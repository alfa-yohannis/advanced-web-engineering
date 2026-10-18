# Sumber Bab 09

Dua versi layanan katalog di belakang satu *reverse proxy*, beserta
instrumentasi dan alat ukurnya. Seluruhnya berjalan dengan Python pustaka
standar; Docker hanya dipakai pada bagian *container*.

| File | Kegunaan |
| --- | --- |
| `aplikasi.py` | Layanan katalog yang sudah diinstrumentasi: log JSON, metrik di `/metrics`, dan *trace id* dari header `traceparent` |
| `proxy.py` | *Reverse proxy* yang membagi permintaan ke dua versi menurut bobot, sekaligus membuat *trace id* |
| `rilis.json` | Pembagian rilis: bobot persen untuk versi kedua, beserta alamat kedua versi |
| `ukur-rilis.py` | Mengukur pembagian yang benar-benar terjadi, dibaca dari header `X-Dilayani` |
| `metrik.py` | Pembaca metrik format Prometheus, dipakai papan dan alarm |
| `papan.py` | Papan operasional: permintaan, kegagalan, rata-rata, dan p95 tiap versi |
| `slo.json` | Tujuan layanan: ketersediaan minimum dan p95 maksimum |
| `alarm.py` | Menilai layanan terhadap SLO, keluar dengan status 1 bila ada yang dilanggar |
| `Dockerfile` | Image layanan, hanya menyalin satu file dan tanpa dependensi |
| `docker-compose.yml` | Dua versi sekaligus dari image yang sama, berbeda hanya di *environment* |
| `ci-contoh.yml` | Contoh *pipeline* CI/CD, bahan bacaan dan bukan *pipeline* yang aktif |

## Menjalankan

```bash
cd sources/chapter09
VERSI=biru PORT=8061 python3 aplikasi.py &
VERSI=hijau PORT=8062 python3 aplikasi.py &
python3 proxy.py &
python3 ukur-rilis.py 200
python3 papan.py
python3 alarm.py
```

Rilis diubah dengan menyunting `bobot_persen_kedua` di `rilis.json`: 0 berarti
seluruh permintaan ke versi pertama, 100 berarti seluruhnya ke versi kedua,
dan di antaranya berarti *canary*. Proxy membaca file itu pada tiap
permintaan, sehingga perubahannya langsung berlaku.

Bagian *container* dijalankan terpisah:

```bash
docker build -t awe9-layanan .
docker compose up -d --build
docker compose down
```

## Catatan etika

Seluruh alat ukur di direktori ini hanya diarahkan ke layanan yang berjalan di
komputer sendiri, dengan beban setara satu pengguna mengirim permintaan
berurutan. Tidak ada sistem milik orang lain yang disentuh.
