// Prowl Week draft: 4 event skins for existing cats + 3 new Blips (Lioness, Cougar, Panther).
const SKINS = {
  Lion:    { name: "Sunmane",    o: "#3a1004", b: "#ffb02a", m: "#ff5a1a", l: "#fff6d8", p: "#ff9f7a", n: "#5a1a08", e: "#2a0a02", f: "#3a1004" },
  Tiger:   { name: "Moonstripe", o: "#14122a", b: "#c8c0f0", s: "#2a2260", l: "#ffffff", a: "#ffffff", n: "#ff8ad8", e: "#14122a" },
  Cheetah: { name: "Dawnspot",   o: "#3a1428", b: "#ffc890", s: "#a83a5a", a: "#e89060", p: "#ff9a6a", l: "#fff4ec", n: "#3a1428", e: "#2a0e1c" },
  Jaguar:  { name: "Emberrose",  o: "#1a0a10", b: "#6a2036", s: "#ff6a3a", a: "#ff9a5a", p: "#ff9a6a", l: "#ffb8a0", n: "#1a0a10", e: "#ffd23a" },
};
const F4 = { stand: "...oo......oo...", walk1: "..oo........oo..", walk2: "....oo....oo....", air: "....o......o...." };
const NEW = {
  Lioness: { eyes: 5, mouth: true, feet: F4, body: [
      "................",
      ".oo..........oo.",
      "oaao........oaao",
      "obbbooooooooobbo",
      "obbbbbbbbbbbbbBo",
      "obbbbbbbbbbbbbBo",
      "obbbbbbbbbbbbbBo",
      "obmbllllllllbmBo",
      "obmbblllnnllbmBo",
      ".oBmbllllllbmBo.",
      "..oBbbllllbbBo..",
      "...oooooooooo..." ],
    colors: [
      { name: "Savanna", o: "#3a2008", b: "#f0c878", a: "#8a5a20", m: "#d8a458", l: "#fff4dc", n: "#5a2a14", e: "#2a1404", f: "#3a2008" },
      { name: "Dusk Rose", o: "#2a1038", b: "#e8b0d8", a: "#8a3a7a", m: "#c880b8", l: "#fff0fa", n: "#5a1a48", e: "#2a0a28", f: "#2a1038" },
      { name: "Ivory", o: "#2a2a3a", b: "#f4f0e8", a: "#a8a098", m: "#d8d0c4", l: "#ffffff", n: "#a85a5a", e: "#1a1a24", f: "#2a2a3a" } ] },
  Cougar: { eyes: 5, mouth: true, feet: F4, body: [
      "..o..........o..",
      ".oto........oto.",
      ".ottooooooootto.",
      "obbbbbbbbbbbbbbo",
      "obbbbbbbbbbbbbbo",
      "obbbbbbbbbbbbbbo",
      "obbbbbbbbbbbbbbo",
      "obbbtbllllbtbbbo",
      "obbbbllnnllbbbbo",
      ".obbbllllllbbbo.",
      "..obbbllllbbbo..",
      "...oooooooooo..." ],
    colors: [
      { name: "Tawny", o: "#2a1a08", b: "#c89a62", t: "#3a2410", l: "#f4ead8", n: "#3a1c10", e: "#2a1a04", f: "#2a1a08" },
      { name: "Ghost Mountain", o: "#1a2230", b: "#a8b4c4", t: "#2a3448", l: "#f4f8ff", n: "#3a2a30", e: "#10161f", f: "#1a2230" },
      { name: "Red Rock", o: "#3a1408", b: "#d8683a", t: "#4a1c0a", l: "#ffe8d0", n: "#3a1408", e: "#2a0e04", f: "#3a1408" } ] },
  Panther: { eyes: 5, mouth: false, feet: { stand: ".....oo..oo.....", walk1: "....oo....oo....", walk2: "......oo.oo.....", air: ".....o....o....." }, body: [
      "..o..........o..",
      ".obo........obo.",
      ".obio......oibo.",
      ".obbbooooooobbbo",
      ".obbbbbbbbbbbbo.",
      ".obbbbbbbbbbbbo.",
      "..obbbbbbbbbbo..",
      "..obrbbbbbbrbo..",
      "...obbbnnbbbo...",
      "....obbbbbbo....",
      ".....oBbbBo.....",
      "......oooo......" ],
    colors: [
      { name: "Midnight", o: "#06060e", b: "#1e1e2e", r: "#34345a", i: "#ff8aa8", n: "#ff8aa8", e: "#7aff5a", f: "#06060e" },
      { name: "Moonlit", o: "#080a1c", b: "#232a4a", r: "#46549a", i: "#8ad8ff", n: "#ffb0d8", e: "#6ad8ff", f: "#080a1c" },
      { name: "Ember Black", o: "#100604", b: "#2a1810", r: "#5a3420", i: "#ff8a3a", n: "#ff6a3a", e: "#ffd23a", f: "#100604" } ] },
};
