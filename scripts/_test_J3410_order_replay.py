"""J-3410 test: the option-order control replay, the site census and the judge-skew reader.

No network, no live data: ask() is stubbed, outputs go to a temp dir, the live judge_panel_log is replaced by synthetic
rows. Run from the worktree:  python scripts/_test_J3410_order_replay.py
"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789/J-3583: no write to the tree's data/
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402  (BEFORE the lab modules)

assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__

import lab_j3410_order_replay as L  # noqa: E402
import lab_j3410_judge_skew as S  # noqa: E402
import lab_j3410_site_census as C  # noqa: E402

fails = []


def check(name, cond):
    if not cond:
        fails.append(name)
    print(("ok   " if cond else "FAIL ") + name)


# --- reverse_order ---------------------------------------------------------------------------------------------
pipe = 'Output ONLY JSON: {"held": true|false, "why": "<one short clause>"}'
orr = 'Output ONLY a JSON object: {"same_lesson": <true or false>, "why": "x"}.'
pair = 'Answer ONLY JSON: {"supported": true} or {"supported": false}.'
pre = 'Schema: {"resolved": true, "why": "one sentence"}'
none = "Decide the relation. Output ONLY a JSON object with a number."
check("pipe reversed", L.reverse_order(pipe) == 'Output ONLY JSON: {"held": false|true, "why": "<one short clause>"}')
check("or-placeholder reversed", "<false or true>" in L.reverse_order(orr))
check("literal pair swapped", L.reverse_order(pair) == 'Answer ONLY JSON: {"supported": false} or {"supported": true}.')
check("prefilled literal flipped", L.reverse_order(pre) == 'Schema: {"resolved": false, "why": "one sentence"}')
check("no form is unchanged", L.reverse_order(none) == none)
for s in (pipe, orr, pair, pre):
    check("reverse twice is identity: " + s[:30], L.reverse_order(L.reverse_order(s)) == s)
check("first_listed pipe", L.first_listed(pipe) is True and L.first_listed(L.reverse_order(pipe)) is False)
check("first_listed pair", L.first_listed(pair) is True and L.first_listed(L.reverse_order(pair)) is False)
check("first_listed none", L.first_listed(none) is None)
check("hubs never Ramses", not any("LAN-HOST" in u for u in L.HUBS.values()))
try:
    L.ask("http://LAN-HOST:11438", "s", "u", "k")
    check("ask refuses Ramses", False)
except AssertionError:
    check("ask refuses Ramses", True)

# --- real production prompts are captured (no network) --------------------------------------------------------
cases = L.build_cases(limit_per=3)
stations = {c["station"] for c in cases}
check("three pilot stations captured", stations == {"P-0117 same_lesson", "P-0109 held", "P-0110 metaphor"})
check("every captured system prompt has a reversible form", all(L.reverse_order(c["system"]) != c["system"] for c in cases))
check("captured keys are the production keys", {c["key"] for c in cases} == {"same_lesson", "held", "metaphor"})
check("interleaved: first three cases are three different stations", len({c["station"] for c in cases[:3]}) == 3)
check("labels present on same_lesson", any(c["label"] is True for c in L.build_cases(limit_per=60) if c["station"] == "P-0117 same_lesson"))

# --- run() resumes and report() maths, with a stub ask --------------------------------------------------------
calls = []


def stub(url, system, user, key, **kw):
    calls.append(1)
    # a "first-option biased" judge: always says whatever the schema lists first
    return L.first_listed(system), None, 0.01


with tempfile.TemporaryDirectory() as td:
    out = Path(td) / "runs.jsonl"
    n1 = L.run(out, ["falcon3"], cases, ask_fn=stub)
    check("run asked 2 per case", n1 == 2 * len(cases) and len(calls) == n1)
    n2 = L.run(out, ["falcon3"], cases, ask_fn=stub)
    check("run resumes without repeating", n2 == 0)
    rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    rep = L.report(rows)
    r = next(iter(rep.values()))
    check("pure first-option judge: first_listed_sum == 2.0", r["first_listed_sum"] == 2.0)
    check("pure first-option judge flips every verdict (T->F)", r["flip_rate"] == 1.0 and r["flips_T_to_F"] == r["n_pairs"])
    check("no write outside temp", not (ROOT / "runs.jsonl").exists())

    def content(url, system, user, key, **kw):
        return len(user) % 2 == 0, None, 0.01   # depends only on the case, never on the order

    out2 = Path(td) / "runs2.jsonl"
    L.run(out2, ["gemma4"], cases, ask_fn=content)
    rep2 = L.report([json.loads(x) for x in out2.read_text(encoding="utf-8").splitlines()])
    r2 = next(iter(rep2.values()))
    check("order-blind judge: zero flips, sum == 1.0", r2["flip_rate"] == 0.0 and r2["first_listed_sum"] == 1.0 and r2["mcnemar_p"] == 1.0)
check("mcnemar exact: 10 vs 0 is significant", L._mcnemar_p(10, 0) < 0.01)
check("mcnemar exact: 5 vs 5 is not", L._mcnemar_p(5, 5) == 1.0)

# --- judge-skew reader on synthetic rows ---------------------------------------------------------------------
syn = [{"key": "k", "context": "a:1", "v1": True, "v2": False, "verdict": True, "hub1": "11438", "hub2": "11440", "hub3": None, "how": "tiebreak"},
       {"key": "k", "context": "a:2", "v1": True, "v2": True, "verdict": True, "hub1": "11438", "hub2": "11440", "hub3": None, "how": "agreed"},
       {"key": "k", "context": "b:3", "v1": False, "v2": True, "verdict": False, "hub1": "11438", "hub2": "11440", "hub3": None, "how": "tiebreak"}]
res = S.summarise(S.measure(syn))
check("skew splits key by context prefix", set(res) == {"k@a", "k@b"})
check("skew counts", res["k@a"]["n"] == 2 and res["k@a"]["v1_true"] == 1.0 and res["k@a"]["v2_true"] == 0.5 and res["k@a"]["split_v1T_v2F"] == 1)

# --- site census: BOM files are parsed (lane2.py begins with a BOM) -----------------------------------------
sites = C.walk(ROOT)
have = {(s["file"], s["key"], s["form"]) for s in sites}
check("census sees lane2 held bool_pipe (BOM file)", ("core/lane2.py", "held", "bool_pipe") in have)
check("census sees the pre-filled assimilate example", ("core/guidance_learning.py", "relation", "prefilled_word") in have)
check("census sees the same_lesson placeholder", ("core/guidance_learning.py", "same_lesson", "bool_or") in have)
check("census sees follow_line literal pair", ("core/follow_line.py", "cuts", "bool_pair") in have)
check("census sees the executive 6-way enum", ("nodes/executive_node.py", "response_type", "enum_pipe") in have)

print("\nFAILED: %s" % fails if fails else "\nALL OK")
sys.exit(1 if fails else 0)
