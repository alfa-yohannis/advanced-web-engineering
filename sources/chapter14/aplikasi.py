"""Aplikasi katalog sebagai Progressive Web App di port 8120.

Alamat yang dilayani:
    GET /                      kerangka halaman, statis/index.html
    GET /aplikasi.js, /sw.js   skrip halaman dan service worker
    GET /manifest.webmanifest  manifest aplikasi beserta /ikon.svg
    GET /api/katalog           data katalog, beserta jam pembuatannya
    GET /statistik             jumlah permintaan yang sampai ke server

Seluruh file statis dikirim dengan Cache-Control: no-cache, dan data katalog
dengan no-store. Akibatnya HTTP cache browser tidak pernah menyimpan apa pun
yang dapat dipakai tanpa server, sehingga halaman yang tetap tampil ketika
server mati pasti dilayani service worker, bukan HTTP cache.

Pemakaian (dari sources/chapter14):
    python3 aplikasi.py
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8120
DIREKTORI_STATIS = Path(__file__).parent / "statis"
# Alamat yang dilayani sebagai file, beserta nama file dan jenis isinya.
FILE_STATIS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/aplikasi.js": ("aplikasi.js", "text/javascript; charset=utf-8"),
    "/sw.js": ("sw.js", "text/javascript; charset=utf-8"),
    "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json"),
    "/ikon.svg": ("ikon.svg", "image/svg+xml"),
}
JENIS_ISI_JSON = "application/json"
JUDUL_BUKU = [
    "Basis Data Terapan", "Jaringan Komputer", "Rekayasa Perangkat Lunak",
    "Sistem Operasi", "Struktur Data", "Keamanan Informasi",
    "Pemrograman Web", "Kecerdasan Buatan",
]
HARGA_DASAR_RUPIAH = 85_000
SELISIH_HARGA_RUPIAH = 5_000

# Jumlah permintaan yang sampai ke server, selain /statistik itu sendiri,
# beserta rinciannya per alamat.
PENGHITUNG = {"permintaan": 0, "per_alamat": {}}
KUNCI = threading.Lock()


def data_katalog():
  """Menyusun data katalog beserta jam pembuatannya.

  Jam pembuatan ikut dikirim agar halaman yang tampil dari cache dapat
  menunjukkan setua apa datanya, bukan berpura-pura data itu baru.
  """
  return {
      "dibuat_pada": time.strftime("%H:%M:%S"),
      "buku": [{"judul": judul,
                "harga": HARGA_DASAR_RUPIAH + urutan * SELISIH_HARGA_RUPIAH}
               for urutan, judul in enumerate(JUDUL_BUKU)],
  }


class PenanganPwa(BaseHTTPRequestHandler):
  """Melayani kerangka, service worker, manifest, dan data katalog."""

  protocol_version = "HTTP/1.1"

  def do_GET(self):
    """Mengirim file statis, data katalog, atau statistik permintaan."""
    if self.path == "/statistik":
      with KUNCI:
        self.kirim(200, JENIS_ISI_JSON, json.dumps(PENGHITUNG).encode(),
                   "no-store")
      return
    with KUNCI:
      PENGHITUNG["permintaan"] += 1
      per_alamat = PENGHITUNG["per_alamat"]
      per_alamat[self.path] = per_alamat.get(self.path, 0) + 1
    if self.path == "/api/katalog":
      self.kirim(200, JENIS_ISI_JSON, json.dumps(data_katalog()).encode(),
                 "no-store")
      return
    if self.path in FILE_STATIS:
      nama_file, jenis_isi = FILE_STATIS[self.path]
      isi = (DIREKTORI_STATIS / nama_file).read_bytes()
      self.kirim(200, jenis_isi, isi, "no-cache")
      return
    self.kirim(404, JENIS_ISI_JSON, b'{"pesan": "alamat tidak dikenal"}',
               "no-store")

  def kirim(self, status, jenis_isi, isi, aturan_cache):
    """Mengirim satu response beserta jenis isi dan aturan cache-nya.

    Browser yang ditutup di tengah pengiriman memutus sambungannya. Kejadian
    itu biasa pada pengukuran dengan Chrome tanpa jendela, sehingga tidak
    dilaporkan sebagai error.
    """
    try:
      self.send_response(status)
      self.send_header("Content-Type", jenis_isi)
      self.send_header("Content-Length", str(len(isi)))
      self.send_header("Cache-Control", aturan_cache)
      self.end_headers()
      self.wfile.write(isi)
    except (BrokenPipeError, ConnectionResetError):
      pass

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, agar keluaran pengukuran tidak tenggelam."""


def main():
  """Menyalakan aplikasi sampai dihentikan dengan Ctrl+C."""
  server = ThreadingHTTPServer((HOST, PORT), PenanganPwa)
  print(f"Katalog PWA di http://{HOST}:{PORT}/  (Ctrl+C untuk berhenti)",
        flush=True)
  server.serve_forever()


if __name__ == "__main__":
  main()
