"""
J-2578 (F-3308, plan error_pathway): core.procedures refusal-kind shadow.

1. refusal_kind() on the real world answer strings F-3308 quoted (copied from data/procedures.json evidence and
   core/garden.py's water answer): grass short already / soil already wet -> already; no seed to hand, choked grate,
   no matches left, bed clean -> precond; the clock ("turn the key ... until it will not turn") -> NOT skill (the live
   _REFUSAL regex flags it as a refusal: a false positive, so a skill-only dock rule would not dock it).
2. observe_hand() on a refusal: the live dock is unchanged (dock_pending=1, rung held down as before) and one shadow
   row lands in the redirected side log with kind + skill-only counterfactual rung. A success writes no shadow row.
3. Kill switch REFUSAL_KIND_SHADOW=False writes nothing.
Run from a throwaway worktree: python scripts/_test_j2578_refusal_kind_shadow.py
"""
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")

import core  # noqa: E402  -- core BEFORE lab_env (F-2570-era leak rule)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.procedures as procedures  # noqa: E402
import lab_env  # noqa: E402
from lab_env import isolate  # noqa: E402

# keep the lab sandbox inside the tree under test (lab_env hardcodes C:\Nascence\data\_lab)
lab_env._ROOT = ROOT
lab_env._LAB_ROOT = ROOT / "data" / "_lab"
lab_env._ISOLATE_OUTCOMES_LOG = lab_env._LAB_ROOT / "_isolate_outcomes.jsonl"

CASES = [
    ("The grass is short already; there is nothing to cut.", "already"),
    ("You water the bed, but the soil was already wet through; it pools on the surface and stands there.", "already"),
    ("You have no seed to hand \u2014 the tin is not here.", "precond"),
    ("You lay the fire on the choked grate and light it; it smoulders, will not draw, and goes out in its ", "skill"),  # J-4181: skill before precond
    ("No matches left to light it with.", "precond"),
    ("You go over the bed, but it is clean; nothing to pull.", "precond"),
    ("The knot slips.", "skill"),
]
CLOCK = "You turn the key in the back of the clock until it will not turn, set the hands by the light as best"

fails = 0


def check(cond, msg):
    global fails
    print(("PASS " if cond else "FAIL ") + msg)
    fails += 0 if cond else 1


# 1. classifier
for ans, want in CASES:
    got = procedures.refusal_kind(ans)
    check(got == want, f"refusal_kind({ans[:40]!r}) = {got} (want {want})")
check(bool(procedures._REFUSAL.search(CLOCK)), "clock answer IS flagged by the live _REFUSAL regex (false positive)")
check(procedures.refusal_kind(CLOCK) == "unknown", f"clock answer kind = {procedures.refusal_kind(CLOCK)} (want unknown, not skill)")

# 2./3. observe_hand under isolation
with isolate(db="empty", also=[(procedures, ["_F", "_LOG", "_REFUSAL_KIND_SHADOW_LOG"])]) as lab:
    shadow = Path(procedures._REFUSAL_KIND_SHADOW_LOG)
    check(str(shadow).startswith(str(lab)), f"shadow log redirected into lab dir ({shadow})")
    # a procedure that has already earned 'persisted' (2 ok days) so a dock is visible as a rung drop
    d = {"procedures": {}, "archive": []}
    row = procedures._new("world:mow", "world", "I can mow", "the world answered my hand")
    row.update({"successes": 2, "days_ok": ["2026-10-01", "2026-10-02"], "last_reinforced": 0.0})
    procedures._climb(row, time.time())
    d["procedures"]["world:mow"] = row
    Path(procedures._F).write_text(json.dumps(d), encoding="utf-8")
    check(row["rung"] == "persisted", f"fixture rung = {row['rung']}")

    p = procedures.observe_hand("mow", "The grass is short already; there is nothing to cut.", "garden")
    check(p.get("dock_pending", 0) == 0 and p["rung"] == "persisted" and p["failures"] == 0, f"J-4181 skill-only: already-refusal does not dock: dock_pending={p.get('dock_pending', 0)} rung={p['rung']}")
    rows = [json.loads(x) for x in shadow.read_text(encoding="utf-8").splitlines() if x.strip()]
    check(len(rows) == 1, f"one shadow row after one refusal (got {len(rows)})")
    r = rows[0]
    check(r["kind"] == "already" and r["rung_live"] == "persisted" and r["rung_skill_only"] == "persisted"
          and r["diverges"] is False and r["would_dock_skill_only"] is False, f"shadow row {r}")

    procedures.observe_hand("knot", "The knot slips.", "porch")
    rows = [json.loads(x) for x in shadow.read_text(encoding="utf-8").splitlines() if x.strip()]
    check(rows[-1]["kind"] == "skill" and rows[-1]["would_dock_skill_only"] is True and rows[-1]["diverges"] is False,
          f"skill refusal row {rows[-1]}")

    procedures.observe_hand("tea", "You brew the tea; it steams in the cup.", "kitchen")
    rows2 = [json.loads(x) for x in shadow.read_text(encoding="utf-8").splitlines() if x.strip()]
    check(len(rows2) == len(rows), "a success writes no shadow row")

    # J-4181: clock false positive (unknown) does not dock; a skill refusal on mow does
    p = procedures.observe_hand("mow", CLOCK, "study")
    check(p.get("dock_pending", 0) == 0 and p["rung"] == "persisted", "unknown refusal does not dock")
    p = procedures.observe_hand("mow", "The scythe slips.", "garden")
    check(p["dock_pending"] == 1 and p["rung"] == "occurred" and p["failures"] == 1, "skill refusal docks")
    rows = [json.loads(x) for x in shadow.read_text(encoding="utf-8").splitlines() if x.strip()]
    procedures.REFUSAL_KIND_SHADOW = False
    procedures.SKILL_ONLY_DOCK = False
    try:
        procedures.observe_hand("lamp", "No matches left to light it with.", "study")
    finally:
        procedures.REFUSAL_KIND_SHADOW = True
        procedures.SKILL_ONLY_DOCK = True
    rows3 = [json.loads(x) for x in shadow.read_text(encoding="utf-8").splitlines() if x.strip()]
    check(len(rows3) == len(rows), "kill switch off writes nothing")
    live = json.loads(Path(procedures._F).read_text(encoding="utf-8"))["procedures"]["world:lamp"]
    check(live["dock_pending"] == 1, "SKILL_ONLY_DOCK off: legacy dock-on-every-refusal")

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL'}")
sys.exit(1 if fails else 0)
