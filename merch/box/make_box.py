"""📦 The Series 1 mystery box: cut template, print artwork and a folded 3D model.

    python3 merch/box/make_box.py         (needs: pip install pillow numpy trimesh)

A reverse-tuck-end box, 52 x 52 x 60 mm inside: room for one figure (about 40 x 32 x 20 mm, glued), its base, the code
card and a little crinkle paper. The whole box comes out of one A4 / US Letter sheet (cardstock, 250-300 gsm).

Writes, next to this file:
  box_cut_template.svg   the die line at 1:1 (red = cut, blue dashed = fold), for a cutting machine or a craft knife
  box_print.png          the artwork at 300 dpi on an A4 page, 3 mm bleed, with the cut / fold lines drawn on top
  box_print_clean.png    the same artwork with no lines (for print-then-cut machines; line it up with the SVG)
  box_panels/*.png       each printed face on its own (front, back, sides, top, bottom)
  mystery_box.glb        the folded box as a 3D model with the artwork on it
  box_preview.png        renders of the 3D model
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cards"))
import make_cards as C  # noqa: E402  (sprites, the pixel logo, fonts and colors shared with the cards)

DPI = 300
MM = DPI / 25.4
W, D, H = 52.0, 52.0, 60.0          # inside-ish panel sizes: front/back width, side depth, height
TUCK, GLUE, DUST = 15.0, 12.0, 22.0  # tuck tongue, glue flap, dust flap depth
BLEED = 3.0
PAGE = (297.0, 210.0)                # A4 landscape (also fits US Letter: 279 x 216)
DIE_W, DIE_H = 2 * W + 2 * D + GLUE, H + 2 * (D + TUCK)
OX, OY = (PAGE[0] - DIE_W) / 2, (PAGE[1] - DIE_H) / 2      # die origin on the page
BODY_Y = D + TUCK                    # top of the body panels (die coordinates)
PRICE = "$4.99"
SERIES = [k for k, _ in C.SERIES]
BG_TOP, BG_BOT = (86, 58, 168), (26, 18, 60)
GOLD, INK, WHITE = (255, 214, 58), (40, 22, 70), (255, 255, 255)
QMARK = ["01110", "10001", "00001", "00010", "00100", "00000", "00100"]


def f(path, size_mm):
    return ImageFont.truetype(path, max(8, round(size_mm * MM)))


# ------------------------------------------------------------------ panel artwork (each drawn on its own, with bleed)
class Panel:
    def __init__(self, w_mm, h_mm, seed, bg=(BG_TOP, BG_BOT), stars=True):
        self.w, self.h = w_mm, h_mm
        self.img = Image.new("RGBA", (round((w_mm + 2 * BLEED) * MM), round((h_mm + 2 * BLEED) * MM)))
        d = ImageDraw.Draw(self.img)
        top, bot = bg
        for y in range(self.img.height):
            t = y / (self.img.height - 1)
            d.line([(0, y), (self.img.width, y)], fill=tuple(round(top[i] * (1 - t) + bot[i] * t) for i in range(3)) + (255,))
        if stars:
            import random
            rnd = random.Random(seed)
            for _ in range(int(w_mm * h_mm / 60)):
                x, y = rnd.randrange(self.img.width), rnd.randrange(self.img.height)
                s = rnd.choice((4, 6, 8, 10))
                c = (255, 255, 255, rnd.randrange(70, 200))
                d.rectangle([x, y, x + s, y + s], fill=c)
                if s >= 8:
                    d.rectangle([x - s, y + s // 3, x + 2 * s, y + 2 * s // 3], fill=c)
                    d.rectangle([x + s // 3, y - s, x + 2 * s // 3, y + 2 * s], fill=c)
        self.d = ImageDraw.Draw(self.img)

    def p(self, x, y):
        return round((x + BLEED) * MM), round((y + BLEED) * MM)

    def text(self, x, y, s, font, fill=WHITE, anchor="mt", stroke=0, stroke_fill=INK):
        self.d.text(self.p(x, y), s, font=font, fill=fill, anchor=anchor, stroke_width=round(stroke * MM), stroke_fill=stroke_fill)

    def rrect(self, x0, y0, x1, y1, r, **kw):
        self.d.rounded_rectangle([*self.p(x0, y0), *self.p(x1, y1)], radius=round(r * MM), **kw)

    def sprite(self, g, cx, cy, size_mm, silhouette=None, shadow=True):
        x, y = self.p(cx, cy)
        C.draw_sprite(self.img, g, x, y, size_mm * MM, silhouette=silhouette, shadow=shadow)
        self.d = ImageDraw.Draw(self.img)

    def chrome_sprite(self, g, cx, cy, size_mm):
        """The sprite in shiny chrome: its own shading turned to silver, with a diagonal sheen across it."""
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        x, y = self.p(cx, cy)
        C.draw_sprite(layer, g, x, y, size_mm * MM, shadow=False)
        rgb, alpha = layer.convert("RGB"), layer.getchannel("A")
        lum = np.asarray(rgb.convert("L"), float) / 255
        h, w = lum.shape
        yy, xx = np.mgrid[0:h, 0:w]
        sheen = 0.5 + 0.5 * np.sin((xx + yy) / (size_mm * MM / 16 * 3.0))
        v = np.clip(70 + 150 * lum ** 0.7 + 55 * sheen, 0, 255)
        silver = np.dstack([v, v, np.clip(v + 14, 0, 255), np.asarray(alpha)]).astype(np.uint8)
        self.img.alpha_composite(Image.fromarray(silver, "RGBA"))
        self.d = ImageDraw.Draw(self.img)

    def qmark(self, cx, cy, h_mm, color, glow=None):
        u = h_mm * MM / 7
        x0, y0 = self.p(cx, cy)[0] - 2.5 * u, self.p(cx, cy)[1] - 3.5 * u
        if glow:
            gl = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
            gd = ImageDraw.Draw(gl)
            for y, row in enumerate(QMARK):
                for x, b in enumerate(row):
                    if b == "1":
                        gd.rectangle([x0 + x * u - u * .4, y0 + y * u - u * .4, x0 + (x + 1) * u + u * .4, y0 + (y + 1) * u + u * .4], fill=glow)
            self.img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(u * 0.9)))
            self.d = ImageDraw.Draw(self.img)
        for y, row in enumerate(QMARK):
            for x, b in enumerate(row):
                if b == "1":
                    self.d.rectangle([round(x0 + x * u), round(y0 + y * u), round(x0 + (x + 1) * u) - 1, round(y0 + (y + 1) * u) - 1], fill=color)

    def logo(self, cx, top, width):
        text = "BLIPVILLE"
        cells = len(text) * 6 - 1
        u = width * MM / cells
        x0 = self.p(cx, 0)[0] - cells * u / 2
        y0 = self.p(0, top)[1]
        for grow, col in ((u * 0.45, INK), (0, WHITE)):
            for i, ch in enumerate(text):
                for gy, row in enumerate(C.GLYPHS[ch]):
                    for gx, bit in enumerate(row):
                        if bit == "1":
                            X, Y = x0 + (i * 6 + gx) * u, y0 + gy * u
                            self.d.rectangle([X - grow, Y - grow, X + u + grow - 1, Y + u + grow - 1], fill=col)
        return top + 7 * u / MM

    def burst(self, cx, cy, r, text, fill=GOLD, ink=INK, size=None):
        x, y = self.p(cx, cy)
        R, rr = r * MM, r * MM * 0.74
        pts = [(x + (R if i % 2 == 0 else rr) * math.cos(math.pi * i / 12 - math.pi / 2),
                y + (R if i % 2 == 0 else rr) * math.sin(math.pi * i / 12 - math.pi / 2)) for i in range(24)]
        self.d.polygon(pts, fill=fill, outline=ink, width=round(0.4 * MM))
        lines = text.split("\n")
        fo = f(C.BOLD, size or r * 0.3)
        for i, line in enumerate(lines):
            self.d.text((x, y + (i - (len(lines) - 1) / 2) * (size or r * 0.3) * 1.15 * MM), line, font=fo, fill=ink, anchor="mm")

    def trimmed(self):
        b = round(BLEED * MM)
        return self.img.crop((b, b, self.img.width - b, self.img.height - b))


def front_panel(m, grids):
    p = Panel(W, H, 1)
    p.logo(W / 2, 4.0, W - 10)
    p.text(W / 2, 11.5, f"SERIES {C.SERIES_NO} \u00b7 {C.SERIES_NAME.upper()}", f(C.BOLD, 2.4), fill=(225, 215, 255))
    # the mystery Blip: a dark silhouette with a glowing ? in front of it
    p.sprite(grids["Blip"], W / 2, 31, 36, silhouette=(14, 8, 32))
    p.qmark(W / 2, 30, 15, GOLD, glow=(255, 214, 58, 200))
    p.rrect(4, 44, W - 4, 53, 2.5, fill=GOLD, outline=INK, width=round(0.4 * MM))
    p.text(W / 2, 45.2, "MYSTERY BLIP", f(C.BOLD, 5.2), fill=INK)
    p.text(W / 2, 54.6, "1 random figure + display base inside", f(C.BOLD, 2.1), fill=WHITE)
    p.burst(W - 8.0, 22.5, 6.6, "CHROME\nCHASE!", fill=(220, 228, 245), size=1.9)
    return p


def lineup_panel(m, grids):
    p = Panel(D, H, 2)
    p.text(D / 2, 4.0, "COLLECT ALL 6!", f(C.BOLD, 4.4), fill=GOLD, stroke=0.35)
    for i, k in enumerate(SERIES):
        cx, cy = 13 + (i % 2) * 26, 17 + (i // 2) * 14.5
        p.rrect(cx - 11.5, cy - 6.2, cx + 11.5, cy + 6.8, 2, fill=(40, 28, 84), outline=(150, 130, 240), width=round(0.25 * MM))
        p.sprite(grids[k], cx, cy - 1.2, 11, silhouette=(14, 8, 32), shadow=False)
        p.text(cx, cy + 3.6, k, f(C.BOLD, 1.9), fill=WHITE)
    p.text(D / 2, 56.0, "Which one will you get?", f(C.BOLD, 2.2), fill=(225, 215, 255))
    return p


def chrome_panel(m, grids):
    p = Panel(D, H, 3)
    p.text(D / 2, 4.0, "FIND A CHROME!", f(C.BOLD, 4.4), fill=(230, 236, 250), stroke=0.35)
    p.chrome_sprite(grids["Silvertear-03"], D / 2, 24, 30)
    for sx, sy in ((10, 14), (42, 18), (38, 33)):
        x, y = p.p(sx, sy)
        r = 1.6 * MM
        p.d.polygon([(x, y - r), (x + r * .25, y - r * .25), (x + r, y), (x + r * .25, y + r * .25), (x, y + r), (x - r * .25, y + r * .25),
                     (x - r, y), (x - r * .25, y - r * .25)], fill=WHITE)
    p.text(D / 2, 37.5, "Every Blip comes in", f(C.BOLD, 2.5))
    p.text(D / 2, 41.0, "BASIC or SHINY CHROME", f(C.BOLD, 2.9), fill=GOLD)
    p.rrect(4, 46, D - 4, 57, 2, fill=(20, 12, 46), outline=(150, 130, 240), width=round(0.25 * MM))
    p.text(D / 2, 47.4, "Each figure: 1 in 6", f(C.BOLD, 2.3))
    p.text(D / 2, 51.4, "Chrome finish: 2 in 5", f(C.BOLD, 2.3), fill=(220, 228, 245))
    return p


def back_panel(m, grids):
    p = Panel(W, H, 4)
    p.text(W / 2, 3.0, "CHECKLIST", f(C.BOLD, 4.0), fill=GOLD, stroke=0.3)
    p.text(W / 2 + 9.5, 9.0, "BASIC", f(C.BOLD, 1.7), fill=(225, 215, 255))
    p.text(W / 2 + 17.5, 9.0, "CHROME", f(C.BOLD, 1.7), fill=(225, 215, 255))
    for i, k in enumerate(SERIES):
        y = 12.0 + i * 5.6
        p.sprite(grids[k], 6.5, y + 2.0, 4.6, shadow=False)
        p.text(10.5, y + 2.0, k, f(C.BOLD, 2.3), anchor="lm")
        for bx in (W / 2 + 9.5, W / 2 + 17.5):
            p.rrect(bx - 1.6, y + 0.4, bx + 1.6, y + 3.6, 0.5, outline=WHITE, width=round(0.25 * MM))
    p.rrect(3, 46, W - 3, 57.5, 2.2, fill=GOLD, outline=INK, width=round(0.35 * MM))
    p.text(W / 2, 47.1, "FREE IN-GAME COLOR!", f(C.BOLD, 2.6), fill=INK)
    p.text(W / 2, 50.6, "Code card inside: type it in Blipville", f(C.REG, 1.75), fill=INK)
    p.text(W / 2, 53.4, "? → Secret code (Windows: right-click a pet)", f(C.REG, 1.75), fill=INK)
    return p


def top_panel(m, grids):
    p = Panel(W, D, 5)
    p.qmark(W / 2, D / 2 - 4, 22, GOLD, glow=(255, 214, 58, 190))
    p.text(W / 2, D - 12, "OPEN HERE ▲", f(C.BOLD, 3.2), fill=WHITE)
    p.text(W / 2, D - 7.5, "Don't peek!", f(C.BOLD, 2.2), fill=(225, 215, 255))
    return p


def bottom_panel(m, grids):
    p = Panel(W, D, 6)
    p.logo(W / 2, 4, W - 18)
    lines = [(C.SERIES_LABEL, C.BOLD, 2.4, WHITE), (f"{PRICE}", C.BOLD, 5.0, GOLD),
             ("Contains: 1 random figure,", C.REG, 2.1, WHITE), ("display base and a code card.", C.REG, 2.1, WHITE),
             ("Each figure 1 in 6 · Chrome 2 in 5", C.BOLD, 2.0, (220, 228, 245)),
             (C.SITE, C.REG, 1.9, (200, 190, 255)), (C.DISCORD, C.REG, 1.9, (200, 190, 255)),
             ("⚠ CHOKING HAZARD — Small parts.", C.BOLD, 1.9, GOLD), ("Not for children under 3 years.", C.REG, 1.9, GOLD)]
    y = 12.5
    for s, fp, sz, col in lines:
        p.text(W / 2, y, s, f(fp, sz), fill=col)
        y += sz * 1.35 + 0.6
    return p


def plain_panel(w, h, seed):
    return Panel(w, h, seed, bg=((60, 40, 120), (40, 26, 90)), stars=False)


# ------------------------------------------------------------------ die line (die coordinates: mm, origin top-left)
def panels_layout():
    """(name, x, y, w, h, rotate_180) for every printed area of the die."""
    xs = {"front": 0.0, "right": W, "back": W + D, "left": 2 * W + D}
    return [("front", xs["front"], BODY_Y, W, H, False), ("right", xs["right"], BODY_Y, D, H, False),
            ("back", xs["back"], BODY_Y, W, H, False), ("left", xs["left"], BODY_Y, D, H, False),
            ("top", xs["back"], TUCK, W, D, True), ("bottom", xs["front"], BODY_Y + H, W, D, True)]


def die_paths():
    """Cut outline (one closed polygon) and fold lines, in die mm."""
    xb, xr, xk, xl, xg = 0.0, W, W + D, 2 * W + D, 2 * W + 2 * D
    y0, y1 = BODY_Y, BODY_Y + H
    ch = 3.0
    cut = []
    # start top-left of the front panel and go clockwise
    cut += [(xb, y0), (xr + 1.0, y0)]
    cut += [(xr + 1.0, y0 - DUST + 6), (xr + 7, y0 - DUST), (xk - 3, y0 - DUST), (xk - 0.5, y0 - 4), (xk, y0)]        # right dust flap (top)
    cut += [(xk, y0 - D), (xk, y0 - D - TUCK + ch), (xk + ch, y0 - D - TUCK), (xl - ch, y0 - D - TUCK), (xl, y0 - D - TUCK + ch), (xl, y0 - D)]  # top lid + tuck
    cut += [(xl, y0), (xl + 0.5, y0 - 4), (xl + 3, y0 - DUST), (xg - 7, y0 - DUST), (xg - 1.0, y0 - DUST + 6), (xg - 1.0, y0)]  # left dust flap (top)
    cut += [(xg, y0), (xg + GLUE, y0 + 6), (xg + GLUE, y1 - 6), (xg, y1)]                                             # glue flap
    cut += [(xg - 1.0, y1), (xg - 1.0, y1 + DUST - 6), (xg - 7, y1 + DUST), (xl + 3, y1 + DUST), (xl + 0.5, y1 + 4), (xl, y1)]   # left dust (bottom)
    cut += [(xk, y1), (xk - 0.5, y1 + 4), (xk - 3, y1 + DUST), (xr + 7, y1 + DUST), (xr + 1.0, y1 + DUST - 6), (xr + 1.0, y1)]  # right dust (bottom)
    cut += [(xr, y1), (xr, y1 + D), (xr, y1 + D + TUCK - ch), (xr - ch, y1 + D + TUCK), (xb + ch, y1 + D + TUCK), (xb, y1 + D + TUCK - ch), (xb, y1 + D)]  # bottom lid + tuck
    cut += [(xb, y1)]
    folds = [((xr, y0), (xr, y1)), ((xk, y0), (xk, y1)), ((xl, y0), (xl, y1)), ((xg, y0), (xg, y1)),       # body corners + glue
             ((xr, y0), (xk, y0)), ((xl, y0), (xg, y0)), ((xk, y0), (xl, y0)), ((xk, y0 - D), (xl, y0 - D)),   # top: dust, lid, tuck
             ((xr, y1), (xk, y1)), ((xl, y1), (xg, y1)), ((xb, y1), (xr, y1)), ((xb, y1 + D), (xr, y1 + D))]    # bottom
    return cut, folds


def svg(path):
    cut, folds = die_paths()
    pts = " ".join(f"{OX + x:.2f},{OY + y:.2f}" for x, y in cut)
    lines = "\n".join(f'  <line x1="{OX + a[0]:.2f}" y1="{OY + a[1]:.2f}" x2="{OX + b[0]:.2f}" y2="{OY + b[1]:.2f}" class="fold"/>' for a, b in folds)
    labels = [("FRONT", 0, BODY_Y, W, H), ("SIDE", W, BODY_Y, D, H), ("BACK", W + D, BODY_Y, W, H), ("SIDE", 2 * W + D, BODY_Y, D, H),
              ("TOP LID", W + D, TUCK, W, D), ("BOTTOM LID", 0, BODY_Y + H, W, D), ("GLUE", 2 * W + 2 * D, BODY_Y, GLUE, H)]
    texts = "\n".join(f'  <text x="{OX + x + w / 2:.2f}" y="{OY + y + h / 2:.2f}" class="lbl">{t}</text>' for t, x, y, w, h in labels)
    open(path, "w").write(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE[0]}mm" height="{PAGE[1]}mm" viewBox="0 0 {PAGE[0]} {PAGE[1]}">
  <title>Blipville mystery box: cut template (52 x 52 x 60 mm)</title>
  <style>.cut{{fill:none;stroke:#e0002a;stroke-width:0.3}} .fold{{stroke:#1060ff;stroke-width:0.3;stroke-dasharray:2 1.2}}
         .lbl{{font:bold 4px sans-serif;fill:#9aa0b0;text-anchor:middle;dominant-baseline:middle}}</style>
  <polygon class="cut" points="{pts}"/>
{lines}
{texts}
  <text x="{OX}" y="{PAGE[1] - 3}" style="font:3px sans-serif;fill:#666">Red = cut, blue dashed = fold (score first). Print at 100% (no scaling). Glue the flap inside the front panel's edge.</text>
</svg>
''')


def main():
    m = C.game()
    grids = {k: C.sprite_grid(m, k) for k in SERIES}
    made = {"front": front_panel(m, grids), "right": lineup_panel(m, grids), "back": back_panel(m, grids),
            "left": chrome_panel(m, grids), "top": top_panel(m, grids), "bottom": bottom_panel(m, grids)}
    os.makedirs(os.path.join(HERE, "box_panels"), exist_ok=True)
    for k, pnl in made.items():
        pnl.trimmed().convert("RGB").save(os.path.join(HERE, "box_panels", f"{k}.png"))
    # the print sheet: a plain inside color under everything (dust flaps, tucks, glue flap), then each panel with bleed
    page = Image.new("RGBA", (round(PAGE[0] * MM), round(PAGE[1] * MM)), (255, 255, 255, 255))
    cut, folds = die_paths()
    shape = Image.new("L", page.size, 0)
    ImageDraw.Draw(shape).polygon([((OX + x) * MM, (OY + y) * MM) for x, y in cut], fill=255)
    shape = shape.filter(ImageFilter.MaxFilter(2 * round(BLEED * MM / 2) + 1))         # bleed past the cut line
    page.paste((52, 34, 104, 255), (0, 0), shape)
    for trimmed in (False, True):                 # bleed first (it only shows past the cut), then each panel's own area
        for name, x, y, w, h, rot in panels_layout():
            im = made[name].trimmed() if trimmed else made[name].img
            if rot:
                im = im.rotate(180)
            off = 0 if trimmed else BLEED
            page.alpha_composite(im, (round((OX + x - off) * MM), round((OY + y - off) * MM)))
    page.convert("RGB").save(os.path.join(HERE, "box_print_clean.png"), dpi=(DPI, DPI))
    marked = page.copy()
    dd = ImageDraw.Draw(marked)
    dd.line([((OX + x) * MM, (OY + y) * MM) for x, y in cut + cut[:1]], fill=(230, 0, 40, 255), width=4)
    for a, b in folds:
        (ax, ay), (bx, by) = a, b
        n = max(1, int(math.hypot(bx - ax, by - ay) / 3.2))
        for i in range(n):
            t0, t1 = i / n, (i + 0.6) / n
            dd.line([((OX + ax + (bx - ax) * t0) * MM, (OY + ay + (by - ay) * t0) * MM),
                     ((OX + ax + (bx - ax) * t1) * MM, (OY + ay + (by - ay) * t1) * MM)], fill=(16, 96, 255, 255), width=4)
    dd.text((OX * MM, (PAGE[1] - 4) * MM), "Print at 100% on 250-300 gsm card. Red = cut, blue dashed = fold. Blipville mystery box, 52 x 52 x 60 mm.",
            font=f(C.REG, 2.6), fill=(90, 90, 110, 255))
    marked.convert("RGB").save(os.path.join(HERE, "box_print.png"), dpi=(DPI, DPI))
    svg(os.path.join(HERE, "box_cut_template.svg"))
    model(made)
    print("wrote box_cut_template.svg, box_print.png, box_print_clean.png, box_panels/, mystery_box.glb")


# ------------------------------------------------------------------ the folded box in 3D
def model(made):
    import trimesh
    from trimesh.visual import TextureVisuals
    from trimesh.visual.material import PBRMaterial
    scene = trimesh.Scene()
    # (panel, corners in mm: bottom-left, bottom-right, top-right, top-left as seen from outside); y up, z toward the viewer
    x0, x1, z0, z1 = -W / 2, W / 2, -D / 2, D / 2
    faces = {
        "front": [(x0, 0, z1), (x1, 0, z1), (x1, H, z1), (x0, H, z1)],
        "right": [(x1, 0, z1), (x1, 0, z0), (x1, H, z0), (x1, H, z1)],
        "back": [(x1, 0, z0), (x0, 0, z0), (x0, H, z0), (x1, H, z0)],
        "left": [(x0, 0, z0), (x0, 0, z1), (x0, H, z1), (x0, H, z0)],
        "top": [(x0, H, z1), (x1, H, z1), (x1, H, z0), (x0, H, z0)],
        "bottom": [(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1)],
    }
    for name, quad in faces.items():
        tex = made[name].trimmed().convert("RGB")
        tex = tex.resize((tex.width // 2, tex.height // 2), Image.LANCZOS)
        mesh = trimesh.Trimesh(vertices=np.array(quad, float), faces=[[0, 1, 2], [0, 2, 3]], process=False)
        mesh.visual = TextureVisuals(uv=np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float),
                                     material=PBRMaterial(baseColorTexture=tex, metallicFactor=0.0, roughnessFactor=0.8))
        scene.add_geometry(mesh, geom_name=name)
    scene.apply_translation([0, -H / 2, 0])
    scene.export(os.path.join(HERE, "mystery_box.glb"))


if __name__ == "__main__":
    main()
