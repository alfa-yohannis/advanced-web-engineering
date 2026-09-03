#!/usr/bin/env python3
"""Merekam aktivitas jaringan sebuah halaman tanpa membuka DevTools.

Skrip ini menjalankan Chrome tanpa antarmuka, mengendalikannya lewat Chrome
DevTools Protocol (CDP), lalu menulis hasilnya sebagai berkas HAR. Berkas
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

import websockets

PORT = 9222
DIAM = 2.0  # detik tanpa permintaan baru sebelum perekaman dihentikan
BATAS = 60.0  # batas waktu keseluruhan


def cari_chrome():
    for nama in ("google-chrome", "chromium", "chromium-browser"):
        jalur = shutil.which(nama)
        if jalur:
            return jalur
    sys.exit("Chrome tidak ditemukan.")


def alamat_debug():
    for _ in range(50):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json") as r:
                for target in json.load(r):
                    if target.get("type") == "page":
                        return target["webSocketDebuggerUrl"]
        except Exception:
            time.sleep(0.2)
    sys.exit("Chrome tidak menjawab pada porta debug.")


async def rekam(url, berkas):
    ws_url = alamat_debug()
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

    with open(berkas, "w", encoding="utf-8") as f:
        json.dump({"log": {"version": "1.2", "entries": entri}}, f, indent=1)

    print(f"Tersimpan {len(entri)} permintaan ke {berkas}")


def main():
    if len(sys.argv) < 2:
        sys.exit("Pemakaian: ./rekam-har.py <alamat> [berkas.har]")

    url = sys.argv[1]
    berkas = sys.argv[2] if len(sys.argv) > 2 else "rekaman.har"

    profil = tempfile.mkdtemp(prefix="chrome-rekam-")
    chrome = subprocess.Popen(
        [cari_chrome(), "--headless=new", "--disable-gpu", "--no-sandbox",
         f"--remote-debugging-port={PORT}", f"--user-data-dir={profil}",
         "--window-size=1280,900", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        asyncio.run(rekam(url, berkas))
    finally:
        chrome.terminate()
        chrome.wait(timeout=10)


if __name__ == "__main__":
    main()
