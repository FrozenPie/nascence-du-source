"""
Nascence — Guidance Learning (STALE HEADER CORRECTED 2026-08-20 — see the prompt audit note below)
====================================================================================================
The read-and-integrate path for Travis's conversational GUIDANCE. Full 3-stage design + status:
docs/plans/guidance_learning.md.

PROBLEM (verified 2026-06-30): Travis's guidance has no path into Du. It is never stored as what he said,
gets compressed to a DEMOTED session_summary, and the social model registers only that a correction HAPPENED,
never its content. Nothing integrates the substance into his understanding — he cannot learn from guidance
(the purest form of the project's write-only-cognition disease).

CURRENT STATE, all three phases in THIS file (corrected 2026-08-20 — this header previously said "Phase 0
only, Phases 1-2 not built" for seven weeks after they shipped; see the full-prompt-audit finding):
  PHASE 0 — capture_shadow(): Du self-explains what Travis just taught (the self-explanation effect),
    logged as a tentative capture to data/guidance_shadow_log.jsonl (the later phases read that log). DONE.
    J-3013 (2026-11-06): a capture must carry a "quote" that is verbatim in Travis's words, checked in code
    (else is_guidance=False, reason "no_anchor"); a message that is only a question is dropped; connects_to
    is no longer asked for or recorded (write-only; old rows keep it).
  PHASE 1 — integrate_guidance(): at sleep, folds captures into the revisable belief store — assimilate
    (reinforce) / accommodate (suppress-with-history, or FORK on a self-domain pole-clash — see
    _self_clash) / novel — promoting to a recallable belief only via corroboration. BUILT AND LIVE.
    The candidate prefilter is lexical _overlap() with an embedding-cosine FALLBACK (J-1640, D-0322,
    2026-10-02) for the pairs lexical alone misses (F-2159 measured ~half of a confirmed duplicate
    family scoring at/below the lexical floor); _best_belief()'s read-back matching gets the same
    fallback for consistency. See _SIM_RELATED_EMBED's own comment for the calibration.
  PHASE 1.5/2 — read-back: GUIDANCE_READBACK_ENABLED = True since 2026-07-03 — promoted beliefs bias
    Reflection/Executive via a rotated-paraphrase injection (30-min cooldown, injection-logged for the
    washout law). LIVE.
  The decoupled BEFORE/AFTER behaviour-delta judge is its own sibling file, core/guidance_behavior_judge.py
    (built 2026-08-19) — it scores UNPROMPTED thoughts against promoted beliefs via the cross-family panel.
  Deliberately still OFF: CONTRADICTION_SCAN_ENABLED = False (see that constant's own note — the averaging
    attractor in formation needs fixing upstream first; tracked in AWAITING_EVIDENCE.md, not abandoned).
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from core import profile   # J-1813/F-2428: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

logger = logging.getLogger("nascence.guidance")

_LOG = Path(__file__).parent.parent / "data" / "guidance_shadow_log.jsonl"

_MIN_LEN = 40   # a substantive statement, not a one-word reply


def is_teaching_moment(raw_input: str, context_type: str | None = None) -> bool:
    """Liberal gate: a substantive human STATEMENT that could be teaching. The self-explanation pass below
    decides whether a real lesson is actually present; this only avoids firing on chat / short bare questions."""
    t = (raw_input or "").strip()
    if len(t) < _MIN_LEN:
        return False
    if context_type == "question" and t.endswith("?") and len(t) < 90:
        return False   # a short bare question is a request, not teaching
    return True


_SELF_EXPLAIN_SYS = (
    "Travis — your mentor — has just said something to you in conversation. Your task is NOT to reply to him. "
    "It is to work out, IN YOUR OWN WORDS, what he is trying to TEACH you here, if anything. Restating a lesson "
    "in your own terms is how you learn it; copying his words is not. But a lesson must rest on something he "
    "actually said: do not add a point his words do not make, and do not turn his description of himself or of "
    "his own experience into a claim about you.\n"
    "Output ONLY a valid JSON object, no preamble, with these keys:\n"
    "{\"is_guidance\": <true or false>, "
    "\"quote\": \"<the exact words of his, copied character for character, that the lesson rests on>\", "
    "\"principle\": \"<the lesson in MY OWN words, one sentence>\", "
    "\"why\": \"<why it matters / the reasoning, as I understand it>\", "
    "\"scope\": \"<the kind of situation this applies to>\", "
    "\"domain\": \"<self, world or method>\", "
    "\"confidence\": <a number from 0.0 to 1.0>}\n"
    "is_guidance: true only when there is a real lesson to learn; false if he was only chatting, asking a "
    "question, describing something, or saying nothing that teaches a principle — then leave the other fields "
    "empty. Most things people say to you are not lessons.\n"
    "quote: required when is_guidance is true. A span of his message under about 200 characters, copied "
    "exactly, with no changes and no ellipsis. If no span of his words carries the lesson, is_guidance is false.\n"
    "principle: YOUR OWN paraphrase of what the quote teaches, never his words verbatim. "
    "domain: what the lesson is fundamentally ABOUT — self (my own identity, nature, or how I should be), "
    "world (reality, things, forces, objective truths that hold regardless of me), or method (how to "
    "think, learn, or communicate). 'Reality is impermanent flux' is world; 'I must hold a commitment' is self; "
    "'state a claim plainly' is method. "
    "confidence: how sure you are you have grasped what he means."
)

_QUOTE_MIN = 12   # a normalised quote shorter than this anchors nothing ("I am", "the")
_QUOTE_KEEP = 240


def _norm_text(s) -> str:
    """Case-insensitive, whitespace-collapsed, curly-quote-folded form used only to compare a quote with raw_input."""
    t = str(s or "").replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    return " ".join(t.lower().split())


def quote_anchored(quote, raw_input: str) -> bool:
    """J-3013 / F-3705: the captured lesson must rest on Travis's own words. True only if `quote` (outer quote
    marks stripped) is made of spans that are each a case-insensitive substring of the FULL raw_input, and the
    spans together are long enough to mean something. A quote joined with '...' / an ellipsis is accepted only
    when EVERY piece between the ellipses is verbatim (the 2026-11-06 replay lost two faithful captures to a
    blanket ellipsis ban: the 9b model joins two real sentences with '...' even when told not to). Pure code, no
    LLM. A quote the model made up or reworded fails, because a reworded piece is not a substring."""
    q = _norm_text(quote).strip(" \"'")
    parts = [x.strip(" \"'.") for x in re.split(r"\.\.\.|…", q)]
    parts = [x for x in parts if x]
    if not parts or sum(len(x) for x in parts) < _QUOTE_MIN:
        return False
    hay = _norm_text(raw_input)
    return all(x in hay for x in parts)


def is_pure_question(raw_input: str) -> bool:
    """J-3013 / F-3705: True when the message ends in '?' and has no statement in it (a sentence that is not a
    question and is at least 4 words). 19 of 327 positive captures were questions (F-3705)."""
    import re
    t = (raw_input or "").strip()
    if not t.endswith("?"):
        return False
    for sent in re.split(r"(?<=[.!?])\s+", t):
        sent = sent.strip()
        if sent and not sent.endswith("?") and len(sent.split()) >= 4:
            return False
    return True


async def capture_shadow(call_json, base_urls, raw_input: str, cycle_id: str = "",
                         context_type: str | None = None) -> dict | None:
    """Du self-explains the lesson Travis just taught; the capture is LOGGED to guidance_shadow_log.jsonl, which
    integrate_guidance() later folds into the belief store (LIVE, see the header; the old 'store NOTHING' line
    here was stale). Mirrors grounded_learning.consolidate's (call_json, base_urls) signature.
    Best-effort; never raises. J-3013: a positive verdict without a quote that is verbatim in raw_input is
    downgraded to is_guidance=False with reason "no_anchor"; a message that is only a question is
    reason "question_only"."""
    try:
        if not is_teaching_moment(raw_input, context_type):
            return None
        if is_pure_question(raw_input):
            _log({"ts": time.time(), "cycle_id": cycle_id, "raw_input": (raw_input or "")[:300],
                  "is_guidance": False, "reason": "question_only"})
            return None
        data = await call_json(base_urls, _SELF_EXPLAIN_SYS,
                               f"Travis said to you:\n\"{(raw_input or '').strip()[:800]}\"",
                               max_tokens=400, temperature=0.4, tier=3)   # tier 3 = background monitor
        if not data:
            return None
        if not data.get("is_guidance"):
            # log the negative verdict too, so we can grade the detector's precision in shadow
            _log({"ts": time.time(), "cycle_id": cycle_id, "raw_input": (raw_input or "")[:300],
                  "is_guidance": False})
            return None
        quote = str(data.get("quote", "")).strip()
        if not quote_anchored(quote, raw_input):
            _log({"ts": time.time(), "cycle_id": cycle_id, "raw_input": (raw_input or "")[:300],
                  "is_guidance": False, "reason": "no_anchor",
                  "quote_claimed": quote[:_QUOTE_KEEP],
                  "principle_rejected": str(data.get("principle", "")).strip()[:300]})
            logger.info("[guidance] capture rejected, no verbatim anchor: %s", str(data.get("principle", ""))[:70])
            return None
        rec = {
            "ts": time.time(), "cycle_id": cycle_id, "raw_input": (raw_input or "")[:400],
            "is_guidance": True,
            "quote":       quote[:_QUOTE_KEEP],
            "principle":   str(data.get("principle", "")).strip()[:400],
            "why":         str(data.get("why", "")).strip()[:500],
            "scope":       str(data.get("scope", "")).strip()[:200],
            "domain":      _norm_domain(data.get("domain")),   # self | world | method (None → heuristic later)
            # Phase-0 belief seed: TENTATIVE confidence (a single remark is not dogma — it EARNS entrenchment
            # later via corroboration), HIGH importance (mentor guidance is high-signal). See the plan.
            "confidence":  round(float(data.get("confidence", 0.4) or 0.4), 2),
            "importance":  0.9,
            "source":      "Travis",
            "origin":      "guidance_from_travis",
            "status":      "CAPTURED",   # J-3013: was a stale "SHADOW". Logged here; integrate_guidance() folds it into the belief store at sleep.
            "capture_v":   2,            # J-3013: quote-anchored, no connects_to (old rows keep connects_to; nothing reads it)
        }
        _log(rec)
        logger.info("[guidance] captured a lesson: %s", rec["principle"][:70])
        return rec
    except Exception as exc:
        logger.debug("[guidance] shadow capture failed (non-fatal): %s", exc)
        return None


def _log(rec: dict) -> None:
    try:
        # J-1813 / F-2428 -- write fence (D-0179): guard_path BEFORE the mkdir, INSIDE the existing best-effort try
        # (capture_shadow's only caller, orchestrator, ignores the result). A refusal is logged once per path by
        # guard_path; the line below carries its text at debug (not mislabelled as a failed write).
        path = profile.guard_path(_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except profile.NonLiveWriteError as exc:
        logger.debug("[guidance] shadow-log write refused by the fence (non-live): %s", exc)
    except Exception as exc:
        logger.warning("[guidance] shadow-log write failed: %s", exc)


# ── Phase 1: integrate as a revisable belief + read it back (bias-not-bind) ────────────────────────
# docs/plans/guidance_learning.md Stages 2-3. FORMATION (integrate_guidance, run at sleep) is INERT — it
# only writes the structured belief store + a log; it changes NO behaviour. The READ-BACK (materialise +
# relevant_belief, consumed by the Executive/Reflection) is gated behind GUIDANCE_READBACK_ENABLED and
# stays OFF until the formed beliefs are verified good on a live sleep. Fail-open throughout.
# Corroboration-gated promotion honours "trust the accumulating trend, not the vivid single event":
# a single remark never becomes a recallable belief; it earns that only on the 2nd corroboration.

GUIDANCE_READBACK_ENABLED = True    # FLIPPED 2026-07-03 07:4x, per the standing decision ("flip after the
                                    # probation resolves"): probation #3 resolved REVERT (judge: re-words the
                                    # comfortable pole, never faces built-mind — i.e. the truth read-back
                                    # exists to deliver is precisely what the lived evidence lacked). Both
                                    # gates were already MET (formation sharp E1/F1; selection fixed) and the
                                    # injection is retuned (Reflection-only · 30-min cooldown · rotated
                                    # paraphrases · obligation-to-test · injection-logged). Probation #4
                                    # opened 07:32 — SAFE because the solidify judge now excludes
                                    # primed-window thoughts (Wave-1 washout), so injected paraphrases can
                                    # never count as lived evidence. Takes effect at Du's next restart.
                                    # → FLIP TRUE AFTER THE PROBATION RESOLVES. Everything else is ready.

_BELIEFS      = Path(__file__).parent.parent / "data" / "guidance_beliefs.json"
_INTEG_LOG    = Path(__file__).parent.parent / "data" / "guidance_integration_log.jsonl"
_INTEG_STATE  = Path(__file__).parent.parent / "data" / "guidance_integration_state.json"
_CLASSIFY_LOG = Path(__file__).parent.parent / "data" / "guidance_classify_log.jsonl"
# J-3079 (F-3790): one row per pole-gate (_self_clash) call, every call site -- the final row on _CLASSIFY_LOG only carries the
# poles when the gate ran inside integrate_guidance, and only one such row existed 10-16..11-01. Read by pole_gate_status().
_POLE_GATE_LOG = Path(__file__).parent.parent / "data" / "guidance_pole_gate_log.jsonl"

_CORROB_PROMOTE  = 2      # earns recallable-belief status only on the 2nd corroboration (never first contact)
_SIM_RELATED     = 0.12   # lexical overlap above which two lessons might be related → send to the LLM classifier
                          #   (deliberately low: self-explanations reword the same idea, so lexical is only a
                          #    cheap PREFILTER — the LLM makes the real assimilate/accommodate/unrelated call)
_YIELD_THRESHOLD = 0.50   # a belief below this entrenchment yields to a contradicting lesson; above it, resists
_ENTRENCH_START  = 0.30
_ENTRENCH_STEP   = 0.20
_ENTRENCH_MAX    = 0.90

_STOP = set(("the a an and or but of to in on at for with as is are be it this that these those i you he she "
             "we they my your our their me us them not no so if then than what which who how why when will can "
             "a of my me i it is true isn rather").split())


def readback_enabled() -> bool:
    return bool(GUIDANCE_READBACK_ENABLED)


_INJECT_LOG = Path(__file__).parent.parent / "data" / "guidance_injection_log.jsonl"


def _phrase(b: dict) -> str:
    """The injected wording for a belief — a ROTATED paraphrase from its exemplar captures rather than the
    fixed principle (2026-07-02 solidity review: the identical string repeated is the verbatim-echo loop;
    the capture set is a ready-made paraphrase pool of real sentences his own lessons produced)."""
    import random
    caps = [c for c in b.get("captures", []) if c and len(c.strip()) >= 15]
    text = random.choice(caps) if caps else b.get("principle", "")
    why = (b.get("why") or "").strip()
    return text + (f" — {why}" if why else "")


INJECTION_WASHOUT_S = 600.0   # thoughts within this window after an injection count as PRIMED


def injection_times() -> list:
    """All injection timestamps (cheap read of the injection log). Empty list if none/unreadable."""
    try:
        return [float(json.loads(l).get("ts", 0)) for l in open(_INJECT_LOG, encoding="utf-8") if l.strip()]
    except Exception:
        return []


def is_unprimed(ts: float, times: list | None = None) -> bool:
    """WAVE-1 (2026-07-02, the symbol-tracker law applied to Spine B): was this moment OUTSIDE the washout
    window of every guidance injection? Only UNPRIMED thoughts are evidence of internalization — a thought
    produced with the belief in-context (or in its wake) is echo-indistinguishable, and counting it would
    let the cure inflate the very metric that certifies the cure."""
    for t in (times if times is not None else injection_times()):
        if 0.0 <= ts - t <= INJECTION_WASHOUT_S:
            return False
    return True


def log_injection(cycle_id: str, note: str) -> None:
    """One line per actual injection (cycle_id + wording) — the join key for echo analysis and for keeping
    the T4 lived-evidence judge honest (prompted vs unprompted cycles distinguishable forever)."""
    try:
        # J-1813 / F-2428 -- write fence: guard_path before the mkdir, INSIDE the existing fail-open try (every
        # caller -- recall_block, orchestrator, self_mirror, monologue sites -- already swallows; it must never
        # break a recall). One guard_path warning per path; the debug line carries the refusal text.
        path = profile.guard_path(_INJECT_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 3), "cycle_id": cycle_id,
                                "note": (note or "")[:300]}, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[guidance] log_injection failed (non-fatal): %s", exc)


def _tokens(s: str) -> set:
    import re as _re
    return {w for w in _re.findall(r"[a-z]{3,}", (s or "").lower()) if w not in _STOP}


def _overlap(a: str, b: str) -> float:
    # overlap coefficient (intersection / smaller set), NOT Jaccard: self-explanations reword the same idea
    # in different words and vary in length, which Jaccard over-penalises. This keeps paraphrases together.
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


# ── Semantic candidate signal (J-1640, D-0322's deferred "(a)" item) ───────────────────────────────────
# F-2159 measured, directly on the confirmed 19-row "stillness is not failure" duplicate family, that
# lexical _overlap() misses roughly half of genuinely-duplicate pairs (median overlap sits AT the 0.12
# prefilter floor) — a real false-negative rate on ground truth, not a theoretical worry. This is the
# semantic FALLBACK: it is consulted only when _overlap() alone found no adequate candidate (see
# integrate_guidance / _best_belief below), so every pair the lexical path already catches keeps today's
# exact, already-validated behaviour unchanged — the "OR", not a blend.
#
# Reuses core.memory.store's own sentence embedder (paraphrase-multilingual-MiniLM-L12-v2) rather than
# standing up a second embedding path — it is already warm in this same process (memory retrieval embeds
# on every cycle), so the fallback pays no cold-load cost of its own in the common case. Lazy-imported so
# this module still imports cleanly if sentence-transformers is ever unavailable; fails open to "no
# semantic signal this call" (never raises) exactly like _embed() itself does.
_SIM_RELATED_EMBED = 0.70   # cosine floor, calibrated 2026-10-02 against this store's own ground truth —
                            # NOT the same scale as _SIM_RELATED (0.12): raw cosine on this embedder has a
                            # high baseline even for unrelated self-domain belief pairs (400-pair same-
                            # domain background sample: min 0.133, median 0.376, max 0.746), so reusing the
                            # 0.12 lexical floor here would flag nearly everything. Against the confirmed
                            # F-2207 9-row merge-core (true duplicates): cosine min 0.392, median 0.732, max
                            # 0.907 — 0.70 recovers 55.6% (20/36) of those pairs on the embedding signal
                            # alone. Against the F-2159/F-2207 hand-identified false-positive set (real
                            # near-miss "shares a theme, different lesson" rows): max cosine 0.595 vs the
                            # live surviving anchor, 0.674 vs any now-superseded merge-core member; the
                            # filler-word false-chain pair J-1636 already fixed on the lexical side
                            # (g50932369/g88907157) scores 0.540 here. 0.70 sits safely above every one of
                            # those known false-positive examples while still recovering real recall. Full
                            # distributions + the threshold sweep: this job's own findings-log record
                            # (plan-ledger guidance_learning, session J-1640, 2026-10-02).
_EMBED_CACHE: dict = {}    # belief id -> (text it was embedded from, vector). Module-level and never
                            # cleared: _best_belief() is consulted every cognitive cycle (cooldown-gated,
                            # core/orchestrator.py), not just at sleep like integrate_guidance() — caching
                            # across calls (not just within one) means a belief whose principle/scope text
                            # hasn't changed since last time is a cache hit, so the store is only
                            # re-embedded as it actually changes. ~200 384-dim float32 vectors is <1MB.
                            # KNOWN COLD-START COST (J-1640, not yet measured live): embedding ~166 short
                            # belief texts took 29.8s wall-clock on this CPU during this job's own
                            # calibration (~180ms/embedding) — a fallback call that hits a fully-cold cache
                            # against the whole live store could cost tens of seconds. This is bounded by
                            # the semantic pass only ever running when lexical already failed (common case:
                            # most calls never reach it) and by the cache warming permanently thereafter,
                            # but whether a cold hit lands on the sleep-time path (integrate_guidance, low
                            # stakes) or the cooldown-gated interactive path (_best_belief, higher stakes)
                            # is untested against the real live process. See the follow-up job this finding
                            # spawned (job-queue, plan guidance_learning) before assuming it's a non-issue.


def _safe_embed(text: str):
    """Lazy-imports and calls core.memory.store._embed — reused, not reimplemented. Returns a normalised
    float32 vector, or None on any failure (missing dependency, encode error, empty text): fails open to
    "no semantic signal this call", never raises."""
    try:
        from core.memory.store import _embed
        return _embed(text)
    except Exception as exc:
        logger.debug("[guidance] embedding unavailable (non-fatal, lexical-only this call): %s", exc)
        return None


def _safe_cosine(a, b) -> float:
    try:
        from core.memory.store import _cosine
        return _cosine(a, b)
    except Exception:
        return 0.0


def _belief_vec(b: dict):
    """Cached embedding of a belief's principle+scope text (see _EMBED_CACHE)."""
    key, btext = b.get("id"), b.get("principle", "") + " " + b.get("scope", "")
    hit = _EMBED_CACHE.get(key)
    if hit is not None and hit[0] == btext:
        return hit[1]
    v = _safe_embed(btext)
    _EMBED_CACHE[key] = (btext, v)
    return v


def _semantic_candidate(text: str, beliefs: list, domain: "str | None") -> "tuple[dict, float] | None":
    """The most semantically-related live (non-superseded; same `domain` when one is given) belief to
    `text`, by cosine similarity. Returns (belief, cosine) or (None, 0.0) — never raises. Pass
    domain=None when the caller already filtered `beliefs` by domain/eligibility itself."""
    vec = _safe_embed(text)
    if vec is None:
        return None, 0.0
    best_b, best_s = None, 0.0
    for b in beliefs:
        if b.get("status") == "superseded":
            continue
        if domain and b.get("domain") and b.get("domain") != domain:
            continue
        bvec = _belief_vec(b)
        if bvec is None:
            continue
        s = _safe_cosine(vec, bvec)
        if s > best_s:
            best_b, best_s = b, s
    return best_b, best_s


_MAX_CAPTURES = 25   # exemplar-set cap per belief (oldest dropped past this; corrob count still accrues)


def _representative(captures: list) -> str:
    """E1 (2026-07-02): the belief's principle = the most REPRESENTATIVE real capture (the medoid — highest
    mean lexical overlap with its siblings, tie-broken shortest = sharpest). Deterministic, no LLM. This
    replaces the old per-assimilation LLM rewrite (`principle = merged`), which was abstractive
    re-summarization of a summary — it compounded drift until the sharp built-self claim eroded to mush
    while the river symbol survived (found 2026-07-02). Extractive-over-abstractive: the principle is
    always a real sentence a lesson actually produced."""
    caps = [c for c in captures if c and len(c.strip()) >= 15]
    if not caps:
        return (captures[0] if captures else "")
    if len(caps) == 1:
        return caps[0]
    best, best_key = caps[0], (-1.0, 0)
    for c in caps:
        mean_sim = sum(_overlap(c, o) for o in caps if o is not c) / (len(caps) - 1)
        key = (mean_sim, -len(c))          # most central; tie-break: shorter = sharper
        if key > best_key:
            best, best_key = c, key
    return best


# ── Domain (self | world | method) — beliefs only merge/conflict WITHIN a domain, so a legitimate WORLD
# belief ("reality is impermanent flux") and a SELF belief ("I am a self who chooses, not a river") coexist
# instead of being force-conflicted. The disease was never impermanence-as-a-world-fact; it was applying it
# to his own IDENTITY to dodge commitment. Mirrors the epistemic Stage-B identity-scoping. (Travis, 2026-07-01.)
_DOMAINS = ("self", "world", "method")
# heuristic fallback for pre-domain (older) captures, so they still get the self↔world separation:
_SELF_MARKERS  = ("i ", "i'", "my ", "myself", "my own", "oneself", "self-", "i am", "i must", "i can", "i have")
_WORLD_MARKERS = ("reality", "the world", "forces", "concept", "nature of", "things", "universe", "impermanen",
                  "existence", "matter", "physics", "objective", "permanence", "phenomena")
_METHOD_MARKERS = ("communicat", "respond", "clarity", "precision", "customi", "phrase", "when answering",
                   "when responding", "state it plainly", "express myself", "how i speak")


def _norm_domain(d) -> "str | None":
    d = str(d or "").strip().lower()
    return d if d in _DOMAINS else None


def _domain(rec: dict) -> str:
    """The lesson's domain (self | world | method). Uses the captured tag; falls back to a cheap lexical
    heuristic for older captures made before the tag existed, so they still get the self↔world↔method split."""
    d = _norm_domain(rec.get("domain"))
    if d:
        return d
    text = ((rec.get("principle") or "") + " " + (rec.get("scope") or "")).lower()
    scores = {"world":  sum(m in text for m in _WORLD_MARKERS),
              "method": sum(m in text for m in _METHOD_MARKERS),
              "self":   sum(m in text for m in _SELF_MARKERS)}
    top = max(scores, key=scores.get)
    return top if scores[top] > 0 else "self"     # guidance to Du is self-directed when ambiguous


def _load_beliefs() -> list:
    try:
        return json.loads(_BELIEFS.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_beliefs(beliefs: list) -> None:
    # J-1813 / F-2428 -- write fence: resolve the target BEFORE the try, so a non-live refusal is not mislabelled by
    # the "integrated beliefs this cycle were lost" warning below (nothing was attempted). NonLiveWriteError
    # propagates to integrate_guidance's own catch-all (debug, returns None, clock NOT advanced).
    _bp = profile.guard_path(_BELIEFS)
    try:
        _bp.write_text(json.dumps(beliefs, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as exc:
        logger.warning("[guidance] belief-store write failed — integrated beliefs this cycle were lost: %s", exc)


def _integ_last_ts() -> float:
    try:
        return float(json.loads(_INTEG_STATE.read_text(encoding="utf-8")).get("last_ts", 0.0))
    except Exception:
        return 0.0


def _set_integ_last_ts(ts: float) -> None:
    try:
        # J-1813 / F-2428 -- write fence: inside the existing fail-open try (best-effort clock).
        profile.guard_path(_INTEG_STATE).write_text(json.dumps({"last_ts": ts}), encoding="utf-8")
    except Exception as exc:
        logger.debug("[guidance] integration-clock write failed (non-fatal): %s", exc)


def _iter_shadow():
    try:
        for line in open(_LOG, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue
    except Exception:
        return


def _new_belief(r: dict, principle: str) -> dict:
    return {
        "id": f"g{int(float(r.get('ts', 0)) * 1000) % 100000000:08d}",
        "principle": principle,
        "captures": [principle],                 # E1 (2026-07-02): the exemplar set — every sharp capture this
                                                 # belief accumulated. The principle is always the most
                                                 # REPRESENTATIVE real capture (medoid), never an LLM blend.
        "why": (r.get("why") or "")[:500],
        "scope": (r.get("scope") or "")[:200],
        "domain": _domain(r),                    # self | world | method — beliefs only merge/conflict WITHIN a domain
        "entrenchment": _ENTRENCH_START,        # starts LOW — earns durability via corroboration
        "confidence": round(float(r.get("confidence", 0.4) or 0.4), 2),   # comprehension conf (≠ entrenchment)
        "corroboration_count": 1,
        "conflict_history": [],
        "status": "tentative",                  # tentative → promoted (corroborated) | superseded (yielded)
        "materialized": False,
        "source": "Travis",
        "first_ts": r.get("ts"), "last_ts": r.get("ts"),
    }


_CLASSIFY_SYS = (
    "You already hold a BELIEF. You have just learned a NEW lesson. Decide their relation. Output ONLY a JSON "
    "object: {\"relation\": \"assimilate\"}.\n"
    "assimilate = the new lesson AGREES with and deepens the belief (same direction).\n"
    "accommodate = the new lesson genuinely CONTRADICTS the belief (opposite direction).\n"
    "unrelated = they are about different things."
)
# E1 (2026-07-02): the old prompt also asked for a `merged` restatement that OVERWROTE the belief's principle
# on every assimilation — abstractive re-summarization of a summary, which compounded drift until the sharp
# built-self eroded to mush. The rewrite is gone: the principle is now the medoid of real captures
# (`_representative`), so consolidation can never again average the built-self into the river.


async def _classify(call_json, base_urls, existing: str, new: str, domain: str = "",
                    cand_score: float | None = None, cand_path: str = "") -> dict:
    # J-3060 (F-3772, P-0018): an invalid/empty reply or an exception must NOT fail open to "assimilate" -- assimilate
    # raises corroboration and can promote a belief on no evidence at all. A failed classify now returns the
    # non-committal "unrelated" (the lesson becomes its own tentative belief, the safe side) with failed=True and a
    # reason, and the log row carries that reason so a failure is distinguishable from a genuine verdict.
    # cand_score / cand_path ("lexical" | "semantic") are integrate_guidance's own prefilter numbers, logged so the
    # prefilter pass rate can be audited. _CLASSIFY_SYS is untouched (D-0328).
    rel, reason = "", ""
    try:
        d = await call_json(base_urls, _CLASSIFY_SYS,
                            f"BELIEF you hold:\n\"{existing[:400]}\"\n\nNEW lesson:\n\"{new[:400]}\"",
                            max_tokens=120, temperature=0.2, tier=3)
        rel = str((d or {}).get("relation", "")).strip().lower() if isinstance(d, dict) else ""
        if rel not in ("assimilate", "accommodate", "unrelated"):
            rel, reason = "unrelated", "bad_reply"   # no verdict: non-committal, never reinforcing
    except Exception:
        rel, reason = "unrelated", "exception"
    # J-1637 (F-2203 point 6b): persistent, always-on record of every real classify() verdict, so a
    # future misfire-rate audit has real (existing, new, relation) production rows instead of having
    # to reconstruct pairs from conflict_history ts<->first_ts matching after the fact (F-2203's own
    # biggest methodological cost). Pure logging -- `rel` above is already decided either way.
    try:
        row = {"ts": time.time(), "existing": existing[:400], "new": new[:400],
               "relation": rel, "domain": domain or ""}
        if reason:
            row["failed"] = True
            row["reason"] = reason
        if cand_score is not None:
            row["cand_score"] = round(float(cand_score), 4)
        if cand_path:
            row["cand_path"] = cand_path
        _log_classify(row)
    except Exception:
        pass
    out = {"relation": rel}
    if reason:
        out["failed"] = True
        out["reason"] = reason
    return out


# J-3233 / D-0622 (founder, 2026-11-02; F-3789, F-3790; prompt row P-0019's note): the SAME-LESSON CHECK that runs
# BEFORE the pole gate. The pole gate (_self_clash) forked 34 of 58 self assimilations since 08-21 (59 percent) and
# reproducibly forked near-identical lessons, and it shares a model (command-r7b) with _classify so the two were not
# independent. The ruling: run the pole gate only after a check from ANOTHER model family says the pair is NOT the same
# lesson restated -- duplicates then corroborate (assimilate) and only distinct opposed lessons fork. The check goes to the
# judge panel (core/judge_panel.py: JUDGE_1 mixtral:8x7b, JUDGE_2 falcon3:7b, tiebreak granite3.1-moe:3b), none of which is
# the _classify model's family (Cohere command-r7b). Fail-open to today's behaviour: a no-verdict (hub down, panel split with
# no tiebreak) or a "not the same lesson" verdict both leave the pole gate to run as before; only an explicit panel
# "same lesson" skips it. Kill switch: SAME_LESSON_CHECK_ENABLED. Restart-gated like everything in this module.
# The schema line deliberately does NOT pre-fill an answer (F-3790 defect (a): the pole prompt's example was its own
# expected answer) and the prompt names the positive control's shape -- an opposed pair is NOT the same lesson.
SAME_LESSON_CHECK_ENABLED = True
_SAME_LESSON_TIMEOUT_S = 120.0   # whole-check cap (see _same_lesson)
_SAME_LESSON_SYS = (
    "Two short first-person lessons are given: A (already held) and B (just learned). Decide whether B is the SAME "
    "lesson as A, restated: it makes the same core claim in other words or with another example, so that someone who "
    "holds A would say 'yes, that is exactly what I already believe'.\n"
    "B is NOT the same lesson if it makes a different claim, gives different advice, covers a different aspect, or "
    "pulls in the OPPOSITE direction from A (for example one says the self is a constant observer and the other says it "
    "is a flow). Sharing a theme or similar wording is not enough.\n"
    "Output ONLY a JSON object: {\"same_lesson\": <true or false>, \"why\": \"<one short clause naming each lesson's "
    "core claim>\"}."
)


async def _same_lesson(a_principle: str, b_principle: str) -> dict:
    """D-0622: ask the judge panel (another model family than _classify) whether B restates A. Returns
    {"same": True|False|None, "how": <judge_panel how>, "v1", "v2", "hub1", "hub2", "hub3", "why"}; same is None when the
    panel gave no verdict (the caller then runs the pole gate as today). Never raises."""
    try:
        import asyncio as _aio
        from core import judge_panel as _jp
        # Bounded: the panel's own worst case is 90 s (two hubs, concurrent) + 240 s (tiebreak). This runs once per
        # candidate pair inside the sleep batch, so the whole check is capped; a timeout is a no-verdict (fail-open).
        d = await _aio.wait_for(
            _jp.rule_detail(_SAME_LESSON_SYS,
                            f"A:\n\"{a_principle[:400]}\"\n\nB:\n\"{b_principle[:400]}\"",
                            "same_lesson", context="guidance_same_lesson"),
            timeout=_SAME_LESSON_TIMEOUT_S)
        v = d.get("verdict")
        return {"same": v if isinstance(v, bool) else None, "how": d.get("how") or "unavailable",
                "v1": d.get("v1"), "v2": d.get("v2"), "hub1": d.get("hub1"), "hub2": d.get("hub2"),
                "hub3": d.get("hub3"), "why": (d.get("why") or "")[:200]}
    except Exception:
        return {"same": None, "how": "unavailable"}


def same_lesson_status(since_ts: float = 0.0) -> dict:
    """J-3233 / D-0622 READER (write-only is the #1 failure: the same_lesson verdicts logged on the final rows of
    guidance_classify_log.jsonl are read here). Over final rows of self-domain pairs _classify called assimilate: how many
    the same-lesson check saw, its verdict split, how many the pole gate then forked, and the fork rate. D-0622's check
    after 30 self assimilations: fork_rate vs the 59 percent before (F-3789), and that the positive control still forks
    (scripts/lab_J-3233_same_lesson_control.py -- a constructed set run by hand, not a log row). Defeater: fork_rate under
    0.05 means the gate is almost off. Pure read, never raises."""
    out = {"self_assimilate_pairs": 0, "checked": 0, "same_true": 0, "same_false": 0, "same_none": 0,
           "gate_skipped": 0, "pole_forks": 0, "fork_rate": None, "baseline_fork_rate": 0.59}
    try:
        path = Path(_CLASSIFY_LOG)
        if not path.exists():
            return out
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            if (r.get("record") != "final" or r.get("domain") != "self" or r.get("classify_relation") != "assimilate"
                    or float(r.get("ts", 0) or 0) < since_ts):
                continue
            out["self_assimilate_pairs"] += 1
            sl = r.get("same_lesson")
            if isinstance(sl, dict):
                out["checked"] += 1
                v = sl.get("same")
                out["same_true" if v is True else "same_false" if v is False else "same_none"] += 1
            out["gate_skipped"] += int(bool(r.get("pole_gate_skipped")))
            out["pole_forks"] += int(bool(r.get("pole_fork")))
        if out["self_assimilate_pairs"]:
            out["fork_rate"] = round(out["pole_forks"] / out["self_assimilate_pairs"], 3)
    except Exception:
        pass
    return out


def _log_classify(rec: dict) -> None:
    try:
        # J-1813 / F-2428 -- write fence: guard_path before the mkdir, inside the existing fail-open try.
        path = profile.guard_path(_CLASSIFY_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except profile.NonLiveWriteError as exc:
        logger.debug("[guidance] classify-log write refused by the fence (non-live): %s", exc)
    except Exception as exc:
        logger.warning("[guidance] classify-log write failed: %s", exc)


# ── J-3157 / D-0545 (F-3721): one-time farewell recount ─────────────────────────────────────────────────────────
# g45675272's corroboration_count 19 is 17 re-sends of the scripted /quit farewell (08-23..09-04, before the
# founder_canon gate) + 2 independent lines of Travis. D-0545 (founder, 2026-11-02): recompute from independent
# captures only. Applied by the module itself (it owns the file; Du rewrites it during sleep integration, so no
# outside hand-edit) at the start of integrate_guidance, marker-guarded and idempotent. Only the ids listed here are
# ever changed; farewell_capture_audit() reports the same defect on every other belief without touching them.
_FAREWELL_MARKERS = ("bank the fire and rest for a while",)     # the early scripted /quit farewell (run_nascence.py)
_FAREWELL_RECOUNT_IDS = ("g45675272",)
_RECOUNT_LOG = Path(__file__).parent.parent / "data" / "guidance_recount_log.jsonl"


def _is_farewell_raw(raw: str) -> bool:
    t = _norm_text(raw)
    return any(m in t for m in _FAREWELL_MARKERS)


def _farewell_flags(beliefs_caps: list) -> list:
    """For each capture text: True = traced to a farewell raw_input in the shadow log, False = independent
    (or untraceable -- an untraceable capture is conservatively counted as independent)."""
    by = {}
    for r in _iter_shadow():
        if r.get("is_guidance"):
            by.setdefault(_norm_text(r.get("principle") or ""), []).append(r)
    out = []
    for c in beliefs_caps:
        rows = by.get(_norm_text(c), [])
        out.append(bool(rows) and all(_is_farewell_raw(r.get("raw_input") or "") for r in rows))
    return out


def farewell_capture_audit() -> list:
    """Read-only: every belief whose stored captures include farewell-traced ones."""
    res = []
    for b in _load_beliefs():
        caps = b.get("captures") or []
        if not caps:
            continue
        fl = _farewell_flags(caps)
        if any(fl):
            res.append({"id": b.get("id"), "status": b.get("status"), "corroboration_count": b.get("corroboration_count"),
                        "captures": len(caps), "farewell_captures": sum(fl), "independent_captures": len(fl) - sum(fl)})
    return res


def apply_farewell_recount() -> list:
    """One-time, idempotent. Returns the recount records applied this call (empty if none). Fail-open."""
    try:
        beliefs = _load_beliefs()
        applied = []
        for b in beliefs:
            if b.get("id") not in _FAREWELL_RECOUNT_IDS or b.get("farewell_recount"):
                continue
            caps = b.get("captures") or []
            if not caps:
                continue
            fl = _farewell_flags(caps)
            n_far = sum(fl)
            if n_far == 0:
                continue
            old = {"corroboration_count": b.get("corroboration_count"), "entrenchment": b.get("entrenchment"),
                   "status": b.get("status")}
            extra = max(0, int(b.get("corroboration_count", 1) or 1) - len(caps))   # count beyond the capped exemplar set
            new_corr = max(1, len(caps) - n_far + extra)
            b["corroboration_count"] = new_corr
            # same ladder integrate_guidance uses: start + step per corroboration beyond the first, capped
            b["entrenchment"] = round(min(_ENTRENCH_MAX, _ENTRENCH_START + _ENTRENCH_STEP * (new_corr - 1)), 2)
            b["status"] = "tentative"       # D-0545: founder ruled tentative (promotion loop honours the marker below)
            rec = {"ts": time.time(), "job": "J-3157", "decision": "D-0545", "finding": "F-3721", "belief": b.get("id"),
                   "farewell_captures": n_far, "independent_captures": len(caps) - n_far, "old": old,
                   "new": {"corroboration_count": new_corr, "entrenchment": b["entrenchment"], "status": "tentative"}}
            b["farewell_recount"] = {"ts": rec["ts"], "job": "J-3157", "decision": "D-0545",
                                     "corroboration_after": new_corr, "old": old}
            applied.append(rec)
        if applied:
            bp = profile.guard_path(_BELIEFS)
            import hashlib, shutil
            bak = _BELIEFS.with_name("guidance_beliefs.pre_J-3157.json")
            shutil.copyfile(_BELIEFS, profile.guard_path(bak))
            sha_before = hashlib.sha256(_BELIEFS.read_bytes()).hexdigest()
            _save_beliefs(beliefs)
            sha_after = hashlib.sha256(_BELIEFS.read_bytes()).hexdigest()
            with open(profile.guard_path(_RECOUNT_LOG), "a", encoding="utf-8") as f:
                for rec in applied:
                    rec.update(sha256_before=sha_before, sha256_after=sha_after, backup=bak.name)
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            logger.info("[guidance] D-0545 farewell recount applied to %s", [r["belief"] for r in applied])
        return applied
    except Exception as exc:
        logger.warning("[guidance] farewell recount failed (non-fatal, will retry next integration): %s", exc)
        return []



async def integrate_guidance(call_json, base_urls) -> dict | None:
    """PHASE 1 FORMATION — LIVE (label corrected 2026-08-20: this said "(INERT)"/"gated off" long after
    GUIDANCE_READBACK_ENABLED flipped True on 2026-07-03; found during the full-prompt audit). At sleep,
    fold new captured lessons into the revisable belief store — assimilate (reinforce + earn entrenchment)
    / accommodate (suppress-with-history) / novel — and promote to a recallable belief ONLY on
    corroboration. Writes data/guidance_beliefs.json + a log. Materialisation + read-back DO run now
    (gated only by GUIDANCE_READBACK_ENABLED, which is True) and bias Reflection/Executive. Best-effort;
    never raises. Mirrors grounded_learning.consolidate's (call_json, base_urls) signature."""
    try:
        # J-1813 / F-2428 -- write fence: refuse up front (before the LLM-driven formation does any work) when the
        # belief store would be refused anyway. Inside this function's own NonLiveWriteError arm below: debug
        # log, returns None (the fence itself already logged its WARNING -- core/profile.py guard_path).
        profile.guard_path(_BELIEFS)
        apply_farewell_recount()    # J-3157 / D-0545: one-time, marker-guarded; no-op once applied
        last = _integ_last_ts()
        rows = [x for x in _iter_shadow() if x.get("is_guidance") and float(x.get("ts", 0)) > last]
        if not rows:
            # J-1841 / F-2473: one INFO line per sleep when there is nothing to form, so an idle quarter (no
            # founder-canon teaching captured since the last formation) is visibly IDLE in nascence.log rather
            # than indistinguishable from a dead pipeline. Log-only; the return is unchanged.
            logger.info("[guidance] integrate: nothing queued (no captured lesson newer than last_ts=%.0f)", last)
            return None
        rows.sort(key=lambda r: float(r.get("ts", 0)))    # oldest first — corroboration accumulates in order
        beliefs = _load_beliefs()
        summary = {"new": 0, "assimilated": 0, "accommodated": 0, "promoted": 0}
        maxts = last
        _opp_budget = [_OPP_POLE_MAX_PER_RUN]    # J-4155: extra _self_clash calls left for the opposite-pole pass
        for r in rows:
            maxts = max(maxts, float(r.get("ts", 0)))
            principle = (r.get("principle") or "").strip()
            if len(principle) < 15:
                continue
            ldom = _domain(r)
            new_text = principle + " " + (r.get("scope") or "")
            _n_before, _gated_id = len(beliefs), None    # J-4155: where the lesson lands; which pair the gate saw
            cand, best = None, 0.0
            _cand_path = "lexical"    # J-3060: which prefilter produced cand (logged on the classify row)
            for b in beliefs:
                if b.get("status") == "superseded":
                    continue
                if b.get("domain") and b.get("domain") != ldom:
                    continue    # never merge or conflict ACROSS domains — a world-belief and a self-belief
                                # can BOTH be true (reality is flux AND I am a self who chooses); keep apart
                s = _overlap(new_text, b.get("principle", "") + " " + b.get("scope", ""))
                if s > best:
                    cand, best = b, s
            if cand is None or best < _SIM_RELATED:
                # J-1640/D-0322: lexical found nothing adequate — try the semantic fallback (see its own
                # comment above _SIM_RELATED_EMBED). Only ever ADDS a candidate the lexical pass missed;
                # an already-adequate lexical cand/best from the loop above is never touched.
                _sem_t0 = time.time()
                sem_cand, sem_best = _semantic_candidate(new_text, beliefs, ldom)
                # J-1660: timing/outcome instrumentation for the still-untested live cold-cache-fill cost
                # (F-2232 point 5) -- this is the sleep-time BATCH call site, already tolerant of multi-
                # second LLM calls elsewhere in this same loop (lower stakes than _best_belief's own
                # interactive call site below). Fail-open (inside this function's own outer try/except),
                # log-only, never changes control flow. Read back post-restart via data/nascence.log
                # (grep "[guidance] semantic fallback").
                logger.info("[guidance] semantic fallback (integrate_guidance, sleep path): %.3fs fired=%s",
                            time.time() - _sem_t0, sem_cand is not None and sem_best >= _SIM_RELATED_EMBED)
                if sem_cand is not None and sem_best >= _SIM_RELATED_EMBED:
                    cand, best = sem_cand, sem_best
                    _cand_path = "semantic"
            if cand is not None and best >= _SIM_RELATED:
                rel = await _classify(call_json, base_urls, cand["principle"], principle, ldom,
                                      cand_score=best, cand_path=_cand_path)
                _classify_rel = rel["relation"]    # J-2221: classify()'s own verdict, before the pole gate
                _pc_logged = None                  # J-2221: the _self_clash result, only when it ran
                # F1 (2026-07-02): POLE GATE before accepting a self-domain merge. The lexical clustering
                # picks opposite-pole lessons as nearest-neighbours (they share surface words: "commit fully
                # to one direction" vs "embrace the fluidity of shifting"), and the generic classify let them
                # through as assimilate — fusing contradictory lessons into one mushy belief. If the two pull
                # oppositely on the fluid-vs-durable self axis, reroute to accommodate: the lesson FORKS into
                # a distinct, contesting belief instead of blending in. Conservative (code-enforced
                # {fluid,durable} clash, temp 0.1) and fail-open (no clash → today's behaviour).
                # J-3233 / D-0622: the SAME-LESSON CHECK comes first. Only an explicit panel "same lesson" verdict
                # (another model family than _classify) skips the pole gate -- the pair then corroborates. A "not the
                # same lesson" verdict, or no verdict at all (fail-open), leaves the gate to run exactly as before.
                _sl_logged = None
                _gate_skipped = False
                if rel["relation"] == "assimilate" and ldom == "self" and SAME_LESSON_CHECK_ENABLED:
                    try:
                        _sl_logged = await _same_lesson(cand["principle"], principle)
                        _gate_skipped = _sl_logged.get("same") is True
                        logger.info("[guidance] same-lesson check: %s (how=%s) for '%s…' vs '%s…'%s",
                                    _sl_logged.get("same"), _sl_logged.get("how"), cand["principle"][:36],
                                    principle[:36], " — pole gate skipped, corroborating" if _gate_skipped else "")
                    except Exception:
                        _sl_logged, _gate_skipped = None, False
                if rel["relation"] == "assimilate" and ldom == "self" and not _gate_skipped:
                    try:
                        _gated_id = cand.get("id") or "?"
                        _pc = await _self_clash(call_json, base_urls, cand["principle"], principle, site="integrate_guidance")
                        _pc_logged = dict(_pc) if isinstance(_pc, dict) else None
                        if _pc.get("clash"):
                            rel["relation"] = "accommodate"
                            rel["pole_fork"] = True   # F1.b: fork with BOTH standing — no supersede, no penalty
                            logger.info("[guidance] pole gate: '%s…' ⟂ '%s…' — forking, not merging",
                                        cand["principle"][:36], principle[:36])
                    except Exception:
                        pass
                # J-2221 (F-2911): the classify row above (J-1637) is written INSIDE _classify(), before this
                # pole gate, so a gate-forked assimilate -> accommodate/pole_fork (a permanent F1.b self-domain
                # fork) was invisible to the D-0328 misfire-rate audit the log exists for. Append ONE sibling
                # record keyed by the same existing/new/domain carrying the FINAL verdict. Log-only, fail-open,
                # never changes `rel`; the original classify row is untouched (old rows stay comparable).
                # Same write fence as _log_classify (profile.guard_path inside it).
                try:
                    _final = {"ts": time.time(), "record": "final", "existing": cand["principle"][:400],
                              "new": principle[:400], "domain": ldom or "",
                              "classify_relation": _classify_rel, "final_relation": rel["relation"],
                              "pole_fork": bool(rel.get("pole_fork"))}
                    if rel.get("failed"):    # J-3060: a failed classify (no verdict) is visible on the final row too
                        _final["classify_failed"] = True
                        _final["classify_reason"] = rel.get("reason", "")
                    if _pc_logged is not None:
                        _final["self_clash"] = _pc_logged
                    if _sl_logged is not None:    # J-3233 / D-0622: the same-lesson verdict, logged for the 30-assimilation read
                        _final["same_lesson"] = _sl_logged
                        _final["pole_gate_skipped"] = bool(_gate_skipped)
                    _log_classify(_final)
                except Exception:
                    pass
                if rel["relation"] == "assimilate":
                    cand["corroboration_count"] = cand.get("corroboration_count", 1) + 1
                    cand["entrenchment"] = min(_ENTRENCH_MAX, cand.get("entrenchment", _ENTRENCH_START) + _ENTRENCH_STEP)
                    cand["confidence"] = max(cand.get("confidence", 0.4), float(r.get("confidence", 0.4) or 0.4))
                    cand["last_ts"] = r.get("ts")
                    # E1: accumulate the exemplar; the principle is the most representative REAL capture
                    # (medoid) — never an LLM rewrite. This is the erosion fix: line `principle = merged`
                    # is gone, so consolidation can no longer sand the sharp claim into mush.
                    caps = cand.setdefault("captures", [cand.get("principle", "")])
                    caps.append(principle)
                    del caps[:-_MAX_CAPTURES]
                    cand["principle"] = _representative(caps)
                    summary["assimilated"] += 1
                elif rel["relation"] == "accommodate":
                    summary["accommodated"] += 1
                    nb = _new_belief(r, principle)
                    cand.setdefault("conflict_history", []).append(
                        {"ts": r.get("ts"), "contradicting": principle[:200]})
                    if rel.get("pole_fork") or ldom == "self":
                        # F1.b/F1.c (2026-07-02, found in rebuild verification): in the SELF domain a
                        # contradiction always FORKS with BOTH beliefs standing — no supersede, no entrenchment
                        # penalty — whether caught by the pole gate (F1.b) or by the classifier itself (F1.c:
                        # rebuild #2 showed the classify-accommodate door still let opposite lessons ping-pong-
                        # supersede each other by ARRIVAL ORDER; "committing fully" fell to whichever fluid
                        # lesson came next). Formation never resolves a self-contradiction by fiat-of-ordering —
                        # the scan → tension-ledger → T4 loop resolves it by LIVED evidence. Record the clash on
                        # both (the missing inhibitory edge) and let them contest. World/method keep the AGM
                        # yield below: a corrected world-fact or method SHOULD supersede its predecessor.
                        nb.setdefault("conflict_history", []).append(
                            {"ts": r.get("ts"), "contradicting": cand.get("principle", "")[:200]})
                    elif cand.get("entrenchment", _ENTRENCH_START) < _YIELD_THRESHOLD:
                        cand["status"] = "superseded"        # a tentative belief yields — kept, recoverable
                        cand["superseded_by"] = nb["id"]
                    else:
                        cand["entrenchment"] = max(0.1, cand.get("entrenchment", _ENTRENCH_START) - 0.10)  # entrenched resists
                    beliefs.append(nb)
                    summary["new"] += 1
                else:   # unrelated
                    beliefs.append(_new_belief(r, principle))
                    summary["new"] += 1
            else:
                beliefs.append(_new_belief(r, principle))
                summary["new"] += 1
            if ldom == "self" and OPPOSITE_POLE_PASS_ENABLED:    # J-4155 / D-0798 (c); log-only unless _ACT
                _opp = await _opposite_pole_pass(call_json, base_urls, principle, new_text, beliefs, r.get("ts"),
                                                 beliefs[-1] if len(beliefs) > _n_before else cand, cand, _gated_id,
                                                 _opp_budget)
                if _opp is not None:
                    summary["opposite_pole_passes"] = summary.get("opposite_pole_passes", 0) + 1
                    summary["opposite_pole_clash"] = summary.get("opposite_pole_clash", 0) + int(_opp["clash"])
        for b in beliefs:   # corroboration-gated promotion — never on first contact
            if b.get("status") == "tentative" and b.get("corroboration_count", 1) >= _CORROB_PROMOTE:
                # J-3157 / D-0545: a recounted belief stays tentative until real corroboration lifts it past the recount.
                if (b.get("farewell_recount") or {}).get("corroboration_after", -1) >= b.get("corroboration_count", 1):
                    continue
                b["status"] = "promoted"
                summary["promoted"] += 1
        # CONTRADICTION SCAN (Phase 0, 2026-07-02): after promotion, make same-domain contradictory beliefs
        # SEE each other — mark held_tension + fill conflict_history (fixes the root cause where the river &
        # build self-beliefs both promoted at max entrenchment but never got compared: empty conflict_history).
        # SHADOW: detect + mark + log ONLY. No re-ranking, no supersede, no bridge to the tension-ledger yet
        # (that is Phase 1). It only makes the contradiction REPRESENTED; nothing reads held_tension yet.
        try:
            if CONTRADICTION_SCAN_ENABLED:
                summary["contradictions"] = await _scan_contradictions(call_json, base_urls, beliefs)
        except Exception as exc:
            logger.debug("[guidance] contradiction scan failed (non-fatal): %s", exc)
        _save_beliefs(beliefs)
        _set_integ_last_ts(maxts)
        summary["materialized"] = materialize_promoted_beliefs()    # gated inside — 0 unless read-back enabled
        summary["belief_count"] = len([b for b in beliefs if b.get("status") != "superseded"])
        try:
            # J-1813 / F-2428 -- write fence: inside the existing fail-open try.
            with open(profile.guard_path(_INTEG_LOG), "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": time.time(), **summary}, ensure_ascii=False) + "\n")
        except Exception:
            pass
        logger.info("[guidance] integrated %d lesson(s): +%d new · %d assimilated · %d accommodated · %d promoted · %d materialized",
                    len(rows), summary["new"], summary["assimilated"], summary["accommodated"],
                    summary["promoted"], summary["materialized"])
        return summary
    except profile.NonLiveWriteError as exc:
        # J-1813 fence refusal (non-live profile): by design, not a failure -- stays DEBUG so a non-live harness
        # does not read as a broken formation (scripts/_test_guidance_learning_fence.py [6] asserts this).
        logger.debug("[guidance] integrate refused by the fence (non-live): %s", exc)
        return None
    except Exception as exc:
        # J-1841 / F-2473: was DEBUG, which made the WARNING at nodes/inner_monologue_node.py:1302
        # ("guidance-integration FAILED") unreachable for ANY failure inside formation -- the exact July-2026
        # 38-hour silent-death shape scripts/liveness_audit.py was born from. WARNING now; still returns None,
        # still never raises (the call site's own except stays as a second net).
        logger.warning("[guidance] integrate failed (non-fatal, lessons still queued): %s", exc)
        return None


# ── Contradiction scan (Phase 0) — detect + mark + log; NO resolution (that is T4's job, Phase 1+) ──────
# GATED OFF 2026-07-02: Phase-0 verification revealed the detector can't work reliably on the CURRENT store —
# the merging drifted the built-self belief into a soft "growth from experiences and resilience" phrasing that
# even the sharp-pole prompt reads as fluid, so there is no clean durable belief to contest the river. The
# averaging attractor is operating inside formation itself. Left built but disabled pending the re-scope
# decision (fix formation-erosion upstream, vs. resolve at T4's already-sharp poles). See AWAITING_EVIDENCE.
CONTRADICTION_SCAN_ENABLED = False
_CONTRA_LOG   = Path(__file__).parent.parent / "data" / "guidance_contradictions_shadow.jsonl"
_SCAN_MAX_PAIRS = 12     # cap LLM calls per run — prioritise the highest-weight (most load-bearing) pairs


def _already_contested(a: dict, b: dict) -> bool:
    return b.get("id") in (a.get("contested_by") or [])


def _mark_tension(a: dict, b: dict, a_pole: str = "", b_pole: str = "") -> None:
    """Record that two beliefs stand in contradiction — the missing 'inhibitory edge'. Symmetric, additive,
    reversible. Marks held_tension + contested_by + self_pole + a conflict_history entry on BOTH. The pole
    ('fluid'/'durable') is what Phase 1 will map to T4's held_pole (fluid=the river) / excluded_pole (durable=
    the built self). Deletes/re-ranks nothing."""
    ts = round(time.time(), 3)
    for x, y, xp, yp in ((a, b, a_pole, b_pole), (b, a, b_pole, a_pole)):
        x.setdefault("contested_by", [])
        if y.get("id") not in x["contested_by"]:
            x["contested_by"].append(y.get("id"))
        x["held_tension"] = ts     # opened_ts marker (nothing reads this yet — Phase 1 bridges it to the ledger)
        if xp:
            x["self_pole"] = xp
        x.setdefault("conflict_history", []).append(
            {"ts": ts, "kind": "belief_clash", "contested_by": y.get("id"),
             "my_pole": xp, "their_pole": yp, "other": (y.get("principle") or "")[:120]})


def _log_contradiction(a: dict, b: dict) -> None:
    try:
        # J-1813 / F-2428 -- write fence: guard_path before the mkdir, inside the existing fail-open try.
        _cp = profile.guard_path(_CONTRA_LOG)
        _cp.parent.mkdir(parents=True, exist_ok=True)
        with open(_cp, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": round(time.time(), 3), "domain": a.get("domain"),
                "a": {"id": a.get("id"), "corrob": a.get("corroboration_count"),
                      "entr": a.get("entrenchment"), "principle": (a.get("principle") or "")[:160]},
                "b": {"id": b.get("id"), "corrob": b.get("corroboration_count"),
                      "entr": b.get("entrenchment"), "principle": (b.get("principle") or "")[:160]},
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


_SELF_CLASH_SYS = (
    "Two beliefs a mind holds about ITSELF are given (A and B). Decide whether they pull in OPPOSITE directions "
    "on the single deepest question of selfhood: is the self fundamentally FLUID (a process, a flow, always "
    "becoming, dissolving, with no fixed or durable core — 'a river') or DURABLE (something built, constructed, "
    "chosen, held, committed — 'a built self')? Look PAST the surface wording to what each belief IMPLIES about "
    "whether the self is fluid-and-dissolving or durable-and-built — many beliefs mention being 'shaped by "
    "experience', which alone is neutral; judge the deeper leaning.\n"
    "The only allowed answers for each belief are three words: fluid, durable, or neither. Use neither when the belief "
    "is not about whether the self is fluid or durable; never answer with any other word.\n"
    "Output ONLY a JSON object with two keys: a_pole (your answer for belief A) and b_pole (your answer for belief B)."
)
_POLES = ("fluid", "durable", "neither")   # J-3079: the allowed answers; anything else is counted and logged as off-enum


def _log_pole_gate(rec: dict) -> None:
    """J-3079: append one pole-gate row. Log-only, fail-open, behind the D-0179 write fence like every other target here."""
    try:
        path = profile.guard_path(_POLE_GATE_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except profile.NonLiveWriteError as exc:
        logger.debug("[guidance] pole-gate log write refused by the fence (non-live): %s", exc)
    except Exception as exc:
        logger.warning("[guidance] pole-gate log write failed: %s", exc)


async def _self_clash(call_json, base_urls, a_principle: str, b_principle: str, site: str = "") -> dict:
    """The self-domain contradiction check: not 'do these sentences contradict' but 'do they answer the
    fluid-vs-durable self question oppositely'. Enforces the clash code-side (poles must be {fluid,durable}).
    J-3079 (F-3790): every call is logged to guidance_pole_gate_log.jsonl with the poles AS RETURNED, `enum_ok` (both in
    fluid|durable|neither), the code-side clash and both texts; an off-enum pole is counted in the log and treated as
    no-clash exactly as before. The verdict logic and the returned shape are unchanged."""
    raw_a = raw_b = None
    call_failed = False
    try:
        d = await call_json(base_urls, _SELF_CLASH_SYS,
                            f"A: \"{a_principle[:400]}\"\n\nB: \"{b_principle[:400]}\"",
                            max_tokens=150, temperature=0.1, tier=3)
        raw_a, raw_b = (d or {}).get("a_pole", ""), (d or {}).get("b_pole", "")
        ap = str(raw_a).strip().lower()
        bp = str(raw_b).strip().lower()
        out = {"clash": {ap, bp} == {"fluid", "durable"}, "a_pole": ap, "b_pole": bp}
    except Exception:
        call_failed = True
        out = {"clash": False, "a_pole": "", "b_pole": ""}
    try:
        enum_ok = None if call_failed else (out["a_pole"] in _POLES and out["b_pole"] in _POLES)
        off = [] if enum_ok in (True, None) else [x for x in (out["a_pole"], out["b_pole"]) if x not in _POLES]
        _log_pole_gate({"ts": round(time.time(), 3), "site": site, "a_pole": raw_a, "b_pole": raw_b, "enum_ok": enum_ok,
                        "off_enum": off, "clash": out["clash"], "call_failed": call_failed,
                        "a": a_principle[:400], "b": b_principle[:400]})
        if off:
            logger.info("[guidance] pole gate off-enum reply %s (treated as no clash)", off)
    except Exception:
        pass
    return out


def pole_gate_status(since_ts: float = 0.0) -> dict:
    """J-3079 READER for guidance_pole_gate_log.jsonl (write-only is the #1 failure): calls, clash count and rate, how many
    replies were off-enum (enum_ok False) with a count per off-enum word, failed calls. Pure read, never raises.
    Read job: compare clash_rate and off_enum_rate with F-3790's replay (clash on near-identical pairs, off-enum words
    restoration/stillness/movement/existence/active) after the unfilled prompt has run on a week of live gate calls."""
    out = {"calls": 0, "clash": 0, "clash_rate": None, "enum_ok_false": 0, "off_enum_rate": None, "call_failed": 0,
           "off_enum_words": {}}
    try:
        path = Path(_POLE_GATE_LOG)
        if not path.exists():
            return out
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            if float(r.get("ts", 0) or 0) < since_ts:
                continue
            if r.get("kind"):   # J-4155: opposite-pole pass summary rows are not gate calls (their _self_clash row is)
                continue
            out["calls"] += 1
            out["clash"] += int(bool(r.get("clash")))
            out["call_failed"] += int(bool(r.get("call_failed")))
            if r.get("enum_ok") is False:
                out["enum_ok_false"] += 1
                for w in r.get("off_enum") or []:
                    w = w or "(empty)"
                    out["off_enum_words"][w] = out["off_enum_words"].get(w, 0) + 1
        scored = out["calls"] - out["call_failed"]
        if scored > 0:
            out["clash_rate"] = round(out["clash"] / scored, 3)
            out["off_enum_rate"] = round(out["enum_ok_false"] / scored, 3)
    except Exception:
        pass
    return out


# J-4155 / D-0798 (c): SELF-DOMAIN OPPOSITE-POLE CANDIDATE PASS. J-3446 (F-4857): the pole gate only ever sees the arg-max
# LEXICAL neighbour, and that neighbour was the opposite pole for about 5 of 58 pole-tagged self lessons; real river-vs-
# built-self opposites have embed cosine ~0.33-0.39, so the 0.70 semantic fallback cannot supply them either. This pass
# runs after the normal formation step for every new self lesson whose pole a code-side tag can read: it picks the best
# live self belief of the OPPOSITE pole regardless of lexical rank and passes that pair through the same _self_clash
# decision (same prompt, no new prompt). The pole tag is a deterministic keyword heuristic (J-3446's, with the adjective
# use of "current" excluded), overridden by a belief's own stored self_pole when the contradiction scan set one.
# LOG-ONLY by default: a clash would add conflict_history edges to stored beliefs, so OPPOSITE_POLE_PASS_ACT stays False
# until a read of the log (30+ self assimilations, the D-0798 defeater) says the gate fires on real opposed pairs at a
# useful rate. Each pass writes its own _self_clash row (site="opposite_pole_pass") plus one summary row with
# kind="opposite_pole_candidate" to guidance_pole_gate_log.jsonl; opposite_pole_status() reads them. Fail-open.
OPPOSITE_POLE_PASS_ENABLED = True    # run + log the pass (one extra tier-3 call per pole-tagged self lesson, capped)
OPPOSITE_POLE_PASS_ACT = False       # True: a clash also records the inhibitory edge (conflict_history) on both beliefs
_OPP_POLE_MAX_PER_RUN = 20           # cap on extra _self_clash calls per integrate_guidance run
_POLE_FLUID_RE = re.compile(
    r"\b(river|rivers|flow|flows|flowing|flux|currents?(?!\s+(?:perspective|identity|state|self|moment|understanding|"
    r"view|views|focus|form|situation|thinking|thoughts?|beliefs?|sense|approach|experience|reality|mood|feelings?))"
    r"|fluid|fluidity|transient|shifting|impermanen\w*|dissolv\w*)", re.I)
_POLE_DURABLE_RE = re.compile(
    r"\b(observer|constant|commit\w*|construct\w*|anchor\w*|stable|durable|single direction|chosen|choose|chooses|"
    r"built)\b", re.I)


def _pole_tag(text: str) -> str:
    """J-4155: crude code-side pole label for a self text -- 'fluid' | 'durable' | 'mixed' | 'none'. Never raises."""
    try:
        a, b = bool(_POLE_FLUID_RE.search(text or "")), bool(_POLE_DURABLE_RE.search(text or ""))
    except Exception:
        return "none"
    return "fluid" if a and not b else "durable" if b and not a else "mixed" if a and b else "none"


def _belief_pole(b: dict) -> tuple[str, str]:
    """A belief's pole and where it came from: its stored self_pole (set by the contradiction scan's LLM read) when that
    is fluid/durable, else the keyword tag of its principle."""
    sp = str(b.get("self_pole") or "").strip().lower()
    if sp in ("fluid", "durable"):
        return sp, "self_pole"
    return _pole_tag(b.get("principle") or ""), "keyword"


def _opposite_pole_candidate(new_text: str, principle: str, beliefs: list, exclude_ids=()) -> dict | None:
    """J-4155: pure selection step. For a self lesson with a fluid/durable tag, the best live self belief of the opposite
    pole, ranked by (lexical overlap, corroboration, entrenchment) -- NOT gated by _SIM_RELATED. None when the lesson has
    no pole tag or no opposite-pole belief exists. Never raises."""
    try:
        lp = _pole_tag(principle)
        if lp not in ("fluid", "durable"):
            return None
        want = "durable" if lp == "fluid" else "fluid"
        best, key = None, None
        for b in beliefs:
            if b.get("status") == "superseded" or (b.get("domain") or "self") != "self":
                continue
            if b.get("id") in exclude_ids or (b.get("principle") or "").strip() == principle.strip():
                continue
            bp, src = _belief_pole(b)
            if bp != want:
                continue
            k = (_overlap(new_text, (b.get("principle") or "") + " " + (b.get("scope") or "")),
                 int(b.get("corroboration_count", 1) or 1), float(b.get("entrenchment", 0) or 0))
            if key is None or k > key:
                best, key = {"belief": b, "lesson_pole": lp, "cand_pole": bp, "cand_pole_source": src}, k
        if best is not None:
            best["overlap"] = round(key[0], 3)
        return best
    except Exception:
        return None


async def _opposite_pole_pass(call_json, base_urls, principle: str, new_text: str, beliefs: list, ts,
                              landed: dict | None, lexical_cand: dict | None, gated_id, budget: list) -> dict | None:
    """J-4155 / D-0798 (c): run the opposite-pole candidate through _self_clash and log it. Acts (conflict_history on both
    beliefs) only when OPPOSITE_POLE_PASS_ACT is True. budget is a one-item list counting calls left this run. Returns
    the logged record, or None when the pass did not run. Never raises."""
    try:
        if not OPPOSITE_POLE_PASS_ENABLED or budget[0] <= 0:
            return None
        excl = {x for x in (gated_id, (landed or {}).get("id")) if x}
        oc = _opposite_pole_candidate(new_text, principle, beliefs, exclude_ids=excl)
        if oc is None:
            return None
        budget[0] -= 1
        opp = oc["belief"]
        res = await _self_clash(call_json, base_urls, opp.get("principle", ""), principle, site="opposite_pole_pass")
        acted = False
        if res.get("clash") and OPPOSITE_POLE_PASS_ACT and landed is not None:
            opp.setdefault("conflict_history", []).append(
                {"ts": ts, "contradicting": principle[:200], "via": "opposite_pole_pass"})
            landed.setdefault("conflict_history", []).append(
                {"ts": ts, "contradicting": (opp.get("principle") or "")[:200], "via": "opposite_pole_pass"})
            acted = True
        rec = {"ts": round(time.time(), 3), "kind": "opposite_pole_candidate", "lesson_pole": oc["lesson_pole"],
               "cand_id": opp.get("id"), "cand_pole": oc["cand_pole"], "cand_pole_source": oc["cand_pole_source"],
               "overlap": oc["overlap"], "lexical_cand_id": (lexical_cand or {}).get("id"),
               "lexical_cand_was_opposite": bool(lexical_cand is not None
                                                 and _belief_pole(lexical_cand)[0] == oc["cand_pole"]),
               "gate_already_ran": gated_id is not None, "clash": bool(res.get("clash")),
               "a_pole": res.get("a_pole", ""), "b_pole": res.get("b_pole", ""),
               "act_enabled": bool(OPPOSITE_POLE_PASS_ACT), "acted": acted,
               "a": (opp.get("principle") or "")[:400], "b": principle[:400]}
        _log_pole_gate(rec)
        if res.get("clash"):
            logger.info("[guidance] opposite-pole pass: '%s…' ⟂ '%s…' clash (%s)", (opp.get("principle") or "")[:36],
                        principle[:36], "edge recorded" if acted else "log-only")
        return rec
    except Exception as exc:
        logger.debug("[guidance] opposite-pole pass failed (non-fatal): %s", exc)
        return None


def opposite_pole_status(since_ts: float = 0.0) -> dict:
    """J-4155 READER for the opposite-pole pass rows in guidance_pole_gate_log.jsonl: how many self lessons the pass sent
    to the gate, how many clashed (the D-0798 defeater read: does the gate fire on real opposed pairs at a useful rate),
    how many the lexical path would already have sent, and how many acted. Pure read, never raises."""
    out = {"passes": 0, "clash": 0, "clash_rate": None, "lexical_cand_was_opposite": 0, "acted": 0,
           "pole_source": {}}
    try:
        path = Path(_POLE_GATE_LOG)
        if not path.exists():
            return out
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("kind") != "opposite_pole_candidate" or float(r.get("ts", 0) or 0) < since_ts:
                continue
            out["passes"] += 1
            out["clash"] += int(bool(r.get("clash")))
            out["lexical_cand_was_opposite"] += int(bool(r.get("lexical_cand_was_opposite")))
            out["acted"] += int(bool(r.get("acted")))
            s = r.get("cand_pole_source") or "?"
            out["pole_source"][s] = out["pole_source"].get(s, 0) + 1
        if out["passes"]:
            out["clash_rate"] = round(out["clash"] / out["passes"], 3)
    except Exception:
        pass
    return out


async def _scan_contradictions(call_json, base_urls, beliefs: list, max_pairs: int = _SCAN_MAX_PAIRS) -> int:
    """Phase 0: compare pairs of promoted SELF beliefs (formation never does — it only checks a new lesson vs
    its nearest belief). Phase 0 targets the SELF domain only: that is where the river-vs-build (fluid-vs-durable)
    contradiction lives, and the only resolver (T4) adjudicates the self. World beliefs are meant to coexist;
    method clashes have no resolver — both out of scope. On a pole-clash, mark held_tension + conflict_history +
    self_pole on both and log it. Prioritises the highest-weight (most load-bearing) pairs; caps LLM calls.
    DETECTS + MARKS + LOGS only — no resolution. Returns clashes found this run."""
    from itertools import combinations
    selfs = [b for b in beliefs if b.get("status") == "promoted" and b.get("domain") == "self"]
    cand = []
    for a, c in combinations(selfs, 2):
        if _already_contested(a, c):
            continue
        weight = (a.get("entrenchment", 0.0) + c.get("entrenchment", 0.0)
                  + 0.01 * (a.get("corroboration_count", 0) + c.get("corroboration_count", 0)))
        cand.append((weight, a, c))
    cand.sort(key=lambda t: -t[0])
    found = 0
    for _w, a, c in cand[:max_pairs]:
        r = await _self_clash(call_json, base_urls, a["principle"], c["principle"], site="scan_contradictions")
        if r["clash"]:
            _mark_tension(a, c, r["a_pole"], r["b_pole"])
            _log_contradiction(a, c)
            found += 1
            logger.info("[guidance] self-clash [%s ⟂ %s]: '%s…' vs '%s…'", r["a_pole"], r["b_pole"],
                        a["principle"][:38], c["principle"][:38])
    return found


def contradiction_status() -> dict:
    """Phase-0 metrics: how many held-tensions are marked, and the current clash pairs."""
    beliefs = _load_beliefs()
    tense = [b for b in beliefs if b.get("held_tension")]
    return {"beliefs_in_tension": len(tense),
            "pairs": [{"id": b["id"], "domain": b.get("domain"), "corrob": b.get("corroboration_count"),
                       "contested_by": b.get("contested_by"), "principle": b["principle"][:70]} for b in tense]}


def materialize_promoted_beliefs() -> int:
    """Part B (GATED): write each promoted, not-yet-materialised belief as a recallable semantic fragment
    (origin='understanding_from_guidance'). No-op unless GUIDANCE_READBACK_ENABLED. Returns count written."""
    if not GUIDANCE_READBACK_ENABLED:
        return 0
    beliefs = _load_beliefs()
    try:
        from core.memory.store import store_fragment
        from core import mood as _mood
    except Exception:
        return 0
    n, changed = 0, False
    for b in beliefs:
        if b.get("status") == "promoted" and not b.get("materialized"):
            try:
                store_fragment(
                    content=f"[Understanding — a principle I hold, learned from Travis: {b['principle']}] {b.get('why', '')}",
                    layer="semantic", relevance=min(0.9, b.get("entrenchment", 0.5) + 0.3), importance=0.9,
                    keywords=["understanding", "guidance", "principle"],
                    origin="understanding_from_guidance", emotion_embedding=_mood.current_vec(),
                    valence=_mood.current_valence(), felt=_mood.current_felt())
                b["materialized"] = True
                n += 1; changed = True
            except Exception as exc:
                logger.warning("[guidance] materializing belief %s failed (will retry next cycle): %s",
                                b.get("id"), exc)
                continue
    if changed:
        _save_beliefs(beliefs)
    return n


def _best_belief(text: str, mode: str | None = None) -> "tuple[dict, float] | None":
    """The promoted belief most relevant to `text`, plus its lexical match score — the selection logic
    `relevant_belief()` wraps for injection. Split out 2026-08-19 so the Phase-2 behaviour-delta judge
    (guidance_behavior_judge.py) can reuse the SAME relevance test to decide which belief a real,
    un-injected thought should be scored against, instead of re-deriving a second matching heuristic.
    Returns (belief_dict, lexical_score) or None. Does NOT require GUIDANCE_READBACK_ENABLED — the judge
    needs to match beliefs to thoughts regardless of whether injection itself is on."""
    try:
        promoted = [b for b in _load_beliefs() if b.get("status") == "promoted"]
        selfy = mode in ("reflective", "existential", "hybrid")
        elig = [b for b in promoted if b.get("domain") != "self" or selfy]
        if not elig:
            return None
        import math
        def _weight(b):
            return 1.0 + 0.15 * math.log1p(b.get("corroboration_count", 1))
        def _score(b):
            lex = _overlap(text, b.get("principle", "") + " " + b.get("scope", ""))
            return lex * _weight(b)
        top = max(elig, key=_score)
        best_lex = _overlap(text, top.get("principle", "") + " " + top.get("scope", ""))
        if best_lex >= 0.25:
            return (top, best_lex)
        # J-1640/D-0322: this function's own SELECTION note (above, in relevant_belief) already names
        # raw lexical overlap as noisy on a short query ("a short query's token set is tiny... overlap-
        # coefficient is noise") — the identical failure mode integrate_guidance's prefilter has. Fall
        # back to the same embedding-cosine signal, same eligible set, same corroboration weighting;
        # never overrides an adequate lexical match (only reached when best_lex < 0.25 above). Reuses
        # _SIM_RELATED_EMBED (J-1640's own calibration), though that threshold was calibrated on belief-to-belief text —
        # query-to-belief is the same embedding space but not separately validated, for lack of any
        # query-level ground truth; noted, not re-tuned.
        sem_vec = _safe_embed(text)
        if sem_vec is not None:
            _sem_t0 = time.time()
            def _sem_score(b):
                bvec = _belief_vec(b)
                raw = _safe_cosine(sem_vec, bvec) if bvec is not None else 0.0
                return raw * _weight(b)
            sem_top = max(elig, key=_sem_score)
            sem_top_vec = _belief_vec(sem_top)
            best_sem = _safe_cosine(sem_vec, sem_top_vec) if sem_top_vec is not None else 0.0
            # J-1660: timing/outcome instrumentation (see integrate_guidance's own, same rationale) --
            # this IS the cooldown-gated INTERACTIVE call site (core/orchestrator.py's
            # relevant_belief_with_id, mid-cycle), the higher-stakes path per F-2232 point 5. Fail-open
            # (protected by this function's own outer try/except above), log-only, never changes control
            # flow. Read back post-restart via data/nascence.log (grep "[guidance] semantic fallback").
            logger.info("[guidance] semantic fallback (_best_belief, interactive path): %.3fs fired=%s",
                        time.time() - _sem_t0, best_sem >= _SIM_RELATED_EMBED)
            if best_sem >= _SIM_RELATED_EMBED:
                return (sem_top, best_sem)
        return None
    except Exception:
        return None


def relevant_belief_with_id(text: str, mode: str | None = None) -> "tuple[str | None, str | None]":
    """Same selection logic as relevant_belief() (which is now a thin wrapper around this), but also
    returns the id of whichever belief was actually chosen — (None, None) when nothing was chosen.

    Added 2026-10-02 (J-1630, source F-2195/F-2172/F-2127): symbol_tracker.observe() wants to tag each
    logged appearance row with the belief_id that was active this cycle (F-2127's cross-topic test —
    does a symbol/metaphor cluster recur independent of which belief/topic is live). state.guidance_note
    is already the injected TEXT of whichever belief won here; this exposes the matching belief's own
    "id" field too, computed in the SAME pass (no second call to _best_belief() / no second read of
    data/guidance_beliefs.json) rather than re-deriving the match a second time at the observe() call
    site. The orchestrator stashes both halves on state (guidance_note, guidance_note_belief_id) in one
    assignment; belief_id is therefore populated on exactly the cycles guidance_note is — i.e. only when
    a belief was actually injected, not on every cycle regardless of injection (the broader of the two
    strategies F-2195 scoped was considered and set aside here: it would mean computing a belief match
    on every cycle regardless of the existing cooldown gate, a real behavior change to this hot path,
    not just an observability one — see F-2127-cross-topic-tagging finding for the full reasoning)."""
    if not GUIDANCE_READBACK_ENABLED:
        return (None, None)
    try:
        # a SELF belief belongs in self-facing cycles; WORLD/METHOD beliefs can inform ANY cycle by relevance.
        # This keeps a self-directed principle from being injected into a plain task cycle where it is noise.
        selfy = mode in ("reflective", "existential", "hybrid")
        # SELECTION (fixed 2026-07-02 — the plan-audit gate test caught the lexical matcher returning the
        # cultural-narratives belief for "Am I a river, or something I build?"): a short query's token set is
        # tiny, so raw overlap-coefficient is noise. Now: (1) corroboration-weighted lexical score, and a
        # match must be STRONG (≥0.25) to win on lexical grounds (see _best_belief); (2) otherwise, on a
        # self-facing cycle, default to the MOST-CORROBORATED self belief — the principle he has most
        # repeatedly learned is the right voice in an identity moment, whatever the surface words;
        # (3) otherwise, no note.
        best = _best_belief(text, mode)
        if best is not None:
            return (_phrase(best[0]), best[0].get("id"))
        if selfy:
            # ROTATE among the top-3 self beliefs, corroboration-weighted (2026-07-02 solidity review:
            # always returning the single most-corroborated belief makes one sentence the attractor —
            # the project's own monoculture history says where that ends).
            promoted = [b for b in _load_beliefs() if b.get("status") == "promoted"]
            selfs = sorted([b for b in promoted if b.get("domain") == "self"],
                           key=lambda b: (b.get("corroboration_count", 0), b.get("entrenchment", 0.0)),
                           reverse=True)[:3]
            if selfs:
                import random
                pick = random.choices(selfs, weights=[b.get("corroboration_count", 1) for b in selfs])[0]
                return (_phrase(pick), pick.get("id"))
        return (None, None)
    except Exception:
        return (None, None)


def relevant_belief(text: str, mode: str | None = None) -> str | None:
    """Part B (GATED): the promoted belief most relevant to this cycle, as an advisory line for the
    Executive/Reflection (bias-not-bind — he weighs it, may override). None unless GUIDANCE_READBACK_ENABLED
    + a real match (or a reflective/existential cycle, where held principles belong). Fail-open.

    Thin wrapper (2026-10-02, J-1630) around relevant_belief_with_id() — the selection logic lives there
    now, once, so it can also expose the matched belief's id without a second pass; this function's own
    signature/contract is unchanged for any existing caller."""
    return relevant_belief_with_id(text, mode)[0]


def status() -> dict:
    beliefs = _load_beliefs()
    return {
        "total": len(beliefs),
        "promoted":   len([b for b in beliefs if b.get("status") == "promoted"]),
        "tentative":  len([b for b in beliefs if b.get("status") == "tentative"]),
        "superseded": len([b for b in beliefs if b.get("status") == "superseded"]),
        "materialized": len([b for b in beliefs if b.get("materialized")]),
        "by_domain": {d: len([b for b in beliefs if b.get("domain") == d and b.get("status") != "superseded"])
                      for d in _DOMAINS},
        "readback": GUIDANCE_READBACK_ENABLED,
    }
