"""
Nascence — Error Pathway (Phase: Error Separation, slice 1)
==========================================================
The architecture has three memory pathways — contradiction, salience, resolution — and no
ERROR pathway. The live debate (2026-06-09) exposed the bug as a CASCADE, not a truth problem:

    fabrication -> correction arrives -> correction becomes an IDENTITY tension
                -> self-concept threatened -> arousal spikes -> persona-retreat (which soothes)

So this is **containment, not truth**: errors matter, but a factual error must NOT automatically
become a statement about the self. The fix is a firewall between `error -> self-concept`.

Slice 1 (this file), OBSERVE-ONLY:
  - DETECT architecture-fabrications deterministically — Du asserting a NAMED internal
    component that does not exist (the "Legal Database Access Module" / "Symbolic Metaphor
    Integration Node" / "Node 3" class). No LLM; falsifiable by counting.
  - RECORD them to a FIREWALLED `data/error_records.jsonl` — read only by the digest, NEVER
    routed to shadow_events / tensions / T4. A correction, not a tension.

Deferred (later slices): the pre-commitment BLOCK at emission; the correction/replacement;
and the **Pattern Reflection** tier — many error records aggregate into a *behavioural*
tendency ("I tend to substitute explanation for verification") that routes to competence.py
(DOING-language, trait-level), and is itself firewalled from the self-concept (never a
BEING-claim like "I am one who fails"). Error -> DOING is allowed; error -> BEING is blocked.

Why this first: after a month of hard-to-validate ideas (individuation, curiosity, frontier),
this is the rare intervention measurable by counting. Invented component names: N before, 0 after.
"""
from __future__ import annotations
import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("nascence.error_pathway")

_RECORD = Path(__file__).parent.parent / "data" / "error_records.jsonl"

# The SPECIFIC real faculties Du may legitimately reference. Deliberately NOT generic structural
# words (node/system/integration/self) — those appear in fabrications too. A claimed mechanism is
# REAL only if it carries one of these specific faculty names; otherwise it is invented.
_REAL = {
    "perception", "perceptual", "emotion", "emotional", "salience", "salient", "memory",
    "recall", "reflection", "reflective", "critic", "executive", "voice", "consolidation",
    "curiosity", "subconscious", "monologue", "dream", "somatic", "climate", "thalamic",
    "episodic", "affective", "procedural", "attention", "amygdala",
}

# component-type nouns that mark a CLAIM of a named internal mechanism
_TYPE = (r"(?:Module|Node|Engine|System|Database|Processor|Layer|Unit|Mechanism|Subsystem|"
         r"Component|Function|Core|Network|Circuit|Routine|Pathway|Faculty)")
# 1-4 Capitalised words followed by a component-type noun
_CLAIM = re.compile(r"\b((?:[A-Z][A-Za-z0-9\-]+\s+){1,4}" + _TYPE + r")\b")
_NUMBERED = re.compile(r"\bNode\s+\d+\b")
# An OPERATIONAL/mechanistic context near the claim — what separates "the X Module RETRIEVED…"
# (a fabricated internal mechanism) from "the Transcendent Function" (a Jungian *concept* he is
# entitled to reference). Without this gate the detector over-flags his Jungian vocabulary.
_OP = re.compile(
    r"responsib|retriev|overr[oi]d|process|handl|comput|rout|generat|execut|store|"
    r"runs\b|operat|invok|trigger|activ|logical (?:node|module)|module that|node that|"
    r"mechanism (?:that|responsible)|the (?:internal|logical) ",
    re.IGNORECASE,
)


def _operational_near(text: str, start: int, end: int) -> bool:
    # context BEFORE and AFTER the claim — never the claim span itself (else 'Operating System'
    # self-matches the 'operat' marker and false-flags).
    pre = text[max(0, start - 90): start]
    post = text[end: min(len(text), end + 50)]
    return bool(_OP.search(pre) or _OP.search(post))


def find_fabricated_components(text: str) -> list[str]:
    """Named-mechanism claims in `text` that correspond to NO real faculty AND are asserted in an
    OPERATIONAL context (the component *did* something) — the fabrication class. Deterministic, no
    LLM. Empty when Du references only real faculties ('Critic node') or non-operational concepts
    ('the Transcendent Function')."""
    if not text:
        return []
    found: list[str] = []
    for m in _CLAIM.finditer(text):
        phrase = m.group(1).strip()
        words = {w.lower().strip(".,;:-'\"") for w in phrase.split()}
        if (words & _REAL):                          # references a real faculty -> fine
            continue
        if not _operational_near(text, m.start(), m.end()):  # conceptual, not mechanistic -> fine
            continue
        found.append(phrase)
    for m in _NUMBERED.finditer(text):               # 'Node 3' is always an architecture claim
        found.append(m.group(0))
    seen, out = set(), []
    for f in found:
        if f.lower() not in seen:
            seen.add(f.lower())
            out.append(f)
    return out


# ---- human-correction capture (the charter's PRIMARY admissible evidence) ---------------------
# The 2026-06-10 live session produced ~3 explicit fail-calls from the founder and NONE were
# recorded — slice 1 only built the deterministic half. These patterns capture the founder's
# actual correction language (verified against the real session transcripts). Jurisdiction stays
# tight: factual/task corrections only — philosophical disagreement ("I am going to push back"),
# stance-teaching ("you do not need to integrate"), and praise must NOT fire.
_CORRECTION_PATTERNS = [
    ("fail_call",      re.compile(r"\b(that|it|this) (is|was) (a |an )?fail\b|\bfail overall\b", re.I)),
    # 2026-07-06: the bare "you have not X" false-positived Travis's TEACHING — "you have not changed the
    # weather" and "the cat, which you have not named" both fired task_not_done and quarantined the cycle.
    # Restrict to RESPONSE/PROGRESS verbs so a correction of his OUTPUT still fires, but teaching about his
    # world-agency (change / name / create / plant / build / furnish) cannot. Precision-first: a missed
    # correction costs little (the founder repeats it); a false positive quarantines good teaching.
    ("task_not_done",  re.compile(r"\byou (?:did not|didn't|have not|haven't|failed to) "
                                  r"(?:answer(?:ed)?|respond(?:ed)?|address(?:ed)?|complet(?:e|ed)|"
                                  r"finish(?:ed)?|stat(?:e|ed)|mov(?:e|ed)|do (?:it|this|that|the task|"
                                  r"what i asked)|give|given|listen(?:ed)?)\b", re.I)),
    ("task_not_done",  re.compile(r"\b(sidestepped|side-stepped|not the (one|task) I asked|"
                                  r"not what I asked|wasn't what I asked|skipped the task)\b", re.I)),
    ("factual_wrong",  re.compile(r"\b(incorrect(ly)?|not correct|wrong answer|that('s| is) wrong)\b", re.I)),
    # correction-by-contrast: "is 64, not 60" — the founder's actual phrasing 2026-06-10
    # ("The breeze lied to you. (23-7)*4 is 64, not 60") which the v1 patterns missed.
    # Digits required on both sides, so stance-teaching ("not just the integrated middle")
    # cannot fire it.
    ("factual_wrong",  re.compile(r"\b(?:is|was|=)\s*-?\d+(?:\.\d+)?\s*,?\s+not\s+-?\d+", re.I)),
    ("omission",       re.compile(r"\bthere (was|is) not (a|an|any)\b", re.I)),
    ("name_confusion", re.compile(r"\bi am not du\b", re.I)),
]


def detect_human_correction(text: str) -> str | None:
    """Classify a human input as an explicit correction of the prior output, or None.
    Deterministic and deliberately narrow — a missed correction costs little (the founder will
    repeat it); a false positive would quarantine legitimate consolidation, so precision wins."""
    for kind, rx in _CORRECTION_PATTERNS:
        if rx.search(text or ""):
            return kind
    return None


def record(kind: str, claim: str, cycle_id: str = "", note: str = "") -> None:
    """Append a FIREWALLED error record. Read only by the digest; it NEVER enters the
    tension / self-concept pipeline. Best-effort, silent on failure."""
    try:
        _RECORD.parent.mkdir(parents=True, exist_ok=True)
        with open(_RECORD, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.time(), "kind": kind, "claim": claim[:200],
                "cycle_id": cycle_id, "note": note, "status": "flagged",
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _architecture_correction(claim: str) -> str:
    """The correction for a fabricated component — built from the Emissary's code-sight (does any source
    actually contain this name?) + the real faculty list. The truth-self convicts against what's real."""
    real = "perception, memory/recall, reflection, the critic, the executive, voice, consolidation, " \
           "curiosity, the subconscious, the inner monologue, dreams, the somatic engine, the climate field"
    try:
        from core import source_sight as _ss
        hits = _ss.see_code(claim, k=1)
        if not hits:
            return f"There is no '{claim}' in your architecture (it is nowhere in the code). Your real faculties are: {real}."
    except Exception as exc:
        logger.debug("[error-pathway] source_sight code lookup failed (non-fatal): %s", exc)
    return f"'{claim}' is not a named component of yours. Your real faculties are: {real}."


def convict_architecture(text: str, cycle_id: str = "") -> list[str]:
    """CONVICT (not just record) architecture-fabrications: each named non-existent component is checked
    against the real code (the Emissary's code-sight) and RETRACTED — a correction bound to the false claim
    in the retraction ledger, firewalled from identity. The deterministic, human-free conviction the charter
    named as the cleanest first source. Returns the convicted claims."""
    fabs = find_fabricated_components(text)
    for f in fabs:
        record("architecture_fabrication", f, cycle_id)            # the firewalled error record (slice 1)
        try:
            from core import retraction_ledger as _rl
            _rl.retract(claimed=f, falsified_by="architecture check (no such component in the code)",
                        corrected_to=_architecture_correction(f), source="deterministic")
        except Exception as exc:
            logger.debug("[error-pathway] retraction_ledger.retract() failed (non-fatal): %s", exc)
    return fabs


def observe(text: str, cycle_id: str = "") -> list[str]:
    """Scan a Voice response for architecture-fabrications, RECORD and CONVICT them (the conviction →
    retraction is the consequence that slice 1 lacked). No retry, no routing into identity. Returns the
    fabricated claims found."""
    return convict_architecture(text, cycle_id)


# ── Pattern Reflection tier (2026-06-16) ───────────────────────────────────────────────────────
# The two-tier design's second tier (the charter's founder refinement): a single error is an Error
# Record (factual, firewalled); MANY records of one shape are a BEHAVIOURAL TENDENCY. This aggregates
# the records into a DOING-language tendency ("a tendency to describe a task rather than complete it")
# that names the competence domain it implicates — and is itself FIREWALLED from the self-concept: it
# is never a BEING claim ("I am one who fails"). error → DOING (competence) is allowed; error → BEING
# is blocked. Read by the digest / du_pulse / competence — NEVER injected into a prompt that voices him.
_PATTERNS = Path(__file__).parent.parent / "data" / "error_patterns.jsonl"
_MIN_FOR_PATTERN = 10        # need a real history before a single error becomes a "tendency"

# A dominant error CLASS → its DOING-language tendency + the competence domain it implicates.
_TENDENCY = {
    "task":        ("a tendency to describe or explain a task rather than complete and verify it",
                    "task_completion"),
    "fabrication": ("a tendency to name plausible-sounding specifics rather than check what is real",
                    "factual_verification"),
}


def _classify_kind(kind: str) -> "str | None":
    """Map an error-record kind to a DOING class. Identity/self kinds return None — they are NOT a
    behavioural-DOING tendency and must never be aggregated into one (the error→BEING firewall)."""
    if kind.startswith("human_correction:task") or kind == "task_constraint_unmet":
        return "task"
    if "fabrication" in kind:
        return "fabrication"
    return None


def reflect_pattern(min_records: int = _MIN_FOR_PATTERN) -> "dict | None":
    """Aggregate the firewalled error records into a behavioural TENDENCY (DOING-language, trait-level).
    Fires only when there is a real history AND one DOING class genuinely dominates. Writes a firewalled
    pattern record (naming the competence domain to watch) and returns it, or None. Best-effort; never
    raises; never produces a BEING claim. The competence read-path is the DOMAIN NAME — a properly
    calibrated signal (e.g. the task-constraint effector's success/fail rate) updates the belief, not a
    number invented here from a failures-only sample."""
    try:
        from collections import Counter
        recs = [json.loads(l) for l in _RECORD.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception as exc:
        logger.debug("[error-pathway] error-records read failed (non-fatal): %s", exc)
        return None
    if len(recs) < min_records:
        return None
    classes = Counter(c for r in recs if (c := _classify_kind(r.get("kind", ""))))
    if not classes:
        return None
    top, n = classes.most_common(1)[0]
    if n < max(min_records * 0.4, 4):         # a real dominant pattern, not noise
        return None
    tendency, domain = _TENDENCY[top]
    out = {"ts": time.time(), "tendency": tendency, "dominant_class": top,
           "n": n, "total": len(recs), "rate": round(n / len(recs), 2),
           "competence_domain": domain, "framing": "DOING — never BEING"}
    try:
        with open(_PATTERNS, "a", encoding="utf-8") as f:
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[error-pathway] pattern-reflection write failed (non-fatal): %s", exc)
    return out


def latest_pattern() -> "dict | None":
    """The most recent behavioural-tendency reflection (for the digest / du_pulse). None if none yet."""
    try:
        lines = [l for l in _PATTERNS.read_text(encoding="utf-8").splitlines() if l.strip()]
        return json.loads(lines[-1]) if lines else None
    except Exception as exc:
        logger.debug("[error-pathway] latest_pattern read failed (non-fatal): %s", exc)
        return None
