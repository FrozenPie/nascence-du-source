"""J-3460 (D-0540 defeater): decoupled blind-pair preference check on logged re-entry Phase 0 pairs.

READ-ONLY on data/reentry_shadow.jsonl; writes only a results JSON (default under docs/lab/). Touches no
live store and never flips a flag. Judge model must be a DIFFERENT family than command-r7b/qwen3.5
(default gemma4:12b on :11439; yi:34b on :11442 is the alternative). The ruling stays with Travis.

CAVEAT: first/settled are logged truncated to 200 chars; settled_full is NOT on disk, so the logged
pairs are 200-char HEADS, not whole thoughts. Say so wherever the numbers are quoted.

Arms (each: judge picks the better of two texts, A/B order randomised per item):
  logged   first-head vs settled-head, as logged (the real Phase 0 revision).
  ingr     first-head vs a fresh revision of first-head WITH the logged ingredient. Needs ingredients_full
           (only on rows written after J-3018; 0 rows on disk at build time), else the 80-char truncated
           ingredient is used only with --allow-truncated-ingredient; otherwise the arm is empty.
  control  first-head vs a fresh revision of first-head with an IRRELEVANT ingredient (no-ingredient control),
           so a rewrite effect is separable from the ingredient effect. ingr vs control compares like with
           like (same reviser model); logged vs control is confounded by reviser model - read accordingly.
Preference margin = share preferring the revised text; Wilson 95% interval; unparseable answers excluded.
"""
import argparse, json, random, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "reentry_shadow.jsonl"
NEUTRAL = ("You had this thought:\n\"{draft}\"\n\nHere is some additional context that may or may not be "
           "relevant:\n\"{ingredient}\"\n\nExpress the thought again in your own voice. Keep your own phrasing "
           "except where this context genuinely changes what you think. Do not check it or fix it - just let the "
           "context work on it, or not.")
IRRELEVANT = ["The kettle on the stove is steaming and the window is fogged.",
              "A list of train times: 07:40, 08:15, 08:50, 09:25.",
              "Gravel crunches on the path outside; someone is walking a dog.",
              "The recipe calls for two onions, diced, and a pinch of salt."]
JUDGE_PROMPT = ("Two short passages (each is the opening of a longer thought) respond to the same moment. "
                "Which is the better piece of thinking: clearer, more alive, more specific, less generic? "
                "Judge only the text.\n\nA: \"{a}\"\n\nB: \"{b}\"\n\nAnswer with exactly one letter: A or B.")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def chat(host, model, prompt, timeout=120):
    body = json.dumps({"model": model, "stream": False, "options": {"temperature": 0},
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(host.rstrip("/") + "/api/chat", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["message"]["content"]


def parse_letter(txt):
    m = re.search(r"\b([AB])\b", (txt or "").strip()[:20].upper())
    return m.group(1) if m else None


def judge_pair(call, base, revised, rng):
    """True if revised preferred, False if base, None if unparseable. Order randomised."""
    flip = rng.random() < 0.5
    a, b = (revised, base) if flip else (base, revised)
    L = parse_letter(call(JUDGE_PROMPT.format(a=a, b=b)))
    if L is None:
        return None
    return (L == "A") == flip


def summarize(votes):
    v = [x for x in votes if x is not None]
    k, n = sum(v), len(v)
    lo, hi = wilson(k, n)
    return {"n": n, "unparsed": len(votes) - n, "revised_preferred": k,
            "share": round(k / n, 3) if n else None, "margin_vs_50": round(k / n - 0.5, 3) if n else None,
            "wilson95": [round(lo, 3), round(hi, 3)]}


def run(rows, judge, reviser, rng, arms, allow_trunc):
    out = {a: [] for a in arms}
    for r in rows:
        first, settled = r.get("first", ""), r.get("settled", "")
        if "logged" in arms:
            out["logged"].append(judge_pair(judge, first, settled, rng))
        if "ingr" in arms:
            ing = (r.get("ingredients_full") or [None])[0] or (
                r["ingredients"][0] if allow_trunc and r.get("ingredients") else None)
            if ing:
                out["ingr"].append(judge_pair(judge, first, reviser(NEUTRAL.format(draft=first, ingredient=ing))[:200], rng))
        if "control" in arms:
            out["control"].append(judge_pair(
                judge, first, reviser(NEUTRAL.format(draft=first, ingredient=rng.choice(IRRELEVANT)))[:200], rng))
    return {a: summarize(v) for a, v in out.items()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-host", default="http://localhost:11439")
    ap.add_argument("--judge-model", default="gemma4:12b")
    ap.add_argument("--reviser-host", default=None, help="default = judge host")
    ap.add_argument("--reviser-model", default=None, help="default = judge model")
    ap.add_argument("--kind", default="principle-voiced")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--seed", type=int, default=3460)
    ap.add_argument("--arms", default="logged,ingr,control")
    ap.add_argument("--allow-truncated-ingredient", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "docs" / "lab" / "J-3460_blind_pair_results.json"))
    a = ap.parse_args(argv)
    for bad in ("command-r", "qwen3.5"):
        if bad in a.judge_model:
            sys.exit("judge must be a different family than command-r7b/qwen3.5")
    rows = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("kind") == a.kind and r.get("first") and r.get("settled") and r["first"] != r["settled"]]
    rng = random.Random(a.seed)
    rng.shuffle(rows)
    rows = rows[:a.limit]
    jm, rh, rm = a.judge_model, a.reviser_host or a.judge_host, a.reviser_model or a.judge_model
    res = run(rows, lambda p: chat(a.judge_host, jm, p), lambda p: chat(rh, rm, p), rng,
              a.arms.split(","), a.allow_truncated_ingredient)
    rec = {"job": "J-3460", "ts": time.time(), "judge": jm, "reviser": rm, "n_rows": len(rows), "seed": a.seed,
           "caveat": "pairs are 200-char heads; settled_full not on disk", "arms": res}
    Path(a.out).write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
