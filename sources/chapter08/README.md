# Sumber Bab 08

Satu halaman katalog yang disajikan dengan lima arsitektur berbeda, beserta
alat ukurnya. Seluruhnya berjalan dengan Python pustaka standar: tanpa basis
data, tanpa container, dan tanpa npm.

| File | Kegunaan |
| --- | --- |
| `katalog.py` | Data katalog dan perakit HTML yang dipakai bersama kelima varian |
| `bangun-statis.py` | Langkah *build* varian SSG: merakit halaman sekali, lalu menyimpannya sebagai file |
| `aplikasi.py` | Server yang melayani kelima varian di port 8040 |
| `ukur-varian.py` | Mengukur byte, jumlah permintaan, dan waktu tiap varian |
| `statis/spa.js` | Skrip varian SPA, menggambar seluruh katalog di browser |
| `statis/pulau.js` | Skrip varian islands, menghidupkan satu kotak penyaring saja |
| `statis/katalog-ssg.html` | Hasil *build*, dibuat `bangun-statis.py` |

## Menjalankan

```bash
cd sources/chapter08
python3 bangun-statis.py
python3 aplikasi.py &
python3 ukur-varian.py
```

Alamat tiap varian: `/ssg`, `/isr`, `/ssr`, `/islands`, dan `/spa`. Data JSON
untuk varian SPA dan islands ada di `/api/katalog`.

## Catatan etika

Alat ukur di direktori ini hanya diarahkan ke aplikasi yang berjalan di
komputer sendiri, dan bebannya setara satu pengunjung membuka halaman. Tidak
ada sistem milik orang lain yang disentuh.
