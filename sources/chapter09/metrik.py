"""Pembaca metrik format Prometheus, dipakai papan.py dan alarm.py.

Pembacaannya sengaja sederhana: baris teks dipilah menurut nama metriknya,
tanpa pustaka tambahan. Yang ingin ditunjukkan bab ini adalah bentuk
metriknya, bukan cara mengurai teksnya.

Pemakaian (dari sources/chapter09):
    python3 -c "import metrik; print(metrik.baca('127.0.0.1', 8061))"
"""

import re
from http.client import HTTPConnection

BATAS_WAKTU_DETIK = 5
POLA_EMBER = re.compile(r'lama_permintaan_ms_bucket\{[^}]*le="([^"]+)"\} (\d+)')
POLA_ANGKA = re.compile(r"^(\w+)\{[^}]*\} ([\d.]+)$")


def ambil_teks_metrik(host, port):
  """Mengambil teks metrik apa adanya dari satu layanan."""
  koneksi = HTTPConnection(host, port, timeout=BATAS_WAKTU_DETIK)
  koneksi.request("GET", "/metrics")
  teks = koneksi.getresponse().read().decode()
  koneksi.close()
  return teks


def baca(host, port):
  """Membaca metrik satu layanan menjadi kamus yang siap dihitung.

  Mengembalikan jumlah permintaan, jumlah gagal, total waktu, dan daftar
  ember histogram beserta hitungan kumulatifnya.
  """
  teks = ambil_teks_metrik(host, port)
  angka = {}
  for baris in teks.split("\n"):
    cocok = POLA_ANGKA.match(baris)
    if cocok and not baris.startswith("lama_permintaan_ms_bucket"):
      angka[cocok.group(1)] = float(cocok.group(2))
  ember = [(batas, int(hitung)) for batas, hitung in POLA_EMBER.findall(teks)]
  return {
      "permintaan": int(angka.get("permintaan_total", 0)),
      "gagal": int(angka.get("permintaan_gagal_total", 0)),
      "total_ms": angka.get("lama_permintaan_ms_sum", 0.0),
      "ember": ember,
  }


def persentil_dari_ember(ember, jumlah_permintaan, persentil):
  """Menaksir persentil dari ember histogram, bukan dari tiap permintaan.

  Hasilnya berupa batas ember tempat persentil itu jatuh, sehingga angkanya
  selalu salah satu batas yang tertulis. Inilah yang membedakan histogram
  dari menyimpan tiap nilai: hemat tempat, tetapi ketelitiannya sebatas
  embernya.
  """
  if jumlah_permintaan == 0:
    return None
  ambang = jumlah_permintaan * persentil / 100
  for batas, kumulatif in ember:
    if kumulatif >= ambang:
      return batas
  return "+Inf"
