/* Blipville: On the Go, the phone version of Blipville.
   Pixel art, colors and lines come from data.js (exported from blip.pyw), so both versions match. */
(() => {
  "use strict";
  const D = window.BLIP_DATA;
  const KINDS = D.kinds;
  const RARE = new Set(D.groups.rare);
  const NIGHT = new Set(D.groups.nightShift);
  const CRYPT = new Set(D.groups.cryptids);
  const KAIJU = new Set([...(D.groups.kaiju || []), ...(D.parkedKinds || [])]), HITS = D.kaijuHits || 3;
  const GIFTS = new Set(D.groups.gifts || []);
  const LEG = new Set(D.groups.legends || []), LEGEND_WORLD = D.legendWorld || {};   // world legends
  const GHOST = new Set(D.groups.ghosts || []);
  const DREAMS = new Set(Object.keys(D.badDreams || {}));          // 🧸 Bad Dreams (plushies until midnight)
  const DREAM_ROBOS = [...DREAMS].filter((k) => D.badDreams[k].big);
  const badDreamHour = () => new Date().getHours() < 6;
  const plushNow = (kind) => !!(KINDS[kind] && KINDS[kind].plush) && !badDreamHour();
  const EGYPT = new Set(D.egyptGods || []), DIG = D.dig || { cols: 6, rows: 5, tries: 8, treasures: 4, hearts: 3 };
  const AWAKEN_FORM = D.awakenForm || {};
  const AWAKEN_CHAIN = D.awakenChain || Object.fromEntries(Object.entries(AWAKEN_FORM).map(([b, f]) => [b, [f]]));   // some Blips awaken up to 3 times
  const AWAKEN_BASE = Object.fromEntries(Object.entries(AWAKEN_CHAIN).flatMap(([b, fs]) => fs.map((f) => [f, b])));
  const STAGE_COSTS = D.stageCosts || [D.crystalCost || 75, 150, 250];
  const awStage = (k) => AWAKEN_BASE[k] ? AWAKEN_CHAIN[AWAKEN_BASE[k]].indexOf(k) + 1 : 0;                                        // ghosts: at night, tap while they glow
  const WORLD_LOOK = {
    "Plant World":  { sky: ["#8fd8a8", "#e8ffd8"], land: ["#4ab85a", "#3a9a4a", "#2f7a3a"], fx: [["leaf", 3], ["petal", 3]], sun: "#fff2a8" },
    "Sweets World": { sky: ["#ffb0d8", "#fff0c8"], land: ["#ff8ab8", "#c8885a", "#a86a3a"], fx: [["sprinkle", 7]], sun: "#fff0f8" },
    "Ocean World":  { sky: ["#0e4a8a", "#3ab0d8"], land: ["#2a7aa8", "#e8d8a0", "#c8b880"], fx: [["bubble", 6]], sun: null },
    "Dino World":   { sky: ["#c8582a", "#ffc87a"], land: ["#5a7a3a", "#6a4a2a", "#4a3418"], fx: [["ash", 5], ["leaf", 1]], sun: "#ffe08a", volcano: true },
    "Space World":  { sky: ["#06061a", "#2a1a5a"], land: ["#5a5a7a", "#8a8aa8", "#6a6a88"], fx: [["star", 5]], sun: null, planet: true },
    "Egypt World":  { sky: ["#e88a3a", "#ffe8b0"], land: ["#e8c878", "#d8b060", "#c89a48"], fx: [["ash", 3]], sun: "#fff4c0" },
  };
  const WORLDS = D.worlds || [], WORLD_OF = {};          // world Blips are locked until you unlock their world
  for (const w of WORLDS) for (const [t, ks] of D.groups.tabs || []) if (t === w.tab) for (const k of ks) WORLD_OF[k] = w.name;
  const EGG_COST = D.eggCost;
  let view = window;                                   // the window the town is in (main page or the pop-out)
  const doc = () => view.document;
  const maxPets = () => (W >= 900 ? 12 : 8);           // bigger screens fit a bigger town
  const SAVE_KEY = "blipville-go-v1";
  const HEART = [".x.x.", "xxxxx", "xxxxx", ".xxx.", "..x.."];
  const ZED = ["xxxx", "..x.", ".x..", "xxxx"];
  const COOKIE = [".cccc.", "cdcccc", "cccdcc", "ccccdc", "cdcccc", ".cccc."];
  const rnd = (a, b) => a + Math.random() * (b - a);
  const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const $ = (id) => doc().getElementById(id) || document.getElementById(id);

  // ------------------------------------------------------------------ save (per device)
  let save = { hearts: 0, hatched: [], pets: [], lastDay: null, lastSeen: null, hatsOwned: [], sound: false, peeked: [], nightsWon: 0, cryptids: [], kaiju: [], gifts: [], worlds: [], world: null, legends: [], ghosts: [], badDreams: [], eventKinds: [], merch: [], merchKinds: [], redeemed: [], trophies: [], stats: {}, awakened: [], awakenLevel: {}, rivalsBeaten: [], skins: [], eventPoints: {} };
  // 💾 save safety: check every field when loading, keep the last good save as a backup, never throw away a damaged save,
  // and tell the player when saving fails instead of failing silently
  const SAVE_DEFAULTS = JSON.parse(JSON.stringify(save)), BAK_KEY = SAVE_KEY + "-backup", BROKEN_KEY = SAVE_KEY + "-broken";
  let saveNote = null, saveFailedAt = 0, saveWarnedAt = 0, lastBackup = 0;
  const numOr = (v, d, lo = 0, hi = Infinity) => (Number.isFinite(+v) && v !== null && v !== "" && typeof v !== "boolean" ? Math.min(hi, Math.max(lo, +v)) : d);
  function sanitizeSave(raw) {
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
    const out = { ...raw };
    const RN = D.kindRenames || {}, ren = (n) => { if (typeof n !== "string") return n; const i = n.indexOf(":"); return i > 0 ? (RN[n.slice(0, i)] || n.slice(0, i)) + n.slice(i) : (RN[n] || n); };
    for (const [k, v] of Object.entries(out)) if (Array.isArray(v) && k !== "pets") out[k] = v.map(ren);     // renamed Blips keep their place in old saves
    if (Array.isArray(out.pets)) out.pets = out.pets.map((p) => (p && typeof p === "object" && typeof p.kind === "string" ? { ...p, kind: ren(p.kind) } : p));
    if (out.awakenLevel && typeof out.awakenLevel === "object") out.awakenLevel = Object.fromEntries(Object.entries(out.awakenLevel).map(([k, v]) => [ren(k), v]));
    for (const [k, def] of Object.entries(SAVE_DEFAULTS)) {
      if (!(k in raw)) continue;                                   // older saves: missing fields keep their defaults
      const v = out[k];
      if (Array.isArray(def)) out[k] = Array.isArray(v) ? v : typeof v === "string" ? [v] : [];
      else if (typeof def === "number") out[k] = numOr(v, def);
      else if (typeof def === "boolean") out[k] = typeof v === "boolean" ? v : def;
      else if (def && typeof def === "object") out[k] = v && typeof v === "object" && !Array.isArray(v) ? v : {};
      else out[k] = v === null || typeof v === "string" || typeof v === "number" ? v : null;
    }
    for (const [k, def] of Object.entries(SAVE_DEFAULTS)) if (Array.isArray(def) && k !== "pets") out[k] = [...new Set((out[k] || []).filter((x) => typeof x === "string"))];
    out.pets = (out.pets || []).filter((p) => p && typeof p === "object" && typeof p.kind === "string").map((p) => ({ ...p,
      name: String(p.name || p.kind).slice(0, 16), color: numOr(p.color, 0, 0, 999) | 0, hunger: numOr(p.hunger, 10, 0, 100),
      energy: numOr(p.energy, 100, 0, 100), bond: numOr(p.bond, 0), tints: p.tints && typeof p.tints === "object" ? p.tints : {} }));
    return out;
  }
  const readKey = (key) => { const text = localStorage.getItem(key); if (text == null) return { missing: true }; try { return { text, data: JSON.parse(text) }; } catch (e) { return { text }; } };
  try {
    const main = readKey(SAVE_KEY);
    let clean = main.missing ? null : sanitizeSave(main.data);
    if (!main.missing && !clean) {                                  // damaged: keep it, then fall back to the backup
      try { localStorage.setItem(BROKEN_KEY, main.text); } catch (e) { /* no room */ }
      const bak = readKey(BAK_KEY); clean = bak.missing ? null : sanitizeSave(bak.data);
      saveNote = clean ? "💾 Your save was damaged, so Blipville loaded your last backup." : "💾 Your save was damaged and there was no backup, so Blipville started a new town. The damaged save was kept.";
    }
    if (clean) Object.assign(save, clean);
  } catch (e) { /* storage blocked: fresh start, still playable */ }
  if (!save.worlds.includes("Egypt World")) save.worlds.push("Egypt World");     // 🏺 free for everyone; its gods are dug up
  save.gods = save.gods || [];
  for (const prefix of save.merch || []) {          // 🎟️ a code redeemed before its Blip arrived: hand out the Blip + skin now
    const m = ((D.merch || {}).items || {})[prefix] || {};
    if (m.kind && D.kinds[m.kind]) {
      const skin = `${m.kind}:${m.name}`; save.skins = save.skins || []; if (!save.skins.includes(skin)) save.skins.push(skin);
      save.merchKinds = save.merchKinds || []; if (!save.merchKinds.includes(m.kind)) save.merchKinds.push(m.kind);
    }
  }
  let saveTimer = null;
  let frozen = false;                                   // set while a loaded save code is taking over
  function persist(now = false) {
    if (frozen) return;
    const write = () => {
      save.pets = pets.map((p) => ({ kind: p.kind, color: p.color, name: p.name, hat: p.hat || null, hat2: p.hat2 || null, tints: p.tints || {}, hunger: Math.round(p.hunger), energy: Math.round(p.energy), bond: Math.round(p.bond || 0) }));
      save.lastSeen = Date.now();
      try {
        const prev = localStorage.getItem(SAVE_KEY);
        if (prev && Date.now() - lastBackup > 60000) {                 // only a save that reads fine becomes the backup
          try { if (sanitizeSave(JSON.parse(prev))) { localStorage.setItem(BAK_KEY, prev); lastBackup = Date.now(); } } catch (e) { /* skip */ }
        }
        localStorage.setItem(SAVE_KEY, JSON.stringify(save)); saveFailedAt = 0;
      } catch (e) {                                                    // private mode or full storage: still playable, but say so
        saveFailedAt = saveFailedAt || Date.now();
        if (Date.now() - saveWarnedAt > 600000) { saveWarnedAt = Date.now(); setTimeout(() => toast("⚠️ Blipville can't save on this device right now (private mode or storage full). Your town still works.", 5), 0); }
      }
    };
    clearTimeout(saveTimer);
    if (now) write(); else saveTimer = setTimeout(write, 400);
  }
  // ------------------------------------------------------------------ sound effects (made with code, off by default)
  let actx = null, noiseBuf = null;
  const lastSfx = {};
  function audio() {
    if (!actx) {
      const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return null;
      actx = new AC();
      noiseBuf = actx.createBuffer(1, actx.sampleRate, actx.sampleRate);
      const d = noiseBuf.getChannelData(0); let last = 0;
      for (let i = 0; i < d.length; i++) { last = last * 0.6 + (Math.random() * 2 - 1) * 0.4; d[i] = last; }
    }
    if (actx.state === "suspended") actx.resume();
    return actx;
  }
  let lastVoice = 0;
  function voiceBlip(kind) {                     // 🔊 one talking blip in this Blip's voice (same voices as the desktop app)
    if (!save.sound || save.voices === false) return;
    const a = audio(); if (!a) return;
    const t = performance.now() / 1000; if (t - lastVoice < 0.07) return; lastVoice = t;
    const [pitch, wave] = (KINDS[kind] && KINDS[kind].voice) || [440, "tri"];
    const f = pitch * pick([0.94, 1, 1.07]), at = a.currentTime + 0.005;
    const o = a.createOscillator(), g = a.createGain();
    o.type = wave === "tri" ? "triangle" : wave; o.frequency.setValueAtTime(f, at); o.frequency.linearRampToValueAtTime(f * 1.02, at + 0.045);
    g.gain.setValueAtTime(0.0001, at); g.gain.linearRampToValueAtTime(wave === "square" ? 0.06 : 0.12, at + 0.004); g.gain.exponentialRampToValueAtTime(0.0001, at + 0.045);
    o.connect(g).connect(a.destination); o.start(at); o.stop(at + 0.06);
  }
  function sfx(name) {
    if (!save.sound) return;
    const a = audio(); if (!a) return;
    const nowT = performance.now() / 1000;
    if (nowT - (lastSfx[name] || 0) < ({ thud: 0.8, munch: 0.5 }[name] || 0.08)) return;
    lastSfx[name] = nowT;
    const out = a.createGain(); out.gain.value = 0.5; out.connect(a.destination);
    let at = a.currentTime + 0.01;
    const tone = (f0, f1, dur, vol = 0.35, type = "sine", decay = true) => {
      const o = a.createOscillator(), g = a.createGain();
      o.type = type === "tri" ? "triangle" : type; o.frequency.setValueAtTime(f0, at); o.frequency.linearRampToValueAtTime(f1, at + dur);
      g.gain.setValueAtTime(0.0001, at); g.gain.linearRampToValueAtTime(type === "square" ? vol * 0.5 : vol, at + 0.005);
      if (decay) g.gain.exponentialRampToValueAtTime(0.0001, at + dur); else g.gain.setValueAtTime(0.0001, at + dur);
      o.connect(g).connect(out); o.start(at); o.stop(at + dur + 0.02); at += dur;
    };
    const noise = (dur, vol = 0.3, swell = false) => {
      const n = a.createBufferSource(), g = a.createGain(); n.buffer = noiseBuf;
      if (swell) { g.gain.setValueAtTime(0.0001, at); g.gain.linearRampToValueAtTime(vol, at + dur / 2); g.gain.linearRampToValueAtTime(0.0001, at + dur); }
      else { g.gain.setValueAtTime(vol, at); g.gain.exponentialRampToValueAtTime(0.0001, at + dur); }
      n.connect(g).connect(out); n.start(at, Math.random() * 0.5); n.stop(at + dur + 0.02); at += dur;
    };
    const rest = (dur) => { at += dur; };
    switch (name) {
      case "boop": tone(520, 820, 0.12); break;
      case "pop": tone(900, 1400, 0.06, 0.3); break;
      case "munch": for (let i = 0; i < 3; i++) { noise(0.05, 0.45); rest(0.06); } break;
      case "whoosh": noise(0.28, 0.35, true); break;
      case "thud": tone(150, 60, 0.14, 0.5); break;
      case "coin": tone(988, 988, 0.07, 0.25, "square", false); tone(1319, 1319, 0.2, 0.25, "square"); break;
      case "crack": noise(0.03, 0.6); rest(0.05); noise(0.04, 0.6); break;
      case "fanfare": for (const f of [523, 659, 784]) tone(f, f, 0.09, 0.3, "tri", false); tone(1047, 1047, 0.3, 0.3, "tri"); break;
      case "zap": tone(1600, 400, 0.15, 0.25, "square"); break;
      case "boing": {
        const o = a.createOscillator(), g = a.createGain(), lfo = a.createOscillator(), lg = a.createGain();
        o.frequency.setValueAtTime(260, at); o.frequency.linearRampToValueAtTime(460, at + 0.4);
        lfo.frequency.value = 6.4; lg.gain.value = 60; lfo.connect(lg).connect(o.frequency);
        g.gain.setValueAtTime(0.4, at); g.gain.linearRampToValueAtTime(0.0001, at + 0.4);
        o.connect(g).connect(out); o.start(at); lfo.start(at); o.stop(at + 0.42); lfo.stop(at + 0.42); break;
      }
    }
  }
  function setSound(on, quiet = false) {
    save.sound = on; if (!quiet) persist(true);
    const b = $("soundBtn"); b.innerHTML = `<img class="px" src="icons/px/${on ? "sound" : "mute"}.png" alt="">`; b.setAttribute("aria-label", on ? "Sound on" : "Sound off");
    if (on && !quiet) sfx("boop");
  }

  const awLevel = (b) => Math.max(+((save.awakenLevel || {})[b]) || 0, save.awakened.includes(b) ? 1 : 0);
  // ⭐ creator perks: the secret creator code is remembered on this device (never in the save, so save codes don't pass it on)
  const CREATOR = new Set(D.groups.creator || []);
  const isCreator = () => { try { return localStorage.getItem("blipville-creator") === (D.creator || {}).hash; } catch (e) { return false; } };
  const isMod = () => { try { return (D.modHashes || []).includes(localStorage.getItem("blipville-mod")); } catch (e) { return false; } };
  const MODK = new Set(D.modKinds || []);
  const modCode = () => { try { return localStorage.getItem("blipville-mod"); } catch (e) { return null; } };
  const codeOwners = (k) => Object.keys(D.modCodeKinds || {}).filter((h) => D.modCodeKinds[h].includes(k));   // 💎 one moderator code's own Blips
  const isUnlocked = (k) => (save.merchKinds || []).includes(k) || (save.eventKinds || []).includes(k) ? true : (D.groups.eventKinds || []).includes(k) ? false : DREAMS.has(k) ? save.badDreams.includes(k) : EGYPT.has(k) ? save.gods.includes(k) : codeOwners(k).length ? codeOwners(k).includes(modCode()) : MODK.has(k) ? isCreator() || isMod() : CREATOR.has(k) ? isCreator() : AWAKEN_BASE[k] ? awLevel(AWAKEN_BASE[k]) >= awStage(k) && isUnlocked(AWAKEN_BASE[k]) : GHOST.has(k) ? save.ghosts.includes(k) : LEG.has(k) ? save.legends.includes(k) : WORLD_OF[k] ? save.worlds.includes(WORLD_OF[k]) : GIFTS.has(k) ? save.gifts.includes(k) : KAIJU.has(k) ? save.kaiju.includes(k) : CRYPT.has(k) ? save.cryptids.includes(k) : (RARE.has(k) ? save.hatched.includes(k) : NIGHT.has(k) ? D.unlocks[k] <= save.nightsWon || (save.robosFound || []).includes(k) : true);

  // ------------------------------------------------------------------ canvas & layout
  const cv = $("world"), ctx = cv.getContext("2d");
  let W = 0, H = 0, S = 5, GROUND = 0, DPR = 1;
  function layout() {
    DPR = Math.min(window.devicePixelRatio || 1, 3);
    W = view.innerWidth; H = view.innerHeight;
    cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR);
    S = clamp(Math.round(Math.min(W / 78, H / 60)), 3, 8);   // phones ≈5, laptops ≈8, the pop-out window ≈5
    const bar = $("bar").getBoundingClientRect();
    GROUND = Math.round(H - (bar.height || 70) - 18);
    for (const p of pets) p.x = clamp(p.x, 8 * S, W - 8 * S);
  }
  window.addEventListener("resize", layout);

  // ------------------------------------------------------------------ pets
  const pets = [];
  let cookies = [];
  let pointer = { x: 0, y: 0 };
  let greeted = {};
  const now = () => performance.now() / 1000;
  const FONT = getComputedStyle(document.body).fontFamily;

  function makePet(kind, color, name, x) {
    const k = KINDS[kind];
    const p = {
      kind, color: color ?? k.default ?? 0, name: name || pick(D.names), x: x ?? rnd(60, W - 60), y: rnd(140, 260), vx: 0, vy: 0,
      state: "fall", until: 0, target: null, facing: 1, energy: 100, hunger: 10, face: "normal", faceUntil: 0,
      bubble: null, blinkUntil: 0, nextBlink: now() + rnd(1, 4), lastPetReward: -99, nextShift: now() + rnd(6, 12),
      playing: false, napBuddy: false, lastPlay: -99, bond: 0,
      squashUntil: 0, particles: [],
    };
    return p;
  }
  function addPet(kind, opts = {}) {
    if (pets.length >= maxPets()) { toast(`Town's full! (${maxPets()} Blips max) Send one away first.`); return null; }
    const used = new Set(pets.map((p) => p.name));
    const name = opts.name || pick(D.names.filter((n) => !used.has(n))) || pick(D.names);
    const p = makePet(kind, opts.color, name, opts.x);
    pets.push(p);
    if (!opts.quiet) say(p, `hi! i'm ${name}`, 2.5);
    persist();
    return p;
  }
  const TYPE_CPS = D.typeCps || 32;              // speech bubbles type themselves out, and the Blip "talks" (see voiceBlip)
  const say = (p, text, secs = 3) => { const t = now(); p.bubble = { text, t0: t, voiced: 0, until: Math.max(t + secs, t + text.length / TYPE_CPS + 1.2) }; };
  const typed = (b, t) => Math.min(b.text.length, 1 + Math.floor((t - b.t0) * TYPE_CPS));
  const setFace = (p, face, secs) => { p.face = face; p.faceUntil = now() + secs; };
  const setState = (p, st, secs = 0) => { p.state = st; p.until = now() + secs; };
  const voice = (p, key, fallback) => { const own = (KINDS[p.kind] || {})[key]; return own && own.length ? pick(own) : fallback; };   // 🗣️ a Blip's own line
  const guardHours = () => { const h = new Date().getHours(); return h >= 19 || h < 7; };
  const linesFor = (p) => plushNow(p.kind) ? KINDS[p.kind].plush.lines : (KINDS[p.kind].night_lines && guardHours()) ? KINDS[p.kind].night_lines.concat(KINDS[p.kind].night_lines, KINDS[p.kind].lines) : KINDS[p.kind].pet_lines ? KINDS[p.kind].lines : D.lines.idle.concat(KINDS[p.kind].lines, KINDS[p.kind].lines, (D.seasonLines || {})[season()] || []);
  function burst(p, kind, n) {
    for (let i = 0; i < n; i++) p.particles.push({ kind, x: rnd(-26, 26) * S / 4, y: 13 * S + rnd(-6, 6), vx: rnd(-20, 20), vy: rnd(-70, -40), life: rnd(1, 1.6), born: now() });
  }
  function reward(p, n) {
    save.hearts += n; persist(); updateHearts(true);
    if (p) p.particles.push({ kind: "plus", text: `+${n} 💖`, x: 30 * S / 4, y: 13 * S + 4, vx: 0, vy: -26, life: 1.6, born: now() });
  }

  // friendship 💞 (the same levels as the desktop app)
  const BOND = D.bond || { levels: [0, 10, 30, 70, 150], titles: ["New friend", "Pal", "Buddy", "Best friend", "Soulmate"], gain: {} };
  const bondLevel = (pts) => BOND.levels.filter((n) => pts >= n).length;
  function bondUp(p, how) {
    const before = bondLevel(p.bond || 0);
    p.bond = (p.bond || 0) + (BOND.gain[how] || 1);
    const lv = bondLevel(p.bond);
    if (lv > before) {
      reward(p, 5 * lv); sfx("fanfare"); vibrate([20, 30, 20]);
      say(p, lv < 5 ? `💞 we're ${BOND.titles[lv - 1]}s now!` : "💞 SOULMATES! i'll never leave your side!", 4);
      setFace(p, "happy", 2.5); burst(p, "heart", 10); bump("bond_ups");
    }
  }
  function petIt(p) {
    if (p.state === "sleep") { wake(p); return; }
    sfx("boop"); bump("pets");
    const t = now();
    if (t - p.lastPetReward > 6) {
      p.lastPetReward = t; reward(p, 1); bondUp(p, "pet"); eventPoint(p, 1); questTick("pet_any");
      if (EVENT.kinds.includes(p.kind)) questTick("pet_spiky");
    }
    if (p.kind === "Puppet Master" || p.kind === "Bad Dream Puppet Master") {     // 🎭 5 quick taps… if you dare
      p.pmTaps = (p.pmTaps || []).filter((x) => t - x < 2.5).concat(t);
      if (p.pmTaps.length >= 5) { p.pmTaps = []; badDreamRewrite(p); return; }
    }
    say(p, voice(p, "pet_lines", pick(D.lines.pet)), 2.5); setFace(p, "happy", 1.5); burst(p, "heart", 4);
    if (KINDS[p.kind].blush && Math.random() < 0.4) p.blushUntil = now() + 1.5;      // a head pat can be a little much
    if (p.state !== "fall" && p.state !== "held") { p.vy = 260; p.vx = 0; setState(p, "fall"); }
    vibrate(10);
  }
  function feed(p) {
    if (p.state === "sleep") wake(p);
    const cx = clamp(p.x + pick([-1, 1]) * rnd(50, 90), 20, W - 20);
    cookies = cookies.filter((c) => c.owner !== p || p.eating === c);   // 🍪 one waiting cookie per Blip: a new one replaces it
    cookies.push({ x: cx, y: 260, vy: 0, landed: false, owner: p, born: now() }); bump("cookies");
    tidyCookies();
    say(p, voice(p, "feed_lines", "ooh! a cookie!"), 2.5); setFace(p, "surprised", 1);
  }
  function nap(p) {
    if (p.state === "sleep") { wake(p); return; }
    if (p.state !== "held" && p.state !== "fall") { setState(p, "sleep", 20); say(p, voice(p, "nap_lines", "good night..."), 2); }
  }
  function wake(p) { setState(p, "idle", 1.5); say(p, voice(p, "wake_lines", pick(D.lines.wake)), 2.5); setFace(p, "surprised", 0.8); }

  function lift(p, t) {
    const move = KINDS[p.kind].move, moving = p.state === "walk", k = S / 4;
    if (move === "float") return p.state === "sleep" ? 2 * k : (9 + 4 * Math.sin(t * 2.5)) * k;
    if (move === "hop" && moving) return Math.abs(Math.sin(t * 7)) * 12 * k;
    if (move === "flutter" && moving) return (8 + 3 * Math.sin(t * 12)) * k;
    return 0;
  }

  function decide(p, t) {
    if (plushNow(p.kind)) { if (Math.random() < 0.1) say(p, pick(linesFor(p)), 2.5); setState(p, "idle", rnd(4, 9)); return; }   // 🧸 it just sits there… mostly
    const hour = new Date().getHours();
    if (p.energy < 25 || ((hour >= 23 || hour < 6) && Math.random() < 0.15)) { say(p, voice(p, "nap_lines", "*yawn* nap time..."), 2.5); setState(p, "sleep", 20); return; }
    if (p.hunger > 70 && Math.random() < 0.35) say(p, pick(D.lines.hungry), 3);
    const r = Math.random();
    if (r < 0.45) { p.target = rnd(30, W - 30); setState(p, "walk", 12); }
    else if (r < 0.62) { say(p, pick(linesFor(p)), 3); setState(p, "idle", rnd(2, 4)); }
    else setState(p, "idle", rnd(2, 5));
  }

  function dreamBurst(p, plush) {              // 🧸 midnight: the plushie bursts out as its Bad Dream (and flops back at 6 AM)
    if (plush) { say(p, "*flop* …just a plushie again", 2.5); return; }
    say(p, pick(["*RRRIIIP!* 🌙", "*stitches pop* it's midnight…", "*bursts out of the plush*"]), 3); setFace(p, "surprised", 1.2); sfx("boing");
    for (let i = 0; i < 14; i++) p.particles.push({ kind: "stuffing", x: rnd(-20, 20) * S / 4, y: rnd(4, 9) * S, vx: rnd(-90, 90), vy: rnd(-220, -80), life: rnd(0.8, 1.4), born: now() });
  }
  function sparkle(p, n = 1) {
    for (let i = 0; i < n; i++) p.particles.push({ kind: "spark", x: rnd(-34, 34) * S / 4, y: rnd(4, 14 * S), vx: 0, vy: -12, life: rnd(0.8, 1.5),
                                                  born: now(), color: pick(["#ffffff", "#fff27a", "#ffd23a", "#a8d8ff"]) });
  }
  function update(p, t, dt) {
    if (AWAKEN_BASE[p.kind] && Math.random() < 0.05) sparkle(p);        // awakened Blips sparkle
    const k = KINDS[p.kind];
    if (t > p.nextBlink) { p.blinkUntil = t + 0.15; p.nextBlink = t + rnd(2, 6); }
    if (k.plush) { const m = plushNow(p.kind); if (p.plushMode !== undefined && p.plushMode !== m) dreamBurst(p, m); p.plushMode = m; }
    if (p.state !== "sleep") p.energy = Math.max(0, p.energy - dt * 0.12);
    p.hunger = Math.min(100, p.hunger + dt * 0.08);
    if (p.playing) return;                           // a game of catch / tag is moving it
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
            if (p.vy < -900) { say(p, pick(D.lines.land), 2); sfx("thud"); }
            p.vy = -p.vy * 0.35; p.vx *= 0.7; p.squashUntil = t + 0.15;
          } else { p.vy = 0; p.vx = 0; p.squashUntil = t + 0.2; setState(p, "idle", rnd(0.6, 1.5)); }
        }
        return;
      }
      case "sleep":
        p.energy = Math.min(100, p.energy + dt * 2);
        if (Math.random() < dt * 0.8) p.particles.push({ kind: "z", x: 18 * S / 4, y: 13 * S, vx: 14, vy: -22, life: 2.5, born: t });
        if (p.energy >= 100 && t > p.until) { wake(p); reward(p, 2); bondUp(p, "nap"); questTick("naps"); }
        return;
      case "eat":
        if (t > p.until) {
          const hungry = p.hunger, gain = hungry > 60 ? 5 : hungry >= 25 ? 2 : 0;   // a full Blip still eats, but gives nothing
          if (gain) { reward(p, gain); bondUp(p, "feed"); eventPoint(p, hungry > 60 ? 3 : 1); questTick("feed_hungry"); }
          p.hunger = 0; p.energy = Math.min(100, p.energy + 15);
          cookies = cookies.filter((c) => c !== p.eating); p.eating = null;
          say(p, gain ? pick(D.lines.eat) : pick(["i'm stuffed!", "*too full to move*", "maybe later…"]), 2.5); setFace(p, "happy", 2); burst(p, "heart", 5); setState(p, "idle", 2);
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
        if (ck && Math.abs(ck.x - p.x) < 30) { p.eating = ck; setState(p, "eat", 1.8); setFace(p, "munch", 1.8); sfx("munch"); }
        else setState(p, "idle", rnd(1, 3));
      } else p.x += speed * dt * p.facing;
    } else if (p.state === "idle" && t > p.until) decide(p, t);
  }

  // ------------------------------------------------------------------ playing together: catch, tag, nap piles
  let plays = [];
  const BALL = [".ooo.", "owwro", "owrro", "orrwo", ".ooo."];
  const headPos = (p) => [p.x, GROUND - p.y - 13 * S + 6];
  function endPlay(play, t, happy = true) {
    if (happy) { questTick("plays"); play.pets.forEach((q) => pets.includes(q) && bondUp(q, "play")); }
    for (const p of play.pets) {
      p.playing = false; p.lastPlay = t;
      if (happy && !["held", "fall", "sleep"].includes(p.state)) { setState(p, "idle", rnd(1.5, 3)); setFace(p, "happy", 1.5); burst(p, "heart", 2); }
    }
    plays = plays.filter((x) => x !== play);
  }
  function playStep(t, dt) {
    const free = pets.filter((p) => !p.playing && p.state === "idle" && t - p.lastPlay > 40);
    outer: for (let i = 0; i < free.length; i++) for (let j = i + 1; j < free.length; j++) {
      const a = free[i], b = free[j], d = Math.abs(a.x - b.x);
      if (d > 12 * S && d < 40 * S && Math.random() < dt * 0.04) {
        a.playing = b.playing = true;
        plays.push({ type: "ball", pets: [a, b], from: a, to: b, t0: t, throws: 0, n: 4 + Math.floor(Math.random() * 4) });
        say(a, pick(["catch!", `heads up, ${b.name}!`, "wanna play?"]), 2); break outer;
      }
      if (d < 64 * S && Math.random() < dt * 0.015) {
        a.playing = b.playing = true;
        plays.push({ type: "chase", pets: [a, b], runner: a, chaser: b, until: t + 7, swapped: false });
        say(a, pick(["can't catch me!", "tag, you're it!"]), 2); say(b, "hey! get back here!", 2); break outer;
      }
    }
    for (const sl of pets.filter((p) => p.state === "sleep")) for (const p of pets) {
      if (p !== sl && !p.playing && !p.napBuddy && p.state === "idle" && p.energy < 60 && Math.random() < dt * 0.15) {
        p.napBuddy = true; p.target = clamp(sl.x + pick([-1, 1]) * 14 * S, 8 * S, W - 8 * S); setState(p, "walk", 10); say(p, "*yawn* me too...", 2);
      }
    }
    for (const p of pets) if (p.napBuddy && p.state === "idle") { p.napBuddy = false; setState(p, "sleep", 20); say(p, "*snuggles*", 2); }
    for (const play of [...plays]) {
      const [a, b] = play.pets;
      if ([a, b].some((p) => !pets.includes(p) || ["held", "fall", "sleep"].includes(p.state) || !p.playing)) { endPlay(play, t, false); continue; }
      if (play.type === "ball") {
        for (const p of [a, b]) { p.state = "idle"; p.facing = (p === a ? b : a).x > p.x ? 1 : -1; }
        const u = Math.min(1, (t - play.t0) / 0.9), [x0, y0] = headPos(play.from), [x1, y1] = headPos(play.to);
        play.ball = [x0 + (x1 - x0) * u, y0 + (y1 - y0) * u - Math.sin(Math.PI * u) * 14 * S];
        if (u >= 1) {
          play.throws++; sfx("pop");
          if (Math.random() < 0.5) say(play.to, pick(["got it!", "nice!", "catch!", "woo!"]), 1.2);
          setFace(play.to, "happy", 0.6);
          [play.from, play.to, play.t0] = [play.to, play.from, t];
          if (play.throws >= play.n) { say(play.from, pick(["that was fun!", "good game!", "again later!"]), 2.5); endPlay(play, t); }
        }
      } else {
        const r = play.runner, c = play.chaser, sp = (p) => Math.sqrt(KINDS[p.kind].speed || 1);
        let away = r.x >= c.x ? 1 : -1;
        if ((away > 0 && r.x >= W - 9 * S) || (away < 0 && r.x <= 9 * S)) away = -away;   // cornered: dodge past
        r.x = clamp(r.x + 66 * (S / 4) * away * sp(r) * dt, 8 * S, W - 8 * S);
        const toward = r.x > c.x ? 1 : -1;
        c.x = clamp(c.x + 132 * (S / 4) * toward * sp(c) * dt, 8 * S, W - 8 * S);
        r.facing = away; c.facing = toward; r.state = c.state = "walk";
        if (Math.abs(r.x - c.x) < 6 * S) {
          say(c, "tag! you're it!", 1.8);
          if (!play.swapped) { [play.runner, play.chaser, play.swapped, play.until] = [c, r, true, t + 6]; c.x = clamp(c.x + (c.x > r.x ? 1 : -1) * 8 * S, 8 * S, W - 8 * S); }
          else endPlay(play, t);
        } else if (t > play.until) { say(r, "*pant pant* ok you win", 2); endPlay(play, t); }
      }
    }
  }
  function drawBalls() {
    const s = Math.max(2, Math.round(S * 0.7));
    for (const play of plays) {
      if (play.type !== "ball" || !play.ball) continue;
      const [bx, by] = play.ball;
      BALL.forEach((row, r) => [...row].forEach((ch, c) => {
        if (ch === ".") return; ctx.fillStyle = { w: "#ffffff", r: "#e8303a", o: "#3a2a3a" }[ch];
        ctx.fillRect(bx - 2.5 * s + c * s, by - 2.5 * s + r * s, s, s);
      }));
    }
  }

  function socialize(t) {
    const idle = pets.filter((p) => !p.playing);
    for (let i = 0; i < idle.length; i++) for (let j = i + 1; j < idle.length; j++) {
      const a = idle[i], b = idle[j];
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
  // sprite letter -> color: a capital letter is a darker shade of its small letter, * is a shine on the body color (1.0 redraws)
  const mixHex = (c1, c2, f) => "#" + [1, 3, 5].map((i) => Math.round(parseInt(c1.slice(i, i + 2), 16) * (1 - f) + parseInt(c2.slice(i, i + 2), 16) * f).toString(16).padStart(2, "0")).join("");
  const pxCache = new Map();
  function pxColor(pal, ch) {
    if (pal[ch]) return pal[ch];
    const lo = ch.toLowerCase(), key = ch + (pal[lo] || "") + (pal.b || "") + pal.o;
    let c = pxCache.get(key);
    if (!c) {
      c = ch === "*" ? mixHex(pal.b || pal.o, "#ffffff", 0.5) : ch !== lo && pal[lo] ? mixHex(pal[lo], "#000000", 0.25) : pal.o;
      pxCache.set(key, c);
    }
    return c;
  }
  const glitching = (t) => { const p = ((t % 5) + 5) % 5; return p < 0.12 || (p >= 0.24 && p < 0.34); };   // twice, briefly, every 5 s
  const isNight = () => { const h = new Date().getHours(); return h >= 22 || h < 6; };
  function grid(kind, colorIdx, opt = {}) {
    let k = KINDS[kind], cols = k.colors;
    if (k.plush && !badDreamHour()) { k = { ...k, body: k.plush.body, eyes: k.plush.eyes, xeye: false }; cols = k.plush.colors; }   // 🧸 plushie by day
    const t = opt.t ?? now(), st = opt.state || "idle";
    let pal = Object.assign({}, cols[colorIdx % cols.length], k.extra || {});
    if (opt.live && pal.glitch != null && glitching(t + (opt.phase || 0))) pal = Object.assign({}, cols[pal.glitch], k.extra || {});   // ⚡ flicker to an old look
    let body = pal.art || k.body;
    if (opt.live && pal.glitch_art && glitching(t)) body = pal.glitch_art;      // 📼 Classic: flicker back to the old drawing
    if (k.alt && ["walk", "fall", "held"].includes(st) && Math.floor(t * 10) % 2) body = k.alt;
    const g = Array.from({ length: 13 }, () => Array(16).fill(null));
    const lying = st === "sleep" || opt.squash, shift = lying ? 1 : 0;
    const bl = opt.blush && k.blush, bpal = bl ? Object.assign({}, pal, k.blush.pal) : pal;     // flustered: only the face flushes
    body.forEach((row, y) => [...row].forEach((ch, x) => { if (ch !== "." && y + shift < 13) g[y + shift][x] = pxColor(bl && y >= k.blush.rows[0] && y <= k.blush.rows[1] ? bpal : pal, ch); }));
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
      if (k.xeye) for (let i = 0; i < 4; i++) { px(3 + i, 4 + i, pal.x || pal.o); px(6 - i, 4 + i, pal.x || pal.o); }   // a stitched X where a button came off
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
  // accessory colors: a tint swaps an item's main color (0 = original); a 2nd slot lets a Blip wear two things
  const TINTS = D.accessoryTints || [["Original", null]];
  function tintedColors(hat, tint) {
    const col = (TINTS[tint || 0] || TINTS[0])[1];
    if (!col) return hat.colors;
    const main = Object.keys(hat.colors)[0];
    return { ...hat.colors, [main]: col };
  }
  const worn = (p) => [p.hat, p.hat2].filter((n) => n && HATS[n]).map((n) => [n, (p.tints || {})[n] || 0]);
  function wearItem(p, name) {
    if (name === p.hat || name === p.hat2) return;
    const two = !!save.slot2, same = [p.hat, p.hat2].find((n) => n && HATS[n] && HATS[n].slot === HATS[name].slot);
    if (same) { if (p.hat === same) p.hat = name; else p.hat2 = name; }
    else if (!two || !p.hat) { p.hat = name; if (!two) p.hat2 = null; }
    else if (!p.hat2) p.hat2 = name;
    else { p.hat = p.hat2; p.hat2 = name; }
  }
  function takeOff(p, name) { if (p.hat === name) { p.hat = p.hat2 || null; p.hat2 = null; } else if (p.hat2 === name) p.hat2 = null; }
  function hatCells(kind, name, shift = 0, tint = 0) {
    const k = KINDS[kind], hat = HATS[name], rows = hat.rows, w = rows[0].length, colors = tintedColors(hat, tint);
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
    rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch !== ".") out.push([top + r, left + c, colors[ch]]); }));
    return out;
  }
  function drawHat(c, kind, name, x, y, s, shift = 0, tint = 0) {
    let topRow = 0;
    if (!name || !HATS[name]) return 0;
    for (const [r, col, color] of hatCells(kind, name, shift, tint)) { c.fillStyle = color; c.fillRect(x + col * s, y + r * s, s, s); topRow = Math.min(topRow, r); }
    return topRow * s;
  }
  function dressedThumb(kind, color, hat, scale = 3, tint = 0) {
    const pad = 8, c = document.createElement("canvas"); c.width = 16 * scale; c.height = (13 + pad) * scale;
    const cx = c.getContext("2d"); drawGrid(cx, grid(kind, color, { t: 0 }), 0, pad * scale, scale); drawHat(cx, kind, hat, 0, pad * scale, scale, 0, tint);
    return c;
  }

  function drawGrid(c, g, x, y, s, soul = null, soulA = 1) {   // soul: colors drawn see-through (the Puppet Master's soul)
    const base = c.globalAlpha;
    for (let r = 0; r < g.length; r++) {
      let col = 0;
      while (col < 16) {
        const color = g[r][col];
        if (!color) { col++; continue; }
        let end = col;
        while (end + 1 < 16 && g[r][end + 1] === color) end++;
        c.globalAlpha = soul && soul.has(color) ? base * soulA : base;
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
  // ------------------------------------------------------------------ seasons & weather
  let seasonOverride = null;                       // for testing: blipvilleGo.setSeason("winter")
  const season = () => seasonOverride || currentSeason();
  let weather = [], lastWeather = 0;
  const BAT = ["x...x", "xx.xx", ".xxx."], BAT_FLAP = [".x.x.", "xxxxx", ".x.x."];
  const hereWorld = () => (save.world && save.worlds.includes(save.world) ? save.world : null);
  function weatherStep(t, night) {
    const dt = Math.min(0.05, t - (lastWeather || t)); lastWeather = t;
    const sz = Math.max(2, Math.round(S * 0.6)), scaleW = W / 400;
    const rates = hereWorld() ? WORLD_LOOK[hereWorld()].fx : ({ winter: [["snow", 10]], spring: [["petal", 4]], autumn: [["leaf", 3.5]],
                    spooky: [["leaf", 2], ["bat", 0.25]], summer: night ? [["firefly", 2.5]] : [] }[season()] || []);
    for (const [kind, rate] of rates) {
      if (Math.random() > rate * scaleW * dt) continue;
      if (kind === "bat") { const d = Math.random() < 0.5 ? 1 : -1; weather.push({ kind, x: d > 0 ? -20 : W + 20, y: rnd(30, GROUND * 0.5), vx: 70 * d, vy: 0, born: t, life: (W + 40) / 70 }); }
      else if (kind === "bubble") weather.push({ kind, x: rnd(0, W), y: GROUND + 4, vx: 0, vy: -rnd(25, 50), born: t, life: GROUND / 25, ph: rnd(0, 6.3), size: pick([1, 1.5, 2.5]) });
      else if (kind === "star") weather.push({ kind, x: rnd(0, W), y: rnd(10, GROUND - 30), vx: 0, vy: 0, born: t, life: rnd(1.5, 3), ph: rnd(0, 6.3), color: pick(["#ffffff", "#fff27a", "#a8d8ff"]) });
      else if (kind === "sprinkle") weather.push({ kind, x: rnd(0, W), y: -6, vx: 0, vy: rnd(30, 60), born: t, life: (GROUND + 10) / 30, ph: rnd(0, 6.3), tall: Math.random() < 0.5,
                                                  color: pick(["#ff5a8a", "#5ad8ff", "#ffd23a", "#8af05a", "#b88aff", "#ffffff"]) });
      else if (kind === "ash") weather.push({ kind, x: rnd(0, W), y: -6, vx: rnd(-6, 14), vy: rnd(15, 35), born: t, life: (GROUND + 10) / 15, ph: rnd(0, 6.3), color: pick(["#8a8090", "#5a5060", "#ff8a3a"]) });
      else if (kind === "firefly") weather.push({ kind, x: rnd(0, W), y: rnd(GROUND * 0.35, GROUND - 10), vx: rnd(-12, 12), vy: rnd(-10, 4), born: t, life: 4 });
      else weather.push({ kind, x: rnd(0, W), y: -6, vx: rnd(-10, 10), vy: rnd(28, 60), born: t, life: (GROUND + 10) / 28, ph: rnd(0, 6.3),
                          color: pick(["#e8702a", "#c8402a", "#ffb83a"]) });
    }
    weather = weather.filter((w) => t - w.born < w.life && w.y < GROUND + 6);
    for (const w of weather) {
      w.x += w.vx * dt; w.y += w.vy * dt; const a = t - w.born;
      if (w.kind === "snow") { ctx.fillStyle = "#f4f8ff"; ctx.fillRect(w.x, w.y, sz, sz); }
      else if (w.kind === "bubble") { const x = w.x + Math.sin(a * 3 + w.ph) * 5, b = sz * w.size; ctx.strokeStyle = "#cdefff"; ctx.lineWidth = 1.5; ctx.strokeRect(x, w.y, b, b); ctx.fillStyle = "#ffffff"; ctx.fillRect(x + 1.5, w.y + 1.5, 1.5, 1.5); }
      else if (w.kind === "star") { if (Math.sin(a * 6 + w.ph) > -0.2) { ctx.fillStyle = w.color; ctx.fillRect(w.x, w.y - sz, sz, sz * 3); ctx.fillRect(w.x - sz, w.y, sz * 3, sz); } }
      else if (w.kind === "sprinkle") { ctx.fillStyle = w.color; const x = w.x + Math.sin(a * 2 + w.ph) * 3; ctx.fillRect(x, w.y, w.tall ? sz : sz * 2, w.tall ? sz * 2 : sz); }
      else if (w.kind === "ash") { ctx.fillStyle = w.color; ctx.fillRect(w.x + Math.sin(a * 2 + w.ph) * 5, w.y, sz, sz); }
      else if (w.kind === "leaf" || w.kind === "petal") {
        const x = w.x + Math.sin(a * 3 + w.ph) * 8;
        ctx.fillStyle = w.kind === "leaf" ? w.color : "#ffb0d8";
        ctx.fillRect(x, w.y, w.kind === "leaf" ? sz * 2 : sz * 1.5, w.kind === "leaf" ? sz * 1.4 : sz);
      } else if (w.kind === "firefly") {
        ctx.globalAlpha = 0.4 + 0.6 * Math.max(0, Math.sin(a * 5)); ctx.fillStyle = "#fff08a"; ctx.fillRect(w.x, w.y, sz, sz); ctx.globalAlpha = 1;
      } else if (w.kind === "bat") {
        const shape = Math.floor(a * 8) % 2 ? BAT : BAT_FLAP, bs = Math.max(3, Math.round(S * 0.7));
        ctx.fillStyle = night ? "#8a6ac8" : "#3a2a5a";
        shape.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === "x") ctx.fillRect(w.x + c * bs, w.y + r * bs + Math.sin(a * 6) * 6, bs, bs); }));
      }
    }
  }

  function sky(t) {
    const h = new Date().getHours() + new Date().getMinutes() / 60;
    const night = h >= 20 || h < 6, dusk = (h >= 17 && h < 20) || (h >= 6 && h < 8);
    const wl = hereWorld() && WORLD_LOOK[hereWorld()];
    if (wl) { worldSky(t, wl); return; }
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
    const sea = season();
    const LAND = {   // [hills, ground, ground edge] by day / by night
      summer: [["#7fcf7a", "#5aa85a", "#4a8a4a"], ["#23304a", "#1b2238", "#141a2c"]],
      spring: [["#8ae07a", "#62b85a", "#4f9a4a"], ["#23304a", "#1b2238", "#141a2c"]],
      autumn: [["#d8904a", "#a8703a", "#8a5a2a"], ["#3a2a2a", "#2a1e1e", "#1e1414"]],
      spooky: [["#6a4a8a", "#3a2a4a", "#2a1e36"], ["#2a1a3a", "#1a1028", "#120a1e"]],
      winter: [["#eef4ff", "#dfe8f8", "#c8d4ea"], ["#8a9ab8", "#6a7a98", "#5a6a88"]],
    }[sea][night ? 1 : 0];
    ctx.fillStyle = LAND[0];
    for (let x = 0; x < W; x += 6) { const hh = 26 + 14 * Math.sin(x / 70) + 8 * Math.sin(x / 23); ctx.fillRect(x, GROUND - hh, 6, hh); }
    ctx.fillStyle = LAND[1]; ctx.fillRect(0, GROUND, W, H - GROUND);
    ctx.fillStyle = LAND[2]; ctx.fillRect(0, GROUND, W, 6);
    if (sea === "spring" && !night) {                // little flowers in the grass
      for (let x = 13; x < W; x += 47) { ctx.fillStyle = ["#ffb0d8", "#ffd23a", "#ffffff"][x % 3]; ctx.fillRect(x, GROUND + 14 + (x % 17), 4, 4); }
    }
    weatherStep(t, night);
  }
  function worldSky(t, wl) {
    const gr = ctx.createLinearGradient(0, 0, 0, GROUND);
    gr.addColorStop(0, wl.sky[0]); gr.addColorStop(1, wl.sky[1]);
    ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
    if (wl.planet) {                                         // space: a ringed planet and a little moon
      ctx.fillStyle = "#b88aff"; ctx.beginPath(); ctx.arc(W * 0.78, GROUND * 0.24, 30, 0, 7); ctx.fill();
      ctx.fillStyle = "#ffd8f0"; ctx.fillRect(W * 0.78 - 48, GROUND * 0.24 - 3, 96, 6);
      ctx.fillStyle = "#e8e8f0"; ctx.beginPath(); ctx.arc(W * 0.2, GROUND * 0.16, 12, 0, 7); ctx.fill();
      for (const [sx, sy, tw] of stars) { ctx.globalAlpha = 0.5 + 0.5 * Math.sin(t * 2 + tw * 9); ctx.fillStyle = "#fff6d8"; ctx.fillRect(sx * W, sy * GROUND, 3, 3); }
      ctx.globalAlpha = 1;
    } else if (wl.sun) { ctx.fillStyle = wl.sun; ctx.beginPath(); ctx.arc(W * 0.8, GROUND * 0.18, 26, 0, 7); ctx.fill(); }
    if (!wl.sun && !wl.planet) {                             // ocean: light rays from the surface
      ctx.fillStyle = "rgba(255,255,255,.08)";
      for (let i = 0; i < 4; i++) { const x = ((i * 0.27 + t * 0.01) % 1) * W; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x + 40, 0); ctx.lineTo(x + 120, GROUND); ctx.lineTo(x + 60, GROUND); ctx.fill(); }
    }
    if (wl.volcano) {                                        // dino: a smoking volcano
      ctx.fillStyle = "#5a3a2a"; ctx.beginPath(); ctx.moveTo(W * 0.62, GROUND); ctx.lineTo(W * 0.74, GROUND * 0.45); ctx.lineTo(W * 0.8, GROUND * 0.45); ctx.lineTo(W * 0.94, GROUND); ctx.fill();
      ctx.fillStyle = "#ff6a2a"; ctx.fillRect(W * 0.74, GROUND * 0.45, W * 0.06, 6);
      ctx.fillStyle = "rgba(90,80,90,.6)"; for (let i = 0; i < 3; i++) { const yy = GROUND * 0.4 - ((t * 12 + i * 30) % 90); ctx.fillRect(W * 0.75 + Math.sin(t + i) * 10, yy, 24, 12); }
    }
    ctx.fillStyle = wl.land[0];
    for (let x = 0; x < W; x += 6) { const hh = 26 + 14 * Math.sin(x / 70) + 8 * Math.sin(x / 23); ctx.fillRect(x, GROUND - hh, 6, hh); }
    ctx.fillStyle = wl.land[1]; ctx.fillRect(0, GROUND, W, H - GROUND);
    ctx.fillStyle = wl.land[2]; ctx.fillRect(0, GROUND, W, 6);
    weatherStep(t, false);
  }
  function pixCloud(x, y) { for (const [dx, dy, w] of [[0, 8, 70], [12, 0, 40], [20, 14, 60]]) ctx.fillRect(Math.round(x + dx), Math.round(y + dy), w, 12); }

  function bubble(text, cx, bottom) {
    ctx.font = "700 14px " + FONT;
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
    ctx.font = "700 11px " + FONT;
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
    if (KINDS[p.kind].ghost && !KINDS[p.kind].colors[p.color % KINDS[p.kind].colors.length].solid) ctx.globalAlpha = 0.8;   // ghosts stay a little see-through (unless the color is solid)
    const K = KINDS[p.kind], soul = K.soul ? new Set([...K.soul].map((ch) => K.colors[p.color % K.colors.length][ch]).filter(Boolean)) : null;
    drawGrid(ctx, grid(p.kind, p.color, { t, live: true, blush: t < (p.blushUntil || 0), state: p.state, face, blink: t < p.blinkUntil, look, lift: l / (S / 4), squash: t < p.squashUntil }), left, top, S,
             soul, soul ? ghostAlpha(t, p.x * 0.01) * 0.75 : 1);
    ctx.globalAlpha = 1;
    const shiftH = (p.state === "sleep" || t < p.squashUntil) ? 1 : 0;
    const hatTop = Math.min(0, ...worn(p).map(([n, tint]) => drawHat(ctx, p.kind, n, left, top, S, shiftH, tint)));
    // particles
    p.particles = p.particles.filter((q) => t - q.born < q.life);
    for (const q of p.particles) {
      const a = t - q.born, qx = p.x + q.x + q.vx * a, qy = GROUND - p.y - q.y + q.vy * a + (q.kind === "crumb" || q.kind === "stuffing" ? 300 * a * a : 0);
      if (q.kind === "heart") drawMask(HEART, qx, qy, 3, "#ff4f7b");
      else if (q.kind === "z") drawMask(ZED, qx, qy, 2 + Math.floor(a), "#bcd2ff");
      else if (q.kind === "crumb") { ctx.fillStyle = "#c98a4b"; ctx.fillRect(qx, qy, 3, 3); }
      else if (q.kind === "stuffing") { ctx.fillStyle = "#f4ece4"; ctx.fillRect(qx, qy, 4, 4); }
      else if (q.kind === "spark") { ctx.fillStyle = q.color; ctx.fillRect(qx, qy - 2, 2, 6); ctx.fillRect(qx - 2, qy, 6, 2); }
      else if (q.kind === "plus") {
        ctx.font = "800 12px " + FONT;
        const w = ctx.measureText(q.text).width + 10;
        ctx.fillStyle = "#e8457a"; ctx.beginPath(); ctx.roundRect(qx - w / 2, qy - 9, w, 18, 8); ctx.fill();
        ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(q.text, qx, qy);
      }
    }
    let above = top + hatTop - 4;
    const lv = bondLevel(p.bond || 0);
    above -= nameTag((lv >= 5 ? "💛 " : lv >= 4 ? "♥ " : "") + p.name, p.x, above);
    if (p.bubble && t < p.bubble.until) {
      const n = typed(p.bubble, t);
      if (n > p.bubble.voiced) { const fresh = p.bubble.text.slice(p.bubble.voiced, n); p.bubble.voiced = n; if (/[a-z0-9]/i.test(fresh)) voiceBlip(p.kind); }
      bubble(p.bubble.text.slice(0, n), p.x, above);
    }
  }
  function drawMask(mask, x, y, s, color) {
    ctx.fillStyle = color;
    mask.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === "x") ctx.fillRect(x + c * s, y + r * s, s, s); }));
  }
  // 🍪 cookies never pile up: they go away with their Blip, uneaten ones vanish after a minute, and there are never
  // more than COOKIE_MAX (oldest go first). Runs every frame, separately from drawing.
  const COOKIE_MAX = 24, COOKIE_LIFE = 60;
  function tidyCookies() {
    const t = now();
    cookies = cookies.filter((c) => pets.includes(c.owner) && (c.owner.eating === c || t - (c.born || t) < COOKIE_LIFE));
    if (cookies.length > COOKIE_MAX) cookies = cookies.filter((c) => c.owner.eating === c).concat(cookies.filter((c) => c.owner.eating !== c).slice(-COOKIE_MAX));
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
  let last = now(), loopId = 0;
  function startLoop() { const id = ++loopId; view.requestAnimationFrame(() => frame(id)); }
  // ------------------------------------------------------------------ cryptid sightings
  // Every few minutes a cryptid shows up in town, each its own way (Mothman lands on a lamp post, Nessie
  // pops out of the water…). Tap it before it gets away to befriend it! Scenes come from blip.pyw.
  let sighting = null, nextSighting = now() + rnd(2, 5) * 60;
  let nextKaiju = now() + rnd(15, 30) * 60;
  let nextLegend = now() + rnd(1, 2) * 60;
  let nextGhost = now() + rnd(1, 3) * 60, candleUntil = 0, nextRobo = 0;     // ghosts: 7 PM to 7 AM, or after a Spirit Candle
  const ghostHours = () => { const h = new Date().getHours(); return h >= 19 || h < 7; };
  const ghostAlpha = (t, phase) => 0.12 + 0.88 * Math.min(1, Math.max(0, Math.sin(t * 1.7 + phase) + 0.35));
  const solid = () => !sighting || !GHOST.has(sighting.kind) || ghostAlpha(now() - sighting.t0, sighting.phase) >= 0.6;              // legends: only while you're visiting their world            // kaiju: much rarer, bigger, and they take 3 taps
  const QMARK = [".xxx.", "x...x", "...x.", "..x..", ".....", "..x.."];
  const [SW, SH] = D.sceneSize, SHADOW = "#16121f", GLOW = "#ffe66a";
  function scenePos(keys, t) {
    if (t <= keys[0][0]) return [keys[0][1], keys[0][2]];
    for (let i = 0; i + 1 < keys.length; i++) {
      const [t0, x0, y0] = keys[i], [t1, x1, y1] = keys[i + 1];
      if (t <= t1) { const f = t1 > t0 ? (t - t0) / (t1 - t0) : 1; return [x0 + (x1 - x0) * f, y0 + (y1 - y0) * f]; }
    }
    const k = keys[keys.length - 1]; return [k[1], k[2]];
  }
  const sceneU = () => Math.min(S, W / SW);
  const sceneLeft = () => (W - SW * sceneU()) / 2;
  function sceneMask(rows, colors, cx, by, t, mirror) {
    const u = sceneU(), L = sceneLeft(), w = rows[0].length, h = rows.length, x0 = Math.round(cx - w / 2);
    rows.forEach((row, r) => {
      if (mirror) row = [...row].reverse().join("");
      const y = GROUND - (by + h - r) * u;
      for (let x = 0; x < w; x++) {
        const ch = row[x]; if (ch === ".") continue;
        let x2 = x; while (x2 + 1 < w && row[x2 + 1] === ch) x2++;
        let col = colors[ch]; if (Array.isArray(col)) col = Math.floor(t * 7) % 5 === 0 ? col[1] : col[0];
        ctx.fillStyle = col; ctx.fillRect(L + (x0 + x) * u, y, (x2 - x + 1) * u + 0.5, u + 0.5);
        x = x2;
      }
    });
  }
  function startSighting(kind) {
    const sc = D.scenes[kind], flip = Math.random() < 0.5;
    sighting = { kind, sc, t0: now(), flip, facing: flip ? -1 : 1, clip: sc.clip ?? -99, s: sc.scale || 1, hits: 0, flash: 0, phase: rnd(0, 6.28),
                 keys: sc.keys.map(([t, x, y]) => [t, flip ? SW - x : x, y]),
                 props: sc.props.map(([n, x, y, layer]) => [n, flip ? SW - x : x, y, layer]) };
    sighting.pos = sighting.keys[0].slice(1);
    const witness = pets.find((p) => !["sleep", "held"].includes(p.state));
    if (witness) say(witness, sc.hint, 4);
    sfx(KAIJU.has(kind) ? "thud" : "whoosh"); if (KAIJU.has(kind)) vibrate([60, 60, 60]);
  }
  const sightingVisible = () => sighting && sighting.pos[1] + 12 * sighting.s >= sighting.clip;
  function sightingStep(t) {
    if (!sighting) {
      if (hereWorld() && t >= nextLegend) {
        nextLegend = t + rnd(2, 5) * 60;
        const leftL = (D.groups.legends || []).filter((k) => LEGEND_WORLD[k] === hereWorld() && !isUnlocked(k));
        if (leftL.length && $("nsSheet").hidden) { startSighting(pick(leftL)); return; }
      }
      if (t >= nextKaiju) {
        nextKaiju = t + rnd(30, 60) * 60;
        const leftK = (D.groups.kaiju || []).filter((k) => !isUnlocked(k));
        if (leftK.length && $("nsSheet").hidden) { startSighting(pick(leftK)); return; }
      }
      if (pets.some((p) => p.kind === D.roboPuppet) && t >= nextRobo) {   // 🎭 the Puppet Master lures robos into town
        nextRobo = t + rnd(8, 16) * 60;
        const leftR = (D.roboScenes || []).filter((k) => !isUnlocked(k));
        if (leftR.length && Math.random() < 0.6 && $("nsSheet").hidden) { startSighting(pick(leftR)); return; }
      }
      if ((ghostHours() || t < candleUntil) && t >= nextGhost) {
        nextGhost = t + (t < candleUntil ? rnd(1, 2) : rnd(4, 9)) * 60;
        const leftG = (D.groups.ghosts || []).filter((k) => !isUnlocked(k) && save.nightsWon >= ((D.ghostNights || {})[k] || 0));   // 🐇 some only after a Night Shift night
        if (leftG.length && $("nsSheet").hidden) { startSighting(pick(leftG)); return; }
      }
      if (t < nextSighting) return;
      const wait = rnd(4, 9) * 60; nextSighting = t + (isNight() ? wait / 2 : wait);
      const left = D.groups.cryptids.filter((k) => !isUnlocked(k));
      if (left.length && $("nsSheet").hidden) startSighting(pick(left));
      return;
    }
    const sg = sighting, st = t - sg.t0, k = KINDS[sg.kind];
    if (st > sg.keys[sg.keys.length - 1][0]) {
      const witness = pets.find((p) => !["sleep", "held"].includes(p.state));
      if (witness && GHOST.has(sg.kind)) say(witness, pick(["it faded away… 👻", "was that a ghost?!", "brrr, it got chilly", "boo… it's gone"]), 3);
      else if (witness && LEG.has(sg.kind)) say(witness, pick(["aww, it sparkled away…", "it went back into the world!", "so pretty! next time!"]), 3);
      else if (witness && KAIJU.has(sg.kind)) say(witness, pick(["it stomped away!!", "THAT WAS HUGE", "the whole town shook!", "next time we'll get it!"]), 3);
      else if (witness) say(witness, pick(["did you see that?!", "w-what was THAT?", "i think i saw something…", "*rubs eyes* huh?", "it got away!"]), 3);
      sighting = null; return;
    }
    let [x, y] = scenePos(sg.keys, st);
    const [nx] = scenePos(sg.keys, st + 0.1), moving = Math.abs(nx - x) > 0.05;
    if (moving) sg.facing = nx > x ? 1 : -1;
    if (k.move === "float") y += Math.sin(st * 2.5) * 1.2;
    else if ((k.move === "hop" || k.move === "flutter") && moving) y += Math.abs(Math.sin(st * 8)) * 2;
    sg.pos = [x, y];
    const u = sceneU(), L = sceneLeft();
    const props = (layer) => sg.props.forEach(([n, px, py, lay]) => {
      if (lay === layer) { const P = D.sceneProps[n]; sceneMask(P.rows, P.colors, px, py, st, sg.flip && n !== "rec"); }
    });
    props("back");
    if (sg.sc.mound && y < sg.clip - 10) { const P = D.sceneProps.mound; sceneMask(P.rows, P.colors, x + Math.sin(st * 9) * 0.6, 0, st, false); }
    const ghost = GHOST.has(sg.kind), legend = LEG.has(sg.kind) || ghost;    // legends and ghosts show up in full color
    const g = grid(sg.kind, 0, { t: legend ? t : 0, silhouette: !legend, state: "walk" });
    if (ghost) ctx.globalAlpha = ghostAlpha(st, sg.phase);             // ghosts fade in and out
    const glow = Math.floor(t * 2.5) % 10 !== 0;
    const s = sg.s, flash = t < sg.flash;
    g.forEach((row, r) => {
      if (y + (12 - r) * s < sg.clip) return;
      const cells = row.map((c, i) => (c ? (flash ? "#ffffff" : legend ? c : glow && r === k.eyes && [4, 5, 10, 11].includes(i) ? GLOW : SHADOW) : null));
      if (sg.facing === -1) cells.reverse();
      const top = GROUND - (y + (13 - r) * s) * u;
      cells.forEach((c, i) => { if (c) { ctx.fillStyle = c; ctx.fillRect(L + (x + (i - 8) * s) * u, top, s * u + 0.5, s * u + 0.5); } });
    });
    ctx.globalAlpha = 1;
    if (sg.sc.sparkle && (!moving || legend)) {
      ctx.fillStyle = "#fff27a";
      for (let i = 0; i < 3; i++) if (Math.floor(st * 6 + i * 2) % 3) {
        const sx = x + sg.facing * (8 + i * 2), sy = y + 5 + ((i * 3 + Math.floor(st * 4)) % 6);
        ctx.fillRect(L + sx * u, GROUND - sy * u, u, u);
      }
    }
    props("front");
    if (sightingVisible() && KAIJU.has(sg.kind)) {             // little bars: how many taps it still needs
      for (let i = 0; i < HITS; i++) {
        const bx = L + (x - 5 + i * 4) * u, by = GROUND - (y + 13 * s + 4) * u;
        ctx.fillStyle = "#16121f"; ctx.fillRect(bx - 1, by - 1, 3 * u + 2, 2 * u + 2);
        ctx.fillStyle = i < sg.hits ? "#ff5a7a" : "#ffffff"; ctx.fillRect(bx, by, 3 * u, 2 * u);
      }
    } else if (sightingVisible() && (!legend || (ghost && solid()))) drawMask(QMARK, L + x * u - 7, GROUND - (y + 22) * u, 3, "#ffffff");
  }
  function sightingAt(px, py) {
    if (!sightingVisible()) return false;
    const u = sceneU(), ux = (px - sceneLeft()) / u, uy = (GROUND - py) / u, [x, y] = sighting.pos;
    const s = sighting.s;
    return Math.abs(ux - x) <= 10 * s + 1 && uy >= Math.max(y, sighting.clip) - 3 && uy <= y + 16 * s + 1;
  }
  function befriend() {
    const kind = sighting.kind, x = sceneLeft() + sighting.pos[0] * sceneU();
    if (!solid()) {                                           // a faded ghost: your tap goes right through
      const w = pets.find((p) => !["sleep", "held"].includes(p.state));
      if (w && now() - (sighting.fadeHint || 0) > 3) { sighting.fadeHint = now(); say(w, pick(["it faded out! wait till it glows…", "your hand went right through!", "now you see it, now you don't…"]), 2.5); }
      return;
    }
    if (KAIJU.has(kind) && ++sighting.hits < HITS) {          // not yet! it flinches and keeps going
      sighting.flash = now() + 0.15; sfx("thud"); vibrate(25);
      const w = pets.find((p) => !["sleep", "held"].includes(p.state));
      if (w) say(w, pick(["again! tap it again!", "it's working!", "keep going!!", "almost!"]), 2);
      return;
    }
    sighting = null;
    if ((D.roboScenes || []).includes(kind)) (save.robosFound = save.robosFound || []).push(kind);   // 🎭 a wandering Night Shift robo
    else (KAIJU.has(kind) ? save.kaiju : LEG.has(kind) ? save.legends : GHOST.has(kind) ? save.ghosts : save.cryptids).push(kind); persist(true); sfx("fanfare"); vibrate([30, 40, 30]);
    const p = addPet(kind, { x: clamp(x, 10 * S, W - 10 * S), quiet: true });
    if (p) { say(p, `you spotted me! 📸 i'm a ${kind}!`, 5); setFace(p, "happy", 2); burst(p, "heart", 6); }
    else toast(`You befriended a ${kind}! 📸 It's waiting in your 📖 Zoo.`, 4);
  }

  function frame(id) {
    if (id !== loopId) return;
    const t = now(), dt = Math.min(0.05, t - last); last = t;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    ctx.imageSmoothingEnabled = false;
    sky(t);
    for (const p of pets) update(p, t, dt);
    tidyCookies();
    socialize(t);
    playStep(t, dt);
    drawCookies(t);
    for (const p of [...pets].sort((a, b) => (a === held ? 1 : 0) - (b === held ? 1 : 0))) drawPet(p, t);
    drawBalls();
    sightingStep(t);
    view.requestAnimationFrame(() => frame(id));
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
    if (sightingAt(e.clientX, e.clientY)) { befriend(); return; }
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
      held = press.p; held.playing = false; held.napBuddy = false; setState(held, "held"); say(held, pick(D.lines.held), 2.5); setFace(held, "surprised", 999);
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
      setFace(held, "surprised", 0.6); setState(held, "fall");
      if (Math.abs(held.vx) + Math.abs(held.vy) > 700) sfx("whoosh");
      held = null;
    } else if (!press.opened) petIt(press.p);
    press = null;
  };
  cv.addEventListener("pointerup", endPress);
  cv.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    const p = petAt(e.clientX, e.clientY);
    clearTimeout(holdTimer); press = null;
    if (p) openPetSheet(p);
  });
  cv.addEventListener("pointermove", (e) => { if (!press) cv.style.cursor = petAt(e.clientX, e.clientY) ? "pointer" : "default"; });
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
  // ------------------------------------------------------------------ trophies 🏆 (the list comes from blip.pyw)
  const stat = (n) => +(save.stats[n] || 0);
  function bump(n, by = 1) { save.stats[n] = stat(n) + by; }
  const anyU = (g) => () => (g || []).some(isUnlocked), allU = (g) => () => (g || []).every(isUnlocked);
  const TCHECK = {
    "first-pet": () => stat("pets") >= 1, "pets-100": () => stat("pets") >= 100, "cookies-25": () => stat("cookies") >= 25,
    "days-7": () => stat("days") >= 7, "full-town": () => pets.length >= maxPets(), "hats-5": () => save.hatsOwned.length >= 5,
    "egg-1": anyU(D.groups.rare), "egg-all": allU(D.groups.rare), "cryptid-1": anyU(D.groups.cryptids), "cryptid-all": allU(D.groups.cryptids),
    "kaiju-1": anyU(D.groups.kaiju), "kaiju-all": allU(D.groups.kaiju), "ghost-1": anyU(D.groups.ghosts), "ghost-all": allU(D.groups.ghosts), "dreams-all": allU([...DREAMS]),
    "world-1": () => WORLDS.some((w) => w.cost > 0 && save.worlds.includes(w.name)), "world-all": () => WORLDS.every((w) => !w.cost || save.worlds.includes(w.name)),
    "awaken-1": () => save.awakened.length >= 1, "arena-1": () => stat("arena_wins") >= 1,
    "arena-champ": () => save.rivalsBeaten.includes("Champion Coco"), "awaken-5": () => save.awakened.length >= 5, "lurker-3": () => awLevel("Lurker") >= 3, "knight-3": () => awLevel("Phantom Knight") >= 3, "boss-1": () => !!save.beatCreator, "bond-5": () => pets.some((q) => bondLevel(q.bond || 0) >= 5), "catch-40": () => stat("catch_best") >= 40, "arena-kaiju": () => save.rivalsBeaten.includes("Kaiju King Kai"), "legend-1": anyU(D.groups.legends), "legend-all": allU(D.groups.legends), "night-1": () => save.nightsWon >= 1, "night-3": () => save.nightsWon >= 3,
  };
  function checkTrophies() {
    for (const tr of D.trophies || []) {
      if (save.trophies.includes(tr.id) || !(TCHECK[tr.id] || (() => false))()) continue;
      save.trophies.push(tr.id);
      const p = pets.find((q) => !["sleep", "held"].includes(q.state)) || pets[0];
      reward(p, tr.bonus); sfx("fanfare"); vibrate([20, 30, 20]);
      if (p) { say(p, `🏆 trophy: ${tr.name}! +${tr.bonus} 💖`, 5); setFace(p, "happy", 2); burst(p, "heart", 6); }
      toast(`🏆 Trophy: ${tr.icon} ${tr.name}! +${tr.bonus} 💖`, 4);
      persist(true);
      return;                                   // one at a time
    }
  }
  setInterval(() => { try { checkTrophies(); } catch (e) { /* never stop the game */ } }, 3000);
  function cupCanvas(earned) {
    const c = doc().createElement("canvas"), s = 4, rows = D.trophyCup || [];
    c.width = 12 * s; c.height = rows.length * s;
    const g = c.getContext("2d"), col = earned ? { c: "#ffd23a", h: "#e8a81a", b: "#8a5a2a" } : { c: "#433b68", h: "#433b68", b: "#433b68" };
    rows.forEach((row, r) => [...row].forEach((ch, i) => { if (ch !== ".") { g.fillStyle = col[ch]; g.fillRect(i * s, r * s, s, s); } }));
    if (earned) { g.fillStyle = "#fff6c0"; g.fillRect(3 * s, s, s, 3 * s); }
    return c;
  }
  function openTrophies() {
    const list = $("trophyGrid"); list.innerHTML = "";
    let n = 0;
    for (const tr of D.trophies || []) {
      const have = save.trophies.includes(tr.id); if (have) n++;
      const cell = doc().createElement("div"); cell.className = "trophy" + (have ? " earned" : "");
      cell.appendChild(cupCanvas(have));
      const name = doc().createElement("b"); name.textContent = `${tr.icon} ${tr.name}`; cell.appendChild(name);
      const how = doc().createElement("small"); how.textContent = have ? tr.how : `${tr.how} (+${tr.bonus} 💖)`; cell.appendChild(how);
      list.appendChild(cell);
    }
    $("trophyCount").textContent = `${n}/${(D.trophies || []).length}`;
    openSheet("trophySheet");
  }

  function openSheet(id) { doc().querySelectorAll(".sheet").forEach((s) => (s.hidden = s.id !== id)); }
  function closeSheets() { doc().querySelectorAll(".sheet").forEach((s) => (s.hidden = true)); persist(); }
  document.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", closeSheets));
  document.querySelectorAll(".sheet").forEach((s) => s.addEventListener("pointerdown", (e) => { if (e.target === s) closeSheets(); }));

  // 🍬🧪 changing colors: a Color Candy for everyday colors, a Color Potion for rare and special ones (same as the Windows app)
  const COLOR_COST = D.colorCost || { candy: 10, potion: 40, special: [] };
  const colorCost = (col) => (col.event || col.unlock || COLOR_COST.special.includes(col.name) ? { icon: "potion", cost: COLOR_COST.potion } : { icon: "candy", cost: COLOR_COST.candy });
  let sheetPet = null;
  function openPetSheet(p) {
    sheetPet = p;
    $("sheetChat").hidden = !chatTree(p);
    $("petName").value = p.name;
    $("petKind").textContent = p.kind + (RARE.has(p.kind) ? " · rare ✨" : "");
    const blv = bondLevel(p.bond || 0);
    $("petBond").textContent = `💞 ${BOND.titles[blv - 1]}` + (blv < 5 ? ` · ${Math.floor(p.bond || 0)}/${BOND.levels[blv]} to ${BOND.titles[blv]}` : " · max friendship!");
    const pc = $("petPortrait").getContext("2d"); pc.clearRect(0, 0, 96, 100);
    drawGrid(pc, grid(p.kind, p.color, { t: 0, face: "happy" }), 8, 31, 5);
    for (const [n, tint] of worn(p)) drawHat(pc, p.kind, n, 8, 31, 5, 0, tint);
    const chips = $("colorChips"); chips.innerHTML = "";
    KINDS[p.kind].colors.forEach((col, i) => {
      const b = document.createElement("button"), locked = skinLocked(p.kind, i);
      b.className = i === p.color ? "on" : locked ? "locked" : "";
      const cc = colorCost(col);
      b.appendChild(thumb(p.kind, i, false, 3)); b.append((locked ? "🔒 " : "") + col.name + (col.event && !locked ? " ✨" : ""));
      if (!locked && i !== p.color) { const pr = doc().createElement("small"); pr.className = "price"; pr.append(pxImg(cc.icon), ` ${cc.cost}`); b.appendChild(pr); }
      b.onclick = () => {
        if (locked) { toast(col.unlock === "puppet" ? `🔒 ${col.name}: fend off this robo's Bad Dream to unlock it! (tap a Puppet Master 5 times)` : col.unlock === "merch" ? `🔒 ${col.name} comes with Blipville merch: type its 🎟️ code in ? → 🔑 Secret code.` : `🔒 ${col.name} is a ${(EVENTS.find((e) => e.id === col.event) || EVENT).icon} ${(EVENTS.find((e) => e.id === col.event) || EVENT).name} skin.${col.event === EVENT.id ? ` Earn it in the event! (tap ${EVENT.icon} at the top)` : " That event is over."}`, 4); return; }
        if (i === p.color) return;
        if (!isCreator()) {                                   // 🍬🧪 a treat changes the color
          if (save.hearts < cc.cost) { toast(`${cc.icon === "potion" ? "🧪 A Color Potion" : "🍬 A Color Candy"} costs ${cc.cost} 💖. You have ${save.hearts}. Care for your Blips to earn more!`, 3.5); return; }
          save.hearts -= cc.cost; updateHearts(true);
        }
        p.color = i; say(p, `*${cc.icon === "potion" ? "sip" : "munch"}* ${col.name.toLowerCase()}!`, 2); burst(p, "heart", 3);
        sfx(cc.icon === "potion" ? "zap" : "munch"); persist(true); openPetSheet(p);
      };
      chips.appendChild(b);
    });
    $("sheetNap").textContent = p.state === "sleep" ? "☀️ Wake" : "💤 Nap";
    const awBase = AWAKEN_BASE[p.kind] || p.kind, aw = $("sheetAwaken"), chain = AWAKEN_CHAIN[awBase], stg = awStage(p.kind);
    aw.hidden = !chain;
    aw.textContent = !chain ? "" : stg >= chain.length ? "💤 Normal form" :
      `✨ Awaken${stg ? " again" : ""}${awLevel(awBase) > stg ? "!" : ` · ${STAGE_COSTS[stg]} 💖`}`;
    $("sheetAwakenBack").hidden = !(chain && stg > 0 && stg < chain.length);
    const hc = $("hatChips"); hc.innerHTML = "";
    for (const name of Object.keys(HATS).filter(hatInShop)) {
      const owned = save.hatsOwned.includes(name), wearing = p.hat === name || p.hat2 === name;
      const b = document.createElement("button"); b.className = wearing ? "on" : "";
      b.appendChild(dressedThumb(p.kind, p.color, name, 3, (p.tints || {})[name] || 0));
      b.append(name);
      const tag = document.createElement("small");
      tag.textContent = wearing ? "✓ on" : owned ? "owned" : `💖 ${HATS[name].price}`;
      tag.className = owned || wearing ? "owned" : "price"; b.appendChild(tag);
      b.onclick = () => {
        if (wearing) { takeOff(p, name); say(p, "back to basics!", 2); }
        else if (owned) { wearItem(p, name); say(p, pick(["how do i look?", "so stylish!", "*strikes a pose*"]), 2.5); setFace(p, "happy", 1.5); }
        else {
          const price = HATS[name].price;
          if (save.hearts < price) { toast(`${name} costs ${price} 💖. You have ${save.hearts}. Care for your Blips to earn more!`, 3.5); return; }
          save.hearts -= price; save.hatsOwned.push(name); updateHearts(true); sfx("coin");
          wearItem(p, name); say(p, `a new ${name.toLowerCase()}! thank you!!`, 3); setFace(p, "happy", 2); burst(p, "heart", 5);
        }
        persist(true); openPetSheet(p);
      };
      hc.appendChild(b);
    }
    const tintBox = $("hatTints"); tintBox.innerHTML = "";          // color swatches for what it's wearing (free)
    for (const [n, cur] of worn(p)) {
      const row = document.createElement("div"); row.className = "tintRow";
      const lab = document.createElement("span"); lab.textContent = `🎨 ${n}`; row.appendChild(lab);
      TINTS.forEach(([tname, col], i) => {
        const sw = document.createElement("button"); sw.className = i === cur ? "on" : ""; sw.title = tname;
        sw.style.background = col || Object.values(HATS[n].colors)[0];
        sw.onclick = () => { p.tints = p.tints || {}; if (i) p.tints[n] = i; else delete p.tints[n];
          say(p, i ? `ooh, ${tname.toLowerCase()}!` : "back to the classic look!", 2); setFace(p, "happy", 1.2); sfx("pop"); persist(true); openPetSheet(p); };
        row.appendChild(sw);
      });
      tintBox.appendChild(row);
    }
    const s2 = $("slot2Btn");
    s2.hidden = !!save.slot2; s2.textContent = `🔓 Unlock a 2nd accessory slot · ${D.slot2Cost || 50} 💖 (wear a hat + glasses or a scarf)`;
    s2.onclick = () => {
      const cost = D.slot2Cost || 50;
      if (save.hearts < cost) { toast(`The 2nd accessory slot costs ${cost} 💖. You have ${save.hearts}.`, 3); return; }
      save.hearts -= cost; save.slot2 = true; persist(true); updateHearts(true); sfx("fanfare");
      say(p, "two accessories?! fancy!", 3); setFace(p, "happy", 2); openPetSheet(p);
    };
    $("hatSeason").textContent = Object.values(HATS).some((h) => h.season === currentSeason()) ? `✨ ${currentSeason()} items are in!` : "";
    openSheet("petSheet");
  }
  $("petName").addEventListener("input", (e) => { if (sheetPet) { sheetPet.name = e.target.value.trim().slice(0, 16) || sheetPet.name; persist(); } });
  $("sheetFeed").onclick = () => { feed(sheetPet); closeSheets(); };
  $("sheetNap").onclick = () => { nap(sheetPet); closeSheets(); };
  $("sheetPet").onclick = () => { petIt(sheetPet); closeSheets(); };
  $("sheetBye").onclick = () => {
    if (pets.length <= 1) { toast("Your town needs at least one Blip! 🏡"); return; }
    pets.splice(pets.indexOf(sheetPet), 1); tidyCookies(); toast(`👋 ${sheetPet.name} waved goodbye.`); closeSheets();
  };
  $("sheetKind").onclick = () => openZoo(sheetPet);
  const toNormal = (p) => { const base = AWAKEN_BASE[p.kind]; if (!base) return; p.kind = base; p.color %= KINDS[base].colors.length; say(p, "phew, back to normal", 2); persist(true); openPetSheet(p); };
  $("sheetAwakenBack").onclick = () => sheetPet && toNormal(sheetPet);
  $("sheetAwaken").onclick = () => {
    const p = sheetPet; if (!p) return;
    const base = AWAKEN_BASE[p.kind] || p.kind, chain = AWAKEN_CHAIN[base]; if (!chain) return;
    const stg = awStage(p.kind);
    if (stg >= chain.length) { toNormal(p); return; }
    const form = chain[stg];
    if (awLevel(base) <= stg) {
      const cost = STAGE_COSTS[stg], again = ["", "again ", "a third time "][stg];
      if (save.hearts < cost) { toast(`Awakening ${p.kind} ${again}into ${form} takes an Awakening Crystal (${cost} 💖). You have ${save.hearts}.`, 4); return; }
      if (!confirm(`Use an Awakening Crystal (${cost} 💖) to awaken ${p.kind} ${again}into ${form}?\n\nIt works for every ${base} you have, forever, and you can switch back any time.${(D.features || {}).arena ? " In the Arena, Awakened Blips hit harder!" : ""}`)) return;
      save.hearts -= cost; updateHearts(true);
      if (stg === 0) save.awakened.push(base); else (save.awakenLevel = save.awakenLevel || {})[base] = stg + 1;
    }
    p.kind = form; p.color %= KINDS[form].colors.length; sfx("fanfare"); vibrate([30, 40, 30]);
    say(p, pick(KINDS[form].lines), 3.5); setFace(p, "happy", 2); sparkle(p, 12); persist(true); openPetSheet(p);
  };

  // ------------------------------------------------------------------ the Arena ⚔️ (same rules and battle codes as the desktop app)
  const AR = D.arena || { stats: {}, types: {}, beats: {}, rivals: [] };
  const PXI = {};                                         // pixel icons for drawing on canvases
  const pxIcon = (n) => { if (!PXI[n]) { PXI[n] = new Image(); PXI[n].src = `icons/px/${n}.png`; } return PXI[n]; };
  const pxImg = (n) => { const i = doc().createElement("img"); i.className = "px"; i.src = `icons/px/${n}.png`; i.alt = ""; return i; };
  Object.keys(AR.types).concat("awaken").forEach(pxIcon);
  const beats = (a, d) => [].concat(AR.beats[a] || []).includes(d);   // a type is strong against a list of others
  const typesOf = (st) => [st.type].concat(st.type2 ? [st.type2] : []);   // some Blips have 2 types
  const typeMult = (a, ds) => ds.reduce((m, d) => m * (beats(a, d) ? 1.5 : beats(d, a) ? 0.7 : 1), 1);
  const effectText = (m) => (m > 2 ? " · double super effective!!" : m > 1.1 ? " · super effective!" : m < 0.5 ? " · barely does anything…" : m < 0.9 ? " · not very effective…" : "");
  let arenaTeam = [], arenaBattle = null, arenaTimer = null;
  const arenaEntry = (p) => { const b = AWAKEN_BASE[p.kind] || p.kind; return [b, p.color % KINDS[b].colors.length, Math.min(awLevel(b), (AWAKEN_CHAIN[b] || []).length)]; };
  function battleCodeFor(name, team) {
    const raw = JSON.stringify({ n: name.slice(0, 20), t: team.slice(0, 3) });
    const b64 = btoa(String.fromCharCode(...new TextEncoder().encode(raw)));
    return "BLIP1-" + b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }
  function readBattleCode(code) {
    code = String(code).replace(/\s+/g, "");
    if (!/^BLIP1-/i.test(code)) throw new Error("That's not a Blipville battle code (they start with BLIP1-).");
    let data;
    try {
      let b = code.slice(6).replace(/-/g, "+").replace(/_/g, "/"); while (b.length % 4) b += "=";
      data = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(b), (c) => c.charCodeAt(0))));
    } catch (e) { throw new Error("That battle code looks broken. Copy it again, all of it."); }
    const team = (data.t || []).slice(0, 3).map(([k, c, a]) => [String(k), +c || 0, +a || 0]).filter(([k]) => KINDS[AWAKEN_BASE[k] || k]);
    if (!team.length) throw new Error("That battle code has no Blips in it.");
    return [String(data.n || "A friend").slice(0, 20), team];
  }
  function fighter([kind, color, canAw]) {
    const base = AWAKEN_BASE[kind] || kind, st = AR.stats[base];
    const lvl = Math.min(+canAw || 0, (AWAKEN_CHAIN[base] || []).length);
    return { base, kind: base, color: +color, lvl, stage: 0, canAw: lvl > 0, hp: st.hp, max: st.hp, aw: false, snacked: false, atkMult: 1 };
  }
  const fst = (f) => AR.stats[f.kind];
  // backgrounds: little scenes 120 x 40 units, the same as the desktop app's (from blip.pyw)
  const fnv = (t) => { let h = 2166136261; for (const b of new TextEncoder().encode(t)) h = Math.imul(h ^ b, 16777619) >>> 0; return h; };
  const arenaBgFor = (foe) => (D.rivalBgs || {})[foe] || (D.friendBgs || ["meadow"])[fnv(foe) % (D.friendBgs || ["meadow"]).length];
  function drawArenaBg(c, name, w, h) {
    const bg = (D.arenaBgs || {})[name]; if (!bg) return;
    const s = 4, x0 = (w - 120 * s) / 2, y0 = h - 40 * s;
    const gr = c.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, bg.sky[0]); gr.addColorStop(1, bg.sky[1]);
    c.fillStyle = gr; c.fillRect(0, 0, w, h);
    const Y = (v) => (v ? y0 + v * s : 0);                 // shapes touching the top reach the top of the canvas
    for (const sh of bg.shapes) {
      const [kind, ...r] = sh;
      if (kind === "rect") { c.fillStyle = r[0]; const ya = Y(r[2]); c.fillRect(x0 + r[1] * s, ya, r[3] * s, y0 + (r[2] + r[4]) * s - ya); }
      else if (kind === "poly") { c.fillStyle = r[0]; c.beginPath(); for (let i = 0; i < r[1].length; i += 2) c.lineTo(x0 + r[1][i] * s, Y(r[1][i + 1])); c.closePath(); c.fill(); }
      else if (kind === "circ") { c.fillStyle = r[0]; c.beginPath(); c.arc(x0 + r[1] * s, y0 + r[2] * s, r[3] * s, 0, Math.PI * 2); c.fill(); }
      else if (kind === "pix") {
        const px = D.arenaPix[r[0]], pal = px[r[4] || "pal"], u = r[3];
        px.rows.forEach((row, ry) => [...row].forEach((ch, rx) => {
          if (ch !== ".") { c.fillStyle = pal[ch]; c.fillRect(x0 + (r[1] + rx * u) * s, y0 + (r[2] + ry * u) * s, Math.ceil(u * s), Math.ceil(u * s)); }
        }));
      }
    }
  }
  function newBattle(mine, theirs, foe, reward) {
    return { sides: [mine.map(fighter), theirs.map(fighter)], idx: [0, 0], awLeft: [1, 1], summoned: [false, false], turn: 0, winner: null, last: null, foe, reward,
             bg: arenaBgFor(foe), queue: [], log: [`⚔️ ${foe} wants to battle! Pick a move.`] };
  }
  const active = (b, s) => b.sides[s][b.idx[s]] || null;
  // one Awaken per battle, but a Blip that can awaken more than once may keep going (the Lurker!)
  const canAwaken = (b, s) => { const f = active(b, s); return !!(f && f.stage < f.lvl && (b.awLeft[s] || f.stage > 0)); };
  function awakenF(b, s) {
    if (!canAwaken(b, s)) return null;
    b.awLeft[s] = 0; const f = active(b, s), frac = f.hp / f.max, was = f.kind;
    f.stage += 1; f.kind = AWAKEN_CHAIN[f.base][f.stage - 1]; f.aw = true; f.color %= KINDS[f.kind].colors.length;
    f.max = Math.round(fst(f).hp * (f.atkMult < 1 ? (D.summon || {}).hp || 0.6 : 1)); f.hp = Math.min(f.max, Math.round(f.max * frac + f.max * 0.25));
    const fin = (D.finalFormBgs || {})[f.kind];
    if (fin && b.bg !== fin[0]) { b.bg = fin[0]; return `✨ ${was} awakens into ${f.kind}! ${fin[1]}`; }
    return `✨ ${was} awakens into ${f.kind}!`;
  }
  // ---- turns: each round you pick a move, the other side picks one, and the faster one goes first (same rules as blip.pyw)
  const movesOf = (b, s) => { const f = active(b, s); return f ? fst(f).moves : []; };
  const usable = (b, s, i) => { const f = active(b, s), m = movesOf(b, s)[i]; return !!(f && m && !(m.heal && (f.snacked || f.hp >= f.max)) && !(m.summon && b.summoned[s])); };
  function aiMove(b, s) {
    const f = active(b, s), foe = active(b, 1 - s), ms = movesOf(b, s);
    if (f.hp < f.max * 0.35 && usable(b, s, 3) && Math.random() < 0.6) return 3;
    const pull = ms.findIndex((m) => m.summon);
    if (pull >= 0 && usable(b, s, pull) && Math.random() < 0.7) return pull;
    let best = 0, top = -1;
    ms.forEach((m, i) => { if (m.heal || m.summon) return; const v = m.power * m.acc * typeMult(m.type, typesOf(fst(foe))) * rnd(0.8, 1.2); if (v > top) { top = v; best = i; } });
    return best;
  }
  function planRound(b, mine) {
    const pre = [], B = active(b, 1);
    if (canAwaken(b, 1) && B.hp < B.max * 0.5) pre.push([1, "awaken", null]);
    const theirs = aiMove(b, 1);
    const key = (s, i) => [movesOf(b, s)[i].fast ? 1 : 0, fst(active(b, s)).spd, Math.random()];
    const order = [[0, mine], [1, theirs]].sort((x, y) => { const p = key(...x), q = key(...y); return q[0] - p[0] || q[1] - p[1] || q[2] - p[2]; });
    return pre.concat(order.map(([s, i]) => [s, i, active(b, s)]));
  }
  function actMove(b, side, i, who) {
    if (b.winner !== null) return null;
    if (i === "awaken") return awakenF(b, side);
    const att = active(b, side), dfn = active(b, 1 - side);
    if (!att || !dfn || (who && att !== who)) return null;   // knocked out before its turn
    const m = fst(att).moves[i];
    if (m.heal) {
      if (att.snacked) return null;
      att.snacked = true; const gain = Math.min(att.max - att.hp, Math.round(att.max * m.heal)); att.hp += gain;
      b.last = [side, -gain, 1]; return `🍪 ${att.kind} had a snack and got ${gain} HP back!`;
    }
    if (m.summon) {                                         // 🎭 Pull the Strings: 2 Shadow Night Shift Blips join the team
      if (b.summoned[side]) return null;
      b.summoned[side] = true;
      const picks = m.summon.slice().sort(() => Math.random() - 0.5).slice(0, 2), S = D.summon || { hp: 0.6, atk: 0.75 };
      for (const k of picks) {
        const shadow = Math.max(0, KINDS[k].colors.findIndex((c) => c.name === "Shadow"));
        const pup = fighter([k, shadow, 0]); pup.atkMult = S.atk; pup.max = pup.hp = Math.round(pup.max * S.hp);
        b.sides[side].push(pup);
      }
      b.last = [side, 0, 1]; return `🎭 ${att.kind} pulls the strings… Shadow ${picks[0]} and Shadow ${picks[1]} join the team!`;
    }
    if (Math.random() > m.acc) { b.last = [side, 0, 1]; return `${att.kind} used ${m.name}… but it missed!`; }
    if (typesOf(fst(dfn)).includes("phantom") && Math.random() < (D.phantomDodge || 0.2)) {   // 👻 hits can pass right through a Phantom
      b.last = [side, 0, 1]; return `${att.kind} used ${m.name}… but it passed right through ${dfn.kind}! 👻`;
    }
    const mult = typeMult(m.type, typesOf(fst(dfn)));
    const crit = Math.random() < (typesOf(fst(att)).includes("cosmic") ? D.cosmicCrit || 0.25 : 0.1);
    const dmg = Math.max(1, Math.round(fst(att).atk * (att.atkMult || 1) * m.power * mult * rnd(0.85, 1.15) * (crit ? 1.5 : 1)));
    dfn.hp = Math.max(0, dfn.hp - dmg); b.last = [side, dmg, mult];
    let line = `${att.kind} used ${m.name}! ${dmg} damage` + effectText(mult) + (crit ? " · critical!" : "");
    if (dfn.hp === 0) {
      b.idx[1 - side]++; line += ` · ${dfn.kind} is out!`;
      if (!active(b, 1 - side)) b.winner = side; else line += ` ${active(b, 1 - side).kind} jumps in!`;
    }
    return line;
  }
  function arenaPick(i) {
    const b = arenaBattle; if (!b || b.winner !== null || b.queue.length || !usable(b, 0, i)) return;
    b.queue = planRound(b, i); arenaTick();
  }
  function openArena() {
    clearTimeout(arenaTimer); arenaBattle = null;
    arenaTeam = arenaTeam.filter((p) => pets.includes(p)); if (!arenaTeam.length) arenaTeam = pets.slice(0, 3);
    $("arenaLobby").hidden = false; $("arenaFight").hidden = true;
    const wins = stat("arena_wins"); $("arenaWins").textContent = `🏆 ${wins} win${wins === 1 ? "" : "s"}`;
    const box = $("arenaTeam"); box.innerHTML = "";
    for (const p of pets) {
      const e = arenaEntry(p), st = AR.stats[e[0]];
      const b = doc().createElement("button"); b.className = arenaTeam.includes(p) ? "on" : "";
      b.appendChild(thumb(e[0], e[1], false, 3));
      const nm = doc().createElement("span"); nm.className = "typed"; nm.append(...typesOf(st).map(pxImg), ` ${e[0]}`); b.appendChild(nm);
      const sm = doc().createElement("small"); sm.textContent = `❤${st.hp} ⚔${st.atk} 💨${st.spd}${e[2] ? " ✨" : ""}`; b.appendChild(sm);
      b.onclick = () => { if (arenaTeam.includes(p)) arenaTeam = arenaTeam.filter((q) => q !== p); else { arenaTeam.push(p); if (arenaTeam.length > 3) arenaTeam.shift(); } openArena(); };
      box.appendChild(b);
    }
    const tc = $("typeChart"); tc.innerHTML = "";                      // 📖 the type chart
    const tname = (t) => { const s = doc().createElement("span"); s.className = "typed"; s.append(pxImg(t), ` ${AR.types[t][1]}`); return s; };
    for (const t of Object.keys(AR.types)) {
      const row = doc().createElement("div"); row.className = "typeRow"; row.appendChild(tname(t));
      const list = [].concat(AR.beats[t] || []), r = doc().createElement("span");
      const perk = t === "phantom" ? "1 in 5 hits pass through it" : t === "cosmic" ? "1 in 4 hits are critical" : "";
      if (list.length) { r.append("beats "); list.forEach((x, i) => { if (i) r.append(" & "); r.appendChild(tname(x)); }); }
      if (perk) { const weak = Object.keys(AR.types).filter((x) => beats(x, t)), w = doc().createElement("div"); w.className = "muted";
                  w.append(perk + (weak.length ? " · weak to " : "")); weak.forEach((x, i) => { if (i) w.append(" & "); w.appendChild(tname(x)); }); r.appendChild(w); }
      row.appendChild(r); tc.appendChild(row);
    }
    const dual = doc().createElement("div"); dual.className = "typeRow";
    dual.textContent = "Some Blips have 2 types: they get both types' strengths and weaknesses (a hit can be super effective twice!) and attack with whichever type works best.";
    tc.appendChild(dual);
    const rv = $("arenaRivals"); rv.innerHTML = "";
    for (const r of AR.rivals) {
      const b = doc().createElement("button");
      b.textContent = `🥊 ${r.name} · +${r.reward} 💖${save.rivalsBeaten.includes(r.name) ? " ✓" : ""}`;
      b.onclick = () => startBattle(r.team, r.name, r.reward); rv.appendChild(b);
    }
    $("arenaCopy").onclick = async () => {
      if (!arenaTeam.length) { toast("Pick at least one Blip for your team!", 2.5); return; }
      const code = battleCodeFor(arenaTeam[0].name, arenaTeam.map(arenaEntry));
      try { await navigator.clipboard.writeText(code); toast("📋 Battle code copied! Send it to a friend (or post it on the Blipville Discord).", 4); }
      catch (e) { prompt("Your battle code (copy it):", code); }
    };
    $("arenaPaste").onclick = async () => {
      let text = ""; try { text = await navigator.clipboard.readText(); } catch (e) { /* not allowed: ask */ }
      if (!/^\s*BLIP1-/i.test(text)) text = prompt("Paste their battle code (it starts with BLIP1-):") || "";
      if (!text.trim()) return;
      try { const [name, team] = readBattleCode(text); startBattle(team, name, 10); } catch (e) { toast(e.message, 3.5); }
    };
    openSheet("arenaSheet");
  }
  function startBattle(theirs, foe, reward) {
    if (!arenaTeam.length) { toast("Pick at least one Blip for your team!", 2.5); return; }
    arenaBattle = newBattle(arenaTeam.map(arenaEntry), theirs, foe, reward);
    $("arenaLobby").hidden = true; $("arenaFight").hidden = false; sfx("whoosh");
    drawBattle();
  }
  function arenaTick() {
    const b = arenaBattle; if (!b) return;
    while (b.queue.length) {                                // one move at a time, so you can see what happened
      const [s, i, who] = b.queue.shift(), line = actMove(b, s, i, who);
      if (line) { b.log.push(line); sfx(i === "awaken" ? "fanfare" : line.startsWith("🍪") ? "munch" : b.last && b.last[1] > 30 ? "thud" : "boop"); break; }
    }
    if (b.winner !== null) { b.queue = []; finishBattle(b); }
    drawBattle();
    if (b.queue.length) arenaTimer = setTimeout(arenaTick, 850);
  }
  function finishBattle(b) {
    if (b.winner === 0) {
      bump("arena_wins"); questTick("arena_win");
      if (b.sides[1].some((f) => f.base === "Blipmaker")) { b.reward = (b.reward || 0) + ((D.creator || {}).bossReward || 50); save.beatCreator = true; b.log.push("You beat the Blipmaker! 👑"); } arenaTeam.forEach((q) => pets.includes(q) && bondUp(q, "arena"));
      if (AR.rivals.some((r) => r.name === b.foe) && !save.rivalsBeaten.includes(b.foe)) save.rivalsBeaten.push(b.foe);
      if (b.foe === D.puppetRival) {                          // 🎭 Shadow colors for the Night Shift crew
        save.skins = save.skins || []; const fresh = (D.shadowSkins || []).filter((sk) => !save.skins.includes(sk));
        if (fresh.length) { save.skins.push(...fresh); b.log.push("🎭 The strings are cut! Shadow colors unlocked for the Night Shift crew and the Wind-Up Hare."); }
      }
      reward(pets[0], b.reward); b.log.push(`🏆 You win! +${b.reward} 💖`); sfx("fanfare"); vibrate([30, 40, 30]);
      const w = stat("arena_wins"); $("arenaWins").textContent = `🏆 ${w} win${w === 1 ? "" : "s"}`;
    } else b.log.push("💤 Your team needs a nap… try again!");
    persist(true);
  }
  // 🎵 music for the special stages (same tunes as the Windows app): a little note scheduler on the sound-effects audio
  const music = { name: null, timer: null, next: 0, pos: [0, 0], at: [0, 0] };
  const NOTE = (n) => { if (n === "-") return 0; const i = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"].indexOf(n.slice(0, -1)); return 440 * 2 ** ((i + 12 * (+n.slice(-1) + 1) - 69) / 12); };
  function musicNote(a, out, f, t, dur, shape, vol) {
    if (!f) return;
    const o = a.createOscillator(), g = a.createGain();
    o.type = shape === "square" ? "square" : shape === "bell" ? "sine" : "triangle"; o.frequency.value = f;
    g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(vol * (shape === "square" ? 0.5 : 1), t + 0.01);
    if (shape === "bell") g.gain.exponentialRampToValueAtTime(0.0001, t + Math.min(dur, 1.2));
    else { g.gain.setValueAtTime(vol * (shape === "square" ? 0.4 : 1), t + Math.max(0.02, dur - 0.04)); g.gain.linearRampToValueAtTime(0.0001, t + dur); }
    o.connect(g).connect(out); o.start(t); o.stop(t + dur + 0.05);
  }
  function stopMusic() { clearInterval(music.timer); music.timer = null; if (music.out) { try { music.out.disconnect(); } catch (e) { /* gone */ } } music.name = null; }
  function playMusic(name) {
    if (name === music.name) return;
    stopMusic();
    const song = (D.arenaMusic || {})[name]; if (!song || !save.sound) return;
    const a = audio(); if (!a) return;
    music.name = name; music.out = a.createGain(); music.out.gain.value = 0.35; music.out.connect(a.destination);
    const beat = 60 / song.bpm, parts = [[song.melody, song.lead, 0.22], [song.bass, song.low, 0.18]];
    music.pos = [0, 0]; music.at = [a.currentTime + 0.1, a.currentTime + 0.1];
    music.timer = setInterval(() => {
      if (!save.sound || $("arenaSheet").hidden || !arenaBattle || arenaBattle.winner !== null || (D.arenaMusic || {})[arenaBattle.bg] !== song) { stopMusic(); return; }
      parts.forEach(([part, shape, vol], v) => {
        while (music.at[v] < a.currentTime + 0.6) {
          const [n, beats] = part[music.pos[v] % part.length];
          musicNote(a, music.out, NOTE(n), music.at[v], beats * beat, shape, vol);
          music.at[v] += beats * beat; music.pos[v]++;
        }
      });
    }, 150);
  }
  function drawBattle() {
    const b = arenaBattle, cv = $("arenaCanvas"), c = cv.getContext("2d");
    playMusic(b.winner === null ? b.bg : null);
    c.clearRect(0, 0, cv.width, cv.height); c.imageSmoothingEnabled = false;
    drawArenaBg(c, b.bg, cv.width, cv.height);
    [0, 1].forEach((side) => {
      const f = active(b, side), x0 = side === 0 ? 20 : 200;
      b.sides[side].forEach((g, j) => drawGrid(c, grid(g.kind, g.color, { t: 0, silhouette: g.hp === 0 }), (side === 0 ? 8 : 268) + j * 30, 8, 2));
      if (!f) return;
      drawGrid(c, grid(f.kind, f.color, { t: now(), face: f.hp > f.max / 2 ? "happy" : "normal" }), x0 + 12, 52, 7);
      c.fillStyle = "#fff"; c.font = "700 11px " + FONT; c.textAlign = "center";
      const label = `${f.kind}${f.aw ? " ✨" : ""}`, lw = c.measureText(label).width, tys = typesOf(fst(f)), lx = x0 + 68 + 9 + (tys.length - 1) * 7;
      c.strokeStyle = "rgba(10, 8, 20, .85)"; c.lineWidth = 3; c.lineJoin = "round"; c.strokeText(label, lx, 48);
      c.fillText(label, lx, 48);
      tys.forEach((t, i) => { const ic = pxIcon(t); if (ic.complete) c.drawImage(ic, lx - lw / 2 - 19 - (tys.length - 1 - i) * 14, 37, 14, 14); });   // 1 or 2 type icons
      c.fillStyle = "#2b2547"; c.fillRect(x0, 150, 136, 12);
      const fr = f.hp / f.max; c.fillStyle = fr > 0.5 ? "#9ad8a8" : fr > 0.2 ? "#ffd23a" : "#ff5a7a"; c.fillRect(x0, 150, 136 * fr, 12);
      c.fillStyle = "#ffffff"; c.font = "800 10px " + FONT; c.fillText(`${f.hp} / ${f.max}`, x0 + 68, 160);
    });
    if (b.last && b.winner === null) {
      const [ls, d] = b.last; c.font = "800 18px " + FONT;
      if (d < 0) { c.fillStyle = "#9ad8a8"; c.fillText(`+${-d}`, ls === 0 ? 90 : 280, 70); }
      else { c.fillStyle = "#ff5a7a"; c.fillText(d ? `-${d}` : "miss!", ls === 0 ? 280 : 90, 70); }
    }
    const mv = $("arenaMoves"); mv.innerHTML = ""; mv.hidden = b.winner !== null;
    if (b.winner === null) {
      const me = active(b, 0), foe = active(b, 1), busy = b.queue.length > 0;
      movesOf(b, 0).forEach((m, i) => {
        const bt = doc().createElement("button"); bt.className = "move m" + i; bt.disabled = busy || !usable(b, 0, i);
        const top = doc().createElement("b"), info = doc().createElement("small");
        if (m.heal) { top.textContent = "🍪 Snack"; info.textContent = me.snacked ? "used" : `heal ${Math.round(m.heal * 100)}% · once`; }
        else if (m.summon) { top.append(pxImg("phantom"), " Pull the Strings"); info.textContent = b.summoned[0] ? "used" : "2 Shadow puppets join · once"; }
        else {
          top.append(pxImg(m.type), ` ${m.name}`);
          const mult = typeMult(m.type, typesOf(fst(foe)));
          info.textContent = [m.fast ? "goes first" : "", m.acc < 1 ? `${Math.round(m.acc * 100)}% hit` : "", mult > 1.1 ? "strong!" : mult < 0.9 ? "weak" : ""].filter(Boolean).join(" · ") || "normal";
        }
        bt.append(top, info); bt.onclick = () => arenaPick(i); mv.appendChild(bt);
      });
    }
    $("arenaLog").innerHTML = ""; for (const l of b.log.slice(-4)) { const d = doc().createElement("div"); d.textContent = l; $("arenaLog").appendChild(d); }
    const aw = $("arenaAwaken"); aw.hidden = !(b.winner === null && canAwaken(b, 0) && !b.queue.length);
    if (!aw.hidden) aw.textContent = `✨ Awaken ${active(b, 0).base}!`;
    aw.onclick = () => { const l = awakenF(b, 0); if (l) { b.log.push(l); sfx("fanfare"); drawBattle(); } };
    const back = $("arenaBack");
    back.textContent = b.winner === null ? "🏳️ Give up" : "↩ Back to the Arena";
    back.onclick = () => { if (b.winner === null) { b.queue = []; b.winner = 1; b.log.push("🏳️ You gave up. Next time!"); clearTimeout(arenaTimer); drawBattle(); } else openArena(); };
  }
  $("arenaBtn").onclick = openArena;
  if (!(D.features || {}).arena) $("arenaBtn").hidden = true;      // 🚧 parked for after 1.0 (blip.pyw FEATURES)

  // ghosts 👻
  function lightCandle() {
    if (!(D.groups.ghosts || []).some((k) => !isUnlocked(k))) { toast("You've met every ghost! 👻🏆", 3); return; }
    if (save.hearts < D.candleCost) { toast(`A Spirit Candle costs ${D.candleCost} 💖. You have ${save.hearts}. Ghosts also drift by on their own at night (7 PM to 7 AM).`, 4); return; }
    save.hearts -= D.candleCost; persist(true); updateHearts(true); sfx("coin");
    candleUntil = now() + 10 * 60; nextGhost = Math.min(nextGhost, now() + rnd(8, 20)); closeSheets();
    toast("🕯️ Candle lit! For 10 minutes ghosts will drift by. They fade in and out: tap one while it glows!", 4.5);
  }
  function openGhosts() {
    const ghosts = D.groups.ghosts || [], grid_ = $("ghostGrid"); grid_.innerHTML = "";
    let met = 0;
    for (const k of ghosts) {
      const open = isUnlocked(k); if (open) met++;
      const b = doc().createElement("button"); b.className = open ? "" : "locked";
      b.appendChild(thumb(k, KINDS[k].default || 0, !open, 4));
      const label = doc().createElement("span"); label.textContent = open ? k : "???"; b.appendChild(label);
      b.onclick = () => { if (open) { if (addPet(k)) closeSheets(); } else toast("Meet it at night, then tap it while it glows! 👻", 3); };
      grid_.appendChild(b);
    }
    $("ghostCount").textContent = `${met}/${ghosts.length}`;
    const left = Math.ceil((candleUntil - now()) / 60);
    $("ghostStatus").textContent = met === ghosts.length ? "🏆 You've met every ghost!"
      : candleUntil > now() ? `🕯️ Your Spirit Candle is burning (${left} min left). Ghosts are on their way!`
      : ghostHours() ? "🌙 Ghosts are out right now! Watch your town and tap one while it glows."
      : "☀️ It's daytime, so the ghosts are hiding until 7 PM. Light a Spirit Candle to call them now!";
    const c = $("ghostCandle");
    c.hidden = met === ghosts.length;
    c.textContent = `🕯️ Light a Spirit Candle · ${D.candleCost} 💖`;
    c.onclick = lightCandle;
    openSheet("ghostSheet");
  }
  $("ghostBtn").onclick = openGhosts;

  // collection
  function openZoo(swapPet = null) {
    const grid_ = $("zooGrid"); grid_.innerHTML = "";
    const groups = [["Critters", D.groups.critters], ["Animals", D.groups.animals], ...(D.groups.tabs || []), ["Rare ✨ (hatch from eggs)", D.groups.rare],
                    ["Night Shift 🌙 (survive the nights)", D.groups.nightShift], ["Cryptids 👣 (spot them in town)", D.groups.cryptids],
                    [`Kaiju 🦖 (super rare! tap one ${HITS} times)`, D.groups.kaiju || []],
                    ["Legends ✨ (visit a world, tap them when they stroll by)", D.groups.legends || []],
                    ["Ghosts 👻 (they drift by at night: tap one while it glows!)", D.groups.ghosts || []],
                    ["Gifts 🎁 (limited-time thank-you Blips)", D.groups.gifts || []],
                    [`Event 🎖️ (earn them in ${EVENT.name})`, D.groups.eventKinds || []],
                    ["Bad Dreams 🧸 (tap a Puppet Master 5 times… then fend them off)", [...DREAMS]]];
    let found = 0, total = 0, armed = null;     // armed = the locked Blip waiting for a second tap (spoiler check)
    const how = (k) => (EGYPT.has(k) ? "🏺 dig it up in Egypt World" : GHOST.has(k) ? "👻 meet it at night" : LEG.has(k) ? `✨ find it in ${LEGEND_WORLD[k]}` : WORLD_OF[k] ? `🌍 unlock ${WORLD_OF[k]}` : GIFTS.has(k) ? "🎁 a limited-time gift" : EVENTK.has(k) ? `🎖️ earn it in ${EVENT.name}` : RARE.has(k) ? "🥚 hatch from an egg" : KAIJU.has(k) ? "🦖 catch it in the city" : CRYPT.has(k) ? "👣 spot it in town" : `🌙 survive Night ${D.unlocks[k]}`);
    for (const [title, kinds] of groups) {
      const h = document.createElement("div"); h.className = "zooGroup"; h.textContent = title; grid_.appendChild(h);
      const world = WORLDS.find((w) => w.tab === title);
      if (world && !save.worlds.includes(world.name)) {           // a locked world: one button to unlock its whole tab
        const u = document.createElement("button"); u.className = "peekAll lure worldBtn";
        u.textContent = `🔓 Unlock ${world.name} ${world.icon} · ${world.cost} 💖`;
        u.onclick = () => unlockWorld(world, u);
        grid_.appendChild(u);
      }
      const cells = document.createElement("div"); cells.className = "zooCells";
      for (const k of kinds) {
        total++;
        const open = isUnlocked(k), peek = !open && (save.peeked.includes(k) || !!WORLD_OF[k]); if (open) found++;
        const b = document.createElement("button");
        b.className = open ? "" : peek ? "locked peeked" : "locked";
        b.appendChild(thumb(k, KINDS[k].default || 0, !open && !peek, 4));
        const label = document.createElement("span"); label.textContent = open || peek ? k : "???"; b.appendChild(label);
        if (!open) { const tag = document.createElement("small"); tag.textContent = peek ? `🔒 ${how(k)}` : "tap to peek 👀"; b.appendChild(tag); }
        b.onclick = () => {
          if (!open && peek) { toast(`${k}: ${how(k)} to unlock it!`); return; }
          if (!open) {
            if (armed !== b) {                       // first tap: spoiler warning
              if (armed) armed.reset();
              armed = b; b.classList.add("armed"); label.textContent = "spoiler!"; b.lastChild.textContent = "tap again to peek";
              b.reset = () => { b.classList.remove("armed"); label.textContent = "???"; b.lastChild.textContent = "tap to peek 👀"; };
              return;
            }
            save.peeked.push(k); persist(true); sfx("pop"); openZoo(swapPet); return;
          }
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
    const lure = $("lureBtn"), crLeft = D.groups.cryptids.filter((k) => !isUnlocked(k)).length;
    lure.hidden = !crLeft; lure.textContent = `🔦 Set out a Cryptid Lure · ${D.lureCost} 💖`;
    lure.onclick = () => {
      if (save.hearts < D.lureCost) { toast(`A Cryptid Lure costs ${D.lureCost} 💖. You have ${save.hearts}. Cryptids also wander by on their own, so keep watching!`, 4); return; }
      save.hearts -= D.lureCost; persist(true); updateHearts(true); sfx("coin");
      nextSighting = Math.min(nextSighting, now() + rnd(8, 20)); closeSheets();
      toast("🔦 Lure set! Watch your town: when a shadow with glowing eyes sneaks by, tap it!", 4.5);
    };
    const beacon = $("beaconBtn"), kLeft = (D.groups.kaiju || []).filter((k) => !isUnlocked(k)).length;
    beacon.hidden = !kLeft; beacon.textContent = `📡 Switch on a Kaiju Beacon · ${D.beaconCost} 💖`;
    beacon.onclick = () => {
      if (save.hearts < D.beaconCost) { toast(`A Kaiju Beacon costs ${D.beaconCost} 💖. You have ${save.hearts}. Kaiju also stomp by on their own… once in a long while.`, 4); return; }
      save.hearts -= D.beaconCost; persist(true); updateHearts(true); sfx("coin");
      nextKaiju = Math.min(nextKaiju, now() + rnd(10, 25)); closeSheets();
      toast(`📡 Beacon on! Something HUGE is coming. Tap it ${HITS} times before it leaves!`, 4.5);
    };
    const candle = $("candleBtn"), gLeft = (D.groups.ghosts || []).filter((k) => !isUnlocked(k)).length;
    candle.hidden = !gLeft; candle.textContent = `🕯️ Light a Spirit Candle · ${D.candleCost} 💖`;
    candle.onclick = lightCandle;
    const all = $("peekAll"), hidden = groups.flatMap(([, ks]) => ks).filter((k) => !isUnlocked(k) && !save.peeked.includes(k));
    all.hidden = !hidden.length; all.textContent = "👀 Peek at all locked Blips"; all.classList.remove("armed");
    all.onclick = () => {
      if (!all.classList.contains("armed")) { all.classList.add("armed"); all.textContent = "Spoilers! Tap again to show them all"; return; }
      save.peeked.push(...hidden); persist(true); sfx("pop"); openZoo(swapPet);
    };
    $("zooHint").textContent = swapPet ? `Pick a new kind for ${swapPet.name}.` : "Tap a Blip to bring it to town.";
    openSheet("zooSheet");
  }

  // save codes: back up your town, or move it to another phone / browser
  const CODE_PREFIX = "BLIPVILLE1:";
  function saveCode() {
    persist(true);
    return CODE_PREFIX + btoa(unescape(encodeURIComponent(JSON.stringify(save))));
  }
  function readCode(text) {
    text = (text || "").trim().replace(/\s+/g, "");
    if (!text.startsWith(CODE_PREFIX)) return null;
    try { const d = JSON.parse(decodeURIComponent(escape(atob(text.slice(CODE_PREFIX.length))))); return d && typeof d === "object" && Array.isArray(d.pets) ? d : null; }
    catch (e) { return null; }
  }
  $("copySave").onclick = async () => {
    const code = saveCode();
    $("saveCode").value = code;
    try { await navigator.clipboard.writeText(code); toast("💾 Save code copied! Paste it somewhere safe (like a note or a message to yourself).", 4.5); }
    catch (e) { $("saveCode").select(); toast("💾 Here's your save code. Copy it and keep it somewhere safe.", 4); }
    sfx("coin");
  };
  $("loadSave").onclick = () => {
    const d = readCode($("saveCode").value);
    if (!d) { toast("That doesn't look like a Blipville save code. Paste the whole thing, starting with BLIPVILLE1:", 4.5); return; }
    const sure = $("loadSave");
    if (!sure.classList.contains("armed")) { sure.classList.add("armed"); sure.textContent = "This replaces your town here. Tap again to load"; return; }
    frozen = true;
    try { localStorage.setItem(SAVE_KEY, JSON.stringify(d)); } catch (e) { frozen = false; toast("Couldn't save on this browser (private mode?)."); return; }
    location.reload();
  };
  window.blipvilleSaveCode = { saveCode, readCode };

  // worlds: unlock with hearts, then visit any time
  function unlockWorld(w, btn) {
    if (save.hearts < w.cost) { toast(`${w.name} costs ${w.cost} 💖. You have ${save.hearts}. Care for your Blips to earn more!`, 4); return false; }
    if (!btn.classList.contains("armed")) { btn.classList.add("armed"); btn.textContent = `Unlock for ${w.cost} 💖? Tap again`; return false; }
    save.hearts -= w.cost; save.worlds.push(w.name); updateHearts(true); sfx("fanfare");
    visitWorld(w.name);
    const kinds = Object.keys(WORLD_OF).filter((k) => WORLD_OF[k] === w.name);
    const p = addPet(pick(kinds), { quiet: true });
    if (p) { say(p, `hi! i'm from ${w.name} ${w.icon}`, 4); burst(p, "heart", 6); }
    toast(`${w.icon} ${w.name} unlocked! Every Blip in ${w.tab} is yours to pick.`, 4.5);
    return true;
  }
  function visitWorld(name) {
    save.world = name; weather = []; persist(true); closeSheets();
    if (name) nextLegend = Math.min(nextLegend, now() + rnd(45, 90));
    const w = WORLDS.find((x) => x.name === name), p = pets.find((q) => q.state !== "sleep");
    if (p) say(p, w ? `welcome to ${w.name}! ${w.icon}` : "home sweet home!", 3);
  }
  function openWorlds() {
    const list = $("worldList"); list.innerHTML = "";
    const row = (icon, name, sub, label, cls, onclick) => {
      const d = document.createElement("div"); d.className = "worldRow";
      const t = document.createElement("div"); t.innerHTML = `<b>${icon} ${name}</b><small>${sub}</small>`;
      const b = document.createElement("button"); b.textContent = label; b.className = cls; b.onclick = () => onclick(b);
      d.append(t, b); list.appendChild(d);
    };
    const here = hereWorld();
    row("🏠", "Home", "your town, with the seasons", here ? "Go home" : "You're here", here ? "" : "here", () => here && visitWorld(null));
    for (const w of WORLDS) {
      const n = Object.keys(WORLD_OF).filter((k) => WORLD_OF[k] === w.name).length;
      if (!w.cost) row(w.icon, w.name, `free! dig up its ${n} gods (${n - Object.keys(WORLD_OF).filter((k) => WORLD_OF[k] === w.name && !isUnlocked(k)).length} found)`, "🏺 Dig", "", () => openDig());
      else if (save.worlds.includes(w.name)) row(w.icon, w.name, `${n} Blips unlocked`, here === w.name ? "You're here" : "Visit", here === w.name ? "here" : "", () => here !== w.name && visitWorld(w.name));
      else row(w.icon, w.name, `unlocks ${n} Blips in ${w.tab}`, `🔒 ${w.cost} 💖`, "locked", (b) => unlockWorld(w, b));
    }
    openSheet("worldSheet");
  }
  $("worldBtn").onclick = openWorlds;

  // 🏺 Dig Site: one hidden god per board, hot/cold hints, a few heart treasures, free new boards
  let dig = null;
  const digHint = (d) => (d === 1 ? ["🔥", "HOT!"] : d === 2 ? ["☀️", "warm"] : d === 3 ? ["🌤️", "lukewarm"] : ["❄️", "cold"]);
  function newDig() {
    const left = [...EGYPT].filter((k) => !isUnlocked(k));
    const cells = []; for (let y = 0; y < DIG.rows; y++) for (let x = 0; x < DIG.cols; x++) cells.push([x, y]);
    for (let i = cells.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [cells[i], cells[j]] = [cells[j], cells[i]]; }
    dig = { god: left.length ? pick(left) : null, at: cells[0], treasure: new Set(cells.slice(1, 1 + DIG.treasures).map((c) => c.join())), dug: {}, tries: DIG.tries, over: false };
    $("digMsg").textContent = dig.god ? `A god is hiding in the sand! ${DIG.tries} digs. Every dig tells you how close you are.` : "You've found every god! 🏆 Dig for treasure anyway.";
    drawDig();
  }
  function drawDig() {
    const g = $("digGrid"); g.innerHTML = ""; g.style.gridTemplateColumns = `repeat(${DIG.cols}, 1fr)`;
    for (let y = 0; y < DIG.rows; y++) for (let x = 0; x < DIG.cols; x++) {
      const b = document.createElement("button"), got = dig.dug[x + "," + y];
      if (got) b.classList.add("dug");
      if (got === "god") { const c = document.createElement("canvas"); c.width = 64; c.height = 52; drawGrid(c.getContext("2d"), grid(dig.god, 0, { t: 0, face: "happy" }), 0, 0, 4); b.appendChild(c); }
      else if (got) b.textContent = got;
      b.onclick = () => digAt(x, y);
      g.appendChild(b);
    }
    $("digNew").textContent = `New dig site · ⛏️ ${dig.tries} digs left`;
  }
  function digAt(x, y) {
    const key = x + "," + y;
    if (dig.over || dig.dug[key]) return;
    dig.tries--;
    if (dig.god && x === dig.at[0] && y === dig.at[1]) {
      dig.dug[key] = "god"; dig.over = true; save.gods.push(dig.god); persist(true); sfx("fanfare"); vibrate([30, 40, 30]);
      $("digMsg").textContent = `You dug up ${dig.god}! 🏺✨ They're joining your town.`;
      const p = addPet(dig.god, { quiet: true }); if (p) say(p, "i'm free! thank you! 🏺", 4);
      checkTrophies();
    } else if (dig.treasure.has(key)) {
      dig.dug[key] = "💖"; save.hearts += DIG.hearts; updateHearts(true); $("digMsg").textContent = `Treasure! +${DIG.hearts} 💖`;
    } else {
      const d = dig.god ? Math.abs(x - dig.at[0]) + Math.abs(y - dig.at[1]) : 9, [icon, word] = digHint(d);
      dig.dug[key] = icon; $("digMsg").textContent = dig.god ? `${word}…` : "just sand…";
    }
    if (!dig.over && dig.tries <= 0) {
      dig.over = true;
      if (dig.god) { dig.dug[dig.at.join()] = "👣"; $("digMsg").textContent = "Out of digs! The god slipped away (they were where the 👣 are). Try a new dig site!"; }
    }
    drawDig();
  }
  function openDig() {
    if (hereWorld() !== "Egypt World") visitWorld("Egypt World");
    if (!dig || dig.over) newDig(); else drawDig();
    openSheet("digSheet");
  }
  $("digNew").onclick = newDig;

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
    const ec = $("eggCanvas"), c = ec.getContext("2d"), t0 = now(); let cracked = false;
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
        if (t > 1.2 && !cracked) { cracked = true; sfx("crack"); }
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
          done.disabled = false; done.textContent = "Yay! Bring it to town 🐾"; vibrate([30, 40, 30]); sfx("fanfare");
          $("eggText").textContent = `You hatched a ${kind}!`;
          $("eggSub").textContent = `Rare Blips found: ${save.hatched.length}/${D.groups.rare.length}`;
          done.onclick = () => {
            closeSheets();
            if (pets.length >= maxPets()) { toast(`${kind} is waiting in your 📖 Zoo (town is full).`); return; }
            const p = addPet(kind, { quiet: true }); if (p) say(p, "i'm new here! hi!! ✨", 4);
          };
        }
      }
      view.requestAnimationFrame(anim);
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
    const a = doc().createElement("a"); a.href = URL.createObjectURL(blob); a.download = "my-blipville.png";
    doc().body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    toast("📸 Saved a picture of your town!");
  }

  let nextFeed = 0;
  $("feedBtn").onclick = () => {
    const awake = pets.filter((p) => p.state !== "held");
    if (!awake.length) return;
    const t = now();
    if (t < nextFeed) { toast(`🍪 The cookie jar needs a moment… (${Math.ceil(nextFeed - t)} s)`, 1.5); return; }
    const p = awake.reduce((a, b) => (b.hunger > a.hunger ? b : a));
    if (p.hunger < 25) { toast("Everyone's full! 🍪 Try again in a few minutes. (Full Blips don't give hearts.)", 3); return; }
    nextFeed = t + 8;
    feed(p); toast(`🍪 Fed ${p.name}!`, 1.8);
  };
  $("friendBtn").onclick = () => {
    const pool = D.groups.critters.concat(D.groups.animals, ...(D.groups.tabs || []).map(([, ks]) => ks)).filter(isUnlocked);
    addPet(pick(pool), { x: rnd(40, W - 40) });
  };
  $("eggBtn").onclick = openEgg;
  $("collectionBtn").onclick = () => openZoo(null);
  $("trophyBtn").onclick = () => openTrophies();
  // ------------------------------------------------------------------ Cookie Catch 🍪 (the same rules as the desktop app)
  const CC = D.cookieCatch || { seconds: 45, lives: 3, maxHearts: 25, cookie: [], kinds: {} };
  let catchGame = null;
  function ccCookie(c, x, y, kind, s = 3) {
    const pal = CC.kinds[kind];
    CC.cookie.forEach((row, r) => [...row].forEach((ch, i) => { if (ch !== ".") { c.fillStyle = pal[ch]; c.fillRect(x + (i - 4) * s, y + (r - 3) * s, s, s); } }));
  }
  function openCatch(p) {
    closeSheets(); openSheet("catchSheet");
    catchGame = { pet: p, kind: p.kind, color: p.color, running: false, x: 180, aim: null };
    ccTitle();
  }
  function ccTitle(result) {
    const g = catchGame, cv = $("catchCanvas"), c = cv.getContext("2d"), W = cv.width, H = cv.height;
    c.fillStyle = "#1d1a2e"; c.fillRect(0, 0, W, H); c.fillStyle = "#3a3360"; c.fillRect(0, H - 24, W, 24);
    c.textAlign = "center"; c.fillStyle = "#ffd23a"; c.font = "800 22px " + FONT; c.fillText("🍪 Cookie Catch", W / 2, 50);
    ccCookie(c, W / 2 - 60, 100, "cookie", 4); ccCookie(c, W / 2, 100, "golden", 4); ccCookie(c, W / 2 + 60, 100, "burnt", 4);
    c.font = "800 11px " + FONT; c.fillStyle = "#fff"; c.fillText("+1", W / 2 - 60, 134); c.fillStyle = "#ffd23a"; c.fillText("+5", W / 2, 134);
    c.fillStyle = "#ff5a7a"; c.fillText("ouch!", W / 2 + 60, 134);
    c.fillStyle = "#e8e4ff"; c.font = "600 12px " + FONT;
    c.fillText(`Drag ${g.pet.name} (or use ← →) to catch cookies.`, W / 2, 158); c.fillText(`Burnt ones cost a heart. ${CC.seconds} seconds!`, W / 2, 175);
    if (result) { c.fillStyle = "#9ad8a8"; c.font = "800 13px " + FONT; c.fillText(result, W / 2, 202); }
    const best = stat("catch_best"); if (best) { c.fillStyle = "#c8c0e8"; c.font = "600 11px " + FONT; c.fillText(`Best: ${best}`, W / 2, 220); }
    c.fillStyle = "#fff"; c.font = "800 14px " + FONT; c.fillText(`Tap to play${result ? " again" : ""}`, W / 2, 239);
    drawGrid(c, grid(g.kind, g.color, { t: 0, face: "happy" }), W / 2 - 32, H - 24 - 52, 4);
  }
  function ccStart() {
    const g = catchGame, t = now();
    Object.assign(g, { running: true, score: 0, lives: CC.lives, items: [], t0: t, last: t, nextDrop: t + 0.6, pops: [] });
    sfx("boop"); requestAnimationFrame(ccStep);
  }
  function ccStep() {
    const g = catchGame; if (!g || !g.running) return;
    if ($("catchSheet").hidden) { g.running = false; return; }
    const cv = $("catchCanvas"), c = cv.getContext("2d"), W = cv.width, H = cv.height, t = now();
    const dt = Math.min(0.05, t - g.last); g.last = t;
    const left = CC.seconds - (t - g.t0);
    if (left <= 0 || g.lives <= 0) { ccFinish(); return; }
    if (g.aim !== null) g.x += (clamp(g.aim, 24, W - 24) - g.x) * Math.min(1, dt * 14);
    const speed = 110 + (t - g.t0) * 4;
    if (t >= g.nextDrop) {
      const r = Math.random(), kind = r < 0.06 ? "golden" : r < 0.30 ? "burnt" : "cookie";
      g.items.push({ kind, x: rnd(18, W - 18), y: 30, v: speed * rnd(0.85, 1.2) });
      g.nextDrop = t + Math.max(0.3, 0.75 - (t - g.t0) * 0.01);
    }
    const top = H - 24 - 52;
    for (const it of [...g.items]) {
      it.y += it.v * dt;
      if (it.y >= top - 8 && it.y <= top + 20 && Math.abs(it.x - g.x) < 28) {
        g.items.splice(g.items.indexOf(it), 1);
        if (it.kind === "burnt") { g.lives--; sfx("thud"); vibrate(30); g.pops.push([it.x, top, "ouch!", "#ff5a7a", t]); }
        else { const pts = CC.kinds[it.kind].points; g.score += pts; sfx(it.kind === "golden" ? "coin" : "pop"); g.pops.push([it.x, top, `+${pts}`, pts > 1 ? "#ffd23a" : "#fff", t]); }
      } else if (it.y > H + 10) g.items.splice(g.items.indexOf(it), 1);
    }
    c.fillStyle = "#1d1a2e"; c.fillRect(0, 0, W, H); c.fillStyle = "#3a3360"; c.fillRect(0, H - 24, W, 24);
    c.font = "800 15px " + FONT; c.textAlign = "left"; c.fillStyle = "#ffd23a"; c.fillText(`🍪 ${g.score}`, 10, 22);
    c.textAlign = "center"; c.fillText("💖".repeat(g.lives) + "🖤".repeat(CC.lives - g.lives), W / 2, 22);
    c.textAlign = "right"; c.fillStyle = "#fff"; c.fillText(`⏱ ${Math.ceil(left)}`, W - 10, 22);
    for (const it of g.items) ccCookie(c, it.x, it.y, it.kind);
    drawGrid(c, grid(g.kind, g.color, { t, face: "happy" }), g.x - 32, top, 4);
    c.textAlign = "center"; c.font = "800 13px " + FONT;
    g.pops = g.pops.filter((q) => t - q[4] < 0.7);
    for (const q of g.pops) { c.fillStyle = q[3]; c.fillText(q[2], q[0], q[1] - 16 - (t - q[4]) * 40); }
    requestAnimationFrame(ccStep);
  }
  function ccFinish() {
    const g = catchGame; g.running = false;
    const p = pets.includes(g.pet) ? g.pet : null, hearts = Math.min(CC.maxHearts, Math.floor(g.score / 3));
    if (hearts) reward(p, hearts);
    const spiky = EVENT.kinds.includes(AWAKEN_BASE[g.kind] || g.kind), pts = spiky ? Math.min(10, Math.floor(g.score / 5)) : 0;
    if (pts && p) eventPoint(p, pts);
    if (p) bondUp(p, "catch");
    questTick("catch", g.score);
    const best = g.score > stat("catch_best"); if (best) save.stats.catch_best = g.score;
    persist(true); sfx(best ? "fanfare" : "pop");
    ccTitle(`You caught ${g.score}! +${hearts} 💖${pts ? ` +${pts} ${EVENT.icon}` : ""}${best ? "  🏆 New best!" : ""}`);
  }
  {
    const cv = $("catchCanvas");
    const aimAt = (e) => { if (!catchGame) return; const r = cv.getBoundingClientRect(); catchGame.aim = (e.clientX - r.left) * (cv.width / r.width); };
    cv.addEventListener("pointerdown", (e) => { if (catchGame && !catchGame.running) ccStart(); aimAt(e); });
    cv.addEventListener("pointermove", aimAt);
    document.addEventListener("keydown", (e) => {
      if (!catchGame || $("catchSheet").hidden) return;
      if (e.key === "ArrowLeft" || e.key === "ArrowRight") { catchGame.aim = null; catchGame.x = clamp(catchGame.x + (e.key === "ArrowLeft" ? -24 : 24), 24, cv.width - 24); e.preventDefault(); }
      if (e.key === " " && !catchGame.running) { ccStart(); e.preventDefault(); }
    });
  }
  $("sheetCatch").onclick = () => sheetPet && openCatch(sheetPet);
  // ------------------------------------------------------------------ 💬 chats: pick ready-made lines, the Blip answers (blip.pyw CHATS)
  const CHATS = D.chats || {};
  const chatTree = (p) => CHATS[AWAKEN_BASE[p.kind] || p.kind] || D.chatDefault;       // everyone can chat; some have their own
  function chatText(p, text) {                    // fill in the {blanks} for this Blip, right now (same as blip.pyw)
    const k = KINDS[p.kind];
    if (text.includes("{mood}")) text = text.replace("{mood}", p.hunger > 70 ? "honestly? kinda hungry… *tummy rumbles*" : p.energy < 30 ? "sleepy… *yawn*"
      : bondLevel(p.bond || 0) >= 3 ? "the best! hanging out with you is my favorite" : "pretty good! thanks for asking :)");
    if (text.includes("{cute}")) text = text.replace("{cute}", pick(k.pet_lines || ["*happy wiggle* you think so?!", "aww, stop it! (don't stop)", "*blushes* hehe"]));
    if (text.includes("{snack}")) text = text.replace("{snack}", p.hunger > 40 ? "ooh, yes please! *hungry eyes*" : "i'm pretty full… but i'd never say no to a cookie");
    if (text.includes("{line}")) text = text.replace("{line}", pick(linesFor(p)));
    return text.replaceAll("{name}", p.name).replaceAll("{kind}", p.kind);
  }
  let chatPet = null;
  function openChat(p) {
    if (!chatTree(p)) return;
    chatPet = p; closeSheets(); openSheet("chatSheet");
    $("chatWho").textContent = `💬 ${p.name} (${p.kind})`;
    chatShow("start");
  }
  function chatShow(node) {
    const p = chatPet, tree = p && chatTree(p);
    if (!tree || node === "end" || !tree[node]) { chatEnd(); return; }
    const n = tree[node], text = chatText(p, n.say);
    if (n.blush) p.blushUntil = now() + 2.5;
    $("chatLine").textContent = text; say(p, text, 4); setFace(p, "happy", 1.2); sfx("boop"); drawChatFace(p);
    if (n.action === "feed") feed(p);              // a real cookie
    const box = $("chatOpts"); box.innerHTML = "";
    for (const [text, nxt] of n.options) { const b = document.createElement("button"); b.textContent = `➜ ${text}`; b.onclick = () => chatShow(nxt); box.appendChild(b); }
  }
  function scale2x(g) {                          // smooth pixel-art upscale (EPX), same as blip.pyw
    const h = g.length, w = g[0].length, out = Array.from({ length: h * 2 }, () => Array(w * 2).fill(null));
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const P = g[y][x], A = y ? g[y - 1][x] : P, B = x < w - 1 ? g[y][x + 1] : P, C = x ? g[y][x - 1] : P, Dn = y < h - 1 ? g[y + 1][x] : P;
      out[2 * y][2 * x] = C === A && C !== Dn && A !== B ? C : P; out[2 * y][2 * x + 1] = A === B && A !== C && B !== Dn ? A : P;
      out[2 * y + 1][2 * x] = Dn === C && Dn !== B && C !== A ? C : P; out[2 * y + 1][2 * x + 1] = B === Dn && B !== A && Dn !== C ? B : P;
    }
    return out;
  }
  function drawChatFace(p) {                     // 💬 a hand-drawn half-torso portrait if the Blip has one, else its sprite upscaled
    const cv = $("chatPortrait"), c = cv.getContext("2d"), k = KINDS[p.kind], t = now(), blushing = t < (p.blushUntil || 0);
    const pal = Object.assign({}, k.colors[p.color % k.colors.length], k.extra || {});
    let g;
    if (k.portrait && !pal.art && !plushNow(p.kind)) {
      if (!pal.b) pal.b = pal.s || pal.o;            // "*" shines are a light version of the plating
      if (!pal.h) pal.h = pal.s || pal.o;            // "h" helmet pieces match the plating (and don't blush)
      const bpal = blushing && k.blush ? Object.assign({}, pal, k.blush.pal) : pal, [r0, r1] = k.portrait.rows;
      g = k.portrait.art.map((row, y) => [...row].map((ch) => (ch === "." ? null : pxColor(blushing && y >= r0 && y <= r1 ? bpal : pal, ch))));
    } else g = scale2x(grid(p.kind, p.color, { t, face: "happy", blush: blushing }));
    c.clearRect(0, 0, cv.width, cv.height);
    const s = Math.min(Math.floor(cv.width / g[0].length), Math.floor(cv.height / g.length)), x0 = (cv.width - g[0].length * s) / 2, y0 = cv.height - g.length * s;
    g.forEach((row, y) => row.forEach((col, x) => { if (col) { c.fillStyle = col; c.fillRect(x0 + x * s, y0 + y * s, s, s); } }));
    if (blushing) setTimeout(() => { if (chatPet === p) drawChatFace(p); }, 2600);     // cool back down
  }
  function chatEnd() {
    const p = chatPet; chatPet = null; closeSheets();
    if (p && pets.includes(p) && now() - (p.lastChat || -999) > 120) { p.lastChat = now(); bondUp(p, "chat"); persist(); }
  }
  $("sheetChat").onclick = () => sheetPet && openChat(sheetPet);
  // ------------------------------------------------------------------ 🧸 Bad Dreams: fend one off for 5 seconds (same rules as blip.pyw)
  let dreamGame = null, dreamRest = 0;
  const DREAM_HOW = { "Bad Dream Bear": "It's slow… but it never stops.", "Bad Dream Bunny": "It hops! Don't lose it.",
                      "Bad Dream Hen": "It zigzags side to side.", "Bad Dream Fox": "It's FAST. Stay on it!", "Bad Dream Hare": "It winds up… then dashes!" };
  const BEAM = 40;
  const dreamArt = {};
  function dreamCanvas(kind, eyesOnly) {          // the big 32 x 30 art, drawn once into a little canvas
    const key = kind + (eyesOnly ? "!" : "");
    if (dreamArt[key]) return dreamArt[key];
    const a = D.badDreams[kind], k = KINDS[kind], pal = { n: "#1a1024", u: "#1a1024", z: "#c8ccd8", g: "#ffd23a", l: "#f4ece0", ...k.colors[0] };
    const mix = (x, y, f) => "#" + [1, 3, 5].map((i) => Math.round(parseInt(x.slice(i, i + 2), 16) * (1 - f) + parseInt(y.slice(i, i + 2), 16) * f).toString(16).padStart(2, "0")).join("");
    Object.assign(pal, { c: pal.t || "#f0e4c8", h: "#ffffff", "%": mix(pal.b, pal.e, 0.45) });
    const cv = document.createElement("canvas"); cv.width = 32; cv.height = 30; const c = cv.getContext("2d");
    a.big.forEach((row, y) => [...row].forEach((ch, x) => { if (ch !== "." && (!eyesOnly || "eh%".includes(ch))) { c.fillStyle = pxColor(pal, ch); c.fillRect(x, y, 1, 1); } }));
    return (dreamArt[key] = cv);
  }
  function badDreamRewrite(pm) {
    const t = now();
    if (dreamGame && (dreamGame.pending || !$("dreamSheet").hidden)) return;
    if (t < dreamRest) { say(pm, `*the strings are tangled…* (try again in ${Math.ceil(dreamRest - t)}s)`, 2.5); return; }
    if (!save.badDreams.includes("Bad Dream Puppet Master")) {
      save.badDreams.push("Bad Dream Puppet Master"); pm.kind = "Bad Dream Puppet Master"; pm.color = 0; pm.plushMode = plushNow(pm.kind);
      dreamBurst(pm, false); say(pm, "*snip* …the strings go both ways now 🎭", 3); persist(true);
    }
    const left = DREAM_ROBOS.filter((k) => !save.badDreams.includes(k));
    if (!left.length) { say(pm, "all my Bad Dreams are yours… sweet dreams 🧸", 3); return; }
    const inTown = left.filter((k) => pets.some((p) => p.kind === D.badDreams[k].robo)), kind = pick(inTown.length ? inTown : left);
    for (const p of pets) if (p.kind === D.badDreams[kind].robo) say(p, "*whirr… rrrip… stitches?*", 2.5);
    dreamRest = t + 30; dreamGame = { pending: true };
    setTimeout(() => openDream(kind), 1400);
  }
  function openDream(kind) {
    closeSheets(); openSheet("dreamSheet");
    const cv = $("dreamCanvas");
    dreamGame = { kind, robo: D.badDreams[kind].robo, state: "intro", t0: now(), last: now(), z: 0.25, lit: false, x: cv.width / 2, y: cv.height / 2 + 14,
                  mx: cv.width / 2, my: cv.height / 2, goal: [cv.width / 2, cv.height / 2 + 14], nextMove: 0, wind: 0 };
    sfx("boing"); vibrate(60); requestAnimationFrame(dreamStep);
  }
  const dreamScale = (g) => 2 + g.z * 4;
  function dreamStep() {
    const g = dreamGame; if (!g || g.pending) return;
    const cv = $("dreamCanvas");
    if ($("dreamSheet").hidden) { dreamGame = null; return; }
    const t = now(), dt = Math.min(0.05, t - g.last); g.last = t;
    if (g.state === "intro" && t - g.t0 > 2.2) { g.state = "play"; g.t0 = t; }
    if (g.state === "play") dreamUpdate(g, cv, t - g.t0, dt);
    dreamDraw(g, cv, t);
    if (g.state === "intro" || g.state === "play") requestAnimationFrame(dreamStep);
  }
  function dreamUpdate(g, cv, t, dt) {          // 🔦 keep it in the beam: lit it backs off, in the dark it creeps closer
    const W = cv.width, H = cv.height, spot = () => [rnd(50, W - 50), rnd(70, H - 56)];
    let speed = 0;
    if (g.kind === "Bad Dream Bear") { if (t >= g.nextMove) { g.goal = spot(); g.nextMove = t + 1.6; } speed = 50; }
    else if (g.kind === "Bad Dream Bunny") { if (t >= g.nextMove) { g.goal = spot(); g.nextMove = t + rnd(0.75, 1.05); sfx("boop"); } speed = 650; }
    else if (g.kind === "Bad Dream Hen") { g.goal = [W / 2 + Math.sin(t * 2.4) * (W / 2 - 70), H / 2 + 14 + Math.sin(t * 4.8) * 50]; speed = 290; }
    else if (g.kind === "Bad Dream Fox") { if (t >= g.nextMove) { g.goal = spot(); g.nextMove = t + rnd(0.45, 0.65); } speed = 275; }
    else { g.wind += dt / 1.1; if (g.wind >= 1) { g.wind = 0; g.goal = spot(); sfx("whoosh"); } if (Math.hypot(g.goal[0] - g.x, g.goal[1] - g.y) > 2) speed = 470; }
    const d = Math.hypot(g.goal[0] - g.x, g.goal[1] - g.y);
    if (d > 0.5) { const f = Math.min(1, speed * dt / d); g.x += (g.goal[0] - g.x) * f; g.y += (g.goal[1] - g.y) * f; }
    g.lit = Math.hypot(g.mx - g.x, g.my - g.y) < BEAM + 3 * dreamScale(g);
    g.z = g.lit ? Math.max(0.1, g.z - 0.25 * dt) : g.z + 0.38 * dt;
    if (g.z >= 1) { g.state = "lost"; sfx("boing"); vibrate(200); }
    else if (t >= 5) {
      g.state = "won";
      if (!save.badDreams.includes(g.kind)) save.badDreams.push(g.kind);
      const shadow = `${g.robo}:Shadow`; save.skins = save.skins || [];
      if (KINDS[g.robo].colors.some((c) => c.name === "Shadow") && !save.skins.includes(shadow)) save.skins.push(shadow);
      reward(null, 15); sfx("fanfare"); vibrate([30, 40, 30]);
      const np = addPet(g.kind, { quiet: true }); if (np) say(np, "…okay. you can keep me. 🧸", 4);
      persist(true); checkTrophies();
    }
  }
  function dreamDraw(g, cv, now_) {
    const c = cv.getContext("2d"), W = cv.width, H = cv.height, name = g.kind.replace("Bad Dream ", "");
    c.imageSmoothingEnabled = false;
    const sprite = (cx, cy, s, eyesOnly) => c.drawImage(dreamCanvas(g.kind, eyesOnly), Math.round(cx - 16 * s), Math.round(cy - 15 * s), 32 * s, 30 * s);
    const text = (str, x, y, size, color, align = "center") => { c.font = `800 ${size}px ${FONT}`; c.fillStyle = color; c.textAlign = align; c.textBaseline = "middle"; c.fillText(str, x, y); };
    const beam = () => { c.fillStyle = "#1e1a24"; c.beginPath(); c.arc(g.mx, g.my, BEAM + 10, 0, Math.PI * 2); c.fill(); c.fillStyle = "#3a3424"; c.beginPath(); c.arc(g.mx, g.my, BEAM, 0, Math.PI * 2); c.fill(); };
    c.fillStyle = "#0c0b14"; c.fillRect(0, 0, W, H);
    if (g.state === "intro") {
      beam(); text("🎭 The strings go taut…", W / 2, 30, 15, "#c8a0d8"); text(`The Puppet Master rewrote ${g.robo}!`, W / 2, 54, 11.5, "#e8e4ff");
      sprite(g.x, g.y, dreamScale(g), Math.floor(now_ * 4) % 2 === 0);
      text("🔦 Keep it in your light for 5 seconds!", W / 2, H - 30, 12, "#ffd23a"); text(DREAM_HOW[g.kind] + " (drag your finger or mouse)", W / 2, H - 11, 9.5, "#9a94c0"); return;
    }
    if (g.state === "won" || g.state === "lost") {
      const won = g.state === "won"; c.fillStyle = won ? "#1a1630" : "#14081a"; c.fillRect(0, 0, W, H);
      sprite(W / 2, won ? H - 80 : H / 2 + 40, won ? 3 : 5);
      c.fillStyle = won ? "#1a1630" : "#14081a"; c.fillRect(0, 0, W, 96);
      if (won) { text(`You kept the Bad Dream ${name}! 🧸`, W / 2, 26, 15, "#ffd23a"); text(`+15 💖 · ${g.robo}'s Shadow color unlocked`, W / 2, 52, 10.5, "#e8e4ff"); text("(it's a plushie until midnight)", W / 2, 74, 10, "#9a94c0"); }
      else { text("GOTCHA! 🧸", W / 2, 28, 20, "#ff4a6a"); text(`The Bad Dream ${name} gave you a big stuffed hug.`, W / 2, 56, 10.5, "#e8e4ff"); text("Tap a Puppet Master 5 times to try again (after a little rest).", W / 2, 78, 9.5, "#9a94c0"); }
      return;
    }
    const t = now_ - g.t0;
    beam(); sprite(g.x, g.y, dreamScale(g), !g.lit);
    if (g.kind === "Bad Dream Hare" && g.wind > 0.6) text("*tick tick tick*", g.x, g.y - 18 * dreamScale(g), 10, "#d8b04a");
    c.fillStyle = "#08070e"; c.fillRect(0, 0, W, 26);
    text(`🔦 KEEP IT IN THE LIGHT  ${Math.max(0, 5 - t).toFixed(1)}s`, 8, 13, 11, "#e8e4ff", "left");
    c.fillStyle = "#3a3360"; c.fillRect(W - 94, 6, 86, 14); c.fillStyle = "#101018"; c.fillRect(W - 92, 8, 82, 10);
    c.fillStyle = "#ff4a6a"; c.fillRect(W - 92, 8, 82 * Math.min(1, g.z), 10);
  }
  {
    const cv = $("dreamCanvas");
    const aim = (e) => { const g = dreamGame; if (!g || g.pending) return; const r = cv.getBoundingClientRect(); g.mx = (e.clientX - r.left) * (cv.width / r.width); g.my = (e.clientY - r.top) * (cv.height / r.height); };
    cv.addEventListener("pointermove", aim); cv.addEventListener("pointerdown", aim);
  }
  // ⭐ secret codes (creator code; early access codes work here too) and the creator's dev sheet
  $("secretGo").onclick = async () => {
    const code = normCode($("secretCode").value);
    if (!code) return;
    const h = await sha256(code);
    if (D.creator && h === D.creator.hash) {
      try { localStorage.setItem("blipville-creator", h); } catch (e) { /* private mode */ }
      sfx("fanfare"); $("secretMsg").textContent = "⭐ Welcome back, creator! Blipmaker and Byte are yours. Tap 🛠️ at the top.";
      $("devBtn").hidden = false; devAddCreators(); persist(true);
    } else if ((D.modHashes || []).includes(h)) {
      try { localStorage.setItem("blipville-mod", h); } catch (e) { /* private mode */ }
      sfx("fanfare"); $("secretMsg").textContent = "🛡️ Welcome to the mod squad! Guardian is yours. Tap 🛠️ at the top.";
      $("devBtn").hidden = false; modMode();
      if (!pets.some((p) => p.kind === "Guardian")) { const p = addPet("Guardian", { name: "Guardian", quiet: true }); if (p) say(p, "🛡️ mod squad, reporting in!", 4); }
      giveCodeKinds();
      persist(true);
    } else if (EARLY_HASHES.includes(h)) {
      try { localStorage.setItem(EARLY_KEY, code); } catch (e) { /* private mode */ }
      $("secretMsg").textContent = "🎟️ Early access code saved on this device!";
    } else if (merchPrefix(code)) await redeemMerch(code);
    else $("secretMsg").textContent = "Hmm, that code doesn't do anything.";
  };
  // 🎟️ merch codes (same rules as blip.pyw): only a slow fingerprint of each code is known, never the code itself
  const MERCH = D.merch || { items: {}, hashes: [] };
  const merchPrefix = (code) => Object.keys(MERCH.items).find((p) => code.startsWith(p.replace(/-/g, "")) && code.length === p.replace(/-/g, "").length + 8);
  async function merchFingerprint(code) {
    const enc = new TextEncoder(), key = await crypto.subtle.importKey("raw", enc.encode(code), "PBKDF2", false, ["deriveBits"]);
    const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", salt: enc.encode(MERCH.salt), iterations: MERCH.rounds, hash: "SHA-256" }, key, 256);
    return [...new Uint8Array(bits)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  async function redeemMerch(code) {
    const msg = $("secretMsg"), prefix = merchPrefix(code), m = MERCH.items[prefix];
    msg.textContent = "🎟️ Checking your code…";
    const fp = await merchFingerprint(code), known = new Set(MERCH.hashes || []);
    try { const r = await fetch(`${MERCH.url}?t=${Math.floor(Date.now() / 60000)}`, { cache: "no-store" }); if (r.ok) for (const h of (await r.json()).hashes || []) known.add(h); }
    catch (e) { /* offline: only the codes shipped with the game work */ }
    if (!known.has(fp)) { msg.textContent = "Hmm, that merch code doesn't work. Check the letters and try again!"; return; }
    let device = []; try { device = JSON.parse(localStorage.getItem("blipville-redeemed") || "[]"); } catch (e) { /* private mode */ }
    if (save.redeemed.includes(fp) || device.includes(fp)) { msg.textContent = "That code has already been used on this device. 🎟️"; return; }
    save.redeemed.push(fp); if (!save.merch.includes(prefix)) save.merch.push(prefix);
    try { localStorage.setItem("blipville-redeemed", JSON.stringify(device.concat(fp))); } catch (e) { /* private mode */ }
    sfx("fanfare"); vibrate([30, 40, 30]);
    if (m.kind) {
      const skin = `${m.kind}:${m.name}`; if (!save.skins.includes(skin)) save.skins.push(skin);
      save.merchKinds = save.merchKinds || []; if (!save.merchKinds.includes(m.kind)) save.merchKinds.push(m.kind);   // the Blip itself is yours too
      const p = addPet(m.kind, { quiet: true });
      if (p) { p.color = KINDS[m.kind].colors.findIndex((c) => c.name === m.name); say(p, "✨ merch link established. hello, keeper. ✨", 4); burst(p, "heart", 10); sparkle(p, 12); }
      msg.textContent = `✨ ${m.kind}: ${m.name} unlocked! Thanks for supporting Blipville. 💜`;
    } else msg.textContent = `✨ ${m.for}: ${m.name} is yours! The ${m.for} arrives in an update soon, and this skin will be waiting for you. 💜`;
    persist(true); checkTrophies();
  }
  function devAddCreators() {
    for (const [k, line] of [["Blipmaker", "the creator has arrived! 👑"], ["Byte", "*beep* ready to ship!"], ["Guardian", "🛡️ on duty!"]]) {
      if (!pets.some((p) => p.kind === k)) { const p = addPet(k, { name: k, quiet: true }); if (p) { say(p, line, 4); burst(p, "heart", 8); } }
    }
  }
  function devSpawn(group) {
    let pool = (D.groups[group] || []).slice();
    if (group === "legends") pool = pool.filter((k) => save.world && LEGEND_WORLD[k] === save.world);
    if (!pool.length) { toast("Legends only show up while you're visiting a world! 🌍", 3); return; }
    const locked = pool.filter((k) => !isUnlocked(k)); closeSheets();
    startSighting(pick(locked.length ? locked : pool));
  }
  function modMode() {                                    // moderators get a smaller menu
    if (isCreator()) return;
    ["devHearts", "devEvent", "devUnlock", "devCreators"].forEach((id) => { $(id).hidden = true; });
    $("devTitle").textContent = "🛡️ Mod menu"; $("devNote").textContent = "For checking reports and running events. Thanks for modding! 🛡️";
  }
  $("devBtn").hidden = !(isCreator() || isMod());
  if (isMod()) modMode();
  $("devBtn").onclick = () => openSheet("devSheet");
  $("devHearts").onclick = () => { reward(pets[0], 100); toast("💖 +100 hearts", 1.5); };
  $("devCryptid").onclick = () => devSpawn("cryptids");
  $("devKaiju").onclick = () => devSpawn("kaiju");
  $("devGhost").onclick = () => devSpawn("ghosts");
  $("devLegend").onclick = () => devSpawn("legends");
  $("devEvent").onclick = () => { eventPoint(pets[0], 10, true); toast(`${EVENT.icon} +10 event points`, 1.5); };
  $("devQuests").onclick = () => { save.quests = null; persist(true); toast("📅 Fresh quests: " + todaysQuests(todayStr()).map((q) => q.text).join(" · "), 5); };
  $("devUnlock").onclick = () => {
    save.hatched = [...D.groups.rare]; save.cryptids = [...D.groups.cryptids]; save.kaiju = [...D.groups.kaiju];
    save.ghosts = [...D.groups.ghosts]; save.legends = [...D.groups.legends]; save.worlds = WORLDS.map((w) => w.name);
    save.nightsWon = Math.max(4, save.nightsWon); save.awakened = Object.keys(AWAKEN_CHAIN);
    save.awakenLevel = Object.fromEntries(Object.entries(AWAKEN_CHAIN).map(([b, ch]) => [b, ch.length]));
    persist(true); sfx("fanfare"); toast("🔓 Everything's unlocked!", 2.5);
  };
  $("devCreators").onclick = () => { devAddCreators(); closeSheets(); };
  $("devBoss").onclick = async () => {
    const code = battleCodeFor(D.creator.boss[0], D.creator.boss[1]);
    try { await navigator.clipboard.writeText(code); toast("🥊 Boss battle code copied! Share it on the Discord.", 4); }
    catch (e) { prompt("Your boss battle code:", code); }
  };


  // ------------------------------------------------------------------ events 🎉 (the same event as the desktop app)
  const EVENTS = D.events || (D.event ? [D.event] : []);        // the one that is on, or the next one coming (the last stays up after it ends)
  const _today = (() => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; })();
  const EVENT = EVENTS.find((e) => _today <= e.until) || EVENTS[EVENTS.length - 1] || { id: "", name: "", icon: "🎉", kinds: [], rewards: [], per_skin: 10, start: "9999", until: "0000" };
  const EVENTK = new Set(D.groups.eventKinds || []);
  const todayStr = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
  const eventPaused = () => !!(EVENT.paused && EVENT.paused[0] <= todayStr() && todayStr() < EVENT.paused[1]);   // closed for maintenance
  const eventOn = () => EVENT.start <= todayStr() && todayStr() <= EVENT.until && !eventPaused();
  function skinLocked(kind, i) {
    const cols = KINDS[kind].colors, col = cols[i % cols.length];
    return !!(col.event || col.unlock) && !(save.skins || []).includes(`${kind}:${col.name}`);
  }
  const eventPts = () => +((save.eventPoints || {})[EVENT.id] || 0);
  // the reward track: [{ type: "skin" | "blip", kind, skin?, at }]. An event can list its own `tiers`; the older ones (skins only,
  // every per_skin points) are turned into tiers here.
  const eventTiers = () => EVENT.tiers || EVENT.rewards.map(([kind, skin], i) => ({ type: "skin", kind, skin, at: (i + 1) * EVENT.per_skin }));
  const tierKey = (t) => (t.type === "blip" ? `blip:${t.kind}` : `${t.kind}:${t.skin}`);
  const tierGot = (t) => (t.type === "blip" ? (save.eventKinds || []).includes(t.kind) : (save.skins || []).includes(tierKey(t)));
  function eventPoint(p, n, anyKind = false) {
    if (n <= 0 || !eventOn() || !p || (!anyKind && !EVENT.kinds.includes(AWAKEN_BASE[p.kind] || p.kind))) return;
    save.eventPoints = save.eventPoints || {}; save.skins = save.skins || []; save.eventKinds = save.eventKinds || [];
    const before = eventPts(); save.eventPoints[EVENT.id] = before + n;
    for (const t of eventTiers()) {
      if (before + n < t.at || tierGot(t)) continue;
      sfx("fanfare"); vibrate([20, 30, 20]); setFace(p, "happy", 2); burst(p, "heart", 6);
      if (t.type === "blip") { save.eventKinds.push(t.kind); say(p, `🎁 a new friend: ${t.kind}! ✨`, 4); toast(`${EVENT.icon} New Blip unlocked: ${t.kind}! Find it in your 📖 Zoo. ✨`, 5); }
      else { save.skins.push(tierKey(t)); say(p, `🎁 new skin unlocked: ${t.skin} ${t.kind}! ✨`, 4); toast(`${EVENT.icon} New skin: ${t.skin} ${t.kind}! Pick it in its color list. ✨`, 4); }
    }
    persist(true);
    if (!$("eventSheet").hidden) openEvent();
  }

  // daily quests 📅 (the same 3 for everyone each day, like the desktop app)
  const QUESTS = (D.quests || []).map((q) => (q.id === "pet_spiky" && EVENT.kinds.length ? { ...q, text: `Pet a ${EVENT.kinds.slice(0, -1).join(", ")} or ${EVENT.kinds[EVENT.kinds.length - 1]} 8 times` } : q)), QR = D.questRewards || { hearts: 10, points: 5, bonus: 5 };
  const todaysQuests = (day) => [...QUESTS].sort((a, b) => fnvQ(day + a.id) - fnvQ(day + b.id)).slice(0, 3);
  function fnvQ(t) { let h = 2166136261; for (const b of new TextEncoder().encode(t)) h = Math.imul(h ^ b, 16777619) >>> 0; return h; }
  function questState() {
    const day = todayStr();
    if (!save.quests || save.quests.day !== day) save.quests = { day, progress: {}, done: [] };
    return save.quests;
  }
  function questTick(what, n = 1) {
    if (eventPaused()) return;                              // daily quests pause with the event
    const q = questState();
    for (const quest of todaysQuests(q.day)) {
      if (quest.id !== what || q.done.includes(what)) continue;
      q.progress[what] = (q.progress[what] || 0) + n;
      if (q.progress[what] >= quest.goal) {
        q.done.push(what);
        const p = pets[0], pts = QR.points + (q.done.length === 3 ? QR.bonus : 0);
        reward(p, QR.hearts); if (eventOn()) eventPoint(p, pts, true);
        sfx("fanfare");
        toast(`📅 Quest done: ${quest.text}! +${QR.hearts} 💖${eventOn() ? ` +${pts} ${EVENT.icon}` : ""}`, 4);
      }
      persist();
      if (!$("eventSheet").hidden) openEvent();
    }
  }
  function drawQuests() {
    const q = questState(), box = $("questList"); box.innerHTML = "";
    $("questNote").textContent = `each: +${QR.hearts} 💖` + (eventOn() ? ` +${QR.points} ${EVENT.icon} (all 3: +${QR.bonus} more)` : "") + " · new ones every day";
    for (const quest of todaysQuests(q.day)) {
      const done = q.done.includes(quest.id), row = doc().createElement("div"); row.className = "quest" + (done ? " done" : "");
      const t = doc().createElement("span"); t.textContent = (done ? "✅ " : "⬜ ") + quest.text;
      const n = doc().createElement("b"); n.textContent = `${Math.min(q.progress[quest.id] || 0, quest.goal)}/${quest.goal}`;
      row.append(t, n); box.appendChild(row);
    }
  }
  function openEvent() {
    drawQuests();
    const tiers = eventTiers(), total = tiers[tiers.length - 1].at, pts = Math.min(eventPts(), total);
    $("eventTitle").textContent = `${EVENT.icon} ${EVENT.name}`; if (EVENT.blurb) $("eventBlurb").textContent = EVENT.blurb;
    if (eventPaused() && window.CountdownStars && CountdownStars.live()) CountdownStars.mount($("cdHost"));   // while Spiky Week is paused
    $("eventWhen").textContent = eventOn() ? `until ${EVENT.until_text}` : eventPaused() ? `paused until ${EVENT.paused_text}` : todayStr() < EVENT.start ? "starts soon!" : "this event is over";
    const next = tiers.find((t) => pts < t.at), prev = tiers.filter((t) => t.at <= pts).pop(), from = prev ? prev.at : 0;
    $("eventPtsBig").textContent = pts;
    $("eventFill").style.width = `${next ? (100 * (pts - from)) / (next.at - from) : 100}%`;
    $("eventPts").textContent = next ? `${pts - from} / ${next.at - from}` : "all rewards unlocked!";
    $("evNextLabel").textContent = next ? `Next: ${next.type === "blip" ? next.kind : `${next.skin} ${next.kind}`} · ${next.at - pts} to go` : "🎉 You earned everything!";
    const tr = $("evTrack"), keepScroll = $("eventSheet").hidden ? null : tr.scrollLeft; tr.innerHTML = "";
    tiers.forEach((t, i) => {
      const have = tierGot(t), reached = pts >= t.at, cell = doc().createElement("div");
      cell.className = "evTier" + (have ? " got" : "") + (t.type === "blip" ? " blip" : "") + (t === next ? " next" : "");
      const badge = doc().createElement("div"); badge.className = "evNum"; badge.textContent = i + 1; cell.appendChild(badge);
      const cost = doc().createElement("div"); cost.className = "evCost"; cost.textContent = `${t.at} pts`; cell.appendChild(cost);
      const card = doc().createElement("div"); card.className = "evCard";
      const idx = t.type === "blip" ? (KINDS[t.kind].default ?? 0) : Math.max(0, KINDS[t.kind].colors.findIndex((c) => c.name === t.skin));
      card.appendChild(thumb(t.kind, idx, !have && t.type === "blip", 4));
      const nm = doc().createElement("b"); nm.textContent = t.type === "blip" ? t.kind : t.skin; card.appendChild(nm);
      const sub = doc().createElement("small"); sub.textContent = t.type === "blip" ? "NEW BLIP" : `${t.kind} skin`; card.appendChild(sub);
      const tag = doc().createElement("div"); tag.className = "evTag"; tag.textContent = have ? "✓ UNLOCKED" : reached ? "READY" : "🔒 LOCKED"; card.appendChild(tag);
      cell.appendChild(card); tr.appendChild(cell);
    });
    const dots = $("evDots"); dots.innerHTML = ""; const pages = Math.max(1, Math.ceil(tiers.length / 2));
    for (let i = 0; i < pages; i++) { const d = doc().createElement("i"); d.dataset.p = i; dots.appendChild(d); }
    const go = (dir) => { const w = tr.firstElementChild ? tr.firstElementChild.getBoundingClientRect().width + 10 : 120; tr.scrollBy({ left: dir * w * 2, behavior: "smooth" }); };
    $("evPrev").onclick = () => go(-1); $("evNext").onclick = () => go(1);
    const mark = () => { const w = tr.firstElementChild ? tr.firstElementChild.getBoundingClientRect().width + 10 : 120; const pg = Math.round(tr.scrollLeft / (w * 2)); dots.querySelectorAll("i").forEach((d, i) => d.classList.toggle("on", i === pg)); };
    tr.onscroll = mark; mark();
    const slot = () => (tr.firstElementChild ? tr.firstElementChild.getBoundingClientRect().width + 10 : 120);
    if (keepScroll != null) tr.scrollLeft = keepScroll;                                   // a refresh keeps its place
    else view.requestAnimationFrame(() => view.requestAnimationFrame(() => { tr.scrollLeft = Math.max(0, ((next ? tiers.indexOf(next) : tiers.length - 2) - 1) * slot()); mark(); }));   // opens on the next reward
    const add = $("eventAdd"); add.innerHTML = "";
    const has = new Set(pets.map((q) => AWAKEN_BASE[q.kind] || q.kind));
    EVENT.kinds.filter((k) => !has.has(k)).forEach((k) => {
      const b = doc().createElement("button"); b.textContent = `➕ Add ${/^[AEIOU]/.test(k) ? "an" : "a"} ${k}`;
      b.onclick = () => { const q = addPet(k); if (q) say(q, `${EVENT.name.toLowerCase()}, let's go!`, 3); openEvent(); };
      add.appendChild(b);
    });
    openSheet("eventSheet");
  }
  $("eventBtn").hidden = false;           // events and daily quests
  $("eventBtn").textContent = EVENT.icon; $("eventBtn").title = `${EVENT.name} event`; $("eventBtn").setAttribute("aria-label", EVENT.name);
  $("eventBtn").onclick = openEvent;
  if (eventOn() && save.eventSeen !== EVENT.id) {
    setTimeout(() => { save.eventSeen = EVENT.id; persist(true);
      toast(`${EVENT.icon} ${EVENT.name} is on! ${EVENT.hello || ""} Tap ${EVENT.icon} at the top!`, 7); }, 5000);
  }

  $("shareBtn").onclick = share;
  $("helpBtn").onclick = () => openSheet("helpSheet");
  $("soundBtn").onclick = () => setSound(!save.sound);
  setSound(!!save.sound, true);
  $("helpEggCost").textContent = EGG_COST;

  function onKey(e) {
    if (e.target && (e.target.tagName === "INPUT" || e.target.isContentEditable) || e.ctrlKey || e.metaKey || e.altKey) return;
    const open = [...doc().querySelectorAll(".sheet")].some((s) => !s.hidden);
    if (e.key === "Escape") { closeSheets(); return; }
    if (open) return;
    const k = e.key.toLowerCase();
    const act = { f: "feedBtn", n: "friendBtn", e: "eggBtn", z: "collectionBtn", g: "ghostBtn", s: "shareBtn", "?": "helpBtn", p: "popBtn" }[k];
    if (act && $(act) && !$(act).hidden) { e.preventDefault(); $(act).click(); }
    else if (k === " ") {                                   // space pets the Blip under the mouse
      const p = petAt(pointer.x, pointer.y); if (p) { e.preventDefault(); petIt(p); }
    }
  }
  document.addEventListener("keydown", onKey);

  // 📌 Pop out: put the town in a small always-on-top window (Chrome / Chromebook "Document Picture-in-Picture")
  const canPop = "documentPictureInPicture" in window && window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  if (canPop) $("popBtn").hidden = false;
  $("popBtn").onclick = async () => {
    if (view !== window) { view.close(); return; }
    let pip;
    try { pip = await window.documentPictureInPicture.requestWindow({ width: 560, height: 300 }); }
    catch (e) { toast("Couldn't pop out here. Try Chrome on a laptop or Chromebook."); return; }
    for (const sheet of document.styleSheets) {
      try {
        const st = pip.document.createElement("style");
        st.textContent = [...sheet.cssRules].map((r) => r.cssText).join("\n"); pip.document.head.appendChild(st);
      } catch (e) {
        const l = pip.document.createElement("link"); l.rel = "stylesheet"; l.href = sheet.href; pip.document.head.appendChild(l);
      }
    }
    pip.document.title = "Blipville";
    pip.document.body.classList.add("mini");
    const moved = [...document.body.children].filter((el) => el.tagName !== "SCRIPT" && el.id !== "popped");
    moved.forEach((el) => pip.document.body.appendChild(el));
    view = pip;                                        // switch first, so lookups find the moved elements
    $("popped").hidden = false;
    $("popBtn").innerHTML = "<span>⤢</span>Back";
    pip.addEventListener("resize", layout);
    pip.document.addEventListener("keydown", onKey);
    pip.addEventListener("pagehide", () => {
      const home = document.getElementById("popped");
      moved.forEach((el) => document.body.insertBefore(el, home));
      view = window;
      home.hidden = true;
      $("popBtn").innerHTML = "<span>📌</span>Pop out";
      layout(); startLoop(); persist(true);
    }, { once: true });
    layout(); startLoop();
  };
  $("popBack").onclick = () => { if (view !== window) view.close(); };

  // ⬇ Install app: Edge and Chrome (Windows laptops, Chromebooks, Android) can install Blipville as an app with its
  // own icon and window. The button only appears when the browser says it can, and never inside the installed app.
  const installed = () => window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  const wantsInstall = /[?&#]install\b/.test(location.search + location.hash);   // the website's "Get the app" link
  let installPrompt = null;
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault(); installPrompt = e;
    if (installed()) return;
    $("installBtn").hidden = false;
    if (wantsInstall) { $("installBtn").classList.add("nudge"); toast("Press ⬇ Install app at the top to add Blipville to this computer!", 6); }
  });
  $("installBtn").onclick = async () => {
    if (!installPrompt) { openSheet("helpSheet"); return; }
    installPrompt.prompt();
    const { outcome } = await installPrompt.userChoice.catch(() => ({}));
    if (outcome === "accepted") { installPrompt = null; $("installBtn").hidden = true; }
  };
  window.addEventListener("appinstalled", () => {
    installPrompt = null; $("installBtn").hidden = true;
    toast("Blipville is installed! Open it from the Start menu or your apps. 💜", 6);
  });
  if (wantsInstall && !installed()) setTimeout(() => {             // a browser that can't install from a button
    if (!installPrompt) toast("To install: use the install icon in the address bar, or ⋮ menu → Install. See ? for help.", 7);
  }, 4000);

  // ------------------------------------------------------------------ start
  layout();
  if (save.pets && save.pets.length) {
    const away = save.lastSeen ? (Date.now() - save.lastSeen) / 3.6e6 : 0;   // hours away
    for (const s of save.pets) {
      if (!KINDS[s.kind] || !(isUnlocked(s.kind) || WORLD_OF[s.kind])) continue;   // world Blips you had stay yours
      const p = makePet(s.kind, s.color, s.name);
      p.hunger = Math.min(100, (s.hunger ?? 10) + away * 8); p.energy = s.energy ?? 100; p.hat = s.hat || null; p.hat2 = save.slot2 ? (s.hat2 || null) : null; p.tints = s.tints || {}; p.bond = +s.bond || 0;
      pets.push(p);
    }
  }
  if (!pets.length) { addPet("Blip", { name: "Blip", quiet: true }); setTimeout(() => openSheet("helpSheet"), 900); }
  if (save.noticeSeen !== "rc1-0.4") {                // one-time thank-you for beta players
    const fresh = !save.hatched.length && !save.cryptids.length && save.hearts < 20;
    save.noticeSeen = "rc1-0.4";
    if (!fresh) setTimeout(() => { toast("💜 Thanks for playing the Blipville beta! This is Release Candidate 2, the last step before 1.0, with 100 new Blips and 5 new tabs.", 7); say(pets[0], "thank you for playing!! <3", 4); }, 1200);
  }
  const localDay = (d = new Date()) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  // Limited-time thank-you Blips. A gift only counts as delivered once it has actually walked into town (or, with a full
  // town, once the player was told it's in the Zoo), so reloading or closing the page early can't lose it.
  if (!save.giftsDelivered) save.giftsDelivered = save.gifts.filter((k) => k !== "Patch");   // older saves: those already arrived
  const cdDone = () => !!(window.CountdownStars && CountdownStars.done());   // ⭐ Countdown Stars (the maintenance event)
  const isTester = (() => { try { return !!localStorage.getItem("blipville-early-code") || isMod() || isCreator(); } catch (e) { return false; } })();   // used an early access code
  const drops = (D.giftDrops || (D.giftNow ? [{ kind: D.giftNow, until: D.giftUntil, why: "" }] : []))
    .filter((d) => !save.giftsDelivered.includes(d.kind) && (!d.until || localDay() <= d.until || save.gifts.includes(d.kind) || (d.countdown && cdDone()))
                   && (!d.start || localDay() >= d.start || save.gifts.includes(d.kind))
                   && (!d.testers || isTester || save.gifts.includes(d.kind))
                   && (!d.countdown || cdDone() || save.gifts.includes(d.kind)));
  const deliverGift = (d) => {
      if (save.giftsDelivered.includes(d.kind)) return;
      if (!save.gifts.includes(d.kind)) save.gifts.push(d.kind);
      save.giftsDelivered.push(d.kind);
      const here = pets.some((p) => p.kind === d.kind);
      const g = here ? null : addPet(d.kind, { quiet: true });
      if (g) { say(g, `surprise!! i'm ${d.kind}, a gift for you 🎁`, 5); setFace(g, "happy", 2); burst(g, "heart", 8); }
      toast(`🎁 ${d.why ? d.why + " " : ""}Here's ${d.kind}, a limited-edition Blip! ` +
            (g || here ? "It's in your 📖 Zoo under Gifts too." : "Your town is full, so it's waiting in your 📖 Zoo under Gifts."), 7);
      persist(true);
  };
  drops.forEach((d, i) => setTimeout(() => deliverGift(d), 2600 + i * 7500));
  if (window.CountdownStars) CountdownStars.onDone = () => {         // ⭐ finished Countdown Stars right here: Liftoff now
    const d = (D.giftDrops || []).find((x) => x.countdown);
    if (d) setTimeout(() => deliverGift(d), 600);
  };
  function giveCodeKinds() {                              // 💎 a moderator code's very own Blip arrives once
    save.codeGifts = save.codeGifts || [];
    for (const k of (D.modCodeKinds || {})[modCode()] || []) {
      if (save.codeGifts.includes(k)) continue;
      save.codeGifts.push(k);
      const g = pets.some((p) => p.kind === k) ? null : addPet(k, { quiet: true });
      if (g) { say(g, "✨ just for you! 💎", 5); setFace(g, "happy", 2); burst(g, "heart", 8); }
      toast(`💎 ${k} is yours, and only yours! A thank-you for helping run Blipville.`, 6); persist(true);
    }
  }
  setTimeout(giveCodeKinds, 2000);
  const today = localDay();          // 📅 the player's own calendar day, the same day quests and events use
  if (saveNote) setTimeout(() => toast(saveNote, 8), 6000);                  // 💾 tell the player what happened to a damaged save
  if (save.lastDay !== today) {
    // older saves stored the UTC date, which can be "tomorrow" in local time: that day's treat was already claimed
    const claimed = typeof save.lastDay === "string" && /^\d{4}-\d\d-\d\d$/.test(save.lastDay) && save.lastDay > today;
    save.lastDay = today;
    if (!claimed) {
      bump("days");
      setTimeout(() => { reward(pets[0], 10); say(pets[0], "daily treat! +10 💖", 4); }, 1600);
    }
  }
  updateHearts(false);
  persist();
  document.addEventListener("visibilitychange", () => { if (document.hidden) persist(true); });
  window.addEventListener("pagehide", () => persist(true));
  startLoop();
  if ("serviceWorker" in navigator && (location.protocol === "https:" || ["localhost", "127.0.0.1"].includes(location.hostname))) navigator.serviceWorker.register("sw.js").catch(() => {});
  // ------------------------------------------------------------------ Night Shift minigame
  // Survive 12 AM → 6 AM. Tap a doorway with glowing eyes to FLASH it and send that robo back to the stage.
  // A robo you're watching on camera can't move, but cameras and flashes use battery, and a camera left on one room
  // overheats after a few seconds (it switches off until it cools down). Each night won unlocks a robo.
  const NS = (() => {
    const HOUR = 20, CW = 360, CH = 300, MIDNIGHT = 3;
    const ROOMS = ["Stage", "Arcade", "Kitchen", "West Hall", "East Hall"];
    const NEXT = { Stage: ["Arcade", "Kitchen"], Arcade: ["West Hall"], Kitchen: ["East Hall"], "West Hall": ["door_L"], "East Hall": ["door_R"] };
    const NIGHTS = {
      1: { robots: ["Robo Bear"], interval: 6.0, chance: 0.55, grace: 3.4 },
      2: { robots: ["Robo Bear", "Robo Bunny"], interval: 4.4, chance: 0.66, grace: 2.2 },
      3: { robots: ["Robo Bear", "Robo Bunny", "Robo Hen"], interval: 3.9, chance: 0.75, grace: 1.9 },
      4: { robots: ["Robo Bear", "Robo Bunny", "Robo Hen", "Robo Fox"], interval: 3.7, chance: 0.78, grace: 1.7 },
    };
    const FAST = { "Robo Fox": 0.7 }, LAST = 4;   // 🦊 the fox moves sooner than the others
    const FLASH_COST = 3, DRAIN = 0.18, CAM_DRAIN = 0.3;
    const CAM_HOT = 8, CAM_COOL = 0.8;            // a camera overheats after 8 s on one room; cools 0.8 s per second off
    const DOORS = { L: [10, 110], R: [250, 350] };
    const cv = $("nsCanvas"), c = cv.getContext("2d");
    let g = { state: "menu" }, last = 0, raf = null, speed = 1, FONT = "sans-serif";

    const sprite = (kind, x, y, sc, face) => drawGrid(c, grid(kind, kind === "Blip" ? 0 : MIDNIGHT, { t: 0, face: face || "normal" }), x, y, sc);
    function text(str, x, y, size, color, align = "center", weight = 800) {
      c.font = `${weight} ${size}px ${FONT}`; c.fillStyle = color; c.textAlign = align; c.textBaseline = "middle";
      c.fillText(str, x, y);
    }
    function wrap(str, x, y, maxW, size, color, lh) {
      c.font = `600 ${size}px ${FONT}`;
      let line = "", yy = y;
      for (const w of str.split(" ")) {
        if (c.measureText(line + w).width > maxW && line) { text(line.trim(), x, yy, size, color, "center", 600); line = ""; yy += lh; }
        line += w + " ";
      }
      text(line.trim(), x, yy, size, color, "center", 600);
    }
    function say(str, secs = 2.5) { g.msg = str; g.msgUntil = g.t + secs; }

    function start(n) {
      const cfg = NIGHTS[n];
      g = { state: "play", night: n, cfg, t: 0, battery: 100, cam: null, heat: Object.fromEntries(ROOMS.map((r) => [r, 0])), hot: new Set(), flashUntil: -1, flashSide: null, flashed: null, msg: "", msgUntil: 0,
            robots: cfg.robots.map((k, i) => ({ kind: k, room: "Stage", next: rnd(4, 9) + i * 2.5, doorSince: null })) };
      say(`Night ${n}, good luck! 🔦`, 3); buttons();
    }
    function flash(side) {
      if (g.state !== "play") return;
      if (g.battery < FLASH_COST) { say("not enough battery to flash!"); return; }
      g.battery -= FLASH_COST; g.cam = null; g.flashUntil = g.t + 0.4; g.flashSide = side;
      const hit = g.robots.filter((r) => r.room === "door_" + side);
      g.flashed = hit.length ? hit[0].kind : null;
      for (const r of hit) { r.room = "Stage"; r.doorSince = null; r.next = g.t + g.cfg.interval * 1.3; }
      say(hit.length ? `*clank clank* ${hit[0].kind} ran back to the stage!` : "nothing there… this time.");
      sfx("zap"); vibrate(12); buttons();
    }
    function cam(room) {
      if (g.state !== "play" || g.battery <= 0) return;
      if (g.hot.has(room)) { say(`📷 the ${room} camera is still cooling down…`); return; }
      g.cam = room; buttons();
    }
    function won() {
      const first = g.night > save.nightsWon;
      const unlock = D.groups.nightShift.find((k) => D.unlocks[k] === g.night);
      g.newUnlock = unlock && !isUnlocked(unlock) ? unlock : null;
      save.nightsWon = Math.max(save.nightsWon, g.night);
      g.state = "won"; reward(null, first ? 25 : 10); persist(true); sfx("fanfare"); vibrate([30, 40, 30]); buttons();
    }
    function update(dt) {
      g.t += dt;
      g.battery = Math.max(0, g.battery - (DRAIN + (g.cam ? CAM_DRAIN : 0)) * dt);
      if (g.battery <= 0 && g.cam) { g.cam = null; say("the battery died… 🔋 lights out!", 4); buttons(); }
      for (const room of ROOMS) {                               // cameras heat up while watched and cool down while off
        if (room === g.cam) {
          g.heat[room] += dt;
          if (g.heat[room] >= CAM_HOT) { g.hot.add(room); g.cam = null; say(`📷 the ${room} camera overheated! check another room`, 3); buttons(); }
        } else {
          g.heat[room] = Math.max(0, g.heat[room] - CAM_COOL * dt);
          if (g.heat[room] === 0 && g.hot.delete(room)) buttons();
        }
      }
      for (const r of g.robots) {
        if (r.room.startsWith("door")) {
          if (g.t - r.doorSince > g.cfg.grace) { g.state = "caught"; g.caughtBy = r.kind; sfx("boing"); vibrate(200); buttons(); return; }
          continue;
        }
        if (g.t < r.next) continue;
        r.next = g.t + g.cfg.interval * rnd(0.7, 1.3) * (FAST[r.kind] || 1);
        if (g.cam === r.room) continue;                         // being watched: frozen
        if (Math.random() < g.cfg.chance) {
          r.room = pick(NEXT[r.room]);
          if (r.room.startsWith("door")) r.doorSince = g.t;
          else if (r.room.endsWith("Hall")) say("you hear clanking on the " + (r.room === "West Hall" ? "left…" : "right…"));
        }
      }
      if (g.t >= 6 * HOUR) won();
    }

    // ---- drawing
    function drawMenu() {
      c.fillStyle = "#0c0b14"; c.fillRect(0, 0, CW, CH);
      text("NIGHT SHIFT 🌙", CW / 2, 30, 24, "#e8e4ff");
      wrap("Survive from 12 AM to 6 AM. Glowing eyes in a doorway? Tap that door to FLASH it. A robo you watch on camera can't move, but a cam left on one room overheats, and everything uses battery!",
           CW / 2, 64, CW - 30, 12.5, "#b8b2d8", 17);
      D.groups.nightShift.forEach((k, i) => {
        const x = CW / 2 - 42 * (D.groups.nightShift.length - 1) + i * 84, open = isUnlocked(k);
        if (open || save.peeked.includes(k)) sprite(k, x - 24, 156, 3); else drawGrid(c, grid(k, 0, { t: 0, silhouette: true }), x - 24, 156, 3);
        text(open ? k : "🔒 " + (save.peeked.includes(k) ? k : "???"), x, 208, 11, open ? "#e8e4ff" : "#7a7598");
        text(`Night ${D.unlocks[k]}`, x, 224, 10, "#7a7598", "center", 600);
      });
      text("Your progress is saved.", CW / 2, 276, 11, "#7a7598", "center", 600);
    }
    function drawOffice() {
      const dark = g.battery <= 0;
      c.fillStyle = dark ? "#0e0c18" : "#1b1830"; c.fillRect(0, 0, CW, CH);
      c.fillStyle = dark ? "#0a0912" : "#14121f"; c.fillRect(0, 230, CW, CH - 230);
      if (!dark) {
        c.fillStyle = "#2a3a5a"; c.fillRect(150, 60, 60, 46); c.fillStyle = "#fff"; c.fillRect(160, 70, 3, 3); c.fillRect(192, 86, 3, 3);
        c.fillStyle = "#3a2e4a"; c.fillRect(120, 196, 120, 12); c.fillStyle = "#2a2238"; c.fillRect(128, 208, 8, 40); c.fillRect(224, 208, 8, 40);
        sprite("Blip", 150, 157, 3, "happy");
        c.fillStyle = "#ffd27a"; c.beginPath(); c.moveTo(206, 156); c.lineTo(226, 156); c.lineTo(232, 170); c.lineTo(200, 170); c.fill();
        c.fillStyle = "#8a7a9a"; c.fillRect(214, 170, 3, 26);
      }
      for (const side of ["L", "R"]) {
        const [x0, x1] = DOORS[side], flashing = g.t < g.flashUntil && g.flashSide === side;
        c.fillStyle = flashing ? "#f6eec0" : "#040308"; c.fillRect(x0, 40, x1 - x0, 200);
        c.strokeStyle = "#3a3360"; c.lineWidth = 3; c.strokeRect(x0, 40, x1 - x0, 200);
        if (flashing && g.flashed) sprite(g.flashed, x0 + 2, 100, 6);
        const robot = g.robots.find((r) => r.room === "door_" + side);
        if (robot && !flashing && Math.floor(g.t * 3 + (side === "R" ? 1 : 0)) % 7 !== 0) {
          c.fillStyle = KINDS[robot.kind].colors[MIDNIGHT].e;
          c.fillRect(x0 + 28, 128, 12, 12); c.fillRect(x0 + 60, 128, 12, 12);
        }
        text(side === "L" ? "◀ tap to flash" : "tap to flash ▶", (x0 + x1) / 2, 254, 10, "#7a7598", "center", 700);
      }
    }
    function drawCamera() {
      const room = g.cam;
      c.fillStyle = "#101a14"; c.fillRect(0, 0, CW, CH); c.fillStyle = "#0b130e"; c.fillRect(0, 210, CW, CH - 210);
      if (room === "Stage") { c.fillStyle = "#3a1420"; for (let i = 0; i < 9; i++) c.fillRect(14 + i * 38, 40, 16, 170); c.fillStyle = "#2a2010"; c.fillRect(10, 202, CW - 20, 14); }
      else if (room === "Arcade") for (let i = 0; i < 4; i++) { const x = 24 + i * 84; c.fillStyle = "#1a1a3a"; c.fillRect(x, 100, 46, 110); c.fillStyle = "#2a6a5a"; c.fillRect(x + 8, 112, 30, 26); }
      else if (room === "Kitchen") { c.fillStyle = "#2a2a2a"; c.fillRect(14, 160, CW - 28, 50); c.fillStyle = "#3a3a3a"; for (let i = 0; i < 6; i++) c.fillRect(22 + i * 56, 96, 38, 30); }
      else { c.fillStyle = "#162016"; c.beginPath(); c.moveTo(0, 40); c.lineTo(CW / 2 - 40, 110); c.lineTo(CW / 2 - 40, 200); c.lineTo(0, 280); c.fill();
             c.beginPath(); c.moveTo(CW, 40); c.lineTo(CW / 2 + 40, 110); c.lineTo(CW / 2 + 40, 200); c.lineTo(CW, 280); c.fill(); }
      const here = g.robots.filter((r) => r.room === room), sc = here.length > 2 ? 4 : 6;
      here.forEach((r, i) => sprite(r.kind, CW / 2 - here.length * 8 * sc - (here.length - 1) * 4 + i * (16 * sc + 8), 120, sc));
      for (let i = 0; i < 22; i++) { c.fillStyle = pick(["#1e2a22", "#26332a", "#18221b"]); c.fillRect(0, Math.random() * CH, CW, 1); }
      text(`● CAM ${ROOMS.indexOf(room) + 1} · ${room.toUpperCase()}`, 10, 44, 12, "#ff4a5a", "left");
      text(here.length ? "watching: it can't move" : "empty", CW - 10, 44, 10, "#9ad8a8", "right", 700);
      const heat = Math.min(1, g.heat[room] / CAM_HOT);         // 🌡️ how close this camera is to overheating
      text("🌡️ HEAT", 10, CH - 52, 10, "#9ad8a8", "left", 700);
      c.fillStyle = "#3a3360"; c.fillRect(70, CH - 59, 104, 14); c.fillStyle = "#101a14"; c.fillRect(72, CH - 57, 100, 10);
      c.fillStyle = heat < 0.5 ? "#5ad87a" : heat < 0.8 ? "#ffd23a" : "#ff4a5a"; c.fillRect(72, CH - 57, 100 * heat, 10);
    }
    function drawPlay() {
      if (g.cam) drawCamera(); else drawOffice();
      c.fillStyle = "#08070e"; c.fillRect(0, 0, CW, 28);
      const hour = Math.floor(g.t / HOUR);
      text(`NIGHT ${g.night}`, 10, 14, 12, "#e8e4ff", "left");
      text(hour === 0 ? "12 AM" : `${hour} AM`, CW / 2, 14, 14, "#ffd23a");
      const b = g.battery; c.strokeStyle = "#3a3360"; c.lineWidth = 2; c.strokeRect(CW - 104, 7, 60, 14);
      c.fillStyle = b > 50 ? "#5ad87a" : b > 20 ? "#ffd23a" : "#ff4a5a"; c.fillRect(CW - 102, 9, 56 * b / 100, 10);
      text(`${Math.floor(b)}%`, CW - 8, 14, 11, "#e8e4ff", "right");
      if (g.t < g.msgUntil) {
        c.fillStyle = "rgba(8,7,14,.9)"; c.fillRect(8, CH - 30, CW - 16, 24);
        text(g.msg, CW / 2, CH - 18, 11.5, "#e8e4ff", "center", 700);
      }
    }
    function drawCaught() {
      c.fillStyle = "#14081a"; c.fillRect(0, 0, CW, CH);
      sprite(g.caughtBy, CW / 2 - 56, 30, 7);
      text("GOTCHA! 🤖", CW / 2, 200, 26, "#ff4a6a");
      wrap(`${g.caughtBy} got into the office. (it just wanted a hug)`, CW / 2, 238, CW - 40, 13, "#d8c8f0", 18);
    }
    function drawWon() {
      c.fillStyle = "#2a1a3a"; c.fillRect(0, 0, CW, CH); c.fillStyle = "#ffb86a"; c.fillRect(0, CH - 70, CW, 70);
      text("6 AM 🌅", CW / 2, 34, 26, "#ffd23a");
      text(`You survived Night ${g.night}!`, CW / 2, 66, 15, "#e8e4ff");
      sprite(g.newUnlock || "Blip", CW / 2 - 40, 88, 5, "happy");
      wrap(g.newUnlock ? `UNLOCKED: ${g.newUnlock}! Bring it to town from here or the 📖 Zoo.` : g.night === LAST ? "You beat every night. The whole crew is yours! 🏆" : "Blip is proud of you.",
           CW / 2, 175, CW - 40, 13, "#ffffff", 18);
    }
    function frame(ts) {
      if ($("nsSheet").hidden) { raf = null; return; }
      const t = ts / 1000, dt = Math.min(0.25, t - (last || t)) * speed; last = t;
      if (g.state === "play") update(dt);
      c.setTransform(cv.width / CW, 0, 0, cv.height / CH, 0, 0); c.imageSmoothingEnabled = false;
      ({ menu: drawMenu, play: drawPlay, caught: drawCaught, won: drawWon })[g.state]();
      raf = requestAnimationFrame(frame);
    }

    // ---- buttons under the screen
    function btn(label, fn, cls = "") { const b = document.createElement("button"); b.textContent = label; b.className = cls; b.onclick = fn; return b; }
    function buttons() {
      const box = $("nsButtons"); box.innerHTML = "";
      const row = () => { const r = document.createElement("div"); r.className = "nsRow"; box.appendChild(r); return r; };
      if (g.state === "menu") {
        const r = row();
        for (const n of Object.keys(NIGHTS).map(Number)) {
          const b = btn(`Night ${n}${n <= save.nightsWon ? " ✓" : ""}`, () => start(n), n === Math.min(save.nightsWon + 1, LAST) ? "primary" : "");
          b.disabled = n > save.nightsWon + 1; r.appendChild(b);
        }
      } else if (g.state === "play") {
        const r = row();
        r.appendChild(btn("◀ FLASH", () => flash("L"), "flash"));
        r.appendChild(btn("🪑 Office", () => { g.cam = null; buttons(); }, g.cam ? "" : "on"));
        r.appendChild(btn("FLASH ▶", () => flash("R"), "flash"));
        const r2 = row(); r2.classList.add("cams");
        ROOMS.forEach((room, i) => r2.appendChild(btn(`📷${i + 1}\n${room.replace(" Hall", "")}`, () => cam(room), g.cam === room ? "on" : g.hot.has(room) ? "hot" : "")));
      } else if (g.state === "caught") {
        const r = row(); r.appendChild(btn(`Try Night ${g.night} again`, () => start(g.night), "primary")); r.appendChild(btn("Menu", menu));
      } else {
        const r = row();
        if (g.newUnlock) {
          const k = g.newUnlock;
          r.appendChild(btn("Bring it to town 🐾", () => {
            closeSheets(); const p = addPet(k, { color: MIDNIGHT, quiet: true }); if (p) say_(p, "*whirr* ...i'm free! hi!!", 4);
          }, "primary"));
        } else if (g.night < LAST) r.appendChild(btn(`Night ${g.night + 1} ▶`, () => start(g.night + 1), "primary"));
        r.appendChild(btn("Menu", menu));
      }
    }
    function menu() { g = { state: "menu" }; buttons(); }
    function open() {
      FONT = getComputedStyle(document.body).fontFamily;
      const dpr = Math.min(window.devicePixelRatio || 1, 3); cv.width = CW * dpr; cv.height = CH * dpr;
      menu(); openSheet("nsSheet"); last = 0; if (!raf) raf = requestAnimationFrame(frame);
    }
    cv.addEventListener("pointerdown", (e) => {
      if (g.state !== "play" || g.cam) return;
      const r = cv.getBoundingClientRect(), x = (e.clientX - r.left) * CW / r.width;
      if (x < DOORS.L[1] + 10) flash("L"); else if (x > DOORS.R[0] - 10) flash("R");
    });
    return { open, start, flash, cam, state: () => g, setSpeed: (v) => { speed = v; } };
  })();
  const say_ = say;
  $("nightBtn").onclick = () => NS.open();

  // ------------------------------------------------------------------ maintenance mode
  // One switch for every version of Blipville: status.json in the repo ("web" is this one). Turned on/off with the
  // "Maintenance mode" button on GitHub. We read it straight from GitHub (fresh within a few minutes), then from this site.
  const STATUS_URLS = ["https://raw.githubusercontent.com/Johnblip189/Blipville/main/status.json", "../status.json"];
  // 🎟️ early access codes: a valid code is remembered on this device and opens the 1.0 early access (in /early/) during
  // maintenance. Only the codes' fingerprints (SHA-256) are stored here, never the codes themselves.
  const EARLY_HASHES = ["9912092ed34702febd9e54f7035b19ab72bf054cebbe38de1161286b863ac6c7", "6d90cbf3483607a667d8a787fcba2ffedbe5959b003a79797e882cf695880c07", "43a83ddfe51fc724ddab9b06adebdd9c1d67c5933546285eced02e943690b024", "25193bec0c0f2d4f89a05f82d4f5e170dd002fb410d6410c5da96c594447885a", "a1c3b063d196e3b16f60441189c069cecaa7500e6f66c75d76c3f61130708849", "804c9e2f83dbf465de9142c1d2f39705c47857c0c3db644f01242254e0172be8"   /* alpha tester */];
  const EARLY_KEY = "blipville-early-code", IN_EARLY = /\/early\//.test(location.pathname);
  const normCode = (t) => String(t || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
  async function sha256(t) {
    const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t));
    return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
  }
  async function earlyOk() {
    if (isCreator() || isMod()) return true;               // creators and moderators can always play
    try { const c = localStorage.getItem(EARLY_KEY); return !!c && EARLY_HASHES.includes(await sha256(normCode(c))); } catch (e) { return false; }
  }
  function earlyGate() {
    $("maint").hidden = false;
    $("maintTitle").textContent = "🎟️ Blipville 1.0 early access";
    $("maintMsg").textContent = "Enter your early access code to play Blipville 1.0 before everyone else!";
  }
  $("earlyGo").onclick = async () => {
    const code = normCode($("earlyCode").value), h = code ? await sha256(code) : "";
    const role = (D.creator && h === D.creator.hash) ? "blipville-creator" : (D.modHashes || []).includes(h) ? "blipville-mod" : null;
    if (role) { try { localStorage.setItem(role, h); } catch (e) { /* private mode */ } }      // creators and mods can always play
    if (code && (role || EARLY_HASHES.includes(h))) {
      if (!role) { try { localStorage.setItem(EARLY_KEY, code); } catch (e) { /* private mode: it just won't be remembered */ } }
      $("earlyMsg").textContent = "🎉 Unlocked! Opening Blipville 1.0…"; sfx("fanfare");
      setTimeout(() => { if (IN_EARLY) location.reload(); else location.href = "../early/"; }, 900);
    } else $("earlyMsg").textContent = "That code doesn't work. Check it for typos!";
  };
  if (IN_EARLY) earlyOk().then((ok) => { if (!ok) earlyGate(); });
  async function checkStatus() {
    for (const url of STATUS_URLS) {
      try {
        const res = await fetch(`${url}?t=${Date.now()}`, { cache: "no-store" });
        if (!res.ok) continue;
        const st = await res.json();
        let closed = typeof st.maintenance === "object" ? !!(st.maintenance && st.maintenance.web) : !!st.maintenance;
        if (IN_EARLY) {                              // early access ignores maintenance, but needs a code
          if (!(await earlyOk())) { earlyGate(); return st; }
          closed = !!(st.maintenance && st.maintenance.early);
        }
        $("maint").hidden = !closed;
        if (closed && !IN_EARLY && await earlyOk()) { location.href = "../early/"; return st; }   // this device has a code
        if (closed) {
          $("maintMsg").textContent = st.message || "We're fixing things up. Back soon!";
          $("maintLink").hidden = !st.link;
          if (st.link) { $("maintLink").href = st.link; $("maintLink").textContent = st.link_text || "More info"; }
        }
        return st;
      } catch (e) { /* offline or blocked: try the next one */ }
    }
    return null;                                    // can't tell: let them keep playing
  }
  $("maintRetry").onclick = () => { $("maintRetry").textContent = "Checking…"; checkStatus().finally(() => { $("maintRetry").textContent = "Check again"; }); };
  checkStatus(); setInterval(checkStatus, 2 * 60 * 1000);

  window.blipvilleGo = { cookies: () => cookies, chat: { open: openChat, show: chatShow }, dream: { open: openDream, game: () => dreamGame, rewrite: badDreamRewrite, rest: (v) => { dreamRest = v; } }, pets, save, addPet, grid, glitching, petIt, feed, nap, openEgg, openZoo, openPetSheet, hatCells, currentSeason,
                         nightShift: NS, checkStatus, sighting: () => sighting, tapSighting: () => sighting && befriend(), checkTrophies, openTrophies, ghostAlpha, openArena, battleCodeFor, readBattleCode, arena: () => arenaBattle, arenaTick, arenaPick, aiMove, musicNow: () => music.name, spawnSighting: () => { nextSighting = 0; }, startSighting: (k, ago = 0) => { startSighting(k); sighting.t0 -= ago; },
                         setSeason: (s) => { seasonOverride = s; weather = []; }, plays: () => plays,
                         startPlay: (type, a, b) => { const t = now(); a.playing = b.playing = true;
                           plays.push(type === "ball" ? { type, pets: [a, b], from: a, to: b, t0: t, throws: 0, n: 4 }
                                                      : { type, pets: [a, b], runner: a, chaser: b, until: t + 7, swapped: false }); } };   // handy for testing
})();
