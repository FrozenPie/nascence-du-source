"""J-3977 (D-0758): Route 2 _evidence_recall passes dedupe=True to evidence_recall.gather. Hermetic: gather stubbed.
    python scripts/_test_J3977_route2_dedupe.py
"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  -- BEFORE anything else
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import evidence_recall as ev  # noqa: E402
from core import wandering as w  # noqa: E402
from nodes.inner_monologue_node import InnerMonologueNode  # noqa: E402


def main():
    seen = {}

    async def fake_gather(q, train_id=None, source="route2", dedupe=False):
        seen.update(q=q, train_id=train_id, source=source, dedupe=dedupe)
        return {"episodes": [], "outcome": "unclear", "deduped": 0}

    orig = (ev.gather, w.perceive)
    ev.gather, w.perceive = fake_gather, lambda text: None
    try:
        me = SimpleNamespace(_train_id="t-test")
        ok = asyncio.run(InnerMonologueNode._evidence_recall(me, None, "does the garden remember the frost?"))
    finally:
        ev.gather, w.perceive = orig
    fails = []
    if ok is not True:
        fails.append(f"returned {ok!r}")
    if seen.get("dedupe") is not True:
        fails.append(f"dedupe not True: {seen}")
    if seen.get("source", "route2") != "route2":
        fails.append(f"source changed: {seen}")
    if seen.get("train_id") != "t-test":
        fails.append(f"train_id lost: {seen}")
    print("ALL PASS" if not fails else "FAIL " + "; ".join(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
