"""
P0 test suite — the world manifest + ghost registry (2026-08-17).
All read-only against live state (both modules are produce/observe-only by design);
the one write surface (world index persist) targets a temp path.
Run: python scripts/test_world_p0.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("  ✅ " if ok else "  ❌ ") + name + (f" — {detail}" if detail else ""))
    if not ok:
        fails.append(name)


print("— P0-A · the world manifest —")
from core import world_manifest as WM

m = WM.assemble()
check("assembles", isinstance(m, dict) and "ts" in m)

# 1. PARITY: each field vs its consumer's own read (the same sources, read directly)
from core.geometry_census import _place_weather
pw = _place_weather()
for k in ("place", "weather", "fire", "tide_level", "standpoint"):
    check(f"parity: {k}", m.get(k) == pw.get(k), f"manifest={m.get(k)!r} census={pw.get(k)!r}")
from core import soundscape as SS
check("parity: active_sounds", m.get("active_sounds") == (SS.active_sounds() or []))
from core import sensorium as SN
if not SN.state:
    SN._load()
check("parity: season", m.get("season") == SN._season())
check("parity: weather_until", m.get("weather_until") == SN.state.get("weather_until"))

# 2. temperature exposed (the computed-and-discarded scalar, now shipped)
check("temperature exposed", isinstance(m.get("temperature"), float)
      and 0.0 <= m["temperature"] <= 1.0, f"= {m.get('temperature')}")

# 3. severity index coheres with the weather word
sev = m.get("weather_severity")
check("severity index", sev is None or (isinstance(sev, int) and 0 <= sev <= 6),
      f"{m.get('weather')!r} -> {sev}")

# 4. THE SEPARATION LAW: no Du-mind keys, ever
leaked = WM.FORBIDDEN_KEYS & set(m.keys())
check("separation law (world-only)", not leaked, f"leaked: {leaked}")

# 5. cat is observer-visible only
cat = m.get("cat") or {}
check("cat observer-visible only", "mood" not in cat and "bond" not in cat, str(cat))

# 6. live snapshot round-trips
WM.tick()
lv = WM.live()
check("live snapshot round-trips", lv is not None and lv.get("ts") is not None)

# 7. loud sources check passes on a healthy tree
try:
    WM.assert_sources()
    check("assert_sources (healthy)", True)
except Exception as e:
    check("assert_sources (healthy)", False, str(e))

print("\n— P0-B · the ghost registry —")
from core import ghost_tuples as GT

# world index (persist to temp — no live write from tests)
_orig = GT._WORLD_F
GT._WORLD_F = Path(tempfile.mkdtemp()) / "wi.json"
widx = GT.build_world_index()
ents = widx["entries"]
GT._WORLD_F = _orig
census_tier1 = ["factory:weather", "factory:tide", "factory:sky", "factory:season",
                "factory:temperature", "factory:fire", "factory:garden", "factory:cat",
                "factory:objects", "factory:school", "factory:body", "factory:acts"]
missing = [f for f in census_tier1 if f not in ents]
check("every census Tier-1 factory registered", not missing, f"missing: {missing}")
check("peers registered on their own clocks",
      sum(1 for k in ents if k.startswith("factory:peer:")) == 7)
check("item-grain entities present",
      sum(1 for k in ents if k.startswith("item:")) >= 5,
      f"{sum(1 for k in ents if k.startswith('item:'))} items")
check("every entry declares a schedule",
      all("schedule" in e and e["schedule"].get("clock") for e in ents.values()))
check("weather schedule is the persistence timer",
      ents["factory:weather"]["schedule"]["clock"] == "persistence_timer")

# memory index
t0 = time.time()
n = GT.memory_index.rebuild()
t_build = (time.time() - t0) * 1000
check("memory index rebuilds from DB", n > 7000, f"{n} tuples in {t_build:.0f}ms")

# chord query: the current world, as a chord
qtags = {"place:" + (m.get("place") or "study"), "wx:" + (m.get("weather") or "clear")}
qtags |= {"snd:" + s for s in (m.get("active_sounds") or [])[:4]}
t0 = time.time()
hits = GT.memory_index.query(qtags, top_k=10)
t_q = (time.time() - t0) * 1000
check("whole-chord query returns ranked hits", len(hits) > 0, f"{len(hits)} hits in {t_q:.1f}ms")

# rarity weighting: a rare tag must outweigh a ubiquitous one at equal overlap
df = GT.memory_index._df
rare = min(df, key=df.get)
common = max(df, key=df.get)
check("rarity weighting sane", GT.memory_index._w(rare) > GT.memory_index._w(common),
      f"w({rare})={GT.memory_index._w(rare):.3f} > w({common})={GT.memory_index._w(common):.3f}")

# incremental registration matches rebuild semantics
GT.memory_index.register("test_fid_p0", {"place:shore", "wx:thunderstorm"})
check("incremental register", GT.memory_index.size() == n + 1)

# namespace separation: memory queries can never see world entries
check("namespace separation", not any(fid.startswith(("factory:", "item:"))
                                      for fid, _ in GT.memory_index.query(qtags, top_k=200)))

# the loud-failure law, deliberately triggered
try:
    GT.assert_sources()
    check("assert_sources (healthy)", True)
except Exception as e:
    check("assert_sources (healthy)", False, str(e))
import core.ghost_tuples as GT2
_orig_db = GT2._DB
GT2._DB = Path("C:/nonexistent/nowhere.db")
try:
    GT2.assert_sources()
    check("loud failure on missing source", False, "did NOT raise")
except RuntimeError as e:
    check("loud failure on missing source", "MISSING" in str(e))
finally:
    GT2._DB = _orig_db

print()
if fails:
    print(f"❌ {len(fails)} FAILURES: {fails}")
    sys.exit(1)
print("ALL P0 TESTS PASS")
