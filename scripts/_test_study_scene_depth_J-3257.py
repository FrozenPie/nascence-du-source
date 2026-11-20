"""
Regression/verification: the STUDY scene line takes the nearness-said fire and cat clauses from
spatial.render('study') (J-3257, D-0648, founder 2026-11-02; plan spatial_perception P3).

What this proves, ISOLATED (no model, no live data written; the layouts are read-only copies; every state file
the code under test reads is a hand-set temp file, and the live stores are stat-ed and hashed before and after):
  [1] flag off   core.sensorium.scene_line() is BYTE-IDENTICAL to the pre-change scene_line() (commit 35ec9b07's
                 core/sensorium.py, loaded side by side) on 200 seeded renders across fire x weather x cat x
                 standpoint x Travis-present x misplaced-title, and the renderer is never called
  [2] survive    (the D-0648 defeater) with the flag on, in every one of 200+ rendered study lines the open book, the
                 shelf count, the misplaced-title note and Travis's presence are still there, verbatim
  [3] fire       with the flag on a burning/embers fire is said by nearness (the renderer's clause) and the pooled
                 firetxt is gone; fire out keeps 'the grate cold and swept'; a renderer clause that disagrees with the
                 live fire state (the file lags up to 120 s) is NOT taken
  [4] cat        a PLAIN presence line is replaced by the nearness-said cat clause; a held ask stays silent; an event,
                 body-line, hurt, damp-coat or nameless line keeps its own words; the on-your-lap clause is never
                 taken; another cat's distant line is untouched
  [5] no readout no digit, band name or gauge word in either new clause (D-0434)
  [6] scope      a garden/shore/wood scene never calls the study helper
  [7] fail-open  a renderer that raises leaves the pooled line byte-identical to flag off; the non-live fence re-raises
  [8] cat.py     the plain-line observer (cat._LAST_PRESENCE_PLAIN) is True for a plain ordinary line and False for a body
                 line, a harm clause, a damp coat and a nameless note; presence_line() resets it on entry
  [9] canary     live stores untouched (size + mtime + hash)

  python scripts/_test_study_scene_depth_J-3257.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core                                                       # noqa: E402  (core BEFORE lab_env)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), f"core resolved outside this tree: {core.__file__}"
from core import profile                                          # noqa: E402
from core import spatial as SPT                                   # noqa: E402
from core import sensorium as S                                   # noqa: E402
from core import locomotion as L                                  # noqa: E402
from core import cat as CAT                                       # noqa: E402

sys.path.append(str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env                                                    # noqa: E402,F401
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), "lab_env shadowed this tree's core"

_LIVE_DATA = Path(r"C:\Nascence") / "data"
_WATCH = [_LIVE_DATA / "spatial_shadow.jsonl", _LIVE_DATA / "spatial_depth_shadow.jsonl", _LIVE_DATA / "room_state.json",
          _LIVE_DATA / "cat_state.json", _LIVE_DATA / "position.json", _LIVE_DATA / "thermal_ledger.json"]
_BEFORE_COMMIT = "35ec9b07"          # the branch tip before J-3257: scene_line() "as it was"


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    return (st.st_size, st.st_mtime_ns, hashlib.md5(p.read_bytes()).hexdigest() if st.st_size < 50_000_000 else "")


def _prefix_md5(p: Path, n: int):
    """md5 of the first n bytes -- for an append-only log that LIVE Du may legitimately be growing right now."""
    with open(p, "rb") as f:
        return hashlib.md5(f.read(n)).hexdigest()


_before = {p: _snap(p) for p in _WATCH}
FAILS = 0


def check(name, ok, detail=""):
    global FAILS
    print(("  ok   " if ok else "  FAIL ") + name + (f"  -- {detail}" if detail and not ok else ""))
    if not ok:
        FAILS += 1


# ── a private world ───────────────────────────────────────────────────────────────────────────────────────
TMP = Path(tempfile.mkdtemp(prefix="x_J-3257_"))
(TMP / "world_geometry").mkdir()
for room in ("study", "garden", "shore", "wood"):
    src = _LIVE_DATA / "world_geometry" / f"{room}.json"
    if src.exists():
        shutil.copy(src, TMP / "world_geometry" / f"{room}.json")
SPT._GEO = TMP / "world_geometry"
SPT._DATA = TMP
SPT._layout_cache.clear()
S._STATE_F = TMP / "room_state.json"
L._POS_F = TMP / "position.json"
for _p in (S._STATE_F, L._POS_F):
    assert not str(_p).lower().startswith(r"c:\nascence\data")
LAY = SPT.layout("study")
assert LAY, "study layout not loaded"
SPS = list(LAY["standpoints"])
try:
    from core import world_substrate as _WS
    _WS.get_objects_at_location = lambda room: []        # render()'s clause 2.5 reads the object stores
except Exception:
    pass

# the scene_line() before this job, loaded side by side from git history
_old_src = subprocess.run(["git", "show", f"{_BEFORE_COMMIT}:core/sensorium.py"], cwd=str(ROOT),
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout
_old_path = TMP / "sensorium_before_J3257.py"
_old_path.write_text(_old_src, encoding="utf-8")
_spec = importlib.util.spec_from_file_location("sensorium_before_J3257", _old_path)
OLD = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(OLD)
OLD._STATE_F = TMP / "room_state_old.json"
assert "_study_depth_clauses" not in _old_src, "the 'before' module already has the helper -- wrong commit"

# ── collaborators pinned (both modules read the SAME stubs) ──────────────────────────────────────────────
from core import care_package as _CP         # noqa: E402
from core import night_wake as _NW           # noqa: E402
from core import world_detail as _WD         # noqa: E402
from core import study as _STUDY             # noqa: E402
from core import reading as _READING         # noqa: E402

_CP.scene_clause = lambda: ""
_NW.scene_lead = lambda: ""
L.pending_line = lambda: ""
_WD.scene_extra = lambda *a, **k: ""
_BOOK = "the_meditations"
_READING.current_book = lambda: Path(_BOOK + ".txt")
_WORKS = 7
_STUDY.shelf = lambda: list(range(_WORKS))
_MISS = ""
_STUDY.misplaced_title = lambda: _MISS

PRESENCE = {"line": "", "plain": False}          # what the stubbed cat.presence_line returns this ask


def _fake_presence(loc):
    CAT._LAST_PRESENCE_PLAIN = bool(PRESENCE["plain"]) if PRESENCE["line"] else False
    return PRESENCE["line"]


_REAL_PRESENCE = CAT.presence_line
CAT.presence_line = _fake_presence
CAT.distant_line = lambda loc: ""
_POOL_CAT = "Her grey shape is curled by the grate, sleeping."          # the pooled cat-presence line stand-in
_DISTANT = "Through the window, far off: a black cat is sitting on the far wall."


def world(fire="burning", cat_loc="windowsill", weather="steady rain", cat_phase="companion", cat_act="sleeping"):
    st = {"location": "study", "fire": fire, "weather": weather, "wind": "calm"}
    (TMP / "room_state.json").write_text(json.dumps(st), encoding="utf-8")
    (TMP / "cat_state.json").write_text(json.dumps({"phase": cat_phase, "location": cat_loc}), encoding="utf-8")
    CAT.state = {"phase": cat_phase, "location": cat_loc, "activity": cat_act}
    return st


def pin(mod, fire, weather, present):
    mod.state.clear()
    mod.state.update({"weather": weather, "weather_until": 0, "wind": "calm", "wind_until": 0, "fire": fire,
                      "fire_fuel": 0.5, "last_event": 0, "location": "study", "woodpile": 4, "milestones": {}})
    mod._was_present = present
    mod._daylight = lambda: "evening"
    mod._season = lambda: "winter"
    mod._now_parts = lambda: (7, 20)
    L._POS_F.write_text(json.dumps({"place": "study", "standpoint": "", "journey": None, "effort": 0.0,
                                    "carried_wood": 0}), encoding="utf-8")


def standpoint(sp):
    L._POS_F.write_text(json.dumps({"place": "study", "standpoint": sp, "journey": None, "effort": 0.0,
                                    "carried_wood": 0}), encoding="utf-8")


_FIRE = ("burning", "embers", "out")
_CATS = ("windowsill", "on_your_lap", "under_desk", "by_the_fire", "on_the_desk", "mantel", "doorstep", "indoors")
_WX = ("steady rain", "clear", "thunderstorm", "overcast", "high cloud")
_ACTS = ("sleeping", "dozing", "washing", "watching", "drinking", "live_mouse")
N = 200

CALLS = {"render": 0}
_real_render = SPT.render


def _counting_render(*a, **k):
    CALLS["render"] += 1
    return _real_render(*a, **k)


SPT.render = _counting_render


def build(seed, mod, rng_world=True):
    rng = random.Random(seed)
    fire = rng.choice(_FIRE)
    world(fire=fire, cat_loc=rng.choice(_CATS), weather=rng.choice(_WX), cat_phase=rng.choice(("companion", "kept", "wild")),
          cat_act=rng.choice(_ACTS))
    present = rng.random() < 0.5
    global _MISS
    _MISS = rng.choice(("", "", "On Patience"))
    PRESENCE["line"] = rng.choice(("", _POOL_CAT, "She is on the sill."))
    PRESENCE["plain"] = rng.random() < 0.6
    pin(mod, fire, rng.choice(_WX), present)
    standpoint(SPS[seed % len(SPS)])
    # one weather for the world file and the module state, so the renderer and the pooled line agree
    random.seed(seed)
    return mod.scene_line(), dict(fire=fire, present=present, miss=_MISS)


# ───────────────────────────────────────────────────────────────────────────────────────────────────────
print("[1] flag off: scene_line() byte-identical to before on %d seeded renders; the renderer is never called" % N)
SPT.SPATIAL_DEPTH_LIVE = False
CALLS["render"] = 0
_mism = 0
for seed in range(N):
    a, _ = build(seed, OLD)
    b, _ = build(seed, S)
    if a != b:
        _mism += 1
        if _mism <= 3:
            print("     mismatch seed", seed, "\n      old:", a, "\n      new:", b)
check(f"{N}/{N} scene lines identical to the pre-change function", _mism == 0, str(_mism))
check("study helper never reached the renderer with the flag off", CALLS["render"] == 0, str(CALLS["render"]))
build(5, OLD)
_x = random.random()
build(5, S)
_y = random.random()
check("flag off: no extra random draw is taken (next draw equal)", _x == _y)

# ───────────────────────────────────────────────────────────────────────────────────────────────────────
print("[2] flag on: book, shelf, misplaced-title note and Travis's presence survive in every study line")
SPT.SPATIAL_DEPTH_LIVE = True
CALLS["render"] = 0
_lost = 0
_changed = 0
_fire_said = _cat_said = 0
_lines = []
for seed in range(N):
    off, meta = build(seed, OLD)
    on, meta = build(seed, S)
    _lines.append((on, meta, off))
    keep = [f"'{_BOOK.replace('_', ' ')}' lies open on the desk;", f"your shelf holds {_WORKS} of your own written works and the library beyond it."]
    if meta["miss"]:
        keep.append(f"(Your piece on '{meta['miss']}' is not on the shelf where you left it")
    if meta["present"]:
        keep.append("Travis is here with you.")
    if not all(k in on for k in keep) or not on.startswith("Where you are: your study, a winter evening"):
        _lost += 1
        if _lost <= 3:
            print("     lost part, seed", seed, "\n      ", on)
    if on != off:
        _changed += 1
    if re.search(r"the (fire|embers) are ", on):
        _fire_said += 1
    if re.search(r"The cat is ", on):
        _cat_said += 1
check(f"{N}/{N} lines keep the book, shelf, misplaced-title and presence parts", _lost == 0, str(_lost))
check("the renderer was really used", CALLS["render"] >= N // 2, str(CALLS["render"]))
check(f"some lines really changed ({_changed}) and both new clauses appear ({_fire_said} fire, {_cat_said} cat)",
      _changed > N // 4 and _fire_said > 20 and _cat_said > 5, f"{_changed}/{_fire_said}/{_cat_said}")

# ───────────────────────────────────────────────────────────────────────────────────────────────────────
print("[3] the fire is said by nearness; out stays pooled; a stale renderer clause is not taken")
POOLED = ("the fire burning warm in the grate", "embers low and red, the warmth pulled close to the hearth")
_bad = _ok_b = _ok_e = 0
for on, meta, off in _lines:
    if meta["fire"] == "burning":
        _ok_b += 1
        _bad += (POOLED[0] in on) or not re.search(r"the fire is [^;.]*", on)
    elif meta["fire"] == "embers":
        _ok_e += 1
        _bad += (POOLED[1] in on) or not re.search(r"the embers are [^;.]*", on)
    else:
        _bad += ("the grate cold and swept" not in on) or on != off.replace(_POOL_CAT, _POOL_CAT) and "the fire" in on
check(f"burning ({_ok_b}) / embers ({_ok_e}) / out lines: nearness clause in, pooled firetxt out; out keeps the cold grate", _bad == 0, str(_bad))
check("the fire clause sits where the pooled one did: 'beyond the window; the fire is ...'",
      all("beyond the window; the fire is" in on or "beyond the window; the embers are" in on
          for on, m, _ in _lines if m["fire"] in ("burning", "embers")))
check("fire out line is byte-identical to the flag-off line apart from the cat clause",
      all(re.sub(r"The cat is [^.]*\.", "", on) == re.sub(re.escape(_POOL_CAT), "", off) or on == off or "The cat is" in on
          for on, m, off in _lines if m["fire"] == "out"))
# stale file: the live state says embers, the renderer's file still says burning
world(fire="burning")
pin(S, "embers", "steady rain", False)
standpoint("at_the_hearth" if "at_the_hearth" in SPS else SPS[0])
PRESENCE.update(line="", plain=False)
_s = S.scene_line()
check("renderer says burning but the live state is embers: the pooled embers line stands, no fire clause taken",
      POOLED[1] in _s and "the fire is" not in _s, _s)

# ───────────────────────────────────────────────────────────────────────────────────────────────────────
print("[4] the cat: plain line replaced; held silent; event / body / hurt / nameless / lap keep their own words")


def scene_with(plain, line, act="sleeping", cat_loc="windowsill", phase="companion", fire="burning", sp=None):
    world(fire=fire, cat_loc=cat_loc, cat_phase=phase, cat_act=act)
    pin(S, fire, "steady rain", False)
    standpoint(sp or SPS[0])
    PRESENCE.update(line=line, plain=plain)
    random.seed(1)
    return S.scene_line()


s_plain = scene_with(True, _POOL_CAT)
check("plain ordinary line -> 'The cat is ...' by nearness, the pooled cat line gone",
      re.search(r"The cat is [^.]*\.", s_plain) and _POOL_CAT not in s_plain, s_plain)
check("the nearness cat clause is the renderer's (place + a distance word + a sector)",
      re.search(r"The cat is on the windowsill, (near|right beside you|across the room|at the far side), "
                r"(ahead|to your right|to your left|behind you)", s_plain) is not None, s_plain)
for act in ("sleeping", "dozing", "washing", "watching"):
    check(f"activity {act}: plain line replaced", "The cat is" in scene_with(True, _POOL_CAT, act=act))
for act in ("live_mouse", "storm_hide", "demanding_food", "drinking", "prowling", "gift_rat"):
    s = scene_with(True, _POOL_CAT, act=act)
    check(f"activity {act}: an event/arc state keeps the pooled line", _POOL_CAT in s and "The cat is" not in s, s)
s = scene_with(False, _POOL_CAT)
check("a line the observer says is NOT plain (body line / hurt / damp coat / nameless / greeting / blink) keeps its words",
      _POOL_CAT in s and "The cat is" not in s, s)
s = scene_with(True, "")
check("a held ask (presence_line returned '') stays silent: no pooled line, no nearness cat clause",
      _POOL_CAT not in s and "The cat is" not in s, s)
s = scene_with(True, _POOL_CAT, cat_loc="on_your_lap")
check("cat on the lap: the renderer's lap clause is never taken, her own lap line stands",
      _POOL_CAT in s and "The cat is on your lap" not in s, s)
s = scene_with(True, _POOL_CAT, phase="wild")
check("cat phase wild/absent: not replaced", _POOL_CAT in s and "The cat is" not in s, s)
CAT.distant_line = lambda loc: _DISTANT
s = scene_with(True, _POOL_CAT)
check("the OTHER cat's distant line is untouched and still follows", s.endswith(_DISTANT) or _DISTANT in s, s)
CAT.distant_line = lambda loc: ""
# nearness actually varies with where she is
_near = {}
for sp in SPS:
    s = scene_with(True, _POOL_CAT, cat_loc="under_desk", sp=sp, fire="out")
    m = re.search(r"The cat is under the desk, ([^,]*), ", s)
    if m:
        _near[sp] = m.group(1)
check(f"the distance word really depends on the standpoint ({sorted(set(_near.values()))})", len(set(_near.values())) >= 2, str(_near))

# ───────────────────────────────────────────────────────────────────────────────────────────────────────
print("[5] no readout: no digit, band name or gauge word in either new clause (D-0434)")
_clauses = []
for on, meta, off in _lines:
    for m in re.finditer(r"; (the (?:fire|embers) are [^;.]*)", on):
        _clauses.append(m.group(1))
    for m in re.finditer(r"(The cat is [^.]*)\.", on):
        _clauses.append(m.group(1))
check(f"{len(_clauses)} new clauses collected", len(_clauses) > 50, str(len(_clauses)))
check("no digit in any new clause", not any(re.search(r"\d", c) for c in _clauses))
_BANNED = {"close", "mid", "faint", "band", "share", "gauge", "reach", "warmth_share", "hearth_dist", "metre", "metres", "m"}
_toks = [set(re.findall(r"[a-z_]+", c.lower())) for c in _clauses]       # whole words: 'faintly' / 'reaching' are prose, not gauges
_hits = sorted(set().union(*_toks) & _BANNED)
check("no band / gauge / measurement word in any new clause " + str(_hits), not _hits)
check("the helper refuses a clause that carries a digit",
      (lambda: (setattr(SPT, "render", lambda *a, **k: {"standpoint": "x", "line": "", "clauses": ["the fire is near, 2 m off — its heat"]}),
                S._study_depth_clauses("burning"))[1])() == ("", ""))
SPT.render = _counting_render

# ───────────────────────────────────────────────────────────────────────────────────────────────────────
print("[6] scope: the study helper is reached only for the study")
_called = []
_real_helper = S._study_depth_clauses
S._study_depth_clauses = lambda fire: (_called.append(fire), _real_helper(fire))[1]
for loc in ("garden", "shore", "wood"):
    world()
    pin(S, "burning", "steady rain", False)
    S.state["location"] = loc
    for _n in ("_garden_scene_line", "_shore_scene_line", "_wood_scene_line"):
        pass
    try:
        S.scene_line()
    except Exception:
        pass
check("garden/shore/wood scene_line() never called the study helper", _called == [], str(_called))
S._study_depth_clauses = _real_helper

# ───────────────────────────────────────────────────────────────────────────────────────────────────────
print("[7] fail-open and the non-live fence")
world()
pin(S, "burning", "steady rain", False)
standpoint(SPS[0])
PRESENCE.update(line=_POOL_CAT, plain=True)


def _boom(*a, **k):
    raise RuntimeError("renderer exploded")


SPT.render = _boom
random.seed(3)
_a = S.scene_line()
SPT.SPATIAL_DEPTH_LIVE = False
SPT.render = _real_render
pin(S, "burning", "steady rain", False)
random.seed(3)
_b = S.scene_line()
check("a raising renderer leaves the pooled line exactly as flag off", _a == _b and "the fire burning warm in the grate" in _a, _a)


def _fence(*a, **k):
    raise profile.NonLiveWriteError("fenced")


SPT.SPATIAL_DEPTH_LIVE = True
SPT.render = _fence
try:
    _helper = S._study_depth_clauses("burning")
    _reraised = False
except profile.NonLiveWriteError:
    _reraised = True
check("the helper re-raises the non-live fence (like every neighbour in scene_line)", _reraised)
SPT.render = _real_render
SPT.SPATIAL_SCENE, _ss = False, SPT.SPATIAL_SCENE
check("SPATIAL_SCENE off also switches the study depth off", S._study_depth_clauses("burning") == ("", ""))
SPT.SPATIAL_SCENE = _ss

# ───────────────────────────────────────────────────────────────────────────────────────────────────────
print("[8] cat.py observer: _LAST_PRESENCE_PLAIN")
import inspect                                                    # noqa: E402
_rand = random.random


def ordinary(**st):
    base = {"phase": "companion", "location": "by_the_fire", "activity": "sleeping", "bond": 0.5, "name": "Mo",
            "body": {"warmth": 0.5}, "fur_moisture": 0.0}
    base.update(st)
    CAT.state = dict(base)
    CAT._LAST_PRESENCE_PLAIN = True
    line = CAT._ordinary_line("study", base["location"], base["activity"], "by_the_fire", base["phase"], "")
    return line, CAT._LAST_PRESENCE_PLAIN


random.seed(2)
_l, _p = ordinary()
check("plain ordinary line (named cat, dry coat, no hurt, no body trigger): plain stays True", _p is True and _l, f"{_l!r} {_p}")
random.seed(2)
_l, _p = ordinary(fur_moisture=0.5)
check("a damp coat rides the line: plain False and the sentence is there", _p is False and "damp" in _l, f"{_l!r}")
random.seed(2)
_l, _p = ordinary(activity="drinking", location="garden")
check("a body line (drinking at the water) is not plain", _p is False, f"{_l!r}")
_found = False
for sd in range(200):
    random.seed(sd)
    _l, _p = ordinary(name=None, phase="kept", name_invited=True)
    if "name" in _l.lower() and "no name" in _l.lower() or "nameless" in _l.lower() or "without a name" in _l.lower():
        _found = (_p is False)
        break
check("a nameless note rides the line: plain False", _found)
# harm clause: stub cat_harm.clause
try:
    from core import cat_harm as _CH
    _orig_clause = _CH.clause
    _CH.clause = lambda state: "She favours a foreleg."
    random.seed(2)
    _l, _p = ordinary()
    check("a hurt she carries rides the line: plain False", _p is False and "favours" in _l, f"{_l!r}")
    _CH.clause = _orig_clause
except Exception as e:
    check("cat_harm importable for the harm check", False, str(e))
_src = inspect.getsource(_REAL_PRESENCE)
check("presence_line() resets the observer on entry", "_LAST_PRESENCE_PLAIN = False" in _src.split("_load()")[0])
check("presence_line() sets it True only at the ordinary tail (after the dosed gate)",
      _src.index("_LAST_PRESENCE_PLAIN = True") > _src.index("if not _g.get(\"ride\")"))

# ───────────────────────────────────────────────────────────────────────────────────────────────────────
print("[9] the live stores are untouched")
for p in _WATCH:
    after = _snap(p)
    if p.suffix == ".jsonl" and after is not None and _before[p] is not None:
        # live Du appends to these while it is up: what matters is that nothing already there was rewritten or truncated
        check(f"{p.name}: existing bytes intact (append-only; live Du may have grown it: {_before[p][0]} -> {after[0]})",
              after[0] >= _before[p][0] and _prefix_md5(p, _before[p][0]) == _before[p][2])
    else:
        check(f"{p.name}: unchanged ({'absent' if after is None else f'{after[0]} bytes'})", after == _before[p])
for _mod, _attr in ((SPT, "_SHADOW"), (SPT, "_DEPTH_SHADOW")):
    check(f"{_mod.__name__}.{_attr} resolves inside this worktree, not the live tree",
          Path(getattr(_mod, _attr)).resolve().is_relative_to(ROOT.resolve()))

print("\nFAILS =", FAILS)
print("ALL OK" if FAILS == 0 else "SOME CHECKS FAILED")
sys.exit(1 if FAILS else 0)
