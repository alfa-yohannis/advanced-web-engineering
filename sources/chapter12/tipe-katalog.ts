// Di-generate dari kontrak.json oleh buat_tipe.py.
// Jangan diubah tangan: jalankan ulang generatornya.
// Judul kontrak: Katalog Buku versi 1.0.0.

export interface Buku {
  id: number;
  judul: string;
  harga: number;
  stok: number;
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
  status: "diterima" | "diproses";
}

export interface Kesalahan {
  type: string;
  title: string;
  status: number;
  detail?: string;
}

export interface KlienKatalog {
  // GET /v1/buku
  ambilBuku(pertanyaan: {
    halaman?: number;
    per_halaman?: number;
    saring?: string;
  }): Promise<HalamanBuku>;
  // POST /v1/pesanan
  buatPesanan(pertanyaan: {
    idempotency_key: string;
  }, isi: PesananBaru): Promise<Pesanan>;
}
