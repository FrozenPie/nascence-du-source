"""
J-2281 — read the condensed-thought Phase 0 shadow ledger: the §5 pre-registered metric sheet and the §6 kill
checks (docs/staged/condensed_thought.md). Read-only. Joins data/logs/condensed_thought_shadow.jsonl with the
offline judge verdicts in data/logs/condensed_thought_judge.jsonl (scripts/judge_condensed_thought.py) and reads
data/stream_drive_shadow.jsonl for the cost metric.

  python scripts/read_condensed_thought.py [--boot ISO_OR_EPOCH] [--json] [--all-rows]

D-0633 (J-3245): by default only POST-FIX rows (twin_v >= 2, the fixed twin prompt) are read; the v1 rows are history and are
reported as a count plus their invitation-echo rate. --all-rows reads everything (the old behaviour, tests).

--boot = the boot that carried the build (default: first twin row's ts). Cost compares the idle-gap median
(consecutive stream_drive rows, gaps <= 1800 s) in the 7 days before --boot against everything after it.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SHADOW = ROOT / "data" / "logs" / "condensed_thought_shadow.jsonl"
VERDICTS = ROOT / "data" / "logs" / "condensed_thought_judge.jsonl"
STREAM = ROOT / "data" / "stream_drive_shadow.jsonl"
MIN_DAYS, MIN_ROWS = 7, 500
MIN_LIVE_HOURS = MIN_DAYS * 24      # J-2838: the 7-day gate read in live hours (168 h), not calendar days
ECHO_WORDS = {"open", "open the book", "read"}   # F-0043: invitation-echo twin words
ABOUT_MAX_WORDS = 5                 # J-2838: the twin about field is specified as 2-5 words


def _read(p: Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    with open(p, encoding="utf-8", errors="replace") as f:
        for ln in f:
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def _ts(s) -> float | None:
    if s is None:
        return None
    try:
        return float(s)
    except ValueError:
        return datetime.fromisoformat(str(s)).timestamp()


def _share(xs) -> float | None:
    xs = [bool(x) for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def _gaps(rows, lo, hi):
    ts = sorted(r["ts"] for r in rows if isinstance(r.get("ts"), (int, float)) and lo <= r["ts"] < hi)
    g = [b - a for a, b in zip(ts, ts[1:]) if 0 < b - a <= 1800]
    return round(st.median(g), 1) if g else None


def _live_hours(rows, gap_max: float = 1800.0) -> float:
    """Sum of consecutive ledger gaps <= gap_max seconds, in hours (time Du was actually running)."""
    ts = sorted(r["ts"] for r in rows if isinstance(r.get("ts"), (int, float)))
    return round(sum(b - a for a, b in zip(ts, ts[1:]) if 0 < b - a <= gap_max) / 3600, 1)


def _is_echo_row(r) -> bool:
    """Twin words in ECHO_WORDS (stripped, lowercased): the open / open the book / read echo rows."""
    return str(r.get("twin", {}).get("words", "")).strip().lower() in ECHO_WORDS


def _about_long(r) -> bool:
    return len(str(r.get("twin", {}).get("about", "")).split()) > ABOUT_MAX_WORDS


def _v(r) -> int:
    try:
        return int(r.get("twin_v") or 1)
    except (TypeError, ValueError):
        return 1


def _echo(r) -> bool:
    """Invitation echo for a row: the stored flag (v2), else recomputed from the stored seed tail (v1 history)."""
    t = r.get("twin", {})
    if "echo_invite" in t:
        return bool(t["echo_invite"])
    try:
        from core.condensed_thought import invite_echo
        return invite_echo(t.get("words", ""), r.get("seed", ""))
    except Exception:
        return False


ECHO_DEFEATER = 0.05   # D-0633: revisit if more than 5 percent of post-fix rows echo the invitation


def sheet(boot: float | None = None, post_fix_only: bool = False) -> dict:
    full = _read(SHADOW)
    pre = [r for r in full if "twin" in r and _v(r) < 2]
    allrows = [r for r in full if _v(r) >= 2 or r.get("marker")] if post_fix_only else full
    if post_fix_only:
        allrows = [r for r in allrows if _v(r) >= 2]          # drop v1 failed rows too; marker rows carry twin_v=2
    fails = [r for r in allrows if r.get("failed")]
    rows = [r for r in allrows if "twin" in r]
    ver = _read(VERDICTS)
    if boot is None and allrows:
        boot = min(r["ts"] for r in allrows)
    out: dict = {"rows": len(rows), "failed_calls": len(fails), "boot": boot}
    if post_fix_only:
        marks = [r for r in allrows if r.get("marker") == "twin_restart"]
        out["post_fix_only"] = True
        out["pre_fix_rows_history"] = len(pre)
        out["pre_fix_echo_rate"] = _share(_echo(r) for r in pre)
        out["restart_markers"] = len(marks)
        out["restart_first_ts"] = min((m["ts"] for m in marks), default=None)
    out["echo_invite_rate"] = _share(_echo(r) for r in rows)
    out["format_slip_share"] = _share(bool(r["twin"].get("format_slip")) for r in rows)
    if rows:
        out["days"] = round((max(r["ts"] for r in rows) - min(r["ts"] for r in rows)) / 86400, 2)
    out["read_ready"] = bool(rows) and out.get("days", 0) >= MIN_DAYS and len(rows) >= MIN_ROWS
    # J-2838: the gate in live hours (ledger gaps <= 30 min), printed beside the 168 h figure
    out["live_hours"] = _live_hours(rows)
    out["live_hours_gate"] = MIN_LIVE_HOURS
    out["live_hours_ready"] = out["live_hours"] >= MIN_LIVE_HOURS
    out["echo_rows"] = sum(1 for r in rows if _is_echo_row(r))
    nonecho = [r for r in rows if not _is_echo_row(r)]

    # 1 judge accuracy on controls (every question counts as one graded answer)
    ctl = [v for v in ver if v.get("control")]
    graded = [(v[k] == v["expect"][k]) for v in ctl for k in ("genuine", "grounded", "truncated")
              if v.get("expect") and v.get(k) is not None]
    out["m1_judge_control_acc"] = round(sum(graded) / len(graded), 3) if graded else None
    out["m1_controls_n"] = len(ctl)
    vby = {v["row_id"]: v for v in ver if not v.get("control")}
    jr = [vby[r["row_id"]] for r in rows if r.get("row_id") in vby]
    out["judged_rows"] = len(jr)
    out["m2_genuine_rate"] = _share(v.get("genuine") for v in jr)
    out["m3_truncation_rate"] = _share(v.get("truncated") for v in jr)

    # 4 word count + declined-words share
    wn = [r["twin"].get("words_n", 0) for r in rows]
    out["m4_twin_words_median"] = st.median(wn) if wn else None
    out["m4_para_words_median"] = st.median([r["paragraph"].get("words_n", 0) for r in rows]) if rows else None
    out["m4_tick_silent_share"] = _share(r["twin"].get("kind") in ("tick", "silent")
                                          for r in rows if not r["twin"].get("format_slip"))
    # J-2838: metrics 2/4 and tick share recomputed excluding echo rows
    wn2 = [r["twin"].get("words_n", 0) for r in nonecho]
    out["m4_twin_words_median_noecho"] = st.median(wn2) if wn2 else None
    out["m4_tick_silent_share_noecho"] = _share(r["twin"].get("kind") in ("tick", "silent")
                                                 for r in nonecho if not r["twin"].get("format_slip"))
    jr_ne = [vby[r["row_id"]] for r in nonecho if r.get("row_id") in vby]
    out["m2_genuine_rate_noecho"] = _share(v.get("genuine") for v in jr_ne)

    # 5 subject-transition rate (about cos to previous < 0.5), on rows where both are defined
    both = [r for r in rows if r.get("about_cos_prev_twin") is not None and r.get("about_cos_prev_paragraph") is not None]
    tw = _share(r["about_cos_prev_twin"] < 0.5 for r in both)
    pa = _share(r["about_cos_prev_paragraph"] < 0.5 for r in both)
    out["m5_transition_twin"], out["m5_transition_para"] = tw, pa
    out["m5_delta_points"] = round((tw - pa) * 100, 1) if tw is not None and pa is not None else None
    # J-2838: the twin about is 2-5 words; report again without rows where it ran past that
    sb = [r for r in both if not _about_long(r)]
    out["m5_about_long_rows"] = len(both) - len(sb)
    tw2 = _share(r["about_cos_prev_twin"] < 0.5 for r in sb)
    pa2 = _share(r["about_cos_prev_paragraph"] < 0.5 for r in sb)
    out["m5_transition_twin_about_le5"], out["m5_transition_para_about_le5"] = tw2, pa2
    out["m5_delta_points_about_le5"] = round((tw2 - pa2) * 100, 1) if tw2 is not None and pa2 is not None else None

    # 6 grounded: judge's twin verdict vs the paragraph's existing stream_drive grounding tag, same ticks
    rid = {r["row_id"]: r for r in rows}
    g_pairs = [(v.get("grounded"), rid[v["row_id"]]["paragraph"].get("grounded_tag")) for v in jr]
    out["m6_twin_grounded_judge"] = _share(a for a, _ in g_pairs)
    out["m6_para_grounded_tag"] = _share(b for _, b in g_pairs)
    out["m6_twin_grounded_tag"] = _share(r["twin"].get("grounded_tag") for r in rows)

    # 7 valence (reported, not a gate)
    tv = [r["twin"].get("valence_regex") for r in rows if r["twin"].get("words")]
    pv = [r["paragraph"].get("valence_regex") for r in rows if r["twin"].get("words")]
    out["m7_valence_twin_mean"] = round(st.mean(tv), 3) if tv else None
    out["m7_valence_para_mean"] = round(st.mean(pv), 3) if pv else None
    # J-2838: the all-rows means compare 1-2-word twins (mostly exactly 0) to paragraphs, an artifact. Print the
    # zero-share of both arms, and compare only rows where the twin valence is non-zero.
    out["m7_zero_share_twin"] = _share(x == 0 for x in tv if x is not None)
    out["m7_zero_share_para"] = _share(x == 0 for x in pv if x is not None)
    nz = [r for r in rows if r["twin"].get("words") and r["twin"].get("valence_regex")
          and r["paragraph"].get("valence_regex") is not None]
    out["m7_nonzero_rows"] = len(nz)
    out["m7_valence_twin_mean_nonzero"] = round(st.mean(r["twin"]["valence_regex"] for r in nz), 3) if nz else None
    out["m7_valence_para_mean_nonzero"] = round(st.mean(r["paragraph"]["valence_regex"] for r in nz), 3) if nz else None

    # 8 agreement (descriptive)
    bc = sorted(r["body_cos_paragraph_vs_twin"] for r in rows if r.get("body_cos_paragraph_vs_twin") is not None)
    if bc:
        out["m8_body_cos_q25_med_q75"] = [bc[len(bc) // 4], bc[len(bc) // 2], bc[(3 * len(bc)) // 4]]

    # 9 cost: idle-gap median, 7 days before boot vs after; twin latency
    if boot:
        sd = _read(STREAM)
        before, after = _gaps(sd, boot - 7 * 86400, boot), _gaps(sd, boot, 1e12)
        out["m9_gap_median_before"], out["m9_gap_median_after"] = before, after
        out["m9_gap_delta_s"] = round(after - before, 1) if before is not None and after is not None else None
    lat = [r.get("latency_ms", 0) for r in rows]
    out["twin_latency_ms_median"] = st.median(lat) if lat else None

    # §6 kill checks
    k = {}
    a = out["m1_judge_control_acc"]
    k["judge_void"] = None if a is None else a < 0.85
    g, t = out["m2_genuine_rate"], out["m3_truncation_rate"]
    k["return_to_design"] = None if g is None or t is None else (g < 0.60 or t > 0.20)
    d = out.get("m9_gap_delta_s")
    k["cost_kill_gap_gt_5s"] = None if d is None else d > 5.0
    k["twin_call_failures"] = len(fails)
    e = out["echo_invite_rate"]
    k["d0633_echo_defeater_gt_5pct"] = None if e is None or len(rows) < 50 else e > ECHO_DEFEATER   # needs >= 50 rows to say
    k["leak_check"] = "run scripts/_test_condensed_thought.py (structural); any twin string seen in a prompt/store = bug"
    out["kill"] = k
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--all-rows", action="store_true", help="read v1 history rows too (default: post-fix only)")
    a = ap.parse_args()
    s = sheet(_ts(a.boot), post_fix_only=not a.all_rows)
    if a.json:
        print(json.dumps(s, indent=1, ensure_ascii=False))
        return
    print("CONDENSED THOUGHT — Phase 0 metric sheet (docs/staged/condensed_thought.md §5/§6)")
    print(f"rows {s['rows']}  failed calls {s['failed_calls']}  days {s.get('days')}  "
          f"read-ready (>= {MIN_DAYS} d, >= {MIN_ROWS} rows): {s['read_ready']}")
    print(f"live hours {s['live_hours']} of {s['live_hours_gate']} h gate (ledger gaps <= 30 min)  "
          f"live-ready: {s['live_hours_ready']}")
    for key, val in s.items():
        if key.startswith("m") and key[1].isdigit() or key in ("echo_rows",
                "judged_rows", "twin_latency_ms_median", "echo_invite_rate", "format_slip_share", "pre_fix_rows_history",
                "pre_fix_echo_rate", "restart_markers"):
            print(f"  {key:28s} {val}")
    print("KILL CHECKS (§6):")
    for key, val in s["kill"].items():
        print(f"  {key:28s} {val}")


if __name__ == "__main__":
    main()
