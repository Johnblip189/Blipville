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

**Printing:** each STL is one plate: the figure on its back, two arms, two legs (a left and a right: the toes point the
other way) and **6 snap pins** (4 plus 2 spares). No supports. PLA, 0.2 mm layers, 3 walls, 15–20% infill. Keep the pins
lying flat as they are: that's what makes them strong.

**🔒 Putting it together:** for each joint, push a pin through the limb from the outside (the head drops into the
pocket, flat sides lined up with the flats in the hole), then hold the limb against the body (arms at the shoulders,
legs in the hip notches with the toes forward) and press the pin in until it clicks. The pin's split barb squeezes
through the body's wall and opens up in a chamber behind it, so the limb **can't come off** (check left and right
before you click it in). See `joint_lock_cutaway.png`. Arms turn all the way round (Wendigo's stop at about 135°, against
its antlers) and legs swing about 80° each way, holding their pose by friction.

**Tips:**
- **A pin too hard to push in:** press with a flat tool (the back of a pen), or sand the barb's slope a little.
- **A pin breaks:** use a spare.
- **A joint that ends up loose:** a drop of thick glue on the shaft sets it in a pose for good.
- **Settings to tweak** are at the top of `make_figures.py`:
  - `BODY_HOLE` (friction: bigger is looser);
  - `BARB_W` (how hard it locks: keep it under `BODY_HOLE + SLOT`).
