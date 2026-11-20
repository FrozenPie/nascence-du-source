"""
J-3468 (F-4078 / F-4094): quantify how the store-stamp / idle-row TWIN pairs in data/geometry_tuples.jsonl
change what the Nascence readers report.

READ-ONLY toward data/: the geometry file is opened for reading only; every output goes under --out
(default docs/lab/J-3468_data/ in this tree). No Du process, no DB, no model call, no Ramses.

The twin rule (Nascence-side, written here on purpose; J-3456's shared UDMS loader may later supply the same):
  a STAMP row is a source=='inner_thought' row whose normalised thought[:70] equals the normalised thought[:70] of an
  idle row that follows it within TWIN_WINDOW_S seconds (scanned over the next TWIN_LOOKAHEAD rows, file order).
  Matching is done on the first 70 characters because core/memory/store.py:1080 stamps thought=content[:70] while
  nodes/inner_monologue_node.py:6656 writes the full thought on the idle call. Each idle row can pair with at most
  one stamp (first come, first served), so a stamp can never be claimed twice.

Arms:
  asis      every row, exactly what core.mapping_census.census(dedupe=False) / core.object_graph._load_tuples see
  stripped  asis minus the stamp rows of detected twins (1.2 s rule)
  stripped_wide  same with a 10 s stamp-to-idle gap allowed (sensitivity)
  frozen    asis then core.mapping_census.dedupe_frozen_bursts (shows what the existing same-source collapse does)

Usage:
  python scripts/j3468_twin_row_audit.py                 # full run (several minutes: 100 permutations x 10 pairs x arms)
  python scripts/j3468_twin_row_audit.py --quick          # 10 permutations, 10 shuffles (smoke)
  python scripts/j3468_twin_row_audit.py --path <jsonl>   # another file (the test uses a synthetic one)
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

LIVE_DEFAULT = Path(r"C:\Nascence\data\geometry_tuples.jsonl")
OUT_DEFAULT = ROOT / "docs" / "lab" / "J-3468_data"

TWIN_WINDOW_S = 1.2
WIDE_WINDOW_S = 10.0         # sensitivity arm: stamp-to-idle gaps up to 10 s (the gap tail is long: p99 16.7 s on the live file)
TWIN_LOOKAHEAD = 5
STAMP_SOURCE = "inner_thought"
IDLE_SOURCE = "idle"
HUD_TAIL_BYTES = 120000      # hud/server.py _tail_rows default tail_bytes
HUD_LIMIT = 140              # hud/server.py load_monitor limit

# the whitelisted numeric fields of the six hud/server.py MONITOR_REGISTRY rows that read this file:
# (monitor id, nested key or None, fields)
HUD_GAUGES = (
    ("cognitive_geometry", None, ("n_spaces", "n_sounds", "level", "fire_fuel")),
    ("spatial_world_clocks", None, ("tide_level", "sun_az", "moon_illum", "weather_dir")),
    ("spatial_location", None, ("at_study", "at_garden", "at_shore", "at_wood")),
    ("somatic_body", "body", ("energy", "fatigue", "tension")),
    ("emotions_warm", "affect", ("joy", "trust", "surprise")),
    ("emotions_dark", "affect", ("fear", "anger", "disgust")),
)


def _norm70(s) -> str:
    return " ".join((s or "").split())[:70]


def _is_prefix_twin(stamp_thought, idle_thought) -> bool:
    """store.py stamps content[:70] RAW (newlines and runs of spaces included) while the idle row carries the full
    thought, so compare after whitespace-normalising BOTH sides: the normalised stamp must be a prefix of the
    normalised idle thought. (Normalising then cutting both to 70 chars would wrongly miss pairs whose raw stamp
    contained whitespace runs: found in the first run of this script.)"""
    s = " ".join((stamp_thought or "").split())
    i = " ".join((idle_thought or "").split())
    return len(s) >= 5 and i[:len(s)] == s


def flag_stamp_twins(rows: list[dict], window_s: float = TWIN_WINDOW_S) -> set[int]:
    """Indices (into `rows`, file order) of stamp rows that have an idle twin. Pure function."""
    stamps: set[int] = set()
    claimed_idle: set[int] = set()
    n = len(rows)
    for i, r in enumerate(rows):
        if r.get("source") != STAMP_SOURCE:
            continue
        ts0 = float(r.get("ts") or 0)
        for j in range(i + 1, min(n, i + 1 + TWIN_LOOKAHEAD)):
            c = rows[j]
            if c.get("source") != IDLE_SOURCE or j in claimed_idle:
                continue
            dt = float(c.get("ts") or 0) - ts0
            if dt < -0.05 or dt > window_s + 1e-6:
                continue
            if _is_prefix_twin(r.get("thought"), c.get("thought")):
                stamps.add(i)
                claimed_idle.add(j)
                break
    return stamps


def _present(v) -> bool:
    return v is not None


def hud_presence(t: dict) -> tuple:
    out = []
    for _mid, nested, fields in HUD_GAUGES:
        src = (t.get(nested) or {}) if nested else t
        for f in fields:
            v = src.get(f) if isinstance(src, dict) else None
            out.append(isinstance(v, (int, float)) and not isinstance(v, bool))
    return tuple(out)


def hud_field_names() -> list[str]:
    return [f"{mid}.{f}" for mid, _n, fields in HUD_GAUGES for f in fields]


def compact(t: dict, offset: int, size: int) -> dict:
    return {
        "ts": t.get("ts"), "source": t.get("source"), "place": t.get("place"), "weather": t.get("weather"),
        "fire": t.get("fire"), "objects": t.get("objects"), "body": t.get("body"), "affect": t.get("affect"),
        "level": t.get("level"), "sounds": t.get("sounds"), "unresolved": t.get("unresolved"),
        "thought": (t.get("thought") or "")[:200], "_off": offset, "_size": size, "_pres": hud_presence(t),
    }


def load_compact(path: Path) -> list[dict]:
    rows, off = [], 0
    with open(path, "rb") as f:
        for raw in f:
            size = len(raw)
            try:
                if raw.strip():
                    t = json.loads(raw)
                    rows.append(compact(t, off, size))
            except Exception:
                pass
            off += size
    return rows


def day_of(ts) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(float(ts)))


def twin_census(rows: list[dict], stamps: set[int]) -> dict:
    src = collections.Counter(r.get("source") for r in rows)
    n_idle = src.get(IDLE_SOURCE, 0)
    per_day = collections.defaultdict(lambda: {"rows": 0, "idle": 0, "twins": 0})
    for i, r in enumerate(rows):
        if not r.get("ts"):
            continue
        d = per_day[day_of(r["ts"])]
        d["rows"] += 1
        if r.get("source") == IDLE_SOURCE:
            d["idle"] += 1
        if i in stamps:
            d["twins"] += 1
    unmatched_stamps = sum(1 for i, r in enumerate(rows) if r.get("source") == STAMP_SOURCE and i not in stamps)
    return {
        "rows_total": len(rows), "by_source": dict(src.most_common()),
        "twin_stamp_rows": len(stamps), "inner_thought_rows_without_idle_twin": unmatched_stamps,
        "idle_rows": n_idle, "twin_share_of_idle_cycles": round(len(stamps) / n_idle, 4) if n_idle else None,
        "twin_share_of_all_rows": round(len(stamps) / len(rows), 4) if rows else None,
        "per_day": {d: v for d, v in sorted(per_day.items())},
    }


def stamp_vs_idle_fields(rows: list[dict], stamps: set[int]) -> dict:
    """Per HUD field: share of twin STAMP rows vs idle rows carrying a numeric value."""
    names = hud_field_names()
    idle_idx = [i for i, r in enumerate(rows) if r.get("source") == IDLE_SOURCE]
    out = {}
    for k, name in enumerate(names):
        s = sum(1 for i in stamps if rows[i]["_pres"][k])
        d = sum(1 for i in idle_idx if rows[i]["_pres"][k])
        out[name] = {"stamp_present": round(s / len(stamps), 4) if stamps else None,
                     "idle_present": round(d / len(idle_idx), 4) if idle_idx else None}
    extra = {}
    for label, getter in (("level", lambda r: r.get("level")), ("unresolved", lambda r: r.get("unresolved")),
                          ("affect", lambda r: r.get("affect")), ("body", lambda r: r.get("body")),
                          ("sounds", lambda r: r.get("sounds")), ("place", lambda r: r.get("place"))):
        s = sum(1 for i in stamps if getter(rows[i]) not in (None, {}, []))
        d = sum(1 for i in idle_idx if getter(rows[i]) not in (None, {}, []))
        extra[label] = {"stamp_present": round(s / len(stamps), 4) if stamps else None,
                        "idle_present": round(d / len(idle_idx), 4) if idle_idx else None}
    return {"hud_fields": out, "other_fields": extra}


def hud_window_composition(rows: list[dict], stamps: set[int], step: int = 400, since_ts: float = 0.0) -> dict:
    """Simulate hud/server.py _tail_rows: the window ending at row i is the rows whose byte offset lies within the last
    HUD_TAIL_BYTES of the file as of row i, capped at the last HUD_LIMIT rows. Reports its composition."""
    sizes, ns, sp, ss, sp_strip = [], [], [], [], []
    for i in range(0, len(rows), step):
        if (rows[i].get("ts") or 0) < since_ts:
            continue
        end = rows[i]["_off"] + rows[i]["_size"]
        lo = end - HUD_TAIL_BYTES
        j = i
        while j > 0 and rows[j - 1]["_off"] >= lo:
            j -= 1
        win = list(range(j, i + 1))[-HUD_LIMIT:]
        if len(win) < 5:
            continue
        n_st = sum(1 for k in win if k in stamps)
        ts = [rows[k]["ts"] for k in win if rows[k].get("ts")]
        keep = [rows[k]["ts"] for k in win if k not in stamps and rows[k].get("ts")]
        ns.append(len(win))
        ss.append(n_st / len(win))
        sp.append(max(ts) - min(ts))
        if len(keep) > 1:
            sp_strip.append(max(keep) - min(keep))
    if not ns:
        return {"windows": 0}
    return {
        "windows": len(ns), "median_rows_in_window": statistics.median(ns),
        "median_stamp_share_of_window": round(statistics.median(ss), 4),
        "mean_stamp_share_of_window": round(statistics.mean(ss), 4),
        "median_span_s_asis": round(statistics.median(sp), 1),
        "median_span_s_same_rows_minus_stamps": round(statistics.median(sp_strip), 1) if sp_strip else None,
    }


# ----------------------------------------------------------------------------------------------------------------------
# mapping census arms
# ----------------------------------------------------------------------------------------------------------------------

def mapping_arm(rows: list[dict], n_permutations: int) -> dict:
    from core import mapping_census as mc
    df = mc._dataframe(rows)
    fo = mc.fanout(df)
    sh = mc.split_half_stability(df)
    sc = mc.state_conditioning(df, n_permutations=n_permutations)
    fu = mc.funnel(df)
    fo_means = [v["mean_effective_fanout"] for v in fo.values()]
    return {
        "rows": len(rows),
        "funnel": {k: {"n": v["n"], "top_value": v["top_value"], "top_value_share": v["top_value_share"],
                       "herfindahl": v["herfindahl"], "distinct_values": v["distinct_values"]} for k, v in fu.items()},
        "split_half": {"overall_mean_tvd": sh["summary"]["overall_mean_tvd"],
                       "pairs_tested": sh["summary"]["pairs_tested"],
                       "n_a_values_tested": sh["summary"]["n_a_values_tested"],
                       "by_pair": {k: v["mean_tvd"] for k, v in sh["by_pair"].items()}},
        "state_conditioning": {k: {"n": v.get("n"), "observed_tvd": v.get("observed_tvd"),
                                   "null_mean_tvd": v.get("null_mean_tvd"), "z": v.get("z")}
                               for k, v in sc.items()},
        "fanout": {"pairs": len(fo), "mean_of_mean_effective_fanout": round(sum(fo_means) / len(fo_means), 3)
                   if fo_means else None,
                   "tested_values_total": sum(v["tested_values"] for v in fo.values()),
                   "by_pair": {k: v["mean_effective_fanout"] for k, v in fo.items()}},
    }


def object_graph_arm(rows: list[dict], now_ts: float, n_shuffles: int) -> dict:
    """Feed object_graph._commonality_pass exactly what object_graph._load_tuples would build (ts, sounds, affect),
    from these (possibly stripped) rows."""
    from core import object_graph as og
    tuples = []
    for r in rows:
        if not r.get("ts"):
            continue
        tuples.append({"ts": float(r["ts"]), "sounds": r.get("sounds") or [], "affect": r.get("affect") or {}})
    old = og.N_SHUFFLES
    og.N_SHUFFLES = n_shuffles
    try:
        res = og._commonality_pass(tuples, now_ts, og.WINDOW_DAYS)
    finally:
        og.N_SHUFFLES = old
    return {"n_tuples_alltime": res["n_tuples_alltime"], "n_tuples_windowed": res["n_tuples_windowed"],
            "n_shuffles": res["n_shuffles"], "window_days": res["window_days"],
            "pairs": [{k: p.get(k) for k in ("pair", "n_with_alltime", "n_without_alltime", "weight_alltime", "z",
                                             "verdict", "weight_windowed", "n_with_windowed",
                                             "n_without_windowed")} for p in res["pairs"]]}


def run(path: Path, out_dir: Path, n_permutations: int, n_shuffles: int, skip_arms: bool = False,
        only: list[str] | None = None) -> dict:
    t0 = time.time()
    rows = load_compact(path)
    stamps = flag_stamp_twins(rows)
    result: dict = {"job": "J-3468", "source_file": str(path), "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "twin_rule": {"window_s": TWIN_WINDOW_S, "lookahead_rows": TWIN_LOOKAHEAD,
                                  "stamp_source": STAMP_SOURCE, "idle_source": IDLE_SOURCE, "key": "normalised thought[:70]"},
                    "n_permutations": n_permutations, "n_shuffles": n_shuffles}
    result["twin_census"] = twin_census(rows, stamps)
    result["twin_count_by_window_s"] = {str(w): len(flag_stamp_twins(rows, w)) for w in (0.5, 1.2, 3.0, 10.0, 60.0)}
    stamps_wide = flag_stamp_twins(rows, WIDE_WINDOW_S)
    result["stamp_vs_idle_fields"] = stamp_vs_idle_fields(rows, stamps)
    result["hud_tail_window"] = {
        "all_time": hud_window_composition(rows, stamps),
        "since_2026_09_01": hud_window_composition(rows, stamps, since_ts=time.mktime((2026, 9, 1, 0, 0, 0, 0, 0, -1))),
    }
    if not skip_arms:
        from core import mapping_census as mc
        now_ts = max((float(r["ts"]) for r in rows if r.get("ts")), default=0.0)
        arm_rows = {
            "asis": lambda: rows,
            "stripped": lambda: [r for i, r in enumerate(rows) if i not in stamps],
            "stripped_wide": lambda: [r for i, r in enumerate(rows) if i not in stamps_wide],
            "frozen_only": lambda: mc.dedupe_frozen_bursts(rows),
        }
        wanted = [a for a in arm_rows if only is None or a in only]
        result["mapping_census"] = {a: mapping_arm(arm_rows[a](), n_permutations) for a in wanted}
        result["object_graph_commonality"] = {
            a: object_graph_arm(arm_rows[a](), now_ts, n_shuffles) for a in wanted if a != "frozen_only"}
        result["object_graph_commonality"]["now_ts_used"] = now_ts
    result["elapsed_s"] = round(time.time() - t0, 1)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / ("results.json" if only is None else "results_" + "+".join(only) + ".json")).write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", type=Path, default=LIVE_DEFAULT)
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only", nargs="+", choices=["asis", "stripped", "stripped_wide", "frozen_only"],
                    help="run just these arms (parallel processes); writes results_<arms>.json, merge by hand/report")
    ap.add_argument("--no-arms", action="store_true", help="twin census + HUD only (fast)")
    a = ap.parse_args()
    res = run(a.path, a.out, 10 if a.quick else 100, 10 if a.quick else 100, skip_arms=a.no_arms, only=a.only)
    tc = res["twin_census"]
    print(f"rows={tc['rows_total']} twins={tc['twin_stamp_rows']} idle={tc['idle_rows']} "
          f"share_of_idle={tc['twin_share_of_idle_cycles']} elapsed={res['elapsed_s']}s -> {a.out / 'results.json'}")


if __name__ == "__main__":
    main()
