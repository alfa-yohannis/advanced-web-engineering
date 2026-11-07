#!/usr/bin/env bash
# Mengumpulkan alamat aset sebuah halaman, lalu menyimpannya ke aset.txt.
# Urutannya mengikuti urutan kemunculan di HTML, bukan urutan alfabet, agar
# aset yang benar-benar dipakai lebih dahulu ikut terambil.
#
# Catatan: aset sebuah halaman sering dititipkan di domain lain, misalnya CDN
# atau penyimpanan objek. Karena itu daftar yang dihasilkan dapat memuat host
# selain host halaman yang diminta.
#
# Argumen ketiga menentukan penyaringan host:
#   sendiri : hanya aset dari host halaman itu sendiri, ini nilai bawaan
#   semua   : seluruh aset, termasuk yang dititipkan di CDN atau S3
#
# Pemakaian: ./kumpulkan-aset.sh https://www.pradita.ac.id/ [jumlah] [sendiri|semua]

url="${1:?alamat wajib diisi}"
jumlah="${2:-10}"
saring="${3:-sendiri}"

host=$(printf '%s' "$url" | awk -F/ '{ print $3 }')

daftar=$(curl -sL --max-time 30 "$url" |
  grep -oE '(href|src)="https?://[^"]+\.(css|js|png|jpg|jpeg|webp)[^"]*"' |
  sed -E 's/^(href|src)="//; s/"$//' |
  awk '!terlihat[$0]++')

if [[ "$saring" == "sendiri" ]]; then
  daftar=$(printf '%s\n' "$daftar" | grep "://$host/")
fi

printf '%s\n' "$daftar" | head -n "$jumlah" > aset.txt

echo "Tersimpan $(wc -l < aset.txt) alamat aset ke aset.txt"
echo "Sebaran host:"
awk -F/ '{ print "  " $3 }' aset.txt | sort | uniq -c | sort -rn
