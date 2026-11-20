"""J-3071 (F-3777): the /quit session epoch samples the WHOLE session, not the newest 25 fragments.

Offline, temp DB only (store.DB_PATH redirected before any call); touches no live data, calls no model.

Covers:
  1. a long uneven session (1200 fragments, a dense last burst like the quit-sleep): get_fragments_in_range(limit=25)
     spans only the tail, get_fragments_spread(n=25) returns exactly 25 spanning >= 90% of the range, oldest first,
     no duplicates, row shape (fragment_id, content, origin).
  2. even session: one fragment per time bucket (the newest of each).
  3. bursty session (all fragments in 3 clusters): shortfall topped up, still exactly n, all from the range.
  4. fewer than n -> all returned; empty range -> []; zero-length range -> still n or fewer, no crash.
  5. only layer='episodic' rows, only rows inside [start, end].
  6. the old get_fragments_in_range is unchanged (newest-first, limit honoured).
  7. wiring: _form_epoch uses get_fragments_spread and no longer calls get_fragments_in_range; the 150-char cut,
     store_epoch call and fragment_count=len(frags) are intact; the prompt text is untouched by this job.
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core                                             # noqa: E402  (core BEFORE lab_env)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
import core.memory.store as store                       # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="j3071_epoch_spread_"))
store.DB_PATH = _TMP / "test.db"

conn = sqlite3.connect(str(store.DB_PATH))
conn.executescript("""CREATE TABLE memory_fragments (
    fragment_id TEXT PRIMARY KEY, content TEXT NOT NULL, layer TEXT NOT NULL DEFAULT 'episodic',
    relevance REAL NOT NULL DEFAULT 0.5, timestamp REAL NOT NULL, keywords TEXT NOT NULL DEFAULT '',
    embedding BLOB, origin TEXT NOT NULL DEFAULT 'lived', derived_from TEXT NOT NULL DEFAULT '[]');""")


def _fill(rows):
    conn.execute("DELETE FROM memory_fragments")
    conn.executemany("INSERT INTO memory_fragments (fragment_id, content, layer, timestamp, origin) VALUES (?,?,?,?,?)", rows)
    conn.commit()


T0, T1 = 1_000_000.0, 1_000_000.0 + 167 * 3600.0
fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (("  " + detail) if detail and not cond else ""))
    if not cond:
        fails.append(name)


# 1. long session, dense tail
rows = [(f"a{i}", f"early {i}", "episodic", T0 + (T1 - T0) * i / 1000.0 * 0.999, "reading") for i in range(1000)]
rows += [(f"b{i}", f"tail {i}", "episodic", T1 - 600 + i * 2.0, "inner_thought") for i in range(200)]
_fill(rows)
old = store.get_fragments_in_range(T0, T1, limit=25)
new = store.get_fragments_spread(T0, T1, n=25)
old_ts = [float(conn.execute("SELECT timestamp FROM memory_fragments WHERE fragment_id=?", (r["fragment_id"],)).fetchone()[0]) for r in old]
new_ts = [float(r["timestamp"]) for r in new]
check("1a old sampler spans < 1% of the session", (max(old_ts) - min(old_ts)) / (T1 - T0) < 0.01)
check("1b spread returns exactly 25", len(new) == 25, str(len(new)))
check("1c spread spans >= 90% of the range", (max(new_ts) - min(new_ts)) / (T1 - T0) >= 0.90, str((max(new_ts) - min(new_ts)) / (T1 - T0)))
check("1d oldest first, no duplicates", new_ts == sorted(new_ts) and len({r["fragment_id"] for r in new}) == 25)
check("1e row shape", all(set(("fragment_id", "content", "origin")) <= set(r.keys()) for r in new))
check("1f the first sample is from the first quarter, not the tail", new_ts[0] < T0 + (T1 - T0) * 0.25)

# 2. even session -> one per bucket
_fill([(f"e{i}", f"x{i}", "episodic", T0 + (T1 - T0) * (i + 0.5) / 100.0, "lived") for i in range(100)])
ev = store.get_fragments_spread(T0, T1, n=25)
bk = [min(24, int((float(r["timestamp"]) - T0) / (T1 - T0) * 25)) for r in ev]
check("2 even session: exactly one per bucket", len(ev) == 25 and sorted(bk) == list(range(25)), str(bk))

# 3. bursty session -> topped up
_fill([(f"c{c}_{i}", f"c{c} {i}", "episodic", T0 + (T1 - T0) * c / 2.0 * 0.999 + i, "dream") for c in range(3) for i in range(40)])
bu = store.get_fragments_spread(T0, T1, n=25)
check("3a bursty: topped up to exactly 25", len(bu) == 25, str(len(bu)))
check("3b bursty: no duplicates, covers all three clusters", len({r["fragment_id"] for r in bu}) == 25
      and {r["fragment_id"].split("_")[0] for r in bu} == {"c0", "c1", "c2"})

# 4. small / empty / zero-length
_fill([(f"s{i}", f"s{i}", "episodic", T0 + i, "lived") for i in range(7)])
check("4a fewer than n -> all", len(store.get_fragments_spread(T0, T1, n=25)) == 7)
_fill([])
check("4b empty -> []", store.get_fragments_spread(T0, T1, n=25) == [])
_fill([(f"z{i}", f"z{i}", "episodic", T0, "lived") for i in range(40)])
zl = store.get_fragments_spread(T0, T0, n=25)
check("4c zero-length range: no crash, at most n", 1 <= len(zl) <= 25, str(len(zl)))

# 5. layer + bounds
_fill([("in1", "i", "episodic", T0 + 10, "lived"), ("sem", "s", "semantic", T0 + 20, "lived"),
       ("pre", "p", "episodic", T0 - 5, "lived"), ("post", "q", "episodic", T1 + 5, "lived"),
       ("in2", "j", "episodic", T0 + 30, "lived")])
fl = store.get_fragments_spread(T0, T1, n=25)
check("5 only episodic rows inside the range", [r["fragment_id"] for r in fl] == ["in1", "in2"], str([r["fragment_id"] for r in fl]))

# 6. old function unchanged (newest first, limit)
_fill([(f"o{i}", f"o{i}", "episodic", T0 + i, "lived") for i in range(50)])
o = store.get_fragments_in_range(T0, T1, limit=5)
check("6 get_fragments_in_range still newest-first with limit", [r["fragment_id"] for r in o] == ["o49", "o48", "o47", "o46", "o45"])

# 7. wiring
src = (TREE / "scripts" / "run_nascence.py").read_text(encoding="utf-8")
body = src[src.index("async def _epoch_synthesise"):src.index("def _save_affect")]  # J-4348: prompt moved into helper
check("7a _form_epoch uses get_fragments_spread", "get_fragments_spread(session_start, session_end, n=25)" in body)
check("7b _form_epoch no longer calls get_fragments_in_range", "get_fragments_in_range(" not in body)
check("7c 150-char cut, JSON contract and fragment_count intact",
      "r['content'][:150]" in body and '{"mood": "...", "impression": "..."}' in body and "fragment_count  = len(frags)" in body)
check("7d import present", "get_fragments_spread" in src.split("def ")[0])

conn.close()
print("\nALL PASS" if not fails else "\nFAILED: " + ", ".join(fails))
sys.exit(1 if fails else 0)
