"""
Test suite — TEMPERATURE + CAT LOCATION dimension stamps (2026-08-17).

Covers the three additive changes:
  1. geometry_census.py: _warmth() / _cat_at() feed the tuple, fail-open, never raise.
  2. memory_edges.py: fragment_context gains warmth/cat_at columns via an idempotent ALTER TABLE.
  3. ghost_tuples.py: _tuple_tags() emits the new coarse tags and omits them on None.

Discipline: everything mutable is temp-pathed. The deliberate live reads are data/room_state.json
via sensorium._load() (sections 1-3 below only) and data/cat_state.json (read-only json load,
skipped cleanly rather than failed when the file is simply absent — e.g. a throwaway worktree with
no accumulated live data, F-1170/F-1231) — both permitted as read-only checks against live stores.

ISOLATION (J-0869, 2026-09-12, closing F-1231's "5th script" gap): section 4's GC.snapshot() call
reaches, via _light_band_truth() -> light.field_at() -> study_life.lamp_on() -> _st(), the identical
5-module write chain J-0830 isolated in the other 4 regression scripts (provisions.py/study_life.py/
world_objects.py/world_substrate.py/locomotion.py), plus geometry_census's own arousal shadow row
and core.watershed's unfenced cognitive shadow — all temp-pathed for that one call only, applied
right before it (not at file top like those 4 scripts) so sections 1-3 above are never disturbed.
sensorium itself is deliberately NOT given that same blind _STATE_F swap: _st() can call
sensorium._save()/_save_now() unconditionally on whatever state is already loaded (three additive
migrations — item J-0422, book items J-0851/D-0205, candles rename F-0785 — each already
hard-raising NonLiveWriteError rather than swallowing it, J-0760/F-1086), so the already-loaded live
state is instead snapshotted into a temp-pathed copy of _STATE_F (the read-only-copy technique
J-0793/F-1177 used for position.json) immediately before the call. Nothing under data/memory/ is
touched, nothing is ever written to a live path.

Run: python scripts/test_dimension_stamps.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("  [OK] " if ok else "  [FAIL] ") + name + (f" — {detail}" if detail else ""))
    if not ok:
        fails.append(name)


print("— dimension stamps: geometry_census —")
from core import geometry_census as GC
from core import sensorium as SN

# 1. _warmth() never raises, and returns float|None, with sensorium state ALREADY loaded
if not SN.state:
    SN._load()
w_loaded = GC._warmth()
check("_warmth() no-raise, loaded state", True)
check("_warmth() type float|None (loaded)", w_loaded is None or isinstance(w_loaded, float),
      f"= {w_loaded!r}")
if isinstance(w_loaded, float):
    check("_warmth() in [0,1] (loaded)", 0.0 <= w_loaded <= 1.0, f"= {w_loaded}")

# 2. _warmth() never raises when sensorium state is NOT yet loaded (the guard's whole job) —
# reset the module's in-process state to {} (this test process only; the live Du process is
# untouched) and confirm _warmth()'s internal `if not _s.state: _s._load()` guard recovers it.
_saved_state = dict(SN.state)
SN.state = {}
try:
    w_unloaded = GC._warmth()
    raised = False
except Exception as exc:
    w_unloaded = None
    raised = True
finally:
    SN.state = _saved_state  # restore in-process state exactly as we found it
check("_warmth() no-raise, unloaded state", not raised)
check("_warmth() type float|None (unloaded)", w_unloaded is None or isinstance(w_unloaded, float),
      f"= {w_unloaded!r}")

# 3. _cat_at(): str|None, never raises, matches live cat_state.json phase gate
cat_at = GC._cat_at()
check("_cat_at() no-raise", True)
check("_cat_at() type str|None", cat_at is None or isinstance(cat_at, str), f"= {cat_at!r}")
_cat_state_path = ROOT / "data" / "cat_state.json"
if not _cat_state_path.exists():
    # J-0869/F-1231: absent (not corrupt) is the expected state of a throwaway/fresh worktree's own
    # git-ignored data/ dir -- this check needs real accumulated live data to mean anything (F-1170),
    # so skip cleanly rather than count a fresh tree as a FAILure. A real Nascence tree that has run
    # live still hits the try/check below exactly as before.
    print("  [SKIP] _cat_at() matches live phase gate — no live data/cat_state.json in this tree")
else:
    try:
        raw_cat = json.loads(_cat_state_path.read_text(encoding="utf-8"))
        expected = raw_cat.get("location") if raw_cat.get("phase") in ("kept", "companion") else None
        check("_cat_at() matches live phase gate", cat_at == expected,
              f"cat_at={cat_at!r} expected={expected!r} phase={raw_cat.get('phase')!r}")
    except Exception as exc:
        check("_cat_at() matches live phase gate", False, f"read failed: {exc}")

# 4. snapshot() carries both fields additively (temp-path the log so nothing live is appended).
# ISOLATION (J-0869, F-1231's "5th script" gap) -- see module docstring for the full mechanism.
# No hasattr() guards on purpose (F-1198): a stale attribute name here should fail loudly, not
# silently un-redirect.
_TMP = Path(tempfile.mkdtemp(prefix="dimension_stamps_test_"))
_orig_log = GC._LOG
GC._LOG = _TMP / "geometry_tuples_test.jsonl"
if not SN.state:
    SN._load()
(_TMP / "room_state.json").write_text(json.dumps(SN.state), encoding="utf-8")
_orig_state_f = SN._STATE_F
SN._STATE_F = _TMP / "room_state.json"          # a live-seeded COPY -- see docstring; not a fresh-state swap
import core.study_life as _sl
_orig_ledger, _orig_events = _sl._LEDGER, _sl._EVENTS
_sl._LEDGER, _sl._EVENTS = _TMP / "study_ledger.jsonl", _TMP / "study_events.jsonl"
import core.provisions as _pv
_orig_pv_f, _orig_pv_log = _pv._F, _pv._LOG
_pv._F, _pv._LOG = _TMP / "provisions.json", _TMP / "provisions_log.jsonl"
import core.world_objects as _wo
_orig_wo_f, _orig_wo_cache, _orig_wo_last = _wo._OBJECTS_F, _wo._objects_cache, _wo._last_load
_wo._OBJECTS_F = _TMP / "world_objects.json"
_wo._objects_cache, _wo._last_load = {}, 0.0
import core.world_substrate as _ws
_orig_ws_f, _orig_ws_log, _orig_ws_looked = _ws._SUBSTRATE_F, _ws._SUBSTRATE_LOG, _ws._LAST_LOOKED_F
_orig_ws_cache, _orig_ws_cache_ts = _ws._cache, _ws._cache_ts
_ws._SUBSTRATE_F = _TMP / "world_substrate.json"
_ws._SUBSTRATE_LOG = _TMP / "world_substrate_events.jsonl"
_ws._LAST_LOOKED_F = _TMP / "world_substrate_last_looked.json"
_ws._cache, _ws._cache_ts = {}, 0.0
import core.locomotion as _loco
_orig_pos_f = _loco._POS_F
_loco._POS_F = _TMP / "position.json"
import core.arousal as _ar
_orig_ar_data, _orig_ar_state, _orig_ar_log = _ar._DATA, _ar._STATE, _ar._LOG
_ar._DATA, _ar._STATE, _ar._LOG = _TMP, _TMP / "arousal_state.json", _TMP / "arousal_shadow.jsonl"
import core.watershed as _wshed
_orig_wshed_data = _wshed._DATA
_wshed.configure(data_dir=_TMP)
try:
    row = GC.snapshot(source="test", thought="a dimension-stamp probe thought, long enough to pass "
                                             "the debounce and any length gate elsewhere in the pipe")
    check("snapshot() returns a row", isinstance(row, dict))
    check("snapshot() carries 'warmth' key", row is not None and "warmth" in row)
    check("snapshot() carries 'cat_at' key", row is not None and "cat_at" in row)
    # additive: none of the pre-existing keys were displaced
    for k in ("ts", "source", "place", "weather", "objects", "body", "affect", "thought", "level"):
        check(f"snapshot() still has '{k}'", row is not None and k in row)
finally:
    GC._LOG = _orig_log
    SN._STATE_F = _orig_state_f
    _sl._LEDGER, _sl._EVENTS = _orig_ledger, _orig_events
    _pv._F, _pv._LOG = _orig_pv_f, _orig_pv_log
    _wo._OBJECTS_F, _wo._objects_cache, _wo._last_load = _orig_wo_f, _orig_wo_cache, _orig_wo_last
    _ws._SUBSTRATE_F, _ws._SUBSTRATE_LOG, _ws._LAST_LOOKED_F = _orig_ws_f, _orig_ws_log, _orig_ws_looked
    _ws._cache, _ws._cache_ts = _orig_ws_cache, _orig_ws_cache_ts
    _loco._POS_F = _orig_pos_f
    _ar._DATA, _ar._STATE, _ar._LOG = _orig_ar_data, _orig_ar_state, _orig_ar_log
    _wshed.configure(data_dir=_orig_wshed_data)

print("\n— dimension stamps: memory_edges (idempotent ALTER TABLE) —")
import core.memory_edges as ME

tmp_dir = Path(tempfile.mkdtemp())
tmp_tuples = tmp_dir / "geometry_tuples.jsonl"
tmp_tuples.write_text("", encoding="utf-8")   # empty log: exercises the schema/ALTER path, then
                                               # returns cleanly before touching memory_fragments
tmp_db = tmp_dir / "fragment_context_test.db"

# seed the OLD schema — everything up to (and including) 'standpoint', but WITHOUT warmth/cat_at,
# mirroring a real pre-migration fragment_context table
seed = sqlite3.connect(str(tmp_db))
seed.execute("""
CREATE TABLE IF NOT EXISTS fragment_context (
    fragment_id TEXT PRIMARY KEY,
    tuple_ts    REAL,
    source      TEXT,
    place       TEXT,
    weather     TEXT,
    weather_dir REAL,
    fire        TEXT,
    tide_level  REAL,
    sun_az      REAL,
    moon_illum  REAL,
    level       REAL,
    valence     REAL,
    arousal     REAL,
    sounds      TEXT,
    standpoint  TEXT
);
""")
seed.commit()
seed.close()


def _temp_connect():
    c = sqlite3.connect(str(tmp_db))
    c.row_factory = sqlite3.Row
    return c


_orig_data, _orig_connect = ME._DATA, ME._connect
ME._DATA = tmp_dir
ME._connect = _temp_connect
migration_raised = None
try:
    r1 = ME.sync_fragment_context()
    r2 = ME.sync_fragment_context()   # second run — must be idempotent (duplicate ALTER swallowed)
except Exception as exc:
    migration_raised = exc
finally:
    ME._DATA, ME._connect = _orig_data, _orig_connect

check("sync_fragment_context() x2 does not raise", migration_raised is None, repr(migration_raised))

check_conn = sqlite3.connect(str(tmp_db))
cols = {row[1] for row in check_conn.execute("PRAGMA table_info(fragment_context)")}
check_conn.close()
check("migration added 'warmth' column", "warmth" in cols, f"cols={sorted(cols)}")
check("migration added 'cat_at' column", "cat_at" in cols, f"cols={sorted(cols)}")
check("pre-existing 'standpoint' column untouched", "standpoint" in cols)

print("\n— dimension stamps: ghost_tuples tags —")
from core import ghost_tuples as GT

t_warm = GT._tuple_tags({"warmth": 0.85, "cat_at": "windowsill"})
check("warm band tag", "warmth:warm" in t_warm, str(t_warm))
check("cat tag present", "cat:windowsill" in t_warm, str(t_warm))

t_mild = GT._tuple_tags({"warmth": 0.5})
check("mild band tag", "warmth:mild" in t_mild, str(t_mild))
check("no cat tag when cat_at absent", not any(t.startswith("cat:") for t in t_mild), str(t_mild))

t_cold = GT._tuple_tags({"warmth": 0.1})
check("cold band tag", "warmth:cold" in t_cold, str(t_cold))

t_none = GT._tuple_tags({"place": "study"})
check("no warmth tag when warmth is None", not any(t.startswith("warmth:") for t in t_none), str(t_none))
check("no cat tag when cat_at is None", not any(t.startswith("cat:") for t in t_none), str(t_none))
check("pre-existing place tag still works", "place:study" in t_none, str(t_none))

print()
if fails:
    print(f"[FAIL] {len(fails)} FAILURES: {fails}")
    sys.exit(1)
print("ALL DIMENSION-STAMP TESTS PASS")
