#!/usr/bin/env python3
"""Mengukur waktu sampai byte pertama satu alamat, lalu melaporkan sebarannya.

Yang diukur sama dengan kolom TungguServer pada ukur-koneksi.sh di Bab 2,
yaitu sejak permintaan terkirim sampai baris status jawaban diterima. Tiap
permintaan membuka koneksi baru, persis seperti curl.

Bila jawaban membawa header X-Cache, jumlah HIT dan MISS ikut dilaporkan,
sehingga angka waktu dapat dikaitkan dengan asal jawabannya.

Peringatan: jalankan hanya terhadap sistem sendiri. Skrip ini mengirim
permintaan berurutan tanpa jeda.

Pemakaian:
    source ../.venv/bin/activate
    python ukur-ttfb.py http://localhost:8000/api/terlaris [jumlah_ulangan]
"""

import collections
import sys
import time
from http.client import HTTPConnection
from urllib.parse import urlsplit

ULANGAN_BAWAAN = 50
BATAS_WAKTU_DETIK = 30


def hitung_persentil(daftar_angka, peringkat):
  """Menghitung persentil lewat interpolasi linear antara dua nilai terdekat.

  Cara yang sama dipakai ukur-query.py pada Bab 3, agar angkanya sebanding.
  """
  angka_terurut = sorted(daftar_angka)
  posisi = (len(angka_terurut) - 1) * peringkat / 100
  indeks_bawah = int(posisi)
  indeks_atas = min(indeks_bawah + 1, len(angka_terurut) - 1)
  nilai_bawah = angka_terurut[indeks_bawah]
  nilai_atas = angka_terurut[indeks_atas]
  return nilai_bawah + (nilai_atas - nilai_bawah) * (posisi - indeks_bawah)


def ukur_satu_permintaan(host, port, jalur):
  """Mengirim satu GET, mengembalikan (waktu ke byte pertama dalam ms, X-Cache).

  Koneksi dibuka lebih dahulu, di luar pengukuran, agar yang terukur hanya
  waktu tunggu server. getresponse() kembali begitu baris status dan header
  selesai dibaca.
  """
  koneksi = HTTPConnection(host, port, timeout=BATAS_WAKTU_DETIK)
  koneksi.connect()
  waktu_mulai = time.perf_counter()
  koneksi.request("GET", jalur)
  jawaban = koneksi.getresponse()
  lama_ms = (time.perf_counter() - waktu_mulai) * 1000
  jawaban.read()
  koneksi.close()
  return lama_ms, jawaban.getheader("X-Cache", "-")


def main():
  """Mengukur satu alamat berulang kali, lalu mencetak p50, p95, dan asalnya."""
  if len(sys.argv) < 2:
    sys.exit("Pemakaian: python ukur-ttfb.py <alamat> [ulangan]")
  alamat = sys.argv[1]
  jumlah_ulangan = int(sys.argv[2]) if len(sys.argv) > 2 else ULANGAN_BAWAAN
  bagian_alamat = urlsplit(alamat)

  daftar_lama_ms = []
  jumlah_per_asal = collections.Counter()
  for _ in range(jumlah_ulangan):
    lama_ms, asal_jawaban = ukur_satu_permintaan(
        bagian_alamat.hostname, bagian_alamat.port, bagian_alamat.path
    )
    daftar_lama_ms.append(lama_ms)
    jumlah_per_asal[asal_jawaban] += 1

  print(f"Alamat       : {alamat}")
  print(f"Ulangan      : {jumlah_ulangan}")
  print(f"p50          : {hitung_persentil(daftar_lama_ms, 50):8.2f} ms")
  print(f"p95          : {hitung_persentil(daftar_lama_ms, 95):8.2f} ms")
  print(f"Terbesar     : {max(daftar_lama_ms):8.2f} ms")
  ringkasan_asal = ", ".join(
      f"{asal} {jumlah}" for asal, jumlah in jumlah_per_asal.items()
  )
  print(f"X-Cache      : {ringkasan_asal}")


if __name__ == "__main__":
  main()
