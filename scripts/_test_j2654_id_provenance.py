"""
Regression: J-2654 (F-3392/F-3393) -- additive per-id provenance on the co-recall ledger row and matched
fragment ids on the felt_recall shadow edge row. Observe-only, restart-gated.

Hermetic: memory_edges' ledger and felt_recall's shadow log are redirected into a temp dir; the two sibling
hooks log_co_recall fires (opponent_process, spring_ledger), the felt_recall theta ray and every
memory_service engine ask() calls are stubbed, so nothing under the real data/ is read or written. The module
refuses to run unless `core` resolves inside this checkout.

  [1] ask()       auto-descend children carry ["auto_descend"] + descend_parent; slot hits carry slots_answered;
                  ids / n_ids / source identical to what the pre-change code would log for the same pool
  [2] old caller  log_co_recall(ids, None, 0, source=) with no new kwargs writes the exact pre-change key set
  [3] guards      misaligned id_slots dropped; >8 ids -> id_slots truncated alongside ids; kill-switch off
  [4] felt_recall fired edge row gains matched_ids (<=8, score order); unfired row unchanged; switch off -> no key
  [5] readers     a mixed old/new ledger + shadow log parses with co_recall_status, downstream_read_counts,
                  felt_recall.status and the sweep script's per-row extraction

  python scripts/_test_j2654_id_provenance.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402
assert str(Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), core.__file__
from core import memory_edges, memory_service, felt_recall  # noqa: E402

# live-store canary: the real ledger/shadow files may exist under ROOT (they do in C:/Nascence); the test
# must leave them byte-identical, so record (size, mtime_ns) now and compare at the end instead of asserting absence
_LIVE_FILES = [ROOT / "data" / "co_recall_ledger.jsonl", ROOT / "data" / "felt_recall_shadow.jsonl"]
_live_before = [(p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else None for p in _LIVE_FILES]
TMP = Path(tempfile.mkdtemp(prefix="j2654_prov_"))
LEDGER = TMP / "co_recall_ledger.jsonl"
SHADOW = TMP / "felt_recall_shadow.jsonl"
memory_edges._DATA = TMP
memory_edges._CO_LEDGER = LEDGER
felt_recall._SHADOW_LOG = SHADOW

# sibling hooks fired after the append: replace with no-ops so no live store is touched
from core import opponent_process, spring_ledger, mood, theta_shadow  # noqa: E402
opponent_process.observe_activation = lambda *a, **k: None
spring_ledger.observe_co_recall = lambda *a, **k: None
mood.current_valence = lambda *a, **k: 0.0
theta_shadow.log_ray = lambda *a, **k: None

FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  {extra}" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


def rows():
    return [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]


# ---------------------------------------------------------------- [1] ask()
def _frag(i, origin="episodic"):
    return {"fragment_id": f"f{i}", "content": f"c{i}", "origin": origin, "activation": 1.0 - i / 100}


import core.associative_recall as ar  # noqa: E402
ar.recall_fragments = lambda cue, k=5, grounded_only=True: [_frag(1, "gist"), _frag(2)]
memory_service._fetch_context = lambda ids: {}
memory_service._descend_from = lambda seed, cap: [_frag(10), _frag(11)] if seed == "f1" else []
memory_service._log_ride = lambda *a, **k: None
memory_service._stash_pending = lambda *a, **k: None
import core.world_ledger_ask as wla  # noqa: E402
wla.shadow_from_ask = lambda *a, **k: None

out = memory_service.ask("curiosity", "a cue", k=5, descend=True)
r1 = rows()[-1]
check("1a ask returns pool incl. descended children", [e["fragment_id"] for e in out] == ["f1", "f2", "f10", "f11"])
check("1b ids/n_ids/source unchanged", r1["ids"] == ["f1", "f2", "f10", "f11"] and r1["n_ids"] == 4 and r1["source"] == "curiosity")
check("1c id_slots per id", r1.get("id_slots") == [["what"], ["what"], ["auto_descend"], ["auto_descend"]], r1.get("id_slots"))
check("1d descend_parent", r1.get("descend_parent") == "f1", r1.get("descend_parent"))

memory_service.ask("pursuits", "a cue", k=5, descend=False)
r2 = rows()[-1]
check("1e no-descend ask: slots only, no descend_parent", r2["id_slots"] == [["what"], ["what"]] and "descend_parent" not in r2, r2)

# multi-slot: 'how' children named explicitly are attributed to "how", not auto_descend
out = memory_service.ask("dream", "a cue", how="f1", descend=True, k=5)
r3 = rows()[-1]
check("1f how children attributed to how", all("auto_descend" not in s for s in r3["id_slots"]) and "descend_parent" not in r3, r3)

# ---------------------------------------------------------------- [2] old-style call
memory_edges.log_co_recall(["a", "b", "c"], 0.5, 3, source="monologue")
r = rows()[-1]
old_keys = {"ts", "n_ids", "ids", "restate_sim", "developed", "step", "source"}
extra_ok = {"moment_ts", "moment_idx"}   # J-2601 stamp, pre-existing
check("2a old-style call: no new keys", set(r) - extra_ok == old_keys, sorted(set(r)))
check("2b old-style call: values", r["ids"] == ["a", "b", "c"] and r["n_ids"] == 3 and r["step"] == 3)

# ---------------------------------------------------------------- [3] guards
memory_edges.log_co_recall(["a", "b"], None, 0, source="x", id_slots=[["what"]])
check("3a misaligned id_slots dropped", "id_slots" not in rows()[-1])
ids12 = [f"i{n}" for n in range(12)]
memory_edges.log_co_recall(ids12, None, 0, source="x", id_slots=[["what"]] * 12)
r = rows()[-1]
check("3b >8 ids: ids and id_slots both capped at 8, n_ids full",
      len(r["ids"]) == 8 and len(r["id_slots"]) == 8 and r["n_ids"] == 12)
memory_edges.CO_RECALL_ID_PROVENANCE = False
memory_edges.log_co_recall(["a"], None, 0, source="x", id_slots=[["what"]])
check("3c kill-switch off -> old shape", "id_slots" not in rows()[-1])
memory_edges.CO_RECALL_ID_PROVENANCE = True
memory_edges.log_co_recall(["a"], None, 0, source="x_shadow", id_slots=[["what"]])
check("3d shadow-source row still appended with provenance",
      rows()[-1]["source"] == "x_shadow" and rows()[-1].get("id_slots") == [["what"]])

# ---------------------------------------------------------------- [4] felt_recall
kept = [f"m{n}" for n in range(24)]


class _P:
    valence, arousal, primary, similarity = 0.2, 0.4, "calm", 0.5


felt_recall._build_prior = lambda dim, value, tup: (_P(), 24, 0.6, list(kept))
felt_recall._get_baseline_valence = lambda: 0.1
felt_recall._affect_now = lambda a: {"valence": 0.0, "arousal": 0.0}
felt_recall._last_fired.clear()
now = time.time()
row = felt_recall._handle_edge("weather", "a", "b", {}, None, now)
check("4a fired row has matched_ids = first 8 in order",
      row.get("matched_ids") == kept[:8] and row["n_match"] == 24, row.get("matched_ids"))
row2 = felt_recall._handle_edge("weather", "b", "c", {}, None, now + 1)   # inside cooldown
check("4b cooldown (unfired) row unchanged: no matched_ids", row2["fired"] is False and "matched_ids" not in row2)
felt_recall._build_prior = lambda dim, value, tup: (None, 0, None, [])
felt_recall._last_fired.clear()
row3 = felt_recall._handle_edge("place", "a", "b", {}, None, now)
check("4c fired with no match: matched_ids == []", row3.get("matched_ids") == [] and row3["n_match"] == 0)
felt_recall.FELT_RECALL_LOG_MATCHED_IDS = False
felt_recall._build_prior = lambda dim, value, tup: (_P(), 24, 0.6, list(kept))
felt_recall._last_fired.clear()
row4 = felt_recall._handle_edge("weather", "a", "b", {}, None, now)
check("4d switch off -> no matched_ids", "matched_ids" not in row4)
felt_recall.FELT_RECALL_LOG_MATCHED_IDS = True
felt_recall._log_row(row4)   # legacy-shaped row
felt_recall._log_row(row)    # new-shaped row

# ---------------------------------------------------------------- [5] readers on a mixed log
mixed = rows()
check("5a ledger is mixed (old-shape and new-shape rows)",
      any("id_slots" in r for r in mixed) and any("id_slots" not in r for r in mixed))
try:
    st = memory_edges.co_recall_status(days=1.0)
    check("5b co_recall_status parses mixed ledger", isinstance(st, dict) and st.get("rows", 0) >= 1, str(st)[:200])
except Exception as exc:
    check("5b co_recall_status parses mixed ledger", False, repr(exc))
try:
    dr = memory_edges.downstream_read_counts(days=1.0)
    check("5c downstream_read_counts parses mixed ledger", isinstance(dr, dict))
except Exception as exc:
    check("5c downstream_read_counts parses mixed ledger", False, repr(exc))
try:
    fs = felt_recall.status()
    check("5d felt_recall.status parses mixed shadow log", isinstance(fs, dict) and not fs.get("error"), str(fs)[:200])
except Exception as exc:
    check("5d felt_recall.status parses mixed shadow log", False, repr(exc))


# the J-2638 sweep loader's per-row logic (scripts/lab_geometric_perturbation_sweep_v2.py read_ledger) reads only
# source / ids, so the extra keys must not change what it extracts
def sweep_extract(line):
    r = json.loads(line)
    src = r.get("source")
    if isinstance(src, str) and src.endswith("_shadow"):
        return None
    return src, list(dict.fromkeys(x for x in (r.get("ids") or []) if x))


lines = [l for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
stripped = []
for l in lines:
    d = json.loads(l)
    d.pop("id_slots", None)
    d.pop("descend_parent", None)
    stripped.append(json.dumps(d))
check("5e sweep-loader extraction identical with/without the new keys",
      [sweep_extract(a) for a in lines] == [sweep_extract(b) for b in stripped])
check("5f this test left the checkout data/ ledger and shadow files untouched (absent, or size+mtime unchanged)",
      [(p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else None for p in _LIVE_FILES] == _live_before)

print("\nALL OK" if not FAILS else f"\nFAILED: {FAILS}")
sys.exit(1 if FAILS else 0)
