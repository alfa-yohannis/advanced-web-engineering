"""Komponen halaman katalog beserta token design system-nya.

Tiap komponen adalah satu fungsi yang mengembalikan potongan HTML, dan
komponen besar disusun dari komponen kecil. Dengan begitu batas tiap bagian
terlihat dari tanda tangan fungsinya, bukan dari kebiasaan penulisnya.

Seluruh nilai tampilan, yaitu warna dan jarak, ditulis sekali di TOKEN lalu
dipakai ulang. Itulah bentuk paling sederhana sebuah design system: satu
sumber nilai, bukan angka yang diketik ulang di tiap tempat.

Pemakaian (dari sources/chapter11):
    python3 -c "import komponen; print(len(komponen.DAFTAR_BUKU))"
"""

import html
import json

# Token design system. Mengubah satu baris di sini mengubah seluruh halaman,
# dan itulah gunanya nilai tampilan tidak ditulis langsung di komponen.
TOKEN = {
    "warna_utama": "#257147",
    "warna_teks": "#1a1a1a",
    "warna_garis": "#d8d8d8",
    "jarak_kecil": "4px",
    "jarak_sedang": "12px",
    "lebar_halaman": "720px",
}

JUDUL_DASAR = [
    "Rekayasa Web Lanjut",
    "Basis Data Terapan",
    "Jaringan untuk Pengembang",
    "Keamanan Aplikasi Web",
    "Pengantar Algoritma",
    "Arsitektur Perangkat Lunak",
]
# Jumlah buku menentukan besar halaman, dan besar halaman itulah yang
# membedakan biaya hidrasi penuh dari hidrasi selektif.
JUMLAH_BUKU_BAWAAN = 200


def buat_daftar(jumlah):
  """Menyusun daftar buku sebanyak jumlah yang diminta.

  Judulnya diulang dengan nomor jilid, sehingga halaman dapat dibesarkan
  tanpa menambah data baru, dan besarnya menjadi satu angka yang diatur.
  """
  daftar = []
  for nomor in range(1, jumlah + 1):
    judul = JUDUL_DASAR[(nomor - 1) % len(JUDUL_DASAR)]
    daftar.append({
        "id": nomor,
        "judul": f"{judul} Jilid {nomor}",
        "harga": 80000 + (nomor % 12) * 5000,
        "stok": nomor % 10,
    })
  return daftar


DAFTAR_BUKU = buat_daftar(JUMLAH_BUKU_BAWAAN)


def saring_daftar(daftar, kata):
  """Menyaring daftar di server, agar penyaringan jalan tanpa JavaScript."""
  if not kata:
    return daftar
  kata_kecil = kata.lower()
  return [buku for buku in daftar if kata_kecil in buku["judul"].lower()]


def cari_buku(daftar, id_buku):
  """Mencari satu buku berdasarkan id, atau None bila tidak ada."""
  for buku in daftar:
    if buku["id"] == id_buku:
      return buku
  return None


def gaya_halaman():
  """Menyusun gaya halaman dari token, bukan dari angka yang diketik ulang."""
  return (
      "<style>\n"
      f"  body {{ color: {TOKEN['warna_teks']}; max-width: "
      f"{TOKEN['lebar_halaman']}; margin: auto; font-family: sans-serif; }}\n"
      f"  .kartu {{ border: 1px solid {TOKEN['warna_garis']}; padding: "
      f"{TOKEN['jarak_sedang']}; margin: {TOKEN['jarak_kecil']} 0; }}\n"
      f"  .judul {{ color: {TOKEN['warna_utama']}; }}\n"
      f"  nav a {{ margin-right: {TOKEN['jarak_sedang']}; }}\n"
      "</style>"
  )


def kartu_buku(buku):
  """Menyusun satu kartu buku, yaitu komponen terkecil pada halaman ini.

  Atribut data-komponen dipakai skrip hidrasi penuh untuk menemukan seluruh
  bagian yang perlu dihidupkan, sehingga jumlahnya dapat dihitung.
  """
  judul = html.escape(buku["judul"])
  harga = f"Rp {buku['harga']:,}".replace(",", ".")
  alamat = f"/kerangka/buku/{buku['id']}"
  return (
      f'      <li class="kartu" data-komponen="kartu"'
      f' data-id="{buku["id"]}">\n'
      f'        <a class="judul" href="{alamat}">{judul}</a>\n'
      f'        <span class="harga">{harga}</span>\n'
      '        <button data-komponen="tombol" type="button">'
      "Tambah</button>\n"
      "      </li>"
  )


def daftar_buku(daftar):
  """Menyusun daftar kartu, yaitu komponen yang dirakit dari komponen lain."""
  isi = "\n".join(kartu_buku(buku) for buku in daftar)
  return f'    <ul id="daftar" data-komponen="daftar">\n{isi}\n    </ul>'


def penyaring(saringan):
  """Menyusun penyaring sebagai form biasa, bukan sebagai kotak yang kosong.

  Form dengan metode GET sudah berfungsi sebelum satu baris JavaScript pun
  berjalan: penekanan tombol Saring mengirim ulang permintaan, dan server
  yang menyaring. Pulau penyaring hanya mempercepatnya menjadi tanpa muat
  ulang. Itulah bentuk progressive enhancement yang paling murah.
  """
  nilai = html.escape(saringan)
  return (
      '    <form class="penyaring" method="get" action="">\n'
      '      <label for="saring">Saring judul</label>\n'
      f'      <input id="saring" name="saring" value="{nilai}"\n'
      '        data-pulau="penyaring" data-komponen="penyaring" />\n'
      '      <button type="submit">Saring</button>\n'
      "    </form>"
  )


def keranjang():
  """Menyusun penghitung keranjang, bagian interaktif yang kedua."""
  return ('    <p data-pulau="keranjang" data-komponen="keranjang">'
          'Keranjang: <span id="jumlah">0</span> buku</p>')


def state_penuh(daftar):
  """Menyusun state yang dikirim bila seluruh komponen akan dihidupkan.

  Hidrasi penuh membangun ulang tiap komponen di browser, dan untuk itu ia
  butuh data tiap komponen. Karena itu data seluruh kartu ikut dikirim di
  dalam halaman, selain sudah tercetak sebagai HTML.
  """
  return {
      "buku": {str(buku["id"]): buku for buku in daftar},
      "keranjang": 0,
      "saringan": "",
  }


def state_pulau():
  """Menyusun state yang dikirim bila hanya pulau yang akan dihidupkan.

  Pulau tidak membangun ulang kartu, sehingga data kartu tidak diperlukan di
  browser. Yang tersisa hanya milik kedua pulau itu sendiri.
  """
  return {"keranjang": 0, "saringan": ""}


def blok_state(state):
  """Menyusun blok state sebagai JSON di dalam halaman.

  Blok ini adalah cara server menitipkan state ke browser. Besarnya ikut
  terhitung sebagai ukuran halaman, dan di sanalah selisih kedua varian
  mulai terlihat sebelum satu baris skrip pun berjalan.
  """
  isi = json.dumps(state, separators=(",", ":"))
  return (f'    <script id="state" type="application/json">{isi}'
          "</script>")


def tata_letak(judul_halaman, isi_badan, skrip):
  """Menyusun kerangka halaman yang dipakai seluruh varian.

  Kedua varian hidrasi memakai kerangka dan markup kartu yang sama persis,
  dan hanya berbeda pada blok state serta nama file skripnya. Dengan begitu
  selisih yang terukur benar-benar berasal dari cara hidrasinya.
  """
  return (
      "<!DOCTYPE html>\n<html lang=\"id\">\n  <head>\n"
      "    <meta charset=\"utf-8\" />\n"
      f"    <title>{judul_halaman}</title>\n"
      f"  {gaya_halaman()}\n"
      f'    <script src="/aset/{skrip}" defer></script>\n'
      "  </head>\n  <body>\n"
      f"    <h1>{judul_halaman}</h1>\n"
      '    <p id="laporan">Hidrasi belum berjalan.</p>\n'
      f"{isi_badan}\n"
      "  </body>\n</html>\n"
  )


def navigasi():
  """Menyusun navigasi kerangka sebagai tautan biasa.

  Tautannya memakai alamat sungguhan, sehingga tetap dapat dibuka langsung,
  dibagikan, dan dibuka di tab baru. Router hanya mencegah muat ulangnya.
  """
  return (
      '    <nav>\n'
      '      <a href="/kerangka/katalog">Katalog</a>\n'
      '      <a href="/kerangka/buku/3">Buku 3</a>\n'
      '      <a href="/kerangka/buku/99999">Buku yang tidak ada</a>\n'
      '      <a href="/kerangka/gagal">Bagian yang gagal</a>\n'
      "    </nav>"
  )


def fragmen_katalog(daftar, saringan):
  """Menyusun fragmen katalog, yaitu isi wilayah tanpa kerangkanya."""
  return "\n".join([penyaring(saringan), keranjang(), daftar_buku(daftar)])


def fragmen_buku(buku):
  """Menyusun fragmen halaman satu buku."""
  judul = html.escape(buku["judul"])
  harga = f"Rp {buku['harga']:,}".replace(",", ".")
  return (
      f'    <article class="kartu" data-komponen="rincian">\n'
      f"      <h2>{judul}</h2>\n"
      f"      <p>Harga {harga}, stok {buku['stok']}.</p>\n"
      '      <p><a href="/kerangka/katalog">Kembali ke katalog</a></p>\n'
      "    </article>"
  )


def fragmen_kosong(pesan):
  """Menyusun fragmen untuk alamat yang isinya tidak ada.

  Alamat yang salah menghasilkan halaman yang tetap utuh, bukan wilayah yang
  kosong. Inilah batas error yang paling sederhana: satu fragmen pengganti.
  """
  return ('    <article class="kartu" data-komponen="rincian">\n'
          f"      <h2>{html.escape(pesan)}</h2>\n"
          '      <p><a href="/kerangka/katalog">Kembali ke katalog</a></p>\n'
          "    </article>")


def kerangka(isi_wilayah):
  """Menyusun application shell, yaitu bagian yang tidak berubah saat pindah.

  Judul dan navigasi dikirim sekali. Yang diganti saat berpindah halaman
  hanya isi wilayah, dan itulah yang membuat perpindahan jauh lebih kecil
  daripada memuat ulang seluruh dokumen.
  """
  isi = "\n".join([
      blok_state(state_pulau()),
      navigasi(),
      '    <main id="wilayah" aria-live="polite">',
      isi_wilayah,
      "    </main>",
  ])
  return tata_letak("Katalog", isi, "rute.js")
