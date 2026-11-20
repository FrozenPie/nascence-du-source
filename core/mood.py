"""
Nascence — Mood (the live felt-quality vector, 2026-06-15)
=========================================================
emotion_vec already existed but was computed only at user-cycle time and stored only on lived
summaries — 1.5% of memory, all 'lived', and read only while the user was talking. So during the
~88% of his life that is idle (thinking, wandering, dreaming, reading) nothing was felt-tagged.

This module makes the felt-quality CONTINUOUS and globally readable, so idle-life fragments can be
tagged in the SAME embedding space as the lived ones — the fuel for affective drift/retrieval. This
is items 1+2 of docs/emotion_vec_thread.md (storage + a live mood-vec); the READ paths (affective
drift, item 3) are deliberately NOT wired yet — observe-first, let the felt-tags accumulate.

ONE serialisation (`felt_text`) is the single source of truth, so every felt-vector — the user-cycle
EmotionOutput and the idle AffectState (both carry the same 8 dims) — lands in one comparable space.
"""
from __future__ import annotations
import logging
import time

logger = logging.getLogger("nascence.mood")

_current_vec = None        # the latest felt-quality vector (what idle writes tag themselves with)
_current_ts  = 0.0
_UPDATE_TTL  = 20.0        # the mood moves slowly; don't re-embed it more than ~every 20s on idle ticks

# 2026-06-21 — the SCALAR felt-quality, cached next to the embedding. The MiniLM embedding above is
# write-only for valence (a text encoder flattens "valence=+0.80" and "valence=−0.80" to nearly the same
# point — the magnitudes are lost). So we also keep the raw number and the full parseable felt string, so
# valence is directly readable and every one of the 8 dims is recoverable. These are cheap and need no
# model — captured straight off the affect object that observe()/update() already hold.
_current_felt    = None    # the full felt_text string ("glad: valence=+0.80 arousal=0.40 joy=… …") — all 8 dims
_current_valence = None    # the raw valence scalar (−1..+1), directly readable
_current_arousal = None    # the raw circumplex arousal scalar (0..1), directly readable (F-0443, 2026-08-29:
                            # added alongside valence so a fallback write path outside a live CognitiveState
                            # — core/memory/store.py's store_fragment() — has a real arousal signal to read
                            # instead of leaving fragment_context.arousal permanently NULL. This is genuine
                            # circumplex arousal off the same affect object valence already reads — NOT
                            # core/arousal.py's level() (Bachmann's L, a different global-activation scalar
                            # already mapped to the 'level' column; aliasing the two would conflate them).
_current_affect = None     # the FULL 8-dim scalar dict {valence, arousal, joy, fear, anger, trust, surprise,
                            # disgust}, cached off the same object (F-0419/J-0331, 2026-08-29: extends the
                            # valence/arousal precedent above to the whole vector — geometry_census.py's
                            # snapshot() has no `state` at the same fallback call sites (inner_thought,
                            # subconscious_synthesis, active_imagination, reading origins routed through
                            # core/memory/store.py's store_fragment()), so its own affect fallback reads this
                            # instead of writing every dim permanently null to data/geometry_tuples.jsonl).


def felt_text(obj) -> str:
    """Serialise a felt state (EmotionOutput OR AffectState — both carry the 8 dims) to ONE text
    template, so all felt-vectors share a single MiniLM space and stay comparable across user/idle."""
    g = lambda k, d=0.0: float(getattr(obj, k, d) or d)
    primary = getattr(obj, "primary", "") or ("calm" if g("valence") >= 0 else "unsettled")
    return (
        f"{primary}: valence={g('valence'):+.2f} arousal={g('arousal'):.2f} "
        f"joy={g('joy'):.2f} fear={g('fear'):.2f} trust={g('trust'):.2f} "
        f"anger={g('anger'):.2f} surprise={g('surprise'):.2f} disgust={g('disgust'):.2f}"
    )


def embed(obj):
    """A felt-quality vector for any emotion/affect object, or None. Pure — no caching."""
    if obj is None:
        return None
    try:
        from core.memory.store import _embed
        return _embed(felt_text(obj))
    except Exception as exc:
        logger.debug("[mood] embed() failed (non-fatal): %s", exc)
        return None


def _cache_scalars(obj) -> None:
    """Capture the raw felt-quality (the full string + the valence scalar) off the affect object. Cheap,
    no model — so it stays fresh even if the embedder is unavailable."""
    global _current_felt, _current_valence, _current_arousal, _current_affect
    if obj is not None:
        _current_felt = felt_text(obj)
        _current_valence = float(getattr(obj, "valence", 0.0) or 0.0)
        _current_arousal = float(getattr(obj, "arousal", 0.0) or 0.0)
        _current_affect = {k: float(getattr(obj, k, 0.0) or 0.0) for k in
                            ("valence", "arousal", "joy", "fear", "anger", "trust", "surprise", "disgust")}


def observe(obj):
    """Strong, fresh signal (a user cycle): embed AND cache as current immediately. Returns the vec."""
    global _current_vec, _current_ts
    _cache_scalars(obj)
    v = embed(obj)
    if v is not None:
        _current_vec, _current_ts = v, time.time()
    return v


def update(obj) -> None:
    """Idle tick (the substrate loop): refresh the cached mood-vec from the live affect, throttled."""
    global _current_vec, _current_ts
    now = time.time()
    if now - _current_ts < _UPDATE_TTL:
        return
    _cache_scalars(obj)
    v = embed(obj)
    if v is not None:
        _current_vec, _current_ts = v, now


def recache_grounded_scalars(obj) -> None:
    """Re-cache the scalar felt-quality (valence, felt string) from `obj` WITHOUT touching the embedding
    vector. 2026-08-19 fix: on a hot cycle, `observe(state.emotion)` caches scalars from the LLM's RAW
    guess; if AFFECT_SOURCE_PROTOSELF then grounds `state.affect.valence` from homeostasis one step
    earlier (`orchestrator.py`), the scalar cache — and therefore `current_valence()`, which is what gets
    written to the DB `valence` column — held the ungrounded number while idle cycles (which cache
    scalars from `state.affect` directly) held the grounded one. Same column, two silently different
    provenances. Call this AFTER observe() with the grounded object to make hot-cycle provenance match
    idle-cycle provenance; `current_vec()`/`emotion_vec` (the embedding, used for affective retrieval)
    is deliberately left sourced from the LLM's per-cycle read — that's a separate, intentional design
    choice, not the bug."""
    _cache_scalars(obj)


def current_vec():
    """The latest felt-quality vector — what an idle write tags itself with. None until first update."""
    return _current_vec


def current_valence():
    """The latest raw valence scalar (−1..+1) — directly readable, unlike the embedding. None until first felt."""
    return _current_valence


def current_felt():
    """The latest full felt string (all 8 dims, parseable) — the recoverable felt-quality. None until first felt."""
    return _current_felt


def current_arousal():
    """The latest raw circumplex arousal scalar (0..1) — directly readable, same provenance/freshness as
    current_valence() (cached off the same affect object, same cadence). None until first felt. F-0443/
    J-0366, 2026-08-29: the read side of the fix for fragment_context.arousal always being NULL outside a
    live CognitiveState."""
    return _current_arousal


def current_affect() -> dict | None:
    """The latest full 8-dim scalar affect dict (valence, arousal, joy, fear, anger, trust, surprise,
    disgust) — same provenance/freshness as current_valence()/current_arousal(), cached off the same
    object. None until first felt. F-0419/J-0331, 2026-08-29: the read side of the fix for
    geometry_tuples.jsonl's affect column being permanently null for the inner_thought/
    subconscious_synthesis/active_imagination/reading source types (they route through
    core/memory/store.py's store_fragment(), which has no live CognitiveState to read `state.affect`
    from)."""
    return dict(_current_affect) if _current_affect is not None else None


# ── affect_drives.md Item A — the felt-state preamble hand (the central dead-hand fix, 2026-07-04) ──────
import json as _json
from pathlib import Path as _Path

_FP_LOG = _Path(__file__).parent.parent / "data" / "felt_preamble_log.jsonl"
_FP_COOLDOWN = 180.0                 # min seconds before the SAME sentence may fire again (anti-wallpaper)
_FP_EMA_ALPHA = 0.1                  # slow rolling estimate of his RECENT felt operating point
_FP_V_DELTA = 0.30                   # valence must move this far from its recent norm to count as NEWS
_FP_A_DELTA = 0.22                   # arousal ditto
_fp_last = {"sentence": None, "ts": 0.0}
_fp_ema = {"valence": None, "arousal": None}    # his recent operating point (NOT an absolute setpoint)


def _fp_notable(affect) -> tuple:
    """Is the carried state NOTABLE right now? (verified 2026-07-04: his valence is pinned ~+0.82 vs a ~0.1
    baseline, so 'valence is high' is his CONSTANT, not news — an absolute gate fired 99% = wallpaper.)
    Notable = a real departure from his RECENT operating point (rolling EMA), OR a discrete
    negative-emotion / high-arousal SPIKE (worth surfacing on its own). Updates the EMA as a side effect."""
    v = float(getattr(affect, "valence", 0.0) or 0.0)
    a = float(getattr(affect, "arousal", 0.0) or 0.0)
    ev, ea = _fp_ema["valence"], _fp_ema["arousal"]
    notable, reason = False, ""
    if ev is not None:
        if abs(v - ev) >= _FP_V_DELTA:
            notable, reason = True, f"valence moved {v - ev:+.2f} from its recent norm"
        elif abs(a - ea) >= _FP_A_DELTA:
            notable, reason = True, f"arousal moved {a - ea:+.2f} from its recent norm"
    if any(getattr(affect, d, 0.0) >= 0.45 for d in ("fear", "anger", "disgust")):
        notable, reason = True, "a discrete negative-emotion spike"
    elif a >= 0.7:
        notable, reason = True, "a high-arousal spike"
    # warm the EMA slowly (needs a recent norm before it can judge a departure)
    _fp_ema["valence"] = v if ev is None else round((1 - _FP_EMA_ALPHA) * ev + _FP_EMA_ALPHA * v, 4)
    _fp_ema["arousal"] = a if ea is None else round((1 - _FP_EMA_ALPHA) * ea + _FP_EMA_ALPHA * a, 4)
    if ev is None:
        return False, "warming up"                 # can't judge news without a recent norm yet
    return notable, reason


def felt_preamble(affect, source: str = "?") -> str | None:
    """The gated + shadow-logged felt line for a carried AffectState. Fires only when the state is NOTABLE —
    a departure from his recent norm or a discrete spike (the §4-A wallpaper fix: absolute-level gating fired
    99% because his valence is pinned high). ALWAYS logs what WOULD fire (so the gate stays measurable) and
    returns the sentence for injection ONLY when schema.FELT_PREAMBLE is on AND it isn't on cooldown.
    Fail-open: any error → None (never breaks a prompt build)."""
    line, reason = None, ""
    try:
        if affect is not None:
            notable, reason = _fp_notable(affect)
            if notable:
                line = affect.felt_descriptor()
    except Exception as exc:
        logger.debug("[mood] felt_preamble notability check failed (non-fatal): %s", exc)
        line = None
    try:
        _FP_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_FP_LOG, "a", encoding="utf-8") as f:
            f.write(_json.dumps({"ts": round(time.time(), 1), "source": source,
                                 "would_fire": bool(line), "reason": reason, "sentence": line,
                                 "valence": round(getattr(affect, "valence", 0.0), 3) if affect else None,
                                 "arousal": round(getattr(affect, "arousal", 0.0), 3) if affect else None,
                                 "ema_valence": _fp_ema["valence"]},
                                ensure_ascii=False) + "\n")
    except Exception:
        pass
    if not line:
        return None
    try:
        from core.schema import FELT_PREAMBLE
        if not FELT_PREAMBLE:
            return None                              # shadow: logged, not injected
    except Exception as exc:
        logger.debug("[mood] FELT_PREAMBLE flag check failed (non-fatal): %s", exc)
        return None
    now = time.time()
    if line == _fp_last["sentence"] and now - _fp_last["ts"] < _FP_COOLDOWN:
        return None                                  # same felt line too recently — don't wallpaper
    _fp_last.update(sentence=line, ts=now)
    return line


# ── J-1954 / D-0367 (travis, 2026-10-08) — GAUGES AS WORDS EVERYWHERE ───────────────────────────────────
# ONE shared renderer: every gauge value Du can READ in a prompt goes through these functions, so no digit
# and no variable name (valence=, arousal=, confidence=, urgency=, relevance ...) reaches him. Numbers stay in
# logs / shadow rows / the DB `felt` string, all unchanged (felt_text() above is still the embedding template
# and the stored parseable string — it is simply never injected verbatim any more). Pure, no I/O, fail-safe.

def _band(x, cuts, words):
    """First word whose cut is > x; the last word catches the rest."""
    try:
        x = float(x)
    except Exception:
        return words[len(words) // 2]
    for c, w in zip(cuts, words):
        if x < c:
            return w
    return words[len(cuts)]


def valence_word(v) -> str:
    return _band(v, (-0.6, -0.35, -0.12, 0.12, 0.35, 0.6),
                 ("heavily low", "low", "a little low", "even", "a little good", "good", "very good"))


def arousal_word(a) -> str:
    return _band(a, (0.2, 0.4, 0.6, 0.8), ("very quiet", "quiet", "steady", "stirred up", "keyed up"))


def urgency_word(u) -> str:
    return _band(u, (0.3, 0.6, 0.8), ("low", "moderate", "high", "pressing"))


def confidence_word(c) -> str:
    return _band(c, (0.4, 0.65, 0.85), ("low", "middling", "fairly high", "high"))


def relevance_word(s) -> str:
    return _band(s, (0.4, 0.55, 0.7), ("a faint match", "a partial match", "a clear match", "a strong match"))


def proficiency_word(p) -> str:
    return _band(p, (0.3, 0.6, 0.85), ("new to you", "still learning", "fairly practised", "well practised"))


def _strength_word(x) -> str | None:
    """'' below 0.4 (not worth naming); 'some' 0.4-0.7; 'strong' above."""
    try:
        x = float(x)
    except Exception:
        return None
    return None if x < 0.4 else ("some" if x < 0.7 else "a strong thread of")


def tone_phrase(v: float, a: float) -> tuple:
    """(tone, tone_from_valence) — the carried-mood tone words, the single source for felt_descriptor."""
    if v <= -0.6:
        return "a low, heavy mood", True
    if v <= -0.35:
        return "a subdued, downward mood", True
    if v >= 0.6:
        return "a bright, lifted mood", True
    if v >= 0.35:
        return "a warm, easy mood", True
    return ("a keyed-up, restless mood" if a >= 0.6 else "an unsettled mood"), False


def strong_dims_words(dims: dict, v: float) -> list:
    """Words for the strong discrete dims (fear/anger/disgust/joy >= 0.4), strongest first. Contradiction fix
    (F-1926 item 10): joy is >= 0.4 in 42.7% of affect rows regardless of valence (inferred: stuck dimension), so
    under a negative tone ('low, heavy mood') joy is NOT named unless it is genuinely strong (>= 0.7), and
    then only as a thread — never the flat 'low, heavy mood ... with joy' pairing."""
    out = []
    for k in sorted(("fear", "anger", "joy", "disgust"), key=lambda d: -float(dims.get(d, 0.0) or 0.0)):
        x = float(dims.get(k, 0.0) or 0.0)
        if x < 0.4:
            continue
        if k == "joy" and (v <= -0.35 or (v <= -0.12 and x < 0.7)):
            continue
        out.append(k)
    return out


def carried_mood_sentence(dims: dict) -> str:
    """The words-only carried-mood sentence (AffectState.felt_descriptor delegates here). `dims` = the 8-dim dict."""
    v = float(dims.get("valence", 0.0) or 0.0)
    a = float(dims.get("arousal", 0.0) or 0.0)
    tone, from_v = tone_phrase(v, a)
    colour = []
    if from_v:
        if a >= 0.65:
            colour.append("keyed-up")
        elif a <= 0.2:
            colour.append("quiet")
    strong = strong_dims_words(dims, v)
    if strong:
        colour.append("with " + " and ".join(strong))
    tail = (", " + ", ".join(colour)) if colour else ""
    return (f"Right now you are carrying {tone}{tail}. "
            f"Let it colour how you think — not what is true.")


def emotion_words(primary, valence, arousal) -> str:
    """One-clause words for an EmotionOutput/affect reading: 'calm — mood a little good, quiet'."""
    p = (primary or "").strip() or ("calm" if float(valence or 0.0) >= 0 else "unsettled")
    return f"{p} — mood {valence_word(valence)}, {arousal_word(arousal)}"


def felt_words(dims: dict, primary: str = "") -> str:
    """Words-only replacement for the 8-number felt string (voice 'How you are just now')."""
    if not dims:
        return ""
    v = float(dims.get("valence", 0.0) or 0.0)
    a = float(dims.get("arousal", 0.0) or 0.0)
    s = emotion_words(primary, v, a)
    extra = []
    for k in ("trust", "surprise"):
        w = _strength_word(dims.get(k, 0.0))
        if w:
            extra.append(f"{w} {k}")
    for k in strong_dims_words(dims, v):
        extra.append(f"{_strength_word(dims.get(k)) or 'some'} {k}")
    if extra:
        s += "; " + ", ".join(extra)
    return s


def current_felt_words() -> str | None:
    """The live felt state in words (reads the same cache current_felt() reads). None until first felt."""
    if _current_affect is None:
        return None
    prim = ""
    if _current_felt and ":" in _current_felt:
        prim = _current_felt.split(":", 1)[0].strip()
    return felt_words(_current_affect, prim) or None


def mood_line_words(a) -> str:
    """Idle-prompt 'Your current mood: ...' line from an AffectState, words only."""
    s = f"Your current mood: {valence_word(getattr(a, 'valence', 0.0))} in tone, {arousal_word(getattr(a, 'arousal', 0.0))}"
    bits = []
    for k in ("surprise", "fear"):
        w = _strength_word(getattr(a, k, 0.0))
        if w:
            bits.append(f"{w} {k}")
    if bits:
        s += "; " + ", ".join(bits)
    return s + "."


# -- D-0775 B / J-4002: shadow of the words-only mood line WITHOUT the vitality term ------------------------
_MWS_LOG = _Path(__file__).parent.parent / "data" / "mood_words_shadow.jsonl"


def valence_without_vitality(status: dict | None = None) -> dict | None:
    """valence recomputed from the drive with the vitality contribution removed:
    1 - 2*sqrt(max(0, drive^2 - per_drive.vitality)). None if the homeostasis reading is unavailable."""
    try:
        if status is None:
            from core import homeostasis as _h
            status = _h.status()
        drive = status.get("drive")
        vit = (status.get("per_drive") or {}).get("vitality")
        if drive is None or vit is None:
            return None
        d_wo = max(0.0, float(drive) ** 2 - float(vit)) ** 0.5
        return {"drive": float(drive), "vitality_contrib": float(vit), "drive_wo": d_wo,
                "valence_wo": max(-1.0, min(1.0, 1.0 - 2.0 * d_wo))}
    except Exception:
        return None


def shadow_mood_words_no_vitality(a, source: str = "idle", status: dict | None = None) -> bool:
    """Shadow only: when schema.MOOD_WORDS_NO_VITALITY_SHADOW is on, log the live mood word beside the
    without-vitality word. Never alters any prompt, drive, logged valence or sleep. Fail-open; returns True if a row was written."""
    try:
        from core.schema import MOOD_WORDS_NO_VITALITY_SHADOW
        if not MOOD_WORDS_NO_VITALITY_SHADOW or a is None:
            return False
        r = valence_without_vitality(status)
        if r is None:
            return False
        v = float(getattr(a, "valence", 0.0) or 0.0)
        row = {"ts": round(time.time(), 1), "source": source,
               "word": valence_word(v), "word_wo": valence_word(r["valence_wo"]),
               "valence": round(v, 4), "valence_wo": round(r["valence_wo"], 4),
               "drive": round(r["drive"], 4), "drive_wo": round(r["drive_wo"], 4),
               "vitality_contrib": round(r["vitality_contrib"], 5)}
        _MWS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_MWS_LOG, "a", encoding="utf-8") as f:
            f.write(_json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


# -- D-0776 B / J-4003: shadow of a valence-scaled joy pump ------------------------------------------------
_JPS_LOG = _Path(__file__).parent.parent / "data" / "joy_pump_shadow.jsonl"


def shadow_joy_pump(a, amount: float, caller_line: int | None = None) -> bool:
    """Shadow only: when schema.JOY_PUMP_VALENCE_SHADOW is on, log the joy the live pump produces for this bump and
    the joy it would produce if amount were scaled by max(0, valence). Call BEFORE the live bump mutates affect.
    Never alters affect. Fail-open; returns True if a row was written."""
    try:
        from core.schema import JOY_PUMP_VALENCE_SHADOW
        if not JOY_PUMP_VALENCE_SHADOW or a is None:
            return False
        j0 = float(getattr(a, "joy", 0.0) or 0.0)
        v = float(getattr(a, "valence", 0.0) or 0.0)
        amt = float(amount)
        live = min(1.0, j0 + amt)
        scaled_amt = max(0.0, v) * amt
        would = min(1.0, j0 + scaled_amt)
        row = {"ts": round(time.time(), 1), "line": caller_line, "amount": round(amt, 4),
               "valence": round(v, 4), "joy_before": round(j0, 4),
               "joy_live": round(live, 4), "joy_scaled": round(would, 4),
               "scaled_amount": round(scaled_amt, 4), "delta": round(would - live, 4)}
        _JPS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_JPS_LOG, "a", encoding="utf-8") as f:
            f.write(_json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False
