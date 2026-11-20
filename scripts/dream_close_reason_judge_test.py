"""
Offline test for J-1847 (D-0356 (B), 2026-10-07): the independent resolution judge, not the dreaming LLM's
own self-report, sets a dream's close_reason (resolved vs ended-unfaced).

No LLM, no live-store WRITES. All sidecars are temp-pathed; core.memory_service.ask, dream_probe,
memory_edges and every store-writing DreamNode method are stubbed. The recorded-arc replay READS the live
data/logs/dream_resolution_shadow.jsonl (read-only) when it exists.

  [1] _judge_close_reason truth table (judge decides resolved/ended-unfaced; stalled/dropped/ceiling pass
      through; judge None -> self-report; kill switch restores old behaviour)
  [2] end-to-end synthesise(commit=True) with a fake dreamer + fake judge: close_reason handed to _log_arc
      follows the judge, the dreamer's unresolved_core is untouched (still feeds _bridge_final), the shadow
      row carries close_reason (self), close_reason_final, judge_decided, self_reported_resolved, agree
  [3] offline replay of recorded shadow rows where BOTH verdicts exist: the new rule makes close_reason
      follow the judge on every row; reports the judge-vs-self-report divergence D-0356's defeater reads

Run:  python scripts/dream_close_reason_judge_test.py   (from the tree under test)
"""
from __future__ import annotations
import asyncio, json, sys, tempfile
from pathlib import Path
from types import SimpleNamespace

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE anything that could repoint paths; assert we are testing the tree we think we are
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import nodes.dream_node as dn
from nodes.dream_node import DreamNode
import core.judge_panel as judge_panel
import core.memory_service as memsvc
import core.dream_probe as dprobe
import core.memory_edges as medges
import core.night as night_mod

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

tmp = Path(tempfile.mkdtemp(prefix="j1847_"))
dn._RESOLUTION_SHADOW_LOG = tmp / "dream_resolution_shadow.jsonl"
dn._DREAM_LOG = tmp / "dream_log.jsonl"
dn._DREAM_STATE_LOG = tmp / "dream_state.jsonl"

# ---------------------------------------------------------------------------------------------
print("\n[1] _judge_close_reason truth table")
f = DreamNode._judge_close_reason
check("self ended-unfaced, judge True  -> resolved", f("ended-unfaced", True) == "resolved")
check("self resolved,      judge False -> ended-unfaced", f("resolved", False) == "ended-unfaced")
check("self ended-unfaced, judge False -> ended-unfaced", f("ended-unfaced", False) == "ended-unfaced")
check("self resolved,      judge True  -> resolved", f("resolved", True) == "resolved")
check("judge unavailable (None) -> self-report stands (ended-unfaced)", f("ended-unfaced", None) == "ended-unfaced")
check("judge unavailable (None) -> self-report stands (resolved)", f("resolved", None) == "resolved")
for r in ("stalled", "dropped", "ceiling"):
    check(f"{r} unchanged for judge True/False/None", all(f(r, v) == r for v in (True, False, None)))
dn.JUDGE_SETS_CLOSE_REASON = False
check("kill switch off -> old behaviour (judge True does not flip ended-unfaced)", f("ended-unfaced", True) == "ended-unfaced")
dn.JUDGE_SETS_CLOSE_REASON = True

# ---------------------------------------------------------------------------------------------
print("\n[2] end-to-end synthesise(commit=True), fake dreamer + fake judge, every store stubbed")
captured = {}
def make_scene(i, unresolved, movement):
    return {"narrative": f"scene {i}", "symbols": ["river"], "tension_source": "t", "movement": movement,
            "unresolved_core": unresolved, "phase": "x"}

async def run(self_unresolved, judge_verdict, stalled=False):
    node = DreamNode()
    captured.clear()
    async def fake_gen(state, material, prev, idx, phase, **kw):
        last = idx >= 2
        return make_scene(idx, self_unresolved if last else "mid", "arrived" if (last and not stalled) else "unfolding")
    node._gen_episode = fake_gen
    node._gather_materials = lambda state, n: ["", "m2", "m3"]      # "" -> no memory_service.ask in synthesise
    node._last_unresolved_arc = lambda: None
    node._log_transition = lambda *a, **k: None
    node._store_episode = lambda *a, **k: None
    node._ground_symbols = lambda *a, **k: None
    node._scene_stalled = (lambda d, p: True) if stalled else (lambda d, p: False)
    node._bridge_final = lambda last, close_reason=None: captured.__setitem__("bridge_unresolved", last["unresolved_core"])
    node._log_arc = lambda scenes, dream_id, close_reason="ceiling": captured.update(
        arc_close=close_reason, ended_unresolved=bool(scenes[-1]["unresolved_core"]))
    async def fake_rule_detail(system, user, key=None, context=None):
        captured["judge_called"] = True
        return {"verdict": judge_verdict, "how": "fake", "v1": judge_verdict, "v2": judge_verdict}
    judge_panel.rule_detail = fake_rule_detail
    memsvc.ask = lambda *a, **k: []
    dprobe.log_seed_pairs = lambda *a, **k: None
    medges.record_dream_sources = lambda *a, **k: None
    night_mod.sleep_kind = lambda *a, **k: "night"
    st = SimpleNamespace(spirit_name="t", axiom="a", background_curiosities=[])
    return await node.synthesise(st, commit=True)

def last_row():
    return json.loads(dn._RESOLUTION_SHADOW_LOG.read_text(encoding="utf-8").strip().splitlines()[-1])

asyncio.run(run("still unfaced thing", True))
row = last_row()
check("self=unresolved, judge=True -> _log_arc gets 'resolved'", captured["arc_close"] == "resolved")
check("dreamer's own unresolved_core still feeds _bridge_final + ended_unresolved (self-report kept)",
      captured["bridge_unresolved"] == "still unfaced thing" and captured["ended_unresolved"] is True)
check("shadow row: close_reason (self)=ended-unfaced, close_reason_final=resolved, judge_decided=True",
      row["close_reason"] == "ended-unfaced" and row["close_reason_final"] == "resolved" and row["judge_decided"] is True)
check("shadow row: self_reported_resolved False, judge_verdict True, agree False",
      row["self_reported_resolved"] is False and row["judge_verdict"] is True and row["agree"] is False)

asyncio.run(run("", False))
row = last_row()
check("self=resolved (empty core), judge=False -> _log_arc gets 'ended-unfaced'", captured["arc_close"] == "ended-unfaced")
check("shadow row records the divergence (close_reason self=resolved, final=ended-unfaced, agree False)",
      row["close_reason"] == "resolved" and row["close_reason_final"] == "ended-unfaced" and row["agree"] is False)

asyncio.run(run("unfaced", False))
row = last_row()
check("self=unresolved, judge=False -> 'ended-unfaced', agree True", captured["arc_close"] == "ended-unfaced" and row["agree"] is True)

asyncio.run(run("unfaced", None))
row = last_row()
check("judge unavailable -> self-report's close_reason stands, judge_decided False",
      captured["arc_close"] == "ended-unfaced" and row["close_reason_final"] == "ended-unfaced" and row["judge_decided"] is False)
asyncio.run(run("", None))
check("judge unavailable + self empty core -> 'resolved' (fail-open to self-report)", captured["arc_close"] == "resolved")

asyncio.run(run("unfaced", True, stalled=True))
row = last_row()
check("stalled arc: judge still runs (agreement measure) but close_reason stays 'stalled'",
      captured["judge_called"] and captured["arc_close"] == "stalled" and row["close_reason_final"] == "stalled" and row["judge_decided"] is False)

# ---------------------------------------------------------------------------------------------
# J-3019 (F-3727): the judge must see the arc's END -- a 4000-char arc keeps its last scene in the user prompt
async def _tail_case():
    seen = {}
    async def fake_rd(system, user, key=None, context=None):
        seen["user"] = user
        return {"verdict": True, "how": "fake", "v1": True, "v2": True}
    judge_panel.rule_detail = fake_rd
    scenes = [make_scene(i, "", "unfolding") for i in range(4)]
    for s_ in scenes:
        s_["narrative"] = ("x" * 990) + f" END{s_['narrative']}"
    scenes[-1]["narrative"] = ("y" * 990) + " FINAL-SCENE-MARKER"
    await DreamNode()._judge_resolution_shadow(scenes, "d-j3019", "ended-unfaced")
    return seen["user"]
_u = asyncio.run(_tail_case())
check("J-3019: 4000-char arc -> last scene text is in the judge's user prompt", "FINAL-SCENE-MARKER" in _u)
check("J-3019: whole 4000-char arc fits (first scene too)", "END" in _u and _u.count("x") >= 2900)

print("\n[3] offline replay of recorded shadow rows (read-only)")
cands = [Path(r"C:\Nascence\data\logs\dream_resolution_shadow.jsonl"), ROOT / "data" / "logs" / "dream_resolution_shadow.jsonl"]
src = next((c for c in cands if c.exists()), None)
if src is None:
    print("  (no recorded shadow log reachable -- replay skipped)")
else:
    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    both = [r for r in rows if r.get("judge_verdict") in (True, False) and r.get("self_reported_resolved") in (True, False)
            and r.get("close_reason") in ("resolved", "ended-unfaced")]
    print(f"  source={src}  rows={len(rows)}  rows with both verdicts + self close_reason={len(both)}")
    follows = sum(1 for r in both if (f(r["close_reason"], r["judge_verdict"]) == "resolved") == bool(r["judge_verdict"]))
    check("replay: new rule makes close_reason follow the judge on EVERY recorded row with both verdicts",
          len(both) > 0 and follows == len(both))
    n = len(both)
    j_rate = sum(1 for r in both if r["judge_verdict"]) / n if n else 0
    s_rate = sum(1 for r in both if r["self_reported_resolved"]) / n if n else 0
    flips = sum(1 for r in both if f(r["close_reason"], r["judge_verdict"]) != r["close_reason"])
    print(f"  judge resolved rate {j_rate*100:.1f}% vs self-report {s_rate*100:.1f}% -> divergence {abs(j_rate-s_rate)*100:.1f} pts "
          f"(D-0356 defeater: >10 pts over 30 arcs); rows whose close_reason would change under the new rule: {flips}")

print("\nRESULT:", "ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)
