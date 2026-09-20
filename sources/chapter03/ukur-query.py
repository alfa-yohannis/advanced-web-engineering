#!/usr/bin/env python3
"""Menjalankan satu query berulang kali, lalu melaporkan sebarannya.

Satu kali EXPLAIN ANALYZE tidak cukup dijadikan angka laporan. Jalankan
pertama menanggung pengisian cache, sedangkan jalankan berikutnya lebih
cepat. Karena itu yang dilaporkan adalah p50 dan p95, bukan satu angka.

Query dibaca dari berkas, satu query per berkas.

Pemakaian:
    source ../.venv/bin/activate
    python ukur-query.py query/q1.sql [jumlah_ulangan]
"""

import sys
from pathlib import Path

import psycopg

DSN = "postgresql://admin:admin123@localhost:5433/toko"


def persentil(daftar_angka, peringkat):
  """Menghitung persentil lewat interpolasi linear antara dua nilai terdekat.

  Dipakai agar tidak bergantung pada pustaka luar, dan agar cara
  perhitungannya terbaca langsung dari kodenya.
  """
  urut = sorted(daftar_angka)
  posisi = (len(urut) - 1) * peringkat / 100
  bawah = int(posisi)
  atas = min(bawah + 1, len(urut) - 1)
  return urut[bawah] + (urut[atas] - urut[bawah]) * (posisi - bawah)


def ambil_rencana(koneksi, sql):
  """Menjalankan query lewat EXPLAIN ANALYZE, mengembalikan rencananya.

  Format JSON dipilih karena hasilnya dapat dibaca program, sedangkan format
  teks harus diurai sendiri.
  """
  with koneksi.cursor() as kursor:
    kursor.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {sql}")
    return kursor.fetchone()[0][0]


def simpul_pemindaian(simpul, ditemukan=None):
  """Menelusuri rencana untuk mengumpulkan seluruh simpul pemindaiannya.

  Simpul inilah yang menunjukkan apakah indeks benar-benar dipakai.
  """
  ditemukan = ditemukan if ditemukan is not None else []
  if "Scan" in simpul["Node Type"]:
    sasaran = simpul.get("Relation Name") or simpul.get("Index Name", "")
    ditemukan.append(f"{simpul['Node Type']} {sasaran}".strip())
  for anak in simpul.get("Plans", []):
    simpul_pemindaian(anak, ditemukan)
  return ditemukan


def main():
  """Mengukur satu berkas query, lalu mencetak sebaran waktunya."""
  if len(sys.argv) < 2:
    sys.exit("Pemakaian: python ukur-query.py <berkas.sql> [ulangan]")
  berkas = Path(sys.argv[1])
  ulangan = int(sys.argv[2]) if len(sys.argv) > 2 else 20
  sql = berkas.read_text(encoding="utf-8").strip().rstrip(";")

  daftar_waktu = []
  with psycopg.connect(DSN) as koneksi:
    # Jalankan pertama dibuang, karena menanggung pengisian cache.
    ambil_rencana(koneksi, sql)
    for _ in range(ulangan):
      rencana = ambil_rencana(koneksi, sql)
      daftar_waktu.append(rencana["Execution Time"])

  print(f"Berkas       : {berkas}")
  print(f"Ulangan      : {ulangan}, jalankan pertama dibuang")
  print(f"p50          : {persentil(daftar_waktu, 50):8.3f} ms")
  print(f"p95          : {persentil(daftar_waktu, 95):8.3f} ms")
  print("Pemindaian   : " + ", ".join(simpul_pemindaian(rencana["Plan"])))


if __name__ == "__main__":
  main()
