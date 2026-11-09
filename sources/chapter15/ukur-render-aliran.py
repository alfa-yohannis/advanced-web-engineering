"""Mengukur biaya render ulang jawaban yang dialirkan, di Chrome tanpa jendela.

Ketiga frontend RAG merender ulang seluruh jawaban tiap kali satu token tiba:
teks dikumpulkan, diurai marked, dibersihkan DOMPurify, dipasang lewat
innerHTML, lalu penanda sitasi diganti chip. render-aliran.js mengulang
langkah yang sama di halaman uji, memakai marked dan DOMPurify milik
repositori yang diukur, dan skrip ini meringkas lama tiap pembaruan.

Jawaban disusun dari jawaban-contoh.md, diulang sampai panjangnya tercapai,
lalu dipotong tiap 4 karakter. Angka 4 ditetapkan sebagai pendekatan panjang
satu token, bukan diukur dari tokenizer model mana pun.

Pengukuran ini bersifat mengamati. Halaman uji dibuka dari disk lokal, dan
tidak ada request ke layanan mana pun.

Cara menjalankan, dari sources/chapter15 dengan venv aktif:
    python3 ukur-render-aliran.py rag/exim
    python3 ukur-render-aliran.py rag/exim 5
Angka kedua mengganti jumlah ulangan, berguna untuk mencoba skripnya.
"""

import html
import json
import re
import sys
import tempfile
from pathlib import Path

from pengukur import (baca_komit, baca_versi_chrome, buka_halaman_lokal,
                      cari_chrome, ringkas_sebaran)

DAFTAR_PANJANG_TOKEN = (512, 1536, 3072)
KARAKTER_PER_TOKEN = 4
JUMLAH_ULANGAN_BAWAAN = 30
AMBANG_LONG_TASK_MS = 50
BYTE_PER_KB = 1024
DIREKTORI_SKRIP = Path(__file__).resolve().parent
POLA_HASIL = re.compile(r'<pre id="hasil">(.*?)</pre>', re.DOTALL)
TEMPLAT_HALAMAN = """<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8"><title>Uji render</title></head>
<body><div id="jawaban"></div><div id="jawaban-sekali"></div>
<pre id="hasil"></pre>
<script>@@MARKED@@</script>
<script>@@DOMPURIFY@@</script>
<script type="application/json" id="konfigurasi">@@KONFIGURASI@@</script>
<script>@@PENGUKUR@@</script>
</body></html>
"""


def baca_jawaban_contoh():
  """Membaca jawaban-contoh.md tanpa baris komentar pertamanya."""
  daftar_baris = (DIREKTORI_SKRIP / "jawaban-contoh.md").read_text(
      encoding="utf-8").splitlines(keepends=True)
  if daftar_baris and daftar_baris[0].startswith("<!--"):
    daftar_baris = daftar_baris[1:]
  return "".join(daftar_baris)


def susun_jawaban(teks_contoh, jumlah_karakter):
  """Mengulang jawaban contoh sampai cukup panjang, lalu memotongnya pas.

  Potongan terakhir boleh berhenti di tengah kalimat atau tabel, karena
  jawaban yang sedang dialirkan pun berhenti di tempat sembarang.
  """
  jumlah_salinan = jumlah_karakter // len(teks_contoh) + 1
  return (teks_contoh * jumlah_salinan)[:jumlah_karakter]


def potong_jadi_token(teks):
  """Memotong teks tiap KARAKTER_PER_TOKEN karakter, satu potongan satu token."""
  return [teks[awal:awal + KARAKTER_PER_TOKEN]
          for awal in range(0, len(teks), KARAKTER_PER_TOKEN)]


def susun_halaman(jalur_repo, daftar_potongan):
  """Menyusun halaman uji dari pustaka repositori dan pengukur Bab 15.

  marked dan DOMPurify diambil dari web/vendor/ repositori yang diukur,
  bukan dari salinan sendiri, agar versi yang diukur sama dengan versi yang
  dikirim ke pengguna. Tanda </ di data disamarkan agar tidak menutup
  elemen script lebih awal.
  """
  direktori_vendor = Path(jalur_repo) / "web" / "vendor"
  konfigurasi = json.dumps({"potongan": daftar_potongan}).replace("</", "<\\/")
  isi_halaman = TEMPLAT_HALAMAN
  isi_halaman = isi_halaman.replace(
      "@@MARKED@@", (direktori_vendor / "marked.min.js").read_text("utf-8"))
  isi_halaman = isi_halaman.replace(
      "@@DOMPURIFY@@", (direktori_vendor / "purify.min.js").read_text("utf-8"))
  isi_halaman = isi_halaman.replace("@@KONFIGURASI@@", konfigurasi)
  return isi_halaman.replace(
      "@@PENGUKUR@@",
      (DIREKTORI_SKRIP / "render-aliran.js").read_text("utf-8"))


def ukur_sekali(chrome, isi_halaman):
  """Membuka halaman uji satu kali, lalu mengembalikan hasil pengukurannya."""
  with tempfile.TemporaryDirectory() as direktori_sementara:
    jalur_halaman = Path(direktori_sementara) / "uji-render.html"
    jalur_halaman.write_text(isi_halaman, encoding="utf-8")
    dom_akhir = buka_halaman_lokal(chrome, jalur_halaman)
  cocok = POLA_HASIL.search(dom_akhir)
  if not cocok or not cocok.group(1).strip():
    raise SystemExit("Halaman uji tidak menulis hasil. Periksa render-aliran.js.")
  return json.loads(html.unescape(cocok.group(1)))


def ringkas_panjang(daftar_hasil):
  """Meringkas seluruh ulangan satu panjang jawaban menjadi satu baris.

  Lama per pembaruan digabung dari seluruh ulangan sebelum diringkas.
  Total adalah jumlah lama seluruh pembaruan satu jawaban, diringkas
  menjadi median antar ulangan, begitu pula render sekali.
  """
  lama_gabungan = []
  daftar_total = []
  daftar_sekali = []
  jumlah_long_task = 0
  for hasil in daftar_hasil:
    lama_gabungan.extend(hasil["per_pembaruan_ms"])
    daftar_total.append(sum(hasil["per_pembaruan_ms"]))
    daftar_sekali.append(hasil["sekali_ms"])
    for lama in hasil["per_pembaruan_ms"]:
      if lama > AMBANG_LONG_TASK_MS:
        jumlah_long_task += 1
  median_pembaruan, p95_pembaruan, maks_pembaruan = ringkas_sebaran(lama_gabungan)
  median_total = ringkas_sebaran(daftar_total)[0]
  median_sekali = ringkas_sebaran(daftar_sekali)[0]
  return (median_pembaruan, p95_pembaruan, maks_pembaruan, median_total,
          median_sekali, jumlah_long_task)


def main():
  """Mengukur ketiga panjang jawaban, lalu mencetak satu baris per panjang."""
  if len(sys.argv) < 2:
    raise SystemExit("Pakai: ukur-render-aliran.py JALUR_REPO [JUMLAH_ULANGAN]")
  jalur_repo = sys.argv[1]
  jumlah_ulangan = (int(sys.argv[2]) if len(sys.argv) > 2
                    else JUMLAH_ULANGAN_BAWAAN)
  chrome = cari_chrome()
  teks_contoh = baca_jawaban_contoh()
  print(f"Repositori : {Path(jalur_repo).name} (komit {baca_komit(jalur_repo)})")
  print(f"Browser    : {baca_versi_chrome(chrome)}")
  print(f"Ulangan    : {jumlah_ulangan} per panjang, "
        f"{KARAKTER_PER_TOKEN} karakter per token\n")
  print(f"{'Token':>6}{'KB':>6}{'Med ms':>9}{'P95 ms':>9}{'Maks ms':>9}"
        f"{'Total ms':>10}{'Sekali ms':>11}{'>50 ms':>8}")
  for panjang_token in DAFTAR_PANJANG_TOKEN:
    teks_jawaban = susun_jawaban(teks_contoh, panjang_token * KARAKTER_PER_TOKEN)
    isi_halaman = susun_halaman(jalur_repo, potong_jadi_token(teks_jawaban))
    daftar_hasil = [ukur_sekali(chrome, isi_halaman)
                    for _ in range(jumlah_ulangan)]
    (median_pembaruan, p95_pembaruan, maks_pembaruan, median_total,
     median_sekali, jumlah_long_task) = ringkas_panjang(daftar_hasil)
    ukuran_kb = len(teks_jawaban.encode("utf-8")) / BYTE_PER_KB
    print(f"{panjang_token:>6}{ukuran_kb:>6.1f}{median_pembaruan:>9.2f}"
          f"{p95_pembaruan:>9.2f}{maks_pembaruan:>9.2f}{median_total:>10.1f}"
          f"{median_sekali:>11.2f}{jumlah_long_task:>8}")


if __name__ == "__main__":
  main()
