# Sumber Bab 01

Bekal pertemuan pertama: satu *smoke test* yang memeriksa lingkungan kerja
untuk keempat belas bab, satu percobaan Git tentang umur cabang dan konflik,
serta kerangka API minimal berpola *route*, *service*, dan *repository*
beserta CI-nya. Seluruhnya Python pustaka standar, tanpa Docker dan tanpa
npm.

| File | Kegunaan |
| --- | --- |
| `periksa-lingkungan.py` | *Smoke test* lingkungan: versi Python, Node.js, npm, Git, Docker, Compose, Chrome, psycopg di venv, dan port seluruh bab |
| `simulasi-cabang.py` | Mengukur jumlah blok konflik ketika dua cabang digabung sesudah 1, 3, 7, dan 14 hari, di repositori Git sementara |
| `repositori.py` | Lapisan *repository*: penyimpanan buku di memori dan di SQLite dengan antarmuka yang sama |
| `layanan.py` | Lapisan *service*: aturan buku yang sah, tanpa HTTP dan tanpa SQL |
| `rute.py` | Lapisan *route*: menerjemahkan HTTP menjadi panggilan *service*, dan kesalahannya menjadi 400 atau 404 |
| `aplikasi.py` | Menyusun ketiga lapisan menjadi API di port 8050 |
| `test_layanan.py` | Uji unit *service* dengan *repository* memori |
| `test_api.py` | Uji API lewat HTTP sungguhan, pada port yang dipilih sistem operasi |
| `ci-lokal.py` | Menjalankan langkah CI di komputer sendiri: sintaks, uji unit, lalu uji API |
| `ci.yml` | Kerangka *workflow* GitHub Actions dengan langkah yang sama, bahan bacaan dan bukan *pipeline* yang aktif |

## Menjalankan

```bash
cd sources/chapter01
python3 periksa-lingkungan.py
python3 simulasi-cabang.py
python3 ci-lokal.py

python3 aplikasi.py &
curl -s -X POST http://127.0.0.1:8050/buku \
  -H 'Content-Type: application/json' \
  -d '{"judul": "Basis Data Terapan", "harga": 85000, "stok": 4}'
curl -s http://127.0.0.1:8050/buku
```

`periksa-lingkungan.py` keluar dengan status 1 bila ada pemeriksaan yang
gagal. Port yang dilaporkan terpakai harus dikosongkan lebih dahulu, karena
bab yang memakainya tidak dapat dinyalakan.

Untuk mengaktifkan CI di repositori tim, salin `ci.yml` ke
`.github/workflows/ci.yml`, lalu sesuaikan `paths` dengan letak kode tim di
monorepo.

## Catatan etika

Seluruh skrip di direktori ini hanya menyentuh komputer sendiri.
`periksa-lingkungan.py` mencoba memesan tiap port sebentar lalu melepasnya,
tanpa mengirim data ke mana pun. `simulasi-cabang.py` bekerja di direktori
sementara dan tidak memakai pengaturan Git milik pengguna.
