# Sumber Bab 07

Aplikasi toko buku yang sudah dikeraskan, beserta skrip yang memeriksanya.
Basis datanya berjalan di port 5437 dan aplikasinya di port 8030, sehingga
tidak berebut port dengan bab lain.

| File | Kegunaan |
| --- | --- |
| `docker-compose.yml` | PostgreSQL 16 di port 5437, terpisah dari container bab lain |
| `siapkan-data.sh` | Mengisi basis data dengan skema, data uji, dan indeks milik Bab 3 |
| `aplikasi.py` | Aplikasi yang sudah dikeraskan: header keamanan, cookie terbatas, CORS berdaftar, *query* berparameter, dan *escaping* keluaran |
| `kebijakan.json` | Daftar syarat keamanan: header wajib, atribut cookie, dan origin yang boleh |
| `kebijakan-pembanding.json` | Kebijakan yang sama, diarahkan ke server statis bawaan Python sebagai pembanding |
| `periksa-keamanan.py` | Menilai aplikasi terhadap kebijakan, keluar dengan status 1 bila ada syarat yang belum terpenuhi |
| `audit-dependensi.sh` | Memeriksa paket Python dan Node terhadap basis data kerentanan yang diumumkan |
| `ruff.toml` | Pengaturan analisis statis, termasuk aturan keamanan dari bandit |
| `statis/index.html` | Halaman demo yang dipakai memeriksa header |

## Menyiapkan

```bash
cd sources/chapter07
docker compose up -d
./siapkan-data.sh
python3 -m venv ../.venv
../.venv/bin/pip install "psycopg[binary]" ruff pip-audit
```

## Menjalankan

```bash
source ../.venv/bin/activate
SECRET_SESI=rahasia-latihan python aplikasi.py &
python periksa-keamanan.py
./audit-dependensi.sh
ruff check .
```

Pembandingnya, yaitu server statis bawaan Python tanpa penyetelan apa pun:

```bash
cd statis && python -m http.server 8031 &
cd .. && python periksa-keamanan.py kebijakan-pembanding.json
```

## Catatan etika

Seluruh pemeriksaan di direktori ini bersifat mengamati, dan sasarannya hanya
aplikasi yang berjalan di komputer sendiri. `periksa-keamanan.py` mengambil
beberapa *response* biasa lalu membaca headernya, sedangkan
`audit-dependensi.sh` hanya mencocokkan daftar paket yang terpasang dengan
pengumuman kerentanan. Tidak ada satu pun skrip di sini yang boleh diarahkan
ke sistem milik orang lain, termasuk situs kampus.

Setelah selesai, hentikan container dengan `docker compose down -v`. Opsi
`-v` ikut menghapus volume datanya.
