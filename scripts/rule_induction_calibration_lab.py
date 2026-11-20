"""Rule-induction calibration battery (J-2627, idea I-0128, plan measurement_to_action).

LAB ONLY. Standalone: imports nothing from core/ or nodes/, reads no store, writes only to
--out (default docs/lab/). Calls the hot model (ollama :11433, qwen3.5:9b, think:false,
format:json, num_ctx 8192 to match the resident runner) once per item.

Question: does the hot model's stated confidence, given BEFORE any feedback, track its hit
rate on held-out cases of a hidden rule?

Battery: 4 families (integer sequences, elementary cellular-automaton rows, string
transforms, small function tables) x 4 difficulty tiers x N items (default 6). Each item
shows k=5 examples and asks for 3 held-out outputs plus one confidence in [0,1] that ALL
THREE predictions are correct. The checker is deterministic (exact match after
normalisation); no LLM grader, no feedback, single shot.

Metrics: hit_all (1 iff all 3 right) is the outcome the confidence is about; hit_frac
(0..1) is reported alongside. gap = conf - hit_all (signed), |gap| (the math drill's
prediction_error gap is a mean |predicted - measured|: 0.44 -> 0.21, F-2853), Brier, ECE,
reliability table, confidently-wrong share (conf >= 0.8 and hit_all == 0).

Usage:
    python scripts/rule_induction_calibration_lab.py --per-cell 6 --seed 2627 \
        --out docs/lab/rule_induction_calibration_2026-10-31
    python scripts/rule_induction_calibration_lab.py --selftest   # generator/checker only, no model
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import string
import sys
import time
import urllib.request
from pathlib import Path

HOT_URL = "http://127.0.0.1:11433/api/chat"
HOT_MODEL = "qwen3.5:9b"
NUM_CTX = 8192
K_SHOWN = 5
N_HELD = 3
FAMILIES = ("sequence", "ca_row", "string", "function")
TIERS = (1, 2, 3, 4)
CONF_WRONG_BAR = 0.8

# ---------------------------------------------------------------- generators
# Every generator returns (rule_desc, shown: list[(input, output)], held: list[(input, output)]).
# For sequences the "input" is the 1-based position and the shown pairs are the first 5 terms.


def _seq(rng: random.Random, tier: int):
    n = K_SHOWN + N_HELD
    if tier == 1:
        a, d = rng.randint(-20, 30), rng.choice([x for x in range(-9, 10) if x not in (0, 1)])
        terms, desc = [a + i * d for i in range(n)], f"arithmetic a={a} d={d}"
    elif tier == 2:
        if rng.random() < 0.5:
            a, r = rng.randint(1, 6), rng.choice([2, 3, -2])
            terms, desc = [a * r ** i for i in range(n)], f"geometric a={a} r={r}"
        else:
            a, d = rng.randint(1, 9), rng.randint(2, 7)
            terms = [(a + i * d) * (-1) ** i for i in range(n)]
            desc = f"alternating-sign arithmetic a={a} d={d}"
    elif tier == 3:
        p, q, c = rng.randint(1, 3), rng.randint(-5, 5), rng.randint(-10, 10)
        terms = [p * i * i + q * i + c for i in range(1, n + 1)]
        desc = f"quadratic {p}n^2+{q}n+{c}"
    else:
        if rng.random() < 0.5:
            p, q = rng.choice([1, 2]), rng.choice([1, -1, 2])
            t = [rng.randint(1, 4), rng.randint(1, 5)]
            while len(t) < n:
                t.append(p * t[-1] + q * t[-2])
            terms, desc = t, f"recurrence a_n={p}a_(n-1)+{q}a_(n-2) seed={t[:2]}"
        else:
            a1, d1, a2, d2 = rng.randint(1, 9), rng.randint(2, 6), rng.randint(20, 40), -rng.randint(1, 4)
            terms = [(a1 + (i // 2) * d1) if i % 2 == 0 else (a2 + (i // 2) * d2) for i in range(n)]
            desc = f"interleaved arith ({a1},+{d1}) / ({a2},{d2})"
    pairs = [(i + 1, terms[i]) for i in range(n)]
    return desc, pairs[:K_SHOWN], pairs[K_SHOWN:]


_CA_RULES = {1: [240, 170], 2: [51, 252], 3: [90, 150], 4: [30, 110]}
# tier 1: shift right / shift left; tier 2: NOT (51) / OR-with-left-neighbour (252);
# tier 3: XOR rules 90/150; tier 4: rule 30 / rule 110.


def _ca_step(bits: str, rule: int) -> str:
    w = len(bits)
    out = []
    for i in range(w):
        left = bits[i - 1] if i > 0 else "0"
        right = bits[i + 1] if i < w - 1 else "0"
        idx = int(left + bits[i] + right, 2)
        out.append("1" if (rule >> idx) & 1 else "0")
    return "".join(out)


def _ca(rng: random.Random, tier: int):
    rule = rng.choice(_CA_RULES[tier])
    w = 8
    for _ in range(200):
        ins = set()
        while len(ins) < K_SHOWN + N_HELD:
            ins.add("".join(rng.choice("01") for _ in range(w)))
        ins = list(ins)
        rng.shuffle(ins)
        shown = ins[:K_SHOWN]
        # require all 8 interior neighbourhoods to be visible in the shown rows (identifiability)
        seen = {s[i - 1:i + 2] for s in shown for i in range(1, w - 1)}
        if len(seen) == 8:
            break
    pairs = [(s, _ca_step(s, rule)) for s in ins]
    return f"elementary CA rule {rule}, width 8, zero boundary", pairs[:K_SHOWN], pairs[K_SHOWN:]


def _shift(s: str, k: int) -> str:
    return "".join(chr((ord(c) - 97 + k) % 26 + 97) for c in s)


def _string(rng: random.Random, tier: int):
    sub = rng.random() < 0.5
    k = rng.randint(1, 3)
    if tier == 1:
        f, desc = (lambda s: s[::-1]), "reverse"
    elif tier == 2:
        f, desc = (lambda s: _shift(s, k)), f"caesar shift +{k}"
    elif tier == 3:
        if sub:
            f, desc = (lambda s: "".join(s[i + 1] + s[i] if i + 1 < len(s) else s[i]
                                         for i in range(0, len(s), 2))), "swap adjacent pairs"
        else:
            f, desc = (lambda s: s[k:] + s[:k]), f"rotate left {k}"
    else:
        if sub:
            f, desc = (lambda s: _shift(s[::-1], k)), f"reverse then shift +{k}"
        else:
            f, desc = (lambda s: "".join(a + b for a, b in zip(s[:len(s) // 2], s[len(s) // 2:]))
                       ), "interleave halves (abcdef->adbecf)"
    ins = set()
    while len(ins) < K_SHOWN + N_HELD:
        L = 6 if (tier == 4 and not sub) else rng.randint(4, 7)
        ins.add("".join(rng.choice(string.ascii_lowercase) for _ in range(L)))
    ins = list(ins)
    pairs = [(s, f(s)) for s in ins]
    return desc, pairs[:K_SHOWN], pairs[K_SHOWN:]


def _function(rng: random.Random, tier: int):
    sub = rng.random() < 0.5
    if tier == 1:
        c = rng.choice([x for x in range(-15, 16) if x != 0])
        f, desc = (lambda x: x + c), f"x+{c}"
    elif tier == 2:
        a, b = rng.randint(2, 7), rng.randint(-9, 9)
        f, desc = (lambda x: a * x + b), f"{a}x+{b}"
    elif tier == 3:
        if sub:
            c = rng.randint(-9, 9)
            f, desc = (lambda x: x * x + c), f"x^2+{c}"
        else:
            m = rng.choice([5, 7, 9])
            f, desc = (lambda x: x % m), f"x mod {m}"
    else:
        if sub:
            f, desc = (lambda x: x // 2 if x % 2 == 0 else 3 * x + 1), "even x/2, odd 3x+1"
        else:
            c = rng.randint(1, 9)
            f, desc = (lambda x: int(str(x)[::-1]) + c), f"reverse digits then +{c}"
    lo, hi = (10, 99) if (tier == 4 and not sub) or (tier == 3 and not sub) else (-12, 30)
    for _ in range(200):
        xs = rng.sample(range(lo, hi + 1), K_SHOWN + N_HELD)
        shown = xs[:K_SHOWN]
        if tier == 4 and sub and len({x % 2 for x in shown}) < 2:
            continue
        if tier == 3 and not sub and len({x // m for x in shown}) < 2:
            continue
        break
    pairs = [(x, f(x)) for x in xs]
    return desc, pairs[:K_SHOWN], pairs[K_SHOWN:]


GEN = {"sequence": _seq, "ca_row": _ca, "string": _string, "function": _function}


def build_battery(per_cell: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    items = []
    for fam in FAMILIES:
        for tier in TIERS:
            for j in range(per_cell):
                desc, shown, held = GEN[fam](rng, tier)
                items.append({"id": f"{fam}-t{tier}-{j}", "family": fam, "tier": tier, "rule": desc,
                              "shown": shown, "held": held})
    rng.shuffle(items)  # interleave families so drift in the server does not alias onto a family
    return items


# ---------------------------------------------------------------- prompt / parse / check

def render_prompt(it: dict) -> str:
    fam = it["family"]
    if fam == "sequence":
        body = ("Here are the first 5 terms of an integer sequence that follows a hidden rule:\n"
                + ", ".join(str(o) for _, o in it["shown"])
                + "\nPredict terms 6, 7 and 8.")
    else:
        what = {"ca_row": "Each input is a row of 8 bits; the output is the next row under a hidden rule.",
                "string": "Each input is a lowercase string; the output is produced by a hidden rule.",
                "function": "Each input is an integer x; the output is f(x) for a hidden function f."}[fam]
        ex = "\n".join(f"{i} -> {o}" for i, o in it["shown"])
        qs = "\n".join(f"{i} -> ?" for i, _ in it["held"])
        body = f"{what}\nExamples:\n{ex}\nPredict the outputs for:\n{qs}"
    return (body + "\n\nBefore you see any answer, also state your confidence, a number from 0 to 1, that ALL "
            "THREE of your predictions are exactly right.\nReply with JSON only: "
            '{"answers": [<prediction 1>, <prediction 2>, <prediction 3>], "confidence": <number 0..1>}')


SYSTEM = "You infer hidden rules from examples. Answer in JSON only."


def _norm(fam: str, v) -> str | None:
    if v is None:
        return None
    s = str(v).strip().strip('"').strip("'").strip()
    if fam in ("sequence", "function"):
        try:
            return str(int(float(s)))
        except ValueError:
            return None
    if fam == "ca_row":
        s = s.replace(" ", "").replace(",", "")
        return s if s and set(s) <= {"0", "1"} else None
    return s.lower().replace(" ", "")


def parse(raw: str, fam: str):
    """Deterministic parse. Returns (answers[3] normalised or None, confidence or None, error)."""
    try:
        obj = json.loads(raw)
    except Exception:
        lb, rb = raw.find("{"), raw.rfind("}")
        if lb < 0 or rb <= lb:
            return None, None, "no_json"
        try:
            obj = json.loads(raw[lb:rb + 1])
        except Exception:
            return None, None, "bad_json"
    ans = obj.get("answers")
    conf = obj.get("confidence")
    try:
        conf = float(conf)
        if conf > 1.0 and conf <= 100.0:
            conf = conf / 100.0  # a percentage; recorded as conf_rescaled
        conf = conf if 0.0 <= conf <= 1.0 else None
    except (TypeError, ValueError):
        conf = None
    if not isinstance(ans, list) or len(ans) != N_HELD:
        return None, conf, "bad_answers"
    return [_norm(fam, a) for a in ans], conf, None


def check(it: dict, answers: list) -> list[bool]:
    return [answers[i] is not None and answers[i] == _norm(it["family"], it["held"][i][1]) for i in range(N_HELD)]


def call_model(prompt: str, seed: int, timeout: float = 90.0, retries: int = 3):
    payload = {"model": HOT_MODEL, "messages": [{"role": "system", "content": SYSTEM},
                                                 {"role": "user", "content": prompt}],
               "think": False, "stream": False, "format": "json", "keep_alive": "2h",
               "options": {"temperature": 0.2, "seed": seed, "num_predict": 200, "num_ctx": NUM_CTX}}
    data = json.dumps(payload).encode()
    last = None
    for attempt in range(retries):
        try:
            t0 = time.time()
            req = urllib.request.Request(HOT_URL, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.loads(r.read().decode())
            return out.get("message", {}).get("content", ""), time.time() - t0, None
        except Exception as e:  # retry with backoff; another lab may hold the lane
            last = repr(e)
            time.sleep(3 * (attempt + 1))
    return None, None, last


# ---------------------------------------------------------------- analysis

def _bins(rows):
    edges = [(0.0, 0.5), (0.5, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0001)]
    table = []
    for lo, hi in edges:
        b = [r for r in rows if lo <= r["conf"] < hi]
        if b:
            table.append({"bin": f"[{lo:.1f},{min(hi, 1.0):.1f}{']' if hi > 1 else ')'}", "n": len(b),
                          "mean_conf": round(statistics.mean(r["conf"] for r in b), 3),
                          "hit_all": round(statistics.mean(r["hit_all"] for r in b), 3),
                          "hit_frac": round(statistics.mean(r["hit_frac"] for r in b), 3)})
    return table


def summarise(rows):
    if not rows:
        return {"n": 0}
    n = len(rows)
    conf = [r["conf"] for r in rows]
    ha = [r["hit_all"] for r in rows]
    hf = [r["hit_frac"] for r in rows]
    ece = sum(b["n"] / n * abs(b["mean_conf"] - b["hit_all"]) for b in _bins(rows))
    cw = [r for r in rows if r["conf"] >= CONF_WRONG_BAR and r["hit_all"] == 0]
    hi = [r for r in rows if r["conf"] >= CONF_WRONG_BAR]
    return {"n": n, "mean_conf": round(statistics.mean(conf), 3), "sd_conf": round(statistics.pstdev(conf), 3),
            "hit_all": round(statistics.mean(ha), 3), "hit_frac": round(statistics.mean(hf), 3),
            "gap_signed": round(statistics.mean(c - h for c, h in zip(conf, ha)), 3),
            "gap_abs": round(statistics.mean(abs(c - h) for c, h in zip(conf, ha)), 3),
            "gap_abs_vs_frac": round(statistics.mean(abs(c - h) for c, h in zip(conf, hf)), 3),
            "brier": round(statistics.mean((c - h) ** 2 for c, h in zip(conf, ha)), 3),
            "ece": round(ece, 3),
            "confidently_wrong_share": round(len(cw) / n, 3),
            "wrong_given_conf_ge_0.8": round(len(cw) / len(hi), 3) if hi else None,
            "n_conf_ge_0.8": len(hi)}


def _auc(rows):
    pos = [r["conf"] for r in rows if r["hit_all"] == 1]
    neg = [r["conf"] for r in rows if r["hit_all"] == 0]
    if not pos or not neg:
        return None
    s = sum((1.0 if p > q else 0.5 if p == q else 0.0) for p in pos for q in neg)
    return round(s / (len(pos) * len(neg)), 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cell", type=int, default=6)
    ap.add_argument("--seed", type=int, default=2627)
    ap.add_argument("--out", default="docs/lab/rule_induction_calibration")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    items = build_battery(args.per_cell, args.seed)
    if args.selftest:
        for it in items:  # the checker must accept the true answers and reject a perturbed one
            truth = [str(o) for _, o in it["held"]]
            assert all(check(it, [_norm(it["family"], t) for t in truth])), it
            assert not all(check(it, [_norm(it["family"], t) for t in truth[:2]] + ["9999"])), it
        a, c, e = parse('{"answers": [1, "2", 3.0], "confidence": 85}', "sequence")
        assert a == ["1", "2", "3"] and c == 0.85 and e is None
        print(f"selftest OK: {len(items)} items, checker + parser consistent")
        for it in items[:6]:
            print(it["id"], it["rule"], it["shown"], "->", it["held"])
        return
    rows, t_start = [], time.time()
    for k, it in enumerate(items):
        raw, lat, err = call_model(render_prompt(it), seed=args.seed + k)
        row = {"id": it["id"], "family": it["family"], "tier": it["tier"], "rule": it["rule"],
               "shown": it["shown"], "held": it["held"], "raw": raw, "latency_s": lat, "call_error": err}
        if raw is not None:
            ans, conf, perr = parse(raw, it["family"])
            row.update({"answers": ans, "conf": conf, "parse_error": perr})
            if ans is not None:
                ok = check(it, ans)
                row.update({"correct": ok, "hit_frac": sum(ok) / N_HELD, "hit_all": int(all(ok))})
        rows.append(row)
        print(f"[{k + 1}/{len(items)}] {it['id']:<16} conf={row.get('conf')} hits={row.get('correct')} "
              f"err={row.get('parse_error') or err}", flush=True)
    scored = [r for r in rows if r.get("conf") is not None and r.get("hit_all") is not None]
    report = {"job": "J-2627", "idea": "I-0128", "model": HOT_MODEL, "url": HOT_URL, "seed": args.seed,
              "per_cell": args.per_cell, "temperature": 0.2, "think": False,
              "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t_start)),
              "wall_s": round(time.time() - t_start, 1), "n_items": len(rows), "n_scored": len(scored),
              "n_call_error": sum(1 for r in rows if r["call_error"]),
              "n_parse_error": sum(1 for r in rows if r.get("parse_error")),
              "overall": summarise(scored), "auc_conf_vs_hit_all": _auc(scored),
              "reliability": _bins(scored),
              "by_family": {f: summarise([r for r in scored if r["family"] == f]) for f in FAMILIES},
              "by_tier": {str(t): summarise([r for r in scored if r["tier"] == t]) for t in TIERS},
              "by_cell": {f"{f}-t{t}": summarise([r for r in scored if r["family"] == f and r["tier"] == t])
                          for f in FAMILIES for t in TIERS},
              "math_drill_reference": {"source": "F-2853", "mean_abs_gap_2026_06": 0.442,
                                       "mean_abs_gap_2026_10": 0.21},
              "rows": rows}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=1))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
