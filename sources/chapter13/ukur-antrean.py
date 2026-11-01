"""Menjalankan satu daur antrean dari ujung ke ujung, lalu mencetak hasilnya.

Tiga pekerjaan dimasukkan ke antrean. Yang pertama berjalan lancar, yang
kedua ditolak webhook dua kali sehingga harus dicoba ulang dengan jeda
berlipat, dan yang ketiga menirukan worker yang mati sesudah mengirim
sehingga pekerjaannya terkirim dua kali.

Dua tabel dicetak. Tabel pertama memuat tiap percobaan yang dilakukan worker,
beserta jarak waktu dari percobaan sebelumnya. Tabel kedua memuat pengiriman
yang benar-benar tiba di webhook, yang jumlahnya lebih sedikit daripada
jumlah percobaan.

Pengukuran ini bersifat mengamati dan hanya diarahkan ke layanan sendiri di
127.0.0.1.

Pemakaian (dari sources/chapter13, setelah webhook.py menyala):
    python3 ukur-antrean.py
"""

import json
import time
from http.client import HTTPConnection

import antrean
import worker

HOST_WEBHOOK = "127.0.0.1"
PORT_WEBHOOK = 8102
BATAS_WAKTU_DETIK = 5
PEKERJAAN = [
    ("kirim-laporan", {"tujuan": "keuangan"}),
    ("gagal-dua-kali", {"tujuan": "mitra"}),
    ("crash-setelah-kirim", {"tujuan": "gudang"}),
]
BATAS_PUTARAN = 12
JEDA_PUTARAN_DETIK = 0.25
LEBAR_ID = 12
LEBAR_JENIS = 20
LEBAR_HASIL = 34


def kosongkan_webhook():
  """Mengosongkan catatan webhook, agar pengukuran dimulai dari nol."""
  koneksi = HTTPConnection(HOST_WEBHOOK, PORT_WEBHOOK,
                           timeout=BATAS_WAKTU_DETIK)
  koneksi.request("POST", "/reset", body=b"{}",
                  headers={"Content-Type": "application/json",
                           "Content-Length": "2"})
  koneksi.getresponse().read()
  koneksi.close()


def ambil_pengiriman():
  """Mengambil seluruh catatan pengiriman dari webhook."""
  koneksi = HTTPConnection(HOST_WEBHOOK, PORT_WEBHOOK,
                           timeout=BATAS_WAKTU_DETIK)
  koneksi.request("GET", "/pengiriman")
  isi = json.loads(koneksi.getresponse().read())
  koneksi.close()
  return isi["pengiriman"]


def jalankan_daur():
  """Menjalankan worker beberapa putaran, lalu mengumpulkan tiap percobaan.

  Putarannya dibatasi, sehingga pengukuran berhenti sendiri walaupun ada
  pekerjaan yang tidak pernah berhasil.
  """
  catatan = []
  mulai = time.monotonic()
  for _ in range(BATAS_PUTARAN):
    for satu in worker.satu_putaran(True):
      satu["detik"] = time.monotonic() - mulai
      catatan.append(satu)
    if antrean.ringkas()["tersisa"] == 0:
      break
    time.sleep(JEDA_PUTARAN_DETIK)
  return catatan


def cetak_percobaan(catatan):
  """Mencetak tiap percobaan worker beserta waktunya sejak awal ukur."""
  print(f"  {'Pekerjaan':<{LEBAR_ID}} {'Jenis':<{LEBAR_JENIS}} "
        f"{'Ke':>3} {'Detik':>7}  Hasil")
  for satu in catatan:
    print(f"  {satu['id']:<{LEBAR_ID}} {satu['jenis']:<{LEBAR_JENIS}} "
          f"{satu['percobaan']:>3} {satu['detik']:>7.2f}  {satu['hasil']}")


def cetak_pengiriman(pengiriman):
  """Mencetak pengiriman yang benar-benar tiba di webhook."""
  print(f"  {'Pekerjaan':<{LEBAR_ID}} {'Jenis':<{LEBAR_JENIS}} "
        f"{'Ke':>3} {'Status':>7}")
  for satu in pengiriman:
    print(f"  {satu['id']:<{LEBAR_ID}} {satu['jenis']:<{LEBAR_JENIS}} "
          f"{satu['percobaan']:>3} {satu['status']:>7}")


def main():
  """Menyiapkan antrean, menjalankan daurnya, lalu mencetak kedua tabelnya."""
  antrean.kosongkan()
  kosongkan_webhook()
  for jenis, isi in PEKERJAAN:
    antrean.kirim(jenis, isi)
  catatan = jalankan_daur()
  cetak_percobaan(catatan)
  print()
  cetak_pengiriman(ambil_pengiriman())
  print()
  ringkasan = antrean.ringkas()
  print(f"  Percobaan worker: {len(catatan)}, "
        f"pengiriman tiba: {len(ambil_pengiriman())}, "
        f"pekerjaan tersisa: {ringkasan['tersisa']}, "
        f"ditandai diproses: {ringkasan['diproses']}")


if __name__ == "__main__":
  main()
