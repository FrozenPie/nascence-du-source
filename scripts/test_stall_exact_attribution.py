"""scripts/test_stall_exact_attribution.py (J-2330, F-3019): hermetic proof of the exact stall-attribution keys.

No LLM, no data/ access: the attribution log is temp-pathed and the live file's size is compared before/after.
Simulates a synchronous block (time.sleep on the loop) around submarks with a short heartbeat interval and checks
prev_sub / sub_set_offset_s / marks_during / sub_age_s for both orderings:
  A. freeze AFTER the mark  -- the label was standing before the freeze (sticky): offset < 0, nothing during.
  B. mark INSIDE the freeze -- the freeze began in the previous sub's code: offset > 0, prev_sub = the old label.
Also: a stage mark inside a freeze, the since-turn cap (prev_sub stays right), the kill switch, the wiring.
Run from the tree under test."""
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

tmp = Path(tempfile.mkdtemp(prefix="j2330_"))
LIVE = ROOT / "data" / "night_stall_attribution.jsonl"
live_before = LIVE.stat().st_size if LIVE.exists() else None
sp0.STALL_ATTRIBUTION_LOG = tmp / "night_stall_attribution.jsonl"
sp0.STALL_S = 0.3
BLOCK = 0.5


async def scenario():
    hb = sp0.SleepHeartbeat(interval=0.05, shadow=False)
    hb.start()
    await asyncio.sleep(0.15)
    hb.mark("consolidation")
    # A: freeze after the mark -- "x" is set, the loop turns, THEN the sync block.
    sp0.submark("x")
    await asyncio.sleep(0.15)
    time.sleep(BLOCK)
    await asyncio.sleep(0.15)
    # B: mark inside the freeze -- "x" stands (baseline), block, set "y", block, then the await.
    time.sleep(BLOCK)
    sp0.submark("y")
    time.sleep(BLOCK)
    await asyncio.sleep(0.15)
    # C: a stage mark inside a freeze resets the sub; it shows as "stage:<label>".
    time.sleep(BLOCK)
    hb.mark("pre_dream_done")
    time.sleep(0.05)
    await asyncio.sleep(0.15)
    # D: cap -- 12 marks inside one freeze; prev_sub must still be the baseline, overflow counted.
    sp0.submark("base")
    await asyncio.sleep(0.15)
    time.sleep(BLOCK)
    for i in range(12):
        sp0.submark(f"m{i}")
    time.sleep(0.05)
    await asyncio.sleep(0.15)
    s = await hb.stop()
    return hb, s


hb, s = asyncio.run(scenario())
rows = [json.loads(l) for l in sp0.STALL_ATTRIBUTION_LOG.read_text(encoding="utf-8").splitlines()] \
    if sp0.STALL_ATTRIBUTION_LOG.exists() else []
for r in rows:
    print("  row:", {k: r.get(k) for k in ("lag_s", "stage", "sub", "prev_sub", "sub_set_offset_s", "sub_age_s",
                                          "marks_during", "marks_during_dropped")})
check("four stalls written to the temp log", len(rows) == 4)
keys = ("freeze_start_ts", "prev_sub", "sub_set_offset_s", "marks_during", "marks_during_dropped", "sub_age_s")
check("every row carries the new keys and keeps the old ones",
      rows and all(all(k in r for k in keys) and all(k in r for k in ("ts", "lag_s", "stage", "sub", "turns"))
                   for r in rows))
if len(rows) == 4:
    a, b, c, d = rows
    check("A: sub x, prev_sub x (sticky, set before the freeze)", a["sub"] == "x" and a["prev_sub"] == "x")
    check("A: sub_set_offset_s < 0 and nothing during", a["sub_set_offset_s"] < 0 and a["marks_during"] == [])
    check("A: sub_age_s >= the block", a["sub_age_s"] >= BLOCK - 0.05)
    check("B: sub y, prev_sub x (the freeze began in x's code)", b["sub"] == "y" and b["prev_sub"] == "x")
    check("B: sub_set_offset_s > 0, about one block", 0.3 < b["sub_set_offset_s"] < BLOCK + 0.15)
    check("B: marks_during == [y] with that offset",
          [m["label"] for m in b["marks_during"]] == ["y"]
          and abs(b["marks_during"][0]["offset_s"] - b["sub_set_offset_s"]) < 0.002)
    check("B: sub_age_s about one block (fresh label)", 0.3 < b["sub_age_s"] < BLOCK + 0.15)
    check("C: stage mark inside the freeze: sub '', prev_sub y, stage:pre_dream_done during",
          c["sub"] == "" and c["prev_sub"] == "y" and c["stage"] == "pre_dream_done"
          and [m["label"] for m in c["marks_during"]] == ["stage:pre_dream_done"])
    check("D: cap: prev_sub still base, 8 kept, 4 dropped, newest kept",
          d["prev_sub"] == "base" and len(d["marks_during"]) == sp0.MARKS_SINCE_TURN_CAP
          and d["marks_during_dropped"] == 4 and d["marks_during"][-1]["label"] == "m11" and d["sub"] == "m11")
    check("freeze_start_ts = ts - lag (within rounding)", all(abs((r["ts"] - r["lag_s"]) - r["freeze_start_ts"]) < 0.2
                                                             for r in rows))
check("since-turn list cleared after the last turn", hb._marks_since_turn == [] or len(hb._marks_since_turn) <= 1)

# backward compatibility: the old one-argument call still works and adds no exact keys
sp0.STALL_ATTRIBUTION_LOG = tmp / "compat.jsonl"
hb2 = sp0.SleepHeartbeat(shadow=False); hb2._note_stall(3.0)
r2 = json.loads((tmp / "compat.jsonl").read_text(encoding="utf-8").splitlines()[0])
check("_note_stall(lag) still works, no exact keys", "prev_sub" not in r2 and r2["lag_s"] == 3.0)

# kill switch
sp0.STALL_EXACT_ATTRIBUTION = False
sp0.STALL_ATTRIBUTION_LOG = tmp / "kill.jsonl"
hb3 = sp0.SleepHeartbeat(shadow=False); hb3.submark("z"); hb3._note_stall(3.0, time.perf_counter() - 3.0, time.perf_counter())
r3 = json.loads((tmp / "kill.jsonl").read_text(encoding="utf-8").splitlines()[0])
check("kill switch: no timeline tracked, no exact keys", hb3._marks_since_turn == [] and "prev_sub" not in r3
      and r3["sub"] == "z")
sp0.STALL_EXACT_ATTRIBUTION = True

# wiring (text/AST): the new sub-marks exist
node = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
dream = (ROOT / "nodes" / "dream_node.py").read_text(encoding="utf-8")
orch = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
ml = (ROOT / "core" / "memory_levels.py").read_text(encoding="utf-8")
for t in (node, dream, orch, ml):
    ast.parse(t)
for lab in ("stick_test", "peer_metrics", "holdrate", "guidance_integration", "grounded_learning",
            "world_consolidation", "book_residue", "memory_levels", "memory_lint", "bus_sync", "rest", "night_mind"):
    check(f"monologue submark {lab}", f'_hb.submark("{lab}")' in node)
check("dream submark dream_met_nightly", '"dream_met_nightly"' in dream)
check("orchestrator submark post_dream_callback", 'submark("post_dream_callback")' in orch)
check("shadow_distill t_marks in the fetch probe", "t_marks=_tm" in ml)
live_after = LIVE.stat().st_size if LIVE.exists() else None
check("live attribution log untouched", live_before == live_after)
print("ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)
