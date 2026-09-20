#!/usr/bin/env bash
# Mengisi basis data Bab 5 dengan skema, data uji, dan indeks milik Bab 3.
# Pemakaian (dari sources/chapter05, setelah docker compose up -d):
#   ./siapkan-data.sh

set -euo pipefail

DSN="postgresql://admin:admin123@localhost/toko"
DIREKTORI_BAB3="../chapter03"

# Container yang baru menyala sempat menjalankan server sementara yang hanya
# mendengar lewat soket lokal. Pemeriksaan lewat TCP menunggu server yang
# sesungguhnya, bukan server sementara tersebut.
until docker compose exec -T db psql "$DSN" -c "SELECT 1" > /dev/null 2>&1; do
  sleep 1
done

for berkas in 01-skema.sql 02-data-uji.sql 04-indeks.sql; do
  echo "=== $berkas"
  docker compose exec -T db psql -q "$DSN" < "$DIREKTORI_BAB3/$berkas"
done
