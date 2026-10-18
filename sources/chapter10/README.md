# Sumber Bab 10

Aplikasi pesanan dengan dua cara mengenali pengguna, aturan hak akses, dan
isolasi *tenant*. Seluruhnya berjalan dengan Python pustaka standar: tanpa
basis data, tanpa container, dan tanpa pustaka tambahan.

| File | Kegunaan |
| --- | --- |
| `token_sederhana.py` | Pembuat dan pemeriksa token bertanda tangan HMAC-SHA256, bentuknya seperti JWT |
| `kebijakan.py` | Aturan hak akses: izin per peran untuk RBAC, dan aturan pemilik serta *tenant* untuk ABAC |
| `aplikasi.py` | Aplikasi di port 8070: masuk lewat sesi atau token, daftar pesanan, rincian, laporan, penyegaran token, dan keluar |
| `pengguna.json` | Empat pengguna pada dua *tenant* beserta pesanannya |
| `ukur-akses.py` | Menjalankan matriks empat pengguna lawan empat alamat, lalu mencetak keputusannya |

Nama file `token_sederhana.py` sengaja bukan `token.py`, karena nama itu
sudah dipakai modul bawaan Python.

## Menjalankan

```bash
cd sources/chapter10
python3 aplikasi.py &
python3 ukur-akses.py

curl -s -X POST "http://127.0.0.1:8070/masuk?cara=token&nama=budi&sandi=budi123"
curl -s -X POST "http://127.0.0.1:8070/masuk?cara=sesi&nama=budi&sandi=budi123" -D -
```

Umur *access token* sengaja hanya lima detik agar kedaluwarsanya terlihat
dalam satu sesi latihan. Pada sistem sungguhan satuannya menit untuk *access
token* dan hari untuk *refresh token*.

## Catatan etika

Kata sandi pada `pengguna.json` hanya untuk latihan di komputer sendiri, dan
kuncinya dibaca dari *environment* `KUNCI_TOKEN`. Seluruh alat ukur di
direktori ini hanya diarahkan ke aplikasi yang berjalan di komputer sendiri.
