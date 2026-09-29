"""Aturan harga pesanan, ditulis sebagai fungsi murni agar mudah diuji.

File ini tidak menyentuh basis data maupun jaringan, sehingga pengujiannya
selesai dalam milidetik dan tidak membutuhkan container. Inilah lapisan yang
pantas diuji dengan unit test bervolume besar.

Seluruh nilai uang memakai bilangan bulat rupiah, bukan pecahan, agar hasil
penjumlahannya tidak bergantung pada pembulatan floating point.

Pemakaian (dari sources/chapter06):
    source ../.venv/bin/activate
    python -c "import harga; print(harga.hitung_total(10, 50000))"
"""

# Pesanan sebanyak batas ini atau lebih dihitung sebagai pembelian grosir.
BATAS_UNIT_GROSIR = 10
PERSEN_DISKON_GROSIR = 10
BIAYA_KIRIM_RUPIAH = 15000
# Belanja di atas batas ini bebas biaya kirim.
BATAS_GRATIS_KIRIM_RUPIAH = 300000


def hitung_subtotal(jumlah_unit, harga_satuan_rupiah):
  """Menghitung harga sebelum diskon dan sebelum biaya kirim.

  Pesanan dengan jumlah unit nol atau negatif ditolak, karena keadaan itu
  menandakan kesalahan di pemanggilnya, bukan pesanan yang sah.
  """
  if jumlah_unit <= 0:
    raise ValueError("jumlah unit harus lebih besar dari nol")
  if harga_satuan_rupiah < 0:
    raise ValueError("harga satuan tidak boleh negatif")
  return jumlah_unit * harga_satuan_rupiah


def hitung_diskon(jumlah_unit, subtotal_rupiah):
  """Menghitung potongan grosir, yaitu potongan untuk pembelian banyak.

  Batasnya inklusif: pesanan tepat sebanyak BATAS_UNIT_GROSIR sudah berhak
  atas potongan. Baris inilah yang paling sering salah ditulis, dan paling
  sering lolos dari unit test yang hanya menguji angka di tengah rentang.
  """
  if jumlah_unit >= BATAS_UNIT_GROSIR:
    return subtotal_rupiah * PERSEN_DISKON_GROSIR // 100
  return 0


def hitung_biaya_kirim(nilai_belanja_rupiah):
  """Menghitung biaya kirim dari nilai belanja sesudah potongan.

  Biaya kirim dihitung sesudah potongan, sehingga potongan dapat menjatuhkan
  pesanan ke bawah batas gratis ongkir. Urutan ini disengaja dan diuji.
  """
  if nilai_belanja_rupiah >= BATAS_GRATIS_KIRIM_RUPIAH:
    return 0
  return BIAYA_KIRIM_RUPIAH


def hitung_total(jumlah_unit, harga_satuan_rupiah):
  """Menghitung total akhir yang dibayar pembeli, lengkap dengan biaya kirim.

  Mengembalikan satu bilangan bulat rupiah, sehingga hasilnya dapat
  dibandingkan persis di dalam pengujian tanpa toleransi pecahan.
  """
  subtotal = hitung_subtotal(jumlah_unit, harga_satuan_rupiah)
  diskon = hitung_diskon(jumlah_unit, subtotal)
  nilai_belanja = subtotal - diskon
  return nilai_belanja + hitung_biaya_kirim(nilai_belanja)
