// File ini SENGAJA salah, dipakai untuk memperlihatkan kesalahan tertangkap
// compiler, bukan pengguna. Isinya memakai kontrak versi 2 dengan cara klien
// versi 1: field harga sudah berganti nama menjadi harga_rupiah.
//
// Diperiksa dengan: tsc --noEmit --strict pakai-tipe-salah.ts

import type { Buku } from "./tipe-katalog-v2";

/**
 * Membaca harga buku dengan nama field versi 1.
 * @param buku Buku menurut kontrak versi 2.
 * @returns Harga buku, bila field-nya masih ada.
 */
export function bacaHarga(buku: Buku): number {
  return buku.harga;
}
