// Konfigurasi Playwright untuk pengujian E2E Bab 6.
// Pemakaian (dari sources/chapter06, setelah docker compose up -d):
//   npx playwright test --config e2e/playwright.config.ts
// Browsernya memakai Google Chrome yang sudah terpasang di sistem lewat
// channel "chrome", sehingga tidak ada browser yang perlu diunduh.

import { defineConfig, devices } from "@playwright/test";

/** Alamat aplikasi yang diuji, sama dengan PORT di aplikasi.py. */
const ALAMAT_APLIKASI = "http://127.0.0.1:8020";
/** Batas waktu menunggu aplikasi menyala sebelum pengujian dimulai. */
const BATAS_WAKTU_SERVER_MS = 30000;
/** Batas waktu satu pengujian. Jalur N+1 memang lebih lambat. */
const BATAS_WAKTU_UJI_MS = 20000;

export default defineConfig({
  testDir: ".",
  timeout: BATAS_WAKTU_UJI_MS,
  // Satu worker saja, agar jumlah query yang terbaca tidak tercampur dengan
  // permintaan dari pengujian lain yang berjalan bersamaan.
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: ALAMAT_APLIKASI,
  },
  projects: [
    {
      name: "chrome",
      use: { ...devices["Desktop Chrome"], channel: "chrome" },
    },
  ],
  // Aplikasinya dinyalakan Playwright bila belum menyala, sehingga pengujian
  // E2E dapat dijalankan dengan satu perintah dari keadaan bersih. Perintahnya
  // dijalankan dari sources/, bukan dari sources/chapter06, agar jalur venv
  // yang diterima Python tidak memuat ".." dan Python tidak memperingatkan
  // sys.prefix yang tidak terduga.
  webServer: {
    command: ".venv/bin/python chapter06/aplikasi.py",
    cwd: "../..",
    url: ALAMAT_APLIKASI,
    reuseExistingServer: true,
    timeout: BATAS_WAKTU_SERVER_MS,
  },
});
