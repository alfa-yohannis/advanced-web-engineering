#!/usr/bin/env python3
"""Aplikasi katalog kecil yang dipakai untuk mengukur anggaran performa.

Tiap alamat mewakili satu bentuk beban:
  /                        halaman demo yang memuat pengukur Core Web Vitals
  /aset/web-vitals.js      hasil kompilasi web-vitals.ts, bila sudah dibuat
  /api/katalog             satu halaman katalog, jumlah barisnya dibatasi
  /api/katalog-penuh       seluruh katalog dalam satu jawaban
  /api/terlaris            agregat buku terlaris 30 hari, dihitung tiap kali
  /api/terlaris-streaming  agregat yang sama, header dikirim lebih dahulu
  /api/vitals              penerima laporan Core Web Vitals dari browser

Jawaban di-compress dengan gzip bila klien mengirim Accept-Encoding: gzip.

Pemakaian (dari sources/chapter05, setelah docker compose up -d):
    source ../.venv/bin/activate
    python aplikasi.py
Lalu buka http://localhost:8010/ di browser.
"""

import gzip
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from psycopg_pool import ConnectionPool

ALAMAT_DENGAR = ("127.0.0.1", 8010)
DSN = "postgresql://admin:admin123@localhost:5435/toko"
UKURAN_POOL = 10

UKURAN_HALAMAN_BAWAAN = 20
UKURAN_HALAMAN_MAKSIMUM = 100
# Jawaban yang lebih kecil dari angka ini tidak di-compress, karena biaya
# compress-nya tidak terbayar oleh byte yang dihemat.
BATAS_COMPRESS_BYTE = 1024
UKURAN_POTONGAN_STREAMING = 10

DIREKTORI_STATIS = Path(__file__).parent / "statis"
BERKAS_VITALS = Path(__file__).parent / "vitals.jsonl"
CACHE_CONTROL_API = "no-store"

SQL_KATALOG = """
    SELECT id, judul, harga, stok
    FROM buku
    ORDER BY id
    LIMIT %s OFFSET %s
"""

SQL_KATALOG_PENUH = """
    SELECT id, judul, harga, stok
    FROM buku
    ORDER BY id
"""

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


def baris_menjadi_kamus(baris):
  """Mengubah satu baris katalog menjadi kamus yang siap di-serialize.

  Harga disimpan sebagai numeric di basis data, dan tipe itu tidak dikenal
  json, sehingga diubah menjadi float lebih dahulu.
  """
  id_buku, judul, harga, stok = baris
  return {"id": id_buku, "judul": judul, "harga": float(harga), "stok": stok}


def ambil_halaman_katalog(pool_koneksi, halaman, ukuran):
  """Mengambil satu halaman katalog, yaitu sebanyak ukuran baris saja.

  Inilah bentuk yang muat di dalam anggaran, karena jumlah barisnya tidak
  tumbuh mengikuti besarnya tabel.
  """
  with pool_koneksi.connection() as koneksi:
    daftar_baris = koneksi.execute(
        SQL_KATALOG, (ukuran, (halaman - 1) * ukuran)
    ).fetchall()
  return [baris_menjadi_kamus(baris) for baris in daftar_baris]


def ambil_katalog_penuh(pool_koneksi):
  """Mengambil seluruh katalog sekaligus.

  Dipakai sebagai pembanding yang sengaja melanggar anggaran, karena jawaban
  dan waktunya tumbuh mengikuti jumlah baris di tabel.
  """
  with pool_koneksi.connection() as koneksi:
    daftar_baris = koneksi.execute(SQL_KATALOG_PENUH).fetchall()
  return [baris_menjadi_kamus(baris) for baris in daftar_baris]


def jalankan_query_terlaris(pool_koneksi):
  """Menjalankan agregat buku terlaris 30 hari, tanpa cache sama sekali.

  Query yang sama dipakai Bab 4. Di sini query itu menjadi beban yang diukur,
  bukan yang disimpan.
  """
  with pool_koneksi.connection() as koneksi:
    daftar_baris = koneksi.execute(SQL_TERLARIS).fetchall()
  return [{"judul": judul, "terjual": terjual} for judul, terjual in daftar_baris]


def baca_parameter_halaman(query_alamat):
  """Membaca parameter halaman dan ukuran dari alamat, beserta batasnya.

  Ukuran dibatasi agar satu permintaan tidak dapat meminta seluruh tabel
  hanya dengan mengubah alamat.
  """
  parameter = parse_qs(query_alamat)
  halaman = max(1, int(parameter.get("halaman", ["1"])[0]))
  ukuran = int(parameter.get("ukuran", [str(UKURAN_HALAMAN_BAWAAN)])[0])
  return halaman, min(max(1, ukuran), UKURAN_HALAMAN_MAKSIMUM)


def compress_bila_diminta(isi_jawaban, nilai_accept_encoding):
  """Meng-compress isi jawaban bila klien menerima gzip dan isinya cukup besar.

  Mengembalikan pasangan (isi, nilai Content-Encoding atau None). Jawaban
  kecil dibiarkan apa adanya, karena gzip justru menambah byte dan waktu.
  """
  menerima_gzip = "gzip" in (nilai_accept_encoding or "")
  if not menerima_gzip or len(isi_jawaban) < BATAS_COMPRESS_BYTE:
    return isi_jawaban, None
  return gzip.compress(isi_jawaban), "gzip"


class ServerKatalog(ThreadingHTTPServer):
  """Server HTTP yang membawa connection pool dan berkas statisnya."""

  def __init__(self, alamat, kelas_penangan, pool_koneksi):
    """Menyimpan pool dan membaca halaman demo sekali di awal.

    Membaca sekali lebih murah daripada membaca ulang pada tiap permintaan,
    dan membuat waktu yang terukur benar-benar berasal dari query.
    """
    super().__init__(alamat, kelas_penangan)
    self.pool_koneksi = pool_koneksi
    self.isi_halaman = (DIREKTORI_STATIS / "index.html").read_bytes()


class PenanganKatalog(BaseHTTPRequestHandler):
  """Menangani tiap permintaan sesuai jalur alamatnya."""

  # Koneksi yang dipakai ulang membuat yang terukur adalah waktu server,
  # bukan waktu membuka koneksi baru.
  protocol_version = "HTTP/1.1"
  # Header dan isi jawaban ditulis sebagai dua segmen TCP. Tanpa baris ini,
  # segmen kedua tertahan Nagle sampai ACK segmen pertama tiba, dan tiap
  # jawaban kecil menanggung tambahan sekitar 40 milidetik.
  disable_nagle_algorithm = True

  def do_GET(self):
    """Menangani GET, yaitu seluruh alamat baca pada aplikasi ini."""
    bagian_alamat = urlsplit(self.path)
    jalur = bagian_alamat.path
    if jalur == "/":
      self.kirim_jawaban(200, self.server.isi_halaman,
                         "text/html; charset=utf-8", {})
    elif jalur.startswith("/aset/"):
      self.layani_berkas_aset(jalur.removeprefix("/aset/"))
    elif jalur == "/api/katalog":
      halaman, ukuran = baca_parameter_halaman(bagian_alamat.query)
      daftar_buku = ambil_halaman_katalog(self.server.pool_koneksi, halaman,
                                          ukuran)
      self.kirim_json(daftar_buku)
    elif jalur == "/api/katalog-penuh":
      self.kirim_json(ambil_katalog_penuh(self.server.pool_koneksi))
    elif jalur == "/api/terlaris":
      self.kirim_json(jalankan_query_terlaris(self.server.pool_koneksi))
    elif jalur == "/api/terlaris-streaming":
      self.layani_terlaris_streaming()
    else:
      self.kirim_jawaban(404, b"tidak ditemukan\n", "text/plain", {})

  def do_POST(self):
    """Menerima laporan Core Web Vitals yang dikirim browser."""
    if urlsplit(self.path).path != "/api/vitals":
      self.kirim_jawaban(404, b"tidak ditemukan\n", "text/plain", {})
      return
    panjang_isi = int(self.headers.get("Content-Length", "0"))
    isi_laporan = self.rfile.read(panjang_isi)
    with BERKAS_VITALS.open("a", encoding="utf-8") as berkas:
      berkas.write(isi_laporan.decode("utf-8").strip() + "\n")
    self.kirim_jawaban(204, b"", "text/plain", {})

  def layani_berkas_aset(self, nama_berkas):
    """Mengirim hasil kompilasi TypeScript, bila berkasnya sudah dibuat.

    Nama berkas dibersihkan lebih dahulu, sehingga alamat tidak dapat
    menunjuk berkas di luar direktori statis.
    """
    berkas_aset = DIREKTORI_STATIS / Path(nama_berkas).name
    if berkas_aset.suffix != ".js" or not berkas_aset.exists():
      pesan = b"// berkas belum dikompilasi, lihat README.md\n"
      self.kirim_jawaban(404, pesan, "text/javascript", {})
      return
    self.kirim_jawaban(200, berkas_aset.read_bytes(), "text/javascript", {})

  def layani_terlaris_streaming(self):
    """Mengirim header lebih dahulu, baru menghitung agregatnya.

    Bagian yang sudah siap dikirim duluan, sehingga waktu sampai byte pertama
    tidak menunggu query selesai. Waktu total tidak berubah.
    """
    self.send_response(200)
    self.send_header("Content-Type", "application/json")
    self.send_header("Cache-Control", CACHE_CONTROL_API)
    self.send_header("Transfer-Encoding", "chunked")
    self.end_headers()
    self.kirim_potongan(b'{"item":[')
    daftar_terlaris = jalankan_query_terlaris(self.server.pool_koneksi)
    for nomor, item in enumerate(daftar_terlaris):
      pemisah = b"" if nomor == 0 else b","
      self.kirim_potongan(pemisah + json.dumps(item).encode())
    self.kirim_potongan(b"]}")
    self.wfile.write(b"0\r\n\r\n")

  def kirim_potongan(self, isi_potongan):
    """Menulis satu potongan dalam format chunked milik HTTP/1.1."""
    self.wfile.write(f"{len(isi_potongan):X}\r\n".encode())
    self.wfile.write(isi_potongan + b"\r\n")

  def kirim_json(self, isi_python):
    """Menyusun jawaban JSON, meng-compress-nya bila klien menerima gzip."""
    isi_jawaban = json.dumps(isi_python).encode()
    isi_jawaban, encoding = compress_bila_diminta(
        isi_jawaban, self.headers.get("Accept-Encoding")
    )
    header_tambahan = {"Cache-Control": CACHE_CONTROL_API}
    if encoding is not None:
      header_tambahan["Content-Encoding"] = encoding
    self.kirim_jawaban(200, isi_jawaban, "application/json", header_tambahan)

  def kirim_jawaban(self, status, isi_jawaban, jenis_isi, header_tambahan):
    """Menulis baris status, header, lalu isi jawaban."""
    self.send_response(status)
    self.send_header("Content-Type", jenis_isi)
    self.send_header("Content-Length", str(len(isi_jawaban)))
    for nama_header, nilai_header in header_tambahan.items():
      self.send_header(nama_header, nilai_header)
    self.end_headers()
    if isi_jawaban:
      self.wfile.write(isi_jawaban)

  def log_message(self, format_pesan, *argumen):
    """Mematikan catatan per permintaan agar keluaran pengukuran tetap bersih."""


def main():
  """Membuka connection pool, lalu melayani sampai dihentikan."""
  pool_koneksi = ConnectionPool(DSN, min_size=2, max_size=UKURAN_POOL, open=True)
  server = ServerKatalog(ALAMAT_DENGAR, PenanganKatalog, pool_koneksi)
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
