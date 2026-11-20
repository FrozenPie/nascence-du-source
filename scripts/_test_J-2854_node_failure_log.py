"""J-2854 (F-3525): NodeBase writes one append-only failure row per failed node call (additive, fail-open),
the cause classes are right, the return value of a failure is unchanged (False), du_pulse's reader counts
the rows, and the human-cycle tier-0 flag is default-off (no `tier` kwarg unless flipped).
Model calls are stubbed; the log path points at a temp dir; no live data is touched."""
import asyncio, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core before lab_env)
from core import node_base, node_failure_log as nfl  # noqa: E402
from core.node_base import NodeBase  # noqa: E402
from core.schema import CognitiveState, NODE_REGISTRY  # noqa: E402

assert Path(node_base.__file__).resolve().parent.parent == ROOT, "test must run against its own tree"

tmp = Path(tempfile.mkdtemp(prefix="j2854_"))
nfl._LOG = tmp / "node_failures.jsonl"

node_id = next(iter(NODE_REGISTRY))


class N(NodeBase):
    system_prompt = "sys"
    mode = "ok"
    def _build_prompt(self, state):
        if self.mode == "build":
            raise KeyError("boom")
        return "p"
    def _write_output(self, state, data):
        if self.mode == "write":
            raise TypeError("float() argument must be a string or a real number, not 'dict'")
        state.scratch = data


seen = {}
async def fake_ok(urls, system, prompt, **kw):
    seen.clear(); seen.update(kw)
    return {"a": 1}
async def fake_empty(urls, system, prompt, **kw):
    raise ValueError("all servers exhausted ['x']: ValueError(\"No JSON object found in response: ''\")")
async def fake_parse(urls, system, prompt, **kw):
    raise ValueError("all servers exhausted ['x']: JSONDecodeError('Expecting value')")
async def fake_transport(urls, system, prompt, **kw):
    raise ValueError("all servers exhausted ['x']: TimeoutError()")

state = CognitiveState(spirit_name="t", axiom="a")
state.input_type = "human"
n = N(node_id)

# 1. success writes no row, passes no tier kwarg with the flag off
node_base.call_node_json = fake_ok
assert asyncio.run(n.run(state)) is True
assert "tier" not in seen, seen
assert not nfl._LOG.exists()

# 2. each cause class -> one row, return value still False
cases = [("build", None, "code_bug"), ("write", fake_ok, "code_bug"),
         ("call", fake_empty, "empty_content"), ("call", fake_parse, "parse"),
         ("call", fake_transport, "transport")]
for mode, fake, want in cases:
    n.mode = mode if mode != "call" else "ok"
    node_base.call_node_json = fake or fake_ok
    assert asyncio.run(n.run(state)) is False
rows = [__import__("json").loads(x) for x in nfl._LOG.read_text(encoding="utf-8").splitlines()]
assert [r["cause"] for r in rows] == [c[2] for c in cases], rows
assert [r["stage"] for r in rows] == ["build", "write", "call", "call", "call"], rows
assert all(r["node"] == node_id and r["cycle_id"] == state.cycle_id and r["input_type"] == "human" for r in rows)

# 3. hedged path logs too
node_base.call_node_json = fake_transport
n.mode = "ok"
assert asyncio.run(n.run_best_of(state, 2)) is False
last = __import__("json").loads(nfl._LOG.read_text(encoding="utf-8").splitlines()[-1])
assert last["hedged"] is True and last["cause"] == "transport", last

# 4. reader (the du_pulse gauge calls this)
st = nfl.stats(since_ts=0)
assert st["total"] == 6 and st["by_cause"] == {"code_bug": 2, "empty_content": 1, "parse": 1, "transport": 2}, st
assert st["code_bug_alarm"] is True and st["code_bug_by_node"] == {node_id: 2}, st
assert nfl.stats(since_ts=1e12)["total"] == 0
assert nfl.stats(path=tmp / "none.jsonl")["total"] == 0

# 5. fail-open: an unwritable log path never breaks the call
nfl._LOG = tmp / "a_file" / "x.jsonl"
(tmp / "a_file").write_text("x", encoding="utf-8")   # a FILE where a dir is needed -> mkdir/open raises, swallowed
assert asyncio.run(n.run(state)) is False

# 6. tier flag: default off; on + human -> tier 0; on + non-human -> no kwarg
nfl._LOG = tmp / "node_failures.jsonl"
node_base.call_node_json = fake_ok
node_base.HUMAN_CYCLE_TIER0 = True
n.mode = "ok"
assert asyncio.run(n.run(state)) is True and seen.get("tier") == 0, seen
state.input_type = "internal"
assert asyncio.run(n.run(state)) is True and "tier" not in seen, seen
node_base.HUMAN_CYCLE_TIER0 = False
assert node_base.HUMAN_CYCLE_TIER0 is False

# 7. du_pulse wires the reader
src = (ROOT / "scripts" / "du_pulse.py").read_text(encoding="utf-8")
assert 'node_failure_log' in src and '"node_failures"' in src
print("J-2854 OK")
