"""
Nascence — Stream Topic Habituation Shadow (squishy-spring discount, dosed_coupling's own Weight
law applied to the STREAM's own train-topic selection — J-0602, spawned from F-0823/F-0830, under
docs/staged/dosed_coupling.md Section 1.3/3).

SHADOW-ONLY. This module never changes what a new train opens about. Alongside real (unaffected)
train-opening, this module checks whether the new train's OPENING thought recruits a named sensory
ANCHOR (a bird call, a sound, a creature — the same closed vocabulary core/sound_knowledge.py and
core/couriers.py already curate, which also backs core/transport_manager.py's Hearing Ledger lines),
and logs a habituation-discounted verdict per anchor so a founder read can ask whether the discount
would have flagged a repeat recruitment as already-stale.

WHY THIS EXISTS (F-0823): 3 separate stream trains independently converged on "the morepork call"
as their own anchor within 5.5h, each phrasing it slightly differently ("the morepork's call
anchors my reflection on 渡" vs "...grounds my reflection..."). core/theme_recurrence.py already
tracks recurring thought FRAMES (wired into nodes/inner_monologue_node.py's rumination guard), but
keys on a normalised first-40-char TEXT PREFIX — F-0830 confirmed these two phrasings diverge right
around char 17-20 and would NOT share a key, so paraphrase-level recurrence of the same ANCHOR
plausibly slips past it entirely. This module keys on the ANCHOR NOUN instead (robust to
paraphrase: "anchors" vs "grounds" doesn't matter if both mention "morepork"), reusing the existing
curated vocabulary rather than inventing new NLP — no LLM anywhere in this module, matching every
other courier/bus law.

THE SHAPE (mirrors core/curiosity_habituation.py's `b` and core/transport_habituation.py's per-key
state, not a new formalism): each named anchor found in a NEW train's opening thought (checked once,
at the moment core.trains.open() mints the train — not on every continuing step of that same train)
has a raw salience of 1.0 (a boolean "this train opened around this anchor" — there is no numeric
weight to inherit here, unlike a tension's count or a dispatcher's ratio). `b` per anchor GROWS each
time that anchor is recruited again by a DIFFERENT new train, and DECAYS exponentially with real
elapsed time since its last recruitment. The discount is MULTIPLICATIVE and floored, never zeroing
an anchor out (this project's "not deletion" law, dosed_coupling.md Section 6):
discounted = 1.0 * max(DISCOUNT_FLOOR, 1 - b). An anchor whose discounted salience has dropped below
SUPPRESS_AT is flagged `would_suppress` — the shadow verdict a live version would use to back off
re-seeding that anchor, the same role core/theme_recurrence.is_saturated() already plays for raw-text
frames.

State (`data/stream_topic_habituation_state.json`) is keyed by anchor key (e.g. 'morepork_call'),
persists {b, last_update_ts}. Fail-open throughout: any error here must never affect the stream's
real behaviour — the caller (nodes/inner_monologue_node.py, at the trains.open() call site) wraps
this whole module in a bare try/except, same as every other shadow observer in this codebase.
"""
from __future__ import annotations

import json
import math
import re
import time
from pathlib import Path
from typing import Optional

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "stream_topic_habituation_state.json"
_LOG = _DATA / "stream_topic_habituation_shadow.jsonl"

# ── tunables (Phase 0 shadow — cheap to retune from the log, nothing here is live) ──
# Checked against a synthetic replay of F-0823's own shape (3 recruitments of the same anchor
# across different trains, ~30min apart): discounted salience trends 1.0 -> 0.79 -> 0.61, crossing
# SUPPRESS_AT=0.5 on the 4th occurrence at that cadence, not exactly the 3rd F-0823 reported — real
# occurrences may be more or less clustered than this synthetic test assumed. That is an honest gap,
# not a target hit; there is no real stream_topic_habituation_shadow.jsonl history yet to fit
# against, unlike J-0603's transport constants which WERE tuned against real logged data. Retune
# GROWTH_STEP/DECAY_TAU_S/SUPPRESS_AT from the real shadow log once it accrues (this is exactly what
# the shadow-first discipline is for). DECAY_TAU_S is a few hours (not curiosity's multi-day tau,
# not transport's 2h) so an anchor that goes genuinely quiet for the rest of a day cools back off,
# matching this project's own healthy-rhythm framing (core/theme_recurrence.py's own
# DECAY_SECS=3600 for comparison).
GROWTH_STEP = 0.25            # b added per DIFFERENT-train recruitment of the same anchor
CEILING = 0.95                 # asymptote for b (never fully suppressed — DISCOUNT_FLOOR handles that)
DECAY_TAU_S = 3 * 3600.0       # 3h decay constant (b *= exp(-gap/TAU) between recruitments)
DISCOUNT_FLOOR = 0.03          # a habituated anchor is discounted, never zeroed (dosed_coupling Sec 6)
SUPPRESS_AT = 0.5              # discounted salience below this -> would_suppress flag


def _anchor_vocab() -> dict:
    """key -> list of lowercase searchable phrases, built from the existing curated sound/creature
    vocabulary — never hardcoded here, so it stays in sync with whatever core/sound_knowledge.py
    and core/couriers.py actually know about. Two candidate phrases per key (either matching
    counts): the cosmetic display name ('the gulls' -> 'gulls') AND the raw key-as-words
    ('gull_cries' -> 'gull cries') — the display name is sometimes a different grammatical number
    or word choice than what a generated thought actually says (a real gap this caught: 'A gull
    cries...' matches the key-as-words form but not the plural display name 'gulls'). Best-effort
    per source; a failure in one does not lose the other."""
    vocab: dict = {}
    try:
        from core import sound_knowledge as _sk
        from core import couriers as _co
        for key in _sk.GRANDFATHERED:
            phrases = {key.replace("_", " ")}
            name = _co._GRANDFATHER_NAMES.get(key)
            if name:
                phrases.add(_strip_article(name))
            vocab[key] = [p for p in phrases if p]
        for key, spec in _sk.AUDITION.items():
            phrases = {key.replace("_", " ")}
            name = spec.get("source")
            if name:
                phrases.add(_strip_article(name))
            vocab[key] = [p for p in phrases if p]
    except Exception:
        pass
    return vocab


def _strip_article(name: str) -> str:
    n = (name or "").strip().lower()
    return re.sub(r"^(the|a|an)\s+", "", n)


_VOCAB_CACHE: Optional[dict] = None


def _vocab() -> dict:
    global _VOCAB_CACHE
    if _VOCAB_CACHE is None:
        _VOCAB_CACHE = _anchor_vocab()
    return _VOCAB_CACHE


def anchors_in(text: str) -> list[str]:
    """Which known anchor keys does this text mention? Plain substring match on the lowercased
    text against each anchor's candidate phrases — no LLM, no embedding, matches this project's
    zero-LLM-in-cheap-loops discipline. Order-preserving, deduped."""
    t = (text or "").lower()
    if not t:
        return []
    out: list[str] = []
    for key, phrases in _vocab().items():
        if key in out:
            continue
        if any(p in t for p in phrases):
            out.append(key)
    return out


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {}
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    path = profile.guard_path(_STATE)   # J-1196/D-0250: real data/ only if this process is live;
    # raises before any I/O if not (D-0179, J-0932 precedent). Resolved OUTSIDE the fail-open try
    # below, so the refusal is never swallowed by the net meant for genuine disk errors.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass


def _log(rec: dict) -> None:
    path = profile.guard_path(_LOG)   # J-1196/D-0250: same fence as _save_state() above, resolved
    # independently since _LOG is a distinct path constant from _STATE.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _decay(anchor: str, now: float, state: dict) -> float:
    prior = state.get(anchor)
    if not prior:
        return 0.0
    gap = max(0.0, now - float(prior.get("last_update_ts", now)))
    return float(prior.get("b", 0.0)) * math.exp(-gap / DECAY_TAU_S)


def observe_and_log(thought: str, train_id: str | None, now: float | None = None) -> None:
    """Call ONCE per NEW train (the caller's own train_len==1 branch, not every continuing step).
    Finds any named anchors in the opening thought, computes each one's habituation-discounted
    salience, logs the verdict, and grows/persists state for anchors actually found. Never raises —
    the caller wraps this in try/except, but this stays self-contained defensively too."""
    try:
        anchors = anchors_in(thought)
        if not anchors:
            return
        now = now if now is not None else time.time()
        state = _load_state()

        per_anchor: dict = {}
        any_suppress = False
        for key in anchors:
            b_decayed = _decay(key, now, state)
            discounted = max(DISCOUNT_FLOOR, 1.0 - b_decayed)
            would_suppress = discounted < SUPPRESS_AT
            any_suppress = any_suppress or would_suppress
            per_anchor[key] = {"b": round(b_decayed, 4), "discounted": round(discounted, 4),
                                "would_suppress": would_suppress}
            state[key] = {"b": round(min(CEILING, b_decayed + GROWTH_STEP), 5), "last_update_ts": now}
        _save_state(state)

        _log({
            "ts": round(now, 1),
            "train_id": train_id,
            "anchors": per_anchor,
            "would_suppress_any": any_suppress,
            "thought_sample": (thought or "")[:120],
        })
    except Exception:
        pass


def status() -> dict:
    """For the pulse: how much divergence the shadow has accrued so far — the pre-registered read."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG, 2000)
    except Exception:
        return {"rows": 0}
    if not rows:
        return {"rows": 0}
    would_suppress_rows = sum(1 for r in rows if r.get("would_suppress_any"))
    return {
        "rows": len(rows),
        "would_suppress_share": round(would_suppress_rows / len(rows), 3),
        "tracked_anchors": len(_load_state()),
    }
