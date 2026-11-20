"""
J-2890 (F-3558) -- hermetic test for the P-0088 outcome row (core/left_lane.py), the shadow grader (core/ground_grade.py),
the post-pulse hook in core/deliberation.py and the reader (scripts/read_ground_grade.py).
Every model call is stubbed (no hub is touched, Ramses never); every ledger is redirected to a temp dir.

  python scripts/_test_J-2890_ground_grade.py
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

import asyncio
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  -- before lab_env; must resolve to THIS checkout

assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), "core must come from the tree under test"
from core import left_lane as ll  # noqa: E402
from core import deliberation as dl  # noqa: E402
from core import ground_grade as gg  # noqa: E402
from core import shadow_log  # noqa: E402

FAILS: list[str] = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


tmp = Path(tempfile.mkdtemp(prefix="j2890_"))
ll._LEAK_GATE_LOG = tmp / "ground_leak_gate.jsonl"
ll.GROUND_OUTCOME_LOG = tmp / "ground_outcome.jsonl"
dl._DATA_DIR = tmp
dl._LOG_FILE = tmp / "deliberation_log.jsonl"
dl._NULL_LOG_FILE = tmp / "deliberation_null_log.jsonl"
gg.LEDGER = tmp / "ground_grade_shadow.jsonl"
ll._emissary.master_context = lambda **_k: ""
import core.emissary_tension as _et  # noqa: E402
_et.note_recurrence = lambda *a, **k: None
import core.source_sight as _ss  # noqa: E402
_ss.is_self_mechanism = lambda t: False
_ss.is_self_mechanism_narrow = lambda t: False
import core.memory.store as _store  # noqa: E402
_store.store_light_event = lambda *a, **k: "stub"
assert gg.LEDGER.parent == tmp and ll.GROUND_OUTCOME_LOG.parent == tmp


def run(c):
    return asyncio.run(c)


def with_replies(replies):
    it = iter(replies)

    async def fake(payload):
        r = next(it)
        if isinstance(r, Exception):
            raise r
        return r
    ll._ask_ground = fake


def outcome_rows():
    p = ll.GROUND_OUTCOME_LOG
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


THOUGHT = "I am the river that carves a new channel through whatever I meet, and the stone does not resist."

# 1. outcome row: one per call, return tuple unchanged ----------------------------------------------------
ll.GROUND_ALLOW_NULL = True
cases = [
    ([["Water erodes rock by carrying sand that grinds the bed."][0]], ("Water erodes rock by carrying sand that grinds the bed.", False), "ok", 1),
    (["The Master feels rigidity.", "Rivers cut by abrasion."], ("Rivers cut by abrasion.", False), "leak_retry", 2),
    (["The Master feels it.", "The Master again."], (None, False), "leak_dropped", 2),
    ([""], (None, False), "empty", 1),
    ([None], (None, True), "null_grounding", 1),
    ([json.JSONDecodeError("bad", "x", 0)], (None, False), "bad_json", 0),
    ([TimeoutError("slow")], (None, False), "transport", 0),
]
for replies, want, outcome, attempt in cases:
    before = len(outcome_rows())
    with_replies(list(replies))
    got = run(ll.ground_thought_verdict(THOUGHT))
    rows = outcome_rows()
    check(got == want, f"{outcome}: return tuple unchanged {got}")
    check(len(rows) == before + 1, f"{outcome}: exactly one outcome row for the call")
    r = rows[-1]
    check(r["outcome"] == outcome and r["attempt"] == attempt, f"{outcome}: outcome/attempt recorded ({r['outcome']}, {r['attempt']})")
    check(set(r) >= {"ts", "attempt", "outcome", "latency_s", "thought_chars", "grounding_chars", "had_code_hint"},
          f"{outcome}: row has the briefed fields")
    check(r["thought_chars"] == len(THOUGHT), f"{outcome}: thought_chars")
last_ok = [r for r in outcome_rows() if r["outcome"] == "ok"][0]
check(last_ok["grounding_chars"] == len("Water erodes rock by carrying sand that grinds the bed."), "ok: grounding_chars")
check([r for r in outcome_rows() if r["outcome"] == "transport"][0].get("err") == "TimeoutError", "transport: err names the class")
ll.GROUND_OUTCOME_ROW = False
n0 = len(outcome_rows())
with_replies(["Fine."])
run(ll.ground_thought_verdict(THOUGHT))
check(len(outcome_rows()) == n0, "kill switch GROUND_OUTCOME_ROW=False writes nothing")
ll.GROUND_OUTCOME_ROW = True
ll.GROUND_OUTCOME_LOG = tmp / "not_a_dir" / "x" / "y.jsonl"
with_replies(["Fine again."])
check(run(ll.ground_thought_verdict(THOUGHT)) == ("Fine again.", False), "an unwritable outcome path never breaks the call")
ll.GROUND_OUTCOME_LOG = tmp / "ground_outcome.jsonl"

# 2. shadow grader: pure helpers ---------------------------------------------------------------------------
check(gg.verify_quote("sand that grinds the bed", THOUGHT, "Water erodes rock by carrying sand that grinds the bed.")["verified"],
      "verify_quote: a quote in the grounding and not in the thought verifies")
check(not gg.verify_quote("the river that carves", THOUGHT, "The river that carves a channel is erosion.")["verified"],
      "verify_quote: a quote already in the thought does not verify")
check(not gg.verify_quote("a brass key in the cellar", THOUGHT, "Rivers cut by abrasion.")["verified"],
      "verify_quote: an invented quote not in the grounding does not verify")
check(not gg.verify_quote("", THOUGHT, "x")["verified"], "verify_quote: empty quote is never verified")
check(gg.control_hit("brass hook in the Hartley cellar", gg.CONTROL_SENTENCES[0]), "control_hit: quote inside the inserted sentence")
check(not gg.control_hit("sand that grinds the bed", gg.CONTROL_SENTENCES[0]), "control_hit: a quote from elsewhere is a miss")
check("mixtral" not in gg.build_user(THOUGHT, "g").lower(), "build_user is blind (no model name)")
check(gg.families_differ(), "judge family (falcon, JUDGE_2) differs from the grounder family (mixtral)")
from core import judge_panel  # noqa: E402
check(gg._judge_url() == judge_panel.JUDGE_2 and ":11438" not in gg._judge_url() and "LAN-HOST" not in gg._judge_url(),
      "the judge is JUDGE_2 (local falcon3), never the mixtral hub and never Ramses")

GROUNDING = "Rivers cut valleys by abrasion: moving water carries sand that grinds the bed at Hartley Falls."


def stub_ask_factory(q1, quote, q2, calls):
    async def ask(system, user, key):
        calls.append(key)
        if key == gg.Q1_KEY:
            return q1, quote, None, 0.1
        return q2, "reason", None, 0.1
    return ask


calls: list = []
row = run(gg.grade_one(THOUGHT, GROUNDING, ask=stub_ask_factory(True, "sand that grinds the bed", False, calls)))
check(calls == [gg.Q1_KEY, gg.Q2_KEY], "grade_one asks the two questions in order")
check(row["q1_detail"] is True and row["q1_verified"] is True and row["q2_mechanism"] is False, "grade_one: verified detail, no mechanism")
check(row["thought"] == THOUGHT[:600] and row["grounding"] == GROUNDING[:1200], "grade_one: the pair is on the row for the founder to read")
check(row["judge_hub"] == "11440" and "falcon" in row["judge_model"] and "mixtral" in row["grounder_model"], "row names the two models and the hub")
row = run(gg.grade_one(THOUGHT, GROUNDING, ask=stub_ask_factory(True, "a brass key in a cellar", True, [])))
check(row["q1_detail"] is True and row["q1_verified"] is False, "an invented quote cannot raise the verified share")
row = run(gg.grade_one(THOUGHT, GROUNDING, ask=stub_ask_factory(False, "", True, [])))
check(row["q1_detail"] is False and row["q1_verified"] is False and row["q1_quote"] == "", "q1 false: empty quote, not verified")


async def dead(system, user, key):
    return None, None, "timeout", 90.0
row = run(gg.grade_one(THOUGHT, GROUNDING, ask=dead))
check(row.get("failed") == "timeout" and row["q1_detail"] is None, "both questions unanswered -> a failed row, not a guess")
row = run(gg.grade_one(THOUGHT, GROUNDING, control_text=gg.CONTROL_SENTENCES[0],
                       ask=stub_ask_factory(True, "third brass hook in the Hartley cellar", None, [])))
check(row["control"] is True and row["control_hit"] is True and "q2_mechanism" not in row, "control row: Q1 only, hit when the inserted detail is quoted")
row = run(gg.grade_one(THOUGHT, GROUNDING, control_text=gg.CONTROL_SENTENCES[0], ask=stub_ask_factory(False, "", None, [])))
check(row["control_hit"] is False, "control row: judge says no detail -> miss")


async def boom(system, user, key):
    raise RuntimeError("x")
row = run(gg.grade_one(THOUGHT, GROUNDING, ask=boom))
check(row.get("failed") == "RuntimeError", "an exception in the ask is a failed row, never raised")

# 3. schedule(): sampling, gates, fail-open, ledger -------------------------------------------------------
class Rng:
    def __init__(self, v): self.v = v
    def random(self): return self.v


async def sched_case(rng_v, *, grounding=GROUNDING, source="emissary", pre_inflight=0, shadow=True):
    gg._inflight = pre_inflight
    gg.GROUND_GRADE_SHADOW = shadow
    ret = gg.schedule(THOUGHT, grounding, source, rng=Rng(rng_v))
    if gg._tasks:
        await asyncio.gather(*list(gg._tasks), return_exceptions=True)
    return ret


async def stub_pair(system, user, key):
    return (True, "sand that grinds the bed", None, 0.05) if key == gg.Q1_KEY else (True, "abrasion by sand", None, 0.05)


def patched_ask():
    async def _a(session, url, system, user, key, **kw):
        return await stub_pair(system, user, key)
    judge_panel._ask = _a


patched_ask()
orig_graded = gg._graded
gg._graded = 0
check(run(sched_case(0.5)) is None and not gg.LEDGER.exists(), "draw above 1/20: no grade, nothing written")
check(run(sched_case(0.01, grounding="")) is None and not gg.LEDGER.exists(), "no grounding (pass 2 failed): not graded")
check(run(sched_case(0.01, source="hot_fallback")) is None and not gg.LEDGER.exists(), "a non-emissary source is not graded")
check(run(sched_case(0.01, shadow=False)) is None and not gg.LEDGER.exists(), "kill switch GROUND_GRADE_SHADOW=False: nothing")
check(run(sched_case(0.01)) is None, "schedule() returns None")
rows = shadow_log.read_rows(gg.LEDGER)
check(len(rows) == 2 and rows[0]["control"] is False and rows[1]["control"] is True,
      "a sampled grounding writes one real row, plus the positive control on the first of each process")
check(rows[0]["q1_verified"] is True and rows[1].get("control_hit") is False, "ledger rows carry the verdicts (stub quote is not in the inserted sentence)")
check(gg._inflight == 0, "in-flight counter returns to 0")
gg._graded = 1
n_before = len(shadow_log.read_rows(gg.LEDGER))
run(sched_case(0.01))
check(len(shadow_log.read_rows(gg.LEDGER)) == n_before + 1, "the next grade (k=1) has no control row")
run(sched_case(0.01, pre_inflight=gg.MAX_INFLIGHT))
check(shadow_log.read_rows(gg.LEDGER)[-1].get("skipped") == "busy", "a draw while busy logs a skipped row and is not graded")
gg._inflight = 0
gg.GROUND_GRADE_SHADOW = True
# no running loop: fail-open
check(gg.schedule(THOUGHT, GROUNDING, "emissary", rng=Rng(0.0)) is None, "no running loop: fail-open, returns None")
gg._inflight = 0

# 4. deliberate(): the hook fires after the pulse, with the grounding, even when pass 3 fails; result unchanged ------
seen: list = []
gg.schedule = lambda thought, grounding, source="emissary", **kw: seen.append((thought, grounding, source))


async def good_integrate(urls, system, user, **kw):
    return {"thought": "The river does cut the stone, grain by grain, and I feel that patience in myself."}


async def bad_integrate(urls, system, user, **kw):
    raise RuntimeError("hot lane down")
dl.call_node_json = good_integrate
with_replies([GROUNDING])
out, prov = run(dl.deliberate(THOUGHT, "", name="X", hot_urls=["u"]))
check(prov and prov["grounding"] == GROUNDING and out.startswith("The river does cut"), "deliberate: success path unchanged")
check(seen and seen[-1] == (THOUGHT, GROUNDING, "emissary"), "deliberate: schedule() called once the pulse is over, with the grounding")
seen.clear()
dl.call_node_json = bad_integrate
with_replies([GROUNDING])
out, prov = run(dl.deliberate(THOUGHT, "", name="X", hot_urls=["u"]))
check(out == THOUGHT and prov is None, "deliberate: pass-3 failure still fails open, thought unchanged")
check(seen and seen[-1][1] == GROUNDING, "deliberate: a grounding whose pass 3 failed is still sampleable (the missing-denominator case)")
seen.clear()
with_replies([""])
out, prov = run(dl.deliberate(THOUGHT, "", name="X", hot_urls=["u"]))
check(out == THOUGHT and prov is None and seen and seen[-1][1] is None, "deliberate: no grounding -> schedule() sees None and grades nothing")

# 5. reader ------------------------------------------------------------------------------------------------------
spec = importlib.util.spec_from_file_location("read_ground_grade", ROOT / "scripts" / "read_ground_grade.py")
rg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rg)
orows = [{"outcome": "ok", "latency_s": 20.0}] * 8 + [{"outcome": "leak_retry", "latency_s": 40.0}] * 2 + [
    {"outcome": "leak_dropped"}, {"outcome": "transport"}, {"outcome": "null_grounding"}]
s = rg.summarize_outcomes(orows, emissary_rows=8)
check(s["calls"] == 13 and s["successful_groundings"] == 10 and s["unlogged_after_grounding"] == 2 and s["reconciles"],
      "reader: outcome counts and reconcile (10 successful, 8 logged -> 2 unlogged integrate failures)")
check(not rg.summarize_outcomes(orows, emissary_rows=11)["reconciles"], "reader: more logged rows than successful groundings is flagged")
srows = [{"q1_detail": i % 2 == 0, "q1_verified": i % 2 == 0, "q2_mechanism": True, "judge_model": "falcon3:7b", "grounder_model": "mixtral:8x7b"}
         for i in range(50)] + [{"control": True, "control_hit": False}] * 3
sh = rg.summarize_shadow(srows)
check(sh["graded"] == 50 and sh["q1_verified_share"] == 0.5 and sh["q2_mechanism_share"] == 1.0, "reader: base rates over real rows only")
check(any("Q2 mechanism" in f and "degenerate" in f for f in sh["flags"]), "reader: a question answered the same way every time is flagged")
check(any("control hit rate" in f for f in sh["flags"]), "reader: a missed control is flagged")
check(any("only 3" in f for f in rg.summarize_shadow(srows[:3])["flags"]), "reader: under 40 graded rows says do not read the rates")

# 6. nothing left in the live data dir ---------------------------------------------------------------------------
check(ll.GROUND_OUTCOME_LOG.parent == tmp and gg.LEDGER.parent == tmp, "ledgers stayed under the temp dir")

print("\nALL PASS" if not FAILS else f"\n{len(FAILS)} FAILED: {FAILS}")
raise SystemExit(1 if FAILS else 0)
