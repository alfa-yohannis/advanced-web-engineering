// Di-generate dari kontrak-v2.json oleh buat_tipe.py.
// Jangan diubah tangan: jalankan ulang generatornya.
// Judul kontrak: Katalog Buku versi 2.0.0.

export interface Buku {
  id: number;
  judul: string;
  harga_rupiah: number;
  stok: number;
  penerbit?: string;
}

export interface HalamanBuku {
  item: Buku[];
  halaman: number;
  per_halaman: number;
  total: number;
  berikutnya?: string;
}

export interface PesananBaru {
  id_buku: number;
  jumlah: number;
}

export interface Pesanan {
  id: string;
  id_buku: number;
  jumlah: number;
  status: "diterima" | "diproses" | "dibatalkan";
}

export interface Kesalahan {
  type: string;
  title: string;
  status: number;
  detail?: string;
}

export interface KlienKatalog {
  // GET /v2/buku
  ambilBuku(pertanyaan: {
    halaman?: number;
    per_halaman?: number;
    saring?: string;
  }): Promise<HalamanBuku>;
  // POST /v2/pesanan
  buatPesanan(pertanyaan: {
    idempotency_key: string;
  }, isi: PesananBaru): Promise<Pesanan>;
}
