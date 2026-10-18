"""Satu aplikasi katalog dengan tiga varian halaman, dipakai sepanjang Bab 11.

Alamat yang dilayani:
    GET /penuh            halaman yang seluruh komponennya dihidupkan
    GET /selektif         halaman sama, hanya dua pulaunya yang dihidupkan
    GET /kerangka/...     application shell beserta routing di sisi browser
    GET /fragmen/...      isi wilayah saja, dipakai router saat berpindah
    GET /api/katalog      server state, yaitu data yang dimiliki server
    GET /aset/<file>      file JavaScript

Kedua varian hidrasi memakai markup kartu yang sama persis. Yang berbeda
hanya blok state yang dititipkan ke browser dan nama file skripnya, sehingga
selisih yang terukur berasal dari cara hidrasinya, bukan dari isi halamannya.

Pemakaian (dari sources/chapter11):
    python3 aplikasi.py
    JUMLAH_BUKU=1000 python3 aplikasi.py
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import komponen

HOST = "127.0.0.1"
PORT = 8080
DIREKTORI_STATIS = Path(__file__).parent / "statis"
JENIS_ISI_HTML = "text/html; charset=utf-8"
JENIS_ISI_JSON = "application/json"
JENIS_ISI_JS = "text/javascript"
AWALAN_BUKU = "/buku/"
# Besar halaman dibaca dari environment, sehingga satu perintah cukup untuk
# mengulang pengukuran pada halaman yang lebih besar atau lebih kecil.
JUMLAH_BUKU = int(os.environ.get("JUMLAH_BUKU",
                                 str(komponen.JUMLAH_BUKU_BAWAAN)))
DAFTAR = komponen.buat_daftar(JUMLAH_BUKU)


def ambil_saringan(query_terurai):
  """Mengambil kata saringan dari query, atau string kosong bila tidak ada."""
  return query_terurai.get("saring", [""])[0]


def rakit_halaman(skrip, state, daftar, saringan):
  """Merakit halaman katalog dengan blok state dan skrip yang diminta."""
  isi = "\n".join([
      komponen.blok_state(state),
      komponen.penyaring(saringan),
      komponen.keranjang(),
      komponen.daftar_buku(daftar),
  ])
  return komponen.tata_letak("Katalog", isi, skrip).encode()


def ambil_id_buku(sisa_jalur):
  """Mengambil nomor buku dari sisa jalur, atau None bila bukan angka."""
  nomor = sisa_jalur[len(AWALAN_BUKU):]
  return int(nomor) if nomor.isdigit() else None


def rakit_fragmen(sisa_jalur, saringan):
  """Merakit isi wilayah untuk satu alamat, beserta status yang pantas.

  Alamat yang isinya tidak ada tetap mengembalikan fragmen, bukan halaman
  kosong, sehingga kerangka di browser punya sesuatu untuk ditampilkan.
  """
  if sisa_jalur in ("", "/", "/katalog"):
    daftar = komponen.saring_daftar(DAFTAR, saringan)
    return 200, komponen.fragmen_katalog(daftar, saringan)
  if sisa_jalur == "/gagal":
    # Alamat ini sengaja gagal, dipakai untuk melihat batas error bekerja.
    return 500, komponen.fragmen_kosong("Bagian ini gagal dimuat")
  if sisa_jalur.startswith(AWALAN_BUKU):
    buku = komponen.cari_buku(DAFTAR, ambil_id_buku(sisa_jalur))
    if buku:
      return 200, komponen.fragmen_buku(buku)
    return 404, komponen.fragmen_kosong("Buku tidak ditemukan")
  return 404, komponen.fragmen_kosong("Alamat tidak dikenal")


class PenanganKatalog(BaseHTTPRequestHandler):
  """Melayani ketiga varian halaman beserta data dan file skripnya."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True
  blokir_skrip = False

  def do_GET(self):
    """Mengarahkan permintaan ke varian, fragmen, atau file yang sesuai."""
    alamat = urlparse(self.path)
    query = parse_qs(alamat.query)
    saringan = ambil_saringan(query)
    # Dengan blokir_skrip=1, server memasang CSP yang menolak seluruh skrip.
    # Halaman lalu terlihat seperti ketika JavaScript-nya gagal diunduh.
    self.blokir_skrip = query.get("blokir_skrip", [""])[0] == "1"
    if alamat.path == "/penuh":
      self.layani_varian("hidrasi-penuh.js", komponen.state_penuh(DAFTAR),
                         saringan)
      return
    if alamat.path == "/selektif":
      self.layani_varian("hidrasi-selektif.js", komponen.state_pulau(),
                         saringan)
      return
    if alamat.path == "/kerangka" or alamat.path.startswith("/kerangka/"):
      sisa = alamat.path[len("/kerangka"):]
      status, fragmen = rakit_fragmen(sisa, saringan)
      self.kirim(status, komponen.kerangka(fragmen).encode(),
                 JENIS_ISI_HTML)
      return
    if alamat.path.startswith("/fragmen"):
      status, fragmen = rakit_fragmen(alamat.path[len("/fragmen"):], saringan)
      self.kirim(status, fragmen.encode(), JENIS_ISI_HTML)
      return
    if alamat.path == "/api/katalog":
      self.kirim(200, json.dumps(DAFTAR).encode(), JENIS_ISI_JSON)
      return
    if alamat.path.startswith("/aset/"):
      self.layani_aset(alamat.path[len("/aset/"):])
      return
    self.kirim(404, b"alamat tidak dikenal", JENIS_ISI_HTML)

  def do_HEAD(self):
    """Melayani HEAD lewat jalur yang sama, agar curl -I ikut terjawab."""
    self.do_GET()

  def layani_varian(self, skrip, state, saringan):
    """Mengirim satu varian hidrasi beserta daftar yang sudah disaring."""
    daftar = komponen.saring_daftar(DAFTAR, saringan)
    self.kirim(200, rakit_halaman(skrip, state, daftar, saringan),
               JENIS_ISI_HTML)

  def layani_aset(self, nama_file):
    """Mengirim satu file JavaScript dari direktori statis."""
    file_diminta = DIREKTORI_STATIS / nama_file
    if not file_diminta.is_file():
      self.kirim(404, b"file tidak ada", JENIS_ISI_JS)
      return
    self.kirim(200, file_diminta.read_bytes(), JENIS_ISI_JS)

  def kirim(self, status, isi, jenis_isi):
    """Mengirim satu response lengkap beserta panjang isinya."""
    self.send_response(status)
    self.send_header("Content-Type", jenis_isi)
    self.send_header("Content-Length", str(len(isi)))
    self.send_header("Cache-Control", "no-store")
    if self.blokir_skrip:
      self.send_header("Content-Security-Policy", "script-src 'none'")
    self.end_headers()
    if self.command != "HEAD":
      self.wfile.write(isi)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, agar keluaran pengukuran tidak tenggelam."""


def main():
  """Menyalakan server sampai dihentikan dengan Ctrl+C."""
  server = ThreadingHTTPServer((HOST, PORT), PenanganKatalog)
  print(f"Melayani di http://{HOST}:{PORT}/penuh dengan {JUMLAH_BUKU} buku"
        "  (Ctrl+C untuk berhenti)")
  server.serve_forever()


if __name__ == "__main__":
  main()
