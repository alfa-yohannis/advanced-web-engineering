#!/usr/bin/env python3
"""Mengukur latensi satu alamat di bawah beban, lalu melaporkan sebarannya.

Sejumlah worker mengirim permintaan berurutan lewat koneksi yang dipakai
ulang. Bentuk beban ini disebut closed loop: tiap worker menunggu jawaban
sebelum mengirim permintaan berikutnya, persis seperti satu pengguna.

Yang dilaporkan p50, p95, p99, jumlah permintaan per detik, dan ukuran
jawaban di kabel. Ukuran itu diambil setelah compress, karena itulah yang
benar-benar diunduh browser.

Peringatan: skrip ini sengaja membebani. Arahkan hanya ke aplikasi sendiri
atau sistem yang sudah memberi izin tertulis.

Pemakaian (dari sources/chapter05, setelah aplikasi.py menyala):
    source ../.venv/bin/activate
    python beban.py "/api/katalog?halaman=1&ukuran=20" [worker] [permintaan]
"""

import sys
import threading
import time
from http.client import HTTPConnection

HOST_BAWAAN = "127.0.0.1"
PORT_BAWAAN = 8010
WORKER_BAWAAN = 8
PERMINTAAN_PER_WORKER_BAWAAN = 25
BATAS_WAKTU_DETIK = 30
BYTE_PER_KB = 1024


def hitung_persentil(daftar_angka, peringkat):
  """Menghitung persentil lewat interpolasi linear antara dua nilai terdekat.

  Cara yang sama dipakai Bab 3 dan Bab 4, agar angka antarbab sebanding.
  """
  angka_terurut = sorted(daftar_angka)
  posisi = (len(angka_terurut) - 1) * peringkat / 100
  indeks_bawah = int(posisi)
  indeks_atas = min(indeks_bawah + 1, len(angka_terurut) - 1)
  nilai_bawah = angka_terurut[indeks_bawah]
  nilai_atas = angka_terurut[indeks_atas]
  return nilai_bawah + (nilai_atas - nilai_bawah) * (posisi - indeks_bawah)


def jalankan_satu_worker(jalur, jumlah_permintaan, catatan):
  """Mengirim permintaan berurutan lewat satu koneksi, lalu mencatat hasilnya.

  Koneksi dibuka sekali dan dipakai ulang, sehingga yang terukur adalah waktu
  server, bukan waktu membuka koneksi baru.
  """
  koneksi = HTTPConnection(HOST_BAWAAN, PORT_BAWAAN, timeout=BATAS_WAKTU_DETIK)
  header = {"Accept-Encoding": "gzip"}
  for _ in range(jumlah_permintaan):
    waktu_mulai = time.perf_counter()
    try:
      koneksi.request("GET", jalur, headers=header)
      jawaban = koneksi.getresponse()
      isi_jawaban = jawaban.read()
    except OSError:
      catatan["gagal"].append(1)
      koneksi.close()
      koneksi = HTTPConnection(HOST_BAWAAN, PORT_BAWAAN,
                               timeout=BATAS_WAKTU_DETIK)
      continue
    catatan["lama_ms"].append((time.perf_counter() - waktu_mulai) * 1000)
    catatan["byte"].append(len(isi_jawaban))
    catatan["encoding"].append(jawaban.getheader("Content-Encoding", "-"))
    if jawaban.status != 200:
      catatan["gagal"].append(1)
  koneksi.close()


def ukur_beban(jalur, jumlah_worker, permintaan_per_worker):
  """Melepas seluruh worker bersamaan, lalu merangkum hasil pengukurannya.

  Mengembalikan kamus berisi p50, p95, p99, throughput, ukuran jawaban, dan
  jumlah permintaan yang gagal.
  """
  catatan = {"lama_ms": [], "byte": [], "encoding": [], "gagal": []}
  daftar_utas = [
      threading.Thread(
          target=jalankan_satu_worker,
          args=(jalur, permintaan_per_worker, catatan),
      )
      for _ in range(jumlah_worker)
  ]
  waktu_mulai = time.perf_counter()
  for utas in daftar_utas:
    utas.start()
  for utas in daftar_utas:
    utas.join()
  durasi_detik = time.perf_counter() - waktu_mulai

  if not catatan["lama_ms"]:
    raise RuntimeError(f"tidak ada jawaban yang berhasil dari {jalur}")
  jumlah_permintaan = len(catatan["lama_ms"])
  return {
      "jalur": jalur,
      "permintaan": jumlah_permintaan,
      "p50_ms": hitung_persentil(catatan["lama_ms"], 50),
      "p95_ms": hitung_persentil(catatan["lama_ms"], 95),
      "p99_ms": hitung_persentil(catatan["lama_ms"], 99),
      "kb": max(catatan["byte"]) / BYTE_PER_KB,
      "encoding": catatan["encoding"][0],
      "rps": jumlah_permintaan / durasi_detik,
      "gagal": len(catatan["gagal"]),
  }


def cetak_hasil(hasil):
  """Mencetak satu hasil pengukuran dalam bentuk daftar berlabel."""
  print(f"Alamat       : {hasil['jalur']}")
  print(f"Permintaan   : {hasil['permintaan']}, gagal {hasil['gagal']}")
  print(f"p50          : {hasil['p50_ms']:8.2f} ms")
  print(f"p95          : {hasil['p95_ms']:8.2f} ms")
  print(f"p99          : {hasil['p99_ms']:8.2f} ms")
  print(f"Throughput   : {hasil['rps']:8.1f} permintaan per detik")
  print(f"Ukuran       : {hasil['kb']:8.1f} KB, encoding {hasil['encoding']}")


def main():
  """Mengukur satu alamat sesuai argumen, lalu mencetak hasilnya."""
  if len(sys.argv) < 2:
    sys.exit('Pemakaian: python beban.py "<jalur>" [worker] [permintaan]')
  jalur = sys.argv[1]
  jumlah_worker = int(sys.argv[2]) if len(sys.argv) > 2 else WORKER_BAWAAN
  permintaan_per_worker = (
      int(sys.argv[3]) if len(sys.argv) > 3 else PERMINTAAN_PER_WORKER_BAWAAN
  )
  print(f"{jumlah_worker} worker, {permintaan_per_worker} permintaan per worker\n")
  cetak_hasil(ukur_beban(jalur, jumlah_worker, permintaan_per_worker))


if __name__ == "__main__":
  main()
