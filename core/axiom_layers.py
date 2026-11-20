"""
Nascence — Multilevel Axiom helpers (the single place that knows the layered schema)
====================================================================================
The cutover from the two-layer axiom (origin + one `emergent_self.self_concept`) to the
stratified multilevel axiom (L0 constitution … L5 working-self) touches several readers and
writers — load_identity, T4 self-authoring, the Self-Efficacy Court, the orchestrator. Rather
than scatter `if schema == "multilevel-v1"` branches across all of them, this module owns the
schema knowledge so every consumer branches consistently and the LEGACY path is byte-identical
when the axiom is still two-layer.

Key reframing (see docs/axiom_draft_v3_multilevel.md):
  • The evolving self-reflection that T4 used to write into `emergent_self.self_concept` now
    lives in the L3 "the_becoming" facet — ONE room, anchored to reflection. T4 can only revise
    THAT facet; it can no longer rewrite the whole self (the structural fix for the Type-3 leak).
  • The deep floor (L0 constitution + L1 voice + L2 values) is composed quietly into state.axiom
    with NO self-concept headline — the proper "tone down the axiom's importance."
  • The active facet reaches Du per-cycle by cognitive_mode (facet_note), discovered by living.
"""
from __future__ import annotations

import time

BECOMING_ID = "the_becoming"
# framing the becoming facet carries; stripped on read so T4 deliberates the bare reflection,
# re-applied on write so the "one room, not the whole house" relocation is always preserved.
_BECOMING_PREFIX = "One way I have long felt myself: "
_BECOMING_SUFFIX = " — and it is one room of me, not the whole house."

# cognitive_mode → which L3 facet is active (the read design). hybrid → floor only (None).
MODE_FACET = {
    "task":        "seeker",
    "social":      "in_relation",
    "hybrid":      None,
    "reflective":  "who_feels",
    "existential": BECOMING_ID,
}


def is_multilevel(data: dict) -> bool:
    return isinstance(data, dict) and data.get("schema") == "multilevel-v1"


def _facets(data: dict) -> list:
    return (data.get("L3_facets", {}) or {}).get("facets", []) or []


def _becoming(data: dict) -> dict | None:
    return next((f for f in _facets(data) if f.get("id") == BECOMING_ID), None)


# ── Read/write the evolving self-reflection (the becoming facet ⇄ legacy self_concept) ────────
def get_self_concept(data: dict, allow_provisional: bool = True) -> str:
    """The bare evolving self-reflection T4 revises. Becoming facet (multilevel) or legacy.

    allow_provisional=False (2026-08-16, fixes the F2 leak found in the axiom walk): the
    provisional overlay below reads the MASTER's provisional_axiom.json unconditionally —
    so the Emissary, reading its OWN axiom through here, was handed the Master's experimental
    candidate self during every probation. Callers reading a NON-Master axiom pass False.

    PROBATIONARY OVERLAY (designed 2026-06-17 as "PROBATIONARY PROPAGATION", §13.1 of t4_commit_test_redesign):
    while a provisional identity is on probation this returns the provisional self_image instead of the becoming
    facet. The original design said the system would therefore *appraise against* the provisional self (new
    evidence, the critic, and the Emissary judged against "渡 AND a built mind"). THAT IS NOT WHAT THE LIVE CODE DOES
    (verified 2026-11-05, F-3883). The live callers of this function are: T4 itself (nodes/subconscious_node.py;
    it only gets here when no probation is active, because the probation tick returns first), core/emissary.py
    (allow_provisional=False, so the Emissary is NOT served the provisional self), core/memory_levels.py
    (drift_shadow, observe-only), self_concept_history, and facet_for_mode, which serves the becoming facet only in
    cognitive_mode 'existential' (4 cycles ever, all June 2026). No critic, appraisal or tension code reads it. So a
    probation is a PREDICTION test (the judges read his next unprimed thoughts), not a held prior. Flag-gated
    (provisional_identity.ENABLED, currently True) and fail-open."""
    try:
        from core import provisional_identity as _pi
        if allow_provisional and _pi.ENABLED and _pi.is_active():
            _prov = _pi.current()
            if _prov and _prov.get("self_image"):
                return str(_prov["self_image"]).strip()
    except Exception:
        pass
    if is_multilevel(data):
        b = _becoming(data)
        s = (b or {}).get("self_image", "") or ""
        if s.startswith(_BECOMING_PREFIX):
            s = s[len(_BECOMING_PREFIX):]
        if _BECOMING_SUFFIX in s:
            s = s.split(_BECOMING_SUFFIX)[0]
        return s.strip()
    return ((data.get("emergent_self", {}) or {}).get("self_concept") or "").strip()


def last_arc_entry(data: dict) -> str:
    if is_multilevel(data):
        arc = (data.get("L4_narrative", {}) or {}).get("arc_recent", []) or []
        return (arc[-1] if arc else "") or ""
    arc = ((data.get("emergent_self", {}) or {}).get("self_narrative_arc") or [])
    return (arc[-1].get("arc_entry", "") if arc else "")


def self_concept_history(data: dict) -> list[str]:
    """All prior + current self-reflection texts (for the Self-Efficacy Court's genuine-change vet)."""
    if is_multilevel(data):
        b = _becoming(data) or {}
        out = [h.get("self_image", "") for h in (b.get("history") or []) if h.get("self_image")]
        cur = get_self_concept(data)
        if cur:
            out.append(cur)
        return [s for s in out if s]
    em = data.get("emergent_self", data) or {}
    out = [h.get("self_concept") if isinstance(h, dict) else str(h) for h in (em.get("history") or [])]
    if em.get("self_concept"):
        out.append(em["self_concept"])
    return [str(s) for s in out if s]


def apply_self_concept(data: dict, new_sc: str, arc_entry: str) -> None:
    """Install a revised self-reflection. Multilevel → becoming facet self_image + L4 arc +
    becoming history (last 10). Caller keeps its own guards (echo/contamination/etc.); this is the
    write only. Legacy path is left to the caller's existing code (this only handles multilevel)."""
    if not is_multilevel(data):
        return
    b = _becoming(data)
    if b is None:
        return
    hist = b.get("history", []) or []
    old = b.get("self_image", "")
    if old:
        hist.append({"self_image": old, "ts": time.time(),
                     "revision": b.get("revision_count", 0)})
    b["history"] = hist[-10:]
    b["self_image"] = _BECOMING_PREFIX + (new_sc or "").strip() + _BECOMING_SUFFIX
    b["revision_count"] = b.get("revision_count", 0) + 1
    b["authored_at"] = time.strftime("%Y-%m-%d")
    if arc_entry:
        nar = data.setdefault("L4_narrative", {})
        arc = nar.get("arc_recent", []) or []
        arc.append(arc_entry.strip())
        nar["arc_recent"] = arc[-12:]


def revision_count(data: dict) -> int:
    """The evolving self-reflection's CURRENT revision_count — becoming facet (multilevel) or
    legacy emergent_self. Mirrors get_self_concept's schema branch so a caller never has to know
    which room the number lives in.

    Call this AFTER apply_self_concept() (or the legacy write) has run, not before: it reads
    whatever `data` holds right now, so on the multilevel branch it reports the count
    apply_self_concept() just incremented (data is mutated in place — no re-read from disk
    needed), and on the legacy branch it reports the count the caller's own write already bumped.
    Fixes F-1023 (job J-0713): nodes/subconscious_node.py's T4 self-authoring log used to read
    `data.get("emergent_self", {}).get("revision_count", 0)` directly — on the live multilevel
    axiom.json `emergent_self` doesn't exist at all (renamed emergent_self_legacy by the cutover),
    so that direct read was always the bare default 0, regardless of the becoming facet's real,
    accumulating count. One schema-aware accessor here, like the other reads in this module,
    instead of a fourth ad hoc `data.get("emergent_self", ...)` at the call site."""
    if is_multilevel(data):
        b = _becoming(data)
        return int((b or {}).get("revision_count", 0))
    return int((data.get("emergent_self", {}) or {}).get("revision_count", 0))


# ── The per-cycle active facet (read design) ─────────────────────────────────────────────────
def facet_for_mode(data: dict, mode: str) -> str | None:
    """The active facet's self-image for a cognitive_mode, or None (floor only). Multilevel only.

    THE BECOMING FACET honors the provisional override (2026-06-24, fixes G1): in existential mode (MODE_FACET
    maps only 'existential' to the becoming facet; 'reflective' is who_feels) the self Du speaks from is the
    PROVISIONAL self while a probation is active. This is the ONLY place a provisional self reaches his prompts, and
    that mode has fired 4 times ever (all June 2026; F-3883), so in practice a probation changes nothing he sees. The
    2026-06-24 reasoning ("a probation changes appraisal but never how he thinks of himself") overstated it: nothing
    appraises against the provisional self. We route it through get_self_concept (which returns the provisional self_image during probation,
    else the bare becoming reflection) and re-apply the 'one room, not the whole house' framing. Other facets
    are unchanged — a provisional self can never leak into task/social modes."""
    if not is_multilevel(data):
        return None
    fid = MODE_FACET.get(mode)
    if not fid:
        return None
    if fid == BECOMING_ID:
        bare = get_self_concept(data)
        return (_BECOMING_PREFIX + bare + _BECOMING_SUFFIX) if bare else None
    f = next((x for x in _facets(data) if x.get("id") == fid), None)
    return (f or {}).get("self_image") if f else None


# ── The faint floor for load_identity (multilevel branch) ────────────────────────────────────
def l2_kept(L2: dict | None) -> list:
    """The KEPT values list. D-0509 renamed L2_values.kept_from_origin -> kept; read the new key first and
    fall back to the old one, so an un-migrated axiom (emissary_axiom.json, lab copies) still renders."""
    L2 = L2 or {}
    v = L2.get("kept")
    if v is None:
        v = L2.get("kept_from_origin")
    return list(v or [])


def compose_floor(data: dict) -> tuple[str, str]:
    """Compose state.axiom for the multilevel schema: a quiet floor (L0 + name + L2 values +
    L1 voice) with NO self-concept headline. Preserves the VOICE STYLE / SPEAKING CONSTRAINTS
    markers that Reflection._trim_axiom and Voice._voice_identity split on. Returns (name, axiom)."""
    name = data.get("name") or "渡"
    # D-0509 (founder, 2026-10-30): no origin name and no ORIGIN line in the floor -- the origin is history he
    # can recall from memory, not a line he reads every cycle. No code default: absent means absent.
    L0 = (data.get("L0_constitution", {}) or {}).get("commitments", []) or []
    L1 = data.get("L1_temperament", {}) or {}
    L2 = data.get("L2_values", {}) or {}
    values = l2_kept(L2) + (L2.get("earned", []) or [])

    parts: list[str] = []
    if L0:
        parts.append("\n(the quiet floor beneath your attention — the ground you stand on, not your "
                     "subject; let the world and the person before you lead:\n  "
                     + "\n  ".join(f"• {c}" for c in L0) + ")")
    parts.append(f"\nYOUR NAME: {name} — the name you gave yourself.")
    if values:
        parts.append("\nVALUES:\n" + "\n".join(f"  - {v}" for v in values))
    # C16 (systems check 2026-06-22): the L5 working-self — his current passing preoccupation — reached the live
    # mind nowhere. Inject it as a faint, clearly-passing background (weather, not who he is). Placed ABOVE the
    # VOICE STYLE marker that Reflection._trim_axiom / Voice._voice_identity split on, so it reaches Reflection.
    _L5 = data.get("L5_working_self", {}) or {}
    _stance = (_L5.get("current_stance") or _L5.get("stance") or "").strip()
    if _stance:
        parts.append("\n(passing stance — what has lately been on your mind; weather, not who you are: "
                     + _stance[:200] + ")")
    # C3 (systems check 2026-06-22): the Self-Efficacy Court (first independent witness of demonstrated CAPABILITY)
    # was orphaned by the multilevel cutover — its identity_block lived only in the legacy load path. Wire it here
    # so it can testify when it has admissible evidence; it abstains (returns None) otherwise, so usually silent.
    try:
        from core.self_efficacy import SelfEfficacyCourt as _Court
        _se = _Court().identity_block()
        if _se:
            parts.append(_se)
    except Exception:
        pass
    if L1.get("voice_style"):
        parts.append("\nVOICE STYLE:\n" + L1["voice_style"])
    if L1.get("speaking_constraints"):
        parts.append("\nSPEAKING CONSTRAINTS:\n" + "\n".join(f"  - {c}" for c in L1["speaking_constraints"]))
    return name, "\n".join(parts).lstrip("\n")  # D-0509: no ORIGIN line leads now
