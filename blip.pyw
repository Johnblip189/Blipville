"""Blipville — tiny pixel pets that live on your taskbar (starring Blip).

Run it:   double-click Blipville.exe, or blip.pyw   (or:  python blip.pyw)

  • Blip wanders along the bottom of your screen, naps, and watches your mouse.
  • Click Blip to pet it. Drag it to pick it up — let go to throw it.
  • Right-click for the menu: feed, nap, follow your mouse, change kind/color,
    add friends (more pets!), name tags, rename, quit.

Critters: Blip, Bun (hops), Sprout, Boo (floats), Fuzz (flutters), Spike.
Animals:  Cat, Dog, Fox, Bear, Panda, Pig, Frog (hops), Penguin, Chick, Owl, Mouse,
          Raccoon, Koala, Cow, Axolotl, Hamster, Sheep, Monkey, Lion, Tiger, Bat,
          Hedgehog, Duck, Seal, Sloth, Deer, Octopus, Unicorn, Shark, Wolf, Squirrel, Otter,
          Skunk, Beaver, Capybara, Llama, Horse, Zebra, Elephant, Giraffe, Hippo, Kangaroo,
          Parrot, Flamingo, Bee, Ladybug, Whale, Jellyfish, Dragon — each with its own colors.

Only uses Python's built-in tkinter, nothing to install. Made for Windows; works on
macOS too.
"""
import math
import random
import sys
import time
import tkinter as tk
import webbrowser

# ----------------------------------------------------------------------------- look
SCALE = 4                     # screen pixels per art pixel
W, H = 220, 180               # window size (room for speech bubbles / hearts above Blip)
KEY = "#ff00fe"               # "invisible" color (made transparent on Windows)
FPS = 30

PALETTES = [  # outline, body, belly, cheeks, eyes
    {"name": "Lavender", "o": "#2b1d3a", "b": "#9b7bd8", "l": "#ddd0ff", "p": "#ff8fb3", "e": "#1a1024"},
    {"name": "Mint",     "o": "#1f2d1f", "b": "#74c972", "l": "#d6f5ca", "p": "#ff9f9f", "e": "#0f170f"},
    {"name": "Peach",    "o": "#3a2414", "b": "#f2a65a", "l": "#ffe4c4", "p": "#ff7a7a", "e": "#1d120a"},
    {"name": "Sky",      "o": "#14263a", "b": "#6fb7ff", "l": "#d6eeff", "p": "#ff9fc8", "e": "#0a1320"},
    {"name": "Ghost",    "o": "#3b3f4a", "b": "#e9edf5", "l": "#ffffff", "p": "#ffb0c8", "e": "#20232a"},
    {"name": "Cream",    "o": "#3a2414", "b": "#f4efe6", "l": "#ffffff", "p": "#ffa3b5", "e": "#2a1a10"},
    {"name": "Leaf",     "o": "#1f2d1f", "b": "#a8dc7a", "l": "#e9f8d6", "p": "#ff9f9f", "e": "#132013"},
    {"name": "Moth",     "o": "#3a2a14", "b": "#c9a46a", "l": "#f3e2bf", "p": "#ff9f9f", "e": "#1d140a"},
    {"name": "Dino",     "o": "#14301f", "b": "#4fbf8a", "l": "#d4f5e4", "p": "#ff9fb0", "e": "#0a1a12"},
    {"name": "Night",    "o": "#0c0c14", "b": "#2e2f45", "l": "#55577a", "p": "#ff6f91", "e": "#ffe66d"},
]
PALETTE_INDEX = {p["name"]: i for i, p in enumerate(PALETTES)}

# 16 x 12 bodies. o=outline b=body l=belly p=cheek, plus per-kind extras  (face drawn on top)
FEET_STD = {"stand": "...oo......oo...", "walk1": "..oo........oo..", "walk2": "....oo....oo....", "air": "....o......o...."}
FEET_SLIM = {"stand": ".....o....o.....", "walk1": "....o......o....", "walk2": "......o..o......", "air": ".....o....o....."}
BLIP_LOWER = [
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obpbbbbbbbbbbpbo",
    "obbbbbllllbbbbbo",
    "obbbblllllllbbbo",
    ".obbbllllllbbbo.",
    "..obbbbbbbbbbo..",
]
VARIANTS = {
    "Blip": {
        "body": ["..oo........oo..", ".obbo......obbo.", ".obbbooooooobbo.", ".obbbbbbbbbbbbo."] + BLIP_LOWER,
        "eyes": 5, "feet": FEET_STD, "move": "walk", "palette": "Lavender",
        "lines": ["i'm guarding your desktop", "boop."],
    },
    "Bun": {
        "body": ["...oo......oo...", "..obpo....opbo..", "..obpo....opbo..", "..obbo....obbo..",
                 ".obbbooooooobbo.", ".obbbbbbbbbbbbo.", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo",
                 "obpbbbbbbbbbbpbo", "obbbbbllllbbbbbo", ".obbbllllllbbbo.", "..obbbbbbbbbbo.."],
        "eyes": 6, "feet": FEET_STD, "move": "hop", "palette": "Cream",
        "lines": ["hop hop!", "got any carrots?", "my ears hear everything", "boing!"],
    },
    "Sprout": {
        "body": ["....oo....oo....", "...oggo..oggo...", "....oggootgo....", "......otto......",
                 "....oooooooo....", "..oobbbbbbbboo..", ".obbbbbbbbbbbbo.", "obbbbbbbbbbbbbbo",
                 "obpbbbbbbbbbbpbo", "obbbbbllllbbbbbo", ".obbbllllllbbbo.", "..obbbbbbbbbbo.."],
        "eyes": 6, "feet": FEET_STD, "move": "walk", "palette": "Leaf",
        "extra": {"g": "#6cc96f", "t": "#3e7d43"},
        "lines": ["need... sunlight...", "photosynthesizing!", "is it watering day?", "i'm growing, i can feel it"],
    },
    "Boo": {
        "body": [".....oooooo.....", "...oobbbbbboo...", "..obbbbbbbbbbo..", ".obbbbbbbbbbbbo.",
                 ".obbbbbbbbbbbbo.", "obbbbbbbbbbbbbbo", "obpbbbbbbbbbbpbo", "obbbbbbbbbbbbbbo",
                 "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", ".obbo.obbo.obbo."],
        "eyes": 4, "feet": None, "move": "float", "palette": "Ghost",
        "lines": ["boo!", "did i scare you?", "i'm see-through. sort of.", "ooOOoo~"],
    },
    "Fuzz": {
        "body": ["...o........o...", "....o......o....", ".....oooooo.....", "oo..obbbbbbo..oo",
                 "owwobbbbbbbbowwo", "owwobbbbbbbbowwo", "owwobbbbbbbbowwo", ".oooobbbbbboooo.",
                 "...opbbbbbbpo...", "...obbllllbbo...", "...obllllllbo...", "....obbbbbbo...."],
        "alt": ["...o........o...", "oo..o......o..oo", "owwo.oooooo.owwo", "owwoobbbbbbooowo",
                ".oowobbbbbbowoo.", "...obbbbbbbbo...", "...obbbbbbbbo...", "...obbbbbbbbo...",
                "...opbbbbbbpo...", "...obbllllbbo...", "...obllllllbo...", "....obbbbbbo...."],
        "eyes": 5, "feet": FEET_SLIM, "move": "flutter", "palette": "Moth",
        "extra": {"w": "#fff1c9"},
        "lines": ["ooh, your screen is so bright", "is that a lamp?", "flutter flutter", "*fuzzy noises*"],
    },
    "Spike": {
        "body": ["....s..ss..s....", "...sss.ss.sss...", ".oooooooooooooo.", ".obbbbbbbbbbbbo."] + BLIP_LOWER,
        "eyes": 5, "feet": FEET_STD, "move": "walk", "palette": "Dino",
        "extra": {"s": "#ffcf4d"},
        "lines": ["rawr!", "i am a fearsome beast", "RAWR (that means hi)", "stomp stomp"],
    },
}
KINDS = list(VARIANTS)

# ----------------------------------------------------------------------------- animals
MUZZLE = [
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obpbbllllllbbpbo",
    "obbblllnnlllbbbo",
    "obbbbllllllbbbbo",
    ".obbbbbbbbbbbbo.",
    "..obbbbbbbbbbo..",
]
ANIMALS = {
 "Cat": dict(eyes=5, body=[
    ".o............o.",
    ".oao........oao.",
    ".oaboooooooobao.",
    ".obbbbbbbbbbbbo."] + MUZZLE, colors=[
    dict(name="Orange Tabby", o="#3a1f0e", b="#f2a24b", l="#ffe2bd", p="#ff8f8f", a="#ffb3a7", n="#ff7f8f", e="#1d120a"),
    dict(name="Black",        o="#0e0e14", b="#2b2b36", l="#4a4a5a", p="#ff7f9f", a="#ff9fb5", n="#ff7f9f", e="#e8d84a"),
    dict(name="Gray",         o="#1e2128", b="#9aa1ad", l="#e3e6ec", p="#ff9fb0", a="#ffb3c0", n="#ff8fa3", e="#122018"),
    dict(name="Snow",         o="#4a4a55", b="#f5f5f8", l="#ffffff", p="#ffb0c0", a="#ffc0cc", n="#ff9fb0", e="#3a7bd5"),
    dict(name="Siamese",      o="#2e1d12", b="#f1e3cc", l="#fff6e8", p="#ffb0b0", a="#5a3a24", n="#5a3a24", e="#3a7bd5"),
 ]),
 "Dog": dict(eyes=5, body=[
    "...oooooooooo...",
    "..obbbbbbbbbbo..",
    "oaaobbbbbbbboaao",
    "oaaobbbbbbbboaao",
    "oaaobbbbbbbboaao",
    "oaaobbbbbbbboaao",
    ".oaobbbbbbbboao.",
    "..obbllllllbbo..",
    "..oblllnnlllbo..",
    "..obllllllllbo..",
    "..obbbbbbbbbbo..",
    "...obbbbbbbbo..."], colors=[
    dict(name="Golden",    o="#3a240e", b="#e8b45c", l="#fde3b0", a="#b7782f", n="#2a1a0e", e="#1d120a"),
    dict(name="Chocolate", o="#1e110a", b="#7a4a2a", l="#c9926a", a="#4a2a16", n="#140b06", e="#0b0604"),
    dict(name="Husky",     o="#20242c", b="#7d8796", l="#f2f4f7", a="#3e4552", n="#14161b", e="#4aa3ff"),
    dict(name="Cream",     o="#4a3a26", b="#fff2dc", l="#ffffff", a="#e9c79a", n="#3a2a1a", e="#2a1a0e"),
 ]),
 "Fox": dict(eyes=5, body=[
    ".o............o.",
    ".oao........oao.",
    ".oaboooooooobao.",
    ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "olllbbbbbbbblllo",
    "ollllllnnllllllo",
    ".ollllllllllllo.",
    "..ollllllllllo..",
    "...oooooooooo..."], colors=[
    dict(name="Red",    o="#3a1606", b="#f07a2a", l="#fff4ea", a="#2a1208", n="#1a0a04", e="#1a0a04"),
    dict(name="Arctic", o="#5a6170", b="#eef2f7", l="#ffffff", a="#9aa3b2", n="#2a2e36", e="#2a2e36"),
    dict(name="Silver", o="#1c1e24", b="#5e6470", l="#e6e8ec", a="#22252c", n="#111216", e="#f2c14e"),
 ]),
 "Bear": dict(eyes=5, body=[
    ".ooo........ooo.",
    "oaaao......oaaao",
    "oaaboooooooobaao",
    ".obbbbbbbbbbbbo."] + MUZZLE, colors=[
    dict(name="Brown", o="#24140a", b="#8a5a34", l="#d9b088", a="#c08a5a", n="#1a0e06", p="#e88a7a", e="#120a04"),
    dict(name="Polar", o="#5a6170", b="#f4f6fa", l="#ffffff", a="#d8dde6", n="#1e2128", p="#ffb3c0", e="#1e2128"),
    dict(name="Black", o="#0a0a0e", b="#2a2a32", l="#a88a6a", a="#4a4a55", n="#0a0a0e", p="#c06a6a", e="#d8d8e0"),
    dict(name="Honey", o="#3a2408", b="#f0b84a", l="#ffe6a8", a="#ffd07a", n="#3a2408", p="#ff9a7a", e="#2a1804"),
 ]),
 "Panda": dict(eyes=5, body=[
    ".ooo........ooo.",
    "oaaao......oaaao",
    "oaaboooooooobaao",
    ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo",
    "obbssssbbssssbbo",
    "obbssssbbssssbbo",
    "obpbssbbbbssbpbo",
    "obbbbbbnnbbbbbbo",
    "obbbbbllllbbbbbo",
    ".obbbbbbbbbbbbo.",
    "..obbbbbbbbbbo.."], colors=[
    dict(name="Classic", o="#101014", b="#f7f7f7", l="#ffffff", s="#2a2a32", a="#1a1a20", n="#1a1a20", p="#ffb0c0", e="#000000", f="#1a1a20"),
    dict(name="Red Panda", o="#2a0e04", b="#d2541e", l="#fff1e0", s="#fff1e0", a="#fff1e0", n="#1a0802", p="#ff9f7a", e="#1a0802", f="#1a0802"),
 ]),
 "Pig": dict(eyes=5, mouth=False, body=[
    "..oo........oo..",
    ".oaao......oaao.",
    ".oaboooooooobao.",
    ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obpbboooooobbpbo",
    "obbbondnndnobbbo",
    "obbbbonnnnobbbbo",
    ".obbbboooobbbbo.",
    "..obbbbbbbbbbo.."], colors=[
    dict(name="Pink",  o="#5a2433", b="#ffb6c8", l="#ffd6e0", p="#ff7f9f", a="#ff8fab", n="#ff8fab", d="#5a2433", e="#2a1018"),
    dict(name="Muddy", o="#3a2414", b="#c99a7a", l="#e6c4a8", p="#ff8f8f", a="#a87a5a", n="#e8a0a0", d="#3a2414", e="#1d120a"),
    dict(name="Black", o="#0e0e12", b="#3a3a44", l="#5a5a66", p="#ff7f9f", a="#5a5a66", n="#7a6a72", d="#0e0e12", e="#e8e8f0"),
 ]),
 "Frog": dict(eyes=1, body=[
    "..oooo....oooo..",
    ".obbbbo..obbbbo.",
    ".obbbboooobbbbo.",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obpbbbbbbbbbbpbo",
    "obbbbbbbbbbbbbbo",
    "obbbllllllllbbbo",
    "obbllllllllllbbo",
    "obbllllllllllbbo",
    ".obbbllllllbbbo.",
    "..obbbbbbbbbbo.."], colors=[
    dict(name="Green",  o="#12301a", b="#5ec26a", l="#d6f5c2", p="#ff9f9f", e="#0a1a0e"),
    dict(name="Poison", o="#0c1a3a", b="#2f7fff", l="#9cc8ff", p="#ffdf4a", e="#000000"),
    dict(name="Tree",   o="#123a1a", b="#7bdc4a", l="#fff7e0", p="#ff7a3a", e="#d81e1e"),
 ]),
 "Penguin": dict(eyes=5, mouth=False, body=[
    ".....oooooo.....",
    "...oobbbbbboo...",
    "..obbbbbbbbbbo..",
    ".obbllllllllbbo.",
    ".obllllllllllbo.",
    "obbllllllllllbbo",
    "obpllllllllllpbo",
    "oblllllkklllllbo",
    "obbllllllllllbbo",
    "obbllllllllllbbo",
    ".obbllllllllbbo.",
    "..obbbbbbbbbbo.."], colors=[
    dict(name="Emperor", o="#0a0c12", b="#1e2330", l="#f7f9fc", p="#ffb0c0", k="#ff9a1f", e="#0a0c12", f="#ff9a1f"),
    dict(name="Fairy",   o="#0c1a2a", b="#4a7fc0", l="#f7f9fc", p="#ffb0c0", k="#2a2a2a", e="#0a0c12", f="#ffb0c0"),
    dict(name="Baby",    o="#3a3a44", b="#8a8f9c", l="#e6e8ee", p="#ffb0c0", k="#1a1a1a", e="#0a0c12", f="#3a3a44"),
 ]),
 "Chick": dict(eyes=5, mouth=False, body=[
    "......o..o......",
    ".......oo.......",
    "....oooooooo....",
    "..oobbbbbbbboo..",
    ".obbbbbbbbbbbbo.",
    ".obbbbbbbbbbbbo.",
    "obpbbbbbbbbbbpbo",
    "obbbbbbkkbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    ".obbbbbbbbbbbbo.",
    "..oobbbbbbbboo.."], colors=[
    dict(name="Sunny", o="#5a3a06", b="#ffd93a", l="#fff2a8", p="#ff9f7a", k="#ff8a1f", e="#2a1a04", f="#ff8a1f"),
    dict(name="Duckling", o="#4a3a10", b="#ffe98a", l="#fff7cc", p="#ffb08a", k="#ff9a3a", e="#2a1a04", f="#ff9a3a"),
    dict(name="Brown", o="#2a1808", b="#b07a42", l="#e6c49a", p="#ff9f8a", k="#ffb03a", e="#1a0e04", f="#ffb03a"),
 ]),
 "Owl": dict(eyes=5, mouth=False, body=[
    ".oo..........oo.",
    ".obo........obo.",
    ".obboooooooobbo.",
    ".obbbbbbbbbbbbo.",
    "obbllllbbllllbbo",
    "obbllllbbllllbbo",
    "obbllllkkllllbbo",
    "obbllllkkllllbbo",
    "obbbbbbbbbbbbbbo",
    "obbsbbsbbsbbsbbo",
    ".obbbbbbbbbbbbo.",
    "..obbbbbbbbbbo.."], colors=[
    dict(name="Barn",  o="#3a2410", b="#c8955a", l="#fff3e0", s="#8a5a2a", k="#e8b04a", e="#120a04", f="#e8b04a"),
    dict(name="Snowy", o="#5a6170", b="#f2f4f8", l="#ffffff", s="#7a8494", k="#2a2e36", e="#f2c11e", f="#c8ccd4"),
    dict(name="Night", o="#0c0a1a", b="#3a2e5a", l="#6a5a9a", s="#1e1a30", k="#f2c11e", e="#f2c11e", f="#f2c11e"),
 ]),
 "Mouse": dict(eyes=5, body=[
    "oooo........oooo",
    "oaaao......oaaao",
    "oaaaooooooooaaao",
    ".oobbbbbbbbbboo."] + MUZZLE, colors=[
    dict(name="Gray",  o="#2a2c34", b="#a8adb8", l="#e8eaee", a="#ffb0c0", n="#ff8fa3", p="#ffb0c0", e="#0e0e12"),
    dict(name="White", o="#6a6a76", b="#fafafa", l="#ffffff", a="#ffc0cc", n="#ff8fa3", p="#ffc0cc", e="#d81e3a"),
    dict(name="Brown", o="#2a1a0e", b="#a8784a", l="#e8cfa8", a="#ffb0a0", n="#ff8f8f", p="#ffb0a0", e="#0e0804"),
 ]),
 "Raccoon": dict(eyes=5, body=[
    ".ooo........ooo.",
    "oaaao......oaaao",
    "oaaboooooooobaao",
    ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo",
    "obsssssbbsssssbo",
    "obsssssbbsssssbo",
    "obbllllllllllbbo",
    "obbllllnnllllbbo",
    ".obbllllllllbbo.",
    "..obbbbbbbbbbo..",
    "...obbbbbbbbo..."], colors=[
    dict(name="Classic", o="#14161a", b="#8a8f99", l="#eef0f3", s="#25282e", a="#25282e", n="#0e0f12", p="#ffb0c0", e="#000000"),
    dict(name="Ginger", o="#2a1406", b="#c27a3a", l="#fff0dc", s="#3a1c08", a="#3a1c08", n="#1a0a02", p="#ffb0a0", e="#000000"),
 ]),
 "Koala": dict(eyes=5, body=[
    "oooo........oooo",
    "oaaao......oaaao",
    "oaaaooooooooaaao",
    ".oobbbbbbbbbboo.",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obbbbbbnnbbbbbbo",
    "obpbbbnnnnbbbpbo",
    "obbbbbnnnnbbbbbo",
    "obbbbbbbbbbbbbbo",
    ".obbbllllllbbbo.",
    "..obbbbbbbbbbo.."], colors=[
    dict(name="Gray",  o="#2a2e36", b="#a9b0bc", l="#f2f4f7", a="#f2f4f7", n="#1e2128", p="#ffb0c0", e="#0e0f12"),
    dict(name="Smoky", o="#16181d", b="#5e6470", l="#c9ced6", a="#c9ced6", n="#0e0f12", p="#ff9fb0", e="#e8e8f0"),
 ]),
 "Cow": dict(eyes=5, body=[
    "...h........h...",
    "...ho......oh...",
    "..oboooooooobo..",
    "oaobbbbsbbbbboao",
    ".obbbsssbbbbbbo.",
    "obbbbssbbbbbbbbo",
    "obbbbbbbbbbbsbbo",
    "obpnnnnnnnnnnpbo",
    "obnnndnnnndnnnbo",
    "obnnnnnnnnnnnnbo",
    ".obnnnnnnnnnnbo.",
    "..obbbbbbbbbbo.."], colors=[
    dict(name="Dairy", o="#1a1a20", b="#fbfbfb", s="#22222a", n="#ffb6c8", d="#5a2433", h="#f2e6c8", a="#ffb6c8", p="#ff8fab", e="#0a0a0e"),
    dict(name="Brown", o="#2a1606", b="#9a5a2a", s="#fff2e0", n="#ffc8b0", d="#5a2a14", h="#f2e6c8", a="#ffc8b0", p="#ff9f8a", e="#0a0604"),
    dict(name="Strawberry", o="#5a2433", b="#ffb6d0", s="#ffffff", n="#ffd6e4", d="#a83a5a", h="#fff4dc", a="#ffd6e4", p="#ff7fa8", e="#3a0e1e"),
 ]),
 "Axolotl": dict(eyes=5, body=[
    ".a............a.",
    "aa.oooooooooo.aa",
    ".aobbbbbbbbbboa.",
    "aaobbbbbbbbbboaa",
    ".aobbbbbbbbbboa.",
    "..obbbbbbbbbbo..",
    ".obbbbbbbbbbbbo.",
    "obpbbbbbbbbbbpbo",
    "obbbbbllllbbbbbo",
    "obbbblllllllbbbo",
    ".obbbllllllbbbo.",
    "..obbbbbbbbbbo.."], colors=[
    dict(name="Pink",  o="#6a2a44", b="#ffc2d6", l="#ffe6ef", a="#ff5f8f", p="#ff8fb0", e="#2a0e1a"),
    dict(name="Wild",  o="#1e2414", b="#6a7a4a", l="#a8b48a", a="#a85a6a", p="#c87a7a", e="#0e1208"),
    dict(name="Gold",  o="#5a3a06", b="#ffd66a", l="#fff2c2", a="#ff9f3a", p="#ffa07a", e="#a81e1e"),
    dict(name="Blue",  o="#14264a", b="#7ab8ff", l="#d6ecff", a="#3a6aff", p="#ff9fc8", e="#0a1430"),
 ]),
}

ANIMALS.update({
 "Hamster": dict(eyes=5, body=[
    "..oo........oo..",
    ".oaao......oaao.",
    ".oaboooooooobao.",
    ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "ollllbbbbbbllllo",
    "olllpllnnllplllo",
    "ollllllllllllllo",
    ".ollllllllllllo.",
    "..oooooooooooo.."], colors=[
    dict(name="Golden", o="#3a2006", b="#f0a848", l="#fff3e2", a="#ffb0a0", n="#ff8f8f", p="#ff9f9f", e="#120a02"),
    dict(name="Dwarf",  o="#2a2c34", b="#9aa1ad", l="#ffffff", a="#ffc0c8", n="#ff8fa3", p="#ffb0c0", e="#0e0f12"),
    dict(name="Cream",  o="#5a4426", b="#fbe7c6", l="#ffffff", a="#ffc0b0", n="#ff9f9f", p="#ffb0b0", e="#a81e2e"),
    dict(name="Panda",  o="#101014", b="#2e2e36", l="#ffffff", a="#ffb0c0", n="#ff8fa3", p="#ffb0c0", e="#0b0b0f"),
 ]),
 "Sheep": dict(eyes=5, body=[
    "..oo.oo..oo.oo..",
    ".owwowwoowwowwo.",
    "owwwwwwwwwwwwwwo",
    "owwobbbbbbbbowwo",
    "oaobbbbbbbbbboao",
    "owobbbbbbbbbbowo",
    "owobbbbbbbbbbowo",
    "owwobbbbbbbbowwo",
    "owwobbbnnbbbowwo",
    "owwwobbbbbbowwwo",
    ".owwwoooooowwwo.",
    "..oooooooooooo.."], colors=[
    dict(name="Classic", o="#3a3a44", w="#fbfbfb", b="#2e2e36", a="#2e2e36", n="#55555f", e="#f4f4f4"),
    dict(name="Cream",   o="#5a4a36", w="#fff6e6", b="#f0d6b4", a="#e0bc94", n="#c08a6a", e="#2a1a0e"),
    dict(name="Black",   o="#0c0c10", w="#3a3a44", b="#1e1e24", a="#1e1e24", n="#55555f", e="#f4f4f4"),
    dict(name="Cotton Candy", o="#6a2a4a", w="#ffc6e0", b="#fff0f6", a="#ffb0d0", n="#ff8fb8", e="#3a0e24"),
 ]),
 "Monkey": dict(eyes=5, body=[
    "....oooooooo....",
    "..oobbbbbbbboo..",
    ".obbbbbbbbbbbbo.",
    "oobbllbbbbllbboo",
    "oaoblllbblllboao",
    "oaobllllllllboao",
    "ooobllllllllbooo",
    "..obllllllllbo..",
    "..oblllddlllbo..",
    "..obllllllllbo..",
    "...obbbbbbbbo...",
    "....oooooooo...."], colors=[
    dict(name="Brown",  o="#24140a", b="#8a5a34", l="#f2d2ae", a="#f2b08e", d="#3a2414", e="#120a04"),
    dict(name="Golden", o="#3a2408", b="#e0a040", l="#fff0d0", a="#ffc8a0", d="#5a3a14", e="#1a1004"),
    dict(name="Gorilla", o="#0a0a0e", b="#2e2e36", l="#6a6a78", a="#55555f", d="#0a0a0e", e="#e8e0c8"),
 ]),
 "Lion": dict(eyes=5, body=[
    "...mmmmmmmmmm...",
    ".mmmmmmmmmmmmmm.",
    "mmmobbbbbbbbommm",
    "mmobbbbbbbbbbomm",
    "mmobbbbbbbbbbomm",
    "mmobbbbbbbbbbomm",
    "mmobbbbbbbbbbomm",
    "mmobpbllllbpbomm",
    "mmobbllnnllbbomm",
    "mmobbllllllbbomm",
    ".mmobbbbbbbbomm.",
    "..mmmoooooommm.."], colors=[
    dict(name="Golden", o="#3a2008", b="#f2c36a", m="#b8642a", l="#fff2d6", p="#ff9f7a", n="#5a2a14", e="#2a1404", f="#3a2008"),
    dict(name="White",  o="#6a6070", b="#fbf6ee", m="#e8dcc8", l="#ffffff", p="#ffb0b0", n="#c08a8a", e="#3a7bd5", f="#6a6070"),
    dict(name="Shadow", o="#14100c", b="#c49a5a", m="#2a1a10", l="#f2dcb4", p="#e08a6a", n="#2a1a10", e="#140c04", f="#14100c"),
 ]),
 "Tiger": dict(eyes=5, body=[
    ".o............o.",
    ".oao........oao.",
    ".oaboooooooobao.",
    ".obbsbbssbbsbbo.",
    "osbbbbbssbbbbbso",
    "obbbbbbbbbbbbbbo",
    "osbbbbbbbbbbbbso",
    "osbbbllllllbbbso",
    "obbblllnnlllbbbo",
    "osbbbllllllbbbso",
    ".obbbbbbbbbbbbo.",
    "..obbbbbbbbbbo.."], colors=[
    dict(name="Bengal", o="#2a1004", b="#f08a2a", s="#1a0a04", l="#fff6ea", a="#fff6ea", n="#ff8f8f", e="#2a1004"),
    dict(name="White",  o="#3a3a44", b="#f6f6f8", s="#2e2e36", l="#ffffff", a="#ffd0d8", n="#ff9fb0", e="#3a7bd5"),
    dict(name="Golden", o="#3a2408", b="#ffd27a", s="#c8803a", l="#fff8e6", a="#fff8e6", n="#ff9f8a", e="#3a2408"),
 ]),
 "Bat": dict(eyes=5, body=[
    "..o..........o..",
    "..oo........oo..",
    "..oboooooooobo..",
    "..obbbbbbbbbbo..",
    "o..obbbbbbbbo..o",
    "owwobbbbbbbbowwo",
    "owwobbbbbbbbowwo",
    "owwwobbbbbbowwwo",
    "owowobbbbbbowowo",
    "o.o.obbllbbo.o.o",
    ".....obbbbo.....",
    "......oooo......"], colors=[
    dict(name="Night", o="#0c0a14", b="#3a3050", w="#5a4a7a", l="#ff8fb0", e="#ffe066"),
    dict(name="Fruit", o="#2a1406", b="#8a5a2a", w="#5a3414", l="#ffb0a0", e="#140a02"),
    dict(name="Ghost", o="#5a6170", b="#f2f4f8", w="#d8dde6", l="#ffb0c0", e="#d81e3a"),
 ]),
 "Hedgehog": dict(eyes=5, body=[
    "..s.s.s.s.s.s...",
    ".ssssssssssssss.",
    "ssssssssssssssss",
    "sssobbbbbbbbosss",
    "ssobbbbbbbbbboss",
    "ssobbbbbbbbbboss",
    "ssobbbbbbbbbboss",
    "ssobpbbbbbbpboss",
    "ssobbbbnnbbbboss",
    "sssobbbbbbbbosss",
    ".sssoooooooosss.",
    "..ssssssssssss.."], colors=[
    dict(name="Brown",  o="#2a1a0e", s="#6a4a2e", b="#f2dcc0", p="#ff9f9f", n="#1a0e06", e="#120a04"),
    dict(name="Albino", o="#7a6a6a", s="#f2e6d8", b="#ffffff", p="#ffb0c0", n="#ff8fa3", e="#d81e3a"),
    dict(name="Cinnamon", o="#3a1a08", s="#b8682a", b="#fff0dc", p="#ff9f8a", n="#3a1a08", e="#1a0a02"),
 ]),
 "Duck": dict(eyes=5, mouth=False, body=[
    "....oooooooo....",
    "..oobbbbbbbboo..",
    ".obbbbbbbbbbbbo.",
    ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obpbbbbbbbbbbpbo",
    "obbbbkkkkkkbbbbo",
    "obbbbkkkkkkbbbbo",
    "obbbbbbbbbbbbbbo",
    ".obbbbbbbbbbbbo.",
    "..obbbbbbbbbbo.."], colors=[
    dict(name="White",   o="#5a5a66", b="#ffffff", p="#ffc0c8", k="#ff9a1f", e="#1a1a20", f="#ff9a1f"),
    dict(name="Mallard", o="#0c2414", b="#2e8a4a", p="#5ab86a", k="#f2d23a", e="#0a0a0e", f="#ff8a1f"),
    dict(name="Rubber",  o="#6a4a06", b="#ffe03a", p="#ff9f6a", k="#ff6a1f", e="#1a1004", f="#ffe03a"),
 ]),
 "Seal": dict(eyes=5, body=[
    "....oooooooo....",
    "..oobbbbbbbboo..",
    ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obpbdbllllbdbpbo",
    "obdbbllnnllbbdbo",
    "obbbbllllllbbbbo",
    ".obbbbbbbbbbbbo.",
    "..oobbbbbbbboo.."], colors=[
    dict(name="Harbor", o="#22262e", b="#8a93a2", l="#c8ced8", d="#3a3f4a", n="#14161b", p="#ffb0c0", e="#0a0b0e"),
    dict(name="Pup",    o="#7a8494", b="#ffffff", l="#ffffff", d="#9aa3b2", n="#2a2e36", p="#ffc0cc", e="#0a0b0e"),
    dict(name="Leopard", o="#1a1c22", b="#b8bfcc", l="#e6e9ef", d="#3a3f4a", n="#14161b", p="#ffb0c0", e="#0a0b0e"),
 ]),
 "Sloth": dict(eyes=5, body=[
    "....oooooooo....",
    "..oobbbbbbbboo..",
    ".obbbbbbbbbbbbo.",
    "obbllllllllllbbo",
    "obllllllllllllbo",
    "oblsssllllssslbo",
    "obssllllllllssbo",
    "obllllllllllllbo",
    "oblllllddlllllbo",
    "obbllllllllllbbo",
    ".obbllllllllbbo.",
    "..obbbbbbbbbbo.."], colors=[
    dict(name="Brown", o="#2a1c10", b="#8a6a4a", l="#e8d6bc", s="#3a2814", d="#1a1006", e="#0a0604"),
    dict(name="Pale",  o="#5a4a3a", b="#c8b49a", l="#fff4e4", s="#6a5038", d="#3a2814", e="#1a1006"),
 ]),
 "Deer": dict(eyes=5, body=[
    ".h.h........h.h.",
    ".hhh........hhh.",
    "...hooooooooh...",
    "oaobbbbbbbbbboao",
    ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obpbbllllllbbpbo",
    "obbblllnnlllbbbo",
    "obbbbllllllbbbbo",
    ".obbbbbbbbbbbbo.",
    "..obbbbbbbbbbo.."], colors=[
    dict(name="Fawn",     o="#2a1606", b="#c8844a", l="#fff0dc", a="#ffc8b0", h="#8a5a2a", n="#1a0a04", p="#ff9f8a", e="#140a02"),
    dict(name="Reindeer", o="#1e1006", b="#7a5030", l="#e8d0b0", a="#c89a7a", h="#e8d8b8", n="#e8202a", p="#ff8f8f", e="#0e0604"),
    dict(name="Snow",     o="#6a6a76", b="#f8f8fa", l="#ffffff", a="#ffd0d8", h="#e0c890", n="#ff8fa3", p="#ffb0c0", e="#2a2e36"),
 ]),
 "Octopus": dict(eyes=5, feet=False, body=[
    ".....oooooo.....",
    "...oobbbbbboo...",
    "..obbbbbbbbbbo..",
    ".obbbsbbbbsbbbo.",
    ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo",
    "obpbbbbbbbbbbpbo",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obbobbobbobbobbo",
    "ob.ob.obbo.bo.bo"], colors=[
    dict(name="Coral",  o="#5a1a2a", b="#ff7a8a", s="#ffb0b8", p="#ff4f6a", e="#2a0a12"),
    dict(name="Purple", o="#2a1440", b="#9a6ad8", s="#c8a8f0", p="#ff8fc0", e="#14082a"),
    dict(name="Deep Sea", o="#0a1a2a", b="#2a5a7a", s="#5ad8e8", p="#5ad8e8", e="#d8f8ff"),
 ]),
 "Unicorn": dict(eyes=5, body=[
    "........h.......",
    ".......hh.......",
    ".oo..oohhoo..oo.",
    ".oaoobbbbbbooao.",
    "omobbbbbbbbbbomo",
    "omobbbbbbbbbbomo",
    "omobbbbbbbbbbomo",
    ".oobpbbbbbbpboo.",
    "..obllllllllbo..",
    "..oblldlldllbo..",
    "..obllllllllbo..",
    "...oooooooooo..."], colors=[
    dict(name="Rainbow", o="#4a3a6a", b="#ffffff", m="#ff7ac8", l="#fff0fa", a="#ffb0d8", h="#ffd23a", p="#ffb0d8", d="#c08ab0", e="#3a2a6a", f="#ffd23a"),
    dict(name="Night",   o="#0a0a1a", b="#2a2a4a", m="#7a5aff", l="#3a3a6a", a="#7a5aff", h="#c8d8ff", p="#ff6aa8", d="#0a0a1a", e="#c8d8ff", f="#c8d8ff"),
    dict(name="Pastel",  o="#5a6a8a", b="#e8f4ff", m="#9ad8ff", l="#ffffff", a="#c8e8ff", h="#ffe8a8", p="#ffc8e0", d="#8aa8c8", e="#3a4a6a", f="#ffe8a8"),
 ]),
 "Shark": dict(eyes=5, mouth=False, body=[
    ".......oo.......",
    "......obbo......",
    ".....obbbbo.....",
    "..oobbbbbbbboo..",
    ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obpbbbbbbbbbbpbo",
    "ollllllllllllllo",
    "olldkdkdkdkdkllo",
    ".ollllllllllllo.",
    "..oooooooooooo.."], colors=[
    dict(name="Great White", o="#22262e", b="#7a8494", l="#f6f8fb", d="#5a1a2a", k="#ffffff", p="#ffb0c0", e="#0a0b0e"),
    dict(name="Blue",        o="#0c1a3a", b="#3a7ad8", l="#e8f2ff", d="#3a0e1a", k="#ffffff", p="#ff9fc0", e="#0a0e1a"),
    dict(name="Pink",        o="#6a2a4a", b="#ff9fc8", l="#fff0f6", d="#8a1a3a", k="#ffffff", p="#ff6a9a", e="#3a0e24"),
 ]),
})

FEET_FLAMINGO = {"stand": ".......o........", "walk1": "......o..o......", "walk2": ".....o....o.....", "air": "......o..o......"}
ANIMALS.update({
 "Wolf": dict(eyes=5, body=[
    ".o............o.", ".oao........oao.", ".oaboooooooobao.", ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obbbbllllllbbbbo",
    "obbllllnnllllbbo", "obbllllllllllbbo", ".obbllllllllbbo.", "..oooooooooooo.."], colors=[
    dict(name="Gray",   o="#1c1f26", b="#7a8290", l="#e6e9ee", a="#3a3f4a", n="#0e1014", e="#f2c11e"),
    dict(name="Timber", o="#24160a", b="#8a6a4a", l="#efe2cf", a="#4a3420", n="#140c06", e="#f2a11e"),
    dict(name="Arctic", o="#6a7080", b="#f4f6fa", l="#ffffff", a="#c8ced8", n="#2a2e36", e="#3a7bd5"),
    dict(name="Shadow", o="#08080c", b="#26262e", l="#55555f", a="#14141a", n="#08080c", e="#ffe066"),
 ]),
 "Squirrel": dict(eyes=5, dx=-2, body=[
    "............aaa.", ".o.......o..aaaa", "oao.....oao.aaaa", "oaboooooobaoaaaa",
    "obbbbbbbbbboaaaa", "obbbbbbbbbboaaao", "obbbbbbbbbboaaao", "obpbllllbpboaao.",
    "obbllnnllbboaao.", "obbllllllbboao..", ".obbbbbbbboo....", "..oooooooo......"], colors=[
    dict(name="Red",    o="#2a1206", b="#d0702a", l="#fff0dc", a="#e08a3a", p="#ff9f8a", n="#1a0a02", e="#140802"),
    dict(name="Gray",   o="#22252c", b="#8a909c", l="#f2f4f7", a="#a8aeb8", p="#ffb0c0", n="#14161b", e="#0a0b0e"),
    dict(name="Black",  o="#08080c", b="#2e2e36", l="#6a6a78", a="#3a3a44", p="#ff8fa3", n="#08080c", e="#ffe066"),
 ]),
 "Otter": dict(eyes=5, body=[
    "................", "...oo......oo...", "..oaooooooooao..", ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "olllldlllldllllo",
    "ollllllnnllllllo", "ollllllllllllllo", ".obllllllllllbo.", "..obbbbbbbbbbo.."], colors=[
    dict(name="River",  o="#24160a", b="#7a5232", l="#f0dcc0", a="#c09a7a", d="#5a3a22", n="#140a04", e="#0e0804"),
    dict(name="Sea",    o="#1a120c", b="#4a3628", l="#d8ccc0", a="#8a7464", d="#2a1e16", n="#0a0604", e="#0a0604"),
    dict(name="Golden", o="#3a2408", b="#c8904a", l="#fff2dc", a="#f0c890", d="#8a5a24", n="#2a1804", e="#1a1004"),
 ]),
 "Skunk": dict(eyes=5, body=[
    ".ooo........ooo.", "oaaao......oaaao", "oaabooossooobaao", ".obbbbbssbbbbbo.",
    "obbbbbbssbbbbbbo", "obbbbbbssbbbbbbo", "obbbbbbssbbbbbbo", "obpbbllllllbbpbo",
    "obbblllnnlllbbbo", "obbbbllllllbbbbo", ".obbbbbbbbbbbbo.", "..obbbbbbbbbbo.."], colors=[
    dict(name="Classic", o="#060608", b="#1e1e26", s="#ffffff", l="#f4f4f6", a="#3a3a44", p="#ff8fa3", n="#ff8fa3", e="#f4f4f6"),
    dict(name="Brown",   o="#140a04", b="#5a3a22", s="#fff4e6", l="#fff4e6", a="#7a5232", p="#ff9f8a", n="#ff9f8a", e="#fff4e6"),
    dict(name="Lavender", o="#1a1028", b="#6a4a9a", s="#ffffff", l="#f4eeff", a="#8a6ab8", p="#ff9fd0", n="#ff9fd0", e="#f4eeff"),
 ]),
 "Beaver": dict(eyes=5, mouth=False, body=[
    ".ooo........ooo.", "oaaao......oaaao", "oaaboooooooobaao", ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obpbbllllllbbpbo",
    "obbblllnnlllbbbo", "obbbbllddllbbbbo", ".obbbbbkkbbbbbo.", "..obbbbbbbbbbo.."], colors=[
    dict(name="Brown",  o="#1e1006", b="#7a4a24", l="#c8946a", a="#a8703e", p="#e88a7a", n="#140a04", d="#2a1406", k="#fff4dc", e="#0e0604"),
    dict(name="Golden", o="#3a2006", b="#c88a3a", l="#f0cc94", a="#e0a85a", p="#ff9f7a", n="#2a1604", d="#3a2006", k="#ffffff", e="#1a0e02"),
    dict(name="Dark",   o="#0c0804", b="#3a2616", l="#7a5a3e", a="#5a3e26", p="#c86a5a", n="#0c0804", d="#0c0804", k="#fff4dc", e="#f2d8a8"),
 ]),
 "Capybara": dict(eyes=5, body=[
    "................", "..oo........oo..", ".oaooooooooooao.", ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obbbbnnnnnnbbbbo",
    "obbbndnnnndnbbbo", "obbbnnnnnnnnbbbo", ".obbbbbbbbbbbbo.", "..oooooooooooo.."], colors=[
    dict(name="Classic", o="#2a1a0c", b="#a8784a", a="#7a5232", n="#6a4626", d="#1a0e06", e="#0e0804"),
    dict(name="Golden",  o="#3a2408", b="#d8a660", a="#a8783a", n="#8a5e30", d="#2a1804", e="#1a1004"),
    dict(name="Mocha",   o="#140a04", b="#6a4a32", a="#4a3220", n="#3a2616", d="#0c0604", e="#f2e2c8"),
 ]),
 "Llama": dict(eyes=5, body=[
    ".oo..........oo.", ".oao..wwww..oao.", ".oaoowwwwwwooao.", ".obbwwwwwwwwbbo.",
    "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", ".obpbbbbbbbbpbo.",
    "..oblldlldllbo..", "..obllllllllbo..", "..obllllllllbo..", "...oooooooooo..."], colors=[
    dict(name="White",   o="#5a5466", b="#f6f2ea", w="#ffffff", l="#ffffff", a="#e8dcd0", p="#ffb0c0", d="#8a7a7a", e="#1e1a22"),
    dict(name="Brown",   o="#24160a", b="#a8784a", w="#d8b08a", l="#e8cfae", a="#7a5232", p="#ff9f8a", d="#3a2414", e="#0e0804"),
    dict(name="Alpaca",  o="#5a4426", b="#f0dcbc", w="#fff6e6", l="#fff8ee", a="#d8bc94", p="#ffb0a0", d="#8a6a4a", e="#2a1a0e"),
    dict(name="Party",   o="#4a1a5a", b="#ffd0f0", w="#7ad8ff", l="#fff0fa", a="#ff7ac8", p="#ff7ac8", d="#a84a9a", e="#2a0a3a"),
 ]),
 "Horse": dict(eyes=5, body=[
    "..o..........o..", ".oao........oao.", ".oaoommmmmmooao.", ".obmmmmmmmmmmbo.",
    "obbbbmmmmmmbbbbo", "obbbbbbmmbbbbbbo", "obbbbbbbbbbbbbbo", ".obpbbbbbbbbpbo.",
    "..obllllllllbo..", "..oblldlldllbo..", "..obllllllllbo..", "...oooooooooo..."], colors=[
    dict(name="Chestnut",  o="#1e0e04", b="#a8582a", m="#3a1a08", l="#d8946a", a="#7a3a16", p="#e87a6a", d="#3a1a08", e="#0e0602"),
    dict(name="Palomino",  o="#3a2408", b="#e8b85a", m="#fff6e0", l="#fff0d0", a="#c8903a", p="#ff9f7a", d="#5a3a14", e="#1a1004"),
    dict(name="Black",     o="#040406", b="#24242c", m="#0c0c10", l="#4a4a55", a="#14141a", p="#a85a6a", d="#040406", e="#e8e0c8"),
    dict(name="Dapple",    o="#3a3f4a", b="#c8ced8", m="#5a606c", l="#eef0f4", a="#8a909c", p="#ffb0c0", d="#3a3f4a", e="#14161b"),
 ]),
 "Zebra": dict(eyes=5, body=[
    "..o..........o..", ".oao........oao.", ".oaoommmmmmooao.", ".obmmmmmmmmmmbo.",
    "osbbbmmmmmmbbbso", "obsbbbbmmbbbbsbo", "osbbsbbbbbbsbbso", ".osbsbbbbbbsbso.",
    "..obllllllllbo..", "..oblldlldllbo..", "..obllllllllbo..", "...oooooooooo..."], colors=[
    dict(name="Classic", o="#0a0a0e", b="#ffffff", s="#1a1a20", m="#1a1a20", l="#4a4a55", a="#1a1a20", p="#ffb0c0", d="#0a0a0e", e="#0a0a0e"),
    dict(name="Candy",   o="#4a1a3a", b="#ffffff", s="#ff7ab8", m="#ff7ab8", l="#ffd0e8", a="#ff7ab8", p="#ffb0d0", d="#8a2a5a", e="#3a0e2a"),
 ]),
 "Elephant": dict(eyes=5, mouth=False, feet=False, body=[
    ".....oooooo.....", "ooo.obbbbbbo.ooo", "oaaobbbbbbbboaao", "oaaobbbbbbbboaao",
    "oaaobbbbbbbboaao", "oaaobbbbbbbboaao", "oaaobpbbbbpboaao", ".oaobbbbbbbboao.",
    "..ooobbbbbbooo..", "..obo.obbo.obo..", "..obo.obbo.obo..", "..ooo..oo..ooo.."], colors=[
    dict(name="Gray",  o="#2a2e36", b="#9aa1ad", a="#c8a8b0", p="#ffb0c0", e="#0e0f12"),
    dict(name="Pink",  o="#6a2a44", b="#ffb6d0", a="#ff8fb8", p="#ff7aa8", e="#3a0e1e"),
    dict(name="Sky",   o="#1a3a5a", b="#a8d8ff", a="#7ab8f0", p="#ffb0d0", e="#0a1a2a"),
 ]),
 "Giraffe": dict(eyes=5, body=[
    "...o........o...", "..oho......oho..", "...h.oooooo.h...", "oaohobbbbbbohoao",
    ".oobbsbbbbsbboo.", "obbsbbbbbbbbsbbo", "obbbbbbsbbbbbbbo", ".obpbbbbbbbbpbo.",
    "..obllllllllbo..", "..oblldlldllbo..", "..obllllllllbo..", "...oooooooooo..."], colors=[
    dict(name="Classic",     o="#3a2008", b="#f2c45a", s="#a8622a", h="#6a3a14", a="#c8843a", l="#fff0d0", p="#ff9f7a", d="#6a3a14", e="#1a0e02"),
    dict(name="Reticulated", o="#2a1406", b="#fff2dc", s="#a84a1e", h="#5a2a0e", a="#c8743a", l="#fff8ee", p="#ff9f8a", d="#5a2a0e", e="#1a0a02"),
    dict(name="Mint",        o="#14301f", b="#c8f0d8", s="#4fbf8a", h="#2a6a4a", a="#8ad8b0", l="#eefaf2", p="#ffb0c0", d="#2a6a4a", e="#0a1a12"),
 ]),
 "Hippo": dict(eyes=5, mouth=False, body=[
    "................", "..oo........oo..", ".oaooooooooooao.", ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "ollldlllllldlllo",
    "ollllllllllllllo", "olllllddddlllllo", "olkllllllllllklo", ".oooooooooooooo."], colors=[
    dict(name="Gray",   o="#22262e", b="#8a8fa8", l="#b8a8b8", a="#d8a8b8", d="#3a2a3a", k="#ffffff", e="#0e0f14"),
    dict(name="Pink",   o="#5a2433", b="#ffa8c0", l="#ffc8d8", a="#ff7fa0", d="#8a2a44", k="#ffffff", e="#2a0e18"),
    dict(name="Purple", o="#24143a", b="#9a7ad8", l="#c8b0f0", a="#ff9fd0", d="#3a1a5a", k="#ffffff", e="#140a24"),
 ]),
 "Kangaroo": dict(eyes=5, body=[
    ".o............o.", ".oo..........oo.", ".oao........oao.", ".oaboooooooobao.",
    "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obpbbllllllbbpbo",
    "obbblllnnlllbbbo", "obbbbllllllbbbbo", ".obbbbbbbbbbbbo.", "..obbbbbbbbbbo.."], colors=[
    dict(name="Red",  o="#2a1006", b="#c06a3a", l="#f4dcc4", a="#e0a080", p="#ff9f8a", n="#1a0a04", e="#140802"),
    dict(name="Gray", o="#22252c", b="#8a909c", l="#e6e9ee", a="#c8b0b8", p="#ffb0c0", n="#14161b", e="#0a0b0e"),
    dict(name="Tan",  o="#3a2810", b="#d8b07a", l="#fff2dc", a="#f0c8a8", p="#ffa08a", n="#2a1a08", e="#1a1004"),
 ]),
 "Parrot": dict(eyes=5, mouth=False, body=[
    ".......oo.......", "......oaao......", "....oooaaooo....", "..oobbbbbbbboo..",
    ".obbbbbbbbbbbbo.", ".obllllbbllllbo.", "obbllllbbllllbbo", "obbbbbkkkkbbbbbo",
    "obbbbbkkkkbbbbbo", "obbbbbbkkbbbbbbo", ".obbbbbbbbbbbbo.", "..obbbbbbbbbbo.."], colors=[
    dict(name="Scarlet",   o="#3a0606", b="#e8202a", a="#ffd23a", l="#ffffff", k="#f2e6c8", e="#0a0a0e", f="#5a5a66"),
    dict(name="Blue Gold", o="#0a1a3a", b="#2a7ad8", a="#2ac86a", l="#ffffff", k="#1a1a20", e="#0a0a0e", f="#5a5a66"),
    dict(name="Green",     o="#0a2a10", b="#3ac84a", a="#ff4a3a", l="#ffffff", k="#f2a23a", e="#0a0a0e", f="#5a5a66"),
    dict(name="Cockatoo",  o="#6a6a76", b="#ffffff", a="#ffe03a", l="#e8f0ff", k="#3a3a44", e="#0a0a0e", f="#6a6a76"),
 ]),
 "Flamingo": dict(eyes=5, mouth=False, feet="flamingo", body=[
    "....oooooooo....", "..oobbbbbbbboo..", ".obbbbbbbbbbbbo.", ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obpbbbbbbbbbbpbo", "obbbbbkkkkbbbbbo",
    "obbbbbbkkbbbbbbo", "obbbbbbddbbbbbbo", ".obbbbbbbbbbbbo.", "..obbbbbbbbbbo.."], colors=[
    dict(name="Pink",    o="#6a1e3a", b="#ff8fb8", p="#ff5f95", k="#fff0f4", d="#1a1a20", e="#2a0a18", f="#ff6a9a"),
    dict(name="Hot Pink", o="#5a0a2a", b="#ff4f95", p="#e8206a", k="#fff0f4", d="#1a1a20", e="#2a0410", f="#e8206a"),
    dict(name="Peach",   o="#6a3a1e", b="#ffc0a0", p="#ff8f6a", k="#fff6f0", d="#1a1a20", e="#2a1408", f="#ff8f6a"),
 ]),
 "Bee": dict(eyes=5, feet=False, body=[
    "...o........o...", "....o......o....", "ww..oooooooo..ww", "wwwobbbbbbbbowww",
    ".wobbbbbbbbbbow.", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "osssssssssssssso",
    "obpbbbbbbbbbbpbo", "obbbbbbbbbbbbbbo", ".osssssssssssso.", "..obbbbbbbbbbo.."], colors=[
    dict(name="Honey",  o="#2a1a04", b="#ffd23a", s="#2a1a04", w="#e8f6ff", p="#ff9f6a", e="#1a1004"),
    dict(name="Bumble", o="#1a0e02", b="#ffb02a", s="#1a0e02", w="#ffffff", p="#ff7a4a", e="#1a0e02"),
    dict(name="Pastel", o="#5a4a2a", b="#fff2a8", s="#c8a8ff", w="#f4f0ff", p="#ffb0c8", e="#3a2a14"),
 ]),
 "Ladybug": dict(eyes=5, mouth=False, body=[
    "...o........o...", "....o......o....", "....oooooooo....", "..oohhhhhhhhoo..",
    ".ohhhhhhhhhhhho.", "ohhhhhhhhhhhhhho", "ohhhhhhhhhhhhhho", "obbbbbbssbbbbbbo",
    "obsbbbbssbbbbsbo", "obbbsbbssbbsbbbo", ".obbbbbssbbbbbo.", "..oooooooooooo.."], colors=[
    dict(name="Red",    o="#0a0a0e", b="#e8202a", s="#0a0a0e", h="#1a1a20", e="#ffffff", f="#0a0a0e"),
    dict(name="Orange", o="#0a0a0e", b="#ff8a1f", s="#0a0a0e", h="#1a1a20", e="#ffffff", f="#0a0a0e"),
    dict(name="Yellow", o="#0a0a0e", b="#ffd23a", s="#0a0a0e", h="#1a1a20", e="#ffffff", f="#0a0a0e"),
 ]),
 "Whale": dict(eyes=5, feet=False, body=[
    "......w..w......", ".......ww.......", "....oooooooo....", "..oobbbbbbbboo..",
    ".obbbbbbbbbbbbo.", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obpbbbbbbbbbbpbo",
    "ollllllllllllllo", "olslslslslslslso", ".ollllllllllllo.", "..oooooooooooo.."], colors=[
    dict(name="Blue",   o="#0a1a3a", b="#3a7ad8", l="#d8e8ff", s="#a8c8f0", w="#a8e0ff", p="#ff9fc0", e="#0a0e1a"),
    dict(name="Orca",   o="#04040a", b="#1a1a24", l="#ffffff", s="#e0e0e8", w="#a8e0ff", p="#ff9fc0", e="#ffffff"),
    dict(name="Beluga", o="#6a7484", b="#f4f8fc", l="#ffffff", s="#dce4ee", w="#a8e0ff", p="#ffc0d0", e="#2a2e36"),
 ]),
 "Jellyfish": dict(eyes=5, feet=False, body=[
    ".....oooooo.....", "...oobbbbbboo...", "..obbbsbbsbbbo..", ".obbbbbbbbbbbbo.",
    ".obbbbbbbbbbbbo.", "obbbbbbbbbbbbbbo", "obpbbbbbbbbbbpbo", "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo", "obobobobbobobobo", ".a..a..aa..a..a.", "a..a..a..a..a..a"], colors=[
    dict(name="Moon",  o="#3a5a8a", b="#c8e4ff", s="#ffffff", a="#a8c8f0", p="#ffb0d0", e="#1a2a4a"),
    dict(name="Pink",  o="#6a2a5a", b="#ffb6e0", s="#fff0fa", a="#ff7ac8", p="#ff7ab0", e="#3a0e2a"),
    dict(name="Glow",  o="#1a0a3a", b="#7a4ad8", s="#5af0ff", a="#5af0ff", p="#ff7ad8", e="#d8faff"),
 ]),
 "Dragon": dict(eyes=5, body=[
    "..h..........h..", "..hh........hh..", "...hooooooooh...", "w.obbbbbbbbbbo.w",
    "wwobbbbbbbbbboww", "wwobbbbbbbbbboww", "wobbbbbbbbbbbbow", "obpbbllllllbbpbo",
    "obbbldlllldlbbbo", "obbbbllllllbbbbo", ".obbbbbbbbbbbbo.", "..obbbbbbbbbbo.."], colors=[
    dict(name="Green", o="#0c2a14", b="#3ac86a", l="#d8f8c8", h="#fff2c8", w="#2a8a4a", d="#0c2a14", p="#ff9f8a", e="#ffd23a"),
    dict(name="Red",   o="#2a0606", b="#e83a2a", l="#ffd8a8", h="#fff2c8", w="#a81a14", d="#2a0606", p="#ffd23a", e="#ffd23a"),
    dict(name="Ice",   o="#1a3a5a", b="#a8e0ff", l="#ffffff", h="#ffffff", w="#5ab0f0", d="#1a3a5a", p="#ffc0e0", e="#1a3a5a"),
    dict(name="Gold",  o="#3a2404", b="#ffc83a", l="#fff4c8", h="#ffffff", w="#d8901a", d="#3a2404", p="#ff8f6a", e="#c81e1e"),
 ]),
})

ANIMAL_TRAITS = {   # how each animal moves + what it says
    "Cat":     ("walk", ["meow", "*purrs*", "i knocked something off your desk", "feed me, human", "mrrp?"]),
    "Dog":     ("walk", ["woof!", "who's a good pet? me!", "ball? BALL?", "*wags tail*", "walk time??"]),
    "Fox":     ("walk", ["what does the fox say? hi.", "*sneaky*", "i'm very clever", "yip!"]),
    "Bear":    ("walk", ["*bear hug*", "honey?", "rawr (friendly)", "time for hibernation soon"]),
    "Panda":   ("walk", ["bamboo please", "*rolls around*", "i'm very fluffy", "nap o'clock"]),
    "Pig":     ("walk", ["oink!", "snort snort", "is there mud nearby?", "oink oink :)"]),
    "Frog":    ("hop",  ["ribbit", "croak!", "any flies around?", "hop hop!"]),
    "Penguin": ("walk", ["*waddles*", "it's too warm in here", "noot!", "i can't fly but i can slide"]),
    "Chick":   ("walk", ["peep!", "cheep cheep", "i'm small but brave", "peep peep!!"]),
    "Owl":     ("walk", ["hoo?", "who? hoo!", "i'm wide awake at night", "*rotates head*"]),
    "Mouse":   ("walk", ["squeak!", "cheese?", "*nibbles*", "i'm tiny and fast"]),
    "Raccoon": ("walk", ["any snacks in the trash?", "*rummages*", "i'm wearing a mask", "trash panda reporting"]),
    "Koala":   ("walk", ["*sleepy*", "eucalyptus pls", "hug?", "i nap 20 hours a day"]),
    "Cow":     ("walk", ["moo!", "mooo~", "got milk?", "*chews grass*"]),
    "Axolotl": ("walk", ["*smiles*", "blub", "i can regrow my legs", "it's dry out here"]),
    "Hamster": ("walk", ["*stuffs cheeks*", "wheel time!", "i'm saving this snack for later", "squeak squeak"]),
    "Sheep":   ("walk", ["baa!", "baaaa~", "i'm very fluffy today", "count me to fall asleep"]),
    "Monkey":  ("hop",  ["ooh ooh ah ah!", "banana?", "*swings around*", "monkey business!"]),
    "Lion":    ("walk", ["ROAR. (hello)", "i'm the king of this desktop", "*majestic mane flip*", "rawr"]),
    "Tiger":   ("walk", ["*pounces*", "grr!", "my stripes are unique", "stealth mode"]),
    "Bat":     ("flutter", ["*echolocates*", "is it night yet?", "squeak!", "hanging out"]),
    "Hedgehog": ("walk", ["*curls into a ball*", "careful, i'm spiky", "huff huff", "gotta go fast"]),
    "Duck":    ("walk", ["quack!", "quack quack", "*waddles*", "got any bread?"]),
    "Seal":    ("walk", ["arf arf!", "*claps flippers*", "where's the ocean?", "*boops*"]),
    "Sloth":   ("walk", ["heyyy... slow down...", "*slooowly waves*", "no rush", "zzz... oh hi"]),
    "Deer":    ("hop",  ["*ears twitch*", "oh! you startled me", "i love leaves", "*prances*"]),
    "Octopus": ("walk", ["*wiggles 8 arms*", "blub blub", "i'm very smart", "ink-credible!"]),
    "Unicorn": ("hop",  ["* magic *", "*sparkles*", "i'm extremely real", "neigh~"]),
    "Shark":   ("float", ["*swims in the air*", "chomp!", "i'm friendly, promise", "nom nom"]),
    "Wolf":    ("walk", ["awoooo!", "where's my pack?", "*howls at the monitor*", "i'm a good boy (wild)"]),
    "Squirrel": ("hop", ["*hides a nut*", "acorn?!", "chitter chitter", "i forgot where i buried it"]),
    "Otter":   ("walk", ["*holds your hand*", "*juggles a rock*", "swim time?", "i have a favorite rock"]),
    "Skunk":   ("walk", ["don't worry, i'm friendly", "i smell... great!", "*stomps feet*", "no sudden moves pls"]),
    "Beaver":  ("walk", ["*chews on your desk*", "dam it!", "building stuff", "nice wood"]),
    "Capybara": ("walk", ["ok i pull up", "*vibes*", "everyone is my friend", "chill mode: on"]),
    "Llama":   ("walk", ["no drama, llama", "*judges you*", "fluffy and proud", "mwaa!"]),
    "Horse":   ("walk", ["neigh!", "*whinnies*", "hay is for horses", "giddy up!"]),
    "Zebra":   ("walk", ["black with white stripes or white with black?", "stripes!", "*hee-haw*"]),
    "Elephant": ("walk", ["*trumpets*", "i never forget", "peanut?", "big ears, big heart"]),
    "Giraffe": ("walk", ["i can see the top of your screen", "leaves up here!", "*long neck noises*"]),
    "Hippo":   ("walk", ["*big yawn*", "mud bath please", "i'm a river horse", "chomp chomp"]),
    "Kangaroo": ("hop", ["boing! boing!", "*hops*", "g'day!", "my pocket is full of snacks"]),
    "Parrot":  ("hop",  ["hello! hello!", "pretty bird!", "squawk!", "polly wants a cookie"]),
    "Flamingo": ("walk", ["*stands on one leg*", "pink is my color", "shrimp please", "fabulous"]),
    "Bee":     ("flutter", ["bzzz", "buzz buzz!", "any flowers?", "bee-lieve in yourself"]),
    "Ladybug": ("walk", ["*tiny steps*", "spot the difference", "i'm lucky!", "hi from down here"]),
    "Whale":   ("float", ["*whale song*", "*sprays water*", "biggest pet ever", "ooooOOOooo~"]),
    "Jellyfish": ("float", ["*floats*", "no brain, no problem", "bloop", "*glows*"]),
    "Dragon":  ("flutter", ["*breathes tiny flame*", "rawr! (fire)", "guarding my treasure", "i hoard cookies"]),
}
SPEED = {"Sloth": 0.35, "Seal": 0.7, "Hedgehog": 1.3, "Mouse": 1.4, "Hamster": 1.2, "Cow": 0.8, "Koala": 0.6,
         "Capybara": 0.6, "Elephant": 0.7, "Hippo": 0.7, "Ladybug": 0.5, "Squirrel": 1.4, "Horse": 1.4, "Zebra": 1.4,
         "Wolf": 1.3, "Jellyfish": 0.5, "Whale": 0.6}
for _name, _a in ANIMALS.items():
    _move, _lines = ANIMAL_TRAITS[_name]
    VARIANTS[_name] = {"body": _a["body"], "eyes": _a["eyes"], "mouth": _a.get("mouth", True),
                       "feet": FEET_FLAMINGO if _a.get("feet") == "flamingo" else (FEET_STD if _a.get("feet", True) else None),
                       "dx": _a.get("dx", 0), "move": _move,
                       "colors": _a["colors"], "lines": _lines, "speed": SPEED.get(_name, 1.0)}
# Blip can also dress up as a dog: these "colors" bring their own markings (art)
BLIP_DOGS = [
    {"name": "Husky", "o": "#1c2028", "b": "#7d8796", "l": "#f4f6f9", "p": "#ffb0c0", "n": "#14161b", "e": "#4aa3ff",
     "art": [
        "..oo........oo..",
        ".olbo......oblo.",
        ".obbbooooooobbo.",
        ".obbbbbbbbbbbbo.",
        "obbbllbbbbllbbbo",
        "obbbbbbbbbbbbbbo",
        "ollbbbbbbbbbbllo",
        "olplllbbbblllplo",
        "ollllllnnllllllo",
        "ollllllllllllllo",
        ".ollllllllllllo.",
        "..ollllllllllo..",
     ]},
    {"name": "German Shepherd", "o": "#1a0e04", "b": "#c8843a", "s": "#1e1a18", "p": "#e88a6a", "n": "#0a0808", "e": "#2a1404",
     "art": [
        "..oo........oo..",
        ".osso......osso.",
        ".osssooooooosso.",
        ".obssssssssssbo.",
        "obbbbssssssbbbbo",
        "obbbbbbssbbbbbbo",
        "obbbbbbssbbbbbbo",
        "obpbbbbssbbbbpbo",
        "obbbbssnnssbbbbo",
        "obbbbssssssbbbbo",
        ".obbbbbbbbbbbbo.",
        "..obbbbbbbbbbo..",
     ]},
]
VARIANTS["Blip"]["colors"] = PALETTES + BLIP_DOGS
CRITTERS = list(KINDS)            # the original made-up critters
ANIMAL_KINDS = sorted(ANIMALS)
KINDS = CRITTERS + ANIMAL_KINDS


def kind_colors(kind):
    """Color choices for a kind: animals have their own, critters can use any fun color."""
    return VARIANTS[kind].get("colors") or PALETTES


def default_color(kind):
    v = VARIANTS[kind]
    return PALETTE_INDEX[v["palette"]] if "palette" in v and not v.get("colors") else 0
SUGGEST_URL = "https://github.com/Johnblip189/blipville/issues/new?template=new-animal.yml"
SUPPORT_URL = "https://github.com/Johnblip189/blipville#support-blipville"   # links live in the README, so they can change anytime
NAMES = ["Pip", "Mochi", "Bean", "Nugget", "Pixel", "Tofu", "Biscuit", "Sprinkles", "Wobble", "Gizmo",
         "Noodle", "Pebble", "Waffle", "Button", "Dot", "Jellybean", "Muffin", "Ziggy", "Clover", "Taco"]
ART_W, ART_H = 16, 13          # body + 1 row of feet
HEART = [".x.x.", "xxxxx", "xxxxx", ".xxx.", "..x.."]
ZED = ["xxxx", "..x.", ".x..", "xxxx"]
COOKIE = [".cccc.", "cdcccc", "cccdcc", "ccccdc", "cdcccc", ".cccc."]

LINES_IDLE = [
    "hi :)", "what are you working on?", "don't forget to drink water!",
    "boop.", "is it snack time?", "you're doing great", "i'm guarding your desktop",
    "the cursor is fast today", "*stretches*", "i like it here", "la la la~",
    "did you hear that?", "remember to take a break!",
]
LINES_PET = ["hehe", "that tickles!", "<3", "more pets pls", "yay!", "^_^"]
LINES_HELD = ["wheee!", "put me down!!", "where are we going?", "i can see everything from up here"]
LINES_LAND = ["ow.", "oof!", "i'm okay!", "10/10 landing"]
LINES_EAT = ["nom nom nom", "thank you!!", "delicious!"]
LINES_WAKE = ["huh? i'm awake!", "five more minutes...", "*yawn*"]
LINES_HUNGRY = ["...hungry", "my tummy is rumbling", "snack? please?"]


def work_area(root):
    """Screen area above the taskbar."""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            r = wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(r), 0)  # SPI_GETWORKAREA
            return r.left, r.top, r.right, r.bottom
        except Exception:  # noqa: BLE001
            pass
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    return 0, 0, sw, sh - (70 if sys.platform == "darwin" else 40)


class Blip:
    def __init__(self, app, kind="Blip", name="Blip", x=None):
        self.app = app
        self.kind = kind
        self.name = name
        self.root = root = tk.Toplevel(app.root)
        root.title(name)
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        bg = KEY
        if sys.platform == "win32":
            root.attributes("-transparentcolor", KEY)
        elif sys.platform == "darwin":
            try:
                root.attributes("-transparent", True)
                bg = "systemTransparent"
            except tk.TclError:
                pass
        root.config(bg=bg)
        self.canvas = tk.Canvas(root, width=W, height=H, bg=bg, highlightthickness=0, bd=0)
        self.canvas.pack()

        self.left, self.top, self.right, self.bottom = work_area(root)
        self.ground = self.bottom - H
        self.wx = x if x is not None else random.uniform(self.left + 50, self.right - W - 50)
        self.wx = min(max(self.wx, self.left), self.right - W)
        self.wy = self.top - H                     # drops in from the top of the screen
        self.vx = self.vy = 0.0
        self.state = "fall"
        self.state_until = 0.0
        self.target_x = None
        self.facing = 1
        self.energy = 100.0
        self.hunger = 10.0
        self.palette = default_color(kind)
        self.follow = tk.BooleanVar(master=root, value=False)
        self.kind_var = tk.StringVar(master=root, value=kind)
        self.greeted = {}                          # other pet's name -> when we last said hi
        self.squash_until = 0.0
        self.next_blink = time.monotonic() + 2
        self.blink_until = 0.0
        self.face = "normal"                       # normal / happy / surprised / sleep / munch
        self.face_until = 0.0
        self.bubble = None                         # (text, until)
        self.particles = []
        self.cookie = None                         # {"x": screen x, "y": canvas y, "vy": .., "landed": bool}
        self.after_land = None
        self.last_hungry_whine = 0.0

        self.press = None
        self.drag_hist = []
        c = self.canvas
        c.bind("<ButtonPress-1>", self.on_press)
        c.bind("<B1-Motion>", self.on_drag)
        c.bind("<ButtonRelease-1>", self.on_release)
        c.bind("<Button-3>", self.on_menu)
        if sys.platform == "darwin":
            c.bind("<Button-2>", self.on_menu)
            c.bind("<Control-Button-1>", self.on_menu)

        self.menu = tk.Menu(root, tearoff=0)
        self.menu.add_command(label="Feed a cookie", command=self.feed)
        self.menu.add_command(label="Pet", command=self.pet)
        self.menu.add_command(label="Nap time", command=self.toggle_sleep)
        self.menu.add_checkbutton(label="Follow my mouse", variable=self.follow, command=self.on_follow)
        self.menu.add_command(label="Say something", command=lambda: self.say(random.choice(self.lines())))
        kinds = tk.Menu(self.menu, tearoff=0)
        n_groups = 3
        size = -(-len(ANIMAL_KINDS) // n_groups)
        chunks = [ANIMAL_KINDS[i:i + size] for i in range(0, len(ANIMAL_KINDS), size)]
        groups = [("Critters", CRITTERS)] + [(f"Animals: {c[0]} – {c[-1]}", c) for c in chunks]
        for group, members in groups:
            sub = tk.Menu(kinds, tearoff=0)
            for k in members:
                sub.add_radiobutton(label=k, value=k, variable=self.kind_var, command=self.change_kind)
            kinds.add_cascade(label=group, menu=sub)
        self.menu.add_cascade(label="Change kind", menu=kinds)
        self.color_var = tk.IntVar(master=root, value=self.palette)
        self.color_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Change color", menu=self.color_menu)
        self.menu.add_command(label="Rename…", command=self.rename)
        self.menu.add_separator()
        self.menu.add_command(label="Add a friend", command=lambda: app.add_pet(x=self.wx))
        self.menu.add_checkbutton(label="Show name tags", variable=app.name_tags)
        self.menu.add_command(label="Suggest an animal…", command=self.suggest)
        self.menu.add_command(label="Support Blipville ♥", command=self.support)
        self.menu.add_separator()
        self.menu.add_command(label=f"Goodbye, {name}", command=self.quit)
        self.menu.add_command(label="Goodbye everyone (quit)", command=app.quit_all)

        self.place()

    # ------------------------------------------------------------------ helpers
    def place(self):
        self.root.geometry(f"{W}x{H}+{int(self.wx)}+{int(self.wy)}")

    def set_state(self, state, seconds=0.0):
        self.state = state
        self.state_until = time.monotonic() + seconds

    def say(self, text, seconds=3.0):
        self.bubble = (text, time.monotonic() + seconds)

    def set_face(self, face, seconds):
        self.face, self.face_until = face, time.monotonic() + seconds

    def burst(self, kind, n):
        for _ in range(n):
            self.particles.append({
                "kind": kind, "x": W / 2 + random.uniform(-26, 26), "y": H - ART_H * SCALE + random.uniform(-6, 6),
                "vx": random.uniform(-0.6, 0.6), "vy": random.uniform(-2.2, -1.2), "life": random.uniform(1.0, 1.6),
                "born": time.monotonic(),
            })

    def pick_walk_target(self):
        return random.uniform(self.left + 10, self.right - W - 10)

    # ------------------------------------------------------------------ actions
    def pet(self):
        if self.state == "sleep":
            self.wake()
            return
        self.say(random.choice(LINES_PET), 2)
        self.set_face("happy", 1.5)
        self.burst("heart", 4)
        if self.state not in ("fall", "held"):
            self.vy, self.vx = -7, 0
            self.set_state("fall")

    def feed(self):
        if self.state == "sleep":
            self.wake()
        cx = self.wx + W / 2 + random.choice([-1, 1]) * random.uniform(45, 85)
        cx = min(max(cx, self.left + 30), self.right - 30)
        self.cookie = {"x": cx, "y": 0.0, "vy": 0.0, "landed": False}
        self.say("ooh! a cookie!", 2)
        self.set_face("surprised", 1.0)

    def toggle_sleep(self):
        if self.state == "sleep":
            self.wake()
        elif self.state not in ("held", "fall"):
            self.set_state("sleep", 20)
            self.say("good night...", 2)

    def wake(self):
        self.set_state("idle", 1.5)
        self.say(random.choice(LINES_WAKE), 2.5)
        self.set_face("surprised", 0.8)

    def on_follow(self):
        if self.follow.get():
            self.say("right behind you!", 2)
            if self.state == "sleep":
                self.wake()

    def next_color(self):
        self.palette = (self.palette + 1) % len(kind_colors(self.kind))
        self.color_var.set(self.palette)
        self.say(f"{kind_colors(self.kind)[self.palette]['name'].lower()}!", 1.5)
        self.burst("heart", 2)

    def lines(self):
        return LINES_IDLE + VARIANTS[self.kind]["lines"] * 2

    def change_kind(self):
        self.kind = self.kind_var.get()
        self.palette = default_color(self.kind)
        self.color_var.set(self.palette)
        self.say(f"i'm a {self.kind} now!", 2)
        self.set_face("happy", 1.2)
        self.burst("heart", 3)

    def rename(self):
        from tkinter import simpledialog
        new = simpledialog.askstring("Rename", f"New name for {self.name}:", initialvalue=self.name, parent=self.root)
        if new and new.strip():
            self.name = new.strip()[:16]
            self.root.title(self.name)
            self.menu.entryconfigure(self.menu.index("end") - 1, label=f"Goodbye, {self.name}")
            self.say(f"call me {self.name}!", 2)
            self.set_face("happy", 1.2)

    def support(self):
        self.say(random.choice(["you're the best!! <3", "thank you for keeping blipville alive!", "*happy wiggle*"]), 2.5)
        self.set_face("happy", 1.5)
        self.burst("heart", 5)
        try:
            webbrowser.open(SUPPORT_URL)
        except Exception:  # noqa: BLE001
            self.say("couldn't open the browser :(", 2.5)

    def suggest(self):
        self.say("ooh, a new friend? tell me!", 2.5)
        self.set_face("happy", 1.5)
        try:
            webbrowser.open(SUGGEST_URL)
        except Exception:  # noqa: BLE001
            self.say("couldn't open the browser :(", 2.5)

    def quit(self):
        self.app.remove(self)

    # ------------------------------------------------------------------ mouse
    def on_press(self, e):
        self.press = (e.x_root, e.y_root, self.wx, self.wy, time.monotonic())
        self.drag_hist = [(time.monotonic(), e.x_root, e.y_root)]

    def on_drag(self, e):
        if not self.press:
            return
        px, py, wx0, wy0, _ = self.press
        if self.state != "held" and abs(e.x_root - px) + abs(e.y_root - py) < 5:
            return
        if self.state != "held":
            self.set_state("held")
            self.say(random.choice(LINES_HELD), 2.5)
            self.set_face("surprised", 9999)
        self.wx, self.wy = wx0 + e.x_root - px, wy0 + e.y_root - py
        self.drag_hist.append((time.monotonic(), e.x_root, e.y_root))
        self.drag_hist = self.drag_hist[-6:]
        self.place()

    def on_release(self, e):
        if self.state == "held":
            t0, x0, y0 = self.drag_hist[0]
            dt = max(time.monotonic() - t0, 1 / FPS)
            self.vx = max(-40, min(40, (e.x_root - x0) / dt / FPS))
            self.vy = max(-40, min(40, (e.y_root - y0) / dt / FPS))
            self.set_face("surprised", 0.6)
            self.set_state("fall")
        else:
            self.pet()
        self.press = None

    def pick_color(self):
        self.palette = self.color_var.get()
        self.say(f"{kind_colors(self.kind)[self.palette]['name'].lower()}!", 1.5)
        self.burst("heart", 2)

    def on_menu(self, e):
        self.color_menu.delete(0, "end")
        for i, col in enumerate(kind_colors(self.kind)):
            self.color_menu.add_radiobutton(label=col["name"], value=i, variable=self.color_var, command=self.pick_color)
        self.menu.entryconfigure(2, label="Wake up" if self.state == "sleep" else "Nap time")
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    # ------------------------------------------------------------------ brain
    def decide(self, now):
        hour = time.localtime().tm_hour
        sleepy = self.energy < 25 or (hour >= 23 or hour < 6) and random.random() < 0.15
        if sleepy:
            self.say("*yawn* nap time...", 2.5)
            self.set_state("sleep", 20)
            return
        if self.hunger > 70 and now - self.last_hungry_whine > 25:
            self.last_hungry_whine = now
            self.say(random.choice(LINES_HUNGRY), 3)
        r = random.random()
        if r < 0.45:
            self.target_x = self.pick_walk_target()
            self.set_state("walk", 12)
        elif r < 0.60:
            mx = self.root.winfo_pointerx()
            self.target_x = min(max(mx - W / 2, self.left), self.right - W)
            self.set_state("walk", 6)
        elif r < 0.75:
            self.say(random.choice(self.lines()), 3)
            self.set_state("idle", random.uniform(2, 4))
        else:
            self.set_state("idle", random.uniform(2, 5))

    def update(self, now):
        dt = 1 / FPS
        if self.state != "sleep":
            self.energy = max(0, self.energy - dt * 0.12)     # ~14 min from full to sleepy
        self.hunger = min(100, self.hunger + dt * 0.08)        # gets hungry after ~15 min

        # cookie physics (in screen x, canvas y)
        ck = self.cookie
        if ck and not ck["landed"]:
            ck["vy"] += 0.6
            ck["y"] += ck["vy"]
            if ck["y"] >= H - 6 * 3:
                ck["y"], ck["landed"] = H - 6 * 3, True
        if ck and ck["landed"] and self.state in ("idle", "walk") and not self.follow.get():
            self.target_x = ck["x"] - W / 2
            self.state = "walk"
            self.state_until = now + 10

        st = self.state
        if st == "held":
            return
        if st == "fall":
            self.vy += 1.1
            self.wx += self.vx
            self.wy += self.vy
            if self.wx < self.left:
                self.wx, self.vx = self.left, -self.vx * 0.6
            elif self.wx > self.right - W:
                self.wx, self.vx = self.right - W, -self.vx * 0.6
            if self.wy < self.top - H / 2 and self.vy < 0:
                self.vy *= -0.3
            if self.wy >= self.ground:
                self.wy = self.ground
                hard = self.vy > 14
                if self.vy > 6:
                    self.vy = -self.vy * 0.35
                    self.vx *= 0.7
                    self.squash_until = now + 0.15
                    if hard:
                        self.say(random.choice(LINES_LAND), 2)
                else:
                    self.vy = self.vx = 0
                    self.squash_until = now + 0.2
                    self.set_state("idle", random.uniform(0.6, 1.5))
            self.place()
            return
        if st == "sleep":
            self.energy = min(100, self.energy + dt * 2.0)
            if random.random() < dt * 0.8:
                self.particles.append({"kind": "z", "x": W / 2 + 18, "y": H - ART_H * SCALE, "vx": 0.5,
                                       "vy": -0.8, "life": 2.5, "born": now})
            if self.energy >= 100 and now > self.state_until:   # nap at least 20 s, wake when rested
                self.wake()
            return
        if st == "eat":
            if now > self.state_until:
                self.hunger = 0
                self.energy = min(100, self.energy + 15)
                self.cookie = None
                self.say(random.choice(LINES_EAT), 2.5)
                self.set_face("happy", 2)
                self.burst("heart", 5)
                self.set_state("idle", 2)
            elif random.random() < 0.3:
                self.particles.append({"kind": "crumb", "x": W / 2 + random.uniform(-6, 6), "y": H - 22,
                                       "vx": random.uniform(-1.5, 1.5), "vy": random.uniform(-3, -1), "life": 0.6, "born": now})
            return

        # follow-my-mouse mode overrides wandering
        if self.follow.get():
            mx = self.root.winfo_pointerx()
            goal = min(max(mx - W / 2, self.left), self.right - W)
            if abs(goal - self.wx) > 50:
                self.target_x, self.state = goal, "walk"
            else:
                self.state = "idle"
                self.state_until = now + 1

        if self.state == "walk" and self.target_x is not None:
            speed = (3.2 if self.follow.get() else 2.0) * VARIANTS[self.kind].get("speed", 1.0)
            d = self.target_x - self.wx
            self.facing = 1 if d > 0 else -1
            if abs(d) <= speed or now > self.state_until:
                self.wx = self.target_x if abs(d) <= speed else self.wx
                self.target_x = None
                if self.cookie and self.cookie["landed"] and abs(self.cookie["x"] - (self.wx + W / 2)) < 30:
                    self.set_state("eat", 1.8)
                    self.set_face("munch", 1.8)
                else:
                    self.set_state("idle", random.uniform(1, 3))
            else:
                self.wx += speed * self.facing
            self.place()
        elif self.state == "idle" and now > self.state_until and not self.follow.get():
            self.decide(now)

    # ------------------------------------------------------------------ drawing
    def eye_offset(self):
        mx, my = self.root.winfo_pointerxy()
        cx, cy = self.wx + W / 2, self.wy + H - ART_H * SCALE + (VARIANTS[self.kind]["eyes"] + 1) * SCALE
        dx, dy = mx - cx, my - cy
        if math.hypot(dx, dy) < 30:
            return 0, 0
        ox = -1 if dx < -40 else (1 if dx > 40 else 0)
        oy = -1 if dy < -80 else (1 if dy > 40 else 0)
        return ox, oy

    def lift(self, now):
        """How many pixels above the ground the art floats (hopping, hovering, fluttering)."""
        move = VARIANTS[self.kind]["move"]
        moving = self.state == "walk"
        if move == "float":
            return 2 if self.state == "sleep" else int(9 + 4 * math.sin(now * 2.5))
        if move == "hop" and moving:
            return int(abs(math.sin(now * 7)) * 12)
        if move == "flutter" and moving:
            return int(8 + 3 * math.sin(now * 12))
        return 0

    def build_art(self, now):
        v = VARIANTS[self.kind]
        colors = kind_colors(self.kind)
        pal = {**colors[self.palette % len(colors)], **v.get("extra", {})}
        g = [[None] * ART_W for _ in range(ART_H)]
        body = pal.get("art") or v["body"]          # some colors come with their own markings
        if v.get("alt") and self.state in ("walk", "fall", "held") and int(now * 10) % 2:
            body = v["alt"]                        # wing flap
        squash = now < self.squash_until
        lying = self.state == "sleep" or squash
        shift = 1 if lying else 0
        for y, row in enumerate(body):
            for x, ch in enumerate(row):
                if ch != "." and y + shift < ART_H:
                    g[y + shift][x] = pal.get(ch, pal["o"])
        if not lying and v["feet"]:
            feet_set = v["feet"]
            if self.state in ("fall", "held") or self.lift(now) > 3:
                feet = feet_set["air"]
            elif self.state == "walk":
                feet = feet_set["walk1"] if int(now * 6) % 2 else feet_set["walk2"]
            else:
                feet = feet_set["stand"]
            for x, ch in enumerate(feet):
                if ch != ".":
                    if 0 <= x + v.get("dx", 0) < ART_W:
                        g[12][x + v.get("dx", 0)] = pal.get("f", pal["o"])

        face_dy = v["eyes"] - 5                    # faces are drawn for eyes on row 5
        face_dx = v.get("dx", 0)                   # ...and centered, unless the head is off to one side

        def px(x, y, color):
            y += shift + face_dy
            x += face_dx
            if 0 <= x < ART_W and 0 <= y < ART_H:
                g[y][x] = color

        face = self.face if now < self.face_until else "normal"
        if self.state == "sleep":
            face = "sleep"
        e, white = pal["e"], "#ffffff"
        r_, g_, b_ = (int(e[i:i + 2], 16) for i in (1, 3, 5))
        if 0.299 * r_ + 0.587 * g_ + 0.114 * b_ > 150:   # light eyes: dark pupil dot instead of a shine
            white = pal["o"]
        blinking = now < self.blink_until
        if face == "sleep" or (blinking and face == "normal"):
            for x in (4, 5, 10, 11):
                px(x, 6, e)
        elif face == "happy":
            for ex in (4, 9):
                px(ex, 6, e); px(ex + 1, 5, e); px(ex + 2, 6, e)
        elif face == "munch":
            for ex in (4, 10):
                px(ex, 6, e); px(ex + 1, 6, e)
        else:
            ox, oy = (0, 0) if face == "surprised" else self.eye_offset()
            for ex in (4, 10):
                size = 2
                for yy in range(size):
                    for xx in range(size):
                        px(ex + ox + xx, 5 + oy + yy, e)
                px(ex + ox, 5 + oy, white)
        # mouth (beaks and snouts are part of the art instead)
        if not v.get("mouth", True):
            pass
        elif face == "surprised":
            px(7, 8, e); px(8, 8, e); px(7, 9, e); px(8, 9, e)
        elif face in ("happy",):
            px(6, 8, e); px(7, 9, e); px(8, 9, e); px(9, 8, e)
        elif face == "munch":
            if int(now * 8) % 2:
                px(7, 8, e); px(8, 8, e); px(7, 9, e); px(8, 9, e)
            else:
                px(7, 9, e); px(8, 9, e)
        elif face != "sleep":
            px(7, 9, e); px(8, 9, e)
        return g

    def draw(self, now):
        c = self.canvas
        c.delete("all")
        ox = (W - ART_W * SCALE) // 2
        oy = H - ART_H * SCALE - self.lift(now)
        # pixel art, merging runs of the same color into one rectangle per row
        for y, row in enumerate(self.build_art(now)):
            x = 0
            while x < ART_W:
                color = row[x]
                if color is None:
                    x += 1
                    continue
                x2 = x
                while x2 + 1 < ART_W and row[x2 + 1] == color:
                    x2 += 1
                c.create_rectangle(ox + x * SCALE, oy + y * SCALE, ox + (x2 + 1) * SCALE, oy + (y + 1) * SCALE,
                                   fill=color, outline="")
                x = x2 + 1

        # cookie
        ck = self.cookie
        if ck:
            cx = ck["x"] - self.wx
            if self.state == "eat":
                cx = W / 2 + 10 * self.facing
            bites = 0 if self.state != "eat" else int((1.8 - max(0, self.state_until - now)) / 0.45)
            for y, row in enumerate(COOKIE):
                for x, ch in enumerate(row):
                    if ch == "." or (x >= 6 - bites and self.state == "eat"):
                        continue
                    col = "#c98a4b" if ch == "c" else "#5a3418"
                    X, Y = cx - 9 + x * 3, ck["y"] + y * 3
                    c.create_rectangle(X, Y, X + 3, Y + 3, fill=col, outline="")

        # particles
        alive = []
        for p in self.particles:
            age = now - p["born"]
            if age > p["life"]:
                continue
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["kind"] == "crumb":
                p["vy"] += 0.4
            alive.append(p)
            if p["kind"] == "heart":
                for y, row in enumerate(HEART):
                    for x, ch in enumerate(row):
                        if ch == "x":
                            X, Y = p["x"] + x * 3, p["y"] + y * 3
                            c.create_rectangle(X, Y, X + 3, Y + 3, fill="#ff4f7b", outline="")
            elif p["kind"] == "z":
                s = 2 + int(age)
                for y, row in enumerate(ZED):
                    for x, ch in enumerate(row):
                        if ch == "x":
                            X, Y = p["x"] + x * s, p["y"] + y * s
                            c.create_rectangle(X, Y, X + s, Y + s, fill="#bcd2ff", outline="")
            elif p["kind"] == "crumb":
                c.create_rectangle(p["x"], p["y"], p["x"] + 3, p["y"] + 3, fill="#c98a4b", outline="")
        self.particles = alive

        # name tag
        tag_h = 0
        if self.app.name_tags.get():
            t = c.create_text(W / 2, oy - 6, text=self.name, font=("Segoe UI", 8, "bold"), fill="#ffffff", anchor="s")
            x1, y1, x2, y2 = c.bbox(t)
            c.create_rectangle(x1 - 4, y1 - 1, x2 + 4, y2 + 1, fill="#1d1b26", outline="#1d1b26")
            c.tag_raise(t)
            tag_h = y2 - y1 + 6

        # speech bubble
        if self.bubble and now < self.bubble[1]:
            t = c.create_text(W / 2, 0, text=self.bubble[0], font=("Segoe UI", 10, "bold"),
                              fill="#222222", width=W - 30, justify="center", anchor="s")
            x1, y1, x2, y2 = c.bbox(t)
            top_of_pet = oy - (6 if self.state != "sleep" else 2) - tag_h
            h = y2 - y1
            c.move(t, 0, top_of_pet - 12)
            x1, y1, x2, y2 = x1 - 8, top_of_pet - 12 - h - 5, x2 + 8, top_of_pet - 7
            # bubble sits on top of everything else (hearts, Zzz), text on top of the bubble
            c.create_polygon(W / 2 - 5, y2 - 1, W / 2 + 5, y2 - 1, W / 2, y2 + 6, fill="#ffffff", outline="#222222", width=2)
            c.create_rectangle(x1, y1, x2, y2, fill="#ffffff", outline="#222222", width=2)
            c.create_line(W / 2 - 4, y2 - 1, W / 2 + 4, y2 - 1, fill="#ffffff", width=3)
            c.tag_raise(t)
        else:
            self.bubble = None

    # ------------------------------------------------------------------ loop
    def step(self, now):
        if now > self.next_blink:
            self.blink_until = now + 0.15
            self.next_blink = now + random.uniform(2, 6)
        self.update(now)
        self.draw(now)


class App:
    """Runs every pet on screen."""
    MAX_PETS = 12

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Blipville")
        self.root.withdraw()                       # pets live in their own little windows
        self.name_tags = tk.BooleanVar(master=self.root, value=True)
        self.pets = []
        self.add_pet("Blip", "Blip")
        self.last_topmost = time.monotonic()
        self.tick()

    def add_pet(self, kind=None, name=None, x=None):
        if len(self.pets) >= self.MAX_PETS:
            if self.pets:
                self.pets[0].say("that's enough friends for now!", 2.5)
            return None
        kind = kind or random.choice(KINDS)
        used = {p.name for p in self.pets}
        name = name or random.choice([n for n in NAMES if n not in used] or NAMES)
        if x is not None:
            x += random.choice([-1, 1]) * random.uniform(80, 160)
        pet = Blip(self, kind, name, x)
        self.pets.append(pet)
        pet.say(f"hi! i'm {name}", 2.5)
        return pet

    def remove(self, pet):
        if pet in self.pets:
            self.pets.remove(pet)
            pet.root.destroy()
        if not self.pets:
            self.root.destroy()

    def quit_all(self):
        self.root.destroy()

    def socialize(self, now):
        """Pets that bump into each other say hi (at most once a minute per pair)."""
        calm = ("idle", "walk")
        for i, a in enumerate(self.pets):
            for b in self.pets[i + 1:]:
                if a.state not in calm or b.state not in calm or abs(a.wx - b.wx) > 90:
                    continue
                if now - a.greeted.get(b.name, -999) < 60:
                    continue
                a.greeted[b.name] = b.greeted[a.name] = now
                a.say(random.choice([f"hi {b.name}!", f"oh, {b.name}!", f"hey {b.name} :)"]), 2.5)
                b.say(random.choice([f"hi {a.name}!", "oh hi!", f"{a.name}!! :D"]), 2.5)
                a.set_face("happy", 1.5)
                b.set_face("happy", 1.5)
                a.facing = 1 if b.wx > a.wx else -1
                b.facing = -a.facing

    def tick(self):
        now = time.monotonic()
        try:
            for pet in list(self.pets):
                pet.step(now)
            self.socialize(now)
            if now - self.last_topmost > 5:        # stay above other windows
                for pet in self.pets:
                    pet.root.attributes("-topmost", True)
                self.last_topmost = now
        except tk.TclError:
            return
        self.root.after(int(1000 / FPS), self.tick)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
