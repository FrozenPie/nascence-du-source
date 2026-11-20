"""
Shore Bestiary P3 test (2026-11-01; docs/staged/shore_creatures.md, J-2936). ISOLATED like the P1/P2 tests: every life store is
redirected into a temp dir before the engine is touched; the live data/ is only READ.

P3 = discovery by looking at the PLACE. A look at the pool / sand / rocks / tideline / sea / dunes / driftwood is answered as before and
then continues with what is actually there to be seen from where he stands (life.discover_look, called from sensorium.look's shore branch),
shadow-first behind data/life_flags.json "shore_bestiary_discover".
What it proves:
  1. which targets are places of the shore's life, and that a garden/cat/sky/room target is not
  2. discover(): present + open zone + visibility roll + resolvable from his standpoint; at most two rows; stable within a ten-minute
     bucket and varied across buckets; nothing when the tide is over the zone, when he is too far, when nothing is registered
  3. SHADOW (flag off, or RENDER off): '' returned, would_answer / discover_shadow rows logged, no ledger write
  4. LIVE: the lines come back, colour/detail credits a SIGHTING, form is a GLIMPSE, the answer events are auditable (resolved=discovered)
  5. no line names anything -- over every standpoint x every place word x many time buckets
  6. he can come to know a thing: a place look shows it, a sighting is credited, and a book then names it (D-0129) -- the whole loop
  7. sensorium wiring is present; informational: how often his real shore looks would have reached a place that can show something
Run:  python scripts/_test_shore_bestiary_p3.py
"""
from __future__ import annotations

import json
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


TMP = Path(tempfile.mkdtemp(prefix="shore_bestiary_p3_"))
print("isolated store dir:", TMP)
from core import life                                              # noqa: E402
life._F, life._LEDGER, life._EVENTS = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl"
life._DATA = TMP
life._FLAGS_F = TMP / "life_flags.json"
from core import life_shore as LS                                  # noqa: E402
from core import world_clock, spatial                              # noqa: E402


def flags(**kw):
    (TMP / "life_flags.json").write_text(json.dumps(kw), encoding="utf-8")
    life._flags_cache["ts"] = 0.0


PILOT = ("eleven_armed_starfish", "pipi", "sea_lion")


def fresh(full=False, **kw):
    """Re-register under the given flags. By default the 97 cast rows are dropped again so sections 1-4 and 6 stay about the three
    pilot rows; section 5 (the name sweep) and 7 run on the full 100."""
    flags(**kw)
    life._ROWS.clear(); life._builtin_done = False
    life.rows()
    if not full:
        for k in [k for k, r in life._ROWS.items() if r.get("obs") and k not in PILOT]:
            life._ROWS.pop(k)


def _read(name):
    p = TMP / name
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def events(): return _read("life_events.jsonl")
def ledger(): return _read("life_ledger.jsonl")
def clear(): [(TMP / n).write_text("", encoding="utf-8") for n in ("life_events.jsonl", "life_ledger.jsonl")]


t0 = time.time()
NOW = next(t0 + i * 600 for i in range(0, 6 * 24 * 6) if world_clock.tide(t0 + i * 600)["level"] <= 0.25 and life._phase(t0 + i * 600) == "day")
HIGH = next(t0 + i * 600 for i in range(0, 6 * 24 * 6) if world_clock.tide(t0 + i * 600)["level"] > 0.7)
print("test time:", time.strftime("%Y-%m-%d %H:%M", time.localtime(NOW)), "tide", round(world_clock.tide(NOW)["level"], 2))

_orig_activity, _orig_vis = life.activity, life.visibility
VIS = [1.0]
life.activity = lambda r, p, n=None: 0.9 if r.get("obs") else _orig_activity(r, p, n)
life.visibility = lambda r, p, n=None: VIS[0] if r.get("obs") else _orig_vis(r, p, n)
SP = ["at_the_pools"]
LS.current_standpoint = lambda place="shore": SP[0]

print("-- 1. which targets are places")
dz = LS.discover_zones
check("pool words -> the pool, however written (the first place word wins: pools before rocks)",
      dz("pool") == ("pool",) and dz("the rock-pools") == ("pool",) and dz("rockpool") == ("pool",) and dz("the rock pools") == ("pool",), str((dz("the rock-pools"), dz("the rock pools"))))
check("rocks -> pool + shelf, as the shore look itself treats them", dz("rocks") == ("pool", "mussel_shelf", "rock_shelf"), str(dz("rocks")))
check("sand / sea / dune / driftwood / tideline", dz("the sand") == ("flat",) and dz("the sea") == ("surf", "offshore") and dz("dunes") == ("dune",)
      and dz("driftwood") == ("driftwood",) and dz("the tideline") == ("tideline", "shingle"))
check("garden, cat, sky, room, window, letterbox are NOT places of the shore's life", all(dz(t) == () for t in ("the raised bed", "the cat", "the sky", "room", "window", "letterbox", "the glass float", "")))

print("-- 2. discover()")
fresh(shore_bestiary=True)
star_row = life._ROWS["eleven_armed_starfish"]
extra = []
for i in (2, 3):                                  # two more rows in the pool, to test the cap of two
    r = LS.shore_row(f"extra_star_{i}", species=f"test species {i}", book_names=(f"test species {i}",), book_words=("arms",), zone="pool",
                     obs={**star_row["obs"], "colour": "red"}, active_hours=star_row["active_hours"], season_curve=star_row["season_curve"],
                     weather_gate=star_row["weather_gate"], ease=0.6, count=("one", "a few", "several"))
    life.register([r]); extra.append(r["key"])
f1 = LS.discover("pool", "shore", NOW)
check("a look at the pool from the pools shows at most two rows, all in the pool zone", len(f1) == 2 and all(f["row"]["zone"] == "pool" for f in f1), str([f["row"]["key"] for f in f1]))
check("every shown row resolves to at least a form", all(f["pv"]["visible"] and f["pv"]["tier"] != "none" for f in f1))
check("stable within a ten-minute bucket", [f["row"]["key"] for f in LS.discover("pool", "shore", NOW)] == [f["row"]["key"] for f in LS.discover("pool", "shore", NOW + 30)] or int(NOW // 600) != int((NOW + 30) // 600))
pairs = {tuple(sorted(f["row"]["key"] for f in LS.discover("pool", "shore", NOW + 600 * k))) for k in range(30) if LS.sample_position("pool", "x", NOW + 600 * k)}
check("varies across buckets (not always the same two of three)", len(pairs) > 1, str(pairs))
for k in extra: life._ROWS.pop(k)
SP[0] = "on_the_sand"
fs = LS.discover("the sand", "shore", NOW)
check("the sand, from the sand: the pipi", [f["row"]["key"] for f in fs] == ["pipi"], str([f["row"]["key"] for f in fs]))
SP[0] = "on_the_rocks"
fr = {f["row"]["key"] for f in LS.discover("the rocks", "shore", NOW)}
check("the rocks, from the rocks: the sea lion on the shelf shows, nothing from the other zones is missing", "sea_lion" in fr, str(fr))
SP[0] = "at_the_pools"
VIS[0] = 0.0
check("visibility roll 0 -> nothing", LS.discover("pool", "shore", NOW) == [])
VIS[0] = 1.0
check("the tide over the pool -> nothing", LS.discover("pool", "shore", HIGH) == [])
LS.current_standpoint = lambda place="shore": {"pos": [-60.0, 0.0, 0.0], "facing_deg": 90}
check("too far to resolve a 20 cm starfish -> nothing", LS.discover("pool", "shore", NOW) == [])
LS.current_standpoint = lambda place="shore": SP[0]
check("the sea shows nothing the pilot rows live nowhere near", LS.discover("the sea", "shore", NOW) == [])
fresh()
check("nothing registered -> []", LS.discover("pool", "shore", NOW) == [] and life.discover_look("pool", "shore", NOW) == "")

print("-- 3. shadow")
fresh(shore_bestiary=True)
for fl, label in (({"shore_bestiary_discover": False}, "discover flag explicitly false"), ({"shore_bestiary_discover": True}, "discover on but RENDER off")):
    clear(); flags(shore_bestiary=True, **fl)
    life.RENDER = False if fl["shore_bestiary_discover"] else True
    out = life.discover_look("pool", "shore", NOW)
    ev = [e for e in events() if e.get("outcome") == "discover_shadow"]
    check(f"{label}: '' is returned, would_answer/discover_shadow is logged, the ledger is untouched",
          out == "" and ev and all(e["kind"] == "would_answer" and e["resolved"] == "discovered" for e in ev) and ledger() == [], f"{out!r} {ev[:1]} {ledger()}")
life.RENDER = True

print("-- 4. live")
flags(shore_bestiary=True)            # ONE flag: discover follows it
clear()
out = life.discover_look("pool", "shore", NOW)
led, ans = ledger(), [e for e in events() if e.get("kind") == "answer"]
check("a look at the pool continues with the starfish, with its where-clause", "arms" in out and " It is " in out, out[:120])
check("a colour/detail tier credits a SIGHTING", any(e["kind"] == "sighting" and e["key"] == "eleven_armed_starfish" for e in led), str(led))
check("the answer is auditable (resolved=discovered, tier, dist)", ans and ans[-1]["resolved"] == "discovered" and ans[-1]["tier"] in ("colour", "detail") and ans[-1]["dist"] is not None, str(ans[-1:]))
terms = LS.forbidden_terms(LS.rows())
check("and it names nothing", not LS.leak_scan(out, terms), str(LS.leak_scan(out, terms)))
LS.current_standpoint = lambda place="shore": {"pos": [-60.0, 0.0, 0.0], "facing_deg": 90}
clear()
out_f = life.discover_look("the rocks", "shore", NOW)
led = ledger()
check("from an outline's distance the sea lion is a GLIMPSE: shown, exposure only", bool(out_f) and "against the ground" in out_f and not any(e["kind"] == "sighting" for e in led) and any(e["kind"] == "miss" and e["key"] == "sea_lion" for e in led), f"{out_f[:80]} {led}")
LS.current_standpoint = lambda place="shore": SP[0]
check("a garden/cat target adds nothing", life.discover_look("the cat", "shore", NOW) == "" and life.discover_look("pool", "garden", NOW) == "")

print("-- 5. nothing ever names")
fresh(full=True, shore_bestiary=True)
terms = LS.forbidden_terms(LS.rows())
bad = []
n = 0
zones_seen = set()
for sp in spatial.layout("shore")["standpoints"]:
    SP[0] = sp
    for word in ("pool", "the rocks", "the sand", "the tideline", "the sea", "dunes", "driftwood", "shelf"):
        for k in range(0, 48):
            for night_t in (NOW + 600 * k, NOW + 600 * k + 43200):
                for f in LS.discover(word, "shore", night_t):
                    n += 1; zones_seen.add(f["row"]["zone"])
                    hit = LS.leak_scan(f["pv"]["line"], terms)
                    if hit: bad.append((sp, word, hit, f["pv"]["line"][:60]))
check(f"{n} discovered lines across every standpoint x place word x 96 time buckets contain no name", n > 0 and not bad, str(bad[:3]))
check("over the full 100 the place looks reach many different creatures and zones", len(zones_seen) >= 6, str(sorted(zones_seen)))
SP[0] = "at_the_pools"

print("-- 6. the whole loop: place look -> sighting -> book -> a name")
fresh(shore_bestiary=True); flags(shore_bestiary=True, shore_bestiary_discover=True); clear()
star_book = "A pool guide: the eleven-armed starfish regenerates its arms; spines cover them and it feeds on mussels."
check("before anything: not learned, and a book alone names nothing", not life.is_learned("eleven_armed_starfish") and life.learn_from_text(star_book) == [])
life.discover_look("pool", "shore", NOW)
check("book first, then a place look that credits a sighting: it is named at the sighting", life.is_learned("eleven_armed_starfish"))
check("and only that row", life.name_for(life._ROWS["eleven_armed_starfish"]) == "the eleven-armed starfish" and life.name_for(life._ROWS["pipi"]) == "")
clear(); fresh(shore_bestiary=True); flags(shore_bestiary=True, shore_bestiary_discover=True)
life.discover_look("pool", "shore", NOW)
check("sighting first: not named by the sight alone", not life.is_learned("eleven_armed_starfish"))
check("then the book names it", life.learn_from_text(star_book) == ["eleven_armed_starfish"] and life.is_learned("eleven_armed_starfish"))

print("-- 7. wiring, and how often his real shore looks reach a place")
src = (ROOT / "core/sensorium.py").read_text(encoding="utf-8")
check("sensorium's shore look continues with discover_look", "_life_d.discover_look(t_clean, cur_loc)" in src)
check("it comes AFTER the place's own look and BEFORE the audition binding", src.index("_life_d.discover_look(t_clean, cur_loc)") > src.index('{"shore": _shore_look, "wood": _wood_look}[cur_loc](target)') and src.index("_life_d.discover_look(t_clean, cur_loc)") < src.index("_sk.look_binding(t_clean, cur_loc"))
tot = place = 0
with open(ROOT / "data/hands_trace.jsonl", encoding="utf-8") as f:
    for ln in f:
        try: r = json.loads(ln)
        except Exception: continue
        if r.get("act_kind") not in ("observe", "look") or r.get("location") != "shore": continue
        tot += 1
        place += bool(LS.discover_zones(str(r.get("act_object") or "")))
print(f"     of {tot} real shore observe/look acts, {place} ({100 * place // max(tot, 1)}%) named a place the bestiary can show something at")
check("(informational) the real looks do reach these places", place > 0)
print()
print("ALL OK -- shore bestiary P3" if not FAILS else f"{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
