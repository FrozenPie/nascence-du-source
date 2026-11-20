"""
core/epistemic_affordance_advisor.py — Epistemic Affordance Advisor (passive Stage-A instrument)

STATUS (2026-10-04, J-1776; D-0326): this module is the PASSIVE Stage-A instrument ONLY, and nothing it ranks is ever
shown to Du. Hint delivery (Stage B / Phase 2 "Live Advisory") is permanently CLOSED and was never wired: the 2026-08-14
founder law ("no hints, ever" -- Stage B REMOVED, not gated; its text sits in core/orchestrator.py's call block for this
module) stands exactly as written, re-confirmed by Travis in D-0326 (2026-10-03). Earlier versions of this docstring
called the module "Live Advisory Coupling"; that framing is withdrawn. epistemic_advisory_hint() below is kept only as
the design record of what the law shut off: it has ZERO call sites and none may be added. What the module does is rank
the real Hand families at Du's location by expected epistemic yield and record, via record_epistemic_episode(), to
data/investigative_action_log.jsonl both the passive shadow ranking core/orchestrator.py logs (selection_source
"advisor_shadow_only") and the real closed episodes the wandering loop closes (close_real_episode(), selection_source
"du"). The Phase-1 exit gate is the Epistemic Independence metric (plan Principle D / Invariant 9), read by
scripts/epistemic_independence_readout.py, which calls only rank_epistemic_affordances().
Plan: docs/plans/investigative_action_loop_plan.md.

Wraps core/affordances.py non-destructively. When an active uncertainty or physical question
is detected in inner thoughts, the advisor ranks available Gibsonian affordances by their
expected epistemic yield (including 'do_nothing' / STOP), logging raw recommendations and selection agency provenance.

Generation 3B.2 Invariants (kept as the design record; plan Section 5 tags each one, mirrored here. MOOT = governed hint
delivery, which no longer exists. STANDS = still governs the Stage-A ranking and telemetry that DO run):
1. Zero Pollution of affordances.within_reach_text() (Environment remains 100% clean).
   [MOOT: subsumed by the stronger law, no advisor output reaches Du by any route]
2. Volitional Non-Directive Advice ("If you wish to distinguish X from Y, scraping would reveal more").
   [MOOT: no hint is ever rendered]
3. 5-State Hypothesis Adoption Provenance (UNSEEN, PRESENTED, CONSIDERED, ADOPTED, REJECTED).
   [MOOT: nothing is ever presented, so only UNSEEN occurs for real; rows written before J-1777 may still say PRESENTED,
   read selection_source advisor_shadow_only / system_suggestion as "never shown"]
4. Hypothesis-Conditioned IG Computation (computed strictly from P(Obs|H) via domain rules; BLIND TO LAYER 1). [STANDS]
5. Layer 1 Firewall: Advisor has ZERO access to object causal_state. [STANDS]
6. Firewalled Metrics: Internal Cognition Metrics (IG, Delta H, C) vs Researcher Audit (Q_rev, Layer 1 distance). [STANDS]
7. Epistemic Compression: Shannon Entropy Reduction (Delta H) + Candidate Contraction (C). [STANDS]
8. Stage A Baseline Telemetry: Shadow Mode baseline before Stage B advisory hints.
   [MOOT: Stage B is never enabled; the Stage-A baseline is simply the standing telemetry]
9. Agency Preservation: Non-optimization of compliance.
   [STANDS: the independence metrics are experimental variables, not compliance targets]
10. First-Class Stopping State (UNDETERMINED / do_nothing when max IG < 0.30). [STANDS]
11. No Creation of Uncertainty Invariant: SILENT when curiosity is casual or unstructured. [STANDS]
"""

import os
import sys
import json
import math
import time
import sqlite3
from typing import Literal, Optional, List, Dict
from dataclasses import dataclass, asdict
from pathlib import Path

# Ensure Nascence root is in sys.path.
# J-1824 / F-2458 (2026-10-06): this was the literal absolute Path("c:/Nascence"), the only module-level
# data path in core/ not anchored to __file__. Two real consequences the J-1718 dynamic write audit hit:
# (1) LOG_JSONL_PATH below pointed at the REAL C:\Nascence\data even when this copy of the module was
# imported from a git worktree (F-2458 row 9 -- the one write that crossed from a worktree into the
# live tree), and core.profile.activate_profile()'s generic rebase could not see it from such a tree
# (it only re-points constants under its own _DATA); (2) the sys.path insert below pushed the real
# tree ahead of the worktree, so any package first imported after this one resolved to the wrong
# tree. Anchoring to __file__ (resolve(): the same C:\Nascence for the live boot -- byte-identical
# paths and the same directory on sys.path) fixes both and lets activate_profile() rebase
# LOG_JSONL_PATH like every other per-agent constant.
NASCE_ROOT = Path(__file__).resolve().parent.parent
if str(NASCE_ROOT) not in sys.path:
    sys.path.insert(0, str(NASCE_ROOT))

from core.memory.store import _connect
from core.affordances import within_reach_text

LOG_JSONL_PATH = NASCE_ROOT / "data" / "investigative_action_log.jsonl"
INFORMATION_GAIN_THRESHOLD = 0.30  # Below this, recommend stopping (UNDETERMINED)


@dataclass
class InvestigativeEpisode:
    episode_id: str
    timestamp: float
    location: str
    question: str
    competing_hypotheses: List[str]
    discriminative_prediction: str
    selected_affordance: str
    raw_observation: str
    prediction_observed_comparison: str
    evidence_outcome: Literal["CONFIRMED", "REFUTED", "INCONCLUSIVE", "UNTESTED", "UNDETERMINED"]
    confidence_explanation: str
    model_revision: str
    agency_mode: Literal["spontaneous", "investigative", "suggested", "follow_up"]
    # "advisor_shadow_only" added 2026-08-24 (J-0180): the pre-existing "system_suggestion"
    # literal at core/orchestrator.py's Stage-A call site was factually wrong (F-0129 —
    # nothing is ever suggested to Du, per the 2026-08-14 founder decision that Stage B
    # hints are REMOVED, not gated). Real closed episodes from the wandering loop always
    # use "du" (F-0129/F-0180: Du's own action, independently taken).
    selection_source: Literal["du", "system_suggestion", "system_follow_up", "advisor_shadow_only"]
    question_source: Literal["du", "system"] = "du"
    hypothesis_source: Literal["du", "system_candidate_generation"] = "du"
    # 2026-10-04 (J-1777 / F-2395): the default was "PRESENTED", so every passive shadow-ranking row
    # (core/orchestrator.py's Stage-A call site, selection_source "advisor_shadow_only", which never passes
    # this field) claimed a hint had been shown to Du -- 1,316 of 2,669 live rows -- although the
    # 2026-08-14 no-hints law means nothing is EVER presented. "UNSEEN" is the truthful default (the same
    # word close_real_episode() below already writes explicitly). Rows written before this change keep
    # "PRESENTED": the JSONL is an immutable raw record, so read selection_source in
    # {advisor_shadow_only, system_suggestion} as "never shown".
    adoption_state: Literal["UNSEEN", "PRESENTED", "CONSIDERED", "ADOPTED", "REJECTED"] = "UNSEEN"
    entropy_reduction: float = 0.0
    hypothesis_contraction: float = 0.0
    stage: Literal["STAGE_A_SHADOW", "STAGE_B_ADVISORY", "STAGE_C_LONGITUDINAL"] = "STAGE_A_SHADOW"
    next_question: Optional[str] = None


def init_db_table() -> None:
    """Initialize the SQLite projection table for query analytics."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS investigative_episodes (
                episode_id TEXT PRIMARY KEY,
                timestamp REAL,
                location TEXT,
                question TEXT,
                selected_affordance TEXT,
                evidence_outcome TEXT,
                agency_mode TEXT,
                selection_source TEXT,
                model_revision TEXT,
                adoption_state TEXT,
                entropy_reduction REAL,
                hypothesis_contraction REAL,
                stage TEXT
            )
        """)
        # Auto-migrate columns if table already existed under older schema
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(investigative_episodes)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        new_cols = [
            ("adoption_state", "TEXT"),
            ("entropy_reduction", "REAL"),
            ("hypothesis_contraction", "REAL"),
            ("stage", "TEXT")
        ]
        for col_name, col_type in new_cols:
            if col_name not in existing_cols:
                try:
                    conn.execute(f"ALTER TABLE investigative_episodes ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass
        conn.commit()


def is_structured_epistemic_uncertainty(question: str, hypotheses: List[str]) -> bool:
    """
    INVARIANT 11: No Creation of Uncertainty.
    Checks whether Du has expressed an active, structured physical question or curiosity.
    Returns False for casual, aesthetic, or non-investigative thoughts.
    """
    if not question and not hypotheses:
        return False

    q_lower = question.lower()
    casual_phrases = [
        "looks beautiful", "feels good", "pleasant", "sitting by the fire",
        "nice day", "peaceful", "rest", "simply be", "quiet"
    ]
    if any(phrase in q_lower for phrase in casual_phrases) and not any(kw in q_lower for kw in ["why", "what", "how", "could", "species"]):
        return False

    # 2026-08-15 GATE FIX: the old gate passed on bare interrogatives ("what drives the tension
    # between humanity's desire…") or on hypotheses alone — so his ABSTRACT identity questions were
    # consuming investigations, each answered with the one driftwood prop (verified in the episode
    # log: identical scrape-predictions attached to philosophy). A physical investigation requires a
    # CONCRETE WORLD-NOUN ANCHOR — a thing that could actually be acted on — and the abstract-tension
    # frame is explicitly excluded. Interrogatives and hypotheses count only WITH an anchor.
    _ABSTRACT_MARKERS = [
        "tension between", "desire for", "identity", "self", "society", "societal", "humanity",
        "individuality", "authenticity", "meaning of", "sense of", "belonging", "expectation",
    ]
    _CONCRETE_ANCHORS = [
        # the investigable world: wood & trees
        "grain", "bark", "wood", "driftwood", "log", "branch", "limb", "deadfall", "timber",
        "rot", "fungus", "borer", "knot", "ring",
        # stone & shore
        "stone", "pebble", "shingle", "rock", "sand", "tide", "tideline", "wave", "shore",
        "shell", "paua", "whelk", "cuttlebone", "kelp", "weed", "glass", "float",
        "bone", "feather", "egg-case", "egg case", "purse", "crab", "gull", "gannet",
        # garden & weather
        "leaf", "leaves", "soil", "root", "stem", "herb", "rosemary", "thyme", "mint", "parsley",
        "frost", "rain", "wind", "moisture", "salt",
        # investigable properties
        "weight", "density", "hollow", "smell", "scent", "texture", "hardness", "surface",
        "species", "washed up", "worn", "bleached",
    ]
    has_anchor = any(n in q_lower for n in _CONCRETE_ANCHORS)
    is_abstract = any(m in q_lower for m in _ABSTRACT_MARKERS)
    if is_abstract and not has_anchor:
        return False
    if not has_anchor:
        return False

    investigative_keywords = [
        "why", "what kind", "what species", "how long", "could this be", "wonder if",
        "differs", "origin", "what made", "how did", "where did", "what is this",
    ]
    return any(kw in q_lower for kw in investigative_keywords) or len(hypotheses) > 0


# 2026-08-24 (J-0180 / F-0129): the candidate vocabulary below used to be five actions
# (scrape, inspect_end, pick_up, look_shore, float_test) that correspond to NO real Hand
# in core/dispatch.py's HANDS registry — even a perfectly-instrumented capture path could
# never observe most of the advisor's own top candidates actually firing, because those
# actions have no execution path in the live system (F-0129, verified). Replaced with the
# real dispatch.HANDS family vocabulary so the candidates the advisor ranks are the same
# candidates that can actually fire and produce a real raw_observation.

# Rough domain-keyword map per real Hand family, used only to bias the (shallow, documented)
# IG heuristic below — NOT a semantic model, NOT sourced from Layer 1 causal_state (Invariant 5
# firewall preserved: the advisor never sees object causal_state, only question/hypothesis text).
_FAMILY_DOMAIN_KEYWORDS: Dict[str, tuple] = {
    "fire":      ("fire", "hearth", "embers", "flame", "log", "burn", "smoke", "ash", "kindle"),
    "tea":       ("tea", "kettle", "cup", "brew"),
    "lamp":      ("lamp", "light", "dark", "wick"),
    "door":      ("door", "draft", "draught"),
    "grate":     ("grate", "ash", "cinder"),
    "clock":     ("clock", "time", "hour"),
    "clean":     ("clean", "dust", "tidy"),
    "wear":      ("wear", "coat", "clothes", "cold", "warm"),
    "note":      ("note", "leave word", "message"),
    "collect":   ("gate", "collect", "delivery", "parcel", "post"),
    "water":     ("moisture", "dry", "wilt", "water", "soil"),
    "sow":       ("seed", "sow", "plant", "germinat"),
    "harvest":   ("herb", "harvest", "ripe", "ready", "crop", "rosemary", "thyme", "mint", "parsley"),
    "weed":      ("weed", "overgrown", "bed", "soil"),
    "stake":     ("stake", "lean", "support", "wind", "flop"),
    "net":       ("net", "bird", "peck", "protect"),
    "save_seed": ("seed", "save", "dry", "viable"),
    "mow":       ("grass", "lawn", "mow", "long"),
    "tool":      ("tool", "blade", "handle"),
    "gather":    ("wood", "shore", "driftwood", "stick", "kindling", "material", "gather"),
    "beachcomb": ("shore", "tide", "tideline", "shell", "washed up", "found"),
    "shore":     ("shore", "stone", "pebble", "shingle", "rock", "sand", "wave", "tide", "salt",
                  "weathering", "erosion", "cavity"),
    "woodwork":  ("wood", "grain", "bark", "log", "branch", "timber", "carve", "species",
                  "hardwood", "density", "beech", "birch"),
    "fieldcraft": ("track", "sign", "trail", "animal", "spoor", "weather"),
}

_FAMILY_REASONS: Dict[str, str] = {
    "fire": "Tending the fire surfaces how the embers/fuel actually respond.",
    "tea": "Making tea surfaces the kettle/water state directly.",
    "lamp": "Handling the lamp surfaces its actual state, though this is rarely diagnostic.",
    "door": "Handling the door surfaces its actual state, though this is rarely diagnostic.",
    "grate": "Clearing the grate surfaces the ash/fuel condition directly.",
    "clock": "Checking the clock is rarely diagnostic of a physical hypothesis.",
    "clean": "Cleaning surfaces dust/condition but is rarely diagnostic.",
    "wear": "Changing what he wears tests comfort, not a physical hypothesis.",
    "note": "Leaving a note doesn't test anything about the physical world.",
    "collect": "Checking the gate surfaces whether anything has actually arrived.",
    "water": "Watering surfaces the soil's real moisture state.",
    "sow": "Sowing tests germination conditions directly.",
    "harvest": "Harvesting reveals ripeness, quantity, and condition directly.",
    "weed": "Weeding surfaces the bed's real soil and growth state.",
    "stake": "Staking surfaces how exposed the plant actually is.",
    "net": "Netting surfaces bird/pest pressure directly.",
    "save_seed": "Saving seed surfaces the seed's real viability/condition.",
    "mow": "Mowing surfaces the grass's real length/condition.",
    "tool": "Handling the tool surfaces its real condition.",
    "gather": "Gathering material surfaces its real texture, weight, and condition.",
    "beachcomb": "Beachcombing surfaces what the tideline actually holds.",
    "shore": "Working the shore directly tests stone/tide/weathering conditions.",
    "woodwork": "Working the wood exposes grain, density, and species-diagnostic detail.",
    "fieldcraft": "Fieldcraft reads tracks and signs directly in the terrain.",
}


def _family_reason(family: str) -> str:
    return _FAMILY_REASONS.get(family, f"Performing '{family}' produces a real observation to test against.")


def _real_candidate_families(location: str) -> List[str]:
    """
    Real Hand families available at `location`, sourced from core/dispatch.py's HANDS
    registry (the single live action registry — F-0129) instead of a hand-authored
    fictional list. 'any'-location hands are included everywhere.

    'look' and 'move' are deliberately excluded: 'look' never changes the world
    (Hand(world=False) in dispatch.py) so it never produces the kind of world-changing
    raw_observation the rest of this module is built to evaluate, and 'move' relocates
    Du rather than investigating anything at his current location. Including either would
    crowd out 'do_nothing' with actions that don't actually test a hypothesis.
    """
    try:
        from core.dispatch import HANDS
    except Exception:
        return []
    fams = []
    for h in HANDS:
        if h.family in ("look", "move"):
            continue
        if location in h.where or "any" in h.where:
            fams.append(h.family)
    return fams


def calculate_action_discriminative_value(
    action: str,
    question: str,
    competing_hypotheses: List[str]
) -> float:
    """
    Computes Expected Information Gain (0.0 to 1.0) of a real Hand family (from
    core/dispatch.py's HANDS registry) against a question/hypotheses pair.

    SIMPLE, DOCUMENTED heuristic (J-0180) — NOT a semantic model:
    tokenize question+hypotheses to lowercase, count how many of the family's domain
    keywords (_FAMILY_DOMAIN_KEYWORDS) appear in that text, and scale IG with hit count:
        0 hits  -> 0.15 (weak, generic — acting still yields *some* incidental info)
        N hits  -> min(0.90, 0.35 + 0.18 * N)
    Strictly hypothesis-conditioned (question/hypothesis TEXT only) — BLIND to object
    Layer 1 causal_state per Invariant 5.

    Known failure modes (documented, not hand-waved): a family with a longer domain-keyword
    list has more chances to score a hit (length bias); keyword matching is shallow and has
    no synonym/lemma awareness (e.g. "beech" vs "birch" both score under "woodwork" without
    actually distinguishing them); this scores DOMAIN RELEVANCE of the family to the
    question, not the true diagnostic power of any specific action within that family.
    """
    q_lower = question.lower()
    hyp_text = " ".join(competing_hypotheses).lower()
    combined = f"{q_lower} {hyp_text}"

    # Unrecoverable questions: no real action can settle these regardless of family.
    unrecoverable_keywords = ["exact days", "exact date", "precise minute", "exact storm count", "original tree height"]
    if any(kw in combined for kw in unrecoverable_keywords):
        return 0.0

    keywords = _FAMILY_DOMAIN_KEYWORDS.get(action, ())
    hits = sum(1 for kw in keywords if kw in combined)
    if hits == 0:
        return 0.15
    return round(min(0.90, 0.35 + 0.18 * hits), 2)


def rank_epistemic_affordances(
    question: str,
    hypotheses: List[str],
    location: str = "study"
) -> List[dict]:
    """
    Ranks REAL dispatch.HANDS families available at `location` by their potential
    epistemic yield (J-0180: rewritten from a fictional 5-action list — F-0129).
    If IG < INFORMATION_GAIN_THRESHOLD (0.30) or unstructured, ranks 'do_nothing' FIRST (UNDETERMINED).
    """
    if not is_structured_epistemic_uncertainty(question, hypotheses):
        return [{
            "affordance": "do_nothing",
            "expected_information_gain": 0.0,
            "reason": "Uncertainty is unstructured or casual. Silence preserved."
        }]

    families = _real_candidate_families(location)
    candidates = []
    for fam in families:
        ig = calculate_action_discriminative_value(fam, question, hypotheses)
        candidates.append({
            "affordance": fam,
            "expected_information_gain": round(ig, 2),
            "reason": _family_reason(fam)
        })

    if not candidates:
        return [{
            "affordance": "do_nothing",
            "expected_information_gain": 0.0,
            "reason": f"No real Hand family is registered for location '{location}'."
        }]

    candidates.sort(key=lambda x: x["expected_information_gain"], reverse=True)
    max_ig = candidates[0]["expected_information_gain"] if candidates else 0.0

    if max_ig < INFORMATION_GAIN_THRESHOLD:
        candidates.insert(0, {
            "affordance": "do_nothing",
            "expected_information_gain": 0.0,
            "reason": f"No available action offers sufficient information gain (max IG {max_ig} < threshold {INFORMATION_GAIN_THRESHOLD}). Outcome: UNDETERMINED. Investigation paused."
        })
    else:
        candidates.append({
            "affordance": "do_nothing",
            "expected_information_gain": 0.0,
            "reason": "Casual observation or rest is preferred."
        })

    return candidates


def epistemic_advisory_hint(question: str, hypotheses: List[str], location: str = "study") -> str:
    """
    Renders non-authoritative cognitive instrument panel hint string when active uncertainty exists
    and top action IG >= 0.30.
    Returns "" (SILENT) when unstructured or low IG.
    Leaves affordances.within_reach_text() 100% clean.
    """
    ranked = rank_epistemic_affordances(question, hypotheses, location)
    top = ranked[0] if ranked else None
    if not top or top["affordance"] == "do_nothing" or top.get("expected_information_gain", 0.0) < INFORMATION_GAIN_THRESHOLD:
        return ""

    action_name = top["affordance"].replace("_", " ")
    reason = top["reason"]
    return (
        f"\n\n[Cognitive Instrument Panel — Optional Epistemic Hint]\n"
        f"Regarding your active question ('{question}'): if you wish to distinguish these possibilities, "
        f"performing '{action_name}' ({reason}) offers high potential evidence."
    )


def calculate_internal_epistemic_metrics(
    prior_dist: Dict[str, float],
    posterior_dist: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculates internal cognition metrics (Du-facing):
    - Shannon Entropy Reduction: Delta H = H(P_prior) - H(P_posterior)
    - Hypothesis Contraction: C = 1 - (N_posterior / N_prior)
    """
    def shannon_entropy(dist: Dict[str, float]) -> float:
        total = sum(dist.values())
        if total <= 0:
            return 0.0
        h = 0.0
        for p in dist.values():
            if p > 0:
                prob = p / total
                h -= prob * math.log2(prob)
        return h

    h_prior = shannon_entropy(prior_dist)
    h_post = shannon_entropy(posterior_dist)
    delta_h = max(0.0, round(h_prior - h_post, 3))

    n_prior = len([v for v in prior_dist.values() if v > 0.05])
    n_post = len([v for v in posterior_dist.values() if v > 0.05])
    contraction = round(1.0 - (n_post / max(1, n_prior)), 3) if n_prior > 0 else 0.0

    return {
        "entropy_reduction": delta_h,
        "hypothesis_contraction": contraction,
        "h_prior": round(h_prior, 3),
        "h_posterior": round(h_post, 3),
    }


def record_epistemic_episode(episode: InvestigativeEpisode) -> None:
    """
    Writes raw episode record to immutable JSONL log and projects query index into SQLite.
    """
    init_db_table()

    LOG_JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_JSONL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(episode), ensure_ascii=False) + "\n")

    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO investigative_episodes (
                episode_id, timestamp, location, question, selected_affordance,
                evidence_outcome, agency_mode, selection_source, model_revision,
                adoption_state, entropy_reduction, hypothesis_contraction, stage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            episode.episode_id,
            episode.timestamp,
            episode.location,
            episode.question,
            episode.selected_affordance,
            episode.evidence_outcome,
            episode.agency_mode,
            episode.selection_source,
            episode.model_revision,
            episode.adoption_state,
            episode.entropy_reduction,
            episode.hypothesis_contraction,
            episode.stage
        ))
        conn.commit()


# ---------------------------------------------------------------------------
# J-0180 (2026-08-24): real episode-closing, relocated to the ONLY place a real
# selected-affordance + real raw-observation pair exists — nodes/inner_monologue_node.py's
# wandering loop, right after core/dispatch.py's dispatch() returns (F-0129, verified:
# core/orchestrator.py's run_cycle() never calls dispatch() and has no action-resolution
# step at all). Business logic lives HERE, not in inner_monologue_node.py, so the change
# to that large, founder-flagged-additive-only file stays a small, self-contained call.
# ---------------------------------------------------------------------------

_STOPWORDS = frozenset({
    "this", "that", "with", "from", "have", "were", "been", "would", "could", "should",
    "what", "when", "where", "which", "while", "about", "there", "their", "those",
    "does", "doing", "done", "being", "into", "over", "under", "again", "further",
    "then", "once", "here", "very", "just", "some", "such", "only", "same", "than",
    "will", "shall", "might", "must", "your", "you're", "them", "they", "these",
})


def _tokenize(text: str) -> set:
    import re as _re
    words = _re.findall(r"[a-z]{4,}", (text or "").lower())
    return {w for w in words if w not in _STOPWORDS}


def _keyword_overlap_outcome(hypotheses: List[str], raw_observation: str) -> "tuple[str, str]":
    """
    SIMPLE, DOCUMENTED evidence_outcome heuristic for J-0180's real episode-closing
    (written per the job's own instruction: "do not hand-wave this, write the exact
    rule and its known failure modes").

    RULE:
      hyp_words = union of tokens(>=4 lowercase letters, stopwords dropped) over
                  `hypotheses` (in practice: [intention[:300]] if Du expressed one
                  this iteration, else []).
      obs_words = same tokenization of `raw_observation` (the real Hand answer string).
      overlap   = hyp_words & obs_words
      ratio     = len(overlap) / max(1, len(hyp_words))
        - hyp_words is empty (no intention text captured)      -> INCONCLUSIVE
        - ratio >= 0.34 (roughly >=1-in-3 hypothesis words hit) -> CONFIRMED
        - ratio == 0.0 AND both word-sets non-empty             -> REFUTED
        - otherwise                                             -> INCONCLUSIVE

    KNOWN FAILURE MODES (documented, not hand-waved):
      1. Synonym/lemma blindness — "beeches" vs "beech", "grained" vs "grain" tokenize
         differently and can under-count a real semantic match.
      2. No negation handling — an observation reading "no sign of the rot he expected"
         still counts "rot" as an overlap hit; this rule cannot detect a negated match
         and will misscore it CONFIRMED rather than REFUTED.
      3. Short Hand answers (a handful of words) make the ratio noisy at low token
         counts — a single shared filler-ish word can swing the verdict.
      4. REFUTED requires a literal ZERO-overlap on two non-empty word-sets — a
         deliberately conservative bar (favors INCONCLUSIVE over a false REFUTED), so
         REFUTED will be rare by construction, not because Du's expectations are
         rarely wrong. This is a corpus-honesty choice, not a claim about Du.
      5. This is a shallow lexical heuristic, not a semantic judge, and has no access
         to Layer 1 causal_state (Invariant 5 firewall preserved) — it is not a
         substitute for a real evaluator and should be read as approximate telemetry.
    """
    hyp_words: set = set()
    for h in (hypotheses or []):
        hyp_words |= _tokenize(h)
    obs_words = _tokenize(raw_observation)

    if not hyp_words:
        return "INCONCLUSIVE", "No hypothesis/intention text was captured this iteration to compare against the observation."

    overlap = hyp_words & obs_words
    ratio = len(overlap) / max(1, len(hyp_words))
    if ratio >= 0.34:
        return "CONFIRMED", f"Observation shares {len(overlap)}/{len(hyp_words)} hypothesis keyword(s): {sorted(overlap)}."
    if ratio == 0.0 and obs_words:
        return "REFUTED", f"Observation shares zero keywords with the hypothesis/intention text (hyp={sorted(hyp_words)})."
    return "INCONCLUSIVE", f"Observation shares {len(overlap)}/{len(hyp_words)} hypothesis keyword(s) — below the CONFIRMED threshold."


def close_real_episode(
    thought: str,
    intention: str,
    location: str,
    dispatched: List[tuple],
    cycle_id: str = "",
) -> Optional[InvestigativeEpisode]:
    """
    J-0180: builds ONE real InvestigativeEpisode from the SAME wandering-loop iteration
    where a real Hand actually fired — called from nodes/inner_monologue_node.py right
    after `dispatched = dispatch.dispatch(...)` returns, with `dispatched` passed through
    unmodified (the [(family, answer), ...] list; `answer` is the REAL, un-truncated
    observation string — hands.fired() truncates to 160 chars for ITS OWN trace file, but
    that truncation is never applied to the list this function receives, so no re-fetch
    is needed).

    Returns None (skip — no episode recorded) when no world-changing hand fired this
    iteration. This is deliberate (recommended by J-0180's own briefing): recording an
    UNTESTED placeholder every non-firing iteration would just re-manufacture the same
    "UNTESTED forever" backlog F-0063/F-0120 found in the orchestrator.py shadow log.
    """
    world_fired = [(f, a) for f, a in (dispatched or []) if f not in ("look", "intention")]
    if not world_fired:
        return None
    family, raw_observation = world_fired[0]  # dispatch.py's own invariant: one world-changing hand per thought

    hypotheses = [intention[:300]] if intention else []
    structured = is_structured_epistemic_uncertainty(thought, hypotheses)
    agency_mode = "investigative" if structured else "spontaneous"

    ranked = rank_epistemic_affordances(thought, hypotheses, location)
    match = next((c for c in ranked if c.get("affordance") == family), None)
    if match:
        discriminative_prediction = str(match.get("reason", ""))[:300]
        ig_note = f"advisor-ranked IG for the family that actually fired = {match.get('expected_information_gain', 0.0)}"
    else:
        discriminative_prediction = (
            f"'{family}' fired; not among the advisor's ranked candidates for location "
            f"'{location}' (heuristic coverage gap — documented in J-0180, not silently dropped)."
        )
        ig_note = "fired family absent from advisor's location candidate list"

    outcome, comparison = _keyword_overlap_outcome(hypotheses, raw_observation)

    import uuid as _uuid
    return InvestigativeEpisode(
        episode_id=f"ep_im_{int(time.time())}_{_uuid.uuid4().hex[:6]}",
        timestamp=time.time(),
        location=location,
        question=thought[:400],
        competing_hypotheses=hypotheses,
        discriminative_prediction=discriminative_prediction,
        selected_affordance=family,
        raw_observation=(raw_observation or "")[:600],
        prediction_observed_comparison=comparison,
        evidence_outcome=outcome,
        confidence_explanation=f"real (non-shadow) episode, inner_monologue wandering loop, J-0180, cycle={cycle_id or 'unknown'}. {ig_note}.",
        model_revision=f"selected={family} outcome={outcome}",
        agency_mode=agency_mode,
        selection_source="du",
        question_source="du",
        hypothesis_source="du",
        adoption_state="UNSEEN",  # nothing was ever presented to Du (Stage B hints permanently off)
        stage="STAGE_A_SHADOW",
        next_question=None,
    )
