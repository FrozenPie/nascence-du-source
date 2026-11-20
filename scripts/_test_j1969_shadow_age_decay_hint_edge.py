"""_test_j1969_shadow_age_decay_hint_edge.py -- proving test for D-0363 (B) + edge-triggered shadow hint (J-1969).
Run from a WORKTREE: python scripts/_test_j1969_shadow_age_decay_hint_edge.py
Pure in-memory: no store, no DB, no log is opened or written (the orchestrator method is called unbound on a
SimpleNamespace; the climate helper is a pure function)."""
from __future__ import annotations
import sys, time, types
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  core FIRST
assert Path(core.__file__).resolve().is_relative_to(ROOT)
if ROOT == Path(r"C:\Nascence"):
    sys.exit("REFUSED: run from a worktree")
from core import schema, climate_engine as ce, orchestrator as orch  # noqa: E402

fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: fails.append(name)

H6 = 6 * 3600
legacy = lambda age: 0.5 ** (age / H6)
check("flags default on", schema.SHADOW_AGE_DECAY_ON is True and schema.CLIMATE_SHADOW_HINT_EDGE_ON is True)
check("half-life 3h", schema.SHADOW_ACTIVATION_HALFLIFE_SECS == 3 * 3600)
w = ce._shadow_age_weight(3 * 3600, legacy(3 * 3600))
check("3h-old event weighs 0.5 (not 0.707)", abs(w - 0.5) < 1e-9)
check("fresh event weighs 1.0", abs(ce._shadow_age_weight(0, 1.0) - 1.0) < 1e-9)
check("12h-old weighs 1/16 (legacy 1/4)", abs(ce._shadow_age_weight(12 * 3600, legacy(12 * 3600)) - 0.0625) < 1e-9)
schema.SHADOW_AGE_DECAY_ON = False
check("flag off returns legacy weight", ce._shadow_age_weight(3 * 3600, legacy(3 * 3600)) == legacy(3 * 3600))
schema.SHADOW_AGE_DECAY_ON = True
# 40 events, one every 4 min over ~2.6h: decayed raw < legacy raw
ages = [i * 240 for i in range(40)]
raw_new = sum(ce._shadow_age_weight(a, legacy(a)) for a in ages); raw_old = sum(legacy(a) for a in ages)
check("decayed raw below legacy raw for an aging pool", raw_new < raw_old)

SH = ce._EXECUTIVE_HINTS["shadow_activation"]; OT = ce._EXECUTIVE_HINTS["completion_tension"]
def mk(): return types.SimpleNamespace(state=types.SimpleNamespace(climate_hint=None), _shadow_hint_active=False, _shadow_hint_last_seen_ts=0.0)
def step(o, hint, now=None):
    o.state.climate_hint = hint
    if now is not None:
        real = time.time; time.time = lambda: now
    try: orch.Orchestrator._edge_trigger_shadow_hint(o)
    finally:
        if now is not None: time.time = real
    return o.state.climate_hint
o = mk(); t = 1000.0
check("edge: first shadow hint passes", step(o, SH, t) == SH)
check("edge: second cycle silent", step(o, SH, t + 60) is None)
check("edge: third cycle silent", step(o, SH, t + 120) is None)
check("other hint untouched", step(o, OT, t + 130) == OT)
check("still silent after short gap (<rearm)", step(o, SH, t + 150) is None)
check("hint absent past rearm window", step(o, None, t + 150 + 700) is None and o._shadow_hint_active is False)
check("re-armed: new episode speaks again", step(o, SH, t + 900) == SH)
schema.CLIMATE_SHADOW_HINT_EDGE_ON = False
o2 = mk()
check("flag off: every cycle passes", step(o2, SH, 1.0) == SH and step(o2, SH, 2.0) == SH)
print("RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL")
sys.exit(1 if fails else 0)
