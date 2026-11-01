"""Membandingkan dua versi kontrak, lalu menguji klien lama ke versi baru.

Perubahan kontrak dipisahkan menjadi dua jenis. Perubahan yang aman hanya
menambah hal opsional, sehingga klien lama tetap jalan. Perubahan yang
merusak menghapus atau mengganti hal yang wajib, sehingga klien lama berhenti
bekerja walaupun servernya sehat.

Bagian kedua membuktikannya pada server yang menyala: isi jawaban versi 2
divalidasi terhadap skema versi 1, dan isi permintaan yang sah di versi 2
dikirim ke versi 1.

Pemakaian (dari sources/chapter12, setelah aplikasi.py menyala):
    python3 uji-kompatibilitas.py
"""

import json
from http.client import HTTPConnection
from pathlib import Path

import jsonschema

HOST = "127.0.0.1"
PORT = 8090
BATAS_WAKTU_DETIK = 5
DIREKTORI = Path(__file__).parent
LEBAR_PERUBAHAN = 46
LEBAR_NAMA = 34


def baca(nama_file):
  """Membaca satu kontrak OpenAPI dari file di direktori ini."""
  return json.loads((DIREKTORI / nama_file).read_text(encoding="utf-8"))


LAMA = baca("kontrak.json")
BARU = baca("kontrak-v2.json")


def skema_dari(kontrak, nama):
  """Menyusun skema yang menunjuk satu komponen di dalam kontraknya."""
  return {"$ref": f"#/components/schemas/{nama}", **kontrak}


def bandingkan_satu(nama, skema_lama, skema_baru):
  """Membandingkan satu skema pada dua versi, lalu menamai perubahannya.

  Tiga hal diperiksa: field wajib yang hilang, field baru, dan daftar nilai
  enum yang bertambah. Ketiganya punya akibat berbeda bagi klien lama.
  """
  hasil = []
  wajib_lama = set(skema_lama.get("required", []))
  wajib_baru = set(skema_baru.get("required", []))
  for field in sorted(wajib_lama - wajib_baru):
    hasil.append((f"{nama}.{field} wajib dihapus", "merusak klien lama"))
  for field in sorted(wajib_baru - wajib_lama):
    hasil.append((f"{nama}.{field} wajib ditambah", "merusak klien lama"))
  sifat_lama = set(skema_lama.get("properties", {}))
  sifat_baru = set(skema_baru.get("properties", {}))
  for field in sorted(sifat_baru - sifat_lama - wajib_baru):
    hasil.append((f"{nama}.{field} opsional ditambah", "aman"))
  for field in sorted(sifat_lama & sifat_baru):
    enum_lama = skema_lama["properties"][field].get("enum")
    enum_baru = skema_baru["properties"][field].get("enum")
    if enum_lama and enum_baru and set(enum_baru) - set(enum_lama):
      tambahan = ", ".join(sorted(set(enum_baru) - set(enum_lama)))
      hasil.append((f"{nama}.{field} enum menerima {tambahan}",
                    "merusak klien lama"))
    batas_lama = skema_lama["properties"][field].get("maximum")
    batas_baru = skema_baru["properties"][field].get("maximum")
    if batas_lama and batas_baru and batas_baru > batas_lama:
      hasil.append((f"{nama}.{field} batas naik ke {batas_baru}",
                    "aman bagi klien lama"))
  return hasil


def bandingkan_kontrak():
  """Membandingkan seluruh skema yang ada di kedua versi kontrak."""
  skema_lama = LAMA["components"]["schemas"]
  skema_baru = BARU["components"]["schemas"]
  hasil = []
  for nama in sorted(set(skema_lama) & set(skema_baru)):
    hasil.extend(bandingkan_satu(nama, skema_lama[nama], skema_baru[nama]))
  return hasil


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


def klien_lama_baca_versi(versi):
  """Memvalidasi jawaban satu versi terhadap skema klien versi 1."""
  status, isi = minta("GET", f"/{versi}/buku?per_halaman=2")
  try:
    jsonschema.validate(isi, skema_dari(LAMA, "HalamanBuku"))
    return f"klien v1 membaca /{versi}/buku", status, "jalan"
  except jsonschema.ValidationError as kesalahan:
    return (f"klien v1 membaca /{versi}/buku", status,
            f"gagal: {kesalahan.message[:38]}")


def klien_baru_kirim_ke(versi, nomor):
  """Mengirim isi yang sah di versi 2, lalu mencatat status jawabannya."""
  isi = {"id_buku": 3, "jumlah": 15}
  kunci = f"uji-kompatibel-{nomor:04d}"
  status, jawaban = minta("POST", f"/{versi}/pesanan", isi,
                          {"Idempotency-Key": kunci})
  keterangan = ("diterima" if status == 201
                else jawaban.get("title", "ditolak"))
  return f"klien v2 memesan 15 ke /{versi}", status, keterangan


def main():
  """Mencetak perbandingan kontrak, lalu hasil pengujian pada server."""
  print(f"  {'Perubahan kontrak v1 ke v2':<{LEBAR_PERUBAHAN}} Akibat")
  for perubahan, akibat in bandingkan_kontrak():
    print(f"  {perubahan:<{LEBAR_PERUBAHAN}} {akibat}")
  print()
  print(f"  {'Yang diuji pada server':<{LEBAR_NAMA}} {'Status':>6}  Hasil")
  baris = [klien_lama_baca_versi("v1"), klien_lama_baca_versi("v2"),
           klien_baru_kirim_ke("v2", 1), klien_baru_kirim_ke("v1", 2)]
  for nama, status, hasil in baris:
    print(f"  {nama:<{LEBAR_NAMA}} {status:>6}  {hasil}")


if __name__ == "__main__":
  main()
