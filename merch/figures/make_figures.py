"""🧸 Blip figures (Series 1), built like the Blipville 3D voxel viewer, each on its own display base. Zero supports.

    python3 merch/figures/make_figures.py                   (needs: pip install manifold3d trimesh numpy pillow)
    python3 merch/figures/make_figures.py sprites.json Blip (just one)

The figure is the game sprite (16 x 13 with its feet) turned into chunky voxels, exactly like the 3D viewer: every pixel
is a 2.5 mm cube column, thickest in the middle (8 cubes deep) and thinner toward the edges, the same front and back,
like a plush toy. About 40 x 32 x 20 mm.

A shape like that overhangs whichever way it lies, so it prints as two halves, split down the middle: the front half
(with the eyes and mouth carved in, each eye keeping a raised glint in its corner) and the back half, each lying flat on
its cut face, so every layer is smaller than the one under it. Two small pins line the halves up for gluing.

The base: a rounded plinth with shallow pockets the feet sit in, and the Blip's name and rarity stars engraved along the
front. Glue the feet into the pockets.

Each STL is one print plate: front half, back half, base and 2 alignment pins. PLA, 0.2 mm, 3 walls, 15-20% infill.
"""
import json
import os
import sys

import manifold3d as mf
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
V = 2.5                     # mm per voxel (one sprite pixel)
ROWS, COLS = 13, 16         # 12 body rows + the feet row
MAX_HALF = 4                # half-thickness in voxels (like the viewer: up to 8 cubes deep)
EYE_D, MOUTH_D = 1.2, 1.0   # carved face (mm)
PIN_D, PIN_HOLE, PIN_L, PIN_DEPTH = 3.0, 3.25, 5.4, 3.0   # alignment pins between the halves
SEG = 48
# 🪧 the base
BASE_D, BASE_H = 32.0, 6.0  # depth (front to back) and height; the width follows the figure (at least 46 mm)
BASE_R = 7.0                # corner rounding
SPLIT_Y = 19.0              # where the figure's middle (the split) sits, measured from the base's front edge
POCKET, POCKET_CLR = 1.2, 0.25
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


def layered(cs, height, chamfer=0.9, steps=3, bottom=0.4):
    """Extrude a profile with softened edges: a small 45-degree chamfer on the bed side, rounded-off top edges."""
    parts = [cs.offset(-bottom, mf.JoinType.Round).extrude(bottom + 0.01), cs.extrude(height - chamfer - bottom + 0.01).translate([0, 0, bottom])]
    for i in range(steps):
        a = (i + 1) / steps
        inset = chamfer * (1 - np.sqrt(1 - a * a))
        parts.append(cs.offset(-inset - 0.05, mf.JoinType.Round).extrude(chamfer / steps + (0.02 if i < steps - 1 else 0)).translate([0, 0, height - chamfer + i * chamfer / steps - 0.01]))
    return union(parts)


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


def to_trimesh(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mm.vert_properties)[:, :3], faces=np.asarray(mm.tri_verts))


def grid(sp):
    """The viewer's grid: letters (or None) per cell, 13 rows x 16, feet in the last row."""
    g = [[None] * COLS for _ in range(ROWS)]
    for y, row in enumerate(sp["body"]):
        for x, ch in enumerate(row):
            if ch != ".":
                g[y][x] = ch
    feet = sp.get("feet") or ""
    for x, ch in enumerate(feet):
        xx = x + sp.get("dx", 0)
        if ch != "." and 0 <= xx < COLS:
            g[12][xx] = "f"
    return g


def depth_map(g):
    """Half-thickness in voxels: 1 at the edge, +1 per step inward (4-neighbours), at most MAX_HALF (as in the viewer)."""
    d = [[99 if c else 0 for c in row] for row in g]
    for _ in range(6):
        for y in range(ROWS):
            for x in range(COLS):
                if d[y][x]:
                    n = [d[b][a] if 0 <= a < COLS and 0 <= b < ROWS else 0 for a, b in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))]
                    d[y][x] = min(d[y][x], 1 + min(n))
    return [[min(MAX_HALF, v) for v in row] for row in d]


def face_cells(sp):
    """Eye cells (with the glint cell in each eye's top-left) and mouth cells, as in the viewer."""
    ey, dx = sp["eyes"], sp.get("dx", 0)
    eyes = {(ex + a, ey + b) for ex in (4 + dx, 10 + dx) for a in (0, 1) for b in (0, 1)}
    glint = {(4 + dx, ey), (10 + dx, ey)}
    mouth = {(7 + dx, ey + 4), (8 + dx, ey + 4)} if sp.get("mouth") else set()
    return eyes, glint, mouth


def cell_xy(x, y):
    """Figure coordinates: x across, y up (y = 0 is the bottom of the feet row)."""
    return x * V, (ROWS - 1 - y) * V


def half(sp, front=True):
    """One half of the figure, lying on its cut face (z = 0 .. depth): a height map of voxel columns."""
    g, d = grid(sp), None
    d = depth_map(g)
    eyes, glint, mouth = face_cells(sp)
    e = 0.02
    cubes = []
    for y in range(ROWS):
        for x in range(COLS):
            if not g[y][x]:
                continue
            h = d[y][x] * V
            if front and (x, y) in eyes and (x, y) not in glint:
                h -= EYE_D
            elif front and (x, y) in mouth:
                h -= MOUTH_D
            x0, y0 = cell_xy(x, y)
            cubes.append(box(x0 - e, y0 - e, 0, x0 + V + e, y0 + V + e, h))
    m = union(cubes)
    for hx, hy in pin_spots(sp):
        m = m - mf.Manifold.cylinder(PIN_DEPTH + 1, PIN_HOLE / 2, PIN_HOLE / 2, SEG).translate([hx, hy, -1])
    return m


def pin_spots(sp):
    """Two thick cells far apart for the alignment pins (centres, figure coordinates)."""
    g = grid(sp)
    d = depth_map(g)
    thick = [(x, y) for y in range(ROWS) for x in range(COLS) if d[y][x] >= 3]
    best = max(((a, b) for a in thick for b in thick), key=lambda p: (p[0][0] - p[1][0]) ** 2 + (p[0][1] - p[1][1]) ** 2)
    return [(cell_xy(x, y)[0] + V / 2, cell_xy(x, y)[1] + V / 2) for x, y in best]


def alignment_pin(x0, y0):
    """A short pin, standing up as printed (chamfered both ends)."""
    r = PIN_D / 2
    m = union([mf.Manifold.cylinder(0.41, r - 0.4, r, SEG), mf.Manifold.cylinder(PIN_L - 0.8, r, r, SEG).translate([0, 0, 0.4]),
               mf.Manifold.cylinder(0.41, r, r - 0.4, SEG).translate([0, 0, PIN_L - 0.41])])
    return m.translate([x0, y0, 0])


def footprint(sp):
    """The bottom row's cells as (x0, x1, half-depth) in mm: what the base's pockets hold."""
    g = grid(sp)
    d = depth_map(g)
    low = max(y for y in range(ROWS) if any(g[y]))
    return [(x * V, (x + 1) * V, d[low][x] * V) for x in range(COLS) if g[low][x]]


def base(sp, name, x0=0.0, y0=0.0):
    """The display base, flat on the bed: x across (matching the figure), y from the front edge (0) to the back, z up."""
    w = max(46.0, COLS * V + 8)
    cx = COLS * V / 2
    outline = soften(mf.CrossSection.square([w, BASE_D]).translate([cx - w / 2, 0]), BASE_R)
    plinth = layered(outline, BASE_H, chamfer=1.2, steps=4, bottom=0.6)
    pockets = union([box(a - POCKET_CLR, SPLIT_Y - hd - POCKET_CLR, BASE_H - POCKET, b + POCKET_CLR, SPLIT_Y + hd + POCKET_CLR, BASE_H + 1)
                     for a, b, hd in footprint(sp)])
    stars = STARS.get(sp.get("rarity"), 0)
    label = name.upper() + ("  " + "\u2605" * stars if stars else "")
    front = SPLIT_Y - max(hd for _, _, hd in footprint(sp)) - 1.5     # the strip in front of the feet
    txt = text_cs(label, min(TEXT_H, front - 2.5), w - 2 * BASE_R).translate([cx, front / 2 + 0.3])
    txt = txt.extrude(ENGRAVE + 1).translate([0, 0, BASE_H - ENGRAVE])
    return (plinth - pockets - txt).translate([x0, y0, 0])


def plate(sp, name):
    """Front half and back half (both cut face down; the back half mirrored), base and two pins, side by side."""
    fw = COLS * V
    fr = half(sp, True)
    bk = half(sp, False).mirror([1, 0, 0]).translate([2 * fw + 6, 0, 0])      # mirrored, so it matches once flipped over
    bw = max(46.0, fw + 8)
    bs = base(sp, name, x0=2 * fw + 12 + bw / 2 - fw / 2, y0=0)
    pins = [alignment_pin(2 * fw + 12 + bw + 6, 4 + i * 6) for i in range(2)]
    return [fr, bk, bs] + pins


def assembled(sp, name):
    """For previews: the figure standing on its base (x across, y up, z toward the viewer), base top at y = 0."""
    fr = half(sp, True)
    bk = half(sp, False).mirror([0, 0, 1])
    b = base(sp, name).rotate([-90, 0, 0]).translate([0, -BASE_H, SPLIT_Y])
    sink = POCKET                                                      # the feet sit down in their pockets
    return fr.translate([0, -sink, 0]), bk.translate([0, -sink, 0]), b


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
