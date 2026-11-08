"""Alat ukur bersama untuk skrip pengukuran keadaan awal Bab 15.

Berisi hal yang dipakai lebih dari satu skrip: membaca komit repositori yang
diukur, mencari dan menjalankan Chrome tanpa jendela, dan meringkas sebaran
angka menjadi median, persentil ke-95, dan nilai terbesar. Diletakkan di satu
tempat agar seluruh skrip menghitung dengan definisi yang sama.

Seluruh pengukuran Bab 15 bersifat mengamati. Yang dibaca hanya file di
repositori yang sudah dikloning, dan halaman uji dibuka dari disk lokal.

Modul ini diimpor, bukan dijalankan langsung:
    ../.venv/bin/python ukur-permukaan.py rag/exim rag/djp rag/akreditasi
"""

import math
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path

BATAS_WAKTU_CHROME_DETIK = 300
PANJANG_KOMIT_PENDEK = 7
NAMA_CHROME = ["google-chrome", "google-chrome-stable", "chromium",
               "chromium-browser"]


def baca_komit(jalur_repo):
  """Mengembalikan komit yang sedang dibuka, tanpa menjalankan git.

  Angka keadaan awal berubah begitu repositorinya berubah, sehingga komit
  dicetak bersama angkanya. Klon baru menyimpan rujukan cabang di
  packed-refs, sedangkan klon yang sudah lama dipakai menyimpannya sebagai
  file sendiri, jadi keduanya diperiksa.
  """
  direktori_git = Path(jalur_repo) / ".git"
  isi_head = (direktori_git / "HEAD").read_text().strip()
  if not isi_head.startswith("ref: "):
    return isi_head[:PANJANG_KOMIT_PENDEK]
  nama_rujukan = isi_head[len("ref: "):]
  file_rujukan = direktori_git / nama_rujukan
  if file_rujukan.exists():
    return file_rujukan.read_text().strip()[:PANJANG_KOMIT_PENDEK]
  for baris in (direktori_git / "packed-refs").read_text().splitlines():
    if baris.endswith(" " + nama_rujukan):
      return baris.split()[0][:PANJANG_KOMIT_PENDEK]
  raise SystemExit(f"Komit {nama_rujukan} tidak ditemukan di {jalur_repo}.")


def cari_chrome():
  """Mencari Chrome di PATH, karena namanya berbeda antar distribusi."""
  for nama in NAMA_CHROME:
    jalur = shutil.which(nama)
    if jalur:
      return jalur
  raise SystemExit("Chrome tidak ditemukan. Pasang Google Chrome "
                   "atau Chromium lebih dahulu.")


def baca_versi_chrome(chrome):
  """Mengembalikan versi Chrome, karena angka render bergantung padanya."""
  hasil = subprocess.run([chrome, "--version"], capture_output=True,
                         text=True, check=True)
  return hasil.stdout.strip()


def buka_halaman_lokal(chrome, jalur_halaman):
  """Membuka satu file HTML tanpa jendela, lalu mengembalikan DOM akhirnya.

  Profil baru dipakai pada tiap pembukaan, agar pembukaan berikutnya tidak
  mewarisi cache atau kode yang sudah dikompilasi dari pembukaan sebelumnya.
  Skrip di halaman berjalan sebelum peristiwa load, sehingga DOM yang
  dikembalikan sudah memuat hasil pengukurannya.
  """
  with tempfile.TemporaryDirectory() as direktori_profil:
    perintah = [
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
        f"--user-data-dir={direktori_profil}", "--dump-dom",
        Path(jalur_halaman).resolve().as_uri(),
    ]
    hasil = subprocess.run(perintah, capture_output=True, text=True,
                           timeout=BATAS_WAKTU_CHROME_DETIK, check=True)
  return hasil.stdout


def hitung_persentil(nilai_terurut, persen):
  """Persentil dengan metode nearest-rank atas daftar yang sudah terurut.

  Metode ini selalu mengembalikan salah satu nilai yang benar-benar
  teramati, bukan hasil interpolasi, sehingga persentil ke-95 dari 30
  ulangan adalah ulangan ke-29 dari yang tercepat.
  """
  peringkat = math.ceil(persen / 100 * len(nilai_terurut))
  return nilai_terurut[max(peringkat, 1) - 1]


def ringkas_sebaran(daftar_nilai):
  """Mengembalikan median, persentil ke-95, dan nilai terbesar.

  Rata-rata sengaja tidak dipakai. Satu pembaruan yang lambat tenggelam di
  rata-rata, padahal justru pembaruan itulah yang terasa tersendat.
  """
  nilai_terurut = sorted(daftar_nilai)
  return (statistics.median(nilai_terurut),
          hitung_persentil(nilai_terurut, 95),
          nilai_terurut[-1])
