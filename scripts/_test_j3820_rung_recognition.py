"""J-3820 / D-0723: recognition gate keyed on persisted rung, not rust-docked confidence (temp ledger only)."""
import sys, json, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import procedures as P
tmp = Path(tempfile.mkdtemp()); P._F = tmp / "procedures.json"; P._LOG = tmp / "log.jsonl"
key = P.talk_key("how do I bake bread")
now = time.time()
P._F.write_text(json.dumps({"procedures": {key: {"key": key, "scope": "talk", "rung": "persisted", "confidence": 0.54,
    "last_ts": now}}, "archive": []}), encoding="utf-8")
assert P.mirror_proficiency("how do I bake bread") == 0.54
assert P.mirror_recognition_proficiency("how do I bake bread") == 0.60   # recognised despite rust
assert P.mirror_recognition_proficiency("unknown thing") is None
print("PASS")
