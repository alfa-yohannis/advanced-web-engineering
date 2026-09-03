#!/usr/bin/env python3
"""Meringkas berkas HAR hasil ekspor panel Network.

HAR (HTTP Archive) adalah format rekaman aktivitas jaringan browser dalam
bentuk JSON. Isinya seluruh permintaan beserta waktu, header, ukuran, protokol,
dan penanda koneksinya. Rekaman ini ikut memuat header, sehingga cookie dan
token autentikasi dapat ikut tersimpan. Jangan dibagikan sembarangan.

Berkas HAR diperoleh dari DevTools, panel Network, klik kanan pada daftar
permintaan, lalu pilih "Save all as HAR with content".

Skrip ini menghitung sendiri jumlah permintaan, jumlah koneksi, protokol, dan
waktu, sehingga tidak perlu dihitung satu per satu dari layar.

Argumen kedua boleh berupa dua hal:
  * potongan nama host, misalnya www.pradita.ac.id
  * nama berkas berisi daftar alamat aset, satu per baris, misalnya aset.txt

Bentuk kedua dipakai bila hasilnya hendak dibandingkan dengan pengukuran
curl, agar kumpulan aset yang dihitung benar-benar sama.

Pemakaian:
    ./ringkas-har.py rekaman.har [saringan_host | daftar_aset.txt]
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime


def waktu(teks):
    return datetime.fromisoformat(teks.replace("Z", "+00:00"))


def main():
    if len(sys.argv) < 2:
        sys.exit("Pemakaian: ./ringkas-har.py rekaman.har [saringan_host]")

    berkas = sys.argv[1]
    saringan = sys.argv[2] if len(sys.argv) > 2 else ""

    with open(berkas, encoding="utf-8") as f:
        entri = json.load(f)["log"]["entries"]

    if saringan and os.path.isfile(saringan):
        with open(saringan, encoding="utf-8") as f:
            daftar = {baris.strip() for baris in f if baris.strip()}
        entri = [e for e in entri if e["request"]["url"] in daftar]
        print(f"Disaring memakai daftar {saringan}, {len(daftar)} alamat.")
        hilang = daftar - {e["request"]["url"] for e in entri}
        if hilang:
            print(f"Tidak ditemukan di rekaman: {len(hilang)} alamat.")
    elif saringan:
        entri = [e for e in entri if saringan in e["request"]["url"]]

    if not entri:
        sys.exit("Tidak ada permintaan yang cocok.")

    protokol = Counter(e["response"].get("httpVersion", "?") for e in entri)
    koneksi = {e.get("connection", "") for e in entri if e.get("connection")}
    dari_cache = sum(1 for e in entri if e["response"].get("_transferSize", 1) == 0)

    mulai = min(waktu(e["startedDateTime"]) for e in entri)
    selesai = max(
        waktu(e["startedDateTime"]).timestamp() + e["time"] / 1000 for e in entri
    )
    total = selesai - mulai.timestamp()

    print(f"Jumlah permintaan : {len(entri)}")
    print(f"Diambil dari cache: {dari_cache}")
    print(f"Jumlah koneksi    : {len(koneksi) if koneksi else 'tidak dicatat HAR'}")
    for nama, jumlah in protokol.most_common():
        print(f"Protokol          : {nama} pada {jumlah} permintaan")
    print(f"Rentang waktu     : {total:.2f} detik")


if __name__ == "__main__":
    main()
