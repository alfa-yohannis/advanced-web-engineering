"""Lapisan akses basis data Bab 6, lengkap dengan penghitung query.

Seluruh query melewati satu fungsi, yaitu jalankan_query. Karena itu jumlah
query tiap permintaan dapat dihitung persis tanpa menambal pustaka apa pun,
dan angka itulah yang dinilai gate mutu sebagai pendeteksi masalah N+1.

Pemakaian (dari sources/chapter06, setelah docker compose up -d):
    source ../.venv/bin/activate
    python -c "import basis_data; print(basis_data.DSN)"
"""

import psycopg

DSN = "postgresql://admin:admin123@localhost:5436/toko"

SQL_PESANAN = """
    SELECT p.id, p.status, p.total, l.nama
    FROM pesanan p
    JOIN pelanggan l ON l.id = p.pelanggan_id
    WHERE p.id = %s
"""

SQL_ITEM_PESANAN = """
    SELECT b.id, b.judul, i.jumlah, i.harga_satuan
    FROM item_pesanan i
    JOIN buku b ON b.id = i.buku_id
    WHERE i.pesanan_id = %s
    ORDER BY b.id
"""

SQL_ITEM_TANPA_JUDUL = """
    SELECT buku_id, jumlah, harga_satuan
    FROM item_pesanan
    WHERE pesanan_id = %s
    ORDER BY buku_id
"""

SQL_JUDUL_BUKU = "SELECT judul FROM buku WHERE id = %s"


class PenghitungQuery:
  """Menghitung berapa query yang dijalankan satu permintaan.

  Penghitung dibuat baru untuk tiap permintaan dan dikirim sebagai argumen,
  bukan disimpan sebagai variabel global, sehingga hitungannya tidak tercampur
  antarpermintaan yang berjalan bersamaan.
  """

  def __init__(self):
    """Memulai hitungan dari nol, satu penghitung untuk satu permintaan."""
    self.jumlah = 0

  def catat(self):
    """Menambah hitungan setiap kali satu query dikirim ke basis data."""
    self.jumlah += 1


def buka_koneksi():
  """Membuka satu koneksi baru ke basis data Bab 6.

  Dipakai aplikasi dan pengujian integrasi. Pengujian menutupnya dengan
  rollback, sehingga data uji kembali seperti semula.
  """
  return psycopg.connect(DSN)


def jalankan_query(koneksi, sql, parameter, penghitung):
  """Menjalankan satu query, mencatatnya, lalu mengembalikan seluruh barisnya.

  Seluruh akses basis data melewati fungsi ini. Tanpa pintu tunggal seperti
  ini, jumlah query hanya dapat ditebak dari membaca kode.
  """
  penghitung.catat()
  return koneksi.execute(sql, parameter).fetchall()


def baris_item_menjadi_kamus(baris):
  """Mengubah satu baris item pesanan menjadi kamus yang siap di-serialize.

  Harga disimpan sebagai numeric di basis data, dan tipe itu tidak dikenal
  json, sehingga diubah menjadi bilangan bulat rupiah lebih dahulu.
  """
  id_buku, judul, jumlah, harga_satuan = baris
  return {
      "buku_id": id_buku,
      "judul": judul,
      "jumlah": jumlah,
      "harga_satuan": int(harga_satuan),
  }


def ambil_pesanan(koneksi, id_pesanan, penghitung):
  """Mengambil satu pesanan beserta itemnya dengan jumlah query tetap dua.

  Query pertama mengambil kepala pesanan, query kedua mengambil seluruh
  itemnya sekaligus. Jumlahnya tidak tumbuh mengikuti banyaknya item.
  """
  baris_pesanan = jalankan_query(koneksi, SQL_PESANAN, (id_pesanan,),
                                 penghitung)
  if not baris_pesanan:
    return None
  id_baris, status, total, nama_pelanggan = baris_pesanan[0]
  baris_item = jalankan_query(koneksi, SQL_ITEM_PESANAN, (id_pesanan,),
                              penghitung)
  return {
      "id": id_baris,
      "status": status,
      "total": int(total),
      "pelanggan": nama_pelanggan,
      "item": [baris_item_menjadi_kamus(baris) for baris in baris_item],
  }


def ambil_pesanan_n_plus_1(koneksi, id_pesanan, penghitung):
  """Mengambil pesanan yang sama dengan pola N+1, sebagai bahan pengujian.

  Judul tiap buku diambil lewat query tersendiri, sehingga jumlah querynya
  satu ditambah sebanyak itemnya. Hasilnya sama persis dengan ambil_pesanan,
  dan justru itulah masalahnya: pengujian yang hanya membandingkan isi
  response tidak akan menangkap cacat ini.
  """
  baris_pesanan = jalankan_query(koneksi, SQL_PESANAN, (id_pesanan,),
                                 penghitung)
  if not baris_pesanan:
    return None
  id_baris, status, total, nama_pelanggan = baris_pesanan[0]
  baris_item = jalankan_query(koneksi, SQL_ITEM_TANPA_JUDUL, (id_pesanan,),
                              penghitung)
  daftar_item = []
  for id_buku, jumlah, harga_satuan in baris_item:
    baris_judul = jalankan_query(koneksi, SQL_JUDUL_BUKU, (id_buku,),
                                 penghitung)
    daftar_item.append(baris_item_menjadi_kamus(
        (id_buku, baris_judul[0][0], jumlah, harga_satuan)))
  return {
      "id": id_baris,
      "status": status,
      "total": int(total),
      "pelanggan": nama_pelanggan,
      "item": daftar_item,
  }
