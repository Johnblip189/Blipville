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
raised bellies, teeth and highlights, and a recessed visor with the eyes standing out. Arms are short, soft Blip nubs with round
paws. Legs are chunky boots.

**Printing:** each STL is one plate:
- the figure on its back;
- two arms and two legs (a left and a right leg: the toes point the other way);
- two **shoulder yokes** (the small forked pieces);
- **8 snap pins:** 5 long and 3 short, including one spare of each.

No supports. PLA, 0.2 mm layers, 3 walls, 15–20% infill. Keep the pins lying flat and the yokes standing on their
edges, as they are: that's what makes them strong.

**💪 Shoulders, Marvel Legends style:** each shoulder has two joints. The **swivel** at the body swings the arm forward
and back, all the way round. The **hinge** in the yoke lifts the arm out to the side and all the way up. Combine them
for flexing, waving, flying and so on.

**🔒 Putting it together** (every pin clicks in and can't come back out, so check left and right first):
1. **Shoulders:** push a **short** pin into a yoke from its fork side (the head drops into the pocket between the
   prongs, flat sides lined up) and press the yoke onto the body's shoulder hole until it clicks.
2. **Arms:** slide the arm's thick top end into the yoke's fork, then push a **long** pin through the fork from the
   front until it clicks out the back.
3. **Legs:** push a **long** pin through the leg from the outside (the head drops into the pocket), hold the leg in its
   hip notch with the toe forward and press until it clicks.

See `joint_lock_cutaway.png` for how a pin locks. Everything holds its pose by friction: the arms swivel all the way
round and lift from hanging straight down to straight up, and the legs swing about 80° each way.

**Tips:**
- **A pin too hard to push in:** press with a flat tool (the back of a pen), or sand the barb's slope a little.
- **A pin breaks:** use a spare.
- **A joint that ends up loose:** a drop of thick glue on the shaft sets it in a pose for good.
- **Settings to tweak** are at the top of `make_figures.py`:
  - `BODY_HOLE` (friction: bigger is looser);
  - `BARB_W` (how hard it locks: keep it under `BODY_HOLE + SLOT`).
