"""🎟️ Make merch codes for Blipville.

    python3 tools/merch_codes.py REX-GRN 200

prints 200 new codes like REX-GRN-7K3M-9QPA into merch/private/ (kept out of git: print them on labels, don't share the
file) and adds their fingerprints to merch-codes.json. Commit and push merch-codes.json to main: the game reads it
online, so the new codes work right away, with no update. The codes themselves are never in the repo or the game.
"""
import csv
import datetime
import json
import os
import secrets
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"          # no 0/O or 1/I, so labels are easy to read


def load_game():
    import importlib.util
    from importlib.machinery import SourceFileLoader
    spec = importlib.util.spec_from_loader("blip", SourceFileLoader("blip", os.path.join(ROOT, "blip.pyw")))
    m = importlib.util.module_from_spec(spec)
    os.environ.setdefault("APPDATA", os.path.join(ROOT, "merch", "private", ".appdata"))
    spec.loader.exec_module(m)
    return m


def main():
    if len(sys.argv) != 3 or not sys.argv[2].isdigit():
        sys.exit(__doc__)
    prefix, count = sys.argv[1].upper(), int(sys.argv[2])
    bl = load_game()
    if prefix not in bl.MERCH:
        sys.exit(f"Unknown prefix {prefix}. Known: {', '.join(bl.MERCH)}")
    codes = set()
    while len(codes) < count:
        body = "".join(secrets.choice(ALPHABET) for _ in range(8))
        codes.add(f"{prefix}-{body[:4]}-{body[4:]}")
    codes = sorted(codes)
    hashes = [bl.merch_fingerprint("".join(ch for ch in c if ch.isalnum())) for c in codes]
    path = os.path.join(ROOT, "merch-codes.json")
    data = json.load(open(path)) if os.path.exists(path) else {"hashes": []}
    data["hashes"] = sorted(set(data["hashes"]) | set(hashes))
    with open(path, "w") as f:
        json.dump(data, f, indent=0)
    out_dir = os.path.join(ROOT, "merch", "private")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"codes-{prefix}-{datetime.date.today()}-{secrets.token_hex(2)}.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "item"])
        for c in codes:
            w.writerow([c, f"{bl.MERCH[prefix].get('for') or bl.MERCH[prefix]['kind']}: {bl.MERCH[prefix]['name']}"])
    print(f"{count} codes written to {out}\n{len(data['hashes'])} fingerprints in merch-codes.json (commit + push it to main)")


if __name__ == "__main__":
    main()
