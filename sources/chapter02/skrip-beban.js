// Skrip k6 untuk uji beban API kerangka Bab 1 di port 8050.
// PERINGATAN: hanya dijalankan pada sistem milik sendiri, atau setelah
// memperoleh izin tertulis dari pengelola sistem. Menjalankannya pada situs
// produksi tanpa izin mengganggu layanan dan dapat dianggap serangan.
//
// Sasarannya API Bab 1, jadi API itu dinyalakan lebih dahulu dari
// sources/chapter01 dengan: python3 aplikasi.py &
// Lalu dari sources/chapter02: k6 run --vus 20 --duration 60s skrip-beban.js

import http from "k6/http";
import { check, sleep } from "k6";

const ALAMAT_SASARAN = "http://127.0.0.1:8050/buku";
const STATUS_BERHASIL = 200;
const JEDA_ANTARPERMINTAAN_DETIK = 1;

export const options = {
  thresholds: {
    http_req_duration: ["p(50)<300", "p(95)<800"],
  },
};

/**
 * Memeriksa apakah satu response berstatus berhasil. Ditulis di tingkat
 * modul, bukan sebagai lambda, agar aturan pemeriksaannya terbaca sendiri.
 * @param {Object} response response HTTP yang diterima k6
 * @returns {boolean} true bila statusnya 200
 */
function statusBerhasil(response) {
  return response.status === STATUS_BERHASIL;
}

/**
 * Satu putaran pengguna tiruan: meminta daftar buku, memeriksa statusnya,
 * lalu diam sejenak agar bebannya menyerupai pengguna, bukan banjir
 * permintaan tanpa jeda.
 */
export default function () {
  const response = http.get(ALAMAT_SASARAN);
  check(response, { "status 200": statusBerhasil });
  sleep(JEDA_ANTARPERMINTAAN_DETIK);
}
