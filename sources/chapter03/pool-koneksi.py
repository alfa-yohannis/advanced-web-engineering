#!/usr/bin/env python3
"""Mengukur biaya membuka koneksi dan manfaat connection pool.

Tiga cara dibandingkan pada beban yang sama persis, yaitu sejumlah kueri
sepele yang biayanya sendiri hampir nol, sehingga yang terukur benar-benar
biaya koneksinya.

  koneksi-baru  satu koneksi dibuka dan ditutup untuk tiap kueri
  satu-koneksi  satu koneksi dipakai ulang untuk seluruh kueri
  pool          connection pool dipakai bersama oleh banyak worker

Bagian terakhir menunjukkan apa yang terjadi ketika jumlah worker melampaui
max_connections milik server.

Pemakaian:
    source ../.venv/bin/activate
    python pool-koneksi.py [jumlah_worker] [kueri_per_worker]
"""

import sys
import threading
import time
from functools import partial

import psycopg
from psycopg_pool import ConnectionPool

DSN = "postgresql://admin:admin123@localhost:5433/toko"

# Kueri sengaja sesepele mungkin agar yang terukur adalah biaya koneksinya.
KUERI = "SELECT 1"

UKURAN_POOL = 10
WORKER_BERLEBIH = 40


def koneksi_baru(ulangan):
  """Membuka dan menutup satu koneksi untuk tiap kueri."""
  for _ in range(ulangan):
    with psycopg.connect(DSN) as koneksi:
      koneksi.execute(KUERI).fetchone()


def satu_koneksi(ulangan):
  """Memakai satu koneksi untuk seluruh kueri milik satu worker."""
  with psycopg.connect(DSN) as koneksi:
    for _ in range(ulangan):
      koneksi.execute(KUERI).fetchone()


def pakai_pool(pool, ulangan):
  """Meminjam koneksi dari pool, memakainya, lalu mengembalikannya."""
  for _ in range(ulangan):
    with pool.connection() as koneksi:
      koneksi.execute(KUERI).fetchone()


def jalankan_aman(cara, ulangan, daftar_error):
  """Menjalankan satu worker dan mencatat error-nya, bukan melemparkannya.

  Kegagalan sengaja tidak menghentikan pengukuran, karena skenario terakhir
  memang dirancang untuk menabrak batas max_connections milik server.
  """
  try:
    cara(ulangan)
  except Exception as error:  # noqa: BLE001
    daftar_error.append(type(error).__name__)


def ukur(nama, cara, jumlah_worker, ulangan, catatan=""):
  """Menjalankan satu skenario pada banyak utas, lalu mencetak hasilnya."""
  daftar_error = []
  daftar_utas = [
      threading.Thread(target=jalankan_aman, args=(cara, ulangan, daftar_error))
      for _ in range(jumlah_worker)
  ]

  mulai = time.perf_counter()
  for utas in daftar_utas:
    utas.start()
  for utas in daftar_utas:
    utas.join()
  durasi_ms = (time.perf_counter() - mulai) * 1000

  total_kueri = jumlah_worker * ulangan
  per_kueri = durasi_ms / total_kueri if not daftar_error else float("nan")
  status = f"{len(daftar_error)} gagal" if daftar_error else "berhasil"
  print(
      f"  {nama:<24} {durasi_ms:9.1f} ms {per_kueri:9.3f} ms "
      f"{status:>10}  {catatan}"
  )


def main():
  """Menjalankan seluruh skenario perbandingan secara berurutan."""
  jumlah_worker = int(sys.argv[1]) if len(sys.argv) > 1 else 10
  ulangan = int(sys.argv[2]) if len(sys.argv) > 2 else 50

  print(f"{jumlah_worker} worker, {ulangan} kueri per worker\n")
  print(f"  {'Cara':<24} {'Total':>12} {'Per kueri':>12} {'Status':>10}")

  ukur("koneksi baru tiap kueri", koneksi_baru, jumlah_worker, ulangan)
  ukur("satu koneksi per worker", satu_koneksi, jumlah_worker, ulangan)

  with ConnectionPool(DSN, min_size=2, max_size=UKURAN_POOL, timeout=5) as pool:
    pool.wait()
    ukur(
        f"pool, maksimum {UKURAN_POOL}",
        partial(pakai_pool, pool),
        jumlah_worker,
        ulangan,
    )

  # Server pada docker-compose.yml dibatasi max_connections=25.
  # Tanpa pool, worker sebanyak ini melampaui batas tersebut.
  print()
  ukur(
      f"{WORKER_BERLEBIH} worker tanpa pool",
      satu_koneksi,
      WORKER_BERLEBIH,
      5,
      "batas server 25",
  )
  with ConnectionPool(DSN, min_size=2, max_size=UKURAN_POOL, timeout=10) as pool:
    pool.wait()
    ukur(
        f"{WORKER_BERLEBIH} worker lewat pool",
        partial(pakai_pool, pool),
        WORKER_BERLEBIH,
        5,
        "antre, tidak ditolak",
    )


if __name__ == "__main__":
  main()
