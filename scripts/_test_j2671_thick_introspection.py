"""J-2671 test: scripts/thick_introspection_read.py on synthetic series (temp dir only, no live data, no model calls)."""
import json
import random
import sys
import tempfile
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402,F401  (core BEFORE lab_env, per the harness rule)
sys.path.insert(0, str(TREE / "scripts"))
import thick_introspection_read as t  # noqa: E402

FAILS = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


rng = random.Random(1)
# 1. an oracle-ish confidence (knows the outcome) must pass the signature; a flat base-rate echo must not.
outcomes = [1.0 if rng.random() < 0.6 else 0.0 for _ in range(140)]
rows_priv = [(float(i), 0.9 if m == 1.0 else 0.1, m) for i, m in enumerate(outcomes)]
res = t.analyse_domain("priv", rows_priv)
check(res["domain_pass_online"] and res["folds_won_online"] >= 4, "privileged confidence wins >= 4/6 folds")
rows_flat = [(float(i), 0.6, m) for i, m in enumerate(outcomes)]
res2 = t.analyse_domain("flat", rows_flat)
check(not res2["domain_pass_online"], "flat base-rate confidence does not pass")
check(res2["n_folds"] == 6, "six folds per domain")

# 2. rivals only see PAST measured values (no look-ahead): row i's rival must equal mean(meas[:i]).
meas = [0.0, 1.0, 1.0, 0.0, 1.0]
rv = t.online_rivals(meas)
check(rv[0] == (0.5, 0.5) and abs(rv[3][0] - 2 / 3) < 1e-9 and abs(rv[4][0] - 0.5) < 1e-9, "online rivals use strictly past values")

# 3. file path end to end on a temp dir: recall-wager domain excluded, short domain skipped, constants give r None.
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    with open(d / "prediction_error_log.jsonl", "w", encoding="utf-8") as fh:
        for i in range(60):
            fh.write(json.dumps({"ts": 1000.0 + i * 1000, "domain": "mathematics", "predicted": 0.8, "measured": float(i % 2), "gap": 0, "large": False}) + "\n")
            fh.write(json.dumps({"ts": 1000.0 + i * 1000, "domain": "factual_recall", "predicted": 0.9, "measured": 0.5, "gap": 0, "large": False}) + "\n")
        for i in range(5):
            fh.write(json.dumps({"ts": 1000.0 + i, "domain": "tiny", "predicted": 0.5, "measured": 0.5, "gap": 0, "large": False}) + "\n")
    (d / "capability_beliefs.json").write_text(json.dumps({"mathematics": {"confidence": 0.8, "accuracy": 0.5, "accuracy_count": 3}}), encoding="utf-8")
    out = d / "out"
    sys.argv = ["x", "--data", str(d), "--out", str(out)]
    r = t.main()
    names = {s["domain"] for s in r["skipped"]}
    check("factual_recall" in names and "tiny" in names, "recall-wager and short domains are skipped")
    check([x["domain"] for x in r["domains"]] == ["mathematics"], "only mathematics analysed")
    check((out / "results.json").exists(), "results.json written under the temp dir")
    check(r["calibration_gap"][0]["gap"] == 0.3, "calibration gap computed")
check(t.pearson([1, 1, 1, 1], [1, 2, 3, 4]) is None, "constant side gives r None, not 0")

# 4. the live data dir was not written by this test
check(not (TREE / "data" / "prediction_error_log.jsonl").exists(), "no live prediction log created in this tree")
print("PASS" if not FAILS else f"{len(FAILS)} FAILED")
sys.exit(1 if FAILS else 0)
