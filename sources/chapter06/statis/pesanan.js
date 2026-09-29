// Logika halaman demo Bab 6: mengambil satu pesanan, lalu menampilkan
// rinciannya beserta jumlah query yang dipakai server. Dilayani aplikasi.py
// pada /aset/pesanan.js, dan diuji e2e/pesanan.spec.ts lewat Playwright.

/** Jalur alamat untuk kedua cara mengambil pesanan yang sama. */
const JALUR_SEHAT = "/api/pesanan";
const JALUR_N_PLUS_1 = "/api/pesanan-n1";
/** Ditampilkan selama permintaan berjalan, dan dipakai pengujian E2E sebagai
 *  penanda bahwa penggambaran yang lama sudah dibatalkan. */
const TEKS_SEDANG_MEMUAT = "Jumlah query: sedang memuat";

/**
 * Menyusun alamat yang diminta dari isi kedua kolom di halaman.
 *
 * Jalurnya dipilih di satu tempat saja, sehingga pengujian E2E cukup mengubah
 * kotak centangnya untuk berpindah jalur.
 *
 * @param {string} idPesanan Id pesanan yang diketik pengguna, apa adanya.
 * @param {boolean} pakaiNPlus1 Benar bila jalur N+1 yang diminta.
 * @returns {string} Alamat lengkap yang siap diminta.
 */
function susunAlamat(idPesanan, pakaiNPlus1) {
  const jalur = pakaiNPlus1 ? JALUR_N_PLUS_1 : JALUR_SEHAT;
  return `${jalur}/${encodeURIComponent(idPesanan)}`;
}

/**
 * Menampilkan pesan kegagalan, lalu mengosongkan daftar itemnya.
 *
 * Kegagalan ikut ditampilkan di halaman, bukan hanya di console, agar
 * pengujian E2E dapat memeriksanya seperti memeriksa keberhasilan.
 *
 * @param {number} status Status HTTP yang diterima.
 * @param {string} pesan Penjelasan singkat dari server.
 * @returns {void}
 */
function tampilkanKegagalan(status, pesan) {
  document.getElementById("ringkasan").textContent =
    `Gagal ${status}: ${pesan}`;
  document.getElementById("daftar-item").replaceChildren();
}

/**
 * Mengubah satu item pesanan menjadi satu baris daftar yang siap ditempel.
 *
 * @param {{judul: string, jumlah: number, harga_satuan: number}} item
 *        Satu item pesanan dari response.
 * @returns {HTMLLIElement} Baris daftar berisi judul, jumlah, dan harganya.
 */
function buatBarisItem(item) {
  const baris = document.createElement("li");
  baris.textContent = `${item.judul} x ${item.jumlah} @ ${item.harga_satuan}`;
  return baris;
}

/**
 * Menampilkan satu pesanan beserta seluruh itemnya.
 *
 * @param {{pelanggan: string, total: number, status: string,
 *          item: Array<{judul: string, jumlah: number,
 *                       harga_satuan: number}>}} pesanan Isi response.
 * @returns {void}
 */
function tampilkanPesanan(pesanan) {
  document.getElementById("ringkasan").textContent =
    `${pesanan.pelanggan} membayar ${pesanan.total} rupiah ` +
    `(status ${pesanan.status})`;
  const barisItem = pesanan.item.map(buatBarisItem);
  document.getElementById("daftar-item").replaceChildren(...barisItem);
}

/**
 * Menampilkan jumlah query yang dilaporkan server lewat header.
 *
 * Angka inilah yang membedakan kedua jalur, karena isi responsenya sama
 * persis. Bagian ini sengaja digambar paling akhir, sehingga pengujian E2E
 * yang menunggunya berubah dapat yakin seluruh halaman sudah diperbarui.
 *
 * @param {string|null} nilaiHeader Isi header X-Query-Count, bila ada.
 * @returns {void}
 */
function tampilkanJumlahQuery(nilaiHeader) {
  const teks = nilaiHeader === null ? "tidak dilaporkan" : nilaiHeader;
  document.getElementById("jumlah-query").textContent =
    `Jumlah query: ${teks}`;
}

/**
 * Mengambil pesanan yang diminta, lalu memperbarui seluruh bagian halaman.
 *
 * @returns {Promise<void>} Selesai setelah halaman diperbarui.
 */
async function muatPesanan() {
  const idPesanan = document.getElementById("id-pesanan").value;
  const pakaiNPlus1 = document.getElementById("pakai-n1").checked;
  document.getElementById("jumlah-query").textContent = TEKS_SEDANG_MEMUAT;
  const response = await fetch(susunAlamat(idPesanan, pakaiNPlus1));
  const isi = await response.json();
  if (response.ok) {
    tampilkanPesanan(isi);
  } else {
    tampilkanKegagalan(response.status, isi.pesan);
  }
  tampilkanJumlahQuery(response.headers.get("X-Query-Count"));
}

document.getElementById("muat").addEventListener("click", muatPesanan);
