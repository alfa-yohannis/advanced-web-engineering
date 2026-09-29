"""Pengujian kontrak: memeriksa response HTTP terhadap JSON Schema.

Pengujian integrasi memeriksa isi response dari dalam proses. Pengujian di file
ini memeriksanya dari luar, lewat HTTP, dan menilainya dengan satu file kontrak
di kontrak/pesanan.schema.json. Yang diperiksa bukan satu nilai tertentu,
melainkan bentuknya: field apa saja yang wajib ada, tipenya apa, dan nilai apa
saja yang boleh muncul.

Kontrak yang dipisahkan seperti ini dapat dibaca kedua pihak. Klien tahu apa
yang boleh diandalkan, dan server tahu apa yang tidak boleh diubah tanpa
menaikkan versi.

Status error ikut diperiksa, karena bentuk kegagalan juga bagian dari kontrak.

Pemakaian (dari sources/chapter06, setelah docker compose up -d):
    source ../.venv/bin/activate
    pytest test_kontrak.py
"""

import json
from http.client import HTTPConnection
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

FILE_SKEMA = Path(__file__).parent / "kontrak" / "pesanan.schema.json"
BATAS_WAKTU_DETIK = 5
QUERY_JALUR_SEHAT = 2
ID_BUKAN_ANGKA = "dua-belas"
# Lebih besar daripada id terbesar pada data uji, sehingga pasti tidak ada.
ID_PESANAN_TIDAK_ADA = 99_000_000
STATUS_PERMINTAAN_SALAH = 400
STATUS_TIDAK_DITEMUKAN = 404


@pytest.fixture(scope="session")
def pemeriksa_kontrak():
  """Membaca file kontrak sekali, lalu memakainya untuk seluruh pengujian.

  Kontraknya disimpan sebagai file terpisah, bukan ditulis di dalam kode
  pengujian, sehingga dapat dikirim kepada pemakai API tanpa membagikan
  pengujiannya.
  """
  skema = json.loads(FILE_SKEMA.read_text(encoding="utf-8"))
  Draft202012Validator.check_schema(skema)
  return Draft202012Validator(skema)


def minta_alamat(alamat_aplikasi, jalur):
  """Mengirim satu permintaan GET, lalu mengembalikan status, header, dan isinya.

  Isi response dikembalikan sebagai teks apa adanya, sehingga pengujian yang
  memeriksa response bukan JSON pun tetap dapat memakai fungsi ini.
  """
  host, port = alamat_aplikasi
  koneksi = HTTPConnection(host, port, timeout=BATAS_WAKTU_DETIK)
  koneksi.request("GET", jalur)
  response = koneksi.getresponse()
  isi = response.read().decode()
  header = dict(response.getheaders())
  koneksi.close()
  return response.status, header, isi


def test_response_jalur_sehat_memenuhi_kontrak(alamat_aplikasi,
                                               pemeriksa_kontrak,
                                               id_pesanan_uji):
  """Response jalur sehat memenuhi seluruh butir kontraknya."""
  status, _, isi = minta_alamat(alamat_aplikasi,
                                f"/api/pesanan/{id_pesanan_uji}")
  assert status == 200
  pemeriksa_kontrak.validate(json.loads(isi))


def test_response_jalur_n_plus_1_memenuhi_kontrak_yang_sama(
    alamat_aplikasi, pemeriksa_kontrak, id_pesanan_uji):
  """Jalur N+1 memenuhi kontrak yang sama persis.

  Inilah batas kemampuan pengujian kontrak: bentuk response tidak berubah
  walaupun jumlah querynya berlipat. Cacat itu hanya terbaca dari header
  X-Query-Count, bukan dari isi response.
  """
  status, _, isi = minta_alamat(alamat_aplikasi,
                                f"/api/pesanan-n1/{id_pesanan_uji}")
  assert status == 200
  pemeriksa_kontrak.validate(json.loads(isi))


def test_isi_response_kedua_jalur_sama_lewat_http(alamat_aplikasi,
                                                  id_pesanan_uji):
  """Dilihat dari luar, kedua jalur mengirim byte JSON yang sama."""
  _, _, isi_sehat = minta_alamat(alamat_aplikasi,
                                 f"/api/pesanan/{id_pesanan_uji}")
  _, _, isi_n1 = minta_alamat(alamat_aplikasi,
                              f"/api/pesanan-n1/{id_pesanan_uji}")
  assert json.loads(isi_sehat) == json.loads(isi_n1)


def test_header_query_count_jalur_sehat_tetap_dua(alamat_aplikasi,
                                                  id_pesanan_uji):
  """Jalur sehat melaporkan dua query lewat header X-Query-Count."""
  _, header, _ = minta_alamat(alamat_aplikasi,
                              f"/api/pesanan/{id_pesanan_uji}")
  assert int(header["X-Query-Count"]) == QUERY_JALUR_SEHAT


def test_header_query_count_jalur_n_plus_1_lebih_besar(alamat_aplikasi,
                                                       id_pesanan_uji):
  """Jalur N+1 melaporkan dua query ditambah satu untuk tiap itemnya.

  Angka inilah yang dinilai gate mutu, karena terbaca dari luar tanpa membaca
  kode aplikasinya.
  """
  _, header, isi = minta_alamat(alamat_aplikasi,
                                f"/api/pesanan-n1/{id_pesanan_uji}")
  jumlah_item = len(json.loads(isi)["item"])
  assert int(header["X-Query-Count"]) == QUERY_JALUR_SEHAT + jumlah_item


def test_id_bukan_angka_dijawab_400(alamat_aplikasi):
  """Permintaan yang salah bentuk ditolak sebelum menyentuh basis data.

  Status 400 menyatakan kesalahan ada di pemanggilnya, dan header
  X-Query-Count bernilai nol membuktikan basis datanya memang tidak dipanggil.
  """
  status, header, isi = minta_alamat(alamat_aplikasi,
                                     f"/api/pesanan/{ID_BUKAN_ANGKA}")
  assert status == STATUS_PERMINTAAN_SALAH
  assert int(header["X-Query-Count"]) == 0
  assert "pesan" in json.loads(isi)


def test_id_tidak_ada_dijawab_404(alamat_aplikasi):
  """Id yang sah tetapi tidak ada dijawab 404, sesudah satu query.

  Bedanya dengan 400 penting: bentuk permintaannya benar, hanya datanya yang
  tidak ada, sehingga satu query memang harus dijalankan lebih dahulu.
  """
  status, header, isi = minta_alamat(alamat_aplikasi,
                                     f"/api/pesanan/{ID_PESANAN_TIDAK_ADA}")
  assert status == STATUS_TIDAK_DITEMUKAN
  assert int(header["X-Query-Count"]) == 1
  assert "pesan" in json.loads(isi)


def test_kontrak_menolak_response_yang_kehilangan_field(pemeriksa_kontrak,
                                                        alamat_aplikasi,
                                                        id_pesanan_uji):
  """Kontraknya benar-benar menolak, bukan sekadar meloloskan apa saja.

  Pengujian kontrak yang tidak pernah dapat gagal tidak membuktikan apa pun.
  Karena itu satu field wajib dibuang dari response yang sungguhan, lalu
  penolakannya diperiksa.
  """
  _, _, isi = minta_alamat(alamat_aplikasi,
                           f"/api/pesanan/{id_pesanan_uji}")
  response_cacat = json.loads(isi)
  del response_cacat["pelanggan"]
  with pytest.raises(ValidationError):
    pemeriksa_kontrak.validate(response_cacat)
