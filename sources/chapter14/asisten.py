"""Asisten katalog: fitur berbantuan LLM yang dijalankan di sisi server.

Browser tidak pernah berbicara langsung dengan model. Ia bertanya ke sini, dan
server inilah yang memegang kunci API, meneruskan pertanyaannya, lalu
mengalirkan jawabannya kembali. Dengan cara itu kunci API tidak pernah sampai
ke browser, dan seluruh pemakaian token tercatat di satu tempat.

Jawaban disimpan di cache menurut pertanyaannya. Pencocokannya persis, setelah
huruf besar-kecil dan spasi dirapikan, sehingga pertanyaan yang sama persis
tidak dibayar dua kali. Pertanyaan yang maknanya sama tetapi kalimatnya lain
tetap dianggap baru. Cache hidup selama prosesnya hidup.

Alamat yang dilayani:
    GET /tanya?q=...&stream=1   jawaban sebagai aliran Server-Sent Events
    GET /tanya?q=...&stream=0   jawaban utuh sebagai JSON
    GET /biaya                  jumlah token yang sudah dibayar ke model

Pemakaian (dari sources/chapter14, setelah model-tiruan.py menyala):
    KUNCI_MODEL=kunci-latihan python3 asisten.py
"""

import json
import os
import threading
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
PORT = 8121
PORT_MODEL = 8122
KUNCI_MODEL = os.environ.get("KUNCI_MODEL", "")
BATAS_WAKTU_DETIK = 30
JENIS_ISI_JSON = "application/json"
JENIS_ISI_SSE = "text/event-stream"
AWALAN_DATA = "data: "

# Jawaban yang sudah pernah dibayar, dengan pertanyaan yang dirapikan sebagai
# kuncinya, beserta jumlah token yang sudah dibayar sejak proses menyala.
CACHE_JAWABAN = {}
BIAYA = {"token_dibayar": 0}
KUNCI = threading.Lock()


def rapikan(pertanyaan):
  """Merapikan pertanyaan menjadi kunci cache: huruf kecil, spasi tunggal."""
  return " ".join(pertanyaan.lower().split())


def catat_jawaban(kunci_cache, jawaban, pemakaian):
  """Menyimpan jawaban ke cache, lalu menambahkan tokennya ke biaya."""
  dibayar = pemakaian["token_masuk"] + pemakaian["token_keluar"]
  with KUNCI:
    CACHE_JAWABAN[kunci_cache] = jawaban
    BIAYA["token_dibayar"] += dibayar
  return dibayar


def tanya_model(pertanyaan, stream):
  """Mengirim pertanyaan ke model beserta kunci API, mengembalikan response.

  Kunci API hanya ada di environment proses ini. Ia ditambahkan di sini,
  pada sisi server, sehingga tidak pernah ikut terkirim ke browser.
  """
  koneksi = HTTPConnection(HOST, PORT_MODEL, timeout=BATAS_WAKTU_DETIK)
  badan = json.dumps({"pertanyaan": pertanyaan, "stream": stream}).encode()
  koneksi.request("POST", "/v1/jawab", body=badan, headers={
      "Authorization": f"Bearer {KUNCI_MODEL}",
      "Content-Type": JENIS_ISI_JSON,
      "Content-Length": str(len(badan)),
  })
  return koneksi.getresponse()


class PenanganAsisten(BaseHTTPRequestHandler):
  """Meneruskan pertanyaan ke model, atau menjawabnya dari cache."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_GET(self):
    """Melayani pertanyaan dan laporan biaya."""
    alamat = urlparse(self.path)
    if alamat.path == "/biaya":
      with KUNCI:
        self.kirim_json(200, dict(BIAYA))
      return
    if alamat.path != "/tanya":
      self.kirim_json(404, {"pesan": "alamat tidak dikenal"})
      return
    argumen = parse_qs(alamat.query)
    pertanyaan = argumen.get("q", [""])[0]
    stream = argumen.get("stream", ["1"])[0] == "1"
    kunci_cache = rapikan(pertanyaan)
    with KUNCI:
      tersimpan = CACHE_JAWABAN.get(kunci_cache)
    if tersimpan is not None:
      self.jawab_dari_cache(tersimpan, stream)
      return
    if stream:
      self.alirkan_dari_model(pertanyaan, kunci_cache)
      return
    isi = json.loads(tanya_model(pertanyaan, False).read())
    dibayar = catat_jawaban(kunci_cache, isi["jawaban"], isi)
    self.kirim_json(200, {"jawaban": isi["jawaban"], "token_dibayar": dibayar},
                    "MISS")

  def jawab_dari_cache(self, jawaban, stream):
    """Mengirim jawaban yang sudah tersimpan, tanpa memanggil model."""
    if not stream:
      self.kirim_json(200, {"jawaban": jawaban, "token_dibayar": 0}, "HIT")
      return
    self.mulai_aliran("HIT")
    self.tulis_peristiwa({"token": jawaban})
    self.tulis_peristiwa({"selesai": True, "token_dibayar": 0})

  def alirkan_dari_model(self, pertanyaan, kunci_cache):
    """Meneruskan tiap token dari model ke browser begitu token itu tiba.

    Token tidak ditampung dulu sampai lengkap, karena justru itulah yang
    membuat pengguna melihat awal jawaban jauh sebelum jawabannya selesai.
    """
    response = tanya_model(pertanyaan, True)
    self.mulai_aliran("MISS")
    potongan_jawaban = []
    for baris_mentah in response:
      baris = baris_mentah.decode().strip()
      if not baris.startswith(AWALAN_DATA):
        continue
      isi = json.loads(baris[len(AWALAN_DATA):])
      if "token" in isi:
        potongan_jawaban.append(isi["token"])
        self.tulis_peristiwa(isi)
        continue
      dibayar = catat_jawaban(kunci_cache, "".join(potongan_jawaban), isi)
      self.tulis_peristiwa({"selesai": True, "token_dibayar": dibayar})

  def mulai_aliran(self, keadaan_cache):
    """Mengirim header aliran SSE beserta keterangan HIT atau MISS."""
    self.send_response(200)
    self.send_header("Content-Type", JENIS_ISI_SSE)
    self.send_header("Cache-Control", "no-store")
    self.send_header("X-Cache", keadaan_cache)
    self.send_header("Connection", "close")
    self.end_headers()
    self.close_connection = True

  def tulis_peristiwa(self, isi):
    """Menulis satu peristiwa SSE ke browser, lalu langsung mengirimkannya."""
    self.wfile.write(f"{AWALAN_DATA}{json.dumps(isi)}\n\n".encode())
    self.wfile.flush()

  def kirim_json(self, status, isi, keadaan_cache="-"):
    """Mengirim satu response JSON beserta keterangan cache-nya."""
    badan = json.dumps(isi).encode()
    self.send_response(status)
    self.send_header("Content-Type", JENIS_ISI_JSON)
    self.send_header("Content-Length", str(len(badan)))
    self.send_header("X-Cache", keadaan_cache)
    self.end_headers()
    self.wfile.write(badan)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, agar keluaran pengukuran tidak tenggelam."""


def main():
  """Menyalakan asisten sampai dihentikan dengan Ctrl+C."""
  if not KUNCI_MODEL:
    raise SystemExit("Isi environment KUNCI_MODEL lebih dahulu, misalnya "
                     "KUNCI_MODEL=kunci-latihan python3 asisten.py")
  server = ThreadingHTTPServer((HOST, PORT), PenanganAsisten)
  print(f"Asisten di http://{HOST}:{PORT}/tanya?q=...  (Ctrl+C untuk berhenti)",
        flush=True)
  server.serve_forever()


if __name__ == "__main__":
  main()
