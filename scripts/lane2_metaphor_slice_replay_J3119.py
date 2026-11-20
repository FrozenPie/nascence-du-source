#!/usr/bin/env python
"""Replay Lane 2's `_judge_metaphor` over stored ticks, OLD passage (joined fields cut at 500 characters) vs NEW
passage (three labelled fields, cut at NEW_CUT), J-3119 / F-3840 / P-0110.

The sysmsg is the REAL one: it is captured by driving `core.lane2._judge_metaphor` itself with
`judge_panel.rule_detail` swapped for a recorder, so the replay can never drift from the shipped prompt.  The OLD user
message is whatever `_judge_metaphor` builds today (so after J-3119 is edited, OLD here is rebuilt by `old_passage()`
below, which keeps the pre-edit 500-cut join for comparison).

ROW SETS (from data/lane2_shadow.jsonl, kind=tick):
  long    every tick since the 2026-10-29 18:30 boot whose joined notice+uncertain+expect_next is over 500 characters
          (the F-3840 population; 48 of 378 on 11-01, more now)
  splits  every tick the LIVE metaphor panel answered by TIEBREAK (or split_no_tiebreak, or 'agreed' metaphor): the
          stored stand-in for F-2876's 128 replayed splits (the replay output itself was not kept)

JUDGES: JUDGE_1 mixtral lives on RAMSES (the founder's gaming machine) so this script never calls it unless
`--allow-ramses`.  Default is LOCAL single-judge A/B: gemma4:12b :11439 (the tiebreak seat; F-2876 found every panel
metaphor verdict was JUDGE_1 True + gemma True and falcon3 False on every call, so gemma-alone True is the upper bound on
what the panel can call metaphor) and falcon3:7b :11440.  Read it as "does the longer, labelled passage move one judge",
not as the shipped panel's verdict.

    python scripts/lane2_metaphor_slice_replay_J3119.py --dry
    python scripts/lane2_metaphor_slice_replay_J3119.py --local gemma --out C:/somewhere/outside/repo/j3119.json
    python scripts/lane2_metaphor_slice_replay_J3119.py --judges panel --allow-ramses     # the real panel, ~4 calls/row
"""
import argparse
import asyncio
import collections
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import core  # noqa: E402,F401  (core BEFORE anything that touches lab_env)
from core import lane2  # noqa: E402
from core import judge_panel as jp  # noqa: E402

assert os.path.abspath(lane2.__file__).startswith(ROOT), lane2.__file__

BOOT_TS = time.mktime((2026, 10, 29, 18, 30, 0, 0, 0, -1))
LOCAL = {"falcon": "http://127.0.0.1:11440", "gemma": "http://127.0.0.1:11439"}
HOT = "http://127.0.0.1:11433"   # ollama hot lane (1080 Ti, GPU): qwen3.5:9b answers in ~1 s; the CPU hubs take minutes/call
HOT_MODEL = "qwen3.5:9b"
GEMMA_TIMEOUT = 400              # judge_panel._TIMEOUT is 90 s; the shared CPU hubs measured ~100 s+/call on 2026-11-06
FIELDS = (("NOTICE", "notice"), ("UNCERTAIN", "uncertain"), ("EXPECTS", "expect_next"))
OLD_CUT = 500
NEW_CUT = 1500   # F-3840 asked for 1,200; the longest labelled passage since the boot is 1,469 characters


def old_passage(r):
    """The pre-J-3119 user message body: the three fields joined with bare spaces, cut at 500."""
    said = " ".join(str(r.get(k) or "") for _l, k in FIELDS)
    return said[:OLD_CUT]


def new_passage(r, cut=NEW_CUT):
    """Labelled fields (empty ones omitted), cut at `cut`."""
    parts = []
    for label, k in FIELDS:
        v = str(r.get(k) or "").strip()
        if v:
            parts.append(f"{label}: {v}")
    return " ".join(parts)[:cut]


def load_rows(shadow_path):
    rows = []
    with open(shadow_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"kind": "tick"' not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("kind") == "tick":
                rows.append(r)
    return rows


def pick(rows):
    long_, splits = {}, {}
    for r in rows:
        said = " ".join(str(r.get(k) or "") for _l, k in FIELDS)
        if not said.strip():
            continue
        mj = r.get("metaphor_judged") or {}
        if (r.get("ts") or 0) >= BOOT_TS and len(said) > OLD_CUT:
            long_[r["ts"]] = r
        if mj.get("how") in ("tiebreak", "split_no_tiebreak") or (mj.get("verdict") == "metaphor"):
            splits[r["ts"]] = r
    both = {**long_, **splits}
    return both, set(long_), set(splits)


def capture_sysmsg():
    """Run the shipped `_judge_metaphor` against a recorder and return (sysmsg, user_message_for_a_probe_row)."""
    got = {}

    async def rec(system, user, key, context="", tiebreak_url=None, **kw):
        got["system"], got["user"], got["key"], got["tiebreak_url"] = system, user, key, tiebreak_url
        return {"verdict": False, "how": "agreed", "why": "rec"}
    real = jp.rule_detail
    jp.rule_detail = rec
    try:
        asyncio.run(lane2._judge_metaphor({"notice": "x", "uncertain": "y", "expect_next": "z"}))
    finally:
        jp.rule_detail = real
    return got


async def _ask_hot(session, system, user, key):
    """One-judge ask against the ollama hot lane (qwen3.5:9b, thinking off, JSON). Same (verdict, why) contract."""
    import aiohttp
    payload = {"model": HOT_MODEL, "stream": False, "format": "json", "think": False, "keep_alive": "20m",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 200}}
    try:
        async with session.post(HOT + "/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=300)) as resp:
            resp.raise_for_status()
            data = await resp.json()
        v = json.loads((data.get("message") or {}).get("content") or "")
        if isinstance(v, dict) and isinstance(v.get(key), bool):
            return v[key], v.get("why") if isinstance(v.get("why"), str) else None
    except Exception:
        pass
    return None, None


async def run(rows, sysmsg, mode, local_names, dry, out=""):
    results = []
    session = None
    real_rule_detail = jp.rule_detail
    if mode == "local" and not dry:
        import aiohttp
        session = aiohttp.ClientSession()
    judges = local_names if mode == "local" else ["panel"]
    for judge in judges:
        for i, r in enumerate(rows, 1):
            res = {"judge": judge, "ts": r["ts"], "live": (r.get("metaphor_judged") or {}).get("verdict"),
                   "live_how": (r.get("metaphor_judged") or {}).get("how"),
                   "old_len": len(old_passage(r)), "new_len": len(new_passage(r)),
                   "same_text": len(" ".join(str(r.get(k) or "") for _l, k in FIELDS)) <= OLD_CUT}
            for variant, text in (("old", old_passage(r)), ("new", new_passage(r))):
                usr = f"PASSAGE: {text}"
                if dry:
                    v, why = False, "dry"
                elif mode == "local" and judge == "hot":
                    v, why = await _ask_hot(session, sysmsg, usr, "metaphor")
                elif mode == "local":
                    v, why, _err, _el = await jp._ask(session, LOCAL[judge], sysmsg, usr, "metaphor",
                                                      timeout=GEMMA_TIMEOUT)
                else:
                    d = await real_rule_detail(sysmsg, usr, "metaphor", context="lane2:metaphor_replay_J3119",
                                               tiebreak_url=lane2._TIEBREAK_LANE2)
                    v, why = d.get("verdict"), d.get("why")
                res[variant] = "metaphor" if v is True else "literal" if v is False else "cannot_tell"
                res[variant + "_why"] = why
            res["old_text"], res["new_text"] = old_passage(r), new_passage(r)
            results.append(res)
            if out:
                with open(out, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=1)
            print(f"  [{judge} {i}/{len(rows)}] live={str(res['live']):<10} old={res['old']:<10} "
                  f"new={res['new']:<10} len {res['old_len']}->{res['new_len']}", flush=True)
    if session is not None:
        await session.close()
    return results


def report(results, long_ts, split_ts):
    for judge in sorted({x["judge"] for x in results}):
        rs = [x for x in results if x["judge"] == judge]
        print(f"\n== judge: {judge}  rows: {len(rs)}")
        for name, sel in (("all", rs), ("long (>500)", [x for x in rs if x["ts"] in long_ts]),
                          ("splits", [x for x in rs if x["ts"] in split_ts])):
            c_old = collections.Counter(x["old"] for x in sel)
            c_new = collections.Counter(x["new"] for x in sel)
            mv = collections.Counter((x["old"], x["new"]) for x in sel if x["old"] != x["new"])
            print(f"  {name:<12} n={len(sel):<4} OLD {dict(c_old)}  NEW {dict(c_new)}  moved {dict(mv) or 'none'}")
        lab_only = [x for x in rs if x["same_text"]]
        mv_lab = collections.Counter((x["old"], x["new"]) for x in lab_only if x["old"] != x["new"])
        print(f"  label-only rows (joined text <=500, nothing cut; only labels differ): n={len(lab_only)} moved {dict(mv_lab) or 'none'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="C:/Nascence/data")
    ap.add_argument("--judges", choices=("local", "panel"), default="local")
    ap.add_argument("--local", default="hot", help="comma list of local judges: hot (qwen3.5:9b GPU), falcon, gemma")
    ap.add_argument("--long-until", type=float, default=0, help="keep long ticks with ts <= this (epoch)")
    ap.add_argument("--splits-sample", type=int, default=0, help="spread of N non-long split ticks (label-only effect)")
    ap.add_argument("--only-ts", default="", help="comma list of tick ts to replay (e.g. the rows the hot judge moved)")
    ap.add_argument("--limit", type=int, default=0, help="rows to replay (0 = all)")
    ap.add_argument("--allow-ramses", action="store_true", help="required for --judges panel (mixtral is on Ramses)")
    ap.add_argument("--dry", action="store_true", help="no network: constant stub judge, a wiring check only")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    if a.judges == "panel" and not a.allow_ramses and not a.dry:
        print("REFUSED: --judges panel calls JUDGE_1 mixtral on Ramses (the founder's gaming machine). "
              "Pass --allow-ramses when he is not playing, or use --judges local.")
        return 2
    rows = load_rows(os.path.join(a.data, "lane2_shadow.jsonl"))
    pool, long_ts, split_ts = pick(rows)
    chosen = [pool[k] for k in sorted(pool)]
    if a.long_until or a.splits_sample:
        # the F-3840 population as the briefing counted it: long ticks up to the finding's date, plus a spread of splits
        sp = sorted(split_ts - long_ts)
        keep_sp = set(sp[::max(1, len(sp) // a.splits_sample)][:a.splits_sample]) if a.splits_sample else set()
        chosen = [r for r in chosen if (r["ts"] in long_ts and (not a.long_until or r["ts"] <= a.long_until))
                  or r["ts"] in keep_sp]
        long_ts = {t for t in long_ts if not a.long_until or t <= a.long_until}
    if a.only_ts:
        want = {float(x) for x in a.only_ts.split(",") if x}
        chosen = [r for r in chosen if float(r["ts"]) in want]
    if a.limit:
        step = max(1, len(chosen) // a.limit)
        chosen = chosen[::step][:a.limit]
    got = capture_sysmsg()
    print(f"ticks {len(rows)}; long {len(long_ts)}; splits {len(split_ts)}; replay pool {len(chosen)}; "
          f"sysmsg {len(got['system'])} chars; tiebreak_url {got['tiebreak_url']}")
    res = asyncio.run(run(chosen, got["system"], a.judges, [s for s in a.local.split(",") if s], a.dry, a.out))
    report(res, long_ts, split_ts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
