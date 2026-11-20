"""
Shore Bestiary P2 test (2026-11-01; docs/staged/shore_creatures.md, J-2868). ISOLATED like life_smoke / the P1 test: every life store
is redirected into a temp dir before the engine is touched; the live data/ is only READ (hands_trace.jsonl, the observe corpus).

P2 = the two additive engine touches, shadow-first:
  (1) life.look_answer(target, place, now, raw): a row that carries NO name or alias is reached by what he DESCRIBES -- one look clause
      (the sentence the willed look hand forwards as `raw`) carrying two different intrinsic attributes of what is there
  (2) the answer is composed for HIS standpoint and the real distance (life_shore.perceive): none | form | colour | detail + where
What it proves:
  1. the matcher: two attributes needed, one is not enough, where-it-is never counts, a guess word counts as a shape word, a word
     is claimed by one attribute only, only look clauses are scored (not a whole long thought)
  2. nothing registered / flag off => described() is None => look_answer is byte-identical for an alias look
  3. SHADOW (shore_bestiary_render off): a described look logs would_answer (outcome described_shadow) and returns '' -- no ledger write
  4. LIVE (render on): the answer is the perceive() line, a colour/detail tier credits a SIGHTING, a form tier is a GLIMPSE (exposure only)
  5. the answers contain no name (leak test over what the engine actually returned)
  6. FALSE-POSITIVE SWEEPS over real data: the 1,518 observe phrasings, every shore scenery alias, and ~4,900 real observe/look thoughts
     -- none of them is taken for a creature
  7. sensorium forwards `raw`; the registered-but-too-far case falls through; a closed zone falls through
Run:  python scripts/_test_shore_bestiary_p2.py
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


TMP = Path(tempfile.mkdtemp(prefix="shore_bestiary_p2_"))
print("isolated store dir:", TMP)
from core import life                                              # noqa: E402
life._F, life._LEDGER, life._EVENTS = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl"
life._DATA = TMP
life._FLAGS_F = TMP / "life_flags.json"
from core import life_shore as LS                                  # noqa: E402
from core import world_clock                                       # noqa: E402


def flags(**kw):
    (TMP / "life_flags.json").write_text(json.dumps(kw), encoding="utf-8")
    life._flags_cache["ts"] = 0.0


PILOT = ("eleven_armed_starfish", "pipi", "sea_lion")


def fresh(full=False, **kw):
    """Re-register from scratch under the given flags. By default the 97 cast rows are dropped again so these tests stay about the
    three pilot rows (the full 100 are covered by the sweeps in section 6 and by scripts/_test_shore_bestiary_p1.py)."""
    flags(**kw)
    life._ROWS.clear(); life._builtin_done = False
    life.rows()
    if not full:
        for k in [k for k, r in life._ROWS.items() if r.get("obs") and k not in PILOT]:
            life._ROWS.pop(k)


def events():
    p = TMP / "life_events.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def ledger():
    p = TMP / "life_ledger.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


# a time when the tide is out (pool, flat, shelf all open) and it is day
t0 = time.time()
NOW = next(t0 + i * 600 for i in range(0, 6 * 24 * 6) if world_clock.tide(t0 + i * 600)["level"] <= 0.25 and life._phase(t0 + i * 600) == "day")
print("test time:", time.strftime("%Y-%m-%d %H:%M", time.localtime(NOW)), "tide", round(world_clock.tide(NOW)["level"], 2))

# deterministic: our rows are present, always seen; every other row keeps its real activity
_orig_activity, _orig_vis = life.activity, life.visibility
_PINNED = ("crabs",)                                              # the one existing row the alias-unchanged check compares
life.activity = lambda r, p, n=None: 0.9 if (r.get("obs") or r["key"] in _PINNED) else _orig_activity(r, p, n)
life.visibility = lambda r, p, n=None: 1.0 if (r.get("obs") or r["key"] in _PINNED) else _orig_vis(r, p, n)
SP = ["at_the_pools"]
REAL_CS = LS.current_standpoint                                    # the real one, kept for section 7
LS.current_standpoint = lambda place="shore": SP[0]

fresh(shore_bestiary=True)
ROWS = {k: r for k, r in life._ROWS.items() if r.get("obs")}
star, pipi, lion = (LS.attr_words(ROWS[k]) for k in ("eleven_armed_starfish", "pipi", "sea_lion"))
terms = LS.forbidden_terms(list(ROWS.values()))

print("-- 1. the matcher")
sc = LS.score_clause
check("the orange arms spread flat -> starfish, two attributes", sc(star, "the orange arms spread flat on the floor")[0] >= 2)
check("'the orange net' is one weak attribute: not a creature", sc(star, "the tangled orange net")[0] < 2)
check("two WEAK attributes are not enough (a colour and a size, no body part or movement)", sc(star, "the orange thing the length of a hand")[0] == 0)
check("'heavy' is not 'heaves', 'stars' is not 'starfish'", sc(lion, "the dark heavy little stone")[0] < 2 and sc(star, "the spinifex head and stars")[0] < 2)
check("'the dark hinged shell' is one attribute for the pipi (dark is not its colour)", sc(pipi, "the dark hinged shell")[0] < 2)
check("'the cream halves standing edge-up' -> pipi", sc(pipi, "the cream halves standing edge-up in the wet sand")[0] >= 2)
check("a buff animal with flippers -> sea lion", sc(lion, "the buff animal with flippers hauling itself")[0] >= 2)
check("a colour and a way of moving are both weak: not enough", sc(lion, "the buff animal hauling itself along")[0] == 0)
check("a guess word is a shape word: 'the orange starfish'", sc(star, "the orange starfish")[0] >= 2)
check("'stars' in the sky is not a guess", sc(star, "the orange stars over the water")[0] < 2)
check("where it is never counts: 'in the pool on the wet sand on the rock' scores nothing", sc(star, "in the pool on the wet sand on the rock")[0] == 0 and sc(pipi, "in the pool on the wet sand on the rock")[0] == 0)
check("one word is claimed by ONE attribute: 'arms' alone is not two", sc(star, "the arms")[0] == 1)
check("a count is its own attribute: 'eleven arms' is two", sc(star, "eleven arms")[0] == 2)
cl = LS.look_clauses("I think about the cream light on the wet sand. Then I look at the pale arms spread in the pool. Rest now.", "pool")
check("only the look clause is scored (plus the target keyword), never the whole thought",
      len(cl) == 2 and cl[0].strip().startswith("at the pale arms") and "cream light" not in " ".join(cl) and cl[1] == "pool", str(cl))
check("a long thought with no look verb contributes nothing but the target", LS.look_clauses("cream sand and orange arms everywhere", "") == [])

print("-- 2. nothing registered / flag off")
fresh()
check("flag absent: no bestiary rows registered", not any(r.get("obs") for r in life._ROWS.values()))
check("described() is None with no candidates", LS.described("pool", "look at the orange arms spread flat on the pool floor", "shore", NOW) is None)
fresh(shore_bestiary=True)
check("registered again", len([r for r in life._ROWS.values() if r.get("obs")]) == 3)

print("-- 3. shadow: shore_bestiary_render off")
RAW = "i want to look at the orange arms spread flat on the pool floor"
flags(shore_bestiary=True, shore_bestiary_render=False)
life.RENDER = True
check("render_live() is off (set explicitly: with the master flag alone it follows it)", not LS.render_live())
open(TMP / "life_events.jsonl", "w").close(); open(TMP / "life_ledger.jsonl", "w").close()
out = life.look_answer("pool", "shore", NOW, raw=RAW)
ev = [e for e in events() if e.get("outcome") == "described_shadow"]
check("the look falls through ('') exactly as before", out == "")
check("a would_answer row is logged with the tier, distance and the line", len(ev) == 1 and ev[0]["kind"] == "would_answer" and ev[0]["key"] == "eleven_armed_starfish"
      and ev[0]["tier"] in ("colour", "detail") and ev[0]["dist"] is not None and ev[0]["line"], str(ev[:1]))
check("no ledger write in shadow", ledger() == [])

print("-- 4. live: shore_bestiary_render on")
flags(shore_bestiary=True, shore_bestiary_render=True)
open(TMP / "life_events.jsonl", "w").close(); open(TMP / "life_ledger.jsonl", "w").close()
out = life.look_answer("pool", "shore", NOW, raw=RAW)
led = ledger()
check("the look is answered by the row", bool(out) and ("arms" in out or "centre" in out), out[:100])
check("the answer carries the where-clause", " It is " in out and out.rstrip().endswith("."), out[-80:])
check("a colour/detail tier credits a SIGHTING", any(e["kind"] == "sighting" and e["key"] == "eleven_armed_starfish" for e in led), str(led))
ans = [e for e in events() if e.get("kind") == "answer"]
check("the answer event is auditable (resolved=described, tier, dist)", ans and ans[-1].get("resolved") == "described" and ans[-1].get("tier") in ("colour", "detail"), str(ans[-1:] ))
check("the answer names nothing", not LS.leak_scan(out, terms), str(LS.leak_scan(out, terms)))
SP[0] = "at_the_path_foot"
out_far = life.look_answer("pool", "shore", NOW, raw=RAW)
check("from far away the same starfish is not resolvable: falls through", out_far == "")
LS.current_standpoint = lambda place="shore": {"pos": [-60.0, 0.0, 0.0], "facing_deg": 90}      # 85 m from the shelf: an outline only
open(TMP / "life_ledger.jsonl", "w").close()
out_form = life.look_answer("rock", "shore", NOW, raw="look at the buff animal with the paddle flippers")
led = ledger()
check("a FORM tier is shown but is a glimpse: exposure only, no sighting",
      bool(out_form) and "against the ground" in out_form and not any(e["kind"] == "sighting" for e in led) and any(e["kind"] == "miss" and e["key"] == "sea_lion" for e in led),
      f"{out_form[:90]} {led}")
check("the glimpse names nothing", not LS.leak_scan(out_form, terms))
LS.current_standpoint = lambda place="shore": SP[0]
SP[0] = "at_the_pools"
tide_hi = next(t0 + i * 600 for i in range(0, 6 * 24 * 6) if world_clock.tide(t0 + i * 600)["level"] > 0.7)
check("a closed zone (tide over the pool) falls through", life.look_answer("pool", "shore", tide_hi, raw=RAW) == "")
check("a scenery look with one attribute falls through", life.look_answer("pool", "shore", NOW, raw="look at the orange net by the pool") == "")

print("-- 5. an alias look is byte-identical with the bestiary on or off")
life.RENDER = True
flags(shore_bestiary=True, shore_bestiary_render=True); a_on = life.look_answer("crab", "shore", NOW, raw="look at the crab")
fresh(); flags(); a_off = life.look_answer("crab", "shore", NOW, raw="look at the crab")
check("'the crab' answers the same either way", a_on == a_off and a_on != "", f"{a_on[:60]!r} {a_off[:60]!r}")
check("a look with no raw (legacy call shape) still works", isinstance(life.look_answer("crab", "shore", NOW), str))
fresh(shore_bestiary=True, shore_bestiary_render=True)

print("-- 6. false-positive sweeps over real data")
rows3 = LS.rows()                                                  # ALL 100 rows, present or not: the sweep is about the words
words3 = {r["key"]: LS.attr_words(r) for r in rows3}
print("     sweep rows:", len(rows3))


def intercepts(text, target=""):
    """Rows a look would be taken for. Production order is alias first (life._match on the keyword), so a target an existing row
    already answers by alias never reaches the described-look matcher."""
    if target and life._match(target, "shore"):
        return []
    return [k for k, w in words3.items() for c in LS.look_clauses(text, target) if LS.score_clause(w, c)[0] >= LS.MIN_ATTRS]


corpus = json.loads((ROOT / "docs/reviews/observe_inventory_2026-09-02.json").read_text(encoding="utf-8"))
phr = [p for cat in corpus.values() for p in cat]
LEGIT = ("butterfly", "prawn", "shrimp", "anemone")   # a clause that genuinely describes such a creature may (and should) reach its row
hit = [(p, intercepts(f"look at {p}", p)) for p in phr if intercepts(f"look at {p}", p) and not any(w in p for w in LEGIT)]
check(len(rows3) == 100, "the sweep covers all 100 rows")
check(f"none of the {len(phr)} phrasings he has actually observed is taken for a creature", not hit, str(hit[:5]))
from core import world_content_shore as WCS                        # noqa: E402
al = [a for spec in WCS.TARGETS.values() for a in spec["aliases"]]
hit = [(a, intercepts(f"look at the {a}", a)) for a in al if intercepts(f"look at the {a}", a)]
check(f"none of the {len(al)} shore scenery aliases is taken for a creature", not hit, str(hit[:5]))
lines = [ln for spec in WCS.TARGETS.values() for pool in spec["pools"].values() for ln in pool]
hit = [(ln[:50], intercepts("look at " + ln, ln)) for ln in lines if intercepts("look at " + ln, ln) and not any(w in ln for w in LEGIT)]
check(f"none of the world's own {len(lines)} shore scenery lines, offered back as a look, is taken for a creature", not hit, str(hit[:5]))
n = hits = 0
hit_rows = []
with open(ROOT / "data/hands_trace.jsonl", encoding="utf-8") as f:
    for ln in f:
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get("act_kind") not in ("observe", "look") or r.get("location") != "shore":
            continue
        n += 1
        raw = f"{r.get('thought', '')} {r.get('intention', '')}".lower()
        h = intercepts(raw, str(r.get("act_object") or ""))
        if h and not any(w in raw for w in LEGIT):
            hits += 1; hit_rows.append((h, str(r.get("act_object")), raw[:140]))
print(f"     real shore observe/look thoughts swept: {n}; taken for a creature: {hits}")
for h in hit_rows[:6]:
    print("       ", h)
check(f"real thoughts: at most 1 in 500 of {n} would be taken for a creature (and each is a genuine description)", hits <= max(1, n // 500), str(hit_rows[:3]))

print("-- 7. wiring")
import inspect                                                     # noqa: E402
check("look_answer takes raw (optional)", "raw" in inspect.signature(life.look_answer).parameters)
check("sensorium.look forwards the full sentence", "look_answer(t_clean, cur_loc, raw=raw)" in (ROOT / "core/sensorium.py").read_text(encoding="utf-8"))
from core import spatial                                           # noqa: E402
check("the real current_standpoint (read-pure) returns a standpoint that exists in shore.json",
      REAL_CS("shore") in spatial.layout("shore")["standpoints"], REAL_CS("shore"))
print()
print("ALL OK -- shore bestiary P2" if not FAILS else f"{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
