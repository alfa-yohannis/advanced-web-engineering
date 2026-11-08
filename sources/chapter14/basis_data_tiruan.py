"""Basis data tiruan: satu komponen bersama dengan kapasitas tetap.

Setiap replika layanan bertanya ke sini satu kali per permintaan. Kapasitasnya
sengaja dibatasi: paling banyak JUMLAH_KONEKSI query dikerjakan bersamaan, dan
tiap query memakan WAKTU_QUERY_DETIK. Dengan angka bawaan, batas atasnya 200
query per detik, berapa pun jumlah replika yang bertanya.

Yang ditirukan hanya satu sifat yang menentukan hasil penskalaan horizontal,
yaitu adanya komponen bersama yang tidak ikut bertambah ketika replika
ditambah. Isi response-nya tidak penting, dan memang dibuat kecil.

Pemakaian (dari sources/chapter14), biasanya dinyalakan ukur-skala.py:
    python3 basis_data_tiruan.py
"""

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8119
# Jumlah query yang boleh dikerjakan bersamaan, setara max_connections pada
# PostgreSQL. Nilainya dapat diubah lewat environment tanpa menyunting kode.
JUMLAH_KONEKSI = int(os.environ.get("JUMLAH_KONEKSI", "4"))
# Lama satu query. Kapasitas = JUMLAH_KONEKSI / WAKTU_QUERY_DETIK, yaitu
# 4 / 0,020 = 200 query per detik dengan angka bawaan.
WAKTU_QUERY_DETIK = 0.020
JENIS_ISI_JSON = "application/json"
# Kategori yang disukai tiap pengguna, dikembalikan sebagai hasil query.
JUMLAH_KATEGORI = 20
KATEGORI_PER_PENGGUNA = 3
# Jarak antarkategori kesukaan, agar tiga kategori seorang pengguna tidak
# berdampingan.
JARAK_KATEGORI = 7

SLOT_KONEKSI = threading.BoundedSemaphore(JUMLAH_KONEKSI)


def baca_kesukaan(nomor_pengguna):
  """Mengembalikan kategori kesukaan satu pengguna, menirukan satu query.

  Slot koneksi diambil lebih dahulu. Bila seluruh slot sedang dipakai, query
  ini menunggu giliran, dan di sanalah antrean basis data terbentuk ketika
  replika di depannya terlalu banyak.
  """
  with SLOT_KONEKSI:
    time.sleep(WAKTU_QUERY_DETIK)
  return [(nomor_pengguna + langkah * JARAK_KATEGORI) % JUMLAH_KATEGORI
          for langkah in range(KATEGORI_PER_PENGGUNA)]


class PenanganQuery(BaseHTTPRequestHandler):
  """Melayani satu jenis query: kategori kesukaan seorang pengguna."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_GET(self):
    """Menjawab GET /kesukaan/<nomor> dengan daftar kategori kesukaannya."""
    bagian = self.path.strip("/").split("/")
    if len(bagian) != 2 or bagian[0] != "kesukaan" or not bagian[1].isdigit():
      self.kirim_json(404, {"pesan": "alamat tidak dikenal"})
      return
    self.kirim_json(200, {"kategori": baca_kesukaan(int(bagian[1]))})

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
  """Menyalakan basis data tiruan sampai dihentikan dengan Ctrl+C."""
  server = ThreadingHTTPServer((HOST, PORT), PenanganQuery)
  kapasitas = JUMLAH_KONEKSI / WAKTU_QUERY_DETIK
  print(f"Basis data tiruan di http://{HOST}:{PORT}/kesukaan/<nomor>, "
        f"{JUMLAH_KONEKSI} koneksi, kapasitas {kapasitas:.0f} query/detik",
        flush=True)
  server.serve_forever()


if __name__ == "__main__":
  main()
