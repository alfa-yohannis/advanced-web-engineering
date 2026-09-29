"""Unit test aturan harga, yaitu lapisan tercepat pada piramida pengujian.

Seluruh pengujian di file ini berjalan tanpa basis data, tanpa jaringan, dan
tanpa container, sehingga dapat dijalankan ratusan kali sehari.

Satu pengujian sengaja diberi nama mengandung batas_grosir, agar pada latihan
dapat dikeluarkan dengan pytest -k "not batas_grosir". Tanpa pengujian itu
coverage tetap 100 persen, padahal cacat batas tidak lagi tertangkap.

Pemakaian (dari sources/chapter06):
    source ../.venv/bin/activate
    pytest test_harga.py
"""

import pytest

import harga


def test_subtotal_mengalikan_jumlah_dengan_harga():
  """Subtotal adalah perkalian biasa, dan itulah dasar seluruh hitungan lain."""
  assert harga.hitung_subtotal(3, 50000) == 150000


def test_subtotal_menolak_jumlah_nol():
  """Jumlah nol menandakan kesalahan pemanggil, sehingga ditolak sejak awal."""
  with pytest.raises(ValueError):
    harga.hitung_subtotal(0, 50000)


def test_subtotal_menolak_harga_negatif():
  """Harga negatif tidak pernah sah, dan ditolak sebelum masuk hitungan."""
  with pytest.raises(ValueError):
    harga.hitung_subtotal(1, -1)


def test_diskon_tidak_berlaku_di_bawah_ambang():
  """Pembelian sedikit tidak mendapat potongan grosir."""
  assert harga.hitung_diskon(3, 150000) == 0


def test_diskon_berlaku_di_atas_ambang():
  """Pembelian jauh di atas ambang mendapat potongan sepuluh persen."""
  assert harga.hitung_diskon(12, 600000) == 60000


def test_diskon_berlaku_tepat_pada_batas_grosir():
  """Pesanan tepat sebanyak sepuluh unit sudah berhak atas potongan.

  Inilah pengujian yang membedakan >= dari >, dan satu-satunya yang gagal
  bila tanda bandingnya diubah.
  """
  assert harga.hitung_diskon(harga.BATAS_UNIT_GROSIR, 500000) == 50000


def test_ongkir_gratis_untuk_belanja_besar():
  """Belanja di atas ambang gratis ongkir tidak dikenai biaya kirim."""
  assert harga.hitung_biaya_kirim(300000) == 0


def test_ongkir_dikenakan_untuk_belanja_kecil():
  """Belanja di bawah ambang tetap membayar biaya kirim penuh."""
  assert harga.hitung_biaya_kirim(299999) == harga.BIAYA_KIRIM_RUPIAH


def test_diskon_dapat_menjatuhkan_pesanan_ke_bawah_gratis_ongkir():
  """Potongan dihitung lebih dahulu, sehingga dapat membatalkan gratis ongkir.

  Subtotal 11 x 30.000 bernilai 330.000 dan tampak bebas ongkir. Sesudah
  potongan sepuluh persen, nilainya 297.000 dan ongkir kembali dikenakan.
  """
  assert harga.hitung_total(11, 30000) == 297000 + harga.BIAYA_KIRIM_RUPIAH


def test_total_menggabungkan_diskon_dan_ongkir():
  """Total akhir untuk pembelian kecil memuat ongkir dan tanpa potongan."""
  assert harga.hitung_total(2, 40000) == 80000 + harga.BIAYA_KIRIM_RUPIAH
