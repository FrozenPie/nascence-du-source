"""scripts/test_night_wake.py (J-2019, sleep_as_a_mode Phase 3, D-0401 B): hermetic proof of the zero-LLM wake monitor.

No LLM, no real sleep, no live data: the shadow log is a temp path, sensorium.state is mutated IN MEMORY ONLY (never _save())
and restored, core is imported FIRST and its location asserted to be this tree. Live files are size-checked at the end.

  [1] flags: WAKE_ON_HUMAN default True since J-2064 (D-0407 B; was False under J-2019), MONITOR_ENABLED True.
      Sections [2]/[3]/[5]/[2b]/[7] exercise OBSERVE mode by patching the flag OFF in the test; the original is restored.
  [2] the monitor: awake = inert; a word before lying down / within MIN_SLEEP_S = no request; a later word = ONE request;
      later words and a second tick change nothing; a new sleep forgets the old request; waking clears it
  [3] observe mode (default): boundary() records and returns False for every stage (nothing is skipped), finish() says
      woken_by pipeline_end, latency recorded, would_have_woken_at recorded
  [4] live mode (flag patched True in the test only): boundary() returns True; finish() says human_message
  [5] no request: boundary() False, finish() notes woken_by pipeline_end, writes nothing
  [6] the node wiring: _wake_gate is the first statement of the 5 optional stage trys; the rest is sliced; finish() runs
      before night.wake(); orchestrator checks boundary('dream') before DreamNode; sensorium.tick calls monitor_tick
  [7] _wake_gate raises _WakeSkip only when the boundary says skip, and the stage's own except absorbs it
  [8] evaluate() reads the shadow log; live files untouched

Run:  python scripts/test_night_wake.py   (from the tree under test)
"""
from __future__ import annotations
import ast, sys, tempfile, time, json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE anything that could repoint paths
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import night_wake as nw, sensorium as sens

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

LIVE = ROOT / "data" / "night_wake_shadow.jsonl"
live_before = LIVE.stat().st_size if LIVE.exists() else None
tmp = Path(tempfile.mkdtemp(prefix="j2019_"))
nw._DATA = tmp
nw.NIGHT_WAKE_SHADOW_LOG = tmp / "night_wake_shadow.jsonl"
LOG = nw.NIGHT_WAKE_SHADOW_LOG

def rows():
    try:
        return [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []

class FakeNight:
    def __init__(self): self.notes = {}
    def note(self, k, v): self.notes[k] = v

st_backup = {k: sens.state.get(k, "__absent__") for k in ("asleep", "asleep_since")}
hts_backup = sens._last_human_ts
flag0 = nw.WAKE_ON_HUMAN
try:
    print("[1] flags")
    check("WAKE_ON_HUMAN default True (J-2064, D-0407 B)", nw.WAKE_ON_HUMAN is True)
    check("MONITOR_ENABLED default True", nw.MONITOR_ENABLED is True)
    nw.WAKE_ON_HUMAN = False      # J-2064: the observe-mode sections below patch the flag off; restored in the outer finally

    print("[2] monitor")
    nw.reset(); nw._handled_ts = 0.0
    sens.state["asleep"] = False; sens.state.pop("asleep_since", None)
    sens._last_human_ts = time.time()
    check("awake: inert", nw.monitor_tick() is False and nw.pending() is None and not rows())
    t0 = time.time() - 600
    sens.state["asleep"] = True; sens.state["asleep_since"] = t0
    sens._last_human_ts = t0 - 5
    check("word before lying down: no request", nw.monitor_tick() is False)
    sens._last_human_ts = t0 + 3
    check("word within MIN_SLEEP_S of lying down: no request", nw.monitor_tick() is False)
    sens._last_human_ts = t0 + 200
    check("a later word: one request", nw.monitor_tick() is True and nw.pending() is not None)
    check("request row logged, source human_message", [r["kind"] for r in rows()] == ["wake_request"] and rows()[0]["source"] == "human_message")
    sens._last_human_ts = t0 + 300
    check("second word / second tick: still one request", nw.monitor_tick() is False and len(rows()) == 1)

    print("[3] observe mode (default flag)")
    check("boundary False (nothing skipped) at every stage", all(nw.boundary(s) is False for s in ("chapter", "journal", "week_rollup", "peers", "consolidation", "dream", "rest")))
    bs = [r for r in rows() if r["kind"] == "boundary"]
    check("7 boundary rows, would_skip True, skipped False", len(bs) == 7 and all(r["would_skip"] and not r["skipped"] for r in bs))
    fn = FakeNight(); time.sleep(0.05)
    sm = nw.finish(fn)
    check("woken_by pipeline_end in observe mode", fn.notes["woken_by"] == "pipeline_end" and sm["mode"] == "observe")
    check("latency + would_have_woken_at + stages recorded", sm["latency_s"] >= 0 and sm["would_have_woken_at_s"] is not None and len(sm["stages"]) == 7)
    check("summary row logged; request cleared", rows()[-1]["kind"] == "wake_summary" and nw.pending() is None)

    print("[4] live mode (flag patched in the test only)")
    nw.reset(); nw._handled_ts = 0.0
    sens.state["asleep_since"] = t0 + 1000     # a new sleep
    sens._last_human_ts = t0 + 1500
    nw.WAKE_ON_HUMAN = True
    try:
        check("new sleep, new request", nw.monitor_tick(t0 + 1600) is True)
        check("boundary True (skip)", nw.boundary("journal") is True)
        fn2 = FakeNight(); sm2 = nw.finish(fn2)
        check("woken_by human_message", fn2.notes["woken_by"] == "human_message" and sm2["mode"] == "live")
    finally:
        nw.WAKE_ON_HUMAN = False

    print("[5] no request")
    n_before = len(rows())
    nw.reset()
    fn3 = FakeNight()
    check("boundary False, finish notes pipeline_end, no row", nw.boundary("dream") is False and nw.finish(fn3) is None
          and fn3.notes["woken_by"] == "pipeline_end" and len(rows()) == n_before)

    print("[2b] lifecycle")
    nw.reset(); nw._handled_ts = 0.0
    sens.state["asleep_since"] = t0 + 2000; sens._last_human_ts = t0 + 2100
    nw.monitor_tick()
    sens.state["asleep_since"] = t0 + 3000   # the next sleep, no new word
    check("new sleep forgets the old request", nw.monitor_tick() is False and nw.pending() is None)
    sens._last_human_ts = t0 + 3100; nw.monitor_tick()
    sens.state["asleep"] = False
    nw.monitor_tick()
    check("waking clears it", nw.pending() is None)

    print("[6] wiring (AST/text)")
    node = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
    tree = ast.parse(node)
    gated = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Try) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Call) \
                and getattr(n.body[0].value.func, "id", "") == "_wake_gate":
            gated.append(n.body[0].value.args[0].value)
            check(f"  gate {gated[-1]!r}: its try has an except Exception handler",
                  any(isinstance(h.type, ast.Name) and h.type.id == "Exception" for h in n.handlers))
    check("5 optional stages gated", sorted(gated) == sorted(["chapter", "journal", "week_rollup", "peers", "consolidation"]))
    check("rest sliced + boundary('rest')", 'boundary("rest")' in node and "min(5.0, rest - _slept)" in node)
    check("finish() before night.wake()", node.index("_nw2.finish(_night)") < node.index("_wk = _night.wake()"))
    check("reset() at begin", node.index("_nw0.reset()") < node.index("_bed = _night.to_bed()"))
    orch = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
    check("orchestrator checks the dream boundary before DreamNode", orch.index('_nw.boundary("dream")') < orch.index("await DreamNode().synthesise(state)"))
    check("dream still runs when not woken", "None if (_pool_thin or _woken) else await DreamNode().synthesise(state)" in orch)
    sensrc = (ROOT / "core" / "sensorium.py").read_text(encoding="utf-8")
    check("sensorium.tick calls monitor_tick", "_nw.monitor_tick(now)" in sensrc)

    print("[7] _wake_gate semantics")
    import importlib
    # exec just the two definitions (importing the whole node pulls the world); they only use core.night_wake
    src = "\n".join(l for l in node.split("\n"))
    start = src.index("class _WakeSkip"); end = src.index("from core.sleep_offloop import off_loop")
    ns = {}
    exec(src[start:end], ns)
    nw.reset(); nw._handled_ts = 0.0
    sens.state["asleep"] = True; sens.state["asleep_since"] = t0 + 5000; sens._last_human_ts = t0 + 5100
    nw.monitor_tick()
    ns["_wake_gate"]("x")
    check("observe mode: gate does not raise", True)
    nw.WAKE_ON_HUMAN = True
    try:
        raised = False
        try:
            try:
                ns["_wake_gate"]("x")
            except Exception:
                raised = True       # the stage's own fail-open handler
        finally:
            pass
        check("live mode: gate raises _WakeSkip, absorbed by `except Exception`", raised)
        check("_WakeSkip is an Exception", issubclass(ns["_WakeSkip"], Exception))
    finally:
        nw.WAKE_ON_HUMAN = False
    nw.reset()
    ns["_wake_gate"]("x")
    check("no request: gate never raises", True)

    print("[8] evaluate + live files")
    ev = nw.evaluate(LOG)
    check("evaluate counts requests/summaries", ev["requests"] >= 2 and ev["summaries"] >= 2)
    check("live shadow log untouched", (LIVE.stat().st_size if LIVE.exists() else None) == live_before)
finally:
    for k, v in st_backup.items():
        if v == "__absent__": sens.state.pop(k, None)
        else: sens.state[k] = v
    sens._last_human_ts = hts_backup
    nw.reset(); nw.WAKE_ON_HUMAN = flag0

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
