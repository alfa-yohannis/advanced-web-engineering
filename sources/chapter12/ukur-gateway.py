"""Mengukur perilaku rate limiting di gateway, termasuk pengisian ulangnya.

Tiga hal diukur. Pertama, satu lonjakan permintaan: berapa yang dilayani
sampai ember token habis. Kedua, isi header Retry-After saat ditolak.
Ketiga, keadaan sesudah menunggu: berapa token yang sudah terisi kembali.

Pengukuran ini bersifat mengamati dan hanya diarahkan ke gateway sendiri di
127.0.0.1.

Pemakaian (dari sources/chapter12, setelah aplikasi.py dan gateway.py
menyala):
    python3 ukur-gateway.py
"""

import time
from http.client import HTTPConnection

HOST = "127.0.0.1"
PORT = 8091
BATAS_WAKTU_DETIK = 5
JALUR = "/v1/buku?per_halaman=1"
JUMLAH_LONJAKAN = 30
JEDA_DETIK = 2.0
LEBAR_TAHAP = 30


def satu_permintaan(nama_klien):
  """Mengirim satu permintaan ke gateway, lalu mengembalikan statusnya."""
  koneksi = HTTPConnection(HOST, PORT, timeout=BATAS_WAKTU_DETIK)
  koneksi.request("GET", JALUR, headers={"X-Klien": nama_klien})
  response = koneksi.getresponse()
  response.read()
  hasil = (response.status, response.getheader("Retry-After"))
  koneksi.close()
  return hasil


def lonjakan(nama_klien, jumlah):
  """Mengirim sejumlah permintaan secepat mungkin, lalu merangkum hasilnya."""
  diterima = 0
  ditolak = 0
  retry_after = None
  mulai = time.monotonic()
  for _ in range(jumlah):
    status, tunggu = satu_permintaan(nama_klien)
    if status == 200:
      diterima += 1
    else:
      ditolak += 1
      retry_after = retry_after or tunggu
  lama = time.monotonic() - mulai
  return {"diterima": diterima, "ditolak": ditolak,
          "retry_after": retry_after or "-", "lama_detik": lama}


def main():
  """Mengukur lonjakan, menunggu, lalu mengukur lonjakan kedua."""
  print(f"  {'Tahap':<{LEBAR_TAHAP}} {'200':>5} {'429':>5} "
        f"{'Retry-After':>12} {'Lama detik':>11}")
  pertama = lonjakan("klien-ukur", JUMLAH_LONJAKAN)
  print(f"  {f'{JUMLAH_LONJAKAN} permintaan sekaligus':<{LEBAR_TAHAP}} "
        f"{pertama['diterima']:>5} {pertama['ditolak']:>5} "
        f"{pertama['retry_after']:>12} {pertama['lama_detik']:>11.2f}")
  time.sleep(JEDA_DETIK)
  kedua = lonjakan("klien-ukur", JUMLAH_LONJAKAN)
  print(f"  {f'setelah menunggu {JEDA_DETIK:.0f} detik':<{LEBAR_TAHAP}} "
        f"{kedua['diterima']:>5} {kedua['ditolak']:>5} "
        f"{kedua['retry_after']:>12} {kedua['lama_detik']:>11.2f}")
  lain = lonjakan("klien-lain", JUMLAH_LONJAKAN)
  print(f"  {'klien lain, ember sendiri':<{LEBAR_TAHAP}} "
        f"{lain['diterima']:>5} {lain['ditolak']:>5} "
        f"{lain['retry_after']:>12} {lain['lama_detik']:>11.2f}")


if __name__ == "__main__":
  main()
