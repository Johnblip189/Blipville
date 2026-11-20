"""🃏 Blipville figure cards (Series 1): a front for each figure plus one shared back, ready for a print shop.

    python3 merch/cards/make_cards.py      (needs Pillow)

Card: 90 x 140 mm trim, 3 mm bleed on every side, 300 DPI (1134 x 1724 px files). Keep text inside the safe area
(4 mm in from the trim). dieline.png shows the cut line, the hang slot and where the blister bubble sits; it is a guide
for the printer, not part of the art. The sprites are drawn from the game's own data (blip.pyw).
"""
import importlib.util
import math
import os
import random
import tempfile
from importlib.machinery import SourceFileLoader

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DPI = 300
MM = DPI / 25.4
TRIM_W, TRIM_H, BLEED = 90, 140, 3
W, H = round((TRIM_W + 2 * BLEED) * MM), round((TRIM_H + 2 * BLEED) * MM)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

SERIES = [("Silvertear-03", "regular"), ("Blip", "regular"), ("T-Rex", "regular"), ("Wendigo", "regular"), ("Bun", "regular"),
          ("Beta Buddy", "regular")]
SLOTS = 6
BIOS = {"Silvertear-03": "Tactical bodyguard. Secretly loves naps.",
        "Blip": "The friendliest Blip in town.",
        "T-Rex": "Tiny arms. Huge heart.",
        "Wendigo": "Spooky antlers, gentle soul.",
        "Bun": "Shy, soft and very good at hiding.",
        "Beta Buddy": "Our very first tester. Still finding bugs."}
THEMES = {   # card colors by rarity: (top, bottom, accent, banner)
    "regular": ((58, 52, 110), (24, 20, 52), (154, 140, 255), (90, 74, 224)),
    "rare": ((112, 60, 170), (34, 14, 64), (255, 140, 220), (176, 70, 200)),
    "ultra-rare": ((250, 214, 120), (150, 96, 20), (255, 248, 210), (200, 130, 30)),
}
STARS = {"regular": 1, "rare": 2, "ultra-rare": 3}
SITE, DISCORD = "johnblip189.github.io/Blipville", "discord.gg/Q3zmYakNZT"

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


def stars(d, cx_mm, y_mm, n, total, size_mm, fill, empty):
    f = font(BOLD, size_mm)
    s = "★" * n + "☆" * (total - n)
    text_center(d, cx_mm, y_mm, s, f, fill)


def warning(d, y_mm, ink):
    f = font(BOLD, 2.0)
    text_center(d, TRIM_W / 2, y_mm, "⚠ WARNING: CHOKING HAZARD — Small parts.", f, ink)
    text_center(d, TRIM_W / 2, y_mm + 2.8, "Not for children under 3 years.", font(REG, 2.0), ink)


def front(m, kind, rarity):
    top, bottom, accent, banner = THEMES[rarity]
    img = gradient(top, bottom)
    pixel_stars(img, kind, (255, 255, 255) if rarity != "ultra-rare" else (255, 255, 240), 90 if rarity != "regular" else 60)
    if rarity == "ultra-rare":                           # a foil-like diagonal shine
        shine = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shine)
        for i, a in ((0, 90), (1, 60)):
            off = i * 260
            sd.polygon([(W * 0.15 + off, 0), (W * 0.32 + off, 0), (W * 0.02 + off, H), (-W * 0.15 + off, H)], fill=(255, 255, 255, a))
        img.alpha_composite(shine.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(img)
    ink = (30, 18, 50) if rarity == "ultra-rare" else (255, 255, 255)
    # logo + series
    bottom_logo = logo(img, TRIM_W / 2, 13.5, 70, (255, 255, 255), (40, 24, 80) if rarity != "ultra-rare" else (110, 60, 10))
    d = ImageDraw.Draw(img)
    text_center(d, TRIM_W / 2, (bottom_logo / MM) - BLEED + 2.2, "FIGURES • SERIES 1", font(BOLD, 3.0), ink)
    # the window (where the bubble and the figure sit): a glowing stage behind the figure
    win = (11, 37, 79, 103)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = px((win[0] + win[2]) / 2, (win[1] + win[3]) / 2 + 4)
    for i in range(12, 0, -1):
        rr = i * 3.2 * MM
        gd.ellipse([cx - rr, cy - rr * 0.8, cx + rr, cy + rr * 0.8], fill=accent + (int(10 + (12 - i) * 6),))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(img)
    rounded(d, win, 7, outline=accent + (255,), width=round(0.8 * MM))
    sx0, sy0 = px(win[0] + 10, win[3] - 9)
    sx1, sy1 = px(win[2] - 10, win[3] - 4)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))                            # a soft stage shadow under the figure
    ImageDraw.Draw(sh).ellipse([sx0, sy0, sx1, sy1], fill=(0, 0, 0, 110))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(img)
    # the figure itself goes in the bubble; a small sprite badge on the card shows who's inside
    burst(img, 73, 38, 12, "WITH\nDISPLAY\nBASE!", (255, 214, 58), (60, 30, 10))
    d = ImageDraw.Draw(img)
    # name banner
    by0, by1 = 106.5, 118.5
    (bx0, _), (bx1, _) = px(6, 0), px(TRIM_W - 6, 0)
    _, y0 = px(0, by0)
    _, y1 = px(0, by1)
    notch = 3 * MM
    d.polygon([(bx0 - notch, y0), (bx1 + notch, y0), (bx1, (y0 + y1) / 2), (bx1 + notch, y1), (bx0 - notch, y1), (bx0, (y0 + y1) / 2)],
              fill=banner + (255,), outline=(255, 255, 255, 255) if rarity != "ultra-rare" else (90, 50, 0, 255), width=round(0.5 * MM))
    name = kind.upper()
    text_center(d, TRIM_W / 2, by0 + 2.0, name, font(BOLD, 6.6 if len(name) < 10 else 5.4), (255, 255, 255), stroke=round(0.35 * MM), stroke_fill=(40, 20, 60))
    # mini sprite badge next to the banner
    draw_sprite(img, sprite_grid(m, kind), px(13, by0 - 2.5)[0], px(0, by0 - 2.5)[1], 12 * MM)
    d = ImageDraw.Draw(img)
    # rarity
    stars(d, TRIM_W / 2, 120.5, STARS[rarity], 3, 4.2, (255, 214, 58) if rarity != "ultra-rare" else (120, 60, 0), None)
    text_center(d, TRIM_W / 2, 125.4, rarity.upper().replace("-", " "), font(BOLD, 2.6), ink)
    warning(d, 130.5, ink)
    return img


def back(m):
    top, bottom, accent, banner = THEMES["regular"]
    img = gradient(top, bottom)
    pixel_stars(img, "back", (255, 255, 255), 50)
    d = ImageDraw.Draw(img)
    bottom_logo = logo(img, TRIM_W / 2, 13.0, 52, (255, 255, 255), (40, 24, 80))
    d = ImageDraw.Draw(img)
    y = (bottom_logo / MM) - BLEED + 2.0
    text_center(d, TRIM_W / 2, y, "COLLECT THEM ALL!", font(BOLD, 4.4), (255, 214, 58), stroke=round(0.3 * MM), stroke_fill=(40, 20, 60))
    # checklist: 3 x 2 tiles
    tw, th, gap = 25.0, 27.0, 2.5
    gx0 = (TRIM_W - (3 * tw + 2 * gap)) / 2
    gy0 = y + 8
    entries = SERIES + [("???", "mystery")] * (SLOTS - len(SERIES))
    for i, (kind, rarity) in enumerate(entries):
        cx0, cy0 = gx0 + (i % 3) * (tw + gap), gy0 + (i // 3) * (th + gap)
        col = THEMES.get(rarity, THEMES["regular"])
        rounded(d, (cx0, cy0, cx0 + tw, cy0 + th), 2.5, fill=col[3] + (235,) if rarity != "mystery" else (30, 26, 60, 235),
                outline=(255, 255, 255, 200), width=round(0.35 * MM))
        tcx = cx0 + tw / 2
        if rarity == "mystery":
            draw_sprite(img, sprite_grid(m, "Blip"), px(tcx, 0)[0], px(0, cy0 + 10.5)[1], 15 * MM, silhouette=(14, 10, 30), shadow=False)
            d = ImageDraw.Draw(img)
            text_center(d, tcx, cy0 + 5.5, "?", font(BOLD, 7), (255, 214, 58))
            label, sub = "???", "COMING SOON"
        else:
            draw_sprite(img, sprite_grid(m, kind), px(tcx, 0)[0], px(0, cy0 + 10.5)[1], 15 * MM)
            d = ImageDraw.Draw(img)
            label, sub = kind, "★" * STARS[rarity] + "  " + rarity.upper().replace("-", " ")
        text_center(d, tcx, cy0 + 19.2, label, font(BOLD, 3.0 if len(label) < 11 else 2.5), (255, 255, 255))
        text_center(d, tcx, cy0 + 23.0, sub, font(BOLD, 1.9), (255, 214, 58))
        d.rectangle([*px(cx0 + 1.8, cy0 + 1.8), *px(cx0 + 4.6, cy0 + 4.6)], outline=(255, 255, 255, 230), width=round(0.35 * MM))   # checkbox
    # bios
    by = gy0 + 2 * th + gap + 2.4
    panel = Image.new("RGBA", img.size, (0, 0, 0, 0))                         # a soft dark panel keeps the bios readable
    ImageDraw.Draw(panel).rounded_rectangle([*px(5, by - 1.0), *px(TRIM_W - 5, by + len(SERIES) * 2.8 + 0.4)],
                                            radius=round(2 * MM), fill=(10, 8, 24, 170))
    img.alpha_composite(panel)
    d = ImageDraw.Draw(img)
    f = font(REG, 2.1)
    for i, (kind, _) in enumerate(SERIES):
        text_center(d, TRIM_W / 2, by + i * 2.8, f"{kind}: {BIOS[kind]}", f, (225, 220, 255))
    # code panel
    py0 = by + len(SERIES) * 2.8 + 1.4
    rounded(d, (6, py0, TRIM_W - 6, py0 + 12.5), 3, fill=(255, 214, 58, 245), outline=(60, 30, 10, 255), width=round(0.4 * MM))
    text_center(d, TRIM_W / 2, py0 + 1.4, "FREE IN-GAME BONUS!", font(BOLD, 3.2), (60, 30, 10))
    text_center(d, TRIM_W / 2, py0 + 5.4, "Find the code card inside. Type it in Blipville:", font(REG, 2.2), (60, 30, 10))
    text_center(d, TRIM_W / 2, py0 + 8.6, "? → Secret code   (Windows: right-click a pet)", font(BOLD, 2.2), (60, 30, 10))
    # where to play
    text_center(d, TRIM_W / 2, py0 + 14.3, f"Play free: {SITE}", font(BOLD, 2.5), (255, 255, 255))
    text_center(d, TRIM_W / 2, py0 + 17.6, f"Join the Discord: {DISCORD}", font(REG, 2.2), (225, 220, 255))
    warning(d, 130.5, (255, 255, 255))
    return img


def dieline():
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    (x0, y0), (x1, y1) = px(0, 0), px(TRIM_W, TRIM_H)
    d.rectangle([0, 0, W - 1, H - 1], outline=(0, 160, 255), width=4)                 # bleed edge
    d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=6)                         # cut
    s0, s1 = px(4, 4), px(TRIM_W - 4, TRIM_H - 4)
    d.rectangle([*s0, *s1], outline=(0, 170, 0), width=3)                               # safe area
    hx, hy = px(TRIM_W / 2, 6)
    w2, h2, r = 11 * MM, 2.6 * MM, 2.6 * MM
    d.rounded_rectangle([hx - w2, hy - h2, hx + w2, hy + h2], radius=r, outline=(255, 0, 0), width=6)   # euro hang slot
    rounded(d, (11, 37, 79, 103), 7, outline=(255, 0, 255), width=5)                   # blister bubble
    f = font(BOLD, 2.6)
    for (xm, ym, t, c) in ((TRIM_W / 2, -2.4, "BLEED (3 mm)", (0, 120, 220)), (TRIM_W / 2, 1.0, "CUT", (255, 0, 0)),
                           (TRIM_W / 2, 9.5, "HANG SLOT (cut)", (255, 0, 0)), (TRIM_W / 2, 68, "BLISTER BUBBLE 68 x 66 mm", (200, 0, 200)),
                           (TRIM_W / 2, 136, "SAFE AREA (4 mm)", (0, 140, 0))):
        text_center(d, xm, ym, t, f, c)
    return img


def punch_slot(img):
    """Show where the hang slot will be punched (for previews only)."""
    d = ImageDraw.Draw(img)
    hx, hy = px(TRIM_W / 2, 6)
    w2, h2 = 11 * MM, 2.6 * MM
    d.rounded_rectangle([hx - w2, hy - h2, hx + w2, hy + h2], radius=h2, fill=(29, 26, 46, 255))
    return img


if __name__ == "__main__":
    m = game()
    out = HERE
    previews = []
    for kind, rarity in SERIES:
        f = front(m, kind, rarity)
        name = kind.lower().replace(" ", "_").replace("-", "")
        f.convert("RGB").save(os.path.join(out, f"{name}_front.png"), dpi=(DPI, DPI))
        previews.append(punch_slot(f.copy()))
    b = back(m)
    b.convert("RGB").save(os.path.join(out, "card_back.png"), dpi=(DPI, DPI))
    previews.append(punch_slot(b.copy()))
    dieline().convert("RGB").save(os.path.join(out, "dieline.png"), dpi=(DPI, DPI))
    # one preview sheet (trimmed, scaled down)
    cut = (round(BLEED * MM), round(BLEED * MM), W - round(BLEED * MM), H - round(BLEED * MM))
    tw = 360
    th = round(tw * TRIM_H / TRIM_W)
    cols = 4
    rows = -(-len(previews) // cols)
    sheet = Image.new("RGB", (tw * cols + 10 * (cols + 1), th * rows + 10 * (rows + 1)), (20, 18, 34))
    for i, p in enumerate(previews):
        sheet.paste(p.crop(cut).convert("RGB").resize((tw, th), Image.LANCZOS), (10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 10)))
    sheet.save(os.path.join(out, "cards_preview.png"))
    print("wrote", len(SERIES), "fronts, card_back.png, dieline.png, cards_preview.png")
