# Pekerjaan yang Belum Selesai

Catatan ini menandai keadaan repositori pada 7 November 2026, supaya pekerjaan
berikutnya tidak dimulai dari menebak-nebak.

## Yang sudah lengkap

Bab 2 sampai Bab 14 sudah punya naskah, slide, file sumber, dan angka yang
diukur sungguhan. Seluruh empat belas bab sudah masuk buku, dan bukunya
terbangun di 261 halaman.

## Penyeragaman istilah

Istilah Inggris yang disepakati sudah dipakai penuh di Bab 5 sampai Bab 14
beserta slidenya, tetapi belum di bab lain. Yang tertinggal di Bab 2 sampai
Bab 4 beserta slidenya: `berkas`, `jawaban`, `anggaran`, `latensi`, `gejala`,
`pita`, `kewarasan`, `pemanasan`, dan `vonis`. Daftar lengkap istilahnya ada
di `CLAUDE.md`.

## Bab 1

Naskah `module/chapter01.tex` masih kerangka berisi `% TODO`, padahal sudah
aktif di buku, sehingga tercetak sebagai bab tanpa isi. Direktori
`sources/chapter01` masih kosong, dan slide `session01` belum ada. Peta
topiknya ada di `README.md` akar.

## Pemeriksaan sumber Bab 2 sampai Bab 13

Belum ada pemeriksaan bahwa seluruh sumber Bab 2 sampai Bab 13 masih dapat
dijalankan. Pemeriksaan yang sempat dimulai pada 7 November 2026 menemukan
lima hal yang perlu disiapkan atau diperiksa lebih dahulu:

- `sources/.venv` belum memuat seluruh pustaka yang diminta README Bab 4,
  Bab 6, dan Bab 7. Pemasangannya sempat dihentikan di tengah jalan.
- `sources/chapter06/node_modules` belum ada. Pengujian E2E Bab 6 dan
  pemeriksaan tipe Bab 12 membutuhkannya.
- `k6` belum terpasang, padahal `sources/chapter02/skrip-beban.js`
  membutuhkannya.
- README Bab 12 menjalankan `python3`, sedangkan aplikasinya membutuhkan
  `jsonschema` yang tidak ada di Python sistem. Hal ini belum diperiksa dengan
  menjalankannya.
- Di komputer pengukuran, port 5433, 8000, dan 8080 dipakai layanan proyek
  lain, sehingga Bab 3, `aplikasi.py` Bab 4, dan Bab 11 tidak dapat dinyalakan
  tanpa mematikan layanan itu lebih dahulu.

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
  sumber masing-masing bila tidak dipakai. Bab 8, Bab 11, dan Bab 14 sengaja
  tidak memakai container sama sekali.
- Kotak meluap 1,42 pt pada log buku berasal dari nomor halaman tiga digit di
  daftar isi, dan memang dibiarkan.
- `package-lock.json` Bab 6 tetap dilacak git, karena ia yang mengunci versi
  Playwright yang dipakai mengukur.
- Bab 13 memakai port 8100 untuk server peristiwa, 8101 untuk WebSocket, dan
  8102 untuk penerima *webhook*. WebSocket-nya ditulis dengan pustaka standar,
  jadi tidak ada dependensi baru. File `antrean.json` dibuat sendiri oleh
  skripnya dan tidak dilacak git.
- Bab 12 memakai `tsc` dari `sources/chapter06/node_modules`, sehingga tidak
  menambah pemasangan npm. Aplikasinya di port 8090 dan *gateway*-nya di
  8091.
- Pengukuran Bab 11 memakai Chrome tanpa jendela lewat `--dump-dom`, bukan
  Playwright, sehingga Bab 11 tidak menambah dependensi npm. Aplikasinya
  memakai port 8080 dan hanya menyala selama pengukuran.
- Bab 14 memakai port 8110 untuk penyeimbang beban, 8111 sampai 8118 untuk
  replika, 8119 untuk basis data tiruan, 8120 untuk PWA, 8121 untuk asisten,
  dan 8122 untuk model tiruan. Seluruhnya Python pustaka standar.
- `ukur-offline.py` Bab 14 mengendalikan Chrome lewat DevTools Protocol di
  atas pipa (`chrome_pipa.py`), bukan `--dump-dom` seperti Bab 11, karena
  `--dump-dom` menutup Chrome sebelum *service worker* selesai dipasang.
  Akibatnya skrip itu hanya berjalan di Linux dan macOS.
- Angka Bab 14 diukur pada laptop Intel Core i9-11900H dengan Python 3.15.2
  dan Chrome 157. Permintaan kedua pada kunjungan kedua `ukur-offline.py`
  berasal dari fitur `ServiceWorkerAutoPreload` Chrome, sehingga versi Chrome
  lain dapat mencatat angka berbeda.
- Biaya di `sources/chapter14/rencana.json` dan waktu token di
  `model-tiruan.py` sengaja ditetapkan, bukan diukur. Keduanya disebut terang
  di naskah Bab 14.
