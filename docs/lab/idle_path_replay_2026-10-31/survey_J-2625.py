"""J-2625 era survey + closed-loop check of data/logs/idle_shadow.jsonl (streams the FULL live log, read-only, no core import).

Checks, per consecutive row pair (t, t+1):
  K1 streak recurrence: every candidate's winner_streak at t+1 == (streak_t[ch] + 1 if argmax_t == ch else 0),
     where streak_t[ch] is ch's logged winner_streak at t (0 if ch was not a candidate at t). Holds iff the module's
     habituation state is fed by its OWN argmax pick and nothing else (code: core/idle_allocator.py lines 407-411).
  K2 s_final == max(0, p_norm * weight * (1 - 0.15 * winner_streak)) within 1e-3 (line 343).
  K3 would_pick_argmax == first candidate with max logged s_final (line 359; logged values are rounded, ties reported).
  K4 'actual' non-null count (the only real-action field; the only caller, nodes/inner_monologue_node.py ~2694, never passes it).
  K5 p_norm vs percentile over a history rebuilt from the log's own raws (rolling 500, cold < 20 -> 0.5; concern bypass
     raw/0.55 when its p_norm is a declared level) - history is fed by EVERY candidate's raw, never by the pick.
Per day: rows, argmax modal + share, softmax != argmax share, distinct argmax channels, longest argmax run, max streak,
  'no-habituation' argmax (argmax of p_norm*weight) != logged argmax share (how much the path channel moves the pick).
"""
import collections, datetime as dt, json, sys
LOG = r"C:\Nascence\data\logs\idle_shadow.jsonl"
DELTA = 0.15
hist = collections.defaultdict(list)
prev = None
day = collections.defaultdict(lambda: collections.Counter())
runs = collections.defaultdict(int); cur_run = [None, 0, None]
K = collections.Counter(); first_k1_fail = []
gaps = []
with open(LOG, encoding="utf-8") as f:
    for ln in f:
        try:
            r = json.loads(ln)
        except Exception:
            K["bad"] += 1; continue
        K["rows"] += 1
        d = dt.datetime.fromtimestamp(r["ts"]).strftime("%Y-%m-%d")
        c = day[d]; c["rows"] += 1
        cands = r.get("candidates") or []
        am = r.get("would_pick_argmax"); sm = r.get("would_pick_softmax")
        if r.get("actual") is not None: K["actual_nonnull"] += 1
        c["am:" + str(am)] += 1
        if sm != am: c["soft_ne_arg"] += 1
        # K2/K3
        for x in cands:
            exp = max(0.0, x["p_norm"] * x["weight"] * (1 - DELTA * x["winner_streak"]))
            if abs(exp - x["s_final"]) > 1e-3: K["k2_fail"] += 1
            c["maxstreak"] = max(c["maxstreak"], x["winner_streak"])
        if cands:
            mx = max(x["s_final"] for x in cands)
            top = [x["channel"] for x in cands if x["s_final"] == mx]
            if len(top) > 1: K["k3_ties"] += 1
            if top[0] != am: K["k3_fail"] += 1
            nh = max(cands, key=lambda x: x["p_norm"] * x["weight"])["channel"]
            if nh != am: c["nohab_ne_arg"] += 1
        # K1
        if prev is not None:
            gap = r["ts"] - prev["ts"]
            if gap > 900: gaps.append((d, round(gap)))
            ps = {x["channel"]: x["winner_streak"] for x in prev.get("candidates") or []}
            pam = prev.get("would_pick_argmax")
            for x in cands:
                e = ps.get(x["channel"], 0) + 1 if pam == x["channel"] else 0
                K["k1_checked"] += 1
                if x["winner_streak"] != e:
                    K["k1_fail"] += 1
                    if len(first_k1_fail) < 8: first_k1_fail.append((d, x["channel"], x["winner_streak"], e, round(gap)))
        # K5
        for x in cands:
            h = hist[x["channel"]]
            if x["channel"] == "concern" and abs(x["p_norm"] - min(1.0, x["raw"] / 0.55)) < 1e-3 and len(h) >= 20:
                K["k5_concern_bypass"] += 1
            else:
                exp = 0.5 if len(h) < 20 else sum(1 for v in h if v <= x["raw"]) / len(h)
                K["k5_checked"] += 1
                if abs(exp - x["p_norm"]) > 1e-3: K["k5_fail"] += 1; c["k5_fail"] += 1
        for x in cands:
            h = hist[x["channel"]]; h.append(x["raw"])
            if len(h) > 500: del h[0]
        # runs
        if cur_run[0] == am and cur_run[2] == d: cur_run[1] += 1
        else: cur_run = [am, 1, d]
        c["longest"] = max(c["longest"], cur_run[1])
        prev = r
print(json.dumps(K))
print("first_k1_fail", first_k1_fail)
print("gaps>900s", len(gaps), gaps[:40])
for d in sorted(day):
    c = day[d]; n = c["rows"]
    ams = {k[3:]: v for k, v in c.items() if k.startswith("am:")}
    mod = max(ams, key=ams.get)
    print(d, n, "modal", mod, round(ams[mod] / n, 2), "distinct", len(ams), "longest", c["longest"], "maxstreak", c["maxstreak"],
          "soft!=arg", round(c["soft_ne_arg"] / n, 2), "nohab!=arg", round(c["nohab_ne_arg"] / n, 2), "k5fail", c["k5_fail"],
          " ".join(f"{k}:{v}" for k, v in sorted(ams.items(), key=lambda kv: -kv[1])))
