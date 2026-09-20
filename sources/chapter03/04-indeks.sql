-- Indeks perbaikan untuk query pada 03-query-baseline.sql.
-- Dijalankan setelah rencana baseline direkam, lalu 03-query-baseline.sql
-- dijalankan ulang untuk membandingkan.
--
-- Jalankan dengan:
--   psql "postgresql://admin:admin123@localhost:5433/toko" -f 04-indeks.sql

-- Q1. Kolom penyaring lebih dahulu, kolom pengurut sesudahnya, arahnya
-- disamakan dengan ORDER BY agar pengurutan tidak perlu dikerjakan lagi.
CREATE INDEX IF NOT EXISTS idx_pesanan_pelanggan_waktu
  ON pesanan (pelanggan_id, dibuat_pada DESC);

-- Q2. Indeks parsial. Baris berstatus 'batal' tidak pernah ikut dihitung,
-- sehingga tidak perlu ikut disimpan di dalam indeks.
CREATE INDEX IF NOT EXISTS idx_pesanan_waktu_aktif
  ON pesanan (dibuat_pada)
  WHERE status <> 'batal';

-- Kunci asing tidak otomatis berindeks di PostgreSQL. Tanpa indeks ini,
-- penggabungan dari pesanan ke item_pesanan memindai seluruh tabel.
CREATE INDEX IF NOT EXISTS idx_item_pesanan_buku
  ON item_pesanan (buku_id);

-- Q3. Pola '%teks%' tidak dapat dilayani B-tree, karena B-tree hanya
-- berguna untuk awalan. Trigram memecah teks menjadi potongan tiga huruf.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_buku_judul_trgm
  ON buku USING gin (judul gin_trgm_ops);

-- Q4 sengaja tidak diberi indeks. Penyaringan yang mengembalikan
-- seperempat tabel tetap dilayani Seq Scan, dan itu memang pilihan
-- yang benar.

ANALYZE;

\echo '=== Ukuran tiap indeks ==='
SELECT indexrelname AS indeks,
       pg_size_pretty(pg_relation_size(indexrelid)) AS ukuran,
       idx_scan AS jumlah_pemakaian
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
