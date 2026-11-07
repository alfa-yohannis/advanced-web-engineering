"""Menjalankan langkah CI yang sama dengan ci.yml, di komputer sendiri.

Urutannya mengikuti prinsip gagal secepat mungkin: yang paling murah dan
paling sering gagal dijalankan lebih dahulu, dan langkah sesudahnya tidak
dijalankan bila satu langkah gagal. Hasilnya hijau bila seluruh langkah
lolos, dan merah dengan status keluar 1 bila ada yang gagal, lengkap dengan
nama uji yang gagal.

Karena langkahnya sama persis dengan ci.yml, yang hijau di komputer sendiri
juga hijau di server CI, dan kegagalan di server CI dapat diulang di sini.

Pemakaian (dari akar repositori atau dari sources/chapter01):
    python3 sources/chapter01/ci-lokal.py
"""

import re
import subprocess
import sys
import time
from pathlib import Path

DIREKTORI = Path(__file__).resolve().parent
DAFTAR_LANGKAH = [
    ("Periksa sintaks", ["-m", "compileall", "-q", "."]),
    ("Uji unit service", ["-m", "unittest", "test_layanan"]),
    ("Uji API lewat HTTP", ["-m", "unittest", "test_api"]),
]
POLA_JUMLAH_UJI = re.compile(r"Ran (\d+) tests?")
POLA_UJI_GAGAL = re.compile(r"^(?:FAIL|ERROR): (\S+)", re.MULTILINE)
LEBAR_LANGKAH = 20
LEBAR_HASIL = 6


def jalankan_langkah(argumen):
  """Menjalankan satu langkah sebagai proses Python terpisah, lalu menilainya.

  Tiap langkah berjalan di prosesnya sendiri, persis seperti di server CI,
  sehingga sisa keadaan dari langkah sebelumnya tidak ikut terbawa.
  """
  mulai = time.perf_counter()
  hasil = subprocess.run([sys.executable, *argumen], cwd=DIREKTORI,
                         capture_output=True, text=True, check=False)
  lama_detik = time.perf_counter() - mulai
  keluaran = hasil.stdout + hasil.stderr
  jumlah_uji = POLA_JUMLAH_UJI.search(keluaran)
  keterangan = f"{jumlah_uji.group(1)} uji" if jumlah_uji else "seluruh file"
  return {
      "lolos": hasil.returncode == 0,
      "lama_detik": lama_detik,
      "keterangan": keterangan,
      "uji_gagal": POLA_UJI_GAGAL.findall(keluaran),
  }


def main():
  """Menjalankan seluruh langkah berurutan, berhenti di langkah yang gagal."""
  print(f"  {'Langkah':<{LEBAR_LANGKAH}} {'Hasil':<{LEBAR_HASIL}} "
        f"{'Detik':>6}  Keterangan")
  for nama_langkah, argumen in DAFTAR_LANGKAH:
    hasil = jalankan_langkah(argumen)
    status = "lolos" if hasil["lolos"] else "gagal"
    print(f"  {nama_langkah:<{LEBAR_LANGKAH}} {status:<{LEBAR_HASIL}} "
          f"{hasil['lama_detik']:>6.2f}  {hasil['keterangan']}")
    if not hasil["lolos"]:
      for nama_uji in hasil["uji_gagal"]:
        print(f"    gagal: {nama_uji}")
      print(f"\n  Hasil: merah, berhenti di langkah {nama_langkah}")
      sys.exit(1)
  print("\n  Hasil: hijau, seluruh langkah lolos")


if __name__ == "__main__":
  main()
