# 🧸 Blipville figures: Series 1

Posable figures built straight from the game sprites (`python3 make_figures.py` rebuilds them all;
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

**The look:** a soft vinyl-toy body about 40 × 37 × 16 mm. The sprite's pixel outline gets slightly rounded corners and the
front swells into a smooth dome. The sprite's details are carved into it: sunk eyes and mouth, grooves for inner outlines,
raised bellies, teeth and highlights, and a recessed visor with the eyes standing out. Arms are rounded, with mitten hands
and a thumb. Legs are chunky boots.

**Printing:** each STL is one plate: the figure on its back, two arms and two legs (a left and a right: the toes point the
other way). No supports. PLA, 0.2 mm layers, 3 walls, 15–20% infill.

**🔒 Locking joints:** every limb has a split snap peg with a barb on the end. Push it firmly into its hole (arms into the
shoulders, legs into the hip notches from the side, toes forward). You feel a click as the barb squeezes through and opens
up in a chamber inside the body. After that it **can't be pulled back out**, so check left and right before you click it
in. See `joint_lock_cutaway.png`. Once in, arms turn all the way round (Wendigo's stop at about 135°, against its antlers) and legs swing about 80° each way. The shaft is a
snug fit, so every joint holds its pose by friction.

**Tips:**
- **A peg too hard to push in:** sand the barb's slope a little.
- **A joint that ends up loose:** a drop of thick glue on the shaft sets it in a pose for good.
- **Settings to tweak** are at the top of `make_figures.py`:
  - `SHAFT_D` (friction);
  - `BARB_D` (how hard it locks: keep it under `HOLE_D + SLOT`).
