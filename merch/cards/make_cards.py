"""🃏 Blipville collectible cards (Series 1): one goes in every mystery box.

    python3 merch/cards/make_cards.py      (needs Pillow)

Card: 48 x 56 mm trim (it lies flat inside the 52 x 52 x 60 mm box), rounded 3 mm corners, 3 mm bleed on every side,
300 DPI. Keep text inside the safe area (2.5 mm in from the trim). For each figure there's a regular front and a chrome
chase front (for the 2 chrome boxes of each Blip), and one shared back with the checklist and a box for the in-game
code. dieline.png is the cut guide for the printer. The sprites are drawn from the game's own data (blip.pyw).

If merch/private/series1-codes.csv is there (it is never committed), it also writes a back for every single card with
its code printed in the box, into merch/private/card_backs/ (copies #1-2 of each figure are the chrome ones).
"""
import csv
import json
import importlib.util
import math
import os
import random
import tempfile
import textwrap
from importlib.machinery import SourceFileLoader

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DPI = 300
MM = DPI / 25.4
TRIM_W, TRIM_H, BLEED, CORNER, SAFE = 48, 56, 3, 3, 2.5
W, H = round((TRIM_W + 2 * BLEED) * MM), round((TRIM_H + 2 * BLEED) * MM)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

SERIES = [("Silvertear-03", "regular"), ("Blip", "regular"), ("T-Rex", "regular"), ("Wendigo", "regular"), ("Bun", "regular"),
          ("Beta Buddy", "regular")]
CHROME_COPIES = (1, 2)      # which copy numbers of each figure are chrome
BIOS = {"Silvertear-03": "Tactical bodyguard. Secretly loves naps.",
        "Blip": "The friendliest Blip in town.",
        "T-Rex": "Tiny arms. Huge heart.",
        "Wendigo": "Spooky antlers, gentle soul.",
        "Bun": "Shy, soft and very good at hiding.",
        "Beta Buddy": "Our very first tester. Still finding bugs."}
THEMES = {   # (top, bottom, accent, banner)
    "regular": ((70, 56, 150), (24, 18, 56), (170, 150, 255), (98, 76, 230)),
    "chrome": ((232, 236, 246), (112, 120, 140), (255, 255, 255), (84, 92, 116)),
}
# 🏷️ which series this is: merch/series.json is the one place to rename it (cards, box and site read it)
_SER = json.load(open(os.path.join(ROOT, "merch", "series.json")))
SERIES_NO, SERIES_NAME = _SER["number"], _SER["name"]
SERIES_LABEL = f"Series {SERIES_NO}: {SERIES_NAME}"
SITE, DISCORD = "johnblip189.github.io/Blipville", "discord.gg/Q3zmYakNZT"
GOLD, INK = (255, 214, 58), (40, 22, 70)

# a little pixel font for the logo (5 x 7)
GLYPHS = {
    "B": ["1111.", "1...1", "1...1", "1111.", "1...1", "1...1", "1111."],
    "L": ["1....", "1....", "1....", "1....", "1....", "1....", "11111"],
    "I": ["11111", "..1..", "..1..", "..1..", "..1..", "..1..", "11111"],
    "P": ["1111.", "1...1", "1...1", "1111.", "1....", "1....", "1...."],
    "V": ["1...1", "1...1", "1...1", "1...1", "1...1", ".1.1.", "..1.."],
    "E": ["11111", "1....", "1....", "1111.", "1....", "1....", "11111"],
}


def game():
    os.environ.setdefault("APPDATA", tempfile.mkdtemp())
    spec = importlib.util.spec_from_loader("blip", SourceFileLoader("blip", os.path.join(ROOT, "blip.pyw")))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def px(x_mm, y_mm):
    """Trim coordinates (mm, top-left of the trimmed card) -> pixels in the bleed file."""
    return round((x_mm + BLEED) * MM), round((y_mm + BLEED) * MM)


def font(path, size_mm):
    return ImageFont.truetype(path, max(8, round(size_mm * MM)))


def sprite_grid(m, kind, color=0):
    """The Blip as the game draws it: body, feet, eyes with a shine, mouth (colors per pixel, None = empty)."""
    v = m.VARIANTS[kind]
    cols = m.kind_colors(kind)
    pal = {**cols[color % len(cols)], **v.get("extra", {})}
    body = pal.get("art") or v["body"]
    g = [[None] * 16 for _ in range(13)]
    for y, row in enumerate(body):
        for x, ch in enumerate(row):
            if ch != ".":
                g[y][x] = m.px_color(pal, ch)
    if v["feet"]:
        for x, ch in enumerate(v["feet"]["stand"]):
            if ch != ".":
                g[12][x] = pal.get("f", pal["o"])
    ey, dx, e = v["eyes"], v.get("dx", 0), pal["e"]
    for ex in (4 + dx, 10 + dx):
        for a in (0, 1):
            for b in (0, 1):
                g[ey + b][ex + a] = e
        g[ey][ex] = "#ffffff"
    if v.get("xeye"):
        for i in range(4):
            g[ey - 1 + i][3 + i] = g[ey - 1 + i][6 - i] = pal.get("x", pal["o"])
    if v.get("mouth", True):
        g[ey + 4][7] = g[ey + 4][8] = e
    return g


def draw_sprite(img, g, cx, cy, size_px, silhouette=None, shadow=True):
    s = size_px / 16
    x0, y0 = cx - 8 * s, cy - 6.5 * s
    d = ImageDraw.Draw(img)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        for y, row in enumerate(g):
            for x, c in enumerate(row):
                if c:
                    sd.rectangle([x0 + x * s + s * 0.35, y0 + y * s + s * 0.35, x0 + (x + 1) * s + s * 0.35, y0 + (y + 1) * s + s * 0.35],
                                 fill=(0, 0, 0, 110))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(s * 0.4)))
        d = ImageDraw.Draw(img)
    for y, row in enumerate(g):
        for x, c in enumerate(row):
            if c:
                d.rectangle([round(x0 + x * s), round(y0 + y * s), round(x0 + (x + 1) * s) - 1, round(y0 + (y + 1) * s) - 1],
                            fill=silhouette or c)


def gradient(top, bottom):
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(3)) + (255,))
    return img


def pixel_stars(img, seed, color, n=70):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y = rnd.randrange(W), rnd.randrange(H)
        s = rnd.choice((4, 6, 8, 12))
        a = rnd.randrange(80, 220)
        c = color + (a,)
        d.rectangle([x, y, x + s, y + s], fill=c)
        if s >= 8:
            d.rectangle([x - s, y + s // 3, x + 2 * s, y + 2 * s // 3], fill=c)
            d.rectangle([x + s // 3, y - s, x + 2 * s // 3, y + 2 * s], fill=c)


def logo(img, cx_mm, top_mm, width_mm, color, outline):
    text = "BLIPVILLE"
    cells = len(text) * 6 - 1
    u = width_mm * MM / cells
    x0 = px(cx_mm, 0)[0] - cells * u / 2
    y0 = px(0, top_mm)[1]
    d = ImageDraw.Draw(img)
    for pass_, col in ((0, outline), (1, color)):
        grow = u * 0.45 if pass_ == 0 else 0
        for i, ch in enumerate(text):
            for gy, row in enumerate(GLYPHS[ch]):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        X = x0 + (i * 6 + gx) * u
                        Y = y0 + gy * u
                        d.rectangle([X - grow, Y - grow, X + u + grow - 1, Y + u + grow - 1], fill=col)
    return y0 + 7 * u


def text_center(d, cx_mm, y_mm, s, f, fill, stroke=0, stroke_fill=None):
    x, y = px(cx_mm, y_mm)
    d.text((x, y), s, font=f, fill=fill, anchor="mt", stroke_width=stroke, stroke_fill=stroke_fill)


def rounded(d, box_mm, r_mm, **kw):
    (x0, y0), (x1, y1) = px(*box_mm[:2]), px(*box_mm[2:])
    d.rounded_rectangle([x0, y0, x1, y1], radius=round(r_mm * MM), **kw)


def burst(img, cx_mm, cy_mm, r_mm, text, fill, ink):
    d = ImageDraw.Draw(img)
    cx, cy = px(cx_mm, cy_mm)
    R, r = r_mm * MM, r_mm * MM * 0.72
    pts = []
    for i in range(28):
        a = math.pi * i / 14 - math.pi / 2
        rr = R if i % 2 == 0 else r
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill, outline=ink, width=round(0.5 * MM))
    f = font(BOLD, r_mm * 0.24)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        d.text((cx, cy + (i - (len(lines) - 1) / 2) * r_mm * 0.30 * MM), line, font=f, fill=ink, anchor="mm")


def chrome_grid(g):
    """A sprite grid turned to polished chrome: every color becomes silver at its own brightness (so details stay)."""
    out = []
    for row in g:
        r2 = []
        for c in row:
            if not c:
                r2.append(None)
                continue
            n = int(c.lstrip("#"), 16)
            lum = (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255
            v = round(60 + 190 * lum ** 0.75)
            r2.append("#%02x%02x%02x" % (v, v, min(255, v + 14)))
        out.append(r2)
    return out


def holo(img):
    """A soft rainbow foil sheen in diagonal bands."""
    sheen = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    cols = [(255, 120, 200), (255, 220, 120), (140, 255, 200), (120, 190, 255), (200, 140, 255)]
    band = W * 0.16
    for i in range(-6, 10):
        c = cols[i % len(cols)]
        x = i * band
        sd.polygon([(x, 0), (x + band, 0), (x + band - W * 0.55, H), (x - W * 0.55, H)], fill=c + (46,))
    img.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(50)))


def wrap_center(d, cx, y, s, f, fill, width_chars, lh):
    for i, line in enumerate(textwrap.wrap(s, width_chars)):
        text_center(d, cx, y + i * lh, line, f, fill)


def front(m, kind, number, chrome=False):
    top, bottom, accent, banner = THEMES["chrome" if chrome else "regular"]
    img = gradient(top, bottom)
    if chrome:
        holo(img)
    pixel_stars(img, kind, (255, 255, 255), 40)
    if chrome:                                           # a foil-like diagonal shine
        shine = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shine)
        for i, a in ((0, 90), (1, 60)):
            off = i * 150
            sd.polygon([(W * 0.15 + off, 0), (W * 0.32 + off, 0), (W * 0.02 + off, H), (-W * 0.15 + off, H)], fill=(255, 255, 255, a))
        img.alpha_composite(shine.filter(ImageFilter.GaussianBlur(25)))
    ink = (40, 44, 64) if chrome else (255, 255, 255)
    logo(img, TRIM_W / 2, 2.8, 34, (255, 255, 255), (60, 66, 86) if chrome else (40, 24, 80))
    d = ImageDraw.Draw(img)
    # the art window: a glowing stage with the Blip, big
    win = (4, 9.6, TRIM_W - 4, 37.2)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = px(TRIM_W / 2, 24.5)
    for i in range(12, 0, -1):
        rr = i * 1.5 * MM
        gd.ellipse([cx - rr, cy - rr * 0.8, cx + rr, cy + rr * 0.8], fill=accent + (int(10 + (12 - i) * 6),))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)
    rounded(d, win, 3, outline=accent + (255,), width=round(0.45 * MM))
    g = sprite_grid(m, kind)
    draw_sprite(img, chrome_grid(g) if chrome else g, *px(TRIM_W / 2, 24.0), 29 * MM)
    d = ImageDraw.Draw(img)
    rounded(d, (5.2, 10.8, 13.6, 14.6), 1.2, fill=(10, 8, 24, 190))
    text_center(d, 9.4, 11.4, f"#{number}/6", font(BOLD, 1.9), (255, 255, 255))
    if chrome:
        burst(img, TRIM_W - 9.0, 13.6, 5.2, "CHROME!", (236, 240, 250), (40, 44, 64))
        d = ImageDraw.Draw(img)
    # name banner
    by0, by1 = 38.4, 44.2
    (bx0, _), (bx1, _) = px(3.5, 0), px(TRIM_W - 3.5, 0)
    _, y0 = px(0, by0)
    _, y1 = px(0, by1)
    notch = 1.6 * MM
    d.polygon([(bx0 - notch, y0), (bx1 + notch, y0), (bx1, (y0 + y1) / 2), (bx1 + notch, y1), (bx0 - notch, y1), (bx0, (y0 + y1) / 2)],
              fill=banner + (255,), outline=(255, 255, 255, 255), width=round(0.3 * MM))
    name = kind.upper()
    text_center(d, TRIM_W / 2, by0 + 1.0, name, font(BOLD, 3.9 if len(name) < 10 else 3.2), (255, 255, 255), stroke=round(0.22 * MM), stroke_fill=(40, 20, 60))
    wrap_center(d, TRIM_W / 2, 45.2, BIOS[kind], font(REG, 1.7), ink, 34, 2.0)
    if chrome:
        text_center(d, TRIM_W / 2, 50.9, "\u2726 CHROME \u00b7 ONLY 2 OF EACH \u2726", font(BOLD, 1.8), (40, 44, 64))
    else:
        text_center(d, TRIM_W / 2, 50.9, f"\u2605 {SERIES_NAME.upper()} \u00b7 {number} OF 6 \u2605", font(BOLD, 1.8), GOLD)
    return round_corners(img)


def back(m, code=None):
    top, bottom, accent, banner = THEMES["regular"]
    img = gradient(top, bottom)
    pixel_stars(img, "back", (255, 255, 255), 30)
    end = logo(img, TRIM_W / 2, 2.6, 30, (255, 255, 255), (40, 24, 80))
    d = ImageDraw.Draw(img)
    text_center(d, TRIM_W / 2, end / MM - BLEED + 1.0, "COLLECT THEM ALL!", font(BOLD, 2.5), GOLD, stroke=round(0.18 * MM), stroke_fill=(40, 20, 60))
    tw, th, gap = 13.0, 11.6, 1.2
    gx0, gy0 = (TRIM_W - (3 * tw + 2 * gap)) / 2, 11.4
    for i, (kind, _) in enumerate(SERIES):
        x0, y0 = gx0 + (i % 3) * (tw + gap), gy0 + (i // 3) * (th + gap)
        rounded(d, (x0, y0, x0 + tw, y0 + th), 1.4, fill=banner + (235,), outline=(255, 255, 255, 200), width=round(0.2 * MM))
        draw_sprite(img, sprite_grid(m, kind), *px(x0 + tw / 2, y0 + 3.9), 7.6 * MM, shadow=False)
        d = ImageDraw.Draw(img)
        label = kind if len(kind) < 11 else kind.replace("-03", "")
        text_center(d, x0 + tw / 2, y0 + 7.0, label, font(BOLD, 1.35), (255, 255, 255))
        for j, t in enumerate(("B", "C")):                              # Basic / Chrome tick boxes
            bx = x0 + tw / 2 - 2.6 + j * 3.6
            d.rectangle([*px(bx, y0 + 9.2), *px(bx + 1.5, y0 + 10.7)], outline=(255, 255, 255, 230), width=round(0.18 * MM))
            d.text(px(bx + 1.9, y0 + 9.95), t, font=font(BOLD, 1.2), fill=GOLD, anchor="lm")
    # the in-game code
    py0 = 37.0
    rounded(d, (3.2, py0, TRIM_W - 3.2, py0 + 10.6), 1.8, fill=GOLD + (255,), outline=(60, 30, 10, 255), width=round(0.25 * MM))
    text_center(d, TRIM_W / 2, py0 + 0.8, "FREE IN-GAME COLOR!", font(BOLD, 2.1), (60, 30, 10))
    rounded(d, (6.5, py0 + 3.6, TRIM_W - 6.5, py0 + 7.0), 0.8, fill=(255, 255, 255, 255), outline=(60, 30, 10, 255), width=round(0.18 * MM))
    if code:
        text_center(d, TRIM_W / 2, py0 + 4.25, code, font(BOLD, 2.2), (30, 20, 50))
    else:
        text_center(d, TRIM_W / 2, py0 + 4.6, "your code", font(REG, 1.5), (170, 160, 150))
    text_center(d, TRIM_W / 2, py0 + 7.75, "In Blipville: ? \u2192 Secret code (Windows: right-click a pet)", font(REG, 1.25), (60, 30, 10))
    text_center(d, TRIM_W / 2, 48.6, f"Play free: {SITE}", font(BOLD, 1.5), (255, 255, 255))
    text_center(d, TRIM_W / 2, 50.6, f"Discord: {DISCORD}", font(REG, 1.4), (225, 220, 255))
    text_center(d, TRIM_W / 2, 52.4, "\u26a0 Small parts. Not for children under 3.", font(BOLD, 1.25), GOLD)
    return round_corners(img)


def round_corners(img):
    """Show the rounded trim in the art (outside the cut stays as bleed, so nothing changes for the printer)."""
    return img


def dieline():
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, H - 1], outline=(0, 160, 255), width=4)                                      # bleed edge
    d.rounded_rectangle([*px(0, 0), *px(TRIM_W, TRIM_H)], radius=round(CORNER * MM), outline=(255, 0, 0), width=5)   # cut
    d.rounded_rectangle([*px(SAFE, SAFE), *px(TRIM_W - SAFE, TRIM_H - SAFE)], radius=round(1 * MM), outline=(0, 170, 0), width=3)
    f = font(BOLD, 1.8)
    for (ym, t, c) in ((-1.8, "BLEED (3 mm)", (0, 120, 220)), (0.8, "CUT (3 mm corners)", (255, 0, 0)), (TRIM_H / 2, "SAFE AREA (2.5 mm)", (0, 140, 0))):
        text_center(d, TRIM_W / 2, ym, t, f, c)
    return img


def trimmed_preview(img):
    """The card as it'll look once cut (for previews): trimmed with rounded corners."""
    b = round(BLEED * MM)
    c = img.crop((b, b, W - b, H - b)).convert("RGBA")
    mask = Image.new("L", c.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, c.width - 1, c.height - 1], radius=round(CORNER * MM), fill=255)
    out = Image.new("RGBA", c.size, (0, 0, 0, 0))
    out.paste(c, (0, 0), mask)
    return out


def sheet(cards, cols, path, scale=0.62):
    tw, th = round(cards[0].width * scale), round(cards[0].height * scale)
    rows = -(-len(cards) // cols)
    s = Image.new("RGBA", (tw * cols + 16 * (cols + 1), th * rows + 16 * (rows + 1)), (20, 18, 34, 255))
    for i, c in enumerate(cards):
        s.alpha_composite(c.resize((tw, th), Image.LANCZOS), (16 + (i % cols) * (tw + 16), 16 + (i // cols) * (th + 16)))
    s.convert("RGB").save(path)


if __name__ == "__main__":
    m = game()
    out = HERE
    for old in os.listdir(out):                                         # the old hang-card files
        if old.endswith(".png"):
            os.remove(os.path.join(out, old))
    fronts, chromes = [], []
    for n, (kind, _) in enumerate(SERIES, 1):
        name = kind.lower().replace(" ", "_").replace("-", "")
        f = front(m, kind, n)
        f.convert("RGB").save(os.path.join(out, f"{name}_front.png"), dpi=(DPI, DPI))
        fronts.append(trimmed_preview(f))
        c = front(m, kind, n, chrome=True)
        c.convert("RGB").save(os.path.join(out, f"{name}_chrome_front.png"), dpi=(DPI, DPI))
        chromes.append(trimmed_preview(c))
    b = back(m)
    b.convert("RGB").save(os.path.join(out, "card_back.png"), dpi=(DPI, DPI))
    dieline().convert("RGB").save(os.path.join(out, "dieline.png"), dpi=(DPI, DPI))
    sheet(fronts + [trimmed_preview(b)], 4, os.path.join(out, "cards_preview.png"))
    sheet(chromes, 3, os.path.join(out, "chrome_cards_preview.png"))
    made = 0
    codes = os.path.join(ROOT, "merch", "private", "series1-codes.csv")
    if os.path.exists(codes):                                            # private: one back per card, with its code
        pdir = os.path.join(ROOT, "merch", "private", "card_backs")
        os.makedirs(pdir, exist_ok=True)
        for row in csv.DictReader(open(codes, newline="")):
            kind, copy = row["figure"], int(row["copy"].strip("#").split()[0])
            finish = "chrome" if copy in CHROME_COPIES else "basic"
            name = kind.lower().replace(" ", "_").replace("-", "")
            back(m, row["code"]).convert("RGB").save(os.path.join(pdir, f"{name}_{copy}_{finish}_back.png"), dpi=(DPI, DPI))
            made += 1
    print("wrote", len(SERIES), "fronts +", len(SERIES), "chrome fronts, card_back.png, dieline.png, previews",
          f"and {made} coded backs (private)" if made else "")
