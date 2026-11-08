# Sumber Bab 14

Bahan latihan evolusi arsitektur: penskalaan horizontal sampai bottleneck-nya
pindah, biaya memecah satu proses menjadi layanan, dua cara mempartisi data,
dan rencana kapasitas untuk beban 100 kali lipat. Ditambah tiga eksperimen
teknologi *emerging*: mode offline Progressive Web App, cold start fungsi
serverless, dan fitur berbantuan LLM. Seluruhnya Python pustaka standar,
tanpa Docker dan tanpa npm. Pengukuran mode offline membutuhkan Google Chrome
atau Chromium.

| File | Kegunaan |
| --- | --- |
| `basis_data_tiruan.py` | Basis data tiruan berkapasitas tetap di port 8119, yaitu komponen bersama yang tidak ikut bertambah ketika replika ditambah |
| `layanan.py` | Satu replika layanan rekomendasi tanpa *state*, port-nya dari *environment* `PORT` |
| `penyeimbang.py` | Penyeimbang beban *round robin* di port 8110, daftar replikanya dari *environment* `REPLIKA` |
| `pengukur.py` | Alat ukur bersama: menyalakan proses, menunggu port, mematikan proses, dan menghitung persentil |
| `ukur-skala.py` | Mengukur permintaan per detik, p50, p95, dan efisiensi pada 1, 2, 4, dan 8 replika |
| `panggilan-jaringan.py` | Membandingkan panggilan fungsi di dalam proses dengan panggilan HTTP ke proses lain |
| `partisi.py` | Membandingkan modulo dengan *consistent hashing*: kunci yang pindah dan beban node terberat |
| `rencana.json` | Angka masukan rencana kapasitas: beban tiap layanan, kapasitas hasil Latihan 1, dan asumsi biaya |
| `rencana-kapasitas.py` | Menghitung replika, replika baca, shard, koneksi, dan biaya bulanan untuk beban berlipat |
| `aplikasi.py` | Katalog sebagai Progressive Web App di port 8120, beserta penghitung permintaan di `/statistik` |
| `statis/index.html`, `statis/aplikasi.js` | Kerangka halaman dan pemuat katalognya |
| `statis/sw.js` | *Service worker*: kerangka dari *cache* lebih dahulu, data dari jaringan lebih dahulu |
| `statis/manifest.webmanifest`, `statis/ikon.svg` | Manifest aplikasi beserta ikonnya |
| `chrome_pipa.py` | Mengendalikan Chrome tanpa jendela lewat Chrome DevTools Protocol di atas pipa, tanpa pustaka tambahan |
| `ukur-offline.py` | Empat kunjungan dengan Chrome: dua ketika server hidup, dua ketika server *down* |
| `fungsi.py` | Fungsi serverless tiruan yang menghitung ongkos kirim dari satu peristiwa |
| `ukur-cold-start.py` | Membandingkan panggilan *warm*, *cold start*, dan *cold start* dengan dependensi |
| `model-tiruan.py` | Model bahasa tiruan di port 8122: waktu tokennya ditetapkan, jumlah tokennya dilaporkan |
| `asisten.py` | Fitur berbantuan LLM di port 8121: memegang kunci API, mengalirkan jawaban, dan *cache* kecocokan persis |
| `ukur-llm.py` | Mengukur token pertama, jawaban selesai, token yang dibayar, dan *cache* dari sisi browser |

Port yang dipakai: 8110 untuk penyeimbang, 8111 sampai 8118 untuk replika,
8119 untuk basis data tiruan, 8120 untuk Progressive Web App, 8121 untuk
asisten, dan 8122 untuk model tiruan.

## Menjalankan

Skrip pengukur menyalakan dan mematikan sendiri proses yang diukurnya,
kecuali bagian LLM:

```bash
cd sources/chapter14
python3 ukur-skala.py
JUMLAH_KONEKSI=16 python3 ukur-skala.py
python3 panggilan-jaringan.py
python3 partisi.py
python3 rencana-kapasitas.py
python3 ukur-offline.py
python3 ukur-cold-start.py
```

Bagian LLM dinyalakan manual, karena kunci API hanya diberikan kepada kedua
server, tidak kepada alat ukur yang berperan sebagai browser:

```bash
KUNCI_MODEL=kunci-latihan python3 model-tiruan.py &
KUNCI_MODEL=kunci-latihan python3 asisten.py &
python3 ukur-llm.py
```

Cache asisten hidup selama prosesnya hidup. Nyalakan ulang `asisten.py`
sebelum mengukur ulang, agar dua skenario pertama kembali menjadi MISS.

Untuk melihat mode offline dengan mata sendiri, nyalakan `python3 aplikasi.py`,
buka `http://127.0.0.1:8120/` di Chrome dua kali, matikan aplikasinya, lalu
muat ulang halamannya. Bagian Application di DevTools memperlihatkan
*service worker* dan isi *cache*-nya.

`chrome_pipa.py` memindahkan pipa ke file descriptor 3 dan 4 sebelum Chrome
dijalankan, sehingga hanya berjalan di Linux dan macOS. Di Windows, jalankan
dari WSL.

## Catatan etika

`ukur-skala.py` sengaja membebani, tetapi yang dibebaninya hanya proses yang
dinyalakannya sendiri di 127.0.0.1. Seluruh alat ukur lain bersifat mengamati.
Tidak ada satu pun skrip di direktori ini yang boleh diarahkan ke sistem milik
orang lain. Angka *throughput* bergantung pada jumlah *core* dan batas daya
komputer, sehingga hasil tiap mahasiswa akan berbeda, sedangkan pola
perbandingannya akan sama.
