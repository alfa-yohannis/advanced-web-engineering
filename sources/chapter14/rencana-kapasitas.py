"""Menyusun rencana kapasitas untuk beban berlipat dari angka hasil pengukuran.

Rencananya dihitung per layanan, karena tiap layanan tumbuh dan dibatasi oleh
hal yang berbeda. Untuk tiap layanan dihitung empat hal:

    replika      berapa replika aplikasi yang dibutuhkan beban sasaran
    replikasi    berapa replika baca basis data untuk query baca yang lolos cache
    partisi      berapa shard yang dibutuhkan query tulis, yang tidak dapat
                 dibagi ke replika baca
    biaya        biaya bulanan dari jumlah replika dan node basis data

Setiap komponen hanya boleh dipakai sampai utilisasi_maksimum dari
kapasitasnya. Sisanya adalah ruang untuk lonjakan dan untuk node yang down,
sehingga rencana tidak bergantung pada keadaan yang serba lancar.

Seluruh angka masukan ada di rencana.json. Kapasitas diambil dari pengukuran
Latihan 1, sedangkan biaya hanya asumsi contoh.

Pemakaian (dari sources/chapter14):
    python3 rencana-kapasitas.py
    python3 rencana-kapasitas.py rencana-lain.json
"""

import json
import math
import sys
from pathlib import Path

FILE_RENCANA_BAWAAN = Path(__file__).parent / "rencana.json"
RUPIAH_PER_JUTA = 1_000_000
PERSEN = 100
LEBAR_NAMA = 9


def baca_rencana(jalur_file):
  """Membaca seluruh angka masukan rencana dari satu file JSON."""
  return json.loads(Path(jalur_file).read_text(encoding="utf-8"))


def hitung_layanan(layanan, rencana):
  """Menghitung kebutuhan satu layanan pada beban sasaran.

  Query baca yang lolos cache dibagi ke replika baca. Query tulis tidak dapat
  dibagi seperti itu, karena tiap tulisan harus masuk ke satu primary. Bila
  tulisannya melebihi budget satu node, datanya harus dipartisi menjadi
  beberapa shard, masing-masing dengan primary sendiri.
  """
  target_rps = layanan["beban_puncak_rps"] * rencana["kelipatan_beban"]
  utilisasi = rencana["utilisasi_maksimum"]
  budget_replika_rps = rencana["kapasitas_replika_rps"] * utilisasi
  budget_node_qps = rencana["kapasitas_node_basis_data_qps"] * utilisasi
  query_rps = target_rps * layanan["query_per_permintaan"]
  baca_qps = (query_rps * (1 - layanan["rasio_tulis"])
              * (1 - layanan["hit_ratio_cache"]))
  tulis_qps = query_rps * layanan["rasio_tulis"]

  replika = math.ceil(target_rps / budget_replika_rps)
  shard = max(1, math.ceil(tulis_qps / budget_node_qps))
  replika_baca_per_shard = math.ceil(baca_qps / shard / budget_node_qps)
  node_basis_data = shard * (1 + replika_baca_per_shard)
  # Tiap replika aplikasi membuka satu pool ke tiap node basis data
  # layanannya, sehingga satu node menerima koneksi dari seluruh replika.
  koneksi_per_node = replika * rencana["koneksi_per_replika"]
  biaya_rupiah = (replika * rencana["biaya_replika_per_bulan_rupiah"]
                  + node_basis_data
                  * rencana["biaya_node_basis_data_per_bulan_rupiah"])
  return {
      "nama": layanan["nama"],
      "target_rps": target_rps,
      "replika": replika,
      "baca_qps": baca_qps,
      "tulis_qps": tulis_qps,
      "shard": shard,
      "node_basis_data": node_basis_data,
      "koneksi_per_node": koneksi_per_node,
      "biaya_rupiah": biaya_rupiah,
  }


def cetak_rencana(daftar_hasil, rencana):
  """Mencetak kebutuhan tiap layanan, pemeriksaan koneksi, dan totalnya."""
  print(f"  Beban {rencana['kelipatan_beban']} kali lipat, utilisasi maksimum "
        f"{rencana['utilisasi_maksimum'] * PERSEN:.0f}%\n")
  print(f"  {'Layanan':<{LEBAR_NAMA}} {'Target':>6} {'Replika':>7} "
        f"{'Baca/s':>7} {'Tulis/s':>7} {'Shard':>5} {'Node BD':>7} "
        f"{'Juta Rp':>7}")
  for hasil in daftar_hasil:
    print(f"  {hasil['nama']:<{LEBAR_NAMA}} {hasil['target_rps']:>6.0f} "
          f"{hasil['replika']:>7} {hasil['baca_qps']:>7.1f} "
          f"{hasil['tulis_qps']:>7.1f} {hasil['shard']:>5} "
          f"{hasil['node_basis_data']:>7} "
          f"{hasil['biaya_rupiah'] / RUPIAH_PER_JUTA:>7.1f}")
  print()
  batas = rencana["batas_koneksi_per_node"]
  for hasil in daftar_hasil:
    keadaan = "aman" if hasil["koneksi_per_node"] <= batas else "perlu pooler"
    print(f"  {hasil['nama']:<{LEBAR_NAMA}} {hasil['koneksi_per_node']:>4} "
          f"koneksi per node basis data, batas {batas}: {keadaan}")
  total_replika = sum(hasil["replika"] for hasil in daftar_hasil)
  total_node = sum(hasil["node_basis_data"] for hasil in daftar_hasil)
  total_biaya = sum(hasil["biaya_rupiah"] for hasil in daftar_hasil)
  print(f"\n  Total: {total_replika} replika, {total_node} node basis data, "
        f"Rp {total_biaya / RUPIAH_PER_JUTA:.1f} juta per bulan")


def main():
  """Membaca rencana, menghitung tiap layanan, lalu mencetak hasilnya."""
  jalur_file = sys.argv[1] if len(sys.argv) > 1 else FILE_RENCANA_BAWAAN
  rencana = baca_rencana(jalur_file)
  daftar_hasil = [hitung_layanan(layanan, rencana)
                  for layanan in rencana["layanan"]]
  cetak_rencana(daftar_hasil, rencana)


if __name__ == "__main__":
  main()
