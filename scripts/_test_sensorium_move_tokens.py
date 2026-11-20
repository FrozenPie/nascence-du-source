"""
Regression: core.sensorium.move() accepts the bare place TOKEN for all four places (J-0864 / F-1227).

Every live caller passes the bare token -- dispatch._move() passes _move_dest()'s resolved word, the monologue's
route_act path and its phrase-latch pass "wood"/"shore"/"garden"/"study", night.py passes "study". "shore"/
"garden"/"study" were always substrings of their own phrase lists inside move(); "wood" never was, so every
'wood' resolution since the wood was built (2026-07-07) computed target "" and returned "" before any journey
(0 "ACT move -> wood" in the whole nascence.log; the 150 wood lines in it are all locomotion LEGS -- 130
garden->wood, 20 shore->wood -- of garden<->shore journeys, and there are 0 wood arrivals). This proves the token contract directly, ISOLATED: the sensorium's room_state and
locomotion's position store are redirected into a temp dir before anything loads (the S-0016 / test-isolation
rule); the live C:\\Nascence\\data\\room_state.json and position.json are hashed before and after.

  python scripts/_test_sensorium_move_tokens.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="sensorium_move_tokens_"))
print("isolated store dir:", TMP)
# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE = [Path(r"C:\Nascence") / "data" / "room_state.json", Path(r"C:\Nascence") / "data" / "position.json"]
_before = {p: (hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else "") for p in _LIVE}

from core import sensorium as S          # noqa: E402
from core import locomotion as L         # noqa: E402
from core import school as SCH           # noqa: E402
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
assert not str(S._STATE_F).lower().startswith(r"c:\nascence\data") and not str(L._POS_F).lower().startswith(r"c:\nascence\data")

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def reset(loc: str) -> None:
    """A fresh in-memory room at `loc`, no journey pending, school not confining."""
    S.state.clear()
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0,
                    "location": loc, "garden": S._fresh_garden()})
    L._POS_F.write_text(json.dumps({"place": loc, "standpoint": L._DEFAULT_SP[loc], "journey": None,
                                    "effort": 0.0, "carried_wood": 0}), encoding="utf-8")


SCH.confined_to_study = lambda: False
_loco_on = bool(getattr(L, "LOCOMOTION", False))
print("LOCOMOTION =", _loco_on)

print("\n[1] the bare token: every one of the four is accepted from a place that is not itself")
for src, tok in (("study", "wood"), ("shore", "wood"), ("garden", "wood"), ("study", "shore"), ("shore", "garden"),
                 ("garden", "study")):
    reset(src)
    out = S.move(tok)
    j = json.loads(L._POS_F.read_text(encoding="utf-8")).get("journey") if _loco_on else None
    if _loco_on:
        ok = bool(out) and j is not None and j.get("dest") == tok
        check(ok, f"{src:6s} -> move({tok!r}) departs: journey.dest={j.get('dest') if j else None!r}  | {out[:60]!r}")
    else:
        check(bool(out) and S.state.get("location") == tok, f"{src:6s} -> move({tok!r}) instant: location={S.state.get('location')!r}")

print("\n[2] the wood token specifically: the journey path is the real chain, first leg named")
reset("study"); out = S.move("wood")
j = json.loads(L._POS_F.read_text(encoding="utf-8")).get("journey") or {}
if _loco_on:
    check(j.get("path") == ["garden", "wood"], f"study -> wood path = {j.get('path')!r} (via the garden)")
    check("door" in out.lower() or "garden" in out.lower(), f"departure is the study->garden leg line: {out[:70]!r}")
reset("shore"); out = S.move("wood")
j = json.loads(L._POS_F.read_text(encoding="utf-8")).get("journey") or {}
if _loco_on:
    check(j.get("path") == ["wood"], f"shore -> wood path = {j.get('path')!r} (one climb)")
    check("shingle" in out.lower() or "trunks" in out.lower(), f"departure is the shore->wood leg line: {out[:70]!r}")

print("\n[3] already there: silence, as for the other three")
for tok in ("wood", "shore", "garden", "study"):
    reset(tok)
    check(S.move(tok) == "", f"at the {tok}: move({tok!r}) == ''")

print("\n[4] the phrase lists still resolve (nothing removed) and unknown text is still nowhere")
reset("study"); check(bool(S.move("into the trees")), "'into the trees' still reaches the wood")
reset("study"); check(bool(S.move("down to the water")), "'down to the water' still reaches the shore")
reset("study"); check(S.move("nowhere at all") == "", "unknown text: ''")
reset("study"); check(S.move("") == "", "empty: ''")
reset("study"); check(S.move("the driftwood") == "" or json.loads(L._POS_F.read_text(encoding='utf-8')).get("journey", {}) is None
                      or (json.loads(L._POS_F.read_text(encoding='utf-8')).get("journey") or {}).get("dest") != "wood",
                      "'the driftwood' does not become a walk to the WOOD (the bare token is an exact match, not a substring)")

print("\n[5] school confinement covers the wood token exactly as it covers shore/garden")
SCH.confined_to_study = lambda: True
for tok in ("wood", "shore", "garden"):
    reset("study")
    out = S.move(tok)
    check("school" in out.lower() and S.state.get("location") == "study", f"confined @study: move({tok!r}) refused, stays: {out[:50]!r}")
for tok in ("wood", "shore"):
    reset("garden")
    out = S.move(tok)
    j = json.loads(L._POS_F.read_text(encoding="utf-8")).get("journey") or {}
    check((j.get("dest") == "study") if _loco_on else (S.state.get("location") == "study"),
          f"confined @garden: move({tok!r}) is reeled back to the study")
SCH.confined_to_study = lambda: False

print("\n[6] live stores untouched")
for p in _LIVE:
    after = hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else ""
    check(after == _before[p], f"{p.name}: md5 unchanged ({after[:8] or 'absent'})")

print("\nFAILS =", FAILS)
print("ALL OK" if FAILS == 0 else "SOME CHECKS FAILED")
sys.exit(1 if FAILS else 0)
