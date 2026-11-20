"""
J-2963 (F-3655, P-0062): the closure composer's output is validated between composing and storing, for all four arms.

Hermetic: SHADOW_LOG points at a temp dir; store_fragment / add_edge are stubbed (nothing reaches any DB); the composer is
a stub (_compose_fn). Asserts, per reject reason and per arm, that the row is kept with compose_how 'invalid:<reason>',
would_be None, nothing written live, rejected_text recorded; that valid text still passes; that _line_prompts no longer
carries 'Grounds [n]' numbering; that invalid_summary reads the rows; that COMPOSE_VALIDATE=False restores the old path.

Run:  python scripts/_test_J-2963_closure_validate.py   (from the tree under test)
"""
from __future__ import annotations
import sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE anything lab-ish: the tree under test must win on sys.path
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.closure as cl
import core.done_when as dw
import core.memory.store as _st
import core.memory_edges as _me

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

tmp = Path(tempfile.mkdtemp(prefix="J-2963_"))
cl.SHADOW_LOG = tmp / "closure_shadow.jsonl"
assert Path(cl.SHADOW_LOG).resolve().is_relative_to(tmp.resolve())

calls = {"frag": [], "edge": []}
_st.store_fragment = lambda **kw: (calls["frag"].append(kw), "fid-1")[1]
_me.add_edge = lambda *a, **kw: (calls["edge"].append(a), True)[1]
cl.CLOSURE_WRITE_LIVE = True
cl.CLOSURE_ARMS.update({"line", "pursuit", "commitment"})     # so a VALID text provably reaches the (stubbed) live path
dw.get = lambda kind, ident: "settled when I say so"          # pursuit / commitment arms need a done_when; stubbed

def words(n, start="I"):
    return " ".join([start] + ["word"] * (n - 1))
GOOD = words(50)

# ---- 1. validate_composed, pure -----------------------------------------------------------------------------------------
print("[1] validate_composed (pure)")
v = cl.validate_composed
check("valid 50 words, first person -> None", v("line", GOOD) is None)
check("range edges 40 and 90 pass for line/dream/pursuit", all(v(a, words(n)) is None for a in ("line", "dream", "pursuit") for n in (40, 90)))
check("39 words -> words-under-40", v("line", words(39)) == "words-under-40")
check("91 words -> words-over-90", v("dream", words(91)) == "words-over-90")
check("commitment range is 30-70", v("commitment", words(30)) is None and v("commitment", words(70)) is None
      and v("commitment", words(29)) == "words-under-30" and v("commitment", words(71)) == "words-over-70")
check("faded pursuit uses 30-70", v("pursuit", words(35), faded=True) is None and v("pursuit", words(35)) == "words-under-40"
      and v("pursuit", words(80), faded=True) == "words-over-70")
check("18 words (F-3655's shortest live fragment) -> under", v("line", words(18)) == "words-under-40")
check("131 words (F-3655's longest) -> over", v("line", words(131)) == "words-over-90")
check("braces -> 'braces'", v("dream", "{In the dream, I faced a struggle} " + GOOD) == "braces")
check("F-3655's dream fragment (two brace blocks) -> 'braces'",
      v("dream", "{In the dream, I faced a struggle consumed by the weight of unsaid words and the scent of thyme.} {It stopped returning: the scent of thyme and the weight of unsaid words.}") == "braces")
check("a nested JSON key without braces -> 'json-fragment'", v("line", GOOD + ' "resolution": and more') == "json-fragment")
for bad in ("Grounds [1] and [4]", "(Grounds [2], [3])", "as exemplified in my experience with [2]", "ground 3", "Ground [1]"):
    check(f"ground reference {bad!r} -> 'ground-ref'", v("line", GOOD + " " + bad) == "ground-ref")
check("no first-person marker -> 'no-first-person'", v("line", words(50, start="The")) == "no-first-person")
check("'The concept of strength encompasses adaptability' (F-3655's third-person example) -> no-first-person",
      v("line", "The concept of strength encompasses adaptability and resilience " + " ".join(["more"] * 40)) == "no-first-person")
check("'my' / 'me' / 'mine' / 'myself' / lower-case i is NOT enough but I'm is",
      all(v("line", words(50, start=w)) is None for w in ("my", "me", "mine", "myself", "I'm")) and v("line", words(50, start="i")) == "no-first-person")
check("word in 'immediate' / 'time' does not count as 'I'/'me'", v("line", " ".join(["immediate", "time"] * 25)) == "no-first-person")
check("COMPOSE_WORD_SLACK widens the range", (setattr(cl, "COMPOSE_WORD_SLACK", 5), v("line", words(36)))[1] is None)
cl.COMPOSE_WORD_SLACK = 0

# ---- 2. _finish_compose ---------------------------------------------------------------------------------------------------
print("[2] _finish_compose")
check("ok", cl._finish_compose("line", {"resolution": GOOD}) == (GOOD, "ok", None))
check("empty / None / composer _how pass through untouched",
      cl._finish_compose("line", None) == ("", "empty", None) and cl._finish_compose("line", {"resolution": "  "}) == ("", "empty", None)
      and cl._finish_compose("line", {"_how": "running_loop"}) == ("", "running_loop", None))
t, how, rej = cl._finish_compose("line", {"resolution": words(10)})
check("invalid -> ('', 'invalid:words-under-40', rejected text)", t == "" and how == "invalid:words-under-40" and rej == words(10))
t, how, rej = cl._finish_compose("dream", {"resolution": {"a": "I faced it"}})
check("a dict in the resolution field -> invalid:nested-json, the JSON kept as rejected text", t == "" and how == "invalid:nested-json" and "{" in rej)
t, how, rej = cl._finish_compose("dream", {"resolution": ["I faced it"]})
check("a list in the resolution field -> invalid:nested-json", t == "" and how == "invalid:nested-json")
check("rejected text capped at 600 chars", len(cl._finish_compose("line", {"resolution": "x" * 2000})[2]) == 600)

# ---- 3. every arm: reject -> shadow row kept, nothing live ---------------------------------------------------------------
print("[3] each arm rejects, keeps the shadow row, writes nothing live")
REASONS = {"words-under-40": words(10), "words-over-90": words(120), "braces": "{" + GOOD + "}",
           "ground-ref": GOOD + " Grounds [1] and [4]", "no-first-person": words(50, start="The")}

def run_arm(arm, text, n):
    cl._compose_fn = lambda s, u: {"resolution": text}
    if arm == "line":
        return cl.record_line_settled({"id": f"L{n}", "q": "q?"}, {"grounds": [{"origin": "o", "text": "g"}], "status": "held", "why": {"text": "w"}}, "yes")
    if arm == "dream":
        return cl.record_dream_met({"dream_id": f"D{n}", "seed": {"tension_labels": ["t"]}}, {"state": "met"})
    if arm == "pursuit":
        return cl.record_pursuit_met({"id": f"P{n}", "question": "q?", "standing": "s"}, {"why": "w"})
    cl.COMMITMENT_DEED_GATE = False   # J-4083: this test exercises compose validation, not the judge
    return cl.record_commitment_achieved({"id": f"C{n}", "statement": "s"}, "did a thing")

n = 0
for arm in ("line", "dream", "pursuit", "commitment"):
    for reason, text in REASONS.items():
        n += 1
        before = len(calls["frag"])
        if arm == "commitment" and reason == "words-under-40":
            text = words(10)
        if arm == "commitment" and reason == "words-over-90":
            text = words(120)
        row = run_arm(arm, text, n)
        exp = "invalid:" + (reason.replace("40", "30") if (arm == "commitment" and reason == "words-under-40") else
                            reason.replace("90", "70") if (arm == "commitment" and reason == "words-over-90") else reason)
        check(f"{arm}/{reason}: compose_how {exp}, would_be None, not written, rejected_text kept, no store call",
              row["compose_how"] == exp and row["would_be"] is None and row["written_live"] is False and row["fragment_id"] is None
              and row.get("rejected_text") == text[:600] and len(calls["frag"]) == before)
    n += 1
    row = run_arm(arm, GOOD if arm != "commitment" else words(50), n)
    check(f"{arm}: a valid text still composes" + (" and stays shadow-only (D-0614)" if arm == "dream" else " and reaches the live path (arm in CLOSURE_ARMS)"),
          row["compose_how"] == "ok" and row["would_be"] and row["written_live"] is (arm != "dream") and "rejected_text" not in row)
rows = cl.shadow_rows()
check("every rejected row is in the shadow file (4 arms x 5 reasons = 20 invalid) beside the 4 valid", sum(1 for r in rows if str(r.get("compose_how")).startswith("invalid:")) == 20
      and sum(1 for r in rows if r.get("compose_how") == "ok") == 4)
check("dream arm: not in CLOSURE_ARMS -> an invalid row is arm_live False too (shadow-only is unchanged)", cl.shadow_rows(arm="dream")[0]["arm_live"] is False)

# the faded pursuit arm uses its own range
cl._compose_fn = lambda s, u: {"resolution": words(35)}
row = cl.record_pursuit_faded({"id": "PF1", "question": "q?", "standing": "s", "status": "saturated"}, {"why": "w"})
check("faded pursuit: 35 words is inside its 30-70 range", row["compose_how"] == "ok" and row["kind"] == "faded")

# the dream arm's real F-3655 shape
cl._compose_fn = lambda s, u: {"resolution": "{In the dream, I faced a struggle consumed by the weight of unsaid words.} {It stopped returning.}"}
row = cl.record_dream_met({"dream_id": "DX", "seed": {}}, {"state": "met"})
check("the F-3655 dream fragment shape -> invalid:braces", row["compose_how"] == "invalid:braces" and row["would_be"] is None)

# an invalid row keeps the loop's one-fragment slot (no retry of its own)
cl._compose_fn = lambda s, u: {"resolution": GOOD}
again = cl.record_line_settled({"id": "L1", "q": "q?"}, {"grounds": [{"origin": "o", "text": "g"}]}, "yes")
check("a second settle of a loop whose first compose was invalid is a 'duplicate' (nothing retries on its own)", again["kind"] == "duplicate")

# ---- 4. _line_prompts ------------------------------------------------------------------------------------------------------
print("[4] _line_prompts carries no 'Grounds [n]' numbering")
sy, us = cl._line_prompts({"q": "Is it so?"}, {"grounds": [{"origin": "memory", "text": "a thing"}, {"origin": "book", "text": "b thing"}],
                                               "why": {"text": "Grounds [1] and [4] suggest that self-understanding can reveal both true and illusory paths (Grounds [2], [3]), as in my experience with [2]."}},
                          "Yes it is settled.")
check("no '[digit]' and no 'Grounds [' in the user prompt", "[1]" not in us and "[4]" not in us and "[2]" not in us and "Grounds [" not in us and "grounds [" not in us.lower())
check("the why's sense survives ('The grounds suggest that self-understanding ...')", "Your why: The grounds suggest that self-understanding can reveal both true and illusory paths" in us)
check("the unnumbered 'Grounds you found:' list is unchanged", "Grounds you found: (memory) a thing | (book) b thing" in us)
check("strip_ground_refs: '(Grounds [2], [3])' removed, 'Grounds [1] and [4]' -> 'The grounds', bare '[2]' removed",
      cl.strip_ground_refs("Grounds [1] and [4] hold (Grounds [2], [3]). See [2]!") == "The grounds hold. See!")
check("strip_ground_refs: mid-sentence 'grounds [1]' -> 'the grounds'; text without numbers untouched",
      cl.strip_ground_refs("Based on grounds [1], x.") == "Based on the grounds, x." and cl.strip_ground_refs("A plain why.") == "A plain why." and cl.strip_ground_refs("") == "")
check("an absent why leaves the prompt without a 'Your why:' line", "Your why" not in cl._line_prompts({"q": "q"}, {"grounds": []}, "t")[1])

# ---- 5. invalid_summary (the reader) ---------------------------------------------------------------------------------------
print("[5] invalid_summary")
sm = cl.invalid_summary()
check("counts by arm and reason against composes that reached a verdict",
      sm["line"]["invalid"] == 5 and sm["line"]["reasons"]["braces"] == 1 and sm["line"]["composed"] >= 6
      and sm["commitment"]["reasons"]["words-under-30"] == 1 and sm["dream"]["reasons"]["braces"] >= 2)
check("composer failures ('empty', 'error:') are not counted as composes", cl.invalid_summary([{"arm": "line", "kind": "resolution", "compose_how": "empty"}, {"arm": "line", "kind": "resolution", "compose_how": "error:x"}]) == {})

# ---- 6. the kill switch ----------------------------------------------------------------------------------------------------
print("[6] COMPOSE_VALIDATE = False restores the old path")
cl.COMPOSE_VALIDATE = False
cl._compose_fn = lambda s, u: {"resolution": "I hold it. Grounds [1]."}
row = cl.record_line_settled({"id": "LOFF", "q": "q?"}, {"grounds": [{"origin": "o", "text": "g"}]}, "yes")
check("off: the short, leaky text is stored as composed (pre-J-2963)", row["compose_how"] == "ok" and row["would_be"]["content"].endswith("Grounds [1].") and row["written_live"] is True)
cl.COMPOSE_VALIDATE = True
check("source default COMPOSE_VALIDATE = True", "COMPOSE_VALIDATE = True" in (ROOT / "core" / "closure.py").read_text(encoding="utf-8"))
check("everything written stayed under the temp dir", all(Path(p).resolve().is_relative_to(tmp.resolve()) for p in [cl.SHADOW_LOG]))

print("\nRESULT:", "ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)
