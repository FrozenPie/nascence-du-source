#!/usr/bin/env python
"""J-3311: used-label for recall_served_log + interim judge calibration + 2-slot ceiling.

READ-ONLY on live data (data/recall_served_log.jsonl, data/training/voice.jsonl, data/training/perception.jsonl,
data/memory/nascence.db opened mode=ro&immutable=1). Writes only under docs/lab/J-3311_data/ of THIS tree.
Definitions and thresholds are fixed in docs/lab/J-3311_data/PREREG_J-3311.md (committed before any result).

Subcommands:
  labels   build U4 / SE / UE labels per served fragment, null A (threshold), null B (diagnostic) -> labels.jsonl
  judge    interim pointwise relevance judge (local hub) on a cycle-ordered sample -> judge_scores.jsonl (resumable)
  report   rates, AUCs, 2-slot ceiling -> results.json
Env: J3311_DATA (default C:\\Nascence\\data) to point at a different data dir (the test uses a temp dir).
"""
import argparse
import json
import math
import os
import random
import re
import sqlite3
import sys
import time
import zlib
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "lab" / "J-3311_data"
DATA = Path(os.environ.get("J3311_DATA", r"C:\Nascence\data"))
SEED = 3311
NULL_A_DRAWS = 5
NULL_B_N = 1500
FRAG_SENT_CAP = 12
CHUNK_CHARS = 400

# --------------------------------------------------------------------------- text helpers
_WORD = re.compile(r"[a-z0-9']+")
_SPLIT = re.compile(r"(?<=[.!?\u2026])\s+|\n+")


def words(t):
    return _WORD.findall((t or "").lower())


def grams4(t):
    w = words(t)
    return {tuple(w[i:i + 4]) for i in range(len(w) - 3)}


def sentences(t, cap=None):
    out = [s.strip()[:CHUNK_CHARS] for s in _SPLIT.split(t or "") if len(words(s)) >= 4]
    return out[:cap] if cap else out


def fragment_chunks(t):
    s = sentences(t, FRAG_SENT_CAP)
    if s:
        return s
    t = (t or "").strip()
    return [t[:CHUNK_CHARS]] if t else []


# --------------------------------------------------------------------------- stats helpers
def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round((c - h) / d, 4), round((c + h) / d, 4))


def auc(scores, labels):
    """Mann-Whitney AUC with average ranks for ties. None if one class is empty."""
    from scipy.stats import rankdata
    s = np.asarray(scores, float)
    y = np.asarray(labels, bool)
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return None
    r = rankdata(s)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def auc_cluster_boot(scores, labels, clusters, n_boot=2000, seed=SEED):
    s = np.asarray(scores, float)
    y = np.asarray(labels, bool)
    cl = np.asarray(clusters)
    uniq = np.unique(cl)
    if len(uniq) == 0:
        return (None, None)
    idx = {c: np.where(cl == c)[0] for c in uniq}
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        ii = np.concatenate([idx[c] for c in pick])
        a = auc(s[ii], y[ii])
        if a is not None:
            vals.append(a)
    if not vals:
        return (None, None)
    return (round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4))


# --------------------------------------------------------------------------- loaders
def read_jsonl(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def _as_dict(v):
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        try:
            import ast
            d = ast.literal_eval(v)
            return d if isinstance(d, dict) else {}
        except Exception:
            return {}
    return {}


def load_voice_finals(data=None):
    data = data or DATA
    out = {}
    for r in read_jsonl(data / "training" / "voice.jsonl"):
        d = _as_dict(r.get("output"))
        f = d.get("final")
        if isinstance(f, str) and f.strip():
            out[r.get("cycle_id")] = f
    return out


def load_perception(data=None):
    data = data or DATA
    out = {}
    for r in read_jsonl(data / "training" / "perception.jsonl"):
        d = _as_dict(r.get("output"))
        out[r.get("cycle_id")] = {"raw_input": r.get("raw_input") or "", "summary": d.get("summary") or ""}
    return out


def open_db(data=None):
    data = data or DATA
    p = (data / "memory" / "nascence.db").as_posix()
    return sqlite3.connect(f"file:{p}?mode=ro&immutable=1", uri=True)


def fetch_fragments(db, ids):
    out = {}
    ids = list(ids)
    for i in range(0, len(ids), 400):
        part = ids[i:i + 400]
        q = ",".join("?" * len(part))
        for fid, content, origin in db.execute(
                f"SELECT fragment_id, content, origin FROM memory_fragments WHERE fragment_id IN ({q})", part):
            out[fid] = (content or "", origin or "")
    return out


# --------------------------------------------------------------------------- embedding
class Embedder:
    """Cached, normalised sentence embeddings. `fn(list[str]) -> ndarray` is injectable for tests."""

    def __init__(self, fn=None):
        self.fn = fn
        self.cache = {}

    def _load(self):
        if self.fn is None:
            from sentence_transformers import SentenceTransformer
            m = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
            self.fn = lambda xs: m.encode(xs, batch_size=64, normalize_embeddings=True, show_progress_bar=False)

    def many(self, texts):
        self._load()
        need = [t for t in dict.fromkeys(texts) if t not in self.cache]
        for i in range(0, len(need), 2048):
            part = need[i:i + 2048]
            vec = np.asarray(self.fn(part), dtype=np.float32)
            n = np.linalg.norm(vec, axis=1, keepdims=True)
            n[n == 0] = 1
            vec = vec / n
            for t, v in zip(part, vec):
                self.cache[t] = v
        return [self.cache[t] for t in texts]

    def mat(self, texts):
        if not texts:
            return np.zeros((0, 384), np.float32)
        return np.vstack(self.many(texts))


def se_score(frag_mat, out_mat):
    if frag_mat.shape[0] == 0 or out_mat.shape[0] == 0:
        return 0.0
    return float((frag_mat @ out_mat.T).max())


# --------------------------------------------------------------------------- labels stage
def build_labels(emb=None, data=None, out_dir=None, verbose=True):
    data = data or DATA
    out_dir = out_dir or OUT
    out_dir.mkdir(parents=True, exist_ok=True)
    emb = emb or Embedder()
    served = read_jsonl(data / "recall_served_log.jsonl")
    finals = load_voice_finals(data)
    db = open_db(data)
    cycles = {}
    dropped_no_voice = 0
    for r in served:
        cid = r.get("cycle_id")
        if cid not in finals:
            dropped_no_voice += 1
            continue
        cycles[cid] = r
    all_ids = {f["fragment_id"] for r in cycles.values() for f in r.get("fragments", [])}
    frags = fetch_fragments(db, all_ids)
    out_sents = {cid: sentences(finals[cid]) for cid in cycles}
    # embed
    texts = []
    for cid in cycles:
        texts += out_sents[cid]
    chunks = {fid: fragment_chunks(c) for fid, (c, _o) in frags.items()}
    for fid in chunks:
        texts += chunks[fid]
    # null B draw (unserved, same origin mix)
    rng = random.Random(SEED)
    served_origin_counts = {}
    for r in cycles.values():
        for f in r.get("fragments", []):
            served_origin_counts[f.get("origin")] = served_origin_counts.get(f.get("origin"), 0) + 1
    origins = list(served_origin_counts)
    weights = [served_origin_counts[o] for o in origins]
    pool_by_origin = {}
    for o in origins:
        pool_by_origin[o] = [x[0] for x in db.execute(
            "SELECT fragment_id FROM memory_fragments WHERE origin=? AND embedding IS NOT NULL", (o,))
            if x[0] not in all_ids]
    nb_ids = []
    for _ in range(NULL_B_N):
        o = rng.choices(origins, weights)[0]
        if pool_by_origin[o]:
            nb_ids.append(rng.choice(pool_by_origin[o]))
    nb_frags = fetch_fragments(db, set(nb_ids))
    db.close()
    nb_chunks = {fid: fragment_chunks(c) for fid, (c, _o) in nb_frags.items()}
    for fid in nb_chunks:
        texts += nb_chunks[fid]
    if verbose:
        print(f"embedding {len(set(texts))} unique texts ...", flush=True)
    t0 = time.time()
    emb.many(texts)
    if verbose:
        print(f"embedded in {time.time() - t0:.0f}s", flush=True)
    out_mats = {cid: emb.mat(out_sents[cid]) for cid in cycles}
    frag_mats = {fid: emb.mat(chunks[fid]) for fid in chunks}
    # units
    units = []
    missing = 0
    by_type = {}
    for cid, r in cycles.items():
        by_type.setdefault(r.get("input_type"), []).append(cid)
    g_out = {cid: grams4(finals[cid]) for cid in cycles}
    nullA = []
    for cid, r in cycles.items():
        fr = r.get("fragments", [])
        for pos, f in enumerate(fr):
            fid = f["fragment_id"]
            if fid not in frags:
                missing += 1
                continue
            content, _o = frags[fid]
            u4 = bool(grams4(content) & g_out[cid])
            se = se_score(frag_mats[fid], out_mats[cid])
            units.append({"cycle_id": cid, "fragment_id": fid, "input_type": r.get("input_type"),
                          "origin": f.get("origin"), "layer": f.get("layer"),
                          "abstraction_level": f.get("abstraction_level"),
                          "relevance": f.get("relevance"), "pos": pos, "n": len(fr),
                          "u4": u4, "se": round(se, 4), "ts": r.get("ts")})
            pool = [c for c in by_type[r.get("input_type")] if c != cid]
            for oc in rng.sample(pool, min(NULL_A_DRAWS, len(pool))):
                nullA.append(se_score(frag_mats[fid], out_mats[oc]))
    nullA = np.asarray(nullA)
    thr = {"p95": float(np.percentile(nullA, 95)), "p99": float(np.percentile(nullA, 99)),
           "p999": float(np.percentile(nullA, 99.9))}
    T = thr["p99"]
    for u in units:
        u["ue"] = u["se"] >= T
        u["ue95"] = u["se"] >= thr["p95"]
        u["ue999"] = u["se"] >= thr["p999"]
    # null B diagnostic
    all_cids = list(cycles)
    nb_scores = []
    for fid in nb_ids:
        if fid in nb_chunks:
            nb_scores.append(se_score(emb.mat(nb_chunks[fid]), out_mats[rng.choice(all_cids)]))
    nb_scores = np.asarray(nb_scores)
    meta = {"n_served_rows": len(served), "n_cycles_with_voice": len(cycles), "dropped_rows_no_voice": dropped_no_voice,
            "n_units": len(units), "units_missing_fragment": missing, "T_emb_p99_nullA": T,
            "null_a_thresholds": thr, "null_a_n": int(len(nullA)),
            "null_a_mean": float(nullA.mean()), "null_b_n": int(len(nb_scores)),
            "null_b_rate_above_T": float((nb_scores >= T).mean()) if len(nb_scores) else None,
            "null_b_mean": float(nb_scores.mean()) if len(nb_scores) else None,
            "served_se_mean": float(np.mean([u["se"] for u in units])),
            "log_first_ts": min(float(r["ts"]) for r in served) if served else None,
            "log_last_ts": max(float(r["ts"]) for r in served) if served else None}
    with open(out_dir / "labels.jsonl", "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps(u) + "\n")
    (out_dir / "labels_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return units, meta


# --------------------------------------------------------------------------- judge stage (interim)
JUDGE_SYS = ("You rate how useful ONE remembered fragment would be to a mind that is about to think or speak about a "
             "given input. Answer with a single digit from 0 to 9 and nothing else. 0 = unrelated, 5 = somewhat "
             "relevant, 9 = exactly what is needed.")


def judge_user(inp, summary, frag):
    return (f"INPUT:\n{(inp or '')[:600]}\n\nSITUATION SUMMARY:\n{(summary or '')[:300]}\n\n"
            f"REMEMBERED FRAGMENT:\n{(frag or '')[:700]}\n\nUsefulness digit (0-9):")


def parse_digit(s):
    m = re.search(r"\d", s or "")
    return int(m.group(0)) if m else None


def hub_call(url, model, system, user, timeout=240):
    import urllib.request
    d = json.dumps({"model": model, "messages": [{"role": "system", "content": system},
                                                  {"role": "user", "content": user}],
                    "stream": False, "options": {"temperature": 0.0, "num_predict": 3}}).encode()
    r = urllib.request.urlopen(urllib.request.Request(url + "/api/chat", d, {"Content-Type": "application/json"}),
                               timeout=timeout)
    return json.loads(r.read())["message"]["content"]


def run_judge(url, model, max_units, call=None, data=None, out_dir=None, tag="falcon3"):
    data = data or DATA
    out_dir = out_dir or OUT
    call = call or (lambda s, u: hub_call(url, model, s, u))
    units = read_jsonl(out_dir / "labels.jsonl")
    perc = load_perception(data)
    db = open_db(data)
    frags = fetch_fragments(db, {u["fragment_id"] for u in units})
    db.close()
    cycles = sorted({u["cycle_id"] for u in units})
    random.Random(SEED).shuffle(cycles)  # any prefix is a random cycle sample
    path = out_dir / f"judge_scores_{tag}.jsonl"
    done = {(r["cycle_id"], r["fragment_id"]) for r in read_jsonl(path)} if path.exists() else set()
    by_cycle = {}
    for u in units:
        by_cycle.setdefault(u["cycle_id"], []).append(u)
    n_done = len(done)
    with open(path, "a", encoding="utf-8") as f:
        for cid in cycles:
            for u in by_cycle[cid]:
                if n_done >= max_units:
                    return n_done
                key = (cid, u["fragment_id"])
                if key in done:
                    continue
                p = perc.get(cid, {})
                t0 = time.time()
                try:
                    raw = call(JUDGE_SYS, judge_user(p.get("raw_input"), p.get("summary"), frags[u["fragment_id"]][0]))
                    err = None
                except Exception as e:
                    raw, err = None, type(e).__name__
                f.write(json.dumps({"cycle_id": cid, "fragment_id": u["fragment_id"], "raw": raw,
                                    "score": parse_digit(raw), "err": err, "sec": round(time.time() - t0, 1)}) + "\n")
                f.flush()
                n_done += 1
    return n_done


BATCH_SYS = ("You rate how useful each of several remembered fragments would be to a mind that is about to think or "
             "speak about a given input. For EACH fragment give one digit 0-9 (0 = unrelated, 5 = somewhat relevant, "
             "9 = exactly what is needed). Reply with only the digits, in order, separated by single spaces.")
BATCH_FRAG_CHARS = 320


def batch_user(inp, summary, frag_texts):
    nl = chr(10)
    lines = nl.join(f"[{i + 1}] {(t or '')[:BATCH_FRAG_CHARS].replace(nl, ' ')}" for i, t in enumerate(frag_texts))
    return (f"INPUT:{nl}{(inp or '')[:600]}{nl}{nl}SITUATION SUMMARY:{nl}{(summary or '')[:300]}{nl}{nl}"
            f"REMEMBERED FRAGMENTS:{nl}{lines}{nl}{nl}"
            f"Digits for fragments 1 to {len(frag_texts)}, space separated:")


def hub_call_n(url, model, system, user, n_pred, timeout=600):
    import urllib.request
    d = json.dumps({"model": model, "messages": [{"role": "system", "content": system},
                                                  {"role": "user", "content": user}],
                    "stream": False, "options": {"temperature": 0.0, "num_predict": n_pred}}).encode()
    r = urllib.request.urlopen(urllib.request.Request(url + "/api/chat", d, {"Content-Type": "application/json"}),
                               timeout=timeout)
    return json.loads(r.read())["message"]["content"]


def run_judge_batch(url, model, max_cycles, call=None, data=None, out_dir=None, tag="falcon3batch"):
    """Listwise variant: one call per cycle scoring all its served fragments (fragment order shuffled per cycle, seed
    fixed, so list position is not the served position). Output rows go to judge_scores_<tag>.jsonl in the same
    format as the pointwise runner. A reply whose digit count != number of fragments is an error row (score None)."""
    data = data or DATA
    out_dir = out_dir or OUT
    units = read_jsonl(out_dir / "labels.jsonl")
    perc = load_perception(data)
    db = open_db(data)
    frags = fetch_fragments(db, {u["fragment_id"] for u in units})
    db.close()
    cycles = sorted({u["cycle_id"] for u in units})
    random.Random(SEED).shuffle(cycles)
    by_cycle = {}
    for u in units:
        by_cycle.setdefault(u["cycle_id"], []).append(u)
    path = out_dir / f"judge_scores_{tag}.jsonl"
    done = {r["cycle_id"] for r in read_jsonl(path)} if path.exists() else set()
    call = call or (lambda s, u, n: hub_call_n(url, model, s, u, n))
    n_done = 0
    with open(path, "a", encoding="utf-8") as f:
        for cid in cycles:
            if len(done) + n_done >= max_cycles:
                break
            if cid in done:
                continue
            us = list(by_cycle[cid])
            random.Random(SEED + zlib.crc32(cid.encode()) % 1000003).shuffle(us)
            p = perc.get(cid, {})
            t0 = time.time()
            try:
                raw = call(BATCH_SYS, batch_user(p.get("raw_input"), p.get("summary"),
                                                 [frags[u["fragment_id"]][0] for u in us]), 3 * len(us) + 8)
                err = None
            except Exception as e:
                raw, err = None, type(e).__name__
            digs = re.findall(r"\d", raw or "")
            ok = err is None and len(digs) == len(us)
            for i, u in enumerate(us):
                f.write(json.dumps({"cycle_id": cid, "fragment_id": u["fragment_id"],
                                    "raw": raw if i == 0 else None, "score": int(digs[i]) if ok else None,
                                    "err": err or (None if ok else f"count_{len(digs)}_vs_{len(us)}"),
                                    "sec": round(time.time() - t0, 1) if i == 0 else None}) + chr(10))
            f.flush()
            n_done += 1
    return len(done) + n_done


# --------------------------------------------------------------------------- report stage
def _rate(rows, key="ue"):
    k = sum(1 for r in rows if r[key])
    n = len(rows)
    lo, hi = wilson(k, n)
    return {"n": n, "k": k, "rate": round(k / n, 4) if n else None, "ci": [lo, hi]}


def group_rates(units, field, keys=("u4", "ue", "ue_noecho", "ub", "ua")):
    out = {}
    vals = sorted({str(u[field]) for u in units})
    for v in vals:
        rows = [u for u in units if str(u[field]) == v]
        out[v] = {k: _rate(rows, k) for k in keys}
    return out


def build_report(out_dir=None):
    out_dir = out_dir or OUT
    units = read_jsonl(out_dir / "labels.jsonl")
    meta = json.loads((out_dir / "labels_meta.json").read_text(encoding="utf-8"))
    for u in units:
        u["ue_noecho"] = bool(u["ue"] and not u["u4"])
        u["ub"] = bool(u["ue"] and u["u4"])
        u["ua"] = bool(u["ue"] or u["u4"])
    res = {"meta": meta}
    keys = ("u4", "ue", "ue_noecho", "ub", "ua", "ue95", "ue999")
    res["overall"] = {k: _rate(units, k) for k in keys}
    res["by_origin"] = group_rates(units, "origin", keys[:5])
    res["by_input_type"] = group_rates(units, "input_type", keys[:5])
    combo = {}
    for u in units:
        combo.setdefault(f"{u['origin']}|{u['input_type']}", []).append(u)
    res["by_origin_x_input"] = {k: {kk: _rate(v, kk) for kk in ("u4", "ue")} for k, v in sorted(combo.items())
                                if len(v) >= 30}
    # per-cycle
    per = {}
    for u in units:
        d = per.setdefault(u["cycle_id"], {"n": 0, "u4": 0, "ue": 0, "type": u["input_type"]})
        d["n"] += 1
        d["u4"] += u["u4"]
        d["ue"] += u["ue"]
    pc = list(per.values())
    res["per_cycle"] = {
        "cycles": len(pc), "mean_served": round(float(np.mean([d["n"] for d in pc])), 2),
        "mean_used_u4": round(float(np.mean([d["u4"] for d in pc])), 3),
        "mean_used_ue": round(float(np.mean([d["ue"] for d in pc])), 3),
        "share_cycles_none_u4": round(float(np.mean([d["u4"] == 0 for d in pc])), 3),
        "share_cycles_none_ue": round(float(np.mean([d["ue"] == 0 for d in pc])), 3),
        "by_type": {t: {"cycles": sum(1 for d in pc if d["type"] == t),
                        "mean_used_ue": round(float(np.mean([d["ue"] for d in pc if d["type"] == t])), 3),
                        "mean_used_u4": round(float(np.mean([d["u4"] for d in pc if d["type"] == t])), 3)}
                    for t in sorted({d["type"] for d in pc})}}
    # by position quartile of the served list, and by logged relevance bin
    posq = {}
    for u in units:
        q = min(3, int(4 * u["pos"] / max(u["n"], 1)))
        posq.setdefault(f"pos_q{q + 1}", []).append(u)
    res["by_position_quartile"] = {k: {kk: _rate(v, kk) for kk in ("u4", "ue")} for k, v in sorted(posq.items())}
    relbin = {}
    for u in units:
        r = u.get("relevance") or 0.0
        b = "rel_0" if r <= 0 else ("rel_0-0.4" if r < 0.4 else ("rel_0.4-0.5" if r < 0.5 else "rel_0.5+"))
        relbin.setdefault(b, []).append(u)
    res["by_logged_relevance"] = {k: {kk: _rate(v, kk) for kk in ("u4", "ue")} for k, v in sorted(relbin.items())}
    # AUC of logged retrieval relevance and of SE-free controls vs labels
    cl = [u["cycle_id"] for u in units]
    res["auc_logged_relevance"] = {}
    for lab in ("u4", "ue"):
        y = [u[lab] for u in units]
        a = auc([u.get("relevance") or 0.0 for u in units], y)
        res["auc_logged_relevance"][lab] = {"auc": None if a is None else round(a, 4),
                                            "ci": list(auc_cluster_boot([u.get("relevance") or 0.0 for u in units],
                                                                        y, cl, 500))}
    # logged relevance within origin strata (is the 0.73 just the lived-origin gradient?)
    res["auc_logged_relevance_within"] = {}
    for name, sel in (("lived", lambda u: u["origin"] == "lived"), ("non_lived", lambda u: u["origin"] != "lived")):
        rows = [u for u in units if sel(u)]
        res["auc_logged_relevance_within"][name] = {}
        for lab in ("u4", "ue"):
            y = [u[lab] for u in rows]
            sc = [u.get("relevance") or 0.0 for u in rows]
            a = auc(sc, y)
            res["auc_logged_relevance_within"][name][lab] = {
                "n": len(rows), "n_pos": int(sum(y)), "auc": None if a is None else round(a, 4),
                "ci": list(auc_cluster_boot(sc, y, [u["cycle_id"] for u in rows], 500))}
    # label agreement
    n = len(units)
    a = sum(1 for u in units if u["u4"] and u["ue"])
    res["label_overlap"] = {"both": a, "u4_only": sum(1 for u in units if u["u4"] and not u["ue"]),
                            "ue_only": sum(1 for u in units if u["ue"] and not u["u4"]),
                            "neither": sum(1 for u in units if not u["u4"] and not u["ue"]), "n": n}
    # judge arm(s)
    res["judge"] = {}
    for jp in sorted(out_dir.glob("judge_scores_*.jsonl")):
        tag = jp.stem.replace("judge_scores_", "")
        sc = {(r["cycle_id"], r["fragment_id"]): r for r in read_jsonl(jp)}
        rows = [u for u in units if (u["cycle_id"], u["fragment_id"]) in sc and sc[(u["cycle_id"], u["fragment_id"])]["score"] is not None]
        errs = sum(1 for r in sc.values() if r["score"] is None)
        if not rows:
            res["judge"][tag] = {"n": 0, "errors": errs}
            continue
        s = [sc[(u["cycle_id"], u["fragment_id"])]["score"] for u in rows]
        cl = [u["cycle_id"] for u in rows]
        d = {"n": len(rows), "errors": errs, "cycles": len(set(cl)),
             "score_hist": {str(k): s.count(k) for k in sorted(set(s))}}
        for lab in ("u4", "ue", "ue_noecho", "ub", "ua"):
            y = [u[lab] for u in rows]
            av = auc(s, y)
            d[f"auc_{lab}"] = {"auc": None if av is None else round(av, 4), "n_pos": int(sum(y)),
                               "ci": list(auc_cluster_boot(s, y, cl))}
        d["auc_logged_relevance_same_rows_ue"] = (lambda av: None if av is None else round(av, 4))(
            auc([u.get("relevance") or 0.0 for u in rows], [u["ue"] for u in rows]))
        res["judge"][tag] = d
    # 2-slot ceiling
    rates_o = {k: v["ue"]["rate"] for k, v in res["by_origin"].items() if v["ue"]["n"] >= 30}
    p_all = res["overall"]["ue"]["rate"]
    res["ceiling_ue"] = {"p_overall": p_all, "best_origin": max(rates_o, key=rates_o.get) if rates_o else None,
                         "p_best_origin": max(rates_o.values()) if rates_o else None,
                         "max_abs_shift_2_slots_swap_used_per_cycle": round(2 * (max(rates_o.values()) if rates_o else 0), 3)}
    # shift implied by the J-3163 pilot origin movement (partial: only the five origins the doc lists)
    added = {"lived": 85, "standing_insight": 82, "consolidation": 77, "inner_thought": 31, "understanding": 38}
    dropped = {"lived": 115, "standing_insight": 70, "consolidation": 86, "inner_thought": 33, "understanding": 34}
    sa, sd = sum(added.values()), sum(dropped.values())
    per_slot = 0.0
    missing = []
    for o in added:
        r = rates_o.get(o)
        if r is None:
            missing.append(o)
            continue
        per_slot += (added[o] / sa - dropped[o] / sd) * r
    res["ceiling_ue"]["pilot_origin_mix_shift_per_swapped_slot"] = round(per_slot, 4)
    res["ceiling_ue"]["pilot_origin_mix_shift_per_cycle_at_2.25_slots"] = round(per_slot * 2.25, 4)
    res["ceiling_ue"]["pilot_origins_missing_rate"] = missing
    # same ceiling computed with the 4-gram baseline label, so the bound is not an artefact of one label
    rates_o4 = {k: v["u4"]["rate"] for k, v in res["by_origin"].items() if v["u4"]["n"] >= 30}
    per4 = sum((added[o] / sa - dropped[o] / sd) * rates_o4.get(o, 0.0) for o in added)
    res["ceiling_u4"] = {"p_overall": res["overall"]["u4"]["rate"],
                         "p_best_origin": max(rates_o4.values()) if rates_o4 else None,
                         "max_abs_shift_2_slots_swap_used_per_cycle": round(2 * (max(rates_o4.values()) if rates_o4 else 0), 3),
                         "pilot_origin_mix_shift_per_swapped_slot": round(per4, 4),
                         "pilot_origin_mix_shift_per_cycle_at_2.25_slots": round(per4 * 2.25, 4)}
    (out_dir / "results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("labels")
    j = sub.add_parser("judge")
    j.add_argument("--url", default="http://127.0.0.1:11440")
    j.add_argument("--model", default="falcon3:7b")
    j.add_argument("--tag", default="falcon3")
    j.add_argument("--max-units", type=int, default=400)
    jb = sub.add_parser("judge-batch")
    jb.add_argument("--url", default="http://127.0.0.1:11440")
    jb.add_argument("--model", default="falcon3:7b")
    jb.add_argument("--tag", default="falcon3batch")
    jb.add_argument("--max-cycles", type=int, default=60)
    sub.add_parser("report")
    a = ap.parse_args(argv)
    if a.cmd == "labels":
        _u, meta = build_labels()
        print(json.dumps(meta, indent=1))
    elif a.cmd == "judge":
        n = run_judge(a.url, a.model, a.max_units, tag=a.tag)
        print("judge units scored:", n)
    elif a.cmd == "judge-batch":
        print("cycles judged:", run_judge_batch(a.url, a.model, a.max_cycles, tag=a.tag))
    else:
        r = build_report()
        print(json.dumps(r, indent=1)[:6000])


if __name__ == "__main__":
    main()
