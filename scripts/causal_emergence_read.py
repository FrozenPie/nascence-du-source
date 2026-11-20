"""causal_emergence_read.py -- J-2513 (T-0106, frontier_disciplines_2026-10-30.md section 2).

Question: does a REGIME-level description of Du carry more effective information (Hoel 2013/2017)
about its own next state than the LOOP-level (micro) description does?

READ-ONLY. Streams data/*.jsonl line by line; writes only the --out JSON. Zero LLM, no core/ import.
Nothing here reaches Du (D-0434). The macro labels are ours; Du never sees them.

EVERYTHING BELOW WAS DECLARED BEFORE THE FIRST RUN (J-2513, 2026-10-30). Do not tune to the outcome.

TICK            60-s buckets. A tick is LIVE iff data/coupling_rides.jsonl has a kind=publish row
                from loop climate or stream in it. Transitions use only pairs (t, t+1) with both live.
WINDOW          from the latest first-row of the micro/macro sources to the earliest last-row.
MINIMUM         >= 2000 live ticks with >= 3 distinct publishing loops (any loop in coupling_rides
                kind=publish), and >= 1000 transitions per half. Unmet -> verdict INSUFFICIENT_ROWS.
MICRO alphabet  7 bits per tick:
                  stream  - coupling_rides publish loop=stream (train step)
                  witness - publish loop=witness
                  ledgers - publish loop=ledgers (idle seed)
                  delib   - publish loop=deliberation
                  ign     - data/ignition_log.jsonl row in tick
                  human   - data/provenance_log.jsonl input_type=human row in tick
                  sleep   - sleep mode (state machine below)
                Excluded, with reason: climate (it is the tick clock, ~always 1); hub/follow/si and
                cup rides (exist only since 10-09 / 10-29 / sparse: alphabet would change between
                halves; F-3305: 11,006 of 12,138 rides empty).
SLEEP mode      data/sleep_pressure_log.jsonl: reason in {sleep_entry, sleep_beat} -> asleep; any other
                reason -> awake. Carried forward between rows.
MACRO A         'regime signal' (F-3216: sleep mode, idle allocation, arousal shadow):
                  sleep x arousal band x idle-allocator would_pick_argmax.
                  arousal band from data/arousal_shadow.jsonl level: <0.35 low, <0.55 mid, else high.
                  idle channel from data/logs/idle_shadow.jsonl would_pick_argmax, carried forward
                  <= 600 s, else 'none'. Arousal also carried forward <= 600 s, else 'none'.
MACRO B         'climate regime': sleep x arousal band x climate ignition_level band (climate publish
                  tuple ignition_level: <0.5 low, <0.8 mid, else high; carried forward <= 600 s).
MACRO C         Hoel-proper coarse-graining OF the micro state (a function of it):
                  sleep x (count of stream/witness/ledgers/delib bits, 0..4) x (ign or human).
                Lane priority is not logged per tick anywhere found (lane2_shadow is a different
                lane), so it is not in any partition.
EI estimator    Per level per half: source states with < N_MIN=20 visits are merged into one RARE
                state (as source and as target). Uniform intervention over the n observed source
                states. EI = H(mean row) - mean H(row) bits; determinism = log2 n - mean H(row);
                degeneracy = log2 n - H(mean row); effectiveness = EI / log2 n.
                Small-sample bias: NULL = mean EI over 200 permutations of the next-state sequence
                (seed 2513); EI_corr = EI - NULL.
HALVES          live transitions split at their median index (equal counts).
VERDICT         EMERGENCE iff EI_corr(macro) > EI_corr(micro) on BOTH halves for BOTH A and B.
                Otherwise FALSIFIED, labelled: MICRO_WINS (micro >= macro everywhere) or
                SIGN_FLIP (differs between halves or between A and B). C is reported, not voted.
                Effectiveness (EI / log2 n) is reported as a secondary, size-normalised view.

POST-HOC DIAGNOSTICS (added AFTER the first run returned EMERGENCE; they do not change the verdict
rule above, they test whether it means what it seems to):
  stay_rate     fraction of transitions where a level's state is unchanged (persistence / inertia).
  cross_ei      EI of each level's CURRENT state about the MICRO NEXT state (same estimator; rare
                merging done separately for source and target). This is the briefing's literal
                question ('about Du's next state'), with the next state held fixed across levels.
"""
import argparse, bisect, collections, datetime, json, math, os, random

TICK = 60
MIN_TICKS_3LOOPS = 2000
MIN_TRANS_PER_HALF = 1000
N_MIN = 20
N_SHUFFLE = 200
SEED = 2513
CARRY_S = 600
AROUSAL_CUTS = (0.35, 0.55)
IGNLVL_CUTS = (0.5, 0.8)
MICRO_LOOPS = ("stream", "witness", "ledgers", "deliberation")


def rows(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if isinstance(r, dict) and isinstance(r.get("ts"), (int, float)):
                yield r


def band(v, cuts):
    if v is None:
        return "none"
    return "low" if v < cuts[0] else ("mid" if v < cuts[1] else "high")


_KEYS = {}


def carried(series, t):
    """series: sorted list of (ts, value). Last value at or before t within CARRY_S, else None."""
    keys = _KEYS.get(id(series))
    if keys is None:
        keys = _KEYS[id(series)] = [s[0] for s in series]
    i = bisect.bisect_right(keys, t) - 1
    if i < 0:
        return None
    ts, v = series[i]
    return v if t - ts <= CARRY_S else None


def H(p):
    return -sum(x * math.log2(x) for x in p if x > 0)


def ei_of(src, dst, cross=False):
    cnt = collections.Counter(src)
    keep = {s for s, c in cnt.items() if c >= N_MIN}
    m = lambda s: s if s in keep else "RARE"
    keep_d = {s for s, c in collections.Counter(dst).items() if c >= N_MIN} if cross else keep
    S = [m(s) for s in src]
    D = [d if d in keep_d else "RARE" for d in dst]
    states = sorted(set(S) | set(D), key=str)
    idx = {s: i for i, s in enumerate(states)}

    def ei(S, D):
        tpm = collections.defaultdict(collections.Counter)
        for a, b in zip(S, D):
            tpm[a][b] += 1
        srcs = list(tpm)
        n = len(srcs)
        if n < 2:
            return dict(n=n, EI=0.0, det=0.0, deg=0.0, eff=0.0)
        rowsP, meanP = [], [0.0] * len(states)
        for s in srcs:
            tot = sum(tpm[s].values())
            p = [0.0] * len(states)
            for b, c in tpm[s].items():
                p[idx[b]] = c / tot
            rowsP.append(p)
            for j, x in enumerate(p):
                meanP[j] += x / n
        mh = sum(H(p) for p in rowsP) / n
        hm = H(meanP)
        ln = math.log2(n)
        return dict(n=n, EI=hm - mh, det=ln - mh, deg=ln - hm, eff=(hm - mh) / ln)

    out = ei(S, D)
    rng = random.Random(SEED)
    nulls = []
    Dp = list(D)
    for _ in range(N_SHUFFLE):
        rng.shuffle(Dp)
        nulls.append(ei(S, Dp)["EI"])
    out["NULL"] = sum(nulls) / len(nulls)
    out["EI_corr"] = out["EI"] - out["NULL"]
    out["n_rare_visits"] = sum(1 for s in S if s == "RARE")
    out["transitions"] = len(S)
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="C:/Nascence/data")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = a.data
    fmt = lambda t: datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%dT%H:%M")

    pub = collections.defaultdict(set)   # tick -> loops published
    ignlvl = []                          # (ts, climate ignition_level)
    first, last = {}, {}

    def seen(name, t):
        first[name] = min(first.get(name, t), t)
        last[name] = max(last.get(name, t), t)

    for r in rows(os.path.join(d, "coupling_rides.jsonl")):
        if r.get("kind") != "publish":
            continue
        lp = r.get("loop")
        pub[int(r["ts"] // TICK)].add(lp)
        if lp in MICRO_LOOPS or lp == "climate":
            seen(lp, r["ts"])
        if lp == "climate":
            v = (r.get("tuple") or {}).get("ignition_level")
            if isinstance(v, (int, float)):
                ignlvl.append((r["ts"], float(v)))
    ign = set()
    for r in rows(os.path.join(d, "ignition_log.jsonl")):
        if r.get("trigger") == "deferred":   # J-2667: marker rows are not fires
            continue
        ign.add(int(r["ts"] // TICK)); seen("ignition", r["ts"])
    human = set()
    for r in rows(os.path.join(d, "provenance_log.jsonl")):
        if r.get("input_type") == "human":
            human.add(int(r["ts"] // TICK))
    sleep_ev = []
    for r in rows(os.path.join(d, "sleep_pressure_log.jsonl")):
        sleep_ev.append((r["ts"], r.get("reason") in ("sleep_entry", "sleep_beat"))); seen("sleep", r["ts"])
    arousal = []
    for r in rows(os.path.join(d, "arousal_shadow.jsonl")):
        if isinstance(r.get("level"), (int, float)):
            arousal.append((r["ts"], float(r["level"]))); seen("arousal", r["ts"])
    idle = []
    for r in rows(os.path.join(d, "logs", "idle_shadow.jsonl")):
        idle.append((r["ts"], str(r.get("would_pick_argmax")))); seen("idle", r["ts"])
    for s in (ignlvl, sleep_ev, arousal, idle):
        s.sort(key=lambda x: x[0])

    w0 = max(first[k] for k in ("stream", "witness", "ledgers", "deliberation", "climate", "sleep", "arousal", "idle"))
    w1 = min(last[k] for k in ("stream", "witness", "ledgers", "deliberation", "climate", "sleep", "arousal", "idle"))
    live = sorted(t for t, L in pub.items() if ({"climate", "stream"} & L) and w0 <= t * TICK <= w1)
    liveset = set(live)
    n3 = sum(1 for t in live if len(pub[t]) >= 3)

    sl_keys = [s[0] for s in sleep_ev]

    def asleep(t):
        i = bisect.bisect_right(sl_keys, t) - 1
        return bool(i >= 0 and sleep_ev[i][1])

    def state(t):
        T = t * TICK + TICK
        L = pub[t]
        bits = tuple(int(lp in L) for lp in MICRO_LOOPS) + (int(t in ign), int(t in human), int(asleep(T)))
        sl = bits[6]
        ab = band(carried(arousal, T), AROUSAL_CUTS)
        A = (sl, ab, carried(idle, T) or "none")
        B = (sl, ab, band(carried(ignlvl, T), IGNLVL_CUTS))
        C = (sl, sum(bits[:4]), int(bits[4] or bits[5]))
        return bits, A, B, C

    trans = [t for t in live if t + 1 in liveset]
    st = {}
    for t in trans:
        for u in (t, t + 1):
            if u not in st:
                st[u] = state(u)
    half = len(trans) // 2
    halves = {"h1": trans[:half], "h2": trans[half:]}

    res = dict(job="J-2513", window=[fmt(w0), fmt(w1)], live_ticks=len(live), ticks_3plus_loops=n3,
               transitions=len(trans), source_first={k: fmt(v) for k, v in first.items()},
               source_last={k: fmt(v) for k, v in last.items()},
               halves={h: dict(n=len(v), span=[fmt(v[0] * TICK), fmt(v[-1] * TICK)]) for h, v in halves.items() if v})
    if n3 < MIN_TICKS_3LOOPS or half < MIN_TRANS_PER_HALF:
        res["verdict"] = "INSUFFICIENT_ROWS"
    else:
        levels = {"micro": 0, "A": 1, "B": 2, "C": 3}
        res["occupancy"] = {}
        res["ei"] = {}
        for h, ts in halves.items():
            res["ei"][h] = {}
            for name, k in levels.items():
                src = [st[t][k] for t in ts]
                dst = [st[t + 1][k] for t in ts]
                res["ei"][h][name] = ei_of(src, dst)
                res["occupancy"].setdefault(name, {})[h] = len(set(src))
        wins = {(p, h): res["ei"][h][p]["EI_corr"] > res["ei"][h]["micro"]["EI_corr"] for p in ("A", "B") for h in halves}
        res["macro_beats_micro"] = {f"{p}_{h}": v for (p, h), v in wins.items()}
        res["C_beats_micro"] = {h: res["ei"][h]["C"]["EI_corr"] > res["ei"][h]["micro"]["EI_corr"] for h in halves}
        res["post_hoc"] = {"stay_rate": {}, "cross_ei_to_micro_next": {}}
        for h, ts in halves.items():
            res["post_hoc"]["stay_rate"][h] = {name: round(sum(st[t][k] == st[t + 1][k] for t in ts) / len(ts), 4)
                                              for name, k in levels.items()}
            res["post_hoc"]["cross_ei_to_micro_next"][h] = {
                name: ei_of([st[t][k] for t in ts], [st[t + 1][0] for t in ts], cross=True)
                for name, k in levels.items()}
        if all(wins.values()):
            res["verdict"] = "EMERGENCE"
        elif not any(wins.values()):
            res["verdict"] = "FALSIFIED_MICRO_WINS"
        else:
            res["verdict"] = "FALSIFIED_SIGN_FLIP"
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
