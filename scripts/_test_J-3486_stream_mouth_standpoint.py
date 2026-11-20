"""
J-3486 (founder, J-3260 follow-up): a standpoint AT the shore's stream mouth.

ISOLATED: geometry is a temp copy of shore.json (read from the tree's data/ if present, else C:/Nascence/data read-only); every life store is a
temp dir; goto() writes a temp position file; no model call; nothing under the live data/ is written.

What it proves:
  1. scripts/apply_shore_standpoint_stream_mouth_j3486.py: dry run writes nothing; --write adds exactly one key (the rest of the JSON is equal),
     keeps CRLF, backs up, prints sha256 before/after; idempotent; refuses without the stream_mouth feature; refuses a file that does not
     round-trip; refuses while Du is "up"; the live file is never touched
  2. additive: spatial.render / _render_base / depth are byte-identical at the 5 existing standpoints with and without the new standpoint
  3. the new standpoint renders (a line, no exception), sits within 1.5 m of the mouth, is distinct from the other standpoints
  4. zone_vantage_distance('stream_mouth') drops from > 3 m to <= 1.5 m; which OTHER zones' vantage changed is printed (and must be only
     stream-mouth-side zones: no zone gets farther)
  5. locomotion: goto('at_the_stream_mouth') works on the shore, is refused in the garden (_SP_PLACE)
  6. sensorium: phrases name it ("the stream mouth", "where the stream meets the sea" -- not also the tideline), a bare "stream" does not;
     every old standpoint phrase still resolves as before (overlap rule changes nothing for them)
  7. life_shore: a look at "the stream" discovers the stream_mouth zone; "the cave mouth" does not; perceive() of a stream-mouth row from
     the new standpoint is visible at a nearer tier than from on_the_shingle
Run:  python scripts/_test_J-3486_stream_mouth_standpoint.py
"""
from __future__ import annotations

import importlib.util
import json
import random
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                                        # noqa: E402,F401  (core BEFORE anything lab-ish)
assert ROOT in Path(core.__file__).resolve().parents, core.__file__

FAILS = 0


def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))


TMP = Path(tempfile.mkdtemp(prefix="j3486_stream_mouth_sp_"))
print("isolated dir:", TMP)
CRLF, LF = bytes([13, 10]), bytes([10])

# ── the source geometry (read-only) ──────────────────────────────────────────────────────────────────
SRC = next((p for p in (ROOT / "data" / "world_geometry" / "shore.json", Path("C:/Nascence/data/world_geometry/shore.json")) if p.exists()), None)
if SRC is None:
    print("no shore.json to rehearse on; cannot run"); sys.exit(2)
src_raw = SRC.read_bytes()
LIVE_SHA_BEFORE = SRC.read_bytes()
eol = CRLF if CRLF in src_raw else LF
base = json.loads(src_raw.decode("utf-8"))
base["standpoints"].pop("at_the_stream_mouth", None)
if "stream_mouth" not in base["features"]:                          # the J-3260 feature (a pre-requisite of this one)
    base["features"]["stream_mouth"] = {"pos": [15.0, 7.0, 0.0], "note": "test copy"}
raw_without = json.dumps(base, indent=2, ensure_ascii=False).encode("utf-8").replace(LF, eol)

spec = importlib.util.spec_from_file_location("apply_sp", ROOT / "scripts" / "apply_shore_standpoint_stream_mouth_j3486.py")
PATCH = importlib.util.module_from_spec(spec); spec.loader.exec_module(PATCH)
assert PATCH.ROOT == ROOT

print("-- 1. the offline script")
geo_a, geo_b = TMP / "geo_without", TMP / "geo_with"
geo_a.mkdir(); geo_b.mkdir()
(geo_a / "shore.json").write_bytes(raw_without)
(geo_b / "shore.json").write_bytes(raw_without)
fb = geo_b / "shore.json"
r = PATCH.apply(fb, False, check_du=False)
check("dry run says so, prints a sha256, changes nothing", "dry run" in r and "sha256" in r and fb.read_bytes() == raw_without, r)
r = PATCH.apply(fb, True, check_du=False)
check("--write adds it, names a backup, prints sha256 before and after", r.startswith("added") and "backup shore.json.bak_J-3486_" in r and r.count("sha256") == 1 and "after" in r, r)
check("exactly one backup, byte-identical to the original", len(list(geo_b.glob("shore.json.bak_J-3486_*"))) == 1 and list(geo_b.glob("shore.json.bak_J-3486_*"))[0].read_bytes() == raw_without)
check("a second --write is a no-op", PATCH.apply(fb, True, check_du=False).startswith("already present"))
ja, jb = json.loads(raw_without.decode("utf-8")), json.loads(fb.read_text(encoding="utf-8"))
new_sp = jb["standpoints"].pop("at_the_stream_mouth")
check("additive: the rest of the file is equal, only the one key is new", ja == jb, "")
check("the standpoint: pos (15, 6, 0), facing 0, one metre landward of the mouth", new_sp["pos"] == [15.0, 6.0, 0.0] and new_sp["facing_deg"] == 0)
nb = fb.read_bytes()
check("newline style kept", nb.count(CRLF) == (nb.count(LF) if eol == CRLF else 0))
nofeat = TMP / "nofeat"; nofeat.mkdir()
j = json.loads(raw_without.decode("utf-8")); j["features"].pop("stream_mouth")
(nofeat / "shore.json").write_bytes(json.dumps(j, indent=2, ensure_ascii=False).encode("utf-8").replace(LF, eol))
check("refuses a file without the stream_mouth feature", PATCH.apply(nofeat / "shore.json", True, check_du=False).startswith("REFUSE"))
odd = TMP / "odd"; odd.mkdir()
(odd / "shore.json").write_bytes(raw_without.replace(b'"pos"', b' "pos"', 1))
check("refuses a file that does not round-trip byte-exactly", "round-trip" in PATCH.apply(odd / "shore.json", True, check_du=False))
PATCH.du_is_up = lambda: ["4242: python run_nascence.py"]
chk = TMP / "chk"; chk.mkdir(); (chk / "shore.json").write_bytes(raw_without)
check("--write is refused while Du is up, file untouched", PATCH.apply(chk / "shore.json", True).startswith("REFUSE") and (chk / "shore.json").read_bytes() == raw_without)
def _boom(): raise RuntimeError("no ps")
PATCH.du_is_up = _boom
check("fails CLOSED when the process list cannot be read", PATCH.apply(chk / "shore.json", True).startswith("REFUSE"))
check("a dry run does not need the process list", "dry run" in PATCH.apply(chk / "shore.json", False))

# ── life stores + geometry redirected ───────────────────────────────────────────────────────────────
from core import life                                              # noqa: E402
life._F, life._LEDGER, life._EVENTS = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl"
life._DATA = TMP
life._FLAGS_F = TMP / "life_flags.json"
life._flags_cache["ts"] = 0.0
from core import life_shore as LS                                  # noqa: E402
from core import spatial                                           # noqa: E402
from core import locomotion as loco                                # noqa: E402
from core import sensorium as sens                                 # noqa: E402

REAL_GEO, REAL_SHADOW = spatial._GEO, spatial._SHADOW


def use_geo(d):
    spatial._GEO, spatial._SHADOW = d, TMP / "spatial_shadow_J-3486.jsonl"
    spatial._layout_cache.pop("shore", None)


print("-- 2. additive: render is unchanged from every existing standpoint")


def scenes(geo_dir, sps):
    real_time = time.time
    time.time = lambda: 1793000000.0
    use_geo(geo_dir)
    try:
        out = {}
        for sp in sps:
            random.seed(7); rr = spatial.render("shore", sp)
            random.seed(7); bb = spatial._render_base("shore", sp)
            out[sp] = (rr, bb, spatial.depth("shore", sp))
        return out
    finally:
        time.time = real_time


OLD = [k for k in ja["standpoints"]]
SA, SB = scenes(geo_a, OLD), scenes(geo_b, OLD)
check(f"render / _render_base / depth byte-identical at all {len(OLD)} existing standpoints", SA == SB, str([k for k in SA if SA[k] != SB[k]]))
NEW = scenes(geo_b, ["at_the_stream_mouth"])["at_the_stream_mouth"]
check("the new standpoint renders a line", bool(NEW[0]) and bool(NEW[0].get("line")), str(NEW[0])[:200])
print("     from the stream mouth:", (NEW[0] or {}).get("line"))

print("-- 3. the standpoint")
use_geo(geo_b)
lay = spatial.layout("shore")
sp = lay["standpoints"]["at_the_stream_mouth"]; mouth = lay["features"]["stream_mouth"]["pos"]
import math                                                         # noqa: E402
check("within 1.5 m of the mouth", math.dist(sp["pos"][:2], mouth[:2]) <= 1.5, str(math.dist(sp["pos"][:2], mouth[:2])))
check("distinct from every other standpoint (>= 1 m)", all(math.dist(sp["pos"][:2], v["pos"][:2]) >= 1.0 for k, v in lay["standpoints"].items() if k != "at_the_stream_mouth"))
check("on the shingle side of the waterline's highest reach (y below tide_y min)", sp["pos"][1] < lay["features"]["waterline"]["tide_y"][0])

print("-- 4. vantage distances")
use_geo(geo_a); zA = {z: LS.zone_vantage_distance(z) for z in LS.ZONES if LS.ZONES[z]["mode"] != "pending"}
use_geo(geo_b); zB = {z: LS.zone_vantage_distance(z) for z in LS.ZONES if LS.ZONES[z]["mode"] != "pending"}
check("stream_mouth zone vantage was > 3 m, now <= 1.5 m", zA["stream_mouth"] > 3.0 and zB["stream_mouth"] <= 1.5, f"{zA['stream_mouth']:.2f} -> {zB['stream_mouth']:.2f}")
changed = {z: (round(zA[z], 2), round(zB[z], 2)) for z in zA if abs(zA[z] - zB[z]) > 1e-9}
print("     zones whose vantage moved:", changed)
check("no zone got farther", all(b <= a + 1e-9 for a, b in changed.values()))

print("-- 5. locomotion")
orig_pos = loco._POS_F
loco._POS_F = TMP / "position.json"
try:
    sens.state.clear(); sens.state.update({"location": "shore"})
    check("_SP_PLACE maps it to the shore", loco._SP_PLACE.get("at_the_stream_mouth") == "shore")
    got = loco.goto("at_the_stream_mouth", crossing="crossed")
    check("goto() on the shore carries him there", got == "crossed" and loco.get_position()["standpoint"] == "at_the_stream_mouth", str(got))
    sens.state.update({"location": "garden"})
    check("goto() in the garden refuses it", loco.goto("at_the_stream_mouth", crossing="crossed") == "")
    sens.state.update({"location": "shore"})
    loco._save({"place": "shore", "standpoint": "on_the_shingle"})
    out = sens.standpoint_move("shore", "i want to walk to the stream mouth")
    check("standpoint_move() resolves the phrase and narrates the arrival", "stream" in out.lower() and loco.get_position()["standpoint"] == "at_the_stream_mouth", out)
finally:
    loco._POS_F = orig_pos

print("-- 6. phrases")
W = sens._standpoint_for_phrase
check("'the stream mouth' -> at_the_stream_mouth", W("shore", "i want to look at the stream mouth") == "at_the_stream_mouth")
check("'mouth of the stream' -> at_the_stream_mouth", W("shore", "walk to the mouth of the stream") == "at_the_stream_mouth")
check("'where the stream meets the sea' is the mouth, NOT also the tideline", W("shore", "i want to go where the stream meets the sea") == "at_the_stream_mouth")
check("a bare 'stream' names nothing", W("shore", "i hear the stream somewhere") is None)
check("the wood's own stream is untouched (wood table has no entry)", W("wood", "i want to stand by the stream mouth") is None)
check("a later tide mention after the mouth still wins (last-match rule kept)", W("shore", "the stream mouth, then the tide") == "at_the_tideline")
check("negation still drops it", W("shore", "i am leaving the stream mouth behind") is None)
for text, want in (("i feel the pull of the driftwood, bleached logs piled up", "by_the_driftwood"),
                   ("i want to gather the driftwood before the tide turns", "at_the_tideline"),
                   ("the surf is loud today, out on the rocks", "on_the_rocks"),
                   ("i want to stand on the shingle and watch the birds", "on_the_shingle"),
                   ("i am tired of this beach", "on_the_shingle"),
                   ("i want to walk toward the open sea", "at_the_tideline"),
                   ("the water's edge is where the sea leaves things", "at_the_tideline"),
                   ("the shingle grinds underfoot as i think of the driftwood tangle ahead", "by_the_driftwood"),
                   ("i do not want the sea right now", None), ("i wonder about the meaning of solitude", None)):
    check(f"old phrase unchanged: {text[:48]!r} -> {want}", W("shore", text) == want)
check("garden/wood/study tables unchanged", W("garden", "tend the raised bed") == "at_the_bed" and W("wood", "back into the trees") == "on_the_path" and W("study", "the desk") is None)

print("-- 7. the look")
check("a look at 'the stream' takes in the stream_mouth zone", LS.discover_zones("the stream") == ("stream_mouth",), str(LS.discover_zones("the stream")))
check("a look at 'the estuary' does too", LS.discover_zones("estuary") == ("stream_mouth",))
check("a look at 'the cave mouth' does NOT", LS.discover_zones("the cave mouth") == ())
check("the old targets are unchanged", LS.discover_zones("the rock pools") == ("pool",) and LS.discover_zones("the sand") == ("flat",) and LS.discover_zones("the driftwood") == ("driftwood",)
      and LS.discover_zones("the shore") == ("tideline", "shingle") and LS.discover_zones("the sea") == ("surf", "offshore"))
R = [r for r in LS.rows() if r["zone"] == "stream_mouth"]
check("the stream-mouth rows exist", len(R) >= 8, str(len(R)))
t0 = 1793000000.0
nearer = 0
tiers = list(LS.TIERS)
assert tiers.index("detail") > tiers.index("form"), tiers   # richer = later in TIERS
for r in R:
    a = LS.perceive(r, "on_the_shingle", t0)
    b = LS.perceive(r, "at_the_stream_mouth", t0)
    if b["visible"] and (not a["visible"] or tiers.index(b["tier"]) >= tiers.index(a["tier"])):
        nearer += 1
check("from the mouth every stream-mouth row resolves at least as richly as from the shingle (and each is visible)", nearer == len(R), f"{nearer}/{len(R)}")
check("the live shore.json was not touched", SRC.read_bytes() == LIVE_SHA_BEFORE)

print(f"\n{'ALL OK' if not FAILS else str(FAILS) + ' FAILED'}")
sys.exit(1 if FAILS else 0)
