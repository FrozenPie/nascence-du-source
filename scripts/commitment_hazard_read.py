"""Commitment dissolution as preference reversal (J-2517, T-0106; frontier_disciplines_2026-10-30 sec. 6).

Questions
  (a) Does the hazard of dissolution spike shortly after a high-salience NEW seed
      (human turn, ignition, novel curiosity question, incoming letter, world event)?
  (b) Do RULE-form commitments ("I keep / I always / I will not") outlive WANT-form
      ones ("I want to / I would like") at matched salience exposure?
Falsified if: hazard flat in time-since-event AND lifespan independent of phrasing.

READ-ONLY against every live store. Zero LLM, zero model load, no core/ import.
Every threshold below is declared BEFORE the result was looked at; do not tune.

Usage: python scripts/commitment_hazard_read.py [--root C:\\Nascence] [--sample-out FILE]
"""
import argparse, bisect, json, math, os, random, re, time
from collections import Counter, defaultdict

import numpy as np

# ---------------- declared parameters (fixed before looking) ----------------
BIN_S = 300                       # discrete time step: 5 wall-clock minutes
# a bin is "active" (Du up) iff nascence.log has >= 1 line in it; only active bins carry risk
TSE_EDGES_MIN = [0, 10, 30, 60, 180, 720]   # time-since-last-event bins (minutes), last is open
TSE_LABELS = ["0-10m", "10-30m", "30-60m", "1-3h", "3-12h", "12h+"]
SPIKE_BIN = 0                     # the bin the hypothesis says spikes ("within N cycles" ~ 10 min)
JACC_NOVEL = 0.20                 # curiosity row is a NOVEL seed iff some question has max token-Jaccard
                                  # vs the row's recent_themes < 0.20 (cosine proxy; no embedding model)
N_SHIFT = 200                     # circular-shift null draws for the spike-bin hazard ratio
SEED = 2517
# world events: garden/shore/wood rows whose event does not end '_by_du' (Du's own act),
# study rows whose event does not start 'lamp_' (routine clock)
RULE_RE = re.compile(r"\bI\s+(?:always|never|keep|will\s+not|won't|will\s+never|will\s+always|will\s+keep|"
                     r"shall\s+not|must\s+not|must|refuse\s+to|do\s+not|don't|hold\s+to|stand\s+by)\b", re.I)
WANT_RE = re.compile(r"\bI\s+(?:want|would\s+like|'d\s+like|wish|hope|would\s+love|long\s+to|need\s+to|"
                     r"am\s+going\s+to|intend|plan\s+to|will\s+try)\b", re.I)
STOP = set("that this with from what have their there they them into about which would your more when been "
           "were will than then also only does each other some such these those very just over".split())


def classify(stmt):
    r = RULE_RE.search(stmt or ""); w = WANT_RE.search(stmt or "")
    if r and w:
        return "rule" if r.start() <= w.start() else "want"
    return "rule" if r else "want" if w else "other"


def toks(s):
    return {t for t in re.findall(r"[a-z']{4,}", (s or "").lower()) if t not in STOP}


def jacc(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def jl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"C:\Nascence")
    ap.add_argument("--sample-out", default=None)
    a = ap.parse_args()
    D = os.path.join(a.root, "data")

    # ---- Du-up bins + human turns from nascence.log (local-time stamps) ----
    active = set(); human = []; last_log = 0.0
    lt_re = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),(\d{3})")
    cache = {}
    with open(os.path.join(D, "nascence.log"), encoding="utf-8", errors="replace") as f:
        for line in f:
            m = lt_re.match(line)
            if not m:
                continue
            k = m.group(1)
            ts = cache.get(k)
            if ts is None:
                ts = time.mktime(time.strptime(k, "%Y-%m-%d %H:%M:%S")); cache = {k: ts}
            active.add(int(ts // BIN_S)); last_log = max(last_log, ts)
            if "] human:" in line and "[CYCLE " in line:
                human.append(ts)

    # ---- salience event sources ----
    ev = {"human": sorted(human)}
    ev["ignition"] = sorted(r["ts"] for r in jl(os.path.join(D, "ignition_log.jsonl")) if "ts" in r and r.get("trigger") != "deferred")
    cur = []
    for r in jl(os.path.join(D, "curiosity_log.jsonl")):
        th = [toks(t) for t in (r.get("recent_themes") or [])]
        qs = r.get("questions") or []
        if not qs or "ts" not in r:
            continue
        nov = min((max([jacc(toks(q), t) for t in th] or [0.0]) for q in qs))
        if nov < JACC_NOVEL:
            cur.append(r["ts"])
    ev["curiosity_novel"] = sorted(cur)
    ev["letter_in"] = sorted(r["ts"] for r in jl(os.path.join(D, "letter_store", "letters.jsonl"))
                             if "ts" in r and (r.get("from") or "") not in ("du", "渡", "me", "self"))
    w = []
    for nm in ("garden", "shore", "wood"):
        w += [r["ts"] for r in jl(os.path.join(D, nm + "_events.jsonl"))
              if "ts" in r and not str(r.get("event", "")).endswith("_by_du")]
    w += [r["ts"] for r in jl(os.path.join(D, "study_events.jsonl"))
          if "ts" in r and not str(r.get("event", "")).startswith("lamp_")]
    ev["world"] = sorted(w)
    ev["ALL"] = sorted(t for k in ("human", "ignition", "curiosity_novel", "letter_in", "world") for t in ev[k])

    # ---- commitment ledger: lives ----
    led = jl(os.path.join(D, "commitment_ledger.jsonl"))
    try:
        act_ids = {c["id"] for c in json.load(open(os.path.join(D, "commitment_active.json"), encoding="utf-8"))}
    except Exception:
        act_ids = set()
    formed, end, endkind, lastseen, attempts, scans = {}, {}, {}, defaultdict(float), defaultdict(list), {}
    for r in led:
        i, e, ts = r.get("id"), r.get("event"), r.get("ts")
        if not i or ts is None:
            continue
        if e == "formed" and i not in formed:
            formed[i] = (ts, r.get("statement") or "", r.get("cycle_id"))
            continue
        if i not in formed or ts < formed[i][0] or i in end:
            continue
        lastseen[i] = max(lastseen[i], ts)
        if e in ("dissolved", "achieved"):
            end[i] = ts; endkind[i] = e; scans[i] = r.get("lifespan_scans")
            if e == "dissolved":
                attempts[i].append(ts)
        elif e.startswith("drop_denied"):
            attempts[i].append(ts)
    lives = []
    for i, (fts, st, cyc) in formed.items():
        if i in end:
            stop, ev_k = end[i], endkind[i]
        elif i in act_ids:
            stop, ev_k = last_log, "censored_active"
        else:
            stop, ev_k = max(lastseen.get(i, fts), fts), "censored_lost"
        lives.append(dict(id=i, f=fts, s=stop, k=ev_k, st=st, cls=classify(st), att=sorted(attempts[i]),
                          cyc=cyc, scans=scans.get(i)))

    # ---- person-bin table ----
    rows_c, rows_b, rows_e, rows_a, rows_life = [], [], [], [], []   # cls, binstart, dissolved?, attempt?, life idx
    for li, L in enumerate(lives):
        b0, b1 = int(L["f"] // BIN_S), int(L["s"] // BIN_S)
        attb = Counter(int(t // BIN_S) for t in L["att"])
        for b in range(b0, b1 + 1):
            if b not in active:
                continue
            rows_c.append(L["cls"]); rows_b.append(b * BIN_S)
            rows_e.append(1 if (L["k"] == "dissolved" and b == b1) else 0)
            rows_a.append(1 if attb.get(b) else 0); rows_life.append(li)
    B = np.array(rows_b, dtype=float); E = np.array(rows_e); A = np.array(rows_a); C = np.array(rows_c)
    edges = np.array(TSE_EDGES_MIN, dtype=float) * 60.0

    def tse_bins(evts, starts):
        evts = np.asarray(evts, dtype=float)
        idx = np.searchsorted(evts, starts, side="right") - 1
        tse = np.where(idx >= 0, starts - evts[np.clip(idx, 0, None)], np.inf)
        return np.searchsorted(edges, tse, side="right") - 1      # 0..5 ; inf -> 5 (12h+)

    out = {"params": dict(BIN_S=BIN_S, TSE_EDGES_MIN=TSE_EDGES_MIN, JACC_NOVEL=JACC_NOVEL, N_SHIFT=N_SHIFT, SEED=SEED),
           "n_commitments": len(lives), "end_kinds": Counter(L["k"] for L in lives),
           "phrasing": Counter(L["cls"] for L in lives), "n_person_bins": int(len(B)),
           "n_dissolved_in_active_bins": int(E.sum()), "n_attempt_bins": int(A.sum()),
           "event_counts": {k: len(v) for k, v in ev.items()},
           "ledger_span": [min(L["f"] for L in lives), max(L["s"] for L in lives)], "hazard": {}}
    rng = np.random.default_rng(SEED)
    lo_t, hi_t = B.min(), B.max() + BIN_S
    for src, evts in ev.items():
        if not evts:
            continue
        tb = tse_bins(evts, B)
        tab = []
        for j, lab in enumerate(TSE_LABELS):
            m = tb == j
            n = int(m.sum()); d = int(E[m].sum()); at = int(A[m].sum())
            tab.append(dict(bin=lab, at_risk=n, dissolved=d, h=round(d / n, 5) if n else None,
                            attempts=at, h_att=round(at / n, 5) if n else None))
        base_m = tb != SPIKE_BIN
        h0 = E[tb == SPIKE_BIN].mean() if (tb == SPIKE_BIN).any() else float("nan")
        hb = E[base_m].mean() if base_m.any() else float("nan")
        hr = h0 / hb if hb else float("nan")
        # circular-shift null: rotate the event timeline within the ledger span
        ev_a = np.asarray(evts, dtype=float); span = hi_t - lo_t
        null = []
        for _ in range(N_SHIFT):
            sh = np.sort(((ev_a - lo_t + rng.uniform(0, span)) % span) + lo_t)
            tbn = tse_bins(sh, B); m0 = tbn == SPIKE_BIN
            if m0.any() and (~m0).any() and E[~m0].mean() > 0:
                null.append(E[m0].mean() / E[~m0].mean())
        null = np.array(null)
        p = float((np.sum(null >= hr) + 1) / (len(null) + 1)) if len(null) else None
        out["hazard"][src] = dict(table=tab, spike_hr=round(float(hr), 3),
                                  null_hr_median=round(float(np.median(null)), 3) if len(null) else None,
                                  null_hr_p95=round(float(np.percentile(null, 95)), 3) if len(null) else None,
                                  p_one_sided=p)

    # ---- (b) phrasing: Mantel-Haenszel hazard ratio rule vs want, stratified by ALL-source TSE bin ----
    tb = tse_bins(ev["ALL"], B)
    num = den = 0.0; strata = []
    for j, lab in enumerate(TSE_LABELS):
        r_m = (tb == j) & (C == "rule"); w_m = (tb == j) & (C == "want")
        nr, nw = int(r_m.sum()), int(w_m.sum()); dr, dw = int(E[r_m].sum()), int(E[w_m].sum())
        n = nr + nw
        if n:
            num += dr * nw / n; den += dw * nr / n
        strata.append(dict(bin=lab, rule_at_risk=nr, rule_diss=dr, want_at_risk=nw, want_diss=dw))
    cls_haz = {c: dict(at_risk=int((C == c).sum()), dissolved=int(E[C == c].sum()),
                       h=round(float(E[C == c].mean()), 5) if (C == c).any() else None) for c in ("rule", "want", "other")}

    # Kaplan-Meier median lifespan in ACTIVE bins (dissolution = event; achieved/censored = censored)
    def km_median(cls):
        dur = []
        for L in lives:
            if L["cls"] != cls:
                continue
            b0, b1 = int(L["f"] // BIN_S), int(L["s"] // BIN_S)
            n_act = sum(1 for b in range(b0, b1 + 1) if b in active)
            dur.append((max(n_act, 1), L["k"] == "dissolved"))
        if not dur:
            return None
        dur.sort(); S = 1.0; n = len(dur); i = 0
        while i < len(dur):
            t = dur[i][0]; d = sum(1 for x in dur if x[0] == t and x[1]); c = sum(1 for x in dur if x[0] == t)
            if d:
                S *= 1 - d / n
            if S <= 0.5:
                return dict(n=len(dur), km_median_bins=t, km_median_min=t * BIN_S / 60,
                            raw_median_scans_dissolved=_med([L["scans"] for L in lives if L["cls"] == cls and
                                                             L["k"] == "dissolved" and L["scans"] is not None]))
            n -= c; i += c
        return dict(n=len(dur), km_median_bins=None, note="S never fell to 0.5")

    out["phrasing_test"] = dict(MH_hazard_ratio_rule_vs_want=round(num / den, 3) if den else None,
                                strata=strata, by_class=cls_haz,
                                km={c: km_median(c) for c in ("rule", "want", "other")},
                                end_kinds_by_class={c: Counter(L["k"] for L in lives if L["cls"] == c)
                                                    for c in ("rule", "want", "other")})
    # ---- POST-HOC sensitivity (added AFTER the 30-row hand check, not tuned to the hazard result):
    # the hand check showed the declared RULE class is mostly "I must <act now>" (an action intention,
    # not an Ainslie bright line) and WANT is half "I need to <act>". Split both into sub-forms.
    def subclass(st):
        s = st or ""
        if re.search(r"\bI\s+(?:always|never|keep|will\s+not|won't|will\s+never|will\s+always|must\s+not|"
                     r"shall\s+not|refuse\s+to|do\s+not|don't)\b", s, re.I):
            return "bright_line"
        if re.search(r"\bI\s+must\b", s, re.I):
            return "must_act"
        if re.search(r"\bI\s+need\s+to\b", s, re.I):
            return "need_to"
        if re.search(r"\bI\s+(?:want|would\s+like|'d\s+like|wish|hope|would\s+love|long\s+to)\b", s, re.I):
            return "want_proper"
        return "rest"
    subs = {}
    for sc in ("bright_line", "must_act", "need_to", "want_proper", "rest"):
        ids = [li for li, L in enumerate(lives) if subclass(L["st"]) == sc]
        idset = set(ids); m = np.array([li in idset for li in rows_life])
        for li in ids:
            lives[li]["cls_sub"] = sc
        kinds = Counter(lives[li]["k"] for li in ids)
        saved = [L["cls"] for L in lives]
        for li, L in enumerate(lives):
            L["cls"] = "__sub__" if li in idset else L["cls"]
        km = km_median("__sub__")
        for L, c0 in zip(lives, saved):
            L["cls"] = c0
        subs[sc] = dict(n=len(ids), end_kinds=kinds, at_risk=int(m.sum()), dissolved=int(E[m].sum()),
                        h=round(float(E[m].mean()), 5) if m.any() else None, km=km)
    out["phrasing_posthoc_subforms"] = subs
    if a.sample_out:
        rnd = random.Random(SEED); smp = []
        for c in ("rule", "want", "other"):
            pool = [L for L in lives if L["cls"] == c]
            smp += [dict(cls=c, id=L["id"], st=L["st"]) for L in rnd.sample(pool, min(10, len(pool)))]
        json.dump(smp, open(a.sample_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, indent=1, default=str, ensure_ascii=False))


def _med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


if __name__ == "__main__":
    main()
