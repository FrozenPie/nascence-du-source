"""J-3870: ai_judge_verdict states the right verdict; hermetic (temp log + temp state only, no live data)."""
import json, sys, tempfile
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from core import shadow_log  # noqa: F401
from nodes import subconscious_node as sn
assert Path(sn.__file__).resolve().is_relative_to(root)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_judge_verdict as v

with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    sn._STATE_FILE = d / "nostate"
    sn._AI_JUDGE_LOG = d / "missing.jsonl"
    assert v.verdict(sn.active_imagination_judge_status()).startswith("NO-DATA")
    def put(rows):
        p = d / "log.jsonl"
        p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        sn._AI_JUDGE_LOG = p
        return v.verdict(sn.active_imagination_judge_status())
    T = {"judge_verdict": True}; F = {"judge_verdict": False}; U = {"judge_verdict": None}
    assert put([T] * 5 + [U] * 20).startswith("JUDGE-UNAVAILABLE")
    assert put([T] * 10).startswith("INSUFFICIENT")
    assert put([T] * 99 + [F]).startswith("AGREES")
    assert put([T] * 60 + [F] * 20).startswith("DIVERGES")
print("OK")
