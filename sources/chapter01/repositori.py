"""Lapisan repository katalog: satu-satunya tempat yang tahu cara menyimpan buku.

Dua implementasi disediakan dengan antarmuka yang sama: satu di memori untuk
uji unit, satu di SQLite untuk aplikasi yang berjalan. Lapisan service hanya
memanggil simpan, ambil, dan semua, sehingga penyimpanannya dapat diganti
tanpa menyentuh aturan bisnis maupun route. Bab 3 mengganti SQLite dengan
PostgreSQL lewat cara yang sama.

Modul ini diimpor, bukan dijalankan langsung:
    python3 aplikasi.py
"""

import sqlite3
import threading

QUERY_BUAT_TABEL = """
CREATE TABLE IF NOT EXISTS buku (
  nomor INTEGER PRIMARY KEY AUTOINCREMENT,
  judul TEXT NOT NULL,
  harga INTEGER NOT NULL,
  stok INTEGER NOT NULL
)
"""
QUERY_SIMPAN = "INSERT INTO buku (judul, harga, stok) VALUES (?, ?, ?)"
QUERY_AMBIL = "SELECT nomor, judul, harga, stok FROM buku WHERE nomor = ?"
QUERY_SEMUA = "SELECT nomor, judul, harga, stok FROM buku ORDER BY nomor"


class RepositoriBukuMemori:
  """Menyimpan buku di dalam kamus, dipakai uji unit yang harus cepat."""

  def __init__(self):
    """Memulai dengan katalog kosong, dan nomor buku pertama 1."""
    self.daftar_buku = {}
    self.nomor_berikutnya = 1

  def simpan(self, judul, harga, stok):
    """Menyimpan satu buku baru, lalu mengembalikannya beserta nomornya."""
    buku = {"nomor": self.nomor_berikutnya, "judul": judul, "harga": harga,
            "stok": stok}
    self.daftar_buku[buku["nomor"]] = buku
    self.nomor_berikutnya += 1
    return dict(buku)

  def ambil(self, nomor):
    """Mengambil satu buku menurut nomornya, atau None bila tidak ada."""
    buku = self.daftar_buku.get(nomor)
    return dict(buku) if buku else None

  def semua(self):
    """Mengambil seluruh buku, terurut menurut nomornya."""
    return [dict(self.daftar_buku[nomor]) for nomor in sorted(self.daftar_buku)]


class RepositoriBukuSqlite:
  """Menyimpan buku di SQLite, dipakai aplikasi yang berjalan."""

  def __init__(self, jalur_basis_data=":memory:"):
    """Membuka basis data, lalu memastikan tabelnya ada.

    Satu koneksi dipakai bersama seluruh utas server, sehingga tiap aksesnya
    dijaga satu kunci. Tanpa kunci itu, dua permintaan yang datang bersamaan
    dapat memakai koneksi yang sama di tengah jalan.
    """
    self.koneksi = sqlite3.connect(jalur_basis_data, check_same_thread=False)
    self.kunci = threading.Lock()
    with self.kunci:
      self.koneksi.execute(QUERY_BUAT_TABEL)
      self.koneksi.commit()

  def simpan(self, judul, harga, stok):
    """Menyimpan satu buku baru, lalu mengembalikannya beserta nomornya."""
    with self.kunci:
      kursor = self.koneksi.execute(QUERY_SIMPAN, (judul, harga, stok))
      self.koneksi.commit()
    return {"nomor": kursor.lastrowid, "judul": judul, "harga": harga,
            "stok": stok}

  def ambil(self, nomor):
    """Mengambil satu buku menurut nomornya, atau None bila tidak ada."""
    with self.kunci:
      baris = self.koneksi.execute(QUERY_AMBIL, (nomor,)).fetchone()
    return ubah_ke_kamus(baris) if baris else None

  def semua(self):
    """Mengambil seluruh buku, terurut menurut nomornya."""
    with self.kunci:
      daftar_baris = self.koneksi.execute(QUERY_SEMUA).fetchall()
    return [ubah_ke_kamus(baris) for baris in daftar_baris]


def ubah_ke_kamus(baris):
  """Mengubah satu baris hasil query menjadi kamus yang sama bentuknya."""
  nomor, judul, harga, stok = baris
  return {"nomor": nomor, "judul": judul, "harga": harga, "stok": stok}
