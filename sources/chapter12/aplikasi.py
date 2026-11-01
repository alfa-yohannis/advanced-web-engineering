"""Aplikasi katalog dua versi yang dilayani dari satu kontrak OpenAPI.

Alamat yang dilayani:
    GET  /v1/buku      daftar buku versi 1, dengan pagination dan filtering
    GET  /v2/buku      versi 2, field harga berganti nama dan ada penerbit
    POST /v1/pesanan   membuat pesanan, idempoten terhadap Idempotency-Key
    POST /v2/pesanan   sama, dengan batas jumlah yang dilonggarkan
    GET  /openapi.json kontrak versi 1
    GET  /openapi-v2.json kontrak versi 2

Isi permintaan divalidasi di batas sistem memakai skema dari kontraknya,
bukan memakai pemeriksaan yang ditulis ulang di dalam kode. Kesalahan dijawab
dengan bentuk Problem Details, yaitu application/problem+json.

Pemakaian (dari sources/chapter12):
    python3 aplikasi.py
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import jsonschema

HOST = "127.0.0.1"
PORT = 8090
DIREKTORI = Path(__file__).parent
JENIS_ISI_JSON = "application/json"
JENIS_ISI_MASALAH = "application/problem+json"
# Batas ukuran isi permintaan, agar satu permintaan tidak dapat memaksa
# server membaca isi yang besar sebelum memeriksanya.
BATAS_ISI_BYTE = 4096
PER_HALAMAN_BAWAAN = 10
JUDUL_DASAR = [
    "Rekayasa Web Lanjut",
    "Basis Data Terapan",
    "Jaringan untuk Pengembang",
    "Keamanan Aplikasi Web",
    "Pengantar Algoritma",
    "Arsitektur Perangkat Lunak",
]
JUMLAH_BUKU = 48
PENERBIT = "Pradita Press"


def baca_kontrak(nama_file):
  """Membaca satu kontrak OpenAPI dari file di direktori ini."""
  return json.loads((DIREKTORI / nama_file).read_text(encoding="utf-8"))


KONTRAK = {"v1": baca_kontrak("kontrak.json"),
           "v2": baca_kontrak("kontrak-v2.json")}


def buat_daftar():
  """Menyusun daftar buku yang dilayani kedua versi dari data yang sama."""
  daftar = []
  for nomor in range(1, JUMLAH_BUKU + 1):
    judul = JUDUL_DASAR[(nomor - 1) % len(JUDUL_DASAR)]
    daftar.append({
        "id": nomor,
        "judul": f"{judul} Jilid {nomor}",
        "harga": 80000 + (nomor % 12) * 5000,
        "stok": nomor % 10,
    })
  return daftar


DAFTAR_BUKU = buat_daftar()
# Pesanan yang sudah dibuat, beserta kunci idempotensinya. Cukup di memori,
# karena yang dibuktikan bab ini perilakunya, bukan ketahanannya.
PESANAN = {}
IDEMPOTENSI = {}


def skema(versi, nama):
  """Menyusun skema yang menunjuk satu komponen di dalam kontraknya.

  Seluruh dokumen kontrak dipakai sebagai skema, dan namanya ditunjuk lewat
  $ref. Dengan begitu rujukan antarskema di dalam kontrak, misalnya
  HalamanBuku ke Buku, tetap dapat ditelusuri validator.
  """
  return {"$ref": f"#/components/schemas/{nama}", **KONTRAK[versi]}


def bentuk_buku(buku, versi):
  """Menyusun satu buku sesuai versi kontrak yang diminta.

  Versi 2 mengganti nama field harga dan menambah penerbit. Datanya sama,
  dan hanya bentuk luarnya yang berbeda, sehingga perbedaan versi tidak
  menuntut dua salinan data.
  """
  if versi == "v1":
    return dict(buku)
  tanpa_harga = {kunci: nilai for kunci, nilai in buku.items()
                 if kunci != "harga"}
  return {**tanpa_harga, "harga_rupiah": buku["harga"], "penerbit": PENERBIT}


def saring_daftar(daftar, kata):
  """Menyaring daftar buku berdasarkan kata pada judulnya."""
  if not kata:
    return daftar
  return [buku for buku in daftar if kata.lower() in buku["judul"].lower()]


def ambil_angka(query, nama, bawaan):
  """Mengambil satu parameter angka dari query, atau None bila bukan angka."""
  nilai = query.get(nama, [str(bawaan)])[0]
  return int(nilai) if nilai.isdigit() else None


def rakit_halaman(versi, query):
  """Merakit satu halaman daftar buku beserta penanda halaman berikutnya."""
  halaman = ambil_angka(query, "halaman", 1)
  per_halaman = ambil_angka(query, "per_halaman", PER_HALAMAN_BAWAAN)
  if not halaman or not per_halaman:
    return None, "halaman dan per_halaman harus bilangan bulat positif"
  if per_halaman > 50:
    return None, "per_halaman melebihi batas 50 pada kontrak"
  saringan = query.get("saring", [""])[0]
  cocok = saring_daftar(DAFTAR_BUKU, saringan)
  awal = (halaman - 1) * per_halaman
  item = [bentuk_buku(buku, versi) for buku in cocok[awal:awal + per_halaman]]
  hasil = {"item": item, "halaman": halaman, "per_halaman": per_halaman,
           "total": len(cocok)}
  if awal + per_halaman < len(cocok):
    hasil["berikutnya"] = (f"/{versi}/buku?halaman={halaman + 1}"
                           f"&per_halaman={per_halaman}")
  return hasil, None


def periksa_isi(versi, isi):
  """Memvalidasi isi permintaan terhadap skema PesananBaru di kontrak.

  Inilah validasi di batas sistem: satu pemeriksaan di pintu masuk, memakai
  skema yang sama dengan yang dipakai meng-generate tipe kliennya.
  """
  try:
    jsonschema.validate(isi, skema(versi, "PesananBaru"))
  except jsonschema.ValidationError as kesalahan:
    return kesalahan.message
  return None


def buat_pesanan(versi, isi, kunci):
  """Membuat satu pesanan, atau mengembalikan pesanan lama untuk kunci sama.

  Mengembalikan pasangan (pesanan, status). Status 200 berarti kunci yang
  sama sudah pernah dipakai dengan isi yang sama, sehingga tidak ada pesanan
  baru yang dibuat.
  """
  sidik = json.dumps(isi, sort_keys=True)
  if kunci in IDEMPOTENSI:
    sidik_lama, id_pesanan = IDEMPOTENSI[kunci]
    if sidik_lama != sidik:
      return None, 409
    return PESANAN[id_pesanan], 200
  id_pesanan = f"psn-{len(PESANAN) + 1:04d}"
  pesanan = {"id": id_pesanan, "id_buku": isi["id_buku"],
             "jumlah": isi["jumlah"], "status": "diterima"}
  PESANAN[id_pesanan] = pesanan
  IDEMPOTENSI[kunci] = (sidik, id_pesanan)
  return pesanan, 201


class PenanganKatalog(BaseHTTPRequestHandler):
  """Melayani kedua versi katalog beserta kontrak yang menjadi sumbernya."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_GET(self):
    """Melayani daftar buku dan kontraknya."""
    alamat = urlparse(self.path)
    if alamat.path == "/openapi.json":
      self.kirim_json(200, KONTRAK["v1"])
      return
    if alamat.path == "/openapi-v2.json":
      self.kirim_json(200, KONTRAK["v2"])
      return
    for versi in ("v1", "v2"):
      if alamat.path == f"/{versi}/buku":
        hasil, salah = rakit_halaman(versi, parse_qs(alamat.query))
        if salah:
          self.kirim_masalah(422, "parameter-tidak-sesuai", salah)
          return
        self.kirim_json(200, hasil)
        return
    self.kirim_masalah(404, "alamat-tidak-dikenal", self.path)

  def do_POST(self):
    """Melayani pembuatan pesanan pada kedua versi."""
    alamat = urlparse(self.path)
    versi = alamat.path.split("/")[1] if "/" in alamat.path[1:] else ""
    if versi not in KONTRAK or not alamat.path.endswith("/pesanan"):
      self.kirim_masalah(404, "alamat-tidak-dikenal", self.path)
      return
    kunci = self.headers.get("Idempotency-Key", "")
    if len(kunci) < 8:
      self.kirim_masalah(400, "kunci-idempotensi-kurang",
                         "header Idempotency-Key minimal 8 huruf")
      return
    isi = self.baca_isi()
    if isi is None:
      return
    salah = periksa_isi(versi, isi)
    if salah:
      self.kirim_masalah(422, "isi-tidak-sesuai", salah)
      return
    pesanan, status = buat_pesanan(versi, isi, kunci)
    if status == 409:
      self.kirim_masalah(409, "kunci-idempotensi-dipakai-ulang",
                         "kunci yang sama sudah dipakai untuk isi berbeda")
      return
    self.kirim_json(status, pesanan)

  def baca_isi(self):
    """Membaca isi permintaan sebagai JSON, atau menjawab masalahnya."""
    panjang = min(int(self.headers.get("Content-Length", "0")),
                  BATAS_ISI_BYTE)
    try:
      return json.loads(self.rfile.read(panjang) or b"{}")
    except json.JSONDecodeError as kesalahan:
      self.kirim_masalah(400, "bukan-json", str(kesalahan))
      return None

  def kirim_json(self, status, isi):
    """Mengirim satu response JSON beserta panjangnya."""
    self.kirim(status, json.dumps(isi).encode(), JENIS_ISI_JSON)

  def kirim_masalah(self, status, jenis, rincian):
    """Mengirim kesalahan dalam bentuk Problem Details.

    Seluruh kesalahan memakai satu bentuk yang sama, sehingga klien cukup
    menulis satu penanganan kesalahan, bukan satu per alamat.
    """
    isi = {"type": f"/masalah/{jenis}", "title": jenis.replace("-", " "),
           "status": status, "detail": rincian}
    self.kirim(status, json.dumps(isi).encode(), JENIS_ISI_MASALAH)

  def kirim(self, status, isi, jenis_isi):
    """Mengirim satu response lengkap beserta panjang isinya."""
    self.send_response(status)
    self.send_header("Content-Type", jenis_isi)
    self.send_header("Content-Length", str(len(isi)))
    self.end_headers()
    self.wfile.write(isi)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, agar keluaran pengukuran tidak tenggelam."""


def main():
  """Menyalakan server sampai dihentikan dengan Ctrl+C."""
  server = ThreadingHTTPServer((HOST, PORT), PenanganKatalog)
  print(f"Melayani di http://{HOST}:{PORT}/v1/buku dengan {JUMLAH_BUKU} buku"
        "  (Ctrl+C untuk berhenti)")
  server.serve_forever()


if __name__ == "__main__":
  main()
