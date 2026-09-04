-- Migrasi 001: skema awal.
-- Berkas migrasi tidak pernah diubah setelah dijalankan di lingkungan mana
-- pun. Perubahan berikutnya ditulis sebagai berkas baru bernomor lebih besar.

BEGIN;

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
  versi       integer NOT NULL DEFAULT 1,
  dibuat_pada timestamptz NOT NULL DEFAULT now()
);

COMMIT;
