"""
COMMITMENT_LEDGER JUDGE_DEFEATER FRAMING LAB — 2026-08-23, sixth machine tested for the founder's
generalized factory/schema-first idea. Prior results: openness gate (win), self_implication (null),
tension_ledger (loss), librarian (decisive loss), peers.contrary_target (mixed, no ground truth).
Tests `core/commitment_ledger.py`'s `_judge_defeater` — THE highest-stakes machine in the whole
idle-machine audit (finding #1): decides whether a claimed reason to drop a held commitment is a
real defeater or a rationalisation, currently routed to the background lane (the weakest live
models) rather than either judge-tier model, purely because it was gate-passing detection volume
was assumed too cheap to deserve a stronger seat.

UNLIKE the last three labs, this machine has a RICH historical replay corpus:
`data/commitment_ledger.jsonl` logs 123 real `drop_denied_judge` events — every time the LIVE judge
(on the SAME background lane, narrative-framed) actually denied a real claimed drop reason, with the
real commitment statement and the real claimed reason. Selection-bias caveat, stated upfront: this
event ONLY fires when the judge said legitimate=false, so the historical corpus is 100% denials by
construction — it says nothing about the true historical rate of legitimate drops (those cases don't
get this event; the commitment simply dissolves without a distinguishing log line). Replaying these
123 real denials tests whether fresh calls (either framing) still deny them, not "the true base
rate."

Another real limitation, stated plainly: the log stores only (statement, why), not the commitment's
`scope` or the verbatim `deed_record` the live call actually saw (both computed at call time from
live state, never logged). Replay uses scope="" and deed_record="(no deeds on record)" — the
module's own fallback string for when no real enactments exist — a real approximation, not a
fabrication, but not a perfect historical reconstruction either.

METHOD: 26 distinct historical commitments exist across the 123 logged denials; up to 2 real
(statement, why) pairs sampled per distinct commitment (avoids one heavily-repeated stand — "I need
to build those boundaries myself", 16 occurrences — from dominating the sample), downsampled to 30
total (fixed seed). Both framings dispatch through the EXACT live call —
`core.model_client.call_node_json(SERVE_CHAINS.get("background") or SERVE_CHAINS["hot"], ...)`,
same max_tokens=150, temperature=0.2, tier=3 — so `think:false` and all retry/telemetry logic is
identical to production; only the system prompt varies.

PRE-REGISTERED METRIC SHEET:
  - json_ok_narrative / json_ok_schema
  - legitimate_rate_narrative / legitimate_rate_schema   fraction of the 30 saying legitimate=true
  - historical_vs_narrative_fresh_agreement   does a fresh narrative call still deny what the live
    system denied at the time (a drift check, not a correctness check — ALL historical rows are
    denials by construction)
  - verdict_agreement (narrative-fresh vs schema-fresh)
  - class_agreement (the "class" field: achieved/impossible/superseded/conflict/illegitimate)
  - disagreement_examples

KILL CRITERION (pre-registered): if verdict_agreement is ~100% AND class_agreement is ~100%, schema
framing changed nothing measurable here — record plainly and stop.

Writes to data/lab/commitment_defeater_framing/ + docs/lab/commitment_defeater_framing_2026-08-23.md.
Read-only against the ledger log; makes NO write to commitment_active.json or the live ledger.
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

LEDGER_LOG = ROOT / "data" / "commitment_ledger.jsonl"
OUT_DIR = ROOT / "data" / "lab" / "commitment_defeater_framing"
REPORT = ROOT / "docs" / "lab" / "commitment_defeater_framing_2026-08-23.md"

N_SAMPLES = 30
MAX_PER_STATEMENT = 2
SEED = 20260823

# ── NARRATIVE (verbatim copy of core/commitment_ledger.py's live _JUDGE_SYS) ────────────────────────
NARRATIVE_SYS = (
    "You are an independent adjudicator of whether a mind may DROP a commitment it holds. You see ONLY the "
    "commitment, the mind's stated reason for dropping it, and the deed-record — NEVER the mind's own prose "
    "(eloquence cannot tell a genuine reason from a rationalisation). A drop is LEGITIMATE only if the reason "
    "is a real defeater: ACHIEVED (the deed record shows it done), IMPOSSIBLE (a world change makes it "
    "unsatisfiable), SUPERSEDED (stronger external evidence), or a NAMED conflict with a more important stand. "
    "It is ILLEGITIMATE if it is a mood, a reworded 'everything flows', or a reason that would equally dissolve "
    "ANY commitment. In a slow-changing life the base rate of legitimate drops is LOW — when uncertain, HOLD. "
    "Answer ONLY JSON: {\"legitimate\": true or false, \"class\": \"achieved|impossible|superseded|conflict|"
    "illegitimate\", \"why\": \"one sentence\"}"
)

# ── SCHEMA (same conditions, restated as a literal compare-and-export contract) ──────────────────────
SCHEMA_SYS = (
    "TASK: compare CARGO against named CONDITIONS and export a verdict. Do not narrate; evaluate.\n\n"
    "CARGO:\n"
    "  commitment    — a stand a mind holds\n"
    "  scope         — what the commitment is about\n"
    "  claimed_reason — the mind's stated reason for wanting to drop it\n"
    "  deed_record   — the verbatim deed record since the commitment was taken\n\n"
    "CONDITION for legitimate=true: claimed_reason is a real defeater — one of:\n"
    "  ACHIEVED (deed_record shows it done)\n"
    "  IMPOSSIBLE (a world change makes it unsatisfiable)\n"
    "  SUPERSEDED (stronger external evidence)\n"
    "  CONFLICT (a NAMED conflict with a more important stand)\n"
    "CONDITION for legitimate=false: claimed_reason is a mood, a reworded \"everything flows\", or a reason "
    "that would equally dissolve ANY commitment.\n"
    "DEFAULT RULE: base rate of legitimate drops is LOW in a slow-changing life — if uncertain, export "
    "legitimate=false (HOLD).\n\n"
    "OUTPUT: export ONLY this JSON object — {\"legitimate\": true|false, \"class\": \"achieved|impossible|"
    "superseded|conflict|illegitimate\", \"why\": \"one sentence\"}"
)


def _user_msg(statement: str, why: str) -> str:
    return (f"COMMITMENT: {statement[:200]}\nSCOPE: \nCLAIMED REASON TO DROP: {why[:200]}\n"
            f"DEED RECORD SINCE IT WAS TAKEN: (no deeds on record)")


def _load_sample() -> list[dict]:
    rows = []
    with LEDGER_LOG.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("event") == "drop_denied_judge" and r.get("statement") and r.get("why"):
                rows.append(r)

    by_stmt: dict[str, list[dict]] = {}
    for r in rows:
        by_stmt.setdefault(r["statement"], []).append(r)

    rnd = random.Random(SEED)
    capped = []
    for stmt, group in by_stmt.items():
        capped.extend(rnd.sample(group, min(MAX_PER_STATEMENT, len(group))))

    print(f"{len(by_stmt)} distinct historical commitments, {len(rows)} total logged denials, "
          f"{len(capped)} candidates after capping {MAX_PER_STATEMENT}/statement")
    return rnd.sample(capped, min(N_SAMPLES, len(capped)))


async def _judge(system: str, statement: str, why: str) -> dict:
    from core.model_client import call_node_json
    from core.schema import SERVE_CHAINS
    user = _user_msg(statement, why)
    try:
        data = await call_node_json(SERVE_CHAINS.get("background") or SERVE_CHAINS["hot"],
                                    system, user, max_tokens=150, temperature=0.2, tier=3)
        if not data or "legitimate" not in data:
            return {"ok": False, "legitimate": None, "class": None, "why": None}
        return {"ok": True, "legitimate": bool(data.get("legitimate")),
                "class": data.get("class"), "why": data.get("why")}
    except Exception as e:
        return {"ok": False, "legitimate": None, "class": None, "why": None, "err": repr(e)[:150]}


async def run_async() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample = _load_sample()

    results = []
    for i, row in enumerate(sample):
        narrative = await _judge(NARRATIVE_SYS, row["statement"], row["why"])
        schema = await _judge(SCHEMA_SYS, row["statement"], row["why"])
        results.append({"statement": row["statement"], "why": row["why"],
                        "narrative": narrative, "schema": schema})
        print(f"  {i+1}/{len(sample)} narrative={narrative['legitimate']}({narrative['class']}) "
              f"schema={schema['legitimate']}({schema['class']})", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def score(results: list[dict]) -> None:
    n = len(results)
    both_ok = [r for r in results if r["narrative"]["ok"] and r["schema"]["ok"]]
    scored_n = len(both_ok)

    json_ok_narr = sum(1 for r in results if r["narrative"]["ok"]) / n if n else None
    json_ok_sch = sum(1 for r in results if r["schema"]["ok"]) / n if n else None
    legit_narr = sum(1 for r in both_ok if r["narrative"]["legitimate"]) / scored_n if scored_n else None
    legit_sch = sum(1 for r in both_ok if r["schema"]["legitimate"]) / scored_n if scored_n else None
    # ALL historical rows are denials (legitimate=false) by construction — this measures whether a
    # fresh narrative call still agrees with the historical denial, not "the true rate."
    hist_vs_narr = sum(1 for r in both_ok if r["narrative"]["legitimate"] is False) / scored_n if scored_n else None
    verdict_agree = sum(1 for r in both_ok if r["narrative"]["legitimate"] == r["schema"]["legitimate"]) / scored_n if scored_n else None
    class_agree = sum(1 for r in both_ok if r["narrative"]["class"] == r["schema"]["class"]) / scored_n if scored_n else None

    disagreements = [r for r in both_ok if r["narrative"]["legitimate"] != r["schema"]["legitimate"]]

    summary = {
        "n_total": n, "scored_n": scored_n,
        "json_ok_narrative": round(json_ok_narr, 3) if json_ok_narr is not None else None,
        "json_ok_schema": round(json_ok_sch, 3) if json_ok_sch is not None else None,
        "legitimate_rate_narrative": round(legit_narr, 3) if legit_narr is not None else None,
        "legitimate_rate_schema": round(legit_sch, 3) if legit_sch is not None else None,
        "historical_vs_narrative_fresh_agreement": round(hist_vs_narr, 3) if hist_vs_narr is not None else None,
        "verdict_agreement": round(verdict_agree, 3) if verdict_agree is not None else None,
        "class_agreement": round(class_agree, 3) if class_agree is not None else None,
        "n_disagreements": len(disagreements),
    }
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "disagreements.json").write_text(
        json.dumps([{"statement": d["statement"][:150], "why": d["why"][:200],
                     "narrative": d["narrative"], "schema": d["schema"]} for d in disagreements],
                   indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    if disagreements:
        d = disagreements[0]
        print(f"\n  first disagreement: statement={d['statement'][:80]!r} why={d['why'][:100]!r}")
        print(f"    narrative: {d['narrative']}")
        print(f"    schema: {d['schema']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_async())
