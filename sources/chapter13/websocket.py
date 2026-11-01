"""Server WebSocket yang menyiarkan peristiwa dari aplikasi ke pelanggannya.

Peristiwa diambil dari aplikasi di port 8100 lewat aliran SSE-nya, lalu
disiarkan ke seluruh pelanggan WebSocket. Pembagian itu disengaja: yang
dibandingkan bab ini adalah cara mengirim ke klien, sedangkan sumber
peristiwanya tetap satu. Aliran SSE dipilih sebagai sumber, bukan polling,
agar keterlambatan yang terukur tidak ditambah jeda pengambilan sendiri.

Pemakaian (dari sources/chapter13, setelah aplikasi.py menyala):
    python3 websocket.py
"""

import json
import socket
import threading
import time
from http.client import HTTPConnection

import websocket_sederhana

HOST = "127.0.0.1"
PORT = 8101
HOST_APLIKASI = "127.0.0.1"
PORT_APLIKASI = 8100
BATAS_WAKTU_DETIK = 60
JUMLAH_ANTREAN_SOKET = 16
# Jeda sebelum menyambung ulang ke aplikasi. Sambungan yang putus bukan hal
# luar biasa, sehingga pengambilnya menyambung ulang, bukan berhenti.
JEDA_SAMBUNG_ULANG_DETIK = 1.0

PELANGGAN = []
KUNCI = threading.Lock()


def jabat_tangan(sambungan):
  """Menjawab jabat tangan WebSocket, lalu True bila jabatannya sah."""
  permintaan = b""
  while b"\r\n\r\n" not in permintaan:
    potongan = sambungan.recv(1024)
    if not potongan:
      return False
    permintaan += potongan
  kunci = ""
  for baris in permintaan.decode(errors="replace").split("\r\n"):
    if baris.lower().startswith("sec-websocket-key:"):
      kunci = baris.split(":", 1)[1].strip()
  if not kunci:
    return False
  jawaban = (
      "HTTP/1.1 101 Switching Protocols\r\n"
      "Upgrade: websocket\r\n"
      "Connection: Upgrade\r\n"
      f"Sec-WebSocket-Accept: "
      f"{websocket_sederhana.jawaban_jabat_tangan(kunci)}\r\n\r\n"
  )
  sambungan.sendall(jawaban.encode())
  return True


def layani_pelanggan(sambungan):
  """Melayani satu pelanggan sampai sambungannya ditutup."""
  if not jabat_tangan(sambungan):
    sambungan.close()
    return
  with KUNCI:
    PELANGGAN.append(sambungan)
  try:
    while True:
      teks, _ = websocket_sederhana.baca_frame(sambungan)
      if teks is None:
        break
  except OSError:
    pass
  finally:
    with KUNCI:
      if sambungan in PELANGGAN:
        PELANGGAN.remove(sambungan)
    sambungan.close()


def siarkan(peristiwa):
  """Mengirim satu peristiwa ke seluruh pelanggan yang masih tersambung."""
  bingkai = websocket_sederhana.susun_frame(json.dumps(peristiwa), False)
  with KUNCI:
    daftar = list(PELANGGAN)
  for sambungan in daftar:
    try:
      sambungan.sendall(bingkai)
    except OSError:
      with KUNCI:
        if sambungan in PELANGGAN:
          PELANGGAN.remove(sambungan)


def ikuti_aliran():
  """Mengikuti aliran SSE aplikasi, lalu menyiarkan tiap peristiwa yang tiba.

  Dua baris SSE menyusun satu peristiwa, yaitu baris id dan baris data.
  Keduanya dikumpulkan dahulu, lalu dikirim sebagai satu frame WebSocket.
  Baris penanda hidup diabaikan, karena isinya memang bukan peristiwa.
  """
  koneksi = HTTPConnection(HOST_APLIKASI, PORT_APLIKASI,
                           timeout=BATAS_WAKTU_DETIK)
  koneksi.request("GET", "/sse")
  response = koneksi.getresponse()
  nomor = 0
  while True:
    baris = response.fp.readline()
    if not baris:
      return
    teks = baris.decode().strip()
    if teks.startswith("id: "):
      nomor = int(teks[4:])
    elif teks.startswith("data: ") and nomor:
      siarkan({"nomor": nomor, "isi": json.loads(teks[6:])})


def jalankan_pengambil():
  """Mengikuti aliran aplikasi, dan menyambung ulang ketika terputus."""
  while True:
    try:
      ikuti_aliran()
    except (OSError, ValueError):
      pass
    time.sleep(JEDA_SAMBUNG_ULANG_DETIK)


def main():
  """Menyalakan server WebSocket beserta pengambil peristiwanya."""
  threading.Thread(target=jalankan_pengambil, daemon=True).start()
  pendengar = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  pendengar.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  pendengar.bind((HOST, PORT))
  pendengar.listen(JUMLAH_ANTREAN_SOKET)
  print(f"WebSocket di ws://{HOST}:{PORT}/  (Ctrl+C untuk berhenti)")
  while True:
    sambungan, _ = pendengar.accept()
    threading.Thread(target=layani_pelanggan, args=(sambungan,),
                     daemon=True).start()


if __name__ == "__main__":
  main()
