"""J-3862: scripts/t5_deed_tail_replay.py -- pure-function checks on synthetic data in a temp dir (no live data,
no model, no DB). Asserts: family names come from the trace rows' hands[].hand key, look/move are not deeds,
duplicates collapse, refusal is graded by the world's words, the tail window is closed at W and cut by a
'Session ended' boundary, and per-cluster (c) counting and the day-shift control behave as constructed."""
import sys as _s
_s.stdout.reconfigure(encoding="utf-8")
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core
tree = Path(__file__).resolve().parent.parent
assert tree in Path(core.__file__).resolve().parents, core.__file__
sys.path.insert(0, str(tree / "scripts"))
import t5_deed_tail_replay as dt

FAILS = []


def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS.append(label)


T0 = 1_790_000_000.0
M = 60.0
rows = [
    {"ts": T0 + 5 * M, "hands": [{"hand": "gather", "answer": "You bundle the driftwood.", "ts": T0 + 5 * M}], "dispatch": [{"family": "gather", "decision": "FIRE"}]},
    {"ts": T0 + 6 * M, "hands": [{"hand": "gather", "answer": "You bundle the driftwood.", "ts": T0 + 5 * M}]},          # duplicate
    {"ts": T0 + 7 * M, "hands": [{"hand": "move", "answer": "You walk.", "ts": T0 + 7 * M}]},                           # not a deed
    {"ts": T0 + 40 * M, "hands": [{"hand": "mow", "answer": "The blades jam; the grass will not cut.", "ts": T0 + 40 * M}]},
    {"ts": T0 + 41 * M, "hands": []},
]
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "hands_trace.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\nnot json\n", encoding="utf-8")
    deeds, st = dt.load_deeds(p)
    dt.annotate_outcomes(deeds)
    check("family names read from hands[].hand", [d["family"] for d in deeds] == ["gather", "mow"])
    check("move dropped, duplicate collapsed", st["excluded_family"] == 1 and st["duplicate"] == 1)
    check("refusal graded from the world's words", [d["outcome"] for d in deeds] == ["ok", "refused"])
    check("refused deed carries a kind", deeds[1]["kind"] in ("already", "precond", "skill", "unknown"))
    check("missing file is empty, not an error", dt.load_deeds(Path(tmp) / "nope.jsonl")[0] == [])

idx = dt.DeedIndex(deeds, [])
W = 30 * M
check("deed 5 min after turn is a tail", idx.tail(T0, W) is not None and idx.tail(T0, W)["family"] == "gather")
check("window is closed at W, deed beyond it is not", idx.tail(T0 + 12 * M, W)["family"] == "mow" and idx.tail(T0 + 8 * M, W) is None)
check("a deed BEFORE the turn is not a tail", idx.tail(T0 + 6 * M, 2 * M) is None)
idx_b = dt.DeedIndex(deeds, [T0 + 2 * M])
check("a Session-ended boundary between turn and deed cuts the tail", idx_b.tail(T0, W) is None)
check("same_conversation=False ignores the boundary", idx_b.tail(T0, W, same_conversation=False) is not None)

clusters = [{"first_seen": T0, "members": [{"ts": T0, "q": "a", "conv": 0}, {"ts": T0 + 35 * M, "q": "b", "conv": 1},
                                           {"ts": T0 + 3 * 86400, "q": "c", "conv": 2}]}]
check("per-cluster deed members counted (2 of 3)", dt.count_qualifying(clusters, idx, W) == [2])
check("shifting all turns by a day removes the tails", dt.count_qualifying(clusters, idx, W, 1) == [0])
pm = dt.per_month(clusters, [2])
check("(c) needs >= 2 deed members", list(pm.values())[0] == {"ab_clusters": 1, "abc_clusters": 1}
      and list(dt.per_month(clusters, [1]).values())[0]["abc_clusters"] == 0)
check("rate()", dt.rate(idx, [T0, T0 + 12 * M, T0 + 500 * M], W) == (2, 3))

print("\nFAILS:", FAILS if FAILS else "none")
sys.exit(1 if FAILS else 0)
