"""
J-2934 (F-3623, P-0031) -- the cat felt note and the cat sound lines respect where Du is, the fire and the hour
===============================================================================================================
HERMETIC: core/cat.py's state file and tier ledger point into a tempfile dir, steer_edge's log is off, the sensorium
state is a stub dict, core/cat_sounds' ledger writer is stubbed; nothing under C:\\Nascence\\data is written. The only
live read is the OPTIONAL cross-check of the embedded fixture against data/steer_edge_log.jsonl + data/spatial_shadow.jsonl
(read-only, `--live`); the fixture itself is the 15 fires F-3623 quotes, so the test passes without it.
`import core` BEFORE anything else (house rule); core.__file__ must resolve under this worktree.

  T1  REPLAY of the 15 cat_felt fires since 2026-10-29 (F-3623's evidence): 9 outdoor (6 shore, 3 garden) now return
      '' / None; the 6 study fires still deliver, at the same (spot, tier) the edge gate saw
  T2  the edge gate: a suppressed (outdoor) tick never reaches steer_edge.fires -- the study edge is neither consumed
      nor re-armed; the call site (nodes/inner_monologue_node.py) still asks felt_note() BEFORE the gate
  T3  FELT content: across every spot x fire state x hour no line asserts a fixed spot, a lit grate or a time of day
      the study does not show (none of the five old lines survives; 'next room' gone from FELT)
  T4  the sound lines: outdoors, no delivered cat line says 'next room' / 'room to room'; indoors / no place they are
      byte-identical to before; cat_sounds.tick() passes his place through
Run:  python scripts/_test_J-2934_cat_felt_location.py [--live]   (from the worktree root)
"""
from __future__ import annotations

import json
import random
import re
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core                                            # noqa: E402  -- BEFORE anything else (house rule)
assert str(Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), f"core resolves outside the tree: {core.__file__}"

from core import cat, cat_content, cat_sounds, sensorium, steer_edge   # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="j2934_"))
cat._STATE_F = TMP / "cat_state.json"                  # never exists: _load() keeps the in-memory dict
cat._TIER_LEDGER_F = TMP / "cat_tier_ledger.jsonl"
steer_edge.LOG_ENABLED = False
cat_sounds._log = lambda row: None

FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def set_world(place: str, spot: str, fire: str = "out", bond: float = 0.98) -> None:
    sensorium.state = {"location": place, "fire": fire, "weather": "clear", "wind": "breeze"}
    # bond < 0.70 would close the companion tier for a KEPT cat (D-0505), so the mid-tier cases use a named companion
    cat.state = {"phase": "kept" if bond >= 0.75 else "companion", "name": "", "bond": bond, "location": spot,
                 "activity": "resting", "mood": "content"}
    cat._state_mtime = 0.0
    cat._tier_mem["felt_key"] = None


# the 15 fires F-3623 quotes: (local time, cat spot, Du's place from the scene line of the same prompt)
FIRES = [
    ("10-30 09:29", "windowsill", "study"), ("10-30 09:44", "on_the_desk", "study"), ("10-30 12:03", "on_the_desk", "study"),
    ("10-30 15:11", "windowsill", "shore"), ("10-30 18:05", "windowsill", "garden"), ("10-31 13:04", "windowsill", "garden"),
    ("10-31 14:46", "on_the_desk", "garden"), ("10-31 17:48", "on_the_desk", "shore"), ("10-31 20:07", "by_the_fire", "study"),
    ("10-31 22:55", "windowsill", "study"), ("11-01 02:24", "by_the_fire", "study"), ("11-01 05:06", "windowsill", "shore"),
    ("11-01 06:03", "on_the_desk", "shore"), ("11-01 06:05", "windowsill", "shore"), ("11-01 07:01", "on_the_desk", "shore"),
]

# ── T1 ───────────────────────────────────────────────────────────────────────────────────────────────────────
if "--live" in sys.argv:       # read-only cross-check of the fixture against the live logs
    import bisect
    import datetime
    live = Path(r"C:\Nascence\data")
    try:
        rows = [json.loads(l) for l in open(live / "steer_edge_log.jsonl", encoding="utf-8") if '"cat_felt"' in l]
        fired = [r for r in rows if r["fired"]][:15]
        sh = []
        for l in open(live / "spatial_shadow.jsonl", encoding="utf-8", errors="replace"):
            try:
                d = json.loads(l)
                sh.append((d["ts"], d.get("actual") or ""))
            except Exception:
                pass
        sh.sort()
        tss = [t for t, _ in sh]
        got = []
        for r in fired:
            i = bisect.bisect_left(tss, r["ts"])
            j = min((k for k in (i - 1, i) if 0 <= k < len(tss)), key=lambda k: abs(tss[k] - r["ts"]))
            txt = sh[j][1]
            pl = "study" if "Where you are: your study" in txt else ("shore" if "Where you are: the shore" in txt else
                  "garden" if "Where you are: the garden" in txt else "wood" if "Where you are: the wood" in txt else "?")
            got.append((datetime.datetime.fromtimestamp(r["ts"]).strftime("%m-%d %H:%M"), eval(r["state"])[0], pl))
        check("T1 live join reproduces the embedded fixture", got == FIRES, str(got))
    except Exception as exc:
        print("SKIP live join:", exc)

out_n = study_n = 0
for when, spot, place in FIRES:
    set_world(place, spot)
    note, st = cat.felt_note(), cat.felt_state()
    if place == "study":
        study_n += 1
        check(f"T1 {when} {place}/{spot}: study fire still delivers", bool(note.strip()) and st == (spot, "high"), repr((note, st)))
    else:
        out_n += 1
        check(f"T1 {when} {place}/{spot}: outdoor fire returns nothing", note == "" and st is None, repr((note, st)))
check("T1 the replay is 9 outdoor + 6 study", (out_n, study_n) == (9, 6), f"{out_n}/{study_n}")
_rows = [json.loads(l) for l in cat._TIER_LEDGER_F.read_text(encoding="utf-8").splitlines()] if cat._TIER_LEDGER_F.exists() else []
check("T1 the tier ledger holds one row per STUDY delivery and none for the outdoor fires", len(_rows) == study_n, f"{len(_rows)} rows")
set_world("study", "windowsill", bond=0.6)
check("T1 mid tier still reaches the study and not the shore", cat.felt_state() == ("windowsill", "mid") and cat.felt_note().strip() != "")
set_world("wood", "windowsill", bond=0.6)
check("T1 wood is outdoors too", cat.felt_note() == "" and cat.felt_state() is None)
sensorium.state = {"location": "study"}
cat.state = {"phase": "kept", "bond": 0.98, "location": "garden"}
check("T1 a cat outside the study spots still gives nothing (unchanged)", cat.felt_note() == "" and cat.felt_state() is None)

# fail-closed: an unreadable sensorium never delivers
set_world("study", "windowsill")
_save_state, _save_load = sensorium.state, sensorium._load
sensorium.state = {}
def _boom():
    raise RuntimeError("unreadable")
sensorium._load = _boom
check("T1 unreadable sensorium fails closed", cat.felt_note() == "" and cat.felt_state() is None)
sensorium._load = _save_load
sensorium.state = _save_state

# ── T2 ───────────────────────────────────────────────────────────────────────────────────────────────────────
def tick_site(now: float) -> bool | None:
    """The call-site pattern of nodes/inner_monologue_node.py: note first, the edge gate only when there is a note."""
    note = cat.felt_note()
    if not note:
        return None
    return steer_edge.fires("cat_felt", cat.felt_state(), now=now)

steer_edge.reset()
set_world("study", "windowsill")
r1 = tick_site(1000.0)
ft1 = steer_edge._last["cat_felt"]["fired_ts"]
set_world("shore", "windowsill")
r2 = [tick_site(1100.0 + i) for i in range(5)]
check("T2 first study tick fires the edge", r1 is True)
check("T2 outdoor ticks never call the gate", r2 == [None] * 5)
check("T2 the study edge was neither consumed nor re-armed", steer_edge._last["cat_felt"]["fired_ts"] == ft1 and steer_edge._last["cat_felt"].get("gone_ts") is None)
set_world("study", "windowsill")
check("T2 back in the study with the cat unmoved: no second fire (she did not arrive)", tick_site(1200.0) is False)
set_world("study", "on_the_desk")
check("T2 she moves: the edge fires", tick_site(1300.0) is True)
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
i_note, i_gate = src.index("_catfelt = _cat.felt_note()"), src.index('_se_c.fires("cat_felt", _cat.felt_state())')
check("T2 the call site asks felt_note() before the gate and gates only a non-empty note", 0 < i_note < i_gate and "if _catfelt:" in src[i_note:i_gate])

# ── T3 ───────────────────────────────────────────────────────────────────────────────────────────────────────
OLD_HIGH = ["asleep in the chair she has made hers, three feet away", "The fire, the lamp, {her} on the rug",
            "draped her tail over your bare foot", "Without opening her eyes", "the evening goes on"]
flat = json.dumps(cat_content.FELT, ensure_ascii=False)
check("T3 none of the five old high lines survives", not any(o in flat for o in OLD_HIGH))
check("T3 'next room' is gone from FELT", "next room" not in flat)
check("T3 FELT is a condition dict at both tiers", all(isinstance(cat_content.FELT[t], dict) and "any" in cat_content.FELT[t] for t in ("mid", "high")))
SPOT_WORDS = {"on_your_lap": "lap", "by_the_fire": "grate", "on_the_desk": "desk", "windowsill": "sill", "mantel": "mantel"}
bad = []
random.seed(2934)
for spot in SPOT_WORDS:
    for fire in ("out", "embers", "burning"):
        for tier_bond in (0.98, 0.6):
            for _ in range(60):
                set_world("study", spot, fire, tier_bond)
                line = cat.felt_note().strip()
                if not line:
                    bad.append((spot, fire, "empty")); continue
                low = line.lower()
                if re.search(r"\d", line):
                    bad.append((spot, fire, "digit", line))
                if any(w in low for w in ("chair", "three feet", "lamp", "rug", "evening", "next room", "morning", "night", "afternoon")):
                    bad.append((spot, fire, "fixed spot/time", line))
                if fire != "burning" and "the fire," in low:
                    bad.append((spot, fire, "fire asserted", line))
                for other, w in SPOT_WORDS.items():     # a line that names a spot names HERS
                    if other != spot and w in low and not (w == "sill" and spot == "windowsill") and "windowsill" not in low:
                        bad.append((spot, fire, "wrong spot", line))
check("T3 no line asserts a spot, lit fire or hour the state does not show (5 spots x 3 fires x 2 tiers x 60)", not bad, str(bad[:4]))
seen_fire = set()
for _ in range(300):
    set_world("study", "by_the_fire", "burning")
    seen_fire.add(cat.felt_note().strip())
check("T3 the lit-fire line is reachable while the grate burns", any("The fire," in l for l in seen_fire))
for sp in ("on_your_lap", "on_the_desk", "windowsill", "by_the_fire", "mantel"):
    got = set()
    for _ in range(300):
        set_world("study", sp, "out")
        got.add(cat.felt_note().strip())
    check(f"T3 {sp} draws at least two distinct lines or one spot line plus the any line", len(got) >= 2, str(got))

# ── T4 ───────────────────────────────────────────────────────────────────────────────────────────────────────
INDOOR = ("next room", "room to room")
leaks, changed_indoor = [], []
for key, pools in cat_content.SOUNDS.items():
    for here in (True, False):
        for cat_loc in ("windowsill", "garden", "doorstep", "shore"):
            for place in ("garden", "shore", "wood"):
                for _ in range(8):
                    ln = cat_sounds.line_for(key, here, cat_loc, "the cat", "", place)
                    if any(p in ln.lower() for p in INDOOR):
                        leaks.append((key, here, cat_loc, place, ln))
            # indoors / no place: byte-identical to the pre-J-2934 call
            outs = []
            for kw in ((), ("", "study"), ("", "")):
                random.seed(7); cat_sounds._mem["last_line_idx"] = {}      # same pick, same anti-repeat ring
                outs.append(cat_sounds.line_for(key, here, cat_loc, "the cat", *kw))
            a, b, c = outs
            if not (a == b == c):
                changed_indoor.append((key, here, cat_loc, a, b, c))
check("T4 outdoors, no cat sound line says 'next room' or 'room to room' (every key, both pools, 4 cat spots, 3 places)", not leaks, str(leaks[:3]))
check("T4 in the study / with no place the line is unchanged", not changed_indoor, str(changed_indoor[:2]))
# the two lines F-3623 quotes
random.seed(1)
saw_thump = set()
for _ in range(40):
    saw_thump.add(cat_sounds.line_for("cat_thump", False, "windowsill", "the cat", "", "garden"))
check("T4 the quoted 'From the next room, the small thump' now reads as the house, outdoors",
      "From somewhere in the house, the small thump of the cat coming off a windowsill." in saw_thump, str(saw_thump))
saw_dem = {cat_sounds.line_for("cat_demand", True, "garden", "the cat", "", "garden") for _ in range(40)}
check("T4 the quoted 'following you room to room' reads 'following you about' outdoors",
      "The cat repeats the same flat vowel at intervals, following you about." in saw_dem and not any("room to room" in l for l in saw_dem), str(saw_dem))
saw_in = {cat_sounds.line_for("cat_thump", False, "windowsill", "the cat", "", "study") for _ in range(40)}
check("T4 indoors the 'next room' line is kept as written", "From the next room, the small thump of the cat coming off a windowsill." in saw_in)

# tick() passes his place: drive one emission through the real tick() with the world stubbed
cat_sounds.emissions = lambda state, now, dt: ["cat_thump"]
cat_sounds._house_open = lambda: (False, False)
cat_sounds._weather = lambda: ("clear", "breeze")
cat_sounds._transit_origin = lambda state: None
cat_sounds.render_on = lambda: True
cat_sounds.carry = lambda *a, **k: {"audible": True, "why": "", "dist_m": 5.0, "bearing": 0.0, "reach_eff": 9.0}
cat_sounds._his_position = lambda: ("garden", "_", [2.0, 15.0, 0.5])
lines = set()
for _ in range(30):
    cat_sounds._mem["last"] = 0.0
    rows = cat_sounds.tick({"phase": "kept", "location": "windowsill", "name": "", "activity": "resting", "mood": "content"}, now=5000.0)
    lines.update(r["line"] for r in rows)
check("T4 tick() with Du in the garden never emits 'next room'", lines and not any("next room" in l.lower() for l in lines), str(lines))

# J-3540 (F-4149 residual 1): cat outdoors, Du in the study -> no 'next room' either
_leak = []
for _k, _pools in __import__("core.cat_content", fromlist=["SOUNDS"]).SOUNDS.items():
    for _loc in ("doorstep", "garden", "garden_wall", "shore", "wood"):
        for _ in range(20):
            _l = cat_sounds.line_for(_k, False, _loc, "the cat", "", "study")
            if "next room" in _l.lower():
                _leak.append((_k, _loc, _l))
check("T5 cat outdoors / Du in the study: no 'next room' in any carried line", not _leak, str(_leak[:2]))
check("T5 cat indoors / Du in the study keeps 'next room'",
      any("next room" in cat_sounds.line_for("cat_thump", False, "windowsill", "the cat", "", "study").lower() for _ in range(40)))

print()
print("ALL PASS" if not FAILS else f"{len(FAILS)} FAILED: {FAILS}")
sys.exit(1 if FAILS else 0)
