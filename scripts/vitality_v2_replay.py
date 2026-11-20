"""
J-3867 (F-4456): read-only replay comparing predict_vitality_v2 (as built), predict_vitality_v2b (sleep-aware) and
naive persistence on the logged two-axis vitality shadow. Scoring per scripts/vitality_causal_retest2.py: a step is
dropped if STALE (no sp row in (prev.ts, cur.ts]), over the regime gap (cur-prev > 1800s), or fire-pinned (the last
sp row at cur is a fire row). Reads COPIES (pass --shadow/--sp-log); writes nothing. Inputs to each predictor are
reconstructed as of prev.ts: the last 60 sp rows with ts <= prev.ts, the body energy the row itself logged
(vitality_v2.vit_body), and the row's own scale_S. Run: python scripts/vitality_v2_replay.py --shadow X --sp-log Y
"""
import argparse, bisect, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import homeostasis_causal as hc  # noqa: E402
assert str(Path(hc.__file__).resolve()).startswith(str(ROOT)), hc.__file__


def load(p):
    out = []
    for l in open(p, encoding="utf-8"):
        l = l.strip()
        if l:
            try: out.append(json.loads(l))
            except Exception: pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shadow", required=True); ap.add_argument("--sp-log", required=True)
    ap.add_argument("--regime-gap", type=float, default=1800.0)
    a = ap.parse_args()
    sh = sorted([r for r in load(a.shadow) if r.get("vitality_v2")], key=lambda r: r["ts"])
    sp = sorted([r for r in load(a.sp_log) if "P" in r and "ts" in r], key=lambda r: r["ts"])
    spt = [r["ts"] for r in sp]
    cols = {"naive": [], "v2": [], "v2b": [], "v2_logged": []}
    strata, agree, nrep = {}, 0, 0
    from core import world_clock as wc
    for i in range(1, len(sh)):
        p, c = sh[i - 1], sh[i]
        if c["ts"] - p["ts"] > a.regime_gap: continue
        lo, hi = bisect.bisect_right(spt, p["ts"]), bisect.bisect_right(spt, c["ts"])
        if hi <= lo: continue                                  # stale
        if sp[hi - 1].get("fire"): continue                    # fire-pinned
        actual = c["vitality_v2"]["vitality_v2"]; naive = p["vitality_v2"]["vitality_v2"]
        tail = sp[max(0, lo - 60):lo]
        if not tail: continue
        body = {"energy": p["vitality_v2"]["vit_body"]}
        sc = p["vitality_v2"].get("scale_S")
        pv2 = hc.predict_vitality_v2(p["ts"], scale=sc, sp_rows=tail, body=body)
        pv2b = hc.predict_vitality_v2b(p["ts"], scale=sc, sp_rows=tail, body=body)
        if pv2 is None or pv2b is None: continue
        lg = p.get("predicted_v2")
        if lg:
            nrep += 1; agree += abs(lg["vitality_v2"] - pv2["vitality_v2"]) < 0.02
            cols["v2_logged"].append(abs(actual - lg["vitality_v2"]))
        sw = (wc.daylight(c["ts"]) == "night") != (wc.daylight(p["ts"]) == "night")
        e = {"naive": abs(actual - naive), "v2": abs(actual - pv2["vitality_v2"]), "v2b": abs(actual - pv2b["vitality_v2"])}
        for k, v in e.items(): cols[k].append(v)
        key = ("switch" if sw else "nonswitch", pv2b["state"])
        s = strata.setdefault(key, {"n": 0, "naive": 0, "v2": 0, "v2b": 0, "w": 0, "l": 0})
        s["n"] += 1
        for k in ("naive", "v2", "v2b"): s[k] += e[k]
        s["w"] += e["v2b"] < e["naive"] - 1e-9; s["l"] += e["v2b"] > e["naive"] + 1e-9
    n = len(cols["naive"])
    print(f"scored steps: {n}; replay v2 vs logged predicted_v2 agree (<0.02): {agree}/{nrep}")
    for k in ("naive", "v2", "v2b"): print(f"  pooled MAE {k:5s} {sum(cols[k]) / n:.5f}")
    if cols["v2_logged"]: print(f"  pooled MAE v2 (as logged) {sum(cols['v2_logged'])/len(cols['v2_logged']):.5f}")
    w = sum(1 for x, y in zip(cols["v2b"], cols["naive"]) if x < y - 1e-9); l = sum(1 for x, y in zip(cols["v2b"], cols["naive"]) if x > y + 1e-9)
    print(f"  v2b vs naive: wins {w} losses {l}")
    for k, s in sorted(strata.items()):
        print(f"  {k}: n={s['n']} naive={s['naive']/s['n']:.4f} v2={s['v2']/s['n']:.4f} v2b={s['v2b']/s['n']:.4f} v2b W{s['w']}/L{s['l']} vs naive")


if __name__ == "__main__":
    main()
