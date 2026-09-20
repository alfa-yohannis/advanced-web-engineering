"use strict";
/**
 * Memuat satu halaman katalog lalu menggambarnya, sebagai beban interaksi.
 *
 * Penggambaran sengaja dilakukan lewat satu fragment, bukan satu per satu ke
 * dalam dokumen, agar tata letak hanya dihitung ulang sekali. Cara ini
 * menekan pergeseran tata letak yang terbaca sebagai CLS.
 *
 * Kompilasi (dari sources/chapter05):
 *   npx -p typescript tsc --target es2022 --module es2022 --strict \
 *     --lib es2022,dom --outDir statis katalog.ts
 */
const ALAMAT_KATALOG = "/api/katalog?halaman=1&ukuran=20";
/**
 * Membuat satu baris katalog sebagai elemen, tanpa menyentuh dokumen.
 * @param buku satu baris jawaban katalog
 * @returns elemen baris yang siap dimasukkan ke fragment
 */
function buatBaris(buku) {
    const baris = document.createElement("div");
    baris.className = "baris";
    baris.textContent = `${buku.judul} — Rp ${buku.harga.toLocaleString("id-ID")}`;
    return baris;
}
/**
 * Mengambil katalog dari server lalu menggambarnya sekali jadi.
 */
async function muatKatalog() {
    const wadah = document.getElementById("daftar");
    if (wadah === null) {
        return;
    }
    const jawaban = await fetch(ALAMAT_KATALOG);
    const daftarBuku = (await jawaban.json());
    const fragment = document.createDocumentFragment();
    for (const buku of daftarBuku) {
        fragment.appendChild(buatBaris(buku));
    }
    wadah.replaceChildren(fragment);
}
/** Menjalankan pemuatan katalog saat tombol ditekan. */
function tanganiKlik() {
    void muatKatalog();
}
document.getElementById("muat")?.addEventListener("click", tanganiKlik);
