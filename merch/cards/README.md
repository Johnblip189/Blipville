# 🃏 Collectible cards (Series 1)

One card goes in every mystery box. `python3 merch/cards/make_cards.py` rebuilds everything from the game data.

**Size:** 48 × 56 mm trim with rounded 3 mm corners, so it lies flat inside the 52 × 52 × 60 mm box. Each file has
3 mm bleed on every side and is 300 dpi. Keep text 2.5 mm inside the trim.

**Fronts:**
- `*_front.png`: the 3 basic boxes of each Blip.
  - Night-sky card with the Blip big in a glowing window and its number (#1/6 … #6/6).
  - Name banner, bio, and "★ SERIES 1 · n OF 6 ★".
- `*_chrome_front.png`: the 2 chrome boxes of each Blip (the chase cards).
  - Holographic silver foil with the Blip in chrome.
  - A CHROME! burst and "✦ CHROME · ONLY 2 OF EACH ✦".

**Back:** `card_back.png`, shared by every card.
- The collect-them-all checklist, with Basic / Chrome tick boxes for each Blip.
- The free in-game color panel with a white box for the code.
- The site, the Discord and the small-parts warning.

**Coded backs (private):** if `merch/private/series1-codes.csv` is there (it is never committed), the script also writes
one back per card with its code printed in the box. They go to `merch/private/card_backs/`, named like
`blip_1_chrome_back.png`; copies #1–2 of each figure are the chrome ones. Print each front on the back of its matching
coded back.

**Other files:**
- `dieline.png`: cut line (red, rounded corners), safe area (green), bleed (blue). It's a guide for the printer, not
  part of the art.
- `cards_preview.png` / `chrome_cards_preview.png`: the cards as they'll look once cut.
