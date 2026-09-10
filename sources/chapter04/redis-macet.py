#!/usr/bin/env python3
"""Mengukur lama satu GET ke Redis yang macet, dengan dan tanpa retry bawaan.

Batas waktu 50 milidetik tampak menjamin bahwa cache yang macet tidak akan
menahan permintaan lama. Kenyataannya, redis-py 8 melakukan retry sampai 10
kali untuk perintah yang gagal, dengan jeda acak yang makin panjang di
antaranya. Skrip ini mengukur selisih kedua pengaturan tersebut.

Redis dibekukan lebih dahulu dengan docker compose pause, sehingga perintah
tidak pernah dijawab. Keadaan ini lebih buruk daripada Redis yang mati,
karena kegagalannya baru ketahuan setelah batas waktu habis.

Pemakaian (dari sources/chapter04):
    docker compose pause cache
    source ../.venv/bin/activate
    python redis-macet.py
    docker compose unpause cache
"""

import statistics
import time

import redis
from redis.backoff import NoBackoff
from redis.retry import Retry

REDIS_HOST = "localhost"
REDIS_PORT = 6380
BATAS_WAKTU_DETIK = 0.05
JUMLAH_ULANGAN = 5
KUNCI_UJI = "terlaris:30hari"


def buat_klien_redis(jumlah_retry):
  """Membuat klien dengan batas waktu 50 ms.

  jumlah_retry None berarti memakai pengaturan bawaan pustaka, yaitu
  pengaturan yang terpakai bila pengembang tidak menulis apa pun.
  """
  pengaturan = {
      "host": REDIS_HOST,
      "port": REDIS_PORT,
      "socket_timeout": BATAS_WAKTU_DETIK,
      "socket_connect_timeout": BATAS_WAKTU_DETIK,
  }
  if jumlah_retry is not None:
    pengaturan["retry"] = Retry(NoBackoff(), jumlah_retry)
  return redis.Redis(**pengaturan)


def ukur_satu_get(cache):
  """Mengirim satu GET, mengembalikan lamanya dalam detik dan nama galatnya."""
  waktu_mulai = time.perf_counter()
  try:
    cache.get(KUNCI_UJI)
    hasil = "berhasil"
  except redis.RedisError as galat:
    hasil = type(galat).__name__
  return time.perf_counter() - waktu_mulai, hasil


def main():
  """Mengukur kedua pengaturan berulang kali, lalu mencetak sebarannya."""
  print(f"Satu GET ke Redis yang dibekukan, batas waktu {BATAS_WAKTU_DETIK} detik, "
        f"{JUMLAH_ULANGAN} ulangan\n")
  print(f"  {'Pengaturan':<18} {'Tercepat':>9} {'Tengah':>9} {'Terlama':>9}  Galat")
  for nama_pengaturan, jumlah_retry in (("bawaan pustaka", None),
                                        ("tanpa retry", 0)):
    cache = buat_klien_redis(jumlah_retry)
    daftar_lama_detik = []
    for _ in range(JUMLAH_ULANGAN):
      lama_detik, hasil = ukur_satu_get(cache)
      daftar_lama_detik.append(lama_detik)
    print(
        f"  {nama_pengaturan:<18} {min(daftar_lama_detik):>8.2f}s "
        f"{statistics.median(daftar_lama_detik):>8.2f}s "
        f"{max(daftar_lama_detik):>8.2f}s  {hasil}"
    )


if __name__ == "__main__":
  main()
