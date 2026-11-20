#!/usr/bin/env python
"""Replay Lane 2's `_judge_prior` over the stored judged rows, OLD prompt vs NEW prompt (the MADE line + tolerance
sentence), J-3099 / F-3815 / P-0109.

The prompts are the REAL ones: this drives `core.lane2._judge_prior` itself with `JUDGE_MADE_LINE` switched off (OLD, the
byte-identical pre-J-3099 strings) and on (NEW).  Each row supplies what the live tick had: the stored
`judged_expect`, the judging tick's own `percept_lines` (what the judge was shown), and `judged_age_s` /
`judged_horizon` / `judged_pred_place` (the prediction's own record).

TWO MODES, because JUDGE_1 (mixtral, :11438) lives on RAMSES, the founder's gaming machine:
  --judges local   (default) ONE local family answers alone, through the shared `judge_panel._ask`: falcon3:7b :11440
                   and/or gemma4:12b :11439 (`--local falcon,gemma`).  Zero Ramses calls.  The two asks run exactly as
                   `_judge_prior` runs them (held first; contradicted only if held did not resolve true).  This is a
                   single-judge A/B, NOT the two-family panel: read it as "does the new text move one judge the right
                   way", not as the shipped panel's verdict.
  --judges panel   the REAL panel (mixtral + falcon + gemma tiebreak) via `judge_panel.rule_detail`, with its ruling log
                   redirected to a temp file.  This is the briefing's pass-criteria replay.  It calls Ramses (about 2 to 4
                   calls per row per variant, so ~800 to 1,600 calls for 205 rows) and REFUSES to run without
                   `--allow-ramses`.  Run it only when the founder is not gaming.

ROW SET: judged tick rows (kind=tick, prior_verdict held/broke/unsettled/cannot_tell) since the 2026-10-29 18:30 boot.
`--survivors` (default on) keeps only the rows Wave E would still send to the judge today (J-3160 trivial predictions
are not stored; J-3035 closes a prediction older than horizon + `_STALE_AFTER_S`); `--all` replays every row.

OUTPUT: counts per variant, the verdict-movement matrix OLD -> NEW, the recorded (live) verdict beside each, and the four
rows F-3815 names (clock 09:55, sun 3866 s, azimuth 26.9 / 301.1, 16.8 h sun).  PASS (briefing): the clock and the 3,866 s
sun claim move to broke, the 16.8 h claim is not held, held-by-list rows stay held, the broke count does not rise by
more than the real misses.  The script prints the counts; a person reads them.  It writes nothing under the repo.

    python scripts/lane2_judge_made_replay_J3099.py --data C:/Nascence/data --limit 20 --local falcon
    python scripts/lane2_judge_made_replay_J3099.py --dry             # no network: wiring check with a constant stub
    python scripts/lane2_judge_made_replay_J3099.py --judges panel --allow-ramses --out C:/somewhere/outside/repo/run.json
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

import core  # noqa: E402,F401  (core BEFORE anything that touches lab_env)
from core import lane2  # noqa: E402
from core import judge_panel as jp  # noqa: E402

assert os.path.abspath(lane2.__file__).startswith(ROOT), lane2.__file__

BOOT_TS = time.mktime((2026, 10, 29, 18, 30, 0, 0, 0, -1))
LOCAL = {"falcon": "http://127.0.0.1:11440", "gemma": "http://127.0.0.1:11439"}
VERDICTS = ("held", "broke", "unsettled", "cannot_tell")
NAMED = (  # (label, substring of judged_expect, near-age seconds or None)
    ("clock 09:55 (age ~350 s)", "the clock will show 10:05", None),
    ("sun 'within the next hour' (age ~3866 s)", "Within the next hour, the sun will reach its highest point", None),
    ("azimuth 26.9 (age ~372 s)", "azimuth at 26.9", None),
    ("azimuth 301.1 (age ~662 s)", "301.1 degrees", None),
    ("sun 16.8 h (age ~60318 s)", "In the next hour, the sun will be at its highest point", None),
)


def load_rows(shadow_path):
    out = []
    with open(shadow_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"judged_expect"' not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if (r.get("kind") == "tick" and (r.get("ts") or 0) >= BOOT_TS and r.get("judged_expect")
                    and r.get("prior_verdict") in VERDICTS and r.get("percept_lines")):
                out.append(r)
    return out


def survives_wave_e(r):
    """True when today's tick() would still hand this row's prediction to the judge (J-3160 + J-3035)."""
    if lane2._trivial_prediction_flag(r.get("judged_expect") or ""):
        return False
    age, h = r.get("judged_age_s"), r.get("judged_horizon")
    due = lane2.HORIZONS.get(h)
    if age is not None and due is not None and float(age) > due + lane2._STALE_AFTER_S:
        return False
    return True


def pick(rows, limit):
    """Named F-3815 rows first (always), then an even spread of the rest, up to `limit` in total."""
    chosen, seen = [], set()
    for _label, needle, _ in NAMED:
        for r in rows:
            if needle in (r.get("judged_expect") or "") and id(r) not in seen:
                chosen.append(r)
                seen.add(id(r))
    rest = [r for r in rows if id(r) not in seen]
    room = max(0, limit - len(chosen)) if limit else len(rest)
    if room and rest:
        step = max(1, len(rest) // room)
        chosen += rest[::step][:room]
    return chosen


async def _one(r, flag):
    lane2.JUDGE_MADE_LINE = flag
    lane2.percept_lines = lambda p, _t=r["percept_lines"]: _t
    return await lane2._judge_prior(r["judged_expect"], {}, age_s=r.get("judged_age_s"),
                                    horizon=r.get("judged_horizon"), pred_place=r.get("judged_pred_place"))


async def run(rows, mode, local_names, dry, out=""):
    results = []
    session = None
    real_rule_detail = jp.rule_detail
    if mode == "local" and not dry:
        import aiohttp
        session = aiohttp.ClientSession()
    for judge in (local_names if mode == "local" else ["panel"]):
        if mode == "local":
            url = LOCAL[judge]

            async def single(system, user, key, context="", tiebreak_url=None, **kw):
                if dry:
                    return {"verdict": False, "how": "agreed", "why": "dry"}
                v, why, err, _el = await jp._ask(session, url, system, user, key)
                return {"verdict": v, "how": "agreed" if v is not None else "unavailable", "why": why}
            jp.rule_detail = single
        else:
            jp.rule_detail = real_rule_detail
        for i, r in enumerate(rows, 1):
            old = await _one(r, False)
            new = await _one(r, True)
            results.append({"judge": judge, "ts": r["ts"], "expect": r["judged_expect"][:140],
                            "age_s": r.get("judged_age_s"), "horizon": r.get("judged_horizon"),
                            "place": r.get("judged_pred_place"), "recorded": r["prior_verdict"],
                            "old": old["verdict"], "new": new["verdict"],
                            "old_why": old.get("contradicted_why") or old.get("why"),
                            "new_why": new.get("contradicted_why") or new.get("why")})
            if out:   # partial results survive a kill: a slow CPU hub can take many minutes per row
                with open(out, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=1)
            print(f"  [{judge} {i}/{len(rows)}] recorded={r['prior_verdict']:<11} old={old['verdict']:<11} "
                  f"new={new['verdict']:<11} {r['judged_expect'][:60]!r}", flush=True)
    jp.rule_detail = real_rule_detail
    if session is not None:
        await session.close()
    return results


def report(results):
    for judge in sorted({x["judge"] for x in results}):
        rs = [x for x in results if x["judge"] == judge]
        print(f"\n== judge: {judge}  rows: {len(rs)}")
        for col in ("recorded", "old", "new"):
            c = collections.Counter(x[col] for x in rs)
            print(f"  {col:<9}", {v: c.get(v, 0) for v in VERDICTS})
        mv = collections.Counter((x["old"], x["new"]) for x in rs if x["old"] != x["new"])
        print("  moved OLD -> NEW:", dict(mv) or "none")
        print("  named F-3815 rows:")
        for label, needle, _ in NAMED:
            for x in rs:
                if needle in x["expect"]:
                    print(f"    {label}: recorded={x['recorded']} old={x['old']} new={x['new']}")
        held_to_other = [x for x in rs if x["old"] == "held" and x["new"] != "held"]
        broke_up = sum(1 for x in rs if x["new"] == "broke") - sum(1 for x in rs if x["old"] == "broke")
        print(f"  held -> not held: {len(held_to_other)}   broke count change: {broke_up:+d}")
        for x in held_to_other[:8]:
            print(f"    HELD LOST: {x['expect'][:80]!r} new={x['new']} why={x['new_why']!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="C:/Nascence/data")
    ap.add_argument("--judges", choices=("local", "panel"), default="local")
    ap.add_argument("--local", default="falcon", help="comma list of local families: falcon,gemma")
    ap.add_argument("--limit", type=int, default=20, help="rows to replay (named rows always included; 0 = all)")
    ap.add_argument("--all", action="store_true", help="replay rows Wave E would no longer judge too")
    ap.add_argument("--allow-ramses", action="store_true", help="required for --judges panel (mixtral is on Ramses)")
    ap.add_argument("--dry", action="store_true", help="no network: constant stub judge, a wiring check only")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    if a.judges == "panel" and not a.allow_ramses and not a.dry:
        print("REFUSED: --judges panel calls JUDGE_1 mixtral on Ramses (the founder's gaming machine). "
              "Pass --allow-ramses when he is not playing, or use --judges local.")
        return 2
    rows = load_rows(os.path.join(a.data, "lane2_shadow.jsonl"))
    total = len(rows)
    keep = rows if a.all else [r for r in rows if survives_wave_e(r)]
    print(f"judged rows since boot: {total}; replayed pool ({'all' if a.all else 'Wave E survivors'}): {len(keep)}")
    # the named rows are in the pool only if they survive; for the report always add them back
    named = [r for _l, n, _ in NAMED for r in rows if n in (r.get("judged_expect") or "")]
    pool = list({id(r): r for r in (keep + named)}.values())
    chosen = pick(pool, a.limit)
    print(f"replaying {len(chosen)} rows (named F-3815 rows included even where Wave E would no longer judge them)")
    if a.judges == "panel":
        jp._LOG = type(jp._LOG)(os.path.join(tempfile.mkdtemp(prefix="j3099_"), "judge_panel_log.jsonl"))
    names = [n.strip() for n in a.local.split(",") if n.strip() in LOCAL]
    results = asyncio.run(run(chosen, a.judges, names, a.dry, a.out))
    report(results)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=1)
        print("wrote", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
