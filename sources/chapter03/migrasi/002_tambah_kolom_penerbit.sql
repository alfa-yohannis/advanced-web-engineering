-- Migrasi 002: menambah kolom penerbit dengan pola expand.
--
-- Kolom ditambahkan dalam keadaan boleh kosong, tanpa NOT NULL. Versi
-- aplikasi yang lama tetap berjalan karena tidak mengenal kolom ini, dan
-- versi baru sudah dapat menulisinya. Pengisian data lama dan pengetatan
-- batasannya dikerjakan pada migrasi terpisah, setelah seluruh instans
-- aplikasi memakai versi baru.
--
-- ADD COLUMN dengan nilai bawaan tidak lagi menulis ulang seluruh tabel
-- sejak PostgreSQL 11, sehingga kuncinya hanya sesaat.

BEGIN;

ALTER TABLE buku ADD COLUMN penerbit text;

COMMIT;
