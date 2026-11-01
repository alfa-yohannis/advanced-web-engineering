"""WebSocket seadanya: jabat tangan dan frame teks, memakai pustaka standar.

Modul ini dipakai dua pihak sekaligus, yaitu server di websocket.py dan alat
ukur di ukur-transport.py. Isinya hanya bagian protokol yang diperlukan bab
ini: jabat tangan HTTP, satu jenis frame, dan penutupan sambungan.

Nama file-nya sengaja bukan websocket.py, karena nama itu dipakai pustaka
pihak ketiga yang lazim dipasang, dan tabrakan nama akan membingungkan.

Modul ini diimpor, bukan dijalankan langsung:
    python3 websocket.py
"""

import base64
import hashlib
import os
import struct

# Nilai tetap dari RFC 6455, dipakai menghitung jawaban jabat tangan.
KUNCI_AJAIB = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
OPCODE_TEKS = 0x1
OPCODE_TUTUP = 0x8
BIT_FRAME_AKHIR = 0x80
BIT_MASK = 0x80
PANJANG_DUA_BYTE = 126
PANJANG_DELAPAN_BYTE = 127
BATAS_PANJANG_PENDEK = 125
BATAS_PANJANG_SEDANG = 65535
PANJANG_MASK = 4


def jawaban_jabat_tangan(kunci_klien):
  """Menghitung nilai Sec-WebSocket-Accept dari kunci yang dikirim klien.

  Nilainya bukan rahasia dan bukan tanda tangan keamanan. Gunanya memastikan
  yang menjawab benar-benar paham WebSocket, bukan server HTTP biasa yang
  kebetulan menjawab 101.
  """
  ringkasan = hashlib.sha1((kunci_klien + KUNCI_AJAIB).encode()).digest()
  return base64.b64encode(ringkasan).decode()


def susun_frame(teks, pakai_mask):
  """Menyusun satu frame teks WebSocket menjadi byte yang siap dikirim.

  Frame dari klien wajib di-mask menurut RFC 6455, sedangkan frame dari
  server wajib tidak di-mask. Karena itu pemanggil yang menentukan.
  """
  isi = teks.encode()
  bingkai = bytearray([BIT_FRAME_AKHIR | OPCODE_TEKS])
  bit_mask = BIT_MASK if pakai_mask else 0
  if len(isi) <= BATAS_PANJANG_PENDEK:
    bingkai.append(bit_mask | len(isi))
  elif len(isi) <= BATAS_PANJANG_SEDANG:
    bingkai.append(bit_mask | PANJANG_DUA_BYTE)
    bingkai.extend(struct.pack(">H", len(isi)))
  else:
    bingkai.append(bit_mask | PANJANG_DELAPAN_BYTE)
    bingkai.extend(struct.pack(">Q", len(isi)))
  if not pakai_mask:
    return bytes(bingkai + isi)
  kunci_mask = os.urandom(PANJANG_MASK)
  bingkai.extend(kunci_mask)
  bingkai.extend(byte ^ kunci_mask[nomor % PANJANG_MASK]
                 for nomor, byte in enumerate(isi))
  return bytes(bingkai)


def baca_tepat(soket, jumlah):
  """Membaca sejumlah byte dari soket, atau None bila soketnya tertutup."""
  data = bytearray()
  while len(data) < jumlah:
    potongan = soket.recv(jumlah - len(data))
    if not potongan:
      return None
    data.extend(potongan)
  return bytes(data)


def baca_panjang(soket, penanda):
  """Membaca panjang isi frame, yang bentuknya tiga kemungkinan."""
  panjang = penanda & 0x7F
  if panjang == PANJANG_DUA_BYTE:
    return struct.unpack(">H", baca_tepat(soket, 2))[0]
  if panjang == PANJANG_DELAPAN_BYTE:
    return struct.unpack(">Q", baca_tepat(soket, 8))[0]
  return panjang


def baca_frame(soket):
  """Membaca satu frame teks, lalu mengembalikan (teks, byte_terpakai).

  Byte yang terpakai ikut dikembalikan, karena bab ini membandingkan biaya
  tiap transport dalam byte, dan header frame WebSocket termasuk biaya itu.
  Mengembalikan (None, 0) bila sambungannya ditutup.
  """
  kepala = baca_tepat(soket, 2)
  if not kepala:
    return None, 0
  if kepala[0] & 0x0F == OPCODE_TUTUP:
    return None, 2
  panjang = baca_panjang(soket, kepala[1])
  tambahan = 2 + (2 if (kepala[1] & 0x7F) == PANJANG_DUA_BYTE else 0)
  kunci_mask = b""
  if kepala[1] & BIT_MASK:
    kunci_mask = baca_tepat(soket, PANJANG_MASK)
    tambahan += PANJANG_MASK
  isi = baca_tepat(soket, panjang) or b""
  if kunci_mask:
    isi = bytes(byte ^ kunci_mask[nomor % PANJANG_MASK]
                for nomor, byte in enumerate(isi))
  return isi.decode(), tambahan + len(isi)
