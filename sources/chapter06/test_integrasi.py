"""Pengujian integrasi lapisan akses data terhadap basis data sungguhan.

Unit test di test_harga.py membuktikan aturan harga benar tanpa menyentuh apa
pun di luar prosesnya. File ini menjawab pertanyaan yang tidak dapat dijawab
unit test: apakah SQL-nya sah, apakah tipe kolomnya cocok dengan kode, dan
berapa query yang sebenarnya dikirim satu permintaan.

Kedua jalur pengambilan pesanan memberi isi response yang sama persis. Yang
berbeda hanya jumlah querynya, dan hanya pengujian integrasi yang dapat
membuktikannya.

Basis datanya berjalan di container, dan tiap pengujian diakhiri rollback lewat
fixture koneksi di conftest.py.

Pemakaian (dari sources/chapter06, setelah docker compose up -d):
    source ../.venv/bin/activate
    pytest test_integrasi.py
"""

import basis_data

# Jumlah query jalur sehat tetap dua: satu untuk kepala pesanan, satu untuk
# seluruh itemnya sekaligus.
QUERY_JALUR_SEHAT = 2
# Id yang pasti tidak ada, karena tabelnya memakai id positif berurutan.
ID_PESANAN_TIDAK_ADA = -1
STATUS_PENGGANTI = "batal"
STATUS_CADANGAN = "baru"

SQL_BACA_STATUS = "SELECT status FROM pesanan WHERE id = %s"
SQL_UBAH_STATUS = """
    UPDATE pesanan SET status = %s WHERE id = %s RETURNING status
"""


def pilih_status_lain(status_sekarang):
  """Memilih status yang berbeda dari status sekarang.

  Tanpa pemilihan ini, pengujian isolasi dapat lolos tanpa mengubah apa pun,
  yaitu ketika status data uji kebetulan sudah sama dengan status penggantinya.
  """
  if status_sekarang == STATUS_PENGGANTI:
    return STATUS_CADANGAN
  return STATUS_PENGGANTI


def test_isi_response_kedua_jalur_sama_persis(koneksi, id_pesanan_uji):
  """Kedua jalur memberi kamus yang sama, sampai ke urutan itemnya.

  Pengujian inilah yang lolos walaupun jalur N+1 dipakai di produksi. Karena
  itu membandingkan isi response saja tidak cukup untuk menjaga mutu.
  """
  penghitung_sehat = basis_data.PenghitungQuery()
  penghitung_n1 = basis_data.PenghitungQuery()
  pesanan_sehat = basis_data.ambil_pesanan(koneksi, id_pesanan_uji,
                                           penghitung_sehat)
  pesanan_n1 = basis_data.ambil_pesanan_n_plus_1(koneksi, id_pesanan_uji,
                                                 penghitung_n1)
  assert pesanan_sehat == pesanan_n1


def test_jalur_sehat_memakai_dua_query(koneksi, id_pesanan_uji):
  """Jumlah query jalur sehat tetap dua, berapa pun banyak itemnya."""
  penghitung = basis_data.PenghitungQuery()
  basis_data.ambil_pesanan(koneksi, id_pesanan_uji, penghitung)
  assert penghitung.jumlah == QUERY_JALUR_SEHAT


def test_jalur_n_plus_1_tumbuh_mengikuti_jumlah_item(koneksi, id_pesanan_uji):
  """Jumlah query jalur N+1 bertambah satu untuk tiap item pesanan.

  Angka harapannya dihitung dari data, bukan ditulis tetap, sehingga
  pengujian tetap benar ketika data uji dibangkitkan ulang.
  """
  penghitung = basis_data.PenghitungQuery()
  pesanan = basis_data.ambil_pesanan_n_plus_1(koneksi, id_pesanan_uji,
                                              penghitung)
  jumlah_item = len(pesanan["item"])
  assert penghitung.jumlah == QUERY_JALUR_SEHAT + jumlah_item


def test_jalur_n_plus_1_lebih_banyak_query_daripada_jalur_sehat(
    koneksi, id_pesanan_uji):
  """Selisih jumlah query kedua jalur selalu sebesar banyaknya item.

  Inilah bentuk pengujian yang dapat dipasang sebagai gate: bukan menghitung
  waktu, melainkan menghitung query, sehingga hasilnya sama di komputer mana
  pun.
  """
  penghitung_sehat = basis_data.PenghitungQuery()
  penghitung_n1 = basis_data.PenghitungQuery()
  pesanan = basis_data.ambil_pesanan(koneksi, id_pesanan_uji,
                                     penghitung_sehat)
  basis_data.ambil_pesanan_n_plus_1(koneksi, id_pesanan_uji, penghitung_n1)
  selisih = penghitung_n1.jumlah - penghitung_sehat.jumlah
  assert selisih == len(pesanan["item"])


def test_pesanan_tidak_ada_memberi_none(koneksi):
  """Id yang tidak ada dijawab None, dan hanya memakai satu query.

  Query kedua tidak pernah dijalankan, karena kepala pesanannya sudah kosong.
  """
  penghitung = basis_data.PenghitungQuery()
  hasil = basis_data.ambil_pesanan(koneksi, ID_PESANAN_TIDAK_ADA, penghitung)
  assert hasil is None
  assert penghitung.jumlah == 1


def test_harga_item_terbaca_sebagai_bilangan_bulat(koneksi, id_pesanan_uji):
  """Kolom numeric diubah menjadi int, agar hasilnya dapat di-serialize json.

  Cacat semacam ini tidak pernah tertangkap unit test, karena tipe numeric
  hanya muncul ketika basis datanya sungguhan.
  """
  penghitung = basis_data.PenghitungQuery()
  pesanan = basis_data.ambil_pesanan(koneksi, id_pesanan_uji, penghitung)
  assert isinstance(pesanan["total"], int)
  for item in pesanan["item"]:
    assert isinstance(item["harga_satuan"], int)


def test_tulisan_pengujian_tidak_terlihat_koneksi_lain(koneksi,
                                                       id_pesanan_uji):
  """Perubahan di dalam pengujian tertahan di transaksinya sendiri.

  Sifat inilah yang membuat urutan pengujian tidak menentukan hasilnya.
  Koneksi kedua dibuka sengaja, untuk membuktikan bahwa data uji di luar
  transaksi pengujian tidak berubah.
  """
  penghitung = basis_data.PenghitungQuery()
  status_awal = basis_data.jalankan_query(koneksi, SQL_BACA_STATUS,
                                          (id_pesanan_uji,), penghitung)[0][0]
  status_diminta = pilih_status_lain(status_awal)
  status_baru = basis_data.jalankan_query(koneksi, SQL_UBAH_STATUS,
                                          (status_diminta, id_pesanan_uji),
                                          penghitung)[0][0]
  assert status_baru == status_diminta
  with basis_data.buka_koneksi() as koneksi_pengamat:
    status_terlihat = basis_data.jalankan_query(koneksi_pengamat,
                                                SQL_BACA_STATUS,
                                                (id_pesanan_uji,),
                                                penghitung)[0][0]
  assert status_terlihat == status_awal
