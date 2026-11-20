"""J-3128 test (P-0104): the second ('seeded') active-imagination shadow judge and its auditable log.

Runs from the worktree. Asserts its own tree. Writes only to a temp dir (both shadow log paths are pointed there); stubs
core.judge_panel.rule_detail (no hub is called); touches no live data."""
import ast
import asyncio
import inspect
import json
import sys
import tempfile
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402,F401  (core BEFORE lab_env, per the lab rules)
try:
    import lab_env  # noqa: E402,F401
except Exception:
    pass

assert Path(core.__file__).resolve().is_relative_to(TREE), core.__file__
from core import judge_panel as jp  # noqa: E402
from core import shadow_log as sl  # noqa: E402
from nodes import subconscious_node as sn  # noqa: E402
assert Path(sn.__file__).resolve().is_relative_to(TREE), sn.__file__

# ---- 1. new log is a different file; the old one is unchanged
assert sn._AI_JUDGE_LOG.name == "active_imagination_judge_shadow.jsonl", sn._AI_JUDGE_LOG
assert sn._AI_JUDGE_V2_LOG.name == "active_imagination_judge_v2_shadow.jsonl", sn._AI_JUDGE_V2_LOG
assert sn._AI_JUDGE_V2_LOG != sn._AI_JUDGE_LOG

# ---- 2. prompt shape: observable question, the 'seeded' bool key, a 'why' that carries the quote, false-on-doubt
s = sn._AI_JUDGE_V2_SYSTEM
assert "PLACEHOLDER" not in s and len(s) > 300, s[:80]
assert '"seeded"' in s and '"why"' in s, s
assert "uncertain" in s.lower() and "false" in s.lower()

# ---- 3. static: the v2 call sits under `if _AI_JUDGE_V2_ON:` and the first call is still awaited unconditionally
src = inspect.getsource(sn.SubconsciousNode._active_imagination)
tree = ast.parse("class _X:\n" + "\n".join("    " + l for l in src.splitlines()))
guarded, bare_v2, old_calls = 0, 0, 0
for node in ast.walk(tree):
    if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "_AI_JUDGE_V2_ON":
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute) and sub.attr == "_judge_active_imagination_seeded":
                guarded += 1
    if isinstance(node, ast.Attribute) and node.attr == "_judge_active_imagination_novelty":
        old_calls += 1
total_v2 = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "_judge_active_imagination_seeded")
assert guarded == 1 and total_v2 == 1, (guarded, total_v2)
assert old_calls == 1
# nothing that decides what is kept reads a v2 verdict
assert "_AI_JUDGE_V2_LOG" not in src
assert "importance   = _imp" in src.replace("importance   = _imp,", "importance   = _imp")

# ---- 4. quote check (mechanical)
q = sn._quoted_phrase_in_entry
entry = "[Active imagination] I stand where the paper burns and the brush weeps."
assert q("the paper burns, and the BRUSH weeps", entry) is True
assert q("a library burning from the inside out", entry) is False
assert q("none", entry) is None and q("", entry) is None and q(None, entry) is None and q(3, entry) is None

# ---- 5. rows: v2 is auditable without a join, old row shape unchanged
tmp = Path(tempfile.mkdtemp(prefix="j3128_"))
sn._AI_JUDGE_V2_LOG = tmp / "v2.jsonl"
sn._AI_JUDGE_LOG = tmp / "v1.jsonl"
calls = []


async def fake_rule_detail(system, user, key, context="", **kw):
    calls.append((key, context, system, user))
    return {"verdict": True, "how": "agreed", "v1": True, "v2": True, "why1": "the paper burns", "why2": "brush weeps",
            "why3": None, "why": "the paper burns"}

_orig_rule_detail = jp.rule_detail
jp.rule_detail = fake_rule_detail
long_entry = "[Active imagination] " + ("x" * 900)
node = sn.SubconsciousNode.__new__(sn.SubconsciousNode)
asyncio.run(node._judge_active_imagination_seeded("unresolved: paper", "tension", entry, 0.5912))
asyncio.run(node._judge_active_imagination_seeded("unresolved: long", "curiosity", long_entry, 0.6))
asyncio.run(node._judge_active_imagination_novelty("unresolved: paper", "tension", entry, 0.5912))
assert [c[0] for c in calls] == ["seeded", "seeded", "genuine"], calls
assert calls[0][1] == "active_imagination_seeded" and calls[2][1] == "active_imagination_novelty"
assert calls[0][2] == sn._AI_JUDGE_V2_SYSTEM and calls[0][3].startswith("Seed (tension): unresolved: paper\n\nEntry:\n[Active")

rows = [json.loads(l) for l in (tmp / "v2.jsonl").read_text(encoding="utf-8").splitlines()]
assert len(rows) == 2
r = rows[0]
for k in ("ts", "prompt", "kind", "seed", "entry", "kept_importance", "verdict", "how", "v1", "v2", "why1", "why2",
          "phrase_ok1", "phrase_ok2"):
    assert k in r, k
assert r["entry"] == entry[:400] and r["kept_importance"] == 0.5912 and r["why1"] == "the paper burns"
assert r["phrase_ok1"] is True and r["phrase_ok2"] is True
assert len(rows[1]["entry"]) == 400 and rows[1]["phrase_ok1"] is False

old = [json.loads(l) for l in (tmp / "v1.jsonl").read_text(encoding="utf-8").splitlines()]
assert len(old) == 1 and set(old[0]) == {"ts", "kind", "seed", "mechanical_importance", "judge_verdict", "judge_how", "v1", "v2"}, set(old[0])

# ---- 6. fail-open: a raising judge never propagates
async def boom(*a, **k):
    raise RuntimeError("hub down")

jp.rule_detail = boom
asyncio.run(node._judge_active_imagination_seeded("s", "tension", entry, 0.5))
assert len(sl.read_rows(sn._AI_JUDGE_V2_LOG)) == 2

# ---- 7. reader
st = sn.active_imagination_judge_v2_status()
assert st["graded"] == 2 and st["seeded_true"] == 2 and st["seeded_false"] == 0 and st["true_with_quote_not_in_entry"] == 1, st
assert st["importance_mean_true"] == round((0.5912 + 0.6) / 2, 4), st
sn._AI_JUDGE_V2_LOG = tmp / "absent.jsonl"
assert sn.active_imagination_judge_v2_status() == {"graded": 0}

# ---- 8. the shared judge module and the shadow log helper are untouched by this job (this file asserts only that they still
# expose what the v2 call uses)
assert "why1" in inspect.getsource(_orig_rule_detail) and hasattr(sl, "append") and hasattr(sl, "read_rows")

print("ALL OK J-3128 (flag _AI_JUDGE_V2_ON=%s)" % sn._AI_JUDGE_V2_ON)
