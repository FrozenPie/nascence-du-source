"""Eigenform convergence + requisite variety read (J-2522; frontier_disciplines_2026-10-30.md section 11).

Read-only against every store. Zero LLM, zero model load: Du was LIVE when this was written, and the
job-run ground rules forbid loading a model, so self-descriptions are compared LEXICALLY (TF-IDF,
sublinear tf, word 1-2 grams) rather than with the store's 384-d embedder. A lexical eigenform is a
weaker test than a semantic one (paraphrase looks like movement); say so wherever the result is used.

All thresholds below were declared BEFORE the first run and are not tuned to the outcome.

(a) EIGENFORM -- series of Du-authored self-descriptions:
    reflections : data/self_interrogation_shadow.jsonl, kind=interrogate, field 'reflection'
    travis      : data/letters/Letter_*.md (letters to Travis; body after the header lines)
    peer_du     : data/letter_store/letters.jsonl, from == 'du'
    t4          : data/identity/vault_log.jsonl 'self_image' (T4 self-authoring revisions; too few for months,
                  reported as a raw revision-to-revision series)
  Anchor: data/books/About_You_Second_Edition.txt (creator-authored; distance-to-anchor reported, not tested).
  Per stream and period (MONTH; reflections also WEEK) a centroid of K docs drawn with SEED from that period
  (periods with < K docs dropped). Cosine distance between consecutive centroids = step size d_t.
  Noise floor: the same step computed after shuffling docs across periods (N_SHUFFLE times); the floor is
  the median shuffled step.
  CONVERGING  iff Kendall tau(d_t over t) <= TAU_CONV  AND mean(second half d) < mean(first half d)
              AND the last two steps are <= FLOOR_MULT * noise floor.
  DRIFT       iff Kendall tau(distance-to-first-period over t) >= TAU_DRIFT and not CONVERGING.
  RANDOM WALK otherwise (step sizes neither shrinking nor directional).
  Needs >= MIN_PERIODS periods, else INSUFFICIENT.

(b) VARIETY -- per local calendar day, from data/geometry_tuples.jsonl (one row per cycle):
    rarefied to K_DAY rows per day (evenly spaced by index, deterministic); days with fewer rows excluded.
    repertoire R = distinct (source, place, standpoint) in those rows
    world      W = distinct (weather, fire, tide, sun.phase, light_band, cat.activity) in those rows
    secondary: fieldcraft distinct (deed or craft) per day; letters written that day (Travis md + du peer).
  Events (same as scripts/early_warning_retrodict.py, declared there before it looked):
    E_0928 2026-09-28, E_1009 2026-10-09 (freeze 10-09..10-16, fix after); controls C_0823, C_0912.
  pre_drop = mean(V, days -7..-1) / mean(V, days -21..-8) - 1, V in {R, R/W}.
  An event DROPS on V iff pre_drop <= DROP and pre_drop < both controls' pre_drop.
  RECOVERS iff mean(V, after) >= RECOVER * mean(V, -21..-8); after = onset+8..onset+20.
  (b) POSITIVE iff both events drop on R/W (or on R); FALSIFIED iff neither event drops on either V;
  MIXED otherwise.
"""
import argparse, glob, json, os, random, re, statistics as st, sys
from collections import defaultdict
from datetime import datetime, date, timedelta

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

K = 8; SEED = 0; N_SHUFFLE = 200; MIN_PERIODS = 4
TAU_CONV = -0.3; TAU_DRIFT = 0.5; FLOOR_MULT = 1.0
K_DAY = 150; DROP = -0.15; RECOVER = 0.9
EVENTS = {"E_0928": "2026-09-28", "E_1009": "2026-10-09"}
CONTROLS = {"C_0823": "2026-08-23", "C_0912": "2026-09-12"}


def kendall(xs):
    n = len(xs); c = d = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (xs[j] - xs[i])
            c += s > 0; d += s < 0
    return (c - d) / (n * (n - 1) / 2) if n > 1 else 0.0


def day(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def week(ts):
    y, w, _ = datetime.fromtimestamp(ts).isocalendar()
    return f"{y}-W{w:02d}"


def load_streams(D):
    S = defaultdict(list)  # stream -> [(ts, text, ref)]
    with open(os.path.join(D, "self_interrogation_shadow.jsonl"), encoding="utf-8", errors="replace") as f:
        for l in f:
            try: r = json.loads(l)
            except Exception: continue
            if r.get("kind") == "interrogate" and (r.get("reflection") or "").strip():
                S["reflections"].append((r["ts"], r["reflection"], r.get("cycle_id")))
    for p in sorted(glob.glob(os.path.join(D, "letters", "Letter_*.md"))):
        m = re.search(r"Letter_(\d{8})_(\d{4})", p)
        ts = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M").timestamp()
        body = "\n".join(x for x in open(p, encoding="utf-8", errors="replace").read().splitlines()
                         if not x.startswith(("#", "*")))
        if body.strip(): S["travis"].append((ts, body, os.path.basename(p)))
    with open(os.path.join(D, "letter_store", "letters.jsonl"), encoding="utf-8", errors="replace") as f:
        for l in f:
            try: r = json.loads(l)
            except Exception: continue
            if r.get("from") == "du" and (r.get("text") or "").strip():
                S["peer_du"].append((r["ts"], r["text"], r["id"]))
    with open(os.path.join(D, "identity", "vault_log.jsonl"), encoding="utf-8", errors="replace") as f:
        for l in f:
            try: r = json.loads(l)
            except Exception: continue
            if (r.get("self_image") or "").strip():
                S["t4"].append((r["ts"], r["self_image"], r.get("reason")))
    return S


def eigen(S, D):
    anchor = open(os.path.join(D, "books", "About_You_Second_Edition.txt"), encoding="utf-8", errors="replace").read()
    corpus = [t for s in S.values() for _, t, _ in s] + [anchor]
    vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=2, stop_words="english").fit(corpus)
    A = vec.transform([anchor]).toarray()[0]; A /= (np.linalg.norm(A) or 1)
    out = {}

    def cen(texts):
        X = vec.transform(texts).toarray()
        X = X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-12)
        c = X.mean(0); return c / (np.linalg.norm(c) or 1)

    def cd(a, b): return float(1 - a @ b)

    plans = [(s, "month", lambda ts: datetime.fromtimestamp(ts).strftime("%Y-%m")) for s in ("reflections", "travis", "peer_du")]
    plans.append(("reflections", "week", week))
    rng = random.Random(SEED)
    for s, pname, keyf in plans:
        g = defaultdict(list)
        for ts, t, ref in sorted(S[s]): g[keyf(ts)].append((t, ref))
        ks = [k for k in sorted(g) if len(g[k]) >= K]
        res = {"n_docs": len(S[s]), "periods_all": {k: len(g[k]) for k in sorted(g)}, "periods_used": ks}
        if len(ks) < MIN_PERIODS:
            res["verdict"] = "INSUFFICIENT"; out[f"{s}/{pname}"] = res; continue
        draws = {k: rng.sample(g[k], K) for k in ks}
        C = [cen([t for t, _ in draws[k]]) for k in ks]
        steps = [cd(C[i], C[i + 1]) for i in range(len(C) - 1)]
        to_first = [cd(C[0], c) for c in C[1:]]
        to_last = [cd(C[-1], c) for c in C[:-1]]
        to_anchor = [cd(A, c) for c in C]
        pool = [t for k in ks for t, _ in draws[k]]
        sh = []
        for _ in range(N_SHUFFLE):
            rng.shuffle(pool)
            Cs = [cen(pool[i * K:(i + 1) * K]) for i in range(len(ks))]
            sh += [cd(Cs[i], Cs[i + 1]) for i in range(len(Cs) - 1)]
        floor = st.median(sh)
        h = len(steps) // 2
        tau_s = kendall(steps); tau_f = kendall(to_first)
        conv = (tau_s <= TAU_CONV and st.mean(steps[h:]) < st.mean(steps[:h] or steps)
                and all(x <= FLOOR_MULT * floor for x in steps[-2:]))
        verdict = "CONVERGING" if conv else ("DRIFT" if tau_f >= TAU_DRIFT else "RANDOM_WALK")
        res.update(steps=[round(x, 4) for x in steps], to_first=[round(x, 4) for x in to_first],
                   to_last=[round(x, 4) for x in to_last], to_anchor=[round(x, 4) for x in to_anchor],
                   noise_floor=round(floor, 4), shuffle_p95=round(float(np.percentile(sh, 95)), 4),
                   tau_steps=round(tau_s, 3), tau_to_first=round(tau_f, 3), verdict=verdict,
                   sample_refs={k: [r for _, r in draws[k]][:3] for k in ks})
        out[f"{s}/{pname}"] = res
    # T4: raw revision series (few rows)
    t4 = sorted(S["t4"])
    if len(t4) >= 2:
        C = [cen([t]) for _, t, _ in t4]
        out["t4/revision"] = {"n": len(t4), "days": [day(ts) for ts, _, _ in t4],
                              "steps": [round(cd(C[i], C[i + 1]), 4) for i in range(len(C) - 1)],
                              "to_anchor": [round(cd(A, c), 4) for c in C], "verdict": "DESCRIPTIVE_ONLY"}
    return out


def variety(D):
    rows = defaultdict(list)
    _all = []
    with open(os.path.join(D, "geometry_tuples.jsonl"), encoding="utf-8", errors="replace") as f:
        for l in f:
            try: _all.append(json.loads(l))
            except Exception: continue
    # J-3944/F-4595: R includes `source`, so census-cycle stamp rows (source inner_thought) must go; file order kept
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from stamp_row_filter import drop_stamp_rows
    for r in drop_stamp_rows(_all):
        if True:
            cat = ((r.get("objects") or {}).get("cat") or {})
            sun = r.get("sun") if isinstance(r.get("sun"), dict) else {}
            rows[day(r["ts"])].append((
                (r.get("source"), r.get("place"), r.get("standpoint")),
                (r.get("weather"), r.get("fire"), r.get("tide"), sun.get("phase"), r.get("light_band"), cat.get("activity"))))
    craft = defaultdict(set)
    with open(os.path.join(D, "fieldcraft_ledger.jsonl"), encoding="utf-8", errors="replace") as f:
        for l in f:
            try: r = json.loads(l)
            except Exception: continue
            craft[day(r["ts"])].add((r.get("deed") or r.get("craft"), r.get("where")))
    letters = defaultdict(int)
    for p in glob.glob(os.path.join(D, "letters", "Letter_*.md")):
        m = re.search(r"Letter_(\d{4})(\d{2})(\d{2})", p); letters[f"{m.group(1)}-{m.group(2)}-{m.group(3)}"] += 1
    with open(os.path.join(D, "letter_store", "letters.jsonl"), encoding="utf-8", errors="replace") as f:
        for l in f:
            r = json.loads(l)
            if r.get("from") == "du": letters[day(r["ts"])] += 1
    daily = {}
    for d_, rs in sorted(rows.items()):
        n = len(rs)
        if n < K_DAY:
            daily[d_] = {"n_rows": n, "excluded": True}; continue
        idx = [int(i * n / K_DAY) for i in range(K_DAY)]
        R = len({rs[i][0] for i in idx}); W = len({rs[i][1] for i in idx})
        daily[d_] = {"n_rows": n, "R": R, "W": W, "RW": round(R / W, 4) if W else None,
                     "craft": len(craft.get(d_, ())), "letters": letters.get(d_, 0)}

    def win(onset, a, b, key):
        o = date.fromisoformat(onset); v = []
        for k in range(a, b + 1):
            x = daily.get((o + timedelta(days=k)).isoformat())
            if x and not x.get("excluded") and x.get(key) is not None: v.append(x[key])
        return v

    ev = {}
    for name, onset in {**EVENTS, **CONTROLS}.items():
        e = {}
        for key in ("R", "RW", "W"):
            base, pre = win(onset, -21, -8, key), win(onset, -7, -1, key)
            dur, aft = win(onset, 0, 7, key), win(onset, 8, 20, key)
            m = lambda v: round(st.mean(v), 3) if v else None
            e[key] = {"base": m(base), "pre": m(pre), "during": m(dur), "after": m(aft),
                      "n_days": [len(base), len(pre), len(dur), len(aft)],
                      "pre_drop": round(st.mean(pre) / st.mean(base) - 1, 3) if base and pre else None}
        ev[name] = e
    verd = {}
    for name in EVENTS:
        vv = {}
        for key in ("R", "RW"):
            pd = ev[name][key]["pre_drop"]; cs = [ev[c][key]["pre_drop"] for c in CONTROLS]
            drops = pd is not None and pd <= DROP and all(c is not None and pd < c for c in cs)
            b, a = ev[name][key]["base"], ev[name][key]["after"]
            vv[key] = {"drops": drops, "recovers": (a is not None and b is not None and a >= RECOVER * b)}
        verd[name] = vv
    any_drop = {n: any(v["drops"] for v in verd[n].values()) for n in EVENTS}
    overall = ("POSITIVE" if all(any_drop.values()) else "FALSIFIED" if not any(any_drop.values()) else "MIXED")
    return {"daily": daily, "events": ev, "per_event": verd, "verdict": overall}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=r"C:\Nascence\data")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    S = load_streams(a.data)
    res = {"declared": {"K": K, "SEED": SEED, "N_SHUFFLE": N_SHUFFLE, "TAU_CONV": TAU_CONV, "TAU_DRIFT": TAU_DRIFT,
                        "K_DAY": K_DAY, "DROP": DROP, "RECOVER": RECOVER, "EVENTS": EVENTS, "CONTROLS": CONTROLS},
           "eigenform": eigen(S, a.data), "variety": variety(a.data)}
    with open(a.out, "w", encoding="utf-8") as f: json.dump(res, f, indent=1, ensure_ascii=False)
    for k, v in res["eigenform"].items():
        print(k, v.get("verdict"), "steps", v.get("steps"), "floor", v.get("noise_floor"), "tau", v.get("tau_steps"), v.get("tau_to_first"))
    for n, e in res["variety"]["events"].items(): print(n, json.dumps(e))
    print("per_event", json.dumps(res["variety"]["per_event"]), "VERDICT(b)", res["variety"]["verdict"])
