"""J-4442 (F-5157 / F-5128) test: the second batch of crash-zeroed state files now write durably (fsync + one
<name>.prev generation) and load through store_persist.read_json_durable (WARNING naming the file, fall back to
<name>.prev, the caller's own default when nothing is recoverable).

Covered: cat_state (core/cat.py), smell_field (core/smell.py), supply (core/supply.py), fieldcraft
(core/fieldcraft.py), world_manifest_live (core/world_manifest.py), transport_cause_lines
(core/transport_cause_shadow.py), climate_state (core/climate_engine.py), sound_knowledge (core/sound_knowledge.py),
frontier.light.json (core/frontier.py _write_light + open_count) and the light-sidecar helpers every light file uses
(core/light_sidecar.write_atomic / load: nodes/subconscious_node._write_light_sidecar, core/pursuits).

Temp paths only: every module path constant is pointed at a tempfile.mkdtemp() directory before any call, and the
test asserts core is imported from the tree this script sits in. Nothing under data/ is read or written.

Run from the repo root:  python scripts/_test_j4442_durable_state_files.py
"""
from __future__ import annotations

import json
import logging
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (import core BEFORE anything else that could touch sys.path)
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"

from core import store_persist as sp  # noqa: E402


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.rows: list[tuple[int, str]] = []

    def emit(self, record):
        self.rows.append((record.levelno, record.getMessage()))

    def warnings(self, needle: str) -> list[str]:
        return [m for lv, m in self.rows if lv >= logging.WARNING and needle in m]

    def clear(self):
        self.rows.clear()


CAP = _Cap()
logging.getLogger().addHandler(CAP)
logging.getLogger().setLevel(logging.DEBUG)

TMP = Path(tempfile.mkdtemp(prefix="j4442_"))
FAILS: list[str] = []
N = 0
PATHS: list[Path] = []


def check(cond: bool, what: str) -> None:
    global N
    N += 1
    if not cond:
        FAILS.append(what)
        print("FAIL", what)


def zero_fill(p: Path) -> None:
    size = p.stat().st_size
    with open(p, "r+b") as f:
        f.write(b"\x00" * size)


def module_case(name: str, set_path, save, load, first: dict, second: dict, pick=lambda d: d.get("marker"),
                default_pick=None):
    """Two saves (so .prev holds `first`), zero-fill the live file, load: must come back as `first` with a
    DAMAGED + RECOVERED warning naming the file. Then the no-.prev case: the caller's own default applies."""
    d = TMP / name
    d.mkdir()
    p = set_path(d)
    PATHS.append(p)
    check(str(p).startswith(str(TMP)), f"{name}: path redirected into temp ({p})")
    save(first)
    save(second)
    check(p.exists(), f"{name}: save wrote the file")
    check(sp.prev_path_for(p).exists(), f"{name}: .prev kept")
    check(not p.with_name(p.name + ".tmp").exists(), f"{name}: no .tmp left behind")
    zero_fill(p)
    CAP.clear()
    got = load()
    check(got is not None and pick(got) == first["marker"],
          f"{name}: zero-filled file falls back to .prev (got {pick(got) if got is not None else None!r})")
    w = CAP.warnings("STATE FILE DAMAGED")
    check(len(w) == 1 and str(p) in w[0], f"{name}: one DAMAGED warning naming the file ({len(w)})")
    check(len(CAP.warnings("STATE FILE RECOVERED")) == 1, f"{name}: RECOVERED warning")
    check(json.loads(p.read_text(encoding="utf-8")) is not None and p.read_bytes()[:1] != b"\x00",
          f"{name}: file restored on disk from .prev")
    # nothing recoverable: zero the file AND its .prev -> NOT RECOVERED warning, caller default (not a crash)
    zero_fill(p)
    zero_fill(sp.prev_path_for(p))
    CAP.clear()
    got2 = load()
    check(len(CAP.warnings("STATE FILE NOT RECOVERED")) == 1, f"{name}: NOT RECOVERED warning when .prev is bad too")
    if default_pick is not None:
        check(default_pick(got2), f"{name}: caller's own default applies when nothing is recoverable (got {got2!r})")


# ── cat_state ────────────────────────────────────────────────────────────────────────────────────────────────
from core import cat  # noqa: E402


def _cat_set(d):
    cat._STATE_F = d / "cat_state.json"
    return cat._STATE_F


def _cat_save(st):
    cat.state = dict(st)
    cat._save()


def _cat_load():
    cat.state = {}
    cat._state_mtime = 0.0
    return cat._load()


module_case("cat", _cat_set, _cat_save, _cat_load, {"marker": "one"}, {"marker": "two"},
            default_pick=lambda s: s.get("marker") is None and s.get("phase") == "appearing")

# ── smell / supply / fieldcraft / sound_knowledge: _F-style module stores ──────────────────────────────────
from core import smell, supply, fieldcraft, sound_knowledge  # noqa: E402

for mod, attr, fname, dflt in (
        (smell, "_F", "smell_field.json", lambda s: s == {"field": {}}),
        (supply, "_F", "supply.json", lambda s: "next_carrier_ts" in s and s.get("marker") is None),
        (fieldcraft, "_F", "fieldcraft.json", lambda s: "skill" in s and s.get("marker") is None),
        (sound_knowledge, "_LEDGER_F", "sound_knowledge.json", lambda s: s == {"sounds": {}, "recent": []})):
    def _set(d, mod=mod, attr=attr, fname=fname):
        setattr(mod, attr, d / fname)
        return getattr(mod, attr)
    module_case(mod.__name__.split(".")[-1], _set, mod._save, mod._load,
                {"marker": "one"}, {"marker": "two"}, default_pick=dflt)

# ── world_manifest_live ─────────────────────────────────────────────────────────────────────────────────────
from core import world_manifest as wm  # noqa: E402

_wm_next = {"m": None}
wm.assemble = lambda: dict(_wm_next["m"])            # no sensorium / census reads
wm._state["last_sample"] = time.time() + 1e9          # no sample-log append
wm._state["last_index"] = time.time() + 1e9           # no ghost world-index rebuild


def _wm_set(d):
    wm._LIVE_F = d / "world_manifest_live.json"
    wm._LOG_F = d / "world_manifest_log.jsonl"
    return wm._LIVE_F


def _wm_save(st):
    _wm_next["m"] = st
    wm.tick()


module_case("world_manifest", _wm_set, _wm_save, wm.live, {"marker": "one"}, {"marker": "two"},
            default_pick=lambda s: s is None)

# ── transport_cause_lines ───────────────────────────────────────────────────────────────────────────────────
from core import transport_cause_shadow as tcs  # noqa: E402


def _tcs_set(d):
    tcs._STATE = d / "transport_cause_lines.json"
    tcs._LOG = d / "transport_cause_shadow.jsonl"
    return tcs._STATE


def _tcs_save(st):
    tcs._state = dict(st)
    tcs._save(force=True)


def _tcs_load():
    tcs._state = None
    return tcs._get_state()


module_case("transport_cause_shadow", _tcs_set, _tcs_save, _tcs_load, {"marker": "one"}, {"marker": "two"},
            default_pick=lambda s: s == {"causes": {}})

# ── climate_state ───────────────────────────────────────────────────────────────────────────────────────────
from core import climate_engine as ce  # noqa: E402


def _ce_set(d):
    ce._DATA_DIR = d
    ce._STATE_FILE = d / "climate_state.json"
    return ce._STATE_FILE


def _ce_engine():
    e = ce.ClimateEngine.__new__(ce.ClimateEngine)   # no __init__: no orchestrator wiring, no ACTIVE swap
    e.field = ce.ClimateField()
    e.dissonance = ce.DissonanceState()
    e._ip_chronic = 0.0
    return e


def _ce_save(st):
    e = _ce_engine()
    e.dissonance.value = float(st["marker"])
    e._save()


def _ce_load():
    e = _ce_engine()
    e.dissonance.value = -1.0
    e._load()
    return {"marker": e.dissonance.value}


module_case("climate", _ce_set, _ce_save, _ce_load, {"marker": 0.25}, {"marker": 0.75},
            default_pick=lambda s: s["marker"] == -1.0)   # load failed -> the fresh-start state is kept

# ── frontier.light.json (frontier._write_light + open_count's light read) ───────────────────────────────────
from core import frontier as fr  # noqa: E402

fr.FRONTIER_LIGHT_READ = True


def _fr_set(d):
    fr._F = d / "frontier.json"          # heavy file never written: a fallback to it would read 0 open
    return fr._light_path()


def _fr_save(st):
    fr._write_light({"questions": [{"status": "open"}] * int(st["marker"])})


def _fr_load():
    return {"marker": fr.open_count()}


module_case("frontier_light", _fr_set, _fr_save, _fr_load, {"marker": 3}, {"marker": 5},
            default_pick=lambda s: s["marker"] == 0)       # light unusable -> heavy file (missing) -> 0, as before
check(not (TMP / "frontier_light" / "frontier.json").exists(), "frontier_light: heavy file was never written")

# ── light_sidecar helpers (subconscious_state.light.json, pursuits light) ──────────────────────────────────
from core import light_sidecar as ls  # noqa: E402

d = TMP / "light_sidecar"
d.mkdir()
lf = d / "subconscious_state.light.json"
check(ls.write_atomic(lf, {"marker": "one"}) is True, "write_atomic returns True")
check(ls.write_atomic(lf, {"marker": "two", "uni": "ō"}) is True, "write_atomic returns True (2)")
check(ls.load(lf) == {"marker": "two", "uni": "ō"}, "load reads a healthy light file (non-ascii kept)")
check("ō" in lf.read_text(encoding="utf-8"), "write_atomic still writes ensure_ascii=False")
zero_fill(lf)
CAP.clear()
check(ls.load(lf) == {"marker": "one"}, "zero-filled light file falls back to .prev")
check(len(CAP.warnings("STATE FILE DAMAGED")) == 1, "light: DAMAGED warning")
check(ls.load(d / "missing.light.json") is None, "missing light file -> None (caller falls back to heavy)")
zero_fill(lf)
zero_fill(sp.prev_path_for(lf))
check(ls.load(lf) is None, "nothing recoverable -> None (caller falls back to heavy, as before)")
check(ls.write_atomic(d / "sub" / "x.light.json", {"a": 1}) and (d / "sub" / "x.light.json").exists(),
      "write_atomic still creates the parent directory")

# the subconscious writer still goes through write_atomic (source check; the node is not imported here)
src = (ROOT / "nodes" / "subconscious_node.py").read_text(encoding="utf-8")
check("_ls.write_atomic(_LIGHT_FILE, light)" in src, "subconscious light writer uses light_sidecar.write_atomic")

# ── nothing landed in the tree's own data/ dir ─────────────────────────────────────────────────────────────
for p in PATHS:
    check(not str(p).startswith(str(ROOT / "data")), f"{p.name} path stayed in temp")

print(f"\nJ-4442 durable state test: {N - len(FAILS)}/{N} checks passed  (temp dir {TMP})")
sys.exit(1 if FAILS else 0)
