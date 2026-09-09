#!/usr/bin/env python3
"""Generate 1200x630 Open Graph share image for WhatsApp / social previews."""
from pathlib import Path

from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "og-share.jpg"

W, H = 1200, 630


def rtl(text: str) -> str:
    return get_display(text)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), "#F4F8FF")
    draw = ImageDraw.Draw(img)

    for y in range(H):
        t = y / H
        r = int(244 * (1 - t) + 10 * t)
        g = int(248 * (1 - t) + 22 * t)
        b = int(255 * (1 - t) + 40 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    cx, cy = 1010, 315
    for dx, dy, radius, color, alpha in [
        (-28, -14, 50, "#1A56A0", 190),
        (28, -14, 50, "#0F3873", 190),
        (0, 20, 50, "#4DAEF5", 190),
    ]:
        rgb = tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
        od.ellipse(
            [cx + dx - radius, cy + dy - radius, cx + dx + radius, cy + dy + radius],
            fill=rgb + (alpha,),
        )
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    title_font = load_font(58, bold=True)
    sub_font = load_font(30)
    url_font = load_font(24)

    draw.text((80, 210), rtl("ההזדמנות שלי"), fill="#0A1628", font=title_font)
    draw.text((80, 295), rtl("המנטור שלך לחיים שאחרי הצבא"), fill="#1A56A0", font=sub_font)
    draw.text((80, 365), rtl("ליווי אישי למשוחררים בגילאי 20–25"), fill="#475569", font=sub_font)
    draw.text((80, 530), "hahizdamnut-shelly.com", fill="#64748B", font=url_font)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "JPEG", quality=88, optimize=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
