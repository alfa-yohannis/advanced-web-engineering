"""Mengukur pembagian rilis yang benar-benar terjadi di proxy.

Yang diukur bukan niat pada file rilis, melainkan berapa permintaan yang
sungguh dilayani tiap versi. Angka itu dibaca dari header X-Dilayani pada
tiap response.

Pengukuran ini bersifat mengamati dan hanya diarahkan ke proxy sendiri di
127.0.0.1.

Pemakaian (dari sources/chapter09, setelah proxy dan kedua layanan menyala):
    python3 ukur-rilis.py 200
"""

import sys
import time
from collections import Counter
from http.client import HTTPConnection

HOST = "127.0.0.1"
PORT = 8060
JALUR = "/api/katalog"
BATAS_WAKTU_DETIK = 5
JUMLAH_BAWAAN = 200


def kirim_permintaan(jumlah):
  """Mengirim sejumlah permintaan lewat satu koneksi, lalu merangkum hasilnya.

  Mengembalikan hitungan per versi, hitungan per status, dan lama seluruh
  permintaan dalam milidetik.
  """
  koneksi = HTTPConnection(HOST, PORT, timeout=BATAS_WAKTU_DETIK)
  per_versi = Counter()
  per_status = Counter()
  daftar_lama_ms = []
  for _ in range(jumlah):
    mulai = time.perf_counter()
    koneksi.request("GET", JALUR)
    response = koneksi.getresponse()
    response.read()
    daftar_lama_ms.append((time.perf_counter() - mulai) * 1000)
    per_versi[response.getheader("X-Dilayani", "-")] += 1
    per_status[response.status] += 1
  koneksi.close()
  return per_versi, per_status, daftar_lama_ms


def hitung_persentil(daftar_angka, persentil):
  """Menghitung persentil dengan cara yang sama seperti alat ukur Bab 5."""
  terurut = sorted(daftar_angka)
  posisi = min(int(len(terurut) * persentil / 100), len(terurut) - 1)
  return terurut[posisi]


def main():
  """Mengirim permintaan lewat proxy, lalu mencetak pembagian yang terjadi."""
  jumlah = int(sys.argv[1]) if len(sys.argv) > 1 else JUMLAH_BAWAAN
  per_versi, per_status, daftar_lama_ms = kirim_permintaan(jumlah)
  print(f"Permintaan   : {jumlah}")
  for nama, hitung in sorted(per_versi.items()):
    print(f"  {nama:<8} : {hitung:>4} permintaan "
          f"({hitung * 100 / jumlah:.1f}%)")
  for status, hitung in sorted(per_status.items()):
    print(f"  status {status} : {hitung:>4} permintaan")
  print(f"p50          : {hitung_persentil(daftar_lama_ms, 50):.1f} ms")
  print(f"p95          : {hitung_persentil(daftar_lama_ms, 95):.1f} ms")


if __name__ == "__main__":
  main()
