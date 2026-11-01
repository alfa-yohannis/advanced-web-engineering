"""API gateway di depan aplikasi katalog: rate limiting dan satu pintu masuk.

Gateway tidak tahu isi bisnis aplikasinya. Tugasnya tiga: membatasi laju
permintaan tiap klien, menempelkan penanda permintaan agar dapat dilacak,
lalu meneruskan sisanya ke aplikasi di belakangnya.

Pembatasannya memakai token bucket: tiap klien punya ember berisi token,
satu permintaan memakai satu token, dan embernya terisi ulang dengan laju
tetap. Dengan begitu lonjakan pendek masih dilayani, sedangkan laju rata-rata
tetap terbatas.

Pemakaian (dari sources/chapter12, bersama aplikasi.py yang sudah menyala):
    python3 gateway.py
"""

import json
import time
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from itertools import count
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8091
HOST_APLIKASI = "127.0.0.1"
PORT_APLIKASI = 8090
BATAS_WAKTU_DETIK = 5
JENIS_ISI_MASALAH = "application/problem+json"
# Isi ember dan laju pengisiannya. Angkanya sengaja kecil agar batasnya
# terlihat dalam satu latihan, tanpa menunggu lama.
KAPASITAS_EMBER = 20
PENGISIAN_PER_DETIK = 5.0
BATAS_ISI_BYTE = 4096

# Satu ember per klien, dikenali dari header X-Klien atau dari alamatnya.
EMBER = {}
NOMOR_PERMINTAAN = count(1)


def ambil_token(nama_klien, sekarang):
  """Mengambil satu token milik satu klien, bila masih ada.

  Mengembalikan pasangan (boleh, tunggu_detik). Tunggu_detik adalah lama
  menunggu sampai satu token berikutnya tersedia, dan dipakai sebagai nilai
  header Retry-After.
  """
  token, waktu_terakhir = EMBER.get(nama_klien, (KAPASITAS_EMBER, sekarang))
  token = min(KAPASITAS_EMBER,
              token + (sekarang - waktu_terakhir) * PENGISIAN_PER_DETIK)
  if token < 1:
    EMBER[nama_klien] = (token, sekarang)
    return False, (1 - token) / PENGISIAN_PER_DETIK
  EMBER[nama_klien] = (token - 1, sekarang)
  return True, 0.0


def teruskan(metode, jalur, header, isi):
  """Meneruskan satu permintaan ke aplikasi, lalu mengembalikan jawabannya."""
  koneksi = HTTPConnection(HOST_APLIKASI, PORT_APLIKASI,
                           timeout=BATAS_WAKTU_DETIK)
  koneksi.request(metode, jalur, body=isi, headers=header)
  response = koneksi.getresponse()
  hasil = (response.status, response.read(),
           response.getheader("Content-Type", "application/json"))
  koneksi.close()
  return hasil


class PenanganGateway(BaseHTTPRequestHandler):
  """Membatasi laju permintaan, lalu meneruskannya ke aplikasi."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_GET(self):
    """Melayani permintaan baca lewat jalur yang sama dengan tulis."""
    self.layani("GET", None)

  def do_POST(self):
    """Membaca isi permintaan lebih dahulu, lalu melayaninya."""
    panjang = min(int(self.headers.get("Content-Length", "0")),
                  BATAS_ISI_BYTE)
    self.layani("POST", self.rfile.read(panjang))

  def layani(self, metode, isi):
    """Memeriksa jatah klien, lalu meneruskan atau menolak permintaannya."""
    nama_klien = self.headers.get("X-Klien", self.client_address[0])
    boleh, tunggu = ambil_token(nama_klien, time.monotonic())
    if not boleh:
      self.tolak(nama_klien, tunggu)
      return
    header = {"X-Permintaan": str(next(NOMOR_PERMINTAAN)),
              "Content-Type": "application/json"}
    if self.headers.get("Idempotency-Key"):
      header["Idempotency-Key"] = self.headers["Idempotency-Key"]
    if isi is not None:
      header["Content-Length"] = str(len(isi))
    alamat = urlparse(self.path)
    jalur = alamat.path + (f"?{alamat.query}" if alamat.query else "")
    status, badan, jenis_isi = teruskan(metode, jalur, header, isi)
    self.kirim(status, badan, jenis_isi, {})

  def tolak(self, nama_klien, tunggu):
    """Menolak satu permintaan karena jatah lajunya habis.

    Penolakannya memakai bentuk Problem Details yang sama dengan aplikasi,
    beserta Retry-After, sehingga klien tahu kapan boleh mencoba lagi.
    """
    isi = {"type": "/masalah/laju-terlampaui",
           "title": "laju permintaan terlampaui",
           "status": 429,
           "detail": f"klien {nama_klien} melewati "
                     f"{PENGISIAN_PER_DETIK:.0f} permintaan per detik"}
    self.kirim(429, json.dumps(isi).encode(), JENIS_ISI_MASALAH,
               {"Retry-After": f"{tunggu:.2f}"})

  def kirim(self, status, isi, jenis_isi, header_tambahan):
    """Mengirim satu response lengkap beserta panjang isinya."""
    self.send_response(status)
    self.send_header("Content-Type", jenis_isi)
    self.send_header("Content-Length", str(len(isi)))
    for nama, nilai in header_tambahan.items():
      self.send_header(nama, nilai)
    self.end_headers()
    self.wfile.write(isi)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, agar keluaran pengukuran tidak tenggelam."""


def main():
  """Menyalakan gateway sampai dihentikan dengan Ctrl+C."""
  server = ThreadingHTTPServer((HOST, PORT), PenanganGateway)
  print(f"Gateway di http://{HOST}:{PORT}/ dengan ember {KAPASITAS_EMBER} "
        f"token dan {PENGISIAN_PER_DETIK:.0f} token per detik"
        "  (Ctrl+C untuk berhenti)")
  server.serve_forever()


if __name__ == "__main__":
  main()
