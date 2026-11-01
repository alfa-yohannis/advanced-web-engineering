"""Meng-generate tipe TypeScript dari kontrak OpenAPI.

Kontrak yang menjadi sumber, bukan kodenya. Karena itu tipe di sisi klien
tidak ditulis tangan, melainkan dibuat ulang dari kontrak setiap kali
kontraknya berubah. Dengan begitu klien yang memakai field yang sudah hilang
tertolak oleh compiler, bukan oleh pengguna.

Pemakaian (dari sources/chapter12):
    python3 buat_tipe.py kontrak.json tipe-katalog.ts
    python3 buat_tipe.py kontrak-v2.json tipe-katalog-v2.ts
"""

import json
import sys
from pathlib import Path

# Pemetaan tipe JSON Schema ke tipe TypeScript. Tipe yang tidak ada di sini
# sengaja dibiarkan gagal, agar kontrak yang memakai tipe baru tidak
# menghasilkan tipe "any" tanpa ada yang menyadarinya.
PETA_TIPE = {
    "string": "string",
    "integer": "number",
    "number": "number",
    "boolean": "boolean",
}
AWALAN_REF = "#/components/schemas/"


def nama_dari_ref(ref):
  """Mengambil nama skema dari satu $ref, misalnya Buku dari ref-nya."""
  if not ref.startswith(AWALAN_REF):
    raise SystemExit(f"ref di luar components/schemas: {ref}")
  return ref[len(AWALAN_REF):]


def tipe_dari_skema(skema):
  """Menerjemahkan satu skema menjadi satu tipe TypeScript.

  Enum diterjemahkan menjadi gabungan string literal, sehingga nilai status
  yang tidak ada di kontrak ikut tertolak compiler, bukan hanya nilai yang
  tipenya salah.
  """
  if "$ref" in skema:
    return nama_dari_ref(skema["$ref"])
  if "enum" in skema:
    return " | ".join(json.dumps(nilai) for nilai in skema["enum"])
  jenis = skema.get("type")
  if jenis == "array":
    return f"{tipe_dari_skema(skema['items'])}[]"
  if jenis in PETA_TIPE:
    return PETA_TIPE[jenis]
  raise SystemExit(f"tipe belum didukung generator: {jenis}")


def buat_antarmuka(nama, skema):
  """Menyusun satu interface TypeScript dari satu skema objek.

  Field yang tidak ada di daftar required ditulis opsional dengan tanda
  tanya, sehingga klien wajib memeriksanya sebelum dipakai.
  """
  wajib = set(skema.get("required", []))
  baris = [f"export interface {nama} {{"]
  for field, isi in skema["properties"].items():
    tanda = "" if field in wajib else "?"
    baris.append(f"  {field}{tanda}: {tipe_dari_skema(isi)};")
  baris.append("}")
  return "\n".join(baris)


def tipe_parameter(operasi):
  """Menyusun tipe parameter satu operasi dari daftar parameter kontraknya."""
  baris = []
  for parameter in operasi.get("parameters", []):
    nama = parameter["name"].replace("-", "_").lower()
    tanda = "" if parameter.get("required") else "?"
    baris.append(f"  {nama}{tanda}: {tipe_dari_skema(parameter['schema'])};")
  return baris


def tipe_badan(operasi):
  """Mengambil tipe isi permintaan satu operasi, atau None bila tidak ada."""
  badan = operasi.get("requestBody")
  if not badan:
    return None
  skema = badan["content"]["application/json"]["schema"]
  return tipe_dari_skema(skema)


def tipe_hasil(operasi):
  """Mengambil tipe response sukses satu operasi dari kontraknya."""
  for status, response in operasi["responses"].items():
    if status.startswith("2"):
      skema = response["content"]["application/json"]["schema"]
      return tipe_dari_skema(skema)
  raise SystemExit("operasi tanpa response sukses")


def buat_klien(paths):
  """Menyusun satu interface klien dari seluruh operasi di kontrak.

  Yang di-generate adalah bentuk panggilannya, bukan isinya. Isi panggilan
  tetap ditulis manusia, tetapi tanda tangannya tidak dapat menyimpang dari
  kontrak tanpa membuat compiler mengeluh.
  """
  baris = ["export interface KlienKatalog {"]
  for jalur, metode in sorted(paths.items()):
    for nama_metode, operasi in sorted(metode.items()):
      argumen = []
      parameter = tipe_parameter(operasi)
      if parameter:
        argumen.append("pertanyaan: {\n  " + "\n  ".join(parameter) + "\n  }")
      badan = tipe_badan(operasi)
      if badan:
        argumen.append(f"isi: {badan}")
      baris.append(f"  // {nama_metode.upper()} {jalur}")
      baris.append(f"  {operasi['operationId']}("
                   f"{', '.join(argumen)}): Promise<{tipe_hasil(operasi)}>;")
  baris.append("}")
  return "\n".join(baris)


def main():
  """Membaca kontrak dari argumen pertama, menulis tipe ke argumen kedua."""
  if len(sys.argv) != 3:
    raise SystemExit("pemakaian: python3 buat_tipe.py <kontrak> <keluaran>")
  kontrak = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
  skema = kontrak["components"]["schemas"]
  bagian = [
      f"// Di-generate dari {sys.argv[1]} oleh buat_tipe.py.",
      "// Jangan diubah tangan: jalankan ulang generatornya.",
      f"// Judul kontrak: {kontrak['info']['title']} "
      f"versi {kontrak['info']['version']}.",
      "",
  ]
  for nama, isi in skema.items():
    bagian.append(buat_antarmuka(nama, isi))
    bagian.append("")
  bagian.append(buat_klien(kontrak["paths"]))
  bagian.append("")
  Path(sys.argv[2]).write_text("\n".join(bagian), encoding="utf-8")
  print(f"{len(skema)} skema dan {len(kontrak['paths'])} jalur di-generate "
        f"menjadi {sys.argv[2]}")


if __name__ == "__main__":
  main()
