# Pekerjaan yang Belum Selesai

Catatan ini menandai keadaan repositori pada 1 November 2026, supaya pekerjaan
berikutnya tidak dimulai dari menebak-nebak.

## Yang sudah lengkap

Bab 2 sampai Bab 12 sudah punya naskah, slide, file sumber, dan angka yang
diukur sungguhan. Keduabelasnya sudah masuk buku, dan bukunya terbangun di
215 halaman.

## Penyeragaman istilah

Istilah Inggris yang disepakati sudah dipakai penuh di Bab 5 sampai Bab 12
beserta slidenya, tetapi belum di bab lain. Yang tertinggal di Bab 2 sampai
Bab 4 beserta slidenya: `berkas`, `jawaban`, `anggaran`, `latensi`, `gejala`,
`pita`, `kewarasan`, `pemanasan`, dan `vonis`. Daftar lengkap istilahnya ada
di `CLAUDE.md`.

## Bab 13 dan sesudahnya

Naskah `module/chapter13.tex` dan `chapter14.tex` masih kerangka berisi
`% TODO`, dan direktori `sources/chapter13` serta `chapter14` masih kosong.
Peta topik tiap pertemuan ada di `README.md` akar.

Bab 1 juga masih kerangka, padahal sudah aktif di buku, sehingga tercetak
sebagai bab tanpa isi.

## Singkatan yang belum dieja di bab sendiri

Bab 8 memakai HTML, SPA, SSR, SSG, dan ISR tanpa mengejanya lebih dahulu di
bab itu, padahal aturannya mengeja tiap singkatan pada kemunculan pertama di
tiap bab. Semua singkatan itu sudah ada di tabel **Daftar Singkatan**
`README.md`, jadi yang kurang hanya ejaan pertamanya di naskah Bab 8.

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
  sumber masing-masing bila tidak dipakai. Bab 8 dan Bab 11 sengaja tidak
  memakai container sama sekali.
- Kotak meluap 1,42 pt pada log buku berasal dari nomor halaman tiga digit di
  daftar isi, dan memang dibiarkan.
- `package-lock.json` Bab 6 tetap dilacak git, karena ia yang mengunci versi
  Playwright yang dipakai mengukur.
- Bab 12 memakai `tsc` dari `sources/chapter06/node_modules`, sehingga tidak
  menambah pemasangan npm. Aplikasinya di port 8090 dan *gateway*-nya di
  8091.
- Pengukuran Bab 11 memakai Chrome tanpa jendela lewat `--dump-dom`, bukan
  Playwright, sehingga Bab 11 tidak menambah dependensi npm. Aplikasinya
  memakai port 8080 dan hanya menyala selama pengukuran.
