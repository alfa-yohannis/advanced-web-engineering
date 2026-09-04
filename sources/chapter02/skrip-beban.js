// Skrip k6 untuk uji beban.
// PERINGATAN: hanya dijalankan pada sistem milik sendiri, atau setelah
// memperoleh izin tertulis dari pengelola sistem. Menjalankannya pada situs
// produksi tanpa izin mengganggu layanan dan dapat dianggap serangan.
//
// Jalankan dengan: k6 run --vus 20 --duration 60s skrip-beban.js

import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  thresholds: {
    http_req_duration: ["p(50)<300", "p(95)<800"],
  },
};

export default function () {
  const res = http.get("http://localhost:8080/");
  check(res, { "status 200": (r) => r.status === 200 });
  sleep(1);
}
