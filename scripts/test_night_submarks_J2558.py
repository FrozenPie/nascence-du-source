"""J-2558 harness: the new replay / pre_dream_done sub-marks name a sync freeze, and sit in the intended bodies.
Run with cwd = the job worktree. Writes only to a temp dir (stall log redirected); touches no DB."""
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

tmp = Path(tempfile.mkdtemp(prefix="j2558_"))
sp0.STALL_ATTRIBUTION_LOG = tmp / "night_stall_attribution.jsonl"
sp0.STALL_S = 0.3
sp0.NIGHT_MIND_SHADOW_ROWS = False
written = []
from core import shadow_log, profile
shadow_log.append = lambda path, row: written.append(row)   # never touch any real file

# 1. AST placement: each new label is inside the intended function
def labels_in(path, func):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func:
            out = set()
            for c in ast.walk(node):
                if isinstance(c, ast.Call) and c.args and isinstance(c.args[0], ast.Constant) \
                        and isinstance(c.args[0].value, str):
                    f = c.func
                    nm = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
                    if nm in ("submark", "_sp0_submark", "_sp0_night_submark"):
                        out.add(c.args[0].value)
            return out
    return set()

want = {
    ("nodes/inner_monologue_node.py", "_enter_sleep"): {"replay_ledger", "night_mind_start", "replay_log", "chapter",
        "chapter_tick", "journal", "journal_tick", "week_rollup", "journal_grounding_shadow", "week_rollup_tick",
        "affections_done", "consolidation_tick"},
    ("core/orchestrator.py", "_nightly_sleep"): {"study_life_on_sleep", "dream_wake_boundary", "dream_remember"},
    ("nodes/dream_node.py", "synthesise"): {"dream_resolution_judge", "dream_bridge_final", "dream_arc_return"},
    ("core/peers.py", "deliver_due"): {"peers_due_scan"},
}
for (path, func), labels in want.items():
    have = labels_in(path, func)
    check(f"{path}:{func} carries {sorted(labels)}", labels <= have)
# no label collides with a J-2557 / earlier one used elsewhere
all_new = set().union(*want.values())
import re
src = "".join(p.read_text(encoding="utf-8", errors="replace") for d in ("core", "nodes") for p in (ROOT / d).rglob("*.py"))
check("each new label is used by exactly one submark call in core/ + nodes/ (no J-2557 duplicate)",
      all(len(re.findall(r'(?:submark|_sp0_submark|_sp0_night_submark)\("' + re.escape(l) + r'"\)', src)) == 1
          for l in all_new))

# 2. behaviour: a sync freeze right after a new mark is attributed to it; the sticky dream label is cleared
from core import orchestrator as orch, peers
from nodes import dream_node

async def scenario():
    hb = sp0.SleepHeartbeat(interval=0.05, shadow=False)
    hb.start()
    await asyncio.sleep(0.15)
    hb.mark("pre_dream_done")
    orch._sp0_night_submark("study_life_on_sleep")
    time.sleep(0.6)                       # sync freeze in study_life
    await asyncio.sleep(0.15)
    dream_node._sp0_submark("dream_scene_2_llm")
    await asyncio.sleep(0.3)              # loop free while 'the dreamer answers'
    dream_node._sp0_submark("dream_arc_return")
    time.sleep(0.6)                       # sync freeze after the arc, formerly under the sticky scene label
    await asyncio.sleep(0.15)
    hb.mark("replay")
    peers._sp0_submark("peers_due_scan")
    time.sleep(0.6)
    await asyncio.sleep(0.15)
    await hb.stop()

asyncio.run(scenario())
rows = [r for r in written if r.get("lag_s", 0) > 0.3]
subs = [(r["stage"], r["sub"]) for r in rows]
print("  stall rows:", subs)
check("freeze after study_life_on_sleep attributed to it under pre_dream_done",
      ("pre_dream_done", "study_life_on_sleep") in subs)
check("freeze after the arc names dream_arc_return, not dream_scene_2_llm",
      ("pre_dream_done", "dream_arc_return") in subs and ("pre_dream_done", "dream_scene_2_llm") not in subs)
check("freeze in the peers roster scan attributed to peers_due_scan under replay",
      ("replay", "peers_due_scan") in subs)
check("no submark outside a sleep raises (heartbeat gone)", (orch._sp0_night_submark("x"), True)[1])
print("ALL PASS" if ok_all else "SOME FAILED")
sys.exit(0 if ok_all else 1)
