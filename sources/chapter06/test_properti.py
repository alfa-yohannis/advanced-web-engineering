"""Property-based test aturan harga memakai Hypothesis.

Unit test biasa menyebutkan contoh satu per satu. Property-based test
menyebutkan sifat yang harus selalu benar, lalu pustakanya yang mencari
angka pembantahnya. Ketika ada yang gagal, Hypothesis menyusutkan angkanya
sampai menjadi contoh terkecil yang masih gagal.

Pemakaian (dari sources/chapter06):
    source ../.venv/bin/activate
    pytest test_properti.py
"""

from hypothesis import given, strategies

import harga

# Rentang sengaja dibatasi agar angkanya tetap masuk akal sebagai harga buku.
UNIT = strategies.integers(min_value=1, max_value=1000)
HARGA_SATUAN = strategies.integers(min_value=0, max_value=10_000_000)


@given(jumlah_unit=UNIT, harga_satuan=HARGA_SATUAN)
def test_total_tidak_pernah_negatif(jumlah_unit, harga_satuan):
  """Berapa pun masukannya, pembeli tidak pernah menerima uang kembali."""
  assert harga.hitung_total(jumlah_unit, harga_satuan) >= 0


@given(jumlah_unit=UNIT, harga_satuan=HARGA_SATUAN)
def test_diskon_tidak_melebihi_subtotal(jumlah_unit, harga_satuan):
  """Potongan selalu lebih kecil daripada belanjanya, sehingga tidak gratis."""
  subtotal = harga.hitung_subtotal(jumlah_unit, harga_satuan)
  assert 0 <= harga.hitung_diskon(jumlah_unit, subtotal) <= subtotal


@given(harga_satuan=strategies.integers(min_value=1, max_value=100_000))
def test_menambah_unit_tidak_menurunkan_subtotal(harga_satuan):
  """Menambah satu unit tidak pernah membuat subtotal menjadi lebih kecil."""
  for jumlah_unit in range(1, 20):
    sekarang = harga.hitung_subtotal(jumlah_unit, harga_satuan)
    berikutnya = harga.hitung_subtotal(jumlah_unit + 1, harga_satuan)
    assert berikutnya >= sekarang


@given(jumlah_unit=strategies.integers(min_value=harga.BATAS_UNIT_GROSIR,
                                       max_value=1000),
       harga_satuan=strategies.integers(min_value=1, max_value=1_000_000))
def test_pesanan_grosir_selalu_mendapat_potongan(jumlah_unit, harga_satuan):
  """Seluruh pesanan sebanyak batas grosir atau lebih mendapat potongan.

  Sifat inilah yang paling dekat dengan cacat batas: bila tanda bandingnya
  diubah menjadi >, contoh tepat di batas langsung ditemukan Hypothesis.
  """
  subtotal = harga.hitung_subtotal(jumlah_unit, harga_satuan)
  if subtotal >= 100:
    assert harga.hitung_diskon(jumlah_unit, subtotal) > 0
