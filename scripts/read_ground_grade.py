"""
Reader for the P-0088 grounder's two J-2890 ledgers (F-3558). Read-only; writes nothing.

  data/ground_outcome.jsonl      one row per ground_thought call (core/left_lane.py)
  data/ground_grade_shadow.jsonl the sampled, different-family quality grade (core/ground_grade.py)

Reports:
  * OUTCOMES: counts and shares of ok / leak_retry / leak_dropped / empty / null_grounding / bad_json / transport, and the
    latency median / p90 of the calls that produced a grounding;
  * RECONCILE against data/deliberation_log.jsonl over the same window: successful groundings (ok + leak_retry) should equal
    the emissary rows plus the groundings whose pass 3 failed, echoed, or came back under 20 characters (those write no
    deliberation_log row). `unlogged_after_grounding` = successful - emissary_rows must be >= 0; a negative number means
    outcome rows are missing. Rows near the window edges can differ by a call in flight, so read it over >= 24 h;
  * SHADOW GRADE, base rate FIRST: the share of true answers to each question and to Q1 after the deterministic quote check;
    a judge that gives the same answer nine times in ten measures nothing (docs/guidelines/prompt_registry.md section 5);
    the positive-control hit rate (a real grounding with an invented concrete sentence appended must give Q1 true with a quote
    from that sentence; a judge that misses its control carries no information); failed and busy-skipped counts; and
    --sample N real rows (newest first) for the founder to read.

  python scripts/read_ground_grade.py [--hours 24] [--sample 10] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import shadow_log  # noqa: E402

OUTCOME_LOG = ROOT / "data" / "ground_outcome.jsonl"
SHADOW_LOG = ROOT / "data" / "ground_grade_shadow.jsonl"
DELIB_LOG = ROOT / "data" / "deliberation_log.jsonl"
OUTCOMES = ("ok", "leak_retry", "leak_dropped", "empty", "null_grounding", "bad_json", "transport")
MIN_BASE_RATE_N = 40          # the J-2890 acceptance count of graded rows
DEGENERATE = 0.90             # a question answered the same way this often measures nothing


def _pct(xs, q):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(q * len(xs)))], 2) if xs else None


def _share(k, n):
    return round(k / n, 3) if n else None


def summarize_outcomes(rows: list[dict], emissary_rows: int | None = None) -> dict:
    n = len(rows)
    counts = {o: sum(1 for r in rows if r.get("outcome") == o) for o in OUTCOMES}
    other = n - sum(counts.values())
    good = counts["ok"] + counts["leak_retry"]
    lat = [r["latency_s"] for r in rows if r.get("outcome") in ("ok", "leak_retry") and isinstance(r.get("latency_s"), (int, float))]
    out = {"calls": n, "counts": counts, "other": other, "shares": {o: _share(c, n) for o, c in counts.items()},
           "successful_groundings": good, "latency_p50_s": _pct(lat, 0.5), "latency_p90_s": _pct(lat, 0.9),
           "with_code_hint": sum(1 for r in rows if r.get("had_code_hint"))}
    if emissary_rows is not None:
        out["deliberation_log_emissary_rows"] = emissary_rows
        out["unlogged_after_grounding"] = good - emissary_rows
        out["reconciles"] = (good - emissary_rows) >= 0
    return out


def summarize_shadow(rows: list[dict]) -> dict:
    real = [r for r in rows if not r.get("control") and "q1_detail" in r and not r.get("failed")]
    ctl = [r for r in rows if r.get("control") and "control_hit" in r]
    failed = [r for r in rows if r.get("failed")]
    skipped = [r for r in rows if r.get("skipped")]
    n = len(real)
    q1 = sum(1 for r in real if r.get("q1_detail") is True)
    q1v = sum(1 for r in real if r.get("q1_verified"))
    q2 = [r for r in real if isinstance(r.get("q2_mechanism"), bool)]
    q2t = sum(1 for r in q2 if r["q2_mechanism"])
    out = {"graded": n, "failed": len(failed), "skipped_busy": len(skipped),
           "q1_detail_true": q1, "q1_detail_share": _share(q1, n),
           "q1_verified": q1v, "q1_verified_share": _share(q1v, n),
           "q2_answered": len(q2), "q2_mechanism_true": q2t, "q2_mechanism_share": _share(q2t, len(q2)),
           "controls": len(ctl), "control_hits": sum(1 for r in ctl if r.get("control_hit")),
           "control_hit_rate": _share(sum(1 for r in ctl if r.get("control_hit")), len(ctl)),
           "judge_models": sorted({str(r.get("judge_model")) for r in rows if r.get("judge_model")}),
           "grounder_models": sorted({str(r.get("grounder_model")) for r in rows if r.get("grounder_model")})}
    flags = []
    if n < MIN_BASE_RATE_N:
        flags.append(f"only {n} graded rows; the acceptance bar is {MIN_BASE_RATE_N}, do not read the rates yet")
    for name, share in (("Q1 detail (verified)", out["q1_verified_share"]), ("Q2 mechanism", out["q2_mechanism_share"])):
        if share is not None and n >= MIN_BASE_RATE_N and (share >= DEGENERATE or share <= 1 - DEGENERATE):
            flags.append(f"{name} base rate {share} is degenerate (same answer >= {int(DEGENERATE * 100)} percent): this question measures nothing")
    if out["controls"] and out["control_hit_rate"] is not None and out["control_hit_rate"] < 0.6:
        flags.append(f"control hit rate {out['control_hit_rate']} < 0.6: the judge misses an inserted detail, Q1 carries no information")
    out["flags"] = flags
    return out


def _window(rows: list[dict], since_ts: float) -> list[dict]:
    return [r for r in rows if isinstance(r.get("ts"), (int, float)) and r["ts"] >= since_ts]


def _emissary_rows(since_ts: float) -> int | None:
    try:
        n = 0
        with open(DELIB_LOG, encoding="utf-8") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                if r.get("source") == "emissary" and r.get("ts", 0) >= since_ts:
                    n += 1
        return n
    except FileNotFoundError:
        return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    since = time.time() - a.hours * 3600
    orows = _window(shadow_log.read_rows(OUTCOME_LOG), since)
    srows = _window(shadow_log.read_rows(SHADOW_LOG), since)
    res = {"window_hours": a.hours, "outcomes": summarize_outcomes(orows, _emissary_rows(since)),
           "shadow": summarize_shadow(srows)}
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    o, s = res["outcomes"], res["shadow"]
    print(f"== P-0088 grounder, last {a.hours:g} h ==")
    print(f"outcomes: {o['calls']} calls  " + "  ".join(f"{k}={v}" for k, v in o["counts"].items()))
    print(f"  successful groundings {o['successful_groundings']}  p50 {o['latency_p50_s']} s  p90 {o['latency_p90_s']} s  "
          f"with code hint {o['with_code_hint']}")
    if "unlogged_after_grounding" in o:
        print(f"  reconcile: deliberation_log emissary rows {o['deliberation_log_emissary_rows']}; "
              f"unlogged after grounding {o['unlogged_after_grounding']} ({'ok' if o['reconciles'] else 'NEGATIVE: outcome rows missing'})")
    print(f"shadow grade (judge {', '.join(s['judge_models']) or '-'} vs grounder {', '.join(s['grounder_models']) or '-'}):")
    print(f"  BASE RATE first: Q1 detail true {s['q1_detail_share']} (verified {s['q1_verified_share']}), "
          f"Q2 mechanism true {s['q2_mechanism_share']}, over {s['graded']} graded rows "
          f"({s['failed']} failed, {s['skipped_busy']} skipped busy)")
    print(f"  control: {s['control_hits']}/{s['controls']} inserted details caught (rate {s['control_hit_rate']})")
    for fl in s["flags"]:
        print("  FLAG: " + fl)
    if a.sample:
        real = [r for r in srows if not r.get("control") and "q1_detail" in r and not r.get("failed")]
        for r in sorted(real, key=lambda r: r["ts"], reverse=True)[: a.sample]:
            print("-" * 70)
            print("THOUGHT:  " + str(r.get("thought", ""))[:300])
            print("GROUNDING: " + str(r.get("grounding", ""))[:500])
            print(f"Q1 {r.get('q1_detail')} verified={r.get('q1_verified')} quote={r.get('q1_quote')!r}")
            print(f"Q2 {r.get('q2_mechanism')} why={r.get('q2_why')!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
