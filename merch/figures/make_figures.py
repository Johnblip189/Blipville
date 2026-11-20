"""🧸 Posable Blip figures (Series 1), built straight from the game sprites. Zero supports.

    python3 merch/figures/make_figures.py            (needs: pip install manifold3d trimesh numpy scipy)

Each STL is one print plate: the figure lying on its back (face up), two arms, two legs, two shoulder yokes and 8 snap
pins (5 long + 3 short, one of each spare).

* Body: the Blip's 16 x 12 game sprite, 2.5 mm per pixel, as a soft vinyl-toy shape: the outline keeps the pixel
  silhouette (with slightly rounded corners) and the front swells into a smooth rounded dome. The sprite's details are carved into the dome: eyes and mouth sunk in, darker patches and
  inner outlines sunk a little, light patches (bellies, teeth, highlights) raised a little, visors recessed with the
  eyes glowing out of them. Every layer is smaller than the one under it, so nothing overhangs.
* Limbs: rounded arms with mitten hands and chunky legs with boots, all with softened edges.
* 💪 Action-figure shoulders: each arm hangs from a yoke. The yoke swivels in the body's shoulder socket (the arm swings
  forward and back, all the way round) and the arm hinges in the yoke's fork (it lifts out to the side, all the way up).
  The yoke prints standing on its edge, so both of its pin holes print as clean teardrops.
* 🔒 Locking joints: separate snap pins. A pin goes through the limb's shoulder/hip hole (its head sits in a keyed pocket
  on the outside, so the limb turns the pin) and into the body, where its split barb clicks open in a chamber behind a
  3 mm wall: it can't be pulled back out, but it turns, with a little friction to hold a pose. The pins print lying flat,
  so their springy halves bend along the print layers (pegs printed standing up snapped at the layer lines). The holes and
  chambers in the body are teardrop-shaped (pointed on top) so they print without supports.
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
# 🔒 locking joints: a separate snap pin (printed lying flat, so its springy halves bend along the layers, not across them)
# goes through the limb into the body. Its head sits keyed in the limb (so the limb turns the pin) and its barbs click
# into a chamber inside the body, behind a wall, so it can't come back out. The pin turns in the body with a little
# friction, which holds poses.
PIN_D, PIN_H = 4.6, 3.6     # pin shaft: a 4.6 mm rod with its top and bottom flattened to 3.6 mm (so it prints lying flat)
BODY_HOLE = 4.5             # the hole in the body's wall (a hair smaller than the pin: the split pin squeezes in = friction)
WALL = 3.0                  # the wall the barbs catch behind
CH_D, CH_LEN = 5.9, 2.8     # the chamber inside the body the barbs open up in
BARB_W, BARB_LEDGE, BARB_CONE, TIP_W = 5.3, 0.5, 1.5, 3.8
SLOT, SLOT_LEN = 1.0, 7.5   # the split down the pin from its tip
HEAD_D, HEAD_T = 6.0, 1.6   # the pin's head, which sits in a pocket on the limb's outer side
KEY_CLR = 0.15              # clearance of the pin in its limb hole
COLLAR = 0.4                # spacer ring on the limb so it doesn't rub the body
SPARE_PINS = 2              # extra pins on every plate (one long, one short)
# 💪 action-figure shoulders: a swivel at the body (the arm swings forward / back) plus a hinge just outside it (the arm
# lifts out to the side and up). The "yoke" snaps into the body with a short pin; the arm's narrow top (the tongue)
# sits in the yoke's fork and a long pin through the fork is the hinge.
YB, HX = 3.6, 4.0           # yoke base thickness (sideways), base to hinge axis
Y_HALF = 4.0                # yoke half height
PL_T, TONGUE, PL_GAP = 1.65, 3.4, 0.3   # fork plate thickness, arm tongue thickness, gap on each side of the tongue
HINGE_R = 3.6               # fork plate radius round the hinge
HINGE_HOLE, TONGUE_HOLE = 4.8, 4.5      # pin holes: loose in the fork plates, a friction fit in the tongue
TONGUE_R = 3.6              # the tongue is thicker than the arm (7.2 mm) so the hinge hole has a solid wall round it
TONGUE_LEN = 5.6            # the arm stays tongue-thin this far below the hinge (clears the fork when it lifts)
ZC = 6.0                    # height of every joint axis above the bed (= inside the body's thickness)
# limbs
ARM_W, ARM_L, ARM_T = 7.0, 16.0, 5.5     # arm width, longest length (shoulder centre to fingertips), thickness
LEG_H, NOTCH_H = 7.0, 8.5   # body height off the ground, hip notch height
LEG_X, LEG_Z, TOE = 5.5, 6.5, 3.5         # leg thickness (side to side), depth (front to back), toe sticking forward
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


def td_y(cy, cz, d):
    """A teardrop in (y, z) pointing toward +y (for holes that print with Y up)."""
    r = d / 2
    pts = [(cy + r * np.sin(a), cz + r * np.cos(a)) for a in np.linspace(3 * np.pi / 4, 2 * np.pi + np.pi / 4, 40)]
    pts.append((cy + r * np.sqrt(2), cz))
    return mf.CrossSection([pts], mf.FillRule.NonZero)


def socket(x_face, inward, cy):
    """🔒 Hole + barb chamber going into the body from a side face at x_face (inward = +1 to the right, -1 to the left)."""
    def seg(a, b, d):
        lo, hi = sorted((x_face + inward * a, x_face + inward * b))
        return _along_x(teardrop_cs(cy, ZC, d), lo, hi)
    return union([seg(-1.0, WALL + 0.01, BODY_HOLE), seg(WALL, WALL + CH_LEN, CH_D)])


def _pin_band(r, x0, x1):
    """A piece of the pin along X (from x0 to x1): a rod of radius r, flattened to PIN_H top and bottom (z = 0 .. PIN_H)."""
    rod = mf.Manifold.cylinder(x1 - x0, r, r, SEG).rotate([0, 90, 0]).translate([x0, 0, PIN_H / 2])
    return rod ^ box(x0 - 1, -r - 1, 0, x1 + 1, r + 1, PIN_H)


def pin_length(limb_t):
    return HEAD_T + (limb_t - HEAD_T) + COLLAR + WALL + 0.2


HINGE_PIN = HEAD_T + 2 * PL_T + 2 * PL_GAP + TONGUE + 0.2     # head (outside the fork) to the barb's catch


def pin(x0, y0, limb_t=ARM_T, s_end=None):
    """🔒 One snap pin lying flat on the bed, pointing +X: head, shaft, then a split barb at the tip."""
    s_end = s_end or pin_length(limb_t)
    head = _pin_band(HEAD_D / 2, 0, HEAD_T)
    shaft = _pin_band(PIN_D / 2, HEAD_T - 0.01, s_end + 0.01)
    prof = mf.CrossSection([[(s_end, -BARB_W / 2), (s_end + BARB_LEDGE, -BARB_W / 2), (s_end + BARB_LEDGE + BARB_CONE, -TIP_W / 2),
                             (s_end + BARB_LEDGE + BARB_CONE, TIP_W / 2), (s_end + BARB_LEDGE, BARB_W / 2), (s_end, BARB_W / 2)]])
    barb = prof.extrude(PIN_H) ^ _pin_band(BARB_W / 2, s_end - 0.01, s_end + BARB_LEDGE + BARB_CONE + 0.01)
    tip = s_end + BARB_LEDGE + BARB_CONE
    slot = box(tip - SLOT_LEN, -SLOT / 2, -1, tip + 1, SLOT / 2, PIN_H + 1)
    return (union([head, shaft, barb]) - slot).translate([x0, y0, 0])


def pin_seat(cx, cy, limb_t, along_y=True):
    """What to cut out of a limb lying flat for its pin: a keyed hole through it (the pin's flattened shape) and a pocket
    for the head on the outer (bed) side. The flats run across the limb's length, so the limb turns the pin."""
    def key(r, z0, z1):
        c = mf.CrossSection.circle(r, SEG) ^ mf.CrossSection.square([2 * r + 2, PIN_H + 2 * KEY_CLR]).translate([-r - 1, -PIN_H / 2 - KEY_CLR])
        return c.extrude(z1 - z0).translate([cx, cy, z0])
    return key(PIN_D / 2 + KEY_CLR, -1, limb_t + 1) + key(HEAD_D / 2 + 0.2, -1, HEAD_T + 0.1)


def washer(cx, cy, z0):
    ring = mf.Manifold.cylinder(COLLAR + 0.5, PIN_D / 2 + 1.4, PIN_D / 2 + 1.4, SEG) - \
        mf.Manifold.cylinder(COLLAR + 3, PIN_D / 2 + 0.4, PIN_D / 2 + 0.4, SEG).translate([0, 0, -1])
    return ring.translate([cx, cy, z0 - 0.5])


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
    """One arm lying flat (outer side down). Hinge at the top end (in a thin tongue that sits in the yoke's fork, with a
    hole across it for the hinge pin), mitten hand at the bottom. The hinge axis is (cx, y0 + length, TONGUE_R), along X."""
    cx, yh = x0 + ARM_W / 2 + 0.6, y0 + length
    yw = yh - TONGUE_LEN                                              # where the arm widens out of the tongue
    hand = mf.CrossSection.circle(ARM_W / 2 + 0.6, SEG).translate([cx, y0 + ARM_W / 2 + 0.6])
    bar = mf.CrossSection([[(cx - ARM_W * 0.42, y0 + ARM_W / 2 + 0.6), (cx + ARM_W * 0.42, y0 + ARM_W / 2 + 0.6),
                            (cx + ARM_W / 2, yw - (ARM_W - TONGUE) / 2), (cx + TONGUE / 2, yw), (cx - TONGUE / 2, yw),
                            (cx - ARM_W / 2, yw - (ARM_W - TONGUE) / 2)]])
    thumb = mf.CrossSection.circle(1.6, SEG).translate([cx + ARM_W / 2 + 0.2, y0 + ARM_W / 2 + 2.2])
    lower = layered(soften(hand + bar + thumb, 0.5), ARM_T)
    r = TONGUE_R                                                      # the tongue's end: round on top, 45 degrees underneath
    arc = [(yh + r * np.cos(a), r + r * np.sin(a)) for a in np.linspace(0, np.pi / 2, 16)]
    end = mf.CrossSection([[(yw - 2, 0), (yh, 0)] + arc + [(yw - 2, 2 * r)]])
    tongue = box(cx - TONGUE / 2, yw - 0.5, 0, cx + TONGUE / 2, yh + r + 1, 2 * r) ^ _along_x(end, cx - TONGUE, cx + TONGUE)
    hole = _along_x(teardrop_cs(yh, r, TONGUE_HOLE) ^ mf.CrossSection.square([40, r + TONGUE_HOLE / 2 + 0.5]).translate([yh - 20, 0]),
                    cx - TONGUE, cx + TONGUE)                            # tip trimmed: a short bridge, not a thin point
    return union([lower, tongue]) - hole


def yoke():
    """💪 The shoulder piece, in its own frame: swivel axis = X (the body is at x > 0; the washer touches it at x = 0.4),
    hinge axis along Z at (-YB - HX, 0). A base block with a keyed hole for the short pin, and a fork of two plates."""
    hx = -YB - HX
    base_cs = soften(mf.CrossSection.square([2 * Y_HALF, 2 * (PL_T + PL_GAP) + TONGUE]).translate([-Y_HALF, -(PL_T + PL_GAP + TONGUE / 2)]), 1.0)
    base = _along_x(base_cs, -YB, 0.01)
    zt = TONGUE / 2 + PL_GAP
    pl = (mf.CrossSection.circle(HINGE_R, SEG).translate([hx, 0]) +
          mf.CrossSection.square([-YB + 0.5 - (hx - HINGE_R), Y_HALF]).translate([hx - HINGE_R, -Y_HALF]) +
          mf.CrossSection.square([-YB + 0.5 - hx, HINGE_R]).translate([hx, 0]))
    plates = union([pl.extrude(PL_T).translate([0, 0, zt]), pl.extrude(PL_T).translate([0, 0, -zt - PL_T])])
    ring = _along_x(mf.CrossSection.circle(PIN_D / 2 + 1.4, SEG) - mf.CrossSection.circle(PIN_D / 2 + 0.4, SEG), -0.5, COLLAR)
    band = lambda h: mf.CrossSection.square([20, h]).translate([-10, -h / 2])
    key = _along_x(td_y(0, 0, PIN_D + 2 * KEY_CLR) ^ band(PIN_H + 2 * KEY_CLR), -YB - 1, 1)
    pocket = _along_x(td_y(0, 0, HEAD_D + 0.4) ^ band(PIN_H + 0.4), -YB - 1, -YB + HEAD_T + 0.1)
    holes = teardrop_cs(hx, 0, HINGE_HOLE).extrude(20).translate([0, 0, -10])
    return union([base, plates, ring]) - key - pocket - holes


def yoke_flat(x0, y0):
    """The yoke turned for printing: Y (its up) becomes Z, sitting flat on its bottom edge."""
    return yoke().rotate([90, 0, 0]).translate([x0, y0, Y_HALF])


def leg(x0, y0, hip, toe=1):
    """One leg lying flat (outer side down), inner side up. Drawn as (u, v) = (front-back, up) from the floor (v = 0) to the hip
    pin (v = hip): a round top that turns inside the hip notch, a shin and a boot with the toe forward. Left and right are
    mirror images (toe = -1 / +1), so both toes point forward once they're on."""
    rd = NOTCH_H / 2 - GAP
    top = mf.CrossSection.circle(rd, SEG).translate([0, hip])
    shin = mf.CrossSection.square([LEG_Z, hip]).translate([-LEG_Z / 2, PX])
    boot = mf.CrossSection.square([LEG_Z + TOE - 1.5, PX + 1.2]).translate([-LEG_Z / 2 - (TOE - 1.5 if toe < 0 else 0), 0])
    tip = mf.CrossSection.circle((PX + 1.2) / 2, SEG).translate([toe * (LEG_Z / 2 + TOE - 1.5), (PX + 1.2) / 2])
    shape = soften(top + shin + boot + tip, 0.6).translate([x0, y0])
    return layered(shape, LEG_X) + washer(x0, y0 + hip, LEG_X) - pin_seat(x0, y0 + hip, LEG_X)


def plate(sprite):
    body, (xl, xr, sy, hl, hr, hy), top_y = body_and_joints(sprite)
    L = arm_length(sy)
    bx = 16 * PX + 6
    a1 = arm(bx, 2.0, L)
    a2 = arm(bx + ARM_W + 6, 2.0, L)
    l1 = leg(bx + LEG_Z / 2 + TOE, top_y + 4, hy, toe=-1)
    l2 = leg(bx + LEG_Z * 1.5 + 2 * TOE + 6, top_y + 4, hy, toe=+1)
    px = max(m.bounding_box()[3] for m in (a1, a2, l1, l2)) + 4      # pins and yokes in columns right of the limbs
    pins = [pin(px, 3.0 + HEAD_D / 2 + i * (HEAD_D + 3), LEG_X) for i in range(5)]          # long: 2 hips, 2 hinges, 1 spare
    pins += [pin(px + 15, 3.0 + HEAD_D / 2 + i * (HEAD_D + 3), YB) for i in range(3)]      # short: 2 shoulders, 1 spare
    yokes = [yoke_flat(px + 30 + YB + HX + HINGE_R, 6 + i * 14) for i in range(2)]
    return body, [a1, a2, l1, l2] + pins + yokes
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
