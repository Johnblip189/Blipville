"""Writes the version and build time into blip.pyw before the .exe is built, so the app can tell
whether a newer release is out.

    python tools/stamp_version.py v0.4.0-rc1                      (the classic app, blip.pyw)
    python tools/stamp_version.py v0.5.0-recode recode/blipville_recode.py
"""
import datetime
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
version = sys.argv[1]
path = os.path.join(ROOT, sys.argv[2] if len(sys.argv) > 2 else "blip.pyw")
built = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open(path, encoding="utf-8") as f:
    src = f.read()
for old, new in (('APP_VERSION = "dev"', f'APP_VERSION = "{version}"'), ('APP_BUILT = ""', f'APP_BUILT = "{built}"')):
    if old not in src:
        sys.exit(f"couldn't find {old!r} in {path}")
    src = src.replace(old, new, 1)
with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(src)
print(f"stamped {version}, built {built}")
