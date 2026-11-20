"""J-2996 step 2: replay the labelled gold pairs through the live 'advances' prompt and candidate variants.

READ-ONLY toward Du. Uses core.judge_panel.rule_detail (the same function core/pursuits.judge_pending calls), with:
  * _LOG and every telemetry path redirected to a scratch dir (nothing is written under C:\\Nascence or the worktree data/);
  * the three panel hubs re-pointed to LOCAL hubs because Ramses (JUDGE_1 :11438 mixtral, TIEBREAK :11437 granite) must not
    be called: JUDGE_1 -> gemma4:12b :11439, JUDGE_2 -> falcon3:7b :11440 (UNCHANGED from live), TIEBREAK -> yi:34b :11442.
    Author family stays qwen3.5:9b; judges are Google / TII / 01.AI, all different. This is NOT the live panel composition
    (the live JUDGE_1 and tiebreak are Mistral and IBM), so absolute pass rates are read against V0 here, never against 82%.
  * --mode single (default) asks ONE judge, gemma4:12b at :11439, through the panel's own _ask(); --mode panel runs the full
    rule_detail. On 2026-11-06 sibling chains held falcon3 and yi at ~220 s per call, so a panel ruling took ~7 min and the
    324-ruling matrix was ~30 h; the panel arm is therefore a lab job (see the report), the single-judge arm is the result.
  * infra errors (timeout/http/exception) retried then excluded, never counted as a verdict.

Variants (system prompt / user block):
  V0 live      exact core/pursuits.py judge_pending prompt, previous confirmed thought only
  V1 no_image  V0 + one sentence: a new image/example/object/sensory detail on the same theme is NOT an advance
  V2 last3     V0 system + 'compare against ALL recent positions'; user block lists the pursuit's last <=3 confirmed thoughts
  V3 both      V1 + V2

Usage (from the worktree):
    python -u scripts/j2996_pursuit_gold_replay.py --dry
    python -u scripts/j2996_pursuit_gold_replay.py                 # all labelled pairs x all variants (resumable)
    python -u scripts/j2996_pursuit_gold_replay.py --extra 150     # + N unlabelled confirmed pairs for the keep-rate estimate
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA = ROOT / "docs" / "lab" / "J-2996_data"
SCRATCH = Path(os.environ.get("J2996_SCRATCH") or (ROOT.parent / "J-2996_scratch"))

LOCAL_J1 = "http://127.0.0.1:11439"     # gemma4:12b
LOCAL_J2 = "http://127.0.0.1:11440"     # falcon3:7b (same as live JUDGE_2)
LOCAL_TB = "http://127.0.0.1:11442"     # yi:34b-v1.5
LAB_TIMEOUT = 240
BACKOFF = (15, 45)
INFRA = ("timeout", "http", "exception")

SYS_LIVE = ("You are a strict judge of intellectual progress. A thought ADVANCES a "
            "pursuit only if it adds something genuinely new beyond the pursuit's prior "
            "position: a further step, a consequence, a distinction, evidence, or a "
            "development. Restating the theme in fresh words, circling it, or merely "
            "mentioning it does NOT advance. When uncertain, answer false. Output ONLY "
            'JSON: {"advances": true|false, "why": "<one short clause>"}')
_IMG = (" A new image, example, object or sensory detail on the same theme is NOT an advance either; "
        "only a new claim, step, consequence or distinction is.")
_L3 = (" You are given the pursuit's recent positions, oldest first; a thought that restates or "
       "re-images ANY of them does not advance.")
_TAIL = ' When uncertain, answer false. Output ONLY JSON: {"advances": true|false, "why": "<one short clause>"}'
_HEAD = SYS_LIVE[: SYS_LIVE.index(" When uncertain")]            # everything up to and including "does NOT advance."


def sys_for(variant: str) -> str:
    extra = ""
    if variant in ("V1", "V3"):
        extra += _IMG
    if variant in ("V2", "V3"):
        extra += _L3
    return SYS_LIVE if variant == "V0" else _HEAD + extra + _TAIL


def user_for(variant: str, r: dict) -> str:
    q, new = r["question"][:200], r["new"][:450]
    if variant in ("V0", "V1"):
        return (f"PURSUIT: {q}\n\nITS PRIOR POSITION: {r['prior'][:280]}\n\n"
                f"NEW THOUGHT: {new}\n\nDoes the thought advance the pursuit?")
    pos = list(r.get("recent3") or [])
    pos = (pos[:-1] if pos else []) + [r["prior"]]          # the last one is the judge's real prior input
    pos = pos[-3:]
    block = "\n".join(f"- {p[:280]}" for p in pos)
    return (f"PURSUIT: {q}\n\nITS RECENT POSITIONS (oldest first):\n{block}\n\n"
            f"NEW THOUGHT: {new}\n\nDoes the thought advance the pursuit?")


VARIANTS = ("V0", "V1", "V2", "V3")


def load_gold() -> list:
    rows = [json.loads(l) for l in open(DATA / "gold_pairs.jsonl", encoding="utf-8")]
    labs = json.load(open(DATA / "gold_labels.json", encoding="utf-8"))["labels"]
    for r in rows:
        r["gold"] = labs[r["gid"]]["label"]
        r["unsure"] = labs[r["gid"]]["unsure"]
    return rows


def load_extra(n: int, exclude_pursuit_idx: set, seed: int = 29961) -> list:
    """N further confirmed pairs (not in the labelled set), unlabelled: only the variants' keep-rate is read from them."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import j2996_pursuit_gold_build as b
    items = b.load_pursuits()
    pool = [r for r in b.confirmed_pairs(items) if (r["pursuit"], r["idx"]) not in exclude_pursuit_idx]
    random.Random(seed).shuffle(pool)
    out = pool[:n]
    for k, r in enumerate(out, 1):
        r["gid"] = f"X{k:03d}"
        r["gold"] = None
        r["unsure"] = False
    return out


def _redirect(scratch: Path):
    from core import judge_panel as jp
    from core import telemetry as tel
    scratch.mkdir(parents=True, exist_ok=True)
    jp._LOG = scratch / "judge_panel_log.scratch.jsonl"
    jp._DATA = scratch
    tel._DATA = scratch
    for name in ("_CALLS", "_HW", "_LLM", "_LAT", "_STATIONS", "_JSONFAIL", "_BREAKER"):
        if hasattr(tel, name):
            setattr(tel, name, scratch / f"tel_{name.strip('_').lower()}.jsonl")
    jp.JUDGE_1, jp.JUDGE_2, jp.TIEBREAK = LOCAL_J1, LOCAL_J2, LOCAL_TB
    orig = jp._ask

    async def _ask_long(session, url, system, user, key, timeout=LAB_TIMEOUT, num_predict=jp._NUM_PREDICT):
        return await orig(session, url, system, user, key, timeout=LAB_TIMEOUT, num_predict=num_predict)

    jp._ask = _ask_long
    return jp


async def rule_one(jp, system: str, user: str, ctx: str) -> dict:
    res = None
    for attempt in range(len(BACKOFF) + 1):
        res = await jp.rule_detail(system, user, "advances", context=ctx)
        errs = [res.get("err1"), res.get("err2"), res.get("err3")]
        if not any(e in INFRA for e in errs):
            res["attempts"] = attempt + 1
            return res
        if attempt < len(BACKOFF):
            await asyncio.sleep(BACKOFF[attempt])
    res["attempts"] = len(BACKOFF) + 1
    res["infra_excluded"] = True
    return res


async def single_one(jp, system: str, user: str) -> dict:
    """ONE local judge (gemma4:12b, JUDGE_1's seat) through the panel's own _ask(): same payload, same parse. Used because the
    two other hubs were saturated by sibling chains (falcon3 ~220 s, yi ~215 s per call) and one panel ruling cost ~7 min."""
    import aiohttp
    res = {"v1": None, "v2": None, "err1": None, "verdict": None, "how": "single", "why1": None}
    for attempt in range(len(BACKOFF) + 1):
        async with aiohttp.ClientSession() as session:
            v, why, err, secs = await jp._ask(session, jp.JUDGE_1, system, user, "advances")
        res.update(v1=v, verdict=v, err1=err, why1=why, s1=secs, attempts=attempt + 1)
        if err not in INFRA:
            return res
        if attempt < len(BACKOFF):
            await asyncio.sleep(BACKOFF[attempt])
    res["infra_excluded"] = True
    return res


async def main_async(args) -> int:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    shard_i, shard_n = args.shard
    prefix = "replay_single" if args.mode == "single" else "replay_results"
    out_path = DATA / (f"{prefix}.jsonl" if shard_n == 1 else f"{prefix}.shard{shard_i}.jsonl")
    gold = load_gold()
    rows = list(gold)
    if args.extra:
        rows += load_extra(args.extra, {(r["pursuit"], r["idx"]) for r in gold if r["source"] == "confirmed"})
    rows = rows[shard_i::shard_n]                       # pair-parity shards: hubs serialise per request, a second
    done = set()                                         # process only claims a fairer share of each hub's queue
    for pth in sorted(DATA.glob(f"{prefix}*.jsonl")):
        for l in open(pth, encoding="utf-8"):
            try:
                d = json.loads(l)
                if not d.get("infra_excluded"):
                    done.add((d["gid"], d["variant"]))
            except Exception:
                pass
    order = ("V0", "V3", "V1", "V2")                    # variant-major: a partial run still has whole variants
    todo = [(r, v) for v in order for r in rows if (r["gid"], v) not in done]
    print(f"pairs {len(rows)} variants {len(VARIANTS)} -> {len(todo)} rulings to run ({len(done)} already done)")
    if args.dry:
        r, v = todo[0] if todo else (rows[0], "V0")
        print("--- sample SYSTEM", v, "\n", sys_for(v), "\n--- sample USER\n", user_for(v, r))
        return 0
    jp = _redirect(SCRATCH)
    t0 = time.time()
    for k, (r, v) in enumerate(todo, 1):
        if args.mode == "single":
            res = await single_one(jp, sys_for(v), user_for(v, r))
        else:
            res = await rule_one(jp, sys_for(v), user_for(v, r), f"j2996:{r['gid']}:{v}")
        row = {"gid": r["gid"], "variant": v, "source": r["source"], "gold": r["gold"], "pursuit": r["pursuit"],
               **{kk: res.get(kk) for kk in ("v1", "v2", "verdict", "how", "err1", "err2", "err3", "why1", "why2", "why3",
                                              "attempts", "infra_excluded", "s1")}}
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        if k % 10 == 0 or k == len(todo):
            print(f"{time.strftime('%H:%M:%S')} {k}/{len(todo)}  {time.time() - t0:.0f}s  last {r['gid']} {v} -> "
                  f"{res.get('verdict')} ({res.get('how')})", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--extra", type=int, default=0)
    ap.add_argument("--mode", choices=("single", "panel"), default="single",
                    help="single = gemma4:12b alone (default, what the saturated hubs allow); panel = full rule_detail (gemma+falcon3+yi)")
    ap.add_argument("--shard", default="0/1", help="i/n: run only pairs i, i+n, ... and write replay_results.shard<i>.jsonl")
    a = ap.parse_args()
    a.shard = tuple(int(x) for x in a.shard.split("/"))
    return asyncio.run(main_async(a))


if __name__ == "__main__":
    raise SystemExit(main())
