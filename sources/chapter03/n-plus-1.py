#!/usr/bin/env python3
"""Membandingkan pengambilan data berpola N+1 dengan query yang jumlahnya tetap.

Kedua cara menghasilkan data yang sama persis. Yang berbeda hanya jumlah
perjalanan ke basis data, dan selisih itulah yang diukur di sini.

Pemakaian:
    source ../.venv/bin/activate
    python n-plus-1.py [jumlah_pesanan]
"""

import sys
import time
from collections import defaultdict

import psycopg

DSN = "postgresql://admin:admin123@localhost:5433/toko"

SQL_DAFTAR_PESANAN = """
    SELECT id, total, dibuat_pada FROM pesanan
    WHERE pelanggan_id = %s ORDER BY dibuat_pada DESC LIMIT %s
"""

SQL_ITEM_SATU_PESANAN = """
    SELECT b.judul, i.jumlah FROM item_pesanan i
    JOIN buku b ON b.id = i.buku_id
    WHERE i.pesanan_id = %s
"""

SQL_PELANGGAN_TERSIBUK = """
    SELECT pelanggan_id, count(*) FROM pesanan
    GROUP BY pelanggan_id ORDER BY count(*) DESC LIMIT 1
"""

SQL_ITEM_BANYAK_PESANAN = """
    SELECT i.pesanan_id, b.judul, i.jumlah FROM item_pesanan i
    JOIN buku b ON b.id = i.buku_id
    WHERE i.pesanan_id = ANY(%s)
"""


def cari_pelanggan_tersibuk(koneksi):
  """Memilih pelanggan dengan pesanan terbanyak, agar N benar-benar tumbuh.

  Mengembalikan pasangan (id pelanggan, jumlah pesanannya).
  """
  baris = koneksi.execute(SQL_PELANGGAN_TERSIBUK).fetchone()
  return baris[0], baris[1]


def ambil_dengan_n_plus_1(koneksi, id_pelanggan, batas):
  """Mengambil daftar pesanan, lalu itemnya satu query untuk tiap pesanan.

  Inilah pola N+1: satu query untuk daftar, ditambah N query untuk isinya.
  Mengembalikan pasangan (daftar hasil, jumlah query yang dijalankan).
  """
  with koneksi.cursor() as kursor:
    kursor.execute(SQL_DAFTAR_PESANAN, (id_pelanggan, batas))
    daftar_pesanan = kursor.fetchall()
    jumlah_query = 1

    hasil = []
    for id_pesanan, total, waktu in daftar_pesanan:
      kursor.execute(SQL_ITEM_SATU_PESANAN, (id_pesanan,))
      hasil.append((id_pesanan, total, waktu, kursor.fetchall()))
      jumlah_query += 1

  return hasil, jumlah_query


def ambil_dengan_dua_query(koneksi, id_pelanggan, batas):
  """Mengambil data yang sama dengan jumlah query yang tidak bergantung N.

  Seluruh id pesanan dikirim sekali sebagai larik, lalu hasilnya
  dikelompokkan di sisi aplikasi. Mengembalikan pasangan yang sama bentuknya
  dengan ambil_dengan_n_plus_1.
  """
  with koneksi.cursor() as kursor:
    kursor.execute(SQL_DAFTAR_PESANAN, (id_pelanggan, batas))
    daftar_pesanan = kursor.fetchall()

    semua_id = [pesanan[0] for pesanan in daftar_pesanan]
    kursor.execute(SQL_ITEM_BANYAK_PESANAN, (semua_id,))

    item_per_pesanan = defaultdict(list)
    for id_pesanan, judul, jumlah in kursor.fetchall():
      item_per_pesanan[id_pesanan].append((judul, jumlah))

  hasil = [
      (id_pesanan, total, waktu, item_per_pesanan[id_pesanan])
      for id_pesanan, total, waktu in daftar_pesanan
  ]
  return hasil, 2


def sidik_jari(hasil):
  """Meringkas hasil menjadi bentuk yang dapat dibandingkan langsung.

  Dipakai untuk membuktikan kedua cara mengembalikan data yang sama.
  """
  return sorted((pesanan[0], sorted(pesanan[3])) for pesanan in hasil)


def ukur(nama, cara, koneksi, id_pelanggan, batas):
  """Menjalankan satu cara, mencetak jumlah query dan waktunya."""
  mulai = time.perf_counter()
  hasil, jumlah_query = cara(koneksi, id_pelanggan, batas)
  durasi_ms = (time.perf_counter() - mulai) * 1000
  jumlah_item = sum(len(pesanan[3]) for pesanan in hasil)
  print(
      f"  {nama:<24} {jumlah_query:>4} query {jumlah_item:>5} item "
      f"{durasi_ms:8.2f} ms"
  )
  return hasil


def main():
  """Membandingkan kedua cara pada pelanggan dan batas yang sama."""
  batas = int(sys.argv[1]) if len(sys.argv) > 1 else 20
  with psycopg.connect(DSN) as koneksi:
    id_pelanggan, jumlah_pesanan = cari_pelanggan_tersibuk(koneksi)
    diambil = min(batas, jumlah_pesanan)
    print(
        f"Pelanggan {id_pelanggan} punya {jumlah_pesanan} pesanan, "
        f"diambil {diambil}.\n"
    )
    print(f"  {'Cara':<24} {'Query':>10} {'Item':>10} {'Waktu':>11}")
    hasil_n_plus_1 = ukur(
        "N+1", ambil_dengan_n_plus_1, koneksi, id_pelanggan, batas
    )
    hasil_dua_query = ukur(
        "Dua query tetap", ambil_dengan_dua_query, koneksi, id_pelanggan, batas
    )

  sama = sidik_jari(hasil_n_plus_1) == sidik_jari(hasil_dua_query)
  print(f"\nHasil kedua cara identik: {sama}")


if __name__ == "__main__":
  main()
