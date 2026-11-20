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

**Engineering:** only three skeletons are needed.
- **Torso core:** the spring-loaded push-button head, shoulder ports, and outward-flaring hip ratchets.
- **Arm frame:** shared by Tricera and Ptera. It folds emblem → bot → arm, with a 360° bicep swivel and a 90° elbow.
- **Leg frame:** shared by Stego and Brachio, with a 360° thigh swivel, a 90° knee and flip-out toe/heel stabilizers.

Only the snap-on dino face panels differ between the two arms and between the two legs.

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
3. **Full triple change** on the three skeletons: folding, swivels, ratchets, the spring head and the stabilizers.
   Prototype one skeleton at a time and test-print it before building on it.

## How each Blip folds (no extra parts: each robot mode contains its own limb)
`tricera_three_modes.png` shows Tricera-Shield going emblem → mini-bot → left arm.

- **Arm frame (Tricera-Shield, Ptera-Blade)**

  | Form | What happens |
  |---|---|
  | Emblem | The face in front, the bot folded flat behind it |
  | Mini-bot | The face splits into chest and shoulder pieces (Tricera's frill becomes shoulder shields, Ptera's crest becomes wing panels), the legs swing down and the head pops up |
  | Arm | The bot's two legs lock together as the upper arm and its chest becomes the forearm, with the face out front as the shield or blade. The head tucks into the chest, the bot's arms fold flat on the sides and a hand folds out. The bot's waist and hip joints become the bicep swivel and the elbow |

- **Leg frame (Stego-Stomp, Brachio-Pillar)**
  - The bot's legs lock together as the shin and its torso becomes the thigh.
  - The bot's arms fold flat and its feet fold out into the stabilizer feet.
  - The face ends up as the shin armor plate.
  - The bot's hip becomes the thigh swivel and its knee becomes the robot's knee.
- **Torso (Tyranno-King)**
  - The bot's legs fold up into the hips (the leg sockets) and its arms fold back into the shoulder ports.
  - The face stays as the chest emblem, and the crowned head springs up out of the shoulders.
