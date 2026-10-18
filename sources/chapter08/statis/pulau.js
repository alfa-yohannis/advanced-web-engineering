// Skrip varian islands: hanya satu bagian halaman yang dihidupkan.
// Daftar katalognya sudah tergambar dari HTML yang dikirim server, dan skrip
// ini hanya menyaringnya ketika pengunjung mengetik.

/**
 * Menyembunyikan baris yang judulnya tidak memuat kata yang diketik.
 * @param {Event} peristiwa Peristiwa input dari kotak penyaring.
 */
function saringBaris(peristiwa) {
  const kata = peristiwa.target.value.toLowerCase();
  const daftar = document.querySelectorAll("#daftar li");
  for (const baris of daftar) {
    const cocok = baris.textContent.toLowerCase().includes(kata);
    baris.hidden = !cocok;
  }
}

document.getElementById("saring")?.addEventListener("input", saringBaris);
