"""Aplikasi pesanan dengan dua cara mengenali pengguna, dipakai di Bab 10.

Dua cara itu berjalan berdampingan agar dapat dibandingkan:
    sesi   server menyimpan keadaannya, klien hanya membawa penanda acak
    token  server tidak menyimpan apa pun, klien membawa isi bertanda tangan

Alamat yang dilayani:
    POST /masuk?cara=sesi|token   menukar nama dan kata sandi dengan penanda
    GET  /api/pesanan             daftar pesanan, disaring menurut hak akses
    GET  /api/pesanan/<id>        satu pesanan, diperiksa secara ABAC
    GET  /api/laporan             hanya untuk peran yang punya izin laporan
    POST /refresh                menukar refresh token dengan pasangan baru
    POST /keluar                  mencabut sesi, hanya berlaku pada cara sesi

Seluruh data ada di pengguna.json dan di memori, sehingga latihan tidak
membutuhkan basis data. Kata sandi di file itu disimpan sebagai salt dan
hash scrypt, bukan teks biasa.

Pemakaian (dari sources/chapter10):
    python3 aplikasi.py
Membuat salt dan hash kata sandi untuk pengguna baru di pengguna.json:
    python3 -c "import aplikasi; print(aplikasi.buat_catatan_sandi('eko123'))"
"""

import hashlib
import hmac
import json
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import kebijakan
import token_sederhana

HOST = "127.0.0.1"
PORT = 8070
FILE_PENGGUNA = Path(__file__).parent / "pengguna.json"
JENIS_ISI_JSON = "application/json"
# Umur sengaja dibuat sangat pendek agar kedaluwarsanya terlihat dalam satu
# sesi latihan. Pada sistem sungguhan satuannya menit untuk access token dan
# hari untuk refresh token.
UMUR_ACCESS_DETIK = 5
UMUR_REFRESH_DETIK = 120
PANJANG_PENANDA_BYTE = 16
# Pengaturan scrypt untuk kata sandi. Biayanya sengaja kecil agar latihan
# tetap cepat, sedangkan sistem sungguhan memakai biaya yang lebih besar.
BIAYA_SCRYPT = 2 ** 14
UKURAN_BLOK_SCRYPT = 8
PARALELISME_SCRYPT = 1
PANJANG_SALT_BYTE = 16
PANJANG_HASH_BYTE = 32
# Salt tetap untuk nama yang tidak terdaftar. Hash-nya tetap dihitung, agar
# lama response tidak membocorkan nama mana yang terdaftar.
SALT_NAMA_TAK_TERDAFTAR = bytes(PANJANG_SALT_BYTE)

# Keadaan yang disimpan server. Sesi dan refresh token sama-sama di sini,
# dan keduanya hilang begitu proses dimatikan.
SESI = {}
REFRESH = {}


def baca_data():
  """Membaca daftar pengguna dan pesanan dari file."""
  return json.loads(FILE_PENGGUNA.read_text(encoding="utf-8"))


def turunkan_hash_sandi(kata_sandi, salt):
  """Menurunkan hash satu kata sandi dengan scrypt dan salt miliknya.

  Salt yang berbeda tiap pengguna membuat dua kata sandi yang sama
  menghasilkan hash yang berbeda. scrypt sengaja lambat dan boros memori,
  sehingga menebak kata sandi satu per satu menjadi mahal.
  """
  return hashlib.scrypt(kata_sandi.encode(), salt=salt, n=BIAYA_SCRYPT,
                        r=UKURAN_BLOK_SCRYPT, p=PARALELISME_SCRYPT,
                        dklen=PANJANG_HASH_BYTE)


def buat_catatan_sandi(kata_sandi):
  """Membuat salt baru beserta hash kata sandinya, untuk pengguna baru.

  Hasilnya teks JSON yang siap ditempel ke entri pengguna di pengguna.json.
  Salt-nya acak, sehingga hasilnya berbeda tiap kali walaupun kata sandinya
  sama.
  """
  salt = secrets.token_bytes(PANJANG_SALT_BYTE)
  hash_sandi = turunkan_hash_sandi(kata_sandi, salt)
  return json.dumps({"salt_sandi": salt.hex(), "hash_sandi": hash_sandi.hex()})


def cari_pengguna(data, nama, kata_sandi):
  """Mencocokkan nama dan kata sandi, lalu mengembalikan penggunanya.

  Hash kata sandi kiriman diturunkan dengan salt milik pengguna itu, lalu
  dibandingkan dengan hmac.compare_digest, sehingga lama pembandingan tidak
  bergantung pada seberapa banyak byte yang cocok. Nama yang tidak terdaftar
  tetap menjalani satu scrypt dengan salt tetap, sehingga lamanya sama dengan
  kata sandi yang salah dan tidak membocorkan nama mana yang ada.
  """
  for pengguna in data["pengguna"]:
    if pengguna["nama"] == nama:
      salt = bytes.fromhex(pengguna["salt_sandi"])
      hash_dikirim = turunkan_hash_sandi(kata_sandi, salt)
      hash_tersimpan = bytes.fromhex(pengguna["hash_sandi"])
      if hmac.compare_digest(hash_dikirim, hash_tersimpan):
        return pengguna
      return None
  turunkan_hash_sandi(kata_sandi, SALT_NAMA_TAK_TERDAFTAR)
  return None


def buat_identitas(pengguna):
  """Menyusun identitas yang dibawa penanda, tanpa data rahasia di dalamnya."""
  return {"sub": pengguna["nama"], "peran": pengguna["peran"],
          "tenant": pengguna["tenant"]}


def terbitkan_pasangan_token(identitas, keluarga=None):
  """Menerbitkan access token baru beserta refresh token penggantinya.

  Tiap refresh token dicatat beserta keluarganya. Ketika satu refresh token
  dipakai, penggantinya terbit dan yang lama ditandai terpakai, sehingga
  pemakaian ulang dapat dikenali.
  """
  access = token_sederhana.buat(identitas, UMUR_ACCESS_DETIK)
  refresh = secrets.token_hex(PANJANG_PENANDA_BYTE)
  REFRESH[refresh] = {
      "identitas": identitas,
      "keluarga": keluarga or secrets.token_hex(PANJANG_PENANDA_BYTE),
      "kedaluwarsa": time.time() + UMUR_REFRESH_DETIK,
      "terpakai": False,
  }
  return access, refresh


def cabut_keluarga(keluarga):
  """Mencabut seluruh refresh token satu keluarga sekaligus.

  Dipanggil ketika ada refresh token lama yang dipakai ulang. Keadaan itu
  menandakan penanda tersebut sudah berada di tangan lain, dan cara teraman
  adalah menghentikan seluruh rantainya.
  """
  jumlah = 0
  for penanda, catatan in list(REFRESH.items()):
    if catatan["keluarga"] == keluarga:
      del REFRESH[penanda]
      jumlah += 1
  return jumlah


def identitas_dari_permintaan(header_otorisasi, header_cookie):
  """Mengenali pemohon dari token Bearer atau dari cookie sesi.

  Mengembalikan pasangan (identitas, alasan). Identitas bernilai None bila
  pemohon tidak dikenali, dan alasannya ikut dikembalikan agar latihan dapat
  membedakan penanda kedaluwarsa dari penanda yang sudah dicabut.
  """
  if header_otorisasi and header_otorisasi.startswith("Bearer "):
    return token_sederhana.periksa(header_otorisasi[len("Bearer "):])
  if header_cookie and "sesi=" in header_cookie:
    penanda = header_cookie.split("sesi=")[1].split(";")[0]
    catatan = SESI.get(penanda)
    if catatan is None:
      return None, "sesi tidak dikenal atau sudah dicabut"
    return catatan, "sah"
  return None, "tanpa penanda"


class PenanganIdentitas(BaseHTTPRequestHandler):
  """Melayani permintaan masuk, pembacaan data, dan penyegaran token."""

  protocol_version = "HTTP/1.1"
  disable_nagle_algorithm = True

  def do_POST(self):
    """Mengarahkan permintaan masuk, penyegaran, dan keluar."""
    bagian = urlparse(self.path)
    parameter = parse_qs(bagian.query)
    if bagian.path == "/masuk":
      self.layani_masuk(parameter)
      return
    if bagian.path == "/refresh":
      self.layani_refresh(parameter)
      return
    if bagian.path == "/keluar":
      self.layani_keluar()
      return
    self.kirim(404, {"pesan": "alamat tidak dikenal"}, [])

  def do_GET(self):
    """Mengarahkan permintaan pembacaan data."""
    bagian = urlparse(self.path)
    if bagian.path == "/api/pesanan":
      self.layani_daftar_pesanan()
      return
    if bagian.path.startswith("/api/pesanan/"):
      self.layani_satu_pesanan(bagian.path.rsplit("/", 1)[-1])
      return
    if bagian.path == "/api/laporan":
      self.layani_laporan()
      return
    self.kirim(404, {"pesan": "alamat tidak dikenal"}, [])

  def layani_masuk(self, parameter):
    """Menukar nama dan kata sandi dengan penanda, sesuai cara yang diminta."""
    data = baca_data()
    nama = parameter.get("nama", [""])[0]
    kata_sandi = parameter.get("sandi", [""])[0]
    pengguna = cari_pengguna(data, nama, kata_sandi)
    if pengguna is None:
      self.kirim(401, {"pesan": "nama atau kata sandi salah"}, [])
      return
    identitas = buat_identitas(pengguna)
    if parameter.get("cara", ["token"])[0] == "sesi":
      penanda = secrets.token_hex(PANJANG_PENANDA_BYTE)
      SESI[penanda] = identitas
      cookie = f"sesi={penanda}; HttpOnly; SameSite=Lax; Path=/"
      self.kirim(200, {"cara": "sesi", "panjang_penanda": len(penanda)},
                 [("Set-Cookie", cookie)])
      return
    access, refresh = terbitkan_pasangan_token(identitas)
    self.kirim(200, {"cara": "token", "access_token": access,
                     "refresh_token": refresh,
                     "panjang_access": len(access),
                     "umur_access_detik": UMUR_ACCESS_DETIK}, [])

  def layani_refresh(self, parameter):
    """Menukar refresh token dengan pasangan baru, sambil merotasinya.

    Refresh token yang sudah terpakai dianggap bocor bila dipakai lagi,
    sehingga seluruh keluarganya dicabut dan pemohon harus masuk ulang.
    """
    penanda = parameter.get("refresh", [""])[0]
    catatan = REFRESH.get(penanda)
    if catatan is None:
      self.kirim(401, {"pesan": "refresh token tidak dikenal"}, [])
      return
    if catatan["terpakai"]:
      jumlah = cabut_keluarga(catatan["keluarga"])
      self.kirim(401, {"pesan": "refresh token dipakai ulang",
                       "dicabut": jumlah}, [])
      return
    if catatan["kedaluwarsa"] < time.time():
      self.kirim(401, {"pesan": "refresh token kedaluwarsa"}, [])
      return
    catatan["terpakai"] = True
    access, refresh = terbitkan_pasangan_token(catatan["identitas"],
                                               catatan["keluarga"])
    self.kirim(200, {"access_token": access, "refresh_token": refresh}, [])

  def layani_keluar(self):
    """Mencabut sesi pemohon, yaitu hal yang tidak dapat dilakukan token."""
    cookie = self.headers.get("Cookie", "")
    if "sesi=" not in cookie:
      self.kirim(400, {"pesan": "hanya berlaku pada cara sesi"}, [])
      return
    penanda = cookie.split("sesi=")[1].split(";")[0]
    ada = SESI.pop(penanda, None) is not None
    self.kirim(200, {"dicabut": ada}, [])

  def kenali_atau_tolak(self):
    """Mengenali pemohon, atau mengirim 401 beserta alasannya."""
    identitas, alasan = identitas_dari_permintaan(
        self.headers.get("Authorization"), self.headers.get("Cookie"))
    if identitas is None:
      self.kirim(401, {"pesan": alasan}, [])
    return identitas

  def layani_daftar_pesanan(self):
    """Mengirim daftar pesanan yang sudah disaring menurut hak akses."""
    identitas = self.kenali_atau_tolak()
    if identitas is None:
      return
    data = baca_data()
    terlihat = kebijakan.saring_pesanan(identitas, data["pesanan"])
    self.kirim(200, {"tenant": identitas["tenant"], "jumlah": len(terlihat),
                     "item": terlihat}, [])

  def layani_satu_pesanan(self, id_teks):
    """Mengirim satu pesanan bila aturan ABAC mengizinkannya."""
    identitas = self.kenali_atau_tolak()
    if identitas is None:
      return
    if not id_teks.isdigit():
      self.kirim(400, {"pesan": "id harus angka"}, [])
      return
    data = baca_data()
    pesanan = next((p for p in data["pesanan"] if p["id"] == int(id_teks)),
                   None)
    if pesanan is None:
      self.kirim(404, {"pesan": "pesanan tidak ada"}, [])
      return
    boleh, alasan = kebijakan.boleh_baca_pesanan(identitas, pesanan)
    if not boleh:
      # Pesanan milik tenant lain dijawab 404, bukan 403, agar keberadaannya
      # tidak ikut bocor kepada tenant yang tidak berhak.
      status = 404 if alasan == "tenant berbeda" else 403
      self.kirim(status, {"pesan": alasan}, [])
      return
    self.kirim(200, {"pesanan": pesanan, "alasan": alasan}, [])

  def layani_laporan(self):
    """Mengirim laporan ringkas, hanya bagi peran yang punya izinnya."""
    identitas = self.kenali_atau_tolak()
    if identitas is None:
      return
    if not kebijakan.punya_izin(identitas["peran"], "baca_laporan"):
      self.kirim(403, {"pesan": "peran tidak punya izin baca_laporan"}, [])
      return
    data = baca_data()
    milik_tenant = [p for p in data["pesanan"]
                    if p["tenant"] == identitas["tenant"]]
    total = sum(pesanan["total"] for pesanan in milik_tenant)
    self.kirim(200, {"tenant": identitas["tenant"],
                     "jumlah_pesanan": len(milik_tenant), "total": total}, [])

  def kirim(self, status, isi_python, header_tambahan):
    """Mengirim satu response JSON lengkap beserta header tambahannya."""
    isi = json.dumps(isi_python).encode()
    self.send_response(status)
    self.send_header("Content-Type", JENIS_ISI_JSON)
    self.send_header("Content-Length", str(len(isi)))
    self.send_header("Cache-Control", "no-store")
    for nama_header, nilai in header_tambahan:
      self.send_header(nama_header, nilai)
    self.end_headers()
    self.wfile.write(isi)

  def log_message(self, format_pesan, *argumen):
    """Mematikan log bawaan, agar keluaran pengukuran tidak tenggelam."""


def main():
  """Menyalakan server sampai dihentikan dengan Ctrl+C."""
  server = ThreadingHTTPServer((HOST, PORT), PenanganIdentitas)
  print(f"Melayani di http://{HOST}:{PORT}/  (Ctrl+C untuk berhenti)")
  server.serve_forever()


if __name__ == "__main__":
  main()
