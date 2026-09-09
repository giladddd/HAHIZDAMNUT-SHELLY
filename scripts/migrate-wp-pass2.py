#!/usr/bin/env python3
"""Download remaining WP assets (WP+ concatenation) and fix leftover URLs."""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SITE_DIR / "assets" / "uploads" / "2025" / "04"
MANIFEST_PATH = SITE_DIR / "assets" / "manifest.json"
USER_AGENT = "HAHIZDAMNUT-migration/1.0"

EXTRA_FILES = [
    "הלפאפ.png",  # correct spelling on server (HTML had final feh)
]


def fetch(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.quote(parsed.path, safe="/:")
    req_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
    req = urllib.request.Request(req_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def download_filename(name: str, manifest: dict) -> None:
    base = f"https://hahizdamnut-shelly.com/wp-content/uploads/2025/04/{name}"
    local = ASSETS_DIR / name
    local.parent.mkdir(parents=True, exist_ok=True)
    if local.exists() and local.stat().st_size > 0:
        return
    for attempt in range(3):
        try:
            local.write_bytes(fetch(base))
            manifest[base] = {"local": f"assets/uploads/2025/04/{name}", "bytes": local.stat().st_size}
            print(f"OK {name}")
            return
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == 2:
                print(f"FAIL {name}: {exc}")
            else:
                time.sleep(1)


def collect_wp_plus_files() -> set[str]:
    files: set[str] = set()
    for html_path in SITE_DIR.glob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        files.update(re.findall(r"WP\+'([^']+)'", text))
    return files


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else {}

    names = collect_wp_plus_files() | set(EXTRA_FILES)
    print(f"Downloading {len(names)} extra files...")
    for name in sorted(names):
        download_filename(name, manifest)

    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Fix var WP in personal-* pages
    for html_path in SITE_DIR.glob("personal-*.html"):
        text = html_path.read_text(encoding="utf-8")
        updated = text.replace(
            "var WP = 'https://hahizdamnut-shelly.com/wp-content/uploads/2025/04/';",
            "var WP = 'assets/uploads/2025/04/';",
        )
        if updated != text:
            html_path.write_text(updated, encoding="utf-8")
            print(f"Updated WP base in {html_path.name}")

    # Fix Help Up typo (final feh -> peh) and Workaway fallback
    replacements = [
        (
            "https://hahizdamnut-shelly.com/wp-content/uploads/2025/04/הלפאף.png",
            "assets/uploads/2025/04/הלפאפ.png",
        ),
        (
            "https://hahizdamnut-shelly.com/wp-content/uploads/2025/04/וורקאווי.png",
            "assets/uploads/2025/04/4.png",  # generic fallback; original missing on WP
        ),
    ]
    for html_path in SITE_DIR.glob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        updated = text
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != text:
            html_path.write_text(updated, encoding="utf-8")
            print(f"Fixed URLs in {html_path.name}")


if __name__ == "__main__":
    main()
