"""
_test_J3050_tension_judge_attempts.py -- proving test for J-3050 (F-3757, P-0103): every tension-judge call is appended
to its own log (data/tension_judge_attempts.jsonl), separate from the subconscious save that overwrites
`resolution_attempts`. Run from the worktree:  python scripts/_test_J3050_tension_judge_attempts.py

Stubbed judge + stubbed embedder, tempdir state and log; no live data, no model call, no Ramses call.
Checks: refuted / unavailable / confirmed each write exactly one row with the spec fields; a later overwrite of the
state file's resolution_attempts leaves the log intact; verdict logic unchanged (refuted/unavailable -> None and the
tension stays unresolved; confirmed -> resolved); fail-open (unwritable log path, kill switch) never changes the
return value; size rotation; reader counts.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import core  # noqa: E402,F401  (core BEFORE lab_env)
from core import tension_ledger as tl  # noqa: E402

assert Path(tl.__file__).resolve().parent.parent == ROOT, "test must load the worktree's own core"

FAILS = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="j3050_"))
    state = tmp / "subconscious_state.json"
    log = tmp / "tension_judge_attempts.jsonl"
    tl._ATTEMPTS_LOG = log
    vec = [0.1] * 384
    tension = {"id": "T-aaa", "label": "the weight of possibility", "centroid": vec}

    def write_state():
        import copy
        state.write_text(json.dumps({"tensions": [copy.deepcopy(tension)]}), encoding="utf-8")

    thought = "The weight of possibility is settled: I decide to act on the first option. " * 3

    def run(verdict):
        async def fake_judge(t, lbl):
            return verdict
        tl._judge_resolution = fake_judge
        write_state()
        return asyncio.run(tl.check_and_resolve_internal_tension(
            thought, about="possibility weight", vec=vec, cycle_id="c1", state_path=state))

    r = run(False)
    check("refuted -> None (verdict logic unchanged)", r is None)
    st = json.loads(state.read_text(encoding="utf-8"))["tensions"][0]
    check("refuted -> tension stays unresolved", not st.get("resolved"))
    r = run(None)
    check("unavailable -> None", r is None)
    r = run(True)
    check("confirmed -> resolved dict returned", isinstance(r, dict) and r.get("resolved") is True)

    rows = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    check("three calls -> three rows", len(rows) == 3)
    check("verdicts in order", [x["verdict"] for x in rows] == ["refuted", "unavailable", "confirmed"])
    need = {"ts", "tension_id", "label", "thought", "sim", "verdict"}
    check("spec fields present", all(need <= set(x) for x in rows))
    check("tension_id / label carried", rows[0]["tension_id"] == "T-aaa" and rows[0]["label"].startswith("the weight"))
    check("thought capped at 300", all(len(x["thought"]) <= 300 for x in rows))
    check("sim is a float ~1.0", all(isinstance(x["sim"], float) and x["sim"] > 0.99 for x in rows))

    # the subconscious save overwriting the state file's resolution_attempts must not touch the log
    write_state()
    check("state overwrite leaves the log intact", len(log.read_text(encoding="utf-8").splitlines()) == 3)

    s = tl.judge_attempts_stats(path=log)
    check("reader counts", s["rows"] == 3 and s["refuted"] == 1 and s["unavailable"] == 1 and s["confirmed"] == 1)
    check("reader: absent file -> zeros", tl.judge_attempts_stats(path=tmp / "nope.jsonl")["rows"] == 0)

    # fail-open: unwritable log path (a directory), and the kill switch
    tl._ATTEMPTS_LOG = tmp
    r = run(True)
    check("unwritable log path never changes the result", isinstance(r, dict) and r.get("resolved") is True)
    tl._ATTEMPTS_LOG = log
    os.environ["NASCENCE_TENSION_JUDGE_ATTEMPTS_LOG"] = "0"
    n = len(log.read_text(encoding="utf-8").splitlines())
    run(False)
    check("kill switch writes nothing", len(log.read_text(encoding="utf-8").splitlines()) == n)
    del os.environ["NASCENCE_TENSION_JUDGE_ATTEMPTS_LOG"]

    # bounded: past the cap the file rotates once to .1 and a fresh file starts
    tl._ATTEMPTS_MAX_BYTES = 100
    run(False)
    check("rotation produced .1 and a fresh log", log.with_name(log.name + ".1").exists()
          and len(log.read_text(encoding="utf-8").splitlines()) == 1)

    print("\nFAILED: %s" % FAILS if FAILS else "\nALL PASS")
    sys.exit(1 if FAILS else 0)


main()
