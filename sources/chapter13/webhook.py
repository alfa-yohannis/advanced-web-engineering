"""Penerima webhook yang sengaja gagal dua kali untuk satu jenis pekerjaan.

Alamat yang dilayani:
    POST /webhook      menerima satu pengiriman dari worker
    GET  /pengiriman   seluruh pengiriman yang pernah tiba, beserta waktunya
    POST /reset        mengosongkan catatan, dipakai sebelum mengukur

Kegagalan yang disengaja itulah gunanya file ini. Tanpa tujuan yang kadang
gagal, retry dan jeda yang berlipat tidak pernah terlihat bekerja.

Pemakaian (dari sources/chapter13):
    python3 webhook.py
"""

import json
import time
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8102
JENIS_ISI_JSON = "application/json"
BATAS_ISI_BYTE = 2048
# Jenis pekerjaan yang dua percobaan pertamanya ditolak, lalu diterima.
JENIS_GAGAL_AWAL = "gagal-dua-kali"
JUMLAH_GAGAL_AWAL = 2

PENGIRIMAN = []
PERCOBAAN = defaultdict(int)


def catat(isi):
  """Mencatat satu pengiriman, lalu memutuskan status jawabannya.

  Keputusannya hanya bergantung pada jenis pekerjaan dan nomor percobaannya,
  sehingga hasil pengukuran dapat diulang dengan angka yang sama.
  """
  id_pesan = isi.get("id", "tanpa-id")
  PERCOBAAN[id_pesan] += 1
  percobaan = PERCOBAAN[id_pesan]
  gagal = (isi.get("jenis") == JENIS_GAGAL_AWAL
           and percobaan <= JUMLAH_GAGAL_AWAL)
  status = 500 if gagal else 200
  PENGIRIMAN.append({"id": id_pesan, "jenis": isi.get("jenis"),
                     "percobaan": percobaan, "status": status,
                     "waktu": time.time()})
  return status


class PenanganWebhook(BaseHTTPRequestHandler):
  """Menerima pengiriman dari worker, lalu mencatat dan menjawabnya."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_POST(self):
    """Melayani penerimaan pengiriman dan pengosongan catatan."""
    if self.path == "/reset":
      PENGIRIMAN.clear()
      PERCOBAAN.clear()
      self.kirim_json(200, {"dikosongkan": True})
      return
    if self.path != "/webhook":
      self.kirim_json(404, {"pesan": "alamat tidak dikenal"})
      return
    panjang = min(int(self.headers.get("Content-Length", "0")),
                  BATAS_ISI_BYTE)
    isi = json.loads(self.rfile.read(panjang) or b"{}")
    status = catat(isi)
    self.kirim_json(status, {"diterima": status == 200,
                             "percobaan": PERCOBAAN[isi.get("id")]})

  def do_GET(self):
    """Mengembalikan seluruh catatan pengiriman."""
    if self.path != "/pengiriman":
      self.kirim_json(404, {"pesan": "alamat tidak dikenal"})
      return
    self.kirim_json(200, {"pengiriman": PENGIRIMAN})

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
  """Menyalakan penerima webhook sampai dihentikan dengan Ctrl+C."""
  server = ThreadingHTTPServer((HOST, PORT), PenanganWebhook)
  print(f"Webhook di http://{HOST}:{PORT}/webhook, dua percobaan pertama "
        f"jenis {JENIS_GAGAL_AWAL} ditolak  (Ctrl+C untuk berhenti)")
  server.serve_forever()


if __name__ == "__main__":
  main()
