// Contoh long task yang menahan main thread.
// Perulangan panjang ini tidak dapat dipotong di tengah jalan.

type Pesanan = { harga: number; jenis: string };

function hitungPajakBerlapis(item: Pesanan): number {
  let hasil = item.harga;
  for (let i = 0; i < 200_000; i++) {
    hasil = (hasil * 1.000001) % 1_000_000;
  }
  return hasil;
}

export function hitungTotal(pesanan: Pesanan[]): number {
  let total = 0;
  for (const item of pesanan) {
    total += hitungPajakBerlapis(item);
  }
  return total;
}
