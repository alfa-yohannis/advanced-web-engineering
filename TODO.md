# Pekerjaan yang Belum Selesai

Catatan ini menandai keadaan repositori pada 29 September 2026, supaya
pekerjaan berikutnya tidak dimulai dari menebak-nebak.

## Bab 6: sudah masuk modul, masih perlu dirapikan

Naskah, slide, dan file sumbernya sudah ada, dan seluruh angkanya diukur
sungguhan. Yang masih perlu dikerjakan:

- Menambah satu latihan yang memakai Playwright secara langsung, karena
  Latihan 1 baru menjalankannya tanpa membedah isinya.
- Memeriksa apakah tabel Daftar Singkatan di `README.md` perlu tambahan untuk
  E2E dan CI.
- Menimbang apakah `package-lock.json` perlu tetap dilacak git, karena
  isinya panjang dan hanya dipakai lapisan E2E.

## Penyeragaman istilah

Istilah Inggris yang baru disepakati sudah dipakai penuh di Bab 5, Bab 6, dan
slide keduanya, tetapi belum di bab lain. Yang tertinggal di Bab 2 sampai
Bab 4 beserta slidenya: `berkas`, `jawaban`, `anggaran`, `latensi`, `gejala`,
`pita`, `kewarasan`, `pemanasan`, dan `vonis`. Daftar lengkap istilahnya ada
di `CLAUDE.md`.

## Bab 7 dan sesudahnya

Naskah `module/chapter07.tex` sampai `chapter14.tex` masih kerangka berisi
`% TODO`, dan direktori `sources/chapter07` sampai `chapter14` masih kosong.
Peta topik tiap pertemuan ada di `README.md` akar.

## Catatan pemeliharaan

- Container basis data Bab 5 (`awe5-db`, port 5435) dan Bab 6 (`awe6-db`,
  port 5436) masih menyala. Matikan dengan `docker compose down -v` dari
  direktori sumber masing-masing bila tidak dipakai.
- Enam belas kotak meluap 1,42 pt pada log buku berasal dari nomor halaman
  tiga digit di daftar isi, dan memang dibiarkan.
