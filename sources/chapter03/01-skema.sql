-- Skema toko buku kampus.
-- Jalankan dengan:
--   psql "postgresql://awe:awe@localhost:5433/toko" -f 01-skema.sql
--
-- Catatan sengaja: pada tahap ini tidak ada satu pun indeks tambahan.
-- Indeks baru ditambahkan pada 04-indeks.sql, setelah rencana eksekusi
-- sebelum perbaikan direkam.

DROP TABLE IF EXISTS item_pesanan, pesanan, buku, pelanggan, kategori CASCADE;
DROP TYPE IF EXISTS status_pesanan;

CREATE TABLE kategori (
  id   bigserial PRIMARY KEY,
  nama text NOT NULL UNIQUE
);

CREATE TABLE buku (
  id          bigserial PRIMARY KEY,
  kategori_id bigint NOT NULL REFERENCES kategori (id),
  judul       text NOT NULL,
  isbn        text NOT NULL UNIQUE,
  harga       numeric(12, 2) NOT NULL CHECK (harga >= 0),
  stok        integer NOT NULL DEFAULT 0 CHECK (stok >= 0),
  -- Dipakai untuk optimistic locking pada Latihan 4.
  versi       integer NOT NULL DEFAULT 1,
  dibuat_pada timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE pelanggan (
  id          bigserial PRIMARY KEY,
  email       text NOT NULL UNIQUE,
  nama        text NOT NULL,
  dibuat_pada timestamptz NOT NULL DEFAULT now()
);

CREATE TYPE status_pesanan AS ENUM ('baru', 'dibayar', 'dikirim', 'batal');

CREATE TABLE pesanan (
  id           bigserial PRIMARY KEY,
  pelanggan_id bigint NOT NULL REFERENCES pelanggan (id),
  status       status_pesanan NOT NULL DEFAULT 'baru',
  total        numeric(12, 2) NOT NULL DEFAULT 0,
  dibuat_pada  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE item_pesanan (
  pesanan_id   bigint NOT NULL REFERENCES pesanan (id) ON DELETE CASCADE,
  buku_id      bigint NOT NULL REFERENCES buku (id),
  jumlah       integer NOT NULL CHECK (jumlah > 0),
  harga_satuan numeric(12, 2) NOT NULL,
  PRIMARY KEY (pesanan_id, buku_id)
);
