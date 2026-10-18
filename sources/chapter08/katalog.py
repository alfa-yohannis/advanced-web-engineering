"""Data katalog dan perakit HTML-nya, dipakai bersama seluruh varian Bab 8.

Datanya sengaja hanya daftar di memori, karena yang dibandingkan bab ini
adalah tempat HTML dirakit, bukan cara data diambil. Dengan begitu kelima
varian memakai data yang sama persis, dan selisih yang terukur benar-benar
berasal dari arsitekturnya.

Pemakaian (dari sources/chapter08):
    python3 -c "import katalog; print(katalog.rakit_baris_html())"
"""

import html

DAFTAR_BUKU = [
    {"judul": "Rekayasa Web Lanjut", "harga": 120000, "stok": 4},
    {"judul": "Basis Data Terapan", "harga": 95000, "stok": 2},
    {"judul": "Jaringan untuk Pengembang", "harga": 110000, "stok": 7},
    {"judul": "Keamanan Aplikasi Web", "harga": 125000, "stok": 3},
    {"judul": "Pengantar Algoritma", "harga": 85000, "stok": 9},
    {"judul": "Arsitektur Perangkat Lunak", "harga": 135000, "stok": 1},
]

# Dipakai alat ukur untuk memeriksa apakah isi katalog sudah ada di dalam
# HTML yang pertama tiba, atau baru menyusul lewat permintaan berikutnya.
PENANDA_ISI = "Rekayasa Web Lanjut"


def rakit_baris_html():
  """Merakit baris katalog menjadi potongan HTML siap tempel.

  Judul di-escape lebih dahulu, sehingga tanda kurung siku pada judul tidak
  ikut terbaca sebagai markup.
  """
  baris = []
  for buku in DAFTAR_BUKU:
    judul = html.escape(buku["judul"])
    baris.append(f"<li>{judul} &mdash; Rp {buku['harga']:,}</li>")
  return "\n      ".join(baris).replace(",", ".")


def rakit_halaman(judul_halaman, isi_badan, skrip=""):
  """Merakit satu halaman utuh dari potongan badannya.

  Kelima varian memakai kerangka halaman yang sama, sehingga selisih
  ukurannya berasal dari isi dan skripnya saja, bukan dari kerangkanya.
  """
  baris_skrip = f'\n    <script src="{skrip}" defer></script>' if skrip else ""
  return (
      "<!DOCTYPE html>\n<html lang=\"id\">\n  <head>\n"
      "    <meta charset=\"utf-8\" />\n"
      f"    <title>{judul_halaman}</title>{baris_skrip}\n"
      "  </head>\n  <body>\n"
      f"    <h1>{judul_halaman}</h1>\n{isi_badan}\n"
      "  </body>\n</html>\n"
  )
