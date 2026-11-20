"""J-4227 (D-0831, D-0498 audition clause, F-4435): regression guard for the rule that a CARRIED cat sound
never names her while he cannot see her. J-4363 rewrote the 14 carried lines in core/cat_content.SOUNDS that
did; this test keeps it that way.

Checks:
  1. every SOUNDS key has a "carried" pool (core/cat_sounds.line_for falls back to the "here" pool, which names
     her, when a key has none), and every "answer_here" variant has a matching "answer_carried";
  2. no carried pool line holds {her}, "the cat", "she" or "her" (a generic "a cat" is allowed: the tom lines
     are unattributed on purpose, D-0507 (c));
  3. the rendered line from cat_sounds.line_for(here=False) never contains the her-token, for every key, every
     carried variant and every place the cat can be.

Read-only: imports the corpus and calls line_for, which writes nothing. Run from the tree under test:
    python scripts/_test_cat_carried_unnamed_J-4227.py
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import core  # noqa: E402  (import core first, and check it is the tree under test)

assert os.path.abspath(core.__file__).lower().startswith(ROOT.lower()), core.__file__

from core import cat_content as cc  # noqa: E402
from core import cat_sounds as cs  # noqa: E402

NAMING = re.compile(r"\{her\}|\bthe cat\b|\bshe\b|\bher\b|\bherself\b", re.I)
TOKEN = "ZZHERZZ"   # a her-token no real line could contain

fails: list[str] = []
n_lines = 0
n_rendered = 0

for key, pools in cc.SOUNDS.items():
    if not pools.get("carried"):
        fails.append(f"{key}: no carried pool (line_for would fall back to the here pool)")
    for pname in pools:
        if pname.endswith("_here") and not pools.get(pname[: -len("_here")] + "_carried"):
            fails.append(f"{key}: {pname} has no matching carried variant")
        if "carried" not in pname:
            continue
        for line in pools[pname]:
            n_lines += 1
            if NAMING.search(line):
                fails.append(f"{key}/{pname}: names her: {line!r}")

locs = list(cs._PLACE_WORD) + ["study", "somewhere_unknown"]
for key, pools in cc.SOUNDS.items():
    variants = [""] + sorted({p[: -len("_carried")] for p in pools if p.endswith("_carried") and p != "carried"})
    for variant in variants:
        for loc in locs:
            for his in ("study", "garden", "wood", ""):
                for _ in range(6):   # enough draws to cover the 1-4 line pools
                    out = cs.line_for(key, False, loc, TOKEN, variant=variant, his_place=his)
                    n_rendered += 1
                    if not out:
                        fails.append(f"{key}/{variant or 'carried'}@{loc}: empty render")
                    elif TOKEN.lower() in out.lower():
                        fails.append(f"{key}/{variant or 'carried'}@{loc}: rendered her-token: {out!r}")

# sanity: the here pool DOES carry the token, so the render check above can see a naming line at all
here = cs.line_for("cat_trill", True, "study", TOKEN)
if TOKEN.lower() not in here.lower():
    fails.append(f"sanity: here pool render lost the her-token: {here!r}")

print(f"carried pool lines checked: {n_lines}; rendered carried lines: {n_rendered}; failures: {len(fails)}")
for f in fails[:20]:
    print("  FAIL", f)
sys.exit(1 if fails else 0)
