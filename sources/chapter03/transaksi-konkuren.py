#!/usr/bin/env python3
"""Memperagakan lost update dan tiga cara mencegahnya.

Sejumlah pekerja mengurangi stok satu buku secara bersamaan. Bila tidak ada
pembaruan yang hilang, stok akhir sama dengan stok awal dikurangi jumlah
pengurangan. Selisihnya adalah pembaruan yang tertimpa.

Empat cara dibandingkan pada beban yang sama persis:
  naif        SELECT lalu UPDATE, tanpa pengaman apa pun
  atomik      pengurangan dikerjakan basis data dalam satu pernyataan
  pesimistis  SELECT ... FOR UPDATE, baris dikunci lebih dahulu
  optimistis  UPDATE ... WHERE versi = ..., yang kalah mengulang

Pemakaian:
    source ../.venv/bin/activate
    python transaksi-konkuren.py [jumlah_pekerja] [pengurangan_per_pekerja]
"""

import sys
import threading

import psycopg

DSN = "postgresql://awe:awe@localhost:5433/toko"
ID_BUKU = 1
STOK_AWAL = 1000

SQL_BACA_STOK = "SELECT stok FROM buku WHERE id = %s"
SQL_BACA_STOK_TERKUNCI = "SELECT stok FROM buku WHERE id = %s FOR UPDATE"
SQL_BACA_STOK_VERSI = "SELECT stok, versi FROM buku WHERE id = %s"
SQL_TULIS_STOK = "UPDATE buku SET stok = %s WHERE id = %s"
SQL_KURANGI_ATOMIK = "UPDATE buku SET stok = stok - 1 WHERE id = %s"
SQL_TULIS_BILA_VERSI_SAMA = (
    "UPDATE buku SET stok = %s, versi = versi + 1 "
    "WHERE id = %s AND versi = %s"
)
SQL_SIAPKAN = "UPDATE buku SET stok = %s, versi = 1 WHERE id = %s"


def kembalikan_stok_awal():
  """Mengembalikan stok dan versi buku uji ke keadaan awal."""
  with psycopg.connect(DSN) as koneksi:
    koneksi.execute(SQL_SIAPKAN, (STOK_AWAL, ID_BUKU))


def baca_stok_akhir():
  """Membaca stok setelah seluruh pekerja selesai."""
  with psycopg.connect(DSN) as koneksi:
    baris = koneksi.execute(SQL_BACA_STOK, (ID_BUKU,)).fetchone()
  return baris[0]


def naif(koneksi):
  """Mengurangi stok tanpa pengaman apa pun.

  Ada jeda antara membaca stok dan menuliskannya kembali. Pekerja lain
  dapat menulis di dalam jeda tersebut, dan tulisannya akan tertimpa.
  Mengembalikan jumlah percobaan, yang di sini selalu satu.
  """
  with koneksi.transaction():
    baris = koneksi.execute(SQL_BACA_STOK, (ID_BUKU,)).fetchone()
    stok_terbaca = baris[0]
    koneksi.execute(SQL_TULIS_STOK, (stok_terbaca - 1, ID_BUKU))
  return 1


def atomik(koneksi):
  """Menyerahkan pembacaan dan pengurangan ke basis data sekaligus.

  Tidak ada jeda yang dapat disisipi pekerja lain, karena tidak ada nilai
  yang sempat singgah di aplikasi.
  """
  with koneksi.transaction():
    koneksi.execute(SQL_KURANGI_ATOMIK, (ID_BUKU,))
  return 1


def pesimistis(koneksi):
  """Mengunci baris sampai transaksi selesai, sehingga pekerja lain menunggu.

  Benturan dicegah sebelum terjadi. Ongkosnya berupa antrean: pekerja lain
  berhenti di baris SELECT sampai kunci dilepas.
  """
  with koneksi.transaction():
    baris = koneksi.execute(SQL_BACA_STOK_TERKUNCI, (ID_BUKU,)).fetchone()
    stok_terbaca = baris[0]
    koneksi.execute(SQL_TULIS_STOK, (stok_terbaca - 1, ID_BUKU))
  return 1


def optimistis(koneksi):
  """Menulis hanya bila versinya belum berubah, lalu mengulang bila kalah.

  Tidak ada yang dikunci, sehingga tidak ada yang menunggu. Ongkosnya
  dibayar oleh pekerja yang kalah dalam race condition, yaitu mengerjakan ulang
  pembacaan dan penulisannya. Mengembalikan jumlah percobaan yang dipakai.
  """
  percobaan = 0
  while True:
    percobaan += 1
    with koneksi.transaction():
      baris = koneksi.execute(SQL_BACA_STOK_VERSI, (ID_BUKU,)).fetchone()
      stok_terbaca, versi_terbaca = baris
      hasil = koneksi.execute(
          SQL_TULIS_BILA_VERSI_SAMA,
          (stok_terbaca - 1, ID_BUKU, versi_terbaca),
      )
    # rowcount nol berarti versinya sudah diubah pekerja lain.
    if hasil.rowcount == 1:
      return percobaan


def kerja_satu_pekerja(cara, ulangan, jumlah_percobaan, nomor_pekerja):
  """Membuka koneksi sendiri, lalu mengurangi stok sebanyak ulangan kali."""
  with psycopg.connect(DSN) as koneksi:
    for _ in range(ulangan):
      jumlah_percobaan[nomor_pekerja] += cara(koneksi)


def jalankan(cara, jumlah_pekerja, ulangan):
  """Menjalankan satu cara pada banyak utas, lalu mencetak selisihnya."""
  kembalikan_stok_awal()
  jumlah_percobaan = [0] * jumlah_pekerja
  daftar_utas = [
      threading.Thread(
          target=kerja_satu_pekerja,
          args=(cara, ulangan, jumlah_percobaan, nomor),
      )
      for nomor in range(jumlah_pekerja)
  ]
  for utas in daftar_utas:
    utas.start()
  for utas in daftar_utas:
    utas.join()

  stok_diharapkan = STOK_AWAL - jumlah_pekerja * ulangan
  stok_akhir = baca_stok_akhir()
  hilang = stok_akhir - stok_diharapkan
  print(
      f"  {cara.__name__:<11} {stok_diharapkan:>10} {stok_akhir:>9} "
      f"{hilang:>8} {sum(jumlah_percobaan):>11}"
  )


def main():
  """Membandingkan keempat cara pada beban konkuren yang sama."""
  jumlah_pekerja = int(sys.argv[1]) if len(sys.argv) > 1 else 8
  ulangan = int(sys.argv[2]) if len(sys.argv) > 2 else 50
  print(
      f"{jumlah_pekerja} pekerja, {ulangan} pengurangan per pekerja, "
      f"stok awal {STOK_AWAL}\n"
  )
  print(
      f"  {'Cara':<11} {'Diharapkan':>10} {'Hasil':>9} "
      f"{'Hilang':>8} {'Percobaan':>11}"
  )
  for cara in (naif, atomik, pesimistis, optimistis):
    jalankan(cara, jumlah_pekerja, ulangan)


if __name__ == "__main__":
  main()
