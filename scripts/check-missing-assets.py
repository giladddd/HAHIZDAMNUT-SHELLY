#!/usr/bin/env python3
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
missing = []
for p in SITE.glob("personal-*.html"):
    text = p.read_text(encoding="utf-8")
    for m in re.findall(r"WP\+'([^']+)'", text):
        local = SITE / "assets" / "uploads" / "2025" / "04" / m
        if not local.exists():
            missing.append((p.name, m))
for name, f in sorted(set(missing)):
    print(f"{name}\t{f}")
print("total", len(set(missing)))
