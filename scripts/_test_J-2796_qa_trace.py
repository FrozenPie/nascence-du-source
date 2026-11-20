"""J-2796: self-test for scripts/j2796_qa_evidence_trace.py (split_qa, resolve_verdicts, end-to-end on a temp tree).
Writes only under a temp dir; touches no live data."""
import importlib.util, json, sqlite3, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
assert (ROOT / "core" / "evidence_recall.py").exists(), ROOT
sys.path.insert(0, str(ROOT))
import core  # noqa: F401,E402  (before lab_env)
spec = importlib.util.spec_from_file_location("j2796", ROOT / "scripts" / "j2796_qa_evidence_trace.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

assert m.split_qa("Q: why?\nA: because") == ("why?", "because")
assert m.split_qa("plain text") == (None, None)

ask = {"ts": 100.0, "secs": 5, "question": "Is the cat's indifference a gift or an insult?",
       "judged": [{"fragment_id": "a", "v1": True, "v2": True, "how": "agreed"},
                  {"fragment_id": "b", "v1": False, "v2": True, "how": "tiebreak"},
                  {"fragment_id": "c", "v1": False, "v2": False, "how": "unavailable"}]}
ctx = "evidence:" + ask["question"][:40]
panel = [{"ts": 102.0, "context": ctx, "v1": False, "v2": True, "how": "tiebreak", "verdict": True},
         {"ts": 102.0, "context": "evidence:other", "v1": False, "v2": True, "how": "tiebreak", "verdict": False}]
assert m.resolve_verdicts(ask, panel) == [True, True, None], m.resolve_verdicts(ask, panel)
panel2 = panel + [{"ts": 103.0, "context": ctx, "v1": False, "v2": True, "how": "tiebreak", "verdict": False}]
assert m.resolve_verdicts(ask, panel2)[1] == "ambiguous"

with tempfile.TemporaryDirectory() as td:
    nd = Path(td); (nd / "data" / "memory").mkdir(parents=True)
    now = 1793000000.0
    c = sqlite3.connect(nd / "data" / "memory" / "nascence.db")
    c.execute("CREATE TABLE memory_fragments (fragment_id TEXT, content TEXT, origin TEXT, timestamp REAL)")
    c.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?)", [
        ("a", "Q: hello travis words\nA: my reply", "lived", now),
        ("t", "[Travis said to me] hello travis words", "lived", now),
        ("b", "Q: my own idle prompt\nA: my reply", "lived", now),
        ("r", "a reading fragment", "reading", now)])
    c.commit(); c.close()
    ev = [{"ts": now + 1, "question": "carried question text here", "n_candidates": 3, "outcome": "found", "n_returned": 2,
           "secs": 1.0, "source": "follow_line", "train_id": "t1",
           "judged": [{"fragment_id": "a", "origin": "lived", "sim": 0.6, "v1": True, "v2": True, "how": "agreed"},
                      {"fragment_id": "b", "origin": "lived", "sim": 0.6, "v1": True, "v2": True, "how": "agreed"},
                      {"fragment_id": "r", "origin": "reading", "sim": 0.6, "v1": True, "v2": True, "how": "agreed"}]}]
    (nd / "data" / "evidence_log.jsonl").write_text("\n".join(json.dumps(r) for r in ev), encoding="utf-8")
    (nd / "data" / "judge_panel_log.jsonl").write_text("", encoding="utf-8")
    out = Path(td) / "out"
    sys.argv = ["x", "--since", "2026-01-01", "--nascence", str(nd), "--out", str(out), "--sample", "0"]
    m.main()
    d = json.loads((out / "qa_pass_rows.json").read_text(encoding="utf-8"))
    t = d["tally"]
    assert t["qa_pass"] == 2 and t["qa_pass_human_asked"] == 1 and t["qa_pass_internal_asked"] == 1 and t["nonqa_pass"] == 1, t
print("OK _test_J-2796_qa_trace")
