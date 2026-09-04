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
