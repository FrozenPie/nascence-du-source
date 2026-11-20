"""J-3314 (D-0671): NodeBase.run_best_of writes one reflection-only shadow row of how much the two hedged drafts agree
(cosine of embeddings), on a background thread; the kept draft is exactly what it was; fail-open; flag-gated; stats()
reads it. Model calls and the embedder are stubbed; the log path points at a temp dir; no live data."""
import asyncio, json, sys, tempfile, time, threading
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core before lab_env)
import numpy as np  # noqa: E402
from core import node_base, hedge_agreement_log as hal, hedge_candidate_log as hcl, node_failure_log as nfl, training_log, schema  # noqa: E402
from core.node_base import NodeBase  # noqa: E402
from core.memory import store  # noqa: E402

assert Path(node_base.__file__).resolve().parent.parent == ROOT, "test must run against its own tree"
assert Path(hal.__file__).resolve().parent.parent == ROOT

tmp = Path(tempfile.mkdtemp(prefix="j3314_"))
hal._LOG = tmp / "agree.jsonl"
hcl._LOG = tmp / "hedge_candidates.jsonl"
nfl._LOG = tmp / "node_failures.jsonl"
for attr in ("_LOG", "_PATH", "LOG_PATH", "_LOG_PATH"):
    if hasattr(training_log, attr):
        setattr(training_log, attr, tmp / "teacher.jsonl")

# stub embedder: identical text -> identical vector (cosine 1.0); different text -> orthogonal vectors
_main_thread = threading.get_ident()
embed_threads = []
def fake_embed(text):
    embed_threads.append(threading.get_ident())
    v = np.zeros(8, dtype=np.float32); v[abs(hash(text)) % 8] = 1.0
    return v
store._embed = fake_embed


class N(NodeBase):
    system_prompt = "sys"
    def _build_prompt(self, state): return "p"
    def _write_output(self, state, data): state.kept = data
    def _score_candidate(self, data):
        d = str(data.get("draft", "")).rstrip()
        return float(len(d)) + (1000.0 if d and d[-1] in '.!?"\'' else 0.0) if d else 0.0

scenario = {}
async def fake(urls, system, prompt, **kw):
    d = scenario["drafts"][0 if kw["temperature"] < 0.5 else 1]
    if isinstance(d, Exception):
        raise d
    return d
node_base.call_node_json = fake

from core.schema import CognitiveState  # noqa: E402
def S():
    st = CognitiveState(spirit_name="t", axiom="a"); st.cycle_id = "cyc-1"; st.input_type = "internal"
    return st

def rows():
    return [json.loads(l) for l in hal._LOG.read_text(encoding="utf-8").splitlines()] if hal._LOG.exists() else []

async def go(node_id="reflection"):
    n = N(node_id); st = S()
    ok = await n.run_best_of(st, 2)
    return ok, getattr(st, "kept", None)

# 1. two identical-text drafts: agreement 1.0, row fields, kept draft unchanged, embed ran OFF the loop thread
same = "A short complete thought."
scenario["drafts"] = [{"draft": same, "confidence": 0.9}, {"draft": same + " Plus more words here.", "confidence": 0.5}]
t0 = time.time()
ok, kept = asyncio.run(go())
call_ms = (time.time() - t0) * 1000
assert ok and kept["draft"].endswith("Plus more words here."), kept       # longest + terminal wins, as before
assert hal.drain(10)
r = rows()
assert len(r) == 1, r
r = r[0]
assert set(r) == {"ts", "cycle_id", "input_type", "n_valid", "agreement", "conf_chosen", "conf_other", "chosen_len", "other_len"}, set(r)
assert r["cycle_id"] == "cyc-1" and r["input_type"] == "internal" and r["n_valid"] == 2
assert r["conf_chosen"] == 0.5 and r["conf_other"] == 0.9
assert r["chosen_len"] > r["other_len"] > 0
assert isinstance(r["agreement"], float) and -1.0001 <= r["agreement"] <= 1.0001
assert embed_threads and all(t != _main_thread for t in embed_threads), "embedding must not run on the caller thread"

# 2. identical drafts -> agreement exactly 1.0
scenario["drafts"] = [{"draft": same, "confidence": 0.7}, {"draft": same, "confidence": 0.7}]
asyncio.run(go()); assert hal.drain(10)
assert rows()[-1]["agreement"] == 1.0, rows()[-1]

# 3. one failed draft -> n_valid 1 -> no agreement row
before = len(rows())
scenario["drafts"] = [{"draft": same}, RuntimeError("boom")]
ok, kept = asyncio.run(go()); assert ok and kept["draft"] == same
hal.drain(10); assert len(rows()) == before

# 4. non-reflection node -> no row
scenario["drafts"] = [{"draft": same}, {"draft": same + " x."}]
asyncio.run(go("executive")); hal.drain(10); assert len(rows()) == before

# 5. flag off -> no row; env-style gate honoured
schema.REFLECTION_HEDGE_AGREEMENT_SHADOW = False
asyncio.run(go()); hal.drain(10); assert len(rows()) == before
schema.REFLECTION_HEDGE_AGREEMENT_SHADOW = True

# 6. embedder raising -> run_best_of still succeeds, row written with agreement null
def bad_embed(text): raise RuntimeError("embedder down")
store._embed = bad_embed
asyncio.run(go()); assert hal.drain(10)
assert rows()[-1]["agreement"] is None and len(rows()) == before + 1

# 7. a write failure (unwritable path) never raises into the cycle
hal._LOG = tmp / "agree.jsonl" / "nested" / "x.jsonl"   # parent is a file -> mkdir fails
ok, kept = asyncio.run(go()); assert ok; hal.drain(10)
hal._LOG = tmp / "agree.jsonl"

# 8. the call path itself is cheap (queueing only; embed stub is instant but this guards against sync blocking work)
assert call_ms < 2000, call_ms

# 9. stats() reader
s = hal.stats(path=hal._LOG)
assert s["rows"] == before + 1 and s["rows_with_agreement"] == before and s["enough"] is False, s
assert s["agreement_median"] is not None and s["last_ts"], s
assert hal.stats(path=tmp / "none.jsonl")["rows"] == 0

# 10. the live data file was never touched
assert not (ROOT / "data" / "reflection_hedge_agreement_shadow.jsonl").exists()
print("J-3314 test OK", s)
