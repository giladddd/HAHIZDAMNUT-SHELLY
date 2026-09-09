#!/usr/bin/env python3
"""Replace duplicated inline JS with shared hahizd-common.js across HTML pages."""
from __future__ import annotations

import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent

COMMON_SCRIPT = '<script src="assets/js/hahizd-common.js"></script>'

AUTH_BLOCK_RE = re.compile(
    r"<script>\s*\(function\(\)\{\s*var SHEETS_URL=[^;]+;.*?sessionStorage\.setItem\('hahizd_auth'[^}]+\}\);\s*\}\);\s*\}\);\s*\}\)\(\);\s*</script>",
    re.DOTALL,
)

# Simpler auth block matcher - from (function(){ var SHEETS_URL to })(); before nav
AUTH_BLOCK_RE2 = re.compile(
    r"<script>\s*\(function\(\)\{\s*\n?\s*var SHEETS_URL='https://script\.google\.com/macros/s/[^']+';\s*"
    r"if\(sessionStorage\.getItem\('hahizd_auth'\)[\s\S]*?\}\)\(\);\s*</script>",
    re.MULTILINE,
)

HAMBURGER_RE = re.compile(
    r"<script>\s*\n?// Hamburger menu\s*\nvar hamburger[\s\S]*?"
    r"window\.addEventListener\('scroll'[\s\S]*?\}\);\s*\n?</script>",
    re.MULTILINE,
)

HAMBURGER_RE2 = re.compile(
    r"<script>\s*\nvar hamburger\s*=\s*document\.getElementById\('navHamburger'\);[\s\S]*?"
    r"window\.addEventListener\('scroll'[\s\S]*?\}\);\s*\n?</script>",
    re.MULTILINE,
)

REG_MODAL_RE = re.compile(
    r"<script>\s*\(function\(\)\{\s*\n?\s*var (?:SHEETS_URL|SU)='https://script\.google\.com/macros/s/[^']+';\s*"
    r"window\.openRegModal[\s\S]*?\}\)\(\);\s*</script>",
    re.MULTILINE,
)

REG_MODAL_INLINE_RE = re.compile(
    r"// ── REG MODAL ──\s*\nvar SHEETS_URL='https://script\.google\.com/macros/s/[^']+';\s*"
    r"window\.openRegModal[\s\S]*?alert\('שגיאה בשליחה[\s\S]*?\};\s*",
    re.MULTILINE,
)

SHEETS_URL_LINE = re.compile(
    r"var SHEETS_URL\s*=\s*'https://script\.google\.com/macros/s/[^']+';\s*\n?",
)

CONTACT_FORM_BLOCK_RE = re.compile(
    r"/\* =+\s*\n\s*CONTACT FORM\s*\n=+\s*\*/\s*\n"
    r"var SHEETS_URL[\s\S]*?"
    r"function showSuccess\(\)\{\s*\n?\s*document\.getElementById\('cfContent'\)[\s\S]*?\}\s*\n",
    re.MULTILINE,
)

PRE_MEETING_FETCH_RE = re.compile(
    r"var params = new URLSearchParams\(\{[\s\S]*?form_type: 'pre_meeting_questionnaire'\s*\}\);\s*\n\s*"
    r"fetch\(SHEETS_URL \+ '\?' \+ params\.toString\(\), \{method:'GET'\}\)",
    re.MULTILINE,
)

HP_FIELD = (
    '<input type="text" name="_hp" tabindex="-1" autocomplete="off" '
    'aria-hidden="true" style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;'
    'overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;opacity:0;pointer-events:none">'
)

PROTECTED_PAGES = {
    "employment.html",
    "finance.html",
    "personal.html",
    "personal-books.html",
    "personal-movies.html",
    "personal-meditation.html",
    "personal-podcasts.html",
    "personal-teachers.html",
}

REG_MODAL_PAGES = {
    "employment.html",
    "finance.html",
    "personal.html",
    "discharge-guide.html",
    "hahazdamnut.html",
}

NAV_ONLY_PAGES = {
    "about.html",
    "app.html",
    "partners.html",
    "404.html",
}


def ensure_common_script(text: str) -> str:
    if "assets/js/hahizd-common.js" in text:
        return text
    # Insert before first inline script at end of body, or before </body>
    if "</body>" in text:
        return text.replace("</body>", COMMON_SCRIPT + "\n</body>", 1)
    return text + "\n" + COMMON_SCRIPT


def add_honeypot_to_auth_reg(text: str) -> str:
    marker = '<textarea id="regNotes"'
    if marker in text and 'name="_hp"' not in text.split(marker)[0][-500:]:
        text = text.replace(
            marker,
            HP_FIELD + "\n      " + marker,
            1,
        )
    return text


def add_honeypot_to_contact_form(text: str) -> str:
    marker = '<form id="contactForm"'
    if marker in text and 'contactForm' in text:
        idx = text.find(marker)
        end = text.find(">", idx)
        if end != -1 and 'name="_hp"' not in text[idx : end + 200]:
            text = text[: end + 1] + "\n          " + HP_FIELD + text[end + 1 :]
    return text


def add_honeypot_to_reg_modal(text: str) -> str:
    for form_id in ("rmForm", "regForm"):
        marker = f'<div id="{form_id}">'
        if marker in text:
            idx = text.find(marker)
            chunk = text[idx : idx + 400]
            if 'name="_hp"' not in chunk:
                insert_after = text.find("<input", idx)
                if insert_after != -1:
                    text = text[:insert_after] + HP_FIELD + "\n      " + text[insert_after:]
    return text


def add_honeypot_to_pre_meeting(text: str) -> str:
    marker = '<form id="surveyForm"'
    if marker in text and 'name="_hp"' not in text:
        idx = text.find(marker)
        insert = text.find("<div class=\"field\">", idx)
        if insert != -1:
            text = text[:insert] + "      " + HP_FIELD + "\n\n      " + text[insert:]
    return text


def strip_duplicate_blocks(text: str) -> str:
    text = AUTH_BLOCK_RE2.sub("", text)
    text = HAMBURGER_RE.sub("", text)
    text = HAMBURGER_RE2.sub("", text)
    text = REG_MODAL_RE.sub("", text)
    text = REG_MODAL_INLINE_RE.sub("", text)
    text = CONTACT_FORM_BLOCK_RE.sub("", text)
    text = SHEETS_URL_LINE.sub("", text)
    return text


def build_init_block(filename: str) -> str:
    lines = ["<script>", "Hahizd.initNav();"]

    if filename in PROTECTED_PAGES:
        lines.append("Hahizd.initProtectedAuth();")

    if filename == "hahazdamnut.html":
        lines.append("Hahizd.initContactForm('contactForm');")
        lines.append("Hahizd.initRegModal({ formId: 'regForm', successId: 'regSuccess' });")
    elif filename in REG_MODAL_PAGES:
        lines.append("Hahizd.initRegModal();")

    if filename == "pre-meeting.html":
        lines.append("// pre-meeting form handled below")

    lines.append("</script>")
    return "\n".join(lines)


def fix_pre_meeting(text: str) -> str:
    replacement = """var payload = {
    name: name,
    phone: phone,
    source: document.getElementById('fSource').value,
    expect: document.getElementById('fExpect').value,
    career_score: document.getElementById('sCareer').value,
    finance_score: document.getElementById('sFinance').value,
    personal_score: document.getElementById('sPersonal').value,
    timestamp: new Date().toLocaleString('he-IL'),
    form_type: 'pre_meeting_questionnaire',
    _hp: (document.querySelector('#surveyForm [name="_hp"]') || {}).value || ''
  };
  Hahizd.submit(payload)"""
    text = PRE_MEETING_FETCH_RE.sub(replacement, text)
    return text


def fix_hahazdamnut_nav_script(text: str) -> str:
    """Keep page-specific nav (intersection observer, accordion), remove hamburger duplicate."""
    # Remove hamburger section inside big IIFE but keep rest
    old = """// Hamburger
var hamburger = document.getElementById('navHamburger');
var drawer = document.getElementById('navDrawer');
var overlay = document.getElementById('navOverlay');
var drawerOpen = false;
function openDrawer(){ drawerOpen=true; hamburger.classList.add('open'); drawer.classList.add('open'); overlay.classList.add('open'); document.body.style.overflow='hidden'; }
function closeDrawer(){ drawerOpen=false; hamburger.classList.remove('open'); drawer.classList.remove('open'); overlay.classList.remove('open'); document.body.style.overflow=''; }
hamburger.addEventListener('click', function(){ drawerOpen ? closeDrawer() : openDrawer(); });
overlay.addEventListener('click', closeDrawer);
document.querySelectorAll('.drawer-link, .nav-drawer .btn').forEach(function(l){ l.addEventListener('click', closeDrawer); });


"""
    if old in text:
        text = text.replace(old, "")
    return text


def fix_discharge_guide_nav(text: str) -> str:
    old = """// ── NAV ──
var hamburger=document.getElementById('navHamburger'),drawer=document.getElementById('navDrawer'),overlay=document.getElementById('navOverlay'),drawerOpen=false;
function openDrawer(){drawerOpen=true;hamburger.classList.add('open');drawer.classList.add('open');overlay.classList.add('open');document.body.style.overflow='hidden';}
function closeDrawer(){drawerOpen=false;hamburger.classList.remove('open');drawer.classList.remove('open');overlay.classList.remove('open');document.body.style.overflow='';}
hamburger.addEventListener('click',function(){drawerOpen?closeDrawer():openDrawer();});
overlay.addEventListener('click',closeDrawer);
window.addEventListener('scroll',function(){document.getElementById('navbar').classList.toggle('scrolled',window.scrollY>10);});

"""
    if old in text:
        text = text.replace(old, "")
    return text


def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = original

    text = add_honeypot_to_auth_reg(text)
    text = add_honeypot_to_contact_form(text)
    text = add_honeypot_to_reg_modal(text)
    if path.name == "pre-meeting.html":
        text = add_honeypot_to_pre_meeting(text)

    text = strip_duplicate_blocks(text)

    if path.name == "hahazdamnut.html":
        text = fix_hahazdamnut_nav_script(text)
    if path.name == "discharge-guide.html":
        text = fix_discharge_guide_nav(text)
    if path.name == "pre-meeting.html":
        text = fix_pre_meeting(text)

    init = build_init_block(path.name)
    if path.name == "index.html":
        # Redirect page — no shared JS needed
        text = re.sub(r"<script>\s*Hahizd\.initNav\(\);\s*</script>\s*", "", text)
        text = text.replace(COMMON_SCRIPT + "\n", "").replace(COMMON_SCRIPT, "")
    elif "Hahizd.initNav()" not in text:
        if "</body>" in text:
            text = text.replace(
                "</body>", COMMON_SCRIPT + "\n" + init + "\n</body>", 1
            )
        else:
            text += "\n" + COMMON_SCRIPT + "\n" + init
    elif "assets/js/hahizd-common.js" not in text:
        text = ensure_common_script(text)

    # Fix script order: common.js must load before init calls
    text = re.sub(
        r"(<script>\s*\n?Hahizd\.init[\s\S]*?</script>\s*\n?"
        r'<script src="assets/js/hahizd-common\.js"></script>)',
        COMMON_SCRIPT + r"\n\1".replace(COMMON_SCRIPT + r"\n<script>", "<script>", 1),
        text,
        count=1,
    )
    # Cleaner fix: swap if init block precedes common script
    bad_order = re.compile(
        r"(<script>\s*\n(?:Hahizd\.init[\s\S]*?)\n</script>\s*\n)"
        r'(<script src="assets/js/hahizd-common\.js"></script>)',
        re.MULTILINE,
    )
    text = bad_order.sub(COMMON_SCRIPT + "\n\\1", text)
    text = text.replace(
        COMMON_SCRIPT + "\n" + COMMON_SCRIPT,
        COMMON_SCRIPT,
    )

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    changed = []
    for html in sorted(SITE.glob("*.html")):
        if process_file(html):
            changed.append(html.name)
            print(f"updated: {html.name}")

    # Grep-style checks
    errors = []
    for html in sorted(SITE.glob("*.html")):
        text = html.read_text(encoding="utf-8")
        if "var SHEETS_URL" in text or "var SU=" in text:
            errors.append(f"{html.name}: still has inline SHEETS_URL")
        if "hahizd_auth" in text:
            errors.append(f"{html.name}: still references hahizd_auth")

    if errors:
        print("\nWARNINGS:")
        for e in errors:
            print(" -", e)
        return 1

    print(f"\nDone. Updated {len(changed)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
