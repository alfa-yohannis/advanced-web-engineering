"""Satu replika layanan rekomendasi, tanpa state di dalam prosesnya.

Tiap permintaan /rekomendasi mengerjakan dua hal: bertanya ke basis data
tiruan, lalu menghitung skor 20.000 buku di dalam proses. Bagian kedua memakai
CPU penuh, sehingga satu replika paling banyak memakai satu core, dan menambah
replika berarti menambah core yang bekerja.

Replika tidak menyimpan apa pun di antara dua permintaan. Karena itu
permintaan mana pun boleh dilayani replika mana pun, dan penyeimbang beban
tidak perlu mengingat siapa melayani siapa.

Alamat yang dilayani:
    GET /rekomendasi/<nomor>   satu query, lalu menghitung skor 20.000 buku
    GET /harga?jumlah=&satuan= menghitung harga satu pesanan, tanpa query

Pemakaian (dari sources/chapter14), biasanya dinyalakan ukur-skala.py:
    PORT=8111 python3 layanan.py
"""

import heapq
import json
import os
import threading
from http.client import HTTPConnection, HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8111"))
PORT_BASIS_DATA = 8119
BATAS_WAKTU_DETIK = 30
JENIS_ISI_JSON = "application/json"
# Jumlah buku yang dihitung skornya pada tiap permintaan. Angka ini yang
# menentukan biaya CPU per permintaan, sekitar 8 milidetik pada komputer
# pengukuran bab ini.
JUMLAH_KANDIDAT = 20_000
JUMLAH_REKOMENDASI = 10
JUMLAH_KATEGORI = 20
SKOR_KATEGORI_DISUKAI = 0.5
# Hash perkalian Knuth, dipakai agar skor dasar tiap buku tersebar tanpa acak
# tetapi tetap sama pada tiap pengukuran.
PENGALI_SEBARAN = 2_654_435_761
PENGALI_PENGGUNA = 40_503
MODULUS_HASH = 2 ** 32
# Aturan harga untuk /harga: diskon grosir mulai 10 eksemplar.
BATAS_GROSIR = 10
DISKON_GROSIR_PERSEN = 15

# Satu sambungan ke basis data untuk tiap utas, dibuka sekali lalu dipakai
# ulang, agar biaya membuka sambungan tidak ikut terukur sebagai biaya query.
SAMBUNGAN_PER_UTAS = threading.local()


def sambungan_basis_data():
  """Mengembalikan sambungan basis data milik utas yang sedang berjalan."""
  if not hasattr(SAMBUNGAN_PER_UTAS, "koneksi"):
    SAMBUNGAN_PER_UTAS.koneksi = HTTPConnection(
        HOST, PORT_BASIS_DATA, timeout=BATAS_WAKTU_DETIK)
  return SAMBUNGAN_PER_UTAS.koneksi


def baca_kesukaan(nomor_pengguna):
  """Menanyakan kategori kesukaan satu pengguna ke basis data tiruan.

  Bila sambungannya sudah ditutup pihak lain, sambungan dibuka ulang satu kali.
  Kegagalan kedua dibiarkan naik, karena itu tanda basis datanya memang mati.
  """
  jalur = f"/kesukaan/{nomor_pengguna}"
  try:
    koneksi = sambungan_basis_data()
    koneksi.request("GET", jalur)
    return json.loads(koneksi.getresponse().read())["kategori"]
  except (OSError, HTTPException):
    SAMBUNGAN_PER_UTAS.koneksi.close()
    del SAMBUNGAN_PER_UTAS.koneksi
    koneksi = sambungan_basis_data()
    koneksi.request("GET", jalur)
    return json.loads(koneksi.getresponse().read())["kategori"]


def hitung_rekomendasi(nomor_pengguna, kategori_disukai):
  """Menghitung skor seluruh kandidat, lalu mengambil sepuluh teratas.

  Seluruh perhitungannya Python murni, sehingga memegang GIL sepanjang
  jalannya. Akibatnya satu proses tidak dapat memakai lebih dari satu core
  untuk pekerjaan ini, dan cara menambah daya hitungnya adalah menambah
  proses.
  """
  disukai = set(kategori_disukai)
  daftar_skor = []
  for nomor_buku in range(JUMLAH_KANDIDAT):
    sebaran = nomor_buku * PENGALI_SEBARAN + nomor_pengguna * PENGALI_PENGGUNA
    skor = (sebaran % MODULUS_HASH) / MODULUS_HASH
    if nomor_buku % JUMLAH_KATEGORI in disukai:
      skor += SKOR_KATEGORI_DISUKAI
    daftar_skor.append((skor, nomor_buku))
  terbaik = heapq.nlargest(JUMLAH_REKOMENDASI, daftar_skor)
  return [nomor_buku for _, nomor_buku in terbaik]


def hitung_harga(jumlah, harga_satuan):
  """Menghitung harga satu pesanan, termasuk diskon grosir.

  Fungsi ini sengaja ringan. Ia dipakai panggilan-jaringan.py untuk
  membandingkan memanggil pekerjaan yang sama sebagai fungsi di dalam proses
  dan sebagai permintaan HTTP ke proses lain.
  """
  harga = jumlah * harga_satuan
  if jumlah >= BATAS_GROSIR:
    harga -= harga * DISKON_GROSIR_PERSEN // 100
  return harga


class PenanganLayanan(BaseHTTPRequestHandler):
  """Melayani rekomendasi dan harga, tanpa menyimpan state antarpermintaan."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_GET(self):
    """Membagi permintaan ke rekomendasi atau harga menurut jalurnya."""
    alamat = urlparse(self.path)
    bagian = alamat.path.strip("/").split("/")
    if len(bagian) == 2 and bagian[0] == "rekomendasi" and bagian[1].isdigit():
      nomor_pengguna = int(bagian[1])
      kesukaan = baca_kesukaan(nomor_pengguna)
      buku = hitung_rekomendasi(nomor_pengguna, kesukaan)
      self.kirim_json(200, {"replika": PORT, "buku": buku})
      return
    if alamat.path == "/harga":
      argumen = parse_qs(alamat.query)
      jumlah = int(argumen.get("jumlah", ["1"])[0])
      harga_satuan = int(argumen.get("satuan", ["0"])[0])
      self.kirim_json(200, {"harga": hitung_harga(jumlah, harga_satuan)})
      return
    self.kirim_json(404, {"pesan": "alamat tidak dikenal"})

  def kirim_json(self, status, isi):
    """Mengirim satu response JSON beserta panjang isinya."""
    badan = json.dumps(isi).encode()
    self.send_response(status)
    self.send_header("Content-Type", JENIS_ISI_JSON)
    self.send_header("Content-Length", str(len(badan)))
    self.end_headers()
    self.wfile.write(badan)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, agar keluaran pengukuran tidak tenggelam."""


def main():
  """Menyalakan satu replika sampai dihentikan dengan Ctrl+C."""
  server = ThreadingHTTPServer((HOST, PORT), PenanganLayanan)
  print(f"Replika di http://{HOST}:{PORT}/rekomendasi/<nomor>", flush=True)
  server.serve_forever()


if __name__ == "__main__":
  main()
