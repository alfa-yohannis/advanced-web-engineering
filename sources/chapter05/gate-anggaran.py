#!/usr/bin/env python3
"""Menilai hasil pengukuran terhadap anggaran performa, lalu memberi vonis.

Gate ini keluar dengan status 1 bila ada satu saja anggaran yang
terlampaui, sehingga dapat dipasang di Continuous Integration untuk memblokir
merge. Latensi dan ukuran jawaban diukur ulang saat gate dijalankan,
sedangkan Core Web Vitals dibaca dari laporan browser di vitals.jsonl.

Peringatan: gate ini ikut membebani aplikasi, karena memanggil beban.py.
Arahkan hanya ke aplikasi sendiri.

Pemakaian (dari sources/chapter05, setelah aplikasi.py menyala):
    source ../.venv/bin/activate
    python gate-anggaran.py [anggaran.json]
"""

import json
import sys
import time
from pathlib import Path

from beban import hitung_persentil, ukur_beban

BERKAS_ANGGARAN_BAWAAN = Path(__file__).parent / "anggaran.json"
BERKAS_VITALS = Path(__file__).parent / "vitals.jsonl"
# Core Web Vitals dinilai pada persentil 75 dari kunjungan nyata.
PERSENTIL_VITALS = 75
# Permintaan pemanasan sebelum tiap pengukuran, agar cache basis data hangat.
PERMINTAAN_PEMANASAN = 30
# Jeda sebelum tiap pengukuran, agar sisa beban alamat sebelumnya reda.
JEDA_ANTAR_ALAMAT_DETIK = 3
LEBAR_NAMA = 38


def baca_anggaran(nama_berkas):
  """Membaca berkas anggaran, yaitu satu-satunya tempat angka target ditulis."""
  return json.loads(Path(nama_berkas).read_text(encoding="utf-8"))


def nilai_alamat(anggaran_alamat, beban):
  """Mengukur satu alamat, lalu menilai latensi p95 dan ukuran jawabannya.

  Tiap alamat dipanaskan lebih dahulu. Tanpa pemanasan, alamat yang diukur
  sesudah alamat berat menanggung cache basis data yang baru saja tersapu,
  dan vonisnya menghukum urutan pengukuran, bukan alamatnya.

  Mengembalikan daftar baris penilaian, masing-masing berisi nama, angka
  anggaran, angka terukur, satuan, dan vonisnya.
  """
  time.sleep(JEDA_ANTAR_ALAMAT_DETIK)
  ukur_beban(anggaran_alamat["jalur"], 1, PERMINTAAN_PEMANASAN)
  hasil = ukur_beban(anggaran_alamat["jalur"], beban["jumlah_worker"],
                     beban["permintaan_per_worker"])
  jalur = anggaran_alamat["jalur"]
  return [
      (f"{jalur} p95", anggaran_alamat["p95_ms"], hasil["p95_ms"], "ms",
       hasil["p95_ms"] <= anggaran_alamat["p95_ms"]),
      (f"{jalur} ukuran", anggaran_alamat["maks_kb"], hasil["kb"], "KB",
       hasil["kb"] <= anggaran_alamat["maks_kb"]),
  ]


def baca_laporan_vitals():
  """Membaca seluruh laporan Core Web Vitals yang dikirim browser.

  Berkasnya berformat JSON Lines, satu laporan per baris, sehingga laporan
  baru cukup ditambahkan di akhir tanpa membaca ulang isinya.
  """
  if not BERKAS_VITALS.exists():
    return []
  daftar_laporan = []
  for baris in BERKAS_VITALS.read_text(encoding="utf-8").splitlines():
    if baris.strip():
      daftar_laporan.append(json.loads(baris))
  return daftar_laporan


def nilai_vitals(anggaran_vitals, daftar_laporan):
  """Menilai ketiga Core Web Vitals pada persentil 75 dari laporan browser.

  Tanpa laporan sama sekali, ketiganya dinyatakan tidak lolos. Perbaikan
  tanpa bukti pengukuran memang tidak dihitung.
  """
  satuan_per_metrik = {"lcp_ms": "ms", "inp_ms": "ms", "cls": ""}
  daftar_baris = []
  for nama_metrik, batas in anggaran_vitals.items():
    angka = [laporan[nama_metrik] for laporan in daftar_laporan
             if nama_metrik in laporan]
    satuan = satuan_per_metrik.get(nama_metrik, "")
    if not angka:
      daftar_baris.append((f"{nama_metrik} p75", batas, None, satuan, False))
      continue
    terukur = hitung_persentil(angka, PERSENTIL_VITALS)
    daftar_baris.append((f"{nama_metrik} p75", batas, terukur, satuan,
                         terukur <= batas))
  return daftar_baris


def cetak_baris(baris):
  """Mencetak satu baris penilaian, lengkap dengan vonisnya."""
  nama, anggaran, terukur, satuan, lolos = baris
  teks_terukur = "tidak ada data" if terukur is None else f"{terukur:.2f} {satuan}"
  vonis = "lolos" if lolos else "LEWAT"
  print(f"  {nama:<{LEBAR_NAMA}} {anggaran:>8} {satuan:<3} "
        f"{teks_terukur:>16}  {vonis}")


def main():
  """Mengukur seluruh alamat pada anggaran, lalu memberi vonis akhirnya."""
  nama_berkas = sys.argv[1] if len(sys.argv) > 1 else BERKAS_ANGGARAN_BAWAAN
  anggaran = baca_anggaran(nama_berkas)
  beban = anggaran["beban"]
  print(f"{beban['jumlah_worker']} worker, "
        f"{beban['permintaan_per_worker']} permintaan per worker\n")
  print(f"  {'Ukuran':<{LEBAR_NAMA}} {'Anggaran':>8}     {'Terukur':>16}  Vonis")

  daftar_baris = []
  for anggaran_alamat in anggaran["alamat"]:
    daftar_baris.extend(nilai_alamat(anggaran_alamat, beban))
  daftar_baris.extend(
      nilai_vitals(anggaran["core_web_vitals"], baca_laporan_vitals())
  )
  for baris in daftar_baris:
    cetak_baris(baris)

  jumlah_lewat = sum(1 for baris in daftar_baris if not baris[-1])
  if jumlah_lewat:
    print(f"\nGagal: {jumlah_lewat} anggaran terlampaui.")
    sys.exit(1)
  print("\nLolos: seluruh anggaran terpenuhi.")


if __name__ == "__main__":
  main()
