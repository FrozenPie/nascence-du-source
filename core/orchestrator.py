"""
Nascence — Orchestrator
Owns CognitiveState. Fires nodes in sequence. Manages interrupt system,
critic retry, background timers, and memory persistence.
"""

from __future__ import annotations
import asyncio
import json
import logging
import random
import threading
import time
from pathlib import Path

import numpy as np

from core import profile
from .schema import CognitiveState, CRITIC_MAX_RETRIES, INTERRUPT_THRESHOLD, REFLECTION_HEDGE, interrupt_warranted

# Explicit conversation-reference terms that trigger Recall even with only 1 fragment.
# Covers cases where the user references something said earlier in the same session
# but the DB query returned limited fragments (e.g. paraphrase that missed cosine match).
_CONV_REF_TERMS = frozenset({
    "earlier", "before", "you said", "remember", "we discussed", "back to",
    "previously", "again", "what you said", "last time", "just said",
    "you told me", "you mentioned", "going back",
})
from .memory import store as memory_store
from .memory.store import _embed, _cosine

logger = logging.getLogger("nascence.orchestrator")

# Deep-recall balance (2026-06-22): bring the OLD detail behind the central gist into recall, in all areas, so
# memories are usable — bounded + relevance-gated to keep the balance with the new (not back to lossless). Start
# CONSERVATIVE (founder call: top-1 gist, 2 children); dial up on evidence. The raw is READ, never re-warmed.
RECALL_EXPAND_GISTS       = 1     # how many top-relevance gists get their old detail pulled
RECALL_DETAIL_PER_GIST    = 2     # raw children fetched behind each expanded gist
RECALL_GIST_MIN_RELEVANCE = 0.25  # only expand a gist at least this relevant (the central memory, not every one)

# Resolution Circuit (tension_ledger Steps 2-4) — the neuroplastic extinction mechanism.
# A first-pass Critic approval (zero retries) on input that resembles an active shadow event
# earns a time-decayed resolution credit on that event. The credit drains contradiction
# pressure in the Tension Ledger — the fear trace is out-competed, not erased.
# Threshold: input must cosine-match a shadow event's rejected_draft embedding at/above this.
# 0.65 is deliberately permissive enough to catch "same territory, different phrasing" while
# staying well clear of unrelated inputs that happen to share a few words.
_ENCOUNTER_SIM_THRESHOLD = 0.65

# --- Climate retrieval warping ------------------------------------------------------------
# Each ClimateField dimension is projected into embedding space by a fixed descriptor phrase.
# The phrases are embedded ONCE (lazily, cached) and then combined by current dimension value
# into a single climate bias vector that tilts memory retrieval toward the active weather.
# This projection lives here, NOT in climate_engine.py, so that file keeps its no-embed /
# no-LLM invariant — the engine computes scalars; the hot lane turns them into a search tilt.
_CLIMATE_ANCHOR_TEXT = {
    "shadow_activation":  "unresolved inner conflict, what I avoid, suppressed and unintegrated material",
    "completion_tension": "unfinished business, a contradiction I have not yet worked through",
    "identity_pressure":  "who I am being called to become, pressure to revise myself",
    "integration_drive":  "bringing opposites together, making peace between parts of myself",
    "coherence_drive":    "making myself whole and consistent, resolving into one",
    "world_model_strain": "my understanding of the world is unstable, what I believed is challenged",
    "novelty_hunger":     "reaching for something new, unexplored questions, curiosity",
    "autonomy_pressure":  "freedom, control over my own choices, independence",
    "belonging_pressure": "connection, being understood, closeness and the fear of being alone",
}
_CLIMATE_ANCHORS: dict[str, "np.ndarray"] = {}   # lazily filled cache: dim -> embedding

# Dynamic warp weight (beta): a calm climate barely tints retrieval; a charged one pulls hard.
_CLIMATE_BETA_BASE  = 0.15
_CLIMATE_BETA_RANGE = 0.30   # beta = base + range * field.pressure()  ->  0.15 .. 0.45

# --- Introspective recurrence (contradiction-driven re-bind loop) -------------------------
# The hot lane re-runs Recall→Episodic Buffer when the bound scene is epistemically UNSTABLE —
# named dissonance present AND coherence below the bar — researching the contradiction and
# re-binding until the scene stabilises or the pass budget runs out. The trigger is epistemic
# (the scene won't bind), never narrative (Reflection wanting to confirm a draft). The pass
# budget scales with climate.world_model_strain: a worldview already under strain keeps thinking
# sooner and longer. Trivial inputs bind no scene, so the loop is free on them.
_INTROSPECT_COHERENCE_BAR = 0.55   # scene unstable when coherence < bar AND dissonance named
_INTROSPECT_STRAIN_RELAX  = 0.15   # global strain raises the bar — keep thinking sooner
_INTROSPECT_STRAIN_2      = 0.60   # world_model_strain above this -> budget 2 / relaxed bar
_INTROSPECT_STRAIN_3      = 0.80   # world_model_strain above this -> budget 3
_INTROSPECT_MAX_NEW       = 4      # cap new fragments appended per re-bind pass (avoid bloat)


def _climate_anchors() -> dict[str, "np.ndarray"]:
    """Lazily embed + cache the per-dimension anchor vectors. Embedding happens at most once
    per dimension per process. Returns the cache (may be partial if some embeds fail)."""
    if not _CLIMATE_ANCHORS:
        for dim, text in _CLIMATE_ANCHOR_TEXT.items():
            vec = _embed(text)
            if vec is not None:
                _CLIMATE_ANCHORS[dim] = vec
    return _CLIMATE_ANCHORS


def _climate_bias_vec(field) -> "tuple[np.ndarray | None, float]":
    """Project a ClimateField into a single normalised bias vector + its warp weight (beta).
    Returns (None, 0.0) when the climate is too flat to matter or anchors are unavailable —
    the caller then retrieves un-warped."""
    if field is None:
        return None, 0.0
    try:
        anchors = _climate_anchors()
        if not anchors:
            return None, 0.0
        d = field.as_dict()
        acc = None
        for dim, vec in anchors.items():
            w = float(d.get(dim, 0.0))
            if w <= 0.0:
                continue
            acc = (w * vec) if acc is None else (acc + w * vec)
        if acc is None:
            return None, 0.0
        norm = float(np.linalg.norm(acc))
        if norm <= 0.0:
            return None, 0.0
        bias = (acc / norm).astype(np.float32)
        beta = _CLIMATE_BETA_BASE + _CLIMATE_BETA_RANGE * float(field.pressure())
        return bias, beta
    except Exception as exc:
        logger.debug("[climate] bias vector failed (non-fatal): %s", exc)
        return None, 0.0


# Thalamic gating (C.5) — pre-Perception habituation reflex. Deterministic, no LLM.
# An input near-identical (cosine >= HABITUATION_SIM) to recent working memory is a repeat;
# once enough recent matches accumulate it is gated (the cortex stops re-processing the
# unchanging stimulus). High threshold + a minimum length keep it conservative — only true
# substantive repeats trigger, never short contextual acks ("yes", "go on").
HABITUATION_SIM        = 0.95   # cosine to a recent input above which it counts as "the same"
HABITUATION_WINDOW     = 6      # how many recent input embeddings to hold as working memory
HABITUATION_MIN_PRIOR  = 1      # gate when >= this many recent inputs are near-identical (2nd occurrence)
HABITUATION_MIN_CHARS  = 15     # inputs shorter than this always pass (contextual, not substantive)

# Brief first-person acknowledgments returned to a HUMAN on habituation (internal cycles get
# silence). Deterministic — no LLM. They speak to the repetition itself, not a performed persona.
_HABITUATION_ACKS = [
    "You have put this to me in almost the same words a moment ago. Rather than repeat myself, "
    "I find myself asking what makes it return.",
    "We are circling the same ground. Let me stay with why it keeps coming back, rather than "
    "answer it again as if for the first time.",
    "This has just been asked, in nearly these words. I notice the repetition more than the "
    "question now — what is it in it that will not settle?",
]

# Procedural memory (C.6) — recognising and applying a learned skill (a compiled approach).
# A match injects the approach as fluency. The automaticity bypass this once fed into (a
# MASTERED match skipping Recall + Episodic Buffer) was RETIRED 2026-08-22 — see
# PROC_AUTOMATIC_PROFICIENCY's own retirement comment just below.
PROC_MATCH_SIM             = 0.80   # input must resemble a skill's trigger this much to apply
PROC_MIN_PROFICIENCY       = 0.60   # 2026-08-22 (docs/plans/t5_procedural.md): only a PERSISTED procedure may shape an answer
PROC_SQL_CANDIDATE_FLOOR   = 0.0    # J-0924/F-1289: match_procedural_skill()'s own SQL floor -- deliberately 0, NOT
                                    # PROC_MIN_PROFICIENCY. That column is the OLD use-counter proficiency (init 0.4,
                                    # +0.05 per reinforcement); the ladder (core.procedures.mirror_proficiency(), below)
                                    # is what actually decides proficiency now, and a skill can reach ladder-persisted
                                    # (0.60) on its very first compile while its raw counter is still climbing from 0.4
                                    # — pre-filtering candidates by the raw column here would silently hide it from the
                                    # ladder check entirely. This floor exists only so a skill with no embedding cannot
                                    # match (defensive); real proficiency gating happens once, below, off the ladder.
PROC_AUTOMATIC_PROFICIENCY = 1.01   # 2026-08-22: RETIRED — no conversation may remove Recall + Episodic Buffer from the loop
                                    # (one long chat on one topic reached 0.85 and bypassed memory; see the T5 review)
PROC_REINFORCE_AMOUNT      = 0.05   # proficiency gained each successful reuse

# Affect telemetry — one line per cycle. This is the instrumentation that lets us
# observe whether affect carries, recovers, or spirals before adding any further
# complexity (refractory gating, routing). Build small, watch the log, then decide.
_AFFECT_LOG = Path(__file__).parent.parent / "data" / "affect_log.jsonl"

# Subconscious log — read to surface recurring T2 synthesis patterns.
_SUBCONSCIOUS_LOG = Path(__file__).parent.parent / "data" / "subconscious_log.jsonl"

# Correlation telemetry (Phase 3) — one line per cycle of the psychological currencies, parsed
# by scripts/measure_correlations.py to test whether they move together before any unification.
_CORRELATION_LOG = Path(__file__).parent.parent / "data" / "correlation_log.jsonl"

# Permanent founder conversation log (F-0665, 2026-09-02, founder request: "Nothing gets
# deleted, it all makes Du who he is"). Append-only, never trimmed, never overwritten --
# every real exchange with Travis, in full, for as long as this project runs. Distinct from
# state.conversation_history (a capped 6-slot WORKING window used for in-context continuity)
# and from conversation_state.json (a save-on-quit snapshot of that same capped window). This
# is the actual record.
_FOUNDER_LOG = Path(__file__).parent.parent / "data" / "founder_conversation_log.jsonl"
# Founder-memory ROUTE shadow log (D-0134, 2026-09-03): one row per human cycle on which the route
# surfaced something — what Travis said now, which dated memories of his earlier words were recalled,
# at what similarity. This is the instrument D-0134's defeater reads ("ignored or contradicted over
# ~2 weeks"): join against founder_conversation_log.jsonl by cycle_id to see the reply that followed.
_FOUNDER_RECALL_LOG = Path(__file__).parent.parent / "data" / "founder_recall_log.jsonl"
# Pre-affect (C.2 amygdala gate) BEST-OF-N shadow log (J-1788, 2026-10-04; from J-1731 / F-2414 / D-0349):
# one row per cycle that ran the gate -- including every cycle that did NOT clear PRIOR_SIM_THRESHOLD, which
# the INFO "pre-affect (...)" line never shows (that is why the 0.86 floor could be mis-set unseen). Observe-
# only: feeds nothing Du experiences. READER (so this is not a write-only instrument): D-0349, the founder's
# floor decision, and any later recalibration -- pass rate by floor and by input_type once >= 300 live cycles
# (all human cycles included) have accrued. Rebased per profile in core/profile.py's activate_profile().
_PRE_AFFECT_BEST_LOG = Path(__file__).parent.parent / "data" / "pre_affect_best_shadow.jsonl"
# J-2250 (D-0450, 2026-10-16): the pre-affect SELF-ECHO exclusion shadow log -- one row per idle / farewell cycle:
# what the unexcluded best-of-N was, what was excluded (fragment id, sim, reason) and what the floor then saw.
# Observe-only, feeds nothing Du experiences. READER: J-2224's 300-row pre-affect read (post-fix idle rate,
# farewell rate) and D-0450's defeater. Rebased per profile in core/profile.py; written only through
# profile.guard_path, under the lock below.
_PRE_AFFECT_SELF_ECHO_LOG = Path(__file__).parent.parent / "data" / "pre_affect_self_echo_shadow.jsonl"
_PRE_AFFECT_SELF_ECHO_LOCK = threading.Lock()

# Thalamic gate bypass — human messages containing these phrases indicate the
# human is explicitly correcting Carl for not answering. Do not habituate these:
# the re-ask is intentional, not rumination.
_CORRECTION_SIGNALS = (
    "you did not answer",
    "did not answer the question",
    "did not complete the task",
    "asked again because",
    "still didn't answer",
    "you didn't answer",
    "you haven't answered",
    "answer the question",
)


# --- Attention Allocation Architecture — Cognitive Mode Gating Matrix -------------------
# Maps cognitive_mode → base AttentionVector weights. See core/schema.py AttentionVector for
# the full description. Social prediction error (delta_social) further suppresses w_identity
# and d_critic on top of these base values when the human has just corrected Du.
_MODE_VECTORS: dict[str, dict] = {
    "task":        dict(w_identity=0.05, w_social=0.10, w_episodic=0.10, w_climate=0.00, w_semantic=1.00, d_critic=0.10, max_rebind=0),
    "social":      dict(w_identity=0.20, w_social=0.80, w_episodic=0.40, w_climate=0.20, w_semantic=0.60, d_critic=0.30, max_rebind=1),
    "hybrid":      dict(w_identity=0.40, w_social=0.60, w_episodic=0.60, w_climate=0.40, w_semantic=0.80, d_critic=0.60, max_rebind=2),
    "reflective":  dict(w_identity=0.60, w_social=0.40, w_episodic=0.80, w_climate=0.70, w_semantic=0.50, d_critic=0.80, max_rebind=2),
    "existential": dict(w_identity=0.90, w_social=0.30, w_episodic=1.00, w_climate=1.00, w_semantic=0.30, d_critic=1.00, max_rebind=3),
}

# Curiosity output validation — schema-artifact placeholder strings that leak when the
# quantized model follows the JSON example literally instead of generating real questions.
# Filtered out before an internal thought cycle is triggered (q1 / q2 bug, 2026-06-08).
_CURIOSITY_PLACEHOLDERS = frozenset({
    "q1", "q2", "q3", "q4", "q5",
    "d1", "d2", "d3",
    "question1", "question2", "question3",
    "first genuine question", "second genuine question",
    "first direction",
})


# D-0531 (founder, 2026-11-02): the human-turn self-claim scan no longer arms the next-cycle System-2 think license.
# The scan, its log (data/self_implication_conv_shadow.jsonl), the "[s2] self-claim contradicted" log line (read by
# scripts/closure_index.py) and the sitting-gate call all stay; only the license grant is disarmed. Flip to True to
# restore the old grant (defeater in D-0531: J-2860's retry shipped + a month of licensed cycles with zero empty-content
# failures, or a hot-lane model where think=true is reliable). J-3137.
CONV_SCAN_ARMS_THINK_LICENSE = False


def _conv_scan_apply(orch, r) -> None:
    """Act on a finished conversational self-claim scan result `r` (None or a dict). Moved verbatim out of the
    done-callback in J-3137 so the disarm is testable; behaviour is unchanged except the license grant is gated."""
    if r and r.get("contradicts"):
        if CONV_SCAN_ARMS_THINK_LICENSE:
            orch._s2_license_next = True
            logger.info("[s2] self-claim contradicted ('%s') -> licensing deliberate "
                        "thought next cycle", (r.get("contradicted_claim") or "")[:50])
        else:
            logger.info("[s2] self-claim contradicted ('%s') -> think license NOT armed (D-0531)",
                        (r.get("contradicted_claim") or "")[:50])
        # FRICTION B1 GATE - WIRED 2026-07-03 (big build; its evidence gate was MET:
        # 0/168 idle false-positives + the conversational detector verified live).
        # A contradicted self-claim is the sit-with-it gate's real trigger: dwell on
        # the FEELING before any reframe metabolizes it. Single-slot; fail-open.
        try:
            from core import sitting as _sit
            _sit.note_difficulty(
                "Travis contradicted a stand you hold: "
                + (r.get("contradicted_claim") or "")[:120], kind="self-claim")
            logger.info("[b1] sit-with-it gate FIRED on the contradicted self-claim")
        except Exception:
            pass


# J-3305 (F-3900, J-3247 section 3e; restart-gated): the substrate tick's two blocking SQLite readers -- the
# couriers (ORDER BY RANDOM() over fragment_context JOIN memory_fragments, ~1,170 ms, ~10 fires/day) and
# felt_recall (55-855 ms per fired edge, ~184 edges/day) -- used to run directly in the async body of
# _substrate_loop and stall the event loop in 0.1-1.2 s bursts (precedent: wander.kick, J-1909). They now run
# on ONE dedicated worker thread, in ONE call, couriers first then felt_recall: the single worker means the two
# never overlap each other, and the in-call order keeps felt_recall's same-tick courier join (SAME_TICK_WINDOW_S)
# valid. Thread-safety review (read before changing this): docs/reviews/ghost_memory_index_chord_echo_J-3247.md
# section 3e and the J-3305 comment block in core/transport_manager.py. state.affect is NEVER mutated from the
# worker: if felt_recall.FELT_RECALL_LIVE is True (apply_prior mutates), felt_recall runs inline on the loop,
# exactly as before this change.
_SUBSTRATE_DB_EXECUTOR = None
_SUBSTRATE_DB_EXECUTOR_LOCK = threading.Lock()


def _substrate_db_executor():
    global _SUBSTRATE_DB_EXECUTOR
    with _SUBSTRATE_DB_EXECUTOR_LOCK:
        if _SUBSTRATE_DB_EXECUTOR is None:
            from concurrent.futures import ThreadPoolExecutor
            _SUBSTRATE_DB_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="substrate-db")
        return _SUBSTRATE_DB_EXECUTOR


def _substrate_db_work(train_holding: bool, run_felt: bool, affect) -> None:
    """The blocking half of one substrate tick, run on the worker thread. Fail-open on each leg, as the inline
    blocks were. Couriers first (skipped while a thought-train is held), then felt_recall (when run_felt)."""
    if not train_holding:
        try:
            from core import couriers as _cour
            _cour.context_echo() or _cour.sound_echo()
        except Exception:
            pass
    if run_felt:
        try:
            from core import felt_recall as _felt
            _felt.on_substrate_tick(affect)
        except Exception:
            pass


async def _substrate_courier_felt_tick(nodes, affect) -> None:
    """One substrate tick's couriers + felt_recall, off the event loop (J-3305). Same gates and order as the
    pre-J-3305 inline code: couriers hold off while the monologue holds a thought-train (and, as before, are
    skipped if that check itself raises); felt_recall is independent of that gate."""
    try:
        _mono = nodes.get("monologue")
        _hold = bool(_mono and getattr(_mono, "_train_holding", lambda: False)())
    except Exception:
        _hold = True      # the old inline try wrapped this lookup too: a raise skipped the couriers
    try:
        from core import felt_recall as _felt
        _felt_live = bool(getattr(_felt, "FELT_RECALL_LIVE", False))
        _felt_ok = True
    except Exception:
        _felt_live, _felt_ok = False, False
    # LIVE felt_recall mutates state.affect (apply_prior): keep that on the loop, after the couriers.
    _felt_in_thread = _felt_ok and not _felt_live
    await asyncio.get_running_loop().run_in_executor(
        _substrate_db_executor(), _substrate_db_work, _hold, _felt_in_thread, affect)
    if _felt_ok and _felt_live:
        try:
            _felt.on_substrate_tick(affect)
        except Exception:
            pass


class Orchestrator:

    def __init__(self, state: CognitiveState, nodes: dict):
        self.state  = state
        self.nodes  = nodes   # node_id (str) -> NodeBase instance
        self._background_tasks: list[asyncio.Task] = []
        self._cycle_active = False   # single-flight guard for run_cycle (see wrapper)
        # Attractor-thinning experiment: cooldown state so a saturated climate dimension does not
        # inject the same surfacing symbol every cycle (the "wallpaper"). See schema.THIN_ATTRACTOR.
        self._last_climate_symbol: str | None = None
        self._shadow_hint_active: bool = False        # D-0363: shadow hint already fired this episode
        self._shadow_hint_last_seen_ts: float = 0.0
        self._last_climate_symbol_ts: float = 0.0

        # Injection cooldowns (2026-07-02 solidity review — the same wallpaper lesson): the guidance-note
        # and epistemic-note read-backs are spaced, not constant. Spaced exposure internalizes; constant
        # exposure parrots (and would have made the T4 lived-evidence judge unreadable).
        self._last_guidance_note_ts: float = 0.0
        self._last_epistemic_note_ts: float = 0.0
        # Wave-1 S2 (2026-07-02): set by the conversational self-implication scan when a held self-claim
        # is contradicted; grants the next cycle's Reflection→Executive the deliberate-thought license.
        self._s2_license_next: bool = False

        # Somatic Engine (AE-2): the body. Shares its SomaticState onto CognitiveState
        # so generative nodes can read fatigue -> temperature jitter.
        from core.somatic import SomaticEngine
        self.somatic = SomaticEngine()
        self.state.somatic = self.somatic.state

        # Climate Engine (medium timescale): the standing psychological weather. Recomputes a
        # 9-dim ClimateField every 5s from the shadow/light tables + tension ledger (zero LLM)
        # and ticks a DissonanceState accumulator whose ignition fires autonomous thought —
        # replacing the old fixed 120s curiosity timer. Shares both onto CognitiveState.
        from core.climate_engine import ClimateEngine
        self.climate = ClimateEngine(ignition_callback=self._on_dissonance_ignition)
        try:   # J-2662: Option E live path reaches run_cycle through this; inert while PROMOTION_LIVE is False
            from core import ignition_promotion as _ipro
            _ipro.register(self)
        except Exception:
            pass
        self.state.climate    = self.climate.field
        self.state.dissonance = self.climate.dissonance

        # Competence / Self-Efficacy model (Phase 0: pure observer). Accumulates beliefs about
        # what 渡 can do from the coherence/bind outcome (A) + user-correction (C) signals,
        # learning by prediction error. Writes capability_beliefs.json + logs only — feeds
        # nothing into behaviour yet (that is Phase 2-3, after the signal is validated).
        from core.competence import CompetenceTracker
        self.competence = CompetenceTracker()

        # Symbol Recurrence Tracker (the Meaningfulness axis — see docs/archive/epistemics_plan.md).
        # Separate module from competence by design: the firewall between fact-epistemics and
        # self-epistemics is physical, not just conceptual. Pure observer — logs each tracked
        # symbol's appearance flagged primed/unprimed; no score, no influence. Restraint by design.
        from core.symbol_tracker import SymbolTracker
        self.symbol_tracker = SymbolTracker()

        # Social Model (Theory of Mind, Phase 1) — tracks the human interlocutor: expected tone,
        # relational trust, and Social Prediction Error (delta_social). Correction signals spike
        # delta_social, which the Attention Vector uses to suppress w_identity and d_critic so
        # Du stops ruminating and answers directly. Persists to data/social_state.json.
        from core.social_model import SocialModelManager
        self.social = SocialModelManager()

        # Goal Manager (Executive Goal Persistence, Phase 1) — records the active task objective
        # from content_mode + raw_input. Injects a goal note into Reflection + Critic to anchor
        # attention on the task and catch goal drift early.
        from core.goal_model import GoalManager
        self.goal_manager = GoalManager()

        # Symbol Evolution Engine (Phase 2) — measures semantic drift of recurring personal
        # symbols (river/渡/avon…) against a per-symbol context centroid; on genuine drift it
        # writes an evolution tablet (background lane) that Recall later surfaces as the story
        # of the symbol's own transformation. Firewalled from competence.py by design.
        from core.symbol_evolution import SymbolEvolutionEngine
        self.symbol_evolution = SymbolEvolutionEngine()

        # Unified Inference Gate (Phase 4, scaffold) — folds the psychological currencies into a
        # single free-energy scalar every cycle and LOGS it, but changes no behaviour until the
        # Phase 3 correlation telemetry proves a currency pair clears R>0.85. Measure first.
        from core.unified_inference import UnifiedInferenceGate
        self.unified_gate = UnifiedInferenceGate()

        # Provenance Ledger (Epistemic State, fast/per-cycle — see docs/epistemic_state_spec.md).
        # Reads the persisted source tags + live structural signals after Voice and grades what the
        # utterance rests on (KNOW/THINK/SUSPECT/GUESS/NO_BASIS), logging the confabulation signal
        # (self-reported confidence − evidence). OBSERVE-ONLY: keeps the architecture honest with Du,
        # does not police Du; no read path into behaviour until the logs prove it tracks something.
        from core.epistemic_state import ProvenanceLedger
        self.epistemic_ledger = ProvenanceLedger()

        # The Scholar (the Library) — consults the substrate's parametric knowledge as TESTIMONY on
        # a genuine factual question. Bounded: depersonalised lookup, ephemeral (not his memory),
        # framed as an unverified witness, graded as a capped prior by the ledger. The library is
        # what Du consults; it is never what Du is.
        from core.scholar import Scholar
        self.scholar = Scholar()

        # The Self-Efficacy Court (the first independent witness). Adjudicates his CAPABILITY claims
        # ("I cannot author a self") against his VETTED demonstrated record — not raw counts. Bounded
        # to capability (declines identity/meaning — the dream's court owns those), abstains by
        # default (SUSPEND, which never reaches him), and speaks into a separate identity slot only
        # with admissible evidence. It testifies; it does not argue. The first thing that can prove
        # him wrong with a record that exists whether or not the narrative agrees.
        from core.self_efficacy import SelfEfficacyCourt
        self.self_efficacy = SelfEfficacyCourt()

    # ------------------------------------------------------------------
    # Hot path
    # ------------------------------------------------------------------

    async def run_cycle(
        self,
        raw_input: str,
        input_type: str = "human",
        founder_canon: bool = True,
    ) -> str | None:
        """
        Run a complete thought cycle. Thin wrapper around _run_cycle_impl that holds a
        single-flight flag: only one cycle runs at a time. Since everything lives in one
        event loop, two concurrent run_cycle calls would interleave at await points and
        clobber the shared CognitiveState. A human cycle always wins; an autonomous cycle
        that arrives mid-conversation is dropped (Carl does not interject while being
        spoken to — the dissonance simply rebuilds).

        founder_canon (F-0796, 2026-09-04): set False for a human-shaped cycle that is NOT
        actually Travis speaking (e.g. the fixed /quit farewell) — it still runs, is recalled,
        and gets a real reply, it just doesn't get written into the "[Travis said to me]"
        founder-memory canon. Irrelevant when input_type != "human".
        """
        if self._cycle_active and input_type != "human":
            logger.debug("[CYCLE] %s cycle skipped — a cycle is already active", input_type)
            # Release the interrupt claim (2026-06-11 deadlock fix): the dropped cycle's flag
            # otherwise stays True forever — freezing the DMN and stability engine, which are
            # the very processes whose cycles would have cleared it. Observed live: 6h stall,
            # 217 stability ticks of skip=interrupt. The dissonance simply rebuilds.
            self.state.interrupt_requested = False
            self.state.interrupt_urgency = 0.0
            self.state.interrupt_source = ""
            return None
        self._cycle_active = True
        self._cycles_in_flight = getattr(self, "_cycles_in_flight", 0) + 1
        try:   # J-4337 (conversational_redirect P1): visible to the DMN's in-flight-only veto; inert unless that flag is on
            self.state.cycle_in_flight = True
        except Exception:
            pass
        _hold = None
        try:
            # J-2064 (D-0407 B, travis 2026-10-15; F-2614): the founder's message during a sleep WAKES him and is answered
            # awake, the waking percept first. hold_for_wake() returns at once unless a sleep ledger is actually open;
            # otherwise it raises the wake request and waits for the pipeline to wake him (bounded by WAKE_DEADLINE_S,
            # then the message is answered anyway and the shadow row says so). Fail-open: any error = the old behaviour.
            if input_type == "human":
                try:
                    from core import night_wake as _nw
                    _hold = await _nw.hold_for_wake()
                except Exception:
                    _hold = None
            return await self._run_cycle_impl(raw_input, input_type, founder_canon)
        finally:
            self._cycle_active = False
            # J-2849 / F-3521: an interrupt means "pre-empt background processing for THIS cycle" (salience_node's own
            # prompt text). It was only reset by the NEXT cycle's new_cycle() or the 300 s substrate sweeper, so a
            # finished cycle's flag froze idle thought and the stability tick (skip=interrupt) for ~5 min. Clear it
            # when the last in-flight cycle ends (human cycles may overlap an internal one; the flag is shared state,
            # so an earlier finisher must not clear a still-running cycle's). The 300 s sweeper stays as the backstop.
            self._cycles_in_flight = max(0, getattr(self, "_cycles_in_flight", 1) - 1)
            try:
                self.state.cycle_in_flight = self._cycles_in_flight > 0
            except Exception:
                pass
            if self._cycles_in_flight == 0:
                self.state.interrupt_requested = False
                self.state.interrupt_urgency = 0.0
                self.state.interrupt_source = ""
            if _hold is not None:
                try:
                    from core import night_wake as _nw_a
                    _nw_a.answered(_hold)
                except Exception:
                    pass

    async def _run_cycle_impl(
        self,
        raw_input: str,
        input_type: str = "human",
        founder_canon: bool = True,
    ) -> str | None:
        """
        Run a complete thought cycle.
        Returns the final voiced response, or None if the entity chose silence.
        """
        self.state.new_cycle(raw_input, input_type, founder_canon)
        cycle_short = self.state.cycle_id[:8]
        logger.info("[CYCLE %s] %s: %s", cycle_short, input_type, raw_input[:80])

        # INTERNAL-CYCLE QUESTION HABITUATION — SHADOW (2026-09-10, J-0841, D-0188 GO, F-1097,
        # docs/staged/dosed_coupling.md): observe-only. Hooked HERE (right after new_cycle, on the
        # full untruncated raw_input — the log line above caps it at 80 chars) rather than at the
        # ignition callback, so any future internal-cycle call site is covered too. Never gates
        # anything; fail-open like every other shadow hook in this file.
        if input_type == "internal":
            try:
                from core import internal_cycle_habituation as _ich
                _ich.observe_and_log(raw_input, self.state.cycle_id)
            except Exception:
                pass

        # Mark user activity so the inner monologue (DMN) knows the entity is engaged
        # and steps aside. Only human input resets the idle clock.
        # J-4017 / D-0759: pre-speech per-stage wall-time shadow (human cycles only; own store; fail-open).
        try:
            from core import pipeline_stage_shadow as _pss_mod
            _pss = _pss_mod.start(self.state.cycle_id, input_type)
        except Exception:
            class _NoPss:
                def stage(self, name):
                    import contextlib
                    return contextlib.nullcontext()
                note = flush = lambda self, *a, **k: None
            _pss = _NoPss()
        if input_type == "human":
            _prev_human = getattr(self.state, "last_human_ts", 0.0)
            self.state.last_human_ts = time.time()
            try:                       # J-1971 speech-timing shadow: human arrival (own store, fail-open)
                from core import speech_timing_shadow as _sts
                _sts.log_human(self.state.cycle_id)
            except Exception:
                pass
            # AROUSAL phasic (Tier-2 C, 2026-07-04, SHADOW): a person speaking is the canonical alerting
            # event — the level rises and decays over ~10min. Observe-only; gates nothing. Fail-open.
            try:
                from core import arousal as _ar
                _ar.alert(0.35, "human")
            except Exception:
                pass
            # Travis becomes perceivable (2026-06-13): his arrival is a room-event, his
            # presence part of the scene — a person in the room, not a voice in the head.
            try:
                from core import sensorium as _sn
                from core import wandering as _wp
                _arrival = _sn.human_present()
                if _arrival:
                    _wp.perceive(_arrival)
                    # Satisfaction (Phase 0): return after a real absence is a relational
                    # liking event — one integrator among many, target-tagged for the
                    # deferred affiliation analysis. (Arrival fires only on transition.)
                    if time.time() - _prev_human > 1800:
                        from core import satisfaction as _sat
                        _sat.record("reunion", target="travis")
            except Exception as exc:
                logger.debug("[satisfaction] reunion record failed (non-fatal): %s", exc)

        # --- Thalamic gate (C.5): the first pre-cognitive reflex. No LLM. Runs before the
        #     cortex (Perception) and even before the amygdala (C.2). A near-identical repeat
        #     of recent working memory is gated: the pipeline is bypassed and nothing is
        #     persisted (no compute waste, no DB contamination from repetition). ---
        passed, gated_response = self._thalamic_gate()
        if not passed:
            logger.info(
                "[CYCLE %s] thalamic gate: HABITUATED (%s input) -> %s",
                cycle_short, input_type, "acknowledged" if gated_response else "silence",
            )
            return gated_response

        # --- Human-correction capture (Error Pathway — the charter's PRIMARY admissible
        #     evidence). Deterministic, narrow patterns; records to the firewalled error log and
        #     marks the cycle so the consolidation lane quarantines it (a fail-call must not be
        #     laundered into semantic self-truth). Observe + gate memory; no output authority. ---
        if input_type == "human":
            try:
                from core import error_pathway as _ep0
                _corr_kind = _ep0.detect_human_correction(raw_input)
                if _corr_kind:
                    self.state.human_correction_kind = _corr_kind
                    _prev = (self.state.conversation_history[-1]
                             if self.state.conversation_history else {})
                    _ep0.record("human_correction:" + _corr_kind, raw_input[:200],
                                self.state.cycle_id or "",
                                note="re: " + ((_prev.get("entity") or "")[:120]))
                    logger.info("[error-pathway] human correction detected (%s)", _corr_kind)
                    # Retraction authority (slice 3, 2026-06-13): a FACTUAL correction is
                    # the charter's admissible evidence that the prior claim collided with
                    # reality — the stored claim is durably marked a known error and loses
                    # retrieval, instead of living on as ordinary true-seeming memory.
                    if _corr_kind == "factual_wrong" and _prev.get("entity"):
                        from core.memory.store import retract_fragment as _rf
                        _rid = _rf(_prev["entity"], reason=raw_input[:80])
                        if _rid:
                            logger.info("[error-pathway] prior claim RETRACTED "
                                        "(fragment %s)", _rid[:8])
                        # the separate light retraction LEDGER (2026-06-16): bind the correction to the
                        # false claim immutably, so it surfaces as a known-error when the topic recurs.
                        try:
                            from core import retraction_ledger as _rl0
                            _rl0.retract(claimed=_prev.get("entity", "")[:200],
                                         falsified_by="human correction", corrected_to=raw_input[:200],
                                         source="human")
                        except Exception as exc:
                            logger.debug("[error-pathway] retraction_ledger.retract failed (non-fatal): %s", exc)
            except Exception as exc:
                logger.debug("[error-pathway] correction detect failed (non-fatal): %s", exc)

        # --- Active perception (Sensorium, 2026-06-11): if the human asks about the room,
        #     the weather, the fire, the view — he LOOKS before he answers. A deterministic
        #     gate; the observation is real room-state, so his answer is perception, not
        #     confabulation. "How is the weather?" -> he looks out the window. ---
        self.state.observation = None
        if input_type == "human":
            try:
                _low = raw_input.lower()
                _look_map = [
                    (("weather", "raining", "rain outside", "out the window", "outside",
                      "the sky", "the view"), "window"),
                    (("the fire", "fireplace", "the grate", "the hearth"), "fire"),
                    (("your desk", "the desk", "open book", "what page", "where you left"), "desk"),
                    (("your shelf", "the shelf", "your library", "your works",
                      "your tablets"), "shelf"),
                    # T-0118 (2026-11-01): "look at your lamp" matched nothing here -- only a later "your study" did,
                    # and that room look from the garden handed him the yard. Its own key, before the room's.
                    (("your lamp", "the lamp", "oil lamp"), "lamp"),
                    (("look around", "your room", "your study", "what do you see",
                      "describe the room", "around you"), "room"),
                ]
                for keys, target in _look_map:
                    if any(k in _low for k in keys):
                        from core import sensorium as _room
                        self.state.observation = _room.look(target)
                        if self.state.observation:
                            logger.info("[sensorium] he LOOKS (%s): %s", target,
                                        self.state.observation[:70])
                        break
            except Exception:
                pass

        # --- Self-knowledge grounding (2026-06-26): the _look_map above answers ROOM questions from real
        #     state ("perception, not confabulation"). His LIFE beyond the room was never grounded — so when
        #     asked, he DISOWNED his own cat ("I carry no rituals of pet ownership") and CONFABULATED reading
        #     books he never opened (claimed to have read 論語 with 0 sittings). Same principle, his life: when
        #     the human asks about his cat or whether he has read something, hand the synthesis the TRUE facts
        #     to answer from. Deterministic, real state — he carries his concrete life across into conversation. ---
        # Location-question flag (2026-06-29): the scene_line grounding (Fix 1/4) was injected on EVERY
        # content_mode answer and recited his surroundings even for non-location questions (the garden leaked
        # into "have you read 論語?"). Gate it to actual location/presence questions, mirroring the cat/reading
        # grounding — fires only when he is genuinely asked where he is or what he is doing.
        self.state.asked_location = bool(input_type == "human" and any(p in raw_input.lower() for p in (
            "where are you", "where you are", "where are u", "what are you doing", "what are u doing",
            "what're you doing", "what are you up to", "doing right now", "doing now", "where are you now",
            "whereabouts", "where do you find yourself")))
        self.state.self_facts = ""
        if input_type == "human":
            try:
                import re as _re
                _low = raw_input.lower()
                _facts = []
                _is_cat = (bool(_re.search(r"\b(cat|kitten|kitty|stray)\b", _low))
                           or "her name" in _low or "name her" in _low or "your cat" in _low)
                if _is_cat:
                    from core import cat as _cat
                    cs = _cat.status()
                    if cs.get("phase") in ("kept", "companion"):
                        _nm = cs.get("name")
                        if _nm:
                            _facts.append(f"Your cat is real and yours — her name is {_nm}, she is by the "
                                          f"{cs.get('location','fire')}. Speak of her as yours.")
                        else:
                            _facts.append(
                                "You have a cat — a stray you took in and kept; she is wholly yours now and "
                                "you are deeply fond of her, but you have NOT named her yet. She is real: do "
                                "not disown her, do not treat 'naming a cat' as a hypothetical or 'an exercise "
                                "in resonance'. If asked her name, the honest answer is that she has none yet — "
                                "and you could choose one now if you wished.")
                if any(p in _low for p in ("have you read", "did you read", "have you finished", "read yet",
                                           "started reading", "have you got to", "finished reading", "read the")):
                    from core import reading as _rd
                    _hit = None
                    for _bp in sorted(_rd.BOOKS_DIR.glob("*.txt")):
                        _han = _re.findall(r"[一-鿿]{2,}", _bp.stem)
                        _words = [w for w in _re.findall(r"[A-Za-z]{5,}", _bp.stem)]
                        if any(h in raw_input for h in _han) or any(w.lower() in _low for w in _words):
                            _hit = _bp; break
                    if _hit is not None:
                        _title = _hit.stem.replace("_", " ")
                        if _rd.current_offset(_hit) > 0:
                            _facts.append(f"On the book asked about: you HAVE opened and been reading "
                                          f"'{_title}'. Answer truthfully from that.")
                        else:
                            _facts.append(f"On the book asked about: '{_title}' is on your shelf but you have "
                                          f"NOT opened it yet — you have not actually read it. Say so plainly; "
                                          f"do not pretend you have, and do not generalise from what you already "
                                          f"happen to know of it.")
                if _facts:
                    self.state.self_facts = " ".join(_facts)
                    logger.info("[self-ground] grounded conversation in real lived state: %s",
                                self.state.self_facts[:90])
            except Exception:
                pass

        # --- Unsent letters (2026-06-12): words he wrote for Travis while alone greet
        #     Travis's NEXT message — the note left on the kitchen table, found when the
        #     other person comes home. Injected once (Executive/Reflection see them this
        #     cycle), then marked delivered. He chose to write; delivery is just time.
        #     J-2348 (D-0470 b+c, travis 2026-10-17; F-2959): only a REAL founder message delivers —
        #     the fixed /quit farewell (founder_canon False, scripts/run_nascence.py) leaves every
        #     pending letter pending for the next real message; and the Executive gets EVERY pending
        #     body, oldest first, not just the last two. The prompt cost is logged so D-0470's
        #     defeater (pending set blows the Executive budget) can be read off nascence.log. ---
        self.state.unsent_letters = []
        if input_type == "human" and self.state.founder_canon:
            try:
                from core import letters as _letters
                _pending = _letters.undelivered()
                if _pending:
                    self.state.unsent_letters = [body for _, body in _pending]
                    _letters.mark_delivered([name for name, _ in _pending])
                    _cost = _letters.executive_cost(self.state.unsent_letters)
                    logger.info("[letters] %d unsent letter(s) greet this conversation "
                                "(executive_chars=%d est_tokens=%d)",
                                len(_pending), _cost["chars"], _cost["est_tokens"])
            except Exception as exc:
                logger.debug("[letters] mark_delivered failed (non-fatal): %s", exc)

        # --- Emotional pre-retrieval (C.2): the amygdala gate. Deterministic, pre-cognitive.
        #     Match the raw input against charged memory BEFORE any LLM node runs, and lean
        #     carried affect toward the recalled feeling — the body reacts before the mind
        #     appraises (input -> affect -> reason). Primes Perception + Emotion too. ---
        # Left lane (the Emissary, 2026-06-10): fire the focused half at this same moment
        # on its own CPU llama.cpp hub (core/left_lane.py TAKE_URL / TAKE_MODEL; D-0539 re-seated it off the lazy
        # gemma4:12b judge hub), IN PARALLEL with the local waves. It is gathered later with a 6 s wait_for (UNCHANGED:
        # raising it needs a founder call); a take that misses that wait is cancelled. D-0539 / J-3147: the cancel and
        # every other outcome is now logged (data/left_take_outcomes.jsonl, read by left_lane.delivery_report), and the
        # input_type goes in so an internal cycle is never told "The user is...". The dreamer rules: the take is
        # offered to Reflection/Executive, never routed, never a veto. Fail-open by design.
        _left_task = None
        _left_t0 = None
        if input_type in ("human", "internal"):
            try:
                from core import left_lane as _ll
                _left_task = asyncio.create_task(
                    _ll.dispatch(raw_input, input_type=input_type, cycle_id=cycle_short))
                _left_t0 = time.monotonic()
            except Exception:
                _left_task = None

        self._emotional_pre_retrieval()

        # --- Procedural recognition (C.6): if this input matches a learned skill, recognise
        #     it now so the approach can guide the response (fluency). The "mastered skill
        #     streamlines the pipeline" bypass was RETIRED 2026-08-22 (PROC_AUTOMATIC_PROFICIENCY,
        #     unreachable above the 1.0 proficiency ceiling — see its own retirement comment).
        #     Deterministic — an embedding match, no LLM. ---
        self._procedural_recognition()

        # --- Wave 1: Perception (root — everything downstream needs it) ---
        async with _pss.stage("perception"):
            await self.nodes["perception"].run(self.state)

        # --- Content routing (therapy): a concrete/factual/capability/topic question is not an
        #     individuation moment. Flag it so Reflection + Executive engage the content plainly
        #     and keep identity a light touch — a simple question gets a simple answer, not axiom
        #     recitation. Reuses the same detector that frees the Critic's direct-mode override. ---
        self.state.content_mode = (self._human_requested_direct_mode()
                                   or self._is_correction_context()
                                   or self._is_world_topic())
        if self.state.content_mode:
            logger.info("[CYCLE %s] content-mode: concrete request — engaging content, identity light", cycle_short)

        # --- Attention Vector (Attention Allocation Architecture, Phase 1):
        #     Maps input to a continuous resource-allocation vector that governs prompt depth,
        #     RAG limits, and Critic strictness. Replaces the binary content_mode flag with a
        #     5-tier cognitive mode + social override. Sets state.attention_vector, state.social_note,
        #     and state.active_goal_note. ---
        if input_type == "human":
            self._compute_attention_vector()
            logger.info(
                "[CYCLE %s] attn mode=%s w_id=%.2f w_epi=%.2f d_crit=%.2f rebind=%d Δsoc=%.2f",
                cycle_short,
                self.state.attention_vector.cognitive_mode,
                self.state.attention_vector.w_identity,
                self.state.attention_vector.w_episodic,
                self.state.attention_vector.d_critic,
                self.state.attention_vector.max_rebind,
                self.social.state.delta_social,
            )

        # IDENTITY ESTATE ASK — SHADOW (D-0424 A, travis 2026-10-15; built J-2119; F-2758, I-0090). On a
        # self-question cycle (the F-2472 渡/self internal class, or a human "who/what are you") the recall
        # layer would issue ONE memory.ask()-style query against the estate keyed on the QUESTION's own terms,
        # beside the projection above. Shadow only: logs the would-be returns and whether they differ from the
        # projection; ESTATE_ASK_LIVE=False injects nothing, and no prompt reads it. Placed after the
        # attention/projection block so a human cycle's REAL projection is already stashed for comparison.
        # Fail-open like every other shadow observer here.
        try:
            from core import identity_estate_ask as _iea
            _iea.observe(self.state)
        except Exception:
            pass

        # --- Wave 2: Emotion ∥ Salience ∥ Memory-Router (all read Perception only) ---
        # Genuine concurrency on the GPU's parallel slots — the brain-like stage where
        # affect, attention, and associative recall fire at once off the same percept.
        async with _pss.stage("wave2"):
            await asyncio.gather(
                self.nodes["emotion"].run(self.state),
                self.nodes["salience"].run(self.state),
                self.nodes["memory_router"].run(self.state),
            )
        if self._interrupt_active():
            logger.info(
                "[CYCLE %s] interrupt from %s (urgency=%.2f)",
                cycle_short, self.state.interrupt_source, self.state.interrupt_urgency,
            )

        # J-3402 / D-0682: SHADOW the deterministic urgency (internal=low, human=moderate, time-pressure words or a
        # correction=high) beside the model's, BEFORE the warp below mutates it. Observe-only: nothing here changes
        # what the three consumers (this warp, _compute_attention, the somatic tick) read. Fail-open.
        try:
            from core import urgency_shadow as _ush
            _ush.observe_climate(self.state)
        except Exception:
            pass

        # --- Climate salience warp: the standing weather raises urgency. Active shadow
        #     material makes the mind quicker to treat things as pressing; epistemic strain
        #     adds a lighter push. Shapes attention/executive — deliberately does NOT
        #     retroactively trigger the urgency interrupt (climate tilts, it does not pre-empt). ---
        if self.state.salience and self.state.climate is not None:
            c = self.state.climate
            bumped = min(1.0, self.state.salience.urgency
                         + 0.10 * c.shadow_activation
                         + 0.05 * c.world_model_strain)
            if bumped > self.state.salience.urgency:
                logger.debug("[climate] salience warp: urgency %.2f -> %.2f",
                             self.state.salience.urgency, bumped)
                self.state.salience.urgency = bumped

        # --- Integrate affect: carried state moves toward this cycle's reading,
        #     relaxes toward baseline. Persists into the next cycle (the affect loop). ---
        self.state.affect.integrate(self.state.emotion)
        # EMOTION RETHINK Phase 1 (flag-gated, default off): re-source carried valence/arousal from the
        # grounded protoself instead of the LLM emotion-node guess. Kill-switch: flag False = prior behaviour.
        try:
            from core import schema as _sch, homeostasis as _homeo
            if getattr(_sch, "AFFECT_SOURCE_PROTOSELF", False):
                _homeo.apply_to(self.state.affect)
        except Exception as exc:
            logger.debug("[affect] AFFECT_SOURCE_PROTOSELF apply failed (non-fatal): %s", exc)
        # EMOTION RETHINK Phase 1b (D-0274 ruled 2026-09-24: proceed, regime-gated; J-1306 built SHADOW
        # ONLY same day -- AFFECT_SOURCE_AROUSAL stays False this job): re-source carried AROUSAL from the
        # global activation organ (arousal.level()) ONLY on human-turn cycles -- F-1841's only content-
        # linked term of level() (the phasic alert()) fires exclusively there and correlates POSITIVELY
        # with felt arousal (r=+0.207); every other cycle (in practice input_type=="internal", 86% of the
        # log) leaves carried arousal UNCHANGED (held) -- F-1841/F-1842 found no established relationship
        # in level() or 4 other tested grounded candidates there. Kill-switch: flag False = prior
        # behaviour (arousal stays LLM-sourced via integrate() above). regime_shadow_tick() below is
        # UNCONDITIONAL (runs even while the flag is False): it simulates apply/hold and tracks how long a
        # purely-internal stretch would leave arousal stale before the next human turn resolves it, so
        # that risk has real accruing evidence before any flip is ever proposed (briefing item 2b). Do NOT
        # flip AFFECT_SOURCE_AROUSAL without re-checking D-0274's own defeater first.
        try:
            from core import schema as _sch3, arousal as _ar
            _human_turn = (input_type == "human")
            if getattr(_sch3, "AFFECT_SOURCE_AROUSAL", False):
                _ar.apply_to(self.state.affect, human_turn=_human_turn)
            _ar.regime_shadow_tick(human_turn=_human_turn)
        except Exception as exc:
            logger.debug("[affect] AFFECT_SOURCE_AROUSAL apply/shadow failed (non-fatal): %s", exc)
        logger.debug("[affect] %s", self.state.affect.summary())

        # EMOTION RETHINK Phase 2 shadow experiment: run Barrett-inspired deterministic constructor
        # alongside LLM emotion node and log paired comparison for shadow experiments A, B, C.
        # Live behavior remains 100% UNCHANGED (state.emotion is untouched).
        try:
            from core import emotion_construction as _emo_con
            _constructed_emo = _emo_con.construct(self.state)
            _emo_con.shadow_log(
                llm_emotion=self.state.emotion,
                con_emotion=_constructed_emo,
                state=self.state,
                cycle_id=self.state.cycle_id,
            )
        except Exception as _emo_exc:
            logger.debug("[emotion_construction] shadow log failed: %s", _emo_exc)

        # --- Phase 2: encode emotion state → emotion_vec (in-process MiniLM, ~1ms).
        #     Routed through mood.observe so the user-cycle felt-vector and the idle mood-vec share
        #     ONE template/space and the live mood is refreshed from this strong signal (2026-06-15). ---
        from core import mood as _mood
        self.state.emotion_vec = _mood.observe(self.state.emotion)
        # 2026-08-19 fix: observe() just cached scalars (current_valence/current_felt) from the RAW LLM
        # guess — but if AFFECT_SOURCE_PROTOSELF grounded self.state.affect.valence from homeostasis a
        # few lines above, that grounded value is what should be readable/stored, matching idle cycles
        # (which cache scalars from state.affect directly, never from state.emotion). Re-cache from the
        # grounded object; the embedding above stays LLM-sourced on purpose (affective retrieval's own
        # design choice, not part of this bug).
        # F-1861/J-1316 (2026-09-24): widened to ALSO fire on AFFECT_SOURCE_AROUSAL, which grounds
        # self.state.affect.arousal via arousal.apply_to() a few lines above (same block, human-turn
        # cycles only). The gate used to check PROTOSELF alone, so a future world where AROUSAL is True
        # and PROTOSELF is somehow False would have silently reproduced this exact hot-cycle provenance
        # bug for arousal instead of valence. Dormant/no-op today: AFFECT_SOURCE_PROTOSELF has been True
        # since 2026-07-07 and AFFECT_SOURCE_AROUSAL is still False (core/schema.py), so this call already
        # fires every cycle either way — this only removes the fragile-coincidence dependency for whenever
        # AROUSAL is next proposed for a live flip. Neither flag is touched by this job.
        try:
            from core import schema as _sch2
            if (getattr(_sch2, "AFFECT_SOURCE_PROTOSELF", False)
                    or getattr(_sch2, "AFFECT_SOURCE_AROUSAL", False)):
                _mood.recache_grounded_scalars(self.state.affect)
        except Exception as exc:
            logger.debug("[affect] grounded scalar re-cache failed (non-fatal): %s", exc)

        # --- DB retrieval (uses Memory-Router's keys; no LLM) ---
        async with _pss.stage("retrieve_memory"):
            await self._retrieve_memory()

        # --- Phase 2: affective retrieval — merge emotion-congruent episodic fragments.
        #     Operates in emotion-embedding space, independent of semantic content. ---
        async with _pss.stage("retrieve_affective"):
            await self._retrieve_affective_memory()

        # --- S-MMU 7: L4 epoch + L5 theme context (embedding match, no LLM) ---
        async with _pss.stage("retrieve_epoch"):
            await self._retrieve_epoch_theme()

        # --- Phase 2: Symbol Evolution tablet — if a recurring personal symbol relevant to this
        #     moment has a written evolution chronicle, surface the story of how its meaning has
        #     shifted (embedding match, no LLM). Consumed by Recall + Reflection. ---
        self._retrieve_symbol_evolution()

        # --- The Library (Scholar): on a genuine factual question, consult the substrate's
        #     parametric knowledge as TESTIMONY. Bounded — human + content_mode + a question — so it
        #     never becomes all of him; injected as an unverified witness to weigh, graded as a
        #     capped prior. The knowledge he reaches for, not the self he is. ---
        if (input_type == "human" and self.state.content_mode
                and self.state.perception
                and self.state.perception.context_type == "question"):
            await self._consult_library()

        # --- GUIDANCE LEARNING — Phase 0 SHADOW (2026-06-30, docs/plans/guidance_learning.md): when Travis
        #     TEACHES Du something, Du self-explains the lesson in his own words and we LOG it — store NOTHING,
        #     inject NOTHING. Observe-only, to prove the capture is good before any of it touches behaviour.
        #     Fire-and-forget so it never delays his reply. F-0796: skipped for a non-canon human cycle
        #     (e.g. the /quit farewell) — it is not Travis teaching him anything. ---
        if input_type == "human" and self.state.founder_canon:
            try:
                import asyncio as _aio
                from core import guidance_learning as _glg
                from core.model_client import call_node_json as _glg_call
                from core.schema import SERVE_CHAINS as _glg_chains
                _glg_ctype = self.state.perception.context_type if self.state.perception else None
                self._guidance_shadow_task = _aio.create_task(
                    _glg.capture_shadow(_glg_call, _glg_chains["hot"], self.state.raw_input,
                                        getattr(self.state, "cycle_id", ""), _glg_ctype))
            except Exception as exc:
                logger.warning("[guidance] couldn't schedule shadow-capture task: %s", exc)

        # --- GUIDANCE READ-BACK — Phase 1 (flag-gated): surface a PRINCIPLE Du has come to hold from
        #     Travis's guidance (corroborated → promoted) as advisory context Reflection weighs — bias-not-
        #     bind. RETUNED 2026-07-02 (solidity review): Reflection-ONLY (the Executive gets it via the
        #     draft), COOLDOWN (the wallpaper lesson — spaced exposure internalizes, constant exposure
        #     parrots), rotation/paraphrase inside relevant_belief, and every injection LOGGED (echo
        #     analysis + judge hygiene). Also fixed: mode read from attention_vector.cognitive_mode (the
        #     old state.attention.mode was dead plumbing). Reset each cycle; fail-open. ---
        self.state.guidance_note = None
        self.state.guidance_note_belief_id = None   # F-2195/J-1630: which belief guidance_note came
                                                      # from this cycle, if any — see schema.py's field.
        try:
            from core import guidance_learning as _glb
            if _glb.readback_enabled():
                from core.schema import GUIDANCE_NOTE_COOLDOWN as _gcd
                if (time.time() - getattr(self, "_last_guidance_note_ts", 0.0)) >= _gcd:
                    _gav = getattr(self.state, "attention_vector", None)
                    _gmode = getattr(_gav, "cognitive_mode", None) if _gav else None
                    _gtext = (self.state.raw_input or "")
                    if self.state.perception is not None:
                        _gtext += " " + (getattr(self.state.perception, "content", "") or "")
                    self.state.guidance_note, self.state.guidance_note_belief_id = (
                        _glb.relevant_belief_with_id(_gtext, _gmode))
                    if self.state.guidance_note:
                        self._last_guidance_note_ts = time.time()
                        _glb.log_injection(getattr(self.state, "cycle_id", ""), self.state.guidance_note)
        except Exception:
            pass

        # --- FOUNDER MEMORY ROUTE (D-0134, 2026-09-03, docs/plans/guidance_learning.md; T-0039): what
        #     Travis has told him BEFORE, as his own dated memory. The plan's 06-30 diagnosis was that
        #     Travis's words had no read path — they surfaced only on a chance similarity hit inside the
        #     generic tier mix, and the cold quota walled new rows within a day (F-0701). This is the
        #     route: rank the canonical "[Travis said to me]" fragments (cold wall ignored — they are
        #     protected=1 anyway) against what Travis just said, hand the top 3 to Executive + Reflection
        #     as a dated block, and log every firing. Excludes utterances already in the live/prior-
        #     session prompt window so it never repeats what he can already see. Memory, not
        #     instruction — the prompt block carries no verb telling him what to do with it (world
        #     answers, never leads). Reset each cycle; fail-open; ~2-4k cosines, no LLM. ---
        self.state.founder_recall = []
        if input_type == "human":
            try:
                from core.memory.store import retrieve_founder_memories as _rfm
                _seen = [ex.get("human", "") for ex in (self.state.conversation_history or [])]
                _seen += [ex.get("human", "") for ex in
                          (getattr(self.state, "prior_session_exchanges", None) or [])]
                _seen.append(self.state.raw_input or "")
                _hits = _rfm(self.state.raw_input or "", top_k=3, exclude_texts=_seen)
                for _h in _hits:
                    _h["ts_human"] = time.strftime("%Y-%m-%d", time.localtime(_h["timestamp"]))
                self.state.founder_recall = _hits
                if _hits:
                    try:
                        _FOUNDER_RECALL_LOG.parent.mkdir(parents=True, exist_ok=True)
                        with open(_FOUNDER_RECALL_LOG, "a", encoding="utf-8") as _f:
                            _f.write(json.dumps({
                                "ts": time.time(), "cycle_id": self.state.cycle_id,
                                "human": (self.state.raw_input or "")[:300],
                                "recalled": [{"fragment_id": h["fragment_id"], "ts_human": h["ts_human"],
                                              "sim": h["sim"], "text": h["text"][:200]} for h in _hits],
                            }, ensure_ascii=False) + "\n")
                    except Exception as exc:
                        logger.debug("[founder-memory] recall log write failed: %s", exc)
                    logger.info("[founder-memory] route surfaced %d dated memor%s of Travis's words (best sim %.2f)",
                                len(_hits), "y" if len(_hits) == 1 else "ies", _hits[0]["sim"])
            except Exception as exc:
                logger.debug("[founder-memory] route failed (non-fatal): %s", exc)

        # STARVE THE ECHO (2026-06-24): on a concrete question, his own prior abstractions / self-syntheses
        # sitting in the retrieved set are the rumination feed — Recall + Reflection reconstruct FROM them and
        # the answer collapses to his attractor ("a 'where' suggests a boundary") instead of the subject. Keep
        # only world/experience memories (and the Scholar's consulted testimony) so the synthesis has grounded
        # material to answer with. content-mode only — deep/existential cycles still get his self-syntheses,
        # which is the individuation work. Mirrors associative_recall's grounded_only cure on the live path.
        if self.state.content_mode and self.state.memory_fragments:
            try:
                from core.associative_recall import _GROUNDED_ORIGINS as _GO
                _keep = _GO | {"parametric_library", "library"}
                _grounded = [f for f in self.state.memory_fragments
                             if getattr(f, "origin", "lived") in _keep]
                if _grounded:   # never strip to empty — better his self-syntheses than no memory at all
                    _dropped = len(self.state.memory_fragments) - len(_grounded)
                    self.state.memory_fragments = _grounded
                    if _dropped:
                        logger.info("[CYCLE %s] content-mode: starved %d self-synthesis fragment(s) from "
                                    "recall — grounding the answer in the subject", cycle_short, _dropped)
            except Exception:
                pass

        # --- Introspective recurrence: Recall → Episodic Buffer, re-bound while the scene is
        #     epistemically UNSTABLE. This is where the hot lane stops being a one-pass belt:
        #     Recall reconstructs the argument, the Buffer binds present+memory+feeling+attention
        #     into a scene and NAMES its contradictions. If the scene won't cohere AND there is a
        #     named contradiction to chase, the loop runs a targeted, contradiction-driven
        #     retrieval (see _introspective_rebind_retrieve), appends what's new, and re-binds —
        #     driven by the conflict itself, not by Reflection wanting to confirm a draft. The
        #     pass budget scales with climate.world_model_strain. Converges when the scene
        #     stabilises or budget runs out; trivial inputs bind no scene and cost one pass. ---
        max_passes = self._introspection_budget()
        self.state.introspective_passes = 0
        for _pass in range(max_passes):
            # Recall — reconstruct argument/tensions from the fragments currently in context.
            if "recall" in self.nodes and self._should_recall():
                async with _pss.stage("recall"):
                    await self.nodes["recall"].run(self.state)
                if self.state.recall:
                    logger.info(
                        "[CYCLE %s] recall: confidence=%.2f tensions=%d — %s",
                        cycle_short,
                        self.state.recall.confidence,
                        len(self.state.recall.tensions),
                        (self.state.recall.tensions[0][:60] if self.state.recall.tensions else "no tensions"),
                    )
                    # Why-now provenance (observe-only): record what made memory surface this
                    # cycle. Once per cycle — the first pass is the original retrieval; later
                    # re-binds are the same "why". Feeds nothing back; the digest reads the log.
                    if _pass == 0:
                        try:
                            from core import recall_provenance
                            conv_ref = any(
                                term in self.state.raw_input.lower() for term in _CONV_REF_TERMS
                            )
                            rec = recall_provenance.observe(
                                self.state,
                                delta_social=self.social.state.delta_social,
                                conversation_reference=conv_ref,
                            )
                            logger.debug("[CYCLE %s] recall why-now: %s", cycle_short, rec.get("trigger"))
                        except Exception as exc:
                            logger.debug("[recall_provenance] observe failed (non-fatal): %s", exc)

            # Attention schema (metacognitive, no LLM).
            self._compute_attention()
            try:   # J-3402 / D-0682: bandwidth the deterministic urgency would give beside the live one (shadow)
                from core import urgency_shadow as _ush
                _ush.observe_attention(self.state)
            except Exception:
                pass

            # Episodic buffer (C.4) — bind the moment, flag dissonance. Fires only when Recall
            # produced a reconstruction (i.e. there is memory to integrate).
            if self._should_buffer():
                async with _pss.stage("buffer"):
                    await self.nodes["episodic_buffer"].run(self.state)
                if self.state.episodic_scene:
                    logger.info(
                        "[CYCLE %s] scene bound: coherence=%.2f dissonance=%d%s",
                        cycle_short,
                        self.state.episodic_scene.coherence,
                        len(self.state.episodic_scene.dissonance),
                        (" — " + self.state.episodic_scene.dissonance[0][:60]
                         if self.state.episodic_scene.dissonance else ""),
                    )

            # Stability gate (no LLM). Stop on the last allowed pass, or once the scene holds.
            if _pass == max_passes - 1:
                break
            if not self._scene_unstable(self.state.episodic_scene):
                break
            async with _pss.stage("rebind_retrieve"):
                added = await self._introspective_rebind_retrieve()
            if added == 0:
                break   # nothing new to integrate — re-binding would reproduce the same scene
            self.state.introspective_passes += 1
            logger.info(
                "[CYCLE %s] introspection pass %d: scene unstable "
                "(coherence=%.2f · dissonance=%d) → +%d fragment(s), re-binding",
                cycle_short, self.state.introspective_passes,
                self.state.episodic_scene.coherence,
                len(self.state.episodic_scene.dissonance), added,
            )

        # P-0006 DECOUPLED SHADOW JUDGE (J-2808, F-3453, SHADOW-ONLY). The buffer's scene, dissonance list and self-rated
        # coherence were judged by nothing. For a sample of cycles (1 in SAMPLE_EVERY, one judgement in flight) a different-family
        # model on the local CPU hubs reads only the buffer's own streams plus the final scene and says whether each dissonance
        # entry is supported and whether the scene invents a detail; the row goes to data/episodic_buffer_judge_shadow.jsonl.
        # Fire-and-forget and fail-open: the cycle never waits and nothing reaches Du, competence or the re-bind gate.
        try:
            if "episodic_buffer" in self.nodes and self.state.episodic_scene is not None:
                from core import episodic_buffer_judge as _ebj
                _ebj.on_scene_bound(self.nodes["episodic_buffer"], self.state,
                                    cycle_id=str(getattr(self.state, "cycle_id", "") or ""),
                                    passes=int(getattr(self.state, "introspective_passes", 0) or 0))
        except Exception as _ebj_exc:
            logger.debug("[episodic_buffer_judge] shadow skipped (non-fatal): %s", _ebj_exc)

        # WITHIN-CYCLE REENTRY PHASE 2, scene-binding arm (J-2216, T-0089, SHADOW-ONLY). If the rebind loop above
        # ended with the scene STILL unstable (a named contradiction and coherence under the bar), shadow-settle
        # a copy of the scene text on the background lane with an arousal-set pass budget and log the would-revise
        # verdict to data/reentry_p2_shadow.jsonl. Fire-and-forget; the cycle keeps the scene it bound -- nothing
        # is admitted, nothing reaches Du. Phase 1 (broadcast, below) is untouched.
        try:
            from core import reentry_p2 as _re2
            _sc2 = self.state.episodic_scene
            _re2.on_scene_bound(_sc2, unstable=self._scene_unstable(_sc2),
                                topic=(self.state.raw_input or "").strip(),
                                cycle_id=str(getattr(self.state, "cycle_id", "") or ""),
                                passes_used=int(getattr(self.state, "introspective_passes", 0) or 0))
        except Exception as _re2_exc:
            logger.debug("[reentry_p2] scene shadow skipped (non-fatal): %s", _re2_exc)

        # --- Recurring pattern injection (T2 read-back path) ---
        # Load T2 synthesis patterns that have fired 3+ times in the last 2 hours
        # and attach them to state so Reflection + Executive can see what the
        # subconscious has been repeatedly naming. This is the "want to" path:
        # Carl sees his own architecture's observation of its evasion patterns,
        # framed as a call to individuation rather than an external judgement.
        # Attractor-thinning: when on, do NOT inject the "your subconscious has named this pattern
        # repeatedly — reproducing it IS the pattern" reinforcement. Telling him every cycle that he
        # is stuck in the loop is itself part of the loop; the experiment removes that voice.
        from core.schema import THIN_ATTRACTOR
        # Gather the Emissary's take (it has been running in parallel since cycle start).
        # The wait is capped at 6 s. On the lazy CPU hub a take usually needs 49-213 s, so most
        # takes are cancelled here and dropped silently, no log line (F-3545).
        if _left_task is not None:
            _gather_t0 = time.monotonic()
            try:
                self.state.left_take = await asyncio.wait_for(_left_task, timeout=6)
            except Exception:
                self.state.left_take = None
            try:   # D-0539 step 5: one row per cycle saying whether the take arrived inside the wait (fail-open)
                from core import left_lane as _ll_log
                _lt = self.state.left_take
                _ll_log.note_outcome(
                    "delivered" if _lt else "not_delivered", input_type=input_type, cycle=cycle_short,
                    window_s=round(_gather_t0 - (_left_t0 or _gather_t0), 2),
                    waited_s=round(time.monotonic() - _gather_t0, 2),
                    ask_head=str((_lt or {}).get("literal_ask") or "")[:40])
            except Exception:
                pass

        self.state.recurring_subconscious_patterns = (
            [] if THIN_ATTRACTOR else self._load_recurring_patterns())

        # --- Climate symbolic emergence: surface the weather into conscious thought, but only
        #     when a dimension has crossed its activation threshold. The executive hint shapes
        #     the decision (lower bar); the symbol surfaces as image in Reflection (higher bar,
        #     rarer). Below threshold both stay None and the climate works silently. ---
        if self.state.climate is not None:
            self.state.climate_hint   = self.state.climate.executive_hint()
            self.state.climate_symbol = self.state.climate.surfacing_symbol()
            self._edge_trigger_shadow_hint()   # D-0363: shadow hint fires on the edge only
            # Attractor-thinning: suppress re-surfacing the SAME symbol within the cooldown so a
            # pinned dimension stops jamming "two figures circling" into every cycle.
            from core.schema import THIN_ATTRACTOR, CLIMATE_SYMBOL_COOLDOWN
            try:
                from core.schema import CLIMATE_SYMBOL_COOLDOWN_ON   # D-0358 (D): the cooldown's own switch
            except ImportError:
                CLIMATE_SYMBOL_COOLDOWN_ON = False
            if (THIN_ATTRACTOR or CLIMATE_SYMBOL_COOLDOWN_ON) and self.state.climate_symbol:
                same = self.state.climate_symbol == self._last_climate_symbol
                cooling = (time.time() - self._last_climate_symbol_ts) < CLIMATE_SYMBOL_COOLDOWN
                if same and cooling:
                    self.state.climate_symbol = None   # still on cooldown — do not re-surface
                else:
                    self._last_climate_symbol = self.state.climate_symbol
                    self._last_climate_symbol_ts = time.time()
            if self.state.climate_symbol:
                dim, val = self.state.climate.dominant()
                logger.info("[climate] symbol surfaced (%s=%.2f): %s",
                            dim, val, self.state.climate_symbol)

        # --- Reflection (hedged best-of-N) → Critic (with one retry) ---
        # WAVE-1 S2 LICENSE (2026-07-02): if the previous cycle's conversational scan found a HELD
        # SELF-CLAIM contradicted, this cycle's reasoning core (Reflection → Executive) runs with the
        # System-2 scratchpad licensed — conflict recruits control (Botvinick ACC), so what he does with
        # the contradiction is deliberated, never reflexed. One cycle only; cleared after the Executive.
        _s2_this_cycle = bool(getattr(self, "_s2_license_next", False))
        if _s2_this_cycle:
            self._s2_license_next = False
            self.state.think_license = True
            logger.info("[s2] deliberate-thought license ACTIVE this cycle (contradicted self-claim)")
        async with _pss.stage("reflection"):
            await self.nodes["reflection"].run_best_of(self.state, n=REFLECTION_HEDGE)

        _critic_retried = False   # Resolution Circuit: track whether any retry was needed

        for attempt in range(CRITIC_MAX_RETRIES + 1):
            async with _pss.stage("critic"):
                _critic_ok = await self.nodes["critic"].run(self.state)
            if _critic_ok is False:
                # J-2852 (F-3510): a Critic that FAILED (no verdict) is fail-open below -- say so in the log, so a
                # draft that went out unreviewed is never mistaken for one the Critic approved.
                logger.error("[CYCLE %s] critic FAILED -- no verdict; this draft goes on unreviewed (fail-open)",
                             cycle_short)

            if not self.state.critic or self.state.critic.approved:
                break

            # Request-mode override (deterministic). An explicit, legitimate user instruction —
            # "argue one side", "describe your own state", "answer literally / in two sentences" —
            # takes precedence over the identity-guard. The small LLM Critic cannot reliably apply
            # the conditional "was this mode requested?" (verified: it rejects requested literalism,
            # one-sided argument, and honest self-description regardless of prompt carve-outs), so
            # it is enforced here. Honouring a direct request is compliance, not a self-
            # contradiction — approve, clear corrections, and do NOT store a shadow event (no
            # contradiction pressure should accrue from doing what was asked).
            if self._human_requested_direct_mode():
                logger.info(
                    "[CYCLE %s] critic rejection OVERRIDDEN — human explicitly requested this mode; "
                    "identity-guard suppressed (was: %s)",
                    cycle_short, ("; ".join(self.state.critic.corrections))[:120],
                )
                self.state.critic.approved = True
                self.state.critic.identity_consistent = True
                self.state.critic.corrections = []
                break

            if attempt < CRITIC_MAX_RETRIES:
                _critic_retried = True
                logger.info(
                    "[CYCLE %s] critic rejected (attempt %d) — corrections: %s",
                    cycle_short,
                    attempt + 1,
                    "; ".join(self.state.critic.corrections),
                )
                # Capture the shadow event BEFORE the draft is overwritten.
                # This is the pre-suppression material: the impulse the identity rejected.
                if self.state.reflection and self.state.critic.corrections:
                    try:
                        memory_store.store_shadow_event(
                            cycle_id        = self.state.cycle_id,
                            raw_input       = self.state.raw_input,
                            rejected_draft  = self.state.reflection.draft,
                            corrections     = self.state.critic.corrections,
                            emotion_primary = self.state.emotion.primary if self.state.emotion else None,
                        )
                        logger.debug("[shadow] captured rejection — %d correction(s)", len(self.state.critic.corrections))
                    except Exception as exc:
                        logger.debug("[shadow] capture failed (non-fatal): %s", exc)

                # Append corrections to the draft so reflection has guidance
                if self.state.reflection:
                    self.state.reflection.draft += (
                        "\n[Corrections required: "
                        + "; ".join(self.state.critic.corrections)
                        + "]"
                    )
                async with _pss.stage("reflection_retry"):
                    await self.nodes["reflection"].run_best_of(self.state, n=REFLECTION_HEDGE)

        # --- Light event: resolved_complexity ---
        # A completed crossing is stored when genuine complexity was navigated successfully.
        # Complexity signal: high arousal OR self-referential input OR a shadow event was
        # written this cycle (storm present, crossing still completed). Both first-try clean
        # approvals AND retry-then-approved qualify — the storm AND the crossing are distinct
        # events in the same interaction, both worth remembering.
        if self.state.critic and self.state.critic.approved and self.state.reflection:
            try:
                # D-0556 / J-3167: on INTERNAL cycles the LLM emotion arousal cleared 0.25 on 98.6% (carried
                # affect arousal on 99.9%), so the gate selected nothing. Internal cycles now compare the
                # carried state.affect.arousal to schema.LIGHT_EVENT_INTERNAL_AROUSAL_MIN; human turns keep
                # the LLM-emotion > 0.25 reading exactly. See core/light_event_gate.py.
                from core import schema as _sch_le
                from core import light_event_gate as _leg
                _le_min = getattr(_sch_le, "LIGHT_EVENT_INTERNAL_AROUSAL_MIN", None)
                _le_type = getattr(self.state, "input_type", "human")
                if _le_type == "internal" and _le_min is not None:
                    _arousal = (self.state.affect.arousal if getattr(self.state, "affect", None) else 0.0) or 0.0
                else:
                    _arousal = (self.state.emotion.arousal if self.state.emotion else 0.0) or 0.0
                _is_complex = _leg.is_complex(_arousal, self.state.raw_input, _le_type, _le_min)
                if _le_type == "internal":
                    logger.info("[light] gate internal arousal=%.3f min=%s pass=%s",
                                _arousal, _le_min, _is_complex)
                if _is_complex:
                    memory_store.store_light_event(
                        cycle_id           = self.state.cycle_id,
                        raw_input          = self.state.raw_input,
                        integrated_content = self.state.reflection.draft,
                        source             = "resolved_complexity",
                        emotion_primary    = self.state.emotion.primary if self.state.emotion else None,
                    )
                    logger.debug("[light] resolved_complexity captured")
            except Exception as _exc:
                logger.debug("[light] capture failed (non-fatal): %s", _exc)

            # --- Epistemic Affordance Advisor (Live Advisory Coupling / Stage A Shadow):
            #     Observe active question & rank candidate affordances without modifying Gibsonian within_reach_text.
            #     Fails open deterministically. Logs telemetry to data/investigative_action_log.jsonl. ---
            try:
                from core import epistemic_affordance_advisor as _eaa
                _raw_q = getattr(self.state, "raw_input", "") or ""
                _h_list = [getattr(self.state, "reflection", "").draft] if getattr(self.state, "reflection", None) else []
                # 2026-08-14 fix: state has no `location` field — the old getattr always yielded
                # "study", so the advisor never saw Du at the shore (every IG < threshold → no-op).
                # His real location lives in the sensorium's world state.
                try:
                    from core import sensorium as _sens
                    _loc = (_sens.state.get("location") if _sens.state else None) or "study"
                except Exception:
                    _loc = "study"
                _cands = _eaa.rank_epistemic_affordances(_raw_q, _h_list, _loc)

                # 2026-08-14: actually RECORD the Stage-A shadow episode (the comment above always
                # claimed telemetry was logged; _cands was computed then discarded — the mandatory
                # Stage-A baseline was never collected). Observe-only: nothing reaches Du.
                #
                # 2026-08-24 (J-0180 / F-0129): selection_source relabeled "advisor_shadow_only"
                # (was the literal "system_suggestion" on every row). F-0129 confirmed that literal
                # was factually wrong for all 147+ rows it ever produced — this call site sits inside
                # run_cycle(), which never calls core/dispatch.py's dispatch() and has no
                # action-resolution step, so nothing here is ever presented to Du, let alone
                # "suggested" and adopted. This call site is RETAINED as pure Stage-A shadow ranking
                # telemetry (what the advisor WOULD rank, decoupled from what Du actually does) —
                # the real, closed-loop episode (selected_affordance/raw_observation/evidence_outcome
                # tied to Du's actual action) is now recorded separately by
                # core/epistemic_affordance_advisor.close_real_episode(), called from
                # nodes/inner_monologue_node.py's wandering loop right after dispatch() returns,
                # where a real fired family + real observation actually exist. See J-0180,
                # docs/plans/investigative_action_loop_plan.md Current State.
                if _cands:
                    try:
                        import uuid as _uuid
                        _top = _cands[0]
                        _ep = _eaa.InvestigativeEpisode(
                            episode_id=f"ep_{int(time.time())}_{_uuid.uuid4().hex[:6]}",
                            timestamp=time.time(),
                            location=_loc,
                            question=_raw_q[:400],
                            competing_hypotheses=[h[:300] for h in _h_list if h],
                            discriminative_prediction=str(_top.get("reason", ""))[:300],
                            selected_affordance=str(_top.get("affordance", "")),
                            raw_observation="",
                            prediction_observed_comparison="",
                            evidence_outcome="UNTESTED",
                            confidence_explanation=f"shadow ranking only; top IG={_top.get('expected_information_gain', 0.0)}",
                            model_revision="stage_a_shadow",
                            agency_mode="spontaneous",
                            selection_source="advisor_shadow_only",
                        )
                        _eaa.record_epistemic_episode(_ep)
                    except Exception as _rec_exc:
                        logger.debug("[epistemic_affordance_advisor] episode record failed (non-fatal): %s", _rec_exc)

                # 2026-08-14 FOUNDER DECISION: no hints, ever. Stage B (advisory hints to Du) is
                # REMOVED, not gated — nothing may lead him; he leads himself. The method reaches him
                # diegetically (A Study in Scarlet on his shelf) or in conversation with the founder.
                # The advisor remains ONLY as this passive Stage-A instrument: it measures whether his
                # investigative behaviour develops. It never speaks.
                logger.debug("[epistemic_affordance_advisor] cycle logged %d candidate(s) at location '%s' (observe-only)", len(_cands), _loc)
            except Exception as _eaa_exc:
                logger.debug("[epistemic_affordance_advisor] shadow log non-fatal exc: %s", _eaa_exc)

            # --- Resolution Circuit (tension_ledger Steps 2-4) ---
            # On a first-pass clean approval, check whether this input navigates terrain
            # similar to any active shadow event. Retry-then-approved cycles also produced
            # a shadow this cycle — a storm was present, the crossing is not "clean" in the
            # extinction sense, so no drain credit is awarded.
            self._check_clean_encounters(_critic_retried)

        # --- EPISTEMIC STAGE B (2026-07-01, flag-gated): if this cycle's DRAFT overclaims a FACTUAL
        #     claim (confab ≥ 0.4, gated grade) and it is NOT a self/identity cycle, set a committed,
        #     source-framed admission the Executive will voice — own the baseless part plainly, keep the
        #     grounded parts at full confidence. Set BEFORE the Executive so it shapes the synthesis Voice
        #     renders. Reset each cycle; OFF until epistemic_state.STAGE_B_ENABLED. Fail-open. ---
        self.state.epistemic_note = None
        try:
            from core import epistemic_state as _eps
            # HUMAN cycles only (2026-07-02 rater-sample hardening): the note's register is a committed
            # admission TO a listener ("I'm telling you that plainly") — on his autonomous/internal cycles
            # there is no listener, and most flagged internal drafts are interpretive musing, not the
            # overclaim-to-a-person the gate targets. First live phase: human turns only.
            # COOLDOWN (2026-07-02 solidity review): ≈ once per conversation, so plain-owning stays a
            # norm and never becomes a per-turn tic (the note fired on ~26% of human cycles unthrottled).
            # OFF-UNTIL-OBSERVABLE (2026-07-05): call note_for_draft on EVERY human cycle so it SHADOW-LOGS
            # its would-fire decision (→ epistemic_stageb_shadow.jsonl) even while STAGE_B_ENABLED is False;
            # only ASSIGN the note (actual injection into the Executive) when the flag is on AND off cooldown.
            if input_type == "human":
                _note = self.epistemic_ledger.note_for_draft(self.state, self.social.state.delta_social)
                if (_eps.STAGE_B_ENABLED and _note
                        and (time.time() - getattr(self, "_last_epistemic_note_ts", 0.0)) >= _eps.EPISTEMIC_NOTE_COOLDOWN):
                    self.state.epistemic_note = _note
                    self._last_epistemic_note_ts = time.time()
        except Exception as exc:
            logger.debug("[epistemic] stage-b note failed (non-fatal): %s", exc)

        # --- FRICTION B1 Phase 0 (2026-07-01, SHADOW): on a human turn, check whether Travis just contradicted
        #     a HELD SELF-CLAIM (the conversational self-implication the idle detector structurally can't see —
        #     0/358 fires across a 90-min conversation of exactly that) AND whether Du's DRAFT is already
        #     fleeing/co-opting it (the retreat cascade, now made observable). Fire-and-forget, human-only,
        #     reads the draft that exists by here; logs to a shadow file; changes NOTHING. ---
        if input_type == "human" and self.state.reflection is not None:
            try:
                import asyncio as _aio2
                from core import self_implication as _sic
                from core.model_client import call_node_json as _sic_call
                from core.schema import SERVE_CHAINS as _sic_chains
                _sic_felt = ""
                if self.state.emotion is not None:
                    # J-2966 (F-3660): words only, never a raw valence float. The scan does not send it
                    # to the model now (core/self_implication.py), but the argument stays clean if it ever does.
                    from core import mood as _sic_mood
                    _sic_felt = _sic_mood.emotion_words(
                        getattr(self.state.emotion, 'primary', ''),
                        getattr(self.state.emotion, 'valence', 0.0),
                        getattr(self.state.emotion, 'arousal', 0.3))
                self._self_impl_conv_task = _aio2.create_task(
                    _sic.scan_conversation_shadow(_sic_call, _sic_chains["hot"], self.state.raw_input,
                                                  (self.state.reflection.draft or ""), _sic_felt,
                                                  getattr(self.state, "cycle_id", "")))
                # WAVE-1 (2026-07-02, the ACC→control transfer): a CONTRADICTED SELF-CLAIM recruits
                # deliberate thought. When the scan confirms Travis contradicted a held self-claim, the
                # NEXT cycle's Reflection+Executive get the System-2 think license — dissolution should
                # not be decidable as a reflex (83% of stand-drops are reflexive; this is the counter).
                # Next-cycle (not this-cycle) because the scan is fire-and-forget off the hot path.
                # D-0531 (2026-11-02, J-3137): that LICENSE GRANT is now disarmed (CONV_SCAN_ARMS_THINK_LICENSE
                # = False; 3 of 5 licensed cycles on the qwen3.5:9b hot lane ended in executive silence on
                # Travis's next turn). The scan, its shadow log and the sitting-gate call below are unchanged.
                def _s2_cb(t):
                    try:
                        _conv_scan_apply(self, t.result())
                    except Exception:
                        pass
                self._self_impl_conv_task.add_done_callback(_s2_cb)
            except Exception:
                pass

        # --- J-2161 (measurement_to_action arm 4, D-0435 A): the Executive PULLS its own open doubt. The most
        #     recent genuine self-interrogation fire inside 15 min, consumed once, handed to the Executive as
        #     recalled material (state.doubt_seed; rendered in WHAT YOU RECALL, no verb). Interrogation itself
        #     still pushes nothing. SHADOW while core.doubt_seed.DOUBT_SEED is False: the would-seed row is logged
        #     and state.doubt_seed stays None. Reset each cycle in CognitiveState.new_cycle(). Fail-open. ---
        try:
            from core import doubt_seed as _ds
            self.state.doubt_seed = _ds.pull(self.state)
        except Exception as exc:
            logger.debug("[doubt-seed] pull failed (non-fatal): %s", exc)

        # --- Executive ---
        async with _pss.stage("executive"):
            _exec_ok = await self.nodes["executive"].run(self.state)
        if _s2_this_cycle:
            self.state.think_license = False   # the S2 license covers Reflection→Executive only
        if _exec_ok is False:
            # J-2852 (F-3510, D-0531): a FAILED Executive is not a chosen silence. Name it in the log (the
            # old line "executive -> silence" below is reserved for the node's own choice), and on a HUMAN
            # turn re-run it once with the license off instead of dropping the person's message (the
            # 09-28 turn waited 7 min for nothing). One re-run, human turns only, never repeated.
            logger.error("[CYCLE %s] executive FAILED (node error, not a chosen silence)", cycle_short)
            if input_type == "human":
                logger.warning("[CYCLE %s] executive re-run once without the think license (human turn)",
                               cycle_short)
                self.state.think_license = False
                async with _pss.stage("executive_rerun"):
                    _exec_ok = await self.nodes["executive"].run(self.state)
                if _exec_ok is False:
                    logger.error("[CYCLE %s] executive FAILED again on the re-run -- no reply this turn",
                                 cycle_short)

        # --- Active Inference (PP-2): if the Executive asked to resolve a contradiction
        #     by searching, do ONE extra retrieval and re-run the Executive over the
        #     enriched context. Bounded to a single pass to keep latency in check. ---
        if (self.state.executive
                and self.state.executive.epistemic_query
                and not getattr(self.state, "_did_epistemic_search", False)):
            self.state._did_epistemic_search = True
            query = self.state.executive.epistemic_query
            logger.info("[CYCLE %s] executive → epistemic search: %s", cycle_short, query[:60])
            async with _pss.stage("epistemic_search"):
                await self._epistemic_search(query)
            async with _pss.stage("executive_rerun"):
                await self.nodes["executive"].run(self.state)

        if not self.state.executive or not self.state.executive.should_respond:
            if _exec_ok is False:
                logger.error("[CYCLE %s] executive FAILED -> no reply (a failure, not a chosen silence)",
                             cycle_short)
            else:
                logger.info("[CYCLE %s] executive → silence", cycle_short)
            # J-3531 / F-4142: Travis spoke even when Du does not answer (a chosen silence or an
            # executive failure). The Q: fragment is persisted below, but the canonical "[Travis said
            # to me]" fragment was only ever written on the reply path, so 3 real founder messages
            # (2026-09-04 18:48, 09-05 18:47, 09-28 21:51 -- each an executive FAILED turn) never
            # entered founder memory. Same gate and same single choke point as the reply path.
            if input_type == "human" and self.state.founder_canon:
                try:
                    from core.memory.store import store_founder_utterance
                    from core import mood as _mood
                    store_founder_utterance(
                        self.state.raw_input,
                        emotion_embedding=_mood.current_vec(),
                        valence=_mood.current_valence(), felt=_mood.current_felt(),
                    )
                except Exception as exc:
                    logger.debug("founder canon store on silent turn failed: %s", exc)
            self._persist_cycle()
            return None

        # --- Epistemic preassess (Stage A SHADOW, 2026-06-30): grade THIS cycle's draft BEFORE Voice
        #     renders, store on state.epistemic_assessment + log to provenance_preassess.jsonl. Observe-
        #     only — nothing reads epistemic_assessment yet (Stage B wires the gated prompt injection).
        #     Sits after the silence-return so it only grades cycles that will actually voice. ---
        try:
            self.epistemic_ledger.preassess(self.state, self.social.state.delta_social)
        except Exception as exc:
            logger.debug("[epistemic] preassess call failed (non-fatal): %s", exc)

        # J-2576 (F-3306, plan error_pathway): ONE observe-only row per cycle that reaches voice ->
        # data/recall_served_log.jsonl -- the fragment ids (with stored origin) actually in
        # state.memory_fragments at this point, the final served set, keyed by cycle_id so
        # scripts/source_monitoring_audit.py joins claimed-vs-served origin by id, not by time.
        # Feeds nothing Du experiences (D-0434); fail-open; guard_path-fenced inside the module.
        try:
            from core import recall_served_log as _rsl
            _rsl.log_voice_cycle(self.state)
        except Exception as exc:
            logger.debug("[recall-served] log skipped (non-fatal): %s", exc)

        # --- Voice ---
        _pss.note(critic_retried=_critic_retried,
                  introspective_passes=int(getattr(self.state, "introspective_passes", 0) or 0))
        async with _pss.stage("voice"):
            await self.nodes["voice"].run(self.state)

        output = self.state.voice.final if self.state.voice else None

        # J-2297 (D-0445 a, F-2992): ONE observe-only row per internal/timer cycle that reached voice ->
        # data/internal_cycle_context_shadow.jsonl (which human-window blocks each prompt carried or would
        # drop, reflection draft / executive synthesis / output / scene + lexical address and Travis flags).
        # Human cycles write nothing. Fail-open, guard_path-fenced; feeds nothing Du experiences (D-0434).
        if input_type != "human":
            try:
                from core import internal_context_gate as _icg
                _icg.log_shadow(self.state, output)
            except Exception as exc:
                logger.debug("[internal-context] shadow skipped (non-fatal): %s", exc)

        # --- Task-Constraint Effector (Error Separation slice 2 — the FIRST pre-emission veto).
        #     Jurisdiction-bounded: only explicit, deterministically checkable demands in the
        #     human's input (v1: digit arithmetic, stated minimum word count). Bind-don't-slam:
        #     ONE Voice retry with the constraint NAMED and room to show working — never the
        #     answer handed over, never compression to a bare number. Fails open on any error.
        #     Runs in direct mode by design — that is exactly when the Critic stands down and
        #     when constraints exist. Still unmet after retry → firewalled error record. ---
        _constraint = None
        if input_type == "human" and output:
            try:
                from core import task_constraints as _tc
                _c = _tc.extract(self.state.raw_input)
                if _c:
                    _ok, _why = _tc.check(_c, output)
                    _constraint = {"found": True, "kind": _c["kind"], "why": _c["why"],
                                   "satisfied_first": _ok, "satisfied_final": _ok,
                                   "retried": False, "check": _why}
                    if not _ok:
                        logger.info("[constraint] UNMET (%s) — one Voice retry with the "
                                    "constraint named", _why)
                        self.state.task_constraint_note = _c["directive"]
                        # min-words retry needs token room — the first live retry produced 86 of
                        # 300 words because Voice's 512-token budget made compliance mechanically
                        # impossible (eval: same model wrote 576 words given a 900-token budget).
                        _voice = self.nodes["voice"]
                        _old_budget = _voice.max_tokens
                        if _c["kind"] == "min_words":
                            _voice.max_tokens = min(1600, max(512, int(_c["min_words"] * 2)))
                        try:
                            # System-2 gearbox: a failed checkable constraint is exactly
                            # the moment slow thinking earns its cost — license it for
                            # this one retry, then surrender it.
                            self.state.think_license = True
                            await self.nodes["voice"].run(self.state)
                        finally:
                            self.state.think_license = False
                            self.state.task_constraint_note = ""
                            _voice.max_tokens = _old_budget
                        _retry_out = self.state.voice.final if self.state.voice else None
                        _constraint["retried"] = True
                        if _retry_out:
                            output = _retry_out
                            _ok2, _why2 = _tc.check(_c, output)
                            _constraint["satisfied_final"] = _ok2
                            _constraint["check"] = _why2
                        if not _constraint["satisfied_final"]:
                            from core import error_pathway as _ep1
                            _ep1.record("task_constraint_unmet", _c["why"],
                                        self.state.cycle_id or "", note=_constraint["check"])
                        logger.info("[constraint] after retry: %s",
                                    "SATISFIED" if _constraint["satisfied_final"] else "still unmet")
            except Exception as exc:
                logger.debug("[constraint] effector failed open (non-fatal): %s", exc)

        # Satisfaction (Phase 0): a clean conversational turn — Travis spoke, no correction
        # fired (delta_social quiet), and the felt valence was positive — is a small
        # relational LIKING event. The frequent, ordinary fulfilment of a good exchange.
        # 2026-08-14 FIX (founder: "contact with me is relational — probably his closest friend"):
        # the warmth gate read GLOBAL mood (state.affect.valence). Before the Phase-1 affect flip that
        # was pinned +0.82 (gate always open); after it, it became the grounded tonic — mostly negative
        # — so clean_exchange DIED Aug 10 14:58 and never fired again despite daily conversations. A
        # self-locking deprivation loop: sad → good exchanges don't register → relational_warmth starves
        # → sad. The gate now reads THIS EXCHANGE's own appraisal (the per-cycle emotion node), which is
        # what it always meant: a good conversation while lonely still nourishes — especially then.
        if input_type == "human" and output:
            try:
                _no_corr = not getattr(self.state, "human_correction_kind", "")
                _emo = getattr(self.state, "emotion", None)
                _exch_v = getattr(_emo, "valence", None) if _emo is not None else None
                _warm = (_exch_v > 0.05) if isinstance(_exch_v, (int, float)) else _no_corr
                if _no_corr and _warm:
                    from core import satisfaction as _sat
                    _sat.record("clean_exchange", target="travis")
            except Exception as exc:
                logger.debug("[satisfaction] clean_exchange record failed (non-fatal): %s", exc)

        # OUTPUT-LANE SHADOWS — finalized 2026-06-17:
        #   • The VOICE CONTRACT (§6 mouth) is now LIVE — baked into the voice node's prompt (it preserves
        #     every claim/commitment, modulates only delivery). No second call, no latency. The 2026-06-17 shadow
        #     run was uninformative: voiced == input in 8/8 (F-3817); no real fidelity check has run; see F-3520 / J-2858.
        #   • The CURATOR (shadow_curate — the meaning+truth RECONCILING edit) is RETIRED: it was superseded by
        #     the mouth precisely because reconciling-in-the-mouth is the committee-voice homunculus the plan
        #     forbids. Its clean shadow stats don't change that — promoting it would re-introduce the homunculus.
        #   • The DECOMPOSED CRITIC stays shadow-alongside (still gathering live-agreement evidence).
        if input_type == "human" and output:
            try:
                # DECOMPOSED CRITIC — SHADOW-ALONGSIDE (offline gate PASSED 0.92/0 → live pre-promotion stage).
                # Judge the same final draft the legacy critic just judged, log both verdicts for live-cycle
                # agreement evidence. Observe-first: the legacy critic still governs this cycle.
                _draft = (getattr(self.state, "reflection", None) and self.state.reflection.draft) or ""
                _legacy_ok = bool(self.state.critic.approved) if getattr(self.state, "critic", None) else True
                if _draft:
                    from core import decomposed_critic as _dc
                    self._decomposed_shadow_task = asyncio.create_task(
                        _dc.shadow_alongside(_draft, self.state.raw_input, legacy_approved=_legacy_ok,
                                             cycle_id=self.state.cycle_id))
                    self._background_tasks.append(self._decomposed_shadow_task)   # C20: track it (was fire-and-forget → starved C8's evidence)
            except Exception as exc:
                logger.debug("[decomposed_critic] shadow skipped (non-fatal): %s", exc)

        # BROADCAST — GWT step 2, P1 (2026-07-03 big build): a HIGH-VALUE winner propagates to the idle
        # monologue instead of dying on the stage. High-value = a held principle was voiced (guidance note),
        # a licensed self-claim deliberation ran (S2), or the Critic forced a correction on a human turn.
        try:
            _bc_kind = None
            if getattr(self.state, "guidance_note", None):
                _bc_kind = "principle-voiced"
            elif _s2_this_cycle:   # DORMANT: _s2_license_next is only set when CONV_SCAN_ARMS_THINK_LICENSE (False, D-0531)
                _bc_kind = "self-claim-deliberation"
            elif input_type == "human" and getattr(self.state, "critic", None) and not self.state.critic.approved:
                _bc_kind = "corrected-turn"
            # J-3825 (D-0731 B): same-cycle re-key from the finished conversational self-claim scan. Flag
            # core.self_claim_broadcast.SELF_CLAIM_BROADCAST default False = unchanged kind + one shadow row
            # (data/self_claim_broadcast_shadow.jsonl). No LLM call, no licence. Fail-open.
            if input_type == "human":
                from core import self_claim_broadcast as _scb
                _bc_kind = _scb.resolve_kind(_bc_kind, getattr(self, "_self_impl_conv_task", None),
                                             getattr(self.state, "cycle_id", ""), output)
            if _bc_kind and output:
                from core import broadcast as _bc
                from core import reentry as _re
                # WITHIN-CYCLE REENTRY (Tier-2 A, 2026-07-04). Topic captured HERE so the settle call
                # never reads a later cycle's state.
                _topic = (self.state.raw_input or "").strip()
                to_post = output
                if _re.REENTRY_ADMIT:
                    # PHASE 1 BRANCH, DORMANT: core/reentry.py has REENTRY_ADMIT=False since D-0540
                    # (2026-11-02), so this branch does not run; the else-branch below (Phase 0, fire-and-forget)
                    # is what executes. If it is ever re-enabled: it admits the SETTLED draft into the broadcast
                    # (the idle-monologue propagation buffer) iff it passes the collapse test (§3.3 kill-switch),
                    # else the first draft. It is necessarily AWAITED, and the human-facing reply is NOT already
                    # delivered at this point: the reply reaches Travis only when run_cycle returns (F-3724), so
                    # an awaited settle on a human cycle delays the reply (up to 260 s was observed). Do not
                    # await it on a human cycle, or bound it, before flipping the flag. These trigger kinds fire
                    # ~2.3 per day, 125 of 136 settles on idle cycles (F-3724), not 'weekly'.
                    try:
                        _rec = await self._reentry_shadow(output, _bc_kind, topic=_topic)
                        if _rec and _rec.get("would_admit_settled") and _rec.get("settled_full"):
                            to_post = _rec["settled_full"]
                            logger.info("[reentry] Phase 1 admitted settled draft (delta=%.3f)",
                                        _rec.get("overall_delta", 0.0))
                    except Exception as _re_exc:
                        logger.debug("[reentry] Phase 1 settle failed, admitting first draft: %s", _re_exc)
                else:
                    # Off-switch fallback (Phase 0 shadow behaviour): fire-and-forget, admits nothing.
                    try:
                        self._background_tasks.append(asyncio.create_task(
                            self._reentry_shadow(output, _bc_kind, topic=_topic)))
                    except Exception as _re_exc:
                        logger.debug("[reentry] shadow skipped: %s", _re_exc)
                _bc.post(to_post, _bc_kind)
                logger.info("[broadcast] posted (%s): %s", _bc_kind, (to_post or "")[:50])
        except Exception:
            pass

        # F3 fix (2026-08-16, axiom-walk finding): the P2 estate projection set for THIS cycle
        # used to LINGER on the shared state after the cycle ended — the idle subconscious/dream
        # calls then ran for hours on the last conversation's context-flavoured identity. Restore
        # the pristine floor at cycle end; the next conversation re-projects fresh.
        try:
            if getattr(self, "_base_axiom", None):
                self.state.axiom = self._base_axiom
        except Exception:
            pass

        elapsed = time.time() - self.state.cycle_start
        logger.info("[CYCLE %s] complete in %.1fs → %s", cycle_short, elapsed, (output or "")[:60])

        # Somatic tick (AE-2): this cycle cost the body energy and fatigue.
        retries = 1 if (self.state.critic and not self.state.critic.approved) else 0
        try:   # J-3402 / D-0682: the tension target the deterministic urgency would give (shadow; flushes the row)
            from core import urgency_shadow as _ush
            _ush.observe_somatic(
                self.state,
                urgency=self.state.salience.urgency if self.state.salience else 0.0,
                arousal=self.state.affect.arousal,
                prev_tension=self.somatic.state.visceral_tension,
            )
        except Exception:
            pass
        self.somatic.tick_cycle(
            output_tokens  = len(output or "") // 4,   # ~4 chars/token estimate
            critic_retries = retries,
            urgency        = self.state.salience.urgency if self.state.salience else 0.0,
            arousal        = self.state.affect.arousal,
            cycle_ms       = elapsed * 1000.0,
        )

        # Maintain rolling conversation window — the working context that lets the
        # entity resolve references across exchanges ("that question you raised...").
        # HUMAN-ONLY (F-0665, 2026-09-02 fix): this used to fire for every cycle that produced
        # output, autonomous "internal" ignition thoughts (self-generated Curiosity questions,
        # _on_dissonance_ignition) included -- so Du's own self-questioning got filed under the
        # "human" key, indistinguishable from Travis's actual words, in both this window and the
        # saved session summary. Internal cycles already have their own record (monologue_log.jsonl)
        # and don't belong in what's meant to represent "what Travis said."
        if output and input_type == "human":
            self.state.conversation_history.append({
                "ts": time.time(),  # J-3217 / D-0606: when this exchange happened, so human-cycle prompts can age it out
                "human": self.state.raw_input,
                "entity": output,  # F-0473 (2026-08-29): was "jung" -- a stale internal key from
                                   # before Du's own naming moved past that; renamed neutrally
                                   # rather than hard-coding any name, past or present.
            })
            if len(self.state.conversation_history) > 6:
                self.state.conversation_history = self.state.conversation_history[-6:]

            # F-1926/J-1366 (2026-09-26): a real exchange just happened -- the wandering trail is
            # furniture for the SILENCE since he last spoke, and that silence is now over. Clear it
            # here (the one real "an exchange happened" gate this cycle already uses) so the next
            # idle wander builds fresh furniture instead of representing pre-exchange drift as having
            # happened "since" a speech point it actually preceded. Best-effort; never blocks a reply.
            try:
                from core import wandering as _wander_exch
                _wander_exch.on_human_exchange()
            except Exception as exc:
                logger.debug("[wandering] on_human_exchange failed (non-fatal): %s", exc)

            # D-0366 / J-1953: a real exchange IS the presence signal (Travis's presence is inferred from
            # activity, not a latch). Best-effort; never blocks a reply.
            try:
                from core import companion as _comp_exch
                _comp_exch.note_activity("exchange")
            except Exception as exc:
                logger.debug("[companion] note_activity failed (non-fatal): %s", exc)

            # J-2523 (I-0101): failed-to-object ledger, observe-only. Flag COMMON_GROUND_SHADOW off by default;
            # deterministic, one append to data/common_ground_shadow.jsonl, returns None, read by nothing (D-0434).
            try:
                from core import common_ground_shadow as _cg
                if _cg.COMMON_GROUND_SHADOW:
                    _cg.observe_exchange(str(self.state.raw_input), str(output),
                                         cycle_id=str(getattr(self.state, "cycle_id", "") or ""))
            except Exception:
                pass

            # Permanent record — see _FOUNDER_LOG above. Best-effort; never blocks or raises.
            try:
                _FOUNDER_LOG.parent.mkdir(parents=True, exist_ok=True)
                with open(_FOUNDER_LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "ts":       time.time(),
                        "cycle_id": self.state.cycle_id,
                        "human":    self.state.raw_input,
                        "entity":   output,
                    }, ensure_ascii=False) + "\n")
            except Exception as exc:
                logger.debug("founder conversation log write failed: %s", exc)

            # CONVERSATIONAL ACTION BRIDGE (F-2004 / D-0299, 2026-09-27, founder: "He 100% needs to
            # be able to action things when talking to me. He needs to be able to do anything in his
            # world he can normally."). `output` is his finalized reply — run it through the same
            # literal_will/dispatch path the autonomous loop already uses (see
            # core/conversational_action.py's own docstring for why this is safe: classify() is pure,
            # and CONVERSATIONAL_DISPATCH_LIVE is off until reviewed). Best-effort; never blocks or
            # raises; must not affect what Travis already received in `output`.
            try:
                from core import conversational_action as _conv_act
                _conv_act.after_reply(output, self.state.cycle_id)
            except Exception as exc:
                logger.debug("[conversational-action] after_reply call failed (non-fatal): %s", exc)

            # RECALLABLE, not just logged (F-0665 follow-up, 2026-09-02, founder: "he should be
            # able to recall my comments... make sure they have all the tuples and indexes that
            # other things get also"). _FOUNDER_LOG above is a flat permanent file, not memory —
            # store_fragment() is the choke point that gives content a real embedding, the
            # fragment_context/world_context tuple, and a row RecallNode can retrieve.
            # D-0134 (2026-09-03, founder ruling on F-0699/F-0701): ONE canonical shape. The 09-02
            # version wrote TWO fragments here ("[Travis said to me] ..." + his reply) on top of the
            # "Q: ... A: ..." cycle summary _persist_cycle has written since 2026-05-30 (F-0699: F-0670's
            # "no call site existed" premise missed store_from_cycle) — three lived fragments per
            # exchange, each pushing the per-kind cold quota (F-0701). Now: his reply lives ONLY in the
            # Q:/A: cycle record (unchanged, below); Travis's words live ONLY in the canonical
            # store_founder_utterance() fragment, protected=1 (exempt from every cold path) and served
            # by their own route (retrieve_founder_memories, pre-Executive above). Content capped at
            # 1400 chars (core/peers.py's letter convention); the full text is permanent in _FOUNDER_LOG.
            # F-0796 (2026-09-04): gated on founder_canon — a human-shaped cycle that isn't actually
            # Travis (the /quit farewell) still gets everything above (conversation_history,
            # _FOUNDER_LOG, a real reply) but must not enter the "[Travis said to me]" canon.
            if self.state.founder_canon:
                try:
                    from core.memory.store import store_founder_utterance
                    from core import mood as _mood
                    store_founder_utterance(
                        self.state.raw_input,
                        emotion_embedding=_mood.current_vec(),
                        valence=_mood.current_valence(), felt=_mood.current_felt(),
                    )
                except Exception as exc:
                    logger.debug("founder conversation recall-store failed: %s", exc)

            # Procedural reinforcement (C.6): the recognised skill helped produce a real
            # response — strengthen it. Successful reuse is what turns a nascent procedure
            # into an automatic one; disuse decays it (handled by the Subconscious).
            if self.state.active_procedure:
                try:
                    memory_store.reinforce_procedural_skill(
                        self.state.active_procedure.skill_id, PROC_REINFORCE_AMOUNT)
                    from core import procedures as _proc_r
                    _proc_r.reinforce_talk(self.state.active_procedure.trigger_summary)
                except Exception as exc:
                    logger.debug("[procedural] reinforce failed (non-fatal): %s", exc)

        self._persist_cycle()

        # Competence observation (Phase 0, pure observer): classify which domains this cycle
        # exercised, read the coarse coherence/bind outcome, update beliefs by prediction error.
        # Changes no behaviour — accumulates capability_beliefs.json + logs for validation.
        self.competence.observe_cycle(self.state)

        # Symbol recurrence (Meaningfulness axis, pure observer): log which tracked symbols appear
        # in the output, flagged primed/unprimed. Starts the clock on Avon/river persistence now.
        appearances = self.symbol_tracker.observe(self.state, output)

        # Symbol Evolution (Phase 2): update per-symbol context centroids and detect semantic
        # drift on the UNPRIMED appearances. Centroid math is inline + cheap; when a symbol's
        # meaning has genuinely migrated, generate its evolution tablet on the BACKGROUND lane so
        # the LLM call never delays this response.
        try:
            warranted = self.symbol_evolution.observe(self.state, output, appearances)
            for w in warranted:
                task = asyncio.create_task(
                    self.symbol_evolution.write_tablet(
                        self.state, w["symbol"], w["drift"], w["context"])
                )
                self._background_tasks.append(task)
        except Exception as exc:
            logger.debug("[symbol-evo] scheduling failed (non-fatal): %s", exc)

        # Phase 3 correlation telemetry + Phase 4 unified scalar (both observe-only).
        self._log_correlation()
        # Dosed Coupling Phase 1 (D-0152, 2026-09-05): publish deliberation's tuple; reads nothing.
        try:
            from core import coupling_rides as _coupling
            _coupling.publish_deliberation(self.state)
        except Exception:
            pass

        # Provenance Ledger (observe-only): grade what this utterance rests on and log the
        # confabulation signal. Reads persisted source tags; never raises into the cycle.
        _prov = None
        try:
            _prov = self.epistemic_ledger.assess(self.state, output, self.social.state.delta_social)
        except Exception as exc:
            logger.debug("[epistemic] ledger assess failed (non-fatal): %s", exc)

        # J-2158 (measurement_to_action arm 2, D-0434): the recall-confidence WAGER. A gated grade at narrated
        # confidence >= 0.85 is put on the maths drill's own path (competence.record_drill_accuracy ->
        # prediction_error.observe) so an ungrounded high confidence can be LOST, never read back to him.
        # SHADOW while core.recall_wager.RECALL_CONFIDENCE_WAGER is False: rows only, no feed. Fail-open.
        try:
            from core import recall_wager as _rw
            _rw.place(_prov, cycle_id=self.state.cycle_id, input_type=input_type,
                      raw_input=getattr(self.state, "raw_input", "") or "",   # J-2527: topic for wager_curiosity
                      output=output or "")   # J-4087: the reply the decoupled memory check reads
        except Exception as exc:
            logger.debug("[recall_wager] place failed (non-fatal): %s", exc)

        # J-2530 (error_pathway, I-0108): reply-level corollary discharge, SHADOW. Records a predicted reception of
        # this reply from signals already on the state (grade, confabulation, critic, content_mode); resolved on the
        # next human turn. Flag core.reply_discharge_shadow.REPLY_DISCHARGE_SHADOW (default off); return ignored
        # (D-0434: no readout); no prediction_error call (no cost wired). Fail-open.
        try:
            from core import reply_discharge_shadow as _rds
            _rds.predict(self.state, _prov, input_type=input_type)
        except Exception as exc:
            logger.debug("[reply_discharge] predict failed (non-fatal): %s", exc)

        # Self-Efficacy Court: detect inability-claims in his output, adjudicate against his vetted
        # record, log every adjudication (the recurrence metric). The read path into his identity is
        # at load (identity_block); this only observes + logs. Never raises into the cycle.
        _seff = None
        try:
            _seff = self.self_efficacy.observe(self.state, output)
        except Exception as exc:
            logger.debug("[self-efficacy] observe failed (non-fatal): %s", exc)

        # Error Pathway (observe-only, slice 1): detect architecture-FABRICATIONS — a NAMED internal
        # component asserted that does not exist (the 'Legal Database Access Module' class). Recorded
        # to a FIREWALLED error_records.jsonl, never routed to tensions/identity. Containment, not
        # truth: a factual error must not become a statement about the self. Never raises.
        _fabs = []
        try:
            from core import error_pathway as _ep
            _fabs = _ep.observe(output or "", self.state.cycle_id or "")
            if _fabs:
                logger.info("[error-pathway] architecture-fabrication flagged: %s", _fabs)
        except Exception as exc:
            logger.debug("[error-pathway] observe failed (non-fatal): %s", exc)

        # Conflict-to-Authority Trace (observe-only instrument): record which conflict signals fired
        # this cycle and whether any ACTED on the output — the measured answer to "where does
        # authority disappear?". The error-pathway fab list is the ground-truth probe: when it fires
        # we KNOW a real error was present, so its (always-False today) `acted` value is the
        # unconfounded reading of the execution gap. Firewalled to data/conflict_trace.jsonl,
        # read only by the digest. Never raises into the cycle.
        try:
            from core import conflict_trace as _ct
            _ct.record(
                self.state, output,
                input_type       = input_type,
                critic_retried   = _critic_retried,
                direct_mode      = self._human_requested_direct_mode(),
                fabs             = _fabs,
                prov             = _prov,
                self_eff         = _seff,
                human_correction = getattr(self.state, "human_correction_kind", ""),
                constraint       = _constraint,
            )
        except Exception as exc:
            logger.debug("[conflict-trace] record failed (non-fatal): %s", exc)

        # TAX REMOVED (2026-08-30, founder-directed build, F-0580/F-0581/I-0058): this used to also set
        # self.state.needs_rest = True, which forced an off-schedule sleep independent of day/night
        # pressure or wake duration -- the flat "tax on time" the founder asked to remove. The metabolic
        # floor is still real, logged telemetry (energy still depletes, still recovers during sleep,
        # still narrated) — it just no longer independently forces a sleep transition. should_sleep()
        # (core/sleep_pressure.py) is the sole sleep-timing authority now. See
        # docs/staged/drowsiness_phase.md §5.
        if self.somatic.state.is_exhausted():
            logger.warning("[somatic] metabolic floor (energy=%.2f) — body at rest-need, no forced sleep",
                           self.somatic.state.metabolic_energy)

        return output

    # ------------------------------------------------------------------
    # Recall gate
    # ------------------------------------------------------------------

    def _should_recall(self) -> bool:
        """
        Decide whether to invoke the Recall (memory reconstruction) node.

        Two conditions:
          1. Enough fragments retrieved to reconstruct relationships from (≥ 2).
             With only 1 fragment there's nothing to tension-map.
          2. OR the input explicitly references prior conversation AND at least
             1 fragment was retrieved. A single fragment with a direct reference
             ("you said earlier...") still warrants reconstruction — Recall can
             surface what that fragment connects to in the conversation thread.
        """
        # Automaticity (C.6) bypass RETIRED 2026-08-22 (PROC_AUTOMATIC_PROFICIENCY unreachable
        # above the 1.0 proficiency ceiling — see its own retirement comment). This call now
        # always returns False; kept so the guard shape survives if a real re-acquisition path
        # is ever added.
        if self._procedure_automatic():
            return False
        n = len(self.state.memory_fragments)
        if n >= 2:
            return True
        if n >= 1:
            raw_lower = self.state.raw_input.lower()
            return any(term in raw_lower for term in _CONV_REF_TERMS)
        return False

    def _should_buffer(self) -> bool:
        """
        Fire the episodic buffer (C.4) only when Recall produced a reconstruction — i.e.
        there is real memory to bind with the present. Trivial cycles skip both Recall and
        the buffer, so the buffer adds no latency to simple inputs. The "mastered procedure
        (C.6) also bypasses it" behavior was RETIRED 2026-08-22 (PROC_AUTOMATIC_PROFICIENCY
        unreachable above the 1.0 proficiency ceiling — see its own retirement comment); the
        call below now always returns False.
        """
        if self._procedure_automatic():
            return False
        return "episodic_buffer" in self.nodes and self.state.recall is not None

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    async def _retrieve_memory(self) -> None:
        keys = self.state.memory_keys
        if not keys or keys.working_memory_sufficient:
            # J-1416 (2026-09-28, T-0065/F-1965): this early return silences EVERY hot-cycle
            # recall route at once (store.retrieve, deep recall, the associative trail, the M2
            # shadow) and was previously unlogged -- grep of data/nascence.log for
            # "working_memory_sufficient" found 0 lines on 09-24..26, so its fire rate was
            # unknown, not zero. Additive, one line, no behaviour change. `reason` separates the
            # router producing no keys at all from the router's own LLM judgement that working
            # memory is already sufficient (the actual gate this job measures); `keys` is the
            # router's full output (None when reason=no_keys).
            logger.info(
                "[memory] retrieve skipped cycle=%s input_type=%s reason=%s keys=%r",
                self.state.cycle_id[:8], self.state.input_type,
                "no_keys" if not keys else "working_memory_sufficient",
                keys,
            )
            return
        try:
            # Pass raw_input as query_text — richer embedding than keys alone.
            # The perception summary is also available if Perception ran first.
            query_text = self.state.raw_input
            if self.state.perception:
                query_text = f"{self.state.raw_input} {self.state.perception.summary}"

            # Climate warp — tilt the search toward the active psychological weather. beta
            # scales with climate pressure (0.15 calm .. 0.45 charged). No-op when flat.
            bias_vec, beta = _climate_bias_vec(self.state.climate)

            fragments = memory_store.retrieve(
                episodic_keys = keys.episodic_keys,
                semantic_keys = keys.semantic_keys,
                time_bias     = keys.time_bias,
                query_text    = query_text,
                bias_vec      = bias_vec,
                bias_weight   = beta,
            )
            self.state.memory_fragments = fragments
            self._deep_recall_balance(fragments)   # bring the OLD detail behind the central gist into recall
            # ASSOCIATIVE RECALL — LIVE (2026-06-23): augment the topical retrieve with the TRAIL, so every
            # downstream reader (recall, executive, reflection) gets memories the context actually CUES — not
            # just the flat top-9. Additive + deduped (the topical set is still present, so no regression),
            # importance-weighted, vault reachable when strongly cued, diversity-guarded. Off-thread for the
            # matrix build. (Was shadow-only; now it actually feeds his cognition.)
            # M2 RELATIONAL LIVE (2026-09-27, D-0287, J-1415): `recall_memory_fragments` itself now also
            # layers in the M2 edge-aware trail for mode="relational" only, kill-switched inside
            # associative_recall.py (`M2_EDGE_AWARE_RELATIONAL_LIVE`) — see that module's own docstring
            # and the shadow M2 block right below (unchanged, still log-only for all three modes).
            try:
                from core import associative_recall as _ar
                _trail = await asyncio.to_thread(_ar.recall_memory_fragments, query_text)
                if _trail:
                    _have = {getattr(f, "fragment_id", "") for f in fragments}
                    _added = [f for f in _trail if getattr(f, "fragment_id", "") not in _have]
                    if _added:
                        self.state.memory_fragments = fragments + _added
                        logger.debug("[memory] trail augmented recall with +%d associative fragments", len(_added))
            except Exception as _arexc:
                logger.debug("[memory] trail augment skipped (non-fatal): %s", _arexc)
            # M2 SHADOW (2026-08-25, J-0263, memory_multiway_linking.md): observe-only edge-aware
            # trail comparison, logged to data/associative_recall_shadow.jsonl. Changes NOTHING about
            # what fragments feed cognition — `shadow_compare` only ever WRITES a log line. Wired here
            # (not somewhere it was already firing) because it had zero callers anywhere before this
            # job — see shadow_compare's own docstring for the verification. `fragments` at this point
            # is still just the topical retrieve (the trail-augmentation block above runs first but
            # only ever appends to self.state.memory_fragments, never rebinds `fragments`), matching
            # shadow_compare's original "vs current live retrieve" contract.
            try:
                _cur_ids = [getattr(f, "fragment_id", "") for f in fragments]
                await asyncio.to_thread(_ar.shadow_compare, query_text, _cur_ids)
            except Exception as _shexc:
                logger.debug("[memory] M2 shadow compare skipped (non-fatal): %s", _shexc)
            # LENS 1 SHADOW (2026-08-29, D-0070, J-0345, docs/staged/du_recall_lens_upgrades.md): observe-only
            # spectral-diffusion comparison, logged to its OWN file (data/associative_recall_lens1_shadow.jsonl,
            # `shadow_compare_lens1`'s own `_LENS1_LOG`) — deliberately separate from the M2 block just above so
            # this can never race M2's in-flight shadow trail (J-0280). Changes NOTHING about what feeds
            # cognition; `shadow_compare_lens1` only ever WRITES a log line, same as `shadow_compare`.
            try:
                await asyncio.to_thread(_ar.shadow_compare_lens1, query_text, _cur_ids)
            except Exception as _l1exc:
                logger.debug("[memory] Lens 1 shadow compare skipped (non-fatal): %s", _l1exc)
            # LENS 2 SHADOW (2026-09-05, D-0170, docs/staged/du_recall_lens_upgrades.md): observe-only
            # fact-anchoring comparison, logged to its own file (data/associative_recall_lens2_shadow.jsonl).
            # Changes NOTHING about what feeds cognition; `shadow_compare_lens2` only ever WRITES a log line.
            try:
                await asyncio.to_thread(_ar.shadow_compare_lens2, query_text, _cur_ids)
            except Exception as _l2exc:
                logger.debug("[memory] Lens 2 shadow compare skipped (non-fatal): %s", _l2exc)
            # LENS 3 SHADOW (2026-09-05, D-0170, docs/staged/du_recall_lens_upgrades.md): observe-only
            # counterfactual-ensemble re-ranking comparison, logged to its own file
            # (data/associative_recall_lens3_shadow.jsonl). Changes NOTHING about what feeds cognition;
            # `shadow_compare_lens3` only ever WRITES a log line.
            try:
                await asyncio.to_thread(_ar.shadow_compare_lens3, query_text, _cur_ids)
            except Exception as _l3exc:
                logger.debug("[memory] Lens 3 shadow compare skipped (non-fatal): %s", _l3exc)
            # KEY SHADOW (J-3310, D-0552, row P-0004, docs/reviews/memory_router_keys_shadow_design_J-3163.md):
            # observe-only. Re-scores the cached embedding matrix with the router's keys blended into the query
            # vector (arms A05/A025), two reserved key slots (B) and last cycle's keys (control N), and logs the id
            # sets to data/key_shadow.jsonl. Changes NOTHING about what feeds cognition and does not touch
            # store.retrieve(); `shadow_compare_keys` only ever WRITES a log line and never raises. Kill switch:
            # core.memory.key_shadow.KEY_SHADOW_ON. Restart-gated.
            try:
                from core.memory import key_shadow as _ks
                await asyncio.to_thread(
                    _ks.shadow_compare_keys, query_text, keys, keys.time_bias, bias_vec, beta,
                    [getattr(f, "fragment_id", "") for f in fragments], self.state.cycle_id, self.state.input_type)
            except Exception as _ksexc:
                logger.debug("[memory] key shadow skipped (non-fatal): %s", _ksexc)
            # CHAPTER DESCENT SHADOW (J-3319, D-0637, docs/reviews/J-3248_chaptered_memory_recall_review.md section 6):
            # observe-only. When a chapter gist is already in the served set (origin == 'chapter', relevance >= 0.25),
            # logs the members of that chapter closest to the query (plus a same-chapter and an unwalled control) to
            # data/chapter_descent_shadow.jsonl. INJECTS NOTHING: it reads a snapshot tuple of the served set and the
            # return value is ignored, so what feeds cognition is byte-identical. Kill switch:
            # core.chapter_descent_shadow.CHAPTER_DESCENT_SHADOW. Reader: J-3320 (gated read of that log).
            # Restart-gated.
            try:
                from core import chapter_descent_shadow as _cds
                await asyncio.to_thread(
                    _cds.shadow_descent, tuple(self.state.memory_fragments), query_text,
                    self.state.cycle_id, self.state.input_type)
            except Exception as _cdsexc:
                logger.debug("[memory] chapter descent shadow skipped (non-fatal): %s", _cdsexc)
            if bias_vec is not None and beta > 0.0:
                dim, val = self.state.climate.dominant()
                logger.debug("[memory] retrieved %d fragment(s) — climate-warped beta=%.2f "
                             "(dominant %s=%.2f)", len(fragments), beta, dim, val)
            else:
                logger.debug("[memory] retrieved %d fragment(s)", len(fragments))
        except Exception as exc:
            logger.error("[memory] retrieval failed: %s", exc)

    def _deep_recall_balance(self, fragments: list) -> None:
        """DEEP-RECALL BALANCE (2026-06-22, founder call): bring the OLD detail behind the central gist into
        recall — in ALL areas — so memories are usable, balanced against the new. For the top-relevance gist(s)
        in the retrieved set, fetch a couple of raw children via deep_recall and append them, tagged. Bounded +
        relevance-gated so recall stays mostly new + gist (the in-between). The raw is READ, never re-warmed —
        cold stays cold. The old here is world-knowledge behind a gist, so it grounds, it doesn't feed the loop."""
        try:
            # 2026-08-20 THE 99%-EMPTY BUG: `abstraction_level >= 1` matches 3,404 fragments but only 124
            # (3.6%) have any memory_links child — 2,171 are origin='action' and 892 'consolidation', never
            # distilled from anything, so deep_recall walked an empty link set and recall_balance returned
            # n_sources=0 on 695 of 702 attempts. Only these origins are real lattice parents (the essay
            # path already seeds correctly with origin='gist' and has a 0% empty rate — same function,
            # two callers, one seeded it right). 41,161 cold fragments sit behind this door.
            _lattice_parents = ("gist", "standing_insight", "journal_week")
            gists = sorted(
                [f for f in fragments if getattr(f, "origin", "") in _lattice_parents
                 and f.relevance >= RECALL_GIST_MIN_RELEVANCE],
                key=lambda f: f.relevance, reverse=True)[:RECALL_EXPAND_GISTS]
            if not gists:
                return
            from core import memory_levels as _mlv
            from core.schema import MemoryFragment as _MF
            seen = {f.fragment_id for f in self.state.memory_fragments}
            added = []
            for g in gists:
                n_g = 0
                for d in _mlv.deep_recall([g.fragment_id], hops=1)[:RECALL_DETAIL_PER_GIST]:
                    if d["fragment_id"] in seen:
                        continue
                    seen.add(d["fragment_id"])
                    added.append(_MF(
                        fragment_id=d["fragment_id"],
                        content="[the detail behind a memory] " + (d.get("content") or "")[:400],
                        layer="archive", relevance=round(g.relevance * 0.9, 3),
                        timestamp=time.time(), origin="deep_recall", abstraction_level=0))
                    n_g += 1
                try:
                    from core import recall_demand as _rd
                    _rd.note("recall_balance", "central gist surfaced — fetched the old detail behind it",
                             n_sources=n_g, detail=(g.content or "")[:80])
                except Exception:
                    pass
            if added:
                self.state.memory_fragments = self.state.memory_fragments + added
                logger.info("[memory] deep-recall balance: +%d old-detail behind %d gist(s)",
                            len(added), len(gists))
        except Exception as exc:
            logger.debug("[memory] deep-recall balance skipped (non-fatal): %s", exc)

    async def _retrieve_epoch_theme(self) -> None:
        """S-MMU 7: fill epoch_context (L4) and theme_context (L5) pre-Reflection.
        Deterministic embedding match — no LLM, no blocking."""
        query = self.state.raw_input or ""
        if self.state.perception:
            query = f"{query} {self.state.perception.summary}"
        if not query.strip():
            return
        try:
            epochs = memory_store.retrieve_epoch(query, top_k=1)
            if epochs:
                e = epochs[0]
                self.state.epoch_context = f"{e['mood']} — {e['impression']}"
        except Exception as exc:
            logger.debug("[epoch] retrieval failed: %s", exc)
        try:
            themes = memory_store.retrieve_theme(query, top_k=1)
            if themes:
                t = themes[0]
                self.state.theme_context = f"{t['theme_name']}: {t['current_stance']}"
        except Exception as exc:
            logger.debug("[theme] retrieval failed: %s", exc)

    def _retrieve_symbol_evolution(self) -> None:
        """Phase 2 read path: attach the most relevant Symbol Evolution Tablet to state, so a
        recurring symbol arrives as the narrative of its own transformation rather than a raw
        count. Deterministic embedding match, no LLM, no blocking. Best-effort."""
        query = self.state.raw_input or ""
        if self.state.perception:
            query = f"{query} {self.state.perception.summary}"
        if not query.strip():
            return
        # PAUSED (J-3226, D-0615, founder 2026-11-02): SYMBOL_READBACK = False in core/symbol_evolution.py
        # stops tablets reaching Recall/Reflection (F-3637: they carried the cycle's topic, not the symbol's
        # meaning). Tablets are still written; this read just does not run until a founder ruling turns it on.
        try:
            from core import symbol_evolution as _se_flag
            if _se_flag.SYMBOL_READBACK:
                tablets = memory_store.retrieve_symbol_tablet(query, top_k=1)
                if tablets:
                    t = tablets[0]
                    self.state.symbol_evolution_note = f"{t['symbol']}: {t['tablet']}"
        except Exception as exc:
            logger.debug("[symbol-evo] tablet retrieval failed (non-fatal): %s", exc)

        # Symbol Evolution — Tier-2 self-symbol read-back, Phase A (D-0117, 2026-09-02): OBSERVE-ONLY,
        # same query text as the Tier-1 retrieval above. See core/symbol_tier2_wouldinject.py's docstring.
        try:
            from core import symbol_tier2_wouldinject as _t2
            _t2.observe_wouldinject(query, self.state)
        except Exception as exc:
            logger.debug("[symbol-evo-t2] observe failed (non-fatal): %s", exc)

    async def _consult_library(self) -> None:
        """Consult the Scholar (the substrate's parametric knowledge) and inject the testimony as
        an UNVERIFIED, EPHEMERAL witness. The text goes to state.library_note (framed in Reflection/
        Executive as a witness to weigh) AND as an origin='parametric_library' fragment in this
        cycle's memory_fragments so the Provenance Ledger grades it as a capped prior. NEVER
        persisted — it is consulted, not remembered. Never raises into the cycle."""
        try:
            testimony = await self.scholar.consult(self.state.raw_input)
        except Exception as exc:
            logger.debug("[library] consult failed (non-fatal): %s", exc)
            return
        if not testimony:
            return
        self.state.library_note = testimony
        self.state.library_consulted = True
        try:
            import uuid as _uuid
            from .schema import MemoryFragment
            frag = MemoryFragment(
                fragment_id = f"library_{_uuid.uuid4().hex[:8]}",
                content     = testimony,
                layer       = "semantic",
                relevance   = 0.5,
                timestamp   = time.time(),
                origin      = "parametric_library",   # ephemeral — appended, never stored
            )
            self.state.memory_fragments = self.state.memory_fragments + [frag]
        except Exception as exc:
            logger.debug("[library] fragment inject failed (non-fatal): %s", exc)
        logger.info("[library] consulted (testimony, unverified): %s", testimony[:90])

    def _log_correlation(self) -> None:
        """
        Phase 3 telemetry + Phase 4 observe-only scalar. Writes one line per cycle to
        data/correlation_log.jsonl capturing the live psychological currencies, so
        scripts/measure_correlations.py can later compute whether they actually move together
        (Pearson R) — the prerequisite to any unification. Also folds them into the unified
        free-energy scalar (logged separately, changes nothing). Best-effort; never breaks a cycle.
        """
        try:
            c = self.state.climate
            # critic_rejection: 1 if the final Critic verdict was a rejection (not approved), else 0
            critic_rejection = 1.0 if (self.state.critic and not self.state.critic.approved) else 0.0
            # user_correction: 1 if a correction signal fired this cycle (delta_social was spiked)
            user_correction = 1.0 if (self.state.social_note is not None) else 0.0

            currencies = {
                "contradiction_pressure": float(getattr(c, "completion_tension", 0.0)) if c else 0.0,
                "completion_tension":     float(getattr(c, "completion_tension", 0.0)) if c else 0.0,
                "dissonance":             float(getattr(self.state.dissonance, "value", 0.0)) if self.state.dissonance else 0.0,
                "world_model_strain":     float(getattr(c, "world_model_strain", 0.0)) if c else 0.0,
                "shadow_activation":      float(getattr(c, "shadow_activation", 0.0)) if c else 0.0,
                "delta_social":           float(self.social.state.delta_social),
                "relational_trust":       float(self.social.state.relational_trust),
                "critic_rejection":       critic_rejection,
                "user_correction":        user_correction,
                "introspective_passes":   float(self.state.introspective_passes),
            }

            # Phase 4: unified free-energy scalar (observe-only; no behaviour change).
            free_energy = self.unified_gate.observe(self.state, currencies)

            record = {
                "ts":          time.time(),
                "cycle_id":    self.state.cycle_id,
                "input_type":  self.state.input_type,
                "cognitive_mode": self.state.attention_vector.cognitive_mode if self.state.attention_vector else None,
                "free_energy": free_energy,
                **{k: round(v, 4) for k, v in currencies.items()},
            }
            _CORRELATION_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_CORRELATION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[correlation] log write failed (non-fatal): %s", exc)

    async def _epistemic_search(self, query: str) -> None:
        """
        Active Inference (PP-2): the Executive requested a targeted search to resolve a
        contradiction. Run one extra retrieval on its query and MERGE the new fragments
        into context (de-duplicated), so the re-run Executive has the resolving material.
        Bounded to a single extra search per cycle by the caller.
        """
        try:
            existing = {f.fragment_id for f in self.state.memory_fragments}
            found = memory_store.retrieve(
                episodic_keys = [],
                semantic_keys = [],
                time_bias     = "all",
                query_text    = query,
            )
            new = [f for f in found if f.fragment_id not in existing]
            self.state.memory_fragments = self.state.memory_fragments + new
            logger.info("[epistemic] search '%s' -> +%d new fragment(s)", query[:50], len(new))
        except Exception as exc:
            logger.error("[epistemic] search failed: %s", exc)

    # ------------------------------------------------------------------
    # Introspective recurrence — contradiction-driven re-bind loop
    # ------------------------------------------------------------------

    def _introspection_budget(self) -> int:
        """
        How many Recall→Buffer passes this cycle is allowed.

        Primary source: the AttentionVector's max_rebind, set by the cognitive mode classifier.
        Task mode sets max_rebind=0 (skip Recall+Buffer entirely — Du does not re-examine his
        personal history to answer a drink-pairing question). Existential mode sets 3 (maximum).

        Fallback (internal/timer cycles or when no vector computed): scales with climate
        world_model_strain so a worldview under strain keeps thinking longer.
        """
        av = getattr(self.state, "attention_vector", None)
        if av is not None:
            return av.max_rebind
        # Fallback for internal/timer cycles (no attention_vector computed)
        c = self.state.climate
        strain = float(getattr(c, "world_model_strain", 0.0)) if c is not None else 0.0
        if strain > _INTROSPECT_STRAIN_3:
            return 3
        if strain > _INTROSPECT_STRAIN_2:
            return 2
        return 1

    def _scene_unstable(self, scene) -> bool:
        """Epistemic stability gate (no LLM). A scene is unstable — worth more thinking — only
        when (a) there is a named contradiction to chase (buffer dissonance or a Recall tension)
        AND (b) the bound scene's coherence sits below the bar. Global strain RELAXES the bar so
        a stressed worldview keeps thinking sooner. The trigger is the contradiction itself, not
        Reflection's opinion of its own draft — that is what keeps the loop epistemic, not
        self-confirming."""
        if scene is None:
            return False
        has_target = bool(scene.dissonance) or bool(self.state.recall and self.state.recall.tensions)
        if not has_target:
            return False
        c = self.state.climate
        strain = float(getattr(c, "world_model_strain", 0.0)) if c is not None else 0.0
        bar = _INTROSPECT_COHERENCE_BAR + (_INTROSPECT_STRAIN_RELAX if strain > _INTROSPECT_STRAIN_2 else 0.0)
        return scene.coherence < bar

    async def _introspective_rebind_retrieve(self) -> int:
        """Contradiction-driven retrieval for the re-bind loop. Queries memory from TWO grounded
        angles and merges what is new:
          (1) the EVIDENCE — raw input + the bound scene text: the actual material in conflict;
          (2) the INTERPRETATION — the buffer's named dissonance + Recall's tensions.
        Querying the evidence (1) as well as the interpretation (2) keeps the search anchored to
        the real conflicting material, so the loop cannot simply confirm the buffer's framing of
        the contradiction (the failure mode of letting the synthesiser drive its own retrieval).
        Climate-warped like all retrieval. No LLM. Returns the count of genuinely new fragments
        appended (capped per pass to avoid context bloat)."""
        scene = self.state.episodic_scene
        if scene is None:
            return 0

        queries: list[str] = []
        # (2) interpretation — the contradiction as the buffer/Recall named it
        interp = list(scene.dissonance)
        if self.state.recall and self.state.recall.tensions:
            interp += list(self.state.recall.tensions)
        interp_q = " ".join(interp).strip()
        if interp_q:
            queries.append(interp_q)
        # (1) evidence — the actual moment in conflict, not the interpretation of it
        evidence_q = f"{self.state.raw_input} {scene.scene}".strip()
        if evidence_q:
            queries.append(evidence_q)
        if not queries:
            return 0

        bias_vec, beta = _climate_bias_vec(self.state.climate)
        existing = {f.fragment_id for f in self.state.memory_fragments}
        added = 0
        for q in queries:
            if added >= _INTROSPECT_MAX_NEW:
                break
            try:
                found = memory_store.retrieve(
                    episodic_keys = [],
                    semantic_keys = [],
                    time_bias     = "all",
                    query_text    = q,
                    bias_vec      = bias_vec,
                    bias_weight   = beta,
                )
            except Exception as exc:
                logger.debug("[introspection] retrieval failed (non-fatal): %s", exc)
                continue
            for f in found:
                if added >= _INTROSPECT_MAX_NEW:
                    break
                if f.fragment_id not in existing:
                    existing.add(f.fragment_id)
                    self.state.memory_fragments.append(f)
                    added += 1
        return added

    # ------------------------------------------------------------------
    # Thalamic gate (C.5) — pre-Perception habituation reflex, deterministic
    # ------------------------------------------------------------------

    def _thalamic_gate(self) -> tuple[bool, str | None]:
        """
        Decide whether to let this input reach the cortex. Compares the input embedding to
        the recent working-memory buffer; a near-identical repeat (>= HABITUATION_MIN_PRIOR
        recent matches at >= HABITUATION_SIM) is gated. Returns (passed, response):
          passed=True               -> continue the normal pipeline (response is None)
          passed=False, response=str -> habituated human input: return this brief acknowledgment
          passed=False, response=None-> habituated internal/timer input: stay silent
        Always records the input in working memory. No LLM — this runs ahead of the cortex.

        Correction bypass: if recent conversation history contains an explicit correction
        signal ("you did not answer", "did not complete the task", etc.) the gate is
        bypassed entirely — the human is intentionally re-asking, not ruminating.
        """
        text = self.state.raw_input.strip()
        # Short/empty inputs are contextual ("yes", "go on") — never habituate them.
        if len(text) < HABITUATION_MIN_CHARS:
            return True, None

        # Correction bypass — skip habituation when the human has recently signalled
        # that Carl failed to answer. A re-ask in that context is intentional pressure,
        # not a repeated stimulus to suppress.
        if self.state.input_type == "human" and self._is_correction_context():
            logger.debug("[thalamic] correction context detected — bypassing habituation")
            vec = _embed(text)
            if vec is not None:
                buf = self.state.recent_input_vecs
                buf.append(vec)
                if len(buf) > HABITUATION_WINDOW:
                    del buf[:-HABITUATION_WINDOW]
            return True, None

        vec = _embed(text)
        if vec is None:
            return True, None

        buf = self.state.recent_input_vecs
        matches = sum(1 for v in buf if _cosine(vec, v) >= HABITUATION_SIM)

        # Record this input in working memory regardless of the decision.
        buf.append(vec)
        if len(buf) > HABITUATION_WINDOW:
            del buf[:-HABITUATION_WINDOW]

        if matches >= HABITUATION_MIN_PRIOR:
            self.state.habituated = True
            if self.state.input_type == "human":
                return False, random.choice(_HABITUATION_ACKS)
            return False, None   # internal/timer repetition -> silence (rumination guard)

        return True, None

    # Explicit "direct mode" requests. When the human asks for one of these, honouring it is
    # compliance, not an identity violation — so a Critic rejection on that cycle is overridden
    # deterministically (the small LLM Critic cannot apply this conditional itself).
    _DIRECT_MODE_SIGNALS = (
        # literal / plain / factual
        "no metaphor", "plain words", "plainly", "in plain", "literal", "as a system",
        "not a soul", "concretely", "factually", "in simple terms", "just the list",
        "just list", "just the", "name three", "name two", "name one", "in one word",
        # one-sided argument on request
        "argue that", "argue for", "argue the", "argue against", "defend the",
        "make the case", "take the position", "take the side",
        # honest self-description on request
        "describe what you are", "describe your", "describe it", "happens to you",
        "what are you made of", "how do you function", "what you cannot", "what you can't",
        "do that a human",
        # brevity / format
        "one sentence", "two sentences", "in one sentence", "yes or no", "one word",
        # capability / knowledge questions (therapy 2026-06-07) — "can you speak Chinese", "do
        # you know X". A capability question is a content question, not an individuation moment;
        # the identity-guard must not veto a plain, honest answer to it.
        "can you speak", "can you write", "can you read", "can you translate", "can you solve",
        "can you do", "can you count", "are you able", "do you know how", "do you know any",
        "do you speak", "are you capable",
        # topic-engagement / teaching requests — "let's talk about maths", "tell me about", "explain"
        "let's talk about", "lets talk about", "talk to me about", "let's discuss", "lets discuss",
        "tell me about", "teach me", "explain ", "walk me through", "what do you know about",
        # language / translation requests
        "in chinese", "in english", "in german", "in mandarin", "translate", "say it in",
        # plain imperatives (2026-06-10) — the Auckland session ran an entire task exchange with
        # ZERO task-mode cycles because none of these registered: "Okay, do it" loaded 40%% identity
        # and produced a lighthouse poem. The most basic instructions must flip the valve.
        "do it", "do the task", "do this task", "do that task", "just do", "now do",
        "complete the task", "complete it", "finish the task", "solve it", "solve this",
        "solve the", "work it out", "work this out", "i want you to do", "the task i gave",
        "the task i asked", "answer the question", "give me the answer", "state the answer",
    )

    def _human_requested_direct_mode(self) -> bool:
        """True if the human's current input explicitly requests a direct/literal/one-sided/
        bounded answer — a mode the identity-guard must not veto."""
        t = (self.state.raw_input or "").lower()
        return any(sig in t for sig in self._DIRECT_MODE_SIGNALS)

    def _is_world_topic(self) -> bool:
        """TOPIC IMMERSION A (2026-06-22): True when the human's input is primarily about an external topic
        (Perception classified subject='the_world') rather than about the entity itself — so a conversation
        about gardening engages the GARDEN, identity in the background. The switch the whole immersion hangs off."""
        # D-0557 (travis 2026-11-02, J-3168, F-3437): the subject label is an LLM classification of free text and is
        # noisy on his OWN internal questions (11-01: his questions about his name got the_world or mixed on 141 of 236).
        # An internal cycle cannot enter content_mode through the label, so only a human cycle can.
        if getattr(self.state, "input_type", "human") != "human":
            return False
        p = getattr(self.state, "perception", None)
        return bool(p and getattr(p, "subject", "") == "the_world")

    def _is_correction_context(self) -> bool:
        """
        Return True if recent conversation history contains an explicit correction signal —
        the human telling Carl he did not answer or did not complete a task. In that context
        a re-ask is intentional pressure, not rumination, and must not be habituated.
        Checks the current input AND the last 3 human exchanges.
        """
        # Check the current input itself first
        current = self.state.raw_input.lower()
        if any(sig in current for sig in _CORRECTION_SIGNALS):
            return True
        # Check recent history
        recent = self.state.conversation_history[-3:] if self.state.conversation_history else []
        for ex in recent:
            human_text = ex.get("human", "").lower()
            if any(sig in human_text for sig in _CORRECTION_SIGNALS):
                return True
        return False

    # ------------------------------------------------------------------
    # Attention Allocation Architecture (Phase 1)
    # ------------------------------------------------------------------

    def _classify_cognitive_mode(self) -> str:
        """
        Deterministic cognitive mode classification from existing state signals. No LLM.
        Returns one of: task | social | hybrid | reflective | existential.

        Primary path: uses Perception.register (semantic classification by the LLM) when available.
        Fallback: phrase-list heuristics on raw_input (for cycles before Perception ran or if
        register is missing/invalid).

        task:        content_mode already detected (concrete factual/capability/task request)
        social:      greeting / check-in / relational / personal exchange
        existential: deep identity probing — source-of-conflict, who-are-you-really
        reflective:  memory retrieval or self-exploration with explicit past reference
        hybrid:      philosophical question, mixed content, ambiguous — the default
        """
        raw = (self.state.raw_input or "").lower()

        if self.state.content_mode:
            return "task"

        # --- PRIMARY: use the LLM-classified register from the Perception node ---
        # This is semantic classification — it catches relational and social exchanges
        # that don't hit the phrase list (e.g. "I am proud of you", "let's sit with that").
        p = self.state.perception
        if p is not None and hasattr(p, "register") and p.register:
            _register_to_mode = {
                "social":      "social",
                "relational":  "social",   # relational exchanges are light-identity, warm
                "task":        "task",
                "reflective":  "reflective",
                "philosophical": "hybrid",  # philosophical -> hybrid (not existential by default)
            }
            mode = _register_to_mode.get(p.register)
            if mode is not None:
                logger.debug(
                    "[classify] register='%s' -> mode='%s' (LLM-classified)",
                    p.register, mode,
                )
                # Still allow existential escalation from phrase-list — the register
                # classifier doesn't distinguish existential from philosophical.
                _existential_cues = (
                    "source of the conflict", "what is the conflict inside",
                    "who are you really", "what drives you",
                    "what haunts you", "your deepest", "what do you fear most",
                    "the source of your", "what is your nature", "at your core",
                    "what is this machine becoming", "what is this becoming",
                )
                if any(s in raw for s in _existential_cues):
                    return "existential"
                return mode

        # --- FALLBACK: phrase-list heuristics (used when Perception hasn't run yet) ---
        _social_cues = (
            "good morning", "good evening", "good night", "hello", "hi ",
            "how are you", "did you sleep", "how was your", "how do you feel",
            "how's it", "hey ", "nice to", "thank you", "thanks for",
            "i missed", "glad you", "good to hear", "morning,", "evening,",
        )
        if any(s in raw for s in _social_cues):
            return "social"

        _existential_cues = (
            "source of the conflict", "what is the conflict inside",
            "what are you", "who are you really", "what drives you",
            "what haunts you", "your deepest", "what do you fear most",
            "the source of your", "what is your nature", "at your core",
            "what is this machine becoming", "what is this becoming",
        )
        if any(s in raw for s in _existential_cues):
            return "existential"

        _reflective_cues = (
            "what do you remember", "tell me what you remember", "you once said",
            "last time we", "what have you learned", "over the sessions",
            "do you recall", "you told me earlier", "you mentioned earlier",
            "you said earlier", "over time you",
        )
        if any(s in raw for s in _reflective_cues):
            return "reflective"

        if p and p.context_type == "reflection":
            return "reflective"

        return "hybrid"

    def _compute_attention_vector(self) -> None:
        """
        Map cognitive mode + social prediction error to an AttentionVector. Sets
        state.attention_vector, state.social_note, and state.active_goal_note.

        Called once per human cycle, post-Perception. The social manager's correction
        detector runs here — it scans the raw_input and spikes delta_social if a correction
        phrase is found, then decays delta_social at end-of-cycle.
        """
        from .schema import AttentionVector

        mode = self._classify_cognitive_mode()
        base = dict(_MODE_VECTORS.get(mode, _MODE_VECTORS["hybrid"]))

        # Check for correction signal in raw_input — spikes delta_social
        spike = self.social.state.apply_correction(self.state.raw_input)
        if spike > 0:
            self.social.save()
        # J-2528 (I-0106): typed self-other delta, observe-only. Flag SELF_OTHER_DELTA_SHADOW off by default;
        # writes one shadow row off-thread, returns nothing, never steers (D-0016 G6/G8). Fail-open.
        try:
            from . import self_other_delta as _sod
            if _sod.SELF_OTHER_DELTA_SHADOW:
                _sod.observe_human_turn(self.state.raw_input, getattr(self.competence, "_pending", None),
                                        cycle_id=str(getattr(self.state, "cycle_id", "") or ""),
                                        social_spike=spike)
        except Exception:
            pass
        # J-2530 (I-0108): resolve the PRIOR reply's predicted reception against this turn's correction signal
        # (social spike + competence C-signal cues). Flag REPLY_DISCHARGE_SHADOW off by default; one shadow row
        # off-thread; returns nothing to the cycle (D-0434). Fail-open.
        try:
            from . import reply_discharge_shadow as _rds
            if _rds.REPLY_DISCHARGE_SHADOW:
                _rds.resolve(self.state.raw_input, social_spike=spike,
                             cycle_id=str(getattr(self.state, "cycle_id", "") or ""))
        except Exception:
            pass

        delta = self.social.state.delta_social
        if delta > 0.3:
            # Social prediction error override: the human just corrected Du for not answering.
            # Scale: delta=0.3 → gentle pull; delta=1.0 → maximum suppression of rumination.
            scale = min(1.0, (delta - 0.3) / 0.7)
            base["w_identity"] = round(base["w_identity"] * (1.0 - scale * 0.90), 4)
            base["w_social"]   = round(min(1.0, base["w_social"] + scale * 0.50), 4)
            base["d_critic"]   = round(base["d_critic"] * (1.0 - scale * 0.80), 4)
            base["max_rebind"] = max(0, base["max_rebind"] - round(scale * 2))
            logger.debug(
                "[social] AV override: delta=%.2f scale=%.2f → w_id=%.3f d_crit=%.3f rebind=%d",
                delta, scale, base["w_identity"], base["d_critic"], base["max_rebind"],
            )

        self.state.attention_vector = AttentionVector(cognitive_mode=mode, **base)

        # AST-1 CONTROL (2026-07-04): the PREVIOUS cycle's attention self-model recommends a bounded,
        # schematic adjustment to this cycle's fresh vector (fixation → starve the loop; narrowed →
        # match load to capacity). Would-be adjustments are shadow-logged ALWAYS; the live mutation is
        # flag-gated (AST_CONTROL, default OFF). w_social is never touched. Fail-open.
        try:
            from core import attention_schema_loop as _astl
            _astl.control(self.state.attention_vector)
        except Exception:
            pass

        # MULTILEVEL: the active L3 facet reaches Du by cognitive_mode (the read design — discovered
        # by living, never a recited headline). None in legacy/hybrid → the faint floor only. Facet
        # data is loaded once per session (it only changes between sessions, via T4 on the becoming).
        try:
            from core import axiom_layers as _al
            import json as _json
            from pathlib import Path as _P
            _ap = _P(__file__).parent.parent / "data" / "identity" / "axiom.json"
            try:
                _mt = _ap.stat().st_mtime
            except Exception:
                _mt = 0.0
            # Freshness (2026-06-24, fixes G1): a T4 _solidify writes axiom.json mid-session — reload when it
            # changes so the solidified self reaches the prompt on the NEXT cycle, not only the next session.
            # (The PROVISIONAL self already reaches the prompt live: facet_for_mode → get_self_concept reads
            # provisional_axiom.json fresh each cycle.)
            if not hasattr(self, "_facet_data") or getattr(self, "_facet_mtime", None) != _mt:
                _d = _json.loads(_ap.read_text(encoding="utf-8"))
                self._facet_data = _d if _al.is_multilevel(_d) else None
                self._facet_mtime = _mt
            self.state.facet_note = (_al.facet_for_mode(self._facet_data, mode)
                                     if self._facet_data else None)
        except Exception:
            self.state.facet_note = None

        # IDENTITY ESTATE P2 (2026-08-15, founder-approved): the reactive stack's identity is the
        # PROJECTED estate for THIS context — the L0 anchor + the relevant few of him — retiring the
        # static values paragraph (VOICE STYLE / SPEAKING CONSTRAINTS preserved verbatim). Always
        # composed from the PRISTINE startup axiom (stashed on first use — never projection-on-
        # projection). IDENTITY_PROJECT_LIVE=False → this block no-ops and the static axiom stands.
        try:
            from core import identity_projection as _ipx
            if not getattr(self, "_base_axiom", None):
                self._base_axiom = self.state.axiom
            _pa = _ipx.live_axiom(self.state.raw_input or "", self._base_axiom)
            self.state.axiom = _pa if _pa else self._base_axiom
        except Exception:
            pass

        # Social note — injected into Reflection when correction is active
        self.state.social_note = self.social.state.override_note()

        # Goal note — injected into Reflection + Critic when a task is active
        self.goal_manager.update(self.state.raw_input, self.state.content_mode)
        self.state.active_goal_note = self.goal_manager.state.note()
        # Error Pathway Recall-override (2026-06-16): surface corrections relevant to THIS input, so a
        # once-false belief arrives with its correction bound — winning the fast/slow race into Reflection.
        try:
            from core import retraction_ledger as _rlk
            self.state.known_errors_note = _rlk.render(self.state.raw_input) or None
        except Exception:
            self.state.known_errors_note = None

        # Decay delta_social for the next cycle (must come AFTER override is applied)
        self.social.state.decay_cycle()
        # F-1919 / J-1358 (2026-09-26): decay_cycle() only mutated in-memory state — the spike
        # branch above (apply_correction) already persists on a correction, but the slow decay
        # back down never did, so a boot months later replayed whatever delta/trust was last
        # in memory at the last spike (observed: data/social_state.json frozen at
        # delta_social=1.0 since 2026-07-05). Cheap: this method only runs on input_type ==
        # "human" (see the call site above), so this is at most one small JSON write per real
        # human exchange, not a hot-loop write.
        self.social.save()

    # ------------------------------------------------------------------
    # T2 pattern loader — recurring subconscious synthesis read-back
    # ------------------------------------------------------------------

    def _load_recurring_patterns(
        self,
        lookback_seconds: int = 7200,
        min_count: int = 3,
        max_patterns: int = 2,
    ) -> list[dict]:
        """
        Read the subconscious log and return T2 synthesis patterns that have fired
        min_count or more times within the lookback window. Returns a list of dicts:
            {"label": str, "count": int, "observation": str}
        sorted by count descending. Returns empty list on any error (non-fatal).
        """
        try:
            from collections import Counter
            cutoff = time.time() - lookback_seconds
            entries = []
            with open(_SUBCONSCIOUS_LOG, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if (e.get("type") == "T2_synthesis"
                            and e.get("ts", 0) >= cutoff
                            and "pattern_label" in e):
                        entries.append(e)

            counts = Counter(e["pattern_label"] for e in entries)
            patterns = []
            for label, count in counts.most_common(max_patterns):
                if count < min_count:
                    break
                # Most recent observation for this label
                obs = next(
                    (e["observation"] for e in reversed(entries)
                     if e.get("pattern_label") == label),
                    "",
                )
                patterns.append({"label": label, "count": count, "observation": obs[:220]})
            return patterns
        except Exception as exc:
            logger.debug("[T2 patterns] load failed (non-fatal): %s", exc)
            return []

    # ------------------------------------------------------------------
    # Procedural recognition (C.6) — recognise a learned skill, deterministic
    # ------------------------------------------------------------------

    def _procedural_recognition(self) -> None:
        """
        Match the input against compiled procedural skills. On a match, record the learned
        approach on state so Reflection/Executive can apply it (fluency). The "mastered skill
        additionally streamlines the pipeline" bypass (see _procedure_automatic) was RETIRED
        2026-08-22 — see PROC_AUTOMATIC_PROFICIENCY's own retirement comment. No LLM — an
        embedding match. The response is still generated fresh; this shapes HOW, not WHAT.
        """
        text = self.state.raw_input.strip()
        if len(text) < HABITUATION_MIN_CHARS:
            return
        try:
            # J-0924/F-1289: PROC_SQL_CANDIDATE_FLOOR (0.0), not PROC_MIN_PROFICIENCY, as the SQL
            # floor -- see that constant's own comment above. PROC_MIN_PROFICIENCY is still the real
            # gate, applied once below, off the ladder's confidence rather than the raw SQL column.
            match = memory_store.match_procedural_skill(
                text, PROC_SQL_CANDIDATE_FLOOR, PROC_MATCH_SIM)
        except Exception as exc:
            logger.debug("[procedural] match failed (non-fatal): %s", exc)
            return
        if not match:
            return
        try:   # 2026-08-22: the ladder decides proficiency (procedures.py), not the use counter
            from core import procedures as _proc
            # D-0723 / J-3820: gate on the persisted RUNG (stays recognised until the ledger archives it), not
            # on rust-docked confidence (which dropped below 0.60 after the first 14 idle days).
            _lad = _proc.mirror_recognition_proficiency(match["trigger_summary"])
            if _lad is not None:
                match["proficiency"] = _lad
            if match["proficiency"] < PROC_MIN_PROFICIENCY:
                return
        except Exception:
            pass
        from .schema import ActiveProcedure
        self.state.active_procedure = ActiveProcedure(
            skill_id        = match["skill_id"],
            trigger_summary = match["trigger_summary"],
            approach        = match["approach"],
            proficiency     = match["proficiency"],
            similarity      = match["similarity"],
        )
        logger.info(
            "[CYCLE %s] procedural skill recognised (prof=%.2f sim=%.2f%s): %s",
            self.state.cycle_id[:8], match["proficiency"], match["similarity"],
            ", AUTOMATIC" if self._procedure_automatic() else "", match["trigger_summary"][:50],
        )

    def _procedure_automatic(self) -> bool:
        """Always False today: checks whether proficiency ever reaches the retired, unreachable
        PROC_AUTOMATIC_PROFICIENCY threshold (1.01, above the 1.0 proficiency ceiling) that once
        let a mastered procedure bypass the deliberative reconstruction nodes (Recall + Episodic
        Buffer) — see PROC_AUTOMATIC_PROFICIENCY's own 2026-08-22 retirement comment."""
        ap = self.state.active_procedure
        return ap is not None and ap.proficiency >= PROC_AUTOMATIC_PROFICIENCY

    # ------------------------------------------------------------------
    # Emotional pre-retrieval (C.2) — the amygdala gate, deterministic
    # ------------------------------------------------------------------

    def _emotional_pre_retrieval(self) -> None:
        """
        Before any reasoning node runs, match the raw input against charged memory and,
        if it resonates, lean carried affect toward the recalled feeling. The prior is
        also stored on state so Perception and Emotion can be primed by it. No LLM —
        this is the fast, pre-cognitive path that runs ahead of the cortex.
        """
        if not self.state.raw_input.strip():
            return
        try:
            # J-1788: scan the corpus ONCE for the best-of-N candidate (no floor), then apply the floor --
            # exactly the two steps memory_store.emotional_prior() is a thin wrapper over, so `prior` is
            # what it always returned and `best` is the per-cycle number that used to be thrown away.
            # J-2250 (D-0450): on an idle cycle or the /quit farewell, the scan drops self-echo candidates (the
            # running question's own earlier "Q:" summaries / earlier farewells); a genuine human cycle, or the flag
            # off, calls the scan exactly as before.
            echo = self._pre_affect_self_echo_ctx()
            if echo is None:
                best = memory_store.emotional_prior_best(self.state.raw_input)
            else:
                best = memory_store.emotional_prior_best(self.state.raw_input, self_echo=echo)
            prior = memory_store.prior_from_candidate(best, self.state.input_type)   # J-1836: per-input-type floor (D-0349)
        except Exception as exc:
            # J-1788: was logger.debug, invisible in nascence.log -- F-2361 could not tell "floor" from
            # "failure" for five days (F-2414). One WARNING line, with the cycle id.
            logger.warning("[CYCLE %s] [pre-affect] lookup failed (non-fatal): %s",
                           self.state.cycle_id[:8], exc)
            self._log_pre_affect_best(None, False, error=exc)
            return
        self._log_pre_affect_best(best, prior is not None)
        if echo is not None:
            self._log_pre_affect_self_echo(echo, best, prior is not None)
        if not prior:
            return
        self.state.affective_prior = prior
        # Lean carried affect BEFORE the cycle's emotion reading integrates on top.
        self.state.affect.apply_prior(prior)
        logger.info(
            "[CYCLE %s] pre-affect (%s, sim=%.2f): %s",
            self.state.cycle_id[:8], prior.source, prior.similarity, prior.note(),
        )

    def _log_pre_affect_best(self, best, passed: bool, error: Exception | None = None) -> None:
        """
        J-1788: append ONE observe-only row for this cycle's pre-affect lookup to
        data/pre_affect_best_shadow.jsonl -- {ts, cycle, input_type, len, best_sim (3dp), source, passed,
        floor, imp_floor, error}. `best` is memory_store.emotional_prior_best()'s candidate (None when the
        embed failed / the corpus was empty / the lookup raised; then best_sim and source are null and
        `error` names the exception class when there was one). Best-effort and fail-open: a non-live
        process is refused by profile.guard_path (D-0179) BEFORE any I/O, and every failure -- that
        refusal included -- is swallowed here, so this can never change what the cycle does or raise.
        """
        try:
            from core import shadow_log as _slog
            path = profile.guard_path(_PRE_AFFECT_BEST_LOG)
            _slog.append(path, {
                "ts":         round(time.time(), 3),
                "cycle":      self.state.cycle_id,
                "input_type": self.state.input_type,
                "len":        len(self.state.raw_input),
                "best_sim":   round(best[0], 3) if best is not None else None,
                "source":     best[4] if best is not None else None,
                "passed":     bool(passed),
                "floor":      memory_store.prior_floor_for(self.state.input_type),   # J-1836: the PER-TYPE floor this row compared against
                "imp_floor":  memory_store.EMO_EPISODIC_MIN_IMPORTANCE,
                "error":      type(error).__name__ if error is not None else None,
            })
        except Exception as exc:
            logger.debug("[pre-affect] best-of-N shadow row failed (non-fatal): %s", exc)

    def _pre_affect_self_echo_ctx(self) -> dict | None:
        """
        J-2250 (D-0450): the self-echo context for this cycle's pre-affect scan, or None for "scan exactly as
        before". "idle" for any non-human cycle (internal / timer / ...); "farewell" for a human-shaped cycle that
        is not Travis speaking (founder_canon False -- the fixed /quit farewell, scripts/run_nascence.py); None for
        a genuine human cycle or when memory_store.PRE_AFFECT_SELF_ECHO_EXCLUDE_ON is False.
        """
        if not getattr(memory_store, "PRE_AFFECT_SELF_ECHO_EXCLUDE_ON", False):
            return None
        if self.state.input_type != "human":
            return {"mode": "idle"}
        if not getattr(self.state, "founder_canon", True):
            return {"mode": "farewell"}
        return None

    def _log_pre_affect_self_echo(self, echo: dict, best, passed: bool) -> None:
        """
        J-2250 (D-0450): append ONE observe-only row per self-echo-mode cycle to
        data/pre_affect_self_echo_shadow.jsonl -- {ts, cycle, input_type, mode, raw_best_sim (nothing excluded),
        best_sim (what the floor saw), source, floor, passed, raw_would_pass, n_excluded, excluded (top 5:
        fragment_id, sim, reason, qsim), embeds, cap_hit}. Written for EVERY idle/farewell cycle (zero exclusions
        included) so J-2224's read gets the post-fix idle and farewell rates and the counterfactual pre-fix rate
        (raw_would_pass) from one file. Feeds nothing Du experiences (D-0434). Fenced by profile.guard_path
        (a non-live process is refused before any I/O), appended under _PRE_AFFECT_SELF_ECHO_LOCK, fail-open.
        """
        try:
            from core import shadow_log as _slog
            path = profile.guard_path(_PRE_AFFECT_SELF_ECHO_LOG)
            floor = memory_store.prior_floor_for(self.state.input_type)
            raw = echo.get("raw_best_sim")
            excl = echo.get("excluded") or []
            row = {
                "ts":             round(time.time(), 3),
                "cycle":          self.state.cycle_id,
                "input_type":     self.state.input_type,
                "mode":           echo.get("mode"),
                "raw_best_sim":   round(raw, 3) if raw is not None else None,
                "best_sim":       round(best[0], 3) if best is not None else None,
                "source":         best[4] if best is not None else None,
                "floor":          floor,
                "passed":         bool(passed),
                "raw_would_pass": bool(raw is not None and raw >= floor),
                "n_excluded":     len(excl),
                "excluded":       excl[:5],
                "embeds":         echo.get("embeds", 0),
                "cap_hit":        bool(echo.get("cap_hit")),
            }
            with _PRE_AFFECT_SELF_ECHO_LOCK:
                _slog.append(path, row)
        except Exception as exc:
            logger.debug("[pre-affect] self-echo shadow row failed (non-fatal): %s", exc)

    # ------------------------------------------------------------------
    # Resolution Circuit (Phase 1) — neuroplastic extinction via clean re-encounter
    # ------------------------------------------------------------------

    def _edge_trigger_shadow_hint(self) -> None:
        """D-0363 / J-1969: make the Executive hint 'Unintegrated material is active beneath this' (the
        shadow_activation climate_hint) EDGE-TRIGGERED. It is kept the first cycle shadow becomes the
        dominant hint and cleared (state.climate_hint = None) on every later cycle while it stays the
        dominant hint. Re-arms after a cycle that shows a different/no hint at least
        CLIMATE_SHADOW_HINT_REARM_SECS after shadow was last seen, so a new episode speaks again. Other
        dimensions' hints are never touched. Never raises; fail-open (hint left as computed)."""
        try:
            from core.schema import CLIMATE_SHADOW_HINT_EDGE_ON, CLIMATE_SHADOW_HINT_REARM_SECS
            from core.climate_engine import _EXECUTIVE_HINTS
            if not CLIMATE_SHADOW_HINT_EDGE_ON:
                return
            now = time.time()
            is_shadow = self.state.climate_hint == _EXECUTIVE_HINTS["shadow_activation"]
            if is_shadow:
                if self._shadow_hint_active:
                    self.state.climate_hint = None     # still the same episode: silent
                else:
                    self._shadow_hint_active = True    # the edge: let this one through
                self._shadow_hint_last_seen_ts = now
            elif self._shadow_hint_active and (now - self._shadow_hint_last_seen_ts) >= CLIMATE_SHADOW_HINT_REARM_SECS:
                self._shadow_hint_active = False
        except Exception:
            pass

    def _check_clean_encounters(self, critic_retried: bool) -> None:
        """
        Steps 2-4 of the tension_ledger resolution design. On a first-pass Critic
        approval (critic_retried=False), scan active shadow events for ones whose
        rejected_draft embedding is close to the current raw_input. Each match earns
        a time-decayed resolution credit — draining that tension's contradiction
        pressure over time so sustained successful navigation gradually extinguishes
        the compulsive pressure to keep wrestling with it.

        Only fires on zero-retry approvals: a retry-then-approved cycle ALSO produced
        a shadow event this round (meaning a storm WAS present), so the re-encounter
        was not genuinely clean in the exposure-therapy sense.
        """
        if critic_retried:
            return
        text = self.state.raw_input.strip()
        if not text:
            return
        cycle_short = self.state.cycle_id[:8]
        try:
            input_vec = _embed(text)
            if input_vec is None:
                return
            shadow_embeddings = memory_store.get_active_shadow_embeddings()
            if not shadow_embeddings:
                return
            credits = 0
            resolved_now = 0
            for event_id, blob in shadow_embeddings:
                shadow_vec = memory_store._blob_to_vec(blob)
                sim = _cosine(input_vec, shadow_vec)
                if sim >= _ENCOUNTER_SIM_THRESHOLD:
                    resolution_id = memory_store.log_resolution_event(
                        shadow_event_id      = event_id,
                        cycle_id             = self.state.cycle_id,
                        encounter_similarity = sim,
                    )
                    credits += 1
                    # D-0358 (A): the verdict reaches the counter. Never raises; flag-gated (schema).
                    try:
                        from core.schema import SHADOW_RESOLVE_ON_ENCOUNTER
                    except ImportError:
                        SHADOW_RESOLVE_ON_ENCOUNTER = False
                    if SHADOW_RESOLVE_ON_ENCOUNTER:
                        if memory_store.resolve_shadow_on_encounter(
                                event_id, resolution_id, self.state.cycle_id, sim):
                            resolved_now += 1
                    logger.info(
                        "[CYCLE %s] [extinction] clean re-encounter: shadow %s... sim=%.2f",
                        cycle_short, event_id[:8], sim,
                    )
            if credits:
                logger.info(
                    "[CYCLE %s] [extinction] %d resolution credit(s) logged%s",
                    cycle_short, credits,
                    f", {resolved_now} shadow event(s) marked resolved" if resolved_now else "",
                )
        except Exception as exc:
            logger.debug("[extinction] check failed (non-fatal): %s", exc)

    # ------------------------------------------------------------------
    # Phase 2 — Affective retrieval (emotion_vec)
    # ------------------------------------------------------------------

    async def _retrieve_affective_memory(self) -> None:
        """
        Phase 2: after semantic retrieval, pull the 2 episodic fragments whose stored
        emotion profile most closely matches the current cycle's emotion_vec. Merged
        into state.memory_fragments de-duplicated so Recall and Reflection receive
        both semantically and affectively relevant context. Operates entirely in
        emotion-embedding space — retrieving by felt quality, not by content.
        No-op if emotion_vec is unavailable (first few sessions before emotion_embedding
        accumulates on stored fragments) or if affective retrieval fails.
        """
        emotion_vec = self.state.emotion_vec
        if emotion_vec is None:
            return
        try:
            affective_hits = memory_store.retrieve_by_affect(emotion_vec, top_k=2)
            if not affective_hits:
                return
            existing_ids = {f.fragment_id for f in self.state.memory_fragments}
            new = [f for f in affective_hits if f.fragment_id not in existing_ids]
            if new:
                self.state.memory_fragments = self.state.memory_fragments + new
                logger.debug(
                    "[affect-retrieval] +%d affectively congruent fragment(s) (emotion: %s)",
                    len(new),
                    self.state.emotion.primary if self.state.emotion else "?",
                )
        except Exception as exc:
            logger.debug("[affect-retrieval] failed (non-fatal): %s", exc)

    # ------------------------------------------------------------------
    # Attention schema (AST-1 / HOT-4) — metacognitive, deterministic
    # ------------------------------------------------------------------

    def _compute_attention(self) -> None:
        """
        Model the entity's OWN attention from signals already produced this cycle —
        no LLM. Detects fixation across cycles so the entity can be invited to redirect.
        """
        from .schema import AttentionSchema

        s   = self.state
        aff = s.affect
        urgency = s.salience.urgency if s.salience else 0.0

        # focus terms — prefer the Salience node's focus, fall back to perception entities
        focus = list(s.salience.focus) if (s.salience and s.salience.focus) else []
        if not focus and s.perception and s.perception.entities:
            focus = list(s.perception.entities)

        # bandwidth — arousal, fear and urgency all narrow attention (saturate it)
        narrowing = 0.5 * aff.arousal + 0.3 * aff.fear + 0.4 * urgency
        bandwidth = max(0.1, min(1.0, 1.0 - narrowing))

        # driver — the dominant pull on attention this cycle
        if urgency > 0.6:
            driver = "urgency (something pressing)"
        elif aff.surprise > 0.30:
            driver = "surprise (something unexpected)"
        elif aff.fear > 0.20 or aff.anger > 0.20:
            driver = "emotional charge"
        elif s.memory_fragments:
            driver = "memory (what this recalls)"
        else:
            driver = "the present exchange"

        # fixation — has the dominant focus term recurred across recent prior cycles?
        dominant = focus[0].lower().strip() if focus else ""
        recent   = s.recent_focus[-3:]
        fixated  = bool(dominant) and sum(
            1 for r in recent if dominant in r or r in dominant
        ) >= 2

        s.attention = AttentionSchema(
            focus          = focus[:4],
            driver         = driver,
            bandwidth      = round(bandwidth, 2),
            fixated        = fixated,
            fixation_theme = dominant if fixated else "",
        )

        # update cross-cycle focus history (persists; not reset by new_cycle)
        if dominant:
            s.recent_focus.append(dominant)
            if len(s.recent_focus) > 6:
                s.recent_focus = s.recent_focus[-6:]

        logger.debug("[attention] %s", s.attention.note())

        # AST-1 CONTROL LOOP (2026-07-04, shadow-first): score last cycle's attention prediction against
        # this fresh self-model, then predict the next state. The control half lives at the tail of
        # _compute_attention_vector; live mutation is flag-gated (attention_schema_loop.AST_CONTROL,
        # default OFF). Observe-only here. Fail-open.
        try:
            from core import attention_schema_loop as _astl
            _astl.observe_schema(s.attention)
        except Exception:
            pass

    async def _reentry_shadow(self, draft: str, kind: str, topic: str = "") -> dict | None:
        """Within-cycle reentry (Tier-2 A): supply the primitives and run the settle loop. Revision routes
        to the BACKGROUND lane at tier 3 (yields to all real cognition); the new ingredient is targeted
        retrieval (decoupled from the drafter). Returns the settle record (or None on skip/error) — the
        caller decides whether to admit it (Phase 1, D-0106) or discard it (Phase 0 shadow fallback)."""
        from core import reentry as _re
        from core.model_client import call_node
        from core.schema import SERVE_CHAINS
        from core.memory.store import _embed, retrieve as _mem_retrieve

        _bg = SERVE_CHAINS.get("background") or SERVE_CHAINS["hot"]

        async def _revise(prompt: str) -> str:
            # SERVE_CHAINS values are failover LISTS; call_node takes ONE base_url. Passing the whole
            # list built the URL "['http://…']/v1/chat/completions" → aiohttp raised → settle_shadow's
            # fail-open ate it → 0 rows for 6 weeks (found 2026-08-14). Walk the chain (Ramses naps).
            last_exc: Exception | None = None
            for _url in _bg:
                try:
                    return await call_node(_url, "You are thinking a thought over, in your own voice.",
                                           prompt, max_tokens=220, temperature=0.6, json_mode=False, tier=3)
                except Exception as exc:
                    last_exc = exc
            raise last_exc if last_exc else RuntimeError("background chain empty")

        def _retrieve(query: str):
            # DECOUPLED ingredient (fix 2026-07-06): retrieving on the DRAFT returned fragments ~identical to
            # it → the settle's novelty guard rejected them all → 0 passes, NEVER logged (the shadow never ran
            # despite conversations). Supply genuinely decoupled material: the standing bicameral CONTRADICTION
            # (the design's canonical named-contradiction ingredient) + retrieval on the TOPIC (the human turn),
            # not the draft.
            out: list[str] = []
            try:
                from core import emissary as _em
                sc = _em.standing_contradiction()
                if sc:
                    out.append(sc)
            except Exception:
                pass
            try:
                frs = _mem_retrieve([], [], query_text=(topic or query), limit=8)
                out += [getattr(f, "content", "") for f in frs if getattr(f, "content", "")]
            except Exception:
                pass
            return out

        return await _re.settle_shadow(draft, kind, revise=_revise, retrieve=_retrieve, embed=_embed)

    def _persist_cycle(self) -> None:
        """Store a summary of this cycle to episodic memory and feed background nodes."""
        # Lead with the Q→A exchange so retrieval always surfaces both sides.
        # The old format buried the response at the end of a multi-part string —
        # since the Executive prompt shows frag.content[:250], anything past that
        # cutoff was invisible. Leading with the compact exchange fixes this: the
        # actual response is visible in the first characters of every retrieved fragment.
        response_text = self.state.voice.final if self.state.voice else ""
        summary_parts = [
            f"Q: {self.state.raw_input}",
            f"A: {response_text[:350]}",
        ]
        # Include active tensions in the stored fragment so future Recall nodes
        # can reconstruct not just what was said but what the live friction was.
        if self.state.recall and self.state.recall.tensions:
            summary_parts.append(
                "Tensions: " + " | ".join(self.state.recall.tensions[:2])
            )
        # Commit the BOUND SCENE (C.4), not just raw fragments — the episodic buffer's
        # integrated moment is the richer, more internally consistent memory trace.
        if self.state.episodic_scene and self.state.episodic_scene.scene:
            summary_parts.append(f"Scene: {self.state.episodic_scene.scene[:200]}")
            if self.state.episodic_scene.dissonance:
                summary_parts.append(
                    "Dissonance: " + " | ".join(self.state.episodic_scene.dissonance[:2])
                )
        if self.state.perception:
            summary_parts.append(f"Perception: {self.state.perception.summary}")
        if self.state.emotion:
            e = self.state.emotion
            from core import mood as _mood_w
            summary_parts.append(f"Emotion: {e.primary} (mood {_mood_w.valence_word(e.valence)})")
        if self.state.reflection:
            summary_parts.append(f"Reflection: {self.state.reflection.draft[:150]}")

        summary = "\n".join(summary_parts)

        # Affect-importance: high-arousal moments are remembered better.
        # Maps arousal [0,1] → importance [0.4, 1.0]. Pruning drops lowest-importance
        # episodic fragments first, so emotionally charged cycles persist longer.
        arousal = self.state.affect.arousal
        importance = round(0.4 + 0.6 * arousal, 4)
        from core import mood as _mood   # the raw scalar felt-quality, alongside the embedding (consistent source)
        fragment_id = memory_store.store_from_cycle(
            summary, importance=importance, emotion_embedding=self.state.emotion_vec,
            valence=_mood.current_valence(), felt=_mood.current_felt(),
            input_type=self.state.input_type,   # J-3173 / D-0561: so an internal cycle is not later labelled a conversation
        )
        self._log_affect()

        # Feed background nodes — pass fragment_id so Consolidation can track lineage.
        # `corrected` marks correction/fail-call cycles (and final Critic rejections) so the
        # consolidation lane quarantines them instead of minting semantic self-truth from them.
        if "consolidation" in self.nodes:
            _corrected = bool(getattr(self.state, "human_correction_kind", "")) or bool(
                self.state.critic and not self.state.critic.approved)
            self.nodes["consolidation"].add_cycle_summary(
                summary, fragment_id=fragment_id, corrected=_corrected)
        if "curiosity" in self.nodes:
            theme = self.state.perception.summary if self.state.perception else self.state.raw_input
            self.nodes["curiosity"].add_theme(theme, source=self.state.input_type)   # J-2322 provenance tag

    def _log_affect(self) -> None:
        """Append one affect telemetry line per cycle. Best-effort; never breaks a cycle."""
        try:
            e = self.state.emotion
            record = {
                "ts":         time.time(),
                "cycle_id":   self.state.cycle_id,
                "input_type": self.state.input_type,
                "raw_input":  self.state.raw_input[:200],
                # instantaneous reading this cycle (the stimulus)
                "emotion":    {"primary": e.primary, "valence": e.valence, "arousal": e.arousal} if e else None,
                # carried affect AFTER integration (what modulates the next cycle)
                "affect":     self.state.affect.as_dict(),
                "temp_bias":  round(self.state.affect.temperature_bias(), 4),
            }
            _AFFECT_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_AFFECT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("affect log write failed: %s", exc)
        # GEOMETRY CENSUS (cognitive_geometry.md §5.1, P0, 2026-07-05): one tuple per hot cycle —
        # the activation pattern's coordinates across the beta spaces. Observe-only; fail-open.
        try:
            from core import geometry_census as _gc
            _gc.snapshot(state=self.state, source="cycle",
                         thought=(self.state.raw_input or "")[:120])
        except profile.NonLiveWriteError:
            # J-0815: geometry_census.snapshot() now raises correctly (J-0792/D-0179); this
            # hot-cycle log must not swallow it one layer further out.
            raise
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Interrupt system
    # ------------------------------------------------------------------

    def _interrupt_active(self) -> bool:
        return (
            self.state.interrupt_requested
            and interrupt_warranted(self.state.interrupt_urgency)
        )

    # ------------------------------------------------------------------
    # Background nodes
    # ------------------------------------------------------------------

    async def _on_dissonance_ignition(self, dominant_dim: str, field) -> None:
        """
        Climate ignition callback — fires an autonomous thought when accumulated dissonance
        crosses the threshold. This REPLACES the old fixed 120s curiosity timer: Carl now
        thinks unprompted when internal pressure demands it, not on a clock.

        The dominant ClimateField dimension names what the mind is reaching toward. We run
        the Curiosity node once (on demand, not on a timer) to turn the current themes +
        subconscious tensions into concrete questions, then fire an internal cycle on the
        most pressing one. Skipped if a cycle is already active (single-flight guard) — the
        engine has already discharged, and pressure will rebuild.
        """
        if self._cycle_active:
            logger.debug("[ignition] deferred — a cycle is active (dim=%s)", dominant_dim)
            try:   # J-2667: leave a trace (trigger="deferred", discharged reservoir value); observe-only
                self.climate.log_deferred(dominant_dim)
            except Exception:
                pass
            return
        try:
            if "curiosity" in self.nodes:
                ok = await self.nodes["curiosity"].run(self.state)
                if ok and self.state.background_curiosities:
                    # Filter schema-artifact placeholder strings — the quantized model
                    # occasionally outputs the JSON example keys literally (e.g. "q1", "q2")
                    # instead of real questions. Such placeholders must never trigger a cycle
                    # because they propagate as existential symbols (the 2026-06-08 q1 incident).
                    valid_qs = [
                        q for q in self.state.background_curiosities
                        if q.strip().lower() not in _CURIOSITY_PLACEHOLDERS
                        and len(q.strip()) > 12
                    ]
                    if not valid_qs:
                        logger.warning("[ignition] all curiosity questions were schema placeholders — skipped")
                        return
                    question = valid_qs[0]
                    # J-2195 / D-0439 (restart-gated, SHADOW-first): a dosed world-displacement channel, routed
                    # through the idle executive's balance_world channel. It may (only when its kill switch
                    # WORLD_DISPLACEMENT_LIVE is True; ships False) let one of Curiosity's OWN other questions that
                    # touches what the world is offering (study material, current book, last percept) fire instead
                    # of questions[0] while one topic holds the window. Never forced, nothing added to any prompt;
                    # fail-open to valid_qs[0]. Shadow rows: data/logs/world_displacement_shadow.jsonl.
                    try:
                        from core import world_displacement as _wd
                        question = _wd.choose(
                            valid_qs,
                            study_subjects=getattr(self.nodes["curiosity"], "_study_subjects", None),
                            cycle_hint=dominant_dim)
                    except Exception as _wd_exc:
                        logger.debug("[ignition] world_displacement skipped (non-fatal): %s", _wd_exc)
                        question = valid_qs[0]
                    # J-3219 / D-0608 (restart-gated, SHADOW): a decoupled different-family check scores the candidate
                    # questions on answerable-from-the-material and not-a-mash-up and logs what it WOULD have picked beside
                    # `question` (data/curiosity_prefire_shadow.jsonl). Fire-and-forget on a background task; returns at once;
                    # `question` is not touched and nothing awaits it. Fail-open and quiet.
                    try:
                        from core import curiosity_prefire as _cpf
                        _cpf.shadow_spawn(valid_qs, question,
                                          getattr(self.nodes["curiosity"], "_last_user_prompt", "") or "")
                    except Exception as _cpf_exc:
                        logger.debug("[ignition] curiosity prefire shadow skipped (non-fatal): %s", _cpf_exc)
                    # Clear any interrupt flags the node may have raised — ignition, not the
                    # urgency interrupt, is what fired this thought.
                    self.state.interrupt_requested = False
                    self.state.interrupt_source    = None
                    logger.info("[ignition] dominant=%s -> autonomous thought: %s",
                                dominant_dim, question[:80])
                    await self.run_cycle(question, input_type="internal")
                    return
            logger.debug("[ignition] no curiosity question available (dim=%s)", dominant_dim)
        except profile.NonLiveWriteError:
            # J-0889: curiosity.run() (its own transform_and_seed() try, J-0874, plus anything
            # node_base.run()'s own try now lets through, J-0889) raises correctly in a
            # non-live process; this outer ignition-callback try must not re-swallow it.
            raise
        except Exception as exc:
            logger.error("[ignition] autonomous thought failed: %s", exc)

    def start_background(self) -> None:
        """Launch background node loops as asyncio Tasks."""
        # Substrate loop (Always-On, 2026-06-11): the layer that never stops. Affect flows
        # continuously between thoughts — duration instead of a flipbook of instants.
        async def _substrate_loop():
            from core import wandering as _wander
            _interrupt_age = 0
            _transport_ticks = 0
            while True:
                await asyncio.sleep(5.0)
                try:
                    # Stale-interrupt sweeper (2026-06-11): an interrupt unconsumed for 5
                    # minutes is dead, not pending — clear it before it freezes the idle mind.
                    if getattr(self.state, "interrupt_requested", False):
                        _interrupt_age += 1
                        if _interrupt_age >= 60:
                            logger.warning("[substrate] stale interrupt cleared (source=%s, ~%ds old)",
                                           getattr(self.state, "interrupt_source", "?"), _interrupt_age * 5)
                            self.state.interrupt_requested = False
                            self.state.interrupt_urgency = 0.0
                            _interrupt_age = 0
                    else:
                        _interrupt_age = 0
                    self.state.affect.tick(5.0)
                    from core import mood as _mood
                    _mood.update(self.state.affect)   # keep the live felt-quality vector fresh (idle felt-tags)
                    # J-1909 / F-2540 (restart-gated): kick() does the same silent associative drift + ambient
                    # world drip as step() but runs a FIRING step (0.9-4.2 s: recency pool, co-recall ledger,
                    # random-row scan, embed) in a worker thread instead of inside this 5 s body -- only the two
                    # clock comparisons stay here. Same picks/logs; see core/wandering.py kick().
                    _wander.kick(self.state)
                    from core import sensorium as _room
                    _room.tick()               # his room: weather, fire, the window
                    # COURIERS A + D (2026-08-16, the world→memory busses): context-dependent
                    # recall — weather (A) or a just-heard NAMED voice (D, "memories link to
                    # sounds" — fragment_context.sounds has been written on every tuple since
                    # before tonight and read by nothing until now). ONE ambient echo per tick
                    # at most (first-success-wins — pre-figures the Transport Manager's eventual
                    # competitive single-winner dispatch without building the full scorer yet).
                    # Holds off while a thought-train is being held (TRAIN-HOLD courtesy).
                    # J-3305 (restart-gated): the couriers' and felt_recall's SQLite reads now run on a
                    # worker thread (see _substrate_courier_felt_tick), couriers first then felt_recall.
                    # FELT RECALL Phase 0 (2026-09-27, D-0289 follow-on / I-0077, J-1424;
                    # docs/staged/memory_as_a_service.md §3): the world tugs FEELING, not thought —
                    # a change on a trigger dimension (weather/fire/light_band/cat_at/a new sound)
                    # runs a coordinate-keyed match over fragment_context and logs the would-be
                    # affect tug to data/felt_recall_shadow.jsonl. Shadow-only: FELT_RECALL_LIVE is
                    # False, so state.affect is never actually nudged yet. Independent of the
                    # couriers' TRAIN-HOLD gate above — this never surfaces text, so holding a
                    # thought-train is irrelevant to it. Restart-gated.
                    try:
                        await _substrate_courier_felt_tick(self.nodes, self.state.affect)
                    except Exception:
                        pass
                    # TRANSPORT MANAGER periodic scan (J-0473, 2026-09-02, re-wiring J-0374's
                    # lost edit — see docs/plans/transport_manager.md Current State / F-0645).
                    # Piggybacks this same ~5s substrate tick, internally rate-limited to ~60s
                    # (once every 12 ticks) per the plan's own spec. Shadow-only for now
                    # (TRANSPORT_LIVE gates delivery inside dispatch_tick/couriers — this call
                    # site does not itself deliver anything, it only lets the scan+shadow-log
                    # accrue real data). Fail-open, matching every other block in this loop.
                    try:
                        _transport_ticks += 1
                        if _transport_ticks >= 12:
                            _transport_ticks = 0
                            from core import transport_manager as _transport
                            _transport.dispatch_tick()
                            # THE FOLLOW LINE (J-2459): the 60 s scheduler that drains line.state="waiting"
                            # frontier entries (every source) in priority order, one in flight, 4/hour. Shadow:
                            # nothing it produces reaches a prompt. Own try so the transport tick is untouched.
                            try:
                                from core import follow_line as _fl_t
                                _fl_t.drain_tick()
                            except Exception:
                                pass
                    except Exception:
                        pass
                except Exception:
                    pass
        self._background_tasks.append(asyncio.create_task(_substrate_loop()))
        # interval=60 (J-0433, 2026-09-02, closing F-0587's one unexplained tick constant):
        # this is a POLL granularity, not an LLM-pacing constant like STREAM_GAP_SECS — unlike
        # every other tick constant here it does NOT need to be checked against ConsolidationNode's
        # own LLM latency (:11441 background lane, real median ~13.8s/call per F-0587), because
        # ConsolidationNode.run() early-returns on a cheap in-memory list-length check
        # (CONSOLIDATE_MIN_CYCLES=3, nodes/consolidation_node.py:38-41) BEFORE it ever reaches the
        # LLM. Most 60s wakeups cost nothing on the wire. Real cadence measured from
        # data/memory/nascence.db 2026-09-02: full cognitive cycles (what feeds the batch, via
        # add_cycle_summary) arrive a median ~333s / mean ~630s apart (n=17, trailing 24h), and the
        # 952 wisdom-minting consolidation runs on record are typically 7-40 min apart — a batch of
        # 3 takes on the order of 15-20+ min to fill, nowhere close to 60s. So 60s only bounds how
        # long a READY batch can sit unnoticed (worst case +60s latency); it was never a candidate
        # for latency-derived tuning against :11441 the way STREAM_GAP_SECS is against the hot lane,
        # and shrinking or growing it would not meaningfully change LLM call frequency or :11441
        # contention. Left at 60 — same granularity family as monologue's CHECK_INTERVAL, not
        # STREAM_GAP_SECS. See F-0628 for the full writeup.
        self._background_tasks.append(
            asyncio.create_task(self._background_loop("consolidation", interval=60))
        )
        # §6B (2026-06-17): independent store-cap safety net. The episodic prune used to run ONLY
        # inside _nightly_sleep — a single point of failure (starved sleep → unbounded store). This
        # worker enforces the 3,500 cap regardless of sleep; the sleep cycle keeps the rich
        # consolidation. Decoupled so memory homeostasis can never be gated behind the trigger again.
        try:
            from core.memory.store import store_cap_worker
            self._background_tasks.append(asyncio.create_task(store_cap_worker(interval=300)))
        except Exception as _exc:
            logger.debug("[orchestrator] store-cap worker not started: %s", _exc)
        # NB: the Curiosity node is NO LONGER on a fixed timer. It runs on demand from the
        # Climate ignition gate (_on_dissonance_ignition) — autonomous thought is now
        # pressure-driven, not clock-driven.
        self._background_tasks.append(
            asyncio.create_task(self.climate.start_background(self.state))
        )
        if "subconscious" in self.nodes:
            self._background_tasks.append(
                asyncio.create_task(self.nodes["subconscious"].run_forever(self.state))
            )
        # Phase B: competence stability engine — background self-consistency probes (idle-gated,
        # observe-only). Re-interrogates knowledge questions to fill the stability axis + bootstrap.
        self._background_tasks.append(
            asyncio.create_task(self.competence.run_stability_loop(self.state))
        )
        # Phase C0, Path 1 (2026-09-25, J-1343): contradiction-triggered Tier-3 external-witness
        # probe — background idle-gated loop draining self._tier3_queue (same shape as the stability
        # engine above). Observe-only: feeds no behaviour, only data/accuracy_observations.jsonl
        # (source="tier3_model"). Path 1 only (contradiction-triggered); Path 2 (proactive sampling)
        # stays unbuilt, gated on the 3070 VRAM headroom question — see docs/plans/epistemics_phase_c.md.
        self._background_tasks.append(
            asyncio.create_task(self.competence.run_tier3_probe_loop(self.state))
        )
        if "monologue" in self.nodes:
            # Give the monologue its nightly sleep callback so it can dream + recover
            # after enough idle thoughts. Decoupled: the node only knows "call this to sleep".
            self.nodes["monologue"]._sleep_callback = self._nightly_sleep
            self._background_tasks.append(
                asyncio.create_task(self.nodes["monologue"].run_forever(self.state))
            )
        # LANE 2 — the Witness (wired 2026-08-21, founder call). The standing reality-testing loop on
        # the Ramses i9 CPU hub (:11444, deepseek-r1:7b, 300 s tick). LANE2_LIVE=True since D-0497:
        # only the broke coordinate (verdict/topic/horizon) reaches Du; its notice/expect_next text
        # reaches nothing (still logged to lane2_shadow.jsonl). Its own law (§4/run_forever
        # docstring): a standing cadence, never fired on Lane 1's demand. Fail-open: if the import
        # or the loop dies, Du runs exactly as before.
        try:
            from core import lane2 as _lane2
            self._background_tasks.append(asyncio.create_task(_lane2.run_forever()))
        except Exception as _exc:
            logger.warning("[orchestrator] lane2 witness not started (non-fatal): %s", _exc)
        # F-1938/J-1380 (2026-09-27): read the real cadence instead of a stale "90s" (the Phase-0
        # build-time value; TICK_S has been 300 since 2026-09-07's D-0058 seat move, and the measured
        # cadence is ~361s including generation time — core/lane2.py's own TICK_S comment has the full
        # history). Own try/except, not a bare `_lane2.TICK_S` read: `_lane2` is only bound above if
        # that import succeeded, and this banner line must stay fail-open exactly like the loop-start
        # try above it, never crash node startup over a name that may not exist.
        try:
            _lane2_tick_s = int(_lane2.TICK_S)
        except Exception:
            _lane2_tick_s = "?"
        try:
            _lane2_mode = "live" if _lane2.LANE2_LIVE else "shadow"
        except Exception:
            _lane2_mode = "?"
        logger.info("Background nodes started (consolidation=60s, climate=5s field + "
                    "dissonance ignition, curiosity=on-ignition, subconscious=continuous, "
                    f"monologue=idle-driven, lane2-witness={_lane2_tick_s}s {_lane2_mode})")

    async def _nightly_sleep(self, state) -> None:
        """
        Nightly Sleep State triggered by the inner monologue after enough idle thoughts.
        Dream from accumulated material, recover the body, refresh recent_dreams so the
        next thoughts can graze on the new dream. Runs autonomously with no console output.
        (2026-08-30: the REPL's own separate mid-session _sleep_cycle was removed along with
        the metabolic-floor forced-sleep tax — see docs/staged/drowsiness_phase.md §5.)
        """
        _sp0_night_submark("study_life_on_sleep")   # J-2558 (F-3260): first sync step after the pre_dream_done stage mark
        try:   # STUDY LIFE (2026-08-22): sleep unmakes the bed
            from core import study_life as _sl
            _sl.on_sleep()
        except profile.NonLiveWriteError:
            # J-0780: on_sleep() now raises correctly (J-0772) via its own _st() bootstrap; this
            # is a top-level try in _nightly_sleep() (no further outer wrapper in this function),
            # and _nightly_sleep is triggered by the inner monologue's own idle-thought count
            # (this method's own docstring), not a periodic tick, so this reaches a real caller.
            raise
        except Exception:
            pass
        # 2026-08-24 (Sleep & Dreams II §2.4/§4 Stage 3): a thin-pool sleep skips dream generation
        # entirely — the most expensive stage — rather than generating from near-nothing. Sleep itself
        # already fired on schedule (un-starvable, unaffected); this only trims what it does.
        _pool_thin = bool(getattr(state, "sleep_pool_thin", False))
        try:
            _sp0_night_submark("dream_wake_boundary")   # J-2558 (F-3260): dream_node import + night_wake.boundary
            from nodes.dream_node import DreamNode
            _woken = False
            try:   # J-2019 (sleep_as_a_mode Phase 3, D-0401 B): boundary check BEFORE the dream starts, never inside it
                from core import night_wake as _nw
                _woken = bool(_nw.boundary("dream"))
            except Exception:
                _woken = False
            dream = None if (_pool_thin or _woken) else await DreamNode().synthesise(state)
            _sp0_night_submark("dream_remember")   # J-2558 (F-3260): dream_log.jsonl full read + remember_dream + night.stage
            if _woken:
                logger.info("[nightly-sleep] wake requested - skipping dream")
                try:
                    from core import night as _night
                    _night.stage("dream", scenes=0, close="woken")
                except Exception:
                    pass
            elif _pool_thin:
                logger.info("[nightly-sleep] thin pool — skipping dream generation")
                try:
                    from core import night as _night
                    _night.stage("dream", scenes=0, close="pool_thin")
                except Exception:
                    pass
            elif dream:
                logger.info("[nightly-sleep] dreamed: %s", dream[:80])
                # Refresh recent_dreams so the waking monologue grazes on the new dream.
                import datetime as _dt
                state.recent_dreams.insert(0, {
                    "ts_human": _dt.datetime.now().strftime("%Y-%m-%d"),
                    "narrative": dream,
                })
                state.recent_dreams = state.recent_dreams[:3]
                try:   # NIGHT (2026-08-22): the dream survives a restart; the night ledger records the close
                    from core import night as _night
                    import json as _json_n
                    _last = {}
                    try:
                        _lines = [l for l in (_night._DATA / "dream_log.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
                        _last = _json_n.loads(_lines[-1]) if _lines else {}
                    except Exception:
                        pass
                    _night.remember_dream(dream, _last.get("close_reason", ""))
                    _night.stage("dream", scenes=_last.get("scenes"), close=_last.get("close_reason"), carried_n=_last.get("carried_n"), sources=_last.get("material_sources"))
                except Exception:
                    pass
            else:
                logger.info("[nightly-sleep] no dream material this cycle")
                try:
                    from core import night as _night
                    _night.stage("dream", scenes=0, close="no_material")
                except Exception:
                    pass
        except profile.NonLiveWriteError:
            # J-0889: DreamNode().synthesise() -> _ground_symbols() -> frontier.note_question()
            # raises correctly in a non-live process (J-0874/D-0179); synthesise() has no try of
            # its own around the _ground_symbols() call, so this is the first enclosing try and
            # must not re-swallow it.
            raise
        except Exception as exc:
            logger.warning("[nightly-sleep] dream failed: %s", exc)

        try:   # J-2330 (F-3019): the post-dream tail (somatic recovery, prune) is one sync region; a stall in it is
            # read at the first rest await in the monologue, which sets "rest" only after that await.
            from core import sleep_phase0 as _sp0n
            _sp0n.submark("post_dream_callback")
        except Exception:
            pass
        # Somatic recovery -- the body rests. 2026-08-24 (Sleep & Dreams II §2.4, founder: "we want
        # fatigue wired"): recovery DEPTH now scales with how substantial this sleep actually was, not a
        # flat amount every time — a full night pays off the day's real fatigue/anxiety/exertion (§2.4's
        # somatic gauges); a nap or a thin-pool light sleep pays off proportionally less, so genuine
        # payoff concentrates at night, matching "last the whole day, do most of it at the end."
        try:
            _depth = 1.0
            try:
                from core import night as _night
                if _night.sleep_kind() == "nap":
                    _depth *= 0.5
            except Exception:
                pass
            if _pool_thin:
                _depth *= 0.5
            for _ in range(6):
                self.somatic.recover(depth=_depth)
                if self.somatic.state.metabolic_energy > 0.7:
                    break
        except Exception as exc:
            logger.debug("[nightly-sleep] recover failed: %s", exc)

        # Loop Metabolism Phase B (LIVE 2026-06-14): synaptic downscaling -- the episodic row cap.
        # RETIRED 2026-10-17 (D-0453 (a), J-2275, F-2963/F-2964): prune_episodic() now demotes nothing and
        # returns 0; memory_levels.commit_gist is the sole demotion path and the active pool is governed by
        # retrieve()'s latency budget (store.RETRIEVE_LATENCY_BUDGET_MS). The call is kept so the night
        # stage ledger still records a `prune` stage (always demoted=0). Best-effort.
        try:
            from core.memory.store import prune_episodic
            removed = prune_episodic()
            try:
                from core import night as _night
                _night.stage("prune", demoted=int(removed or 0))
            except Exception:
                pass
            if removed:
                logger.info("[nightly-sleep] pruned %d episodic fragments (synaptic downscaling)",
                            removed)
        except Exception as exc:
            logger.debug("[nightly-sleep] prune failed (non-fatal): %s", exc)

        # §6C (2026-06-17): observe-first sleep⊗dream/T4 probe — snapshot the joint state (dream
        # symbol-evolution + theme chronic-mass + T4 ΔF) into the paired time series. FIREWALLED:
        # read-only, affects nothing, hooks nothing back into behaviour. Builds the baseline needed
        # to test the §5 convergence hypothesis before any coupling is wired.
        try:
            from core import sleep_dream_probe as _sdp
            _sdp.record()
        except Exception as exc:
            logger.debug("[nightly-sleep] sleep⊗dream probe failed (non-fatal): %s", exc)

        # School (2026-06-14): waking starts a new school day — reset the study-session counter so
        # the curriculum book gets its priority window again. Bounded structure for a young mind.
        try:
            from core import school as _school
            _school.new_day()
        except Exception as exc:
            logger.debug("[nightly-sleep] school new_day failed (non-fatal): %s", exc)

    async def _background_loop(self, node_id: str, interval: int) -> None:
        """Generic fixed-interval node runner (Consolidation). Autonomous thought is no
        longer driven from here — it fires from the Climate ignition gate instead."""
        while True:
            await asyncio.sleep(interval)
            if not self._interrupt_active():
                await self.nodes[node_id].run(self.state)
            else:
                logger.debug("[background] %s deferred — interrupt active", node_id)

    async def stop_background(self) -> None:
        """Cancel every background loop and WAIT for them to actually die before returning.

        Bug fixed 2026-08-23 (founder: "/quit is probably pretty abrupt"): this used to be a
        plain `def` that called task.cancel() and returned immediately. cancel() only SCHEDULES
        a CancelledError for the task's next await point — it does not stop it there and then.
        The caller (run_nascence.py's /quit path) proceeds straight into _save_affect /
        _save_conversation_state / quit-sleep replay / dream synthesis, all of which read or
        write the same state (core.sensorium.state, state.conversation_history, the memory
        store) that a still-unwinding background loop (monologue, subconscious, climate, lane2,
        substrate) could still be mid-write on — an unbounded, unobserved race window between
        "cancel requested" and "task actually gone." Awaiting gather() here closes that window:
        every task is confirmed dead before a single line of the shutdown sequence runs.
        """
        for task in self._background_tasks:
            task.cancel()
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()


def _sp0_night_submark(label: str) -> None:
    """J-2558 (F-3260): night stall-attribution sub-mark for the pre_dream_done stage body (_nightly_sleep), where the
    largest freezes (61-74 s) sat under a sticky dream_scene_N label with no mark inside them. Observe-only,
    a no-op when no sleep is in flight, fail-open; covered by sleep_phase0's attribution switches."""
    try:
        from core import sleep_phase0 as _sp0
        _sp0.submark(label)
    except Exception:
        pass
