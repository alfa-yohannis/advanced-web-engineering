"""Aturan hak akses: siapa boleh melakukan apa, dan terhadap data siapa.

Dua model dipakai berdampingan agar bedanya terlihat. RBAC menjawab dari
peran saja, sedangkan ABAC ikut membaca sifat permintaannya: pemilik data,
tenant asal, dan tenant datanya.

File ini tidak menyentuh HTTP sama sekali, sehingga aturannya dapat diuji
langsung seperti harga.py pada Bab 6.

Pemakaian (dari sources/chapter10):
    python3 -c "import kebijakan; print(kebijakan.IZIN_PERAN)"
"""

# RBAC: tiap peran membawa daftar izin, dan izin itulah yang diperiksa,
# bukan nama perannya. Dengan begitu menambah peran baru tidak menuntut
# perubahan di tiap pemeriksaan.
IZIN_PERAN = {
    "admin": {"baca_pesanan", "baca_semua_pesanan", "baca_laporan"},
    "staf": {"baca_pesanan", "baca_semua_pesanan"},
    "pembeli": {"baca_pesanan"},
}


def punya_izin(peran, izin):
  """Memeriksa satu izin menurut peran, yaitu bentuk pemeriksaan RBAC."""
  return izin in IZIN_PERAN.get(peran, set())


def boleh_baca_pesanan(identitas, pesanan):
  """Memutuskan satu pesanan boleh dibaca atau tidak, secara ABAC.

  Tiga sifat ikut dibaca: tenant pemohon, tenant pesanan, dan pemiliknya.
  Mengembalikan pasangan (boleh, alasan), sehingga alasan penolakan dapat
  ikut diuji dan ikut dicatat.
  """
  if identitas["tenant"] != pesanan["tenant"]:
    return False, "tenant berbeda"
  if punya_izin(identitas["peran"], "baca_semua_pesanan"):
    return True, "peran boleh membaca seluruh pesanan tenantnya"
  if pesanan["pemilik"] == identitas["sub"]:
    return True, "pemohon adalah pemilik pesanan"
  return False, "bukan pemilik dan perannya tidak mencakup"


def saring_pesanan(identitas, daftar_pesanan):
  """Menyaring daftar pesanan menurut aturan yang sama.

  Penyaringan dilakukan di satu tempat, sehingga alamat daftar dan alamat
  rincian tidak dapat berbeda pendapat tentang siapa boleh melihat apa.
  """
  return [pesanan for pesanan in daftar_pesanan
          if boleh_baca_pesanan(identitas, pesanan)[0]]
