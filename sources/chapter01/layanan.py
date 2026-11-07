"""Lapisan service katalog: aturan bisnis, tanpa HTTP dan tanpa SQL.

Seluruh aturan tentang buku yang sah tinggal di sini. Lapisan route di atasnya
hanya menerjemahkan HTTP, dan lapisan repository di bawahnya hanya menyimpan.
Karena itu aturan ini dapat diuji tanpa server dan tanpa basis data, cukup
dengan repository memori.

Modul ini diimpor, bukan dijalankan langsung:
    python3 aplikasi.py
"""

PANJANG_JUDUL_MAKSIMUM = 200
HARGA_MINIMUM_RUPIAH = 1
STOK_MINIMUM = 0


class KesalahanValidasi(Exception):
  """Masukan melanggar aturan katalog. Route menerjemahkannya menjadi 400."""


class BukuTidakDitemukan(Exception):
  """Nomor buku yang diminta tidak ada. Route menerjemahkannya menjadi 404."""


def bilangan_bulat(nilai):
  """Memeriksa bilangan bulat sungguhan.

  True dan False juga bertipe int di Python, sehingga keduanya ditolak secara
  khusus. Tanpa itu, harga true dari JSON akan dibaca sebagai Rp1.
  """
  return isinstance(nilai, int) and not isinstance(nilai, bool)


class LayananKatalog:
  """Aturan bisnis katalog, dengan repository yang diberikan dari luar."""

  def __init__(self, repositori):
    """Menerima repository dari pemanggil, bukan membuatnya sendiri.

    Dengan cara ini aplikasi memberi SQLite, sedangkan uji unit memberi
    repository memori, tanpa satu baris pun di lapisan ini yang berubah.
    """
    self.repositori = repositori

  def tambah_buku(self, judul, harga, stok):
    """Memeriksa satu buku baru terhadap aturan katalog, lalu menyimpannya."""
    judul = judul.strip() if isinstance(judul, str) else ""
    if not judul:
      raise KesalahanValidasi("judul wajib diisi")
    if len(judul) > PANJANG_JUDUL_MAKSIMUM:
      raise KesalahanValidasi(
          f"judul paling panjang {PANJANG_JUDUL_MAKSIMUM} karakter")
    if not bilangan_bulat(harga) or harga < HARGA_MINIMUM_RUPIAH:
      raise KesalahanValidasi("harga harus bilangan bulat positif")
    if not bilangan_bulat(stok) or stok < STOK_MINIMUM:
      raise KesalahanValidasi("stok harus bilangan bulat, tidak negatif")
    return self.repositori.simpan(judul, harga, stok)

  def cari(self, nomor):
    """Mengambil satu buku, atau menimbulkan BukuTidakDitemukan."""
    buku = self.repositori.ambil(nomor)
    if buku is None:
      raise BukuTidakDitemukan(f"buku nomor {nomor} tidak ada")
    return buku

  def daftar(self):
    """Mengambil seluruh buku di katalog, terurut menurut nomornya."""
    return self.repositori.semua()
