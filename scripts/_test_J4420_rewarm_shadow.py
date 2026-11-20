"""J-4420 test: re-warm SHADOW log. Temp paths only; never reads or writes C:/Nascence/data.

Checks: walled-only pending; 4-gram label; embedding label at T_EMB with an injected embedder; unused rows
write no would_warm; the scored denominator; would_warm_until = ts + 7 d; TTL drop; kill switch; nothing is
applied (no DB touched: the module has no DB code path); associative_recall hook passes only SERVED walled rows;
daily_counts; the fence refuses a non-live process for the real _LOG.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (import core BEFORE anything else; assert it is this tree)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), core.__file__

import numpy as np  # noqa: E402
from core import rewarm_shadow as rw  # noqa: E402
from core import associative_recall as ar  # noqa: E402

assert Path(rw._LOG).resolve().is_relative_to(ROOT.resolve()), rw._LOG   # this tree's data/, not another

TMP = Path(tempfile.mkdtemp(prefix="J4420_"))
LOG = TMP / "rewarm_shadow.jsonl"


def fake_embed_batch(texts):
    """Deterministic, orthogonal: 'river' -> e0, 'remember' -> e1, anything else -> e2."""
    out = []
    for t in texts:
        v = np.zeros(4, dtype=np.float32)
        tl = (t or "").lower()
        v[0 if "river" in tl else (1 if "remember" in tl else 2)] = 1.0
        out.append(v)
    return out


def rows():
    return [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines()] if LOG.exists() else []


fails = 0


def check(name, cond):
    global fails
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails += 1


# 1. pending keeps walled only
rw._pending.clear()
rw.note_surfaced([
    {"fragment_id": "w1", "walled": True, "origin": "lived", "activation": 0.31,
     "content": "We walked along the old stone bridge at dusk."},
    {"fragment_id": "w2", "walled": True, "origin": "dream", "activation": 0.25,
     "content": "The river was very loud that night."},
    {"fragment_id": "w3", "walled": True, "origin": "lived", "activation": 0.23,
     "content": "Nothing in common with anything at all here."},
    {"fragment_id": "a1", "walled": False, "origin": "lived", "activation": 0.5,
     "content": "We walked along the old stone bridge at dusk."},
], "recall_memory_fragments")
check("pending holds the 3 walled rows only", sorted(rw._pending) == ["w1", "w2", "w3"])

# 2. label + log
now = 1_800_000_000.0
items = rw._take_pending(time.time())
check("take_pending clears", rw._pending == {} and len(items) == 3)
out_text = "I remember we walked along the old path. A river ran beside it."
written = rw.label_and_log(items, out_text, "voice", embed_batch=fake_embed_batch, log_path=LOG, now=now)
by = {r["fragment_id"]: r for r in written}
check("w1 used by 4-gram only", by.get("w1", {}).get("used_label") == "4gram")
check("w2 used by embedding only", by.get("w2", {}).get("used_label") == "emb"
      and by["w2"]["emb_max_cos"] >= rw.T_EMB)
check("w3 unused -> no would_warm", "w3" not in by)
check("would_warm_until = ts + 7 d", all(abs(r["would_warm_until"] - (now + 7 * 86400)) < 1e-3 for r in written))
check("mode is shadow on every row", all(r["mode"] == "shadow" for r in written))
lr = rows()
scored = [r for r in lr if r["kind"] == "scored"]
check("one scored row with n_walled=3 n_used=2", len(scored) == 1 and scored[0]["n_walled"] == 3
      and scored[0]["n_used"] == 2)
check("row fields", set(written[0]) >= {"ts", "fragment_id", "origin", "trail_activation", "used_label",
                                         "would_warm_until"})

# 3. both labels
rw.label_and_log([{"fragment_id": "w4", "content": "the river ran past the mill", "origin": "lived",
                   "trail_activation": 0.3, "surfaced_source": "recall_fragments"}],
                 "and the river ran past the mill again", "idle_thought",
                 embed_batch=fake_embed_batch, log_path=LOG, now=now + 86400)
check("both labels", [r for r in rows() if r.get("fragment_id") == "w4"][0]["used_label"] == "both")

# 4. TTL
rw.note_surfaced([{"fragment_id": "old", "walled": True, "content": "an old memory of the river bank"}], "x")
rw._pending["old"]["surfaced_ts"] -= rw.PENDING_TTL_S + 5
check("expired pending dropped", rw._take_pending(time.time()) == [])

# 5. kill switch
rw.REWARM_SHADOW_ON = False
rw.note_surfaced([{"fragment_id": "k", "walled": True, "content": "some content here ok"}], "x")
check("kill switch: nothing pending", rw._pending == {})
rw.REWARM_SHADOW_ON = True

# 6. associative_recall hook passes only SERVED walled rows, with content
rw._pending.clear()
trail = [{"fragment_id": "s1", "walled": True, "activation": 0.3, "origin": "lived"},
         {"fragment_id": "s2", "walled": True, "activation": 0.25, "origin": "lived"},   # walled, NOT served
         {"fragment_id": "s3", "walled": False, "activation": 0.4, "origin": "lived"}]
ar._note_rewarm_surfaced(trail, {"s1": "served walled content here", "s3": "served warm content"}, "recall_fragments")
check("hook: only served walled row pending", list(rw._pending) == ["s1"]
      and rw._pending["s1"]["content"] == "served walled content here")
rw._pending.clear()

# 7. note_output with nothing pending spawns nothing and never raises
rw.note_output("a thought", "idle_thought")
ar.note_output_for_rewarm("", "voice")
check("note_output with empty pending is a no-op", True)

# 8. daily counts
d = rw.daily_counts(LOG)
check("daily_counts two days", len(d) == 2 and sum(v["would_warm"] for v in d.values()) == 3
      and sum(v["scored_walled"] for v in d.values()) == 4)

# 9. the real _LOG is fenced: label_and_log with default path in this non-live process writes nothing there
real_before = rw._LOG.exists() and rw._LOG.stat().st_size
res = rw.label_and_log([{"fragment_id": "z", "content": "the river ran past the mill"}],
                       "the river ran past the mill", "voice", embed_batch=fake_embed_batch)
real_after = rw._LOG.exists() and rw._LOG.stat().st_size
check("fence: real data log not written by a non-live process", real_before == real_after)

# 10. nothing in the module writes the DB
src = Path(rw.__file__).read_text(encoding="utf-8")
check("module has no DB write path", "cold=0" not in src.replace("no cold=0 write", "")
      and "UPDATE" not in src and "sqlite3" not in src)

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL'}  (tmp {TMP})")
sys.exit(1 if fails else 0)
