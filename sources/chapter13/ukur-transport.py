"""Membandingkan polling, SSE, dan WebSocket pada peristiwa yang sama.

Tiga hal diukur untuk tiap transport: keterlambatan dari saat peristiwa
diterbitkan sampai diterima klien, jumlah byte yang diterima klien, dan
jumlah permintaan HTTP yang dipakai. Peristiwanya sama, jumlahnya sama, dan
yang berbeda hanya cara mengirimnya.

Pengukuran ini bersifat mengamati dan hanya diarahkan ke aplikasi sendiri di
127.0.0.1.

Pemakaian (dari sources/chapter13, setelah aplikasi.py dan websocket.py
menyala):
    python3 ukur-transport.py
"""

import base64
import json
import os
import socket
import statistics
import threading
import time
from http.client import HTTPConnection

import websocket_sederhana

HOST = "127.0.0.1"
PORT = 8100
PORT_WEBSOCKET = 8101
BATAS_WAKTU_DETIK = 10
JUMLAH_PERISTIWA = 10
# Jeda polling. Nilainya yang menentukan keterlambatan rata-rata varian
# polling, yaitu sekitar setengah jeda ini.
JEDA_POLLING_DETIK = 0.5
JEDA_TUNGGU_DETIK = 0.002
JEDA_ANTARPENERBITAN_DETIK = 0.3
LEBAR_NAMA = 11


def terbitkan(nomor):
  """Menerbitkan satu peristiwa, lalu mengembalikan waktu penerbitannya."""
  koneksi = HTTPConnection(HOST, PORT, timeout=BATAS_WAKTU_DETIK)
  badan = json.dumps({"pesan": f"peristiwa-{nomor}"}).encode()
  mulai = time.monotonic()
  koneksi.request("POST", "/kirim", body=badan,
                  headers={"Content-Type": "application/json",
                           "Content-Length": str(len(badan))})
  koneksi.getresponse().read()
  koneksi.close()
  return mulai


def nomor_awal():
  """Mengambil nomor peristiwa terakhir, agar pengukuran dimulai dari sana."""
  koneksi = HTTPConnection(HOST, PORT, timeout=BATAS_WAKTU_DETIK)
  koneksi.request("GET", "/riwayat")
  isi = json.loads(koneksi.getresponse().read())
  koneksi.close()
  return isi["peristiwa"][-1]["nomor"] if isi["peristiwa"] else 0


def langganan_polling(keadaan):
  """Mengambil peristiwa baru berulang kali dengan jeda tetap.

  Permintaan yang tidak membawa peristiwa apa pun ikut dihitung, karena
  biaya itulah yang membedakan polling dari transport yang mendorong.
  """
  terakhir = keadaan["mulai_nomor"]
  while not keadaan["berhenti"].is_set():
    koneksi = HTTPConnection(HOST, PORT, timeout=BATAS_WAKTU_DETIK)
    koneksi.request("GET", f"/polling?sejak={terakhir}")
    mentah = koneksi.getresponse().read()
    koneksi.close()
    keadaan["byte"] += len(mentah)
    keadaan["permintaan"] += 1
    for peristiwa in json.loads(mentah)["peristiwa"]:
      terakhir = peristiwa["nomor"]
      keadaan["terima"][peristiwa["nomor"]] = time.monotonic()
    keadaan["berhenti"].wait(JEDA_POLLING_DETIK)


def langganan_sse(keadaan):
  """Membuka satu aliran SSE, lalu mencatat tiap blok data yang tiba."""
  koneksi = HTTPConnection(HOST, PORT, timeout=BATAS_WAKTU_DETIK)
  koneksi.request("GET", "/sse")
  response = koneksi.getresponse()
  keadaan["permintaan"] += 1
  nomor_terakhir = 0
  while not keadaan["berhenti"].is_set():
    baris = response.fp.readline()
    if not baris:
      break
    keadaan["byte"] += len(baris)
    teks = baris.decode().strip()
    if teks.startswith("id: "):
      nomor_terakhir = int(teks[4:])
    elif teks.startswith("data: ") and nomor_terakhir:
      keadaan["terima"][nomor_terakhir] = time.monotonic()
  koneksi.close()


def langganan_websocket(keadaan):
  """Menyambung ke server WebSocket, lalu mencatat tiap frame yang tiba."""
  sambungan = socket.create_connection((HOST, PORT_WEBSOCKET),
                                       timeout=BATAS_WAKTU_DETIK)
  kunci = base64.b64encode(os.urandom(16)).decode()
  permintaan = (
      f"GET / HTTP/1.1\r\nHost: {HOST}:{PORT_WEBSOCKET}\r\n"
      "Upgrade: websocket\r\nConnection: Upgrade\r\n"
      f"Sec-WebSocket-Key: {kunci}\r\nSec-WebSocket-Version: 13\r\n\r\n"
  )
  sambungan.sendall(permintaan.encode())
  jawaban = b""
  while b"\r\n\r\n" not in jawaban:
    jawaban += sambungan.recv(1024)
  keadaan["permintaan"] += 1
  while not keadaan["berhenti"].is_set():
    teks, byte_terpakai = websocket_sederhana.baca_frame(sambungan)
    if teks is None:
      break
    keadaan["byte"] += byte_terpakai
    peristiwa = json.loads(teks)
    keadaan["terima"][peristiwa["nomor"]] = time.monotonic()
  sambungan.close()


def tunggu_peristiwa(keadaan, nomor):
  """Menunggu satu nomor peristiwa tiba, lalu mengembalikan waktu tibanya."""
  batas = time.monotonic() + BATAS_WAKTU_DETIK
  while time.monotonic() < batas:
    if nomor in keadaan["terima"]:
      return keadaan["terima"][nomor]
    time.sleep(JEDA_TUNGGU_DETIK)
  raise SystemExit(f"peristiwa {nomor} tidak pernah tiba")


def ukur_transport(nama, pelanggan):
  """Mengukur satu transport dengan menerbitkan sejumlah peristiwa."""
  keadaan = {"terima": {}, "byte": 0, "permintaan": 0,
             "berhenti": threading.Event(), "mulai_nomor": nomor_awal()}
  utas = threading.Thread(target=pelanggan, args=(keadaan,), daemon=True)
  utas.start()
  time.sleep(JEDA_POLLING_DETIK)
  keterlambatan = []
  for urutan in range(JUMLAH_PERISTIWA):
    nomor = keadaan["mulai_nomor"] + urutan + 1
    terbit = terbitkan(nomor)
    keterlambatan.append((tunggu_peristiwa(keadaan, nomor) - terbit) * 1000)
    time.sleep(JEDA_ANTARPENERBITAN_DETIK)
  keadaan["berhenti"].set()
  return {
      "nama": nama,
      "tengah_ms": statistics.median(keterlambatan),
      "tertinggi_ms": max(keterlambatan),
      "byte": keadaan["byte"],
      "permintaan": keadaan["permintaan"],
  }


def main():
  """Mengukur ketiga transport, lalu mencetak hasilnya sebagai satu tabel."""
  hasil = [
      ukur_transport("polling", langganan_polling),
      ukur_transport("sse", langganan_sse),
      ukur_transport("websocket", langganan_websocket),
  ]
  print(f"  {'Transport':<{LEBAR_NAMA}} {'Peristiwa':>9} {'Tengah ms':>10} "
        f"{'Tertinggi':>10} {'Byte':>8} {'Permintaan':>11}")
  for satu in hasil:
    print(f"  {satu['nama']:<{LEBAR_NAMA}} {JUMLAH_PERISTIWA:>9} "
          f"{satu['tengah_ms']:>10.1f} {satu['tertinggi_ms']:>10.1f} "
          f"{satu['byte']:>8} {satu['permintaan']:>11}")


if __name__ == "__main__":
  main()
