// Hidrasi selektif: hanya bagian yang ditandai data-pulau yang dihidupkan.
// Kartu buku tetap HTML yang dikirim server, tidak dibangun ulang di browser,
// sehingga datanya pun tidak perlu ikut dititipkan ke halaman.

/** Nama varian, ikut dicetak pada baris laporan. */
const VARIAN = "selektif";

/**
 * Membaca state yang dititipkan server di dalam halaman.
 * @returns {{keranjang: number, saringan: string}} State kedua pulau.
 */
function bacaState() {
  const blok = document.getElementById("state");
  return JSON.parse(blok.textContent);
}

/**
 * Menghidupkan kotak penyaring beserta isi terakhirnya.
 * @param {Element} node Elemen input penyaring.
 * @param {object} state State kedua pulau.
 */
function hidupkanPenyaring(node, state) {
  node.value = state.saringan;
  node.addEventListener("input", saringBaris);
}

/**
 * Menghidupkan penghitung keranjang dari state.
 *
 * Satu listener dipasang di daftar, bukan di tiap tombol, sehingga jumlah
 * listener tidak ikut bertambah ketika jumlah kartunya bertambah.
 * @param {Element} node Elemen paragraf keranjang.
 * @param {object} state State kedua pulau.
 */
function hidupkanKeranjang(node, state) {
  node.querySelector("#jumlah").textContent = String(state.keranjang);
  document.getElementById("daftar")
    .addEventListener("click", tambahKeranjang);
}

/**
 * Menghidupkan satu pulau sesuai jenisnya.
 * @param {Element} node Elemen yang membawa atribut data-pulau.
 * @param {object} state State kedua pulau.
 */
function hidupkanPulau(node, state) {
  const jenis = node.dataset.pulau;
  if (jenis === "penyaring") {
    hidupkanPenyaring(node, state);
    return;
  }
  if (jenis === "keranjang") {
    hidupkanKeranjang(node, state);
  }
}

/**
 * Menyembunyikan baris yang judulnya tidak memuat kata yang diketik.
 * @param {Event} peristiwa Peristiwa input dari kotak penyaring.
 */
function saringBaris(peristiwa) {
  const kata = peristiwa.target.value.toLowerCase();
  for (const baris of document.querySelectorAll("#daftar li")) {
    baris.hidden = !baris.textContent.toLowerCase().includes(kata);
  }
}

/**
 * Menambah satu buku ke keranjang bila yang diklik adalah tombol Tambah.
 * @param {Event} peristiwa Peristiwa click yang naik dari dalam daftar.
 */
function tambahKeranjang(peristiwa) {
  if (peristiwa.target.dataset.komponen !== "tombol") {
    return;
  }
  const jumlah = document.getElementById("jumlah");
  jumlah.textContent = String(Number(jumlah.textContent) + 1);
}

/**
 * Menuliskan hasil pengukuran ke halaman, agar dapat dibaca langsung.
 * @param {number} komponen Jumlah pulau yang dihidupkan.
 * @param {number} lama Lama hidrasi dalam milidetik.
 */
function laporkan(komponen, lama) {
  const buku = document.querySelectorAll("#daftar li").length;
  document.getElementById("laporan").textContent =
    `${VARIAN}: ${buku} buku, ${komponen} komponen dihidupkan, ` +
    `${lama.toFixed(2)} ms`;
}

/** Menghidupkan kedua pulau saja, lalu melaporkan biayanya. */
function hidrasiSelektif() {
  const mulai = performance.now();
  const state = bacaState();
  const daftar = document.querySelectorAll("[data-pulau]");
  for (const node of daftar) {
    hidupkanPulau(node, state);
  }
  laporkan(daftar.length, performance.now() - mulai);
}

hidrasiSelektif();
