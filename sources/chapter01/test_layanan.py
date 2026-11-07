"""Uji unit lapisan service, tanpa HTTP dan tanpa basis data.

Repository memori dipakai sebagai pengganti SQLite, sehingga tiap uji hanya
memeriksa aturan bisnis dan selesai jauh di bawah satu milidetik. Uji di
lapisan inilah yang paling banyak ditulis.

Pemakaian (dari sources/chapter01):
    python3 -m unittest -v test_layanan
"""

import unittest

from layanan import BukuTidakDitemukan, KesalahanValidasi, LayananKatalog
from repositori import RepositoriBukuMemori

HARGA_CONTOH_RUPIAH = 85_000
STOK_CONTOH = 4
JUDUL_TERLALU_PANJANG = "a" * 201


class UjiTambahBuku(unittest.TestCase):
  """Memeriksa aturan yang menentukan buku mana yang boleh masuk katalog."""

  def setUp(self):
    """Membuat service baru dengan repository memori yang kosong."""
    self.layanan = LayananKatalog(RepositoriBukuMemori())

  def test_buku_sah_tersimpan_dengan_nomor(self):
    """Buku yang sah mendapat nomor 1 sebagai buku pertama."""
    buku = self.layanan.tambah_buku("Basis Data Terapan", HARGA_CONTOH_RUPIAH,
                                    STOK_CONTOH)
    self.assertEqual(buku["nomor"], 1)
    self.assertEqual(buku["judul"], "Basis Data Terapan")

  def test_judul_dirapikan_dari_spasi(self):
    """Spasi di awal dan akhir judul dibuang sebelum disimpan."""
    buku = self.layanan.tambah_buku("  Struktur Data  ", HARGA_CONTOH_RUPIAH,
                                    STOK_CONTOH)
    self.assertEqual(buku["judul"], "Struktur Data")

  def test_judul_kosong_ditolak(self):
    """Judul yang hanya berisi spasi dianggap kosong."""
    with self.assertRaises(KesalahanValidasi):
      self.layanan.tambah_buku("   ", HARGA_CONTOH_RUPIAH, STOK_CONTOH)

  def test_judul_terlalu_panjang_ditolak(self):
    """Judul lebih dari 200 karakter ditolak."""
    with self.assertRaises(KesalahanValidasi):
      self.layanan.tambah_buku(JUDUL_TERLALU_PANJANG, HARGA_CONTOH_RUPIAH,
                               STOK_CONTOH)

  def test_harga_nol_ditolak(self):
    """Buku gratis tidak boleh masuk katalog toko."""
    with self.assertRaises(KesalahanValidasi):
      self.layanan.tambah_buku("Sistem Operasi", 0, STOK_CONTOH)

  def test_harga_bukan_bilangan_bulat_ditolak(self):
    """Harga berupa teks atau true dari JSON ditolak."""
    for harga in ["85000", True, 85000.5]:
      with self.subTest(harga=harga):
        with self.assertRaises(KesalahanValidasi):
          self.layanan.tambah_buku("Sistem Operasi", harga, STOK_CONTOH)

  def test_stok_negatif_ditolak(self):
    """Stok di bawah nol tidak mungkin terjadi di gudang sungguhan."""
    with self.assertRaises(KesalahanValidasi):
      self.layanan.tambah_buku("Jaringan Komputer", HARGA_CONTOH_RUPIAH, -1)


class UjiCariBuku(unittest.TestCase):
  """Memeriksa pencarian dan daftar buku."""

  def setUp(self):
    """Membuat service berisi dua buku."""
    self.layanan = LayananKatalog(RepositoriBukuMemori())
    self.layanan.tambah_buku("Basis Data Terapan", HARGA_CONTOH_RUPIAH,
                             STOK_CONTOH)
    self.layanan.tambah_buku("Struktur Data", HARGA_CONTOH_RUPIAH, STOK_CONTOH)

  def test_nomor_yang_ada_ditemukan(self):
    """Nomor yang ada mengembalikan bukunya."""
    self.assertEqual(self.layanan.cari(2)["judul"], "Struktur Data")

  def test_nomor_yang_tidak_ada_menimbulkan_kesalahan(self):
    """Nomor yang tidak ada menimbulkan BukuTidakDitemukan, bukan None."""
    with self.assertRaises(BukuTidakDitemukan):
      self.layanan.cari(99)

  def test_daftar_terurut_menurut_nomor(self):
    """Daftar buku selalu terurut menurut nomornya."""
    nomor = [buku["nomor"] for buku in self.layanan.daftar()]
    self.assertEqual(nomor, [1, 2])


if __name__ == "__main__":
  unittest.main()
