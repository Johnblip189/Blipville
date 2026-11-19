# 🎟️ Merch codes

Physical Blipville merch comes with a code like `AEGIS-CHR-7K3M-9QPA`. Players type it in the 🔑 Secret code box
(Windows: right-click a pet → ⭐ Secret code; website: ? → 🔑) to unlock that merch's skin.

| Prefix | Unlocks |
|---|---|
| `REX-GRN` | T-Rex: Classic Dino Green (saved now; the T-Rex itself arrives in a later update) |
| `REX-MAG` | T-Rex: Awakened Volcanic (same) |
| `REX-SLV` | T-Rex: Mecha / Fossil Silver (same) |
| `AEGIS-CHR` | Silvertear-03 + her merch-only **Mirror Chrome** color |

## Making a batch

```
python3 tools/merch_codes.py AEGIS-CHR 200
```

* The codes go to `merch/private/codes-….csv`. That folder is git-ignored: print the codes on labels and keep the file private.
* Their fingerprints are added to `merch-codes.json`. Commit and push it to **main**: the game reads it online, so the new
  codes work right away, with no update.

## How it's protected

* The game and the repo never contain a code, only a slow fingerprint (PBKDF2-SHA256, 60,000 rounds). With 8 random
  letters per code, guessing codes from the fingerprints would take months of computer time, not minutes.
* A code works once per town (it's remembered in the save and in save codes) and once per browser on the website.
  Without a server nothing can stop the same code being typed into two different towns, so keep codes on the inside of
  the packaging.
* Adding a new prefix: add it to `MERCH` in `blip.pyw` (and the skin, if it's in the game already), then re-export the
  website data with `python3 tools/export_go_data.py`.
