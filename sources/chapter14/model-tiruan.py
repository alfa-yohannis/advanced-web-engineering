"""Model bahasa tiruan: menirukan waktu dan biaya sebuah LLM, bukan isinya.

Yang ditirukan hanya dua sifat yang menentukan rancangan aplikasi di depannya.
Pertama, token pertama baru keluar sesudah WAKTU_TOKEN_PERTAMA_DETIK, lalu
token berikutnya menyusul satu per satu tiap JEDA_ANTARTOKEN_DETIK. Kedua,
tiap permintaan dibayar per token, sehingga jumlah tokennya ikut dilaporkan.

Angka waktunya ditetapkan di file ini, bukan diukur dari model mana pun, dan
dipilih pada orde yang lazim: kurang dari satu detik sampai token pertama,
lalu puluhan token per detik. Akibatnya, yang terukur di depan model ini
adalah akibat rancangan aplikasinya, bukan kecepatan modelnya.

Alamat yang dilayani:
    POST /v1/jawab   isi JSON {"pertanyaan": "...", "stream": true|false}

Kunci API dibaca dari environment KUNCI_MODEL, dan permintaan tanpa kunci yang
sama ditolak, seperti penyedia model sungguhan.

Pemakaian (dari sources/chapter14):
    KUNCI_MODEL=kunci-latihan python3 model-tiruan.py
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8122
KUNCI_MODEL = os.environ.get("KUNCI_MODEL", "")
WAKTU_TOKEN_PERTAMA_DETIK = 0.6
JEDA_ANTARTOKEN_DETIK = 0.02
JUMLAH_TOKEN_JAWABAN = 120
BATAS_ISI_BYTE = 4096
JENIS_ISI_JSON = "application/json"
JENIS_ISI_SSE = "text/event-stream"
KATA_JAWABAN = ("Jawaban tiruan ini hanya membawa jumlah token yang tetap "
                "agar waktunya dapat dibandingkan").split()


def buat_token():
  """Menyusun token jawaban yang panjangnya tetap, apa pun pertanyaannya."""
  return [KATA_JAWABAN[urutan % len(KATA_JAWABAN)] + " "
          for urutan in range(JUMLAH_TOKEN_JAWABAN)]


def hitung_token_masuk(pertanyaan):
  """Menaksir jumlah token pertanyaan dengan menghitung kata.

  Penyedia sungguhan memakai tokenizer sendiri, sehingga jumlahnya berbeda.
  Taksiran ini cukup untuk membandingkan biaya antarskenario.
  """
  return len(pertanyaan.split())


class PenanganModel(BaseHTTPRequestHandler):
  """Menjawab pertanyaan dengan atau tanpa streaming, setelah memeriksa kunci."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_POST(self):
    """Membaca isi permintaan, memeriksa kunci, lalu mengirim jawabannya.

    Isi permintaan selalu dibaca lebih dahulu, termasuk ketika permintaannya
    akan ditolak. Isi yang dibiarkan tidak terbaca akan dikira permintaan
    berikutnya pada sambungan yang sama.
    """
    panjang = min(int(self.headers.get("Content-Length", "0")), BATAS_ISI_BYTE)
    isi_mentah = self.rfile.read(panjang)
    if self.path != "/v1/jawab":
      self.kirim_json(404, {"pesan": "alamat tidak dikenal"})
      return
    if self.headers.get("Authorization") != f"Bearer {KUNCI_MODEL}":
      self.kirim_json(401, {"pesan": "kunci API salah"})
      return
    isi = json.loads(isi_mentah or b"{}")
    pertanyaan = isi.get("pertanyaan", "")
    token = buat_token()
    pemakaian = {"token_masuk": hitung_token_masuk(pertanyaan),
                 "token_keluar": len(token)}
    if isi.get("stream"):
      self.kirim_stream(token, pemakaian)
      return
    time.sleep(WAKTU_TOKEN_PERTAMA_DETIK
               + JEDA_ANTARTOKEN_DETIK * (len(token) - 1))
    self.kirim_json(200, {"jawaban": "".join(token), **pemakaian})

  def kirim_stream(self, token, pemakaian):
    """Mengirim token satu per satu sebagai aliran Server-Sent Events.

    Peristiwa terakhir membawa jumlah token, karena biayanya baru diketahui
    setelah jawabannya selesai.
    """
    self.send_response(200)
    self.send_header("Content-Type", JENIS_ISI_SSE)
    self.send_header("Cache-Control", "no-store")
    self.send_header("Connection", "close")
    self.end_headers()
    time.sleep(WAKTU_TOKEN_PERTAMA_DETIK)
    for urutan, satu_token in enumerate(token):
      if urutan:
        time.sleep(JEDA_ANTARTOKEN_DETIK)
      self.tulis_peristiwa({"token": satu_token})
    self.tulis_peristiwa({"selesai": True, **pemakaian})
    self.close_connection = True

  def tulis_peristiwa(self, isi):
    """Menulis satu peristiwa SSE, lalu langsung mengirimkannya."""
    self.wfile.write(f"data: {json.dumps(isi)}\n\n".encode())
    self.wfile.flush()

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
  """Menyalakan model tiruan sampai dihentikan dengan Ctrl+C."""
  if not KUNCI_MODEL:
    raise SystemExit("Isi environment KUNCI_MODEL lebih dahulu, misalnya "
                     "KUNCI_MODEL=kunci-latihan python3 model-tiruan.py")
  server = ThreadingHTTPServer((HOST, PORT), PenanganModel)
  print(f"Model tiruan di http://{HOST}:{PORT}/v1/jawab, token pertama "
        f"{WAKTU_TOKEN_PERTAMA_DETIK} detik, {JUMLAH_TOKEN_JAWABAN} token",
        flush=True)
  server.serve_forever()


if __name__ == "__main__":
  main()
