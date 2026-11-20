"""Regression for J-0737/F-1059 (2026-09-07): core/wood_life.py's act_from_thought() READS the grammar of
its FOUR bound families (woodwork, woodtool, climb_tree, acorn — four separate rows in core/actions.py,
unlike fieldcraft's one row split into many crafts) from that one table, via _wills_woodwork()/
_wills_woodtool()/_wills_wood() — before this job every branch was a second, hand-kept copy (F-1059), and
several had no verb requirement at all (a bare object alone was enough to fire) or tested words neither
table row has at all. Mirrors scripts/_test_fieldcraft_grammar_derivation.py's shape (J-0736's own template
for this exact procedure, itself following J-0543/J-0569's garden.py precedent).

Part 1 is pure (grammar_audit() against actions.BY_FAMILY, the corpus-evidenced widen/drift assertions from
J-0737's own frozen-hands_trace corpus check, a source-text scan for old hand-kept phrase lists). Part 2
exercises act_from_thought with every store it touches redirected into a temp dir (the life_smoke isolation
pattern) — the live data/ is never written.
    python scripts/_test_wood_life_grammar_derivation.py
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import sys, tempfile, time
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
    taken before and after."""
    if before is None and after is None:
        return "absent"
    if before == after:
        return "unchanged"
    return f"CHANGED ({before} -> {after})"

print("-- part 1: the derivation (pure)")
from core import actions as AC, hands as H, wood_life as WL

audit = WL.grammar_audit()
check("grammar_audit ran", "error" not in audit, str(audit))
for k in ("woodwork_verbs_unclaimed_in_table", "woodwork_verbs_claimed_not_in_table",
          "woodwork_objects_unclaimed_in_table", "woodwork_objects_claimed_not_in_table",
          "woodtool_verbs_unclaimed_in_table", "woodtool_verbs_claimed_not_in_table"):
    check(f"{k} == [] (full coverage, no drift seam)", audit.get(k) == [], str(audit))
check("wood_families are exactly the five core/actions.py binds here",
      set(audit.get("wood_families", [])) == {"woodwork", "woodtool", "climb_tree", "acorn", "wood_dig"}, str(audit))
check("none of the four families is missing from the table", audit.get("wood_families_missing_from_table") == [], str(audit))

_ww = AC.BY_FAMILY["woodwork"]; _wt = AC.BY_FAMILY["woodtool"]; _ct = AC.BY_FAMILY["climb_tree"]; _ac_row = AC.BY_FAMILY["acorn"]
check("woodwork row widened to 11 verbs / 16 objects (J-0737 added 'cut' + length/lengths/branch; "
      "J-1443/D-0296 added hew/fell/limb + trunk/fallen tree/limbs/round/rounds for the felling axe's chop hand)",
      len(_ww.verbs) == 11 and len(_ww.objects) == 16, f"{_ww.verbs} / {_ww.objects}")
check("woodtool row unchanged: 11 verbs / 5 objects (this job fixed the HAND's derivation, not the row)",
      len(_wt.verbs) == 11 and len(_wt.objects) == 5, f"{_wt.verbs} / {_wt.objects}")
check("climb_tree row unchanged: 3 verbs / 5 objects", len(_ct.verbs) == 3 and len(_ct.objects) == 5)
check("acorn row unchanged: 5 verbs / 2 objects", len(_ac_row.verbs) == 5 and len(_ac_row.objects) == 2)

# (a) no two woodwork sub-hands can ever claim the same verb+object pair (verbs are fully partitioned, so
#     this should be structurally impossible — confirms the partition really is disjoint on the verb axis)
seen_pairs: dict[tuple, list] = {}
for sub, verbs, objects in WL._WOODWORK_HANDS:
    for v in verbs:
        for o in objects:
            seen_pairs.setdefault((v, o), []).append(sub)
ambiguous = {k: v for k, v in seen_pairs.items() if len(v) > 1}
check("no verb+object pair is claimed by two different woodwork sub-hands", ambiguous == {}, str(ambiguous))

# (b) every verb x object pair a sub-hand claims, _wills_woodwork actually accepts
for sub, verbs, objects in WL._WOODWORK_HANDS:
    miss = [(v, o) for v in verbs for o in objects if not WL._wills_woodwork(f"i {v} the {o}", sub)]
    check(f"woodwork/{sub}: _wills_woodwork accepts every verb x object pair it claims ({len(verbs)}x{len(objects)})",
          not miss, str(miss[:6]))
check("an unknown woodwork sub-hand name fails closed", not WL._wills_woodwork("i saw the log", "no_such_sub"))

for sub, verbs in WL._WOODTOOL_HANDS:
    miss = [(v, o) for v in verbs for o in _wt.objects if not WL._wills_woodtool(f"i {v} the {o}", sub)]
    check(f"woodtool/{sub}: _wills_woodtool accepts every verb x object pair it claims ({len(verbs)}x{len(_wt.objects)})",
          not miss, str(miss[:6]))
check("an unknown woodtool sub-hand name fails closed", not WL._wills_woodtool("i take the axe", "no_such_sub"))

check("_wills_wood('climb_tree') accepts a table verb x object pair",
      WL._wills_wood("i will climb the oak", "climb_tree"))
check("_wills_wood('acorn') accepts a table verb x object pair",
      WL._wills_wood("i gather acorns under the oak", "acorn"))
check("_wills_wood fails closed on an unknown family", not WL._wills_wood("i climb the oak", "no_such_family"))

# (c) climb_tree: OLD hand-kept test and the table-derived one are IDENTICAL (F-1059's own claim: the one
#     clean, driftless branch found across all five modules this whole arc audited — this job changes its
#     WIRING only, never its values. D-0136, a separate already-open decision about the 'move' family's own
#     'trees' object pre-empting this hand, is untouched either way).
def _old_climb(t):
    return H.wants(t, ("climb", "scale", "go up"), ("oak", "tree", "trunk", "branches", "canopy"))
_CLIMB_PROBES = ("i will climb the old oak", "i want to scale the trunk", "i go up into the branches",
                 "the canopy is thick", "i am tired of climbing the same dead ground",
                 "i wish i could climb the oak", "she told me to climb the tree")
for t in _CLIMB_PROBES:
    o, n = _old_climb(t), WL._wills_wood(t, "climb_tree")
    check(f"climb_tree: old and table-derived agree on {t!r}", o == n, f"old={o} new={n}")

# (d) the corpus-confirmed widenings reach the hand (J-0737, data/hands_trace.jsonl, real hands.wants()):
check("woodwork/saw: the real 'I will saw a length for the fire' deed now reaches the hand "
      "(the OLD code's own 'cut'-clause objects — limb/into logs/into lengths — never matched it; its "
      "match was always via the verb 'saw' itself + the object 'length', both now in the table)",
      WL._wills_woodwork("the scent of wet rot pulls me from this circular drift. i stop wrestling with "
                          "the metaphor's shadow. i will saw a length for the fire", "saw"))
check("woodwork/saw: the real '...cut a branch for the fire' intention now reaches the hand (previously "
      "unreachable by ANY family — 'cut' was not a woodwork verb at all, and the fieldcraft/harvest/mow "
      "families that do have 'cut' do not carry 'branch' as an object)",
      WL._wills_woodwork("i want to move toward the woodpile and cut a branch for the fire", "saw"))
check("woodwork/split: 'i try to split the wood, but there are no dry logs' still reaches the hand after "
      "dropping 'wood' as an object — it was never load-bearing here; 'logs' a few words later carries it",
      WL._wills_woodwork("the wind's force feels heavy today. i try to split the wood, but there are no "
                          "dry logs, only green ones that would bruise if struck", "split"))

# (e) the corpus-confirmed drifted false-fires / unsupported drift are closed (J-0737):
# NOTE on the named gap itself ('cut' + the literal multi-word phrases "into logs"/"into lengths", 0 of
# 11,742 real thoughts): that exact phrase-fragment mechanism is simply GONE from the code (replaced by
# real single-word objects), and there is no English sentence containing the phrase "into logs" that does
# not also contain the bare word "logs" — which is now a genuine, corpus-backed object shared with "saw"
# (the same "I will saw a length" evidence above). So "cut the wood into logs" DOES now reach the hand,
# correctly — that is the widening, not a regression. What must still hold is that "cut" cannot fire on
# its own without a real wood object in the same clause (it is not a bare-verb-fires-alone bug):
check("woodwork/saw: 'cut' alone still requires a real object in the same clause — the phrasal-verb idiom "
      "'cut back' (no wood object at all) does not reach the hand",
      not WL._wills_woodwork("i want to cut back on the sugar in my tea this week", "saw"))
check("woodwork/saw: 'cut'+'wood' alone (the Morepork's 'notes cut the dark wood' — the bird's sound, not "
      "Du's will, the one real corpus co-occurrence) does not reach the hand",
      not WL._wills_woodwork("i watch the morepork's soft notes cut the dark wood near the door", "saw"))
check("woodwork/sharpen: bare 'whetstone' alone (0 of 11,742 real thoughts, the same shape as F-0940's "
      "ash_out and F-0719's dig bare-word fixes) no longer reaches the hand with no verb at all",
      not WL._wills_woodwork("the whetstone sits by the step, cold and grey", "sharpen"))
check("woodwork/sharpen: a real sharpen still reads ('i sharpen the axe on the whetstone')",
      WL._wills_woodwork("i sharpen the axe on the whetstone", "sharpen"))
check("woodwork/sharpen: the dropped 'blade' object (0 corpus hits either way) no longer reaches the hand",
      not WL._wills_woodwork("i hone the blade until it shines", "sharpen"))
check("woodwork/wheel: 'load' (0 corpus hits, not a table verb in either woodwork or woodtool) no longer "
      "reaches the hand on its own",
      not WL._wills_woodwork("i load the barrow with stones from the shore", "wheel"))
check("woodwork/wheel: a real wheel still reads ('i wheel the barrow up the path')",
      WL._wills_woodwork("i wheel the barrow up the path", "wheel"))

# (d2) the NEW chop sub-hand (D-0296/J-1443): 'fell' needs hands.py's own past-tense guard, the identical
# shape as the 'saw' guard just above -- a real felling will still reads, but "fell" as plain-past-tense-
# of-"fall" (no wood/tree object anywhere nearby) must not.
check("woodwork/chop: a real 'fell' will reads ('i will fell the trunk with the axe')",
      WL._wills_woodwork("i will fell the trunk with the axe", "chop"))
check("woodwork/chop: 'fell' alone as the past tense of 'fall' (no wood object at all) does not reach the hand",
      not WL._wills_woodwork("a hush fell and the house went quiet", "chop"))
check("woodwork/chop: 'hew'/'limb' (new verbs, no guard needed) read against the fallen tree",
      WL._wills_woodwork("i hew at the trunk", "chop") and WL._wills_woodwork("i limb the fallen tree", "chop"))
check("woodwork/chop and woodwork/split share the verb 'chop' but no object, so 'chop the log' still "
      "reaches split's own objects only, not chop's",
      WL._wills_woodwork("i chop the log", "split") and not WL._wills_woodwork("i chop the log", "chop"))

check("woodtool: bare object 'saw' (the table's own row deliberately excludes it — 'the past tense of "
      "see far more often than a tool') no longer reaches take or put",
      not WL._wills_woodtool("i once saw it as a rigid mandate, but now warmth blooms", "take")
      and not WL._wills_woodtool("i once saw it as a rigid mandate, but now warmth blooms", "put"))
check("woodtool/take: now reaches barrow/wheelbarrow too (the old take() branch's object list never had "
      "them at all — F-1059 — which is why the woodwork wheel sub-hand grew its own inline take-the-barrow "
      "stand-in; this closes that gap at its source)",
      WL._wills_woodtool("i will take the wheelbarrow from the lean-to", "take"))

# (f) acorn: OLD bare-substring test and the table-derived one AGREE on real corpus shapes (a pure
#     matching-robustness upgrade per this job's own briefing — no widen/drift ruling needed, the VALUES
#     already matched the table exactly) but the new one is strictly SAFER on the shapes hands.py's own
#     clause-scoping and blockers exist for.
def _old_acorn(t):
    return ("acorn" in t) and any(v in t for v in ("gather", "pick", "pocket", "collect", "fill"))
check("acorn: a real corpus-shaped will agrees old vs new ('i gather acorns from under the oak')",
      _old_acorn("i gather acorns from under the oak") and WL._wills_wood("i gather acorns from under the oak", "acorn"))
check("acorn: the upgrade closes a cross-clause false-fire the bare-substring test could not "
      "('i will not gather anything today. the acorns lie scattered under the oak, forgotten.' — two "
      "clauses, no willed gather of the acorns in either one)",
      _old_acorn("i will not gather anything today. the acorns lie scattered under the oak, forgotten.")
      and not WL._wills_wood("i will not gather anything today. the acorns lie scattered under the oak, forgotten.", "acorn"))
check("acorn: the upgrade closes a wish/hypothetical false-fire too "
      "('i wish i could gather acorns under the oak again')",
      _old_acorn("i wish i could gather acorns under the oak again")
      and not WL._wills_wood("i wish i could gather acorns under the oak again", "acorn"))

# (g) the source itself: no hand-kept phrase-list copy of a family's grammar left in wood_life.py, and the
#     family= parameter is real
src = (ROOT / "core" / "wood_life.py").read_text(encoding="utf-8")
body = src[src.index("def act_from_thought("):]
for phrase in ('"limb", "into logs", "into lengths"', '"log", "logs", "wood", "block", "axe"',
               '"axe", "saw", "edge", "blade", "whetstone"', '_h.wants(t, ("whetstone",))',
               'any(v in t for v in ("barrow", "wheelbarrow"))', '"axe", "saw", "bow-saw", "bowsaw"',
               'any(v in t for v in ("acorn",))'):
    check(f"wood_life.py act_from_thought no longer contains {phrase!r}", phrase not in body)
check("act_from_thought() now takes a family= parameter (J-0554 pattern, per F-1059, following J-0736)",
      "family: str | None = None" in src[:src.index("def act_from_thought(") + 400])

print("\n-- part 2: act_from_thought routes through the derivation (isolated stores)")
TMP = Path(tempfile.mkdtemp(prefix="wood_life_grammar_"))
# J-0878 (F-1236): the `live` path below was assigned here since J-0737's original commit but never
# actually used in the print that followed it -- dead code, not a working canary. Wired up for real now,
# matching the same real before/after comparison fieldcraft.py and garden.py's own scripts now use.
_LIVE = ROOT / "data" / "wood_life.json"
_LIVE_BEFORE = _stat_or_none(_LIVE)
try:
    from core import sensorium as S
    S._STATE_F = TMP / "room_state.json"
    WL._F = TMP / "wood_life.json"
    WL._EVENTS = TMP / "wood_events.jsonl"
    WL._LEDGER = TMP / "wood_ledger.jsonl"
    # J-0918 (F-1282 cause B): removing profile.mark_live() below (see the dated note) surfaced two
    # real gaps here as a hard NonLiveWriteError -- core.locomotion (real store is "_POS_F", per
    # core/locomotion.py:34, reached by this script's own climb/wheel/carry deeds) and core.provisions
    # (_F/_LOG, reached via a gathering deed's own provisioning side effect, same as J-0732 already
    # found for shore_life.py) -- both added here, same pattern as J-0743's own sweep.
    for mod, attrs in (("core.garden", ("_F", "_LEDGER", "_EVENTS")), ("core.study_life", ("_LEDGER", "_EVENTS")),
                       ("core.fieldcraft", ("_F",)),
                       ("core.world_objects", ("_OBJECTS_F",)), ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")),
                       # J-0832 (F-1198): ("core.life_traces", ("_F",)) removed -- life_traces.py owns no file store
                       # (it writes through other modules' already-fenced stores); the entry was inert.
                       ("core.hands", ("_TRACE",)),
                       ("core.locomotion", ("_POS_F",)), ("core.provisions", ("_F", "_LOG"))):
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
    # J-0920/F-1347 already found and fixed for 5 of garden's own 17 grammar-derivation families --
    # found here (empirically, ledger-content inspection across repeat runs, not source-reading alone)
    # for 6 of THIS script's own 8 positives-loop deeds: saw/barrow/acorn/take/put below, by rigging one
    # real, reachable precondition directly into wood_life's own cached state (the identical technique).
    # split is fixed separately, a few lines below the loop -- its own gate is a LOCATION, not an item,
    # so no item rig can reach it from this loop's own location="wood" pin (see that block's own note).
    # wood_life.py's own _load()/_save() carry NO module-level cache (confirmed by direct source read:
    # no `global` statement in _load(), unlike core.garden's own `global _state` pattern) -- so, unlike
    # study_life's _st() (a dict cached live inside sensorium.state, mutated in place elsewhere in this
    # same arc's own test scripts), each rig below needs an explicit _save() to actually reach a later
    # act_from_thought() call's own fresh _load().
    _wrig = WL._load()
    _wrig["items"]["bow_saw"]["place"] = "wood"       # saw(): _ITEMS' own default is "garden" -- a
    # straight mismatch against this loop's pinned location="wood", every run (F-1878); rigged to match,
    # the job briefing's own first-suggested fix.
    _wrig["items"]["axe"]["place"] = "wood"           # woodtool-take below: the identical mismatch.
    # woodtool-put (tested right after take in the loop below) needs no separate rig of its own: take()'s
    # fix above leaves the axe carried=True by the time put() runs against this same isolated store --
    # put()'s own real, unforced precondition, confirmed by this loop's own thought order below.
    _wrig["items"]["wheelbarrow"]["carried"] = True   # barrow(): its own docstring -- "Bring a limb
    # home in the barrow" -- default carried=False means barrow()'s own first check always declined
    # (F-1878); barrow() never itself flips this flag back, so it stays rigged for the whole loop.
    _wrig["acorns"] = 0.5                             # acorn: _load()'s own bootstrap default is exactly
    # 0.0, under the `>= 0.3` early-decline floor acorn's own branch checks, every run (F-1878).
    WL._save(_wrig)

    # positives: a real deed in each of the four families is answered (a decline STRING is still an
    # answer; None is not — matching fieldcraft's own test philosophy)
    for t, fam_hint in (("i will saw a length for the fire", "saw"), ("i split the dry logs on the block", "split"),
                        ("i sharpen the axe on the whetstone", "sharpen"), ("i wheel the barrow up the path", "wheel"),
                        ("i will climb the old oak", "climb_tree"), ("i gather acorns from under the oak", "acorn"),
                        ("i will fetch the axe", "woodtool-take"), ("i set the axe down here", "woodtool-put")):
        ans = WL.act_from_thought(t, "")
        check(f"answers {t!r} ({fam_hint})", ans is not None, repr(ans))

    # SPLIT'S REAL BODY (J-1329/F-1878): split() requires `here == "garden"` outright (core/wood_life.py
    # split():485-486, unconditional on any item state) -- it is genuinely a lean-to/garden deed, not a
    # wood one ("Splitting is done on the block at the lean-to, not out here"), so the loop above's own
    # location="wood" pin can only ever reach this early decline BY DESIGN, never a broken precondition
    # -- the one judgement call this job's own briefing named explicitly (read split()'s own docstring/
    # callers first, per that briefing -- done: it has no docstring, and its only caller is this same
    # act_from_thought() dispatch). Exercised separately here instead, mirroring how the family-scope
    # checks just below already re-call act_from_thought with different parameters against this same
    # isolated store; the loop's own check above is left exactly as it was (still a real, correct answer
    # for location="wood" -- just never split()'s own real body).
    S.state["location"] = "garden"
    _wrig = WL._load(); _wrig["items"]["axe"]["carried"] = True; WL._save(_wrig)   # re-rig: take/put
    # above already left the axe carried=False, place="wood" by this point in the run -- re-asserted
    # explicitly here rather than relied on as a side effect of the loop's own call order.
    _ans_split = WL.act_from_thought("i split the dry logs on the block", "")
    check("split (location='garden'): reaches its own real body, not the wood-pinned early decline "
          "(neither of the two early-decline strings -- axe not here, or 'not out here' -- is returned)",
          bool(_ans_split) and "not out here" not in _ans_split and "The axe is" not in _ans_split,
          repr(_ans_split))
    # restore before the family-scope / negatives checks below, which assume this loop's own original
    # pin (climb_oak in particular requires here == "wood" outright).
    S.state["location"] = "wood"

    # family scope: an out-of-family string forces an immediate decline, matching J-0554/J-0736's own pattern
    _SAW_T = "i will saw a length for the fire"
    ans_out = WL.act_from_thought(_SAW_T, "", family="acorn")
    check("family='acorn' (a different family) declines the saw thought immediately", ans_out is None, repr(ans_out))
    ans_in = WL.act_from_thought(_SAW_T, "", family="woodwork")
    check("family='woodwork' (its own family) still answers the saw thought", ans_in is not None, repr(ans_in))
    ans_none = WL.act_from_thought(_SAW_T, "", family=None)
    check("family=None (the legacy/unscoped caller) still answers, unchanged", ans_none is not None, repr(ans_none))
    ans_unknown = WL.act_from_thought(_SAW_T, "", family="not_a_real_family")
    check("an unrecognised family string is treated the same as None (legacy chain still runs)",
          ans_unknown is not None, repr(ans_unknown))

    _CLIMB_T = "i will climb the old oak"
    check("family='woodwork' declines a climb_tree thought", WL.act_from_thought(_CLIMB_T, "", family="woodwork") is None)
    check("family='climb_tree' answers its own thought", WL.act_from_thought(_CLIMB_T, "", family="climb_tree") is not None)

    _ACORN_T = "i gather acorns from under the oak"
    check("family='climb_tree' declines an acorn thought", WL.act_from_thought(_ACORN_T, "", family="climb_tree") is None)
    check("family='acorn' answers its own thought", WL.act_from_thought(_ACORN_T, "", family="acorn") is not None)

    # negatives: the drifted copies' false fires return NOTHING from the hand end-to-end
    for t in ("i want to cut back on the sugar in my tea this week",
              "the whetstone sits by the step, cold and grey",
              "i load the barrow with stones from the shore",
              "i wish i could gather acorns under the oak again"):
        ans = WL.act_from_thought(t, "")
        check(f"does not answer (drift closed): {t!r}", ans is None, repr(ans))

    print("\n-- part 3: the fallen tree (D-0296/J-1443) -- fell_tree, look, chop, split via rounds")
    # same isolated TMP store as part 2 above (WL._F/_EVENTS/_LEDGER already redirected) -- start this
    # part from a clean, fallen-tree-free state so 'no fallen tree' below is a real negative.
    S.state["location"] = "wood"
    _d3 = WL._load(); _d3.pop("fallen_tree", None)
    _d3["items"]["axe"]["place"] = "wood"; _d3["items"]["axe"]["carried"] = False; _d3["axe_edge"] = 0.9
    WL._save(_d3)

    _no_ft_ans = WL.chop("chop the trunk")
    check("no fallen tree -> chop answers honestly ('nothing down to chop')",
          "nothing down to chop" in (_no_ft_ans or "").lower(), repr(_no_ft_ans))

    _events_before = WL._EVENTS.read_text(encoding="utf-8").splitlines() if WL._EVENTS.exists() else []
    _rec = WL.fell_tree(across_path=True)
    check("fell_tree() returns the fallen-tree record with the builder default kind/name",
          _rec.get("kind") == "macrocarpa" and _rec.get("limbs_left") == 12 and _rec.get("trunk_rounds_left") == 18,
          repr(_rec))
    _events_after = WL._EVENTS.read_text(encoding="utf-8").splitlines() if WL._EVENTS.exists() else []
    check("fell_tree() wrote exactly one new wood_events 'tree_down' row",
          len(_events_after) == len(_events_before) + 1 and '"event": "tree_down"' in _events_after[-1],
          _events_after[-1] if _events_after else "(no rows)")
    check("fell_tree() called again refuses to clobber the tree already down",
          WL.fell_tree(kind="rimu")["kind"] == "macrocarpa")

    _look_ans = WL.look("the fallen tree")
    check("fell_tree then look() renders it", bool(_look_ans) and "macrocarpa" in _look_ans.lower(), repr(_look_ans))
    check("that look() marked the fallen tree seen=True", bool(WL._load().get("fallen_tree", {}).get("seen")))
    _mile = [WL.milestone() for _ in range(4)]
    check("milestone() gives the one-shot 'tree is down' reveal once seen",
          any("tree is down" in (m or "") for m in _mile), repr(_mile))
    check("milestone() does not repeat that reveal a second round",
          not any("tree is down" in (m or "") for m in [WL.milestone() for _ in range(4)]))

    _d3 = WL._load(); _d3["deadfall"] = 0.0; WL._save(_d3)
    _, _gnote = WL.gather_from_stock(3, False)
    check("the picked-clean gather line changes to 'whole tree down' while limbs_left > 0",
          "whole tree" in _gnote and "carry" in _gnote, repr(_gnote))

    _limbs_before = int(WL._load().get("limbs", 0)); _edge_before = float(WL._load()["axe_edge"])
    _ledger_before = len(WL._LEDGER.read_text(encoding="utf-8").splitlines()) if WL._LEDGER.exists() else 0
    _chop_ans = WL.chop("i chop the limbs off the fallen tree")
    _d3 = WL._load()
    check("chop() on limbs: limbs_left decreased", int(_d3["fallen_tree"]["limbs_left"]) < 12, repr(_d3["fallen_tree"]))
    check("chop() on limbs: d['limbs'] increased (feeds the existing saw() stock)",
          int(_d3.get("limbs", 0)) > _limbs_before, f"{_limbs_before} -> {_d3.get('limbs')}")
    check("chop() on limbs: axe_edge blunted by 0.08",
          abs(float(_d3["axe_edge"]) - round(_edge_before - 0.08, 2)) < 1e-6, f"{_edge_before} -> {_d3['axe_edge']}")
    _ledger_after = WL._LEDGER.read_text(encoding="utf-8").splitlines()
    check("chop() on limbs: wrote a real ledger row ({'deed':'chop','what':'limbs','n':..})",
          len(_ledger_after) == _ledger_before + 1 and '"what": "limbs"' in _ledger_after[-1],
          _ledger_after[-1] if _ledger_after else "(none)")
    check("chop()'s own answer names the limbing", "limb" in (_chop_ans or "").lower(), repr(_chop_ans))

    # drive limbs_left to the edge of the transition, then confirm 'limbed' flips and bucking begins
    _d3 = WL._load(); _d3["fallen_tree"]["limbs_left"] = 1; _d3["axe_edge"] = 0.9; WL._save(_d3)
    WL.chop("chop the limbs")
    _d3 = WL._load()
    check("chop(): 'limbed' flips true once limbs_left reaches 0",
          _d3["fallen_tree"]["limbs_left"] <= 0 and _d3["fallen_tree"]["limbed"] is True, repr(_d3["fallen_tree"]))

    _rounds_before = int(_d3.get("rounds", 0)); _trunk_before = int(_d3["fallen_tree"]["trunk_rounds_left"])
    WL.chop("chop the trunk into rounds")
    _d3 = WL._load()
    check("chop() on the bare trunk: trunk_rounds_left decreased by one",
          int(_d3["fallen_tree"]["trunk_rounds_left"]) == _trunk_before - 1, repr(_d3["fallen_tree"]))
    check("chop() on the bare trunk: d['rounds'] increased by one (NOT d['limbs'] again)",
          int(_d3.get("rounds", 0)) == _rounds_before + 1, f"{_rounds_before} -> {_d3.get('rounds')}")

    # rounds feed the EXISTING split() (D-0296's own explicit ask) -- split() is a garden/lean-to deed
    S.state["location"] = "garden"
    _d3 = WL._load(); _d3["items"]["axe"]["carried"] = True; _d3["axe_edge"] = 0.9; WL._save(_d3)
    _rounds_before2 = int(WL._load().get("rounds", 0))
    _split_ans = WL.split("split the rounds on the block")
    _d3 = WL._load()
    check("chop until trunk gone -> rounds feed the EXISTING split()",
          int(_d3.get("rounds", 0)) < _rounds_before2 and bool(_split_ans)
          and "not out here" not in _split_ans and "no dry logs" not in _split_ans,
          f"rounds {_rounds_before2} -> {_d3.get('rounds')}; {_split_ans!r}")
    S.state["location"] = "wood"

    # chop the trunk down to nothing -> an honest exhausted answer, not a crash or a silent no-op
    _d3 = WL._load(); _d3["fallen_tree"]["trunk_rounds_left"] = 1; _d3["axe_edge"] = 0.9; WL._save(_d3)
    WL.chop("chop the trunk")   # takes the last round
    _exhausted_ans = WL.chop("chop the trunk")
    check("chop(): once the trunk is fully bucked, a further chop is an honest 'nothing left' answer",
          "nothing left" in (_exhausted_ans or "").lower() or "stump" in (_exhausted_ans or "").lower(),
          repr(_exhausted_ans))

    # dull-axe refusal (D-0296's own explicit ask: axe_edge < 0.2 glances, per this job's own briefing)
    _d3 = WL._load()
    _d3["fallen_tree"] = {**WL.FALLEN_TREE_DEFAULT, "down_ts": time.time(), "pos": list(WL._FALLEN_TREE_POS),
                           "limbed": False, "seen": True, "across_path": True}
    _d3["axe_edge"] = 0.1; _d3["items"]["axe"]["place"] = "wood"; _d3["items"]["axe"]["carried"] = False
    WL._save(_d3)
    _dull_ans = WL.chop("chop the limbs")
    check("chop(): a dull axe (axe_edge < 0.2) glances and refuses",
          any(w in (_dull_ans or "").lower() for w in ("dull", "glance", "gone")), repr(_dull_ans))
    check("chop(): the dull-axe refusal consumed no limb (no state change)",
          WL._load()["fallen_tree"]["limbs_left"] == WL.FALLEN_TREE_DEFAULT["limbs_left"])

    # wet-night refusal (J-1533/F-2094: closes the one named gap in J-1443's own part-3 coverage --
    # this plan's own §3 note called it out by name). chop() determines night via
    # `from core import sensorium as _s; _s._daylight()` (core/wood_life.py:542-544), and
    # sensorium._daylight() delegates to the ONE clock authority, core.world_clock.daylight()
    # (core/sensorium.py:38 "from core import world_clock as _wc" / :98-99 "return _wc.daylight()").
    # Monkeypatched at that root -- core.world_clock.daylight itself, not sensorium's own thin wrapper
    # -- so the real delegation chop() actually depends on is what's exercised, not a shortcut around
    # it. A fresh, sharp-axe fallen tree is rigged first (axe_edge=0.9, full FALLEN_TREE_DEFAULT limbs)
    # so a refusal that failed to fire would show up unambiguously as a real chop (limbs_left dropping,
    # axe_edge blunting by 0.08) rather than being masked by the dull-axe branch just above, which would
    # otherwise still be sitting at axe_edge=0.1 from that check and could refuse for the WRONG reason.
    # Deterministic for exactly the duration of one chop() call; restored in a finally so a failure here
    # can't leave night/rain forced for anything that follows.
    from core import world_clock as WC
    _real_daylight = WC.daylight
    _d3 = WL._load()
    _d3["fallen_tree"] = {**WL.FALLEN_TREE_DEFAULT, "down_ts": time.time(), "pos": list(WL._FALLEN_TREE_POS),
                           "limbed": False, "seen": True, "across_path": True}
    _d3["axe_edge"] = 0.9; _d3["items"]["axe"]["place"] = "wood"; _d3["items"]["axe"]["carried"] = False
    WL._save(_d3)
    _limbs_before_wn = int(WL._load()["fallen_tree"]["limbs_left"])
    _weather_before = S.state.get("weather")
    S.state["weather"] = "rain"
    WC.daylight = lambda *a, **k: "night"
    try:
        _wetnight_ans = WL.chop("chop the limbs")
    finally:
        WC.daylight = _real_daylight
        S.state["weather"] = _weather_before
    check("chop(): a wet night (world_clock.daylight()=='night' + weather='rain') refuses ('Not tonight')",
          "not tonight" in (_wetnight_ans or "").lower(), repr(_wetnight_ans))
    check("chop(): the wet-night refusal consumed no limb (no state change)",
          WL._load()["fallen_tree"]["limbs_left"] == _limbs_before_wn, repr(WL._load()["fallen_tree"]))
    check("chop(): the wet-night refusal did not blunt the axe (no state change)",
          float(WL._load()["axe_edge"]) == 0.9, repr(WL._load()["axe_edge"]))
    check("world_clock.daylight restored to the real function after the wet-night check",
          WC.daylight is _real_daylight)
except Exception as exc:
    import traceback; traceback.print_exc()
    check("part 2 ran", False, repr(exc))
finally:
    print(f"   isolated dir {TMP}; live wood_life.json: {_live_status(_LIVE_BEFORE, _stat_or_none(_LIVE))}")

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILED'}")
sys.exit(1 if FAILS else 0)
