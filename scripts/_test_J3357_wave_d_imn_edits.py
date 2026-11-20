"""Wave D0-b edits to nodes/inner_monologue_node.py (J-3357 / J-3374 / J-3196).

  [1] J-3357 (D-0582): _math_drill, executed from the real source with stubs: a miss at level <= HINT_AUTHORED_MAX_LEVEL
      still gets ONE taught re-attempt (2 _solve_attempt calls); a miss at level > the cap gets NONE (1 call), and the
      independent result is what record()/log() receive in both cases. A hit never re-attempts.
  [2] J-3374 (D-0587): exactly one recall_fragments call passes exclude_own_works=True, and it is the _author
      grounding call (k=5, grounded_only=True); no other recall_fragments call in the file passes it.
  [3] J-3196 (D-0584): the import is in, _author builds the part prompt through core.plain_prose.part_system_prompt with
      the flag read from GRAND_WORK_PLAIN_PROSE; the flag is False; flag False -> json path (call_node_json, 'part' key),
      flag True -> call_node_prose. The old inline prompt literal is gone from the node (it lives in plain_prose).
Offline; touches no live data.   python scripts/_test_J3357_wave_d_imn_edits.py
"""
from __future__ import annotations

import ast
import asyncio
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
from core import math_drill, plain_prose  # noqa: E402

SRC = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
TREE = ast.parse(SRC)

# ---------------------------------------------------------------- [1] J-3357
fn = next(n for n in ast.walk(TREE) if isinstance(n, ast.AsyncFunctionDef) and n.name == "_math_drill")
seg = ast.get_source_segment(SRC, fn)
code = textwrap.dedent(seg)


class _Log:
    def info(self, *a, **k): pass
    def warning(self, *a, **k): pass


class _Node:
    def __init__(self, right):
        self.calls = 0
        self.right = right
    def _feel_joy(self, *a, **k): pass

    async def _rate_drill_item(self, domain, prob):   # J-4052: J-3830 added this call; stub = rating step off
        return None
    async def _solve_attempt(self, system, user, **kw):      # J-2988: require_answer=True
        self.calls += 1
        # first call is the independent attempt; later ones are taught re-attempts (system mentions the method)
        taught = "Here is the method" in system
        return {"working": "w", "answer": "42" if (self.right or taught) else "0"}


async def run(level, right):
    rec, logged = [], []
    probs = [{"text": "6*7", "answer": 42, "level": level}]
    saved = {k: getattr(math_drill, k) for k in ("due", "generate", "record", "log", "status", "BATCH", "method_hint")}
    n_due = {"n": 0}
    def due():
        n_due["n"] += 1
        return n_due["n"] <= 1
    math_drill.due = due
    math_drill.generate = lambda: probs[0]
    math_drill.record = lambda lvl, ok: rec.append((lvl, ok))
    math_drill.log = lambda *a, **k: logged.append(a)   # J-4052: J-3830 passes item_id=
    math_drill.status = lambda: {"today_done": 1}
    math_drill.BATCH = 1
    math_drill.method_hint = lambda lvl: "HINT"
    ns = {"asyncio": asyncio, "time": __import__("time"), "logger": _Log(), "store_fragment": lambda **k: None,
          "JOY_CROSSING": 0.0, "CognitiveState": object, "InnerMonologueNode": object}
    try:
        exec(code, ns)
        node = _Node(right)
        await ns["_math_drill"](node, None)
    finally:
        for k, v in saved.items():
            setattr(math_drill, k, v)
    return node.calls, rec, logged

cap = math_drill.HINT_AUTHORED_MAX_LEVEL
assert cap == 9, cap
c, rec, lg = asyncio.run(run(cap, right=False))
assert c == 2 and rec == [(cap, False)], (c, rec)            # authored level: taught re-attempt happens, ladder unaffected
c, rec, lg = asyncio.run(run(cap + 1, right=False))
assert c == 1 and rec == [(cap + 1, False)], (c, rec)        # above the cap: no second attempt, miss stands
assert lg[0][3] is False                                      # log() got correct=False (independent result)
c, rec, lg = asyncio.run(run(cap + 5, right=True))
assert c == 1 and rec == [(cap + 5, True)], (c, rec)
c, rec, lg = asyncio.run(run(1, right=True))
assert c == 1 and rec == [(1, True)], (c, rec)
print("[1] ok: taught re-attempt only when level <= HINT_AUTHORED_MAX_LEVEL")

# ---------------------------------------------------------------- [2] J-3374
calls = [n for n in ast.walk(TREE) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
         and n.func.attr == "recall_fragments"]
with_flag = [n for n in calls if any(k.arg == "exclude_own_works" for k in n.keywords)]
assert len(with_flag) == 1, len(with_flag)
call = with_flag[0]
kw = {k.arg: k.value for k in call.keywords}
assert isinstance(kw["exclude_own_works"], ast.Constant) and kw["exclude_own_works"].value is True
assert kw["grounded_only"].value is True and call.args[0].id == "topic" and kw["k"].value == 5
line = SRC.splitlines()[call.lineno - 1]
assert "_frs = _ar.recall_fragments(topic, k=5, grounded_only=True, exclude_own_works=True)" in line
# it sits inside _author
author = next(n for n in ast.walk(TREE) if isinstance(n, ast.AsyncFunctionDef) and n.name == "_author")
assert author.lineno < call.lineno <= author.end_lineno
import inspect  # noqa: E402
from core import associative_recall as _ar  # noqa: E402
assert "exclude_own_works" in inspect.signature(_ar.recall_fragments).parameters
print("[2] ok: one exclude_own_works call, in _author grounding")

# ---------------------------------------------------------------- [3] J-3196
assert "from core.model_client import call_node_json, call_node_prose\n" in SRC
assert plain_prose.GRAND_WORK_PLAIN_PROSE is True  # D-0823 flip
assert "_plain = bool(_pp.GRAND_WORK_PLAIN_PROSE)" in SRC
assert "_csys = _pp.part_system_prompt(i, title, claim, ct, cs, grounding, prev_tail, _plain)" in SRC
assert 'I am writing part " + str(i) + " of my own work' not in SRC            # moved to core/plain_prose.py
aseg = ast.get_source_segment(SRC, author)
i = aseg.index("if _plain:")
branch = aseg[i:i + 700]
assert "call_node_prose(self.base_urls, _csys" in branch.split("else:")[0]
assert "call_node_json(self.base_urls, _csys" in branch.split("else:")[1]
assert 'ptext = str((cdata or {}).get("part", "")).strip()' in branch
# flag False: byte-identical to the legacy inline expression
grounding = "\n\nWhat you already know of this...\n  - a fragment"
for claim, tail in (("C", "x" * 900), ("", "")):
    legacy = (
        "/no_think\nI am writing part " + str(3) + " of my own work, \"" + "T" + "\" -- the thing "
        "ITSELF, in my own voice, followed through, not notes about it.\n"
        + ("The whole piece builds toward this: " + claim + "\n" if claim else "")
        + "This part -- \"" + "CT" + "\": " + "CS" + grounding
        + (("\n\nWhere the previous part left off (carry it forward; do NOT repeat its conclusions "
            "or restate it):\n" + tail[-700:]) if tail else "")
        + "\nWrite this part IN FULL, 350-550 words, first person, my own voice, no heading. "
          "Output ONLY JSON: {\"part\": \"<the prose>\"}")
    assert plain_prose.part_system_prompt(3, "T", claim, "CT", "CS", grounding, tail, False) == legacy
print("[3] ok: flag False -> JSON path, prompt byte-identical; flag True -> call_node_prose")
print("ALL OK")
