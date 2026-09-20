#!/usr/bin/env python3
"""Memprofil pekerjaan sisi server satu alamat, tanpa lewat jaringan.

cProfile mencatat waktu tiap fungsi, sehingga bagian yang paling mahal
terlihat langsung. Yang diprofil hanya query dan serialisasi, karena itulah
bagian yang dapat diperbaiki di kode aplikasi.

Pemakaian (dari sources/chapter05, setelah docker compose up -d):
    source ../.venv/bin/activate
    python profil-endpoint.py [katalog-penuh|katalog|terlaris] [ulangan]
"""

import cProfile
import json
import pstats
import sys

from psycopg_pool import ConnectionPool

from aplikasi import (DSN, UKURAN_HALAMAN_BAWAAN, ambil_halaman_katalog,
                      ambil_katalog_penuh, jalankan_query_terlaris)

ULANGAN_BAWAAN = 20
JUMLAH_BARIS_LAPORAN = 12
HALAMAN_PERTAMA = 1


def kerjakan_katalog_penuh(pool_koneksi):
  """Mengerjakan seluruh pekerjaan alamat katalog penuh, sampai byte JSON."""
  return json.dumps(ambil_katalog_penuh(pool_koneksi)).encode()


def kerjakan_katalog(pool_koneksi):
  """Mengerjakan seluruh pekerjaan alamat katalog satu halaman."""
  daftar_buku = ambil_halaman_katalog(pool_koneksi, HALAMAN_PERTAMA,
                                      UKURAN_HALAMAN_BAWAAN)
  return json.dumps(daftar_buku).encode()


def kerjakan_terlaris(pool_koneksi):
  """Mengerjakan seluruh pekerjaan alamat agregat buku terlaris."""
  return json.dumps(jalankan_query_terlaris(pool_koneksi)).encode()


PEKERJAAN_PER_NAMA = {
    "katalog-penuh": kerjakan_katalog_penuh,
    "katalog": kerjakan_katalog,
    "terlaris": kerjakan_terlaris,
}


def ulangi_pekerjaan(pekerjaan, pool_koneksi, jumlah_ulangan):
  """Menjalankan satu pekerjaan berulang kali, lalu melaporkan ukuran akhirnya.

  Diulang agar waktu tiap fungsi terkumpul cukup banyak untuk dibandingkan,
  bukan tenggelam oleh derajat ketelitian pengukur waktunya.
  """
  isi_jawaban = b""
  for _ in range(jumlah_ulangan):
    isi_jawaban = pekerjaan(pool_koneksi)
  return isi_jawaban


def main():
  """Memprofil satu pekerjaan, lalu mencetak fungsi termahal di urutan atas."""
  nama_pekerjaan = sys.argv[1] if len(sys.argv) > 1 else "katalog-penuh"
  if nama_pekerjaan not in PEKERJAAN_PER_NAMA:
    sys.exit(f"Pilihan: {', '.join(PEKERJAAN_PER_NAMA)}")
  jumlah_ulangan = int(sys.argv[2]) if len(sys.argv) > 2 else ULANGAN_BAWAAN

  pool_koneksi = ConnectionPool(DSN, min_size=1, max_size=2, open=True)
  profil = cProfile.Profile()
  isi_jawaban = profil.runcall(ulangi_pekerjaan,
                               PEKERJAAN_PER_NAMA[nama_pekerjaan],
                               pool_koneksi, jumlah_ulangan)
  pool_koneksi.close()

  print(f"Pekerjaan    : {nama_pekerjaan}, {jumlah_ulangan} ulangan")
  print(f"Ukuran JSON  : {len(isi_jawaban) / 1024:.1f} KB\n")
  laporan = pstats.Stats(profil)
  laporan.sort_stats(pstats.SortKey.CUMULATIVE)
  laporan.print_stats(JUMLAH_BARIS_LAPORAN)


if __name__ == "__main__":
  main()
