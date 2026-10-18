"""Menilai layanan terhadap Service Level Objective, lalu memberi verdict.

Alarm ini keluar dengan status 1 bila ada satu saja tujuan yang tidak
terpenuhi, sehingga dapat dipasang di penjadwal atau di Continuous
Integration sesudah rilis.

Yang dinilai hanya angka yang sudah dikumpulkan layanan sendiri, sehingga
alarm ini tidak menambah beban apa pun pada layanan yang diawasi.

Pemakaian (dari sources/chapter09, setelah kedua layanan menyala):
    python3 alarm.py [slo.json]
"""

import json
import sys
from pathlib import Path

import metrik

FILE_SLO_BAWAAN = Path(__file__).parent / "slo.json"
FILE_RILIS = Path(__file__).parent / "rilis.json"
LEBAR_NAMA = 34


def nilai_satu_versi(tujuan, slo):
  """Menilai satu versi layanan terhadap seluruh tujuan pada SLO."""
  hasil = metrik.baca(tujuan["host"], tujuan["port"])
  permintaan = hasil["permintaan"]
  nama = tujuan["nama"]
  if permintaan < slo["jendela_permintaan_minimum"]:
    return [(f"{nama}: jumlah permintaan", slo["jendela_permintaan_minimum"],
             permintaan, False)]

  ketersediaan = (permintaan - hasil["gagal"]) * 100 / permintaan
  p95_teks = metrik.persentil_dari_ember(hasil["ember"], permintaan, 95)
  p95 = float("inf") if p95_teks in (None, "+Inf") else float(p95_teks)
  return [
      (f"{nama}: ketersediaan persen", slo["ketersediaan_persen_minimum"],
       round(ketersediaan, 2),
       ketersediaan >= slo["ketersediaan_persen_minimum"]),
      (f"{nama}: p95 milidetik", slo["p95_milidetik_maksimum"], p95_teks,
       p95 <= slo["p95_milidetik_maksimum"]),
  ]


def cetak_baris(baris):
  """Mencetak satu baris penilaian, lengkap dengan verdict-nya."""
  nama, tujuan, terukur, lolos = baris
  verdict = "lolos" if lolos else "LANGGAR"
  print(f"  {nama:<{LEBAR_NAMA}} {str(tujuan):>8} {str(terukur):>10} "
        f"  {verdict}")


def main():
  """Menilai kedua versi terhadap SLO, lalu memberi verdict akhirnya."""
  nama_file = sys.argv[1] if len(sys.argv) > 1 else FILE_SLO_BAWAAN
  slo = json.loads(Path(nama_file).read_text(encoding="utf-8"))
  rilis = json.loads(FILE_RILIS.read_text(encoding="utf-8"))
  print(f"  {'Tujuan':<{LEBAR_NAMA}} {'SLO':>8} {'Terukur':>10}   Verdict")

  daftar_baris = []
  for kunci in ("versi_pertama", "versi_kedua"):
    daftar_baris.extend(nilai_satu_versi(rilis[kunci], slo))
  for baris in daftar_baris:
    cetak_baris(baris)

  jumlah_langgar = sum(1 for baris in daftar_baris if not baris[-1])
  if jumlah_langgar:
    print(f"\nGagal: {jumlah_langgar} tujuan SLO tidak terpenuhi.")
    sys.exit(1)
  print("\nLolos: seluruh tujuan SLO terpenuhi.")


if __name__ == "__main__":
  main()
