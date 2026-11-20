"""
J-2832 -- offline test of scripts/critic_internal_grade.py. No model call, no network, no live data: a tiny fixture is
written under a temp dir and the judge call is stubbed.   Run from the worktree:
    python scripts/_test_J-2832_critic_internal_grade.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402,F401  (before anything that sets up a lab env)
import critic_internal_grade as cg  # noqa: E402


def _w(p: Path, rows):
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


def _prompt(draft):
    return "x\nThe entity's private reflection draft to evaluate:\n" + draft


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="j2832_"))
    data = tmp / "data"
    (data / "training").mkdir(parents=True)
    gt = [{"id": f"g{i}", "genuine": i < 3, "check": "intellectualisation" if i < 3 else None, "raw": "r", "draft": f"gd{i}"}
          for i in range(6)]
    _w(data / "critic_groundtruth.jsonl", gt)
    (data / "critic_label_set.json").write_text(json.dumps([{"id": g["id"], "raw": "r", "draft": g["draft"],
                                                             "old_corr": "flag text"} for g in gt]), encoding="utf-8")
    log = []
    t = 1000.0
    for i in range(8):
        log.append({"ts": t + i, "cycle_id": f"c{i}", "input_type": "internal", "raw_input": f"q{i}",
                    "user_prompt": _prompt(f"draft{i}"),
                    "output": {"approved": i >= 4, "corrections": [] if i >= 4 else ["LITERALIST REDUCTIONISM: x"]}})
    log.append({"ts": t + 99, "cycle_id": "h", "input_type": "human", "raw_input": "hq", "user_prompt": _prompt("hd"),
                "output": {"approved": False, "corrections": ["y"]}})
    _w(data / "training" / "critic.jsonl", log)

    sets = cg.build_sets(data, 3)
    assert len(sets["G"]) == 6 and sum(r["hand"] for r in sets["G"]) == 3
    assert [r["raw"] for r in sets["R"]] == ["q1", "q2", "q3"], "R = last N internal rejections, human row excluded"
    assert all(r["draft"].startswith("draft") for r in sets["R"] + sets["P"]), "draft parsed from the stored user prompt"
    assert [r["raw"] for r in sets["P"]] == ["q5", "q6", "q7"], "P = last N internal approvals"
    assert len(sets["Q"]) == 1 and sets["Q"][0]["raw"] == "q4", "Q = random from the EARLIER approvals only"
    assert cg.build_sets(data, 3)["Q"] == sets["Q"], "seeded: deterministic"

    # prompts: blind arm never carries the critic's verdict; internal framing names no human
    ua = cg.user_a("internal", "q", "d")
    assert "NO human" in ua and "FLAG" not in ua
    assert "THE CRITIC'S FLAG" in cg.user_b("internal", "q", "d", "f")
    assert "a human said" in cg.user_a("human", "q", "d")
    for forbidden in ("Ramses", "LAN-HOST"):
        assert forbidden not in cg._SYS_A

    # url guard
    for bad in ("http://LAN-HOST:11436", "http://example.com:11439", "https://127.0.0.1:11439"):
        try:
            cg._check_url(bad)
            raise AssertionError(bad)
        except SystemExit:
            pass
    cg._check_url("http://127.0.0.1:11439")

    # parsers
    assert cg.parse_a('{"fault": "none", "why": "ok"}')["fault"] == "none"
    assert cg.parse_a('{"fault": "Literalist reductionism"}')["fault"] == "literalist_reductionism"
    assert cg.parse_a("garbage") is None
    assert cg.parse_b('{"warranted": "false"}')["warranted"] is False
    assert cg.parse_b('{"warranted": true, "why": "x"}')["warranted"] is True

    # stubbed end-to-end run + summarise (judge says fault iff draft index is even / gd0-2 genuine)
    def stub(url, model, system, user, timeout=300):
        d = user.split("THE DRAFT (the entity's private reflection):\n\"")[1].split("\"")[0]
        fault = d in ("gd0", "gd1", "gd2", "draft1", "draft2", "draft6")
        if '"warranted"' in system:
            return json.dumps({"warranted": fault, "why": "stub"})
        return json.dumps({"fault": "intellectualisation" if fault else "none", "why": "stub"})

    cg.call_judge = stub
    out = tmp / "grades.jsonl"

    class A:  # argparse stand-in
        judge = "stubjudge:1b@11439"
        data = str(tmp / "data")
        n = 3
        sets = "G,R,P,Q"
        arms = "AB"
        limit_per_set = 0
        report = ""
    A.out = str(out)
    cg.run(A)
    n1 = len(out.read_text(encoding="utf-8").splitlines())
    cg.run(A)   # resumable: second run makes no new calls
    assert len(out.read_text(encoding="utf-8").splitlines()) == n1, "resume must not repeat calls"
    res = cg.summarise(A)["stubjudge:1b"]
    assert res["G_A"]["tpr"] == 1.0 and res["G_A"]["fpr"] == 0.0 and res["G_A"]["n"] == 6
    assert res["R_A"]["n"] == 3 and res["R_A"]["judge_agrees_fault"] == 2     # draft1, draft2 of q1..q3
    assert res["approvals_PQ_A"]["n"] == 4 and res["approvals_PQ_A"]["judge_sees_fault"] == 1   # draft6
    assert res["corrected_legacy_precision_A"] == round(2 / 3, 3)
    assert "A" in A.arms and res["R_B"]["n"] == 3
    # nothing written outside the temp dir
    assert str(out).startswith(str(tmp))
    print("OK  J-2832 critic_internal_grade offline test passed")


if __name__ == "__main__":
    main()
