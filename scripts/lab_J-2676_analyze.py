"""J-2676 analysis: python scripts/lab_J-2676_analyze.py <scratch dir>. Prints summaries (medians, sums, parse rates)."""
import json, statistics as st, sys
from pathlib import Path

d = Path(sys.argv[1])


def load(n):
    p = d / n
    rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []
    if "inter" in n:                      # inter order: 50 idle + 100 interleaved 'other' payloads, then the chains
        for r in rows:
            if r["kind"] == "human" and r["i"] < 150:
                r["kind"] = "other"
    return rows


def med(x):
    x = [v for v in x if v is not None]
    return round(st.median(x), 3) if x else None


def summ(rows, label):
    idle = [r for r in rows if r["kind"] == "idle"]
    hum = [r for r in rows if r["kind"] == "human"]
    out = {"label": label, "n": len(rows)}
    oth = [r for r in rows if r["kind"] == "other"]
    for nm, g in (("idle", idle), ("human", hum), ("other", oth)):
        if not g:
            continue
        out[nm] = {"n": len(g), "wall_med": med([r["wall"] for r in g]), "wall_mean": round(st.mean(r["wall"] for r in g), 3),
                   "wall_sum": round(sum(r["wall"] for r in g), 1),
                   "prompt_n_med": med([r.get("prompt_n") for r in g]), "prompt_ms_med": med([r.get("prompt_ms") for r in g]),
                   "cache_n_med": med([r.get("cache_n") for r in g]),
                   "gen_n_med": med([r.get("gen_n") for r in g]),
                   "parsed": f"{sum(1 for r in g if r.get('parsed'))}/{len(g)}", "http_fail": sum(1 for r in g if not r.get("ok")),
                   "think_leak": sum(1 for r in g if r.get("think_leak"))}
        if nm == "idle":
            out[nm]["has_thought"] = f"{sum(1 for r in g if r.get('has_thought'))}/{len(g)}"
    return out


for n in ("ollama_b2b.jsonl", "llama_b2b.jsonl", "ollama_inter.jsonl", "llama_inter.jsonl"):
    rows = load(n)
    if rows:
        print(json.dumps(summ(rows, n), indent=1))


def paired(a, b, kind):
    A = {(r["i"]): r for r in load(a)}
    B = {(r["i"]): r for r in load(b)}
    diffs = [A[i]["wall"] - B[i]["wall"] for i in A if i in B and A[i]["kind"] == kind and A[i].get("ok") and B[i].get("ok")]
    return diffs


for order in ("b2b", "inter"):
    for kind in ("idle", "human", "other"):
        df = paired(f"ollama_{order}.jsonl", f"llama_{order}.jsonl", kind)
        if df:
            print(f"paired {order} {kind}: n={len(df)} median drop {med(df)} s, mean drop {round(st.mean(df),3)} s, "
                  f"win rate {sum(1 for x in df if x>0)}/{len(df)}")
# human chain wall: ollama arm vs llama arm, per chain
for order in ("b2b", "inter"):
    for arm in ("ollama", "llama"):
        rows = [r for r in load(f"{arm}_{order}.jsonl") if r["kind"] == "human"]
        by = {}
        for r in rows:
            by.setdefault(r["chain"], []).append(r["wall"])
        if by:
            print(order, arm, "per-chain wall sums (s):", {k: round(sum(v), 1) for k, v in sorted(by.items())},
                  "median", round(st.median(sum(v) for v in by.values()), 1))
