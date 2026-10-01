"""Menilai aplikasi terhadap kebijakan keamanan, lalu memberi verdict.

Pemeriksaannya bersifat mengamati: skrip ini hanya mengambil response biasa
dari aplikasi sendiri, lalu membaca header, cookie, dan perilaku CORS-nya.
Tidak ada permintaan yang dibuat untuk membebani atau menembus apa pun.

Gerbang ini keluar dengan status 1 bila ada satu saja syarat yang belum
terpenuhi, sehingga dapat dipasang di Continuous Integration untuk memblokir
merge.

Pemakaian (dari sources/chapter07, setelah aplikasi.py menyala):
    source ../.venv/bin/activate
    python periksa-keamanan.py [kebijakan.json]
"""

import json
import sys
from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import urlparse

FILE_KEBIJAKAN_BAWAAN = Path(__file__).parent / "kebijakan.json"
BATAS_WAKTU_DETIK = 5
LEBAR_NAMA = 44
LEBAR_KEADAAN = 12


def baca_kebijakan(nama_file):
  """Membaca kebijakan keamanan, yaitu daftar syarat yang harus dipenuhi."""
  return json.loads(Path(nama_file).read_text(encoding="utf-8"))


def ambil_response(alamat_dasar, jalur, header_tambahan):
  """Mengambil satu response apa adanya, lalu mengembalikan status dan headernya.

  Yang dikembalikan hanya status dan daftar header, karena isi response tidak
  dinilai pemeriksaan ini.
  """
  bagian = urlparse(alamat_dasar)
  koneksi = HTTPConnection(bagian.hostname, bagian.port,
                           timeout=BATAS_WAKTU_DETIK)
  koneksi.request("GET", jalur, headers=header_tambahan)
  response = koneksi.getresponse()
  response.read()
  daftar_header = response.getheaders()
  koneksi.close()
  return response.status, daftar_header


def cari_header(daftar_header, nama_dicari):
  """Mencari satu header tanpa mempedulikan besar kecil hurufnya."""
  for nama, nilai in daftar_header:
    if nama.lower() == nama_dicari.lower():
      return nilai
  return None


def nilai_header_wajib(kebijakan, jalur):
  """Memeriksa seluruh header wajib pada satu alamat.

  Nilainya ikut dibandingkan, bukan hanya keberadaannya, karena header yang
  ada tetapi isinya longgar tidak melindungi apa pun.
  """
  _, daftar_header = ambil_response(kebijakan["alamat_dasar"], jalur, {})
  daftar_baris = []
  for nama_header, nilai_wajib in kebijakan["header_wajib"].items():
    nilai_terbaca = cari_header(daftar_header, nama_header)
    daftar_baris.append((f"{jalur} {nama_header}", nilai_wajib,
                         nilai_terbaca or "tidak ada",
                         nilai_terbaca == nilai_wajib))
  return daftar_baris


def nilai_atribut_cookie(kebijakan):
  """Memeriksa atribut pembatas pada cookie sesi.

  Cookie tanpa HttpOnly dapat dibaca JavaScript mana pun yang berjalan di
  halaman itu, dan cookie tanpa SameSite ikut terkirim pada permintaan yang
  dipicu situs lain.
  """
  _, daftar_header = ambil_response(kebijakan["alamat_dasar"],
                                    "/api/profil", {})
  cookie = cari_header(daftar_header, "Set-Cookie") or ""
  daftar_baris = []
  for atribut in kebijakan["atribut_cookie_wajib"]:
    ada = atribut.lower() in cookie.lower()
    daftar_baris.append((f"cookie sesi {atribut}", "ada",
                         "ada" if ada else "tidak ada", ada))
  return daftar_baris


def nilai_cors(kebijakan):
  """Memeriksa bahwa izin CORS hanya diberikan kepada origin yang terdaftar.

  Origin yang terdaftar harus menerima namanya sendiri pada header izin,
  sedangkan origin lain tidak boleh menerima izin apa pun, termasuk bintang.
  """
  daftar_baris = []
  for origin in kebijakan["origin_boleh"]:
    _, daftar_header = ambil_response(kebijakan["alamat_dasar"],
                                      "/api/profil", {"Origin": origin})
    izin = cari_header(daftar_header, "Access-Control-Allow-Origin")
    daftar_baris.append((f"CORS izin untuk {origin}", origin,
                         izin or "tidak ada", izin == origin))
  for origin in kebijakan["origin_ditolak"]:
    _, daftar_header = ambil_response(kebijakan["alamat_dasar"],
                                      "/api/profil", {"Origin": origin})
    izin = cari_header(daftar_header, "Access-Control-Allow-Origin")
    daftar_baris.append((f"CORS tolak {origin}", "tidak ada",
                         izin or "tidak ada", izin is None))
  return daftar_baris


def ringkas_keadaan(diharapkan, terbaca, lolos):
  """Meringkas hasil satu pemeriksaan menjadi satu kata.

  Nilai header bisa panjang, dan mencetaknya utuh membuat tabel tidak
  terbaca. Yang perlu diketahui pembaca hanya tiga keadaan: sesuai, berbeda,
  atau memang tidak ada.
  """
  if lolos:
    return "sesuai"
  if terbaca in ("tidak ada", ""):
    return "tidak ada"
  return "beda"


def cetak_baris(baris):
  """Mencetak satu baris penilaian, lengkap dengan verdict-nya."""
  nama, diharapkan, terbaca, lolos = baris
  keadaan = ringkas_keadaan(diharapkan, terbaca, lolos)
  verdict = "lolos" if lolos else "LANGGAR"
  print(f"  {nama:<{LEBAR_NAMA}} {keadaan:<{LEBAR_KEADAAN}} {verdict}")


def main():
  """Menilai seluruh syarat pada kebijakan, lalu memberi verdict akhirnya."""
  nama_file = sys.argv[1] if len(sys.argv) > 1 else FILE_KEBIJAKAN_BAWAAN
  kebijakan = baca_kebijakan(nama_file)
  print(f"  {'Pemeriksaan':<{LEBAR_NAMA}} {'Keadaan':<{LEBAR_KEADAAN}} "
        "Verdict")

  daftar_baris = []
  for jalur in kebijakan["alamat_diperiksa"]:
    daftar_baris.extend(nilai_header_wajib(kebijakan, jalur))
  daftar_baris.extend(nilai_atribut_cookie(kebijakan))
  daftar_baris.extend(nilai_cors(kebijakan))
  for baris in daftar_baris:
    cetak_baris(baris)

  jumlah_langgar = sum(1 for baris in daftar_baris if not baris[-1])
  if jumlah_langgar:
    print(f"\nGagal: {jumlah_langgar} syarat keamanan belum terpenuhi.")
    sys.exit(1)
  print("\nLolos: seluruh syarat keamanan terpenuhi.")


if __name__ == "__main__":
  main()
