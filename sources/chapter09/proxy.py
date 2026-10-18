"""Reverse proxy yang membagi permintaan ke dua versi layanan.

Pembagiannya dibaca dari rilis.json, sehingga rilis blue-green, canary, dan
rollback cukup dilakukan dengan mengubah satu angka di file itu, tanpa
menyentuh kode dan tanpa menyalakan ulang layanan mana pun.

Proxy ini juga yang membuat trace id. Id tersebut dikirim ke layanan lewat
header traceparent menurut W3C Trace Context, lalu ikut dicatat kedua pihak,
sehingga satu permintaan dapat ditelusuri melintasi dua proses.

Pemakaian (dari sources/chapter09, setelah kedua layanan menyala):
    python3 proxy.py
"""

import json
import os
import secrets
import sys
import time
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT_PROXY", "8060"))
FILE_RILIS = Path(__file__).parent / "rilis.json"
BATAS_WAKTU_DETIK = 5
PANJANG_TRACE_ID = 16
PANJANG_SPAN_ID = 8


def baca_rilis():
  """Membaca pembagian rilis, yaitu satu-satunya tempat bobot ditulis.

  File dibaca pada tiap permintaan, sehingga mengubah bobot langsung berlaku
  tanpa menyalakan ulang proxy. Pada sistem sungguhan nilainya datang dari
  tempat setelan terpusat.
  """
  return json.loads(FILE_RILIS.read_text(encoding="utf-8"))


def pilih_tujuan(rilis, nomor_permintaan):
  """Memilih versi tujuan menurut bobot pada file rilis.

  Pemilihannya berurutan, bukan acak, supaya hasilnya dapat diulang: dari
  tiap seratus permintaan, tepat sebanyak bobot yang menuju versi kedua.
  """
  bobot_kedua = rilis["bobot_persen_kedua"]
  if nomor_permintaan % 100 < bobot_kedua:
    return rilis["versi_kedua"]
  return rilis["versi_pertama"]


def buat_traceparent():
  """Membuat header traceparent baru menurut W3C Trace Context.

  Bentuknya 00-<trace id>-<span id>-01, dengan trace id sebagai penanda satu
  permintaan dari awal sampai akhir.
  """
  trace_id = secrets.token_hex(PANJANG_TRACE_ID)
  span_id = secrets.token_hex(PANJANG_SPAN_ID)
  return f"00-{trace_id}-{span_id}-01", trace_id


def teruskan(tujuan, jalur, traceparent):
  """Meneruskan satu permintaan ke layanan tujuan, lalu membawa balik hasilnya."""
  koneksi = HTTPConnection(tujuan["host"], tujuan["port"],
                           timeout=BATAS_WAKTU_DETIK)
  koneksi.request("GET", jalur, headers={"traceparent": traceparent})
  response = koneksi.getresponse()
  isi = response.read()
  status = response.status
  koneksi.close()
  return status, isi


def tulis_log(baris_log):
  """Menulis satu baris log proxy sebagai JSON ke stdout."""
  sys.stdout.write(json.dumps(baris_log) + "\n")
  sys.stdout.flush()


class PenanganProxy(BaseHTTPRequestHandler):
  """Meneruskan permintaan ke salah satu versi menurut bobot rilis."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_GET(self):
    """Memilih tujuan, meneruskan permintaan, lalu mencatat hasilnya."""
    mulai = time.perf_counter()
    rilis = baca_rilis()
    tujuan = pilih_tujuan(rilis, self.server.nomor_permintaan)
    self.server.nomor_permintaan += 1
    traceparent, trace_id = buat_traceparent()
    status, isi = teruskan(tujuan, self.path, traceparent)
    lama_ms = (time.perf_counter() - mulai) * 1000
    tulis_log({
        "waktu": time.strftime("%H:%M:%S"),
        "peran": "proxy",
        "tujuan": tujuan["nama"],
        "jalur": self.path,
        "status": status,
        "lama_ms": round(lama_ms, 1),
        "trace_id": trace_id,
    })
    self.send_response(status)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(isi)))
    self.send_header("X-Dilayani", tujuan["nama"])
    self.send_header("X-Trace-Id", trace_id)
    self.end_headers()
    self.wfile.write(isi)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, karena log terstruktur sudah ditulis sendiri."""


class ServerProxy(ThreadingHTTPServer):
  """Server proxy yang menghitung permintaan agar pembagiannya berurutan."""

  def __init__(self, alamat, kelas_penangan):
    """Memulai hitungan permintaan dari nol."""
    super().__init__(alamat, kelas_penangan)
    self.nomor_permintaan = 0


def main():
  """Menyalakan proxy sampai dihentikan dengan Ctrl+C."""
  rilis = baca_rilis()
  server = ServerProxy((HOST, PORT), PenanganProxy)
  tulis_log({"peristiwa": "mulai", "peran": "proxy", "port": PORT,
             "bobot_persen_kedua": rilis["bobot_persen_kedua"]})
  server.serve_forever()


if __name__ == "__main__":
  main()
