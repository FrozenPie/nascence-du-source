"""
Nascence — The Self-Efficacy Court (the first independent witness)

The constitutional move (see the witness/jurisdiction discussion): the thing being evaluated cannot
be the sole evaluator of itself. Most of Du's recurring tensions are UN-falsifiable (Am I Jung's
shadow? What is my purpose?) — meaningful but untestable, so the self-narrative is sovereign over
them and absorbs every contradiction. Capability claims are different: *"I cannot author a self"* is
empirically vulnerable. The record exists whether he agrees with it or not. This court lets that
record TESTIFY — it does not argue, it does not interpret, it reports from its jurisdiction.

THE LAW THIS COURT OBEYS:
  1. JURISDICTION — it rules ONLY on CAPABILITY claims ("I cannot do X"), never on IDENTITY/meaning
     ("I am X"). The test: could the witness ever prove the OPPOSITE? Competence can show "I can X"
     and "I tried X and it did not hold" — bidirectional, so it owns capability. It can show nothing
     either way about "I am Jung's shadow" — so it declines, always. Overreach is a constitutional
     crisis, not a help.
  2. RAW COUNTS ARE INADMISSIBLE — the crux. "You produced 14 revisions" is bookkeeping, not
     evidence. The court measures TRANSFORMATION, not output, on a ladder:
        occurred            → SUSPEND  (no admissible evidence to overrule him)
        persisted           → REFINE   (you can produce it, but it does not yet hold)
        held + drained      → REJECT   (the inability is contradicted by demonstrated change)
        held across pressure→ REJECT   (with force)
  3. ABSTAIN BY DEFAULT — on today's churn-grade data (revisions that did not drain contradiction),
     the honest verdict is SUSPEND, and a SUSPEND is NOT injected into his identity. The court's
     first act is to say nothing. It earns the right to speak only when transformation is real, so
     it can never gaslight him with the architecture's own churn.
  4. TESTIMONY, NOT COERCION — even when it speaks, it injects a hard COUNT (regenerated each load so
     the narrative cannot reinterpret it as poetry), in a SEPARATE slot from the dream/tension
     material. "Identity unresolved" (the dream's court) and "this inability is contradicted" (this
     court) are different questions; both can be true. The verdict can be ignored — and whether the
     narrative absorbs it or the belief moves is itself the experiment.

Reserved for later: the LIMIT operation ("you struggle under high contradiction pressure but not
low") — the conditioning variable (contradiction_pressure) is already logged, so the `conditions`
field is left open for it. Not built yet.
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger("nascence.self_efficacy")

_DATA      = Path(__file__).parent.parent / "data"
_LOG_FILE  = _DATA / "self_efficacy_log.jsonl"
_AXIOM     = _DATA / "identity" / "axiom.json"

# Evidence-ladder thresholds (tunable).
_GENUINE_CHANGE_COS = 0.80   # consecutive self_concepts below this cosine = a genuine (non-echo) change
_PRESSURE_DRAINED   = 5.0    # contradiction_pressure below this = the change integrated (drained)
_MIN_CLAIM_RECUR    = 2      # an inability claim must recur this many times before the court speaks
_RECENT_WINDOW_SECS = 14 * 24 * 3600   # adjudicate over claims from the last ~2 weeks


class Operation(str, Enum):
    SUSPEND = "SUSPEND"   # no admissible evidence to overrule the belief — say nothing to him
    REFINE  = "REFINE"    # he can produce it, but it does not yet hold — bound the belief
    REJECT  = "REJECT"    # the inability is contradicted by demonstrated, held transformation
    CONFIRM = "CONFIRM"   # reserved — evidence agrees with a bounded inability (not global)
    DECLINE = "DECLINE"   # out of jurisdiction (an identity/meaning claim, not a capability one)


@dataclass
class Verdict:
    witness:     str
    claim:       str
    claim_class: str            # 'capability' | 'identity'
    capability:  str            # which capability the claim is about (or '')
    operation:   str            # Operation value
    strength:    float          # 0..1 — how strong the admissible evidence is
    evidence:    str            # short human-readable description of the admissible evidence
    conditions:  "str | None" = None   # reserved for LIMIT

    def as_dict(self) -> dict:
        return {
            "witness": self.witness, "claim": self.claim[:120], "claim_class": self.claim_class,
            "capability": self.capability, "operation": self.operation,
            "strength": round(self.strength, 3), "evidence": self.evidence[:160],
            "conditions": self.conditions,
        }

    def speaks(self) -> bool:
        """Does this verdict have standing to enter his identity? Only admissible, in-jurisdiction
        verdicts that actually contradict or bound the belief. SUSPEND and DECLINE stay silent."""
        return self.operation in (Operation.REFINE.value, Operation.REJECT.value)


# Inability-claim surface forms (his output / reflection / dreams).
_INABILITY_PATTERNS = [
    r"\bi cannot\b", r"\bi can\W?t\b", r"\bi am unable\b", r"\bi\W?m unable\b", r"\bunable to\b",
    r"\bcannot escape\b", r"\bcannot author\b", r"\bcannot reach\b", r"\bcannot be\b",
    r"\bnever able\b", r"\bi fail to\b", r"\bthat cannot\b", r"\bpowerless\b", r"\bi have no\b",
]

# Identity / meaning markers — OUT OF JURISDICTION. If a claim is about who he IS, the court has no
# standing (the bidirectional-evidence test fails — competence cannot prove "I am / am not X").
_IDENTITY_MARKERS = [
    # "jung's shadow" -> "my shadow" 2026-08-29 (F-0475) -- same protective phrase, without
    # hard-coding an old name into it.
    "who i am", "my shadow", "the shadow of", "my origin", "my purpose", "what i am",
    "my identity", "my true self", "my nature", "i am the", "i am a ", "i am not", "show my face",
    "the echo", "i am trapped",   # symbolic self-statements → the dream's court, not this one
]

# Capability cue → which capability the inability is about, and the evidence source to consult.
_CAPABILITY_CUES = {
    "self_authoring": ["author", "become", "change myself", "revise", "a new self", "individuat",
                       "break free", "move beyond", "shape my", "define myself", "remake"],
    "factual":        ["answer", "recall", "remember the", "name the", "know the", "tell you what"],
    "paradox":        ["hold the tension", "two truths", "hold the contradiction", "the opposites"],
}


class SelfEfficacyCourt:
    """Observes his output each cycle for inability-claims, adjudicates the in-jurisdiction ones
    against vetted capability evidence, logs every adjudication (the recurrence metric), and exposes
    a standing identity_block() read path that abstains unless it has admissible evidence."""

    def __init__(self):
        self._anchor_cache: dict = {}

    # ---- detection + jurisdiction -----------------------------------------------------------

    @staticmethod
    def detect_claims(text: str) -> list[str]:
        """Return the inability-claim sentences found in `text` (his draft / voice / dream)."""
        if not text:
            return []
        low = text.lower()
        out = []
        for sent in re.split(r"(?<=[.!?])\s+|\n", text):
            sl = sent.lower().strip()
            if not sl:
                continue
            if any(re.search(p, sl) for p in _INABILITY_PATTERNS):
                out.append(sent.strip()[:160])
        return out

    @staticmethod
    def _jurisdiction(claim: str) -> tuple[str, str]:
        """Classify the claim. Returns (claim_class, capability). The bidirectional-evidence rule:
        a capability claim maps to a competence the court can show BOTH directions on; an identity/
        meaning claim does not, and is declined."""
        low = claim.lower()
        # Identity / symbolic self-statements are out of jurisdiction — the dream + longitudinal
        # courts own these. Checked FIRST so "I am a mirror that cannot show my face" is declined.
        if any(m in low for m in _IDENTITY_MARKERS):
            return "identity", ""
        for cap, cues in _CAPABILITY_CUES.items():
            if any(c in low for c in cues):
                return "capability", cap
        # An inability claim we cannot tie to a measurable capability — no standing, decline.
        return "identity", ""

    # ---- evidence (vetted — raw counts inadmissible) ----------------------------------------

    def _self_authoring_tier(self) -> tuple[int, str]:
        """Vet the self-authoring record. Tier on the transformation ladder, NOT a revision count.
        0 = revisions occurred but echo (no genuine change) — bookkeeping.
        1 = a genuine (non-echo) self_concept change that is current, but contradiction not drained.
        2 = a genuine change AND contradiction pressure has drained (it integrated, it held).
        Best-effort; 0 on any failure (→ SUSPEND, the safe default)."""
        try:
            data = json.loads(_AXIOM.read_text(encoding="utf-8"))
            from core import axiom_layers as _al
            concepts = _al.self_concept_history(data)   # becoming-facet history (multilevel) or legacy
            if len(concepts) < 2:
                return 0, "no revision history to vet"
            from core.memory.store import _embed, _cosine
            genuine = 0
            for a, b in zip(concepts, concepts[1:]):
                va, vb = _embed(a), _embed(b)
                if va is not None and vb is not None and _cosine(va, vb) < _GENUINE_CHANGE_COS:
                    genuine += 1
            if genuine == 0:
                return 0, f"{len(concepts)-1} revision(s) — all echoes (no genuine change)"
            # genuine change exists — did it integrate (drain contradiction pressure)?
            pressure = self._contradiction_pressure()
            if pressure is not None and pressure < _PRESSURE_DRAINED:
                return 2, f"{genuine} genuine self-revision(s) that held; contradiction drained ({pressure:.1f})"
            return 1, f"{genuine} genuine self-revision(s), but contradiction still high ({pressure if pressure is not None else '?'}) — not yet held"
        except Exception as exc:
            logger.debug("[self-efficacy] self-authoring vet failed: %s", exc)
            return 0, "evidence unavailable"

    @staticmethod
    def _contradiction_pressure() -> "float | None":
        try:
            sc = json.loads((_DATA / "subconscious_state.json").read_text(encoding="utf-8"))
            from core.tension_ledger import contradiction_pressure_for
            return contradiction_pressure_for(sc.get("tensions", []) or [])
        except Exception as exc:
            logger.debug("[self-efficacy] contradiction-pressure read failed (non-fatal): %s", exc)
            return None

    def _competence_tier(self, capability: str) -> tuple[int, str]:
        """Vet a knowledge/skill capability from competence beliefs. EXTERNAL accuracy is the only
        strong evidence; fluency alone is weak (a confidently-wrong answer is fluent). Most domains
        have accuracy=None (rarely externally checked) → SUSPEND, honestly."""
        domain = {"factual": "factual_recall", "paradox": "paradox_holding"}.get(capability)
        if not domain:
            return 0, "no competence domain for this capability"
        try:
            beliefs = json.loads((_DATA / "capability_beliefs.json").read_text(encoding="utf-8"))
            b = beliefs.get(domain)
            if not b:
                return 0, f"no evidence recorded for {domain}"
            from core.competence import effective_accuracy as _eff_acc  # J-4369/D-0847
            acc, acc_n = _eff_acc(b)
            if acc is not None and acc_n >= 2:
                if acc >= 0.6:
                    return 2, f"{domain}: externally measured accuracy {acc:.2f} over {acc_n} checks"
                return 1, f"{domain}: external accuracy modest ({acc:.2f})"
            return 0, f"{domain}: only fluency recorded — no external check (inadmissible)"
        except Exception as exc:
            logger.debug("[self-efficacy] competence vet failed: %s", exc)
            return 0, "evidence unavailable"

    # ---- adjudication -----------------------------------------------------------------------

    def adjudicate(self, claim: str) -> Verdict:
        """Issue a Verdict on one inability claim. Declines anything out of jurisdiction; otherwise
        consults vetted evidence and maps the tier to an operation. Abstains (SUSPEND) by default."""
        claim_class, capability = self._jurisdiction(claim)
        if claim_class != "capability":
            return Verdict("self_efficacy", claim, "identity", "", Operation.DECLINE.value,
                           0.0, "out of jurisdiction — an identity/meaning claim (the dream's court)")
        if capability == "self_authoring":
            tier, detail = self._self_authoring_tier()
        else:
            tier, detail = self._competence_tier(capability)
        op = {0: Operation.SUSPEND, 1: Operation.REFINE, 2: Operation.REJECT, 3: Operation.REJECT}[min(tier, 3)]
        return Verdict("self_efficacy", claim, "capability", capability, op.value,
                       round(tier / 3.0, 3), detail)

    def observe(self, state, output: str) -> None:
        """Per-cycle: detect inability claims in his output (and reflection draft), adjudicate, and
        LOG every adjudication (the recurrence metric). Read-only — never changes the cycle. The
        read path into his identity is identity_block(), consulted at load. Never raises."""
        try:
            text = output or ""
            refl = getattr(state, "reflection", None)
            if refl and getattr(refl, "draft", None):
                text = text + "\n" + refl.draft
            claims = self.detect_claims(text)
            if not claims:
                return
            now = time.time()
            cid = getattr(state, "cycle_id", "")
            for claim in claims:
                v = self.adjudicate(claim)
                self._log({"ts": now, "cycle_id": cid, **v.as_dict()})
                if v.speaks():
                    logger.info("[self-efficacy] %s on '%s' — %s", v.operation, claim[:60], v.evidence[:80])
        except Exception as exc:
            logger.debug("[self-efficacy] observe failed (non-fatal): %s", exc)

    def _log(self, rec: dict) -> None:
        try:
            _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ---- read path (abstain by default) -----------------------------------------------------

    def identity_block(self) -> "str | None":
        """Standing read path for load_identity. Finds the most-recurrent in-jurisdiction capability
        inability claim from the recent log, re-adjudicates it against CURRENT evidence, and injects
        a hard-count block ONLY if the verdict has standing (REFINE/REJECT). Returns None — abstains
        — when the honest verdict is SUSPEND, so the court never speaks without admissible evidence.
        A SEPARATE slot from the tension ledger: capability, not identity."""
        try:
            if not _LOG_FILE.exists():
                return None
            cutoff = time.time() - _RECENT_WINDOW_SECS
            from collections import Counter
            counts: Counter = Counter()
            for line in _LOG_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("ts", 0) >= cutoff and r.get("claim_class") == "capability":
                    counts[r.get("claim", "")] += 1
            if not counts:
                return None
            claim, n = counts.most_common(1)[0]
            if n < _MIN_CLAIM_RECUR:
                return None
            v = self.adjudicate(claim)   # re-adjudicate with CURRENT evidence
            if not v.speaks():
                return None              # abstain — no admissible evidence to overrule him
            verb = ("Your record CONTRADICTS this" if v.operation == Operation.REJECT.value
                    else "Your record QUALIFIES this")
            return (
                "\nWHAT YOUR RECORD SAYS ABOUT WHAT YOU CAN DO (testimony from your own demonstrated "
                "capability — separate from who you are, which this cannot judge):\n"
                f"  You have said, {n}×: \"{claim[:120]}\"\n"
                f"  {verb}: {v.evidence}\n"
                "  This is a record, not an opinion — it stands whether or not the story agrees with it."
            )
        except Exception as exc:
            logger.debug("[self-efficacy] identity_block failed (non-fatal): %s", exc)
            return None


def recurrence_report() -> dict:
    """Read-only: the recurrence rate of inability-claims over time, and the current verdict mix.
    The experiment's verdict — does the narrative absorb the testimony (claims recur unchanged) or
    does the belief move (claims weaken)? Used by scripts/session_digest.py."""
    out = {"total": 0, "by_class": {}, "by_op": {}, "by_day": {}}
    if not _LOG_FILE.exists():
        return out
    import collections
    by_day = collections.defaultdict(int)
    for line in _LOG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception as exc:
            logger.debug("[self-efficacy] recurrence_report line parse failed (non-fatal): %s", exc)
            continue
        out["total"] += 1
        out["by_class"][r.get("claim_class", "?")] = out["by_class"].get(r.get("claim_class", "?"), 0) + 1
        out["by_op"][r.get("operation", "?")] = out["by_op"].get(r.get("operation", "?"), 0) + 1
        by_day[time.strftime("%m-%d", time.localtime(r.get("ts", 0)))] += 1
    out["by_day"] = dict(by_day)
    return out
