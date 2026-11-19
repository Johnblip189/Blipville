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
    rows = list(sprite["body"]) + ([sprite["feet"]] if sprite.get("feet") else [])
    n = len(rows)
    top_y = n * PX
    ey, dx = sprite["eyes"], sprite.get("dx", 0)
    eyes = {(ey + b, ex + a + dx) for ex in (4, 10) for a in (0, 1) for b in (0, 1)}
    mouth = {(ey + 4, 7), (ey + 4, 8)} if sprite.get("mouth") else set()
    visor = any("v" in r for r in rows)
    body_rows = sprite["body"]
    widest = min(min(c for c, ch in enumerate(r) if ch != ".") for r in body_rows)
    # shoulder: the row nearest eyes+3 where the body is at its widest (so nothing sticks out past the arm)
    cand = [r for r in range(len(body_rows)) if min(c for c, ch in enumerate(body_rows[r]) if ch != ".") == widest]
    shoulder = min(cand, key=lambda r: abs(r - (ey + 3)))
    sy = top_y - (shoulder + 0.5) * PX
    cl = min(c for c, ch in enumerate(rows[shoulder]) if ch != ".")
    cr = max(c for c, ch in enumerate(rows[shoulder]) if ch != ".")
    xl, xr = cl * PX, (cr + 1) * PX
    cubes = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            x0, y0 = c * PX, top_y - (r + 1) * PX
            if (x0 < xl or x0 + PX > xr) and abs(y0 + PX / 2 - sy) < ARM_L + 2:
                continue                                              # nothing past the shoulders where arms swing
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
    return body, (xl, xr, sy), top_y


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


def plate(sprite):
    body, (xl, xr, sy), top_y = body_and_arms(sprite)
    w = xr - xl
    L = arm_length(sy)
    a1 = arm(xr + 6, 2.0, L)
    a2 = arm(xr + 6 + ARM_W + 6, 2.0, L)
    return body, [a1, a2]


def to_trimesh(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mm.vert_properties)[:, :3], faces=np.asarray(mm.tri_verts))


if __name__ == "__main__":
    sprites = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "sprites.json")))
    for name, sp in sprites.items():
        body, arms = plate(sp)
        t = to_trimesh(union([body] + arms))
        keep = [c for c in t.split(only_watertight=False) if abs(c.volume) > 1.0]   # drop zero-volume slivers where
        t = trimesh.util.concatenate(keep)                                           # pixel blocks meet exactly
        path = os.path.join(HERE, name.lower().replace(" ", "_").replace("-", "") + "_figure.stl")
        t.export(path)
        print(f"{name:14} {os.path.basename(path)}  plate {np.round(t.extents, 1).tolist()} mm  watertight={t.is_watertight}  "
              f"parts={len(t.split(only_watertight=False))}")
