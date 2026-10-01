"""Aplikasi toko buku yang sudah dikeraskan, bahan audit keamanan Bab 7.

Seluruh pertahanan pada file ini bersifat bawaan, bukan pilihan: header
keamanan dipasang pada tiap response, cookie sesi diberi atribut pembatas,
daftar origin yang boleh memanggil API ditulis di kebijakan.json, teks dari
pengguna di-escape sebelum masuk HTML, dan seluruh query memakai parameter.

Secret dibaca dari environment, bukan ditulis di kode. Tanpa environment itu
aplikasi memakai nilai sementara yang hanya layak untuk latihan di komputer
sendiri.

Pemakaian (dari sources/chapter07, setelah docker compose up -d):
    source ../.venv/bin/activate
    SECRET_SESI=rahasia-latihan python aplikasi.py
"""

import html
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import psycopg

HOST = "127.0.0.1"
PORT = 8030
DSN = "postgresql://admin:admin123@localhost:5437/toko"
DIREKTORI_STATIS = Path(__file__).parent / "statis"
FILE_KEBIJAKAN = Path(__file__).parent / "kebijakan.json"
JENIS_ISI_JSON = "application/json"
JENIS_ISI_HTML = "text/html; charset=utf-8"
# Batas jumlah baris yang dikembalikan pencarian, agar satu permintaan tidak
# dapat menarik seluruh tabel.
BATAS_HASIL_CARI = 20
PANJANG_SESI_BYTE = 16

SQL_CARI_BUKU = """
    SELECT id, judul, harga
    FROM buku
    WHERE judul ILIKE %s
    ORDER BY id
    LIMIT %s
"""


def baca_kebijakan():
  """Membaca kebijakan keamanan, yaitu satu-satunya tempat syaratnya ditulis.

  Aplikasi dan skrip pemeriksa membaca file yang sama, sehingga keduanya
  tidak dapat berbeda pendapat tentang apa yang wajib ada.
  """
  return json.loads(FILE_KEBIJAKAN.read_text(encoding="utf-8"))


def ambil_secret_sesi():
  """Mengambil secret penanda sesi dari environment.

  Secret tidak pernah ditulis di kode, karena kode masuk repositori dan
  dibaca siapa saja yang punya aksesnya. Bila environment-nya kosong,
  aplikasi membuat nilai acak sekali jalan, yang hilang begitu aplikasi
  dimatikan.
  """
  return os.environ.get("SECRET_SESI") or secrets.token_hex(PANJANG_SESI_BYTE)


def cari_buku(judul_dicari):
  """Mencari buku menurut judulnya, dengan judul dikirim sebagai parameter.

  Teks dari pengguna tidak pernah disambung ke dalam SQL. Tanda kutip, tanda
  titik koma, dan kata kunci SQL di dalamnya diperlakukan sebagai data biasa,
  sehingga hasilnya hanya kosong, bukan perintah tambahan.
  """
  pola = f"%{judul_dicari}%"
  with psycopg.connect(DSN) as koneksi:
    baris = koneksi.execute(SQL_CARI_BUKU, (pola, BATAS_HASIL_CARI)).fetchall()
  return [{"id": id_buku, "judul": judul, "harga": int(harga)}
          for id_buku, judul, harga in baris]


def susun_halaman_sapaan(nama_dikirim):
  """Menyusun halaman sapaan dari teks yang dikirim pengguna.

  Teksnya di-escape lebih dahulu dengan html.escape, sehingga tanda kurung
  siku dan tanda kutip berubah menjadi entitas dan terbaca sebagai teks,
  bukan sebagai markup yang ikut dijalankan browser.
  """
  nama_aman = html.escape(nama_dikirim, quote=True)
  return (
      "<!DOCTYPE html>\n<html lang=\"id\">\n<head><meta charset=\"utf-8\">"
      "<title>Sapaan</title></head>\n"
      f"<body><h1>Halo, {nama_aman}</h1>\n"
      "<p>Teks di atas berasal dari parameter alamat.</p></body></html>\n"
  ).encode()


class PenanganToko(BaseHTTPRequestHandler):
  """Melayani permintaan HTTP dengan header keamanan yang selalu terpasang.

  Header dipasang di satu tempat, yaitu kirim_response, sehingga alamat baru
  tidak dapat lupa memasangnya.
  """

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_GET(self):
    """Mengarahkan permintaan ke penangan yang sesuai dengan jalurnya."""
    bagian = urlparse(self.path)
    if bagian.path == "/":
      self.layani_halaman_depan()
      return
    if bagian.path == "/sapa":
      self.layani_sapaan(parse_qs(bagian.query))
      return
    if bagian.path == "/api/cari":
      self.layani_pencarian(parse_qs(bagian.query))
      return
    if bagian.path == "/api/profil":
      self.layani_profil()
      return
    self.kirim_response(404, b'{"pesan":"alamat tidak dikenal"}',
                        JENIS_ISI_JSON, [])

  def do_HEAD(self):
    """Menjawab HEAD dengan header yang sama persis, tanpa isinya.

    Permintaan HEAD dipakai alat pemeriksa untuk membaca header tanpa ikut
    mengunduh isinya. Tanpa metode ini, server menjawab 501 dan pemeriksaan
    header gagal sebelum sempat dinilai.
    """
    self.do_GET()

  def do_OPTIONS(self):
    """Menjawab permintaan preflight CORS menurut daftar origin yang boleh."""
    header_tambahan = self.susun_header_cors()
    header_tambahan.append(("Access-Control-Allow-Methods", "GET, OPTIONS"))
    self.kirim_response(204, b"", JENIS_ISI_JSON, header_tambahan)

  def susun_header_cors(self):
    """Menyusun header CORS hanya untuk origin yang terdaftar di kebijakan.

    Origin yang tidak terdaftar tidak mendapat header izin sama sekali,
    sehingga browser yang memintanya menolak membaca response itu sendiri.
    Nilai bintang sengaja tidak dipakai, karena membuka API bagi situs mana
    pun.
    """
    origin_diminta = self.headers.get("Origin")
    if origin_diminta in self.server.kebijakan["origin_boleh"]:
      return [("Access-Control-Allow-Origin", origin_diminta),
              ("Vary", "Origin")]
    return [("Vary", "Origin")]

  def layani_halaman_depan(self):
    """Mengirim halaman depan dari direktori statis."""
    file_halaman = DIREKTORI_STATIS / "index.html"
    self.kirim_response(200, file_halaman.read_bytes(), JENIS_ISI_HTML, [])

  def layani_sapaan(self, parameter):
    """Mengirim halaman sapaan berisi teks pengguna yang sudah di-escape."""
    nama = parameter.get("nama", ["Pengunjung"])[0]
    self.kirim_response(200, susun_halaman_sapaan(nama), JENIS_ISI_HTML, [])

  def layani_pencarian(self, parameter):
    """Mencari buku, lalu mengirim hasilnya sebagai JSON."""
    judul = parameter.get("judul", [""])[0]
    isi = json.dumps({"kata_kunci": judul, "hasil": cari_buku(judul)}).encode()
    self.kirim_response(200, isi, JENIS_ISI_JSON, self.susun_header_cors())

  def layani_profil(self):
    """Mengirim profil ringkas sambil memasang cookie sesi yang dibatasi.

    Atribut HttpOnly menutup cookie dari JavaScript, SameSite=Lax menahannya
    pada permintaan lintas situs, dan Secure membuatnya hanya dikirim lewat
    HTTPS. Pada latihan ini aplikasinya berjalan lewat HTTP di localhost,
    sehingga Secure sengaja tidak dipasang agar cookie tetap terlihat saat
    diperiksa.
    """
    cookie = (f"sesi={self.server.secret_sesi}; HttpOnly; SameSite=Lax; "
              "Path=/; Max-Age=3600")
    isi = json.dumps({"nama": "Mahasiswa", "peran": "pembeli"}).encode()
    self.kirim_response(200, isi, JENIS_ISI_JSON,
                        [("Set-Cookie", cookie)] + self.susun_header_cors())

  def kirim_response(self, status, isi_response, jenis_isi, header_tambahan):
    """Mengirim satu response lengkap beserta seluruh header keamanannya."""
    self.send_response(status)
    self.send_header("Content-Type", jenis_isi)
    self.send_header("Content-Length", str(len(isi_response)))
    for nama_header, nilai in self.server.kebijakan["header_wajib"].items():
      self.send_header(nama_header, nilai)
    for nama_header, nilai in header_tambahan:
      self.send_header(nama_header, nilai)
    self.end_headers()
    if isi_response and self.command != "HEAD":
      self.wfile.write(isi_response)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, agar keluaran pemeriksaan tidak tenggelam."""


class ServerToko(ThreadingHTTPServer):
  """Server yang membawa kebijakan keamanan dan secret sesinya sendiri.

  Keduanya dibaca sekali saat server dibuat, sehingga tiap permintaan tidak
  perlu membaca file lagi.
  """

  def __init__(self, alamat, kelas_penangan, kebijakan, secret_sesi):
    """Menyimpan kebijakan dan secret agar dapat dipakai tiap penangan."""
    super().__init__(alamat, kelas_penangan)
    self.kebijakan = kebijakan
    self.secret_sesi = secret_sesi


def main():
  """Menyalakan server sampai dihentikan dengan Ctrl+C."""
  server = ServerToko((HOST, PORT), PenanganToko, baca_kebijakan(),
                      ambil_secret_sesi())
  print(f"Melayani di http://{HOST}:{PORT}/  (Ctrl+C untuk berhenti)")
  server.serve_forever()


if __name__ == "__main__":
  main()
