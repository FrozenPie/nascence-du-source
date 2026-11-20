"""J-2536 tuple-join integrity audit. READ-ONLY. nascence.db opened ?mode=ro; geometry_tuples.jsonl and
moments.jsonl only read. Writes only J-2536_*.json/pkl in the scratchpad. CPU only, no model.
Usage: python J-2536_audit.py <section>   (split|ambig|spot|moments|weeks|all)
"""
import sqlite3, json, pickle, sys, time, re, random, collections, bisect, statistics, os

SP = os.path.dirname(os.path.abspath(__file__))
DB = "file:C:/Nascence/data/memory/nascence.db?mode=ro"
RNG = random.Random(2536)


def norm(s):
    return " ".join((s or "").split())


def conn():
    c = sqlite3.connect(DB, uri=True)
    c.row_factory = sqlite3.Row
    return c


def load_frags():
    c = conn()
    frags = {}
    for r in c.execute("select fragment_id, origin, timestamp, content from memory_fragments"):
        frags[r["fragment_id"]] = (r["origin"], r["timestamp"], norm(r["content"])[:600])
    fc = {}
    for r in c.execute("select fragment_id, source, tuple_ts, place, weather, cat_at, sounds, warmth, fire, valence from fragment_context"):
        fc[r["fragment_id"]] = tuple(r)[1:]
    wc = {}
    for r in c.execute("select fragment_id, source, tuple_ts, place, weather, cat_at, sounds, warmth from world_context"):
        wc[r["fragment_id"]] = tuple(r)[1:]
    cut = c.execute("select min(tuple_ts) from fragment_context where source like 'experienced:%'").fetchone()[0]
    return frags, fc, wc, cut


def load_tuples():
    return pickle.load(open(os.path.join(SP, "J-2536_tuples.pkl"), "rb"))


def classify(fid, fc):
    r = fc.get(fid)
    if r is None:
        return "none"
    return "exact" if r[0].startswith("experienced:") else "window"


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def sec_split(frags, fc, wc, cut):
    out = {"cut": cut}
    tab = collections.defaultdict(lambda: collections.Counter())
    for fid, (o, ts, _) in frags.items():
        era = "post" if ts >= cut else "pre"
        tab[(o, era)][classify(fid, fc)] += 1
        tab[(o, "all")][classify(fid, fc)] += 1
        tab[("ALL", era)][classify(fid, fc)] += 1
        tab[("ALL", "all")][classify(fid, fc)] += 1
    out["split"] = {f"{o}|{e}": dict(v) for (o, e), v in tab.items()}
    # post-stamp unjoined residue by origin
    return out


def sec_weeks(frags, fc, wc, cut):
    # weeks starting Sunday 2026-07-05 local; earlier = 'pre-07-05'
    t0 = time.mktime(time.strptime("2026-07-05", "%Y-%m-%d"))
    wk = collections.defaultdict(lambda: collections.Counter())
    for fid, (o, ts, _) in frags.items():
        if ts < t0:
            k = "pre-07-05"
        else:
            k = time.strftime("%Y-%m-%d", time.localtime(t0 + 7 * 86400 * int((ts - t0) // (7 * 86400))))
        cl = classify(fid, fc)
        wk[k][cl] += 1
        wk[k]["n"] += 1
        if o == "inner_thought":
            wk[k]["it_n"] += 1
            wk[k]["it_" + cl] += 1
        if o == "reading":
            wk[k]["rd_n"] += 1
            wk[k]["rd_" + cl] += 1
    # tuples per week by source family
    tw = collections.defaultdict(lambda: collections.Counter())
    for t in load_tuples():
        ts = t["ts"]
        if ts < t0:
            k = "pre-07-05"
        else:
            k = time.strftime("%Y-%m-%d", time.localtime(t0 + 7 * 86400 * int((ts - t0) // (7 * 86400))))
        tw[k]["n"] += 1
        tw[k]["idle" if t["source"] in ("idle", "monologue", "monologue_train") else "other"] += 1
    return {"weeks": {k: dict(v) for k, v in wk.items()}, "tuple_weeks": {k: dict(v) for k, v in tw.items()}}


def sec_ambig(frags, fc, wc, cut):
    tuples = load_tuples()
    out = {}
    IDLE = ("idle", "monologue", "monologue_train")
    # ---- (i) the live window rule, re-run exactly (tuple side)
    rows = []
    for t in tuples:
        if t["source"] not in IDLE:
            continue
        th = norm(t["thought"])
        if len(th) < 30:
            continue
        rows.append((t, th[:70]))
    it_frags = [(fid, v[1], v[2]) for fid, v in frags.items() if v[0] == "inner_thought"]
    bins = collections.defaultdict(list)
    for fid, ts, ct in it_frags:
        bins[int(ts // 300)].append((fid, ts, ct))
    cand_hist = collections.Counter()
    per_frag = collections.defaultdict(list)  # fid -> list of tuple idx matching
    chosen = []  # (tuple, fid) unique ones
    for i, (t, probe) in enumerate(rows):
        b = int(t["ts"] // 300)
        cands = [f for k in (b - 1, b, b + 1) for f in bins.get(k, []) if abs(f[1] - t["ts"]) <= 300 and probe in f[2]]
        cand_hist[min(len(cands), 5)] += 1
        for f in cands:
            per_frag[f[0]].append(i)
        if len(cands) == 1:
            chosen.append((i, cands[0][0]))
    out["rule_tuple_side"] = {"idle_tuples_eligible": len(rows), "cand_hist(0..5+)": dict(cand_hist)}
    # forward side: per inner_thought fragment, number of eligible tuples that match it
    fwd = collections.Counter(min(len(v), 5) for v in per_frag.values())
    out["rule_fragment_side"] = {"fragments_with_>=1_candidate_tuple": len(per_frag), "n_tuples_matching(1..5+)": dict(fwd)}
    # tuples with 2+ fragments in window (reverse ambiguity) - same as cand_hist >=2
    # which of the chosen are the legacy rows (census_world:idle)?
    leg = {fid for fid, v in fc.items() if v[0].startswith("census_world:")}
    ch_ids = {fid for _, fid in chosen}
    out["legacy_rows"] = {"census_world_rows": len(leg), "rule_reproduces": len(leg & ch_ids),
                          "legacy_not_reproduced": len(leg - ch_ids), "rule_chooses_not_in_legacy": len(ch_ids - leg)}
    # legacy rows: how many fragments (of those joined) ALSO had a 2nd tuple candidate (forward ambiguity)
    leg_fwd = collections.Counter(min(len(per_frag.get(fid, [])), 5) for fid in leg)
    out["legacy_forward_candidates"] = dict(leg_fwd)
    # offsets for legacy rows
    offs = []
    ti = {}
    for i, (fid_i) in chosen:
        pass
    for i, fid in chosen:
        if fid in leg:
            offs.append(abs(rows[i][0]["ts"] - frags[fid][1]))
    if offs:
        offs.sort()
        out["legacy_offset_s"] = {"median": round(statistics.median(offs), 2), "p90": round(offs[int(.9 * len(offs))], 1), "max": round(offs[-1], 1)}
    # ---- (iii) validate the rule against the write-time stamp (post-stamp inner_thoughts that the rule picks)
    cmp_n = same_place = same_weather = same_both = 0
    unique_in_post = 0
    n_post_frag = sum(1 for fid, ts, ct in it_frags if ts >= cut)
    mism = []
    for i, fid in chosen:
        if frags[fid][1] < cut:
            continue
        unique_in_post += 1
        w = wc.get(fid)
        if not w:
            continue
        t = rows[i][0]
        cmp_n += 1
        sp = (w[2] == t["place"])
        sw = (w[3] == t["weather"])
        same_place += sp
        same_weather += sw
        same_both += (sp and sw)
        if not (sp and sw) and len(mism) < 8:
            mism.append((fid, round(t["ts"] - frags[fid][1], 1), w[2], t["place"], w[3], t["weather"]))
    out["rule_vs_writetime_stamp_post_era_inner_thought"] = {
        "post_era_inner_thought_fragments": n_post_frag, "rule_picks_unique": unique_in_post, "compared": cmp_n,
        "place_agree": same_place, "weather_agree": same_weather, "both_agree": same_both,
        "wrong_attachment_rate_pct": pct(cmp_n - same_both, cmp_n), "examples": mism}
    # ---- (ii) counterfactual window join for EVERY origin, using that origin's own stamp-time tuples
    # tuple side: tuples with source == origin; probe = norm(thought)[:70]; fragment side prefix in content
    by_src = collections.defaultdict(list)
    for t in tuples:
        by_src[t["source"]].append(t)
    cf = {}
    for o in sorted({v[0] for v in frags.values()}):
        src_t = by_src.get(o, [])
        if not src_t:
            continue
        fr = [(fid, v[1], v[2]) for fid, v in frags.items() if v[0] == o and v[1] >= cut]
        if not fr:
            continue
        fb = collections.defaultdict(list)
        for f in fr:
            fb[int(f[1] // 300)].append(f)
        tb = collections.defaultdict(list)
        probes = []
        for t in src_t:
            th = norm(t["thought"])
            tb[int(t["ts"] // 300)].append((t["ts"], th[:70]))
        # fragment side: how many same-source tuples with matching prefix in +-300s of fragment ts
        hist = collections.Counter()
        for fid, ts, ct in fr:
            b = int(ts // 300)
            n = 0
            for k in (b - 1, b, b + 1):
                for (tts, pr) in tb.get(k, []):
                    if abs(tts - ts) <= 300 and len(pr) >= 20 and pr in ct:
                        n += 1
            hist[min(n, 5)] += 1
        # tuple side: how many same-origin fragments match each tuple
        thist = collections.Counter()
        for t in src_t:
            th = norm(t["thought"])[:70]
            if t["ts"] < cut or len(th) < 20:
                continue
            b = int(t["ts"] // 300)
            n = 0
            for k in (b - 1, b, b + 1):
                for f in fb.get(k, []):
                    if abs(f[1] - t["ts"]) <= 300 and th in f[2]:
                        n += 1
            thist[min(n, 5)] += 1
        cf[o] = {"frag_side(0..5+ matching tuples)": dict(sorted(hist.items())),
                 "tuple_side(0..5+ matching frags)": dict(sorted(thist.items())), "n_frags": len(fr)}
    out["counterfactual_all_origins_post_era"] = cf
    return out


# ---- spot check
WEATHER_RULES = {
    "rain": (re.compile(r"\b(rain|raining|rainy|rains|drizzl\w*|downpour|showers?)\b", re.I), {"drizzle", "steady rain", "wind and rain", "thunderstorm"}),
    "storm": (re.compile(r"\b(storm\w*|thunder\w*|lightning|gale)\b", re.I), {"thunderstorm", "wind and rain"}),
    "clearsky": (re.compile(r"\b(clear sky|cloudless|blue sky|sunny)\b", re.I), {"clear", "high cloud"}),
}
PLACE_RULES = {
    "shore": re.compile(r"\b(shore|beach|shingle|waterline|tide|tideline|surf|sea)\b", re.I),
    "garden": re.compile(r"\b(garden|flowerbed|thyme|parsley|rosemary|herb\w*|garden wall|gate)\b", re.I),
    "wood": re.compile(r"\b(wood|woods|woodland|forest|fern\w*|leaf.?mould|trees?)\b", re.I),
    "study": re.compile(r"\b(study|desk|lamp|grate|hearth|bookshelf|bookcase)\b", re.I),
}
SOUND_RULES = {
    "morepork_call": re.compile(r"\bmorepork\b", re.I),
    "clock_tick": re.compile(r"\b(clock|ticking)\b", re.I),
    "fire_crackle": re.compile(r"\b(crackl\w*)\b", re.I),
    "waves_on_shingle": re.compile(r"\b(waves?|surf)\b", re.I),
    "rain_on_roof": re.compile(r"\brain on the roof\b", re.I),
    "tui_song": re.compile(r"\btui\b", re.I),
    "gull_cries": re.compile(r"\bgulls?\b", re.I),
}
CAT = re.compile(r"\b(cat|kitten|tabby)\b", re.I)


def spot(fid, text, row):
    """row = fragment_context tuple (source,tuple_ts,place,weather,cat_at,sounds,warmth,fire,valence). Returns dict test-> 'agree'/'disagree'."""
    res = {}
    place, weather, cat_at, sounds = row[2], row[3], row[4], row[5]
    try:
        sl = set(json.loads(sounds or "[]"))
    except Exception:
        sl = set()
    for name, (rx, ok) in WEATHER_RULES.items():
        if rx.search(text):
            res["w_" + name] = "agree" if weather in ok else "disagree"
    mentioned = [p for p, rx in PLACE_RULES.items() if rx.search(text)]
    if mentioned:
        res["place"] = "agree" if place in mentioned else "disagree"
    for k, rx in SOUND_RULES.items():
        if rx.search(text):
            res["s_" + k] = "agree" if k in sl else "disagree"
    if CAT.search(text):
        res["cat_here"] = "agree" if cat_at else "disagree"
    return res


def sec_spot(frags, fc, wc, cut):
    out = {}
    by_o = collections.defaultdict(list)
    for fid, r in fc.items():
        f = frags.get(fid)
        if not f:
            continue
        if r[0].startswith("experienced:"):
            by_o[f[0]].append(fid)
        else:
            by_o["WINDOW(census_world:idle)"].append(fid)
    ex = {}
    for o, ids in sorted(by_o.items(), key=lambda kv: -len(kv[1])):
        if len(ids) < 300:
            continue
        sample = RNG.sample(ids, 50)

        def agg(idlist):
            cnt = collections.Counter()
            frag_any_dis = frag_any_app = 0
            for fid in idlist:
                res = spot(fid, frags[fid][2], fc[fid])
                if res:
                    frag_any_app += 1
                if any(v == "disagree" for v in res.values()):
                    frag_any_dis += 1
                for k, v in res.items():
                    grp = k.split("_")[0] if k.startswith("w_") or k.startswith("s_") else k
                    cnt[(grp, v)] += 1
            d = {}
            for grp in ("w", "place", "s", "cat_here"):
                a = cnt[(grp, "agree")]
                b = cnt[(grp, "disagree")]
                d[grp] = {"agree": a, "disagree": b, "mismatch_pct": pct(b, a + b)}
            d["frags_with_any_testable_mention"] = frag_any_app
            d["frags_with_any_disagree"] = frag_any_dis
            d["n"] = len(idlist)
            return d

        out[o] = {"sample50": agg(sample), "population": agg(ids)}
        # keep disagreeing examples from the sample for manual reading
        exs = []
        for fid in ids:
            res = spot(fid, frags[fid][2], fc[fid])
            if any(v == "disagree" for v in res.values()):
                exs.append((fid, {k: v for k, v in res.items() if v == "disagree"}, fc[fid][2], fc[fid][3], frags[fid][2][:240]))
        RNG.shuffle(exs)
        ex[o] = exs[:12]
    out["_examples"] = ex
    return out


def sec_moments(frags, fc, wc, cut):
    out = {}
    tuples = load_tuples()
    idle_t = [(t["ts"], norm(t["thought"])[:70], t["source"]) for t in tuples if t["source"] in ("idle", "monologue", "monologue_train")]
    idle_t.sort()
    its = [x[0] for x in idle_t]
    # fragments binned
    fb = collections.defaultdict(list)
    for fid, (o, ts, ct) in frags.items():
        fb[int(ts // 300)].append((fid, o, ts, ct))
    n = 0
    stats = collections.Counter()
    src_cnt = collections.Counter()
    moms = []
    keys = collections.Counter()
    with open("C:/Nascence/data/moments.jsonl", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                m = json.loads(line)
            except Exception:
                stats["bad_line"] += 1
                continue
            n += 1
            if n == 1:
                keys.update(m.keys())
            th = norm(m.get("thought"))
            moms.append((m["ts"], th[:70], m.get("source")))
            src_cnt[m.get("source")] += 1
    out["moments_total"] = n
    out["moment_keys_first_row"] = sorted(keys)
    out["moment_span"] = [time.strftime("%F", time.localtime(moms[0][0])), time.strftime("%F", time.localtime(moms[-1][0]))]
    out["moment_source_tags"] = dict(src_cnt)
    # exact-key check: any fragment column holds a moment ts?
    c = conn()
    mts = {repr(round(m[0], 1)) for m in moms}
    hit = 0
    for r in c.execute("select source_id, encounter_id from memory_fragments where source_id is not null or encounter_id is not null"):
        for v in (r[0], r[1]):
            if v is not None and str(v) in mts:
                hit += 1
    out["fragments_with_source_or_encounter_id_equal_to_a_moment_ts"] = hit
    cols = [r[1] for r in c.execute("pragma table_info(memory_fragments)")]
    out["memory_fragments_columns"] = cols
    # text+time join, moment -> fragment (any origin / inner_thought), +-300 s, prefix in content
    j_any = collections.Counter()
    j_it = collections.Counter()
    j_tup = collections.Counter()
    by_week = collections.defaultdict(lambda: collections.Counter())
    t0 = time.mktime(time.strptime("2026-07-05", "%Y-%m-%d"))
    for ts, pr, srcx in moms:
        wkey = time.strftime("%Y-%m-%d", time.localtime(t0 + 7 * 86400 * int((ts - t0) // (7 * 86400)))) if ts >= t0 else "pre-07-05"
        by_week[wkey]["n"] += 1
        if len(pr) < 30:
            j_any["short"] += 1
            j_it["short"] += 1
            continue
        b = int(ts // 300)
        ca = []
        for k in (b - 1, b, b + 1):
            for (fid, o, fts, ct) in fb.get(k, []):
                if abs(fts - ts) <= 300 and pr in ct:
                    ca.append((fid, o))
        j_any[min(len(ca), 3)] += 1
        ci = [x for x in ca if x[1] == "inner_thought"]
        j_it[min(len(ci), 3)] += 1
        if ca:
            by_week[wkey]["frag_joined"] += 1
        lo = bisect.bisect_left(its, ts - 300)
        hi = bisect.bisect_right(its, ts + 300)
        ct_ = [x for x in idle_t[lo:hi] if x[1] and (pr[:40] in x[1] or x[1][:40] in pr)]
        j_tup[min(len(ct_), 3)] += 1
        if ct_:
            by_week[wkey]["tuple_joined"] += 1
    out["moment_to_fragment_any_origin(0..3+ candidates)"] = dict(j_any)
    out["moment_to_fragment_inner_thought(0..3+)"] = dict(j_it)
    out["moment_to_idle_tuple(0..3+)"] = dict(j_tup)
    out["moment_by_week"] = {k: dict(v) for k, v in sorted(by_week.items())}
    # co_recall ledger: rows stamped with moment_ts (J-2601)
    tot = withm = 0
    try:
        with open("C:/Nascence/data/co_recall_ledger.jsonl", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                tot += 1
                if r.get("moment_ts") is not None:
                    withm += 1
    except Exception as e:
        out["co_recall_err"] = repr(e)
    out["co_recall_ledger"] = {"rows": tot, "with_moment_ts": withm}
    return out


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    frags, fc, wc, cut = load_frags()
    secs = {"split": sec_split, "ambig": sec_ambig, "spot": sec_spot, "moments": sec_moments, "weeks": sec_weeks}
    todo = secs if which == "all" else {which: secs[which]}
    for name, fn in todo.items():
        t0 = time.time()
        res = fn(frags, fc, wc, cut)
        json.dump(res, open(os.path.join(SP, f"J-2536_out_{name}.json"), "w", encoding="utf-8"), indent=1, default=str)
        print(name, "done", round(time.time() - t0, 1), "s")
