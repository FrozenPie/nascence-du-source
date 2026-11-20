"""
Hermetic test for prompt_manager P0 (D-0771; plan docs/staged/prompt_manager.md 6.2): Level-1 provenance.

No LLM, no live data; every path redirected into a temp dir. Checks:
  [1] one provenance row per idle assembly (all of them, not 1-in-N), with assembly/system/user hashes
  [2] same inputs -> same assembly hash; a different user prompt under the SAME system prompt -> different assembly hash,
      same system hash (the 123-hashes-none-named gap)
  [3] privacy: the row stores 48-char labels only, never a full part (no second copy of memory material)
  [4] phrasing.vary picks are recorded, drained into the NEXT row once, and the row after is empty
  [5] phrasing.vary selection is UNCHANGED: with a seeded RNG it returns exactly what the pre-P0 algorithm returns
  [6] PROVENANCE_ON=False -> no file; no user_prompt -> no row; the shadow log is unaffected
  [7] fail-open: an unwritable path never raises, and is recorded as a skip row
  [8] write fence: the default data/ path in a non-live process is refused (not created)
  [9] size rotation keeps one backup
Run:  python scripts/_test_prompt_manager_p0_provenance.py   (from the tree under test)
"""
from __future__ import annotations
import json, random, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE lab_env (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import prompt_budget as pb
from core import phrasing as ph

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

LONG = "A question lingering in you: why does the lamp go out when nobody looks at it " * 4
PARTS = ["Where you are: the garden " + "x" * 120, LONG, "WHAT YOU ALREADY KNOW ABOUT THIS: " + "y" * 300]
def up(extra=""): return "No one is speaking to you right now.\n\n" + "\n".join(PARTS) + extra + "\n\nWhat moves in you now? One quiet thought."
def rows(p): return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

def old_vary(key, variants, last, rng):
    """The pre-P0 algorithm, verbatim."""
    if not variants: return ""
    if len(variants) == 1: return variants[0]
    prev = last.get(key, -1)
    choices = [i for i in range(len(variants)) if i != prev]
    idx = rng.choice(choices)
    last[key] = idx
    return variants[idx]

with tempfile.TemporaryDirectory() as td:
    tdp = Path(td)
    pb._LOG = tdp / "prompt_budget_shadow.jsonl"
    pb._SAMPLES = tdp / "idle_prompt_samples.jsonl"
    pb._PROV = tdp / "prompt_provenance.jsonl"
    pb.PROVENANCE_ON = True
    ph.drain_picks()

    print("[1] every assembly")
    for i in range(30):
        pb.observe_assembly(PARTS, system_prompt="SYS-A", base_url="", cycle_id=f"c{i}", wrapper_chars=10, source="t", user_prompt=up(), mid_thread=True, wandering=False)
    pr = rows(pb._PROV)
    check("30 assemblies -> 30 provenance rows", len(pr) == 30)
    check("row carries the three hashes, lane and flags", all(k in pr[0] for k in ("assembly_sha256", "system_sha256", "user_sha256", "lane", "mid_thread", "wandering", "over_cap", "pool_picks")))
    check("cycle ids preserved in order", [r["cycle"] for r in pr] == [f"c{i}" for i in range(30)])

    print("[2] hash identity")
    check("same inputs -> same assembly hash", pr[0]["assembly_sha256"] == pr[1]["assembly_sha256"])
    pb.observe_assembly(PARTS, system_prompt="SYS-A", cycle_id="d1", source="t", user_prompt=up(" and a different memory"))
    pb.observe_assembly(PARTS, system_prompt="SYS-B", cycle_id="d2", source="t", user_prompt=up())
    d1, d2 = rows(pb._PROV)[-2:]
    check("different user prompt, same system: assembly differs, system same", d1["assembly_sha256"] != pr[0]["assembly_sha256"] and d1["system_sha256"] == pr[0]["system_sha256"])
    check("different system, same user: assembly differs, user same", d2["assembly_sha256"] != pr[0]["assembly_sha256"] and d2["user_sha256"] == pr[0]["user_sha256"])

    print("[3] privacy")
    raw = pb._PROV.read_text(encoding="utf-8")
    check("no full part text is stored (labels only)", LONG not in raw and ("y" * 300) not in raw and max(len(x) for r in pr for x in r["labels"]) <= 48)

    print("[4] pool picks")
    ph.drain_picks()
    ph.vary("k1", ["a", "b", "c"]); ph.vary("k2", ["only"])
    pb.observe_assembly(PARTS, system_prompt="SYS-A", cycle_id="p1", source="t", user_prompt=up())
    pb.observe_assembly(PARTS, system_prompt="SYS-A", cycle_id="p2", source="t", user_prompt=up())
    p1, p2 = rows(pb._PROV)[-2:]
    check("picks since last assembly appear on the next row", [x[0] for x in p1["pool_picks"]] == ["k1", "k2"] and p1["pool_picks"][1][1:] == [0, 1])
    check("and are not repeated on the one after", p2["pool_picks"] == [])

    print("[5] vary unchanged")
    ph._last.clear()
    ph.drain_picks()
    a, b, last = random.Random(1234), random.Random(1234), {}
    seq_new, seq_old = [], []
    orig = ph.random
    class R:                      # route phrasing's random.choice to a seeded generator
        @staticmethod
        def choice(x): return a.choice(x)
    ph.random = R
    for i in range(300):
        v = ["w", "x", "y", "z"][: 1 + i % 4]
        seq_new.append(ph.vary("kk%d" % (i % 3), v))
        seq_old.append(old_vary("kk%d" % (i % 3), v, last, b))
    ph.random = orig
    check("300 selections identical to the pre-P0 algorithm", seq_new == seq_old)

    print("[6] off switches")
    n0 = len(rows(pb._PROV))
    pb.observe_assembly(PARTS, cycle_id="nou", source="t")
    check("no user_prompt -> no row", len(rows(pb._PROV)) == n0)
    pb.PROVENANCE_ON = False
    pb.observe_assembly(PARTS, cycle_id="off", source="t", user_prompt=up())
    check("PROVENANCE_ON=False -> no row", len(rows(pb._PROV)) == n0)
    check("shadow log still records every assembly", any(r.get("cycle") == "off" and r.get("kind") == "assembly" for r in rows(pb._LOG)))
    pb.PROVENANCE_ON = True

    print("[7] fail-open")
    blocker = tdp / "iamafile"; blocker.write_text("x")
    pb._PROV = blocker / "sub" / "prov.jsonl"
    try:
        pb.observe_assembly(PARTS, cycle_id="cfail", source="t", user_prompt=up()); raised = False
    except Exception:
        raised = True
    check("unwritable path does not raise", not raised)
    check("failure recorded as a skip row", any(r.get("reason") == "provenance failed" for r in rows(pb._LOG) if r.get("kind") == "skip"))

    print("[8] write fence")
    default_path = ROOT / "data" / "prompt_provenance.jsonl"
    existed = default_path.exists()
    pb._PROV = default_path
    pb.observe_assembly(PARTS, cycle_id="cfence", source="t", user_prompt=up())
    check("non-live process: default data/ path refused (not created)", default_path.exists() == existed)

    print("[9] rotation")
    pb._PROV = tdp / "rot.jsonl"
    pb._PROV_MAX_BYTES, pb._PROV_CHECK_EVERY, pb._prov_appends = 2000, 5, 0
    for i in range(40):
        pb.observe_assembly(PARTS, system_prompt="S", cycle_id=f"r{i}", source="t", user_prompt=up())
    check("rotated once to a .1 backup", (tdp / "rot.jsonl.1").exists())

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
