"""
J-3164 test: the Salience-ablation lab script's pure parts (prompt arms, deterministic urgency, stats).
No model call, no live data, writes only under a temp dir.   python scripts/_test_J3164_salience_ablation.py
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core BEFORE lab_env, per the lab rules; this test needs no isolate(), it writes nothing under data/)

spec = importlib.util.spec_from_file_location("lab_sal", ROOT / "scripts" / "lab_salience_ablation_J3164.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

assert lab.ROOT == ROOT, (lab.ROOT, ROOT)
ok = 0


def check(cond, msg):
    global ok
    assert cond, msg
    ok += 1


UP = ("Axiom: x\n\nInput\n\nPerception: p [statement]\nEmotion: joy\n"
      "Salience: urgency is pressing, focus=[a, b]\n"
      "Attention (your own focus, monitored): I am attending to a, b — drawn by urgency (something pressing); my attentional bandwidth is narrowed.\n"
      "  — Attention has circled this repeatedly. You may deliberately redirect it if a truer concern is calling beneath the fixation.\n"
      "WHAT YOU RECALL (...):\nmem\nReflection: r\nCritic: approved (high confidence)")
row = {"user_prompt": UP, "det_word": "moderate"}

check(lab.make_prompt(row, "A1") == UP and lab.make_prompt(row, "A2") == UP, "A arms are byte-identical to the log")
b = lab.make_prompt(row, "B")
check("Salience:" not in b and "Attention (your own focus" in b and b.count("\n") == UP.count("\n") - 1, "B removes exactly the Salience line")
u = lab.make_prompt(row, "U")
check("Salience: urgency is moderate, focus=[a, b]" in u and u.replace("moderate", "pressing", 1) == UP, "U changes only the urgency word")
c = lab.make_prompt(row, "C")
check("Salience:" not in c and "Attention" not in c and "circled" not in c and "Critic: approved" in c and "WHAT YOU RECALL" in c,
      "C removes Salience + Attention + the fixation line and nothing else")

check(lab.det_urgency("internal", "why is the sky blue", None)[0] == "low", "internal -> low")
check(lab.det_urgency("human", "hello", None)[0] == "moderate", "human -> moderate")
check(lab.det_urgency("human", "I need this done urgently", None)[0] == "high", "time pressure -> high")
check(lab.det_urgency("human", "we are going to pause for a while now", None)[0] == "moderate", "bare 'now' is not time pressure")
check(lab.det_urgency("human", "hello", "fail_call")[0] == "high", "correction -> high")
check(lab.det_urgency("human", "right now! quickly", "factual_wrong")[0] == "pressing", "both -> pressing")

# stats: Fisher on [[8,2],[1,9]] two-sided = 0.005477 (the standard textbook value)
check(abs(lab._fisher(8, 2, 1, 9) - 0.0054775) < 5e-5, lab._fisher(8, 2, 1, 9))
check(abs(lab._binom_two_sided(0, 10) - 2 / 1024) < 1e-9, "two-sided binomial tail")
check(lab._binom_two_sided(5, 10) == 1.0, "symmetric centre is 1")
lo, hi = lab._wilson(5, 10)
check(0.23 < lo < 0.25 and 0.75 < hi < 0.77, (lo, hi))

# parse + cap
check(lab._parse('{"a":1}') == {"a": 1} and lab._parse('noise {"a":2} tail') == {"a": 2} and lab._parse("zzz") is None, "parse")
big = "x" * 30000
cap = lab._cap_prompt(big)
check(len(cap) < len(big) and "[...context truncated...]" in cap and lab._cap_prompt("short") == "short", "cap")

# the script never targets a live path for writing: every _append goes under DATA inside this tree
check(str(lab.DATA).startswith(str(ROOT)), lab.DATA)
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "t.jsonl"
    lab._append(p, {"k": "v渡"})
    check(lab._read_jsonl(p) == [{"k": "v渡"}], "jsonl roundtrip")

print(f"ALL OK ({ok} checks)")
