#!/usr/bin/env python
"""Does asking the Lane 2 coherence judge for a "why" move its coherent / incoherent answer? (J-3127, F-3854, P-0111)

For 20 stored tick pairs (RECENT RECORD + NEW OBSERVATION rebuilt from data/lane2_shadow.jsonl with the REAL
`core.lane2._coherence_check` prompt builder) the SAME judge is asked twice: with the OLD sysmsg (answer
{"coherent": bool}) and the NEW sysmsg (this build, {"coherent": bool, "why": str}).  Only the final instruction differs.
Reported per judge: answers that flipped, the coherent share under each wording, and the share of NEW answers carrying a
non-empty why (job target: at least 90 percent; mix movement of more than a few points means report and stop).

JUDGES.  Local hubs only: JUDGE_2 falcon3:7b (:11440, the production JUDGE_2 seat) and the lane2 tiebreak seat gemma4:12b
(:11439).  The production JUDGE_1 (mixtral, Ramses :11438) is NOT called -- Ramses is the founder's gaming machine -- so this
is a two-voice local read, not the production panel.  The Ramses leg is the spawned lab job.

SAMPLE.  Stratified by the logged panel verdict (default 10 incoherent + 10 coherent, fixed seed) so the incoherent rows,
the ones an audit cares about, are not drowned by the 86 percent coherent majority; the mix figures are therefore read as
flip counts per stratum, not as a population rate.

LIVE-STORE SAFE: reads the shadow log read-only; the panel ruling log is redirected to a temp dir; the only network
calls are to the local hubs above.  Imports `core` first and asserts it resolves inside this tree.

    python scripts/lane2_coherence_why_replay_J3127.py --data C:/Nascence/data --out C:/path/outside/repo/run.json
    --dry : no network at all (every judge answers True with a stub why), wiring check only
"""
import argparse
import asyncio
import collections
import json
import os
import random
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

import core as _core  # noqa: E402
assert os.path.abspath(_core.__file__).lower().startswith(ROOT.lower()), _core.__file__
from core import judge_panel as _jp  # noqa: E402
from core import lane2  # noqa: E402

_jp._LOG = type(_jp._LOG)(os.path.join(tempfile.mkdtemp(prefix="j3127_replay_"), "judge_panel_log.jsonl"))

NEW_TAIL = 'Output ONLY JSON: {"coherent": true|false, "why": "<one short clause>"}'
OLD_TAIL = 'Output ONLY JSON: {"coherent": true|false}'


def load_ticks(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
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


def fact(r):
    return {"ts": r.get("ts"), "notice": (r.get("notice") or "")[:200], "place": r.get("place"),
            "standpoint": r.get("standpoint")}


_CAP: dict = {}


async def _capture(system, user, key, context="", num_predict=0, tiebreak_url=None, **kw):
    _CAP["system"], _CAP["user"] = system, user
    return {"verdict": True, "how": "agreed"}


async def build(factual, notice, place, standpoint):
    """(system_new, user) from the REAL _coherence_check; system_old is system_new with the final instruction reverted."""
    real = _jp.rule_detail
    _jp.rule_detail = _capture
    try:
        _CAP.clear()
        await lane2._coherence_check({"notice": notice}, {"factual": factual},
                                     {"world": {"place": place}, "standpoint": standpoint})
    finally:
        _jp.rule_detail = real
    return _CAP.get("system"), _CAP.get("user")


async def ask(url, system, user, dry):
    if dry:
        return True, "stub why", None
    import aiohttp
    async with aiohttp.ClientSession() as s:
        v, why, err, _el = await _jp._ask(s, url, system, user, "coherent", timeout=150)
    return v, why, err


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="C:/Nascence/data")
    ap.add_argument("--out", default=None)
    ap.add_argument("--n-incoherent", type=int, default=10)
    ap.add_argument("--n-coherent", type=int, default=10)
    ap.add_argument("--seed", type=int, default=3127)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--only-new", action="store_true", help="skip the OLD-wording ask (why-coverage read only)")
    ap.add_argument("--first", type=int, default=0, help="only the first N picks (0 = all)")
    ap.add_argument("--judges", default="falcon", help="falcon (default, fast) | gemma | falcon,gemma (gemma is slow on the "
                                                      "shared CPU hub: tens of seconds per call, minutes when queued)")
    a = ap.parse_args()

    ticks = load_ticks(os.path.join(a.data, "lane2_shadow.jsonl"))
    cand = {"incoherent": [], "coherent": []}
    for i, r in enumerate(ticks):
        v = (r.get("coherence") or {}).get("verdict")
        if v in cand and i >= 6 and r.get("notice") and r.get("place") and r.get("standpoint"):
            cand[v].append(i)
    rng = random.Random(a.seed)
    picks = (rng.sample(cand["incoherent"], min(a.n_incoherent, len(cand["incoherent"])))
             + rng.sample(cand["coherent"], min(a.n_coherent, len(cand["coherent"]))))
    allj = {"falcon": ("falcon3:7b", _jp.JUDGE_2), "gemma": ("gemma4:12b", lane2._TIEBREAK_LANE2)}
    if a.first:
        picks = picks[:a.first]
    judges = [allj[k.strip()] for k in a.judges.split(",")]
    assert "LAN-HOST" not in "".join(u for _n, u in judges), "a judge URL points at Ramses"

    rows, t0 = [], time.time()
    for i in picks:
        r = ticks[i]
        factual = [fact(x) for x in ticks[max(0, i - 6):i]]
        sys_new, usr = await build(factual, r["notice"], r.get("place"), r.get("standpoint"))
        if not sys_new or not sys_new.endswith(NEW_TAIL):
            raise SystemExit("system prompt does not end with the J-3127 instruction; wrong tree?")
        sys_old = sys_new[: -len(NEW_TAIL)] + OLD_TAIL
        row = {"i": i, "ts": r.get("ts"), "logged": (r.get("coherence") or {}).get("verdict"),
               "notice": r["notice"][:120]}
        for name, url in judges:
            vo, eo = (None, "skipped") if a.only_new else (await ask(url, sys_old, usr, a.dry))[::2]
            vn, wn, en = await ask(url, sys_new, usr, a.dry)
            row[name] = {"old": vo, "new": vn, "why": wn, "err_old": eo, "err_new": en}
        rows.append(row)
        if a.out:        # incremental: a hub timeout mid-run must not lose the rows already read
            with open(a.out + ".partial", "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=1)
        print(f"[{len(rows)}/{len(picks)}] t={time.time() - t0:.0f}s logged={row['logged']} "
              + " ".join(f"{n}:{row[n]['old']}->{row[n]['new']}" for n, _u in judges), flush=True)

    summary = {}
    for name, _u in judges:
        ok = [r for r in rows if r[name]["old"] is not None and r[name]["new"] is not None]
        flips = [r for r in ok if r[name]["old"] != r[name]["new"]]
        answered_new = [r for r in rows if r[name]["new"] is not None]
        with_why = [r for r in answered_new if str(r[name]["why"] or "").strip()]
        by_strat = collections.defaultdict(lambda: {"n": 0, "old_coherent": 0, "new_coherent": 0, "flips": 0})
        for r in ok:
            b = by_strat[r["logged"]]
            b["n"] += 1
            b["old_coherent"] += bool(r[name]["old"])
            b["new_coherent"] += bool(r[name]["new"])
            b["flips"] += r[name]["old"] != r[name]["new"]
        summary[name] = {"rows": len(rows), "both_answered": len(ok), "flipped": len(flips),
                         "old_coherent_share": round(sum(bool(r[name]["old"]) for r in ok) / len(ok), 3) if ok else None,
                         "new_coherent_share": round(sum(bool(r[name]["new"]) for r in ok) / len(ok), 3) if ok else None,
                         "new_answered": len(answered_new), "new_with_why": len(with_why),
                         "why_coverage": round(len(with_why) / len(answered_new), 3) if answered_new else None,
                         "by_logged_verdict": dict(by_strat)}
    out = {"seed": a.seed, "dry": a.dry, "judges": dict(judges), "ramses_calls": 0, "summary": summary, "rows": rows}
    print(json.dumps(summary, indent=2))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
