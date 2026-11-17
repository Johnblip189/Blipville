"""Writes the version and build time into blip.pyw before the .exe is built, so the app can tell
whether a newer release is out.

    python tools/stamp_version.py v0.4.0-rc2                      (Blipville, the classic app)
    python tools/stamp_version.py v0.5.0-redux --edition redux    (Blipville Redux, from the same blip.pyw)
"""
import datetime
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[1:]
edition = None
if "--edition" in args:
    i = args.index("--edition")
    edition = args[i + 1]
    del args[i:i + 2]
version = args[0]
path = os.path.join(ROOT, args[1] if len(args) > 1 else "blip.pyw")
built = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open(path, encoding="utf-8") as f:
    src = f.read()
swaps = [('APP_VERSION = "dev"', f'APP_VERSION = "{version}"'), ('APP_BUILT = ""', f'APP_BUILT = "{built}"')]
if edition:
    swaps.append(('EDITION = "classic"', f'EDITION = "{edition}"'))
for old, new in swaps:
    if old not in src:
        sys.exit(f"couldn't find {old!r} in {path}")
    src = src.replace(old, new, 1)
with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(src)
print(f"stamped {version}, built {built}" + (f", edition {edition}" if edition else ""))
