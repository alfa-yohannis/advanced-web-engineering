"""Satu halaman katalog yang disajikan dengan lima arsitektur berbeda.

Alamat yang dilayani:
    GET /ssr        HTML dirakit server pada tiap permintaan
    GET /ssg        HTML yang sudah dirakit sebelumnya, dibaca dari file
    GET /isr        seperti SSG, tetapi dirakit ulang setelah file kedaluwarsa
    GET /spa        kerangka kosong, isinya diambil JavaScript lewat JSON
    GET /islands    HTML berisi isi lengkap, ditambah satu widget kecil
    GET /api/katalog  data JSON untuk varian SPA dan islands
    GET /aset/<file>  file JavaScript

Kelima varian memakai data dan kerangka halaman yang sama, sehingga selisih
yang terukur benar-benar berasal dari tempat HTML-nya dirakit.

Pemakaian (dari sources/chapter08):
    python3 bangun-statis.py
    python3 aplikasi.py
"""

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import katalog

HOST = "127.0.0.1"
PORT = 8040
DIREKTORI_STATIS = Path(__file__).parent / "statis"
FILE_SSG = DIREKTORI_STATIS / "katalog-ssg.html"
FILE_ISR = DIREKTORI_STATIS / "katalog-isr.html"
JENIS_ISI_HTML = "text/html; charset=utf-8"
JENIS_ISI_JSON = "application/json"
JENIS_ISI_JS = "text/javascript"
# Umur file ISR sebelum dirakit ulang. Dipilih pendek agar pengaruhnya
# terlihat dalam satu sesi latihan.
UMUR_ISR_DETIK = 10
# Perakitan sengaja diperlambat sedikit, meniru halaman yang isinya mahal
# dihitung. Tanpa ini, selisih SSR dan SSG tidak terbaca pengukur waktu.
LAMA_RAKIT_DETIK = 0.05


def rakit_halaman_katalog():
  """Merakit halaman katalog lengkap, yaitu pekerjaan yang dihemat SSG.

  Jeda di dalamnya mewakili pekerjaan nyata sebuah halaman, misalnya
  memanggil basis data dan menyusun ringkasannya.
  """
  time.sleep(LAMA_RAKIT_DETIK)
  isi = f"    <ul>\n      {katalog.rakit_baris_html()}\n    </ul>"
  return katalog.rakit_halaman("Katalog", isi)


def baca_atau_rakit_isr():
  """Membaca file ISR, dan merakitnya ulang bila umurnya sudah lewat.

  Inilah inti Incremental Static Regeneration: pengunjung tetap dilayani
  file yang sudah jadi, sedangkan perakitan ulang hanya terjadi sesekali.
  """
  if FILE_ISR.exists():
    umur = time.time() - FILE_ISR.stat().st_mtime
    if umur < UMUR_ISR_DETIK:
      return FILE_ISR.read_bytes(), "file lama dipakai"
  FILE_ISR.write_text(rakit_halaman_katalog(), encoding="utf-8")
  return FILE_ISR.read_bytes(), "dirakit ulang"


class PenanganVarian(BaseHTTPRequestHandler):
  """Melayani kelima varian halaman katalog beserta datanya."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_GET(self):
    """Mengarahkan permintaan ke varian yang sesuai dengan jalurnya."""
    if self.path == "/ssr":
      self.kirim(200, rakit_halaman_katalog().encode(), JENIS_ISI_HTML, [])
      return
    if self.path == "/ssg":
      self.kirim(200, FILE_SSG.read_bytes(), JENIS_ISI_HTML, [])
      return
    if self.path == "/isr":
      isi, keterangan = baca_atau_rakit_isr()
      self.kirim(200, isi, JENIS_ISI_HTML, [("X-ISR", keterangan)])
      return
    if self.path == "/spa":
      self.kirim(200, self.rakit_kerangka_spa(), JENIS_ISI_HTML, [])
      return
    if self.path == "/islands":
      self.kirim(200, self.rakit_halaman_islands(), JENIS_ISI_HTML, [])
      return
    if self.path == "/api/katalog":
      isi = json.dumps(katalog.DAFTAR_BUKU).encode()
      self.kirim(200, isi, JENIS_ISI_JSON, [])
      return
    if self.path.startswith("/aset/"):
      self.layani_aset(self.path[len("/aset/"):])
      return
    self.kirim(404, b"alamat tidak dikenal", JENIS_ISI_HTML, [])

  def do_HEAD(self):
    """Menjawab HEAD dengan header yang sama persis, tanpa isinya.

    Alat pemeriksa sering memakai HEAD untuk membaca header saja. Tanpa
    metode ini, server menjawab 501 dan headernya tidak pernah terbaca.
    """
    self.do_GET()

  def rakit_kerangka_spa(self):
    """Merakit kerangka SPA, yaitu halaman tanpa isi katalog sama sekali.

    Isinya baru ada sesudah browser mengunduh skripnya, menjalankannya, lalu
    meminta data lewat permintaan kedua.
    """
    isi = '    <ul id="daftar"></ul>'
    return katalog.rakit_halaman("Katalog", isi, "/aset/spa.js").encode()

  def rakit_halaman_islands(self):
    """Merakit halaman islands, yaitu isi lengkap ditambah satu widget kecil.

    Isinya sudah ada di HTML yang pertama tiba, sedangkan skripnya hanya
    menghidupkan satu bagian, yaitu kotak penyaring.
    """
    isi = ('    <input id="saring" placeholder="Saring judul" />\n'
           f'    <ul id="daftar">\n      {katalog.rakit_baris_html()}\n'
           '    </ul>')
    return katalog.rakit_halaman("Katalog", isi, "/aset/pulau.js").encode()

  def layani_aset(self, nama_file):
    """Mengirim satu file JavaScript dari direktori statis."""
    file_diminta = DIREKTORI_STATIS / nama_file
    if not file_diminta.is_file():
      self.kirim(404, b"file tidak ada", JENIS_ISI_JS, [])
      return
    self.kirim(200, file_diminta.read_bytes(), JENIS_ISI_JS, [])

  def kirim(self, status, isi, jenis_isi, header_tambahan):
    """Mengirim satu response lengkap beserta panjang isinya."""
    self.send_response(status)
    self.send_header("Content-Type", jenis_isi)
    self.send_header("Content-Length", str(len(isi)))
    self.send_header("Cache-Control", "no-store")
    for nama_header, nilai in header_tambahan:
      self.send_header(nama_header, nilai)
    self.end_headers()
    if self.command != "HEAD":
      self.wfile.write(isi)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, agar keluaran pengukuran tidak tenggelam."""


def main():
  """Menyalakan server sampai dihentikan dengan Ctrl+C."""
  if not FILE_SSG.exists():
    raise SystemExit("Jalankan python3 bangun-statis.py lebih dahulu.")
  server = ThreadingHTTPServer((HOST, PORT), PenanganVarian)
  print(f"Melayani di http://{HOST}:{PORT}/ssr  (Ctrl+C untuk berhenti)")
  server.serve_forever()


if __name__ == "__main__":
  main()
