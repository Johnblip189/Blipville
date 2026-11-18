// ⭐ Countdown Stars: the event that runs on the maintenance screen while Blipville gets ready for 1.0.
// Catch falling stars to help launch 1.0. Catch 200 and you earn Liftoff, a limited-edition Blip that flies into your
// town when Blipville 1.0 opens. Progress is saved on this device (localStorage), the same place your pets are.
// This file is shared by the main site (the maintenance screen) and the 1.0 build (the Events sheet, while Spiky Week
// is paused), and the 1.0 build reads CountdownStars.done() to hand out the Blip.
(function () {
  const KEY = "blipville-countdown", GOAL = 200, END = "2026-11-22";   // ends the moment 1.0 opens
  const REWARD = "Liftoff";
  const SPRITE = {
    body: ["......rrrr......", ".....rwwwwr.....", "....rwwccwwr....", "..oooooooooooo..", ".obbbbbbbbbbbbo.", "fobbbbbbbbbbbbof",
           "fobbbbbbbbbbbbof", "fobpbbbbbbbbpbof", ".obbbbbbbbbbbbo.", "..oooooooooooo..", "....yyllllyy....", ".....yyllyy....."],
    colors: { o: "#2a1a3a", b: "#c8d8ff", r: "#ff4a6a", w: "#ffffff", c: "#5ad8ff", f: "#ff4a6a", p: "#ff9ac0", y: "#ffd23a", l: "#ff8a2a", e: "#1a1030" },
  };
  const localDay = (d = new Date()) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const load = () => { try { return Object.assign({ stars: 0, done: false }, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (e) { return { stars: 0, done: false }; } };
  const store = (s) => { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) { /* private mode: progress only lasts this visit */ } };

  function drawSprite(cv, t) {
    const g = cv.getContext("2d"), px = Math.floor(cv.width / 16);
    const bob = Math.round(Math.sin(t / 300) * 1.5);
    g.clearRect(0, 0, cv.width, cv.height);
    SPRITE.body.forEach((row, r) => [...row].forEach((ch, i) => {
      if (ch === ".") return;
      let col = SPRITE.colors[ch];
      if ((ch === "y" || ch === "l") && Math.floor(t / 120) % 2) col = ch === "y" ? "#ff8a2a" : "#ffd23a";   // flickering flame
      g.fillStyle = col; g.fillRect(i * px, (r + 1) * px + bob, px, px);
    }));
    g.fillStyle = SPRITE.colors.e;                          // eyes
    [5, 10].forEach((i) => g.fillRect(i * px, 6 * px + bob, px, px * 2));
  }

  const CSS = `
.cdBox { margin-top: 18px; padding: 14px 12px; border-radius: 18px; background: linear-gradient(180deg, #1c1640, #2a1a4a); border: 2px solid #5a4aa8; text-align: center; }
.cdHead { display: flex; align-items: center; gap: 12px; text-align: left; }
.cdHead canvas { width: 64px; height: 56px; image-rendering: pixelated; flex: none; }
.cdHead b { display: block; font-size: 18px; color: #ffd23a; }
.cdHead span { display: block; font-size: 14px; color: #c8c0e8; line-height: 1.35; }
.cdField { display: block; width: 100%; height: auto; aspect-ratio: 32 / 17; margin-top: 12px; border-radius: 14px; background: #0c0a20; touch-action: manipulation; cursor: pointer; }
.cdBar { height: 14px; margin-top: 10px; border-radius: 7px; background: #0c0a20; overflow: hidden; }
.cdBar i { display: block; height: 100%; width: 0; background: linear-gradient(90deg, #ffd23a, #ff8a2a); border-radius: 7px; transition: width .2s; }
.cdText { margin-top: 6px; font-size: 14px; font-weight: 700; color: #ffd23a; }
.cdBox button.cdPlay { margin-top: 10px; }
`;

  function mount(host) {
    if (!host || host.querySelector(".cdBox") || !live()) return null;
    if (!document.getElementById("cdCss")) { const st = document.createElement("style"); st.id = "cdCss"; st.textContent = CSS; document.head.appendChild(st); }
    const box = document.createElement("div");
    box.className = "cdBox";
    box.innerHTML = `<div class="cdHead"><canvas width="96" height="84"></canvas><div><b>⭐ Countdown Stars</b>
      <span>Help launch Blipville 1.0! Catch <b style="display:inline;font-size:inherit">${GOAL} stars</b> to earn <b style="display:inline;font-size:inherit">${REWARD}</b>, a limited-edition Blip. Only until 1.0 opens on Sunday!</span></div></div>
      <canvas class="cdField" width="640" height="340" aria-label="Tap the stars to catch them"></canvas>
      <div class="cdBar"><i></i></div><div class="cdText"></div>`;
    host.appendChild(box);
    const icon = box.querySelector(".cdHead canvas"), field = box.querySelector(".cdField"), bar = box.querySelector(".cdBar i"), text = box.querySelector(".cdText");
    const g = field.getContext("2d"), W = field.width, H = field.height;
    let s = load(), stars = [], pops = [], nextStar = 0, raf = 0, bg = [];
    for (let i = 0; i < 40; i++) bg.push([Math.random() * W, Math.random() * H, Math.random() * 2 + 1]);

    function show() {
      bar.style.width = Math.min(100, (s.stars / GOAL) * 100) + "%";
      text.textContent = s.done ? `🚀 You earned ${REWARD}! It flies into your town when Blipville 1.0 opens.` : `${s.stars} / ${GOAL} stars`;
    }
    function spawn(t) {
      const gold = Math.random() < 0.12;
      stars.push({ x: 40 + Math.random() * (W - 80), y: -20, vy: 70 + Math.random() * 60 + Math.min(60, s.stars / 4), vx: (Math.random() - 0.5) * 40,
                   r: gold ? 26 : 20, gold, born: t });
    }
    function star(x, y, r, col, spin) {
      g.save(); g.translate(x, y); g.rotate(spin); g.fillStyle = col; g.beginPath();
      for (let i = 0; i < 10; i++) { const a = (i * Math.PI) / 5 - Math.PI / 2, rr = i % 2 ? r * 0.45 : r; g.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); }
      g.closePath(); g.fill(); g.restore();
    }
    let last = 0;
    function frame(t) {
      raf = requestAnimationFrame(frame);
      if (!box.isConnected || box.offsetParent === null) return;   // hidden: don't spend anything
      const dt = Math.min(0.05, (t - (last || t)) / 1000); last = t;
      if (t > nextStar && stars.length < 6) { spawn(t); nextStar = t + 380 + Math.random() * 420; }
      stars.forEach((st) => { st.y += st.vy * dt; st.x += st.vx * dt; });
      stars = stars.filter((st) => st.y < H + 30);
      pops = pops.filter((p) => t - p.t < 700);
      g.fillStyle = "#0c0a20"; g.fillRect(0, 0, W, H);
      bg.forEach(([x, y, r], i) => { g.globalAlpha = 0.3 + 0.3 * Math.sin(t / 500 + i); g.fillStyle = "#ffffff"; g.fillRect(x, y, r, r); });
      g.globalAlpha = 1;
      g.fillStyle = "#3a2a6a"; g.fillRect(0, H - 22, W, 22);                       // the launch pad
      g.fillStyle = "#ffd23a"; for (let x = 10; x < W; x += 60) g.fillRect(x, H - 14, 30, 6);
      stars.forEach((st) => {
        g.globalAlpha = 0.25; star(st.x, st.y - 18, st.r * 0.6, st.gold ? "#ffd23a" : "#bfe8ff", 0); g.globalAlpha = 1;   // trail
        star(st.x, st.y, st.r, st.gold ? "#ffd23a" : "#fff6b0", (t - st.born) / 400);
      });
      pops.forEach((p) => {
        const k = (t - p.t) / 700; g.globalAlpha = 1 - k; g.fillStyle = p.gold ? "#ffd23a" : "#ffffff";
        g.font = "bold 28px system-ui, sans-serif"; g.textAlign = "center"; g.fillText(p.gold ? "+3" : "+1", p.x, p.y - k * 40); g.globalAlpha = 1;
      });
      drawSprite(icon, t);
    }
    function tap(ev) {
      const rc = field.getBoundingClientRect(), x = ((ev.clientX - rc.left) / rc.width) * W, y = ((ev.clientY - rc.top) / rc.height) * H;
      const hit = stars.find((st) => Math.hypot(st.x - x, st.y - y) < st.r + 18);
      if (!hit) return;
      stars.splice(stars.indexOf(hit), 1);
      pops.push({ x: hit.x, y: hit.y, gold: hit.gold, t: performance.now() });
      s = load(); s.stars += hit.gold ? 3 : 1;
      if (!s.done && s.stars >= GOAL) { s.done = true; s.doneOn = localDay(); if (window.CountdownStars.onDone) window.CountdownStars.onDone(); }
      store(s); show();
    }
    field.addEventListener("pointerdown", tap);
    show(); raf = requestAnimationFrame(frame);
    return { box, stop: () => cancelAnimationFrame(raf) };
  }
  function live() { return localDay() < END; }
  window.CountdownStars = { mount, live, done: () => load().done, reward: REWARD, goal: GOAL, end: END, onDone: null,
                            add: (n) => { const s = load(); s.stars += n; if (s.stars >= GOAL) s.done = true; store(s); return s; } };
})();
