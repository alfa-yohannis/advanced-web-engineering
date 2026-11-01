# Sumber Bab 12

Satu API katalog yang seluruhnya diturunkan dari kontrak OpenAPI: tipe klien
di-*generate* dari kontrak, isi permintaan divalidasi dengan skema dari
kontrak yang sama, dan kompatibilitas antarversi diuji dengan membandingkan
kedua kontrak. Aplikasinya memakai Python pustaka standar ditambah
`jsonschema`.

| File | Kegunaan |
| --- | --- |
| `kontrak.json` | Kontrak OpenAPI 3.1 versi 1: dua jalur, lima skema, *error* bentuk Problem Details |
| `kontrak-v2.json` | Kontrak versi 2, dengan satu perubahan aman dan tiga perubahan yang merusak klien lama |
| `buat_tipe.py` | Meng-*generate* tipe TypeScript dan tanda tangan klien dari kontrak |
| `tipe-katalog.ts` | Hasil *generate* dari `kontrak.json`, jangan diubah tangan |
| `tipe-katalog-v2.ts` | Hasil *generate* dari `kontrak-v2.json` |
| `pakai-tipe.ts` | Contoh pemakaian tipe hasil *generate*, lolos `tsc --strict` |
| `pakai-tipe-salah.ts` | Sengaja salah: memakai field versi 1 pada tipe versi 2 |
| `aplikasi.py` | API di port 8090: dua versi, *pagination*, *filtering*, idempotensi, validasi di batas |
| `gateway.py` | *Gateway* di port 8091: *rate limiting* token bucket, lalu meneruskan |
| `uji-kontrak.py` | Memvalidasi jawaban server, isi permintaan, dan janji idempotensinya |
| `uji-kompatibilitas.py` | Memisahkan perubahan kontrak yang aman dari yang merusak, lalu mengujinya pada server |
| `ukur-gateway.py` | Mengukur lonjakan permintaan, penolakan 429, dan pengisian ulang embernya |

## Menjalankan

```bash
cd sources/chapter12
python3 aplikasi.py &
python3 gateway.py &

python3 buat_tipe.py kontrak.json tipe-katalog.ts
python3 buat_tipe.py kontrak-v2.json tipe-katalog-v2.ts
python3 uji-kontrak.py
python3 uji-kompatibilitas.py
python3 ukur-gateway.py

curl -s "http://127.0.0.1:8090/v1/buku?per_halaman=2"
curl -s "http://127.0.0.1:8090/v2/buku?per_halaman=2"
curl -s http://127.0.0.1:8090/openapi.json | head -5
```

Nomor pesanan pada keluaran `uji-kontrak.py` dihitung dari aplikasi yang baru
menyala. Jalankan ulang aplikasinya sebelum mengukur bila nomornya ingin sama
dengan yang tercetak di naskah bab.

## Pemeriksaan tipe

Pemeriksaan tipe memakai `tsc` yang sudah terpasang di Bab 6, sehingga Bab 12
tidak menambah pemasangan npm:

```bash
cd sources/chapter12
../chapter06/node_modules/.bin/tsc --noEmit -p tsconfig.json
# Keluarannya: tanpa kesalahan

../chapter06/node_modules/.bin/tsc --noEmit --strict --ignoreConfig \
  pakai-tipe-salah.ts
# Keluarannya:
# pakai-tipe-salah.ts(15,15): error TS2339: Property 'harga' does not exist
# on type 'Buku'.
```

File `pakai-tipe-salah.ts` sengaja dikeluarkan dari `tsconfig.json`, karena
kegagalannya memang hasil yang diinginkan.

## Catatan etika

Seluruh alat ukur di direktori ini hanya diarahkan ke aplikasi dan *gateway*
yang berjalan di komputer sendiri di 127.0.0.1, dan sifatnya mengamati, bukan
membebani. Lonjakan 30 permintaan pada `ukur-gateway.py` dipakai untuk
melihat batas lajunya bekerja, bukan untuk menguji ketahanan sistem lain.
