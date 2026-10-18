"""Membangun halaman statis, yaitu langkah build pada varian SSG.

Pekerjaan merakit HTML dipindahkan ke sini, sehingga saat pengunjung datang
server tinggal mengirim file yang sudah jadi. Inilah yang membedakan Static
Site Generation dari Server-Side Rendering: tempat perakitannya, bukan
hasilnya.

Pemakaian (dari sources/chapter08):
    python3 bangun-statis.py
"""

import time
from pathlib import Path

import katalog

DIREKTORI_STATIS = Path(__file__).parent / "statis"
FILE_SSG = DIREKTORI_STATIS / "katalog-ssg.html"


def bangun():
  """Merakit halaman katalog sekali, lalu menuliskannya sebagai file.

  Mengembalikan lama perakitan dalam detik, agar latihan dapat
  membandingkannya dengan lama melayani satu permintaan SSG.
  """
  mulai = time.perf_counter()
  isi = f"    <ul>\n      {katalog.rakit_baris_html()}\n    </ul>"
  halaman = katalog.rakit_halaman("Katalog", isi)
  DIREKTORI_STATIS.mkdir(exist_ok=True)
  FILE_SSG.write_text(halaman, encoding="utf-8")
  return time.perf_counter() - mulai


def main():
  """Membangun halaman statis, lalu melaporkan hasilnya."""
  lama = bangun()
  ukuran = FILE_SSG.stat().st_size
  print(f"Dibangun     : {FILE_SSG.name}")
  print(f"Ukuran       : {ukuran} byte")
  print(f"Lama merakit : {lama * 1000:.1f} ms")


if __name__ == "__main__":
  main()
