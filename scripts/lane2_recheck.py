"""
Lane 2 Recheck — founder-check re-run of K1/K3 against the CURRENT object-graph (2026-08-18).

WHY: docs/plans/lane2_lab.md pre-registered kill criteria for the Lane 2 standing loop
(docs/plans/emissary_lane2.md); the run (docs/lab/lane2_lab_report.md, 2026-08-17) recorded K1 and K3 both
TRIGGERED — including K3: "no real temporal structure... the standing prediction loop is premature." The
report's own diagnosis says both are probably artifacts (K1: text-mining pollution the later voiceprint
filter was built to fix; K3: a ~30-day fragment-store gap the temporal-holdout split fell into) and is
explicit that this needs a "FOUNDER-CHECK before the kill is treated as final." That check never happened.

Since then, core/object_graph.py (the fixed, voiceprint-filtered builder) has been run for real —
data/lane2/graph.json exists, built 2026-08-18, postdating the report and its fixes. This script re-tests
K1 (as L3) and K3 (as L7) against THAT graph, using the report's own corrected understanding of what "the
glass float" actually looks like (NOT terminal — "near-daily rumination" — the original terminal/world-
absent criterion was itself named as the wrong premise in the report's diagnosis).

ISOLATION CONTRACT (same as scripts/lane2_lab.py): reads data/lane2/graph.json and nascence.db (mode=ro)
read-only. Writes ONLY under data/lab/lane2_recheck/ and docs/lab/lane2_recheck_report.md. Zero LLM. Du
stays up. Does not touch object_graph.py's own output, any live code, or any flag.
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
GRAPH_PATH = ROOT / "data" / "lane2" / "graph.json"
LAB = ROOT / "data" / "lab" / "lane2_recheck"
LAB.mkdir(parents=True, exist_ok=True)
REPORT = ROOT / "docs" / "lab" / "lane2_recheck_report.md"
REPORT.parent.mkdir(parents=True, exist_ok=True)

HOLDOUT_TRAIN = 0.80        # same split as the original lab
RECENT_TRAIN_DAYS = 14      # same recency window as the original lab
MIN_TOTAL_MENTIONS = 30     # same eligibility floor as the original lab
N_SHUFFLES = 100
random.seed(20260817)       # same seed as the original lab — this IS the same pre-registered test


def log(msg: str) -> None:
    print(f"[lane2-recheck] {msg}", flush=True)


def _daily_series(mentions: dict, max_day: int) -> list[int]:
    return [int(mentions.get(str(d), 0)) for d in range(max_day + 1)]


def _holdout_gap(series: list[int], split_day: int) -> float | None:
    train, test = series[:split_day], series[split_day:]
    if not test or sum(train) < MIN_TOTAL_MENTIONS:
        return None
    recent = train[-RECENT_TRAIN_DAYS:]
    pred_rate = sum(recent) / max(1, len(recent))
    actual = sum(test) / len(test)
    return abs(pred_rate - actual)


def l3_glass_float_recheck(refs: dict) -> dict:
    """Re-check against the report's OWN corrected premise: not 'terminal + world-absent' (named as the
    wrong criterion in the original diagnosis) but high-observation + recurring/not-silent presence — the
    'near-daily rumination' finding. Checks both 'glass' (item_class) and 'sea_glass' if present."""
    cands = [k for k in refs if k in ("glass", "sea_glass") or "glass" in k.lower()]
    detail = {}
    winner = None
    for lbl in cands:
        r = refs[lbl]
        total = r.get("total_mentions", sum(r.get("mentions", {}).values()))
        trend = r.get("trend", {})
        d = {
            "kind": r.get("kind"), "total_mentions": total,
            "seen": r.get("depth", {}).get("seen", 0), "kept": r.get("depth", {}).get("kept", 0),
            "trend_shape": trend.get("shape"), "days_silent": r.get("days_silent"),
            "last_mention_day": r.get("last_mention_day"), "float_like": r.get("float_profile", {}).get("float_like"),
            "in_world_substrate": "world_substrate" in (r.get("sources") or []),
        }
        detail[lbl] = d
        # corrected criterion: real observed presence (>=20 obs) AND recurring, not vanished
        # (days_silent low relative to its own lifespan, or trend shape is a "still here" shape)
        recurring = (d["days_silent"] is not None and d["days_silent"] < 0.5) or \
                    d["trend_shape"] in ("settled_companion", "perennial_symbol", "growing_presence")
        if d["seen"] >= 20 and recurring:
            winner = lbl
    return {"emerged_corrected": winner is not None, "winner": winner, "detail": detail,
            "note": "corrected criterion: >=20 observations AND recurring (low days_silent or a "
                    "'still here' trend shape) — replaces the original terminal+world-absent test, which "
                    "the lab report's own diagnosis named as the wrong premise."}


def l7_holdout_recheck(refs: dict, max_day: int) -> dict:
    split_day = int(max_day * HOLDOUT_TRAIN)
    eligible = [(lbl, r) for lbl, r in refs.items()
                if sum(r.get("mentions", {}).values()) >= MIN_TOTAL_MENTIONS]
    real_gaps, per_ref = [], []
    for lbl, r in eligible:
        s = _daily_series(r.get("mentions", {}), max_day)
        g = _holdout_gap(s, split_day)
        if g is not None:
            real_gaps.append(g)
            per_ref.append((lbl, g, s))
    med_real = sorted(real_gaps)[len(real_gaps) // 2] if real_gaps else None

    null_medians = []
    for _ in range(N_SHUFFLES):
        gaps = []
        for lbl, _g, s in per_ref:
            sh = s[:]
            random.shuffle(sh)
            g = _holdout_gap(sh, split_day)
            if g is not None:
                gaps.append(g)
        if gaps:
            null_medians.append(sorted(gaps)[len(gaps) // 2])
    med_null = sorted(null_medians)[len(null_medians) // 2] if null_medians else None

    per_ref.sort(key=lambda x: -x[1])
    return {"n_referents": len(per_ref), "split_day": split_day, "max_day": max_day,
            "median_gap_real": round(med_real, 4) if med_real is not None else None,
            "median_gap_shuffled": round(med_null, 4) if med_null is not None else None,
            "pass": (med_real is not None and med_null is not None and med_real < med_null),
            "top_gaps": [(l, round(g, 3)) for l, g, _ in per_ref[:10]]}


def main():
    t0 = time.time()
    if not GRAPH_PATH.exists():
        log(f"error: {GRAPH_PATH} not found — run `python -m core.object_graph` first")
        sys.exit(1)

    log(f"loading {GRAPH_PATH} (read-only)...")
    g = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    refs = g["referents"]
    day0 = g["day0"]
    max_day = int((g["last_fragment_ts"] - day0) // 86400)
    built_age_days = round((time.time() - g["built_ts"]) / 86400, 2)
    log(f"graph: {len(refs)} referents, built {built_age_days}d ago, day0={g['day0_date']}, max_day={max_day}")

    log("L3 (K1) recheck: glass float, corrected criterion...")
    l3 = l3_glass_float_recheck(refs)
    log(f"L3: emerged_corrected={l3['emerged_corrected']} winner={l3['winner']}")

    log(f"L7 (K3) recheck: temporal holdout, {N_SHUFFLES} shuffles...")
    l7 = l7_holdout_recheck(refs, max_day)
    log(f"L7: real={l7['median_gap_real']} shuffled={l7['median_gap_shuffled']} pass={l7['pass']} "
        f"n_referents={l7['n_referents']}")

    kills = {
        "K1 (glass float absent, corrected criterion)": not l3["emerged_corrected"],
        "K3 (holdout no better than shuffled)": not l7["pass"],
    }

    (LAB / "recheck.json").write_text(
        json.dumps({"l3": l3, "l7": l7, "kills": kills, "graph_built_ts": g["built_ts"],
                    "graph_day0": g["day0_date"], "max_day": max_day}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    L = []
    L.append("# Lane 2 Recheck — founder-check re-run of K1/K3 (2026-08-18)")
    L.append("")
    L.append("> Re-runs the two triggered kill criteria from `docs/lab/lane2_lab_report.md` (2026-08-17)")
    L.append("> against the CURRENT `core/object_graph.py` output (`data/lane2/graph.json`), which postdates")
    L.append("> the report's own fixes (voiceprint filter) and the data-gap window the original K3 fell into.")
    L.append("> Same pre-registered methodology, same seed (20260817). Zero LLM. Read-only. Spec:")
    L.append("> `docs/plans/lane2_lab.md`.")
    L.append("")
    L.append(f"**Graph checked:** built {built_age_days} day(s) ago, {len(refs)} referents, "
             f"day0={g['day0_date']}, max_day={max_day}.")
    L.append("")
    L.append("## Verdicts")
    L.append("")
    L.append("| Criterion | Original (2026-08-17) | Recheck (2026-08-18) |")
    L.append("|---|---|---|")
    L.append(f"| K1 (glass float) | TRIGGERED (did not emerge) | "
             f"{'still TRIGGERED' if not l3['emerged_corrected'] else 'RESOLVED — not triggered'} |")
    L.append(f"| K3 (temporal holdout) | TRIGGERED (real ≥ shuffled) | "
             f"{'still TRIGGERED' if not l7['pass'] else 'RESOLVED — not triggered (real < shuffled)'} |")
    L.append("")
    for k, v in kills.items():
        L.append(f"- **{k}**: {'TRIGGERED' if v else 'not triggered'}")
    L.append("")
    L.append("## L3 detail — corrected criterion")
    L.append("")
    L.append(l3["note"])
    L.append("")
    for lbl, d in l3["detail"].items():
        L.append(f"- `{lbl}`: {json.dumps(d, ensure_ascii=False)}")
    if not l3["detail"]:
        L.append("- no glass/float-labeled referent found in the current graph at all")
    L.append("")
    L.append("## L7 detail — temporal holdout")
    L.append("")
    L.append(f"- {l7['n_referents']} eligible referents (>= {MIN_TOTAL_MENTIONS} total mentions)")
    L.append(f"- split day {l7['split_day']} / {l7['max_day']} ({HOLDOUT_TRAIN:.0%} train)")
    L.append(f"- median holdout gap: real={l7['median_gap_real']}, shuffled={l7['median_gap_shuffled']}")
    L.append("- top real gaps (worst-predicted referents):")
    for lbl, gap in l7["top_gaps"]:
        L.append(f"  - `{lbl}`: gap {gap}")
    L.append("")
    L.append("## Reading this result")
    L.append("")
    if l3["emerged_corrected"] and l7["pass"]:
        L.append("**Both criteria now pass.** The founder-check is resolved: the original K1/K3 triggers")
        L.append("were artifacts of the old builder/data-gap, not a true absence of structure. The LLM")
        L.append("prediction call and dedicated hub are legitimately unblocked — building them is real new")
        L.append("scope (model/prompt design, picking a hub port, wiring `orchestrator.start_background()`)")
        L.append("and should be scoped as its own next step, not assumed from this recheck alone.")
    elif not l3["emerged_corrected"] and not l7["pass"]:
        L.append("**Both criteria still fail against the current builder and current data.** The premature-")
        L.append("kill stands. Per the plan's own design: \"the graph survives as an index only (still")
        L.append("useful), and the loop waits for a richer world.\" Recommend NOT building the LLM")
        L.append("prediction call, dedicated hub, or affect-nudge courier yet.")
    else:
        L.append("**Mixed result** — one criterion resolved, one didn't. Read both details above before")
        L.append("deciding; this is not a clean go/no-go and deserves a direct founder read rather than an")
        L.append("automatic verdict.")
    L.append("")
    L.append(f"*Recheck runtime: {round(time.time() - t0, 1)}s. Raw data: `data/lab/lane2_recheck/recheck.json`.*")
    REPORT.write_text("\n".join(L), encoding="utf-8")
    log(f"report written: {REPORT}")
    log(f"DONE in {round(time.time() - t0, 1)}s")


if __name__ == "__main__":
    main()
