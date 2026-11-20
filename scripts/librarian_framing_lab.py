"""
LIBRARIAN FRAMING LAB — 2026-08-23, fourth machine tested for the founder's generalized factory/
schema-first idea (see docs/lab/idle_thought_machine_audit_2026-08-23.md finding #5,
docs/lab/factory_station_2026-08-23.md, docs/lab/self_implication_framing_2026-08-23.md,
docs/lab/tension_ledger_framing_2026-08-23.md — one win, one null, one caution so far). Tests
`core/librarian.py`'s `subjects_for` — maps a carried question to 3-6 Library-of-Congress-style
subject headings, which `core/library_hand.py`'s `search_by_subjects` then turns into real catalogue
rows. Unlike the first three labs, this one has a REAL, OBJECTIVE downstream ground truth available:
does the subject list actually retrieve a real book? (The module's own pre-registered R1 metric,
per its docstring: "fraction of question-asks returning >=1 real candidate.")

A design constraint stated upfront, matching this lab series' discipline: `data/librarian_log.jsonl`
(where real question->subjects->hits history would live) does not exist — confirmed by
`/plan-files-audit` earlier today; the librarian has essentially never been asked a real question in
production. A direct search of all 29,778 logged historical thoughts through the module's OWN
`question_from()` regex extractor found exactly ONE naturally-occurring match. There is no
historical replay corpus for this machine either.

DESIGN CHOICE, stated plainly: this lab draws its test questions from `data/frontier.json`'s 5,957
REAL "carried questions" (Du's own open curiosity/intention threads, born from study/reading/idle
thought) rather than fabricating them — these are exactly the shape of thing the librarian's own
docstring says it serves ("a book that bears on a question you are carrying"), just not literally
routed through the librarian's own rare regex latch. Sourced from real Du data, not invented text.

METHOD: 25 real frontier questions sampled (fixed seed). Each run through BOTH framings via the
SAME dispatch as the live code — `core.model_client.call_node`, hubs :11440 (falcon3:7b, primary)
then :11439 (gemma4:12b, fallback), max_tokens=120, temperature=0.0, json_mode=True — only the
system prompt varies. Each framing's returned subject list is then fed through the REAL
`core.library_hand.search_by_subjects()` against the actual 55,905-book catalogue, giving a genuine,
objective, non-self-referential ground truth: did this subject list retrieve any real book at all.

PRE-REGISTERED METRIC SHEET:
  - json_ok_narrative / json_ok_schema       fraction of calls returning a valid subjects list
  - hit_rate_narrative / hit_rate_schema     fraction of questions where search_by_subjects found
                                             >=1 real catalogue row — the module's OWN R1 metric
  - mean_n_hits_narrative / mean_n_hits_schema
  - subject_jaccard_mean     mean Jaccard overlap between the two framings' subject sets per question
  - disagreement_examples    cases where one framing hit and the other didn't

KILL CRITERION (pre-registered, same standard as the series): if hit_rate is materially the same
between framings AND subject_jaccard_mean is high (near-identical subject choices), schema framing
changed nothing measurable here — record plainly and stop.

Writes to data/lab/librarian_framing/ + docs/lab/librarian_framing_2026-08-23.md. Read-only against
frontier.json and the real book catalogue; writes NOTHING back to either. The only live traffic is
the same judge-hub calls production already makes constantly.
"""
from __future__ import annotations

import asyncio
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FRONTIER_FILE = ROOT / "data" / "frontier.json"
OUT_DIR = ROOT / "data" / "lab" / "librarian_framing"
REPORT = ROOT / "docs" / "lab" / "librarian_framing_2026-08-23.md"

HUBS = ("http://127.0.0.1:11440", "http://127.0.0.1:11439")   # falcon3:7b primary, gemma4:12b fallback
N_QUESTIONS = 25
SEED = 20260823

# ── NARRATIVE (verbatim copy of core/librarian.py's live _SYSTEM) ──────────────────────────────────
NARRATIVE_SYS = (
    "You are a library catalogue assistant. Given a reader's question, return ONLY JSON: "
    "{\"subjects\": [3 to 6 Library-of-Congress-style subject headings under which books bearing "
    "on the question would be filed, e.g. \"Conduct of life\", \"Ethics\", \"Liberty\", "
    "\"Natural history\"]}. Short established headings only — no sentences, no book titles."
)

# ── SCHEMA (same task, restated as a literal compare-and-export contract) ───────────────────────────
SCHEMA_SYS = (
    "TASK: map CARGO to catalogue subject headings and export a list. Do not narrate; classify.\n\n"
    "CARGO:\n"
    "  question — a reader's question\n\n"
    "CONDITIONS on the export:\n"
    "  - 3 to 6 headings\n"
    "  - each a short, ESTABLISHED Library-of-Congress-style subject heading (e.g. \"Conduct of "
    "life\", \"Ethics\", \"Liberty\", \"Natural history\")\n"
    "  - no sentences, no book titles, no invented headings\n"
    "  - headings must be ones under which books bearing on the question would actually be filed\n\n"
    'OUTPUT: export ONLY this JSON object — {"subjects": ["...", "..."]}'
)


def _load_questions() -> list[str]:
    d = json.loads(FRONTIER_FILE.read_text(encoding="utf-8"))
    qs = [q["q"] for q in d["questions"] if q.get("q") and len(q["q"].strip()) >= 8]
    rnd = random.Random(SEED)
    return rnd.sample(qs, min(N_QUESTIONS, len(qs)))


async def _subjects_for(system: str, question: str) -> dict:
    from core.model_client import call_node
    for hub in HUBS:
        try:
            raw = await call_node(hub, system, question, max_tokens=120, temperature=0.0,
                                  timeout=60, json_mode=True)
            v = json.loads(raw or "")
            subs = [s.strip() for s in (v.get("subjects") or [])
                    if isinstance(s, str) and 2 < len(s.strip()) < 60][:6]
            if subs:
                return {"ok": True, "subjects": subs, "hub": hub}
        except Exception as exc:
            continue
    return {"ok": False, "subjects": [], "hub": None}


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = {s.lower() for s in a}, {s.lower() for s in b}
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0


async def run_async() -> None:
    from core import library_hand as _lib
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    questions = _load_questions()
    print(f"sampled {len(questions)} real carried questions from data/frontier.json (seed={SEED})")

    results = []
    for i, q in enumerate(questions):
        narrative = await _subjects_for(NARRATIVE_SYS, q)
        schema = await _subjects_for(SCHEMA_SYS, q)
        narr_hits = await asyncio.to_thread(_lib.search_by_subjects, narrative["subjects"], 8) if narrative["ok"] else []
        sch_hits = await asyncio.to_thread(_lib.search_by_subjects, schema["subjects"], 8) if schema["ok"] else []
        results.append({
            "question": q, "narrative": narrative, "schema": schema,
            "narrative_n_hits": len(narr_hits), "schema_n_hits": len(sch_hits),
            "jaccard": _jaccard(narrative["subjects"], schema["subjects"]),
        })
        print(f"  {i+1}/{len(questions)} narrative_hits={len(narr_hits)} schema_hits={len(sch_hits)} "
              f"jaccard={results[-1]['jaccard']:.2f}", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def score(results: list[dict]) -> None:
    n = len(results)
    n_ok_narr = sum(1 for r in results if r["narrative"]["ok"])
    n_ok_sch = sum(1 for r in results if r["schema"]["ok"])
    hit_narr = sum(1 for r in results if r["narrative_n_hits"] > 0)
    hit_sch = sum(1 for r in results if r["schema_n_hits"] > 0)
    mean_hits_narr = sum(r["narrative_n_hits"] for r in results) / n if n else 0
    mean_hits_sch = sum(r["schema_n_hits"] for r in results) / n if n else 0
    mean_jaccard = sum(r["jaccard"] for r in results) / n if n else 0

    disagreements = [r for r in results if (r["narrative_n_hits"] > 0) != (r["schema_n_hits"] > 0)]

    summary = {
        "n_total": n,
        "json_ok_narrative": round(n_ok_narr / n, 3) if n else None,
        "json_ok_schema": round(n_ok_sch / n, 3) if n else None,
        "hit_rate_narrative": round(hit_narr / n, 3) if n else None,
        "hit_rate_schema": round(hit_sch / n, 3) if n else None,
        "mean_n_hits_narrative": round(mean_hits_narr, 2),
        "mean_n_hits_schema": round(mean_hits_sch, 2),
        "subject_jaccard_mean": round(mean_jaccard, 3),
        "n_hit_disagreements": len(disagreements),
    }
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "disagreements.json").write_text(
        json.dumps([{"question": d["question"][:150],
                     "narrative_subjects": d["narrative"]["subjects"], "narrative_hits": d["narrative_n_hits"],
                     "schema_subjects": d["schema"]["subjects"], "schema_hits": d["schema_n_hits"]}
                    for d in disagreements], indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    if disagreements:
        d = disagreements[0]
        print(f"\n  first hit-disagreement: q={d['question'][:100]!r}")
        print(f"    narrative: {d['narrative']['subjects']} -> {d['narrative_n_hits']} hits")
        print(f"    schema:    {d['schema']['subjects']} -> {d['schema_n_hits']} hits")


if __name__ == "__main__":
    asyncio.run(run_async())
