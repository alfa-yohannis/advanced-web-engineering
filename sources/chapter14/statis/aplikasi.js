// Pemuat katalog di browser untuk demo Progressive Web App Bab 14. Halaman
// mendaftarkan service worker, mengambil data katalog, lalu menuliskan dari
// mana datanya datang ke atribut body, agar dapat dibaca alat ukur.

/** Alamat data katalog di server. */
const ALAMAT_KATALOG = "/api/katalog";
/** Alamat skrip service worker. Cakupannya seluruh situs, karena ada di akar. */
const ALAMAT_SERVICE_WORKER = "/sw.js";
/** Header yang ditambahkan service worker pada data yang diambil dari cache. */
const HEADER_SUMBER = "X-Sumber";

/**
 * Menulis satu kalimat keadaan di atas daftar katalog.
 * @param {string} teks Kalimat yang ditampilkan kepada pengguna.
 */
function tulisKeadaan(teks) {
  document.getElementById("keadaan").textContent = teks;
}

/**
 * Menampilkan daftar buku, lalu mencatat sumber datanya.
 *
 * Judul dimasukkan lewat textContent, bukan innerHTML, karena data dari
 * cache sama tidak terpercayanya dengan data dari jaringan.
 * @param {{dibuat_pada: string, buku: Array<{judul: string, harga: number}>}} isi
 *   Data katalog dari server atau dari cache.
 * @param {string} sumber Asal data, yaitu "jaringan" atau "cache".
 */
function tampilkanKatalog(isi, sumber) {
  const daftar = document.getElementById("katalog");
  daftar.replaceChildren();
  for (const buku of isi.buku) {
    const baris = document.createElement("li");
    baris.className = "buku";
    baris.textContent = `${buku.judul}, Rp${buku.harga}`;
    daftar.append(baris);
  }
  document.body.dataset.sumber = sumber;
  document.body.dataset.tampilMs = String(Math.round(performance.now()));
  tulisKeadaan(`${isi.buku.length} buku dari ${sumber}, ` +
    `data dibuat pukul ${isi.dibuat_pada}`);
}

/**
 * Mengambil data katalog, lewat service worker bila sudah ada.
 *
 * Halaman tidak tahu apakah datanya dari jaringan atau dari cache. Yang
 * memberi tahu hanya header penanda dari service worker.
 */
async function muatKatalog() {
  try {
    const respon = await fetch(ALAMAT_KATALOG);
    const sumber = respon.headers.get(HEADER_SUMBER) || "jaringan";
    tampilkanKatalog(await respon.json(), sumber);
  } catch (gagal) {
    document.body.dataset.sumber = "tidak ada";
    tulisKeadaan("Server tidak dapat dihubungi, dan katalog belum tersimpan.");
  }
}

/**
 * Mendaftarkan service worker, lalu mencatat keadaannya ke atribut body.
 *
 * Kunjungan pertama hanya memasangnya, sehingga halaman pertama itu sendiri
 * tidak terlindungi. Halaman dikendalikan service worker mulai kunjungan
 * berikutnya, atau sejak service worker mengklaimnya sesudah aktif.
 */
async function daftarkanServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    document.body.dataset.serviceWorker = "tidak didukung";
    return;
  }
  document.body.dataset.serviceWorker =
    navigator.serviceWorker.controller ? "mengendalikan" : "belum";
  try {
    await navigator.serviceWorker.register(ALAMAT_SERVICE_WORKER);
  } catch {
    // Saat server tidak dapat dihubungi, pemeriksaan versi baru sw.js gagal.
    // Service worker yang sudah terpasang tetap bekerja seperti biasa.
  }
  await navigator.serviceWorker.ready;
  document.body.dataset.serviceWorkerSiap = "ya";
}

muatKatalog();
daftarkanServiceWorker();
