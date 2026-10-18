"""Mengukur biaya hidrasi kedua varian halaman, lalu mencetak tabelnya.

Halaman sendiri yang mengukur dirinya dengan performance.now(), lalu
menuliskan hasilnya ke paragraf laporan. Skrip ini membuka halaman itu
dengan Chrome tanpa jendela, membaca paragraf tersebut, dan mengulanginya
beberapa kali agar yang dilaporkan adalah nilai tengah, bukan satu kebetulan.

Ukuran HTML dan ukuran file JavaScript ikut diambil, karena biaya hidrasi
bukan hanya waktu CPU: state yang dititipkan server ikut menambah byte yang
harus diunduh dan diurai.

Pemakaian (dari sources/chapter11, setelah aplikasi.py menyala):
    python3 ukur-hidrasi.py
    JUMLAH_BUKU=1000 python3 aplikasi.py   # lalu ukur sekali lagi
"""

import re
import statistics

import pengukur

ULANGAN = 5
VARIAN = [
    ("penuh", "/penuh", "hidrasi-penuh.js"),
    ("selektif", "/selektif", "hidrasi-selektif.js"),
]
POLA_LAPORAN = re.compile(
    r"(\w+): (\d+) buku, (\d+) komponen dihidupkan, ([\d.]+) ms")
LEBAR_NAMA = 9


def baca_laporan(dom):
  """Membaca baris laporan dari DOM, lalu memecahnya menjadi angka."""
  cocok = POLA_LAPORAN.search(dom)
  if not cocok:
    raise SystemExit("Baris laporan tidak ditemukan. Periksa console "
                     "browser pada halaman tersebut.")
  return {
      "buku": int(cocok.group(2)),
      "komponen": int(cocok.group(3)),
      "lama_ms": float(cocok.group(4)),
  }


def ukur_varian(chrome, jalur, nama_skrip):
  """Mengukur satu varian sebanyak ULANGAN kali, lalu merangkumnya."""
  laporan = [baca_laporan(pengukur.buka_sekali(chrome, jalur))
             for _ in range(ULANGAN)]
  lama = sorted(satu["lama_ms"] for satu in laporan)
  return {
      "buku": laporan[0]["buku"],
      "komponen": laporan[0]["komponen"],
      "html_byte": pengukur.ambil_response(jalur)[1],
      "js_byte": pengukur.ambil_response(f"/aset/{nama_skrip}")[1],
      "tengah_ms": statistics.median(lama),
      "rentang": f"{lama[0]:.2f}-{lama[-1]:.2f}",
  }


def main():
  """Mengukur kedua varian, lalu mencetak hasilnya sebagai satu tabel."""
  chrome = pengukur.cari_chrome()
  print(f"  {'Varian':<{LEBAR_NAMA}} {'Buku':>5} {'Komponen':>9} "
        f"{'HTML byte':>10} {'JS byte':>8} {'Tengah ms':>10} "
        f"{'Rentang ms':>12}")
  for nama, jalur, nama_skrip in VARIAN:
    hasil = ukur_varian(chrome, jalur, nama_skrip)
    print(f"  {nama:<{LEBAR_NAMA}} {hasil['buku']:>5} "
          f"{hasil['komponen']:>9} {hasil['html_byte']:>10} "
          f"{hasil['js_byte']:>8} {hasil['tengah_ms']:>10.2f} "
          f"{hasil['rentang']:>12}")


if __name__ == "__main__":
  main()
