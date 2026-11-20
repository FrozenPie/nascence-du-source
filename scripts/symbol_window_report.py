"""
symbol_window_report.py — the READER for core/symbol_window_shadow.py's log, plus the cross-family
hold-out judge.  J-3226 / D-0615 (part 2 comparison, part 3 judge).

  python scripts/symbol_window_report.py                 # old-vs-new comparison, read-only
  python scripts/symbol_window_report.py --judge         # also run the hold-out judge (gemma4:12b :11439, local)
  python scripts/symbol_window_report.py --judge --max 40 --dry     # show what would be judged, no calls
  python scripts/symbol_window_report.py --calibrate     # order-permutation null for the rolling-drift bar (local embedder, no hub)

COMPARISON (no model calls): per symbol, how often the OLD whole-cycle metric wanted a tablet vs the
provisional rolling-window bar, the two distance distributions side by side, and how far a window sits
from the cycle it came from (window_cycle_cos: low = the window really is a different object from the cycle).

JUDGE (D-0615 part 3). Hold-out = windows from the shadow log. Two labels per window, from different
instruments:
  engine  nearest-centroid on the engine's own embeddings, leave-one-out: the window is "specific" if it is
          nearer to the OTHER windows of its own symbol than to any other symbol's windows.
  judge   gemma4:12b (Google) says whether the passage is about the symbol or merely contains the word.
          A different family from the embedder and from the tablet writer (command-r7b, Cohere).
The same judge also scores the whole-output excerpt of the same cycles (the old metric's input, approximated
by the first 500 chars of the output) so the report shows whether a window is MORE symbol-specific than the
cycle it was cut from. Agreement = fraction where engine label == judge label (plus Cohen's kappa; the base
rates are skewed). D-0615's defeater: agreement above 0.7 -> read-back may be turned on again BY A FOUNDER
RULING (this script turns nothing on); metric cannot separate symbols -> option (b), relabel as day-summaries.
Verdicts are printed, never acted on. Judge results are cached in data/symbol_window_judge.jsonl so reruns
spend no calls on windows already judged. Needs >= _MIN_JUDGED rows for a verdict, else INSUFFICIENT.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_SHADOW_LOG = ROOT / "data" / "symbol_window_shadow.jsonl"
_JUDGE_LOG = ROOT / "data" / "symbol_window_judge.jsonl"
_AGREEMENT_BAR = 0.7        # D-0615 defeater
_MIN_JUDGED = 20            # below this the agreement figure is INSUFFICIENT, not a verdict


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def _med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else None


def comparison(rows: list[dict]) -> dict:
    """Per-symbol old-vs-new readings from the shadow log. Read-only."""
    out: dict = {}
    for r in rows:
        d = out.setdefault(r.get("symbol", "?"), {"rows": 0, "ok": 0, "no_window": 0, "old_drift": [],
                                                   "old_due": 0, "single": [], "window": [],
                                                   "would_fire": 0, "win_cycle_cos": []})
        d["rows"] += 1
        if r.get("status") == "ok":
            d["ok"] += 1
        elif r.get("status") == "no_window":
            d["no_window"] += 1
        d["old_drift"].append(r.get("old_drift"))
        d["old_due"] += 1 if r.get("old_tablet_due") else 0
        d["single"].append(r.get("single_drift"))
        d["window"].append(r.get("window_drift"))
        d["would_fire"] += 1 if r.get("would_fire") else 0
        d["win_cycle_cos"].append(r.get("window_cycle_cos"))
    summary = {}
    for sym, d in out.items():
        summary[sym] = {
            "rows": d["rows"], "windows_ok": d["ok"], "no_window": d["no_window"],
            "old_median_drift": _med(d["old_drift"]), "old_tablets_due": d["old_due"],
            "new_single_median": _med(d["single"]), "new_rolling_median": _med(d["window"]),
            "new_rolling_n": sum(1 for x in d["window"] if x is not None),
            "new_would_fire_at_provisional_bar": d["would_fire"],
            "median_window_vs_cycle_cos": _med(d["win_cycle_cos"]),
        }
    return summary


def rolling_null(rows: list[dict], embed_batch, n_perm: int = 200, seed: int = 0) -> dict:
    """Calibration for the provisional bar: per symbol, the observed rolling-window drift series (same
    recent-N vs older-centroid rule as core/symbol_window_shadow.py) against the SAME windows in random
    order. A drift that is not above the order-shuffled null is not migration, only the noise of short
    sentences. Returns per-symbol observed median, null 95th percentile, share of observed points above it,
    and a pooled suggested bar. Needs >= recent_n + min_older windows per symbol."""
    import numpy as np
    from core import symbol_window_shadow as sw
    rng = np.random.RandomState(seed)
    by_sym: dict[str, list] = {}
    for r in sorted(rows, key=lambda x: x.get("ts", 0)):
        if r.get("status") == "ok" and r.get("window"):
            by_sym.setdefault(r["symbol"], []).append(r["window"])
    need = sw._RECENT_N + sw._MIN_OLDER

    def series(V):
        out = []
        for t in range(need, len(V) + 1):
            recent = V[t - sw._RECENT_N:t]
            older = V[:t - sw._RECENT_N]
            if len(older) >= sw._MIN_OLDER:
                a = np.mean(recent, axis=0); b = np.mean(older, axis=0)
                out.append(1.0 - float(np.dot(a, b) / ((np.linalg.norm(a) * np.linalg.norm(b)) or 1.0)))
        return out

    res, pooled = {}, []
    for sym, texts in by_sym.items():
        if len(texts) < need:
            res[sym] = {"windows": len(texts), "note": f"needs >= {need} windows"}
            continue
        V = np.stack([_unit(v) for v in embed_batch(texts) if v is not None])
        obs = series(list(V))
        null = []
        for _ in range(n_perm):
            null.extend(series([V[i] for i in rng.permutation(len(V))]))
        p95 = float(np.percentile(null, 95)) if null else None
        pooled.extend(null)
        res[sym] = {"windows": len(V), "observed_median": _med(obs), "null_p95": round(p95, 3) if p95 else None,
                    "share_observed_above_null_p95": round(sum(1 for x in obs if p95 is not None and x > p95) / len(obs), 3) if obs else None}
    return {"per_symbol": res,
            "suggested_pooled_bar_null_p95": round(float(np.percentile(pooled, 95)), 3) if pooled else None}


def _unit(v):
    import numpy as np
    n = float(np.linalg.norm(v)) or 1.0
    return v / n


def engine_labels(rows: list[dict], embed_batch) -> dict:
    """Leave-one-out nearest-centroid label per (cycle_id, symbol) window with status ok. Returns
    {key: {"symbol", "window", "excerpt", "margin", "engine_specific"}}. Windows of a symbol with <2
    windows, or a corpus with <2 symbols, get no label (None) — the engine cannot be asked to separate
    one class."""
    import numpy as np
    items = {}
    for r in rows:
        if r.get("status") != "ok" or not r.get("window"):
            continue
        items[(r["cycle_id"], r["symbol"])] = r
    keys = list(items)
    if not keys:
        return {}
    vecs = embed_batch([items[k]["window"] for k in keys])
    by_sym: dict[str, list[int]] = {}
    for i, k in enumerate(keys):
        if vecs[i] is not None:
            by_sym.setdefault(k[1], []).append(i)
    sums = {s: np.sum([_unit(vecs[i]) for i in idx], axis=0) for s, idx in by_sym.items()}
    out = {}
    for i, k in enumerate(keys):
        s = k[1]
        r = items[k]
        rec = {"symbol": s, "window": r["window"], "excerpt": r.get("cycle_excerpt", ""),
               "margin": None, "engine_specific": None}
        if vecs[i] is not None and len(by_sym.get(s, [])) >= 2 and len(by_sym) >= 2:
            v = _unit(vecs[i])
            own = _unit(sums[s] - v)
            own_sim = float(np.dot(v, own))
            other = max(float(np.dot(v, _unit(sums[o]))) for o in by_sym if o != s)
            rec["margin"] = round(own_sim - other, 4)
            rec["engine_specific"] = (own_sim - other) > 0.0
        out[k] = rec
    return out


def sample_holdout(labels: dict, n: int) -> list[tuple]:
    """Deterministic, symbol-stratified (round-robin) sample of up to n labelled windows."""
    by_sym: dict[str, list] = {}
    for k, rec in labels.items():
        if rec["engine_specific"] is None:
            continue
        by_sym.setdefault(k[1], []).append(k)
    for s in by_sym:
        by_sym[s].sort(key=lambda k: hashlib.sha1(f"{k[0]}|{k[1]}".encode()).hexdigest())
    picked: list[tuple] = []
    while len(picked) < n and any(by_sym.values()):
        for s in sorted(by_sym):
            if by_sym[s] and len(picked) < n:
                picked.append(by_sym[s].pop(0))
    return picked


def cohen_kappa(a: list[bool], b: list[bool]) -> "float | None":
    n = len(a)
    if n == 0:
        return None
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe >= 1.0 else round((po - pe) / (1 - pe), 3)


async def run_judge(picked: list[tuple], labels: dict, judge_fn, cache: dict, judge_log: Path) -> None:
    """Judge window + excerpt for each picked key not already in `cache`; append to the judge log."""
    for k in picked:
        rec = labels[k]
        row = cache.get(k)
        if row is None:
            row = {"cycle_id": k[0], "symbol": k[1]}
        changed = False
        for arm, text in (("window", rec["window"]), ("excerpt", rec["excerpt"])):
            if arm in row or not text:
                continue
            res = await judge_fn(k[1], text)
            if res is None:
                continue
            row[arm] = res
            changed = True
        if changed:
            cache[k] = row
            judge_log.parent.mkdir(parents=True, exist_ok=True)
            with open(judge_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_judge_cache(path: Path) -> dict:
    cache: dict = {}
    for r in load_jsonl(path):
        k = (r.get("cycle_id"), r.get("symbol"))
        cur = cache.setdefault(k, {"cycle_id": k[0], "symbol": k[1]})
        for arm in ("window", "excerpt"):
            if arm in r:
                cur[arm] = r[arm]
    return cache


def agreement(labels: dict, cache: dict) -> dict:
    eng, jdg, jx, margins_spec, margins_not = [], [], [], [], []
    for k, row in cache.items():
        rec = labels.get(k)
        if not rec or rec["engine_specific"] is None or "window" not in row:
            continue
        e, j = bool(rec["engine_specific"]), bool(row["window"]["specific"])
        eng.append(e)
        jdg.append(j)
        (margins_spec if j else margins_not).append(rec["margin"])
        if "excerpt" in row:
            jx.append(bool(row["excerpt"]["specific"]))
    n = len(eng)
    agree = round(sum(1 for e, j in zip(eng, jdg) if e == j) / n, 3) if n else None
    if n < _MIN_JUDGED:
        verdict = "INSUFFICIENT"
    elif agree is not None and agree > _AGREEMENT_BAR:
        verdict = "AGREEMENT_ABOVE_BAR"
    else:
        verdict = "AGREEMENT_NOT_ABOVE_BAR"
    return {
        "n_judged": n, "agreement": agree, "kappa": cohen_kappa(eng, jdg), "bar": _AGREEMENT_BAR,
        "engine_specific_rate": round(sum(eng) / n, 3) if n else None,
        "judge_specific_rate_window": round(sum(jdg) / n, 3) if n else None,
        "judge_specific_rate_cycle_excerpt": round(sum(jx) / len(jx), 3) if jx else None,
        "n_excerpt": len(jx),
        "mean_margin_when_judge_specific": round(statistics.mean(margins_spec), 4) if margins_spec else None,
        "mean_margin_when_judge_not": round(statistics.mean(margins_not), 4) if margins_not else None,
        "verdict": verdict,
        "note": "Printed, never acted on: turning the read-back on again is a founder ruling (D-0615).",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(_SHADOW_LOG))
    ap.add_argument("--judge-log", default=str(_JUDGE_LOG))
    ap.add_argument("--judge", action="store_true", help="run the cross-family hold-out judge (local hub)")
    ap.add_argument("--calibrate", action="store_true", help="order-permutation null for the rolling-drift bar (local embedder only)")
    ap.add_argument("--max", type=int, default=40, help="hold-out windows to judge (2 calls each)")
    ap.add_argument("--dry", action="store_true", help="with --judge: list what would be judged, make no calls")
    a = ap.parse_args(argv)

    rows = load_jsonl(Path(a.log))
    if not rows:
        print(f"no shadow rows in {a.log} yet (the metric is restart-gated and logs only on UNPRIMED appearances)")
        return 0
    print(json.dumps({"comparison": comparison(rows)}, indent=2, ensure_ascii=False))
    if not a.judge and not a.calibrate:
        return 0

    import core  # noqa: F401  (before anything that imports lab_env)
    from core.memory.store import _embed_batch
    if a.calibrate:
        print(json.dumps({"rolling_null": rolling_null(rows, _embed_batch)}, indent=2, ensure_ascii=False))
    if not a.judge:
        return 0
    labels = engine_labels(rows, _embed_batch)
    picked = sample_holdout(labels, a.max)
    cache = load_judge_cache(Path(a.judge_log))
    todo = [k for k in picked if "window" not in cache.get(k, {})]
    print(f"labelled windows: {sum(1 for v in labels.values() if v['engine_specific'] is not None)} · "
          f"hold-out sample: {len(picked)} · to judge now: {len(todo)} (up to {2 * len(todo)} calls, local hub only)")
    if a.dry:
        return 0
    from core.symbol_window_judge import judge_window
    asyncio.run(run_judge(picked, labels, judge_window, cache, Path(a.judge_log)))
    print(json.dumps({"judge": agreement(labels, cache)}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
