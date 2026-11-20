"""
Test suite -- J-3126 / F-3853 / P-0111: Lane 2 tick rows carry `coherence_moved` ('place' / 'standpoint' / 'same' / None)
and `status()` reports `incoherence_by_move` beside the pooled `incoherence_rate`.  Instrument only: no judge input or
verdict changes.

Hermetic: lane2's `_LOG` is redirected to a temp dir for the status() checks; nothing live is written (the live shadow
log is stat-checked before and after).  The live-window figures at the end are READ-ONLY.

Run: python scripts/_test_J-3126_coherence_moved.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core as _core_pkg  # noqa: E402
assert str(Path(_core_pkg.__file__).resolve()).lower().startswith(str(ROOT).lower()), _core_pkg.__file__
from core import lane2  # noqa: E402

_ORIG_LOG = lane2._LOG
_before = (_ORIG_LOG.stat().st_size, _ORIG_LOG.stat().st_mtime_ns) if _ORIG_LOG.exists() else None
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {extra}" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


# --- helper -------------------------------------------------------------------------------------------------------
def store(*entries):
    return {"factual": list(entries)}


e = {"ts": 1, "notice": "x", "place": "study", "standpoint": "at_the_door"}
check("no store entries -> None", lane2._coherence_moved({}, "study", "at_the_door") is None)
check("empty factual -> None", lane2._coherence_moved({"factual": []}, "study", "at_the_door") is None)
check("same place + standpoint -> same", lane2._coherence_moved(store(e), "study", "at_the_door") == "same")
check("place differs -> place", lane2._coherence_moved(store(e), "garden", "at_the_door") == "place")
check("place AND standpoint differ -> place", lane2._coherence_moved(store(e), "garden", "by_the_fire") == "place")
check("only standpoint differs -> standpoint", lane2._coherence_moved(store(e), "study", "by_the_fire") == "standpoint")
old = {"ts": 1, "notice": "x"}                                   # entry from before F-1933: neither key
check("old entry lacking fields -> None", lane2._coherence_moved(store(old), "study", "at_the_door") is None)
check("old entry with only place -> None",
      lane2._coherence_moved(store({"ts": 1, "place": "study"}), "study", "at_the_door") is None)
n1 = {"ts": 1, "notice": "x", "place": None, "standpoint": None}
check("previous values None -> None (not 'same')", lane2._coherence_moved(store(n1), None, None) is None)
check("new place None -> None", lane2._coherence_moved(store(e), None, "at_the_door") is None)
check("new standpoint None -> None", lane2._coherence_moved(store(e), "study", None) is None)
check("uses NEWEST entry only",
      lane2._coherence_moved(store({"place": "garden", "standpoint": "a"}, e), "study", "at_the_door") == "same")
check("non-dict store entry -> None", lane2._coherence_moved({"factual": ["junk"]}, "a", "b") is None)
check("None factual -> None", lane2._coherence_moved({"factual": None}, "a", "b") is None)

# --- wiring: tick() row sets the key from percepts, before the store append -----------------------------------------
src = (ROOT / "core" / "lane2.py").read_text(encoding="utf-8")
i_key = src.index('"coherence_moved": _coherence_moved(store,')
i_append = src.index('store.setdefault("factual", []).append(', i_key)
check("tick row key present and precedes this tick's store append", 0 < i_key < i_append)
check("tick row key uses percepts world place + standpoint",
      '_coherence_moved(store, (percepts.get("world") or {}).get("place"),' in src
      and 'percepts.get("standpoint"))' in src[i_key:i_key + 400])
i_cc = src.index("async def _coherence_check(")
i_cc_end = src.index("\n# D-0342", i_cc)
check("_coherence_check (the judge) does not mention coherence_moved", "coherence_moved" not in src[i_cc:i_cc_end])


# --- status() split ------------------------------------------------------------------------------------------------
def row(i, verdict, moved="__absent__"):
    r = {"kind": "tick", "ts": 1000 + i, "notice": f"n{i}", "expect_next": f"e{i}",
         "coherence": {"verdict": verdict, "how": "t"}, "grounding": {"grounded_share": 1.0}}
    if moved != "__absent__":
        r["coherence_moved"] = moved
    return r


rows = ([row(i, "incoherent", "place") for i in range(3)] + [row(10 + i, "coherent", "place") for i in range(2)]
        + [row(20, "incoherent", "same")] + [row(30 + i, "coherent", "same") for i in range(9)]
        + [row(40, "coherent", "standpoint"), row(41, "cannot_tell", "standpoint")]
        + [row(50 + i, "incoherent") for i in range(4)]            # OLD rows: no key -> excluded from the split
        + [row(60, "incoherent", None)])                            # None -> excluded from the split
tmp = Path(tempfile.mkdtemp(prefix="J-3126_"))
lane2._LOG = tmp / "lane2_shadow.jsonl"
lane2._LOG.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
try:
    st = lane2.status()
finally:
    lane2._LOG = _ORIG_LOG
by = st.get("incoherence_by_move") or {}
check("status has incoherence_by_move", set(by) == {"place", "standpoint", "same"}, str(by))
check("place: 3 of 5 incoherent", by.get("place") == {"rate": 0.6, "n": 5, "incoherent": 3, "rows": 5}, str(by.get("place")))
check("same: 1 of 10 incoherent", by.get("same") == {"rate": 0.1, "n": 10, "incoherent": 1, "rows": 10}, str(by.get("same")))
check("standpoint: cannot_tell not in n", by.get("standpoint") == {"rate": 0.0, "n": 1, "incoherent": 0, "rows": 2},
      str(by.get("standpoint")))
check("old/None rows not counted as 'same'", by.get("same", {}).get("rows") == 10)
check("pooled incoherence_rate still over every judged row (9 of 21)",
      st.get("incoherence_rate") == round(9 / 21, 3), str(st.get("incoherence_rate")))

# no tagged rows at all: rate None, not 0
lane2._LOG = tmp / "lane2_old.jsonl"
lane2._LOG.write_text("\n".join(json.dumps(row(i, "coherent")) for i in range(3)) + "\n", encoding="utf-8")
try:
    st2 = lane2.status()
finally:
    lane2._LOG = _ORIG_LOG
by2 = st2.get("incoherence_by_move") or {}
check("log with no tagged rows -> every bucket rate None, n 0",
      len(by2) == 3 and all(v["rate"] is None and v["n"] == 0 and v["rows"] == 0 for v in by2.values()), str(by2))

# --- live window, READ-ONLY: the live rows carry no coherence_moved yet (restart-gated), so reconstruct the tag from
# consecutive tick rows' place/standpoint to show the split F-3853 reported -------------------------------------------
try:
    from core.shadow_log import tail_rows
    _live_log = _ORIG_LOG if _ORIG_LOG.exists() else Path("C:/Nascence/data/lane2_shadow.jsonl")   # worktree has no data/
    live = [r for r in tail_rows(_live_log, 2000) if r.get("kind") == "tick"]
    tally = {}
    prev = None
    for r in live:
        if prev is not None and None not in (prev.get("place"), prev.get("standpoint"), r.get("place"), r.get("standpoint")):
            mv = "place" if prev["place"] != r["place"] else "standpoint" if prev["standpoint"] != r["standpoint"] else "same"
            v = (r.get("coherence") or {}).get("verdict")
            if v in ("coherent", "incoherent"):
                t = tally.setdefault(mv, [0, 0])
                t[1] += 1
                t[0] += v == "incoherent"
        prev = r
    print("LIVE (reconstructed from consecutive tick rows, read-only):",
          {k: f"{a}/{n} = {a / n:.0%}" for k, (a, n) in tally.items()}, "of", len(live), "tick rows")
except Exception as exc:                                                    # informational only
    print("live reconstruction skipped:", exc)

_after = (_ORIG_LOG.stat().st_size, _ORIG_LOG.stat().st_mtime_ns) if _ORIG_LOG.exists() else None
check("live lane2_shadow.jsonl untouched", _before == _after)
print("\nFAILED: " + ", ".join(FAILS) if FAILS else "\nALL PASSED")
sys.exit(1 if FAILS else 0)
