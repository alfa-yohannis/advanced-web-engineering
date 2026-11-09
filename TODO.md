# Pekerjaan yang Belum Selesai

Catatan ini menandai keadaan repositori pada 8 November 2026, supaya pekerjaan
berikutnya tidak dimulai dari menebak-nebak.

## Yang sudah lengkap

Bab 1 sampai Bab 14 sudah punya naskah, slide, file sumber, dan angka yang
diukur sungguhan. Seluruh empat belas bab sudah masuk buku, dan bukunya
terbangun di 291 halaman.

Seluruh perintah di README sumber dan di listing latihan Bab 1 sampai Bab 14
dijalankan ulang pada 9 November 2026 di port bawaan tiap bab, termasuk Bab 3,
`aplikasi.py` Bab 4, dan Bab 11 yang sebelumnya terhalang port proyek lain.
Seluruhnya berjalan. `sources/chapter02/skrip-beban.js` dijalankan lewat image
Docker `grafana/k6`, karena `k6` tidak terpasang, dan sasarannya kini API
Bab 1 di port 8050. Kedua skrip Bab 15 juga berjalan pada ketiga repositori
RAG-nya.

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

Dasar aturannya sudah diperiksa ke sumber primernya. Pedoman Operasional
Penilaian Angka Kredit (PO PAK) 2019 diganti Kepmendiktisaintek Nomor
63/M/KEP/2025. Salinannya berupa pindaian, jadi dibaca lewat OCR, dan tabel
angka kreditnya berbunyi begini:

| Kegiatan | Angka kredit | Batas pengakuan | Letak |
| --- | --- | --- | --- |
| Buku referensi | 40 | 1 buku/tahun | lampiran hlm. 32 |
| Monograf | 20 | 1 buku/tahun | lampiran hlm. 32 |
| Book chapter internasional | 15 | 1 buku/tahun | lampiran hlm. 32 |
| Book chapter nasional | 10 | 1 buku/tahun | lampiran hlm. 32 |
| Buku ajar | 20 | 1 buku/tahun | lampiran hlm. 30 |
| Diktat, modul, petunjuk praktikum | 5 | 1 produk/semester | lampiran hlm. 30 |

Dua kabar yang beredar di panduan penerbit ternyata tidak ada di keputusan
itu: monograf tetap 20, bukan 40, dan tidak ada angka 125 halaman di seluruh
41 halaman salinannya. Keputusan itu memuat jenis kegiatan, bukti, angka
kredit, dan batas pengakuan, tanpa definisi maupun syarat tebal buku. Syarat
substansinya, yaitu ISBN, tebal paling sedikit 40 halaman cetak format
UNESCO, dan keharusan berasal dari hasil penelitian atau pemikiran penulis,
masih mengacu PO PAK 2019 beserta penjelasan butirnya, dan itu yang perlu
dipastikan ke tim Penetapan Angka Kredit (PAK) kampus.

Definisi buku referensi pada PO PAK bersifat positif: ber-ISBN, satu bidang
ilmu sesuai kompetensi penulis, serta memenuhi syarat karya ilmiah utuh, yaitu
rumusan masalah bernilai kebaruan, metodologi pemecahan masalah, dukungan
data atau teori mutakhir, kesimpulan, dan daftar pustaka. Tidak ada kalimat
yang melarang soal latihan. Yang berisiko adalah penggolongannya: bab yang
dibuka tujuan pembelajaran lalu ditutup latihan beserta lembar isian terbaca
sebagai buku ajar, dan buku ajar bernilai 20 angka kredit, bukan 40.

Prosedur pengukuran justru memperkuat syarat metodologi, selama dibaca
sebagai metode, bukan sebagai pekerjaan rumah.

Rencana dua edisi dibatalkan pada 9 November 2026. Naskahnya kini satu buku
referensi yang dapat juga digunakan sebagai buku ajar, dan pernyataan itu
ditulis di Prakata serta di Pendahuluan Bab 1. Badan bab tetap bergaya
referensi: tanpa tujuan pembelajaran di awal bab dan tanpa latihan di akhir
bab. Keduanya, beserta 57 lembar isian, dikumpulkan di Lampiran A, Latihan
dan Prosedur Pengukuran. Risikonya tetap tercatat: lembar isian dan tujuan
pembelajaran di lampiran masih dapat dibaca penilai sebagai ciri buku ajar.

### Sudah dikerjakan

- Preamble dipisah ke `module/preamble.tex`.
- Seksi Latihan tiap bab dipindah ke `module/latihanNN.tex`, dan seluruhnya
  dicetak sebagai Lampiran A. Tiap bagian lampiran dibuka Tujuan
  Pembelajaran babnya, lalu latihan berjudul "Latihan N" beserta lembar
  isiannya.
- `module/prakata.tex` dan `module/metode.tex` ditulis, berisi lingkungan
  pengukuran, empat aturan yang dipegang, dan batas keberlakuan angkanya.
- Bab 1 berjudul "Cakupan Bidang dan Alur Rekayasanya". Pendahuluannya
  menyatakan buku ini buku referensi yang dapat juga digunakan sebagai buku
  ajar, dan seksi Peta Empat Belas Bab memetakan bab, bukan pertemuan,
  dengan satu kalimat bahwa satu bab mengisi satu pertemuan bila dipakai di
  kelas.
- Penanda `\ifajar`, makro `\tabisi`, dan
  `advanced-web-engineering-ajar.tex` sudah dibuang. Bukunya terbangun di
  289 halaman tanpa rujukan yang menggantung.

### Masih harus dikerjakan

1. Kata "pertemuan", "praktikum", dan "mahasiswa" masih muncul di badan bab,
   misalnya di Ringkasan Bab 1. Karena buku ini juga dipakai sebagai buku
   ajar, kata itu tidak salah, tetapi badan bab yang dibaca sebagai referensi
   lebih tepat memakai "pembaca" dan "pengukuran".
2. ~~Halaman judul masih bertuliskan "Course Module -- IF140303".~~ Sudah
   dikerjakan. Judulnya *Measurement-Based Web Engineering*, baris Course
   Module dibuang, dan arti berbasis pengukuran dijelaskan di Metode
   Pengukuran beserta tiga contohnya.
3. Jenis komputer pengukuran tidak seragam. `metode.tex` dan Bab 11 menyebut
   komputer meja, sedangkan Bab 1, Bab 14, dan Latihan 14 menyebut laptop
   Intel Core i9-11900H. Komputer yang menjalankan seluruh sumber pada
   9 November 2026 adalah laptop HP ENVY 15 dengan prosesor itu.
4. Indeks belum ada isinya. `makeidx` sudah dipasang; perlu satu sapuan
   `\index{}` untuk istilah di `CLAUDE.md` dan singkatan di `README.md`,
   lalu `\printindex` di belakang buku.
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

- Port 5433, 8000, dan 8080 dipakai NikahYuk: container `nikahyuk-db-1`,
  service systemd user `nikahyuk-api`, dan `nikahyuk-website`. Bab 3,
  `aplikasi.py` Bab 4, dan Bab 11 hanya dapat dinyalakan di port bawaannya bila
  NikahYuk dimatikan dulu dengan
  `systemctl --user stop nikahyuk-api nikahyuk-website` lalu
  `docker stop nikahyuk-db-1`. Nyalakan lagi sesudahnya dengan
  `docker start nikahyuk-db-1` lalu
  `systemctl --user start nikahyuk-api nikahyuk-website`, karena
  `nikahyuk-api` adalah API uji yang dibuka lewat tunnel Cloudflare.
- Python sistem di komputer pengukuran sudah 3.15.2, sedangkan
  `sources/.venv` dibuat dengan 3.14. Menjalankan `python3 -m venv` di atas
  venv yang sudah ada menulis ulang `pyvenv.cfg` dan pip untuk 3.15, dan
  pemasangan berikutnya tidak terlihat oleh Python venv. Karena itu seluruh
  listing, README, dan slide kini memakai
  `test -d ../.venv || python3 -m venv ../.venv`.
- Volume `chapter03_data-awe` milik `awe-db` dibuat 4 September dengan user
  `awe`, sebelum compose diganti ke `admin`. Pada 9 November role `admin`
  ditambahkan dan data Bab 3 dimuat ulang dari `01-skema.sql` dan
  `02-data-uji.sql`, sehingga `awe-db` kini dapat dipakai seperti tertulis.
- Container `awe4-db`, `awe4-redis`, `awe5-db`, `awe6-db`, `awe7-db`,
  `awe9-biru`, dan `awe9-hijau` dalam keadaan *stop*. Volume basis data Bab 4
  sampai Bab 7 dan image `awe9-layanan` masih ada. Hapus dengan
  `docker compose down -v` dari direktori sumber masing-masing bila tidak
  dipakai. Bab 8, Bab 11, dan Bab 14 sengaja tidak memakai container sama
  sekali.
- Container `awe3-cek-db` di port 5439 beserta volume `ch03-cek_data-awe3cek`
  dibuat untuk memeriksa Bab 3 tanpa menyentuh `awe-db`. Sejak `awe-db` dapat
  dipakai lagi, keduanya tidak diperlukan dan boleh dihapus.
- Dua angka contoh layak diukur ulang di komputer yang sedang sepi. Pada
  9 November p95 `/api/terlaris` Bab 5 sekitar 262 milidetik, di bawah budget
  400 milidetik, sehingga `gate-budget.py` mencetak "Gagal: 5", bukan 6
  seperti `lst:gate-jalan`, `lst:c5-lat1-jalan`, dan `tab:c5-lat1-contoh`.
  Angka Bab 5 untuk *query* itu dua sampai tiga kali lebih lambat daripada
  angka Bab 4 untuk *query* yang sama. Kolom "p50, 1" di
  `tab:c4-lat3-contoh` juga sekitar dua kali waktu satu *query* di bab itu.
- `rekam-har.py` Bab 2 meminta Chrome memilih port debug sendiri dan membaca
  `DevToolsActivePort` dari profilnya, karena port tetap 9222 bentrok dengan
  Chrome lain di komputer yang sama. Profil sementaranya kini dihapus sesudah
  rekaman.
- Pilihan `javascript_hidup=False` di `sources/chapter11/pengukur.py` tidak
  berjalan pada Chrome 157: `--dump-dom` dengan `scriptEnabled=false`
  mencetak 0 byte. Belum ada yang memanggilnya, karena `ukur-tanpa-js.py`
  memakai rute `blokir_skrip=1`.
- Repositori RAG Bab 15 diklon dari `github.com/alfa-yohannis/exim`, `djp`,
  dan `akreditasi` ke `sources/chapter15/rag/`, yang tidak dilacak git.
  Skripnya dijalankan sesudah `source ../.venv/bin/activate`, karena
  pemanggilan `../.venv/bin/python` lewat jalur relatif membuat Python 3.14
  mencetak peringatan `sys.prefix`.
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
