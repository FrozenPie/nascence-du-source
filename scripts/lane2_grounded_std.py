#!/usr/bin/env python
"""Place/daylight-standardised grounded_share for the Lane 2 shadow log (J-2172, D-0427).  READ-ONLY.

Why: F-2798 showed the raw grounded_share drop after the D-0411 label change is mostly a place-mix shift
(garden ticks ~13% -> ~33% of ticks; garden runs ~0.30 vs ~0.40 elsewhere).  D-0427 keeps the D-0411 (a)
ruling and asks for a place/daylight-standardised grounded_share going forward, with a defeater: revisit if
the standardised 7-day value < 0.35, or judged metaphor leak > 0.05 on >= 100 judged rows.

Method (direct standardisation): strata = (place, daylight).  Reference weights = the stratum mix of the whole
log (all ticks with a grounded_share), so the number is "what the window's per-stratum means would average to
under the log's long-run place/daylight mix".  Strata with < --min-n window ticks are dropped and the remaining
reference weights renormalised (reported, never silent).  Reference ticks with no recorded place (older rows) are excluded from the reference mix.
No change to core/lane2.py; nothing is written.

    python scripts/lane2_grounded_std.py [--days 7] [--shadow PATH] [--min-n 5]
"""
import argparse, collections, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
DEFEATER_STD_FLOOR = 0.35      # D-0427
DEFEATER_LEAK_CEIL = 0.05      # D-0427
DEFEATER_LEAK_MIN_N = 100


def _rows(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def stratum(r):
    return (str(r.get("place") or "unknown"), str(r.get("daylight") or "unknown"))


def _gs(r):
    v = (r.get("grounding") or {}).get("grounded_share")
    return v if isinstance(v, (int, float)) else None


def standardise(window, reference, min_n=5):
    """window / reference: lists of tick rows.  Returns a dict (pure; no I/O)."""
    ref_cnt = collections.Counter(stratum(r) for r in reference if _gs(r) is not None and r.get("place"))
    ref_tot = sum(ref_cnt.values())
    by = collections.defaultdict(list)
    for r in window:
        if _gs(r) is not None:
            by[stratum(r)].append(_gs(r))
    raw_vals = [v for vs in by.values() for v in vs]
    raw = sum(raw_vals) / len(raw_vals) if raw_vals else None
    used, dropped, num, den = {}, [], 0.0, 0.0
    for s, vs in by.items():
        w = ref_cnt.get(s, 0) / ref_tot if ref_tot else 0.0
        if len(vs) < min_n or w == 0.0:
            dropped.append(("/".join(s), len(vs)))
            continue
        m = sum(vs) / len(vs)
        used["/".join(s)] = {"n": len(vs), "mean": round(m, 3), "ref_w": round(w, 3)}
        num += w * m
        den += w
    std = round(num / den, 3) if den else None
    place_only = collections.defaultdict(list)
    for s, vs in by.items():
        place_only[s[0]] += vs
    return {"n": len(raw_vals), "raw": None if raw is None else round(raw, 3), "standardised": std,
            "ref_coverage": round(den, 3), "strata": used, "dropped_strata": dropped,
            "place_means": {p: {"n": len(v), "mean": round(sum(v) / len(v), 3)} for p, v in place_only.items()}}


def metaphor_leak(window):
    mj = [r for r in window if (r.get("metaphor_judged") or {}).get("verdict") in ("metaphor", "literal")]
    k = sum(1 for r in mj if r["metaphor_judged"]["verdict"] == "metaphor")
    return {"judged_n": len(mj), "leak": round(k / len(mj), 3) if mj else None}


def defeater_check(res, leak):
    """D-0427 defeater: True = a revisit trigger has fired; None = cannot tell yet."""
    low = None if res["standardised"] is None else res["standardised"] < DEFEATER_STD_FLOOR
    leaky = (leak["leak"] > DEFEATER_LEAK_CEIL) if (leak["judged_n"] >= DEFEATER_LEAK_MIN_N and leak["leak"] is not None) else None
    return {"std_below_0.35": low, "leak_above_0.05_on_100plus": leaky,
            "revisit": True if (low or leaky) else (None if (low is None and leaky is None) else False)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--shadow", default=os.path.join(DATA, "lane2_shadow.jsonl"))
    ap.add_argument("--days", type=float, default=7.0)
    ap.add_argument("--min-n", type=int, default=5)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    ticks = [r for r in _rows(a.shadow) if r.get("kind") == "tick"]
    if not ticks:
        print("no ticks")
        return
    last = max(r.get("ts", 0) for r in ticks)
    win = [r for r in ticks if r.get("ts", 0) >= last - a.days * 86400]
    res, leak = standardise(win, ticks, a.min_n), metaphor_leak(win)
    print("== place/daylight-standardised grounded_share (D-0427), last %.1f d: ticks %d ==" % (a.days, len(win)))
    print("raw %s | standardised %s (reference coverage %s) | metaphor leak %s" % (
        res["raw"], res["standardised"], res["ref_coverage"], leak))
    print("per-place:", res["place_means"])
    print("strata used:", res["strata"])
    print("dropped (n<%d or unseen in reference):" % a.min_n, res["dropped_strata"])
    print("D-0427 defeater:", defeater_check(res, leak))


if __name__ == "__main__":
    main()
