#!/usr/bin/env python3
"""Membandingkan empat cara memanggil layanan lain yang kadang lambat.

Sepuluh worker memanggil layanan biaya kirim bersamaan. Empat cara
dibandingkan pada dua skenario, yaitu layanan yang sesekali lambat dan
layanan yang seluruhnya lambat:
  tanpa_batas_waktu  menunggu selama apa pun sampai layanan menjawab
  batas_waktu        menyerah setelah 300 milidetik
  batas_waktu_retry  menyerah setelah 300 milidetik, lalu retry sampai tiga
                     percobaan dengan exponential backoff dan jitter
  circuit_breaker    seperti sebelumnya, ditambah circuit breaker

Jalankan layanan-lambat.py lebih dahulu di terminal lain. Peringatan: skrip
ini mengirim ratusan permintaan. Arahkan hanya ke layanan milik sendiri.

Pemakaian (dari sources/chapter04):
    source ../.venv/bin/activate
    python resilience.py [permintaan_per_skenario]
"""

import queue
import random
import sys
import threading
import time
import urllib.error
import urllib.request

POLA_ALAMAT_LAYANAN = "http://127.0.0.1:8081/ongkir?peluang_lambat={peluang}"
DAFTAR_SKENARIO = (("sesekali lambat", 0.2), ("seluruhnya lambat", 1.0))
JUMLAH_WORKER = 10
PERMINTAAN_PER_SKENARIO_BAWAAN = 100

BATAS_WAKTU_DETIK = 0.3
PERCOBAAN_MAKSIMUM = 3
JEDA_DASAR_DETIK = 0.05
JEDA_MAKSIMUM_DETIK = 1.0

AMBANG_GAGAL_BERUNTUN = 5
COOLDOWN_DETIK = 1.0
CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half-open"


def hitung_persentil(daftar_angka, peringkat):
  """Menghitung persentil lewat interpolasi linear antara dua nilai terdekat."""
  angka_terurut = sorted(daftar_angka)
  posisi = (len(angka_terurut) - 1) * peringkat / 100
  indeks_bawah = int(posisi)
  indeks_atas = min(indeks_bawah + 1, len(angka_terurut) - 1)
  nilai_bawah = angka_terurut[indeks_bawah]
  nilai_atas = angka_terurut[indeks_atas]
  return nilai_bawah + (nilai_atas - nilai_bawah) * (posisi - indeks_bawah)


class CatatanHasil:
  """Mengumpulkan hasil seluruh worker. Aman dipakai banyak utas sekaligus."""

  def __init__(self):
    """Menyiapkan daftar lama permintaan dan dua penghitung, semuanya kosong."""
    self.daftar_lama_ms = []
    self.jumlah_berhasil = 0
    self.jumlah_panggilan = 0
    self.gembok = threading.Lock()

  def catat_panggilan(self):
    """Mencatat satu panggilan yang benar-benar sampai ke layanan."""
    with self.gembok:
      self.jumlah_panggilan += 1

  def catat_hasil_akhir(self, berhasil, lama_ms):
    """Mencatat hasil akhir satu permintaan, termasuk seluruh retry-nya."""
    with self.gembok:
      self.daftar_lama_ms.append(lama_ms)
      self.jumlah_berhasil += int(berhasil)


class CircuitBreaker:
  """Circuit breaker dengan tiga keadaan: closed, open, dan half-open.

  Closed: panggilan diteruskan. Setelah lima kegagalan beruntun, keadaan
  berpindah ke open, dan seluruh panggilan langsung ditolak tanpa menyentuh
  layanan. Setelah cooldown satu detik, keadaan berpindah ke half-open dan
  satu panggilan uji diizinkan. Bila uji itu berhasil keadaan kembali closed,
  bila gagal kembali open.
  """

  def __init__(self):
    """Mulai dalam keadaan closed, tanpa kegagalan yang tercatat."""
    self.keadaan = CLOSED
    self.gagal_beruntun = 0
    self.waktu_dibuka = 0.0
    self.gembok = threading.Lock()

  def izinkan_panggilan(self):
    """Menentukan apakah satu panggilan boleh diteruskan ke layanan."""
    with self.gembok:
      if self.keadaan == CLOSED:
        return True
      cooldown_habis = time.monotonic() - self.waktu_dibuka >= COOLDOWN_DETIK
      if self.keadaan == OPEN and cooldown_habis:
        # Hanya satu panggilan uji. Sisanya ditolak sampai hasilnya ada.
        self.keadaan = HALF_OPEN
        return True
      return False

  def catat_berhasil(self):
    """Satu keberhasilan cukup untuk kembali ke keadaan closed."""
    with self.gembok:
      self.keadaan = CLOSED
      self.gagal_beruntun = 0

  def catat_gagal(self):
    """Pindah ke open bila ambang terlampaui atau panggilan uji gagal."""
    with self.gembok:
      self.gagal_beruntun += 1
      ambang_terlampaui = self.gagal_beruntun >= AMBANG_GAGAL_BERUNTUN
      if self.keadaan == HALF_OPEN or ambang_terlampaui:
        self.keadaan = OPEN
        self.waktu_dibuka = time.monotonic()


def panggil_layanan_sekali(alamat, batas_waktu_detik, catatan_hasil):
  """Satu panggilan ke layanan. Mengembalikan True bila jawabannya diterima.

  batas_waktu_detik None berarti menunggu tanpa batas, yaitu perilaku bawaan
  banyak pustaka HTTP bila batas waktunya lupa diatur.
  """
  catatan_hasil.catat_panggilan()
  try:
    with urllib.request.urlopen(alamat, timeout=batas_waktu_detik) as jawaban:
      jawaban.read()
    return True
  except (urllib.error.URLError, TimeoutError, ConnectionError):
    return False


def hitung_jeda_sebelum_retry(percobaan_ke, pengacak):
  """Jeda acak antara nol dan batas atas yang berlipat dua tiap percobaan.

  Cara ini disebut exponential backoff dengan jitter. Tanpa unsur acak,
  seluruh klien yang gagal bersamaan akan retry bersamaan pula, dan layanan
  dihantam gelombang yang sama berulang kali.
  """
  batas_atas = min(JEDA_MAKSIMUM_DETIK, JEDA_DASAR_DETIK * 2 ** percobaan_ke)
  return pengacak.uniform(0, batas_atas)


def tanpa_batas_waktu(alamat, catatan_hasil, breaker, pengacak):
  """Menunggu jawaban selama apa pun."""
  return panggil_layanan_sekali(alamat, None, catatan_hasil)


def batas_waktu(alamat, catatan_hasil, breaker, pengacak):
  """Menyerah setelah 300 milidetik, tanpa retry."""
  return panggil_layanan_sekali(alamat, BATAS_WAKTU_DETIK, catatan_hasil)


def batas_waktu_retry(alamat, catatan_hasil, breaker, pengacak):
  """Menyerah setelah 300 milidetik, lalu retry dengan jeda acak."""
  for percobaan_ke in range(PERCOBAAN_MAKSIMUM):
    if panggil_layanan_sekali(alamat, BATAS_WAKTU_DETIK, catatan_hasil):
      return True
    if percobaan_ke < PERCOBAAN_MAKSIMUM - 1:
      time.sleep(hitung_jeda_sebelum_retry(percobaan_ke, pengacak))
  return False


def circuit_breaker(alamat, catatan_hasil, breaker, pengacak):
  """Seperti batas_waktu_retry, tetapi tiap percobaan meminta izin breaker."""
  for percobaan_ke in range(PERCOBAAN_MAKSIMUM):
    if not breaker.izinkan_panggilan():
      # Gagal seketika. Layanan yang sedang kewalahan tidak ditambah bebannya.
      return False
    if panggil_layanan_sekali(alamat, BATAS_WAKTU_DETIK, catatan_hasil):
      breaker.catat_berhasil()
      return True
    breaker.catat_gagal()
    if percobaan_ke < PERCOBAAN_MAKSIMUM - 1:
      time.sleep(hitung_jeda_sebelum_retry(percobaan_ke, pengacak))
  return False


def jalankan_worker(cara, alamat, antrean_permintaan, catatan_hasil, breaker,
                    nomor_worker):
  """Mengambil permintaan dari antrean sampai habis, lalu mencatat hasilnya."""
  pengacak = random.Random(nomor_worker)
  while True:
    try:
      antrean_permintaan.get_nowait()
    except queue.Empty:
      return
    waktu_mulai = time.perf_counter()
    berhasil = cara(alamat, catatan_hasil, breaker, pengacak)
    lama_ms = (time.perf_counter() - waktu_mulai) * 1000
    catatan_hasil.catat_hasil_akhir(berhasil, lama_ms)


def jalankan_satu_cara(cara, peluang_lambat, jumlah_permintaan):
  """Menjalankan satu cara pada satu skenario, lalu mencetak satu baris hasil."""
  alamat = POLA_ALAMAT_LAYANAN.format(peluang=peluang_lambat)
  catatan_hasil = CatatanHasil()
  breaker = CircuitBreaker()
  antrean_permintaan = queue.Queue()
  for nomor_permintaan in range(jumlah_permintaan):
    antrean_permintaan.put(nomor_permintaan)
  daftar_utas = [
      threading.Thread(
          target=jalankan_worker,
          args=(cara, alamat, antrean_permintaan, catatan_hasil, breaker,
                nomor_worker),
      )
      for nomor_worker in range(JUMLAH_WORKER)
  ]
  waktu_mulai = time.perf_counter()
  for utas in daftar_utas:
    utas.start()
  for utas in daftar_utas:
    utas.join()
  durasi_total_detik = time.perf_counter() - waktu_mulai
  persen_berhasil = 100 * catatan_hasil.jumlah_berhasil / jumlah_permintaan
  print(
      f"  {cara.__name__:<18} {persen_berhasil:>8.0f}% "
      f"{hitung_persentil(catatan_hasil.daftar_lama_ms, 50):>9.1f} "
      f"{hitung_persentil(catatan_hasil.daftar_lama_ms, 95):>9.1f} "
      f"{catatan_hasil.jumlah_panggilan:>10} {durasi_total_detik:>10.1f}"
  )


def main():
  """Menjalankan keempat cara pada kedua skenario."""
  jumlah_permintaan = (
      int(sys.argv[1]) if len(sys.argv) > 1 else PERMINTAAN_PER_SKENARIO_BAWAAN
  )
  for nama_skenario, peluang_lambat in DAFTAR_SKENARIO:
    print(
        f"\nSkenario {nama_skenario} (peluang lambat {peluang_lambat}), "
        f"{jumlah_permintaan} permintaan, {JUMLAH_WORKER} worker\n"
    )
    print(
        f"  {'Cara':<18} {'Berhasil':>9} {'p50 (ms)':>9} {'p95 (ms)':>9} "
        f"{'Panggilan':>10} {'Durasi (s)':>10}"
    )
    for cara in (tanpa_batas_waktu, batas_waktu, batas_waktu_retry,
                 circuit_breaker):
      jalankan_satu_cara(cara, peluang_lambat, jumlah_permintaan)


if __name__ == "__main__":
  main()
