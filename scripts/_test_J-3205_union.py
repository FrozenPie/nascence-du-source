"""J-3205 test: scripts/lab_metaphor_union.py asserts its own tree, builds nothing live.

Runs from the worktree. Synthetic shadow/judge-panel-log files in a temp dir; the panel is exercised
with a monkeypatched `ask` (no HTTP). Nothing under C:\\Nascence is read or written."""
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402,F401  (core BEFORE lab_env, per the lab rules)
try:
    import lab_env  # noqa: E402,F401
except Exception:
    pass  # lab_env lives with the skill; this test never needs isolate() because it writes only to a temp dir

assert Path(core.__file__).resolve().is_relative_to(TREE), core.__file__

spec = importlib.util.spec_from_file_location("lab_union", TREE / "scripts" / "lab_metaphor_union.py")
lu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lu)
assert Path(lu.ROOT).resolve() == TREE.resolve(), (lu.ROOT, TREE)

# ---- prompts: v1 is the production sysmsg (AST), v2 is the J-2212 candidate, and they differ
v1, v2 = lu.production_prompt(), lu.v2_prompt()
assert v1.startswith("You judge whether a short first-person passage uses figurative language")
assert "Output ONLY JSON" in v1 and "Output ONLY JSON" in v2 and v1 != v2

# ---- stats
assert lu.wilson(0, 0) == (None, None)
lo, hi = lu.wilson(6, 8)
assert 40 < lo < 41.5 and 90 < hi < 93.5, (lo, hi)   # F-2955 reported 40.9-92.9 for 6/8
assert lu.pct(1, 4) == 25.0 and lu.pct(0, 0) is None

# ---- passage joins the three fields and caps at 500
t = {"notice": "a" * 300, "uncertain": "b" * 300, "expect_next": "c"}
assert len(lu.passage_of(t)) == 500
assert lu.passage_of({"notice": "x", "uncertain": None, "expect_next": "z"}) == "x  z"

# ---- era loading + join against a synthetic judge_panel_log (log row is AFTER the tick-start ts)
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    base = lu.ERA_START + 1000
    ticks = [
        {"kind": "tick", "model": "deepseek-r1:7b", "ts": base, "notice": "n1", "uncertain": "", "expect_next": "",
         "metaphor_flags": ["journey"], "figurative_flags": [], "metaphor_judged": {"verdict": "metaphor", "how": "tiebreak", "why": "w"}},
        {"kind": "tick", "model": "deepseek-r1:7b", "ts": base + 600, "notice": "n2", "uncertain": "", "expect_next": "",
         "metaphor_flags": [], "figurative_flags": [], "metaphor_judged": {"verdict": "not_sampled", "how": None}},
        {"kind": "tick", "model": None, "ts": base + 700, "notice": "old", "metaphor_judged": {"verdict": "literal", "how": "agreed"}},
        {"kind": "skip", "ts": base + 800},
    ]
    jpl = [{"ts": base + 30, "context": "lane2:metaphor", "verdict": True, "how": "tiebreak", "v1": True, "v2": False, "v3": True},
           {"ts": base + 40, "context": "other", "verdict": False, "how": "agreed"}]
    (td / "s.jsonl").write_text("\n".join(json.dumps(x) for x in ticks), encoding="utf-8")
    (td / "j.jsonl").write_text("\n".join(json.dumps(x) for x in jpl), encoding="utf-8")
    era, _ = lu.load_era(str(td / "s.jsonl"), str(td / "j.jsonl"))
    assert [e["ts"] for e in era] == [base, base + 600], "only deepseek ticks in the era"
    assert era[0]["_stored"]["v3"] is True and era[1]["_stored"] is None

    # ---- panel logic with a fake ask: agree, split->tiebreak, unavailable
    calls = []

    def fake(url, system, user, timeout):
        calls.append(url)
        table = {lu.JUDGE_1: (True, "w1", None, 1.0), lu.JUDGE_2: (False, "w2", None, 1.0),
                 lu.TIEBREAK: (True, "w3", None, 1.0)}
        return table[url]
    lu.ask = fake
    r = lu.panel("SYS", "passage")
    assert r["how"] == "tiebreak" and r["verdict"] is True and r["why"] == "w3" and lu.TIEBREAK in calls
    lu.ask = lambda url, s, u, t: (False, None, None, 1.0)
    r = lu.panel("SYS", "passage")
    assert r["how"] == "agreed" and r["verdict"] is False
    lu.ask = lambda url, s, u, t: (None, None, "timeout", 1.0)
    r = lu.panel("SYS", "passage")
    assert r["how"] == "unavailable" and r["verdict"] is None

    # ---- prf arithmetic
    out = lu.prf({1, 2, 3, 4}, {1, 2, 9}, {1, 2, 3, 4, 9})
    assert out["tp"] == 2 and out["precision_pct"] == 50.0 and abs(out["recall_pct"] - 66.7) < 0.1

# ---- the shipped union file (if built) is internally consistent and holds no unlabelled-source leakage
u = TREE / "docs" / "lab" / "metaphor_union_ticks.jsonl"
if u.exists():
    rows = [json.loads(x) for x in u.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert rows and all("sources" in r and "passage" in r for r in rows)
    assert all((r["in_union"] is True) == ("control_sample" not in r["sources"]) for r in rows)
    sheet = (TREE / "docs" / "lab" / "J-3205_data" / "labelling_sheet.md").read_text(encoding="utf-8")
    for bad in ("kw_metaphor", "kw_figurative", "v1_stored", "flag_arm", "control_sample"):
        assert bad not in sheet, f"blind sheet leaks a mark: {bad}"
print("J-3205 union lab test: OK")
