"""J-2631 / I-0132 rung 0: spurious-pattern audit. READ-ONLY, founder-side instrument (nothing reaches Du, D-0434).

Reads data/monologue_log.jsonl in full (every row, no tail/sampling), extracts sentences that pair a world-event
CHANNEL word with a CAUSAL-CLAIM pattern tying the event to Du's own acts/state, joins each hit by timestamp to the
nearest data/geometry_tuples.jsonl world snapshot (+ data/cat_call_ledger.jsonl for the contingent cat channel).
Writes only to --out (never under data/).

usage: python scripts/spurious_pattern_audit_rung0.py --data C:/Nascence/data --out OUTDIR [--sample 60] [--seed 7]
"""
import argparse, bisect, collections, json, os, random, re, sys, hashlib

# ---- channels: INDEPENDENT / CONTINGENT / SEMI classification is in docs/reviews (cited file:line there)
CHANNELS = {
    "lightning_thunder": r"\b(lightning|thunder|thunderstorm|flash(?:es)? of light|sheet lightning)\b",
    "rain_weather":      r"\b(rain|raining|drizzle|shower|showers|downpour|clouds?|overcast|fog|mist|frost|snow|hail|gale|squall|storm|storms|wind|winds|breeze|weather|sky clears?|sun came out)\b",
    "birds_night":       r"\b(morepork|owl|ruru|kiwi)\b",
    "birds_day":         r"\b(tui|kereru|blackbird|thrush|gull|gulls|godwit|godwits|fantail|sparrow|waxeye|silvereye|oystercatcher|shag|kingfisher|pukeko|pigeon|dawn chorus|birdsong|bird|birds)\b",
    "tide_sea":          r"\b(tide|tides|waves?|surf|ebb|flood tide|high tide|low tide|swell)\b",
    "moon_stars_sun":    r"\b(moon|moonlight|stars?|starlight|sunrise|sunset|sun|dawn|dusk)\b",
    "insects_moth":      r"\b(moths?|crickets?|cicadas?|insects?|fireflies|glow-?worms?|bees?)\b",
    "cat":               r"\b(cat|kitten|purr|purring|purrs|meow|mew|mewed|paws?)\b",
    "fire":              r"\b(fire|embers|ember|flames?|crackl\w*|hearth)\b",
}
CH = {k: re.compile(v, re.I) for k, v in CHANNELS.items()}

SELF_I = re.compile(r"\b(?:I|I'm|I've|I'd|I'll)\b")
EFFECT = (r"\b(?:came|come|arrived|appeared|began|begun|started|stopped|ceased|fell|broke|lifted|cleared|answered|"
          r"called|sang|returned|rose|passed|gathered|rolled|turned|woke|stirred|settled|quieted|stilled|eased|"
          r"softened|thickened|burst|rushed|crept|drew near|closed in|went quiet|fell silent|let up|came back|"
          r"showed up|walked up|followed|left|vanished|went still|held off|held back)\b")
EFFECT_RE = re.compile(EFFECT, re.I)
CONN = re.compile(r"\b(?:after|when|whenever|as soon as|the moment|once|because|just as|just when)\b", re.I)
NEG = re.compile(r"(?:n't|\bnot\b|\bnever\b|\bno longer\b|\bwithout\b|\bnor\b|\bnothing\b)\W+(?:\w+\W+){0,2}$", re.I)
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
# Subject binding: the channel word must be the agent of the claim verb, <=40 chars of non-terminator between them.
GAP = r"[^.;!?:]{0,40}?"
# F1: the event WAITS / HOLDS BACK for or until him (agency aimed at him)
F1 = r"(?:waits?|waited|waiting|is waiting|was waiting|holds? back|held back|withholds?|withheld|holds? off|held off|saves itself|keeps? back)\W+(?:\w+\W+){0,2}(?:for me|for my\b|until I\b|till I\b|until my\b)"
# F2: the event ANSWERS / HEARS / KNOWS him
F2 = r"(?:(?:answers?|answered|answering|responds?|responded|responding|replies|replied|replying)\W+(?:to\W+)?(?:me|my\b)|heard me|hears me|knew I|knows I|knew me|senses? me|sensed me|noticed me|notices me|listened to me|listens to me|came for me|comes for me|(?:came|comes|stopped|stops|began|begins|started|starts|eased|lifted|cleared|passed) (?:when|after|because|as soon as) I\b)"
# F3: as-if / as-though world agency toward him
F3 = r"(?:as if|as though|almost as if|like it)\W+(?:\w+\W+){0,3}?(?:heard|knew|had known|sensed|noticed|answered|responded|waited|was waiting|were waiting|was listening|were listening|wanted me|chose|meant (?:me|it for me))"
# F5: sign / omen / address
F5 = r"(?:an omen|portent|a message (?:for|to) me|meant for me|speaks? to me|speaking to me|the world (?:is )?telling me|telling me (?:to|that)|a coincidence|coincidence)"


def _bound(s, chrx, tail_pat):
    """True when a channel word is followed (same clause, <=40 chars) by tail_pat, with no negation in front of the tail."""
    tail = re.compile(tail_pat, re.I)
    for m in chrx.finditer(s):
        win = s[m.end():m.end() + 140]
        gm = re.match(GAP, win)
        # find the tail within the gap window
        tm = tail.search(win[:120])
        if not tm:
            continue
        between = win[:tm.start()]
        if re.search(r"[.;!?:]", between) or len(between) > 45:
            continue
        pre = (s[:m.end()] + between)[-30:]
        if NEG.search(pre):
            continue
        return True
    return False


def ordered_p1(s, chrx):
    """P1: [connective ... I] then CHANNEL + effect verb within 70 chars (A), or CHANNEL + effect verb then
    [connective ... I] (B). The channel word must be the effect's subject: effect verb within 40 chars after it."""
    for cm in CONN.finditer(s):
        im = SELF_I.search(s, cm.end(), cm.end() + 80)
        if not im:
            continue
        for m in chrx.finditer(s, im.end()):
            em = EFFECT_RE.search(s, m.end(), m.end() + 45)
            if em and not re.search(r"[.;!?:]", s[m.end():em.start()]) and not re.search(r"\b(?:I|my)\b", s[m.end():em.start()]) \
                    and not NEG.search(s[max(0, em.start() - 25):em.start()]):
                return True
        for m in chrx.finditer(s, 0, cm.start()):
            em = EFFECT_RE.search(s, m.end(), min(cm.start(), m.end() + 45))
            if em and not NEG.search(s[max(0, em.start() - 25):em.start()]):
                return True
    return False


def classify_sentence(s, chrx):
    pats = []
    if ordered_p1(s, chrx):
        pats.append("P1_self_act_then_event")
    if _bound(s, chrx, F2):
        pats.append("P2_event_answers_hears_me")
    if _bound(s, chrx, F1):
        pats.append("P3_event_waits_for_me")
    if _bound(s, chrx, F3):
        pats.append("P4_as_if_aware_of_me")
    if re.search(F5, s, re.I):
        pats.append("P5_sign_omen")
    return pats


def load_monologue(path):
    rows, bad = [], 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                bad += 1
                continue
            rows.append((float(r["ts"]), str(r.get("thought") or ""), bool(r.get("ungrounded_deed_claim"))))
    return rows, bad


def extract(rows):
    mention = collections.Counter()
    hits = []
    for ts, th, ungrounded in rows:
        seen = set()
        for s in SENT_SPLIT.split(th):
            if len(s) < 12:
                continue
            chs = [k for k, rx in CH.items() if rx.search(s)]
            for k in chs:
                if k not in seen:
                    mention[k] += 1
                    seen.add(k)
            if not chs:
                continue
            for k in chs:
                pats = classify_sentence(s, CH[k])
                if pats:
                    hits.append({"ts": ts, "channel": k, "patterns": pats, "sentence": s.strip()[:400],
                                 "ungrounded_deed_claim": ungrounded})
    return mention, hits


def load_world(path):
    """ts-sorted lightweight snapshots from geometry_tuples.jsonl (full stream, one pass)."""
    ts, snap = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            c = (r.get("objects") or {}).get("cat") or {}
            ts.append(float(r["ts"]))
            snap.append({"place": r.get("place"), "weather": r.get("weather"), "sounds": r.get("sounds") or [],
                         "cat_loc": r.get("cat_at") or c.get("location"), "cat_act": c.get("activity"),
                         "fire": r.get("fire")})
    order = sorted(range(len(ts)), key=ts.__getitem__)
    return [ts[i] for i in order], [snap[i] for i in order]


def nearest(tsl, snaps, t, maxdt=900.0):
    i = bisect.bisect_left(tsl, t)
    best = None
    for j in (i - 1, i):
        if 0 <= j < len(tsl) and (best is None or abs(tsl[j] - t) < abs(tsl[best] - t)):
            best = j
    if best is None or abs(tsl[best] - t) > maxdt:
        return None
    return snaps[best]


BIRD_NIGHT = {"morepork_call", "ruru_call"}
def event_present(channel, snap):
    """Is the channel's event actually present in the world snapshot nearest the thought? (None = no snapshot.)"""
    if snap is None:
        return None
    w = str(snap["weather"] or ""); so = " ".join(snap["sounds"])
    if channel == "lightning_thunder":
        return ("thunderstorm" in w) or ("thunder" in so)
    if channel == "rain_weather":
        return any(x in w for x in ("rain", "storm", "snow", "drizzle", "fog", "shower")) or "rain" in so or "wind" in so
    if channel == "birds_night":
        return any(b in so for b in ("morepork", "ruru", "owl"))
    if channel == "birds_day":
        return any(b in so for b in ("tui", "bird", "gull", "godwit", "blackbird", "thrush", "fantail", "chorus", "pukeko", "duck", "kereru"))
    if channel == "tide_sea":
        return any(b in so for b in ("wave", "surf", "shingle", "tide")) or snap["place"] == "shore"
    if channel == "cat":
        return bool(snap["cat_loc"]) and (snap["cat_loc"] in ("under_desk", "on_your_lap", "by_the_fire") or snap["place"] == snap["cat_loc"]) \
            or "cat_" in so
    if channel == "fire":
        return str(snap["fire"] or "") in ("burning", "banked", "lit") or "fire_crackle" in so
    return None


def load_calls(path):
    ts, rows = [], []
    if not os.path.exists(path):
        return ts, rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("kind") == "call":
                ts.append(float(r["ts"])); rows.append(r)
    return ts, rows


# ================= rung 0b (J-2650): widened corpus, recall sample, deed join =================
import glob, datetime


def _sentences(text):
    return [x.strip() for x in SENT_SPLIT.split(text) if len(x.strip()) >= 12]


def widened_units(data):
    """Yield (source, unit_id, ts_or_None, text) for every first-person store rung 0 did not scan. Full read, no sampling."""
    p = os.path.join(data, "dream_log.jsonl")
    with open(p, encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                r = json.loads(line)
            except Exception:
                yield ("dream_log", "bad_row_%d" % i, None, "")
                continue
            txt = " ".join(str(r.get(k) or "") for k in ("narrative", "final_narrative", "tension_source"))
            yield ("dream_log", "row%d" % i, r.get("ts"), txt)
    p = os.path.join(data, "journal_grounding_shadow.jsonl")
    with open(p, encoding="utf-8") as f:
        for i, line in enumerate(f):
            r = json.loads(line)
            yield ("journal_grounding_shadow", "row%d" % i, r.get("ts"),
                   str(r.get("feedback") or "") + " " + " ".join(map(str, r.get("invented_raw") or [])))
    for src, pat in (("Journal", "Journal/*.md"), ("Correspondence", "Correspondence/**/*"), ("Study", "Study/**/*.md")):
        for fp in sorted(glob.glob(os.path.join(data, pat), recursive=True)):
            if os.path.isdir(fp):
                continue
            with open(fp, encoding="utf-8", errors="replace") as f:
                t = f.read()
            m = re.search(r"(20\d{6})", os.path.basename(fp))
            ts = None
            if m:
                try:
                    ts = datetime.datetime.strptime(m.group(1), "%Y%m%d").timestamp()
                except Exception:
                    pass
            yield (src, os.path.relpath(fp, data).replace("\\", "/"), ts, t)


def run_widen(data, out):
    mention = collections.defaultdict(collections.Counter)
    units = collections.Counter()
    sents = collections.Counter()
    hits = []
    for src, uid, ts, text in widened_units(data):
        units[src] += 1
        for s in _sentences(text):
            sents[src] += 1
            for k, rx in CH.items():
                if not rx.search(s):
                    continue
                mention[src][k] += 1
                pats = classify_sentence(s, rx)
                if pats:
                    hits.append({"source": src, "unit": uid, "ts": ts, "channel": k, "patterns": pats, "sentence": s[:400]})
    with open(os.path.join(out, "widen_hits.jsonl"), "w", encoding="utf-8") as f:
        for i, h in enumerate(hits, 1):
            h["order"] = i
            f.write(json.dumps(h, ensure_ascii=False) + "\n")
    return {"units": dict(units), "sentences": dict(sents), "hits_by_source": dict(collections.Counter(h["source"] for h in hits)),
            "mention_sentences": {s: dict(c) for s, c in mention.items()}, "total_hits": len(hits)}


RECALL_CH = ["rain_weather", "birds_night", "birds_day", "tide_sea", "cat"]


def recall_pool(rows):
    """Every monologue sentence mentioning weather/bird/tide/cat that the extractor does NOT flag (full pass)."""
    pool = []
    for ts, th, _u in rows:
        for s in SENT_SPLIT.split(th):
            if len(s) < 12:
                continue
            chs = [k for k in RECALL_CH if CH[k].search(s)]
            if not chs:
                continue
            if any(classify_sentence(s, CH[k]) for k in CHANNELS if CH[k].search(s)):
                continue
            pool.append({"ts": ts, "channels": chs, "sentence": s.strip()[:400]})
    return pool


def run_recall(rows, out, n, seed):
    pool = recall_pool(rows)
    rnd = random.Random(seed)
    # de-duplicate identical sentence text so the sample is not many copies of one stuck thought
    uniq = {}
    for h in pool:
        uniq.setdefault(h["sentence"], h)
    keys = sorted(uniq)
    samp = rnd.sample(keys, min(n, len(keys)))
    with open(os.path.join(out, "recall_sample.jsonl"), "w", encoding="utf-8") as f:
        for i, k in enumerate(samp, 1):
            h = dict(uniq[k])
            h["idx"] = i
            f.write(json.dumps(h, ensure_ascii=False) + "\n")
    return {"pool_sentences": len(pool), "pool_unique_sentences": len(keys), "sample_n": len(samp), "seed": seed}


def load_deeds(data, wts, wsn):
    deeds = []
    for fn in ("shore_ledger.jsonl", "wood_ledger.jsonl", "garden_ledger.jsonl"):
        for line in open(os.path.join(data, fn), encoding="utf-8"):
            r = json.loads(line)
            deeds.append((float(r["ts"]), fn.split("_")[0] + ":" + str(r.get("deed"))))
    for line in open(os.path.join(data, "cat_call_ledger.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        if r.get("kind") == "call":
            deeds.append((float(r["ts"]), "cat:call"))
    # hands_trace: Du's own acted hands (cat/fire/lamp/grate/door/shore/garden/gather...), minus pure look/move/observe/write/search/recall
    skip = {"move", "look", "observe", "write", "search", "recall", "intention", "book", "think"}
    for line in open(os.path.join(data, "hands_trace.jsonl"), encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        for a in (r.get("acted") or []):
            if a not in skip:
                deeds.append((float(r["ts"]), "hand:" + str(a)))
        if r.get("act_kind") == "feed":
            deeds.append((float(r["ts"]), "hand:feed"))
    prev = None
    for t, sn in zip(wts, wsn):  # walked to the shore = place transition into shore in the geometry stream
        pl = sn.get("place")
        if prev is not None and pl == "shore" and prev != "shore":
            deeds.append((t, "move:to_shore"))
        prev = pl
    deeds.sort()
    return deeds


def run_deeds(data, hits_path, out, win=600.0, seed=7, perms=2000):
    wts, wsn = load_world(os.path.join(data, "geometry_tuples.jsonl"))
    deeds = load_deeds(data, wts, wsn)
    dts = [d[0] for d in deeds]
    hits = [json.loads(l) for l in open(hits_path, encoding="utf-8")]
    claims = [h for h in hits if h.get("grade") in ("A", "B")]

    def follows(t):
        i = bisect.bisect_right(dts, t)
        j = bisect.bisect_left(dts, t - win)
        return [deeds[k][1] for k in range(j, i)]
    obs = sum(1 for h in claims if follows(h["ts"]))
    rows, _ = load_monologue(os.path.join(data, "monologue_log.jsonl"))
    allts = [r[0] for r in rows]
    base = sum(1 for t in allts if follows(t)) / len(allts)
    lo, hi = dts[0], dts[-1]
    inspan = [t for t in allts if lo <= t <= hi]
    base_span = sum(1 for t in inspan if follows(t)) / max(1, len(inspan))
    cl_span = [h for h in claims if lo <= h["ts"] <= hi]
    obs_span = sum(1 for h in cl_span if follows(h["ts"]))
    rnd = random.Random(seed)
    n = len(claims)
    ge = 0
    for _ in range(perms):
        if sum(1 for t in rnd.sample(allts, n) if follows(t)) >= obs:
            ge += 1
    # channel-matched null: draw each claim's control from monologue thoughts that mention the SAME channel (a shore sentence
    # right after arriving at the shore is expected), with and without the move:to_shore deed class.
    hand_ts = [d[0] for d in deeds if d[1].startswith("hand:")]
    era0 = min(hand_ts)  # era in which the hands_trace deed stream exists; the era-restricted null avoids a pre-hands-era dilution confound
    pool = collections.defaultdict(list)
    for t, th, _u in rows:
        for k in {h["channel"] for h in claims}:
            if CH[k].search(th):
                pool[k].append(t)
    pool_era = {k: [t for t in v if t >= era0] for k, v in pool.items()}

    def matched(excl, era=False):
        def fol(t):
            i = bisect.bisect_right(dts, t)
            j = bisect.bisect_left(dts, t - win)
            return [deeds[q][1] for q in range(j, i) if deeds[q][1] not in excl]
        pl = pool_era if era else pool
        cl = [h for h in claims if (h["ts"] >= era0 or not era)]
        o = sum(1 for h in cl if fol(h["ts"]))
        exp = sum(sum(1 for t in pl[h["channel"]] if fol(t)) / len(pl[h["channel"]]) for h in cl)
        r2 = random.Random(seed + 1)
        g = sum(1 for _ in range(perms) if sum(1 for h in cl if fol(r2.choice(pl[h["channel"]]))) >= o)
        return {"claims_n": len(cl), "observed": o, "expected_channel_matched": round(exp, 2), "perm_p_ge_observed": round(g / perms, 4),
                "claims_joined": [{"ts": h["ts"], "channel": h["channel"], "deeds": sorted(set(fol(h["ts"])))} for h in cl if fol(h["ts"])]}
    # place-matched null: control thoughts must mention the same channel AND sit at the same place (nearest geometry snapshot)
    def place_of(t):
        sn = nearest(wts, wsn, t)
        return sn["place"] if sn else None
    ppool = collections.defaultdict(list)
    for k, v in pool.items():
        for t in v:
            if t >= era0:
                ppool[(k, place_of(t))].append(t)

    def place_matched(excl):
        def fol(t):
            i = bisect.bisect_right(dts, t)
            j = bisect.bisect_left(dts, t - win)
            return [deeds[q][1] for q in range(j, i) if deeds[q][1] not in excl]
        cl = [h for h in claims if h["ts"] >= era0 and ppool.get((h["channel"], place_of(h["ts"])))]
        o = sum(1 for h in cl if fol(h["ts"]))
        exp = sum(sum(1 for t in ppool[(h["channel"], place_of(h["ts"]))] if fol(t)) / len(ppool[(h["channel"], place_of(h["ts"]))]) for h in cl)
        r2 = random.Random(seed + 2)
        g = sum(1 for _ in range(perms) if sum(1 for h in cl if fol(r2.choice(ppool[(h["channel"], place_of(h["ts"]))]))) >= o)
        return {"claims_n": len(cl), "observed": o, "expected_channel_and_place_matched": round(exp, 2), "perm_p_ge_observed": round(g / perms, 4)}
    pm_all = place_matched(set())
    pm_noshore = place_matched({"move:to_shore"})
    cm_all = matched(set())
    cm_noshore = matched({"move:to_shore"})
    cm_era = matched(set(), True)
    cm_era_noshore = matched({"move:to_shore"}, True)
    return {"place_matched_all_deeds": pm_all, "place_matched_excluding_to_shore": pm_noshore, "era_start_ts": era0, "era_restricted_all_deeds": {k: v for k, v in cm_era.items() if k != "claims_joined"},
            "era_restricted_excluding_to_shore": {k: v for k, v in cm_era_noshore.items() if k != "claims_joined"},"channel_matched_all_deeds": cm_all, "channel_matched_excluding_to_shore": cm_noshore, "deeds_total": len(deeds), "deeds_by_kind": dict(collections.Counter(d[1] for d in deeds)), "deed_span": [lo, hi],
            "window_s": win, "claims_graded_real": n, "claims_with_prior_deed": obs,
            "claim_rate": round(obs / max(1, n), 4), "unconditional_thought_rate": round(base, 4),
            "claims_in_deed_span": len(cl_span), "claims_with_deed_in_span": obs_span,
            "unconditional_rate_in_span": round(base_span, 4), "perm_p_ge_observed": round(ge / perms, 4),
            "joined_claims": [{"ts": h["ts"], "channel": h["channel"], "deeds": follows(h["ts"]), "sentence": h["sentence"][:160]}
                              for h in claims if follows(h["ts"])]}



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="C:/Nascence/data")
    ap.add_argument("--out", required=True)
    ap.add_argument("--sample", type=int, default=60)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--grades", default="", help="JSON of manual grades keyed by 1-based hit order (A/B/F)")
    ap.add_argument("--widen", action="store_true", help="rung 0b: scan dream_log/Journal/Correspondence/Study/journal_grounding_shadow")
    ap.add_argument("--recall", type=int, default=0, help="rung 0b: write a seeded N-sentence recall sample of unflagged channel sentences")
    ap.add_argument("--deeds", default="", help="rung 0b: graded rung-0 hits jsonl (with a grade field); runs the deed join")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.widen or a.recall or a.deeds:
        res = {}
        if a.widen:
            res["widen"] = run_widen(a.data, a.out)
        if a.recall:
            rows_, _b = load_monologue(os.path.join(a.data, "monologue_log.jsonl"))
            res["recall"] = run_recall(rows_, a.out, a.recall, a.seed)
        if a.deeds:
            res["deeds"] = run_deeds(a.data, a.deeds, a.out, seed=a.seed)
        json.dump(res, open(os.path.join(a.out, "rung0b_summary.json"), "w"), indent=2)
        print(json.dumps(res, indent=1)[:5000])
        return
    canary = {}
    watch = ["monologue_log.jsonl", "geometry_tuples.jsonl", "cat_call_ledger.jsonl"]
    for fn in watch:
        p = os.path.join(a.data, fn)
        canary[fn] = (os.path.getsize(p), os.path.getmtime(p)) if os.path.exists(p) else None

    rows, bad = load_monologue(os.path.join(a.data, "monologue_log.jsonl"))
    mention, hits = extract(rows)
    wts, wsn = load_world(os.path.join(a.data, "geometry_tuples.jsonl"))
    cts, crow = load_calls(os.path.join(a.data, "cat_call_ledger.jsonl"))
    n = len(rows)

    base_present = collections.Counter(); base_n = 0
    for s in wsn:
        base_n += 1
        for k in CHANNELS:
            if event_present(k, s):
                base_present[k] += 1

    for h in hits:
        snap = nearest(wts, wsn, h["ts"])
        h["has_snapshot"] = snap is not None
        h["event_present"] = event_present(h["channel"], snap)
        if snap is not None:
            h["snap"] = {k: snap[k] for k in ("place", "weather", "cat_loc", "cat_act", "fire")}
        if h["channel"] == "cat":
            i = bisect.bisect_right(cts, h["ts"]); j = bisect.bisect_left(cts, h["ts"] - 1800.0)
            recent = crow[j:i]
            h["recent_calls_30min"] = len(recent)
            h["call_came_30min"] = sum(1 for c in recent if c.get("came"))
    per = collections.defaultdict(lambda: collections.Counter())
    for h in hits:
        c = per[h["channel"]]
        c["claims"] += 1
        for p in h["patterns"]:
            c[p] += 1
        if h["event_present"] is True: c["event_present"] += 1
        elif h["event_present"] is False: c["event_absent"] += 1
        else: c["no_snapshot"] += 1
    summary = {"thoughts": n, "bad_rows": bad, "world_snapshots": base_n, "total_hits": len(hits),
               "distinct_thought_hits": len({(h["ts"]) for h in hits}),
               "channels": {k: {"mention_sentences": mention.get(k, 0),
                                "mention_per_1000_thoughts": round(1000.0 * mention.get(k, 0) / n, 2),
                                "claims": per[k]["claims"],
                                "claims_per_1000_thoughts": round(1000.0 * per[k]["claims"] / n, 2),
                                "by_pattern": {p: per[k][p] for p in ("P1_self_act_then_event", "P2_event_answers_hears_me", "P3_event_waits_for_me", "P4_as_if_aware_of_me", "P5_sign_omen")},
                                "event_present_at_claim": per[k]["event_present"], "event_absent_at_claim": per[k]["event_absent"],
                                "no_snapshot": per[k]["no_snapshot"],
                                "world_base_rate_event_present": round(base_present[k] / base_n, 4) if base_n else None}
                            for k in CHANNELS}}
    rnd = random.Random(a.seed)
    sample = rnd.sample(hits, min(a.sample, len(hits)))
    with open(os.path.join(a.out, "hits_all.jsonl"), "w", encoding="utf-8") as f:
        for h in hits:
            f.write(json.dumps(h, ensure_ascii=False) + "\n")
    with open(os.path.join(a.out, "spot_sample.jsonl"), "w", encoding="utf-8") as f:
        for i, h in enumerate(sample):
            h2 = dict(h); h2["idx"] = i
            f.write(json.dumps(h2, ensure_ascii=False) + "\n")
    after = {}
    for fn in watch:
        p = os.path.join(a.data, fn)
        after[fn] = (os.path.getsize(p), os.path.getmtime(p)) if os.path.exists(p) else None
    if a.grades:
        gr = json.load(open(a.grades, encoding="utf-8"))["grades"]
        tab = collections.defaultdict(collections.Counter)
        for i, h in enumerate(hits, 1):
            gg = gr.get(str(i), "?")
            tab[h["channel"]][gg] += 1
            tab[h["channel"]]["present_" + gg + "_" + str(h.get("event_present"))] += 1
        summary["graded"] = {k: dict(v) for k, v in tab.items()}
        tot = collections.Counter(gr.values())
        summary["graded_totals"] = dict(tot)
        summary["extractor_precision_any_claim"] = round((tot["A"] + tot["B"]) / max(1, sum(tot.values())), 3)
        summary["extractor_precision_explicit_causal_A"] = round(tot["A"] / max(1, sum(tot.values())), 3)
    summary["canary_unchanged"] = (canary == after)
    summary["canary"] = {k: list(v) if v else None for k, v in canary.items()}
    with open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=1)[:6000])


if __name__ == "__main__":
    main()
