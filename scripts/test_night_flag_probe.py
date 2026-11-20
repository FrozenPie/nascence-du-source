"""scripts/test_night_flag_probe.py (J-2149 / F-2844): hermetic proof of the additive night flag probe.

Probe path is redirected to a temp dir (guard_path allows paths outside data/), sensorium.state is mutated in memory
only and restored, nothing is _save()d, core is imported FIRST and asserted to be this tree. Live data/ size-checked.
Run:  python scripts/test_night_flag_probe.py   (from the tree under test)
"""
from __future__ import annotations
import sys, tempfile, json, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE anything else
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import night, sensorium as sens

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

LIVE = ROOT / "data" / "night_flag_probe.jsonl"
live_before = LIVE.stat().st_size if LIVE.exists() else None
tmp = Path(tempfile.mkdtemp(prefix="j2149_"))
night._FLAG_PROBE = tmp / "night_flag_probe.jsonl"
night._LOG = tmp / "night_log.jsonl"
night.tick = lambda: None   # no sensorium tick in a hermetic test
orig = {k: sens.state.get(k, "<absent>") for k in ("asleep", "asleep_since")}

def rows():
    try:
        return [json.loads(l) for l in night._FLAG_PROBE.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []

try:
    sens.state["asleep"] = True; sens.state["asleep_since"] = 123.0
    night.begin("night")
    night.stage("consolidate", n=1)
    sens.state["asleep"] = False; sens.state.pop("asleep_since", None)   # simulated mid-sleep loss
    night.stage("dream")
    night.end()
    r = rows()
    check("4 rows: begin, 2 stages, end", [x["stage"] for x in r] == ["begin", "stage:consolidate", "stage:dream", "end"])
    check("asleep recorded true then false", [x["asleep"] for x in r] == [True, True, False, False])
    check("asleep_since recorded then None", r[0]["asleep_since"] == 123.0 and r[2]["asleep_since"] is None)
    check("id_state stable and equals id(state)", len({x["id_state"] for x in r}) == 1 and r[0]["id_state"] == id(sens.state))
    check("module list contains core.sensorium", all("core.sensorium" in x["sensorium_modules"] for x in r))
    check("fields present", all({"ts", "len_state", "last_save_age_s", "id_sensorium_module"} <= set(x) for x in r))
    check("stage still recorded in ledger", "consolidate" in night._current["stages"] and "dream" in night._current["stages"])
    check("night_log row written by end()", night._LOG.exists())

    # fail-open: unwritable probe path must not raise or alter behaviour
    night._FLAG_PROBE = tmp / "no_such" / "\0bad"
    try:
        night.stage("x"); night.begin("nap"); night.end()
        raised = False
    except Exception:
        raised = True
    check("fail-open on bad path", not raised)
    # fail-open: non-live write guard (default data/ path from a non-live importer)
    night._FLAG_PROBE = ROOT / "data" / "night_flag_probe.jsonl"
    try:
        night.stage("y"); raised = False
    except Exception:
        raised = True
    check("fail-open on guard_path refusal", not raised)
finally:
    for k, v in orig.items():
        if v == "<absent>": sens.state.pop(k, None)
        else: sens.state[k] = v

live_after = LIVE.stat().st_size if LIVE.exists() else None
check("live data/night_flag_probe.jsonl untouched", live_before == live_after)
print("ALL PASS" if ok_all else "FAILED")
sys.exit(0 if ok_all else 1)
