// 🏠 Blip homes (Blipville: On the Go). Every Blip can have its own customizable house on your town's street.
// This file is only art + rules: the town (app.js) decides when a Blip goes home and what the sheet looks like.
// All of the art is original and drawn with code, so there are no image files to load.
(function () {
  "use strict";

  // 💖 The hearts side of homes. These are the only numbers that touch the game's balance, so they live here, together.
  const BALANCE = {
    visitChance: 0.07,        // each time an idle Blip decides what to do, the chance it heads home (if it has a home)
    visitSeconds: [14, 28],   // how long a visit lasts (a tired Blip stays until it has napped)
    cooldown: 600,            // seconds before the same Blip's home pays out again
    bonus: (cozy) => (cozy >= 8 ? 3 : cozy >= 4 ? 2 : cozy >= 1 ? 1 : 0),   // hearts when a Blip comes out; "cozy" = items placed (0 to 9)
  };

  const HW = 20, HH = 20, SPACING = 30, ROOM_W = 32, ROOM_H = 16;   // house = 20 x 20 cells; a street slot is 30 cells wide
  const HEX = /^#[0-9a-f]{6}$/i;
  const shade = (hex, f) => {
    const n = parseInt(hex.slice(1), 16), a = f < 0 ? 0 : 255, p = Math.abs(f);
    const c = [n >> 16, (n >> 8) & 255, n & 255].map((v) => Math.round(v + (a - v) * p));
    return "#" + c.map((v) => v.toString(16).padStart(2, "0")).join("");
  };
  const WALLS = ["#f4e6c8", "#cfe8ff", "#c8f0d8", "#ffd0e0", "#fff2a8", "#e0d0ff", "#ffd8b8", "#c8ccd8", "#c89a6a", "#ffffff"];
  const ROOFS = ["#d8503a", "#4a7ae8", "#3aa860", "#8a5ae8", "#f09a2a", "#2ab0b0", "#8a5a3a", "#ff7ab0", "#e8c030", "#4a4a5a"];
  const DOORS = ["#7a5230", "#d8402a", "#3a6ae8", "#ffd23a", "#3aa860", "#ffffff", "#2b2b3a", "#a05ae0"];

  // ---------------------------------------------------------------- house shapes
  // Built on a 20 x 20 grid of letters, then given a dark outline.  w/W wall, r/R roof, d/D door, g/G glass, n doorway (dark, lit when
  // someone's home), k/K wood, l/L leaves, s/S stone, q spots.  meta tells the decorations where things are.
  const mk = () => Array.from({ length: HH }, () => Array(HW).fill("."));
  const rect = (g, x, y, w, h, c) => { for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) { const yy = y + j, xx = x + i; if (yy >= 0 && yy < HH && xx >= 0 && xx < HW) g[yy][xx] = c; } };
  function outline(g) {
    const out = g.map((r) => r.slice());
    for (let y = 0; y < HH; y++) for (let x = 0; x < HW; x++) {
      if (g[y][x] !== ".") continue;
      if ([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => (g[y + dy] || [])[x + dx] && g[y + dy][x + dx] !== ".")) out[y][x] = "o";
    }
    return out;
  }
  const STYLE_BUILD = {
    cottage() {
      const g = mk();
      rect(g, 13, 2, 2, 6, "W");                                                         // chimney (the roof covers its foot)
      rect(g, 3, 11, 14, 8, "w"); rect(g, 3, 18, 14, 1, "W");
      for (let i = 0; i <= 8; i++) rect(g, 9 - i, 2 + i, 2 + 2 * i, 1, "r");
      for (let y = 2; y <= 9; y++) for (let x = 0; x < HW; x++) if (g[y][x] === "r" && (x + y) % 4 === 0) g[y][x] = "R";
      rect(g, 1, 10, 18, 1, "R");
      rect(g, 4, 12, 6, 7, "t"); rect(g, 5, 13, 4, 6, "d"); rect(g, 8, 16, 1, 1, "y");   // door
      rect(g, 11, 13, 5, 5, "t"); rect(g, 12, 14, 3, 3, "g"); rect(g, 12, 14, 1, 1, "G");  // window
      return { g, door: { x0: 5, x1: 8, y0: 13 }, entry: 6.5, win: { x: 12, y: 14, w: 3, h: 3 }, chimney: { x: 14, y: 1 }, apex: { x: 9.5, y: 2 },
               eave: { y: 10, x0: 1, x1: 18 }, wallL: 3 };
    },
    tent() {
      const g = mk();
      for (let i = 0; i <= 14; i++) {
        const half = Math.round(i * 0.6);
        for (let x = 9 - half; x <= 10 + half; x++) g[4 + i][x] = (x >> 1) % 2 === 0 ? "r" : "w";
      }
      rect(g, 9, 1, 2, 4, "k");                                                           // pole
      for (let j = 0; j < 8; j++) { const half = 1 + (j >> 1); rect(g, 10 - half - 1, 11 + j, 1, 1, "d"); rect(g, 10 + half, 11 + j, 1, 1, "d"); rect(g, 10 - half, 11 + j, half * 2, 1, "n"); }
      return { g, door: { x0: 8, x1: 11, y0: 11 }, entry: 9.5, win: null, chimney: null, apex: { x: 9.5, y: 1 }, eave: { y: 9, x0: 4, x1: 15 }, wallL: 4 };
    },
    igloo() {
      const g = mk();
      for (let y = 5; y <= 18; y++) {
        const dy = 18.5 - y, half = Math.round(9.5 * Math.sqrt(Math.max(0, 1 - (dy / 14) ** 2)));
        for (let x = 10 - half; x < 10 + half; x++) g[y][x] = y % 3 === 0 || (x + ((y / 3) | 0) % 2 * 2) % 4 === 0 ? "W" : "w";
      }
      rect(g, 11, 12, 8, 7, "w"); rect(g, 11, 12, 8, 1, "r"); rect(g, 12, 13, 6, 1, "R"); rect(g, 13, 14, 4, 5, "n"); rect(g, 12, 14, 1, 5, "r"); rect(g, 17, 14, 1, 5, "r");
      rect(g, 4, 9, 4, 3, "t"); rect(g, 5, 10, 2, 1, "g"); rect(g, 5, 10, 1, 1, "G");
      return { g, door: { x0: 13, x1: 16, y0: 14 }, entry: 14.5, win: { x: 5, y: 10, w: 2, h: 1 }, chimney: { x: 9, y: 4 }, apex: { x: 9.5, y: 5 }, eave: { y: 8, x0: 3, x1: 14 }, wallL: 2 };
    },
    mushroom() {
      const g = mk(), span = [[2, [6, 13]], [3, [4, 15]], [4, [3, 16]], [5, [2, 17]], [6, [1, 18]], [7, [1, 18]], [8, [1, 18]], [9, [1, 18]], [10, [2, 17]]];
      rect(g, 6, 11, 8, 8, "w"); rect(g, 13, 11, 1, 8, "W"); rect(g, 6, 18, 8, 1, "W");
      for (const [y, [a, b]] of span) rect(g, a, y, b - a + 1, 1, y >= 9 ? "R" : "r");
      for (const [x, y, w] of [[4, 4, 2], [12, 4, 2], [8, 3, 2], [3, 7, 2], [15, 7, 2], [10, 6, 3], [6, 7, 2]]) rect(g, x, y, w, w === 3 ? 2 : w, "q");
      rect(g, 8, 13, 4, 6, "d"); rect(g, 8, 13, 1, 1, "w"); rect(g, 11, 13, 1, 1, "w"); rect(g, 11, 16, 1, 1, "y");
      rect(g, 14, 5, 2, 2, "g"); rect(g, 14, 5, 1, 1, "G");
      return { g, door: { x0: 8, x1: 11, y0: 13 }, entry: 10, win: { x: 14, y: 5, w: 2, h: 2 }, chimney: { x: 10, y: 1 }, apex: { x: 9.5, y: 2 }, eave: { y: 10, x0: 2, x1: 17 }, wallL: 6 };
    },
    treehouse() {
      const g = mk();
      for (let y = 0; y <= 10; y++) { const dy = (y - 5.5) / 6.2, half = Math.round(9.5 * Math.sqrt(Math.max(0, 1 - dy * dy)));
        for (let x = 10 - half; x < 10 + half; x++) g[y][x] = (x * 7 + y * 3) % 11 === 0 ? "L" : "l"; }
      rect(g, 8, 10, 4, 9, "k"); rect(g, 11, 10, 1, 9, "K"); rect(g, 6, 17, 8, 2, "k"); rect(g, 6, 18, 1, 1, "K");
      rect(g, 3, 11, 14, 1, "K"); rect(g, 5, 5, 10, 6, "w"); rect(g, 4, 3, 12, 2, "r"); rect(g, 5, 2, 10, 1, "r"); rect(g, 4, 5, 12, 1, "R");
      rect(g, 6, 7, 3, 4, "d"); rect(g, 11, 6, 3, 3, "t"); rect(g, 12, 7, 1, 1, "g"); rect(g, 11, 6, 3, 1, "t");
      rect(g, 12, 7, 1, 1, "G");
      return { g, door: { x0: 6, x1: 8, y0: 7 }, entry: 10, win: { x: 12, y: 7, w: 1, h: 1 }, chimney: { x: 13, y: 1 }, apex: { x: 9.5, y: 2 }, eave: { y: 5, x0: 4, x1: 15 }, wallL: 5 };
    },
    tower() {
      const g = mk();
      rect(g, 5, 7, 10, 12, "s"); rect(g, 14, 7, 1, 12, "S");
      for (let y = 7; y < 19; y++) for (let x = 5; x < 14; x++) if (y % 3 === 0 || (x + (y / 3 | 0) * 2) % 4 === 0) g[y][x] = "S";
      for (let i = 0; i <= 6; i++) rect(g, 9 - i, i + 0, 2 + 2 * i, 1, i % 2 ? "R" : "r");
      rect(g, 4, 6, 12, 1, "r");
      rect(g, 8, 13, 4, 6, "d"); rect(g, 8, 13, 1, 1, "s"); rect(g, 11, 13, 1, 1, "s"); rect(g, 11, 16, 1, 1, "y");
      rect(g, 9, 9, 2, 3, "g"); rect(g, 9, 9, 1, 1, "G");
      return { g, door: { x0: 8, x1: 11, y0: 13 }, entry: 10, win: { x: 9, y: 9, w: 2, h: 3 }, chimney: null, apex: { x: 9.5, y: 0 }, eave: { y: 7, x0: 4, x1: 15 }, wallL: 5 };
    },
  };
  const STYLES = [
    { id: "cottage", name: "Cottage", cost: 0 }, { id: "tent", name: "Tent", cost: 25 }, { id: "igloo", name: "Igloo", cost: 40 },
    { id: "mushroom", name: "Mushroom", cost: 60 }, { id: "treehouse", name: "Treehouse", cost: 60 }, { id: "tower", name: "Tower", cost: 80 },
  ];
  const STYLE_BY = Object.fromEntries(STYLES.map((s) => [s.id, s]));
  const built = {};
  function styleOf(id) {
    if (!built[id]) { const b = STYLE_BUILD[id](); built[id] = { ...b, g: outline(b.g) }; }
    return built[id];
  }

  // ---------------------------------------------------------------- outside decorations (each fits an 8 x 10 box)
  const O = (c, list, X, Y, s) => { for (const [col, x, y, w, h] of list) { c.fillStyle = col; c.fillRect(X + x * s, Y + y * s, w * s, h * s); } };
  const glow = (c, X, Y, s, x, y, r, night) => { if (!night) return; c.fillStyle = "rgba(255,226,120,.22)"; c.fillRect(X + (x - r) * s, Y + (y - r) * s, 2 * r * s, 2 * r * s); c.fillStyle = "rgba(255,226,120,.2)"; c.fillRect(X + (x - r / 2) * s, Y + (y - r / 2) * s, r * s, r * s); };
  const stat = (list) => (c, X, Y, s) => O(c, list, X, Y, s);
  const DECOR = [
    // roof
    { id: "flag", name: "Flag", slots: ["roof"], cost: 10, draw(c, X, Y, s, t, o) { O(c, [["#7a5230", 3, 1, 1, 9]], X, Y, s); c.fillStyle = "#ff5a6a";
      for (let r = 0; r < 3; r++) c.fillRect(X + (4 + Math.round(Math.sin(t * 4 + r) * 0.7)) * s, Y + (1 + r) * s, (r === 2 ? 2 : 3) * s, s); } },
    { id: "vane", name: "Weathervane", slots: ["roof"], cost: 14, draw(c, X, Y, s, t) { const f = Math.sin(t * 0.9) > 0; O(c, [["#8a8fa0", 3, 3, 1, 7], ["#e8c050", 1, 3, 6, 1], [f ? "#e8c050" : "#d8a030", f ? 6 : 0, 2, 1, 3], ["#e8c050", f ? 0 : 6, 3, 1, 1]], X, Y, s); } },
    { id: "smoke", name: "Chimney smoke", slots: ["roof"], cost: 15, at: "chimney", draw(c, X, Y, s, t) {
      for (let i = 0; i < 3; i++) { const ph = (t * 0.45 + i / 3) % 1; c.fillStyle = `rgba(240,240,250,${(0.85 * (1 - ph)).toFixed(2)})`;
        const z = Math.round((1 + ph * 2) * s); c.fillRect(X + 3 * s + Math.sin(ph * 7 + i) * s * 1.2, Y + 9 * s - ph * 9 * s, z, z); } } },
    { id: "nest", name: "Bird nest", slots: ["roof"], cost: 12, draw(c, X, Y, s, t) { const hop = Math.floor(t * 1.5) % 6 === 0 ? 1 : 0;
      O(c, [["#8a5a2a", 1, 8, 6, 2], ["#b87a3a", 2, 7, 4, 1], ["#ff7a5a", 3, 5 - hop, 3, 3], ["#ffd23a", 6, 6 - hop, 1, 1], ["#2b1b33", 3, 6 - hop, 1, 1]], X, Y, s); } },
    // left / right
    { id: "mailbox", name: "Mailbox", slots: ["left"], cost: 8, draw: stat([["#7a5230", 3, 5, 1, 5], ["#4a7ae8", 1, 2, 6, 3], ["#2b3a8a", 1, 4, 6, 1], ["#2b1b33", 1, 3, 1, 1], ["#ff5a5a", 6, 0, 1, 3], ["#ff5a5a", 7, 0, 1, 1]]) },
    { id: "pot", name: "Flower pot", slots: ["left", "right"], cost: 5, draw: stat([["#3a9a4a", 3, 4, 1, 3], ["#3a9a4a", 4, 5, 1, 2], ["#ff7ab8", 2, 2, 2, 2], ["#ffd23a", 4, 3, 2, 2], ["#c8683a", 2, 7, 4, 3], ["#a8502a", 2, 9, 4, 1]]) },
    { id: "bush", name: "Bush", slots: ["left", "right"], cost: 6, draw: stat([["#2f8a3c", 1, 5, 6, 4], ["#3a9a4a", 2, 3, 4, 2], ["#3a9a4a", 1, 5, 5, 3], ["#2a7a3a", 1, 8, 6, 1], ["#ff5a6a", 2, 5, 1, 1], ["#ff5a6a", 5, 6, 1, 1], ["#ff5a6a", 4, 4, 1, 1]]) },
    { id: "lamp", name: "Lamp post", slots: ["left", "right"], cost: 12, draw(c, X, Y, s, t, o) { glow(c, X, Y, s, 3.5, 1.5, 3.5, o.night);
      O(c, [["#3a3a4a", 3, 3, 1, 7], ["#3a3a4a", 2, 9, 3, 1], ["#3a3a4a", 2, 0, 3, 1], ["#fff27a", 2, 1, 3, 2]], X, Y, s); } },
    { id: "birdbath", name: "Bird bath", slots: ["left", "right"], cost: 15, draw: stat([["#b8bcc8", 1, 4, 6, 2], ["#8ad8ff", 2, 4, 4, 1], ["#b8bcc8", 3, 6, 2, 3], ["#98a0b0", 2, 9, 4, 1], ["#ffd23a", 5, 2, 2, 2], ["#ff9a3a", 7, 3, 1, 1]]) },
    { id: "snowman", name: "Snowman", slots: ["left", "right"], cost: 12, draw: stat([["#ffffff", 2, 6, 4, 3], ["#ffffff", 3, 3, 3, 3], ["#2b1b33", 3, 1, 3, 2], ["#2b1b33", 2, 3, 5, 1], ["#2b1b33", 4, 4, 1, 1], ["#ff9a3a", 5, 4, 2, 1], ["#2b1b33", 4, 7, 1, 1], ["#d0e0f0", 2, 8, 4, 1]]) },
    { id: "fence", name: "Picket fence", slots: ["left", "right"], cost: 10, draw: stat([["#e8d0a0", 0, 5, 8, 1], ["#e8d0a0", 0, 8, 8, 1], ...[0, 2, 4, 6].flatMap((x) => [["#fff0d0", x, 4, 1, 6], ["#fff0d0", x, 3, 1, 1]])]) },
    { id: "bed", name: "Flower bed", slots: ["left", "right"], cost: 8, draw: stat([["#6b4a2e", 0, 8, 8, 2], ["#3a9a4a", 1, 6, 1, 2], ["#3a9a4a", 3, 5, 1, 3], ["#3a9a4a", 5, 6, 1, 2], ["#3a9a4a", 7, 5, 1, 3], ["#ff5a8a", 0, 4, 2, 2], ["#ffd23a", 2, 3, 2, 2], ["#a05ae0", 4, 5, 2, 1], ["#ff9a3a", 6, 3, 2, 2]]) },
    { id: "gnome", name: "Garden gnome", slots: ["left", "right"], cost: 12, draw: stat([["#e8453a", 3, 0, 2, 1], ["#e8453a", 2, 1, 4, 2], ["#ffd0a8", 2, 3, 4, 2], ["#2b1b33", 3, 3, 1, 1], ["#2b1b33", 5, 3, 1, 1], ["#ffffff", 2, 5, 4, 3], ["#4a7ae8", 2, 8, 4, 1], ["#7a5230", 2, 9, 1, 1], ["#7a5230", 5, 9, 1, 1]]) },
    // door
    { id: "mat", name: "Welcome mat", slots: ["door"], cost: 4, ground: true, draw: stat([["#c8503a", 0, 8, 8, 2], ["#ffd23a", 1, 9, 6, 1], ["#a8402a", 0, 8, 8, 1]]) },
    { id: "wreath", name: "Wreath", slots: ["door"], cost: 8, dy: 1, draw: stat([["#3a9a4a", 2, 0, 4, 1], ["#3a9a4a", 1, 1, 1, 3], ["#3a9a4a", 6, 1, 1, 3], ["#3a9a4a", 2, 4, 4, 1], ["#2f8a3c", 2, 1, 1, 1], ["#ff5a6a", 2, 3, 1, 1], ["#ff5a6a", 5, 1, 1, 1], ["#ff5a8a", 3, 5, 2, 1]]) },
    { id: "lantern", name: "Hanging lantern", slots: ["door"], cost: 10, hang: true, draw(c, X, Y, s, t, o) { glow(c, X, Y, s, 4, 6, 3.5, o.night);
      O(c, [["#3a3a4a", 3, 0, 2, 1], ["#3a3a4a", 4, 1, 1, 2], ["#3a3a4a", 3, 3, 2, 1], ["#ffd23a", 3, 4, 2, 3], ["#3a3a4a", 3, 7, 2, 1]], X, Y, s); } },
    { id: "sign", name: "Name post", slots: ["door"], cost: 5, ground: true, draw(c, X, Y, s, t, o) {
      O(c, [["#7a5230", 3, 5, 2, 5], ["#7a5230", 0, 1, 8, 4], ["#e8c88a", 1, 2, 6, 2]], X, Y, s);
      if (o.name) { c.fillStyle = "#4a2e18"; c.font = `800 ${Math.max(7, Math.round(s * 1.9))}px ${o.font || "sans-serif"}`; c.textAlign = "center"; c.textBaseline = "middle";
        let txt = o.name; while (txt.length > 2 && c.measureText(txt).width > 6 * s - 2) txt = txt.slice(0, -1); c.fillText(txt, X + 4 * s, Y + 3 * s + 1); c.textAlign = "left"; } } },
    // trim (along the whole front of the house)
    { id: "lights", name: "Fairy lights", slots: ["trim"], cost: 20, wide: true, draw(c, X, Y, s, t, o, st) {
      const e = st.eave, cols = ["#ff5a6a", "#ffd23a", "#5ad8ff", "#7aff8a"];
      c.fillStyle = "#3a3a4a"; for (let x = e.x0; x <= e.x1; x++) c.fillRect(X + x * s, Y + (e.y + 1 + (x % 3 === 1 ? 1 : 0)) * s, s, Math.max(1, s >> 1));
      for (let x = e.x0 + 1, i = 0; x <= e.x1; x += 3, i++) { const on = (Math.floor(t * 2 + i) % 2 === 0) || o.night; c.fillStyle = on ? cols[i % 4] : shade(cols[i % 4], -0.35);
        c.fillRect(X + x * s, Y + (e.y + 2) * s, s, s); if (o.night && on) { c.fillStyle = "rgba(255,255,255,.18)"; c.fillRect(X + (x - 1) * s, Y + (e.y + 1) * s, 3 * s, 3 * s); } } } },
    { id: "bunting", name: "Bunting", slots: ["trim"], cost: 12, wide: true, draw(c, X, Y, s, t, o, st) {
      const e = st.eave, cols = ["#ff7ab8", "#ffd23a", "#5ad8ff", "#7aff8a", "#ff9a3a"];
      c.fillStyle = "#6b4a2e"; c.fillRect(X + e.x0 * s, Y + (e.y + 1) * s, (e.x1 - e.x0 + 1) * s, Math.max(1, s >> 1));
      for (let x = e.x0 + 1, i = 0; x <= e.x1 - 1; x += 3, i++) { c.fillStyle = cols[i % 5]; c.fillRect(X + x * s, Y + (e.y + 2) * s, 2 * s, s); c.fillRect(X + (x + 0.5) * s, Y + (e.y + 3) * s, s, s); } } },
    { id: "ivy", name: "Ivy", slots: ["trim"], cost: 14, wide: true, draw(c, X, Y, s, t, o, st) {
      const x0 = st.wallL; c.fillStyle = "#2f8a3c";
      for (let y = st.eave.y + 1; y < HH - 1; y++) { const off = Math.round(Math.sin(y * 0.9) * 0.8) + 1; c.fillRect(X + (x0 + off) * s, Y + y * s, s, s); if (y % 3 === 0) { c.fillStyle = "#4aa84a"; c.fillRect(X + (x0 + off + 1) * s, Y + y * s, s, s); c.fillStyle = "#2f8a3c"; } } } },
    { id: "boxes", name: "Window boxes", slots: ["trim"], cost: 10, wide: true, draw(c, X, Y, s, t, o, st) {
      if (!st.win) return; const w = st.win, x = w.x - 1, y = w.y + w.h + 1;
      c.fillStyle = "#8a5a3a"; c.fillRect(X + x * s, Y + y * s, (w.w + 2) * s, 2 * s);
      for (let i = 0; i < w.w + 2; i++) { c.fillStyle = ["#ff7ab8", "#ffd23a", "#ff5a6a"][i % 3]; c.fillRect(X + (x + i) * s, Y + (y - 1) * s, s, s); } } },
  ];
  const DECOR_BY = Object.fromEntries(DECOR.map((d) => [d.id, d]));
  const OUT_SLOTS = [["roof", "Roof"], ["left", "Left side"], ["right", "Right side"], ["door", "Door"], ["trim", "Trim"]];

  // ---------------------------------------------------------------- the inside (a cutaway room, 32 x 16 cells)
  const FURN = [
    // bed (drawn 12 wide, 5 tall, on the floor)
    { id: "basket", name: "Basket", slot: "bed", cost: 0, draw: stat([["#b88a48", 1, 4, 10, 1], ["#d8b070", 0, 2, 12, 2], ["#d8b070", 1, 4, 10, 1], ["#ff9fc0", 2, 1, 8, 2], ["#ff7aa0", 2, 2, 8, 1], ["#b88a48", 0, 2, 1, 2], ["#b88a48", 11, 2, 1, 2]]) },
    { id: "softbed", name: "Soft bed", slot: "bed", cost: 12, draw: stat([["#8a5a3a", 0, 3, 12, 2], ["#7ab0ff", 1, 1, 10, 2], ["#5a90e8", 1, 2, 10, 1], ["#ffffff", 1, 0, 3, 2], ["#e8e8f8", 1, 1, 3, 1]]) },
    { id: "hammock", name: "Hammock", slot: "bed", cost: 18, draw: stat([["#6b4a2e", 0, 0, 1, 5], ["#6b4a2e", 11, 0, 1, 5], ["#e8a850", 1, 1, 2, 1], ["#e8a850", 2, 2, 3, 1], ["#e8a850", 4, 3, 4, 1], ["#e8a850", 7, 2, 3, 1], ["#e8a850", 9, 1, 2, 1], ["#c88830", 4, 4, 4, 1]]) },
    { id: "cloud", name: "Cloud bed", slot: "bed", cost: 30, draw(c, X, Y, s, t) { O(c, [["#cfe8ff", 1, 4, 10, 1], ["#ffffff", 0, 2, 12, 2], ["#ffffff", 1, 1, 4, 1], ["#ffffff", 6, 0, 4, 2], ["#e8f4ff", 2, 3, 8, 1]], X, Y, s);
      if (Math.sin(t * 3) > 0.3) O(c, [["#fff27a", 10, -1, 1, 1], ["#fff27a", 1, 0, 1, 1]], X, Y, s); } },
    // rug (flat, 12 wide, 3 tall)
    { id: "roundrug", name: "Round rug", slot: "rug", cost: 6, draw: stat([["#e8688a", 1, 0, 10, 3], ["#e8688a", 0, 1, 12, 1], ["#ffb0c8", 3, 1, 6, 1]]) },
    { id: "stripes", name: "Striped rug", slot: "rug", cost: 8, draw: stat([["#4a7ae8", 0, 0, 12, 3], ["#ffd23a", 2, 0, 2, 3], ["#ffd23a", 6, 0, 2, 3], ["#ffffff", 10, 0, 1, 3]]) },
    { id: "heartrug", name: "Heart rug", slot: "rug", cost: 12, draw: stat([["#8a5ae8", 0, 0, 12, 3], ["#ff7aa0", 3, 0, 2, 2], ["#ff7aa0", 7, 0, 2, 2], ["#ff7aa0", 2, 1, 8, 1], ["#ff7aa0", 4, 2, 4, 1]]) },
    // wall (6 wide, 5 tall)
    { id: "picture", name: "Picture", slot: "wall", cost: 6, draw: stat([["#8a5a3a", 0, 0, 6, 5], ["#8ad8ff", 1, 1, 4, 3], ["#3aa860", 1, 3, 4, 1], ["#ffd23a", 3, 1, 1, 1]]) },
    { id: "clock", name: "Clock", slot: "wall", cost: 8, draw: stat([["#7a5230", 1, 0, 4, 5], ["#7a5230", 0, 1, 6, 3], ["#fffaf0", 1, 1, 4, 3], ["#fffaf0", 2, 0, 2, 5], ["#2b1b33", 3, 1, 1, 2], ["#2b1b33", 3, 2, 2, 1]]) },
    { id: "shelf", name: "Shelf", slot: "wall", cost: 12, draw: stat([["#8a5a3a", 0, 4, 6, 1], ["#e8453a", 0, 1, 1, 3], ["#4a7ae8", 1, 2, 1, 2], ["#ffd23a", 2, 1, 1, 3], ["#3aa860", 4, 2, 2, 2], ["#c8683a", 4, 3, 2, 1]]) },
    { id: "poster", name: "Moon poster", slot: "wall", cost: 10, draw: stat([["#2a2a6a", 0, 0, 6, 5], ["#ffe66a", 2, 1, 2, 2], ["#2a2a6a", 3, 1, 1, 1], ["#ffffff", 1, 3, 1, 1], ["#ffffff", 4, 3, 1, 1], ["#ffffff", 4, 1, 1, 1]]) },
    // corner (5 wide, 9 tall)
    { id: "lamp", name: "Lamp", slot: "corner", cost: 8, draw(c, X, Y, s, t, o) { if (o.night) { c.fillStyle = "rgba(255,226,120,.2)"; c.fillRect(X - 2 * s, Y, 9 * s, 7 * s); }
      O(c, [["#7a5230", 2, 3, 1, 6], ["#6b4a2e", 1, 8, 3, 1], ["#ffe9a0", 0, 0, 5, 3], ["#ffd070", 1, 2, 3, 1]], X, Y, s); } },
    { id: "plant", name: "Plant", slot: "corner", cost: 6, draw: stat([["#3a9a4a", 2, 0, 1, 4], ["#3a9a4a", 0, 2, 2, 2], ["#3a9a4a", 3, 1, 2, 3], ["#2f8a3c", 1, 3, 3, 2], ["#c8683a", 1, 5, 3, 4], ["#a8502a", 1, 8, 3, 1]]) },
    { id: "toybox", name: "Toy box", slot: "corner", cost: 10, draw: stat([["#ff7ab8", 0, 4, 5, 5], ["#d85a98", 0, 4, 5, 1], ["#ffd23a", 0, 1, 2, 2], ["#5ad8ff", 2, 2, 2, 2], ["#7aff8a", 3, 0, 2, 2]]) },
    { id: "cookiejar", name: "Cookie jar", slot: "corner", cost: 14, draw: stat([["#7a5230", 0, 5, 5, 1], ["#7a5230", 1, 6, 1, 3], ["#7a5230", 3, 6, 1, 3], ["#cfe8ff", 1, 1, 3, 4], ["#c98a4b", 1, 3, 3, 2], ["#5a3418", 2, 3, 1, 1], ["#7a5230", 1, 0, 3, 1]]) },
  ];
  const FURN_BY = Object.fromEntries(FURN.map((f) => [f.id, f]));
  const IN_SLOTS = [["bed", "Bed"], ["rug", "Rug"], ["wall", "On the wall"], ["corner", "Corner"]];
  const BED_X = 2, RUG_X = 9, WALL_X = 14, CORNER_X = 26, FLOOR = 11;

  // ---------------------------------------------------------------- homes
  const defaultHouse = () => ({ style: "cottage", wall: WALLS[0], roof: ROOFS[0], door: DOORS[0], decor: {}, furn: { bed: "basket" } });
  function clean(h) {                                         // anything from a save: keep what makes sense, fix the rest
    const d = defaultHouse();
    if (!h || typeof h !== "object") return d;
    const col = (v, def) => (typeof v === "string" && HEX.test(v) ? v.toLowerCase() : def);
    const out = { style: STYLE_BY[h.style] ? h.style : d.style, wall: col(h.wall, d.wall), roof: col(h.roof, d.roof), door: col(h.door, d.door), decor: {}, furn: {} };
    for (const [slot] of OUT_SLOTS) { const it = DECOR_BY[(h.decor || {})[slot]]; if (it && it.slots.includes(slot)) out.decor[slot] = it.id; }
    for (const [slot] of IN_SLOTS) { const it = FURN_BY[(h.furn || {})[slot]]; if (it && it.slot === slot) out.furn[slot] = it.id; }
    if (!out.furn.bed) out.furn.bed = "basket";
    return out;
  }
  const cozy = (h) => OUT_SLOTS.filter(([s]) => h.decor[s]).length + IN_SLOTS.filter(([s]) => h.furn[s] && !(s === "bed" && h.furn[s] === "basket")).length;

  function draw(c, h, cx, base, s, t, o = {}) {              // the outside; cx = middle of the house, base = the ground line
    const st = styleOf(h.style), left = Math.round(cx - (HW * s) / 2), top = base - HH * s, lit = !!(o.lit || o.night);
    const p = { w: h.wall, W: shade(h.wall, -0.16), r: h.roof, R: shade(h.roof, -0.2), d: h.door, D: shade(h.door, -0.25), o: "#2b1b33",
      g: lit ? "#ffe27a" : "#8fd0f0", G: lit ? "#fff3b8" : "#d6f1ff", n: o.lit ? "#ffcf5a" : "#2b1f3a", k: "#7a5230", K: "#5a3a22", l: "#4aa84a", L: "#2f8a3c",
      s: "#aab0c0", S: "#8a90a4", y: "#ffd23a", q: "#fffaf0", t: "#efe2c4" };
    for (let y = 0; y < HH; y++) for (let x = 0; x < HW; x++) { const ch = st.g[y][x]; if (ch === ".") continue; c.fillStyle = p[ch] || "#f0f"; c.fillRect(left + x * s, top + y * s, s, s); }
    const opt = { night: !!o.night, name: o.name, font: o.font };
    const slotBox = (slot) => {                              // top-left of an 8 x 10 box, in cells from the house's top-left
      if (slot === "left") return [-6, HH - 10];
      if (slot === "right") return [HW - 2, HH - 10];
      return null;
    };
    for (const slot of ["left", "right"]) { const it = DECOR_BY[h.decor[slot]], b = slotBox(slot); if (it) it.draw(c, left + b[0] * s, top + b[1] * s, s, t, opt, st); }
    const doorMid = (st.door.x0 + st.door.x1 + 1) / 2;
    const dd = DECOR_BY[h.decor.door];
    if (dd) dd.draw(c, Math.round(left + (doorMid - 4) * s), top + (dd.ground ? HH - 10 : dd.hang ? st.eave.y + 1 : st.door.y0 + (dd.dy || 0)) * s, s, t, opt, st);
    const tr = DECOR_BY[h.decor.trim]; if (tr) tr.draw(c, left, top, s, t, opt, st);
    const rf = DECOR_BY[h.decor.roof];
    if (rf) { const at = rf.at === "chimney" && st.chimney ? st.chimney : st.apex; rf.draw(c, Math.round(left + (at.x - 3.5) * s), top + (at.y + 1 - 10) * s, s, t, opt, st); }
    return { left, top, width: HW * s, height: HH * s };
  }

  function drawRoom(c, h, X, Y, s, t, o = {}) {             // the inside, with the Blip's picture (a canvas) on its bed
    const wall = shade(h.wall, 0.35), night = !!o.night;
    c.fillStyle = "#2b1b33"; c.fillRect(X - s, Y - s, (ROOM_W + 2) * s, (ROOM_H + 2) * s);
    c.fillStyle = wall; c.fillRect(X, Y, ROOM_W * s, FLOOR * s);
    c.fillStyle = shade(wall, -0.07); for (let x = 0; x < ROOM_W; x += 4) c.fillRect(X + x * s, Y, s, FLOOR * s);
    c.fillStyle = "#c89a64"; c.fillRect(X, Y + FLOOR * s, ROOM_W * s, (ROOM_H - FLOOR) * s);
    c.fillStyle = "#b08450"; for (let y = FLOOR + 1; y < ROOM_H; y += 2) c.fillRect(X, Y + y * s, ROOM_W * s, Math.max(1, s >> 2));
    c.fillStyle = shade(h.wall, -0.3); c.fillRect(X, Y + (FLOOR - 1) * s, ROOM_W * s, s);   // skirting board
    c.fillStyle = "#7a5230"; c.fillRect(X + 20 * s, Y + s, 6 * s, 6 * s);                  // the window
    c.fillStyle = night ? "#1c1840" : "#9ad8ff"; c.fillRect(X + 21 * s, Y + 2 * s, 4 * s, 4 * s);
    c.fillStyle = night ? "#ffffff" : "#ffffff"; if (night) { c.fillRect(X + 22 * s, Y + 3 * s, s, s); c.fillRect(X + 24 * s, Y + 4 * s, s, s); } else c.fillRect(X + 21 * s, Y + 3 * s, 2 * s, s);
    c.fillStyle = "#7a5230"; c.fillRect(X + 22.5 * s, Y + 2 * s, Math.max(1, s >> 1), 4 * s);
    const at = (slot, list, x, y) => { const it = list[h[slot === "bed" || slot === "rug" || slot === "wall" || slot === "corner" ? "furn" : "decor"][slot]]; if (it) it.draw(c, X + x * s, Y + y * s, s, t, { night }, null); };
    at("rug", FURN_BY, RUG_X, 13); at("bed", FURN_BY, BED_X, FLOOR); at("wall", FURN_BY, WALL_X, 2); at("corner", FURN_BY, CORNER_X, 6);
    if (o.pet) { const px = X + (BED_X + 6) * s - o.pet.width / 2, py = Y + (FLOOR + 3) * s - o.pet.height; c.drawImage(o.pet, Math.round(px), Math.round(py)); }
  }

  window.HOUSES = { BALANCE, HW, HH, SPACING, ROOM_W, ROOM_H, STYLES, STYLE_BY, DECOR, DECOR_BY, FURN, FURN_BY, OUT_SLOTS, IN_SLOTS, WALLS, ROOFS, DOORS,
                    defaultHouse, clean, cozy, draw, drawRoom, styleOf, entryCell: (h) => styleOf(h.style).entry };
})();
