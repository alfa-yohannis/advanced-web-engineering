"""Mengukur biaya cold start sebuah fungsi serverless dibanding keadaan warm.

Tiga cara memanggil fungsi.py yang sama dibandingkan. Warm memakai satu proses
yang terus hidup, sehingga tiap pemanggilan hanya membayar fungsinya. Cold
start menyalakan satu proses baru untuk tiap pemanggilan. Cold start dengan
dependensi melakukan hal yang sama, ditambah memuat sejumlah modul saat
proses dinyalakan.

Pada layanan serverless sungguhan, cold start masih ditambah waktu mengunduh
kode dan menyalakan container atau mesin virtual. Yang terukur di sini hanya
bagian yang ditentukan kode fungsinya sendiri.

Pemakaian (dari sources/chapter14):
    python3 ukur-cold-start.py
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pengukur

FILE_FUNGSI = str(Path(__file__).parent / "fungsi.py")
PERISTIWA = {"berat_gram": 1200, "kota": "Bandung"}
JUMLAH_PEMANGGILAN_COLD = 30
JUMLAH_PEMANGGILAN_WARM = 300
# Pemanggilan pertama tidak dihitung, agar file yang belum ada di cache
# sistem operasi tidak ikut menjadi angka.
JUMLAH_WARMUP = 3
LEBAR_CARA = 30


def panggil_cold(dengan_dependensi):
  """Memanggil fungsi sekali dengan proses baru, lalu mengembalikan lamanya."""
  environment = dict(os.environ,
                     MUAT_DEPENDENSI="1" if dengan_dependensi else "0")
  mulai = time.perf_counter()
  subprocess.run([sys.executable, FILE_FUNGSI], input=json.dumps(PERISTIWA),
                 capture_output=True, text=True, env=environment, check=True)
  return (time.perf_counter() - mulai) * 1000


def ukur_cold(dengan_dependensi):
  """Mengukur sejumlah cold start berturut-turut."""
  lama_ms = [panggil_cold(dengan_dependensi)
             for _ in range(JUMLAH_WARMUP + JUMLAH_PEMANGGILAN_COLD)]
  return lama_ms[JUMLAH_WARMUP:]


def ukur_warm():
  """Mengukur pemanggilan berulang pada satu proses yang terus hidup.

  Proses dinyalakan sekali di luar pengukuran. Yang diukur hanya perjalanan
  satu peristiwa masuk lewat stdin dan hasilnya keluar lewat stdout.
  """
  proses = subprocess.Popen([sys.executable, FILE_FUNGSI, "--warm"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            text=True)
  baris_peristiwa = json.dumps(PERISTIWA) + "\n"
  lama_ms = []
  for urutan in range(JUMLAH_WARMUP + JUMLAH_PEMANGGILAN_WARM):
    mulai = time.perf_counter()
    proses.stdin.write(baris_peristiwa)
    proses.stdin.flush()
    proses.stdout.readline()
    if urutan >= JUMLAH_WARMUP:
      lama_ms.append((time.perf_counter() - mulai) * 1000)
  proses.stdin.close()
  proses.wait()
  return lama_ms


def main():
  """Mengukur ketiga cara, lalu mencetak hasilnya sebagai tabel."""
  daftar_hasil = [
      ("warm, proses dipakai ulang", ukur_warm()),
      ("cold start", ukur_cold(False)),
      ("cold start, dengan dependensi", ukur_cold(True)),
  ]
  print(f"  {'Cara':<{LEBAR_CARA}} {'p50 ms':>8} {'p95 ms':>8} {'Kali lipat':>11}")
  p50_warm = pengukur.hitung_persentil(daftar_hasil[0][1], 50)
  for nama_cara, lama_ms in daftar_hasil:
    p50_ms = pengukur.hitung_persentil(lama_ms, 50)
    p95_ms = pengukur.hitung_persentil(lama_ms, 95)
    print(f"  {nama_cara:<{LEBAR_CARA}} {p50_ms:>8.3f} {p95_ms:>8.3f} "
          f"{p50_ms / p50_warm:>11.0f}")


if __name__ == "__main__":
  main()
