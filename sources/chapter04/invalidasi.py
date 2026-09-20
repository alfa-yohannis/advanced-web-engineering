#!/usr/bin/env python3
"""Mengukur berapa lama pembaca masih melihat harga lama setelah harga diubah.

Empat cara pembaruan dibandingkan. Setelah harga di basis data diubah,
pembaca memeriksa lewat cache setiap 100 milidetik, lalu dicatat berapa kali
dan berapa lama harga lama masih terbaca:
  ttl_saja            cache tidak disentuh, menunggu kedaluwarsa sendiri
  hapus_saat_menulis  kunci cache dihapus tepat setelah basis data diubah
  hapus_kalah_race    sama, tetapi kalah race condition dengan pembaca lambat
  hapus_dua_kali      seperti hapus_kalah_race, ditambah penghapusan kedua
                      0,5 detik kemudian

Race condition pada cara ketiga sengaja dipaksa lewat threading.Event, agar
urutan kejadian yang jarang itu muncul setiap kali skrip dijalankan.

Pemakaian (dari sources/chapter04, setelah siapkan-data.sh):
    source ../.venv/bin/activate
    python invalidasi.py
"""

import threading
import time

import psycopg
import redis

DSN = "postgresql://admin:admin123@localhost:5434/toko"
REDIS_HOST = "localhost"
REDIS_PORT = 6380

ID_BUKU = 1
KUNCI_HARGA = f"buku:{ID_BUKU}:harga"
HARGA_AWAL = 50000
HARGA_BARU = 55000
TTL_DETIK = 5
SELANG_BACA_DETIK = 0.1
JEDA_HAPUS_KEDUA_DETIK = 0.5

SQL_BACA_HARGA = "SELECT harga FROM buku WHERE id = %s"
SQL_UBAH_HARGA = "UPDATE buku SET harga = %s WHERE id = %s"


def baca_harga_lewat_cache(koneksi, cache):
  """Membaca harga dengan pola cache-aside: cache dulu, basis data bila tidak ada."""
  harga_tersimpan = cache.get(KUNCI_HARGA)
  if harga_tersimpan is not None:
    return int(harga_tersimpan)
  harga = int(koneksi.execute(SQL_BACA_HARGA, (ID_BUKU,)).fetchone()[0])
  cache.set(KUNCI_HARGA, harga, ex=TTL_DETIK)
  return harga


def ubah_harga_di_basis_data(koneksi, harga):
  """Mengubah harga di basis data, yang menjadi source of truth."""
  koneksi.execute(SQL_UBAH_HARGA, (harga, ID_BUKU))


def kembalikan_keadaan_awal(koneksi, cache):
  """Mengembalikan harga awal dan mengosongkan cache sebelum tiap cara."""
  ubah_harga_di_basis_data(koneksi, HARGA_AWAL)
  cache.delete(KUNCI_HARGA)


def amati_harga_stale(koneksi, cache):
  """Membaca berulang sampai harga baru terlihat, atau sampai TTL habis.

  Mengembalikan jumlah pembacaan yang masih melihat harga lama, dan lama
  harga lama itu bertahan sejak basis data diubah.
  """
  waktu_ubah = time.monotonic()
  jumlah_baca_stale = 0
  while time.monotonic() - waktu_ubah < TTL_DETIK + 1:
    if baca_harga_lewat_cache(koneksi, cache) == HARGA_BARU:
      break
    jumlah_baca_stale += 1
    time.sleep(SELANG_BACA_DETIK)
  return jumlah_baca_stale, time.monotonic() - waktu_ubah


def isi_ulang_cache_terlambat(cache, sudah_membaca, penulis_selesai):
  """Pembaca yang membaca harga lama, lalu terlambat menyimpannya ke cache.

  Urutannya dipaksa: membaca basis data, memberi tanda, menunggu penulis
  selesai menghapus cache, baru menyimpan. Harga lama pun kembali ke cache
  sesudah penghapusan, dan bertahan sampai TTL habis.
  """
  with psycopg.connect(DSN, autocommit=True) as koneksi:
    harga_lama = int(koneksi.execute(SQL_BACA_HARGA, (ID_BUKU,)).fetchone()[0])
  sudah_membaca.set()
  penulis_selesai.wait()
  cache.set(KUNCI_HARGA, harga_lama, ex=TTL_DETIK)


def ttl_saja(koneksi, cache):
  """Mengubah basis data tanpa menyentuh cache sama sekali."""
  baca_harga_lewat_cache(koneksi, cache)
  ubah_harga_di_basis_data(koneksi, HARGA_BARU)


def hapus_saat_menulis(koneksi, cache):
  """Mengubah basis data, lalu langsung menghapus kunci cache-nya."""
  baca_harga_lewat_cache(koneksi, cache)
  ubah_harga_di_basis_data(koneksi, HARGA_BARU)
  cache.delete(KUNCI_HARGA)


def hapus_kalah_race(koneksi, cache, hapus_sekali_lagi=False):
  """Menghapus saat menulis, tetapi kalah race condition dengan pembaca lambat."""
  sudah_membaca = threading.Event()
  penulis_selesai = threading.Event()
  pembaca_lambat = threading.Thread(
      target=isi_ulang_cache_terlambat,
      args=(cache, sudah_membaca, penulis_selesai),
  )
  pembaca_lambat.start()
  sudah_membaca.wait()
  ubah_harga_di_basis_data(koneksi, HARGA_BARU)
  cache.delete(KUNCI_HARGA)
  if hapus_sekali_lagi:
    # Penghapusan kedua menyapu harga lama yang sempat diisi ulang pembaca.
    threading.Timer(
        JEDA_HAPUS_KEDUA_DETIK, cache.delete, args=(KUNCI_HARGA,)
    ).start()
  penulis_selesai.set()
  pembaca_lambat.join()


def hapus_dua_kali(koneksi, cache):
  """Race condition yang sama, ditambah penghapusan kedua 0,5 detik kemudian."""
  hapus_kalah_race(koneksi, cache, hapus_sekali_lagi=True)


def main():
  """Menjalankan keempat cara berurutan, lalu mencetak lama harga stale."""
  cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
  print(
      f"Harga {HARGA_AWAL} menjadi {HARGA_BARU}, TTL {TTL_DETIK} detik, "
      f"dibaca tiap {SELANG_BACA_DETIK} detik\n"
  )
  print(f"  {'Cara':<21} {'Baca stale':>10} {'Lama stale (s)':>14}")
  with psycopg.connect(DSN, autocommit=True) as koneksi:
    for cara in (ttl_saja, hapus_saat_menulis, hapus_kalah_race, hapus_dua_kali):
      kembalikan_keadaan_awal(koneksi, cache)
      cara(koneksi, cache)
      jumlah_baca_stale, lama_stale = amati_harga_stale(koneksi, cache)
      print(f"  {cara.__name__:<21} {jumlah_baca_stale:>10} {lama_stale:>14.1f}")
    kembalikan_keadaan_awal(koneksi, cache)


if __name__ == "__main__":
  main()
