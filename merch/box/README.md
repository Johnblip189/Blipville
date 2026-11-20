# 📦 Series 1 mystery box

A reverse-tuck-end box, 52 × 52 × 60 mm. It holds one glued figure, its base, the code card and a little crinkle paper.
`python3 make_box.py` rebuilds everything from the game sprites and the card art.

| File | What it's for |
|---|---|
| `box_cut_template.svg` | Die line at 1:1 (red = cut, blue dashed = fold). For a cutting machine, or print it and cut with a craft knife. |
| `box_print.png` | The artwork on an A4 page at 300 dpi with 3 mm bleed, with the cut and fold lines drawn on. |
| `box_print_clean.png` | The same artwork with no lines, for print-then-cut machines (line it up with the SVG). |
| `box_panels/` | Each printed face on its own. |
| `mystery_box.glb` | The folded box as a 3D model with the art on it. |
| `box_preview.png` | Renders of the 3D model. |

**Making one:**
1. Print at 100% (no "fit to page") on 250–300 gsm card. The sheet fits A4 and US Letter.
2. Cut along the red lines.
3. Score the blue fold lines with a blunt edge, then fold.
4. Glue the narrow flap inside the front panel's edge.
5. Tuck the bottom lid in. Add the figure, base, code card and crinkle paper, then tuck the top lid.
6. A small sticker across the top lid shows it hasn't been opened.

**What's on it:**

| Panel | Contents |
|---|---|
| Front | Logo, mystery silhouette with a glowing "?", and a CHROME CHASE! burst. |
| Right side | Collect-all-6 lineup as silhouettes. |
| Back | Basic / Chrome checklist and the free in-game color note. |
| Left side | Find a Chrome! and the odds (each figure 1 in 6, chrome 2 in 5). |
| Top | Open here. |
| Bottom | Price, contents, site, Discord and the small-parts warning. |

The price and the odds are at the top of `make_box.py` and in `bottom_panel` / `chrome_panel`.
