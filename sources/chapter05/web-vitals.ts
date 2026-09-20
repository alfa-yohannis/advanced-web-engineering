/**
 * Mengukur Core Web Vitals pada kunjungan nyata, lalu melaporkannya ke server.
 *
 * Ketiga metrik diambil dari PerformanceObserver milik browser, bukan dari
 * alat ukur di luar. Angka yang terkumpul inilah yang dinilai gate
 * anggaran, karena angka lab saja tidak membuktikan pengalaman pengguna.
 *
 * Kompilasi (dari sources/chapter05):
 *   npx -p typescript tsc --target es2022 --module es2022 --strict \
 *     --lib es2022,dom --outDir statis web-vitals.ts
 */

/** Entri pergeseran tata letak, belum ada di pustaka tipe bawaan browser. */
interface PergeseranTataLetak extends PerformanceEntry {
  value: number;
  hadRecentInput: boolean;
}

/** Pengaturan observer beserta ambang durasinya, juga belum ada di tipe bawaan. */
interface PengaturanObserverInteraksi extends PerformanceObserverInit {
  durationThreshold: number;
}

const ALAMAT_LAPORAN = "/api/vitals";
/** Interaksi lebih singkat dari ambang ini tidak dilaporkan browser. */
const AMBANG_INTERAKSI_MS = 16;

const laporan = { lcp_ms: 0, inp_ms: 0, cls: 0 };
let sudahDikirim = false;

/**
 * Mencatat elemen terbesar yang tergambar, yaitu nilai LCP terakhir.
 * @param daftar entri largest-contentful-paint dari browser
 */
function catatLcp(daftar: PerformanceObserverEntryList): void {
  const entri = daftar.getEntries();
  const terakhir = entri[entri.length - 1];
  if (terakhir !== undefined) {
    laporan.lcp_ms = Math.round(terakhir.startTime);
  }
}

/**
 * Mencatat interaksi terlama sebagai pendekatan INP.
 * @param daftar entri event dari browser
 */
function catatInp(daftar: PerformanceObserverEntryList): void {
  for (const entri of daftar.getEntries()) {
    laporan.inp_ms = Math.max(laporan.inp_ms, Math.round(entri.duration));
  }
}

/**
 * Menjumlahkan pergeseran tata letak yang tidak disebabkan interaksi pengguna.
 * @param daftar entri layout-shift dari browser
 */
function catatCls(daftar: PerformanceObserverEntryList): void {
  for (const entri of daftar.getEntries()) {
    const pergeseran = entri as PergeseranTataLetak;
    if (!pergeseran.hadRecentInput) {
      laporan.cls = Number((laporan.cls + pergeseran.value).toFixed(4));
    }
  }
}

/**
 * Mengirim laporan sekali saja, memakai sendBeacon agar tidak menahan halaman.
 */
function kirimLaporan(): void {
  if (sudahDikirim) {
    return;
  }
  sudahDikirim = true;
  navigator.sendBeacon(ALAMAT_LAPORAN, JSON.stringify(laporan));
}

/** Mengirim laporan ketika halaman ditinggalkan, bukan ketika selesai dimuat. */
function kirimBilaTersembunyi(): void {
  if (document.visibilityState === "hidden") {
    kirimLaporan();
  }
}

new PerformanceObserver(catatLcp).observe({
  type: "largest-contentful-paint",
  buffered: true,
});
const PENGATURAN_INTERAKSI: PengaturanObserverInteraksi = {
  type: "event",
  buffered: true,
  durationThreshold: AMBANG_INTERAKSI_MS,
};
new PerformanceObserver(catatInp).observe(PENGATURAN_INTERAKSI);
new PerformanceObserver(catatCls).observe({
  type: "layout-shift",
  buffered: true,
});
document.addEventListener("visibilitychange", kirimBilaTersembunyi);
