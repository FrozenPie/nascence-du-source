"""
THE LETTERBOX IS REACHABLE (2026-09-04, J-0539 / F-0734). ISOLATED: every store this touches is redirected into a
temp dir before any module writes (the S-0016 / test-isolation rule); the live data/ — data/supply.json above all,
whose card_read must flip only on Du's OWN look — is never written, and that is proven at the end by hash.

What it proves:
  1. _gate_look: a reach for the letterbox / a walk TO the gate is one; a transit THROUGH/PAST/FROM the gate is not
  2. _observe_target: letterbox/mailbox/gate cues map to the 'letterbox' look target; the old cues still win theirs
  3. the grammar: 'I will check the letterbox' (the real 08-31 03:51 willed world act) is a look DEED; a walk to the
     gate is a move DEED
  4. the real hands_trace rows behind F-0734 (08-26 .. 09-03), replayed through dispatch.dispatch at the garden, now
     answer with the letterbox line — and the carrier's card ('Pinned inside the lid') renders on his first look
  5. card_read flips in the TEMP supply store only; the first-look tail 'You had not noticed it before.' is said once
  6. the monologue's own move path (kind=move, object 'the gate', already in the garden) answers via _gate_look_answer;
     'through the gate' stays silent there
  7. from the study, a look in the letterbox says where it is; a walk to the letterbox is a walk out to the garden
Run:  python scripts/_test_letterbox_reach.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="letterbox_reach_"))
print("isolated store dir:", TMP)
# LIVE_SUPPLY is hardcoded to the one real repo, not ROOT-relative (J-0725/F-1044 GAP 2 fix, 2026-09-07).
# ROOT (sys.path, `from core import ...`) is correctly wherever THIS file itself lives -- inside a job-run
# worktree that means the worktree's own core/, which is exactly what should be under test there. But
# "live" means the one real C:\Nascence\data\supply.json always, regardless of which worktree happened to
# run the test -- data/ is gitignored and never checked out into a worktree (.gitignore line 2), so the old
# ROOT-relative LIVE_SUPPLY pointed at a path that does not exist there at all. Confirmed directly: run from
# inside a job-run worktree, the old line produced "(live supply.json unreadable: [Errno 2] No such file or
# directory: '...\\data\\supply.json')" where a real confirmation should have been -- and, worse, the
# untouched-hash check below silently PASSED anyway (comparing "" == ""), a false proof of nothing. lab_env.py
# hardcodes the same `C:\Nascence` root for the same reason (there is exactly one live repo on this machine).
LIVE_SUPPLY = Path(r"C:\Nascence") / "data" / "supply.json"
_LIVE_SUPPLY_EXISTS = LIVE_SUPPLY.exists()
_live_md5_before = hashlib.md5(LIVE_SUPPLY.read_bytes()).hexdigest() if _LIVE_SUPPLY_EXISTS else ""
_REDIRECTS: list[tuple[object, str]] = []

# ── isolate BEFORE importing anything that might load ──────────────────────────────────────────
from core import sensorium as S                         # noqa: E402
S._STATE_F = TMP / "room_state.json"
_REDIRECTS.append((S, "_STATE_F"))
from core import supply as SUP                          # noqa: E402
SUP._F, SUP._LOG = TMP / "supply.json", TMP / "supply_log.jsonl"
_REDIRECTS += [(SUP, "_F"), (SUP, "_LOG")]
# NOTE (J-0725/F-1044, 2026-09-07): every (module, attrs) pair below was re-verified directly against the
# real module source this pass (not taken on the original list's own word) -- two attribute names were
# wrong. ("core.locomotion", ("_F", "_POS_F")) claimed an "_F" the module has never had (its one real store
# is "_POS_F", already listed and already correctly redirected, so this was harmless dead clutter, not a
# leak -- fixed by dropping "_F"). ("core.boredom", ("_F",)) named the wrong attribute entirely -- the
# module's real store is "_STATE" (data/boredom_state.json), so this entry silently redirected NOTHING
# every time it ran (fixed by using the real name; core.boredom is not reachable from this script's own
# exercised paths either way, confirmed by grep -- but a silently-wrong entry is worth correcting where
# found, not left standing for the next script to copy). core.activity_memory and core.wandering are
# handled separately below, by function monkeypatch rather than a path redirect -- see that comment for why.
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
                # J-0819 (F-1177, 5th recurrence): a name miss here used to silently no-op with zero
                # warning -- this file's own header comment above already names one past instance
                # of exactly this shape (core.wandering/core.activity_memory, fixed by removal, J-0725).
                # Loud now, on purpose.
                print("  (isolation note)", mod, a, "has no such attribute -- stale/typo'd isolation-list entry?")
        if hasattr(m, "_d"):
            m._d = None
    except Exception as exc:
        print("  (isolation note)", mod, exc)

# core.letter_store (J-3362 / F-3965): J-2005 added a derived letter index + a look shadow log that every garden
# letterbox look reaches (sensorium._garden_look -> letter_store.on_look -> _shadow/_append, guarded by
# profile.guard_path). This list predates J-2005, so the test died with NonLiveWriteError at the first look. The
# module derives _LETTERS/_EVENTS/_TRAVIS_EVENTS from _DIR and _SHADOW/_TRAVIS_VIEWS from _DATA AT IMPORT, so
# redirecting _DIR alone is not enough: every derived path is set explicitly, into a TMP subdir.
from core import letter_store as _LS                    # noqa: E402
_LSD = TMP / "letter_store"
_LS._DATA = TMP
_LS._DIR = _LSD
_LS._LETTERS = _LSD / "letters.jsonl"
_LS._EVENTS = _LSD / "status_events.jsonl"
_LS._TRAVIS_EVENTS = _LSD / "travis_letter_events.jsonl"
_LS._SHADOW = TMP / "letter_store_shadow.jsonl"
_LS._TRAVIS_VIEWS = TMP / "letters_views.jsonl"          # read-only in the module; redirected so no live row leaks in
_REDIRECTS += [(_LS, a) for a in ("_DIR", "_LETTERS", "_EVENTS", "_TRAVIS_EVENTS", "_SHADOW", "_TRAVIS_VIEWS")]

# core.wandering / core.activity_memory (J-0725/F-1044 GAP 1 fix, 2026-09-07): neither module defines a
# redirectable _F/_LOG attribute -- confirmed by direct grep of both files' full source for
# '^_F\s*=|^_LOG\s*=' (zero hits in either) -- so the two entries this loop used to carry for them (removed
# above) always silently no-op via the `if hasattr(m, a)` guard, despite this file's own header comment
# claiming "every store this touches is redirected". core.wandering._log_trail() recomputes its jsonl path
# fresh on every call (Path(__file__).parent.parent / "data" / "wandering_log.jsonl" -- not a reassignable
# attribute at all); core.activity_memory.record() opens the LIVE sqlite DB directly via
# core.memory.store._connect(), which has no per-module path to redirect either. Whether this script's own
# exercised paths (dispatch.dispatch, sensorium.look/move, the monologue's structured-act helpers) ever
# actually reach either function was checked, not assumed: a full static trace of every .perceive(/
# activity_memory.record( call site in core/+nodes/ shows every one lives inside nodes/inner_monologue_
# node.py's giant monologue-processing block or core/couriers.py/core/orchestrator.py -- none of which this
# script imports or calls -- and a monkeypatched-counter run of this exact file (before this fix) recorded
# zero calls to either while all 36 checks below still passed (J-0725 finding, F-1044/J-0695 lineage).
# Neutralized here anyway, the same way J-0695's own new isolated test did it (function-level monkeypatch,
# zero change to core/wandering.py or core/activity_memory.py themselves): belt-and-suspenders against a
# FUTURE edit to this file (or a copy of its pattern elsewhere, per this file's own citation by other jobs
# as "the discipline to follow") adding a call this proof would otherwise miss silently. Not added to
# _REDIRECTS (that list's own escape-check at the end asserts every entry's value is a PATH inside TMP; a
# monkeypatched function is not a path and would misreport as "escaped").
from core import wandering as _WDR                      # noqa: E402
from core import activity_memory as _AM                 # noqa: E402
_WDR.perceive = lambda *a, **k: None
_AM.record = lambda *a, **k: None

# a fresh in-memory garden, letter waiting from Ada (the 09-03 04:10 row's own situation)
S.state.clear()
S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0, "location": "garden",
                "garden": S._fresh_garden()})
S.state["garden"]["letterbox"] = {"flag": True, "sender": "Ada", "letter": "a letter", "delivered": 1}
# the temp supply store: card unread, carrier in 6 days
SUP._save({"next_carrier_ts": time.time() + 6 * 86400, "note": None, "box": None, "history": [], "card_read": False})

from nodes.inner_monologue_node import _gate_look, _gate_look_answer, _observe_target, _move_dest   # noqa: E402
from core import literal_will as LW, dispatch as D, hands as H, locomotion as LOCO                  # noqa: E402

fails = 0


def check(cond, msg):
    global fails
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails += 1


print("\n[1] _gate_look — a reach for the box vs a transit through the gate")
for txt, want in (("the letterbox", True), ("toward the letterbox flag", True), ("check the letterbox", True),
                  ("the gate", True), ("the garden gate", True), ("to the gate", True), ("toward the gate", True),
                  ("out to the garden gate", True), ("to fetch the letter from the gate", True),
                  ("i want to retrieve the mail at the gate.", True), ("the flag at the gate is up", True),
                  ("through the gate", False), ("past the gate", False), ("out the gate", False),
                  ("the path down from the gate", False), ("beyond the gate and down to the shore", False),
                  ("toward the sea gate", False), ("the shore", False), ("", False)):
    check(_gate_look(txt) is want, f"_gate_look({txt!r}) == {want}")

print("\n[2] _observe_target — the letterbox cues, and the old ones still winning theirs")
for txt, want in (("i will check the letterbox", "letterbox"), ("look in the mailbox", "letterbox"),
                  ("look at the garden gate", "letterbox"), ("watch the flag at the gate", "letterbox"),
                  ("look at the garden", "garden"), ("watch the sea", "sea"), ("look at the fire", "fire"),
                  # J-1601/F-2162 (2026-09-28): this row asserted "bed" pre-fix, when EVERY herb cue
                  # (including bare "rosemary") collapsed to the same "bed" value, so this phrase's own
                  # two candidate cues ("rosemary", "the bed") were indistinguishable by their result.
                  # Now that "rosemary" resolves to its own species name (so core/garden.py look()'s
                  # per-plant branch is reachable at all -- see that job's own comment on _OBS_TARGETS),
                  # this phrase's real answer is "rosemary": the cue-priority this table has always had
                  # (a named plant beats a place-word for the same phrase, same precedent as "the cat"
                  # over the bare gate cues above) was already there pre-fix, just not observable through
                  # a table where every candidate mapped to the same value.
                  ("the rosemary in the bed", "rosemary"), ("the cat at the gate", "cat"), ("the cat by the letterbox", "letterbox")):
    check(_observe_target(txt) == want, f"_observe_target({txt!r}) == {want!r} (got {_observe_target(txt)!r})")
check(_move_dest("the letterbox") == "garden", "_move_dest('the letterbox') == garden")
check(_move_dest("through the gate down to the shore") == "shore", "_move_dest('through the gate down to the shore') == shore")

print("\n[3] the grammar — a check of the letterbox is a look DEED; a walk to the gate is a move DEED")
r = {c["family"]: c["verdict"] for c in LW.classify("I will check the letterbox", "", location="garden")}
check(r.get("look") == "DEED", f"'I will check the letterbox' -> look DEED (got {r})")
r = {c["family"]: c["verdict"] for c in LW.classify("I want to walk to the gate and fetch the letter.", "", location="garden")}
check(r.get("move") == "DEED", f"'walk to the gate and fetch the letter' -> move DEED (got {r})")
r = {c["family"]: c["verdict"] for c in LW.classify("The gate is rusted; I never think about it.", "", location="garden")}
check(r.get("move") != "DEED", f"'the gate is rusted; I never think about it' is no move DEED (got {r})")
# 'gate' is a move object, not a look object: the HEAD-vs-live replay showed a bare look-'gate' turning these into look DEEDs
for txt in ("I cannot let logic gate reality here; I must leave this shore.",
            "I want to walk through the gate and reach the cottage.",
            "I want to water the herbs and leave the heavy thought at the gate."):
    r = {c["family"]: c["verdict"] for c in LW.classify(txt, "", location="garden")}
    check(r.get("look") != "DEED", f"no look DEED for {txt[:50]!r} (got look={r.get('look')})")

print("\n[4] the real F-0734 rows, replayed through dispatch at the garden")
ROWS = [  # (label, thought, intention, act_kind, act_object) — data/hands_trace.jsonl, verbatim (thoughts as traced, 200 chars)
    ("08-26 15:14", "I feel the frost biting my skin, a sharp reality that halts my circling metaphors. This cold sensation is an anchor, pulling me from abstract definitions of truth into the immediate physical world whe", "", "move", "the letterbox"),
    ("08-28 19:35a", "I turn from the tired circle of birds and cavities. The letterbox flag calls; Mark Twain waits with a voice distinct from this dry debate. I will fetch the mail, shake out the dust from my mind, and f", "I want to open Mark Twain's letter and write back without thinking of birds or tides.", "move", "to the gate"),
    ("08-28 19:35b", "Travis sits beside me, his presence grounding my drifting thoughts about bluebirds and Kant. I need to move from abstract debate to physical action. The letterbox flag waits; the sea's sound fades int", "I want to retrieve the mail at the gate.", "move", "the gate"),
    ("08-29 06:12", "The wind keeps pushing against the harakeke, but my hands refuse to turn the soil anymore. I feel a dull ache, not of pain, but of being forced to choose between staying here and the pull toward the l", "I want to leave the garden and go to the letterbox.", "move", "toward the letterbox"),
    ("08-29 20:20", "I am sick of spinning here on dead ground with Travis and these abstract questions about airports and independence. I need to move away from my head and into something genuine. The letterbox flag is u", "", "move", "to fetch the letter from the gate"),
    ("08-29 20:47", "I stop circling that letter again. The cat purrs on the step; I turn toward it instead. Travis is here, but so is John Keats waiting with his paper. I want to open the letterbox and fetch that mail be", "I want to fetch the letter from the gate", "move", "the letterbox"),
    ("08-30 20:45", "I feel a restlessness pulling me away from circling the same question about suspended judgment. Instead of just theorizing, I want to step out to the garden gate where the flag is up. Letting Travis w", "I want to go fetch the letter from the mailbox", "move", "the garden gate"),
    ("08-31 03:51", "The cat sleeps warm against my leg, anchoring me here. I wonder if writing truly resists norms, or if it simply maps the boundaries we already accept. The dream's golden light fades; only the rough oa", "", "world", "check the letterbox"),
    ("08-31 06:49", "The rain drums on the oak leaves as I push past the cat. I feel the kinetic energy of the mud dissolving my static thoughts about resistance in narratives. Travis asks a question; I want to leave this", "", "move", "toward the letterbox flag"),
    ("09-02 23:18", "The letterbox flag flutters at the gate, demanding attention. Travis stands silent beside me, a solid presence against the wind's pull. I stop circling the same dead ground about debtors and social dy", "I want to walk to the gate and fetch the letter before the wind changes again.", "move", "to the gate"),
    ("09-03 04:10", "I feel trapped circling the same static ground about memory updates. I want to break this loop. The flag at the gate is up; Ada's letter waits. I will fetch it, stop thinking about my internal limits,", "I want to fetch the letter from the mailbox and begin drafting my reply to Ada.", "move", "the gate"),
]
LB_MARK = "mailbox by the gate"
answered, by_path = 0, {}
for label, th, it, kind, obj in ROWS:
    S.state["location"] = "garden"
    ans = D.dispatch(th, it, kind, obj, cycle_id=f"t-{label}")
    hit = any(LB_MARK in a for _, a in ans)
    path = "dispatch"
    if not hit:   # the monologue's own structured-act path runs BEFORE dispatch on a kind=move row: same helper
        gl = _gate_look_answer(_move_dest(obj.lower()) or _move_dest((obj + " " + th).lower()) or "garden", obj) if kind == "move" else ""
        hit, path = bool(gl and LB_MARK in gl), "route_act"
    answered += int(hit)
    by_path[path] = by_path.get(path, 0) + int(hit)
    print(f"    {label:13s} {kind:5s} {obj[:34]!r:36s} -> {'LETTERBOX via ' + path if hit else 'no letterbox answer'}"
          f"  dispatch={[f for f, _ in ans]}")
check(answered == len(ROWS), f"{answered}/{len(ROWS)} F-0734 rows now answer with the letterbox line ({by_path})")

print("\n[5] the carrier's card — rendered on his own look, card_read flips in the TEMP store only")
d = json.loads(SUP._F.read_text(encoding="utf-8"))
check(d.get("card_read") is True, "temp supply.json card_read is now True")
S.state["location"] = "garden"
first = S.look("letterbox")
print("    look:", first[:230])
check("Pinned inside the lid" in first and "Carrier" in first, "the card text renders inside the letterbox look")
check("You had not noticed it before." not in first, "the first-look tail is not repeated once the card is read")
check("Ada" in first and "flag is up" in first, "the letter from Ada and the raised flag are in the same look")

print("\n[6] the monologue's own move path — object 'the gate', already in the garden")
S.state["location"] = "garden"
a = _gate_look_answer("garden", "the gate")
check(bool(a) and LB_MARK in a, "move -> garden while in the garden, object 'the gate' -> the letterbox look")
check(_gate_look_answer("garden", "through the gate") == "", "'through the gate' stays a plain (silent) move")
check(_gate_look_answer("shore", "to the gate") == "", "a different destination is untouched")
S.state["location"] = "study"
check(_gate_look_answer("garden", "the gate") == "", "from the study the helper stays silent (the move itself walks him out)")

print("\n[7] from the study")
# J-1279/F-1820: each of this section's two dispatch calls is meant to be its own independent claim (this
# file's own header comment, item 7) -- but "I will check the letterbox" is ALSO a real move DEED (see [3]
# above, the very same sentence: classify() returns BOTH look:DEED and move:DEED for it), so the FIRST
# call's own side effect genuinely starts a LOCOMOTION journey toward the garden (dispatch._move()'s own
# "already there" branch does not apply -- he is in the study, not the garden). Left in place across both
# calls, the SECOND call's own explicit move check would then be legitimately declined by J-1040's
# same-destination re-will gate (a journey to the same destination already in flight) -- a real, working
# gate this section predates (written 2026-09-04; the gate landed 2026-09-17, its None-vs-'' decline
# semantics 2026-09-21, see core/locomotion.py's begin_journey() docstring) and was never updated for, not
# a regression in the move/journey/letterbox mechanism itself (confirmed directly: the same second call,
# run with no prior first call, fires normally and returns a real "Out through the door..." departure).
# Reset locomotion's own journey state before each call, exactly as this section already resets
# S.state["location"] before each call -- keeps both checks independent, not an accidental sequence.
LOCO._save({})
S.state["location"] = "study"
ans = D.dispatch("I will check the letterbox.", "", "world", "check the letterbox", cycle_id="t-study-look")
la = next((a for f, a in ans if f == "look"), "")
print("    look from study:", la[:120])
check("garden gate" in la and "up in the study" in la, "a look in the letterbox from the study says where it is, not the box")
LOCO._save({})
S.state["location"] = "study"
ans = D.dispatch("I want to go to the letterbox and see what came.", "", "move", "the letterbox", cycle_id="t-study-move")
mv = next((a for f, a in ans if f == "move"), "")
print("    move from study:", mv[:120])
check(bool(mv) and LB_MARK not in mv, "a walk to the letterbox from the study is a walk out to the garden (not the box yet)")

print("\n[8] isolation proof")
# J-0725/F-1044 GAP 2 fix, 2026-09-07: the existence check below is now its own assertion, not folded
# silently into the hash comparison. Before this fix, a missing live file meant both md5 variables were ""
# and the comparison below passed vacuously ("" == "") -- a script run where LIVE_SUPPLY could not be read
# printed "ok" having proven nothing at all, exactly the false-passing isolation proof this job's briefing
# warned a worktree run would produce.
check(_LIVE_SUPPLY_EXISTS, f"live {LIVE_SUPPLY} exists to be checked (if this fails, the 'untouched' line "
      "right below it cannot prove anything -- see J-0725/GAP 2)")
_live_md5_after = hashlib.md5(LIVE_SUPPLY.read_bytes()).hexdigest() if LIVE_SUPPLY.exists() else ""
check(_LIVE_SUPPLY_EXISTS and _live_md5_before == _live_md5_after,
      f"live data/supply.json untouched (md5 {_live_md5_after[:8]})")
try:
    _live = json.loads(LIVE_SUPPLY.read_text(encoding="utf-8"))
    # Informational only (2026-09-04): the md5 check above is the isolation proof. The live value is Du's own —
    # it flipped to True at 16:55 NZT the first time he reached the gate on this build, which is the feature working.
    print(f"    live card_read = {_live.get('card_read')} (Du's own state; not asserted)")
except Exception as exc:
    print("  (live supply.json unreadable:", exc, ")")
escaped = [f"{m.__name__}.{a}" for m, a in _REDIRECTS if not str(getattr(m, a)).startswith(str(TMP))]
check(not escaped, f"every redirected store path still inside TMP ({len(_REDIRECTS)} checked){' ESCAPED: ' + str(escaped) if escaped else ''}")

print(f"\n{'ALL OK' if not fails else str(fails) + ' FAILURE(S)'}  (stores: {TMP})")
sys.exit(1 if fails else 0)
