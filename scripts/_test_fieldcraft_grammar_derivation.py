"""Regression for J-0736/F-1059 (2026-09-07): core/fieldcraft.py's act_from_thought() READS the grammar of
its thirteen crafts from the ONE table in core/actions.py ('fieldcraft' row: 18 verbs, 20 objects) via the
_FIELDCRAFT_HANDS verb+object partition — before this job every branch was a second, hand-kept copy, and
several had no verb requirement at all (a bare object, or even a bare two-word phrase, was enough to fire).
Mirrors scripts/_test_garden_grammar_derivation.py's shape (J-0543/J-0569's own template for this exact
procedure), adapted for fieldcraft's own difference: BOTH verbs and objects are partitioned per craft here
(garden's trap/tool/compost partition verbs only), because fieldcraft's thirteen crafts are semantically
unrelated to one another where trap/tool/compost's sub-hands are not.

Part 1 is pure (grammar_audit() against actions.BY_FAMILY["fieldcraft"], the corpus-evidenced widen/drift
assertions, a source-text scan for old hand-kept phrase lists). Part 2 exercises act_from_thought with
every store it touches redirected into a temp dir (the life_smoke isolation pattern) — the live data/ is
never written.
    python scripts/_test_fieldcraft_grammar_derivation.py
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

def _stat_or_none(p: Path):
    """(mtime, size) of a path, or None if it doesn't exist -- used by part 2's live-untouched canary
    (J-0878/F-1236) so 'never existed' can be told apart from 'existed and never moved'."""
    try:
        st = p.stat()
        return (st.st_mtime, st.st_size)
    except OSError:
        return None

def _live_status(before, after):
    """Describe what happened to a live data file across part 2's run, from _stat_or_none() snapshots
    taken before and after. A bare .exists() read cannot tell 'absent' from 'present and untouched' --
    it reports the same False for both a real worktree (no data/ dir at all) and a real leak, which is
    exactly what read as a leak report in J-0832 (F-1236)."""
    if before is None and after is None:
        return "absent"
    if before == after:
        return "unchanged"
    return f"CHANGED ({before} -> {after})"

print("-- part 1: the derivation (pure)")
from core import actions as AC, hands as H, fieldcraft as FCFT

audit = FCFT.grammar_audit()
check("grammar_audit ran", "error" not in audit, str(audit))
check("every table verb is claimed by some craft", audit.get("verbs_unclaimed_in_table") == [], str(audit))
check("no craft claims a verb the table does not have", audit.get("verbs_claimed_not_in_table") == [], str(audit))
check("only 'knot' is a deliberately-unclaimed table object (see _FIELDCRAFT_HANDS's own note)",
      audit.get("objects_unclaimed_in_table") == ["knot"], str(audit))
check("no craft claims an object the table does not have", audit.get("objects_claimed_not_in_table") == [], str(audit))

_row = AC.BY_FAMILY["fieldcraft"]
# J-2483 (2026-10-28, D-0504): the row grew to 32 verbs / 44 objects for the practical-school rung 2-3
# hands (14 verbs, 24 objects added, each claimed by exactly one craft -- the audit checks above prove
# it). The original J-0736 assertion ("this job changed no table row") is kept as an exact count so the
# next widening has to say so here too.
check("the table row is 32 verbs / 44 objects (18/20 from J-0736, +14/+24 from J-2483)",
      len(_row.verbs) == 32 and len(_row.objects) == 44, f"{len(_row.verbs)} verbs, {len(_row.objects)} objects")

# (a) no two crafts claim the same verb+object PAIR, except the one DELIBERATE overlap: "hitch"/"stake"
#     on clothesline+handrail (both hands share the clove-hitch/bowline skill check core/actions.py's own
#     comment names — see _FIELDCRAFT_HANDS's note). act_from_thought()'s own if/elif order breaks the
#     tie (clothesline is checked first); this just confirms no OTHER, accidental overlap crept in.
seen_pairs: dict[tuple, list] = {}
for craft, verbs, objects in FCFT._FIELDCRAFT_HANDS:
    for v in verbs:
        for o in objects:
            seen_pairs.setdefault((v, o), []).append(craft)
ambiguous = {k: sorted(v) for k, v in seen_pairs.items() if len(v) > 1}
expected_overlap = {(v, o): ["clothesline", "handrail"] for v in ("tie", "lash", "string", "rig") for o in ("hitch", "stake")}
check("the only verb+object overlap between crafts is the deliberate clothesline/handrail one "
      "(hitch/stake, per core/actions.py's own comment) — no accidental overlap crept in",
      ambiguous == expected_overlap, str({k: v for k, v in ambiguous.items() if expected_overlap.get(k) != v}))

# (b) every verb x object pair a craft claims, _wills_craft() actually accepts
for craft, verbs, objects in FCFT._FIELDCRAFT_HANDS:
    miss = [(v, o) for v in verbs for o in objects if not FCFT._wills_craft(f"i {v} the {o}", craft)]
    check(f"{craft}: _wills_craft accepts every verb x object pair it claims ({len(verbs)}x{len(objects)})",
          not miss, str(miss[:6]))
check("an unknown craft name fails closed", not FCFT._wills_craft("i tie the line", "no_such_craft"))

# (c) the corpus-confirmed widenings reach the hand (J-0736, data/hands_trace.jsonl)
check("hang_coat: the table's real grammar ('hang'/'peg' + 'coat'/'line') now reaches the hand "
      "(2 real corpus thoughts: 'i hang my coat on the hook...')",
      FCFT._wills_craft("i hang my coat on the hook, feeling the dampness leave my skin", "hang_coat"))
check("clothesline: the practical-school 'hitch' widening (J-0627/D-0159) reaches the hand",
      FCFT._wills_craft("i will tie the hitch before i lose the light", "clothesline"))
check("handrail: the practical-school 'stake' widening (J-0627/D-0159) reaches the hand",
      FCFT._wills_craft("i lash the stake tight before the wind gets up", "handrail"))

# (d) the corpus-confirmed drifted false-fires are closed (J-0736, data/hands_trace.jsonl quotes below)
check("uncover_fire: the bare phrase 'the banked' fire (Du's own cosy-room scene-setting, 22/22 real "
      "corpus hits, never a deed) no longer reaches the hand",
      not FCFT._wills_craft("i sit before the banked fire, watching the light dance on the walls", "uncover_fire"))
check("uncover_fire: a real uncover still reads ('i uncover the fire and rake the ash back')",
      FCFT._wills_craft("i uncover the fire and rake the ash back", "uncover_fire"))
check("whittle: bare 'carve' idiom (15/18 real corpus hits, e.g. 'patterns we carve from chaos') no "
      "longer reaches the hand without a real made-thing object",
      not FCFT._wills_craft("maybe they're not ideals but patterns we carve from chaos", "whittle"))
check("whittle: a real whittle still reads ('i will whittle a small stick')",
      FCFT._wills_craft("i will whittle a small stick by the fire", "whittle"))
check("whittle: 'whittled' (past participle — the recurring keepsake-stick REFERENCE, 14 real corpus "
      "hits) was already excluded by hands.wants()'s own word-boundary rule, not by this job's object "
      "gate — confirmed still excluded",
      not FCFT._wills_craft("i reach for the whittled stick on the sand below me", "whittle"))
check("follow_trail: the restlessness idiom ('i must follow it', a pronoun object) no longer reaches "
      "the hand (5/5 real corpus hits were this idiom)",
      not FCFT._wills_craft("that pull toward something else is real; i must follow it", "follow_trail"))
check("follow_trail: a real follow still reads ('i follow the cat's prints across the lawn')",
      FCFT._wills_craft("i follow the cat's prints across the lawn", "follow_trail"))
check("strike_flint: the bare object 'flint' (1/1 real corpus hit was a geological musing, never a "
      "deed) no longer reaches the hand without the verb",
      not FCFT._wills_craft("that flint-knapped stone on the sand feels heavy yet hollow", "strike_flint"))
check("strike_flint: a real strike still reads ('i strike the flint and steel together')",
      FCFT._wills_craft("i strike the flint and steel together", "strike_flint"))
check("measure_by_shadow: the extra 'cliff' object (1/1 real corpus hit was the restlessness idiom) no "
      "longer reaches the hand",
      not FCFT._wills_craft("i do not need to conquer the void or measure it from a single cliff-top", "measure_by_shadow"))
check("measure_by_shadow: a real measure still reads ('i pace out the shadow and measure it')",
      FCFT._wills_craft("i pace out the shadow and measure it", "measure_by_shadow"))
check("bank_fire: the extra 'cover'/'grate' (0/73 real corpus hits ever needed them — 73 old = 73 new) "
      "are gone; a real bank still reads",
      FCFT._wills_craft("i bank the fire under a good bed of ash", "bank_fire")
      and not FCFT._wills_craft("i cover the model with a cloth", "bank_fire"))

# (e) the source itself: no hand-kept phrase-list copy of a craft's grammar left in fieldcraft.py
src = (ROOT / "core" / "fieldcraft.py").read_text(encoding="utf-8")
body = src[src.index("def act_from_thought("):]
for phrase in ('"clothes line", "washing line"', '"hang the coat", "peg the coat"',
               '"wind-break", "shelter on the shore"', '"hand-line", "hand line"',
               '"the banked", "see if the embers"', '"steel and flint"',
               '"put out the fire", "put the fire out", "smother the fire"',
               'any_object_ok=True'):
    check(f"fieldcraft.py act_from_thought no longer contains {phrase!r}", phrase not in body)
check("act_from_thought() now takes a family= parameter (J-0554 pattern, per F-1059)",
      "family: str | None = None" in src[:src.index("def act_from_thought(") + 400])

print("\n-- part 2: act_from_thought routes through the derivation (isolated stores)")
TMP = Path(tempfile.mkdtemp(prefix="fieldcraft_grammar_"))
# J-0878 (F-1236): a bare live.exists() here used to read "untouched: False" whenever ROOT/data/fieldcraft.json
# simply doesn't exist (every run inside a git worktree, which has no data/ dir at all) and "untouched: True"
# whenever it happens to exist regardless of whether THIS run touched it -- inverted wording that looked like
# a leak report (J-0832 initially read it as one). Snapshot before part 2 runs, compare for real after.
_LIVE = ROOT / "data" / "fieldcraft.json"
_LIVE_BEFORE = _stat_or_none(_LIVE)
_real_sun = None   # J-1324: captured/restored inside try/finally below
try:
    from core import sensorium as S, world_clock as WC
    S._STATE_F = TMP / "room_state.json"
    FCFT._F = TMP / "fieldcraft.json"
    FCFT._LEDGER = TMP / "fieldcraft_ledger.jsonl"
    # J-1324 (2026-09-24, following F-1872's sibling finding for shore_life_grammar's own tide gate):
    # measure_by_shadow() (below, one of the five positives this loop exercises) opens with
    # `s = _wc.sun(); if not s.get("up"): return "No sun, no shadow; it will have to wait for day."` --
    # core.world_clock.sun() is a pure function of REAL wall-clock time (his own NZ seasonal sunrise/
    # sunset table), not anything this isolation block resets, so whether the positives loop's own
    # `ans is not None` check ever reaches measure_by_shadow's real body (its _try()/_save()/_log(),
    # gated on nothing else) depends on whether it happens to be day where the process runs its clock
    # at the exact moment this script runs -- a decline STRING is itself non-None, so the check cannot
    # tell the two branches apart either way (confirmed empirically, not just by inspection -- see this
    # job's own finding). Pinned to a fixed daytime sun position so the real body is guaranteed every
    # run, matching scripts/life_smoke.py's own already-established month-pinning convention (G._month)
    # for the same class of real-time gate; restored in this block's own finally below regardless of how
    # part 2 exits. core.world_clock.sun is patched at the MODULE level (not a local FCFT reference)
    # because measure_by_shadow() does its own `from core import world_clock as _wc` fresh on every call
    # -- that import binds the same module object this WC does, so setting WC.sun here is what it sees.
    _real_sun = WC.sun
    WC.sun = lambda t=None: {"up": True, "phase": "high", "az": 0.0, "f": 0.5}
    # J-0918 (F-1282 cause B): removing profile.mark_live() below (see the dated note) turned three
    # real gaps in this list -- confirmed by guard_path()'s own refusal warnings on an unfixed run --
    # into visible NonLiveWriteError attempts instead of silent live writes: core.provisions (_F/_LOG,
    # reached via a craft's own provisioning side effect), core.world_traces (_TRACES_F), and
    # core.procedures (_F/_LOG, now guard_path()-fenced itself since J-0917/F-1296 -- before that it
    # leaked unconditionally regardless of this list). All three added here, same pattern as J-0743's
    # own sweep below.
    for mod, attrs in (("core.garden", ("_F", "_LEDGER", "_EVENTS")), ("core.study_life", ("_LEDGER", "_EVENTS")),
                       ("core.world_objects", ("_OBJECTS_F",)), ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")),
                       ("core.wood_life", ("_F", "_EVENTS", "_LEDGER")),
                       # J-0832 (F-1198): ("core.life_traces", ("_F",)) removed -- life_traces.py owns no file store
                       # (it writes through other modules' already-fenced stores); the entry was inert.
                       ("core.hands", ("_TRACE",)),
                       ("core.provisions", ("_F", "_LOG")), ("core.world_traces", ("_TRACES_F",)),
                       ("core.procedures", ("_F", "_LOG"))):
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
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0, "location": "wood"})

    # J-0918 (F-1282 cause B): profile.mark_live() used to be called here. It doesn't just mark
    # THIS script's own redirected paths as safe -- guard_path() returns EVERY path unchanged once
    # LIVE is True, so it silently defeated D-0179's hard-raise fence for every already-fenced
    # module this script does NOT explicitly redirect above, not only the ones it forgot to. Removed
    # so a redirect-list gap now fails loud (NonLiveWriteError) instead of leaking into data/ while
    # this script's own check()s stay green. See docs/staged/world_store_write_fence.md's dated note.

    # PRECONDITION RIG (2026-09-24, J-1329/F-1878): the SAME "early decline vs. real body" shape
    # J-0920/F-1347 already found and fixed for garden's own grammar-derivation script -- found here
    # (empirically, ledger-content inspection across repeat runs, not source-reading alone) for 3 of
    # THIS script's own 5 positives-loop deeds: whip_end/follow_trail below, by rigging one real,
    # reachable precondition directly into each store's own cached state (the identical technique).
    # strike_flint is fixed separately, a few lines below the loop -- its own gate is a LOCATION, not
    # an item, so no item rig can reach it from this loop's own location="wood" pin (see that block).
    from core import study_life as _sl, garden as _g, world_traces as _wt
    _sl._st()["items"]["rope"]["carried"] = True   # whip_end: rope's own default place is "shelf_east"
    # (core/study_life.py's own _ITEMS), never any top-level location string whip_end()'s own bare
    # `rope.get("place") == here` could ever match (F-1878 left this one's exact root cause
    # unconfirmed; traced here) -- carried=True sidesteps the place/here mismatch entirely, and needs
    # no _save(): _st() returns a dict cached live inside sensorium.state (confirmed by direct source
    # read), already mutated in place by this same file's own S.state.clear()/update() just above.
    _g._load()["items"]["twine"]["carried"] = True   # whip_end also needs _has_twine() true (core/
    # fieldcraft.py's own cross-link into core.garden's item store); core.garden._load() DOES cache
    # (`global _state`, confirmed by direct source read) so, like study_life's _st() just above, this
    # mutation is already live for any later _load() in this same process -- no _save() needed.
    _wt.create_trace("rig_follow_trail_J1329", "boot_prints", "wood", [0.0, 0.0, 0.0], clarity=0.8, cause="test_rig")
    # follow_trail: get_active_traces("wood") is empty on a fresh isolated core.world_traces store every
    # run (F-1878) -- a real trace, above the module's own clarity>0.2 floor, at this loop's own pinned
    # location="wood" (core.world_traces._TRACES_F is already redirected into TMP by the isolation list
    # above, so create_trace()'s own _save_traces() call cannot reach the live store).

    # positives: a real craft is answered (a decline STRING is still an answer; None is not)
    for t in ("i whip the rope's end before it frays", "i strike the flint and steel together",
              "i pace out the shadow and measure it", "i will whittle a small stick by the fire",
              "i follow the trail as far as it goes"):
        ans = FCFT.act_from_thought(t, "")
        check(f"answers {t!r}", ans is not None, repr(ans))

    # STRIKE_FLINT'S REAL BODY (J-1329/F-1878): strike_flint() requires `_where() == "study"` outright
    # (core/fieldcraft.py strike_flint():328-329, unconditional on any item state) -- it is genuinely a
    # hearth deed, not a wood one, so the loop above's own location="wood" pin can only ever reach this
    # early decline BY DESIGN, never a broken precondition -- the one judgement call this job's own
    # briefing named explicitly (mirroring wood_life's identical split() case, J-1329's sibling fix).
    # tinder (fieldcraft's own d["tinder"], bootstrap default 0.3) and flint (study_life's st["flint"],
    # synced True by default from core.provisions' own bootstrap stock -- confirmed by direct source
    # read, core/provisions.py's own `("flint", 1)` stock entry feeding sync()'s `st[key] = have > 0`)
    # both already clear their own floors without further rigging; only the location itself was ever
    # unmet. Exercised separately here, mirroring split()'s own sibling fix in wood_life's own script and
    # the family-scope checks just below that already re-call act_from_thought with different parameters
    # against this same isolated store; the loop's own check above is left exactly as it was.
    S.state["location"] = "study"
    _ans_flint = FCFT.act_from_thought("i strike the flint and steel together", "")
    check("strike_flint (location='study'): passes its own flint/tinder gates and reaches _try() "
          "(fire_lay) -- neither of the two early-decline strings (missing flint / missing tinder) is "
          "returned",
          bool(_ans_flint) and not _ans_flint.startswith(("There is no flint", "You have no tinder")),
          repr(_ans_flint))
    # restore before hang_coat/family-scope/negatives below, which assume this loop's own original pin.
    S.state["location"] = "wood"

    # hang_coat: declines honestly (no clothesline exists in this fresh isolated store) rather than
    # erroring or silently doing nothing unexplained
    ans = FCFT.act_from_thought("i hang my coat on the hook, feeling the dampness leave my skin", "")
    check("hang_coat: a fresh store (no clothesline yet) answers with the honest decline, not an error",
          ans == "", repr(ans))

    # family scope: an out-of-family string forces an immediate decline, matching J-0554's own pattern
    ans_scoped_out = FCFT.act_from_thought("i strike the flint and steel together", "", family="gather")
    check("family='gather' (a different family) declines immediately", ans_scoped_out is None, repr(ans_scoped_out))
    ans_scoped_in = FCFT.act_from_thought("i strike the flint and steel together", "", family="fieldcraft")
    check("family='fieldcraft' (its own family) still answers", ans_scoped_in is not None, repr(ans_scoped_in))
    ans_scoped_none = FCFT.act_from_thought("i strike the flint and steel together", "", family=None)
    check("family=None (the legacy/unscoped caller) still answers, unchanged", ans_scoped_none is not None, repr(ans_scoped_none))

    # negatives: the drifted copies' false fires return NOTHING from the hand
    for t in ("i sit before the banked fire, watching the light dance on the walls",
              "maybe they're not ideals but patterns we carve from chaos",
              "that pull toward something else is real; i must follow it",
              "that flint-knapped stone on the sand feels heavy yet hollow",
              "i do not need to conquer the void or measure it from a single cliff-top"):
        ans = FCFT.act_from_thought(t, "")
        check(f"does not answer (drift closed): {t!r}", ans is None, repr(ans))
except Exception as exc:
    import traceback; traceback.print_exc()
    check("part 2 ran", False, repr(exc))
finally:
    # J-1324: restore the real clock whatever happened above -- guarded by the None-init at the top of
    # this block so a failure before the capture line itself can never leave this raising instead.
    if _real_sun is not None:
        WC.sun = _real_sun
    print(f"   isolated dir {TMP}; live fieldcraft.json: {_live_status(_LIVE_BEFORE, _stat_or_none(_LIVE))}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILED'}")
sys.exit(1 if FAILS else 0)
