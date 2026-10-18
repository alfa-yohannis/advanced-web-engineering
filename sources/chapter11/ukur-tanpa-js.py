"""Memeriksa apa yang masih tampil ketika skripnya tidak jalan.

Tiap halaman dibuka dua kali dengan Chrome tanpa jendela. Pembukaan kedua
memakai blokir_skrip=1, yang membuat server memasang CSP penolak skrip,
sehingga halaman terlihat seperti ketika file JavaScript-nya gagal diunduh.
Jumlah baris katalog pada DOM akhir dihitung di kedua pembukaan, sehingga
terlihat bagian mana yang berasal dari server dan bagian mana yang bergantung
pada skrip.

Pemakaian (dari sources/chapter11, setelah aplikasi.py menyala):
    python3 ukur-tanpa-js.py
"""

import pengukur

HALAMAN = [
    "/selektif",
    "/selektif?saring=jaringan",
    "/kerangka/katalog",
    "/kerangka/katalog?saring=jaringan",
]
PENANDA_BARIS = '<li class="kartu"'
PENANDA_FORM = 'name="saring"'
LEBAR_HALAMAN = 34


def tambah_blokir(jalur):
  """Menambahkan blokir_skrip=1 pada satu alamat, apa pun querynya."""
  pemisah = "&" if "?" in jalur else "?"
  return f"{jalur}{pemisah}blokir_skrip=1"


def ukur_halaman(chrome, jalur):
  """Membuka satu halaman dua kali, dengan dan tanpa skrip yang jalan."""
  dom_hidup = pengukur.buka_sekali(chrome, jalur)
  dom_mati = pengukur.buka_sekali(chrome, tambah_blokir(jalur))
  return {
      "jalur": jalur,
      "baris_hidup": dom_hidup.count(PENANDA_BARIS),
      "baris_mati": dom_mati.count(PENANDA_BARIS),
      "form_mati": PENANDA_FORM in dom_mati,
  }


def main():
  """Memeriksa seluruh halaman, lalu mencetak hasilnya sebagai satu tabel."""
  chrome = pengukur.cari_chrome()
  print(f"  {'Halaman':<{LEBAR_HALAMAN}} {'Skrip jalan':>11} "
        f"{'Skrip mati':>10} {'Form':>5}")
  for jalur in HALAMAN:
    hasil = ukur_halaman(chrome, jalur)
    form = "ada" if hasil["form_mati"] else "tiada"
    print(f"  {hasil['jalur']:<{LEBAR_HALAMAN}} {hasil['baris_hidup']:>11} "
          f"{hasil['baris_mati']:>10} {form:>5}")


if __name__ == "__main__":
  main()
