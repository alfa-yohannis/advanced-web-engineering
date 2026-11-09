#!/usr/bin/env python3
"""Merekam aktivitas jaringan sebuah halaman tanpa membuka DevTools.

Skrip ini menjalankan Chrome tanpa antarmuka, mengendalikannya lewat Chrome
DevTools Protocol (CDP), lalu menulis hasilnya sebagai file HAR. File
tersebut dapat langsung diringkas dengan ringkas-har.py, sehingga seluruh
rangkaian pengukuran berjalan tanpa langkah manual.

Pemakaian:
    ./rekam-har.py https://www.pradita.ac.id/ rekaman.har

Prasyarat: google-chrome terpasang, dan pustaka websockets tersedia.
"""

import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import websockets

# Port 0 meminta Chrome memilih sendiri port debug yang kosong. Port tetap
# seperti 9222 sering sudah dipakai Chrome lain di komputer yang sama, dan
# skrip lalu tersambung ke browser yang salah.
PORT_DEBUG_PILIHAN_CHROME = 0
# Chrome menulis port pilihannya di baris pertama file ini, di profilnya.
NAMA_FILE_PORT_DEBUG = "DevToolsActivePort"
JUMLAH_PERCOBAAN_DEBUG = 50
JEDA_PERCOBAAN_DETIK = 0.2
DIAM = 2.0  # detik tanpa permintaan baru sebelum perekaman dihentikan
BATAS = 60.0  # batas waktu keseluruhan


def cari_chrome():
  for nama in ("google-chrome", "chromium", "chromium-browser"):
    jalur = shutil.which(nama)
    if jalur:
      return jalur
  sys.exit("Chrome tidak ditemukan.")


def baca_port_debug(direktori_profil):
  """Membaca port debug yang dipilih Chrome, atau None bila belum siap.

  File itu berada di profil milik skrip ini, sehingga port yang terbaca
  pasti milik Chrome yang baru dijalankan, bukan Chrome lain yang kebetulan
  sedang terbuka.
  """
  file_port = Path(direktori_profil) / NAMA_FILE_PORT_DEBUG
  try:
    baris_pertama = file_port.read_text(encoding="utf-8").splitlines()[0]
  except (OSError, IndexError):
    return None
  return int(baris_pertama) if baris_pertama.isdigit() else None


def alamat_debug(direktori_profil):
  """Menunggu Chrome siap, lalu mengembalikan alamat WebSocket tab-nya.

  Selama port belum tertulis atau tab belum terdaftar, pemeriksaan diulang
  sebentar lagi. Bila Chrome tetap tidak menjawab, skrip berhenti dengan
  pesan, bukan menunggu selamanya.
  """
  for _ in range(JUMLAH_PERCOBAAN_DEBUG):
    port_debug = baca_port_debug(direktori_profil)
    if port_debug:
      alamat_daftar_tab = f"http://127.0.0.1:{port_debug}/json"
      try:
        with urllib.request.urlopen(alamat_daftar_tab) as response:
          for target in json.load(response):
            if target.get("type") == "page":
              return target["webSocketDebuggerUrl"]
      except (OSError, ValueError):
        pass
    time.sleep(JEDA_PERCOBAAN_DETIK)
  sys.exit("Chrome tidak menjawab pada port debug.")


async def rekam(url, file_har, direktori_profil):
  """Membuka satu alamat di Chrome milik skrip ini, lalu menulis file HAR.

  Direktori profil dikirim agar alamat debug dibaca dari Chrome yang
  dijalankan main(), bukan ditebak dari nomor port yang tetap.
  """
  ws_url = alamat_debug(direktori_profil)
  permintaan, respons, selesai = {}, {}, {}
  pesan_ke = 0

  async with websockets.connect(ws_url, max_size=None) as ws:

    async def kirim(metode, params=None):
      nonlocal pesan_ke
      pesan_ke += 1
      await ws.send(json.dumps({"id": pesan_ke, "method": metode,
                                "params": params or {}}))

    await kirim("Network.enable")
    await kirim("Network.setCacheDisabled", {"cacheDisabled": True})
    await kirim("Page.enable")
    await kirim("Page.navigate", {"url": url})

    mulai = time.time()
    terakhir = time.time()
    while time.time() - mulai < BATAS and time.time() - terakhir < DIAM:
      try:
        pesan = json.loads(await asyncio.wait_for(ws.recv(), timeout=DIAM))
      except asyncio.TimeoutError:
        break

      metode = pesan.get("method")
      p = pesan.get("params", {})

      if metode == "Network.requestWillBeSent":
        permintaan[p["requestId"]] = {
            "url": p["request"]["url"],
            "wallTime": p.get("wallTime", time.time()),
            "timestamp": p["timestamp"],
        }
        terakhir = time.time()
      elif metode == "Network.responseReceived":
        r = p["response"]
        respons[p["requestId"]] = {
            "protocol": r.get("protocol", "?"),
            "connectionId": r.get("connectionId", 0),
            "fromCache": r.get("fromDiskCache", False),
        }
        terakhir = time.time()
      elif metode == "Network.loadingFinished":
        selesai[p["requestId"]] = {
            "timestamp": p["timestamp"],
            "encodedDataLength": p.get("encodedDataLength", 0),
        }
        terakhir = time.time()

  entri = []
  for rid, req in permintaan.items():
    res = respons.get(rid)
    fin = selesai.get(rid)
    if not res or not fin:
      continue
    mulai_iso = datetime.fromtimestamp(req["wallTime"], timezone.utc).isoformat()
    entri.append({
        "startedDateTime": mulai_iso,
        "time": (fin["timestamp"] - req["timestamp"]) * 1000,
        "connection": "" if res["fromCache"] else str(res["connectionId"]),
        "request": {"url": req["url"]},
        "response": {
            "httpVersion": res["protocol"],
            "_transferSize": 0 if res["fromCache"] else fin["encodedDataLength"],
        },
    })

  with open(file_har, "w", encoding="utf-8") as f:
    json.dump({"log": {"version": "1.2", "entries": entri}}, f, indent=1)

  print(f"Tersimpan {len(entri)} permintaan ke {file_har}")


def main():
  """Menjalankan Chrome tanpa antarmuka dengan profil sendiri, lalu merekam.

  Profil baru membuat Chrome ini terpisah dari Chrome pengguna, termasuk
  dari cache dan port debug-nya.
  """
  if len(sys.argv) < 2:
    sys.exit("Pemakaian: ./rekam-har.py <alamat> [file.har]")

  url = sys.argv[1]
  file_har = sys.argv[2] if len(sys.argv) > 2 else "rekaman.har"

  # Profil sementara dihapus begitu Chrome berhenti. Tanpa itu, tiap rekaman
  # meninggalkan sekitar 39 MB di /tmp.
  with tempfile.TemporaryDirectory(prefix="chrome-rekam-",
                                   ignore_cleanup_errors=True) as profil:
    chrome = subprocess.Popen(
        [cari_chrome(), "--headless=new", "--disable-gpu", "--no-sandbox",
         f"--remote-debugging-port={PORT_DEBUG_PILIHAN_CHROME}",
         f"--user-data-dir={profil}", "--window-size=1280,900",
         "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
      asyncio.run(rekam(url, file_har, profil))
    finally:
      chrome.terminate()
      chrome.wait(timeout=10)


if __name__ == "__main__":
  main()
