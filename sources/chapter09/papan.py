"""Papan operasional sederhana untuk kedua versi layanan.

Angkanya dibaca dari alamat /metrics tiap layanan, lalu ditampilkan
berdampingan. Inilah bentuk paling sederhana sebuah dashboard: beberapa
angka yang sama, dari beberapa sumber, dalam satu layar.

Pemakaian (dari sources/chapter09, setelah kedua layanan menyala):
    python3 papan.py
"""

import json
from pathlib import Path

import metrik

FILE_RILIS = Path(__file__).parent / "rilis.json"
LEBAR_NAMA = 24


def baris_papan(nama, hasil):
  """Menyusun satu baris papan untuk satu versi layanan."""
  permintaan = hasil["permintaan"]
  gagal = hasil["gagal"]
  persen_gagal = (gagal * 100 / permintaan) if permintaan else 0.0
  rata_ms = (hasil["total_ms"] / permintaan) if permintaan else 0.0
  p95 = metrik.persentil_dari_ember(hasil["ember"], permintaan, 95)
  return (f"  {nama:<{LEBAR_NAMA}} {permintaan:>8} {gagal:>7} "
          f"{persen_gagal:>8.1f} {rata_ms:>9.1f} {str(p95):>8}")


def main():
  """Membaca metrik kedua versi, lalu mencetaknya sebagai satu papan."""
  rilis = json.loads(FILE_RILIS.read_text(encoding="utf-8"))
  print(f"  {'Versi':<{LEBAR_NAMA}} {'Minta':>8} {'Gagal':>7} "
        f"{'% gagal':>8} {'Rata ms':>9} {'p95 ms':>8}")
  for kunci in ("versi_pertama", "versi_kedua"):
    tujuan = rilis[kunci]
    hasil = metrik.baca(tujuan["host"], tujuan["port"])
    print(baris_papan(tujuan["nama"], hasil))


if __name__ == "__main__":
  main()
