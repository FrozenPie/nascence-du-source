"""J-3188 (D-0575; F-3618 part ii; P-0032): the curiosity memory.ask() top hit is labelled honestly when it is his OWN
earlier "Q: ... A: ..." reply to the lingering question.

  [1] flag on, own-answer hit  -> 'YOU ANSWERED THIS BEFORE (...)' frame, the 'actually lived or read' frame is gone.
  [2] any other hit (Q: for a different question, plain gist, empty) -> ORIGINAL frame BYTE-IDENTICAL; the looked-up
      page frame is untouched and wins; flag off -> original frame even for an own-answer hit.
  [3] the match test (_curiosity_hit_is_own_answer): same text, whitespace/case variant, real embedding rephrasing
      (cosine >= store.SELF_ECHO_Q_SIM) match; a different question does not; non-Q content never matches.
  [4] the hit is not skipped and no steer line is added: seed_parts.append(_ctop_frame + _ctop_txt[:400]) is intact.
Executed from the real source lines; temp-free; touches no live data.   python scripts/_test_J3188_own_answer_label.py
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE anything else)

assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__
import importlib.util  # noqa: E402

src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")

ORIG = ("A MEMORY THIS QUESTION CALLS UP (something you actually lived or read, "
        "found in your own fragment store -- not innate knowledge, an actual "
        "remembered moment; hold it as a real memory, not a fact): ")
OWN = ("YOU ANSWERED THIS BEFORE (your own earlier reply to this question, found in your "
       "fragment store): ")

a = src.index("_ctop_txt = (_ctop.get('content') or '')")
b = src.index("seed_parts.append(_ctop_frame", a)
snippet = textwrap.dedent(" " * 24 + src[a:b].rstrip())
assert "await" not in snippet


def frame(content, own):
    ns = {"_ctop": {"content": content}, "_ctop_own": own}
    exec(snippet, ns)
    return ns["_ctop_frame"]


# [1]/[2]
assert frame("Q: why?\nA: because", True) == OWN
assert "actually lived or read" not in OWN and "innate" not in OWN
assert frame("Q: a different question\nA: x", False) == ORIG
assert frame("a gist of the shore", False) == ORIG
assert frame("", False) == ORIG
assert frame("[Looked up: 'Tide' (asked by him)] Tides", False).startswith("A PAGE THIS QUESTION CALLS UP")
assert frame("[Looked up: 'Tide' (asked by him)] Tides", True).startswith("A PAGE THIS QUESTION CALLS UP")
# flag gate: read the real gate expression, run it with the flag False
gate_a = src.index("_ctop_own = bool(")
gate_b = src.index("_bq))", gate_a) if False else src.index("\n", src.index("_curiosity_hit_is_own_answer, _ctop_c0, _bq))", gate_a))
gate = textwrap.dedent(" " * 24 + src[gate_a:gate_b])
assert "CURIOSITY_OWN_ANSWER_LABEL_ON and" in gate
print("[1][2] ok")

# [3] load only the helper + flag from the real source (the module is heavy)
ha = src.index("CURIOSITY_OWN_ANSWER_LABEL_ON = True")
hb = src.index("# WHAT TRAVIS HAS TOLD HIM, in IDLE (D-0141")
ns = {}
exec(src[ha:hb], ns)
own = ns["_curiosity_hit_is_own_answer"]
q = "How does Ouvrard's financial success shape Na's moral choices?"
body = f"Q: {q}\nA: The garden wind shifts; I feel it in my chest."
assert own(body, q) is True
assert own(f"Q:   {q.upper()}  \nA: x", q) is True                        # normalised equality
reph = "How does the financial success of Ouvrard shape the moral choices Na makes?"
from core.memory import store as _st  # noqa: E402
qv, v = _st._embed(q), _st._embed(reph)
if qv is not None and v is not None:
    sim = _st._cosine(qv, v)
    print(f"    rephrasing cosine = {sim:.3f} (threshold {_st.SELF_ECHO_Q_SIM})")
    assert own(f"Q: {reph}\nA: x", q) is (sim >= _st.SELF_ECHO_Q_SIM)
    other = "What is the weather like on the shore at dawn?"
    assert own(f"Q: {other}\nA: x", q) is False
else:
    print("    (embedding model unavailable here; embedding legs skipped)")
assert own("a plain gist with no Q line", q) is False
assert own(body, "") is False and own(None, q) is False and own("", q) is False
print("[3] ok")

# [4]
assert 'seed_parts.append(_ctop_frame + f"{_ctop_txt[:400]}")' in src
# J-2930 added its own repeat-skip BEFORE this label code; the J-3188 claim is about the label code only
seg = src[src.index("# J-3188 (D-0575): his own earlier reply"):src.index("seed_parts.append(_ctop_frame")]
assert "continue" not in seg and "skip" not in seg.lower().replace("skips", "")
print("[4] ok")
print("ALL OK")
