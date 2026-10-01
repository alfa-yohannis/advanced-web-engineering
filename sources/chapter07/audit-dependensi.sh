#!/usr/bin/env bash
# Memeriksa dependensi proyek terhadap basis data kerentanan yang diumumkan.
# Pemeriksaan ini hanya membaca daftar paket yang terpasang di komputer
# sendiri, lalu mencocokkannya dengan pengumuman resmi. Tidak ada sistem lain
# yang disentuh.
#
# Pemakaian (dari sources/chapter07):
#   ./audit-dependensi.sh

set -uo pipefail

# Venv diaktifkan lebih dahulu, agar pip-audit membaca jalur venv yang sama
# dengan yang dipakai menjalankannya.
source ../.venv/bin/activate

echo "=== Paket Python yang terpasang"
pip list 2>/dev/null | tail -n +3 | wc -l

echo "=== Hasil pemeriksaan paket Python"
python -m pip_audit --progress-spinner off 2>&1 | tail -20

echo
echo "=== Paket Node pada Bab 6"
if [ -d ../chapter06/node_modules ]; then
  (cd ../chapter06 && npm audit --omit=dev 2>&1 | tail -10)
else
  echo "Direktori ../chapter06/node_modules belum ada, lewati."
fi
