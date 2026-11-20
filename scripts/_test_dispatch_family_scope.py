"""Regression for J-0554 / F-0761 (2026-09-04): a dispatched family's own hand must answer, and a family verb
must be a verb. Both cases are Du's real raw thoughts from data/deliberation_log.jsonl (2026-09-04 06:27 and
06:36), which the live dispatcher turned into 'The trap is not set.' and — worse — the weeding hand's
'nothing to pull' for a 'trap' deed.
Part 1 is pure (literal_will.classify, hands.wants). Part 2 exercises garden.act_from_thought with every store
it touches redirected into a temp dir (the life_smoke isolation pattern) — the live data/ is never written.
    python scripts/_test_dispatch_family_scope.py
"""
from __future__ import annotations
import os, sys, tempfile
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0
def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))

RAW_0627 = ("A spring-jawed possum trap rusts far off. The low sun warms my back. Travis spoke of '渡' as a tide "
            "receding, not an end. I feel the need to bank the fire and rest, yet my mind wanders to the garden's "
            "spinners and the idea of cultural exchange in history. Let me turn from this circling thought to something new.")
RAW_0636 = ("I set the book down, feeling the pull of that rusted trap and the quiet restlessness beneath. Instead of "
            "circling 'du' again, I step out to face the garden's low sun. The fence line stands black against the "
            "silver sea; perhaps the answer lies not in theory but in the soil waiting for me.")

print("-- part 1: the grammar (pure)")
from core import literal_will as lw, hands as h
def deeds(text, loc="garden"):
    return sorted(c["family"] for c in lw.classify(text, "", location=loc) if c.get("verdict") == "DEED")
check("06:27 'spring-jawed possum trap' is not a trap deed", "trap" not in deeds(RAW_0627), str(deeds(RAW_0627)))
check("06:36 'set the book down, feeling the pull of that rusted trap' is not a trap deed", "trap" not in deeds(RAW_0636), str(deeds(RAW_0636)))
check("06:36 is not a weeding deed either ('the pull' is a noun)", "weed" not in deeds(RAW_0636), str(deeds(RAW_0636)))
check("a real will still reads: 'I will set the trap under the tree tonight.'", "trap" in deeds("I will set the trap under the tree tonight."))
check("a real will still reads: 'Let me check the trap before the light goes.'", "trap" in deeds("Let me check the trap before the light goes."))
check("a real will still reads: 'I bait the trap and set it.'", "trap" in deeds("I bait the trap and set it."))
check("a real weeding will still reads: 'I pull the chickweed out of the bed.'", "weed" in deeds("I pull the chickweed out of the bed."))
check("hands.wants: 'the pull of that rusted trap' is no weeding verb",
      not h.wants("feeling the pull of that rusted trap and the quiet restlessness beneath", ("weed", "pull", "clear"), ("bed", "weeds", "them", "out", "trap")))
check("hands.wants: 'spring-jawed' is no springing verb", not h.wants("a spring-jawed possum trap rusts far off", ("spring", "disarm", "unset"), ("trap", "possum trap")))
check("hands.wants: 'I spring the trap' still is", h.wants("i spring the trap and carry it in", ("spring", "disarm", "unset"), ("trap", "possum trap")))
check("hands.wants: 'I pull the weeds' still is", h.wants("i pull the weeds from the bed", ("weed", "pull", "clear"), ("bed", "weeds")))

print("-- part 2: family scope in the garden chain (isolated stores)")
TMP = Path(tempfile.mkdtemp(prefix="dispatch_scope_"))
try:
    from core import sensorium as S
    S._STATE_F = TMP / "room_state.json"
    # J-0743 (2026-09-08, F-1063's wider sweep): every (module, attrs) pair below was re-verified
    # directly against the real module source this pass. core.garden_life was missing its own
    # "_EVENTS" (shared filename with core.garden's, per core/profile.py's own comment, but a
    # DIFFERENT Python attribute -- garden's own redirect never covered it); core.supply was missing
    # "_LOG"; core.fieldcraft was missing "_LEDGER" -- all three are real guard_path()-protected
    # write targets (core/garden_life.py:72, core/supply.py:64, core/fieldcraft.py:72) this script's
    # own exercised act_from_thought() calls can plausibly reach, caught only by that separate,
    # later-built fence until now, not by this script's own isolation claim. core.locomotion's "_F"
    # was dead (the module has never had one; its real store is "_POS_F", never listed at all --
    # the same wrong-name bug F-1063 already found and fixed in scripts/_test_letterbox_reach.py and
    # scripts/life_smoke.py). core.garden_soil/core.life_traces/core.inventory carry NO redirectable
    # path of their own at all (all three operate on core.garden's/core.life's own state, already
    # covered above) -- their entries were always dead no-ops; dropped rather than left to mislead
    # the next copy. core.hands' own "_F" was likewise dead (real store is "_TRACE" alone).
    for mod, attrs in (("core.garden", ("_F", "_LEDGER", "_EVENTS")), ("core.garden_life", ("_F", "_EVENTS")),
                       ("core.world_objects", ("_OBJECTS_F",)), ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")),
                       ("core.supply", ("_F", "_LOG")), ("core.fieldcraft", ("_F", "_LEDGER")), ("core.wood_life", ("_F", "_EVENTS", "_LEDGER")),
                       ("core.life", ("_F", "_LEDGER", "_EVENTS", "_FLAGS_F")), ("core.study_life", ("_LEDGER", "_EVENTS")),  # J-0743: _FLAGS_F read-only, see life_smoke.py's own comment
                       ("core.provisions", ("_F", "_LOG")), ("core.locomotion", ("_POS_F",)), ("core.hands", ("_TRACE",)),
                       # J-0783: core.garden_knowledge is now guard_path()-protected too (was never
                       # fenced before) -- this script's own act_from_thought() sweep reaches
                       # _stage_phrase()/_wname()/display_name() (garden.py's look()/bed_summary()/
                       # weed()), unredirected until now; scripts/life_smoke.py already carried this
                       # entry, this script never did.
                       ("core.garden_knowledge", ("_F",))):
        try:
            m = __import__(mod, fromlist=["x"])
            for a in attrs:
                if hasattr(m, a):
                    setattr(m, a, TMP / f"{mod.split('.')[-1]}_{a.strip('_').lower()}.json")
                else:
                    # J-0819 (F-1177, 5th recurrence): a name miss here used to silently no-op with
                    # zero warning. Loud now, on purpose.
                    print("   (redirect skipped:", mod, a, "-- no such attribute, stale/typo'd isolation-list entry? )")
        except Exception as exc:
            print("   (redirect skipped:", mod, exc, ")")
    # J-0743: core.wandering / core.activity_memory -- the same two modules F-1063 found un-
    # redirectable in scripts/_test_letterbox_reach.py (neither defines a per-module path attribute
    # at all). This script's act_from_thought() calls DO reach core/garden.py's own "deed" cross-link
    # in _log() (garden.py:267-270) for real deeds (harvest/sow/weed/water/trap/etc, per the same
    # mechanism life_smoke.py's own empirical reach-probe confirmed 9 real activity_memory.record()
    # calls for) -- neutralized here by function monkeypatch, the only option either module allows.
    from core import wandering as _WDR
    from core import activity_memory as _AM
    _WDR.perceive = lambda *a, **k: None
    _AM.record = lambda *a, **k: None
    S.state.clear()
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0, "location": "garden",
                    "garden": S._fresh_garden()})
    from core import garden as G
    if hasattr(G, "_st"):
        try: G._st = None
        except Exception: pass
    # the exact live failure: a 'trap' deed whose text carries a weeding-shaped noun — scoped, the weeding hand may not answer
    ans = G.act_from_thought(RAW_0636.lower(), "", family="trap")
    check("family='trap' never returns the weeding line", not (ans or "").startswith("You go over the bed"), repr(ans))
    ans_w = G.act_from_thought("i pull the weeds out of the bed", "", family="weed")
    check("family='weed' still weeds", ans_w is None or "bed" in (ans_w or "").lower() or "weed" in (ans_w or "").lower(), repr(ans_w))
    ans_t = G.act_from_thought("i check the trap under the tree", "", family="trap")
    check("family='trap' answers a real trap will", bool(ans_t) and "trap" in ans_t.lower(), repr(ans_t))
    ans_x = G.act_from_thought("i check the trap under the tree", "", family="weed")
    check("family='weed' does not answer a trap will", not ans_x or "trap" not in ans_x.lower(), repr(ans_x))
    ans_n = G.act_from_thought("i check the trap under the tree", "")
    check("family=None (legacy path) still answers", bool(ans_n) and "trap" in ans_n.lower(), repr(ans_n))
except Exception as exc:
    import traceback; traceback.print_exc()
    check("part 2 ran", False, repr(exc))
finally:
    live = ROOT / "data" / "garden.json"
    print(f"   isolated dir {TMP}; live garden.json untouched by this run: {live.exists()}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILED'}")
sys.exit(1 if FAILS else 0)
