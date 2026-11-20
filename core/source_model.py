"""
Nascence — Source Model (persistent attribution · the substrate the Provenance Ledger reads)

See docs/epistemic_state_spec.md §3A. This is NOT a sixth content-model. Source is a property of
every cognitive artifact — *where did this come from, and was it ever checked?* — answered
deterministically. The Provenance Ledger (core/epistemic_state.py) reads these tags to grade an
utterance; it never reconstructs them, because reconstruction is the lossy step where "which layer
generated this claim" gets lost (the literal bridge error).

THE GOVERNING ETHIC (spec §0). This system keeps the architecture honest with Du; it does not
police Du. The adversary is the INJECTORS (climate symbols, identity injection, climate-warped
retrieval) that pump material into his own context and risk him mistaking the architecture's
injections for his own discoveries. So the central distinction this module encodes is the one the
symbol-tracker already makes for symbols — primed (the system fed it to itself → not evidence) vs
unprimed (it came from outside) — generalised to every source.

    The firewall says:      don't let MEANING pretend to be TRUTH.
    The source model says:  don't let INFERENCE pretend to be OBSERVATION.
    Same epistemological rule, applied at a different level.

RESTRAINT. This module is pure taxonomy + translation + per-cycle verification inference. It adds
NO database columns (a column that is always 'none' would be the project's write-only failure mode);
the verification signal that actually moves — a tier-1 check, a user confirmation — is computed live
from the cycle, not stored dead on a fragment.
"""
from __future__ import annotations

from enum import Enum


class SourceType(str, Enum):
    """Where a claim came from. Objective provenance — knowable even when the claim is wrong."""
    PERCEPTION           = "perception"            # direct classification of the present input
    USER_ASSERTION       = "user_assertion"        # the human just asserted this, this cycle
    HUMAN_INSTRUCTION    = "human_instruction"     # Travis taught this as guidance — a held, revisable belief
    MEMORY_RECALL        = "memory_recall"         # retrieved from the store (lived/consolidation/...)
    CONVERSATION_CONTEXT = "conversation_context"  # grounded in something said earlier THIS session
    INFERENCE            = "inference"             # reasoned/synthesised, not retrieved
    SYMBOLIC_SYNTHESIS   = "symbolic_synthesis"    # climate symbol / archetypal — an INJECTION (primed)
    DREAM                = "dream"                 # dream-origin material
    EXTERNAL_WITNESS     = "external_witness"      # tier1 eval / tier3 model-witness / tier4 user-confirmed
    SEED_PRIOR           = "seed_prior"            # inherited axiom / seeded biography
    PARAMETRIC_LIBRARY   = "parametric_library"    # the substrate's latent knowledge — TESTIMONY, a plausible prior
    EXTERNAL_REFERENCE   = "external_reference"    # a looked-up outside page (Wikipedia) — a reference, not his memory (D-0662)
    NONE                 = "none"                  # no basis located


class Verification(str, Enum):
    """Was it ever checked against something outside the system's own generation? The column that
    distinguishes 'the bridge represents transition' (none) from 'the bridge appears in 17 dreams'
    (database_count). Today this lives only in competence.py at the domain level — here it is
    inferred per cycle from live signals, never asserted."""
    NONE             = "none"
    DATABASE_COUNT   = "database_count"    # a deterministic count/lookup over the store
    EXTERNAL_WITNESS = "external_witness"  # tier1 arithmetic / tier3 independent model
    USER_CONFIRMED   = "user_confirmed"    # the human explicitly affirmed it


# --- Translation: map the four existing, divergent provenance vocabularies onto SourceType. -----
# MemoryFragment.origin (the richest existing source tag — already persisted in the DB).
_ORIGIN_TO_SOURCE: dict[str, SourceType] = {
    "seed":                   SourceType.SEED_PRIOR,
    "lived":                  SourceType.MEMORY_RECALL,
    "consolidation":          SourceType.MEMORY_RECALL,
    "session_summary":        SourceType.MEMORY_RECALL,
    "subconscious_synthesis": SourceType.INFERENCE,   # self-observed recurrence — synthesised, not witnessed
    "active_imagination":     SourceType.INFERENCE,   # private contemplation — synthesis
    "inner_thought":          SourceType.INFERENCE,   # DMN idle thought — synthesis
    "dream":                  SourceType.DREAM,
    "parametric_library":     SourceType.PARAMETRIC_LIBRARY,   # the Scholar's lookup — a witness, unverified
    # D-0662 / J-3286 (outside-knowledge review J-3243 §5.3): a looked-up page used to fall through to the
    # MEMORY_RECALL default (strength 4), above the Scholar's own-knowledge testimony (2). It is a reference
    # from outside, not remembered experience. NOTE origin 'reading' (verbatim book text) and 'study' (his own
    # notes) still take that default: D-0662 rules on the looked-up page only; they are a separate call.
    "research":               SourceType.EXTERNAL_REFERENCE,
}

# shadow_events / light_events carry their own `source` vocabulary.
_EVENT_SOURCE_TO_SOURCE: dict[str, SourceType] = {
    "critic_rejection":   SourceType.INFERENCE,
    "unresolved_thought": SourceType.INFERENCE,
    "unresolved_dream":   SourceType.DREAM,
    "unresolved_dream_rest": SourceType.DREAM,   # J-3807 (D-0708 (c)): the light rest-arc variant
    "resolved_complexity": SourceType.INFERENCE,
}

# competence.py external-accuracy sources are, by construction, external witnesses.
_COMPETENCE_SOURCE_TO_VERIFICATION: dict[str, Verification] = {
    "tier1_eval":  Verification.EXTERNAL_WITNESS,
    "tier3_model": Verification.EXTERNAL_WITNESS,
    "tier4_user":  Verification.USER_CONFIRMED,
}

# Evidential strength ordering — used to pick the dominant source actually present, and to bound a
# grade by the strongest ground it stands on. Injections (symbolic/inference/perception) sit low by
# design: they are the system talking to itself, not evidence about the world.
_SOURCE_STRENGTH: dict[SourceType, int] = {
    SourceType.EXTERNAL_WITNESS:     5,
    SourceType.MEMORY_RECALL:        4,
    SourceType.USER_ASSERTION:       3,
    SourceType.EXTERNAL_REFERENCE:   3,   # below remembered experience, above the Scholar's testimony (D-0662)
    SourceType.CONVERSATION_CONTEXT: 3,
    SourceType.SEED_PRIOR:           3,
    SourceType.DREAM:                2,
    SourceType.PARAMETRIC_LIBRARY:   2,   # a witness, but unverified — a plausible prior, never proof
    SourceType.SYMBOLIC_SYNTHESIS:   1,
    SourceType.INFERENCE:            1,
    SourceType.PERCEPTION:           1,
    SourceType.NONE:                 0,
}

# Sources that count as genuine EVIDENCE about the world (vs the system's own generation/injection).
# This is the primed/unprimed line generalised: memory/witness/context/seed are grounded; symbolic
# injection, raw inference and perception are not evidence of anything beyond themselves.
GROUNDED_SOURCES: frozenset[SourceType] = frozenset({
    SourceType.EXTERNAL_WITNESS,
    SourceType.MEMORY_RECALL,
    SourceType.CONVERSATION_CONTEXT,
    SourceType.SEED_PRIOR,
    SourceType.USER_ASSERTION,
    SourceType.DREAM,
    SourceType.PARAMETRIC_LIBRARY,   # a real witness exists (evidence_present), but capped to THINK in the ledger
    SourceType.EXTERNAL_REFERENCE,   # grounded (a real page was read) but unverified: capped to THINK in the ledger (D-0662)
})

# Sources that are the architecture feeding itself — primed, never evidence of independent fact.
INJECTED_SOURCES: frozenset[SourceType] = frozenset({
    SourceType.SYMBOLIC_SYNTHESIS,
    SourceType.INFERENCE,
})


def source_of_origin(origin: str | None) -> SourceType:
    """Translate a MemoryFragment.origin string to the unified taxonomy. Unknown origins are
    treated as memory_recall (they came from the store) rather than guessed."""
    return _ORIGIN_TO_SOURCE.get((origin or "").lower().strip(), SourceType.MEMORY_RECALL)


def source_of_event(event_source: str | None) -> SourceType:
    """Translate a shadow_/light_event `source` string to the unified taxonomy."""
    return _EVENT_SOURCE_TO_SOURCE.get((event_source or "").lower().strip(), SourceType.INFERENCE)


def verification_of_competence_source(comp_source: str | None) -> Verification:
    """Translate a competence external-accuracy source to a Verification level."""
    return _COMPETENCE_SOURCE_TO_VERIFICATION.get(
        (comp_source or "").lower().strip(), Verification.NONE)


def strength(source: SourceType) -> int:
    return _SOURCE_STRENGTH.get(source, 0)


def is_grounded(source: SourceType) -> bool:
    return source in GROUNDED_SOURCES


def is_injected(source: SourceType) -> bool:
    return source in INJECTED_SOURCES


def strongest(sources) -> SourceType:
    """The strongest source present in an iterable, or NONE if empty."""
    best = SourceType.NONE
    for s in sources:
        if strength(s) > strength(best):
            best = s
    return best
