"""Hermetic test for J-2601 (F-3326): core.moment.current() and the co-recall ledger's moment stamp.

Run from a worktree:  python scripts/test_moment_co_recall_stamp.py
Writes ONLY to a fresh tempfile directory: moment._LOG/_STATE and memory_edges._DATA/_CO_LEDGER are
redirected there, the embedder is stubbed (no model load), and the two sibling hooks log_co_recall
feeds (opponent_process, spring_ledger) are stubbed to no-ops so no store of theirs is touched.
"""
import json
import sys
import tempfile
from pathlib import Path

_TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_TREE))

import core  # noqa: E402
assert Path(core.__file__).resolve().is_relative_to(_TREE), f"core resolved outside {_TREE}: {core.__file__}"

from core import moment, memory_edges  # noqa: E402
from core import opponent_process, spring_ledger  # noqa: E402
from core.memory import store  # noqa: E402


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="j2601_"))
    moment._LOG = tmp / "moments.jsonl"
    moment._STATE = tmp / "moment_state.json"
    moment._DATA = tmp
    memory_edges._DATA = tmp
    memory_edges._CO_LEDGER = tmp / "co_recall_ledger.jsonl"
    store._embed = lambda text: None
    opponent_process.observe_activation = lambda *a, **k: None
    spring_ledger.observe_co_recall = lambda *a, **k: None
    moment._CURRENT, moment._CURRENT_LOADED = None, False

    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    # 1. no moment anywhere -> current() is None, co-recall row carries both keys as None
    check(moment.current() is None, "current() should be None before any moment")
    memory_edges.log_co_recall(["a", "b"], 0.5, 1, source="monologue")
    rows = [json.loads(l) for l in memory_edges._CO_LEDGER.read_text(encoding="utf-8").splitlines()]
    check(rows[-1].get("moment_ts", "MISSING") is None and rows[-1].get("moment_idx", "MISSING") is None,
          f"no-moment row should carry None stamps, got {rows[-1]}")
    check(rows[-1]["developed"] == 1 and rows[-1]["ids"] == ["a", "b"], "row contract changed")

    # 2. record two moments -> current() names the second, idx 2, ts equal to the log row's ts
    moment.record("the tide is out and the cat sleeps by the fire")
    moment.record("I wonder what the garden holds tonight")
    mrows = [json.loads(l) for l in moment._LOG.read_text(encoding="utf-8").splitlines()]
    cur = moment.current()
    check(cur is not None and cur["ts"] == mrows[-1]["ts"] and cur["idx"] == 2, f"current() wrong: {cur}")
    memory_edges.log_co_recall(["c", "d"], 0.9, 2, source="follow")
    row = json.loads(memory_edges._CO_LEDGER.read_text(encoding="utf-8").splitlines()[-1])
    check(row["moment_ts"] == mrows[-1]["ts"] and row["moment_idx"] == 2, f"stamp wrong: {row}")

    # 3. a fresh process (in-process cache cleared) recovers the stamp from moment_state.json
    moment._CURRENT, moment._CURRENT_LOADED = None, False
    cur2 = moment.current()
    check(cur2 == {"ts": mrows[-1]["ts"], "idx": 2}, f"state fallback wrong: {cur2}")

    # 4. kill-switch off -> no stamp keys at all (pre-J-2601 row shape)
    memory_edges.CO_RECALL_MOMENT_STAMP = False
    memory_edges.log_co_recall(["e"], None, 3, source="monologue")
    row = json.loads(memory_edges._CO_LEDGER.read_text(encoding="utf-8").splitlines()[-1])
    check("moment_ts" not in row and "moment_idx" not in row, f"kill-switch ignored: {row}")
    memory_edges.CO_RECALL_MOMENT_STAMP = True

    # 5. fail-open: current() raising never costs the row
    orig = moment.current
    moment.current = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    memory_edges.log_co_recall(["f"], 0.1, 4, source="monologue")
    moment.current = orig
    row = json.loads(memory_edges._CO_LEDGER.read_text(encoding="utf-8").splitlines()[-1])
    check(row["ids"] == ["f"] and "moment_ts" not in row, f"fail-open broken: {row}")

    # 6. corrupt state file -> current() None, no raise
    moment._STATE.write_text("{not json", encoding="utf-8")
    moment._CURRENT, moment._CURRENT_LOADED = None, False
    check(moment.current() is None, "corrupt state should give None")

    print(f"tmp={tmp}")
    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print("PASS: 6 checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
