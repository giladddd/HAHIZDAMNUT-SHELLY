#!/usr/bin/env python3
"""Ensure hahizd-common.js loads before Hahizd.init* calls."""
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
COMMON = '<script src="assets/js/hahizd-common.js"></script>'
BAD = re.compile(
    r"(<script>\s*\n(?:Hahizd\.init[\s\S]*?)\n</script>\s*\n)"
    r'(<script src="assets/js/hahizd-common\.js"></script>)'
)

for html in SITE.glob("*.html"):
    text = html.read_text(encoding="utf-8")
    orig = text
    if html.name == "index.html":
        text = re.sub(r"<script>\s*Hahizd\.initNav\(\);\s*</script>\s*", "", text)
        text = text.replace(COMMON + "\n", "").replace(COMMON, "")
    else:
        text = BAD.sub(COMMON + "\n\\1", text)
        text = text.replace(COMMON + "\n" + COMMON, COMMON)
    if text != orig:
        html.write_text(text, encoding="utf-8")
        print("fixed:", html.name)
