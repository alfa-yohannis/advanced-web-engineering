#!/usr/bin/env bash
# Mengukur durasi tiap tahap pembukaan koneksi.
# Pemakaian: ./ukur-koneksi.sh https://www.pradita.ac.id/ [jumlah_ulangan]

url="${1:?alamat wajib diisi}"
ulangan="${2:-5}"

format="%{time_namelookup} %{time_connect} %{time_appconnect}"
format+=" %{time_starttransfer} %{time_total}\n"

printf "%-10s %-10s %-10s %-14s %-10s\n" \
  "DNS" "TCP" "TLS" "TungguServer" "Total"
for ((i = 1; i <= ulangan; i++)); do
  curl -o /dev/null -s -w "$format" --max-time 30 "$url" |
    awk '{
      printf "%-10.0f %-10.0f %-10.0f %-14.0f %-10.0f\n",
        $1*1000, ($2-$1)*1000, ($3-$2)*1000, ($4-$3)*1000, $5*1000
    }'
  sleep 1
done
