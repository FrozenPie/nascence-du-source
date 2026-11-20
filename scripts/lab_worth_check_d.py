"""J-3473: evaluate the deterministic worth check (core/curiosity_worth_d.py) on labelled sets.
Usage: python scripts/lab_worth_check_d.py main|holdout|fresh|all  [--frontier PATH]
Reads the frozen lab sets under docs/lab/J-3253_data and docs/lab/J-3473_data; the frontier is read-only
(default C:/Nascence/data/frontier.json). Writes nothing but stdout."""
from __future__ import annotations
import json, sys, random
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import curiosity_worth_d as D            # noqa: E402

LAB = ROOT / "docs" / "lab" / "J-3253_data"
LAB2 = ROOT / "docs" / "lab" / "J-3473_data"
FRONTIER = Path("C:/Nascence/data/frontier.json")
CONTROLS = [("K_hello", "hello"), ("K_2plus2", "what is 2+2"), ("K_book", "What is a book?"),
            ("K_bluebird", "Bluebird's arrival rewrites the physical laws governing the Second Empire")]
CONTROL_TS = 1793600000.0


def auc(pos, neg):
    if not pos or not neg:
        return float("nan")
    return sum(1.0 if p > q else 0.5 if p == q else 0.0 for p in pos for q in neg) / (len(pos) * len(neg))


def boot_ci(pos, neg, n=2000, seed=3):
    rng = random.Random(seed); xs = []
    for _ in range(n):
        xs.append(auc([rng.choice(pos) for _ in pos], [rng.choice(neg) for _ in neg]))
    xs.sort()
    return xs[int(.025 * n)], xs[int(.975 * n)]


def load_frontier():
    qs = json.loads(FRONTIER.read_text(encoding="utf-8"))["questions"]
    return sorted(((float(x.get("born", 0) or 0), D.toks(x.get("q", "")), x.get("q", "")) for x in qs if x.get("q")), key=lambda r: r[0])


def prior_for(item, fr):
    me = D.toks(item["q"])
    ts = float(item.get("ts") or 0)
    seen, out = set(), []
    for b, t, q in fr:
        if b >= ts:
            break
        if t == me or q.strip().lower() == item["q"].strip().lower() or t in seen:
            continue
        seen.add(t); out.append(t)
    return out


def agenda_for(item, ag):
    return ag.get("agenda", {}).get(item["id"], [])


def load(which):
    items = []
    if which in ("main", "all"):
        items += json.loads((LAB / "labelled.json").read_text(encoding="utf-8"))["items"]
        items += [{"id": c, "q": q, "ts": CONTROL_TS, "label": "control"} for c, q in CONTROLS]
    if which in ("holdout", "all"):
        items += json.loads((LAB / "holdout.json").read_text(encoding="utf-8"))["items"]
    if which in ("fresh", "all"):
        p = LAB2 / "fresh_labelled.json"
        if p.exists():
            items += json.loads(p.read_text(encoding="utf-8"))["items"]
    return items


def evaluate(which, show=False):
    items = load(which)
    fr = load_frontier()
    ag = json.loads((LAB / "agendas.json").read_text(encoding="utf-8"))
    rows = []
    for it in items:
        f = D.features(it["q"], prior_for(it, fr), agenda_for(it, ag))
        rows.append((it, f, D.raw_score(f)))
    pos = [r for r in rows if r[0]["label"] == "good"]
    neg = [r for r in rows if r[0]["label"] == "bad"]
    res = {"set": which, "n_good": len(pos), "n_bad": len(neg)}
    per = {}
    for k in list(D.WEIGHTS) + list(D.LOGGED_ONLY):
        sign = -1 if (D.WEIGHTS.get(k, -1 if k in ('generic_ref','redundancy','agenda') else 1) < 0) else 1
        per[k] = round(auc([sign * r[1][k] for r in pos], [sign * r[1][k] for r in neg]), 3)
    res["per_feature_auc"] = per
    ps, ns = [r[2] for r in pos], [r[2] for r in neg]
    lo, hi = boot_ci(ps, ns)
    res["composite_auc"] = round(auc(ps, ns), 3); res["ci95"] = [round(lo, 3), round(hi, 3)]
    res["controls"] = {r[0]["id"]: round(D.score(r[0]["q"], prior_for(r[0], fr), agenda_for(r[0], ag)), 3)
                       for r in rows if r[0]["label"] == "control"}
    bord = [r[2] for r in rows if r[0]["label"] == "borderline"]
    res["mean_raw"] = {"good": round(sum(ps) / max(1, len(ps)), 2), "bad": round(sum(ns) / max(1, len(ns)), 2),
                       "borderline": round(sum(bord) / max(1, len(bord)), 2)}
    if show:
        for it, f, s in sorted(rows, key=lambda r: -r[2]):
            print(f"{s:6.2f} {it['label'][:4]:4} {it['id']:5} {it['q'][:90]}")
    return res


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "main"
    print(json.dumps(evaluate(which, show="--show" in sys.argv), indent=1))
