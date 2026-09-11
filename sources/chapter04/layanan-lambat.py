#!/usr/bin/env python3
"""Layanan biaya kirim tiruan yang kadang lambat, untuk latihan resilience.

Tiap permintaan GET /ongkir dijawab setelah 20 milidetik. Sebagian permintaan
sengaja ditahan 2 detik sebelum dijawab, meniru layanan pihak lain yang
sedang kewalahan. Besarnya bagian yang ditahan dikirim klien lewat
parameter peluang_lambat, agar satu skrip pengujian dapat memperagakan
beberapa skenario tanpa menyalakan ulang layanan ini.

Pemakaian (dari sources/chapter04):
    source ../.venv/bin/activate
    python layanan-lambat.py
Contoh permintaan dari terminal lain:
    curl "http://localhost:8081/ongkir?peluang_lambat=0.2"
"""

import json
import random
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

ALAMAT_DENGAR = ("127.0.0.1", 8081)
JEDA_NORMAL_DETIK = 0.02
JEDA_LAMBAT_DETIK = 2.0
ONGKIR_RUPIAH = 18000
# Benih tetap membuat urutan undian sama setiap kali layanan dinyalakan.
BENIH_PENGACAK = 42
PANJANG_ANTREAN_KONEKSI = 64


class ServerOngkir(ThreadingHTTPServer):
  """Server yang membawa satu pengacak bersama beserta gemboknya."""

  request_queue_size = PANJANG_ANTREAN_KONEKSI

  def __init__(self, alamat, kelas_penangan):
    """Membuat pengacak berbenih tetap, dijaga satu gembok.

    Satu pengacak dipakai bersama oleh seluruh utas penangan. Gembok mencegah
    dua utas mengambil angka acak pada saat yang sama.
    """
    super().__init__(alamat, kelas_penangan)
    self.pengacak = random.Random(BENIH_PENGACAK)
    self.gembok_pengacak = threading.Lock()

  def undi_apakah_lambat(self, peluang_lambat):
    """Mengundi apakah permintaan ini ditahan lama, sesuai peluang yang diminta."""
    with self.gembok_pengacak:
      return self.pengacak.random() < peluang_lambat

  def handle_error(self, request, client_address):
    """Mengabaikan koneksi yang ditutup klien di tengah jalan.

    Klien yang memakai batas waktu menutup koneksinya sebelum jawaban
    dikirim. Error tulis yang muncul sesudahnya bukan kesalahan layanan.
    """
    if not isinstance(sys.exc_info()[1], ConnectionError):
      super().handle_error(request, client_address)


class PenanganOngkir(BaseHTTPRequestHandler):
  """Menjawab /ongkir, kadang cepat, kadang sengaja lambat."""

  def do_GET(self):
    """Menahan jawaban sesuai hasil undian, lalu mengirim biaya kirim."""
    bagian_alamat = urlsplit(self.path)
    if bagian_alamat.path != "/ongkir":
      self.send_error(404)
      return
    parameter_kueri = parse_qs(bagian_alamat.query)
    peluang_lambat = float(parameter_kueri.get("peluang_lambat", ["0"])[0])
    if self.server.undi_apakah_lambat(peluang_lambat):
      time.sleep(JEDA_LAMBAT_DETIK)
    else:
      time.sleep(JEDA_NORMAL_DETIK)
    isi_jawaban = json.dumps({"ongkir": ONGKIR_RUPIAH}).encode()
    self.send_response(200)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(isi_jawaban)))
    self.end_headers()
    self.wfile.write(isi_jawaban)

  def log_message(self, format_pesan, *argumen):
    """Mematikan catatan per permintaan agar terminal tetap terbaca."""


def main():
  """Melayani sampai dihentikan dengan Ctrl+C."""
  server = ServerOngkir(ALAMAT_DENGAR, PenanganOngkir)
  host, port = ALAMAT_DENGAR
  print(f"Layanan ongkir di http://{host}:{port}/ongkir  (Ctrl+C untuk berhenti)")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass
  finally:
    server.server_close()


if __name__ == "__main__":
  main()
