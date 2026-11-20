"""🧸 Blip figures (Series 1), built straight from the game sprites, each on its own display base. Zero supports.

    python3 merch/figures/make_figures.py                   (needs: pip install manifold3d trimesh numpy scipy pillow)
    python3 merch/figures/make_figures.py sprites.json Blip (just one)

Each STL is one print plate with two parts: the figure lying on its back (face up) and its base.

* Figure: the Blip's whole 16 x 12 game sprite, 2.5 mm per pixel (about 40 x 30 x 16 mm), as a soft vinyl-toy shape: the
  outline keeps the pixel silhouette (with slightly rounded corners) and the front swells into a smooth rounded dome. The
  sprite's details are carved into the dome: eyes and mouth sunk in, darker patches and inner outlines sunk a little,
  light patches (bellies, teeth, highlights) raised a little, visors recessed with the eyes glowing out of them. Nothing
  overhangs. A teardrop-shaped hole in its bottom (pointed toward the front, so it prints cleanly) fits the base's peg.
* Base: a rounded plinth with the Blip's name and its rarity stars engraved in the front. A matching teardrop peg holds
  the figure upright and facing forward (it can't spin). Snug fit; a drop of glue makes it permanent.
* Print in PLA at 0.2 mm, 3 walls, 15-20% infill.
"""
import json
import os
import sys

import manifold3d as mf
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PX = 2.5                    # mm per sprite pixel
SUB = 10                    # height-field cells per pixel (0.25 mm)
T0, DOME, DOME_R = 9.5, 6.0, 7.0   # body thickness at the outline, extra height in the middle, how far in it reaches full height
ROUND = 0.6                 # silhouette corner rounding
EYE, MOUTH, DARK, LIGHT, VISOR = 1.6, 1.2, 0.7, 0.45, 1.2   # relief depths (mm)
SEG = 48
# 🪧 the base
BASE_D, BASE_H = 30.0, 6.0  # depth (front to back) and height; the width follows the figure (at least 46 mm)
BASE_R = 7.0                # corner rounding
BACK = 3.0                  # the figure's back stands this far in from the base's back edge
PEG_D, HOLE_D = 5.0, 5.3    # teardrop peg and the hole in the figure's bottom
PEG_L, HOLE_L = 6.0, 6.8
HOLE_Z = 4.6                # the hole's centre, in from the figure's back (inside the thin outline: the tip stays inside)
TEXT_H, ENGRAVE = 6.0, 0.8  # name lettering height and depth
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
STARS = {"ultra-rare": 3, "rare": 2, "regular": 1}


def box(x0, y0, z0, x1, y1, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def union(parts):
    return mf.Manifold.batch_boolean(parts, mf.OpType.Add) if parts else mf.Manifold()


def rects_cs(mask, x0, y0, cell):
    """A CrossSection covering the True cells of a 2D mask (row 0 = top), cell size `cell`, top-left corner (x0, y0)."""
    polys = []
    rows, cols = mask.shape
    for r in range(rows):
        c = 0
        while c < cols:
            if mask[r, c]:
                s = c
                while c < cols and mask[r, c]:
                    c += 1
                xa, xb = x0 + s * cell, x0 + c * cell
                yb, ya = y0 - r * cell, y0 - (r + 1) * cell
                polys.append([(xa, ya), (xb, ya), (xb, yb), (xa, yb)])
            else:
                c += 1
    if not polys:
        return mf.CrossSection()
    return mf.CrossSection(polys, mf.FillRule.Positive)


def soften(cs, r):
    return cs.offset(-r, mf.JoinType.Round).offset(r, mf.JoinType.Round).offset(r, mf.JoinType.Round).offset(-r, mf.JoinType.Round)


def _along_x(cs, x0, x1):
    """A CrossSection drawn in (y, z) -> a prism along X from x0 to x1."""
    mesh = cs.extrude(x1 - x0).to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].copy()
    v = np.stack([v[:, 2] + x0, v[:, 0], v[:, 1]], axis=1)
    tri = np.asarray(mesh.tri_verts)
    m = mf.Manifold(mf.Mesh(vert_properties=v.astype(np.float32), tri_verts=tri.astype(np.uint32)))
    return m if m.volume() > 0 else mf.Manifold(mf.Mesh(vert_properties=v.astype(np.float32), tri_verts=tri[:, ::-1].astype(np.uint32)))


def teardrop_cs(cy, cz, d):
    """Round at the bottom, pointed on top (+Z), so a sideways hole prints without supports."""
    r = d / 2
    pts = [(cy + r * np.cos(a), cz + r * np.sin(a)) for a in np.linspace(3 * np.pi / 4, 2 * np.pi + np.pi / 4, 40)]
    pts.append((cy, cz + r * np.sqrt(2)))
    return mf.CrossSection([pts])


def lum(hexcol):
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.3 * r + 0.59 * g + 0.11 * b


def relief_map(sprite, rows):
    """Per-pixel height change (mm) from the sprite's details."""
    pal = sprite.get("colors", {})
    letters = [ch.lower() for row in rows for ch in row if ch not in ".o*"]
    main = max(set(letters), key=letters.count) if letters else "b"
    base = lum(pal.get(main, "#888888"))
    ey, dx = sprite["eyes"], sprite.get("dx", 0)
    eyes = {(ey + b, ex + a + dx) for ex in (4, 10) for a in (0, 1) for b in (0, 1)}
    mouth = {(ey + 4, 7 + dx), (ey + 4, 8 + dx)} if sprite.get("mouth") else set()
    visor = any("v" in r for r in rows)
    n, w = len(rows), 16
    filled = np.array([[ch != "." for ch in row] for row in rows])
    rel = np.zeros((n, w))
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            edge = any(not (0 <= r + i < n and 0 <= c + j < w and filled[r + i, c + j]) for i in (-1, 0, 1) for j in (-1, 0, 1))
            if (r, c) in eyes:
                rel[r, c] = 0.0 if visor else -EYE           # a visor's eyes glow out of it
            elif (r, c) in mouth:
                rel[r, c] = -MOUTH
            elif ch == "v":
                rel[r, c] = -VISOR
            elif ch == "o":
                rel[r, c] = 0.0 if edge else -DARK               # outlines inside the shape become grooves
            elif ch == "*":
                rel[r, c] = LIGHT
            else:
                col = pal.get(ch.lower())
                if col and ch.lower() != main:
                    d = lum(col) - base
                    rel[r, c] = LIGHT if d > 40 else -DARK if d < -40 else 0.0
    return rel


def _no_corner_touch(m):
    """Fill one cell wherever two filled cells touch only at a corner (keeps the mesh a clean solid)."""
    m = m.copy()
    changed = True
    while changed:
        changed = False
        a, b, c, d = m[:-1, :-1], m[:-1, 1:], m[1:, :-1], m[1:, 1:]
        for r, cc in zip(*np.where(a & d & ~b & ~c)):
            m[r, cc + 1] = True
            changed = True
        for r, cc in zip(*np.where(b & c & ~a & ~d)):
            m[r, cc] = True
            changed = True
    return m


def heightfield(mask, h, x0, y0, cell):
    """A closed solid: flat bottom at z = 0, vertical walls round the mask, and a smooth top whose corners take the
    lowest height of the cells around them (so sunk details stay crisp). Row 0 of the mask is the top (y0)."""
    R, C = mask.shape
    hp = np.where(mask, h, np.inf)
    pad = np.pad(hp, 1, constant_values=np.inf)
    corner = np.minimum(np.minimum(pad[:-1, :-1], pad[:-1, 1:]), np.minimum(pad[1:, :-1], pad[1:, 1:]))   # (R+1, C+1)
    vid, verts = {}, []

    def v(r, c, top):
        key = (r, c, top)
        if key not in vid:
            vid[key] = len(verts)
            verts.append((x0 + c * cell, y0 - r * cell, corner[r, c] if top else 0.0))
        return vid[key]
    faces = []
    for r, c in zip(*np.where(mask)):
        a, b, cc, d = (r, c), (r, c + 1), (r + 1, c + 1), (r + 1, c)     # tl, tr, br, bl (y goes down with r)
        faces += [(v(*a, 1), v(*d, 1), v(*cc, 1)), (v(*a, 1), v(*cc, 1), v(*b, 1))]           # top, facing +z
        faces += [(v(*a, 0), v(*cc, 0), v(*d, 0)), (v(*a, 0), v(*b, 0), v(*cc, 0))]           # bottom, facing -z
        for (p, q), (dr, dc) in (((a, b), (-1, 0)), ((b, cc), (0, 1)), ((cc, d), (1, 0)), ((d, a), (0, -1))):
            rr, c2 = r + dr, c + dc
            if 0 <= rr < R and 0 <= c2 < C and mask[rr, c2]:
                continue
            faces += [(v(*p, 0), v(*q, 1), v(*q, 0)), (v(*p, 0), v(*p, 1), v(*q, 1))]
    V = np.array(verts, np.float32)
    Fc = np.array(faces, np.uint32)
    m = mf.Manifold(mf.Mesh(vert_properties=V, tri_verts=Fc))
    if m.volume() < 0 or m.is_empty():
        m = mf.Manifold(mf.Mesh(vert_properties=V, tri_verts=Fc[:, ::-1].copy()))
    return m


def layered(cs, height, chamfer=0.9, steps=3, bottom=0.4):
    """Extrude a profile with softened edges: a small 45-degree chamfer on the bed side, rounded-off top edges."""
    parts = [cs.offset(-bottom, mf.JoinType.Round).extrude(bottom + 0.01), cs.extrude(height - chamfer - bottom + 0.01).translate([0, 0, bottom])]
    for i in range(steps):
        a = (i + 1) / steps
        inset = chamfer * (1 - np.sqrt(1 - a * a))
        parts.append(cs.offset(-inset - 0.05, mf.JoinType.Round).extrude(chamfer / steps + (0.02 if i < steps - 1 else 0)).translate([0, 0, height - chamfer + i * chamfer / steps - 0.01]))
    return union(parts)


def to_trimesh(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mm.vert_properties)[:, :3], faces=np.asarray(mm.tri_verts))


def _along_y(cs, y0, y1):
    """A CrossSection drawn in (x, z) -> a prism along Y from y0 to y1."""
    mesh = cs.extrude(y1 - y0).to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].copy()
    v = np.stack([v[:, 0], v[:, 2] + y0, v[:, 1]], axis=1)
    tri = np.asarray(mesh.tri_verts)
    m = mf.Manifold(mf.Mesh(vert_properties=v.astype(np.float32), tri_verts=tri.astype(np.uint32)))
    return m if m.volume() > 0 else mf.Manifold(mf.Mesh(vert_properties=v.astype(np.float32), tri_verts=tri[:, ::-1].astype(np.uint32)))


def hole_x(rows):
    """Where the base's peg goes: the middle of the widest solid stretch of the sprite's bottom 3 rows."""
    solid = np.all([[ch != "." for ch in row] for row in rows[-3:]], axis=0)
    best, run, start = (0, 0), 0, 0
    for c in range(17):
        if c < 16 and solid[c]:
            run, start = run + 1, (start if run else c)
        else:
            if run > best[0]:
                best = (run, start)
            run = 0
    if best[0] < 3:
        raise ValueError("no room for the stand peg in the bottom rows")
    return (best[1] + best[0] / 2) * PX


def body(sprite):
    """The figure, lying face up as printed: x across, y up (y = 0 is its bottom), z out of its face."""
    rows = list(sprite["body"])
    n = len(rows)
    top_y = n * PX
    keep = np.array([[ch != "." for ch in row] for row in rows])
    rel = relief_map(sprite, rows)
    fine = _no_corner_touch(np.kron(keep, np.ones((SUB, SUB), bool)))
    cell = PX / SUB
    dist = ndimage.distance_transform_edt(np.pad(fine, 1))[1:-1, 1:-1] * cell - cell / 2
    t = np.clip(dist / DOME_R, 0, 1)
    h = T0 + DOME * np.sqrt(1 - (1 - t) ** 2) + np.kron(rel, np.ones((SUB, SUB)))
    fig = heightfield(fine, h, 0, top_y, cell) ^ soften(rects_cs(keep, 0, top_y, PX), ROUND).extrude(40)
    hx = hole_x(rows)
    hole = _along_y(teardrop_cs(hx, HOLE_Z, HOLE_D), -1, HOLE_L)        # pointed toward the face (up, as it prints)
    return fig - hole, hx


def text_cs(text, height, max_w):
    """Lettering as a CrossSection (cut from a high-res render), centred on (0, 0), at most max_w wide."""
    font = ImageFont.truetype(FONT, 120)
    x0, y0, x1, y1 = font.getbbox(text)
    img = Image.new("L", (x1 - x0 + 8, y1 - y0 + 8), 0)
    ImageDraw.Draw(img).text((4 - x0, 4 - y0), text, fill=255, font=font)
    a = _no_corner_touch(np.asarray(img)[::3, ::3] > 127)              # 40 px tall is plenty for a 5 mm line
    cell = min(height / a.shape[0], max_w / a.shape[1])
    cs = rects_cs(a, 0, 0, cell)
    return cs.translate([-a.shape[1] * cell / 2, a.shape[0] * cell / 2])


def base(sprite, name, hx, fig_w, x0=0.0, y0=0.0):
    """The display base, flat on the bed: x across (matching the figure), y from the front edge (0) to the back (BASE_D),
    z up. The peg stands up at the figure's hole; the name and stars are engraved along the front."""
    w = max(46.0, fig_w + 8)
    cx = fig_w / 2
    outline = soften(mf.CrossSection.square([w, BASE_D]).translate([cx - w / 2, 0]), BASE_R)
    plinth = layered(outline, BASE_H, chamfer=1.2, steps=4, bottom=0.6)
    # the peg: the hole's teardrop, a little smaller, pointing toward the front (-y)
    py = BASE_D - BACK - HOLE_Z
    r = PEG_D / 2
    pts = [(hx + r * np.cos(a), py - r * np.sin(a)) for a in np.linspace(3 * np.pi / 4, 2 * np.pi + np.pi / 4, 40)]
    pts.append((hx, py - r * np.sqrt(2)))
    peg_cs = mf.CrossSection([pts], mf.FillRule.NonZero)
    peg = peg_cs.extrude(PEG_L - 0.6 + 1.0).translate([0, 0, BASE_H - 1.0]) + \
        peg_cs.offset(-0.5, mf.JoinType.Round).extrude(0.61).translate([0, 0, BASE_H + PEG_L - 0.6 - 0.01])
    stars = STARS.get(sprite.get("rarity"), 0)
    label = name.upper() + ("  " + "★" * stars if stars else "")
    front = BASE_D - BACK - 17.0                                        # the strip in front of the figure
    txt = text_cs(label, TEXT_H, w - 2 * BASE_R).translate([cx, front / 2 + 0.6]).extrude(ENGRAVE + 1).translate([0, 0, BASE_H - ENGRAVE])
    return (plinth + peg - txt).translate([x0, y0, 0])


def plate(sprite, name):
    fig, hx = body(sprite)
    fig_w = 16 * PX
    return [fig, base(sprite, name, hx, fig_w, x0=fig_w + 8 + max(46.0, fig_w + 8) / 2 - fig_w / 2, y0=0)]


if __name__ == "__main__":
    sprites = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "sprites.json")))
    only = sys.argv[2:] or None
    for name, sp in sprites.items():
        if only and name not in only:
            continue
        t = to_trimesh(union(plate(sp, name)))
        keep = [c for c in t.split(only_watertight=False) if abs(c.volume) > 1.0]   # drop zero-volume slivers
        t = trimesh.util.concatenate(keep)
        path = os.path.join(HERE, name.lower().replace(" ", "_").replace("-", "") + "_figure.stl")
        t.export(path)
        print(f"{name + ' (' + sp.get('rarity', 'extra') + ')':28} {os.path.basename(path)}  plate {np.round(t.extents, 1).tolist()} mm  "
              f"watertight={t.is_watertight}  parts={len(keep)}")
