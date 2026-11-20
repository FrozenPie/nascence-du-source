"""J-2076 (F-2689): a verdict that lands on a no-output skip row also carries the second-ask evidence.
Hermetic: temp data dir, stubbed _judge_prior and _ask. Run: python scripts/test_lane2_skip_row_second_ask_evidence.py"""
import asyncio, json, sys, tempfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import lane2  # noqa: E402
from core import lane2_break_habituation as _hab  # noqa: E402
from core import telemetry as _t  # noqa: E402
assert str(Path(lane2.__file__).resolve()).startswith(str(ROOT)), lane2.__file__
TMP = Path(tempfile.mkdtemp(prefix="j2076_lane2_"))
lane2._DATA = TMP; lane2._LOG = TMP / "lane2_shadow.jsonl"; lane2._STATE = TMP / "lane2_store.json"
lane2._HINTS = TMP / "lane2_hints.json"; lane2._LOG_WONDER = TMP / "lane2_would_ask.jsonl"
_t.log_llm_call = lambda *a, **k: None
_hab.phase1_metric_sheet = lambda: None
P = {"available": ["world"], "missing": [], "run": 2, "world": {"place": "study", "standpoint": "at_the_desk"},
     "standpoint": "at_the_desk", "world_fields": ["place", "standpoint"]}
lane2.gather_percepts = lambda: dict(P)
lane2.read_weather = lambda: {"valence": None, "arousal": None, "unresolved": None}
async def _ask(payload): return ({}, 1.0, "empty")
lane2._ask = _ask
async def _judge(expect, percepts, *_a, **_k):   # J-3099 added age_s, horizon, pred_place
    return {"verdict": "broke", "how": "confirmed", "why": "J-why", "contradicted_how": "clear",
            "contradicted_why": "C-why"}
lane2._judge_prior = _judge
now = time.time()
lane2._save_store({"factual": [], "prediction": [{"expect": "the lamp stays on", "horizon": "next",
    "ts": now - 500, "due_ts": now - 10, "standpoint": "at_the_desk", "place": "study", "verdict": None}]})
asyncio.run(lane2.tick())
rows = [json.loads(l) for l in open(lane2._LOG, encoding="utf-8") if l.strip()]
r = rows[-1]
bad = []
def chk(n, c):
    print("PASS" if c else "FAIL", "-", n)
    if not c: bad.append(n)
chk("no-output skip row", r.get("skip") == "no-output")
chk("old keys kept", r.get("prior_verdict") == "broke" and r.get("prior_judged_how") == "confirmed"
    and r.get("judged_expect") == "the lamp stays on")
chk("prior_judged_why", r.get("prior_judged_why") == "J-why")
chk("prior_contradicted_how/why", r.get("prior_contradicted_how") == "clear" and r.get("prior_contradicted_why") == "C-why")
chk("prior_judgeability", r.get("prior_judgeability") == "matched-standpoint")
chk("judged_age_s ~500", isinstance(r.get("judged_age_s"), float) and 490 < r["judged_age_s"] < 520)
chk("percept_lines present", isinstance(r.get("percept_lines"), str) and len(r["percept_lines"]) <= 600)
# no due prediction -> row unchanged (no new keys)
lane2._save_store({"factual": [], "prediction": []})
asyncio.run(lane2.tick())
r2 = [json.loads(l) for l in open(lane2._LOG, encoding="utf-8") if l.strip()][-1]
chk("no-due skip row has none of the new keys", not ({"prior_judged_why", "prior_contradicted_how",
    "prior_judgeability", "judged_age_s", "percept_lines"} & set(r2)))
sys.exit(1 if bad else 0)
