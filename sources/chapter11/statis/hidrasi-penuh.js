// Hidrasi penuh: seluruh komponen di halaman dihidupkan, termasuk kartu yang
// tidak pernah disentuh pengguna. Inilah bentuk yang paling mudah ditulis,
// dan paling mahal dijalankan ketika halamannya besar.

/** Nama varian, ikut dicetak pada baris laporan. */
const VARIAN = "penuh";

/**
 * Membaca state yang dititipkan server di dalam halaman.
 * @returns {{buku: object, keranjang: number, saringan: string}} State awal.
 */
function bacaState() {
  const blok = document.getElementById("state");
  return JSON.parse(blok.textContent);
}

/**
 * Menghidupkan satu kartu buku, yaitu mencocokkannya dengan state.
 * @param {Element} node Elemen kartu yang membawa data-id.
 * @param {object} state State awal seluruh halaman.
 */
function hidupkanKartu(node, state) {
  const buku = state.buku[node.dataset.id];
  // Inilah biaya yang dibayar untuk tiap kartu: datanya dibaca, lalu kartu
  // ditandai sudah dihidupkan, walaupun kartu itu tidak punya perilaku.
  node.dataset.stok = String(buku.stok);
  node.dataset.hidrasi = "selesai";
}

/**
 * Menghidupkan satu tombol Tambah.
 * @param {Element} node Elemen tombol.
 */
function hidupkanTombol(node) {
  node.addEventListener("click", tambahKeranjang);
}

/**
 * Menghidupkan kotak penyaring beserta isi terakhirnya.
 * @param {Element} node Elemen input penyaring.
 * @param {object} state State awal seluruh halaman.
 */
function hidupkanPenyaring(node, state) {
  node.value = state.saringan;
  node.addEventListener("input", saringBaris);
}

/**
 * Menghidupkan penghitung keranjang dari state.
 * @param {Element} node Elemen paragraf keranjang.
 * @param {object} state State awal seluruh halaman.
 */
function hidupkanKeranjang(node, state) {
  node.querySelector("#jumlah").textContent = String(state.keranjang);
}

/**
 * Menghidupkan satu komponen sesuai jenisnya.
 * @param {Element} node Elemen yang membawa atribut data-komponen.
 * @param {object} state State awal seluruh halaman.
 */
function hidupkanKomponen(node, state) {
  const jenis = node.dataset.komponen;
  if (jenis === "kartu") {
    hidupkanKartu(node, state);
    return;
  }
  if (jenis === "tombol") {
    hidupkanTombol(node);
    return;
  }
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

/** Menambah satu buku ke penghitung keranjang. */
function tambahKeranjang() {
  const jumlah = document.getElementById("jumlah");
  jumlah.textContent = String(Number(jumlah.textContent) + 1);
}

/**
 * Menuliskan hasil pengukuran ke halaman, agar dapat dibaca langsung.
 * @param {number} komponen Jumlah komponen yang dihidupkan.
 * @param {number} lama Lama hidrasi dalam milidetik.
 */
function laporkan(komponen, lama) {
  const buku = document.querySelectorAll("#daftar li").length;
  document.getElementById("laporan").textContent =
    `${VARIAN}: ${buku} buku, ${komponen} komponen dihidupkan, ` +
    `${lama.toFixed(2)} ms`;
}

/** Menghidupkan seluruh komponen halaman, lalu melaporkan biayanya. */
function hidrasiPenuh() {
  const mulai = performance.now();
  const state = bacaState();
  const daftar = document.querySelectorAll("[data-komponen]");
  for (const node of daftar) {
    hidupkanKomponen(node, state);
  }
  laporkan(daftar.length, performance.now() - mulai);
}

hidrasiPenuh();
