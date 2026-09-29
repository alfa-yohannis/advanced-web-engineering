"""Klien layanan biaya kirim milik pihak lain, beserta aturan yang memakainya.

File ini menjadi bahan peragaan test double. Fungsi hitung_ongkir memanggil
layanan luar lewat sebuah klien, dan klien itulah yang diganti oleh stub,
fake, atau mock saat pengujian, sehingga pengujian tidak menyentuh jaringan.

Pemakaian (dari sources/chapter06):
    source ../.venv/bin/activate
    python -c "import layanan_kirim; print(layanan_kirim.TARIF_DARURAT_RUPIAH)"
"""

import json
from http.client import HTTPConnection

HOST_LAYANAN_BAWAAN = "127.0.0.1"
PORT_LAYANAN_BAWAAN = 8030
BATAS_WAKTU_DETIK = 2
# Dipakai ketika layanan luar tidak menjawab, agar pesanan tetap dapat
# diselesaikan. Angkanya sengaja lebih mahal daripada tarif normal.
TARIF_DARURAT_RUPIAH = 25000


class KlienBiayaKirim:
  """Memanggil layanan biaya kirim lewat HTTP.

  Kelas ini satu-satunya bagian yang menyentuh jaringan. Karena dipisahkan,
  aturan bisnis di sekitarnya dapat diuji tanpa layanan itu menyala.
  """

  def __init__(self, host=HOST_LAYANAN_BAWAAN, port=PORT_LAYANAN_BAWAAN):
    """Menyimpan alamat layanan, tanpa membuka koneksi lebih dahulu.

    Koneksi dibuka saat dipakai, sehingga membuat klien tidak pernah gagal
    hanya karena layanannya sedang mati.
    """
    self.host = host
    self.port = port

  def minta_biaya(self, kode_pos, berat_gram):
    """Meminta tarif kirim ke layanan luar, lalu mengembalikannya dalam rupiah.

    Melempar OSError bila layanan tidak dapat dihubungi. Pemanggilnya yang
    memutuskan apa yang dilakukan terhadap kegagalan itu.
    """
    koneksi = HTTPConnection(self.host, self.port, timeout=BATAS_WAKTU_DETIK)
    jalur = f"/tarif?kode_pos={kode_pos}&berat_gram={berat_gram}"
    koneksi.request("GET", jalur)
    jawaban = koneksi.getresponse()
    isi = json.loads(jawaban.read())
    koneksi.close()
    return int(isi["tarif_rupiah"])


def hitung_ongkir(klien, kode_pos, berat_gram, gratis_ongkir):
  """Menentukan ongkir satu pesanan, dengan layanan luar sebagai sumber tarif.

  Ada tiga jalan yang harus diuji. Pesanan yang sudah bebas ongkir tidak
  memanggil layanan sama sekali. Panggilan yang berhasil memakai tarif dari
  layanan. Panggilan yang gagal memakai tarif darurat, sehingga pesanan tetap
  dapat diselesaikan ketika layanan sedang down.
  """
  if gratis_ongkir:
    return 0
  try:
    return klien.minta_biaya(kode_pos, berat_gram)
  except OSError:
    return TARIF_DARURAT_RUPIAH
