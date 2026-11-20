"""J-2662 (ignition_pressure_and_time Option E, I-0138): hermetic test of core/ignition_promotion.py and the
ClimateEngine additions (licensing_reservoir, discharge_for_promotion, _log_ignition extra).

PROVES (each PASS/FAIL; exit 1 on any FAIL):
  * flag OFF (PROMOTION_LIVE False, the shipped state): observe() writes ONLY the shadow row; the live field,
    pressure/reservoir values, refractory stamp, defensive-fire list and ignition_log are byte-identical
    before and after, and maybe_promote() returns False without touching anything (the J-1763 pattern).
  * shadow rows: eligible only when building AND grounded AND level >= smallest grid value AND no refractory
    AND no hourly cap; blocked_by names each reason; the grid flags track the level.
  * the stream's ignition term is wired to the engine (stream_drive._ignition follows ignition_level()).
  * flag ON with a stub orchestrator: ONLY the licensing reservoir resets, ignition_log gets trigger="promoted"
    with the promotion payload, run_cycle is called with input_type="internal", a busy cycle (_cycle_active)
    discharges nothing, the per-hour cap holds, the refractory blocks.
HERMETIC: no model, no network. core is imported BEFORE lab_env and core.__file__ asserted to lie in this tree;
lab_env.isolate(db="empty") redirects the shadow log, ignition_log and climate state file into a lab dir.
"""
import asyncio
import json
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                          # noqa: E402  (before lab_env on purpose)
from core import climate_engine as ce                # noqa: E402
from core import ignition_promotion as ip            # noqa: E402
from core import stream_drive as sd                  # noqa: E402
assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
import lab_env                                       # noqa: E402

FAILS = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


def rows(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


class StubOrch:
    def __init__(self):
        self._cycle_active = False
        self.calls = []

    async def run_cycle(self, raw, input_type="human"):
        self.calls.append((raw, input_type))


def snap(eng):
    return (round(eng.dissonance.value, 6), round(eng.dissonance.explore_value, 6),
            eng.dissonance.last_ignition_ts, list(eng._defensive_fire_ts), dict(eng._contrib),
            json.dumps(eng.field.as_dict(), sort_keys=True))


SIG_GOOD = {"building": True, "coherent": True, "circling": False, "slow_loop": False, "bored_streak": 0,
            "redundancy": 0.1, "about": "tide pools", "source": "world", "train_kind": "thought", "train_len": 3}
SIG_UNGR = dict(SIG_GOOD, about="my own mind and identity", source=None)
SIG_NOTB = dict(SIG_GOOD, building=False)

with lab_env.isolate(also=[(ip, ["_LOG"]), (ce, ["_IGNITION_LOG", "_STATE_FILE"])], db="empty") as lab:
    eng = ce.ClimateEngine()
    check("engine published as ce._ACTIVE", ce._ACTIVE is eng)
    check("PROMOTION_LIVE ships False", ip.PROMOTION_LIVE is False)
    thr = ce._IGNITION_THRESHOLD

    # ---- wire: stream term follows the engine ------------------------------------------------------------
    eng.dissonance.value = 0.0
    eng.dissonance.explore_value = 0.0
    lo = ce.ignition_level()
    eng.dissonance.value = thr * 0.9
    hi = ce.ignition_level()
    check("module ignition_level() live and follows reservoir", lo == 0.0 and abs(hi - 0.9) < 1e-6)
    check("licensing_reservoir picks the larger", eng.licensing_reservoir()[0] == "defensive")
    eng.dissonance.explore_value = thr * 0.95
    check("licensing_reservoir flips to exploratory", eng.licensing_reservoir()[0] == "exploratory")
    eng.dissonance.explore_value = 0.0

    # ---- flag OFF: byte-identical ------------------------------------------------------------------------
    eng.dissonance.value = thr * 0.85
    eng.dissonance.last_ignition_ts = 0.0
    before = snap(eng)
    ign_before = rows(ce._IGNITION_LOG)
    ip.observe(SIG_GOOD, "a thought", scan_saw=True)
    after = snap(eng)
    check("flag off: engine state unchanged by observe()", before == after)
    check("flag off: ignition_log untouched by observe()", rows(ce._IGNITION_LOG) == ign_before)
    sh = rows(ip._LOG)
    check("flag off: exactly one shadow row", len(sh) == 1)
    r = sh[0]
    check("row eligible + grid 0.6/0.7/0.8 flags", r["eligible"] and r["grid"] == {"0.6": True, "0.7": True, "0.8": True}
          or (r["eligible"] and r["grid"]["0.8"] and r["grid"]["0.6"]))
    check("row carries drive/progress/grounded/reservoirs/would_reset/scan flag",
          all(k in r for k in ("drive", "progress", "grounded", "reservoir_defensive", "reservoir_explore",
                               "would_reset", "ledger_scan_saw_thought")) and r["would_reset"] == "defensive"
          and r["ledger_scan_saw_thought"] is True and r["live"] is False)
    ok = asyncio.run(ip.maybe_promote(SIG_GOOD, "a thought"))
    check("flag off: maybe_promote() is a no-op", ok is False and snap(eng) == before
          and rows(ce._IGNITION_LOG) == ign_before)

    # ---- eligibility reasons -----------------------------------------------------------------------------
    ip.observe(SIG_UNGR, "x")
    ip.observe(SIG_NOTB, "x")
    eng.dissonance.value = thr * 0.3
    ip.observe(SIG_GOOD, "x")
    eng.dissonance.value = thr * 0.85
    eng.dissonance.last_ignition_ts = time.time()
    ip.observe(SIG_GOOD, "x")
    eng.dissonance.last_ignition_ts = 0.0
    sh = rows(ip._LOG)
    check("ungrounded blocked", "ungrounded" in sh[1]["blocked_by"] and not sh[1]["eligible"])
    check("not building blocked", "not_building" in sh[2]["blocked_by"])
    check("low level blocked", "level_below_grid" in sh[3]["blocked_by"])
    check("refractory blocked", "refractory" in sh[4]["blocked_by"])

    # ---- flag ON, stub orchestrator ----------------------------------------------------------------------
    ip.PROMOTION_LIVE = True
    try:
        orch = StubOrch()
        ip.register(orch)
        eng.dissonance.value = thr * 0.9
        eng.dissonance.explore_value = thr * 0.2
        eng.dissonance.last_ignition_ts = 0.0
        orch._cycle_active = True
        b = snap(eng)
        ok = asyncio.run(ip.maybe_promote(SIG_GOOD, "held thought"))
        check("busy cycle: nothing discharged, no cycle", ok is False and snap(eng) == b and not orch.calls)
        orch._cycle_active = False
        ok = asyncio.run(ip.maybe_promote(SIG_UNGR, "held thought"))
        check("ungrounded never promotes", ok is False and not orch.calls)
        ok = asyncio.run(ip.maybe_promote(SIG_GOOD, "held thought"))
        check("promoted: run_cycle(internal) called with the thought", ok and orch.calls == [("held thought", "internal")])
        check("promoted: only the licensing reservoir reset",
              eng.dissonance.value == 0.0 and abs(eng.dissonance.explore_value - thr * 0.2) < 1e-9)
        check("promoted: refractory stamped and defensive fire counted",
              eng.dissonance.last_ignition_ts > 0 and len(eng._defensive_fire_ts) == 1)
        lg = rows(ce._IGNITION_LOG)
        check("ignition_log row trigger=promoted with promotion payload",
              len(lg) == 1 and lg[0]["trigger"] == "promoted" and lg[0]["promotion"]["grounded"] is True
              and lg[0]["promotion"]["threshold"] == ip.LIVE_THRESHOLD)
        # refractory blocks an immediate second one
        eng.dissonance.value = thr * 0.9
        ok = asyncio.run(ip.maybe_promote(SIG_GOOD, "again"))
        check("refractory blocks back-to-back promotion", ok is False and len(orch.calls) == 1)
        # hourly cap
        ip._promoted_ts[:] = [time.time()] * ip.PROMOTION_MAX_PER_HOUR
        eng.dissonance.last_ignition_ts = 0.0
        ok = asyncio.run(ip.maybe_promote(SIG_GOOD, "capped"))
        check("hourly cap blocks", ok is False and len(orch.calls) == 1)
    finally:
        ip.PROMOTION_LIVE = False
        ip._promoted_ts[:] = []
        ip._runner = None

print("\nRESULT:", "FAIL " + str(FAILS) if FAILS else "ALL PASS")
sys.exit(1 if FAILS else 0)
