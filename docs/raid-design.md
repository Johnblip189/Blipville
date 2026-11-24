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
