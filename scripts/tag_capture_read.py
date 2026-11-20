"""
Nascence -- SYNAPTIC TAG-AND-CAPTURE, shadow read (J-2529, I-0107, F-3222 item 2). Read-only. Zero LLM.

Question: for each sleep in a declared window, which of the wake block's LOW-SALIENCE fragments (those the
salience replay did not take) fell within a short window BEFORE a consequential event -- and would therefore
have been "captured" by tag-and-capture? Nothing enters the replay set; this only logs would_capture rows.

The replay cut is NOT re-declared here: core/memory/store.py replay_strengthen() has no numeric threshold --
it takes the per-stratum top-K by (importance - 0.08*replay_count) over episodic, chapter_id IS NULL fragments
since the last sleep, quotas world 3 / lived 3 / inner 2 / deeds+dreams 2. This script reuses that rule.

DECLARED BEFORE THE FIRST RUN (do not tune to the result):
  NIGHT_WINDOW_START   2026-10-16 00:00 local -> every night_log.jsonl row (nap or night) from then on
  WAKE BLOCK           (end of previous sleep row = prev.ts + prev.duration_s, this.ts], capped at 24 h back
  LOW-SALIENCE         episodic, chapter_id IS NULL, replay_count == 0, and NOT in the per-stratum top-K of
                       replay_strengthen's own ORDER BY recomputed on CURRENT values (approximation: importance
                       has since been downscaled; replay_count==0 is the direct "never replayed" evidence)
  CAPTURE_WINDOW_S     1200 (20 min) after the fragment; event must also fall inside the SAME wake block
                       (tags expire with the night; never carried across nights)
  CONSEQUENCE CLASSES and weights:
    deed        data/hands_trace.jsonl dispatch entry decision=='FIRE' with family != 'look'      weight 1.0
    refusal     data/hands_trace.jsonl hands[] answer of a non-look hand matching REFUSAL_RX          weight 1.0
                + data/nascence.log '[monologue] cannot <verb>:' lines                               weight 1.0
    correction  data/nascence.log 'correction detected -> delta_social=X' with X >= 0.5              weight X
    wager_loss  data/logs/recall_wager_shadow.jsonl rows with predicted - measured >= 0.2            weight gap
    retraction  data/retractions.jsonl rows (by ts)                                                  weight 1.0
  consequence score of a fragment = sum of weights of events in (ts, ts + CAPTURE_WINDOW_S] within its block
  BASELINE A (briefed) random same-size sample of the night's low-salience fragments, 1000 draws, seed 2529
  BASELINE B           event-time circular shift within each wake block, 200 iterations, seed 2529
  FALSIFIED IF         overall capture_rate < 0.01, OR the observed capture count is <= the 95th percentile of
                       baseline B (captures no more tied to consequences than event density alone predicts)

Usage: python scripts/tag_capture_read.py --out <path outside data/> [--root C:\\Nascence]
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sqlite3
import statistics
from datetime import datetime
from pathlib import Path

NIGHT_WINDOW_START = datetime(2026, 10, 16, 0, 0).timestamp()
BLOCK_CAP_S = 24 * 3600
CAPTURE_WINDOW_S = 1200
CORRECTION_MIN = 0.5
WAGER_GAP_MIN = 0.2
SEED = 2529
N_SAMPLE_A = 1000
N_SHIFT_B = 200
REFUSAL_RX = re.compile(r"(no seed|have no|there is no|nothing to|already;|too dark|cannot|can't|won't)", re.I)
STRATA = [  # core/memory/store.py replay_strengthen(), verbatim WHERE clauses and quotas
    ("origin IN ('reading','study','research')", 3),
    ("origin IN ('lived','social_notification')", 3),
    ("origin NOT IN ('reading','study','research','lived','social_notification','dream','action','activity')", 2),
    ("origin IN ('dream','action','activity')", 2),
]
LOG_RX = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),(\d{3}) ")
CORR_RX = re.compile(r"correction detected .{0,4}delta_social=([0-9.]+)")
CANNOT_RX = re.compile(r"\[monologue\] cannot [a-z ]+:")


def _jsonl(p: Path):
    if not p.exists():
        return
    with open(p, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                yield json.loads(line)
            except Exception:
                continue


def load_events(root: Path, t0: float) -> list[tuple[float, str, float, str]]:
    ev = []
    for r in _jsonl(root / "data" / "hands_trace.jsonl"):
        ts = float(r.get("ts") or 0)
        if ts < t0:
            continue
        for d in r.get("dispatch") or []:
            if d.get("decision") == "FIRE" and d.get("family") != "look":
                ev.append((ts, "deed", 1.0, f"{r.get('cycle')}:{d.get('family')}"))
        for h in r.get("hands") or []:
            if isinstance(h, dict) and h.get("hand") != "look" and REFUSAL_RX.search(str(h.get("answer") or "")):
                ev.append((ts, "refusal", 1.0, f"{r.get('cycle')}:{h.get('hand')}"))
    with open(root / "data" / "nascence.log", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if "correction detected" not in line and "[monologue] cannot " not in line:
                continue
            m = LOG_RX.match(line)
            if not m:
                continue
            ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp() + int(m.group(2)) / 1000
            if ts < t0:
                continue
            c = CORR_RX.search(line)
            if c and float(c.group(1)) >= CORRECTION_MIN:
                ev.append((ts, "correction", float(c.group(1)), "nascence.log@" + m.group(1)))
            elif CANNOT_RX.search(line):
                ev.append((ts, "refusal", 1.0, "nascence.log@" + m.group(1)))
    for r in _jsonl(root / "data" / "logs" / "recall_wager_shadow.jsonl"):
        ts = float(r.get("ts") or 0)
        gap = float(r.get("predicted") or 0) - float(r.get("measured") or 0)
        if ts >= t0 and gap >= WAGER_GAP_MIN:
            ev.append((ts, "wager_loss", round(gap, 3), str(r.get("cycle_id"))))
    for r in _jsonl(root / "data" / "retractions.jsonl"):
        ts = float(r.get("ts") or 0)
        if ts >= t0:
            ev.append((ts, "retraction", 1.0, str(r.get("claimed"))[:40]))
    ev.sort()
    return ev


def nights(root: Path) -> list[dict]:
    rows = sorted(_jsonl(root / "data" / "night_log.jsonl"), key=lambda r: float(r.get("ts") or 0))
    out, prev_end = [], None
    for r in rows:
        ts = float(r.get("ts") or 0)
        start = max(prev_end or 0.0, ts - BLOCK_CAP_S)
        prev_end = ts + float(r.get("duration_s") or 0)
        if ts >= NIGHT_WINDOW_START:
            out.append({"ts": ts, "kind": r.get("kind"), "start": start, "replay_n": (r.get("stages") or {}).get("replay", {}).get("n")})
    return out


def low_salience(conn, start: float, end: float) -> list[dict]:
    top = set()
    for where, quota in STRATA:
        for (fid,) in conn.execute(
                f"SELECT fragment_id FROM memory_fragments WHERE layer='episodic' AND timestamp > ? AND timestamp <= ? "
                f"AND chapter_id IS NULL AND {where} ORDER BY (importance - 0.08 * replay_count) DESC, timestamp DESC LIMIT ?",
                (start, end, quota)):
            top.add(fid)
    rows = conn.execute(
        "SELECT fragment_id, timestamp, origin, importance FROM memory_fragments WHERE layer='episodic' AND timestamp > ? "
        "AND timestamp <= ? AND chapter_id IS NULL AND COALESCE(replay_count,0)=0", (start, end)).fetchall()
    return [{"fid": f, "ts": float(t), "origin": o, "importance": i} for f, t, o, i in rows if f not in top]


def score(frags, evs, start, end):
    import bisect
    keys = [e[0] for e in evs]  # evs sorted by ts
    out = []
    for f in frags:
        lo = bisect.bisect_right(keys, f["ts"])
        hi = bisect.bisect_right(keys, min(f["ts"] + CAPTURE_WINDOW_S, end))
        hit = evs[lo:hi]
        out.append((sum(e[2] for e in hit), hit))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"C:\Nascence")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    root, out = Path(a.root), Path(a.out)
    if "data" in out.resolve().parts and str(out.resolve()).lower().startswith(str((root / "data").resolve()).lower()):
        raise SystemExit("refusing to write under data/ (read-only shadow read)")
    rng = random.Random(SEED)
    ns = nights(root)
    events = load_events(root, min(n["start"] for n in ns))
    conn = sqlite3.connect(f"file:{(root / 'data' / 'memory' / 'nascence.db').as_posix()}?mode=ro", uri=True)
    table, caps, tot_low, tot_cap, obs_total = [], [], 0, 0, 0
    null_totals = [0] * N_SHIFT_B
    a_means, cap_scores = [], []
    with open(out, "w", encoding="utf-8") as fo:
        for n in ns:
            s, e = n["start"], n["ts"]
            frags = low_salience(conn, s, e)
            evs = [x for x in events if s < x[0] <= e]
            sc = score(frags, evs, s, e)
            cap = [(f, v, h) for f, (v, h) in zip(frags, sc) if h]
            for f, v, h in cap:
                rec = {"night_ts": n["ts"], "fragment_id": f["fid"], "frag_ts": f["ts"], "origin": f["origin"],
                       "score": round(v, 3), "events": [[round(x[0], 1), x[1], x[2], x[3]] for x in h], "would_capture": True}
                fo.write(json.dumps(rec) + "\n")
                caps.append(rec)
                cap_scores.append(v)
            if cap:
                allv = [v for v, _ in sc]
                a_means.append(statistics.mean(statistics.mean(rng.sample(allv, len(cap))) for _ in range(N_SAMPLE_A // 10)))
            span = max(e - s, 1.0)
            for i in range(N_SHIFT_B):
                off = rng.uniform(0, span)
                sh = sorted((s + ((x[0] - s + off) % span), x[1], x[2], x[3]) for x in evs)
                null_totals[i] += sum(1 for _, h in score(frags, sh, s, e) if h)
            by = {}
            for x in evs:
                by[x[1]] = by.get(x[1], 0) + 1
            row = {"night_ts": round(n["ts"], 1), "night": datetime.fromtimestamp(n["ts"]).strftime("%m-%d %H:%M"), "kind": n["kind"],
                   "block_h": round((e - s) / 3600, 2), "replay_n": n["replay_n"], "n_low": len(frags), "n_events": len(evs),
                   "events_by_class": by, "n_captured": len(cap), "capture_rate": round(len(cap) / len(frags), 4) if frags else None}
            table.append(row)
            fo.write(json.dumps({"night_row": row}) + "\n")
            tot_low += len(frags)
            tot_cap += len(cap)
    null_totals.sort()
    p95 = null_totals[int(0.95 * N_SHIFT_B) - 1]
    by_class, by_origin = {}, {}
    for c in caps:
        by_origin[c["origin"]] = by_origin.get(c["origin"], 0) + 1
        for x in c["events"]:
            by_class[x[1]] = by_class.get(x[1], 0) + 1
    summ = {"nights": len(ns), "low_salience": tot_low, "captured": tot_cap,
            "capture_rate": round(tot_cap / tot_low, 4) if tot_low else None,
            "events_total": sum(1 for x in events if x[0] >= min(n["start"] for n in ns)),
            "capture_events_by_class": by_class, "captured_by_origin": by_origin,
            "captured_mean_score": round(statistics.mean(cap_scores), 3) if cap_scores else None,
            "baselineA_random_same_size_mean_score": round(statistics.mean(a_means), 3) if a_means else None,
            "baselineB_shift_null_mean_captured": round(statistics.mean(null_totals), 1), "baselineB_p95": p95,
            "baselineB_p_ge_observed": round(sum(1 for t in null_totals if t >= tot_cap) / N_SHIFT_B, 3),
            "falsified": (tot_low == 0) or (tot_cap / max(tot_low, 1) < 0.01) or (tot_cap <= p95),
            "top10": sorted(caps, key=lambda c: (-c["score"], c["frag_ts"]))[:10]}
    with open(out, "a", encoding="utf-8") as fo:
        fo.write(json.dumps({"summary": summ}) + "\n")
    for r in table:
        print(json.dumps(r))
    s2 = dict(summ)
    s2["top10"] = [(c["fragment_id"], c["origin"], c["score"], [x[1] for x in c["events"]]) for c in summ["top10"]]
    print(json.dumps(s2, indent=1))


if __name__ == "__main__":
    main()
