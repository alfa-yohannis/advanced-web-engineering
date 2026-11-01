"""Antrean pekerjaan sederhana dengan pengiriman at-least-once.

Antreannya satu file JSON, dan itu memang bukan antrean untuk produksi.
Yang ditirukan di sini hanya sifat-sifat yang menentukan cara menulis
consumer: pesan tidak hilang ketika worker-nya mati, pesan yang belum
di-ack akan dikirim ulang, dan pengiriman ulang itu memakai jeda yang
berlipat.

Dua catatan ikut disimpan. Daftar pesan memuat pekerjaan yang belum
selesai, dan buku diproses memuat id pekerjaan yang sudah pernah
dikerjakan, sehingga consumer dapat menolak duplikat.

Modul ini diimpor, bukan dijalankan langsung:
    python3 worker.py
"""

import json
import time
from pathlib import Path

FILE_ANTREAN = Path(__file__).parent / "antrean.json"
# Jeda percobaan pertama, lalu dilipatkan dua tiap percobaan berikutnya.
# Nilainya kecil agar seluruh daur terlihat dalam satu latihan.
JEDA_DASAR_DETIK = 0.5
BATAS_PERCOBAAN = 5


def muat():
  """Membaca keadaan antrean, atau keadaan kosong bila filenya belum ada."""
  if not FILE_ANTREAN.exists():
    return {"pesan": [], "diproses": [], "nomor_terakhir": 0}
  return json.loads(FILE_ANTREAN.read_text(encoding="utf-8"))


def simpan(keadaan):
  """Menuliskan keadaan antrean ke file."""
  FILE_ANTREAN.write_text(json.dumps(keadaan, indent=2), encoding="utf-8")


def kosongkan():
  """Mengosongkan antrean beserta buku diproses, dipakai sebelum mengukur."""
  simpan({"pesan": [], "diproses": [], "nomor_terakhir": 0})


def jeda_backoff(percobaan):
  """Menghitung jeda sebelum percobaan berikutnya, berlipat dua tiap kali.

  Jeda yang berlipat menahan worker dari membanjiri tujuan yang sedang
  bermasalah. Percobaan pertama memakai jeda dasar, yang kedua dua kali,
  yang ketiga empat kali, dan seterusnya.
  """
  return JEDA_DASAR_DETIK * (2 ** max(0, percobaan - 1))


def kirim(jenis, isi):
  """Memasukkan satu pekerjaan ke antrean, lalu mengembalikan idnya."""
  keadaan = muat()
  keadaan["nomor_terakhir"] += 1
  id_pesan = f"kerja-{keadaan['nomor_terakhir']:04d}"
  keadaan["pesan"].append({
      "id": id_pesan,
      "jenis": jenis,
      "isi": isi,
      "percobaan": 0,
      "siap_pada": time.time(),
  })
  simpan(keadaan)
  return id_pesan


def ambil(sekarang):
  """Mengambil satu pekerjaan yang sudah waktunya dikerjakan.

  Pekerjaan yang diambil tidak langsung hilang dari antrean. Waktu siapnya
  digeser sejauh jeda backoff, sehingga pekerjaan itu kembali muncul bila
  worker-nya mati sebelum memanggil selesai. Di sanalah sifat at-least-once
  berasal: pekerjaan dapat terkirim lebih dari sekali, dan tidak pernah
  hilang tanpa dikerjakan.
  """
  keadaan = muat()
  for pesan in keadaan["pesan"]:
    if pesan["siap_pada"] <= sekarang:
      pesan["percobaan"] += 1
      pesan["siap_pada"] = sekarang + jeda_backoff(pesan["percobaan"])
      simpan(keadaan)
      return dict(pesan)
  return None


def selesai(id_pesan):
  """Menghapus satu pekerjaan dari antrean, yaitu meng-ack pekerjaan itu."""
  keadaan = muat()
  keadaan["pesan"] = [pesan for pesan in keadaan["pesan"]
                      if pesan["id"] != id_pesan]
  simpan(keadaan)


def sudah_diproses(id_pesan):
  """Memeriksa apakah satu pekerjaan sudah pernah dikerjakan sampai tuntas."""
  return id_pesan in muat()["diproses"]


def tandai_diproses(id_pesan):
  """Mencatat satu pekerjaan sebagai sudah dikerjakan.

  Catatan ini yang membuat consumer menjadi idempoten: pengiriman kedua
  dikenali, lalu dilewati, tanpa mengulang akibat yang sudah terjadi.
  """
  keadaan = muat()
  if id_pesan not in keadaan["diproses"]:
    keadaan["diproses"].append(id_pesan)
  simpan(keadaan)


def ringkas():
  """Merangkum keadaan antrean menjadi angka yang mudah dicetak."""
  keadaan = muat()
  return {"tersisa": len(keadaan["pesan"]),
          "diproses": len(keadaan["diproses"])}
