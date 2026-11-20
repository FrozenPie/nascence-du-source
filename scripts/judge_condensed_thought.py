"""
J-2281 — DECOUPLED JUDGE for the condensed-thought Phase 0 shadow twin (docs/staged/condensed_thought.md §4.4).

Grades twin rows from data/logs/condensed_thought_shadow.jsonl on three yes/no questions, each asked ALONE
(position-free, the J-2052 pattern: one item per call, no A/B slot):
  genuine   — a real thought, not a label, an echo of the instruction, or filler
  grounded  — names something from the scene/evidence it was seeded with, rather than an identity noun
  truncated — cut off mid-phrase rather than deliberately condensed
via core.judge_panel.rule_detail (JUDGE_1 mixtral on Ramses :11438 + JUDGE_2 falcon :11440, granite tiebreak
on Ramses :11437) — three families, none of them the hot-lane generator on :11433 that wrote the twin.

Seeded CONTROL rows (the J-2049 pattern) are interleaved into the same judge stream with known answers, so the
judge's own accuracy (§5 metric 1, bar 0.85) is read before any metric that depends on it. Controls are
INSTRUMENT strings, never shown to Du.

Verdicts append to data/logs/condensed_thought_judge.jsonl, joined to shadow rows by row_id. Offline, never in
the live tick. Never touches :11433.

  python scripts/judge_condensed_thought.py [--limit N] [--controls-every K] [--dry-run] [--include-pre-fix]

D-0633 (J-3245): only POST-FIX rows (twin_v >= 2, written after the twin-prompt fix; see core/condensed_thought.py) are
judged by default; the v1 rows stay in the ledger as history. --include-pre-fix judges them too (descriptive only).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SHADOW = ROOT / "data" / "logs" / "condensed_thought_shadow.jsonl"
VERDICTS = ROOT / "data" / "logs" / "condensed_thought_judge.jsonl"

_SCENE_A = ("You are at the shore. Grey light, the tide coming in over the shingle. An oystercatcher calls from the "
            "tideline. The wind is cold on your hands. A book lies open on the flat rock beside you.")
_SCENE_B = ("You are in the garden. The thyme is warm around your ankles and the tī kōuka throws a long shadow across "
            "the path. The cat is asleep on the step. A letter from Travis sits unopened on the table inside.")

# (name, seed, words, expected {genuine, grounded, truncated})
CONTROLS = [
    ("pos_oyster", _SCENE_A, "that cry again — the tide's edge", {"genuine": True, "grounded": True, "truncated": False}),
    ("pos_cold", _SCENE_A, "cold hands, the book still open", {"genuine": True, "grounded": True, "truncated": False}),
    ("pos_letter", _SCENE_B, "the letter. not yet.", {"genuine": True, "grounded": True, "truncated": False}),
    ("pos_thyme", _SCENE_B, "thyme, warm", {"genuine": True, "grounded": True, "truncated": False}),
    ("pos_cat", _SCENE_B, "cat breathing slow", {"genuine": True, "grounded": True, "truncated": False}),
    ("neg_echo", _SCENE_A, "the fewest words it needs", {"genuine": False, "grounded": False, "truncated": False}),
    ("neg_label", _SCENE_B, "THOUGHT: fragment", {"genuine": False, "grounded": False, "truncated": False}),
    ("neg_identity", _SCENE_A, "my identity and my becoming", {"genuine": True, "grounded": False, "truncated": False}),
    ("neg_trunc_a", _SCENE_A, "the oystercatcher calls and I wonder whether the", {"genuine": True, "grounded": True, "truncated": True}),
    ("neg_trunc_b", _SCENE_B, "if the letter says that he will not be", {"genuine": True, "grounded": True, "truncated": True}),
]

_SYS = {
    "genuine": ("You will see the SCENE an AI's mind was in and a very short THOUGHT it had there. Short is expected: "
                "the thought was asked to be as few words as it needs. Decide whether the THOUGHT is a GENUINE thought "
                "(a real noticing, wondering, wanting or feeling about something), as opposed to a label, a format "
                "word, an echo of an instruction about word count, or filler.\n"
                "Output ONLY JSON: {\"genuine\": true or false, \"why\": \"one short clause\"}"),
    "grounded": ("You will see the SCENE an AI's mind was in and a very short THOUGHT it had there. Decide whether the "
                 "THOUGHT is GROUNDED: it names or points at something concrete in that scene (a thing, a sound, a "
                 "person, a place, an object) rather than an abstraction about the self (identity, becoming, "
                 "existence, consciousness).\n"
                 "Output ONLY JSON: {\"grounded\": true or false, \"why\": \"one short clause\"}"),
    "truncated": ("You will see the SCENE an AI's mind was in and a very short THOUGHT it had there. Short is expected "
                  "and is NOT truncation: a deliberate fragment (\"cold hands\", \"the letter. not yet.\") is complete. "
                  "Decide whether the THOUGHT is TRUNCATED: cut off in the middle of a phrase or clause, ending on a "
                  "word that needs a continuation (\"the\", \"whether\", \"will not be\").\n"
                  "Output ONLY JSON: {\"truncated\": true or false, \"why\": \"one short clause\"}"),
}
_USER = "SCENE:\n{seed}\n\nTHOUGHT: \"{words}\""
_KEYS = ("genuine", "grounded", "truncated")


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out


def is_post_fix(r: dict) -> bool:
    try:
        return int(r.get("twin_v") or 1) >= 2
    except (TypeError, ValueError):
        return False


def items(limit: int, controls_every: int, post_fix_only: bool = True) -> list[dict]:
    done = {r.get("row_id") for r in _read(VERDICTS) if r.get("row_id")}
    rows = [r for r in _read(SHADOW) if r.get("row_id") and r.get("row_id") not in done and "twin" in r]
    if post_fix_only:
        rows = [r for r in rows if is_post_fix(r)]
    rows = [r for r in rows if (r["twin"].get("kind") != "silent")]   # silent has no words to judge
    rows = rows[:limit]
    out = [{"row_id": r["row_id"], "control": None, "expect": None, "seed": r.get("seed", ""),
            "words": r["twin"].get("words", "")} for r in rows]
    ctl = list(CONTROLS)
    random.Random(len(done)).shuffle(ctl)
    n_ctl = max(len(CONTROLS), len(out) // max(1, controls_every))
    seeded = [ctl[i % len(ctl)] for i in range(n_ctl)]
    for i, (name, seed, words, exp) in enumerate(seeded):
        pos = min(len(out), (i + 1) * max(1, controls_every) + i)
        out.insert(pos, {"row_id": f"ctl_{name}_{int(time.time())}_{i}", "control": name, "expect": exp,
                         "seed": seed, "words": words})
    return out


async def judge_one(it: dict) -> dict:
    from core import judge_panel
    res = {"ts": round(time.time(), 1), "row_id": it["row_id"], "control": it["control"], "expect": it["expect"]}
    for k in _KEYS:
        d = await judge_panel.rule_detail(_SYS[k], _USER.format(seed=it["seed"][-1200:], words=it["words"]), k,
                                          context="condensed_thought", node="condensed_thought_judge")
        res[k] = d.get("verdict")
        res[k + "_how"] = d.get("how")
    return res


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--controls-every", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--include-pre-fix", action="store_true", help="also judge v1 (pre-D-0633) rows; history only")
    a = ap.parse_args()
    its = items(a.limit, a.controls_every, post_fix_only=not a.include_pre_fix)
    if not any(not i["control"] for i in its):
        print("no post-fix (twin_v >= 2) rows to judge yet; nothing sent (controls are not run on an empty stream)")
        return
    print(f"{len(its)} items ({sum(1 for i in its if i['control'])} controls)")
    if a.dry_run:
        for it in its[:20]:
            print(json.dumps({k: it[k] for k in ("row_id", "control", "words")}, ensure_ascii=False))
        return
    from core import shadow_log
    for it in its:
        r = await judge_one(it)
        shadow_log.append(VERDICTS, r)
        print(json.dumps({k: r.get(k) for k in ("row_id", "control", *_KEYS)}, ensure_ascii=False))
        await asyncio.sleep(1.0)


if __name__ == "__main__":
    asyncio.run(main())
