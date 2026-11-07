"""Alat ukur bersama untuk skrip pengukuran Bab 14.

Berisi tiga hal yang dipakai berulang: menyalakan satu file Python sebagai
proses terpisah, menunggu port-nya siap, lalu mematikannya, ditambah cara
menghitung persentil. Keempatnya diletakkan di satu tempat agar seluruh skrip
pengukur menyalakan proses dan menghitung angka dengan cara yang sama persis.

Pengukuran di bab ini hanya diarahkan ke proses yang dinyalakan sendiri di
127.0.0.1.

Modul ini diimpor, bukan dijalankan langsung:
    python3 ukur-skala.py
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

DIREKTORI = Path(__file__).parent
HOST = "127.0.0.1"
BATAS_TUNGGU_PORT_DETIK = 10
BATAS_SATU_PERCOBAAN_DETIK = 1
JEDA_PERIKSA_PORT_DETIK = 0.05


def nyalakan(nama_file, environment_tambahan=None):
  """Menyalakan satu file Python sebagai proses terpisah, tanpa keluarannya.

  Environment proses induk ikut diwariskan, sehingga setelan seperti
  JUMLAH_KONEKSI yang ditulis di depan perintah sampai ke proses anaknya.
  """
  environment = dict(os.environ, **(environment_tambahan or {}))
  return subprocess.Popen([sys.executable, str(DIREKTORI / nama_file)],
                          env=environment, stdout=subprocess.DEVNULL)


def tunggu_port(port):
  """Menunggu sampai satu port menerima sambungan, atau menyerah."""
  batas = time.monotonic() + BATAS_TUNGGU_PORT_DETIK
  while time.monotonic() < batas:
    try:
      socket.create_connection((HOST, port),
                               timeout=BATAS_SATU_PERCOBAAN_DETIK).close()
      return
    except OSError:
      time.sleep(JEDA_PERIKSA_PORT_DETIK)
  raise RuntimeError(f"port {port} tidak kunjung menyala")


def matikan(daftar_proses):
  """Mematikan seluruh proses, lalu menunggu sampai benar-benar berhenti."""
  for proses in daftar_proses:
    proses.terminate()
  for proses in daftar_proses:
    proses.wait()


def hitung_persentil(daftar_angka, peringkat):
  """Menghitung persentil lewat interpolasi linear, sama seperti Bab 5.

  Cara yang sama dipakai sejak Bab 3, agar angka antarbab sebanding.
  """
  angka_terurut = sorted(daftar_angka)
  posisi = (len(angka_terurut) - 1) * peringkat / 100
  indeks_bawah = int(posisi)
  indeks_atas = min(indeks_bawah + 1, len(angka_terurut) - 1)
  nilai_bawah = angka_terurut[indeks_bawah]
  nilai_atas = angka_terurut[indeks_atas]
  return nilai_bawah + (nilai_atas - nilai_bawah) * (posisi - indeks_bawah)
