// 🥊 Blipville real-time battles (the new battle system). Pure simulation: no drawing, no page, no clock.
// A match is plain data, stepped 60 times a second with each fighter's buttons for that frame, so a host can run it and send the state
// to friends (raid rooms), and a computer fighter is just a function that makes buttons. All the numbers are in BAL / MOVES.
// Fighter coordinates: x goes across the arena (0 to 360), y is the height above the ground (0 = standing on it).
(function () {
  "use strict";
  const FPS = 60, DT = 1 / FPS, W = 360, LEFT = 20, RIGHT = 340;

  // 💖 Balance. These are first guesses for testing: nothing here has been tuned or approved yet.
  const BAL = {
    stocks: 2, matchSeconds: 99, gravity: 1500, jump: 470, walk: 52, walkPerSpd: 3.2, airControl: 0.55,
    dmgScale: 1.6,                        // every move's damage = the Blip's attack stat x the move's factor x this
    parryFrames: 8, guardMax: 100, guardRegen: 0.45, guardBreakStun: 50, chipFraction: 0.12,
    awakenSeconds: 10, awakenDmg: 1.3, awakenSpeed: 1.15, awakenCost: 100, meterPerDmg: 1.2, meterPerDmgTaken: 0.6,
    dashSpeed: 300, dashFrames: 14, dashCool: 40, respawnFrames: 90, invulnFrames: 120, specialCost: 25, spRegen: 0.1,
  };
  // start / active / recovery are frames. dmg is a factor of the attacker's attack stat. kb = knockback speed, launch = upward speed.
  const MOVES = {
    light:   { start: 4,  active: 3, rec: 9,  reach: 36, h: 34, dmg: 0.18, kb: 70,  stun: 14 },
    heavy:   { start: 12, active: 4, rec: 20, reach: 42, h: 48, dmg: 0.42, kb: 60,  stun: 26, launch: 340, guardBreak: true },
    air:     { start: 4,  active: 7, rec: 8,  reach: 36, h: 36, dmg: 0.22, kb: 90,  stun: 16, lowered: 6 },
    dash:    { start: 0,  active: 14, rec: 8, reach: 30, h: 34, dmg: 0.2,  kb: 110, stun: 16 },
    special: { start: 10, active: 0,  rec: 16, dmg: 0.3, kb: 90, stun: 18, speed: 230, life: 90 },   // a projectile
  };

  const NO = {};
  const KEYS = ["left", "right", "jump", "light", "heavy", "dash", "guard", "special", "awaken"];
  function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  const newStats = () => ({ hits: 0, airHits: 0, heavyHits: 0, dashHits: 0, specialHits: 0, guardBreaks: 0, counters: 0, blocks: 0, projCounters: 0, awakenings: 0, kos: 0, damage: 0, taken: 0, maxCombo: 0 });

  // spec: { id, name, kind, hp, atk, spd, types:[], canAw, team, ai: 0|1|2|null, big }
  function fighter(spec, x, face) {
    return { id: spec.id, name: spec.name || spec.id, kind: spec.kind, team: spec.team, hp: spec.hp, max: spec.hp, atk: spec.atk, spd: spec.spd, types: spec.types || [],
      canAw: !!spec.canAw, ai: spec.ai == null ? null : { level: spec.ai, tick: 0, plan: "approach", planT: 0 }, big: spec.big || 1, stocks: spec.stocks || BAL.stocks,
      x, y: 0, vx: 0, vy: 0, face, home: x, state: "idle", t: 0, stunT: 0, act: null, hit: [], combo: 0, comboWindow: 0, g: BAL.guardMax, meter: 0, awakeT: 0,
      sp: 100, dashCool: 0, inv: 60, respawn: 0, out: false, prev: {}, hurt: 0, takenCombo: 0 };
  }
  function create(specs, opts = {}) {
    const n = specs.length, m = { frame: 0, over: null, events: [], projectiles: [], stats: {}, opts, rand: rng(opts.seed == null ? 1234 : opts.seed), fighters: [] };
    const sides = {}; specs.forEach((s) => (sides[s.team] = (sides[s.team] || 0) + 1));
    const seen = {};
    specs.forEach((s, i) => {
      const side = Object.keys(sides).indexOf(String(s.team)), k = seen[s.team] = (seen[s.team] || 0) + 1;
      const x = side === 0 ? 90 - (k - 1) * 28 : 270 + (k - 1) * 28;
      m.fighters.push(fighter(s, x, side === 0 ? 1 : -1)); m.stats[s.id] = newStats();
    });
    m.limit = (opts.seconds || BAL.matchSeconds) * FPS;
    return m;
  }

  const pressed = (f, inp, k) => !!inp[k] && !f.prev[k];
  const hurtbox = (f) => ({ x0: f.x - 18 * f.big, x1: f.x + 18 * f.big, y0: f.y, y1: f.y + 36 * f.big });
  const overlap = (a, b) => a.x0 < b.x1 && a.x1 > b.x0 && a.y0 < b.y1 && a.y1 > b.y0;
  const enemies = (m, f) => m.fighters.filter((d) => d.team !== f.team && !d.out && d.respawn <= 0);
  const speedOf = (f) => (BAL.walk + f.spd * BAL.walkPerSpd) * (f.awakeT > 0 ? BAL.awakenSpeed : 1);
  const typeMult = (m, f, d) => (m.opts.typeMult ? m.opts.typeMult(f.types, d.types) : 1);
  const ev = (m, type, data) => m.events.push({ type, frame: m.frame, ...data });

  function startAct(f, name) { f.state = name; f.t = 0; f.act = MOVES[name]; f.hit = []; }
  function free(f) { return f.state === "idle" || f.state === "walk" || f.state === "jump"; }

  function updateFighter(m, f, inp) {
    if (f.out) return;
    if (f.respawn > 0) { if (--f.respawn === 0) { f.x = f.home; f.y = 0; f.vx = f.vy = 0; f.hp = f.max; f.state = "idle"; f.inv = BAL.invulnFrames; f.g = BAL.guardMax; f.sp = 100; } f.prev = { ...inp }; return; }
    if (f.inv > 0) f.inv--;
    if (f.dashCool > 0) f.dashCool--;
    if (f.comboWindow > 0 && --f.comboWindow === 0) f.takenCombo = 0;
    if (f.awakeT > 0 && --f.awakeT === 0) ev(m, "AWAKEN_END", { who: f.id });
    f.sp = Math.min(100, f.sp + BAL.spRegen);
    const grounded = f.y <= 0 && f.vy <= 0;
    const dir = (inp.right ? 1 : 0) - (inp.left ? 1 : 0), sp = speedOf(f);
    f.t++;
    switch (f.state) {
      case "idle": case "walk": case "jump": {
        if (!grounded) f.state = "jump"; else if (f.state === "jump") f.state = "idle";
        if (inp.guard && grounded) { f.state = "guard"; f.t = 0; break; }
        if (pressed(f, inp, "awaken") && f.canAw && f.meter >= BAL.awakenCost && f.awakeT <= 0) {
          f.awakeT = BAL.awakenSeconds * FPS; f.meter = 0; f.hp = Math.min(f.max, f.hp + f.max * 0.15); m.stats[f.id].awakenings++; ev(m, "AWAKEN", { who: f.id }); break;
        }
        if (pressed(f, inp, "dash") && f.dashCool <= 0 && grounded) { if (dir) f.face = dir; startAct(f, "dash"); f.dashCool = BAL.dashCool; f.vx = f.face * BAL.dashSpeed; break; }
        if (pressed(f, inp, "heavy") && grounded) { startAct(f, "heavy"); f.vx = 0; break; }
        if (pressed(f, inp, "special") && f.sp >= BAL.specialCost) { startAct(f, "special"); f.sp -= BAL.specialCost; f.vx = 0; break; }
        if (pressed(f, inp, "light")) { if (grounded) { startAct(f, "light"); f.vx = 0; f.combo = 1; } else startAct(f, "air"); break; }
        if (pressed(f, inp, "jump") && grounded) { f.vy = BAL.jump; f.state = "jump"; }
        if (grounded) { f.vx = dir * sp; f.state = dir ? "walk" : "idle"; } else f.vx += (dir * sp - f.vx) * BAL.airControl * 0.2;
        if (dir) f.face = dir;
        break;
      }
      case "light": case "heavy": case "air": case "special": {
        const a = f.act;
        if (f.state === "special" && f.t === a.start) {
          const d = f.face, dmg = f.atk * a.dmg * BAL.dmgScale * (f.awakeT > 0 ? BAL.awakenDmg : 1);
          m.projectiles.push({ x: f.x + d * 22, y: f.y + 18 * f.big, vx: d * a.speed, owner: f.id, team: f.team, dmg, life: a.life, from: f });
        }
        if (f.state === "light" && f.t >= a.start + 2 && pressed(f, inp, "light") && f.combo < 3 && f.t < a.start + a.active + a.rec) { f.combo++; f.t = 0; f.hit = []; if (dir) f.face = dir; }
        if (f.t >= a.start + a.active + a.rec) { f.state = grounded ? "idle" : "jump"; f.act = null; f.combo = 0; }
        else if (f.state === "air" && grounded) { f.state = "idle"; f.act = null; }
        break;
      }
      case "dash":
        if (f.t >= BAL.dashFrames) { f.vx *= 0.2; if (f.t >= BAL.dashFrames + MOVES.dash.rec) { f.state = "idle"; f.act = null; } }
        break;
      case "guard":
        if (!inp.guard || !grounded) { f.state = "idle"; }
        f.vx = 0;
        break;
      case "hitstun": case "guardbroken":
        f.vx *= 0.9; if (f.t >= f.stunT) { f.state = grounded ? "idle" : "jump"; }
        break;
      case "launched":
        if (grounded) { f.state = "down"; f.t = 0; f.vx = 0; }
        break;
      case "down":
        f.vx = 0; if (f.t >= 26) f.state = "idle";
        break;
    }
    if (f.state !== "guard" && f.g < BAL.guardMax) f.g = Math.min(BAL.guardMax, f.g + BAL.guardRegen);
    // physics
    if (f.y > 0 || f.vy > 0) { f.vy -= BAL.gravity * DT; f.y += f.vy * DT; if (f.y <= 0) { f.y = 0; f.vy = 0; } }
    f.x = Math.max(LEFT, Math.min(RIGHT, f.x + f.vx * DT));
    f.prev = { ...inp };
  }

  // an attack lands (or is blocked / parried). att = { x, fighter|null }, mv = the move, dmg = full damage
  function strike(m, att, d, mv, dmg, kind) {
    const f = att.fighter, st = m.stats[att.owner], dst = m.stats[d.id], towards = Math.sign(att.x - d.x) || 1;
    if (d.state === "guard" && d.face === towards) {
      if (d.t <= BAL.parryFrames) {                                         // 🛡️ perfect guard
        if (att.proj) { att.proj.vx *= -1.25; att.proj.owner = d.id; att.proj.team = d.team; att.proj.dmg *= 1.2; att.proj.from = d; dst.projCounters++; ev(m, "PROJ_COUNTER", { who: d.id }); }
        else if (f) { f.state = "hitstun"; f.t = 0; f.stunT = 30; f.vx = -f.face * 60; f.act = null; dst.counters++; ev(m, "COUNTER", { who: d.id, from: att.owner }); }
        d.meter = Math.min(100, d.meter + 6); return false;
      }
      if (mv.guardBreak || d.g - dmg * 2.2 <= 0) {                           // 💥 guard broken
        d.state = "guardbroken"; d.t = 0; d.stunT = BAL.guardBreakStun; d.g = 0; d.vx = -towards * 40; if (st) st.guardBreaks++; ev(m, "GUARD_BREAK", { who: att.owner, to: d.id }); return true;
      }
      d.g -= dmg * 2.2; d.hp = Math.max(1, d.hp - dmg * BAL.chipFraction); d.vx = -towards * 50; dst.blocks++; ev(m, "BLOCK", { who: d.id });
      if (att.proj) att.proj.life = 0; return false;
    }
    if (d.inv > 0 || d.state === "down") return false;
    const mult = f ? typeMult(m, f, d) : 1, dealt = dmg * mult;
    d.hp -= dealt; d.hurt = 8; d.takenCombo++; d.comboWindow = 50;
    const air = !!(f && f.y > 2 && kind === "air"), heavy = kind === "heavy", dash = kind === "dash", spec = kind === "special";
    if (st) { st.hits++; st.damage += dealt; if (air) st.airHits++; if (heavy) st.heavyHits++; if (dash) st.dashHits++; if (spec) st.specialHits++; st.maxCombo = Math.max(st.maxCombo, d.takenCombo); }
    dst.taken += dealt;
    const f0 = m.fighters.find((x) => x.id === att.owner); if (f0) f0.meter = Math.min(100, f0.meter + dealt * BAL.meterPerDmg); d.meter = Math.min(100, d.meter + dealt * BAL.meterPerDmgTaken);
    d.state = mv.launch ? "launched" : "hitstun"; d.t = 0; d.stunT = mv.stun; d.act = null;
    d.vx = -towards * mv.kb; if (mv.launch) { d.vy = mv.launch; } else if (d.y > 0) d.vy = Math.max(d.vy, 140);
    ev(m, "HIT", { who: att.owner, to: d.id, kind, dmg: Math.round(dealt), x: d.x, y: d.y + 14 });
    if (d.hp <= 0) knockOut(m, d, att.owner);
    return true;
  }
  function knockOut(m, d, by) {
    d.hp = 0; d.stocks--; const k = m.stats[by]; if (k) k.kos++; ev(m, "KO", { who: by, to: d.id, stocksLeft: d.stocks });
    d.state = "launched"; d.vy = 360; d.vx = 0; d.act = null; d.takenCombo = 0;
    if (d.stocks <= 0) { d.out = true; d.y = 0; } else d.respawn = BAL.respawnFrames;
  }

  function step(m, inputs = {}) {
    if (m.over) return m;
    m.frame++;
    const ins = {};                                           // everyone decides from the same snapshot, then everyone moves
    for (const f of m.fighters) ins[f.id] = f.ai ? aiInputs(m, f) : inputs[f.id] || NO;
    for (const f of m.fighters) updateFighter(m, f, ins[f.id]);
    // melee hit boxes (all collected first, then applied, so two fighters who hit on the same frame trade blows)
    const queue = [];
    for (const f of m.fighters) {
      if (f.out || f.respawn > 0 || !f.act || f.state === "special") continue;
      const a = f.act, kind = f.state === "dash" ? "dash" : f.state;
      const from = a.start, to = a.start + a.active;
      if (f.t < from || f.t >= to) continue;
      const x0 = f.face > 0 ? f.x + 12 : f.x - 12 - a.reach * f.big, x1 = f.face > 0 ? f.x + 12 + a.reach * f.big : f.x - 12;
      const box = { x0, x1, y0: f.y + (a.lowered || 2), y1: f.y + (a.lowered || 2) + a.h * f.big };
      for (const d of enemies(m, f)) {
        if (f.hit.includes(d.id) || !overlap(box, hurtbox(d))) continue;
        f.hit.push(d.id);
        const comboBoost = kind === "light" ? 1 + (f.combo - 1) * 0.12 : 1;
        queue.push({ f, d, a, kind, dmg: f.atk * a.dmg * BAL.dmgScale * (f.awakeT > 0 ? BAL.awakenDmg : 1) * comboBoost, x: f.x });
      }
    }
    for (const q of (m.frame % 2 ? queue : queue.reverse())) strike(m, { x: q.x, fighter: q.f, owner: q.f.id }, q.d, q.a, q.dmg, q.kind);
    // projectiles
    for (const p of m.projectiles) {
      p.x += p.vx * DT; p.life--;
      if (p.x < -10 || p.x > W + 10) p.life = 0;
      const box = { x0: p.x - 8, x1: p.x + 8, y0: p.y - 8, y1: p.y + 8 };
      for (const d of m.fighters) {
        if (p.life <= 0) break;
        if (d.team === p.team || d.out || d.respawn > 0 || !overlap(box, hurtbox(d))) continue;
        const hitIt = strike(m, { x: p.x, fighter: null, owner: p.owner, proj: p }, d, MOVES.special, p.dmg, "special");
        if (hitIt) p.life = 0;
        break;
      }
    }
    m.projectiles = m.projectiles.filter((p) => p.life > 0);
    // end of the match
    const alive = new Set(m.fighters.filter((f) => !f.out).map((f) => f.team));
    if (alive.size <= 1) m.over = { winner: [...alive][0] ?? null, frame: m.frame, reason: "ko" };
    else if (m.frame >= m.limit) {
      const score = {}; for (const f of m.fighters) score[f.team] = (score[f.team] || 0) + (f.out ? 0 : f.stocks * 1000 + f.hp);
      const best = Object.entries(score).sort((a, b) => b[1] - a[1]); m.over = { winner: best[0][1] === (best[1] || [0, -1])[1] ? null : best[0][0], frame: m.frame, reason: "time" };
    }
    if (m.over) ev(m, "OVER", { winner: m.over.winner });
    return m;
  }

  // ---------------------------------------------------------------- computer fighters (level 0 easy, 1 normal, 2 hard)
  function aiInputs(m, f) {
    const a = f.ai, inp = {}, foes = enemies(m, f);
    if (!foes.length || f.respawn > 0) return inp;
    const t = foes.reduce((best, d) => (Math.abs(d.x - f.x) < Math.abs(best.x - f.x) ? d : best), foes[0]);
    const dx = t.x - f.x, dist = Math.abs(dx), toward = dx > 0 ? "right" : "left", away = dx > 0 ? "left" : "right", L = a.level, r = m.rand;
    const react = [26, 14, 7][L];
    const incoming = m.projectiles.find((p) => p.team !== f.team && Math.abs(p.x - f.x) < 90 && Math.sign(f.x - p.x) === Math.sign(p.vx));
    const foeStrikes = ["light", "heavy", "air", "dash", "special"].includes(t.state) && dist < 84;
    if (a.planT > 0) a.planT--;
    if ((incoming || foeStrikes) && (f.state === "idle" || f.state === "walk" || f.state === "guard") && r() < [0.08, 0.16, 0.26][L]) { a.plan = "guard"; a.planT = [8, 12, 14][L]; }
    else if (t.act && t.t >= t.act.start + t.act.active && dist < 76 && f.state !== "guard" && r() < [0, 0.5, 0.9][L]) { a.plan = r() < 0.6 ? "light" : "heavy"; a.planT = react; }      // punish a recovering foe
    else if (a.planT <= 0) {
      const roll = r();
      if (dist > 190) a.plan = roll < 0.3 && f.sp >= BAL.specialCost ? "special" : roll < 0.55 ? "dash" : "approach";
      else if (dist > 84) a.plan = roll < 0.25 ? "dash" : roll < 0.35 && f.sp >= BAL.specialCost ? "special" : roll < 0.5 ? "jumpin" : "approach";
      else { const pg = [0.14, 0.08, 0.03][L]; a.plan = roll < 0.45 ? "light" : roll < 0.62 ? "heavy" : roll < 0.74 ? "jumpin" : roll < 0.74 + pg ? "guard" : roll < 0.74 + 2 * pg ? "retreat" : "light"; }
      a.planT = react + Math.floor(r() * react);
    }
    a.tick++;
    const pulse = a.tick % 5 === 0;                           // a fresh button press now and then, so combos can chain
    f.face = f.face || 1;
    if (f.canAw && f.meter >= BAL.awakenCost && f.awakeT <= 0) inp.awaken = a.tick % 2 === 0;
    switch (a.plan) {
      case "approach": inp[toward] = dist > 42; break;
      case "retreat": inp[away] = true; break;
      case "guard": inp.guard = true; break;
      case "dash": inp[toward] = true; inp.dash = pulse; break;
      case "special": inp[toward] = dist > 240; inp.special = pulse; if (f.face !== (dx > 0 ? 1 : -1)) inp[toward] = true; break;
      case "jumpin": inp[toward] = dist > 34; if (f.y <= 0) inp.jump = pulse; else if (dist < 70) inp.light = pulse; break;
      case "light": inp[toward] = dist > 36; inp.light = pulse; break;
      case "heavy": inp[toward] = dist > 40; inp.heavy = pulse; break;
    }
    return inp;
  }

  window.FIGHT = { FPS, DT, W, LEFT, RIGHT, BAL, MOVES, KEYS, create, step, hurtbox, newStats };
})();
