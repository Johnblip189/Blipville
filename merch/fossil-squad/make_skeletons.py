"""🦖 Amber Age X: five Fossil Blips, each a voxel Blip shell with a little robot folded up inside.

    python3 merch/fossil-squad/make_skeletons.py      (needs: pip install manifold3d trimesh numpy pillow)

Units are mm. In a frame's own coordinates X is across, Y is up and Z points out of the face.

HOW IT WORKS
- Every Blip is a chunky voxel Blip (the game sprite, the same style as the Series 1 figures) split into two halves:
  - the FRONT half (the face), pinned to the robot's chest with a filament pin, so it never comes off;
  - the BACK half, a hollow cup that clips onto the front half with two filament pins and covers the whole robot.
- To transform, you have to split it: pull the back half off, swing the robot's legs down, and clip the back half back
  on. The legs now come out through the notch in the bottom.
- Three forms:
  - **Blip:** shell closed, legs folded up inside, so nothing of the robot shows.
  - **Walker:** shell closed, the robot's legs and feet sticking out underneath. Tyranno-King's crowned head also pops
    up out of the hatch in its top.
  - **Amber Age X:** the four limb Blips plug onto Tyranno-King:
    - the arms on shoulder axles (through the side holes; they swing all the way round);
    - the legs on hip joints (into the top hole; they swivel).

FRAMES (the robots inside)
- **Limb frame** (×4, one in each of Tricera-Shield, Ptera-Blade, Stego-Stomp and Brachio-Pillar):
  - a chest block with a hip hinge and two legs that fold up behind it;
  - a socket in the top (the hip joint goes in it) and a blind hole in each side (the shoulder axle goes in it);
  - a pin hole in the front for the face.
- **Torso frame** (Tyranno-King):
  - a torso block with a sliding crowned head in a tunnel (push it down for Blip mode, pull it up for the others);
  - two legs that fold up behind;
  - holes for the shoulder axles and hip joints;
  - a pin hole for the face.

Hinges use 1.75 mm 3D-printer filament as pins: cut a piece, push it through, trim it flush. The holes are 1.8 mm, so
the pin is a snug friction fit. If a hole prints tight, run a 1.8 mm drill through it.

Everything is laid out on plates in its print orientation, with no supports. The only overhangs are small hole tops and
the ceiling inside each back half, which bridges and is hidden. An interference check of every mode runs each time.
"""
import json
import math
import os
import sys

import manifold3d as mf
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "figures"))
import make_figures as FIG  # noqa: E402

SEG = 40
PIN = 1.8                   # hinge holes for 1.75 mm filament
GAP = 0.3                   # moving clearance
CLR = 0.6                   # clearance between a frame and the inside of its shell
WALL = 1.6                  # shell wall
JOINT_D, JOINT_HOLE, JOINT_CUT = 5.0, 5.15, 5.8   # shoulder axles / hip joints, the holes they turn in, the holes in the shells
# ---------------------------------------------------------------- limb frame
CW, CH, CD = 18.0, 16.0, 10.0           # chest: x -9..9, y 0..16, z -5..5
LW, LL, LD = 5.5, 15.0, 8.0             # legs: width, length (hip axle to sole), depth
HIP_Y, HIP_Z, KN_R = 1.0, -6.5, 3.0     # hip axle (behind the chest, near its bottom) and the knuckle round it
LUG_OUT, LUG_MID = 1.4, 3.0             # hip lug thickness: two outer, one middle
LEG_X = (-(LUG_MID / 2 + GAP + LW), LUG_MID / 2 + GAP)   # left / right leg x0
FOOT_H = 4.0                            # the foot block (sticks forward a little)
SOCKET_Z, SOCKET_DEPTH = 0.5, 8.0       # the top socket (hip joint) and the side holes (shoulder axle)
ARM_Y, ARM_DEPTH = 12.0, 6.0
LIMB_FPIN = (0.0, 6.0)                  # the face's pin (chest front)
# ---------------------------------------------------------------- torso frame
TW, TH, TD = 34.0, 36.0, 14.0           # x -17..17, y 0..36, z -7..7
HEAD_W, HEAD_D, HEAD_L, HEAD_RISE = 13.0, 9.0, 28.0, 22.0
SLIDE = 0.2                             # the head's sliding clearance (per side)
TUN_Y0 = TH - HEAD_L - 0.4              # the head tunnel's floor
J_Z = 0.0                               # the shoulder axles and hip joints are on the torso's mid-plane
SH_Y, HJ_Y, J_DEPTH = TH - 4.0, 3.0, 8.0
T_HIP_Y, T_HIP_Z = -2.0, -TD / 2 - 1.5  # the torso legs' hinge (behind and below the torso)
TLEG_W, TLEG_L = 9.0, 16.0
TLEG_X = (-TW / 2 + 2, TW / 2 - 2 - TLEG_W)
TORSO_FPIN = (0.0, 4.0)
# ---------------------------------------------------------------- shells
F_MAX = 2                   # the front half: up to 2 voxels thick
PROFILE = 3                 # the back half's rounding (voxels) before it gets as deep as the robot needs
RIM_PIN_DEPTH, BOSS_R, BOSS_D = 3.0, 2.4, 4.2
TORSO_SCALE = 1.7          # Tyranno-King is the big Blip: its voxels are at least this much bigger than the limbs'


def box(x0, y0, z0, x1, y1, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def U(parts):
    parts = [p for p in parts if not p.is_empty()]
    return mf.Manifold.batch_boolean(parts, mf.OpType.Add) if parts else mf.Manifold()


def cyl_x(d, x0, x1, y, z, seg=SEG):
    return mf.Manifold.cylinder(x1 - x0, d / 2, d / 2, seg).rotate([0, 90, 0]).translate([x0, y, z])


def cyl_y(d, y0, y1, x, z, seg=SEG):
    return mf.Manifold.cylinder(y1 - y0, d / 2, d / 2, seg).rotate([-90, 0, 0]).translate([x, y0, z])


def cyl_z(d, z0, z1, x, y, seg=SEG):
    return mf.Manifold.cylinder(z1 - z0, d / 2, d / 2, seg).translate([x, y, z0])


def _along_x(cs, x0, x1):
    mesh = cs.extrude(x1 - x0).to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].copy()
    v = np.stack([v[:, 2] + x0, v[:, 0], v[:, 1]], axis=1)
    tri = np.asarray(mesh.tri_verts)
    m = mf.Manifold(mf.Mesh(vert_properties=v.astype(np.float32), tri_verts=tri.astype(np.uint32)))
    return m if m.volume() > 0 else mf.Manifold(mf.Mesh(vert_properties=v.astype(np.float32), tri_verts=tri[:, ::-1].astype(np.uint32)))


def circle_yz(cy, cz, r):
    return mf.CrossSection([[(cy + r * np.cos(a), cz + r * np.sin(a)) for a in np.linspace(0, 2 * np.pi, SEG, endpoint=False)]])


def rot_x_about(m, deg, y, z):
    return m.translate([0, -y, -z]).rotate([deg, 0, 0]).translate([0, y, z])


def grow(m, r):
    """A slightly bigger copy (the union of 27 shifted copies): clearance round a part."""
    return U([m.translate([dx * r, dy * r, dz * r]) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)])


# ================================================================ limb frame
def limb_chest():
    hx = CW / 2
    c = box(-hx, 0, -CD / 2, hx, CH, CD / 2)
    lug_cs = circle_yz(HIP_Y, HIP_Z, KN_R) + mf.CrossSection.square([2 * KN_R, -CD / 2 + 2 - HIP_Z]).translate([HIP_Y - KN_R, HIP_Z])
    c = c + U([_along_x(lug_cs, x0, x1) for x0, x1 in ((-hx, -hx + LUG_OUT), (-LUG_MID / 2, LUG_MID / 2), (hx - LUG_OUT, hx))])
    for x0 in LEG_X:                                                      # room for the legs' knuckles to turn
        c = c - box(x0 - GAP, HIP_Y - KN_R - 2, HIP_Z - KN_R - 2, x0 + LW + GAP, HIP_Y + KN_R + GAP, -CD / 2 + 2.2)
    c = c - cyl_x(PIN, -hx - 1, hx + 1, HIP_Y, HIP_Z)                     # hip axle
    c = c - cyl_z(PIN, CD / 2 - 4, CD / 2 + 1, *LIMB_FPIN)                # the face's pin
    c = c - cyl_y(JOINT_HOLE, CH - SOCKET_DEPTH, CH + 1, 0, SOCKET_Z)     # top socket (hip joint)
    for s in (-1, 1):                                                     # side holes (shoulder axle)
        c = c - cyl_x(JOINT_HOLE, *sorted((s * (hx + 1), s * (hx - ARM_DEPTH))), ARM_Y, SOCKET_Z)
    return c


def limb_leg(x0):
    """One leg, hanging down from the hip axle."""
    top = min(HIP_Y, -GAP)                                                # the leg stays below the chest
    body = box(x0, HIP_Y - LL, -CD / 2, x0 + LW, top, -CD / 2 + LD)
    kn = _along_x(circle_yz(HIP_Y, HIP_Z, KN_R), x0, x0 + LW)
    bridge = box(x0, HIP_Y - KN_R, HIP_Z, x0 + LW, HIP_Y, -CD / 2 + 0.5) + box(x0, HIP_Y - KN_R, -CD / 2, x0 + LW, top, -CD / 2 + 2.5)
    foot = box(x0, HIP_Y - LL, -CD / 2, x0 + LW, HIP_Y - LL + FOOT_H, CD / 2)
    return U([body, kn, bridge, foot]) - cyl_x(PIN + 0.05, x0 - 1, x0 + LW + 1, HIP_Y, HIP_Z)


def limb_frame(mode):
    """mode: 'blip' (legs folded up behind the chest) or 'walker' (legs down)."""
    P = {"chest": limb_chest(), "legL": limb_leg(LEG_X[0]), "legR": limb_leg(LEG_X[1])}
    if mode == "blip":
        for k in ("legL", "legR"):
            P[k] = rot_x_about(P[k], -180, HIP_Y, HIP_Z)
    return P


# ================================================================ torso frame
def torso():
    hx = TW / 2
    t = box(-hx, 0, -TD / 2, hx, TH, TD / 2)
    t = t - box(-HEAD_W / 2 - SLIDE, TUN_Y0, -HEAD_D / 2 - SLIDE, HEAD_W / 2 + SLIDE, TH + 1, HEAD_D / 2 + SLIDE)   # head tunnel
    for s in (-1, 1):
        for y in (SH_Y, HJ_Y):                                            # shoulder axle and hip joint holes
            t = t - cyl_x(JOINT_HOLE, *sorted((s * (hx + 1), s * (hx - J_DEPTH))), y, J_Z)
    for x0 in TLEG_X:                                                     # the legs hang between lugs at the bottom-back
        cs = circle_yz(T_HIP_Y, T_HIP_Z, 3.0) + \
            mf.CrossSection.square([1.0 - T_HIP_Y, -TD / 2 + 3 - (T_HIP_Z - 3.0)]).translate([T_HIP_Y, T_HIP_Z - 3.0])
        t = t + _along_x(cs, x0 - GAP - 1.4, x0 - GAP) + _along_x(cs, x0 + TLEG_W + GAP, x0 + TLEG_W + GAP + 1.4)
        t = t - box(x0 - GAP, -1, T_HIP_Z - 4, x0 + TLEG_W + GAP, T_HIP_Y + 3 + GAP, -TD / 2 + 2.2)
        t = t - cyl_x(PIN, x0 - 3, x0 + TLEG_W + 3, T_HIP_Y, T_HIP_Z)
    t = t - cyl_z(PIN, TD / 2 - 4, TD / 2 + 1, *TORSO_FPIN)              # the face's pin
    return t


def torso_head(up):
    """The crowned head on a long neck: it slides in the torso's tunnel. Down for Blip mode, up for the others."""
    w, d = HEAD_W, HEAD_D
    y0 = TUN_Y0 + 0.2
    h = box(-w / 2, y0, -d / 2, w / 2, y0 + HEAD_L, d / 2)
    top = y0 + HEAD_L
    for x in (-3.9, 3.9):                                                 # the crown: three spikes
        h = h - box(x - 1.2, top - 3.5, -d, x + 1.2, top + 1, d)
    h = h - box(-w / 2 - 1, top - 3.5, -d, -w / 2 + 1.2, top + 1, d) - box(w / 2 - 1.2, top - 3.5, -d, w / 2 + 1, top + 1, d)
    h = h - box(-w / 2 + 2, top - 8.5, d / 2 - 0.8, w / 2 - 2, top - 6.3, d)   # the visor
    return h.translate([0, HEAD_RISE if up else 0, 0])


def torso_leg(x0):
    body = box(x0, T_HIP_Y - TLEG_L, -TD / 2, x0 + TLEG_W, T_HIP_Y, -1)
    kn = _along_x(circle_yz(T_HIP_Y, T_HIP_Z, 3.0), x0, x0 + TLEG_W)
    bridge = box(x0, T_HIP_Y - 3, T_HIP_Z, x0 + TLEG_W, T_HIP_Y, -TD / 2 + 0.5)
    return U([body, kn, bridge]) - cyl_x(PIN + 0.05, x0 - 1, x0 + TLEG_W + 1, T_HIP_Y, T_HIP_Z)


def torso_frame(mode):
    """mode: 'blip' (legs folded behind, head down), 'walker' (legs down, head up) or 'combined' (legs folded, head up)."""
    P = {"torso": torso(), "head": torso_head(mode != "blip"),
         "legL": torso_leg(TLEG_X[0]), "legR": torso_leg(TLEG_X[1])}
    if mode in ("blip", "combined"):
        for k in ("legL", "legR"):
            P[k] = rot_x_about(P[k], -180, T_HIP_Y, T_HIP_Z)
    return P


# ================================================================ joints
def rod_x(x0, x1):
    """A 5 mm rod along X with a small flat underneath (it prints lying down) and chamfered ends."""
    r = JOINT_D / 2
    rod = cyl_x(JOINT_D, x0 + 0.5, x1 - 0.5, 0, 0) + \
        mf.Manifold.cylinder(0.5, r - 0.5, r, SEG).rotate([0, 90, 0]).translate([x0, 0, 0]) + \
        mf.Manifold.cylinder(0.5, r, r - 0.5, SEG).rotate([0, 90, 0]).translate([x1 - 0.5, 0, 0])
    return rod ^ box(x0 - 1, -r - 1, -r + 0.4, x1 + 1, r + 1, r + 1)


def shoulder_axle(length):
    return rod_x(0, length)


def hip_joint(reach, drop):
    """An L: a rod along +X from x = 0 (the end that goes into the torso) to the corner at x = reach, then straight down
    by `drop` (to the tip that goes into the leg's top socket). Printed lying flat: the L is in the XY plane."""
    r = JOINT_D / 2
    across = rod_x(0, reach + r)
    down = rod_x(0, drop + r).rotate([0, 0, -90]).translate([reach, r, 0])   # +X rotated to -Y, from y = r to -drop
    return across + down


# ================================================================ shells
def body_grid(sp):
    """The sprite's body (12 x 16, no feet: the robot's legs are the feet now). Letters or None."""
    return [[ch if ch != "." else None for ch in row] for row in sp["body"]]


def depth_map(g):
    rows, cols = len(g), len(g[0])
    d = [[99 if c else 0 for c in row] for row in g]
    for _ in range(12):
        for y in range(rows):
            for x in range(cols):
                if d[y][x]:
                    n = [d[b][a] if 0 <= a < cols and 0 <= b < rows else 0 for a, b in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))]
                    d[y][x] = min(d[y][x], 1 + min(n))
    return np.array(d)


def tm(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mm.vert_properties)[:, :3], faces=np.asarray(mm.tri_verts), process=False)


def zmin_map(solid, x0, x1, y0, y1, step=0.25):
    """For a grid of (x, y) points: the lowest z of `solid` above that point (+inf where there's nothing)."""
    xs = np.arange(x0, x1 + step / 2, step)
    ys = np.arange(y0, y1 + step / 2, step)
    gx, gy = np.meshgrid(xs, ys)
    o = np.stack([gx.ravel(), gy.ravel(), np.full(gx.size, -500.0)], 1)
    t = tm(solid)
    loc, idx, _ = t.ray.intersects_location(o, np.tile([0, 0, 1.0], (len(o), 1)), multiple_hits=False)
    z = np.full(len(o), np.inf)
    np.minimum.at(z, idx, loc[:, 2])
    return xs, ys, z.reshape(gx.shape)


class Shell:
    """A Blip's two halves around a frame. Frame coordinates: x = fig_x - ox, y = fig_y - oy, rim plane z = zs."""

    def __init__(self, sp, v, ox, oy, zs):
        self.sp, self.v, self.ox, self.oy, self.zs = sp, v, ox, oy, zs
        self.g = body_grid(sp)
        self.rows, self.cols = len(self.g), len(self.g[0])
        self.filled = np.array([[c is not None for c in row] for row in self.g])
        self.dm = depth_map(self.g)

    def cell_rect(self, r, c):
        v = self.v
        return (c * v - self.ox, (self.rows - 1 - r) * v - self.oy, (c + 1) * v - self.ox, (self.rows - r) * v - self.oy)


def widen(zmap, r):
    """The z map with every point taking the lowest z within r (so a cell 'sees' the cavity up to r away)."""
    from scipy.ndimage import minimum_filter
    xs, ys, z = zmap
    k = int(math.ceil(r / (xs[1] - xs[0]))) * 2 + 1
    return xs, ys, minimum_filter(np.where(np.isfinite(z), z, 1e9), size=k, mode="constant", cval=1e9)


def need_cells(zwide, sh):
    """Voxels of depth each cell needs (0 = nothing inside it) so the hollow keeps a WALL round the cavity.
    None if the cavity (plus its WALL) pokes out of the sprite's body."""
    xs, ys, z = zwide
    gx, gy = np.meshgrid(xs, ys)
    inside = z < 1e8
    c = np.floor((gx + sh.ox) / sh.v).astype(int)
    r = sh.rows - 1 - np.floor((gy + sh.oy) / sh.v).astype(int)
    ok = (r >= 0) & (r < sh.rows) & (c >= 0) & (c < sh.cols)
    if (inside & ~ok).any():
        return None
    rr, cc, zz = r[inside], c[inside], z[inside]
    if (~sh.filled[rr, cc]).any():
        return None
    zmin = np.full((sh.rows, sh.cols), np.inf)
    np.minimum.at(zmin, (rr, cc), zz)
    return np.where(np.isfinite(zmin), np.ceil((sh.zs - zmin + WALL - 1e-6) / sh.v), 0).astype(int)


def fit(sp, zmap, zs, v_range, x_shift=(0.0,)):
    """The smallest voxel size (and the vertical / sideways offset) that holds the cavity inside the sprite's body."""
    zwide = widen(zmap, WALL)
    for v in v_range:
        best = None
        for dx in x_shift:
            for oy in np.arange(0, 12 * v, 0.25):
                sh = Shell(sp, v, 8 * v + dx, oy, zs)
                need = need_cells(zwide, sh)
                if need is None:
                    continue
                score = (oy, need.sum())                   # sit the robot low, so its legs show
                if best is None or score < best[0]:
                    best = (score, sh, need)
        if best:
            return best[1], best[2]
    raise RuntimeError("no voxel size fits")


def build_halves(sh, need, f_pin, cuts_b=(), cuts_f=(), avoid=None):
    """The front half (solid, the face) and the back half (a hollow cup with WALL-thick walls), plus rim pin bosses."""
    v, zs = sh.v, sh.zs
    dB = np.where(sh.filled, np.maximum(need, np.minimum(sh.dm, PROFILE)), 0)
    for _ in range(4):                                                    # no cliffs more than 3 voxels high
        pad = np.pad(dB, 1)
        nb = np.max([pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:]], axis=0)
        dB = np.where(sh.filled, np.maximum(dB, nb - 3), 0)
    dF = np.where(sh.filled, np.minimum(sh.dm, F_MAX), 0)
    e = 0.01
    eyes, glint, mouth = FIG.face_cells(sh.sp)
    back, front = [], []
    for r in range(sh.rows):
        for c in range(sh.cols):
            if not sh.filled[r, c]:
                continue
            x0, y0, x1, y1 = sh.cell_rect(r, c)
            back.append(box(x0 - e, y0 - e, zs - dB[r, c] * v, x1 + e, y1 + e, zs))
            h = dF[r, c] * v
            if (c, r) in eyes and (c, r) not in glint:
                h -= FIG.EYE_D
            elif (c, r) in mouth:
                h -= FIG.MOUTH_D
            front.append(box(x0 - e, y0 - e, zs, x1 + e, y1 + e, zs + h))
    blob, F = U(back), U(front)
    # the hollow: each depth level's outline, pulled in by WALL, as deep as that level less WALL
    hollow = []
    top_left = (-sh.ox, sh.rows * v - sh.oy)
    for k in range(1, int(dB.max()) + 1):
        cs = FIG.rects_cs(dB >= k, top_left[0], top_left[1], v).offset(-WALL, mf.JoinType.Miter)
        if cs.area() > 0:
            hollow.append(cs.extrude(k * v - WALL + 1.0).translate([0, 0, zs - (k * v - WALL)]))
    hollow = U(hollow)
    B = blob - hollow
    # rim pins: two bosses where the frame never goes, far apart
    xs, ys, z = avoid
    spots = []
    for r in range(sh.rows):
        for c in range(sh.cols):
            if sh.filled[r, c] and dF[r, c] >= 2 and dB[r, c] >= 2:
                x0, y0, x1, y1 = sh.cell_rect(r, c)
                for fx in (0.25, 0.5, 0.75):
                    for fy in (0.25, 0.5, 0.75):
                        spots.append((x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)))
    ok = []
    r_need = PIN / 2 + 0.9                                                # a pin hole and a wall round it
    for x, y in spots:
        mx = (xs >= x - r_need - CLR) & (xs <= x + r_need + CLR)
        my = (ys >= y - r_need - CLR) & (ys <= y + r_need + CLR)
        if np.isfinite(z[np.ix_(my, mx)]).any():
            continue
        if (cyl_z(2 * r_need, zs - RIM_PIN_DEPTH - 0.6, zs, x, y, 24) - blob).volume() > 0.02:     # room in the back half
            continue
        if (cyl_z(2 * r_need, zs, zs + RIM_PIN_DEPTH + 0.6, x, y, 24) - F).volume() > 0.02:        # and in the front
            continue
        if any((cyl_z(2 * r_need, zs - BOSS_D, zs + 1, x, y, 24) ^ k).volume() > 0.01 for k in cuts_b):
            continue
        ok.append((x, y))
    if len(ok) < 2:
        raise RuntimeError("no room for the rim pins")
    left, right = [p for p in ok if p[0] < 0], [p for p in ok if p[0] > 0]
    pairs = [(p, q) for p in left for q in right] or [(p, q) for p in ok for q in ok]   # one each side if we can
    a, b = max(pairs, key=lambda pq: (pq[0][0] - pq[1][0]) ** 2 + (pq[0][1] - pq[1][1]) ** 2 - 2 * (pq[0][1] - pq[1][1]) ** 2)
    pins = [a, b]
    for x, y in pins:
        B = B + (cyl_z(2 * BOSS_R, zs - BOSS_D, zs, x, y, 24) ^ blob)
    for x, y in pins:
        B = B - cyl_z(PIN, zs - RIM_PIN_DEPTH, zs + 1, x, y)
        F = F - cyl_z(PIN, zs - 1, zs + RIM_PIN_DEPTH, x, y)
    F = F - cyl_z(PIN, zs - 1, zs + 3.5, *f_pin)                         # onto the chest's pin
    for k in cuts_b:
        B = B - k
    for k in cuts_f:
        F = F - k
    return {"front": F, "back": B, "hollow": hollow, "pins": pins, "dB": dB, "dF": dF, "blob": blob}


# ================================================================ the five Blips
LIMBS = ("Tricera-Shield", "Ptera-Blade", "Stego-Stomp", "Brachio-Pillar")
ARMS = {"Tricera-Shield": -1, "Ptera-Blade": 1}           # -1 = on your left as you look at Amber Age X
LEGS = {"Stego-Stomp": -1, "Brachio-Pillar": 1}


def limb_cuts():
    """What the limb's back half has holes for: the top socket, the side holes, and the legs (out to the rim)."""
    zs = CD / 2 + GAP
    cuts = [cyl_y(JOINT_CUT, CH - 2, 200, 0, SOCKET_Z), cyl_x(JOINT_CUT, -200, 200, ARM_Y, SOCKET_Z)]
    for x0 in LEG_X:
        b = limb_leg(x0).bounding_box()
        cuts.append(box(b[0] - CLR, b[1] - 50, b[2] - CLR, b[3] + CLR, HIP_Y - KN_R - 0.2, zs + 1))
    return cuts


def torso_cuts(joints):
    zs = TD / 2 + GAP
    cuts = [box(-HEAD_W / 2 - 0.5, TH - 3, -HEAD_D / 2 - 0.5, HEAD_W / 2 + 0.5, 300, HEAD_D / 2 + 0.5)]   # the head hatch
    for s in (-1, 1):
        cuts.append(cyl_x(JOINT_CUT, *sorted((s * (TW / 2 - 2), s * 300)), SH_Y, J_Z))
    for x0 in TLEG_X:
        b = torso_leg(x0).bounding_box()
        cuts.append(box(b[0] - CLR, b[1] - 50, b[2] - CLR, b[3] + CLR, T_HIP_Y - 3.2, zs + 1))
    for j, s in zip(joints, (-1, 1)):                                     # the hip joints, plus the way they slide in
        cuts.append(U([grow(j, 0.4).translate([s * dx, 0, 0]) for dx in np.arange(0, 8.5, 1.0)]))
    return cuts


def build_all(sprites):
    """Size every shell, then lay out Amber Age X. Returns a dict of everything."""
    out = {}
    # ---- limbs: one voxel size for all four, so they match
    cav_l = U([grow(m, CLR) for m in limb_frame("blip").values()])
    b = cav_l.bounding_box()
    zmap_l = zmin_map(cav_l, b[0] - 4, b[3] + 4, b[1] - 4, b[4] + 4)
    zs_l = CD / 2 + GAP
    shifts = {n: (np.arange(-4, 4.01, 0.5) if n == "Ptera-Blade" else (0.0,)) for n in LIMBS}
    v_l = max(fit(sprites[n], zmap_l, zs_l, np.arange(2.4, 4.01, 0.05), shifts[n])[0].v for n in LIMBS)
    for n in LIMBS:
        sh, need = fit(sprites[n], zmap_l, zs_l, [v_l], shifts[n])
        out[n] = build_halves(sh, need, LIMB_FPIN, cuts_b=limb_cuts(), avoid=zmap_l)
        out[n]["shell"] = sh
    # ---- torso
    cav_t = U([grow(m, CLR) for m in torso_frame("blip").values()])
    b = cav_t.bounding_box()
    zmap_t = zmin_map(cav_t, b[0] - 4, b[3] + 4, b[1] - 4, b[4] + 4)
    zs_t = TD / 2 + GAP
    sh_t, need_t = fit(sprites["Tyranno-King"], zmap_t, zs_t, np.arange(round(TORSO_SCALE * v_l, 2), 8.01, 0.05))   # the big one
    # ---- the layout (needs the shells' sizes; the hip joints need the layout)
    def ext(n, i):
        return out[n]["blob"].bounding_box()[i]
    half_l = max(max(-ext(n, 0), ext(n, 3)) for n in LIMBS)
    tb = U([box(*sh_t.cell_rect(r, c)[:2], zs_t - 1, *sh_t.cell_rect(r, c)[2:], zs_t)
            for r in range(sh_t.rows) for c in range(sh_t.cols) if sh_t.filled[r, c]]).bounding_box()
    half_t = max(-tb[0], tb[3])
    x_arm = half_t + 0.8 + half_l
    x_leg = half_l + 0.5
    top_l = max(ext(n, 4) for n in LIMBS)                                 # the limb shells' tops above their chests' origin
    y_leg0 = tb[1] - 1.0 - top_l                                          # the legs' frame origin (below the torso shell)
    reach = x_leg - (TW / 2 - J_DEPTH)
    drop = HJ_Y - (y_leg0 + CH - SOCKET_DEPTH + 0.5)
    joints = []
    for s in (-1, 1):
        j = hip_joint(reach, drop).translate([TW / 2 - J_DEPTH, HJ_Y, J_Z])
        joints.append(j if s > 0 else j.mirror([1, 0, 0]))
    out["Tyranno-King"] = build_halves(sh_t, need_t, TORSO_FPIN, cuts_b=torso_cuts(joints), avoid=zmap_t)
    out["Tyranno-King"]["shell"] = sh_t
    axle_len = (x_arm - CW / 2 + ARM_DEPTH - 0.5) - (TW / 2 - J_DEPTH)
    out["layout"] = dict(x_arm=x_arm, x_leg=x_leg, y_leg0=y_leg0, reach=reach, drop=drop, axle_len=axle_len, v_limb=v_l,
                         v_torso=sh_t.v, joints=joints)
    return out


def limb_in_place(H, name, mode, at):
    """A limb Blip (frame + both halves) in a mode, moved to `at` (frame origin)."""
    P = {f"{name}.{k}": m for k, m in limb_frame("blip" if mode == "blip" else "walker").items()}
    P[f"{name}.front"], P[f"{name}.back"] = H[name]["front"], H[name]["back"]
    return {k: m.translate(at) for k, m in P.items()}


def tyranno(H, mode):
    P = {f"T.{k}": m for k, m in torso_frame(mode).items()}
    P["T.front"], P["T.back"] = H["Tyranno-King"]["front"], H["Tyranno-King"]["back"]
    return P


def amber_age_x(H):
    L = H["layout"]
    P = tyranno(H, "combined")
    for n, s in ARMS.items():
        P.update(limb_in_place(H, n, "walker", [s * L["x_arm"], SH_Y - ARM_Y, J_Z - SOCKET_Z]))
        ax = shoulder_axle(L["axle_len"]).translate([TW / 2 - J_DEPTH, SH_Y, J_Z])
        P[f"{n}.axle"] = ax if s > 0 else ax.mirror([1, 0, 0])
    for n, s in LEGS.items():
        P.update(limb_in_place(H, n, "walker", [s * L["x_leg"], L["y_leg0"], J_Z - SOCKET_Z]))
        P[f"{n}.joint"] = L["joints"][0 if s < 0 else 1]
    return P


def check(parts, label):
    names = list(parts)
    bad = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = (parts[a] ^ parts[b]).volume()
            if v > 0.05:
                bad.append(f"{a}/{b} {v:.2f}")
    print(f"  {label:34} {'clear' if not bad else 'OVERLAP: ' + ', '.join(bad)}")
    return not bad


def lay_out(parts, gap=4.0, max_w=170.0):
    """Lay (already print-oriented) parts in rows on the bed, at most max_w mm wide."""
    x = y = row_h = 0.0
    out = []
    for m in parts:
        b = m.bounding_box()
        w, h = b[3] - b[0], b[4] - b[1]
        if x > 0 and x + w > max_w:
            x, y, row_h = 0.0, y + row_h + gap, 0.0
        out.append(m.translate([x - b[0], y - b[1], -b[2]]))
        x += w + gap
        row_h = max(row_h, h)
    return out


def overhang(m):
    t = tm(m)
    n, c = t.face_normals, t.triangles_center
    return float(t.area_faces[(n[:, 2] < -0.77) & (c[:, 2] > 0.3)].sum())


def save(parts, path):
    t = tm(U(parts))
    keep = [c for c in t.split(only_watertight=False) if abs(c.volume) > 1.0]
    t = trimesh.util.concatenate(keep)
    t.export(path)
    return t, len(keep)


def main():
    sprites = json.load(open(os.path.join(HERE, "sprites.json")))
    H = build_all(sprites)
    L = H["layout"]
    print(f"voxel: limbs {L['v_limb']:.2f} mm, Tyranno-King {L['v_torso']:.2f} mm")
    for n in ("Tyranno-King",) + LIMBS:
        b = H[n]["blob"].bounding_box()
        f = H[n]["front"].bounding_box()
        print(f"  {n:15} {b[3] - b[0]:.0f} x {b[4] - b[1]:.0f} x {f[5] - b[2]:.0f} mm   rim pins {np.round(H[n]['pins'], 1).tolist()}")
    print("checks:")
    for n in LIMBS:
        for mode in ("blip", "walker"):
            check(limb_in_place(H, n, mode, [0, 0, 0]), f"{n}, {mode}")
    for mode in ("blip", "walker"):
        check(tyranno(H, mode), f"Tyranno-King, {mode}")
    check(amber_age_x(H), "Amber Age X")
    os.makedirs(os.path.join(HERE, "skeletons"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "shells"), exist_ok=True)
    flat = lambda m: m.rotate([0, 90, 0])                                 # on its side: hinge profiles in the bed plane
    upside = lambda m: m.rotate([180, 0, 0])
    lf = limb_frame("walker")
    T = torso_frame("walker")
    plates = {
        "skeletons/limb_frame": [upside(lf["chest"]), flat(lf["legL"]), flat(lf["legR"])],
        "skeletons/torso_frame": [upside(T["torso"]), torso_head(False).rotate([90, 0, 0]), flat(torso_leg(0)), flat(torso_leg(0)),
                                  shoulder_axle(L["axle_len"]), shoulder_axle(L["axle_len"]),
                                  hip_joint(L["reach"], L["drop"]), hip_joint(L["reach"], L["drop"]).mirror([1, 0, 0])],
    }
    for n in ("Tyranno-King",) + LIMBS:
        h = H[n]
        zs = h["shell"].zs
        plates[f"shells/{n.lower().replace('-', '_')}"] = [h["front"].translate([0, 0, -zs]),
                                                          h["back"].translate([0, 0, -zs]).rotate([0, 180, 0])]
    for name, parts in plates.items():
        laid = lay_out(parts)
        t, k = save(laid, os.path.join(HERE, f"{name}.stl"))
        oh = sum(overhang(p) for p in laid)
        print(f"{name}.stl  {np.round(t.extents, 1).tolist()} mm  watertight={t.is_watertight}  parts={k}  overhang={oh:.0f} mm2")
    json.dump({k: round(float(v), 2) for k, v in L.items() if k != "joints"}, open(os.path.join(HERE, "skeletons", "layout.json"), "w"), indent=1)
    return H


if __name__ == "__main__":
    main()
