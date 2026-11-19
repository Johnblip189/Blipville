"""🧸 Posable Blip figures, built straight from the game sprites. Zero supports.

    python3 merch/figures/make_figures.py            (needs: pip install manifold3d trimesh)

Each STL is one print plate: the figure lying on its back (face up) plus its two arms lying flat beside it.

* The body is the Blip's 16 x 12 sprite (plus feet) as chunky pixel art, 2.5 mm per pixel. Outline pixels stand 0.6 mm
  proud of the body and the eyes are sunk in, so it reads like the sprite even in one color.
* The shoulders are friction joints, like an action figure's: each arm has a split peg (4.2 mm, with a 0.8 mm slot so
  it squeezes in) that presses into a 4.3 mm teardrop-topped hole in the body's side (the point on top prints without
  support). Push the arms in after printing; they turn all the way round and hold any pose by friction.
* Print in PLA at 0.2 mm, 3 walls. If a peg is loose, wrap it in a turn of tape; if it's too tight,
  sand the peg lightly or set PEG_D a little lower and re-export.
"""
import json
import os
import sys

import manifold3d as mf
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
PX = 2.5                    # mm per sprite pixel
T = 16.0                    # body thickness (print height); the front face is up
RELIEF, EYE = 0.6, 1.8      # body pixels sit RELIEF below the outline; eyes / mouth are sunk EYE
HOLE_D, HOLE_DEPTH = 4.3, 7.0
PEG_D, PEG_LEN, SLOT = 4.2, 5.5, 0.8
ARM_W, ARM_L, ARM_T = 6.0, 15.0, 6.0     # arm width, longest length (shoulder to hand) and thickness
COLLAR = 0.4                # small spacer ring on the peg so the arm doesn't rub the body
# 🦵 legs: the body is raised LEG_H off the ground; each leg pegs into a hip notch cut into the body's bottom corner and
# swings forward / back (walk, sit, kick). They replace the little feet drawn in the sprite.
LEG_H, NOTCH_H = 6.0, 7.5   # body height off the ground, hip notch height
LEG_X, LEG_Z, TOE = 5.0, 6.0, 3.0         # leg width (2 pixels), depth front-to-back, toe sticking forward
LEG_COLS = (3, 11)          # left / right leg at these sprite columns (where the sprite's feet are)
GAP = 0.5
SEG = 48


def box(x0, y0, z0, x1, y1, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def union(parts):
    return mf.Manifold.batch_boolean(parts, mf.OpType.Add) if parts else mf.Manifold()


def _along_x(cs, x0, x1):
    # a CrossSection drawn in (y, z) -> a prism along X from x0 to x1
    m = cs.extrude(x1 - x0)                      # in (u=y, v=z, w=extrusion)
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].copy()
    v = np.stack([v[:, 2] + x0, v[:, 0], v[:, 1]], axis=1)          # w->x, u->y, v->z
    tri = np.asarray(mesh.tri_verts)
    return mf.Manifold(mf.Mesh(vert_properties=v.astype(np.float32), tri_verts=tri.astype(np.uint32)))


def body_and_arms(sprite):
    rows = list(sprite["body"])                       # the posable legs replace the sprite's little feet
    n = len(rows)
    top_y = n * PX + LEG_H
    ey, dx = sprite["eyes"], sprite.get("dx", 0)
    eyes = {(ey + b, ex + a + dx) for ex in (4, 10) for a in (0, 1) for b in (0, 1)}
    mouth = {(ey + 4, 7), (ey + 4, 8)} if sprite.get("mouth") else set()
    visor = any("v" in r for r in rows)
    body_rows = sprite["body"]
    # shoulder: 3 rows below the eyes, at the body's width just under the eyes (antlers, ears, tails and claws that
    # stick out further are left off where the arms swing: the arms replace any little arms drawn into the sprite)
    shoulder = min(ey + 3, len(body_rows) - 3)
    span = [r for r in range(ey, min(ey + 4, len(body_rows)))]
    cl = min(min(c for c, ch in enumerate(body_rows[r]) if ch != ".") for r in span)
    cr = max(max(c for c, ch in enumerate(body_rows[r]) if ch != ".") for r in span)
    sy = top_y - (shoulder + 0.5) * PX
    while sy - HOLE_D / 2 < LEG_H + NOTCH_H + 1 and shoulder > ey:   # keep the shoulder holes clear of the hip joints
        shoulder -= 1
        sy = top_y - (shoulder + 0.5) * PX
    xl, xr = cl * PX, (cr + 1) * PX
    cubes = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            x0, y0 = c * PX, top_y - (r + 1) * PX
            if (x0 < xl or x0 + PX > xr) and sy - ARM_L - 2 < y0 + PX / 2 < sy + PX:
                continue                                              # nothing past the shoulders where arms hang
                                                                      # (antlers / ears above them stay)
            if (r, c) in eyes:
                h = T - 0.4 if visor else T - EYE                     # a visor's eyes glow out of it; others are sunk
            elif (r, c) in mouth:
                h = T - EYE
            elif ch == "v":
                h = T - 1.6
            elif ch == "y" and visor:
                h = T - 0.4
            elif ch == "o":
                h = T
            else:
                h = T - RELIEF
            e = 0.02                                                  # a hair of overlap: pixels touching only at a
            cubes.append(box(x0 - e, y0 - e, 0, x0 + PX + e, y0 + PX + e, h))   # corner still join into one solid
    body = union(cubes)
    holes = union([_along_x(teardrop_cs(sy, T / 2, HOLE_D), xl - 1, xl + HOLE_DEPTH),
                   _along_x(teardrop_cs(sy, T / 2, HOLE_D), xr - HOLE_DEPTH, xr + 1)])
    body = body - holes
    # hips: a notch at each bottom corner (open to the side, front and back) with a peg hole in its inner wall
    hy = LEG_H + NOTCH_H / 2
    hl = LEG_COLS[0] * PX + LEG_X + COLLAR + GAP / 2           # inner wall of the left notch
    hr = LEG_COLS[1] * PX - COLLAR - GAP / 2                    # inner wall of the right notch
    notches = union([box(-5, LEG_H - 1, -1, hl, LEG_H + NOTCH_H, T + 1), box(hr, LEG_H - 1, -1, 16 * PX + 5, LEG_H + NOTCH_H, T + 1)])
    hips = union([_along_x(teardrop_cs(hy, T / 2, HOLE_D), hl - 0.5, hl + HOLE_DEPTH),
                  _along_x(teardrop_cs(hy, T / 2, HOLE_D), hr - HOLE_DEPTH, hr + 0.5)])
    body = body - notches - hips
    return body, (xl, xr, sy, hl, hr, hy), top_y


def teardrop_cs(cy, cz, d):
    r = d / 2
    # round at the bottom (from 135 degrees, down and round, to 45 degrees), then up to a point on top (+Z is up)
    pts = [(cy + r * np.cos(a), cz + r * np.sin(a)) for a in np.linspace(3 * np.pi / 4, 2 * np.pi + np.pi / 4, 40)]
    pts.append((cy, cz + r * np.sqrt(2)))
    return mf.CrossSection([pts])


def arm_length(sy):
    """As long as it can be while the hand stays 1 mm off the ground with the arm hanging down (sy: shoulder height)."""
    return min(ARM_L, sy + ARM_W / 2 - 1.5 - 1.0)


def arm(x0, y0, length=ARM_L):
    """One arm lying flat (its outer face down), peg pointing up: a stepped pixel bar with a rounder 'hand'."""
    ARM_L_ = length
    bar = union([box(x0, y0, 0, x0 + ARM_W, y0 + ARM_L_, ARM_T),
                 box(x0 + 1.0, y0 - 1.5, 0, x0 + ARM_W - 1.0, y0, ARM_T)])   # hand
    cx, cy = x0 + ARM_W / 2, y0 + ARM_L_ - ARM_W / 2                 # the peg sits at the shoulder end
    collar = mf.Manifold.cylinder(COLLAR, PEG_D / 2 + 1.2, PEG_D / 2 + 1.2, SEG).translate([cx, cy, ARM_T])
    peg = mf.Manifold.cylinder(PEG_LEN, PEG_D / 2, PEG_D / 2, SEG).translate([cx, cy, ARM_T + COLLAR])
    tip = mf.Manifold.cylinder(0.6, PEG_D / 2, PEG_D / 2 - 0.5, SEG).translate([cx, cy, ARM_T + COLLAR + PEG_LEN])
    slot = box(cx - SLOT / 2, cy - PEG_D, ARM_T + COLLAR + 1.5, cx + SLOT / 2, cy + PEG_D, ARM_T + COLLAR + PEG_LEN + 1)
    return union([bar, collar, peg, tip]) - slot


def leg(x0, y0, hip, toe=1):
    """One leg lying flat (its outer side down), peg pointing up. Drawn in (u, v) = (front-back, up): a pixel leg from
    the floor (v = 0) up to the hip pin (v = hip) with a round top so it turns inside the notch, and a toe in front.
    Left and right legs are mirror images (toe = -1 / +1), so both toes point forward once they're on."""
    rd = NOTCH_H / 2 - GAP
    shape = mf.CrossSection.circle(rd, SEG).translate([0, hip]) + \
        mf.CrossSection.square([LEG_Z, hip]).translate([-LEG_Z / 2, 0]) + \
        mf.CrossSection.square([LEG_Z + TOE, PX]).translate([-LEG_Z / 2 - (TOE if toe < 0 else 0), 0])
    body = shape.extrude(LEG_X).translate([x0 + LEG_Z / 2, y0, 0])
    cx, cy = x0 + LEG_Z / 2, y0 + hip
    collar = mf.Manifold.cylinder(COLLAR, PEG_D / 2 + 1.2, PEG_D / 2 + 1.2, SEG).translate([cx, cy, LEG_X])
    peg = mf.Manifold.cylinder(PEG_LEN, PEG_D / 2, PEG_D / 2, SEG).translate([cx, cy, LEG_X + COLLAR])
    tip = mf.Manifold.cylinder(0.6, PEG_D / 2, PEG_D / 2 - 0.5, SEG).translate([cx, cy, LEG_X + COLLAR + PEG_LEN])
    slot = box(cx - SLOT / 2, cy - PEG_D, LEG_X + COLLAR + 1.5, cx + SLOT / 2, cy + PEG_D, LEG_X + COLLAR + PEG_LEN + 1)
    return union([body, collar, peg, tip]) - slot


def plate(sprite):
    body, (xl, xr, sy, hl, hr, hy), top_y = body_and_arms(sprite)
    L = arm_length(sy)
    a1 = arm(xr + 6, 2.0, L)
    a2 = arm(xr + 6 + ARM_W + 6, 2.0, L)
    l1 = leg(xr + 6 + TOE, top_y - 1, hy, toe=-1)                  # left leg
    l2 = leg(xr + 6 + LEG_Z + 2 * TOE + 6, top_y - 1, hy, toe=+1)   # right leg
    return body, [a1, a2, l1, l2]


def to_trimesh(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mm.vert_properties)[:, :3], faces=np.asarray(mm.tri_verts))


if __name__ == "__main__":
    sprites = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "sprites.json")))
    for name, sp in sprites.items():
        body, arms = plate(sp)                                # arms = all four limbs
        name_rarity = f"{name} ({sp.get('rarity', 'extra')})"
        t = to_trimesh(union([body] + arms))
        keep = [c for c in t.split(only_watertight=False) if abs(c.volume) > 1.0]   # drop zero-volume slivers where
        t = trimesh.util.concatenate(keep)                                           # pixel blocks meet exactly
        path = os.path.join(HERE, name.lower().replace(" ", "_").replace("-", "") + "_figure.stl")
        t.export(path)
        print(f"{name_rarity:28} {os.path.basename(path)}  plate {np.round(t.extents, 1).tolist()} mm  watertight={t.is_watertight}  "
              f"parts={len(t.split(only_watertight=False))}")
