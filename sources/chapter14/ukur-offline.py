"""Membuktikan halaman tetap tampil ketika server mati, berkat service worker.

Empat kunjungan dibuat dengan Chrome tanpa jendela, masing-masing sebagai
proses Chrome baru, seperti browser yang ditutup lalu dibuka lagi. Dua yang
pertama terjadi ketika server hidup dan memakai satu profil yang sama. Sesudah
itu servernya dimatikan. Kunjungan ketiga memakai profil yang sama, sedangkan
kunjungan keempat memakai profil baru, yaitu pengguna yang belum pernah
membuka halaman ini.

Untuk tiap kunjungan dicatat jumlah buku yang tampil, asal datanya, keadaan
service worker ketika halaman mulai, lama sampai katalog tampil, dan jumlah
permintaan yang sampai ke server. Chrome dikendalikan lewat DevTools Protocol,
sehingga alat ukur menunggu sampai service worker benar-benar siap, bukan
menebak lamanya.

Skrip ini menyalakan dan mematikan sendiri aplikasinya, karena yang diukur
justru keadaan ketika servernya mati. Seluruhnya di 127.0.0.1, dan sifatnya
mengamati, bukan membebani.

Pemakaian (dari sources/chapter14):
    python3 ukur-offline.py
"""

import json
import tempfile
from http.client import HTTPConnection

import chrome_pipa
import pengukur

HOST = "127.0.0.1"
PORT = 8120
ALAMAT = f"http://{HOST}:{PORT}/"
BATAS_WAKTU_DETIK = 10
JUMLAH_KUNJUNGAN_DARING = 2
# Ringkasan keadaan halaman, dihitung di dalam halaman lalu dibawa pulang.
UNGKAPAN_RINGKASAN = (
    "({buku: document.querySelectorAll('li.buku').length,"
    " sumber: document.body.dataset.sumber,"
    " serviceWorker: document.body.dataset.serviceWorker,"
    " tampilMs: Number(document.body.dataset.tampilMs || 0)})"
)
UNGKAPAN_SUMBER_TERCATAT = "document.body && document.body.dataset.sumber"
UNGKAPAN_SERVICE_WORKER_SIAP = "document.body.dataset.serviceWorkerSiap"
LEBAR_KUNJUNGAN = 15
LEBAR_SUMBER = 9
LEBAR_KEADAAN = 13


def kunjungi(direktori_profil):
  """Membuka halaman dengan satu proses Chrome baru, lalu meringkas hasilnya.

  Kunjungan baru dianggap selesai sesudah katalog tampil dan service worker
  siap. Bila navigasinya gagal karena tidak ada yang menjawab, teks error
  dari Chrome dilaporkan sebagai asal datanya.
  """
  chrome = chrome_pipa.ChromeLewatPipa(direktori_profil)
  try:
    galat = chrome.buka(ALAMAT)
    if galat:
      return {"buku": 0, "sumber": "gagal", "serviceWorker": "-",
              "tampilMs": 0, "galat": galat}
    chrome.tunggu(UNGKAPAN_SUMBER_TERCATAT)
    chrome.tunggu(UNGKAPAN_SERVICE_WORKER_SIAP)
    return chrome.nilai(UNGKAPAN_RINGKASAN)
  finally:
    chrome.tutup()


def jumlah_permintaan_server():
  """Menanyakan berapa permintaan yang sudah sampai ke server sejauh ini."""
  koneksi = HTTPConnection(HOST, PORT, timeout=BATAS_WAKTU_DETIK)
  koneksi.request("GET", "/statistik")
  jumlah = json.loads(koneksi.getresponse().read())["permintaan"]
  koneksi.close()
  return jumlah


def cetak_baris(nama, server_hidup, hasil, permintaan):
  """Mencetak satu baris hasil kunjungan, ditambah teks error bila ada."""
  server = "hidup" if server_hidup else "down"
  tampil = f"{hasil['tampilMs']:.0f}" if hasil["tampilMs"] else "-"
  print(f"  {nama:<{LEBAR_KUNJUNGAN}} {server:<6} {hasil['buku']:>4}  "
        f"{hasil['sumber']:<{LEBAR_SUMBER}} "
        f"{hasil['serviceWorker']:<{LEBAR_KEADAAN}} {tampil:>9} "
        f"{permintaan:>9}")
  if hasil.get("galat"):
    print(f"  {'':<{LEBAR_KUNJUNGAN}} Chrome: {hasil['galat']}")


def main():
  """Menjalankan keempat kunjungan, lalu mencetak hasilnya sebagai tabel."""
  print(f"  {'Kunjungan':<{LEBAR_KUNJUNGAN}} {'Server':<6} {'Buku':>4}  "
        f"{'Sumber':<{LEBAR_SUMBER}} {'Saat mulai':<{LEBAR_KEADAAN}} "
        f"{'Tampil ms':>9} {'Ke server':>9}")
  with tempfile.TemporaryDirectory() as profil_lama, \
       tempfile.TemporaryDirectory() as profil_baru:
    server = pengukur.nyalakan("aplikasi.py")
    try:
      pengukur.tunggu_port(PORT)
      sebelumnya = 0
      for urutan in range(1, JUMLAH_KUNJUNGAN_DARING + 1):
        hasil = kunjungi(profil_lama)
        sekarang = jumlah_permintaan_server()
        nama = f"{urutan}, profil " + ("baru" if urutan == 1 else "sama")
        cetak_baris(nama, True, hasil, sekarang - sebelumnya)
        sebelumnya = sekarang
    finally:
      pengukur.matikan([server])
    cetak_baris("3, profil sama", False, kunjungi(profil_lama), 0)
    cetak_baris("4, profil baru", False, kunjungi(profil_baru), 0)


if __name__ == "__main__":
  main()
