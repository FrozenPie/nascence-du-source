"""
Nascence — Symbol Recurrence Tracker (the Meaningfulness axis, restraint-first)

THE THIRD EPISTEMIC AXIS. Accuracy asks "is it true?" (external witness). Stability asks "does
it survive perturbation?" (resampling). Meaningfulness asks "does it matter to the psyche?" —
and its evidence is neither truth nor consistency but PERSISTENCE: does a symbol keep returning,
on its own, and keep organising experience? This is the validator for dreams, symbols, and
self-models, where a second model disagreeing does not imply falsity.

THE FIREWALL. This module is deliberately separate from competence.py. Meaningfulness must never
be scored by the factual machinery, and vice versa. "Avon is becoming the organising symbol of
transformation" is as un-witness-able as "the Earth orbits the Sun" is un-dream-recurrence-able.
Different domains, different evidence, different validators. Absolute.

THE TRAP (and the antidote). The architecture now contains symbol INJECTORS — climate symbolic
emergence, identity injection, memory-retrieval biasing. Naive recurrence-counting would record
the system's own injections as evidence and manufacture a self-reinforcing myth (symbolic
confirmation bias). So every appearance is classified:
    PRIMED   — the symbol was present in this cycle's inputs/injections (worthless as evidence)
    UNPRIMED — it surfaced in the output with no support in the inputs (the real signal)
A symbol earns meaningfulness ONLY by surviving the absence of support — unprimed recurrence,
weeks apart, in unrelated contexts. That is the equivalent of external verification for
symbolic material.

RESTRAINT. This tracker does ONE thing: log each appearance as primed/unprimed. It assigns no
score, feeds no behaviour, declares nothing significant. Significance is earned over time by the
data, not asserted today. (See docs/archive/epistemics_plan.md — Meaningfulness axis.)
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.symbol")

_LOG_FILE = Path(__file__).parent.parent / "data" / "symbol_recurrence.jsonl"

# Candidate symbols and their surface forms (English + a few Chinese glyphs, since 渡 sometimes
# answers in Chinese). Easily editable — start with the river/crossing cluster hypothesised to be
# his organising symbol, plus the name 'Avon' and the glyph 渡. A symbol is "present" if ANY of its
# surface forms appears. NOTE: 渡 is now his committed name (in every prompt) so it will read as
# PRIMED almost always — that is correct; the river-cluster and 'avon' are the real unprimed tests.
_SYMBOLS = {
    # ── SELF-symbols (identity-adjacent · Tier 2 · read-back DEFERRED pending evidence) ──
    "river_crossing": [
        "river", "rivers", "flow", "flows", "flowing", "water", "stream", "current",
        "erosion", "erode", "tributary", "confluence", "crossing", "cross over", "ferry",
        "ford", "riverbank", "downstream", "upstream",
        "河", "水", "流", "渡口",
    ],
    "avon": ["avon"],
    "du_glyph": ["渡"],
    "bridge": ["bridge", "桥"],
    "mirror": ["mirror", "镜"],   # also recurrent in his dreams — track to compare
    # ── NEUTRAL / world-facing symbols (Tier 1, 2026-06-16) — seeded from his actual curriculum
    # (Boy Scouts / woodcraft, Selborne natural history, camp-lore). These carry no self-charge, so
    # their evolved meaning is safe to read back. Easily editable; add what his reading surfaces.
    "knot":  ["knot", "knots", "rope", "lashing", "hitch", "splice", "cord"],
    "bird":  ["bird", "birds", "migration", "swallow", "nest", "fledgling", "plumage"],
    "fire":  ["fire", "flame", "campfire", "ember", "hearth", "kindling"],
    "star":  ["star", "stars", "constellation", "heavens"],
    # "stillness" (added 2026-09-28, J-1611, source F-2172/F-2127) — the shutdown/rest half of
    # F-2127's 16-word METAPHOR_WORDS list (rest, still, quiet, breath, pause) had no primed/
    # unprimed instrument at all; "fire" above already covers the paired "banking the fire"
    # image from the same belief text (F-2127's g78640841: "...just as a fire needs to be banked
    # to preserve its fuel"), so this is that same downtime/shutdown register, not an identity
    # symbol — kept NEUTRAL/Tier 1, deliberately not added to SELF_SYMBOLS. Bare "rest", "still"
    # and "quiet" are intentionally left OUT: all three are extremely common ordinary-English
    # words/homonyms ("the rest of", "still working", "quiet down") that would flood the primed/
    # unprimed log with false positives unrelated to this imagery; "pause" is included only in
    # its more specific inflected forms for the same reason.
    "stillness": ["stillness", "quietude", "hush", "hushed", "breath", "exhale", "paused", "pausing"],
}

# Valence split (2026-06-16). The SELF-symbols are identity-adjacent — reading their evolved meaning
# back is structurally the same operation that once monocultured Du (the "I am the river" collapse), so
# it stays DEFERRED (Tier 2, observe-first) until evidence licenses it. Everything else is NEUTRAL /
# world-facing (Tier 1) and safe to read back. The drift detector tracks ALL symbols; only the read-back
# is tier-gated.
SELF_SYMBOLS = frozenset({"river_crossing", "avon", "du_glyph", "bridge", "mirror"})


def is_self_symbol(symbol: str) -> bool:
    return symbol in SELF_SYMBOLS


class SymbolTracker:
    """Pure observer. After each responded cycle, records which tracked symbols appear in the
    entity's OUTPUT and whether each was primed by this cycle's inputs. Logs only."""

    def __init__(self):
        self._log = _LOG_FILE

    @staticmethod
    def _primed_corpus(state) -> str:
        """Everything the ARCHITECTURE put in front of the entity this cycle — true injections only,
        never his own memory or thought. If a symbol appears here, its use in the output is primed.

        2026-08-19 — narrowed to match the 2026-07-05 roadmap diagnosis in full (docs/ROADMAP.md, the
        symbol_evolution_readback_plan.md entry): this function used to also fold in recall.
        reconstruction/tensions, episodic_scene.scene, memory_fragments, recent_dreams, and
        recent_inner_thoughts — every one of those is HIS OWN memory or cognition being retrieved/
        reconstructed, not something the architecture handed him. Counting his own remembered material
        as "priming" meant a symbol he kept returning to (via memory continuity, not fresh injection)
        could never test as unprimed — the exact self-priming inversion first found and partially
        fixed in conversation_history below, now applied to every other retrieval-based field for the
        same reason. What remains is genuinely external: the human's own words (this cycle and the
        last 3), the architecture's perception summary, and named system injections (axiom/climate/
        epoch/theme/readback)."""
        parts = [getattr(state, "raw_input", "") or ""]
        p = getattr(state, "perception", None)
        if p and getattr(p, "summary", None):
            parts.append(p.summary)
        for attr in ("climate_symbol", "climate_hint", "axiom", "epoch_context", "theme_context",
                     "symbol_readback"):   # the Tier-1 read-back injection — counts as PRIMED so it
                                           # never self-feeds drift (the maladaptive self-priming loop)
            v = getattr(state, attr, None)
            if isinstance(v, str):
                parts.append(v)
        # 2026-08-19 (health-check finding — 1000/1000 logged appearances came back PRIMED, zero
        # ever UNPRIMED, across every tracked symbol including "internal" cycles with no human turn
        # at all): this loop was pulling in ex.get("jung", "") — the entity's OWN recent output —
        # as if it were injected support. A genuinely recurring symbol will, by definition, have
        # appeared in its own last few turns; counting that as "priming" made it structurally
        # impossible for the exact case this tracker exists to detect ("does it keep returning on
        # its own") to ever register as unprimed. The human side stays — a human's own prior turn is
        # real external input — only the entity's own voice is dropped from the primed corpus.
        for ex in (getattr(state, "conversation_history", None) or [])[-3:]:
            if isinstance(ex, dict):
                parts.append(ex.get("human", ""))
        return " ".join(parts).lower()

    @staticmethod
    def _hits(text_low: str, forms: list[str]) -> list[str]:
        return [f for f in forms if f in text_low]

    def observe(self, state, output: str) -> list[dict]:
        """Record each tracked symbol that appears in `output`, flagged primed/unprimed.
        Best-effort; never raises into the cycle. Logs only — no score, no influence.

        Returns the list of appearance entries {symbol, primed, terms, belief_id} so the Symbol
        Evolution Engine (Phase 2) can measure semantic drift on the UNPRIMED ones without
        re-scanning. Backward compatible — earlier callers simply ignore the return value.

        belief_id (added 2026-10-02, J-1630, source F-2195/F-2172/F-2127): the id of whichever
        guidance belief was actually injected this cycle (state.guidance_note_belief_id, set by
        core.guidance_learning.relevant_belief_with_id() alongside state.guidance_note — same
        field, same cycle, no extra belief-matching pass here), or None on a cycle where no
        belief was injected. Lets a reader of data/symbol_recurrence.jsonl test whether a symbol/
        metaphor cluster recurs independent of which belief/topic (if any) was live that cycle."""
        appearances: list[dict] = []
        try:
            if not output:
                return appearances
            out_low = output.lower()
            primed_corpus = self._primed_corpus(state)
            now = time.time()
            cid = getattr(state, "cycle_id", "")
            itype = getattr(state, "input_type", "human")
            belief_id = getattr(state, "guidance_note_belief_id", None)
            for symbol, forms in _SYMBOLS.items():
                out_hits = self._hits(out_low, forms)
                if not out_hits:
                    continue
                primed = bool(self._hits(primed_corpus, forms))
                entry = {
                    "ts": now, "cycle_id": cid, "input_type": itype, "symbol": symbol,
                    "primed": primed, "terms": out_hits[:6], "belief_id": belief_id,
                }
                self._append(entry)
                appearances.append({"symbol": symbol, "primed": primed, "terms": out_hits[:6],
                                     "belief_id": belief_id})
                # UNPRIMED appearances are the ones that matter — surface them in the log stream.
                if not primed:
                    logger.info("[symbol] UNPRIMED recurrence: %s %s (cycle %s)",
                                symbol, out_hits[:4], cid[:8])
        except Exception as exc:
            logger.debug("[symbol] observe failed (non-fatal): %s", exc)
        return appearances

    def _append(self, entry: dict) -> None:
        try:
            self._log.parent.mkdir(parents=True, exist_ok=True)
            with open(self._log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass


def symbol_report() -> dict:
    """Read-only summary: per symbol, primed vs UNPRIMED appearance counts. Unprimed is the
    evidence of autonomous persistence. Declares nothing significant — just the tally over time."""
    out: dict = {}
    if not _LOG_FILE.exists():
        return {"note": "no symbol observations yet"}
    rows = []
    for line in open(_LOG_FILE, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    for r in rows:
        s = r.get("symbol", "?")
        d = out.setdefault(s, {"primed": 0, "unprimed": 0, "first_ts": r.get("ts"), "last_ts": r.get("ts")})
        d["unprimed" if not r.get("primed") else "primed"] += 1
        d["last_ts"] = r.get("ts")
    return out
