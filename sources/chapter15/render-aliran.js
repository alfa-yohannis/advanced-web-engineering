// Pengukur render jawaban Bab 15: mengulang cara frontend ketiga sistem RAG
// merender jawaban yang dialirkan, lalu mencatat lama tiap pembaruan. File ini
// dimuat halaman uji yang disusun ukur-render-aliran.py, bukan dibuka sendiri.

/**
 * Pola penanda sitasi, disalin dari CitationLinker.REFERENCE di web/app.js
 * ketiga sistem, agar biaya pencocokannya sama.
 */
const POLA_PENANDA_SITASI = new RegExp(
  '[\\[【]((?:(?:n|no\\.?|sumber|source|nguồn)\\s*)?\\d{1,2}' +
  '(?:\\s*[,;–-]\\s*(?:(?:n|no\\.?|sumber|source|nguồn)\\s*)?\\d{1,2})*)[\\]】]',
  'giu');

/** Elemen yang teksnya tidak diubah menjadi chip, sama dengan aslinya. */
const PEMILIH_TERLINDUNG = 'code, pre, a';

/** Rentang nomor terpanjang yang dijabarkan, sama dengan MAX_RANGE aslinya. */
const RENTANG_TERPANJANG = 10;

/**
 * Membaca daftar potongan jawaban yang disisipkan skrip Python ke halaman.
 * @returns {{potongan: string[]}} Konfigurasi satu kali pengukuran.
 */
function bacaKonfigurasi() {
  return JSON.parse(document.getElementById('konfigurasi').textContent);
}

/**
 * Mengubah markdown menjadi HTML yang sudah dibersihkan, persis seperti
 * MarkdownRenderer.render di ketiga frontend.
 * @param {string} teksMarkdown Seluruh teks jawaban yang sudah terkumpul.
 * @returns {string} HTML yang siap dipasang lewat innerHTML.
 */
function renderMarkdown(teksMarkdown) {
  return DOMPurify.sanitize(marked.parse(teksMarkdown),
                            { ADD_ATTR: ['target', 'rel'] });
}

/**
 * Menjabarkan isi satu penanda menjadi nomor sitasi, misalnya "1-3"
 * menjadi 1, 2, 3, mengikuti #numbersIn pada CitationLinker.
 * @param {string} isiPenanda Teks di antara kurung siku.
 * @returns {string[]} Nomor sitasi sebagai teks.
 */
function ambilNomorSitasi(isiPenanda) {
  const daftarNomor = [];
  for (const bagian of isiPenanda.split(/[,;]/)) {
    const nomorDitemukan = bagian.match(/\d{1,2}/g).map(Number);
    const nomorPertama = nomorDitemukan[0];
    const nomorTerakhir = nomorDitemukan[1];
    const rentangSah = nomorDitemukan.length === 2 &&
      nomorTerakhir > nomorPertama &&
      nomorTerakhir - nomorPertama < RENTANG_TERPANJANG;
    if (rentangSah) {
      for (let nomor = nomorPertama; nomor <= nomorTerakhir; nomor += 1) {
        daftarNomor.push(String(nomor));
      }
    } else {
      daftarNomor.push(...nomorDitemukan.map(String));
    }
  }
  return daftarNomor;
}

/**
 * Penangan klik chip. Isinya kosong, karena yang diukur hanya biaya
 * memasang penangannya, bukan akibat kliknya.
 */
function tanganiKlikSitasi() {}

/**
 * Membuat satu chip sitasi, sama dengan #buildChip pada CitationLinker.
 * @param {string} nomorSitasi Nomor yang ditampilkan di chip.
 * @returns {HTMLSpanElement} Elemen chip yang sudah punya penangan klik.
 */
function buatChipSitasi(nomorSitasi) {
  const chip = document.createElement('span');
  chip.className = 'citation-marker';
  chip.dataset.citation = nomorSitasi;
  chip.textContent = nomorSitasi;
  chip.addEventListener('click', tanganiKlikSitasi);
  return chip;
}

/**
 * Memecah satu simpul teks menjadi teks biasa dan chip sitasi.
 * @param {Text} simpulTeks Simpul yang memuat penanda.
 * @param {RegExpMatchArray[]} daftarPenanda Penanda yang ditemukan di simpul.
 */
function gantiSimpulTeks(simpulTeks, daftarPenanda) {
  const teks = simpulTeks.nodeValue;
  const kumpulan = document.createDocumentFragment();
  let posisi = 0;
  for (const penanda of daftarPenanda) {
    if (penanda.index > posisi) {
      kumpulan.appendChild(
        document.createTextNode(teks.slice(posisi, penanda.index)));
    }
    for (const nomorSitasi of ambilNomorSitasi(penanda[1])) {
      kumpulan.appendChild(buatChipSitasi(nomorSitasi));
    }
    posisi = penanda.index + penanda[0].length;
  }
  if (posisi < teks.length) {
    kumpulan.appendChild(document.createTextNode(teks.slice(posisi)));
  }
  simpulTeks.parentNode.replaceChild(kumpulan, simpulTeks);
}

/**
 * Mengganti seluruh penanda sitasi di bawah satu elemen dengan chip,
 * mengikuti CitationLinker.apply: dikumpulkan dulu, baru diganti.
 * @param {HTMLElement} elemenAkar Elemen yang memuat jawaban.
 */
function pasangChipSitasi(elemenAkar) {
  const penjelajah = document.createTreeWalker(elemenAkar, NodeFilter.SHOW_TEXT);
  const daftarCalon = [];
  while (penjelajah.nextNode()) {
    const simpulTeks = penjelajah.currentNode;
    const induk = simpulTeks.parentElement;
    if (!induk || induk.closest(PEMILIH_TERLINDUNG)) continue;
    const daftarPenanda = [...simpulTeks.nodeValue.matchAll(POLA_PENANDA_SITASI)];
    if (daftarPenanda.length > 0) daftarCalon.push([simpulTeks, daftarPenanda]);
  }
  for (const [simpulTeks, daftarPenanda] of daftarCalon) {
    gantiSimpulTeks(simpulTeks, daftarPenanda);
  }
}

/**
 * Satu pembaruan seperti appendText: seluruh teks dirender ulang, lalu
 * chip sitasi dipasang ulang.
 * @param {HTMLElement} elemenJawaban Tempat jawaban ditampilkan.
 * @param {string} teksTerkumpul Seluruh teks yang sudah diterima.
 */
function perbaruiJawaban(elemenJawaban, teksTerkumpul) {
  elemenJawaban.innerHTML = renderMarkdown(teksTerkumpul);
  pasangChipSitasi(elemenJawaban);
}

/**
 * Mengalirkan potongan satu per satu dan mencatat lama tiap pembaruan.
 * @param {string[]} daftarPotongan Potongan jawaban seukuran satu token.
 * @param {HTMLElement} elemenJawaban Tempat jawaban ditampilkan.
 * @returns {number[]} Lama tiap pembaruan dalam milidetik.
 */
function ukurAliran(daftarPotongan, elemenJawaban) {
  const daftarLama = [];
  let teksTerkumpul = '';
  for (const potongan of daftarPotongan) {
    teksTerkumpul += potongan;
    const mulai = performance.now();
    perbaruiJawaban(elemenJawaban, teksTerkumpul);
    daftarLama.push(performance.now() - mulai);
  }
  return daftarLama;
}

/**
 * Merender jawaban lengkap satu kali, sebagai benchmark batas: biaya yang
 * tetap dibayar meski jawaban dirender hanya sekali di akhir.
 * @param {string} teksLengkap Seluruh jawaban.
 * @param {HTMLElement} elemenJawaban Elemen kosong untuk render ini.
 * @returns {number} Lama render dalam milidetik.
 */
function ukurRenderSekali(teksLengkap, elemenJawaban) {
  const mulai = performance.now();
  perbaruiJawaban(elemenJawaban, teksLengkap);
  return performance.now() - mulai;
}

/** Menjalankan kedua pengukuran, lalu menulis hasilnya ke elemen hasil. */
function jalankanPengukuran() {
  marked.setOptions({ gfm: true, breaks: true });
  const konfigurasi = bacaKonfigurasi();
  const lamaPerPembaruan = ukurAliran(konfigurasi.potongan,
                                      document.getElementById('jawaban'));
  const lamaSekali = ukurRenderSekali(konfigurasi.potongan.join(''),
                                      document.getElementById('jawaban-sekali'));
  document.getElementById('hasil').textContent = JSON.stringify({
    per_pembaruan_ms: lamaPerPembaruan,
    sekali_ms: lamaSekali,
  });
}

jalankanPengukuran();
