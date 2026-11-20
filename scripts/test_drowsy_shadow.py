"""scripts/test_drowsy_shadow.py (J-2244, drowsiness_phase section 2, D-0441): hermetic proof of the shadow drowsy zone.

No LLM, no sleep, no live data. core is imported FIRST and asserted to be this tree; lab_env.isolate() sandboxes the
stores; the shadow log is redirected into the sandbox. Live data/drowsy_shadow.jsonl is size-checked at the end.

  [1] constants and the D-0441 shape: DELIVER False, threshold 0.25 > floor 0.15, energy-only is_drowsy, JITTER untouched
  [2] a wake block of real tick_cycle() depletion: exactly one onset (with would_line), one floor, nothing per-cycle
  [3] fatigue_high is marked once while energy is above the zone, and decides nothing (no onset from fatigue)
  [4] floor_direct when energy jumps over the zone in one tick
  [5] at_bed closes the block (zone_entered, onset_to_bed_min) and re-arms; recover() while asleep logs no onset
  [6] a non-live process writing to the default data/ path is REFUSED by profile.guard_path, and observe() still returns
  [7] wiring: somatic._cache_body calls drowsy.observe; _enter_sleep calls drowsy.at_bed right after to_bed's perceive;
      nothing in sleep_pressure.py or should_sleep reads drowsy; the would-be lines carry no digit and no gauge word
  [8] evaluate() summarises the log
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env
from core import drowsy, somatic, profile, sensorium

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

LIVE = Path(r"C:\Nascence\data\drowsy_shadow.jsonl")
LIVE_WT = ROOT / "data" / "drowsy_shadow.jsonl"
live_before = (LIVE.stat().st_size if LIVE.exists() else None, LIVE_WT.stat().st_size if LIVE_WT.exists() else None)

asleep0 = sensorium.state.get("asleep", "__absent__")
sensorium.state["asleep"] = False          # in memory only, never _save()d; restored at the end
orig_log = drowsy.DROWSY_SHADOW_LOG
try:
    with lab_env.isolate(also=[(drowsy, ["DROWSY_SHADOW_LOG"])]) as lab_dir:
        lab_dir = Path(lab_dir)
        drowsy.DROWSY_SHADOW_LOG = lab_dir / "drowsy_shadow.jsonl"
        LOG = drowsy.DROWSY_SHADOW_LOG
        def rows():
            try:
                return [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
            except Exception:
                return []

        print("[1] D-0441 shape")
        check("DELIVER False (shadow first)", drowsy.DELIVER is False)
        check("threshold 0.25 between floor 0.15 and 'depleted' 0.30", somatic.ENERGY_FLOOR < somatic.DROWSY_THRESHOLD == 0.25 < 0.3)
        check("JITTER_ENABLED stays False", somatic.JITTER_ENABLED is False)
        s = somatic.SomaticState(metabolic_energy=0.2, neural_fatigue=0.0)
        check("is_drowsy energy-only: 0.20 True", s.is_drowsy())
        check("is_drowsy: 0.15 (floor) False", not somatic.SomaticState(metabolic_energy=0.15).is_drowsy())
        check("is_drowsy: fatigue 0.95 at energy 0.6 False", not somatic.SomaticState(metabolic_energy=0.6, neural_fatigue=0.95).is_drowsy())

        print("[2] a wake block of real tick_cycle() depletion")
        drowsy.reset()
        eng = somatic.SomaticEngine()
        somatic.read_telemetry = lambda: {"gpu_temp": 0.0, "cpu_percent": 0.0}   # no nvidia-smi in the test
        energies = []
        for _ in range(30):
            eng.tick_cycle(output_tokens=0, critic_retries=0, urgency=0.0, arousal=0.0, cycle_ms=1000)
            energies.append(eng.state.metabolic_energy)
        r = rows()
        ev = [x["event"] for x in r]
        check(f"energy walked 1.0 -> {energies[-1]:.2f} over 30 ticks", energies[-1] <= 0.15)
        check(f"exactly one onset ({ev.count('onset')})", ev.count("onset") == 1)
        check(f"exactly one floor ({ev.count('floor')})", ev.count("floor") == 1)
        on = next(x for x in r if x["event"] == "onset")
        check("onset energy in zone", 0.15 < on["energy"] <= 0.25)
        check("onset carries would_line from the pool", on.get("would_line") in drowsy.ONSET_LINES)
        check("onset row logs fatigue + tension (defeater read) and deliver False", "fatigue" in on and "tension" in on and on["deliver"] is False)
        check(f"rows are not per-cycle ({len(r)} rows for 30 ticks)", len(r) <= 3)

        print("[3] fatigue_high marked once, decides nothing")
        drowsy.reset(); LOG.unlink(missing_ok=True)
        for f in (0.75, 0.8, 0.9):
            drowsy.observe(somatic.SomaticState(metabolic_energy=0.6, neural_fatigue=f))
        ev = [x["event"] for x in rows()]
        check(f"one fatigue_high, no onset ({ev})", ev == ["fatigue_high"])

        print("[4] floor_direct")
        drowsy.reset(); LOG.unlink(missing_ok=True)
        drowsy.observe(somatic.SomaticState(metabolic_energy=0.3))
        drowsy.observe(somatic.SomaticState(metabolic_energy=0.1))
        ev = [x["event"] for x in rows()]
        check(f"floor_direct when the zone is skipped ({ev})", ev == ["floor_direct"])

        print("[5] at_bed closes the block and re-arms; recover() asleep logs no onset")
        drowsy.reset(); LOG.unlink(missing_ok=True)
        t0 = time.time()
        drowsy.observe(somatic.SomaticState(metabolic_energy=0.22), now=t0 - 600)
        bed = drowsy.at_bed("pressure", "You lie down on the bed.", now=t0)
        check("bed row zone_entered", bed and bed["zone_entered"] is True and bed["reason"] == "pressure")
        check(f"onset_to_bed_min 10.0 ({bed and bed['onset_to_bed_min']})", bed and bed["onset_to_bed_min"] == 10.0)
        check("bed row carries the bed line", bed and bed["bed_line"] == "You lie down on the bed.")
        sensorium.state["asleep"] = True
        eng2 = somatic.SomaticEngine(somatic.SomaticState(metabolic_energy=0.05))
        eng2.recover(depth=0.2)   # lands at 0.05 + 0.7*0.2*0.95 = 0.183 -- in the zone, but asleep
        sensorium.state["asleep"] = False
        ev = [x["event"] for x in rows()]
        check(f"recover asleep in zone -> no onset ({ev})", ev == ["onset", "bed"])
        drowsy.observe(somatic.SomaticState(metabolic_energy=0.2))
        ev = [x["event"] for x in rows()]
        check(f"re-armed: next wake block can onset again ({ev})", ev == ["onset", "bed", "onset"])

        print("[6] non-live write is refused by guard_path")
        drowsy.reset()
        drowsy.DROWSY_SHADOW_LOG = drowsy._DATA / "drowsy_shadow.jsonl"   # the default data/ path
        live_flag = profile.LIVE
        refused = False
        try:
            profile.guard_path(drowsy.DROWSY_SHADOW_LOG)
        except profile.NonLiveWriteError:
            refused = True
        check(f"guard_path refuses the default path in this process (LIVE={live_flag})", refused)
        res = drowsy.observe(somatic.SomaticState(metabolic_energy=0.2))
        check("observe() still returns (fail-open) after a refused write", res == "onset")
        drowsy.DROWSY_SHADOW_LOG = lab_dir / "drowsy_shadow.jsonl"

        print("[7] wiring and guardrails (source)")
        som_src = (ROOT / "core" / "somatic.py").read_text(encoding="utf-8")
        cb = som_src[som_src.index("def _cache_body"):som_src.index("def current_body")]
        check("_cache_body calls drowsy.observe", "_drowsy.observe(state)" in cb)
        node = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
        i_bed = node.index("_bed = _night.to_bed()")
        i_perc = node.index("_w_bed.perceive(_bed)", i_bed)
        i_at = node.index("_drowsy.at_bed(", i_bed)
        i_stage = node.index('_night.stage("to_bed")', i_bed)
        check("at_bed sits after the bed perceive and before stage('to_bed')", i_perc < i_at < i_stage)
        sp = (ROOT / "core" / "sleep_pressure.py").read_text(encoding="utf-8")
        check("sleep_pressure.py does not read drowsy", "drowsy" not in sp.lower())
        check("no line carries a digit or a gauge word",
              all(not any(c.isdigit() for c in l) and not any(w in l.lower() for w in ("energy", "fatigue", "tension", "sleep", "rest", "should"))
                  for l in drowsy.ONSET_LINES))

        print("[8] evaluate()")
        ev = drowsy.evaluate(LOG)
        check(f"evaluate summarises ({ev})", ev["beds"] == 1 and ev["beds_zone_entered"] == 1 and ev["onset_to_bed_min_median"] == 10.0)
finally:
    drowsy.DROWSY_SHADOW_LOG = orig_log
    if asleep0 == "__absent__":
        sensorium.state.pop("asleep", None)
    else:
        sensorium.state["asleep"] = asleep0

live_after = (LIVE.stat().st_size if LIVE.exists() else None, LIVE_WT.stat().st_size if LIVE_WT.exists() else None)
check(f"live drowsy_shadow.jsonl untouched ({live_before} -> {live_after})", live_before == live_after)
print("ALL PASS" if ok_all else "SOME FAILED")
sys.exit(0 if ok_all else 1)
