"""J-2126: static journal_week semantic origin is excluded from the frontier pool. Pure, no I/O."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core
from core import investigation_deepening_shadow as ids
assert str(Path(core.__file__).resolve()).startswith(str(Path(__file__).resolve().parent.parent)), core.__file__
c = lambda i, o, rel, layer="semantic": {"fragment_id": i, "origin": o, "relevance": rel, "layer": layer, "content": i}
assert ids._scored_pool([c("w", "journal_week", 0.7)]) == []
assert ids._pick_frontier([{"ts": 1, "candidates": [c("w", "journal_week", 0.7), c("e", "inner_thought", 0.0, "episodic")]}]) is None
r = ids._pick_frontier([{"ts": 1, "candidates": [c("w", "journal_week", 0.9), c("m", "inner_thought", 0.3, "episodic")]}])
assert r["fragment_id"] == "m"
print("J-2126 OK")
