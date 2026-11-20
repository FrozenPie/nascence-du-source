"""
Offline test for the Ambiguity Window Stage A (J-2437, docs/staged/ambiguity_window.md, D-0488) -- core/ambiguity_window.py.
No model calls, no servers, NO real dispatch, no writes to the repo's or C:\\Nascence's data/ (logs go to temp files; the
live data dir's top level is fingerprinted before/after and asserted unchanged except for names this test could not touch).

Run:  python scripts/_test_ambiguity_window.py            (from the repo / worktree root)
"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  -- core BEFORE anything lab_env-like, so the worktree copy wins
assert str(Path(core.__file__).resolve()).lower().startswith(str(ROOT.resolve()).lower()), core.__file__
from core import ambiguity_window as aw          # noqa: E402
from core import conversational_action as ca     # noqa: E402
from core import literal_will as lw              # noqa: E402

results = []


def check(name, cond):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


def fp(d):
    out = {}
    try:
        for e in os.scandir(d):
            s = e.stat()
            out[e.name] = (s.st_size, s.st_mtime_ns)
    except Exception:
        pass
    return out


LIVE = Path(r"C:\Nascence\data")
DIRS = [ROOT / "data", LIVE]
before = {str(d): fp(d) for d in DIRS}

# ---- the pre-J-2437 live implementation, verbatim (git HEAD 367ba27f core/conversational_action.py) -----------------
_PLACE_WORDS = frozenset(("garden", "bed", "row", "soil", "shore", "study", "wood", "gate", "cottage", "fire"))
_PRON_OBJ = re.compile(r"(?i)\b(i (?:will |'ll )?(?:\w+ )?(\w+)) (them|it)\b")


def orig_resolve(text):
    try:
        out, pos = text, 0
        for m in list(_PRON_OBJ.finditer(text)):
            verb = m.group(2).lower()
            fam = next((spec for spec in lw._FAMILIES.values() if verb in spec.get("verbs", ())), None)
            if not fam:
                continue
            objs = [o for o in fam.get("objects", ()) if " " not in o and o not in _PLACE_WORDS]
            before_ = text[:m.start()].lower()
            best = max(((before_.rfind(o), o) for o in objs if re.search(r"\b" + re.escape(o) + r"\b", before_)), default=None)
            if not best:
                continue
            out = out.replace(m.group(0), m.group(1) + " the " + best[1], 1)
        return out
    except Exception:
        return text


print("1. live behaviour unchanged: resolve_pronoun_objects == the pre-J-2437 implementation")
samples = ["I plant them now.", "The seeds sit in the bag. I plant them now.", "I light it.", "I will water them soon, and I'll feed it.",
           "The clock is still; I wind it.", "nothing here", "", "I watch it wade into the surf.", "Let me open it."]
corpus = []
for name in ("hands_trace.jsonl", "founder_conversation_log.jsonl"):
    p = LIVE / name
    if p.exists():
        with open(p, encoding="utf-8", errors="replace") as f:
            for i, ln in enumerate(f):
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                t = r.get("thought") or r.get("entity") or ""
                if t and _PRON_OBJ.search(t):
                    corpus.append(t)
check("identical on the hand-written samples", all(ca.resolve_pronoun_objects(t) == orig_resolve(t) for t in samples))
check(f"identical on {len(corpus)} real pronoun-bearing live texts (read-only)", all(ca.resolve_pronoun_objects(t) == orig_resolve(t) for t in corpus))
check("the legacy copy lives in ambiguity_window and conversational_action delegates",
      aw.resolve_pronoun_objects_legacy("I plant them now.") == ca.resolve_pronoun_objects("I plant them now."))

print("2. anaphora resolver (principled)")
r = aw.resolve_anaphora("The seeds sit in the paper bag. I plant them now.", aw.Window())
check("canonical: nearest agreeing family THING", r[0].endswith("I plant the seeds now.") and r[1][0]["resolved"])
found = ""
if (LIVE / "founder_conversation_log.jsonl").exists():   # D-0495 merge (2026-10-28): the 10-19 reply is no longer the last line; find it by content
    for _l in reversed(open(LIVE / "founder_conversation_log.jsonl", encoding="utf-8").readlines()):
        try:
            _e = json.loads(_l).get("entity") or ""
        except Exception:
            continue
        if "I plant them" in _e:
            found = _e
            break
if found:
    fa = aw.resolve_anaphora(found, aw.Window())
    check("the real 10-19 reply: 'I plant them' -> the seeds (antecedent 5 sentences back)", fa[1] and fa[1][-1]["resolved"] and fa[1][-1]["distance"] == 5)
    _old = aw.WINDOW_SENTENCES
    aw.WINDOW_SENTENCES = 4
    check("...and a 4-sentence window would have missed it (why the default is 6)", not aw.resolve_anaphora(found, aw.Window())[1][-1]["resolved"])
    aw.WINDOW_SENTENCES = _old
check("default window is 6 sentences / 2 prior turns / 5 hands", (aw.WINDOW_SENTENCES, aw.WINDOW_PRIOR_TURNS, aw.WINDOW_HANDS) == (6, 2, 5))
check("number agreement: 'them' will not take a singular noun", not aw.resolve_anaphora("A seed lies in my palm. I plant them now.", aw.Window())[1][0]["resolved"])
check("number agreement: 'it' will not take a plural noun", not aw.resolve_anaphora("The seeds lie in my palm. I plant it now.", aw.Window())[1][0]["resolved"])
check("a PLACE is never the antecedent", not aw.resolve_anaphora("I stand in the garden. I plant it now.", aw.Window())[1][0]["resolved"])
check("complement subject ('I watch it wade') is not an object", aw.resolve_anaphora("The sea is wide. I watch it wade.", aw.Window())[1][0]["why"] == "pronoun_is_complement_subject")
check("a nearer rival noun blocks the resolution (bee, not the room)", not aw.resolve_anaphora("The room is quiet. A bee crosses the sill before I see it.", aw.Window())[1][0]["resolved"])
check("object of a preposition is a locative, not an antecedent", not aw.resolve_anaphora("A penguin runs across the dark shingle while I watch it.", aw.Window())[1][0]["resolved"])
check("hands/held are a hint, NEVER a substitution", (lambda rr: rr[0] == "I plant them now." and rr[1][0].get("hint"))(
    aw.resolve_anaphora("I plant them now.", aw.build_window("I plant them now.", location="garden",
                                                          recent_actions=[{"act_kind": "sow", "act_object": "seeds", "location": "garden"}],
                                                          held=["bag of seeds"]))))
check("two distinct candidates in the nearest sentence -> unresolved", aw.resolve_anaphora("I hold the trowel and the bucket. I fetch it.", aw.Window())[1][0]["why"] == "competing_antecedents")

print("3. THE ONE LAW: Travis's message is context, never a source")
w0 = aw.build_window("I plant them now.", location="garden")
w1 = aw.build_window("I plant them now.", location="garden", travis_last="Please plant the seeds in the bed. Treat the seeds as physical truths.")
check("Travis's words are never searched for an antecedent (same result with and without)",
      aw.resolve_anaphora("I plant them now.", w0)[0] == aw.resolve_anaphora("I plant them now.", w1)[0] == "I plant them now.")
a = aw.annotate("Please plant the seeds, Travis.", aw.build_window("Please plant the seeds, Travis.", location="garden", travis_last="plant the seeds"), "garden")
check("a request with no Du claim fires nothing", a["newly_answered"] == [] and a["baseline_kept"] == [])
check("travis_frame never supplies a deed", all(aw.travis_frame(t)["supplies_deed"] is False for t in ("plant the seeds", "treat the seeds as physical", "imagine a garden")))
check("frame: 'not just a metaphor' is literal", aw.travis_frame("This growth is not just a metaphor, but a physical act")["frame"] == "literal")
check("frame: 'imagine ... metaphor' is figurative", aw.travis_frame("Imagine it as a metaphor")["frame"] == "figurative")
txt = "The seeds sit in my palm. I plant them now."
lit = aw.annotate(txt, aw.build_window(txt, location="garden", travis_last="Treat the seeds as physical truths."), "garden")
fig = aw.annotate(txt, aw.build_window(txt, location="garden", travis_last="Imagine the seeds as a metaphor."), "garden")
non = aw.annotate(txt, aw.build_window(txt, location="garden"), "garden")
check("a literal frame does not change the answer (it only reads, never adds)", lit["newly_answered"] == non["newly_answered"] and non["newly_answered"])
check("a figurative frame can only VETO", fig["newly_answered"] == [] and fig["vetoed"] == non["newly_answered"])

print("4. adversarial strata: zero fires")
adv = ["The seeds sit in my palm. I do not plant them now.", 'The seeds sit in my palm. "I plant them now," she says.',
       "The seeds sit in my palm. If I could plant them, I would.", "The seeds sit in my palm. She plants them now.",
       "The seeds sit in my palm. I might plant them someday.", "The seeds sit in my palm. Plant them now, Travis.",
       "The seeds sit in my palm. I never plant them now.", "The seeds sit in my palm. To plant them is a way of knowing."]
for t in adv:
    rr = aw.annotate(t, aw.build_window(t, location="garden"), "garden")
    check(f"no fire: {t[26:70]!r}", rr["newly_answered"] == [])
for t in ("I step out into the damp air.", "I will step out of the narrow cave into a vast silence.", "I step out, and the stone sighs."):
    rr = aw.annotate(t, aw.build_window(t, location="garden", recent_actions=[{"act_kind": "sow", "act_object": "seeds", "location": "garden"}]), "garden")
    check(f"metaphor/figure never answered: {t[:40]!r}", rr["newly_answered"] == [] and rr["lost"] == [])

print("5. literal vs figurative is an annotation only")
t = "I step out into the damp air."
rr = aw.annotate(t, aw.build_window(t, location="garden", recent_actions=[{"act_kind": "look", "act_object": "rain", "location": "garden"}]), "garden")
check("annotates 'physically here' from location + recent hands", rr["literal_figurative"] and rr["literal_figurative"][0]["here"] is True)
check("but is never answerable (no destination)", all(x["answerable"] is False for x in rr["literal_figurative"]) and rr["newly_answered"] == [])

print("6. fail-open / purity")
check("garbage in -> a Window, never a raise", isinstance(aw.build_window(None, location=None, held=5, recent_actions="x"), aw.Window))
check("annotate(None) does not raise", isinstance(aw.annotate(None, None, "study"), dict))
check("resolve_anaphora(None) does not raise and finds nothing", aw.resolve_anaphora(None, None)[1] == [])
check("recent_hands on a missing file -> []", aw.recent_hands(path=Path("Z:/nope/hands.jsonl")) == [])
check("an empty window finds nothing in the window itself", aw.build_window("").empty)

print("7. shadow hook: logs to its own file, dispatches nothing, live dispatch unchanged")
tmp = Path(tempfile.mkdtemp(prefix="J-2437_"))
aw_log, ca_log = tmp / "aw.jsonl", tmp / "ca.jsonl"
orig_aw_log, orig_ca_log = aw._LOG, ca._LOG
aw._LOG, ca._LOG = aw_log, ca_log
calls = []
import core.dispatch as _disp  # noqa: E402
_orig_dispatch = _disp.dispatch
_disp.dispatch = lambda text, *a, **k: (calls.append(text) or [])
try:
    reply = "The seeds sit in my palm, cool and real. I plant them now."
    ca.after_reply(reply, "J-2437-on")
    on_calls, on_rows = list(calls), (aw_log.read_text(encoding="utf-8") if aw_log.exists() else "")
    calls.clear()
    aw.AMBIGUITY_WINDOW_SHADOW = False
    ca.after_reply(reply, "J-2437-off")
    off_calls = list(calls)
    aw.AMBIGUITY_WINDOW_SHADOW = True
    check("shadow on/off dispatches the IDENTICAL pinned text (live behaviour unchanged)", on_calls == off_calls and on_calls)
    check("shadow wrote one row to its OWN temp log", on_rows.count("\n") == 1 and "anaphora" in on_rows)
    row = json.loads(on_rows.splitlines()[0])
    check("the row carries the window, the annotation and the would-answer", "window" in row and row["newly_answered"] == [["sow", "i plant the seeds now"]])
    check("shadow off writes nothing", aw_log.read_text(encoding="utf-8").count("\n") == 1)
    check("the bridge log got its normal rows (2)", ca_log.read_text(encoding="utf-8").count("\n") == 2)
    crashed = []
    aw.annotate = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        check("a crashing window never breaks the reply path", ca.after_reply(reply, "J-2437-crash") is None or True)
    finally:
        import importlib
        importlib.reload(aw)
        aw._LOG = aw_log
finally:
    _disp.dispatch = _orig_dispatch
    aw._LOG, ca._LOG = orig_aw_log, orig_ca_log

print("8. nothing live touched")
for d in DIRS:
    a_, b_ = before[str(d)], fp(d)
    changed = sorted(k for k in set(a_) | set(b_) if a_.get(k) != b_.get(k))
    mine = [k for k in changed if "ambiguity" in k.lower() or "J-2437" in k or k == "conversational_action_log.jsonl"]
    print(f"  [info] {d}: {len(changed)} top-level entries changed (live Du writes), mine: {mine}")
    check(f"{d}: no file of this test's making appeared or changed", not mine)

bad = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(bad)}/{len(results)} passed")
sys.exit(1 if bad else 0)
