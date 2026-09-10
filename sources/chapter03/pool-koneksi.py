#!/usr/bin/env python3
"""Mengukur biaya membuka koneksi dan manfaat connection pool.

Tiga cara dibandingkan pada beban yang sama persis, yaitu sejumlah kueri
sepele yang biayanya sendiri hampir nol, sehingga yang terukur benar-benar
biaya koneksinya.

  koneksi-baru  satu koneksi dibuka dan ditutup untuk tiap kueri
  satu-koneksi  satu koneksi dipakai ulang untuk seluruh kueri
  pool          connection pool dipakai bersama oleh banyak pekerja

Bagian terakhir menunjukkan apa yang terjadi ketika jumlah pekerja melampaui
max_connections milik server.

Pemakaian:
    source ../.venv/bin/activate
    python pool-koneksi.py [jumlah_pekerja] [kueri_per_pekerja]
"""

import sys
import threading
import time
from functools import partial

import psycopg
from psycopg_pool import ConnectionPool

DSN = "postgresql://awe:awe@localhost:5433/toko"

# Kueri sengaja sesepele mungkin agar yang terukur adalah biaya koneksinya.
KUERI = "SELECT 1"

UKURAN_POOL = 10
PEKERJA_BERLEBIH = 40


def koneksi_baru(ulangan):
  """Membuka dan menutup satu koneksi untuk tiap kueri."""
  for _ in range(ulangan):
    with psycopg.connect(DSN) as koneksi:
      koneksi.execute(KUERI).fetchone()


def satu_koneksi(ulangan):
  """Memakai satu koneksi untuk seluruh kueri milik satu pekerja."""
  with psycopg.connect(DSN) as koneksi:
    for _ in range(ulangan):
      koneksi.execute(KUERI).fetchone()


def pakai_pool(pool, ulangan):
  """Meminjam koneksi dari pool, memakainya, lalu mengembalikannya."""
  for _ in range(ulangan):
    with pool.connection() as koneksi:
      koneksi.execute(KUERI).fetchone()


def jalankan_aman(cara, ulangan, daftar_galat):
  """Menjalankan satu pekerja dan mencatat galatnya, bukan melemparkannya.

  Kegagalan sengaja tidak menghentikan pengukuran, karena skenario terakhir
  memang dirancang untuk menabrak batas max_connections milik server.
  """
  try:
    cara(ulangan)
  except Exception as galat:  # noqa: BLE001
    daftar_galat.append(type(galat).__name__)


def ukur(nama, cara, jumlah_pekerja, ulangan, catatan=""):
  """Menjalankan satu skenario pada banyak utas, lalu mencetak hasilnya."""
  daftar_galat = []
  daftar_utas = [
      threading.Thread(target=jalankan_aman, args=(cara, ulangan, daftar_galat))
      for _ in range(jumlah_pekerja)
  ]

  mulai = time.perf_counter()
  for utas in daftar_utas:
    utas.start()
  for utas in daftar_utas:
    utas.join()
  durasi_ms = (time.perf_counter() - mulai) * 1000

  total_kueri = jumlah_pekerja * ulangan
  per_kueri = durasi_ms / total_kueri if not daftar_galat else float("nan")
  status = f"{len(daftar_galat)} gagal" if daftar_galat else "berhasil"
  print(
      f"  {nama:<24} {durasi_ms:9.1f} ms {per_kueri:9.3f} ms "
      f"{status:>10}  {catatan}"
  )


def main():
  """Menjalankan seluruh skenario perbandingan secara berurutan."""
  jumlah_pekerja = int(sys.argv[1]) if len(sys.argv) > 1 else 10
  ulangan = int(sys.argv[2]) if len(sys.argv) > 2 else 50

  print(f"{jumlah_pekerja} pekerja, {ulangan} kueri per pekerja\n")
  print(f"  {'Cara':<24} {'Total':>12} {'Per kueri':>12} {'Status':>10}")

  ukur("koneksi baru tiap kueri", koneksi_baru, jumlah_pekerja, ulangan)
  ukur("satu koneksi per pekerja", satu_koneksi, jumlah_pekerja, ulangan)

  with ConnectionPool(DSN, min_size=2, max_size=UKURAN_POOL, timeout=5) as pool:
    pool.wait()
    ukur(
        f"pool, maksimum {UKURAN_POOL}",
        partial(pakai_pool, pool),
        jumlah_pekerja,
        ulangan,
    )

  # Server pada docker-compose.yml dibatasi max_connections=25.
  # Tanpa pool, pekerja sebanyak ini melampaui batas tersebut.
  print()
  ukur(
      f"{PEKERJA_BERLEBIH} pekerja tanpa pool",
      satu_koneksi,
      PEKERJA_BERLEBIH,
      5,
      "batas server 25",
  )
  with ConnectionPool(DSN, min_size=2, max_size=UKURAN_POOL, timeout=10) as pool:
    pool.wait()
    ukur(
        f"{PEKERJA_BERLEBIH} pekerja lewat pool",
        partial(pakai_pool, pool),
        PEKERJA_BERLEBIH,
        5,
        "antre, tidak ditolak",
    )


if __name__ == "__main__":
  main()
