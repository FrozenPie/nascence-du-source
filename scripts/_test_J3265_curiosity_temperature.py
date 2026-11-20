"""J-3265: offline tests for scripts/lab_curiosity_temperature.py (pure metrics + pre-registered verdict logic).

No model call, no live data: every file goes under a temp dir. Run from the worktree:
    python scripts/_test_J3265_curiosity_temperature.py
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402  (BEFORE lab_env / anything else)
assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__

import lab_curiosity_temperature as L  # noqa: E402


def test_metrics():
    a = "What did Napoleon's court reflect about the politics of the time?"
    b = "What did Napoleon's court reflect about the politics of the era?"
    c = "How did tidal erosion shape the shoreline of the bay?"
    assert L.jaccard(L.tokens(a), L.tokens(a)) == 1.0
    assert L.jaccard(L.tokens(a), L.tokens(b)) > L.TOK_JACCARD_DUP
    assert L.jaccard(L.tokens(a), L.tokens(c)) < 0.2
    nd = L.is_near_dup(b, [c, a])
    assert nd["dup_tok"] and nd["dup_tri"], nd
    nd = L.is_near_dup(c, [a, b])
    assert not nd["dup_tok"] and not nd["dup_tri"], nd
    assert L.is_near_dup("anything", []) == {"tok_sim": 0.0, "tri_sim": 0.0, "dup_tok": False, "dup_tri": False}
    assert L.trigrams("one two") == set()


def test_pools():
    rows = [{"output": {"questions": [f"q{j}a", f"q{j}b"]}} for j in range(8)]
    rows[3]["output"] = {"questions": []}
    assert L.prev_pool(rows, 7) == ["q2a", "q2b", "q4a", "q4b", "q5a", "q5b", "q6a", "q6b"]
    assert L.prev_first(rows, 7) == ["q2a", "q4a", "q5a", "q6a"]
    assert L.as_questions({"questions": ["x ", {"question": "y"}, ""]}) == ["x", "y"]
    assert L.as_questions(None) == []


def test_verdict():
    ok = L.verdict_for(0.5, {"base": 0.5, "arm": 0.2}, {"base": 0.6, "arm": 0.3}, {"base": 3.0, "arm": 3.0})
    assert ok["worth_proposing"] and ok["near_dup_falls_by_third_on_both"] and ok["specificity_not_fall"]
    # falls on one metric only -> not proposed
    one = L.verdict_for(0.5, {"base": 0.5, "arm": 0.2}, {"base": 0.6, "arm": 0.55}, {"base": 3.0, "arm": 3.2})
    assert not one["worth_proposing"] and not one["near_dup_falls_by_third_on_both"]
    # specificity falls beyond the margin -> not proposed
    sp = L.verdict_for(0.5, {"base": 0.5, "arm": 0.2}, {"base": 0.6, "arm": 0.3}, {"base": 3.0, "arm": 2.8})
    assert not sp["worth_proposing"] and not sp["specificity_not_fall"]
    # within-margin dip is not a fall
    mg = L.verdict_for(0.5, {"base": 0.5, "arm": 0.2}, {"base": 0.6, "arm": 0.3}, {"base": 3.0, "arm": 2.95})
    assert mg["worth_proposing"]
    # exactly one third on both counts as "at least a third"
    th = L.verdict_for(0.35, {"base": 0.6, "arm": 0.4}, {"base": 0.3, "arm": 0.2}, {"base": 3.0, "arm": 3.0})
    assert th["near_dup_falls_by_third_on_both"], th
    # zero baseline cannot pass
    z = L.verdict_for(0.5, {"base": 0.0, "arm": 0.0}, {"base": 0.0, "arm": 0.0}, {"base": 3.0, "arm": 3.0})
    assert not z["worth_proposing"]


def test_bootstrap_and_json_helpers():
    d = L.paired_bootstrap([1, 2, 3, 4], [2, 3, 4, 5])
    assert abs(d["mean"] - 1.0) < 1e-9 and d["lo"] == d["hi"] == 1.0 and d["n"] == 4
    assert L.paired_bootstrap([], [])["n"] == 0
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "x.jsonl"
        L.append_jsonl(p, {"a": "渡"})
        L.append_jsonl(p, {"a": 2})
        assert [r["a"] for r in L.read_jsonl(p)] == ["渡", 2]
        assert L.read_jsonl(Path(td) / "missing.jsonl") == []


def test_select_and_baseline_on_synthetic_log():
    """A synthetic log, a temp out dir: select + baseline write only under --out and never touch data/."""
    import argparse
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "cur.jsonl"
        sysp = "SYS"
        for i in range(40):
            up = f"Entity: x\n\nRecent themes:\n  - t{i}\n\nRecently studied or read - ask:\n  - (S) snippet {i // 3}\n\nUnresolved\n\nGenerate questions and research directions worth exploring next."
            L.append_jsonl(src, {"ts": i, "cycle_id": str(i), "input_type": "internal", "system_prompt": sysp, "user_prompt": up,
                                 "output": {"questions": [f"what is snippet {i // 3} about today", "second"], "urgency": 0.3}})
        out = td / "out"
        a = argparse.Namespace(src=str(src), window=40, out=str(out), seed=1, n=12)
        L.cmd_select(a)
        ins = L.read_jsonl(out / "inputs.jsonl")
        assert len(ins) == 12 and all(len(r["prev_pool"]) > 0 for r in ins)
        assert all(r["idx"] >= L.PREV_K for r in ins)
        L.cmd_baseline(a)
        b = json.loads((out / "baseline.json").read_text(encoding="utf-8"))
        assert b["scored"] == 35 and b["dup_tok"] > 0
        assert b["dup_tok_rate_when_same_study"] is not None
        # the lab never wrote anywhere but out
        assert sorted(p.name for p in out.iterdir()) == ["baseline.json", "inputs.jsonl"]


def test_report_pipeline_without_model():
    """Hand-built gen + judge files -> report: checks the arm/verdict plumbing end to end."""
    import argparse
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        qs_prev = ["What drove the Directory against Napoleon at Acre?"]
        for idx in (10, 11, 12):
            L.append_jsonl(out / "inputs.jsonl", {"idx": idx, "ts": 0, "cycle_id": "c", "input_type": "internal", "system_prompt": "s",
                                                  "user_prompt": "Entity: x", "logged_questions": qs_prev, "logged_urgency": 0.3,
                                                  "prev_pool": qs_prev, "prev_first": qs_prev, "same_study_as_prev": idx == 11})
            for t in L.TEMPS:
                for s in range(L.SAMPLES):
                    q = qs_prev[0] if t == 0.2 else f"Which casualty figures at Acre disagree, sample {s} row {idx} at {t}?"
                    L.append_jsonl(out / "gen.jsonl", {"idx": idx, "temp": t, "sample": s, "ok": True, "err": None, "secs": 1.0,
                                                       "questions": [q], "directions": [], "urgency": 0.3})
                    L.append_jsonl(out / "judge_falcon.jsonl", {"idx": idx, "temp": t, "sample": s, "ok": True, "novelty": 3.0,
                                                                "specificity": 3.0, "answerable": 1.0, "secs": 1.0})
        a = argparse.Namespace(out=str(out), judge_samples="0,1,2", seed=1)
        L.cmd_report(a)
        r = json.loads((out / "report.json").read_text(encoding="utf-8"))
        assert r["rows_complete_all_arms"] == 3
        assert r["arms_mechanical"]["0.2"]["dup_tok_rate"] == 1.0
        assert r["arms_mechanical"]["0.5"]["dup_tok_rate"] == 0.0
        v = r["preregistered_verdict"]["falcon@0.5"]
        assert v["worth_proposing"] is True, v
        assert r["arms_mechanical"]["0.2"]["within_row_pairs_dup_tri_rate"] == 1.0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("ALL OK")
