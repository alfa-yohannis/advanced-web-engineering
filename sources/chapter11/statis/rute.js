// Router di sisi browser untuk application shell. Hanya isi wilayah yang
// diganti saat berpindah halaman, sedangkan judul dan navigasi tetap.
// Seluruh tautannya adalah tautan biasa, sehingga halaman tetap dapat dibuka
// langsung ketika JavaScript mati. Router hanya mencegah muat ulangnya.

/** Awalan alamat yang ditangani router ini. */
const AWALAN_KERANGKA = "/kerangka";
/** Awalan alamat yang mengembalikan isi wilayah saja. */
const AWALAN_FRAGMEN = "/fragmen";
/** Teks pengganti ketika satu wilayah gagal dimuat. */
const PESAN_GAGAL = "Bagian ini gagal dimuat. Navigasi tetap jalan.";

/**
 * Mengubah alamat kerangka menjadi alamat fragmennya.
 * @param {string} alamat Alamat kerangka, misalnya /kerangka/buku/3.
 * @returns {string} Alamat fragmen, misalnya /fragmen/buku/3.
 */
function alamatFragmen(alamat) {
  return AWALAN_FRAGMEN + alamat.slice(AWALAN_KERANGKA.length);
}

/**
 * Menampilkan pesan pengganti di dalam wilayah.
 *
 * Inilah batas error yang paling sederhana: kegagalan ditahan di satu
 * wilayah, sehingga kerangka beserta navigasinya tetap dapat dipakai.
 * @param {string} pesan Pesan yang ditampilkan kepada pengguna.
 */
function tampilkanGagal(pesan) {
  document.getElementById("wilayah").innerHTML =
    `<article class="kartu"><h2>${pesan}</h2></article>`;
}

/**
 * Mengambil satu fragmen, lalu memasangnya sebagai isi wilayah.
 *
 * Status response ikut diperiksa, karena fetch tidak menganggap status 500
 * sebagai kegagalan. Tanpa pemeriksaan itu, halaman error akan terpasang
 * seolah-olah isi yang benar.
 * @param {string} alamat Alamat kerangka yang dituju.
 */
async function muatWilayah(alamat) {
  try {
    const respon = await fetch(alamatFragmen(alamat));
    if (!respon.ok) {
      tampilkanGagal(PESAN_GAGAL);
      return;
    }
    document.getElementById("wilayah").innerHTML = await respon.text();
  } catch (gagal) {
    tampilkanGagal(PESAN_GAGAL);
  }
}

/**
 * Berpindah ke satu alamat tanpa memuat ulang dokumen.
 * @param {string} alamat Alamat kerangka yang dituju.
 */
async function pindah(alamat) {
  history.pushState({}, "", alamat);
  await muatWilayah(alamat);
}

/**
 * Menangkap klik pada tautan di dalam aplikasi, lalu mengubahnya jadi pindah.
 * @param {MouseEvent} peristiwa Peristiwa klik yang naik ke document.
 */
function tanganiKlik(peristiwa) {
  const tautan = peristiwa.target.closest("a");
  if (!tautan || !tautan.pathname.startsWith(AWALAN_KERANGKA)) {
    return;
  }
  peristiwa.preventDefault();
  pindah(tautan.pathname + tautan.search);
}

/**
 * Menangkap pengiriman form penyaring, lalu mengubahnya jadi pindah.
 *
 * Tanpa JavaScript, form ini tetap terkirim ke server dan server yang
 * menyaring. Dengan JavaScript, hasilnya sama tetapi tanpa muat ulang.
 * @param {SubmitEvent} peristiwa Peristiwa submit yang naik ke document.
 */
function tanganiKirim(peristiwa) {
  const kata = document.getElementById("saring").value;
  peristiwa.preventDefault();
  pindah(`${AWALAN_KERANGKA}/katalog?saring=${encodeURIComponent(kata)}`);
}

/**
 * Menambah satu buku ke keranjang bila yang diklik adalah tombol Tambah.
 *
 * Listener-nya dipasang sekali di kerangka, bukan di tiap tombol. Karena
 * itu tombol yang baru masuk setelah perpindahan ikut jalan tanpa perlu
 * dihidupkan ulang.
 * @param {MouseEvent} peristiwa Peristiwa klik yang naik ke document.
 */
function tanganiTambah(peristiwa) {
  if (peristiwa.target.dataset.komponen !== "tombol") {
    return;
  }
  const jumlah = document.getElementById("jumlah");
  jumlah.textContent = String(Number(jumlah.textContent) + 1);
}

/** Memuat ulang wilayah ketika tombol kembali browser ditekan. */
function tanganiKembali() {
  muatWilayah(location.pathname + location.search);
}

/** Memasang seluruh listener kerangka, masing-masing satu kali. */
function pasangKerangka() {
  document.addEventListener("click", tanganiKlik);
  document.addEventListener("click", tanganiTambah);
  document.addEventListener("submit", tanganiKirim);
  window.addEventListener("popstate", tanganiKembali);
  document.getElementById("laporan").textContent =
    "kerangka: navigasi dan keranjang dipasang sekali di shell";
}

pasangKerangka();
