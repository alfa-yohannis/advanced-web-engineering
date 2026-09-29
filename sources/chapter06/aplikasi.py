"""Aplikasi pesanan yang diuji sepanjang Bab 6.

Tiap response membawa header X-Query-Count berisi jumlah query yang dipakai
permintaan itu. Angka tersebut membuat cacat N+1 terbaca dari luar, sehingga
pengujian dan gate mutu dapat menilainya tanpa membaca kode.

Alamat yang dilayani:
    GET /                        halaman demo untuk pengujian E2E
    GET /aset/<file>             file JavaScript hasil kompilasi
    GET /api/pesanan/<id>        pesanan dengan jumlah query tetap dua
    GET /api/pesanan-n1/<id>     pesanan yang sama dengan pola N+1

Pemakaian (dari sources/chapter06, setelah docker compose up -d):
    source ../.venv/bin/activate
    python aplikasi.py
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import basis_data

HOST = "127.0.0.1"
PORT = 8020
DIREKTORI_STATIS = Path(__file__).parent / "statis"
JENIS_ISI_JSON = "application/json"
JENIS_ISI_HTML = "text/html; charset=utf-8"
JENIS_ISI_JS = "text/javascript"
# Response pengujian tidak boleh tersimpan di mana pun, agar tiap permintaan
# benar-benar menyentuh basis data dan jumlah querynya terbaca apa adanya.
CACHE_CONTROL = "no-store"


class PenanganPesanan(BaseHTTPRequestHandler):
  """Melayani permintaan HTTP untuk halaman demo dan alamat pesanan.

  Header dan isi response ditulis sebagai dua segmen TCP. Tanpa baris
  disable_nagle_algorithm, segmen kedua tertahan sampai ACK segmen pertama
  tiba, dan tiap response kecil menanggung tambahan sekitar 40 milidetik.
  """

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_GET(self):
    """Mengarahkan permintaan ke penangan yang sesuai dengan jalurnya."""
    if self.path == "/":
      self.layani_file_statis("index.html", JENIS_ISI_HTML)
      return
    if self.path.startswith("/aset/"):
      self.layani_file_statis(self.path[len("/aset/"):], JENIS_ISI_JS)
      return
    if self.path.startswith("/api/pesanan-n1/"):
      self.layani_pesanan(self.path.rsplit("/", 1)[-1], n_plus_1=True)
      return
    if self.path.startswith("/api/pesanan/"):
      self.layani_pesanan(self.path.rsplit("/", 1)[-1], n_plus_1=False)
      return
    self.kirim_response(404, b'{"pesan":"alamat tidak dikenal"}',
                       JENIS_ISI_JSON, 0)

  def layani_file_statis(self, nama_file, jenis_isi):
    """Mengirim satu file dari direktori statis, atau 404 bila tidak ada."""
    file_diminta = DIREKTORI_STATIS / nama_file
    if not file_diminta.is_file():
      self.kirim_response(404, b"file tidak ditemukan", JENIS_ISI_HTML, 0)
      return
    self.kirim_response(200, file_diminta.read_bytes(), jenis_isi, 0)

  def layani_pesanan(self, id_teks, n_plus_1):
    """Melayani satu pesanan, lalu melaporkan jumlah querynya lewat header.

    Dua jalur memberi isi response yang sama persis dan hanya berbeda pada
    jumlah querynya. Perbedaan itulah yang diuji pada latihan bab ini.
    """
    if not id_teks.isdigit():
      self.kirim_response(400, b'{"pesan":"id harus angka"}',
                         JENIS_ISI_JSON, 0)
      return
    penghitung = basis_data.PenghitungQuery()
    with basis_data.buka_koneksi() as koneksi:
      if n_plus_1:
        pesanan = basis_data.ambil_pesanan_n_plus_1(koneksi, int(id_teks),
                                                    penghitung)
      else:
        pesanan = basis_data.ambil_pesanan(koneksi, int(id_teks), penghitung)
    if pesanan is None:
      self.kirim_response(404, b'{"pesan":"pesanan tidak ada"}',
                         JENIS_ISI_JSON, penghitung.jumlah)
      return
    isi = json.dumps(pesanan).encode()
    self.kirim_response(200, isi, JENIS_ISI_JSON, penghitung.jumlah)

  def kirim_response(self, status, isi_response, jenis_isi, jumlah_query):
    """Mengirim satu response lengkap beserta jumlah query yang dipakainya."""
    self.send_response(status)
    self.send_header("Content-Type", jenis_isi)
    self.send_header("Content-Length", str(len(isi_response)))
    self.send_header("Cache-Control", CACHE_CONTROL)
    self.send_header("X-Query-Count", str(jumlah_query))
    self.end_headers()
    self.wfile.write(isi_response)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, agar keluaran pengujian tidak tenggelam."""


def main():
  """Menyalakan server sampai dihentikan dengan Ctrl+C."""
  server = ThreadingHTTPServer((HOST, PORT), PenanganPesanan)
  print(f"Melayani di http://{HOST}:{PORT}/  (Ctrl+C untuk berhenti)")
  server.serve_forever()


if __name__ == "__main__":
  main()
