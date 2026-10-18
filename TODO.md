# Pekerjaan yang Belum Selesai

Catatan ini menandai keadaan repositori pada 18 Oktober 2026, supaya pekerjaan
berikutnya tidak dimulai dari menebak-nebak.

## Yang sudah lengkap

Bab 2 sampai Bab 9 sudah punya naskah, slide, file sumber, dan angka yang
diukur sungguhan. Kesembilannya sudah masuk buku, dan bukunya terbangun di
172 halaman.

## Penyeragaman istilah

Istilah Inggris yang disepakati sudah dipakai penuh di Bab 5 sampai Bab 9
beserta slidenya, tetapi belum di bab lain. Yang tertinggal di Bab 2 sampai
Bab 4 beserta slidenya: `berkas`, `jawaban`, `anggaran`, `latensi`, `gejala`,
`pita`, `kewarasan`, `pemanasan`, dan `vonis`. Daftar lengkap istilahnya ada
di `CLAUDE.md`.

## Bab 10 dan sesudahnya

Naskah `module/chapter10.tex` sampai `chapter14.tex` masih kerangka berisi
`% TODO`, dan direktori `sources/chapter10` sampai `chapter14` masih kosong.
Peta topik tiap pertemuan ada di `README.md` akar.

Bab 1 juga masih kerangka, padahal sudah aktif di buku, sehingga tercetak
sebagai bab tanpa isi.

## Catatan bentuk praktikum Bab 7

Peta pertemuan di `README.md` menuliskan praktikum Bab 7 sebagai menyerang
*branch* yang sengaja dibuat rentan. Bentuk itu diganti menjadi mengaudit dan
mengeraskan aplikasi sendiri, lalu menegakkannya sebagai *gate* keamanan.
Cakupan materinya tetap sama, dan seluruh pemeriksaannya bersifat mengamati
terhadap aplikasi di komputer sendiri. Bila bentuk lamanya tetap diinginkan,
teks peta pertemuan perlu disesuaikan atau dibahas lebih dahulu.

## Catatan pemeliharaan

- Container basis data Bab 6 (`awe6-db`, 5436) dan Bab 7 (`awe7-db`, 5437)
  masih menyala. Matikan dengan `docker compose down -v` dari direktori
  sumber masing-masing bila tidak dipakai. Bab 8 sengaja tidak memakai
  container sama sekali.
- Kotak meluap 1,42 pt pada log buku berasal dari nomor halaman tiga digit di
  daftar isi, dan memang dibiarkan.
- `package-lock.json` Bab 6 tetap dilacak git, karena ia yang mengunci versi
  Playwright yang dipakai mengukur.
