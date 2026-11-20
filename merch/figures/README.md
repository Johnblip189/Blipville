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
paws. Legs are stubby Blip feet under the body, so the whole sprite is there.

**Printing:** each STL is one plate:
- the figure on its back;
- two arms and two legs (a left and a right leg: the toes point the other way);
- two flat **shoulder keys**;
- **6 snap pins:** 3 big ones for the hips and 3 small ones for the shoulders, including one spare of each.

No supports. PLA, 0.2 mm layers, 3 walls, 15–20% infill. Keep the pins and keys lying flat, as they are: that's what
makes their springy ends strong.

**💪 Shoulders, Marvel Legends style (but small):** each shoulder has two joints. The **swivel** at the body swings the
arm forward and back, all the way round. The **hinge** at the top of the arm lifts it out to the side and all the way up.
The whole joint sits within about 7 mm of the body.

**🔒 Putting it together** (every pin clicks in and can't come back out, so check left and right first):
1. **Shoulder keys:** push each key's pointed peg into a shoulder hole until it clicks. The flat round end sticks out.
2. **Arms:** slide the slot in the top of the arm over the key's round end, then push a **small** pin through from the
   front until it clicks out the back.
3. **Legs:** push a **big** pin through the leg from the outside (the head drops into the pocket), hold the leg against
   the little tab under the body (toe forward) and press until the pin clicks out on the tab's inner side.

See `joint_lock_cutaway.png` for how a pin locks. Everything holds its pose by friction: the arms swivel all the way
round and lift from hanging straight down to straight up, and the legs swing about 60° back and 90° forward.

**Tips:**
- **A pin too hard to push in:** press with a flat tool (the back of a pen), or sand the barb's slope a little.
- **A pin breaks:** use a spare.
- **A joint that ends up loose:** a drop of thick glue on the shaft sets it in a pose for good.
- **Settings to tweak** are at the top of `make_figures.py`:
  - `BODY_HOLE` (friction: bigger is looser);
  - `BARB_W` (how hard it locks: keep it under `BODY_HOLE + SLOT`).
