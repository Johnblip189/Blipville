# 🦖 Apex Dino-Fossil Squadron (planned)

Five new Blips that are each a triple changer (emblem → mini-bot → combiner part) and combine into one big robot:
**Amber Age X**.
It's its own set, sold alongside Series 1.

| Blip | Colors | Combiner part |
|---|---|---|
| Fossil-01 Tyranno-King | black & gold, dark-blue visor with blue eyes | torso + spring-loaded push-button head with a T-Rex crown crest |
| Fossil-02 Tricera-Shield | blue with a black frill & gold horns | left arm: triple-horn shield gauntlet |
| Fossil-03 Ptera-Blade | gold with a black crest & blue eyes | right arm: crest energy blade |
| Fossil-04 Stego-Stomp | black with blue & gold dorsal plates | left leg: dorsal-plate shin, flip-out foot |
| Fossil-05 Brachio-Pillar | blue with a gold crest & jaw armor | right leg: wide flip-out boot |

**Engineering (current design: shell-formers).**
- Every Blip is a full voxel Blip shell (a front half with the face and a hollow back half) with its robot folded up
  inside, so in Blip mode none of the robot shows.
- To transform you have to split it: the back half pulls off, the legs swing down, and the back half clips back on.
- Only two skeletons are needed:
  - **Limb frame** (all four limb Blips): a chest and two legs, a top socket for the hip joint, and side holes for the
    shoulder axle.
  - **Torso frame** (Tyranno-King): a sliding crowned head, two legs, and holes for the shoulder axles and hip joints.

## Naming and colors
- **The combiner's name: settled.** The combined robot is **Amber Age X**, an original name ("Megazord" is a
  Power Rangers trademark).
- **The colors: settled.** The whole squad shares one gold, black and blue team scheme, mixed differently on each Blip,
  which keeps it clearly Blipville's own and not a red / blue / pink Dinozord look.

## Stages
1. **The five Blips (in progress).**
   - Done: first-pass sprites in `sprites.json` (same format as `merch/figures/sprites.json`) and
     `emblems_preview.png` (the game sprite, plus a voxel figure).
   - Next: refine them, put them in the game, and make voxel display figures.
2. **Non-transforming combiner.** Five chunky voxel parts that snap together, to settle proportions, connections and
   standing balance.
3. **Full triple change: first prototype done** (`make_skeletons.py`, `shells/`, `skeletons/`,
   `instructions/`). Blip → walker → Amber Age X, checked clear in the model.
   - Still to come: the spring-loaded crown, hip ratchets, and knees/elbows.
   - Test-print one limb Blip before building on it.

## How each Blip changes
`limb_modes.png` and `tyranno_modes.png` show it; `amber_age_x_preview.png` shows the combine.

| Form | Limb Blips (Tricera-Shield, Ptera-Blade, Stego-Stomp, Brachio-Pillar) | Tyranno-King |
|---|---|---|
| Blip | Shell closed, robot folded inside | Shell closed, robot folded inside, crown pushed down |
| Walker | Split it, legs down, back half back on: legs stick out underneath | Same, and the crown pulls up out of the hatch on top |
| Amber Age X | Arms hang on shoulder axles through their side holes (swing all the way round). Legs hang on L-shaped hip joints in their top holes (swivel) | The chest: legs folded inside, crown up |

The earlier idea (an open mini-bot with arms and a head, the face splitting into shoulder plates) was replaced by the
shell design on request: "I wanted the whole frame covered by the Blip and then you have to split it to transform it".
