"""
_replay_steer_edge_j1955.py -- J-1955 / D-0368 A verification: replay a window of REAL idle-prompt assemblies and
count, per affective steer, how often it fired BEFORE (every prompt in which the old code delivered it) vs AFTER
(the edge gate core/steer_edge.fires() applied, on the prompt's own timestamps).

Input: data/prompt_budget_shadow.jsonl (READ ONLY; each 'assembly' row carries the first 48 chars of every seed
part in `labels`). Nothing is written anywhere: steer_edge.LOG_ENABLED is forced False and the module state is
in-process. Run from a worktree:  python scripts/_replay_steer_edge_j1955.py [--hours 24] [--log <path>]

Fidelity note (conservative): a prompt in which the old code did NOT deliver a steer (hold-suppressed, escape
stacking) is treated as 'steer inactive', which RE-ARMS the gate, so the AFTER count is an upper bound.
The cat warmth line is not replayed (its text lives in a content corpus, not in the labels); it is unit-tested.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402,F401  (import core BEFORE anything lab-ish)
from core import steer_edge as SE  # noqa: E402

SE.LOG_ENABLED = False

LIVE_LOG = Path(r"C:\Nascence\data\prompt_budget_shadow.jsonl")

# label-prefix classifiers -> (steer key, state)
_RULES = [
    (re.compile(r"^\s*A restlessness is creeping"), "boredom_felt", "mild"),
    (re.compile(r"^\s*You are growing tired of this"), "boredom_felt", "tired"),
    (re.compile(r"^\s*You are sick of this"), "boredom_felt", "sick"),
    (re.compile(r"^\s*Something in you is hard right now"), "b6_hard", True),
    (re.compile(r"^\s*(You have circled this same thought|That is \d+ times round|You keep returning to this same"
                r"|\d+ passes over the same ground)"), "habituation", True),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--log", default=str(LIVE_LOG))
    ap.add_argument("--end-ts", type=float, default=None, help="window end (default: last row)")
    a = ap.parse_args()

    rows = []
    with open(a.log, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("kind") == "assembly" and r.get("source") == "inner_monologue.idle_thought":
                rows.append(r)
    rows.sort(key=lambda r: r["ts"])
    end = a.end_ts or rows[-1]["ts"]
    win = [r for r in rows if end - a.hours * 3600 <= r["ts"] <= end]
    print(f"window: {len(win)} idle prompts, {a.hours:.0f} h ending {time.strftime('%Y-%m-%d %H:%M', time.localtime(end))}")

    SE.reset()
    before, after = Counter(), Counter()
    keys = sorted({k for _, k, _ in _RULES})
    for r in win:
        active = {}
        for lab in r.get("labels", []):
            for rx, key, state in _RULES:
                if rx.match(lab):
                    active[key] = state
        for key in keys:
            st = active.get(key)
            if st:
                before[key] += 1
            kw = {"boredom_felt": dict(rank={"mild": 1, "tired": 2, "sick": 3}.get(st, 1), rearm_s=900.0),
                  "b6_hard": dict(rearm_s=600.0)}.get(key, {})      # mirrors the call sites in inner_monologue_node.py
            if SE.fires(key, st, now=r["ts"], **kw):
                after[key] += 1
    n = max(len(win), 1)
    print(f"{'steer':<14}{'before':>8}{'after':>8}{'before%':>9}{'after%':>9}")
    for k in keys:
        print(f"{k:<14}{before[k]:>8}{after[k]:>8}{100 * before[k] / n:>8.1f}%{100 * after[k] / n:>8.1f}%")
    print(f"TOTAL steer deliveries: before={sum(before.values())} after={sum(after.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
