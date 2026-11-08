# Pekerjaan yang Belum Selesai

Catatan ini menandai keadaan repositori pada 8 November 2026, supaya pekerjaan
berikutnya tidak dimulai dari menebak-nebak.

## Yang sudah lengkap

Bab 1 sampai Bab 14 sudah punya naskah, slide, file sumber, dan angka yang
diukur sungguhan. Seluruh empat belas bab sudah masuk buku, dan bukunya
terbangun di 275 halaman.

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

## Temuan pemeriksaan sumber yang belum dibereskan

Pemeriksaan 8 November 2026 menemukan hal-hal berikut. Perintahnya tetap
berjalan, tetapi naskah, langkah latihan, atau isi file belum sesuai.

- Bab 5: `lst:gate-jalan` disebut keluaran apa adanya, tetapi tidak memuat
  baris "8 worker, 25 permintaan per worker".
- Bab 6: langkah 4 Latihan 3 tidak dapat dikerjakan, karena seluruh 200.000
  pesanan berisi tepat 3 item. Langkah 4 Latihan 4, mengarahkan ulang
  `statis/pesanan.js`, tidak mengubah hasil *gate*, karena *gate* meminta
  `/api/pesanan-n1/1` secara langsung dan tetap keluar dengan status 1.
- Bab 7: langkah 4 Latihan 4 menghapus header dari `kebijakan.json`, sehingga
  header itu hilang dari aplikasi dan dari syarat *gate* sekaligus. Hasilnya
  15 dari 15 syarat, dengan status 0.
- Bab 8: listing `wc` tidak memuat baris `1635 total`. Latihan 4 menyapa
  pembaca dengan "Anda".
- Bab 9: komentar `Dockerfile` menyebut dua file disalin, padahal hanya satu.
  Docstring `ukur-rilis.py` menyebut cara persentil Bab 5, padahal yang
  dipakai *nearest-rank*. `ci-contoh.yml` gagal bila dijalankan apa adanya:
  tidak ada langkah pemasangan dependensi, pengujian Bab 6 butuh basis data,
  dan ruff 0.17 menandai RUF010 di `alarm.py` dan `dashboard.py`. Latihan 3
  dan `ci-contoh.yml` menyapa pembaca dengan "Anda".
- Bab 10: `pengguna.json` menyebut password disimpan sebagai *hash*, padahal
  isinya teks asli.
- Bab 12: kontrak hanya mendeklarasikan 201, 409, dan 422 untuk `POST`
  pesanan, padahal server dan naskah memakai 200 untuk permintaan ulang.
  `lst:c12-siapkan` belum mengaktifkan venv, padahal README sudah.
  `openapi.json | head -5` mencetak seluruh JSON, karena isinya satu baris.
- Bab 13: `BATAS_PERCOBAAN = 5` di `antrean.py` tidak pernah dipakai, padahal
  naskah menyebut batas lima percobaan. `LEBAR_HASIL` di `ukur-antrean.py`
  juga tidak dipakai. `curl -sN .../sse | head -4` baru selesai sesudah dua
  *event* atau *keep-alive* 15 detik, dan memotong blok kedua. Baris awal
  `webhook.py` mencetak "jenis gagal-dua-kali" yang tidak ada di listing.
  Listing `| tail -3` tidak memuat baris tabel dan baris kosong yang
  sebenarnya tercetak.

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
