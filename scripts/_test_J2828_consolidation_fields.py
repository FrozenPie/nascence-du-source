"""J-2828 (F-3471, P-0012): ConsolidationNode stops requesting the write-only memories_processed / patterns_noted.

Checks (no model call, store_fragment and the dedup probe stubbed, nothing live touched):
  (a) the system prompt asks only wisdom_extracted and still keeps the Entity-name sentence;
  (b) ConsolidationOutput.JSON_SCHEMA requires only wisdom_extracted (old keys still allowed);
  (c) _write_output with a NEW object {"wisdom_extracted": ...} and with an OLD object (extra legacy keys) stores the same
      fragment (same content / layer / origin / derived_from), and ignores the legacy keys without raising;
  (d) the log line reports the code's own cycle count (len(_recent_cycles)), not a model-reported number;
  (e) the thin-batch, corrected-batch and null-wisdom paths still behave as before.
Run (from the worktree):  python scripts/_test_J2828_consolidation_fields.py
"""
from __future__ import annotations
import logging, pathlib, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                     # noqa: E402  (BEFORE lab_env)
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), core.__file__
from core.schema import CognitiveState, ConsolidationOutput   # noqa: E402
import nodes.consolidation_node as CN                          # noqa: E402

ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and bool(cond)
    print(("  ok   " if cond else "  FAIL ") + name)

stored = []
CN.store_fragment = lambda **kw: stored.append(kw)
CN.wisdom_dup_rule = lambda w: None

node = CN.ConsolidationNode()
sp = node.system_prompt
check("prompt has no memories_processed / patterns_noted", "memories_processed" not in sp and "patterns_noted" not in sp)
check("prompt asks wisdom_extracted only", sp.count('"wisdom_extracted"') == 1 and "Schema: {\"wisdom_extracted\": \"one sentence or null\"}" in sp)
check("Entity-name sentence kept", "personal name" in sp and "Output ONLY a valid JSON object" in sp)
sch = ConsolidationOutput.JSON_SCHEMA
check("schema requires only wisdom_extracted", sch["required"] == ["wisdom_extracted"])
check("schema still allows the legacy keys", {"memories_processed", "patterns_noted"} <= set(sch["properties"]))
check("dataclass builds from the short object", ConsolidationOutput(wisdom_extracted="x").patterns_noted == [])

class Cap(logging.Handler):
    def __init__(self): super().__init__(); self.msgs = []
    def emit(self, r): self.msgs.append(r.getMessage())
cap = Cap(); node.logger.addHandler(cap); node.logger.setLevel(logging.INFO)

def fill(n, corrected=False):
    node._recent_cycles.clear(); node._recent_fragment_ids.clear(); node._batch_corrected = False
    for i in range(n):
        node.add_cycle_summary(f"cycle {i}", fragment_id=f"f{i}", corrected=corrected and i == 0)

st = CognitiveState(spirit_name="Du", axiom="J-2828 test")
fill(5); node._write_output(st, {"wisdom_extracted": "quiet gets louder when it is attended to"})
new_row = dict(stored[-1])
fill(5); node._write_output(st, {"memories_processed": 3, "wisdom_extracted": "quiet gets louder when it is attended to",
                                 "patterns_noted": ["a", "b", "c"]})
old_row = dict(stored[-1])
check("new and old object store the identical fragment", new_row == old_row and len(stored) == 2)
check("fragment content is the prefixed wisdom, layer semantic, origin consolidation",
      new_row["content"] == "I have come to understand: quiet gets louder when it is attended to"
      and new_row["layer"] == "semantic" and new_row["origin"] == "consolidation"
      and new_row["derived_from"] == ["f0", "f1", "f2", "f3", "f4"] and new_row["relevance"] == 0.8)
check("log line carries the code's own count (5) and no patterns", any("processed=5 wisdom=True" in m for m in cap.msgs)
      and not any("patterns=" in m for m in cap.msgs))
check("batch state cleared after the write", node._recent_cycles == [] and node._recent_fragment_ids == [])

n0 = len(stored); cap.msgs.clear()
fill(2); node._write_output(st, {"wisdom_extracted": "thin batch"})
check("thin batch (<3) still withheld", len(stored) == n0 and any("processed=2 wisdom=False" in m for m in cap.msgs))
fill(4, corrected=True); node._write_output(st, {"wisdom_extracted": "a failure turned doctrine"})
check("corrected batch still quarantined", len(stored) == n0)
fill(4); node._write_output(st, {"wisdom_extracted": None})
check("null wisdom stores nothing", len(stored) == n0)
fill(4); node._write_output(st, {})
check("empty object tolerated", len(stored) == n0)

print("PASS" if ok_all else "FAIL")
sys.exit(0 if ok_all else 1)
