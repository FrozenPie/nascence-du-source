"""
Nascence — Headless Cat Ecological Laboratory (Task 4 Harness)
================================================================
Pure physical simulation testing for autonomous cat locomotion, 3D coordinates,
substrate-conditioned traces, fur moisture response functions, and reboot persistence.
ZERO LLM calls | ZERO prompt contamination.
"""
import os
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import cat, world_traces

# ISOLATION (2026-08-19, health-check finding): this harness used to delete the LIVE
# world_traces.json and overwrite the LIVE cat_state.json (fabricated location/bond/moisture),
# with no sandboxing at all — a real hazard if ever run while Du is up, or even stopped, since
# it clobbers his actual companion state. Redirect both modules' file path constants into a lab
# dir first, matching this codebase's other isolated lab scripts (lane2_lab.py, etc.) — nothing
# below this point touches data/cat_state.json or data/world_traces.json.
#
# LAB DIR MOVED OUTSIDE data/ (2026-09-07, J-0733, F-1055's own follow-up): the old lab dir
# (data/lab/cat_ecological_lab/) is still a subpath of data/ — harmless before core/cat.py had any
# write-fence protection, but core.cat._save() now resolves profile.guard_path(_STATE_F) first
# (J-0733), which raises NonLiveWriteError for any path under data/ unless the process called
# profile.mark_live() (D-0179) — this script never does, deliberately (it is a pure offline
# simulation harness, not the real live boot). A data/-relative "lab" dir is NOT the same thing as
# "outside data/" to guard_path()'s own check (path.relative_to(_DATA) still succeeds), so the old
# location would have made every cat._save() call in this file raise the moment the guard landed.
# tempfile.mkdtemp() — a real OS temp dir, genuinely outside data/ — is the same pattern this
# codebase's OWN scripts/_test_*_grammar_derivation.py / _test_dispatch_family_scope.py /
# _test_dark_house_answers.py already use for every OTHER already-fenced module's isolation, not a
# new convention invented here. (lab_env.py's isolate() was considered too — it is job-queue's own
# sanctioned isolation helper — but its lab dir is ALSO under data/_lab/, so it has the identical
# gap; not used here for that reason. See this job's own finding for the full verified detail.)
#
# UPDATE (2026-09-12, J-0862, post-D-0200): the "identical gap" named just above is fixed now —
# D-0200 (J-0840, F-1225) taught profile.guard_path() to explicitly allow-list data/_lab/<dir>/...,
# so lab_env.isolate()'s lab dir genuinely clears the fence today (confirmed empirically: J-0862
# removed the equivalent guard_path mock.patch workaround from scripts/_test_practical_lesson.py and
# re-ran it clean, 34/34, zero NonLiveWriteError). This script is NOT migrated to lab_env.isolate()
# by that fix alone, on purpose, out of scope for J-0862's own narrow ask (update this comment, not
# change the isolation mechanism) — tempfile.mkdtemp() still works exactly as before and needs no
# change; a future job may revisit whether switching brings any real benefit (matching this file's
# own convention of also getting lab_env's DB-copy machinery, which this script never uses).
_LAB_DIR = Path(tempfile.mkdtemp(prefix="cat_ecological_lab_"))
cat._STATE_F = _LAB_DIR / "cat_state.json"
world_traces._TRACES_F = _LAB_DIR / "world_traces.json"

print("=================================================================")
print("  NASCENCE HEADLESS CAT ECOLOGICAL LABORATORY (TASK 4 HARNESS)   ")
print("  No LLM | No Chat | Pure Autonomous Biological Simulation       ")
print(f"  Isolated to: {_LAB_DIR}")
print("=================================================================\n")

# 0. Clean reset of traces and cat state (lab copies only)
world_traces._traces_cache.clear()
if world_traces._TRACES_F.exists():
    world_traces._TRACES_F.unlink()

cat._load()
cat.state["phase"] = "companion"
cat.state["bond"] = 0.85
cat.state["location"] = "study"
cat.state["position"] = [0.0, 0.0, 0.0]
cat.state["fur_moisture"] = 0.0
cat.state["last_fur_decay_ts"] = time.time()
cat._save()

# --- TEST A: Substrate-Conditioned Trace Creation & Process Decay ---
print("🔬 RUNNING TEST A — Substrate-Conditioned Trace Creation & Process Decay...")
now = time.time()

# Force wet shore visit
cat.state["location"] = "shore"
cat.state["position"] = [8.0, 2.5, 0.1]
cat._save()

# Create substrate trace
tr_shore = world_traces.create_trace(
    trace_id=f"cat_paw_{int(now)}",
    trace_type="cat_paw_print",
    location="shore",
    position=[8.0, 2.5, 0.1],
    clarity=0.9,
    cause="stray_cat_locomotion"
)

# Move cat to wood
tr_wood = world_traces.create_trace(
    trace_id=f"cat_leaf_{int(now)}",
    trace_type="disturbed_leaf_litter",
    location="wood",
    position=[0.0, 45.0, 2.0],
    clarity=0.85,
    cause="stray_cat_hunting"
)

active_shore = world_traces.get_active_traces("shore")
active_wood = world_traces.get_active_traces("wood")
print(f"   Post-Locomotion Active Shore Traces: {len(active_shore)} (Cause: {tr_shore['cause']})")
print(f"   Post-Locomotion Active Wood Traces:  {len(active_wood)} (Cause: {tr_wood['cause']})")

assert len(active_shore) == 1 and len(active_wood) == 1, "Test A Locomotion Traces Failed!"

# Apply high tide wash to shore
world_traces.advance_trace_decay(weather="clear", tide="high", dt_hours=1.5)
post_tide_shore = world_traces.get_active_traces("shore")
post_tide_wood = world_traces.get_active_traces("wood")

print(f"   Post-Tide Shore Traces: {len(post_tide_shore)} (Erased by high tide!)")
print(f"   Post-Tide Wood Traces:  {len(post_tide_wood)} (Persists under canopy!)")

assert len(post_tide_shore) == 0 and len(post_tide_wood) == 1, "Test A Process Decay Failed!"
print("   ✅ Test A PASSED!\n")

# --- TEST B: Fur Moisture Response Function & Cross-Boundary State Carry-Over ---
print("🔬 RUNNING TEST B — Fur Moisture Response Function & Cross-Boundary State Carry-Over...")

# Step 1: Cat exposed to rain outdoors
cat.state["location"] = "shore"
cat.state["fur_moisture"] = 1.0  # Fully soaked in rain
cat.state["last_fur_decay_ts"] = now
cat._save()
print(f"   [Outdoors Rain] Location: {cat.state['location']} | Fur Moisture: {cat.state['fur_moisture']}")

# Step 2: Cat returns indoors to burning hearth
cat.state["location"] = "by_the_fire"
cat.state["position"] = [0.5, 0.5, 0.0]
cat._save()

# Simulate 15 minutes (0.25h) drying near burning hearth (half-life = 15m, decay_rate = 2.77/h)
dry_dt = now + (15 * 60)  # +15 minutes
last_decay = cat.state["last_fur_decay_ts"]
dt_hours = (dry_dt - last_decay) / 3600.0
decay_rate = 2.77  # hearth acceleration
cat.state["fur_moisture"] = max(0.0, round(cat.state["fur_moisture"] - decay_rate * dt_hours, 2))
cat.state["last_fur_decay_ts"] = dry_dt
cat._save()

print(f"   [Indoors +15m Hearth] Location: {cat.state['location']} | Fur Moisture: {cat.state['fur_moisture']}")
print(f"   [Presence Line Texture]: \"{cat.presence_line('study')}\"")

assert 0.25 <= cat.state["fur_moisture"] <= 0.40, "Test B Damp Fur Calculation Failed!"
assert "damp with rain" in cat.presence_line("study"), "Test B Presence Line Texture Failed!"
print("   ✅ Test B PASSED!\n")

# --- TEST C: Non-Interference & Reboot Persistence ---
print("🔬 RUNNING TEST C — Non-Interference & Reboot Persistence...")

# Purge cache and reload
cat.state.clear()
cat._load()

print(f"   Post-Reboot Location:  {cat.state['location']}")
print(f"   Post-Reboot Position:  {cat.state['position']}")
print(f"   Post-Reboot Moisture:  {cat.state['fur_moisture']}")

assert cat.state["location"] == "by_the_fire", "Test C Reboot Location Failed!"
assert cat.state["position"] == [0.5, 0.5, 0.0], "Test C Reboot Position Failed!"
assert 0.25 <= cat.state["fur_moisture"] <= 0.40, "Test C Reboot Moisture Failed!"
print("   ✅ Test C PASSED!\n")

print("=================================================================")
print("  ALL ECOLOGICAL CAT LABORATORY TESTS PASSED PERFECTLY!          ")
print("=================================================================")

