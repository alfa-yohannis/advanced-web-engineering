"""Satu fungsi serverless tiruan: menghitung ongkos kirim dari satu peristiwa.

Fungsinya dijalankan dengan dua cara, seperti pada layanan serverless
sungguhan. Pada cold start, satu proses baru dinyalakan untuk satu
pemanggilan: interpreter dimulai, modul dimuat, fungsinya dipanggil sekali,
lalu prosesnya selesai. Pada keadaan warm, proses yang sama dipakai ulang,
sehingga tiap pemanggilan hanya membayar fungsinya sendiri.

Environment MUAT_DEPENDENSI=1 membuat fungsi ini memuat sejumlah modul
pustaka standar saat dinyalakan, menirukan fungsi yang membawa dependensi.

Pemakaian (dari sources/chapter14), biasanya dijalankan ukur-cold-start.py:
    echo '{"berat_gram": 1200, "kota": "Bandung"}' | python3 fungsi.py
    python3 fungsi.py --warm
"""

import importlib
import json
import math
import os
import sys

# Modul yang dimuat ketika MUAT_DEPENDENSI=1. Seluruhnya pustaka standar,
# agar latihan ini tidak membutuhkan pemasangan apa pun.
DAFTAR_DEPENDENSI = [
    "asyncio", "decimal", "email.mime.multipart", "http.server",
    "logging.handlers", "sqlite3", "unittest", "urllib.request",
    "xml.etree.ElementTree", "zipfile",
]
TARIF_PER_KILOGRAM_RUPIAH = {"Bandung": 9_000, "Jakarta": 8_000,
                             "Surabaya": 12_000}
TARIF_BAWAAN_RUPIAH = 15_000
GRAM_PER_KILOGRAM = 1000


def muat_dependensi():
  """Memuat seluruh dependensi bila diminta, seperti fungsi yang besar.

  Pemuatan ini terjadi sekali per proses. Pada cold start biayanya dibayar
  tiap pemanggilan, sedangkan pada keadaan warm dibayar sekali saja.
  """
  if os.environ.get("MUAT_DEPENDENSI") == "1":
    for nama_modul in DAFTAR_DEPENDENSI:
      importlib.import_module(nama_modul)


def tangani(peristiwa):
  """Menghitung ongkos kirim satu paket. Bentuknya seperti handler serverless.

  Handler hanya menerima peristiwa dan mengembalikan hasil. Ia tidak
  menyimpan apa pun di antara dua pemanggilan, karena pemanggilan berikutnya
  belum tentu sampai ke proses yang sama.
  """
  kilogram = math.ceil(peristiwa["berat_gram"] / GRAM_PER_KILOGRAM)
  tarif = TARIF_PER_KILOGRAM_RUPIAH.get(peristiwa["kota"],
                                        TARIF_BAWAAN_RUPIAH)
  return {"ongkir_rupiah": kilogram * tarif}


def layani_warm():
  """Melayani peristiwa baris demi baris dari stdin sampai stdin ditutup."""
  for baris in sys.stdin:
    print(json.dumps(tangani(json.loads(baris))), flush=True)


def main():
  """Memuat dependensi, lalu melayani satu peristiwa atau banyak peristiwa."""
  muat_dependensi()
  if "--warm" in sys.argv:
    layani_warm()
    return
  print(json.dumps(tangani(json.load(sys.stdin))))


if __name__ == "__main__":
  main()
