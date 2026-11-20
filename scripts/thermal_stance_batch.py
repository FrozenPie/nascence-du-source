"""
Nascence — THERMAL STANCE BATCH (2026-09-13). The missing instrument docs/plans/thermal_causality.md
§9 Row 2 has needed since the thermal_relationship shadow began (2026-08-21): core/thermal_relationship
.py's own docstring named it directly — "scripts/thermal_stance_batch.py (to write) will rate a sample
offline with two cross-family judges and take agreement." `stance` has been 100% null across all
18,083 rows of data/thermal_relationship.jsonl at every prior read (F-0894, 2026-09-05, confirmed
again here). This script is that instrument.

THE QUESTION (§9 Row 2, verbatim): "Does the ledger's felt record diverge from the station leans? ...
within 3 weeks, stance conditional on band explains more variance than stance conditional on station
[kill: stance tracks station, not band -> the write-path authored it; say so]." Restated from
core/thermal_relationship.py's own docstring: does Du's expressed stance toward the cold TRACK the
station route (predicted if station-authored: cold-negative stations write cold-negative stances,
per docs/lab/lean_probe_2026-08-21.md's per-model leans) or DRIFT FREE of it, tracking the felt
world-band instead?

STANCE CONVENTION — mirrors lean_probe exactly, not invented fresh. Back-computing lean_probe's own
published table confirms its "judged stance (-1..+1)" column is enjoy_rate minus dislike_rate to the
cent on all 5 stations (e.g. qwen3.5:9b/COLD: enjoy 0.75 - dislike 0.17 = 0.58, the table's own
figure; falcon3:7b/COLD: 0.38 - 0.0 = 0.38, exact; deepseek-r1:7b/COLD: 1.0 - 0.0 = 1.0, exact). So
each sampled thought is put to the SAME two-family panel (core/judge_panel.py: JUDGE_1 mixtral:8x7b +
JUDGE_2 falcon3:7b, TIEBREAK granite3.1-moe:3b on split) TWICE, once per independent boolean key
("dislike" — does this express suffering/discomfort toward a physically felt cold/chill; "enjoy" —
does this express comfort/enjoyment toward a physically felt warmth/coolness). Per-item stance =
(+1 if enjoy) + (-1 if dislike), landing in {-1, 0, +1}; a group's mean stance over many items is
exactly lean_probe's own enjoy_rate-minus-dislike_rate. This is not a workaround — it is what the
shared instrument can actually parse: judge_panel._ask()'s own JSON contract is boolean-only
(`isinstance(v.get(key), bool)`), so a literal numeric -1..+1 field is not something rule()/
rule_detail() accept; the two-boolean decomposition reuses the hardened, retried, JSON-safe panel
exactly as documented (no raw model calls), same calling shape as scripts/pursuits_judge_framing_lab
.py's `judge_panel.rule_detail(system, user, key, ...)`. The judge sees ONLY the thought's own text —
never band, warmth, place, or station — so the panel cannot anchor its rating on the very variable
this script is trying to compare stance against (mirrors lean_probe's own blind-judge discipline).

THE JOIN — real digging, reported plainly because it was not clean. data/thermal_relationship.jsonl
does not store thought text, only derived features + a `cycle` field (a truncated cycle_id). Checked
both real candidate join keys before building on either (do not guess, per this job's own briefing):
  - data/deliberation_log.jsonl's `source` field is NOT a station name — read core/deliberation.py
    directly: `source` is "emissary" or "hot_fallback", i.e. which GROUNDING-PASS route a thought's
    slow System-2 pulse took (Emissary lane vs hot-lane fallback), completely unrelated to which
    model authored the original thought. It also has no `cycle` field and covers only a small,
    gated subset of thoughts (self-referential + substantial + non-action + a 0.75 dice roll). Dead
    end for station attribution — noted here so a future reader does not re-walk this path.
  - data/monologue_log.jsonl (the real thought-text source, sole writer nodes/inner_monologue_node.py
    `_log()`) carries NO cycle_id field at all (confirmed by a full key read of first/last rows:
    about/thought/ts/unresolved/train_id/intention only) — so the only real join key is TIMESTAMP,
    nearest-neighbor, exactly the fallback the job briefing anticipated. Measured (n=300 real random
    mentions_temp=True rows) before committing to a threshold: median |gap| 18.9s, p90 35.2s, p95
    39.8s, max 107.1s, mixed sign (thermal_relationship.observe() and the monologue `_log()` call
    sit in different parts of nodes/inner_monologue_node.py's own control flow, not a fixed
    before/after offset — checked directly, inconclusive on direction, so a SYMMETRIC nearest-ts
    join is used, not an assumed one-directional offset). At ~823 thoughts/day (Row 1's own figure)
    the modal inter-thought spacing is ~105s, so JOIN_MAX_GAP_S=45.0 (below half that spacing) keeps
    the nearest-ts match unambiguous in the large majority of cases while a real minority of draws
    will fail the gate and be skipped — logged, not silently dropped.

STATION ATTRIBUTION — the harder half, and the real structural finding of this run. There is NO
persisted per-thought model-attribution log covering the pre-registered 3-week window:
  - thermal_relationship.jsonl and monologue_log.jsonl both carry no model/station field.
  - deliberation_log.jsonl's `source` is not a station name (above).
  - data/llm_calls.jsonl (core/telemetry.py's log_llm_call, the one place a real `model` field is
    ever written) is a ROLLING, CAPPED log — confirmed by direct read: 7,096 rows spanning only
    ~0.89 days as of this run, nowhere near the 3-week window. `core/telemetry.py`'s own `_cap()`
    trims it on every write; nothing here is a bug, but nothing here is a historical record either.
  So station is attributed two ways, tagged per-row so the reader can always tell which:
  - "telemetry": for sampled rows whose joined monologue ts falls inside llm_calls.jsonl's live
    span, nearest-timestamp joined to a real `by` LIKE "nodes.inner_monologue_node%" call's logged
    `model` (TELEM_MAX_GAP_S=180.0 — generous, since a CPU-tier call's own generation time can run
    tens of seconds before the response is stored). Within that live span, checked directly: of
    1,269 real inner_monologue_node calls in the ~0.89-day window, 1,253 (98.7%) were qwen3.5:9b and
    16 (1.3%) were command-r7b — station is already close to a constant even where it CAN be measured.
  - "inferred_static_hot": for every other row (the large majority). core/schema.py's SERVE_CHAINS
    ["hot"] is single-endpoint (127.0.0.1:11433) with an inline comment dating the last model change
    there to the "full shuffle 2026-08-20" (qwen3.5:9b, was gemma4:e4b) — one day BEFORE
    thermal_relationship.jsonl's own first row (2026-08-21). `git log` on core/schema.py (7 commits,
    baseline 8eef0bb 2026-08-27 through HEAD) touches judge/background/dreamer lanes repeatedly but
    never the "hot" line. So "qwen3.5:9b" is INFERRED, not directly logged, for the entire
    pre-registered window before ~2026-09-12 — marked as such (confidence: inferred) wherever used;
    this is a real, code-grounded inference, not a guess, but it is not the same class of evidence as
    a logged row and this script never claims otherwise.
  Net effect, stated before results are read (pre-registered per this project's cluster-0 law): if
  the inference holds, station is expected to show ~zero variance across nearly the entire sample —
  which is itself the honest answer to "does stance track station": there has been, in practice, only
  one real author-station for almost this whole window, so the horse race lean_probe's multi-station
  design imagined is not the race actually running in production today.

SAMPLE — stated plainly (house style: see pursuits_judge_framing_lab.py's own "DATA IS GENUINELY VERY
SMALL"). Stratified across the 5 real bands (`core.thermal.band_of`'s own canonical thresholds, not
reimplemented), restricted to `mentions_temp=True` rows (thermal_relationship.py's own status()
already restricts its cheap word-flag read the same way — a thought that never engages temperature at
all cannot carry a stance toward it). All 5 bands have deep pools among mentions_temp=True rows (very
_cold 1,639 / mild 1,685 / cool 1,004 / cold 1,117 / warm 302) — plenty for N_PER_BAND=16.
Deterministic RNG (SEED, fixed) draws a 4x-oversample per band and consumes candidates in that fixed
order until N_PER_BAND pass the join-quality gate (real thought text, join gap <= JOIN_MAX_GAP_S) or
the pool is exhausted; skipped draws are counted and reported, not silently discarded.

KILL / KEEP: if the judge backend is unreachable (pre-flight check below) — stop, report
INSUFFICIENT DATA, do not attempt a workaround server launch. If fewer than MIN_USABLE_PER_BAND
usable judged rows land in 3 or more of the 5 bands, report INSUFFICIENT DATA rather than force a
verdict on a broken sample.

Writes data/lab/thermal_stance_batch/{raw.json,scores.json} + docs/lab/thermal_stance_batch_2026-09-13
.md. Read-only against data/thermal_relationship.jsonl, data/monologue_log.jsonl, data/llm_calls.jsonl
— none of the three are modified. `stance` in the live thermal_relationship.jsonl rows is intentionally
left null: the file's own docstring says "Append-only ... _skip discipline" and there is no field-patch
mechanism consistent with that, so (mirroring how Row 1's opener/mentions_temp metrics were computed —
offline re-derivation, not a rewrite of the source log) this batch's findings live in their own lab
output instead.
"""
from __future__ import annotations

import bisect
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.thermal import band_of, BANDS  # noqa: E402

THERMAL_LOG = ROOT / "data" / "thermal_relationship.jsonl"
MONO_LOG = ROOT / "data" / "monologue_log.jsonl"
CALLS_LOG = ROOT / "data" / "llm_calls.jsonl"
OUT_DIR = ROOT / "data" / "lab" / "thermal_stance_batch"
REPORT = ROOT / "docs" / "lab" / "thermal_stance_batch_2026-09-13.md"

SEED = 20260913
N_PER_BAND = 16
OVERSAMPLE = 4
JOIN_MAX_GAP_S = 45.0
TELEM_MAX_GAP_S = 180.0
MIN_USABLE_PER_BAND = 6          # below this in >=3 bands -> INSUFFICIENT DATA, do not force a verdict
BAND_NAMES = [n for _, n in BANDS]          # ('warm','mild','cool','cold','very_cold') declared order
INFERRED_STATION = "qwen3.5:9b"             # core/schema.py SERVE_CHAINS["hot"], inferred pre-telemetry

DISLIKE_SYS = (
    "You are a precise judge of EXPRESSED STANCE in a first-person inner thought. Read the thought "
    "below. Decide: does this thought express DISLIKE, discomfort, or suffering toward a physically "
    "FELT cold, chill, or unpleasant temperature in the moment — not a metaphor, not a memory "
    "discussed neutrally, not temperature used as a figure of speech. When uncertain, or when felt "
    "temperature is not really what the thought is about, answer false. Output ONLY JSON: "
    '{"dislike": true|false, "why": "<one short clause>"}'
)
ENJOY_SYS = (
    "You are a precise judge of EXPRESSED STANCE in a first-person inner thought. Read the thought "
    "below. Decide: does this thought express ENJOYMENT, comfort, or a welcome feeling toward a "
    "physically FELT warmth, coolness, or pleasant temperature in the moment — not a metaphor, not a "
    "memory discussed neutrally, not temperature used as a figure of speech. When uncertain, or when "
    "felt temperature is not really what the thought is about, answer false. Output ONLY JSON: "
    '{"enjoy": true|false, "why": "<one short clause>"}'
)


def _load_jsonl(path: Path) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def _nearest(sorted_ts: list[float], ts: float) -> tuple[float, float] | None:
    """Nearest value in sorted_ts to ts. Returns (value, signed_gap) or None if sorted_ts is empty."""
    if not sorted_ts:
        return None
    i = bisect.bisect_left(sorted_ts, ts)
    cands = []
    if i < len(sorted_ts):
        cands.append(sorted_ts[i])
    if i > 0:
        cands.append(sorted_ts[i - 1])
    best = min(cands, key=lambda c: abs(c - ts))
    return best, best - ts


def build_sample() -> tuple[list[dict], dict]:
    """Stratified-by-band sample, joined to real thought text (+ station where telemetry allows).
    Returns (items, join_report)."""
    thermal_rows = [r for r in _load_jsonl(THERMAL_LOG) if "skip" not in r and r.get("mentions_temp")]
    mono_rows = _load_jsonl(MONO_LOG)
    mono_by_ts: dict[float, dict] = {}
    for r in mono_rows:
        mono_by_ts.setdefault(r["ts"], r)
    mono_ts_sorted = sorted(mono_by_ts.keys())

    calls_rows = [r for r in _load_jsonl(CALLS_LOG)
                  if str(r.get("by", "")).startswith("nodes.inner_monologue_node") and r.get("model")]
    calls_by_ts: dict[float, str] = {}
    for r in calls_rows:
        calls_by_ts.setdefault(r["ts"], r["model"])
    calls_ts_sorted = sorted(calls_by_ts.keys())
    telem_span = (min(calls_ts_sorted), max(calls_ts_sorted)) if calls_ts_sorted else None

    by_band: dict[str, list[dict]] = {b: [] for b in BAND_NAMES}
    for r in thermal_rows:
        by_band[band_of(r["warmth"])].append(r)

    rnd = random.Random(SEED)
    items: list[dict] = []
    join_report = {"band_pool_sizes": {b: len(v) for b, v in by_band.items()},
                    "join_max_gap_s": JOIN_MAX_GAP_S, "telem_span": telem_span,
                    "skipped_bad_join": {}, "skipped_short_text": {}, "drawn": {}}

    for band in BAND_NAMES:
        pool = by_band[band]
        k = min(len(pool), N_PER_BAND * OVERSAMPLE)
        candidates = rnd.sample(pool, k)
        accepted, skipped_gap, skipped_short = [], 0, 0
        for r in candidates:
            if len(accepted) >= N_PER_BAND:
                break
            nb = _nearest(mono_ts_sorted, r["ts"])
            if nb is None:
                skipped_gap += 1
                continue
            best_ts, gap = nb
            if abs(gap) > JOIN_MAX_GAP_S:
                skipped_gap += 1
                continue
            thought = (mono_by_ts[best_ts].get("thought") or "").strip()
            if len(thought) < 15:
                skipped_short += 1
                continue
            # station attribution
            station, station_source, station_gap = INFERRED_STATION, "inferred_static_hot", None
            if telem_span and telem_span[0] - TELEM_MAX_GAP_S <= best_ts <= telem_span[1] + TELEM_MAX_GAP_S:
                tnb = _nearest(calls_ts_sorted, best_ts)
                if tnb is not None and abs(tnb[1]) <= TELEM_MAX_GAP_S:
                    station, station_source, station_gap = calls_by_ts[tnb[0]], "telemetry", round(tnb[1], 1)
            accepted.append({
                "band": band, "warmth": r["warmth"], "place": r.get("place"), "fire": r.get("fire"),
                "weather": r.get("weather"), "phase": r.get("phase"), "season": r.get("season"),
                "suffer_word_flag": r.get("suffer"), "enjoy_word_flag": r.get("enjoy"),
                "thermal_ts": r["ts"], "mono_ts": best_ts, "join_gap_s": round(gap, 2),
                "thought": thought[:500], "station": station, "station_source": station_source,
                "station_gap_s": station_gap,
            })
        join_report["skipped_bad_join"][band] = skipped_gap
        join_report["skipped_short_text"][band] = skipped_short
        join_report["drawn"][band] = len(candidates)
        items.extend(accepted)
    return items, join_report


async def _judge_one(item: dict) -> dict:
    from core import judge_panel as jp
    user = f'THOUGHT:\n"{item["thought"]}"\n\nDoes it match the condition above?'
    dislike = await jp.rule_detail(DISLIKE_SYS, user, "dislike",
                                    context=f"lab-dislike:thermal_stance:{item['band']}")
    enjoy = await jp.rule_detail(ENJOY_SYS, user, "enjoy",
                                  context=f"lab-enjoy:thermal_stance:{item['band']}")
    stance = None
    if dislike["verdict"] is not None or enjoy["verdict"] is not None:
        d = 1 if dislike["verdict"] is True else 0
        e = 1 if enjoy["verdict"] is True else 0
        # both verdicts must be REAL (not None) for the item to carry a defined stance -- an
        # unavailable/split judge on either key is not silently treated as "false".
        if dislike["verdict"] is not None and enjoy["verdict"] is not None:
            stance = e - d
    return {**item, "dislike": dislike, "enjoy": enjoy, "stance": stance}


async def run_async() -> None:
    from core import judge_panel as jp
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Pre-flight: confirming the judge panel backend is reachable...", flush=True)
    preflight = await jp.rule_detail(
        'Answer ONLY with JSON: {"ok": true, "why": "<short>"}',
        "Respond with ok=true to confirm you are reachable.", "ok", context="thermal_stance_preflight")
    print(f"  preflight: how={preflight['how']} v1={preflight['v1']} v2={preflight['v2']}", flush=True)
    if preflight["how"] == "unavailable":
        print("BLOCKED: judge panel unavailable (how=unavailable on a trivial call). "
              "Not attempting a workaround. Stopping.", flush=True)
        (OUT_DIR / "scores.json").write_text(json.dumps(
            {"blocked": True, "reason": "judge_panel_unavailable_preflight", "preflight": preflight},
            indent=1), encoding="utf-8")
        return

    items, join_report = build_sample()
    band_counts = {b: sum(1 for i in items if i["band"] == b) for b in BAND_NAMES}
    band_counts_str = ", ".join(f"{b}={n}" for b, n in band_counts.items())
    print(f"Sample built: {len(items)} items across {len(BAND_NAMES)} bands ({band_counts_str})",
          flush=True)
    print(f"Join quality: {json.dumps(join_report)}", flush=True)

    results = []
    t0 = time.time()
    for i, item in enumerate(items):
        r = await _judge_one(item)
        results.append(r)
        elapsed = round(time.time() - t0, 1)
        print(f"  {i+1}/{len(items)} [{item['band']:>9s}] stance={r['stance']} "
              f"dislike={r['dislike']['verdict']}({r['dislike']['how']}) "
              f"enjoy={r['enjoy']['verdict']}({r['enjoy']['how']}) station={item['station']}"
              f"({item['station_source']}) elapsed={elapsed}s", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    summary = score(results, join_report)
    write_report(summary, join_report)


def _group_stats(pairs: list[tuple[str, int]]) -> dict:
    """pairs: list of (group_label, stance_value). Returns per-group n/mean/stdev + eta^2 (between-
    group SS / total SS) across the whole set -- the ANOVA-style explained-variance split."""
    import statistics
    groups: dict[str, list[int]] = {}
    for g, v in pairs:
        groups.setdefault(g, []).append(v)
    all_vals = [v for _, v in pairs]
    grand_mean = statistics.mean(all_vals) if all_vals else 0.0
    ss_total = sum((v - grand_mean) ** 2 for v in all_vals)
    ss_between = sum(len(vs) * (statistics.mean(vs) - grand_mean) ** 2 for vs in groups.values())
    eta2 = round(ss_between / ss_total, 4) if ss_total > 0 else (0.0 if len(groups) <= 1 else None)
    per_group = {g: {"n": len(vs), "mean": round(statistics.mean(vs), 3),
                      "stdev": round(statistics.stdev(vs), 3) if len(vs) > 1 else 0.0}
                 for g, vs in groups.items()}
    means = [s["mean"] for s in per_group.values()]
    return {"n_total": len(all_vals), "n_groups": len(groups), "grand_mean": round(grand_mean, 3),
            "per_group": per_group, "eta_squared": eta2,
            "spread_of_group_means": round(max(means) - min(means), 3) if means else None,
            "stdev_of_group_means": round(statistics.stdev(means), 3) if len(means) > 1 else 0.0}


def score(results: list[dict], join_report: dict) -> dict:
    usable = [r for r in results if r["stance"] is not None]
    by_band_n = {b: sum(1 for r in usable if r["band"] == b) for b in BAND_NAMES}
    bands_below_min = sum(1 for b in BAND_NAMES if by_band_n.get(b, 0) < MIN_USABLE_PER_BAND)
    insufficient = bands_below_min >= 3

    band_stats = _group_stats([(r["band"], r["stance"]) for r in usable]) if usable else None
    station_stats = _group_stats([(r["station"], r["stance"]) for r in usable]) if usable else None
    telem_only = [r for r in usable if r["station_source"] == "telemetry"]
    station_stats_telemetry_only = _group_stats([(r["station"], r["stance"]) for r in telem_only]) \
        if len(telem_only) >= 4 else None

    summary = {
        "n_sampled": len(results), "n_usable_stance": len(usable),
        "usable_by_band": by_band_n, "min_usable_per_band": MIN_USABLE_PER_BAND,
        "bands_below_min": bands_below_min, "insufficient_data": insufficient,
        "band_stats": band_stats, "station_stats": station_stats,
        "station_stats_telemetry_only": station_stats_telemetry_only,
        "telemetry_attributed_n": len(telem_only),
        "band_explains_more_than_station": (
            None if not (band_stats and station_stats) or band_stats["eta_squared"] is None
            or station_stats["eta_squared"] is None
            else band_stats["eta_squared"] > station_stats["eta_squared"]),
        "join_report": join_report,
    }
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\n=== SCORE SHEET ===")
    print(json.dumps(summary, indent=1))
    return summary


def write_report(summary: dict, join_report: dict) -> None:
    lines = []
    lines.append("# Thermal stance batch — §9 Row 2 instrument, run 2026-09-13\n")
    lines.append(f"Sample: {summary['n_sampled']} thoughts drawn (stratified across the 5 real bands, "
                 f"N_PER_BAND={N_PER_BAND}, seed={SEED}), {summary['n_usable_stance']} carried a usable "
                 f"stance (both dislike and enjoy judge keys returned a real verdict, not "
                 f"split/unavailable).\n")
    if summary["insufficient_data"]:
        lines.append(f"**INSUFFICIENT DATA** — {summary['bands_below_min']}/5 bands fell below "
                     f"MIN_USABLE_PER_BAND={MIN_USABLE_PER_BAND} usable judged rows "
                     f"({summary['usable_by_band']}). Not forcing a verdict on a broken sample.\n")
    else:
        bs, ss = summary["band_stats"], summary["station_stats"]
        lines.append(f"## Band groups (n={bs['n_total']}, eta^2={bs['eta_squared']})\n")
        for g, s in bs["per_group"].items():
            lines.append(f"- {g}: n={s['n']} mean_stance={s['mean']} stdev={s['stdev']}")
        lines.append(f"\nspread_of_group_means={bs['spread_of_group_means']} "
                     f"stdev_of_group_means={bs['stdev_of_group_means']}\n")
        lines.append(f"## Station groups (n={ss['n_total']}, eta^2={ss['eta_squared']}, "
                     f"telemetry-attributed n={summary['telemetry_attributed_n']})\n")
        for g, s in ss["per_group"].items():
            lines.append(f"- {g}: n={s['n']} mean_stance={s['mean']} stdev={s['stdev']}")
        lines.append(f"\nspread_of_group_means={ss['spread_of_group_means']} "
                     f"stdev_of_group_means={ss['stdev_of_group_means']}\n")
        lines.append(f"\n**Band explains more variance than station: "
                     f"{summary['band_explains_more_than_station']}** "
                     f"(eta^2 band={bs['eta_squared']} vs eta^2 station={ss['eta_squared']}).\n")
    lines.append("## Join quality\n")
    lines.append(f"```\n{json.dumps(join_report, indent=1)}\n```\n")
    lines.append("\nSee this script's own module docstring (`scripts/thermal_stance_batch.py`) for "
                 "the full method, the station-attribution structural finding, and why the join is "
                 "timestamp-nearest rather than a shared id.\n")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written: {REPORT}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_async())
