# Sumber Bab 4: Caching, Consistency, dan Resilience

| Berkas | Kegunaan |
| --- | --- |
| `docker-compose.yml` | PostgreSQL 16 di port 5434 dan Redis 7 di port 6380, Redis dibatasi 64 MB |
| `siapkan-data.sh` | Mengisi basis data dengan skema, data uji, dan indeks milik Bab 3 |
| `aplikasi.py` | Aplikasi toko kecil: header cache HTTP, ETag, dan cache-aside di Redis |
| `statis/index.html` | Halaman demo, dikirim dengan `Cache-Control: no-cache` |
| `statis/app.3f9a2c.js` | *Fingerprinted asset*, dikirim dengan `max-age` satu tahun |
| `ukur-ttfb.py` | Mengukur waktu sampai byte pertama, melaporkan p50, p95, dan jumlah HIT dan MISS |
| `stampede.py` | Memperagakan cache stampede dan dua cara meredamnya |
| `invalidasi.py` | Mengukur lama data *stale* pada empat cara memperbarui cache |
| `optimistic-update.ts` | Tombol suka yang diperbarui secara optimistis di browser |
| `layanan-lambat.py` | Layanan biaya kirim tiruan yang sebagian jawabannya ditahan 2 detik |
| `resilience.py` | Membandingkan tanpa batas waktu, batas waktu, *retry*, dan *circuit breaker* |
| `redis-macet.py` | Mengukur lama satu GET ke Redis yang macet, dengan dan tanpa *retry* bawaan redis-py |

Skrip yang sengaja membebani, yaitu `stampede.py`, `resilience.py`, dan
`ukur-ttfb.py`, hanya diarahkan ke container dan layanan milik sendiri.

## Menyiapkan lingkungan

```bash
cd sources/chapter04
docker compose up -d
./siapkan-data.sh
```

Pengisian data memakan sekitar lima belas detik. Skrip `siapkan-data.sh`
membaca berkas SQL milik `sources/chapter03`, sehingga direktori tersebut harus
ada di sebelah direktori bab ini.

## Menyiapkan venv

Skrip memakai venv bersama di `sources/.venv`. Bab ini menambahkan pustaka
`redis` pada daftar Bab 3:

```bash
cd sources
python3 -m venv .venv
.venv/bin/pip install "psycopg[binary,pool]" sqlalchemy redis
```

## Menjalankan

Dari direktori bab ini, setelah `source ../.venv/bin/activate`:

```bash
python aplikasi.py                  # terminal pertama, biarkan menyala
python ukur-ttfb.py http://localhost:8000/api/terlaris 50
python ukur-ttfb.py http://localhost:8000/api/terlaris-cache 50
python stampede.py
python invalidasi.py
python layanan-lambat.py            # terminal kedua, biarkan menyala
python resilience.py
docker compose pause cache
python redis-macet.py
docker compose unpause cache
```

Pemeriksaan tipe berkas TypeScript:

```bash
npx -p typescript tsc --noEmit --strict --lib es2022,dom optimistic-update.ts
```

## Membersihkan

```bash
docker compose down -v
```

Opsi `-v` ikut menghapus volume datanya, sehingga penyiapan berikutnya dimulai
dari keadaan bersih.
