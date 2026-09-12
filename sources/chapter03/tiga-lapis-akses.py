#!/usr/bin/env python3
"""Menulis satu kebutuhan yang sama dalam tiga lapis abstraksi akses data.

Ketiganya menghasilkan baris yang sama. Yang berbeda adalah seberapa jauh
SQL yang benar-benar dikirim terlihat dari kodenya, dan seberapa banyak kode
yang harus ditulis sendiri.

  orm            objek dan relasi, SQL di-generate seluruhnya
  query builder  SQL disusun dari objek tabel dan kolom, masih terbaca sebagai SQL
  sql langsung   SQL ditulis apa adanya

Kebutuhannya: sepuluh pesanan terakhir milik satu pelanggan, beserta jumlah
item tiap pesanan.

Pemakaian:
    source ../.venv/bin/activate
    python tiga-lapis-akses.py
"""

from datetime import datetime
from decimal import Decimal

import psycopg
from sqlalchemy import (
    ForeignKey,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

DSN = "postgresql://admin:admin123@localhost:5433/toko"
URL_SQLALCHEMY = "postgresql+psycopg://admin:admin123@localhost:5433/toko"
ID_PELANGGAN = 12345
BATAS = 10

# Susunannya sengaja sama dengan lewat_orm dan lewat_query_builder, sehingga
# tiap klausa SQL dapat dicocokkan dengan metode di kedua fungsi itu.
SQL_LANGSUNG = """
    SELECT p.id, p.total, count(i.buku_id)
    FROM pesanan p
    JOIN item_pesanan i ON i.pesanan_id = p.id
    WHERE p.pelanggan_id = %s
    GROUP BY p.id
    ORDER BY p.dibuat_pada DESC
    LIMIT %s
"""


class Dasar(DeclarativeBase):
  """Kelas dasar bagi seluruh pemetaan tabel ke kelas Python."""


class Pesanan(Dasar):
  """Pemetaan tabel pesanan. Hanya kolom yang dipakai yang didaftarkan."""

  __tablename__ = "pesanan"

  id: Mapped[int] = mapped_column(primary_key=True)
  pelanggan_id: Mapped[int]
  total: Mapped[Decimal]
  dibuat_pada: Mapped[datetime]


class ItemPesanan(Dasar):
  """Pemetaan tabel item_pesanan, dipakai untuk menghitung jumlah item."""

  __tablename__ = "item_pesanan"

  pesanan_id: Mapped[int] = mapped_column(
      ForeignKey("pesanan.id"), primary_key=True
  )
  buku_id: Mapped[int] = mapped_column(primary_key=True)
  jumlah: Mapped[int]


def lewat_orm(mesin):
  """Menyusun kueri dari kelas hasil pemetaan, tanpa menulis SQL sama sekali.

  Paling ringkas, tetapi SQL yang benar-benar dikirim tidak terlihat dari
  kodenya. Itulah yang membuat masalah N+1 mudah lolos.
  """
  perintah = (
      select(Pesanan.id, Pesanan.total, func.count(ItemPesanan.buku_id))
      .join(ItemPesanan, ItemPesanan.pesanan_id == Pesanan.id)
      .where(Pesanan.pelanggan_id == ID_PELANGGAN)
      .group_by(Pesanan.id)
      .order_by(Pesanan.dibuat_pada.desc())
      .limit(BATAS)
  )
  with Session(mesin) as sesi:
    return [tuple(baris) for baris in sesi.execute(perintah).all()]


def lewat_query_builder(mesin):
  """Menyusun SQL dari objek tabel dan kolom, tanpa memetakan tabel ke kelas.

  Bentuknya masih terbaca sebagai SQL, sehingga kuerinya dapat diperkirakan
  dari kodenya, dan nama kolom yang salah ketahuan sebelum kueri dikirim.
  """
  pesanan = Pesanan.__table__
  item = ItemPesanan.__table__
  perintah = (
      select(pesanan.c.id, pesanan.c.total, func.count(item.c.buku_id))
      .select_from(pesanan.join(item, item.c.pesanan_id == pesanan.c.id))
      .where(pesanan.c.pelanggan_id == ID_PELANGGAN)
      .group_by(pesanan.c.id)
      .order_by(pesanan.c.dibuat_pada.desc())
      .limit(BATAS)
  )
  with mesin.connect() as koneksi:
    return [tuple(baris) for baris in koneksi.execute(perintah).all()]


def lewat_sql_langsung():
  """Mengirim SQL apa adanya lewat psycopg.

  Paling banyak kodenya, tetapi yang dijalankan basis data persis seperti
  yang tertulis. Dipakai untuk kueri laporan dan kueri yang perlu disetel.
  """
  with psycopg.connect(DSN) as koneksi:
    baris = koneksi.execute(SQL_LANGSUNG, (ID_PELANGGAN, BATAS)).fetchall()
  return [(b[0], float(b[1]), b[2]) for b in baris]


def rapikan(hasil):
  """Menyeragamkan tipe angka agar ketiga hasil dapat dibandingkan langsung."""
  return sorted((int(id_), round(float(total), 2), int(n)) for id_, total, n in hasil)


def main():
  """Menjalankan ketiga lapis, lalu membuktikan hasilnya sama."""
  mesin = create_engine(URL_SQLALCHEMY)
  hasil_orm = rapikan(lewat_orm(mesin))
  hasil_builder = rapikan(lewat_query_builder(mesin))
  hasil_sql = rapikan(lewat_sql_langsung())

  print(f"Pesanan terakhir pelanggan {ID_PELANGGAN}, {len(hasil_sql)} baris:")
  for id_pesanan, total, jumlah_item in hasil_sql:
    print(f"  pesanan {id_pesanan:>7}  total {total:>12,.2f}  {jumlah_item} item")

  print(f"\nORM sama dengan SQL langsung      : {hasil_orm == hasil_sql}")
  print(f"Query builder sama dengan SQL     : {hasil_builder == hasil_sql}")


if __name__ == "__main__":
  main()
