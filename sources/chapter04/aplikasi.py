#!/usr/bin/env python3
"""Aplikasi toko kecil untuk memperagakan caching HTTP dan cache-aside.

Empat alamat disediakan, masing-masing dengan kebijakan cache berbeda:
  /                    halaman HTML, selalu divalidasi ulang lewat ETag
  /aset/app.3f9a2c.js  fingerprinted asset, boleh disimpan setahun
  /api/terlaris        buku terlaris 30 hari, dihitung ulang tiap permintaan
  /api/terlaris-cache  kueri yang sama, lewat cache-aside di Redis

Header X-Cache pada alamat terakhir berisi HIT atau MISS, sehingga asal
jawabannya dapat diamati lewat curl maupun panel Network.

Pemakaian (dari sources/chapter04, setelah docker compose up -d):
    source ../.venv/bin/activate
    python aplikasi.py
Lalu buka http://localhost:8000/ di browser.
"""

import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import redis
from psycopg_pool import ConnectionPool
from redis.backoff import NoBackoff
from redis.retry import Retry

ALAMAT_DENGAR = ("127.0.0.1", 8000)
DSN = "postgresql://awe:awe@localhost:5434/toko"
REDIS_HOST = "localhost"
REDIS_PORT = 6380
UKURAN_POOL = 10

KUNCI_TERLARIS = "terlaris:30hari"
TTL_TERLARIS_DETIK = 60
# Cache yang lambat lebih buruk daripada tanpa cache. Bila Redis tidak
# menjawab dalam 50 milidetik, permintaan langsung diteruskan ke basis data.
BATAS_WAKTU_REDIS_DETIK = 0.05
# redis-py 8 melakukan retry sampai 10 kali secara bawaan untuk perintah yang
# gagal. Untuk cache, retry itu dimatikan agar batas waktu di atas benar-benar
# menjadi batas.
JUMLAH_RETRY_REDIS = 0

DIREKTORI_STATIS = Path(__file__).parent / "statis"
NAMA_BERKAS_ASET = "app.3f9a2c.js"

CACHE_CONTROL_HALAMAN = "no-cache"
CACHE_CONTROL_ASET = "public, max-age=31536000, immutable"
CACHE_CONTROL_API = "no-store"

SQL_TERLARIS = """
    SELECT b.judul, sum(i.jumlah) AS terjual
    FROM item_pesanan i
    JOIN pesanan p ON p.id = i.pesanan_id
    JOIN buku b ON b.id = i.buku_id
    WHERE p.dibuat_pada >= now() - interval '30 days'
      AND p.status <> 'batal'
    GROUP BY b.id, b.judul
    ORDER BY terjual DESC
    LIMIT 10
"""


def hitung_etag(isi_berkas):
  """Menurunkan ETag dari isi berkas.

  Isi yang sama selalu menghasilkan ETag yang sama, sehingga browser dapat
  bertanya "masih sama?" tanpa mengunduh ulang isinya.
  """
  return '"' + hashlib.sha256(isi_berkas).hexdigest()[:16] + '"'


def jalankan_kueri_terlaris(pool_koneksi):
  """Menjalankan kueri buku terlaris langsung ke basis data.

  Inilah pekerjaan mahal yang ingin dihindari. Pada data uji Bab 3 kueri ini
  memakan puluhan milidetik, walaupun indeksnya sudah dipasang.
  """
  with pool_koneksi.connection() as koneksi:
    daftar_baris = koneksi.execute(SQL_TERLARIS).fetchall()
  return [{"judul": judul, "terjual": terjual} for judul, terjual in daftar_baris]


def baca_dari_cache(cache, kunci):
  """Membaca satu kunci dari Redis, atau None bila kuncinya tidak ada.

  Error Redis sengaja ditelan. Cache bukan source of truth, sehingga Redis
  yang mati hanya membuat aplikasi lebih lambat, bukan ikut mati.
  """
  try:
    return cache.get(kunci)
  except redis.RedisError:
    return None


def simpan_ke_cache(cache, kunci, isi, ttl_detik):
  """Menyimpan isi ke Redis beserta masa berlakunya. Error-nya ikut ditelan."""
  try:
    cache.set(kunci, isi, ex=ttl_detik)
  except redis.RedisError:
    pass


def ambil_terlaris_lewat_cache(pool_koneksi, cache):
  """Pola cache-aside: periksa cache, bila tidak ada hitung lalu simpan.

  Mengembalikan pasangan (isi JSON dalam bentuk byte, "HIT" atau "MISS").
  """
  isi_tersimpan = baca_dari_cache(cache, KUNCI_TERLARIS)
  if isi_tersimpan is not None:
    return isi_tersimpan, "HIT"
  isi_json = json.dumps(jalankan_kueri_terlaris(pool_koneksi)).encode()
  simpan_ke_cache(cache, KUNCI_TERLARIS, isi_json, TTL_TERLARIS_DETIK)
  return isi_json, "MISS"


class ServerToko(ThreadingHTTPServer):
  """Server HTTP yang membawa connection pool, klien Redis, dan berkas statis.

  Semuanya disimpan sebagai atribut server, sehingga penangan permintaan
  memakainya lewat self.server tanpa variabel global.
  """

  def __init__(self, alamat, kelas_penangan, pool_koneksi, cache):
    """Membaca berkas statis sekali di awal, lalu menghitung ETag halamannya.

    Membaca sekali lebih murah daripada membaca ulang tiap permintaan. ETag
    yang dihitung dari isi berkas otomatis berganti bila berkasnya diubah
    lalu server dinyalakan ulang.
    """
    super().__init__(alamat, kelas_penangan)
    self.pool_koneksi = pool_koneksi
    self.cache = cache
    self.isi_halaman = (DIREKTORI_STATIS / "index.html").read_bytes()
    self.isi_aset = (DIREKTORI_STATIS / NAMA_BERKAS_ASET).read_bytes()
    self.etag_halaman = hitung_etag(self.isi_halaman)


class PenanganToko(BaseHTTPRequestHandler):
  """Menangani tiap permintaan sesuai jalur alamatnya."""

  def do_GET(self):
    """Menangani GET, yaitu permintaan yang dikirim browser."""
    self.layani_permintaan(sertakan_isi=True)

  def do_HEAD(self):
    """Sama dengan GET tanpa isi, dipakai oleh curl -I untuk melihat header."""
    self.layani_permintaan(sertakan_isi=False)

  def layani_permintaan(self, sertakan_isi):
    """Memilih jawaban berdasarkan jalur alamat."""
    server = self.server
    if self.path == "/":
      self.layani_halaman(sertakan_isi)
    elif self.path == "/aset/" + NAMA_BERKAS_ASET:
      header_tambahan = {"Cache-Control": CACHE_CONTROL_ASET}
      self.kirim_jawaban(200, server.isi_aset, "text/javascript",
                         header_tambahan, sertakan_isi)
    elif self.path == "/api/terlaris":
      isi_json = json.dumps(jalankan_kueri_terlaris(server.pool_koneksi)).encode()
      header_tambahan = {"Cache-Control": CACHE_CONTROL_API}
      self.kirim_jawaban(200, isi_json, "application/json",
                         header_tambahan, sertakan_isi)
    elif self.path == "/api/terlaris-cache":
      isi_json, asal_jawaban = ambil_terlaris_lewat_cache(
          server.pool_koneksi, server.cache
      )
      header_tambahan = {"Cache-Control": CACHE_CONTROL_API, "X-Cache": asal_jawaban}
      self.kirim_jawaban(200, isi_json, "application/json",
                         header_tambahan, sertakan_isi)
    else:
      self.kirim_jawaban(404, b"tidak ditemukan\n", "text/plain", {}, sertakan_isi)

  def layani_halaman(self, sertakan_isi):
    """Menjawab 304 bila ETag kiriman browser masih sama, 200 bila tidak."""
    header_tambahan = {
        "Cache-Control": CACHE_CONTROL_HALAMAN,
        "ETag": self.server.etag_halaman,
    }
    if self.headers.get("If-None-Match") == self.server.etag_halaman:
      # 304 tidak membawa isi. Browser memakai salinan yang sudah dimilikinya.
      self.kirim_jawaban(304, b"", "text/html", header_tambahan,
                         sertakan_isi=False)
      return
    jenis_isi = "text/html; charset=utf-8"
    self.kirim_jawaban(200, self.server.isi_halaman, jenis_isi,
                       header_tambahan, sertakan_isi)

  def kirim_jawaban(self, status, isi_jawaban, jenis_isi, header_tambahan,
                    sertakan_isi):
    """Menulis baris status, header, lalu isi jawaban bila diminta."""
    self.send_response(status)
    self.send_header("Content-Type", jenis_isi)
    if status != 304:
      self.send_header("Content-Length", str(len(isi_jawaban)))
    for nama_header, nilai_header in header_tambahan.items():
      self.send_header(nama_header, nilai_header)
    self.end_headers()
    if sertakan_isi:
      self.wfile.write(isi_jawaban)

  def log_message(self, format_pesan, *argumen):
    """Mematikan catatan per permintaan agar keluaran pengukuran tetap bersih."""


def main():
  """Membuka connection pool dan klien Redis, lalu melayani sampai dihentikan."""
  pool_koneksi = ConnectionPool(DSN, min_size=2, max_size=UKURAN_POOL, open=True)
  cache = redis.Redis(
      host=REDIS_HOST,
      port=REDIS_PORT,
      socket_timeout=BATAS_WAKTU_REDIS_DETIK,
      socket_connect_timeout=BATAS_WAKTU_REDIS_DETIK,
      retry=Retry(NoBackoff(), JUMLAH_RETRY_REDIS),
  )
  server = ServerToko(ALAMAT_DENGAR, PenanganToko, pool_koneksi, cache)
  host, port = ALAMAT_DENGAR
  print(f"Melayani di http://{host}:{port}/  (Ctrl+C untuk berhenti)")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass
  finally:
    server.server_close()
    pool_koneksi.close()


if __name__ == "__main__":
  main()
