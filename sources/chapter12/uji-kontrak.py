"""Menguji jawaban server dan isi permintaan terhadap kontraknya.

Tiga hal diuji sekaligus. Pertama, jawaban server divalidasi terhadap skema
di kontrak, sehingga kontrak yang sudah berubah tetapi kodenya belum langsung
terlihat. Kedua, beberapa isi permintaan dikirim ke server, termasuk yang
sengaja salah, lalu statusnya dibandingkan dengan yang dijanjikan kontrak.
Ketiga, janji idempotensi dibuktikan: kunci yang sama dipakai dua kali.

Pengujian ini bersifat mengamati dan hanya diarahkan ke aplikasi sendiri di
127.0.0.1.

Pemakaian (dari sources/chapter12, setelah aplikasi.py menyala):
    python3 uji-kontrak.py
"""

import json
from http.client import HTTPConnection
from pathlib import Path

import jsonschema

HOST = "127.0.0.1"
PORT = 8090
BATAS_WAKTU_DETIK = 5
DIREKTORI = Path(__file__).parent
KONTRAK = json.loads((DIREKTORI / "kontrak.json").read_text(encoding="utf-8"))
# Isi permintaan yang diuji di batas sistem, beserta status yang dijanjikan
# kontrak. Nama kuncinya ikut dicetak, agar tabelnya terbaca tanpa kode.
ISI_UJI = [
    ("sesuai kontrak", {"id_buku": 3, "jumlah": 2}, 201),
    ("field wajib hilang", {"jumlah": 2}, 422),
    ("tipe salah", {"id_buku": "tiga", "jumlah": 2}, 422),
    ("melebihi batas", {"id_buku": 3, "jumlah": 99}, 422),
    ("field asing", {"id_buku": 3, "jumlah": 2, "catatan": "titip"}, 422),
]
LEBAR_NAMA = 28


def skema(nama):
  """Menyusun skema yang menunjuk satu komponen di dalam kontraknya."""
  return {"$ref": f"#/components/schemas/{nama}", **KONTRAK}


def minta(metode, jalur, isi=None, header=None):
  """Mengirim satu permintaan, lalu mengembalikan status beserta isinya."""
  koneksi = HTTPConnection(HOST, PORT, timeout=BATAS_WAKTU_DETIK)
  badan = json.dumps(isi).encode() if isi is not None else None
  semua_header = dict(header or {})
  if badan:
    semua_header["Content-Type"] = "application/json"
  koneksi.request(metode, jalur, body=badan, headers=semua_header)
  response = koneksi.getresponse()
  mentah = response.read()
  status = response.status
  koneksi.close()
  return status, json.loads(mentah) if mentah else {}


def periksa_jawaban(nama, jalur, nama_skema):
  """Memvalidasi satu jawaban server terhadap skema di kontrak."""
  status, isi = minta("GET", jalur)
  try:
    jsonschema.validate(isi, skema(nama_skema))
    return nama, status, "sesuai skema"
  except jsonschema.ValidationError as kesalahan:
    return nama, status, f"melanggar: {kesalahan.message[:40]}"


def periksa_permintaan(nama, isi, status_dijanjikan, nomor):
  """Mengirim satu isi permintaan, lalu membandingkan statusnya."""
  kunci = f"uji-kontrak-{nomor:04d}"
  status, jawaban = minta("POST", "/v1/pesanan", isi,
                          {"Idempotency-Key": kunci})
  sesuai = "sesuai" if status == status_dijanjikan else "TIDAK sesuai"
  alasan = jawaban.get("title", jawaban.get("status", ""))
  return nama, status, f"{sesuai}, {alasan}"


def periksa_idempotensi():
  """Membuktikan janji idempotensi dengan memakai satu kunci dua kali.

  Kunci yang sama dengan isi yang sama tidak boleh membuat pesanan kedua,
  dan kunci yang sama dengan isi berbeda harus ditolak, bukan diterima
  diam-diam sebagai pesanan baru.
  """
  kunci = "idempotensi-sama"
  isi = {"id_buku": 5, "jumlah": 1}
  status_awal, pesanan_awal = minta("POST", "/v1/pesanan", isi,
                                    {"Idempotency-Key": kunci})
  status_ulang, pesanan_ulang = minta("POST", "/v1/pesanan", isi,
                                      {"Idempotency-Key": kunci})
  status_beda, jawaban_beda = minta("POST", "/v1/pesanan",
                                    {"id_buku": 6, "jumlah": 1},
                                    {"Idempotency-Key": kunci})
  sama = pesanan_awal.get("id") == pesanan_ulang.get("id")
  return [
      ("kunci baru", status_awal, f"pesanan {pesanan_awal.get('id')} dibuat"),
      ("kunci sama, isi sama", status_ulang,
       f"pesanan {pesanan_ulang.get('id')} dikembalikan, "
       f"{'sama' if sama else 'BERBEDA'}"),
      ("kunci sama, isi beda", status_beda,
       jawaban_beda.get("title", "diterima")),
  ]


def main():
  """Menjalankan ketiga pengujian, lalu mencetak hasilnya sebagai tabel."""
  baris = [
      periksa_jawaban("GET /v1/buku", "/v1/buku", "HalamanBuku"),
      periksa_jawaban("GET /v1/buku?halaman=2", "/v1/buku?halaman=2",
                      "HalamanBuku"),
      periksa_jawaban("GET /v1/buku?per_halaman=99",
                      "/v1/buku?per_halaman=99", "Kesalahan"),
  ]
  for nomor, (nama, isi, status) in enumerate(ISI_UJI, start=1):
    baris.append(periksa_permintaan(nama, isi, status, nomor))
  baris.extend(periksa_idempotensi())
  print(f"  {'Yang diuji':<{LEBAR_NAMA}} {'Status':>6}  Hasil")
  for nama, status, hasil in baris:
    print(f"  {nama:<{LEBAR_NAMA}} {status:>6}  {hasil}")


if __name__ == "__main__":
  main()
