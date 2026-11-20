"""
Wood turn-stone / peel-bark hand test (D-0714, J-3812; core/wood_dig.py + wood_life.wood_dig / _wills_wood_dig).
ISOLATED like the bestiary tests: every life and wood store is redirected into a temp dir; live data/ is only read.
Proves: the hand does not exist with the flag off; first-person grammar with his "turning over the same stones" idiom vetoed; the site
choice; the hour/season/weather gate (present by life.activity only); the North-Island rows are never dug up; every FINDS key is a real row;
a find is composed, nameless, credited as a sighting, and a book then names it (D-0129); the sign/trace rows are untouched.
Run:  python scripts/_test_wood_dig_d0714.py
"""
from __future__ import annotations

import json
import random
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0


def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))


TMP = Path(tempfile.mkdtemp(prefix="wood_dig_"))
print("isolated store dir:", TMP)
from core import life                                              # noqa: E402
life._F, life._LEDGER, life._EVENTS = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl"
life._DATA = TMP
life._FLAGS_F = TMP / "life_flags.json"
from core import life_shore as LS, life_wood as LW, wood_dig as WD, wood_life as WL, sensorium   # noqa: E402
WL._F, WL._LEDGER = TMP / "wood_life.json", TMP / "wood_ledger.jsonl"
sensorium.state["location"] = "wood"


def flags(**kw):
    (TMP / "life_flags.json").write_text(json.dumps(kw), encoding="utf-8")
    life._flags_cache["ts"] = 0.0


def fresh(**kw):
    flags(**kw)
    life._ROWS.clear(); life._builtin_done = False
    life.rows()


def _read(name):
    p = TMP / name
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


t0 = time.time()
step = 600
def find(pred):
    return next(t0 + i * step for i in range(0, 6 * 24 * 30) if pred(t0 + i * step))
DAY = find(lambda t: life._phase(t) == "day")
NIGHT = find(lambda t: life._phase(t) == "night")

_orig_act = life.activity
PRESENT = [0.9]
life.activity = lambda r, p, n=None: PRESENT[0] if r.get("obs") else _orig_act(r, p, n)

print("-- 1. the flag: with it off the hand does not exist")
fresh()
check("enabled() False with no flag", WD.enabled() is False)
check("act_from_thought does not answer a turned stone with the flag off", WL.act_from_thought("i turn over a stone", "turn over the stone", "wood_dig") is None)
check("wood_dig returns '' with the flag off", WL.wood_dig("") == "")
fresh(wood_bestiary=True)
check("enabled() True with the flag", WD.enabled() is True)

print("-- 2. grammar: his will, not his idiom")
yes = ["i turn over a stone beside the path", "let me peel the bark off the dead branch", "i will turn over the stones by the stream",
       "i want to overturn a log", "i peel the loose bark from the deadfall"]
no = ["i am tired of turning over the same stones in my head", "the wind turns over the stones", "i am sick of turning over the same stones",
      "i turn over the same stones of logic", "the bark peels from the oak", "i will turn over the soil", "i watch the stones"]
check("his own will reads", all(WL._wills_wood_dig(t) for t in yes), str([t for t in yes if not WL._wills_wood_dig(t)]))
check("idiom, scene, other objects read as no will", not any(WL._wills_wood_dig(t) for t in no), str([t for t in no if WL._wills_wood_dig(t)]))
check("the family exists in the table and wood_life lists it", "wood_dig" in WL._WOOD_FAMILIES)
check("site: water words -> the stream", WD.site_for("turn over a stone in the stream") == "stream" and WD.site_for("turn over a stone by the spring") == "stream")
check("site: bark / log -> bark; else a floor stone", WD.site_for("peel the bark") == "bark" and WD.site_for("turn over a log") == "bark" and WD.site_for("turn over a stone") == "stone")

print("-- 3. the FINDS are real rows, South Island, and gated by the engine")
rowkeys = {r["key"] for r in LW.rows()}
missing = [(s, k) for s, d in WD.FINDS.items() for k in d if k not in rowkeys]
check("every FINDS key is a real wood row", not missing, str(missing))
check("no North-Island-only row is in any FINDS list", not [(s, k) for s, d in WD.FINDS.items() for k in d if k in WD.NORTH_ONLY])
cands = {s: {c["key"] for c in WD.candidates(s, DAY)} for s in WD.SITES}
check("each site has candidates when the rows are present", all(cands[s] for s in WD.SITES), str({s: len(v) for s, v in cands.items()}))
check("stream finds are stream things, bark finds are bark things (no crossover of the sets' signature rows)",
      "mayfly_nymph" in cands["stream"] and "mayfly_nymph" not in cands["stone"] and "pie_dish_beetle" in cands["bark"] and "pie_dish_beetle" not in cands["stream"])
PRESENT[0] = 0.0
check("nothing present (season, hour, weather) -> nothing to find, whatever the roll", all(WD.candidates(s, DAY) == [] for s in WD.SITES))
PRESENT[0] = 0.9
a = WD.dig("stone", {}, DAY); b = WD.dig("stone", {}, DAY)
check("the same bucket and the same turn number answer the same", a == b)
reach = {s: set() for s in WD.SITES}
for s in WD.SITES:
    for k in range(400):
        c = WD.pick(s, random.Random(f"{s}:{k}"), DAY)
        if c:
            reach[s].add(c["key"])
check("over many turns every row of every site is reachable", all(reach[s] >= set(WD.FINDS[s]) - WD.NORTH_ONLY for s in WD.SITES),
      str({s: sorted(set(WD.FINDS[s]) - reach[s]) for s in WD.SITES}))

print("-- 4. gates: night and tiredness")
check("night: refused in the world's words, no bucket spent", WD.dig("stone", (st := {}), NIGHT) == WD._NIGHT and not st.get("dig_n"))
st = {}
for i in range(WD.MAX_TURNS_PER_BUCKET):
    WD.dig("stone", st, DAY)
check("a fifth turn in ten minutes: tired", WD.dig("stone", st, DAY) == WD._TIRED)

print("-- 5. a find: composed, nameless, credited")
life.RENDER = True
terms = LS.forbidden_terms([life._ROWS[k] for k in {k for d in WD.FINDS.values() for k in d} if k in life._ROWS])
bad = []
for site, d in WD.FINDS.items():
    for key in d:
        r = life._ROWS.get(key)
        if not r:
            bad.append(("unregistered", key)); continue
        text = WD.line_for({"key": key, "row": r, "act": 0.9, "p": 0.5}, site)
        leaks = LS.leak_scan(text, terms)
        if leaks:
            bad.append((key, site, leaks[:3]))
check("every dug line, every site, names nothing (leak test over all FINDS)", not bad, str(bad[:4]))
for n in WD._NOTHING.values():
    check("the empty answers name nothing", not any(LS.leak_scan(s, terms) for s in n))
[(TMP / n).write_text("", encoding="utf-8") for n in ("life_events.jsonl", "life_ledger.jsonl")]
c = {"key": "stone_centipede", "row": life._ROWS["stone_centipede"], "act": 0.9, "p": 0.5}
txt = WD.line_for(c, "stone")
check("credit_find credits a wood sighting and logs an answer", life.credit_find("stone_centipede", "wood", DAY, txt) is True
      and any(r.get("kind") == "sighting" and r.get("key") == "stone_centipede" and r.get("place") == "wood" for r in _read("life_ledger.jsonl"))
      and any(e.get("resolved") == "dug" for e in _read("life_events.jsonl")))
check("a name still needs a book AND a face (D-0129): a book now names it",
      "stone_centipede" in life.learn_from_text("The stone centipede is a fast flat-bodied predator that hides under stones and logs in the damp leaf litter of the bush."))

print("-- 6. nothing is altered")
before = json.dumps({k: life._ROWS[k]["obs"] for k in ("pie_dish_beetle", "stone_centipede", "mayfly_nymph")}, sort_keys=True)
for _ in range(10):
    WD.dig("bark", {}, DAY)
check("turning never alters a registered row", before == json.dumps({k: life._ROWS[k]["obs"] for k in ("pie_dish_beetle", "stone_centipede", "mayfly_nymph")}, sort_keys=True))

print("-- 7. through the hand end to end (flag on, in the wood)")
real_dig = WD.dig
WD.dig = lambda site, state, now=None, rng=None: real_dig(site, state, DAY, rng)
out = WL.act_from_thought("i want to turn over a stone in the stream", "turn over the stone", "wood_dig")
check("act_from_thought answers a willed turn with a world line", isinstance(out, str) and len(out) > 20, repr(out))
check("the deed is logged", any(r.get("deed") == "turn_stone" for r in _read("wood_ledger.jsonl")))
check("the deed is told to the life engine (note_deed)", any(k.startswith("turn_stone@wood") for k in (life._load().get("deeds") or {})))
out2 = WL.act_from_thought("let me peel the bark off the deadfall", "", None)
check("unscoped (family None) also reaches it", isinstance(out2, str) and len(out2) > 20, repr(out2))
check("a scoped family that is not this one declines", WL.act_from_thought("i turn over a stone", "", "woodtool") is None)
sensorium.state["location"] = "study"
check("away from the wood it does not fire", WL.act_from_thought("i turn over a stone", "", "wood_dig") in (None, ""))
sensorium.state["location"] = "wood"
WD.dig = real_dig

print("\nALL OK" if not FAILS else f"\n{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
