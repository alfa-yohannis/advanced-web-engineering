# Sumber Bab 3: Data Engineering untuk Aplikasi Web

| Berkas | Kegunaan |
| --- | --- |
| `docker-compose.yml` | PostgreSQL 16 untuk seluruh latihan, dibatasi `max_connections=25` |
| `01-skema.sql` | Skema toko buku kampus, sengaja tanpa indeks tambahan |
| `02-data-uji.sql` | Mengisi 20 kategori, 50.000 buku, 20.000 pelanggan, 200.000 pesanan, 600.000 item |
| `03-query-baseline.sql` | Empat kueri acuan beserta `EXPLAIN (ANALYZE, BUFFERS)` |
| `04-indeks.sql` | Indeks perbaikan: gabungan, parsial, kunci asing, dan trigram |
| `kueri/q1.sql` sampai `q4.sql` | Keempat kueri acuan sebagai berkas terpisah, dipakai `ukur-query.py` |
| `tiga-lapis-akses.py` | Menulis satu kebutuhan yang sama sebagai ORM, query builder, dan SQL langsung |
| `ukur-query.py` | Menjalankan satu kueri berulang kali, melaporkan p50, p95, dan simpul pemindaiannya |
| `n-plus-1.py` | Membandingkan pola N+1 dengan kueri yang jumlahnya tetap |
| `transaksi-konkuren.py` | Memperagakan lost update dan tiga cara mencegahnya |
| `kolam-koneksi.py` | Mengukur biaya membuka koneksi dan manfaat kolam koneksi |
| `migrasi/001_skema_awal.sql` | Migrasi pertama, dijalankan di dalam satu transaksi |
| `migrasi/002_tambah_kolom_penerbit.sql` | Penambahan kolom dengan pola *expand*, aman bagi versi lama |
| `migrasi/003_indeks_pesanan.sql` | `CREATE INDEX CONCURRENTLY`, tanpa blok transaksi |

## Menyiapkan lingkungan

```bash
cd sources/chapter03
docker compose up -d
docker compose exec -T db psql "postgresql://awe:awe@localhost/toko" < 01-skema.sql
docker compose exec -T db psql "postgresql://awe:awe@localhost/toko" < 02-data-uji.sql
```

Pengisian data memakan sekitar dua belas detik. Basis data dapat dihubungi dari
luar container pada port 5433.

## Menjalankan skrip Python

Skrip memakai venv bersama di `sources/.venv`. Bila belum ada, buat sekali saja:

```bash
cd sources
python3 -m venv .venv
.venv/bin/pip install "psycopg[binary,pool]" sqlalchemy
```

Selanjutnya, dari direktori bab ini:

```bash
source ../.venv/bin/activate
python n-plus-1.py 25
python transaksi-konkuren.py 8 50
python kolam-koneksi.py 10 50
python ukur-query.py kueri/q1.sql 20
python tiga-lapis-akses.py
```

## Membersihkan

```bash
docker compose down -v
```

Opsi `-v` ikut menghapus volume datanya, sehingga penyiapan berikutnya dimulai
dari keadaan bersih.
