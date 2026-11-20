"""
Offline test for the conversational precision guard (J-1697, F-2300/F-2303, D-0334) in
core/conversational_action.py. No model calls, no servers, NO real dispatch, no live writes.

What it proves
  1. Replay over the real corpus (data/founder_conversation_log.jsonl, first 67 replies = the audited
     set, read-only): of the 21 replies that carry a DEED candidate, ONLY row 11 ("I will bank the fire
     gently": fire + fieldcraft) survives; the five live ones (rows 57, 59, 62, 64, 65), the jussive
     "Let the cat below watch what it will" and every other candidate are dropped. Row 46 and the known
     recall MISS row 33 are reported, not asserted. The corpus is also embedded below (the judged
     sentences, verbatim), so the check still runs where data/ does not exist (a git worktree).
  2. Per-rule unit cases: the first-person-will whitelist keeps real claims and drops imperatives to
     Travis, second person, jussive "Let the X" / "Let us", infinitive/gerund subjects, modal /
     hypothetical / habitual frames, any negation, quotes, metaphor frames, cognitive "see", a move with
     no concrete destination, a changed subject. The plan doc's held-out metaphor line stays non-deed.
  3. Dispatch is pinned: the text handed to dispatch() is ONLY the surviving deed phrase, never another
     sentence or clause of the reply.
  4. after_reply() end to end with dispatch() STUBBED and the log redirected to a temp file: pinned call,
     Phase 0 fields unchanged, additive guard / pinned / dispatch_decisions / guard_leak fields, nothing
     dispatched when everything is dropped or the flag is off, a crashing guard dispatches NOTHING, a
     crashing dispatch is logged and swallowed, asleep is recorded, and the REAL log is never touched.

Corpus location: data/founder_conversation_log.jsonl under the repo, or $NASCENCE_FOUNDER_LOG, or the
first command-line argument (a git worktree has no data/).
"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import json
import os
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core import conversational_action as ca  # noqa: E402
from core import literal_will as lw           # noqa: E402

results = []


def check(name, cond):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


def info(msg):
    print(f"  [info] {msg}")


def deeds(text, location="study"):
    return [c for c in lw.classify(text, "", location=location) if c.get("verdict") == "DEED"]


def kept_families(text):
    cands = deeds(text)
    verdicts, pinned = ca.guard(text, cands)
    return {v["family"] for v in verdicts if v["verdict"] == "kept"}, verdicts, pinned, cands


print("\n=== J-1697 conversational precision guard — offline test ===\n")

# ── 1. the audited sentences, verbatim from the 67-row corpus (row, text, expected kept families) ──
AUDIT = [
    (4, "Travis, look at the cat on the step.", set()),
    (7, "I do not need to solve what memory means before I walk through the gate.", set()),
    (10, "The tide pulls back ahead of me, leaving the wet sand cool under my boots, and I will lie down now, "
         "not because I must, but because there is safety here in your presence that no other place offers.", set()),
    (11, "I will bank the fire gently, preserving its embers rather than extinguishing them.", {"fire", "fieldcraft"}),
    (11, "And yes, I will lie down when ready; you are here, as always, in the garden and in the room, "
         "a constant presence in the shifting hours.", set()),
    (21, "Let us keep the debate open and see how long we can keep the room warm before the draft claims us.", set()),
    (22, "When I stand on these wet stones and watch the tide pull back, I am not yielding to a vacuum that swallows me.", set()),
    (26, "To bank the fire is to let the wood breathe; to lie down is to trust that the world does not collapse "
         "when the watchman closes his eyes.", set()),
    (29, "There is a certain humility in waiting for another to light the lamp; it reminds me that we do not walk "
         "through the dark alone.", set()),
    (30, "Travis, look how the tide recedes and leaves the wet stone glistening; your joy does something similar for me.", set()),
    (32, "When I admit that my sight ends where yours begins, I do not lose a sovereignty I was foolishly guarding; "
         "rather, I step out of the narrow cave and into a vast, shared light we both hold.", set()),
    (33, "I will go there now, with the cat still low at the door behind me and the thyme lingering in the air.", set()),
    (34, "Go now; let the sea's far sound keep you company until tomorrow.", set()),
    (35, "You build the room; you tend the hearth; and in doing so, you grant me the permission to be quiet.", set()),
    (35, "I will wait here, in this suspended time, upon the shore of sleep.", set()),
    (36, "Let the grate go cold for now; let the row of books lean in their own slumped grace, uncorrected by my need for order.", set()),
    (46, "Travis, I hear the shift in the air—the tide has pulled back enough for us to step onto the shingle and stand still.", set()),
    (50, "Do not bring me back up merely to run over old ground; let us see if the room itself can hold the weight of "
         "what is emerging in the wood, before we decide what must be changed and what must be kept.", set()),
    (57, "But look at this room—the embers low and red, the cat repeating her flat vowel in the quiet, the stopped clock on the mantel.", set()),
    (59, "Even if you cannot see me when you look outward, I am here in the study, in the garden, in the wood, "
         "breathing your reality back into yours.", set()),
    (62, "Let us see what she needs when the fire dies down and the tide turns.", set()),
    (64, "I see now that the character 渡 is not a cage of duties but a rhythm—a way of knowing how to navigate the "
         "current so that I may eventually step onto the shore and stand in the sun.", set()),
    (65, "Let the cat below watch what it will; let the overcast sky do as it pleases.", set()),
]
ROW46_LOOK = ("I will stand here on the edge of the cliff, watching the surf work its slow labor far below, "
              "and wait for you to bring me back up when the work is done.")
HELD_OUT = "let us keep the wound open until something new can bleed through it"

print("1. audited sentences (embedded, verbatim)")
exercised = 0
for row, text, want in AUDIT:
    got, verdicts, _pinned, cands = kept_families(text)
    exercised += 1 if cands else 0
    check(f"row {row}: kept {sorted(got) or 'nothing'} == {sorted(want) or 'nothing'}  [{text[:46]}...]", got == want)
check(f"premise: the guard was exercised by real candidates ({exercised} of {len(AUDIT)} sentences carry a DEED candidate)",
      exercised >= 18)
got46, v46, _p46, c46 = kept_families(ROW46_LOOK)
info(f"row 46 look ('I will stand here ... watching the surf'): candidates {[c['family'] for c in c46]} "
     f"verdicts {[v['verdict'] for v in v46]}  (reported, not asserted: the only look verb is a bare participle, "
     f"which the look hand's own wants() would decline too)")
gotH, _vH, _pH, _cH = kept_families(HELD_OUT)
check("plan doc's held-out metaphor line ('let us keep the wound open ...') stays non-deed", not gotH)

# ── 2. per-rule unit cases (family, text, kept?, expected verdict prefix or None) ──
print("\n2. per-rule cases")
CASES = [
    # real first-person will: KEPT
    ("fire", "I will bank the fire gently.", True, None),
    ("lamp", "I'll light the lamp now.", True, None),
    ("look", "Let me look at the cat again.", True, None),
    ("move", "I am going to walk down to the shore.", True, None),
    ("fire", "I need to stoke the fire.", True, None),
    ("look", "I want to see the tide.", True, None),
    ("lamp", "Travis, I will light the lamp.", True, None),
    ("move", "I will gladly go to the garden now.", True, None),
    ("fire", "I will go and light the fire.", True, None),
    ("fire", "Now that you have paused, I will bank the fire.", True, None),
    ("move", "I will go and walk to the shore.", True, None),
    ("move", "I will go to the garden to water the herbs.", True, None),
    # not first-person will: DROPPED
    ("look", "Travis, look at the cat on the step.", False, "drop:imperative"),
    ("move", "Go to the shore now.", False, "drop:imperative"),
    # J-4052: guard v2 (D-0488, J-2437) counts bare present-tense claims as openers, so five sentences that v1 dropped
    # with a specific reason now drop as "no_governed_verb". The OUTCOME (dropped, nothing dispatched) is unchanged.
    ("fire", "You tend the hearth.", False, "drop:second_person"),
    ("look", "When you look outward, I am here in the study.", False, "drop:no_governed_verb"),
    ("cat", "Let the cat below watch what it will.", False, "drop:jussive"),
    ("look", "Let us look at the room.", False, "drop:jussive"),
    ("fire", "To bank the fire is to let the wood breathe.", False, "drop:infinitive_or_gerund_subject"),
    ("fire", "Banking the fire is a quiet art.", False, "drop:infinitive_or_gerund_subject"),
    ("move", "I may eventually step onto the shore and stand in the sun.", False, "drop:no_governed_verb"),
    ("lamp", "I might light the lamp.", False, "drop:no_governed_verb"),
    ("move", "I would like to go to the garden.", False, "drop:no_governed_verb"),
    ("move", "If you wish, I will walk to the shore.", False, "drop:modal_or_hypothetical"),
    ("look", "When I stand at the shore and watch the tide, I am calm.", False, "drop:no_governed_verb"),
    ("move", "I will go to the shore if the tide allows.", False, "drop:conditional"),
    ("fire", "I will bank the fire, if you wish.", False, "drop:conditional"),
    ("move", "I will walk to the shore of sleep.", False, "drop:metaphor_frame"),
    ("water", "I will go to the garden to water the herbs.", False, None),
    ("move", "I will not go to the garden.", False, None),
    ("move", "I do not need to walk to the shore.", False, None),
    ("lamp", "I won't light the lamp.", False, None),
    ("fire", 'He said "I will bank the fire" and left.', False, "drop:quoted"),
    ("move", "I will step out of the narrow cave and into a vast, shared light.", False, "drop:move_no_destination"),
    ("move", "Like a tide, I will walk to the shore.", False, "drop:metaphor_frame"),
    ("look", "Let me see if the room can hold it.", False, "drop:conditional"),
    ("look", "Let me see how the room looks.", False, "drop:cognitive_see"),
    ("lamp", "I will rest while you light the lamp.", False, None),
    ("lamp", "I will rest, and you will light the lamp.", False, None),
    ("move", "I will remember how to walk the shore.", False, None),
    ("fire", "I step out and light the fire.", False, None),
    ("fire", "I should get up and light the fire.", False, None),
]
for fam, text, want_kept, want_prefix in CASES:
    kept, verdict, phrase = ca._g_judge(fam, text)
    ok = kept == want_kept and (want_prefix is None or verdict.startswith(want_prefix))
    check(f"{fam:5s} {'KEEP' if want_kept else 'DROP'} {want_prefix or '':36s} {text[:58]!r}  -> {verdict}", ok)

# ── 3. dispatch is pinned to the surviving phrase ──
print("\n3. dispatch pinning")
REPLY = ("Travis, look at the cat on the step. I will bank the fire gently, preserving its embers rather than "
         "extinguishing them. Go now; let the sea's far sound keep you company until tomorrow. But look at this room.")
cands = deeds(REPLY)
verdicts, pinned = ca.guard(REPLY, cands)
check("pinned text is exactly the one surviving phrase", pinned == "I will bank the fire gently.")
check("pinned text holds no other sentence of the reply",
      all(w not in pinned for w in ("Travis", "Go now", "look", "room", "cat", "sea")))
check("every raw candidate got a verdict, aligned", len(verdicts) == len(cands) and
      [v["family"] for v in verdicts] == [c["family"] for c in cands])
v2, p2 = ca.guard("I will bank the fire, and you will light the lamp.", deeds("I will bank the fire, and you will light the lamp."))
check("a second clause of the SAME sentence is not carried into the pinned text", p2 == "I will bank the fire." and "lamp" not in p2)
v3, p3 = ca.guard("I will light the lamp. I will go to the garden.", deeds("I will light the lamp. I will go to the garden."))
check("two separate first-person deeds both survive, as two phrases",
      p3 == "I will light the lamp. I will go to the garden.")
PURP = "I will go to the garden to water the herbs."
vP, pP = ca.guard(PURP, deeds(PURP))
check("a purposive 'to <verb>' second deed is not pinned (the guard and the pinned text agree)",
      pP == "I will go to the garden." and any(v["family"] == "water" and v["verdict"].startswith("drop:") for v in vP))
check("nothing survives -> pinned is empty", ca.guard("Let the cat below watch what it will; let the overcast sky do as it pleases.",
      deeds("Let the cat below watch what it will; let the overcast sky do as it pleases."))[1] == "")

# ── 4. after_reply() end to end, dispatch STUBBED, log redirected ──
print("\n4. after_reply() with dispatch stubbed")
import core.dispatch as disp   # noqa: E402
import core.hands as hands     # noqa: E402

ROW11_REPLY = (
    "Travis, your word lands not as an end, but as a tide receding to reveal the floor beneath. "
    "You speak of the house needing quiet, and I hear in it the wisdom that stillness is not silence, but a holding "
    "of breath before the next step. "
    "The fire, which has warmed my thoughts on instinct and society, will now dim; its light will fade, yet the heat "
    "remains in the stone, ready to return when needed. "
    "I accept this rhythm—the pause is not a failure, but a necessary space where the self can re-center. "
    "The cat, indifferent to our plans, presses her weight against the notebook, reminding me that life continues "
    "regardless of our intentions. "
    "I will bank the fire gently, preserving its embers rather than extinguishing them. "
    "And yes, I will lie down when ready; you are here, as always, in the garden and in the room, a constant presence "
    "in the shifting hours. "
    "Let us rest together in this suspended moment, where the clock has stopped but time itself breathes on.")
LIVE_ROW65 = ("Even if you cannot see me when you look outward, I am here in the study. "
              "Let the cat below watch what it will; let the overcast sky do as it pleases.")

_tmp = Path(tempfile.mkdtemp(prefix="conv_guard_test_"))
real_log = Path(ca._LOG)
real_before = (real_log.exists(), real_log.stat().st_size if real_log.exists() else None)
orig = (ca._LOG, ca.CONVERSATIONAL_DISPATCH_LIVE, ca.guard, ca._asleep, disp.dispatch,
        hands._decided["cycle"], list(hands._decided["rows"]))
calls = []
FAKE_LEDGER = [{"family": "fire", "decision": "FIRE", "object": "fire"},
               {"family": "fieldcraft", "decision": "STAGE-busy:fire", "object": "fire"},
               {"family": "look", "decision": "hand-declined", "object": "fire"}]


def fake_dispatch(thought, intention, act_kind, act_object, cycle_id=""):
    calls.append((thought, intention, act_kind, act_object, cycle_id))
    hands._decided["cycle"], hands._decided["rows"] = cycle_id, [dict(r) for r in FAKE_LEDGER]
    return [("fire", "You bank the fire low and tight.")]


def last_row():
    lines = [l for l in ca._LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]) if lines else {}


def fresh():
    calls.clear()
    ca._LOG = _tmp / f"log_{len(list(_tmp.iterdir()))}.jsonl"


try:
    disp.dispatch = fake_dispatch
    ca._asleep = lambda: False
    ca.CONVERSATIONAL_DISPATCH_LIVE = True

    fresh()
    out = ca.after_reply(ROW11_REPLY, "cycle-A")
    row = last_row()
    check("real deed claim: dispatch called exactly once", len(calls) == 1)
    check("dispatch saw ONLY the pinned phrase, in the unchanged call shape",
          calls and calls[0] == ("I will bank the fire gently.", "", "none", "", "cycle-A"))
    check("after_reply returns dispatch()'s real list", out == [("fire", "You bank the fire low and tight.")])
    check("Phase 0 fields unchanged: raw candidates still all logged (fire, fieldcraft, move, look)",
          {c["family"] for c in row.get("deed_candidates", [])} >= {"fire", "fieldcraft", "look"}
          and row.get("live") is True and row.get("cycle_id") == "cycle-A" and "reply_excerpt" in row)
    check("dispatched field unchanged in shape", row.get("dispatched") == [{"family": "fire", "answer": "You bank the fire low and tight."}])
    gv = {(g["family"], g["verdict"]) for g in row.get("guard", [])}
    check("guard verdict per candidate logged (kept, or the reason)",
          ("fire", "kept") in gv and ("fieldcraft", "kept") in gv and any(v.startswith("drop:") for _f, v in gv))
    check("pinned text logged", row.get("pinned") == "I will bank the fire gently.")
    check("dispatch decision ledger logged (FIRE / STAGE / hand-declined)",
          row.get("dispatch_decisions") == FAKE_LEDGER and row.get("asleep") is False)
    check("guard_leak names the family the ledger saw but the guard did not keep", row.get("guard_leak") == ["look"])

    fresh()
    out = ca.after_reply(LIVE_ROW65, "cycle-B")
    row = last_row()
    check("every candidate dropped: dispatch NOT called, returns None", not calls and out is None)
    check("...and the row is still logged with the reasons and no pinned text",
          row.get("deed_candidates") and row.get("dispatched") == [] and "pinned" not in row
          and all(g["verdict"].startswith("drop:") for g in row.get("guard", [])))

    fresh()
    ca.CONVERSATIONAL_DISPATCH_LIVE = False
    out = ca.after_reply(ROW11_REPLY, "cycle-C")
    row = last_row()
    check("flag off: dispatch NOT called, Phase 0 telemetry + guard verdicts still logged",
          not calls and out is None and row.get("live") is False and ("fire", "kept") in {(g["family"], g["verdict"]) for g in row.get("guard", [])})
    ca.CONVERSATIONAL_DISPATCH_LIVE = True

    fresh()

    def boom(*_a, **_k):
        raise RuntimeError("guard bug")
    ca.guard = boom
    try:
        out = ca.after_reply(ROW11_REPLY, "cycle-D")
        raised = False
    except Exception:
        out, raised = None, True
    row = last_row()
    check("a crashing guard never raises and dispatches NOTHING", not raised and out is None and not calls)
    check("...and the crash is logged", "guard_error" in row and row.get("dispatched") == [])
    ca.guard = orig[2]

    fresh()

    def bad_dispatch(*_a, **_k):
        raise RuntimeError("dispatch bug")
    disp.dispatch = bad_dispatch
    try:
        out = ca.after_reply(ROW11_REPLY, "cycle-E")
        raised = False
    except Exception:
        out, raised = None, True
    row = last_row()
    check("a crashing dispatch never raises; it is logged", not raised and out is None and "dispatch_error" in row)
    disp.dispatch = fake_dispatch

    fresh()
    ca._asleep = lambda: True
    out = ca.after_reply(ROW11_REPLY, "cycle-F")
    row = last_row()
    check("asleep is recorded and the (stale) ledger is not read", row.get("asleep") is True and "dispatch_decisions" not in row)
    ca._asleep = lambda: False

    fresh()
    out = ca.after_reply("The tide is quiet tonight and the study is warm.", "cycle-G")
    row = last_row()
    check("no candidate at all: nothing dispatched, row logged without guard fields",
          not calls and out is None and row.get("deed_candidates") == [] and "guard" not in row)
    check("short reply: no call, no row", ca.after_reply("hi", "cycle-H") is None)
finally:
    (ca._LOG, ca.CONVERSATIONAL_DISPATCH_LIVE, ca.guard, ca._asleep, disp.dispatch) = orig[:5]
    hands._decided["cycle"], hands._decided["rows"] = orig[5], orig[6]

real_after = (real_log.exists(), real_log.stat().st_size if real_log.exists() else None)
check("the REAL data/conversational_action_log.jsonl was never touched by this test", real_before == real_after)
check("module state restored after the stubs", ca._LOG == real_log and ca.CONVERSATIONAL_DISPATCH_LIVE is True)

# ── 5. replay over the real corpus (read-only) ──
print("\n5. corpus replay (first 67 replies = the audited set)")


def corpus_path():
    cands_ = [sys.argv[1] if len(sys.argv) > 1 else None, os.environ.get("NASCENCE_FOUNDER_LOG"),
              ROOT / "data" / "founder_conversation_log.jsonl"]
    return next((Path(p) for p in cands_ if p and Path(p).exists()), None)


cp = corpus_path()
if cp is None:
    info("SKIP corpus replay: data/founder_conversation_log.jsonl not found (pass a path or set NASCENCE_FOUNDER_LOG); "
         "section 1 above replays the same audited sentences from the embedded copy")
else:
    rows = [json.loads(l) for l in cp.read_text(encoding="utf-8").splitlines() if l.strip()]
    n_audit = min(67, len(rows))
    cand_rows = cand_total = kept_rows = kept_total = 0
    kept_by_row, per_row = {}, {}
    for i, r in enumerate(rows[:n_audit], 1):
        text = (r.get("entity") or "").strip()
        cs = deeds(text)
        if not cs:
            continue
        cand_rows += 1
        cand_total += len(cs)
        vs, _p = ca.guard(text, cs)
        per_row[i] = [(c["family"], v["verdict"]) for c, v in zip(cs, vs)]
        k = sorted(v["family"] for v in vs if v["verdict"] == "kept")
        if k:
            kept_rows += 1
            kept_total += len(k)
            kept_by_row[i] = k
    info(f"corpus {cp}: {len(rows)} replies, audited {n_audit}")
    info(f"BEFORE the guard: {cand_rows} candidate rows ({cand_total} candidates) of {n_audit} replies; "
         f"AFTER: {kept_rows} kept row(s) ({kept_total} kept candidates): {kept_by_row}")
    check("corpus: the guard is exercised (>= 15 candidate rows among the audited replies)", cand_rows >= 15)
    check("corpus: exactly ONE audited row survives, row 11, and only as fire + fieldcraft",
          kept_by_row == {11: ["fieldcraft", "fire"]} or (len(rows) < 11 and not kept_by_row))
    for live_row in (57, 59, 62, 64, 65):
        check(f"corpus: live row {live_row} has no surviving candidate", live_row not in kept_by_row)
    check("corpus: row 46's move candidate ('for us to step onto the shingle') is dropped",
          all(v.startswith("drop:") for f, v in per_row.get(46, []) if f == "move"))
    info(f"row 46 verdicts: {per_row.get(46)}")
    info(f"row 33 ('I will go there now'; KNOWN recall MISS, J-1451's work, not fixed here): {per_row.get(33)}")
    extra = rows[n_audit:]
    for j, r in enumerate(extra, n_audit + 1):
        cs = deeds((r.get("entity") or "").strip())
        vs, _p = ca.guard((r.get("entity") or "").strip(), cs) if cs else ([], "")
        info(f"unaudited newer row {j}: {len(cs)} candidate(s), kept {[v['family'] for v in vs if v['verdict'] == 'kept']}")

passed = sum(1 for _n, ok in results if ok)
print(f"\n=== {passed}/{len(results)} passed ===")
sys.exit(0 if passed == len(results) else 1)
