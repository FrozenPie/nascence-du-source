"""J-3308 (U4): replay the near-duplicate text tests on real pairs against a decoupled judge panel.

READ-ONLY on live data: only opens files under --src/data for reading (default C:/Nascence). Writes ONLY under --out
(default docs/lab/J-3308_data in this tree). Pre-registration: docs/lab/J-3308_preregistration.md (read it first; the
rules, thresholds and decision rule in this file are the ones registered there).

Stages (run from the worktree root):
  python scripts/lab_J-3308_nearduplicate_replay.py build            # pairs, site rules, 3 tiers, strata, judge sample
  python scripts/lab_J-3308_nearduplicate_replay.py judge [--n N]    # call the local hubs (never Ramses); resumable
  python scripts/lab_J-3308_nearduplicate_replay.py report           # agreement tables + decision, writes summary.json

The module also exposes pure functions (tiers, site rules, wilson) that scripts/_test_J-3308_nearduplicate.py tests.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402,F401  (before anything else, per the job-run test rule)

SEED = 3308
T2_MIN = 0.60            # char 3-gram Jaccard (pre-registered, not tuned)
T3_MIN = 0.85            # embedding cosine (the frontier's validated bar)
HUBS = {"gemma4:12b": 11439, "falcon3:7b": 11440, "yi:34b-v1.5": 11442}   # local only; Ramses is never called
SOURCES = ("F", "L", "C", "D", "G")
TARGET_N = {"F": 600, "L": 500, "C": 300, "D": 400, "G": 200}
STRATA = ("A_both_dup", "B_site_only", "C_ref_only", "D_neither_hard", "E_neither_easy")
JUDGE_PER_STRATUM = 6    # 5 strata x 6 = 30 per source, 150 total


# ───────────────────────── pure helpers (tested) ─────────────────────────
def norm(s: str) -> str:
    return re.sub(r"[\W_]+", " ", (s or "").lower()).strip()


def shingles(s: str, n: int = 3) -> set:
    t = norm(s)
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))} if t else set()


def jac(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0


def cos(u, v) -> float | None:
    if u is None or v is None:
        return None
    dot = sum(x * y for x, y in zip(u, v))
    nu = math.sqrt(sum(x * x for x in u)) or 1.0
    nv = math.sqrt(sum(y * y for y in v)) or 1.0
    return float(dot / (nu * nv))


def tiers(a: str, b: str, ca: float | None) -> dict:
    """The three-tier reference. ca = embedding cosine (None when no embedding)."""
    t1 = norm(a) == norm(b) and bool(norm(a))
    j3 = jac(shingles(a), shingles(b))
    t2 = j3 >= T2_MIN
    t3 = ca is not None and ca >= T3_MIN
    return {"t1": t1, "t2": t2, "t3": t3, "j3": round(j3, 4), "ref_dup": bool(t1 or t2 or t3)}


def wilson(k: int, n: int, z: float = 1.96) -> tuple:
    if n <= 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round((c - h) / d, 3), round((c + h) / d, 3))


def site_rules():
    """Import the sites' OWN functions where one exists (so the replay cannot drift from the code); the rest are the
    inline expressions, copied with their file:line in the pre-registration."""
    from core import frontier, lane2, deliberation, guidance_learning, moment, wager_curiosity

    def r_frontier_lex(a, b, c):                  # core/frontier.py:275 (note_question_ex), the lexical leg alone
        ta, tb = frontier._toks(a), frontier._toks(b)
        return bool(ta and tb and len(ta & tb) / max(1, len(ta | tb)) > 0.55)

    def r_frontier(a, b, c):                      # LIVE verdict since D-0495: lexical leg OR semantic merge at 0.85
        return r_frontier_lex(a, b, c) or (c is not None and c >= frontier.SEMANTIC_MERGE_THRESHOLD)

    def r_wager(a, b, c):                         # core/wager_curiosity.py:154 same expression on its own tokenizer
        ta, tb = wager_curiosity._toks(a), wager_curiosity._toks(b)
        return bool(ta and tb and len(ta & tb) / max(1, len(ta | tb)) > wager_curiosity.TOPIC_JACCARD)

    def r_lane2(a, b, c):                         # core/lane2.py:370 pairwise core
        sa, sb = lane2._wonder_stems(a), lane2._wonder_stems(b)
        return bool(sa and sb and len(sa & sb) / len(sa | sb) >= lane2.WONDER_REPEAT_SIM)

    def r_delib(a, b, c):                         # core/deliberation.py:166
        return bool(deliberation._too_similar(a, b))

    def r_guid(a, b, c):                          # core/guidance_learning.py:231,305,327 (candidate pre-filter)
        if guidance_learning._overlap(a, b) >= guidance_learning._SIM_RELATED:
            return True
        return c is not None and c >= guidance_learning._SIM_RELATED_EMBED

    def r_commit(a, b, c):                        # core/commitment_ledger.py:855-885
        if c is not None and c >= 0.45:
            return True
        wa = {x for x in a.lower().split() if len(x) > 3}
        wb = {x for x in b.lower().split() if len(x) > 3}
        return bool(wa and wb and len(wa & wb) / max(1, len(wa | wb)) >= 0.5)

    def r_moment(a, b, c):                        # core/moment.py:209,221 (recall anchor, token fallback)
        ta, tb = moment._tokens(a), moment._tokens(b)
        return bool(ta and tb and len(ta & tb) / max(1, len(ta | tb)) >= moment._ANCHOR_FLOOR)

    return {"frontier": r_frontier, "frontier_lex": r_frontier_lex, "wager": r_wager, "lane2": r_lane2, "delib": r_delib, "guid": r_guid,
            "commit": r_commit, "moment": r_moment}


OWN_RULE = {"F": "frontier", "L": "lane2", "C": "commit", "D": "delib", "G": "guid"}

JUDGE_Q = {
    "F": "Two questions a mind asked itself. Are they asking the SAME question (one is a rewording or close paraphrase of "
         "the other, so answering one answers the other)? If they ask about different aspects or different things, "
         "answer false.",
    "L": "Two things a mind wondered. Are they the SAME wondering (the same question about the same thing, reworded)? "
         "If they wonder about different things or different aspects, answer false.",
    "C": "Two sentences in which a mind took a stand. Do they state the SAME stand (one is the other re-taken in "
         "different words)? A different claim, a different object, or a stronger or weaker claim is false.",
    "D": "A is a thought. B is the same thought thought again after more was added. Does B ONLY restate A, adding no new "
         "fact, image, idea or turn (an echo)? If B adds anything material, answer false.",
    "G": "Two lessons a mind wrote for itself. Do they teach the SAME lesson (one is a rewording or near copy of the "
         "other)? If the lesson differs in what it asks the mind to do, answer false.",
}


# ───────────────────────── data readers (read-only) ─────────────────────────
def _jl(path: Path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except Exception:
                    pass


def embed_all(texts: list) -> dict:
    from core.memory import store
    uniq = list(dict.fromkeys(t for t in texts if t))
    out = {}
    B = 128
    for i in range(0, len(uniq), B):
        chunk = uniq[i:i + B]
        for t, v in zip(chunk, store._embed_batch(chunk)):
            out[t] = v
    return out


def pool_F(src: Path, rng: random.Random):
    d = json.load(open(src / "data" / "frontier.json", encoding="utf-8"))["questions"]
    by_id = {q["id"]: q for q in d}
    pairs = []
    for q in d:
        if q.get("status") == "merged" and q.get("merged_into") in by_id:
            pairs.append((q["q"], by_id[q["merged_into"]]["q"], "merged_to_parent"))
        for v in q.get("variants") or []:
            if v.get("q"):
                pairs.append((v["q"], q["q"], "variant_of_entry"))
    seen = {frozenset((a, b)) for a, b, _ in pairs}
    live = [q["q"] for q in d if q.get("q") and q.get("status") != "merged"]
    sub = rng.sample(live, min(3500, len(live)))
    return pairs, sub, seen


def build_F(src: Path, rng: random.Random):
    pairs, sub, seen = pool_F(src, rng)
    emb = embed_all([x for p in pairs for x in p[:2]] + sub)
    import numpy as np
    keep = [t for t in sub if emb.get(t) is not None]
    M = np.array([emb[t] for t in keep], dtype="float32")
    M /= np.linalg.norm(M, axis=1, keepdims=True) + 1e-9
    S = M @ M.T
    np.fill_diagonal(S, -1)
    idx = np.argsort(-S, axis=1)[:, :3]
    for i, t in enumerate(keep):                         # hard neighbours: top-3 by embedding in a 3,500 subset
        for j in idx[i]:
            k = frozenset((t, keep[int(j)]))
            if k not in seen and len(k) == 2:
                seen.add(k)
                pairs.append((t, keep[int(j)], "nn_embedding"))
    for _ in range(2500):                                # random pairs and Jaccard-near pairs
        a, b = rng.sample(keep, 2)
        k = frozenset((a, b))
        if k not in seen:
            seen.add(k)
            pairs.append((a, b, "random"))
    return pairs, emb


def build_L(src: Path, rng: random.Random):
    rows = []
    seen_t = set()
    for r in _jl(src / "data" / "lane2_would_ask.jsonl"):
        w = (r.get("wonder") or "").strip()
        if w and w not in seen_t:
            seen_t.add(w)
            rows.append((float(r.get("ts") or 0), w))
    rows.sort()
    emb = embed_all([w for _, w in rows])
    from core import lane2
    stems = [lane2._wonder_stems(w) for _, w in rows]
    pairs = []
    for i in range(len(rows)):                           # the exact comparison set _wonder_repeat_check uses
        for j in range(i):
            if rows[i][0] - rows[j][0] > lane2.WONDER_REPEAT_WINDOW_S:
                continue
            si, sj = stems[i], stems[j]
            jj = len(si & sj) / len(si | sj) if si and sj and (si | sj) else 0.0
            c = cos(emb.get(rows[i][1]), emb.get(rows[j][1]))
            if jj >= 0.25 or (c is not None and c >= 0.62) or rng.random() < 0.0015:
                pairs.append((rows[i][1], rows[j][1], "in_window"))
    return pairs, emb


def build_C(src: Path, rng: random.Random):
    rows = []
    seen_t = set()
    for r in _jl(src / "data" / "commitment_ledger.jsonl"):
        if r.get("event") == "formed":
            s = (r.get("statement") or "").strip()
            if s and s != "None" and s not in seen_t:
                seen_t.add(s)
                rows.append((float(r.get("ts") or 0), s))
    rows.sort()
    emb = embed_all([s for _, s in rows])
    pairs = []
    for i in range(len(rows)):
        for j in range(i):
            if rows[i][0] - rows[j][0] > 86400.0:
                continue
            a, b = rows[i][1], rows[j][1]
            wa = {x for x in a.lower().split() if len(x) > 3}
            wb = {x for x in b.lower().split() if len(x) > 3}
            jj = len(wa & wb) / max(1, len(wa | wb))
            c = cos(emb.get(a), emb.get(b))
            if jj >= 0.25 or (c is not None and c >= 0.55) or rng.random() < 0.01:
                pairs.append((a, b, "formed_within_24h_PROXY"))
    return pairs, emb


def build_D(src: Path, rng: random.Random):
    rows = list(_jl(src / "data" / "deliberation_log.jsonl"))
    rows = [r for r in rows if r.get("raw") and r.get("integrated")]
    pick = rng.sample(rows, min(4000, len(rows)))
    pairs = [(r["raw"], r["integrated"], "raw_vs_integrated") for r in pick]
    emb = embed_all([x for p in pairs for x in p[:2]])
    return pairs, emb


def build_G(src: Path, rng: random.Random):
    g = json.load(open(src / "data" / "guidance_beliefs.json", encoding="utf-8"))
    texts = []
    for b in g:
        t = (str(b.get("principle", "")) + " " + str(b.get("scope", ""))).strip()
        if t:
            texts.append(t)
    texts = list(dict.fromkeys(texts))
    emb = embed_all(texts)
    from core import guidance_learning as GL
    pairs = []
    for i in range(len(texts)):
        for j in range(i):
            ov = GL._overlap(texts[i], texts[j])
            c = cos(emb.get(texts[i]), emb.get(texts[j]))
            if ov >= 0.08 or (c is not None and c >= 0.5) or rng.random() < 0.02:
                pairs.append((texts[i], texts[j], "belief_pair"))
    return pairs, emb


BUILDERS = {"F": build_F, "L": build_L, "C": build_C, "D": build_D, "G": build_G}


# ───────────────────────── stage: build ─────────────────────────
def stratum(site_dup: bool, ref_dup: bool, hard: bool) -> str:
    if site_dup and ref_dup:
        return STRATA[0]
    if site_dup:
        return STRATA[1]
    if ref_dup:
        return STRATA[2]
    return STRATA[3] if hard else STRATA[4]


def cmd_build(a) -> None:
    src, out = Path(a.src), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rules = site_rules()
    rng = random.Random(SEED)
    all_rows, pool_counts = [], {}
    for code in SOURCES:
        t0 = time.time()
        pairs, emb = BUILDERS[code](src, rng)
        pairs = [p for p in pairs if p[0] and p[1] and p[0] != "" and p[1] != ""]
        rows = []
        for a_, b_, kind in pairs:
            c = cos(emb.get(a_), emb.get(b_))
            tr = tiers(a_, b_, c)
            verdicts = {name: bool(fn(a_, b_, c)) for name, fn in rules.items()}
            site_dup = verdicts[OWN_RULE[code]]
            hard = (tr["j3"] >= 0.30) or (c is not None and c >= 0.60)
            rows.append({"src": code, "kind": kind, "a": a_, "b": b_, "cos": None if c is None else round(c, 4),
                         **tr, "rules": verdicts, "site_dup": site_dup,
                         "stratum": stratum(site_dup, tr["ref_dup"], hard)})
        cells = {s: [r for r in rows if r["stratum"] == s] for s in STRATA}
        pool_counts[code] = {s: len(v) for s, v in cells.items()}
        # allocate TARGET_N[code] equally over the strata, redistribute what a small stratum cannot fill
        want, left = {}, TARGET_N[code]
        order = sorted(STRATA, key=lambda s: len(cells[s]))
        for k, s in enumerate(order):
            share = left // (len(order) - k)
            want[s] = min(len(cells[s]), share)
            left -= want[s]
        chosen = []
        for s in STRATA:
            rng.shuffle(cells[s])
            chosen += cells[s][:want[s]]
        for r in chosen:
            r["pool_n"] = int(pool_counts[code][r["stratum"]])
            r["alloc_n"] = want[r["stratum"]]
        all_rows += chosen
        print(f"{code}: pool {len(rows)} -> {len(chosen)} pairs in {time.time() - t0:.0f}s; strata pool {pool_counts[code]}")
    for i, r in enumerate(all_rows):
        r["pid"] = f"P{i:04d}"
    with open(out / "pairs.jsonl", "w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # judge sample: JUDGE_PER_STRATUM per stratum per source (all of a stratum if fewer)
    sample = []
    for code in SOURCES:
        for s in STRATA:
            cell = [r for r in all_rows if r["src"] == code and r["stratum"] == s]
            rng.shuffle(cell)
            for r in cell[:JUDGE_PER_STRATUM]:
                swap = rng.random() < 0.5
                sample.append({"pid": r["pid"], "src": code, "stratum": s, "swap": swap,
                               "a": r["b"] if swap else r["a"], "b": r["a"] if swap else r["b"],
                               "pool_n": r["pool_n"], "judged_n": 0})
    for code in SOURCES:                                  # weight = pool stratum size / judged in that stratum
        for s in STRATA:
            cell = [x for x in sample if x["src"] == code and x["stratum"] == s]
            for x in cell:
                x["judged_n"] = len(cell)
    rng.shuffle(sample)
    with open(out / "judge_pairs.jsonl", "w", encoding="utf-8") as f:
        for x in sample:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    json.dump({"pool_counts": pool_counts, "n_pairs": len(all_rows), "n_judge": len(sample), "seed": SEED},
              open(out / "build_summary.json", "w"), indent=1)
    print("pairs", len(all_rows), "judge sample", len(sample))


def cmd_topup(a) -> None:
    """Empty strata leave fewer than 30 pairs for a source (F had no site-only pairs, D no site-dup pairs...). Top each
    source up to 30 by round-robin over its NON-EMPTY strata, drawn from pairs.jsonl, appended to judge_pairs.jsonl.
    Deviation from the pre-registered 6 per stratum, recorded in the report; weights use actual counts."""
    out = Path(a.out)
    rng = random.Random(SEED + 1)
    pairs = [json.loads(l) for l in open(out / "pairs.jsonl", encoding="utf-8")]
    sample = [json.loads(l) for l in open(out / "judge_pairs.jsonl", encoding="utf-8")]
    have = {x["pid"] for x in sample}
    added = []
    for code in SOURCES:
        n = sum(1 for x in sample if x["src"] == code)
        pool = {s: [r for r in pairs if r["src"] == code and r["stratum"] == s and r["pid"] not in have] for s in STRATA}
        for s in STRATA:
            rng.shuffle(pool[s])
        while n < 30 and any(pool.values()):
            for s in STRATA:
                if n >= 30:
                    break
                if pool[s]:
                    r = pool[s].pop()
                    swap = rng.random() < 0.5
                    added.append({"pid": r["pid"], "src": code, "stratum": s, "swap": swap,
                                  "a": r["b"] if swap else r["a"], "b": r["a"] if swap else r["b"],
                                  "pool_n": r["pool_n"], "judged_n": 0, "topup": True})
                    n += 1
    with open(out / "judge_pairs.jsonl", "a", encoding="utf-8") as f:
        for x in added:
            f.write(json.dumps(x, ensure_ascii=False) + chr(10))
    print("topup added", len(added))


# ───────────────────────── stage: judge ─────────────────────────
def ask(model: str, system: str, user: str, timeout: int = 200) -> tuple:
    import requests
    t0 = time.time()
    r = requests.post(f"http://127.0.0.1:{HUBS[model]}/api/chat", timeout=timeout, json={
        "model": model, "stream": False,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "options": {"temperature": 0, "num_predict": 80}})
    txt = ((r.json().get("message") or {}).get("content") or "")
    m = re.search(r'"same"\s*:\s*(true|false)', txt, re.I)
    return (None if not m else m.group(1).lower() == "true"), txt[:200], round(time.time() - t0, 1)


def cmd_judge(a) -> None:
    """Gemma and falcon judge every sampled pair, each on its own hub in its own thread; yi breaks ties (capped).
    Resumable: rows already in judge_labels.jsonl are not asked again. Local hubs only."""
    import threading
    out = Path(a.out)
    sample = [json.loads(l) for l in open(out / "judge_pairs.jsonl", encoding="utf-8")][: a.n]
    path = out / "judge_labels.jsonl"
    done = {}
    if path.exists():
        for l in open(path, encoding="utf-8"):
            r = json.loads(l)
            done[(r["pid"], r["model"])] = r
    lock = threading.Lock()
    f = open(path, "a", encoding="utf-8")

    def refresh():
        """Re-read the label file so two judge processes (forward and --rev) never ask the same pair twice."""
        with lock:
            for l in open(path, encoding="utf-8"):
                try:
                    r = json.loads(l)
                except Exception:
                    continue
                done[(r["pid"], r["model"])] = r

    def one(model, x, timeout=200):
        if (x["pid"], model) not in done:
            refresh()
        if (x["pid"], model) in done:
            return done[(x["pid"], model)]["same"]
        sysmsg = JUDGE_Q[x["src"]] + ' Answer ONLY JSON: {"same": true} or {"same": false}.'
        try:
            v, raw, s = ask(model, sysmsg, "A: " + x["a"] + chr(10) + "B: " + x["b"], timeout=timeout)
        except Exception as exc:
            v, raw, s = None, repr(exc)[:150], None
        rec = {"pid": x["pid"], "model": model, "same": v, "raw": raw, "s": s}
        with lock:
            f.write(json.dumps(rec, ensure_ascii=False) + chr(10))
            f.flush()
            done[(x["pid"], model)] = rec
        return v

    def worker(model):
        for k, x in enumerate(reversed(sample) if a.rev else sample):
            one(model, x)
            if k % 10 == 0:
                print(model, k, flush=True)

    ths = [threading.Thread(target=worker, args=(m,)) for m in a.models.split(",")]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    n_yi = 0
    for x in sample:
        g, fa = done.get((x["pid"], "gemma4:12b"), {}).get("same"), done.get((x["pid"], "falcon3:7b"), {}).get("same")
        if g is not None and fa is not None and g != fa and n_yi < a.yi_cap and (x["pid"], "yi:34b-v1.5") not in done:
            n_yi += 1
            one("yi:34b-v1.5", x, timeout=400)
            print("yi", x["pid"], flush=True)
    f.close()


# ───────────────────────── stage: report ─────────────────────────
def panel_label(votes: dict) -> tuple:
    g, fa, y = votes.get("gemma4:12b"), votes.get("falcon3:7b"), votes.get("yi:34b-v1.5")
    ans = [v for v in (g, fa) if v is not None]
    if len(ans) == 2 and g == fa:
        return g, "unanimous2"
    if len(ans) == 2 and y is not None:
        return y, "yi_tiebreak"
    if len(ans) == 2:
        return None, "split_no_tiebreak"
    if len(ans) == 1:
        return ans[0], "single_judge"
    return None, "no_judge"


def cmd_report(a) -> None:
    out = Path(a.out)
    pairs = {r["pid"]: r for r in (json.loads(l) for l in open(out / "pairs.jsonl", encoding="utf-8"))}
    sample = [json.loads(l) for l in open(out / "judge_pairs.jsonl", encoding="utf-8")]
    votes: dict = {}
    lp = out / "judge_labels.jsonl"
    if lp.exists():
        for l in open(lp, encoding="utf-8"):
            r = json.loads(l)
            votes.setdefault(r["pid"], {})[r["model"]] = r["same"]
    summ = {"per_source": {}, "cross_site_matrix": {}, "judge_coverage": {}}
    # cross-site matrix: how often each rule says dup on each source's pairs, and pairwise agreement with the own rule
    for code in SOURCES:
        rows = [r for r in pairs.values() if r["src"] == code]
        summ["cross_site_matrix"][code] = {name: round(sum(1 for r in rows if r["rules"][name]) / max(1, len(rows)), 3)
                                           for name in rows[0]["rules"]} if rows else {}
    # the sites against each other on the SAME text (no judge needed): share of pairs where two rules give different verdicts
    names = ["frontier", "lane2", "delib", "commit", "guid"]
    allp = list(pairs.values())
    summ["rule_pairwise_disagreement_all_pairs"] = {
        f"{x}|{y}": round(sum(1 for r in allp if r["rules"][x] != r["rules"][y]) / max(1, len(allp)), 3)
        for i, x in enumerate(names) for y in names[i + 1:]}
    summ["ladder_vs_rules_all_pairs"] = {n: round(sum(1 for r in allp if r["rules"][n] != r["ref_dup"]) / max(1, len(allp)), 3)
                                         for n in names}
    for code in SOURCES:
        xs = [x for x in sample if x["src"] == code]
        lab = []
        for x in xs:
            p = pairs[x["pid"]]
            lbl, how = panel_label(votes.get(x["pid"], {}))
            lab.append({**x, "label": lbl, "how": how, "site": p["site_dup"], "ref": p["ref_dup"], "t1": p["t1"],
                        "t2": p["t2"], "t3": p["t3"], "rules": p["rules"]})
        judged = [r for r in lab if r["label"] is not None]
        _cnt: dict = {}
        for r in judged:
            _cnt[r["stratum"]] = _cnt.get(r["stratum"], 0) + 1
        for r in judged:
            r["judged_n"] = _cnt[r["stratum"]]          # weight = pool stratum size / judged in that stratum (actual)
        summ["judge_coverage"][code] = {"sampled": len(xs), "judged": len(judged),
                                        "how": {h: sum(1 for r in lab if r["how"] == h) for h in sorted({r["how"] for r in lab})}}
        if not judged:
            continue
        # stratum-weighted agreement of the SITE rule with the judge label
        def wagree(pred):
            num = den = 0.0
            for r in judged:
                w = r["pool_n"] / max(1, r["judged_n"])
                den += w
                num += w * (1.0 if pred(r) == r["label"] else 0.0)
            return round(num / den, 3) if den else None
        ties = [r for r in lab if r["how"] == "split_no_tiebreak"]     # gemma and falcon split, yi did not answer
        site_ag = wagree(lambda r: r["site"])
        ref_ag = wagree(lambda r: r["ref"])
        tier_ag = {t: wagree(lambda r, t=t: r[t]) for t in ("t1", "t2", "t3")}
        raw_ag = sum(1 for r in judged if r["site"] == r["label"])
        # D_site: among pairs where at least one tier equals the judge label, site differs from the judge
        tier_right = [r for r in judged if any(r[t] == r["label"] for t in ("t1", "t2", "t3"))]
        dis = [r for r in tier_right if r["site"] != r["label"]]
        summ["per_source"][code] = {
            "n_judged": len(judged), "site_rule": OWN_RULE[code],
            "judge_dup_share": round(sum(1 for r in judged if r["label"]) / len(judged), 3),
            "site_agree_weighted": site_ag, "site_agree_raw": f"{raw_ag}/{len(judged)}",
            "site_agree_raw_ci95": wilson(raw_ag, len(judged)),
            "unresolved_ties": len(ties),
            "site_agree_raw_ties_worst_best": [f"{raw_ag}/{len(judged) + len(ties)}", f"{raw_ag + len(ties)}/{len(judged) + len(ties)}"],
            "ref_ladder_agree_weighted": ref_ag, "tier_agree_weighted": tier_ag,
            "D_site_disagree_where_tier_right": f"{len(dis)}/{len(tier_right)}",
            "D_site_rate": round(len(dis) / len(tier_right), 3) if tier_right else None,
            "D_site_ci95": wilson(len(dis), len(tier_right)),
            "site_fp_vs_judge": sum(1 for r in judged if r["site"] and not r["label"]),
            "site_fn_vs_judge": sum(1 for r in judged if (not r["site"]) and r["label"]),
        }
    near = [c for c in ("F", "L", "C", "D") if c in summ["per_source"]]
    over10 = [c for c in near if (summ["per_source"][c]["D_site_rate"] or 0) >= 0.10]
    allge90 = bool(near) and all((summ["per_source"][c]["site_agree_weighted"] or 0) >= 0.90 for c in near)
    def _best_ref(c):          # pre-registered wording: the best single tier, or the ladder
        ps = summ["per_source"][c]
        return max([ps["ref_ladder_agree_weighted"] or 0] + [v or 0 for v in ps["tier_agree_weighted"].values()])
    nreg = [c for c in near if _best_ref(c) < (summ["per_source"][c]["site_agree_weighted"] or 0)]
    # NOT pre-registered, reported beside it: does ONE shared tier/ladder (the same on every site) regress anywhere?
    nreg_shared_ladder = [c for c in near if (summ["per_source"][c]["ref_ladder_agree_weighted"] or 0)
                          < (summ["per_source"][c]["site_agree_weighted"] or 0)]
    nreg_shared_t3 = [c for c in near if (summ["per_source"][c]["tier_agree_weighted"]["t3"] or 0)
                      < (summ["per_source"][c]["site_agree_weighted"] or 0)]
    settled = [c for c in over10 if (summ["per_source"][c]["D_site_ci95"][0] or 0) >= 0.10]
    summ["decision_inputs"] = {"near_dup_sites_D_ge_10pct": over10, "all_sites_agree_ge_90pct": allge90,
                               "sites_where_best_ref_regresses_prereg": nreg,
                               "sites_where_one_shared_ladder_regresses_not_prereg": nreg_shared_ladder,
                               "sites_where_one_shared_t3_regresses_not_prereg": nreg_shared_t3,
                               "sites_D_ge_10pct_with_ci_lower_ge_10pct": settled}
    if allge90:
        summ["decision"] = "STOP: leave the sites alone, log the duplication as known and free"
    elif len(settled) >= 2 and not nreg:
        summ["decision"] = "RECOMMEND shared helper per the pre-registered rule (upper bound: enriched universe; confirm on natural traffic first); see qualifiers in the report"
    elif len(over10) >= 2 and not nreg:
        summ["decision"] = "NOT SETTLED: D_site point estimate >= 10 percent on 2+ sites but fewer than 2 have a CI lower bound >= 10 percent"
    else:
        summ["decision"] = "PARTIAL: no shared helper; see per_source for the one-site fix"
    json.dump(summ, open(out / "summary.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(summ, indent=1, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("build", "topup", "judge", "report"))
    ap.add_argument("--src", default="C:/Nascence")
    ap.add_argument("--out", default=str(ROOT / "docs" / "lab" / "J-3308_data"))
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--yi-cap", type=int, default=12)
    ap.add_argument("--rev", action="store_true", help="judge in reverse order (second process)")
    ap.add_argument("--models", default="gemma4:12b,falcon3:7b")
    a = ap.parse_args()
    {"build": cmd_build, "topup": cmd_topup, "judge": cmd_judge, "report": cmd_report}[a.stage](a)


if __name__ == "__main__":
    main()
