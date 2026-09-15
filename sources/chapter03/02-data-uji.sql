-- Data uji berukuran cukup besar agar selisih rencana eksekusi terlihat.
-- Jalankan dengan:
--   psql "postgresql://admin:admin123@localhost:5433/toko" -f 02-data-uji.sql
--
-- Ukurannya: 20 kategori, 50.000 buku, 20.000 pelanggan, 200.000 pesanan,
-- dan 600.000 item pesanan. Pengisian memakan sekitar lima belas detik.

SELECT setseed(0.42);

INSERT INTO kategori (nama)
SELECT 'Kategori ' || g
FROM generate_series(1, 20) g;

INSERT INTO buku (kategori_id, judul, isbn, harga, stok)
SELECT 1 + (g % 20),
       'Buku Pengantar Jilid ' || g,
       lpad(g::text, 13, '0'),
       (10000 + (g % 50) * 5000)::numeric,
       10 + (g % 100)
FROM generate_series(1, 50000) g;

INSERT INTO pelanggan (email, nama)
SELECT 'pengguna' || g || '@kampus.ac.id', 'Pengguna ' || g
FROM generate_series(1, 20000) g;

-- Tanggal disebar ke belakang sampai satu tahun, agar penyaringan
-- "30 hari terakhir" benar-benar menyaring.
INSERT INTO pesanan (pelanggan_id, status, total, dibuat_pada)
SELECT 1 + (random() * 19999)::int,
       (ARRAY['baru', 'dibayar', 'dikirim', 'batal'])[1 + (random() * 3)::int]::status_pesanan,
       0,
       now() - (random() * 365) * interval '1 day'
FROM generate_series(1, 200000);

-- Tiga item per pesanan. Rumus modulo dipakai agar pasangan
-- (pesanan_id, buku_id) tidak pernah kembar, sehingga kunci primer aman.
INSERT INTO item_pesanan (pesanan_id, buku_id, jumlah, harga_satuan)
SELECT p.id, b.id, 1 + (s % 3), b.harga
FROM pesanan p
CROSS JOIN generate_series(1, 3) AS s
JOIN buku b ON b.id = 1 + ((p.id * 7 + s) % 50000);

UPDATE pesanan p
SET total = t.nilai
FROM (
  SELECT pesanan_id, sum(jumlah * harga_satuan) AS nilai
  FROM item_pesanan
  GROUP BY pesanan_id
) t
WHERE t.pesanan_id = p.id;

-- Statistik wajib disegarkan. Tanpa ini perencana masih memakai
-- perkiraan lama, dan rencana eksekusinya menyesatkan.
ANALYZE;

SELECT 'kategori' AS tabel, count(*) FROM kategori
UNION ALL SELECT 'buku', count(*) FROM buku
UNION ALL SELECT 'pelanggan', count(*) FROM pelanggan
UNION ALL SELECT 'pesanan', count(*) FROM pesanan
UNION ALL SELECT 'item_pesanan', count(*) FROM item_pesanan;
