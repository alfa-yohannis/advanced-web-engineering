-- Empat query yang dipakai sepanjang Bab 3.
-- Dijalankan sebelum indeks tambahan dipasang, sehingga rencana yang
-- terekam di sini menjadi baseline.
--
-- Jalankan dengan:
--   psql "postgresql://admin:admin123@localhost:5433/toko" -f 03-query-baseline.sql

\echo '=== Q1: sepuluh pesanan terakhir milik satu pelanggan ==='
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status, total, dibuat_pada
FROM pesanan
WHERE pelanggan_id = 12345
ORDER BY dibuat_pada DESC
LIMIT 10;

\echo '=== Q2: sepuluh buku terlaris dalam 30 hari terakhir ==='
EXPLAIN (ANALYZE, BUFFERS)
SELECT b.judul, sum(i.jumlah) AS terjual
FROM item_pesanan i
JOIN pesanan p ON p.id = i.pesanan_id
JOIN buku b ON b.id = i.buku_id
WHERE p.dibuat_pada >= now() - interval '30 days'
  AND p.status <> 'batal'
GROUP BY b.id, b.judul
ORDER BY terjual DESC
LIMIT 10;

\echo '=== Q3: pencarian judul dengan pola di tengah ==='
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, judul
FROM buku
WHERE judul ILIKE '%Jilid 4321%'
LIMIT 20;

\echo '=== Q4: penyaringan yang mengembalikan seperempat tabel ==='
EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*)
FROM pesanan
WHERE status = 'baru';
