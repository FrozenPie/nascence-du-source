"""J-4426 (F-5128) test: durable state writes keep one .prev generation, and a zero-filled / empty / unparseable
state file logs a WARNING naming the file and falls back to <name>.prev before defaults.

Temp paths only: every module path constant is pointed at a tempfile.mkdtemp() directory before any call, and the
test asserts core is imported from the tree this script sits in. Nothing under data/ is read for the checks or
written at all (profile.guard_path refuses a non-live write there anyway).

Run from the repo root:  python scripts/_test_j4426_durable_state_files.py
"""
from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
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

TMP = Path(tempfile.mkdtemp(prefix="j4426_"))
FAILS: list[str] = []
N = 0


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


def corrupt_files(d: Path) -> list[Path]:
    return sorted(d.glob("*.corrupt.*"))


ALLOW = lambda p: p  # noqa: E731  (a guard that lets this process write the temp path)


def deny(p):
    raise PermissionError("read-only process")


# ── 1. helper-level ──────────────────────────────────────────────────────────────────────────────────────────
d1 = TMP / "unit"
d1.mkdir()
f = d1 / "state.json"
sp.write_text_durable(f, json.dumps({"gen": 1}))
check(not sp.prev_path_for(f).exists(), "first write has no .prev (nothing to keep)")
sp.write_text_durable(f, json.dumps({"gen": 2}))
check(json.loads(f.read_text()) == {"gen": 2}, "path holds gen 2")
check(json.loads(sp.prev_path_for(f).read_text()) == {"gen": 1}, ".prev holds gen 1 after the second write")
sp.write_text_durable(f, json.dumps({"gen": 3}))
check(json.loads(sp.prev_path_for(f).read_text()) == {"gen": 2}, ".prev advances one generation (gen 2)")
check(not (d1 / "state.json.tmp").exists() and not (d1 / "state.json.prev.tmp").exists(), "no tmp files left")

# zero-fill -> warning + recovery from .prev, file restored on disk, damaged one kept aside
CAP.clear()
zero_fill(f)
v = sp.read_json_durable(f, "unit", guard=ALLOW)
check(v == {"gen": 2}, f"zero-filled file recovers .prev value (got {v})")
check(len(CAP.warnings("STATE FILE DAMAGED")) == 1 and str(f) in CAP.warnings("STATE FILE DAMAGED")[0],
      "one DAMAGED warning naming the file")
check("all NUL" in CAP.warnings("STATE FILE DAMAGED")[0], "warning says all NUL")
check(len(CAP.warnings("STATE FILE RECOVERED")) == 1, "one RECOVERED warning")
check(json.loads(f.read_text()) == {"gen": 2}, "file on disk restored from .prev")
check(len(corrupt_files(d1)) == 1 and corrupt_files(d1)[0].read_bytes().count(0) > 0, "damaged file moved aside")
check(json.loads(sp.prev_path_for(f).read_text()) == {"gen": 2}, ".prev untouched by the restore")

# a damaged file is never rotated into .prev by the next save
zero_fill(f)
sp.write_text_durable(f, json.dumps({"gen": 4}))
check(json.loads(sp.prev_path_for(f).read_text()) == {"gen": 2}, "NUL file was not rotated into .prev")
check(json.loads(f.read_text()) == {"gen": 4}, "save after damage writes gen 4")

# empty and unparseable both recover
for label, bad in (("empty", b""), ("unparseable", b'{"gen": 4, "tru')):
    sp.write_text_durable(f, json.dumps({"gen": 5}))           # prev = gen 4
    f.write_bytes(bad)
    CAP.clear()
    v = sp.read_json_durable(f, "unit", guard=ALLOW)
    check(v == {"gen": 4}, f"{label} file recovers .prev (got {v})")
    check(len(CAP.warnings("STATE FILE DAMAGED")) == 1, f"{label}: DAMAGED warning")

# read-only process: value from .prev, file left alone, warned once only
sp.write_text_durable(f, json.dumps({"gen": 6}))                # prev = gen 4 (restored file) -> rotated
prev_val = json.loads(sp.prev_path_for(f).read_text())
zero_fill(f)
before = len(corrupt_files(d1))
CAP.clear()
v1 = sp.read_json_durable(f, "unit", guard=deny)
v2 = sp.read_json_durable(f, "unit", guard=deny)
check(v1 == prev_val and v2 == prev_val, "read-only process gets the .prev value")
check(f.read_bytes().count(0) == f.stat().st_size, "read-only process leaves the damaged file in place")
check(len(corrupt_files(d1)) == before, "read-only process moves nothing")
check(len(CAP.warnings("STATE FILE DAMAGED")) == 1, "read-only: warned once, not on every read")

# no usable .prev -> warning, moved aside, ValueError (caller default)
g = d1 / "lonely.json"
g.write_bytes(b"\x00" * 100)
CAP.clear()
try:
    sp.read_json_durable(g, "unit", guard=ALLOW)
    check(False, "no .prev: should raise")
except ValueError:
    check(True, "no .prev: raises ValueError")
check(len(CAP.warnings("STATE FILE NOT RECOVERED")) == 1, "no .prev: NOT RECOVERED warning")
check(not g.exists(), "no .prev: damaged file moved aside (cannot reach .prev later)")

# missing file stays a silent FileNotFoundError (a deliberate reset is not undone)
CAP.clear()
try:
    sp.read_json_durable(d1 / "missing.json", "unit", guard=ALLOW)
    check(False, "missing: should raise")
except FileNotFoundError:
    check(True, "missing raises FileNotFoundError")
check(not CAP.warnings("STATE FILE"), "missing file: no warning")

# write_text_atomic still works (fsync added)
h = d1 / "atomic.json"
sp.write_text_atomic(h, json.dumps({"ok": 1}))
check(json.loads(h.read_text()) == {"ok": 1}, "write_text_atomic still writes")


# ── 2. module-level: every converted store, zero-filled after two saves ────────────────────────────────────
def module_case(name: str, set_path, save, load, first: dict, second: dict, pick=lambda d: d.get("marker")):
    d = TMP / name
    d.mkdir()
    p = set_path(d)
    save(first)
    save(second)
    check(sp.prev_path_for(p).exists(), f"{name}: .prev kept")
    zero_fill(p)
    CAP.clear()
    got = load()
    check(pick(got) == first["marker"], f"{name}: zero-filled file falls back to .prev (got {pick(got)!r})")
    w = CAP.warnings("STATE FILE DAMAGED")
    check(len(w) == 1 and str(p) in w[0], f"{name}: DAMAGED warning names the file")
    check(len(CAP.warnings("STATE FILE RECOVERED")) == 1, f"{name}: RECOVERED warning")


from core import spring_ledger, opponent_process, life, transport_manager, garden_life, shore_life, wood_life  # noqa: E402
from core import sensorium  # noqa: E402

for mod in (spring_ledger, opponent_process):
    def _set(d, mod=mod):
        mod._STATE = d / Path(mod._STATE).name
        mod._STORE = sp.CoalescedJsonStore(mod.__name__, logging.getLogger("t"))
        return mod._STATE
    module_case(mod.__name__.split(".")[-1], _set,
                lambda st, mod=mod: mod._write_now(mod._STATE, st),
                lambda mod=mod: mod._read_disk(mod._STATE),
                {"marker": "one"}, {"marker": "two"})


def _life_set(d):
    life._F = d / "life_state.json"
    return life._F


def _life_save(st):
    life._state = dict(st)
    life._save(force=True)


def _life_load():
    life._state = {}
    return life._load()


module_case("life", _life_set, _life_save, _life_load, {"marker": "one"}, {"marker": "two"})


def _tm_set(d):
    transport_manager._STATE = d / "transport_lines.json"
    return transport_manager._STATE


module_case("transport_manager", _tm_set, transport_manager._save, transport_manager._load,
            {"marker": "one"}, {"marker": "two"})


def _sens_set(d):
    sensorium._STATE_F = d / "room_state.json"
    return sensorium._STATE_F


def _sens_save(st):
    sensorium.state = dict(st)
    sensorium._last_save = 0.0
    sensorium._save()


def _sens_load():
    sensorium._load()
    return sensorium.state


module_case("sensorium", _sens_set, _sens_save, _sens_load, {"marker": "one"}, {"marker": "two"})

for mod, fname in ((garden_life, "garden_life.json"), (shore_life, "shore_life.json"), (wood_life, "wood_life.json")):
    def _set(d, mod=mod, fname=fname):
        mod._F = d / fname
        return mod._F
    module_case(mod.__name__.split(".")[-1], _set, mod._save, mod._load,
                {"marker": "one", "items": {}}, {"marker": "two", "items": {}})

# no module wrote into the real data/ dir from this test
for mod in (spring_ledger, opponent_process, transport_manager):
    check(not str(mod._STATE).startswith(str(ROOT / "data")), f"{mod.__name__} path stayed in temp")

print(f"\nJ-4426 durable state test: {N - len(FAILS)}/{N} checks passed  (temp dir {TMP})")
sys.exit(1 if FAILS else 0)
