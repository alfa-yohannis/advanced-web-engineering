"""Menjalankan matriks permintaan, lalu mencetak keputusan tiap kombinasinya.

Yang diuji bukan satu permintaan, melainkan seluruh persilangan antara empat
pengguna dan empat alamat. Tabel yang keluar memperlihatkan sekaligus dua
hal: peran mana yang boleh apa, dan tenant mana yang melihat apa.

Pengukuran ini bersifat mengamati dan hanya diarahkan ke aplikasi sendiri di
127.0.0.1.

Pemakaian (dari sources/chapter10, setelah aplikasi.py menyala):
    python3 ukur-akses.py
"""

import json
from http.client import HTTPConnection

HOST = "127.0.0.1"
PORT = 8070
BATAS_WAKTU_DETIK = 5
PENGGUNA = [("ani", "ani123"), ("budi", "budi123"), ("cita", "cita123"),
            ("dedi", "dedi123")]
ALAMAT = ["/api/pesanan", "/api/pesanan/1", "/api/pesanan/3", "/api/laporan"]
LEBAR_NAMA = 8
LEBAR_KOLOM = 16


def minta(metode, jalur, header=None):
  """Mengirim satu permintaan, lalu mengembalikan status beserta isinya."""
  koneksi = HTTPConnection(HOST, PORT, timeout=BATAS_WAKTU_DETIK)
  koneksi.request(metode, jalur, headers=header or {})
  response = koneksi.getresponse()
  isi = response.read()
  status = response.status
  koneksi.close()
  return status, json.loads(isi) if isi else {}


def masuk(nama, kata_sandi):
  """Masuk dengan cara token, lalu mengembalikan access tokennya."""
  status, isi = minta("POST", f"/masuk?cara=token&nama={nama}&sandi={kata_sandi}")
  if status != 200:
    raise SystemExit(f"gagal masuk sebagai {nama}: {isi}")
  return isi["access_token"]


def ringkas(status, isi):
  """Meringkas satu hasil menjadi satu sel tabel yang pendek.

  Jumlah baris ikut ditampilkan pada alamat daftar, karena di sanalah isolasi
  tenant paling terlihat: pengguna yang sama-sama berhasil tetap melihat
  jumlah yang berbeda.
  """
  if status == 200 and "jumlah" in isi:
    return f"200, {isi['jumlah']} baris"
  if status == 200:
    return "200"
  return f"{status}"


def main():
  """Menjalankan seluruh persilangan pengguna dan alamat, lalu mencetaknya."""
  judul = "".join(f"{jalur:>{LEBAR_KOLOM}}" for jalur in ALAMAT)
  print(f"  {'Pengguna':<{LEBAR_NAMA}}{judul}")
  for nama, kata_sandi in PENGGUNA:
    token = masuk(nama, kata_sandi)
    header = {"Authorization": f"Bearer {token}"}
    sel = []
    for jalur in ALAMAT:
      status, isi = minta("GET", jalur, header)
      sel.append(f"{ringkas(status, isi):>{LEBAR_KOLOM}}")
    print(f"  {nama:<{LEBAR_NAMA}}{''.join(sel)}")


if __name__ == "__main__":
  main()
