"""Mengukur kelima varian arsitektur pada halaman yang sama.

Yang diukur bukan selera, melainkan empat hal yang dapat dihitung: berapa
byte yang tiba, apakah isinya sudah ada di response pertama, berapa
permintaan lagi yang dibutuhkan sampai isinya tampil, dan berapa lama
seluruhnya.

Pengukuran ini bersifat mengamati dan hanya diarahkan ke aplikasi sendiri di
127.0.0.1. Beban yang diberikan setara satu pengunjung membuka halaman.

Pemakaian (dari sources/chapter08, setelah aplikasi.py menyala):
    python3 ukur-varian.py
"""

import re
import time
from http.client import HTTPConnection

import katalog

HOST = "127.0.0.1"
PORT = 8040
BATAS_WAKTU_DETIK = 5
ALAMAT_DATA = "/api/katalog"
VARIAN = ["/ssg", "/isr", "/ssr", "/islands", "/spa"]
POLA_SKRIP = re.compile(r'<script src="([^"]+)"')
LEBAR_NAMA = 10


def ambil(jalur):
  """Mengambil satu alamat, lalu melaporkan isinya beserta lamanya.

  Koneksi dibuka dan ditutup tiap kali, sama seperti alat ukur sederhana
  lain, sehingga angkanya mudah dibandingkan antarvarian.
  """
  mulai = time.perf_counter()
  koneksi = HTTPConnection(HOST, PORT, timeout=BATAS_WAKTU_DETIK)
  koneksi.request("GET", jalur)
  response = koneksi.getresponse()
  isi = response.read()
  koneksi.close()
  return isi, (time.perf_counter() - mulai) * 1000


def ukur_satu_varian(jalur):
  """Mengukur satu varian dari sudut pandang pengunjung pertama kali.

  Bila isi katalog belum ada di HTML, skrip dan datanya ikut diambil, persis
  seperti yang dilakukan browser, dan permintaan tambahan itu ikut dihitung.
  """
  html_isi, lama_html = ambil(jalur)
  isi_ada_di_html = katalog.PENANDA_ISI.encode() in html_isi
  byte_total = len(html_isi)
  lama_total = lama_html
  permintaan = 1

  skrip = POLA_SKRIP.search(html_isi.decode())
  if skrip:
    isi_skrip, lama_skrip = ambil(skrip.group(1))
    byte_total += len(isi_skrip)
    lama_total += lama_skrip
    permintaan += 1
  if not isi_ada_di_html:
    isi_data, lama_data = ambil(ALAMAT_DATA)
    byte_total += len(isi_data)
    lama_total += lama_data
    permintaan += 1

  return {
      "jalur": jalur,
      "byte_html": len(html_isi),
      "byte_total": byte_total,
      "isi_di_html": isi_ada_di_html,
      "permintaan": permintaan,
      "lama_html_ms": lama_html,
      "lama_total_ms": lama_total,
  }


def cetak_hasil(daftar_hasil):
  """Mencetak hasil seluruh varian sebagai satu tabel."""
  print(f"  {'Varian':<{LEBAR_NAMA}} {'HTML':>7} {'Total':>7} "
        f"{'Isi di HTML':>12} {'Minta':>6} {'HTML ms':>8} {'Total ms':>9}")
  for hasil in daftar_hasil:
    nama = hasil["jalur"].lstrip("/")
    isi_di_html = "ya" if hasil["isi_di_html"] else "tidak"
    print(f"  {nama:<{LEBAR_NAMA}} {hasil['byte_html']:>7} "
          f"{hasil['byte_total']:>7} {isi_di_html:>12} "
          f"{hasil['permintaan']:>6} {hasil['lama_html_ms']:>8.1f} "
          f"{hasil['lama_total_ms']:>9.1f}")


def main():
  """Mengukur seluruh varian berurutan, lalu mencetak tabelnya."""
  daftar_hasil = [ukur_satu_varian(jalur) for jalur in VARIAN]
  cetak_hasil(daftar_hasil)


if __name__ == "__main__":
  main()
