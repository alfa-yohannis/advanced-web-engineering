"""Fixture bersama untuk pengujian integrasi dan pengujian kontrak.

Basis datanya sungguhan, berjalan di container, dan tiap pengujian diakhiri
rollback sehingga data uji kembali seperti semula. Aplikasinya dinyalakan di
utas terpisah pada port bebas, sehingga pengujian tidak bentrok dengan
aplikasi yang sedang dijalankan tangan di port 8020.

File conftest.py dikenali pytest secara otomatis, sehingga tidak perlu
di-import dari file pengujian.
"""

import threading
from http.server import ThreadingHTTPServer

import pytest

import aplikasi
import basis_data

SQL_PESANAN_BERITEM = """
    SELECT pesanan_id
    FROM item_pesanan
    GROUP BY pesanan_id
    HAVING count(*) >= 2
    ORDER BY pesanan_id
    LIMIT 1
"""


@pytest.fixture()
def koneksi():
  """Memberi satu koneksi basis data yang dibatalkan sesudah pengujian.

  Rollback membuat pengujian dapat menulis tanpa mengotori data uji, sehingga
  urutan pengujian tidak lagi menentukan hasilnya.
  """
  with basis_data.buka_koneksi() as koneksi_uji:
    yield koneksi_uji
    koneksi_uji.rollback()


@pytest.fixture()
def id_pesanan_uji(koneksi):
  """Mencari satu pesanan yang punya minimal dua item.

  Idnya dicari dari data, bukan ditulis tetap di kode, sehingga pengujian
  tetap jalan walaupun data uji dibangkitkan ulang dengan id yang berbeda.
  """
  penghitung = basis_data.PenghitungQuery()
  baris = basis_data.jalankan_query(koneksi, SQL_PESANAN_BERITEM, (),
                                    penghitung)
  if not baris:
    pytest.skip("data uji tidak memuat pesanan dengan dua item atau lebih")
  return baris[0][0]


@pytest.fixture(scope="session")
def alamat_aplikasi():
  """Menyalakan aplikasi di utas terpisah selama satu sesi pengujian.

  Port 0 meminta sistem memilih port yang bebas, sehingga pengujian dapat
  berjalan bersamaan dengan aplikasi yang sedang dipakai mengetes tangan.
  """
  server = ThreadingHTTPServer((aplikasi.HOST, 0), aplikasi.PenanganPesanan)
  utas = threading.Thread(target=server.serve_forever, daemon=True)
  utas.start()
  yield server.server_address
  server.shutdown()
  server.server_close()
