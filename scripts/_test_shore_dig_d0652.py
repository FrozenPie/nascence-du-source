"""
Shore dig / turn-stone / open-shell hand test (D-0652, J-3261; core/shore_dig.py + shore_life.dig_sand/turn_stone/open_shell).
ISOLATED like the bestiary P1-P3 tests: every life and shore store is redirected into a temp dir; live data/ is only read.
Proves: the hand does not exist with the flag off; the three hands' first-person grammar; the tide / season / hour gates; a known
(site, tide, bucket) gives the expected set; a find is composed, nameless, credited as a sighting, and a book then names it (D-0129);
the traces (mound, cast, dead test) are untouched and still found by a look at the place; the pea crab only from a held mussel.
Run:  python scripts/_test_shore_dig_d0652.py
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


TMP = Path(tempfile.mkdtemp(prefix="shore_dig_"))
print("isolated store dir:", TMP)
from core import life                                              # noqa: E402
life._F, life._LEDGER, life._EVENTS = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl"
life._DATA = TMP
life._FLAGS_F = TMP / "life_flags.json"
from core import life_shore as LS, shore_dig as SD, shore_life as SL, world_clock, sensorium   # noqa: E402
SL._F, SL._EVENTS, SL._LEDGER = TMP / "shore_life.json", TMP / "shore_events.jsonl", TMP / "shore_ledger.jsonl"
sensorium.state["location"] = "shore"


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
LOW = find(lambda t: world_clock.tide(t)["level"] <= 0.25 and life._phase(t) == "day")
HIGH = find(lambda t: world_clock.tide(t)["level"] > 0.7 and life._phase(t) == "day")
NIGHT = find(lambda t: life._phase(t) == "night" and world_clock.tide(t)["level"] <= 0.25)
print("low-tide day:", time.strftime("%Y-%m-%d %H:%M", time.localtime(LOW)))

# make every registered row present (activity is the engine's own; we pin it so the test is about the hand, not today's weather)
_orig_act = life.activity
PRESENT = [0.9]
life.activity = lambda r, p, n=None: PRESENT[0] if r.get("obs") else _orig_act(r, p, n)

print("-- 1. the flag: with it off the hand does not exist")
fresh()
check("enabled() False with no flag", SD.enabled() is False)
check("act_from_thought does not answer a dig with the flag off",
      SL.act_from_thought("i dig the sand with my hands", "dig the sand") is None)
check("dig_sand returns '' with the flag off", SL.dig_sand("") == "")
fresh(shore_bestiary=True)
check("enabled() True with the flag", SD.enabled() is True)

print("-- 2. grammar: his will, not the scene")
yes = {"dig_sand": ["i dig the sand with my hands", "i want to dig into the wet sand", "let me dig the sand at the edge"],
       "turn_stone": ["i will turn over a stone at the water's edge", "i turn over the stones by the pool"],
       "open_shell": ["let me open the shell", "i open the shell with my knife"]}
no = ["the gull hammers a shell open", "the stones turn over endlessly", "i watch the buzzard's talons dig into the wet sand",
      "i feel the weight of silence breaking open the shell", "the tide turns over the stones"]
for name, ts in yes.items():
    check(f"{name}: his own will reads", all(SL._wills_dig_shore(t, name) for t in ts), str([t for t in ts if not SL._wills_dig_shore(t, name)]))
check("scene sentences (gull, stones turning, a buzzard) read as none of the three",
      not any(SL._wills_dig_shore(t, n) for t in no for n in yes), str([(t, n) for t in no for n in yes if SL._wills_dig_shore(t, n)]))

print("-- 3. gates: tide, night, tiredness, no shell")
st = {}
check("high tide: the flat is under the sea, nothing found, no bucket spent", SD.dig("sand", st, HIGH).startswith("The flat is under") and not st.get("dig_n"))
check("night: refused, in the world's words", SD.dig("sand", {}, NIGHT) == SD._NIGHT)
st = {}
for i in range(SD.MAX_DIGS_PER_BUCKET):
    SD.dig("sand", st, LOW)
check("a fifth dig in ten minutes: tired", SD.dig("sand", st, LOW) == SD._TIRED)
check("no mussel held: nothing to open", SL.open_shell("") == SD._NO_SHELL)

print("-- 4. what a dig finds depends on place and tide")
sand_keys = {c["key"] for c in SD.candidates("sand", LOW)}
wet_keys = {c["key"] for c in SD.candidates("wet", LOW)}
stone_keys = {c["key"] for c in SD.candidates("stone", LOW)}
check("the flat dig can turn up the burrowers of the flat", {"pipi", "cockle", "lugworm", "ghost_shrimp", "heart_urchin"} <= sand_keys, str(sand_keys))
check("the water's edge dig turns up the tuatua, which the flat does not", "tuatua" in wet_keys and "tuatua" not in sand_keys, str((wet_keys, sand_keys)))
check("a stone turns up the ragworm and nothing else", stone_keys == {"ragworm"}, str(stone_keys))
check("pea crab is not in any sand or stone dig", "pea_crab" not in sand_keys | wet_keys | stone_keys)
PRESENT[0] = 0.0
check("nothing present (season, hour, weather) -> nothing to find, whatever the roll", SD.candidates("sand", LOW) == [])
PRESENT[0] = 0.9
# deterministic: same state, same bucket -> same answer
a = SD.dig("sand", {}, LOW); b = SD.dig("sand", {}, LOW)
check("the same bucket and the same dig number answer the same", a == b)
found_keys = set()
for k in range(240):
    c = SD.pick("sand", random.Random(f"t:{k}"), LOW)
    if c: found_keys.add(c["key"])
check("over many digs every flat burrower is reachable", {"pipi", "cockle", "toheroa", "lugworm", "ghost_shrimp", "heart_urchin", "sand_dollar", "ragworm", "sand_sea_cucumber"} <= found_keys, str(found_keys))
found_wet = set()
for k in range(240):
    c = SD.pick("wet", random.Random(f"w:{k}"), LOW)
    if c: found_wet.add(c["key"])
check("the tuatua turns up at the water's edge", "tuatua" in found_wet, str(found_wet))

print("-- 5. a find: composed, nameless, credited")
terms = LS.forbidden_terms()
bad = []
for site in ("sand", "wet", "stone", "shell"):
    for key in SD.FINDS[site]:
        r = life._ROWS.get(key)
        if not r:
            bad.append(("unregistered", key)); continue
        text = SD.line_for({"key": key, "row": r, "act": 0.9, "p": 0.5}, site)
        leaks = LS.leak_scan(text, terms)
        if leaks:
            bad.append((key, site, leaks[:3]))
check("every dug line, every site, names nothing (leak test over all FINDS)", not bad, str(bad[:4]))
for k in SD.DUG_OBS:
    try:
        LS.make_obs(**SD.DUG_OBS[k]); ok = True
    except Exception as exc:
        ok = False
    check(f"DUG_OBS[{k}] is valid in the closed vocabularies", ok)
life.RENDER = True
clear = lambda: [(TMP / n).write_text("", encoding="utf-8") for n in ("life_events.jsonl", "life_ledger.jsonl")]
clear()
c = {"key": "lugworm", "row": life._ROWS["lugworm"], "act": 0.9, "p": 0.5}
txt = SD.line_for(c, "sand")
check("the lugworm dug is the worm, not its cast", "worm" in txt.lower() or "segmented" in txt.lower() or "limbless" in txt.lower(), txt)
check("credit_find credits a sighting and logs an answer", life.credit_find("lugworm", "shore", LOW, txt) is True
      and any(r.get("kind") == "sighting" and r.get("key") == "lugworm" for r in _read("life_ledger.jsonl"))
      and any(e.get("resolved") == "dug" for e in _read("life_events.jsonl")))
check("a name still needs a book AND a face (D-0129): a book now names it",
      "lugworm" in life.learn_from_text("The lugworm lives in a burrow in the sand and leaves a cast; fishermen dig it for bait."))
check("credit_find on an unregistered key credits nothing", life.credit_find("no_such_row", "shore", LOW, "") is False)

print("-- 6. the traces are kept")
r_mound, r_cast, r_test = life._ROWS["ghost_shrimp"], life._ROWS["lugworm"], life._ROWS["heart_urchin"]
check("the sign rows are unchanged: mound, coil of sand, dead test",
      (r_mound["obs"]["shape"], r_cast["obs"]["shape"], r_test["obs"]["shape"]) == ("mound_hole", "sand_coil", "egg_fragile"),
      str((r_mound["obs"]["shape"], r_cast["obs"]["shape"], r_test["obs"]["shape"])))
before = json.dumps({k: life._ROWS[k]["obs"] for k in ("ghost_shrimp", "lugworm", "heart_urchin")}, sort_keys=True)
for _ in range(10):
    SD.dig("sand", {}, LOW)
after = json.dumps({k: life._ROWS[k]["obs"] for k in ("ghost_shrimp", "lugworm", "heart_urchin")}, sort_keys=True)
check("digging never alters a registered row", before == after)
LS.current_standpoint = lambda place="shore": "on_the_sand"
seen_signs = set()
for k in range(60):
    for f in LS.discover("the sand", "shore", LOW + 600 * k):
        seen_signs.add(f["row"]["key"])
check("a look at the sand still shows a sign (a burrower row) before he digs", bool(seen_signs & {"ghost_shrimp", "lugworm", "heart_urchin", "pipi", "cockle", "sand_dollar"}), str(seen_signs))

print("-- 7. the pea crab: only from a mussel he holds")
d = SL._load(); d["mussels_held"] = 0; SL._save(d)
check("no mussel, no pea crab", SL.open_shell("") == SD._NO_SHELL)
d = SL._load(); d["mussels_held"] = 2; SL._save(d)
shell_hits = 0
for k in range(300):
    c = SD.pick("shell", random.Random(f"s:{k}"), LOW)
    shell_hits += bool(c)
check("a held mussel gives a pea crab about one time in eight, never always", 10 <= shell_hits <= 80, str(shell_hits))
out = SL.open_shell("")
d = SL._load()
check("opening spends the mussel", d.get("mussels_held") == 1, str(d.get("mussels_held")))

print("-- 8. through the hand end to end (low tide, flag on)")
real_dig = SD.dig
SD.dig = lambda site, state, now=None, rng=None: real_dig(site, state, LOW, rng)
SL._standpoint = lambda: "on_the_sand"
out = SL.act_from_thought("i want to dig into the wet sand", "dig the sand", "shore")
check("act_from_thought answers a willed dig with a world line", isinstance(out, str) and len(out) > 20, repr(out))
check("the dig is logged as a deed", any(r.get("deed") == "dig" for r in _read("shore_ledger.jsonl")))
check("the deed is told to the life engine (note_deed)", any(k.startswith("dig@shore") for k in (life._load().get("deeds") or {})))
SD.dig = real_dig

print("\nALL OK" if not FAILS else f"\n{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
