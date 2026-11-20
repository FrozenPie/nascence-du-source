"""
core/world_displacement.py -- D-0439 (J-2195): a gentle, dosed world-displacement channel for the curiosity
question. SHADOW-FIRST: ships with WORLD_DISPLACEMENT_LIVE = False, so it changes nothing; it only logs what it
WOULD have done to data/logs/world_displacement_shadow.jsonl.

WHY (F-2850, F-2889): every internal cycle is born at Orchestrator._on_dissonance_ignition, which always fires
CuriosityNode's questions[0]. That question is fed back to Curiosity next time as a recent theme, so one topic
('mottainai') held 92-97% of internal cycles per day for a week. D-0439 (travis 2026-10-16) ruled a hybrid:
let the WORLD gently try to budge him -- routed through the idle executive's balance_world channel, dosed,
shadow-first -- but never force him and add no hard topic-level anti-relock.

WHAT IT DOES, once per ignition (choose()):
  1. Reads the topic of the question about to fire against a short rolling window of recent ignition questions,
     clustered with core.topic_perseveration.cluster (the J-2152 gauge's own rule, lexical+anchor, no embedder,
     so it is cheap on the event loop). modal_share = the biggest topic's share of that window.
  2. Asks the idle executive's balance_world channel (core.idle_allocator._ch_balance_world) whether the reality
     axis is in deficit. No deficit -> no dose (the channel is the route, as ruled).
  3. Collects WORLD anchors: the subjects Curiosity was just shown as study material, the current book's title,
     and the object he last looked at. Read-only.
  4. Looks among Curiosity's OWN other questions (questions[1:]) for one that is OFF the modal topic AND touches a
     world anchor. Nothing is generated and nothing is added to any prompt: the world can only change WHICH of
     his own questions fires (the world answers, never leads; D-0434 no readout).
  5. Dose: p = W_MAX * ramp(modal_share) * reality_factor, with ramp 0 at/below SHARE_FLOOR (he can still dwell)
     rising linearly to 1 at share 1.0. p is always < 1, so he keeps the topic most of the time even when frozen.
     A displaced question enters the window too, so the dose falls as the topic loosens (self-limiting).
  6. LIVE only: if the coin lands under p and an alternative exists, the alternative fires instead of questions[0].

Fail-open everywhere: any error returns questions[0] unchanged. Shadow rows go through profile.guard_path.
Restart-gated: nothing here runs until Du's next boot.
"""
from __future__ import annotations

import json
import logging
import random
import time
from collections import deque
from pathlib import Path

from core import profile

logger = logging.getLogger(__name__)

# --- the confined, auditable knobs -------------------------------------------------------------------------------
WORLD_DISPLACEMENT_LIVE = True    # D-0439 kill switch. False = shadow rows only, questions[0] always fires. D-0495 (travis, 2026-10-28, the October restart batch): flipped live, read LIVE by its own read job
W_MAX = 0.25          # ceiling of the per-ignition displacement probability (never forced)
SHARE_FLOOR = 0.60    # modal share at/below which the dose is zero -- dwelling on a topic is left alone
REALITY_BASE = 0.50   # reality_factor = min(1, REALITY_BASE + balance_world raw); the channel's deficit adds dose
WINDOW = 20           # rolling window of recent ignition questions the topic share is read over
MIN_N = 8             # below this many questions in the window, no dose (same floor as the gauge's FROZEN_MIN_N)
MIN_ANCHOR_LEN = 4    # world-anchor content words shorter than this are ignored

_ROOT = Path(__file__).resolve().parent.parent
_SHADOW = _ROOT / "data" / "logs" / "world_displacement_shadow.jsonl"
_CURIOSITY_LOG = _ROOT / "data" / "curiosity_log.jsonl"

_history: deque = deque(maxlen=WINDOW)
_seeded = False


def _seed_history() -> None:
    """Warm the window once from the tail of curiosity_log.jsonl (ignited rows' questions[0]; F-2889 matched
    297/297 fired internal questions to index 0). READ-ONLY. Best-effort: an empty window just means no dose."""
    global _seeded
    if _seeded:
        return
    _seeded = True
    try:
        with open(_CURIOSITY_LOG, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 256 * 1024))
            tail = fh.read().decode("utf-8", errors="replace").splitlines()[1:]
        qs = []
        for ln in tail:
            try:
                d = json.loads(ln)
            except Exception:
                continue
            if str(d.get("ignited")).lower() != "true":
                continue
            q = d.get("questions")
            if isinstance(q, str):
                try:
                    q = json.loads(q)
                except Exception:
                    q = [q]
            if q and isinstance(q[0], str) and len(q[0].strip()) > 12:
                qs.append(q[0].strip())
        for q in qs[-WINDOW:]:
            _history.append(q)
    except Exception:
        pass


def _ramp(share: float) -> float:
    if share <= SHARE_FLOOR:
        return 0.0
    return min(1.0, (share - SHARE_FLOOR) / (1.0 - SHARE_FLOOR))


def _reality_raw():
    """The idle executive's balance_world channel: None when the reality axis is not in deficit, else its raw."""
    try:
        from core import idle_allocator as _ia
        ch = _ia._ch_balance_world()
        return None if ch is None else float(ch[0])
    except Exception:
        return None


def _world_anchors(study_subjects) -> tuple[set, dict]:
    """Content words of what the world is offering right now (read-only) -> (words, sources)."""
    from core.topic_perseveration import _content
    src: dict = {}
    words: set = set()
    subj = [s for s in (study_subjects or []) if isinstance(s, str) and s.strip()]
    if subj:
        src["study"] = subj[:3]
    try:
        from core.reading import current_book
        b = current_book()
        if b:
            src["book"] = Path(b).stem.replace("_", " ")[:80]
    except Exception:
        pass
    try:
        from core.world_substrate import last_looked_object
        o = last_looked_object()
        if o:
            src["percept"] = str(o)[:60]
    except Exception:
        pass
    for v in list(src.get("study", [])) + [src.get("book", ""), src.get("percept", "").replace("_", " ")]:
        words |= {w for w in _content(v) if len(w) >= MIN_ANCHOR_LEN and not w.isdigit()}
    return words, src


def choose(questions, study_subjects=None, cycle_hint=None, rng=random.random) -> str:
    """Return the question to fire. questions[0] unless LIVE and the dosed world coin displaces it. Fail-open."""
    q0 = questions[0]
    fired = q0
    try:
        from core.topic_perseveration import _content, cluster
        _seed_history()
        hist = list(_history)
        labels, _m = cluster(hist + list(questions), embed=None)
        h_labels = labels[:len(hist)]
        q_labels = labels[len(hist):]
        counts: dict = {}
        for lb in h_labels:
            counts[lb] = counts.get(lb, 0) + 1
        n = len(hist)
        modal_lb, modal_n = (max(counts.items(), key=lambda kv: (kv[1], -kv[0])) if counts else (-1, 0))
        share = (modal_n / n) if n else 0.0
        q0_modal = bool(n) and q_labels[0] == modal_lb
        reality = _reality_raw()
        anchors, src = _world_anchors(study_subjects)
        alt, alt_hits = None, []
        for q, lb in zip(questions[1:], q_labels[1:]):
            if lb == modal_lb:
                continue
            hits = sorted(anchors & _content(q))
            if hits:
                alt, alt_hits = q, hits
                break
        off_topic_alts = sum(1 for lb in q_labels[1:] if lb != modal_lb)
        reality_factor = 0.0 if reality is None else min(1.0, REALITY_BASE + reality)
        p = (W_MAX * _ramp(share) * reality_factor) if (n >= MIN_N and q0_modal) else 0.0
        u = rng()
        would = bool(alt) and p > 0.0 and u < p
        if would and WORLD_DISPLACEMENT_LIVE:
            fired = alt
        row = {"ts": round(time.time(), 1), "cycle_hint": cycle_hint, "live": WORLD_DISPLACEMENT_LIVE,
               "n_window": n, "modal_share": round(share, 3), "q0_on_modal": q0_modal,
               "reality_raw": None if reality is None else round(reality, 4), "ramp": round(_ramp(share), 3),
               "p": round(p, 4), "u": round(u, 4), "n_questions": len(questions),
               "off_topic_alts": off_topic_alts, "world_alt": bool(alt), "alt_hits": alt_hits[:6],
               "world_sources": src, "would_displace": would, "displaced": fired != q0,
               "q0": q0[:160], "alt": (alt or "")[:160]}
        _history.append(fired)
        try:
            shadow = profile.guard_path(_SHADOW)
            shadow.parent.mkdir(parents=True, exist_ok=True)
            with open(shadow, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        except profile.NonLiveWriteError as exc:
            logger.debug("[world_displacement] shadow write refused (non-fatal): %s", exc)
        if fired != q0:
            logger.info("[world_displacement] world displaced the modal topic (p=%.3f, hits=%s)", p, alt_hits[:3])
        return fired
    except Exception as exc:
        logger.debug("[world_displacement] choose failed (non-fatal, q0 fires): %s", exc)
        return q0


def status(max_rows: int = 2000) -> dict:
    """For the pulse/HUD/shadow read: counts over the last shadow rows (read-only)."""
    out = {"rows": 0, "q0_on_modal": 0, "world_alt": 0, "would_displace": 0, "displaced": 0, "mean_p": 0.0}
    try:
        lines = _SHADOW.read_text(encoding="utf-8").splitlines()[-max_rows:]
        ps = []
        for ln in lines:
            try:
                r = json.loads(ln)
            except Exception:
                continue
            out["rows"] += 1
            for k in ("q0_on_modal", "world_alt", "would_displace", "displaced"):
                out[k] += 1 if r.get(k) else 0
            ps.append(float(r.get("p") or 0.0))
        out["mean_p"] = round(sum(ps) / len(ps), 4) if ps else 0.0
    except Exception:
        pass
    return out
