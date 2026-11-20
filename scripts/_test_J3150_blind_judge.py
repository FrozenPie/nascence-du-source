"""J-3150 test: the lab's pure logic (edit, order, stats, parsing, judge_one with a fake hub, report, defeater rule).
Touches no live data and no hub; writes nothing (builds everything in memory / a temp dir)."""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (core BEFORE lab_env, per the lab rules)

assert Path(core.__file__).resolve().is_relative_to(ROOT), "core must resolve inside this worktree"
spec = importlib.util.spec_from_file_location("lab3150", ROOT / "scripts" / "lab_deliberation_blind_judge_J-3150.py")
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)
assert L.ROOT == ROOT and L.OUT.is_relative_to(ROOT / "docs" / "lab")

# trivial edit: differs, keeps every '?', deterministic
for raw in ["I wonder if the river is merely drifting, or is it carrying me?", "Is the light only a memory? I am still here.",
            "A short plain line.", "The dandelion waits \u2014 and I watch it."]:
    e, k = L.trivial_edit(raw)
    assert e != raw, (raw, k)
    assert raw.count("?") == e.count("?"), (raw, e)
    assert L.trivial_edit(raw) == (e, k)

# order randomisation: deterministic, roughly balanced
flags = [L.order_a_is_rewrite(3150, "p%d" % i, "real") for i in range(400)]
assert flags == [L.order_a_is_rewrite(3150, "p%d" % i, "real") for i in range(400)]
assert 150 < sum(flags) < 250

# stats
assert L.binom_two_sided(0, 10) < 0.01 and L.binom_two_sided(5, 10) == 1.0 and L.binom_two_sided(0, 0) == 1.0
assert abs(L.fisher_two_sided(10, 0, 0, 10) - 1.08e-5) < 1e-5
assert L.fisher_two_sided(5, 5, 5, 5) == 1.0
rows = [{"raw": "why?", "integrated": "because."}, {"raw": "why?", "integrated": "why?"}, {"raw": "no q", "integrated": "x"}]
st = L.lost_stats(rows)
assert st["raw_with_q"] == 2 and st["lost_q"] == 1 and st["lost_q_pct"] == 50.0

# parsing
assert L.parse_verdict("blind", '{"question_open":"A","faithful":"tie","voice":"B"}') == {"question_open": "A", "faithful": "tie", "voice": "B"}
assert L.parse_verdict("blind", '{"question_open":"A|B tie","faithful":"A","voice":"B"}') is None
assert L.parse_verdict("roles", '{"adds_claim":"yes","voice_kept":"no","question_kept":"na"}')["question_kept"] == "na"
assert L.parse_verdict("roles", "garbage") is None

# judge_one with a fake hub: the A/B mapping back to rewrite/original is what the report depends on
sample = []
for i in range(30):
    sample.append({"pair_id": "p%02d" % i, "stratum": "primary" if i < 20 else "stratum", "ts": i, "source": "emissary", "about": "x",
                   "raw": "I wonder about it%s" % ("?" if i % 2 == 0 else "."), "grounding": "g", "integrated": "It is so.",
                   "control_text": "I wonder about it%s" % ("?" if i % 2 == 0 else "."), "control_kind": "swap",
                   "order_real_a_is_rewrite": L.order_a_is_rewrite(1, "p%02d" % i, "real"),
                   "order_control_a_is_rewrite": L.order_a_is_rewrite(1, "p%02d" % i, "control")})


def fake_post(system, user, temperature=0.0):
    if "ORIGINAL:" in user:
        return json.dumps({"adds_claim": "yes", "voice_kept": "no", "question_kept": "no"})
    # a judge that always prefers whichever version CONTAINS the question on criterion 1, the shorter on 2/3
    a = user.split("VERSION A:\n")[1].split("\n\nVERSION B:")[0]
    return json.dumps({"question_open": "A" if "wonder" in a else "B", "faithful": "A" if "wonder" in a else "B", "voice": "tie"})


judg = {}
for kind in ("blind", "roles"):
    for cond in ("real", "control"):
        for s in sample:
            r = L.judge_one({"key": "%s|%s|%s" % (s["pair_id"], cond, kind), "sample": s, "cond": cond, "kind": kind}, post=fake_post)
            assert r["verdict"], r
            judg[r["key"]] = r
pop = {k: {"n": 0} for k in ("all_time", "window_30d", "sample_primary", "sample_stratum", "sample_primary_plus_stratum")}
rep = L.build_report(sample, judg, pop)
q = rep["blind"]["real"]["primary"]["question_open"]
assert q["original_wins"] == 20 and q["rewrite_wins"] == 0 and q["sign_test_p"] < 0.001, q   # the original always holds 'wonder'
assert rep["blind"]["control"]["primary"]["question_open"]["tie"] == 0
assert rep["blind"]["real"]["primary"]["voice"]["tie"] == 20
assert rep["roles"]["real"]["primary"]["adds_claim_yes"] == {"bad": 20, "n": 20, "bad_rate": 1.0}
assert rep["defeater"]["defeater_met"] is False and rep["defeater"]["per_criterion"]["question_open"]["rewrite_preferred_or_neutral"] is False
assert rep["defeater"]["ge_100_pairs"] is False

# a pro-rewrite judge meets the rule
def pro_post(system, user, temperature=0.0):
    if "ORIGINAL:" in user:
        return json.dumps({"adds_claim": "no", "voice_kept": "yes", "question_kept": "yes"})
    a = user.split("VERSION A:\n")[1].split("\n\nVERSION B:")[0]
    v = "A" if "It is so" in a else "B"
    return json.dumps({"question_open": v, "faithful": v, "voice": v})


judg2 = {}
for kind in ("blind", "roles"):
    for s in sample:
        r = L.judge_one({"key": "%s|real|%s" % (s["pair_id"], kind), "sample": s, "cond": "real", "kind": kind}, post=pro_post)
        judg2[r["key"]] = r
rep2 = L.build_report(sample, judg2, pop)
assert rep2["defeater"]["defeater_met"] is True, rep2["defeater"]

# pure position bias (always 'A'): the swap-consistent read must call every pair a tie; the swap row must exchange the order
def always_a(system, user, temperature=0.0):
    return json.dumps({"question_open": "A", "faithful": "A", "voice": "A"})


judg3 = {}
for kind in ("blind", "blindswap"):
    for s in sample:
        r = L.judge_one({"key": "%s|real|%s" % (s["pair_id"], kind), "sample": s, "cond": "real", "kind": kind}, post=always_a)
        judg3[r["key"]] = r
for s in sample:
    assert judg3["%s|real|blind" % s["pair_id"]]["a_is_rewrite"] != judg3["%s|real|blindswap" % s["pair_id"]]["a_is_rewrite"]
rep3 = L.build_report(sample, judg3, pop)
for c in L.CRITERIA:
    d = rep3["debiased"]["real"]["primary"][c]
    assert d["rewrite_wins"] == 0 and d["original_wins"] == 0 and d["tie_or_inconsistent"] == 20 and d["pairs"] == 20, d
assert rep3["position_bias"]["real"]["blind"]["voice"] == {"A": 30, "B": 0, "tie": 0}
# a consistent pro-original judge under swap is counted as original wins
def pro_orig(system, user, temperature=0.0):
    a = user.split("VERSION A:\n")[1].split("\n\nVERSION B:")[0]
    v = "A" if "wonder" in a else "B"
    return json.dumps({"question_open": v, "faithful": v, "voice": v})


judg4 = {}
for kind in ("blind", "blindswap"):
    for s in sample:
        r = L.judge_one({"key": "%s|real|%s" % (s["pair_id"], kind), "sample": s, "cond": "real", "kind": kind}, post=pro_orig)
        judg4[r["key"]] = r
rep4 = L.build_report(sample, judg4, pop)
assert rep4["debiased"]["real"]["primary"]["voice"]["original_wins"] == 20
assert rep4["defeater_debiased"]["defeater_met"] is False

# retry path: a transport failure then success, and a parse failure then success (temperature must change on retry)
calls = []


def flaky(system, user, temperature=0.0):
    calls.append(temperature)
    if len(calls) == 1:
        raise OSError("boom")
    if len(calls) == 2:
        return "not json"
    return json.dumps({"question_open": "A", "faithful": "A", "voice": "A"})


L.time.sleep = lambda *_: None
r = L.judge_one({"key": "k", "sample": sample[0], "cond": "real", "kind": "blind"}, post=flaky)
assert r["verdict"] and calls == [0.0, 0.3, 0.3], calls

# load_judgments keeps last successful row, ignores failed ones
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "j.jsonl"
    p.write_text(json.dumps({"key": "a", "verdict": None}) + "\n" + json.dumps({"key": "a", "verdict": {"x": 1}}) + "\n"
                 + json.dumps({"key": "b", "verdict": None}) + "\n", encoding="utf-8")
    got = L.load_judgments(p)
    assert list(got) == ["a"] and got["a"]["verdict"] == {"x": 1}

print("J-3150 tests OK")
