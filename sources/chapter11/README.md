# Sumber Bab 11

Satu aplikasi katalog dengan tiga varian halaman: dua cara hidrasi dan satu
*application shell* beserta *routing*-nya. Seluruhnya berjalan dengan Python
pustaka standar, dan pengukurannya memakai Chrome tanpa jendela.

| File | Kegunaan |
| --- | --- |
| `komponen.py` | Komponen halaman sebagai fungsi, token *design system*, dan penyusun *state* kedua varian |
| `aplikasi.py` | Aplikasi di port 8080: `/penuh`, `/selektif`, `/kerangka/...`, `/fragmen/...`, `/api/katalog`, `/aset/<file>` |
| `statis/hidrasi-penuh.js` | Menghidupkan seluruh komponen yang bertanda `data-komponen` |
| `statis/hidrasi-selektif.js` | Menghidupkan hanya dua bagian yang bertanda `data-pulau` |
| `statis/rute.js` | Router di sisi browser untuk kerangka, beserta batas *error*-nya |
| `pengukur.py` | Alat ukur bersama: mengambil satu alamat, dan membuka halaman dengan Chrome tanpa jendela |
| `ukur-hidrasi.py` | Mengukur biaya hidrasi kedua varian, lima kali tiap varian |
| `ukur-rute.py` | Membandingkan ukuran dokumen penuh dengan ukuran fragmen untuk tujuan yang sama |
| `ukur-tanpa-js.py` | Menghitung isi yang tetap tampil ketika skripnya diblokir |

Besar halaman diatur lewat *environment* `JUMLAH_BUKU`, karena biaya hidrasi
penuh tumbuh mengikuti jumlah komponen, sedangkan hidrasi selektif tidak.

## Menjalankan

```bash
cd sources/chapter11
python3 aplikasi.py &
python3 ukur-hidrasi.py
python3 ukur-rute.py
python3 ukur-tanpa-js.py

curl -s http://127.0.0.1:8080/penuh | grep -c 'data-komponen='
curl -s http://127.0.0.1:8080/selektif | grep -c 'data-pulau='
curl -s http://127.0.0.1:8080/fragmen/buku/3
```

Mengulang pengukuran pada halaman yang lebih besar cukup dengan satu
*environment*:

```bash
JUMLAH_BUKU=2000 python3 aplikasi.py &
python3 ukur-hidrasi.py
```

Di browser, `http://127.0.0.1:8080/kerangka/katalog` memperlihatkan
*routing*-nya: judul dan navigasi tidak dimuat ulang, dan tautan "Bagian yang
gagal" memperlihatkan batas *error* menahan satu wilayah yang gagal.
Menambahkan `?blokir_skrip=1` pada alamat mana pun membuat server memasang
CSP penolak skrip, sehingga halaman terlihat seperti ketika file JavaScript
gagal diunduh.

## Catatan etika

Seluruh alat ukur di direktori ini hanya diarahkan ke aplikasi yang berjalan
di komputer sendiri di 127.0.0.1, dan sifatnya mengamati, bukan membebani.
Alamat `/kerangka/gagal` sengaja menjawab 500, dan hanya ada untuk melihat
batas *error* bekerja.
