# Real-time battle engine (1.1, beta)

`go/fight.js` is the engine: a deterministic sim (60 steps a second) with light/heavy/air attacks, dash, guard with a parry window,
guard breaks, a projectile special, an awakening meter and stocks. It records the stats the quests need (air hits, heavy hits, dash
hits, guard breaks, parries, blocks, awakenings, KOs, combos). Computer fighters have 3 levels. All numbers are in `BAL` and `MOVES`
at the top of the file and are **untuned first guesses**.

Try it: creator menu (🛠️) → ⚔️ New battle (beta). It is not visible to players. The raid boss and the Speedster event were scrapped
(their notes are in git history, commit 06d92cd and earlier).

The Speedster event was scrapped (its sprites and notes are in git history, commit 328ad87 and earlier).
