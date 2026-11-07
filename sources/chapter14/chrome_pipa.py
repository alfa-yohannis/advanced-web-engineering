"""Mengendalikan Chrome tanpa jendela lewat Chrome DevTools Protocol di pipa.

Chrome yang dinyalakan dengan --remote-debugging-pipe membaca perintah dari
file descriptor 3 dan menulis jawaban ke file descriptor 4. Tiap pesan berupa
satu JSON yang diakhiri byte nol. Dengan cara ini alat ukur dapat menunggu
sampai keadaan tertentu benar-benar tercapai, misalnya service worker siap,
tanpa WebSocket dan tanpa pustaka tambahan. Protokol yang sama dipakai
Playwright dan Puppeteer di balik layar.

Modul ini diimpor, bukan dijalankan langsung:
    python3 ukur-offline.py
"""

import functools
import json
import os
import shutil
import subprocess
import time

NAMA_CHROME = ["google-chrome", "google-chrome-stable", "chromium",
               "chromium-browser"]
# Nomor file descriptor yang dipakai Chrome untuk --remote-debugging-pipe.
FD_PERINTAH_CHROME = 3
FD_JAWABAN_CHROME = 4
PEMISAH_PESAN = b"\0"
UKURAN_BACA_BYTE = 65536
BATAS_TUNGGU_DETIK = 15
JEDA_PERIKSA_DETIK = 0.05


def cari_chrome():
  """Mencari Chrome di PATH, karena namanya berbeda antar distribusi."""
  for nama in NAMA_CHROME:
    jalur = shutil.which(nama)
    if jalur:
      return jalur
  raise SystemExit("Chrome tidak ditemukan. Pasang Google Chrome "
                   "atau Chromium lebih dahulu.")


def pasang_pipa_di_anak(ujung_perintah, ujung_jawaban):
  """Memindahkan kedua ujung pipa ke fd 3 dan 4 di proses anak.

  Fungsi ini berjalan di proses anak, sesudah fork dan sebelum Chrome
  dijalankan. Urutannya disengaja: fd 3 dipasang lebih dahulu, karena ujung
  jawaban selalu bernomor lebih besar dari 4 dan tidak akan tertimpa.
  """
  os.dup2(ujung_perintah, FD_PERINTAH_CHROME)
  os.dup2(ujung_jawaban, FD_JAWABAN_CHROME)
  os.set_inheritable(FD_PERINTAH_CHROME, True)
  os.set_inheritable(FD_JAWABAN_CHROME, True)


class ChromeLewatPipa:
  """Satu proses Chrome tanpa jendela beserta satu tab yang dikendalikannya."""

  def __init__(self, direktori_profil):
    """Menyalakan Chrome dengan profil tertentu, lalu membuka satu tab kosong.

    Profil yang sama menyimpan service worker beserta cache-nya di antara dua
    proses Chrome, persis seperti browser pengguna yang ditutup lalu dibuka.
    """
    baca_chrome, tulis_kita = os.pipe()
    baca_kita, tulis_chrome = os.pipe()
    perintah = [
        cari_chrome(), "--headless=new", "--disable-gpu", "--no-sandbox",
        "--no-first-run", f"--user-data-dir={direktori_profil}",
        "--remote-debugging-pipe", "about:blank",
    ]
    self.proses = subprocess.Popen(
        perintah, pass_fds=(FD_PERINTAH_CHROME, FD_JAWABAN_CHROME),
        preexec_fn=functools.partial(pasang_pipa_di_anak, baca_chrome,
                                     tulis_chrome),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.close(baca_chrome)
    os.close(tulis_chrome)
    self.tulis = os.fdopen(tulis_kita, "wb")
    self.baca = os.fdopen(baca_kita, "rb", buffering=0)
    self.sisa = b""
    self.nomor_pesan = 0
    target = self.kirim("Target.createTarget", {"url": "about:blank"})
    sesi = self.kirim("Target.attachToTarget",
                      {"targetId": target["targetId"], "flatten": True})
    self.sesi = sesi["sessionId"]

  def baca_pesan(self):
    """Membaca satu pesan utuh dari Chrome, yaitu sampai byte nol berikutnya."""
    while PEMISAH_PESAN not in self.sisa:
      potongan = self.baca.read(UKURAN_BACA_BYTE)
      if not potongan:
        raise RuntimeError("Chrome menutup pipanya")
      self.sisa += potongan
    pesan, self.sisa = self.sisa.split(PEMISAH_PESAN, 1)
    return json.loads(pesan)

  def kirim(self, metode, parameter=None, sesi=None):
    """Mengirim satu perintah, lalu menunggu jawaban dengan nomor yang sama.

    Pesan lain yang datang lebih dahulu, misalnya pemberitahuan peristiwa,
    dilewati, karena alat ukur ini hanya membaca jawaban perintahnya sendiri.
    """
    self.nomor_pesan += 1
    pesan = {"id": self.nomor_pesan, "method": metode,
             "params": parameter or {}}
    if sesi:
      pesan["sessionId"] = sesi
    self.tulis.write(json.dumps(pesan).encode() + PEMISAH_PESAN)
    self.tulis.flush()
    while True:
      jawaban = self.baca_pesan()
      if jawaban.get("id") != self.nomor_pesan:
        continue
      if "error" in jawaban:
        raise RuntimeError(f"{metode}: {jawaban['error']['message']}")
      return jawaban.get("result", {})

  def buka(self, alamat):
    """Membuka satu alamat di tab, lalu mengembalikan teks error-nya bila ada.

    Bila servernya tidak dapat dihubungi dan tidak ada service worker yang
    melayani, Chrome melaporkan kegagalannya di sini, misalnya
    net::ERR_CONNECTION_REFUSED.
    """
    hasil = self.kirim("Page.navigate", {"url": alamat}, self.sesi)
    return hasil.get("errorText", "")

  def nilai(self, ungkapan):
    """Menghitung satu ungkapan JavaScript di halaman, lalu mengembalikan nilainya."""
    hasil = self.kirim("Runtime.evaluate",
                       {"expression": ungkapan, "returnByValue": True},
                       self.sesi)
    return hasil["result"].get("value")

  def tunggu(self, ungkapan):
    """Menunggu sampai ungkapan bernilai benar, lalu mengembalikan nilainya.

    Bila batas waktunya lewat, nilai terakhirnya dikembalikan apa adanya,
    sehingga pemanggil dapat melaporkan keadaan yang tidak pernah tercapai.
    """
    batas = time.monotonic() + BATAS_TUNGGU_DETIK
    nilai_terakhir = self.nilai(ungkapan)
    while not nilai_terakhir and time.monotonic() < batas:
      time.sleep(JEDA_PERIKSA_DETIK)
      nilai_terakhir = self.nilai(ungkapan)
    return nilai_terakhir

  def tutup(self):
    """Menutup Chrome dengan rapi, agar profilnya tersimpan utuh ke disk."""
    try:
      self.kirim("Browser.close")
    except RuntimeError:
      pass
    self.proses.wait()
    self.tulis.close()
    self.baca.close()
