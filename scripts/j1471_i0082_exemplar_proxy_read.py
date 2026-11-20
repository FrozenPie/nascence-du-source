"""
J-1471 / I-0082 exemplar-memory offline PROXY read (strings_and_sheets).

Implements EXACTLY the pre-registered method in
docs/lab/i0082_exemplar_proxy_metric_sheet.md — written and committed before this script was run
for real. Do not change the method here without updating that file first.

Read-only against every live store. Imports NO core/ module and touches NO live state file: the
six-axis _SOUNDS coordinates and the _WEATHERS severity ladder are copied verbatim from
core/soundscape.py and core/sensorium.py (source lines cited in the metric sheet's own §3/§6), since
this is a strictly offline analysis over one existing data file. lab_env.isolate() is therefore not
applicable — nothing live-adjacent is touched (see metric sheet §6).

Usage: python j1471_i0082_exemplar_proxy_read.py
Reads (absolute, read-only): C:\\Nascence\\data\\geometry_tuples.jsonl, C:\\Nascence\\data\\sound_knowledge.json
Writes: a JSON results file next to this script's own docs/lab output, in THIS worktree only.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stamp_row_filter import drop_stamp_rows  # noqa: E402

# ---- verbatim-copied constants (see metric sheet §2/§3 for exact source citations) ----
_TARGET_KEYS = ("morepork_call", "tui_song", "gull_cries", "cat_purr")

_SOUNDS_COORDS = {   # core/soundscape.py _SOUNDS, reference only -- NOT used in the distance calc
    "morepork_call": {"brightness": .45, "energy": .35, "onset": .30, "periodicity": .65, "roughness": .10, "continuity": .15},
    "tui_song":      {"brightness": .75, "energy": .50, "onset": .60, "periodicity": .35, "roughness": .45, "continuity": .30},
    "gull_cries":    {"brightness": .70, "energy": .65, "onset": .70, "periodicity": .25, "roughness": .85, "continuity": .15},
    "cat_purr":      {"brightness": .08, "energy": .20, "onset": .05, "periodicity": .95, "roughness": .30, "continuity": .90},
}

_WEATHERS = ["clear", "high cloud", "overcast", "drizzle", "steady rain", "wind and rain", "thunderstorm"]  # core/sensorium.py:40


def _weather_severity(weather: str | None) -> int:
    """Verbatim reimplementation of core/soundscape.py:_weather_severity() -- fail-open to 0 for
    any weather string not on the real ladder (confirmed live case: "snow")."""
    try:
        return _WEATHERS.index(weather)
    except Exception:
        return 0


_LIVE_DATA = Path(r"C:\Nascence\data")
_GEOM_LOG = _LIVE_DATA / "geometry_tuples.jsonl"
_SOUND_KNOWLEDGE = _LIVE_DATA / "sound_knowledge.json"

_OUT_DIR = Path(__file__).parent.parent / "docs" / "lab"
_OUT_JSON = _OUT_DIR / "i0082_exemplar_proxy_results_2026-09-28.json"

_K = 4
_THRESHOLDS = (0.1, 0.2, 0.3)
_BUCKETS = (("dawn", 5, 8), ("day", 8, 17), ("dusk", 17, 20))   # else -> night


def _bucket(hour: float) -> str:
    for name, lo, hi in _BUCKETS:
        if lo <= hour < hi:
            return name
    return "night"


def _phase(ts: float) -> float:
    lt = time.localtime(ts)
    return (lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec) / 86400.0


def _hour(ts: float) -> int:
    return time.localtime(ts).tm_hour


def load_hearings() -> dict[str, list[dict]]:
    """One full, in-order pass over the live census log. Returns {key: [hearing, ...]} in ts order
    (the file is already append-order == ts order; no re-sort needed, but we sort defensively in
    case of any out-of-order write)."""
    out: dict[str, list[dict]] = {k: [] for k in _TARGET_KEYS}
    n_rows = 0
    n_bad = 0
    parsed: list[dict] = []
    with open(_GEOM_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n_rows += 1
            try:
                parsed.append(json.loads(line))
            except Exception:
                n_bad += 1
                continue
    # J-3944/F-4595: drop census-cycle stamp rows (each doubles its idle cycle's hearing); file order, so before any sort
    for row in drop_stamp_rows(parsed):
        if True:
            sounds = row.get("sounds") or []
            if not sounds:
                continue
            ts = row.get("ts")
            if ts is None:
                continue
            for k in _TARGET_KEYS:
                if k in sounds:
                    out[k].append({
                        "ts": float(ts),
                        "weather": row.get("weather"),
                        "place": row.get("place"),
                        "weather_dir": row.get("weather_dir"),
                    })
    for k in _TARGET_KEYS:
        out[k].sort(key=lambda h: h["ts"])
    return out, n_rows, n_bad


def decide_direction_usable(hearings: dict[str, list[dict]]) -> bool:
    total = sum(len(v) for v in hearings.values())
    present = sum(1 for v in hearings.values() for h in v if h["weather_dir"] is not None)
    frac = (present / total) if total else 0.0
    print(f"[direction usability] {present}/{total} = {frac:.3f} non-null across all 4 keys combined")
    return frac >= 0.90


def _circ01(a: float, b: float, period: float = 1.0) -> float:
    d = abs(a - b)
    return min(d, period - d) / (period / 2.0)


def make_point(h: dict) -> dict:
    return {"phase": _phase(h["ts"]), "sev": _weather_severity(h["weather"]), "place": h["place"],
            "dir": h["weather_dir"]}


def distance(a: dict, b: dict, use_dir: bool) -> float:
    d_tod = _circ01(a["phase"], b["phase"], 1.0)             # already in [0,1]
    d_sev = abs(a["sev"] - b["sev"]) / 6.0
    d_place = 0.0 if a["place"] == b["place"] else 1.0
    terms = [d_tod, d_sev, d_place]
    if use_dir:
        if a["dir"] is None or b["dir"] is None:
            d_dir = 1.0   # unknown direction treated as maximally different -- conservative, documented here
        else:
            d_dir = _circ01(float(a["dir"]), float(b["dir"]), 360.0)
        terms.append(d_dir)
    return (sum(t * t for t in terms) / len(terms)) ** 0.5


def main() -> None:
    t0 = time.time()
    hearings, n_rows, n_bad = load_hearings()
    print(f"[load] {n_rows} census rows scanned ({n_bad} unparseable), "
          f"in {time.time() - t0:.1f}s from {_GEOM_LOG}")
    for k in _TARGET_KEYS:
        print(f"  {k}: {len(hearings[k])} hearings "
              f"(ts span {hearings[k][0]['ts']:.0f}..{hearings[k][-1]['ts']:.0f})" if hearings[k] else f"  {k}: 0 hearings")

    use_dir = decide_direction_usable(hearings)

    # structural place-set check (pre-registered prediction from the source read)
    place_sets = {k: sorted({h["place"] for h in hearings[k]}) for k in _TARGET_KEYS}
    print(f"[place sets observed] {place_sets}")

    results: dict = {
        "generated_ts": time.time(),
        "n_rows_scanned": n_rows,
        "n_rows_unparseable": n_bad,
        "geometry_tuples_path": str(_GEOM_LOG),
        "direction_usable": use_dir,
        "place_sets_observed": place_sets,
        "per_key": {},
    }

    for key in _TARGET_KEYS:
        hs = hearings[key]
        n = len(hs)
        pts = [make_point(h) for h in hs]
        key_result: dict = {"n_hearings": n, "reliable": n >= 50, "by_threshold": {}}

        # base rates for the secondary reads (independent of T)
        base_bucket_counts = {"dawn": 0, "day": 0, "dusk": 0, "night": 0}
        for h in hs:
            base_bucket_counts[_bucket(_hour(h["ts"]))] += 1
        base_bucket_frac = {b: (c / n if n else 0.0) for b, c in base_bucket_counts.items()}

        weather_change_pairs = 0
        for i in range(1, n):
            if hs[i]["weather"] != hs[i - 1]["weather"]:
                weather_change_pairs += 1
        base_weather_change_frac = (weather_change_pairs / (n - 1)) if n > 1 else 0.0

        for T in _THRESHOLDS:
            exemplars: list[dict] = []
            admissions = 0
            admission_considered = 0
            admission_bucket_counts = {"dawn": 0, "day": 0, "dusk": 0, "night": 0}
            admission_weather_change = 0
            for i, p in enumerate(pts):
                if not exemplars:
                    exemplars.append({"point": p, "order": i})
                    admissions += 1
                    continue
                dstar = min(distance(p, e["point"], use_dir) for e in exemplars)
                if dstar > T:
                    admissions += 1
                    admission_considered += 1
                    b = _bucket(_hour(hs[i]["ts"]))
                    admission_bucket_counts[b] += 1
                    if i > 0 and hs[i]["weather"] != hs[i - 1]["weather"]:
                        admission_weather_change += 1
                    if len(exemplars) < _K:
                        exemplars.append({"point": p, "order": i})
                    else:
                        best_j, best_val = None, None
                        for j, e in enumerate(exemplars):
                            nn = min(distance(e["point"], other["point"], use_dir)
                                     for j2, other in enumerate(exemplars) if j2 != j)
                            if best_val is None or nn < best_val:
                                best_val, best_j = nn, j
                            elif nn == best_val and exemplars[j]["order"] < exemplars[best_j]["order"]:
                                best_j = j
                        exemplars[best_j] = {"point": p, "order": i}
            admission_bucket_frac = {b: (c / admission_considered if admission_considered else 0.0)
                                      for b, c in admission_bucket_counts.items()}
            admission_weather_change_frac = (admission_weather_change / admission_considered
                                              if admission_considered else 0.0)
            key_result["by_threshold"][str(T)] = {
                "admissions_total": admissions,
                "admissions_excl_seed": admission_considered,
                "admissions_per_1000_hearings": round(admissions / n * 1000, 2) if n else None,
                "final_exemplar_count": len(exemplars),
                "bucket_base_rate": base_bucket_frac,
                "bucket_admission_rate": admission_bucket_frac,
                "bucket_lift": {b: (round(admission_bucket_frac[b] / base_bucket_frac[b], 2)
                                     if base_bucket_frac[b] > 0 else None)
                                for b in base_bucket_frac},
                "weather_change_base_rate": round(base_weather_change_frac, 4),
                "weather_change_admission_rate": round(admission_weather_change_frac, 4),
                "weather_change_lift": (round(admission_weather_change_frac / base_weather_change_frac, 2)
                                        if base_weather_change_frac > 0 else None),
            }
        results["per_key"][key] = key_result

    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(_OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[written] {_OUT_JSON}")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
