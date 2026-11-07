// Service worker katalog Bab 14. Kerangka halaman disimpan ke cache saat
// pemasangan, lalu dilayani dari cache lebih dahulu. Data katalog diambil dari
// jaringan lebih dahulu, dan salinan terakhirnya dipakai ketika jaringan gagal.

/** Nama cache. Versinya dinaikkan setiap kerangka berubah. */
const NAMA_CACHE = "katalog-v1";
/** File kerangka yang disimpan saat pemasangan. */
const KERANGKA = ["/", "/aplikasi.js", "/manifest.webmanifest", "/ikon.svg"];
/** Alamat data katalog, satu-satunya yang diambil dari jaringan lebih dahulu. */
const ALAMAT_KATALOG = "/api/katalog";
/** Header penanda bahwa response diambil dari cache, bukan dari jaringan. */
const HEADER_SUMBER = "X-Sumber";

/** Menyimpan seluruh kerangka ke cache, lalu langsung aktif. */
async function pasang() {
  const cache = await caches.open(NAMA_CACHE);
  await cache.addAll(KERANGKA);
  await self.skipWaiting();
}

/**
 * Menghapus cache versi lama, lalu mengambil alih halaman yang terbuka.
 *
 * Tanpa penghapusan, tiap versi kerangka meninggalkan cache yang tidak
 * pernah dipakai lagi di perangkat pengguna.
 */
async function aktifkan() {
  for (const nama of await caches.keys()) {
    if (nama !== NAMA_CACHE) {
      await caches.delete(nama);
    }
  }
  await self.clients.claim();
}

/**
 * Melayani kerangka dari cache lebih dahulu, jaringan bila belum tersimpan.
 * @param {Request} permintaan Permintaan dari halaman.
 * @returns {Promise<Response>} Response dari cache atau dari jaringan.
 */
async function cacheLebihDahulu(permintaan) {
  const tersimpan = await caches.match(permintaan);
  return tersimpan || fetch(permintaan);
}

/**
 * Menyalin response dari cache, ditambah header penanda sumbernya.
 * @param {Response} respon Response yang diambil dari cache.
 * @returns {Promise<Response>} Salinan dengan header X-Sumber: cache.
 */
async function tandaiDariCache(respon) {
  const header = new Headers(respon.headers);
  header.set(HEADER_SUMBER, "cache");
  return new Response(await respon.blob(), { status: respon.status, headers: header });
}

/**
 * Mengambil data dari jaringan lebih dahulu, salinan terakhir bila gagal.
 *
 * Setiap response yang berhasil disimpan, sehingga salinan di cache selalu
 * yang terakhir dilihat pengguna, bukan yang tersimpan saat pemasangan.
 * @param {Request} permintaan Permintaan data katalog dari halaman.
 * @returns {Promise<Response>} Response dari jaringan atau dari cache.
 */
async function jaringanLebihDahulu(permintaan) {
  const cache = await caches.open(NAMA_CACHE);
  try {
    const respon = await fetch(permintaan);
    await cache.put(permintaan, respon.clone());
    return respon;
  } catch (gagal) {
    const tersimpan = await cache.match(permintaan);
    if (!tersimpan) {
      throw gagal;
    }
    return tandaiDariCache(tersimpan);
  }
}

/** Menyimpan kerangka ketika service worker dipasang. */
function tanganiPasang(peristiwa) {
  peristiwa.waitUntil(pasang());
}

/** Membersihkan cache lama ketika service worker aktif. */
function tanganiAktif(peristiwa) {
  peristiwa.waitUntil(aktifkan());
}

/**
 * Memilih cara melayani tiap permintaan GET ke situs sendiri.
 *
 * Permintaan ke situs lain dan permintaan selain GET dibiarkan lewat ke
 * jaringan seperti biasa, karena keduanya tidak boleh dilayani dari cache.
 */
function tanganiAmbil(peristiwa) {
  const alamat = new URL(peristiwa.request.url);
  const bukanGet = peristiwa.request.method !== "GET";
  const situsLain = alamat.origin !== self.location.origin;
  if (bukanGet || situsLain) {
    return;
  }
  if (alamat.pathname === ALAMAT_KATALOG) {
    peristiwa.respondWith(jaringanLebihDahulu(peristiwa.request));
    return;
  }
  peristiwa.respondWith(cacheLebihDahulu(peristiwa.request));
}

self.addEventListener("install", tanganiPasang);
self.addEventListener("activate", tanganiAktif);
self.addEventListener("fetch", tanganiAmbil);
