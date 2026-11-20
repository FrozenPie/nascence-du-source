"""J-3172 / D-0560: Executive `reasoning` is optional in the prompt and defaulted in ExecutiveOutput.

  [1] the prompt schema line marks reasoning optional; the old required wording is gone; epistemic_query text untouched.
  [2] ExecutiveOutput(...) without reasoning is valid (default ""); JSON_SCHEMA no longer requires it but still declares it.
  [3] _write_output tolerates reasoning missing / null / present, and a present value is kept verbatim.
  [4] the teacher-distillation log (training_log.log_example) still writes a row when reasoning is absent (temp dir only).
Reads source and builds prompts only; writes only under a temp dir; no live data.
"""
from __future__ import annotations
import sys, json, tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (BEFORE lab_env / anything else)
assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__

from core.schema import CognitiveState, ExecutiveOutput  # noqa: E402
from core import training_log  # noqa: E402
from nodes.executive_node import ExecutiveNode  # noqa: E402

node = ExecutiveNode()
sp = node.system_prompt
assert '\\"reasoning\\": \\"one sentence\\"' not in (ROOT / "nodes" / "executive_node.py").read_text(encoding="utf-8")
assert '"reasoning": "one sentence"' not in sp
assert '"reasoning": "optionally, one sentence"' in sp
assert "reasoning: optional." in sp
assert '"epistemic_query": null}' in sp
assert "epistemic_query: a search phrase ONLY when a real contradiction needs resolving; else null." in sp
assert "EPISTEMIC SEARCH" in sp
print("[1] ok: prompt marks reasoning optional, epistemic_query untouched")

o = ExecutiveOutput(synthesis="x", should_respond=True, response_type="answer")
assert o.reasoning == "" and o.epistemic_query is None
sch = ExecutiveOutput.JSON_SCHEMA
assert "reasoning" not in sch["required"] and "reasoning" in sch["properties"]
assert sch["required"] == ["synthesis", "should_respond", "response_type"]
assert "epistemic_query" in sch["properties"]
print("[2] ok: dataclass default + schema")

for data, want in (({"synthesis": "a", "response_type": "answer"}, ""),
                   ({"synthesis": "a", "reasoning": None}, ""),
                   ({"synthesis": "a", "reasoning": ""}, ""),
                   ({"synthesis": "a", "reasoning": "because"}, "because")):
    st = CognitiveState(spirit_name="t", axiom="t")
    node._write_output(st, dict(data))
    assert st.executive.reasoning == want, (data, st.executive.reasoning)
    assert st.executive.synthesis == "a"
st = CognitiveState(spirit_name="t", axiom="t")
node._write_output(st, {"synthesis": "a", "epistemic_query": " null "})
assert st.executive.epistemic_query is None
node._write_output(st, {"synthesis": "a", "epistemic_query": "foo bar"})
assert st.executive.epistemic_query == "foo bar"
print("[3] ok: _write_output")

with tempfile.TemporaryDirectory() as td:
    training_log._LOG_DIR = Path(td)
    training_log._dir_ready = False
    training_log.log_example("executive", "p", {"synthesis": "a", "should_respond": True, "response_type": "answer"},
                             system_prompt=sp, cycle_id="t")
    rows = [json.loads(l) for l in (Path(td) / "executive.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1 and "reasoning" not in rows[0]["output"]
print("[4] ok: distillation log row written without reasoning; tree:", ROOT)
