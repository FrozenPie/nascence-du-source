"""Regression for J-0739/F-1059 (2026-09-07): core/study_life.py's act() READS the grammar of all NINE
bound families (tea, lamp, door, grate, clock, clean, candles, wear, sketch) from core/actions.py via the
_STUDY_HANDS verb+object partition, and now family-SCOPES all nine (only 'candles' was scoped before this
job). Mirrors scripts/_test_shore_life_grammar_derivation.py's shape (J-0736/J-0737/J-0738's own template
for this exact procedure), adapted for study's own difference: nine separate table rows share one module
(fieldcraft/shore_life each split ONE row into many behaviours; study does that AND spans nine rows).

Part 1 is pure (grammar_audit() against actions.BY_FAMILY per family, the corpus-evidenced widen/drift
assertions from J-0739's own frozen-hands_trace corpus check, a source-text scan for old hand-kept phrase
lists). Part 2 exercises act() with every store it touches redirected into a temp dir (the life_smoke
isolation pattern) — the live data/ is never written.
    python scripts/_test_study_life_grammar_derivation.py
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
from core import actions as AC, hands as H, study_life as SL

audit = SL.grammar_audit()
check("grammar_audit ran", "error" not in audit, str(audit))
check("grammar_audit covers exactly the eight non-candles families",
      set(audit.keys()) == set(SL._STUDY_FAMILIES) - {"candles"}, str(sorted(audit.keys())))
for fam, a in audit.items():
    if fam == "lamp":
        # lamp_blowout/lantern_blowout deliberately KEEP "douse"/"put out"/"extinguish" — zero
        # demonstrated false-fire cost (unlike every other extra word this job dropped) and a real
        # dependency (scripts/life_smoke.py exercises "put out the lantern"). See _STUDY_HANDS's own note.
        check("lamp: the only verbs claimed-not-in-table are the deliberately-kept blowout synonyms",
              a["verbs_claimed_not_in_table"] == ["douse", "extinguish", "put out"], str(a))
    else:
        check(f"{fam}: no verb claimed that the table row does not have", a["verbs_claimed_not_in_table"] == [], str(a))
    check(f"{fam}: no object claimed that the table row does not have", a["objects_claimed_not_in_table"] == [], str(a))
check("tea: only 'steep' is a deliberately-unclaimed verb (see _STUDY_HANDS's own note — 4/4 corpus "
      "'steep' occurrences are about a STEEP PATH, none about tea, and no dedicated hand exists to test)",
      audit["tea"]["verbs_unclaimed_in_table"] == ["steep"], str(audit["tea"]))
check("grate: only 'ash' is a deliberately-unclaimed object (89 historical fires, 86 false — F-1059/J-0739)",
      audit["grate"]["objects_unclaimed_in_table"] == ["ash"], str(audit["grate"]))
check("clean: only 'scrub' is a deliberately-unclaimed verb (0 corpus occurrences at all)",
      audit["clean"]["verbs_unclaimed_in_table"] == ["scrub"], str(audit["clean"]))
for fam in ("lamp", "door", "clock", "wear", "sketch"):
    check(f"{fam}: full verb+object coverage, zero unclaimed either side",
          audit[fam]["verbs_unclaimed_in_table"] == [] and audit[fam]["objects_unclaimed_in_table"] == [],
          str(audit[fam]))

_row = AC.BY_FAMILY["tea"]
check("the tea table row is still 8 verbs / 4 objects (this job changed no table row)",
      len(_row.verbs) == 8 and len(_row.objects) == 4, f"{len(_row.verbs)} verbs, {len(_row.objects)} objects")

# (a) no two behaviours within the SAME family claim the same verb+object PAIR (accidental ambiguity check;
#     candle_light/lamp_light both use verb "light" but different objects, which is fine and expected)
seen_pairs: dict[tuple, list] = {}
for name, fam, verbs, objects in SL._STUDY_HANDS:
    for v in verbs:
        for o in objects:
            seen_pairs.setdefault((fam, v, o), []).append(name)
ambiguous = {k: sorted(v) for k, v in seen_pairs.items() if len(v) > 1}
check("no two behaviours in the same family claim an identical verb+object pair", ambiguous == {}, str(ambiguous))

# (b) every verb x object pair a behaviour claims, _wills_study() actually accepts (sanity on the helper itself)
for name, fam, verbs, objects in SL._STUDY_HANDS:
    v0, o0 = verbs[0], objects[0]
    probe = f"i will {v0} the {o0} now"
    check(f"_wills_study accepts its own first verb+object for {name!r}", SL._wills_study(probe, name), probe)

# (c) the source itself: the specific old hand-kept fragments this job removed are gone
src = (ROOT / "core" / "study_life.py").read_text(encoding="utf-8")
body = src[src.index("def act(action:"):]
REMOVED_FRAGMENTS = (
    '"put", "set", "fill", "boil"',                       # the TOP-PRIORITY kettle bug (bare put/set)
    're.search(r"\\bash\\b", t)',                          # the bare-ash grate_clear bug
    '"light", "lit", "strike"',                            # the candle-light bare-substring bug
    'any_object_ok=True)\n                or _h.wants(t, ("draw",)',  # the old sketch veto shape
    '"pull to"',                                            # window_shut's dropped false-fire phrase
    '"take the coat", "get the coat", "shrug"',
    '"kick off", "unlace", "off the boots"',
    '"unlatch", "push up"',
    '"back", "part"',
)
for frag in REMOVED_FRAGMENTS:
    check(f"study_life.py act() no longer contains {frag!r}", frag not in body)
check("act() now family-scopes every one of the nine study families, not just candles",
      body.count('family in (None, "", ') >= 20, f"count={body.count(chr(39)+'family in (None, ')}")

print("\n-- part 1b: hand_delta regressions frozen from J-0739's own corpus check (permanent, no live data needed)")
# Each pair is a REAL text (or a minimal synthetic standing in for a truncated/ambiguous real one) from
# data/hands_trace.jsonl at the time of this job's own analysis; see docs/staged/actions_expansion.md's
# Current State note and F-1082 for the full counts these are drawn from.
REGRESSIONS = (
    # (name, text, should_fire) — "should_fire" is what _wills_study(text, name) must now return
    ("candle_light", "the candlelight casts dancing shadows across the room", False),  # compound noun self-match
    ("candle_light", "the lamp sputters; ink runs dry. i will fetch candles from the box. "
                      "the fire banks itself well enough for now, but the room needs its own light to think clearly.", False),
    ("candle_light", "i will light a candle before the lamp is filled", True),
    ("grate_clear", "the ash swirls like transition, a thing i must accept before the fire settles", False),
    ("grate_clear", "i want to sweep the grate and tend the fire", True),
    ("grate_clear", "i rake the cold ash from the grate into the bucket by the door", True),
    ("floor_sweep", "a hard gust sweeps the wood over, scattering leaf-mould at my feet", False),
    ("floor_sweep", "i will sweep the floor before the light goes", True),
    ("kettle_on", "i put the cup down on the shelf by the kettle", False),  # the exact bug the table's own fix documents
    ("kettle_on", "i will put the kettle on and wait for it to boil", True),
    # cross-clause "hang"/"wear": a PERIOD separates the clauses, matching the real corpus shape
    # ("the cold dampness bites through my coat. travis's words on plato hang in the air like
    # mist..." — two sentences, "coat" and "hang" never share a clause) — hands.wants()'s clause
    # scoping is what the old bare-substring test lacked entirely.
    ("coat_off", "the cold dampness bites through my coat. travis's words hang in the air like mist.", False),
    ("coat_off", "i take off my coat and hang it by the door", True),
    ("boots_on", "the cold water laps at my boots. the picture hangs crooked on the wall.", False),
    ("boots_on", "i pull on my boots before going out", True),
    ("window_shut", "i feel a restless pull toward the window, yet the open book waits", False),
    ("window_shut", "i shut the window and latch it against the wind", True),
    ("sketch_draw", "the gull's flight and the bee's labor draw my eyes outward instead", False),
    ("sketch_draw", "i will sketch the cat asleep by the fire", True),
    ("lamp_fill", "the lamp needs oil, but that is not the point right now", False),
    ("lamp_fill", "i fill the lamp from the can", True),
)
for name, text, expected in REGRESSIONS:
    got = SL._wills_study(text.lower(), name)
    check(f"{name} on {text[:60]!r}... -> {expected}", got == expected, f"got {got}")

print("\n-- part 2: act() routes through the derivation and family-scopes correctly (isolated stores)")
TMP = Path(tempfile.mkdtemp(prefix="study_life_grammar_"))
try:
    from core import sensorium as S
    S._STATE_F = TMP / "room_state.json"
    # J-0918 (F-1282 cause B): removing profile.mark_live() below (see the dated note) surfaced two
    # real gaps here -- core.provisions had no entry at all (_F/_LOG, reached via a gathering deed's
    # own provisioning side effect, same module J-0732 already found for shore_life.py and J-0918
    # also added to fieldcraft.py/wood_life.py's own lists this pass) and raised a hard
    # NonLiveWriteError on the very first act() call; core.locomotion had no entry either (real store
    # is "_POS_F", per core/locomotion.py:34) and its own refused write is swallowed somewhere in the
    # call chain above this script (this fence's own already-documented "further outer swallow"
    # pattern, J-0917/J-0931) rather than raising here -- still added for the same reason J-0743's own
    # sweep gives: an explicitly isolated store, not a silently-refused-and-dropped one, so this
    # script's own assertions stay meaningful if a walk/carry deed's outcome ever depends on it.
    for mod, attrs in (("core.study_life", ("_LEDGER", "_EVENTS")),
                       ("core.garden", ("_F", "_LEDGER", "_EVENTS")),
                       ("core.supply", ("_F", "_LOG")) if True else (None, ()),
                       ("core.world_objects", ("_OBJECTS_F",)),
                       ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")),
                       ("core.world_traces", ("_TRACES_F",)),
                       ("core.hands", ("_TRACE",)),
                       ("core.procedures", ("_F", "_LOG")),
                       ("core.provisions", ("_F", "_LOG")), ("core.locomotion", ("_POS_F",))):
        if mod is None:
            continue
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

    # J-0918 (F-1282 cause B): profile.mark_live() used to be called here. It doesn't just mark
    # THIS script's own redirected paths as safe -- guard_path() returns EVERY path unchanged once
    # LIVE is True, so it silently defeated D-0179's hard-raise fence for every already-fenced
    # module this script does NOT explicitly redirect above, not only the ones it forgot to. Removed
    # so a redirect-list gap now fails loud (NonLiveWriteError) instead of leaking into data/ while
    # this script's own check()s stay green. See docs/staged/world_store_write_fence.md's dated note.

    S.state.clear()
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "burning", "fire_fuel": 0.5,
                    "last_event": 0, "location": "study"})

    st = SL._st()
    # give the room enough real state to actually answer, not just decline for lack of props
    st["items"]["coat"]["place"] = "study"
    st["items"]["boots"]["place"] = "study"
    st["items"]["oil_can"]["place"] = "study"; st["items"]["ash_bucket"]["place"] = "study"
    st["items"]["hearth_brush"]["place"] = "study"; st["items"]["broom"]["place"] = "study"
    st["items"]["cloth"]["place"] = "study"; st["items"]["water_pail"]["place"] = "study"
    st["water"] = 0.9; st["ash"] = 0.5; st["matches"] = 5; st["lamp_oil"] = 0.9
    st["door_open"] = False; st["window_open"] = False

    POSITIVE = (
        ("i pull on my boots", "wear", "boots_on"),
        ("i open the door", "door", "door_open"),
        ("i light the lamp", "lamp", "lamp_light"),
        ("i wind the clock", "clock", "clock_wind"),
        ("i will sketch the cat asleep by the fire", "sketch", "sketch_draw"),
    )
    for text, fam, name in POSITIVE:
        ans = SL.act(text, "", family=fam)
        check(f"family={fam!r} answers its own thought {text!r}", ans is not None, repr(ans))

    # family scope: a wrong-but-known family declines immediately; family=None/"" still runs the full chain
    _BOOT_T = "i pull on my boots"
    ans_wrong = SL.act(_BOOT_T, "", family="tea")
    check("family='tea' (a different family) declines the boots thought immediately", ans_wrong is None, repr(ans_wrong))
    st["boots_on"] = False
    ans_legacy = SL.act(_BOOT_T, "")
    check("family='' (the legacy/unscoped sensorium.act() forward) still answers, unchanged", ans_legacy is not None, repr(ans_legacy))

    _DOOR_T = "i open the door"
    st["door_open"] = False
    check("family='wear' declines a door thought", SL.act(_DOOR_T, "", family="wear") is None)
    st["door_open"] = False
    check("family='door' answers its own thought", SL.act(_DOOR_T, "", family="door") is not None)

    _LAMP_T = "i light the lamp"
    st["lamp_lit"] = False
    check("family='clock' declines a lamp thought", SL.act(_LAMP_T, "", family="clock") is None)
    st["lamp_lit"] = False
    check("family='lamp' answers its own thought", SL.act(_LAMP_T, "", family="lamp") is not None)

    an_unknown = SL.act(_BOOT_T, "", family="not_a_real_family")
    check("an unrecognised family string declines immediately (defensive symmetry, F-1059's own ask)",
          an_unknown is None, repr(an_unknown))

    # negatives: the drifted copies' false fires answer NOTHING from the real hand end-to-end
    st["candles"] = 3
    NEGATIVE = (
        ("the candlelight casts dancing shadows across the room", "lamp"),
        ("a hard gust sweeps the wood over, scattering leaf-mould at my feet", "clean"),
        ("i feel a restless pull toward the window, yet the open book waits", "door"),
        ("the cold water laps at my boots. the picture hangs crooked on the wall.", "wear"),
    )
    for text, fam in NEGATIVE:
        ans = SL.act(text, "", family=fam or "")
        check(f"does not answer (drift closed): {text[:60]!r}...", ans is None, repr(ans))
except Exception as exc:
    import traceback; traceback.print_exc()
    check("part 2 ran", False, repr(exc))
finally:
    print(f"   isolated dir {TMP}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILED'}")
sys.exit(1 if FAILS else 0)
