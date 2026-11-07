"""Membandingkan dua cara membagi data ke beberapa node.

Seratus ribu kunci pelanggan dibagi ke empat node, lalu satu node ditambahkan.
Dua hal diukur. Pertama, berapa persen kunci yang harus pindah node karena
penambahan itu, karena tiap kunci yang pindah berarti data yang harus disalin
lewat jaringan. Kedua, seberapa berat node yang paling sibuk, sekali menurut
jumlah kunci dan sekali menurut jumlah permintaan, ketika sebagian kecil
pelanggan jauh lebih sering datang daripada yang lain.

Cara pertama modulo: node = hash(kunci) mod jumlah node. Cara kedua consistent
hashing: tiap node menempati sejumlah titik pada lingkaran hash, dan tiap
kunci menjadi milik titik pertama sesudah posisinya di lingkaran itu.

Hasilnya dihitung, bukan diukur dengan jam, sehingga sama persis pada tiap
komputer.

Pemakaian (dari sources/chapter14):
    python3 partisi.py
"""

import bisect
import hashlib

JUMLAH_KUNCI = 100_000
JUMLAH_NODE_AWAL = 4
JUMLAH_NODE_AKHIR = 5
# Popularitas pelanggan mengikuti sebaran Zipf: pelanggan peringkat r datang
# sebanding 1 / r^EKSPONEN_ZIPF. Eksponen 1 berarti pelanggan teratas datang
# dua kali lebih sering daripada peringkat kedua.
EKSPONEN_ZIPF = 1.0
BYTE_HASH = 8
PERSEN = 100
LEBAR_CARA = 29
DAFTAR_CARA = [
    {"nama": "modulo", "jenis": "modulo", "titik_per_node": 0},
    {"nama": "consistent hashing, 1 titik", "jenis": "lingkaran",
     "titik_per_node": 1},
    {"nama": "consistent hashing, 100 titik", "jenis": "lingkaran",
     "titik_per_node": 100},
]


def nilai_hash(teks):
  """Mengubah teks menjadi bilangan bulat 64 bit yang sama pada tiap proses.

  hash() bawaan Python tidak dipakai, karena nilainya diacak ulang tiap kali
  proses dinyalakan, sehingga node yang dipilih akan berubah-ubah.
  """
  ringkasan = hashlib.sha256(teks.encode()).digest()
  return int.from_bytes(ringkasan[:BYTE_HASH], "big")


def buat_lingkaran(jumlah_node, titik_per_node):
  """Membuat lingkaran hash: posisi titik yang terurut beserta node pemiliknya.

  Posisi titik hanya bergantung pada nomor node dan nomor titiknya. Karena
  itu menambah satu node tidak menggeser titik milik node lama, dan hanya
  kunci di dekat titik baru yang berpindah.
  """
  daftar_titik = sorted(
      (nilai_hash(f"node-{nomor_node}-titik-{nomor_titik}"), nomor_node)
      for nomor_node in range(jumlah_node)
      for nomor_titik in range(titik_per_node))
  posisi = [posisi_titik for posisi_titik, _ in daftar_titik]
  pemilik = [nomor_node for _, nomor_node in daftar_titik]
  return posisi, pemilik


def petakan(cara, jumlah_node, daftar_nilai):
  """Mengembalikan nomor node untuk tiap kunci menurut satu cara pembagian."""
  if cara["jenis"] == "modulo":
    return [nilai % jumlah_node for nilai in daftar_nilai]
  posisi, pemilik = buat_lingkaran(jumlah_node, cara["titik_per_node"])
  return [pemilik[bisect.bisect_right(posisi, nilai) % len(posisi)]
          for nilai in daftar_nilai]


def bagian_terberat(daftar_node, daftar_bobot, jumlah_node):
  """Menghitung persen bobot yang jatuh ke node paling berat."""
  bobot_per_node = [0.0] * jumlah_node
  for nomor_node, bobot in zip(daftar_node, daftar_bobot):
    bobot_per_node[nomor_node] += bobot
  return max(bobot_per_node) / sum(bobot_per_node) * PERSEN


def nilai_cara(cara, daftar_nilai, bobot_zipf):
  """Menghitung kunci yang pindah dan beban node terberat untuk satu cara."""
  sebelum = petakan(cara, JUMLAH_NODE_AWAL, daftar_nilai)
  sesudah = petakan(cara, JUMLAH_NODE_AKHIR, daftar_nilai)
  pindah = sum(1 for lama, baru in zip(sebelum, sesudah) if lama != baru)
  bobot_rata = [1.0] * len(daftar_nilai)
  return {
      "pindah": pindah / len(daftar_nilai) * PERSEN,
      "terberat_kunci": bagian_terberat(sesudah, bobot_rata, JUMLAH_NODE_AKHIR),
      "terberat_permintaan": bagian_terberat(sesudah, bobot_zipf,
                                             JUMLAH_NODE_AKHIR),
  }


def main():
  """Menghitung ketiga cara, lalu mencetak hasilnya sebagai tabel."""
  daftar_kunci = [f"pelanggan-{nomor:06d}" for nomor in range(1, JUMLAH_KUNCI + 1)]
  daftar_nilai = [nilai_hash(kunci) for kunci in daftar_kunci]
  bobot_zipf = [1 / peringkat ** EKSPONEN_ZIPF
                for peringkat in range(1, JUMLAH_KUNCI + 1)]
  print(f"  {JUMLAH_KUNCI} kunci, {JUMLAH_NODE_AWAL} node menjadi "
        f"{JUMLAH_NODE_AKHIR} node, ideal {PERSEN / JUMLAH_NODE_AKHIR:.1f}% "
        f"tiap node\n")
  print(f"  {'Cara':<{LEBAR_CARA}} {'Pindah':>7} {'Terberat, kunci':>15} "
        f"{'Terberat, permintaan':>20}")
  for cara in DAFTAR_CARA:
    hasil = nilai_cara(cara, daftar_nilai, bobot_zipf)
    print(f"  {cara['nama']:<{LEBAR_CARA}} {hasil['pindah']:>6.1f}% "
          f"{hasil['terberat_kunci']:>14.1f}% "
          f"{hasil['terberat_permintaan']:>19.1f}%")


if __name__ == "__main__":
  main()
