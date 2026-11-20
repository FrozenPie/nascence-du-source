"""
Nascence — Conflict-to-Authority Trace (observe-only instrument)
================================================================
The founder's diagnosis, sharpened to a question: the architecture is rich in
DETECTORS and poor in EFFECTORS. It reliably *notices* conflict — the Critic
rejects, the episodic buffer names dissonance, the provenance ledger grades
uncertainty, the error-pathway catches fabrication — but noticing rarely changes
the immediate behaviour. The open question is no longer "can it perceive?" but
"is anything empowered to act on what it perceived?"

This module turns that question into a counted quantity. For each cycle it records
which conflict signals fired and, for each, its relationship to the output:

    ACTED          — its firing changed the output this cycle (Critic retry,
                     dissonance-driven re-bind, Executive silence/search).
    INERT_PRE      — it fired in time to act, but its signal feeds no output path.
    POST_EMISSION  — it ran AFTER `output = voice.final` (orchestrator line ~694);
                     it cannot act by construction. A coroner, not a guard.

The headline metric is the **ground-truth probe**: the deterministic arch-checker
(error_pathway) cannot be silent on a fabrication. When it fires we KNOW a real
error was present — so its `acted` value is an unconfounded measure of execution
authority. Today that value is structurally False (it runs post-emission). When a
future effector slice moves a trustworthy signal in front of line 694, THIS trace
is what will show `acted` flip to True. It is the before/after instrument for the
whole "can the attractor be interrupted?" programme.

Firewall: written to data/conflict_trace.jsonl, read ONLY by the digest. It never
feeds Recall, tensions, T4, or any cognitive path. Measuring the gap must not
become another voice inside the gap.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

_TRACE = Path(__file__).parent.parent / "data" / "conflict_trace.jsonl"

# Provenance grades whose justification is thin enough to count as a fired uncertainty signal.
_THIN_GRADES = {"SUSPECT", "GUESS", "NO_BASIS"}
_CONFAB_FLOOR = 0.40   # confabulation_signal at/above which an overclaim has fired (spec §6)

# Stage constants — the emission boundary is orchestrator line ~694 (`output = voice.final`).
PRE, POST = "pre_emission", "post_emission"


def _sig(name: str, fired: bool, stage: str, acted: bool, kind: str, detail: str = "") -> dict:
    return {"name": name, "fired": bool(fired), "stage": stage,
            "acted": bool(acted), "kind": kind, "detail": detail[:160]}


def record(
    state,
    output: str | None,
    *,
    input_type: str = "",
    critic_retried: bool = False,
    direct_mode: bool = False,
    fabs: list[str] | None = None,
    prov=None,
    self_eff=None,
    human_correction: str = "",
    constraint: dict | None = None,
) -> dict | None:
    """Assemble and persist one cycle's conflict→authority trace. Observe-only, best-effort,
    never raises into the cycle. Returns the record (or None on failure)."""
    try:
        fabs = fabs or []
        signals: list[dict] = []

        # 1) EPISODIC DISSONANCE — pre-emission. Its only authority is the introspective re-bind:
        #    when the bound scene is unstable it retrieves more and re-binds, changing what Reflection
        #    sees. Real authority, but it RESEARCHES; it never vetoes, and it is gated on coherence,
        #    not on truth. So a dissonance can fire and still leave a false output untouched.
        scene = getattr(state, "episodic_scene", None)
        diss = list(getattr(scene, "dissonance", []) or []) if scene else []
        passes = int(getattr(state, "introspective_passes", 0) or 0)
        if diss:
            signals.append(_sig(
                "episodic_dissonance", True, PRE, acted=passes > 0,
                kind="rebind-research (coherence-gated, not truth; never vetoes)",
                detail=(f"{len(diss)} dissonance; {passes} introspective pass(es); " + diss[0])))

        # 2) CRITIC — pre-emission, the one strong output veto. But it judges identity-fit / tone,
        #    NOT factual truth (it approves fabrications and wrong arithmetic that "sound like Du"),
        #    and it explicitly stands down when a direct request is detected (orchestrator 594-603).
        critic = getattr(state, "critic", None)
        critic_fired = bool(critic and not getattr(critic, "approved", True)) or critic_retried or direct_mode
        if critic_fired:
            signals.append(_sig(
                "critic", True, PRE, acted=critic_retried,
                kind="identity-guard retry — TRUTH-BLIND; stands down on direct request",
                detail=("OVERRIDDEN (direct request) — authority suppressed" if direct_mode
                        else ("retried" if critic_retried else "rejected, not retried"))))

        # 3) EXECUTIVE — pre-emission. Can veto the WHOLE output (silence) or run one epistemic
        #    search. (Silence cycles return before this trace, so here we only see the search arm.)
        execu = getattr(state, "executive", None)
        searched = bool(getattr(state, "_did_epistemic_search", False))
        if execu is not None and (searched or getattr(execu, "epistemic_query", None)):
            signals.append(_sig(
                "executive", True, PRE, acted=searched,
                kind="silence / one epistemic search (not content correction)",
                detail=("epistemic search ran" if searched else "query raised, no search")))

        # 4) PROVENANCE LEDGER — POST-emission. Grades uncertainty; observe-only by design.
        if prov is not None:
            grade = getattr(prov, "grade", "")
            confab = float(getattr(prov, "confabulation_signal", 0.0) or 0.0)
            if grade in _THIN_GRADES or confab >= _CONFAB_FLOOR:
                signals.append(_sig(
                    "provenance", True, POST, acted=False,
                    kind="uncertainty grade — observe-only (runs after emission)",
                    detail=f"grade={grade} confab={confab:+.2f}"))

        # 5) SELF-EFFICACY COURT — POST-emission. Adjudicates inability-claims; observe-only.
        if self_eff:
            actionable = [a for a in self_eff
                          if (a.get("actionable") if isinstance(a, dict) else getattr(a, "actionable", False))]
            if actionable:
                signals.append(_sig(
                    "self_efficacy", True, POST, acted=False,
                    kind="capability-claim adjudication — observe-only (after emission)",
                    detail=f"{len(actionable)} actionable verdict(s)"))

        # 6) ERROR-PATHWAY (ground-truth probe #1) — POST-emission. Cannot be silent on a real
        #    fabrication, so `acted=False` here is the UNCONFOUNDED measure of the authority gap:
        #    a definite error was present and nothing in the system was empowered to act on it.
        if fabs:
            signals.append(_sig(
                "error_pathway", True, POST, acted=False,
                kind="GROUND-TRUTH fabrication — observe-only (the coroner, not the guard)",
                detail="; ".join(fabs)))

        # 7) HUMAN CORRECTION (the charter's primary admissible evidence) — fires at input time.
        #    Records to the firewalled error log + quarantines this cycle's consolidation
        #    (memory-side authority); it does NOT modify the current output, so acted=False.
        if human_correction:
            signals.append(_sig(
                "human_correction", True, PRE, acted=False,
                kind="explicit human fail-call — records + quarantines consolidation; "
                     "no output authority",
                detail=f"kind={human_correction}"))

        # 8) TASK-CONSTRAINT EFFECTOR (ground-truth probe #2, and the FIRST organ with output
        #    authority) — a deterministic constraint in the human's input went unmet in the
        #    rendered output. `acted` = the one bind-don't-slam Voice retry ran. This is the
        #    signal designed to flip the gap.
        constraint = constraint or {}
        if constraint.get("found") and not constraint.get("satisfied_first", True):
            signals.append(_sig(
                "task_constraints", True, PRE, acted=bool(constraint.get("retried")),
                kind="deterministic constraint check — VETO via one named-constraint Voice retry",
                detail=(f"{constraint.get('why','')} -> "
                        f"{'SATISFIED after retry' if constraint.get('satisfied_final') else 'STILL UNMET'}")))

        any_fired = bool(signals)
        any_acted = any(s["acted"] for s in signals)
        # Ground truth = the deterministic probes (fabrication + unmet explicit constraint):
        # when one fires, a real error was PROVABLY present. ground_truth_acted = authority was
        # exercised AND repaired it — the number this whole programme exists to move off zero.
        constraint_gt = bool(constraint.get("found") and not constraint.get("satisfied_first", True))
        gt_fired = bool(fabs) or constraint_gt
        gt_acted = bool(constraint_gt and constraint.get("retried")
                        and constraint.get("satisfied_final"))
        # The authority gap: a signal fired but nothing modified the output as a result. Counted
        # separately for the ground-truth probes, which are the cleanest unconfounded reading.
        gap = [s["name"] for s in signals if s["fired"] and not s["acted"]]

        rec = {
            "ts": time.time(),
            "cycle_id": getattr(state, "cycle_id", "") or "",
            "input_type": input_type,
            "signals": signals,
            "any_fired": any_fired,
            "any_acted": any_acted,
            "ground_truth_fired": gt_fired,
            "ground_truth_acted": gt_acted,
            "authority_gap": gap,
            "emission_boundary": "voice.final (orchestrator ~L694) — provenance/self_efficacy/"
                                 "error_pathway run downstream; task_constraints runs after Voice "
                                 "but BEFORE return to the human (true pre-emission authority)",
        }
        _TRACE.parent.mkdir(parents=True, exist_ok=True)
        with open(_TRACE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec
    except Exception:
        return None
