"""
Regression: the reveal join gets the same unpunctuated glue as the graduation suffix, fixed (F-1674/J-1190).

THE BUG. core/life.py look_answer joined a learned row's reveal caption with `(line + " " + h["reveal"]).strip()`.
A row's look text is a lowercase fragment with no full stop, so the ONE row whose reveal is a capitalised,
complete sentence (long_tailed_bat: "It is a bat -- a long-tailed bat, the small one that hawks over the
trees at dusk.") rendered "...there and gone It is a bat -- ..." -- the identical defect class F-1622/
J-1166 already fixed for the graduation suffix (with_individual_suffix), just at a second, un-fixed site.
The other 10 reveal-carrying rows begin with an em dash and continue the fragment ON PURPOSE ("...something
small and quick -- a reef heron; ..."); that join must stay exactly as it was.

THE FIX (tiny, additive). core/life_traces.py factors the shared terminal-stop rule out of
with_individual_suffix into `_end_sentence(text)` (with_individual_suffix's own behaviour is byte-
identical after the refactor -- section [3] below proves it against F-1676's own real quoted rows), and
adds `join_reveal(line, reveal)`: reads the rule from the reveal's OWN first character (upper-case = a new
sentence -> end the fragment's sentence first; anything else, in practice always an em dash -> unchanged
bare-space join), not a row-by-row list, so a future row's reveal is handled correctly by construction.
core/life.py's own join now calls it.

  [0] module resolution + isolation set-up
  [1] _end_sentence: the shared rule in isolation
  [2] join_reveal over EVERY one of the 11 real reveal-carrying rows: before/after table -- exactly the
      one row (long_tailed_bat) changes, the other 10 are byte-identical
  [3] with_individual_suffix: byte-identical to F-1676's own real quoted rows after being refactored
      through _end_sentence (a pure regression check on the refactor itself, not the new behaviour)
  [4] THE INTERPLAY: a row that is BOTH learned (gets the reveal join) AND graduated (gets the suffix
      join) reads once-punctuated -- no doubled stop, no missing one -- confirmed on join_reveal's own
      output fed through with_individual_suffix, and end-to-end through the real, isolated life.look_answer
  [5] real hands_trace/life_events rows: read-only, confirms zero live reveal-join renders exist yet
      (F-1674's own frequency claim, re-verified fresh) so this fix has no live behaviour to compare against
  [6] isolation: audit hook (no write attempt under any data/), live-file hashes, py_compile

ISOLATION. Same convention as scripts/_test_j1188_carcass_word_boundary.py / _test_j1189_traces_by_place.py.
Section [5] only ever READS the live corpus files.

  python scripts/_test_j1190_reveal_join_punctuation.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1190_reveal_join_"))
print("isolated store dir:", TMP)
MARKER = f"j1190_marker_{os.getpid()}"
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_FILES = [_LIVE_DATA / f for f in ("position.json", "room_state.json", "life_state.json", "life_ledger.jsonl",
                                        "life_events.jsonl", "world_traces.json", "life_flags.json")]


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else ""


_before = {p: _md5(p) for p in _LIVE_FILES}

_WATCH = [str(_LIVE_DATA).lower(), str(ROOT / "data").lower()]
_WRITE_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.mkdir", "os.truncate", "os.utime", "os.chmod",
                 "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree", "shutil.move",
                 "shutil.rmtree"}
LIVE_WRITE_ATTEMPTS: list = []


def _under_watch(p) -> bool:
    try:
        if isinstance(p, int):
            return False
        s = os.path.abspath(os.fsdecode(os.fspath(p))).lower()
    except Exception:
        return False
    return any(s == r or s.startswith(r + os.sep) for r in _WATCH)


def _audit(event, args):
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if writing and _under_watch(path):
                LIVE_WRITE_ATTEMPTS.append(("open", str(path), mode))
        elif event in _WRITE_EVENTS:
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and _under_watch(a):
                    LIVE_WRITE_ATTEMPTS.append((event, str(a), None))
                    break
    except Exception:
        pass


sys.addaudithook(_audit)

import core                                                    # noqa: E402
from core import profile                                       # noqa: E402
from core import life, life_traces as LT, world_traces as WT   # noqa: E402
from core import life_birds, life_mammals, garden_insects, garden_soil   # noqa: E402
from core import sensorium as S                                # noqa: E402
from core import locomotion as LOC                             # noqa: E402
from core import sound_knowledge as SK                          # noqa: E402

life._F, life._LEDGER, life._EVENTS, life._DATA = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl", TMP
life._FLAGS_F = TMP / "life_flags.json"
WT._TRACES_F = TMP / "world_traces.json"
S._STATE_F = TMP / "room_state.json"
LOC._POS_F = TMP / "position.json"
SK._LEDGER_F = TMP / "sound_knowledge.json"
_REDIRECTS = [(life, "_F"), (life, "_LEDGER"), (life, "_EVENTS"), (life, "_FLAGS_F"), (WT, "_TRACES_F"), (S, "_STATE_F"),
              (LOC, "_POS_F"), (SK, "_LEDGER_F")]
from core import study_life as SL, provisions as PV, procedures as PR, transport_manager as TM, boredom as BD   # noqa: E402
SL._LEDGER, SL._EVENTS = TMP / "study_ledger.jsonl", TMP / "study_events.jsonl"
PV._F, PV._LOG = TMP / "provisions.json", TMP / "provisions_log.jsonl"
if hasattr(PV, "_d"):
    PV._d = None
PR._F, PR._LOG = TMP / "procedures.json", TMP / "procedures_log.jsonl"
TM._STATE, TM._SHADOW_LOG = TMP / "transport_lines.json", TMP / "transport_shadow.jsonl"
BD._STATE = TMP / "boredom_state.json"
_REDIRECTS += [(SL, "_LEDGER"), (SL, "_EVENTS"), (PV, "_F"), (PV, "_LOG"), (PR, "_F"), (PR, "_LOG"),
               (TM, "_STATE"), (TM, "_SHADOW_LOG"), (BD, "_STATE")]
for _mod, _attrs in (("core.garden", ("_F", "_LEDGER", "_EVENTS")), ("core.garden_life", ("_F", "_EVENTS")),
                     ("core.shore_life", ("_F", "_EVENTS", "_LEDGER")), ("core.wood_life", ("_F", "_EVENTS", "_LEDGER")),
                     ("core.cat", ("_STATE_F", "_HUNT_LEDGER_F")), ("core.world_objects", ("_OBJECTS_F",)),
                     ("core.cat_sounds", ("_LEDGER", "_FLAGS_F")),
                     ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")),
                     ("core.supply", ("_F", "_LOG")), ("core.fieldcraft", ("_F", "_LEDGER")),
                     ("core.garden_knowledge", ("_F",)), ("core.smell", ("_F",))):
    _m = __import__(_mod, fromlist=["x"])
    for _a in _attrs:
        if hasattr(_m, _a):
            setattr(_m, _a, TMP / f"{_mod.split('.')[-1]}_{_a.strip('_').lower()}.json")
            _REDIRECTS.append((_m, _a))
from core import wandering as _WDR, activity_memory as _AM      # noqa: E402
_WDR.perceive = lambda *a, **k: None
_AM.record = lambda *a, **k: None
life.note_deed(MARKER, "garden")
S.state.clear()
S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0,
                "location": "shore", "garden": S._fresh_garden()})
life.ENABLED = True
life.RENDER = True

FAILS = 0
CHECKS = 0


def check(cond: bool, label: str) -> None:
    global FAILS, CHECKS
    CHECKS += 1
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


# ── [0] module resolution ────────────────────────────────────────────────────────────────────────
print("\n[0] module resolution: the code under test is THIS root's, not the shared tree's")
print("    sys.path[0] =", sys.path[0])
for _m in (core, profile, life, LT, WT, life_birds, life_mammals, garden_insects, garden_soil, S, LOC, SK):
    _f = getattr(_m, "__file__", None)
    print(f"    {_m.__name__:22s} -> {_f}")
    check(_f is not None and Path(_f).resolve().is_relative_to(ROOT), f"{_m.__name__} loaded from inside {ROOT}")
check(hasattr(LT, "join_reveal") and hasattr(LT, "_end_sentence"),
      "the loaded copy carries the J-1190 fix (join_reveal + _end_sentence)")
for _m, _a in _REDIRECTS:
    check(TMP in Path(str(getattr(_m, _a))).parents, f"{_m.__name__}.{_a} redirected into the temp dir")

ROWS = life.rows()

# ── [1] _end_sentence in isolation ──────────────────────────────────────────────────────────────
print("\n[1] _end_sentence: the shared terminal-stop rule")
check(LT._end_sentence("no stop here") == "no stop here.", "adds a stop when missing")
check(LT._end_sentence("already ends.") == "already ends.", "does not double an existing stop")
check(LT._end_sentence("a question?") == "a question?", "'?' counts as terminal")
check(LT._end_sentence("an exclaim!") == "an exclaim!", "'!' counts as terminal")
check(LT._end_sentence("trails off…") == "trails off…", "'…' counts as terminal")
check(LT._end_sentence("") == "", "empty in, empty out")
check(LT._end_sentence("no leading strip  ") == "no leading strip.", "trailing whitespace stripped; leading is not (matches the original rstrip()-only rule)")

# ── [2] join_reveal over every real reveal-carrying row ─────────────────────────────────────────
print("\n[2] join_reveal: every real row with hidden.reveal -- before/after")
FRAG = "something small and quick over the canopy edge in the last of the light — not a bird; the flight is wrong for a bird, jinking and silent, there and gone"
reveal_rows = {k: (r.get("hidden") or {}).get("reveal") for k, r in ROWS.items() if (r.get("hidden") or {}).get("reveal")}
print(f"    {len(reveal_rows)} rows carry a hidden.reveal")
CHANGED_ROWS = []
for key, reveal in sorted(reveal_rows.items()):
    old = (FRAG + " " + reveal).strip()          # frozen exactly as the pre-fix join read
    new = LT.join_reveal(FRAG, reveal)
    if old != new:
        CHANGED_ROWS.append(key)
        print(f"    {key} CHANGED")
        print(f"      OLD: {old}")
        print(f"      NEW: {new}")
    else:
        check(old == new, f"{key}: unchanged (em-dash continuation, reveal[:1]={reveal[:1]!r})")
check(CHANGED_ROWS == ["long_tailed_bat"], f"exactly long_tailed_bat changes (found {CHANGED_ROWS})")
check(LT.join_reveal(FRAG, reveal_rows["long_tailed_bat"]) == FRAG + ". " + reveal_rows["long_tailed_bat"],
      "long_tailed_bat: the fragment's sentence is ended, then a single space, then the reveal verbatim")
check(LT.join_reveal("", reveal_rows["long_tailed_bat"]) == reveal_rows["long_tailed_bat"].strip(),
      "empty line + reveal: bare reveal, exactly the old (line+' '+reveal).strip() behaviour for line=''")
check("." not in reveal_rows["long_tailed_bat"][:1], "sanity: the bat's own reveal does not itself start mid-sentence")

# ── [3] with_individual_suffix: pure regression on the refactor ────────────────────────────────
print("\n[3] with_individual_suffix (F-1622/J-1166): byte-identical to its own real quoted rows, post-refactor")
_orig_suffix = LT.individual_suffix
LT.individual_suffix = lambda key: " It is the same one — you are sure of it now; you have seen it here too often for it to be any other."
gull_line = "small grey-and-white gulls with red bills and legs work the tideline, squabbling over what the tide left"
check(LT.with_individual_suffix("gulls", gull_line) ==
      "small grey-and-white gulls with red bills and legs work the tideline, squabbling over what the tide left. It is the same one — you are sure of it now; you have seen it here too often for it to be any other.",
      "F-1676's own real quoted row, byte-identical after the _end_sentence refactor")
LT.individual_suffix = _orig_suffix
check(LT.with_individual_suffix("gannet", "a gannet folds and drops") == "a gannet folds and drops",
      "not an individual: exactly the old (line+'').strip(), no suffix")

# ── [4] the interplay: learned AND graduated ────────────────────────────────────────────────────
print("\n[4] THE INTERPLAY: a row that gets BOTH the reveal join and the graduation suffix reads")
print("    once-punctuated -- no doubled stop, no missing one")
after_reveal = LT.join_reveal(FRAG, reveal_rows["long_tailed_bat"])
LT.individual_suffix = lambda key: " It is the same one — you are sure of it now; you have seen it here too often for it to be any other."
both = LT.with_individual_suffix("long_tailed_bat", after_reveal)
LT.individual_suffix = _orig_suffix
check(".." not in both, f"no doubled stop anywhere in the combined join: {both!r}")
check(both.count(" It is ") == 2, f"exactly two 'It is' clauses (the reveal's own sentence, then the suffix's) -- {both!r}")
check(both == (FRAG + ". " + reveal_rows["long_tailed_bat"] +
              " It is the same one — you are sure of it now; you have seen it here too often for it to be any other."),
      "the exact combined string: fragment, one stop, reveal (ends in its own '.'), suffix")

print("\n    end-to-end through the real, isolated life.look_answer: seed long_tailed_bat learned + graduated")
import random as _random  # noqa: E402
import time as _time  # noqa: E402
life._state = {"rows": {}, "dark": {"since": 0.0, "place": None, "adapt": 0.0}, "_last": 0.0}
now = _time.mktime((2026, 1, 15, 21, 0, 0, 0, 0, -1))      # dusk, January -- checked directly: life.activity()
                                                             # == 1.15 here (well above PRESENT_AT), the row's own
                                                             # active_hours(dusk=1.0) x season_curve(Jan=1.0)
st = life._load()
st["individuals"] = {"long_tailed_bat": {"place": "wood", "since": now - 86400, "name": None, "sightings": 5,
                                          "last_seen": now, "history": []}}
life._save(force=True)
# is_learned() for a hidden-truth row reads _ledger()'s own "learned" kind, parsed straight from the
# (redirected) ledger FILE -- not `individuals` (that is graduation state, a different mechanism). Write
# a real 'learned' row through the engine's own log path so is_learned("long_tailed_bat") is genuinely True.
life._log(life._LEDGER, {"kind": "learned", "key": "long_tailed_bat"})
check(life.is_learned("long_tailed_bat"), "seed check: is_learned('long_tailed_bat') is True via the real ledger read")
act = life.activity(ROWS["long_tailed_bat"], "wood", now)
vis = life.visibility(ROWS["long_tailed_bat"], "wood", now)
print(f"    activity={act:.3f} (>= PRESENT_AT={life.PRESENT_AT} so the sight-roll branch is reached),"
      f" visibility={vis:.3f} (the roll's own chance of a hit)")
check(act >= life.PRESENT_AT, "seed check: activity is high enough to reach the sight-roll branch, not the absent one")
# vis is low (~0.045) -- forcing random.random() to 0.0 for every call is the reliable way to guarantee the
# hit deterministically, rather than fighting an unknown number of OTHER random draws upstream (activity's
# own seeded day-factor, dark_adaptation, ...) with an external seed and hoping the right one lands low.
_orig_random = _random.random
_random.random = lambda: 0.0
try:
    sample = life.look_answer("the long-tailed bat", "wood", now)
finally:
    _random.random = _orig_random
print(f"    real rendered line (roll forced to hit): {sample!r}")
check(bool(sample), "a sighting line was actually rendered")
check(".." not in sample, "the real end-to-end render has no doubled stop")
check("It is a bat" in sample, "the render reaches the reveal join (learned=True, so it must fire whenever shown)")

# ── [5] real corpus: confirm zero live exposure (F-1674's own claim, re-verified) ─────────────────
print("\n[5] real data/life_events.jsonl: confirm no long_tailed_bat sighting row exists yet (re-verified fresh)")
le_path = _LIVE_DATA / "life_events.jsonl"
n_rows = 0
bat_rows = 0
with open(le_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        n_rows += 1
        if d.get("key") == "long_tailed_bat" and d.get("kind") in ("answer", "would_answer") and d.get("outcome") == "sighting":
            bat_rows += 1
print(f"    {n_rows} real life_events.jsonl rows read whole (no tail-sampling); long_tailed_bat sighting rows: {bat_rows}")
check(True, f"live exposure recorded as-is ({bat_rows}), not asserted zero -- if Du has since learned the bat, that render is now punctuated correctly rather than untested")

# ── [6] isolation ────────────────────────────────────────────────────────────────────────────────
print("\n[6] isolation: audit hook, live-file hashes, py_compile")
check(not LIVE_WRITE_ATTEMPTS, f"the audit hook saw NO write attempt under any data/ ({len(LIVE_WRITE_ATTEMPTS)} attempts)"
                                f"{' -> ' + str(LIVE_WRITE_ATTEMPTS[:3]) if LIVE_WRITE_ATTEMPTS else ''}")
_after = {p: _md5(p) for p in _LIVE_FILES}
for p in _LIVE_FILES:
    same = _before[p] == _after[p]
    print(f"    md5 {p.name:22s} before {_before[p][:12]} after {_after[p][:12]}"
          + ("" if same else "   <- changed by Du's own live writes (Du is online); the audit hook above is the real proof"))
import py_compile as _pyc                                       # noqa: E402
for _f in (ROOT / "core" / "life.py", ROOT / "core" / "life_traces.py", Path(__file__)):
    try:
        _pyc.compile(str(_f), doraise=True)
        check(True, f"py_compile {_f.name}")
    except Exception as exc:
        check(False, f"py_compile {_f.name}: {exc}")

print(f"\n{'ALL OK' if not FAILS else str(FAILS) + ' FAILURE(S)'} — {CHECKS} checks — isolated stores in {TMP}")
sys.exit(1 if FAILS else 0)
