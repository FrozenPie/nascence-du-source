"""scripts/test_stall_attribution.py (J-2141, F-2825): hermetic proof of the stall-attribution sub-marks.
No LLM, no live data: the attribution log is temp-pathed. Run from the tree under test."""
from __future__ import annotations
import ast, asyncio, json, sys, tempfile, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import sleep_phase0 as sp0

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

tmp = Path(tempfile.mkdtemp(prefix="j2141_"))
LIVE = ROOT / "data" / "night_stall_attribution.jsonl"
live_before = LIVE.stat().st_size if LIVE.exists() else None
sp0.STALL_ATTRIBUTION_LOG = tmp / "night_stall_attribution.jsonl"
sp0.STALL_S = 0.3

async def scenario():
    hb = sp0.SleepHeartbeat(interval=0.05, shadow=False)
    hb.start()
    await asyncio.sleep(0.15)
    hb.mark("replay")
    sp0.submark("affections")
    time.sleep(0.6)                  # inline block: the loop stalls here
    await asyncio.sleep(0.15)
    sp0.submark("dream_scene_0")
    time.sleep(0.5)
    await asyncio.sleep(0.15)
    s = await hb.stop()
    return hb, s

hb, s = asyncio.run(scenario())
notes = s.get("stall_attribution", [])
print("notes:", notes)
check("two stalls recorded", len(notes) >= 2)
check("first attributed to stage replay / sub affections", notes and notes[0]["stage"] == "replay" and notes[0]["sub"] == "affections")
check("second attributed to dream_scene_0", any(n["sub"] == "dream_scene_0" for n in notes))
check("lag recorded > threshold", all(n["lag_s"] > 0.3 for n in notes))
rows = [json.loads(l) for l in sp0.STALL_ATTRIBUTION_LOG.read_text(encoding="utf-8").splitlines()] if sp0.STALL_ATTRIBUTION_LOG.exists() else []
check("jsonl rows written (temp path)", len(rows) == len(notes) and rows and "sleep_ts" in rows[0])
check("module submark is a no-op after stop (no raise)", sp0.submark("x") is None and sp0._CURRENT is None)

# cap
hb2 = sp0.SleepHeartbeat(shadow=False)
sp0.STALL_ATTRIBUTION_LOG = tmp / "cap.jsonl"
for _ in range(sp0.STALL_NOTES_CAP + 7):
    hb2._note_stall(3.0)
check("notes capped at 100, overflow counted", len(hb2.stall_notes) == sp0.STALL_NOTES_CAP and hb2.stalls_dropped == 7)

# kill switch
sp0.STALL_ATTRIBUTION = False
hb3 = sp0.SleepHeartbeat(shadow=False); hb3._note_stall(5.0)
check("kill switch: nothing recorded", hb3.stall_notes == [] and "stall_attribution" not in hb3.summary())
sp0.STALL_ATTRIBUTION = True

# wiring (AST/text)
node = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
dream = (ROOT / "nodes" / "dream_node.py").read_text(encoding="utf-8")
ast.parse(node); ast.parse(dream)
for lab in ("affections", "peers", "self_mirror", "psyche_graph", "refinery", "pursuits_judge", "drift_shadow", "reading_reconcile"):
    check(f"consolidation submark {lab}", f'submark("{lab}")' in node)
for lab in ("dream_gather", "dream_memory_ask", "dream_probe", "dream_store", "dream_edges", "dream_ground", "dream_log_arc"):
    check(f"dream submark {lab}", f'_sp0_submark("{lab}")' in dream)
check("per-scene submark", 'dream_scene_{i}' in dream)
live_after = LIVE.stat().st_size if LIVE.exists() else None
check("live attribution log untouched", live_before == live_after)
print("ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)
