#!/usr/bin/env python3
"""Post-migration verification: no WP asset URLs, local files exist."""
from __future__ import annotations

import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
WP_SITE_RE = re.compile(r"https://hahizdamnut-shelly\.com/wp-content")
WP_PLUS_RE = re.compile(r"https://hahizdamnut-shelly\.com/wp-content/uploads/2025/04/")
ASSET_RE = re.compile(r"""assets/uploads/[^\s"'<>]+""")


def main() -> int:
    errors: list[str] = []

    for html in sorted(SITE.glob("*.html")):
        text = html.read_text(encoding="utf-8")
        if WP_SITE_RE.search(text):
            errors.append(f"{html.name}: still references hahizdamnut-shelly.com/wp-content")
        if "var WP = 'https://" in text:
            errors.append(f"{html.name}: WP var still points to remote URL")

    for html in sorted(SITE.glob("*.html")):
        text = html.read_text(encoding="utf-8")
        for rel in set(ASSET_RE.findall(text)):
            rel = rel.rstrip("),.;'\"")
            path = SITE / rel.replace("/", "\\")
            if not path.exists():
                errors.append(f"missing file: {rel} (from {html.name})")

    job_left = sum(
        1
        for html in SITE.glob("*.html")
        for _ in re.finditer(r"hahizdamnut-shelly\.com/job/", html.read_text(encoding="utf-8"))
    )
    if job_left:
        errors.append(f"{job_left} job links still point to WordPress")

    asset_count = sum(1 for _ in (SITE / "assets").rglob("*") if _.is_file())

    print(f"Assets on disk: {asset_count}")
    if errors:
        print("FAILURES:")
        for e in errors:
            print(" -", e)
        return 1
    print("OK: zero WP asset dependencies, all referenced assets exist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
