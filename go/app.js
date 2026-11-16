/* Blipville: On the Go, the phone version of Blipville.
   Pixel art, colors and lines come from data.js (exported from blip.pyw), so both versions match. */
(() => {
  "use strict";
  const D = window.BLIP_DATA;
  const KINDS = D.kinds;
  const RARE = new Set(D.groups.rare);
  const NIGHT = new Set(D.groups.nightShift);
  const EGG_COST = D.eggCost;
  const MAX_PETS = 8;
  const SAVE_KEY = "blipville-go-v1";
  const HEART = [".x.x.", "xxxxx", "xxxxx", ".xxx.", "..x.."];
  const ZED = ["xxxx", "..x.", ".x..", "xxxx"];
  const COOKIE = [".cccc.", "cdcccc", "cccdcc", "ccccdc", "cdcccc", ".cccc."];
  const rnd = (a, b) => a + Math.random() * (b - a);
  const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const $ = (id) => document.getElementById(id);

  // ------------------------------------------------------------------ save (per device)
  let save = { hearts: 0, hatched: [], pets: [], lastDay: null, lastSeen: null, hatsOwned: [] };
  try { Object.assign(save, JSON.parse(localStorage.getItem(SAVE_KEY)) || {}); } catch (e) { /* fresh start */ }
  let saveTimer = null;
  function persist(now = false) {
    const write = () => {
      save.pets = pets.map((p) => ({ kind: p.kind, color: p.color, name: p.name, hat: p.hat || null, hunger: Math.round(p.hunger), energy: Math.round(p.energy) }));
      save.lastSeen = Date.now();
      try { localStorage.setItem(SAVE_KEY, JSON.stringify(save)); } catch (e) { /* private mode: still playable */ }
    };
    clearTimeout(saveTimer);
    if (now) write(); else saveTimer = setTimeout(write, 400);
  }
  const isUnlocked = (k) => (RARE.has(k) ? save.hatched.includes(k) : !NIGHT.has(k));

  // ------------------------------------------------------------------ canvas & layout
  const cv = $("world"), ctx = cv.getContext("2d");
  let W = 0, H = 0, S = 5, GROUND = 0, DPR = 1;
  function layout() {
    DPR = Math.min(window.devicePixelRatio || 1, 3);
    W = window.innerWidth; H = window.innerHeight;
    cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR);
    S = clamp(Math.round(Math.min(W, 700) / 78), 4, 7);
    const bar = $("bar").getBoundingClientRect();
    GROUND = Math.round(H - bar.height - 18);
    for (const p of pets) p.x = clamp(p.x, 8 * S, W - 8 * S);
  }
  window.addEventListener("resize", layout);

  // ------------------------------------------------------------------ pets
  const pets = [];
  let cookies = [];
  let pointer = { x: 0, y: 0 };
  let greeted = {};
  const now = () => performance.now() / 1000;

  function makePet(kind, color, name, x) {
    const k = KINDS[kind];
    const p = {
      kind, color: color ?? k.default ?? 0, name: name || pick(D.names), x: x ?? rnd(60, W - 60), y: rnd(140, 260), vx: 0, vy: 0,
      state: "fall", until: 0, target: null, facing: 1, energy: 100, hunger: 10, face: "normal", faceUntil: 0,
      bubble: null, blinkUntil: 0, nextBlink: now() + rnd(1, 4), lastPetReward: -99, nextShift: now() + rnd(6, 12),
      squashUntil: 0, particles: [],
    };
    return p;
  }
  function addPet(kind, opts = {}) {
    if (pets.length >= MAX_PETS) { toast(`Town's full! (${MAX_PETS} Blips max) Send one away first.`); return null; }
    const used = new Set(pets.map((p) => p.name));
    const name = opts.name || pick(D.names.filter((n) => !used.has(n))) || pick(D.names);
    const p = makePet(kind, opts.color, name, opts.x);
    pets.push(p);
    if (!opts.quiet) say(p, `hi! i'm ${name}`, 2.5);
    persist();
    return p;
  }
  const say = (p, text, secs = 3) => { p.bubble = { text, until: now() + secs }; };
  const setFace = (p, face, secs) => { p.face = face; p.faceUntil = now() + secs; };
  const setState = (p, st, secs = 0) => { p.state = st; p.until = now() + secs; };
  const linesFor = (p) => D.lines.idle.concat(KINDS[p.kind].lines, KINDS[p.kind].lines);
  function burst(p, kind, n) {
    for (let i = 0; i < n; i++) p.particles.push({ kind, x: rnd(-26, 26) * S / 4, y: 13 * S + rnd(-6, 6), vx: rnd(-20, 20), vy: rnd(-70, -40), life: rnd(1, 1.6), born: now() });
  }
  function reward(p, n) {
    save.hearts += n; persist(); updateHearts(true);
    if (p) p.particles.push({ kind: "plus", text: `+${n} 💖`, x: 30 * S / 4, y: 13 * S + 4, vx: 0, vy: -26, life: 1.6, born: now() });
  }

  function petIt(p) {
    if (p.state === "sleep") { wake(p); return; }
    const t = now();
    if (t - p.lastPetReward > 6) { p.lastPetReward = t; reward(p, 1); }
    say(p, pick(D.lines.pet), 2); setFace(p, "happy", 1.5); burst(p, "heart", 4);
    if (p.state !== "fall" && p.state !== "held") { p.vy = 260; p.vx = 0; setState(p, "fall"); }
    vibrate(10);
  }
  function feed(p) {
    if (p.state === "sleep") wake(p);
    const cx = clamp(p.x + pick([-1, 1]) * rnd(50, 90), 20, W - 20);
    cookies.push({ x: cx, y: 260, vy: 0, landed: false, owner: p });
    say(p, "ooh! a cookie!", 2); setFace(p, "surprised", 1);
  }
  function nap(p) {
    if (p.state === "sleep") { wake(p); return; }
    if (p.state !== "held" && p.state !== "fall") { setState(p, "sleep", 20); say(p, "good night...", 2); }
  }
  function wake(p) { setState(p, "idle", 1.5); say(p, pick(D.lines.wake), 2.5); setFace(p, "surprised", 0.8); }

  function lift(p, t) {
    const move = KINDS[p.kind].move, moving = p.state === "walk", k = S / 4;
    if (move === "float") return p.state === "sleep" ? 2 * k : (9 + 4 * Math.sin(t * 2.5)) * k;
    if (move === "hop" && moving) return Math.abs(Math.sin(t * 7)) * 12 * k;
    if (move === "flutter" && moving) return (8 + 3 * Math.sin(t * 12)) * k;
    return 0;
  }

  function decide(p, t) {
    const hour = new Date().getHours();
    if (p.energy < 25 || ((hour >= 23 || hour < 6) && Math.random() < 0.15)) { say(p, "*yawn* nap time...", 2.5); setState(p, "sleep", 20); return; }
    if (p.hunger > 70 && Math.random() < 0.35) say(p, pick(D.lines.hungry), 3);
    const r = Math.random();
    if (r < 0.45) { p.target = rnd(30, W - 30); setState(p, "walk", 12); }
    else if (r < 0.62) { say(p, pick(linesFor(p)), 3); setState(p, "idle", rnd(2, 4)); }
    else setState(p, "idle", rnd(2, 5));
  }

  function update(p, t, dt) {
    const k = KINDS[p.kind];
    if (t > p.nextBlink) { p.blinkUntil = t + 0.15; p.nextBlink = t + rnd(2, 6); }
    if (p.state !== "sleep") p.energy = Math.max(0, p.energy - dt * 0.12);
    p.hunger = Math.min(100, p.hunger + dt * 0.08);
    if (k.shifty && t > p.nextShift && p.state !== "sleep" && p.state !== "held") {
      p.nextShift = t + rnd(8, 15); p.color = (p.color + 1) % k.colors.length;
      if (Math.random() < 0.4) say(p, "*changes color*", 1.8);
    }
    const speed = 64 * (S / 4) * (k.speed || 1);
    switch (p.state) {
      case "held": return;
      case "fall": {
        p.vy -= 1900 * dt; p.x += p.vx * dt; p.y += p.vy * dt;
        if (p.x < 8 * S) { p.x = 8 * S; p.vx = -p.vx * 0.6; }
        if (p.x > W - 8 * S) { p.x = W - 8 * S; p.vx = -p.vx * 0.6; }
        if (p.y <= 0) {
          p.y = 0;
          if (p.vy < -320) {
            if (p.vy < -900) say(p, pick(D.lines.land), 2);
            p.vy = -p.vy * 0.35; p.vx *= 0.7; p.squashUntil = t + 0.15;
          } else { p.vy = 0; p.vx = 0; p.squashUntil = t + 0.2; setState(p, "idle", rnd(0.6, 1.5)); }
        }
        return;
      }
      case "sleep":
        p.energy = Math.min(100, p.energy + dt * 2);
        if (Math.random() < dt * 0.8) p.particles.push({ kind: "z", x: 18 * S / 4, y: 13 * S, vx: 14, vy: -22, life: 2.5, born: t });
        if (p.energy >= 100 && t > p.until) { wake(p); reward(p, 2); }
        return;
      case "eat":
        if (t > p.until) {
          reward(p, p.hunger > 60 ? 5 : 3);
          p.hunger = 0; p.energy = Math.min(100, p.energy + 15);
          cookies = cookies.filter((c) => c !== p.eating); p.eating = null;
          say(p, pick(D.lines.eat), 2.5); setFace(p, "happy", 2); burst(p, "heart", 5); setState(p, "idle", 2);
        } else if (Math.random() < 0.3) {
          p.particles.push({ kind: "crumb", x: rnd(-6, 6), y: 6 * S, vx: rnd(-40, 40), vy: rnd(40, 90), life: 0.6, born: t });
        }
        return;
    }
    // a landed cookie for this pet? go get it
    const ck = cookies.find((c) => c.owner === p && c.landed);
    if (ck && (p.state === "idle" || p.state === "walk")) { p.target = ck.x; p.state = "walk"; p.until = t + 10; }
    if (p.state === "walk" && p.target != null) {
      const d = p.target - p.x;
      p.facing = d > 0 ? 1 : -1;
      if (Math.abs(d) <= speed * dt || t > p.until) {
        if (Math.abs(d) <= speed * dt) p.x = p.target;
        p.target = null;
        if (ck && Math.abs(ck.x - p.x) < 30) { p.eating = ck; setState(p, "eat", 1.8); setFace(p, "munch", 1.8); }
        else setState(p, "idle", rnd(1, 3));
      } else p.x += speed * dt * p.facing;
    } else if (p.state === "idle" && t > p.until) decide(p, t);
  }

  function socialize(t) {
    for (let i = 0; i < pets.length; i++) for (let j = i + 1; j < pets.length; j++) {
      const a = pets[i], b = pets[j];
      if (!["idle", "walk"].includes(a.state) || !["idle", "walk"].includes(b.state) || Math.abs(a.x - b.x) > 18 * S) continue;
      const key = a.name + "|" + b.name;
      if (t - (greeted[key] || -999) < 60) continue;
      greeted[key] = t;
      say(a, pick([`hi ${b.name}!`, `oh, ${b.name}!`, `hey ${b.name} :)`]), 2.5);
      say(b, pick([`hi ${a.name}!`, "oh hi!", `${a.name}!! :D`]), 2.5);
      setFace(a, "happy", 1.5); setFace(b, "happy", 1.5);
      a.facing = b.x > a.x ? 1 : -1; b.facing = -a.facing;
    }
  }

  // ------------------------------------------------------------------ pixel art (same rules as the desktop app)
  const isNight = () => { const h = new Date().getHours(); return h >= 22 || h < 6; };
  function grid(kind, colorIdx, opt = {}) {
    const k = KINDS[kind], cols = k.colors, pal = Object.assign({}, cols[colorIdx % cols.length], k.extra || {});
    const t = opt.t ?? now(), st = opt.state || "idle";
    let body = pal.art || k.body;
    if (k.alt && ["walk", "fall", "held"].includes(st) && Math.floor(t * 10) % 2) body = k.alt;
    const g = Array.from({ length: 13 }, () => Array(16).fill(null));
    const lying = st === "sleep" || opt.squash, shift = lying ? 1 : 0;
    body.forEach((row, y) => [...row].forEach((ch, x) => { if (ch !== "." && y + shift < 13) g[y + shift][x] = pal[ch] || pal.o; }));
    if (!lying && k.feet) {
      const f = k.feet;
      const feet = st === "fall" || st === "held" || (opt.lift || 0) > 3 ? f.air : st === "walk" ? (Math.floor(t * 6) % 2 ? f.walk1 : f.walk2) : f.stand;
      [...feet].forEach((ch, x) => { const X = x + (k.dx || 0); if (ch !== "." && X >= 0 && X < 16) g[12][X] = pal.f || pal.o; });
    }
    const fdy = k.eyes - 5, fdx = k.dx || 0;
    const px = (x, y, c) => { y += shift + fdy; x += fdx; if (x >= 0 && x < 16 && y >= 0 && y < 13) g[y][x] = c; };
    let face = opt.face || "normal";
    if (st === "sleep") face = "sleep";
    const e = pal.e;
    const lum = 0.299 * parseInt(e.slice(1, 3), 16) + 0.587 * parseInt(e.slice(3, 5), 16) + 0.114 * parseInt(e.slice(5, 7), 16);
    let shine = lum > 150 ? pal.o : "#ffffff";
    if (NIGHT.has(kind) && isNight()) shine = e;
    if (opt.silhouette) {
      for (const row of g) for (let x = 0; x < 16; x++) if (row[x]) row[x] = "#5c528c";
      return g;
    }
    if (face === "sleep" || (opt.blink && face === "normal")) { for (const x of [4, 5, 10, 11]) px(x, 6, e); }
    else if (face === "happy") { for (const ex of [4, 9]) { px(ex, 6, e); px(ex + 1, 5, e); px(ex + 2, 6, e); } }
    else if (face === "munch") { for (const ex of [4, 10]) { px(ex, 6, e); px(ex + 1, 6, e); } }
    else {
      const [ox, oy] = face === "surprised" ? [0, 0] : (opt.look || [0, 0]);
      for (const ex of [4, 10]) { for (let a = 0; a < 2; a++) for (let b = 0; b < 2; b++) px(ex + ox + a, 5 + oy + b, e); px(ex + ox, 5 + oy, shine); }
    }
    if (k.mouth) {
      if (face === "surprised") { px(7, 8, e); px(8, 8, e); px(7, 9, e); px(8, 9, e); }
      else if (face === "happy") { px(6, 8, e); px(7, 9, e); px(8, 9, e); px(9, 8, e); }
      else if (face === "munch") { if (Math.floor(t * 8) % 2) { px(7, 8, e); px(8, 8, e); } px(7, 9, e); px(8, 9, e); }
      else if (face !== "sleep") { px(7, 9, e); px(8, 9, e); }
    }
    return g;
  }
  // ------------------------------------------------------------------ hats & outfits (same rules as blip.pyw)
  const HATS = D.hats;
  function currentSeason(d = new Date()) {
    const md = (d.getMonth() + 1) * 100 + d.getDate();
    if (md >= 1015 && md <= 1102) return "spooky";
    if (md >= 1201 || md <= 229) return "winter";
    if (md >= 320 && md <= 531) return "spring";
    if (md >= 922 && md <= 1130) return "autumn";
    return "summer";
  }
  const hatInShop = (n) => !HATS[n].season || HATS[n].season === currentSeason();
  function hatCells(kind, name, shift = 0) {
    const k = KINDS[kind], hat = HATS[name], rows = hat.rows, w = rows[0].length;
    const half = 8 - w / 2, f = Math.floor(half);       // round half to even, exactly like Python's round()
    const left = (half - f !== 0.5 ? Math.round(half) : (f % 2 === 0 ? f : f + 1)) + (k.dx || 0) + (hat.x || 0);
    let top;
    if (hat.slot === "head") {
      let headTop = k.body.findIndex((r) => r.length - r.split(".").length + 1 >= 8);
      if (headTop < 0) headTop = k.body.findIndex((r) => r.replace(/\./g, ""));
      top = headTop + shift + (hat.overlap ?? 1) - rows.length;
    } else if (hat.slot === "face") top = k.eyes + shift + (hat.y || 0);
    else top = Math.min(k.eyes + 5, 11) + shift + (hat.y || 0);
    const out = [];
    rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch !== ".") out.push([top + r, left + c, hat.colors[ch]]); }));
    return out;
  }
  function drawHat(c, kind, name, x, y, s, shift = 0) {
    let topRow = 0;
    if (!name || !HATS[name]) return 0;
    for (const [r, col, color] of hatCells(kind, name, shift)) { c.fillStyle = color; c.fillRect(x + col * s, y + r * s, s, s); topRow = Math.min(topRow, r); }
    return topRow * s;
  }
  function dressedThumb(kind, color, hat, scale = 3) {
    const pad = 8, c = document.createElement("canvas"); c.width = 16 * scale; c.height = (13 + pad) * scale;
    const cx = c.getContext("2d"); drawGrid(cx, grid(kind, color, { t: 0 }), 0, pad * scale, scale); drawHat(cx, kind, hat, 0, pad * scale, scale);
    return c;
  }

  function drawGrid(c, g, x, y, s) {
    for (let r = 0; r < g.length; r++) {
      let col = 0;
      while (col < 16) {
        const color = g[r][col];
        if (!color) { col++; continue; }
        let end = col;
        while (end + 1 < 16 && g[r][end + 1] === color) end++;
        c.fillStyle = color; c.fillRect(x + col * s, y + r * s, (end - col + 1) * s, s);
        col = end + 1;
      }
    }
  }
  function thumb(kind, color, silhouette = false, scale = 4) {
    const c = document.createElement("canvas"); c.width = 16 * scale; c.height = 13 * scale;
    drawGrid(c.getContext("2d"), grid(kind, color, { silhouette, t: 0 }), 0, 0, scale);
    return c;
  }

  // ------------------------------------------------------------------ drawing the town
  const stars = Array.from({ length: 60 }, () => [Math.random(), Math.random() * 0.6, Math.random()]);
  function sky(t) {
    const h = new Date().getHours() + new Date().getMinutes() / 60;
    const night = h >= 20 || h < 6, dusk = (h >= 17 && h < 20) || (h >= 6 && h < 8);
    const [top, bottom] = night ? ["#151233", "#3a2f63"] : dusk ? ["#5a3a8a", "#ffa98a"] : ["#6fb8ff", "#c8e8ff"];
    const gr = ctx.createLinearGradient(0, 0, 0, GROUND);
    gr.addColorStop(0, top); gr.addColorStop(1, bottom);
    ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
    if (night) {
      for (const [sx, sy, tw] of stars) { ctx.globalAlpha = 0.5 + 0.5 * Math.sin(t * 2 + tw * 9); ctx.fillStyle = "#fff6d8"; ctx.fillRect(sx * W, sy * GROUND, 3, 3); }
      ctx.globalAlpha = 1; ctx.fillStyle = "#fff6d8"; ctx.beginPath(); ctx.arc(W * 0.8, GROUND * 0.18, 22, 0, 7); ctx.fill();
      ctx.fillStyle = top; ctx.beginPath(); ctx.arc(W * 0.8 + 10, GROUND * 0.18 - 6, 20, 0, 7); ctx.fill();
    } else {
      ctx.fillStyle = dusk ? "#ffd27a" : "#fff2a8"; ctx.beginPath(); ctx.arc(W * 0.8, GROUND * (dusk ? 0.55 : 0.18), 26, 0, 7); ctx.fill();
      ctx.fillStyle = "rgba(255,255,255,.85)";
      for (let i = 0; i < 3; i++) { const cx = ((t * (8 + i * 4) + i * 260) % (W + 200)) - 100, cy = GROUND * (0.15 + i * 0.12); pixCloud(cx, cy); }
    }
    // little pixel hills + ground
    ctx.fillStyle = night ? "#23304a" : "#7fcf7a";
    for (let x = 0; x < W; x += 6) { const hh = 26 + 14 * Math.sin(x / 70) + 8 * Math.sin(x / 23); ctx.fillRect(x, GROUND - hh, 6, hh); }
    ctx.fillStyle = night ? "#1b2238" : "#5aa85a"; ctx.fillRect(0, GROUND, W, H - GROUND);
    ctx.fillStyle = night ? "#141a2c" : "#4a8a4a"; ctx.fillRect(0, GROUND, W, 6);
  }
  function pixCloud(x, y) { for (const [dx, dy, w] of [[0, 8, 70], [12, 0, 40], [20, 14, 60]]) ctx.fillRect(Math.round(x + dx), Math.round(y + dy), w, 12); }

  function bubble(text, cx, bottom) {
    ctx.font = "700 14px " + getComputedStyle(document.body).fontFamily;
    const maxW = Math.min(220, W - 24), words = text.split(" "), lines = [];
    let line = "";
    for (const w of words) { const test = line ? line + " " + w : w; if (ctx.measureText(test).width > maxW - 20 && line) { lines.push(line); line = w; } else line = test; }
    lines.push(line);
    const bw = Math.max(...lines.map((l) => ctx.measureText(l).width)) + 20, bh = lines.length * 18 + 12;
    const x = clamp(cx - bw / 2, 6, W - bw - 6), y = bottom - bh - 8;
    ctx.fillStyle = "#ffffff"; ctx.strokeStyle = "#222"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.roundRect(x, y, bw, bh, 10); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(cx - 6, y + bh - 1); ctx.lineTo(cx + 6, y + bh - 1); ctx.lineTo(cx, y + bh + 7); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillRect(cx - 5, y + bh - 3, 10, 3);
    ctx.fillStyle = "#222"; ctx.textAlign = "center"; ctx.textBaseline = "top";
    lines.forEach((l, i) => ctx.fillText(l, x + bw / 2, y + 7 + i * 18));
  }
  function nameTag(text, cx, bottom) {
    ctx.font = "700 11px " + getComputedStyle(document.body).fontFamily;
    const w = ctx.measureText(text).width + 10;
    ctx.fillStyle = "rgba(20,16,36,.85)"; ctx.beginPath(); ctx.roundRect(cx - w / 2, bottom - 16, w, 16, 6); ctx.fill();
    ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(text, cx, bottom - 8);
    return 20;
  }

  function drawPet(p, t) {
    const l = lift(p, t);
    const left = Math.round(p.x - 8 * S), top = Math.round(GROUND - 13 * S - p.y - l);
    const dx = pointer.x - p.x, dy = pointer.y - (top + 6 * S);
    const look = Math.hypot(dx, dy) < 30 ? [0, 0] : [dx < -40 ? -1 : dx > 40 ? 1 : 0, dy < -80 ? -1 : dy > 40 ? 1 : 0];
    const face = t < p.faceUntil ? p.face : "normal";
    drawGrid(ctx, grid(p.kind, p.color, { t, state: p.state, face, blink: t < p.blinkUntil, look, lift: l / (S / 4), squash: t < p.squashUntil }), left, top, S);
    const hatTop = drawHat(ctx, p.kind, p.hat, left, top, S, (p.state === "sleep" || t < p.squashUntil) ? 1 : 0);
    // particles
    p.particles = p.particles.filter((q) => t - q.born < q.life);
    for (const q of p.particles) {
      const a = t - q.born, qx = p.x + q.x + q.vx * a, qy = GROUND - p.y - q.y + q.vy * a + (q.kind === "crumb" ? 300 * a * a : 0);
      if (q.kind === "heart") drawMask(HEART, qx, qy, 3, "#ff4f7b");
      else if (q.kind === "z") drawMask(ZED, qx, qy, 2 + Math.floor(a), "#bcd2ff");
      else if (q.kind === "crumb") { ctx.fillStyle = "#c98a4b"; ctx.fillRect(qx, qy, 3, 3); }
      else if (q.kind === "plus") {
        ctx.font = "800 12px " + getComputedStyle(document.body).fontFamily;
        const w = ctx.measureText(q.text).width + 10;
        ctx.fillStyle = "#e8457a"; ctx.beginPath(); ctx.roundRect(qx - w / 2, qy - 9, w, 18, 8); ctx.fill();
        ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(q.text, qx, qy);
      }
    }
    let above = top + hatTop - 4;
    above -= nameTag(p.name, p.x, above);
    if (p.bubble && t < p.bubble.until) bubble(p.bubble.text, p.x, above);
  }
  function drawMask(mask, x, y, s, color) {
    ctx.fillStyle = color;
    mask.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === "x") ctx.fillRect(x + c * s, y + r * s, s, s); }));
  }
  function drawCookies(t) {
    for (const c of cookies) {
      if (!c.landed) { c.vy += 1500 * (1 / 60); c.y = Math.max(0, c.y - c.vy * (1 / 60)); if (c.y <= 0) c.landed = true; }
      if (c.owner && c.owner.eating === c) continue;
      COOKIE.forEach((row, r) => [...row].forEach((ch, x) => {
        if (ch === ".") return; ctx.fillStyle = ch === "c" ? "#c98a4b" : "#5a3418";
        ctx.fillRect(c.x - 9 + x * 3, GROUND - c.y - 18 + r * 3, 3, 3);
      }));
    }
  }

  // ------------------------------------------------------------------ main loop
  let last = now();
  function frame() {
    const t = now(), dt = Math.min(0.05, t - last); last = t;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    ctx.imageSmoothingEnabled = false;
    sky(t);
    for (const p of pets) update(p, t, dt);
    socialize(t);
    drawCookies(t);
    for (const p of [...pets].sort((a, b) => (a === held ? 1 : 0) - (b === held ? 1 : 0))) drawPet(p, t);
    requestAnimationFrame(frame);
  }

  // ------------------------------------------------------------------ touch: tap = pet, drag = toss, hold = menu
  let held = null, press = null, holdTimer = null, trail = [];
  function petAt(x, y) {
    for (let i = pets.length - 1; i >= 0; i--) {
      const p = pets[i], top = GROUND - 13 * S - p.y - lift(p, now());
      if (x > p.x - 8 * S - 6 && x < p.x + 8 * S + 6 && y > top - 6 && y < top + 13 * S + 6) return p;
    }
    return null;
  }
  cv.addEventListener("pointerdown", (e) => {
    pointer = { x: e.clientX, y: e.clientY };
    const p = petAt(e.clientX, e.clientY);
    if (!p) return;
    cv.setPointerCapture(e.pointerId);
    press = { p, x: e.clientX, y: e.clientY, moved: false, opened: false };
    trail = [[now(), e.clientX, e.clientY]];
    clearTimeout(holdTimer);
    holdTimer = setTimeout(() => { if (press && !press.moved) { press.opened = true; vibrate(15); openPetSheet(p); } }, 480);
  });
  cv.addEventListener("pointermove", (e) => {
    pointer = { x: e.clientX, y: e.clientY };
    if (!press) return;
    if (!press.moved && Math.hypot(e.clientX - press.x, e.clientY - press.y) > 9) {
      press.moved = true; clearTimeout(holdTimer);
      held = press.p; setState(held, "held"); say(held, pick(D.lines.held), 2.5); setFace(held, "surprised", 999);
    }
    if (held) {
      held.x = clamp(e.clientX, 8 * S, W - 8 * S);
      held.y = Math.max(0, GROUND - e.clientY - 6 * S);
      trail.push([now(), e.clientX, e.clientY]); trail = trail.slice(-6);
    }
  });
  const endPress = (e) => {
    clearTimeout(holdTimer);
    if (!press) return;
    if (held) {
      const [t0, x0, y0] = trail[0], dt = Math.max(now() - t0, 1 / 60);
      held.vx = clamp((e.clientX - x0) / dt, -1600, 1600) * 0.6;
      held.vy = clamp(-(e.clientY - y0) / dt, -1600, 1600) * 0.6;
      setFace(held, "surprised", 0.6); setState(held, "fall"); held = null;
    } else if (!press.opened) petIt(press.p);
    press = null;
  };
  cv.addEventListener("pointerup", endPress);
  cv.addEventListener("pointercancel", endPress);

  // ------------------------------------------------------------------ UI: hearts, toast, sheets
  function updateHearts(bump) {
    $("heartCount").textContent = save.hearts;
    if (bump) { const h = $("hearts"); h.classList.remove("bump"); void h.offsetWidth; h.classList.add("bump"); }
  }
  let toastTimer = null;
  function toast(text, secs = 3) {
    const el = $("toast"); el.textContent = text; el.classList.add("show");
    clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove("show"), secs * 1000);
  }
  const vibrate = (ms) => { try { navigator.vibrate && navigator.vibrate(ms); } catch (e) { /* not supported */ } };
  function openSheet(id) { document.querySelectorAll(".sheet").forEach((s) => (s.hidden = s.id !== id)); }
  function closeSheets() { document.querySelectorAll(".sheet").forEach((s) => (s.hidden = true)); persist(); }
  document.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", closeSheets));
  document.querySelectorAll(".sheet").forEach((s) => s.addEventListener("pointerdown", (e) => { if (e.target === s) closeSheets(); }));

  let sheetPet = null;
  function openPetSheet(p) {
    sheetPet = p;
    $("petName").value = p.name;
    $("petKind").textContent = p.kind + (RARE.has(p.kind) ? " · rare ✨" : "");
    const pc = $("petPortrait").getContext("2d"); pc.clearRect(0, 0, 96, 100);
    drawGrid(pc, grid(p.kind, p.color, { t: 0, face: "happy" }), 8, 31, 5); drawHat(pc, p.kind, p.hat, 8, 31, 5);
    const chips = $("colorChips"); chips.innerHTML = "";
    KINDS[p.kind].colors.forEach((col, i) => {
      const b = document.createElement("button"); b.className = i === p.color ? "on" : "";
      b.appendChild(thumb(p.kind, i, false, 3)); b.append(col.name);
      b.onclick = () => { p.color = i; say(p, `${col.name.toLowerCase()}!`, 1.5); burst(p, "heart", 2); persist(); openPetSheet(p); };
      chips.appendChild(b);
    });
    $("sheetNap").textContent = p.state === "sleep" ? "☀️ Wake" : "💤 Nap";
    const hc = $("hatChips"); hc.innerHTML = "";
    for (const name of Object.keys(HATS).filter(hatInShop)) {
      const owned = save.hatsOwned.includes(name), wearing = p.hat === name;
      const b = document.createElement("button"); b.className = wearing ? "on" : "";
      b.appendChild(dressedThumb(p.kind, p.color, name));
      b.append(name);
      const tag = document.createElement("small");
      tag.textContent = wearing ? "✓ on" : owned ? "owned" : `💖 ${HATS[name].price}`;
      tag.className = owned || wearing ? "owned" : "price"; b.appendChild(tag);
      b.onclick = () => {
        if (wearing) { p.hat = null; say(p, "back to basics!", 2); }
        else if (owned) { p.hat = name; say(p, pick(["how do i look?", "so stylish!", "*strikes a pose*"]), 2.5); setFace(p, "happy", 1.5); }
        else {
          const price = HATS[name].price;
          if (save.hearts < price) { toast(`${name} costs ${price} 💖. You have ${save.hearts}. Care for your Blips to earn more!`, 3.5); return; }
          save.hearts -= price; save.hatsOwned.push(name); updateHearts(true);
          p.hat = name; say(p, `a new ${name.toLowerCase()}! thank you!!`, 3); setFace(p, "happy", 2); burst(p, "heart", 5);
        }
        persist(true); openPetSheet(p);
      };
      hc.appendChild(b);
    }
    $("hatSeason").textContent = Object.values(HATS).some((h) => h.season === currentSeason()) ? `✨ ${currentSeason()} items are in!` : "";
    openSheet("petSheet");
  }
  $("petName").addEventListener("input", (e) => { if (sheetPet) { sheetPet.name = e.target.value.trim().slice(0, 16) || sheetPet.name; persist(); } });
  $("sheetFeed").onclick = () => { feed(sheetPet); closeSheets(); };
  $("sheetNap").onclick = () => { nap(sheetPet); closeSheets(); };
  $("sheetPet").onclick = () => { petIt(sheetPet); closeSheets(); };
  $("sheetBye").onclick = () => {
    if (pets.length <= 1) { toast("Your town needs at least one Blip! 🏡"); return; }
    pets.splice(pets.indexOf(sheetPet), 1); toast(`👋 ${sheetPet.name} waved goodbye.`); closeSheets();
  };
  $("sheetKind").onclick = () => openZoo(sheetPet);

  // collection
  function openZoo(swapPet = null) {
    const grid_ = $("zooGrid"); grid_.innerHTML = "";
    const groups = [["Critters", D.groups.critters], ["Animals", D.groups.animals], ["Rare ✨ (hatch from eggs)", D.groups.rare],
                    ["Night Shift 🌙 (coming to On the Go soon)", D.groups.nightShift]];
    let found = 0, total = 0;
    for (const [title, kinds] of groups) {
      const h = document.createElement("div"); h.className = "zooGroup"; h.textContent = title; grid_.appendChild(h);
      const cells = document.createElement("div"); cells.className = "zooCells";
      for (const k of kinds) {
        total++;
        const open = isUnlocked(k); if (open) found++;
        const b = document.createElement("button");
        b.className = open ? "" : "locked";
        b.appendChild(thumb(k, KINDS[k].default || 0, !open, 4));
        b.append(open ? k : "???");
        b.onclick = () => {
          if (!open) { toast(RARE.has(k) ? "🥚 Hatch it from a Mystery Egg!" : "🌙 Coming to On the Go soon!"); return; }
          if (swapPet) {
            swapPet.kind = k; swapPet.color = KINDS[k].default || 0; say(swapPet, `i'm a ${k} now!`, 2); setFace(swapPet, "happy", 1.2);
            burst(swapPet, "heart", 3); closeSheets();
          } else if (addPet(k)) closeSheets();
        };
        cells.appendChild(b);
      }
      grid_.appendChild(cells);
    }
    $("zooCount").textContent = `${found}/${total}`;
    $("zooHint").textContent = swapPet ? `Pick a new kind for ${swapPet.name}.` : "Tap a Blip to bring it to town.";
    openSheet("zooSheet");
  }

  // eggs
  const EGG = ["....oooo....", "...oeeeeo...", "..oeesseeo..", ".oeeeeeeseo.", ".oeseeeeeeo.", "oeeeeeeeeseo",
               "oeeesseeeeeo", "oeeeeeeeeeeo", "oeseeeeeesso", ".oeeeeeeeeo.", "..oeeeeeeo..", "...oooooo..."];
  function openEgg() {
    const left = D.groups.rare.filter((k) => !save.hatched.includes(k));
    if (!left.length) { toast("You've hatched every rare Blip! 🏆"); return; }
    if (save.hearts < EGG_COST) {
      toast(`A Mystery Egg costs ${EGG_COST} 💖. You have ${save.hearts}. Pet, feed and nap your Blips to earn more!`, 4.5);
      return;
    }
    const weights = left.map((k) => (k === "Golden Blip" ? 0.25 : 1));
    let r = Math.random() * weights.reduce((a, b) => a + b, 0), kind = left[0];
    for (let i = 0; i < left.length; i++) { r -= weights[i]; if (r <= 0) { kind = left[i]; break; } }
    save.hearts -= EGG_COST; save.hatched.push(kind); persist(true); updateHearts(true);
    const ec = $("eggCanvas"), c = ec.getContext("2d"), t0 = now();
    $("eggText").textContent = "✨ something is hatching… ✨"; $("eggSub").textContent = "";
    const done = $("eggDone"); done.disabled = true; done.textContent = "Hatching…";
    openSheet("eggSheet");
    (function anim() {
      if ($("eggSheet").hidden) return;
      const t = now() - t0;
      c.clearRect(0, 0, 280, 220); c.imageSmoothingEnabled = false;
      if (t < 2.6) {
        const wob = Math.sin(t * (6 + t * 6)) * Math.min(10, 2 + t * 4);
        EGG.forEach((row, y) => [...row].forEach((ch, x) => {
          if (ch === ".") return; c.fillStyle = { o: "#3a2a4a", e: "#fff4dc", s: "#ff9fd0" }[ch];
          c.fillRect(140 - 48 + wob + x * 8, 110 - 56 + y * 8, 8, 8);
        }));
        if (t > 1.2) {
          const pts = [[-30, -8], [-14, -18], [0, -6], [16, -20], [30, -8]].slice(0, Math.min(5, 2 + Math.floor((t - 1.2) * 3)));
          c.strokeStyle = "#3a2a4a"; c.lineWidth = 3; c.beginPath();
          pts.forEach(([x, y], i) => (i ? c.lineTo : c.moveTo).call(c, 140 + x + wob, 110 + y)); c.stroke();
        }
        if (t > 0.3 && Math.floor(t * 8) % 4 === 0) vibrate(8);
      } else {
        if (t < 2.85) { c.fillStyle = "#fff"; c.fillRect(0, 0, 280, 220); }
        for (let i = 0; i < 12; i++) {
          const a = i * Math.PI / 6 + t, rr = 86 + 8 * Math.sin(t * 4 + i);
          c.fillStyle = ["#ffd23a", "#ff9fd0", "#9ad8ff"][i % 3]; c.fillRect(140 + Math.cos(a) * rr - 3, 104 + Math.sin(a) * rr * 0.7 - 3, 6, 6);
        }
        drawGrid(c, grid(kind, 0, { t: 0, face: "happy" }), 140 - 48, 104 - 39, 6);
        if (done.disabled) {
          done.disabled = false; done.textContent = "Yay! Bring it to town 🐾"; vibrate([30, 40, 30]);
          $("eggText").textContent = `You hatched a ${kind}!`;
          $("eggSub").textContent = `Rare Blips found: ${save.hatched.length}/${D.groups.rare.length}`;
          done.onclick = () => {
            closeSheets();
            if (pets.length >= MAX_PETS) { toast(`${kind} is waiting in your 📖 Zoo (town is full).`); return; }
            const p = addPet(kind, { quiet: true }); if (p) say(p, "i'm new here! hi!! ✨", 4);
          };
        }
      }
      requestAnimationFrame(anim);
    })();
  }

  // share a picture of the town
  async function share() {
    const shot = document.createElement("canvas"); shot.width = cv.width; shot.height = cv.height;
    const c = shot.getContext("2d"); c.drawImage(cv, 0, 0);
    c.font = `800 ${Math.round(16 * DPR)}px sans-serif`; c.fillStyle = "rgba(255,255,255,.9)"; c.textAlign = "left";
    c.fillText("🏘️ Blipville", 14 * DPR, (GROUND + 30) * DPR);
    const blob = await new Promise((r) => shot.toBlob(r, "image/png"));
    const file = new File([blob], "my-blipville.png", { type: "image/png" });
    try {
      if (navigator.canShare && navigator.canShare({ files: [file] })) { await navigator.share({ files: [file], title: "My Blipville" }); return; }
    } catch (e) { if (e && e.name === "AbortError") return; }
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "my-blipville.png"; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    toast("📸 Saved a picture of your town!");
  }

  $("feedBtn").onclick = () => {
    const awake = pets.filter((p) => p.state !== "held");
    if (!awake.length) return;
    const p = awake.reduce((a, b) => (b.hunger > a.hunger ? b : a));
    feed(p); toast(`🍪 Fed ${p.name}!`, 1.8);
  };
  $("friendBtn").onclick = () => {
    const pool = D.groups.critters.concat(D.groups.animals).filter(isUnlocked);
    addPet(pick(pool), { x: rnd(40, W - 40) });
  };
  $("eggBtn").onclick = openEgg;
  $("collectionBtn").onclick = () => openZoo(null);
  $("shareBtn").onclick = share;
  $("helpBtn").onclick = () => openSheet("helpSheet");
  $("helpEggCost").textContent = EGG_COST;

  // ------------------------------------------------------------------ start
  layout();
  if (save.pets && save.pets.length) {
    const away = save.lastSeen ? (Date.now() - save.lastSeen) / 3.6e6 : 0;   // hours away
    for (const s of save.pets) {
      if (!KINDS[s.kind] || !isUnlocked(s.kind)) continue;
      const p = makePet(s.kind, s.color, s.name);
      p.hunger = Math.min(100, (s.hunger ?? 10) + away * 8); p.energy = s.energy ?? 100; p.hat = s.hat || null;
      pets.push(p);
    }
  }
  if (!pets.length) { addPet("Blip", { name: "Blip", quiet: true }); setTimeout(() => openSheet("helpSheet"), 900); }
  const today = new Date().toISOString().slice(0, 10);
  if (save.lastDay !== today) {
    save.lastDay = today;
    setTimeout(() => { reward(pets[0], 10); say(pets[0], "daily treat! +10 💖", 4); }, 1600);
  }
  updateHearts(false);
  persist();
  document.addEventListener("visibilitychange", () => { if (document.hidden) persist(true); });
  window.addEventListener("pagehide", () => persist(true));
  requestAnimationFrame(frame);
  if ("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register("sw.js").catch(() => {});
  window.blipvilleGo = { pets, save, addPet, petIt, feed, nap, openEgg, openZoo, openPetSheet, hatCells, currentSeason };   // handy for testing
})();
