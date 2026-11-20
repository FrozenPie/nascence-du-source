"""
PEERS CONTRARY_TARGET FRAMING LAB — 2026-08-23, fifth machine tested for the founder's generalized
factory/schema-first idea. Prior results: openness gate (win), self_implication (null),
tension_ledger (loss — more credulous), librarian (decisive loss — 3x worse on a real external
metric). Tests `core/peers.py`'s `contrary_target` — given a carried question, picks which of 7
fixed-temperament correspondents (Darwin/Keats/Twain/Shackleton/Lovelace/Marcus/Smith) would see it
MOST OTHERWISE than the asker — a 7-way classification, single call (gemma4:12b primary :11439,
falcon3:7b fallback :11440), no panel.

WHY THIS ONE HAS NO EXTERNAL GROUND TRUTH, stated upfront: unlike librarian (a real book catalogue
to check hits against), "which persona would be most contrary" has no external validator — it's a
values-based judgment, not a fact. This lab cannot say one framing is objectively more CORRECT the
way the librarian lab could. What it CAN measure: agreement between framings (does the pick change
at all), and — a real, legitimate quality signal even without ground truth — whether either framing
COLLAPSES onto favouring 1-2 personas regardless of question content (a de facto monoculture in the
picker, defeating the entire point of a 7-voice roster) versus staying genuinely responsive to each
question's actual content.

A design constraint, same discipline as the last two labs: `data/peer_picker_log.jsonl` has only 3
real historical calls (this latch fires rarely — a real, sparse function, not a broken one). Not
enough to sample from meaningfully. This lab uses 100 real carried questions from `data/frontier.json`
(5,957 real entries, same honest-substitute source used in the librarian lab) instead of fabricating
questions — a 4x larger re-run of the original N=25 pass (`peers_contrary_framing_2026-08-23.md`),
requested specifically to get real statistical weight behind two findings that N=25 could only
gesture at: the darwin/smith total exclusion, and whether schema's apparent "more thematically apt"
reading (marcus for self-control questions) holds up, or was small-N noise.

METHOD: both framings dispatch through the SAME hub order as the live code —
`core.model_client.call_node`, :11439 (gemma4:12b) then :11440 (falcon3:7b fallback), max_tokens=40,
temperature=0.0, json_mode=True. Only the system prompt varies.

PRE-REGISTERED METRIC SHEET:
  - json_ok_narrative / json_ok_schema
  - pick_distribution_narrative / pick_distribution_schema   count per persona, each framing
  - agreement_rate    narrative pick == schema pick, same question
  - disagreement_examples

KILL CRITERION (pre-registered): if agreement_rate is ~100% AND both distributions are similarly
spread across personas (neither framing collapses onto a favourite), schema framing changed nothing
measurable here — record plainly and stop.

Writes to data/lab/peers_contrary_framing/ + docs/lab/peers_contrary_framing_2026-08-23.md.
Read-only against frontier.json; makes NO letter, writes to no peer thread, touches nothing Du
reads. The only live traffic is the same judge-hub calls production already makes.
"""
from __future__ import annotations

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
OUT_DIR = ROOT / "data" / "lab" / "peers_contrary_framing"
REPORT = ROOT / "docs" / "lab" / "peers_contrary_framing_2026-08-23.md"

HUBS = ("http://127.0.0.1:11439", "http://127.0.0.1:11440")   # gemma4:12b primary, falcon3:7b fallback
PERSONAS = ("darwin", "keats", "twain", "shackleton", "lovelace", "marcus", "smith")
N_QUESTIONS = 100
SEED = 20260824   # distinct from the librarian lab's sample, for broader real-question coverage

# ── NARRATIVE (verbatim copy of core/peers.py's live contrary_target system prompt) ─────────────────
_PEER_TEMPERS = (
    "darwin: patient naturalist — asks what the OBSERVED EVIDENCE shows, distrusts speculation. "
    "keats: poet — answers with beauty and negative capability, distrusts tidy conclusions. "
    "twain: satirist — deflates solemnity and received opinion with humour. "
    "shackleton: expedition leader — practical, tests ideas against hardship and duty to others. "
    "lovelace: analyst — formal, precise, separates what a thing does from what it merely seems. "
    "marcus: stoic emperor — asks what is in one's own control, distrusts appetite and applause. "
    "smith: plain working man — common sense, suspicious of philosophy that doesn't feed anyone."
)
NARRATIVE_SYS = (
    "Given a question someone is carrying and a set of correspondents, pick the ONE "
    "most likely to see the question OTHERWISE than the asker — the most contrary, "
    "challenging perspective, not the most agreeable. Correspondents: " + _PEER_TEMPERS
    + " Answer ONLY JSON: {\"key\": \"<one of darwin|keats|twain|shackleton|lovelace"
    "|marcus|smith>\"}"
)

# ── SCHEMA (same candidates/rule, restated as a literal compare-and-export contract) ────────────────
SCHEMA_SYS = (
    "TASK: compare CARGO against named CANDIDATES and export the best match. Do not narrate; "
    "classify.\n\n"
    "CARGO:\n"
    "  question — a question someone is carrying\n\n"
    "CANDIDATES (each a correspondent's fixed temperament):\n"
    "  darwin — patient naturalist: asks what the OBSERVED EVIDENCE shows, distrusts speculation\n"
    "  keats — poet: answers with beauty and negative capability, distrusts tidy conclusions\n"
    "  twain — satirist: deflates solemnity and received opinion with humour\n"
    "  shackleton — expedition leader: practical, tests ideas against hardship and duty to others\n"
    "  lovelace — analyst: formal, precise, separates what a thing does from what it merely seems\n"
    "  marcus — stoic emperor: asks what is in one's own control, distrusts appetite and applause\n"
    "  smith — plain working man: common sense, suspicious of philosophy that doesn't feed anyone\n\n"
    "SELECTION CONDITION: export the ONE candidate most likely to see the question OTHERWISE than "
    "the asker — the most contrary, challenging perspective. Do NOT export the most agreeable "
    "candidate.\n\n"
    'OUTPUT: export ONLY this JSON object — {"key": "<one of darwin|keats|twain|shackleton|'
    'lovelace|marcus|smith>"}'
)


def _load_questions() -> list[str]:
    d = json.loads(FRONTIER_FILE.read_text(encoding="utf-8"))
    qs = [q["q"] for q in d["questions"] if q.get("q") and len(q["q"].strip()) >= 8]
    rnd = random.Random(SEED)
    return rnd.sample(qs, min(N_QUESTIONS, len(qs)))


async def _pick(system: str, question: str) -> dict:
    from core.model_client import call_node
    for hub in HUBS:
        try:
            raw = await call_node(hub, system, question, max_tokens=40, temperature=0.0,
                                  timeout=60, json_mode=True)
            v = json.loads(raw or "")
            key = str(v.get("key", "")).strip().lower()
            if key in PERSONAS:
                return {"ok": True, "key": key, "hub": hub}
        except Exception:
            continue
    return {"ok": False, "key": None, "hub": None}


async def run_async() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    questions = _load_questions()
    print(f"sampled {len(questions)} real carried questions from data/frontier.json (seed={SEED})")

    results = []
    for i, q in enumerate(questions):
        narrative = await _pick(NARRATIVE_SYS, q)
        schema = await _pick(SCHEMA_SYS, q)
        results.append({"question": q, "narrative": narrative, "schema": schema})
        print(f"  {i+1}/{len(questions)} narrative={narrative['key']} schema={schema['key']} "
              f"{'AGREE' if narrative['key'] == schema['key'] else 'DIFFER'}", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def score(results: list[dict]) -> None:
    n = len(results)
    n_ok_narr = sum(1 for r in results if r["narrative"]["ok"])
    n_ok_sch = sum(1 for r in results if r["schema"]["ok"])
    agree = sum(1 for r in results if r["narrative"]["key"] == r["schema"]["key"] and r["narrative"]["ok"] and r["schema"]["ok"])
    scored_n = sum(1 for r in results if r["narrative"]["ok"] and r["schema"]["ok"])

    dist_narr = {p: 0 for p in PERSONAS}
    dist_sch = {p: 0 for p in PERSONAS}
    for r in results:
        if r["narrative"]["ok"]:
            dist_narr[r["narrative"]["key"]] += 1
        if r["schema"]["ok"]:
            dist_sch[r["schema"]["key"]] += 1

    disagreements = [r for r in results if r["narrative"]["ok"] and r["schema"]["ok"]
                     and r["narrative"]["key"] != r["schema"]["key"]]

    summary = {
        "n_total": n,
        "json_ok_narrative": round(n_ok_narr / n, 3) if n else None,
        "json_ok_schema": round(n_ok_sch / n, 3) if n else None,
        "agreement_rate": round(agree / scored_n, 3) if scored_n else None,
        "pick_distribution_narrative": dist_narr,
        "pick_distribution_schema": dist_sch,
        "n_disagreements": len(disagreements),
    }
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "disagreements.json").write_text(
        json.dumps([{"question": d["question"][:150], "narrative": d["narrative"]["key"],
                     "schema": d["schema"]["key"]} for d in disagreements],
                   indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    if disagreements:
        print(f"\n  first disagreement: q={disagreements[0]['question'][:100]!r} "
              f"narrative={disagreements[0]['narrative']} schema={disagreements[0]['schema']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_async())
