# 🧸 Blipville figures: Series 1

Voxel figures in the style of the Blipville 3D viewer, each on its own display base. To rebuild:
- all of them: `python3 make_figures.py`;
- one: `python3 make_figures.py sprites.json Blip`;
- the website's 3D models: `python3 make_web_models.py`.

| Figure | Rarity | File |
|---|---|---|
| Silvertear-03 | regular | `silvertear03_figure.stl` |
| Blip | regular | `blip_figure.stl` |
| T-Rex | regular | `trex_figure.stl` |
| Wendigo | regular | `wendigo_figure.stl` |
| Bun | regular | `bun_figure.stl` |
| Beta Buddy | regular | `beta_buddy_figure.stl` |

Extras (not in the series yet): `robo_bear_figure.stl`, `boo_figure.stl`, `spike_figure.stl`.

**The look:** the game sprite, feet included, turned into chunky 2.5 mm cubes, exactly like the 3D viewer. Each pixel
is a column of cubes: 8 deep in the middle, thinner toward the edges, the same front and back, like a plush toy. The figure
is about 40 × 32 × 20 mm. The eyes and mouth are carved into the front, and each eye keeps a raised glint in its corner.

**Printing:** each STL is one plate with 5 parts, all with no supports. PLA, 0.2 mm layers, 3 walls, 15–20% infill.

| Part | How it prints |
|---|---|
| Front half | On its flat cut face. The face is on this half. |
| Back half | On its flat cut face. It's mirrored on the plate, so it matches once flipped over. |
| Base | Flat. It has foot pockets and the engraved name and rarity stars. |
| 2 small pins | Standing up. They line the halves up for gluing. |

A voxel shape overhangs whichever way it lies, which is why the figure prints as two halves.

**Putting it together:**
1. Push the two pins into the holes on one half's flat face.
2. Glue the halves together. The pins line them up.
3. Glue the feet into the pockets on the base, with the face toward the name.

**Tips:** print the base in a contrasting color (or paint the engraved name) so it pops. A light sanding of the cut
faces before gluing makes the seam disappear.

**Bases on their own:** `bases/*_base.stl` has just the base for each Series 1 figure, for printing in a different color.
