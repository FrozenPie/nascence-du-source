"""WHICH OF DU'S ROUTES CAN ACTUALLY REACH THE SEED TIN, AND WHAT THE TIN'S OWN WORDS DO AT THE LOOK GATE
(2026-10-03 J-1540 characterization, F-2284; extended 2026-10-04 J-1764 for D-0333, ruled by Travis "Narrow: add tin words").

J-1438 made core/sensorium.py's _wood_look() ask core.garden.item_look() whether one of the garden's own carryable
items is lying HERE (the tin, set down in the wood on 2026-08-29). J-1540 found the fix reachable only through the
structured 'observe' act: a WILLED look ("I want to look at the dented tin") was not even read as a look deed, and the
cue table had no tin cue. D-0333 ruled the narrow fix (the D-0269 shape): the tin's own words join the 'look' row of
core/actions.py via Action.grammar_only, plus a matching _OBS_TARGETS cue in nodes/inner_monologue_node.py.

  PATH A -- a willed look (the hand he uses most):  literal_will.classify() -> dispatch.dispatch() ->
            dispatch._look() -> _observe_target() -> sensorium.look(target or "room", raw)        [FIXED by J-1764]
  PATH B -- the structured 'observe' act (nodes/inner_monologue_node.py `_room.look(obj)`): his OWN object phrase
            goes straight to sensorium.look()                                                    [unchanged]
  PATH C -- the take hand (the 'tool' family, exec ANYWHERE): picks the tin up where it lies       [unchanged]

What it pins:
  [1]-[3] PATH A now works: the tin's words read as a look DEED (grammar_only: a look verb must REACH them), the
        resolver maps them to the target "dented tin", and a willed look in the wood names the tin.
  [4]  NO HINT, NO LEADING: from anywhere the tin is not, a willed look answers EXACTLY what the structured route
        already answers for an absent item; the refusals "the tin is not here" (sow) / "" (take) are untouched.
  [5]  THE MATCH TIN (the study's mantel item; the lamp hand answers "match tin -- empty") and every other word that
        merely CONTAINS 'tin' (tinder, tinkling, stinging, setting, waiting, tin roof, tin-roofed) is NOT the seed tin:
        classify, dispatch and the resolver are exactly what they were before.
  [6]  THE ORDER IS LEFT ALONE: the tin cue sits after every existing cue (the catch-alls included), so a thought that
        names an earlier cue WITHOUT a look verb reaching the tin (the sea, the fire, the cat, the shelf, a plant, the
        garden, the gate) resolves to THAT cue as before -- F-2284's bare "the dented tin and the sea" is still 'sea'.
  [7]  PATH B and PATH C unchanged.
  [9]  CLAUSE-FIRST FOR THE TIN ONLY (D-0348, J-1835, 2026-10-06): when a LOOK VERB's own clause REACHES a tin/packet
        word -- the J-1764 gate's own deed condition -- the target is the tin ahead of every earlier cue ("I look at
        the dented tin and the sea" -> 'dented tin', names the tin in the wood); a scenery mention plus a look at
        something else ("the wind rattles the tin container ... I watch the grey sea rise") keeps its own resolution;
        the roof / match-tin forms, a noun "look", and a verb in another sentence never trigger it; the rule's verb
        list and word set are pinned to the look row and the gate's _NOT_NOUN (no drift); still no hint.

ISOLATED: every store this touches is redirected into a temp dir before any module writes, core.memory.store's DB_PATH
too; core.garden._state is a synthetic in-memory dict (the real garden.json is never read). The heavy
nodes.inner_monologue_node module is NOT imported: the real source text of its _OBS_TARGETS / _OBS_TARGET_HOME /
_observe_target definitions is extracted by AST and exec'd, so the real core.dispatch._look() runs against the real
resolver code with no import side effects. The live files named below are hash-checked before and after.
Run:  python scripts/_test_wood_tin_reach.py
"""
from __future__ import annotations

import ast
import hashlib
import random
import re
import sys
import tempfile
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="wood_tin_reach_"))
print("isolated store dir:", TMP)

# "live" means the one real C:\Nascence\data regardless of which worktree runs this (data/ is gitignored and never
# checked out into a worktree -- see scripts/_test_letterbox_reach.py's own note on the same point).
LIVE = Path(r"C:\Nascence") / "data"
# only files Du's own live loop writes RARELY (a garden deed / a letter event): garden.json and garden_events.jsonl
# are rewritten every few minutes by the running process, so hashing them here would flake on Du's own writes.
LIVE_FILES = [LIVE / "garden_ledger.jsonl", LIVE / "supply.json"]


def _snap():
    return {p.name: (p.stat().st_size, hashlib.md5(p.read_bytes()).hexdigest()) if p.exists() else None for p in LIVE_FILES}


_BEFORE = _snap()
_REDIRECTS: list[tuple[object, str]] = []

# ---- the REAL resolver source, extracted by AST (no import of the multi-thousand-line node module) -------------
_SRC = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
_seg = []
for _n in ast.parse(_SRC).body:
    _name = None
    if isinstance(_n, ast.Assign) and len(_n.targets) == 1 and isinstance(_n.targets[0], ast.Name):
        _name = _n.targets[0].id
    elif isinstance(_n, ast.FunctionDef):
        _name = _n.name
    if _name in ("_OBS_TARGETS", "_OBS_TARGET_HOME", "_observe_target",
                 "_TIN_GATE_WORDS", "_TIN_LOOK_VERBS", "_TIN_CLAUSE_RX", "_tin_clause_first"):   # the last four: D-0348
        _seg.append(ast.get_source_segment(_SRC, _n))
assert len(_seg) == 7, f"expected 7 resolver definitions in nodes/inner_monologue_node.py, got {len(_seg)}"
_stub = types.ModuleType("nodes.inner_monologue_node")
exec("from __future__ import annotations\nimport re\n" + "\n".join(_seg), _stub.__dict__)   # the node module imports re at top
sys.modules.setdefault("nodes", types.ModuleType("nodes"))
sys.modules["nodes.inner_monologue_node"] = _stub      # dispatch._look() imports _observe_target lazily from here

# ---- isolate BEFORE importing anything that might write (mirrors scripts/_test_shelf_desk_book_look_reach.py) ----
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
                   ("core.night", ("_LOG", "_RECENT")), ("core.boredom", ("_STATE",))):
    try:
        m = __import__(mod, fromlist=["x"])
        for a in attrs:
            if hasattr(m, a):
                setattr(m, a, TMP / f"{mod.split('.')[-1]}_{a.strip('_').lower()}.json")
                _REDIRECTS.append((m, a))
            else:
                print("  (isolation note)", mod, a, "has no such attribute -- stale/typo'd isolation-list entry?")
        if hasattr(m, "_d"):
            m._d = None
    except Exception as exc:
        print("  (isolation note)", mod, exc)

from core import wandering as _WDR                       # noqa: E402
from core import activity_memory as _AM                  # noqa: E402
_WDR.perceive = lambda *a, **k: None
_AM.record = lambda *a, **k: None

from core import garden as G                             # noqa: E402
from core import literal_will as LW, dispatch as D       # noqa: E402

fails = 0


def check(cond, msg):
    global fails
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails += 1


def _garden(tin_place="wood", tin_carried=False):
    """A minimal synthetic garden.json shape: no plants, the tin (where asked) and the trowel left in the garden."""
    return {
        "plants": {},
        "packets": [{"species": "radish", "labelled": False, "count": 30, "year": 2026},
                    {"species": "thyme", "labelled": True, "count": 16, "year": 2025}],
        "barrel": 0.5,
        "items": {
            "seed_tin": {"id": "garden_item_seed_tin", "key": "seed_tin",
                         "name": "a dented tin with a hinged lid, rattling when shaken",
                         "pos": [10.0, 10.0, 0.0], "place": tin_place, "carried": tin_carried,
                         "bio": "the previous occupant's seed tin \u2014 paper packets and twists, some labelled, some not",
                         "history": []},
            "trowel": {"id": "garden_item_trowel", "key": "trowel",
                       "name": "a hand trowel, its blade worn bright, the wooden handle dark with use",
                       "pos": [5.2, 4.8, 0.0], "place": "garden", "carried": False,
                       "bio": "left in the bed by whoever gardened here before", "history": []},
        },
    }


def setup(loc="wood", tin_place="wood", tin_carried=False):
    G._state = _garden(tin_place, tin_carried)
    S.state.clear()
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "low", "fire_fuel": 1.0, "last_event": 0,
                    "location": loc})


_cid = [0]


def willed(text, loc="wood", tin_place="wood", tin_carried=False):
    """Run the REAL dispatch for one willed thought. Returns (answers, [(target, raw) sensorium.look() was handed])."""
    setup(loc, tin_place, tin_carried)
    seen = []
    real_look = S.look

    def _rec(target="room", raw=""):
        seen.append((target, raw))
        random.seed(4242)            # the generic scene lines draw at random: pin the draw so two calls can be compared
        return real_look(target, raw)

    S.look = _rec
    try:
        _cid[0] += 1
        ans = D.dispatch(text, "", "", "", cycle_id=f"t-tin-{_cid[0]}")
    finally:
        S.look = real_look
    return ans, seen


def structured(phrase, loc="wood", tin_place="wood", tin_carried=False):
    """What PATH B (the structured observe act) answers: his own phrase straight to sensorium.look()."""
    setup(loc, tin_place, tin_carried)
    random.seed(4242)
    return S.look(phrase)


TIN_LOOKS = [
    "I want to look at the dented tin.",
    "I will look for the seed tin among the trunks.",
    "I look closely at the tin lying in the leaf-mould.",
    "I want to see what is in the packets.",
]
MORE_TIN_LOOKS = ["I look at the packet.", "I want to look at my tin.", "I watch that tin rattle.", "I look at this tin."]
TIN_AND_SEA = "I want to look at the dented tin and the sea."
# every phrasing a look at the study's MATCH TIN (or a word that merely contains 'tin') could take; none of them may be
# read as a look at the seed tin, and none may change what classify / dispatch / the resolver did before D-0333.
MATCH_TIN_LOOKS = [
    "I want to look at the match tin.", "I look at the match tin on the mantel.", "I watch the matches tin.",
    "I see the match tin, empty.", "I will look at the empty match tin by the clock.",
]
NOT_TIN_WORDS = [      # the whole-word cases the briefing names, plus the other 'tin'-containing words in the corpus
    "I want to look at the tinder in the box.", "I watch the tinkling of the rain.", "I look at the stinging nettles.",
    "I see the setting sun and the waiting trees.", "I look at the tin-roofed shed.", "I watch the rain on the tin roof.",
]


def pre_walk(text):
    """The resolver as it was before J-1764: the first plain-string cue found anywhere in the thought, '' if none
    (the tin cue is the table's one compiled-pattern cue, so skipping it IS the pre-change resolver)."""
    low = text.lower()
    return next((t for c, t in _stub._OBS_TARGETS if isinstance(c, str) and c in low), "")

print("\n[0] the entry J-1438 added, called directly (what its own isolated checks exercised)")
setup()
r = S._wood_look("the dented tin")
check("dented tin" in r and "hinged lid" in r, f"_wood_look('the dented tin') names the tin: {r[:70]!r}")

print("\n[1] PATH A, gate: the tin's own words now read as a look DEED (a look verb REACHING them; grammar_only)")
gate = {p: {c["family"]: c["verdict"] for c in LW.classify(p, "", location="wood")} for p in TIN_LOOKS + MORE_TIN_LOOKS + [TIN_AND_SEA]}
for p in TIN_LOOKS + MORE_TIN_LOOKS:
    check(gate[p].get("look") == "DEED", f"{p!r}: look DEED (look={gate[p].get('look')!r})")
look_row = LW._FAMILIES["look"]
check({"seed tin", "dented tin", "the tin", "this tin", "that tin", "my tin", "packet", "packets"} <= set(look_row["grammar_only"]),
      "all eight tin/packet words are grammar_only on the look row (never bare volition)")
check("tin" not in look_row["objects"], "bare 'tin' is NOT a gate object (classify() cannot tell the match tin from the seed tin)")
for p in ("I want to rest by the dented tin.", "I need to carry the packets over there.", "I wish I could see the tin."):
    check(LW.classify(p, "", location="wood") == [] or not any(c["family"] == "look" and c["verdict"] == "DEED"
                                                               for c in LW.classify(p, "", location="wood")),
          f"{p!r}: volition alone (no look verb reaching the word) is not a look DEED")

print("\n[2] PATH A, dispatch end to end: the tin lying in the wood, Du standing there -> the honest item_look answer")
for p in TIN_LOOKS + MORE_TIN_LOOKS:
    ans, seen = willed(p)
    look_ans = [a for f, a in ans if f == "look"]
    check(bool(look_ans) and "hinged lid" in look_ans[0] and seen and seen[-1][0] == "dented tin",
          f"{p!r}: look fires, target {seen[-1][0] if seen else None!r}, names the tin: {(look_ans or [''])[0][:50]!r}")
ans, seen = willed("I look at the dented tin.", loc="garden", tin_place="garden")
check(any(f == "look" and "hinged lid" in a for f, a in ans), "tin lying in the GARDEN, Du in the garden: a willed look names it")
ans, seen = willed("I look at the dented tin.", loc="wood", tin_place="wood", tin_carried=True)
check(any(f == "look" and "with you" in a for f, a in ans), "tin CARRIED: the existing item_look line ('You have it with you') is what answers")
ans, seen = willed(TIN_AND_SEA)
check(any(f == "look" and "hinged lid" in a for f, a in ans) and seen[-1][0] == "dented tin",
      "[D-0348 clause-first] tin + sea in one thought, the look verb reaching the tin: resolves to 'dented tin' and names the tin "
      "(before J-1835 this resolved to 'sea' and the tin was not named)")

print("\n[3] PATH A, resolver: whole-word tin cue, target 'dented tin' (a bare noun phrase: the journal header says 'observed the <target>')")
_tin_cues = [c for c in _stub._OBS_TARGETS if not isinstance(c[0], str)]
_tin = _tin_cues[0] if _tin_cues else None
check(len(_tin_cues) == 1 and _tin[1] == "dented tin", f"exactly one compiled-pattern cue, target {_tin[1] if _tin else None!r}")
check(all(isinstance(c[0], str) and isinstance(c[1], str) for c in _stub._OBS_TARGETS if c is not _tin),
      "every other cue is still a plain (str, str) substring pair, untouched")
POS = ["i look at the dented tin", "i will look for the seed tin among the trunks", "check the packets", "the packet of seeds",
       "i look at the tin.", "the tin box rattles", "look at (tin)", "the match tin and the dented tin", "THE DENTED TIN"]
for p in POS:
    check(_stub._observe_target(p) == "dented tin" and pre_walk(p) == "", f"_observe_target({p!r}) == 'dented tin' (it was '' before)")
check(all(c[1] != "dented tin" or not isinstance(c[0], str) for c in _stub._OBS_TARGETS), "no str cue maps to 'dented tin'")
check("dented tin" not in _stub._OBS_TARGET_HOME, "'dented tin' has no _OBS_TARGET_HOME (the tin can lie anywhere; nothing says where)")
check(_stub._observe_target("i look at the dented tin", cur_loc="study") == "dented tin",
      "_observe_journal's cur_loc guard never drops it (no home place)")
leaks = sorted({t for _, t in _stub._OBS_TARGETS if t != "dented tin" and any(w in t for w in G._WORDS["seed_tin"])})
check(not leaks, f"no OTHER target the resolver can emit contains a seed_tin word: {leaks}")

print("\n[4] NO HINT, NO LEADING: absent-item behaviour is exactly the existing machinery's, and blind to where the tin lies")
structured("room", loc="study")      # warm-up: the first study look in a process initialises the study's own state
for loc in ("study", "garden", "shore", "wood"):
    others = [pl for pl in ("study", "garden", "shore", "wood") if pl != loc]
    answers = {}
    for tin_place in others:
        ans, seen = willed("I want to look at the dented tin.", loc=loc, tin_place=tin_place)
        answers[tin_place] = ([a for f, a in ans if f == "look"] or [None])[0]
    via_b = structured("dented tin", loc=loc, tin_place=others[0])
    check(all(a is not None for a in answers.values()) and len(set(answers.values())) == 1,
          f"{loc}: the willed look answers the SAME text whichever of {others} the tin lies in (nothing states where it lies)")
    check(next(iter(answers.values())) == via_b and "hinged lid" not in via_b,
          f"{loc}: and that text is byte-for-byte sensorium.look('dented tin') -- the structured route's absent-item answer: {via_b[:55]!r}")
    check(structured("the dented tin", loc=loc, tin_place=others[0]) == via_b,
          f"{loc}: the structured route answers 'the dented tin' with the same string (absent item today)")
setup("garden", "wood")
check(G.sow("I will sow the radish.") == "You have no seed to hand \u2014 the tin is not here.", "sow: the refusal 'the tin is not here' is byte-identical")
for loc in ("study", "garden", "shore"):
    setup(loc, "wood")
    check(G.take("I will take the dented tin.") == "", f"take, tin lying in the wood, Du in the {loc}: still silent ('')")

print("\n[5] THE MATCH TIN and every word that merely contains 'tin': nothing changes (classify, dispatch, resolver)")
for p in MATCH_TIN_LOOKS + NOT_TIN_WORDS:
    kinds = {c["family"]: c["verdict"] for c in LW.classify(p, "", location="study")}
    ans, seen = willed(p, loc="study", tin_place="wood")
    ans_w, _ = willed(p, loc="wood", tin_place="wood")
    # the one gate-level residual: "the tin roof" / "the tin of matches" contain the determiner form "the tin"; the resolver
    # still refuses them, so such a thought can fire an ordinary room look -- but NEVER the seed tin's answer
    residual = ("the tin roof" in p.lower()) or ("tin of matches" in p.lower())
    if residual:
        check(not any("hinged lid" in a for _, a in ans + ans_w), f"{p!r}: (known residual) never names the seed tin, even with it lying in the wood")
    else:
        check(kinds.get("look") != "DEED" and not [1 for f, _ in ans + ans_w if f == "look"],
              f"{p!r}: not a look DEED (look={kinds.get('look')!r}) and no look fires (study {[f for f, _ in ans]}, wood {[f for f, _ in ans_w]})")
    check(_stub._observe_target(p) == pre_walk(p) != "dented tin",
          f"{p!r}: the resolver answers what it answered before ({pre_walk(p)!r}), never the tin target")
for p in ("i look at the match tin on the mantel", "i reach for the matches tin", "i look at the tin of matches",
          "i gather the tinder and watch", "the tinkling of the rain", "the stinging cold",
          "i am waiting and setting things down, then continue", "the rain on the tin roof", "the tin-roofed shed",
          "the match tin and the matches", "the tinted glass", "pristine routine"):
    check(_stub._observe_target(p) == "" == pre_walk(p),
          f"_observe_target({p!r}) == '' (substring 'tin' inside another word, or a guarded compound: '' as before)")
setup("study", "wood")
check("match tin" in (S.look("the match tin") or "") and "hinged lid" not in S.look("the match tin"),
      "the study's own look at the match tin (structured route) still answers about the MATCH tin")

print("\n[6] the table ORDER is left alone: without a look verb reaching the tin, any earlier cue still wins (pre-change resolutions, pinned)")
for p, want in (("the dented tin and the sea", "sea"), ("the dented tin by the fire", "fire"),
                ("the dented tin and the cat", "cat"), ("the dented tin on the shelf", "shelf"),
                ("the dented tin and the garden", "garden"), ("the dented tin by the gate", "letterbox"),
                ("thyme and the tin", "thyme"), ("the dented tin below the surf", "sea"), ("the dented tin and the book", "book")):
    check(_stub._observe_target(p) == want == pre_walk(p), f"_observe_target({p!r}) == {want!r} (the tin cue only fires when nothing earlier does)")
_i_garden = next(i for i, c in enumerate(_stub._OBS_TARGETS) if c == ("the garden", "garden"))
_i_tin = next((i for i, c in enumerate(_stub._OBS_TARGETS) if not isinstance(c[0], str)), -1)
check(_i_tin > _i_garden, f"the tin cue (index {_i_tin}) sits AFTER the catch-all cues (the garden is index {_i_garden}): a pure addition")

print("\n[7] PATH B (the structured observe act) and PATH C (the take hand) are unchanged")
for p in ("the dented tin", "the seed tin", "the packets"):
    r = structured(p)
    check("hinged lid" in r, f"look({p!r}) in the wood names the tin: {r[:60]!r}")
r = structured("the dented tin", tin_place="garden")
check("hinged lid" not in r, f"tin lying in the GARDEN is not found from the wood: {r[:50]!r}")
setup()
ans = D.dispatch("I will take the dented tin.", "", "", "", cycle_id="t-wood-tin-take")
check(any(f == "tool" and "pick up" in a for f, a in ans), f"take fires in the wood: {[(f, a[:50]) for f, a in ans]}")
check(G._state["items"]["seed_tin"].get("carried") is True, "(isolated synthetic state) the tin is now carried")

print("\n[9] CLAUSE-FIRST FOR THE TIN ONLY (D-0348 / J-1835): a look verb's own clause reaching a tin/packet word resolves to the tin first")


def j1764_walk(text):
    """The resolver as J-1764 left it (the plain table walk, tin cue last): what the rule overrides, and only when it fires."""
    low = text.lower()
    return next((t for c, t in _stub._OBS_TARGETS if ((c in low) if isinstance(c, str) else c.search(low))), "")


_stub._tin_clause_first("warm up")                                   # compiles the pattern (lazy import of literal_will._NOT_NOUN)
check(_stub._TIN_CLAUSE_RX is not None and _stub._TIN_CLAUSE_RX.pattern.startswith(LW._NOT_NOUN),
      "the rule's verb is guarded by literal_will._NOT_NOUN -- the same noun guard the gate and hands.wants() use (no drift)")
check(tuple(_stub._TIN_LOOK_VERBS) == tuple(look_row["verbs"]), f"the rule's verbs are the look row's own: {look_row['verbs']}")
_tin_words = [w for w in look_row["grammar_only"] if "tin" in w or "packet" in w]
check(len(_tin_words) == 8 and all(re.search(_stub._TIN_GATE_WORDS, f" {w} ") for w in _tin_words),
      f"every tin/packet grammar_only word on the look row satisfies the rule's word set: {_tin_words}")
check(not re.search(_stub._TIN_GATE_WORDS, " tin ") and not re.search(_stub._TIN_GATE_WORDS, " the tin roof ")
      and not re.search(_stub._TIN_GATE_WORDS, " the tin of matches ") and not re.search(_stub._TIN_GATE_WORDS, " the match tin "),
      "bare 'tin', 'the tin roof', 'the tin of matches', 'the match tin' are NOT in the rule's word set (the gate's residual stays out)")
_same = [(c if isinstance(c, str) else c.pattern, t) for c, t in _stub._OBS_TARGETS]
check(len(_same) == 77 and _same[-1][1] == "dented tin" and all(isinstance(c, str) for c, _ in _stub._OBS_TARGETS[:-1]),
      "the cue table is untouched by the rule: 77 cues, the tin cue still last, every other cue a plain string (no reorder)")
# the rule FIRES: the verb's own clause reaches the tin word, an earlier cue elsewhere in the thought no longer wins
for p, was in (("i look at the dented tin and the sea", "sea"), ("i want to look at the dented tin and the sea.", "sea"),
               ("the thyme scent hangs heavy. travis asks me to look at the tin beside us", "thyme"),
               ("only the flag's drag remains. i hear the wood pigeon and look down at the dented tin beside me", "letterbox"),
               ("i watch the dented tin rest still beside me. the book offers a different presence", "book"),
               ("i stand on the shingle. the dream fades as i look at the dented tin beside me", "shore"),
               ("i see the packets by the fire", "fire"), ("i observe my tin near the gate", "letterbox"),
               ("the cat sleeps. i look at this tin, then that tin", "cat"), ("by the garden i watch the seed tin", "garden")):
    check(_stub._observe_target(p) == "dented tin" and j1764_walk(p) == was,
          f"_observe_target({p!r}) == 'dented tin' (the table walk alone gave {was!r})")
# the rule does NOT fire: a scenery mention of the tin while looking at something else keeps its own resolution
for p, want in (("the wind rattles the tin container again, mixing with my own breath as i watch the grey sea rise. "
                 "i feel a gentle pull toward the shore where the surf awaits", "sea"),
                ("the dented tin rattles beside me. instead, i watch the shadow of the western cloud stretch across the floor", "sky"),
                ("i close the tin can beside me, the dent cold against my palm. i will tend the fire now, and watch it", "fire"),
                ("the wind rattles the tin box, but my mind is stuck on birds. i want to walk out to the garden and look", "garden"),
                ("i look at the fire. the dented tin and the sea", "sea"),                  # the verb's reach never crosses a sentence
                ("i look at the cat. the dented tin rattles", "cat"),                       # (the table walk: 'the sea' precedes 'the fire')
                ("a look at the dented tin and the sea", "sea"),                            # a NOUN 'look' (_NOT_NOUN), as at the gate
                ("i look at the tin roof and the sea", "sea"), ("i look at the tin of matches by the fire", "fire"),
                ("i look at the match tin by the fire", "fire"), ("i look at the tinder and the sea", "sea"),
                ("the dented tin and the sea", "sea")):
    check(_stub._observe_target(p) == want == j1764_walk(p), f"_observe_target({p!r}) == {want!r} (unchanged: no look verb reaches a tin word)")
check(_stub._observe_target("i look at the dented tin") == "dented tin" == j1764_walk("i look at the dented tin"),
      "a thought no other cue claims resolves to the tin exactly as the J-1764 cue already did")
# DOCUMENTED RESIDUAL, pinned so a change is noticed: the reach is the gate's own (<=50 chars inside the sentence), so a look at
# the sea whose SAME sentence goes on to name the tin within reach reads as a tin look here, exactly as the gate reads it as a
# tin-reaching look deed. Zero such rows among the 13 real scenery-mention look deeds in the corpus replay (J-1835); D-0348's
# own defeater (a false tin look live) is the read that would surface one.
check(_stub._observe_target("i look at the sea while the dented tin rattles") == "dented tin",
      "(known residual) 'i look at the sea while the dented tin rattles' -> 'dented tin': the verb's 50-char reach is the gate's own")
# end to end, with the earlier cue in the same thought: the tin is named where it lies, and NOTHING more where it does not
ans, seen = willed("I look at the dented tin and the sea.", loc="wood", tin_place="wood")
check(any(f == "look" and "hinged lid" in a for f, a in ans) and seen[-1][0] == "dented tin",
      "wood, tin lying here: 'I look at the dented tin and the sea.' names the tin (target 'dented tin')")
for loc in ("study", "garden", "shore", "wood"):
    others = [pl for pl in ("study", "garden", "shore", "wood") if pl != loc]
    answers = {pl: ([a for f, a in willed("I look at the dented tin and the sea.", loc=loc, tin_place=pl)[0] if f == "look"] or [None])[0]
               for pl in others}
    check(all(a is not None for a in answers.values()) and len(set(answers.values())) == 1
          and next(iter(answers.values())) == structured("dented tin", loc=loc, tin_place=others[0]),
          f"{loc}: tin lying elsewhere, the clause-first look answers byte-for-byte sensorium.look('dented tin') whichever of {others} holds it (no hint)")
check(_stub._observe_target("i look at the dented tin and the garden", cur_loc="shore") == "dented tin",
      "_observe_journal's cur_loc guard: the tin target has no home, so the header is 'observed the dented tin' (not dropped as 'garden' would be)")

print("\n[8] isolation proof")
_after = _snap()
for name in _BEFORE:
    check(_BEFORE[name] == _after[name], f"live data/{name} untouched {_after[name]}")
escaped = [f"{m.__name__}.{a}" for m, a in _REDIRECTS if not str(getattr(m, a)).startswith(str(TMP))]
check(not escaped, f"every redirected store path is inside the temp dir ({len(_REDIRECTS)} checked){' ESCAPED: ' + str(escaped) if escaped else ''}")

print(f"\n{'ALL OK' if not fails else str(fails) + ' FAILURE(S)'}  (stores: {TMP})")
sys.exit(1 if fails else 0)
