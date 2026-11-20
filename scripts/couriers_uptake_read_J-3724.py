"""J-3724: read-only read of courier delivery uptake (precondition for U1 stage 3 of
docs/reviews/ghost_memory_index_chord_echo_J-3247.md).  Reads data/couriers_log.jsonl, data/memory/nascence.db (mode=ro),
data/monologue_log.jsonl.  Writes NOTHING to data/.
Usage: python scripts/couriers_uptake_read_J-3724.py [--root C:/Nascence] [--out report.md]

Measures FIXED BEFORE LOOKING:
 (1) n_candidates per route: min/median/p90/max, share at cap (20000), share <=10.
 (2) uptake: for each delivered row, thoughts in (ts, ts+WINDOW_S]; distinctive tokens = lowercase alpha words len>=5 of the
     delivered text (first 180 chars, as shown), minus stopwords, minus any token in >DF_CUT of all thoughts. UPTAKE = some thought
     shares >=2 distinctive tokens with the fragment. Nulls: (a) pre-window (ts-WINDOW_S, ts] same fragment; (b) permutation: the
     same thoughts against 30 other delivered rows' fragments (mean rate).
 (3) chord first-order: present tuple = fragment_context row nearest in time to the delivery (within 20 min); pool = same WHERE as
     the route (capped 20000, arbitrary subset when capped); chord score = rarity-weighted overlap (core.ghost_tuples.MemoryIndex
     formula, df over the whole fragment_context). Report percentile of the random pick in the pool's chord ranking.
"""
import argparse, json, math, re, sqlite3, statistics, sys, time, bisect, random, collections

WINDOW_S = 30 * 60
DF_CUT = 0.01
MIN_AGE = 3 * 86400.0
CAP = 20000
STOP = set("""about above after again against because before being below between could doing during every from further
having herself himself itself might more most myself other ought ourselves over same should since some such than that their
theirs them themselves then there these they this those through under until very were what when where which while whom
with would your yours yourself yourselves into only just like also still something nothing everything""".split())
TOK = re.compile(r"[a-z]{5,}")


def toks(s):
    return {t for t in TOK.findall((s or "").lower()) if t not in STOP}


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="C:/Nascence")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    root = a.root
    out = []
    P = out.append
    rows = [json.loads(l) for l in open(f"{root}/data/couriers_log.jsonl", encoding="utf-8") if l.strip()]
    deliv = [r for r in rows if r.get("fragment_id") and not r.get("would_have_delivered")]
    P(f"delivered rows with fragment_id: {len(deliv)} (of {len(rows)} total log rows); "
      f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(deliv[0]['ts']))} .. {time.strftime('%Y-%m-%d %H:%M', time.localtime(deliv[-1]['ts']))}")
    # ---- (1)
    P("\n## 1. n_candidates per route")
    byroute = collections.defaultdict(list)
    for r in deliv:
        byroute[r["route"]].append(r)
    for rt, rs in byroute.items():
        n = [r["n_candidates"] for r in rs if r.get("n_candidates") is not None]
        none = len(rs) - len(n)
        P(f"- {rt}: rows={len(rs)} n_candidates None={none} min={min(n)} median={statistics.median(n):.0f} p90={pct(n,.9)} max={max(n)}; "
          f"at cap({CAP})={sum(x>=CAP for x in n)} ({100*sum(x>=CAP for x in n)/len(n):.0f}%); <=10: {sum(x<=10 for x in n)}; <=100: {sum(x<=100 for x in n)}")
        key = "sound" if rt == "sound_echo" else "context"
        bys = collections.defaultdict(list)
        for r in rs:
            if r.get("n_candidates") is not None:
                bys[r.get(key)].append(r["n_candidates"])
        P(f"  per {key} (rows, median n): " + "; ".join(f"{k}({len(v)},{statistics.median(v):.0f})" for k, v in sorted(bys.items(), key=lambda kv: -len(kv[1]))[:12]))
    fids = [r["fragment_id"] for r in deliv]
    P(f"- distinct fragments delivered: {len(set(fids))} of {len(fids)} (repeats: {len(fids)-len(set(fids))})")
    conn = sqlite3.connect(f"file:{root}/data/memory/nascence.db?mode=ro", uri=True)
    text = {}
    for r in deliv:
        row = conn.execute("SELECT content FROM memory_fragments WHERE fragment_id=?", (r["fragment_id"],)).fetchone()
        text[r["fragment_id"]] = (row[0] or "")[:180] if row else ""
    P(f"- fragments not found in memory_fragments now: {sum(1 for f in fids if not text[f])}")
    # ---- (2)
    P("\n## 2. Uptake in the thought stream")
    th = []
    for l in open(f"{root}/data/monologue_log.jsonl", encoding="utf-8"):
        try:
            d = json.loads(l)
            th.append((float(d["ts"]), d.get("thought") or ""))
        except Exception:
            pass
    th.sort()
    tts = [t for t, _ in th]
    df = collections.Counter()
    ttok = []
    for _, s in th:
        k = toks(s)
        ttok.append(k)
        df.update(k)
    common = {t for t, c in df.items() if c > DF_CUT * len(th)}
    P(f"thoughts: {len(th)}; common tokens dropped (df>{DF_CUT:.0%}): {len(common)}")

    def win(lo, hi):
        return range(bisect.bisect_right(tts, lo), bisect.bisect_right(tts, hi))

    def uptake(ft, w):
        return max((len(ft & ttok[i]) for i in w), default=0)

    keys = [i for i in range(len(deliv))]
    ftok = {i: toks(text[deliv[i]["fragment_id"]]) - common for i in keys}
    wins = {i: win(deliv[i]["ts"], deliv[i]["ts"] + WINDOW_S) for i in keys}
    pre = {i: win(deliv[i]["ts"] - WINDOW_S, deliv[i]["ts"]) for i in keys}
    cov = sum(1 for i in keys if len(wins[i]) > 0)
    P(f"delivered rows with >=1 thought in the following {WINDOW_S//60} min: {cov}/{len(keys)}; median thoughts/window {statistics.median(len(wins[i]) for i in keys):.1f}; "
      f"median distinctive tokens/fragment {statistics.median(len(ftok[i]) for i in keys):.0f}")
    rnd = random.Random(7)
    for lab, thr in (("share>=1 distinctive token", 1), ("share>=2 (PRIMARY)", 2), ("share>=3", 3)):
        post = [uptake(ftok[i], wins[i]) >= thr for i in keys]
        prer = [uptake(ftok[i], pre[i]) >= thr for i in keys]
        perm = []
        for i in keys:
            others = rnd.sample([o for o in keys if o != i], 30)
            perm.append(sum(uptake(ftok[o], wins[i]) >= thr for o in others) / 30)
        P(f"- {lab}: post-window {sum(post)}/{len(keys)} ({100*sum(post)/len(keys):.1f}%); pre-window null {sum(prer)}/{len(keys)} ({100*sum(prer)/len(keys):.1f}%); "
          f"permuted-fragment null {100*statistics.mean(perm):.1f}%")
    P("per route (PRIMARY >=2): " + "; ".join(
        f"{rt}: post {sum(uptake(ftok[i],wins[i])>=2 for i in keys if deliv[i]['route']==rt)}/{len(rs)}, pre {sum(uptake(ftok[i],pre[i])>=2 for i in keys if deliv[i]['route']==rt)}"
        for rt, rs in byroute.items()))
    for i in [i for i in keys if uptake(ftok[i], wins[i]) >= 2][:6]:
        best = max((ftok[i] & ttok[j] for j in wins[i]), key=len)
        P(f"  hit: {deliv[i]['route']} {deliv[i].get('sound') or deliv[i].get('context')} shared={sorted(best)}")
    # ---- (3)
    P("\n## 3. First-order chord vs random pick")
    sys.path.insert(0, root)
    from core.ghost_tuples import _tuple_tags  # pure function
    cols = "fragment_id, place, weather, tide_level, sounds, standpoint, warmth, cat_at, tuple_ts"
    dfc = collections.Counter()
    alltags = {}
    ts_list = []
    cur = conn.execute(f"SELECT {cols} FROM fragment_context")
    names = [d[0] for d in cur.description]
    for rw in cur:
        d = dict(zip(names, rw))
        tg = _tuple_tags(d)
        alltags[d["fragment_id"]] = tg
        dfc.update(tg)
        ts_list.append((d["tuple_ts"], d["fragment_id"]))
    ts_list.sort()
    tsv = [t for t, _ in ts_list]
    wgt = lambda t: 1.0 / math.log(2 + dfc.get(t, 0))

    def score(q, tg):
        c = q & tg
        return sum(wgt(t) for t in c) / (math.sqrt(len(tg)) + 0.001) if c else 0.0

    pcts, top_same, ratios, nopres = [], 0, [], 0
    for r in deliv:
        i = bisect.bisect_left(tsv, r["ts"])
        cand = [ts_list[j] for j in (i - 1, i) if 0 <= j < len(ts_list) and abs(ts_list[j][0] - r["ts"]) <= 1200]
        if not cand:
            nopres += 1
            continue
        q = alltags[min(cand, key=lambda c: abs(c[0] - r["ts"]))[1]]
        base = ("SELECT fc.fragment_id FROM fragment_context fc JOIN memory_fragments mf USING (fragment_id) WHERE ")
        orig = " AND mf.origin IN ('lived','reading','study','journal','action','inner_thought') LIMIT ?"
        if r["route"] == "sound_echo":
            pool = conn.execute(base + "fc.sounds LIKE ? AND fc.tuple_ts < ?" + orig, (f'%"{r["sound"]}"%', r["ts"] - MIN_AGE, CAP)).fetchall()
        else:
            pool = conn.execute(base + "lower(fc.weather)=lower(?) AND fc.tuple_ts < ?" + orig, (r["context"], r["ts"] - MIN_AGE, CAP)).fetchall()
        sc = {f: score(q, alltags.get(f, set())) for (f,) in pool}
        if r["fragment_id"] not in sc or len(sc) < 2:
            continue
        mine = sc[r["fragment_id"]]
        below = sum(1 for v in sc.values() if v < mine)
        eq = sum(1 for v in sc.values() if v == mine)
        pcts.append((below + 0.5 * eq) / len(sc))
        top = max(sc.values())
        ratios.append(mine / top if top else 1.0)
        top_same += (mine == top and eq == 1)
    P(f"rows scored: {len(pcts)} (no present tuple within 20 min: {nopres}); present tuple = nearest fragment_context row (proxy; the real one was not logged)")
    if pcts:
        P(f"- random pick's percentile in the pool's chord ranking: mean {statistics.mean(pcts):.2f} median {statistics.median(pcts):.2f} (0.50 if chord score is independent of what random picks)")
        P(f"- random pick score / chord top score: median {statistics.median(ratios):.2f}; random pick was already the unique chord top in {top_same}/{len(pcts)}")
        P(f"- a deterministic chord pick would change the delivered fragment in {len(pcts)-top_same}/{len(pcts)} rows")
    s = "\n".join(out)
    print(s)
    if a.out:
        open(a.out, "w", encoding="utf-8").write("# J-3724 courier uptake read\n\n" + s + "\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
