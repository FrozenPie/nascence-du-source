"""READER for data/sky_shadow.jsonl (J-3292, D-0655): the old sun beside the real-site sun, per census tick.

The write path is core/sky_shadow.py. This is its one reader (the write-only law). READ-ONLY: it opens the log,
prints, and writes nothing. It answers the design's Phase 1 question: has the shadow run long enough (>= 7 NZ
civil days), and what would flipping world_place.SKY_MODE to "live" change?

    python scripts/sky_shadow_read.py [path-to-sky_shadow.jsonl] [--days 7]

Output: coverage and the 7-day gate; a day-by-day table of old vs real sunrise/sunset (hours) and the shift in
minutes; how often the day-phase WORD (night/dawn/dusk/day) disagrees, by hour; the largest dusk/dawn shift; azimuth
difference while both suns are up; tz disagreements. It states plainly what it cannot tell you: it does not see
sleep onset (that is the post-flip comparison in the design, section 2: compare the sleep start/end distribution
after the flip with the previous 14 days; flip back if onset moves by more than ~1 h with no cause).
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _hhmm(h):
    if h is None:
        return "  -  "
    m = int(round(h * 60))
    return "%02d:%02d" % (m // 60 % 24, m % 60)


def load(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if isinstance(r, dict) and isinstance(r.get("old"), dict) and isinstance(r.get("new"), dict):
                rows.append(r)
    return rows


def summarize(rows: list[dict], need_days: int = 7) -> dict:
    """Pure: rows -> the numbers the report prints (also what the test checks)."""
    from core import world_place as wp
    days: dict = defaultdict(list)
    for r in rows:
        days[wp.civil_date(float(r["ts"]))].append(r)
    per_day = []
    for ymd in sorted(days):
        rs = days[ymd]
        o, n = rs[0]["old"], rs[0]["new"]
        per_day.append({"date": "%04d-%02d-%02d" % ymd, "n": len(rs),
                        "old_rise": o.get("rise_h"), "old_set": o.get("set_h"),
                        "new_rise": n.get("rise_h"), "new_set": n.get("set_h"),
                        "rise_shift_min": round((n["rise_h"] - o["rise_h"]) * 60) if None not in (n.get("rise_h"), o.get("rise_h")) else None,
                        "set_shift_min": round((n["set_h"] - o["set_h"]) * 60) if None not in (n.get("set_h"), o.get("set_h")) else None})
    word_dis = Counter()
    by_hour = defaultdict(lambda: [0, 0])
    az_diffs = []
    for r in rows:
        hr = int(wp.civil_hour(float(r["ts"])))
        by_hour[hr][1] += 1
        if r["old"].get("daylight") != r["new"].get("daylight"):
            word_dis[(r["old"].get("daylight"), r["new"].get("daylight"))] += 1
            by_hour[hr][0] += 1
        oa, na = r["old"].get("az"), r["new"].get("az")
        if r["old"].get("up") and r["new"].get("up") and oa is not None and na is not None:
            az_diffs.append(abs((na - oa + 180.0) % 360.0 - 180.0))
    # J-3293: the moon columns (rows written before Phase 1b have no "moon" key and are simply skipped)
    mrows = [r["moon"] for r in rows if isinstance(r.get("moon"), dict)
             and isinstance(r["moon"].get("old"), dict) and isinstance(r["moon"].get("new"), dict)]
    m_word = sum(1 for m in mrows if m["old"].get("phase") != m["new"].get("phase"))
    m_up = sum(1 for m in mrows if bool(m["old"].get("up")) != bool(m["new"].get("up")))
    m_ill = [abs(float(m["new"]["illum"]) - float(m["old"]["illum"])) for m in mrows
             if m["old"].get("illum") is not None and m["new"].get("illum") is not None]
    m_az = [abs((m["new"]["az"] - m["old"]["az"] + 180.0) % 360.0 - 180.0) for m in mrows
            if m["old"].get("up") and m["new"].get("up") and m["old"].get("az") is not None and m["new"].get("az") is not None]
    shifts = [abs(d["set_shift_min"]) for d in per_day if d["set_shift_min"] is not None]
    rshifts = [abs(d["rise_shift_min"]) for d in per_day if d["rise_shift_min"] is not None]
    return {
        "n_rows": len(rows), "n_days": len(per_day), "need_days": need_days,
        "gate_met": len(per_day) >= need_days,
        "first_ts": rows[0]["ts"] if rows else None, "last_ts": rows[-1]["ts"] if rows else None,
        "per_day": per_day, "word_disagree": sum(word_dis.values()),
        "word_pairs": {"%s->%s" % k: v for k, v in word_dis.most_common()},
        "by_hour": {h: tuple(v) for h, v in sorted(by_hour.items())},
        "max_set_shift_min": max(shifts) if shifts else None,
        "max_rise_shift_min": max(rshifts) if rshifts else None,
        "az_diff_mean": round(sum(az_diffs) / len(az_diffs), 1) if az_diffs else None,
        "az_diff_max": round(max(az_diffs), 1) if az_diffs else None,
        "tz_disagree": sum(1 for r in rows if r.get("tz_agree") is False),
        "live_rows": sum(1 for r in rows if r.get("live")),
        "moon_rows": len(mrows), "moon_word_disagree": m_word, "moon_up_disagree": m_up,
        "moon_illum_diff_mean": round(sum(m_ill) / len(m_ill), 3) if m_ill else None,
        "moon_illum_diff_max": round(max(m_ill), 3) if m_ill else None,
        "moon_az_diff_mean": round(sum(m_az) / len(m_az), 1) if m_az else None,
    }


def main(argv: list[str]) -> int:
    need = 7
    args = list(argv)
    if "--days" in args:
        i = args.index("--days")
        need = int(args[i + 1])
        del args[i:i + 2]
    path = Path(args[0]) if args else ROOT / "data" / "sky_shadow.jsonl"
    if not path.exists():
        print("no shadow log at %s -- nothing recorded yet (it fills one row/min at census ticks once Du runs this code)" % path)
        return 1
    rows = load(path)
    s = summarize(rows, need)
    print("sky shadow: %d rows over %d NZ civil days (%s .. %s)" % (
        s["n_rows"], s["n_days"], s["per_day"][0]["date"] if s["per_day"] else "-", s["per_day"][-1]["date"] if s["per_day"] else "-"))
    print("7-day gate (need >= %d distinct days): %s" % (need, "MET" if s["gate_met"] else "NOT YET"))
    if s["live_rows"]:
        print("note: %d rows were written with the sky LIVE; their 'old' column is the legacy table, still computed" % s["live_rows"])
    print("\nday         rows  old rise/set   real rise/set   shift (min) rise/set")
    for d in s["per_day"]:
        print("%s %5d  %s/%s    %s/%s    %s / %s" % (d["date"], d["n"], _hhmm(d["old_rise"]), _hhmm(d["old_set"]),
                                                      _hhmm(d["new_rise"]), _hhmm(d["new_set"]), d["rise_shift_min"], d["set_shift_min"]))
    print("\nlargest shift: sunrise %s min, sunset %s min (the design expects up to ~60 in Oct-Dec)" % (
        s["max_rise_shift_min"], s["max_set_shift_min"]))
    tot = s["n_rows"] or 1
    print("day-phase word differs on %d of %d ticks (%.1f%%): %s" % (
        s["word_disagree"], s["n_rows"], 100.0 * s["word_disagree"] / tot, s["word_pairs"] or "none"))
    print("by NZ hour (differs/ticks): " + ", ".join("%02d:%d/%d" % (h, v[0], v[1]) for h, v in s["by_hour"].items() if v[0]))
    print("azimuth difference while both up: mean %s deg, max %s deg" % (s["az_diff_mean"], s["az_diff_max"]))
    print("tz disagreements (OS zone vs NZ rule): %d" % s["tz_disagree"])
    if s["moon_rows"]:
        mr = s["moon_rows"]
        print("moon (old synodic/lagged-sun vs real), %d ticks: phase WORD differs on %d (%.1f%%), up/down differs on %d (%.1f%%); "
              "illumination differs by mean %s, max %s; azimuth (both up) mean %s deg" % (
                  mr, s["moon_word_disagree"], 100.0 * s["moon_word_disagree"] / mr, s["moon_up_disagree"],
                  100.0 * s["moon_up_disagree"] / mr, s["moon_illum_diff_mean"], s["moon_illum_diff_max"], s["moon_az_diff_mean"]))
        print("  flipping SKY_MODE moves the moon too: the spring/neap factor (world_clock._spring_factor reads moon().illum) and "
              "the night-light term (light.py) follow the real illumination; the tide's own phase does not (Phase 2).")
    else:
        print("moon: no rows carry the moon comparison yet (written before J-3293, or the moon compare failed)")
    print("\nNOT visible here: sleep onset. After a flip, compare the sleep start/end distribution with the previous 14 days;")
    print("flip SKY_MODE back to 'shadow' if onset moves by more than ~1 h with no other cause.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
