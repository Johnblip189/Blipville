"""🧸 Posable Blip figures (Series 1), built straight from the game sprites. Zero supports.

    python3 merch/figures/make_figures.py            (needs: pip install manifold3d trimesh numpy scipy)

Each STL is one print plate: the figure lying on its back (face up) plus two arms and two legs lying flat beside it.

* Body: the Blip's 16 x 12 game sprite, 2.5 mm per pixel, as a soft vinyl-toy shape: the outline keeps the pixel
  silhouette (with slightly rounded corners) and the front swells into a smooth rounded dome. The sprite's details are carved into the dome: eyes and mouth sunk in, darker patches and
  inner outlines sunk a little, light patches (bellies, teeth, highlights) raised a little, visors recessed with the
  eyes glowing out of them. Every layer is smaller than the one under it, so nothing overhangs.
* Limbs: rounded arms with mitten hands and chunky legs with boots, all with softened edges.
* 🔒 Locking joints: every limb has a split snap peg with a barb on the end. Push it into its hole and the barb squeezes
  through, then springs open in a wider chamber inside the body and catches behind the hole's back wall: the limb can't
  be pulled back out (please don't try: it's meant to be permanent), but it still turns and holds a pose by friction.
  The holes and chambers are teardrop-shaped (pointed on top) so they print without supports.
* Print in PLA at 0.2 mm, 3 walls, 15-20% infill. Arms turn all the way round; legs swing about 80 degrees each way.
"""
import json
import os
import sys

import manifold3d as mf
import numpy as np
import trimesh
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PX = 2.5                    # mm per sprite pixel
SUB = 10                    # height-field cells per pixel (0.25 mm)
T0, DOME, DOME_R = 9.5, 6.0, 7.0   # body thickness at the outline, extra height in the middle, how far in it reaches full height
ROUND = 0.6                 # silhouette corner rounding
EYE, MOUTH, DARK, LIGHT, VISOR = 1.6, 1.2, 0.7, 0.45, 1.2   # relief depths (mm)
SEG = 48
# 🔒 snap-lock joints (the same for shoulders and hips)
HOLE_D = 4.2                # hole through the wall
WALL = 3.0                  # how thick the wall is that the barb catches behind
CH_D, CH_LEN = 5.6, 2.4     # the chamber inside the body the barb opens up in
SHAFT_D = 4.4               # a hair bigger than the hole: the split shaft squeezes in and holds poses by friction
BARB_D, BARB_LEDGE, BARB_CONE, TIP_D = 4.9, 0.4, 1.2, 3.3
SLOT = 1.2                  # the split down the peg (lets the barb squeeze to HOLE_D)
COLLAR = 0.4                # spacer ring so the limb doesn't rub the body
ZC = 6.0                    # height of every joint axis above the bed (= inside the body's thickness)
# limbs
ARM_W, ARM_L, ARM_T = 7.0, 16.0, 5.5     # arm width, longest length (shoulder centre to fingertips), thickness
LEG_H, NOTCH_H = 7.0, 8.5   # body height off the ground, hip notch height
LEG_X, LEG_Z, TOE = 5.0, 6.5, 3.5         # leg thickness (side to side), depth (front to back), toe sticking forward
LEG_COLS = (3, 11)          # left / right leg under these sprite columns (where the sprite's feet are)
GAP = 0.5


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


def socket(x_face, inward, cy):
    """🔒 Hole + barb chamber going into the body from a side face at x_face (inward = +1 to the right, -1 to the left)."""
    def seg(a, b, d):
        lo, hi = sorted((x_face + inward * a, x_face + inward * b))
        return _along_x(teardrop_cs(cy, ZC, d), lo, hi)
    return union([seg(-1.0, WALL + 0.01, HOLE_D), seg(WALL, WALL + CH_LEN, CH_D)])


def peg(cx, cy, z0):
    """🔒 The snap peg on a limb, standing up from the face at height z0: collar, split shaft, barb with a flat catch."""
    s_len = WALL + 0.25
    parts = [mf.Manifold.cylinder(COLLAR + 1.0, SHAFT_D / 2 + 1.2, SHAFT_D / 2 + 1.2, SEG).translate([cx, cy, z0 - 1.0]),   # sunk 1 mm into the limb
             mf.Manifold.cylinder(s_len + 0.01, SHAFT_D / 2, SHAFT_D / 2, SEG).translate([cx, cy, z0 + COLLAR]),
             mf.Manifold.cylinder(BARB_LEDGE, BARB_D / 2, BARB_D / 2, SEG).translate([cx, cy, z0 + COLLAR + s_len]),
             mf.Manifold.cylinder(BARB_CONE, BARB_D / 2, TIP_D / 2, SEG).translate([cx, cy, z0 + COLLAR + s_len + BARB_LEDGE])]
    top = z0 + COLLAR + s_len + BARB_LEDGE + BARB_CONE
    slot = box(cx - SLOT / 2, cy - BARB_D, z0 + COLLAR + 0.5, cx + SLOT / 2, cy + BARB_D, top + 1)
    return union(parts) - slot


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


def body_and_joints(sprite):
    rows = list(sprite["body"])
    n = len(rows)
    top_y = n * PX + LEG_H
    ey = sprite["eyes"]
    # shoulders: 3 rows below the eyes, at the body's width just under the eyes. Anything sticking out further (ears,
    # claws, little drawn-in arms) is left off where the arms hang; antlers and ears above the shoulders stay.
    shoulder = min(ey + 3, n - 3)
    span = range(ey, min(ey + 4, n))
    cl = min(min(c for c, ch in enumerate(rows[r]) if ch != ".") for r in span)
    cr = max(max(c for c, ch in enumerate(rows[r]) if ch != ".") for r in span)
    xl, xr = cl * PX, (cr + 1) * PX
    sy = top_y - (shoulder + 0.5) * PX
    while sy - CH_D * 0.72 < LEG_H + NOTCH_H + 1 and shoulder > ey:   # keep the shoulder chambers clear of the hips
        shoulder -= 1
        sy = top_y - (shoulder + 0.5) * PX
    keep = np.array([[ch != "." for ch in row] for row in rows])
    for r in range(n):
        y_mid = top_y - (r + 0.5) * PX
        for c in range(16):
            x0 = c * PX
            if (x0 < xl or x0 + PX > xr) and sy - ARM_L - 2 < y_mid < sy + PX:
                keep[r, c] = False
    rel = relief_map(sprite, rows)
    # height field on a fine grid: the dome (by distance from the edge) + the sprite's relief
    fine = np.kron(keep, np.ones((SUB, SUB), bool))
    fine = _no_corner_touch(fine)
    cell = PX / SUB
    dist = ndimage.distance_transform_edt(np.pad(fine, 1))[1:-1, 1:-1] * cell - cell / 2
    t = np.clip(dist / DOME_R, 0, 1)
    h = T0 + DOME * np.sqrt(1 - (1 - t) ** 2) + np.kron(rel, np.ones((SUB, SUB)))
    body = heightfield(fine, h, 0, top_y, cell)
    sil = soften(rects_cs(keep, 0, top_y, PX), ROUND)
    body = body ^ sil.extrude(40)
    # hips: a notch at each bottom corner (open to the side, front and back) with a socket in its inner wall
    hy = LEG_H + NOTCH_H / 2
    hl = LEG_COLS[0] * PX + LEG_X + COLLAR + GAP / 2
    hr = LEG_COLS[1] * PX - COLLAR - GAP / 2
    notches = union([box(-5, LEG_H - 1, -1, hl, LEG_H + NOTCH_H, 30), box(hr, LEG_H - 1, -1, 16 * PX + 5, LEG_H + NOTCH_H, 30)])
    sockets = union([socket(xl, +1, sy), socket(xr, -1, sy), socket(hl, +1, hy), socket(hr, -1, hy)])
    body = body - notches - sockets
    return body, (xl, xr, sy, hl, hr, hy), top_y


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


def arm_length(sy):
    """As long as it can be while the hand stays 1 mm off the ground with the arm hanging down (sy: shoulder height)."""
    return min(ARM_L, sy - 1.0)


def layered(cs, height, chamfer=0.9, steps=3, bottom=0.4):
    """Extrude a profile with softened edges: a small 45-degree chamfer on the bed side, rounded-off top edges."""
    parts = [cs.offset(-bottom, mf.JoinType.Round).extrude(bottom), cs.extrude(height - chamfer - bottom).translate([0, 0, bottom])]
    for i in range(steps):
        a = (i + 1) / steps
        inset = chamfer * (1 - np.sqrt(1 - a * a))
        parts.append(cs.offset(-inset - 0.05, mf.JoinType.Round).extrude(chamfer / steps).translate([0, 0, height - chamfer + i * chamfer / steps]))
    return union(parts)


def arm(x0, y0, length=ARM_L):
    """One arm lying flat (outer side down), peg up. Shoulder at the top end, mitten hand at the bottom."""
    cx, cy = x0 + ARM_W / 2 + 0.6, y0 + length
    shoulder = mf.CrossSection.circle(ARM_W / 2 + 0.3, SEG).translate([cx, cy])
    hand = mf.CrossSection.circle(ARM_W / 2 + 0.6, SEG).translate([cx, y0 + ARM_W / 2 + 0.6])
    bar = mf.CrossSection([[(cx - ARM_W * 0.42, y0 + ARM_W / 2 + 0.6), (cx + ARM_W * 0.42, y0 + ARM_W / 2 + 0.6),
                            (cx + ARM_W / 2, cy), (cx - ARM_W / 2, cy)]])
    thumb = mf.CrossSection.circle(1.6, SEG).translate([cx + ARM_W / 2 + 0.2, y0 + ARM_W / 2 + 2.2])
    shape = soften(shoulder + hand + bar + thumb, 0.5)
    return layered(shape, ARM_T) + peg(cx, cy, ARM_T)


def leg(x0, y0, hip, toe=1):
    """One leg lying flat (outer side down), peg up. Drawn as (u, v) = (front-back, up) from the floor (v = 0) to the hip
    pin (v = hip): a round top that turns inside the hip notch, a shin and a boot with the toe forward. Left and right are
    mirror images (toe = -1 / +1), so both toes point forward once they're on."""
    rd = NOTCH_H / 2 - GAP
    top = mf.CrossSection.circle(rd, SEG).translate([0, hip])
    shin = mf.CrossSection.square([LEG_Z, hip]).translate([-LEG_Z / 2, PX])
    boot = mf.CrossSection.square([LEG_Z + TOE - 1.5, PX + 1.2]).translate([-LEG_Z / 2 - (TOE - 1.5 if toe < 0 else 0), 0])
    tip = mf.CrossSection.circle((PX + 1.2) / 2, SEG).translate([toe * (LEG_Z / 2 + TOE - 1.5), (PX + 1.2) / 2])
    shape = soften(top + shin + boot + tip, 0.6).translate([x0, y0])
    return layered(shape, LEG_X) + peg(x0, y0 + hip, LEG_X)


def plate(sprite):
    body, (xl, xr, sy, hl, hr, hy), top_y = body_and_joints(sprite)
    L = arm_length(sy)
    bx = 16 * PX + 6
    a1 = arm(bx, 2.0, L)
    a2 = arm(bx + ARM_W + 6, 2.0, L)
    l1 = leg(bx + LEG_Z / 2 + TOE, top_y + 4, hy, toe=-1)
    l2 = leg(bx + LEG_Z * 1.5 + 2 * TOE + 6, top_y + 4, hy, toe=+1)
    return body, [a1, a2, l1, l2]


def to_trimesh(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mm.vert_properties)[:, :3], faces=np.asarray(mm.tri_verts))


if __name__ == "__main__":
    sprites = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "sprites.json")))
    only = sys.argv[2:] or None
    for name, sp in sprites.items():
        if only and name not in only:
            continue
        body, limbs = plate(sp)
        t = to_trimesh(union([body] + limbs))
        keep = [c for c in t.split(only_watertight=False) if abs(c.volume) > 1.0]   # drop zero-volume slivers
        t = trimesh.util.concatenate(keep)
        path = os.path.join(HERE, name.lower().replace(" ", "_").replace("-", "") + "_figure.stl")
        t.export(path)
        print(f"{name + ' (' + sp.get('rarity', 'extra') + ')':28} {os.path.basename(path)}  plate {np.round(t.extents, 1).tolist()} mm  "
              f"watertight={t.is_watertight}  parts={len(keep)}")
