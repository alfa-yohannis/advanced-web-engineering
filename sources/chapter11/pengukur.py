"""Alat ukur bersama untuk ketiga skrip pengukuran Bab 11.

Berisi dua hal yang dipakai berulang: mengambil satu alamat lewat HTTP, dan
membuka satu halaman dengan Chrome tanpa jendela lalu mengambil DOM akhirnya.
Keduanya diletakkan di satu tempat agar ketiga skrip pengukur mengukur dengan
cara yang sama persis.

Pengukuran di bab ini bersifat mengamati dan hanya diarahkan ke aplikasi
sendiri di 127.0.0.1.

Modul ini diimpor, bukan dijalankan langsung:
    python3 ukur-hidrasi.py
"""

import shutil
import subprocess
import tempfile
from http.client import HTTPConnection

HOST = "127.0.0.1"
PORT = 8080
BATAS_WAKTU_DETIK = 60
NAMA_CHROME = ["google-chrome", "google-chrome-stable", "chromium",
               "chromium-browser"]


def ambil_response(jalur):
  """Mengambil satu alamat, lalu mengembalikan status dan ukuran isinya."""
  koneksi = HTTPConnection(HOST, PORT, timeout=BATAS_WAKTU_DETIK)
  koneksi.request("GET", jalur)
  response = koneksi.getresponse()
  isi = response.read()
  status = response.status
  koneksi.close()
  return status, len(isi)


def cari_chrome():
  """Mencari Chrome di PATH, karena namanya berbeda antar distribusi."""
  for nama in NAMA_CHROME:
    jalur = shutil.which(nama)
    if jalur:
      return jalur
  raise SystemExit("Chrome tidak ditemukan. Pasang Google Chrome "
                   "atau Chromium lebih dahulu.")


def buka_sekali(chrome, jalur, javascript_hidup=True):
  """Membuka satu halaman tanpa jendela, lalu mengembalikan DOM akhirnya.

  Direktori profil yang baru dipakai untuk tiap pembukaan, agar tidak ada
  cache yang membuat pembukaan kedua lebih ringan daripada yang pertama.
  Dengan javascript_hidup bernilai False, halaman dibuka seperti dilihat
  pengguna yang JavaScript-nya mati atau gagal diunduh.
  """
  with tempfile.TemporaryDirectory() as direktori_profil:
    perintah = [
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
        f"--user-data-dir={direktori_profil}", "--dump-dom",
    ]
    if not javascript_hidup:
      perintah.append("--blink-settings=scriptEnabled=false")
    perintah.append(f"http://{HOST}:{PORT}{jalur}")
    hasil = subprocess.run(perintah, capture_output=True, text=True,
                           timeout=BATAS_WAKTU_DETIK, check=True)
  return hasil.stdout
