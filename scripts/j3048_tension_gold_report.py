"""J-3048 step 3: score the replay rulings against the blind gold labels.  Pure reader: no model call, no write except stdout
(and --md PATH, a table dump under the worktree).

Reads docs/lab/J-3048_data/{gold_pairs.jsonl,gold_labels.json,replay_gemma.jsonl,replay_falcon.jsonl}.
gold: S (settles) is the positive class; R (restates) and U (unrelated) are both 'does not settle'.
Arms: gemma (one local judge), falcon (one local judge), panel (both must say True; both False -> False; a split -> None, which
the live panel returns for key 'resolves' under D-0530, and which is read as NOT passed).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
DATA = ROOT / "docs" / "lab" / "J-3048_data"
VARIANTS = ("V0", "V1", "V2", "V3")
NAMES = {"V0": "V0 live", "V1": "V1 no-prefix", "V2": "V2 +events", "V3": "V3 both"}


def wilson(k: int, n: int, z: float = 1.96) -> tuple:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def kappa(tp: int, fp: int, fn: int, tn: int) -> float:
    n = tp + fp + fn + tn
    if n == 0:
        return float("nan")
    po = (tp + tn) / n
    pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def load(path: Path) -> list:
    if not path.exists():
        return []
    out = []
    for l in open(path, encoding="utf-8"):
        try:
            out.append(json.loads(l))
        except Exception:
            pass
    return out


def load_gold() -> dict:
    labs = json.load(open(DATA / "gold_labels.json", encoding="utf-8"))["labels"]
    return {g: v for g, v in labs.items()}


def verdicts(rows_by_hub: dict) -> dict:
    """{(arm, variant): {gid: True|False|None}} for arms gemma, falcon, panel. Infra-excluded rows are dropped; a gid is in the
    panel arm only if BOTH hubs answered it."""
    one = {}
    for hub, rows in rows_by_hub.items():
        for r in rows:
            if r.get("infra_excluded"):
                continue
            one.setdefault((hub, r["variant"]), {})[r["gid"]] = r["v"]
    out = dict(one)
    for v in VARIANTS:
        g, f = one.get(("gemma", v), {}), one.get(("falcon", v), {})
        both = set(g) & set(f)
        if both:
            out[("panel", v)] = {gid: (g[gid] if g[gid] == f[gid] else None) if g[gid] is not None and f[gid] is not None else None
                                 for gid in both}
    return out


def score(vmap: dict, gold: dict, source_of: dict) -> dict:
    """vmap gid->verdict. None verdicts are not counted in agreement; on the panel a None is a split (reported separately)."""
    tp = fp = fn = tn = nov = 0
    cl_pass = cl_n = rf_pass = rf_n = 0
    sure = [0, 0]
    for gid, vd in vmap.items():
        if vd is None:
            nov += 1
            continue
        g = gold[gid]["label"] == "S"
        if vd and g:
            tp += 1
        elif vd and not g:
            fp += 1
        elif (not vd) and g:
            fn += 1
        else:
            tn += 1
        if not gold[gid]["unsure"]:
            sure[1] += 1
            sure[0] += int(vd == g)
        if source_of[gid] == "closure":
            cl_n += 1
            cl_pass += int(vd)
        else:
            rf_n += 1
            rf_pass += int(vd)
    n = tp + fp + fn + tn
    return {"n": n, "no_verdict": nov, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "agree": (tp + tn, n), "kappa": kappa(tp, fp, fn, tn),
            "pass": (tp + fp, n), "false_keep": (fp, fp + tn), "false_reject": (fn, fn + tp),
            "closure_pass": (cl_pass, cl_n), "refuted_pass": (rf_pass, rf_n), "sure_agree": tuple(sure)}


def pct(t) -> str:
    k, n = t
    if n == 0:
        return "-"
    lo, hi = wilson(k, n)
    return f"{100 * k / n:.0f}% ({k}/{n}) [{100 * lo:.0f}-{100 * hi:.0f}]"


def cost(rows_by_hub: dict) -> dict:
    out = {}
    for hub, rows in rows_by_hub.items():
        for v in VARIANTS:
            rs = [r for r in rows if r["variant"] == v and not r.get("infra_excluded") and r.get("secs") is not None]
            if rs:
                out[(hub, v)] = (sum(r["secs"] for r in rs) / len(rs), sum(r["prompt_chars"] for r in rs) / len(rs), len(rs))
    return out


def flips(base: dict, other: dict, gold: dict) -> tuple:
    """Paired change vs V0 over gids both ruled with a verdict: (pass->fail correct, pass->fail wrong, fail->pass correct, fail->pass wrong)."""
    a = b = c = d = 0
    for gid in set(base) & set(other):
        x, y = base[gid], other[gid]
        if x is None or y is None or x == y:
            continue
        g = gold[gid]["label"] == "S"
        if x and not y:
            a, b = (a + 1, b) if not g else (a, b + 1)
        else:
            c, d = (c + 1, d) if g else (c, d + 1)
    return a, b, c, d


def report(md: bool = False) -> str:
    gold = load_gold()
    pairs = [json.loads(l) for l in open(DATA / "gold_pairs.jsonl", encoding="utf-8")]
    source_of = {p["gid"]: p["source"] for p in pairs}
    rows = {"gemma": load(DATA / "replay_gemma.jsonl"), "falcon": load(DATA / "replay_falcon.jsonl")}
    vm = verdicts(rows)
    lines = []
    ng = defaultdict(int)
    for g in gold.values():
        ng[g["label"]] += 1
    nclos = sum(1 for s in source_of.values() if s == "closure")
    gold_by_src = defaultdict(lambda: defaultdict(int))
    for gid, g in gold.items():
        gold_by_src[source_of[gid]][g["label"]] += 1
    lines.append(f"gold: {dict(ng)}  unsure {sum(g['unsure'] for g in gold.values())}/{len(gold)};  "
                 f"closures {dict(gold_by_src['closure'])}, refuted {dict(gold_by_src['refuted'])}")
    # the LIVE panel's own verdicts (closure = confirmed True; refuted = False) against the same gold, and the trivial baseline
    live = {p["gid"]: (p["source"] == "closure") for p in pairs}
    sl = score(live, gold, source_of)
    n_nons = sum(1 for g in gold.values() if g["label"] != "S")
    lines.append("\nbaseline 'always refuse' agrees with gold on " + pct((n_nons, len(gold))) + "; the LIVE panel's own verdicts "
                 "(closure=True, refuted=False) agree on " + pct(sl["agree"]) + f", kappa {sl['kappa']:.2f}, precision of its "
                 "confirmations " + pct((sl["tp"], sl["tp"] + sl["fp"])) + ", gold-S among its refutals " + pct((sl["fn"], sl["fn"] + sl["tn"])))
    sure = {g: v for g, v in live.items() if not gold[g]["unsure"]}
    ss = score(sure, gold, source_of)
    lines.append(f"- same, labeller-SURE items only (n={ss['n']}): agree {pct(ss['agree'])}, kappa {ss['kappa']:.2f}, "
                 f"confirmations that are gold-S {pct((ss['tp'], ss['tp'] + ss['fp']))}, refutals that are gold-S {pct((ss['fn'], ss['fn'] + ss['tn']))}")
    for how in ("agreed", "tiebreak"):
        ids = [p["gid"] for p in pairs if p["source"] == "refuted" and p["panel"].get("how") == how]
        if ids:
            lines.append(f"- refuted by '{how}' ({len(ids)}): gold S = " + pct((sum(gold[i]["label"] == "S" for i in ids), len(ids))))
    for arm in ("gemma", "falcon", "panel"):
        lines.append(f"\n### arm: {arm}")
        lines.append("| variant | agree w/ gold | kappa | pass rate | false-keep | false-reject | closures still passed | refuted passed | no verdict | labeller-sure agree |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for v in VARIANTS:
            m = vm.get((arm, v))
            if not m:
                lines.append(f"| {NAMES[v]} | not run | | | | | | | | |")
                continue
            s = score(m, gold, source_of)
            lines.append(f"| {NAMES[v]} | {pct(s['agree'])} | {s['kappa']:.2f} | {pct(s['pass'])} | {pct(s['false_keep'])} | "
                         f"{pct(s['false_reject'])} | {pct(s['closure_pass'])} | {pct(s['refuted_pass'])} | {s['no_verdict']} | {pct(s['sure_agree'])} |")
        base = vm.get((arm, "V0"))
        if base:
            for v in VARIANTS[1:]:
                m = vm.get((arm, v))
                if m:
                    a, b, c, d = flips(base, m, gold)
                    lines.append(f"- paired {v} vs V0: pass->fail {a + b} ({a} correct, {b} wrong), fail->pass {c + d} ({c} correct, {d} wrong)")
    lines.append("\n### cost (mean seconds per ruling, mean prompt chars, rulings)")
    for (hub, v), (sec, ch, n) in sorted(cost(rows).items()):
        lines.append(f"- {hub} {NAMES[v]}: {sec:.1f} s, {ch:.0f} chars (~{ch / 4:.0f} tokens), n={n}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=None)
    a = ap.parse_args()
    text = report()
    print(text)
    if a.md:
        Path(a.md).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
