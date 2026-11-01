# Sumber Bab 13

Dua bagian yang berjalan bersama: satu fitur *real-time* yang mengirim
peristiwa ke klien dengan tiga cara, dan satu alur asinkron yang memakai
antrean, *worker*, serta *webhook*. Seluruhnya Python pustaka standar,
termasuk WebSocket-nya.

| File | Kegunaan |
| --- | --- |
| `aplikasi.py` | Server peristiwa di port 8100: `POST /kirim`, `GET /polling`, `GET /sse`, `GET /riwayat` |
| `websocket_sederhana.py` | Jabat tangan dan frame teks WebSocket, dipakai server maupun alat ukur |
| `websocket.py` | Server WebSocket di port 8101 yang mengikuti aliran SSE aplikasi lalu menyiarkannya |
| `ukur-transport.py` | Membandingkan *polling*, SSE, dan WebSocket: keterlambatan, byte, dan jumlah permintaan |
| `antrean.py` | Antrean satu file dengan *visibility timeout*, *backoff* berlipat, dan buku diproses |
| `webhook.py` | Penerima *webhook* di port 8102 yang sengaja menolak dua percobaan pertama satu jenis pekerjaan |
| `worker.py` | *Worker* idempoten: memeriksa duplikat, mengirim *webhook*, lalu meng-*ack* |
| `ukur-antrean.py` | Menjalankan satu daur antrean dari ujung ke ujung, lalu mencetak percobaan dan pengirimannya |

File `antrean.json` dibuat sendiri oleh `antrean.py` dan tidak dilacak git,
karena isinya hasil percobaan, bukan sumber.

## Menjalankan

```bash
cd sources/chapter13
python3 aplikasi.py &
python3 webhook.py &
python3 websocket.py &

python3 ukur-transport.py
python3 ukur-antrean.py

curl -s -X POST http://127.0.0.1:8100/kirim \
  -H 'Content-Type: application/json' -d '{"pesan":"uji"}'
curl -s "http://127.0.0.1:8100/polling?sejak=0"
curl -sN http://127.0.0.1:8100/sse | head -4
```

`websocket.py` dinyalakan sesudah `aplikasi.py`, karena ia mengikuti aliran
SSE aplikasi. Bila aplikasinya dinyalakan ulang, `websocket.py` menyambung
sendiri sesudah satu detik.

Untuk menjalankan *worker* sebagai proses yang hidup terus, bukan lewat alat
ukur:

```bash
python3 worker.py
```

## Catatan etika

Seluruh alat ukur di direktori ini hanya diarahkan ke layanan yang berjalan
di komputer sendiri di 127.0.0.1, dan sifatnya mengamati, bukan membebani.
Alamat `/webhook` sengaja menolak dua percobaan pertama untuk jenis
`gagal-dua-kali`, dan penolakan itu satu-satunya kegagalan yang dibuat
sengaja di direktori ini.
