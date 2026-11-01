"""Background worker yang mengerjakan antrean dan mengirimkannya ke webhook.

Worker ini idempoten: sebelum mengerjakan satu pesan, ia memeriksa buku
diproses lebih dahulu. Pemeriksaan itu diperlukan karena antreannya bersifat
at-least-once, sehingga satu pesan dapat tiba dua kali, misalnya ketika
worker mati sesudah mengirim tetapi sebelum meng-ack.

Satu jenis pekerjaan, yaitu crash-setelah-kirim, memang menirukan kematian
itu: webhooknya dikirim, pesannya ditandai diproses, lalu worker berhenti
tanpa meng-ack. Pengiriman kedua dipakai untuk membuktikan duplikatnya
tertahan.

Pemakaian (dari sources/chapter13, setelah webhook.py menyala):
    python3 worker.py
"""

import json
import time
from http.client import HTTPConnection

import antrean

HOST_WEBHOOK = "127.0.0.1"
PORT_WEBHOOK = 8102
BATAS_WAKTU_DETIK = 5
JENIS_CRASH = "crash-setelah-kirim"
JEDA_PUTARAN_DETIK = 0.1


def kirim_webhook(pesan):
  """Mengirim satu pesan ke webhook, lalu mengembalikan statusnya."""
  badan = json.dumps({"id": pesan["id"], "jenis": pesan["jenis"],
                      "isi": pesan["isi"]}).encode()
  koneksi = HTTPConnection(HOST_WEBHOOK, PORT_WEBHOOK,
                           timeout=BATAS_WAKTU_DETIK)
  koneksi.request("POST", "/webhook", body=badan,
                  headers={"Content-Type": "application/json",
                           "Content-Length": str(len(badan))})
  response = koneksi.getresponse()
  response.read()
  status = response.status
  koneksi.close()
  return status


def kerjakan(pesan, tirukan_crash):
  """Mengerjakan satu pesan, lalu mengembalikan keterangan hasilnya.

  Urutannya penting. Pemeriksaan duplikat dilakukan paling dahulu, sebelum
  webhooknya dikirim, karena itulah satu-satunya tempat duplikat masih dapat
  ditahan tanpa akibat.
  """
  if antrean.sudah_diproses(pesan["id"]):
    antrean.selesai(pesan["id"])
    return "duplikat ditahan"
  status = kirim_webhook(pesan)
  if status != 200:
    return f"gagal, webhook {status}, dicoba lagi nanti"
  antrean.tandai_diproses(pesan["id"])
  if pesan["jenis"] == JENIS_CRASH and tirukan_crash:
    return "terkirim, worker mati sebelum ack"
  antrean.selesai(pesan["id"])
  return "terkirim dan di-ack"


def satu_putaran(tirukan_crash):
  """Mengerjakan seluruh pesan yang sudah waktunya, lalu merangkumnya."""
  hasil = []
  while True:
    pesan = antrean.ambil(time.time())
    if pesan is None:
      return hasil
    hasil.append({"id": pesan["id"], "jenis": pesan["jenis"],
                  "percobaan": pesan["percobaan"],
                  "hasil": kerjakan(pesan, tirukan_crash)})


def main():
  """Menjalankan worker terus-menerus sampai dihentikan dengan Ctrl+C."""
  print(f"Worker menyala, webhook di http://{HOST_WEBHOOK}:{PORT_WEBHOOK}"
        "  (Ctrl+C untuk berhenti)")
  while True:
    for satu in satu_putaran(True):
      print(f"  {satu['id']} percobaan {satu['percobaan']}: {satu['hasil']}")
    time.sleep(JEDA_PUTARAN_DETIK)


if __name__ == "__main__":
  main()
