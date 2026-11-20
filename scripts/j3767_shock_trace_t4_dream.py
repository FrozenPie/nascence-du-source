# J-3767 trace, committed by J-4010 unchanged from the scratchpad original (main trace: T4 per-exposure, dream day_material, world-ground reconstruction, wandering; --out DIR --days N --embed).
# READ-ONLY. Imports scripts/j2916_shock_trace.py by path and reads the live data dir. Re-run for J-3764 after pursuit lookup retirement.
"""J-3767: shock pages -> T4 authoring, dream world-ground, wandering pools. READ-ONLY.
Reuses scripts/j2916_shock_trace.py (imported by path, no bytecode written). Output json to --out (scratchpad)."""
import sys, json, re, argparse, collections, statistics, bisect, datetime as dt
from pathlib import Path
sys.dont_write_bytecode = True
import importlib.util
spec = importlib.util.spec_from_file_location("j2916", r"C:\Nascence\scripts\j2916_shock_trace.py")
J = importlib.util.module_from_spec(spec); spec.loader.exec_module(J)
import numpy as np
try:
    from scipy.stats import fisher_exact
except Exception:
    fisher_exact = None

NASC = Path(r"C:\Nascence"); D = NASC / "data"; H = 3600.0
SHIFTS = [-14, -7, 7, 14]


def fisher(a, n1, b, n2):
    if not fisher_exact or not n1 or not n2:
        return None
    return round(float(fisher_exact([[a, n1 - a], [b, n2 - b]])[1]), 5)


def jl(path):
    out = []
    for l in open(path, encoding="utf-8", errors="replace"):
        try:
            out.append(json.loads(l))
        except Exception:
            pass
    return out


def tot(stream, recs, kws, lo, hi, shift_d=0):
    vals = []
    for r in recs:
        t = r["ts"] + shift_d * 86400
        vals.append(sum(J.count(stream, t, kws[r["id"]], lo, hi).values()))
    return vals


def block(stream, shocks, controls, kws, end):
    """48h post / pre / shifted null for shocks vs pursuit controls (only pages with a full 48h)."""
    S = [r for r in shocks if r["ts"] + 48 * H <= end]
    C = [r for r in controls if r["ts"] + 48 * H <= end]
    post_s, post_c = tot(stream, S, kws, 0, 48), tot(stream, C, kws, 0, 48)
    pre_s, pre_c = tot(stream, S, kws, -48, 0), tot(stream, C, kws, -48, 0)
    sh = []
    for d in SHIFTS:
        sh += tot(stream, S, kws, 0, 48, d)
    f = lambda v: J.fmt_rate(v)
    return dict(n_shock=len(S), n_ctrl=len(C), post_shock=f(post_s), post_ctrl=f(post_c), pre_shock=f(pre_s),
                pre_ctrl=f(pre_c), shifted_null_shock=f(sh),
                fisher_ge1_shock_vs_ctrl=fisher(sum(v >= 1 for v in post_s), len(post_s), sum(v >= 1 for v in post_c), len(post_c)))


def merge_events(items, gap=180):
    items = sorted(items, key=lambda x: x[0]); ev = []
    for ts, tx in items:
        if ev and ts - ev[-1][0] <= gap:
            ev[-1][1] += " " + tx
        else:
            ev.append([ts, tx])
    return ev


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--out", type=Path, required=True); ap.add_argument("--embed", type=int, default=1)
    a = ap.parse_args()
    a.db = NASC / "data" / "memory" / "nascence.db"; a.data = D
    B = J.build(a)
    start, end, streams = B["start"], B["end"], B["streams"]
    shocks, controls = B["shocks"], B["controls"]
    df, n = J.background_df(streams)
    kws = {r["id"]: J.keywords(r, df, n) for r in shocks + controls}
    res = dict(days=a.days, n_shocks=len(shocks), n_controls=len(controls), window=[start, end])

    # world rows (feed): ts, class
    cls_by_ts = {}
    for r in shocks: cls_by_ts[r["ts"]] = ("shock", r)
    for r in controls: cls_by_ts[r["ts"]] = ("pursuit", r)
    world = []   # (ts, class, rec)
    for fid, ts, imp, rel, rc, origin, content, layer, dfrom in B["rows"]:
        if origin in ("study", "reading", "research"):
            c = cls_by_ts.get(ts)
            world.append((ts, c[0] if c else "other", c[1] if c else None))
    world.sort(key=lambda x: x[0]); wts = [w[0] for w in world]

    # ---------------- T4 ----------------
    t4items = []
    for r in jl(D / "logs" / "t4_chain_trace.jsonl"):
        t4items.append((float(r["ts"]), " ".join(str(r.get(k) or "") for k in ("delta", "evidence", "self_concept", "arc_entry"))))
    for r in jl(D / "logs" / "t4_emissary_judge.jsonl"):
        t4items.append((float(r["ts"]), " ".join(str(r.get(k) or "") for k in ("candidate", "evidence"))))
    for r in jl(D / "narrative_quality_log.jsonl"):
        if str(r.get("kind", "")).startswith("t4_") and r.get("ts", 0) > start - 21 * 86400:
            t4items.append((float(r["ts"]), r.get("text_head") or ""))
    ev = merge_events([x for x in t4items if x[0] >= start - 21 * 86400])
    t4s = J.Stream("T4"); [t4s.add(t, x) for t, x in ev]; t4s.seal()
    res["t4_events_total"] = len(ev); res["t4_events_in_window"] = sum(1 for t, _ in ev if t >= start)
    res["t4_post_block"] = block(t4s, shocks, controls, kws, end)
    # exposure: newest-6 world rows at each event time (>= start)
    expo = collections.Counter(); cited = collections.Counter(); ev_with_shock_in_view = 0; evn = 0
    for t, tx in ev:
        if t < start: continue
        evn += 1
        i = bisect.bisect_right(wts, t); view = world[max(0, i - 6):i]
        tk = J.toks(tx.lower()); txl = tx.lower()
        has = False
        for ts_, c, rec in view:
            expo[c] += 1
            if c == "shock": has = True
            if rec is not None and J.cites(txl, tk, *kws[rec["id"]]):
                cited[c] += 1
        ev_with_shock_in_view += has
    res["t4_exposure"] = dict(events=evn, events_with_shock_in_newest6=ev_with_shock_in_view,
                              rows_in_view=dict(expo), cited=dict(cited),
                              rate_shock=(cited["shock"], expo["shock"]), rate_pursuit=(cited["pursuit"], expo["pursuit"]),
                              fisher=fisher(cited["shock"], expo["shock"], cited["pursuit"], expo["pursuit"]))
    # authored subset: events from chain_trace with authored True and shock titles named
    ct = [r for r in jl(D / "logs" / "t4_chain_trace.jsonl")]
    res["t4_chain_trace_rows"] = len(ct); res["t4_chain_authored"] = sum(1 for r in ct if str(r.get("authored")) == "True")
    # shock title/word occurrences (whole-store 'T4' text) for any shock in authored self_concept texts, by tier
    tier = collections.Counter(); hits = []
    for t, tx in ev:
        txl = tx.lower(); tk = J.toks(txl)
        for r in shocks:
            if 0 <= t - r["ts"] <= 48 * H:
                v = J.cites(txl, tk, *kws[r["id"]])
                if v:
                    tier[v] += 1; hits.append((round((t - r["ts"]) / H, 1), v, r["title"]))
    res["t4_hits_by_tier"] = dict(tier); res["t4_hits_sample"] = hits[:25]

    # ---------------- wandering ----------------
    wr = [r for r in jl(D / "wandering_log.jsonl") if r.get("ts", 0) >= start - 21 * 86400]
    WORLD = ("reading", "research", "study", "essay", "understanding")
    tab = collections.Counter(); wnon = J.Stream("wand_nonworld"); wshock_rows = []
    pages_hits = collections.defaultdict(list)   # rec id -> list of (dt_h, via)
    title_idx = {}
    for r in shocks + controls:
        title_idx.setdefault(r["title"].lower(), []).append(r)
    for r in wr:
        tx = r.get("text") or ""; o = r.get("origin"); via = r.get("via"); ts = r["ts"]
        if o in WORLD:
            m = re.match(r"\[Looked up: '(.*?)' \((.*?)\)\]", tx)
            if m:
                c = "shock" if m.group(2).startswith("external shock") else "pursuit"
            else:
                c = "other_world"
            if ts >= start: tab[(via, o, c)] += 1
            if m:
                for rec in title_idx.get(m.group(1).lower(), []):
                    if abs(ts - rec["ts"]) < 3 * 86400 or True:
                        pages_hits[rec["id"]].append((ts - rec["ts"], via))
        else:
            wnon.add(ts, tx)
    wnon.seal()
    res["wander_rows_window"] = sum(1 for r in wr if r["ts"] >= start)
    res["wander_world_table"] = {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in sorted(tab.items(), key=lambda x: -x[1])}
    # per-page appearances within 48h of storage and total after
    def app(recs, hrs):
        return [sum(1 for dtt, v in pages_hits[r["id"]] if 0 <= dtt <= hrs * H) for r in recs if r["ts"] + hrs * H <= end]
    for nm, hrs in (("48h", 48), ("30d", 24 * 30)):
        s, c = app(shocks, hrs), app(controls, hrs)
        res[f"wander_pool_appearances_{nm}"] = dict(shock=J.fmt_rate(s), pursuit=J.fmt_rate(c),
                                                     fisher_ge1=fisher(sum(v >= 1 for v in s), len(s), sum(v >= 1 for v in c), len(c)))
    # share: shock fraction among research-origin rows stored in window vs among research-origin wandering world rows
    store_share = (len(shocks), len(shocks) + len(controls))
    wsh = sum(v for k, v in tab.items() if k[2] == "shock"); wpu = sum(v for k, v in tab.items() if k[2] == "pursuit")
    res["wander_research_share"] = dict(stored_shock=store_share[0], stored_all=store_share[1], wander_shock=wsh, wander_pursuit=wpu)
    res["wander_nonworld_block"] = block(wnon, shocks, controls, kws, end)

    # ---------------- dreams ----------------
    dr = [r for r in jl(D / "dream_log.jsonl") if r.get("ts", 0) >= start - 21 * 86400]
    ds = J.Stream("dream")
    for r in dr:
        tx = " ".join([str(r.get("narrative") or ""), str(r.get("final_narrative") or ""), " ".join(r.get("symbols") or []),
                       str(r.get("tension_source") or ""), str(r.get("final_unresolved_core") or "")])
        ds.add(float(r["ts"]), tx)
    ds.seal()
    res["dreams_window"] = sum(1 for r in dr if r["ts"] >= start)
    res["dream_post_block"] = block(ds, shocks, controls, kws, end)
    # id-level: seed fragment ids that are shocks
    sid = {}
    for fid, ts, imp, rel, rc, origin, content, layer, dfrom in B["rows"]:
        pass
    shock_ids = {r["id"] for r in shocks}; ctrl_ids = {r["id"] for r in controls}
    n_seed_shock = sum(1 for r in dr if r["ts"] >= start and shock_ids & set((r.get("seed") or {}).get("fragment_ids") or []))
    n_seed_ctrl = sum(1 for r in dr if r["ts"] >= start and ctrl_ids & set((r.get("seed") or {}).get("fragment_ids") or []))
    res["dream_seed_id_level"] = dict(dreams_with_shock_in_seed=n_seed_shock, dreams_with_pursuit_in_seed=n_seed_ctrl)
    res["dream_tension_source_counts"] = dict(collections.Counter("+".join(r.get("material_sources") or []) for r in dr if r["ts"] >= start))
    lab = [(r, (r.get("seed") or {}).get("tension_labels") or []) for r in dr if r["ts"] >= start]
    res["dreams_with_tension_labels"] = sum(1 for r, l in lab if l)
    # world-ground reconstruction
    if a.embed:
        import sqlite3
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
        c = sqlite3.connect(f"file:{(D/'memory'/'nascence.db').as_posix()}?mode=ro&immutable=1", uri=True)
        pool = c.execute("select fragment_id,timestamp,origin,content,embedding from memory_fragments where origin in "
                         "('reading','study','research') and embedding is not null and timestamp>=? order by timestamp desc",
                         (start - 40 * 86400,)).fetchall()
        pts = [p[1] for p in pool][::-1]; pool = pool[::-1]       # ascending
        picks = collections.Counter(); pool_share = collections.Counter(); n_with = 0; cite_by = collections.Counter(); n_by = collections.Counter()
        sample = []
        for r, labels in lab:
            if not labels: continue
            t0 = float(str(r.get("dream_id", "dream_0")).split("_")[-1]) if r.get("dream_id") else r["ts"]
            i = bisect.bisect_right(pts, t0); win = pool[max(0, i - 400):i]
            if not win: continue
            vecs = np.stack([np.frombuffer(p[4], dtype=np.float32) for p in win])
            dtx = " ".join([str(r.get("narrative") or ""), str(r.get("final_narrative") or ""), " ".join(r.get("symbols") or [])]).lower()
            dtk = J.toks(dtx)
            for lbl in labels[:3]:       # _build uses n tensions; one ground each
                lv = m.encode(lbl, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
                sims = vecs @ lv; j = int(np.argmax(sims)); best = float(sims[j])
                n_with += 1
                for p in win:
                    pool_share["shock" if p[0] in shock_ids else "pursuit" if p[0] in ctrl_ids else "other"] += 1
                if best < 0.22: picks["below_threshold"] += 1; continue
                pid = win[j][0]
                k = "shock" if pid in shock_ids else "pursuit" if pid in ctrl_ids else "other"
                picks[k] += 1; n_by[k] += 1
                if k != "other":
                    rec = next(x for x in (shocks + controls) if x["id"] == pid)
                    cv = J.cites(dtx, dtk, *kws[rec["id"]])
                    if cv: cite_by[k] += 1
                    if k == "shock" and len(sample) < 12: sample.append((rec["title"], round(best, 3), cv))
        res["dream_ground_reconstruction"] = dict(tension_grounds_scored=n_with, picks=dict(picks), pool_rows_by_class=dict(pool_share),
                                                  dream_cites_its_ground=dict(cite_by), n_ground=dict(n_by), shock_ground_sample=sample)
    args_out = a.out / f"j3767_results_{a.days}d.json"
    args_out.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print("wrote", args_out)


main()
