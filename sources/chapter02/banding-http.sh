#!/usr/bin/env bash
# Memisahkan dua hal yang sering tercampur saat membandingkan versi HTTP:
#
#   konkurensi : berapa permintaan berjalan bersamaan
#   koneksi    : berapa koneksi yang dibuka untuk mencapai konkurensi itu
#
# Empat skenario dijalankan pada daftar aset yang sama.
#   1. HTTP/1.1 berurutan, tiap permintaan proses terpisah, koneksi tidak
#      dipakai ulang
#   2. HTTP/1.1 berurutan, satu proses, koneksi dipakai ulang (keep-alive)
#   3. HTTP/1.1 serentak
#   4. HTTP/2 serentak
#
# Pemakaian: ./banding-http.sh https://www.pradita.ac.id/ [jumlah_aset] [sendiri|semua]

sumber="${1:?alamat halaman atau berkas daftar aset wajib diisi}"
jumlah="${2:-10}"
saring="${3:-sendiri}"

if [[ -f "$sumber" ]]; then
  cp "$sumber" aset.txt
  echo "Memakai daftar aset dari $sumber, $(wc -l < aset.txt) alamat."
else
  ./kumpulkan-aset.sh "$sumber" "$jumlah" "$saring"
fi

echo
echo "Host aset dan versi HTTP yang dilayaninya:"
for host in $(awk -F/ '{ print $3 }' aset.txt | sort -u); do
  versi=$(curl -s -o /dev/null -w '%{http_version}' --max-time 20 "https://$host/")
  jml=$(grep -c "://$host/" aset.txt)
  printf "  %-45s HTTP/%-5s %2d aset\n" "$host" "$versi" "$jml"
done

# Argumen: label, konkurensi, lalu perintahnya.
ukur() {
  local label="$1" konkurensi="$2"; shift 2
  local mulai selesai koneksi
  mulai=$(date +%s.%N)
  koneksi=$("$@" | awk '{ n += $1 } END { print n }')
  selesai=$(date +%s.%N)
  awk -v l="$label" -v c="$konkurensi" -v a="$mulai" -v b="$selesai" -v k="$koneksi" \
    'BEGIN { printf "  %-34s %-10s %2s koneksi %8.2f detik\n", l, c, k, b - a }'
}

daftar_o=$(awk '{ print "-o /dev/null " $0 }' aset.txt)
n=$(wc -l < aset.txt)

echo
printf "  %-34s %-10s %-11s %s\n" "Skenario" "Konkurensi" "Koneksi" "Waktu"
ukur "1. HTTP/1.1 berurutan, koneksi baru" "1" \
  xargs -a aset.txt -I{} curl --http1.1 -s -o /dev/null -w '%{num_connects}\n' {}
ukur "2. HTTP/1.1 berurutan, keep-alive" "1" \
  curl --http1.1 -s -w '%{num_connects}\n' $daftar_o
ukur "3. HTTP/1.1 serentak" "$n" \
  curl --http1.1 --parallel -s -w '%{num_connects}\n' $daftar_o
ukur "4. HTTP/2 serentak" "$n" \
  curl --http2 --parallel -s -w '%{num_connects}\n' $daftar_o
