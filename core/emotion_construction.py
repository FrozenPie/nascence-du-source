"""
Nascence — Emotion Construction (Phase 2 shadow experiment, 2026-08-10)

Barrett-inspired deterministic emotion constructor. Produces an EmotionOutput from
grounded architectural signals (homeostasis, arousal, satisfaction, concerns) rather
than an LLM guess from percept text.

THIS IS A HYPOTHESIS UNDER TEST. The formulas mapping grounded quantities to Ekman
dimensions are implementation proposals, not established mappings. The shadow period
is where they earn legitimacy or get revised.

Dimension classification:
  GROUNDED    — has an identified physiological/architectural source
  CONSTRUCTED — derived from grounded quantities via the hypothesis formula
  VESTIGIAL   — retained for interface compatibility, not strongly grounded

  valence  : GROUNDED    (homeostasis tonic: 1 - 2*drive)
  arousal  : GROUNDED    (arousal.level() — global activation)
  joy      : CONSTRUCTED (positive valence × satisfaction liking)
  fear     : CONSTRUCTED (negative valence × arousal × concern threat-relevance)
  anger    : CONSTRUCTED (negative valence × (1-arousal) × satisfaction gap)
  trust    : CONSTRUCTED (relational warmth from satisfaction)
  surprise : CONSTRUCTED (interoceptive prediction error from homeostasis)
  disgust  : VESTIGIAL   (no grounded source; 0.0 for compatibility)

NOTE: disgust=0 means "our architecture has no grounded source from which to
construct disgust", NOT "Du has demonstrated no disgust."

Ships OBSERVE-ONLY. Called by the orchestrator alongside the live LLM emotion node;
output is logged and discarded. Nothing changes for Du until EMOTION_CONSTRUCTED
is flipped — and that requires evidence from three structured experiments.
"""
from __future__ import annotations

import json
import logging
import time
import threading
from pathlib import Path

logger = logging.getLogger("nascence.emotion_construction")

_DATA = Path(__file__).parent.parent / "data"
_SHADOW_LOG = _DATA / "emotion_construction_shadow.jsonl"
# Experiment C, part 2 (affective retrieval) writes here — a SIBLING file, not the main shadow log,
# because it needs an off-thread DB read (mirrors how inner_monologue_node.py fires
# euclidean_recall.shadow_log() off-thread) and must never delay or corrupt the hot-path row above.
# Correlate the two files on `cycle_id`.
_AR_SHADOW_LOG = _DATA / "emotion_construction_affective_retrieval_shadow.jsonl"
# Fixed ranking weights for the Experiment-C comparison: affect_match weighted heavily and identically
# for both sides, so any difference in the resulting top-k is attributable to the mood VECTOR
# (llm vs constructed), not to the weighting. FEATURES order (euclidean_recall.py):
# semantic_sim, recency, affect_match, salience, abstraction, provenance.
_AR_WEIGHTS = [1.0, 0.5, 1.5, 0.4, 0.2, 0.2]
_AR_NEED_PT = [1.0, 0.5, 1.0, 1.0, 0.5, 0.8]  # mirrors euclidean_recall.shadow_log's own need point


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    """Plain Pearson r, no external deps (matches scratchpad/analyze_J-1298.py's own implementation, so
    a fresh status() read and that one-off script's numbers are directly comparable). None below n=3 or
    on a degenerate (zero-variance) side, same fail-open contract as the rest of this module's readers."""
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / (sxx * syy) ** 0.5


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _clip_valence(x: float) -> float:
    return max(-1.0, min(1.0, float(x)))


def _threat_weight(concerns: list[dict]) -> float:
    """How much the active concerns carry a threat/obstacle flavour.
    Holds (commitments at risk) and pursuits (unresolved questions) weight higher."""
    if not concerns:
        return 0.3  # mild ambient unease without active concerns
    weights = {"hold": 0.8, "pursuit": 0.5, "project": 0.3}
    total = sum(weights.get(c.get("kind", ""), 0.3) for c in concerns)
    return _clip01(total / max(1, len(concerns)))


def _frustration_weight(sat: dict) -> float:
    """How much wanting exceeds liking (Berridge gap = blocked pursuit)."""
    gaps = sat.get("gap", {})
    if not gaps:
        return 0.0
    pos_gaps = [max(0.0, float(v)) for v in gaps.values()]
    return _clip01(sum(pos_gaps) / max(1, len(pos_gaps)))


def _relational_trust(sat: dict) -> float:
    """Trust/warmth from the relational liking dimension."""
    liking = sat.get("liking", {})
    return _clip01(float(liking.get("relational", 0.0)))


def _label_from_quadrant(v: float, a: float, dominant: str | None) -> str:
    """Circumplex-to-label map (HYPOTHESIS — to be tested, not asserted).
    Conditioned on the specific drive deficit that is pulling Du."""
    if abs(v) < 0.08:
        # near-zero valence — the specific deficit names the feeling
        return {
            "novelty": "curiosity",
            "coherence": "uncertainty",
            "relational_warmth": "longing",
            "commitment_integrity": "restlessness",
            "vitality": "weariness",
        }.get(dominant or "", "neutrality")

    if v > 0:
        if a >= 0.55:
            return "excitement"
        elif a >= 0.30:
            return "contentment"
        else:
            return "serenity"
    else:
        if a >= 0.55:
            return {
                "coherence": "anxiety",
                "relational_warmth": "distress",
                "commitment_integrity": "guilt",
            }.get(dominant or "", "agitation")
        elif a >= 0.30:
            return {
                "coherence": "unease",
                "commitment_integrity": "guilt",
            }.get(dominant or "", "disquiet")
        else:
            return "sadness"


def construct(state=None):
    """Build an EmotionOutput from grounded architectural signals.

    Returns an EmotionOutput (same schema as emotion_node.py) or None on failure.
    Fail-open: missing sources default to neutral rather than crashing."""
    try:
        from core.schema import EmotionOutput
    except ImportError as exc:
        logger.debug("[emotion-construction] EmotionOutput import failed (non-fatal): %s", exc)
        return None

    # --- Read grounded sources (each fail-open) ---
    try:
        from core import homeostasis
        ca = homeostasis.core_affect()
    except Exception as exc:
        logger.debug("[emotion-construction] homeostasis.core_affect() failed (non-fatal): %s", exc)
        ca = {}

    try:
        from core import arousal as _ar
        ar_level = _ar.level()
    except Exception as exc:
        logger.debug("[emotion-construction] arousal.level() failed (non-fatal): %s", exc)
        ar_level = 0.4

    try:
        from core import satisfaction as _sat
        sat = _sat.snapshot()
    except Exception as exc:
        logger.debug("[emotion-construction] satisfaction.snapshot() failed (non-fatal): %s", exc)
        sat = {"liking": {}, "wanting": {}, "gap": {}}

    try:
        from core import concerns as _con
        concerns = _con.current_concerns()
    except Exception as exc:
        logger.debug("[emotion-construction] concerns.current_concerns() failed (non-fatal): %s", exc)
        concerns = []

    # --- Grounded dimensions ---
    v = _clip_valence(ca.get("valence", 0.0))           # tonic: 1 - 2*drive
    a = _clip01(ar_level)                                # global activation

    # --- Constructed dimensions (HYPOTHESIS) ---
    # joy: positive valence scaled by how much liking is present
    liking_sum = sum(float(x) for x in sat.get("liking", {}).values())
    liking_norm = _clip01(liking_sum / 4.0) if liking_sum > 0 else 0.0
    joy = _clip01(max(0.0, v) * (0.5 + 0.5 * liking_norm))

    # fear: negative valence × arousal × threat relevance of active concerns
    fear = _clip01(max(0.0, -v) * a * _threat_weight(concerns))

    # anger: negative valence × inverse arousal × satisfaction gap (blocked pursuit)
    anger = _clip01(max(0.0, -v) * (1.0 - a) * _frustration_weight(sat))

    # trust: relational warmth from satisfaction
    trust = _relational_trust(sat)

    # surprise: interoceptive prediction error (genuine surprise from homeostasis)
    surprise = _clip01(ca.get("arousal", 0.0))  # homeostasis arousal = interoceptive PE

    # disgust: VESTIGIAL — no grounded source
    disgust = 0.0

    # --- Primary label (HYPOTHESIS — conditioned on dominant deficit) ---
    dominant = ca.get("dominant")
    primary = _label_from_quadrant(v, a, dominant)

    return EmotionOutput(
        joy=joy, fear=fear, anger=anger,
        trust=trust, surprise=surprise, disgust=disgust,
        valence=v, arousal=a, primary=primary,
    )


# J-1926 / F-2550: one daemon thread per cycle writes this log; a slow DB read can overlap the next cycle's thread; serialise the append.
_AR_LOG_LOCK = threading.Lock()


def _affective_retrieval_shadow(llm_vec, con_vec, query_text, cycle_id: str, max_candidates: int = 300) -> None:
    """Experiment C, part 2 — 'affective retrieval' concretely means `core/euclidean_recall.py`'s
    `affect_match` feature (cosine similarity between a memory's stored `emotion_embedding` and the
    current felt-quality vector), which is one of the six dims that already shape state-weighted recall
    ranking (verified via grep: `euclidean_recall.featurize()` is the only consumer of a mood vector
    for retrieval; `core/mood.py`'s `current_vec()` — sourced from the LLM's `state.emotion`,
    `orchestrator.py:671` — is what live affective retrieval would read if wired).

    Ranks the SAME candidate memory-fragment rows TWICE with identical weights (`_AR_WEIGHTS`) —
    once using the LLM's mood embedding as `field_emo_vec`, once using the constructed one — so any
    divergence in the resulting top-k is attributable to the mood vector, not the ranking weights.
    Logs Jaccard overlap of the top-5 plus the mean affect_match under each side.

    Off-thread (does a DB read) and fail-open — mirrors euclidean_recall.shadow_log()'s own pattern
    exactly (same query, same table, same candidate cap ballpark) so the two are directly comparable.
    Writes to the SIBLING file `_AR_SHADOW_LOG`, never the main shadow log, and never raises."""
    if con_vec is None:
        return
    try:
        import json
        import sqlite3
        import numpy as np
        from core import euclidean_recall as _er
        from core.memory.store import _embed

        db = _DATA / "memory" / "nascence.db"
        con = sqlite3.connect(str(db))
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT content, embedding, emotion_embedding, timestamp, importance, layer, origin "
            "FROM memory_fragments WHERE embedding IS NOT NULL AND (cold IS NULL OR cold=0) AND origin != 'system_note' "
            "ORDER BY timestamp DESC LIMIT ?", (max_candidates,)).fetchall()
        con.close()
        if not rows:
            return

        need_emb = _embed(query_text) if query_text else None  # None -> semantic_sim=0 for all rows,
        # which is deliberate: it isolates the affect_match dimension as the source of any divergence.
        need_pt = np.array(_AR_NEED_PT, dtype=np.float32)
        weights = np.array(_AR_WEIGHTS, dtype=np.float32)

        def _top(field_vec, k: int = 5):
            scored = _er.rank(rows, need_emb, field_vec, need_pt, weights, top_k=k)
            titles = [" ".join((r["row"]["content"] or "").split())[:80] for r in scored]
            match = [r["features"]["affect_match"] for r in scored]
            return titles, match

        out_row = {"ts": round(time.time(), 1), "cycle_id": cycle_id,
                   "candidates": len(rows), "llm_vec_available": llm_vec is not None}
        t_con, am_con = _top(con_vec)
        out_row["con_affect_match_mean"] = round(sum(am_con) / len(am_con), 4) if am_con else None
        if llm_vec is not None:
            t_llm, am_llm = _top(llm_vec)
            jac = len(set(t_llm) & set(t_con)) / max(1, len(set(t_llm) | set(t_con)))
            out_row["jaccard_llm_vs_con"] = round(jac, 3)
            out_row["llm_affect_match_mean"] = round(sum(am_llm) / len(am_llm), 4) if am_llm else None
            if out_row["llm_affect_match_mean"] is not None and out_row["con_affect_match_mean"] is not None:
                out_row["affect_match_mean_gap"] = round(
                    abs(out_row["llm_affect_match_mean"] - out_row["con_affect_match_mean"]), 4)

        _DATA.mkdir(parents=True, exist_ok=True)
        with _AR_LOG_LOCK, open(_AR_SHADOW_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(out_row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[emotion-construction] affective-retrieval shadow failed (non-fatal): %s", exc)


def shadow_log(llm_emotion, con_emotion, state=None, cycle_id: str = "") -> None:
    """Log paired LLM-vs-constructor comparison for the three shadow experiments.

    Includes the full grounded state so the experiments can test explanatory sensitivity,
    temporal coherence, and downstream preservation quantitatively."""
    if con_emotion is None:
        return
    try:
        # --- Grounded state snapshot (for Experiment A counterfactual analysis) ---
        grounded = {}
        try:
            from core import homeostasis
            ca = homeostasis.core_affect()
            st = homeostasis.status()
            grounded["drive"] = ca.get("drive")
            grounded["dominant"] = ca.get("dominant")
            grounded["tonic_valence"] = ca.get("valence")
            grounded["phasic_valence"] = ca.get("valence_phasic")
            grounded["variables"] = st.get("variables")
        except Exception as exc:
            logger.debug("[emotion-construction] grounded homeostasis snapshot failed (non-fatal): %s", exc)
        try:
            from core import arousal as _ar
            grounded["arousal_level"] = _ar.level()
        except Exception as exc:
            logger.debug("[emotion-construction] grounded arousal read failed (non-fatal): %s", exc)
        try:
            from core import homeostasis as _h
            s = _h.status()
            grounded["arousal_interoceptive_pe"] = s.get("arousal")
        except Exception as exc:
            logger.debug("[emotion-construction] grounded interoceptive-PE read failed (non-fatal): %s", exc)
        try:
            from core import satisfaction as _sat
            snap = _sat.snapshot()
            grounded["satisfaction"] = snap
        except Exception as exc:
            logger.debug("[emotion-construction] grounded satisfaction snapshot failed (non-fatal): %s", exc)
        try:
            from core import concerns as _con
            cc = _con.current_concerns()
            grounded["concerns"] = [{"kind": c.get("kind"), "text": c.get("text", "")[:80]} for c in cc]
        except Exception as exc:
            logger.debug("[emotion-construction] grounded concerns read failed (non-fatal): %s", exc)

        # --- Downstream comparison (for Experiment C) ---
        downstream = {}
        try:
            from core.schema import AffectState
            # Simulate temperature_bias from LLM dims
            if llm_emotion:
                _a_llm = AffectState(
                    joy=llm_emotion.joy, fear=llm_emotion.fear, anger=llm_emotion.anger,
                    trust=llm_emotion.trust, surprise=llm_emotion.surprise, disgust=llm_emotion.disgust,
                    valence=llm_emotion.valence, arousal=llm_emotion.arousal,
                )
                downstream["llm_temp_bias"] = round(_a_llm.temperature_bias(), 4)
            # Simulate temperature_bias from constructed dims
            _a_con = AffectState(
                joy=con_emotion.joy, fear=con_emotion.fear, anger=con_emotion.anger,
                trust=con_emotion.trust, surprise=con_emotion.surprise, disgust=con_emotion.disgust,
                valence=con_emotion.valence, arousal=con_emotion.arousal,
            )
            downstream["con_temp_bias"] = round(_a_con.temperature_bias(), 4)
        except Exception as exc:
            logger.debug("[emotion-construction] downstream temperature_bias simulation failed (non-fatal): %s", exc)

        # --- Downstream comparison, mood embedding (Experiment C, part 1): both llm_emotion and
        # con_emotion carry the same 8 dims mood.py's felt_text() serialises, so both can be embedded
        # in the SAME MiniLM felt-quality space live affective retrieval would use (mood.embed(), the
        # same function that backs mood.observe()/current_vec()). _embed() normalises, so the dot
        # product IS the cosine similarity — no extra normalisation needed. ---
        _llm_vec = _con_vec = None
        try:
            from core import mood as _mood
            _con_vec = _mood.embed(con_emotion)
            if llm_emotion:
                _llm_vec = _mood.embed(llm_emotion)
            if _llm_vec is not None and _con_vec is not None:
                downstream["mood_embed_cosine"] = round(float((_llm_vec * _con_vec).sum()), 4)
            downstream["mood_embed_available"] = _llm_vec is not None and _con_vec is not None
        except Exception as exc:
            logger.debug("[emotion-construction] downstream mood-embedding comparison failed (non-fatal): %s", exc)

        # --- Downstream comparison, affective retrieval (Experiment C, part 2): does euclidean_recall's
        # affect_match ranking dimension diverge between the LLM's mood vector and the constructed one?
        # Fires off-thread (DB read) into the sibling _AR_SHADOW_LOG, correlated by cycle_id — see
        # _affective_retrieval_shadow()'s docstring for what "affective retrieval" concretely means here
        # and why this can't just be appended inline to `downstream` above. ---
        try:
            import threading as _thr
            _query_text = None
            try:
                _query_text = getattr(getattr(state, "perception", None), "summary", None)
            except Exception:
                _query_text = None
            _thr.Thread(
                target=_affective_retrieval_shadow,
                args=(_llm_vec, _con_vec, _query_text, cycle_id),
                daemon=True,
            ).start()
        except Exception as exc:
            logger.debug("[emotion-construction] affective-retrieval thread spawn failed (non-fatal): %s", exc)

        # --- Geometry census linkage (for exploratory multidimensional analysis) ---
        geometry_tuple_id = None
        try:
            import os
            geo_path = _DATA / "geometry_tuples.jsonl"
            if geo_path.exists():
                sz = os.path.getsize(geo_path)
                if sz > 0:
                    with open(geo_path, "rb") as f:
                        # read last line efficiently
                        f.seek(max(0, sz - 2048))
                        last_line = f.readlines()[-1]
                    last_tuple = json.loads(last_line)
                    # link if the tuple is recent (within 30s)
                    if abs(time.time() - last_tuple.get("ts", 0)) < 30:
                        geometry_tuple_id = f"ts_{last_tuple.get('ts', 0)}"
        except Exception as exc:
            logger.debug("[emotion-construction] geometry census linkage failed (non-fatal): %s", exc)

        # --- Build the shadow row ---
        row = {"ts": round(time.time(), 1), "cycle_id": cycle_id}

        if llm_emotion:
            row.update({
                "llm_primary": llm_emotion.primary,
                "llm_valence": round(llm_emotion.valence, 4),
                "llm_arousal": round(llm_emotion.arousal, 4),
                "llm_joy": round(llm_emotion.joy, 4),
                "llm_fear": round(llm_emotion.fear, 4),
                "llm_anger": round(llm_emotion.anger, 4),
                "llm_trust": round(llm_emotion.trust, 4),
                "llm_surprise": round(llm_emotion.surprise, 4),
                "llm_disgust": round(llm_emotion.disgust, 4),
            })

        row.update({
            "con_primary": con_emotion.primary,
            "con_valence": round(con_emotion.valence, 4),
            "con_arousal": round(con_emotion.arousal, 4),
            "con_joy": round(con_emotion.joy, 4),
            "con_fear": round(con_emotion.fear, 4),
            "con_anger": round(con_emotion.anger, 4),
            "con_trust": round(con_emotion.trust, 4),
            "con_surprise": round(con_emotion.surprise, 4),
            "con_disgust": round(con_emotion.disgust, 4),
        })

        row["grounded_state"] = grounded
        row["downstream"] = downstream
        if geometry_tuple_id:
            row["geometry_tuple_id"] = geometry_tuple_id
        # D-0274 / J-1306 (2026-09-24): tag with input_type directly, off the SAME state object already
        # passed in -- no new import cycle, no join against affect_log.jsonl needed for any row logged
        # from here on. F-1841's stratified Experiment-B read (con_arousal vs llm_arousal by input_type)
        # had to join two files by cycle_id (97.4% coverage) because this field was never logged inline;
        # status() below reads it directly for a permanent, no-re-derive-by-hand stratified breakdown.
        row["input_type"] = getattr(state, "input_type", None)

        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_SHADOW_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    except Exception as exc:
        logger.debug("[emotion-construction] shadow_log() failed (non-fatal): %s", exc)  # fail-open: shadow never disrupts the live path


def status() -> dict:
    """Read-out for du_pulse/HUD (2026-08-19 — a survey found this module actively called from the
    live orchestrator, 152+ rows and growing, with NO reporting surface anywhere reading its log; the
    three named promotion experiments have no code that computes them either. This doesn't build the
    experiments — that's a bigger, separate design task — but it stops the log from being a complete
    blind spot: primary-emotion agreement rate and mean valence gap between the LLM's guess and the
    grounded constructor, the most direct signal for whether the hypothesis is tracking anything real."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): the old read parsed EVERY line then sliced [-500:]; this
        # reads ~500 rows from EOF instead. Same 500-row window, same stats.
        rows = _tail_rows(_SHADOW_LOG, 500)
    except Exception:
        return {"rows": 0}
    if not rows:
        return {"rows": 0}
    paired = [r for r in rows if r.get("llm_primary") and r.get("con_primary")]
    agree = sum(1 for r in paired if r["llm_primary"] == r["con_primary"])
    gaps = [abs(r["llm_valence"] - r["con_valence"]) for r in paired
            if r.get("llm_valence") is not None and r.get("con_valence") is not None]
    try:
        from core.schema import EMOTION_CONSTRUCTED as _flag
    except Exception:
        _flag = False
    # 2026-08-19 fix: primary_agreement_rate compares the LLM's free-text label against the
    # constructor's fixed 16-word quadrant vocabulary (_label_from_quadrant) by exact string match.
    # Verified against 152 real rows: the two vocabularies are near-disjoint (LLM: curiosity 87.5% of
    # rows, plus surprise/fear/anxiety/contentment/interest/trust; constructor: disquiet/longing/
    # sadness/unease/distress/contentment/serenity/anxiety/excitement/uncertainty) — a low match rate
    # is close to guaranteed by the label-set design alone, NOT by itself evidence the constructor is
    # miscalibrated. valence_sign_agreement (do the two sides at least agree on positive vs negative?)
    # is the fairer read; it survives the vocabulary mismatch and is what actually caught the real
    # finding (mean_valence_gap stayed large, 0.406, WITH some outright sign disagreements in the raw
    # rows — that part is a genuine open question, not an artifact of this metric).
    sign_pairs = [r for r in paired if r.get("llm_valence") is not None and r.get("con_valence") is not None]
    sign_agree = sum(1 for r in sign_pairs if (r["llm_valence"] >= 0) == (r["con_valence"] >= 0))
    llm_vocab = {r["llm_primary"] for r in paired}
    con_vocab = {r["con_primary"] for r in paired}
    # 2026-08-24 — J-0159 (Experiment C instrumentation): mood-embedding cosine, once enough rows exist.
    mood_cos = [r["downstream"]["mood_embed_cosine"] for r in rows
                if isinstance(r.get("downstream"), dict) and r["downstream"].get("mood_embed_cosine") is not None]
    # D-0274 / J-1306 (2026-09-24): permanent stratified Experiment-B breakdown (con_arousal vs
    # llm_arousal, split by input_type) so this doesn't need re-deriving by hand each time -- F-1841
    # diagnosed the pooled r=-0.221 as a between-group confound: positive within human-turn cycles
    # (r=+0.207), ~zero within internal cycles (r=-0.016). Only rows carrying the `input_type` tag (added
    # by this job, going forward -- see shadow_log() above) count here; older untagged rows in this same
    # tail window are excluded rather than silently guessed at. `tagged_rows` says how much of this
    # window is covered yet -- low coverage right after this ships is expected, not a bug.
    tagged = [r for r in rows if r.get("input_type") in ("human", "internal")
              and r.get("llm_arousal") is not None and r.get("con_arousal") is not None]
    arousal_strat: dict = {"tagged_rows": len(tagged)}
    for grp in ("human", "internal"):
        pts = [r for r in tagged if r["input_type"] == grp]
        xs = [r["con_arousal"] for r in pts]
        ys = [r["llm_arousal"] for r in pts]
        arousal_strat[grp] = {"n": len(pts), "r_con_vs_llm_arousal": _pearson(xs, ys)}
    arousal_strat["note"] = ("expected shape per F-1841/F-1842/D-0274: positive within human, ~zero "
                              "within internal -- a material departure here is new evidence worth a "
                              "fresh founder read, not just confirmation")
    return {
        "rows": len(rows), "paired": len(paired),
        "primary_agreement_rate": round(agree / len(paired), 3) if paired else None,
        "primary_agreement_caveat": ("near-disjoint label vocabularies (overlap "
            f"{len(llm_vocab & con_vocab)}/{len(llm_vocab | con_vocab)} distinct labels) — low "
            "agreement is expected by construction; read valence_sign_agreement instead"),
        "valence_sign_agreement": round(sign_agree / len(sign_pairs), 3) if sign_pairs else None,
        "mean_valence_gap": round(sum(gaps) / len(gaps), 3) if gaps else None,
        "mood_embed_cosine_rows": len(mood_cos),
        "mean_mood_embed_cosine": round(sum(mood_cos) / len(mood_cos), 4) if mood_cos else None,
        "arousal_stratified_by_input_type": arousal_strat,
        "constructed": bool(_flag),
    }


def affective_retrieval_status() -> dict:
    """Read-out for the sibling `_AR_SHADOW_LOG` (Experiment C, part 2 — see
    `_affective_retrieval_shadow()`'s docstring). Same fail-open / read-only pattern as `status()`."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_AR_SHADOW_LOG, 500)   # bounded (J-0278/F-0335): same 500-row window as before
    except Exception:
        return {"rows": 0}
    if not rows:
        return {"rows": 0}
    paired = [r for r in rows if r.get("llm_vec_available") and r.get("jaccard_llm_vs_con") is not None]
    jacs = [r["jaccard_llm_vs_con"] for r in paired]
    gaps = [r["affect_match_mean_gap"] for r in paired if r.get("affect_match_mean_gap") is not None]
    return {
        "rows": len(rows), "paired": len(paired),
        "mean_jaccard_top5": round(sum(jacs) / len(jacs), 3) if jacs else None,
        "mean_affect_match_gap": round(sum(gaps) / len(gaps), 4) if gaps else None,
    }
