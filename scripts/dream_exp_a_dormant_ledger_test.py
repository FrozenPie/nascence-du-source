"""
J-1800 (F-2425): hermetic test for scripts/dream_experiment_a.py pick_dormant_fragment()'s co_recall_ledger
scan -- the D-0231 "absent from co_recall_ledger.jsonl for >= 14 days" criterion.

Before J-1800 the scan read row["fragment_ids"], a key no ledger row has ever carried (log_co_recall writes
"ids"), so recent_ids was always empty and the criterion excluded nothing. The fix reads "ids" (tolerating
"fragment_ids"), and skips *_shadow rows (core.memory_edges._is_shadow_source -- would-have-shown rows a
kill-switched path logs instead of showing, never a recall). This test FAILS on the pre-J-1800 script
(n_candidates 6, nothing excluded) and PASSES on the fixed one (n_candidates 4).

J-1865 (F-2487) adds F_future_row: an ids row dated AFTER hist_now (a historical hist_now sees later
recalls up to the real freeze moment). It must stay a candidate -- fails on the unbounded J-1800 scan
(n_candidates 3), passes once the window is bounded at hist_now (n_candidates 4).

Hermetic: no live store is opened. core.memory.store._connect / medges._connect / mstore._embed / DB_PATH
are stubbed against a temp sqlite file plus a temp ledger written beside it (the same place amain() copies
the real ledger to -- DB_PATH.parent / "co_recall_ledger.jsonl"). Run from the tree under test:

    python scripts/dream_exp_a_dormant_ledger_test.py
"""
from __future__ import annotations

import importlib.util
import json
import random
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

_TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_TREE))

import core  # noqa: E402  -- BEFORE anything imports lab_env (which appends C:\Nascence to sys.path)

assert Path(core.__file__).resolve().is_relative_to(_TREE), f"core resolved outside the tree under test: {core.__file__}"

import numpy as np  # noqa: E402

_spec = importlib.util.spec_from_file_location("dream_experiment_a_under_test", _TREE / "scripts" / "dream_experiment_a.py")
dea = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dea)
assert Path(dea.mstore.__file__).resolve().is_relative_to(_TREE), f"store resolved outside the tree: {dea.mstore.__file__}"
assert Path(dea.medges.__file__).resolve().is_relative_to(_TREE), f"memory_edges resolved outside the tree: {dea.medges.__file__}"
assert Path(dea.dn.__file__).resolve().is_relative_to(_TREE), f"dream_node resolved outside the tree: {dea.dn.__file__}"


def _vec(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(8).astype(np.float32)
    return v / np.linalg.norm(v)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="J-1800_dormant_ledger_test_"))
    db = tmp / "nascence.db"
    hist_now = time.time() - 3 * 86400.0
    day = 86400.0
    old_ts = hist_now - 60 * day  # all candidates comfortably past the 30-day age cut

    conn0 = sqlite3.connect(str(db))
    conn0.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, embedding BLOB, "
                  "origin TEXT, timestamp REAL, chapter_id TEXT)")
    conn0.execute("CREATE TABLE memory_edges (src_kind TEXT, src_id TEXT, dst_kind TEXT, dst_id TEXT)")
    frags = {
        "X_recent_ids":      "in a plain ids row 1 day before hist_now -> must be EXCLUDED",
        "Y_shadow_only":     "only in a monologue_shadow row 1 day before hist_now -> must stay a candidate",
        "Z_old_row":         "in an ids row 20 days before hist_now -> outside 14d, must stay a candidate",
        "W_legacy_key":      "in a row using the old fragment_ids key 2 days before -> tolerated, EXCLUDED",
        "V_never_recalled":  "never in the ledger -> candidate",
        "E_edged":           "has a memory_edges edge to the seed id -> EXCLUDED by the untouched edge rule",
        "F_future_row":      "in an ids row 2 days AFTER hist_now (J-1865) -> a later recall, must stay a candidate",
    }
    for i, (fid, content) in enumerate(frags.items()):
        conn0.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?)",
                      (fid, content, _vec(i + 10).tobytes(), "reading", old_ts, "chapter-1"))
    conn0.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?)",
                  ("S1_seed", "the seed fragment this night recalled", _vec(99).tobytes(), "reading", old_ts, "chapter-1"))
    conn0.execute("INSERT INTO memory_edges VALUES ('fragment','S1_seed','fragment','E_edged')")
    conn0.commit()
    conn0.close()

    ledger = tmp / "co_recall_ledger.jsonl"  # == DB_PATH.parent / "co_recall_ledger.jsonl", as amain() lays it out
    rows = [
        {"ts": hist_now - 1 * day, "n_ids": 1, "ids": ["X_recent_ids"], "source": "monologue"},
        {"ts": hist_now - 1 * day, "n_ids": 1, "ids": ["Y_shadow_only"], "source": "monologue_shadow"},
        {"ts": hist_now - 20 * day, "n_ids": 1, "ids": ["Z_old_row"], "source": "wandering"},
        {"ts": hist_now - 2 * day, "n_ids": 1, "fragment_ids": ["W_legacy_key"]},
        # J-1865 (F-2487): a recall made AFTER the simulated night (a historical hist_now) must not count
        {"ts": hist_now + 2 * day, "n_ids": 1, "ids": ["F_future_row"], "source": "monologue"},
    ]
    ledger.write_text("\n".join(json.dumps(r) for r in rows) + "\n\n", encoding="utf-8")

    def _connect():
        c = sqlite3.connect(str(db))
        c.row_factory = sqlite3.Row
        return c

    dea.mstore._connect = _connect
    dea.medges._connect = _connect
    dea.mstore.DB_PATH = db
    dea.mstore._embed = lambda text: _vec(1) if text else None

    random.seed(1800)
    res = dea.pick_dormant_fragment(day_block_text="a day block", seed_ids=["S1_seed"], hist_now=hist_now)
    assert res is not None, "pick_dormant_fragment returned None"
    expected_candidates = {"Y_shadow_only", "Z_old_row", "V_never_recalled", "F_future_row"}
    print(f"[test] n_candidates={res['n_candidates']} pick={res['fragment_id']} (expected pool {sorted(expected_candidates)})")
    failures = []
    if res["n_candidates"] != len(expected_candidates):
        failures.append(f"n_candidates {res['n_candidates']} != {len(expected_candidates)} -- the 14-day ledger rule "
                        f"did not bite (pre-J-1800 reads a key no row carries), the shadow skip is missing, "
                        f"or (J-1865) a row dated after hist_now wrongly excluded its fragment")
    if res["fragment_id"] not in expected_candidates:
        failures.append(f"picked {res['fragment_id']!r}, which the fixed rule should have excluded")
    if failures:
        for f in failures:
            print(f"[test] FAIL: {f}")
        return 1
    print(f"[test] PASS -- ids key read, legacy fragment_ids tolerated, *_shadow row skipped, >14d row ignored, row after hist_now ignored, "
          f"edge rule untouched (temp dir {tmp})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
