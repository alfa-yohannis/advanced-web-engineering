# Sumber Bab 2: Browser, HTTP, dan Network Internals

| Berkas | Kegunaan |
| --- | --- |
| `ukur-koneksi.sh` | Mengukur durasi DNS, TCP, TLS, tunggu server, dan unduh isi |
| `kumpulkan-aset.sh` | Mengumpulkan alamat aset sebuah halaman ke `aset.txt` |
| `banding-http.sh` | Membandingkan empat skenario pengambilan aset, memisahkan konkurensi dari jumlah koneksi |
| `urutan-event-loop.js` | Membuktikan urutan macrotask dan microtask |
| `tugas-berat.ts` | Contoh long task yang menahan main thread |
| `preconnect.html` | Contoh preconnect dan dns-prefetch |
| `defer-async.html` | Perbandingan script biasa, defer, dan async |
| `skrip-beban.js` | Skrip k6, hanya untuk sistem sendiri atau yang sudah berizin |
| `rekam-har.py` | Merekam aktivitas jaringan lewat Chrome tanpa antarmuka, hasilnya berkas HAR |
| `ringkas-har.py` | Meringkas rekaman HAR dari panel Network, menghitung permintaan, koneksi, protokol, dan waktu |

Seluruh skrip dijalankan dari direktori ini.

## Menjalankan skrip Python

`rekam-har.py` membutuhkan Google Chrome dan pustaka `websockets`, sedangkan
`ringkas-har.py` hanya memakai pustaka standar. Keduanya memakai venv bersama
di `sources/.venv`. Bila belum ada, buat sekali saja dari direktori ini:

```bash
python3 -m venv ../.venv
../.venv/bin/pip install websockets
```

Selanjutnya, dari direktori ini:

```bash
source ../.venv/bin/activate
./rekam-har.py https://www.pradita.ac.id/ rekaman.har
./ringkas-har.py rekaman.har www.pradita.ac.id
```
