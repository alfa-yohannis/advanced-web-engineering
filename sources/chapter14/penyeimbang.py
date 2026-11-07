"""Penyeimbang beban round robin di depan sejumlah replika layanan.

Tiap permintaan diteruskan ke replika berikutnya secara bergiliran. Daftar
port replikanya dibaca dari environment REPLIKA, misalnya "8111,8112,8113",
sehingga jumlah replika diubah tanpa menyentuh kode.

Penyeimbang ini tidak menyimpan apa pun tentang pengguna. Ia dapat bekerja
seperti itu hanya karena replikanya tanpa state: replika mana pun sanggup
melayani permintaan mana pun.

Pemakaian (dari sources/chapter14), biasanya dinyalakan ukur-skala.py:
    REPLIKA=8111,8112 python3 penyeimbang.py
"""

import itertools
import os
import threading
from http.client import HTTPConnection, HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8110
DAFTAR_PORT_REPLIKA = [int(port) for port in
                       os.environ.get("REPLIKA", "8111").split(",")]
BATAS_WAKTU_DETIK = 30

# Penghitung giliran bersama seluruh utas. Kuncinya menjaga agar dua utas
# tidak mendapat giliran yang sama.
PENGHITUNG_GILIRAN = itertools.count()
KUNCI_GILIRAN = threading.Lock()
# Sambungan ke tiap replika, satu set untuk tiap utas, dipakai ulang.
SAMBUNGAN_PER_UTAS = threading.local()


def pilih_replika():
  """Memilih port replika berikutnya secara bergiliran."""
  with KUNCI_GILIRAN:
    giliran = next(PENGHITUNG_GILIRAN)
  return DAFTAR_PORT_REPLIKA[giliran % len(DAFTAR_PORT_REPLIKA)]


def sambungan_ke(port):
  """Mengembalikan sambungan utas ini ke satu replika, dibuka sekali saja."""
  if not hasattr(SAMBUNGAN_PER_UTAS, "daftar"):
    SAMBUNGAN_PER_UTAS.daftar = {}
  if port not in SAMBUNGAN_PER_UTAS.daftar:
    SAMBUNGAN_PER_UTAS.daftar[port] = HTTPConnection(
        HOST, port, timeout=BATAS_WAKTU_DETIK)
  return SAMBUNGAN_PER_UTAS.daftar[port]


def teruskan(port, jalur):
  """Meneruskan satu permintaan ke replika, lalu membawa balik hasilnya.

  Sambungan yang ternyata sudah ditutup replika dibuka ulang satu kali.
  """
  try:
    koneksi = sambungan_ke(port)
    koneksi.request("GET", jalur)
    response = koneksi.getresponse()
  except (OSError, HTTPException):
    SAMBUNGAN_PER_UTAS.daftar.pop(port).close()
    koneksi = sambungan_ke(port)
    koneksi.request("GET", jalur)
    response = koneksi.getresponse()
  return response.status, response.read()


class PenanganPenyeimbang(BaseHTTPRequestHandler):
  """Meneruskan tiap permintaan GET ke replika yang mendapat giliran."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_GET(self):
    """Memilih replika, meneruskan permintaan, lalu mengirim balik isinya."""
    port = pilih_replika()
    status, isi = teruskan(port, self.path)
    self.send_response(status)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(isi)))
    self.send_header("X-Replika", str(port))
    self.end_headers()
    self.wfile.write(isi)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, agar keluaran pengukuran tidak tenggelam."""


def main():
  """Menyalakan penyeimbang beban sampai dihentikan dengan Ctrl+C."""
  server = ThreadingHTTPServer((HOST, PORT), PenanganPenyeimbang)
  print(f"Penyeimbang di http://{HOST}:{PORT}/, "
        f"{len(DAFTAR_PORT_REPLIKA)} replika: {DAFTAR_PORT_REPLIKA}", flush=True)
  server.serve_forever()


if __name__ == "__main__":
  main()
