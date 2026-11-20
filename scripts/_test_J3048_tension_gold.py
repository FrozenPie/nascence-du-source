"""J-3048: offline test of the tension-resolution gold-set tooling. Temp dir only, no model call, no live data write.
Asserts its own tree, stubs judge_panel._ask, checks the live prompt is reproduced verbatim, the variants, the join helpers,
the scorer and the panel composition rule."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402,F401  (import core before anything that patches it)
from core import judge_panel as jp  # noqa: E402
import j3048_tension_gold_build as build  # noqa: E402
import j3048_tension_gold_replay as rp  # noqa: E402
import j3048_tension_gold_report as rep  # noqa: E402

assert (ROOT / "core" / "tension_ledger.py").exists() and ROOT.name != "Nascence"

# 1. V0 is the live prompt in core/tension_ledger._judge_resolution, byte for byte
src = (ROOT / "core" / "tension_ledger.py").read_text(encoding="utf-8")
live_frag = ["You are a strict resolution judge for an internal tension ledger. A tension is ",
             "RESOLVED only if the thought states a genuine settlement, synthesis, decision, or ",
             "answer that addresses the tension's actual conflict. A thought that merely mentions ",
             "the same topic, restates the tension in new words, poses a question, or describes a ",
             "feeling (fatigue, pressure, ache) does NOT resolve it. When uncertain, answer false. ",
             "Output ONLY valid JSON: {\"resolves\": true|false, \"why\": \"<one short clause>\"}"]
assert all(f in src for f in live_frag)
assert "".join(live_frag[:5]) + 'Output ONLY valid JSON: {"resolves": true|false, "why": "<one short clause>"}' == rp.SYS_LIVE
assert 'f"TENSION: {label[:200]}\\n\\nTHOUGHT: {thought[:600]}\\n\\nDoes the thought resolve the tension?"' in src
assert '"resolves"' in src and "GRANITE_CONSTANT_TIEBREAK_KEYS" in (ROOT / "core" / "judge_panel.py").read_text(encoding="utf-8")
assert "resolves" in jp.GRANITE_CONSTANT_TIEBREAK_KEYS

# 2. variants
r = {"label": "unresolved: asking the library", "thought": "T" * 700,
     "events": [{"text": "A" * 300}, {"text": "B"}, {"text": "C"}, {"text": "D"}]}
u0, u1, u2, u3 = (rp.user_for(v, r) for v in rp.VARIANTS)
assert u0 == "TENSION: unresolved: asking the library\n\nTHOUGHT: " + "T" * 600 + "\n\nDoes the thought resolve the tension?"
assert u1.startswith("TENSION: asking the library\n") and "unresolved" not in u1
assert "WHAT FORMED THE TENSION" not in u0 and "WHAT FORMED THE TENSION" not in u1
assert u2.startswith("TENSION: unresolved: asking the library") and u2.count("\n- ") == 3 and "- " + "A" * 200 + "\n" in u2
assert "D" not in u2.split("WHAT FORMED")[1].replace("Does the thought resolve the tension?", "").replace("FORMED", "").replace("THE", "")
assert u3.startswith("TENSION: asking the library") and "WHAT FORMED THE TENSION" in u3 and u3.endswith("resolve the tension?")
assert rp.strip_prefix("unresolved dream: the confrontation") == "the confrontation"
assert rp.strip_prefix("Mottainai and design") == "Mottainai and design"
assert rp.user_for("V2", {"label": "x", "thought": "t", "events": []}).count("WHAT FORMED") == 0

# 3. build helpers (the matcher's own token guard; about extraction)
assert build.passes_gate("the rain on the thyme", "thyme", "unresolved: the thyme patch")       # shared about token
assert not build.passes_gate("a cat sleeps", "cat", "unresolved: the library")                   # no overlap at all
assert build.passes_gate("library shelves hold the quiet", "", "unresolved: library shelves")    # two thought tokens
assert build.about_of("(idle thought about: sea glass)") == "sea glass" and build.about_of("x") == ""
pairs = [{"tension_id": "a", "panel": {"verdict": False}}] * 5 + [{"tension_id": "b", "panel": {"verdict": False}},
                                                                   {"tension_id": "c", "panel": {"verdict": True}}]
pk = build.pick_refuted(pairs, 10, 1)
assert sorted(p["tension_id"] for p in pk) == ["a", "a", "b"] and all(p["source"] == "refuted" for p in pk)
assert "panel" not in build.blind_text({"gid": "T001", "label": "l", "thought": "t", "events": [{"text": "e"}]}).lower()

# 4. gold set committed in the worktree is well-formed
gold = rp.load_gold()
assert len(gold) == 120 and {g["source"] for g in gold} == {"closure", "refuted"}
assert {g["gold"] for g in gold} <= {"S", "R", "U"} and sum(g["source"] == "closure" for g in gold) == 60
assert all(len(g["events"]) >= 1 for g in gold) and len({g["gid"] for g in gold}) == 120

# 5. rule_detail composes the two seats exactly as the report's panel arm does (stub _ask; scratch _LOG)
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    jp._LOG, jp._DATA = d / "jp.jsonl", d
    answers = {}

    async def fake_ask(session, url, system, user, key, timeout=0, num_predict=0):
        return answers[url], "w", None, 0.1

    orig = jp._ask
    jp._ask = fake_ask
    try:
        for a1, a2, exp in [(True, True, (True, "agreed")), (False, False, (False, "agreed")),
                            (True, False, (None, "split_no_tiebreak")), (False, True, (None, "split_no_tiebreak"))]:
            answers[jp.JUDGE_1], answers[jp.JUDGE_2], answers[jp.TIEBREAK] = a1, a2, True
            out = asyncio.run(jp.rule_detail("s", "u", "resolves"))
            assert (out["verdict"], out["how"]) == exp, (a1, a2, out)
    finally:
        jp._ask = orig
    assert (d / "jp.jsonl").exists()

# 6. report: panel composition, scorer, flips
gl = {f"T{i:03d}": {"label": lab, "unsure": False} for i, lab in enumerate("SSRRUU", 1)}
src_of = {"T001": "closure", "T002": "refuted", "T003": "closure", "T004": "refuted", "T005": "closure", "T006": "refuted"}


def rows(hub, v, vals):
    return [{"gid": f"T{i:03d}", "variant": v, "hub": hub, "v": x, "secs": 1.0, "prompt_chars": 100} for i, x in enumerate(vals, 1)]


vm = rep.verdicts({"gemma": rows("gemma", "V0", [True, True, True, False, None, False]),
                   "falcon": rows("falcon", "V0", [True, False, True, False, True, False])})
pm = vm[("panel", "V0")]
assert [pm[f"T{i:03d}"] for i in range(1, 7)] == [True, None, True, False, None, False]
s = rep.score(pm, gl, src_of)
assert (s["tp"], s["fp"], s["fn"], s["tn"], s["no_verdict"]) == (1, 1, 0, 2, 2), s
assert s["closure_pass"] == (2, 2) and s["refuted_pass"] == (0, 2)
assert abs(rep.kappa(1, 1, 0, 2) - 0.5) < 1e-9
lo, hi = rep.wilson(5, 10)
assert 0.23 < lo < 0.25 and 0.75 < hi < 0.77
assert rep.flips({"a": True, "b": True, "c": False}, {"a": False, "b": True, "c": True}, {"a": {"label": "R"}, "b": {"label": "S"}, "c": {"label": "S"}}) == (1, 0, 1, 0)
print("J-3048 test OK")
