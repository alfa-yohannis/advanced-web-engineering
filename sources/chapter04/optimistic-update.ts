// Optimistic update di browser untuk Bab 4: tampilan diubah lebih dahulu,
// lalu dikembalikan bila server menolak.
// Pemeriksaan tipe, dari sources/chapter04:
//   npx -p typescript tsc --noEmit --strict --lib es2022,dom optimistic-update.ts

const ALAMAT_SUKA = "/api/buku/suka";

/** Keadaan tombol suka yang digambar ke layar. */
interface KeadaanSuka {
  sudahSuka: boolean;
  jumlahSuka: number;
  sedangMenyimpan: boolean;
}

/** Fungsi milik halaman yang menggambar ulang tombol setiap keadaannya berubah. */
type Penggambar = (keadaan: KeadaanSuka) => void;

/**
 * Menghitung keadaan sesudah tombol ditekan, tanpa menunggu server.
 * Dipisahkan dari tekanSuka agar dapat diuji tanpa browser dan tanpa jaringan.
 */
function keadaanSesudahKlik(sebelum: KeadaanSuka): KeadaanSuka {
  const sudahSuka = !sebelum.sudahSuka;
  return {
    sudahSuka,
    jumlahSuka: sebelum.jumlahSuka + (sudahSuka ? 1 : -1),
    sedangMenyimpan: true,
  };
}

/**
 * Menekan tombol suka secara optimistis.
 *
 * Layar langsung diperbarui, sehingga pengguna tidak menunggu satu RTT pun.
 * Bila server menolak atau jaringan putus, keadaan sebelum klik dipasang
 * kembali. PUT dan DELETE dipilih karena keduanya idempoten, sehingga aman
 * diulang bila jawabannya hilang di jalan.
 */
async function tekanSuka(
  idBuku: number,
  sebelum: KeadaanSuka,
  gambarUlang: Penggambar,
): Promise<KeadaanSuka> {
  const sesudah = keadaanSesudahKlik(sebelum);
  gambarUlang(sesudah); // Pengguna melihat hasilnya sebelum server menjawab.
  try {
    const jawaban = await fetch(`${ALAMAT_SUKA}/${idBuku}`, {
      method: sesudah.sudahSuka ? "PUT" : "DELETE",
    });
    if (!jawaban.ok) {
      throw new Error(`server menolak dengan status ${jawaban.status}`);
    }
  } catch {
    // Dikembalikan ke keadaan sebelum klik. Tombolnya tampak "memantul".
    gambarUlang(sebelum);
    return sebelum;
  }
  const tersimpan = { ...sesudah, sedangMenyimpan: false };
  gambarUlang(tersimpan);
  return tersimpan;
}

export { keadaanSesudahKlik, tekanSuka };
export type { KeadaanSuka, Penggambar };
