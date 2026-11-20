"""J-2805 (F-3445): NodeBase.run_best_of writes one shadow row per hedged run with BOTH drafts (temps, words,
terminal flag, score, winner index), the kept draft is exactly what it was before (the max-score pick), a failed
draft is recorded as invalid, an all-failed run writes no hedge row, the log is fenced/fail-open, and stats()
answers the two job questions. Model calls are stubbed; the log path points at a temp dir; no live data."""
import asyncio, json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core before lab_env)
from core import node_base, hedge_candidate_log as hcl  # noqa: E402
from core.node_base import NodeBase  # noqa: E402
from core.schema import CognitiveState, NODE_REGISTRY  # noqa: E402

assert Path(node_base.__file__).resolve().parent.parent == ROOT, "test must run against its own tree"
assert Path(hcl.__file__).resolve().parent.parent == ROOT

tmp = Path(tempfile.mkdtemp(prefix="j2805_"))
hcl._LOG = tmp / "hedge_candidates.jsonl"
# keep the other shadow writers off the live data dir too
from core import node_failure_log as nfl, training_log  # noqa: E402
nfl._LOG = tmp / "node_failures.jsonl"
for attr in ("_LOG", "_PATH", "LOG_PATH", "_LOG_PATH"):
    if hasattr(training_log, attr):
        setattr(training_log, attr, tmp / "teacher.jsonl")

node_id = next(iter(NODE_REGISTRY))


class N(NodeBase):
    system_prompt = "sys"
    def _build_prompt(self, state):
        return "p"
    def _write_output(self, state, data):
        state.kept = data
    def _score_candidate(self, data):   # Reflection's selector, copied
        draft = str(data.get("draft", "")).rstrip()
        if not draft:
            return 0.0
        return float(len(draft)) + (1000.0 if draft[-1] in '.!?"\'' else 0.0)


SHORT = "A short complete thought."
LONG = " ".join(["word"] * 95) + "."
TRUNC = " ".join(["word"] * 120)   # longest but no terminal punctuation
scenario = {"drafts": []}


async def fake(urls, system, prompt, **kw):
    t = kw["temperature"]
    d = scenario["drafts"][0 if t < 0.5 else 1]
    if isinstance(d, Exception):
        raise d
    return {"draft": d}


node_base.call_node_json = fake
n = N(node_id)
state = CognitiveState(spirit_name="t", axiom="a")
state.cycle_id = "cyc-1"


def rows():
    return [json.loads(l) for l in hcl._LOG.read_text(encoding="utf-8").splitlines()] if hcl._LOG.exists() else []


# 1. second (0.75) draft longer and complete -> wins; both logged
scenario["drafts"] = [SHORT, LONG]
assert asyncio.run(n.run_best_of(state, 2)) is True
assert state.kept["draft"] == LONG                      # same pick as before the instrument
r = rows()[-1]
assert r["node"] == node_id and r["cycle_id"] == "cyc-1" and r["n"] == 2 and r["n_valid"] == 2
assert r["kept_index"] == 1 and r["kept_over_90"] is True and r["shorter_valid_exists"] is True
c0, c1 = r["candidates"]
assert c0["temp"] < c1["temp"] and c0["words"] == 4 and c1["words"] == 95
assert c0["ends_terminal"] and c1["ends_terminal"] and c1["score"] > c0["score"]
assert c1["text"] == LONG and len(c1["text"]) <= hcl.TEXT_CAP

# 2. truncated long draft loses to a clean short one (the +1000 guard)
scenario["drafts"] = [SHORT, TRUNC]
assert asyncio.run(n.run_best_of(state, 2)) is True
assert state.kept["draft"] == SHORT
r = rows()[-1]
assert r["kept_index"] == 0 and r["candidates"][1]["ends_terminal"] is False
assert r["kept_over_90"] is False

# 3. one draft failing -> recorded invalid, kept is the survivor, not "contested"
scenario["drafts"] = [ValueError("boom"), LONG]
assert asyncio.run(n.run_best_of(state, 2)) is True
r = rows()[-1]
assert r["n_valid"] == 1 and r["kept_index"] == 1 and r["candidates"][0]["valid"] is False
assert "boom" in r["candidates"][0]["err"] and r["shorter_valid_exists"] is False

# 4. all failed -> False and no hedge row
before = len(rows())
scenario["drafts"] = [ValueError("a"), ValueError("b")]
assert asyncio.run(n.run_best_of(state, 2)) is False
assert len(rows()) == before

# 5. text cap
scenario["drafts"] = ["x" * 5000 + ".", SHORT]
asyncio.run(n.run_best_of(state, 2))
assert len(rows()[-1]["candidates"][0]["text"]) == hcl.TEXT_CAP

# 6. fail-open: an unwritable path (a directory) must not break the run or change the pick
hcl._LOG = tmp   # a directory: open(..., "a") raises
scenario["drafts"] = [SHORT, LONG]
assert asyncio.run(n.run_best_of(state, 2)) is True and state.kept["draft"] == LONG
hcl._LOG = tmp / "hedge_candidates.jsonl"

# 7. stats answers the two questions
s = hcl.stats(path=hcl._LOG)
assert s["rows"] == 4 and s["contested_rows"] == 3 and s["enough"] is False
assert s["wins_by_index"] == {"1": 1, "0": 2} or s["wins_by_index"] == {"0": 2, "1": 1}, s
assert s["second_index_win_rate"] == round(1 / 3, 3), s
assert s["kept_over_90"] == 2 and s["kept_over_90_shorter_valid"] == 1, s
assert hcl.stats(path=tmp / "nope.jsonl")["rows"] == 0
assert hcl.stats(since_ts=9e12, path=hcl._LOG)["rows"] == 0
# 30 contested rows flips `enough`
for _ in range(30):
    hcl.log_hedged(node_id, temps=[0.35, 0.75], results=[{"draft": SHORT}, {"draft": LONG}], best={"draft": LONG}, scorer=len)
# `best` above is not an identity match -> kept_index None -> skipped by stats, so identity must hold:
a, b = {"draft": SHORT}, {"draft": LONG}
for _ in range(30):
    hcl.log_hedged(node_id, temps=[0.35, 0.75], results=[a, b], best=b, scorer=len)
assert hcl.stats(path=hcl._LOG)["enough"] is True

# 8. disabled flag writes nothing
hcl._ENABLED = False
sz = hcl._LOG.stat().st_size
asyncio.run(n.run_best_of(state, 2))
assert hcl._LOG.stat().st_size == sz

# 9. du_pulse wiring is present
assert "hedge_candidates" in (ROOT / "scripts" / "du_pulse.py").read_text(encoding="utf-8")
print("J-2805 hedge candidate log: all assertions passed")
