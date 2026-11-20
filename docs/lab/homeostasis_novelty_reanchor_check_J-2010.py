"""J-2010: offline check of the re-anchored predict_novelty (core/homeostasis_causal.py).
Part 1 (unit): imports core from THIS tree (asserted), monkeypatches _load_climate_snapshot with synthetic
snapshots -- no live store is read or written -- and checks predict_novelty == clip01(nh + 0.25*(proj-value_now)),
predict_novelty_level == the old 0.5*quietness+0.25*proj formula, and the fallback/None paths.
Part 2 (replay): read-only replay over data/homeostasis_shadow.jsonl post-F-0810 rows. The function's inputs
(novelty_now, value_now, projected value) are exactly the previous row's logged variables.novelty,
1-variables.coherence and 1-predicted_causal.coherence (unclipped rows), so the replay applies the same
arithmetic; prints MAE naive / old level / new, per-step W/L, pooled event-aligned folds.
"""
import json, math, sys
from pathlib import Path
TREE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TREE))
import core                                   # import core BEFORE anything else
assert str(Path(core.__file__).resolve()).startswith(str(TREE)), core.__file__
from core import homeostasis_causal as hc
from core import world_clock as wc
assert str(Path(hc.__file__).resolve()).startswith(str(TREE))

def snap(nh, value, sa=0.3, explore=0.1):
    return {"field": {"novelty_hunger": nh, "shadow_activation": sa, "world_model_strain": 0.04,
                      "completion_tension": 0.5, "integration_drive": 0.5},
            "dissonance": {"value": value, "explore_value": explore, "last_ignition_ts": 0.0, "refractory_secs": 300.0},
            "updated": 1.0e9}
hc._explore_pull = lambda: 0.0

def _level(snap_, proj_):   # J-2125: predict_novelty_level was dropped; old formula inlined here
    return max(0.0, min(1.0, 0.5 * (1 - snap_['field'].get('shadow_activation', 0.0)) + 0.5 * (proj_ / hc._DISS_MAX)))
n_ok = 0
for nh, v in [(0.29, 0.40), (0.55, 0.10), (0.05, 0.95), (0.9, 0.2)]:
    s = snap(nh, v); hc._load_climate_snapshot = lambda s=s: s
    proj = hc._project_dissonance(s["field"], s["dissonance"], s["updated"], s["updated"] + 600.0)
    exp = max(0.0, min(1.0, nh + 0.25 * (proj - v)))
    got = hc.predict_novelty()
    old = _level(s, proj)
    exp_old = max(0.0, min(1.0, 0.5 * (1 - 0.3) + 0.5 * (proj / hc._DISS_MAX)))
    assert abs(got - exp) < 1e-12 and abs(old - exp_old) < 1e-12, (nh, v, got, exp, old, exp_old)
    n_ok += 1
s = snap(0.3, 0.4); del s["field"]["novelty_hunger"]; hc._load_climate_snapshot = lambda: s
_p = hc._project_dissonance(s['field'], s['dissonance'], s['updated'], s['updated'] + 600.0)
assert abs(hc.predict_novelty() - _level(s, _p)) < 1e-12
hc._load_climate_snapshot = lambda: None
assert hc.predict_novelty() is None
print(f"UNIT OK: {n_ok} synthetic snapshots + fallback + None path; tree={TREE}")

rows = [json.loads(l) for l in (Path(r"C:\Nascence\data\homeostasis_shadow.jsonl")).open(encoding="utf-8") if l.strip()]
rows = [r for r in rows if r.get("ts", 0) >= 1788517496.0 and isinstance(r.get("predicted_causal"), dict)]
rows.sort(key=lambda r: r["ts"])
regs = []; cur = [rows[0]]
for r in rows[1:]:
    if r["ts"] - cur[-1]["ts"] > 1800: regs.append(cur); cur = [r]
    else: cur.append(r)
regs.append(cur)
steps = []
for gi, g in enumerate(regs):
    for p, c in zip(g, g[1:]):
        vp, vc, pc = p["variables"], c["variables"], p["predicted_causal"]
        if not all("novelty" in d for d in (vp, vc, pc)): continue
        if not (0 < vp["coherence"] < 1 and 0 < pc["coherence"] < 1): new = vp["novelty"]
        else: new = max(0.0, min(1.0, vp["novelty"] + hc._NOVELTY_PER_DISSONANCE * ((1 - pc["coherence"]) - (1 - vp["coherence"]))))
        steps.append({"g": gi, "sw": (wc.daylight(p["ts"]) == "night") != (wc.daylight(c["ts"]) == "night"),
                      "en": abs(vc["novelty"] - vp["novelty"]), "ec": abs(vc["novelty"] - pc["novelty"]), "ex": abs(vc["novelty"] - new)})
m = lambda k, ss=steps: sum(s[k] for s in ss) / len(ss)
w = sum(s["en"] - s["ex"] > 1e-12 for s in steps); l = sum(s["ex"] - s["en"] > 1e-12 for s in steps)
print(f"REPLAY steps={len(steps)} MAE naive={m('en'):.4f} old(level, as logged)={m('ec'):.4f} new(re-anchored)={m('ex'):.4f}; new beats naive {w} / loses {l}")
sw = [s for s in steps if s["sw"]]
print(f"switch rows {len(sw)}: MAE naive={m('en', sw):.4f} new={m('ex', sw):.4f}")
idx = [i for i, s in enumerate(steps) if s["sw"]]; k = len(idx); nf = 6
b = [0] + [(idx[(j * k) // nf - 1] + idx[(j * k) // nf]) // 2 + 1 for j in range(1, nf)] + [len(steps)]
f = []
for j in range(nf):
    seg = steps[b[j]:b[j + 1]]; f.append("NEW" if m("ex", seg) < m("en", seg) else "naive")
print("event-aligned folds:", f, "->", f.count("NEW"), "/6")
neg = [gi for gi in range(len(regs)) if sum(s["en"] - s["ex"] > 1e-12 for s in steps if s["g"] == gi) < sum(s["ex"] - s["en"] > 1e-12 for s in steps if s["g"] == gi)]
print("regimes where new loses:", neg, "of", len(regs))
