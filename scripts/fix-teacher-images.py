#!/usr/bin/env python3
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "assets" / "uploads" / "2025" / "04"
FALLBACK = ROOT / "8.png"

SOURCES = {
    "רוברט-גריייני.jpg": [
        "https://upload.wikimedia.org/wikipedia/commons/4/4a/Robert_Greene_%28author%29.jpg",
        "https://i.ytimg.com/vi/4A4sSng7K6M/hqdefault.jpg",
    ],
    "גיים-רואהן.jpg": [
        "https://upload.wikimedia.org/wikipedia/en/9/9e/Jim_Rohn.jpg",
        "https://i.ytimg.com/vi/6hXS5QP6xYk/hqdefault.jpg",
    ],
    "רוברט-קווסקי.jpg": [
        "https://upload.wikimedia.org/wikipedia/commons/4/4a/Robert_Kiyosaki_by_Gage_Skidmore.jpg",
        "https://i.ytimg.com/vi/your/hqdefault.jpg",
    ],
}

def save(name: str, urls: list[str]) -> None:
    dest = ROOT / name
    if dest.exists() and dest.stat().st_size > 0:
        print("exists", name)
        return
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=20).read()
            if len(data) > 1000:
                dest.write_bytes(data)
                print("ok", name, url[:60], len(data))
                return
        except Exception as exc:
            print("fail", name, url[:60], exc)
    dest.write_bytes(FALLBACK.read_bytes())
    print("fallback", name)

for fname, urls in SOURCES.items():
    save(fname, urls)
