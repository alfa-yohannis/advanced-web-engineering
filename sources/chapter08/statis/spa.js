// Skrip varian SPA: seluruh isi katalog diminta dan digambar di browser.
// Halaman yang tiba lebih dahulu tidak memuat satu judul pun, sehingga
// pengunjung melihat kerangka kosong sampai permintaan kedua selesai.

/** Alamat data katalog, dipakai hanya oleh varian SPA dan islands. */
const ALAMAT_KATALOG = "/api/katalog";

/**
 * Mengambil katalog dari server lalu menggambarnya sekali jadi.
 */
async function gambarKatalog() {
  const wadah = document.getElementById("daftar");
  if (wadah === null) {
    return;
  }
  const response = await fetch(ALAMAT_KATALOG);
  const daftarBuku = await response.json();
  const fragment = document.createDocumentFragment();
  for (const buku of daftarBuku) {
    const baris = document.createElement("li");
    baris.textContent = `${buku.judul} — Rp ${buku.harga.toLocaleString("id-ID")}`;
    fragment.appendChild(baris);
  }
  wadah.replaceChildren(fragment);
}

void gambarKatalog();
