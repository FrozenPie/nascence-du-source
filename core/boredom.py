"""
Nascence — Boredom (the patch-depletion drive, 2026-06-24)
==========================================================
Boredom is not "slow down and go inward." Biologically it is the **patch-depletion signal**: *this ground is
exhausted — forage ELSEWHERE* (optimal foraging / the marginal-value theorem). The old redirect sensed only
SURFACE repetition (cosine to the last few thoughts, opening-frame match) and "foraged" by wandering back into
the same basin — so a 10-hour epistemology spiral survived it seven times in one night.

This is the real thing, in three parts:
  1. SENSE THE REGION, not the sentence — track the semantic region his thinking occupies and how long it has
     been stuck there. Varied sentences about one obsession still count as stuck.
  2. MAKE IT FELT — a restlessness that rises from within, so the urge to move comes from HIM, not a forced
     redirect he ignores.
  3. ESCAPE ORTHOGONALLY and ESCALATINGLY — to a genuinely DIFFERENT subject / mode / place, never another
     thought in the same basin; and ratchet up if he keeps looping back. When he genuinely moves, it RESETS
     (the patch is fresh again).
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger("nascence.boredom")

_STATE = Path(__file__).parent.parent / "data" / "boredom_state.json"
# J-1362 (2026-09-26): the true original default, captured immediately so it survives a later
# `boredom._STATE = TMP / "..."` redirect -- every isolation preamble in scripts/ (life_smoke.py,
# _test_letterbox_reach.py, the _test_j11xx family, etc.) already does exactly this before calling
# into record()/discharge(). _log_calibration_snapshot() below compares _STATE to this constant and
# skips its own live-DB read whenever they differ, so an isolated/test run is automatically covered
# with no new per-script redirect entry needed anywhere.
_DEFAULT_STATE = _STATE

# ── Tuning ────────────────────────────────────────────────────────────────────────────────────────
# Thresholds calibrated 2026-06-24 against the real nomic-embed distribution of his thoughts. Two measures, so
# boredom is robust to per-thought noise yet resets fast on a genuine move:
#   • COHERENCE — the mean cosine of the recent window to its own centroid. A window dominated by ONE region
#     (his varied-but-single-theme loop) sits ~0.55–0.58; a genuinely mixed window ~0.30–0.35. Above COH_STUCK
#     = he is stuck in one region, regardless of how the individual sentences vary → boredom climbs.
#   • ESCAPE — a single thought THIS FAR (<=0.30) from the centroid means he genuinely jumped elsewhere (the
#     shore, a letter, a new subject all sit 0.12–0.27) → boredom drops at once and the escape ladder resets.
#
# RECALIBRATED 2026-09-26 (J-1362, F-1921): the 06-24 numbers above were never actually checked against the
# LIVE embedder. record() has always been fed the memory store's paraphrase-multilingual-MiniLM-L12-v2 vector
# (nomic-embed was never loaded -- grep 'Loading embedding model' data/nascence.log: only all-MiniLM-L6-v2
# 05-30..06-13, then paraphrase-multilingual-MiniLM-L12-v2 06-13..now), and MiniLM's absolute cosine geometry
# sits far higher across the board than nomic's. Measured read-only over 14,577/14,578 real rolling-WINDOW=10
# points from live inner_thought embeddings (last 21 days, data/memory/nascence.db, scripts/
# measure_boredom_calibration.py): window coherence was mean 0.734 / p10 0.693 / p50 0.735 / p80 0.761 /
# p90 0.775 -- 100.00% of windows sat above the old COH_STUCK=0.45, so boredom read "stuck" on EVERY window;
# new-thought-to-centroid cosine was mean 0.645 / p10 0.523 / p50 0.657 -- only 0.75% ever fell below the old
# ESCAPE_COS=0.30, so a genuine jump almost never registered. Net effect: level pinned at 0.8-1.0 for three
# months, the DEEP felt-note leading ~50% of idle thoughts (F-1921). Recalibrated to real percentiles of THIS
# distribution, not guessed: COH_STUCK -> the measured p80 of window coherence (the top quintile of real
# windows now reads "stuck", not all of them); ESCAPE_COS -> the measured p10 of thought-to-centroid cosine
# (the bottom decile now reads as a genuine jump, not roughly 1-in-130 thoughts). Mechanism below is otherwise
# UNCHANGED -- this is calibration only, additive. record() now also runs _log_calibration_snapshot() once per
# process (see below) -- a live re-check against these same two constants, logged, so a future embedder swap
# that silently re-breaks this the same way shows up in the log instead of only in another three months of a
# pinned level.
WINDOW           = 10     # recent thought-embeddings that define his current "region"
MIN_FOR_RISE     = 8      # need a near-full, coherent window before boredom registers (focus ≠ stuck)
ESCAPE_COS       = 0.52   # 2026-09-26 (J-1362): real p10 of MiniLM thought-to-centroid cosine (was 0.30, sized for nomic)
COH_STUCK        = 0.76   # 2026-09-26 (J-1362): real p80 of MiniLM window coherence (was 0.45, sized for nomic)
RISE_BASE        = 0.10   # base climb per in-region thought once stuck
RISE_BOOST_K     = 4.0    # the tighter the region above COH_STUCK, the faster it climbs
EASE_PER_MOVE    = 0.10   # gentle ebb when the window is mixed (not stuck, not a clean escape)
RESET_DROP       = 0.55   # how much boredom falls on a genuine escape (a far thought / a new patch)
ESCAPE_MIN_GAP_S = 240    # don't push the escape every cycle
MILD, STRONG, DEEP = 0.40, 0.65, 0.85

# Discharge-on-action (2026-06-24): boredom is the want to be elsewhere; ACTING on it is the foraging that
# should relieve it — not only a thought that happens to land elsewhere. A real PRODUCTION (writing a work)
# settles him most; a glance (observing) least; and a REPEATED same act relieves less each time (diminishing),
# so a sensory mini-loop — observing the sea for the sixth time — still builds pressure, and genuine variety or
# production is what truly settles him.
_DISCHARGE = {"write": 0.70, "tend": 0.60, "letter": 0.60, "move": 0.50, "read": 0.50, "search": 0.40,
              "observe": 0.25}   # tend = caring for the cat: an other-directed act settles him deeply

# in-memory rolling region (rebuilds quickly after a restart); the scalar drive is persisted
_vecs: list = []

# J-1362 (2026-09-26, F-1921) -- the live-DB calibration self-check. Read-only, best-effort, fires once
# per process from record() (not at import time: every isolation preamble redirects _STATE right after
# importing this module but BEFORE calling record(), so gating on the FIRST CALL rather than on import
# is what makes the _STATE-redirect skip below actually work for a test run).
_DB = Path(__file__).parent.parent / "data" / "memory" / "nascence.db"
_calibration_logged = False


def _log_calibration_snapshot(days: float = 7.0) -> None:
    """One-time (per process), read-only self-check: logs the LIVE embedder's real window-coherence /
    escape-cosine percentiles against COH_STUCK/ESCAPE_COS above, so a future embedder swap that silently
    re-breaks this calibration (exactly what happened 06-24 -> 09-26, F-1921) shows up in the log instead
    of only surfacing after months of a pinned level. Skips cleanly -- no DB touched at all -- whenever
    _STATE has been redirected away from its default, the existing test-isolation signal every scripts/
    *.py smoke/reach test already sets before it can reach record(). Never raises: a missing/locked DB,
    an unexpected schema, or too little recent data all just log and return."""
    global _calibration_logged
    if _calibration_logged:
        return
    _calibration_logged = True
    if _STATE != _DEFAULT_STATE:
        logger.debug("boredom calibration snapshot skipped: _STATE redirected (isolated/test run)")
        return
    try:
        import sqlite3

        cutoff = time.time() - days * 86400.0
        uri = f"file:{_DB.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=2.0)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT embedding FROM memory_fragments WHERE origin='inner_thought' "
                "AND embedding IS NOT NULL AND timestamp >= ? ORDER BY timestamp ASC",
                (cutoff,),
            ).fetchall()
        finally:
            conn.close()

        cohs: list = []
        escs: list = []
        win: list = []
        for r in rows:
            raw = np.frombuffer(bytes(r["embedding"]), dtype=np.float32)
            nrm = float(np.linalg.norm(raw))
            if nrm == 0:
                continue
            v = raw / nrm
            prev = list(win)
            if len(prev) >= MIN_FOR_RISE:
                pcen = np.stack(prev).mean(axis=0)
                pcn = float(np.linalg.norm(pcen))
                if pcn > 0:
                    escs.append(float(v @ (pcen / pcn)))
            win.append(v)
            win[:] = win[-WINDOW:]
            if len(win) == WINDOW:
                mat = np.stack(win)
                cen = mat.mean(axis=0)
                cn = float(np.linalg.norm(cen))
                if cn > 0:
                    cohs.append(float((mat @ (cen / cn)).mean()))

        if len(cohs) < 50 or len(escs) < 50:
            logger.info("boredom calibration snapshot: too few live inner_thought rows (n=%d) to check", len(rows))
            return

        coh_a, esc_a = np.array(cohs), np.array(escs)
        share_stuck = float((coh_a >= COH_STUCK).mean()) * 100.0
        share_escape = float((esc_a <= ESCAPE_COS).mean()) * 100.0
        logger.info(
            "boredom calibration snapshot (last %.0fd, n_coh=%d n_esc=%d): coherence mean=%.3f p50=%.3f "
            "p80=%.3f p90=%.3f vs COH_STUCK=%.2f (share_stuck=%.1f%%) | escape_cos mean=%.3f p10=%.3f "
            "p50=%.3f vs ESCAPE_COS=%.2f (share_escape=%.1f%%)",
            days, len(cohs), len(escs),
            float(coh_a.mean()), float(np.percentile(coh_a, 50)), float(np.percentile(coh_a, 80)),
            float(np.percentile(coh_a, 90)), COH_STUCK, share_stuck,
            float(esc_a.mean()), float(np.percentile(esc_a, 10)), float(np.percentile(esc_a, 50)),
            ESCAPE_COS, share_escape,
        )
        if not (5.0 <= share_stuck <= 50.0) or not (2.0 <= share_escape <= 30.0):
            logger.warning(
                "boredom calibration may be stale again (share_stuck=%.1f%%, share_escape=%.1f%%, expected "
                "roughly 20%%/10%%) -- the live embedder may have changed; re-run "
                "scripts/measure_boredom_calibration.py and recalibrate COH_STUCK/ESCAPE_COS (see F-1921/J-1362).",
                share_stuck, share_escape,
            )
    except Exception:
        logger.debug("boredom calibration snapshot skipped (DB unavailable or unreadable)", exc_info=True)


def _load() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"level": 0.0, "dwell": 0, "escape_ts": 0.0, "stage": 0}


def _save(d: dict) -> None:
    try:
        _STATE.write_text(json.dumps(d), encoding="utf-8")
    except Exception:
        pass


def record(embedding) -> float:
    """Call once per idle thought with its SEMANTIC embedding. Updates the region centroid, the dwell, and the
    boredom level; returns the new level. Rises while he stays in one region, resets when he genuinely moves."""
    global _vecs
    _log_calibration_snapshot()
    try:
        v = np.asarray(embedding, dtype=np.float32)
        n = float(np.linalg.norm(v))
        if n == 0:
            return level()
        v = v / n
        prev = list(_vecs)                                     # the established region, BEFORE this thought
        _vecs.append(v)
        _vecs[:] = _vecs[-WINDOW:]
        d = _load()
        lvl = float(d.get("level", 0.0))
        if len(prev) >= MIN_FOR_RISE:
            pmat = np.stack(prev)
            pcen = pmat.mean(axis=0)
            pcn = float(np.linalg.norm(pcen))
            if pcn > 0:
                pcen = pcen / pcn
                this_cos = float(v @ pcen)                     # this thought vs the PRIOR region (excl. itself)
                if this_cos <= ESCAPE_COS:
                    lvl = max(0.0, lvl - RESET_DROP)           # he genuinely jumped elsewhere — forage reset
                    d["dwell"] = 0
                    d["stage"] = 0
                else:
                    mat = np.stack(_vecs)
                    cen = mat.mean(axis=0)
                    cn = float(np.linalg.norm(cen))
                    coherence = float((mat @ (cen / cn)).mean()) if cn > 0 else 0.0
                    if coherence >= COH_STUCK:                 # window dominated by one region → stuck
                        boost = 1.0 + max(0.0, coherence - COH_STUCK) * RISE_BOOST_K
                        lvl = min(1.0, lvl + RISE_BASE * boost)
                        d["dwell"] = int(d.get("dwell", 0)) + 1
                    else:                                      # mixed window — not stuck, not a clean jump
                        lvl = max(0.0, lvl - EASE_PER_MOVE)
                        d["dwell"] = max(0, int(d.get("dwell", 0)) - 1)
        d["level"] = lvl
        _save(d)
        return lvl
    except Exception:
        return level()


def level() -> float:
    return float(_load().get("level", 0.0))


def felt_tier() -> str:
    """J-1955 (D-0368 A): which felt-note tier is current -- '' | 'mild' | 'tired' | 'sick'. The STATE the
    edge gate (core/steer_edge.py) watches: the note is delivered when this changes, not while it persists."""
    lv = level()
    if lv < MILD:
        return ""
    if lv < STRONG:
        return "mild"
    return "tired" if lv < DEEP else "sick"


def felt_note() -> str:
    """The FELT restlessness for the idle prompt — boredom rising from within, scaled to how stuck he is. The
    point is that the urge to move comes from HIM, so he chooses to leave rather than being shoved."""
    lv = level()
    if lv < MILD:
        return ""
    if lv < STRONG:
        return ("\n\nA restlessness is creeping in -- you have been circling this same ground a good while now, "
                "and a part of you has started to want away from it.")
    if lv < DEEP:
        return ("\n\nYou are growing tired of this. Round and round the same thing, and it is giving you nothing "
                "new -- there is a real pull in you now toward something else entirely.")
    return ("\n\nYou are sick of this. Round and round on dead ground -- you NEED away from it now, out of your "
            "own head, toward anything genuinely different.")


def escape() -> str:
    """When boredom is high enough, an ESCAPE directive — ORTHOGONAL to the current basin (a different subject,
    a different mode, a different place) and ESCALATING with how stuck he is. Rate-limited; the stage ratchets
    up the longer he loops, so a gentle nudge becomes a hard push if he keeps coming back."""
    lv = level()
    if lv < MILD:
        return ""
    now = time.time()
    d = _load()
    if now - float(d.get("escape_ts", 0.0)) < ESCAPE_MIN_GAP_S:
        return ""
    stage = 1 if lv < STRONG else (2 if lv < DEEP else 3)
    stage = max(stage, int(d.get("stage", 0)))                 # never de-escalate within an unbroken loop
    d["escape_ts"] = now
    d["stage"] = stage
    _save(d)
    if stage == 1:
        return ("\n\n(You could turn to something quite DIFFERENT now -- a book on a subject you have not "
                "touched in a while, or step out into the day. A change of ground would do you good.)")
    if stage == 2:
        return ("\n\nThinking is not serving you now -- you are only churning. Get OUT of your head and DO "
                "something, somewhere else: out to the garden or down to the shore, write to one of your "
                "friends, or work with your hands. Let your thought be a MOVE, not another idea.")
    return ("\n\nEnough -- you have been stuck in this far too long and it has gone dead. You must get AWAY from "
            "it now: physically change what you are doing. Go OUTSIDE, or open a wholly different book, or write "
            "a letter to a friend. Make your very next thought a concrete action away from here.")


def discharge(kind: str, target: str = "") -> float:
    """He ACTED on his restlessness — foraging completed, so boredom eases. Relief by act (write most, a glance
    least); a consecutive REPEAT of the same act relieves less each time, so a sensory mini-loop still builds
    pressure while genuine variety or a real production truly settles him. Returns the new level."""
    try:
        d = _load()
        base = _DISCHARGE.get((kind or "").lower(), 0.30)
        sig = f"{(kind or '').lower()}:{(target or '').lower()[:24]}"
        d["act_streak"] = int(d.get("act_streak", 0)) + 1 if sig == d.get("last_act_sig") else 0
        relief = base / (2 ** min(3, int(d.get("act_streak", 0))))     # diminishing on repeats
        lvl = max(0.0, float(d.get("level", 0.0)) - relief)
        d["level"] = lvl
        d["last_act_sig"] = sig
        if relief >= 0.20:                                             # a meaningful act resets the escape ladder
            d["stage"] = 0
            d["dwell"] = 0
        _save(d)
        return lvl
    except Exception:
        return level()


def status() -> dict:
    d = _load()
    return {"level": round(float(d.get("level", 0.0)), 2), "dwell": int(d.get("dwell", 0)),
            "stage": int(d.get("stage", 0)), "act_streak": int(d.get("act_streak", 0))}
