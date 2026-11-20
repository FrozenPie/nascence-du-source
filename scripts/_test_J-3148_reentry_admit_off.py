"""J-3148 test (D-0540): within-cycle re-entry Phase 1 admission is OFF and no human cycle awaits a settle.

Runs from the worktree. Asserts its own tree. Writes only to a temp dir (reentry._LOG/_STATE are pointed
there); stubs every model call and the embedder; touches no live data and no hub."""
import ast
import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402,F401  (core BEFORE lab_env, per the lab rules)
try:
    import lab_env  # noqa: E402,F401
except Exception:
    pass

assert Path(core.__file__).resolve().is_relative_to(TREE), core.__file__
from core import reentry  # noqa: E402
assert Path(reentry.__file__).resolve().is_relative_to(TREE), reentry.__file__

# ---- 1. the flag is off
assert reentry.REENTRY_ADMIT is False, reentry.REENTRY_ADMIT

# ---- 2. static: in the orchestrator, every AWAITED _reentry_shadow call is inside `if _re.REENTRY_ADMIT:` body,
# and the else branch schedules it with asyncio.create_task (fire-and-forget). So off => nothing awaited.
src = (TREE / "core" / "orchestrator.py").read_text(encoding="utf-8")
tree = ast.parse(src)


def _is_shadow_call(n):
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "_reentry_shadow")


def _is_admit_test(n):
    return isinstance(n, ast.Attribute) and n.attr == "REENTRY_ADMIT"


awaited, scheduled = [], []
parents = {}
for node in ast.walk(tree):
    for ch in ast.iter_child_nodes(node):
        parents[ch] = node
for node in ast.walk(tree):
    if isinstance(node, ast.Await) and _is_shadow_call(node.value):
        awaited.append(node)
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "create_task"
            and node.args and _is_shadow_call(node.args[0])):
        scheduled.append(node)
assert len(awaited) == 1 and len(scheduled) == 1, (len(awaited), len(scheduled))


def _branch_of(node):
    """Return (if_node, 'body'|'orelse') for the nearest enclosing `if REENTRY_ADMIT` of node, else None."""
    child, cur = node, parents.get(node)
    while cur is not None:
        if isinstance(cur, ast.If) and _is_admit_test(cur.test):
            return cur, ("body" if any(child is b or _contains(b, child) for b in cur.body) else "orelse")
        child, cur = cur, parents.get(cur)
    return None


def _contains(root, target):
    return any(n is target for n in ast.walk(root))


a = _branch_of(awaited[0])
s = _branch_of(scheduled[0])
assert a and a[1] == "body", "the awaited settle must live only under `if REENTRY_ADMIT:`"
assert s and s[1] == "orelse", "the fire-and-forget settle must be the else branch"
assert a[0] is s[0], "both calls belong to the same REENTRY_ADMIT switch"

# ---- 3. behaviour: settle_shadow still runs, still logs a settle row (the shadow keeps accruing) and returns
# the record; the caller (admission off) ignores settled_full. All stubs, temp dir.
tmp = Path(tempfile.mkdtemp(prefix="J-3148_"))
reentry._DATA = tmp
reentry._LOG = tmp / "reentry_shadow.jsonl"
reentry._STATE = tmp / "reentry_state.json"


def _vec(text):
    # deterministic toy embedding: bag of 8 hashed buckets, normalised
    import numpy as np
    v = np.zeros(8, dtype="float32")
    for w in text.lower().split():
        v[hash(w) % 8] += 1.0
    n = float((v ** 2).sum()) ** 0.5 or 1.0
    return v / n


calls = {"revise": 0}


async def _revise(prompt):
    calls["revise"] += 1
    await asyncio.sleep(0.05)
    return "A rewritten thought about doors and rivers that moves somewhere quite different today"


def _retrieve(q):
    return ["a standing contradiction about lamps and weather and bread and distant salt marshes"]


draft = "I keep returning to the same quiet idea about thresholds and what it costs to cross them."
t0 = time.time()
rec = asyncio.run(reentry.settle_shadow(draft, "principle-voiced", revise=_revise, retrieve=_retrieve,
                                        embed=_vec, basin=None))
assert rec and rec.get("passes", 0) >= 1 and "settled_full" in rec, rec
assert calls["revise"] >= 1
rows = reentry._LOG.read_text(encoding="utf-8").strip().splitlines()
assert len(rows) == 1 and '"passes"' in rows[0], rows
_row = json.loads(rows[0]); assert _row.get("settled_full") == rec["settled_full"] and _row.get("admitted") is False, "J-3018: full settled text + admitted flag now logged (admission off -> admitted False)"

# ---- 4. with the flag off the caller's decision (to_post) is the FIRST draft whatever the record says:
# mirror the orchestrator's else-branch arithmetic on the real record.
to_post = draft
if reentry.REENTRY_ADMIT:
    if rec.get("would_admit_settled") and rec.get("settled_full"):
        to_post = rec["settled_full"]
assert to_post == draft

print("J-3148 OK: REENTRY_ADMIT False; awaited settle only under the flag; else branch create_task; "
      "settle still logs; first draft is what broadcasts (%.2fs)" % (time.time() - t0))
