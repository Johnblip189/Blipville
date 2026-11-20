# 🦖 Amber Age X skeletons (prototype)

`python3 merch/fossil-squad/make_skeletons.py` rebuilds everything and re-runs the fit checks.

| File | Print | What it is |
|---|---|---|
| `arm_frame.stl` | ×2 | Tricera-Shield and Ptera-Blade: chest, two legs, head, two arms (6 parts) |
| `leg_frame.stl` | ×2 | Stego-Stomp and Brachio-Pillar: the same bot plus a thigh socket, a head pocket and two flip-out toe plates (8 parts) |
| `torso_frame.stl` | ×1 | Tyranno-King: torso, flip-up head, two fold-up mini-bot legs, two arms, two shoulder axles, two hip pegs (10 parts) |
| `face_*.stl` | one each | The five Blip faces (voxel relief); each spins on a filament pin |

Every part is already laid out in its print orientation, with no supports. The only overhangs are the tops of small
pin holes, which bridge fine. Print in PLA, 0.12–0.16 mm layers for the small parts, 3 walls. Combined, Amber Age X
is about 11 cm tall.

## Pins
- **Hinges:** cut 1.75 mm filament into pins. Push one through each hinge and trim it flush. The holes are 1.8 mm, so
  the fit holds a pose by friction. If a hole is tight, run a 1.8 mm drill through it.
- **Face panels:** each face spins on a short filament pin pushed into the centre of the chest.
- **Shoulder axles and hip pegs:** the printed 5 mm pins. They press into the torso and turn in the limbs' 5.2 mm
  holes, which is the 360° swivel.

| Bot | Hinge pins |
|---|---|
| Limb bot | 5: hip, head, two arms, face; plus two toe pins on a leg frame |
| Torso | 5: head, mini-bot legs, two arms (share one pin per side), face |

## Modes
| Mode | How |
|---|---|
| Emblem | Swing the legs back and up behind the chest and fold the head back on top of them. Only the face shows. |
| Mini-bot | Legs down, head up. |
| Arm | Turn the bot upside down. The legs are now the upper arm and the chest the forearm. Spin the face on its pin so it's upright. The head is the fist. Slide both feet onto the torso's shoulder axle: that locks the legs together and is the 360° bicep swivel. The hip hinge is the elbow. |
| Leg | The bot stands as it is (chest = thigh, legs = shin). Fold the head down into the pocket in the back of the chest, push the chest's top socket onto a torso hip peg (the 360° thigh swivel) and flip the toe plates down. The hip hinge is the knee. |
| Torso | Fold the mini-bot legs up behind and swing its arms up into gold shoulder pauldrons. Flip the crowned head up. |

## Checked in the model
- Every part, in every mode, is clear of every other part.
- The full Amber Age X combine is clear.
- The axles and pegs sit in their holes.

Still to come:
- the spring-loaded push-button head (it's a manual flip-up for now);
- the hip ratchets;
- the face splitting into shoulder plates.

Test-print one arm frame first.
