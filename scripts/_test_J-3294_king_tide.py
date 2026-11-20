"""Proof for J-3294 (F-3886, D-0668): pins the facts the king-tide analysis stands on, against THIS tree.
No Du code was changed by this job; the test fails if the code the numbers describe changes (then the numbers need re-running).

  [1] world_objects.move_tick still gates on tide_level >= 0.92, rolls 0.08 per floater, and is called from exactly one site
      (sensorium._advance_weather, weather-change branch only), and its returned prose is discarded there.
  [2] world_clock.tide() over 2026 (10-min steps) reproduces F-3886: share at >=0.92 within 12.1-13.1 percent, days_with_any >= 330.
  [3] threshold what-if ordering: share falls monotonically with the threshold; 0.995 stays under 1 percent, 0.99 above it.
  [4] the analysis scripts compile; the test reads no live data and writes nothing.

  python scripts/_test_J-3294_king_tide.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import datetime as dt
import py_compile
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import core  # noqa: E402,F401  (before any lab_env use)
from core import world_clock as wc  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not ok:
        FAILS.append(name)


wo = (ROOT / "core" / "world_objects.py").read_text(encoding="utf-8")
sens = (ROOT / "core" / "sensorium.py").read_text(encoding="utf-8")
# J-4052 re-pin: J-3797 moved the bare `tide_level >= 0.92` behind king_tide_now(); with the gate flag OFF (default) the
# legacy threshold is the same 0.92, kept as KING_TIDE_LEGACY_THRESHOLD.
check("[1a] king threshold 0.92 (legacy, gate OFF) in move_tick", "KING_TIDE_LEGACY_THRESHOLD = 0.92" in wo and "king = king_tide_now(None, tide_level)" in wo)
check("[1b] per-floater roll 0.08", "rng.random() < 0.08" in wo)
callers = [str(p.relative_to(ROOT)) for p in list((ROOT / "core").rglob("*.py")) + list((ROOT / "nodes").rglob("*.py"))
           if "move_tick(" in p.read_text(encoding="utf-8", errors="ignore") and p.name != "world_objects.py"]
check("[1c] exactly one call site (sensorium.py)", [c.replace("\\", "/") for c in callers] == ["core/sensorium.py"], str(callers))
# J-4052 re-pin: J-3797 binds the result (`_ev2 = ...`) but it is only used to queue a heard sound when the gate flag is ON;
# the returned prose is still never announced as a percept.
check("[1d] returned prose never announced (only used for the flag-gated heard sound)", re.search(r"^\s+_ev2 = _wo2\.move_tick\(", sens, re.M) is not None
      and "pending_world_sound" in sens and "KING_TIDE_GATE_ENABLED" in sens)


def sweep(T, step=600.0):
    t0, t1 = dt.datetime(2026, 1, 1).timestamp(), dt.datetime(2027, 1, 1).timestamp()
    n = hit = 0
    days = set()
    t = t0
    while t < t1:
        if wc.tide(t)["level"] >= T:
            hit += 1
            days.add(dt.datetime.fromtimestamp(t).date())
        n += 1
        t += step
    return hit / n, len(days)


s92, d92 = sweep(0.92)
check("[2] 2026 share at >=0.92 reproduces F-3886 (12.1-13.1 pct, >=330 days)", 0.121 <= s92 <= 0.131 and d92 >= 330,
      f"share={s92:.4f} days={d92}")
s99, _ = sweep(0.99)
s995, _ = sweep(0.995)
check("[3] monotone and 0.995 under 1 pct, 0.99 over 1 pct", s92 > s99 > s995 and s995 < 0.01 < s99, f"{s92:.4f} {s99:.4f} {s995:.4f}")
for p in ("docs/lab/J-3294_data/king_tide_rate.py", "docs/lab/J-3294_data/exposure.py"):
    try:
        py_compile.compile(str(ROOT / p), doraise=True)
        check(f"[4] compiles {p}", True)
    except Exception as e:
        check(f"[4] compiles {p}", False, str(e))
print("ALL OK" if not FAILS else f"{len(FAILS)} FAILED: {FAILS}")
sys.exit(1 if FAILS else 0)
