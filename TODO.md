# Pekerjaan yang Belum Selesai

Catatan ini menandai keadaan repositori pada 29 September 2026, supaya
pekerjaan berikutnya tidak dimulai dari menebak-nebak.

## Bab 6: Testing, Reliability, dan Code Quality

File sumber di `sources/chapter06/` sudah ada dan `pyflakes` bersih, tetapi
naskah dan slidenya belum ditulis.

| Bagian | Keadaan |
| --- | --- |
| `sources/chapter06/*.py`, `e2e/`, `kontrak/`, `statis/` | Sudah ada |
| `sources/chapter06/README.md` | Masih teks placeholder, perlu tabel daftar file |
| Pengukuran nyata | Belum dijalankan dan belum dicatat |
| `module/chapter06.tex` | Masih kerangka berisi `% TODO` |
| `slides/session06/session06.tex` | Belum ada |
| `\include{chapter06}` di `module/advanced-web-engineering.tex` | Masih dikomentari |

Pengukuran yang perlu dijalankan dan dicatat, sesuai aturan bab lain:

1. Waktu jalan tiap lapisan pengujian: unit, integration, dan E2E.
2. Coverage `harga.py` penuh, lalu tanpa pengujian batas
   (`pytest -k "not batas_grosir"`), untuk memperlihatkan coverage tetap 100
   persen padahal cacat batas lolos.
3. Mutasi tangan pada `hitung_diskon`, yaitu mengubah `>=` menjadi `>`,
   dijalankan terhadap kedua suite. Kembalikan file sesudahnya.
4. Jumlah query tiap alamat, dibaca dari header `X-Query-Count`.
5. Temuan `ruff` dan status keluar `gate-mutu.py`.

Sebelum mengukur: `docker compose up -d` lalu `./siapkan-data.sh` dari
`sources/chapter06`. Basis datanya di port 5436, aplikasinya di port 8020.

## Penyeragaman istilah

Istilah Inggris yang baru disepakati sudah dipakai penuh di Bab 5 dan slide
sesi 5, tetapi belum di bab lain. Yang tertinggal di Bab 2 sampai Bab 4
beserta slidenya: `berkas`, `jawaban`, `anggaran`, `latensi`, `gejala`,
`pita`, `kewarasan`, `pemanasan`, dan `vonis`. Daftar lengkap istilahnya ada
di `CLAUDE.md`.

## Catatan pemeliharaan

- Container basis data Bab 5 (`awe5-db`, port 5435) masih menyala. Matikan
  dengan `docker compose down -v` dari `sources/chapter05` bila tidak dipakai.
- Empat kotak meluap 1,42 pt pada log buku berasal dari nomor halaman tiga
  digit di daftar isi, dan memang dibiarkan.
