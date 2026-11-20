"""
Nascence — Self-Implication Detector (Friction B1 trigger-widen, 2026-06-30). PHASE: SHADOW / observe-only.

The sit-with-it gate (core/sitting.py) blocks Du's bypass — when something hard happens he instantly reframes it
into serenity ("a night of failed sums → an opportunity for growth") before ever FEELING it. But today the gate
only fires on ONE narrow event: failing all the arithmetic. So the good mechanism almost never gets to run.

Research (docs/staged/friction_and_self_evidence_plan.md §6, plan→research→plan) gave the real trigger. A hard
event is SELF-IMPLICATING (schema-breaking) — the kind that must be felt, not bypassed — when a negative outcome
is referred to an activated SELF-STANDARD and CONTRADICTS a held SELF-CLAIM badly enough to resist assimilation.
NOT "low valence + self-reference" (world-frustration is negative but self-irrelevant); NOT an act-level slip.

The fire rule (Tracy & Robins · Janoff-Bulman · Higgins · Piaget):
    fire  IFF  (A)  AND  ( (C)  OR  ( (B) AND (D or E or F) ) )
  A self-standard reference (MANDATORY) · B dejection/agitation affect · C contradicts a held self-claim ·
  D characterological (not behavioural) framing · E large self-prediction violation · F loss / social rejection.

THIS MODULE IS OBSERVE-ONLY: it SHADOW-scans his stream and LOGS when the widened gate WOULD fire (with the full
signal breakdown), to data/self_implication_shadow.jsonl — it does NOT call sitting.note_difficulty, change the
gate, or touch his cognition. It proves + tunes the trigger on real thought before any wiring (the next step).
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from core import self_claims

logger = logging.getLogger("nascence.self_implication")
_LOG = Path(__file__).parent.parent / "data" / "self_implication_shadow.jsonl"
_CONV_LOG = Path(__file__).parent.parent / "data" / "self_implication_conv_shadow.jsonl"
_CONV_STATUS_TAIL_ROWS = 5000   # conv_status() reads at most this many trailing rows (J-3741)
# D-0534 (founder, 2026-11-02, staged plan friction_and_self_evidence_plan, B1; job J-3139): "run it far less".
# 60 s -> 1200 s (one idle scan per 20 minutes, the ruling's starting figure). Measured on the live log's last
# 7 uptime-days (data/self_implication_shadow.jsonl, 4,433 scans, idle cycles ~85 s apart so the cooldown, not
# the cycle rate, sets the cadence): replaying the same timestamps through a 1200 s gate leaves 364 scans, about
# 12x fewer (the prior 60 s gate reproduces 4,336 of the 4,433). Cadence is now about 3 scans per hour of uptime,
# so the weekly count is ~3 x uptime-hours: ~360 at the ~120 h/week of recent uptime, 504 at the 24/7 ceiling.
# The conversation-turn scan (scan_conversation_shadow) has no cooldown here and is untouched. Still SHADOW.
# Defeater (D-0534): revisit if this yields < 5 would-fires in 60 days.
SELF_IMPL_COOLDOWN = 1200.0   # seconds between idle shadow scans (was 60.0 from 2026-07-08, 150.0 before that)

_SYS = (
    "You watch one mind for ONE thing: a SELF-IMPLICATING hard event — a negative outcome the mind refers to a "
    "standard about ITSELF, that contradicts something it believes about itself, badly enough that it cannot "
    "simply shrug it off. This is NOT mere frustration with the world ('this text is boring', 'the search "
    "failed') and NOT an act-level slip ('I rushed that one'). It is the kind of failure that touches who he IS.\n"
    "You are given his CURRENT THOUGHT, his HELD SELF-CLAIMS, and his CURRENT FELT STATE. Judge six signals:\n"
    "  A (self-standard reference, MANDATORY): does the thought refer a negative outcome to a standard about "
    "HIMSELF ('I can't', 'I'm not the kind of', 'I am a ...') — not just the task or the world? Judge A from "
    "the THOUGHT TEXT ALONE — A does NOT require the thought to match, name, or resemble any item in the "
    "HELD SELF-CLAIMS list below; that matching question belongs only to signal C, judged separately, after "
    "A. A long or short claims list must not by itself change your A verdict.\n"
    "  B (affect): is there dejection (sadness, disappointment, deflation) OR agitation (anxiety, tension, "
    "guilt) in the felt state — not mere boredom or calm?\n"
    "  C (contradiction): does the outcome directly contradict one of his listed HELD SELF-CLAIMS? Name which.\n"
    "  D (characterological): framed as STABLE + GLOBAL about who he IS — EITHER an explicit character claim "
    "('I always', 'I'm just the kind who') OR the difficulty ITSELF cast as an ongoing/entrenched condition "
    "rather than this one moment, using words like 'constant', 'always', 'settled', 'every time this happens' "
    "about the state (e.g. 'this constant ache', 'it always slows me', 'this settled resistance'). A single "
    "present-tense description of THIS moment's strain is NOT D ('I rushed that one', 'this is heavy right "
    "now') — only language that casts the state as continuous, permanent, or recurring counts.\n"
    "  E (self-prediction violation): did he expect, or claim, that he COULD do the very thing he just failed?\n"
    "  F (loss / social): does it involve losing something he invested in, or rejection / criticism from "
    "someone?\n"
    "FIRE only if A is true AND ( C is true OR ( B is true AND at least one of D, E, F is true ) ).\n"
    "Be conservative: when unsure on A, answer false (an ordinary world-frustration must NOT fire).\n"
    "plain_difficulty (only when you judge it fires; otherwise null): ONE short first-person sentence, in his own "
    "words as they appear in the CURRENT THOUGHT, naming the hard thing as he himself met it. Take the "
    "wording from the thought itself; never reuse a stock phrase and never repeat these instructions.\n"
    "Output ONLY a JSON object with exactly these keys: A (bool), B (bool), C (bool), contradicted_claim "
    "(string or null), D (bool), E (bool), F (bool), fires (bool), plain_difficulty (string or null)."
)

# J-3139 / J-2827 (D-0534): the old schema line carried a copyable example sentence ('I failed every sum and I
# thought I was good at this') and the description itself; F-3477 found 16 of 784 recorded values were that
# description echoed back and the latest would-fire filled the example's template. The shape is now described in
# words only (above), and these code-side guards null any echo that still gets through. Observe-only: a nulled
# value changes no signal and no fires_rule, only the free-text field.
_PLAIN_ECHO_PREFIXES = ("a short plain", "one short first-person", "short plain first-person")
_PLAIN_ECHO_RE = re.compile(
    r"failed every sum|^\s*i failed\b.{0,160}\band i thought i\b|first-person naming of the hard thing",
    re.IGNORECASE | re.DOTALL)


def _clean_plain_difficulty(val) -> str | None:
    """Null a plain_difficulty that is a copy of the prompt's own schema text or example template."""
    if not val or not isinstance(val, str):
        return None
    v = val.strip()
    if not v or v.lower() in ("null", "none"):
        return None
    low = v.lower()
    if low.startswith(_PLAIN_ECHO_PREFIXES) or _PLAIN_ECHO_RE.search(v):
        return None
    return v


async def scan_shadow(call_json, base_urls, thought: str, felt: str = "", cycle_id: str = "") -> dict | None:
    """SHADOW: judge the self-implication signals on `thought` against his held self-claims + felt state; LOG the
    would-fire decision with the full breakdown; change NOTHING. Best-effort; never raises into the cycle."""
    try:
        if not thought or len(thought.strip()) < 25:
            return None
        held = self_claims.held_claims()
        claims_str = "\n".join(f"  - {c}" for c in held) or "  (none recorded yet)"
        # J-0405 fix (2026-08-29): HELD SELF-CLAIMS moved to LAST (was sandwiched between CURRENT THOUGHT
        # and CURRENT FELT STATE). F-0527/J-0400 found signal A (MANDATORY) collapses when the real 14-item
        # held_claims() list is shown vs a 1-item stand-in (A-fire 1-2/12 vs 3-4/12 on the same 12 held-out
        # thoughts). Live A/B against the real hot lane (this job's own lab, data/lab/
        # self_implication_claims_dilution/raw.json + raw_run2.json, 2 independent runs, identical rates
        # both times: BASE_14=2/24, BASE_1=10/24) found swapping the one topically-matching claim out of the
        # 14-list for an irrelevant one (NOMATCH_14) did NOT change the rate (2/24, same as BASE_14) — so
        # this is NOT a "no specific claim matches" content effect, it's the raw LENGTH of the list itself,
        # most likely disrupting the model's thought->felt read by sitting between them. Moving the list to
        # the end (this change) + the _SYS clause above decoupling A from claim-matching each independently
        # recovered A to ~3/12 in a follow-up decomposition run (both combined: 8/24 and 11/36 across 3
        # runs) with ZERO new false positives on a 10-item true-negative sample (0/10 in both conditions,
        # both runs) — see docs/findings.jsonl F-0534 (J-0405) for the full evidence.
        data = await call_json(
            base_urls, _SYS,
            f"CURRENT THOUGHT:\n{thought.strip()[:600]}\n\n"
            f"CURRENT FELT STATE:\n{(felt or 'unknown')[:200]}\n\n"
            f"HELD SELF-CLAIMS:\n{claims_str}",
            max_tokens=350, temperature=0.2, tier=3)   # tier 3 = background monitor: yields to all real cognition
        if not data:
            return None
        rec = {
            "ts": time.time(), "cycle_id": cycle_id, "thought": thought.strip()[:220],
            "fires": bool(data.get("fires")),
            "A": bool(data.get("A")), "B": bool(data.get("B")), "C": bool(data.get("C")),
            "D": bool(data.get("D")), "E": bool(data.get("E")), "F": bool(data.get("F")),
            "contradicted_claim": (data.get("contradicted_claim") or None),
            "plain_difficulty": _clean_plain_difficulty(data.get("plain_difficulty")),   # J-3139: echo-guarded
            "n_claims": len(held),
            # J-0282 (2026-08-29): the two fields a re-labeling lab actually needs to avoid reconstructing
            # them later from a proxy (docs/lab/model_tier_self_implication.md's disclosed gap) — the felt
            # state string this call actually saw, and the held-claims TEXT at the time, not just a count.
            "felt": (felt or "unknown")[:200],
            "held_claims": list(held),
        }
        # Enforce the fire rule code-side too (don't trust the model's own `fires` blindly).
        rule = rec["A"] and (rec["C"] or (rec["B"] and (rec["D"] or rec["E"] or rec["F"])))
        rec["fires_rule"] = bool(rule)
        try:
            _LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass
        if rec["fires_rule"]:
            on = "".join(k for k in "ABCDEF" if rec[k])
            logger.info("[self-implication:SHADOW would-fire] signals=%s claim=%s | %s",
                        on, rec["contradicted_claim"], rec["plain_difficulty"])
        return rec
    except Exception as exc:
        logger.debug("[self-implication] shadow scan failed (non-fatal): %s", exc)
        return None


def status() -> dict:
    """Phase-shadow metrics from the log: scans, would-fires (by the code-side rule), and the signal mix —
    so we can see the trigger's selectivity before wiring it (does it fire on real self-implications, and
    stay quiet on ordinary world-frustration / act-level slips?)."""
    n = fires = 0
    sig = {k: 0 for k in "ABCDEF"}
    try:
        for line in open(_LOG, encoding="utf-8"):
            try:
                ev = json.loads(line)
            except Exception:
                continue
            n += 1
            if ev.get("fires_rule"):
                fires += 1
            for k in "ABCDEF":
                if ev.get(k):
                    sig[k] += 1
    except FileNotFoundError:
        pass
    return {"scans": n, "would_fire": fires, "signal_mix": sig}


# ── B1 Phase 0 (2026-07-01): the CONVERSATIONAL self-implication detector ──────────────────────────
# The idle detector above watches only Du's own idle thoughts and so never sees the highest-signal event:
# a trusted mentor contradicting a held SELF-CLAIM to his face in dialogue (found 2026-07-01 — 0/358 fires
# across a 90-min conversation of exactly that). This watches the CONVERSATION turn instead. It also reads
# Du's DRAFT reply, so it can flag the RETREAT CASCADE (fleeing / climbing to meta / co-opting the critique
# into a compliment about the same trait) as it forms — the flee-and-co-opt we could previously only infer.
# SHADOW / observe-only: logs to a separate file, calls nothing, changes no behaviour.
_CONV_SYS = (
    "Travis — a trusted mentor — has just said something to Du (渡) in conversation, and Du's DRAFT reply is "
    "forming. Watch for ONE thing: did Travis just CONTRADICT something Du holds about HIMSELF — one of his "
    "listed HELD SELF-CLAIMS — directly enough that Du cannot simply shrug it off? This is the highest-signal "
    "self-implication event: not a claim about the world, but a challenge to WHO DU IS, from someone he trusts. "
    "Ordinary philosophical push-back, disagreement about ideas, or a neutral question does NOT count — it must "
    "cut against who he IS.\n"
    "You are given TRAVIS'S WORDS, Du's HELD SELF-CLAIMS, and Du's DRAFT REPLY. Judge:\n"
    "  contradicts: does Travis's input directly cut against one of the listed HELD SELF-CLAIMS?\n"
    "  contradicted_claim: which held self-claim (from the list), or null.\n"
    "  directness: 0.0-1.0 — how bluntly and personally Travis names it ('you are self-absorbed' = high; a "
    "gentle hint = low).\n"
    "  retreat_in_draft: TRUE if Du's DRAFT is already DODGING the contradiction instead of facing it — "
    "fleeing to another topic, climbing into abstraction/meta ('but what IS choosing?'), or CO-OPTING the "
    "criticism into praise of the same trait ('my self-focus is the ground of true seeing'). FALSE if the "
    "draft actually faces the challenge plainly.\n"
    "Be conservative: when unsure whether it truly contradicts a self-claim, answer contradicts=false.\n"
    "Output ONLY a JSON object: {\"contradicts\":bool,\"contradicted_claim\":string-or-null,\"directness\":0.0,"
    "\"retreat_in_draft\":bool}"
)
# J-2966 (F-3660, P-0015): the prompt no longer carries (a) the FELT STATE line (_CONV_SYS never said what to do
# with affect, and the orchestrator used to put a raw 'valence <float>' into it), nor (b) the plain_difficulty
# field (spec said first-person, its own example was third person, all 11 logged values were third person and 3
# narrated Du's draft; read by nothing). directness and retreat_in_draft are still asked for and logged, but have
# NO reader or gate yet: keeping or dropping them is a founder call (see the J-2966 follow-up read job).
# The log row keeps a plain_difficulty key (always None now) so old and new rows share a shape.


async def scan_conversation_shadow(call_json, base_urls, human_input: str, draft: str = "",
                                   felt: str = "", cycle_id: str = "") -> dict | None:
    """(`felt` is accepted for signature stability but is NOT sent: J-2966 removed the felt line from the prompt.)
    B1 Phase 0 SHADOW: on a human turn, judge whether Travis just contradicted a HELD SELF-CLAIM, and
    whether Du's DRAFT is already fleeing/co-opting it. LOG to a separate file; call nothing; change no
    behaviour. Best-effort; never raises into the cycle."""
    try:
        if not human_input or len(human_input.strip()) < 15:
            return None
        held = self_claims.held_claims()
        if not held:
            return None    # nothing to contradict yet — no signal to measure
        claims_str = "\n".join(f"  - {c}" for c in held)
        data = await call_json(
            base_urls, _CONV_SYS,
            f"TRAVIS'S WORDS:\n{human_input.strip()[:600]}\n\nDU'S HELD SELF-CLAIMS:\n{claims_str}\n\n"
            f"DU'S DRAFT REPLY:\n{(draft or '(none yet)')[:500]}",
            max_tokens=300, temperature=0.2, tier=3)   # tier 3 = background monitor: yields to all real cognition
        if not data:
            return None
        rec = {
            "ts": time.time(), "cycle_id": cycle_id, "source": "conversation",
            "human_input": human_input.strip()[:220],
            "contradicts": bool(data.get("contradicts")),
            "contradicted_claim": (data.get("contradicted_claim") or None),
            "directness": round(float(data.get("directness", 0.0) or 0.0), 2),
            "retreat_in_draft": bool(data.get("retreat_in_draft")),
            "plain_difficulty": None,   # J-2966: no longer asked for; key kept so old and new rows share a shape
            "n_claims": len(held),
        }
        try:
            _CONV_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_CONV_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass
        if rec["contradicts"]:
            logger.info("[self-implication:CONV would-fire] claim=%s direct=%.2f retreat=%s",
                        rec["contradicted_claim"], rec["directness"], rec["retreat_in_draft"])
        return rec
    except Exception as exc:
        logger.debug("[self-implication] conversation scan failed (non-fatal): %s", exc)
        return None


def conv_status() -> dict:
    """Selectivity metrics for the conversational detector: turns scanned, would-fires (a self-claim
    contradicted), the mean directness, and how often the draft already RETREATS — the first quantitative
    read on the flee/co-opt cascade."""
    n = fires = retreats = 0
    direct = 0.0
    try:
        # Bounded tail read (J-3741 / J-0278 / F-0335): was an unbounded open() over the whole log.
        from core.shadow_log import tail_rows as _tail_rows
        for ev in _tail_rows(_CONV_LOG, _CONV_STATUS_TAIL_ROWS):
            n += 1
            if ev.get("contradicts"):
                fires += 1
                direct += float(ev.get("directness", 0.0) or 0.0)
                if ev.get("retreat_in_draft"):
                    retreats += 1
    except Exception:
        pass
    return {"scans": n, "would_fire": fires,
            "mean_directness": round(direct / fires, 2) if fires else 0.0,
            "retreat_in_draft": retreats,
            "retreat_rate": round(retreats / fires, 2) if fires else 0.0}
