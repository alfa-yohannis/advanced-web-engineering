# Sumber Bab 5: Performance Engineering

| Berkas | Kegunaan |
| --- | --- |
| `docker-compose.yml` | PostgreSQL 16 di port 5435, terpisah dari container Bab 3 dan Bab 4 |
| `siapkan-data.sh` | Mengisi basis data dengan skema, data uji, dan indeks milik Bab 3 |
| `aplikasi.py` | Aplikasi katalog yang diukur: katalog berhalaman, katalog penuh, agregat, dan versi *streaming* |
| `beban.py` | *Load generator* dengan sejumlah *worker*, melaporkan p50, p95, p99, *throughput*, dan ukuran jawaban |
| `anggaran.json` | Anggaran performa: p95 dan ukuran tiap alamat, ditambah target Core Web Vitals |
| `gate-anggaran.py` | Menilai hasil pengukuran terhadap anggaran, keluar dengan status 1 bila terlampaui |
| `profil-endpoint.py` | Memprofil pekerjaan sisi server memakai `cProfile`, untuk menemukan bagian termahal |
| `web-vitals.ts` | Pengukur Core Web Vitals pada kunjungan nyata, hasilnya dikirim ke `/api/vitals` |
| `katalog.ts` | Pemuat katalog di browser, dipakai sebagai beban interaksi |
| `statis/index.html` | Halaman demo yang memuat kedua berkas di atas |

Skrip yang sengaja membebani, yaitu `beban.py` dan `gate-anggaran.py`, hanya
diarahkan ke aplikasi milik sendiri.

## Menyiapkan lingkungan

```bash
cd sources/chapter05
docker compose up -d
./siapkan-data.sh
```

Pengisian data memakan sekitar lima belas detik.

## Menyiapkan venv

Skrip memakai venv bersama di `sources/.venv`. Bila belum ada, buat sekali saja
dari direktori bab ini:

```bash
python3 -m venv ../.venv
../.venv/bin/pip install "psycopg[binary,pool]" sqlalchemy
```

## Mengompilasi berkas TypeScript

Halaman demo memuat hasil kompilasinya, bukan berkas `.ts`:

```bash
npx -p typescript tsc --target es2022 --module es2022 --strict \
  --lib es2022,dom --outDir statis web-vitals.ts katalog.ts
```

## Menjalankan

Dari direktori bab ini, setelah `source ../.venv/bin/activate`:

```bash
python aplikasi.py                                  # terminal pertama
python beban.py "/api/katalog?halaman=1&ukuran=20"  # terminal kedua
python beban.py /api/katalog-penuh
python beban.py /api/terlaris 8 25
python profil-endpoint.py katalog-penuh
python gate-anggaran.py
```

Core Web Vitals baru terisi setelah <http://localhost:8010/> dibuka di browser,
tombol katalognya ditekan, lalu tabnya ditutup atau dipindah. Laporannya
tersimpan di `vitals.jsonl`.

## Membersihkan

```bash
docker compose down -v
```

Opsi `-v` ikut menghapus volume datanya, sehingga penyiapan berikutnya dimulai
dari keadaan bersih.
