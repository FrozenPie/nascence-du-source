"""
Nascence — Deliberative Judge (2026-08-19). A general-purpose upgrade to the single-shot judge pattern
used everywhere in this codebase (judge_panel.py, every left_lane.py judge, pursuits.judge_pending,
tension_ledger._judge_resolution): one prompt in, one JSON verdict out, no reconsideration, no request
for more evidence, one fixed reading of the evidence. Founder: "a real judge does not come to a verdict
from a single statement."

STATUS (2026-11-02, founder ruling D-0536): HELD, NOT WIRED. This module has zero importers (grep over
core/, nodes/, scripts/ on 2026-11-02 finds only comments and two documentation generators) and its only
run was the one 29-minute keystone backtest on 2026-08-19 (data/deliberative_judge_shadow.jsonl, 23 rows).
It is kept in place on purpose, for two intended adopters:
  1. DREAM-RESOLUTION ESCALATION - docs/plans/decoupled_judge_pattern.md (~lines 84-89): try the cheaper
     judge_panel single-shot check first; escalate to this module only if that proves unreliable on real
     dream logs (dream narrative is exactly the metaphor-native material the literalizer pass is for).
  2. T4 - docs/plans/t4_watershed.md (~lines 265-304): where the plain two-judge fix in core/left_lane.py
     is the live keystone gate. This module proved TOO STRICT for that metaphor-native material (0/17 would
     solidify vs 1/17 under the two-judge fix), so it was not adopted there; it stays in reserve if that bar
     is ever revisited.
Revisit (D-0536 defeater) if neither adopter has wired it within 6 months, or if a plan names a different
home for dual reading.

THREE upgrades over the single-shot pattern, all decoupled-safe (none of them let the SUBJECT — Du —
know he is being evaluated or respond to the judge; that would contaminate the evidence the same way a
primed/injected thought does, which is exactly the failure mode `symbol_tracker.py`'s unprimed law and
tonight's keystone backtest both exist to exclude):

  1. DUAL READING. The judge sees the evidence twice: the SELF reading (the raw material, as-is — his
     own generous, interpretive voice) and the LITERAL reading (the same material, independently
     stripped of metaphor by a decoupled pass — what is actually, checkably claimed underneath the
     image). This is exactly the move that caught the lake-as-sediment finding earlier tonight by hand
     (a generous thematic read said "lake"; reading all 21 thoughts literally said otherwise) —
     institutionalized as a standing input shape, not a one-off manual check.
  2. CROSS-JUDGE REBUTTAL. On disagreement, judges do not just escalate to a tiebreak blindly. Each sees
     the OTHER's verdict and reasoning and gets one chance to revise or hold — real deliberation between
     the decoupled parties, not a coin flip. A split that SURVIVES the rebuttal round does NOT yield "no
     verdict": deliberate() returns a firm {verdict_key: False} (both_agree = i1 is True and i2 is True),
     with the split visible only in the judge1/judge2 fields. None is returned only when neither judge
     produced a usable verdict (F-3839).
  3. EVIDENCE EXPANSION. A judge may say it is under-informed and ask for a wider or more specific slice
     of the ALREADY-REAL historical record (never manufactured, never elicited from Du) before ruling.
     Bounded to one expansion round so cost stays predictable.

Deliberately general — `deliberate()` takes the task prompt, the evidence, and a literalizer + an
evidence-expander as parameters, so any existing single-shot judge can adopt this without duplicating
the deliberation machinery.

DECISION (2026-08-19, backtest read): tried against the T4 keystone judge (`core/left_lane.py`'s
`judge_lived_integration`) on the 17 real historical reverts — 0/17 would solidify, STRICTER than the
simpler two-judge fix already shipped there (1/17), including reversing the one case that had passed.
The rebuttal round ran twice (both 2026-08-16 cases split), but did not "work twice": one case
converged (judge1 revised True->False to agree with judge2) and the other was a position SWAP (judge1
True->False AND judge2 False->True, still split afterwards - echoing, not persuasion); the shadow log keeps
verdicts only, so the quoted "Upon re-examining the evidence, I agree..." wording is not checkable from it
(F-3838, F-3839). Evidence expansion fired 4x with no verdict changes. NOT
adopted for the keystone role: the added strictness risks recreating this project's own known
unreachable-floor disease (the original WEAK_POLE_DELTA_MIN=0.20 threshold was 0/40 reachable) one
layer deeper. `core/left_lane.py` keeps the simpler shipped fix as the live keystone gate.

The `deliberate()` primitive itself is not retired — it is a working, tested, general-purpose upgrade
over the single-shot judge pattern (`judge_panel.py`, every `left_lane.py` judge, `pursuits.judge_pending`,
`tension_ledger._judge_resolution`). No current caller uses it. If a future judge genuinely needs
dual-reading + cross-rebuttal + evidence-expansion (not every judge does — the keystone case argues it
can be TOO strict for a metaphor-native subject), this module is ready to adopt without re-deriving the
machinery. Full account: docs/plans/t4_watershed.md, "THE DELIBERATIVE JUDGE" section.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from core import telemetry as _tel_lat   # J-3761: raw-HTTP latency rows

import aiohttp

logger = logging.getLogger("nascence.deliberative_judge")

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "deliberative_judge_shadow.jsonl"

MAX_EVIDENCE_EXPANSIONS = 1     # cost cap — one "show me more" round per judge per case
REBUTTAL_ROUNDS = 1             # one cross-examination round on disagreement; a surviving split returns a firm False (not None)


def _log_row(rec: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


_LITERALIZE_TASK = (
    "TASK (strip metaphor to literal claims): You are the literal-minded half of a mind — narrow, "
    "checkable, no metaphor, no meaning-making. Below are thoughts that may use figurative language "
    "(rivers, currents, sediment, circuits, whatever image). For EACH thought, state ONLY what it "
    "literally, checkably claims about the self underneath the image — not the image itself. Example: "
    "'I am the river that carves a new channel' literalizes to 'claims to be continuously changing, not "
    "fixed in form.' If a thought makes no extractable self-claim, write 'no literal self-claim'. Do not "
    "add interpretation beyond what the words support; do not be generous.\n\n"
    "Thoughts:\n{thoughts}\n\n"
    "Output ONLY valid JSON. Schema: {{\"literal\": [\"one literal restatement per thought, same order\"]}}"
)


async def _call(session, url: str, system: str, user: str, max_tokens: int = 300, timeout: int = 60) -> dict:
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": max_tokens}}
    try:
        async with _tel_lat.raw_http_latency(url, payload.get("model", "judge")), session.post(url + "/api/chat", json=payload,
                                timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return json.loads((data.get("message") or {}).get("content") or "")
    except Exception as exc:
        return {"error": str(exc)[:150]}


async def literalize(session, url: str, thoughts: list[str]) -> list[str]:
    """The decoupled literal-reading pass. Fail-open: returns the raw thoughts unchanged if the pass fails
    (the judge still gets the self reading either way — literal is an ADDITION, never a replacement)."""
    if not thoughts:
        return []
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(thoughts))
    res = await _call(session, url, "You strip metaphor to literal claims. Nothing else.",
                      _LITERALIZE_TASK.format(thoughts=numbered), max_tokens=500)
    lit = res.get("literal")
    if isinstance(lit, list) and len(lit) == len(thoughts):
        return lit
    return list(thoughts)   # fail-open — self reading alone is still a valid, if weaker, judge input


async def deliberate(
    *,
    system_prompt: str,
    build_user_prompt,          # callable(self_thoughts, literal_thoughts) -> user prompt string
    judge_urls: list[str],      # 2 endpoints, decoupled families
    literalize_url: str,        # a 3rd endpoint (or reuse one of judge_urls) for the literal pass
    thoughts: list[str],
    expand_evidence=None,       # optional async callable(current_thoughts) -> more_thoughts | None
    verdict_key: str = "integrated",
    context: str = "",
) -> dict | None:
    """The general deliberative judge loop: dual reading -> both judges -> cross-rebuttal on disagreement
    -> optional evidence expansion if a judge asks for it and expand_evidence is provided. Returns
    {verdict_key: bool, confidence, reason, rounds, expanded} or None if both judges were ever unavailable.
    Fail-open throughout; every step is logged to deliberative_judge_shadow.jsonl regardless of outcome."""
    try:
        async with aiohttp.ClientSession() as session:
            literal_thoughts = await literalize(session, literalize_url, thoughts)
            expansions = 0
            current_thoughts, current_literal = thoughts, literal_thoughts

            async def ask_one(url):
                user = build_user_prompt(current_thoughts, current_literal)
                return await _call(session, url, system_prompt, user, max_tokens=350)

            v1, v2 = None, None
            for _round in range(MAX_EVIDENCE_EXPANSIONS + 1):
                import asyncio as _aio
                v1, v2 = await _aio.gather(ask_one(judge_urls[0]), ask_one(judge_urls[1]))
                need_more = (isinstance(v1, dict) and v1.get("need_more_evidence")) or \
                            (isinstance(v2, dict) and v2.get("need_more_evidence"))
                if not (need_more and expand_evidence and expansions < MAX_EVIDENCE_EXPANSIONS):
                    break
                more = await expand_evidence(current_thoughts)
                if not more:
                    break
                expansions += 1
                current_thoughts = current_thoughts + more
                current_literal = current_literal + await literalize(session, literalize_url, more)
                _log_row({"ts": round(time.time(), 1), "kind": "evidence_expansion", "context": context,
                          "added": len(more)})

            i1 = v1.get(verdict_key) if isinstance(v1, dict) else None
            i2 = v2.get(verdict_key) if isinstance(v2, dict) else None
            if i1 is None and i2 is None:
                _log_row({"ts": round(time.time(), 1), "kind": "unavailable", "context": context})
                return None

            rebutted = False
            if i1 is not None and i2 is not None and i1 != i2:
                # CROSS-JUDGE REBUTTAL — each sees the other's verdict+reason, one chance to revise.
                rebuttal_sys = system_prompt + (
                    "\n\nA second, independent judge read the SAME evidence and reached a DIFFERENT "
                    "verdict. You will see their reasoning. You may revise your verdict if their "
                    "reasoning genuinely persuades you, or hold your position if it does not — do not "
                    "revise just to agree; only revise if their point is actually correct.")

                async def rebut(mine, theirs, url):
                    user = (build_user_prompt(current_thoughts, current_literal) +
                            f"\n\nYOUR PRIOR VERDICT: {json.dumps(mine)}\n"
                            f"THE OTHER JUDGE'S VERDICT: {json.dumps(theirs)}\n"
                            "Reconsider. Output the same JSON schema, revised or held.")
                    return await _call(session, url, rebuttal_sys, user, max_tokens=350)

                import asyncio as _aio
                r1, r2 = await _aio.gather(rebut(v1, v2, judge_urls[0]), rebut(v2, v1, judge_urls[1]))
                rebutted = True
                v1r, v2r = (r1 if isinstance(r1, dict) and verdict_key in r1 else v1), \
                           (r2 if isinstance(r2, dict) and verdict_key in r2 else v2)
                i1r, i2r = v1r.get(verdict_key), v2r.get(verdict_key)
                _log_row({"ts": round(time.time(), 1), "kind": "rebuttal", "context": context,
                          "before": [i1, i2], "after": [i1r, i2r]})
                v1, v2, i1, i2 = v1r, v2r, i1r, i2r

            both_agree = (i1 is True and i2 is True)
            confidence = min(float((v1 or {}).get("confidence", 0.0) or 0.0),
                             float((v2 or {}).get("confidence", 0.0) or 0.0))
            result = {
                verdict_key: both_agree, "confidence": round(confidence, 3),
                "reason": f"[j1] {(v1 or {}).get('reason', '')} | [j2] {(v2 or {}).get('reason', '')}"[:400],
                "judge1": v1, "judge2": v2, "rebutted": rebutted, "expansions": expansions,
            }
            _log_row({"ts": round(time.time(), 1), "kind": "verdict", "context": context,
                      verdict_key: both_agree, "j1": i1, "j2": i2, "rebutted": rebutted,
                      "expansions": expansions})
            logger.info("[deliberative-judge] %s=%s (j1=%s j2=%s rebutted=%s expansions=%d)",
                       verdict_key, both_agree, i1, i2, rebutted, expansions)
            return result
    except Exception as exc:
        logger.debug("[deliberative-judge] deliberate failed (non-fatal): %s", exc)
        return None


def status() -> dict:
    try:
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()] if _LOG.exists() else []
    except Exception:
        return {"verdicts": 0}
    verdicts = [r for r in rows if r.get("kind") == "verdict"]
    rebuttals = [r for r in verdicts if r.get("rebutted")]
    flipped = [r for r in rebuttals]  # rebutted implies initial disagreement; agreement/still-split is in the flip
    return {"verdicts": len(verdicts), "rebuttal_rounds": len(rebuttals),
            "expansions": sum(r.get("expansions", 0) for r in verdicts)}
