# 🧸 Blipville figures: Series 1

Display figures built straight from the game sprites, each on its own base (`python3 make_figures.py` rebuilds them all;
`python3 make_figures.py sprites.json Blip` rebuilds one).

| Figure | Rarity | File |
|---|---|---|
| Silvertear-03 | ⭐⭐⭐ ultra-rare | `silvertear03_figure.stl` |
| Blip | ⭐⭐ rare | `blip_figure.stl` |
| T-Rex | regular | `trex_figure.stl` |
| Wendigo | regular | `wendigo_figure.stl` |
| Bun | regular | `bun_figure.stl` |
| Beta Buddy | regular | `beta_buddy_figure.stl` |

Extras (not in the series yet): `robo_bear_figure.stl`, `boo_figure.stl`, `spike_figure.stl`.

**The look:** the Blip's whole sprite as a soft vinyl-toy body, about 40 × 30 × 16 mm. The pixel outline gets slightly
rounded corners and the front swells into a smooth dome. The sprite's details are carved into it:
- sunk eyes and mouth;
- grooves for inner outlines;
- raised bellies, teeth and highlights;
- a recessed visor with the eyes standing out.

**The base:** a rounded plinth, about 46 × 30 × 6 mm, with the Blip's name and rarity stars engraved along the front.
A teardrop-shaped peg fits a matching hole in the figure's bottom, so it stands upright facing forward and can't spin.

**Printing:** each STL is one plate with two parts, the figure (lying face up) and its base. No supports. PLA, 0.2 mm
layers, 3 walls, 15–20% infill. Print the base in a contrasting color, or paint the engraved name, to make it pop.

**Putting it together:** press the figure down onto the peg. It's a snug fit; a drop of glue makes it permanent.

**Settings to tweak** (at the top of `make_figures.py`):
- `PEG_D` / `HOLE_D`: the peg fit (bigger gap is looser);
- `BASE_D`, `BASE_H`, `TEXT_H`: the base's size and lettering.
