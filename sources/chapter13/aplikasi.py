"""Satu aplikasi dengan tiga cara mengirim peristiwa ke browser.

Alamat yang dilayani:
    POST /kirim          menerbitkan satu peristiwa ke seluruh pelanggan
    GET  /polling?sejak= mengembalikan peristiwa sesudah nomor tertentu
    GET  /sse            aliran Server-Sent Events yang tetap terbuka
    GET  /riwayat        seluruh peristiwa yang pernah terbit

Ketiga cara membaca peristiwa yang sama, sehingga perbedaan biayanya memang
berasal dari cara pengirimannya, bukan dari isinya. WebSocket dilayani proses
terpisah di websocket.py, karena protokolnya berbeda sejak jabat tangan.

Pemakaian (dari sources/chapter13):
    python3 aplikasi.py
"""

import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
PORT = 8100
JENIS_ISI_JSON = "application/json"
JENIS_ISI_SSE = "text/event-stream"
BATAS_ISI_BYTE = 2048
# Batas antrean tiap pelanggan SSE. Pelanggan yang tidak sanggup mengikuti
# tidak boleh membuat server menyimpan peristiwa tanpa batas.
BATAS_ANTREAN_PELANGGAN = 100
# Jeda pengiriman baris penanda hidup. Tanpa itu, sambungan yang lama
# menganggur dapat ditutup perantara di tengah jalan, dan pelanggannya baru
# tahu ketika peristiwa berikutnya tidak pernah tiba.
JEDA_PENANDA_HIDUP_DETIK = 15.0

# Seluruh peristiwa yang pernah terbit, dipakai cara polling, beserta
# daftar antrean milik tiap pelanggan SSE yang sedang tersambung.
RIWAYAT = []
PELANGGAN = []
KUNCI = threading.Lock()


def terbitkan(isi):
  """Mencatat satu peristiwa, lalu menitipkannya ke tiap pelanggan SSE.

  Pencatatan dan penitipan dilakukan di dalam satu kunci, agar nomor
  peristiwa tidak pernah terlewat atau terbalik ketika dua penerbit datang
  bersamaan.
  """
  with KUNCI:
    peristiwa = {"nomor": len(RIWAYAT) + 1, "isi": isi}
    RIWAYAT.append(peristiwa)
    for antrean in list(PELANGGAN):
      if antrean.qsize() < BATAS_ANTREAN_PELANGGAN:
        antrean.put(peristiwa)
  return peristiwa


def sesudah(nomor):
  """Mengambil seluruh peristiwa yang nomornya lebih besar dari nomor itu."""
  with KUNCI:
    return [satu for satu in RIWAYAT if satu["nomor"] > nomor]


class PenanganPeristiwa(BaseHTTPRequestHandler):
  """Melayani penerbitan peristiwa serta kedua cara membacanya."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_POST(self):
    """Menerima satu peristiwa baru, lalu menerbitkannya."""
    if urlparse(self.path).path != "/kirim":
      self.kirim_json(404, {"pesan": "alamat tidak dikenal"})
      return
    panjang = min(int(self.headers.get("Content-Length", "0")),
                  BATAS_ISI_BYTE)
    isi = json.loads(self.rfile.read(panjang) or b"{}")
    self.kirim_json(201, terbitkan(isi))

  def do_GET(self):
    """Melayani polling, aliran SSE, dan riwayat peristiwa."""
    alamat = urlparse(self.path)
    if alamat.path == "/polling":
      nomor = int(parse_qs(alamat.query).get("sejak", ["0"])[0])
      self.kirim_json(200, {"peristiwa": sesudah(nomor)})
      return
    if alamat.path == "/riwayat":
      self.kirim_json(200, {"peristiwa": sesudah(0)})
      return
    if alamat.path == "/sse":
      self.layani_sse()
      return
    self.kirim_json(404, {"pesan": "alamat tidak dikenal"})

  def layani_sse(self):
    """Membuka satu aliran SSE, lalu mengirim tiap peristiwa yang terbit.

    Sambungannya tidak ditutup sampai kliennya pergi. Karena itu panjang
    isinya tidak dapat disebutkan lebih dahulu, dan tiap peristiwa dikirim
    sebagai satu blok data yang diakhiri baris kosong.
    """
    antrean = queue.Queue()
    with KUNCI:
      PELANGGAN.append(antrean)
    self.send_response(200)
    self.send_header("Content-Type", JENIS_ISI_SSE)
    self.send_header("Cache-Control", "no-store")
    self.send_header("Connection", "keep-alive")
    self.end_headers()
    try:
      while True:
        try:
          peristiwa = antrean.get(timeout=JEDA_PENANDA_HIDUP_DETIK)
        except queue.Empty:
          self.wfile.write(b": tetap hidup\n\n")
          self.wfile.flush()
          continue
        blok = (f"id: {peristiwa['nomor']}\n"
                f"data: {json.dumps(peristiwa['isi'])}\n\n")
        self.wfile.write(blok.encode())
        self.wfile.flush()
    except (BrokenPipeError, ConnectionResetError):
      pass
    finally:
      with KUNCI:
        PELANGGAN.remove(antrean)

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
  """Menyalakan server peristiwa sampai dihentikan dengan Ctrl+C."""
  server = ThreadingHTTPServer((HOST, PORT), PenanganPeristiwa)
  print(f"Melayani di http://{HOST}:{PORT}/sse dan /polling"
        "  (Ctrl+C untuk berhenti)")
  server.serve_forever()


if __name__ == "__main__":
  main()
