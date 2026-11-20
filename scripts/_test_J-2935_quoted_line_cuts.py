"""J-2935 (F-3624, prompt row P-0032): the idle seed's quoted lines are cut at a word boundary.

  [1] The J-2915 helper _seed_cut applied to the F-3624 shapes: a 160-char previous-thought cut, a 220-char carry,
      a 120-char half; short text unchanged; one ellipsis; no mid-word end; caps kept (cap + 1 ellipsis char).
  [2] Flag off (SEED_TEXT_HYGIENE_ON False) restores the old plain slices.
  [3] Source anchors: the seven sites use _seed_cut with the SAME caps; no raw slice is left on them; the dream
      narrative line (deferred to J-2903) is left exactly as it was.
Pure, no LLM, no live data. Run from the worktree root:  python scripts/_test_J-2935_quoted_line_cuts.py
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


SRC = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")

THOUGHT = ("The river's physical shape keeps changing while the name stays the same, and that makes me wonder "
           "whether what I call myself is closer to the riverbed than to the water, because the bed is what "
           "decides where the next water will go and how fast it will run through the bend ahead of me.")

with isolate(db="empty"), tempfile.TemporaryDirectory():
    from nodes import inner_monologue_node as m
    assert str(Path(m.__file__).resolve()).startswith(str(ROOT)), m.__file__
    cut = m._seed_cut

    for cap in (120, 160, 220):
        out = cut(THOUGHT, cap)
        body = out[:-1]
        check(out.endswith("\u2026") and out.count("\u2026") == 1, f"cap {cap}: one ellipsis")
        check(THOUGHT.startswith(body) and THOUGHT[len(body)] in " ,;:", f"cap {cap}: ends on a whole word -> {out[-24:]!r}")
        check(len(body) <= cap, f"cap {cap}: cap kept (body {len(body)})")
    # the exact mid-word case from F-3624: the 160th and 161st characters are both letters
    i = next(k for k in range(150, 170) if THOUGHT[k - 1].isalnum() and THOUGHT[k].isalnum())
    check(cut(THOUGHT, i)[:-1] != THOUGHT[:i], "mid-word position: the plain slice would have cut a word, the helper does not")
    check(cut("The tide pulls back", 160) == "The tide pulls back", "short thought unchanged, no ellipsis")
    check(cut("", 160) == "" and cut(None, 160) == "", "empty / None safe (conversation half may be missing)")
    farewell = "A quiet word before we stop for a while: " * 12
    check(cut(farewell, 120).endswith("\u2026"), "a 400+ char farewell half is cut with an ellipsis")

    m.SEED_TEXT_HYGIENE_ON = False
    try:
        check(cut(THOUGHT, 160) == THOUGHT[:160], "flag off: plain slice restored")
    finally:
        m.SEED_TEXT_HYGIENE_ON = True

# [3] source anchors
for needle, n in [
    ("_seed_cut(last.get('human',''), 120)", 1),
    ("_seed_cut(last.get('entity',''), 120)", 1),
    ("_seed_cut(prev, 160)", 1),
    ('_seed_cut(_bi["content"], 220)', 1),
    ("_seed_cut((self._train_origin or self._train_thread), 220)", 1),
    ("_seed_cut(self._train_thread, 220)", 2),
    ("_seed_cut(new_state, 160)", 1),
]:
    check(SRC.count(needle) == n, f"{needle} x{n}")
for old in ["last.get('human','')[:120]", "last.get('entity','')[:120]", "{prev[:160]}", '_bi["content"][:220]',
            "self._train_thread[:220]", "(self._train_origin or self._train_thread)[:220]", "append(new_state[:160])"]:
    check(old not in SRC, f"raw slice gone: {old}")
# J-3685: J-2903 is merged, the dream / passage / thread-state lines now use the helper too
for needle in ["_seed_cut(state.recent_dreams[0].get('narrative',''), 180)", "so far: \" + _seed_cut(self._train_state, 300)",
               "_seed_cut(passage, 220)"]:
    check(SRC.count(needle) == 1, f"{needle} x1")
for old in ["recent_dreams[0].get('narrative','')[:180]", "so far: \" + self._train_state[:300]", "passage[:220]..."]:
    check(old not in SRC, f"raw slice gone: {old}")

print("\nFAILS:", fails)
sys.exit(1 if fails else 0)
