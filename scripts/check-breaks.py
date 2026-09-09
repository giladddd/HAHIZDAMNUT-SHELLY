#!/usr/bin/env python3
"""Quick audit: where assets/links break."""
import re
import pathlib
import urllib.request
import urllib.error
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
html_files = sorted(ROOT.glob("*.html"))

local_missing = []
wp_by_file = defaultdict(list)
wp_unique = set()
dead_hash = []
tracks_links = []
open_reg_stub = []
href_hash_only = []

for fp in html_files:
    text = fp.read_text(encoding="utf-8", errors="ignore")
    if "openRegModal=function(){}" in text.replace(" ", "") or "openRegModal = function(){}" in text:
        open_reg_stub.append(fp.name)
    for i, line in enumerate(text.splitlines(), 1):
        if "#tracks" in line and "href" in line:
            tracks_links.append(f"{fp.name}:{i}")
        if re.search(r'href=["\']#["\']', line):
            href_hash_only.append(f"{fp.name}:{i}")
    for m in re.finditer(r'(?:src|href|poster)=["\']([^"\']+)["\']', text):
        u = m.group(1)
        if u.startswith("images/") or u.startswith("./images/"):
            p = ROOT / u.replace("./", "")
            if not p.exists():
                local_missing.append((fp.name, u))
        if "wp-content" in u and u.startswith("http"):
            wp_by_file[fp.name].append(u.split("?")[0])
            wp_unique.add(u.split("?")[0])

print("=== BROKEN / RISKY LOCATIONS ===\n")
print(f"1) #tracks links (no id=tracks on homepage): {len(tracks_links)}")
for x in tracks_links:
    print(f"   {x}")

has_tracks = "id=\"tracks\"" in (ROOT / "hahazdamnut.html").read_text(encoding="utf-8")
has_programs = "id=\"programs\"" in (ROOT / "hahazdamnut.html").read_text(encoding="utf-8")
print(f"   homepage has id=tracks? {has_tracks} | id=programs? {has_programs}\n")

print(f"2) openRegModal stub (button does nothing): {len(open_reg_stub)} files")
for x in open_reg_stub:
    print(f"   {x}\n")

print(f"3) href='#' dead links: {len(href_hash_only)}")
for x in href_hash_only[:12]:
    print(f"   {x}")
if len(href_hash_only) > 12:
    print(f"   ... +{len(href_hash_only)-12} more\n")

print(f"4) missing local images: {len(local_missing)}")
for x in local_missing:
    print(f"   {x[0]} -> {x[1]}")
print()

print("5) WordPress dependency per file:")
for name in sorted(wp_by_file, key=lambda k: -len(wp_by_file[k])):
    print(f"   {name}: {len(wp_by_file[name])} wp refs")
print(f"   TOTAL unique wp URLs: {len(wp_unique)}\n")

print("6) Sampling wp-content URLs (HEAD request)...")
broken = []
ok = 0
for u in sorted(wp_unique):
    try:
        req = urllib.request.Request(u, method="HEAD")
        urllib.request.urlopen(req, timeout=12)
        ok += 1
    except Exception as e:
        broken.append((u, str(e)[:80]))
print(f"   OK: {ok} | BROKEN: {len(broken)}")
for u, err in broken[:15]:
    print(f"   BROKEN: {u[:90]}")
    print(f"           {err}")
if len(broken) > 15:
    print(f"   ... +{len(broken)-15} more broken")
