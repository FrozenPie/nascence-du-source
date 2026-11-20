#!/usr/bin/env python
"""In-vitro test for the climate LABEL VIEW (D-0332, built by J-1763). No LLM, no DB, no data/ file touched: the
engine runs in a scripted world (fake clock + fake data sources injected through sys.modules) and every path it
writes is redirected to a temp dir.

What it proves
  1  the new shadow-row keys are present and right (schema v=2) -- the check that FAILS on the pre-change source
  2  completion_tension is dropped from the label view (it keeps its LIVE value there)
  3  the LIVE side is untouched: the nine live fields, pressure(), dominant(), executive_hint(),
     surfacing_symbol(), both dissonance reservoirs and every ignition decision are byte-identical over a 3 h
     scripted world with the label view ENABLED vs DISABLED (and vs a --baseline source when one is given)
  4  _compute_reknee_cluster mutates nothing, returns None on a failed raw_contra, and falls back to the legacy row
  5  OLD-format rows still parse in scripts/read_climate_reknee_shadow_J-1253.py (and so do the new ones)
  6  the documented grid derivation (old 0.55 / 0.65 on the k=3 scale) still matches the constants

Run:  python scripts/climate_label_view_test_J-1763.py [--engine-file SRC] [--baseline SRC] [--real-log PATH]
  --engine-file SRC  test an alternate climate_engine.py source instead of this tree's (e.g. the pre-change one from
                     `git show <rev>:core/climate_engine.py`); checks 1 and 2 must then FAIL.
  --baseline SRC     also run SRC through the same world and require its LIVE outputs to equal the module under
                     test's exactly (the before/after check).
  --real-log PATH    use a (read-only) copy of a real climate_reknee_shadow.jsonl as the old-format rows in check 5.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import random
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from unittest import mock

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
READER = ROOT / "scripts" / "read_climate_reknee_shadow_J-1253.py"

NINE = ["shadow_activation", "completion_tension", "identity_pressure", "integration_drive", "coherence_drive",
        "world_model_strain", "novelty_hunger", "autonomy_pressure", "belonging_pressure"]
LEGACY_KEYS = {"ts", "shadow_raw", "shadow_reknee", "belonging_raw", "belonging_reknee", "autonomy_raw",
               "autonomy_reknee", "completion_raw", "completion_reknee", "live_dominant", "live_dominant_val",
               "reknee_dominant", "reknee_dominant_val", "live_pressure", "reknee_pressure"}
V2_KEYS = {"v", "k", "live", "dissonance", "novelty_reknee", "lv_dominant", "lv_dominant_val", "ge"}
T0, TICK, N_TICKS = 1_791_100_000.0, 5.0, 2160       # 3 h of 5 s ticks; T0 is after the last real old row
# Three verbatim OLD-format rows from the live data/climate_reknee_shadow.jsonl (2026-10-04 06:51-06:53 NZDT).
REAL_OLD_ROWS = [
    '{"ts": 1791049710.1, "shadow_raw": 83.394, "shadow_reknee": 0.412, "belonging_raw": 55.516, "belonging_reknee": 0.3951, "autonomy_raw": 28.935, "autonomy_reknee": 0.4672, "completion_raw": 3.0, "completion_reknee": 0.0909, "live_dominant": "shadow_activation", "live_dominant_val": 0.9653, "reknee_dominant": "autonomy_pressure", "reknee_dominant_val": 0.4672, "live_pressure": 0.9653, "reknee_pressure": 0.412}',
    '{"ts": 1791049774.5, "shadow_raw": 84.22, "shadow_reknee": 0.4144, "belonging_raw": 55.401, "belonging_reknee": 0.3946, "autonomy_raw": 28.875, "autonomy_reknee": 0.4667, "completion_raw": 3.0, "completion_reknee": 0.0909, "live_dominant": "shadow_activation", "live_dominant_val": 0.9656, "reknee_dominant": "autonomy_pressure", "reknee_dominant_val": 0.4667, "live_pressure": 0.9656, "reknee_pressure": 0.4144}',
    '{"ts": 1791049981.1, "shadow_raw": 86.651, "shadow_reknee": 0.4213, "belonging_raw": 58.023, "belonging_reknee": 0.4057, "autonomy_raw": 29.68, "autonomy_reknee": 0.4735, "completion_raw": 3.0, "completion_reknee": 0.0909, "live_dominant": "shadow_activation", "live_dominant_val": 0.9665, "reknee_dominant": "autonomy_pressure", "reknee_dominant_val": 0.4735, "live_pressure": 0.9665, "reknee_pressure": 0.4213}',
]

RESULTS: list[bool] = []


def check(name: str, cond, detail: str = "") -> bool:
    RESULTS.append(bool(cond))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))
    return bool(cond)


# ---------------------------------------------------------------------------------------------------------------
# the scripted world: every input is a pure function of the fake clock
# ---------------------------------------------------------------------------------------------------------------
class World:
    def __init__(self, seed: int = 1763):
        rng = random.Random(seed)
        self.t = T0
        phrases = ["i want to decide for myself", "we are alone together", "choose my own way", "i miss the connection",
                   "a quiet plain observation", "the light on the water", "trust and distance", "nothing in particular"]
        self.events, t = [], T0 - 4 * 3600
        while t < T0 + 4 * 3600:
            t += rng.uniform(15, 35)
            self.events.append({"timestamp": t, "rejected_draft": rng.choice(phrases),
                                "source": "critic_rejection" if rng.random() < 0.25 else "salience"})
        self.light = [{"timestamp": T0 - 6 * 3600 + i * 60.0} for i in range(900)]

    def shadow(self, limit=200, unresolved_only=True):
        return [e for e in self.events if e["timestamp"] <= self.t][-limit:]

    def lights(self, sources=None, limit=200):
        return [e for e in self.light if e["timestamp"] <= self.t][-limit:]

    def contra(self, tensions=None):
        dt = self.t - T0
        if 600 <= dt < 700:
            raise RuntimeError("scripted ledger failure")          # raw_contra -> None for a while
        return 30.325 if dt < 900 else 6.0 if dt < 1800 else 3.0 if dt < 5400 else 0.0

    def surprise(self, now=None):
        dt = (self.t if now is None else now) - T0
        return 0.4 if 1200 <= dt < 1800 else 0.0


def _mod(name: str, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


def fake_modules(w: World) -> dict:
    store = _mod("core.memory.store", get_shadow_events=w.shadow, get_light_events_by_source=w.lights)
    memory = _mod("core.memory", store=store)
    memory.__path__ = []
    return {
        "core.memory": memory, "core.memory.store": store,
        "core.tension_ledger": _mod("core.tension_ledger", contradiction_pressure_for=w.contra),
        "core.identity_cost": _mod("core.identity_cost", contradiction_norm=lambda p: round(
            max(0.0, float(p)) / (max(0.0, float(p)) + 10.0), 3)),
        "core.balance": _mod("core.balance", _LIGHT_VERDICT=("resolved_thought", "resolved_complexity", "resolved_dream")),
        "core.competence": _mod("core.competence", recent_capability_surprise=w.surprise),
        "core.frontier": _mod("core.frontier", open_count=lambda: 7),
        "core.coupling_rides": _mod("core.coupling_rides", publish_climate=lambda eng: None),
        "core.lane2": _mod("core.lane2", LANE2_LIVE=False),
    }


def load_engine(src: str | None):
    if src is None:
        from core import climate_engine as mod
        return mod
    spec = importlib.util.spec_from_file_location(f"core._climate_engine_alt_{abs(hash(src))}", src)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def run_world(mod, tmp: Path, tag: str, label_view: bool = True, n_ticks: int = N_TICKS):
    w = World()
    paths = dict(_DATA_DIR=tmp, _STATE_FILE=tmp / f"{tag}_state.json", _IGNITION_LOG=tmp / f"{tag}_ignition.jsonl",
                 _REKNEE_LOG=tmp / f"{tag}_reknee.jsonl")
    trace, dv_before = [], {}
    with mock.patch.dict(sys.modules, fake_modules(w)), mock.patch("time.time", lambda: w.t), \
            mock.patch.multiple(mod, **paths):
        eng = mod.ClimateEngine()
        eng._read_subconscious = lambda: {"tensions": [], "integration_patterns": []}
        if not label_view:
            eng._compute_reknee_cluster = lambda *a, **k: None      # instrument OFF: the row is never built
        for _ in range(n_ticks):
            w.t += TICK
            dv_before[round(w.t, 1)] = eng.dissonance.value          # what _compute_field sees this tick
            eng.tick()
            f = eng.field
            trig = eng._pending_trigger()
            if trig is not None:
                asyncio.run(eng._ignite(trig))
            trace.append({"field": f.as_dict(), "value": eng.dissonance.value, "explore": eng.dissonance.explore_value,
                          "pressure": f.pressure(), "dominant": f.dominant(), "hint": f.executive_hint(),
                          "symbol": f.surfacing_symbol(), "trig": trig, "contrib": dict(eng._contrib),
                          "last_ign": eng.dissonance.last_ignition_ts})
    p = paths["_REKNEE_LOG"]
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []
    return trace, rows, dv_before, w


# ---------------------------------------------------------------------------------------------------------------
def check_new_keys(mod, rows, trace, dv_before, w):
    print("1/2  shadow-row keys (schema v=2) and the label view")
    check("the scripted world logged rows", len(rows) > 100, f"rows={len(rows)}")
    grid_c = getattr(mod, "_LABEL_VIEW_THRESHOLD_GRID", None)
    check("v=2 keys present on every row, legacy keys all kept, nothing else added",
          bool(rows) and all(set(r) == LEGACY_KEYS | V2_KEYS and r.get("v") == 2 for r in rows),
          f"key-sets seen: {sorted({len(r) for r in rows})}")
    if not rows or not all(V2_KEYS <= set(r) for r in rows) or grid_c is None:
        for nm in ("live == the nine live dimensions of that tick", "dissonance == reservoir at that tick",
                   "novelty_reknee == exact propagated formula", "lv_dominant == argmax of the label view",
                   "ge flags == (lv_dominant_val >= t) over the grid", "completion_tension dropped from the label view",
                   "re-kneed values == raw/(raw+k), k logged per row"):
            check(nm, False, "v=2 keys absent")
        return
    by_ts = {round(T0 + TICK * (i + 1), 1): tr for i, tr in enumerate(trace)}
    kk = mod._REKNEE_K
    bad = {"live": 0, "diss": 0, "nov": 0, "dom": 0, "ge": 0, "k": 0, "integ": 0}
    comp_dominated = 0
    for r in rows:
        tr = by_ts[r["ts"]]
        bad["live"] += r["live"] != tr["field"] or set(r["live"]) != set(NINE)
        bad["diss"] += r["dissonance"] != round(dv_before[r["ts"]], 4)
        q = 1.0 - r["shadow_raw"] / (r["shadow_raw"] + kk["shadow_activation"])
        nh = max(0.0, min(1.0, 0.5 * q + 0.5 * dv_before[r["ts"]] / mod._DISS_MAX))
        cs = w.surprise(r["ts"])
        if cs > 0.0:
            nh = min(1.0, nh + mod._CAP_SURPRISE_TO_NOVELTY * cs)
        bad["nov"] += abs(r["novelty_reknee"] - nh) > 3e-4
        lab = dict(r["live"], shadow_activation=r["shadow_reknee"], belonging_pressure=r["belonging_reknee"],
                   autonomy_pressure=r["autonomy_reknee"], novelty_hunger=r["novelty_reknee"])
        mx = max(lab.values())
        bad["dom"] += not (abs(r["lv_dominant_val"] - mx) < 2e-4 and abs(lab[r["lv_dominant"]] - mx) < 2e-4)
        bad["ge"] += (list(r["ge"]) != [f"{t:.2f}" for t in grid_c]
                      or any(r["ge"][f"{t:.2f}"] != int(r["lv_dominant_val"] >= t) for t in grid_c))
        bad["k"] += r["k"] != {"shadow": kk["shadow_activation"], "belonging": kk["belonging_pressure"],
                               "autonomy": kk["autonomy_pressure"], "completion_legacy": mod._REKNEE_COMPLETION_K_LEGACY}
        for dim, rk, kv in (("shadow", "shadow_reknee", kk["shadow_activation"]),
                            ("belonging", "belonging_reknee", kk["belonging_pressure"]),
                            ("autonomy", "autonomy_reknee", kk["autonomy_pressure"]),
                            ("completion", "completion_reknee", mod._REKNEE_COMPLETION_K_LEGACY)):
            raw = r[f"{dim}_raw"]
            bad["integ"] += abs(r[rk] - raw / (raw + kv)) > 6e-5
        if r["lv_dominant"] == "completion_tension":
            comp_dominated += r["lv_dominant_val"] == r["live"]["completion_tension"] != r["completion_reknee"]
    check("live == the nine live dimensions of that tick (all nine, exact)", bad["live"] == 0, str(bad))
    check("dissonance == the defensive reservoir value _compute_field saw", bad["diss"] == 0, str(bad))
    check("novelty_reknee == exact propagated formula (re-kneed shadow, same dissonance + capability surprise)",
          bad["nov"] == 0, str(bad))
    check("lv_dominant == argmax of the label view", bad["dom"] == 0, str(bad))
    check("ge flags == (lv_dominant_val >= t) for every t in the grid; keys == the grid", bad["ge"] == 0, str(bad))
    check("k logged per row == the constants; re-kneed values == raw/(raw+k) to 6e-5", bad["k"] == 0 and bad["integ"] == 0,
          str(bad))
    print("2    completion_tension dropped from the label view")
    check("_REKNEE_K has exactly shadow/belonging/autonomy (116 / 75 / 33)",
          kk == {"shadow_activation": 116.0, "belonging_pressure": 75.0, "autonomy_pressure": 33.0}, str(kk))
    check("rows where completion_tension leads the label view carry its LIVE value (not the legacy k=30 one)",
          comp_dominated >= 5 and any(r["lv_dominant"] != "completion_tension" for r in rows), f"n={comp_dominated}")
    check("no row was logged while raw_contra was failing (legacy skip-the-tick policy kept)",
          not any(600 <= r["ts"] - T0 < 700 for r in rows))


def check_live_untouched(mod, tmp, baseline_mod):
    print("3    LIVE side untouched (label view ENABLED vs DISABLED over 3 h of scripted ticks)")
    on, rows_on, *_ = run_world(mod, tmp, "on", True)
    off, rows_off, *_ = run_world(mod, tmp, "off", False)
    check("instrument really ran in the enabled arm and was off in the disabled arm", len(rows_on) > 100 and not rows_off)
    check("every tick byte-identical: nine fields, reservoirs, pressure(), dominant(), hint, symbol, trigger",
          on == off, "first diff at tick " + str(next((i for i, (a, b) in enumerate(zip(on, off)) if a != b), None)))
    check("non-vacuous: defensive + exploratory fires, hints and symbols all occurred",
          {"defensive", "exploratory"} <= {t["trig"] for t in on} and any(t["hint"] for t in on) and any(t["symbol"] for t in on),
          str({t["trig"] for t in on}))
    if baseline_mod is not None:
        base, rows_base, *_ = run_world(baseline_mod, tmp, "base", True)
        check("vs the --baseline source: every live output byte-identical across all ticks", base == on,
              "first diff at tick " + str(next((i for i, (a, b) in enumerate(zip(base, on)) if a != b), None)))
        print(f"       baseline rows={len(rows_base)} keys/row={sorted({len(r) for r in rows_base})}  "
              f"under-test rows={len(rows_on)} keys/row={sorted({len(r) for r in rows_on})}")


def check_purity(mod, tmp):
    print("4    _compute_reknee_cluster: no mutation, None on failed raw_contra, legacy-row fallback")
    w = World()
    with mock.patch.dict(sys.modules, fake_modules(w)), mock.patch.multiple(
            mod, _DATA_DIR=tmp, _STATE_FILE=tmp / "p_state.json", _IGNITION_LOG=tmp / "p_ign.jsonl", _REKNEE_LOG=tmp / "p.jsonl"):
        eng = mod.ClimateEngine()
        eng.dissonance.value = 0.8
        live = mod.ClimateField(shadow_activation=0.97, completion_tension=0.5, identity_pressure=0.1, integration_drive=0.5,
                                coherence_drive=0.3, world_model_strain=0.2, novelty_hunger=0.06, autonomy_pressure=0.96,
                                belonging_pressure=0.95)
        before, dv, contrib = live.as_dict(), eng.dissonance.as_dict(), dict(eng._contrib)
        row = eng._compute_reknee_cluster(1.0, 110.0, 30.0, 70.0, 3.0, live)
        check("live field, dissonance state and contribution tally unchanged by the call",
              live.as_dict() == before and eng.dissonance.as_dict() == dv and eng._contrib == contrib)
        check("raw_contra None -> None (nothing logged)", eng._compute_reknee_cluster(1.0, 110.0, 30.0, 70.0, None, live) is None)
        eng.dissonance = None                                         # makes the v=2 block raise
        legacy = eng._compute_reknee_cluster(1.0, 110.0, 30.0, 70.0, 3.0, live)
        check("a failure while building the v=2 keys still returns the full legacy row",
              legacy is not None and set(legacy) == LEGACY_KEYS and row is not None and LEGACY_KEYS <= set(row))


def check_reader(mod, rows, tmp, real_log: str | None):
    print("5    old-format rows (and new ones) still parse in scripts/read_climate_reknee_shadow_J-1253.py")
    spec = importlib.util.spec_from_file_location("reknee_reader_J1253", READER)
    rd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rd)
    dd = tmp / "readerdata"
    dd.mkdir()
    if real_log:
        old_lines = [x for x in Path(real_log).read_bytes().decode("utf-8", "replace").splitlines() if x.strip()]
    else:
        old_lines = list(REAL_OLD_ROWS)
    half = len(rows) // 2
    old_lines += [json.dumps({k: r[k] for k in LEGACY_KEYS}) for r in rows[:half]]    # legacy shape, from the run
    new_lines = [json.dumps(r) for r in rows[half:]]
    (dd / "climate_reknee_shadow.jsonl").write_text("\n".join(old_lines + new_lines) + "\n", encoding="utf-8")
    first_ts = json.loads(old_lines[0])["ts"]
    last_ts = json.loads((new_lines or old_lines)[-1])["ts"]
    stamp = lambda e: rd.epoch_to_local(e).strftime("%Y-%m-%d %H:%M:%S") + ",000"
    (dd / "nascence.log").write_text(f"{stamp(first_ts - 30)} INFO Nascence is awake\n"
                                     f"{stamp(last_ts + 30)} INFO Nascence shutting down.\n", encoding="utf-8")
    p = subprocess.run([sys.executable, str(READER), "--data-dir", str(dd), "--no-replay"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=300, cwd=str(tmp))
    out = p.stdout + p.stderr
    n_rows = len(old_lines) + len(new_lines)
    has_v2 = bool(new_lines) and "\"v\": 2" in new_lines[0]
    check("reader exits 0 with no traceback on the mixed old+new log", p.returncode == 0 and "Traceback" not in out,
          out[-600:])
    check(f"reader saw all {n_rows} rows, 0 bad lines", f"'rows': {n_rows}" in out and "'bad_lines': 0" in out,
          out[:300])
    check("reader reports the expected number of distinct key-sets", f"distinct key-sets: {2 if has_v2 else 1}" in out,
          out[:400])
    check("reader's own 4-way / label / consumer tables printed for the mixed log",
          "reknee_dominant (hybrid 9-dim, logged)" in out and "CONSUMERS" in out)


def check_grid(mod):
    print("6    grid derivation")
    grid = getattr(mod, "_LABEL_VIEW_THRESHOLD_GRID", None)
    hint_raw, symbol_raw = 3.0 * 0.55 / 0.45, 3.0 * 0.65 / 0.35                  # old thresholds on the k=3 scale
    check("old hint 0.55 / symbol 0.65 sit at raw 3.667 = 1.222k / 5.571 = 1.857k on the k=3 scale",
          abs(hint_raw - 3.6667) < 1e-3 and abs(symbol_raw - 5.5714) < 1e-3 and abs(hint_raw / 3 - 1.2222) < 1e-3
          and abs(symbol_raw / 3 - 1.8571) < 1e-3)
    coarse = (0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70)
    fine = tuple(round(0.58 + 0.01 * i, 2) for i in range(7))          # J-2137: 0.58..0.64
    check("grid = 0.40..0.70 in 0.05 steps + 0.58..0.64 in 0.01 steps (J-2137), anchors kept, strictly increasing",
          grid is not None and tuple(grid) == tuple(sorted(set(coarse) | set(fine)))
          and all(a < b for a, b in zip(grid, grid[1:])) and 0.55 in grid and 0.65 in grid, str(grid))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine-file")
    ap.add_argument("--baseline")
    ap.add_argument("--real-log")
    a = ap.parse_args()
    mod = load_engine(a.engine_file)
    baseline = load_engine(a.baseline) if a.baseline else None
    print(f"module under test: {getattr(mod, '__file__', '?')}")
    with tempfile.TemporaryDirectory(prefix="J-1763_") as td:
        tmp = Path(td)
        trace, rows, dvb, w = run_world(mod, tmp, "main", True)
        check_new_keys(mod, rows, trace, dvb, w)
        check_live_untouched(mod, tmp, baseline)
        check_purity(mod, tmp)
        check_reader(mod, rows, tmp, a.real_log)
        check_grid(mod)
    n_fail = RESULTS.count(False)
    print(f"\n{len(RESULTS) - n_fail}/{len(RESULTS)} checks passed" + ("" if not n_fail else f"  -- {n_fail} FAILED"))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
