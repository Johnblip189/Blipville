"""Copies every Blip's art, colors, hats and lines from blip.pyw into recode/blipdata.json, so Blipville Recode
(recode/blipville_recode.py) always matches. Run it after changing any art:

    python tools/export_recode_data.py
"""
import importlib.util
import json
import os
from importlib.machinery import SourceFileLoader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_loader("blip", SourceFileLoader("blip", os.path.join(ROOT, "blip.pyw")))
bl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bl)

kinds = {}
for k in bl.KINDS:
    if k in bl.CUSTOM_KINDS:
        continue
    v = bl.VARIANTS[k]
    kinds[k] = {"body": v["body"], "alt": v.get("alt"), "eyes": v["eyes"], "mouth": v.get("mouth", True), "feet": v["feet"],
                "dx": v.get("dx", 0), "move": v["move"], "speed": v.get("speed", 1.0), "shifty": bool(v.get("shifty")),
                "extra": v.get("extra", {}), "lines": v["lines"], "colors": bl.kind_colors(k), "default": bl.default_color(k)}
data = {
    "kinds": kinds,
    "groups": {"critters": bl.CRITTERS, "animals": bl.ANIMAL_KINDS, "tabs": bl.TAB_GROUPS, "nightShift": bl.NIGHT_SHIFT,
               "rare": bl.RARE_KINDS, "cryptids": bl.CRYPTID_KINDS, "kaiju": bl.KAIJU_KINDS, "legends": bl.LEGEND_KINDS,
               "gifts": bl.GIFT_KINDS},
    "unlocks": bl.UNLOCKS, "worldOf": bl.WORLD_OF, "legendWorld": bl.LEGEND_WORLD,
    "worlds": [{k: w[k] for k in ("name", "icon", "tab", "cost", "fx")} for w in bl.WORLDS],
    "hats": bl.HATS, "robots": list(bl.ROBOTS),
    "lines": {"idle": bl.LINES_IDLE, "pet": bl.LINES_PET, "held": bl.LINES_HELD, "land": bl.LINES_LAND, "eat": bl.LINES_EAT,
              "wake": bl.LINES_WAKE, "hungry": bl.LINES_HUNGRY, "night": bl.NIGHT_LINES, "season": bl.SEASON_LINES},
    "names": bl.NAMES, "eggCost": bl.EGG_COST,
    "shapes": {"heart": bl.HEART, "zed": bl.ZED, "cookie": bl.COOKIE, "ball": bl.BALL, "bat": bl.BAT, "batFlap": bl.BAT_FLAP,
               "egg": bl.EGG},
    "scenes": bl.SCENES, "sceneProps": bl.SCENE_PROPS, "scene": [bl.SCENE_W, bl.SCENE_H, bl.SCENE_PX],
    "kaijuHits": bl.KAIJU_HITS, "lureCost": bl.LURE_COST, "beaconCost": bl.BEACON_COST,
    "gift": {"now": bl.GIFT_NOW, "until": bl.GIFT_UNTIL, "untilText": bl.GIFT_UNTIL_TEXT},
    "notice": {"id": bl.NOTICE_ID, "text": bl.NOTICE_TEXT},
}
out = os.path.join(ROOT, "recode", "blipdata.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
print(f"wrote {out}: {len(kinds)} kinds, {os.path.getsize(out) // 1024} KB")
