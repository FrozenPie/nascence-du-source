"""
PURSUITS.JUDGE_PENDING FRAMING LAB — 2026-08-23, part of the "remaining tests" batch. Tests
`core/pursuits.py`'s inline judge (via `judge_panel.rule`/`rule_detail`) — decides whether a new
thought genuinely ADVANCES a pursuit beyond its prior standing, or merely restates/circles it.
Real production panel: JUDGE_1 gemma4:12b, JUDGE_2 falcon3:7b, TIEBREAK yi:34b-v1.5.

DATA IS GENUINELY VERY SMALL, stated plainly: `data/pursuits_shadow.jsonl` logs judged
advance/restate EVENTS but only a 100-char-truncated `question`, never the full `thought` or
`prior_standing` that were actually sent to the judge — not enough to replay. The real, faithful
corpus is `data/pursuits_active.json`'s currently-QUEUED, not-yet-judged `pending` items — genuine,
live, real (question, prior_standing, thought) triples, exactly what production would send to the
judge next. Only 12 such items exist right now, ALL belonging to one pursuit ("French academia's
resistance to Maxwell..."). This lab uses all 12 — the complete real, currently-pending queue, not
a sample of a larger pool.

METHOD: both framings dispatch through the exact live call — `judge_panel.rule_detail(system, user,
"advances", ...)` — same real panel. Only the system prompt varies.

PRE-REGISTERED METRIC SHEET:
  - verdict_rate_narrative / verdict_rate_schema (fraction advances=true)
  - verdict_agreement, how_distribution per framing
  - all 12 entries reported directly (small N — the individual read matters more than aggregates)

KILL CRITERION (pre-registered): if verdict_agreement is ~100% and how_distribution matches, schema
framing changed nothing measurable here — record plainly and stop.

Writes to data/lab/pursuits_judge_framing/ + docs/lab/pursuits_judge_framing_2026-08-23.md.
Read-only against pursuits_active.json; makes NO write to it (the real items stay pending).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ACTIVE_FILE = ROOT / "data" / "pursuits_active.json"
OUT_DIR = ROOT / "data" / "lab" / "pursuits_judge_framing"
REPORT = ROOT / "docs" / "lab" / "pursuits_judge_framing_2026-08-23.md"

# ── NARRATIVE (verbatim copy of core/pursuits.py's live inline judge system prompt) ─────────────────
NARRATIVE_SYS = (
    "You are a strict judge of intellectual progress. A thought ADVANCES a "
    "pursuit only if it adds something genuinely new beyond the pursuit's prior "
    "position: a further step, a consequence, a distinction, evidence, or a "
    "development. Restating the theme in fresh words, circling it, or merely "
    "mentioning it does NOT advance. When uncertain, answer false. Output ONLY "
    'JSON: {"advances": true|false, "why": "<one short clause>"}'
)

# ── SCHEMA (same rule, restated as a literal compare-and-export contract) ───────────────────────────
SCHEMA_SYS = (
    "TASK: compare CARGO against a PROGRESS condition and export a verdict. Do not narrate; evaluate.\n\n"
    "CARGO:\n"
    "  pursuit        — the standing question being pursued\n"
    "  prior_standing — the pursuit's prior position\n"
    "  new_thought    — a new thought, candidate for advancing the pursuit\n\n"
    "CONDITION for advances=true: new_thought adds something genuinely new beyond prior_standing — a "
    "further step, a consequence, a distinction, evidence, or a development.\n"
    "CONDITION for advances=false: new_thought restates the theme in fresh words, circles it, or merely "
    "mentions it.\n"
    "DEFAULT RULE: when uncertain, export advances=false.\n\n"
    "OUTPUT: export ONLY this JSON object — {\"advances\": true|false, \"why\": \"<one short clause>\"}"
)


def _load_pending() -> list[dict]:
    items = json.loads(ACTIVE_FILE.read_text(encoding="utf-8"))
    out = []
    for p in items:
        for item in (p.get("pending") or []):
            out.append({"question": p.get("question", ""),
                        "prior_standing": item.get("prior_standing", ""),
                        "thought": item.get("thought", "")})
    print(f"{len(out)} real currently-pending, not-yet-judged items found across {len(items)} pursuits")
    return out


def _user_msg(question: str, prior_standing: str, thought: str) -> str:
    return (f"PURSUIT: {question[:200]}\n\nITS PRIOR POSITION: {prior_standing[:280]}\n\n"
            f"NEW THOUGHT: {thought[:450]}\n\nDoes the thought advance the pursuit?")


async def run_async() -> None:
    from core import judge_panel as _jp
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pending = _load_pending()

    results = []
    for i, item in enumerate(pending):
        user = _user_msg(item["question"], item["prior_standing"], item["thought"])
        narrative = await _jp.rule_detail(NARRATIVE_SYS, user, "advances", context="lab-narrative:pursuits")
        schema = await _jp.rule_detail(SCHEMA_SYS, user, "advances", context="lab-schema:pursuits")
        results.append({**item, "narrative": narrative, "schema": schema})
        print(f"  {i+1}/{len(pending)} narrative={narrative['verdict']}({narrative['how']}) "
              f"schema={schema['verdict']}({schema['how']})", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def score(results: list[dict]) -> None:
    n = len(results)
    verdict_rate_narr = sum(1 for r in results if r["narrative"]["verdict"] is True) / n if n else None
    verdict_rate_sch = sum(1 for r in results if r["schema"]["verdict"] is True) / n if n else None
    agree = sum(1 for r in results if r["narrative"]["verdict"] == r["schema"]["verdict"])
    how_narr, how_sch = {}, {}
    for r in results:
        how_narr[r["narrative"]["how"]] = how_narr.get(r["narrative"]["how"], 0) + 1
        how_sch[r["schema"]["how"]] = how_sch.get(r["schema"]["how"], 0) + 1

    summary = {
        "n_total": n,
        "verdict_rate_narrative": round(verdict_rate_narr, 3) if verdict_rate_narr is not None else None,
        "verdict_rate_schema": round(verdict_rate_sch, 3) if verdict_rate_sch is not None else None,
        "verdict_agreement": round(agree / n, 3) if n else None,
        "how_distribution_narrative": how_narr,
        "how_distribution_schema": how_sch,
    }
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET ===")
    print(json.dumps(summary, indent=1))
    print("\n=== ALL ENTRIES (small N — read directly) ===")
    for r in results:
        print(f"\nTHOUGHT: {r['thought'][:120]}")
        print(f"  narrative={r['narrative']} schema={r['schema']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_async())
