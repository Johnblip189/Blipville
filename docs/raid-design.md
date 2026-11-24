# Raid boss (1.1 design notes)

Decisions so far (from the developer):

- **Spawn:** a normal randomly timed spawn, like kaiju and cryptids. It rolls once an hour with a **20% chance** to appear.
- **Guardians:** the boss has **7 guardians (Wardens)**. They are beaten first, then the boss unlocks.
- **Battles:** the redone battle system is **real time** (not the turn-based 1.0 Arena).
- **Multiplayer:** **peer-to-peer (WebRTC)**, no server and no broker. The host sends a long invite code and each friend sends a reply
  code back (copy and paste, like save codes). The host runs the fight and sends state to the guests. Solo play always works.
- **Safety:** WebRTC shows players' IP addresses to the others in the room, so joining needs a notice first.
- **Originality:** all Wardens, the boss and the quests are new designs. Nothing is taken from other games.

Still to decide: how long the alert stays up (suggested 10 minutes), the hearts rewards (solo vs room), the controls of the new battle system.

Build order: 1) the connection layer (invite/reply codes, a two-browser test screen), 2) the raid alert and spawn timer, 3) Wardens and boss on top of the new battle system.

## Next event after Spiky Week: the Speedsters

- The next event is a **speedster** recruitment event (the quest chain from the developer's draft JSON: four recruitable fast Blips with
  heart rewards, plus the Hydro-style evolution tiers and the dojo mastery quest).
- The Speedsters must be **original** characters and names. The draft's names and the `SONIC_RECRUITMENT` category are placeholders only.
- Its objectives (air hits, dash hits, guard breaks, counters) need the new real-time battle system, so the event follows it.
- Spiky Week runs until December 3.

## Real-time battle engine (started)

`go/fight.js` is the engine: a deterministic sim (60 steps a second) with light/heavy/air attacks, dash, guard with a parry window,
guard breaks, a projectile special, an awakening meter and stocks. It records the stats the quests need (air hits, heavy hits, dash
hits, guard breaks, parries, blocks, awakenings, KOs, combos). Computer fighters have 3 levels. All numbers are in `BAL` and `MOVES`
at the top of the file and are **untuned first guesses**.

Try it: creator menu (🛠️) → ⚔️ New battle (beta). It is not visible to players. Next: wardens/boss on top of it (extra fighters,
big HP, phases), then the peer-to-peer rooms (the host runs `FIGHT.step`, guests send buttons and receive state).

## Speedster sprites (draft, awaiting approval)

Four original recruitable Speedsters, drawn in the game's 16 x 12 sprite format with 3 colors each: **Whippet** (lightning-brow
dog), **Peregrine** (swift falcon), **Sprinter** (swept-horn gazelle) and **Racer** (striped racing lizard). Source:
`docs/speedsters/sprites-draft.js`, preview: `docs/speedsters/preview.png`. Not in the game yet.

## Speedster concept sprites (developer-approved exception)

The developer chose to use the original JSON concepts (Rotor-Kit, Rose-Mallet, Pyre-Lynx, Chrono-Quill) for the Speedster event, as a
**one-time exception** to the "everything stays original" rule. Draft sprites with 3 colors each: `docs/speedsters/sprites-concepts.js`
and `preview-concepts.png`. In data and UI the category is called `SPEEDSTER_RECRUITMENT` (no outside franchise names). The earlier
original four (Whippet, Peregrine, Sprinter, Racer) are kept in `sprites-draft.js` as spares.

## The other four Speedster roles (original designs)

Roster roles from the developer: a starter speedster (Gilded Form → Overdrive), a dark rival with 3 Eclipse awakenings
(Crimson / Azure / Radiant), a chrome robot rival (Neo-Alloy → Meltdown) and a water elemental with 4 skin tiers (0 / 2 / 4 / 6).
These four are drawn as **original** Blips so the roles are covered: **Comet Hare**, **Eclipse Panther**, **Mirror Mech** and
**Tidecore** (`docs/speedsters/sprites-originals.js`, `preview-originals.png`). Drafts only, not in the game yet.

## Speedster roster (final naming: the franchise names were only to explain the inspiration)

Dash-Quill (starter), Eclipse-Quill (3 Eclipses), Chrome-Quill, Rotor-Kit, Rose-Mallet, Pyre-Lynx, Chrono-Quill, Hydro-Core (4 tiers).
Drafts: `sprites-quills.js` (Dash/Eclipse/Chrome-Quill), `sprites-concepts.js` (Rotor-Kit, Rose-Mallet, Pyre-Lynx, Chrono-Quill) and
the droplet in `sprites-originals.js` (drawn as "Tidecore", use it as **Hydro-Core**). Comet Hare, Eclipse Panther, Mirror Mech and
the first four originals are spares.
