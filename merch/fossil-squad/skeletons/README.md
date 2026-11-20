# 🦖 Amber Age X: printable parts (prototype)

`python3 merch/fossil-squad/make_skeletons.py` rebuilds everything and re-runs the fit checks.

Each Fossil Blip is a voxel Blip shell with a little robot folded up inside. The shell is a front half (the face) and a
back half. **To transform, you have to split it:** pull the back half off, swing the legs down, and clip it back on.

| File | Print | What it is |
|---|---|---|
| `../shells/tyranno_king.stl` | ×1 | Tyranno-King's front and back halves (77 × 58 × 39 mm closed) |
| `../shells/tricera_shield.stl`, `ptera_blade.stl`, `stego_stomp.stl`, `brachio_pillar.stl` | one each | The four limb Blips' halves (46 × 34 × 31 mm closed; Brachio-Pillar is 40 wide) |
| `limb_frame.stl` | ×4 | The robot inside each limb Blip: a chest and two legs |
| `torso_frame.stl` | ×1 | Tyranno-King's robot: the torso, the sliding crowned head, two legs, two shoulder axles and two hip joints |

Every part is laid out in its print orientation, with no supports.
- **Front halves** print face up.
- **Back halves** print rim down. The ceiling inside them bridges (up to about 4 cm on Tyranno-King). A little droop there
  is hidden.

Use PLA, 0.2 mm layers for the shells, 0.12–0.16 mm for the frames, and 3 walls. Combined, Amber Age X is about
11 cm tall and 17 cm wide.

## Pins (1.75 mm filament)
- **Hinges:** the hip of every robot (one pin each). Push a piece through and trim it flush. The holes are 1.8 mm, so the
  pin holds by friction. If a hole is tight, run a 1.8 mm drill through it.
- **The face:** push a short pin into the hole in the chest front (about 3 mm sticking out), then press the front half
  onto it.
- **Rim pins:** glue a 6 mm piece into each of the two holes in the back of the front half, with 3 mm sticking out. The
  back half clips onto them.

## Forms
| Form | How |
|---|---|
| Blip | Shell closed, legs folded up behind the chest inside it. Tyranno-King's crown is pushed down. |
| Walker | Pull the back half off, swing the legs down, and clip the back half on. The legs come out of the notch underneath. On Tyranno-King, pull the crown up out of the hatch. |
| Amber Age X | Tyranno-King's legs stay folded inside and its crown is up. For each leg, the hip joint's short end goes in the leg Blip's top hole, and its long end goes through the slot under Tyranno-King into the hip. The shoulder axles go through Tyranno-King's side holes, and each arm Blip's side hole pushes onto one. |

Left and right as you look at it from the front: Tricera-Shield is the left arm and Ptera-Blade the right arm.
Stego-Stomp is the left leg and Brachio-Pillar the right leg.

## Checked in the model
- Every Blip's robot fits inside its shell in Blip mode, with 0.6 mm clearance and 1.6 mm walls.
- The back half pulls straight off. It also clips back on with the legs down (walker).
- The full Amber Age X combine is clear: every part, axle and joint is clear of everything else.

## Not in yet
- The spring-loaded crown (it slides up by hand for now).
- The hip ratchets.
- Elbows and knees: in this version the legs only fold in and out.

Test-print one limb Blip first: Tricera-Shield's shell and one `limb_frame.stl`.
