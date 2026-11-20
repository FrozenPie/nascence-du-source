"""J-2915 (F-3587, F-3579, F-3575): idle seed text hygiene in nodes/inner_monologue_node.py.

  [1] _seed_cut: text that fits is unchanged (no ellipsis); a cut lands on a word boundary and gets ONE ellipsis;
      a first word longer than the limit is hard-cut; trailing comma/dash dropped before the ellipsis; terminate=True
      adds a full stop to a bare uncut ending and not to one already terminal; the shock/finding/title cases.
  [2] _seed_join_tail: a question-ended concern + '. Turn to it' -> no '?.'; a '.'-ended concern -> no '..'; bare
      '.' tail after a '?' -> just the '?'; a concern with no terminal punctuation keeps the old join; closing quote
      after '?' is looked through; a tail not starting with '.' is untouched.
  [3] Flag off (SEED_TEXT_HYGIENE_ON False) restores the old slices and join exactly.
  [4] Source anchors: the four slices/the join are replaced at their five sites, no raw [:260]/[:400]-on-finding left.
Pure functions, no LLM, no live data.
Run from the worktree root:  python scripts/_test_J-2915_seed_text_hygiene.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE lab_env)

assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate  # noqa: E402

fails = 0


def check(cond, msg):
    global fails
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails += 1


SRC_PATH = ROOT / "nodes" / "inner_monologue_node.py"
SRC = SRC_PATH.read_text(encoding="utf-8")

with isolate(db="empty"), tempfile.TemporaryDirectory():
    from nodes import inner_monologue_node as m
    assert str(Path(m.__file__).resolve()).startswith(str(ROOT)), m.__file__
    cut, join = m._seed_cut, m._seed_join_tail

    # [1] _seed_cut
    check(cut("short text", 260) == "short text", "fits: unchanged, no ellipsis")
    check(cut("x" * 260, 260) == "x" * 260, "exactly at the limit: unchanged")
    shock = ("The film follows a young woman who takes on her sister's persona after a terrible accident, "
             "and the town slowly comes to doubt which of them it buried that winter in the old churchyard "
             "behind the mill, where nobody had gone since the flood of the year before the war began.")
    out = cut(shock, 100)
    check(out.endswith("\u2026") and out.count("\u2026") == 1, "cut: exactly one ellipsis -> " + repr(out[-30:]))
    body = out[:-1]
    check(shock.startswith(body) and shock[len(body)] in " ,", "cut lands on a word boundary (next char is a space)")
    check(len(body) <= 100, "cut body within the limit")
    # the F-3575 example: cut falls inside 'persona' at index limit
    ex = "the film takes on her sister's persona and goes on"
    i = ex.index("persona") + 3
    o2 = cut(ex, i)
    check(o2 == "the film takes on her sister's\u2026", "mid-word cut backs off to the last whole word -> " + repr(o2))
    check(cut("alpha, beta, gamma, delta", 12) == "alpha, beta\u2026", "trailing comma dropped before the ellipsis")
    check(cut("alpha beta \u2014 gamma delta", 13) == "alpha beta\u2026", "trailing dash dropped before the ellipsis")
    check(cut("a" * 50, 10) == "a" * 10 + "\u2026", "single long word hard-cut, ellipsis")
    check(cut("alpha beta gamma", 10) == "alpha beta\u2026", "limit falling on a space: clean cut")
    fnd = "Biological clocks in plants are driven by a feedback loop of genes" + " and proteins that run all day long." * 15
    f_out = cut(fnd, 400, terminate=True)
    check(f_out.endswith("\u2026") and not f_out.endswith(".\u2026"), "finding cut: ellipsis, no doubled stop")
    seed_line = "'. While it sat, you found something: " + f_out + " Does this answer it?"
    check("\u2026 Does this answer it?" in seed_line and "biolog Does" not in seed_line, "finding then next sentence reads cleanly")
    check(cut("A short finding.", 400, terminate=True) == "A short finding.", "terminate: already terminal -> unchanged")
    check(cut("A short finding", 400, terminate=True) == "A short finding.", "terminate: bare ending gets a full stop")
    check(cut("Is it so?", 400, terminate=True) == "Is it so?", "terminate: '?' counts as terminal")
    check(cut("A short finding", 400) == "A short finding", "no terminate flag: bare ending untouched")
    check(cut("", 60, terminate=True) == "", "empty -> empty")
    check(cut(None, 60) == "", "None -> empty")
    check(len(cut("Title of a very long book " * 5, 60)) <= 61, "reread title bounded (limit + ellipsis)")

    # [2] _seed_join_tail
    t1 = ". Turn to it if it pulls you, or let it rest."
    check(join("Who is the 'Evil Twin'?", t1) == "Who is the 'Evil Twin'? Turn to it if it pulls you, or let it rest.",
          "question concern: no '?.'")
    check("?." not in join("Who is the 'Evil Twin'?", t1), "no '?.' substring")
    check(join("Finish the chapter.", t1) == "Finish the chapter. Turn to it if it pulls you, or let it rest.",
          "full-stop concern: no '..'")
    check(join("Who is it?", ".") == "Who is it?", "bare '.' tail after '?' -> just the '?'")
    check(join("Learn the harbour songs", t1) == "Learn the harbour songs" + t1, "no terminal punct: old join kept")
    check(join("Learn the harbour songs", ".") == "Learn the harbour songs.", "no terminal punct, bare tail: old join")
    check(join("Why 'the sea'?'", ". x").startswith("Why 'the sea'?' x"), "closing quote after '?' looked through")
    check(join("Why?", " no leading stop") == "Why? no leading stop", "tail without leading '.' untouched")
    check(join("Why?  ", t1) == "Why? Turn to it if it pulls you, or let it rest.", "trailing spaces trimmed on join")
    check(join("Wait\u2026", ". a") == "Wait\u2026 a", "ellipsis counts as terminal")
    check(join("", ".") == ".", "empty concern keeps old join")

    # [3] flag off -> old behaviour exactly
    m.SEED_TEXT_HYGIENE_ON = False
    try:
        check(cut(shock, 100) == shock[:100], "flag off: plain slice")
        check(join("Why?", t1) == "Why?" + t1, "flag off: old join (the '?.' returns)")
    finally:
        m.SEED_TEXT_HYGIENE_ON = True

# [4] source anchors
check("[:260]" not in SRC.replace("_seed_cut(_shock[1], 260)", ""), "no raw [:260] left on the shock")
check(SRC.count("_seed_cut(_shock[1], 260)") == 1, "shock site uses _seed_cut")
check(SRC.count("terminate=True)") == 2, "both frontier-finding sites use _seed_cut(..., terminate=True)")
check('["finding"][:400]' not in SRC and '"finding") or "")[:400]' not in SRC, "no raw [:400] on a finding")
check('_rr["title"][:60]' not in SRC and '_seed_cut(_rr["title"], 60)' in SRC, "reread title uses _seed_cut")
check('_seed_join_tail(_pc["text"], _tail)' in SRC and '_pc["text"] + _tail' not in SRC, "concern join uses _seed_join_tail")
check("SEED_TEXT_HYGIENE_ON = True" in SRC, "flag defaults True")

print("\nFAILS:", fails)
sys.exit(1 if fails else 0)
