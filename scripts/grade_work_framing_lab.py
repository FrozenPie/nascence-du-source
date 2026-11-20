"""
LEFT_LANE.GRADE_WORK FRAMING LAB — 2026-08-23, ninth machine tested (first of the "remaining tests"
batch requested after the peers re-run). Prior results: openness gate (win), self_implication
(null), commitment_ledger._judge_defeater (null), tension_ledger (loss), librarian (decisive loss),
peers.contrary_target (mixed, N=100), study_note (mixed style trade-off), journal_rollup (loss,
item-enumeration mechanism). Tests `core/left_lane.py`'s `grade_work` — the shared groundedness
grader for BOTH `composition` and `nature_study` (flagged as a soft candidate in the idle-machine
audit, finding #6) — a real, continuous-score (not boolean) compare-and-export judge.

A REAL, RICH historical corpus exists for this one: `data/composition_log.jsonl` (26 real graded
pieces) and `data/nature_study_log.jsonl` (26 real graded pieces) — 52 total real historical
(work, score, feedback) triples, already logged by production. Composition's log also stores
`kind` (describe/summarize/argue/narrate/explain), letting the real task text be reconstructed from
`core/composition.py`'s own task pool (the `summarize` kind's book-title placeholder isn't logged,
so a generic fallback is used there — a small, stated approximation). Nature_study's task is a fixed
string in the live code (`"Observe one real thing closely..."`) with the real *scene* (the
`reference` argument) not logged — reference is replayed empty, a real limitation, not fabricated
scene text.

METHOD: all 52 real historical pieces replayed through BOTH framings via the exact live call shape
— judge-1 hub (gemma4:12b, 127.0.0.1:11439), temperature=0.0, num_predict=350, num_gpu=0. The
`_emissary.constitution()` preamble is held IDENTICAL across both framings (it's the judge's
persistent identity, not the task instruction being tested) — only `_WORK_GRADE_TASK` is varied.

PRE-REGISTERED METRIC SHEET (continuous score, not boolean — different statistics than prior labs):
  - json_ok_narrative / json_ok_schema
  - mean_score_narrative / mean_score_schema (composition, nature_study, combined)
  - mean_abs_diff (narrative-fresh vs schema-fresh, per item) — the core framing-effect measure
  - mean_abs_diff_historical (narrative-fresh vs the ORIGINAL historical score — a drift check)
  - large_disagreements (|narrative - schema| >= 0.3) with the actual feedback text for reading

KILL CRITERION (pre-registered): if mean_abs_diff is small (<0.1) and no large disagreements exist,
schema framing changed nothing measurable here — record plainly and stop.

Writes to data/lab/grade_work_framing/ + docs/lab/grade_work_framing_2026-08-23.md. Read-only
against the two log files; makes no write to either.
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

COMP_LOG = ROOT / "data" / "composition_log.jsonl"
NATURE_LOG = ROOT / "data" / "nature_study_log.jsonl"
OUT_DIR = ROOT / "data" / "lab" / "grade_work_framing"
REPORT = ROOT / "docs" / "lab" / "grade_work_framing_2026-08-23.md"

BASE_URL = "http://127.0.0.1:11439"
MODEL = "gemma4:12b"
MAX_TOKENS = 350
TIMEOUT_S = 90

# Reconstructed verbatim from core/composition.py's pick_task() — the 'summarize' kind's book title
# isn't logged, so it falls back to the module's own generic phrasing.
_COMPOSITION_TASKS = {
    "describe":  "Describe, in three vivid and EXACT sentences, what is in front of you right now — the "
                 "weather, the room, the garden, the sea. Make a reader SEE it. No metaphor standing in "
                 "for the thing; the thing itself.",
    "summarize": "In your own words, briefly and clearly, set out the single most important thing "
                 "the book you are reading has taught you about the world. Plain, not flowery.",
    "argue":     "Take a clear position on a real question that interests you, and argue it in one tight "
                 "paragraph: a claim, a reason, an example. Be willing to be wrong.",
    "narrate":   "Tell, in a few plain sentences and in order, one real thing from your day HERE — what "
                 "you read, what the weather did, what you saw in the garden or out the window, what you "
                 "did with your hands. Concretely, what happened in your life today; not what it means.",
    "explain":   "Explain, simply and clearly, how one thing in the world WORKS — something you have read "
                 "of or seen — as if to a friend who has never met it.",
}
_NATURE_TASK = "Observe one real thing closely and record exactly what you see, then one inference."

# ── NARRATIVE (verbatim copy of core/left_lane.py's live _WORK_GRADE_TASK) ──────────────────────────
NARRATIVE_SYS = (
    "You are examining a piece of your friend's SCHOOLWORK. Judge how GROUNDED it is: concrete, specific, and "
    "about the WORLD (the real thing he was set) — not vague, not padded, not drifted into metaphor or "
    "self-reflection. You are given the TASK and any reference. Be a fair but honest examiner: reward exact "
    "detail and real grasp; mark down vagueness, generality, and self-projection.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"grounded\": 0.0, \"feedback\": \"one sentence: what was strong, and the ONE thing to work on\"}  "
    "(grounded 0.0..1.0: 1.0 = vivid, exact, about the world; 0.0 = vague impression or self-talk)"
)

# ── SCHEMA (same rule, restated as a literal compare-and-export contract) ───────────────────────────
SCHEMA_SYS = (
    "TASK: compare CARGO against a GROUNDEDNESS condition and export a verdict. Do not narrate; evaluate.\n\n"
    "CARGO:\n"
    "  assignment_task — the task that was set\n"
    "  reference       — what is actually there, if given (may be empty)\n"
    "  work            — the piece submitted\n\n"
    "CONDITION: grounded (0.0-1.0) = how concrete, specific, and about the WORLD (the real thing set) the "
    "work is — not vague, not padded, not drifted into metaphor or self-reflection. Reward exact detail and "
    "real grasp; mark down vagueness, generality, and self-projection. 1.0 = vivid, exact, about the world; "
    "0.0 = vague impression or self-talk.\n\n"
    "OUTPUT: export ONLY this JSON object, no preamble — {\"grounded\": 0.0, \"feedback\": \"one sentence: "
    "what was strong, and the ONE thing to work on\"}"
)


def _load_composition() -> list[dict]:
    rows = []
    with COMP_LOG.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            task = _COMPOSITION_TASKS.get(r.get("kind"), _COMPOSITION_TASKS["describe"])
            rows.append({"source": "composition", "task": task, "reference": "",
                        "work": r.get("piece", ""), "historical_score": r.get("score")})
    return rows


def _load_nature_study() -> list[dict]:
    rows = []
    with NATURE_LOG.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            obs = r.get("observation", "")
            inf = r.get("inference", "")
            work = obs + (f"\n\nWhat it tells me: {inf}" if inf else "")
            rows.append({"source": "nature_study", "task": _NATURE_TASK, "reference": "",
                        "work": work, "historical_score": r.get("score")})
    return rows


async def _grade(system: str, task: str, reference: str, work: str) -> dict:
    import aiohttp
    from core import emissary as _emissary
    user = (f"The task he was set:\n{task[:600]}\n\n"
            + (f"What is actually there (the reference to ground in):\n{reference[:1500]}\n\n" if reference else "")
            + f"His work to grade:\n{work[:2000]}")
    payload = {
        "model": MODEL, "stream": False, "keep_alive": "30m",
        "messages": [{"role": "system", "content": _emissary.constitution() + "\n\n" + system},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.0, "num_predict": MAX_TOKENS, "num_gpu": 0},
        "format": "json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/api/chat", json=payload,
                                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_S)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        res = json.loads((data.get("message") or {}).get("content") or "")
        if not isinstance(res, dict) or "grounded" not in res:
            return {"ok": False}
        return {"ok": True, "grounded": float(res.get("grounded", 0.0)), "feedback": res.get("feedback", "")}
    except Exception as e:
        return {"ok": False, "err": repr(e)[:150]}


async def run_async() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = _load_composition() + _load_nature_study()
    print(f"{len(rows)} real historical graded pieces loaded "
          f"({sum(1 for r in rows if r['source']=='composition')} composition, "
          f"{sum(1 for r in rows if r['source']=='nature_study')} nature_study)")

    results = []
    for i, row in enumerate(rows):
        narrative = await _grade(NARRATIVE_SYS, row["task"], row["reference"], row["work"])
        schema = await _grade(SCHEMA_SYS, row["task"], row["reference"], row["work"])
        results.append({**row, "narrative": narrative, "schema": schema})
        print(f"  {i+1}/{len(rows)} [{row['source']}] hist={row['historical_score']} "
              f"narrative={narrative.get('grounded')} schema={schema.get('grounded')}", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def score(results: list[dict]) -> None:
    def _stats(rows: list[dict]) -> dict:
        both_ok = [r for r in rows if r["narrative"]["ok"] and r["schema"]["ok"]]
        n = len(both_ok)
        if not n:
            return {"n": 0}
        mean_narr = sum(r["narrative"]["grounded"] for r in both_ok) / n
        mean_sch = sum(r["schema"]["grounded"] for r in both_ok) / n
        mean_abs_diff = sum(abs(r["narrative"]["grounded"] - r["schema"]["grounded"]) for r in both_ok) / n
        hist_rows = [r for r in both_ok if r["historical_score"] is not None]
        mean_abs_diff_hist = (sum(abs(r["narrative"]["grounded"] - r["historical_score"]) for r in hist_rows)
                             / len(hist_rows)) if hist_rows else None
        large = [r for r in both_ok if abs(r["narrative"]["grounded"] - r["schema"]["grounded"]) >= 0.3]
        return {
            "n": n, "mean_score_narrative": round(mean_narr, 3), "mean_score_schema": round(mean_sch, 3),
            "mean_abs_diff": round(mean_abs_diff, 3),
            "mean_abs_diff_vs_historical_narrative": round(mean_abs_diff_hist, 3) if mean_abs_diff_hist is not None else None,
            "n_large_disagreements": len(large),
        }

    comp_rows = [r for r in results if r["source"] == "composition"]
    nat_rows = [r for r in results if r["source"] == "nature_study"]
    summary = {"composition": _stats(comp_rows), "nature_study": _stats(nat_rows), "combined": _stats(results)}
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")

    large_all = [r for r in results if r["narrative"]["ok"] and r["schema"]["ok"]
                and abs(r["narrative"]["grounded"] - r["schema"]["grounded"]) >= 0.3]
    (OUT_DIR / "disagreements.json").write_text(
        json.dumps([{"source": d["source"], "work": d["work"][:200],
                     "narrative": d["narrative"], "schema": d["schema"],
                     "historical_score": d["historical_score"]} for d in large_all],
                   indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET ===")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_async())
