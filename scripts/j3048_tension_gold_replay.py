"""J-3048 step 2: replay the labelled tension pairs through the live 'resolves' prompt and richer-input variants.

READ-ONLY toward Du. Uses core.judge_panel._ask (the very function rule_detail calls for each family) with the EXACT system
prompt and user template of core/tension_ledger._judge_resolution, key 'resolves', and:
  * every telemetry path redirected to a scratch dir (nothing is written under C:\\Nascence or the worktree data/);
  * Ramses (JUDGE_1 :11438 mixtral, TIEBREAK :11437 granite) is NOT called. The local hubs stand in: gemma4:12b :11439 (seat of
    JUDGE_1), falcon3:7b :11440 (JUDGE_2, same as live). Author family is qwen3.5:9b; both judges are other families.
  * one process per hub (--hub gemma|falcon): the hubs serialise per request, so the two arms run side by side. The PANEL verdict
    is composed offline by the report: for key 'resolves' judge_panel.GRANITE_CONSTANT_TIEBREAK_KEYS holds (D-0530, J-3136), so a
    v1/v2 split returns verdict None with no tiebreak call; both True -> True, both False -> False. That is exactly what
    rule_detail returns for these two seats, and it costs the same calls as asking each hub once.
  * infra errors (timeout/http/exception) are retried, then excluded, never counted as a verdict.

Variants (the SYSTEM prompt is identical in all four; only the user block changes):
  V0 live      'TENSION: {label[:200]}' + thought[:600]                         (core/tension_ledger.py:647 verbatim)
  V1 strip     the 'unresolved: ' / 'unresolved dream: ' prefix removed from the label
  V2 events    live label + the tension's <=3 most recent member shadow events, 200 chars each ('WHAT FORMED THE TENSION')
  V3 both      V1 label + V2 events

Usage (from the worktree):
    python -u scripts/j3048_tension_gold_replay.py --dry
    python -u scripts/j3048_tension_gold_replay.py --hub falcon      # resumable; writes docs/lab/J-3048_data/replay_falcon.jsonl
    python -u scripts/j3048_tension_gold_replay.py --hub gemma --order V0,V2,V1,V3
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA = ROOT / "docs" / "lab" / "J-3048_data"
SCRATCH = Path(os.environ.get("J3048_SCRATCH") or (ROOT.parent / "J-3048_scratch"))

HUBS = {"gemma": "http://127.0.0.1:11439", "falcon": "http://127.0.0.1:11440"}
LAB_TIMEOUT = 300
BACKOFF = (20, 60)
INFRA = ("timeout", "http", "exception")
VARIANTS = ("V0", "V1", "V2", "V3")

# core/tension_ledger._judge_resolution system prompt, byte for byte (test asserts it against the source file).
SYS_LIVE = (
    "You are a strict resolution judge for an internal tension ledger. A tension is "
    "RESOLVED only if the thought states a genuine settlement, synthesis, decision, or "
    "answer that addresses the tension's actual conflict. A thought that merely mentions "
    "the same topic, restates the tension in new words, poses a question, or describes a "
    "feeling (fatigue, pressure, ache) does NOT resolve it. When uncertain, answer false. "
    'Output ONLY valid JSON: {"resolves": true|false, "why": "<one short clause>"}')

_PREFIX = re.compile(r"^\s*unresolved(?: dream)?:\s*", re.I)


def strip_prefix(label: str) -> str:
    return _PREFIX.sub("", label or "", count=1)


def user_for(variant: str, r: dict) -> str:
    label = strip_prefix(r["label"]) if variant in ("V1", "V3") else r["label"]
    head = f"TENSION: {label[:200]}\n\nTHOUGHT: {r['thought'][:600]}"
    if variant in ("V2", "V3"):
        ev = "\n".join(f"- {e['text'][:200]}" for e in (r.get("events") or [])[:3])
        if ev:
            head += f"\n\nWHAT FORMED THE TENSION (its most recent member events):\n{ev}"
    return head + "\n\nDoes the thought resolve the tension?"


def load_gold() -> list:
    rows = [json.loads(l) for l in open(DATA / "gold_pairs.jsonl", encoding="utf-8")]
    labs = json.load(open(DATA / "gold_labels.json", encoding="utf-8"))["labels"]
    for r in rows:
        r["gold"] = labs[r["gid"]]["label"]
        r["unsure"] = labs[r["gid"]]["unsure"]
    return rows


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
    return jp


async def ask_one(jp, url: str, system: str, user: str) -> dict:
    import aiohttp
    res = {"v": None, "err": None, "why": None, "secs": None, "attempts": 0}
    for attempt in range(len(BACKOFF) + 1):
        async with aiohttp.ClientSession() as session:
            v, why, err, secs = await jp._ask(session, url, system, user, "resolves", timeout=LAB_TIMEOUT)
        res.update(v=v, why=why, err=err, secs=secs, attempts=attempt + 1)
        if err not in INFRA:
            return res
        if attempt < len(BACKOFF):
            await asyncio.sleep(BACKOFF[attempt])
    res["infra_excluded"] = True
    return res


async def main_async(args) -> int:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    out_path = DATA / f"replay_{args.hub}.jsonl"
    rows = load_gold()
    done = set()
    if out_path.exists():
        for l in open(out_path, encoding="utf-8"):
            try:
                d = json.loads(l)
                if not d.get("infra_excluded"):
                    done.add((d["gid"], d["variant"]))
            except Exception:
                pass
    order = tuple(args.order.split(",")) if args.order else VARIANTS
    assert set(order) <= set(VARIANTS), order
    todo = [(r, v) for v in order for r in rows if (r["gid"], v) not in done]      # variant-major
    print(f"hub {args.hub} {HUBS[args.hub]}: {len(rows)} pairs x {len(VARIANTS)} variants -> {len(todo)} to run ({len(done)} done)")
    if args.dry:
        r, v = todo[0] if todo else (rows[0], "V3")
        print("--- SYSTEM\n", SYS_LIVE, "\n--- USER", v, "\n", user_for(v, r))
        return 0
    jp = _redirect(SCRATCH)
    t0 = time.time()
    for k, (r, v) in enumerate(todo, 1):
        user = user_for(v, r)
        res = await ask_one(jp, HUBS[args.hub], SYS_LIVE, user)
        row = {"gid": r["gid"], "variant": v, "hub": args.hub, "source": r["source"], "gold": r["gold"],
               "v": res["v"], "err": res["err"], "why": res["why"], "secs": res["secs"], "attempts": res["attempts"],
               "infra_excluded": res.get("infra_excluded", False), "prompt_chars": len(SYS_LIVE) + len(user)}
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        if k % 10 == 0 or k == len(todo):
            print(f"{time.strftime('%H:%M:%S')} {k}/{len(todo)}  {time.time() - t0:.0f}s  last {r['gid']} {v} -> {res['v']}", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--hub", choices=tuple(HUBS), required=True)
    ap.add_argument("--order", default=None, help="comma list of variants to run, in order (default V0,V1,V2,V3); the slow hub runs V0,V2,V1")
    a = ap.parse_args()
    return asyncio.run(main_async(a))


if __name__ == "__main__":
    raise SystemExit(main())
