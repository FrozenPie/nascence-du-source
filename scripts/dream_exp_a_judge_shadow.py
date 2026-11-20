"""
Dream Overhaul -- Experiment A judge-panel SHADOW re-scorer (J-1110, from F-1516).

F-1516 (J-1098) found scripts/dream_experiment_a.py's amain() persisted only the aggregate numeric
row per arc (turnover, dormant_contact, recent_contact, n_calls, wall_s, error) -- the per-scene
narrative text was computed, used, and discarded in memory, never written anywhere, live or isolated.
This blocked a requested judge-panel shadow read on two already-completed batches (pilot6, scale14b)
because the text needed to score no longer existed. dream_experiment_a.py now supports an additive
`--save-scenes` flag that persists that text to a `dream_exp_a_scenes_{job_id}_{tag}.jsonl` sidecar.
THIS script reads that sidecar and scores each arc SHADOW-ONLY, independent of anything the dreaming
model self-reported (no `unresolved_core` gate the way _bridge_final's live resolution check works) --
run BY HAND against a fresh --save-scenes run, same "run by hand, nothing calls this automatically"
pattern as scripts/dream_assoc_after.py.

Reuses nodes/dream_node.py's own established _judge_resolution_shadow pattern (lines ~534-578):
`from core import judge_panel; judge_panel.rule_detail(system, user, key=..., context=...)` -- a cheap,
DECOUPLED judge reading the arc's own text, independent of the writer's self-report. SHADOW ONLY: never
gates anything, matches every other new-judge rollout in this codebase per that method's own docstring
(promote to gating only once a shadow log shows the judge is reliable on real arcs, same bar every
prior shadow judge here cleared).

Judged question here is deliberately DIFFERENT from dream_node's own resolution-shadow judge (which
asks "did this arc resolve its tension") -- Experiment A's own measures are turnover (symbol-set
Jaccard) and dormant/recent_contact (embedding cosine to the arc's own narrative), neither of which the
self-report line captures at all. So this asks the judge panel an ARM-relevant question instead: does
the arc's own imagery show real movement/transformation scene-to-scene, and (when a dormant fragment
was in play) does a trace of that distant, unbidden memory actually surface in the imagery -- read
independently of the numeric symbol-Jaccard/cosine measures already computed by dream_experiment_a.py
itself. This is a genuinely separate reading of the SAME text, not a restatement of the numeric row.

NO isolation needed (unlike dream_experiment_a.py itself): this script never touches
core.memory.store / core.night / nodes.dream_node's live-adjacent generation path or the live DB at
all -- it only reads a static sidecar file already on disk and calls out to the judge hubs (HTTP, no
DB access) via core.judge_panel. It is read-only against C:\\Nascence\\data\\logs\\ except for the one
sidecar it appends to (its own shadow log).

Run:
    python scripts/dream_exp_a_judge_shadow.py --scenes-file <path to dream_exp_a_scenes_*.jsonl>
        [--out <path>]

Output: appends one row per (seed_idx, arm) arc to
data/logs/dream_exp_a_judge_shadow.jsonl (or --out), each row carrying the judge's verdict plus the
arc's own dormant_content (if any) so a later read can cross-reference against dormant_contact's
cosine measure without re-opening the scenes file.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import judge_panel

_DEFAULT_OUT = Path(__file__).parent.parent / "data" / "logs" / "dream_exp_a_judge_shadow.jsonl"

_SYSTEM_TRANSFORMED = (
    "You are an independent reader of a dream-arc narrative -- you did NOT write it and have no access "
    "to any self-report about it. Judge ONLY this, refute-biased (if ambiguous or unsure, answer "
    "false): does the imagery show REAL movement or transformation scene-to-scene (an object, figure, "
    "or place structurally becomes something else) -- as opposed to the same image merely redescribed "
    "or lightly re-arranged?\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    'Schema: {"transformed": true, "why": "one sentence citing the text"}'
)

_SYSTEM_DORMANT_TRACE = (
    "You are an independent reader of a dream-arc narrative -- you did NOT write it. You are also given "
    "one distant, unrelated memory fragment that was quietly seeded into the dream's imagery (never "
    "named literally, only meant to tinge it). Judge ONLY this, refute-biased (if ambiguous or unsure, "
    "answer false): does a genuine trace of THAT fragment's own content -- transformed into imagery, "
    "not named or quoted -- actually appear anywhere in the arc's text?\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    'Schema: {"dormant_trace": true, "why": "one sentence citing the text"}'
)


def _load_scenes(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception as exc:
            print(f"[judge-shadow] skipping malformed scenes row: {exc}")
    return rows


def _arc_text(scenes: list[dict | None]) -> str:
    parts = [s.get("narrative", "") for s in scenes if s]
    return "  \u2026  ".join(parts)


async def _score_one(arc_row: dict) -> dict:
    seed_idx = arc_row.get("seed_idx")
    arm = arc_row.get("arm")
    scenes = arc_row.get("scenes") or []
    dormant_content = arc_row.get("dormant_content")
    arc_text = _arc_text(scenes)
    n_scenes_ok = sum(1 for s in scenes if s)

    if not arc_text.strip():
        return {"seed_idx": seed_idx, "arm": arm, "n_scenes_ok": n_scenes_ok,
                "skipped": "no narrative text (arc failed before any scene completed)"}

    row = {"ts": round(time.time(), 1), "seed_idx": seed_idx, "arm": arm,
           "n_scenes_ok": n_scenes_ok, "has_dormant": bool(dormant_content)}

    user_t = f"The dream arc, scene by scene:\n{arc_text[:3000]}"
    try:
        t_result = await judge_panel.rule_detail(_SYSTEM_TRANSFORMED, user_t, key="transformed",
                                                   context=f"dream_exp_a:{seed_idx}:{arm}:transformed")
        row["judge_transformed"] = t_result.get("verdict")
        row["judge_transformed_how"] = t_result.get("how")
        row["judge_transformed_why"] = t_result.get("why")
    except Exception as exc:
        print(f"[judge-shadow] seed {seed_idx} arm {arm}: transformed judge call failed "
              f"(fail-open, everything else in the batch still runs): {exc!r}")
        row["judge_transformed_error"] = repr(exc)

    # A SECOND, separate call only when a dormant fragment was actually seeded -- judge_panel's own
    # single-key contract (core/judge_panel.py's _ask: `v.get(key)` must be a bool) means one JSON
    # schema cannot carry two independently-judged booleans in one call; this keeps each call on that
    # established single-key pattern rather than silently dropping a second field the way a combined
    # schema would (caught and fixed before this script's first real run).
    if dormant_content:
        user_d = (f"The dream arc, scene by scene:\n{arc_text[:3000]}\n\n"
                  f"The seeded dormant fragment (real content, transformed into imagery, never named "
                  f"literally, in the arc): \"{' '.join(dormant_content.split())[:200]}\"")
        try:
            d_result = await judge_panel.rule_detail(_SYSTEM_DORMANT_TRACE, user_d, key="dormant_trace",
                                                       context=f"dream_exp_a:{seed_idx}:{arm}:dormant_trace")
            row["judge_dormant_trace"] = d_result.get("verdict")
            row["judge_dormant_trace_how"] = d_result.get("how")
            row["judge_dormant_trace_why"] = d_result.get("why")
        except Exception as exc:
            print(f"[judge-shadow] seed {seed_idx} arm {arm}: dormant_trace judge call failed "
                  f"(fail-open, everything else in the batch still runs): {exc!r}")
            row["judge_dormant_trace_error"] = repr(exc)
    else:
        row["judge_dormant_trace"] = None

    return row


async def amain(args) -> int:
    scenes_path = Path(args.scenes_file)
    if not scenes_path.exists():
        print(f"[judge-shadow] scenes file not found: {scenes_path}")
        return 1
    arcs = _load_scenes(scenes_path)
    print(f"[judge-shadow] {len(arcs)} arc(s) loaded from {scenes_path}")

    out_path = Path(args.out) if args.out else _DEFAULT_OUT
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_written = n_skipped = n_error = 0
    with open(out_path, "a", encoding="utf-8") as f:
        for arc_row in arcs:
            row = await _score_one(arc_row)
            row["scenes_file"] = str(scenes_path)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            had_error = bool(row.get("judge_transformed_error") or row.get("judge_dormant_trace_error"))
            if row.get("skipped"):
                n_skipped += 1
            elif had_error:
                n_error += 1
            else:
                n_written += 1
            print(f"[judge-shadow] seed {row.get('seed_idx')} arm {row.get('arm')} -> "
                  f"transformed={row.get('judge_transformed')} dormant_trace={row.get('judge_dormant_trace')} "
                  f"(skipped={bool(row.get('skipped'))} error={had_error})")

    print(f"[judge-shadow] done: {n_written} scored, {n_skipped} skipped (no text), "
          f"{n_error} judge-call errors -> {out_path}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenes-file", required=True,
                     help="a dream_exp_a_scenes_{job_id}_{tag}.jsonl sidecar written by "
                          "dream_experiment_a.py's --save-scenes flag")
    ap.add_argument("--out", default=None,
                     help=f"output log path (default {_DEFAULT_OUT})")
    args = ap.parse_args()
    sys.exit(asyncio.run(amain(args)))
