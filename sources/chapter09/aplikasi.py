"""Layanan katalog yang sudah diinstrumentasi, dipakai sepanjang Bab 9.

Satu proses layanan menjalankan satu versi, dan versinya dibaca dari
environment. Dengan begitu dua versi dapat dinyalakan bersamaan di port
berbeda, lalu dibandingkan lewat reverse proxy, persis seperti rilis
blue-green dan canary.

Tiga keluaran instrumentasi tersedia sekaligus:
    log     baris JSON ke stdout, satu baris per permintaan
    metrik  teks format Prometheus di /metrics
    trace   id dari header traceparent ikut dicatat di tiap baris log

Pemakaian (dari sources/chapter09):
    VERSI=biru PORT=8061 python3 aplikasi.py
    VERSI=hijau PORT=8062 python3 aplikasi.py
"""

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Alamat ikat dibaca dari environment. Di komputer sendiri 127.0.0.1 sudah
# cukup, sedangkan di dalam container alamat itu berarti container itu
# sendiri, sehingga port yang dipublikasikan tidak pernah terjawab.
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8061"))
VERSI = os.environ.get("VERSI", "biru")
# Versi hijau sengaja dibuat sedikit lebih lambat dan sesekali gagal, agar
# rilis canary punya sesuatu untuk dibandingkan.
LAMA_KERJA_DETIK = {"biru": 0.005, "hijau": 0.020}
# Satu dari sekian permintaan versi hijau dijawab 500, meniru cacat yang
# baru ketahuan setelah rilis.
SETIAP_GAGAL = {"biru": 0, "hijau": 25}
JENIS_ISI_JSON = "application/json"
JENIS_ISI_TEKS = "text/plain; charset=utf-8"
# Batas ember histogram, dalam milidetik. Dipilih mengapit nilai yang
# diharapkan, agar p95 terbaca tanpa menyimpan tiap permintaan.
BATAS_EMBER_MS = [5, 10, 25, 50, 100, 250]


class Pencatat:
  """Menyimpan hitungan permintaan, kegagalan, dan sebaran waktunya.

  Disimpan di memori proses, karena yang diajarkan bab ini bentuk metriknya,
  bukan cara menyimpannya. Pada sistem sungguhan angka ini diambil berkala
  oleh pengumpul metrik.
  """

  def __init__(self):
    """Memulai seluruh hitungan dari nol, satu pencatat untuk satu proses."""
    self.jumlah_permintaan = 0
    self.jumlah_gagal = 0
    self.ember = {batas: 0 for batas in BATAS_EMBER_MS}
    self.jumlah_lebih = 0
    self.total_ms = 0.0

  def catat(self, lama_ms, gagal):
    """Mencatat satu permintaan beserta lamanya ke dalam ember yang cocok."""
    self.jumlah_permintaan += 1
    self.total_ms += lama_ms
    if gagal:
      self.jumlah_gagal += 1
    for batas in BATAS_EMBER_MS:
      if lama_ms <= batas:
        self.ember[batas] += 1
        return
    self.jumlah_lebih += 1

  def sebagai_teks_prometheus(self, versi):
    """Menyusun seluruh metrik sebagai teks format Prometheus.

    Format teks dipilih karena dapat dibaca manusia dan alat sekaligus,
    sehingga latihan tidak membutuhkan pengumpul metrik yang berjalan.
    """
    baris = [
        "# HELP permintaan_total Jumlah permintaan yang sudah dilayani.",
        "# TYPE permintaan_total counter",
        f'permintaan_total{{versi="{versi}"}} {self.jumlah_permintaan}',
        "# HELP permintaan_gagal_total Jumlah permintaan yang dijawab 5xx.",
        "# TYPE permintaan_gagal_total counter",
        f'permintaan_gagal_total{{versi="{versi}"}} {self.jumlah_gagal}',
        "# HELP lama_permintaan_ms Sebaran lama permintaan dalam milidetik.",
        "# TYPE lama_permintaan_ms histogram",
    ]
    kumulatif = 0
    for batas in BATAS_EMBER_MS:
      kumulatif += self.ember[batas]
      baris.append(
          f'lama_permintaan_ms_bucket{{versi="{versi}",le="{batas}"}} '
          f"{kumulatif}")
    baris.append(
        f'lama_permintaan_ms_bucket{{versi="{versi}",le="+Inf"}} '
        f"{self.jumlah_permintaan}")
    baris.append(
        f'lama_permintaan_ms_sum{{versi="{versi}"}} {self.total_ms:.1f}')
    baris.append(
        f'lama_permintaan_ms_count{{versi="{versi}"}} {self.jumlah_permintaan}')
    return "\n".join(baris) + "\n"


PENCATAT = Pencatat()

DAFTAR_BUKU = [
    {"judul": "Rekayasa Web Lanjut", "harga": 120000},
    {"judul": "Basis Data Terapan", "harga": 95000},
    {"judul": "Jaringan untuk Pengembang", "harga": 110000},
]


def ambil_trace_id(header_traceparent):
  """Mengambil id trace dari header traceparent menurut W3C Trace Context.

  Bentuk headernya versi-traceid-spanid-flag, dan yang dipakai di sini hanya
  bagian traceid, karena itulah yang menyatukan satu permintaan yang melewati
  beberapa layanan.
  """
  if not header_traceparent:
    return "-"
  bagian = header_traceparent.split("-")
  return bagian[1] if len(bagian) >= 2 else "-"


def tulis_log(baris_log):
  """Menulis satu baris log sebagai JSON ke stdout.

  Satu baris satu peristiwa, sehingga log dapat disaring dan digabungkan
  dengan perkakas teks biasa, tanpa format khusus.
  """
  sys.stdout.write(json.dumps(baris_log) + "\n")
  sys.stdout.flush()


class PenanganLayanan(BaseHTTPRequestHandler):
  """Melayani permintaan katalog sambil mencatat log, metrik, dan trace."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_GET(self):
    """Mengarahkan permintaan, lalu mencatat hasilnya ke ketiga keluaran."""
    if self.path == "/metrics":
      isi = PENCATAT.sebagai_teks_prometheus(VERSI).encode()
      self.kirim(200, isi, JENIS_ISI_TEKS)
      return
    mulai = time.perf_counter()
    status, isi = self.kerjakan_permintaan()
    lama_ms = (time.perf_counter() - mulai) * 1000
    PENCATAT.catat(lama_ms, status >= 500)
    tulis_log({
        "waktu": time.strftime("%H:%M:%S"),
        "versi": VERSI,
        "jalur": self.path,
        "status": status,
        "lama_ms": round(lama_ms, 1),
        "trace_id": ambil_trace_id(self.headers.get("traceparent")),
    })
    self.kirim(status, isi, JENIS_ISI_JSON)

  def kerjakan_permintaan(self):
    """Mengerjakan satu permintaan, lalu mengembalikan status dan isinya.

    Versi hijau sengaja lebih lambat dan sesekali gagal, sehingga perbedaan
    antarversi terbaca dari metrik, bukan dari cerita.
    """
    if self.path == "/sehat":
      return 200, json.dumps({"versi": VERSI, "keadaan": "sehat"}).encode()
    if self.path != "/api/katalog":
      return 404, json.dumps({"pesan": "alamat tidak dikenal"}).encode()
    time.sleep(LAMA_KERJA_DETIK[VERSI])
    setiap = SETIAP_GAGAL[VERSI]
    if setiap and PENCATAT.jumlah_permintaan % setiap == setiap - 1:
      return 500, json.dumps({"pesan": "gagal mengambil katalog"}).encode()
    return 200, json.dumps({"versi": VERSI, "item": DAFTAR_BUKU}).encode()

  def kirim(self, status, isi, jenis_isi):
    """Mengirim satu response lengkap beserta penanda versinya."""
    self.send_response(status)
    self.send_header("Content-Type", jenis_isi)
    self.send_header("Content-Length", str(len(isi)))
    self.send_header("X-Versi", VERSI)
    self.end_headers()
    self.wfile.write(isi)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, karena log terstruktur sudah ditulis sendiri."""


def main():
  """Menyalakan satu versi layanan sampai dihentikan dengan Ctrl+C."""
  server = ThreadingHTTPServer((HOST, PORT), PenanganLayanan)
  tulis_log({"peristiwa": "mulai", "versi": VERSI, "port": PORT})
  server.serve_forever()


if __name__ == "__main__":
  main()
