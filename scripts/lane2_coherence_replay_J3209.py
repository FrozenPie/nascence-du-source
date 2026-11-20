#!/usr/bin/env python
"""Replay the Lane 2 COHERENCE judge over the last N logged ticks, BEFORE vs AFTER the D-0599 (2) repoint (J-3209).

BEFORE = what the live panel actually ruled: the tick row's own `coherence` verdict in data/lane2_shadow.jsonl, whose
split votes were settled by the shared granite TIEBREAK (Ramses :11437).
AFTER  = the REAL `core.lane2._coherence_check` path, now passing `tiebreak_url=_TIEBREAK_LANE2` (gemma4:12b, local
:11439).  JUDGE_1 (mixtral, Ramses :11438) and JUDGE_2 (falcon3, local :11440) are NOT re-asked: their LOGGED votes
(data/judge_panel_log.jsonl, matched to the tick by timestamp) are replayed, so this script makes ZERO Ramses calls and
only asks the gemma hub, once per logged split (about 54 of 245).  Agreed rows keep their verdict by construction;
only splits can move.

What is reconstructed, not logged (so read the AFTER column as a close replay, not a byte-exact one): the prompt's
RECENT RECORD is rebuilt from the previous tick rows' notice/place/standpoint (the live `store["factual"]` tier, last 6
entries with a notice) and the NEW OBSERVATION from the tick row's own place/standpoint/notice.  The store can have
been trimmed or restarted between ticks, which this cannot see.  The row alignment check (aligned_consistent) reports
how many ticks' logged coherence verdict agrees with the matched panel-log row, a check on the vote matching.

LIVE-STORE SAFE: reads the shadow log and judge_panel_log read-only; the panel's own ruling log (_LOG) and telemetry are
redirected/stubbed; the only network call is the tiebreak ask to the local gemma hub.  Imports `core` first and asserts it
resolves inside this tree.

    python scripts/lane2_coherence_replay_J3209.py --data C:/Nascence/data --n 245 --out C:/path/outside/repo/run.json
    --dry : no network at all (the tiebreak answers a constant, for a wiring check only)
"""
import argparse
import asyncio
import collections
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def load_ticks(shadow_path):
    """Every kind=='tick' row of the shadow log, in order (cheap substring prefilter before json.loads)."""
    out = []
    with open(shadow_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"kind": "tick"' not in line[:120]:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("kind") == "tick":
                out.append(r)
    return out


def load_coherence_votes(panel_log_path, since_ts):
    out = []
    with open(panel_log_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if "lane2:coherence" not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("context") == "lane2:coherence" and (r.get("ts") or 0) >= since_ts:
                out.append(r)
    return out


def select_targets(ticks, n):
    """The last n ticks that carry a coherence verdict, each with the previous <=6 notice-bearing ticks as its factual tier."""
    idx = [i for i, r in enumerate(ticks) if (r.get("coherence") or {}).get("verdict")]
    idx = idx[-n:]
    targets = []
    for i in idx:
        recent = [t for t in ticks[:i] if t.get("notice")][-6:]
        store = {"factual": [{"notice": (t.get("notice") or "")[:200], "standpoint": t.get("standpoint"),
                              "place": t.get("place")} for t in recent]}
        r = ticks[i]
        targets.append({"tick": r, "store": store, "out": {"notice": r.get("notice") or ""},
                        "percepts": {"world": {"place": r.get("place")}, "standpoint": r.get("standpoint")}})
    return targets


def align(targets, votes, window_s=400.0):
    """Each target takes the first unused panel-log row with ts in [tick_ts - 5, tick_ts + window_s]."""
    used = set()
    lags = []
    for t in targets:
        ts = t["tick"]["ts"]
        t["vote"] = None
        for j, v in enumerate(votes):
            if j in used:
                continue
            if ts - 5 <= v["ts"] <= ts + window_s:
                used.add(j)
                t["vote"] = v
                lags.append(round(v["ts"] - ts, 1))
                break
    return lags


def _dist(verdicts):
    c = collections.Counter(verdicts)
    n = sum(c.values()) or 1
    return {str(k): {"n": v, "share": round(v / n, 3)} for k, v in sorted(c.items(), key=lambda kv: str(kv[0]))}


async def replay(targets, jp, lane2, tiebreak_ask=None):
    """Run the REAL _coherence_check on every target with JUDGE_1/JUDGE_2 answering their logged votes.
    `tiebreak_ask(url, system, user, key)` -> (verdict, why, err, secs) answers any other URL (the gemma seat); when
    None the real `jp._ask` is used (a real network call to that URL)."""
    real_ask = jp._ask
    state = {"vote": None, "tb_calls": 0, "tb_urls": collections.Counter()}

    async def fake_ask(session, url, system, user, key, timeout=jp._TIMEOUT, num_predict=jp._NUM_PREDICT):
        v = state["vote"] or {}
        if url == jp.JUDGE_1:
            return v.get("v1"), None, ("replay-none" if v.get("v1") is None else None), 0.0
        if url == jp.JUDGE_2:
            return v.get("v2"), None, ("replay-none" if v.get("v2") is None else None), 0.0
        state["tb_calls"] += 1
        state["tb_urls"][url] += 1
        if tiebreak_ask is not None:
            return await tiebreak_ask(url, system, user, key)
        return await real_ask(session, url, system, user, key, timeout=timeout, num_predict=num_predict)

    jp._ask = fake_ask
    results = []
    try:
        for t in targets:
            state["vote"] = t["vote"]
            if t["vote"] is None:
                results.append({"ts": t["tick"]["ts"], "after": None, "after_how": "no-vote-matched"})
                continue
            r = await lane2._coherence_check(t["out"], t["store"], t["percepts"])
            results.append({"ts": t["tick"]["ts"], "after": r.get("verdict"), "after_how": r.get("how")})
    finally:
        jp._ask = real_ask
    return results, state


def summarise(targets, results, lags, tb_state):
    before = [(t["tick"].get("coherence") or {}).get("verdict") for t in targets]
    after = [r["after"] for r in results]
    trans = collections.Counter(f"{b}->{a}" for b, a in zip(before, after))
    splits = [(t, r) for t, r in zip(targets, results) if (t["vote"] or {}).get("how") in ("tiebreak", "split_no_tiebreak")]
    aligned = [t for t in targets if t["vote"] is not None]
    consistent = sum(1 for t in aligned
                     if t["vote"].get("verdict") is not None
                     and ((t["vote"].get("verdict") is True) == ((t["tick"].get("coherence") or {}).get("verdict") == "coherent")))
    granite_true = sum(1 for t, _r in splits if t["vote"].get("verdict") is True)
    gemma_true = sum(1 for _t, r in splits if r["after"] == "coherent")
    agree = sum(1 for t, r in splits if r["after"] in ("coherent", "incoherent")
                and (t["vote"].get("verdict") is True) == (r["after"] == "coherent"))
    return {
        "n_ticks": len(targets), "n_vote_matched": len(aligned), "aligned_consistent": consistent,
        "align_lag_s": {"min": min(lags) if lags else None, "median": sorted(lags)[len(lags) // 2] if lags else None,
                        "max": max(lags) if lags else None},
        "before_logged": _dist(before), "after_replay": _dist(after), "transitions": dict(trans),
        "splits": {"n": len(splits), "granite_logged_coherent": granite_true, "gemma_replay_coherent": gemma_true,
                   "agree_n": agree},
        "tiebreak_calls": tb_state["tb_calls"], "tiebreak_urls": dict(tb_state["tb_urls"]),
    }


def stat(p):
    try:
        s = os.stat(p)
        return (s.st_size, s.st_mtime_ns)
    except OSError as e:
        return ("ERR", str(e))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", default=r"C:\Nascence\data")
    ap.add_argument("--n", type=int, default=245)
    ap.add_argument("--out", required=True, help="results json; keep it OUTSIDE the repo")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    import core                                   # BEFORE anything else
    from core import judge_panel as jp, lane2, telemetry
    assert os.path.realpath(core.__file__).lower().startswith(os.path.realpath(ROOT).lower()), core.__file__
    telemetry.log_llm_call = lambda *x, **k: None
    tmp = tempfile.mkdtemp(prefix="j3209_replay_")
    jp._LOG = type(jp._LOG)(os.path.join(tmp, "judge_panel_log.jsonl"))      # never the live ruling log

    shadow = os.path.join(a.data, "lane2_shadow.jsonl")
    panel = os.path.join(a.data, "judge_panel_log.jsonl")
    live = [shadow, panel]
    before_stat = {p: stat(p) for p in live}

    ticks = load_ticks(shadow)
    targets = select_targets(ticks, a.n)
    votes = load_coherence_votes(panel, targets[0]["tick"]["ts"] - 60)
    lags = align(targets, votes)

    async def dry_tb(url, system, user, key):
        return True, None, None, 0.0

    t0 = time.time()
    results, st = asyncio.run(replay(targets, jp, lane2, tiebreak_ask=dry_tb if a.dry else None))
    summ = summarise(targets, results, lags, st)
    summ["tiebreak_seat"] = lane2._TIEBREAK_LANE2
    summ["dry"] = a.dry
    summ["wall_s"] = round(time.time() - t0, 1)
    summ["live_files_unchanged"] = before_stat == {p: stat(p) for p in live}
    rows = [{"ts": t["tick"]["ts"], "before": (t["tick"].get("coherence") or {}).get("verdict"),
             "panel_how": (t["vote"] or {}).get("how"), "v1": (t["vote"] or {}).get("v1"),
             "v2": (t["vote"] or {}).get("v2"), "granite": (t["vote"] or {}).get("verdict"),
             "after": r["after"], "after_how": r["after_how"], "notice": t["tick"].get("notice")}
            for t, r in zip(targets, results)]
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"summary": summ, "rows": rows}, f, indent=1, ensure_ascii=False)
    print(json.dumps(summ, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
