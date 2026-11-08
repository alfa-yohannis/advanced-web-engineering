# Pekerjaan yang Belum Selesai

Catatan ini menandai keadaan repositori pada 8 November 2026, supaya pekerjaan
berikutnya tidak dimulai dari menebak-nebak.

## Yang sudah lengkap

Bab 1 sampai Bab 14 sudah punya naskah, slide, file sumber, dan angka yang
diukur sungguhan. Seluruh empat belas bab sudah masuk buku, dan bukunya
terbangun di 279 halaman.

Seluruh perintah di README sumber dan di listing latihan Bab 1 sampai Bab 14
sudah dijalankan pada 7 dan 8 November 2026, dan seluruhnya berjalan.
Perkecualiannya hanya `sources/chapter02/skrip-beban.js`, karena `k6` belum
terpasang di komputer pengukuran.

Istilah di naskah, slide, README sumber, dan nama di kode sudah mengikuti
daftar istilah di `CLAUDE.md`. Seluruh slide memberi baris kosong sesudah tabel dan gambar, dan
tidak ada lagi judul slide yang menutupi logo.

## Istilah lama yang sengaja dibiarkan

Nama di kode sudah mengikuti daftar istilah sejak 8 November 2026. Yang sengaja
dibiarkan:

- `const jawaban` di `sources/chapter04/statis/app.3f9a2c.js`, karena *hash*
  isi file itu menjadi bagian namanya, sedangkan ETag dan ukurannya dikutip
  naskah. Mengganti namanya berarti mengukur ulang seluruh angka itu.
- Nama `*_mati` di Bab 11 (`pengukur.py`, `statis/rute.js`,
  `ukur-tanpa-js.py`), karena di sana artinya JavaScript dimatikan, dan kolom
  "Skrip mati" yang tercetak dikutip di tabel Bab 11.
- `jawaban` dalam arti jawaban model LLM di `asisten.py`, `model-tiruan.py`,
  dan `ukur-llm.py` Bab 14.
- `berkas` dan `papan` di dalam analogi naskah, dan `jawaban` dalam arti
  jawaban atas pertanyaan.

Bagian topik penelitian di `README.md` belum diseragamkan, dan masih memakai
`latensi`, `anggaran`, `basi`, `segar`, dan `jawaban`.

## Listing yang dirapikan

Setiap listing kode sama persis dengan file sumbernya, dan tidak ada baris
listing yang lebih dari 78 karakter. Satu-satunya keluaran yang dirapikan
adalah rencana Q1 Bab 3, yaitu `lst:plan-sebelum` dan salinannya di slide
sesi 3. Baris aslinya selebar 126 karakter, sehingga `loops=1` dibuang dan
bagian `actual` milik *node* Parallel Seq Scan dipindah ke baris berikutnya.
Caption dan slidenya menyebut bahwa keluaran itu dirapikan.

Dua baris di slide sesi 3 tampak lebih dari 78 karakter bila markup pewarna
`(*\textcolor{red}{...}*)` dan spasi yang dibuang `gobble` ikut dihitung. Lebar
tampilnya 59 dan 76 karakter.

## Menjadikan buku ini buku referensi

Dasar aturannya perlu dipastikan lebih dahulu. Pedoman Operasional
Penilaian Angka Kredit (PO PAK) 2019 sudah diganti
Kepmendiktisaintek Nomor 63/M/KEP/2025, dan ringkasan dari penerbit menyebut
syarat tebal buku referensi maupun monograf naik menjadi 125 halaman, dengan
monograf kini bernilai sama, yaitu 40 angka kredit. Salinan resminya berupa
pindaian yang tidak dapat dibaca mesin, jadi angka itu belum terverifikasi
dari sumber primer dan perlu ditanyakan ke tim Penetapan Angka
Kredit (PAK) kampus.

Definisi buku referensi pada PO PAK bersifat positif: ber-ISBN, satu bidang
ilmu sesuai kompetensi penulis, serta memenuhi syarat karya ilmiah utuh, yaitu
rumusan masalah bernilai kebaruan, metodologi pemecahan masalah, dukungan
data atau teori mutakhir, kesimpulan, dan daftar pustaka. Tidak ada kalimat
yang melarang soal latihan. Yang berisiko adalah penggolongannya: bab yang
dibuka tujuan pembelajaran lalu ditutup latihan beserta lembar isian terbaca
sebagai buku ajar, dan buku ajar bernilai 20 angka kredit, bukan 40.

Prosedur pengukuran justru memperkuat syarat metodologi, selama dibaca
sebagai metode, bukan sebagai pekerjaan rumah. Karena satu terbitan dinilai
sekali, rencananya tetap: satu sumber naskah, dua edisi, dan yang ber-ISBN
adalah edisi referensi.

### Sudah dikerjakan

- Preamble dipisah ke `module/preamble.tex`, dipakai kedua edisi.
- Penanda `\ifajar` dipasang. `advanced-web-engineering.tex` membangun edisi
  referensi, dan `advanced-web-engineering-ajar.tex` membangun edisi ajar.
- Seksi Latihan tiap bab dipindah ke `module/latihanNN.tex`. Edisi ajar
  mencetaknya di akhir babnya, edisi referensi mengumpulkannya sebagai
  Lampiran A "Prosedur Pengukuran".
- Tujuan Pembelajaran hanya dicetak di edisi ajar.
- Judul tiap prosedur mengikuti edisinya: "Latihan N" atau "Prosedur N".
- `module/prakata.tex` dan `module/metode.tex` ditulis, berisi lingkungan
  pengukuran, empat aturan yang dipegang, dan batas keberlakuan angkanya.
- Keduanya terbangun bersih: edisi referensi 285 halaman, edisi ajar 283.

### Masih harus dikerjakan

1. Lembar isian kosong (57 tabel berjudul "Lembar isian") masih tercetak di
   edisi referensi. Bungkus dengan `\ifajar`, karena tabel kosong itulah
   penanda paling kuat yang membuat buku terbaca sebagai buku ajar.
2. Bab 1 masih bergaya pengantar mata kuliah, termasuk peta pertemuan. Di
   edisi referensi, bab itu perlu dibingkai ulang sebagai pengantar bidang
   ilmu, atau dipindahkan ke edisi ajar saja.
3. Kata "latihan", "pertemuan", dan "mahasiswa" di badan bab perlu disapu
   untuk edisi referensi.
4. Indeks belum ada isinya. `makeidx` sudah dipasang; perlu satu sapuan
   `\index{}` untuk istilah di `CLAUDE.md` dan singkatan di `README.md`,
   lalu `\printindex` di belakang edisi referensi.
5. Glosarium dan biografi penulis belum ada. Keduanya bagian akhir yang
   disarankan panduan penerbit.
6. Tiap bab perlu satu paragraf metode di depan hasilnya: apa yang diukur,
   dengan alat apa, berapa ulangan.
7. Pustaka perlu diperkuat. Dari 116 entri, baru 15 berupa jurnal dan
   prosiding, sedangkan sisanya RFC, spesifikasi, dan dokumentasi vendor.
   Sasaran: dua sampai tiga karya ilmiah per bab yang membahas hal yang sama.
8. Bab penutup lintas bab belum ada, yaitu rangkuman temuan dan arah
   penelitian lanjutan.
9. Ukuran cetak perlu dipastikan ke penerbit. Naskah sekarang B5 (17,6 x 25
   cm), sedangkan panduan menyebut format UNESCO 15,5 x 23 cm. Ditjen Dikti
   menyebut rentang A5 sampai A4, jadi B5 masih di dalamnya, tetapi penerbit
   yang menentukan.
10. ISBN dan penerbit belum ada. Perpusnas mensyaratkan paling sedikit 49
    halaman untuk ISBN, dan jumlah halaman buku ini sudah jauh melewatinya.

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
- Container `awe3-cek-db` di port 5439 beserta volume `ch03-cek_data-awe3cek`
  dibuat untuk memeriksa Bab 3 tanpa menyentuh `awe-db`. Keduanya dalam
  keadaan *stop* dan boleh dihapus bila tidak dipakai.
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
