#!/usr/bin/env python3
"""Download wp-content assets and rewrite HTML to local assets/ paths."""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
ASSETS_ROOT = SITE_DIR / "assets" / "uploads"
MANIFEST_PATH = SITE_DIR / "assets" / "manifest.json"

WP_URL_RE = re.compile(
    r"https://hahizdamnut-shelly\.com/wp-content/uploads/[^\s\"'<>]+"
)
JOB_URL_RE = re.compile(
    r"https://hahizdamnut-shelly\.com/job/[^\s\"'<>]+"
)
WP_PAGE_RE = re.compile(
    r"https://hahizdamnut-shelly\.com/[^\s\"'<>]+"
)

USER_AGENT = "HAHIZDAMNUT-migration/1.0"


def normalize_wp_url(url: str) -> str:
    """Canonical form: decoded path, no trailing junk."""
    url = url.rstrip("),.;'\"")
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.unquote(parsed.path)
    return urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, path, "", "", "")
    )


def wp_url_to_local_rel(url: str) -> str:
    """Map WP upload URL -> assets/uploads/... relative path."""
    parsed = urllib.parse.urlparse(normalize_wp_url(url))
    prefix = "/wp-content/uploads/"
    if prefix not in parsed.path:
        raise ValueError(f"Not an uploads URL: {url}")
    rel = parsed.path.split(prefix, 1)[1].lstrip("/")
    return f"assets/uploads/{rel.replace(chr(92), '/')}"


def fetch_url(url: str) -> bytes:
    parsed = urllib.parse.urlparse(normalize_wp_url(url))
    # Re-encode path for HTTP request (Hebrew filenames)
    path = urllib.parse.quote(parsed.path, safe="/:")
    req_url = urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, path, "", "", "")
    )
    req = urllib.request.Request(req_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def download_asset(url: str, manifest: dict) -> str:
    canonical = normalize_wp_url(url)
    if canonical in manifest:
        return manifest[canonical]["local"]

    local_rel = wp_url_to_local_rel(canonical)
    local_path = SITE_DIR / local_rel.replace("/", os.sep)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if not local_path.exists() or local_path.stat().st_size == 0:
        for attempt in range(3):
            try:
                data = fetch_url(canonical)
                local_path.write_bytes(data)
                break
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 2:
                    raise RuntimeError(f"Failed to download {canonical}: {exc}") from exc
                time.sleep(1.5 * (attempt + 1))

    manifest[canonical] = {
        "local": local_rel.replace("\\", "/"),
        "bytes": local_path.stat().st_size,
    }
    return manifest[canonical]["local"]


def collect_wp_urls() -> list[str]:
    urls: set[str] = set()
    for html_path in sorted(SITE_DIR.glob("*.html")):
        text = html_path.read_text(encoding="utf-8")
        for match in WP_URL_RE.findall(text):
            urls.add(normalize_wp_url(match))
    return sorted(urls)


def rewrite_html(manifest: dict) -> dict:
    stats = {"files": 0, "replacements": 0, "jobs": 0, "wp_pages": 0}

    # Build replace map: every raw substring found in files -> local path
    url_map: dict[str, str] = {}
    for canonical, info in manifest.items():
        local = info["local"]
        url_map[canonical] = local
        # Also map encoded variant
        parsed = urllib.parse.urlparse(canonical)
        encoded_path = urllib.parse.quote(parsed.path, safe="/:")
        encoded_url = urllib.parse.urlunparse(
            (parsed.scheme, parsed.netloc, encoded_path, "", "", "")
        )
        url_map[encoded_url] = local
        # Partial encoded (as stored in some HTML files)
        url_map[canonical.replace(
            urllib.parse.unquote(parsed.path), parsed.path
        )] = local

    for html_path in sorted(SITE_DIR.glob("*.html")):
        original = html_path.read_text(encoding="utf-8")
        updated = original
        file_replacements = 0

        # Replace wp-content URLs longest-first to avoid partial overlaps
        found_urls = sorted(
            set(WP_URL_RE.findall(updated)),
            key=len,
            reverse=True,
        )
        for raw in found_urls:
            canonical = normalize_wp_url(raw)
            if canonical not in manifest:
                continue
            local = manifest[canonical]["local"]
            if raw in updated:
                count = updated.count(raw)
                updated = updated.replace(raw, local)
                file_replacements += count

        # Job pages -> pre-meeting intake
        job_matches = JOB_URL_RE.findall(updated)
        for raw in job_matches:
            count = updated.count(raw)
            updated = updated.replace(raw, "pre-meeting.html")
            file_replacements += count
            stats["jobs"] += count

        # Other WP pages on same domain (not wp-content, not canonical/og)
        for raw in WP_PAGE_RE.findall(updated):
            if "/wp-content/" in raw or raw.endswith(".html"):
                continue
            if "hahizdamnut-shelly.com/job/" in raw:
                continue
            # e.g. /מסע-אל-האופק/ — send to programs section
            replacement = "personal.html#programs"
            if raw in updated:
                count = updated.count(raw)
                updated = updated.replace(raw, replacement)
                file_replacements += count
                stats["wp_pages"] += count

        if updated != original:
            html_path.write_text(updated, encoding="utf-8")
            stats["files"] += 1
            stats["replacements"] += file_replacements
            print(f"  updated {html_path.name} ({file_replacements} replacements)")

    return stats


def main() -> int:
    print(f"Site dir: {SITE_DIR}")
    urls = collect_wp_urls()
    print(f"Found {len(urls)} unique wp-content URLs")

    manifest: dict = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    ASSETS_ROOT.mkdir(parents=True, exist_ok=True)

    failed: list[str] = []
    for i, url in enumerate(urls, 1):
        try:
            local = download_asset(url, manifest)
            print(f"[{i}/{len(urls)}] OK -> {local}")
        except Exception as exc:  # noqa: BLE001
            print(f"[{i}/{len(urls)}] FAIL {url}: {exc}")
            failed.append(url)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\nRewriting HTML...")
    stats = rewrite_html(manifest)
    print(
        f"\nDone. Downloaded/found {len(manifest)} assets, "
        f"{len(failed)} failures, "
        f"HTML: {stats['files']} files, {stats['replacements']} replacements, "
        f"{stats['jobs']} job links -> pre-meeting.html"
    )
    if failed:
        fail_log = SITE_DIR / "assets" / "download-failures.json"
        fail_log.write_text(
            json.dumps(failed, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Failures logged to {fail_log}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
