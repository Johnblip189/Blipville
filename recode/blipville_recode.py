"""Blipville Recode: the desktop pets, rebuilt on Qt (PySide6).

Each pet lives in its own small see-through window. Qt gives real per-pixel transparency on Windows, so there are
no black flashes, and clicks pass straight through the empty parts of a window. All the art, colors and lines come
from blipdata.json (made from blip.pyw by tools/export_recode_data.py), and the save file is the same one the
classic app uses, so your town, hearts and unlocks carry over.

    pip install PySide6
    python recode/blipville_recode.py
"""
import json
import math
import os
import random
import subprocess
import sys
import time
import webbrowser

from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QCursor, QFont, QFontMetrics, QGuiApplication, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QInputDialog, QMenu, QMessageBox, QScrollArea, QWidget

# Filled in by the GitHub build. "dev" means "running from source".
APP_VERSION = "dev"
APP_BUILT = ""
APP_NAME = "Blipville Recode"
EXE_NAME = "Blipville-Recode.exe"

SCALE = 4                       # screen pixels per art pixel
ART_W, ART_H = 16, 13
W, H = 220, 180                 # each pet's window (room above it for bubbles and hearts)
FPS = 30
MAX_PETS = 8
UI_BG, UI_CARD, UI_EDGE, UI_GOLD, UI_PINK, UI_GREEN = "#1d1a2e", "#2b2547", "#3a3360", "#ffd23a", "#ff9fc0", "#9ad8a8"


# ----------------------------------------------------------------------------- data
def resource(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


with open(resource("blipdata.json"), encoding="utf-8") as _f:
    DATA = json.load(_f)
KINDS = DATA["kinds"]
G = DATA["groups"]
LINES = DATA["lines"]
HATS = DATA["hats"]
ROBOTS = set(DATA["robots"])
WORLD_OF = DATA["worldOf"]
LEGEND_WORLD = DATA["legendWorld"]
WORLDS = DATA["worlds"]
WORLD_BY_NAME = {w["name"]: w for w in WORLDS}
SHAPES = DATA["shapes"]
HEART, ZED, COOKIE, BALL, BAT, BAT_FLAP, EGG = (SHAPES[k] for k in ("heart", "zed", "cookie", "ball", "bat", "batFlap", "egg"))
SCENES, SCENE_PROPS = DATA["scenes"], DATA["sceneProps"]
SCENE_W, SCENE_H, SCENE_PX = DATA["scene"]
KAIJU_HITS, LURE_COST, BEACON_COST, EGG_COST = DATA["kaijuHits"], DATA["lureCost"], DATA["beaconCost"], DATA["eggCost"]
GIFT = DATA["gift"]
NOTICE = DATA["notice"]


def kind_colors(kind):
    return KINDS[kind]["colors"]


def is_night():
    h = time.localtime().tm_hour
    return h >= 20 or h < 6


def season():
    t = time.localtime()
    md = (t.tm_mon, t.tm_mday)
    if (10, 15) <= md <= (11, 2):
        return "spooky"
    if md >= (12, 1) or md <= (2, 29):
        return "winter"
    if (3, 20) <= md <= (5, 31):
        return "spring"
    if (6, 1) <= md <= (8, 31):
        return "summer"
    return "autumn"


def hat_in_shop(name):
    s = HATS[name].get("season")
    return s is None or s == season()


# ----------------------------------------------------------------------------- sprites (shared by pets and the windows)
def build_grid(kind, ci=0, *, now=0.0, face="normal", blink=False, eye=(0, 0), lying=False, feet="stand", flap=False,
               night_eyes=False):
    """A pet's 16x13 pixel art as rows of colors (None = see-through), face included."""
    v = KINDS[kind]
    cols = kind_colors(kind)
    pal = {**cols[ci % len(cols)], **(v.get("extra") or {})}
    g = [[None] * ART_W for _ in range(ART_H)]
    body = pal.get("art") or (v["alt"] if flap and v.get("alt") else v["body"])
    shift = 1 if lying else 0
    for y, row in enumerate(body):
        for x, ch in enumerate(row):
            if ch != "." and y + shift < ART_H:
                g[y + shift][x] = pal.get(ch, pal["o"])
    dxo = v.get("dx", 0)
    if not lying and v["feet"]:
        for x, ch in enumerate(v["feet"][feet]):
            if ch != "." and 0 <= x + dxo < ART_W:
                g[12][x + dxo] = pal.get("f", pal["o"])
    face_dy = v["eyes"] - 5

    def px(x, y, color):
        y += shift + face_dy
        x += dxo
        if 0 <= x < ART_W and 0 <= y < ART_H:
            g[y][x] = color
    e, white = pal["e"], "#ffffff"
    r_, g_, b_ = (int(e[i:i + 2], 16) for i in (1, 3, 5))
    if 0.299 * r_ + 0.587 * g_ + 0.114 * b_ > 150:
        white = pal["o"]
    if night_eyes:
        white = e
    if face == "sleep" or (blink and face == "normal"):
        for x in (4, 5, 10, 11):
            px(x, 6, e)
    elif face == "happy":
        for ex in (4, 9):
            px(ex, 6, e); px(ex + 1, 5, e); px(ex + 2, 6, e)
    elif face == "munch":
        for ex in (4, 10):
            px(ex, 6, e); px(ex + 1, 6, e)
    else:
        ox, oy = (0, 0) if face == "surprised" else eye
        for ex in (4, 10):
            for yy in range(2):
                for xx in range(2):
                    px(ex + ox + xx, 5 + oy + yy, e)
            px(ex + ox, 5 + oy, white)
    if v.get("mouth", True):
        if face == "surprised":
            px(7, 8, e); px(8, 8, e); px(7, 9, e); px(8, 9, e)
        elif face == "happy":
            px(6, 8, e); px(7, 9, e); px(8, 9, e); px(9, 8, e)
        elif face == "munch":
            if int(now * 8) % 2:
                px(7, 8, e); px(8, 8, e)
            px(7, 9, e); px(8, 9, e)
        elif face != "sleep":
            px(7, 9, e); px(8, 9, e)
    return g


def hat_cells(kind, hat_name, shift=0):
    hat = HATS.get(hat_name)
    if not hat:
        return []
    v = KINDS[kind]
    body = v["body"]
    rows, w = hat["rows"], len(hat["rows"][0])
    left = round(8 - w / 2) + v.get("dx", 0) + hat.get("x", 0)
    if hat["slot"] == "head":
        head_top = next((i for i, r in enumerate(body) if len(r) - r.count(".") >= 8), next(i for i, r in enumerate(body) if r.strip(".")))
        top = head_top + shift + hat.get("overlap", 1) - len(rows)
    elif hat["slot"] == "face":
        top = v["eyes"] + shift + hat.get("y", 0)
    else:
        top = min(v["eyes"] + 5, 11) + shift + hat.get("y", 0)
    return [(top + r, left + c, hat["colors"][ch]) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch != "."]


def paint_grid(p, g, x, y, scale, silhouette=None, mirror=False):
    for r, row in enumerate(g):
        row = row[::-1] if mirror else row
        c = 0
        while c < len(row):
            col = row[c]
            if col is None:
                c += 1
                continue
            c2 = c
            while c2 + 1 < len(row) and row[c2 + 1] == col:
                c2 += 1
            p.fillRect(int(x + c * scale), int(y + r * scale), (c2 - c + 1) * scale, scale, QColor(silhouette or col))
            c = c2 + 1


def paint_sprite(p, kind, ci, x, y, scale, face="normal", hat=None, silhouette=None):
    paint_grid(p, build_grid(kind, ci, face=face), x, y, scale, silhouette)
    if hat and not silhouette:
        for r, c, col in hat_cells(kind, hat):
            p.fillRect(int(x + c * scale), int(y + r * scale), scale, scale, QColor(col))


def paint_shape(p, rows, x, y, size, color):
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "x":
                p.fillRect(int(x + c * size), int(y + r * size), size, size, QColor(color))


# ----------------------------------------------------------------------------- save file + log (shared with the classic app)
def save_dir():
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "Blipville")


def save_path():
    return os.path.join(save_dir(), "save.json")


def load_save():
    try:
        with open(save_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def write_save(data):
    try:
        os.makedirs(save_dir(), exist_ok=True)
        tmp = save_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
        os.replace(tmp, save_path())
    except OSError:
        pass


def log_path():
    return os.path.join(save_dir(), "blipville-recode.log")


def log(message):
    try:
        os.makedirs(save_dir(), exist_ok=True)
        if os.path.exists(log_path()) and os.path.getsize(log_path()) > 200_000:
            with open(log_path(), encoding="utf-8", errors="replace") as f:
                keep = f.read()[-100_000:]
            with open(log_path(), "w", encoding="utf-8") as f:
                f.write(keep)
        with open(log_path(), "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {APP_VERSION} {APP_BUILT} | {message.rstrip()}\n")
    except OSError:
        pass


def ask(title, text):
    return QMessageBox.question(None, title, text) == QMessageBox.Yes


def tell(title, text):
    QMessageBox.information(None, title, text)


# ----------------------------------------------------------------------------- sound effects (made with code, off by default)
def _synth(name):
    import struct
    rate, out = 22050, []

    def tone(f0, f1, dur, vol=0.35, shape="sine", decay=True):
        n, phase = int(rate * dur), 0.0
        for i in range(n):
            t = i / n
            phase += 2 * math.pi * (f0 + (f1 - f0) * t) / rate
            v = math.sin(phase)
            if shape == "square":
                v = 0.6 if v >= 0 else -0.6
            elif shape == "tri":
                v = 2 / math.pi * math.asin(math.sin(phase))
            out.append(v * vol * min(1.0, i / (rate * 0.005)) * ((1 - t) ** 2 if decay else 1))

    def noise(dur, vol=0.3, swell=False):
        n, last = int(rate * dur), 0.0
        for i in range(n):
            t = i / n
            last = last * 0.6 + random.uniform(-1, 1) * 0.4
            out.append(last * vol * (math.sin(math.pi * t) if swell else (1 - t) ** 3))

    def rest(dur):
        out.extend([0.0] * int(rate * dur))
    random.seed(name)
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
        n, phase = int(rate * 0.4), 0.0
        for i in range(n):
            t = i / n
            phase += 2 * math.pi * (260 + 200 * t + 60 * math.sin(t * 40)) / rate
            out.append(math.sin(phase) * 0.4 * (1 - t))
    random.seed()
    frames = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32000)) for v in out)
    header = b"RIFF" + struct.pack("<I", 36 + len(frames)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
    return header + b"data" + struct.pack("<I", len(frames)) + frames


class Sound:
    def __init__(self, app):
        self.app, self.last = app, {}
        self.dir = os.path.join(save_dir(), "sounds-v1")       # same sounds the classic app made

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
        if not self.app.sound_on:
            return
        now = time.monotonic()
        if now - self.last.get(name, 0) < {"thud": 0.8, "munch": 0.5}.get(name, 0.08):
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
        except Exception:  # noqa: BLE001
            pass


# ----------------------------------------------------------------------------- one pet
class Pet(QWidget):
    def __init__(self, app, kind="Blip", name="Blip", x=None):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(W, H)
        self.setWindowTitle(name)
        self.app, self.kind, self.name = app, kind, name
        self.palette_i = KINDS[kind].get("default", 0)
        self.hat = None
        self.hunger, self.energy = 10.0, 100.0
        area = app.area
        self.left, self.top, self.right, self.bottom = area.left(), area.top(), area.right() + 1, area.bottom() + 1
        self.ground = self.bottom - H
        self.wx = x if x is not None else random.uniform(self.left + 50, self.right - W - 50)
        self.wx = min(max(self.wx, self.left), self.right - W)
        self.wy = self.top - H                   # drops in from the top of the screen
        self.vx = self.vy = 0.0
        self.state, self.state_until = "fall", 0.0
        self.target_x, self.facing = None, 1
        self.face, self.face_until = "normal", 0.0
        self.blink_until, self.next_blink = 0.0, time.monotonic() + random.uniform(2, 6)
        self.squash_until = 0.0
        self.bubble = None                       # (text, until)
        self.particles = []
        self.cookie = None
        self.last_pet_reward = self.last_hungry = 0.0
        self.press, self.drag_hist = None, []
        self.follow = False
        self.playing, self.nap_buddy, self.last_play, self.greeted = False, False, 0.0, {}
        self.next_shift = time.monotonic() + random.uniform(8, 15)
        self._key = None
        self.place()
        self.show()

    # ---- basics
    def v(self):
        return KINDS[self.kind]

    def place(self):
        pos = (int(self.wx), int(self.wy))
        if pos != getattr(self, "_placed", None):
            self.move(*pos)
            self._placed = pos

    def set_state(self, state, seconds=0.0):
        self.state, self.state_until = state, time.monotonic() + seconds

    def say(self, text, seconds=3.0):
        self.bubble = (text, time.monotonic() + seconds)

    def set_face(self, face, seconds):
        self.face, self.face_until = face, time.monotonic() + seconds

    def lines(self):
        if self.kind in ROBOTS and is_night():
            return LINES["night"] * 2 + self.v()["lines"]
        return LINES["idle"] + self.v()["lines"] * 2 + LINES["season"].get(season(), [])

    def burst(self, kind, n):
        for _ in range(n):
            self.particles.append({"kind": kind, "x": W / 2 + random.uniform(-26, 26), "y": H - ART_H * SCALE + random.uniform(-6, 6),
                                   "vx": random.uniform(-0.6, 0.6), "vy": random.uniform(-2.2, -1.2),
                                   "life": random.uniform(1.0, 1.6), "born": time.monotonic()})

    def show_reward(self, text):
        self.particles.append({"kind": "plus", "text": text, "x": W / 2 + 34, "y": H - ART_H * SCALE - 4,
                               "vx": 0, "vy": -0.6, "life": 1.6, "born": time.monotonic()})

    # ---- actions
    def pet(self):
        if self.state == "sleep":
            self.wake()
            return
        self.app.sound.play("boop")
        now = time.monotonic()
        if now - self.last_pet_reward > 6:       # petting earns a heart (not by spam-clicking)
            self.last_pet_reward = now
            self.app.add_hearts(1, self)
        self.say(random.choice(LINES["pet"]), 2)
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
        self.say(random.choice(LINES["wake"]), 2.5)
        self.set_face("surprised", 0.8)

    # ---- brain + physics
    def decide(self, now):
        hour = time.localtime().tm_hour
        if self.energy < 25 or (hour >= 23 or hour < 6) and random.random() < 0.15:
            self.say("*yawn* nap time...", 2.5)
            self.set_state("sleep", 20)
            return
        if self.hunger > 70 and now - self.last_hungry > 25:
            self.last_hungry = now
            self.say(random.choice(LINES["hungry"]), 3)
        r = random.random()
        if r < 0.45:
            self.target_x = random.uniform(self.left + 10, self.right - W - 10)
            self.set_state("walk", 12)
        elif r < 0.60:
            self.target_x = min(max(QCursor.pos().x() - W / 2, self.left), self.right - W)
            self.set_state("walk", 6)
        elif r < 0.75:
            self.say(random.choice(self.lines()), 3)
            self.set_state("idle", random.uniform(2, 4))
        else:
            self.set_state("idle", random.uniform(2, 5))

    def update_state(self, now):
        dt = 1 / FPS
        if now > self.next_blink:
            self.blink_until, self.next_blink = now + 0.15, now + random.uniform(2, 6)
        if self.playing:
            return
        if self.state != "sleep":
            self.energy = max(0, self.energy - dt * 0.12)
        self.hunger = min(100, self.hunger + dt * 0.08)
        ck = self.cookie
        if ck and not ck["landed"]:
            ck["vy"] += 0.6
            ck["y"] += ck["vy"]
            if ck["y"] >= H - 6 * 3:
                ck["y"], ck["landed"] = H - 6 * 3, True
        if ck and ck["landed"] and self.state in ("idle", "walk") and not self.follow:
            self.target_x, self.state, self.state_until = ck["x"] - W / 2, "walk", now + 10
        if self.v().get("shifty") and now > self.next_shift and self.state not in ("sleep", "held"):
            self.next_shift = now + random.uniform(8, 15)
            self.palette_i = (self.palette_i + 1) % len(kind_colors(self.kind))

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
                    self.vy, self.vx = -self.vy * 0.35, self.vx * 0.7
                    self.squash_until = now + 0.15
                    if hard:
                        self.say(random.choice(LINES["land"]), 2)
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
                self.particles.append({"kind": "z", "x": W / 2 + 18, "y": H - ART_H * SCALE, "vx": 0.5, "vy": -0.8, "life": 2.5, "born": now})
            if self.energy >= 100 and now > self.state_until:
                self.wake()
                self.app.add_hearts(2, self)
            return
        if st == "eat":
            if now > self.state_until:
                self.app.add_hearts(5 if self.hunger > 60 else 3, self)
                self.hunger, self.energy, self.cookie = 0, min(100, self.energy + 15), None
                self.say(random.choice(LINES["eat"]), 2.5)
                self.set_face("happy", 2)
                self.burst("heart", 5)
                self.set_state("idle", 2)
            elif random.random() < 0.3:
                self.particles.append({"kind": "crumb", "x": W / 2 + random.uniform(-6, 6), "y": H - 22,
                                       "vx": random.uniform(-1.5, 1.5), "vy": random.uniform(-3, -1), "life": 0.6, "born": now})
            return
        if self.follow:
            goal = min(max(QCursor.pos().x() - W / 2, self.left), self.right - W)
            if abs(goal - self.wx) > 50:
                self.target_x, self.state = goal, "walk"
            else:
                self.state, self.state_until = "idle", now + 1
        if self.state == "walk" and self.target_x is not None:
            speed = (3.2 if self.follow else 2.0) * self.v().get("speed", 1.0)
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
        elif self.state == "idle" and now > self.state_until and not self.follow:
            self.decide(now)

    def weather(self, now):
        """Seasonal weather around this pet, or the air of the world you're visiting."""
        dt = 1 / FPS
        world = self.app.world()
        if world:
            rates = world["fx"]
        elif self.app.weather_on:
            rates = {"winter": [("snow", 4.0)], "spring": [("petal", 2.0)], "autumn": [("leaf", 1.8)],
                     "spooky": [("leaf", 1.0), ("bat", 0.12)], "summer": [("firefly", 1.4)] if is_night() else []}.get(season(), [])
        else:
            return
        for kind, rate in rates:
            if random.random() > rate * dt:
                continue
            base = {"kind": kind, "born": now, "phase": random.uniform(0, 6.3)}
            if kind == "bat":
                d = random.choice([-1, 1])
                base.update(x=-10 if d > 0 else W + 10, y=random.uniform(15, 80), vx=1.6 * d, vy=0, life=(W + 20) / 1.6 / FPS)
            elif kind == "firefly":
                base.update(x=random.uniform(10, W - 10), y=random.uniform(40, H - 20), vx=random.uniform(-0.3, 0.3),
                            vy=random.uniform(-0.3, 0.1), life=3.0)
            elif kind == "bubble":
                vy = -random.uniform(0.5, 1.0)
                base.update(x=random.uniform(0, W), y=H + 4, vx=0, vy=vy, life=H / -vy / FPS, size=random.choice([3, 4, 6]))
            elif kind == "star":
                base.update(x=random.uniform(6, W - 6), y=random.uniform(10, H - 30), vx=0, vy=0, life=random.uniform(1.5, 3.0),
                            color=random.choice(["#ffffff", "#fff27a", "#a8d8ff"]))
            else:
                vy = random.uniform(0.3, 0.7) if kind == "ash" else random.uniform(0.6, 1.2) if kind == "sprinkle" else random.uniform(0.5, 1.1)
                colors = {"ash": ["#8a8090", "#5a5060", "#ff8a3a"],
                          "sprinkle": ["#ff5a8a", "#5ad8ff", "#ffd23a", "#8af05a", "#b88aff", "#ffffff"]}.get(kind, ["#e8702a", "#c8402a", "#ffb83a"])
                base.update(x=random.uniform(0, W), y=-4, vx=random.uniform(-0.3, 0.3), vy=vy, life=H / vy / FPS,
                            color=random.choice(colors), tall=random.random() < 0.5)
            self.particles.append(base)

    # ---- art
    def lift(self, now):
        move = self.v()["move"]
        moving = self.state == "walk"
        if move == "float":
            return 2 if self.state == "sleep" else int(9 + 4 * math.sin(now * 2.5))
        if move == "hop" and moving:
            return int(abs(math.sin(now * 7)) * 12)
        if move == "flutter" and moving:
            return int(8 + 3 * math.sin(now * 12))
        return 0

    def eye_offset(self):
        m = QCursor.pos()
        cx, cy = self.wx + W / 2, self.wy + H - ART_H * SCALE + (self.v()["eyes"] + 1) * SCALE
        dx, dy = m.x() - cx, m.y() - cy
        if math.hypot(dx, dy) < 30:
            return 0, 0
        return (-1 if dx < -40 else (1 if dx > 40 else 0)), (-1 if dy < -80 else (1 if dy > 40 else 0))

    def build_art(self, now):
        lying = self.state == "sleep" or now < self.squash_until
        if self.state in ("fall", "held") or self.lift(now) > 3:
            feet = "air"
        elif self.state == "walk":
            feet = "walk1" if int(now * 6) % 2 else "walk2"
        else:
            feet = "stand"
        face = "sleep" if self.state == "sleep" else (self.face if now < self.face_until else "normal")
        g = build_grid(self.kind, self.palette_i, now=now, face=face, blink=now < self.blink_until,
                       eye=self.eye_offset() if face == "normal" else (0, 0), lying=lying, feet=feet,
                       flap=self.state in ("walk", "fall", "held") and int(now * 10) % 2 == 1,
                       night_eyes=self.kind in ROBOTS and is_night())
        return g, 1 if lying else 0

    # ---- frame
    def step(self, now):
        self.weather(now)
        self.update_state(now)
        alive = []
        for p in self.particles:
            if now - p["born"] > p["life"]:
                continue
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["kind"] == "crumb":
                p["vy"] += 0.4
            alive.append(p)
        self.particles = alive
        if self.bubble and now > self.bubble[1]:
            self.bubble = None
        art, shift = self.build_art(now)
        self._frame = (art, shift, self.lift(now), now)
        ball = self.app.ball_near(self)
        key = (str(art), self._frame[2], self.hat, self.bubble and self.bubble[0], self.app.name_tags, self.name)
        if key != self._key or self.particles or self.cookie or ball:
            self._key = key
            self.update()

    def paintEvent(self, _e):
        if not hasattr(self, "_frame"):
            return
        art, shift, lift, now = self._frame
        p = QPainter(self)
        ox = (W - ART_W * SCALE) // 2
        oy = H - ART_H * SCALE - lift
        paint_grid(p, art, ox, oy, SCALE)
        hat_top = 0
        for r, c, col in hat_cells(self.kind, self.hat, shift):
            p.fillRect(ox + c * SCALE, oy + r * SCALE, SCALE, SCALE, QColor(col))
            hat_top = min(hat_top, r * SCALE)
        ball = self.app.ball_near(self)
        if ball:
            bx, by = ball[0] - self.wx, ball[1] - self.wy
            for yy, row in enumerate(BALL):
                for xx, ch in enumerate(row):
                    if ch != ".":
                        p.fillRect(int(bx - 8 + xx * 3), int(by - 8 + yy * 3), 3, 3, QColor({"w": "#ffffff", "r": "#e8303a", "o": "#3a2a3a"}[ch]))
        ck = self.cookie
        if ck:
            cx = (W / 2 + 10 * self.facing) if self.state == "eat" else ck["x"] - self.wx
            bites = 0 if self.state != "eat" else int((1.8 - max(0, self.state_until - now)) / 0.45)
            for y, row in enumerate(COOKIE):
                for x, ch in enumerate(row):
                    if ch == "." or (self.state == "eat" and x >= 6 - bites):
                        continue
                    p.fillRect(int(cx - 9 + x * 3), int(ck["y"] + y * 3), 3, 3, QColor("#c98a4b" if ch == "c" else "#5a3418"))
        self.paint_particles(p, now)
        small = QFont("Segoe UI", 8, QFont.Bold)
        tag_h = 0
        if self.app.name_tags:
            p.setFont(small)
            r = QFontMetrics(small).boundingRect(self.name).adjusted(-4, -1, 4, 1)
            r.moveCenter(QPoint(W // 2, oy + hat_top - 6 - r.height() // 2))
            p.fillRect(r, QColor("#1d1b26"))
            p.setPen(QColor("#ffffff"))
            p.drawText(r, Qt.AlignCenter, self.name)
            tag_h = r.height() + 6
        if self.bubble:
            f = QFont("Segoe UI", 10, QFont.Bold)
            p.setFont(f)
            tr = QFontMetrics(f).boundingRect(QRect(0, 0, W - 30, 400), Qt.TextWordWrap | Qt.AlignCenter, self.bubble[0])
            bottom = oy + hat_top - (6 if self.state != "sleep" else 2) - tag_h - 7
            box = QRect(W // 2 - tr.width() // 2 - 8, bottom - tr.height() - 5, tr.width() + 16, tr.height() + 5)
            path = QPainterPath()
            path.addRoundedRect(box, 6, 6)
            tail = QPainterPath()
            tail.moveTo(W / 2 - 5, box.bottom())
            tail.lineTo(W / 2 + 5, box.bottom())
            tail.lineTo(W / 2, box.bottom() + 7)
            tail.closeSubpath()
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(QPen(QColor("#222222"), 2))
            p.setBrush(QColor("#ffffff"))
            p.drawPath(path.united(tail))
            p.setPen(QColor("#222222"))
            p.drawText(box, Qt.TextWordWrap | Qt.AlignCenter, self.bubble[0])
        p.end()

    def paint_particles(self, p, now):
        small = QFont("Segoe UI", 8, QFont.Bold)
        for q in self.particles:
            age, k = now - q["born"], q["kind"]
            if k == "heart":
                paint_shape(p, HEART, q["x"], q["y"], 3, "#ff4f7b")
            elif k == "z":
                paint_shape(p, ZED, q["x"], q["y"], 2 + int(age), "#bcd2ff")
            elif k == "crumb":
                p.fillRect(int(q["x"]), int(q["y"]), 3, 3, QColor("#c98a4b"))
            elif k == "snow":
                s = 3 if q["phase"] > 2 else 2
                p.fillRect(int(q["x"]), int(q["y"]), s, s, QColor("#f4f8ff"))
            elif k in ("leaf", "petal"):
                x = q["x"] + math.sin(age * 3 + q["phase"]) * 4
                w_, h_, col = (4, 3, q["color"]) if k == "leaf" else (3, 2, "#ffb0d8")
                p.fillRect(int(x), int(q["y"]), w_, h_, QColor(col))
            elif k == "firefly":
                if math.sin(age * 5) > -0.3:
                    p.fillRect(int(q["x"]), int(q["y"]), 3, 3, QColor("#fff08a"))
            elif k == "bat":
                paint_shape(p, BAT if int(age * 8) % 2 else BAT_FLAP, q["x"], q["y"] + math.sin(age * 6) * 3, 2, "#6a4a9a")
            elif k == "bubble":
                x, s = int(q["x"] + math.sin(age * 3 + q["phase"]) * 3), q["size"]
                p.setPen(QColor("#bfe8ff"))
                p.setBrush(Qt.NoBrush)
                p.drawRect(x, int(q["y"]), s, s)
                p.fillRect(x + 1, int(q["y"]) + 1, 1, 1, QColor("#ffffff"))
            elif k == "star":
                if math.sin(age * 6 + q["phase"]) > -0.2:
                    x, y = int(q["x"]), int(q["y"])
                    p.fillRect(x, y - 2, 2, 6, QColor(q["color"]))
                    p.fillRect(x - 2, y, 6, 2, QColor(q["color"]))
            elif k == "sprinkle":
                x = q["x"] + math.sin(age * 2 + q["phase"]) * 2
                p.fillRect(int(x), int(q["y"]), 2 if q["tall"] else 4, 4 if q["tall"] else 2, QColor(q["color"]))
            elif k == "ash":
                p.fillRect(int(q["x"] + math.sin(age * 2 + q["phase"]) * 3), int(q["y"]), 2, 2, QColor(q["color"]))
            elif k == "plus":
                p.setFont(small)
                r = QFontMetrics(small).boundingRect(q["text"]).adjusted(-4, -1, 4, 1)
                r.moveCenter(QPoint(int(q["x"]), int(q["y"])))
                p.fillRect(r, QColor("#e8457a"))
                p.setPen(QColor("#ffffff"))
                p.drawText(r, Qt.AlignCenter, q["text"])

    # ---- mouse
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            g = e.globalPosition().toPoint()
            self.press = (g.x(), g.y(), self.wx, self.wy)
            self.drag_hist = [(time.monotonic(), g.x(), g.y())]

    def mouseMoveEvent(self, e):
        if not self.press:
            return
        g = e.globalPosition().toPoint()
        px_, py_, wx0, wy0 = self.press
        if self.state != "held" and abs(g.x() - px_) + abs(g.y() - py_) < 5:
            return
        if self.state != "held":
            self.playing = False
            self.set_state("held")
            self.say(random.choice(LINES["held"]), 2.5)
            self.set_face("surprised", 9999)
        self.wx, self.wy = wx0 + g.x() - px_, wy0 + g.y() - py_
        self.drag_hist = (self.drag_hist + [(time.monotonic(), g.x(), g.y())])[-6:]
        self.place()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton or not self.press:
            return
        if self.state == "held":
            t0, x0, y0 = self.drag_hist[0]
            g = e.globalPosition().toPoint()
            dt = max(time.monotonic() - t0, 1 / FPS)
            self.vx = max(-40, min(40, (g.x() - x0) / dt / FPS))
            self.vy = max(-40, min(40, (g.y() - y0) / dt / FPS))
            self.set_face("surprised", 0.6)
            self.set_state("fall")
            if abs(self.vx) + abs(self.vy) > 12:
                self.app.sound.play("whoosh")
        else:
            self.pet()
        self.press = None

    def contextMenuEvent(self, e):
        if self.state == "walk":
            self.set_state("idle", 3)
        self.app.menu_for(self).exec(e.globalPos())


# ----------------------------------------------------------------------------- cryptid / kaiju / legend sightings
def scene_pos(keys, t):
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
            return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
    return keys[-1][1], keys[-1][2]


class Sighting(QWidget):
    """A cryptid, kaiju or world legend appears in its own little scene at the bottom of the screen. Click it!"""
    SHADOW, GLOW = "#16121f", "#ffe66a"

    def __init__(self, app, kind):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.app, self.kind = app, kind
        self.scene = sc = SCENES[kind]
        flip = random.random() < 0.5
        self.keys = [(t, SCENE_W - x if flip else x, y) for t, x, y in sc["keys"]]
        self.props = [(n, SCENE_W - x if flip else x, y, layer, flip) for n, x, y, layer in sc["props"]]
        self.clip, self.sc = sc.get("clip", -99), sc.get("scale", 1)
        self.legend, self.kaiju = bool(sc.get("legend")), kind in G["kaiju"]
        self.hits, self.flash_until, self.caught = 0, 0.0, False
        self.cw, self.ch = SCENE_W * SCENE_PX, SCENE_H * SCENE_PX
        self.setFixedSize(self.cw, self.ch)
        a = app.area
        self.wx = random.uniform(a.left(), max(a.left(), a.right() - self.cw))
        self.move(int(self.wx), a.bottom() + 1 - self.ch)
        self.born = time.monotonic()
        self.facing, self.pos, self.moving, self.now = (-1 if flip else 1), self.keys[0][1:], False, self.born
        witness = next((p for p in app.pets if p.state not in ("sleep", "held")), None)
        if witness:
            witness.say(sc["hint"], 4)
        self.show()

    def visible_now(self):
        return self.pos[1] + 12 * self.sc >= self.clip

    def step(self, now):
        t = now - self.born
        if t > self.keys[-1][0]:
            self.leave(escaped=True)
            return
        x, y = scene_pos(self.keys, t)
        nx, _ = scene_pos(self.keys, t + 0.1)
        self.moving = abs(nx - x) > 0.05
        if self.moving:
            self.facing = 1 if nx > x else -1
        move = KINDS[self.kind]["move"]
        if move == "float":
            y += math.sin(t * 2.5) * 1.2
        elif move in ("hop", "flutter") and self.moving:
            y += abs(math.sin(t * 8)) * 2
        self.pos, self.now = (x, y), now
        self.update()

    def mask(self, p, rows, colors, cx, by, t, mirror=False):
        P = SCENE_PX
        w, h = len(rows[0]), len(rows)
        x0 = round(cx - w / 2)
        lit = int(t * 7) % 5 == 0
        for r, row in enumerate(rows):
            row = row[::-1] if mirror else row
            y = (SCENE_H - (by + h - r)) * P
            x = 0
            while x < w:
                ch = row[x]
                if ch == ".":
                    x += 1
                    continue
                x2 = x
                while x2 + 1 < w and row[x2 + 1] == ch:
                    x2 += 1
                col = colors[ch]
                if isinstance(col, list):
                    col = col[1] if lit else col[0]
                p.fillRect(int((x0 + x) * P), int(y), (x2 - x + 1) * P, P, QColor(col))
                x = x2 + 1

    def art(self, now):
        v = KINDS[self.kind]
        if self.legend:                          # legends stroll by in full color
            return build_grid(self.kind, 0, now=now, blink=int(now * 2.5) % 10 == 0,
                              feet="walk1" if int(now * 6) % 2 else "walk2")
        g = [[self.SHADOW if ch != "." else None for ch in row] + [None] * (ART_W - len(row)) for row in v["body"]]
        g.append([None] * ART_W)
        if v.get("feet"):
            for x, ch in enumerate(v["feet"]["walk1" if int(now * 6) % 2 else "walk2"]):
                if ch != "." and 0 <= x < ART_W:
                    g[12][x] = self.SHADOW
        if int(now * 2.5) % 10:                  # glowing eyes, with the odd blink
            for ex in (4, 10):
                g[v["eyes"]][ex] = g[v["eyes"]][ex + 1] = self.GLOW
        return g

    def paintEvent(self, _e):
        p = QPainter(self)
        P, now = SCENE_PX, self.now
        t = now - self.born
        x, y = self.pos
        for name, px_, py_, layer, flip in self.props:
            if layer == "back":
                pr = SCENE_PROPS[name]
                self.mask(p, pr["rows"], pr["colors"], px_, py_, t, flip and name != "rec")
        if self.scene.get("mound") and y < self.clip - 10:
            pr = SCENE_PROPS["mound"]
            self.mask(p, pr["rows"], pr["colors"], x + math.sin(t * 9) * 0.6, 0, t)
        sc, flash = self.sc, now < self.flash_until
        for r, row in enumerate(self.art(now)):
            if y + (12 - r) * sc < self.clip:
                continue
            row = row if self.facing == 1 else row[::-1]
            top = (SCENE_H - (y + (13 - r) * sc)) * P
            for i, col in enumerate(row):
                if col:
                    left = (x + (i - 8) * sc) * P
                    p.fillRect(int(left), int(top), int(P * sc), int(P * sc), QColor("#ffffff" if flash else col))
        if self.scene.get("sparkle") and (not self.moving or self.legend):
            for k in range(3):
                if int(t * 6 + k * 2) % 3:
                    sx, sy = x + self.facing * (8 + k * 2), y + 5 + (k * 3 + int(t * 4)) % 6
                    p.fillRect(int(sx * P), int((SCENE_H - sy) * P), P, P, QColor("#fff27a"))
        for name, px_, py_, layer, flip in self.props:
            if layer == "front":
                pr = SCENE_PROPS[name]
                self.mask(p, pr["rows"], pr["colors"], px_, py_, t, flip and name != "rec")
        if self.visible_now() and self.kaiju:           # how many more clicks it needs
            for k in range(KAIJU_HITS):
                bx, by = (x - 5 + k * 4) * P, (SCENE_H - (y + 13 * sc + 4)) * P
                if by >= 0:
                    p.setPen(QColor("#16121f"))
                    p.setBrush(QColor("#ff5a7a" if k < self.hits else "#ffffff"))
                    p.drawRect(int(bx), int(by), 3 * P, 2 * P)
        elif self.visible_now() and not self.legend:
            qx, qy = x * P - 8, (SCENE_H - (y + 22)) * P
            for r, row in enumerate([".xxx.", "x...x", "...x.", "..x..", ".....", "..x.."]):
                for i, ch in enumerate(row):
                    if ch == "x" and qy >= 0:
                        p.fillRect(int(qx + i * 3), int(qy + r * 3), 3, 3, QColor("#ffffff"))
        p.end()

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton or self.caught or not self.visible_now():
            return
        pt = e.position()
        ux, uy = pt.x() / SCENE_PX, SCENE_H - pt.y() / SCENE_PX
        x, y = self.pos
        if abs(ux - x) > 10 * self.sc or not (max(y, self.clip) - 2 <= uy <= y + 16 * self.sc):
            return
        app, kind = self.app, self.kind
        if self.kaiju:
            self.hits += 1
            if self.hits < KAIJU_HITS:
                self.flash_until = time.monotonic() + 0.15
                app.sound.play("thud")
                w = next((p for p in app.pets if p.state not in ("sleep", "held")), None)
                if w:
                    w.say(random.choice(["again! click it again!", "it's working!", "keep going!!", "almost!"]), 2)
                return
        self.caught = True
        app.save.setdefault("kaiju" if self.kaiju else "legends" if self.legend else "cryptids", []).append(kind)
        write_save(app.save)
        app.sound.play("fanfare")
        screen_x = self.wx + x * SCENE_PX - W / 2
        self.leave()
        pet = app.add_pet(kind, x=screen_x, greet=False)
        if pet:
            pet.wy = pet.ground
            pet.say(f"you spotted me! 📸 i'm a {kind}!", 5)
            pet.set_face("happy", 2)
            pet.burst("heart", 6)
        elif app.pets:
            app.pets[0].say(f"you befriended a {kind}! 📸 (it's in your Collection)", 5)

    def leave(self, escaped=False):
        if self in self.app.sightings:
            self.app.sightings.remove(self)
        self.close()
        self.deleteLater()
        if escaped:
            w = next((p for p in self.app.pets if p.state not in ("sleep", "held")), None)
            if w:
                lines = (["aww, it sparkled away…", "it went back into the world!", "so pretty! next time!"] if self.legend else
                         ["it stomped away!!", "THAT WAS HUGE", "the whole town shook!", "next time we'll get it!"] if self.kaiju else
                         ["did you see that?!", "w-what was THAT?", "i think i saw something…", "*rubs eyes* huh?", "it got away!"])
                w.say(random.choice(lines), 3)


# ----------------------------------------------------------------------------- windows: egg, hat shop, collection
class Panel(QWidget):
    """A small dark window drawn by hand, with clickable rectangles."""
    def __init__(self, title, w, h):
        super().__init__(None, Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowTitle(title)
        self.setFixedSize(w, h)
        self.spots = []                          # (QRect, callback)

    def spot(self, rect, fn):
        self.spots.append((rect, fn))

    def mousePressEvent(self, e):
        pt = e.position().toPoint()
        for rect, fn in reversed(self.spots):
            if rect.contains(pt):
                fn()
                return

    def text(self, p, x, y, s, size=10, color="#ffffff", bold=True, align=Qt.AlignLeft | Qt.AlignVCenter, w=400, h=24):
        p.setFont(QFont("Segoe UI", size, QFont.Bold if bold else QFont.Normal))
        p.setPen(QColor(color))
        flags = align | Qt.TextWordWrap
        rect = QRect(int(x), int(y), int(w), int(h))
        if align & Qt.AlignHCenter:
            rect.moveLeft(int(x - w / 2))
        p.drawText(rect, flags, s)


class EggHatch(Panel):
    """A Mystery Egg wobbles, cracks and hatches a rare Blip."""
    def __init__(self, app, kind):
        super().__init__("Mystery Egg — Blipville", 360, 330)
        self.app, self.kind, self.t0 = app, kind, time.monotonic()
        self.cracked = self.revealed = self.released = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(40)
        self.show()

    def closeEvent(self, e):
        self.release()
        super().closeEvent(e)

    def release(self):
        if not self.released:
            self.released = True
            pet = self.app.add_pet(self.kind)
            if pet:
                pet.say("i'm new here! hi!! ✨", 4)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(UI_BG))
        self.spots = []
        t = time.monotonic() - self.t0
        cx, cy = 180, 150
        if t < 2.6:
            wob = math.sin(t * (6 + t * 6)) * min(10, 2 + t * 4)
            for y, row in enumerate(EGG):
                for x, ch in enumerate(row):
                    if ch != ".":
                        p.fillRect(int(cx - 48 + wob + x * 8), int(cy - 56 + y * 8), 8, 8, QColor({"o": "#3a2a4a", "e": "#fff4dc", "s": "#ff9fd0"}[ch]))
            if t > 1.2:
                if not self.cracked:
                    self.cracked = True
                    self.app.sound.play("crack")
                pts = [(cx - 30 + wob, cy - 8), (cx - 14 + wob, cy - 18), (cx + wob, cy - 6), (cx + 16 + wob, cy - 20), (cx + 30 + wob, cy - 8)]
                n = min(len(pts), 2 + int((t - 1.2) * 3))
                p.setPen(QPen(QColor("#3a2a4a"), 3))
                for a, b in zip(pts[:n], pts[1:n]):
                    p.drawLine(int(a[0]), int(a[1]), int(b[0]), int(b[1]))
            self.text(p, cx, 252, "✨ something is hatching… ✨", 11, "#d8d0ff", align=Qt.AlignHCenter | Qt.AlignVCenter, w=340)
        else:
            if not self.revealed:
                self.revealed = True
                self.app.sound.play("fanfare")
            if t < 2.9:
                p.fillRect(self.rect(), QColor("#ffffff"))
            for i in range(12):
                a = i * math.pi / 6 + t
                r = 90 + 10 * math.sin(t * 4 + i)
                p.fillRect(int(cx + math.cos(a) * r - 3), int(cy - 10 + math.sin(a) * r * 0.7 - 3), 6, 6,
                           QColor(["#ffd23a", "#ff9fd0", "#9ad8ff"][i % 3]))
            paint_sprite(p, self.kind, 0, cx - 48, cy - 64, 6, face="happy")
            self.text(p, cx, 222, f"You hatched a {self.kind}!", 15, align=Qt.AlignHCenter | Qt.AlignVCenter, w=340, h=30)
            found = sum(1 for k in G["rare"] if self.app.is_unlocked(k))
            self.text(p, cx, 252, f"Rare Blips found: {found}/{len(G['rare'])}", 10, "#b8b2d8", False, Qt.AlignHCenter | Qt.AlignVCenter, w=340)
            btn = QRect(110, 282, 140, 34)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#6a4cff"))
            p.drawRoundedRect(btn, 10, 10)
            self.text(p, 180, 282, "Yay! Let it out 🐾", 11, align=Qt.AlignHCenter | Qt.AlignVCenter, w=140, h=34)
            self.spot(btn, self.close)
        p.end()


class HatShop(Panel):
    COLS, CW, CH = 4, 132, 150

    def __init__(self, app, pet):
        self.names = [n for n in HATS if hat_in_shop(n)]
        rows = -(-len(self.names) // self.COLS)
        super().__init__(f"Hats & outfits — {pet.name}", self.COLS * self.CW + 20, rows * self.CH + 70)
        self.app, self.pet = app, pet
        self.show()

    def owned(self):
        return self.app.save.setdefault("hats_owned", [])

    def paintEvent(self, _e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(UI_BG))
        self.spots, pet = [], self.pet
        self.text(p, 16, 10, f"🎩 Dress up {pet.name}", 14, w=360, h=26)
        self.text(p, self.width() - 216, 10, f"💖 {self.app.hearts()}", 13, UI_PINK, align=Qt.AlignRight | Qt.AlignVCenter, w=200, h=26)
        for i, name in enumerate(self.names):
            hat = HATS[name]
            x0, y0 = 10 + (i % self.COLS) * self.CW, 50 + (i // self.COLS) * self.CH
            wearing, owned = pet.hat == name, name in self.owned()
            box = QRect(x0, y0, self.CW - 10, self.CH - 10)
            p.setPen(QPen(QColor(UI_GOLD if wearing else UI_EDGE), 3 if wearing else 2))
            p.setBrush(QColor(UI_CARD))
            p.drawRect(box)
            paint_sprite(p, pet.kind, pet.palette_i, x0 + 29, y0 + 30, 4, hat=name)
            self.text(p, x0 + (self.CW - 10) / 2, y0 + 92, name, 10, align=Qt.AlignHCenter | Qt.AlignVCenter, w=self.CW - 14)
            label = "✓ wearing · click to remove" if wearing else ("owned · click to wear" if owned else f"💖 {hat['price']}")
            self.text(p, x0 + (self.CW - 10) / 2, y0 + 112, label, 7, UI_GOLD if wearing else (UI_GREEN if owned else UI_PINK),
                      align=Qt.AlignHCenter | Qt.AlignVCenter, w=self.CW - 18, h=24)
            self.spot(box, lambda n=name: self.pick(n))
        p.end()

    def pick(self, name):
        pet, app = self.pet, self.app
        if pet.hat == name:
            pet.hat = None
            pet.say("back to basics!", 2)
        elif name in self.owned():
            pet.hat = name
            pet.say(random.choice(["how do i look?", "so stylish!", "*strikes a pose*"]), 2.5)
            pet.set_face("happy", 1.5)
        else:
            price = HATS[name]["price"]
            if app.hearts() < price:
                tell("Hats & outfits", f"{name} costs {price} 💖. You have {app.hearts()}.\n\nPet, feed and nap your Blips to earn more hearts!")
                return
            app.save["hearts"] = app.hearts() - price
            self.owned().append(name)
            write_save(app.save)
            pet.hat = name
            pet.say(f"a new {name.lower()}! thank you!!", 3)
            app.sound.play("coin")
            pet.set_face("happy", 2)
            pet.burst("heart", 5)
        app.save_town()
        self.update()


class CollectionView(Panel):
    COLS, CW, CH = 13, 84, 92

    def __init__(self, app):
        self.groups = [("Rare ✨  hatch them from Mystery Eggs", G["rare"]), ("Night Shift 🌙  survive the nights", G["nightShift"]),
                       ("Cryptids 👣  spot them wandering by, then click them!", G["cryptids"]),
                       (f"Kaiju 🦖  super rare! click one {KAIJU_HITS} times before it stomps off", G["kaiju"]),
                       ("Legends ✨  visit a world and click them when they stroll by", G["legends"]),
                       ("Gifts 🎁  limited-time thank-you Blips", G["gifts"])]
        h = 60 + sum(34 + -(-len(k) // self.COLS) * self.CH for _, k in self.groups)
        super().__init__("Blipville collection", self.COLS * self.CW + 20, h)
        self.app = app

    def peeked(self):
        return self.app.save.setdefault("peeked", [])

    def how(self, k):
        if k in DATA["unlocks"]:
            return f"survive Night {DATA['unlocks'][k]}"
        if k in G["cryptids"]:
            return "spot it in the wild"
        if k in G["kaiju"]:
            return "catch it in the city"
        if k in G["gifts"]:
            return "a limited-time gift"
        if k in LEGEND_WORLD:
            return f"find it in {LEGEND_WORLD[k]}"
        return "hatch from an egg"

    def paintEvent(self, _e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(UI_BG))
        self.spots = []
        every = [k for _, ks in self.groups for k in ks]
        found = sum(1 for k in every if self.app.is_unlocked(k))
        self.text(p, 16, 12, f"📖 Collection  {found}/{len(every)}", 14, w=400, h=26)
        if any(not self.app.is_unlocked(k) and k not in self.peeked() for k in every):
            r = QRect(self.width() - 230, 12, 214, 26)
            self.text(p, r.x(), r.y(), "👀 peek at all (spoilers!)", 10, UI_PINK, align=Qt.AlignRight | Qt.AlignVCenter, w=214, h=26)
            self.spot(r, self.peek_all)
        y = 50
        for title, kinds in self.groups:
            self.text(p, 16, y, title, 10, UI_GOLD, w=900)
            y += 30
            for i, k in enumerate(kinds):
                x0, y0 = 10 + (i % self.COLS) * self.CW, y + (i // self.COLS) * self.CH
                open_, peek = self.app.is_unlocked(k), k in self.peeked()
                box = QRect(x0, y0, self.CW - 8, self.CH - 8)
                p.setPen(QPen(QColor(UI_EDGE if open_ else UI_CARD), 2))
                p.setBrush(QColor(UI_CARD))
                p.drawRect(box)
                paint_sprite(p, k, KINDS[k].get("default", 0), x0 + 14, y0 + 4, 3, silhouette=None if open_ or peek else "#0f0d1a")
                mid = x0 + (self.CW - 8) / 2
                self.text(p, mid, y0 + 44, k if open_ or peek else "???", 8, "#ffffff" if open_ else "#b8b0d8",
                          align=Qt.AlignHCenter | Qt.AlignVCenter, w=self.CW - 12, h=18)
                sub = "✓ yours!" if open_ else (f"🔒 {self.how(k)}" if peek else "peek 👀")
                self.text(p, mid, y0 + 60, sub, 7, UI_GREEN if open_ else UI_PINK, align=Qt.AlignHCenter | Qt.AlignTop, w=self.CW - 12, h=24)
                if not open_ and not peek:
                    self.spot(box, lambda k=k: self.peek(k))
            y += -(-len(kinds) // self.COLS) * self.CH + 4
        p.end()

    def peek(self, k):
        if ask("Spoiler warning 👀", "Peek at this locked Blip?\n\nYou'll see what it looks like before you unlock it."):
            self.peeked().append(k)
            write_save(self.app.save)
            self.app.sound.play("pop")
            self.update()

    def peek_all(self):
        if ask("Spoiler warning 👀", "Peek at every locked Blip?\n\nYou'll see what they look like before you unlock them."):
            self.peeked().extend(k for _, ks in self.groups for k in ks if k not in self.peeked())
            write_save(self.app.save)
            self.update()


# ----------------------------------------------------------------------------- Night Shift minigame
class NightShift(Panel):
    """Survive 12 AM → 6 AM while the Night Shift crew wanders toward your office. FLASH a doorway to send a robo back
    to the stage. A robo you're watching on camera can't move, but cameras and flashes use battery."""
    HOUR, CW, CH = 20.0, 720, 380
    ROOMS = ["Stage", "Arcade", "Kitchen", "West Hall", "East Hall"]
    NEXT = {"Stage": ("Arcade", "Kitchen"), "Arcade": ("West Hall",), "Kitchen": ("East Hall",), "West Hall": ("door_L",), "East Hall": ("door_R",)}
    NIGHTS = {1: dict(robots=["Robo Bear"], interval=6.0, chance=0.55, grace=3.4),
              2: dict(robots=["Robo Bear", "Robo Bunny"], interval=4.4, chance=0.66, grace=2.2),
              3: dict(robots=["Robo Bear", "Robo Bunny", "Robo Hen"], interval=3.9, chance=0.75, grace=1.9)}
    MIDNIGHT = 3
    FLASH_COST, DRAIN, CAM_DRAIN = 5.0, 0.2, 0.5
    BG, PANEL, TXT, DIM = "#0c0b14", "#1d1a2e", "#e8e4ff", "#7a7598"

    def __init__(self, app):
        super().__init__("Night Shift — Blipville", self.CW + 20, self.CH + 70)
        self.app, self.state = app, "menu"
        self.night = min(app.nights_won() + 1, 3)
        self.last = time.monotonic()
        self.setFocusPolicy(Qt.StrongFocus)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loop)
        self.timer.start(50)
        self.show()
        self.activateWindow()

    def closeEvent(self, e):
        self.timer.stop()
        self.app.game = None
        super().closeEvent(e)

    # ---- flow
    def start(self, night):
        cfg = self.NIGHTS[night]
        self.night, self.cfg = night, cfg
        self.t, self.battery, self.cam = 0.0, 100.0, None
        self.flash_until, self.flash_side, self.flashed = -1.0, None, None
        self.msg, self.msg_until = f"Night {night} — good luck! 🔦", 3.0
        self.robots = [{"kind": k, "room": "Stage", "next": random.uniform(4, 9) + i * 2.5, "door_since": None} for i, k in enumerate(cfg["robots"])]
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
        hit = [r for r in self.robots if r["room"] == "door_" + side]
        self.flashed = hit[0]["kind"] if hit else None
        for r in hit:
            r["room"], r["door_since"], r["next"] = "Stage", None, self.t + self.cfg["interval"] * 1.3
        self.say(f"*clank clank* {hit[0]['kind']} ran back to the stage!" if hit else "nothing there… this time.")
        self.app.sound.play("zap")

    def open_cam(self, room):
        if self.state == "play" and self.battery > 0:
            self.cam = room

    def office(self):
        if self.state == "play":
            self.cam = None

    def won(self):
        self.state = "won"
        self.app.sound.play("fanfare")
        first = self.night > self.app.nights_won()
        self.app.record_night(self.night)
        self.app.add_hearts(25 if first else 10)
        unlock = next((k for k, n in DATA["unlocks"].items() if n == self.night), None)
        self.new_unlock = unlock if unlock and not self.app.is_unlocked(unlock) else None
        if self.new_unlock:
            self.app.unlock(self.new_unlock)
            pet = self.app.add_pet(self.new_unlock)
            if pet:
                pet.palette_i = self.MIDNIGHT
                pet.say("*whirr* ...i'm free! hi!!", 4)

    def update_game(self, dt):
        self.t += dt
        cfg = self.cfg
        self.battery = max(0.0, self.battery - (self.DRAIN + (self.CAM_DRAIN if self.cam else 0)) * dt)
        if self.battery <= 0 and self.cam:
            self.cam = None
            self.say("the battery died… 🔋 lights out!", 4)
        for r in self.robots:
            if r["room"].startswith("door"):
                if self.t - r["door_since"] > cfg["grace"]:
                    self.state, self.caught_by = "caught", r["kind"]
                    self.app.sound.play("boing")
                    return
                continue
            if self.t < r["next"]:
                continue
            r["next"] = self.t + cfg["interval"] * random.uniform(0.7, 1.3)
            if self.cam == r["room"]:
                continue
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
        dt, self.last = min(0.25, now - self.last), now
        if self.state == "play":
            self.update_game(dt)
        self.update()

    def keyPressEvent(self, e):
        k = e.key()
        if k in (Qt.Key_Left, Qt.Key_A):
            self.flash("L")
        elif k in (Qt.Key_Right, Qt.Key_D):
            self.flash("R")
        elif k in (Qt.Key_Space, Qt.Key_Escape):
            self.office()
        elif Qt.Key_1 <= k <= Qt.Key_5:
            self.open_cam(self.ROOMS[k - Qt.Key_1])

    # ---- drawing helpers (game area starts at (10, 10))
    def rect(self, p, x0, y0, x1, y1, fill, edge=None, width=2):
        p.setPen(QPen(QColor(edge), width) if edge else Qt.NoPen)
        p.setBrush(QColor(fill) if fill else Qt.NoBrush)
        p.drawRect(QRect(int(10 + x0), int(10 + y0), int(x1 - x0), int(y1 - y0)))

    def label(self, p, x, y, s, size=11, color=None, bold=True, anchor="c", w=600):
        color = color or self.TXT
        if anchor == "c":
            self.text(p, 10 + x, 10 + y - 14, s, size, color, bold, Qt.AlignHCenter | Qt.AlignVCenter, w=w, h=28)
        elif anchor == "w":
            self.text(p, 10 + x, 10 + y - 14, s, size, color, bold, Qt.AlignLeft | Qt.AlignVCenter, w=w, h=28)
        else:
            self.text(p, 10 + x - w, 10 + y - 14, s, size, color, bold, Qt.AlignRight | Qt.AlignVCenter, w=w, h=28)

    def button(self, p, x, y, text, fn, primary=False, enabled=True, in_game=True, tw=None):
        tw = tw or len(text) * 8 + 34
        r = QRect(int((10 if in_game else 0) + x - tw / 2), int((10 if in_game else 0) + y - 18), int(tw), 36)
        p.setPen(QPen(QColor("#3a3360"), 2))
        p.setBrush(QColor(("#6a4cff" if primary else self.PANEL) if enabled else "#15131f"))
        p.drawRoundedRect(r, 8, 8)
        self.text(p, r.center().x(), r.y(), text, 10, self.TXT if enabled else self.DIM, True, Qt.AlignHCenter | Qt.AlignVCenter, w=tw, h=36)
        if enabled:
            self.spot(r, fn)

    def sprite(self, p, kind, ci, x, y, scale, face="normal", locked=False):
        paint_grid(p, build_grid(kind, ci, face=face, night_eyes=True), 10 + x, 10 + y, scale, "#16121f" if locked else None)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.fillRect(self.rect_all(), QColor(self.BG))
        self.spots = []
        getattr(self, "draw_" + self.state)(p)
        bar_y, playing = self.CH + 36, self.state == "play"   # the control bar under the game
        self.button(p, 60, bar_y, "◀ FLASH", lambda: self.flash("L"), enabled=playing, in_game=False)
        self.button(p, 168, bar_y, "OFFICE", self.office, enabled=playing, in_game=False)
        x = 222
        for i, (room, short) in enumerate(zip(self.ROOMS, ("Stage", "Arcade", "Kitchen", "W Hall", "E Hall")), 1):
            label = f"{i} {short}"
            tw = len(label) * 7 + 22
            self.button(p, x + tw / 2, bar_y, label, lambda r=room: self.open_cam(r), enabled=playing, in_game=False, tw=tw)
            x += tw + 4
        self.button(p, self.width() - 60, bar_y, "FLASH ▶", lambda: self.flash("R"), enabled=playing, in_game=False)
        p.end()

    def rect_all(self):
        return QRect(0, 0, self.width(), self.height())

    def draw_menu(self, p):
        W_ = self.CW
        self.label(p, W_ / 2, 46, "NIGHT SHIFT 🌙", 24)
        self.text(p, 10 + W_ / 2, 84, "Survive from 12 AM to 6 AM. The Night Shift crew wanders toward your office.\n"
                  "Glowing eyes in a doorway? FLASH that side (◀ ▶ or A / D) to send them back to the stage.\n"
                  "Check rooms with the cameras (1–5): a robo you're watching can't move. But cameras and flashes use battery!",
                  9, "#b8b2d8", False, Qt.AlignHCenter | Qt.AlignTop, w=620, h=70)
        for i, k in enumerate(G["nightShift"]):
            x = W_ / 2 - 150 + i * 150
            unlocked = self.app.is_unlocked(k)
            self.sprite(p, k, self.MIDNIGHT, x - 32, 165, 4, locked=not unlocked)
            self.label(p, x, 236, k if unlocked else "🔒 " + k, 9, self.TXT if unlocked else self.DIM)
            self.label(p, x, 252, f"Night {DATA['unlocks'][k]}", 8, self.DIM, False)
        best = self.app.nights_won()
        for n in (1, 2, 3):
            self.button(p, W_ / 2 - 170 + (n - 1) * 170, 300, f"Night {n}" + (" ✓" if n <= best else ""),
                        lambda n=n: self.start(n), primary=(n == self.night), enabled=n <= best + 1)
        self.label(p, W_ / 2, 346, "Close this window anytime. Your progress is saved.", 8, self.DIM, False)

    def draw_play(self, p):
        W_, H_ = self.CW, self.CH
        (self.draw_camera if self.cam else self.draw_office)(p)
        self.rect(p, 0, 0, W_, 34, "#08070e")
        hour = int(self.t // self.HOUR)
        self.label(p, 14, 17, f"NIGHT {self.night}", 11, anchor="w")
        self.label(p, W_ / 2, 17, "12 AM" if hour == 0 else f"{hour} AM", 13, UI_GOLD)
        b = self.battery
        self.label(p, W_ - 160, 17, "🔋", 11, anchor="e", w=40)
        self.rect(p, W_ - 152, 9, W_ - 52, 25, None, "#3a3360")
        self.rect(p, W_ - 150, 11, W_ - 150 + 96 * b / 100, 23, "#5ad87a" if b > 50 else ("#ffd23a" if b > 20 else "#ff4a5a"))
        self.label(p, W_ - 8, 17, f"{int(b)}%", 9, anchor="e", w=40)
        if self.t < self.msg_until:
            self.rect(p, W_ / 2 - 230, H_ - 30, W_ / 2 + 230, H_ - 6, "#08070e", "#3a3360", 1)
            self.label(p, W_ / 2, H_ - 18, self.msg, 10, w=460)

    def draw_office(self, p):
        W_, H_ = self.CW, self.CH
        dark = self.battery <= 0
        self.rect(p, 0, 34, W_, H_, "#0e0c18" if dark else "#1b1830")
        self.rect(p, 0, 280, W_, H_, "#0a0912" if dark else "#14121f")
        if not dark:
            self.rect(p, 250, 236, 470, 252, "#3a2e4a")
            self.rect(p, 262, 252, 274, 300, "#2a2238")
            self.rect(p, 446, 252, 458, 300, "#2a2238")
            lamp = QPainterPath()
            lamp.moveTo(420, 206); lamp.lineTo(450, 206); lamp.lineTo(460, 224); lamp.lineTo(410, 224); lamp.closeSubpath()
            p.setPen(Qt.NoPen); p.setBrush(QColor("#ffd27a")); p.drawPath(lamp)
            self.rect(p, 423, 214, 427, 236, "#8a7a9a")
            paint_sprite(p, "Blip", 0, 310, 194, 3, face="happy")
            self.rect(p, 330, 120, 390, 170, "#2a3a5a", "#3a3360", 3)
            self.rect(p, 340, 130, 343, 133, "#ffffff")
            self.rect(p, 372, 146, 375, 149, "#ffffff")
        for side, x0 in (("L", 30), ("R", 560)):
            x1 = x0 + 130
            flashing = self.t < self.flash_until and self.flash_side == side
            self.rect(p, x0, 70, x1, 300, "#f6eec0" if flashing else "#040308", "#3a3360", 4)
            if flashing and self.flashed:
                self.sprite(p, self.flashed, self.MIDNIGHT, x0 + 1, 140, 8)
            robot = next((r for r in self.robots if r["room"] == "door_" + side), None)
            if robot and not flashing and int(self.t * 3 + (1 if side == "R" else 0)) % 7:
                e = kind_colors(robot["kind"])[self.MIDNIGHT]["e"]
                for ex in (x0 + 38, x0 + 76):
                    self.rect(p, ex, 170, ex + 16, 186, e)
            self.label(p, (x0 + x1) / 2, 316, "◀ A" if side == "L" else "D ▶", 9, self.DIM)

    def draw_camera(self, p):
        W_, H_ = self.CW, self.CH
        room = self.cam
        self.rect(p, 0, 34, W_, H_, "#101a14")
        self.rect(p, 0, 250, W_, H_, "#0b130e")
        if room == "Stage":
            for i in range(12):
                self.rect(p, 60 + i * 50, 60, 82 + i * 50, 250, "#3a1420")
            self.rect(p, 40, 240, W_ - 40, 262, "#2a2010")
        elif room == "Arcade":
            for i in range(5):
                x = 70 + i * 130
                self.rect(p, x, 120, x + 60, 250, "#1a1a3a", "#3a3a7a")
                self.rect(p, x + 10, 135, x + 50, 170, "#2a6a5a")
        elif room == "Kitchen":
            self.rect(p, 40, 190, W_ - 40, 250, "#2a2a2a")
            for i in range(8):
                self.rect(p, 60 + i * 80, 120, 110 + i * 80, 160, "#3a3a3a")
        else:
            for pts in (((0, 60), (W_ / 2 - 60, 140), (W_ / 2 - 60, 230), (0, 330)), ((W_, 60), (W_ / 2 + 60, 140), (W_ / 2 + 60, 230), (W_, 330))):
                path = QPainterPath()
                path.moveTo(10 + pts[0][0], 10 + pts[0][1])
                for x, y in pts[1:]:
                    path.lineTo(10 + x, 10 + y)
                path.closeSubpath()
                p.setPen(Qt.NoPen); p.setBrush(QColor("#162016")); p.drawPath(path)
        here = [r for r in self.robots if r["room"] == room]
        for i, r in enumerate(here):
            self.sprite(p, r["kind"], self.MIDNIGHT, W_ / 2 - len(here) * 70 + i * 140 + 6, 150, 8)
        for _ in range(28):
            y = random.randrange(34, H_)
            p.setPen(QColor(random.choice(["#1e2a22", "#26332a", "#18221b"])))
            p.drawLine(10, 10 + y, 10 + W_, 10 + y)
        self.label(p, 16, 52, f"● CAM {self.ROOMS.index(room) + 1} · {room.upper()}", 11, "#ff4a5a", anchor="w")
        self.label(p, W_ - 16, 52, "watching — it can't move" if here else "empty", 9, UI_GREEN, anchor="e", w=300)

    def draw_caught(self, p):
        W_, H_ = self.CW, self.CH
        self.rect(p, 0, 0, W_, H_, "#14081a")
        self.sprite(p, self.caught_by, self.MIDNIGHT, W_ / 2 - 80, 40, 10)
        self.label(p, W_ / 2, 200, "GOTCHA! 🤖", 24, "#ff4a6a")
        self.label(p, W_ / 2, 236, f"{self.caught_by} got into the office. (it just wanted a hug)", 11, "#d8c8f0", False)
        self.button(p, W_ / 2 - 100, 300, f"Try Night {self.night} again", lambda: self.start(self.night), primary=True)
        self.button(p, W_ / 2 + 120, 300, "Menu", lambda: setattr(self, "state", "menu"))

    def draw_won(self, p):
        W_, H_ = self.CW, self.CH
        self.rect(p, 0, 0, W_, H_, "#2a1a3a")
        self.rect(p, 0, H_ - 120, W_, H_, "#ffb86a")
        self.label(p, W_ / 2, 56, "6 AM 🌅", 26, UI_GOLD)
        self.label(p, W_ / 2, 100, f"You survived Night {self.night}!", 15)
        if self.new_unlock:
            self.sprite(p, self.new_unlock, self.MIDNIGHT, W_ / 2 - 48, 130, 6, face="happy")
            self.label(p, W_ / 2, 222, f"UNLOCKED: {self.new_unlock}! It's on your desktop now.", 12, "#ffffff")
        else:
            paint_sprite(p, "Blip", 0, 10 + W_ / 2 - 48, 140, 6, face="happy")
            self.label(p, W_ / 2, 222, "Blip is proud of you.", 12, "#ffffff")
        if self.night < 3:
            self.button(p, W_ / 2 - 100, 300, f"Night {self.night + 1} ▶", lambda: self.start(self.night + 1), primary=True)
            self.button(p, W_ / 2 + 100, 300, "Menu", lambda: setattr(self, "state", "menu"))
        else:
            self.label(p, W_ / 2, 258, "You beat every night. The whole crew is yours! 🏆", 11, "#3a1a14")
            self.button(p, W_ / 2, 310, "Menu", lambda: setattr(self, "state", "menu"))


def open_collection(app):
    view = CollectionView(app)
    scroll = QScrollArea()
    scroll.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
    scroll.setWindowTitle("Blipville collection")
    scroll.setWidget(view)
    scroll.setStyleSheet(f"QScrollArea {{ background: {UI_BG}; border: 0; }}")
    scroll.resize(view.width() + 20, min(view.height() + 4, app.area.height() - 120))
    scroll.show()
    app.windows.append(scroll)


# ----------------------------------------------------------------------------- the app
class App:
    def __init__(self):
        self.qt = QApplication.instance() or QApplication(sys.argv)
        self.qt.setQuitOnLastWindowClosed(False)
        self.qt.setApplicationName(APP_NAME)
        self.area = QGuiApplication.primaryScreen().availableGeometry()
        self.save = load_save()
        self.name_tags = bool(self.save.get("name_tags", True))
        self.sound_on = bool(self.save.get("sound", False))
        self.weather_on = bool(self.save.get("weather", True))
        self.sound = Sound(self)
        self.pets, self.sightings, self.plays, self.windows = [], [], [], []
        self.game = None
        now = time.monotonic()
        self.last_town_save = now
        self.next_sighting = now + random.uniform(6, 14) * 60
        self.next_kaiju = now + random.uniform(30, 60) * 60
        self.next_legend = now + random.uniform(1, 3) * 60
        self._logged = {}
        self.updater = Updater(self)
        log(f"started {APP_NAME} on {sys.platform}, Python {sys.version.split()[0]}")
        if not self.restore_town():
            self.add_pet("Blip", "Blip")
        QTimer.singleShot(1600, self.daily_treat)
        QTimer.singleShot(2500, self.show_notice)
        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.timer.start(int(1000 / FPS))
        self.updater.start()

    # ---- hearts, unlocks, worlds
    def hearts(self):
        return int(self.save.get("hearts", 0))

    def add_hearts(self, n, pet=None):
        self.save["hearts"] = self.hearts() + n
        write_save(self.save)
        if pet is not None:
            pet.show_reward(f"+{n} 💖")

    def is_unlocked(self, kind):
        s = self.save
        if kind in LEGEND_WORLD:
            return kind in s.get("legends", [])
        if kind in WORLD_OF:
            return WORLD_OF[kind] in s.get("worlds", [])
        if kind in G["gifts"]:
            return kind in s.get("gifts", [])
        if kind in G["kaiju"]:
            return kind in s.get("kaiju", [])
        if kind in G["cryptids"]:
            return kind in s.get("cryptids", [])
        if kind in G["rare"]:
            return kind in s.get("hatched", [])
        return kind not in DATA["unlocks"] or kind in s.get("unlocked", [])

    def world(self):
        w = self.save.get("world")
        return WORLD_BY_NAME.get(w) if w in self.save.get("worlds", []) else None

    def visit_world(self, name):
        self.save["world"] = name
        write_save(self.save)
        w = WORLD_BY_NAME.get(name)
        for p in self.pets:
            p.particles = [q for q in p.particles if q["kind"] in ("heart", "z", "crumb", "plus")]
        if name:
            self.next_legend = min(self.next_legend, time.monotonic() + random.uniform(45, 120))
        if self.pets:
            self.pets[0].say(f"welcome to {name}! {w['icon']}" if w else "home sweet home!", 3)
            self.pets[0].set_face("happy", 1.5)

    def unlock_world(self, name):
        w = WORLD_BY_NAME[name]
        if name in self.save.get("worlds", []):
            self.visit_world(name)
            return
        if self.hearts() < w["cost"]:
            tell(name, f"{name} {w['icon']} costs {w['cost']} 💖 hearts. You have {self.hearts()}.\n\nPet, feed and care for your Blips to earn more!")
            return
        if not ask(name, f"Unlock {name} {w['icon']} for {w['cost']} 💖?\n\nYou'll be able to pick every Blip in the {w['tab']} tab, "
                   "and your town can visit it any time."):
            return
        self.save["hearts"] = self.hearts() - w["cost"]
        self.save.setdefault("worlds", []).append(name)
        write_save(self.save)
        self.sound.play("fanfare")
        self.visit_world(name)
        pet = self.add_pet(random.choice([k for k, wn in WORLD_OF.items() if wn == name]), greet=False)
        if pet:
            pet.say(f"hi! i'm from {name} {w['icon']}", 4)
            pet.burst("heart", 6)

    def daily_treat(self):
        today = time.strftime("%Y-%m-%d")
        if self.save.get("last_day") != today and self.pets:
            self.save["last_day"] = today
            self.add_hearts(10, self.pets[0])
            self.pets[0].say("daily treat! +10 💖", 4)

    def give_gift(self):
        g = GIFT.get("now")
        if not g or g in self.save.get("gifts", []) or time.strftime("%Y-%m-%d") > GIFT["until"]:
            return False
        self.save.setdefault("gifts", []).append(g)
        write_save(self.save)
        pet = self.add_pet(g, greet=False)
        if pet:
            pet.say(f"surprise!! i'm {g}, a gift for you 🎁", 5)
            pet.set_face("happy", 2)
            pet.burst("heart", 8)
        self.sound.play("fanfare")
        return True

    def show_notice(self):
        gift = self.give_gift()
        g = GIFT.get("now")
        if self.save.get("notice_seen") != NOTICE["id"]:
            self.save["notice_seen"] = NOTICE["id"]
            write_save(self.save)
            tell("Blipville 💜", NOTICE["text"] + (f"\n\n🎁 As a thank-you, here's {g}: a limited-edition Blip, only given out until "
                                                  f"{GIFT['untilText']}." if gift else ""))
        elif gift:
            tell("A gift for you! 🎁", f"Here's {g}, a limited-edition Blip, only given out until {GIFT['untilText']}.\n\n"
                 "Find it any time under Change kind → Gifts 🎁.")

    # ---- Night Shift
    def nights_won(self):
        return int(self.save.get("nights_won", 0))

    def record_night(self, night):
        if night > self.nights_won():
            self.save["nights_won"] = night
            write_save(self.save)

    def unlock(self, kind):
        got = self.save.setdefault("unlocked", [])
        if kind not in got:
            got.append(kind)
            write_save(self.save)

    def open_night_shift(self):
        if self.game:
            self.game.raise_()
            self.game.activateWindow()
        else:
            self.game = NightShift(self)

    # ---- eggs, lures
    def open_egg(self):
        left = [k for k in G["rare"] if not self.is_unlocked(k)]
        if not left:
            tell("Mystery Egg", "You've hatched every rare Blip! 🏆")
            return
        if self.hearts() < EGG_COST:
            tell("Mystery Egg", f"A Mystery Egg costs {EGG_COST} 💖 hearts. You have {self.hearts()}.\n\n"
                 "Earn hearts by taking care of your Blips:\n  💖 pet them (+1)\n  🍪 feed them a cookie (+3, or +5 when they're hungry)\n"
                 "  💤 let them nap until rested (+2)\n  🎁 come back each day for a daily treat (+10)")
            return
        kind = random.choices(left, weights=[0.25 if k == "Golden Blip" else 1.0 for k in left])[0]
        self.save["hearts"] = self.hearts() - EGG_COST
        self.save.setdefault("hatched", []).append(kind)
        write_save(self.save)
        self.windows.append(EggHatch(self, kind))

    def set_lure(self, beacon=False):
        kinds, cost = (G["kaiju"], BEACON_COST) if beacon else (G["cryptids"], LURE_COST)
        what = "Kaiju Beacon" if beacon else "Cryptid Lure"
        if all(self.is_unlocked(k) for k in kinds):
            tell(what, "You've caught them all! 🏆")
            return
        if self.hearts() < cost:
            tell(what, f"A {what} costs {cost} 💖 hearts. You have {self.hearts()}.")
            return
        self.save["hearts"] = self.hearts() - cost
        write_save(self.save)
        soon = time.monotonic() + random.uniform(15, 45)
        if beacon:
            self.next_kaiju = min(self.next_kaiju, soon)
            tell("Kaiju Beacon 📡", f"Something HUGE is coming. When it stomps through the city at the bottom of your screen, click it {KAIJU_HITS} times!")
        else:
            self.next_sighting = min(self.next_sighting, soon)
            tell("Cryptid Lure 🔦", "Watch the bottom of your screen. When a shadow with glowing eyes sneaks by, click it before it gets away!")

    def sighting_step(self, now):
        for s in list(self.sightings):
            s.step(now)
        if self.sightings or not self.pets:
            return
        world = self.world()
        if world and now >= self.next_legend:
            self.next_legend = now + random.uniform(3, 7) * 60
            left = [k for k, w in LEGEND_WORLD.items() if w == world["name"] and not self.is_unlocked(k)]
            if left:
                self.sightings.append(Sighting(self, random.choice(left)))
                self.sound.play("boing")
                return
        if now >= self.next_kaiju:
            self.next_kaiju = now + random.uniform(45, 90) * 60
            left = [k for k in G["kaiju"] if not self.is_unlocked(k)]
            if left:
                self.sightings.append(Sighting(self, random.choice(left)))
                self.sound.play("thud")
                return
        if now >= self.next_sighting:
            wait = random.uniform(8, 20) * 60
            self.next_sighting = now + (wait / 2 if is_night() else wait)
            left = [k for k in G["cryptids"] if not self.is_unlocked(k)]
            if left:
                self.sightings.append(Sighting(self, random.choice(left)))
                self.sound.play("whoosh")

    # ---- the town
    def add_pet(self, kind=None, name=None, x=None, greet=True):
        if len(self.pets) >= MAX_PETS:
            if self.pets:
                self.pets[0].say("that's enough friends for now!", 2.5)
            return None
        if not kind and self.world() and random.random() < 0.5:
            kind = random.choice([k for k, wn in WORLD_OF.items() if wn == self.world()["name"]])
        kind = kind or random.choice([k for k in KINDS if self.is_unlocked(k)])
        name = name or random.choice(DATA["names"])
        pet = Pet(self, kind, name, x)
        self.pets.append(pet)
        if greet:
            pet.say(f"hi! i'm {name}", 2.5)
        return pet

    def remove(self, pet):
        if pet in self.pets:
            self.pets.remove(pet)
        pet.close()
        pet.deleteLater()
        self.save_town()
        if not self.pets:
            self.quit_all()

    def town_snapshot(self):
        return [{"kind": p.kind, "color": p.palette_i, "name": p.name, "hat": p.hat,
                 "hunger": round(p.hunger), "energy": round(p.energy)} for p in self.pets]

    def save_town(self):
        town = self.town_snapshot()
        if town != self.save.get("town"):
            self.save["town"], self.save["town_saved_at"] = town, time.time()
            write_save(self.save)

    def restore_town(self):
        town = self.save.get("town") or []
        away = max(0.0, (time.time() - float(self.save.get("town_saved_at", time.time()))) / 3600)
        back = 0
        for t in town[:MAX_PETS]:
            kind = t.get("kind")
            if kind not in KINDS or not (self.is_unlocked(kind) or kind in WORLD_OF):
                continue
            pet = self.add_pet(kind, str(t.get("name") or kind)[:16], greet=False)
            if not pet:
                break
            pet.palette_i = int(t.get("color", 0)) % len(kind_colors(kind))
            pet.hat = t.get("hat")
            pet.hunger = min(100.0, float(t.get("hunger", 10)) + away * 8)
            pet.energy = float(t.get("energy", 100))
            pet.say(random.choice(["i'm back!", "missed you!", "*stretches* hi again!", "good to see you!"]), 3)
            back += 1
        return back

    def quit_all(self):
        self.save_town()
        self.qt.quit()

    # ---- pets together
    def head_pos(self, pet):
        return pet.wx + W / 2, pet.wy + H - ART_H * SCALE + 6

    def ball_near(self, pet):
        for play in self.plays:
            if play["type"] == "ball" and "ball" in play:
                bx, by = play["ball"]
                if pet.wx - 10 < bx < pet.wx + W + 10 and pet.wy - 10 < by < pet.wy + H + 10:
                    return play["ball"]
        return None

    def end_play(self, play, now, happy=True):
        for pet in play["pets"]:
            pet.playing, pet.last_play = False, now
            if happy and pet.state not in ("held", "fall", "sleep"):
                pet.set_state("idle", random.uniform(1.5, 3))
                pet.set_face("happy", 1.5)
                pet.burst("heart", 2)
        if play in self.plays:
            self.plays.remove(play)

    def play_step(self, now):
        dt = 1 / FPS
        free = [p for p in self.pets if not p.playing and p.state == "idle" and now - p.last_play > 40]
        for i, a in enumerate(free):
            for b in free[i + 1:]:
                d = abs(a.wx - b.wx)
                if 60 < d < 190 and random.random() < dt * 0.04:
                    a.playing = b.playing = True
                    self.plays.append({"type": "ball", "pets": [a, b], "from": a, "to": b, "t0": now, "throws": 0, "n": random.randint(4, 7)})
                    a.say(random.choice(["catch!", f"heads up, {b.name}!", "wanna play?"]), 2)
                    break
                if d < 320 and random.random() < dt * 0.015:
                    a.playing = b.playing = True
                    self.plays.append({"type": "chase", "pets": [a, b], "runner": a, "chaser": b, "until": now + 7, "swapped": False})
                    a.say(random.choice(["can't catch me!", "tag, you're it!"]), 2)
                    b.say("hey! get back here!", 2)
                    break
        for sleeper in [p for p in self.pets if p.state == "sleep"]:
            for p in self.pets:
                if (p is not sleeper and not p.playing and not p.nap_buddy and p.state == "idle" and p.energy < 60
                        and abs(p.wx - sleeper.wx) < 600 and random.random() < dt * 0.15):
                    p.nap_buddy = True
                    p.target_x = min(max(sleeper.wx + random.choice([-1, 1]) * 70, p.left), p.right - W)
                    p.set_state("walk", 10)
                    p.say("*yawn* me too...", 2)
        for p in self.pets:
            if p.nap_buddy and p.state == "idle":
                p.nap_buddy = False
                p.set_state("sleep", 20)
                p.say("*snuggles*", 2)
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
            else:
                runner, chaser = play["runner"], play["chaser"]
                left, right = runner.left, runner.right - W
                away = 1 if runner.wx >= chaser.wx else -1
                if (away > 0 and runner.wx >= right - 2) or (away < 0 and runner.wx <= left + 2):
                    away = -away
                runner.wx = min(max(runner.wx + 2.2 * away * KINDS[runner.kind].get("speed", 1.0) ** 0.5, left), right)
                toward = 1 if runner.wx > chaser.wx else -1
                chaser.wx += 4.4 * toward * KINDS[chaser.kind].get("speed", 1.0) ** 0.5
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
        calm = ("idle", "walk")
        idle = [p for p in self.pets if not p.playing]
        for i, a in enumerate(idle):
            for b in idle[i + 1:]:
                if a.state not in calm or b.state not in calm or abs(a.wx - b.wx) > 90:
                    continue
                if now - a.greeted.get(b.name, -999) < 60:
                    continue
                a.greeted[b.name] = b.greeted[a.name] = now
                a.say(random.choice([f"hi {b.name}!", f"oh, {b.name}!", f"hey {b.name} :)"]), 2.5)
                b.say(random.choice([f"hi {a.name}!", "oh hi!", f"{a.name}!! :D"]), 2.5)
                a.set_face("happy", 1.5)
                b.set_face("happy", 1.5)

    # ---- the loop
    def safely(self, fn, *args, what=""):
        try:
            return fn(*args)
        except Exception:  # noqa: BLE001  (one problem must never stop the game)
            import traceback
            key = (what, traceback.format_exc().splitlines()[-1])
            if time.monotonic() - self._logged.get(key, -999) > 60:
                self._logged[key] = time.monotonic()
                log(f"error in {what}:\n{traceback.format_exc()}")
            return None

    def tick(self):
        now = time.monotonic()
        for pet in list(self.pets):
            self.safely(pet.step, now, what=pet.kind)
        self.safely(self.socialize, now, what="saying hi")
        self.safely(self.play_step, now, what="games")
        self.safely(self.sighting_step, now, what="sightings")
        if now - self.last_town_save > 15:
            self.safely(self.save_town, what="saving")
            self.last_town_save = now

    # ---- right-click menu
    def menu_for(self, pet):
        m = QMenu()

        def act(menu, label, fn=None, checked=None, enabled=True):
            a = QAction(label, menu)
            if checked is not None:
                a.setCheckable(True)
                a.setChecked(checked)
            a.setEnabled(enabled)
            if fn:
                a.triggered.connect(fn)
            menu.addAction(a)
            return a
        act(m, "Feed a cookie", pet.feed)
        act(m, "Pet", pet.pet)
        act(m, "Wake up" if pet.state == "sleep" else "Nap time", pet.toggle_sleep)
        act(m, "Follow my mouse", lambda c: setattr(pet, "follow", c), checked=pet.follow)
        act(m, "Say something", lambda: pet.say(random.choice(pet.lines()), 3))

        kinds = m.addMenu("Change kind")
        animals = G["animals"]
        size = -(-len(animals) // 6)
        groups = ([("Critters", G["critters"])] + [(f"Animals: {c[0]} – {c[-1]}", c) for c in (animals[i:i + size] for i in range(0, len(animals), size))]
                  + [(t, ks) for t, ks in G["tabs"]]
                  + [("Night Shift 🌙", G["nightShift"]), ("Rare 🥚", G["rare"]), ("Cryptids 👣", G["cryptids"]),
                     ("Kaiju 🦖", G["kaiju"]), ("Legends ✨", G["legends"]), ("Gifts 🎁", G["gifts"])])
        for title, members in groups:
            sub = kinds.addMenu(title)
            tab_world = next((w for w in WORLDS if w["tab"] == title), None)
            if tab_world and tab_world["name"] not in self.save.get("worlds", []):
                act(sub, f"🔒 Unlock {tab_world['name']} {tab_world['icon']} ({tab_world['cost']} 💖)…",
                    lambda _=False, n=tab_world["name"]: self.unlock_world(n))
                sub.addSeparator()
            for k in members:
                if self.is_unlocked(k):
                    act(sub, k, lambda _=False, k=k: self.change_kind(pet, k), checked=(k == pet.kind))
                else:
                    act(sub, f"🔒 {k}" if k in WORLD_OF else (f"🔒 ???  (visit {LEGEND_WORLD[k]})" if k in LEGEND_WORLD else "🔒 ???"), enabled=False)
        colors = m.addMenu("Change color")
        for i, c in enumerate(kind_colors(pet.kind)):
            act(colors, c["name"], lambda _=False, i=i: self.change_color(pet, i), checked=(i == pet.palette_i))
        act(m, "Rename…", lambda: self.rename(pet))
        m.addSeparator()
        act(m, "Add a friend", lambda: self.add_pet(x=pet.wx))
        act(m, "🎩 Hats & outfits…", lambda: self.windows.append(HatShop(self, pet)))
        act(m, f"🥚 Hatch a Mystery Egg ({EGG_COST} 💖)…", self.open_egg)
        act(m, f"🔦 Set out a Cryptid Lure ({LURE_COST} 💖)…", lambda: self.set_lure(False))
        act(m, f"📡 Switch on a Kaiju Beacon ({BEACON_COST} 💖)…", lambda: self.set_lure(True))
        act(m, "📖 Collection (peek at locked Blips)…", lambda: open_collection(self))
        worlds = m.addMenu("🌍 Worlds")
        here = self.world()
        act(worlds, "🏠 Home", lambda: self.visit_world(None), checked=here is None)
        for w in WORLDS:
            if w["name"] in self.save.get("worlds", []):
                act(worlds, f"{w['icon']} Visit {w['name']}", lambda _=False, n=w["name"]: self.visit_world(n),
                    checked=bool(here and here["name"] == w["name"]))
            else:
                act(worlds, f"🔒 {w['icon']} Unlock {w['name']} ({w['cost']} 💖)…", lambda _=False, n=w["name"]: self.unlock_world(n))
        act(m, f"💖 {self.hearts()} hearts", enabled=False)
        act(m, "Show name tags", self.toggle_tags, checked=self.name_tags)
        act(m, "Sound effects", self.toggle_sound, checked=self.sound_on)
        act(m, "Weather effects", self.toggle_weather, checked=self.weather_on)
        act(m, "🌙 Play Night Shift…", self.open_night_shift)
        upd = m.addMenu("🔄 Updates")
        act(upd, "Check for updates now", lambda: self.updater.check(quiet=False))
        act(upd, "Update automatically (asks first)", self.updater.set_auto, checked=self.updater.auto)
        act(upd, f"You have {version_label()}", enabled=False)
        talk = m.addMenu("💬 Suggestions & help")
        act(talk, "💡 Suggest an idea…", lambda: webbrowser.open("https://github.com/Johnblip189/blipville/issues/new?template=idea.yml"))
        act(talk, "🆘 Get help / report a problem…", lambda: webbrowser.open("https://github.com/Johnblip189/blipville/issues/new?template=help.yml"))
        act(talk, "📋 Copy error log (for bug reports)", lambda: self.copy_log(pet))
        m.addSeparator()
        act(m, f"Goodbye, {pet.name}", lambda: self.remove(pet))
        act(m, "Goodbye everyone (quit)", self.quit_all)
        return m

    def change_kind(self, pet, kind):
        pet.kind, pet.palette_i = kind, KINDS[kind].get("default", 0)
        pet.say(f"i'm a {kind} now!", 2)
        pet.set_face("happy", 1.2)
        pet.burst("heart", 3)

    def change_color(self, pet, i):
        pet.palette_i = i
        pet.say(f"{kind_colors(pet.kind)[i]['name'].lower()}!", 1.5)
        pet.burst("heart", 2)

    def rename(self, pet):
        new, ok = QInputDialog.getText(None, "Rename", f"New name for {pet.name}:", text=pet.name)
        if ok and new.strip():
            pet.name = new.strip()[:16]
            pet.setWindowTitle(pet.name)
            pet.say(f"call me {pet.name}!", 2)
            pet.set_face("happy", 1.2)

    def toggle_tags(self, on):
        self.name_tags = self.save["name_tags"] = bool(on)
        write_save(self.save)

    def toggle_sound(self, on):
        self.sound_on = self.save["sound"] = bool(on)
        write_save(self.save)
        self.sound.play("boop")

    def toggle_weather(self, on):
        self.weather_on = self.save["weather"] = bool(on)
        write_save(self.save)

    def copy_log(self, pet):
        try:
            with open(log_path(), encoding="utf-8", errors="replace") as f:
                text = "".join(f.readlines()[-80:])
        except OSError:
            text = ""
        if "error" not in text:
            pet.say("no errors logged! 🎉", 3)
            return
        QGuiApplication.clipboard().setText(text)
        pet.say("copied the error log! paste it in a bug report 📋", 4)

    def run(self):
        sys.excepthook = lambda *exc: log("error:\n" + "".join(__import__("traceback").format_exception(*exc)))
        return self.qt.exec()


# ----------------------------------------------------------------------------- updates (same idea as the classic app)
RELEASES_API = "https://api.github.com/repos/Johnblip189/blipville/releases?per_page=20"
RELEASES_FEED = "https://github.com/Johnblip189/blipville/releases.atom"
RELEASES_PAGE = "https://github.com/Johnblip189/blipville/releases"
DOWNLOAD_URL = "https://github.com/Johnblip189/blipville/releases/download/{tag}/" + EXE_NAME


def _iso(t):
    import calendar
    try:
        return float(calendar.timegm(time.strptime(t[:19], "%Y-%m-%dT%H:%M:%S")))
    except (TypeError, ValueError):
        return 0.0


def version_label():
    if APP_VERSION == "dev":
        return "the source version"
    when = _iso(APP_BUILT)
    if not when:
        return APP_VERSION
    t = time.localtime(when)
    return f"{APP_VERSION} (built {time.strftime('%b', t)} {t.tm_mday}, {(t.tm_hour % 12) or 12}:{t.tm_min:02d} {'AM' if t.tm_hour < 12 else 'PM'})"


def newest_release(releases):
    for r in releases:
        if r.get("draft"):
            continue
        for a in r.get("assets", []):
            if a.get("name", "").lower() == EXE_NAME.lower() and a.get("browser_download_url"):
                return r.get("tag_name", ""), a
    return None


def is_newer(tag, asset, my_version=None, my_built=None, my_size=None):
    my_version = APP_VERSION if my_version is None else my_version
    my_built = APP_BUILT if my_built is None else my_built
    if my_size is None and getattr(sys, "frozen", False):
        try:
            my_size = os.path.getsize(sys.executable)
        except OSError:
            my_size = None
    if my_version == "dev":
        return False
    if tag != my_version:
        return True
    uploaded, built = _iso(asset.get("updated_at", "")), _iso(my_built)
    if not (uploaded and built and uploaded > built):
        return False
    if my_size and asset.get("size"):
        return asset["size"] != my_size
    return uploaded - built > 15 * 60


def _why(e):
    text = str(getattr(e, "reason", "") or e) or type(e).__name__
    return (text[:140] + "…") if len(text) > 140 else text


def _curl(args, timeout):
    import shutil
    exe = shutil.which("curl.exe") or shutil.which("curl")
    if not exe:
        raise RuntimeError("curl isn't available")
    r = subprocess.run([exe, "-sSL", "--fail", "-A", "Blipville-updater", "--max-time", str(timeout)] + args,
                       capture_output=True, timeout=timeout + 10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip() or f"curl error {r.returncode}")
    return r.stdout


def http_get(url, timeout=15):
    import urllib.request
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Blipville-updater"}), timeout=timeout) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001
        first = _why(e)
    try:
        return _curl([url], timeout)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"{first} / backup: {_why(e)}") from None


def http_head(url, timeout=15):
    import urllib.request
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Blipville-updater"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {k.lower(): v for k, v in r.headers.items()}
    except Exception as e:  # noqa: BLE001
        first = _why(e)
    try:
        raw = _curl(["-I", url], timeout).decode("latin-1")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"{first} / backup: {_why(e)}") from None
    block = [b for b in raw.replace("\r", "").split("\n\n") if b.strip()][-1]
    return {ln.split(":", 1)[0].strip().lower(): ln.split(":", 1)[1].strip() for ln in block.split("\n") if ":" in ln}


def http_download(url, path, timeout=300):
    import urllib.request
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Blipville-updater"}), timeout=timeout) as r, open(path, "wb") as f:
            while True:
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
        return
    except Exception as e:  # noqa: BLE001
        first = _why(e)
    try:
        _curl(["-o", path, url], timeout)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"{first} / backup: {_why(e)}") from None


def find_update_backup():
    """Doesn't count against GitHub's hourly API limit: newest tags from the public feed, then the file itself."""
    import re
    from email.utils import parsedate_to_datetime
    tags = []
    try:
        tags = re.findall(r"/releases/tag/([^\"<>\s]+)", http_get(RELEASES_FEED).decode("utf-8", "replace"))
    except Exception:  # noqa: BLE001
        pass
    for tag in list(dict.fromkeys(tags))[:6] + [APP_VERSION]:
        try:
            head = http_head(DOWNLOAD_URL.format(tag=tag))
        except Exception:  # noqa: BLE001  (that release has no Recode download)
            continue
        modified = head.get("last-modified")
        when = parsedate_to_datetime(modified).strftime("%Y-%m-%dT%H:%M:%SZ") if modified else ""
        return tag, {"name": EXE_NAME, "browser_download_url": DOWNLOAD_URL.format(tag=tag),
                     "size": int(head.get("content-length") or 0), "updated_at": when}
    raise RuntimeError("no Recode download found")


class Updater:
    def __init__(self, app):
        import queue
        self.app, self.busy, self.offered = app, False, None
        self.auto = bool(app.save.get("auto_update", True))
        self.inbox = queue.Queue()
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll)

    def poll(self):
        while not self.inbox.empty():
            self.inbox.get_nowait()()

    def start(self):
        self.poll_timer.start(250)
        if self.auto:
            QTimer.singleShot(15000, lambda: self.check(quiet=True))
        self.repeat = QTimer()
        self.repeat.timeout.connect(lambda: self.auto and self.check(quiet=True))
        self.repeat.start(6 * 3600 * 1000)

    def set_auto(self, on):
        self.auto = bool(on)
        self.app.save["auto_update"] = self.auto
        write_save(self.app.save)

    def check(self, quiet=False):
        if self.busy:
            return
        self.busy = True
        import threading

        def work():
            try:
                result = newest_release(json.loads(http_get(RELEASES_API).decode("utf-8")))
                if result is None:
                    result = find_update_backup()
            except Exception as e1:  # noqa: BLE001
                try:
                    result = find_update_backup()
                except Exception as e2:  # noqa: BLE001
                    result = ("error", f"{_why(e1)}\n{_why(e2)}")
            self.inbox.put(lambda: self.found(result, quiet))
        threading.Thread(target=work, daemon=True).start()

    def found(self, result, quiet):
        self.busy = False
        pet = self.app.pets[0] if self.app.pets else None
        if result is None or (isinstance(result, tuple) and result[0] == "error"):
            if not quiet:
                tell("Blipville updates", "Couldn't reach GitHub to check for updates. Check your internet and try again in a few minutes!"
                     "\n\nDetails:\n" + (result[1] if result else "no download found"))
            return
        tag, asset = result
        if not is_newer(tag, asset):
            if not quiet:
                tell("Blipville updates", f"You're on the newest {APP_NAME}! 🎉\n\nYou have {version_label()}."
                     if APP_VERSION != "dev" else "You're running from source, so it can't update itself.")
            return
        if quiet and self.offered == asset.get("updated_at"):
            return
        self.offered = asset.get("updated_at")
        if pet:
            pet.say("ooh, an update is ready! ✨", 5)
        text = f"A fresh build of {APP_NAME} {tag} is ready!" if tag == APP_VERSION else f"{APP_NAME} {tag} is out! (You have {APP_VERSION}.)"
        if not getattr(sys, "frozen", False):
            if ask("Update", text + "\n\nOpen the download page?"):
                webbrowser.open(RELEASES_PAGE)
            return
        if ask("Update", text + "\n\nUpdate now? It closes for a few seconds and comes right back. Your pets, hearts and unlocks are kept."):
            self.download(asset)

    def download(self, asset):
        import threading
        exe = os.path.abspath(sys.executable)
        new = exe + ".new"
        if self.app.pets:
            self.app.pets[0].say("downloading the update… ⏳", 30)

        def work():
            ok = False
            try:
                http_download(asset["browser_download_url"], new)
                size = os.path.getsize(new)
                with open(new, "rb") as f:
                    ok = f.read(2) == b"MZ" and size > 1_000_000 and (not asset.get("size") or size == asset["size"])
            except Exception as e:  # noqa: BLE001
                log(f"update download failed: {_why(e)}")
            self.inbox.put(lambda: self.install(exe, new, ok))
        threading.Thread(target=work, daemon=True).start()

    def install(self, exe, new, ok):
        if not ok:
            try:
                os.remove(new)
            except OSError:
                pass
            tell("Update", "The download didn't finish. Try again later, or get it from the releases page.")
            return
        bat = os.path.join(os.path.dirname(exe), "blipville-recode-update.bat")
        with open(bat, "w", encoding="utf-8") as f:
            f.write("@echo off\r\nchcp 65001 >nul\r\nset tries=0\r\n:wait\r\n"
                    f'move /y "{new}" "{exe}" >nul 2>&1 && goto done\r\n'
                    "set /a tries+=1\r\nif %tries% geq 60 goto done\r\nping -n 2 127.0.0.1 >nul\r\ngoto wait\r\n"
                    ":done\r\nping -n 2 127.0.0.1 >nul\r\n"
                    f'start "" "{exe}"\r\ndel "%~f0"\r\n')
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("_MEI", "_PYI"))}
        env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
        subprocess.Popen(["cmd", "/c", bat], creationflags=flags, close_fds=True, env=env, cwd=os.path.dirname(exe))
        self.app.quit_all()


def main():
    # A hard crash (for example Qt failing to start) can't be caught normally; faulthandler writes where it happened.
    try:
        import faulthandler
        os.makedirs(save_dir(), exist_ok=True)
        main.crash_file = open(os.path.join(save_dir(), "blipville-recode-crash.txt"), "a", encoding="utf-8")
        main.crash_file.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} {APP_VERSION} {APP_BUILT}\n")
        main.crash_file.flush()
        faulthandler.enable(main.crash_file)
    except Exception:  # noqa: BLE001
        pass
    log(f"starting {APP_NAME} (frozen={getattr(sys, 'frozen', False)})")
    return App().run()


if __name__ == "__main__":
    sys.exit(main())
