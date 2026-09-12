# Aturan Penulisan Modul

Aturan ini diekstrak dari `module/chapter02.tex`, yang menjadi bab acuan. Bab
lain ditulis mengikuti pola yang sama persis, sehingga seluruh modul terbaca
sebagai satu suara.

## 1. Bahasa

- Bahasa Indonesia baku, kalimat pendek, satu gagasan per kalimat.
- Keterbacaan dan kemudahan dipahami didahulukan di atas istilah yang terdengar
  canggih. Pilih kata yang biasa dipakai sehari-hari, dan jelaskan istilah
  teknis dengan kalimat sederhana saat pertama muncul.
- Kalimat aktif. Hindari "dapat dilakukan dengan cara", cukup "dilakukan dengan".
- Tanpa kata pengisi: "sangat", "sebenarnya", "tentu saja", "cukup jelas bahwa".
- Pakai kata yang lazim: "biaya", bukan "ongkos".
- Tanpa sapaan langsung ke pembaca ("Anda", "kita akan", "mari"). Naskah
  berbicara tentang sistem, bukan kepada orang.
- Istilah asing yang belum punya padanan mapan ditulis miring: `\textit{cache}`,
  `\textit{main thread}`, `\textit{frame}`. Istilah yang sudah diserap ditulis
  biasa: server, browser, klien, data.
- Istilah yang terasa janggal atau tidak lazim bila diterjemahkan tetap ditulis
  dalam bahasa Inggris dan dicetak miring: `\textit{pool}`, `\textit{circuit
  breaker}`, `\textit{retry}`, `\textit{race condition}`, `\textit{source of
  truth}`, `\textit{request}`, `\textit{key-value}`, `\textit{compress}`,
  `\textit{range}`, `\textit{dashboard}`, `\textit{social network}`,
  `\textit{constraint}`, `\textit{generate}`, `\textit{error}`,
  `\textit{worker}`, `\textit{conflict}`, `\textit{disk}`, `\textit{node}`,
  `\textit{noise}`, `\textit{refresh}`, `\textit{throttling}`, bukan kolam,
  pemutus sirkuit, pengulangan, balapan, sumber kebenaran, pemanggilan,
  kunci-nilai, dimampatkan, papan pemantauan, jaringan pertemanan,
  dibangkitkan, galat, pekerja, benturan, cakram, simpul, derau,
  menyegarkan, pembatasan, batasan
  dalam arti \textit{constraint} basis data, atau rentang dalam arti
  \textit{range} pada kueri dan penyimpanan. Judul slide dan
  judul seksi menulis istilah Inggris tegak, tanpa cetak miring. Imbuhan bahasa Indonesia pada
  istilah Inggris ditulis dengan tanda hubung, misalnya di-`\textit{commit}`
  dan di-`\textit{compress}`. Nama variabel dan fungsi di kode memakai istilah
  yang sama.
- Singkatan dieja penuh saat pertama muncul di bab itu, lalu dipakai singkatnya:
  "HyperText Transfer Protocol (HTTP)". Setiap singkatan baru wajib ditambahkan
  ke tabel **Daftar Singkatan** di `README.md`.
- Nama berkas, perintah, header, dan potongan kode inline memakai `\texttt{}`.
  Jalur berkas memakai `\berkas{}` (aman untuk garis bawah dan pemenggalan).
- Garis bawah di luar `lstlisting` wajib di-escape: `\texttt{time\_namelookup}`.

## 2. Struktur bab

Urutan seksi tetap, tanpa perkecualian:

1. `\section*{Tujuan Pembelajaran}` — tepat tiga butir, tiap butir berupa kata
   kerja terukur (Menjelaskan, Membedakan, Mengukur, Merancang), bukan
   "Memahami" atau "Mengetahui".
2. `\section{Pendahuluan}` — dua sampai tiga paragraf. Paragraf terakhir
   menyebut referensi utama bab tersebut dengan `\cite{}`.
3. Seksi materi, tiga sampai delapan buah.
4. `\section{Ringkasan}` — empat sampai lima paragraf naratif, bukan daftar
   berbutir. Paragraf terakhir menutup dengan pesan utama bab.
5. `\section{Latihan}` — lihat bagian 6 di bawah.

**Tidak ada seksi Praktikum.** Kegiatan praktikum diwujudkan sebagai Latihan.
Syarat penilaian yang dahulu ditulis di seksi Praktikum dipindahkan ke paragraf
pengantar Latihan.

## 3. Cara menjelaskan satu konsep

Pola tiga langkah, dipakai berulang:

1. **Pernyataan.** Satu paragraf berisi definisi dan cara kerjanya.
2. **Analogi sehari-hari.** Diambil dari dunia kampus atau kehidupan biasa:
   percetakan, warung dengan satu kasir, loket pembayaran uang kuliah, gudang
   cabang, buku alamat. Analogi ditulis satu paragraf, lalu ditinggalkan. Tidak
   dipaksakan sepanjang seksi.
3. **Contoh konkret.** Umumnya dua, ditulis sebagai `enumerate` dan diawali
   kalimat pengantar seperti "Dua contoh kasus nyata:" atau "Contoh untuk LCP:".
   Contohnya memakai angka: 5.000 baris, 900 milidetik, berkas 8 MB.

Transisi antarbagian memakai pertanyaan eksplisit yang langsung dijawab:

> Pertanyaan kemudian muncul: bagaimana bila banyak tab dibuka sekaligus?
> Pertanyaan berikutnya, siapa yang mengerjakan tahap-tahap tersebut.

Perbedaan yang sering tertukar dibereskan lewat seksi khusus, misalnya Renderer
lawan GPU, atau konkurensi lawan jumlah koneksi. Pola kalimatnya: "Dua hal pada
X sering tertukar. Pembagiannya begini."

Setiap konsekuensi ditulis eksplisit dan dihitung: "Aturan ini punya dua
konsekuensi praktis. Pertama, ... Kedua, ...".

## 4. Gambar dan tabel

- Tiap seksi materi punya minimal satu gambar TikZ atau satu tabel.
- Gambar dibuat dengan TikZ, bukan gambar raster, kecuali tangkapan layar.
- Palet tetap: `blue!8` untuk tahap biasa, `orange!12` untuk tahap yang
  ditekankan, `green!10` untuk hasil akhir, `praditagreen!15` untuk node
  induk, `red!22` dan `gray!35` untuk penanda masalah.
- Gaya panah tetap: `panah/.style={-{Stealth[length=2mm]}, thick}`.
- Font di dalam gambar `\scriptsize` atau `\footnotesize`, keterangan kecil
  memakai `{\tiny\mdseries ...}`.
- Tabel memakai `tabularx` selebar `\textwidth`, dengan `\hline` di **setiap**
  baris, termasuk sebelum baris judul dan sesudah baris terakhir.
- Tiap gambar dan tabel wajib punya `\caption` dan `\label`, dan wajib dirujuk
  dari naskah dengan `\ref{}` sebelum kemunculannya.
- Penamaan label: `fig:nama-pendek`, `tab:nama-pendek`, `lst:nama-pendek`.
  Tabel lembar isian latihan memakai pola `tab:latN-hasil`, contoh terisi
  memakai `tab:latN-contoh`, dan N mengikuti nomor latihannya.

## 5. Kode

- Bahasa kode untuk contoh sisi server dan skrip adalah **Python**. Kode sisi
  browser tetap JavaScript atau TypeScript, karena memang berjalan di browser.
  Perintah terminal memakai `bash`, kueri memakai SQL.

### 5.1 Aturan penulisan kode

Kode di modul ini dibaca lebih sering daripada dijalankan. Keterbacaan
didahulukan di atas keringkasan.

- **Tanpa fungsi bersarang.** Seluruh fungsi berada di tingkat modul. Bila
  sebuah fungsi butuh nilai dari pemanggilnya, nilai itu dikirim sebagai
  argumen, bila perlu lewat `functools.partial`, bukan lewat penutupan
  (*closure*). Aturan ini berlaku untuk semua bahasa, termasuk JavaScript dan
  TypeScript, dan termasuk `lambda` yang berisi logika.
- **Setiap modul, kelas, metode, dan fungsi wajib punya komentar yang
  berguna**, termasuk `__init__`. Docstring menjelaskan *mengapa* dan *apa
  akibatnya*, bukan mengulang nama fungsinya. Docstring modul menyebutkan
  kegunaan berkas dan cara menjalankannya. Fungsi JavaScript dan TypeScript
  memakai komentar JSDoc, sedangkan berkas HTML, YAML, dan shell diberi komentar
  kegunaan di baris pertama.
- **Nama menjelaskan isinya.** Nama modul, kelas, fungsi, variabel, dan
  konstanta dipilih agar pembaca baru langsung paham isinya tanpa membaca
  kodenya. Tanpa singkatan satu huruf: `koneksi` bukan `c`, `daftar_utas`
  bukan `u`, `stok_terbaca` bukan `s`. Nama fungsi berupa kata kerja, nama
  kelas dan variabel berupa kata benda, dan konstanta menyebut satuannya,
  misalnya `BATAS_WAKTU_DETIK`. Istilah yang janggal bila diterjemahkan tetap
  dipakai dalam bahasa Inggris, misalnya `pool_koneksi` dan `circuit_breaker`.
- **Kode diperiksa sebelum dikutip.** Skrip Python lolos `pyflakes`, dan
  berkas TypeScript lolos `tsc --noEmit --strict`.
- **Angka ajaib diberi nama** sebagai konstanta di puncak modul.
- Kueri SQL yang panjang diangkat menjadi konstanta bernama di puncak modul,
  sehingga alur fungsinya terbaca tanpa terpotong teks SQL.
- Baris maksimum 88 karakter, agar potongannya muat di halaman B5 tanpa
  terpenggal. Baris yang dikutip ke dalam listing naskah maksimum 78 karakter,
  karena listing bernomor baris di halaman B5 sudah terpenggal di atas itu.
- Bila nama di kode berubah dan nama itu ikut tercetak pada keluaran program,
  program dijalankan ulang, lalu keluaran dan angka di naskah serta slide
  diperbarui dari hasil yang baru.
- **Tanpa karakter tab.** Indentasi memakai dua spasi, termasuk pada berkas
  `.tex`. Pengaturan `listings` pun memakai `tabsize=2`.
- Komentar sebaris dipakai untuk menandai baris yang menjadi inti pelajaran,
  misalnya baris yang justru menimbulkan masalah yang sedang dibahas.
- Setiap `lstlisting` wajib punya `caption` dan `label`, dan captionnya
  menyebutkan lokasi berkasnya: `tersedia di \berkas{sources/chapterNN/nama}`.
- Kode di dalam naskah adalah salinan dari berkas di `sources/chapterNN/`,
  bukan kode yang hanya hidup di halaman cetak. Potongan yang ditampilkan boleh
  lebih pendek daripada berkasnya, tetapi tidak boleh berbeda isinya.
- Berkas di `sources/` diberi komentar berbahasa Indonesia di baris pertama,
  berisi kegunaan dan cara menjalankannya.
- Keluaran nyata perintah disertakan sebagai komentar di bawah perintahnya,
  diawali `# Keluarannya:`.
- Skrip Python dijalankan memakai venv lokal di `sources/.venv`.

## 6. Latihan

- Latihan diberi judul `\subsection*{Latihan N: Judul}`, bernomor urut dari 1
  dan **konsisten dengan penomoran pada caption tabelnya**.
- Tiap latihan berisi: kalimat pembuka yang menyebut apa yang dibuktikan,
  langkah kerja sebagai `enumerate`, listing perintah untuk menjalankannya,
  satu tabel contoh yang **sudah terisi**, dan satu tabel lembar isian kosong
  berisi `\dots`.
- Langkah kerja ditulis berurutan sesuai waktu pelaksanaan. Berkas tidak boleh
  dirujuk sebelum langkah yang menghasilkannya.
- Latihan ditutup dengan dua atau tiga pertanyaan analisis yang jawabannya
  menuntut pembacaan angka, bukan hafalan.
- Angka pada tabel contoh diambil apa adanya dari pengukuran nyata, **termasuk
  kejanggalannya**, lalu kejanggalan itu dijelaskan sebabnya di paragraf
  sesudahnya.
- Disebutkan bahwa hasil tiap mahasiswa akan berbeda, dan yang dilaporkan
  adalah pola perbandingannya, bukan angka persisnya.

## 7. Etika dan keamanan

Setiap kegiatan yang membebani sistem milik orang lain diberi peringatan
eksplisit di dekat perintahnya: pengukuran bersifat mengamati, bukan membebani;
uji beban hanya untuk sistem sendiri atau yang sudah berizin tertulis. Peringatan
yang sama diulang pada berkas skripnya.

## 8. Referensi

- Sumber primer lebih dahulu: RFC, spesifikasi resmi, dokumentasi vendor, buku
  acuan. Blog dan tutorial tidak dipakai sebagai rujukan utama.
- Entri ditambahkan ke `module/references.bib`, disertai `url` yang dapat
  dibuka.
- Sitasi dipasang pada kalimat yang benar-benar mengambil isinya, bukan
  ditumpuk di akhir paragraf.

## 9. Struktur repositori

- Naskah bab: `module/chapterNN.tex`, disatukan oleh
  `module/advanced-web-engineering.tex`.
- Berkas pendukung: `sources/chapterNN/`, satu direktori per bab, masing-masing
  punya `README.md` berisi tabel daftar berkas dan kegunaannya.
- Slide: `slides/sessionNN/sessionNN.tex`, memakai tema di `slides/theme/`.
  Isinya ringkasan bab, memakai gambar TikZ dan tabel yang sama dengan babnya.
  Angka pada slide wajib sama dengan angka pada naskah bab.
- Gambar bersama: `figures/`.
- Peta pertemuan, topik penelitian, dan daftar singkatan: `README.md` di akar.
