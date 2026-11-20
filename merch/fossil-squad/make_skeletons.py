"""🦖 Amber Age X: the three skeletons (arm frame, leg frame, torso) plus the five snap-on face panels.

    python3 merch/fossil-squad/make_skeletons.py      (needs: pip install manifold3d trimesh numpy)

Units are mm. In the frame's own coordinates X is across, Y is up and Z points out of the face.

Hinges use 1.75 mm 3D-printer filament as pins: cut a piece, push it through, trim it flush. The holes are 1.8 mm, so
the pin is a snug friction fit that holds any angle. If a hole prints tight, run a 1.8 mm drill through it.

LIMB FRAMES (two of each):
- The arm frame is Tricera-Shield and Ptera-Blade; the leg frame is Stego-Stomp and Brachio-Pillar.
- Both are the same little bot:
  - a chest block;
  - two legs on one hip hinge (the hinge sits behind the chest, so the legs swing back and up, flat behind it);
  - two side arms on pins;
  - a head on a hinge at the top-back of the chest;
  - the Blip's face panel, which spins on a short filament pin in the chest front.
- The modes:
  - **Emblem:** the legs, head and arms folded behind, with only the face showing.
  - **Mini-bot:** legs down, head up.
  - **Arm:** turn the bot upside down. The legs become the upper arm and the chest the forearm, with the face spun to
    stay the right way up. The head becomes the fist. The feet have a cross hole: the torso's shoulder axle goes
    through both feet, which locks the legs together and is the 360° bicep swivel. The hip hinge is the elbow.
  - **Leg** (the leg frame only): the bot stands as it is, with the chest as the thigh and the legs as the shin. The
    head folds back, which uncovers a socket in the top of the chest. The torso's hip peg goes in it, as the 360°
    thigh swivel. The hip hinge is the knee, and flip-out toe plates are the stabilizer feet.

TORSO (Tyranno-King):
- A big chest block with the face panel.
- A head on a hinge that flips up out of a slot in the top.
- Two bot legs that fold up behind, for the Tyranno-King mini-bot.
- Two side arms.
- Holes for the shoulder axles and hip pegs. These are separate pins printed flat (with flats, so they're strong).

The pieces are laid out on plates in their print orientation, and nothing needs supports. Previews and an
interference check of every mode are written alongside.
"""
import json
import os

import manifold3d as mf
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = 40
PIN = 1.8                   # hinge holes for 1.75 mm filament
GAP = 0.3                   # moving clearance
# ---------------------------------------------------------------- limb frame (arm / leg)
CW, CH, CD = 20.0, 16.0, 10.0           # chest: x -10..10, y 0..16, z -5..5
LW, LL, LD = 6.5, 14.5, 8.0             # legs: width, length (hip axle to sole), depth
HIP_Y, HIP_Z, KN_R = -2.0, -6.5, 3.0    # hip axle (behind and below the chest) and the knuckle round it
LUG_OUT, LUG_MID = 1.4, 3.0             # hip lug thickness: two outer, one middle
LEG_X = (-(LUG_MID / 2 + GAP + LW), LUG_MID / 2 + GAP)   # left / right leg x0
FOOT_H = 4.0                            # the foot block at the end of each leg (with the cross hole)
AXLE_D, AXLE_HOLE = 5.0, 5.2            # shoulder axle / hip peg and the holes they turn in
HEAD = (9.0, 8.0, 8.0)                  # head w, h, d
ARM = (3.6, 12.0, 5.0)                  # bot arm w, h, d
PEG_D, PEG_HOLE, PEG_L = 3.0, 3.15, 3.0 # face panel centre peg
FACE_T = 1.6                            # face panel base thickness (the voxel face sits on it)
TOE_Y, TOE_Z = HIP_Y - LL + 1.1, CD / 2 - 1.6   # the toe plate pin, at the front of the foot
# ---------------------------------------------------------------- torso
TW, TH, TD = 40.0, 36.0, 18.0           # x -20..20, y 0..36, z -9..9
T_HEAD = (14.0, 11.0, 12.0)
SHOULDER_Y, SHOULDER_Z = 32.0, 2.0      # shoulder axle holes (along X, near the top of the side faces)
HIP_PEG_X, HIP_PEG_Z = 14.2, 4.0        # hip peg holes (along Y, in the bottom face)
T_HIP_Y, T_HIP_Z = -2.0, -TD / 2 - 1.5   # the mini-bot legs' hinge (behind and below the torso)
TLEG_X = (-TW / 2 + 3, TW / 2 - 3 - 9)
ARM_OUT = 14.5                                          # the arm frames' centres sit this far out from the torso's sides
SHOULDER_AXLE = 8 + ARM_OUT + LW + LUG_MID / 2 + GAP + 0.6   # 8 mm in the torso, across, and through both feet
HIP_PEG = 8 + 7.5                                       # 8 mm in the torso + 7.5 mm into the thigh


def box(x0, y0, z0, x1, y1, z1):
    return mf.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def U(parts):
    return mf.Manifold.batch_boolean(parts, mf.OpType.Add)


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


def knuckle_yz(cy, cz, r, n=28):
    """A round knuckle in (y, z), with 45-degree chamfers underneath so it prints with Z up."""
    pts = [(cy + r * np.cos(a), cz + r * np.sin(a)) for a in np.linspace(-np.pi / 4, 5 * np.pi / 4, n)]
    pts.append((cy, cz - r * np.sqrt(2)))
    return pts


# ================================================================ limb frame parts (frame coordinates)
def limb_chest(leg_frame):
    hx = CW / 2
    c = box(-hx, 0, -CD / 2, hx, CH, CD / 2)
    # hip lugs: two outer and one middle, reaching back and down to the hip axle
    lug_cs = mf.CrossSection.circle(KN_R, SEG).translate([HIP_Y, HIP_Z]) + \
        mf.CrossSection.square([0.6 - HIP_Y, -CD / 2 + 2 - (HIP_Z - KN_R)]).translate([HIP_Y, HIP_Z - KN_R])
    lugs = U([_along_x(lug_cs, x0, x1) for x0, x1 in ((-hx, -hx + LUG_OUT), (-LUG_MID / 2, LUG_MID / 2), (hx - LUG_OUT, hx))])
    c = c + lugs
    # notches so the legs' knuckles can turn under the chest
    for x0 in LEG_X:
        c = c - box(x0 - GAP, HIP_Y - KN_R - 2, HIP_Z - KN_R - 2, x0 + LW + GAP, HIP_Y + KN_R + GAP, -CD / 2 + 2.2)
    c = c - cyl_x(PIN, -hx - 1, hx + 1, HIP_Y, HIP_Z)                     # hip axle hole
    # head hinge: a slot in the top-back edge with a pin across
    c = c - box(-HEAD[0] / 2 - GAP, CH - 4.4, -CD / 2 - 1, HEAD[0] / 2 + GAP, CH + 1, -CD / 2 + 4.2)
    c = c - cyl_x(PIN, -hx - 1, hx + 1, CH - 1.6, -CD / 2 + 1.6)
    # side arm pins (in the chest, at the shoulders)
    c = c - cyl_x(PIN, -hx - 1, hx + 1, CH - 3.0, 0)
    # the face panel's peg socket
    c = c - cyl_z(PIN, CD / 2 - 4, CD / 2 + 1, 0, CH / 2)                 # face panel pin
    if leg_frame:                                                         # a pocket in the back for the head (leg mode)
        c = c - box(-HEAD[0] / 2 - GAP, CH - 3.2 - HEAD[1] - 2.2, -CD / 2 - 1, HEAD[0] / 2 + GAP, CH - 1.0, -CD / 2 + 3.6)
    if leg_frame:                                                         # the thigh swivel socket (torso hip peg)
        c = c - cyl_y(AXLE_HOLE, CH - 8, CH + 1, 0, 1.5)
    return c


def limb_leg(x0, foot_flaps):
    """One leg, hanging down from the hip axle (y = HIP_Y at the top, z behind)."""
    body = box(x0, HIP_Y - LL, -CD / 2, x0 + LW, HIP_Y, -CD / 2 + LD)
    kn = _along_x(mf.CrossSection([[(y, z) for y, z in
                                    [(HIP_Y + KN_R * np.cos(a), HIP_Z + KN_R * np.sin(a)) for a in np.linspace(0, 2 * np.pi, SEG)]]],
                                  mf.FillRule.NonZero), x0, x0 + LW)
    bridge = box(x0, HIP_Y - KN_R, HIP_Z, x0 + LW, HIP_Y, -CD / 2 + 0.5)
    foot = box(x0, HIP_Y - LL, -CD / 2, x0 + LW, HIP_Y - LL + FOOT_H, CD / 2 + 0.5)
    leg = U([body, kn, bridge, foot]) - cyl_x(PIN + 0.05, x0 - 1, x0 + LW + 1, HIP_Y, HIP_Z)
    leg = leg - cyl_x(AXLE_HOLE, x0 - 1, x0 + LW + 1, HIP_Y - LL + FOOT_H / 2, 1.0)   # the cross hole (shoulder axle)
    if foot_flaps:                                                      # a notch + pin for the flip-out toe plate
        leg = leg - box(x0 - 1, HIP_Y - LL - 1, CD / 2 - 3.4, x0 + LW + 1, HIP_Y - LL + 2.6, CD / 2 + 2)
        leg = leg - cyl_x(PIN, x0 - 1, x0 + LW + 1, TOE_Y, TOE_Z)
    return leg


def toe_plate(x0):
    """Flip-out toe plate (leg frame): hinges in a notch at the front of the foot; flips down flat as a stabilizer."""
    r = 1.1
    knuckle = _along_x(mf.CrossSection.circle(r, 24).translate([TOE_Y, TOE_Z]), x0 + GAP, x0 + LW - GAP)
    plate = box(x0 + GAP, TOE_Y - r, TOE_Z, x0 + LW - GAP, TOE_Y - r + 2.0, TOE_Z + 9.0)
    return (knuckle + plate) - cyl_x(PIN + 0.05, x0 - 1, x0 + LW + 1, TOE_Y, TOE_Z)


def limb_head():
    """The head: hinges on the chest's top-back pin; stands up in bot mode, folds back flat for emblem mode."""
    w, h, d = HEAD
    y0 = CH + GAP
    head = box(-w / 2, y0, -CD / 2 + 0.2, w / 2, y0 + h, -CD / 2 + 0.2 + d)
    tab = box(-w / 2 + 0.6, CH - 3.2 + GAP, -CD / 2 - 0.8, w / 2 - 0.6, y0 + 0.5, -CD / 2 + 4.0)
    visor = box(-w / 2 + 1.5, y0 + 3.6, -CD / 2 + 0.2 + d - 0.6, w / 2 - 1.5, y0 + 5.4, -CD / 2 + 0.2 + d + 0.6)
    return (U([head, tab]) - visor) - cyl_x(PIN + 0.05, -w, w, CH - 1.6, -CD / 2 + 1.6)


def limb_arm(side):
    """A side arm on the chest's shoulder pin (side -1 = left)."""
    w, h, d = ARM
    x0 = CW / 2 + GAP if side > 0 else -CW / 2 - GAP - w
    arm = box(x0, CH - 3.0 - h + 2.0, -d / 2, x0 + w, CH - 3.0 + 2.6, d / 2)
    return arm - cyl_x(PIN + 0.05, x0 - 1, x0 + w + 1, CH - 3.0, 0)


# ================================================================ torso (frame coordinates)
def torso():
    hx = TW / 2
    t = box(-hx, 0, -TD / 2, hx, TH, TD / 2)
    t = t - box(-T_HEAD[0] / 2 - GAP, TH - 6, -TD / 2 - 1, T_HEAD[0] / 2 + GAP, TH + 1, TD / 2 - 2)      # head slot (folded)
    t = t - cyl_x(PIN, -hx - 1, hx + 1, TH - 3, -TD / 2 + 3)                                            # head hinge
    for s in (-1, 1):
        x0, x1 = (hx - 8, hx + 1) if s > 0 else (-hx - 1, -hx + 8)
        t = t - cyl_x(AXLE_D, x0, x1, SHOULDER_Y, SHOULDER_Z)                                           # shoulder axle holes
        t = t - cyl_y(AXLE_D, -1, 8, s * HIP_PEG_X, HIP_PEG_Z)                                          # hip peg holes
    # bot legs fold up behind: each leg hangs between two lugs at the bottom-back (hinge behind the body)
    for x0 in TLEG_X:
        cs = mf.CrossSection.circle(3.0, SEG).translate([T_HIP_Y, T_HIP_Z]) + \
            mf.CrossSection.square([1.0 - T_HIP_Y, -TD / 2 + 3 - (T_HIP_Z - 3.0)]).translate([T_HIP_Y, T_HIP_Z - 3.0])
        t = t + _along_x(cs, x0 - GAP - 1.4, x0 - GAP) + _along_x(cs, x0 + 9 + GAP, x0 + 9 + GAP + 1.4)
        t = t - box(x0 - GAP, -1, T_HIP_Z - 4, x0 + 9 + GAP, T_HIP_Y + 3 + GAP, -TD / 2 + 2.2)       # knuckle notch
        t = t - cyl_x(PIN, x0 - 3, x0 + 12, T_HIP_Y, T_HIP_Z)
    t = t - cyl_x(PIN, -hx - 1, hx + 1, TH - 7, -4)                                                    # side arm pins
    t = t - cyl_z(PIN, TD / 2 - 5, TD / 2 + 1, 0, TH / 2 - 1)                                          # face panel pin
    return t


def torso_head():
    w, h, d = T_HEAD
    head = box(-w / 2, TH - 6 + GAP, -TD / 2 + 0.5, w / 2, TH - 6 + GAP + h, -TD / 2 + 0.5 + d)
    crest = U([box(-1.6, TH - 6 + GAP + h, -TD / 2 + 4, 1.6, TH - 6 + GAP + h + 5, -TD / 2 + 8),
               box(-5, TH - 6 + GAP + h, -TD / 2 + 4, 5, TH - 6 + GAP + h + 1.6, -TD / 2 + 8)])
    visor = box(-w / 2 + 2, TH + 0.5, -TD / 2 + 0.5 + d - 0.8, w / 2 - 2, TH + 3, -TD / 2 + 0.5 + d + 0.2)
    return (U([head, crest]) - visor) - cyl_x(PIN + 0.05, -w, w, TH - 3, -TD / 2 + 3)


def torso_bot_leg(x0):
    """Tyranno-King's mini-bot leg: hangs from a hinge behind the torso's bottom and folds up flat behind it."""
    body = box(x0, T_HIP_Y - 16, -TD / 2, x0 + 9, T_HIP_Y, -1)
    kn = _along_x(mf.CrossSection([[(T_HIP_Y + 3 * np.cos(a), T_HIP_Z + 3 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, SEG)]]), x0, x0 + 9)
    bridge = box(x0, T_HIP_Y - 3, T_HIP_Z, x0 + 9, T_HIP_Y, -TD / 2 + 0.5)
    return U([body, kn, bridge]) - cyl_x(PIN + 0.05, x0 - 1, x0 + 10, T_HIP_Y, T_HIP_Z)


def torso_arm(side):
    w = 5.0
    x0 = TW / 2 + GAP if side > 0 else -TW / 2 - GAP - w
    return box(x0, TH - 7 - 14, -7, x0 + w, TH - 7 + 3, -1) - cyl_x(PIN + 0.05, x0 - 1, x0 + w + 1, TH - 7, -4)


def axle_pin(length):
    """Shoulder axle / hip peg: a 5 mm rod with flats top and bottom (prints lying flat), slightly snug."""
    rod = cyl_x(AXLE_D, 0, length, 0, AXLE_D * 0.4)
    return rod ^ box(-1, -AXLE_D, 0, length + 1, AXLE_D, AXLE_D * 0.8)


# ================================================================ face panels (from the sprites)
def face_panel(sp, width):
    """The Blip's face as a voxel relief on a base plate, with a centre peg on the back (z < 0)."""
    rows = sp["body"]
    px = width / 16
    h_total = len(rows) * px
    cells = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            x0, y0 = -width / 2 + x * px, h_total / 2 - (y + 1) * px
            raise_ = 1.2 if ch in "o" else 0.8
            cells.append(box(x0 - 0.06, y0 - 0.06, 0, x0 + px + 0.06, y0 + px + 0.06, FACE_T + raise_))
    plate = U(cells)
    ey = sp["eyes"]
    for ex in (4, 10):                                                     # eyes sunk in
        x0, y0 = -width / 2 + ex * px, h_total / 2 - (ey + 2) * px
        plate = plate - box(x0, y0, FACE_T + 0.2, x0 + 2 * px, y0 + 2 * px, FACE_T + 3)
    return plate - cyl_z(PIN, -1, FACE_T - 0.4, 0, 0)                      # filament pin hole (the panel spins on it)


# ================================================================ assemblies (for previews and checks)
def rot_x_about(m, deg, y, z):
    return m.translate([0, -y, -z]).rotate([deg, 0, 0]).translate([0, y, z])


def limb_parts(leg_frame):
    return {"chest": limb_chest(leg_frame), "legL": limb_leg(LEG_X[0], leg_frame), "legR": limb_leg(LEG_X[1], leg_frame),
            "head": limb_head(), "armL": limb_arm(-1), "armR": limb_arm(1)}


def limb_pose(parts, mode):
    """emblem / bot / limb. Returns posed parts (in frame coordinates)."""
    out = dict(parts)
    if mode == "emblem":
        for k in ("legL", "legR"):
            out[k] = rot_x_about(parts[k], -180, HIP_Y, HIP_Z)              # swing back and up behind the chest
        out["head"] = rot_x_about(parts["head"], -90, CH - 1.6, -CD / 2 + 1.6)    # tips back, flat on top of the folded legs
    return out


def rot_z_about(m, deg, x, y):
    return m.translate([-x, -y, 0]).rotate([0, 0, deg]).translate([x, y, 0])


def axle_at(length, x0, x1, y, z):
    return cyl_x(AXLE_D, min(x0, x1), max(x0, x1), y, z)


def amber_age_x(sprites):
    """Everything put together as Amber Age X (torso coordinates). Returns {name: (manifold, sprite name or None)}."""
    out = {}
    T = {"torso": torso(), "head": torso_head(), "legL": rot_x_about(torso_bot_leg(TLEG_X[0]), -180, T_HIP_Y, T_HIP_Z),
         "legR": rot_x_about(torso_bot_leg(TLEG_X[1]), -180, T_HIP_Y, T_HIP_Z),
         "armL": rot_x_about(torso_arm(-1), 180, TH - 7, -4), "armR": rot_x_about(torso_arm(1), 180, TH - 7, -4)}   # arms up: shoulder pauldrons
    for k, m in T.items():
        out["T." + k] = (m, None)
    out["T.face"] = (face_panel(sprites["Tyranno-King"], TW - 2).translate([0, TH / 2 - 1, TD / 2]), "Tyranno-King")
    # arms: the arm frame turned upside down (180 degrees about Z), its feet on the shoulder axle
    foot_y = HIP_Y - LL + FOOT_H / 2
    for side, name in ((-1, "Tricera-Shield"), (1, "Ptera-Blade")):
        P = limb_parts(False)
        cx = side * (TW / 2 + ARM_OUT)
        place = lambda m: rot_z_about(m, 180, 0, 0).translate([cx, SHOULDER_Y + foot_y, SHOULDER_Z - 1.0])
        for k, m in P.items():
            out[f"{name}.{k}"] = (place(m), None)
        face = face_panel(sprites[name], CW - 2).translate([0, -CH / 2, CD / 2])   # spun on its pin so it stays upright
        out[f"{name}.face"] = (face.translate([cx, SHOULDER_Y + foot_y, SHOULDER_Z - 1.0]), name)
        x0, x1 = (side * TW / 2, cx + side * (LW + LUG_MID / 2 + GAP + 0.6))
        out[f"{name}.axle"] = (axle_at(SHOULDER_AXLE, side * (TW / 2 - 8), x1, SHOULDER_Y, SHOULDER_Z), None)
    # legs: the leg frame standing upright under the hip pegs, head folded back, toe plates flipped down
    for side, name in ((-1, "Stego-Stomp"), (1, "Brachio-Pillar")):
        P = limb_parts(True)
        P["head"] = rot_x_about(P["head"], -180, CH - 1.6, -CD / 2 + 1.6)     # down into the pocket in the thigh's back
        P["toeL"], P["toeR"] = toe_plate(LEG_X[0]), toe_plate(LEG_X[1])
        place = lambda m: m.translate([side * HIP_PEG_X, -CH - GAP, HIP_PEG_Z - 1.5])
        for k, m in P.items():
            out[f"{name}.{k}"] = (place(m), None)
        out[f"{name}.face"] = (place(face_panel(sprites[name], CW - 2).translate([0, CH / 2, CD / 2])), name)
        out[f"{name}.peg"] = (cyl_y(AXLE_D, -HIP_PEG + 8, 8, side * HIP_PEG_X, HIP_PEG_Z), None)
    return out


def check(parts, label):
    names = list(parts)
    bad = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = (parts[a] ^ parts[b]).volume()
            if v > 0.5:
                bad.append(f"{a}/{b} {v:.1f}")
    print(f"  {label:28} {'clear' if not bad else 'OVERLAP: ' + ', '.join(bad)}")
    return not bad


def tm(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mm.vert_properties)[:, :3], faces=np.asarray(mm.tri_verts))


def upside_down(m):
    return m.rotate([180, 0, 0])            # top face on the bed (lugs and slots then grow straight up)


def on_side(m):
    return m.rotate([0, 90, 0])             # lying on its side: the hinge profile is in the bed plane


def back_down(m):
    return m                                # as modelled with +Z up... (front up, back on the bed)


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
    """Downward-facing area (mm^2) more than 50 degrees from vertical, above the first layer: what would need support."""
    t = tm(m)
    n, c = t.face_normals, t.triangles_center
    return float(t.area_faces[(n[:, 2] < -0.77) & (c[:, 2] > 0.3)].sum())


if __name__ == "__main__":
    sprites = json.load(open(os.path.join(HERE, "sprites.json")))
    os.makedirs(os.path.join(HERE, "skeletons"), exist_ok=True)
    print("checks:")
    for leg in (False, True):
        P = limb_parts(leg)
        for mode in ("bot", "emblem"):
            check(limb_pose(P, mode), f"{'leg' if leg else 'arm'} frame, {mode}")
    T = {"torso": torso(), "head": torso_head(), "legL": torso_bot_leg(TLEG_X[0]), "legR": torso_bot_leg(TLEG_X[1]),
         "armL": torso_arm(-1), "armR": torso_arm(1)}
    check(T, "torso, mini-bot")
    folded = dict(T, legL=rot_x_about(T["legL"], -180, T_HIP_Y, T_HIP_Z), legR=rot_x_about(T["legR"], -180, T_HIP_Y, T_HIP_Z))
    check(folded, "torso, Amber Age X (legs up)")
    full = amber_age_x(sprites)
    hinge_pins = {k: v[0] for k, v in full.items()}
    # the pegs / axles are meant to sit in their holes: check everything else against everything else
    check({k: m for k, m in hinge_pins.items() if not k.endswith((".axle", ".peg"))}, "Amber Age X, combined")
    for k in [k for k in hinge_pins if k.endswith((".axle", ".peg"))]:
        rubs = [f"{o} {(hinge_pins[k] ^ hinge_pins[o]).volume():.1f}" for o in hinge_pins
                if o != k and not o.endswith((".axle", ".peg")) and (hinge_pins[k] ^ hinge_pins[o]).volume() > 0.5]
        print(f"  {k:28} {'fits' if not rubs else 'rubs: ' + ', '.join(rubs)}")
    L, G = limb_parts(False), limb_parts(True)
    plates = {
        "arm_frame": lay_out([upside_down(L["chest"]), on_side(L["legL"]), on_side(L["legR"]), on_side(L["head"]),
                              on_side(L["armL"]), on_side(L["armR"])]),
        "leg_frame": lay_out([upside_down(G["chest"]), on_side(G["legL"]), on_side(G["legR"]), on_side(G["head"]),
                              on_side(G["armL"]), on_side(G["armR"]), on_side(toe_plate(0)), on_side(toe_plate(0))]),
        "torso_frame": lay_out([upside_down(T["torso"]), on_side(T["head"]), on_side(T["legL"]), on_side(T["legR"]),
                                on_side(T["armL"]), on_side(T["armR"]), axle_pin(SHOULDER_AXLE), axle_pin(SHOULDER_AXLE), axle_pin(HIP_PEG), axle_pin(HIP_PEG)]),
    }
    for name, parts in plates.items():
        t = tm(U(parts))
        keep = [c for c in t.split(only_watertight=False) if abs(c.volume) > 1.0]      # drop zero-volume slivers
        t = trimesh.util.concatenate(keep)
        t.export(os.path.join(HERE, "skeletons", f"{name}.stl"))
        oh = sum(overhang(p) for p in parts)
        print(f"{name}.stl  {np.round(t.extents, 1).tolist()} mm  watertight={t.is_watertight}  parts={len(keep)}  overhang={oh:.0f} mm2")
    for name, sp in sprites.items():
        fp = face_panel(sp, TW - 2 if name == "Tyranno-King" else CW - 2)
        t = tm(fp)
        path = os.path.join(HERE, "skeletons", f"face_{name.lower().replace('-', '_')}.stl")
        t.export(path)
        print(f"{os.path.basename(path)}  {np.round(t.extents, 1).tolist()} mm  watertight={t.is_watertight}")
