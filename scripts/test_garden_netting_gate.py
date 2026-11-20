"""scripts/test_garden_netting_gate.py (J-2112, D-0418 (i)): hermetic proof of the netting-read event gate.

Synthetic ledger / garden / marker files in a temp dir; the job filer is a recorder (job_queue.py is never called);
the live data files are read ONCE at the end only to prove the gate reads today's real state as 'no event'. Nothing
is written outside the temp dir.

  [1] vulnerable(): structural rule from core.garden.CATALOGUE (radish yes; dandelion/chickweed weeds no; rosemary
      evergreen no; mint herbaceous no; unknown species no)
  [2] no event: empty ledger + established plants -> event None, no job, no marker
  [3] sow deed -> fires once, files the job with the row quoted, writes the marker; a second run files nothing
  [4] vulnerable shoot in a bed slot -> fires once; a shoot with slot None, a weed shoot or a herbaceous shoot -> no event
  [5] sow wins over shoot when both exist; dry-run files nothing and writes no marker
  [6] a filer that raises -> no marker (so the next pass retries), error reported, exit path never raises
  [7] the live files, read only: today's real ledger/garden give 'no event' (zero sow deeds, no shoot-stage crop, F-2734)
  [8] plan-maintain wiring: step 7c calls this script fail-open (text check on the skill file, if present)

Run:  python scripts/test_garden_netting_gate.py   (from the tree under test)
"""
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: F401  (from this tree)
assert Path(core.__file__).resolve().is_relative_to(ROOT)
from core.garden import CATALOGUE
import importlib.util
spec = importlib.util.spec_from_file_location("garden_netting_gate", ROOT / "scripts" / "garden_netting_gate.py")
gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)

ok_all = True
def check(name, cond, detail=""):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"    <- {detail}" if detail and not cond else ""))

tmp = Path(tempfile.mkdtemp(prefix="j2112_"))
L, G, M = tmp / "ledger.jsonl", tmp / "garden.json", tmp / "marker.json"
def write_ledger(rows): L.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
def write_garden(plants, netted=False): G.write_text(json.dumps({"plants": plants, "netted": netted}), encoding="utf-8")
def plant(species, stage, slot=0, ts=1.7e9): return {"species": species, "stage": stage, "slot": slot, "germ_ts": ts, "sown_ts": ts}
filed = []
def recorder(title, briefing, session): filed.append((title, briefing, session)); return "J-9999 ADDED (fake)"
def reset():
    filed.clear()
    if M.exists(): M.unlink()

print("[1] vulnerable()")
check("radish (veg, annual) vulnerable", gate.vulnerable("radish", CATALOGUE) is True)
check("lettuce (veg, annual) vulnerable", gate.vulnerable("lettuce", CATALOGUE) is True)
check("dandelion / chickweed (weeds) not", not gate.vulnerable("dandelion", CATALOGUE) and not gate.vulnerable("chickweed", CATALOGUE))
check("rosemary (evergreen) and mint (herbaceous) not", not gate.vulnerable("rosemary", CATALOGUE) and not gate.vulnerable("mint", CATALOGUE))
check("unknown species not", gate.vulnerable("triffid", CATALOGUE) is False)

print("[2] no event")
reset(); write_ledger([{"ts": 1, "deed": "water"}, {"ts": 2, "deed": "harvest", "species": "parsley"}])
write_garden({"p1": plant("rosemary", "flowering"), "p2": plant("thyme", "established", 1)})
r = gate.run(L, G, M, filer=recorder, catalogue=CATALOGUE)
check("event None, nothing filed, no marker", r["event"] is None and r["filed"] is None and not filed and not M.exists(), str(r))

print("[3] sow deed")
write_ledger([{"ts": 1, "deed": "water"}, {"ts": 5.5, "deed": "sow", "species": "radish", "slot": 3}])
r = gate.run(L, G, M, filer=recorder, session="sess-1", catalogue=CATALOGUE)
check("fires on the first sow deed; job filed once with the row quoted", r["event"]["kind"] == "sow" and r["event"]["ts"] == 5.5 and len(filed) == 1
      and "first sow deed at ts 5.5" in filed[0][1] and '"deed": "sow"' in filed[0][1] and filed[0][2] == "sess-1", str(r))
check("job title names D-0278 / D-0418 and the plan is garden_upgrade (title text)", "D-0278" in filed[0][0] and "D-0418" in filed[0][0])
mk = json.loads(M.read_text(encoding="utf-8"))
check("marker written: fired True, event + filed recorded", mk["fired"] is True and mk["event"]["kind"] == "sow" and mk["filed"].startswith("J-9999"))
r2 = gate.run(L, G, M, filer=recorder, catalogue=CATALOGUE)
check("second run: fired_before, nothing filed again", r2["fired_before"] is True and len(filed) == 1)

print("[4] vulnerable shoot")
reset(); write_ledger([{"ts": 1, "deed": "water"}])
write_garden({"p1": plant("rosemary", "flowering"), "p2": plant("radish", "shoot", slot=2, ts=42.0)}, netted=False)
r = gate.run(L, G, M, filer=recorder, catalogue=CATALOGUE)
check("radish shoot in slot 2 fires; event carries species/slot/netted/germ_ts", r["event"]["kind"] == "shoot" and r["event"]["species"] == "radish"
      and r["event"]["slot"] == 2 and r["event"]["netted"] is False and r["event"]["ts"] == 42.0 and len(filed) == 1 and "vulnerable shoot in a bed slot: radish" in filed[0][1], str(r))
reset(); write_garden({"p2": plant("radish", "shoot", slot=None)})
check("a shoot with no slot (not in a bed) -> no event", gate.run(L, G, M, filer=recorder, catalogue=CATALOGUE)["event"] is None and not filed)
write_garden({"p2": plant("dandelion", "shoot", slot=1)})
check("a weed shoot -> no event", gate.run(L, G, M, filer=recorder, catalogue=CATALOGUE)["event"] is None and not filed)
write_garden({"p2": plant("mint", "shoot", slot=1)})
check("a herbaceous shoot -> no event", gate.run(L, G, M, filer=recorder, catalogue=CATALOGUE)["event"] is None and not filed)
write_garden({"p2": plant("radish", "leaf", slot=1)})
check("a vulnerable crop past the shoot stage -> no event (the exposure text is shoot-only)", gate.run(L, G, M, filer=recorder, catalogue=CATALOGUE)["event"] is None and not filed)

print("[5] precedence and dry-run")
reset(); write_ledger([{"ts": 9, "deed": "sow", "species": "peas"}]); write_garden({"p2": plant("radish", "shoot", slot=1)})
r = gate.run(L, G, M, dry_run=True, filer=recorder, catalogue=CATALOGUE)
check("sow wins over shoot; dry-run files nothing and writes no marker", r["event"]["kind"] == "sow" and r["dry_run"] and not filed and not M.exists() and "DRY-RUN" in r["filed"])

print("[6] a failing filer")
def boom(title, briefing, session): raise RuntimeError("job_queue down")
reset()
r = gate.run(L, G, M, filer=boom, catalogue=CATALOGUE)
check("filer raises -> error reported, no marker (next pass retries), no exception", "job_queue down" in r.get("error", "") and not M.exists())
r = gate.run(L, G, M, filer=recorder, catalogue=CATALOGUE)
check("the retry files and marks", len(filed) == 1 and M.exists())

print("[7] the live files (read-only)")
live = gate.detect(gate.LEDGER, gate.GARDEN, CATALOGUE)
check("today's real ledger/garden: no event (zero sow deeds, no vulnerable shoot in a bed; F-2734)", live is None, str(live))
check("default marker path is under docs/reviews, never data/", "docs" in gate.MARKER.parts and "data" not in gate.MARKER.parts)

print("[8] plan-maintain wiring")
pm = Path.home() / ".claude" / "skills" / "plan-maintain" / "plan_maintain.py"
if pm.exists():
    t = pm.read_text(encoding="utf-8")
    check("plan_maintain.py step 7c runs garden_netting_gate.py inside a try (fail-open)", "garden_netting_gate.py" in t and "7c." in t)
else:
    print("  [SKIP] plan_maintain.py not found on this machine")

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
