"""Pembuat dan pemeriksa token bertanda tangan, bentuknya seperti JWT.

Token ditulis sendiri dengan pustaka standar agar isinya terlihat utuh:
bagian header, bagian isi, dan tanda tangan, masing-masing dikodekan
base64url lalu disambung dengan titik. Pustaka sungguhan dipakai di sistem
produksi, tetapi yang perlu dipahami lebih dahulu adalah bentuknya.

Tanda tangan memakai HMAC-SHA256, sehingga siapa pun dapat membaca isi
token, tetapi hanya pemegang kunci yang dapat membuat token baru. Karena
itu token tidak pernah diisi data rahasia.

Nama filenya sengaja bukan token.py, karena nama itu sudah dipakai modul
bawaan Python, dan menimpanya membuat impor lain ikut salah sasaran.

Pemakaian (dari sources/chapter10):
    python3 -c "import token_sederhana as t; print(t.buat({'sub': 'ani'}, 60))"
"""

import base64
import hashlib
import hmac
import json
import os
import time

# Kunci dibaca dari environment, sama seperti aturan Bab 7. Nilai cadangan
# hanya layak untuk latihan di komputer sendiri.
KUNCI = os.environ.get("KUNCI_TOKEN", "kunci-latihan-bab-10").encode()
ALGORITMA = "HS256"


def kode_base64url(data_byte):
  """Mengodekan byte menjadi base64url tanpa tanda sama dengan di ujungnya."""
  return base64.urlsafe_b64encode(data_byte).rstrip(b"=").decode()


def dekode_base64url(teks):
  """Mengembalikan teks base64url menjadi byte, dengan padding dipulihkan."""
  sisa = len(teks) % 4
  if sisa:
    teks += "=" * (4 - sisa)
  return base64.urlsafe_b64decode(teks)


def tanda_tangani(bagian_awal):
  """Menandatangani dua bagian pertama token dengan HMAC-SHA256."""
  tanda = hmac.new(KUNCI, bagian_awal.encode(), hashlib.sha256).digest()
  return kode_base64url(tanda)


def buat(isi, umur_detik):
  """Membuat satu token bertanda tangan yang berlaku selama umur tertentu.

  Waktu kedaluwarsa ikut masuk ke dalam isinya, sehingga pemeriksa tidak
  perlu menyimpan apa pun untuk tahu token sudah lewat atau belum.
  """
  header = {"alg": ALGORITMA, "typ": "JWT"}
  isi_lengkap = dict(isi)
  isi_lengkap["exp"] = int(time.time()) + umur_detik
  bagian_header = kode_base64url(json.dumps(header, separators=(",", ":")).encode())
  bagian_isi = kode_base64url(json.dumps(isi_lengkap, separators=(",", ":")).encode())
  bagian_awal = f"{bagian_header}.{bagian_isi}"
  return f"{bagian_awal}.{tanda_tangani(bagian_awal)}"


def periksa(token):
  """Memeriksa tanda tangan dan masa berlaku, lalu mengembalikan isinya.

  Mengembalikan pasangan (isi, alasan). Isi bernilai None bila tokennya
  ditolak, dan alasannya menyebut penyebabnya, sehingga latihan dapat
  membedakan token palsu dari token yang sekadar kedaluwarsa.
  """
  bagian = token.split(".")
  if len(bagian) != 3:
    return None, "bentuk token salah"
  bagian_awal = f"{bagian[0]}.{bagian[1]}"
  # compare_digest dipakai agar lama pembandingan tidak bergantung pada
  # seberapa banyak huruf yang cocok.
  if not hmac.compare_digest(tanda_tangani(bagian_awal), bagian[2]):
    return None, "tanda tangan tidak cocok"
  isi = json.loads(dekode_base64url(bagian[1]))
  if isi.get("exp", 0) < time.time():
    return None, "token kedaluwarsa"
  return isi, "sah"
