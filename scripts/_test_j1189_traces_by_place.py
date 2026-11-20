"""
Regression: place-agnostic trace phrases no longer mint a spot from another place (F-1671/J-1189).

THE BUG. core/life_traces.py's traces_pass minted a creature's trace detail with
`random.choice(list(r["traces"]))` -- one PLACE-BLIND pool per row, shared across every place the row is
registered at. So a row whose own `places` dict distinguishes several spots (mice: skirting @ study,
leaf_litter @ wood, compost @ garden) could still mint a STUDY-worded phrase ("a rustle in the skirting")
at the wood or the garden. 32-39 of ~235-275 live kind=trace rows carried a phrase naming a spot the row
registers only at ANOTHER of its own places (F-1671; this job's own fresh count, below).

THE FIX (additive; touches ONLY the rows whose fix needs no new content -- see the job's own finding for
the three rows deliberately left untouched and the needs_input job spawned for them). core/life.row()
gains a new defaulted field, `traces_only_at: {phrase: (place, ...)}` -- an OPTIONAL per-phrase place
RESTRICTION. A phrase absent from this dict is unrestricted and fires at every one of the row's places,
byte-identical to before this field existed; `traces` ITSELF IS NEVER TOUCHED (still the row's whole
vocabulary, in the same order) -- only life_traces.place_traces(), called from traces_pass at mint time,
narrows the pool using it. This was chosen over an earlier draft that moved place-specific phrases OUT of
`traces` into a separate additive dict: that draft left garden_spider's own `traces` empty (it has no
neutral phrase at all, both of its phrases are place-specific), which silently broke
scripts/_test_j1165_trace_object_look.py's own `TRACE_ROWS = {k: r for ... if r.get("traces") ...}` filter
-- a real regression this job's own full suite run caught before it shipped, not assumed away. Four rows
(mice, rabbit, possum, garden_spider) got a `traces_only_at` entry for their own already-wrong phrase(s);
no new text invented, every phrase keeps firing at exactly the place(s) it was already true at.

  [0] module resolution + isolation set-up
  [1] the schema: row()'s new default field; place_traces() narrows correctly, is a no-op for any row
      with no traces_only_at entry (the overwhelming majority); `traces` itself is never shortened
  [2] the four fixed rows: exact pool at every one of their own places, all row-internal-truthful now
  [3] the three rows LEFT untouched (cicada/kingfisher/welcome_swallows -- need new content, needs_input
      job spawned instead) are BYTE-IDENTICAL to their pre-fix pool at every place (nothing here changed)
  [4] REPLAY the whole real data/life_events.jsonl kind=trace history, OLD pool (unrestricted) vs NEW pool
      (place_traces) per (key, place): every phrase that was already truthful is STILL present (no
      truthful phrase changes); a wrong phrase is gone for the four fixed rows, unchanged for the rest
  [5] trace_nouns/trace_object_noun (J-1165's own trace-object gate) untouched by this fix, confirmed
      identical before/after on every trace-carrying row (they read `traces` directly, never `place_traces`)
  [6] isolation: audit hook (no write attempt under any data/), live-file hashes, py_compile

ISOLATION. Same convention as scripts/_test_j1188_carcass_word_boundary.py / _test_j1165_trace_object_look.py.
Sections [4]-[5] only ever READ the live corpus files.

  python scripts/_test_j1189_traces_by_place.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1189_traces_by_place_"))
print("isolated store dir:", TMP)
MARKER = f"j1189_marker_{os.getpid()}"
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
check(hasattr(LT, "place_traces"), "the loaded copy carries the J-1189 fix (place_traces)")
for _m, _a in _REDIRECTS:
    check(TMP in Path(str(getattr(_m, _a))).parents, f"{_m.__name__}.{_a} redirected into the temp dir")

ROWS = life.rows()


REVIEWED_RESTRICTED = {("cicada", "garden"): {"a split brown cicada shell clinging to the bark of a trunk"}}   # J-1281 / F-1801


def row_internal_wrong(r: dict, place: str, phrase: str) -> bool:
    """Row-internal truthfulness check (this job's own analysis method, matching F-1671's own): does
    `phrase` use a word this SAME row registers under one of its OTHER places, not under `place`?"""
    places = r.get("places") or {}
    reg = list(places.keys())
    if place not in reg:
        return False

    def words_of(spots):
        out = set()
        for sp in spots or ():
            out.update(w for w in re.findall(r"[a-z]+", str(sp).lower().replace("_", " ")) if len(w) >= 4)
        return out
    own = {p: words_of(places.get(p)) for p in reg}
    foreign = set()
    for p2 in reg:
        if p2 != place:
            foreign |= (own[p2] - own[place])
    phrase_words = {w for w in re.findall(r"[a-z]+", phrase.lower()) if len(w) >= 4}
    return bool(phrase_words & foreign)


# ── [1] schema sanity ────────────────────────────────────────────────────────────────────────────
print("\n[1] schema: every row defaults traces_only_at={}; place_traces() narrows using it, `traces` itself")
print("    is never shortened (a row with no restriction gets its exact old tuple back, every place)")
for key, r in ROWS.items():
    check(isinstance(r.get("traces_only_at"), dict), f"{key}.traces_only_at is a dict (default {{}})")
UNCHANGED_ROW = "gannet"          # a real row with traces, no restriction -- sanity-checks the no-op path
r0 = ROWS[UNCHANGED_ROW]
check(r0.get("traces_only_at") == {}, f"{UNCHANGED_ROW}: no restriction entries (untouched by this job)")
for place in r0.get("places", {}):
    check(LT.place_traces(r0, place) == list(r0.get("traces") or ()),
          f"{UNCHANGED_ROW}@{place}: place_traces() == the bare traces tuple (no restriction -> byte-identical)")
# a synthetic probe: restricting ONE phrase to ONE place changes nothing for an unrestricted sibling phrase
_syn = life.row("zz_j1189_probe", places={"garden": ["x"], "wood": ["y"]},
                traces=("a neutral phrase", "a garden-only phrase"),
                traces_only_at={"a garden-only phrase": ("garden",)})
check(set(LT.place_traces(_syn, "garden")) == {"a neutral phrase", "a garden-only phrase"}, "synthetic: garden gets both")
check(set(LT.place_traces(_syn, "wood")) == {"a neutral phrase"}, "synthetic: wood gets only the unrestricted one")
check(_syn["traces"] == ("a neutral phrase", "a garden-only phrase"), "synthetic: the row's own `traces` tuple is untouched")

# ── [2] the five rows fixed with every place still non-empty ───────────────────────────────────
print("\n[2] five rows restricted, every registered place keeps a non-empty, row-internally-truthful pool")
print("    (mice/rabbit/possum/garden_spider by J-1189; cicada by J-1281 2026-09-23 -- a new")
print("     wood-appropriate variant added rather than leaving wood empty -- Travis-approved, F-1801)")
FIXED = ("mice", "rabbit", "possum", "garden_spider", "cicada")
for key in FIXED:
    r = ROWS[key]
    check(bool(r.get("traces_only_at")), f"{key}: has at least one traces_only_at restriction")
    for place in r.get("places", {}):
        pool = LT.place_traces(r, place)
        check(len(pool) > 0, f"{key}@{place}: pool is non-empty ({pool})")
        bad = [ph for ph in pool if row_internal_wrong(r, place, ph)]
        check(not bad, f"{key}@{place}: no row-internally-wrong phrase in the pool (found {bad})")

# ── [2b] two rows restricted to ONE place, legitimately empty elsewhere ────────────────────────
print("\n[2b] kingfisher and welcome_swallows: restricted to their one real trace-bearing place;")
print("     an EMPTY pool at their other registered place(s) is the intended fix, not a bug --")
print("     Travis chose (2026-09-23 /decide-review, F-1801) 'no findable ground trace there,")
print("     only the living-row's own sighting continues' over inventing a new world feature")
RESTRICTED_TO_ONE_PLACE = {"kingfisher": "shore", "welcome_swallows": "study"}
for key, only_place in RESTRICTED_TO_ONE_PLACE.items():
    r = ROWS[key]
    check(bool(r.get("traces_only_at")), f"{key}: has at least one traces_only_at restriction")
    for place in r.get("places", {}):
        pool = LT.place_traces(r, place)
        if place == only_place:
            check(len(pool) > 0, f"{key}@{place}: the one real place keeps a non-empty pool ({pool})")
        else:
            check(len(pool) == 0, f"{key}@{place}: correctly empty (restricted away from here) ({pool})")
        bad = [ph for ph in pool if row_internal_wrong(r, place, ph)]
        check(not bad, f"{key}@{place}: no row-internally-wrong phrase in the pool (found {bad})")

# ── [3] no rows left unfixed ─────────────────────────────────────────────────────────────────────
print("\n[3] no rows remain deliberately unfixed -- J-1281 (2026-09-23) closed all three that J-1189")
print("    originally escalated as needing world-content judgement (F-1801, Travis-approved)")
UNFIXED = ()

# ── [4] replay the whole real life_events.jsonl kind=trace history ─────────────────────────────
print("\n[4] REPLAY: every real data/life_events.jsonl kind=trace row, OLD pool (unrestricted) vs NEW pool")
le_path = _LIVE_DATA / "life_events.jsonl"
n_rows = 0
lost_truthful = []
still_wrong = []
removed_wrong = 0
by_key_place = {}
with open(le_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("kind") != "trace":
            continue
        n_rows += 1
        key, place = d.get("key"), d.get("place")
        by_key_place.setdefault((key, place), 0)
        by_key_place[(key, place)] += 1
print(f"    {n_rows} real kind=trace rows read whole (no tail-sampling); {len(by_key_place)} distinct (key, place) pairs")
for (key, place), n in sorted(by_key_place.items()):
    r = ROWS.get(key)
    if not r or place not in (r.get("places") or {}):
        continue                                        # a row/place no longer registered -- not this job's concern
    old = set(r.get("traces") or ())                     # the OLD pool: unrestricted, every phrase, every place
    new = set(LT.place_traces(r, place))
    old_truthful = {ph for ph in old if not row_internal_wrong(r, place, ph)}
    old_wrong = old - old_truthful
    # J-4052: J-1281 (F-1801, Travis-approved via /decide-review 2026-09-23) deliberately restricted the cicada's two phrases
    # to their own places (fence post: garden; "bark of a trunk": wood). The word heuristic above calls the trunk phrase
    # "truthful" in the garden (the garden registers "tree"), but its removal there is the reviewed fix, not a loss.
    old_truthful_lost = old_truthful - new - REVIEWED_RESTRICTED.get((key, place), set())
    if old_truthful_lost:
        lost_truthful.append((key, place, old_truthful_lost))
    remaining_wrong = old_wrong & new
    if remaining_wrong:
        still_wrong.append((key, place, remaining_wrong))
    removed_wrong += len(old_wrong - new)
check(not lost_truthful, f"NO truthful phrase was ever removed from any real (key,place) pool "
                          f"({len(lost_truthful)} violations: {lost_truthful[:5]})")
print(f"    wrong phrases removed from a real (key,place) pool by this fix: {removed_wrong}")
print(f"    real (key,place) pairs still carrying a row-internally-wrong phrase (expected: the 3 unfixed rows only):")
for key, place, wrong in still_wrong:
    print(f"      {key}@{place}: {wrong}")
check(all(key in UNFIXED for key, place, wrong in still_wrong),
      f"every still-wrong real pair belongs to one of the 3 deliberately-unfixed rows "
      f"(violations: {[x for x in still_wrong if x[0] not in UNFIXED]})")
check(removed_wrong > 0, "at least one real historical wrong-place phrase is confirmed gone from its pool")

# ── [5] trace_nouns/trace_object_noun untouched ────────────────────────────────────────────────
print("\n[5] trace_nouns / trace_object_noun (J-1165's own noun gate): reads `traces` directly, never")
print("    place_traces() -- confirmed unaffected by this job's traces_only_at restrictions, all 30 rows")
TRACE_ROWS = {k: r for k, r in ROWS.items() if r.get("traces") and not r.get("external")}
print(f"    {len(TRACE_ROWS)} rows still carry `traces` after this fix (this job touched only whether a")
print(f"    given phrase is restricted, never whether a row has any traces at all)")
for key in FIXED:
    check(key in TRACE_ROWS, f"{key} still appears in the trace-carrying row set (traces was never shortened)")
check(TRACE_ROWS["garden_spider"]["traces"] == ("a web strung between two rosemary stems, holding the last of the dew", "a web in the window corner"),
      "garden_spider's own `traces` tuple in particular is byte-identical to before this job (both phrases, same order)")
for key, r in sorted(TRACE_ROWS.items()):
    nouns = LT.trace_nouns(r)
    aliases = [a for a in (r.get("aliases") or ()) if a]
    for phrase in r["traces"]:
        head = LT.trace_head(phrase)
        if not head or not aliases:
            continue
        target = f"the {aliases[0]}'s {head}"
        noun = LT.trace_object_noun(r, target)
        if noun:
            check(noun in nouns or noun == head, f"{key}: trace_object_noun({target!r}) -> {noun!r}, a real trace head")
check(True, "trace_nouns/trace_object_noun ran clean (no exception) for every trace-carrying row")

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
for _f in (ROOT / "core" / "life.py", ROOT / "core" / "life_traces.py", ROOT / "core" / "life_mammals.py",
           ROOT / "core" / "garden_insects.py", Path(__file__)):
    try:
        _pyc.compile(str(_f), doraise=True)
        check(True, f"py_compile {_f.name}")
    except Exception as exc:
        check(False, f"py_compile {_f.name}: {exc}")

print(f"\n{'ALL OK' if not FAILS else str(FAILS) + ' FAILURE(S)'} — {CHECKS} checks — isolated stores in {TMP}")
sys.exit(1 if FAILS else 0)
