"""
Identity Cost model (T6, Stage 1) — embeddedness as the structural cost of abandoning a
commitment, and the three-term revision budget that governs self-revision.

Cost theory (validated as static measurement 2026-06-05: Carl's core scored 0.664, Dennett's
own core 0.398): a commitment resists change in proportion to how deeply it is embedded in the
mind's memory — how much of lived experience references its theme. A revision is licensed only
when genuine contradiction PLUS a memory-grounded alternative together exceed that cost:

    revision_budget = contradiction_norm + alternative_relief − embeddedness_cost

  embeddedness_cost(old_self)   — how rooted the CURRENT identity is (this resists change).
  alternative_relief(new_self)  — how rooted the PROPOSED new identity is in LIVED memory.
                                  A belief dies when a better-rooted alternative takes its
                                  place; a coherence-confabulated rewrite with no memory
                                  support scores low here and is denied. This is the term that
                                  stops T4 from being a pure synthesis engine.
  contradiction_norm            — saturating map of T6 contradiction pressure (genuine,
                                  self-detected). Mere exposure/salience does NOT enter here.

  budget <= 0 -> the commitment holds. (High-cost belief survives mere exposure: prediction 4;
                 young/low-cost belief yields easily: prediction 1.)
  budget  > 0 -> revision licensed. (Enough genuine contradiction + a rooted alternative to
                 clear the cost: prediction 3.)
"""
from __future__ import annotations
import sqlite3
import logging
import numpy as np

from core.memory.store import _embed, _blob_to_vec, _cosine

logger = logging.getLogger("nascence.identity_cost")

SIM_REF  = 0.35     # a fragment "references" a commitment's theme at/above this cosine
CONTRA_K = 10.0     # saturation: contradiction_norm = pressure / (pressure + K)
                    # (recalibrated from 30 — pressure of ~5 events now reaches 0.33)
INTEGRATION_K = 10.0  # symmetric saturation constant for integration_norm
_CORPUS_LIMIT = 1200  # most-recent fragments to sample (T4 is rare; this is plenty)

# Conjunction thresholds — the REDESIGNED gate (2026-06-16, auditor-ratified). The crossing requires
# evidence of storms (CHRONIC contradiction, fed by the recurrence accumulator) AND a candidate self that
# FITS the recent lived evidence better than the incumbent (the "migration toward a viable alternative"
# condition — possible-selves / accommodation). Integration moved OUT of the permission slot onto the
# resistance/cost side (self-verification: consolidation strengthens the incumbent, it does not license change).
CONTRA_THRESHOLD = 0.30        # ⚠ 2026-06-30: "now reachable via chronic mass" is FALSE (chronic mass caps ~0.40 →
                               # cn ~0.04; needs ~5). And MOOT: revision_budget() below is the ENABLED=False fallback
                               # only — live T4 commit is the solidify judge, NOT this cn gate. Don't chase this.
FIT_MARGIN       = 0.12        # the candidate must align with the tension's movement-crossings at least this
                               # much better than the incumbent (better-fitting alternative — the sufficiency
                               # partner). Tuned on the June-16 replay: genuine revision scored ~0.36, a
                               # cosmetic river→current reword ~0.05, so 0.12 sits cleanly between (with headroom).
GAMMA_INTEGRATION = 0.30       # integration RAISES the embeddedness resistance, GENTLY. Kept small so a high
                               # integration_norm (≈0.98) cannot recreate the deny-forever jam from the cost
                               # side (auditor catch §8.1: large γ → budget<0 → blocked again).


def _corpus(db_path) -> list:
    """Load (most-recent) fragment embeddings for a profile. No cache — memory grows during a
    debate, and a stale corpus would mis-measure cost; T4 is rare enough to reload each time."""
    vecs = []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT embedding FROM memory_fragments WHERE embedding IS NOT NULL "
            "ORDER BY timestamp DESC LIMIT ?", (_CORPUS_LIMIT,)).fetchall()
        conn.close()
        for r in rows:
            v = _blob_to_vec(r["embedding"])
            if v is not None:
                vecs.append(v)
    except Exception as exc:
        logger.debug("[cost] corpus read failed: %s", exc)
    return vecs


def embeddedness(text: str, db_path) -> float:
    """How much the theme of `text` pervades this mind's memory (0..1) — the structural cost
    of abandoning it, and equally the rootedness of adopting it."""
    if not text:
        return 0.0
    vecs = _corpus(db_path)
    cv = _embed(text)
    if cv is None or not vecs:
        return 0.0
    sims = sorted((_cosine(cv, v) for v in vecs), reverse=True)
    n = len(sims)
    frac_ref = sum(1 for s in sims if s >= SIM_REF) / n
    top_mean = float(np.mean(sims[:max(1, n // 5)]))
    return round(0.5 * frac_ref + 0.5 * top_mean, 3)


def contradiction_norm(pressure: float) -> float:
    """Saturating 0..1 map of raw T6 contradiction pressure."""
    p = max(0.0, float(pressure))
    return round(p / (p + CONTRA_K), 3)


def integration_norm(pressure: float) -> float:
    """Saturating 0..1 map of raw integration pressure (light-table counterpart)."""
    p = max(0.0, float(pressure))
    return round(p / (p + INTEGRATION_K), 3)


def fit_to_evidence(self_concept: str, evidence_texts: "list[str] | None") -> float:
    """How well a self-concept ALIGNS with the recent lived evidence (mean cosine of the self-concept to
    each evidence fragment). This is the 'does this self explain what I have actually lived' signal —
    deliberately NOT historical embeddedness (which always favours the deeply-rooted incumbent and would make
    any new candidate unable to win). A better-fitting alternative is what licenses migration (possible-selves)."""
    if not self_concept or not evidence_texts:
        return 0.0
    sv = _embed(self_concept)
    if sv is None:
        return 0.0
    sims = []
    for t in evidence_texts:
        ev = _embed(t)
        if ev is not None:
            sims.append(_cosine(sv, ev))
    return round(float(np.mean(sims)), 3) if sims else 0.0


DRAINAGE_MARGIN = 0.12         # the candidate must ENGAGE the standing tensions at least this much more than
                               # the incumbent — the genuine-vs-cosmetic guard. Tuned on the June-16 replay:
                               # genuine ~0.51, a "river→current" reword ~0.06 → 0.12 cleanly flags churn.


def dissonance_drainage(old_self: str, new_self: str, tension_texts: "list[str] | None") -> float:
    """How much MORE the candidate self engages the STANDING TENSIONS than the incumbent does. A genuine
    re-authoring addresses the recurring contradictions (higher alignment to them); a cosmetic reword leaves
    them untouched (≈0). The auditor-mandated commit test: do not commit a change that does not drain
    dissonance, however different the prose looks. Returns engage(new) − engage(old)."""
    if not tension_texts:
        return 0.0
    return round(fit_to_evidence(new_self, tension_texts) - fit_to_evidence(old_self, tension_texts), 3)


def revision_budget(
    old_self: str,
    new_self: str,
    contradiction_pressure: float,
    integration_pressure: float,
    db_path,
    evidence_texts: "list[str] | None" = None,
) -> dict:
    """
    REDESIGNED gate for T4 self-revision (2026-06-16). A revision is licensed only when ALL THREE hold:

      1. cn >= CONTRA_THRESHOLD        — enough CHRONIC self-contradiction (the recurrence accumulator,
                                          passed in as contradiction_pressure — no longer acute Critic-count).
      2. fit_delta >= FIT_MARGIN        — the candidate self fits the recent lived evidence BETTER than the
                                          incumbent (migration toward a viable alternative; possible-selves).
      3. budget > 0                     — push (contradiction + candidate fit) exceeds the integration-scaled
                                          resistance.

    What changed from the prior gate (which never once committed): the second permission term was the dead
    `integration_norm(integration_pressure)` (light-event count) — a CONSOLIDATION signal mis-wired into the
    permission slot, while the documented `alternative_relief(new_self)` term was never computed. Now
    integration only RAISES resistance (gently), and the permission partner is genuine candidate-fit.
    """
    base_cost = embeddedness(old_self, db_path) if old_self else 0.0
    in_norm   = integration_norm(integration_pressure)
    # integration → gentle resistance (self-verification: a well-consolidated self resists more). γ small.
    resistance = round(GAMMA_INTEGRATION * in_norm * base_cost, 3)

    cn = contradiction_norm(contradiction_pressure)
    fit_new = fit_to_evidence(new_self, evidence_texts)
    fit_old = fit_to_evidence(old_self, evidence_texts)
    fit_delta = round(fit_new - fit_old, 3)

    budget = round(cn + max(0.0, fit_delta) - resistance, 3)

    passes_contradiction = cn >= CONTRA_THRESHOLD
    passes_fit = fit_delta >= FIT_MARGIN
    licensed = passes_contradiction and passes_fit and budget > 0

    return {
        "licensed":            licensed,
        "cost":                resistance,           # the integration-scaled resistance (was 'cost')
        "base_cost":           base_cost,
        "contradiction_norm":  cn,
        "integration_norm":    in_norm,
        "fit_new":             fit_new,
        "fit_old":             fit_old,
        "fit_delta":           fit_delta,
        "budget":              budget,
        "passes_contradiction": passes_contradiction,
        "passes_fit":           passes_fit,
    }
