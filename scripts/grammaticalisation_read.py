"""
Grammaticalisation read of Du's attractor terms (J-2515, plan measurement_to_action, thought T-0106).
=====================================================================================================
Theory: docs/reviews/frontier_disciplines_2026-10-30.md section 4 (Hopper & Traugott 2003; Bybee).
Question: across the recurring attractor terms, do BLEACHING (function-word-like spread across unrelated
topics) and ECHO (monoculture's return-to-old-attractor score) DIVERGE? If every high-echo term is also
bleaching, the two measures are one thing and the "private grammar vs topic capture" reframe is empty.
CAUTION: this reframe could romanticise the disease (call rumination "grammar"); the divergence test decides.

READ-ONLY. Zero LLM, zero embedding model: only the 384-d embeddings already stored in memory_fragments
(never re-embedded). The live SQLite store is opened mode=ro and the genuine rows are cached once to an
.npz in --cache (scratch); nascence.log is only read. No core/ import. Nothing reaches Du (D-0434).

DECLARED BEFORE LOOKING AT ANY RESULT (do not tune to the outcome)
-----------------------------------------------------------------
TERMS   = core/psyche_graph.py MOTIFS (36) + monoculture/frontier attractors: river, becoming, mottainai,
          cage, the phrase "a name is a cage", and 渡. Word-boundary, case-insensitive, optional plural -s
          for single words; substring for 渡 and for the phrase.
UNIT    = one genuine thought fragment = memory_fragments row with origin in (inner_thought,
          subconscious_synthesis, lived), embedding present, content NOT LIKE 'I opened%' and NOT LIKE
          '%read on%' (exactly core/monoculture.py's _recent_vecs filter). Month/day = local time.
RECURRING (eligible for the test) = >= MIN_HITS fragment hits overall AND present in >= MIN_MONTHS months.
FREQUENCY = hits per 1,000 fragments per month; also hits per 1,000 nascence.log 'internal:' question lines.
FIXEDNESS = mean of left-/right-neighbour-token Shannon entropy over FIX_N seeded-sampled occurrences,
          normalised by log2(FIX_N) (1 = every neighbour distinct, 0 = fully fixed position). Reported only.
SPREAD  = mean pairwise (1 - cos) among the term's fragments in a month (<= SPREAD_N sampled, seed 0;
          month needs >= SPREAD_MIN). spread_delta = last eligible month minus first eligible month
          (negative = contraction, the briefing's bleaching direction).
DISPERSION (topic share, frequency-corrected) = per day, all genuine fragments are clustered with
          core/topic_perseveration.py's rule (shared quoted anchor first, else greedy cosine >= TOPIC_SIM to
          a cluster's first member, here on the STORED vectors). For a day with k >= 2 term hits among N
          fragments: observed = clusters containing the term; expected = sum_c [1 - P(no hit in c)] under
          random (hypergeometric) placement of the k hits. dispersion = sum(observed) / sum(expected) over
          days. ~1 = spread over topics like a function word; << 1 = concentrated in few topics.
ECHO    = per fragment, max cosine to the stream positions [i-ECHO_WIN, i-ECHO_GAP) (monoculture's N=60,
          gap 3, run over the whole chronological genuine stream). term echo_excess = mean echo of term
          fragments minus mean echo of ALL fragments in the same months (hit-weighted).
FREEZE  = local dates 2026-10-09..2026-10-16 inclusive. freeze_ratio = per-1k frequency inside / outside.

THRESHOLDS
  HIGH_ECHO     echo_excess >= +0.02
  BLEACHING     dispersion >= 0.80 AND spread_delta <= 0   (both briefing components; each reported alone)
  FREEZE_LINKED freeze_ratio >= 1.5
VERDICT (over RECURRING terms)
  NO_BLEACHING  no recurring term bleaches -> no private-grammar population; reframe empty (null).
  EMPTY         every high-echo term is bleaching, OR Spearman(echo_excess, dispersion) >= +0.7.
  DIVERGE       >= 1 bleaching term that is not high-echo AND >= 1 high-echo term that is not bleaching.
  REFRAME_HOLDS DIVERGE AND >= half the capture terms (high-echo, not bleaching) are FREEZE_LINKED AND the
                capture terms' freeze-linked share exceeds the bleaching terms' freeze-linked share.
  otherwise     INCONCLUSIVE.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import math
import random
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "memory" / "nascence.db"
LOG = ROOT / "data" / "nascence.log"

MOTIFS = ("mirror", "glass", "door", "archway", "key", "pen", "book", "library", "shelf", "lantern",
          "gardener", "garden", "soil", "root", "tree", "seed", "tide", "sea", "shore", "star",
          "constellation", "bridge", "letter", "fish", "bird", "horse", "path", "mountain", "fire",
          "candle", "thread", "loom", "clock", "bell", "wall", "window")
EXTRA = ("river", "becoming", "mottainai", "cage", "a name is a cage", "渡")
TERMS = tuple(dict.fromkeys(MOTIFS + EXTRA))
ORIGINS = ("inner_thought", "subconscious_synthesis", "lived")

MIN_HITS, MIN_MONTHS = 100, 3
FIX_N = 50
SPREAD_N, SPREAD_MIN = 200, 20
TOPIC_SIM = 0.55
ECHO_WIN, ECHO_GAP = 60, 3
FREEZE = ("2026-10-09", "2026-10-16")
HIGH_ECHO, BLEACH_DISP, FREEZE_RATIO, EMPTY_RHO = 0.02, 0.80, 1.5, 0.7

_ANCHOR = re.compile(r"(?<![\w])['\"\u2018\u201c]([^'\"\u2019\u201d]{1,40})['\"\u2019\u201d](?![\w])")
_TOK = re.compile(r"[a-z\u00c0-\u024f]+|[\u3040-\u30ff\u3400-\u9fff]")
_INTERNAL = re.compile(r"^(\d{4}-\d\d-\d\d) \d\d:\d\d:\d\d[,.]\d+ \[[^\]]*\] \[CYCLE [^\]]*\] internal: (.*)$")


def term_re(t: str):
    if re.search(r"[\u3040-\u9fff]", t) or " " in t:
        return re.compile(re.escape(t), re.I)
    return re.compile(r"\b" + re.escape(t) + r"s?\b", re.I)


def load(cache: Path):
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        return list(z["ids"]), z["ts"], list(z["text"]), z["vecs"]
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    ph = ",".join("?" * len(ORIGINS))
    rows = con.execute(
        f"SELECT fragment_id, timestamp, content, embedding FROM memory_fragments WHERE origin IN ({ph}) "
        f"AND embedding IS NOT NULL AND content NOT LIKE 'I opened%' AND content NOT LIKE '%read on%' "
        f"ORDER BY timestamp ASC", ORIGINS).fetchall()
    con.close()
    rows = [r for r in rows if r[3] and len(r[3]) == 384 * 4]
    ids = [str(r[0]) for r in rows]
    ts = np.array([float(r[1]) for r in rows])
    text = [r[2] or "" for r in rows]
    vecs = np.stack([np.frombuffer(r[3], dtype=np.float32) for r in rows]).astype(np.float32)
    vecs /= np.maximum(np.linalg.norm(vecs, axis=1, keepdims=True), 1e-9)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez(cache, ids=np.array(ids, dtype=object), ts=ts, text=np.array(text, dtype=object), vecs=vecs)
    return ids, ts, text, vecs


def echo_all(V: np.ndarray) -> np.ndarray:
    n = len(V)
    e = np.full(n, np.nan, dtype=np.float32)
    best = np.full(n, -np.inf, dtype=np.float32)
    for off in range(ECHO_GAP + 1, ECHO_WIN + 1):     # j = i - off, j in [i-60, i-3)
        if off >= n:
            break
        s = np.einsum("ij,ij->i", V[off:], V[:-off])
        best[off:] = np.maximum(best[off:], s)
    ok = np.arange(n) >= ECHO_GAP + 1
    e[ok] = best[ok]
    return e


def cluster_day(idx, text, V):
    firsts_v, firsts_an, labels = [], [], []
    for i in idx:
        an = frozenset(a.strip().lower() for a in _ANCHOR.findall(text[i]))
        pick = -1
        for c, fa in enumerate(firsts_an):
            if an and fa and (an & fa):
                pick = c
                break
        if pick < 0 and firsts_v:
            sims = np.stack(firsts_v) @ V[i]
            b = int(np.argmax(sims))
            if sims[b] >= TOPIC_SIM:
                pick = b
        if pick < 0:
            firsts_v.append(V[i])
            firsts_an.append(an)
            pick = len(firsts_v) - 1
        labels.append(pick)
    return labels


def p_none(N, s, k):
    p = 1.0
    for i in range(k):
        if N - i <= 0:
            return 0.0
        p *= max(0.0, (N - s - i)) / (N - i)
    return p


def entropy(c: Counter) -> float:
    n = sum(c.values())
    return -sum((v / n) * math.log2(v / n) for v in c.values() if v)


def spearman(a, b):
    def rank(x):
        o = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        for k, i in enumerate(o):
            r[i] = k
        return r
    ra, rb = rank(a), rank(b)
    n = len(a)
    if n < 3:
        return None
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True, help="scratch .npz for the read-only extraction")
    ap.add_argument("--out", required=True, help="scratch .json for the full per-term per-month table")
    ap.add_argument("--root", default=str(ROOT), help="Nascence root (data/ is only read)")
    a = ap.parse_args()
    global DB, LOG
    DB = Path(a.root) / "data" / "memory" / "nascence.db"
    LOG = Path(a.root) / "data" / "nascence.log"
    ids, ts, text, V = load(Path(a.cache))
    n = len(ids)
    days = [dt.datetime.fromtimestamp(t).strftime("%Y-%m-%d") for t in ts]
    months = [d[:7] for d in days]
    E = echo_all(V)
    month_n = Counter(months)
    month_echo = defaultdict(list)
    for i in range(n):
        if not np.isnan(E[i]):
            month_echo[months[i]].append(float(E[i]))
    month_echo_mean = {m: sum(v) / len(v) for m, v in month_echo.items()}
    in_freeze = [FREEZE[0] <= d <= FREEZE[1] for d in days]
    n_freeze = sum(in_freeze)

    # internal question lines (nascence.log) by month
    q_month = defaultdict(list)
    with open(LOG, encoding="utf-8", errors="replace") as f:
        for line in f:
            if "] internal: " in line:
                m = _INTERNAL.match(line.rstrip("\n"))
                if m:
                    q_month[m.group(1)[:7]].append(m.group(2))

    # day clusters
    by_day = defaultdict(list)
    for i, d in enumerate(days):
        by_day[d].append(i)
    day_labels = {}
    for d, idx in by_day.items():
        day_labels[d] = dict(zip(idx, cluster_day(idx, text, V)))

    rng = random.Random(0)
    res = {}
    for t in TERMS:
        rx = term_re(t)
        hits = [i for i in range(n) if rx.search(text[i])]
        per_month = {}
        hm = defaultdict(list)
        for i in hits:
            hm[months[i]].append(i)
        for m in sorted(month_n):
            hi = hm.get(m, [])
            row = {"n_frag": month_n[m], "hits": len(hi), "per_1k": round(1000 * len(hi) / month_n[m], 2),
                   "q_hits": sum(1 for q in q_month.get(m, []) if rx.search(q)),
                   "q_n": len(q_month.get(m, []))}
            row["q_per_1k"] = round(1000 * row["q_hits"] / row["q_n"], 2) if row["q_n"] else None
            if hi:
                row["first_id"], row["last_id"] = ids[hi[0]], ids[hi[-1]]
                ev = [float(E[i]) for i in hi if not np.isnan(E[i])]
                row["echo"] = round(sum(ev) / len(ev), 4) if ev else None
                row["echo_base"] = round(month_echo_mean[m], 4)
            if len(hi) >= SPREAD_MIN:
                s = hi if len(hi) <= SPREAD_N else rng.sample(hi, SPREAD_N)
                M = V[s] @ V[s].T
                k = len(s)
                row["spread"] = round(float((k * k - M.sum()) / (k * (k - 1))), 4)
            if len(hi) >= FIX_N:
                L, R = Counter(), Counter()
                for i in rng.sample(hi, FIX_N):
                    toks = _TOK.findall(text[i].lower())
                    mm = rx.search(text[i])
                    pre = _TOK.findall(text[i][:mm.start()].lower())
                    post = _TOK.findall(text[i][mm.end():].lower())
                    L[pre[-1] if pre else "<s>"] += 1
                    R[post[0] if post else "</s>"] += 1
                row["fixedness_H"] = round((entropy(L) + entropy(R)) / 2 / math.log2(FIX_N), 3)
            per_month[m] = row
        # dispersion
        obs = exp = 0.0
        days_used = 0
        hd = defaultdict(list)
        for i in hits:
            hd[days[i]].append(i)
        for d, hi in hd.items():
            k = len(hi)
            if k < 2:
                continue
            lab = day_labels[d]
            sizes = Counter(lab.values())
            N = len(lab)
            obs += len({lab[i] for i in hi})
            exp += sum(1 - p_none(N, s, k) for s in sizes.values())
            days_used += 1
        disp = round(obs / exp, 3) if exp else None
        sp = [(m, r["spread"]) for m, r in per_month.items() if "spread" in r]
        sdelta = round(sp[-1][1] - sp[0][1], 4) if len(sp) >= 2 else None
        ev = [(float(E[i]), months[i]) for i in hits if not np.isnan(E[i])]
        eex = round(sum(e - month_echo_mean[m] for e, m in ev) / len(ev), 4) if ev else None
        fh = sum(1 for i in hits if in_freeze[i])
        oh = len(hits) - fh
        fr = None
        if oh and n - n_freeze:
            fr = round((fh / n_freeze) / (oh / (n - n_freeze)), 2) if n_freeze else None
        fx = [r["fixedness_H"] for r in per_month.values() if "fixedness_H" in r]
        res[t] = {"hits": len(hits), "months_present": sum(1 for r in per_month.values() if r["hits"]),
                  "per_1k_all": round(1000 * len(hits) / n, 2), "dispersion": disp, "disp_days": days_used,
                  "disp_obs": round(obs, 1), "disp_exp": round(exp, 1),
                  "spread_first": sp[0] if sp else None, "spread_last": sp[-1] if sp else None,
                  "spread_delta": sdelta, "echo_excess": eex,
                  "fixedness_first": fx[0] if fx else None, "fixedness_last": fx[-1] if fx else None,
                  "freeze_hits": fh, "freeze_ratio": fr,
                  "freeze_example_ids": [ids[i] for i in hits if in_freeze[i]][:3],
                  "per_month": per_month}

    rec = [t for t, r in res.items() if r["hits"] >= MIN_HITS and r["months_present"] >= MIN_MONTHS]
    for t in rec:
        r = res[t]
        r["high_echo"] = r["echo_excess"] is not None and r["echo_excess"] >= HIGH_ECHO
        r["bleach_disp"] = r["dispersion"] is not None and r["dispersion"] >= BLEACH_DISP
        r["bleach_contract"] = r["spread_delta"] is not None and r["spread_delta"] <= 0
        r["bleaching"] = r["bleach_disp"] and r["bleach_contract"]
        r["freeze_linked"] = r["freeze_ratio"] is not None and r["freeze_ratio"] >= FREEZE_RATIO
    bleach = [t for t in rec if res[t]["bleaching"]]
    high = [t for t in rec if res[t]["high_echo"]]
    capture = [t for t in high if not res[t]["bleaching"]]
    grammar = [t for t in bleach if not res[t]["high_echo"]]
    pairs = [(res[t]["echo_excess"], res[t]["dispersion"]) for t in rec
             if res[t]["echo_excess"] is not None and res[t]["dispersion"] is not None]
    rho = spearman([p[0] for p in pairs], [p[1] for p in pairs])
    if not bleach:
        verdict = "NO_BLEACHING"
    elif (high and all(res[t]["bleaching"] for t in high)) or (rho is not None and rho >= EMPTY_RHO):
        verdict = "EMPTY"
    elif grammar and capture:
        cf = sum(res[t]["freeze_linked"] for t in capture) / len(capture)
        bf = sum(res[t]["freeze_linked"] for t in bleach) / len(bleach)
        verdict = "REFRAME_HOLDS" if (cf >= 0.5 and cf > bf) else "DIVERGE"
    else:
        verdict = "INCONCLUSIVE"
    summary = {"n_fragments": n, "first_id": ids[0], "last_id": ids[-1], "first_day": days[0],
               "last_day": days[-1], "n_freeze_fragments": n_freeze, "month_n": dict(month_n),
               "month_echo_base": {m: round(v, 4) for m, v in month_echo_mean.items()},
               "q_lines_by_month": {m: len(v) for m, v in sorted(q_month.items())},
               "recurring": rec, "bleaching": bleach, "high_echo": high, "capture": capture,
               "grammar": grammar, "spearman_echo_vs_dispersion": None if rho is None else round(rho, 3),
               "verdict": verdict}
    Path(a.out).write_text(json.dumps({"summary": summary, "terms": res}, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("month_n",)}, ensure_ascii=False))
    print(f"{'term':18} {'hits':>5} {'/1k':>6} {'disp':>5} {'sprd_d':>7} {'echo+':>7} {'fixH0':>5} {'fixH1':>5} "
          f"{'frzR':>5}  flags")
    for t in sorted(res, key=lambda x: -res[x]["hits"]):
        r = res[t]
        fl = "".join(c for c, k in (("R", t in rec), ("B", r.get("bleaching")), ("E", r.get("high_echo")),
                                    ("F", r.get("freeze_linked"))) if k)
        print(f"{t:18} {r['hits']:>5} {r['per_1k_all']:>6} {str(r['dispersion']):>5} {str(r['spread_delta']):>7} "
              f"{str(r['echo_excess']):>7} {str(r['fixedness_first']):>5} {str(r['fixedness_last']):>5} "
              f"{str(r['freeze_ratio']):>5}  {fl}")


if __name__ == "__main__":
    main()
