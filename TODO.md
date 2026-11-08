# Pekerjaan yang Belum Selesai

Catatan ini menandai keadaan repositori pada 8 November 2026, supaya pekerjaan
berikutnya tidak dimulai dari menebak-nebak.

## Yang sudah lengkap

Bab 1 sampai Bab 14 sudah punya naskah, slide, file sumber, dan angka yang
diukur sungguhan. Seluruh empat belas bab sudah masuk buku, dan bukunya
terbangun di 277 halaman.

Seluruh perintah di README sumber dan di listing latihan Bab 1 sampai Bab 14
sudah dijalankan pada 7 dan 8 November 2026, dan seluruhnya berjalan.
Perkecualiannya hanya `sources/chapter02/skrip-beban.js`, karena `k6` belum
terpasang di komputer pengukuran.

Istilah di naskah, slide, dan README sumber sudah mengikuti daftar istilah di
`CLAUDE.md`. Seluruh slide memberi baris kosong sesudah tabel dan gambar, dan
tidak ada lagi judul slide yang menutupi logo.

## Nama di kode yang masih memakai istilah lama

Sekitar 150 nama variabel dan fungsi di `sources/` masih memakai istilah lama,
terutama `jawaban`, `berkas`, dan `rakit`. Contohnya `kirim_jawaban` dan
`isi_berkas` di Bab 4, `LAMA_RAKIT_DETIK` di Bab 8, serta `periksa_jawaban`
dan `rakit_halaman` di Bab 12. Banyak di antaranya dikutip di listing naskah
dan slide, sehingga penggantiannya harus ikut memperbarui listing itu, dan
juga keluaran yang dikutip bila nama tersebut tercetak.

Beberapa kata lama sengaja dibiarkan, karena maknanya berbeda:

- `berkas` dan `papan` di dalam analogi: berkas di loket, papan harga warung,
  papan pengumuman, papan tulis, dan papan peringkat.
- `jawaban` dalam arti jawaban atas pertanyaan, termasuk jawaban model LLM di
  Bab 14.
- `Skrip mati` di Bab 11, yang berarti JavaScript dimatikan, bukan *down*.

Bagian topik penelitian di `README.md` juga belum diseragamkan, dan masih
memakai `latensi`, `anggaran`, `basi`, `segar`, dan `jawaban`.

## Listing yang belum sama persis dengan sumber atau keluarannya

Masalah isi yang ditemukan pemeriksaan sumber 8 November 2026 sudah
dibereskan. Yang tersisa hanya listing yang belum sama persis:

- Bab 12: baris pembuka server di `lst:c12-siapkan` dipendekkan, karena baris
  aslinya lebih dari 78 karakter. Agar dapat dikutip apa adanya, pesan
  programnya yang perlu dipendekkan. Slide sesi 12 memendekkan baris
  *gateway* lebih jauh lagi, dan keluaran `uji-kontrak` di sana tidak memuat
  ", sama".
- Bab 13: listing Latihan 3 hanya memuat tabel pertama dari keluaran
  `ukur-antrean.py`.
- Beberapa listing kode lama bukan salinan persis file sumbernya, atau
  panjangnya 79 sampai 80 karakter, misalnya `chapter05.tex` baris 125, 180,
  409, dan 653.

## Catatan pemeliharaan

- Port 5433, 8000, dan 8080 dipakai layanan proyek lain di komputer
  pengukuran. Bab 3, `aplikasi.py` Bab 4, dan Bab 11 hanya dapat dinyalakan di
  port bawaannya bila layanan itu dimatikan lebih dahulu.
- Container `awe4-db`, `awe4-redis`, `awe5-db`, `awe6-db`, `awe7-db`,
  `awe9-biru`, dan `awe9-hijau` dalam keadaan *stop*. Volume basis data Bab 4
  sampai Bab 7 dan image `awe9-layanan` masih ada. Hapus dengan
  `docker compose down -v` dari direktori sumber masing-masing bila tidak
  dipakai. Bab 8, Bab 11, dan Bab 14 sengaja tidak memakai container sama
  sekali.
- Label keluaran `ukur-query.py` Bab 3, `worker.py` Bab 13, dan
  `ukur-offline.py` Bab 14 diganti mengikuti daftar istilah. Kutipan
  keluarannya ditulis ulang dengan angka pengukuran yang sama, seperti pada
  commit 25bc112. `ukur-antrean.py` dan `ukur-offline.py` sudah dijalankan
  ulang dan mencetak label baru itu.
- Kalimat hasil di `worker.py` Bab 13 dipendekkan, agar keluaran
  `ukur-antrean.py` muat utuh di listing 78 karakter tanpa dipotong tangan.
- Kata sandi Bab 10 disimpan sebagai *salt* dan *hash* scrypt dengan biaya
  2^14, sengaja kecil agar latihan tetap cepat. Nama yang tidak terdaftar
  tetap menjalani satu scrypt, sehingga lama *response* tidak membocorkan
  nama mana yang terdaftar. Ketiga jalurnya sama-sama sekitar 32 milidetik.
- Langkah 4 Latihan 4 Bab 6 meminta mahasiswa memperbaiki N+1 di
  `aplikasi.py` sekaligus memperbarui uji kontrak yang mengunci perilaku
  lama, lalu mengembalikan keduanya sebelum Latihan 5, karena uji E2E
  Latihan 5 membutuhkan jalur N+1.
- `alarm.py` Bab 9 tidak menilai versi yang belum menerima permintaan sama
  sekali, dan gagal bila belum ada versi yang menerima permintaan.
  `ci-contoh.yml` hanya menjalankan lapisan unit, karena pengujian integrasi
  Bab 6 membutuhkan PostgreSQL berisi data Bab 3.
- Antrean Bab 13 memindahkan pekerjaan yang sudah dicoba lima kali ke
  *dead letter*, sesuai `BATAS_PERCOBAAN`.
- Judul slide dibatasi sekitar 37 karakter. Judul yang tepi kanannya lewat
  343 pt menutupi logo Pradita, karena kotak judul berlatar putih digambar di
  atas logo.
- Kotak meluap 1,42 pt dan 1,71 pt pada log buku berasal dari nomor halaman
  tiga digit di daftar isi, dan memang dibiarkan. Kotak meluap 0,43 pt di
  Bab 7 berasal dari kata `Content-Security-Policy` yang tidak dapat dipenggal.
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
- API kerangka Bab 1 memakai port 8050. `periksa-lingkungan.py` memeriksa
  seluruh port bab 1 sampai 14, sehingga daftar `PORT_PER_BAB` di dalamnya
  ikut diperbarui bila bab mana pun mengganti port.
- Angka `simulasi-cabang.py` Bab 1 diukur dengan Git 2.43. Benih acaknya
  tetap, tetapi versi Git lain dapat menghitung batas blok konflik sedikit
  berbeda.
