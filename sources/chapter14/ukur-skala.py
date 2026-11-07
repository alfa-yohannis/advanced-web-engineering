"""Mengukur penskalaan horizontal pada 1, 2, 4, dan 8 replika.

Untuk tiap jumlah replika, skrip ini menyalakan replika dan penyeimbang beban
sebagai proses terpisah, lalu melepas sejumlah worker yang mengirim
permintaan berurutan lewat penyeimbang. Basis data tiruan dinyalakan sekali
untuk seluruh pengukuran, karena dialah komponen bersama yang sengaja tidak
ikut bertambah.

Bentuk bebannya closed loop, sama seperti Bab 5: tiap worker menunggu response
sebelum mengirim permintaan berikutnya. Yang dilaporkan jumlah permintaan per
detik, p50, p95, dan efisiensi, yaitu throughput dibagi jumlah replika kali
throughput satu replika.

Peringatan: skrip ini sengaja membebani. Seluruh prosesnya dinyalakan sendiri
di komputer ini pada 127.0.0.1, dan tidak boleh diarahkan ke sistem milik
orang lain.

Pemakaian (dari sources/chapter14):
    python3 ukur-skala.py
    JUMLAH_KONEKSI=16 python3 ukur-skala.py
"""

import os
import threading
import time
from http.client import HTTPConnection, HTTPException

import pengukur

HOST = "127.0.0.1"
PORT_PENYEIMBANG = 8110
PORT_REPLIKA_PERTAMA = 8111
PORT_BASIS_DATA = 8119
DAFTAR_JUMLAH_REPLIKA = [1, 2, 4, 8]
JUMLAH_WORKER = 32
# Permintaan pada detik pertama tidak dihitung, agar sambungan dan utas yang
# baru dibuka tidak ikut menjadi angka.
LAMA_WARMUP_DETIK = 1.0
LAMA_UKUR_DETIK = 5.0
BATAS_WAKTU_DETIK = 30
JUMLAH_PENGGUNA = 1000
PENGALI_PENGGUNA = 7919
PERSEN = 100


def jalankan_worker(nomor_worker, keadaan):
  """Mengirim permintaan berurutan lewat satu sambungan sampai disuruh berhenti.

  Tiap permintaan yang selesai dicatat bersama waktu selesainya. Pemilahan
  mana yang masuk jendela pengukuran dilakukan sesudahnya, bukan di sini.
  """
  koneksi = HTTPConnection(HOST, PORT_PENYEIMBANG, timeout=BATAS_WAKTU_DETIK)
  urutan = 0
  while not keadaan["berhenti"].is_set():
    nomor_pengguna = (nomor_worker * PENGALI_PENGGUNA + urutan) % JUMLAH_PENGGUNA
    urutan += 1
    mulai = time.monotonic()
    try:
      koneksi.request("GET", f"/rekomendasi/{nomor_pengguna}")
      response = koneksi.getresponse()
      response.read()
    except (OSError, HTTPException):
      koneksi.close()
      koneksi = HTTPConnection(HOST, PORT_PENYEIMBANG, timeout=BATAS_WAKTU_DETIK)
      continue
    selesai = time.monotonic()
    if response.status == 200:
      keadaan["catatan"].append((selesai, (selesai - mulai) * 1000))
  koneksi.close()


def ukur_beban():
  """Melepas seluruh worker, lalu menghitung hasil di jendela pengukuran."""
  keadaan = {"berhenti": threading.Event(), "catatan": []}
  daftar_utas = [
      threading.Thread(target=jalankan_worker, args=(nomor, keadaan))
      for nomor in range(JUMLAH_WORKER)
  ]
  mulai_ukur = time.monotonic() + LAMA_WARMUP_DETIK
  selesai_ukur = mulai_ukur + LAMA_UKUR_DETIK
  for utas in daftar_utas:
    utas.start()
  time.sleep(selesai_ukur - time.monotonic())
  keadaan["berhenti"].set()
  for utas in daftar_utas:
    utas.join()
  lama_ms = [lama for selesai, lama in keadaan["catatan"]
             if mulai_ukur <= selesai < selesai_ukur]
  return {
      "rps": len(lama_ms) / LAMA_UKUR_DETIK,
      "p50_ms": pengukur.hitung_persentil(lama_ms, 50),
      "p95_ms": pengukur.hitung_persentil(lama_ms, 95),
  }


def ukur_satu_jumlah(jumlah_replika):
  """Menyalakan sejumlah replika dan penyeimbangnya, mengukur, lalu mematikan."""
  daftar_port = [PORT_REPLIKA_PERTAMA + urutan for urutan in range(jumlah_replika)]
  daftar_proses = [pengukur.nyalakan("layanan.py", {"PORT": str(port)})
                   for port in daftar_port]
  for port in daftar_port:
    pengukur.tunggu_port(port)
  daftar_replika = ",".join(str(port) for port in daftar_port)
  daftar_proses.append(
      pengukur.nyalakan("penyeimbang.py", {"REPLIKA": daftar_replika}))
  pengukur.tunggu_port(PORT_PENYEIMBANG)
  try:
    return ukur_beban()
  finally:
    pengukur.matikan(daftar_proses)


def main():
  """Mengukur seluruh jumlah replika, lalu mencetak hasilnya sebagai tabel."""
  koneksi_basis_data = os.environ.get("JUMLAH_KONEKSI", "4")
  basis_data = pengukur.nyalakan("basis_data_tiruan.py")
  pengukur.tunggu_port(PORT_BASIS_DATA)
  print(f"  {JUMLAH_WORKER} worker, basis data tiruan {koneksi_basis_data} "
        f"koneksi, {LAMA_UKUR_DETIK:.0f} detik tiap baris\n")
  print(f"  {'Replika':>7} {'Permintaan/detik':>17} {'p50 ms':>8} "
        f"{'p95 ms':>8} {'Efisiensi':>10}")
  try:
    rps_satu_replika = None
    for jumlah_replika in DAFTAR_JUMLAH_REPLIKA:
      hasil = ukur_satu_jumlah(jumlah_replika)
      if rps_satu_replika is None:
        rps_satu_replika = hasil["rps"]
      efisiensi = hasil["rps"] / (jumlah_replika * rps_satu_replika) * PERSEN
      print(f"  {jumlah_replika:>7} {hasil['rps']:>17.1f} "
            f"{hasil['p50_ms']:>8.1f} {hasil['p95_ms']:>8.1f} "
            f"{efisiensi:>9.0f}%", flush=True)
  finally:
    pengukur.matikan([basis_data])


if __name__ == "__main__":
  main()
