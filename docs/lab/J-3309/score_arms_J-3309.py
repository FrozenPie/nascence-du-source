"""J-3309 step 2: score arms plain / A05 / A025 / B / N on the frozen 100 queries.
Replicates core/memory/store.py retrieve() fast-path ranking (TIER_SLOTS 2/3/4 with spare cascade, recency x
seed weight, cos on the same MiniLM embedder), recency-guarantee rows EXCLUDED. Climate warp (bias_vec) is not
logged so it is NOT applied (same for every arm). Pilot code cited: J-3163 scratchpad pilot_J-3163.py (not found on
disk this run; logic rebuilt from store.py lines 1989-2213, not from the pilot).
Reads the live DB with mode=ro only. lab_env.isolate(db='empty') redirects any store write into data/_lab."""
import sys, json, time, sqlite3, random, math, collections
sys.path.insert(0, r"C:\Nascence"); sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
import numpy as np
from core.memory import store as S          # core BEFORE lab_env
from nodes.memory_router_node import MemoryRouterNode
import lab_env
Q = json.load(open(r"C:\Nascence\docs\lab\J-3309\frozen_queries_J-3309.json", encoding="utf-8"))
OUT = r"C:\Nascence\docs\lab\J-3309\arms_J-3309.json"
JUNK = set(MemoryRouterNode._JUNK_ENTITY_TOKENS) | {"key entities", "the_entity", "the entity", "the_person", "the_world"}
def clean_keys(keys):
    out = []
    for k in keys:
        n = " ".join(str(k).replace("_", " ").lower().split()).strip(" .\"'")
        if n and n not in JUNK: out.append(str(k))
    return out
with lab_env.isolate(db="empty") as lab_dir:
    uri = "file:" + r"C:/Nascence/data/memory/nascence.db".replace("\\", "/") + "?mode=ro"
    cn = sqlite3.connect(uri, uri=True)
    rows = cn.execute("SELECT fragment_id, layer, timestamp, origin, embedding " + S._POOL_SQL_WHERE).fetchall()
    cn.close()
    print("pool rows", len(rows))
    ids = [r[0] for r in rows]
    layer = np.array([r[1] if r[1] in ("archive", "semantic", "episodic") else ("working" if r[1] == "working" else "episodic") for r in rows])
    ts = np.array([r[2] for r in rows], dtype=np.float64)
    origin = np.array([r[3] for r in rows])
    ok = np.array([bool(r[4]) and len(r[4]) == 384 * 4 for r in rows])
    mat = np.zeros((len(rows), 384), dtype=np.float32)
    for i, r in enumerate(rows):
        if ok[i]: mat[i] = np.frombuffer(r[4], dtype=np.float32)
    print("rows without usable embedding:", int((~ok).sum()))
    now = time.time(); age = (now - ts) / 86400.0
    is_seed = origin == "seed"
    sw = np.ones(len(rows))
    for i in np.where(is_seed)[0]: sw[i] = S._seed_weight(ts[i])
    def rec(tb):
        if tb == "recent": return 1.0 + 0.2 * np.maximum(0.0, 1.0 - age / 7.0)
        if tb == "distant": return 1.0 + 0.1 * np.minimum(age / 7.0, 1.0)
        return np.ones(len(rows))
    tier_idx = {t: np.where(layer == t)[0] for t in ("archive", "semantic", "episodic")}
    def rank(vec, tb):
        sims = mat @ vec
        sims[~ok] = 0.0
        sc_r = sims * rec(tb) * sw
        sc_a = sims * 1.0                      # archive: time_bias 'all', no seed weight
        spare = 0; res = []
        for tier, n in S.TIER_SLOTS.items():
            n += spare; spare = 0
            ix = tier_idx[tier]
            sc = sc_a[ix] if tier == "archive" else sc_r[ix]
            order = np.argsort(-sc, kind="stable")[:max(16, n)]
            take = [(int(ix[o]), float(sc[o]), tier) for o in order[:n]]
            res.extend(take)
            if tier != "episodic": spare = n - len(take)
        return res
    def norm(v):
        n = np.linalg.norm(v); return v / n if n > 0 else v
    qvec, kvec_raw = [], []
    kstr = []
    for q in Q:
        text = (q["raw_input"] + " " + q["summary"]) if q["summary"] else q["raw_input"]
        qvec.append(S._embed(text))
        ks = clean_keys(q["episodic_keys"] + q["semantic_keys"])
        kstr.append(ks)
        kvec_raw.append(S._embed(", ".join(ks)) if ks else None)
    # derangement for N (keys shuffled across queries; only among queries that have non-empty keys)
    rng = random.Random(3163)
    have = [i for i in range(len(Q)) if kvec_raw[i] is not None]
    while True:
        perm = have[:]; rng.shuffle(perm)
        if all(a != b for a, b in zip(have, perm)): break
    shuf = dict(zip(have, perm))
    out = []
    for i, q in enumerate(Q):
        tb = q["time_bias"]; qv = qvec[i]; kv = kvec_raw[i]
        plain = rank(qv, tb)
        pids = {x[0] for x in plain}
        rec_ = {"cycle_id": q["cycle_id"], "input_type": q["input_type"], "n_clean_keys": len(kstr[i]),
                "keys_used": kstr[i], "plain": plain}
        if kv is None:
            rec_["no_keys"] = True; out.append(rec_); continue
        for name, a in (("A05", 0.5), ("A025", 0.25)):
            rec_[name] = rank(norm(qv + a * kv), tb)
        # arm B: 2 best key-only rows (non-archive) not in plain replace 2 lowest-scoring non-archive plain slots
        ksims = (mat @ kv); ksims[~ok] = 0.0
        ksc = ksims * rec(tb) * sw
        cand = np.where((layer != "archive") & (layer != "working"))[0]
        order = cand[np.argsort(-ksc[cand], kind="stable")]
        add = []
        for j in order:
            if int(j) not in pids: add.append((int(j), float(ksc[j]), str(layer[j])))
            if len(add) == 2: break
        na = sorted([x for x in plain if x[2] != "archive"], key=lambda x: x[1])
        drop = {x[0] for x in na[:2]}
        rec_["B"] = [x for x in plain if x[0] not in drop] + add
        kvn = kvec_raw[shuf[i]]
        rec_["N"] = rank(norm(qv + 0.5 * kvn), tb)
        rec_["N_from"] = Q[shuf[i]]["cycle_id"]
        rec_["cos_q_k"] = float(qv @ kv)
        out.append(rec_)
    # convert idx -> fragment ids
    def conv(lst): return [{"id": ids[x[0]], "score": round(x[1], 5), "tier": x[2]} for x in lst]
    for r in out:
        for k in ("plain", "A05", "A025", "B", "N"):
            if k in r: r[k] = conv(r[k])
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    # summary
    for arm in ("A05", "A025", "B", "N"):
        ch = [9 - len({x["id"] for x in r["plain"]} & {x["id"] for x in r[arm]}) for r in out if arm in r]
        print(arm, "mean slots changed %.2f" % (sum(ch) / len(ch)), "zero-change", sum(1 for c in ch if c == 0), "of", len(ch))
    print("queries without clean keys:", sum(1 for r in out if r.get("no_keys")))
