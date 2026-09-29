#!/usr/bin/env python3
"""Menjalankan seluruh pemeriksaan mutu Bab 6, lalu memberi satu vonis.

Lima jenis pemeriksaan dijalankan berurutan, dari yang paling murah:

  1. Unit test, yang tidak menyentuh basis data maupun jaringan.
  2. Integration test dan contract test, yang menyentuh basis data sungguhan.
  3. Coverage baris pada modul aturan harga, dibandingkan dengan ambangnya.
  4. Analisis statis dengan ruff.
  5. Jumlah query tiap alamat, dibaca dari header X-Query-Count.

Gate keluar dengan status 1 bila ada satu saja batas yang dilanggar, sehingga
Continuous Integration dapat memakainya untuk memblokir merge. Seluruh angka
batas ditulis di mutu.json, bukan di dalam kode ini, sehingga menaikkan atau
menurunkan standar terbaca sebagai satu perubahan file.

Peringatan: gate ini menyalakan aplikasinya sendiri dan mengirim permintaan
kepadanya. Seluruh permintaan hanya ditujukan ke aplikasi di komputer sendiri,
dan tidak ada satu pun yang keluar dari mesin ini.

Pemakaian (dari sources/chapter06, setelah docker compose up -d dan
./siapkan-data.sh):
    source ../.venv/bin/activate
    python gate-mutu.py [mutu.json]
"""

import json
import subprocess
import sys
import threading
import time
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

import aplikasi

FILE_MUTU_BAWAAN = Path(__file__).parent / "mutu.json"
DIREKTORI_KERJA = Path(__file__).parent
BATAS_WAKTU_HTTP_DETIK = 10
LEBAR_NAMA = 36
# Ruff memakai status 1 untuk "ada temuan" dan status di atas 1 untuk gagal
# menjalankan pemeriksaannya, misalnya karena pengaturannya salah.
STATUS_RUFF_ADA_TEMUAN = 1


def baca_mutu(nama_file):
  """Membaca file standar mutu, yaitu satu-satunya tempat angka batas ditulis."""
  return json.loads(Path(nama_file).read_text(encoding="utf-8"))


def jalankan_perintah(argumen):
  """Menjalankan satu perintah di direktori bab ini, lalu melaporkan hasilnya.

  Keluaran standar dan keluaran error digabung, karena yang dibutuhkan gate
  hanya angka di dalamnya, bukan asal salurannya.

  Mengembalikan pasangan (status keluar, keluaran sebagai teks).
  """
  hasil = subprocess.run(argumen, cwd=DIREKTORI_KERJA, capture_output=True,
                         text=True, check=False)
  return hasil.returncode, hasil.stdout + hasil.stderr


def nilai_lapisan_pengujian(lapisan):
  """Menjalankan satu lapisan pengujian, lalu menilai hasil dan waktunya.

  Dua hal dinilai sekaligus. Pertama, semua pengujiannya harus lulus. Kedua,
  lapisan itu harus selesai di dalam waktu yang dianggarkan, karena lapisan
  yang lambat akhirnya dilewati orang dan berhenti melindungi apa pun.

  Mengembalikan dua baris penilaian.
  """
  perintah = [sys.executable, "-m", "pytest", "-q", *lapisan["file"]]
  waktu_mulai = time.perf_counter()
  status, _ = jalankan_perintah(perintah)
  detik = time.perf_counter() - waktu_mulai
  nama = lapisan["nama"]
  return [
      (f"pytest {nama}", 0, status, "", status == 0),
      (f"waktu {nama}", lapisan["maksimum_detik"], round(detik, 2), "s",
       detik <= lapisan["maksimum_detik"]),
  ]


def nilai_coverage(pengaturan):
  """Mengukur coverage baris satu modul, lalu membandingkannya dengan ambangnya.

  Angka ini sengaja dipasang walaupun bab ini justru menunjukkan batasnya.
  Coverage berguna untuk menemukan bagian yang belum tersentuh sama sekali,
  dan tidak berguna untuk membuktikan pengujiannya bermutu.

  Mengembalikan satu baris penilaian.
  """
  perintah_ukur = [sys.executable, "-m", "coverage", "run",
                   f"--include={pengaturan['modul']}", "-m", "pytest", "-q",
                   *pengaturan["file"]]
  jalankan_perintah(perintah_ukur)
  perintah_laporan = [sys.executable, "-m", "coverage", "report",
                      "--format=total"]
  status, keluaran = jalankan_perintah(perintah_laporan)
  minimum = pengaturan["minimum_persen"]
  if status != 0:
    return ("coverage " + pengaturan["modul"], minimum, None, "%", False)
  persen = int(keluaran.strip())
  return ("coverage " + pengaturan["modul"], minimum, persen, "%",
          persen >= minimum)


def nilai_analisis_statis(pengaturan):
  """Menjalankan ruff, lalu menghitung berapa temuan yang dilaporkannya.

  Keluaran JSON dipakai agar hitungannya tidak bergantung pada susunan teks
  laporan. Status keluar di atas satu berarti ruff sendiri gagal berjalan, dan
  keadaan itu dinilai tidak lolos, bukan diabaikan.

  Mengembalikan satu baris penilaian.
  """
  maksimum = pengaturan["maksimum_temuan"]
  status, keluaran = jalankan_perintah(["ruff", "check", "--output-format=json",
                                        "."])
  if status > STATUS_RUFF_ADA_TEMUAN:
    return ("temuan ruff", maksimum, None, "", False)
  jumlah = len(json.loads(keluaran))
  return ("temuan ruff", maksimum, jumlah, "", jumlah <= maksimum)


def nyalakan_aplikasi():
  """Menyalakan aplikasi di utas terpisah pada port yang dipilih sistem.

  Gate menyalakan aplikasinya sendiri, sehingga hasilnya tidak bergantung pada
  ada atau tidaknya aplikasi yang sedang dijalankan tangan. Port 0 meminta port
  bebas, sehingga gate tidak berebut port 8020.
  """
  server = ThreadingHTTPServer((aplikasi.HOST, 0), aplikasi.PenanganPesanan)
  utas = threading.Thread(target=server.serve_forever, daemon=True)
  utas.start()
  return server


def hitung_query_alamat(alamat_server, jalur):
  """Meminta satu alamat, lalu membaca jumlah querynya dari header jawaban.

  Angka ini diambil dari luar aplikasi, bukan dari membaca kodenya, sehingga
  cacat N+1 tetap terbaca walaupun kodenya sudah ditulis ulang.
  """
  host, port = alamat_server
  koneksi = HTTPConnection(host, port, timeout=BATAS_WAKTU_HTTP_DETIK)
  koneksi.request("GET", jalur)
  jawaban = koneksi.getresponse()
  jawaban.read()
  jumlah = int(jawaban.getheader("X-Query-Count"))
  koneksi.close()
  return jumlah


def nilai_query_alamat(alamat_server, batas_alamat):
  """Menilai jumlah query satu alamat terhadap batas yang ditetapkan.

  Mengembalikan satu baris penilaian.
  """
  jalur = batas_alamat["jalur"]
  jumlah = hitung_query_alamat(alamat_server, jalur)
  maksimum = batas_alamat["maksimum"]
  return (f"query {jalur}", maksimum, jumlah, "", jumlah <= maksimum)


def nilai_seluruh_alamat(daftar_batas):
  """Menyalakan aplikasi sekali, menilai seluruh alamat, lalu mematikannya."""
  server = nyalakan_aplikasi()
  try:
    return [nilai_query_alamat(server.server_address, batas_alamat)
            for batas_alamat in daftar_batas]
  finally:
    server.shutdown()
    server.server_close()


def cetak_baris(baris):
  """Mencetak satu baris penilaian, lengkap dengan vonisnya."""
  nama, batas, terukur, satuan, lolos = baris
  teks_terukur = "gagal jalan" if terukur is None else f"{terukur} {satuan}"
  vonis = "lolos" if lolos else "LANGGAR"
  print(f"  {nama:<{LEBAR_NAMA}} {batas:>8} {satuan:<3} "
        f"{teks_terukur:>14}  {vonis}")


def main():
  """Menjalankan seluruh pemeriksaan, mencetak tabelnya, lalu memberi vonis."""
  nama_file = sys.argv[1] if len(sys.argv) > 1 else FILE_MUTU_BAWAAN
  mutu = baca_mutu(nama_file)
  print(f"  {'Pemeriksaan':<{LEBAR_NAMA}} {'Batas':>8}     {'Terukur':>14}"
        "  Vonis")

  daftar_baris = []
  for lapisan in mutu["lapisan_pengujian"]:
    daftar_baris.extend(nilai_lapisan_pengujian(lapisan))
  daftar_baris.append(nilai_coverage(mutu["coverage"]))
  daftar_baris.append(nilai_analisis_statis(mutu["analisis_statis"]))
  daftar_baris.extend(nilai_seluruh_alamat(mutu["query_per_alamat"]))
  for baris in daftar_baris:
    cetak_baris(baris)

  jumlah_langgar = sum(1 for baris in daftar_baris if not baris[-1])
  if jumlah_langgar:
    print(f"\nGagal: {jumlah_langgar} batas mutu dilanggar.")
    sys.exit(1)
  print("\nLolos: seluruh batas mutu terpenuhi.")


if __name__ == "__main__":
  main()
