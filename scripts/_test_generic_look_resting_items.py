"""THE GENERIC LOOK NAMES WHAT LIES THERE -- wood, garden and shore default looks end with one clause of resting
carryable items (2026-10-28, J-2481 / D-0502, I-0084 promoted to garden_upgrade; D-0333's defeater (c) met).

core/sensorium.py's _wood_look(), _garden_look() and _shore_look() each had an unconditional default line for a look
with no target (dispatch's "room"; F-2101, J-1438). That default line now ends with ONE clause, in passing, naming the
carryable items whose real `place` is this place and which are not carried -- from core/garden.py's items,
core/wood_life.py's items and core/study_life.py's items (the study's put() writes place = here, so its items travel
too; the shore has no item store of its own). The item's own short name words, sorted by name, no verb, no "you
could", no number, no hint; the by-name looks, the refusal lines and where anything lies are untouched.

What it pins, ON THE REAL STORE COPIES (data/garden.json, data/wood_life.json and the study items in data/room_state.json
are copied into a temp dir and read from there -- the live files are never written; a hash canary proves it):
  [1]  each place's default look names EXACTLY the resting carryable items the stores hold for that place -- the set
       computed here independently from the copies (place == here, not carried, key in the module's own _CARRYABLE) --
       and nothing else; the wood's live case is the seed tin (garden.json items.seed_tin, place=wood since 2026-08-29).
  [2]  a carried item (today: the trowel, the watering can, the axe, the candles) never appears in any place's default
       look; an item lying elsewhere never appears (the tin is not named in the garden; the bow-saw and the barrow are
       not named in the wood); the shore, holding nothing, gets no clause at all.
  [3]  the clause is a world fact only: no digit, no "you could"/"might"/"should"/"take"/"use", no ordering by
       usefulness (the names come sorted by name, the article stripped for the sort).
  [4]  the frame rotates: at least four distinct phrasings per place across the sweep (every new line pool rotates).
  [5]  the clause follows the stores: an item moved to the shore in the temp copy appears there (and nowhere else);
       a study item set down in the wood appears in the wood; picked up again, it vanishes; the kill switch
       (NASCENCE_LOOK_RESTING_ITEMS=0) removes the clause and nothing else.
  [6]  the by-name looks are untouched: no by-name look in any place carries a resting frame, and the garden's own
       item_look / the wood's own look for the tin answer exactly as before. With --baseline-root <HEAD worktree> the
       same by-name sweep (same seeds, same store copies) is run in a fresh process against THAT tree and compared
       byte for byte with this one (--dump / --root are that subprocess's own switches).

ISOLATED: every store this touches is redirected into a temp dir before any module writes; core.memory.store's
DB_PATH too; `import core` happens BEFORE any lab helper and core.__file__ is asserted to be this tree's own.
Run:  python scripts/_test_generic_look_resting_items.py [--baseline-root C:\\path\\to\\HEAD-worktree]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_ap = argparse.ArgumentParser()
_ap.add_argument("--root", default="", help="(subprocess) import core from THIS tree instead of the script's own")
_ap.add_argument("--dump", default="", help="(subprocess) write the by-name sweep to this JSON file and exit")
_ap.add_argument("--baseline-root", default="", help="a HEAD worktree to compare the by-name sweep against")
ARGS = _ap.parse_args()

ROOT = Path(ARGS.root).resolve() if ARGS.root else Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  -- BEFORE any lab helper (F-2500-family rule: import core first, then isolate)
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"
assert not str(Path(core.__file__).resolve()).lower().startswith(r"c:\nascence\core"), "core imported from the LIVE tree"

TMP = Path(tempfile.mkdtemp(prefix="generic_look_resting_"))
print("tree:", ROOT)
print("isolated store dir:", TMP)

LIVE = Path(r"C:\Nascence") / "data"
LIVE_FILES = [LIVE / n for n in ("garden.json", "wood_life.json", "room_state.json", "garden_ledger.jsonl",
                                 "wood_ledger.jsonl", "study_ledger.jsonl", "hands_trace.jsonl", "world_objects.json")]


def _snap():
    return {p.name: (p.stat().st_size, hashlib.md5(p.read_bytes()).hexdigest()) if p.exists() else None for p in LIVE_FILES}


_BEFORE = _snap()
_REDIRECTS: list[tuple[object, str]] = []

# ---- isolate BEFORE importing anything that might write (mirrors scripts/_test_wood_tin_reach.py) ----------------
from core.memory import store as _store                  # noqa: E402
_store.DB_PATH = TMP / "nascence.db"
_store.init_db()
_REDIRECTS.append((_store, "DB_PATH"))
from core import sensorium as S                          # noqa: E402
S._STATE_F = TMP / "room_state.json"
_REDIRECTS.append((S, "_STATE_F"))
from core import supply as SUP                           # noqa: E402
SUP._F, SUP._LOG = TMP / "supply.json", TMP / "supply_log.jsonl"
_REDIRECTS += [(SUP, "_F"), (SUP, "_LOG")]
for mod, attrs in (("core.life", ("_F", "_LEDGER", "_EVENTS")), ("core.study_life", ("_LEDGER", "_EVENTS")),
                   ("core.provisions", ("_F", "_LOG")), ("core.sound_knowledge", ("_LEDGER_F",)),
                   ("core.locomotion", ("_POS_F",)), ("core.garden", ("_F", "_LEDGER", "_EVENTS")),
                   ("core.garden_life", ("_F",)), ("core.shore_life", ("_F", "_EVENTS")),
                   ("core.wood_life", ("_F", "_EVENTS", "_LEDGER")), ("core.cat", ("_STATE_F",)),
                   ("core.world_objects", ("_OBJECTS_F",)),
                   ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")),
                   ("core.fieldcraft", ("_F",)), ("core.intentions", ("_F", "_LOG")), ("core.hands", ("_TRACE",)),
                   ("core.procedures", ("_F", "_LOG")), ("core.literal_will", ("_LOG", "_STATE")),
                   ("core.night", ("_LOG", "_RECENT")), ("core.boredom", ("_STATE",)),
                   ("core.letter_store", ("_F", "_LOG")), ("core.shore_nest_look_ledger", ("_F", "_LEDGER")),
                   ("core.garden_knowledge", ("_F",)), ("core.garden_life", ("_EVENTS",)), ("core.smell", ("_F",)),
                   ("core.keepsakes", ("_F",)), ("core.look_render_ledger", ("_LEDGER",)),
                   ("core.scene_extra_ledger", ("_LEDGER",)), ("core.world_traces", ("_TRACES_F",)),
                   ("core.spatial", ("_DEPTH_SHADOW",)), ("core.nature_study", ("_STATE", "_LOG")),
                   ("core.nest_gate_shadow", ("_LEDGER",)), ("core.care_package", ("_F", "_LOG"))):
    try:
        m = __import__(mod, fromlist=["x"])
        for a in attrs:
            if hasattr(m, a):
                setattr(m, a, TMP / f"{mod.split('.')[-1]}_{a.strip('_').lower()}.json")
                _REDIRECTS.append((m, a))
        if hasattr(m, "_d"):
            m._d = None
    except Exception as exc:
        print("  (isolation note)", mod, exc)

from core import wandering as _WDR                       # noqa: E402
from core import activity_memory as _AM                  # noqa: E402
_WDR.perceive = lambda *a, **k: None
_AM.record = lambda *a, **k: None

from core import garden as G                             # noqa: E402
from core import wood_life as WL                         # noqa: E402
from core import study_life as SL                        # noqa: E402

# ---- the REAL store copies ------------------------------------------------------------------------------------------
shutil.copy(LIVE / "garden.json", TMP / "garden_f.json")          # G._F already points here (redirect above)
shutil.copy(LIVE / "wood_life.json", TMP / "wood_life_f.json")    # WL._F likewise
assert G._F == TMP / "garden_f.json" and WL._F == TMP / "wood_life_f.json"
G._state = None
_STUDY_ITEMS = json.loads((LIVE / "room_state.json").read_text(encoding="utf-8")).get("study", {}).get("items", {})
GARDEN_COPY = json.loads((TMP / "garden_f.json").read_text(encoding="utf-8"))
WOOD_COPY = json.loads((TMP / "wood_life_f.json").read_text(encoding="utf-8"))

fails = 0


def check(cond, msg):
    global fails
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails += 1


def setup(loc: str):
    S.state.clear()
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0,
                    "location": loc, "study": {"_init": True, "items": json.loads(json.dumps(_STUDY_ITEMS))}})


def expected(place: str) -> dict:
    """{key: short name} computed here, independently of sensorium's own walk."""
    out = {}
    for k, it in GARDEN_COPY.get("items", {}).items():
        if k in G._CARRYABLE and it.get("place") == place and not it.get("carried"):
            out[k] = S._resting_short_name(k, it["name"])
    for k, it in WOOD_COPY.get("items", {}).items():
        if k in WL._CARRYABLE and it.get("place") == place and not it.get("carried"):
            out[k] = S._resting_short_name(k, it["name"])
    for k, it in _STUDY_ITEMS.items():
        if k in SL._CARRYABLE and it.get("place") == place and not it.get("carried"):
            out[k] = S._resting_short_name(k, it["name"])
    return out


_FRAME_RX = {p: [re.compile(r"(?:^|\s)" + re.escape(f.split("{items}")[0]) + r"(.+?)\.$") for f in fr]
             for p, fr in getattr(S, "_RESTING_FRAMES", {}).items()}   # {} in the --dump subprocess against a HEAD tree


def parse_clause(place: str, text: str):
    """(frame index, [names]) for the resting clause at the END of a default look, or (None, None)."""
    for i, rx in enumerate(_FRAME_RX[place]):
        m = rx.search(text)
        if m and text.endswith(m.group(0).strip()):
            body = m.group(1)
            names = [n.strip() for part in body.split(", ") for n in part.split(" and ")]
            return i, names
    return None, None


FORBIDDEN = ("you could", "could", "might", "should", "take ", "use ", "useful", "handy", "need")

# ---- the by-name sweep (also the --dump mode's whole job) -----------------------------------------------------------
BY_NAME = {
    "wood": ["tin", "dented tin", "seed tin", "axe", "saw", "barrow", "tree", "deadfall", "sea", "sky", "oak", "stream"],
    "garden": ["tin", "dented tin", "trowel", "fork", "twine", "stakes", "pot", "bucket", "netting", "shears",
               "bed", "soil", "sea", "sky", "barrel", "compost", "can", "lawn"],
    "shore": ["tide", "pools", "rocks", "sea", "sky", "driftwood", "cave", "sand", "board", "shelf", "cairn", "fire"],
}


def by_name_sweep() -> dict:
    out = {}
    for place, targets in BY_NAME.items():
        for tgt in targets:
            setup(place)
            random.seed(f"{place}|{tgt}|J-2481")
            out[f"{place}:{tgt}"] = S.look(tgt)
    return out


if ARGS.dump:
    Path(ARGS.dump).write_text(json.dumps(by_name_sweep(), indent=1, ensure_ascii=False), encoding="utf-8")
    print("dumped", ARGS.dump)
    sys.exit(0)

# ---- [1]-[4] the default looks on the real copies -------------------------------------------------------------------
print("\n[1]-[4] default looks, real store copies")
carried_now = [S._resting_short_name(k, it["name"]) for src, car in ((GARDEN_COPY["items"], G._CARRYABLE),
                                                                      (WOOD_COPY["items"], WL._CARRYABLE),
                                                                      (_STUDY_ITEMS, SL._CARRYABLE))
               for k, it in src.items() if k in car and it.get("carried")]
print("  carried today:", carried_now)
all_short = {}
for src, car in ((GARDEN_COPY["items"], G._CARRYABLE), (WOOD_COPY["items"], WL._CARRYABLE), (_STUDY_ITEMS, SL._CARRYABLE)):
    for k, it in src.items():
        if k in car:
            all_short[k] = S._resting_short_name(k, it["name"])
print("  short names:", sorted(set(all_short.values())))
check("seed_tin" in expected("wood") and expected("wood")["seed_tin"] == "a dented tin",
      "the live case: garden.json's seed_tin rests in the wood and is named 'a dented tin'")
check(not expected("shore"), "today nothing carryable rests on the shore")

for place in ("wood", "garden", "shore"):
    exp = expected(place)
    frames, outs = set(), []
    for i in range(60):
        setup(place)
        random.seed(i)
        outs.append(S.look("room"))
    named_sets = []
    for o in outs:
        fi, names = parse_clause(place, o)
        if fi is not None:
            frames.add(fi)
            named_sets.append(tuple(names))
    print(f"  {place}: expected {sorted(exp.values())}; sample: {outs[0][-160:]!r}")
    if exp:
        check(len(named_sets) == len(outs), f"{place}: every one of {len(outs)} default looks carries the clause")
        check(all(sorted(ns) == sorted(exp.values()) for ns in named_sets),
              f"{place}: the clause names exactly the resting carryable items {sorted(exp.values())} and nothing else")
        check(all(list(ns) == sorted(ns, key=lambda n: re.sub(r'^(a|an|the|some|two)\s+', '', n.lower())) for ns in named_sets),
              f"{place}: names sorted by name (article stripped), never by usefulness")
        check(len(frames) >= 4, f"{place}: the frame rotates -- {len(frames)} distinct phrasings seen in {len(outs)} looks")
        clauses = [o[o.rfind(S._RESTING_FRAMES[place][fi].split('{items}')[0]):] for o, (fi, _) in
                   zip(outs, [parse_clause(place, o) for o in outs]) if fi is not None]
        check(all(not re.search(r"\d", c) for c in clauses), f"{place}: no digit in any clause")
        check(all(not any(w in c.lower() for w in FORBIDDEN) for c in clauses),
              f"{place}: no verb, no 'you could', no usefulness word in any clause")
    else:
        check(not named_sets, f"{place}: no clause at all when nothing rests here ({len(outs)} looks)")
    for cn in carried_now:
        check(all(cn not in o for o in outs), f"{place}: carried item {cn!r} never appears")
    elsewhere = {k: n for k, n in all_short.items() if k not in exp}
    for k, n in elsewhere.items():
        check(all(n not in o for o in outs), f"{place}: item lying elsewhere {n!r} ({k}) never appears")

# ---- [5] the clause follows the stores ------------------------------------------------------------------------------
print("\n[5] the clause follows the stores (temp copies only)")
G._load()["items"]["hand_fork"]["place"] = "shore"
setup("shore"); random.seed(7)
fi, names = parse_clause("shore", S.look("room"))
check(names == ["a three-tined hand fork"], f"hand fork moved to the shore (in the copy): the shore names it alone -> {names}")
setup("garden"); random.seed(7)
fi, names = parse_clause("garden", S.look("room"))
check(names is not None and "a three-tined hand fork" not in names, "... and the garden no longer names it")
G._load()["items"]["hand_fork"]["place"] = "garden"

setup("wood")
S.state["study"]["items"]["lantern"]["place"] = "wood"; S.state["study"]["items"]["lantern"]["carried"] = False
random.seed(3)
fi, names = parse_clause("wood", S.look("room"))
check(names == ["a dented tin", "a tin lantern"], f"a study item set down in the wood is named beside the tin -> {names}")
S.state["study"]["items"]["lantern"]["carried"] = True
random.seed(3)
fi, names = parse_clause("wood", S.look("room"))
check(names == ["a dented tin"], f"... picked up again, it vanishes -> {names}")

setup("wood"); random.seed(5)
_on = S.look("room")
os.environ["NASCENCE_LOOK_RESTING_ITEMS"] = "0"
setup("wood"); random.seed(5)
_off = S.look("room")
del os.environ["NASCENCE_LOOK_RESTING_ITEMS"]
check(parse_clause("wood", _off)[0] is None and _on.startswith(_off) and len(_on) > len(_off),
      "kill switch: the clause is gone and the rest of the default look is byte-identical")

# ---- [6] by-name looks untouched --------------------------------------------------------------------------------------
print("\n[6] by-name looks untouched")
sweep = by_name_sweep()
check(all(parse_clause(k.split(':')[0], v)[0] is None for k, v in sweep.items()),
      f"no by-name look ({len(sweep)}) carries a resting frame")
setup("wood")
check(sweep["wood:dented tin"].startswith("You look at a dented tin with a hinged lid"),
      f"the wood's by-name tin look is the J-1438 item line: {sweep['wood:dented tin'][:70]!r}")
setup("garden")
check(G.item_look("tin") == "", "from the garden, item_look('tin') still answers '' (the tin lies in the wood)")
check("the tin is not here" in G.sow("I want to sow the radish seed").lower() or "tin" in G.sow("I want to sow the radish seed").lower(),
      "the sow refusal still names the absent tin, unchanged")
if ARGS.baseline_root:
    base = Path(ARGS.baseline_root).resolve()
    out_b, out_m = TMP / "sweep_baseline.json", TMP / "sweep_mine.json"
    for root, out in ((base, out_b), (ROOT, out_m)):
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--root", str(root), "--dump", str(out)],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-2000:])
        check(r.returncode == 0, f"by-name sweep subprocess against {root} ran")
    if out_b.exists() and out_m.exists():
        b, m = json.loads(out_b.read_text(encoding="utf-8")), json.loads(out_m.read_text(encoding="utf-8"))
        diff = [k for k in b if b[k] != m.get(k)]
        for k in diff[:6]:
            print("   DIFF", k, "\n     base:", b[k][:160], "\n     mine:", m.get(k, "")[:160])
        check(not diff, f"by-name looks byte-identical to the HEAD tree ({len(b)} targets across 3 places){' -- differ: ' + str(diff) if diff else ''}")

# ---- canaries ----------------------------------------------------------------------------------------------------------
print("\ncanaries")
_after = _snap()
check(_after == _BEFORE, "live data/ stores untouched (hash canary on " + ", ".join(p.name for p in LIVE_FILES) + ")")
escaped = [f"{m.__name__}.{a}" for m, a in _REDIRECTS if not str(getattr(m, a)).startswith(str(TMP))]
check(not escaped, f"every redirected store path is inside the temp dir ({len(_REDIRECTS)} checked){' ESCAPED: ' + str(escaped) if escaped else ''}")
print("\nFAILS:", fails)
sys.exit(1 if fails else 0)
