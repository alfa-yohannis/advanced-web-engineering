"""Lapisan route: menerjemahkan HTTP menjadi panggilan service, dan sebaliknya.

Route tidak memuat aturan bisnis dan tidak menyentuh SQL. Tugasnya tiga:
membaca alamat dan isi permintaan, memanggil satu method service, lalu
mengubah hasil atau kesalahannya menjadi status HTTP dan JSON.

Alamat yang dilayani:
    GET  /sehat         tanda hidup, dipakai smoke test dan CI
    GET  /buku          seluruh buku
    GET  /buku/<nomor>  satu buku, atau 404
    POST /buku          menambah buku dari JSON, atau 400

Modul ini diimpor, bukan dijalankan langsung:
    python3 aplikasi.py
"""

import json
from http.server import BaseHTTPRequestHandler

from layanan import BukuTidakDitemukan, KesalahanValidasi

JENIS_ISI_JSON = "application/json"
BATAS_ISI_BYTE = 4096
AWALAN_BUKU = "/buku/"


class PenanganKatalog(BaseHTTPRequestHandler):
  """Menerjemahkan permintaan HTTP katalog menjadi panggilan service."""

  protocol_version = "HTTP/1.1"

  def do_GET(self):
    """Melayani tanda hidup, daftar buku, dan satu buku."""
    layanan = self.server.layanan
    if self.path == "/sehat":
      self.kirim_json(200, {"status": "sehat"})
      return
    if self.path == "/buku":
      self.kirim_json(200, {"buku": layanan.daftar()})
      return
    nomor = self.path.removeprefix(AWALAN_BUKU)
    if self.path.startswith(AWALAN_BUKU) and nomor.isdigit():
      try:
        self.kirim_json(200, layanan.cari(int(nomor)))
      except BukuTidakDitemukan as kesalahan:
        self.kirim_json(404, {"pesan": str(kesalahan)})
      return
    self.kirim_json(404, {"pesan": "alamat tidak dikenal"})

  def do_POST(self):
    """Menambah satu buku dari isi JSON permintaan."""
    panjang = min(int(self.headers.get("Content-Length", "0")), BATAS_ISI_BYTE)
    isi_mentah = self.rfile.read(panjang)
    if self.path != "/buku":
      self.kirim_json(404, {"pesan": "alamat tidak dikenal"})
      return
    try:
      isi = json.loads(isi_mentah)
    except json.JSONDecodeError:
      self.kirim_json(400, {"pesan": "isi permintaan bukan JSON"})
      return
    if not isinstance(isi, dict):
      self.kirim_json(400, {"pesan": "isi permintaan harus objek JSON"})
      return
    try:
      buku = self.server.layanan.tambah_buku(
          isi.get("judul"), isi.get("harga"), isi.get("stok"))
    except KesalahanValidasi as kesalahan:
      self.kirim_json(400, {"pesan": str(kesalahan)})
      return
    self.kirim_json(201, buku)

  def kirim_json(self, status, isi):
    """Mengirim satu response JSON beserta panjang isinya."""
    badan = json.dumps(isi).encode()
    self.send_response(status)
    self.send_header("Content-Type", JENIS_ISI_JSON)
    self.send_header("Content-Length", str(len(badan)))
    self.end_headers()
    self.wfile.write(badan)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, agar keluaran uji dan CI tetap terbaca."""
