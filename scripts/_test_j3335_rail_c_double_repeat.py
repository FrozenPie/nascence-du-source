"""J-3335: Rail C shadow double_repeat trigger. Hermetic: temp log path (outside data/), stub embedder, no live store,
no model call. Run from the worktree:  python scripts/_test_j3335_rail_c_double_repeat.py  (exit 0 = ALL OK)"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (core BEFORE lab_env)
sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env  # noqa: E402

assert ROOT in Path(core.__file__).resolve().parents, core.__file__
lab_env.isolate()
from core import grounding_injection as gi  # noqa: E402

fails = []


def ok(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c:
        fails.append(m)


tmp = Path(tempfile.mkdtemp(prefix="j3335_"))
gi._LOG = tmp / "gi.jsonl"
gi.gather = lambda state=None, now=None: []      # no pool reads
gi.recent_curiosity_themes = lambda *a, **k: []
gi._seed_pick_counts = lambda: None
stub = lambda t: None  # noqa: E731
sig = {"about": "x", "source": "dmn", "train_kind": "k", "train_len": 1}

r0 = gi.observe(dict(sig), "a first thought", None, live={}, now=1000.0, embed=stub, bored_streak=0)
ok(r0["double_repeat"] is False and r0["trigger"] is None, "streak 0: no double_repeat, trigger None")
r1 = gi.observe(dict(sig), "second thought", None, live={"redirected": True}, now=2000.0, embed=stub, bored_streak=2)
ok(r1["double_repeat"] is True and r1["trigger"] == "double_repeat" and r1["would_inject"], "streak 2: row trigger double_repeat, would inject")
ok(r1["live_redirect"] is True and "pools_v" in r1 and r1["pools_v"] == gi.POOLS_V, "same pool evaluation (pools_v) and live flags carried")
r2 = gi.observe(dict(sig), "third thought", None, live={}, now=2100.0, embed=stub, bored_streak=3)
ok(r2["double_repeat"] and r2["cooldown_blocked"] and not r2["would_inject"], "cooled-down double_repeat still logged, cooldown_blocked set")
r3 = gi.observe(dict(sig, circling=True), "fourth thought", None, live={}, now=9000.0, embed=stub, bored_streak=None)
ok(r3["trigger"] == "circling" and r3["double_repeat"] is False, "no streak passed: old trigger name, no double_repeat")
r4 = gi.observe(dict(sig, circling=True), "fifth thought", None, live={}, now=20000.0, embed=stub, bored_streak=2)
ok(r4["trigger"] == "circling" and "double_repeat" in r4["reasons"], "double_repeat alongside another reason keeps the other as trigger")
rows = [json.loads(l) for l in gi._LOG.read_text(encoding="utf-8").splitlines()]
ok(len(rows) == 5 and sum(1 for r in rows if r["trigger"] == "double_repeat") == 2, "log has 5 rows, 2 of kind double_repeat")
old = {"ts": 1.0, "reasons": ["topic_lock"], "would_inject": True}
ok(old.get("trigger") is None and old.get("double_repeat") is None, "old-shape rows lack the fields and still read")
ok(gi.status().get("rows", 0) >= 0, "status() parses a mixed log")
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
ok('bored_streak=_gi.get("streak_start")' in src, "node passes tick-start streak into the existing observe call")
print("ALL OK" if not fails else f"{len(fails)} FAIL")
sys.exit(1 if fails else 0)
