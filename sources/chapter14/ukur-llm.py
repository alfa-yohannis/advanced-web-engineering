"""Mengukur fitur berbantuan LLM dari sisi browser: waktu, token, dan cache.

Empat skenario dikirim ke asisten.py, berperan sebagai browser. Untuk tiap
skenario dicatat lama sampai token pertama tiba, lama sampai jawaban selesai,
jumlah token yang dibayar ke model, dan apakah jawabannya dari cache.

Alat ukur ini tidak tahu kunci API model, dan memang tidak perlu tahu. Yang
memegangnya hanya asisten.py di sisi server.

Waktu model ditetapkan di model-tiruan.py, sehingga angka di sini
memperlihatkan akibat rancangan aplikasinya, bukan kecepatan model mana pun.
Cache asisten hidup selama prosesnya hidup, jadi asisten.py dinyalakan ulang
sebelum mengukur ulang.

Pemakaian (dari sources/chapter14, setelah model-tiruan.py dan asisten.py
menyala):
    python3 ukur-llm.py
"""

import json
import time
from http.client import HTTPConnection
from urllib.parse import quote

HOST = "127.0.0.1"
PORT_ASISTEN = 8121
BATAS_WAKTU_DETIK = 30
AWALAN_DATA = "data: "
DAFTAR_SKENARIO = [
    {"nama": "tanpa streaming", "stream": False,
     "pertanyaan": "Berapa lama buku dikirim ke Bandung?"},
    {"nama": "streaming", "stream": True,
     "pertanyaan": "Apa beda buku cetak dan buku elektronik?"},
    {"nama": "streaming, kalimat sama", "stream": True,
     "pertanyaan": "Apa beda buku cetak dan buku elektronik?"},
    {"nama": "streaming, kalimat lain", "stream": True,
     "pertanyaan": "Buku cetak dan buku elektronik, bedanya apa?"},
]
LEBAR_SKENARIO = 25


def kirim_pertanyaan(skenario):
  """Mengirim satu pertanyaan, lalu mengukur token pertama dan selesainya.

  Tanpa streaming, token pertama tiba bersamaan dengan seluruh jawaban,
  sehingga kedua angkanya sama. Dengan streaming, token pertama tiba begitu
  model mengeluarkannya.
  """
  jalur = (f"/tanya?q={quote(skenario['pertanyaan'])}"
           f"&stream={int(skenario['stream'])}")
  koneksi = HTTPConnection(HOST, PORT_ASISTEN, timeout=BATAS_WAKTU_DETIK)
  mulai = time.perf_counter()
  koneksi.request("GET", jalur)
  response = koneksi.getresponse()
  keadaan_cache = response.getheader("X-Cache", "-")
  if not skenario["stream"]:
    isi = json.loads(response.read())
    selesai_ms = (time.perf_counter() - mulai) * 1000
    koneksi.close()
    return selesai_ms, selesai_ms, isi["token_dibayar"], keadaan_cache
  pertama_ms = None
  for baris_mentah in response:
    baris = baris_mentah.decode().strip()
    if not baris.startswith(AWALAN_DATA):
      continue
    isi = json.loads(baris[len(AWALAN_DATA):])
    if pertama_ms is None:
      pertama_ms = (time.perf_counter() - mulai) * 1000
    if isi.get("selesai"):
      selesai_ms = (time.perf_counter() - mulai) * 1000
      koneksi.close()
      return pertama_ms, selesai_ms, isi["token_dibayar"], keadaan_cache
  raise RuntimeError("aliran berakhir sebelum jawaban selesai")


def main():
  """Menjalankan keempat skenario, lalu mencetak hasilnya sebagai tabel."""
  print(f"  {'Skenario':<{LEBAR_SKENARIO}} {'Token pertama':>13} "
        f"{'Selesai':>8} {'Token':>8} {'Cache':>6}")
  print(f"  {'':<{LEBAR_SKENARIO}} {'ms':>13} {'ms':>8} {'dibayar':>8}")
  for skenario in DAFTAR_SKENARIO:
    pertama_ms, selesai_ms, dibayar, keadaan_cache = kirim_pertanyaan(skenario)
    print(f"  {skenario['nama']:<{LEBAR_SKENARIO}} {pertama_ms:>13.1f} "
          f"{selesai_ms:>8.1f} {dibayar:>8} {keadaan_cache:>6}")


if __name__ == "__main__":
  main()
