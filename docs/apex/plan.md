# Apex Nexus: the 5-Core Hunt (permanent questline, 1.1)

Replaces the scrapped Speedster event. It is **permanent** (always there, no dates), **chapters at your own pace**, and the
rewards are **new Blips**. It runs on the new real-time battle system (`go/fight.js`), so it ships with that (1.1), not 1.0.x.

Everything below marked **(proposal)** is my guess, not decided.

## The hunt
Five Cores. Each one is a chapter. Each unlocks a weapon for the real-time fights.

| # | Core | Where | Trial | Weapon |
|---|------|-------|-------|--------|
| 1 | Obsidian | Town Workshop Vault | Win 3 Arena matches with a tech Blip | Solar-Edge Greatsword |
| 2 | Crimson | Volcano / Magma Ridge | Land 15 ranged hits in one match, then defeat the rogue Crimson Drone | Dual Magma Pistols |
| 3 | Cobalt | Ocean / Sunken Ruins | Win an Ocean or Ice Arena fight taking under 30% damage | Double-Sided Glacial Trident |
| 4 | Amber | Desert / Sandstone Temple | Land 10 heavy guard-breaks or slams | Twin Grappling Wrecking-Maces |
| 5 | Emerald | Dino World / Prehistoric Canopy | Dodge or counter 8 attacks in one match | Boomerang Shield and Twin Daggers |

Progress is saved as `saveData.apexNexusCores` (the list of Cores you hold), plus a small counter per trial.
It travels in the save code like the other lists.

## Center-Switch Rotation (proposal)
A button in the middle of the fight pad that cycles through the weapons you hold (starts with only the Obsidian
Greatsword once Chapter 1 is done). Each weapon replaces the light, heavy and special moves, so it changes how a Blip fights.
Computer fighters never use them.

## What the engine already has, and what it still needs
`go/fight.js` already records: `guardBreaks`, `counters`, `heavyHits`, `specialHits`, `taken`, `damage`, wins and KOs.

Needs adding:
- **ranged hits** (a stat counting every projectile or pistol hit that lands)
- **dodges** (a stat for a dash or jump that makes an attack miss)
- **slams** (a heavy or air-down hit that lands while the foe is grounded)
- **weapon move sets** (reach, speed, damage, projectiles) in `MOVES`, all untuned first guesses
- **stages**: Volcano / Magma Ridge does not exist yet. Ocean (Ocean World), Desert (Egypt World) and Dino (Dino World) do.
  Worlds that are still locked would need to be unlocked to take the trial (Egypt World is free).
- **Crimson Drone**: a boss-style computer fighter (level 2 AI) for Chapter 2
- **tech Blips** (Chapter 1): needs a rule for which Blips count (proposal: the Robots, plus anything with a spark or cosmic type)

## Rewards: new Blips (proposal, 5 of them, original)
One per Core, unlocked when you finish the chapter. Names are placeholders:
Obsidian Smith, Crimson Drone (adopt the boss after you beat it), Cobalt Skipper, Amber Mason, Emerald Ranger.
Finishing all five could add a sixth (a "Nexus" Blip). Not decided.

## Not decided yet
1. The 5 reward Blips: names, look, or do you want to pick?
2. Weapon system: is the Center-Switch button what you meant?
3. Volcano / Magma Ridge: new stage, or hide it inside Dino World?
4. Heart rewards per chapter: none for now (rewards are Blips only).

## Rules
Original designs only, nothing from other games. No gameplay balance numbers get tuned without the developer.
