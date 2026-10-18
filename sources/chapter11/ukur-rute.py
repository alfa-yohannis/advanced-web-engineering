"""Membandingkan biaya satu perpindahan: dokumen penuh lawan fragmen.

Pada application shell, perpindahan halaman hanya mengganti isi wilayah.
Yang diunduh adalah fragmen, bukan dokumen beserta kerangka, gaya, dan
skripnya. Skrip ini mengambil kedua alamat untuk tujuan yang sama, lalu
mencetak ukuran keduanya berdampingan.

Pemakaian (dari sources/chapter11, setelah aplikasi.py menyala):
    python3 ukur-rute.py
"""

import pengukur

TUJUAN = ["/katalog", "/katalog?saring=jaringan", "/buku/3", "/gagal"]
LEBAR_TUJUAN = 24


def ukur_tujuan(tujuan):
  """Mengukur satu tujuan sebagai dokumen penuh dan sebagai fragmen."""
  status_dokumen, byte_dokumen = pengukur.ambil_response(f"/kerangka{tujuan}")
  status_fragmen, byte_fragmen = pengukur.ambil_response(f"/fragmen{tujuan}")
  return {
      "tujuan": tujuan,
      "status": f"{status_dokumen}/{status_fragmen}",
      "dokumen": byte_dokumen,
      "fragmen": byte_fragmen,
      "bagian": 100 * byte_fragmen / byte_dokumen,
  }


def main():
  """Mengukur seluruh tujuan, lalu mencetak hasilnya sebagai satu tabel."""
  print(f"  {'Tujuan':<{LEBAR_TUJUAN}} {'Status':>7} {'Dokumen':>9} "
        f"{'Fragmen':>9} {'Fragmen %':>10}")
  for tujuan in TUJUAN:
    hasil = ukur_tujuan(tujuan)
    print(f"  {hasil['tujuan']:<{LEBAR_TUJUAN}} {hasil['status']:>7} "
          f"{hasil['dokumen']:>9} {hasil['fragmen']:>9} "
          f"{hasil['bagian']:>9.1f}%")


if __name__ == "__main__":
  main()
