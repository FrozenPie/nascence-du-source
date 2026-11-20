"""
Nascence — LANE 1 SELF-CORRECTION BASELINE  ·  docs/plans/lane2_the_witness.md §5  ·  2026-08-20

The pre-Lane-2 counterfactual. Automation-complacency research (Parasuraman & Manzey 2010) says a monitor
makes the monitored party LESS careful, and that this is not preventable by training — so the kill
criterion for Lane 2's eventual read path is "Lane 1's unaided self-correction rate must not fall after
Lane 2's findings reach it." That comparison needs a BEFORE number, captured while Lane 2 does not exist.

SCOPE CORRECTION (2026-08-20): this is NOT as urgent as first written. Complacency requires Lane 2's
findings to actually REACH Lane 1; Phase 0 is shadow-only, so the real deadline is before PHASE 1. And a
baseline is only comparable if the system hasn't drifted in between — so this is built as a ROLLING
instrument (append a snapshot each run) rather than a one-shot capture, giving both long history and a
clean pre-Phase-1 window whenever that arrives.

METHOD — a VECTOR, with one endpoint pre-registered as primary. Five channels measure genuinely different
things, and we do not know which would move under complacency. Capturing all of them and then reporting
whichever moved is HARKing — exactly what pre-registration exists to prevent. So: capture all five, declare
the primary in PRIMARY_ENDPOINT below, treat the rest as secondary/exploratory (the primary/secondary split
clinical trials use; cf. the DSMB precedent in the methodology research).

HONESTY RAIL (the lesson from `lane2_prechecks.py`'s first run, same session): a rate computed over rows
whose verdict is None is not a low rate, it is a BROKEN INSTRUMENT wearing the costume of a finding. Every
channel here reports its own DATA HEALTH (how many rows were actually decidable) alongside its rate, and
the report refuses to state a rate whose denominator is mostly undecidable.

CONTRACT: read-only over `nascence.db` (mode=ro) and read-only over data/*.jsonl. Writes ONLY to
data/lab/lane1_baseline/ + docs/lab/lane1_baseline_report.md. Zero LLM. Deterministic and re-runnable —
re-running it later must measure the same things the same way, or the before/after comparison is void.
"""
from __future__ import annotations

import json
import sqlite3
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB = ROOT / "data" / "memory" / "nascence.db"
DATA = ROOT / "data"
OUT_DIR = ROOT / "data" / "lab" / "lane1_baseline"
SERIES = OUT_DIR / "baseline_series.jsonl"          # rolling: one snapshot appended per run
REPORT = ROOT / "docs" / "lab" / "lane1_baseline_report.md"

DAY = 86400.0
WINDOW_D = 14.0            # days of history summarised per run

# ── PRE-REGISTERED ENDPOINT (declare BEFORE reading any result — changing this later voids the design) ──
PRIMARY_ENDPOINT = "self_interrogation.genuine_per_1k_thoughts"
PRIMARY_RATIONALE = (
    "The most direct operationalisation of spontaneous self-doubt that names something real, and already "
    "graded by a DECOUPLED judge panel rather than self-scored. Chosen despite having the thinnest data of "
    "the five channels, because the alternatives measure architecture-driven correction (resolution_events) "
    "or something only loosely related to self-correction at all (train movement)."
)
MIN_DECIDABLE = 0.30       # below this share of decidable rows, a rate is reported as UNRELIABLE, not stated

# canonical train-movement thresholds — mirrored from core/memory_edges.py so the two agree by construction
RESTATE_HI, DEEPEN_LO = 0.82, 0.40


def _day(ts: float) -> str:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d")


def _jsonl(path: Path):
    if not path.exists():
        return []
    out = []
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def _since(rows, key="ts", days=WINDOW_D):
    cut = time.time() - days * DAY
    return [r for r in rows if float(r.get(key) or 0) >= cut]


# ── denominator: Lane 1's actual thought volume, per day ─────────────────────────────────────────
def thought_volume(con, days=WINDOW_D):
    cut = time.time() - days * DAY
    per_day = defaultdict(int)
    for (ts,) in con.execute(
            "SELECT timestamp FROM memory_fragments WHERE origin='inner_thought' AND timestamp>=?",
            (cut,)):
        per_day[_day(ts)] += 1
    return dict(per_day)


# ── channel 1 (PRIMARY): self-interrogation ──────────────────────────────────────────────────────
def ch_self_interrogation(days=WINDOW_D):
    rows = _since(_jsonl(DATA / "self_interrogation_shadow.jsonl"), days=days)
    fires = [r for r in rows if r.get("kind") == "interrogate"]
    skips = [r for r in rows if r.get("skip")]
    # `genuine` may be None when the decoupled judge panel SPLIT without a tiebreak — that is an
    # undecided row, NOT a "not genuine" row. Conflating them would silently deflate the primary endpoint.
    decided = [r for r in fires if r.get("genuine") in (True, False)]
    genuine = [r for r in decided if r.get("genuine") is True]
    per_day = defaultdict(lambda: {"fires": 0, "decided": 0, "genuine": 0})
    for r in fires:
        d = per_day[_day(r["ts"])]
        d["fires"] += 1
        if r.get("genuine") in (True, False):
            d["decided"] += 1
        if r.get("genuine") is True:
            d["genuine"] += 1
    return {"fires": len(fires), "skips": len(skips), "decided": len(decided), "genuine": len(genuine),
            "decidable_share": round(len(decided) / len(fires), 3) if fires else None,
            "per_day": {k: dict(v) for k, v in per_day.items()}}


# ── channel 2: resolution events (architecture-driven correction) ────────────────────────────────
def ch_resolutions(con, days=WINDOW_D):
    cut = time.time() - days * DAY
    per_day = defaultdict(int)
    n = 0
    for (ts,) in con.execute("SELECT timestamp FROM resolution_events WHERE timestamp>=?", (cut,)):
        per_day[_day(ts)] += 1
        n += 1
    return {"total": n, "per_day": dict(per_day)}


# ── channel 3: T4 provisional identity (identity-level refusal to over-commit) ───────────────────
def ch_provisional(days=WINDOW_D):
    rows = _since(_jsonl(DATA / "logs" / "provisional_identity.jsonl"), days=days)
    ev = defaultdict(int)
    per_day = defaultdict(lambda: defaultdict(int))
    for r in rows:
        e = r.get("event") or "?"
        ev[e] += 1
        per_day[_day(r["ts"])][e] += 1
    return {"events": dict(ev), "per_day": {k: dict(v) for k, v in per_day.items()}}


# ── channel 4: train movement (circling vs developing vs jumping) ────────────────────────────────
def ch_train(days=WINDOW_D):
    rows = _since(_jsonl(DATA / "train_state_log.jsonl"), days=days)
    scored = [r for r in rows if isinstance(r.get("restate_sim"), (int, float))]
    per_day = defaultdict(lambda: {"steps": 0, "circle": 0, "deepen": 0, "jump": 0})
    tot = {"circle": 0, "deepen": 0, "jump": 0}
    for r in scored:
        s = float(r["restate_sim"])
        k = "circle" if s >= RESTATE_HI else ("deepen" if s >= DEEPEN_LO else "jump")
        tot[k] += 1
        d = per_day[_day(r["ts"])]
        d["steps"] += 1
        d[k] += 1
    return {"steps": len(scored), "unscored": len(rows) - len(scored), **tot,
            "decidable_share": round(len(scored) / len(rows), 3) if rows else None,
            "per_day": {k: dict(v) for k, v in per_day.items()}}


# ── channel 5: contradiction pressure (with a staleness guard) ───────────────────────────────────
def ch_contradiction(days=WINDOW_D):
    rows = _since(_jsonl(DATA / "contradiction_ledger_log.jsonl"), days=days)
    vals = [float(r["contradiction_pressure"]) for r in rows
            if isinstance(r.get("contradiction_pressure"), (int, float))]
    distinct = len(set(round(v, 3) for v in vals))
    return {"readings": len(vals), "distinct_values": distinct,
            "mean": round(statistics.fmean(vals), 3) if vals else None,
            # a pressure series that never moves is a dead gauge, not a calm mind
            "stale_suspect": bool(vals and distinct <= max(2, len(vals) // 20))}


def _rate_per_1k(count, thoughts):
    return round(1000.0 * count / thoughts, 3) if thoughts else None


def main():
    if not DB.exists():
        print(f"no DB at {DB}", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)

    vol = thought_volume(con)
    si = ch_self_interrogation()
    res = ch_resolutions(con)
    prov = ch_provisional()
    tr = ch_train()
    contra = ch_contradiction()
    con.close()

    thoughts = sum(vol.values())
    days_seen = sorted(vol)
    # per-day PRIMARY rate — this is what natural variance gets measured on
    primary_daily = []
    for d in days_seen:
        t = vol.get(d, 0)
        g = si["per_day"].get(d, {}).get("genuine", 0)
        if t:
            primary_daily.append(_rate_per_1k(g, t))
    primary_rate = _rate_per_1k(si["genuine"], thoughts)
    primary_sd = round(statistics.stdev(primary_daily), 3) if len(primary_daily) > 1 else None

    snap = {
        "ts": round(t0, 1), "window_days": WINDOW_D, "thoughts": thoughts,
        "primary_endpoint": PRIMARY_ENDPOINT, "primary_rate": primary_rate,
        "primary_daily_sd": primary_sd,
        "self_interrogation": {k: v for k, v in si.items() if k != "per_day"},
        "resolutions_per_1k": _rate_per_1k(res["total"], thoughts),
        "provisional_events": prov["events"],
        "train": {k: v for k, v in tr.items() if k != "per_day"},
        "contradiction": contra,
        "thought_days": len(days_seen),
    }
    with open(SERIES, "a", encoding="utf-8") as f:
        f.write(json.dumps(snap, ensure_ascii=False) + "\n")
    (OUT_DIR / "latest_detail.json").write_text(
        json.dumps({"snapshot": snap, "volume_per_day": vol,
                    "self_interrogation_per_day": si["per_day"], "train_per_day": tr["per_day"],
                    "resolutions_per_day": res["per_day"], "provisional_per_day": prov["per_day"]},
                   indent=1), encoding="utf-8")

    L, A = [], None
    A = L.append
    A("# Lane 1 self-correction baseline — the pre-Lane-2 counterfactual\n")
    A(f"*Run {time.strftime('%Y-%m-%d %H:%M')} · {round(time.time() - t0, 1)}s · zero LLM · DB read-only · "
      f"window {WINDOW_D:.0f}d · rolling series: `data/lab/lane1_baseline/baseline_series.jsonl`*\n")
    A(f"**Pre-registered PRIMARY endpoint:** `{PRIMARY_ENDPOINT}`  ")
    A(f"*{PRIMARY_RATIONALE}*\n")
    A(f"All other channels are SECONDARY/exploratory. Reporting a secondary channel as the result because "
      f"it happened to move is the failure this split exists to prevent.\n")
    A(f"**Denominator:** {thoughts} `inner_thought` fragments across {len(days_seen)} days.\n")

    A("## PRIMARY — self-interrogation\n")
    A(f"- fires: **{si['fires']}** · skips (not sampled): {si['skips']}")
    A(f"- judge reached a verdict on: **{si['decided']}** of {si['fires']}"
      + (f" (**{si['decidable_share']:.0%} decidable**)" if si["decidable_share"] is not None else ""))
    A(f"- genuine: **{si['genuine']}**")
    if si["decidable_share"] is not None and si["decidable_share"] < MIN_DECIDABLE:
        A("")
        A(f"> ⚠ **RATE NOT STATED — INSTRUMENT UNRELIABLE.** Only {si['decidable_share']:.0%} of fires got a")
        A("> real verdict; the rest are judge-panel splits with no tiebreak (`verdict: None`), which are")
        A("> UNDECIDED, not \"not genuine\". Computing a genuine-rate over them would report a broken")
        A("> instrument as a low rate — the exact failure this script's honesty rail exists to catch.")
        A("> **This is the known tiebreak-judge capacity issue (`docs/staged/DEFERRED_PLANS.md` #5):**")
        A("> yi:34b is not resident, so split panels drop. The primary endpoint is BLOCKED on that, not on")
        A("> more runtime. Fix the judge or pick a different primary before this baseline means anything.")
    else:
        A(f"- **primary rate: {primary_rate} genuine per 1k thoughts** "
          f"(daily SD {primary_sd if primary_sd is not None else 'n/a — need >1 day'})")
    A("")

    A("## SECONDARY channels\n")
    A(f"- **resolution_events:** {res['total']} in window → {snap['resolutions_per_1k']} per 1k thoughts")
    A(f"- **T4 provisional identity:** {prov['events'] or '(none in window)'}")
    A(f"- **train movement:** {tr['steps']} scored steps → circling {tr['circle']} · "
      f"deepening {tr['deepen']} · jumping {tr['jump']}"
      + (f" · {tr['circle'] / tr['steps']:.1%} circling" if tr["steps"] else ""))
    A(f"- **contradiction pressure:** {contra['readings']} readings, "
      f"{contra['distinct_values']} distinct values, mean {contra['mean']}"
      + ("  ⚠ **STALE-SUSPECT — the gauge barely moves; treat as dead until confirmed otherwise**"
         if contra["stale_suspect"] else ""))
    A("")

    A("## How to use this\n")
    A("1. Re-run this script unchanged before Phase 1 wires any Lane 2 read path, and again after. Changing")
    A("   the endpoint, thresholds, or channels between runs **voids the comparison**.")
    A("2. The kill threshold is deliberately NOT set yet. Set it from this baseline's own natural")
    A("   week-to-week variance once several snapshots exist — setting a number before knowing the noise")
    A("   floor would be calibrating a gauge nothing has passed through.")
    A("3. Run it periodically regardless; the rolling series is the point.\n")
    A("*Raw: `data/lab/lane1_baseline/latest_detail.json`*")

    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {REPORT}")
    print(f"  thoughts={thoughts} over {len(days_seen)}d · SI fires={si['fires']} "
          f"decidable={si['decidable_share']} genuine={si['genuine']}")
    print(f"  resolutions/1k={snap['resolutions_per_1k']} · train circling="
          f"{(tr['circle'] / tr['steps']) if tr['steps'] else None}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
