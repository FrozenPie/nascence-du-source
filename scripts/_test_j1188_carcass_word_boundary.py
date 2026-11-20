"""
Regression: J-0887's carcass gate matches its dead-thing words by WHOLE WORD, not substring (F-1669/J-1188).

THE BUG. core/life.py look_answer's carcass gate and core/life_traces.py's dead_trace_look/carcass_look all
tested `any(w in text for w in _CARCASS_WORDS)` -- plain substring. So "the deadfall" ("dead" inside
"deadfall"), "the cuttlebones" ("bones" inside "cuttlebones"), and "nobody" ("body" inside "nobody") were
wrongly diverted into the carcass path and answered "There is no body here -- nothing of the kind you can
find." even though the wood/shore/garden each has a real, unrelated, lookable thing under that name.

THE FIX, THREE PARTS.
  (A) core/life_traces.word_present(words, text): the same word/phrase-boundary rule life._match and
      J-1165's trace-object gate already use ((?<![a-z-])word(?![a-z-]); a hyphen ends a word too),
      applied to the FULL entry (so a two-word phrase like "the kill" cannot match inside "the killer
      whale" either -- the lookahead right after "kill" fails on the following "e"). Used at all three
      substring-test call sites (core/life.py look_answer's gate; life_traces.carcass_look;
      life_traces.dead_trace_look).
  (B) Whole-word ALONE does not close "the dead wood" / "the fallen dead wood": "dead" really is a
      standalone word there, and the wood's own "deadfall" object is literally aliased "dead wood"
      (core/world_content_wood.py). A NEW life_traces.is_place_object_target(target, place) -- derived
      from core.world_detail's own place-content registry, the same discipline is_plant_target already
      uses for garden.CATALOGUE -- lets a real, non-carcass place object whose OWN alias also carries a
      carcass word fall through to its own look. Checked only as the LAST resort in look_answer's carcass
      block, after carcass_look/dead_trace_look have both already found nothing real, so an actual active
      carcass or trace always wins the tie.
  (C) A regression THIS FIX'S OWN differential caught, not assumed safe: a bare world_detail match is too
      wide -- garden's ambient "birds" content object is aliased plain "bird", so "the dead bird" would
      otherwise fall through to a pool describing LIVE birds, a wrong answer worse than the honest "no
      body" line it replaced. is_place_object_target therefore requires the MATCHED ALIAS ITSELF to carry
      a carcass word (as "dead wood" does for deadfall) -- not merely that Du's own "dead X" phrasing
      coincidentally overlaps some unrelated object's ordinary noun.

  [0] module resolution + isolation set-up
  [1] the SIX named false positives (F-1669's own evidence) now fall through ('') to the place's own look
  [2] true carcass phrasings: word_present still matches every _CARCASS_WORDS entry, unchanged
  [3] is_place_object_target: derived correctly (deadfall-family YES, ambient "birds"/"gulls" pools NO);
      the "the dead bird" regression this job's own differential found is pinned down as a hard assertion
  [4] in-process differential A: OLD (substring) vs NEW (word_present) over the whole observe_inventory
      corpus + every real historical hands_trace/life_events look target -- must show ONLY word-boundary
      corrections, all in the false-positive direction
  [5] in-process differential B: is_place_object_target forced OFF vs live (full look_answer pipeline),
      same broad corpus -- must show ONLY the deadfall-family targets change, nothing else (this is the
      section that would have caught "the dead bird" before it ever shipped)
  [6] REAL rows replayed read-only: data/hands_trace.jsonl's own carcass-word-substring rows through the
      live gate (F-1669's own frequency read: exactly one, 'the tide sorting cuttlebones')
  [7] isolation: audit hook (no write attempt under any data/), live-file hashes

ISOLATION. Same convention as scripts/_test_j1165_trace_object_look.py / scripts/life_smoke.py: every
store look_answer/traces_pass can reach is redirected into a temp dir before anything can write; a Python
audit hook records any attempt by THIS process to open-for-write/rename/remove anything under
C:\\Nascence\\data or <root>\\data (a hash comparison alone cannot prove a negative while Du is online and
legitimately writing on his own). Sections [4]-[6] only ever READ the live corpus files.

  python scripts/_test_j1188_carcass_word_boundary.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1188_carcass_word_boundary_"))
print("isolated store dir:", TMP)
MARKER = f"j1188_marker_{os.getpid()}"
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
from core import life, life_traces as LT, world_traces as WT, world_detail as WD   # noqa: E402
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


def quiet(cond: bool, label: str, sink: list) -> None:
    global FAILS, CHECKS
    CHECKS += 1
    if not cond:
        FAILS += 1
        sink.append(label)


def at(month: int, hour: int, day: int = 15, year: int = 2026) -> float:
    return time.mktime((year, month, day, hour, 0, 0, 0, 0, -1))


# ── [0] module resolution ────────────────────────────────────────────────────────────────────────
print("\n[0] module resolution: the code under test is THIS root's, not the shared tree's")
print("    sys.path[0] =", sys.path[0])
for _m in (core, profile, life, LT, WT, WD, life_birds, life_mammals, garden_insects, garden_soil, S, LOC, SK):
    _f = getattr(_m, "__file__", None)
    print(f"    {_m.__name__:22s} -> {_f}")
    check(_f is not None and Path(_f).resolve().is_relative_to(ROOT), f"{_m.__name__} loaded from inside {ROOT}")
check(hasattr(LT, "word_present") and hasattr(LT, "is_place_object_target"),
      "the loaded copy carries the J-1188 fix (word_present + is_place_object_target)")
for _m, _a in _REDIRECTS:
    check(TMP in Path(str(getattr(_m, _a))).parents, f"{_m.__name__}.{_a} redirected into the temp dir")

# ── [1] the six named false positives now fall through ──────────────────────────────────────────────
print("\n[1] F-1669's own six false-positive phrasings now fall through to the place's own look ('')")
FALSE_POS = [
    ("the deadfall", "wood"), ("the dead wood", "wood"), ("the fallen dead wood", "wood"),
    ("the cuttlebones", "shore"), ("the tide sorting cuttlebones", "shore"), ("nobody", "garden"),
]
for target, place in FALSE_POS:
    ans = life.look_answer(target, place, at(9, 12))
    check(ans == "", f"{target!r} @ {place}: look_answer == '' (falls through) -- got {ans!r}")

# ── [2] true carcass phrasings: word_present unchanged ───────────────────────────────────────────────
print("\n[2] true carcass phrasings (no carcass/trace present, so the honest no-body/no-dead-X line) --")
print("    word_present must still fire on every real _CARCASS_WORDS entry, exactly as substring did")
TRUE_CARCASS = ["the dead gannet", "the body", "the bones", "the skull", "feathers and bone", "the kill",
                "a corpse", "the carcass", "the carcase", "the skeleton", "the remains", "a dead mouse",
                "the dead thing"]
for t in TRUE_CARCASS:
    check(LT.word_present(LT._CARCASS_WORDS, t.lower()), f"word_present fires on {t!r}")
    ans = life.look_answer(t, "garden", at(9, 12))
    check(ans.startswith("There is no"), f"{t!r} @ garden (no carcass/trace there): honest no-body line, got {ans!r}")
check(not LT.word_present(LT._CARCASS_WORDS, "the killer whale dives"),
      "'the kill' does not falsely match inside 'the killer whale' (phrase boundary, not just per-word)")
check(not LT.word_present(LT._CARCASS_WORDS, "an embodied thought"), "'body' does not match inside 'embodied'")
check(not LT.word_present(LT._CARCASS_WORDS, "the deadline looms"), "'dead' does not match inside 'deadline'")

# ── [3] is_place_object_target: derived correctly, and the "dead bird" regression pinned down ────────
print("\n[3] is_place_object_target: the deadfall family YES (own alias carries 'dead'/'dead wood'),")
print("    an ambient live-creature pool sharing an ordinary noun NO (this job's own differential catch)")
check(LT.is_place_object_target("the deadfall", "wood"), "'the deadfall' is a real wood place-object")
check(LT.is_place_object_target("the dead wood", "wood"), "'the dead wood' (deadfall's own alias) is a real wood place-object")
check(LT.is_place_object_target("the fallen dead wood", "wood"), "'the fallen dead wood' is a real wood place-object")
check(not LT.is_place_object_target("the dead wood", "garden"), "'the dead wood' is NOT a garden place-object (wrong place)")
check(not LT.is_place_object_target("the dead bird", "garden"),
      "REGRESSION GUARD: 'the dead bird' does NOT match garden's ambient 'birds' pool (alias 'bird' carries no carcass word)")
check(not LT.is_place_object_target("the dead gull", "shore"),
      "REGRESSION GUARD: 'the dead gull' does NOT match shore's ambient 'birds' pool ('gulls' alias carries no carcass word)")
check(life.look_answer("the dead bird", "garden", at(9, 12)) == "There is no body here — nothing of the kind you can find.",
      "end-to-end: 'the dead bird' @ garden still gets the honest no-body line, not the live-birds ambient pool")
check(not LT.word_present(LT._CARCASS_WORDS, "the wood pigeon"), "sanity: 'the wood pigeon' itself carries no carcass word (would never even reach the gate)")

# ── [4] in-process differential A: OLD substring vs NEW word_present, whole real corpus ───────────────
print("\n[4] DIFFERENTIAL A -- OLD (substring) vs NEW (word_present) over the whole real corpus")
_OLD_NOUNS = tuple(w for w in LT._CARCASS_WORDS if w != "dead")


def old_carcass_match(text: str) -> bool:
    """Frozen exactly as core/life.py's gate (and life_traces's own two sites) read before this fix:
    plain substring `in`, no word boundary."""
    return any(w in text for w in LT._CARCASS_WORDS)


def load_corpus() -> list:
    out = set(t for t, _p in FALSE_POS)    # F-1669's own six named phrasings, explicit (none has a live
                                            # trace row today, so the real-history sources below would
                                            # otherwise never exercise them at all)
    inv = json.loads((ROOT / "docs" / "reviews" / "observe_inventory_2026-09-02.json").read_text(encoding="utf-8"))
    for cat, d in inv.items():
        out.update(d.keys())
    le = _LIVE_DATA / "life_events.jsonl"
    if le.exists():
        with open(le, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("kind") in ("would_answer", "answer") and d.get("target"):
                    out.add(d["target"])
    ht = _LIVE_DATA / "hands_trace.jsonl"
    if ht.exists():
        with open(ht, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("act_kind") == "observe" and d.get("act_object"):
                    out.add(d["act_object"])
    return sorted(out)


CORPUS = load_corpus()
print(f"    corpus: {len(CORPUS)} distinct phrasings (observe_inventory + real life_events targets + real hands_trace observe objects)")
flips_a = []
for t in CORPUS:
    tl = t.lower()
    old, new = old_carcass_match(tl), LT.word_present(LT._CARCASS_WORDS, tl)
    if old != new:
        flips_a.append((t, old, new))
print(f"    flips: {len(flips_a)}")
check(len(flips_a) > 0, "at least one real flip found (the fix does something observable on this corpus)")
all_false_positive_direction = all(old and not new for _, old, new in flips_a)
check(all_false_positive_direction, "EVERY flip is old=True/new=False (a false-positive correction), none the other way "
                                     f"(violations: {[f for f in flips_a if not (f[1] and not f[2])][:5]})")
for t, old, new in flips_a[:20]:
    print(f"      {t!r:45s} old={old} new={new}")

# ── [5] in-process differential B: is_place_object_target forced OFF vs live, full pipeline ───────────
print("\n[5] DIFFERENTIAL B -- is_place_object_target forced OFF vs LIVE, over the same corpus x 4 places,")
print("    full look_answer() pipeline -- must show ONLY the deadfall-family targets change")
_real_ipot = LT.is_place_object_target
PLACES = ("study", "garden", "shore", "wood")
flips_b = []
import copy as _copy
import random as _random
for t in CORPUS:
    for place in PLACES:
        seed = (hash((t, place)) % 96821) + 1     # same seed for OFF and ON -- isolates the ONE variable
        saved_state = _copy.deepcopy(life._state)
        LT.is_place_object_target = lambda *_a, **_k: False
        _random.seed(seed)
        off = life.look_answer(t, place, at(9, 12))
        life._state = _copy.deepcopy(saved_state)   # undo any side effect (noticed flags, sightings, ...)
        LT.is_place_object_target = _real_ipot
        _random.seed(seed)
        on = life.look_answer(t, place, at(9, 12))
        life._state = saved_state
        if off != on:
            flips_b.append((t, place, off, on))
LT.is_place_object_target = _real_ipot
print(f"    flips: {len(flips_b)}")
unexpected_b = [f for f in flips_b if not (f[2].startswith("There is no") and f[3] == "")]
check(len(unexpected_b) == 0, f"every flip is honest-no-body-line -> '' (falls through); "
                               f"{len(unexpected_b)} unexpected (first 5: {unexpected_b[:5]})")
for t, place, off, on in flips_b[:20]:
    print(f"      {t!r:35s}@{place:7s}  OFF={off[:45]!r:48s} ON={on!r}")
check(not any(t == "the dead bird" for t, *_ in flips_b), "REGRESSION GUARD reconfirmed: 'the dead bird' never appears in the mechanism-D flip set")

# ── [6] real rows replayed read-only ────────────────────────────────────────────────────────────────
print("\n[6] REAL data/hands_trace.jsonl rows through the live word_present gate (F-1669's own frequency:")
print("    exactly one substring-only carcass-word match in the whole file, 'the tide sorting cuttlebones')")
ht_hits_old, ht_hits_new = [], []
ht_path = _LIVE_DATA / "hands_trace.jsonl"
n_rows = 0
with open(ht_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        n_rows += 1
        if d.get("act_kind") != "observe" or not d.get("act_object"):
            continue
        obj = d["act_object"].lower()
        if old_carcass_match(obj):
            ht_hits_old.append(d["act_object"])
        if LT.word_present(LT._CARCASS_WORDS, obj):
            ht_hits_new.append(d["act_object"])
print(f"    {n_rows} rows read whole (no tail-sampling); OLD substring hits: {len(ht_hits_old)} {sorted(set(ht_hits_old))}")
print(f"                                                   NEW word_present hits: {len(ht_hits_new)} {sorted(set(ht_hits_new))}")
check(len(ht_hits_old) >= len(ht_hits_new), "NEW never finds MORE substring-style hits than OLD (whole-word only narrows)")

# ── [7] isolation ────────────────────────────────────────────────────────────────────────────────────
print("\n[7] isolation: audit hook, live-file hashes, py_compile")
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
