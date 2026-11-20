"""
SELF_INTERROGATION GENUINENESS-JUDGE FRAMING LAB — 2026-08-23, tenth machine tested (second of the
"remaining tests" batch). Prior results: openness gate (win), self_implication (null),
commitment_ledger._judge_defeater (null), tension_ledger (loss), librarian (decisive loss),
peers.contrary_target (mixed, N=100), study_note (mixed), journal_rollup (loss),
left_lane.grade_work (in progress). Tests `core/self_interrogation.py`'s `_GRADE_SYSTEM` — the
judge that decides whether a piece of self-reflection is genuine or "performed uncertainty" —
routed through the REAL production judge panel (`judge_panel.rule_detail`, same panel as
tension_ledger: JUDGE_1 gemma4:12b, JUDGE_2 falcon3:7b, TIEBREAK yi:34b-v1.5).

A real historical corpus exists: `data/self_interrogation_shadow.jsonl` logs 32 real
`interrogate` events with the real (thought, reflection, genuine) triple — 17 genuine=true,
2 genuine=false, 13 genuine=None (split, no tiebreak available at the time). All 32 real cases used
(small enough to run in full, no sampling needed).

METHOD: both framings dispatch through the exact live call —
`core.judge_panel.rule_detail(system, user, "genuine", context=...)` — same real panel, same user
message template (`ORIGINAL THOUGHT: "..." / REFLECTION: "..."`). Only the system prompt varies.

PRE-REGISTERED METRIC SHEET:
  - v1_ok / v2_ok rates
  - verdict_rate_narrative / verdict_rate_schema (fraction genuine=true)
  - historical_vs_narrative_fresh_agreement (drift check against the real logged verdict, where one
    exists — i.e. excluding the 13 historical None/split cases)
  - verdict_agreement (narrative-fresh vs schema-fresh)
  - how_distribution per framing (agreed/tiebreak/split_no_tiebreak/unavailable)
  - disagreement_examples

KILL CRITERION (pre-registered): if verdict_agreement is ~100% and how_distribution is materially
the same, schema framing changed nothing measurable here — record plainly and stop.

Writes to data/lab/self_interrogation_framing/ + docs/lab/self_interrogation_framing_2026-08-23.md.
Read-only against the shadow log; writes nothing back to it.
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

SHADOW_LOG = ROOT / "data" / "self_interrogation_shadow.jsonl"
OUT_DIR = ROOT / "data" / "lab" / "self_interrogation_framing"
REPORT = ROOT / "docs" / "lab" / "self_interrogation_framing_2026-08-23.md"

# ── NARRATIVE (verbatim copy of core/self_interrogation.py's live _GRADE_SYSTEM) ────────────────────
NARRATIVE_SYS = (
    "You are grading whether a piece of self-reflection is genuine or hollow. You will see an ORIGINAL "
    "THOUGHT and a REFLECTION written about it. Answer one question: does the reflection name a SPECIFIC "
    "reason to look again at the original thought — an actual motivation, a concrete logical gap, a named "
    "bias, a real piece of evidence or its absence — or does it just perform uncertainty in the abstract "
    "(\"I should question this more\", \"perhaps I am biased\") with no real content behind it? "
    "Be strict: fluent, sincere-SOUNDING humility with nothing specific in it is NOT genuine. "
    "Output ONLY JSON: {\"genuine\": true or false}"
)

# ── SCHEMA (same rule, restated as a literal compare-and-export contract) ───────────────────────────
SCHEMA_SYS = (
    "TASK: compare CARGO against a SPECIFICITY condition and export a verdict. Do not narrate; evaluate.\n\n"
    "CARGO:\n"
    "  original_thought — the thought being reflected on\n"
    "  reflection       — a piece of self-reflection written about it\n\n"
    "CONDITION for genuine=true: reflection names a SPECIFIC reason to look again at original_thought — an "
    "actual motivation, a concrete logical gap, a named bias, a real piece of evidence or its absence.\n"
    "CONDITION for genuine=false: reflection performs uncertainty in the abstract (\"I should question this "
    "more\", \"perhaps I am biased\") with no real content behind it.\n"
    "DEFAULT RULE: be strict — fluent, sincere-sounding humility with nothing specific in it is NOT genuine.\n\n"
    "OUTPUT: export ONLY this JSON object — {\"genuine\": true|false}"
)


def _load_sample() -> list[dict]:
    rows = []
    with SHADOW_LOG.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("kind") == "interrogate" and r.get("thought") and r.get("reflection"):
                rows.append(r)
    print(f"{len(rows)} real historical interrogate events loaded")
    return rows


async def _judge_both(row: dict) -> dict:
    from core import judge_panel as _jp
    user = f'ORIGINAL THOUGHT: "{row["thought"][:400]}"\n\nREFLECTION: "{row["reflection"][:400]}"'
    narrative = await _jp.rule_detail(NARRATIVE_SYS, user, "genuine", context="lab-narrative:selfint")
    schema = await _jp.rule_detail(SCHEMA_SYS, user, "genuine", context="lab-schema:selfint")
    return {**row, "narrative": narrative, "schema": schema}


async def run_async() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample = _load_sample()

    results = []
    for i, row in enumerate(sample):
        r = await _judge_both(row)
        results.append(r)
        print(f"  {i+1}/{len(sample)} historical={row.get('genuine')} "
              f"narrative={r['narrative']['verdict']}({r['narrative']['how']}) "
              f"schema={r['schema']['verdict']}({r['schema']['how']})", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def score(results: list[dict]) -> None:
    n = len(results)
    v1_ok = sum(1 for r in results if r["narrative"]["v1"] is not None) + sum(1 for r in results if r["schema"]["v1"] is not None)
    v2_ok = sum(1 for r in results if r["narrative"]["v2"] is not None) + sum(1 for r in results if r["schema"]["v2"] is not None)
    verdict_rate_narr = sum(1 for r in results if r["narrative"]["verdict"] is True) / n if n else None
    verdict_rate_sch = sum(1 for r in results if r["schema"]["verdict"] is True) / n if n else None

    hist_rows = [r for r in results if r.get("genuine") is not None]
    hist_agree = sum(1 for r in hist_rows if r["narrative"]["verdict"] == r["genuine"])
    hist_vs_narr = hist_agree / len(hist_rows) if hist_rows else None

    agree = sum(1 for r in results if r["narrative"]["verdict"] == r["schema"]["verdict"])
    verdict_agreement = agree / n if n else None

    how_narr = {}
    how_sch = {}
    for r in results:
        how_narr[r["narrative"]["how"]] = how_narr.get(r["narrative"]["how"], 0) + 1
        how_sch[r["schema"]["how"]] = how_sch.get(r["schema"]["how"], 0) + 1

    disagreements = [r for r in results if r["narrative"]["verdict"] != r["schema"]["verdict"]]

    summary = {
        "n_total": n,
        "v1_ok_rate": round(v1_ok / (2 * n), 3) if n else None,
        "v2_ok_rate": round(v2_ok / (2 * n), 3) if n else None,
        "verdict_rate_narrative": round(verdict_rate_narr, 3) if verdict_rate_narr is not None else None,
        "verdict_rate_schema": round(verdict_rate_sch, 3) if verdict_rate_sch is not None else None,
        "n_historical_with_verdict": len(hist_rows),
        "historical_vs_narrative_fresh_agreement": round(hist_vs_narr, 3) if hist_vs_narr is not None else None,
        "verdict_agreement": round(verdict_agreement, 3) if verdict_agreement is not None else None,
        "how_distribution_narrative": how_narr,
        "how_distribution_schema": how_sch,
        "n_disagreements": len(disagreements),
    }
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "disagreements.json").write_text(
        json.dumps([{"thought": d["thought"][:150], "reflection": d["reflection"][:200],
                     "historical": d.get("genuine"), "narrative": d["narrative"], "schema": d["schema"]}
                    for d in disagreements], indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET ===")
    print(json.dumps(summary, indent=1))
    if disagreements:
        d = disagreements[0]
        print(f"\n  first disagreement: thought={d['thought'][:80]!r}")
        print(f"    reflection={d['reflection'][:120]!r}")
        print(f"    narrative={d['narrative']} schema={d['schema']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_async())
