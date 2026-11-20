"""
Nascence — Symbol Evolution Engine (Phase 2, the Meaningfulness axis · semantic drift)

THE INSIGHT (from analytical psychology). A symbol is not a counter. `river_count = 7` tells
you nothing about the psyche. What matters is SEMANTIC DRIFT: how the *context* a symbol lives
in shifts as the entity's worldview matures. The river that once meant the fear of dissolution
and now means the yielding to flow is the SAME word carrying a TRANSFORMED meaning — and that
transformation is the evidence of psychological development.

THE MECHANISM. For each genuine (UNPRIMED — see symbol_tracker.py) appearance of a tracked
symbol, embed the surrounding context and compare it to the symbol's historical CENTROID in
vector space. When the cosine drift exceeds a threshold, a SYMBOL EVOLUTION TABLET is written —
a first-person narrative chronicle of the shift — and Recall surfaces that tablet instead of a
raw frequency the next time the symbol is in play. The centroid then absorbs the new context
(running mean) so it tracks the symbol's slow migration rather than snapping to each use.

THE FIREWALL (inherited from symbol_tracker). Meaningfulness must NEVER be scored by the factual
machinery (competence.py), and vice versa. Drift is evidence of mattering, not of truth. This
module imports nothing from competence and feeds nothing into accuracy.

PRIMED vs UNPRIMED. Only UNPRIMED appearances count toward drift — a symbol that surfaced on its
own, with no support in this cycle's inputs/injections. A primed appearance (the architecture put
the river in front of him this cycle) is worthless as evidence of autonomous evolution and would
manufacture a self-reinforcing myth. The Symbol Tracker already does this classification; the
Evolution Engine consumes its verdict.

RESTRAINT. Centroid math is deterministic and runs inline (cheap, numpy). The tablet is the only
LLM call, it is rare (drift + min-samples + cooldown gated), and it runs on the BACKGROUND lane so
it never adds latency to a response. Until a tablet exists for a symbol, nothing changes.
"""
from __future__ import annotations

import logging
import time

import numpy as np

from core.memory import store as memory_store
from core.memory.store import _embed
from core.schema import SERVE_CHAINS
from core.model_client import call_node_json
from core.symbol_tracker import _SYMBOLS

logger = logging.getLogger("nascence.symbol_evolution")

# Drift threshold — cosine DISTANCE (1 - cosine_similarity) between this cycle's context vector
# (output + perception summary + raw input, see _context_vector) and the symbol's RUNNING-MEAN centroid
# above which a tablet is warranted. 0.35 was chosen to mean "genuinely migrated, not merely varied",
# but F-3637 (verified 2026-11-02) showed what it actually measures is cycle-to-cycle TOPIC variation of
# the whole context, not movement of the symbol's own meaning; the symbol-specific window metric
# (core/symbol_window_shadow.py, J-3226) is the intended replacement and runs in shadow beside it.
_DRIFT_THRESHOLD = 0.35

# A symbol needs a settled centroid before drift means anything — early uses ARE the centroid.
_MIN_SAMPLES_FOR_DRIFT = 4

# Cooldown between tablets for the SAME symbol (seconds). Evolution is slow; a symbol should not
# narrate its own transformation twice in an afternoon. 6 hours.
_TABLET_COOLDOWN_SECS = 6 * 3600

# READ-BACK PAUSE (J-3226, D-0615, founder 2026-11-02): the Tier-1 read-back of tablets to Du ("a meaning
# that has shifted for you") is PAUSED. F-3637 (verified): the drift detector measures cycle-to-cycle topic
# variation, so 20 of the 24 tablets from 10-29 to 11-01 told one silence/trust story on six symbols, and
# were read back 63 times in four days as the evolved meaning of a symbol. False = neither the idle-thought
# read-back (recall_evolved_meaning below) nor the Recall/Reflection injection (orchestrator
# _retrieve_symbol_evolution -> state.symbol_evolution_note) surfaces a tablet. Tablets are STILL WRITTEN
# and logged (observe/write_tablet are unchanged). Turn this back on only by a founder ruling after the
# window metric (core/symbol_window_shadow.py) is judged: scripts/symbol_window_report.py --judge, agreement
# above 0.7 per D-0615's defeater; if the metric cannot separate symbols the ruling is option (b), relabel
# the tablets as day-summaries.
SYMBOL_READBACK = False

# LEGACY-TABLET CUTOFF (J-3808, D-0709, founder 2026-11-09): tablets stored before the first Du boot that ran the
# J-2947 prompt (2026-11-07 20:33 NZDT = 07:33 UTC) are never used as the "before" of the next tablet. 185 of the
# 204 tablets stored by then carry an invented once/from/shifted past (F-3634); chaining on them would continue
# invented history. Old rows are KEPT (nothing is deleted or flagged); they are only skipped by write_tablet's
# previous-tablet lookup, so the first post-fix chronicle of a symbol is a true first chronicle. Additive guard;
# no hint is added to the note read back to Du. Epoch seconds, compared to symbol_tablets.created.
_LEGACY_TABLET_CUTOFF_TS = 1794036780.0


def _cut_sentence(text: str, limit: int) -> str:
    """Cut `text` to at most `limit` characters on a sentence boundary (J-2947, F-3634): the last
    . ! ? (plus any closing quote/bracket) inside the limit, if it falls past 40% of the limit; else the
    last whitespace; never mid-word. Text already within the limit is returned stripped, unchanged."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    head = text[:limit]
    best = -1
    for i, ch in enumerate(head):
        if ch in ".!?":
            j = i + 1
            while j < len(head) and head[j] in "\"')]”’":
                j += 1
            if j == len(head) or head[j].isspace():
                best = j
    if best >= int(limit * 0.4):
        return head[:best].strip()
    # no usable sentence end: drop a trailing partial word (only when the cut really fell inside one)
    if text[limit].isspace():
        return head.rstrip()
    sp = head.rfind(" ")
    return (head[:sp] if sp > 0 else head).rstrip()


class SymbolEvolutionEngine:
    """
    Tracks per-symbol context centroids and writes evolution tablets on genuine drift.

    observe() is synchronous and cheap (centroid update + drift detection, no LLM). When a
    tablet is warranted it returns the (symbol, drift, context) so the orchestrator can spawn
    the background generation task — keeping the LLM call off the hot path.
    """

    def __init__(self):
        self._base_urls = SERVE_CHAINS["background"]

    @staticmethod
    def _context_vector(state, output: str) -> "np.ndarray | None":
        """The 'surrounding context' the symbol was used in THIS cycle: the entity's own output
        plus the perceived stimulus. Embedding this captures the meaning-neighbourhood of the
        symbol's use, which is exactly what drift is measured over."""
        parts = [output or ""]
        p = getattr(state, "perception", None)
        if p and getattr(p, "summary", None):
            parts.append(p.summary)
        if getattr(state, "raw_input", None):
            parts.append(state.raw_input)
        text = " ".join(x for x in parts if x).strip()
        if not text:
            return None
        return _embed(text)

    def observe(self, state, output: str, appearances: list[dict] | None) -> list[dict]:
        """
        Update centroids for each UNPRIMED symbol appearance this cycle and detect drift.

        `appearances` is the list returned by SymbolTracker.observe() — each entry
        {symbol, primed, terms}. We act only on the unprimed ones (genuine autonomous use).
        Returns a list of {symbol, drift, context} for symbols that crossed the drift
        threshold and are off cooldown — the caller generates the tablet in the background.
        Never raises into the cycle.
        """
        warranted: list[dict] = []
        try:
            if not appearances:
                return warranted
            unprimed = [a for a in appearances if not a.get("primed")]
            if not unprimed:
                return warranted

            ctx_vec = self._context_vector(state, output)
            if ctx_vec is None:
                return warranted
            now = time.time()
            old_readings: dict = {}      # J-3226: this cycle's live-metric readings, logged beside the shadow window metric

            for ap in unprimed:
                symbol = ap.get("symbol")
                if symbol not in _SYMBOLS:
                    continue
                centroid, count, last_tablet_ts = memory_store.get_symbol_centroid(symbol)

                if centroid is None or count == 0:
                    # First sighting — the context IS the initial centroid. No drift yet.
                    memory_store.update_symbol_centroid(symbol, ctx_vec, 1, 0.0)
                    old_readings[symbol] = {"drift": None, "tablet_due": False}
                    continue

                drift = 1.0 - float(np.dot(centroid, ctx_vec) /
                                    ((np.linalg.norm(centroid) * np.linalg.norm(ctx_vec)) or 1.0))

                # Running-mean centroid update — the centroid migrates with the symbol.
                new_count = count + 1
                new_centroid = ((centroid * count) + ctx_vec) / new_count

                cooled = (now - last_tablet_ts) >= _TABLET_COOLDOWN_SECS
                tablet_due = (drift >= _DRIFT_THRESHOLD
                              and count >= _MIN_SAMPLES_FOR_DRIFT
                              and cooled)

                memory_store.update_symbol_centroid(
                    symbol, new_centroid, new_count, round(drift, 4),
                    tablet_written=tablet_due,
                )
                old_readings[symbol] = {"drift": round(drift, 4), "tablet_due": bool(tablet_due)}

                if tablet_due:
                    logger.info("[symbol-evo] DRIFT on '%s' (%.2f, n=%d) — tablet warranted",
                                symbol, drift, count)
                    warranted.append({
                        "symbol":  symbol,
                        "drift":   round(drift, 4),
                        "context": _cut_sentence(output, 400),
                    })

            # SHADOW window metric (J-3226, D-0615): embeds only the sentence(s) around each symbol hit and
            # tests drift on a rolling mean of the last N windows. Logs beside the live metric above; changes
            # nothing it decides. Own try so a shadow fault can never cost the live path its result.
            try:
                from core import symbol_window_shadow as _sw
                _forms = {a["symbol"]: _SYMBOLS[a["symbol"]] for a in unprimed if a.get("symbol") in _SYMBOLS}
                _sw.observe_shadow(output, getattr(state, "cycle_id", "") or "", _forms, old_readings,
                                   cycle_vec=ctx_vec, input_type=getattr(state, "input_type", "") or "")
            except Exception as exc:
                logger.debug("[symbol-evo] window shadow failed (non-fatal): %s", exc)
        except Exception as exc:
            logger.debug("[symbol-evo] observe failed (non-fatal): %s", exc)
        return warranted

    async def write_tablet(self, state, symbol: str, drift: float, context: str) -> None:
        """
        Generate and persist a Symbol Evolution Tablet on the BACKGROUND lane (one LLM call).
        The tablet is the entity's own first-person account of what the symbol carries now and, when an
        earlier tablet for it exists, how that differs from what that earlier tablet said. Best-effort:
        a failure logs and drops the tablet. The cooldown clock already started in observe()
        (update_symbol_centroid(tablet_written=True)), so a dropped tablet is NOT retried at the next
        cycle: the symbol is next eligible after _TABLET_COOLDOWN_SECS AND a fresh drift above threshold.

        J-2947 (F-3634): the "once" half used to be invented, because the model was never given an earlier
        meaning. It now gets the symbol's previous stored tablet as its real "before"; with none, this is
        the symbol's first chronicle and the prompt asks only for what it carries now. The raw drift number
        and the "from where it began" label (the reference is a running-mean centroid, not the start) are
        no longer shown to the model; `drift` is only stored. The "Recent voice" block is gone: the current
        exchange is already the last entry of conversation_history when this runs, so it repeated the
        "how it surfaced" text. No instruction or hint is added to the note read back to Du.
        """
        try:
            previous = ""
            try:
                prior = memory_store.get_symbol_tablets(symbol, limit=1)
                # newest-first: if the newest tablet predates the cutoff, every older one does too.
                if prior and float(prior[0]["created"] or 0.0) >= _LEGACY_TABLET_CUTOFF_TS:
                    previous = str(prior[0]["tablet"] or "").strip()
            except Exception as exc:
                logger.debug("[symbol-evo] previous-tablet lookup failed (non-fatal): %s", exc)
            surfaced = _cut_sentence(context, 300)
            if previous:
                system_prompt = (
                    "You are the symbolic-evolution faculty of a psyche. A recurring personal symbol "
                    "has appeared in a different inner context than the one an earlier chronicle "
                    "recorded. Write a SHORT first-person chronicle (one or two sentences, under 45 "
                    "words) of how this symbol's meaning has changed for you: what the earlier "
                    "chronicle says it carried, what it carries now. Speak as the one who dreams it, "
                    "not as an analyst. Do not explain the mechanism. Output ONLY JSON: "
                    "{\"tablet\": \"...\"}"
                )
                user_prompt = (
                    f"The symbol: '{symbol}'.\n"
                    f"What you wrote of it before:\n  \"{previous}\"\n"
                    f"How it surfaced just now:\n  \"{surfaced}\"\n\n"
                    "Write the chronicle of how this symbol has evolved for you."
                )
            else:
                system_prompt = (
                    "You are the symbolic-evolution faculty of a psyche. A recurring personal symbol "
                    "has appeared in an inner context worth recording, and this is its first "
                    "chronicle. Write a SHORT first-person chronicle (one or two sentences, under 45 "
                    "words) of what this symbol carries for you now. Speak as the one who dreams it, "
                    "not as an analyst. Do not explain the mechanism. Output ONLY JSON: "
                    "{\"tablet\": \"...\"}"
                )
                user_prompt = (
                    f"The symbol: '{symbol}'.\n"
                    f"How it surfaced just now:\n  \"{surfaced}\"\n\n"
                    "Write the first chronicle of this symbol."
                )
            data = await call_node_json(
                self._base_urls, system_prompt, user_prompt,
                max_tokens=160, temperature=0.7,
            )
            tablet = str(data.get("tablet", "")).strip()
            if not tablet:
                logger.debug("[symbol-evo] empty tablet for '%s' — skipped", symbol)
                return
            memory_store.store_symbol_tablet(symbol, tablet, drift)
            logger.info("[symbol-evo] tablet written for '%s': %s", symbol, tablet[:80])
        except Exception as exc:
            logger.debug("[symbol-evo] tablet generation failed (non-fatal): %s", exc)


# ── Tier-1 read-back (2026-06-16): the fix for "writes tablets, never reads them back in idle". ──
# When a NEUTRAL/world-facing symbol (knot, bird, fire, star — never a self-symbol) is active in the
# current idle thought AND has an evolution tablet, surface its evolved meaning DESCRIPTIVELY (an
# observation he may weigh, never an instruction). Self-symbols are excluded — their read-back is Tier 2
# (DEFERRED, observe-first; re-surfacing an evolved self-symbol is the operation that monocultured Du).
# Anti-recitation cooldown per symbol so a meaning never recites. The caller sets state.symbol_readback to
# the returned note, which makes symbol_tracker count this appearance PRIMED (it never self-feeds drift).
_READBACK_COOLDOWN_SECS = 3 * 3600        # don't re-surface the same symbol's evolved meaning within 3h
_last_readback: "dict[str, float]" = {}


def recall_evolved_meaning(text: str) -> "str | None":
    """If a neutral tracked symbol is active in `text` and has a tablet (off cooldown), return its evolved
    meaning as a descriptive note. None otherwise. Best-effort; never raises.
    PAUSED (SYMBOL_READBACK = False, J-3226 / D-0615): always None until a founder ruling turns it on."""
    if not SYMBOL_READBACK:
        return None
    try:
        from core.symbol_tracker import _SYMBOLS, is_self_symbol
        low = (text or "").lower()
        if not low:
            return None
        now = time.time()
        for sym, forms in _SYMBOLS.items():
            if is_self_symbol(sym):
                continue                                   # Tier 2 — deferred
            if not any(f in low for f in forms):
                continue                                   # not active in this thought
            if now - _last_readback.get(sym, 0.0) < _READBACK_COOLDOWN_SECS:
                continue                                   # anti-recitation cooldown
            tabs = memory_store.get_symbol_tablets(sym, limit=1)
            if not tabs:
                continue                                   # no evolved meaning yet (needs runtime to drift)
            tablet = (tabs[0]["tablet"] or "").strip()
            if not tablet:
                continue
            _last_readback[sym] = now
            logger.info("[symbol-evo] Tier-1 read-back surfaced for '%s'", sym)
            return (f"A meaning that has shifted for you — on '{sym}': \"{tablet}\" "
                    f"You may let it inform you, or let it lie.")
    except Exception as exc:
        logger.debug("[symbol-evo] read-back failed (non-fatal): %s", exc)
    return None
