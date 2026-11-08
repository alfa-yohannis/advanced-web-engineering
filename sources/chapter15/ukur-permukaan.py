"""Membaca kode tiga sistem RAG, lalu mencetak keadaan awal yang diukur Bab 15.

Skrip ini hanya membaca file di repositori yang sudah dikloning. Tidak ada
kode sistem RAG yang dijalankan, dan tidak ada request yang dikirim ke
layanan mana pun. Tiap baris keluaran punya definisi yang tertulis di
docstring fungsinya, karena definisi yang berbeda menghasilkan angka yang
berbeda.

Cara menjalankan, dari sources/chapter15 sesudah ketiga repositori dikloning
ke dalam rag/:
    ../.venv/bin/python ukur-permukaan.py rag/exim rag/djp rag/akreditasi
"""

import ast
import gzip
import re
import sys
from pathlib import Path

from pengukur import baca_komit

LEVEL_GZIP = 6
BYTE_PER_KB = 1024
LEBAR_LABEL = 26
LEBAR_KOLOM = 12
HEADER_KEAMANAN = [
    "Content-Security-Policy", "Strict-Transport-Security",
    "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy",
    "Permissions-Policy",
]
POLA_SINK_HTML = re.compile(
    r"\.innerHTML\s*\+?=(?!=)|\.outerHTML\s*=(?!=)|insertAdjacentHTML\(|"
    r"document\.write\(")
POLA_RENDER_ULANG_PENUH = re.compile(
    r"innerHTML\s*=\s*this\.markdown\.render\(\s*this\.accumulatedText\s*\)")
POLA_MASA_SESI = re.compile(r'"SESSION_HOURS",\s*(\d+)')
POLA_FUNGSI_UJI = re.compile(r"^\s*(?:async\s+)?def test_", re.MULTILINE)


def hitung_modul_python(jalur_repo):
  """Banyaknya file .py di app/ beserta jumlah barisnya.

  File __init__.py ikut dihitung, agar angkanya sama dengan hitungan pada
  buku Software Architecture yang memakai ketiga sistem yang sama.
  """
  daftar_file = sorted((Path(jalur_repo) / "app").glob("*.py"))
  jumlah_baris = 0
  for file_python in daftar_file:
    jumlah_baris += len(file_python.read_text(encoding="utf-8").splitlines())
  return len(daftar_file), jumlah_baris


def hitung_fungsi_uji(jalur_repo):
  """Banyaknya fungsi berawalan test_ di tests/test_*.py.

  Fungsi uji di dalam kelas ikut terhitung, karena pytest menjalankannya
  juga. Parameterisasi tidak dikembangkan, jadi satu fungsi dihitung satu.
  """
  jumlah = 0
  for file_uji in (Path(jalur_repo) / "tests").glob("test_*.py"):
    jumlah += len(POLA_FUNGSI_UJI.findall(file_uji.read_text(encoding="utf-8")))
  return jumlah


def baca_nilai_kelas(pohon_sintaks, nama_atribut):
  """Mengambil nilai literal satu atribut kelas, misalnya PUBLIC_PATHS.

  Nilai frozenset({...}) dibuka menjadi isinya, karena ast.literal_eval
  tidak menerima pemanggilan fungsi.
  """
  for simpul in ast.walk(pohon_sintaks):
    if not isinstance(simpul, ast.Assign):
      continue
    for target in simpul.targets:
      if isinstance(target, ast.Name) and target.id == nama_atribut:
        nilai = simpul.value
        if isinstance(nilai, ast.Call) and nilai.args:
          nilai = nilai.args[0]
        return ast.literal_eval(nilai)
  return ()


def baca_jalur_rute(pohon_sintaks):
  """Mengumpulkan jalur tiap pemanggilan add_api_route di server.py."""
  daftar_jalur = []
  for simpul in ast.walk(pohon_sintaks):
    if (isinstance(simpul, ast.Call)
        and isinstance(simpul.func, ast.Attribute)
        and simpul.func.attr == "add_api_route"
        and simpul.args
        and isinstance(simpul.args[0], ast.Constant)):
      daftar_jalur.append(simpul.args[0].value)
  return daftar_jalur


def hitung_rute(jalur_repo):
  """Banyaknya rute HTTP, dan berapa di antaranya terbuka tanpa sesi.

  Rute terbuka adalah rute yang jalurnya ada di PUBLIC_PATHS atau berawalan
  salah satu PUBLIC_PREFIXES, sehingga dilewatkan middleware pemeriksa sesi.
  Direktori statis yang dipasang lewat mount tidak dihitung sebagai rute.
  """
  kode_server = (Path(jalur_repo) / "app" / "server.py").read_text(
      encoding="utf-8")
  pohon_sintaks = ast.parse(kode_server)
  jalur_publik = set(baca_nilai_kelas(pohon_sintaks, "PUBLIC_PATHS"))
  awalan_publik = tuple(baca_nilai_kelas(pohon_sintaks, "PUBLIC_PREFIXES"))
  daftar_jalur = baca_jalur_rute(pohon_sintaks)
  jumlah_terbuka = 0
  for jalur in daftar_jalur:
    if jalur in jalur_publik or jalur.startswith(awalan_publik):
      jumlah_terbuka += 1
  return len(daftar_jalur), jumlah_terbuka


def gabungkan_kode_python(jalur_repo):
  """Seluruh isi app/*.py sebagai satu teks, untuk pencarian sederhana."""
  daftar_isi = []
  for file_python in sorted((Path(jalur_repo) / "app").glob("*.py")):
    daftar_isi.append(file_python.read_text(encoding="utf-8"))
  return "\n".join(daftar_isi)


def hitung_header_keamanan(jalur_repo):
  """Berapa dari enam header keamanan yang namanya muncul di app/*.py.

  Yang diperiksa hanya kode aplikasinya. Header yang ditambahkan proxy di
  depan aplikasi, misalnya CDN, tidak terlihat dari sini dan diukur dari
  response-nya sendiri.
  """
  kode_kecil = gabungkan_kode_python(jalur_repo).lower()
  jumlah = 0
  for nama_header in HEADER_KEAMANAN:
    if nama_header.lower() in kode_kecil:
      jumlah += 1
  return f"{jumlah} dari {len(HEADER_KEAMANAN)}"


def daftar_javascript_sendiri(jalur_repo):
  """File .js di web/ yang ditulis sendiri, tanpa pustaka di web/vendor/."""
  direktori_web = Path(jalur_repo) / "web"
  daftar_file = []
  for file_js in sorted(direktori_web.rglob("*.js")):
    if "vendor" not in file_js.relative_to(direktori_web).parts:
      daftar_file.append(file_js)
  return daftar_file


def hitung_sink_html(jalur_repo):
  """Banyaknya penulisan HTML mentah ke DOM di JavaScript sendiri.

  Yang dihitung: penugasan innerHTML dan outerHTML, insertAdjacentHTML, dan
  document.write. Tiap sink adalah satu tempat yang harus di-escape dengan
  benar oleh tangan. Escape yang benar tidak mengurangi hitungannya.
  """
  jumlah = 0
  for file_js in daftar_javascript_sendiri(jalur_repo):
    jumlah += len(POLA_SINK_HTML.findall(file_js.read_text(encoding="utf-8")))
  return jumlah


def cek_render_ulang_penuh(jalur_repo):
  """Apakah tiap token memicu render ulang seluruh teks jawaban."""
  kode_aplikasi = (Path(jalur_repo) / "web" / "app.js").read_text(
      encoding="utf-8")
  return "ya" if POLA_RENDER_ULANG_PENUH.search(kode_aplikasi) else "tidak"


def cek_aliran_tersambung(jalur_repo):
  """Apakah jawaban dibuat di latar belakang dan dapat disambung ulang.

  Syaratnya dua: modul answer_streams.py ada, dan server membaca header
  Last-Event-ID. Tanpa keduanya, jawaban dibuat di dalam response, sehingga
  koneksi yang putus ikut menghentikan pembuatannya.
  """
  direktori_aplikasi = Path(jalur_repo) / "app"
  kode_server = (direktori_aplikasi / "server.py").read_text(encoding="utf-8")
  modul_ada = (direktori_aplikasi / "answer_streams.py").exists()
  return "ya" if modul_ada and "last-event-id" in kode_server.lower() else "tidak"


def baca_masa_sesi_jam(jalur_repo):
  """Masa berlaku token sesi bawaan, dibaca dari setelan SESSION_HOURS."""
  kode_setelan = (Path(jalur_repo) / "app" / "config.py").read_text(
      encoding="utf-8")
  cocok = POLA_MASA_SESI.search(kode_setelan)
  return cocok.group(1) if cocok else "tidak ada"


def hitung_workflow_ci(jalur_repo):
  """Banyaknya file workflow di .github/workflows/."""
  direktori_workflow = Path(jalur_repo) / ".github" / "workflows"
  if not direktori_workflow.exists():
    return 0
  return len([file for file in direktori_workflow.iterdir() if file.is_file()])


def ukur_javascript(jalur_repo):
  """Ukuran seluruh .js di web/, termasuk pustaka vendor, mentah dan gzip.

  Pustaka vendor ikut dihitung karena browser tetap mengunduhnya. Ukuran
  gzip dihitung per file pada level 6, mendekati yang dikirim server yang
  memampatkan response-nya.
  """
  ukuran_mentah = 0
  ukuran_gzip = 0
  for file_js in sorted((Path(jalur_repo) / "web").rglob("*.js")):
    isi = file_js.read_bytes()
    ukuran_mentah += len(isi)
    ukuran_gzip += len(gzip.compress(isi, compresslevel=LEVEL_GZIP))
  return (f"{ukuran_mentah / BYTE_PER_KB:.1f}",
          f"{ukuran_gzip / BYTE_PER_KB:.1f}")


def ukur_satu_repo(jalur_repo):
  """Mengumpulkan seluruh ukuran satu repositori sebagai pasangan berurutan."""
  jumlah_modul, jumlah_baris = hitung_modul_python(jalur_repo)
  jumlah_rute, jumlah_rute_terbuka = hitung_rute(jalur_repo)
  javascript_mentah, javascript_gzip = ukur_javascript(jalur_repo)
  return [
      ("Komit", baca_komit(jalur_repo)),
      ("Modul Python di app/", jumlah_modul),
      ("Baris Python di app/", jumlah_baris),
      ("Fungsi uji", hitung_fungsi_uji(jalur_repo)),
      ("Rute HTTP", jumlah_rute),
      ("Rute tanpa sesi", jumlah_rute_terbuka),
      ("Header keamanan dipasang", hitung_header_keamanan(jalur_repo)),
      ("Sink HTML di web/", hitung_sink_html(jalur_repo)),
      ("Render ulang tiap token", cek_render_ulang_penuh(jalur_repo)),
      ("Aliran dapat disambung", cek_aliran_tersambung(jalur_repo)),
      ("Masa berlaku sesi (jam)", baca_masa_sesi_jam(jalur_repo)),
      ("Workflow CI", hitung_workflow_ci(jalur_repo)),
      ("JavaScript (KB)", javascript_mentah),
      ("JavaScript gzip (KB)", javascript_gzip),
  ]


def cetak_tabel(daftar_nama_repo, daftar_hasil):
  """Mencetak satu baris per ukuran, satu kolom per repositori."""
  judul = "Ukuran".ljust(LEBAR_LABEL)
  for nama_repo in daftar_nama_repo:
    judul += nama_repo.rjust(LEBAR_KOLOM)
  print(judul)
  for nomor_baris, (label, _nilai) in enumerate(daftar_hasil[0]):
    baris = label.ljust(LEBAR_LABEL)
    for hasil_repo in daftar_hasil:
      baris += str(hasil_repo[nomor_baris][1]).rjust(LEBAR_KOLOM)
    print(baris)


def main():
  """Mengukur tiap repositori yang disebut di argumen, lalu mencetak tabelnya."""
  daftar_jalur_repo = sys.argv[1:]
  if not daftar_jalur_repo:
    raise SystemExit("Pakai: ukur-permukaan.py JALUR_REPO [JALUR_REPO ...]")
  daftar_nama_repo = [Path(jalur).name for jalur in daftar_jalur_repo]
  daftar_hasil = [ukur_satu_repo(jalur) for jalur in daftar_jalur_repo]
  cetak_tabel(daftar_nama_repo, daftar_hasil)


if __name__ == "__main__":
  main()
