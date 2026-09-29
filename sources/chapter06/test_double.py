"""Peragaan test double: dummy, stub, fake, dan mock.

Keempatnya sama-sama menggantikan layanan biaya kirim yang sungguhan, tetapi
menjawab pertanyaan yang berbeda. Stub menjawab "apa hasilnya bila layanan
menjawab X". Fake menjawab "apakah aturannya benar untuk banyak masukan".
Mock menjawab "apakah layanannya benar-benar dipanggil, dan dengan argumen
apa". Dummy hanya mengisi tempat yang tidak pernah dipakai.

Pemakaian (dari sources/chapter06):
    source ../.venv/bin/activate
    pytest test_double.py
"""

from unittest.mock import Mock

import layanan_kirim

TARIF_STUB_RUPIAH = 18000
KODE_POS_JAKARTA = "10110"
KODE_POS_LUAR_JAWA = "94111"
BERAT_GRAM = 1200


class StubBiayaKirim:
  """Selalu menjawab satu tarif yang sama, apa pun yang ditanyakan.

  Dipakai untuk menguji jalur berhasil tanpa peduli isi jawabannya.
  """

  def minta_biaya(self, kode_pos, berat_gram):
    """Mengembalikan tarif tetap, mengabaikan kedua argumennya."""
    return TARIF_STUB_RUPIAH


class FakeBiayaKirim:
  """Tiruan sederhana yang berisi aturan tarif, bukan sekadar nilai tetap.

  Cukup pintar untuk dipakai banyak pengujian sekaligus, tetapi tetap berjalan
  di dalam memori tanpa jaringan.
  """

  def minta_biaya(self, kode_pos, berat_gram):
    """Menghitung tarif dari kode pos dan berat, meniru aturan layanan asli."""
    tarif_dasar = 15000 if kode_pos.startswith("1") else 32000
    return tarif_dasar + (berat_gram // 1000) * 5000


class KlienGagal:
  """Selalu gagal, meniru layanan yang sedang down.

  Dipakai menguji jalur cadangan, yang sulit dimunculkan dengan layanan asli.
  """

  def minta_biaya(self, kode_pos, berat_gram):
    """Melempar OSError, persis seperti koneksi yang ditolak."""
    raise OSError("layanan biaya kirim tidak menjawab")


def test_stub_memberi_tarif_tetap():
  """Jalur berhasil memakai tarif dari layanan apa adanya."""
  ongkir = layanan_kirim.hitung_ongkir(StubBiayaKirim(), KODE_POS_JAKARTA,
                                       BERAT_GRAM, gratis_ongkir=False)
  assert ongkir == TARIF_STUB_RUPIAH


def test_fake_membedakan_tujuan_dan_berat():
  """Fake dipakai untuk memeriksa beberapa masukan sekaligus."""
  fake = FakeBiayaKirim()
  dekat = layanan_kirim.hitung_ongkir(fake, KODE_POS_JAKARTA, BERAT_GRAM,
                                      gratis_ongkir=False)
  jauh = layanan_kirim.hitung_ongkir(fake, KODE_POS_LUAR_JAWA, BERAT_GRAM,
                                     gratis_ongkir=False)
  assert dekat == 20000
  assert jauh > dekat


def test_layanan_down_memakai_tarif_darurat():
  """Kegagalan layanan luar tidak boleh membatalkan pesanan."""
  ongkir = layanan_kirim.hitung_ongkir(KlienGagal(), KODE_POS_JAKARTA,
                                       BERAT_GRAM, gratis_ongkir=False)
  assert ongkir == layanan_kirim.TARIF_DARURAT_RUPIAH


def test_mock_membuktikan_layanan_tidak_dipanggil():
  """Pesanan bebas ongkir tidak boleh memanggil layanan luar sama sekali.

  Sifat ini hanya dapat dibuktikan dengan mock, karena yang diperiksa bukan
  hasil hitungannya, melainkan ada atau tidaknya panggilan.
  """
  mock_klien = Mock()
  ongkir = layanan_kirim.hitung_ongkir(mock_klien, KODE_POS_JAKARTA,
                                       BERAT_GRAM, gratis_ongkir=True)
  assert ongkir == 0
  mock_klien.minta_biaya.assert_not_called()


def test_mock_memeriksa_argumen_panggilan():
  """Kode pos dan berat harus diteruskan apa adanya ke layanan luar."""
  mock_klien = Mock()
  mock_klien.minta_biaya.return_value = TARIF_STUB_RUPIAH
  layanan_kirim.hitung_ongkir(mock_klien, KODE_POS_LUAR_JAWA, BERAT_GRAM,
                              gratis_ongkir=False)
  mock_klien.minta_biaya.assert_called_once_with(KODE_POS_LUAR_JAWA,
                                                 BERAT_GRAM)
