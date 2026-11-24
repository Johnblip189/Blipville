// Prowl Week, second batch: 4 more new Blips.
const SKINS = {};
const F4 = { stand: "...oo......oo...", walk1: "..oo........oo..", walk2: "....oo....oo....", air: "....o......o..." };
const NEW = {
  "Serval": { eyes: 5, mouth: true, feet: F4, body: ["..ooo......ooo..", "obibo......obibo", "obibo......obibo", "obbbboo..oobbbbo", "obbsbbbbbbbbsbbo", "obbbbbbbbbbbbbbo", "obbbbsbbbbsbbbbo", "obsbbllllllbbsbo", "obbbbllnnllbbbbo", ".obsbllllllbsbo.", "..obbbllllbbbo..", "...oooooooooo..."],
    colors: [
      { name: "Golden", o: "#3a2208", b: "#e8b858", l: "#fff2d8", i: "#ff9f7a", n: "#1a1004", e: "#1a1004", s: "#1a1004" },
      { name: "Sandstone", o: "#3a2a18", b: "#d8c098", l: "#fff8ec", i: "#ff9f7a", n: "#2a1a0c", e: "#2a1a0c", s: "#2a1a0c" },
      { name: "Midnight Spots", o: "#10142a", b: "#6a78b8", l: "#e8ecff", i: "#ff9ad8", n: "#0a0c1c", e: "#0a0c1c", s: "#0a0c1c" },
    ] },
  "Caracal": { eyes: 5, mouth: true, feet: F4, body: ["..t..........t..", ".oto........oto.", ".obbo......obbo.", "obbbboo..oobbbbo", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obbbbbbbbbbbbbbo", "obbtbbllllbbtbbo", "obbbbllnnllbbbbo", ".obbbllllllbbbo.", "..obbbllllbbbo..", "...oooooooooo..."],
    colors: [
      { name: "Desert", o: "#2a1608", b: "#d08848", l: "#fff0dc", i: "#ff8f8f", n: "#0a0604", e: "#0a0604", t: "#0a0604" },
      { name: "Ember", o: "#3a1006", b: "#e8582a", l: "#ffe4d0", i: "#ff9a6a", n: "#0a0402", e: "#0a0402", t: "#0a0402" },
      { name: "Smoke", o: "#1a1c26", b: "#8a90a4", l: "#f0f2f8", i: "#ff9ab0", n: "#06060a", e: "#06060a", t: "#06060a" },
    ] },
  "Ocelot": { eyes: 5, mouth: true, feet: F4, body: ["................", ".oo..........oo.", "obbo........obbo", "obbbboo..oobbbbo", "obbbsbsbbsbsbbbo", "obbbbbbbbbbbbbbo", "obsbbbbbbbbbbsbo", "obsbbllllllbbsbo", "obbbbllnnllbbbbo", ".obsbllllllbsbo.", "..obbbllllbbbo..", "...oooooooooo..."],
    colors: [
      { name: "Jungle", o: "#2a1a08", b: "#e0a040", l: "#fff0d0", i: "#ff9f7a", n: "#1a0e04", e: "#1a0e04", s: "#1a0e04" },
      { name: "Sunset", o: "#3a0e18", b: "#f07a6a", l: "#ffe8e0", i: "#ff9ab8", n: "#220608", e: "#220608", s: "#220608" },
      { name: "Moss", o: "#10281a", b: "#7ab868", l: "#f0ffe8", i: "#ff9fb0", n: "#06140a", e: "#06140a", s: "#06140a" },
    ] },
  "Clouded Leopard": { eyes: 5, mouth: true, feet: F4, body: ["................", ".oo..........oo.", "obbo........obbo", "obccboooooobccbo", "occcbbbbbbbbccco", "obccbbbbbbbbccbo", "obbbbccbbccbbbbo", "obbbbccllccbbbbo", "obbbbllnnllbbbbo", ".obccllbbllccbo.", "..obbbllllbbbo..", "...oooooooooo..."],
    colors: [
      { name: "Cloud", o: "#2a2418", b: "#c8b890", l: "#f8f0e0", i: "#ff9f7a", n: "#14100a", e: "#14100a", c: "#887850" },
      { name: "Dusk Cloud", o: "#241438", b: "#a890d0", l: "#f4ecff", i: "#ff9ad8", n: "#10081c", e: "#10081c", c: "#685090" },
      { name: "Storm", o: "#10182a", b: "#7a8aa8", l: "#e8eef8", i: "#ff9ab0", n: "#080c14", e: "#080c14", c: "#3a4a68" },
    ] },
};
