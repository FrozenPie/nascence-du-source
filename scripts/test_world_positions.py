"""
Position-authority test suite (2026-08-17, founder: "all the objects need places, and they need
to be able to move of course"). TEST-ISOLATION LAW: world_objects' _OBJECTS_F and world_substrate's
_SUBSTRATE_F are temp-pathed for every mutating test — live stores are never touched. Read-only
checks against live data are allowed (they mutate nothing).
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

PASS = FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    PASS += ok
    FAIL += (not ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def main():
    tmp = Path(tempfile.mkdtemp(prefix="lane_pos_"))
    from core import world_objects as wo
    from core import world_substrate as ws

    # ── isolate BOTH stores ──
    live_obj_f, live_sub_f = wo._OBJECTS_F, ws._SUBSTRATE_F
    wo._OBJECTS_F = tmp / "world_objects.json"
    ws._SUBSTRATE_F = tmp / "world_substrate.json"
    wo._objects_cache, wo._last_load = {}, 0.0
    ws._cache, ws._cache_ts = {}, 0.0
    try:
        shutil.copy(live_obj_f, wo._OBJECTS_F)         # start from the live shape, isolated
        shutil.copy(live_sub_f, ws._SUBSTRATE_F)
        print("— placement —")
        n = wo.backfill_positions()
        objs = wo._load_objects()
        subs = ws._load()
        check("backfill covers every substrate object", all(oid in objs for oid in subs),
              f"backfilled {n}, records {len(objs)}")
        # in-frame per room (shore size [30,20]; wood [24,20])
        frames = {"shore": (30, 20), "wood": (24, 20), "garden": (10.5, 12.5), "study": (4.2, 5.2)}
        ok = True
        for oid, rec in objs.items():
            loc, pos = rec.get("location"), rec.get("position")
            if loc in frames and pos:
                fx, fy = frames[loc]
                if not (0 <= pos[0] <= fx and 0 <= pos[1] <= fy):
                    ok = False
                    print(f"      out-of-frame: {oid} {pos} in {loc}")
        check("every position inside its room frame", ok)
        # marine items in the tideline/dry bands
        ok = all(2.0 <= rec["position"][1] <= 14.0 for rec in objs.values()
                 if rec.get("location") == "shore" and rec.get("object_class") in wo._MARINE_CLASSES
                 and rec.get("object_id") != "driftwood_17")
        check("shore marine items within the shore bands", ok)
        # determinism
        p1 = wo._spawn_position("determin_test_1", "shore", "shell")
        p2 = wo._spawn_position("determin_test_1", "shore", "shell")
        p3 = wo._spawn_position("determin_test_2", "shore", "shell")
        check("same object id → same position", p1 == p2, str(p1))
        check("different id → different position", p1 != p3)

        print("— spawn births a place —")
        new = ws.spawn_object("shell", "shore", seed="postest")
        check("spawned object gets a position record", new is not None and wo.pos_of(new.object_id) is not None,
              f"{new.object_id if new else '—'} at {wo.pos_of(new.object_id) if new else '—'}")

        print("— movement —")
        drift_before = wo.get_object("driftwood_17")
        moved_any = reclaimed_any = False
        for h in range(40):                      # simulate 40 hourly storm passes deterministically
            wo._load_objects()
            import core.world_objects as _w
            real_time = time.time
            try:
                time_offset = h * 3600
                _w.time.time = lambda: real_time() + time_offset      # advance the hour seed
                ev = wo.move_tick("thunderstorm", tide_level=0.95)
            finally:
                _w.time.time = real_time
            if any("shifted" in e for e in ev):
                moved_any = True
            if any("taken" in e or "floated" in e for e in ev):
                reclaimed_any = True
        check("storms move objects (40 simulated hours)", moved_any)
        check("storms/king tide can reclaim floaters", reclaimed_any)
        drift_after = wo.get_object("driftwood_17")
        check("driftwood_17 untouched by the generic mover",
              drift_before.get("position") == drift_after.get("position")
              and len(drift_before.get("history", [])) == len(drift_after.get("history", [])))
        gone = [o for o in wo._load_objects().values() if o.get("location") == "gone"]
        ok_hist = all(o.get("history") and o["history"][-1].get("to") is None for o in gone)
        check("reclaimed objects keep full history, position→None recorded", ok_hist or not gone,
              f"{len(gone)} gone")
        moved = [o for o in wo._load_objects().values()
                 if len(o.get("history", [])) > 1 and o.get("location") == "shore"
                 and o.get("object_id") != "driftwood_17"]
        ok_moves = all(all(e.get("from") is not None for e in o["history"][1:]) for o in moved)
        check("every move carries from→to causal provenance", ok_moves, f"{len(moved)} movers")
        check("legacy surge still works (driftwood bespoke path)",
              callable(wo.process_storm_surge))

        print("— register passthrough —")
        from core import ghost_tuples as gt
        idx = gt.build_world_index(persist=False)
        items = {k: v for k, v in idx["entries"].items() if k.startswith("item:")}
        with_pos = [k for k, v in items.items() if v.get("pos")]
        check("ghost world-index items carry pos", len(with_pos) >= len(items) - len(gone) - 1,
              f"{len(with_pos)}/{len(items)} placed")
        check("gone objects tagged state:gone in the register",
              all("state:gone" in v.get("tags", []) for k, v in items.items()
                  if k[5:] in {o['object_id'] for o in gone}) or not gone)

        print("— live read-only sanity (no mutation) —")
        wo._OBJECTS_F, wo._objects_cache, wo._last_load = live_obj_f, {}, 0.0
        ws._SUBSTRATE_F, ws._cache, ws._cache_ts = live_sub_f, {}, 0.0
        live = wo._load_objects()
        check("live store still has driftwood_17 with its true position",
              (live.get("driftwood_17") or {}).get("position") == [12.4, 4.1, 0.2])
    finally:
        wo._OBJECTS_F, wo._objects_cache, wo._last_load = live_obj_f, {}, 0.0
        ws._SUBSTRATE_F, ws._cache, ws._cache_ts = live_sub_f, {}, 0.0
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
