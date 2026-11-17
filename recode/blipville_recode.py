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
from PySide6.QtWidgets import QApplication, QInputDialog, QMenu, QMessageBox, QWidget

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
HEART, ZED, COOKIE = DATA["shapes"]["heart"], DATA["shapes"]["zed"], DATA["shapes"]["cookie"]


def kind_colors(kind):
    return KINDS[kind]["colors"]


def is_night():
    h = time.localtime().tm_hour
    return h >= 20 or h < 6


def season():
    t = time.localtime()
    if t.tm_mon == 10 and t.tm_mday >= 15:
        return "spooky"
    return {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
            6: "summer", 7: "summer", 8: "summer"}.get(t.tm_mon, "autumn")


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
        self.last_pet_reward = 0.0
        self.last_hungry = 0.0
        self.press = None
        self.drag_hist = []
        self.follow = False
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
            mx = QCursor.pos().x()
            self.target_x = min(max(mx - W / 2, self.left), self.right - W)
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
                    self.set_face("munch", 1.8)
                else:
                    self.set_state("idle", random.uniform(1, 3))
            else:
                self.wx += speed * self.facing
            self.place()
        elif self.state == "idle" and now > self.state_until and not self.follow:
            self.decide(now)

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
        v = self.v()
        cols = kind_colors(self.kind)
        pal = {**cols[self.palette_i % len(cols)], **(v.get("extra") or {})}
        g = [[None] * ART_W for _ in range(ART_H)]
        body = pal.get("art") or v["body"]
        if v.get("alt") and self.state in ("walk", "fall", "held") and int(now * 10) % 2:
            body = v["alt"]
        lying = self.state == "sleep" or now < self.squash_until
        shift = 1 if lying else 0
        for y, row in enumerate(body):
            for x, ch in enumerate(row):
                if ch != "." and y + shift < ART_H:
                    g[y + shift][x] = pal.get(ch, pal["o"])
        dxo = v.get("dx", 0)
        if not lying and v["feet"]:
            fs = v["feet"]
            if self.state in ("fall", "held") or self.lift(now) > 3:
                feet = fs["air"]
            elif self.state == "walk":
                feet = fs["walk1"] if int(now * 6) % 2 else fs["walk2"]
            else:
                feet = fs["stand"]
            for x, ch in enumerate(feet):
                if ch != "." and 0 <= x + dxo < ART_W:
                    g[12][x + dxo] = pal.get("f", pal["o"])
        face_dy = v["eyes"] - 5

        def px(x, y, color):
            y += shift + face_dy
            x += dxo
            if 0 <= x < ART_W and 0 <= y < ART_H:
                g[y][x] = color
        face = self.face if now < self.face_until else "normal"
        if self.state == "sleep":
            face = "sleep"
        e, white = pal["e"], "#ffffff"
        r_, g_, b_ = (int(e[i:i + 2], 16) for i in (1, 3, 5))
        if 0.299 * r_ + 0.587 * g_ + 0.114 * b_ > 150:
            white = pal["o"]
        if self.kind in ROBOTS and is_night():
            white = e
        if face == "sleep" or (now < self.blink_until and face == "normal"):
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
        if self.facing < 0 and False:            # art faces the viewer; no flipping needed
            g = [list(reversed(r)) for r in g]
        return g, shift

    def hat_cells(self, shift):
        hat = HATS.get(self.hat)
        if not hat:
            return []
        v, body = self.v(), self.v()["body"]
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

    # ---- frame
    def step(self, now):
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
        key = (str(art), self._frame[2], self.hat, self.bubble and self.bubble[0], self.app.name_tags,
               self.name, len(self.particles), self.cookie is not None)
        if key != self._key or self.particles or self.cookie:
            self._key = key
            self.update()

    def paintEvent(self, _e):
        if not hasattr(self, "_frame"):
            return
        art, shift, lift, now = self._frame
        p = QPainter(self)
        ox = (W - ART_W * SCALE) // 2
        oy = H - ART_H * SCALE - lift
        for y, row in enumerate(art):
            x = 0
            while x < ART_W:
                c = row[x]
                if c is None:
                    x += 1
                    continue
                x2 = x
                while x2 + 1 < ART_W and row[x2 + 1] == c:
                    x2 += 1
                p.fillRect(ox + x * SCALE, oy + y * SCALE, (x2 - x + 1) * SCALE, SCALE, QColor(c))
                x = x2 + 1
        hat_top = 0
        for r, c, col in self.hat_cells(shift):
            p.fillRect(ox + c * SCALE, oy + r * SCALE, SCALE, SCALE, QColor(col))
            hat_top = min(hat_top, r * SCALE)
        ck = self.cookie
        if ck:
            cx = (W / 2 + 10 * self.facing) if self.state == "eat" else ck["x"] - self.wx
            bites = 0 if self.state != "eat" else int((1.8 - max(0, self.state_until - now)) / 0.45)
            for y, row in enumerate(COOKIE):
                for x, ch in enumerate(row):
                    if ch == "." or (self.state == "eat" and x >= 6 - bites):
                        continue
                    p.fillRect(int(cx - 9 + x * 3), int(ck["y"] + y * 3), 3, 3, QColor("#c98a4b" if ch == "c" else "#5a3418"))
        small = QFont("Segoe UI", 8, QFont.Bold)
        for q in self.particles:
            age = now - q["born"]
            if q["kind"] == "heart":
                for y, row in enumerate(HEART):
                    for x, ch in enumerate(row):
                        if ch == "x":
                            p.fillRect(int(q["x"] + x * 3), int(q["y"] + y * 3), 3, 3, QColor("#ff4f7b"))
            elif q["kind"] == "z":
                s = 2 + int(age)
                for y, row in enumerate(ZED):
                    for x, ch in enumerate(row):
                        if ch == "x":
                            p.fillRect(int(q["x"] + x * s), int(q["y"] + y * s), s, s, QColor("#bcd2ff"))
            elif q["kind"] == "crumb":
                p.fillRect(int(q["x"]), int(q["y"]), 3, 3, QColor("#c98a4b"))
            elif q["kind"] == "plus":
                p.setFont(small)
                r = QFontMetrics(small).boundingRect(q["text"]).adjusted(-4, -1, 4, 1)
                r.moveCenter(QPoint(int(q["x"]), int(q["y"])))
                p.fillRect(r, QColor("#e8457a"))
                p.setPen(QColor("#ffffff"))
                p.drawText(r, Qt.AlignCenter, q["text"])
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
            path = path.united(tail)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(QPen(QColor("#222222"), 2))
            p.setBrush(QColor("#ffffff"))
            p.drawPath(path)
            p.setPen(QColor("#222222"))
            p.drawText(box, Qt.TextWordWrap | Qt.AlignCenter, self.bubble[0])
        p.end()

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
        else:
            self.pet()
        self.press = None

    def contextMenuEvent(self, e):
        if self.state == "walk":
            self.set_state("idle", 3)
        self.app.menu_for(self).exec(e.globalPos())


# ----------------------------------------------------------------------------- the app
class App:
    def __init__(self):
        self.qt = QApplication.instance() or QApplication(sys.argv)
        self.qt.setQuitOnLastWindowClosed(False)
        self.qt.setApplicationName(APP_NAME)
        self.area = QGuiApplication.primaryScreen().availableGeometry()
        self.save = load_save()
        self.name_tags = bool(self.save.get("name_tags", True))
        self.pets = []
        self.last_town_save = time.monotonic()
        self.updater = Updater(self)
        log(f"started {APP_NAME} on {sys.platform}, Python {sys.version.split()[0]}")
        if not self.restore_town():
            self.add_pet("Blip", "Blip")
        QTimer.singleShot(1600, self.daily_treat)
        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.timer.start(int(1000 / FPS))
        self.updater.start()

    # ---- unlocks and hearts
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

    def daily_treat(self):
        today = time.strftime("%Y-%m-%d")
        if self.save.get("last_day") != today and self.pets:
            self.save["last_day"] = today
            self.add_hearts(10, self.pets[0])
            self.pets[0].say("daily treat! +10 💖", 4)

    # ---- the town
    def add_pet(self, kind=None, name=None, x=None, greet=True):
        if len(self.pets) >= MAX_PETS:
            if self.pets:
                self.pets[0].say("that's enough friends for now!", 2.5)
            return None
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

    def tick(self):
        now = time.monotonic()
        for pet in list(self.pets):
            try:
                pet.step(now)
            except Exception:  # noqa: BLE001  (one pet's problem must never stop the others)
                import traceback
                log(f"error in {pet.kind}:\n{traceback.format_exc()}")
        if now - self.last_town_save > 15:
            self.save_town()
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
            for k in members:
                if self.is_unlocked(k):
                    act(sub, k, lambda _=False, k=k: self.change_kind(pet, k), checked=(k == pet.kind))
                else:
                    secret = k not in WORLD_OF
                    act(sub, "🔒 ???" if secret else f"🔒 {k}", enabled=False)
        colors = m.addMenu("Change color")
        for i, c in enumerate(kind_colors(pet.kind)):
            act(colors, c["name"], lambda _=False, i=i: self.change_color(pet, i), checked=(i == pet.palette_i))
        act(m, "Rename…", lambda: self.rename(pet))
        hats = m.addMenu("🎩 Hat")
        act(hats, "No hat", lambda: setattr(pet, "hat", None), checked=pet.hat is None)
        for h in self.save.get("hats_owned", []):
            if h in HATS:
                act(hats, h, lambda _=False, h=h: setattr(pet, "hat", h), checked=pet.hat == h)
        m.addSeparator()
        act(m, "Add a friend", lambda: self.add_pet(x=pet.wx))
        act(m, f"💖 {self.hearts()} hearts", enabled=False)
        act(m, "Show name tags", self.toggle_tags, checked=self.name_tags)
        soon = m.addMenu("🚧 Coming to the Recode soon")
        for label in ("🥚 Mystery Eggs", "📖 Collection", "👣 Cryptids, 🦖 kaiju & ✨ legends", "🌍 Worlds & weather",
                      "🎩 Hat shop", "🌙 Night Shift", "🔊 Sounds"):
            act(soon, label, enabled=False)
        act(soon, "(open the classic Blipville for these for now)", enabled=False)
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
        self.name_tags = bool(on)
        self.save["name_tags"] = self.name_tags
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
                QMessageBox.information(None, "Blipville updates", "Couldn't reach GitHub to check for updates. Check your internet "
                                        "and try again in a few minutes!\n\nDetails:\n" + (result[1] if result else "no download found"))
            return
        tag, asset = result
        if not is_newer(tag, asset):
            if not quiet:
                QMessageBox.information(None, "Blipville updates", f"You're on the newest {APP_NAME}! 🎉\n\nYou have {version_label()}."
                                        if APP_VERSION != "dev" else "You're running from source, so it can't update itself.")
            return
        if quiet and self.offered == asset.get("updated_at"):
            return
        self.offered = asset.get("updated_at")
        if pet:
            pet.say("ooh, an update is ready! ✨", 5)
        text = f"A fresh build of {APP_NAME} {tag} is ready!" if tag == APP_VERSION else f"{APP_NAME} {tag} is out! (You have {APP_VERSION}.)"
        if not getattr(sys, "frozen", False):
            if QMessageBox.question(None, "Update", text + "\n\nOpen the download page?") == QMessageBox.Yes:
                webbrowser.open(RELEASES_PAGE)
            return
        if QMessageBox.question(None, "Update", text + "\n\nUpdate now? It closes for a few seconds and comes right back. "
                                "Your pets, hearts and unlocks are kept.") == QMessageBox.Yes:
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
            QMessageBox.information(None, "Update", "The download didn't finish. Try again later, or get it from the releases page.")
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


if __name__ == "__main__":
    sys.exit(App().run())
