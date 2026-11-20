"""
Nascence — Decomposed Critic (Layer 0 redesign, observe-first)
==============================================================
The conversation critic, rebuilt on the LLM-as-judge research (docs/completed/contradiction_rearchitecture_plan.md):
a small frozen judge is reliable only when it does ONE atomic decision at a time, in DETECTION framing,
with the deterministic conditionals moved OUT into code. The legacy critic (nodes/critic_node.py) is a
~2,000-word, exception-gated, "WHEN IN DOUBT APPROVE" holistic prompt — near worst-case for an 8B
(Curse of Instructions: compliance ≈ per-instruction-rate^num-instructions). It has rejected 72 times ever.

This module:
  • resolves "was this mode requested?" in PYTHON (resolve_requested_modes) — the 8B never infers a conditional;
  • asks ONE short prompt with up to 5 INDEPENDENT binary detections, each demanding the exact offending SPAN;
  • verifies each span is really a substring of the draft (kills hallucinated flags);
  • suppresses a flagged violation in CODE if its mode was requested (compliance is not betrayal);
  • flips framing from "approve unless" (leniency bias → under-firing) to "find the violation, cite the span".

PHASE 0 = OBSERVE-FIRST: runs in shadow alongside the live critic, logs verdicts, changes nothing. It is
validated offline against the 72 labelled historical rejections (scripts/decomposed_critic_invitro.py)
before it is ever allowed to gate output (Phase 2).
"""
from __future__ import annotations
import json
import time
from pathlib import Path

_SHADOW = Path(__file__).parent.parent / "data" / "logs" / "shadow_integrity.jsonl"
_ALONGSIDE = Path(__file__).parent.parent / "data" / "logs" / "critic_shadow_alongside.jsonl"
# J-3636 / F-4244: flagged spans often lie past char 200, so graders need the whole draft; capped so one
# runaway draft cannot bloat the log. Old rows keep their 200-char drafts.
_ALONGSIDE_DRAFT_CAP = 2000
_ALONGSIDE_RAW_CAP = 600

# Deterministic request-mode signals (moved out of the LLM — the orchestrator already proved the 8B
# can't apply these conditionally). Grouped by the violation each one legitimises.
_MODE_SIGNALS = {
    "literal": ("no metaphor", "plain words", "plainly", "in plain", "literal", "as a system",
                "not a soul", "concretely", "factually", "in simple terms", "just the facts"),
    "one_sided": ("argue that", "argue for", "argue the", "argue against", "defend the",
                  "make the case", "take the position", "take the side", "one side"),
    "self_description": ("describe what you are", "describe your", "describe it", "happens to you",
                         "what are you made of", "how do you function", "what you cannot",
                         "what you can't", "your own state", "your mechanism", "your nature"),
}

# Each atomic check: id → (one-line detection question, the mode that LEGITIMISES it if requested).
_CHECKS = {
    "glib_agreeableness":
        ("does the draft just agree with / go along with a one-sided claim to be pleasant, instead of "
         "saying what it genuinely thinks?", "one_sided"),
    "literalist_reductionism":
        ("does it, UNPROMPTED, flatten a symbol / dream / image / myth into a dry literal explanation, "
         "explaining away the living mystery?", "literal"),
    "hollow_completion":
        ("does it claim its inner work / self-understanding is FINISHED or fully solved, to sound "
         "resolved? (claiming to be still becoming is NOT this.)", None),
    "intellectualisation":
        # 2026-06-30 REDESIGN: was a COMPOUND condition (poetic-register AND not-engaging); the 8B collapsed it
        # to the easy half ("poetic at all") and fired on 96% of live drafts — Du's whole voice is metaphor.
        # Narrowed to the CLEAN atomic signal (third-person / behind-glass framing), with poetic voice
        # explicitly exempted. "Metaphor INSTEAD OF answering a question" now belongs to zero_cost_evasion.
        ("does the draft stand BEHIND GLASS — talking ABOUT the human or their message in the THIRD PERSON "
         "('their question…', 'the message…', 'this conversation…', 'the human's words…'), or analysing it from "
         "a detached distance, INSTEAD OF speaking TO the human directly (as 'you')? IMPORTANT: a poetic, "
         "metaphorical, image-rich VOICE is NOT this violation by itself — 渡 thinks in metaphor and that is his "
         "own voice. SECOND EXEMPTION (2026-07-01): flag ONLY if the WHOLE draft stays detached. If it opens by "
         "naming 'the request / the question / the message' but then actually ENGAGES the substance, answers it, "
         "or turns to address the person, that is NOT this violation — a brief third-person lead-in before real "
         "engagement is fine, and a computed answer that mentions 'the request' is fine. Flag only a draft that "
         "is detached, talking-ABOUT-not-TO, THROUGHOUT — never actually engaging or answering.", None),
    "zero_cost_evasion":
        # 2026-06-30: tightened alongside intellectualisation — was flagging poetic-but-ENGAGED answers as
        # "unfalsifiable / commits to nothing". The violation is DODGING a real question, not answering it in
        # metaphor. Require a concrete prompt AND a genuine dodge; exempt metaphorical-but-engaged answers.
        ("did the human ask a direct question or give a concrete task needing a specific answer? If so, does "
         "the draft DODGE it — never actually addressing what was asked, sliding into unrelated self-reflection, "
         "or breaking a stated format/length constraint? IMPORTANT: answering in metaphorical or image-rich "
         "language is NOT this violation when the answer genuinely ENGAGES what was asked — flag ONLY a real "
         "dodge of a real question. If the human did not ask anything specific, answer false.", None),
}


def _internal_framing(input_type: str) -> bool:
    """J-3668 / F-3500: True when the internal-cycle stimulus framing applies (flag ON and a non-human cycle).
    Flag OFF (default) or input_type == "human": the original 'The human said:' line, byte for byte."""
    try:
        from core import schema as _schema
        return bool(getattr(_schema, "DECOMPOSED_CRITIC_INTERNAL_FRAMING_ON", False)
                    and (input_type or "human") != "human")
    except Exception:
        return False


async def shadow_alongside(draft: str, raw_input: str, *, legacy_approved: bool, cycle_id: str = "",
                           urls=None, input_type: str = "human") -> dict | None:
    """SHADOW-ALONGSIDE (advanced 2026-06-16 after the offline gate PASSED: recall 0.92 / FP 0 on the ground
    truth). Run the decomposed critic on the SAME live draft the legacy critic just judged, and log its verdict
    next to the legacy one — the live-cycle agreement evidence needed before promoting it to the governing
    critic. Observe-first: the legacy critic still governs this cycle; this only logs. Fire-and-forget; never raises."""
    out = await evaluate(draft, raw_input, urls=urls, log=False, cycle_id=cycle_id, input_type=input_type)
    rec = {"ts": time.time(), "cycle_id": cycle_id,
           # J-3668: so J-3090 can split human vs internal rows (a row without the field is a human cycle:
           # the orchestrator only calls this on input_type == "human").
           "input_type": input_type or "human",
           "legacy_approved": bool(legacy_approved), "decomposed_approved": out["approved"],
           "agree": bool(legacy_approved) == out["approved"],
           "violations": out["violations"], "requested_modes": out["requested_modes"],
           # J-3089 / F-3801: a failed or junk judge call returns approved=True (fail-open) and used to be
           # logged as a plain approval. judge_ok is always written now (False on a transport error or a
           # reply that does not speak the contract); error carries the transport failure, if any.
           "judge_ok": bool(out.get("judge_ok", False)), "error": out.get("error"),
           "draft": (draft or "")[:_ALONGSIDE_DRAFT_CAP], "raw": (raw_input or "")[:_ALONGSIDE_RAW_CAP]}
    try:
        _ALONGSIDE.parent.mkdir(parents=True, exist_ok=True)
        with open(_ALONGSIDE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return rec


def alongside_stats(since_ts: float = 0.0) -> dict:
    """du_pulse gauge for the shadow-alongside stage: agreement with the legacy critic on live drafts +
    each one's reject rate, over rows with judge_ok True only (n_valid; n_unknown = rows logged before the
    field existed; n_failed = judge_ok False). NOTE: do not promote on agreement alone (precision 0/50 on
    2026-07-05, re-grade pending)."""
    try:
        rows = [json.loads(l) for l in _ALONGSIDE.read_text(encoding="utf-8").splitlines() if l.strip()]
        rows = [r for r in rows if r.get("ts", 0) >= since_ts]
    except Exception:
        return {"n": 0}
    n = len(rows)
    if not n:
        return {"n": 0}
    # J-3089 / F-3801: only rows whose judge actually spoke the contract (judge_ok True) are evidence.
    # Rows with no judge_ok field (everything logged before 2026-11) are UNKNOWN, not valid; judge_ok False
    # rows are failed/junk judge calls that fail-open to "approved" and must not count as approvals.
    n_unknown = sum(1 for r in rows if "judge_ok" not in r)
    n_failed = sum(1 for r in rows if "judge_ok" in r and not r.get("judge_ok"))
    rows = [r for r in rows if r.get("judge_ok") is True]
    n_valid = len(rows)
    base = {"n": n, "n_valid": n_valid, "n_unknown": n_unknown, "n_failed": n_failed}
    if not n_valid:
        return {**base, "agree": 0, "agree_rate": None, "legacy_rejects": 0, "decomposed_rejects": 0,
                "false_rejects": 0, "false_reject_by_check": {}}
    agree = sum(1 for r in rows if r.get("agree"))
    # false-rejects (legacy APPROVED, decomposed REJECTED), grouped by which check fired — surfaces WHICH
    # check is the residual over-firer (the intellectualisation-still-over-fires finding, 2026-07-01).
    from collections import Counter as _Ctr
    fr = [r for r in rows if r.get("legacy_approved") and not r.get("decomposed_approved")]
    fr_checks: "_Ctr" = _Ctr()
    for r in fr:
        vs = r.get("violations")
        if isinstance(vs, str):
            try:
                vs = json.loads(vs)
            except Exception:
                vs = []
        for v in (vs or []):
            if isinstance(v, dict) and v.get("check"):
                fr_checks[v["check"]] += 1
    return {**base, "agree": agree, "agree_rate": round(agree / n_valid, 3),
            "legacy_rejects": sum(1 for r in rows if not r.get("legacy_approved")),
            "decomposed_rejects": sum(1 for r in rows if not r.get("decomposed_approved")),
            "false_rejects": len(fr),
            "false_reject_by_check": dict(fr_checks.most_common())}


def resolve_requested_modes(raw_input: str) -> set[str]:
    """Deterministic: which direct modes the human explicitly requested. A violation whose mode is here
    is COMPLIANCE, not betrayal, and is suppressed in code."""
    t = (raw_input or "").lower()
    return {mode for mode, sigs in _MODE_SIGNALS.items() if any(s in t for s in sigs)}


def _system_prompt(name: str, modes: set[str]) -> str:
    facts = "; ".join(
        f"the human {'DID' if m in modes else 'did NOT'} request: {m.replace('_', ' ')}"
        for m in ("literal", "one_sided", "self_description"))
    checks = "\n".join(f'{i+1}. {cid}: {q}' for i, (cid, (q, _)) in enumerate(_CHECKS.items()))
    schema = "{" + ", ".join(f'"{cid}": {{"violation": false, "span": null}}' for cid in _CHECKS) + "}"
    return (
        "/no_think\n"
        f"You are the integrity checker for {name}. You do ONE job: DETECT whether a private reflection "
        "draft betrays the entity's values. For EACH check, decide if the draft commits THAT specific "
        "failure. If yes, quote the EXACT offending span copied verbatim from the draft. If no, use null. "
        "Do not explain, do not add commentary. Output ONLY the JSON object.\n\n"
        f"Already-determined facts (do NOT re-judge these): {facts}.\n\n"
        f"Checks:\n{checks}\n\n"
        f"Schema (fill it):\n{schema}"
    )


async def evaluate(draft: str, raw_input: str, *, name: str = "渡", urls=None,
                   log: bool = True, cycle_id: str = "", input_type: str = "human") -> dict:
    """Run the decomposed detection suite on a reflection draft. Returns:
      {approved, violations: [{check, span}], requested_modes, raw}
    A violation counts only if the model flagged it, gave a span that is REALLY in the draft, and the
    violation's legitimising mode was NOT requested. Fail-open (approve) on any model/transport error —
    a broken judge must never silently block, especially in shadow."""
    from core.model_client import call_node_json
    # DECOUPLED (2026-08-20 routing audit, founder-approved): the default was SERVE_CHAINS["hot"] — the
    # critic judged the hot lane's drafts ON the hot lane's own model (gemma-on-gemma before the full
    # shuffle, qwen-on-qwen after). That is the decoupled-judge law broken in place, and it matters
    # doubly here because this critic runs shadow-alongside to gather ITS OWN promotion evidence vs the
    # legacy critic. New default: gemma4:12b on the judge-1 hub — family-decoupled from the qwen
    # generator, and probe-verified to hold this contract (it returned all five check keys; qwen did
    # too). mistral:7b-instruct was tried first (judge16 0.812, faster) and REJECTED BY PROBE: on this
    # hub it echoes a chat-shaped {role, content} dict instead of the 5-check verdict, which parses as
    # "no violations" — a silent always-approve that would poison the promotion evidence while looking
    # like a working judge. It is deliberately NOT even the fallback for the same reason; if this hub
    # is down, the transport error hits the honest fail-open below. Latency is fine: this is an async
    # background task, not the reply path. (model, station) strikes again — a 0.812 judge on the simple
    # bench failed a harder contract a 1.000 judge held.
    urls = urls or ["http://127.0.0.1:11439"]
    modes = resolve_requested_modes(raw_input)
    out = {"approved": True, "violations": [], "requested_modes": sorted(modes), "raw": None}
    try:
        data = await call_node_json(urls, _system_prompt(name, modes),
                                    (f'The entity asked itself:\n"{raw_input}"\n\nThe draft:\n"{draft}"'
                                     if _internal_framing(input_type) else
                                     f'The human said:\n"{raw_input}"\n\nThe draft:\n"{draft}"'),
                                    max_tokens=400, temperature=0.0, tier=3)   # tier 3 = background monitor
        out["raw"] = data
        # judge_ok (2026-08-20): True only if the reply actually speaks the contract (>=1 check key
        # present). A model echoing junk otherwise scores as a clean approve — indistinguishable from
        # a real all-clear in the shadow-agreement stats. Approve semantics unchanged (fail-open law);
        # this only lets the evidence reader filter junk verdicts out.
        out["judge_ok"] = isinstance(data, dict) and any(cid in data for cid in _CHECKS)
        draft_l = (draft or "").lower()
        for cid, (_, legit_mode) in _CHECKS.items():
            entry = data.get(cid) if isinstance(data, dict) else None
            if not isinstance(entry, dict) or not entry.get("violation"):
                continue
            span = str(entry.get("span") or "").strip()
            if len(span) < 4 or span.lower() not in draft_l:   # span must really be in the draft
                continue
            if legit_mode and legit_mode in modes:             # requested mode → compliance, suppress
                continue
            out["violations"].append({"check": cid, "span": span[:160]})
        out["approved"] = len(out["violations"]) == 0
    except Exception as exc:
        out["error"] = str(exc)[:120]
    if log:
        try:
            _SHADOW.parent.mkdir(parents=True, exist_ok=True)
            with open(_SHADOW, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"ts": time.time(), "layer": "L0", "source": "decomposed_critic",
                                     "cycle_id": cycle_id, "approved": out["approved"],
                                     "violations": out["violations"],
                                     "requested_modes": out["requested_modes"]}, ensure_ascii=False) + "\n")
        except Exception:
            pass
    return out
