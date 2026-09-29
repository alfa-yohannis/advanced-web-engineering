// Pengujian E2E halaman rincian pesanan, dijalankan di Google Chrome sungguhan.
// Yang diperiksa adalah apa yang terbaca pengguna di layar, bukan nilai
// kembalian sebuah fungsi. Karena itu lapisan ini menangkap cacat yang lolos
// dari unit test dan integration test, misalnya tombol yang tidak terhubung,
// modul yang gagal dimuat, atau daftar yang tidak pernah tergambar.
// Pemakaian (dari sources/chapter06, setelah docker compose up -d):
//   npx playwright test --config e2e/playwright.config.ts

import { expect, test, type Page } from "@playwright/test";

/** Pesanan pertama pada data uji Bab 3 punya tiga item. */
const ID_PESANAN_UJI = "1";
/** Lebih besar daripada id terbesar pada data uji. */
const ID_PESANAN_TIDAK_ADA = "99000000";
const ID_BUKAN_ANGKA = "dua-belas";
/** Jalur sehat selalu memakai dua query, berapa pun banyak itemnya. */
const QUERY_JALUR_SEHAT = 2;

/**
 * Mengambil teks seluruh baris daftar item apa adanya.
 *
 * Perbandingan dilakukan pada teks yang tergambar, bukan pada response JSON,
 * sehingga kesalahan penggambaran ikut tertangkap.
 *
 * @param halaman Halaman yang sedang diuji.
 * @returns Daftar teks tiap baris item, berurutan seperti di layar.
 */
async function bacaDaftarItem(halaman: Page): Promise<string[]> {
  return halaman.locator("#daftar-item li").allTextContents();
}

/**
 * Menekan tombol Muat pesanan, lalu menunggu halaman selesai diperbarui.
 *
 * Penantiannya bertumpu pada satu sifat halaman: baris jumlah query digambar
 * paling akhir. Begitu angkanya cocok, seluruh bagian lain pasti sudah
 * tergambar, sehingga pembacaan sesudahnya tidak perlu jeda buatan.
 *
 * @param halaman Halaman yang sedang diuji.
 * @param idPesanan Id yang diisikan ke kolom masukan.
 * @param pakaiNPlus1 Benar bila kotak centang jalur N+1 ikut dicentang.
 * @param jumlahQueryDiharapkan Angka yang ditunggu pada baris jumlah query.
 */
async function muatPesanan(
  halaman: Page,
  idPesanan: string,
  pakaiNPlus1: boolean,
  jumlahQueryDiharapkan: number,
): Promise<void> {
  await halaman.fill("#id-pesanan", idPesanan);
  await halaman.locator("#pakai-n1").setChecked(pakaiNPlus1);
  await halaman.click("#muat");
  await expect(halaman.locator("#jumlah-query")).toHaveText(
    `Jumlah query: ${jumlahQueryDiharapkan}`,
  );
}

test("halaman kosong sebelum tombol ditekan", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#ringkasan")).toHaveText(
    "Belum ada pesanan yang dimuat.",
  );
  await expect(page.locator("#daftar-item li")).toHaveCount(0);
});

test("jalur sehat menampilkan item dan melaporkan dua query", async ({
  page,
}) => {
  await page.goto("/");
  await muatPesanan(page, ID_PESANAN_UJI, false, QUERY_JALUR_SEHAT);
  await expect(page.locator("#ringkasan")).toContainText("membayar");
  const jumlahItem = (await bacaDaftarItem(page)).length;
  expect(jumlahItem).toBeGreaterThan(1);
});

test("jalur N+1 tampak sama di layar tetapi memakai query lebih banyak",
  async ({ page }) => {
    await page.goto("/");
    await muatPesanan(page, ID_PESANAN_UJI, false, QUERY_JALUR_SEHAT);
    const ringkasanSehat = await page.locator("#ringkasan").textContent();
    const itemSehat = await bacaDaftarItem(page);

    const queryNPlus1 = QUERY_JALUR_SEHAT + itemSehat.length;
    await muatPesanan(page, ID_PESANAN_UJI, true, queryNPlus1);
    const ringkasanNPlus1 = await page.locator("#ringkasan").textContent();
    const itemNPlus1 = await bacaDaftarItem(page);

    expect(ringkasanNPlus1).toBe(ringkasanSehat);
    expect(itemNPlus1).toEqual(itemSehat);
  });

test("id yang tidak ada ditampilkan sebagai kegagalan 404", async ({
  page,
}) => {
  await page.goto("/");
  await muatPesanan(page, ID_PESANAN_TIDAK_ADA, false, 1);
  await expect(page.locator("#ringkasan")).toContainText("Gagal 404");
  await expect(page.locator("#daftar-item li")).toHaveCount(0);
});

test("id bukan angka ditolak tanpa menyentuh basis data", async ({ page }) => {
  await page.goto("/");
  await muatPesanan(page, ID_BUKAN_ANGKA, false, 0);
  await expect(page.locator("#ringkasan")).toContainText("Gagal 400");
});
