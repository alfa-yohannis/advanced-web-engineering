"""Mengukur hubungan umur cabang dengan jumlah konflik ketika digabung.

Satu repositori Git sementara dibuat, berisi satu file katalog 300 baris. Dua
pengembang bekerja di dua cabang. Tiap hari kerja, masing-masing mengubah
beberapa baris acak di file itu lalu meng-commit-nya. Sesudah 1, 3, 7, dan 14
hari, cabang kedua digabung ke cabang pertama, dan blok konflik yang dibuat
Git dihitung dari isi file-nya.

Kedua pengembang memakai urutan acak yang sama pada tiap umur, sehingga
cabang tiga hari adalah awal dari cabang tujuh hari. Yang berbeda hanya kapan
cabangnya digabung. Benih acaknya tetap, sehingga hasilnya sama pada tiap
komputer dengan versi Git yang sama.

Pengaturan Git milik pengguna tidak ikut dipakai, agar tanda tangan commit
atau hook pribadi tidak mengubah hasil. Seluruhnya terjadi di direktori
sementara yang dihapus sesudahnya.

Pemakaian (dari sources/chapter01):
    python3 simulasi-cabang.py
"""

import os
import random
import subprocess
import tempfile
from pathlib import Path

JUMLAH_BARIS = 300
BARIS_PER_HARI = 3
DAFTAR_UMUR_HARI = [1, 3, 7, 14]
HARGA_AWAL_RUPIAH = 50_000
LANGKAH_HARGA_RUPIAH = 500
NAMA_FILE = "katalog.txt"
PENANDA_KONFLIK = "<<<<<<<"
# Identitas commit dan pengaturan Git yang terpisah dari milik pengguna.
ENVIRONMENT_GIT = dict(
    os.environ,
    GIT_AUTHOR_NAME="Latihan", GIT_AUTHOR_EMAIL="latihan@contoh.invalid",
    GIT_COMMITTER_NAME="Latihan", GIT_COMMITTER_EMAIL="latihan@contoh.invalid",
    GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
)


def git(direktori, *argumen, boleh_gagal=False):
  """Menjalankan satu perintah git di direktori repositori latihan."""
  return subprocess.run(["git", *argumen], cwd=direktori, env=ENVIRONMENT_GIT,
                        capture_output=True, text=True, check=not boleh_gagal)


def isi_awal():
  """Menyusun isi awal katalog: satu baris untuk tiap buku."""
  return [f"buku-{nomor:03d} harga={HARGA_AWAL_RUPIAH}"
          for nomor in range(1, JUMLAH_BARIS + 1)]


def tulis_katalog(direktori, baris_katalog):
  """Menulis seluruh baris katalog ke file-nya."""
  (direktori / NAMA_FILE).write_text("\n".join(baris_katalog) + "\n")


def kerja_satu_hari(direktori, pengembang, hari, acak, baris_diubah):
  """Mengubah beberapa baris acak, lalu meng-commit-nya sebagai satu hari.

  Nomor baris yang diubah dicatat, agar sesudahnya dapat dibandingkan dengan
  baris yang diubah pengembang lain.
  """
  baris_katalog = (direktori / NAMA_FILE).read_text().splitlines()
  for indeks in acak.sample(range(JUMLAH_BARIS), BARIS_PER_HARI):
    harga = HARGA_AWAL_RUPIAH + acak.randint(1, 20) * LANGKAH_HARGA_RUPIAH
    baris_katalog[indeks] = (f"buku-{indeks + 1:03d} harga={harga} "
                             f"# {pengembang} hari {hari}")
    baris_diubah.add(indeks)
  tulis_katalog(direktori, baris_katalog)
  git(direktori, "commit", "-q", "-am", f"{pengembang}: harga hari {hari}")


def bekerja_di_cabang(direktori, cabang, pengembang, umur_hari, baris_diubah):
  """Membuat satu cabang dari main, lalu bekerja di sana selama umurnya."""
  acak = random.Random(pengembang)
  git(direktori, "checkout", "-q", "-b", cabang, "main")
  for hari in range(1, umur_hari + 1):
    kerja_satu_hari(direktori, pengembang, hari, acak, baris_diubah)


def ukur_satu_umur(direktori, umur_hari):
  """Membiarkan dua cabang hidup selama umurnya, lalu menggabungkan keduanya.

  Penggabungan dibatalkan sesudah konfliknya dihitung, agar umur berikutnya
  dimulai lagi dari main yang sama.
  """
  diubah_a, diubah_b = set(), set()
  bekerja_di_cabang(direktori, f"a-{umur_hari}", "A", umur_hari, diubah_a)
  bekerja_di_cabang(direktori, f"b-{umur_hari}", "B", umur_hari, diubah_b)
  git(direktori, "checkout", "-q", f"a-{umur_hari}")
  hasil = git(direktori, "merge", "--no-edit", f"b-{umur_hari}",
              boleh_gagal=True)
  isi = (direktori / NAMA_FILE).read_text()
  blok_konflik = sum(1 for baris in isi.splitlines()
                     if baris.startswith(PENANDA_KONFLIK))
  if hasil.returncode != 0:
    git(direktori, "merge", "--abort")
  git(direktori, "checkout", "-q", "main")
  return {
      "umur": umur_hari,
      "diubah_a": len(diubah_a),
      "diubah_b": len(diubah_b),
      "diubah_keduanya": len(diubah_a & diubah_b),
      "blok_konflik": blok_konflik,
  }


def main():
  """Menyiapkan repositori sementara, mengukur tiap umur, lalu mencetaknya."""
  with tempfile.TemporaryDirectory() as tempat:
    direktori = Path(tempat)
    git(direktori, "init", "-q", "-b", "main")
    tulis_katalog(direktori, isi_awal())
    git(direktori, "add", NAMA_FILE)
    git(direktori, "commit", "-q", "-m", "Katalog awal")
    versi_git = git(direktori, "--version").stdout.strip()
    print(f"  {JUMLAH_BARIS} baris, tiap pengembang mengubah {BARIS_PER_HARI} "
          f"baris per hari, {versi_git}\n")
    print(f"  {'Umur cabang':>11} {'Diubah A':>9} {'Diubah B':>9} "
          f"{'Diubah keduanya':>16} {'Blok konflik':>13}")
    for umur_hari in DAFTAR_UMUR_HARI:
      hasil = ukur_satu_umur(direktori, umur_hari)
      print(f"  {str(hasil['umur']) + ' hari':>11} {hasil['diubah_a']:>9} "
            f"{hasil['diubah_b']:>9} {hasil['diubah_keduanya']:>16} "
            f"{hasil['blok_konflik']:>13}")


if __name__ == "__main__":
  main()
