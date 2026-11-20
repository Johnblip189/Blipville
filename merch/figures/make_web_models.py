"""🌐 Colored 3D models of the merch for the website's viewer (docs/merch/models/*.glb).

    python3 merch/figures/make_web_models.py          (needs what make_figures.py needs)

Each figure is put together standing on its base and painted with the sprite's colors (one mesh per color, so the
files stay small). The chompers are one color.
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_figures as F  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "docs", "merch", "models")
BASE_COLOR = (64, 55, 98)
LETTER_COLOR = (255, 210, 90)
FILES = {"T-Rex": "trex"}


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main_letter(sp):
    letters = [c.lower() for r in sp["body"] for c in r if c not in ".o*"]
    return max(set(letters), key=letters.count)


def figure_colors(t, sp):
    """Each face gets the sprite color under it (front faces), or the Blip's main color (sides and back)."""
    rows, pal = sp["body"], sp["colors"]
    main = hexrgb(pal[main_letter(sp)])
    top_y = len(rows) * F.PX
    ey, dx = sp["eyes"], sp.get("dx", 0)
    eyes = {(ey + b, ex + a + dx) for ex in (4, 10) for a in (0, 1) for b in (0, 1)}
    visor = any("v" in r for r in rows)
    out = np.tile(np.array(main, float), (len(t.faces), 1))
    c, n = t.triangles_center, t.face_normals
    for i in np.where(n[:, 2] > 0.5)[0]:
        col_, row_ = int(c[i, 0] // F.PX), int((top_y - c[i, 1]) // F.PX)
        if not (0 <= row_ < len(rows) and 0 <= col_ < 16):
            continue
        ch = rows[row_][col_]
        if (row_, col_) in eyes:
            out[i] = hexrgb(pal.get("e", "#111111")) if not visor else hexrgb(pal.get("e", "#ffffff"))
        elif ch == "*":
            out[i] = np.minimum(np.array(main) * 1.2 + 30, 255)
        elif ch != ".":
            out[i] = hexrgb(pal.get(ch.lower(), pal[main_letter(sp)]))
    return out.astype(np.uint8)


def by_color(meshes_colors):
    """One mesh per color (with a plain material each)."""
    scene = trimesh.Scene()
    groups = {}
    for t, cols in meshes_colors:
        for col in np.unique(cols, axis=0):
            sub = t.submesh([np.where((cols == col).all(1))[0]], append=True)
            groups.setdefault(tuple(int(v) for v in col), []).append(sub)
    for i, (col, parts) in enumerate(groups.items()):
        m = trimesh.util.concatenate(parts)
        m.merge_vertices()
        lin = [round(255 * ((v / 255) / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4)) for v in col]
        m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(     # glTF colors are linear
            baseColorFactor=[*lin, 255], metallicFactor=0.0, roughnessFactor=0.75))
        scene.add_geometry(m, geom_name=f"c{i}")
    return scene


def figure_scene(name, sp):
    fig, hx = F.body(sp)
    b = F.base(sp, name, hx, 16 * F.PX)
    # the base as printed (x, y from its front edge, z up) -> standing: y up, z toward the viewer
    b = b.rotate([-90, 0, 0]).translate([0, -F.BASE_H, F.BASE_D - F.BACK])
    ft, bt = F.to_trimesh(fig), F.to_trimesh(b)
    bc = np.tile(np.array(BASE_COLOR, np.uint8), (len(bt.faces), 1))
    c, n = bt.triangles_center, bt.face_normals
    front = F.BASE_D - F.BACK                                        # the lettering strip, in from the base's edges
    strip = (c[:, 2] > front - (F.BASE_D - F.BACK - 17.0) + 0.3) & (c[:, 2] < front - 1.5) & (np.abs(c[:, 0] - 8 * F.PX) < 16)
    bc[(n[:, 1] > 0.5) & (c[:, 1] < -0.3) & (c[:, 1] > -1.2) & strip] = LETTER_COLOR     # the engraved name
    scene = by_color([(ft, figure_colors(ft, sp)), (bt, bc)])
    return scene


def chomper_scene(path, color):
    t = trimesh.load(path)
    return by_color([(t, np.tile(np.array(color, np.uint8), (len(t.faces), 1)))])


def save(scene, name):
    lo, hi = scene.bounds
    scene.apply_translation(-(lo + hi) / 2)                         # centred on the origin, in mm
    path = os.path.join(OUT, name + ".glb")
    scene.export(path)
    print(f"{name}.glb  {os.path.getsize(path) // 1024} KB")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sprites = json.load(open(os.path.join(HERE, "sprites.json")))
    only = sys.argv[1:] or None
    for name, sp in sprites.items():
        if sp.get("rarity") in (None, "extra") or (only and name not in only):
            continue
        save(figure_scene(name, sp), FILES.get(name, name.lower().replace(" ", "-").replace("-03", "03")))
    if not only:
        save(chomper_scene(os.path.join(HERE, "..", "trex_chomper.stl"), (95, 180, 95)), "trex-chomper")
        save(chomper_scene(os.path.join(HERE, "..", "blip_chomper.stl"), (160, 130, 225)), "blip-chomper")
