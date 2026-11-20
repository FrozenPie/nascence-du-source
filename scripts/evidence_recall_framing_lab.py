"""
EVIDENCE_RECALL FRAMING LAB — 2026-08-23, part of the "remaining tests" batch, and the last of the
judge_panel-consumer machines named in judge_panel.py's own header comment (self_interrogation
`genuine`, tension_ledger `resolves`, pursuits `advances`, evidence `bears` — all four now tested).
Tests `core/evidence_recall.py`'s `_JUDGE_SYSTEM` — decides whether a remembered episode is real
EVIDENCE bearing on a question someone is carrying (vs. merely thematic/word-overlap resemblance,
or a past conversation ABOUT the question rather than a test of it).

A real historical corpus exists, reconstructed via a DB join: `data/evidence_log.jsonl` logs 11 real
historical asks, each with several judged candidate fragment_ids (v1/v2/how) but NOT the episode
text itself (only the id). Joined against `memory_fragments` (all 11 asks' fragment_ids resolve —
0 missing), this recovers 66 real (question, episode content, historical verdict) triples — the
full real corpus, used entirely, no sampling needed.

METHOD: both framings dispatch through the exact live call — `judge_panel.rule_detail(system, user,
"bears", ...)` — same real panel (JUDGE_1 gemma4:12b, JUDGE_2 falcon3:7b, TIEBREAK yi:34b-v1.5).
Only the system prompt varies.

PRE-REGISTERED METRIC SHEET:
  - verdict_rate_narrative / verdict_rate_schema
  - historical_vs_narrative_fresh_agreement (drift check against the real logged v1 — JUDGE_1 is the
    same gemma4:12b in both the historical log and this lab, so this specifically checks JUDGE_1's
    own stability, not the panel's combined verdict, since only per-judge votes were logged)
  - verdict_agreement (narrative-fresh vs schema-fresh, the core framing test)
  - how_distribution per framing
  - disagreement_examples

KILL CRITERION (pre-registered): if verdict_agreement is ~100% and how_distribution matches, schema
framing changed nothing measurable here — record plainly and stop.

Writes to data/lab/evidence_recall_framing/ + docs/lab/evidence_recall_framing_2026-08-23.md.
Read-only against evidence_log.jsonl and memory_fragments; writes to neither.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EVIDENCE_LOG = ROOT / "data" / "evidence_log.jsonl"
DB_PATH = ROOT / "data" / "memory" / "nascence.db"
OUT_DIR = ROOT / "data" / "lab" / "evidence_recall_framing"
REPORT = ROOT / "docs" / "lab" / "evidence_recall_framing_2026-08-23.md"

# ── NARRATIVE (verbatim copy of core/evidence_recall.py's live _JUDGE_SYSTEM) ───────────────────────
NARRATIVE_SYS = (
    "You judge whether a remembered episode is real EVIDENCE bearing on a question someone is "
    "carrying. Bearing means the episode could actually support, weaken, or complicate an answer "
    "— a lived instance, a counterexample, a relevant fact, or something they were told or read "
    "about the matter itself. If the connection is vague, merely thematic, or just shares words "
    "with the question, it does not bear. IMPORTANT: an episode that is merely a past CONVERSATION "
    "DISCUSSING this same question — someone posing it, the rememberer theorizing an answer — does "
    "NOT bear: talk about a question is not a test of it. "
    "Answer ONLY JSON: {\"bears\": true} or {\"bears\": false}. When uncertain, answer false."
)

# ── SCHEMA (same rule, restated as a literal compare-and-export contract) ───────────────────────────
SCHEMA_SYS = (
    "TASK: compare CARGO against an EVIDENTIARY condition and export a verdict. Do not narrate; "
    "evaluate.\n\n"
    "CARGO:\n"
    "  question — a question someone is carrying\n"
    "  episode  — a remembered episode\n\n"
    "CONDITION for bears=true: episode could actually support, weaken, or complicate an answer to "
    "question — a lived instance, a counterexample, a relevant fact, or something read/told about the "
    "matter itself.\n"
    "CONDITION for bears=false: the connection is vague, merely thematic, or shares only words with "
    "question. Also false if episode is merely a past CONVERSATION DISCUSSING this same question — "
    "someone posing it, the rememberer theorizing an answer — talk about a question is not a test of it.\n"
    "DEFAULT RULE: when uncertain, export bears=false.\n\n"
    "OUTPUT: export ONLY this JSON object — {\"bears\": true|false}"
)


def _load_pairs() -> list[dict]:
    rows = [json.loads(l) for l in EVIDENCE_LOG.open(encoding="utf-8") if l.strip()]
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    pairs = []
    for r in rows:
        question = r.get("question", "")
        for j in r.get("judged", []):
            fr = conn.execute("SELECT content, timestamp FROM memory_fragments WHERE fragment_id=?",
                              (j["fragment_id"],)).fetchone()
            if fr and fr["content"]:
                pairs.append({"question": question, "origin": j.get("origin", ""),
                             "episode": fr["content"], "historical_v1": j.get("v1"),
                             "historical_v2": j.get("v2"), "historical_how": j.get("how")})
    conn.close()
    print(f"{len(pairs)} real (question, episode) pairs resolved via DB join "
          f"across {len(rows)} historical asks")
    return pairs


def _age_text_stub(ts) -> str:
    return "some time ago"   # the real _age_text needs live 'now'; a stable stand-in for the lab


def _user_msg(question: str, origin: str, episode: str) -> str:
    return f"QUESTION: {question}\n\nEPISODE ({origin}, {_age_text_stub(None)}): {episode[:600]}"


async def run_async() -> None:
    from core import judge_panel as _jp
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pairs = _load_pairs()

    results = []
    for i, p in enumerate(pairs):
        user = _user_msg(p["question"], p["origin"], p["episode"])
        narrative = await _jp.rule_detail(NARRATIVE_SYS, user, "bears", context="lab-narrative:evidence")
        schema = await _jp.rule_detail(SCHEMA_SYS, user, "bears", context="lab-schema:evidence")
        results.append({**p, "narrative": narrative, "schema": schema})
        print(f"  {i+1}/{len(pairs)} hist_v1={p['historical_v1']} "
              f"narrative={narrative['verdict']}({narrative['how']}) "
              f"schema={schema['verdict']}({schema['how']})", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def score(results: list[dict]) -> None:
    n = len(results)
    verdict_rate_narr = sum(1 for r in results if r["narrative"]["verdict"] is True) / n if n else None
    verdict_rate_sch = sum(1 for r in results if r["schema"]["verdict"] is True) / n if n else None

    hist_rows = [r for r in results if r.get("historical_v1") is not None]
    hist_agree = sum(1 for r in hist_rows if r["narrative"]["v1"] == r["historical_v1"])
    hist_vs_narr_v1 = hist_agree / len(hist_rows) if hist_rows else None

    agree = sum(1 for r in results if r["narrative"]["verdict"] == r["schema"]["verdict"])
    how_narr, how_sch = {}, {}
    for r in results:
        how_narr[r["narrative"]["how"]] = how_narr.get(r["narrative"]["how"], 0) + 1
        how_sch[r["schema"]["how"]] = how_sch.get(r["schema"]["how"], 0) + 1

    disagreements = [r for r in results if r["narrative"]["verdict"] != r["schema"]["verdict"]]

    summary = {
        "n_total": n,
        "verdict_rate_narrative": round(verdict_rate_narr, 3) if verdict_rate_narr is not None else None,
        "verdict_rate_schema": round(verdict_rate_sch, 3) if verdict_rate_sch is not None else None,
        "n_historical_v1_available": len(hist_rows),
        "historical_v1_vs_narrative_fresh_v1_agreement": round(hist_vs_narr_v1, 3) if hist_vs_narr_v1 is not None else None,
        "verdict_agreement": round(agree / n, 3) if n else None,
        "how_distribution_narrative": how_narr,
        "how_distribution_schema": how_sch,
        "n_disagreements": len(disagreements),
    }
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "disagreements.json").write_text(
        json.dumps([{"question": d["question"][:150], "episode": d["episode"][:200],
                     "historical_v1": d["historical_v1"], "narrative": d["narrative"], "schema": d["schema"]}
                    for d in disagreements], indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET ===")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_async())
