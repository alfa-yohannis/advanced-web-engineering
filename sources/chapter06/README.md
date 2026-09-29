# Sumber Bab 06

Aplikasi pesanan beserta seluruh lapisan pengujiannya. Basis datanya berjalan
di port 5436 dan aplikasinya di port 8020, sehingga tidak berebut port dengan
bab lain.

| File | Kegunaan |
| --- | --- |
| `docker-compose.yml` | PostgreSQL 16 di port 5436, terpisah dari container Bab 3, 4, dan 5 |
| `siapkan-data.sh` | Mengisi basis data dengan skema, data uji, dan indeks milik Bab 3 |
| `harga.py` | Aturan harga sebagai fungsi murni, target unit test dan *property-based testing* |
| `basis_data.py` | Akses basis data lewat satu pintu, lengkap dengan penghitung *query* |
| `aplikasi.py` | Aplikasi yang diuji, melaporkan jumlah *query* lewat header `X-Query-Count` |
| `layanan_kirim.py` | Klien layanan biaya kirim milik pihak lain, bahan peragaan *test double* |
| `conftest.py` | *Fixture* bersama: koneksi yang di-*rollback*, id pesanan uji, dan aplikasi di utas terpisah |
| `test_harga.py` | Unit test aturan harga, termasuk pengujian batas grosir |
| `test_properti.py` | *Property-based testing* memakai Hypothesis |
| `test_double.py` | Peragaan dummy, stub, fake, dan mock |
| `test_integrasi.py` | Integration test terhadap basis data sungguhan, termasuk jumlah *query* |
| `test_kontrak.py` | Pengujian kontrak *response* terhadap JSON Schema |
| `kontrak/pesanan.schema.json` | Kontrak bentuk *response* alamat pesanan |
| `e2e/pesanan.spec.ts` | Pengujian E2E lewat Google Chrome memakai Playwright |
| `e2e/playwright.config.ts` | Konfigurasi Playwright, memakai channel `chrome` tanpa mengunduh browser |
| `statis/index.html`, `statis/pesanan.js` | Halaman demo yang diuji lapisan E2E |
| `mutu.json` | Batas mutu: waktu tiap lapisan, *coverage*, temuan analisis statis, dan jumlah *query* |
| `gate-mutu.py` | Menilai seluruh batas di `mutu.json`, keluar dengan status 1 bila ada yang dilanggar |
| `ruff.toml`, `package.json`, `tsconfig.json` | Konfigurasi analisis statis dan perkakas Node |

## Menyiapkan

```bash
cd sources/chapter06
docker compose up -d
./siapkan-data.sh
python3 -m venv ../.venv
../.venv/bin/pip install "psycopg[binary]" pytest hypothesis jsonschema \
  coverage ruff
npm install
```

Pengisian data memakan sekitar lima belas detik. Skrip `siapkan-data.sh`
membaca file SQL milik `sources/chapter03`, sehingga direktori tersebut harus
ada di sebelah direktori bab ini.

## Menjalankan

```bash
source ../.venv/bin/activate
pytest -q test_harga.py test_properti.py test_double.py
pytest -q test_integrasi.py test_kontrak.py
python aplikasi.py &
npx playwright test --config e2e/playwright.config.ts
python gate-mutu.py
```

## Catatan etika

Seluruh kegiatan pada bab ini hanya menyentuh basis data dan aplikasi milik
sendiri di komputer sendiri. Tidak ada satu pun skrip di direktori ini yang
boleh diarahkan ke sistem milik orang lain.

Setelah selesai, hentikan container dengan `docker compose down -v`. Opsi
`-v` ikut menghapus volume datanya.
