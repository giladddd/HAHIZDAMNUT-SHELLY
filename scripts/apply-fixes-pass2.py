#!/usr/bin/env python3
"""Second pass: no-cors, auth bypass, form_type."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

for path in sorted(ROOT.glob("*.html")):
    text = path.read_text(encoding="utf-8")
    orig = text

    text = re.sub(r",?\s*mode:\s*['\"]no-cors['\"]", "", text)

    text = text.replace(
        "if(saved.indexOf(norm)>-1){grantAccess();return;}\n    ",
        "",
    )

    text = text.replace(
        "{name:name,phone:phone,notes:notes,timestamp:new Date().toLocaleString('he-IL')}",
        "{name:name,phone:phone,notes:notes,timestamp:new Date().toLocaleString('he-IL'),form_type:'lead'}",
    )

    if text != orig:
        path.write_text(text, encoding="utf-8")
        print("updated", path.name)
