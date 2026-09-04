-- Migrasi 003: indeks untuk riwayat pesanan per pelanggan.
--
-- CREATE INDEX biasa mengunci tabel terhadap seluruh penulisan sampai
-- indeksnya selesai dibangun. Pada tabel produksi, kunci itu berarti
-- layanan berhenti menerima pesanan selama pembangunan berlangsung.
--
-- CONCURRENTLY membangun indeks tanpa kunci tersebut, dengan tiga syarat:
--   * tidak boleh berada di dalam blok transaksi, sehingga tanpa BEGIN
--   * pembangunannya memindai tabel dua kali, jadi lebih lama
--   * bila gagal, indeksnya tertinggal dalam keadaan INVALID dan harus
--     dihapus lalu dibuat ulang
--
-- Periksa indeks yang gagal dengan:
--   SELECT indexrelid::regclass FROM pg_index WHERE NOT indisvalid;

SET lock_timeout = '5s';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pesanan_pelanggan_waktu
  ON pesanan (pelanggan_id, dibuat_pada DESC);
