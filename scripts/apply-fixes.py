#!/usr/bin/env python3
"""Apply non-WP / non-social / non-privacy site fixes."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = "https://hahizdamnut-shelly.com"

META: dict[str, str] = {
    "employment.html": "הזדמנויות תעסוקתיות למשוחררים — משרות, עבודה בחו\"ל, אבטחה והכשרות מקצועיות.",
    "finance.html": "ליווי כלכלי למשוחררים — ייעוץ פיננסי, השקעות, נדל\"ן וכלים לניהול כסף חכם.",
    "personal.html": "ליווי אישי למשוחררים — ספרים, סרטים, מורים, פודקאסטים ומדיטציה לצמיחה אישית.",
    "discharge-guide.html": "מדריך 16 שלבים למשוחרר — צ'קליסט מעשי לחיים אחרי הצבא, חינם.",
    "pre-meeting.html": "שאלון קצר לפני פגישת היכרות — עוזר לנו להתאים את הליווי אליך.",
    "404.html": "הדף לא נמצא — חזרה לאתר ההזדמנות שלי.",
    "personal-books.html": "ספרים מומלצים לצמיחה אישית וכלכלית — תוכן לרשומים באזור האישי.",
    "personal-movies.html": "סרטים מומלצים להשראה וצמיחה — תוכן לרשומים באזור האישי.",
    "personal-teachers.html": "מורים ומנטורים מומלצים — תוכן לרשומים באזור האישי.",
    "personal-podcasts.html": "פודקאסטים מומלצים ללמידה והשראה — תוכן לרשומים.",
    "personal-meditation.html": "מדיטציה ומיינדפולנס — תוכן לרשומים באזור האישי.",
}

OG_DESC: dict[str, str] = {
    "employment.html": "הזדמנויות תעסוקתיות ומשרות למשוחררים.",
    "finance.html": "ליווי כלכלי וייעוץ פיננסי למשוחררים.",
    "personal.html": "ליווי אישי — ספרים, סרטים, מורים ועוד.",
    "about.html": "הסיפור של ההזדמנות שלי — ליווי אחרי הצבא.",
    "app.html": "אפליקציית ההזדמנות שלי — ניהול מטרות ומשימות.",
    "partners.html": "שיתופי פעולה וארגונים שמלווים משוחררים.",
    "hahazdamnut.html": "ליווי אישי למשוחררים בגילאי 20-25.",
}

NOINDEX = {"404.html", "pre-meeting.html"}

IMG_FIXES = [
    ("יייעוץ-פיננסי-חינם.png", "ייעוץ-פיננסי-חינם.png"),
    ("פרונטליייף.png", "%D7%A4%D7%A8%D7%95%D7%A0%D7%98%D7%9C%D7%99%D7%99%D7%A3.png"),
    ("בית-הספר-לקוסמיים.png", "בית-הספר-לקוסמים.png"),
]

LS_BEFORE_FETCH = re.compile(
    r"try\{var n2=phone\.replace\(/\\D/g,''\)\.replace\(/\^0\+/,''\);"
    r"var s2=JSON\.parse\(localStorage\.getItem\('hahizd_phones'\)\|\|\'\[\]\'\);"
    r"if\(s2\.indexOf\(n2\)===-1\)\{s2\.push\(n2\);\}"
    r"localStorage\.setItem\('hahizd_phones',JSON\.stringify\(s2\)\);\}catch\(e\)\{\}"
)


def insert_after_title(text: str, insert: str) -> str:
    if insert.strip() in text:
        return text
    return re.sub(
        r"(<title>[^<]+</title>)",
        r"\1\n" + insert,
        text,
        count=1,
    )


def fix_file(path: pathlib.Path) -> list[str]:
    name = path.name
    changes: list[str] = []
    text = path.read_text(encoding="utf-8")
    orig = text

    # meta description
    if name in META and 'name="description"' not in text:
        block = f'<meta name="description" content="{META[name]}"/>'
        text = insert_after_title(text, block)
        changes.append("meta description")

    # noindex
    if name in NOINDEX and 'name="robots"' not in text:
        text = insert_after_title(text, '<meta name="robots" content="noindex, nofollow"/>')
        changes.append("noindex")

    # og:url + canonical
    page_url = f"{SITE}/{name}"
    text = text.replace(
        "https://giladddd.github.io/HAHIZDAMNUT-SHELLY/hahazdamnut.html",
        page_url,
    )
    if f'property="og:url" content="{page_url}"' in text and f'rel="canonical"' not in text:
        text = text.replace(
            f'<meta property="og:url" content="{page_url}"/>',
            f'<link rel="canonical" href="{page_url}"/>\n<meta property="og:url" content="{page_url}"/>',
            1,
        )
        changes.append("canonical/og:url")

    # og/twitter description per page
    if name in OG_DESC:
        desc = OG_DESC[name]
        text = re.sub(
            r'<meta property="og:description" content="[^"]*"/>',
            f'<meta property="og:description" content="{desc}"/>',
            text,
            count=1,
        )
        text = re.sub(
            r'<meta name="twitter:description" content="[^"]*"/>',
            f'<meta name="twitter:description" content="{desc}"/>',
            text,
            count=1,
        )
        changes.append("og description")

    # image filename typos
    for old, new in IMG_FIXES:
        if old in text:
            text = text.replace(old, new)
            changes.append(f"img:{old}")

    # phone placeholder
    if "050-0000000" in text:
        text = text.replace("050-0000000", "05X-XXX-XXXX")
        changes.append("phone placeholder")

    # email case
    text = text.replace("Hahizdamnutshelly@gmail.com", "hahizdamnutshelly@gmail.com")

    # remove auto popup modal (homepage only)
    if name == "hahazdamnut.html":
        text = re.sub(
            r"\n<script>\nsetTimeout\(function\(\)\{\n  if\(typeof openRegModal === 'function'\) openRegModal\(\);\n\}, 20000\);\n</script>",
            "",
            text,
        )
        if "setTimeout" not in orig or "openRegModal" in text:
            if "setTimeout(function" not in text and "20000" not in text:
                changes.append("remove auto modal")

        # orphan #tracks CSS
        text = re.sub(
            r"#tracks\{background:var\(--hero-bg\);position:relative;overflow:hidden\}\n"
            r"#tracks::before\{[^}]+\}\n"
            r"#tracks \.container\{position:relative\}\n"
            r"#tracks \.sec-title\{color:#fff\}\n"
            r"#tracks \.sec-sub\{color:rgba\(255,255,255,\.55\)\}\n",
            "",
            text,
        )
        changes.append("remove #tracks CSS")

    # partners: consistent about link
    if name == "partners.html":
        text = text.replace(
            '<li><a href="hahazdamnut.html#about">אודות</a></li>',
            '<li><a href="about.html">אודות</a></li>',
            1,
        )
        changes.append("partners about nav")

    # auth: don't write localStorage before fetch
    if LS_BEFORE_FETCH.search(text):
        text = LS_BEFORE_FETCH.sub("", text)
        changes.append("auth localStorage order")

    # forms: remove no-cors (browser can surface network errors)
    if "mode:'no-cors'" in text or 'mode: "no-cors"' in text:
        text = text.replace(",mode:'no-cors'", "")
        text = text.replace(', mode: "no-cors"', "")
        text = text.replace("mode:'no-cors',", "")
        changes.append("remove no-cors")

    # contact form: don't show success on catch
    if name == "hahazdamnut.html":
        text = text.replace(
            "}).then(function(){ showSuccess(); }).catch(function(){ showSuccess(); });",
            "}).then(function(){ showSuccess(); }).catch(function(){ "
            "btn.disabled=false; document.getElementById('cfBtnText').style.display='inline'; "
            "document.getElementById('cfSpinner').style.display='none'; "
            "document.getElementById('errPhone').textContent='שגיאה בשליחה, נסה שוב'; "
            "document.getElementById('errPhone').classList.add('show'); });",
        )
        if "form_type" not in text.split("contactForm")[1][:800] if "contactForm" in text else True:
            text = text.replace(
                "timestamp: new Date().toLocaleString('he-IL')\n  });",
                "timestamp: new Date().toLocaleString('he-IL'),\n    form_type: 'contact'\n  });",
                1,
            )
        changes.append("contact form error handling")

    # reg modal form_type on homepage
    if name == "hahazdamnut.html" and "form_type:'registration_modal'" not in text:
        text = text.replace(
            "timestamp:new Date().toLocaleString('he-IL')\n    });",
            "timestamp:new Date().toLocaleString('he-IL'),\n      form_type:'registration_modal'\n    });",
            1,
        )

    # pre-meeting phone validation align
    if name == "pre-meeting.html":
        text = text.replace(
            "if(!phone || !/^\\d{9,15}$/.test(phone.replace(/[\\s\\-\\+]/g,''))){",
            "if(!phone || !/^(\\+972|0)\\d{1,2}[-]?\\d{7}$/.test(phone.replace(/\\s/g,''))){",
        )

    if text != orig:
        path.write_text(text, encoding="utf-8")
    return changes


def fix_hahazdamnut_nav(text: str) -> str:
    needle = '<li><a href="discharge-guide.html">מדריך למשוחרר 🎁</a></li>'
    link = '<li><a href="pre-meeting.html">שאלון לפני פגישה</a></li>\n    '
    if needle in text and "pre-meeting.html" not in text.split("nav-links")[1][:1200]:
        return text.replace(needle, link + needle, 1)
    return text


def main() -> None:
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: https://hahizdamnut-shelly.com/sitemap.xml\n",
        encoding="utf-8",
    )
    print("robots.txt updated")

    hp = ROOT / "hahazdamnut.html"
    t = hp.read_text(encoding="utf-8")
    t2 = fix_hahazdamnut_nav(t)
    if t2 != t:
        hp.write_text(t2, encoding="utf-8")
        print("hahazdamnut.html: pre-meeting nav link")

    for html in sorted(ROOT.glob("*.html")):
        ch = fix_file(html)
        if ch:
            print(f"{html.name}: {', '.join(ch)}")


if __name__ == "__main__":
    main()
