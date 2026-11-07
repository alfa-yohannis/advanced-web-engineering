"""Smoke test lingkungan kerja: perkakas, versinya, Docker, dan port bab lain.

Satu perintah ini menjawab pertanyaan sebelum praktikum pertama dimulai:
apakah seluruh perkakas yang dipakai keempat belas bab sudah terpasang dengan
versi yang cukup, apakah Docker benar-benar dapat dihubungi, apakah pustaka
basis data sudah ada di venv bersama, dan apakah port yang dipakai bab-bab
berikutnya masih kosong. Hasilnya hijau bila seluruh pemeriksaan lolos, dan
merah dengan status keluar 1 bila ada yang gagal.

Pemeriksaan port hanya mencoba memesan port itu sebentar lalu melepasnya.
Tidak ada data yang dikirim ke mana pun.

Pemakaian (dari sources/chapter01):
    python3 periksa-lingkungan.py
"""

import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

PYTHON_MINIMUM = (3, 11)
NODE_MINIMUM = 20
NPM_MINIMUM = 10
GIT_MINIMUM = (2, 30)
DOCKER_MINIMUM = 24
COMPOSE_MINIMUM = 2
BATAS_WAKTU_DETIK = 20
PYTHON_VENV = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python"
NAMA_CHROME = ["google-chrome", "google-chrome-stable", "chromium",
               "chromium-browser"]
# Port yang dipakai tiap bab, agar bentrokan ketahuan sejak pertemuan pertama,
# bukan di tengah praktikum bab yang membutuhkannya.
PORT_PER_BAB = {
    5433: 3, 5434: 4, 6380: 4, 8000: 4, 8081: 4, 5435: 5, 8010: 5,
    5436: 6, 8020: 6, 5437: 7, 8030: 7, 8031: 7, 8040: 8, 8050: 1,
    8060: 9, 8061: 9, 8062: 9, 8070: 10, 8080: 11, 8090: 12, 8091: 12,
    8100: 13, 8101: 13, 8102: 13,
    **{port: 14 for port in range(8110, 8123)},
}
LEBAR_PEMERIKSAAN = 32
LEBAR_HASIL = 6


def jalankan(perintah):
  """Menjalankan satu perintah, lalu mengembalikan keluarannya atau None.

  None berarti perintahnya tidak ada, gagal, atau terlalu lama. Ketiganya
  diperlakukan sama, karena bagi praktikum akibatnya sama: perkakas itu
  belum dapat dipakai.
  """
  if shutil.which(perintah[0]) is None:
    return None
  try:
    hasil = subprocess.run(perintah, capture_output=True, text=True,
                           timeout=BATAS_WAKTU_DETIK, check=True)
  except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
    return None
  return hasil.stdout.strip()


def angka_versi(teks):
  """Mengambil angka versi pertama dari teks, misalnya (2, 43, 0)."""
  cocok = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", teks or "")
  if not cocok:
    return None
  return tuple(int(bagian) for bagian in cocok.groups() if bagian is not None)


def periksa_python():
  """Memeriksa versi interpreter yang sedang menjalankan skrip ini."""
  versi = sys.version_info[:3]
  return versi[:2] >= PYTHON_MINIMUM, ".".join(str(bagian) for bagian in versi)


def periksa_versi(perintah, minimum):
  """Memeriksa satu perkakas lewat perintah versinya, terhadap versi minimum.

  Minimum berupa satu angka untuk versi mayor saja, atau tuple untuk versi
  mayor dan minor.
  """
  keluaran = jalankan(perintah)
  versi = angka_versi(keluaran)
  if versi is None:
    return False, "tidak ditemukan"
  if isinstance(minimum, int):
    return versi[0] >= minimum, keluaran.splitlines()[0]
  return versi[:len(minimum)] >= minimum, keluaran.splitlines()[0]


def periksa_docker():
  """Memeriksa klien Docker sekaligus daemon-nya.

  Klien yang terpasang belum berarti Docker dapat dipakai. Daemon yang mati
  atau pengguna yang belum masuk grup docker baru ketahuan ketika server
  ditanya, sehingga keduanya diperiksa di sini.
  """
  klien = jalankan(["docker", "version", "--format", "{{.Client.Version}}"])
  server = jalankan(["docker", "info", "--format", "{{.ServerVersion}}"])
  if klien is None:
    return False, "tidak ditemukan"
  if server is None:
    return False, f"klien {klien}, daemon tidak dapat dihubungi"
  return angka_versi(server)[0] >= DOCKER_MINIMUM, f"server {server}"


def periksa_chrome():
  """Memeriksa Chrome atau Chromium, dipakai pengukuran Bab 2, 11, dan 14."""
  for nama in NAMA_CHROME:
    keluaran = jalankan([nama, "--version"])
    if keluaran:
      return True, keluaran
  return False, "tidak ditemukan"


def periksa_psycopg():
  """Memeriksa pustaka basis data di venv bersama, sources/.venv."""
  if not PYTHON_VENV.exists():
    return False, "sources/.venv belum dibuat"
  keluaran = jalankan([str(PYTHON_VENV), "-c",
                       "import psycopg; print(psycopg.__version__)"])
  if keluaran is None:
    return False, "psycopg belum terpasang di venv"
  return True, keluaran


def port_terpakai(port):
  """Mencoba memesan satu port di seluruh alamat, lalu langsung melepasnya.

  SO_REUSEADDR dipasang agar sambungan lama yang sedang ditutup tidak
  dianggap pemakai. Yang gagal dipesan hanya port yang sedang didengarkan
  proses lain.
  """
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soket:
    soket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
      soket.bind(("", port))
    except OSError:
      return True
  return False


def periksa_port():
  """Memeriksa seluruh port bab 1 sampai 14, lalu meringkas yang terpakai."""
  terpakai = [port for port in sorted(PORT_PER_BAB) if port_terpakai(port)]
  if not terpakai:
    return True, f"{len(PORT_PER_BAB)} port kosong", []
  daftar = ", ".join(str(port) for port in terpakai)
  return False, f"{len(terpakai)} terpakai: {daftar}", terpakai


def cetak_baris(nama, lolos, keterangan):
  """Mencetak satu baris hasil pemeriksaan."""
  hasil = "lolos" if lolos else "gagal"
  print(f"  {nama:<{LEBAR_PEMERIKSAAN}} {hasil:<{LEBAR_HASIL}} {keterangan}")


def main():
  """Menjalankan seluruh pemeriksaan, mencetak hasilnya, lalu keluar."""
  daftar_pemeriksaan = [
      ("Python 3.11 atau lebih baru", periksa_python()),
      ("Node.js 20 atau lebih baru",
       periksa_versi(["node", "--version"], NODE_MINIMUM)),
      ("npm 10 atau lebih baru",
       periksa_versi(["npm", "--version"], NPM_MINIMUM)),
      ("Git 2.30 atau lebih baru",
       periksa_versi(["git", "--version"], GIT_MINIMUM)),
      ("Docker 24 atau lebih baru", periksa_docker()),
      ("Docker Compose 2 atau lebih baru",
       periksa_versi(["docker", "compose", "version", "--short"],
                     COMPOSE_MINIMUM)),
      ("Chrome atau Chromium", periksa_chrome()),
      ("psycopg di sources/.venv", periksa_psycopg()),
  ]
  print(f"  {'Pemeriksaan':<{LEBAR_PEMERIKSAAN}} {'Hasil':<{LEBAR_HASIL}} "
        f"Keterangan")
  gagal = 0
  for nama, (lolos, keterangan) in daftar_pemeriksaan:
    cetak_baris(nama, lolos, keterangan)
    gagal += not lolos
  port_lolos, port_keterangan, terpakai = periksa_port()
  cetak_baris("Port bab 1 sampai 14", port_lolos, port_keterangan)
  gagal += not port_lolos
  for port in terpakai:
    print(f"    port {port} milik Bab {PORT_PER_BAB[port]} "
          f"sedang dipakai proses lain")
  if gagal:
    print(f"\n  Hasil: merah, {gagal} pemeriksaan gagal")
    sys.exit(1)
  print("\n  Hasil: hijau, seluruh pemeriksaan lolos")


if __name__ == "__main__":
  main()
