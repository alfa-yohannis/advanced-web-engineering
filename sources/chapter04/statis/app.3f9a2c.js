// Aset bernama sidik jari untuk Bab 4, disajikan aplikasi.py dengan max-age setahun.
// Mengisi daftar buku terlaris dari /api/terlaris-cache.

const ALAMAT_TERLARIS = "/api/terlaris-cache";

/** Menulis satu butir daftar per buku, beserta jumlah terjualnya. */
function tampilkanTerlaris(daftarBuku) {
  const wadah = document.getElementById("daftar-terlaris");
  for (const buku of daftarBuku) {
    const butir = document.createElement("li");
    butir.textContent = `${buku.judul} (${buku.terjual} terjual)`;
    wadah.appendChild(butir);
  }
}

/** Mengambil daftar terlaris dari server, lalu menampilkannya. */
async function muatTerlaris() {
  const jawaban = await fetch(ALAMAT_TERLARIS);
  tampilkanTerlaris(await jawaban.json());
}

muatTerlaris();
