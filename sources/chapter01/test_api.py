"""Uji API lewat HTTP sungguhan, dengan repository SQLite di memori.

Server dinyalakan di utas terpisah pada port yang dipilih sistem operasi,
sehingga uji ini tidak berebut port 8050 dengan aplikasi yang mungkin sedang
menyala. Yang diperiksa di sini hanya hal yang tidak dapat diperiksa uji
unit: status HTTP, bentuk JSON, dan penerjemahan kesalahan oleh route.

Pemakaian (dari sources/chapter01):
    python3 -m unittest -v test_api
"""

import json
import threading
import unittest
from http.client import HTTPConnection

import aplikasi

BATAS_WAKTU_DETIK = 5
PORT_PILIHAN_SISTEM = 0
# Selang server memeriksa permintaan berhenti. Nilai bawaannya 0,5 detik,
# sehingga tanpa setelan ini seluruh uji API menunggu setengah detik hanya
# untuk mematikan server, bukan untuk menguji apa pun.
JEDA_PERIKSA_BERHENTI_DETIK = 0.01
HARGA_CONTOH_RUPIAH = 85_000
STOK_CONTOH = 4


class UjiApiKatalog(unittest.TestCase):
  """Memeriksa keempat alamat API beserta status HTTP-nya."""

  @classmethod
  def setUpClass(cls):
    """Menyalakan satu server untuk seluruh uji di kelas ini."""
    cls.server = aplikasi.buat_server(port=PORT_PILIHAN_SISTEM)
    cls.port = cls.server.server_address[1]
    cls.utas = threading.Thread(
        target=cls.server.serve_forever,
        kwargs={"poll_interval": JEDA_PERIKSA_BERHENTI_DETIK}, daemon=True)
    cls.utas.start()

  @classmethod
  def tearDownClass(cls):
    """Mematikan server dan melepas port-nya."""
    cls.server.shutdown()
    cls.server.server_close()

  def kirim(self, metode, jalur, isi=None):
    """Mengirim satu permintaan, lalu mengembalikan status dan isi JSON-nya."""
    koneksi = HTTPConnection(aplikasi.HOST, self.port, timeout=BATAS_WAKTU_DETIK)
    badan = isi if isinstance(isi, bytes) else json.dumps(isi).encode()
    if isi is None:
      koneksi.request(metode, jalur)
    else:
      koneksi.request(metode, jalur, body=badan,
                      headers={"Content-Type": "application/json"})
    response = koneksi.getresponse()
    hasil = response.status, json.loads(response.read())
    koneksi.close()
    return hasil

  def test_tanda_hidup_menjawab_200(self):
    """Alamat /sehat menjawab 200, dipakai smoke test aplikasi."""
    status, isi = self.kirim("GET", "/sehat")
    self.assertEqual((status, isi["status"]), (200, "sehat"))

  def test_tambah_buku_menjawab_201(self):
    """Buku yang sah disimpan dan dijawab 201 beserta nomornya."""
    status, isi = self.kirim("POST", "/buku", {
        "judul": "Pemrograman Web", "harga": HARGA_CONTOH_RUPIAH,
        "stok": STOK_CONTOH})
    self.assertEqual(status, 201)
    self.assertIn("nomor", isi)

  def test_buku_tidak_sah_menjawab_400(self):
    """Kesalahan validasi dari service diterjemahkan menjadi 400."""
    status, isi = self.kirim("POST", "/buku", {
        "judul": "Pemrograman Web", "harga": 0, "stok": STOK_CONTOH})
    self.assertEqual(status, 400)
    self.assertIn("harga", isi["pesan"])

  def test_json_rusak_menjawab_400(self):
    """Isi yang bukan JSON ditolak sebelum menyentuh service."""
    status, _ = self.kirim("POST", "/buku", b"{judul: tanpa kutip}")
    self.assertEqual(status, 400)

  def test_buku_tidak_ada_menjawab_404(self):
    """BukuTidakDitemukan dari service diterjemahkan menjadi 404."""
    status, _ = self.kirim("GET", "/buku/9999")
    self.assertEqual(status, 404)

  def test_alamat_tidak_dikenal_menjawab_404(self):
    """Alamat di luar keempat alamat API dijawab 404."""
    status, _ = self.kirim("GET", "/rahasia")
    self.assertEqual(status, 404)


if __name__ == "__main__":
  unittest.main()
