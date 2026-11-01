// Contoh pemakaian tipe hasil generate. File ini lolos tsc --strict, dan
// dipakai untuk memastikan tipe yang di-generate benar-benar dapat dipakai.

import type { Buku, HalamanBuku, KlienKatalog, Pesanan } from "./tipe-katalog";

/**
 * Menjumlahkan harga seluruh buku pada satu halaman.
 * @param halaman Satu halaman hasil ambilBuku.
 * @returns Jumlah harga seluruh buku di halaman itu.
 */
export function jumlahHarga(halaman: HalamanBuku): number {
  return halaman.item.reduce((jumlah: number, buku: Buku) =>
    jumlah + buku.harga, 0);
}

/**
 * Memesan satu buku lewat klien yang tanda tangannya di-generate.
 * @param klien Klien katalog hasil generate.
 * @param idBuku Nomor buku yang dipesan.
 * @param kunci Idempotency-Key, wajib menurut kontrak.
 * @returns Pesanan yang diterima server.
 */
export async function pesanSatu(klien: KlienKatalog, idBuku: number,
                                kunci: string): Promise<Pesanan> {
  return klien.buatPesanan({ idempotency_key: kunci },
                           { id_buku: idBuku, jumlah: 1 });
}
