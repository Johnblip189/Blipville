"""🌐 Colored 3D models of the merch for the website's viewer (docs/merch/models/*.glb).

    python3 merch/figures/make_web_models.py          (needs what make_figures.py needs)

Each figure is put together standing on its base, voxel style like the Blipville 3D viewer, painted with the sprite's
colors (one mesh per color, so the files stay small). The chompers are one color.
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


def letter_color(pal, ch):
    """A sprite letter's color: lowercase from the palette, uppercase = its shade, * = a highlight, f = feet."""
    if ch == "f":
        return hexrgb(pal.get("f", pal["o"]))
    if ch in pal:
        return hexrgb(pal[ch])
    if ch == "*":
        main = max((k for k in pal if len(k) == 1 and k not in "oe"), key=lambda k: 0, default="o")
        return tuple(min(255, int(v * 1.25 + 30)) for v in hexrgb(pal.get("b", pal[main])))
    low = ch.lower()
    if low in pal:
        return tuple(int(v * 0.78) for v in hexrgb(pal[low]))
    return hexrgb(pal["o"])


def figure_colors(t, sp, front):
    """Like the viewer: the front face shows the sprite (eyes, glints, mouth), everything else the pixel's own color."""
    pal = sp["colors"]
    g = F.grid(sp)
    eyes, glint, mouth = F.face_cells(sp)
    eye = hexrgb(pal.get("e", "#111111"))
    lum = 0.299 * eye[0] + 0.587 * eye[1] + 0.114 * eye[2]
    shine = hexrgb(pal["o"]) if lum > 150 else (255, 255, 255)
    c, n = t.triangles_center, t.face_normals
    out = np.zeros((len(c), 3), np.uint8)
    for i in range(len(c)):
        x, y = int(c[i, 0] // F.V), F.ROWS - 1 - int(c[i, 1] // F.V)
        x, y = min(max(x, 0), F.COLS - 1), min(max(y, 0), F.ROWS - 1)
        ch = g[y][x] or "o"
        col = letter_color(pal, ch)
        if front and n[i, 2] > 0.5 or front and (x, y) in eyes | mouth:
            if (x, y) in glint:
                col = shine
            elif (x, y) in eyes or (x, y) in mouth:
                col = eye
        out[i] = col
    return out


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


def voxel_mesh(sp, sink):
    """The figure exactly like the 3D viewer: one cube per voxel (only outside faces), the front-most cube of each column
    showing the sprite (eyes, glint, mouth), the rest the pixel's own color."""
    pal = sp["colors"]
    g, d = F.grid(sp), F.depth_map(F.grid(sp))
    eyes, glint, mouth = F.face_cells(sp)
    eye = hexrgb(pal.get("e", "#111111"))
    shine = hexrgb(pal["o"]) if 0.299 * eye[0] + 0.587 * eye[1] + 0.114 * eye[2] > 150 else (255, 255, 255)
    vox = {}
    for y in range(F.ROWS):
        for x in range(F.COLS):
            if not g[y][x]:
                continue
            h = d[y][x]
            base_col = letter_color(pal, g[y][x])
            face = shine if (x, y) in glint else eye if (x, y) in eyes or (x, y) in mouth else base_col
            for k in range(-h + 1, h + 1):
                vox[(x, y, k)] = face if k == h else base_col
    V = F.V
    verts, faces, cols = [], [], []
    dirs = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]), ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
            ((0, -1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]), ((0, 1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
            ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]), ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)])]
    for (x, y, k), col in vox.items():
        X0, Y0, Z0 = x * V, (F.ROWS - 1 - y) * V - sink, (k - 1) * V
        for (dx, dy, dz), quad in dirs:
            if (x + dx, y + dy, k + dz) in vox:                          # (grid y grows downward)
                continue
            b = len(verts)
            for qx, qy, qz in quad:
                verts.append((X0 + qx * V, Y0 + (1 - qy) * V if dy else Y0 + qy * V, Z0 + qz * V))
            faces += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
            cols += [col, col]
    m = trimesh.Trimesh(vertices=np.array(verts, float), faces=np.array(faces), process=False)
    m.fix_normals()
    return m, np.array(cols, np.uint8)


def figure_scene(name, sp):
    _, _, b = F.assembled(sp, name)
    fig, fc = voxel_mesh(sp, F.POCKET)
    bt = F.to_trimesh(b)
    bc = np.tile(np.array(BASE_COLOR, np.uint8), (len(bt.faces), 1))
    c, n = bt.triangles_center, bt.face_normals
    floor = (n[:, 1] > 0.5) & (c[:, 1] < -0.3) & (c[:, 1] > -1.0)               # engraved floors (and the foot pockets)
    strip = (np.abs(c[:, 0] - F.COLS * F.V / 2) < 18) & (c[:, 2] < F.SPLIT_Y - 1.5)
    front_of_feet = c[:, 2] > max(hd for _, _, hd in F.footprint(sp)) + 1.0
    bc[floor & strip & front_of_feet] = LETTER_COLOR
    return by_color([(fig, fc), (bt, bc)])


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
