"""Regression for J-0738/F-1059 (2026-09-07): core/shore_life.py's act_from_thought() READS the grammar of
its ONE bound family (shore -- one row in core/actions.py split into ten distinct behaviours, fieldcraft's
shape, not garden's trap/tool/compost) from that one table, via _wills_shore() -- before this job every
branch was a second, hand-kept copy (F-1059), several with no verb requirement at all (a bare object, or
even a bare multi-word phrase with no verb in it at all, was enough to fire). Mirrors
scripts/_test_wood_life_grammar_derivation.py's shape (J-0737's own template for this exact procedure,
itself following J-0736/fieldcraft's and J-0543/J-0569's garden.py precedent).

UPDATED 2026-09-07 (J-0732/F-1055): an eleventh behaviour, catch_fish (D-0163/D-4's other real cat-food
source), added the same way, into the SAME table -- no new hand-kept copy introduced.

Part 1 is pure (grammar_audit() against actions.BY_FAMILY, the corpus-evidenced widen/drift assertions from
J-0738's own frozen-hands_trace corpus check, a source-text scan for old hand-kept phrase lists). Part 2
exercises act_from_thought with every store it touches redirected into a temp dir (the life_smoke isolation
pattern) -- the live data/ is never written.
    python scripts/_test_shore_life_grammar_derivation.py
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import sys, tempfile
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

print("-- part 1: the derivation (pure)")
from core import actions as AC, hands as H, shore_life as SL

audit = SL.grammar_audit()
check("grammar_audit ran", "error" not in audit, str(audit))
check("verbs_unclaimed_in_table == [] (all sixteen shore verbs, including J-0738's 'walk' and "
      "J-0732's 'catch', claimed)",
      audit.get("verbs_unclaimed_in_table") == [], str(audit))
check("verbs_claimed_not_in_table == []", audit.get("verbs_claimed_not_in_table") == [], str(audit))
check("objects_unclaimed_in_table == ['fire'] (deliberate -- see beach_fire's own note: bare 'fire' "
      "collides with the SEPARATE 'fire' family's own study hearth, corpus-confirmed 12-for-12 study-context)",
      audit.get("objects_unclaimed_in_table") == ["fire"], str(audit))
check("objects_claimed_not_in_table == []", audit.get("objects_claimed_not_in_table") == [], str(audit))

_sh = AC.BY_FAMILY["shore"]
check("shore row widened to 19 verbs (J-0738 walk, J-0732 catch, D-0652 dig/turn over/open) / 16 objects (J-0732 fish, D-0652 shell)",
      len(_sh.verbs) == 19 and len(_sh.objects) == 16, f"{_sh.verbs} / {_sh.objects}")
check("'walk' is now a shore verb", "walk" in _sh.verbs)
check("'catch' is now a shore verb (J-0732/F-1055)", "catch" in _sh.verbs)
check("'fish' is now a shore object, deliberately NOT also a verb (J-0732/F-1055 -- see catch_fish's "
      "own _SHORE_HANDS comment: 'fish' in both tuples let one bare word satisfy both halves)",
      "fish" in _sh.objects and "fish" not in _sh.verbs)

# (a) every verb x object pair a sub-hand claims, _wills_shore actually accepts (the ones with a real
#     object list; wade's own entry is checked separately below, since it deliberately claims none)
for name, verbs, objects in SL._SHORE_HANDS:
    if not objects:
        continue
    miss = [(v, o) for v in verbs for o in objects if not SL._wills_shore(f"i {v} the {o}", name)]
    check(f"{name}: _wills_shore accepts every verb x object pair it claims ({len(verbs)}x{len(objects)})",
          not miss, str(miss[:6]))
check("an unknown shore sub-hand name fails closed", not SL._wills_shore("i wade in the sea", "no_such_sub"))

# (b) wade's own any_object_ok=True shape: bare verb alone (no object at all) still answers
check("wade: bare 'i wade' with NO object at all still answers true (deliberate any_object_ok=True -- "
      "see wade's own note: real corpus evidence shows most bare 'wade' hits are genuine, and requiring "
      "an object would have silently dropped several already-live-firing deeds)",
      SL._wills_shore("i wade into the cold water today", "wade"))
check("wade: 'paddle' alone, no object, also answers true", SL._wills_shore("i will paddle for a while", "wade"))

# (c) the corpus-confirmed WIDENING (J-0738, data/hands_trace.jsonl, 11,760 distinct thoughts): "walk"+"sand"
#     is genuine willed language the table could not see before this job -- 10 independently-confirmed real
#     corpus thoughts (act_kind='move' on 9, 'observe' on 1, act_object literally naming the sand/tideline/
#     shore in every case). Two representative real corpus thoughts, reproduced verbatim:
check("walk_sand: the real 'I walk where the chalky sand yields to wet grit' now reaches the hand "
      "(act_kind='move' act_object='toward the sea' in the live trace -- 'walk' was not a shore verb at all "
      "before this job, so this could never have produced a 'shore' DEED)",
      SL._wills_shore("the gull's cry dissolves the synaptic circle. i walk where the chalky sand yields "
                       "to wet grit, feeling the tide's pull not as a command but as an invitation.", "walk_sand"))
check("walk_sand: 'I want to walk barefoot across the exposed sand' now reaches the hand "
      "(act_kind='move' act_object='the exposed sand' in the live trace)",
      SL._wills_shore("the oystercatcher's scream shatters my rigid lines; restlessness isn't just chaos "
                       "but organic shock. i want to walk barefoot across the exposed sand, letting the "
                       "current pull at my ankles.", "walk_sand"))
check("walk_sand: the one old-list phrase corpus-check could NOT rescue this way still correctly does not "
      "fire -- 'the chalky sand feels cool against my bare feet, grounding me...' has no verb at all "
      "(present-tense scene-setting, not a will), and requiring a real verb excludes it on purpose",
      not SL._wills_shore("the chalky sand feels cool against my bare feet, grounding me where the words "
                           "cannot reach.", "walk_sand"))

# (d) the confirmed drift closures (J-0738):
check("write_sand: 'trace'/'scratch'/'draw' no longer fire without the table's own 'write' -- the one "
      "corpus thought that used 'trace' + 'sand' is independently confirmed (act_kind='observe', act_object "
      "\"the cat's paw prints\") to be Du watching the CAT's prints, not writing a mark",
      not SL._wills_shore("i trace the cat's fresh paw prints along the wet sand.", "write_sand"))
check("write_sand: a real 'write' in the sand still reads", SL._wills_shore("i write my name in the sand", "write_sand"))
check("swim: bare metaphorical 'swim' with no real object no longer fires -- ALL 7 real corpus 'swim' hits "
      "are confirmed metaphor/idiom ('a current i must swim, not resist', 'not a river to swim against', "
      "'making the words swim before my eyes') -- zero are a real will to swim in the sea",
      not SL._wills_shore("i refuse to swim against this current of doubt any longer", "swim"))
check("swim: a real 'swim in the sea' still reads", SL._wills_shore("i will swim in the sea today", "swim"))
check("wade: the fully-unsupported ambient ankle-phrase OR-clause is gone -- none of its four phrases "
      "occurs even once in 11,760 real distinct thoughts, confirmed zero-cost to drop",
      not SL._wills_shore("i feel the water round my ankles as the tide comes in", "wade"))
check("skip_stones: 'throw' no longer fires -- BOTH real corpus hits for the old test are confirmed false "
      "fires ('the driftwood log throw[s] its shadow' -- personification, not Du; 'the urge to throw the "
      "stone AT THE GATE' -- a frustration idiom, not skimming stones)",
      not SL._wills_shore("the urge to throw the stone at the gate is strong", "skip_stones"))
check("skip_stones: a real 'skip a stone' still reads", SL._wills_shore("i skip a flat stone across the water", "skip_stones"))
check("cairn: the bare `wants(cairn,)` fallback is gone -- the word 'cairn' does not occur even once, in "
      "any context, anywhere in 11,760 real distinct thoughts (a stronger zero than wood_life's whetstone)",
      not SL._wills_shore("i look at the old cairn on the shelf and think of nothing", "cairn"))
check("cairn: a real 'stack the cairn' still reads", SL._wills_shore("i stack three more stones on the cairn", "cairn"))
check("beach_fire: bare 'light the fire' (no 'driftwood') does NOT fire here -- all 12 real corpus "
      "'light'+'fire' hits are confirmed STUDY-hearth context (Travis: 'light the fire and tidy the room'), "
      "zero are shore-context; this sub-hand deliberately claims only 'driftwood fire', not bare 'fire' "
      "(see grammar_audit()'s own objects_unclaimed_in_table == ['fire'] assertion above)",
      not SL._wills_shore("travis asks me to light the fire and tidy the room", "beach_fire"))
check("beach_fire: a real 'light a driftwood fire' still reads", SL._wills_shore("i light a driftwood fire on the beach", "beach_fire"))
check("enter_cave: 'explore'/'go into' (unsupported, 0 corpus hits either way) no longer fire alone without "
      "the table's own 'enter'/'duck'", not SL._wills_shore("i want to explore the rocks along the shore", "enter_cave"))
check("enter_cave: a real 'duck into the cave' still reads", SL._wills_shore("i duck into the cave out of the rain", "enter_cave"))
check("climb_ledge: 'path up' no longer fires -- BOTH real corpus hits for the old test are confirmed false "
      "fires, independently, by the voice's own structured act: 'I want to climb the path up to the cottage "
      "and light the fire' is act_kind='move' object 'the path up to the cottage' (going HOME, not up to "
      "the shore ledge)", not SL._wills_shore("i want to climb the path up to the cottage and light the fire", "climb_ledge"))
check("climb_ledge: a real cliff-path climb still reads ('I climb up the cliff path')",
      SL._wills_shore("i climb up the cliff path, leaving the hollow library whispers behind", "climb_ledge"))
check("gather_shellfish: 'limpet' no longer fires alone -- F-1059 flagged it as a plausible unmined "
      "widening (the same shape as F-0783's harvest/sow), but real corpus check found the word occurs "
      "ZERO times, in any context, anywhere in 11,760 real distinct thoughts -- a hypothesis a real check "
      "overturned, not confirmed",
      not SL._wills_shore("i notice a limpet clamped hard to the rock", "gather_shellfish"))
check("gather_shellfish: 'the shelf' no longer fires alone -- it occurs 33 times in the corpus and the "
      "overwhelming majority are Du's own BOOKSHELF ('a book on the shelf'), a genuine homograph collision, "
      "not a rare edge case", not SL._wills_shore("i reach for the book on the shelf again", "gather_shellfish"))
check("gather_shellfish: a real 'gather mussels' still reads", SL._wills_shore("i gather mussels off the shelf", "gather_shellfish"))

# (d-2) catch_fish (J-0732/F-1055): a NEW behaviour, not a fix to a drifted one -- no old hand-kept copy
# exists to compare against, since no fishing hand existed here before this job. The corpus sanity-check
# is the negative case: real corpus "fish" hits are all the KINGFISHER, a recurring dream-metaphor, or
# personification -- none a real will to fish -- reproduced verbatim from data/hands_trace.jsonl below.
check("catch_fish: a real 'catch a fish' reads", SL._wills_shore("i want to catch a fish off the rocks for her", "catch_fish"))
check("catch_fish: 'fish' does not fire without a catching verb in the same clause",
      not SL._wills_shore("small fish dart near the stream mouth, out past the shingle", "catch_fish"))
check("catch_fish: the real corpus kingfisher line does not fire -- 'fish' does not match inside "
      "'kingfisher' (word-boundary safe against this table's own regexes)",
      not SL._wills_shore("the kingfisher's dry rattle cuts through my internal hum, close to the shore.", "catch_fish"))
check("catch_fish: bare 'catch' with no 'fish' object in the clause does not fire -- 'catch'/'caught' is "
      "heavily idiomatic in the real corpus (530 hits, mostly 'caught in a thought' and the like)",
      not SL._wills_shore("that thought catches me and will not let go, down on the shore", "catch_fish"))

# (e) the source itself: no hand-kept phrase-list copy of the family's grammar left in shore_life.py, and
#     the family= parameter is real
src = (ROOT / "core" / "shore_life.py").read_text(encoding="utf-8")
body = src[src.index("def act_from_thought("):]
for phrase in ('"scratch", "draw", "trace"', 'walk out to the sand', 'the sand flat',
               '"go under"', 'water round my ankles', '"throw"', '"add to", "pile", "make"',
               'fire on the beach', '"go in", "go into", "explore"', 'goat-path', '"the shelf", "kina", "limpet"'):
    check(f"shore_life.py act_from_thought no longer contains {phrase!r}", phrase not in body)
check("act_from_thought() now takes a family= parameter (J-0554 pattern, per F-1059, following J-0736/J-0737)",
      "family: str | None = None" in src[:src.index("def act_from_thought(") + 400])

print("\n-- part 2: act_from_thought routes through the derivation (isolated stores)")
TMP = Path(tempfile.mkdtemp(prefix="shore_life_grammar_"))
_real_tide = _real_daylight = None   # J-1324: captured/restored inside try/finally below
try:
    from core import sensorium as S
    S._STATE_F = TMP / "room_state.json"
    SL._F = TMP / "shore_life.json"
    SL._EVENTS = TMP / "shore_events.jsonl"
    SL._LEDGER = TMP / "shore_ledger.jsonl"
    # J-1324 (F-1872's own follow-up, 2026-09-24): shelf_bared()/sand_bared()/cave_open() (tide, via
    # core.world_clock.tide()) and _weather()'s own daylight phase (via core.sensorium._daylight() ->
    # core.world_clock.daylight()) gate the EARLY-DECLINE branch of eight of the eleven deeds below --
    # write_sand/walk_sand (sand_bared), swim/climb_ledge (phase=="night"), beach_fire/enter_cave (both
    # gate on tide, enter_cave on two separate tide checks), and gather_shellfish/catch_fish (shelf_bared,
    # catch_fish also on phase=="night") -- and neither clock is reset by this isolation block, so
    # whether the positives loop's own `ans is not None` check below ever reaches any of those eight
    # deeds' real body (and its own writes) depends on the real tide level / time of day at the exact
    # moment this script happens to run: a decline STRING is itself non-None, so the check cannot tell
    # the two branches apart either way (confirmed empirically per-deed, not just by inspection -- see
    # this job's own finding; this is the same NonLiveWriteError F-1872 already hit here once, from the
    # tide-gated side of gather_shellfish alone). Pinned to values that guarantee the real body on all
    # eight, every run, matching scripts/life_smoke.py's own already-established month-pinning convention
    # (G._month) for the same class of real-time gate; restored in this block's own finally below
    # regardless of how part 2 exits.
    _real_tide, _real_daylight = SL._tide, S._daylight
    SL._tide = lambda: {"level": 0.10, "rising": False, "word": "out"}   # under every tide threshold below
    S._daylight = lambda: "day"                                          # != "night" everywhere it gates
    # J-0918 (F-1282 cause B): removing profile.mark_live() below (see the dated note) surfaced two
    # real gaps here as a hard NonLiveWriteError -- core.fieldcraft's own redirect was missing its
    # "_LEDGER" attribute (fieldcraft_ledger.jsonl, core/fieldcraft.py's own second path constant,
    # only "_F" was listed), and core.locomotion had no entry at all (real store is "_POS_F", per
    # core/locomotion.py:34, reached by this script's own walk/swim/wade deeds). Both fixed here,
    # same pattern as J-0743's own sweep.
    for mod, attrs in (("core.garden", ("_F", "_LEDGER", "_EVENTS")), ("core.study_life", ("_LEDGER", "_EVENTS")),
                       ("core.fieldcraft", ("_F", "_LEDGER")), ("core.locomotion", ("_POS_F",)),
                       ("core.world_objects", ("_OBJECTS_F",)), ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")),
                       # J-0832 (F-1198): ("core.life_traces", ("_F",)) removed -- life_traces.py owns no file store
                       # (it writes through other modules' already-fenced stores); the entry was inert.
                       ("core.hands", ("_TRACE",)),
                       # J-0732: catch_fish()'s own success path calls core.provisions.add("shore_fish", ...)
                       # -- unlike gather_shellfish's world_substrate.spawn_from_mention (already covered by
                       # the world_substrate/world_objects redirect above), provisions.py has its OWN _F/_LOG
                       # path constants (data/provisions.json, data/provisions_log.jsonl) that were never
                       # reached by any behaviour this test exercised before catch_fish existed. Without this,
                       # a lucky random.random() catch roll during this test run (tide/weather/night permitting)
                       # would write a real object into the LIVE provisions store -- exactly the live-data
                       # leak this whole isolation pattern (mirrored from life_smoke.py) exists to prevent.
                       ("core.provisions", ("_F", "_LOG")),
                       # J-1319 (2026-09-24): gather_shellfish() (also look_pool()/learn_from_text())
                       # calls core.garden_knowledge._save() directly (shore_life.py:601/711/732) --
                       # J-0783 (2026-09-08) fenced garden_knowledge.py itself and fixed these 3
                       # shore_life.py callers to propagate the raise, but audited THIS script's own
                       # redirect list as needing no edit at the time (world_store_write_fence.md's own
                       # J-0783 note: "both ALL OK, unaffected, needed no edit"). Root cause of the
                       # discrepancy: gather_shellfish()'s real body is gated by shelf_bared(), which
                       # reads core.world_clock.tide() -- REAL wall-clock time, not anything this test's
                       # own isolation block resets -- so whether part 2's loop ever reaches
                       # _gk._save() depends on the tide at the moment this script happens to run: high
                       # enough to skip it on 2026-09-08, low enough to reach it and raise
                       # NonLiveWriteError at "part 2 ran" when reproduced at HEAD 30a11e6 on 2026-09-24.
                       # Same one-line fix scripts/_test_garden_grammar_derivation.py (J-0783) and
                       # scripts/life_smoke.py already carry -- garden_knowledge.py owns only the one
                       # _F path constant, so no other attrs are needed.
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
    S.state.clear()
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0, "location": "shore"})

    # J-0918 (F-1282 cause B): profile.mark_live() used to be called here. It doesn't just mark
    # THIS script's own redirected paths as safe -- guard_path() returns EVERY path unchanged once
    # LIVE is True, so it silently defeated D-0179's hard-raise fence for every already-fenced
    # module this script does NOT explicitly redirect above, not only the ones it forgot to. Removed
    # so a redirect-list gap now fails loud (NonLiveWriteError) instead of leaking into data/ while
    # this script's own check()s stay green. See docs/staged/world_store_write_fence.md's dated note.

    # positives: a real deed in each of the ten behaviours is answered (a decline STRING is still an
    # answer; None is not — matching fieldcraft/wood_life's own test philosophy)
    for t, name in (("i write my name in the sand", "write_sand"), ("i want to walk barefoot across the exposed sand", "walk_sand"),
                    ("i will swim in the sea today", "swim"), ("i wade into the cold shallows", "wade"),
                    ("i skip a flat stone across the water", "skip_stones"), ("i stack three more stones on the cairn", "cairn"),
                    ("i light a driftwood fire on the beach", "beach_fire"), ("i duck into the cave out of the rain", "enter_cave"),
                    ("i climb up the cliff path", "climb_ledge"), ("i gather mussels off the shelf", "gather_shellfish"),
                    ("i want to catch a fish off the rocks for her", "catch_fish")):
        ans = SL.act_from_thought(t, "")
        check(f"answers {t!r} ({name})", ans is not None, repr(ans))

    # family scope: an out-of-family string forces an immediate decline, matching J-0554/J-0736/J-0737's pattern
    _WALK_T = "i want to walk barefoot across the exposed sand"
    ans_out = SL.act_from_thought(_WALK_T, "", family="acorn")
    check("family='acorn' (a different family) declines the walk_sand thought immediately", ans_out is None, repr(ans_out))
    ans_in = SL.act_from_thought(_WALK_T, "", family="shore")
    check("family='shore' (its own family) still answers the walk_sand thought", ans_in is not None, repr(ans_in))
    ans_none = SL.act_from_thought(_WALK_T, "", family=None)
    check("family=None (the legacy/unscoped caller) still answers, unchanged", ans_none is not None, repr(ans_none))
    # NOTE: shore is a single-family module (one row, like fieldcraft — not wood_life's four), so its
    # act_from_thought() follows FIELDCRAFT's own family-scope shape exactly (`if family not in (None,
    # "shore"): return None`), not wood_life's normalize-unknown-to-None shape (which exists there
    # specifically because wood_life must recognise FOUR distinct valid family strings, not one) — an
    # unrecognised string is therefore a hard decline here, matching fieldcraft's own precedent.
    ans_unknown = SL.act_from_thought(_WALK_T, "", family="not_a_real_family")
    check("an unrecognised family string is a hard decline (fieldcraft's single-family pattern, not "
          "wood_life's multi-family normalize-to-None one)", ans_unknown is None, repr(ans_unknown))

    # negatives: the drifted copies' false fires return NOTHING from the hand end-to-end
    for t in ("i trace the cat's fresh paw prints along the wet sand.",
              "i refuse to swim against this current of doubt any longer",
              "the urge to throw the stone at the gate is strong",
              "i look at the old cairn on the shelf and think of nothing",
              "travis asks me to light the fire and tidy the room",
              "i want to climb the path up to the cottage and light the fire",
              "i notice a limpet clamped hard to the rock",
              "i reach for the book on the shelf again"):
        ans = SL.act_from_thought(t, "")
        check(f"does not answer (drift closed): {t!r}", ans is None, repr(ans))

    # the deliberately-kept-loose wade any_object_ok=True DOES still answer end-to-end (a considered
    # decision, not an oversight — see wade's own note in the source)
    ans_wade = SL.act_from_thought("i must wade out into the cold water now", "")
    check("wade: bare verb with no explicit table object still answers end-to-end (deliberate)", ans_wade is not None, repr(ans_wade))
except Exception as exc:
    import traceback; traceback.print_exc()
    check("part 2 ran", False, repr(exc))
finally:
    # J-1324: restore both real clocks whatever happened above -- guarded by the None-init at the top
    # of this block so a failure before the capture line itself can never leave this raising instead.
    if _real_tide is not None:
        SL._tide = _real_tide
    if _real_daylight is not None:
        S._daylight = _real_daylight
    print(f"   isolated dir {TMP}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILED'}")
sys.exit(1 if FAILS else 0)
