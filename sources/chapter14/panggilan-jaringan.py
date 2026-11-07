"""Membandingkan pemanggilan di dalam proses dengan pemanggilan lewat jaringan.

Pekerjaannya sama persis, yaitu hitung_harga dari layanan.py. Yang berbeda
hanya jalannya. Pada modular monolith, modul pesanan memanggil modul harga
sebagai fungsi. Pada microservices, layanan pesanan memanggil layanan harga
lewat HTTP, dan layanan itu proses lain.

Satu halaman pesanan dianggap memanggil harga sepuluh kali berurutan, satu
untuk tiap baris pesanan. Waktu satu halaman itulah yang diukur, dengan tiga
cara: fungsi di dalam proses, HTTP dengan sambungan yang dipakai ulang, dan
HTTP dengan sambungan baru tiap panggilan.

Skrip ini menyalakan sendiri satu proses layanan.py sebagai layanan harga,
mengukur, lalu mematikannya. Seluruhnya di 127.0.0.1, yaitu jaringan terbaik
yang mungkin: tanpa kabel, tanpa switch, dan tanpa jarak.

Pemakaian (dari sources/chapter14):
    python3 panggilan-jaringan.py
"""

import time
from http.client import HTTPConnection

import layanan
import pengukur

HOST = "127.0.0.1"
PORT_LAYANAN_HARGA = 8111
BATAS_WAKTU_DETIK = 10
PANGGILAN_PER_HALAMAN = 10
JUMLAH_HALAMAN = 1000
# Halaman pertama tidak dihitung, agar sambungan dan cache yang baru dibuka
# tidak ikut menjadi angka.
JUMLAH_HALAMAN_WARMUP = 50
JUMLAH_EKSEMPLAR = 12
HARGA_SATUAN_RUPIAH = 50_000
JALUR_HARGA = f"/harga?jumlah={JUMLAH_EKSEMPLAR}&satuan={HARGA_SATUAN_RUPIAH}"
LEBAR_CARA = 34


def halaman_lewat_fungsi(koneksi):
  """Memanggil harga sepuluh kali sebagai fungsi, seperti pada monolith.

  Argumen koneksi tidak dipakai. Ia ada agar ketiga cara dipanggil dengan
  bentuk yang sama oleh pengukurnya.
  """
  for _ in range(PANGGILAN_PER_HALAMAN):
    layanan.hitung_harga(JUMLAH_EKSEMPLAR, HARGA_SATUAN_RUPIAH)


def halaman_lewat_http(koneksi):
  """Memanggil harga sepuluh kali lewat satu sambungan yang dipakai ulang."""
  for _ in range(PANGGILAN_PER_HALAMAN):
    koneksi.request("GET", JALUR_HARGA)
    koneksi.getresponse().read()


def halaman_lewat_http_baru(koneksi):
  """Memanggil harga sepuluh kali, membuka sambungan TCP baru tiap kali.

  Argumen koneksi tidak dipakai, karena justru sambungan baru yang diukur.
  """
  for _ in range(PANGGILAN_PER_HALAMAN):
    sambungan_baru = HTTPConnection(HOST, PORT_LAYANAN_HARGA,
                                    timeout=BATAS_WAKTU_DETIK)
    sambungan_baru.request("GET", JALUR_HARGA)
    sambungan_baru.getresponse().read()
    sambungan_baru.close()


def ukur_cara(cara_halaman):
  """Mengukur satu cara pada sejumlah halaman, lalu mengembalikan p50 dan p95."""
  koneksi = HTTPConnection(HOST, PORT_LAYANAN_HARGA, timeout=BATAS_WAKTU_DETIK)
  lama_ms = []
  for urutan in range(JUMLAH_HALAMAN_WARMUP + JUMLAH_HALAMAN):
    mulai = time.perf_counter()
    cara_halaman(koneksi)
    if urutan >= JUMLAH_HALAMAN_WARMUP:
      lama_ms.append((time.perf_counter() - mulai) * 1000)
  koneksi.close()
  return (pengukur.hitung_persentil(lama_ms, 50),
          pengukur.hitung_persentil(lama_ms, 95))


def main():
  """Mengukur ketiga cara, lalu mencetak hasilnya sebagai tabel."""
  layanan_harga = pengukur.nyalakan("layanan.py",
                                    {"PORT": str(PORT_LAYANAN_HARGA)})
  pengukur.tunggu_port(PORT_LAYANAN_HARGA)
  daftar_cara = [
      ("fungsi di dalam proses", halaman_lewat_fungsi),
      ("HTTP, sambungan dipakai ulang", halaman_lewat_http),
      ("HTTP, sambungan baru tiap kali", halaman_lewat_http_baru),
  ]
  print(f"  {PANGGILAN_PER_HALAMAN} panggilan harga per halaman, "
        f"{JUMLAH_HALAMAN} halaman tiap cara\n")
  print(f"  {'Cara':<{LEBAR_CARA}} {'p50 ms':>8} {'p95 ms':>8} {'Kali lipat':>11}")
  try:
    p50_fungsi = None
    for nama_cara, cara_halaman in daftar_cara:
      p50_ms, p95_ms = ukur_cara(cara_halaman)
      if p50_fungsi is None:
        p50_fungsi = p50_ms
      print(f"  {nama_cara:<{LEBAR_CARA}} {p50_ms:>8.4f} {p95_ms:>8.4f} "
            f"{p50_ms / p50_fungsi:>11.0f}", flush=True)
  finally:
    pengukur.matikan([layanan_harga])


if __name__ == "__main__":
  main()
