# 🏛️ Series 2: House of Myths (planned)

Series 1 is "The Beginning" (set in merch/series.json). Series 2 waits on how Series 1 sells; the quantities below are still open.

## Lineup
| Blip | Role |
|---|---|
| Mothman | regular figure (basic + chrome) |
| Kitsune | regular figure (basic + chrome) |
| Qilin | regular figure (basic + chrome) |
| Nessie | regular figure (basic + chrome) |
| Lurker | **secret figure**: shown only as a ??? silhouette on the box and checklist (its odds printed on the box) |
| Mythkeeper | **code-exclusive Blip**: not a figure; a special code card in *some* boxes unlocks it in the game |

`myths_preview.png` shows the lineup as voxel figures (from the game sprites; it also has the two Blips that were
considered and dropped).

## Mythkeeper
A new Blip: a hooded keeper with glowing gold eyes and a little lantern who guards the House of Myths.
- The sprite and palette are in `mythkeeper.json`, in the same format as `merch/figures/sprites.json`.
- `mythkeeper_preview.png` shows it as the game sprite and as a voxel figure.
- In the game it gets added hidden, like a parked Blip, and the only way to unlock it is its merch code.

## Still to decide (after Series 1)
- How many of each regular figure, and how many of those are chrome. Series 1 was 5 each, 2 of them chrome.
- How many secret Lurkers.
- How many boxes get a Mythkeeper code (for example 1 in 5).
- The box color. The idea is deep green and gold, so the two series are easy to tell apart.

## To build when it's time
1. Set `merch/series.json` to Series 2 / House of Myths (the cards and box read it; update the site text to match).
2. Mythkeeper in the game: a hidden kind, a merch prefix and codes, and the in-game unlock.
3. Figures and bases (`merch/figures`), cards with a ??? card for the Lurker (`merch/cards`), the box with the real
   odds (`merch/box`), and a House of Myths section on the website.
4. Touch-ups:
   - Anubis would need brighter eyes, but it isn't in the lineup any more.
   - Mothman and the Lurker are very dark, which suits their chrome versions.
