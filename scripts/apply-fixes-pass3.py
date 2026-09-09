#!/usr/bin/env python3
"""Third pass: form .finally→.then/.catch, og:title, drawer link, meta quotes."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

AUTH_REG_CATCH = """\
.catch(function(){
    document.getElementById('regBtnTxt').style.display='';
    document.getElementById('regSpin').style.display='none';
    btn.disabled=false;
    document.getElementById('regErr').textContent='שגיאה בשליחה, נסה שוב';
    document.getElementById('regErr').style.display='block';
  });"""

MODAL_CATCH = """\
.catch(function(){
    document.getElementById('rmBtnTxt').style.display='';
    document.getElementById('rmSpin').style.display='none';
    btn.disabled=false;
    alert('שגיאה בשליחה. בדוק חיבור לאינטרנט ונסה שוב.');
  });"""

H_HOME_REG_CATCH = """\
.catch(function(){
    document.getElementById('rmBtnTxt').style.display='';
    document.getElementById('rmSpin').style.display='none';
    btn.disabled=false;
    alert('שגיאה בשליחה. בדוק חיבור לאינטרנט ונסה שוב.');
  });"""

OG_TITLES = {
    "employment.html": "הזדמנויות תעסוקתי — ההזדמנות שלי",
    "finance.html": "הזדמנויות כלכלי — ההזדמנות שלי",
    "personal.html": "הזדמנויות אישי — ההזדמנות שלי",
}


def fix_auth_reg_finally(text: str) -> str:
    pattern = re.compile(
        r"fetch\((SHEETS_URL[^)]+)\)\.catch\(function\(\)\{\}\)\.finally\(function\(\)\{\s*"
        r"(show\('Success'\);[\s\S]*?\}\);)",
        re.MULTILINE,
    )

    def repl(m):
        url, body = m.group(1), m.group(2)
        inner = body[:-3]  # drop "});"
        return f"fetch({url})\n      .then(function(){{\n      {inner}\n    }})\n      {AUTH_REG_CATCH}"

    return pattern.sub(repl, text)


def fix_modal_finally(text: str) -> str:
    pattern = re.compile(
        r"fetch\((SU\+'\?'\+p\.toString\(\)|SHEETS_URL\+'\?'\+p\.toString\(\))\,\{method:'GET'\}\)"
        r"\.catch\(function\(\)\{\}\)\.finally\(function\(\)\{\s*"
        r"(document\.getElementById\('rmForm'\)[\s\S]*?\}\);)",
        re.MULTILINE,
    )

    def repl(m):
        url, body = m.group(1), m.group(2)
        inner = body[:-3]
        return (
            f"fetch({url},{{method:'GET'}})\n      .then(function(){{\n      {inner}\n    }})\n      {MODAL_CATCH}"
        )

    return pattern.sub(repl, text)


def fix_hahazdamnut_reg(text: str) -> str:
    old = """fetch(SHEETS_URL+'?'+p.toString(),{method:'GET'})
      .catch(function(){})
      .finally(function(){
        document.getElementById('regForm').style.display='none';
        document.getElementById('regSuccess').style.display='block';
      });"""
    new = """fetch(SHEETS_URL+'?'+p.toString(),{method:'GET'})
      .then(function(){
        document.getElementById('regForm').style.display='none';
        document.getElementById('regSuccess').style.display='block';
      })
      """ + H_HOME_REG_CATCH
    return text.replace(old, new)


def fix_discharge_guide(text: str) -> str:
    old = (
        "fetch(SHEETS_URL+'?'+new URLSearchParams({name:name,phone:phone,notes:notes,timestamp:new Date().toLocaleString('he-IL'),form_type:'lead'}).toString(),{method:'GET'})"
        ".catch(function(){}).finally(function(){\n"
        "    document.getElementById('rmForm').style.display='none';document.getElementById('rmSuccess').style.display='block';\n"
        "  });"
    )
    new = (
        "fetch(SHEETS_URL+'?'+new URLSearchParams({name:name,phone:phone,notes:notes,timestamp:new Date().toLocaleString('he-IL'),form_type:'lead'}).toString(),{method:'GET'})\n"
        "    .then(function(){\n"
        "    document.getElementById('rmForm').style.display='none';document.getElementById('rmSuccess').style.display='block';\n"
        "  })\n"
        "    .catch(function(){\n"
        "    document.getElementById('rmBtnTxt').style.display='';\n"
        "    document.getElementById('rmSpin').style.display='none';\n"
        "    btn.disabled=false;\n"
        "    alert('שגיאה בשליחה. בדוק חיבור לאינטרנט ונסה שוב.');\n"
        "  });"
    )
    return text.replace(old, new)


def fix_compact_auth_reg(text: str) -> str:
    pattern = re.compile(
        r"fetch\(SHEETS_URL\+'\?'\+new URLSearchParams\(\{name:name,phone:phone,notes:notes,timestamp:new Date\(\)\.toLocaleString\('he-IL'\),form_type:'lead'\}\)\.toString\(\),\{method:'GET'\}\)"
        r"\.catch\(function\(\)\{\}\)\.finally\(function\(\)\{\s*"
        r"(show\('Success'\);[\s\S]*?\}\);)"
    )

    def repl(m):
        body = m.group(1)[:-3]
        return (
            "fetch(SHEETS_URL+'?'+new URLSearchParams({name:name,phone:phone,notes:notes,timestamp:new Date().toLocaleString('he-IL'),form_type:'lead'}).toString(),{method:'GET'})\n"
            "      .then(function(){\n      "
            + body
            + "\n    })\n      "
            + AUTH_REG_CATCH
        )

    return pattern.sub(repl, text)


def fix_movies_modal(text: str) -> str:
    old = "fetch(SU+'?'+p.toString(),{method:'GET'}).catch(function(){}).finally(function(){closeRegModal();});"
    new = (
        "fetch(SU+'?'+p.toString(),{method:'GET'})\n"
        "      .then(function(){closeRegModal();})\n"
        "      .catch(function(){alert('שגיאה בשליחה. בדוק חיבור לאינטרנט ונסה שוב.');});"
    )
    return text.replace(old, new)


def fix_og_titles(text: str, name: str) -> str:
    title = OG_TITLES.get(name)
    if not title:
        return text
    text = re.sub(
        r'<meta property="og:title" content="[^"]*"/>',
        f'<meta property="og:title" content="{title}"/>',
        text,
        count=1,
    )
    text = re.sub(
        r'<meta name="twitter:title" content="[^"]*"/>',
        f'<meta name="twitter:title" content="{title}"/>',
        text,
        count=1,
    )
    return text


def fix_hahazdamnut_drawer(text: str) -> str:
    needle = '<a href="partners.html" class="drawer-link">🤝 שיתופי פעולה</a>\n    <a href="#contact" class="drawer-link">✉️ צור קשר</a>'
    repl = (
        '<a href="partners.html" class="drawer-link">🤝 שיתופי פעולה</a>\n'
        '    <a href="pre-meeting.html" class="drawer-link">📝 שאלון לפני פגישה</a>\n'
        '    <a href="#contact" class="drawer-link">✉️ צור קשר</a>'
    )
    if needle in text and "pre-meeting.html" not in text.split("navDrawer")[1][:800]:
        text = text.replace(needle, repl)
    return text


def fix_meta_quotes(text: str) -> str:
    return text.replace(
        'content="מדריך 16 שלבים למשוחרר — צ\'קליסט מעשי לחיים אחרי הצבא, חינם."/>',
        'content="מדריך 16 שלבים למשוחרר — צ&apos;קליסט מעשי לחיים אחרי הצבא, חינם."/>',
    )


for path in sorted(ROOT.glob("*.html")):
    text = path.read_text(encoding="utf-8")
    orig = text
    name = path.name

    text = fix_auth_reg_finally(text)
    text = fix_modal_finally(text)
    text = fix_compact_auth_reg(text)
    text = fix_og_titles(text, name)

    if name == "hahazdamnut.html":
        text = fix_hahazdamnut_reg(text)
        text = fix_hahazdamnut_drawer(text)
    if name == "discharge-guide.html":
        text = fix_discharge_guide(text)
        text = fix_meta_quotes(text)
    if name == "personal-movies.html":
        text = fix_movies_modal(text)

    if text != orig:
        path.write_text(text, encoding="utf-8")
        print("updated", name)
