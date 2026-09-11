#!/usr/bin/env python3
"""Memperagakan cache stampede dan dua cara meredamnya.

Kunci yang sering dibaca baru saja kedaluwarsa, lalu banyak permintaan datang
bersamaan. Tanpa pengaman, seluruhnya meleset dan menjalankan kueri yang sama
ke basis data. Tiga cara dibandingkan pada beban yang sama persis:
  tanpa_pengaman          tiap permintaan yang meleset menghitung sendiri
  single_flight           hanya satu yang menghitung, sisanya menunggu hasilnya
  stale_while_revalidate  nilai lama langsung dipakai, satu utas menyegarkan

Peringatan: skrip ini sengaja membebani basis data. Jalankan hanya pada
container milik sendiri.

Pemakaian (dari sources/chapter04, setelah siapkan-data.sh):
    source ../.venv/bin/activate
    python stampede.py [jumlah_permintaan_serentak]
"""

import json
import sys
import threading
import time

import redis
from psycopg_pool import ConnectionPool

DSN = "postgresql://awe:awe@localhost:5434/toko"
REDIS_HOST = "localhost"
REDIS_PORT = 6380
UKURAN_POOL = 10
PERMINTAAN_SERENTAK_BAWAAN = 50

# Nama kunci sengaja berbeda dari aplikasi.py, karena bentuk nilainya berbeda.
KUNCI_TERLARIS = "peragaan:terlaris:30hari"
KUNCI_GEMBOK = "peragaan:gembok:terlaris:30hari"
# Setelah TTL keras, Redis membuang nilainya. Setelah TTL lunak, nilainya
# dianggap basi, tetapi masih boleh dipakai sambil disegarkan.
TTL_KERAS_DETIK = 300
TTL_LUNAK_DETIK = 60
# Gembok dilepas otomatis bila pemegangnya mati sebelum sempat melepasnya.
UMUR_GEMBOK_MS = 2000
JEDA_PERIKSA_ULANG_DETIK = 0.01
BATAS_MENUNGGU_DETIK = 2.0
NAMA_UTAS_PENYEGAR = "penyegar"

SQL_TERLARIS = """
    SELECT b.judul, sum(i.jumlah) AS terjual
    FROM item_pesanan i
    JOIN pesanan p ON p.id = i.pesanan_id
    JOIN buku b ON b.id = i.buku_id
    WHERE p.dibuat_pada >= now() - interval '30 days'
      AND p.status <> 'batal'
    GROUP BY b.id, b.judul
    ORDER BY terjual DESC
    LIMIT 10
"""


class PenghitungKueri:
  """Menghitung kueri yang sampai ke basis data, aman dipakai banyak utas.

  Tanpa gembok, dua utas yang menambah bersamaan dapat kehilangan satu
  tambahan, persis seperti lost update pada Bab 3.
  """

  def __init__(self):
    """Mulai dari nol, dengan satu gembok yang dipakai bergantian semua utas."""
    self.jumlah = 0
    self.gembok = threading.Lock()

  def tambah_satu(self):
    """Menambah satu di bawah perlindungan gembok."""
    with self.gembok:
      self.jumlah += 1


def hitung_persentil(daftar_angka, peringkat):
  """Menghitung persentil lewat interpolasi linear antara dua nilai terdekat."""
  angka_terurut = sorted(daftar_angka)
  posisi = (len(angka_terurut) - 1) * peringkat / 100
  indeks_bawah = int(posisi)
  indeks_atas = min(indeks_bawah + 1, len(angka_terurut) - 1)
  nilai_bawah = angka_terurut[indeks_bawah]
  nilai_atas = angka_terurut[indeks_atas]
  return nilai_bawah + (nilai_atas - nilai_bawah) * (posisi - indeks_bawah)


def jalankan_kueri_terlaris(pool_koneksi, penghitung_kueri):
  """Menjalankan kueri mahal ke basis data, sekaligus mencatat jumlahnya."""
  penghitung_kueri.tambah_satu()
  with pool_koneksi.connection() as koneksi:
    daftar_baris = koneksi.execute(SQL_TERLARIS).fetchall()
  return json.dumps([[judul, terjual] for judul, terjual in daftar_baris])


def tanpa_pengaman(pool_koneksi, cache, penghitung_kueri):
  """Cache-aside biasa: permintaan yang meleset langsung menghitung sendiri."""
  nilai_tersimpan = cache.get(KUNCI_TERLARIS)
  if nilai_tersimpan is not None:
    return nilai_tersimpan
  isi_json = jalankan_kueri_terlaris(pool_koneksi, penghitung_kueri)
  cache.set(KUNCI_TERLARIS, isi_json, ex=TTL_KERAS_DETIK)
  return isi_json


def single_flight(pool_koneksi, cache, penghitung_kueri):
  """Hanya pemegang gembok yang menghitung, sisanya menunggu hasilnya muncul.

  SET NX berhasil bagi tepat satu klien. Klien lain memeriksa ulang cache
  setiap 10 milidetik sampai nilainya tersedia.
  """
  nilai_tersimpan = cache.get(KUNCI_TERLARIS)
  if nilai_tersimpan is not None:
    return nilai_tersimpan
  if cache.set(KUNCI_GEMBOK, "1", nx=True, px=UMUR_GEMBOK_MS):
    isi_json = jalankan_kueri_terlaris(pool_koneksi, penghitung_kueri)
    cache.set(KUNCI_TERLARIS, isi_json, ex=TTL_KERAS_DETIK)
    cache.delete(KUNCI_GEMBOK)
    return isi_json
  batas_waktu_tunggu = time.monotonic() + BATAS_MENUNGGU_DETIK
  while time.monotonic() < batas_waktu_tunggu:
    time.sleep(JEDA_PERIKSA_ULANG_DETIK)
    nilai_tersimpan = cache.get(KUNCI_TERLARIS)
    if nilai_tersimpan is not None:
      return nilai_tersimpan
  # Pemegang gembok terlalu lama, jadi hitung sendiri daripada gagal.
  return jalankan_kueri_terlaris(pool_koneksi, penghitung_kueri)


def bungkus_dengan_batas_segar(isi_json):
  """Menyimpan batas kesegaran bersama isinya, dalam satu nilai JSON."""
  batas_segar = time.time() + TTL_LUNAK_DETIK
  return json.dumps({"isi": isi_json, "segar_sampai": batas_segar})


def segarkan_di_latar(pool_koneksi, cache, penghitung_kueri):
  """Menghitung ulang nilai lalu menyimpannya. Dijalankan di utas terpisah."""
  try:
    isi_json = jalankan_kueri_terlaris(pool_koneksi, penghitung_kueri)
    nilai_baru = bungkus_dengan_batas_segar(isi_json)
    cache.set(KUNCI_TERLARIS, nilai_baru, ex=TTL_KERAS_DETIK)
  finally:
    cache.delete(KUNCI_GEMBOK)


def stale_while_revalidate(pool_koneksi, cache, penghitung_kueri):
  """Nilai basi langsung dipakai, sementara satu utas menyegarkannya.

  Tidak ada klien yang menunggu kueri. Biayanya, sebagian klien menerima
  nilai yang sudah lewat masa segarnya.
  """
  nilai_tersimpan = cache.get(KUNCI_TERLARIS)
  if nilai_tersimpan is None:
    # Belum ada nilai sama sekali, jadi tidak ada yang dapat dipakai sementara.
    isi_json = jalankan_kueri_terlaris(pool_koneksi, penghitung_kueri)
    nilai_baru = bungkus_dengan_batas_segar(isi_json)
    cache.set(KUNCI_TERLARIS, nilai_baru, ex=TTL_KERAS_DETIK)
    return isi_json
  nilai_terbungkus = json.loads(nilai_tersimpan)
  sudah_basi = nilai_terbungkus["segar_sampai"] < time.time()
  if sudah_basi and cache.set(KUNCI_GEMBOK, "1", nx=True, px=UMUR_GEMBOK_MS):
    threading.Thread(
        target=segarkan_di_latar,
        args=(pool_koneksi, cache, penghitung_kueri),
        name=NAMA_UTAS_PENYEGAR,
    ).start()
  return nilai_terbungkus["isi"]


def siapkan_keadaan_kedaluwarsa(cara, pool_koneksi, cache):
  """Menyiapkan keadaan tepat setelah kunci kedaluwarsa, sebelum tiap cara.

  Untuk stale_while_revalidate, nilai lama sengaja ditinggalkan dengan masa
  segar yang sudah lewat. Kueri penyiapan ini tidak ikut dihitung.
  """
  cache.delete(KUNCI_TERLARIS, KUNCI_GEMBOK)
  if cara is stale_while_revalidate:
    isi_lama = jalankan_kueri_terlaris(pool_koneksi, PenghitungKueri())
    nilai_basi = json.dumps({"isi": isi_lama, "segar_sampai": time.time() - 1})
    cache.set(KUNCI_TERLARIS, nilai_basi, ex=TTL_KERAS_DETIK)


def kirim_satu_permintaan(cara, pool_koneksi, cache, penghitung_kueri,
                          aba_aba_mulai, daftar_lama_ms):
  """Satu klien: menunggu aba-aba bersama, lalu mencatat lama jawabannya."""
  aba_aba_mulai.wait()
  waktu_mulai = time.perf_counter()
  cara(pool_koneksi, cache, penghitung_kueri)
  daftar_lama_ms.append((time.perf_counter() - waktu_mulai) * 1000)


def tunggu_utas_penyegar():
  """Menunggu utas penyegar selesai, agar kuerinya ikut terhitung."""
  for utas in threading.enumerate():
    if utas.name == NAMA_UTAS_PENYEGAR:
      utas.join()


def jalankan_satu_cara(cara, jumlah_permintaan, pool_koneksi, cache):
  """Melepas seluruh permintaan serentak, lalu mencetak satu baris hasil."""
  siapkan_keadaan_kedaluwarsa(cara, pool_koneksi, cache)
  penghitung_kueri = PenghitungKueri()
  # Barrier menahan semua utas sampai lengkap, lalu melepasnya bersamaan.
  aba_aba_mulai = threading.Barrier(jumlah_permintaan)
  daftar_lama_ms = []
  daftar_utas = [
      threading.Thread(
          target=kirim_satu_permintaan,
          args=(cara, pool_koneksi, cache, penghitung_kueri,
                aba_aba_mulai, daftar_lama_ms),
      )
      for _ in range(jumlah_permintaan)
  ]
  for utas in daftar_utas:
    utas.start()
  for utas in daftar_utas:
    utas.join()
  tunggu_utas_penyegar()
  print(
      f"  {cara.__name__:<23} {penghitung_kueri.jumlah:>5} "
      f"{hitung_persentil(daftar_lama_ms, 50):>11.1f} "
      f"{hitung_persentil(daftar_lama_ms, 95):>11.1f} "
      f"{max(daftar_lama_ms):>11.1f}"
  )


def main():
  """Membandingkan ketiga cara pada jumlah permintaan serentak yang sama."""
  jumlah_permintaan = (
      int(sys.argv[1]) if len(sys.argv) > 1 else PERMINTAAN_SERENTAK_BAWAAN
  )
  pool_koneksi = ConnectionPool(
      DSN, min_size=UKURAN_POOL, max_size=UKURAN_POOL, open=True
  )
  cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
  # Pemanasan: satu kueri di awal agar halaman data sudah ada di memori
  # PostgreSQL, sehingga cara pertama tidak menanggung pembacaan cakram.
  jalankan_kueri_terlaris(pool_koneksi, PenghitungKueri())

  print(f"{jumlah_permintaan} permintaan serentak tepat setelah kunci kedaluwarsa\n")
  print(
      f"  {'Cara':<23} {'Kueri':>5} {'p50 (ms)':>11} {'p95 (ms)':>11} "
      f"{'Maks (ms)':>11}"
  )
  for cara in (tanpa_pengaman, single_flight, stale_while_revalidate):
    jalankan_satu_cara(cara, jumlah_permintaan, pool_koneksi, cache)
  cache.delete(KUNCI_TERLARIS, KUNCI_GEMBOK)
  pool_koneksi.close()


if __name__ == "__main__":
  main()
