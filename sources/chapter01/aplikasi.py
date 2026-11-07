"""Kerangka API minimal Bab 1 di port 8050: route, service, dan repository.

File ini hanya menyusun ketiga lapisan lalu menyalakan server. Route ada di
rute.py, aturan bisnis di layanan.py, dan penyimpanan di repositori.py.
Kerangka ini menjadi sistem yang diukur pada bab-bab berikutnya.

Pemakaian (dari sources/chapter01):
    python3 aplikasi.py
    curl -s http://127.0.0.1:8050/buku
"""

from http.server import ThreadingHTTPServer

from layanan import LayananKatalog
from repositori import RepositoriBukuSqlite
from rute import PenanganKatalog

HOST = "127.0.0.1"
PORT = 8050


class ServerKatalog(ThreadingHTTPServer):
  """Server HTTP yang membawa satu service katalog untuk seluruh route-nya."""

  def __init__(self, alamat, layanan):
    """Menyimpan service, agar tiap penangan permintaan memakai yang sama."""
    super().__init__(alamat, PenanganKatalog)
    self.layanan = layanan


def buat_server(port=PORT, repositori=None):
  """Menyusun repository, service, dan route menjadi satu server.

  Port 0 meminta sistem operasi memilih port yang kosong, dan itulah yang
  dipakai uji API agar tidak berebut port dengan aplikasi yang menyala.
  """
  layanan = LayananKatalog(repositori or RepositoriBukuSqlite())
  return ServerKatalog((HOST, port), layanan)


def main():
  """Menyalakan API sampai dihentikan dengan Ctrl+C."""
  server = buat_server()
  print(f"Katalog di http://{HOST}:{PORT}/buku  (Ctrl+C untuk berhenti)",
        flush=True)
  server.serve_forever()


if __name__ == "__main__":
  main()
