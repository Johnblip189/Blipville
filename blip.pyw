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
import json
import math
import os
import random
import subprocess
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

# ----------------------------------------------------------------------------- Night Shift crew
# Night Shift crew: original animatronic pets. r = rivet, s = metal seam, k = teeth, d = dark hinge line
ROBOTS = {
 "Robo Bear": dict(eyes=5, mouth=False, body=[
    ".ooo........ooo.",
    "oaaao......oaaao",
    "oaaboooooooobaao",
    ".obrbbbbbbbbrbo.",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obpbbllllllbbpbo",
    "obbblllnnlllbbbo",
    "osssskkkkkksssso",
    ".obbbllllllbbbo.",
    "..obrbbbbbbrbo.."], colors=[
    dict(name="Arcade",   o="#0e2a3a", b="#3ab8c8", l="#c8f4f8", a="#1e7a8a", r="#d8dde6", s="#5a6170", k="#ffffff", n="#0e2a3a", p="#ff9fb0", e="#ffd23a"),
    dict(name="Rusty",    o="#2a1206", b="#b8643a", l="#e8c0a0", a="#7a3a1a", r="#c8a070", s="#4a3424", k="#f2e6c8", n="#1a0a04", p="#e87a6a", e="#ff8a1f"),
    dict(name="Bubblegum", o="#5a1a3a", b="#ff9fcf", l="#fff0f8", a="#e85a9a", r="#ffffff", s="#a8708a", k="#ffffff", n="#5a1a3a", p="#ff5f9f", e="#5af0ff"),
    dict(name="Midnight", o="#06060c", b="#2a2a3a", l="#4a4a62", a="#16161f", r="#7a7a8a", s="#12121a", k="#d8d8e0", n="#06060c", p="#5a2a3a", e="#ff3b3b"),
 ]),
 "Robo Bunny": dict(eyes=6, mouth=False, body=[
    "...oo......oo...",
    "..obao....oabo..",
    "..obao....oabo..",
    "..obro....orbo..",
    ".obbbooooooobbo.",
    ".obbbbbbbbbbbbo.",
    "obbbbbbbbbbbbbbo",
    "obbbbbbbbbbbbbbo",
    "obpbbllnnllbbpbo",
    "obbbbllllllbbbbo",
    "osssskkkkkksssso",
    "..obrbbbbbbrbo.."], colors=[
    dict(name="Mint",     o="#0e2a1a", b="#7adcaa", l="#e0f8ec", a="#ff9fb8", r="#ffffff", s="#4a7a62", k="#ffffff", n="#ff7a9a", p="#ff9fb8", e="#ff4a6a"),
    dict(name="Rusty",    o="#2a1206", b="#c87a4a", l="#f0d0b0", a="#7a3a1a", r="#d8b080", s="#4a3424", k="#f2e6c8", n="#1a0a04", p="#e87a6a", e="#ffd23a"),
    dict(name="Sunset",   o="#3a1406", b="#ff9a4a", l="#fff0dc", a="#ffd06a", r="#ffffff", s="#a85a2a", k="#ffffff", n="#a82a2a", p="#ff6a5a", e="#3a1406"),
    dict(name="Midnight", o="#06060c", b="#2a2a3a", l="#4a4a62", a="#16161f", r="#7a7a8a", s="#12121a", k="#d8d8e0", n="#06060c", p="#5a2a3a", e="#ff3b3b"),
 ]),
 "Robo Hen": dict(eyes=5, mouth=False, body=[
    "......o..o......",
    ".......oo.......",
    "....oooooooo....",
    "..oobrbbbbrboo..",
    ".obbbbbbbbbbbbo.",
    ".obbbbbbbbbbbbo.",
    "obpbbbbbbbbbbpbo",
    "obbbbbnnnnbbbbbo",
    "osssssddddssssso",
    "obbbbbnnnnbbbbbo",
    ".obbbbbbbbbbbbo.",
    "..oobrbbbbrboo.."], colors=[
    dict(name="Classic",  o="#3a3a44", b="#f6f6f8", r="#a8aeb8", s="#8a909c", n="#ff8a1f", d="#3a1a04", p="#ff7a7a", e="#1a1a20", f="#ff8a1f"),
    dict(name="Rusty",    o="#2a1206", b="#b8643a", r="#d8b080", s="#4a3424", n="#e8c03a", d="#1a0a04", p="#e87a6a", e="#ffd23a", f="#e8c03a"),
    dict(name="Arcade",   o="#3a0a14", b="#e8303a", r="#ffffff", s="#8a1a24", n="#ffd23a", d="#3a0a14", p="#ff9f9f", e="#5af0ff", f="#ffd23a"),
    dict(name="Midnight", o="#06060c", b="#2a2a3a", r="#7a7a8a", s="#12121a", n="#5a4a2a", d="#06060c", p="#5a2a3a", e="#ff3b3b", f="#3a3a4a"),
 ]),
}
ANIMALS.update(ROBOTS)

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
    "Robo Bear":  ("walk", ["*servo whirr*", "beep boop... i mean, hi", "my joints need oiling", "i'm totally not watching you"]),
    "Robo Bunny": ("hop",  ["*boing* *clank*", "battery at 12%...", "who turned off the lights?", "*ears twitch mechanically*"]),
    "Robo Hen":   ("walk", ["*mechanical clucking*", "bawk. boop.", "my jaw squeaks", "still on the night shift"]),
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
# ----------------------------------------------------------------------------- 50 more animals
# Everyday animals (free) and rare ones that only hatch from Mystery Eggs (bought with hearts).
NEW_ANIMALS = {'Rabbit': {'eyes': 5,
            'move': 'hop',
            'lines': ['*nose wiggle*', 'carrot?', 'binky!', '*thump thump*'],
            'body': ['....oooooooo....',
                     '..oobbbbbbbboo..',
                     'oaaobbbbbbbboaao',
                     'oaaobbbbbbbboaao',
                     'oaaobbbbbbbboaao',
                     'oaaobbbbbbbboaao',
                     'oaaobbbbbbbboaao',
                     '.oaobpbbbbpboao.',
                     '..oobbbnnbbboo..',
                     '...obbllllbbo...',
                     '...obbbbbbbbo...',
                     '....oooooooo....'],
            'colors': [{'name': 'White',
                        'o': '#6a6070',
                        'b': '#ffffff',
                        'a': '#f0e6ea',
                        'l': '#fff4f6',
                        'p': '#ffb0c0',
                        'n': '#ff8fa3',
                        'e': '#d81e3a'},
                       {'name': 'Brown',
                        'o': '#2a1a0e',
                        'b': '#a8784a',
                        'a': '#8a5e36',
                        'l': '#e8cfae',
                        'p': '#ff9f8a',
                        'n': '#3a2414',
                        'e': '#140a04'},
                       {'name': 'Gray',
                        'o': '#22252c',
                        'b': '#9aa1ad',
                        'a': '#7a828e',
                        'l': '#e6e9ee',
                        'p': '#ffb0c0',
                        'n': '#ff8fa3',
                        'e': '#0a0b0e'},
                       {'name': 'Dutch',
                        'o': '#14141a',
                        'b': '#2e2e36',
                        'a': '#2e2e36',
                        'l': '#ffffff',
                        'p': '#ffb0c0',
                        'n': '#ff8fa3',
                        'e': '#e8e0c8'}]},
 'Goat': {'eyes': 5,
          'move': 'walk',
          'lines': ['meeeh!', '*eats your homework*', "i'll climb anything", 'baa... wait no'],
          'body': ['...h........h...',
                   '..hh........hh..',
                   'oaohoooooooohoao',
                   '.obbbbbbbbbbbbo.',
                   'obbbbbbbbbbbbbbo',
                   'obbbbbbbbbbbbbbo',
                   'obbbbbbbbbbbbbbo',
                   '.obpbbbbbbbbpbo.',
                   '..obbbbnnbbbbo..',
                   '..obbbbbbbbbbo..',
                   '...obbllllbbo...',
                   '.....ollllo.....'],
          'colors': [{'name': 'White',
                      'o': '#5a5466',
                      'b': '#f6f2ea',
                      'a': '#ffd0d8',
                      'h': '#a8a090',
                      'l': '#e8e0d0',
                      'p': '#ffb0c0',
                      'n': '#8a7a7a',
                      'e': '#a87a1a'},
                     {'name': 'Brown',
                      'o': '#24160a',
                      'b': '#8a5a34',
                      'a': '#c08a5a',
                      'h': '#e8d8b8',
                      'l': '#5a3a1a',
                      'p': '#e88a7a',
                      'n': '#1a0e06',
                      'e': '#d8a01a'},
                     {'name': 'Black',
                      'o': '#06060a',
                      'b': '#2a2a32',
                      'a': '#4a4a55',
                      'h': '#a8a8b0',
                      'l': '#14141a',
                      'p': '#a85a6a',
                      'n': '#06060a',
                      'e': '#e8c01a'}]},
 'Donkey': {'eyes': 5,
            'move': 'walk',
            'lines': ['hee-haw!', '*stubborn noises*', "i'm not slow, i'm relaxed", 'carrot me'],
            'body': ['.o............o.',
                     '.oo..........oo.',
                     '.oao........oao.',
                     '.oaboooooooobao.',
                     'obbbbbbbbbbbbbbo',
                     'obbbbbbbbbbbbbbo',
                     'obbbbbbbbbbbbbbo',
                     '.obpbbbbbbbbpbo.',
                     '..obllllllllbo..',
                     '..oblldlldllbo..',
                     '..obllllllllbo..',
                     '...oooooooooo...'],
            'colors': [{'name': 'Gray',
                        'o': '#22252c',
                        'b': '#8a909c',
                        'a': '#3a3f4a',
                        'l': '#e6e9ee',
                        'p': '#ffb0c0',
                        'd': '#3a3f4a',
                        'e': '#0a0b0e'},
                       {'name': 'Brown',
                        'o': '#24160a',
                        'b': '#8a6a4a',
                        'a': '#3a2414',
                        'l': '#efe2cf',
                        'p': '#e88a7a',
                        'd': '#3a2414',
                        'e': '#0e0804'},
                       {'name': 'Spotted',
                        'o': '#22252c',
                        'b': '#f2f2f4',
                        'a': '#5a3a22',
                        'l': '#d8ccc0',
                        'p': '#ffb0c0',
                        'd': '#5a3a22',
                        'e': '#0a0b0e'}]},
 'Rhino': {'eyes': 5,
           'move': 'walk',
           'speed': 0.8,
           'lines': ['*charges... slowly*', 'my horn is my whole personality', 'snort!', 'big but gentle'],
           'body': ['................',
                    '..oo........oo..',
                    '.oaooooooooooao.',
                    '.obbbbbbbbbbbbo.',
                    'obbbbbbbbbbbbbbo',
                    'obbbbbbbbbbbbbbo',
                    'obbbbbbhhbbbbbbo',
                    'obbbbbhhhhbbbbbo',
                    'obbbbllllllbbbbo',
                    'obbbldllllldbbbo',
                    '.obbbllllllbbbo.',
                    '..oooooooooooo..'],
           'colors': [{'name': 'Gray',
                       'o': '#22262e',
                       'b': '#8a909c',
                       'a': '#c8a8b0',
                       'h': '#e8e0d0',
                       'l': '#a8aeb8',
                       'd': '#3a3f4a',
                       'e': '#0e0f12'},
                      {'name': 'White',
                       'o': '#5a6170',
                       'b': '#d8dce4',
                       'a': '#ffc0cc',
                       'h': '#fff8e8',
                       'l': '#eef0f4',
                       'd': '#7a8494',
                       'e': '#22262e'},
                      {'name': 'Blue',
                       'o': '#14264a',
                       'b': '#7ab8ff',
                       'a': '#ff9fc8',
                       'h': '#ffffff',
                       'l': '#c8e4ff',
                       'd': '#3a6aa8',
                       'e': '#0a1430'}]},
 'Lemur': {'eyes': 5,
           'move': 'hop',
           'lines': ['*sunbathes*', 'move it move it!', 'ring-tail club', 'i like to climb'],
           'body': ['.o............o.',
                    '.oao........oao.',
                    '.oaboooooooobao.',
                    '.obbbbbbbbbbbbo.',
                    'obllllbbbbllllbo',
                    'ollssssllssssllo',
                    'ollssssllssssllo',
                    'ollllllllllllllo',
                    'ollllllssllllllo',
                    'obllllssssllllbo',
                    '.obbllllllllbbo.',
                    '..oooooooooooo..'],
           'colors': [{'name': 'Ring-tailed',
                       'o': '#1c1e24',
                       'b': '#8a909c',
                       'l': '#f6f6f8',
                       's': '#22252c',
                       'a': '#22252c',
                       'e': '#ff9a1f'},
                      {'name': 'Red-ruffed',
                       'o': '#2a0e04',
                       'b': '#c0401e',
                       'l': '#1e1612',
                       's': '#0a0604',
                       'a': '#fff4e6',
                       'e': '#ffd23a'},
                      {'name': 'Sifaka',
                       'o': '#5a5466',
                       'b': '#f6f2ea',
                       'l': '#ffffff',
                       's': '#2a2a32',
                       'a': '#2a2a32',
                       'e': '#ffd23a'}]},
 'Meerkat': {'eyes': 5,
             'move': 'walk',
             'lines': ['*stands guard*', "i'm on lookout duty", 'did you see that?!', 'family first'],
             'body': ['..oo........oo..',
                      '.oaao......oaao.',
                      '.oaboooooooobao.',
                      '.obbbbbbbbbbbbo.',
                      'obbbbbbbbbbbbbbo',
                      'obbsssbbbbsssbbo',
                      'obbsssbbbbsssbbo',
                      'obbbbbllllbbbbbo',
                      'obbbbllnnllbbbbo',
                      'obbbbllllllbbbbo',
                      '.obbbbbbbbbbbbo.',
                      '..obbbbbbbbbbo..'],
             'colors': [{'name': 'Desert',
                         'o': '#3a2810',
                         'b': '#d8b07a',
                         'a': '#5a3a1a',
                         's': '#3a2414',
                         'l': '#f4e2c4',
                         'n': '#1a1006',
                         'p': '#ff9f7a',
                         'e': '#0e0804'},
                        {'name': 'Dusky',
                         'o': '#22201c',
                         'b': '#a8987a',
                         'a': '#3a3020',
                         's': '#2a2418',
                         'l': '#e8dcc0',
                         'n': '#14120e',
                         'p': '#e88a7a',
                         'e': '#0a0806'}]},
 'Ferret': {'eyes': 5,
            'move': 'walk',
            'speed': 1.4,
            'lines': ['*war dance*', 'dook dook!', 'i stole your sock', 'zoomies!!'],
            'body': ['..oo........oo..',
                     '.oaao......oaao.',
                     '.oaboooooooobao.',
                     '.obbbbbbbbbbbbo.',
                     'ollllllllllllllo',
                     'osssssllllssssso',
                     'obssssllllssssbo',
                     'obbllllllllllbbo',
                     'oblllllnnlllllbo',
                     'obbllllllllllbbo',
                     '.obbbbbbbbbbbbo.',
                     '..obbbbbbbbbbo..'],
            'colors': [{'name': 'Sable',
                        'o': '#1e1006',
                        'b': '#6a4a2e',
                        'a': '#e8cfae',
                        'l': '#f4e6d0',
                        's': '#2a1a0e',
                        'n': '#ff8f8f',
                        'p': '#ff9f8a',
                        'e': '#0a0604'},
                       {'name': 'Albino',
                        'o': '#7a6a6a',
                        'b': '#fffaf0',
                        'a': '#ffd0d8',
                        'l': '#ffffff',
                        's': '#f2e6d8',
                        'n': '#ffb0c0',
                        'p': '#ffb0c0',
                        'e': '#d81e3a'},
                       {'name': 'Cinnamon',
                        'o': '#3a1a08',
                        'b': '#b8682a',
                        'a': '#ffd8b0',
                        'l': '#fff0dc',
                        's': '#7a3a14',
                        'n': '#ff9f8a',
                        'p': '#ff9f8a',
                        'e': '#1a0a02'}]},
 'Chinchilla': {'eyes': 5,
                'move': 'hop',
                'lines': ['*dust bath*', 'so soft. so fluffy.', 'boing boing', '*squeak*'],
                'body': ['oooo........oooo',
                         'oaaao......oaaao',
                         'oaaaooooooooaaao',
                         '.oobbbbbbbbbboo.',
                         'obbbbbbbbbbbbbbo',
                         'obbbbbbbbbbbbbbo',
                         'obbbbbbbbbbbbbbo',
                         'obpbdbllllbdbpbo',
                         'obdbbllnnllbbdbo',
                         'obbbbllllllbbbbo',
                         '.obbbllllllbbbo.',
                         '..obbbbbbbbbbo..'],
                'colors': [{'name': 'Standard',
                            'o': '#2a2e36',
                            'b': '#a9b0bc',
                            'a': '#ffc8d0',
                            'l': '#f2f4f7',
                            'd': '#5a606c',
                            'n': '#ff8fa3',
                            'p': '#ffb0c0',
                            'e': '#0e0f12'},
                           {'name': 'Beige',
                            'o': '#5a4a36',
                            'b': '#e8d4b4',
                            'a': '#ffc8c0',
                            'l': '#fff6e6',
                            'd': '#a8906a',
                            'n': '#ff9f9f',
                            'p': '#ffb0b0',
                            'e': '#a81e2e'},
                           {'name': 'Black Velvet',
                            'o': '#0a0a0e',
                            'b': '#3a3a44',
                            'a': '#ffb0c0',
                            'l': '#e6e8ee',
                            'd': '#6a6a78',
                            'n': '#ff8fa3',
                            'p': '#ff9fb0',
                            'e': '#0a0a0e'}]},
 'Guinea Pig': {'eyes': 5,
                'move': 'walk',
                'lines': ['wheek wheek!', '*popcorns*', 'veggies please!', "i'm a potato with feet"],
                'body': ['................',
                         '....oooooooo....',
                         '..oosssbbbbboo..',
                         '.obsssbbbbbbbbo.',
                         'oassbbbbbbbbbbao',
                         'obssbbbbbbbbbbbo',
                         'obbbbbbbbbbsssbo',
                         'obpbbllllllbbpbo',
                         'obbblllnnlllbbbo',
                         'obbbbllllllbbbbo',
                         '.obbbbbbbbbbbbo.',
                         '..oooooooooooo..'],
                'colors': [{'name': 'Tricolor',
                            'o': '#2a1a0e',
                            'b': '#ffffff',
                            's': '#e8903a',
                            'a': '#ffc0b0',
                            'l': '#fff6ee',
                            'n': '#ff9f9f',
                            'p': '#ffb0b0',
                            'e': '#140a04'},
                           {'name': 'Brown & White',
                            'o': '#2a1a0e',
                            'b': '#fff8ee',
                            's': '#7a4a24',
                            'a': '#ffc0b0',
                            'l': '#ffffff',
                            'n': '#ff9f9f',
                            'p': '#ffb0b0',
                            'e': '#140a04'},
                           {'name': 'Cream',
                            'o': '#5a4426',
                            'b': '#fbe7c6',
                            's': '#f0c890',
                            'a': '#ffc0b0',
                            'l': '#fff6e6',
                            'n': '#ff9f9f',
                            'p': '#ffb0b0',
                            'e': '#a81e2e'}]},
 'Mole': {'eyes': 5,
          'move': 'walk',
          'speed': 0.8,
          'lines': ['*digs*', 'where am i?', 'too bright up here', 'dirt is cozy'],
          'body': ['....oooooooo....',
                   '..oobbbbbbbboo..',
                   '.obbbbbbbbbbbbo.',
                   '.obbbbbbbbbbbbo.',
                   'obbbbbbbbbbbbbbo',
                   'obbbbbbbbbbbbbbo',
                   'obbbbbbnnbbbbbbo',
                   'obbbbbnnnnbbbbbo',
                   'okkbbbbnnbbbbkko',
                   'okkbbbbbbbbbbkko',
                   '.obbbbbbbbbbbbo.',
                   '..oooooooooooo..'],
          'colors': [{'name': 'Velvet',
                      'o': '#14101a',
                      'b': '#3a3440',
                      'n': '#ff9fb8',
                      'k': '#ffc0cc',
                      'e': '#0a080e'},
                     {'name': 'Golden',
                      'o': '#3a2408',
                      'b': '#c8a04a',
                      'n': '#ff9f8a',
                      'k': '#ffd0a8',
                      'e': '#1a1004'},
                     {'name': 'Star-nosed',
                      'o': '#0e0a14',
                      'b': '#2a2232',
                      'n': '#ff5f95',
                      'k': '#ffb0c8',
                      'e': '#e8e0f0'}]},
 'Armadillo': {'eyes': 6,
               'move': 'walk',
               'speed': 0.8,
               'lines': ['*rolls into a ball*', 'armored and adorable', 'bonk-proof', '*scurries*'],
               'body': ['..oo........oo..',
                        '.oao.oooooo.oao.',
                        '..osbsbsbsbsbo..',
                        '.osbsbsbsbsbsbo.',
                        'osbsbsbsbsbsbsbo',
                        'ollllllllllllllo',
                        'ollllllllllllllo',
                        'ollllllllllllllo',
                        'olpllllllllllplo',
                        'ollllllnnllllllo',
                        '.ollllllllllllo.',
                        '..oooooooooooo..'],
               'colors': [{'name': 'Nine-banded',
                           'o': '#2a1c10',
                           'b': '#b8946a',
                           's': '#8a6a46',
                           'a': '#e0b8a0',
                           'l': '#e8c8b0',
                           'p': '#ff9f8a',
                           'n': '#5a3a22',
                           'e': '#140a04'},
                          {'name': 'Pink Fairy',
                           'o': '#6a2a44',
                           'b': '#ffc0d6',
                           's': '#ff8fb8',
                           'a': '#ffe0ea',
                           'l': '#fff0f6',
                           'p': '#ff7aa8',
                           'n': '#a83a6a',
                           'e': '#2a0e1a'},
                          {'name': 'Golden',
                           'o': '#3a2408',
                           'b': '#ffd27a',
                           's': '#d8a040',
                           'a': '#fff0d0',
                           'l': '#fff6e0',
                           'p': '#ffa07a',
                           'n': '#7a4a14',
                           'e': '#1a1004'}]},
 'Fennec': {'eyes': 5,
            'move': 'hop',
            'lines': ['my ears hear EVERYTHING', '*big ear wiggle*', 'desert vibes', 'yip yip!'],
            'body': ['oo............oo',
                     'oao..........oao',
                     'oaao........oaao',
                     'oaaboooooooobaao',
                     'obbbbbbbbbbbbbbo',
                     'obbbbbbbbbbbbbbo',
                     'obbbbbbbbbbbbbbo',
                     'olllbbbbbbbblllo',
                     'ollllllnnllllllo',
                     '.ollllllllllllo.',
                     '..ollllllllllo..',
                     '...oooooooooo...'],
            'colors': [{'name': 'Sand',
                        'o': '#3a2810',
                        'b': '#f0d0a0',
                        'a': '#ffc8b0',
                        'l': '#fffaf0',
                        'n': '#2a1a08',
                        'e': '#1a1004'},
                       {'name': 'Cream',
                        'o': '#5a4a36',
                        'b': '#fff2dc',
                        'a': '#ffd0c0',
                        'l': '#ffffff',
                        'n': '#3a2a1a',
                        'e': '#2a1a0e'},
                       {'name': 'Ginger',
                        'o': '#3a1a06',
                        'b': '#e8a050',
                        'a': '#ffc8a0',
                        'l': '#fff4e6',
                        'n': '#1a0a02',
                        'e': '#140802'}]},
 'Corgi': {'eyes': 5,
           'move': 'walk',
           'speed': 1.2,
           'lines': ['*loaf mode*', 'tiny legs, big heart', "the queen's favorite", 'zoom zoom'],
           'body': ['.o............o.',
                    '.oao........oao.',
                    '.oaboooooooobao.',
                    '.obbbbbbbbbbbbo.',
                    'obbbbbbllbbbbbbo',
                    'obbbbbbllbbbbbbo',
                    'obbbbbbllbbbbbbo',
                    'obpbbllllllbbpbo',
                    'obbllllnnllllbbo',
                    'obllllllllllllbo',
                    '.ollllllllllllo.',
                    '..oooooooooooo..'],
           'colors': [{'name': 'Red',
                       'o': '#2a1406',
                       'b': '#e88a3a',
                       'a': '#ffd0b0',
                       'l': '#ffffff',
                       'n': '#1a0a02',
                       'p': '#ff9f8a',
                       'e': '#140802'},
                      {'name': 'Tricolor',
                       'o': '#0a0806',
                       'b': '#2a2420',
                       'a': '#c8803a',
                       'l': '#ffffff',
                       'n': '#0a0806',
                       'p': '#ff9f8a',
                       'e': '#e8c8a0'},
                      {'name': 'Sable',
                       'o': '#2a1406',
                       'b': '#b8783a',
                       'a': '#5a3414',
                       'l': '#fff4e6',
                       'n': '#1a0a02',
                       'p': '#ff9f8a',
                       'e': '#140802'}]},
 'Shiba': {'eyes': 5,
           'move': 'walk',
           'lines': ['much wow', '*side-eye*', 'such desktop', 'i am a good boy (debatable)'],
           'body': ['.o............o.',
                    '.oao........oao.',
                    '.oaboooooooobao.',
                    '.obbbbbbbbbbbbo.',
                    'obbbllbbbbllbbbo',
                    'obbbbbbbbbbbbbbo',
                    'olbbbbbbbbbbbblo',
                    'ollbbllllllbbllo',
                    'ollllllnnllllllo',
                    'ollllllllllllllo',
                    '.ollllllllllllo.',
                    '..oooooooooooo..'],
           'colors': [{'name': 'Red',
                       'o': '#2a1406',
                       'b': '#e0903a',
                       'a': '#fff4e6',
                       'l': '#fff4e6',
                       'n': '#1a0a02',
                       'e': '#140802'},
                      {'name': 'Black & Tan',
                       'o': '#0a0806',
                       'b': '#2a2420',
                       'a': '#e8c8a0',
                       'l': '#f4e2c4',
                       'n': '#0a0806',
                       'e': '#c87a2a'},
                      {'name': 'Cream',
                       'o': '#5a4426',
                       'b': '#f6e2c0',
                       'a': '#ffffff',
                       'l': '#ffffff',
                       'n': '#3a2a1a',
                       'e': '#2a1a0e'}]},
 'Pug': {'eyes': 5,
         'move': 'walk',
         'speed': 0.8,
         'lines': ['*snort*', '*wheeze* hi', "i'm squishy", 'nap time is all the time'],
         'body': ['.oo..........oo.',
                  'osso.oooooo.osso',
                  'ossobbbbbbbbosso',
                  '.oobbbsbbsbbboo.',
                  'obbbbbbssbbbbbbo',
                  'obbbbbbbbbbbbbbo',
                  'obbbbssssssbbbbo',
                  'obpbssssssssbpbo',
                  'obbbsssnnsssbbbo',
                  'obbbbssssssbbbbo',
                  '.obbbbbbbbbbbbo.',
                  '..oooooooooooo..'],
         'colors': [{'name': 'Fawn',
                     'o': '#2a1a0e',
                     'b': '#e8c890',
                     's': '#2a2420',
                     'n': '#0a0806',
                     'p': '#e88a7a',
                     'e': '#140a04'},
                    {'name': 'Black',
                     'o': '#040406',
                     'b': '#2a2a32',
                     's': '#141418',
                     'n': '#040406',
                     'p': '#a85a6a',
                     'e': '#e8e0c8'},
                    {'name': 'Apricot',
                     'o': '#3a1a08',
                     'b': '#f0b070',
                     's': '#3a2a20',
                     'n': '#0a0806',
                     'p': '#ff8f7a',
                     'e': '#140802'}]},
 'Dalmatian': {'eyes': 5,
               'move': 'walk',
               'speed': 1.2,
               'lines': ['spot the difference', '*sniffs*', 'i have 101 friends', 'firehouse buddy'],
               'body': ['...oooooooooo...',
                        '..obbsbbbbbbbo..',
                        'oaaobbbbbbbboaao',
                        'oaaobsbbbbbboaao',
                        'oaaobbbbbbsboaao',
                        'oaaobbbbbbbboaao',
                        '.oaobbsbbbbboao.',
                        '..obbllllllbbo..',
                        '..oblllnnlllbo..',
                        '..obllllllllbo..',
                        '..obbbbsbbbbbo..',
                        '...obbbbbbbbo...'],
               'colors': [{'name': 'Classic',
                           'o': '#0a0a0e',
                           'b': '#ffffff',
                           's': '#14141a',
                           'a': '#14141a',
                           'l': '#f6f6f8',
                           'n': '#14141a',
                           'e': '#2a1a0e'},
                          {'name': 'Liver',
                           'o': '#2a1406',
                           'b': '#ffffff',
                           's': '#7a3a1a',
                           'a': '#7a3a1a',
                           'l': '#fff6ee',
                           'n': '#7a3a1a',
                           'e': '#c87a2a'},
                          {'name': 'Lemon',
                           'o': '#5a3a14',
                           'b': '#fffaf0',
                           's': '#f0b040',
                           'a': '#f0b040',
                           'l': '#ffffff',
                           'n': '#c86a3a',
                           'e': '#5a3a14'}]},
 'Turtle': {'eyes': 5,
            'move': 'walk',
            'speed': 0.45,
            'lines': ['slow and steady', '*retreats into shell*', "i'm 100 years old (jk)", 'no rush'],
            'body': ['...oooooooooo...',
                     '..osasasasasao..',
                     '.osasasasasasao.',
                     'osobbbbbbbbbboso',
                     'osobbbbbbbbbboso',
                     'osobbbbbbbbbboso',
                     'osobbbbbbbbbboso',
                     'osobpbbbbbbpboso',
                     'osobbbbbbbbbboso',
                     'osobbbbbbbbbboso',
                     'ossobbbbbbbbosso',
                     '.oooooooooooooo.'],
            'colors': [{'name': 'Sea',
                        'o': '#0e2a1a',
                        'b': '#7ac88a',
                        's': '#7a5a2a',
                        'a': '#c8a05a',
                        'p': '#ff9f9f',
                        'e': '#0a1a0e',
                        'f': '#5aa86a'},
                       {'name': 'Box',
                        'o': '#1a1a0a',
                        'b': '#a8a85a',
                        's': '#3a2a10',
                        'a': '#e8b83a',
                        'p': '#ff9f7a',
                        'e': '#1a1a0a',
                        'f': '#8a8a4a'},
                       {'name': 'Pastel',
                        'o': '#3a2a5a',
                        'b': '#b8e8d0',
                        's': '#c8a8f0',
                        'a': '#fff0a8',
                        'p': '#ffb0c8',
                        'e': '#2a1a4a',
                        'f': '#98d8b8'}]},
 'Crab': {'eyes': 1,
          'move': 'walk',
          'speed': 1.3,
          'lines': ['*sideways shuffle*', 'snip snip!', 'pinch? no. hug.', 'beach day?'],
          'body': ['...oooo..oooo...',
                   '...ollo..ollo...',
                   '...ollo..ollo...',
                   'oo...o....o...oo',
                   'obo..o....o..obo',
                   'obboobbbbbboobbo',
                   '.obbbbbbbbbbbbo.',
                   'obpbbbbbbbbbbpbo',
                   'obbbbbbbbbbbbbbo',
                   '.obbbbbbbbbbbbo.',
                   '..obbbbbbbbbbo..',
                   '...oooooooooo...'],
          'colors': [{'name': 'Red', 'o': '#3a0a0a', 'b': '#e8402a', 'l': '#ffffff', 'p': '#ff9f7a', 'e': '#0a0a0e'},
                     {'name': 'Blue', 'o': '#0a1a3a', 'b': '#3a7ad8', 'l': '#ffffff', 'p': '#ff9fc0', 'e': '#0a0a0e'},
                     {'name': 'Sandy',
                      'o': '#3a2810',
                      'b': '#e8c088',
                      'l': '#ffffff',
                      'p': '#ff9f7a',
                      'e': '#0a0a0e'}]},
 'Snail': {'eyes': 6,
           'move': 'walk',
           'speed': 0.35,
           'feet': False,
           'lines': ['slooow day', '*leaves a sparkly trail*', 'home is where my shell is', 'eventually...'],
           'body': ['....oooooooo....',
                    '..ooaaaaaaaaoo..',
                    '.oaassssssssaao.',
                    '.oasaaaaaaaasao.',
                    'oooooooooooooooo',
                    'obbbbbbbbbbbbbbo',
                    'obbbbbbbbbbbbbbo',
                    'obbbbbbbbbbbbbbo',
                    'obpbbbbbbbbbbpbo',
                    'obbbbbbbbbbbbbbo',
                    'obbbbbbbbbbbbbbo',
                    '.oooooooooooooo.'],
           'colors': [{'name': 'Garden',
                       'o': '#2a1c10',
                       'a': '#d8a060',
                       's': '#7a4a1a',
                       'b': '#c8c0a8',
                       'p': '#ffb0a0',
                       'e': '#14120e'},
                      {'name': 'Rainbow',
                       'o': '#3a1a4a',
                       'a': '#ffd23a',
                       's': '#ff5f95',
                       'b': '#e8e0f8',
                       'p': '#ff9fc8',
                       'e': '#2a1a3a'},
                      {'name': 'Mint',
                       'o': '#0e2a1a',
                       'a': '#a8f0c8',
                       's': '#3ab878',
                       'b': '#f4f0e0',
                       'p': '#ffb0c0',
                       'e': '#0a1a0e'}]},
 'Starfish': {'eyes': 5,
              'move': 'walk',
              'speed': 0.5,
              'feet': False,
              'lines': ['*star power*', "i'm a star!", 'five arms of friendship', 'beach vibes'],
              'body': ['.......oo.......',
                       '......obbo......',
                       '......obbo......',
                       'ooooobbbbbbooooo',
                       'obbbbbbbbbbbbbbo',
                       '.obbbbbbbbbbbbo.',
                       '..obbbbbbbbbbo..',
                       '..obpbbbbbbpbo..',
                       '..obbbbbbbbbbo..',
                       '.obbbbbbbbbbbbo.',
                       'obbbo......obbbo',
                       'ooo..........ooo'],
              'colors': [{'name': 'Orange', 'o': '#3a1406', 'b': '#ff8a3a', 'p': '#ff5f5f', 'e': '#1a0a02'},
                         {'name': 'Purple', 'o': '#2a1440', 'b': '#a87ad8', 'p': '#ff8fc0', 'e': '#14082a'},
                         {'name': 'Blue', 'o': '#0a1a3a', 'b': '#5aa8ff', 'p': '#ff9fc8', 'e': '#0a0e1a'}]},
 'Pufferfish': {'eyes': 5,
                'move': 'float',
                'feet': False,
                'lines': ['*puffs up*', "don't poke me", "i'm not round, you're round", 'blub'],
                'body': ['..k..k....k..k..',
                         '...oooooooooo...',
                         'k.obbbbbbbbbbo.k',
                         '.obbbbbbbbbbbbo.',
                         'obbbbbbbbbbbbbbo',
                         'obbbbbbbbbbbbbbo',
                         'kobbbbbbbbbbbbok',
                         'obpbbbbbbbbbbpbo',
                         'obbbbbllllbbbbbo',
                         'obbbbllllllbbbbo',
                         'k.obbbbbbbbbbo.k',
                         '...oooooooooo...'],
                'colors': [{'name': 'Yellow',
                            'o': '#5a3a06',
                            'b': '#ffd23a',
                            'l': '#fff6d0',
                            'k': '#c8902a',
                            'p': '#ff9f6a',
                            'e': '#1a1004'},
                           {'name': 'Spotted',
                            'o': '#22262e',
                            'b': '#c8ced8',
                            'l': '#ffffff',
                            'k': '#5a606c',
                            'p': '#ffb0c0',
                            'e': '#0a0b0e'},
                           {'name': 'Blue',
                            'o': '#0a1a3a',
                            'b': '#7ac0ff',
                            'l': '#e8f4ff',
                            'k': '#3a6aa8',
                            'p': '#ff9fc8',
                            'e': '#0a0e1a'}]},
 'Goldfish': {'eyes': 5,
              'move': 'float',
              'feet': False,
              'lines': ['*blub blub*', 'wait what was i saying', '10 second memory, 100% love', 'bloop'],
              'body': ['......oooo......',
                       '.....oaaaao.....',
                       '...oooooooooo...',
                       '..obbbbbbbbbbo..',
                       '.obbbbbbbbbbbbo.',
                       'aobbbbbbbbbbbboa',
                       'aaobbbbbbbbbboaa',
                       'aobpbbbbbbbbpboa',
                       '.obbbbbbbbbbbbo.',
                       '.obbbbbllbbbbbo.',
                       '..obbbbbbbbbbo..',
                       '...oooooooooo...'],
              'colors': [{'name': 'Orange',
                          'o': '#5a1a06',
                          'b': '#ff8a2a',
                          'a': '#ffc06a',
                          'l': '#ffd0a0',
                          'p': '#ff5f5f',
                          'e': '#1a0a02'},
                         {'name': 'Calico',
                          'o': '#2a1a1a',
                          'b': '#fff4e6',
                          'a': '#ff8a3a',
                          'l': '#ffffff',
                          'p': '#ff9f9f',
                          'e': '#1a0a0a'},
                         {'name': 'Black Moor',
                          'o': '#06060a',
                          'b': '#2a2a32',
                          'a': '#4a4a55',
                          'l': '#3a3a44',
                          'p': '#a85a6a',
                          'e': '#e8c01a'}]},
 'Dolphin': {'eyes': 5,
             'move': 'float',
             'feet': False,
             'lines': ['*clicks and whistles*', 'eee-eee!', "let's play!", '*does a flip*'],
             'body': ['.......oo.......',
                      '......obbo......',
                      '....oobbbboo....',
                      '..oobbbbbbbboo..',
                      '.obbbbbbbbbbbbo.',
                      'obbbbbbbbbbbbbbo',
                      'obbbbbbbbbbbbbbo',
                      'obpbbbbbbbbbbpbo',
                      'obbbbbllllbbbbbo',
                      'obbbllllllllbbbo',
                      '.obbbllllllbbbo.',
                      '..oooooooooooo..'],
             'colors': [{'name': 'Gray',
                         'o': '#22262e',
                         'b': '#8a9aac',
                         'l': '#e6ecf2',
                         'p': '#ffb0c0',
                         'e': '#0a0b0e'},
                        {'name': 'Pink',
                         'o': '#6a2a44',
                         'b': '#ffa8c4',
                         'l': '#ffe0ea',
                         'p': '#ff6a9a',
                         'e': '#2a0e1a'},
                        {'name': 'Blue',
                         'o': '#0a1a3a',
                         'b': '#5a9ae8',
                         'l': '#d8ecff',
                         'p': '#ff9fc8',
                         'e': '#0a0e1a'}]},
 'Clownfish': {'eyes': 5,
               'move': 'float',
               'feet': False,
               'lines': ['just keep swimming', "i'm funny, i swear", 'anemone? enemy? friend!', 'blub'],
               'body': ['.......oo.......',
                        '......oaao......',
                        '...oooooooooo...',
                        '..obsbbssbbsbo..',
                        '.obbsbbssbbsbbo.',
                        'aobbsbbssbbsbboa',
                        'aobbsbbssbbsbboa',
                        '.obpsbbssbbspbo.',
                        '.obbsbbssbbsbbo.',
                        '..obsbbssbbsbo..',
                        '...obbbssbbbo...',
                        '....oooooooo....'],
               'colors': [{'name': 'Orange',
                           'o': '#1a0a02',
                           'b': '#ff7a1f',
                           's': '#ffffff',
                           'a': '#1a0a02',
                           'p': '#ff4a4a',
                           'e': '#0a0604'},
                          {'name': 'Black',
                           'o': '#06060a',
                           'b': '#1e1e26',
                           's': '#ffffff',
                           'a': '#ff7a1f',
                           'p': '#a85a6a',
                           'e': '#e8c01a'},
                          {'name': 'Pink',
                           'o': '#5a1a3a',
                           'b': '#ff8fbf',
                           's': '#ffffff',
                           'a': '#a83a6a',
                           'p': '#ff5f95',
                           'e': '#2a0e1a'}]},
 'Snake': {'eyes': 3,
           'move': 'walk',
           'speed': 0.8,
           'feet': False,
           'lines': ['hisss (hi)', '*tongue blep*', 'nope rope reporting', 'sss-so nice to meet you'],
           'body': ['....oooooooo....',
                    '...obbbbbbbbo...',
                    '..obbbbbbbbbbo..',
                    '..obbbbbbbbbbo..',
                    '..obbbbbbbbbbo..',
                    '..obpbbbbbbpbo..',
                    '...obbbbbbbbo...',
                    '..oosbbbbbbsoo..',
                    '.osssssssssssso.',
                    'osbsbsbsbsbsbsbo',
                    'osssssssssssssso',
                    '.oooooooooooooo.'],
           'colors': [{'name': 'Green',
                       'o': '#0c2a14',
                       'b': '#5ac86a',
                       's': '#3a9a4a',
                       'p': '#ff9f9f',
                       'e': '#0a1a0e'},
                      {'name': 'Corn',
                       'o': '#3a1406',
                       'b': '#ff9a5a',
                       's': '#d85a2a',
                       'p': '#ff6a6a',
                       'e': '#1a0a02'},
                      {'name': 'Python',
                       'o': '#2a1c06',
                       'b': '#e8c85a',
                       's': '#7a5a1a',
                       'p': '#ff9f7a',
                       'e': '#1a1004'}]},
 'Gecko': {'eyes': 5,
           'move': 'walk',
           'speed': 1.3,
           'lines': ['*licks own eyeball*', 'i can climb walls', 'sticky toes!', '*chirp*'],
           'body': ['................',
                    '...oooooooooo...',
                    '..obbsbbbbsbbo..',
                    '.obbbbbbbbbbbbo.',
                    'obsbbbbbbbbbbsbo',
                    'obbbbbbbbbbbbbbo',
                    'obbbbbbbbbbbbbbo',
                    'obpbbbbbbbbbbpbo',
                    'obbsbbbbbbbbsbbo',
                    'obbbbbbbbbbbbbbo',
                    '.obsbbbbbbbbsbo.',
                    '..oooooooooooo..'],
           'colors': [{'name': 'Leopard',
                       'o': '#3a2408',
                       'b': '#ffd27a',
                       's': '#5a3a14',
                       'p': '#ff9f7a',
                       'e': '#1a1004'},
                      {'name': 'Crested',
                       'o': '#3a1406',
                       'b': '#e8904a',
                       's': '#a8501e',
                       'p': '#ff8f7a',
                       'e': '#1a0a02'},
                      {'name': 'Green',
                       'o': '#0c2a14',
                       'b': '#7ae88a',
                       's': '#3aa85a',
                       'p': '#ff9f9f',
                       'e': '#c81e1e'}]},
 'Chameleon': {'eyes': 5,
               'move': 'walk',
               'speed': 0.6,
               'shifty': True,
               'lines': ['*changes color*', "you can't see me", "i'm a mood ring", '*slow blink*'],
               'body': ['......oooo......',
                        '.....oaaaao.....',
                        '....oaaaaaao....',
                        '..oobbbbbbbboo..',
                        '.olllbbbbbblllo.',
                        'ollllbbbbbbllllo',
                        'ollllbbbbbbllllo',
                        '.olllbbbbbblllo.',
                        'obbbbbbbbbbbbbbo',
                        'obbbbbbbbbbbbbbo',
                        '.obbbbbbbbbbbbo.',
                        '..oooooooooooo..'],
               'colors': [{'name': 'Green',
                           'o': '#0c2a14',
                           'b': '#5ac86a',
                           'a': '#2a8a4a',
                           'l': '#a8f0b0',
                           'e': '#0a1a0e'},
                          {'name': 'Panther',
                           'o': '#2a0a1a',
                           'b': '#e83a5a',
                           'a': '#3a6ad8',
                           'l': '#ffb0c0',
                           'e': '#1a0610'},
                          {'name': 'Sunny',
                           'o': '#3a2408',
                           'b': '#ffd23a',
                           'a': '#ff8a1f',
                           'l': '#fff4b0',
                           'e': '#1a1004'},
                          {'name': 'Ocean',
                           'o': '#0a1a3a',
                           'b': '#3ab8e8',
                           'a': '#7a5aff',
                           'l': '#b0f0ff',
                           'e': '#0a0e1a'}]},
 'Crocodile': {'eyes': 1,
               'move': 'walk',
               'speed': 0.7,
               'mouth': False,
               'lines': ['*toothy grin*', 'see you later!', "i'm just smiling", 'chomp? no. hug.'],
               'body': ['..oooo....oooo..',
                        '.obbbbo..obbbbo.',
                        '.obbbboooobbbbo.',
                        'obbbbbbbbbbbbbbo',
                        'obbsbbbbbbbbsbbo',
                        'obbbbbbbbbbbbbbo',
                        'obbbbbbbbbbbbbbo',
                        'ollllllllllllllo',
                        'okdkdkdkdkdkdkdo',
                        'ollllllllllllllo',
                        '.obbbbbbbbbbbbo.',
                        '..oooooooooooo..'],
               'colors': [{'name': 'Green',
                           'o': '#0c2010',
                           'b': '#4a8a4a',
                           's': '#2a5a2a',
                           'l': '#c8d8a0',
                           'k': '#ffffff',
                           'd': '#5a1a1a',
                           'e': '#e8c01a'},
                          {'name': 'Albino',
                           'o': '#7a6a6a',
                           'b': '#fff4e6',
                           's': '#f0d8c0',
                           'l': '#ffffff',
                           'k': '#ffffff',
                           'd': '#c86a6a',
                           'e': '#d81e3a'},
                          {'name': 'Swamp',
                           'o': '#0a0e08',
                           'b': '#3a4a2a',
                           's': '#1e2814',
                           'l': '#8a9a6a',
                           'k': '#f2f2e0',
                           'd': '#3a0e0e',
                           'e': '#e8a01a'}]},
 'Butterfly': {'eyes': 5,
               'move': 'flutter',
               'feet': False,
               'lines': ['*flutters*', 'i was a caterpillar once', 'flower hunting', 'so pretty out here'],
               'body': ['...o........o...',
                        '....o......o....',
                        'www.oooooooo.www',
                        'wswobbbbbbbbowsw',
                        'wswobbbbbbbbowsw',
                        'wwwobbbbbbbbowww',
                        '.wwobbbbbbbboww.',
                        'wwwobpbbbbpbowww',
                        'wswobbbbbbbbowsw',
                        'wswobbbbbbbbowsw',
                        'www.obbbbbbo.www',
                        '.....oooooo.....'],
               'colors': [{'name': 'Monarch',
                           'o': '#1a0a02',
                           'b': '#3a2a1a',
                           'w': '#ff8a1f',
                           's': '#1a0a02',
                           'p': '#ff9f7a',
                           'e': '#ffd23a'},
                          {'name': 'Blue Morpho',
                           'o': '#06102a',
                           'b': '#2a2a3a',
                           'w': '#2a8aff',
                           's': '#0a1a4a',
                           'p': '#ff9fc8',
                           'e': '#a8e0ff'},
                          {'name': 'Pink',
                           'o': '#5a1a3a',
                           'b': '#ffe0ef',
                           'w': '#ff8fcf',
                           's': '#ffffff',
                           'p': '#ff5f95',
                           'e': '#3a0e24'}]},
 'Caterpillar': {'eyes': 5,
                 'move': 'walk',
                 'speed': 0.5,
                 'lines': ['*munch munch*', "one day i'll be a butterfly", 'so many leaves', '*wiggles*'],
                 'body': ['...o........o...',
                          '....o......o....',
                          '....oooooooo....',
                          '..oobbbbbbbboo..',
                          '.obbbbbbbbbbbbo.',
                          'obbbbbbbbbbbbbbo',
                          'obbbbbbbbbbbbbbo',
                          'obpbbbbbbbbbbpbo',
                          'obbbbbbbbbbbbbbo',
                          '.obbbbbbbbbbbbo.',
                          'osssssssssssssso',
                          '.oooooooooooooo.'],
                 'colors': [{'name': 'Green',
                             'o': '#0c2a14',
                             'b': '#8ae86a',
                             's': '#5ab84a',
                             'p': '#ff9f9f',
                             'e': '#0a1a0e'},
                            {'name': 'Monarch',
                             'o': '#0a0a0e',
                             'b': '#ffe03a',
                             's': '#1e1e26',
                             'p': '#ff9f7a',
                             'e': '#0a0a0e'},
                            {'name': 'Fuzzy',
                             'o': '#2a1a0e',
                             'b': '#c8905a',
                             's': '#7a4a24',
                             'p': '#ff9f8a',
                             'e': '#140a04'}]}}

RARE = {'Phoenix': {'eyes': 5,
             'move': 'flutter',
             'mouth': False,
             'lines': ['*rises from the ashes*', "i'm on fire (literally)", 'reborn and ready', '*sparkles*'],
             'body': ['......a..a......',
                      '.....aaaaaa.....',
                      '....oaaaaaao....',
                      '..oobbbbbbbboo..',
                      'w.obbbbbbbbbbo.w',
                      'wwobbbbbbbbbboww',
                      'wwobbbbbbbbbboww',
                      'wobpbbbbbbbbpbow',
                      '.obbbbbkkbbbbbo.',
                      '.obbbbbbbbbbbbo.',
                      '..obbbbbbbbbbo..',
                      '...oaaooooaao...'],
             'colors': [{'name': 'Flame',
                         'o': '#3a0606',
                         'b': '#e8302a',
                         'a': '#ffd23a',
                         'w': '#ff8a1f',
                         'k': '#ffe08a',
                         'p': '#ffd23a',
                         'e': '#1a0402'},
                        {'name': 'Blue Flame',
                         'o': '#06143a',
                         'b': '#2a6aff',
                         'a': '#5af0ff',
                         'w': '#7ab8ff',
                         'k': '#e8f8ff',
                         'p': '#5af0ff',
                         'e': '#e8f8ff'},
                        {'name': 'Shadow',
                         'o': '#06060a',
                         'b': '#2a1a3a',
                         'a': '#a85aff',
                         'w': '#5a2a8a',
                         'k': '#d8b0ff',
                         'p': '#a85aff',
                         'e': '#ff4a8a'}]},
 'Griffin': {'eyes': 5,
             'move': 'flutter',
             'mouth': False,
             'lines': ['half eagle, half lion, all friend', '*majestic screech*', 'i guard treasure', 'skrrreee!'],
             'body': ['..oo........oo..',
                      '.obbo......obbo.',
                      '.obbboooooobbbo.',
                      'w.obbbbbbbbbbo.w',
                      'wwobbbbbbbbbboww',
                      'wwobbbbbbbbbboww',
                      'wobbbbbbbbbbbbow',
                      'wobpbbbkkbbbpbow',
                      '.obbbbbkkbbbbbo.',
                      '.obbbbbbkbbbbbo.',
                      '..oaaaaaaaaaao..',
                      '...oaaaaaaaao...'],
             'colors': [{'name': 'Golden',
                         'o': '#2a1606',
                         'b': '#ffffff',
                         'a': '#e0b060',
                         'w': '#8a5a2a',
                         'k': '#ffc83a',
                         'p': '#ffb0a0',
                         'e': '#140a02',
                         'f': '#c8903a'},
                        {'name': 'Royal',
                         'o': '#0a1a3a',
                         'b': '#f4f8ff',
                         'a': '#ffd23a',
                         'w': '#2a5ad8',
                         'k': '#ffc83a',
                         'p': '#ffb0c8',
                         'e': '#0a0e1a',
                         'f': '#d8a01a'},
                        {'name': 'Storm',
                         'o': '#14161c',
                         'b': '#c8ccd4',
                         'a': '#5a606c',
                         'w': '#3a3f4a',
                         'k': '#e8e0c8',
                         'p': '#ffb0c0',
                         'e': '#5af0ff',
                         'f': '#3a3f4a'}]},
 'Kitsune': {'eyes': 5,
             'move': 'walk',
             'lines': ["nine tails? i've got... some.", '*mystical fox noises*', 'i know a little magic', 'kon kon!'],
             'body': ['aa.o........o.aa',
                      'aaoao......oaoaa',
                      'aaoaboooooobaoaa',
                      '.obbbbbbbbbbbbo.',
                      'obbsbbbbbbbbsbbo',
                      'obbbbbbbbbbbbbbo',
                      'obbbbbbbbbbbbbbo',
                      'osllbbbbbbbbllso',
                      'ollllllnnllllllo',
                      '.ollllllllllllo.',
                      '..ollllllllllo..',
                      '...oooooooooo...'],
             'colors': [{'name': 'Spirit',
                         'o': '#5a3a4a',
                         'b': '#ffffff',
                         'a': '#fff0f4',
                         'l': '#ffffff',
                         's': '#e8203a',
                         'n': '#3a1a2a',
                         'e': '#e8203a'},
                        {'name': 'Moon',
                         'o': '#1a1a3a',
                         'b': '#d8dcf0',
                         'a': '#a8b0e8',
                         'l': '#ffffff',
                         's': '#5a6aff',
                         'n': '#1a1a3a',
                         'e': '#5a6aff'},
                        {'name': 'Flame',
                         'o': '#3a1406',
                         'b': '#ff9a3a',
                         'a': '#ffd23a',
                         'l': '#fff4e6',
                         's': '#c81e1e',
                         'n': '#1a0a02',
                         'e': '#c81e1e'}]},
 'Yeti': {'eyes': 5,
          'move': 'walk',
          'speed': 0.9,
          'lines': ['*abominably adorable*', "brrr? no, i'm cozy", 'have you seen my footprints?', 'snowball fight!'],
          'body': ['....oo.oo.oo....',
                   '..oobbobbobboo..',
                   '.obbbbbbbbbbbbo.',
                   'obbbbbbbbbbbbbbo',
                   'obbllllllllllbbo',
                   'obllllllllllllbo',
                   'obllllllllllllbo',
                   'obllpllllllpllbo',
                   'oblllllddlllllbo',
                   'obbllllllllllbbo',
                   'obbbbbbbbbbbbbbo',
                   '.oboobbbbbboobo.'],
          'colors': [{'name': 'Snow',
                      'o': '#5a6a8a',
                      'b': '#ffffff',
                      'l': '#c8dcf0',
                      'p': '#ffb0c8',
                      'd': '#3a4a6a',
                      'e': '#1a2a4a'},
                     {'name': 'Mountain',
                      'o': '#1e1006',
                      'b': '#7a5030',
                      'l': '#d8b890',
                      'p': '#e88a7a',
                      'd': '#2a1406',
                      'e': '#0e0604'},
                     {'name': 'Pink',
                      'o': '#6a2a4a',
                      'b': '#ffd0e4',
                      'l': '#fff4f8',
                      'p': '#ff7ab0',
                      'd': '#a83a6a',
                      'e': '#3a0e24'}]},
 'Moon Bunny': {'eyes': 6,
                'move': 'hop',
                'lines': ['*glows softly*', 'i live on the moon', 'making mochi up there', 'goodnight, earthling'],
                'body': ['...oo......oo...',
                         '..obpo....opbo..',
                         '..obpo....opbo..',
                         '..obbo....obbo..',
                         '.obbbooooooobbo.',
                         '.obbbbbssbbbbbo.',
                         'obbbbbbbbbbbbbbo',
                         'obbbbbbbbbbbbbbo',
                         'obpbbbbbbbbbbpbo',
                         'obbbbbllllbbbbbo',
                         '.obbbllllllbbbo.',
                         '..obbbbbbbbbbo..'],
                'colors': [{'name': 'Moon',
                            'o': '#5a5a7a',
                            'b': '#ffffff',
                            'p': '#ffc0d8',
                            's': '#ffd23a',
                            'l': '#f4f4ff',
                            'e': '#5a5aa8'},
                           {'name': 'Eclipse',
                            'o': '#06060e',
                            'b': '#2a2a40',
                            'p': '#ff6aa8',
                            's': '#d8dcff',
                            'l': '#4a4a6a',
                            'e': '#ffd23a'},
                           {'name': 'Starlight',
                            'o': '#3a2a6a',
                            'b': '#d8c8ff',
                            'p': '#ff9fd8',
                            's': '#ffffff',
                            'l': '#f0e8ff',
                            'e': '#3a2a6a'}]},
 'Pegasus': {'eyes': 5,
             'move': 'flutter',
             'lines': ['*flies majestically*', 'neigh... from above!', 'cloud surfing', 'wings out!'],
             'body': ['..o..........o..',
                      '.oao........oao.',
                      '.oaoommmmmmooao.',
                      'w.obmmmmmmmmbo.w',
                      'wwobbbmmmmbbboww',
                      'wwobbbbbbbbbboww',
                      'wobbbbbbbbbbbbow',
                      'w.obpbbbbbbpbo.w',
                      '..obllllllllbo..',
                      '..oblldlldllbo..',
                      '..obllllllllbo..',
                      '...oooooooooo...'],
             'colors': [{'name': 'Cloud',
                         'o': '#4a5a7a',
                         'b': '#ffffff',
                         'm': '#7ab8ff',
                         'w': '#e8f4ff',
                         'a': '#ffc8e0',
                         'l': '#f4f8ff',
                         'p': '#ffc0d8',
                         'd': '#8aa0c0',
                         'e': '#2a3a5a'},
                        {'name': 'Night',
                         'o': '#06060e',
                         'b': '#2a2a40',
                         'm': '#7a5aff',
                         'w': '#4a4a6a',
                         'a': '#7a5aff',
                         'l': '#3a3a5a',
                         'p': '#ff6aa8',
                         'd': '#06060e',
                         'e': '#c8d8ff'},
                        {'name': 'Sunset',
                         'o': '#5a1a2a',
                         'b': '#ffd8c0',
                         'm': '#ff6a5a',
                         'w': '#ffb08a',
                         'a': '#ff8fb0',
                         'l': '#fff0e6',
                         'p': '#ff7a8a',
                         'd': '#a8506a',
                         'e': '#3a0e1a'}]},
 'Narwhal': {'eyes': 5,
             'move': 'float',
             'feet': False,
             'lines': ['unicorn of the sea!', '*horn sparkle*', "i'm a real animal, i promise", 'blub blub'],
             'body': ['.......h........',
                      '.......hh.......',
                      '....oooohhoo....',
                      '..oobbbbbbbboo..',
                      '.obbbbbbbbbbbbo.',
                      'obbbbbbbbbbbbbbo',
                      'obsbbbbbbbbbbsbo',
                      'obpbbbbbbbbbbpbo',
                      'ollllllllllllllo',
                      'ollllllllllllllo',
                      '.ollllllllllllo.',
                      '..oooooooooooo..'],
             'colors': [{'name': 'Arctic',
                         'o': '#22303e',
                         'b': '#8aa0b8',
                         's': '#4a5a6a',
                         'h': '#fff8e8',
                         'l': '#e8f0f8',
                         'p': '#ffb0c0',
                         'e': '#0a0e14'},
                        {'name': 'Pink',
                         'o': '#6a2a44',
                         'b': '#ffb0cc',
                         's': '#ff7aa8',
                         'h': '#fff4c8',
                         'l': '#ffe8f0',
                         'p': '#ff6a9a',
                         'e': '#2a0e1a'},
                        {'name': 'Gold',
                         'o': '#3a2404',
                         'b': '#ffd27a',
                         's': '#d8a040',
                         'h': '#ffffff',
                         'l': '#fff6e0',
                         'p': '#ffa07a',
                         'e': '#1a1004'}]},
 'Snow Leopard': {'eyes': 5,
                  'move': 'walk',
                  'lines': ['*silent paws*',
                            'the ghost of the mountains',
                            'fluffy tail, fierce heart',
                            'purr... rawr'],
                  'body': ['.o............o.',
                           '.oao........oao.',
                           '.oaboooooooobao.',
                           '.obbbbbbbbbbbbo.',
                           'obbsbbbbbbbbsbbo',
                           'obbbbbbbbbbbbbbo',
                           'osbbbbbbbbbbbbso',
                           'obpbbllllllbbpbo',
                           'osbblllnnlllbbso',
                           'obbbbllllllbbbbo',
                           '.obsbbbbbbbbsbo.',
                           '..obbbbbbbbbbo..'],
                  'colors': [{'name': 'Snow',
                              'o': '#3a3f4a',
                              'b': '#e6e9ee',
                              's': '#5a606c',
                              'a': '#c8ced8',
                              'l': '#ffffff',
                              'n': '#ff9fb0',
                              'p': '#ffb0c0',
                              'e': '#8ad8b8'},
                             {'name': 'Golden',
                              'o': '#3a2408',
                              'b': '#ffd27a',
                              's': '#5a3a14',
                              'a': '#ffe8b0',
                              'l': '#fff6e0',
                              'n': '#c86a5a',
                              'p': '#ffa07a',
                              'e': '#5ac86a'},
                             {'name': 'Black',
                              'o': '#06060a',
                              'b': '#2a2a32',
                              's': '#141418',
                              'a': '#3a3a44',
                              'l': '#4a4a55',
                              'n': '#5a3a44',
                              'p': '#a85a6a',
                              'e': '#ffd23a'}]},
 'Pangolin': {'eyes': 5,
              'move': 'walk',
              'speed': 0.7,
              'lines': ['*curls up*', 'scales, not shells', 'i love ants', 'rare and proud'],
              'body': ['....oooooooo....',
                       '..oosasasasaoo..',
                       '.osasasasasasao.',
                       'osasasasasasasao',
                       'oooobbbbbbbboooo',
                       '...obbbbbbbbo...',
                       '...obbbbbbbbo...',
                       '...opbbbbbbpo...',
                       '....obbnnbbo....',
                       '....obbbbbbo....',
                       '.....obbbbo.....',
                       '......oooo......'],
              'colors': [{'name': 'Bronze',
                          'o': '#2a1606',
                          's': '#a8703a',
                          'a': '#d8a060',
                          'b': '#e8c8a0',
                          'p': '#ff9f8a',
                          'n': '#3a2414',
                          'e': '#140a04',
                          'f': '#2a1606'},
                         {'name': 'Mossy',
                          'o': '#14200e',
                          's': '#5a7a3a',
                          'a': '#8aa85a',
                          'b': '#d8e0b0',
                          'p': '#ff9f9f',
                          'n': '#2a3a1a',
                          'e': '#0a1206',
                          'f': '#14200e'},
                         {'name': 'Gold',
                          'o': '#3a2404',
                          's': '#ffc83a',
                          'a': '#fff08a',
                          'b': '#fff6e0',
                          'p': '#ffa07a',
                          'n': '#7a4a14',
                          'e': '#1a1004',
                          'f': '#3a2404'}]},
 'Okapi': {'eyes': 5,
           'move': 'walk',
           'lines': ["i'm related to giraffes!",
                     '*long tongue*',
                     'forest giraffe reporting',
                     'zebra legs, giraffe heart'],
           'body': ['...o........o...',
                    '..oho......oho..',
                    'oaoh.oooooo.hoao',
                    '.oobbbbbbbbbboo.',
                    'obbbbbbbbbbbbbbo',
                    'obbbbbbbbbbbbbbo',
                    'olbbbbbbbbbbbblo',
                    '.ollbbbbbbbbllo.',
                    '..ollllllllllo..',
                    '..ollldlldlllo..',
                    '..osbsbsbsbsbo..',
                    '...oooooooooo...'],
           'colors': [{'name': 'Forest',
                       'o': '#140a06',
                       'b': '#4a2a1a',
                       'h': '#3a2014',
                       'a': '#c8a090',
                       'l': '#f4e8dc',
                       'd': '#2a1a10',
                       's': '#fff4e6',
                       'e': '#0a0604'},
                      {'name': 'Chocolate',
                       'o': '#0e0604',
                       'b': '#3a1e12',
                       'h': '#2a140a',
                       'a': '#a87a6a',
                       'l': '#e8d8c8',
                       'd': '#1a0e08',
                       's': '#ffffff',
                       'e': '#e8c8a0'},
                      {'name': 'Pastel',
                       'o': '#3a2a4a',
                       'b': '#c8a8d8',
                       'h': '#8a6aa8',
                       'a': '#ffd0e8',
                       'l': '#fff4fa',
                       'd': '#7a5a8a',
                       's': '#ffffff',
                       'e': '#2a1a3a'}]},
 'Quokka': {'eyes': 5,
            'move': 'hop',
            'mouth': False,
            'lines': ['*happiest animal ever*', ':D', 'selfie?', 'everything is great!'],
            'body': ['..oo........oo..',
                     '.oaao......oaao.',
                     '.oaboooooooobao.',
                     '.obbbbbbbbbbbbo.',
                     'obbbbbbbbbbbbbbo',
                     'obbbbbbbbbbbbbbo',
                     'obbbbbbbbbbbbbbo',
                     'obpbbllllllbbpbo',
                     'obbblllnnlllbbbo',
                     'obbbdlllllldbbbo',
                     '.obbbddddddbbbo.',
                     '..obbbbbbbbbbo..'],
            'colors': [{'name': 'Classic',
                        'o': '#2a1c10',
                        'b': '#a8805a',
                        'a': '#e0b8a0',
                        'l': '#e8d4b8',
                        'p': '#ff9f8a',
                        'n': '#1a1006',
                        'd': '#3a1a0e',
                        'e': '#0e0804'},
                       {'name': 'Golden',
                        'o': '#3a2408',
                        'b': '#e0b060',
                        'a': '#ffe0c0',
                        'l': '#fff0d0',
                        'p': '#ffa07a',
                        'n': '#3a2408',
                        'd': '#5a2a0e',
                        'e': '#1a1004'},
                       {'name': 'Rosy',
                        'o': '#5a2a3a',
                        'b': '#e8b0b8',
                        'a': '#ffe0e8',
                        'l': '#fff0f2',
                        'p': '#ff7a9a',
                        'n': '#5a2a3a',
                        'd': '#7a2a3a',
                        'e': '#2a0e1a'}]},
 'Tardigrade': {'eyes': 5,
                'move': 'walk',
                'speed': 0.6,
                'mouth': False,
                'lines': ['i survived space. this is easy.',
                          'water bear reporting',
                          '*microscopic waddle*',
                          'unbreakable!'],
                'body': ['................',
                         '...oooooooooo...',
                         '..obbbbbbbbbbo..',
                         '.obsbbbbbbbbsbo.',
                         'obbbbbbbbbbbbbbo',
                         'obbbbbbbbbbbbbbo',
                         'osbbbbbbbbbbbbso',
                         'obbbbbbbbbbbbbbo',
                         'obbbbbbddbbbbbbo',
                         'obbbbbbddbbbbbbo',
                         'osbbbbbbbbbbbbso',
                         '.oooooooooooooo.'],
                'colors': [{'name': 'Pink',
                            'o': '#6a3a4a',
                            'b': '#ffc8d4',
                            's': '#e89aaa',
                            'd': '#a84a6a',
                            'e': '#2a0e1a'},
                           {'name': 'Moss',
                            'o': '#2a3a1a',
                            'b': '#c8e0a0',
                            's': '#98b870',
                            'd': '#5a7a3a',
                            'e': '#14200a'},
                           {'name': 'Glass',
                            'o': '#3a5a7a',
                            'b': '#e0f4ff',
                            's': '#b0d8f0',
                            'd': '#5a8ab0',
                            'e': '#1a2a3a'}]},
 'Slime': {'eyes': 6,
           'move': 'hop',
           'feet': False,
           'lines': ['*boing*', 'squish squish', "i'm made of jelly", '*wobbles happily*'],
           'body': ['................',
                    '................',
                    '......oooo......',
                    '....oobbbboo....',
                    '...obllbbbbbo...',
                    '..obllbbbbbbbo..',
                    '.obbbbbbbbbbbbo.',
                    '.obbbbbbbbbbbbo.',
                    'obpbbbbbbbbbbpbo',
                    'obbbbbbbbbbbbbbo',
                    'obbbbbbbbbbbbbbo',
                    '.oooooooooooooo.'],
           'colors': [{'name': 'Mint',
                       'o': '#0e4a2a',
                       'b': '#5ae8a0',
                       'l': '#d8fff0',
                       'p': '#ff9fc8',
                       'e': '#0a2a1a'},
                      {'name': 'Berry',
                       'o': '#4a0e3a',
                       'b': '#e85ac0',
                       'l': '#ffd8f4',
                       'p': '#ff9fd8',
                       'e': '#2a0620'},
                      {'name': 'Lava',
                       'o': '#4a0e06',
                       'b': '#ff5a2a',
                       'l': '#ffd23a',
                       'p': '#ffd23a',
                       'e': '#2a0602'},
                      {'name': 'Gold',
                       'o': '#5a3a06',
                       'b': '#ffd23a',
                       'l': '#fffbe0',
                       'p': '#ffa06a',
                       'e': '#3a2404'}]},
 'Shroomy': {'eyes': 5,
             'move': 'walk',
             'lines': ['*spore puff*', 'fun-gi to be around', "i'm a mushroom, hi", "grow where you're planted"],
             'body': ['....oooooooo....',
                      '..oossslssssoo..',
                      '.osslsssssslsso.',
                      'osssssslssssssso',
                      'oooooooooooooooo',
                      '...obbbbbbbbo...',
                      '...obbbbbbbbo...',
                      '...opbbbbbbpo...',
                      '...obbbbbbbbo...',
                      '...obbbbbbbbo...',
                      '...obbbbbbbbo...',
                      '....oooooooo....'],
             'colors': [{'name': 'Toadstool',
                         'o': '#3a0a0a',
                         's': '#e8302a',
                         'l': '#ffffff',
                         'b': '#fff4e0',
                         'p': '#ff9f9f',
                         'e': '#1a0a0a',
                         'f': '#3a0a0a'},
                        {'name': 'Blue Cap',
                         'o': '#0a1a3a',
                         's': '#3a7ad8',
                         'l': '#d8ecff',
                         'b': '#f4f8ff',
                         'p': '#ff9fc8',
                         'e': '#0a0e1a',
                         'f': '#0a1a3a'},
                        {'name': 'Golden',
                         'o': '#3a2404',
                         's': '#ffb83a',
                         'l': '#fff4c8',
                         'b': '#fff8ee',
                         'p': '#ffa07a',
                         'e': '#1a1004',
                         'f': '#3a2404'}]},
 'Cactus Pal': {'eyes': 5,
                'move': 'hop',
                'feet': False,
                'lines': ['free hugs! (careful)', '*blooms*', 'water me maybe?', 'sharp but sweet'],
                'body': ['.......aa.......',
                         '......aaaa......',
                         '....oooooooo....',
                         '..oobsbbbbsboo..',
                         '.obbbbbbbbbbbbo.',
                         'osbbbbbbbbbbbbso',
                         'obbbbbbbbbbbbbbo',
                         'obpbbbbbbbbbbpbo',
                         'osbbbbbbbbbbbbso',
                         'obbbbbbbbbbbbbbo',
                         'oooooooooooooooo',
                         '.okkkkkkkkkkkko.'],
                'colors': [{'name': 'Desert',
                            'o': '#0c2a14',
                            'b': '#5ab86a',
                            's': '#ffffff',
                            'a': '#ff6aa8',
                            'p': '#ff9fc8',
                            'k': '#c8643a',
                            'e': '#0a1a0e'},
                           {'name': 'Blue',
                            'o': '#0e2a3a',
                            'b': '#6ab8c8',
                            's': '#ffffff',
                            'a': '#ffd23a',
                            'p': '#ff9fc8',
                            'k': '#8a5a8a',
                            'e': '#0a1a2a'},
                           {'name': 'Sunset',
                            'o': '#2a1a0a',
                            'b': '#a8c85a',
                            's': '#fff4c8',
                            'a': '#ff5a3a',
                            'p': '#ff9f7a',
                            'k': '#e8a03a',
                            'e': '#141a06'}]},
 'Nimbus': {'eyes': 5,
            'move': 'float',
            'feet': False,
            'lines': ['*drizzles a little*', 'cloudy with a chance of hugs', "i'm on cloud nine", '*rumble*'],
            'body': ['................',
                     '....oooooooo....',
                     '..oobbbbbbbboo..',
                     '.obbbbbbbbbbbbo.',
                     'obbbbbbbbbbbbbbo',
                     'obbbbbbbbbbbbbbo',
                     'obbbbbbbbbbbbbbo',
                     'obpbbbbbbbbbbpbo',
                     'obbbbbbbbbbbbbbo',
                     '.obbbbbbbbbbbbo.',
                     '..oooooooooooo..',
                     '...s..s..s..s...'],
            'colors': [{'name': 'Sunny',
                        'o': '#5a6a8a',
                        'b': '#ffffff',
                        'p': '#ffc0d8',
                        's': '#5ab8ff',
                        'e': '#2a3a5a'},
                       {'name': 'Storm',
                        'o': '#14161c',
                        'b': '#5a606c',
                        'p': '#a85a7a',
                        's': '#ffd23a',
                        'e': '#e8f0ff'},
                       {'name': 'Sunset',
                        'o': '#6a2a4a',
                        'b': '#ffc8d8',
                        'p': '#ff7ab0',
                        's': '#ff9a5a',
                        'e': '#3a0e24'}]},
 'Zorp': {'eyes': 5,
          'move': 'float',
          'feet': False,
          'lines': ['take me to your cookie', 'beep. greetings.', '*probes gently*', 'earth is cute'],
          'body': ['.......aa.......',
                   '.......oo.......',
                   '....oooooooo....',
                   '..oobbbbbbbboo..',
                   '.obbbbbbbbbbbbo.',
                   'obbbbbbbbbbbbbbo',
                   'obbbbbbbbbbbbbbo',
                   'obbbbbbbbbbbbbbo',
                   '.obbbbbbbbbbbbo.',
                   '..obbbbbbbbbbo..',
                   '...obbbbbbbbo...',
                   '....oooooooo....'],
          'colors': [{'name': 'Classic', 'o': '#0c2a0c', 'b': '#8ae86a', 'a': '#ff4a8a', 'e': '#0a0a0e'},
                     {'name': 'Purple', 'o': '#2a0a3a', 'b': '#b87aff', 'a': '#5af0ff', 'e': '#0a0a0e'},
                     {'name': 'Gray', 'o': '#22262e', 'b': '#a8b0bc', 'a': '#ff3b3b', 'e': '#06060a'}]},
 'T-Rex': {'eyes': 4,
            'move': 'walk',
            'mouth': False,
            'lines': ['RAWR!! (hello)', 'tiny arms, big hugs', '*stomp stomp*', "i'm extinct-ly adorable"],
            'body': ['.....h..h..h....',
                     '...oooooooooo...',
                     '..obbbbbbbbbbo..',
                     '.obbssbbbbssbbo.',
                     'obbbbbbbbbbbbbbo',
                     'obbbbbbbbbbbbbbo',
                     'obbbbbdbbdbbbbbo',
                     'obbbbbbbbbbbbbbo',
                     'obkdkdkdkdkdkdbo',
                     'obddddddddddddbo',
                     'aaobbkbbbbkbboaa',
                     '..obbllllllbbo..'],
            'colors': [{'name': 'Green',
                        'o': '#0c2a14',
                        'b': '#4aa85a',
                        's': '#2e7a3a',
                        'h': '#2e7a3a',
                        'k': '#ffffff',
                        'd': '#5a1a1a',
                        'l': '#c8e8a0',
                        'a': '#3a8a4a',
                        'e': '#ffd23a'},
                       {'name': 'Brown',
                        'o': '#2a1606',
                        'b': '#a8703a',
                        's': '#7a4a1e',
                        'h': '#5a3414',
                        'k': '#ffffff',
                        'd': '#4a1a0a',
                        'l': '#e8c890',
                        'a': '#8a5a2a',
                        'e': '#ffd23a'},
                       {'name': 'Purple',
                        'o': '#2a0a3a',
                        'b': '#9a5ad8',
                        's': '#6a2ab0',
                        'h': '#ff7ad8',
                        'k': '#ffffff',
                        'd': '#3a0a2a',
                        'l': '#e0c8f8',
                        'a': '#7a3ab8',
                        'e': '#5af0ff'}]},
 'Mammoth': {'eyes': 5,
             'move': 'walk',
             'speed': 0.7,
             'mouth': False,
             'feet': False,
             'lines': ['*trumpets from the ice age*', 'fluffy elephant!', "brrr... nope, i'm fine", 'i never forget'],
             'body': ['.....oooooo.....',
                      'ooo.obbbbbbo.ooo',
                      'oaaobbbbbbbboaao',
                      'oaaobbbbbbbboaao',
                      'oaaobbbbbbbboaao',
                      'oaaobbbbbbbboaao',
                      'oaaobbbbbbbboaao',
                      '.oaohbbbbbbhoao.',
                      '..oh.obbbbo.ho..',
                      '..h...obbo...h..',
                      '..hh..obbo..hh..',
                      '.......oo.......'],
             'colors': [{'name': 'Woolly',
                         'o': '#1e1006',
                         'b': '#7a4a24',
                         'a': '#5a3218',
                         'h': '#fff4dc',
                         'e': '#0e0604'},
                        {'name': 'Ice',
                         'o': '#3a5a7a',
                         'b': '#e0f0ff',
                         'a': '#b0d0f0',
                         'h': '#ffffff',
                         'e': '#1a2a3a'},
                        {'name': 'Ember',
                         'o': '#2a0a04',
                         'b': '#a83a1a',
                         'a': '#7a2a10',
                         'h': '#ffd23a',
                         'e': '#ffd23a'}]},
 'Golden Blip': {'eyes': 5,
                 'move': 'walk',
                 'lines': ['✦ shiny ✦', "i'm worth a lot of cookies", '*sparkles*', 'ultra rare, ultra cute'],
                 'body': ['..oo........oo..',
                          '.obbo......obbo.',
                          '.obbbooooooobbo.',
                          '.obbbbbbbbbbbbo.',
                          'obbbbbbbbbbbbbbo',
                          'obbbbbbbbbbbbbbo',
                          'obbbbbbbbbbbbbbo',
                          'obpbbbbbbbbbbpbo',
                          'obbbbbllllbbbbbo',
                          'obbbblllllllbbbo',
                          '.obbbllllllbbbo.',
                          '..obbbbbbbbbbo..'],
                 'colors': [{'name': 'Gold',
                             'o': '#5a3a06',
                             'b': '#ffcf3a',
                             'l': '#fff6c8',
                             'p': '#ffa06a',
                             'e': '#3a2404'},
                            {'name': 'Rose Gold',
                             'o': '#5a2a2a',
                             'b': '#f4b0a0',
                             'l': '#fff0ea',
                             'p': '#ff7a8a',
                             'e': '#3a1a1a'},
                            {'name': 'Diamond',
                             'o': '#3a5a7a',
                             'b': '#d8f4ff',
                             'l': '#ffffff',
                             'p': '#ffc0e0',
                             'e': '#2a4a6a'}]}}

# Cryptids 👣: Blips based on legendary creatures. You can't buy or hatch them: you have to SPOT one
# wandering past (or set out a Cryptid Lure) and click it before it gets away.
CRYPTIDS = {
 "Bigfoot": {"eyes": 5, "move": "walk", "speed": 0.8,
  "lines": ["*blurry photo noises*", "you didn't see me", "size 22 feet, thank you", "i just like long walks in the woods", "no photos please"],
  "body": ["....oooooooo....",
           "...obbbbbbbbo...",
           "..obbbbbbbbbbo..",
           ".obbllllllllbbo.",
           ".obllllllllllbo.",
           "obbllllllllllbbo",
           "obbllllllllllbbo",
           "obbpllllllllpbbo",
           "obbbllllllllbbbo",
           "obbbbllllllbbbbo",
           "obbobbbbbbbbobbo",
           ".oo.obbbbbbo.oo."],
  "colors": [{"name": "Forest", "o": "#2a1a0e", "b": "#7a4a2a", "l": "#c8a07a", "p": "#e8806a", "e": "#1a0e06"},
             {"name": "Auburn", "o": "#2a1006", "b": "#b0582a", "l": "#e8b890", "p": "#ff8a6a", "e": "#1a0a04"},
             {"name": "Swamp", "o": "#1a2010", "b": "#4a5a32", "l": "#a8a878", "p": "#d8906a", "e": "#10140a"}]},
 "Death Worm": {"eyes": 5, "move": "walk", "speed": 0.7, "feet": False,
  "lines": ["*wiggles out of the sand*", "from the gobi desert", "i'm a worm. a big one", "wiggle wiggle", "they say i'm scary. i say i'm squishy"],
  "body": ["....oooooooo....",
           "...obbbbbbbbo...",
           "..obbbbbbbbbbo..",
           "..obbbbbbbbbbo..",
           "..oddddddddddo..",
           "..obbbbbbbbbbo..",
           "..obbbbbbbbbbo..",
           "..obpbbbbbbpbo..",
           "..oddddddddddo..",
           "..obbbbbbbbbbo..",
           "ssssobbbbbbossss",
           "ssssssssssssssss"],
  "colors": [{"name": "Gobi Red", "o": "#4a1a1a", "b": "#e86a6a", "d": "#b83a4a", "p": "#ffb0a0", "s": "#e8c87a", "e": "#1a0a0a"},
             {"name": "Sandy", "o": "#4a3a0a", "b": "#e8c84a", "d": "#b8902a", "p": "#ffa070", "s": "#d8b070", "e": "#1a1404"},
             {"name": "Ghost", "o": "#3a3a4a", "b": "#e8e0f0", "d": "#b0a8c8", "p": "#ffb0d0", "s": "#c8b890", "e": "#2a2440"}]},
 "Mothman": {"eyes": 5, "move": "flutter", "mouth": False,
  "lines": ["*stares with big red eyes*", "i come in peace (and moth)", "is that a porch light?!", "bzzz... i mean hello", "they made a statue of me"],
  "body": ["...a........a...",
           "....a......a....",
           "....oooooooo....",
           "w..obbbbbbbbo..w",
           "ww.obbbbbbbbo.ww",
           "wwwobbbbbbbbowww",
           "wwwobbbbbbbbowww",
           "wwwobbbbbbbbowww",
           "wwoobbbbbbbbooww",
           "w..obbbbbbbbo..w",
           "...obbbbbbbbo...",
           "....oooooooo...."],
  "colors": [{"name": "Classic", "o": "#0e0e14", "b": "#3a3a4a", "w": "#5a4a5a", "a": "#2a2a3a", "e": "#ff2a2a"},
             {"name": "Luna", "o": "#14281a", "b": "#7ac88a", "w": "#c8f0a8", "a": "#3a6a4a", "e": "#ff5a8a"},
             {"name": "Dusty", "o": "#2a2014", "b": "#8a7a5a", "w": "#c8b088", "a": "#5a4a2a", "e": "#ff6a2a"}]},
 "Nessie": {"eyes": 2, "move": "float", "mouth": False, "feet": False,
  "lines": ["*splash*", "i'm from a loch far away", "the photo was real, i promise", "glub glub", "come on in, the water's fine"],
  "body": ["....oooooooo....",
           "...obbbbbbbbo...",
           "...obbbbbbbbo...",
           "...obbbbbbbbo...",
           "...obpbbbbpbo...",
           "....obbbbbbo....",
           ".....obbbbo.....",
           ".....obbbbo.....",
           "..ooo.obbo.ooo..",
           ".obbbobbbbobbbo.",
           "wwwwwwwwwwwwwwww",
           "w.ww..ww..ww.ww."],
  "colors": [{"name": "Loch Green", "o": "#0e2a1a", "b": "#4aa86a", "p": "#8ad89a", "w": "#3a6ab8", "e": "#0a1a10"},
             {"name": "Deep Blue", "o": "#0a1a3a", "b": "#3a7ac8", "p": "#8ac0ff", "w": "#1a3a7a", "e": "#06101a"},
             {"name": "Mossy", "o": "#1a2a0e", "b": "#7a9a3a", "p": "#c8d87a", "w": "#2a5a6a", "e": "#10180a"}]},
 "Chupacabra": {"eyes": 5, "move": "walk", "speed": 1.3, "shifty": True,
  "lines": ["*sneaky sneaky*", "i only drink juice boxes now", "rawr (politely)", "have you seen any goats? asking for a friend", "*spikes go up*"],
  "body": ["..a.a.a..a.a.a..",
           ".oaoaoaooaoaoao.",
           "obbbbbbbbbbbbbbo",
           "obbbbbbbbbbbbbbo",
           "obbbbbbbbbbbbbbo",
           "obbbbbbbbbbbbbbo",
           "obbbbbbbbbbbbbbo",
           "obpbbbllllbbbpbo",
           "obbbbllllllbbbbo",
           "..obblwllwlbbo..",
           "...obbbbbbbbo...",
           "....oooooooo...."],
  "colors": [{"name": "Desert", "o": "#1a1a10", "b": "#6a7a5a", "a": "#3a5a3a", "l": "#a8b090", "p": "#c87a6a", "w": "#ffffff", "e": "#e83a2a"},
             {"name": "Midnight", "o": "#0a0a14", "b": "#3a3a5a", "a": "#7a3aa8", "l": "#6a6a8a", "p": "#a85a8a", "w": "#ffffff", "e": "#ffd23a"},
             {"name": "Sandy", "o": "#2a1a0a", "b": "#b8986a", "a": "#7a4a2a", "l": "#e0c8a0", "p": "#e8806a", "w": "#ffffff", "e": "#c82a2a"}]},
 "Jersey Devil": {"eyes": 5, "move": "flutter", "mouth": False,
  "lines": ["*screeches from the pine trees*", "i'm the 13th kid. long story", "boo! ...did it work?", "flap flap flap", "the hockey team is named after me"],
  "body": [".a............a.",
           ".aa..........aa.",
           "..aaooooooooaa..",
           "w..obbbbbbbbo..w",
           "ww.obbbbbbbbo.ww",
           "wwobbbbbbbbbboww",
           "wwobbbbbbbbbboww",
           "wwobpbbbbbbpboww",
           "w.obbbllllbbbo.w",
           "..obllllllllbo..",
           "...obbllllbbo...",
           "....oooooooo...."],
  "colors": [{"name": "Pine Barrens", "o": "#2a0a0e", "b": "#a82a2a", "a": "#f0e0c0", "w": "#5a1a2a", "l": "#d86a5a", "p": "#ff8a7a", "e": "#ffd23a"},
             {"name": "Smoke", "o": "#14101a", "b": "#5a5060", "a": "#d8d0c0", "w": "#2a2430", "l": "#8a8090", "p": "#c87a8a", "e": "#ff5a3a"},
             {"name": "Hockey", "o": "#0a1a10", "b": "#c82a3a", "a": "#ffffff", "w": "#1a5a2a", "l": "#e87a6a", "p": "#ff9a8a", "e": "#1a0a0a"}]},
 "Jackalope": {"eyes": 5, "move": "hop",
  "lines": ["half bunny, half antelope", "*hops majestically*", "yes the antlers are real", "i can sing like a cowboy", "catch me if you can!"],
  "body": ["a.a..........a.a",
           ".aa..........aa.",
           "..a.ob....bo.a..",
           "...obbo..obbo...",
           "...obboooobbo...",
           "..obbbbbbbbbbo..",
           ".obbbbbbbbbbbbo.",
           ".obpbbbbbbbbpbo.",
           ".obbbbbllbbbbbo.",
           "..obbbllllbbbo..",
           "..obbbbbbbbbbo..",
           "...oooooooooo..."],
  "colors": [{"name": "Prairie", "o": "#2a1a0e", "b": "#c8a07a", "a": "#7a4a2a", "l": "#f4e8d8", "p": "#ff9aa8", "e": "#1a0e06"},
             {"name": "Snowshoe", "o": "#3a3a4a", "b": "#f4f4f8", "a": "#8a6a4a", "l": "#ffffff", "p": "#ffb0c8", "e": "#1a1a2a"},
             {"name": "Dusk", "o": "#1a1428", "b": "#8a7aa8", "a": "#4a3a2a", "l": "#d8d0e8", "p": "#ff9ac8", "e": "#100a1a"}]},
 "Flatwoods Monster": {"eyes": 6, "move": "float", "mouth": False, "feet": False,
  "lines": ["*hovers ominously*", "greetings from west virginia", "this hood is my whole look", "i smell like metal. sorry", "*hissssss*"],
  "body": [".......oo.......",
           "......oaao......",
           ".....oaaaao.....",
           "...ooaaaaaaoo...",
           "..oaaaaaaaaaao..",
           ".oaallllllllaao.",
           ".oaallllllllaao.",
           "..oallllllllao..",
           "...oolllllloo...",
           "....obbbbbbo....",
           "...obbbbbbbbo...",
           "..obbbbbbbbbbo.."],
  "colors": [{"name": "Classic", "o": "#1a0a0e", "a": "#c8303a", "l": "#3a2a3a", "b": "#2a6a4a", "e": "#ff8a1a"},
             {"name": "Toxic", "o": "#0a1a0a", "a": "#5ac83a", "l": "#1a2a1a", "b": "#5a3a8a", "e": "#e8ff5a"},
             {"name": "Royal", "o": "#0a0a2a", "a": "#3a4ac8", "l": "#1a1a3a", "b": "#ffd23a", "e": "#5af0ff"}]},
 "Dover Demon": {"eyes": 5, "move": "walk", "speed": 0.9, "feet": False,
  "lines": ["*blinks slowly*", "my head is mostly brain", "i'm not a demon, i'm just shy", "seen in 1977, still got it", "hi. i am small and spooky"],
  "body": ["...oooooooooo...",
           "..obbbbbbbbbbo..",
           ".obbbbbbbbbbbbo.",
           "obbbbbbbbbbbbbbo",
           "obbbbbbbbbbbbbbo",
           "obbbbbbbbbbbbbbo",
           "obbbbbbbbbbbbbbo",
           ".obbbbbbbbbbbbo.",
           "..obbbbbbbbbbo..",
           "...oobbbbbboo...",
           "......obbo......",
           ".....obbbbo....."],
  "colors": [{"name": "Peach", "o": "#4a2a1a", "b": "#e8c8a0", "e": "#ff8a2a"},
             {"name": "Moonlight", "o": "#1a3a2a", "b": "#c8e8c8", "e": "#2a8a5a"},
             {"name": "Ghost", "o": "#3a3a4a", "b": "#d8d8e8", "e": "#5a3aa8"}]},
 "Fresno Nightcrawler": {"eyes": 3, "move": "walk", "speed": 1.2, "feet": False, "mouth": False,
  "lines": ["*walks by on two long legs*", "caught on a security camera", "i'm basically just pants", "strolling... strolling...", "from fresno with love"],
  "body": ["...oooooooooo...",
           "..obbbbbbbbbbo..",
           "..obbbbbbbbbbo..",
           "..obbbbbbbbbbo..",
           "..obbbbbbbbbbo..",
           "..obbbbbbbbbbo..",
           "..obbbbbbbbbbo..",
           "..obbboooobbbo..",
           "..obbbo..obbbo..",
           "..obbbo..obbbo..",
           "..obbbo..obbbo..",
           "..obbbo..obbbo.."],
  "colors": [{"name": "White", "o": "#4a4a6a", "b": "#f4f4ff", "e": "#1a1a2a"},
             {"name": "Glow", "o": "#2a5a3a", "b": "#d8ffe0", "e": "#1a3a2a"},
             {"name": "Shadow", "o": "#0a0a14", "b": "#3a3a5a", "e": "#c8f0ff"}]},
 "Frogman": {"eyes": 5, "move": "hop",
  "lines": ["ribbit (but taller)", "from loveland, ohio", "*waves a sparkly wand*", "i stand on two legs, thank you", "hop to it!"],
  "body": ["..ooo......ooo..",
           ".obbbo....obbbo.",
           ".obbboooooobbbo.",
           "obbbbbbbbbbbbbbo",
           "obbbbbbbbbbbbbbo",
           "obbbbbbbbbbbbbbo",
           "obbbbbbbbbbbbbbo",
           "obpbbbbbbbbbbpbo",
           ".obbbbbbbbbbbbo.",
           ".obbbllllllbbbo.",
           "..obllllllllbo..",
           "...oooooooooo..."],
  "colors": [{"name": "Leathery", "o": "#14200e", "b": "#5a7a3a", "l": "#c8c890", "p": "#8aa85a", "e": "#1a1a0a"},
             {"name": "River", "o": "#0a1a2a", "b": "#3a8a8a", "l": "#b8e0d8", "p": "#7ac8b8", "e": "#06121a"},
             {"name": "Bog", "o": "#1a140a", "b": "#6a5a3a", "l": "#c8b890", "p": "#a88a5a", "e": "#140e06"}]},
 "Batsquatch": {"eyes": 5, "move": "flutter",
  "lines": ["bigfoot... but with wings", "*flaps loudly*", "spotted near a volcano", "i'm purple and proud", "skreee-hoo!"],
  "body": ["..o..........o..",
           "..oo.oooooo.oo..",
           "..obobbbbbbobo..",
           "w.obbbllllbbbo.w",
           "wwobllllllllboww",
           "wwobllllllllboww",
           "wwobllllllllboww",
           "wwobpllllllpboww",
           "w.obbllllllbbo.w",
           "..obbbllllbbbo..",
           "..obbbbbbbbbbo..",
           "...oooooooooo..."],
  "colors": [{"name": "Purple", "o": "#1a0a2a", "b": "#6a3aa8", "l": "#b89ad8", "w": "#3a1a5a", "p": "#ff8ac8", "e": "#ffd23a"},
             {"name": "Volcanic", "o": "#1a0a0a", "b": "#4a3a3a", "l": "#a88a7a", "w": "#a82a1a", "p": "#ff7a5a", "e": "#ff5a1a"},
             {"name": "Twilight", "o": "#0a1428", "b": "#2a4a8a", "l": "#8aa8d8", "w": "#141e3a", "p": "#ff9ac0", "e": "#ffe08a"}]},
}

for _name, _a in {**NEW_ANIMALS, **RARE, **CRYPTIDS}.items():
    VARIANTS[_name] = {"body": _a["body"], "eyes": _a["eyes"], "mouth": _a.get("mouth", True),
                       "feet": FEET_STD if _a.get("feet", True) else None, "dx": 0, "move": _a["move"],
                       "colors": _a["colors"], "lines": _a["lines"], "speed": _a.get("speed", 1.0),
                       "shifty": _a.get("shifty", False)}

NIGHT_SHIFT = list(ROBOTS)        # the animatronic crew gets its own menu group
RARE_KINDS = list(RARE)           # hatched from Mystery Eggs
CRYPTID_KINDS = list(CRYPTIDS)    # spotted in the wild
ANIMAL_KINDS = sorted([k for k in ANIMALS if k not in ROBOTS] + list(NEW_ANIMALS))
KINDS = CRITTERS + ANIMAL_KINDS + NIGHT_SHIFT + RARE_KINDS + CRYPTID_KINDS
EGG_COST = 30                     # hearts per Mystery Egg
LURE_COST = 20                    # hearts per Cryptid Lure

# ----------------------------------------------------------------------------- hats & outfits
# slot: head (sits on the head), face (over the eyes), neck (under the chin). Bought with hearts.
HATS = {'Party Hat': {'slot': 'head',
               'price': 15,
               'overlap': 1,
               'colors': {'p': '#ff5f95', 'y': '#ffd23a', 'w': '#ffffff'},
               'rows': ['....w....', '...pyp...', '...ypy...', '..pypyp..', '..ypypy..']},
 'Bow': {'slot': 'head',
         'price': 15,
         'overlap': 1,
         'x': 3,
         'colors': {'p': '#ff5f95', 'r': '#c8306a'},
         'rows': ['pp.pp', 'ppppp', 'pprpp', 'pp.pp']},
 'Flower': {'slot': 'head',
            'price': 15,
            'overlap': 1,
            'x': -3,
            'colors': {'p': '#ffb0d8', 'y': '#ffd23a', 'g': '#5ac86a'},
            'rows': ['.p.', 'pyp', '.p.', '.g.']},
 'Beanie': {'slot': 'head',
            'price': 20,
            'overlap': 2,
            'colors': {'w': '#ffffff', 'b': '#3a8aff', 'c': '#8ac0ff'},
            'rows': ['....w....', '...www...', '..bbbbb..', '.bbbbbbb.', '.ccccccc.']},
 'Sunglasses': {'slot': 'face',
                'price': 20,
                'colors': {'k': '#14141a', 'w': '#7ad8ff'},
                'rows': ['kkkkkkkkkk', 'kwkk..kwkk', '.kk....kk.']},
 'Scarf': {'slot': 'neck',
           'price': 20,
           'colors': {'r': '#e8303a', 'w': '#ffffff'},
           'rows': ['rrwrrwrrwr', '........rr', '........wr']},
 'Bow Tie': {'slot': 'neck',
             'price': 15,
             'colors': {'r': '#e8303a', 'k': '#8a1a24'},
             'rows': ['rr.rr', 'rrkrr', 'rr.rr']},
 'Top Hat': {'slot': 'head',
             'price': 30,
             'overlap': 1,
             'colors': {'k': '#1a1a22', 'r': '#c8303a', 'g': '#3a3a48'},
             'rows': ['..kkkkk..', '..kgkkk..', '..kgkkk..', '..rrrrr..', 'kkkkkkkkk']},
 'Cowboy Hat': {'slot': 'head',
                'price': 30,
                'overlap': 1,
                'colors': {'b': '#a8703a', 'd': '#6a4220', 'r': '#c8303a'},
                'rows': ['...bbbbb...', '..bbbbbbb..', '..ddrrrdd..', 'bbbbbbbbbbb', '.b.......b.']},
 'Crown': {'slot': 'head',
           'price': 40,
           'overlap': 1,
           'colors': {'y': '#ffcf3a', 'o': '#c8901a', 'r': '#e8303a', 'b': '#3a8aff'},
           'rows': ['.y..y..y.', '.yy.y.yy.', '.yyyyyyy.', '.yryyyby.', '.ooooooo.']},
 'Halo': {'slot': 'head',
          'price': 40,
          'overlap': -2,
          'colors': {'y': '#fff08a', 'o': '#ffd23a'},
          'rows': ['.yyyyyyy.', 'yo.....oy', '.yyyyyyy.']},
 'Wizard Hat': {'slot': 'head',
                'price': 50,
                'overlap': 1,
                'colors': {'p': '#6a4aff', 'y': '#ffd23a', 'd': '#4a2ab8'},
                'rows': ['.....p...',
                         '....pp...',
                         '...pyp...',
                         '...ppp...',
                         '..ppppy..',
                         '..ypppp..',
                         '.ddddddd.',
                         'ppppppppp']},
 'Santa Hat': {'slot': 'head',
               'price': 25,
               'overlap': 1,
               'season': 'winter',
               'colors': {'r': '#e8303a', 'w': '#ffffff'},
               'rows': ['......w..', '.....rr..', '....rrr..', '...rrrr..', '.wwwwwww.']},
 'Witch Hat': {'slot': 'head',
               'price': 25,
               'overlap': 1,
               'season': 'spooky',
               'colors': {'k': '#2a1a3a', 'o': '#ff8a1f', 'p': '#7a3ab8'},
               'rows': ['....k....', '...kk....', '...kkk...', '..kkkkk..', '..ooooo..', 'kkkkkkkkk']},
 'Pumpkin Hat': {'slot': 'head',
                 'price': 25,
                 'overlap': 2,
                 'season': 'spooky',
                 'colors': {'o': '#ff8a1f', 'd': '#c85a0a', 'g': '#3a8a3a'},
                 'rows': ['....g....', '..ododo..', '.ododood.', '.ooooooo.']},
 'Flower Crown': {'slot': 'head',
                  'price': 25,
                  'overlap': 1,
                  'season': 'spring',
                  'colors': {'p': '#ff9fd0', 'y': '#ffd23a', 'w': '#ffffff', 'g': '#5ac86a'},
                  'rows': ['.p.y.w.p.y.', 'gpgygwgpgyg']},
 'Leaf Cap': {'slot': 'head',
              'price': 25,
              'overlap': 1,
              'season': 'autumn',
              'colors': {'o': '#e8702a', 'r': '#c8402a', 'y': '#ffb83a', 's': '#6a3a14'},
              'rows': ['....s....', '..ooroy..', '.oyrooro.']}}


def current_season(day=None):
    """spooky (Halloween time), winter, spring, autumn or summer, from today's date."""
    import datetime
    d = day or datetime.date.today()
    md = (d.month, d.day)
    if (10, 15) <= md <= (11, 2):
        return "spooky"
    if md >= (12, 1) or md <= (2, 29):
        return "winter"
    if (3, 20) <= md <= (5, 31):
        return "spring"
    if (9, 22) <= md <= (11, 30):
        return "autumn"
    return "summer"


def hat_in_shop(name):
    season = HATS[name].get("season")
    return season is None or season == current_season()


def hat_cells(v, hat, shift=0, body=None):
    """Where an item's pixels go on a pet: list of (row, col, color). Rows can be negative (above the art)."""
    body = body or v["body"]
    rows, w = hat["rows"], len(hat["rows"][0])
    left = round(8 - w / 2) + v.get("dx", 0) + hat.get("x", 0)
    if hat["slot"] == "head":
        # the top of the head itself (the first wide row), so hats sit between ears instead of on ear tips
        head_top = next((i for i, r in enumerate(body) if len(r) - r.count(".") >= 8),
                        next(i for i, r in enumerate(body) if r.strip(".")))
        top = head_top + shift + hat.get("overlap", 1) - len(rows)
    elif hat["slot"] == "face":
        top = v["eyes"] + shift + hat.get("y", 0)
    else:
        top = min(v["eyes"] + 5, 11) + shift + hat.get("y", 0)
    return [(top + r, left + c, hat["colors"][ch]) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch != "."]

NIGHT_LINES = ["*eyes glow in the dark*", "the night shift starts now", "is anyone still awake?",
               "*whirr... click*", "we're more active at night", "don't mind me. just wandering."]


def is_night():
    h = time.localtime().tm_hour
    return h >= 22 or h < 6


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
SEASON_LINES = {
    "winter": ["brrr! it's snowy!", "*catches a snowflake*", "hot cocoa weather", "i'm a snow-Blip now"],
    "spring": ["the flowers are back!", "*sniffs a petal*", "spring is in the air", "achoo! (pollen)"],
    "summer": ["it's so sunny!", "beach day?", "*sweats in pixels*", "ice cream please"],
    "autumn": ["*crunch crunch* leaves!", "cozy sweater season", "the leaves are falling!", "pumpkin spice everything"],
    "spooky": ["boo! did i scare you?", "happy spooky season!", "*spooky noises*", "trick or treat?"],
}
BAT = ["x...x", "xx.xx", ".xxx."]
BALL = [".ooo.", "owwro", "owrro", "orrwo", ".ooo."]
BAT_FLAP = [".x.x.", "xxxxx", ".x.x."]


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
        self.last_pet_reward = -99.0
        self.hat = None                            # what it's wearing (from the hat shop)
        self.playing = False                       # busy with a game of catch / tag (the App moves it)
        self.nap_buddy = False                     # walking over to nap next to a sleeping friend
        self.last_play = -99.0
        self.next_shift = time.monotonic() + random.uniform(6, 12)   # chameleons change color now and then

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
        n_groups = 4
        size = -(-len(ANIMAL_KINDS) // n_groups)
        chunks = [ANIMAL_KINDS[i:i + size] for i in range(0, len(ANIMAL_KINDS), size)]
        groups = ([("Critters", CRITTERS)] + [(f"Animals: {c[0]} – {c[-1]}", c) for c in chunks]
                  + [("Night Shift 🌙", NIGHT_SHIFT), ("Rare 🥚", RARE_KINDS), ("Cryptids 👣", CRYPTID_KINDS)]
                  + ([("My Blips ⭐", CUSTOM_KINDS)] if CUSTOM_KINDS else []))
        for group, members in groups:
            sub = tk.Menu(kinds, tearoff=0)
            if members is NIGHT_SHIFT:
                self.night_menu = sub              # filled in on_menu, since locks can change
            elif members is RARE_KINDS:
                self.rare_menu = sub
            elif members is CRYPTID_KINDS:
                self.cryptid_menu = sub
            else:
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
        self.menu.add_command(label="Play Night Shift 🌙…", command=app.open_night_shift)
        self.menu.add_command(label="🎩 Hats & outfits…", command=lambda: HatShop(app, self))
        self.menu.add_command(label=f"🥚 Hatch a Mystery Egg ({EGG_COST} 💖)…", command=lambda: app.open_egg(self.root))
        self.menu.add_command(label=f"🔦 Set out a Cryptid Lure ({LURE_COST} 💖)…", command=lambda: app.set_lure(self.root))
        self.menu.add_command(label="📖 Collection (peek at locked Blips)…", command=lambda: Collection(app))
        self.menu.add_command(label="💖 0 hearts", state="disabled")
        self.hearts_entry = self.menu.index("end")
        self.menu.add_checkbutton(label="Show name tags", variable=app.name_tags)
        self.menu.add_checkbutton(label="Sound effects", variable=app.sound_on,
                                  command=lambda: (app.save.update(sound=app.sound_on.get()), write_save(app.save),
                                                   app.sound.play("boop")))
        self.menu.add_checkbutton(label="Weather effects", variable=app.weather,
                                  command=lambda: app.save.update(weather=app.weather.get()) or write_save(app.save))
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

    def show_reward(self, text):
        self.particles.append({"kind": "plus", "text": text, "x": W / 2 + 34, "y": H - ART_H * SCALE - 4,
                               "vx": 0, "vy": -0.6, "life": 1.6, "born": time.monotonic()})

    def pick_walk_target(self):
        return random.uniform(self.left + 10, self.right - W - 10)

    # ------------------------------------------------------------------ actions
    def pet(self):
        if self.state == "sleep":
            self.wake()
            return
        self.app.sound.play("boop")
        now = time.monotonic()
        if now - self.last_pet_reward > 6:          # petting earns a heart (not by spam-clicking)
            self.last_pet_reward = now
            self.app.add_hearts(1, self)
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
        if self.kind in ROBOTS and is_night():
            return NIGHT_LINES * 2 + VARIANTS[self.kind]["lines"]
        return LINES_IDLE + VARIANTS[self.kind]["lines"] * 2 + SEASON_LINES.get(self.app.season, [])

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
            if abs(self.vx) + abs(self.vy) > 12:
                self.app.sound.play("whoosh")
        else:
            self.pet()
        self.press = None

    def pick_color(self):
        self.palette = self.color_var.get()
        self.say(f"{kind_colors(self.kind)[self.palette]['name'].lower()}!", 1.5)
        self.burst("heart", 2)

    def on_menu(self, e):
        self.night_menu.delete(0, "end")
        for k in NIGHT_SHIFT:
            if self.app.is_unlocked(k):
                self.night_menu.add_radiobutton(label=k, value=k, variable=self.kind_var, command=self.change_kind)
            else:
                self.night_menu.add_command(label=f"🔒 {k}  (survive Night {UNLOCKS[k]})", state="disabled")
        self.night_menu.add_separator()
        self.night_menu.add_command(label="Play Night Shift 🌙…", command=self.app.open_night_shift)
        self.rare_menu.delete(0, "end")
        for k in RARE_KINDS:
            if self.app.is_unlocked(k):
                self.rare_menu.add_radiobutton(label=k, value=k, variable=self.kind_var, command=self.change_kind)
            else:
                self.rare_menu.add_command(label="🔒 ???", state="disabled")
        hatched = sum(1 for k in RARE_KINDS if self.app.is_unlocked(k))
        self.rare_menu.add_separator()
        self.rare_menu.add_command(label=f"🥚 Hatch a Mystery Egg… ({hatched}/{len(RARE_KINDS)} found)",
                                   command=lambda: self.app.open_egg(self.root))
        self.rare_menu.add_command(label="👀 Peek at locked Blips…", command=lambda: Collection(self.app))
        self.cryptid_menu.delete(0, "end")
        for k in CRYPTID_KINDS:
            if self.app.is_unlocked(k):
                self.cryptid_menu.add_radiobutton(label=k, value=k, variable=self.kind_var, command=self.change_kind)
            else:
                self.cryptid_menu.add_command(label="🔒 ???", state="disabled")
        spotted = sum(1 for k in CRYPTID_KINDS if self.app.is_unlocked(k))
        self.cryptid_menu.add_separator()
        self.cryptid_menu.add_command(label=f"🔦 Set out a Cryptid Lure… ({LURE_COST} 💖, {spotted}/{len(CRYPTID_KINDS)} spotted)",
                                      command=lambda: self.app.set_lure(self.root))
        self.cryptid_menu.add_command(label="👀 Peek at locked Blips…", command=lambda: Collection(self.app))
        self.menu.entryconfigure(self.hearts_entry, label=f"💖 {self.app.hearts()} hearts")
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
        if self.playing:
            return
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

        if VARIANTS[self.kind].get("shifty") and now > self.next_shift and self.state not in ("sleep", "held"):
            self.next_shift = now + random.uniform(8, 15)
            self.palette = (self.palette + 1) % len(kind_colors(self.kind))
            if random.random() < 0.4:
                self.say("*changes color*", 1.8)

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
                        self.app.sound.play("thud")
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
                self.app.add_hearts(2, self)                      # a well-rested pet is a happy pet
            return
        if st == "eat":
            if now > self.state_until:
                self.app.add_hearts(5 if self.hunger > 60 else 3, self)   # feeding a hungry pet is worth more
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
                    self.app.sound.play("munch")
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
        if self.kind in ROBOTS and is_night():          # animatronics' eyes glow solid at night
            white = e
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

        # a ball in flight (games of catch are drawn in every pet window the ball passes through)
        for play in self.app.plays:
            if play["type"] == "ball" and "ball" in play:
                bx, by = play["ball"][0] - self.wx, play["ball"][1] - self.wy
                if -10 < bx < W + 10 and -10 < by < H + 10:
                    for yy, row in enumerate(BALL):
                        for xx, ch in enumerate(row):
                            if ch != ".":
                                c.create_rectangle(bx - 8 + xx * 3, by - 8 + yy * 3, bx - 5 + xx * 3, by - 5 + yy * 3,
                                                   fill={"w": "#ffffff", "r": "#e8303a", "o": "#3a2a3a"}[ch], outline="")

        # hat / glasses / scarf
        hat_top = 0
        if self.hat in HATS:
            shift = 1 if (self.state == "sleep" or now < self.squash_until) else 0
            for row, col, color in hat_cells(VARIANTS[self.kind], HATS[self.hat], shift):
                c.create_rectangle(ox + col * SCALE, oy + row * SCALE, ox + (col + 1) * SCALE, oy + (row + 1) * SCALE,
                                   fill=color, outline="")
                hat_top = min(hat_top, row * SCALE)

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
            elif p["kind"] == "snow":
                s_ = 3 if p["phase"] > 2 else 2
                c.create_rectangle(p["x"], p["y"], p["x"] + s_, p["y"] + s_, fill="#f4f8ff", outline="")
            elif p["kind"] in ("leaf", "petal"):
                X = p["x"] + math.sin(age * 3 + p["phase"]) * 4
                w_, h_, col = (4, 3, p["color"]) if p["kind"] == "leaf" else (3, 2, "#ffb0d8")
                c.create_rectangle(X, p["y"], X + w_, p["y"] + h_, fill=col, outline="")
            elif p["kind"] == "firefly":
                if math.sin(age * 5) > -0.3:
                    c.create_rectangle(p["x"], p["y"], p["x"] + 3, p["y"] + 3, fill="#fff08a", outline="")
            elif p["kind"] == "bat":
                shape = BAT if int(age * 8) % 2 else BAT_FLAP
                for y, row in enumerate(shape):
                    for x, ch in enumerate(row):
                        if ch == "x":
                            X, Y = p["x"] + x * 2, p["y"] + y * 2 + math.sin(age * 6) * 3
                            c.create_rectangle(X, Y, X + 2, Y + 2, fill="#6a4a9a", outline="")
            elif p["kind"] == "plus":
                t = c.create_text(p["x"], p["y"], text=p["text"], font=("Segoe UI", 9, "bold"), fill="#ffffff")
                x1, y1, x2, y2 = c.bbox(t)
                c.create_rectangle(x1 - 4, y1 - 1, x2 + 4, y2 + 1, fill="#e8457a", outline="#e8457a")
                c.tag_raise(t)
        self.particles = alive

        # name tag
        tag_h = 0
        if self.app.name_tags.get():
            t = c.create_text(W / 2, oy + hat_top - 6, text=self.name, font=("Segoe UI", 8, "bold"), fill="#ffffff", anchor="s")
            x1, y1, x2, y2 = c.bbox(t)
            c.create_rectangle(x1 - 4, y1 - 1, x2 + 4, y2 + 1, fill="#1d1b26", outline="#1d1b26")
            c.tag_raise(t)
            tag_h = y2 - y1 + 6

        # speech bubble
        if self.bubble and now < self.bubble[1]:
            t = c.create_text(W / 2, 0, text=self.bubble[0], font=("Segoe UI", 10, "bold"),
                              fill="#222222", width=W - 30, justify="center", anchor="s")
            x1, y1, x2, y2 = c.bbox(t)
            top_of_pet = oy + hat_top - (6 if self.state != "sleep" else 2) - tag_h
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
        if self.app.weather.get():
            self.weather(now)
        self.update(now)
        self.draw(now)

    def weather(self, now):
        """A light sprinkle of seasonal weather around this pet."""
        season, dt = self.app.season, 1 / FPS
        rates = {"winter": [("snow", 4.0)], "spring": [("petal", 2.0)], "autumn": [("leaf", 1.8)],
                 "spooky": [("leaf", 1.0), ("bat", 0.12)], "summer": [("firefly", 1.4)] if is_night() else []}
        for kind, rate in rates.get(season, []):
            if random.random() > rate * dt:
                continue
            if kind == "bat":
                d = random.choice([-1, 1])
                self.particles.append({"kind": "bat", "x": -10 if d > 0 else W + 10, "y": random.uniform(15, 80),
                                       "vx": 1.6 * d, "vy": 0, "life": (W + 20) / 1.6 / FPS, "born": now})
            elif kind == "firefly":
                self.particles.append({"kind": "firefly", "x": random.uniform(10, W - 10), "y": random.uniform(40, H - 20),
                                       "vx": random.uniform(-0.3, 0.3), "vy": random.uniform(-0.3, 0.1), "life": 3.0, "born": now})
            else:
                vy = random.uniform(0.5, 1.1)
                self.particles.append({"kind": kind, "x": random.uniform(0, W), "y": -4, "vx": random.uniform(-0.3, 0.3),
                                       "vy": vy, "life": H / vy / FPS, "born": now, "phase": random.uniform(0, 6.3),
                                       "color": random.choice(["#e8702a", "#c8402a", "#ffb83a"])})


# ----------------------------------------------------------------------------- save file
UNLOCKS = {"Robo Bear": 1, "Robo Bunny": 2, "Robo Hen": 3}   # kind -> Night Shift night you must survive


def save_path():
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "Blipville", "save.json")


CUSTOM_KINDS = []                  # your own Blips, loaded from my_blips.json (kept out of the repo)


def app_dir():
    return os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))


def load_custom_blips():
    """Read my_blips.json (next to the app, or in the save folder) and register each Blip as a kind."""
    for path in (os.path.join(app_dir(), "my_blips.json"), os.path.join(os.path.dirname(save_path()), "my_blips.json")):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:  # noqa: BLE001  (no file, or a typo in it: just skip)
            continue
        for b in data.get("blips", []):
            try:
                name, body, colors = str(b["name"])[:20], list(b["body"]), dict(b["colors"])
                eyes = int(b.get("eyes", 5))
                if len(body) != 12 or any(len(r) != 16 for r in body) or "o" not in colors or not 0 <= eyes <= 10:
                    continue
                colors.setdefault("e", "#1a1024")
                VARIANTS[name] = {"body": body, "eyes": eyes, "mouth": bool(b.get("mouth", True)), "feet": FEET_STD,
                                  "dx": 0, "move": b.get("move", "walk"), "lines": list(b.get("lines", [])) or ["hi!"],
                                  "colors": [{"name": "Original", **colors}], "speed": 1.0}
                if name not in CUSTOM_KINDS:
                    CUSTOM_KINDS.append(name)
                    KINDS.append(name)
            except Exception:  # noqa: BLE001
                continue


def load_save():
    try:
        with open(save_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001  (no save yet, or unreadable: start fresh)
        return {}


def write_save(data):
    try:
        os.makedirs(os.path.dirname(save_path()), exist_ok=True)
        tmp = save_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, save_path())
    except Exception:  # noqa: BLE001  (read-only disk etc.: the game still works, it just won't remember)
        pass


def draw_sprite(canvas, kind, color_idx, x, y, scale, face="normal", glow=False, tags=(), hat=None, silhouette=None):
    """Draw a pet's pixel art on any canvas (top-left at x, y). Used by the minigame."""
    v = VARIANTS[kind]
    colors = kind_colors(kind)
    pal = {**colors[color_idx % len(colors)], **v.get("extra", {})}
    body = pal.get("art") or v["body"]
    g = [[None] * ART_W for _ in range(ART_H)]
    for yy, row in enumerate(body):
        for xx, ch in enumerate(row):
            if ch != ".":
                g[yy][xx] = pal.get(ch, pal["o"])
    if v["feet"]:
        for xx, ch in enumerate(v["feet"]["stand"]):
            if ch != "." and 0 <= xx + v.get("dx", 0) < ART_W:
                g[12][xx + v.get("dx", 0)] = pal.get("f", pal["o"])
    er, dx, e = v["eyes"], v.get("dx", 0), pal["e"]
    for ex in (4 + dx, 10 + dx):
        if face == "happy":
            g[er + 1][ex] = g[er][ex + 1] = e
            if ex + 2 < ART_W:
                g[er + 1][ex + 2] = e
        else:
            for a in range(2):
                for b in range(2):
                    g[er + b][ex + a] = e
            if not glow:
                g[er][ex] = "#ffffff"
    if silhouette:
        g = [[silhouette if col else None for col in row] for row in g]
    for yy, row in enumerate(g):
        xx = 0
        while xx < ART_W:
            col = row[xx]
            if col is None:
                xx += 1
                continue
            x2 = xx
            while x2 + 1 < ART_W and row[x2 + 1] == col:
                x2 += 1
            canvas.create_rectangle(x + xx * scale, y + yy * scale, x + (x2 + 1) * scale, y + (yy + 1) * scale,
                                    fill=col, outline="", tags=tags)
            xx = x2 + 1
    if hat in HATS:
        for row, col, color in hat_cells(v, HATS[hat]):
            canvas.create_rectangle(x + col * scale, y + row * scale, x + (col + 1) * scale, y + (row + 1) * scale,
                                    fill=color, outline="", tags=tags)


# ----------------------------------------------------------------------------- cryptid sightings
class Sighting:
    """A shadowy cryptid sneaks across the bottom of the screen. Click it before it gets away to befriend it!"""
    SHADOW, GLOW = "#16121f", "#ffe66a"

    def __init__(self, app, kind):
        self.app, self.kind = app, kind
        self.root = root = tk.Toplevel(app.root)
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
        self.canvas = tk.Canvas(root, width=W, height=H, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        left, top, right, bottom = work_area(root)
        self.left, self.right, self.wy = left, right, bottom - H
        self.dir = random.choice([-1, 1])
        self.wx = left - W + 30 if self.dir == 1 else right - 30
        speed = VARIANTS[kind].get("speed", 1.0)
        self.speed = 70 * max(0.7, speed)           # pixels per second: quick, but catchable
        self.born = self.last = time.monotonic()
        self.caught = False
        self.place()

    def place(self):
        self.root.geometry(f"{W}x{H}+{int(self.wx)}+{int(self.wy)}")

    def art(self, now):
        v = VARIANTS[self.kind]
        g = [[self.SHADOW if ch != "." else None for ch in row] + [None] * (ART_W - len(row)) for row in v["body"]]
        g.append([None] * ART_W)
        if v.get("feet"):
            step = v["feet"]["walk1"] if int(now * 6) % 2 else v["feet"]["walk2"]
            for x, ch in enumerate(step):
                if ch != "." and 0 <= x < ART_W:
                    g[12][x] = self.SHADOW
        if int(now * 2.5) % 10:                    # glowing eyes, with the odd blink
            for ex in (4, 10):
                g[v["eyes"]][ex] = g[v["eyes"]][ex + 1] = self.GLOW
        return g

    def step(self, now):
        dt, self.last = min(0.1, now - self.last), now
        self.wx += self.dir * self.speed * dt
        if (self.dir == 1 and self.wx > self.right) or (self.dir == -1 and self.wx < self.left - W):
            self.leave(escaped=True)
            return
        self.place()
        c = self.canvas
        c.delete("all")
        ox = (W - ART_W * SCALE) // 2
        bob = abs(math.sin(now * 8)) * 3 if VARIANTS[self.kind]["move"] in ("hop", "flutter", "float") else 0
        oy = H - ART_H * SCALE - bob
        g = self.art(now)
        for y, row in enumerate(g):
            for x, col in enumerate(row if self.dir == 1 else row[::-1]):
                if col:
                    c.create_rectangle(ox + x * SCALE, oy + y * SCALE, ox + (x + 1) * SCALE, oy + (y + 1) * SCALE,
                                       fill=col, outline="")
        for y, row in enumerate([".xxx.", "x...x", "...x.", "..x..", ".....", "..x.."]):   # a pixel "?"
            for x, ch in enumerate(row):
                if ch == "x":
                    c.create_rectangle(W // 2 - 8 + x * 3, oy - 26 + y * 3, W // 2 - 5 + x * 3, oy - 23 + y * 3,
                                       fill="#ffffff", outline="")

    def on_click(self, e):
        if self.caught:
            return
        self.caught = True
        app, kind = self.app, self.kind
        app.save.setdefault("cryptids", []).append(kind)
        write_save(app.save)
        app.sound.play("fanfare")
        x = self.wx
        self.leave()
        pet = app.add_pet(kind, x=x, greet=False)
        if not pet and app.pets:
            app.pets[0].say(f"you befriended a {kind}! 📸 (it's in your Collection)", 5)
        if pet:
            pet.wy = pet.ground
            pet.say(f"you spotted me! 📸 i'm a {kind}!", 5)
            pet.set_face("happy", 2)
            pet.burst("heart", 6)

    def leave(self, escaped=False):
        if self in self.app.sightings:
            self.app.sightings.remove(self)
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        if escaped:
            witness = next((p for p in self.app.pets if p.state not in ("sleep", "held")), None)
            if witness:
                witness.say(random.choice(["did you see that?!", "w-what was THAT?", "i think i saw something…",
                                           "*rubs eyes* huh?", "it went that way!"]), 3)


# ----------------------------------------------------------------------------- collection (peek at locked Blips)
class Collection:
    """Every rare and Night Shift Blip. Locked ones are shadows, but you can peek (spoilers!)."""
    COLS, CELL_W, CELL_H = 8, 96, 92

    def __init__(self, app):
        self.app = app
        self.win = tk.Toplevel(app.root)
        self.win.title("Blipville collection")
        self.win.resizable(False, False)
        self.win.configure(bg="#1d1a2e")
        self.win.attributes("-topmost", True)
        self.groups = [("Rare ✨  hatch them from Mystery Eggs", RARE_KINDS), ("Night Shift 🌙  survive the nights", NIGHT_SHIFT),
                       ("Cryptids 👣  spot them wandering by, then click them!", CRYPTID_KINDS)]
        h = 60 + sum(34 + -(-len(k) // self.COLS) * self.CELL_H for _, k in self.groups)
        self.canvas = tk.Canvas(self.win, width=self.COLS * self.CELL_W + 20, height=h, bg="#1d1a2e", highlightthickness=0)
        self.canvas.pack(padx=6, pady=6)
        self.canvas.tag_bind("cell", "<Button-1>", self.on_click)
        self.canvas.tag_bind("peekall", "<Button-1>", lambda e: self.peek_all())
        self.draw()

    def peeked(self):
        return self.app.save.setdefault("peeked", [])

    def how(self, k):
        return f"survive Night {UNLOCKS[k]}" if k in UNLOCKS else "spot it in the wild" if k in CRYPTIDS else "hatch from an egg"

    def draw(self):
        c = self.canvas
        c.delete("all")
        every = [k for _, kinds in self.groups for k in kinds]
        found = sum(1 for k in every if self.app.is_unlocked(k))
        c.create_text(16, 24, anchor="w", text=f"📖 Collection  {found}/{len(every)}", fill="#ffffff", font=("Segoe UI", 14, "bold"))
        if any(not self.app.is_unlocked(k) and k not in self.peeked() for k in every):
            c.create_text(self.COLS * self.CELL_W + 4, 24, anchor="e", text="👀 peek at all (spoilers!)", fill="#ff9fc0",
                          font=("Segoe UI", 10, "bold underline"), tags=("peekall",))
        self.cells, y = {}, 50
        for title, kinds in self.groups:
            c.create_text(16, y + 12, anchor="w", text=title, fill="#ffd23a", font=("Segoe UI", 10, "bold"))
            y += 30
            for i, k in enumerate(kinds):
                x0, y0 = 10 + (i % self.COLS) * self.CELL_W, y + (i // self.COLS) * self.CELL_H
                tag = f"cell{len(self.cells)}"
                self.cells[tag] = k
                open_, peek = self.app.is_unlocked(k), k in self.peeked()
                c.create_rectangle(x0, y0, x0 + self.CELL_W - 8, y0 + self.CELL_H - 8, fill="#2b2547",
                                   outline="#3a3360" if open_ else "#2b2547", width=2, tags=("cell", tag))
                draw_sprite(c, k, default_color(k), x0 + 20, y0 + 6, 3, tags=("cell", tag),
                            silhouette=None if open_ or peek else "#0f0d1a")
                mid = x0 + (self.CELL_W - 8) / 2
                c.create_text(mid, y0 + 54, text=k if open_ or peek else "???", fill="#ffffff" if open_ else "#b8b0d8",
                              font=("Segoe UI", 9, "bold"), width=self.CELL_W - 14, tags=("cell", tag))
                sub = "✓ yours!" if open_ else (f"🔒 {self.how(k)}" if peek else "click to peek 👀")
                c.create_text(mid, y0 + 72, text=sub, fill="#9ad8a8" if open_ else "#ff9fc0", font=("Segoe UI", 7, "bold"),
                              width=self.CELL_W - 14, justify="center", tags=("cell", tag))
            y += -(-len(kinds) // self.COLS) * self.CELL_H + 4

    def spoiler_ok(self, what):
        from tkinter import messagebox
        return messagebox.askyesno("Spoiler warning 👀", f"Peek at {what}?\n\nYou'll see what it looks like before you unlock it.",
                                   parent=self.win)

    def on_click(self, e):
        tag = next((t for t in self.canvas.gettags("current") if t in self.cells), None)
        if not tag:
            return
        k = self.cells[tag]
        if self.app.is_unlocked(k) or k in self.peeked():
            return
        if self.spoiler_ok("this locked Blip"):
            self.peeked().append(k)
            write_save(self.app.save)
            self.app.sound.play("pop")
            self.draw()

    def peek_all(self):
        if self.spoiler_ok("every locked Blip"):
            self.peeked().extend(k for _, kinds in self.groups for k in kinds if k not in self.peeked())
            write_save(self.app.save)
            self.draw()


# ----------------------------------------------------------------------------- sound effects
# Every sound is made with code (no audio files to download). Off by default: right-click → Sound effects.
def _synth(name):
    rate = 22050
    out = []

    def tone(f0, f1, dur, vol=0.35, shape="sine", decay=True):
        n = int(rate * dur)
        phase = 0.0
        for i in range(n):
            t = i / n
            f = f0 + (f1 - f0) * t
            phase += 2 * math.pi * f / rate
            v = math.sin(phase)
            if shape == "square":
                v = 0.6 if v >= 0 else -0.6
            elif shape == "tri":
                v = 2 / math.pi * math.asin(math.sin(phase))
            env = min(1.0, i / (rate * 0.005)) * ((1 - t) ** 2 if decay else 1)
            out.append(v * vol * env)

    def noise(dur, vol=0.3, swell=False):
        n, last = int(rate * dur), 0.0
        for i in range(n):
            t = i / n
            last = last * 0.6 + random.uniform(-1, 1) * 0.4          # a softer, "chunky" noise
            env = math.sin(math.pi * t) if swell else (1 - t) ** 3
            out.append(last * vol * env)

    def rest(dur):
        out.extend([0.0] * int(rate * dur))

    random.seed(name)                                                   # same sound every time
    if name == "boop":
        tone(520, 820, 0.12)
    elif name == "pop":
        tone(900, 1400, 0.06, 0.3)
    elif name == "munch":
        for _ in range(3):
            noise(0.05, 0.45)
            rest(0.06)
    elif name == "whoosh":
        noise(0.28, 0.35, swell=True)
    elif name == "thud":
        tone(150, 60, 0.14, 0.5)
    elif name == "coin":
        tone(988, 988, 0.07, 0.25, "square", decay=False)
        tone(1319, 1319, 0.2, 0.25, "square")
    elif name == "crack":
        noise(0.03, 0.6)
        rest(0.05)
        noise(0.04, 0.6)
    elif name == "fanfare":
        for f in (523, 659, 784):
            tone(f, f, 0.09, 0.3, "tri", decay=False)
        tone(1047, 1047, 0.3, 0.3, "tri")
    elif name == "zap":
        tone(1600, 400, 0.15, 0.25, "square")
    elif name == "boing":
        n = int(rate * 0.4)
        phase = 0.0
        for i in range(n):
            t = i / n
            phase += 2 * math.pi * (260 + 200 * t + 60 * math.sin(t * 40)) / rate
            out.append(math.sin(phase) * 0.4 * (1 - t))
    random.seed()
    import struct
    frames = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32000)) for v in out)
    header = b"RIFF" + struct.pack("<I", 36 + len(frames)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
    return header + b"data" + struct.pack("<I", len(frames)) + frames


SOUNDS = ("boop", "pop", "munch", "whoosh", "thud", "coin", "crack", "fanfare", "zap", "boing")


class Sound:
    def __init__(self, app):
        self.app = app
        self.dir = os.path.join(os.path.dirname(save_path()), "sounds-v1")
        self.last = {}

    def path(self, name):
        p = os.path.join(self.dir, name + ".wav")
        if not os.path.isfile(p):
            try:
                os.makedirs(self.dir, exist_ok=True)
                with open(p, "wb") as f:
                    f.write(_synth(name))
            except OSError:
                return None
        return p

    def play(self, name):
        if not self.app.sound_on.get():
            return
        now = time.monotonic()
        if now - self.last.get(name, 0) < {"thud": 0.8, "munch": 0.5}.get(name, 0.08):   # one thud per bouncy landing
            return
        self.last[name] = now
        p = self.path(name)
        if not p:
            return
        try:
            if sys.platform == "win32":
                import winsound
                winsound.PlaySound(p, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            elif sys.platform == "darwin":
                subprocess.Popen(["afplay", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                import shutil
                player = shutil.which("paplay") or shutil.which("aplay")
                if player:
                    subprocess.Popen([player, p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:  # noqa: BLE001  (no audio device: just stay quiet)
            pass


# ----------------------------------------------------------------------------- hat shop
class HatShop:
    """Try on, buy and wear hats & outfits for one pet."""
    COLS, CELL_W, CELL_H = 4, 132, 150

    def __init__(self, app, pet):
        self.app, self.pet = app, pet
        self.win = tk.Toplevel(app.root)
        self.win.title(f"Hats & outfits — {pet.name}")
        self.win.resizable(False, False)
        self.win.configure(bg="#1d1a2e")
        self.win.attributes("-topmost", True)
        names = [n for n in HATS if hat_in_shop(n)]
        rows = -(-len(names) // self.COLS)
        self.canvas = tk.Canvas(self.win, width=self.COLS * self.CELL_W + 20, height=rows * self.CELL_H + 70,
                                bg="#1d1a2e", highlightthickness=0)
        self.canvas.pack(padx=6, pady=6)
        self.canvas.tag_bind("cell", "<Button-1>", self.on_click)
        self.names = names
        self.draw()

    def owned(self):
        return self.app.save.setdefault("hats_owned", [])

    def draw(self):
        c, pet = self.canvas, self.pet
        c.delete("all")
        c.create_text(16, 22, anchor="w", text=f"🎩 Dress up {pet.name}", fill="#ffffff", font=("Segoe UI", 14, "bold"))
        c.create_text(self.COLS * self.CELL_W + 4, 22, anchor="e", text=f"💖 {self.app.hearts()}", fill="#ff9fc0",
                      font=("Segoe UI", 13, "bold"))
        season = current_season()
        if any(HATS[n].get("season") == season for n in self.names):
            c.create_text(16, 46, anchor="w", text=f"✨ Seasonal items are here for {season}!", fill="#ffd23a",
                          font=("Segoe UI", 9, "bold"))
        for i, name in enumerate(self.names):
            hat = HATS[name]
            x0 = 10 + (i % self.COLS) * self.CELL_W
            y0 = 60 + (i // self.COLS) * self.CELL_H
            wearing, owned = pet.hat == name, name in self.owned()
            tag = f"cell{i}"
            c.create_rectangle(x0, y0, x0 + self.CELL_W - 10, y0 + self.CELL_H - 10, outline="#ffd23a" if wearing else "#3a3360",
                               width=3 if wearing else 2, fill="#2b2547", tags=("cell", tag))
            draw_sprite(c, pet.kind, pet.palette, x0 + 27, y0 + 34, 4, tags=("cell", tag), hat=name)
            c.create_text(x0 + (self.CELL_W - 10) / 2, y0 + 104, text=name, fill="#ffffff", font=("Segoe UI", 10, "bold"),
                          tags=("cell", tag))
            label = "✓ wearing · click to remove" if wearing else ("owned · click to wear" if owned else f"💖 {hat['price']}")
            color = "#ffd23a" if wearing else ("#9ad8a8" if owned else "#ff9fc0")
            c.create_text(x0 + (self.CELL_W - 10) / 2, y0 + 122, text=label, fill=color, font=("Segoe UI", 7, "bold"),
                          width=self.CELL_W - 18, justify="center", tags=("cell", tag))
        self.cells = {f"cell{i}": n for i, n in enumerate(self.names)}

    def on_click(self, e):
        tag = next((t for t in self.canvas.gettags("current") if t in getattr(self, "cells", {})), None)
        if not tag:
            return
        name, pet = self.cells[tag], self.pet
        if pet.hat == name:
            pet.hat = None
            pet.say("back to basics!", 2)
        elif name in self.owned():
            pet.hat = name
            pet.say(random.choice(["how do i look?", "so stylish!", "*strikes a pose*"]), 2.5)
            pet.set_face("happy", 1.5)
        else:
            price = HATS[name]["price"]
            if self.app.hearts() < price:
                from tkinter import messagebox
                messagebox.showinfo("Hats & outfits", f"{name} costs {price} 💖. You have {self.app.hearts()}.\n\n"
                                    "Pet, feed and nap your Blips to earn more hearts!", parent=self.win)
                return
            self.app.save["hearts"] = self.app.hearts() - price
            self.owned().append(name)
            write_save(self.app.save)
            pet.hat = name
            pet.say(f"a new {name.lower()}! thank you!!", 3)
            self.app.sound.play("coin")
            pet.set_face("happy", 2)
            pet.burst("heart", 5)
        self.app.save_town()
        self.draw()


# ----------------------------------------------------------------------------- Mystery Egg
EGG = [
    "....oooo....",
    "...oeeeeo...",
    "..oeesseeo..",
    ".oeeeeeeseo.",
    ".oeseeeeeeo.",
    "oeeeeeeeeseo",
    "oeeesseeeeeo",
    "oeeeeeeeeeeo",
    "oeseeeeeesso",
    ".oeeeeeeeeo.",
    "..oeeeeeeo..",
    "...oooooo...",
]


class EggHatch:
    """A little window where a Mystery Egg wobbles, cracks, and hatches a rare Blip."""
    CW, CH = 360, 300

    def __init__(self, app, kind):
        self.app, self.kind, self.t0 = app, kind, time.monotonic()
        self.win = tk.Toplevel(app.root)
        self.win.title("Mystery Egg — Blipville")
        self.win.resizable(False, False)
        self.win.configure(bg="#1d1a2e")
        self.win.attributes("-topmost", True)
        self.canvas = tk.Canvas(self.win, width=self.CW, height=self.CH, bg="#1d1a2e", highlightthickness=0)
        self.canvas.pack(padx=8, pady=8)
        self.btn = tk.Button(self.win, text="Hatching…", state="disabled", command=self.done, bg="#6a4cff", fg="#ffffff",
                             activebackground="#8a6cff", relief="flat", bd=0, font=("Segoe UI", 11, "bold"), padx=16, pady=6)
        self.btn.pack(pady=(0, 10))
        self.win.protocol("WM_DELETE_WINDOW", self.done)
        self.hatched = False
        self.cracked = self.revealed = False
        self.loop()

    def done(self):
        if not self.hatched:
            self.hatched = True
            self.release()
        self.win.destroy()

    def release(self):
        pet = self.app.add_pet(self.kind)
        if pet:
            pet.say("i'm new here! hi!! ✨", 4)

    def loop(self):
        try:
            t = time.monotonic() - self.t0
            c = self.canvas
            c.delete("all")
            cx, cy = self.CW / 2, 150
            if t < 2.6:
                wob = math.sin(t * (6 + t * 6)) * min(10, 2 + t * 4)
                for y, row in enumerate(EGG):
                    for x, ch in enumerate(row):
                        if ch != ".":
                            col = {"o": "#3a2a4a", "e": "#fff4dc", "s": "#ff9fd0"}[ch]
                            X, Y = cx - 48 + wob + x * 8, cy - 56 + y * 8
                            c.create_rectangle(X, Y, X + 8, Y + 8, fill=col, outline="")
                if t > 1.2 and not self.cracked:
                    self.cracked = True
                    self.app.sound.play("crack")
                if t > 1.2:   # cracks
                    pts = [(cx - 30 + wob, cy - 8), (cx - 14 + wob, cy - 18), (cx + wob, cy - 6), (cx + 16 + wob, cy - 20),
                           (cx + 30 + wob, cy - 8)]
                    n = min(len(pts), 2 + int((t - 1.2) * 3))
                    c.create_line(*[v for p in pts[:n] for v in p], fill="#3a2a4a", width=3)
                c.create_text(cx, 262, text="✨ something is hatching… ✨", fill="#d8d0ff", font=("Segoe UI", 11, "bold"))
            else:
                if not self.revealed:
                    self.revealed = True
                    self.app.sound.play("fanfare")
                if t < 2.9:
                    c.create_rectangle(0, 0, self.CW, self.CH, fill="#ffffff", outline="")
                for i in range(12):   # sparkle burst
                    a = i * math.pi / 6 + t
                    r = 90 + 10 * math.sin(t * 4 + i)
                    x, y = cx + math.cos(a) * r, cy - 10 + math.sin(a) * r * 0.7
                    c.create_rectangle(x - 3, y - 3, x + 3, y + 3, fill=random.choice(["#ffd23a", "#ff9fd0", "#9ad8ff"]),
                                       outline="")
                draw_sprite(c, self.kind, 0, cx - 48, cy - 64, 6, face="happy")
                c.create_text(cx, 236, text=f"You hatched a {self.kind}!", fill="#ffffff", font=("Segoe UI", 15, "bold"))
                found = sum(1 for k in RARE_KINDS if self.app.is_unlocked(k))
                c.create_text(cx, 266, text=f"Rare Blips found: {found}/{len(RARE_KINDS)}", fill="#b8b2d8",
                              font=("Segoe UI", 10))
                if str(self.btn["state"]) == "disabled":
                    self.btn.configure(state="normal", text="Yay! Let it out 🐾")
            self.win.after(40, self.loop)
        except tk.TclError:
            return


# ----------------------------------------------------------------------------- Night Shift minigame
class NightShiftGame:
    """Survive 12 AM → 6 AM while the Night Shift crew wanders toward your office.

    FLASH a doorway to send a robo back to the stage. A robo you're watching on camera can't move,
    but cameras and flashes use battery. Each night you survive unlocks a new robo pet.
    """
    HOUR = 20.0                                   # seconds per in-game hour (6 hours ≈ 2 minutes)
    CW, CH = 720, 380
    ROOMS = ["Stage", "Arcade", "Kitchen", "West Hall", "East Hall"]
    NEXT = {"Stage": ("Arcade", "Kitchen"), "Arcade": ("West Hall",), "Kitchen": ("East Hall",),
            "West Hall": ("door_L",), "East Hall": ("door_R",)}
    NIGHTS = {
        1: dict(robots=["Robo Bear"], interval=6.0, chance=0.55, grace=3.4),
        2: dict(robots=["Robo Bear", "Robo Bunny"], interval=4.4, chance=0.66, grace=2.2),
        3: dict(robots=["Robo Bear", "Robo Bunny", "Robo Hen"], interval=3.9, chance=0.75, grace=1.9),
    }
    MIDNIGHT = 3                                  # color index of the spooky glowing-eye look
    FLASH_COST, DRAIN, CAM_DRAIN = 5.0, 0.2, 0.5  # battery % per flash, per second, extra per second on camera
    BG, PANEL, TEXT, DIM = "#0c0b14", "#1d1a2e", "#e8e4ff", "#7a7598"

    def __init__(self, app, speed=1.0):
        self.app, self.speed = app, speed
        self.win = top = tk.Toplevel(app.root)
        top.title("Night Shift — Blipville")
        top.resizable(False, False)
        top.configure(bg=self.BG)
        top.attributes("-topmost", True)
        top.protocol("WM_DELETE_WINDOW", self.close)
        self.canvas = tk.Canvas(top, width=self.CW, height=self.CH, bg=self.BG, highlightthickness=0)
        self.canvas.pack(padx=10, pady=(10, 6))
        bar = tk.Frame(top, bg=self.BG)
        bar.pack(fill="x", padx=10, pady=(0, 10))
        st = dict(bg=self.PANEL, fg=self.TEXT, activebackground="#3a3360", activeforeground="#ffffff",
                  relief="flat", bd=0, font=("Segoe UI", 10, "bold"), padx=10, pady=6, cursor="hand2")
        self.buttons = [tk.Button(bar, text="◀ FLASH", command=lambda: self.flash("L"), **st)]
        self.buttons[0].pack(side="left")
        mid = tk.Frame(bar, bg=self.BG)
        mid.pack(side="left", expand=True)
        self.buttons.append(tk.Button(mid, text="OFFICE", command=self.office, **st))
        self.buttons[-1].pack(side="left", padx=2)
        for i, room in enumerate(self.ROOMS, 1):
            self.buttons.append(tk.Button(mid, text=f"{i} {room}", command=lambda r=room: self.open_cam(r), **st))
            self.buttons[-1].pack(side="left", padx=2)
        self.buttons.append(tk.Button(bar, text="FLASH ▶", command=lambda: self.flash("R"), **st))
        self.buttons[-1].pack(side="right")
        for keys, fn in ((("<Left>", "a", "A"), lambda e: self.flash("L")), (("<Right>", "d", "D"), lambda e: self.flash("R")),
                         (("<space>", "<Escape>"), lambda e: self.office())):
            for k in keys:
                top.bind(k, fn)
        for i, room in enumerate(self.ROOMS, 1):
            top.bind(str(i), lambda e, r=room: self.open_cam(r))
        self.canvas.tag_bind("click", "<Button-1>", self.on_click)
        self.state, self.clicks = "menu", {}
        self.night = min(self.app.nights_won() + 1, 3)
        self.after_id = None
        self.last = time.monotonic()
        self.loop()

    # ------------------------------------------------------------------ flow
    def close(self):
        if self.after_id:
            self.win.after_cancel(self.after_id)
        self.win.destroy()
        self.app.game = None

    def start(self, night):
        cfg = self.NIGHTS[night]
        self.night, self.cfg = night, cfg
        self.t, self.battery, self.cam = 0.0, 100.0, None
        self.flash_until, self.flash_side, self.flashed = -1.0, None, None
        self.msg, self.msg_until = "Night " + str(night) + " — good luck! 🔦", 3.0
        self.robots = [{"kind": k, "room": "Stage", "next": random.uniform(4, 9) + i * 2.5, "door_since": None}
                       for i, k in enumerate(cfg["robots"])]
        self.state = "play"

    def say(self, text, secs=2.5):
        self.msg, self.msg_until = text, self.t + secs

    def flash(self, side):
        if self.state != "play":
            return
        if self.battery < self.FLASH_COST:
            self.say("not enough battery to flash!")
            return
        self.battery -= self.FLASH_COST
        self.cam = None
        self.flash_until, self.flash_side = self.t + 0.4, side
        door = "door_" + side
        hit = [r for r in self.robots if r["room"] == door]
        self.flashed = hit[0]["kind"] if hit else None
        for r in hit:
            r["room"], r["door_since"] = "Stage", None
            r["next"] = self.t + self.cfg["interval"] * 1.3
        self.say(f"*clank clank* {hit[0]['kind']} ran back to the stage!" if hit else "nothing there… this time.")
        self.app.sound.play("zap")

    def open_cam(self, room):
        if self.state == "play" and self.battery > 0:
            self.cam = room

    def office(self):
        if self.state == "play":
            self.cam = None

    def caught(self, robot):
        self.state, self.caught_by = "caught", robot["kind"]
        self.app.sound.play("boing")

    def won(self):
        self.state = "won"
        self.app.sound.play("fanfare")
        first_time = self.night > self.app.nights_won()
        self.app.record_night(self.night)
        self.app.add_hearts(25 if first_time else 10)
        unlock = next((k for k, n in UNLOCKS.items() if n == self.night), None)
        self.new_unlock = unlock if unlock and not self.app.is_unlocked(unlock) else None
        if self.new_unlock:
            self.app.unlock(self.new_unlock)
            pet = self.app.add_pet(self.new_unlock)
            if pet:
                pet.palette = self.MIDNIGHT
                pet.say("*whirr* ...i'm free! hi!!", 4)

    def on_click(self, e):
        for tag, fn in self.clicks.items():
            if tag in self.canvas.gettags("current"):
                fn()
                return

    # ------------------------------------------------------------------ simulation
    def update(self, dt):
        self.t += dt
        cfg = self.cfg
        self.battery = max(0.0, self.battery - (self.DRAIN + (self.CAM_DRAIN if self.cam else 0)) * dt)
        if self.battery <= 0 and self.cam:
            self.cam = None
            self.say("the battery died… 🔋 lights out!", 4)
        for r in self.robots:
            if r["room"].startswith("door"):
                if self.t - r["door_since"] > cfg["grace"]:
                    self.caught(r)
                    return
                continue
            if self.t < r["next"]:
                continue
            r["next"] = self.t + cfg["interval"] * random.uniform(0.7, 1.3)
            if self.cam == r["room"]:
                continue                          # being watched: frozen
            if random.random() < cfg["chance"]:
                r["room"] = random.choice(self.NEXT[r["room"]])
                if r["room"].startswith("door"):
                    r["door_since"] = self.t
                elif r["room"] in ("West Hall", "East Hall"):
                    self.say("you hear clanking on the " + ("left…" if r["room"] == "West Hall" else "right…"))
        if self.t >= 6 * self.HOUR:
            self.won()

    def loop(self):
        now = time.monotonic()
        dt = min(0.25, now - self.last) * self.speed
        self.last = now
        try:
            if self.state == "play":
                self.update(dt)
            self.draw()
        except tk.TclError:
            return
        self.after_id = self.win.after(50, self.loop)

    # ------------------------------------------------------------------ drawing
    def button(self, x, y, text, fn, primary=False, enabled=True):
        tag = f"btn{len(self.clicks)}"
        c = self.canvas
        tw = len(text) * 8 + 34
        fill = ("#6a4cff" if primary else self.PANEL) if enabled else "#15131f"
        c.create_rectangle(x - tw / 2, y - 18, x + tw / 2, y + 18, fill=fill, outline="#3a3360", width=2,
                           tags=(tag, "click") if enabled else ())
        c.create_text(x, y, text=text, fill=self.TEXT if enabled else self.DIM, font=("Segoe UI", 11, "bold"),
                      tags=(tag, "click") if enabled else ())
        if enabled:
            self.clicks[tag] = fn

    def draw(self):
        c = self.canvas
        c.delete("all")
        self.clicks = {}
        for b in self.buttons:
            b.configure(state="normal" if self.state == "play" else "disabled")
        getattr(self, "draw_" + self.state)()

    def draw_menu(self):
        c, W_, H_ = self.canvas, self.CW, self.CH
        c.create_text(W_ / 2, 46, text="NIGHT SHIFT 🌙", fill=self.TEXT, font=("Segoe UI", 26, "bold"))
        c.create_text(W_ / 2, 108, width=600, justify="center", fill="#b8b2d8", font=("Segoe UI", 10),
                      text="Survive from 12 AM to 6 AM. The Night Shift crew wanders toward your office.\n"
                           "Glowing eyes in a doorway? FLASH that side (◀ ▶ or A / D) to send them back to the stage.\n"
                           "Check rooms with the cameras (1–5): a robo you're watching can't move. "
                           "But cameras and flashes use battery!")
        for i, k in enumerate(NIGHT_SHIFT):
            x = W_ / 2 - 150 + i * 150
            unlocked = self.app.is_unlocked(k)
            draw_sprite(c, k, self.MIDNIGHT if unlocked else 3, x - 32, 165, 4, glow=not unlocked)
            c.create_text(x, 236, text=(k if unlocked else "🔒 " + k), fill=self.TEXT if unlocked else self.DIM,
                          font=("Segoe UI", 9, "bold"))
            c.create_text(x, 252, text=f"Night {UNLOCKS[k]}", fill=self.DIM, font=("Segoe UI", 8))
        best = self.app.nights_won()
        for n in (1, 2, 3):
            self.button(W_ / 2 - 170 + (n - 1) * 170, 300, f"Night {n}" + (" ✓" if n <= best else ""),
                        lambda n=n: self.start(n), primary=(n == self.night), enabled=n <= best + 1)
        c.create_text(W_ / 2, 346, text="Close this window anytime. Your progress is saved.", fill=self.DIM,
                      font=("Segoe UI", 8))

    def draw_play(self):
        c, W_, H_ = self.canvas, self.CW, self.CH
        if self.cam:
            self.draw_camera()
        else:
            self.draw_office()
        # top bar
        c.create_rectangle(0, 0, W_, 34, fill="#08070e", outline="")
        hour = int(self.t // self.HOUR)
        c.create_text(14, 17, anchor="w", text=f"NIGHT {self.night}", fill=self.TEXT, font=("Segoe UI", 11, "bold"))
        c.create_text(W_ / 2, 17, text=("12 AM" if hour == 0 else f"{hour} AM"), fill="#ffd23a",
                      font=("Segoe UI", 13, "bold"))
        b = self.battery
        col = "#5ad87a" if b > 50 else ("#ffd23a" if b > 20 else "#ff4a5a")
        c.create_text(W_ - 160, 17, anchor="e", text="🔋", fill=self.TEXT, font=("Segoe UI", 11))
        c.create_rectangle(W_ - 152, 9, W_ - 52, 25, outline="#3a3360", width=2)
        c.create_rectangle(W_ - 150, 11, W_ - 150 + 96 * b / 100, 23, fill=col, outline="")
        c.create_text(W_ - 8, 17, anchor="e", text=f"{int(b)}%", fill=self.TEXT, font=("Segoe UI", 9, "bold"))
        if self.t < self.msg_until:
            c.create_rectangle(W_ / 2 - 230, H_ - 30, W_ / 2 + 230, H_ - 6, fill="#08070e", outline="#3a3360")
            c.create_text(W_ / 2, H_ - 18, text=self.msg, fill=self.TEXT, font=("Segoe UI", 10, "bold"))

    def draw_office(self):
        c, W_, H_ = self.canvas, self.CW, self.CH
        dark = self.battery <= 0
        c.create_rectangle(0, 34, W_, H_, fill="#0e0c18" if dark else "#1b1830", outline="")
        c.create_rectangle(0, 280, W_, H_, fill="#0a0912" if dark else "#14121f", outline="")
        if not dark:   # cozy desk, lamp and a Blip plush
            c.create_rectangle(250, 236, 470, 252, fill="#3a2e4a", outline="")
            c.create_rectangle(262, 252, 274, 300, fill="#2a2238", outline="")
            c.create_rectangle(446, 252, 458, 300, fill="#2a2238", outline="")
            c.create_polygon(410, 196, 440, 196, 450, 214, 400, 214, fill="#ffd27a", outline="")
            c.create_rectangle(423, 214, 427, 236, fill="#8a7a9a", outline="")
            draw_sprite(c, "Blip", 0, 300, 184, 3, face="happy")
            c.create_rectangle(330, 120, 390, 170, fill="#2a3a5a", outline="#3a3360", width=3)   # window
            c.create_rectangle(340, 130, 343, 133, fill="#ffffff", outline="")
            c.create_rectangle(372, 146, 375, 149, fill="#ffffff", outline="")
        for side, x0 in (("L", 30), ("R", 560)):
            x1 = x0 + 130
            flashing = self.t < self.flash_until and self.flash_side == side
            c.create_rectangle(x0, 70, x1, 300, fill="#f6eec0" if flashing else "#040308", outline="#3a3360", width=4)
            if flashing and self.flashed:
                draw_sprite(c, self.flashed, self.MIDNIGHT, x0 + 1, 140, 8)
            robot = next((r for r in self.robots if r["room"] == "door_" + side), None)
            if robot and not flashing:
                pal = kind_colors(robot["kind"])[self.MIDNIGHT]
                blink = int(self.t * 3 + (1 if side == "R" else 0)) % 7 == 0
                if not blink:
                    for ex in (x0 + 38, x0 + 76):
                        c.create_rectangle(ex, 170, ex + 16, 186, fill=pal["e"], outline="")
            c.create_text((x0 + x1) / 2, 316, text=("◀ A" if side == "L" else "D ▶"), fill=self.DIM,
                          font=("Segoe UI", 9, "bold"))

    def draw_camera(self):
        c, W_, H_ = self.canvas, self.CW, self.CH
        room = self.cam
        c.create_rectangle(0, 34, W_, H_, fill="#101a14", outline="")
        c.create_rectangle(0, 250, W_, H_, fill="#0b130e", outline="")
        if room == "Stage":
            for i in range(12):
                c.create_rectangle(60 + i * 50, 60, 60 + i * 50 + 22, 250, fill="#3a1420", outline="")
            c.create_rectangle(40, 240, W_ - 40, 262, fill="#2a2010", outline="")
        elif room == "Arcade":
            for i in range(5):
                x = 70 + i * 130
                c.create_rectangle(x, 120, x + 60, 250, fill="#1a1a3a", outline="#3a3a7a", width=2)
                c.create_rectangle(x + 10, 135, x + 50, 170, fill="#2a6a5a", outline="")
        elif room == "Kitchen":
            c.create_rectangle(40, 190, W_ - 40, 250, fill="#2a2a2a", outline="")
            for i in range(8):
                c.create_rectangle(60 + i * 80, 120, 110 + i * 80, 160, fill="#3a3a3a", outline="")
        else:
            c.create_polygon(0, 60, W_ / 2 - 60, 140, W_ / 2 - 60, 230, 0, 330, fill="#162016", outline="")
            c.create_polygon(W_, 60, W_ / 2 + 60, 140, W_ / 2 + 60, 230, W_, 330, fill="#162016", outline="")
        here = [r for r in self.robots if r["room"] == room]
        for i, r in enumerate(here):
            x = W_ / 2 - len(here) * 70 + i * 140 + 6
            draw_sprite(c, r["kind"], self.MIDNIGHT, x, 150, 8)
        for _ in range(28):   # camera static
            y = random.randrange(34, H_)
            c.create_line(0, y, W_, y, fill=random.choice(["#1e2a22", "#26332a", "#18221b"]))
        c.create_text(16, 52, anchor="w", text=f"● CAM {self.ROOMS.index(room) + 1} · {room.upper()}",
                      fill="#ff4a5a", font=("Segoe UI", 11, "bold"))
        c.create_text(W_ - 16, 52, anchor="e", text=("watching — it can't move" if here else "empty"),
                      fill="#9ad8a8", font=("Segoe UI", 9, "bold"))

    def draw_caught(self):
        c, W_, H_ = self.canvas, self.CW, self.CH
        c.create_rectangle(0, 0, W_, H_, fill="#14081a", outline="")
        draw_sprite(c, self.caught_by, self.MIDNIGHT, W_ / 2 - 80, 40, 10, glow=True)
        c.create_text(W_ / 2, 200, text="GOTCHA! 🤖", fill="#ff4a6a", font=("Segoe UI", 26, "bold"))
        c.create_text(W_ / 2, 236, text=f"{self.caught_by} got into the office. (it just wanted a hug)",
                      fill="#d8c8f0", font=("Segoe UI", 11))
        self.button(W_ / 2 - 100, 300, f"Try Night {self.night} again", lambda: self.start(self.night), primary=True)
        self.button(W_ / 2 + 120, 300, "Menu", lambda: setattr(self, "state", "menu"))

    def draw_won(self):
        c, W_, H_ = self.canvas, self.CW, self.CH
        c.create_rectangle(0, 0, W_, H_, fill="#2a1a3a", outline="")
        c.create_rectangle(0, H_ - 120, W_, H_, fill="#ffb86a", outline="")
        c.create_text(W_ / 2, 56, text="6 AM 🌅", fill="#ffd23a", font=("Segoe UI", 28, "bold"))
        c.create_text(W_ / 2, 100, text=f"You survived Night {self.night}!", fill=self.TEXT, font=("Segoe UI", 15, "bold"))
        if self.new_unlock:
            draw_sprite(c, self.new_unlock, self.MIDNIGHT, W_ / 2 - 48, 130, 6, face="happy")
            c.create_text(W_ / 2, 222, text=f"UNLOCKED: {self.new_unlock}! It's on your desktop now.",
                          fill="#ffffff", font=("Segoe UI", 12, "bold"))
        else:
            draw_sprite(c, "Blip", 0, W_ / 2 - 48, 130, 6, face="happy")
            c.create_text(W_ / 2, 222, text="Blip is proud of you.", fill="#ffffff", font=("Segoe UI", 12, "bold"))
        if self.night < 3:
            self.button(W_ / 2 - 100, 300, f"Night {self.night + 1} ▶", lambda: self.start(self.night + 1), primary=True)
            self.button(W_ / 2 + 100, 300, "Menu", lambda: setattr(self, "state", "menu"))
        else:
            c.create_text(W_ / 2, 258, text="You beat every night. The whole crew is yours! 🏆", fill="#3a1a14",
                          font=("Segoe UI", 11, "bold"))
            self.button(W_ / 2, 310, "Menu", lambda: setattr(self, "state", "menu"))


class App:
    """Runs every pet on screen."""
    MAX_PETS = 12

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Blipville")
        self.root.withdraw()                       # pets live in their own little windows
        self.name_tags = tk.BooleanVar(master=self.root, value=True)
        self.season = current_season()
        self.save = load_save()
        self.weather = tk.BooleanVar(master=self.root, value=bool(self.save.get("weather", True)))
        self.sound_on = tk.BooleanVar(master=self.root, value=bool(self.save.get("sound", False)))
        self.sound = Sound(self)
        load_custom_blips()
        self.game = None
        self.plays = []                            # games of catch / tag going on right now
        self.sightings = []                        # a cryptid sneaking past right now
        self.next_sighting = time.monotonic() + random.uniform(6, 14) * 60
        self.pets = []
        if not self.restore_town():
            self.add_pet("Blip", "Blip")
        self.daily_treat()
        self.last_topmost = self.last_town_save = time.monotonic()
        self.tick()

    # ----- remembering your town between launches
    def town_snapshot(self):
        return [{"kind": p.kind, "color": p.palette, "name": p.name, "hat": getattr(p, "hat", None),
                 "hunger": round(p.hunger), "energy": round(p.energy)} for p in self.pets]

    def save_town(self):
        town = self.town_snapshot()
        if town != self.save.get("town"):
            self.save["town"] = town
            self.save["town_saved_at"] = time.time()
            write_save(self.save)

    def restore_town(self):
        town = self.save.get("town") or []
        hours_away = max(0.0, (time.time() - float(self.save.get("town_saved_at", time.time()))) / 3600)
        back = 0
        for t in town[:self.MAX_PETS]:
            kind = t.get("kind")
            if kind not in VARIANTS or not self.is_unlocked(kind):
                continue
            pet = self.add_pet(kind, str(t.get("name") or kind)[:16], greet=False)
            if not pet:
                break
            pet.palette = int(t.get("color", 0)) % len(kind_colors(kind))
            pet.color_var.set(pet.palette)
            pet.hat = t.get("hat")
            pet.hunger = min(100.0, float(t.get("hunger", 10)) + hours_away * 8)    # they got peckish while you were away
            pet.energy = float(t.get("energy", 100))
            pet.say(random.choice(["i'm back!", "missed you!", "*stretches* hi again!", "good to see you!"]), 3)
            back += 1
        return back

    def add_pet(self, kind=None, name=None, x=None, greet=True):
        if len(self.pets) >= self.MAX_PETS:
            if self.pets:
                self.pets[0].say("that's enough friends for now!", 2.5)
            return None
        kind = kind or random.choice([k for k in KINDS if self.is_unlocked(k)])
        used = {p.name for p in self.pets}
        name = name or random.choice([n for n in NAMES if n not in used] or NAMES)
        if x is not None:
            x += random.choice([-1, 1]) * random.uniform(80, 160)
        pet = Blip(self, kind, name, x)
        self.pets.append(pet)
        if greet:
            pet.say(f"hi! i'm {name}", 2.5)
        return pet

    # ----- unlocks & Night Shift
    def cryptid_step(self, now):
        for s in list(self.sightings):
            s.step(now)
        if now < self.next_sighting or self.sightings:
            return
        wait = random.uniform(8, 20) * 60          # the next one shows up in 8-20 minutes (sooner at night)
        self.next_sighting = now + (wait / 2 if is_night() else wait)
        left = [k for k in CRYPTID_KINDS if not self.is_unlocked(k)]
        if left and self.pets:
            self.sightings.append(Sighting(self, random.choice(left)))
            self.sound.play("whoosh")

    def set_lure(self, parent):
        from tkinter import messagebox
        if all(self.is_unlocked(k) for k in CRYPTID_KINDS):
            messagebox.showinfo("Cryptid Lure", "You've spotted every cryptid! 🏆", parent=parent)
            return
        if self.hearts() < LURE_COST:
            messagebox.showinfo("Cryptid Lure", f"A Cryptid Lure costs {LURE_COST} 💖 hearts. You have {self.hearts()}.\n\n"
                                "Cryptids also wander by on their own every so often (more at night). Keep an eye out!",
                                parent=parent)
            return
        self.save["hearts"] = self.hearts() - LURE_COST
        write_save(self.save)
        self.next_sighting = min(self.next_sighting, time.monotonic() + random.uniform(15, 45))
        messagebox.showinfo("Cryptid Lure 🔦", "You set out a Cryptid Lure…\n\nWatch the bottom of your screen. "
                            "When a shadow with glowing eyes sneaks by, click it before it gets away!", parent=parent)

    def is_unlocked(self, kind):
        if kind in CRYPTIDS:
            return kind in self.save.get("cryptids", [])
        if kind in RARE:
            return kind in self.save.get("hatched", [])
        return kind not in UNLOCKS or kind in self.save.get("unlocked", [])

    def hearts(self):
        return int(self.save.get("hearts", 0))

    def add_hearts(self, n, pet=None):
        self.save["hearts"] = self.hearts() + n
        write_save(self.save)
        if pet is not None:
            pet.show_reward(f"+{n} 💖")

    def daily_treat(self):
        today = time.strftime("%Y-%m-%d")
        if self.save.get("last_day") != today:
            self.save["last_day"] = today
            self.add_hearts(10, self.pets[0] if self.pets else None)
            if self.pets:
                self.pets[0].say("daily treat! +10 💖", 4)

    def open_egg(self, parent):
        from tkinter import messagebox
        left = [k for k in RARE_KINDS if not self.is_unlocked(k)]
        if not left:
            messagebox.showinfo("Mystery Egg", "You've hatched every rare Blip! 🏆", parent=parent)
            return
        if self.hearts() < EGG_COST:
            messagebox.showinfo("Mystery Egg",
                                f"A Mystery Egg costs {EGG_COST} 💖 hearts. You have {self.hearts()}.\n\n"
                                "Earn hearts by taking care of your Blips:\n"
                                "  💖 pet them (+1)\n  🍪 feed them a cookie (+3, or +5 when they're hungry)\n"
                                "  💤 let them nap until rested (+2)\n  🌙 survive a night in Night Shift (+10, +25 the first time)\n"
                                "  🎁 come back each day for a daily treat (+10)", parent=parent)
            return
        weights = [0.25 if k == "Golden Blip" else 1.0 for k in left]   # the golden one is extra rare
        kind = random.choices(left, weights=weights)[0]
        self.save["hearts"] = self.hearts() - EGG_COST
        self.save.setdefault("hatched", []).append(kind)
        write_save(self.save)
        EggHatch(self, kind)

    def unlock(self, kind):
        got = self.save.setdefault("unlocked", [])
        if kind not in got:
            got.append(kind)
            write_save(self.save)

    def nights_won(self):
        return int(self.save.get("nights_won", 0))

    def record_night(self, night):
        if night > self.nights_won():
            self.save["nights_won"] = night
            write_save(self.save)

    def open_night_shift(self):
        if self.game:
            self.game.win.lift()
            self.game.win.focus_force()
        else:
            self.game = NightShiftGame(self)

    def remove(self, pet):
        if pet in self.pets:
            self.pets.remove(pet)
            pet.root.destroy()
        self.save_town()
        if not self.pets:
            self.root.destroy()

    def quit_all(self):
        self.save_town()
        self.root.destroy()

    # ----- pets playing together
    def head_pos(self, pet):
        return pet.wx + W / 2, pet.wy + H - ART_H * SCALE + 6

    def end_play(self, play, now, happy=True):
        for pet in play["pets"]:
            pet.playing = False
            pet.last_play = now
            if happy and pet.state not in ("held", "fall", "sleep"):
                pet.set_state("idle", random.uniform(1.5, 3))
                pet.set_face("happy", 1.5)
                pet.burst("heart", 2)
        if play in self.plays:
            self.plays.remove(play)

    def play_step(self, now):
        dt = 1 / FPS
        free = [p for p in self.pets if not p.playing and p.state == "idle" and now - p.last_play > 40
                and not getattr(p, "visitor", None)]
        # start a game now and then
        for i, a in enumerate(free):
            for b in free[i + 1:]:
                d = abs(a.wx - b.wx)
                if 60 < d < 190 and random.random() < dt * 0.04:
                    a.playing = b.playing = True
                    self.plays.append({"type": "ball", "pets": [a, b], "from": a, "to": b, "t0": now, "throws": 0,
                                       "n": random.randint(4, 7)})
                    a.say(random.choice(["catch!", f"heads up, {b.name}!", "wanna play?"]), 2)
                    break
                if d < 320 and random.random() < dt * 0.015:
                    a.playing = b.playing = True
                    self.plays.append({"type": "chase", "pets": [a, b], "runner": a, "chaser": b, "until": now + 7,
                                       "swapped": False})
                    a.say(random.choice(["can't catch me!", "tag, you're it!"]), 2)
                    b.say("hey! get back here!", 2)
                    break
        # a sleepy pet sometimes joins a napping friend
        for sleeper in [p for p in self.pets if p.state == "sleep"]:
            for p in self.pets:
                if (p is not sleeper and not p.playing and not p.nap_buddy and p.state == "idle" and p.energy < 60
                        and abs(p.wx - sleeper.wx) < 600 and random.random() < dt * 0.15):
                    p.nap_buddy = True
                    p.target_x = min(max(sleeper.wx + random.choice([-1, 1]) * 70, self.pets[0].left), self.pets[0].right - W)
                    p.set_state("walk", 10)
                    p.say("*yawn* me too...", 2)
        for p in self.pets:
            if p.nap_buddy and p.state == "idle":
                p.nap_buddy = False
                p.set_state("sleep", 20)
                p.say("*snuggles*", 2)
        # run the games
        for play in list(self.plays):
            a, b = play["pets"]
            if any(p not in self.pets or p.state in ("held", "fall", "sleep") or not p.playing for p in (a, b)):
                self.end_play(play, now, happy=False)
                continue
            if play["type"] == "ball":
                src, dst = play["from"], play["to"]
                for p in (a, b):
                    p.state = "idle"
                    other = b if p is a else a
                    p.facing = 1 if other.wx > p.wx else -1
                u = (now - play["t0"]) / 0.9
                (x0, y0), (x1, y1) = self.head_pos(src), self.head_pos(dst)
                play["ball"] = (x0 + (x1 - x0) * min(u, 1), y0 + (y1 - y0) * min(u, 1) - math.sin(math.pi * min(u, 1)) * 60)
                if u >= 1:
                    play["throws"] += 1
                    self.sound.play("pop")
                    if random.random() < 0.5:
                        dst.say(random.choice(["got it!", "nice!", "catch!", "woo!"]), 1.2)
                    dst.set_face("happy", 0.6)
                    play["from"], play["to"], play["t0"] = dst, src, now
                    if play["throws"] >= play["n"]:
                        dst.say(random.choice(["that was fun!", "good game!", "again later!"]), 2.5)
                        self.end_play(play, now)
            else:   # tag
                runner, chaser = play["runner"], play["chaser"]
                left, right = runner.left, runner.right - W
                away = 1 if runner.wx >= chaser.wx else -1
                if (away > 0 and runner.wx >= right - 2) or (away < 0 and runner.wx <= left + 2):
                    away = -away                    # cornered: dodge past
                runner.wx = min(max(runner.wx + 2.2 * away * VARIANTS[runner.kind].get("speed", 1.0) ** 0.5, left), right)
                toward = 1 if runner.wx > chaser.wx else -1
                chaser.wx += 4.4 * toward * VARIANTS[chaser.kind].get("speed", 1.0) ** 0.5
                runner.facing, chaser.facing = away, toward
                runner.state = chaser.state = "walk"
                runner.place()
                chaser.place()
                if abs(runner.wx - chaser.wx) < 26:
                    chaser.say("tag! you're it!", 1.8)
                    if not play["swapped"]:
                        play["runner"], play["chaser"], play["swapped"] = chaser, runner, True
                        play["until"] = now + 6
                        runner.wx += 30 * (1 if runner.wx > chaser.wx else -1)
                    else:
                        self.end_play(play, now)
                elif now > play["until"]:
                    runner.say("*pant pant* ok you win", 2)
                    self.end_play(play, now)

    def socialize(self, now):
        """Pets that bump into each other say hi (at most once a minute per pair)."""
        calm = ("idle", "walk")
        idle_pets = [p for p in self.pets if not p.playing]
        for i, a in enumerate(idle_pets):
            for b in idle_pets[i + 1:]:
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
            self.play_step(now)
            self.cryptid_step(now)
            if now - self.last_town_save > 15:     # remember the town every so often
                self.save_town()
                self.last_town_save = now
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
