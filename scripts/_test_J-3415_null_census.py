"""J-3415 test: the null-rate census computes what it says on synthetic logs, touches nothing live,
and the prompt audit file is complete and self-consistent.

Run from the worktree:  python scripts/_test_J-3415_null_census.py
Writes only under a temp dir; the census is run as a subprocess pointed at a synthetic data dir.
"""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
assert (ROOT / "scripts" / "lab_J-3415_null_rate_census.py").exists(), "wrong tree"
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL:", msg)
    else:
        print("ok:  ", msg)


def jl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


# ---- 1. census on a synthetic data dir -------------------------------------------------------------
_baseline = ROOT / "docs" / "lab" / "J-3415_data" / "null_rates.json"
_baseline_mtime = _baseline.stat().st_mtime if _baseline.exists() else None
old = time.mktime((2026, 8, 1, 0, 0, 0, 0, 0, -1))
new = time.mktime((2026, 10, 15, 0, 0, 0, 0, 0, -1))
with tempfile.TemporaryDirectory() as td:
    data = Path(td) / "data"
    # recall: 10 rows, 1 empty tensions (old) ; 4 rows since boot, 0 empty
    rows = [{"ts": old, "input_type": "internal", "output": {"tensions": [] if i == 0 else ["a"]}} for i in range(6)]
    rows += [{"ts": new, "input_type": "human", "output": {"tensions": ["a", "b"]}} for _ in range(4)]
    jl(data / "training" / "recall.jsonl", rows)
    # episodic buffer: 5 rows since boot, 2 empty dissonance
    jl(data / "training" / "episodic_buffer.jsonl",
       [{"ts": new, "input_type": "internal", "output": {"dissonance": [] if i < 2 else ["x"]}} for i in range(5)])
    # consolidation: 4 rows, 1 null, 1 empty-string, 1 missing key (ignored), 1 real
    jl(data / "training" / "consolidation.jsonl", [
        {"ts": new, "output": {"wisdom_extracted": None}},
        {"ts": new, "output": {"wisdom_extracted": ""}},
        {"ts": new, "output": {"memories_processed": 3}},
        {"ts": new, "output": {"wisdom_extracted": "a real one"}},
    ])
    # critic: 3 approved, 1 rejected, plus a non-dict output (ignored)
    jl(data / "training" / "critic.jsonl", [
        {"ts": new, "input_type": "human", "output": {"approved": True}},
        {"ts": new, "input_type": "human", "output": {"approved": True}},
        {"ts": new, "input_type": "internal", "output": {"approved": True}},
        {"ts": new, "input_type": "internal", "output": {"approved": False}},
        {"ts": new, "output": "garbage"},
    ])
    jl(data / "training" / "curiosity.jsonl", [{"ts": new, "output": {"questions": ["q"]}}])
    jl(data / "training" / "executive.jsonl", [
        {"ts": new, "output": {"response_type": "silence", "should_respond": False}},
        {"ts": new, "output": {"response_type": "answer", "should_respond": True}},
    ])
    jl(data / "self_interrogation_shadow.jsonl", [
        {"kind": "interrogate", "reflection": "I am clinging to this because it is comfortable", "genuine": True},
        {"kind": "interrogate", "reflection": "It holds up, I trust it as it stands", "genuine": False},
        {"kind": "skip", "skip": "cooldown"},
    ])
    jl(data / "self_implication_shadow.jsonl", [
        {"fires": False, "A": False}, {"fires": True, "A": True}, {"cycle": "no fires key"},
    ])
    jl(data / "refinery_shadow.jsonl", [
        {"insight": "x", "accepted": True, "fidelity": 0.9}, {"insight": "y", "accepted": False, "fidelity": 0.2},
    ])
    out = Path(td) / "out" / "r.json"
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "lab_J-3415_null_rate_census.py"), str(data), str(out)],
                       capture_output=True, text=True, encoding="utf-8")
    check(p.returncode == 0, f"census exits 0 (stderr: {p.stderr[-200:]!r})")
    rep = json.loads(out.read_text(encoding="utf-8"))
    n = rep["nodes"]
    check(n["recall"]["windows"]["all"]["any"] == {"n": 10, "null": 1, "rate": 0.1}, "recall all-window 1 of 10")
    check(n["recall"]["windows"]["since_0925"]["any"]["n"] == 4 and n["recall"]["windows"]["since_0925"]["any"]["null"] == 0,
          "recall since-boot window 0 of 4")
    check(n["episodic_buffer"]["windows"]["all"]["any"]["null"] == 2, "episodic buffer 2 empty dissonance")
    check(n["consolidation"]["windows"]["all"]["any"] == {"n": 3, "null": 2, "rate": 0.6667},
          "consolidation: missing key row excluded, null and empty string counted")
    check(n["critic"]["windows"]["all"]["any"]["n"] == 4 and n["critic"]["windows"]["all"]["any"]["null"] == 3,
          "critic: approve counts as null-use, non-dict output excluded")
    check(n["critic"]["windows"]["all"]["human"]["null"] == 2 and n["critic"]["windows"]["all"]["internal"]["null"] == 1,
          "critic split by input_type")
    check(n["curiosity"]["windows"]["all"]["any"]["null"] == 0, "curiosity zero nulls")
    check(n["executive"]["windows"]["all"]["any"] == {"n": 2, "null": 1, "rate": 0.5}, "executive silence counts as null")
    check(rep["other"]["self_interrogation"]["n"] == 2 and rep["other"]["self_interrogation"]["judge_genuine"] == 1,
          "self-interrogation counts only kind=interrogate")
    check(rep["other"]["self_implication_thought_scan"] == {"n": 2, "fires": 1, "A": 1}, "self-implication scan counts rows with a fires key")
    check(rep["other"]["refinery_shadow"]["fidelity_under_0.5"] == 1 and rep["other"]["refinery_shadow"]["n"] == 2, "refinery counters")
    check(_baseline_mtime == (_baseline.stat().st_mtime if _baseline.exists() else None),
          "the synthetic run left the committed baseline report untouched")

# ---- 2. the audit file ------------------------------------------------------------------------------
audit = json.loads((ROOT / "docs" / "lab" / "J-3415_data" / "prompt_audit.json").read_text(encoding="utf-8"))
reg_ids = [json.loads(l)["id"] for l in open(ROOT / "docs" / "prompt_registry.jsonl", encoding="utf-8") if l.strip()]
# J-4052: the audit is a point-in-time artifact (registry rows up to P-0123 existed when J-3415 ran); rows registered
# since (P-0124+) are new prompts the audit never saw, not gaps in it.
want = {i for i in reg_ids if int(i.split("-")[1]) <= 123} | {f"P-{i:04d}" for i in range(113, 124)}
have = set(audit["per_prompt"])
check(not (want - have), f"every registry row classified (missing: {sorted(want - have)[:5]})")
check(not (have - want), f"no unknown ids classified (extra: {sorted(have - want)[:5]})")
check(set(audit["per_prompt"].values()) <= set(audit["class_legend"]), "every class code is in the legend")
ranks = [g["rank"] for g in audit["groups_ranked"]]
check(ranks == list(range(1, len(ranks) + 1)), "group ranks are 1..n in order")
bad = [(g["rank"], pid) for g in audit["groups_ranked"] for pid in g["prompts"] if pid not in have]
check(not bad, f"every prompt id in a group exists ({bad[:3]})")
for pid in audit["exemplars_with_admissible_null"]:
    if audit["per_prompt"].get(pid) not in ("G", "GU"):
        check(False, f"exemplar {pid} is classed G/GU (is {audit['per_prompt'].get(pid)})")
check(len(audit["ledger"]["findings"]) == 8 and len(audit["ledger"]["jobs_spawned"]) == 6, "ledger ids listed")
check(all(g.get("finding") for g in audit["groups_ranked"]), "every group names a finding")

print("\nALL PASS" if not fails else f"\n{len(fails)} FAILED")
sys.exit(1 if fails else 0)
