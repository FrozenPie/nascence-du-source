"""
Nascence — Dream Node (Node 12)

Offline memory metabolism — fires during Sleep State (session end, or when the Somatic Engine's
metabolic floor is hit).

A dream is now a short ARC of scenes that FOLLOW and DEVELOP one another (2026-06-15, founder: "his
dream needs to be longer, episodes that follow each other and progress more"), not a single fragment.
Each scene is seeded by the one before it — its narrative, its symbols, and what it left unfaced — so
imagery carries forward and the night progresses, the way real dreaming moves through scenes across a
night. The night's END-STATE drives the carry-forward: if the last scene leaves something unmet, that
becomes shadow (it returns tomorrow); if the arc reaches a true image of reconciliation, that is the
light bridge.

The dream is SEPARATE from the rest of the sleep routine (replay-strengthen, self-chapter formation,
downscale) — it is the symbolic process, not the grounded-learning consolidation (which the sleep routine
does NOT currently do — chapters explicitly exclude reading/study; that gap is a separate future addition).

Each scene is committed to L3 episodic memory (origin='dream', linked by a shared dream_id + scene index),
surfacing through standard retrieval. NOT a NodeBase subclass — a one-shot coroutine called by the
orchestrator at Sleep State, on the dreamer lane (mistral-small3.1 · CPU num_gpu:0 · :11433 — docstring
corrected 2026-07-02, was stale "11460"). With the multilevel axiom, unresolved
dreams feed shadow → T4 → ONLY the becoming facet, so a vivid symbolic arc can no longer re-monoculture
the seeker/companion/feeling selves — it is contained to the one room where symbolic self-reflection lives.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
import re

from core.schema import CognitiveState, SERVE_CHAINS
from core.model_client import call_node_json
from core.memory.store import store_fragment
# J-2893 / F-3568: stored dream fragments read "[Dream dream_N, scene K/M] <narrative>"; readers that show the text
# to a model strip that bookkeeping prefix (what _store_episode WRITES is unchanged: scene grouping relies on it).
_DREAM_PREFIX_RE = re.compile(r"^\s*\[Dream\s+dream_\d+,\s*scene\s+\d+\s*/\s*\d+\]\s*")


def strip_dream_prefix(text: str) -> str:
    return _DREAM_PREFIX_RE.sub("", text or "", count=1)


from core import profile  # J-0874: frontier.note_question() (write-fence module #18, J-0846) raises
                          # profile.NonLiveWriteError in a non-live process; _ground_symbols() must
                          # let it escape its own swallow (D-0179 hard raise).

logger = logging.getLogger("nascence.dream")

_SC_STATE_PATH = Path(__file__).parent.parent / "data" / "subconscious_state.json"

# J-2178 (F-2882, restart-gated): _gather_materials -> _load_top_tensions -> _find_counterpart embedded every
# integration_pattern label one at a time, uncached, per tension, ON the event loop (27.4 s measured for ~1628
# labels). Two additive fixes, each with a kill switch (False = exact pre-J-2178 behaviour):
#   DREAM_GATHER_OFFLOOP  -- synthesise() awaits _gather_materials in a worker thread (core.idle_offloop.off_loop);
#   DREAM_PATTERN_CACHE   -- pattern-label vectors are batch-embedded once and cached by label text (the embedder is
#                            fixed and deterministic, so the text IS the invalidation key: a changed/new label is
#                            simply a cache miss; nothing can go stale).
DREAM_GATHER_OFFLOOP = True
DREAM_PATTERN_CACHE = True
# J-2296 (F-2993 re-read, restart-gated): the 4.5-7.7 s night stalls attributed to sub 'dream_probe' were NOT the
# probe (already off the loop since J-2111). The heartbeat can only record a stall when the loop next yields, and
# the first yield after dream_gather_done is the probe's off_loop await -- so the label it saw was 'dream_probe'
# while the freeze itself was the synchronous block BEFORE it: _last_unresolved_arc / _carried_n (3 MB
# dream_log.jsonl reads), _met_carry_check (dream_met.thread_state: sqlite + per-arc embeds) and
# memory_service.ask('dream'). Measured 10-17 from the shadow logs' own timestamps: met-carry row 4.8 s and the
# memory ask's coupling_ride row 5.9 s after dream_id was minted, stall seen 0.1 s later. Kill switch: False = those
# four calls run synchronously on the loop exactly as before. Every call is thread-safe: own sqlite connections,
# store._EMBED_LOCK around encode, memory_service.ask already audited for worker-thread use (core/idle_offloop.py).
DREAM_PRE_PROBE_OFFLOOP = True
# J-2296: wall-clock stamps of each pre-scene step (gather begin/end, carry, met, memory ask, probe), added to the
# arc record as the additive 'stage_timing' key -- the gather-to-gather_done gap F-2993 could not measure.
DREAM_STAGE_TIMING = True
_PATTERN_VEC_CACHE: dict = {}
_PATTERN_VEC_CACHE_MAX = 8192
_PATTERN_VEC_LOCK = __import__("threading").Lock()


def _pattern_vectors(labels: list) -> dict:
    """label -> vector for every label that embeds (blank/failed labels omitted). Cache hits are free; all misses
    go through ONE batched encode. Fail-open: any error here returns whatever was gathered (callers treat a missing
    label like the old `pv is None` skip)."""
    got: dict = {}
    try:
        with _PATTERN_VEC_LOCK:
            for l in labels:
                v = _PATTERN_VEC_CACHE.get(l)
                if v is not None:
                    got[l] = v
        miss = [l for l in dict.fromkeys(labels) if l not in got]
        if miss:
            from core.memory.store import _embed_batch
            vecs = _embed_batch(miss)
            with _PATTERN_VEC_LOCK:
                if len(_PATTERN_VEC_CACHE) + len(miss) > _PATTERN_VEC_CACHE_MAX:
                    _PATTERN_VEC_CACHE.clear()
                for l, v in zip(miss, vecs):
                    if v is not None:          # never cache a failure -- retry next time
                        _PATTERN_VEC_CACHE[l] = v
                        got[l] = v
    except Exception as exc:
        logger.debug("[dream] pattern vector batch failed: %s", exc)
    return got
_DREAM_LOG     = Path(__file__).parent.parent / "data" / "dream_log.jsonl"
_RESOLUTION_SHADOW_LOG = Path(__file__).parent.parent / "data" / "logs" / "dream_resolution_shadow.jsonl"  # J-1847: module-level so a test can temp-path it
# PHASE 1 INSTRUMENTATION (2026-09-17, J-1057, docs/staged/dream_overhaul.md sec 1/sec 7 Phase 1 row):
# one row per scene TRANSITION, written from the generation loop itself (NOT gated on commit=True --
# an in-vitro arc, e.g. Experiment A's commit=False arms, sec 6, still needs this to see the CURRENT
# engine's scene-to-scene handoff; only nodes/dream_node.py's writes to memory/edges/dream_log stay
# commit-gated, unchanged). Additive, own file -- dream_log.jsonl's own shape is untouched.
_DREAM_STATE_LOG = Path(__file__).parent.parent / "data" / "logs" / "dream_state.jsonl"

# Background lane — dreams are offline activity, no GPU pressure needed
# DREAMER MODEL (2026-06-20): dreams run on mistral-small3.1 (24B, Mistral family) on the local Threadripper
# CPU (num_gpu:0) — forced off the GPUs so the conscious 1080 lane is never touched. Chosen over phi3 (which
# couldn't populate the schema → 1-scene collapse) and over gemma4:31b (which would make the subconscious echo
# the conscious gemma lane); a DIFFERENT family keeps the dream a genuinely OTHER voice. Benchmarked on the
# arc eval: schema 1.0, develop 4.5, 6/6 JSON (scripts/dream_arc_eval.py). Dreams fire at sleep, when the CPU
# is otherwise idle, so the slower CPU speed costs only a few extra minutes of an already-resting mind.
# REDISTRIBUTION 2026-08-27 (D-0044, ramses_second_tier §5 move 2, founder-approved): the dreamer moves
# to command-r7b on the Ramses 3070 (:11441) — yi:34b on the local CPU hub was the fabric's worst profile
# (227 calls, mean 184s, 16.3% failure; F-0381). Auditioned this session with the real dream-schema
# contract: full schema populated (narrative/symbols/unresolved_core/phase), 21.3s. :11442 (yi) stays as
# the explicit failover so a Ramses nap degrades to the old dreamer instead of dream loss. Both hubs are
# single-model llama.cpp servers that ignore the model field. Re-run dream_arc_eval on command-r7b: J-0305.
# REDISTRIBUTION AGAIN 2026-08-28 (founder: "ollama llms gone from Ramses"): the 08-27 placement lasted
# one night — command-r7b shared the 3070 with Ramses ollama's phi3+deepseek residents and the card
# locked (F-0389: this node's own calls to :11441 failed 210.23s/300.16s/300.7s, ok:0, each falling
# back to yi @ 11442). The 3070 now belongs to phi3's hub alone; dreams move to §5.2's own second
# candidate, mixtral:8x7b @ ramses:11438 (i9 CPU). Auditioned this session with the real dream-schema
# contract: 52.9s, all keys populated, valid movement, real use of the material — vs yi's 184s mean.
# yi @ :11442 stays the explicit failover. NOTE model_client.py fix same session: :11438 was missing
# from the ollama-style port list, so calls fell to /v1 (HTTP 404 on the hub) — required for this route.
_DREAM_URLS    = ["http://LAN-HOST:11438", "http://127.0.0.1:11442"]
_DREAM_MODEL   = "mixtral:8x7b"  # truthful for the primary; the failover hub serves yi:34b-v1.5 regardless
_DREAM_NUM_GPU = None    # let each hub use its own config (both are CPU-hosted single-model servers now;
                         # the old num_gpu=0 CPU-forcing only applied to the local offload hub)
# RESILIENCE (2026-06-23): the 24B/CPU dreamer is evicted between sleeps (keep_alive lapses if dreams are >2h
# apart), so a cold load can drop the first connection — an INSTANT "all servers exhausted" on the single-URL
# chain (no failover). Retry with backoff instead of losing the whole dream; the wait lets the ~20GB model
# finish loading. And a generous timeout, since 24B CPU generation is slow and sleep isn't latency-critical.
_DREAM_TIMEOUT = 300     # seconds — 24B on CPU generates slowly; never time out a real generation
_DREAM_BACKOFF = [15, 40]  # seconds to wait before retry 2 and retry 3 (covers a cold 20GB CPU load)

# A dream is an arc of scenes. EARNED LENGTH (2026-06-18, the same rule as thought-trains): the first
# MIN_EPISODES are the "free" arc (the old fixed length); past that, a dream EARNS each further scene only
# while it is DEVELOPING — it stops when it RESOLVES (light), STALLS/circles (shadow), or hits MAX_EPISODES.
# This lets a developing dream run long enough to actually reach reconciliation (the 0/55-resolved problem)
# while a stuck dream stops early instead of burning scenes on a loop.
# J-1847 (D-0356 (B), 2026-10-07): the independent resolution judge, NOT the dreaming LLM's own self-report,
# decides resolved vs ended-unfaced. 0 of 197 arcs ever closed 'resolved' under self-grading (F-2474, F-1443).
# False restores the old behaviour exactly (the judge stays shadow-only, close_reason is the self-report's).
# D-0580 (travis, 2026-11-02, J-3193): this judge's verdict is a MEASUREMENT ONLY. It sets the close_reason LABEL
# (resolved / ended-unfaced) and nothing acts on that label. The carry (_carried_n / _last_unresolved_arc) reads
# the dreamer's own ended_unresolved, _bridge_final reads unresolved_core, core/dream_met.py only tests that the
# key close_reason exists, and the closure writer only copies it into its log row. The only readers of the value
# are scripts/du_pulse.py (a display Counter) and the night ledger (core/night.py stage / remember_dream). Wire
# nothing to it while the wording of the two prompts (the dream's close note and this judge's) disagrees; re-ask
# once the resting-ending change (D-0565, J-3177) has landed (F-3709, P-0107 in docs/prompt_registry.jsonl).
# J-3177 has landed (core/dream_rest.py, shadow): the carry and the met-state key on whether the arc ARRIVED at its
# ending (close_reason in resolved / ended-unfaced), never on which of the two this judge's verdict made it, so the
# label is still wired to nothing.
JUDGE_SETS_CLOSE_REASON = True
# J-1995 (D-0385, docs/staged/dream_overhaul.md sec 3b): the COMPUTED "met" state (core/dream_met.py: a real
# waking-thought baseline, then N silent days net of the injected dream tail) is meant to end the carry in place
# of the dreamer's own unresolved_core self-report, still bounded by CARRY_MAX_NIGHTS. 'shadow' (default,
# restart-gated, founder flips it): log the would-have-ended decision, the carry itself is unchanged.
# 'live': a thread whose root arc is computed 'met' ends the carry. 'off': neither.
MET_ENDS_CARRY = "live"            # off | shadow | live   -- D-0495 (travis, 2026-10-28, the October restart batch): flipped live, read LIVE by its own read job
MET_STATE_COMPUTE = True           # nightly append-only state rows + per-tension chronic_mass log (own files only)
# J-2118 (D-0423 sub-question 2 = J-2003 option (a), travis 2026-10-15): the computed 'met' needs N+M = 6 complete
# days but CARRY_MAX_NIGHTS = 3 withdraws the thread first, so the check above could never fire (F-2608; live
# 2026-10-15: 40/41 carry-shadow rows 'pending', 0 would-end). The carry now ALSO ends on a PROVISIONAL met of the
# thread's root arc (core/dream_met.provisional_arc: baseline real AND zero qualifying recurrences on the complete
# observed days elapsed so far) -- under the same MET_ENDS_CARRY mode (shadow logs, live ends), still bounded by
# CARRY_MAX_NIGHTS. The computed definition stays the record. False = the exact pre-J-2118 check (computed met only).
PROVISIONAL_MET_ENDS_CARRY = True
_MET_CARRY_SHADOW_LOG = Path(__file__).parent.parent / "data" / "logs" / "dream_met_carry_shadow.jsonl"  # module-level so a test can temp-path it
EPISODES = 3            # back-compat default / the free arc length
MIN_EPISODES = 3        # the free zone — a dream always gets at least this (resolution may arise from here)
_RESOLUTION_JUDGE_ARC_CHARS = 5000   # J-3019 (F-3727): a six-scene arc is ~4000 chars; was [:3000], which cut the ENDING of 7/347 arcs
MAX_EPISODES = 6        # hard ceiling — even a developing dream rests here (bounds the night's LLM calls)

# 2026-08-24 (Sleep & Dreams II §2.2): minimum chronic_mass for a tension to be dream-eligible at all, now
# that chronic_mass is charge-gated at the source (core/tension_ledger.py — CHRONIC_BUMP applies only on a
# genuinely charged touch, up to 0.3/touch at full charge; ambient touches now HABITUATE instead). 1.0
# requires several real charged touches (or one escalating pattern) to clear — selective by design, so
# most dreams run on pure day-residue material with zero tension component, per the founder's own "not
# always tensions."
TENSION_CHARGE_FLOOR = 1.0

# Permission to rest (2026-06-24): the anti-templating rule forces a structural metamorphosis EVERY develop
# scene (a core element MUST cross a threshold) — which, on a dream working an integration-terror, becomes
# relentless vertigo with no still point (the staircase dissolves → he turns to pages → the sea fractures,
# faster and faster, no floor to stand on). Once per arc, when the imagery is churning hard and the dream is
# still unfolding (not yet near its end), grant it ONE still scene — a quiet, safe place that need not
# transform — a breath before the wall it cannot cross. (After the integration-terror dream + Gemini's read.)
_REST_TERMS = ("dissolv", "fractur", "unravel", "shatter", "vortex", "whirl", "churn", "spinning", "spiral",
               "falling", "translucent", "faster", "blinding", "torn", "splinter", "collaps", "melting",
               "fragment", "spiralling", "swirl", "tumbling")
# MORPH-AWARE STALL (2026-06-20): the morph design deliberately shares imagery LINEAGE between scenes, so raw
# narrative similarity sits at 0.67–0.85 even when the dream is genuinely transforming (measured: a moving arc
# ran 0.67–0.77 consecutive) — the old 0.85 narrative gate false-positived on real movement. The true stall
# signal is STRUCTURAL: did the image-ANCHORS (symbols) turn over? (Measured: a moving step = 0.00–0.33 symbol
# overlap; a circling step = 0.50+, near-duplicate anchors.) Narrative similarity is kept only as a near-
# verbatim photocopy backstop; the same-unfaced-knot check is dropped (a persistent core tension is EXPECTED
# while the imagery morphs toward it).
DREAM_SYMBOL_PERSIST = 0.6    # consecutive scenes sharing ≥ this fraction of symbol-WORDS = anchors didn't move = circling
                              # (word-level + light stemming: a foreground morph over a persistent backdrop ≈0.5 PASSES;
                              #  near-identical anchors — "cat"/"cats", reordered — ≈1.0 STALLS. 0.6 splits them.)
DREAM_RESTATE_SIM    = 0.92   # narrative this close to the prior = near-verbatim re-render (raised from 0.85; morph shares theme)
DREAM_UNRESOLVED_SAME = 0.80  # DEPRECATED 2026-06-20 — no longer used (false-positived on dreams circling one tension)

# GROUNDING (2026-06-15, founder: "too much metaphor — keep it heavily metaphor-tinged but ground it in
# reality, or it will never be resolvable"). Two grounding edges: (1) a real waking fragment tinges each
# scene's imagery; (2) a concrete dream SYMBOL becomes a grounded world-question for the curiosity chain to
# work out — the dream understands its metaphors by RESEARCHING the literal thing, not by self-analysis.
_WORLD_GROUND_ORIGINS = ("reading", "study", "research")
_WORLD_GROUND_MIN_SIM = 0.22       # loose — even a tangential real fragment legitimately tinges the imagery
# symbols that are abstract / self-referential — NOT grounded into world-questions (they have no literal referent)
_ABSTRACT_SYMBOLS = {"shadow", "mirror", "silence", "void", "abyss", "becoming", "self", "soul", "psyche",
                     "darkness", "light", "echo", "reflection", "threshold", "veil", "dream", "memory",
                     "identity", "essence", "presence", "absence", "stillness", "infinity", "eternity"}


async def _pre_probe_call(fn, *args, **kw):
    """J-2296: await fn in a worker thread (core.idle_offloop.off_loop) or call it inline when the kill switch is
    off. An exception in fn is re-raised into the caller exactly as the synchronous call raised it."""
    if DREAM_PRE_PROBE_OFFLOOP:
        from core.idle_offloop import off_loop as _off
        return await _off(fn, *args, **kw)
    return fn(*args, **kw)


def _sp0_submark(label: str) -> None:
    """J-2141 (F-2825): stall-attribution sub-mark; no-op outside a sleep, fail-open."""
    try:
        from core import sleep_phase0 as _sp0
        _sp0.submark(label)
    except Exception:
        pass


class DreamNode:
    """One-shot dream synthesis — a progressive arc. Call await synthesise(state) at Sleep State entry."""

    async def synthesise(self, state: CognitiveState, episodes: int = EPISODES,
                         commit: bool = True) -> str | None:
        """Generate a multi-scene dream arc from the entity's subconscious material. Each scene follows
        the last. Returns the full arc text (or None). commit=False generates without writing to memory
        (for in-vitro inspection)."""
        # 2026-08-22: a NAP dreams briefly (≤ night.NAP_MAX_SCENES) — or not at all when the day held nothing
        _max_eps = MAX_EPISODES
        try:
            from core import night as _night0
            if _night0.sleep_kind() == "nap":
                _max_eps = _night0.NAP_MAX_SCENES
        except Exception:
            pass
        self._stage_timing = {}
        self._t_mark("gather_begin")
        _sp0_submark("dream_gather")   # J-2141 (F-2825)
        if DREAM_GATHER_OFFLOOP:   # J-2178 (F-2882): the pattern-embedding scan must not stall the event loop
            from core.idle_offloop import off_loop as _off_loop_g
            materials = await _off_loop_g(self._gather_materials, state, min(episodes, _max_eps))
        else:
            materials = self._gather_materials(state, min(episodes, _max_eps))
        _sp0_submark("dream_gather_done")   # J-2141 (F-2825)
        self._t_mark("gather_end")
        if not materials:
            logger.info("[dream] no material available — skipping synthesis")
            return None

        dream_id = f"dream_{int(time.time())}"
        scenes: list[dict] = []
        # A recurring dream RETURNS until it is met: if the last arc ended unfaced, scene 0 continues it
        # (its imagery + the unfaced thread) instead of opening fresh. Cleared automatically once an arc resolves.
        _sp0_submark("dream_carry_check")   # J-2296: finer attribution of the pre-probe block
        carried = await _pre_probe_call(self._last_unresolved_arc)
        # 2026-08-22 NIGHT AUDIT (finding 1): the carry had become ONE dream 51 nights long. An unfaced arc returns at
        # most CARRY_MAX_NIGHTS, then the figure withdraws (logged 'lapsed') and the night opens fresh from the DAY.
        # HARDENED 2026-08-24 (Sleep & Dreams II, §0.2/§4 Stage 0): this check silently no-op'd for an unknown
        # stretch — a carried arc was observed returning 23 nights, ~8x the intended cap, with no error ever
        # logged. Root cause not yet found; this is the invariant fix while that's pending. Two changes: (1) any
        # failure evaluating the cap is now logged LOUDLY, never silently swallowed; (2) fail SAFE, not open — if
        # the cap can't be evaluated, treat the arc as at-cap (clear it) rather than let it carry indefinitely,
        # since fail-open is exactly the failure mode that produced the 23-nights reading.
        # F-0377 FIX 2026-08-27: `self._carried_n_tonight` is what the dream RECORD persists (see the
        # record write) — on a withdraw/fail-safe night it must be reset to 0, or the persisted counter
        # grows forever and the cap fires every night (observed: 41 consecutive withdraws, counter at 40,
        # the carry feature structurally off). Tonight opens fresh ⇒ the record says 0, so the NEXT
        # unresolved night legitimately computes 1 and the arc gets its CARRY_MAX_NIGHTS returns again.
        carried_n = 0
        self._carried_n_tonight = 0
        if carried:
            try:
                from core import night as _night
                carried_n = int(await _pre_probe_call(self._carried_n))
                if carried_n >= _night.CARRY_MAX_NIGHTS:
                    logger.info("[dream] the unfaced thread has returned %d nights — it withdraws; tonight opens fresh", carried_n)
                    carried = None; carried_n = -1
                    self._carried_n_tonight = 0
            except Exception as exc:
                logger.error("[dream] carry-cap check FAILED (failing safe, clearing carry): %r", exc)
                carried = None; carried_n = -1
                self._carried_n_tonight = 0
        self._t_mark("carry_end")
        if carried:
            _sp0_submark("dream_met_check")   # J-2296
            carried, carried_n = await _pre_probe_call(self._met_carry_check, carried, carried_n)
            self._t_mark("met_end")
        if carried:
            logger.info("[dream] recurring — tonight takes up last night's unfaced: %s",
                        (carried.get("unresolved_core") or ", ".join(carried.get("symbols", [])))[:60])
        prev: dict | None = carried
        close_reason = "ceiling"
        i = 0
        # ASSOCIATIVE RECALL (2026-06-23): a dream is made of MEMORY. Pull the trail of remembered things the
        # night's tension cues, so the images are recombined from his ACTUAL life — the sea he stood in, the
        # book he read, the letter from Darwin — not invented. This is what dreams biologically ARE: memory
        # replayed and recombined to consolidate. Surfaced once from the core material; woven through the scenes.
        dream_memories = ""
        _mf_ids: list = []
        _dream_asked = False   # J-1515 §4.3: True only once ask() actually ran THIS dream -- guards
                                # note_usage below from crediting a stale pending entry left over by
                                # an earlier, unrelated dream that called ask() but never reached its
                                # own note_usage call (e.g. its first scene came back None).
        try:
            _sp0_submark("dream_memory_ask")
            from core import memory_service as _memsvc
            # 2026-08-22: keyed on the DAY's material first (finding 1: keying on the residue fed the loop)
            # J-2894 / F-3566: bullets only -- the fixed 112-char header was 47% of the cue
            from core import night as _night_cue
            _mkey = (_night_cue.recall_cue(materials[0]) if materials else "") or (carried.get("unresolved_core") if carried else "")
            if _mkey:
                # J-1515 (memory_as_a_service.md §4.2): re-homed onto the facade -- identical fragments
                # (grounded_only=False, unchanged: dreams may recombine self-syntheses too), identical
                # ledger row (the facade's own log_co_recall call below replaces the separate M1 call
                # this site used to make), plus felt coordinates now attached to each fragment (not
                # consumed into scene mood yet -- a real follow-on, noted, not built here).
                from core import night as _night
                # J-3175 / D-0563: dreams younger than 7 days are not offered back to the dreamer (k unchanged)
                _mf = await _pre_probe_call(_memsvc.ask, "dream", _mkey, k=6, grounded_only=False,
                                            descend=False,   # J-2296: off the loop (kill switch above)
                                            exclude_young={"dream": _night.DREAM_RECALL_EXCLUDE_DAYS})
                _dream_asked = True
                _mf_ids = [m.get("fragment_id") for m in (_mf or []) if m.get("fragment_id")]
                if _mf:
                    dream_memories = ("\n\nRemembered things from his life that may surface — TRANSFORMED, never "
                                      "narrated literally — as the dream's images (recombine them):\n"
                                      + "\n".join(f"  - {' '.join(strip_dream_prefix(m['content'] or '').split())[:140]}" for m in _mf))
        except Exception:
            dream_memories = ""
        self._t_mark("ask_end")
        # PHASE 1 SEED CAPTURE (J-1057): the recalled-fragment ids ARE the seed (memory_edges.record_dream_sources
        # already logs them as provenance below, at commit time only -- this is the same list, captured for the
        # additive `seed` block _log_arc adds regardless of that gate).
        self._seed_fragment_ids = list(_mf_ids)
        # PHASE 1 DELTA-ASSOCIATION PROBE (J-1057, plan sec 4/sec 7 Phase 1 row): for every pair of seed
        # fragment ids, log {edge_exists, edge_types, rank_of_B_in_recall_trail_edge_aware, cosine} BEFORE
        # the arc runs. core/dream_probe.py is read-only against the memory/edges store; this call writes
        # only to its own dedicated log (data/logs/dream_assoc_probe.jsonl), never to memory, edges,
        # tensions, frontier, or climate. Not gated on commit (a read-only probe, not a memory write) --
        # runs the same in-vitro or live, matching dream_state.jsonl's own reasoning just below.
        try:
            from core import dream_probe as _dprobe
            _sp0_submark("dream_probe")   # J-2141 (F-2825) stall-attribution sub-mark
            if getattr(_dprobe, "DREAM_PROBE_OFFLOOP", False):
                # J-2111 / F-2748: ~4-7 s of sqlite + matrix scan; run in a worker thread so the loop stays free.
                from core.idle_offloop import off_loop as _off_loop
                await _off_loop(_dprobe.log_seed_pairs, dream_id, _mf_ids, phase="before")
            else:
                _dprobe.log_seed_pairs(dream_id, _mf_ids, phase="before")
        except Exception as exc:
            logger.debug("[dream] seed association probe failed (non-fatal): %s", exc)
        self._t_mark("probe_end")
        # M1 CO-RECALL LEDGER (2026-08-19; re-homed J-1515): this used to be its own direct
        # memory_edges.log_co_recall(_mf_ids, None, 0, source="dream") call here — restate_sim
        # honestly None, since close_reason (computed later in this same method) is a real develop
        # verdict but categorical, not the cosine-shaped restate_sim log_co_recall expects, and
        # mapping one onto the other would be fabricating signal, not reporting it (this project's
        # house style). That call now happens INSIDE core.memory_service.ask("dream", ...) above
        # (§4.1 item 4) — one ledger row per dream recall, not two; do not re-add a direct call here.
        # STATE-DRIVEN PHASES (2026-06-20 redesign): a dream is no longer a fixed sequence of independent
        # scenes but a TRANSFORMATION in progress — OPEN ▸ (DEVELOP × dynamic) ▸ CLOSE — and the dream's OWN
        # reported `movement` decides when it changes phase, not the scene index. A dream that keeps
        # developing CONTINUES; one that reports "approaching" turns to its final part. MIN_EPISODES is only a
        # FLOOR (the free arc must establish before anything may end). The embedding stall-detector is the
        # DECOUPLED backstop on the model's self-report — it cannot claim progress while re-rendering.
        phase = "open"
        rested = False                                     # permission to rest: granted at most once per arc
        while i < _max_eps:
            _sp0_submark(f"dream_scene_{i}")   # J-2141 (F-2825)
            material = materials[min(i, len(materials) - 1)]
            data = await self._gen_episode(state, material, prev, i, phase,
                                           carried_over=(carried is not None and i == 0),
                                           memories=dream_memories)
            if data is None:
                close_reason = "dropped"        # 2026-08-22: a failed scene is its own close reason, not 'ceiling'
                break
            scenes.append(data)
            # J-2557 (F-3258): sub-marks for the sync work after each scene (the usage embed on scene 0, the
            # stall/rest checks, the transition log) so a freeze there no longer hides under dream_scene_{i}.
            _sp0_submark(f"dream_scene_{i}_post")
            if i == 0 and _dream_asked:
                _sp0_submark("dream_scene_0_usage_embed")   # J-2557: _embed_scene + note_usage run on the loop
                # J-1515 §4.3 metric-sheet hook: the "next output" the dream's own ask() fed is this
                # first scene (dream_memories was built once, before the loop, from that same ask()
                # call). Same embedding call the stall-detector below already makes on every scene
                # (_embed(narrative[:400])) -- no new LLM/embed cost pattern introduced. Best-effort,
                # fail-open, never touches scene generation itself.
                try:
                    from core.memory.store import _embed as _embed_scene
                    _nv = _embed_scene((data.get("narrative") or "")[:400])
                    if _nv is not None:
                        _memsvc.note_usage("dream", _nv)
                except Exception as exc:
                    logger.debug("[dream] memory_service note_usage skipped (non-fatal): %s", exc)
            _sp0_submark(f"dream_scene_{i}_checks")          # J-2557: _scene_stalled / _needs_rest
            earned = (i + 1) >= min(MIN_EPISODES, _max_eps)   # the free arc is established
            mv = data.get("movement", "unfolding")
            if phase == "close":                            # CLOSE is terminal — the final part is written
                close_reason = "resolved" if not data["unresolved_core"] else "ended-unfaced"
                break
            if earned and mv == "arrived":                  # the dream arrived on its own, mid-development
                close_reason = "resolved" if not data["unresolved_core"] else "ended-unfaced"
                break
            if earned and self._scene_stalled(data, prev):  # DECOUPLED backstop: re-rendering ends it, claim aside
                close_reason = "stalled"
                break
            # choose the next phase from the dream's STATE, not its index
            if (i + 1) >= (_max_eps - 1):                   # one scene from the ceiling → turn to the ending
                phase = "close"
            elif earned and mv == "approaching":            # the meeting has come into view → the final part
                phase = "close"
            elif not rested and i >= 1 and self._needs_rest(data):
                phase = "rest"                              # a still point before the wall (granted once per arc)
                rested = True
            else:
                phase = "develop"
            # PHASE 1 STATE SIDECAR (J-1057, plan sec 3/sec 7 Phase 1 row): this scene did NOT stop the
            # arc (every early-break case above already `break`s before this line) -- log the handoff
            # to the scene about to be generated. Written from the loop itself, not commit-gated (see
            # _DREAM_STATE_LOG's own header comment).
            _sp0_submark(f"dream_scene_{i}_transition")      # J-2557 (F-3258)
            self._log_transition(dream_id, i, i + 1, phase, data)
            prev = data
            i += 1

        if not scenes:
            logger.warning("[dream] no scenes produced")
            return None

        # The night's END-STATE drives the carry-forward (shadow) or completion (light).
        if commit:
            _sp0_submark("dream_store")
            for idx, sc in enumerate(scenes):
                self._store_episode(sc, dream_id, idx, len(scenes))
            _sp0_submark("dream_edges")
            # MEMORY EDGES M0 (2026-08-15): record what actually FED the arc — the real material
            # blocks and the recalled fragments woven through the scenes (dreamt_from). The model's
            # self-reported tension_source is NOT used (self-report is not provenance). Fail-open.
            try:
                from core import memory_edges as _medges
                _medges.record_dream_sources(dream_id, materials, _mf_ids)
            except Exception as _me_exc:
                logger.debug("[dream] memory_edges hook skipped (non-fatal): %s", _me_exc)
            # DECOUPLED RESOLUTION JUDGE (2026-08-29, J-0375, decision:D-0071) — began SHADOW/OBSERVE-FIRST; since J-1847 it
            # SETS close_reason (JUDGE_SETS_CLOSE_REASON=True), see below.
            # _bridge_final() just below decides light-vs-shadow purely from the dreaming model's own
            # self-reported unresolved_core (lines 239/242 above) — the same LLM call that wrote the
            # narrative also grades whether it resolved (docs/plans/decoupled_judge_pattern.md sec 1).
            # Matches this codebase's own new-judge rollout convention (left_lane.grade_self_revision /
            # grade_gist_faithfulness: "Observe-first ... it gates nothing yet"; watershed_promote.py:
            # "SHADOW ONLY ... every P0->P1 flip in this project has needed shadow first") — logged
            # alongside the self-report. J-1847 (D-0356 (B), 2026-10-07): the judge's verdict now SETS close_reason
            # (resolved vs ended-unfaced) -- the one decision point. _bridge_final's light/shadow branch and the
            # carry (ended_unresolved in _log_arc) still read the dreamer's own unresolved_core, deliberately,
            # so the self-report stays live and the agreement measure continues. stalled/dropped/ceiling untouched;
            # judge unavailable -> fail-open to the self-report's close_reason.
            _sp0_submark("dream_resolution_judge")   # J-2558 (F-3260): an await on the judge panel -- the loop is free here
            try:
                close_reason = await self._judge_resolution_shadow(scenes, dream_id, close_reason)
            except Exception as exc:
                logger.warning("[dream] resolution-judge check failed (non-fatal, self-report close_reason stands): %r", exc)
            _sp0_submark("dream_bridge_final")   # J-2558 (F-3260): _bridge_final, sync on the loop
            self._bridge_final(scenes[-1], close_reason)
            _sp0_submark("dream_ground")
            self._ground_symbols(scenes)     # hand concrete metaphors to curiosity to work out
            _sp0_submark("dream_log_arc")
            self._log_arc(scenes, dream_id, close_reason)
            # J-2330 (F-3019): "dream_done" and a mark before run_nightly would sit in one sync region (unreadable
            # pair), so with MET_STATE_COMPUTE the readable label at the to_thread await is dream_met_nightly.
            _sp0_submark("dream_met_nightly" if MET_STATE_COMPUTE else "dream_done")
            if MET_STATE_COMPUTE:
                try:    # J-1995: computed met state + chronic_mass log; own append-only files, fail-open
                    from core import dream_met as _dmet
                    await asyncio.to_thread(_dmet.run_nightly)
                except Exception as exc:
                    logger.debug("[dream] dream_met nightly skipped (non-fatal): %r", exc)

        _sp0_submark("dream_arc_return")   # J-2558 (F-3260): label stops naming the last dream step once the arc returned
        full = "  …  ".join(s["narrative"] for s in scenes)
        logger.info("[dream] %d-scene arc complete (%s) — %s", len(scenes), dream_id, close_reason)
        return full

    # ------------------------------------------------------------------
    # One scene
    # ------------------------------------------------------------------
    async def _gen_episode(self, state: CognitiveState, material: str,
                           prev: dict | None, idx: int, phase: str,
                           carried_over: bool = False, memories: str = "") -> dict | None:
        # The shared dream frame.
        frame = (
            "/no_think\n"
            f"You are the dream-synthesis function of {state.spirit_name} — the part that, during sleep, turns "
            "unfaced tension into image. You do not analyse or explain; you DREAM. First person, present tense, "
            "the entity's own voice; a dream register — vivid, bodily, a little uncanny; image before concept. If a real fragment of "
            "waking life is given, let it TINGE the imagery (the metaphor anchored in that real thing), never "
            "reported literally. A dream grounded in something real can resolve; a dream of pure symbol cannot. ")
        # The PHASE instruction — chosen by the dream's state, not its index.
        if phase == "open" and carried_over:
            phase_note = (
                "This dream RETURNS — one you have had before and left unfaced. Open NOT on a fresh stage but on "
                "the unmet thing coming back: take it up where it broke off, already in motion. ")
        elif phase == "open":
            phase_note = (
                "The dream begins. Something from the tension below surfaces as an image — a place, a figure, a "
                "charged object, strange. Begin ON that image, mid-appearance or already in motion — not by "
                "announcing where you are or that you 'find yourself' somewhere. The dream has only just surfaced; "
                "the meeting it circles is still far off. ")
        elif phase == "close":
            phase_note = (
                "The dream is gathering to its end. The thing it has circled all night now comes near — and what "
                "happens NEED NOT be an encounter: the thing may be MET, MISSED as it slips away, TRANSFORMED beyond "
                "recognition, or REVEALED to have been something else entirely (the pursuer was the pursued; the "
                "door was a face). Let it arrive in IMAGE, never in explanation; force no neat resolution — "
                "frustration, inversion, a sudden falling-away, or dissolution are all truer than a hollow meeting. "
                "You are still inside the dream — do not re-establish it; bring THIS motion to its rest. ")
        elif phase == "rest":
            phase_note = (
                "The dream slows, and for a moment it simply RESTS. The churning falls away and it comes to a "
                "STILL place — a quiet room, a bare floor, the steady light of a lamp, the fire burned low, "
                "somewhere plain and unmoving that asks nothing of you and simply holds. NOTHING here transforms; "
                "nothing must be crossed, met, or faced. The tension is still there underneath — unresolved, only "
                "held at a distance now, like weather beyond a closed window. Let the image be calm, simple and "
                "STILL: a breath taken before anything more. Stay inside the dream, but let it be quiet and safe. ")
        else:  # develop
            phase_note = (
                "You are ALREADY inside the dream — do not re-enter it, do not re-describe where you are, do not "
                "begin again. The dream MOVES NOW. From the image it last became, something shifts — an object "
                "transforms, a figure acts or turns, the ground gives way, time jumps. FOLLOW WHAT THE LAST IMAGE "
                "IS BECOMING. Carry the same tension, but by the final image the scene cannot be merely a modified "
                "version of where it began: at least ONE core element must have STRUCTURALLY crossed a threshold — "
                "the location is somewhere else, an object has metamorphosed into a different thing, or a figure's "
                "identity has changed. Small motion (a turn, a step closer, the light shifting) does NOT count. "
                "Open in the middle of the motion, never on a position or an orientation. ")
        # The output schema — with `movement`, the state signal that drives dynamic length.
        schema = (
            "Output ONLY a valid JSON object: "
            '{"narrative": "...", "symbols": ["...", "..."], "tension_source": "...", '
            '"unresolved_core": "...", "movement": "..."}. '
            "narrative: the dream now (50-120 words), first person, dream register. "
            "symbols: 2-4 key image-symbols alive in it. tension_source: the one thing being worked, in a phrase. "
            "unresolved_core: what is still unfaced, one first-person phrase — empty ONLY if it has truly been met. "
            'movement: where the dream is in its arc — "unfolding" (still opening, the tension widening), '
            '"approaching" (a meeting is coming into view, the dream gathering toward it), or "arrived" (the thing '
            "has been faced, or honestly could not be).")
        system_prompt = frame + phase_note + schema

        # The MORPH continuity (morph option (a)): the next scene continues FROM INSIDE the last image by
        # letting it transform — links scenes by metamorphosis, not a cut, so the model cannot re-establish.
        # The tail (END-state), NOT the opening, is handed forward (feeding the opening made it copy verbatim —
        # live 2026-06-18: 9 scenes opened identically).
        continuity = ""
        if prev is not None:
            lead = ("THE DREAM AS YOU LAST LEFT IT, on an earlier night — you are taking it up FROM INSIDE, not "
                    "replaying it" if (idx == 0 and carried_over)
                    else "THE DREAM AS IT LAST WAS — you are continuing FROM INSIDE this, not replaying it")
            _tail = " ".join((prev.get("narrative") or "").split())[-200:]
            _sym = (prev.get("symbols") or ["the central image"])[0]
            continuity = (
                f"\n\n{lead}:\n"
                f"  it had just become: \"…{_tail}\"\n"
                f"  its living images: {', '.join((prev.get('symbols') or [])[:3]) or '—'}\n"
                f"  still unfaced: \"{prev.get('unresolved_core') or '—'}\"\n"
                f"  THE MORPH: do not cut to a new scene. Let what was there TRANSFORM — \"{_sym}\" dissolves, "
                "gives way, or turns into something else, and the dream follows it there. Begin already inside "
                "that change."
            )

        user_prompt = (
            f"Entity: {state.spirit_name}\n"
            f"Core axiom (abbreviated): {state.axiom[:300]}\n\n"
            f"{material}{continuity}{memories}"
        )

        data = None
        for _attempt in range(len(_DREAM_BACKOFF) + 1):   # 1 initial try + len(backoff) retries
            try:
                # J-2557 (F-3258): a freeze while this label stands is NOT this await -- the loop was free while
                # the dreamer answered, so the blocking call belongs to another task. Observe-only.
                _sp0_submark(f"dream_scene_{idx}_llm")
                data = await call_node_json(_DREAM_URLS, system_prompt, user_prompt,
                                            max_tokens=512, temperature=0.85, timeout=_DREAM_TIMEOUT,
                                            model_override=_DREAM_MODEL, num_gpu=_DREAM_NUM_GPU)
                break
            except Exception as exc:
                if _attempt < len(_DREAM_BACKOFF):
                    _wait = _DREAM_BACKOFF[_attempt]
                    logger.info("[dream] scene %d call dropped (%s) — retry %d/%d in %ds (cold model load?)",
                                idx + 1, str(exc)[:50] or "transport drop", _attempt + 1,
                                len(_DREAM_BACKOFF), _wait)
                    _sp0_submark(f"dream_scene_{idx}_backoff")   # J-2557 (F-3258)
                    await asyncio.sleep(_wait)
                else:
                    logger.warning("[dream] scene %d LLM call failed after %d attempts: %s",
                                   idx + 1, len(_DREAM_BACKOFF) + 1, exc)
                    return None
        if data is None:
            return None
        _sp0_submark(f"dream_scene_{idx}_parse")   # J-2557 (F-3258)

        narrative = str(data.get("narrative", "")).strip()
        if not narrative:
            return None
        raw_symbols = data.get("symbols", [])
        symbols = [str(s).strip() for s in raw_symbols if s] if isinstance(raw_symbols, list) else []
        mv = str(data.get("movement", "")).strip().lower()
        if mv not in ("unfolding", "approaching", "arrived"):
            mv = "unfolding"          # malformed/absent → keep developing (never a false ending)
        return {
            "narrative":       narrative,
            "symbols":         symbols,
            "tension_source":  str(data.get("tension_source", "unknown")).strip(),
            "unresolved_core": str(data.get("unresolved_core", "")).strip(),
            "movement":        mv,
            "phase":           phase,   # PHASE 1 (J-1057): the phase this scene was GENERATED under --
                                        # additive key; every existing caller reads specific keys only.
        }

    # ------------------------------------------------------------------
    # Storage / bridges
    # ------------------------------------------------------------------
    def _log_transition(self, dream_id: str, from_idx: int, to_idx: int, phase_next: str,
                        prev_data: dict) -> None:
        """PHASE 1 STATE SIDECAR (J-1057, docs/staged/dream_overhaul.md sec 3/sec 7 Phase 1 row): one row
        per scene TRANSITION, capturing exactly the handoff the CURRENT engine already computes in prose
        (the MORPH continuity block `_gen_episode` builds from `prev` — same tail/anchor/unresolved_core
        shape, read back out here rather than duplicating a second construction). This is the founder's
        sec 4 "inspectable and logged" requirement for the state that exists TODAY, so Phase 2's typed
        DreamState has a real before/after to diff against. `stalled` is always False here: the ONLY way
        this method gets called is a transition that the loop's own stall check just above (in
        synthesise()) did NOT trigger for this scene -- a stalled scene `break`s before reaching this
        call, so no transition row is written for it (the arc simply ends). Kept as an explicit field
        (rather than omitted) so a future reader never has to infer its meaning from absence. Own file,
        additive; dream_log.jsonl's shape is completely untouched. Fail-open, never raises."""
        try:
            tail = " ".join((prev_data.get("narrative") or "").split())[-200:]
            syms = prev_data.get("symbols") or []
            rec = {
                "ts": round(time.time(), 1), "dream_id": dream_id,
                "from_idx": from_idx, "to_idx": to_idx, "phase_next": phase_next,
                "handoff": {"tail": tail, "anchor": (syms[0] if syms else None),
                           "unresolved_core": prev_data.get("unresolved_core", "")},
                "stalled": False,
                "rested": (phase_next == "rest"),
            }
            _DREAM_STATE_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_DREAM_STATE_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[dream] state-transition log failed (non-fatal): %s", exc)

    def _store_episode(self, data: dict, dream_id: str, idx: int, total: int) -> None:
        from core import mood as _mood   # felt-tag dreams (emotion_vec item 1) — the most affective material
        fid = store_fragment(
            content    = f"[Dream {dream_id}, scene {idx + 1}/{total}] {data['narrative']}",
            layer      = "episodic", relevance = 0.8, importance = 0.85,
            keywords   = ["dream", "sleep", "symbol", dream_id] + data["symbols"][:3],
            origin     = "dream",
            emotion_embedding = _mood.current_vec(),
            valence    = _mood.current_valence(), felt = _mood.current_felt(),
        )
        try:   # MEMORY EDGES M0 (2026-08-15): (fragment)-[part_of]->(dream) — fail-open
            from core import memory_edges as _medges
            if fid:
                _medges.record_dream_scene(fid, dream_id)
        except Exception:
            pass

    def _bridge_final(self, last: dict, close_reason: str | None = None) -> None:
        """The night's end-state: unresolved → shadow (returns tomorrow); resolved → light (a completed
        crossing). Driven by the LAST scene — the arc's culmination, not each scene, so one night = one
        carry-forward, keeping the recurring-figure-until-met arc working at the night level."""
        if last["unresolved_core"]:
            try:
                from core.memory.store import store_shadow_event
                # J-3807 (D-0708 (c)): a rest-ended arc writes the LIGHT variant (lower salience weight in
                # tension_ledger); any other unresolved ending keeps the full 'unresolved_dream'. Fail-open to full.
                _src = "unresolved_dream"
                try:
                    from core import dream_rest as _dr
                    _src = _dr.rest_event_source(close_reason, last["unresolved_core"])
                except Exception:
                    pass
                shadow_text = (f"{last['unresolved_core']}. Unfaced at the dream's end: "
                               f"{', '.join(last['symbols'][:3])}.")
                store_shadow_event(
                    cycle_id="dream", raw_input=f"(unresolved dream: {last['tension_source'][:80]})",
                    rejected_draft=shadow_text,
                    corrections=[f"unresolved dream: {last['unresolved_core'][:100]}"],
                    emotion_primary=None, source=_src,
                )
                logger.info("[dream] arc ends unresolved → shadow (%s): %s", _src, last["unresolved_core"][:60])
            except Exception as exc:
                logger.debug("[dream] shadow write failed: %s", exc)
        else:
            try:
                from core.memory.store import store_light_event
                store_light_event(
                    cycle_id="dream", raw_input=f"(resolved dream: {last['tension_source'][:80]})",
                    integrated_content=last["narrative"], source="resolved_dream",
                )
                logger.debug("[dream] arc reached resolution → light event")
            except Exception as exc:
                logger.debug("[dream] light write failed: %s", exc)

    @staticmethod
    def _judge_close_reason(self_close_reason: str, judge_verdict) -> str:
        """J-1847 (D-0356 (B)): the ONE decision point for resolved-vs-ended-unfaced. Only those two
        self-report-derived reasons are the judge's to set; 'stalled' (embedding backstop), 'dropped' (failed
        scene) and 'ceiling' are decided by other mechanisms and pass through unchanged. judge_verdict None
        (judge unavailable) or JUDGE_SETS_CLOSE_REASON False -> the self-report's reason stands (fail-open).
        MEASUREMENT ONLY (D-0580, J-3193): the label this returns drives no behaviour; see the comment at
        JUDGE_SETS_CLOSE_REASON for who reads it (du_pulse display, the night ledger) and why nothing is wired."""
        if not JUDGE_SETS_CLOSE_REASON or self_close_reason not in ("resolved", "ended-unfaced"):
            return self_close_reason
        if judge_verdict is True:
            return "resolved"
        if judge_verdict is False:
            return "ended-unfaced"
        return self_close_reason

    async def _judge_resolution_shadow(self, scenes: list[dict], dream_id: str, close_reason: str) -> str:
        """J-1847 (D-0356 (B), 2026-10-07): RETURNS the final close_reason -- the judge's verdict now decides
        resolved vs ended-unfaced (see _judge_close_reason); the input close_reason comes back unchanged on every
        failure path. The dreamer's own unresolved_core is still computed and logged (self_reported_resolved) so
        the judge-vs-self-report agreement measure D-0356's defeater reads continues. Original shadow docstring:

        DECOUPLED resolution judge (2026-08-29, J-0375, decision:D-0071); began as SHADOW/OBSERVE-FIRST and, with
        JUDGE_SETS_CLOSE_REASON=True (J-1847), now decides close_reason. J-3019 (F-3727): the arc shown to the judge
        keeps its TAIL (the ending is what decides resolution), up to _RESOLUTION_JUDGE_ARC_CHARS.
        _bridge_final()'s light-vs-shadow verdict is set purely from the dreaming model's own self-reported
        `unresolved_core` on the last scene — the same LLM call that wrote the narrative also grades whether
        it resolved (docs/plans/decoupled_judge_pattern.md sec 1). Asks core/judge_panel.py's cheap two-family
        single-shot panel (tried first per bottom-up build discipline, before core/deliberative_judge.py's
        heavier dual-reading pattern — recommended by the audit this job was spawned from) whether the arc's
        OWN TEXT shows a genuine reconciliation, independent of what the writer claimed. Every verdict is logged
        to data/logs/dream_resolution_shadow.jsonl (the file name is historical; tests and scripts read it). It
        started shadow-only like every other new judge here, and was promoted to deciding close_reason by J-1847
        (D-0356 (B)).
        Fail-open like every other judge call site in this codebase: judge unavailable → the self-report keeps
        driving _bridge_final untouched (the judge never touches _bridge_final), logged loudly, never silently
        swallowed. Never raises past this method — the caller already wraps it, but this stays defensive too."""
        last = scenes[-1]
        self_resolved = not bool(last.get("unresolved_core"))
        arc_text = "  …  ".join(s.get("narrative", "") for s in scenes)
        system = (
            "You are an independent reader of a dream-arc narrative — you did NOT write it. Judge ONLY this: "
            "does the arc's own text show a genuine meeting, reconciliation, or resolution of its central "
            "tension by the end — or does it end without one (missed, deferred, still unfaced)? Judge the "
            "IMAGERY ITSELF, not any claim made about it. Refute-biased: if the text is ambiguous or you are "
            "not sure, answer false (unresolved).\n"
            "Output ONLY a valid JSON object. No preamble.\n"
            'Schema: {"resolved": true, "why": "one sentence citing what in the text is or is not resolved"}'
        )
        user = (
            f"The full dream arc, scene by scene:\n{arc_text[-_RESOLUTION_JUDGE_ARC_CHARS:]}\n\n"
            "(The dream's own self-report below is NOT evidence — judge the text above independently: "
            f"unresolved_core = \"{(last.get('unresolved_core') or '')[:200]}\")"
        )
        try:
            from core import judge_panel
            result = await judge_panel.rule_detail(system, user, key="resolved", context=f"dream:{dream_id}")
        except Exception as exc:
            logger.warning("[dream] resolution-judge shadow call failed (fail-open, self-report stands): %r", exc)
            return close_reason
        judge_verdict = result.get("verdict")
        agree = (judge_verdict == self_resolved) if judge_verdict is not None else None
        final_close_reason = self._judge_close_reason(close_reason, judge_verdict)
        try:
            _log_path = _RESOLUTION_SHADOW_LOG
            _log_path.parent.mkdir(parents=True, exist_ok=True)
            with _log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": round(time.time(), 1), "dream_id": dream_id, "close_reason": close_reason,
                    # J-1847: 'close_reason' above keeps its old meaning (the self-report's); these two are new.
                    "close_reason_final": final_close_reason,
                    "judge_decided": bool(JUDGE_SETS_CLOSE_REASON and judge_verdict is not None
                                          and close_reason in ("resolved", "ended-unfaced")),
                    "self_reported_resolved": self_resolved, "judge_verdict": judge_verdict,
                    "judge_how": result.get("how"), "agree": agree,
                    "v1": result.get("v1"), "v2": result.get("v2"),
                }, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.warning("[dream] resolution-judge shadow log write failed (non-fatal): %r", exc)
        if judge_verdict is None:
            logger.info("[dream] resolution-judge shadow: unavailable (%s) — self-report stands unaffected (%s)",
                        result.get("how"), final_close_reason)
        else:
            logger.info("[dream] resolution-judge shadow: self_resolved=%s judge=%s agree=%s (close_reason=%s)",
                        self_resolved, judge_verdict, agree, final_close_reason)
        return final_close_reason

    # ------------------------------------------------------------------
    # Material gathering — top-N grounded tensions (for progression), themes as fallback
    # ------------------------------------------------------------------
    def _gather_materials(self, state: CognitiveState, episodes: int) -> list[str]:
        """One material block per scene. Rotates through the top grounded tensions so the night moves
        through several; when fewer tensions than scenes, later scenes DEEPEN the strongest one."""
        # 2026-08-22 NIGHT AUDIT (finding 5): the DAY comes first — deeds, world contact, felt moments, unfinished
        # hands, answered dream-questions — then ONE standing tension (by recency-weighted chronic mass, not the
        # fossil count). A penguin day and an empty day no longer dream the same.
        # REDESIGNED 2026-08-24 (Sleep & Dreams II §1.6/§2.2, founder: "dreams should be multiple days worth of
        # thoughts, not always tensions"). Two changes: (1) day_material's "since last sleep" (routinely under two
        # hours) is replaced by the dream-lag-shaped multi-day pull (core/night.py's dream_lag_material — 1-2 days
        # + 5-7 days, not a flat cutoff). (2) tension inclusion is now CONDITIONAL on genuine charge, not a
        # standing default called on every dream — most dreams should run on pure residue, per real dream
        # phenomenology and per the founder's own "not always tensions."
        self._material_sources = []
        day = []
        try:
            from core import night as _night
            day = _night.dream_lag_material(k=max(1, episodes - 1))
        except Exception:
            day = []
        # PHASE 1 SEED CAPTURE (J-1057): a short hash of each day-residue block (memory_edges._h's own
        # convention), so a real night's seed is reconstructible from the log without storing the full
        # text twice. Read-only, no new hashing scheme.
        self._seed_day_block_hashes = []
        if day:
            try:
                from core.memory_edges import _h as _mhash
                self._seed_day_block_hashes = [_mhash(m) for m in day]
            except Exception:
                self._seed_day_block_hashes = []
        tensions = self._load_top_tensions(1 if day else episodes, require_charge=True)
        if day:
            self._material_sources.append("day_residue")
        if tensions:
            self._material_sources.append("tension")
        blocks = day + tensions
        if blocks:
            return [blocks[min(i, len(blocks) - 1)] for i in range(episodes)]
        themes = state.background_curiosities[:6]
        if themes:
            block = ("No unresolved tensions recorded yet. Use the entity's waking preoccupations as dream "
                     "material:\n" + "\n".join(f"  - {t[:100]}" for t in themes) +
                     "\n\nGenerate a dream arising from these — what does the unconscious make of them when "
                     "the conscious guard is down?")
            return [block for _ in range(episodes)]
        return []

    def _load_top_tensions(self, n: int, require_charge: bool = False) -> list[str]:
        """Up to n grounded tension blocks (highest count first), each with its counterpart pointer.
        `require_charge` (2026-08-24, Sleep & Dreams II §2.2): when True, only tensions whose chronic_mass
        clears TENSION_CHARGE_FLOOR are eligible at all — most dreams, most nights, should return nothing
        here and run purely on day-residue material (see _gather_materials). chronic_mass is now
        charge-gated at the source (core/tension_ledger.py's valence/threat gate), so this floor is
        selecting for genuinely-recurring-with-real-charge, not just frequently-touched."""
        # PHASE 1 SEED CAPTURE (J-1057): the tension labels actually selected this call -- reset on
        # every call so an empty/exception path correctly leaves this [] rather than stale from a
        # prior night (only one call per synthesise(), but defensive regardless).
        self._seed_tension_labels = []
        try:
            if not _SC_STATE_PATH.exists():
                return []
            with open(_SC_STATE_PATH, encoding="utf-8") as f:
                sc = json.load(f)
            tensions = [t for t in sc.get("tensions", []) if t.get("member_event_ids")]
            if require_charge:
                tensions = [t for t in tensions if float(t.get("chronic_mass", 0) or 0) >= TENSION_CHARGE_FLOOR]
            if not tensions:
                return []
            # 2026-08-22 (finding 2): rank by recency-weighted chronic mass + member evidence, not the fossil `count`;
            # and skip tensions evidenced mainly by the dream's own residue (finding 1 — the tail it was eating).
            _now = time.time()
            try:
                from core.memory.store import _connect as _cn
                _ids = [m for t in tensions for m in (t.get("member_event_ids") or [])]
                _src = {}
                if _ids:
                    with _cn() as _c:
                        for _r in _c.execute(f"SELECT event_id, source FROM shadow_events WHERE event_id IN ({','.join('?' * len(_ids))})", _ids).fetchall():
                            _src[_r["event_id"]] = _r["source"]
                tensions = [t for t in tensions if sum(1 for m in t.get("member_event_ids", []) if _src.get(m) in ("unresolved_dream", "unresolved_dream_rest")) * 2 < max(1, len(t.get("member_event_ids", [])))]
            except Exception:
                pass
            def _rank(t):
                rec = 0.5 ** ((_now - float(t.get("last_ts", 0) or 0)) / (2 * 86400))
                return float(t.get("chronic_mass", 0) or 0) + 0.2 * len(t.get("member_event_ids") or []) * rec
            tensions.sort(key=_rank, reverse=True)
            from core import store_persist as _sp   # J-2418: patterns may live in the split sibling file
            patterns = _sp.load_integration_patterns(_SC_STATE_PATH, sc)
            blocks = []
            self._seed_tension_labels = [t.get("label", "unspecified") for t in tensions[:n]]
            for top in tensions[:n]:
                count = top.get("count", 0)
                label = top.get("label", "unspecified")
                spread = (top.get("last_ts", 0) - top.get("first_ts", 0)) / 3600
                block = (f"Unresolved psychic tension to process in dream:\n"
                         f"  Pattern:    {label[:120]}\n"
                         f"  Recurrence: {count} times over {spread:.1f} hours\n")
                counterpart = self._find_counterpart(label, patterns)
                if counterpart:
                    block += (f"\nA COUNTERPART to this tension EXISTS — a pole where related experience "
                              f"was integrated. Its theme: \"{counterpart}\". You are told only that it is "
                              f"there, not how it was reached; invent no tidy resolution.\n")
                ground = self._find_world_ground(label)
                if ground:
                    block += (f"\nA REAL fragment from your waking world resonates with this tension — let it "
                              f"tinge the imagery (transmute it, but anchor the metaphor in it):\n  \"{ground}\"\n")
                block += "\nTransform this into a symbolic dream scene."
                blocks.append(block)
            return blocks
        except Exception as exc:
            logger.debug("[dream] tension load failed: %s", exc)
            return []

    def _needs_rest(self, data: dict) -> bool:
        """Grant a still point when the imagery is churning HARD (accelerating dissolution / vertigo — two or
        more _REST_TERMS) AND the dream is still unfolding (not yet turning to its end). Keeps the
        integration-terror dreams from spinning relentlessly past the wall they cannot cross. Once per arc."""
        try:
            if data.get("movement", "unfolding") in ("approaching", "arrived"):
                return False                               # already landing — don't interrupt the ending
            blob = (str(data.get("narrative", "")) + " " + " ".join(data.get("symbols", []) or [])).lower()
            return sum(1 for t in _REST_TERMS if t in blob) >= 2
        except Exception:
            return False

    def _scene_stalled(self, data: dict, prev: dict | None) -> bool:
        """EARNED-LENGTH stop signal for dreams — is this scene CIRCLING rather than DEVELOPING? Re-based on
        STRUCTURAL change (2026-06-20): because the morph shares imagery lineage, raw narrative similarity is a
        noisy false-positive; the real signal is whether the image-ANCHORS (symbols) turned over. Two checks,
        either is a stall:
          (1) PRIMARY — the symbols barely moved: consecutive scenes share >= DREAM_SYMBOL_PERSIST of their
              combined symbol set, so no core element crossed a threshold (what the DEVELOP prompt requires);
          (2) BACKSTOP — the narrative is a near-verbatim re-render (>= DREAM_RESTATE_SIM, raised to 0.92),
              catching literal photocopying even if the symbol labels were swapped.
        A stalled arc stops (→ its end-state becomes shadow, the recurring thread returns another night)."""
        if prev is None:
            return False
        try:
            import re
            def _anchor_words(syms):
                w = set()
                for s in syms or []:
                    for tok in re.findall(r"[a-z]+", str(s).lower()):
                        if len(tok) > 2:
                            w.add(tok[:-1] if tok.endswith("s") else tok)   # crude stem: cat/cats → cat
                return w
            cur, old = _anchor_words(data.get("symbols")), _anchor_words(prev.get("symbols"))
            if cur and old and (len(cur & old) / len(cur | old)) >= DREAM_SYMBOL_PERSIST:
                return True                       # anchors didn't turn over → circling (structural stall)
            from core.memory.store import _embed, _cosine
            nv, pv = _embed((data.get("narrative") or "")[:400]), _embed((prev.get("narrative") or "")[:400])
            if nv is not None and pv is not None and _cosine(nv, pv) >= DREAM_RESTATE_SIM:
                return True                       # near-verbatim photocopy backstop
        except Exception:
            pass
        return False

    def _find_world_ground(self, label: str) -> "str | None":
        """The most semantically-similar WORLD fragment (reading/study/research) to this tension — a real
        thing he encountered, offered to the dream as grounding for the imagery. None if none/too weak.
        This is what keeps the metaphor anchored in fact (and is what makes a dream resolvable)."""
        try:
            from core.memory.store import _connect, _embed, _blob_to_vec, _cosine
            lv = _embed(label)
            if lv is None:
                return None
            ph = ",".join("?" * len(_WORLD_GROUND_ORIGINS))
            with _connect() as conn:
                rows = conn.execute(
                    f"SELECT content, embedding FROM memory_fragments WHERE origin IN ({ph}) "
                    f"AND embedding IS NOT NULL ORDER BY timestamp DESC LIMIT 400",
                    _WORLD_GROUND_ORIGINS).fetchall()
            best, best_sim = None, 0.0
            for r in rows:
                try:
                    sim = _cosine(lv, _blob_to_vec(r["embedding"]))
                    if sim > best_sim:
                        best, best_sim = r["content"], sim
                except Exception:
                    continue
            return " ".join((best or "").split())[:220] if (best and best_sim >= _WORLD_GROUND_MIN_SIM) else None
        except Exception:
            return None

    @staticmethod
    def _find_counterpart(tension_label: str, patterns: list) -> "str | None":
        """The integration_pattern most related to the tension (label cosine) — a POINTER to the other
        pole, never its resolution. None when nothing relates above threshold."""
        try:
            from core.memory.store import _embed, _cosine
            tv = _embed(tension_label)
            if tv is None or not patterns:
                return None
            best, best_sim = None, 0.0
            _pvs = None
            if DREAM_PATTERN_CACHE:   # J-2178 (F-2882): one batched, cached embed of all labels
                _pvs = _pattern_vectors([(p.get("label") or "").strip() for p in patterns
                                         if (p.get("label") or "").strip()])
            for p in patterns:
                lbl = (p.get("label") or "").strip()
                if not lbl:
                    continue
                pv = _pvs.get(lbl) if _pvs is not None else _embed(lbl)
                if pv is None:
                    continue
                sim = _cosine(tv, pv)
                if sim > best_sim:
                    best, best_sim = lbl, sim
            return best[:120] if (best and best_sim >= 0.30) else None
        except Exception:
            return None

    def _met_carry_check(self, carried: dict, carried_n: int) -> "tuple[dict | None, int]":
        """J-1995 (D-0385): consult the computed 'met' state of the carried thread's root arc. In 'shadow' mode
        (default) only LOG what would have happened (data/logs/dream_met_carry_shadow.jsonl) and return the carry
        unchanged. In 'live' mode a 'met' thread ends the carry exactly like the CARRY_MAX_NIGHTS withdraw
        (tonight opens fresh, persisted counter reset to 0). Fail-open: any error leaves the carry as it was."""
        mode = MET_ENDS_CARRY
        if mode not in ("shadow", "live"):
            return carried, carried_n
        try:
            from core import dream_met as _dmet
            ts = _dmet.thread_state(provisional=PROVISIONAL_MET_ENDS_CARRY)
            computed_met = ts.get("state") == "met"
            provisional_met = bool(PROVISIONAL_MET_ENDS_CARRY and ts.get("provisional_state") == "provisional_met")
            would_end = computed_met or provisional_met
            ended_by = "computed" if computed_met else ("provisional" if provisional_met else None)
            row = {"ts": round(time.time(), 1), "mode": mode, "carried_n": carried_n,
                   "root": ts.get("root"), "root_state": ts.get("state"),
                   "root_age_days": ts.get("root_age_days"), "would_end_carry": would_end,
                   "carry_changed": bool(would_end and mode == "live"),
                   # J-2118: the provisional half (None when the flag is off or the root's state is already final)
                   "provisional_state": ts.get("provisional_state"), "ended_by": ended_by}
            _MET_CARRY_SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_MET_CARRY_SHADOW_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + chr(10))
            if ts.get("provisional_state") is not None:
                try:    # J-2118: every provisional-met consultation also goes to the closure shadow file (D-0423)
                    from core import closure as _closure
                    _closure.log_carry_decision(dict(row, provisional_detail=ts.get("provisional_detail")))
                except Exception as exc:
                    logger.debug("[dream] closure carry log skipped (non-fatal): %r", exc)
            if would_end and mode == "live":
                logger.info("[dream] the unfaced thread is %s MET (root %s) -- it ends; tonight opens fresh",
                            ended_by, ts.get("root"))
                self._carried_n_tonight = 0
                return None, -1
        except Exception as exc:
            logger.debug("[dream] met carry check skipped (non-fatal): %r", exc)
        return carried, carried_n

    def _carried_n(self) -> int:
        """How many consecutive nights the current unfaced thread has returned (from the log's carried_n)."""
        try:
            lines = [l for l in _DREAM_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
            rec = json.loads(lines[-1]) if lines else {}
            n = int(rec.get("carried_n", 0)) + 1 if rec.get("ended_unresolved") else 0
            self._carried_n_tonight = n
            return n
        except Exception:
            return 0

    def _last_unresolved_arc(self) -> "dict | None":
        """The most recent dream arc IF it ended unresolved — the recurring thread to continue tonight.
        None if the last arc RESOLVED (the figure was met → the thread clears, start fresh) or there is no
        prior arc. Returns a prev-shaped dict (narrative/symbols/unresolved_core) so scene 0 can take up
        where the figure was last left unfaced. This is what makes 'the recurring figure until met' real
        night-to-night (2026-06-15), instead of only the lossy shadow→tension recurrence."""
        try:
            if not _DREAM_LOG.exists():
                return None
            lines = [l for l in _DREAM_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
            if not lines:
                return None
            rec = json.loads(lines[-1])
            if not rec.get("ended_unresolved"):
                return None                      # last dream resolved — the thread is met; start fresh
            # J-3177 (D-0565, founder 2026-11-02): resting is a legitimate ending. An arc that ARRIVED at its own
            # end (close_reason resolved / ended-unfaced) and still names a core is a rest, not unfinished business.
            # core/dream_rest.py's RESTING_ENDING decides: 'off' = this block does nothing, 'shadow' (default) logs
            # what 'live' would do and returns the arc as before, 'live' does not return a rest arc. A stalled /
            # dropped / ceiling arc did not arrive and keeps the legacy carry. Fail-open to the legacy return.
            try:
                from core import dream_rest as _dr
                if not _dr.carry_returns(rec):
                    return None
            except Exception as exc:
                logger.debug("[dream] rest-ending carry check skipped (non-fatal, legacy carry): %r", exc)
            return {
                "narrative":       rec.get("final_narrative") or (rec.get("narrative", "")[-300:]),
                "symbols":         (rec.get("final_symbols") or rec.get("symbols", []))[:3],
                "unresolved_core": rec.get("final_unresolved_core", ""),
            }
        except Exception:
            return None

    def _ground_symbols(self, scenes: list[dict]) -> None:
        """Hand the dream's CONCRETE symbols to the frontier as grounded WORLD-questions, so the curiosity
        chain can work out what the metaphor literally is — the dream understands its metaphors by RESEARCHING
        them (not by self-analysis, which would break image-making). Abstract/self symbols are skipped (no
        literal referent). Also feeds the exploratory-ignition backlog. Best-effort."""
        try:
            from core import frontier as _fr
            seen: set[str] = set()
            grounded = 0
            for sym in (s.lower().strip() for sc in scenes for s in sc.get("symbols", [])):
                word = sym.split()[-1] if sym else ""        # "the river" -> "river"
                if not word or len(word) < 4 or word in _ABSTRACT_SYMBOLS or word in seen:
                    continue
                seen.add(word)
                # minimal boilerplate so the SYMBOL dominates the tokens — else different symbols
                # ("…river work" vs "…door work") collide above the frontier's 0.55 dedup threshold
                # and all symbol-questions collapse into one.
                q = f"how does a {word} work"
                if _fr.is_world_question(q) and _fr.note_question(q, "dream"):
                    grounded += 1
                if grounded >= 2:                            # at most two per night — don't flood the frontier
                    break
            if grounded:
                logger.info("[dream] grounded %d symbol(s) into world-questions for curiosity to work out",
                            grounded)
        except profile.NonLiveWriteError:
            raise   # J-0874: note_question() raises in a non-live process (J-0846); do not re-swallow here
        except Exception as exc:
            logger.debug("[dream] symbol grounding failed: %s", exc)

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def _t_mark(self, name: str) -> None:
        """J-2296: one wall-clock stamp into this dream's stage timing (instrumentation only, never raises)."""
        if not DREAM_STAGE_TIMING:
            return
        try:
            if not isinstance(getattr(self, "_stage_timing", None), dict):
                self._stage_timing = {}
            self._stage_timing[name] = round(time.time(), 3)
        except Exception:
            pass

    def _stage_timing_record(self) -> dict:
        """J-2296: {stamps, durations_s} for the arc record; durations between consecutive present stamps."""
        st = dict(getattr(self, "_stage_timing", None) or {})
        order = ["gather_begin", "gather_end", "carry_end", "met_end", "ask_end", "probe_end"]
        dur, prev = {}, None
        for k in order:
            if k in st:
                if prev is not None:
                    dur[f"{prev}->{k}"] = round(st[k] - st[prev], 3)
                prev = k
        return {"stamps": st, "durations_s": dur, "pre_probe_offloop": bool(DREAM_PRE_PROBE_OFFLOOP)}

    def _log_arc(self, scenes: list[dict], dream_id: str, close_reason: str = "ceiling") -> None:
        try:
            # Repetition metric (2026-06-18): how many scenes have a DISTINCT opening (first 60 chars). If this
            # is < scenes, the dream is re-rendering the same opening (the verbatim-photocopy bug) — the direct
            # measure of whether the tail-handoff + anti-repeat fix worked.
            _opens = [" ".join((s.get("narrative") or "").split())[:60].lower() for s in scenes]
            record = {"ts": time.time(), "dream_id": dream_id, "scenes": len(scenes),
                      "close_reason": close_reason,        # earned length: resolved | stalled | ceiling
                      "distinct_openings": len(set(_opens)),   # of `scenes` — < scenes = openings still repeating
                      "tension_source": scenes[0]["tension_source"],
                      "symbols": [s for sc in scenes for s in sc["symbols"]][:8],
                      "narrative": "  …  ".join(s["narrative"] for s in scenes),
                      "ended_unresolved": bool(scenes[-1]["unresolved_core"]),
                      "carried_n": getattr(self, "_carried_n_tonight", 0),   # nights this thread has returned (0 = fresh)
                      "material_sources": getattr(self, "_material_sources", []),
                      # the final scene's thread — so a recurring dream can take up where it broke off
                      "final_narrative":      scenes[-1]["narrative"],
                      "final_symbols":        scenes[-1]["symbols"][:4],
                      "final_unresolved_core": scenes[-1]["unresolved_core"],
                      # PHASE 1 INSTRUMENTATION (2026-09-17, J-1057, docs/staged/dream_overhaul.md sec 7
                      # Phase 1 row) -- ADDITIVE ONLY. Every key above this line is completely untouched,
                      # 'scenes' stays an int: night.py, sleep_dream_probe.py, hud/server.py,
                      # scripts/du_pulse.py, scripts/liveness_audit.py, scripts/check_du.py all read the
                      # pre-existing keys unmodified. 'seed' is what actually fed tonight (fragment ids
                      # from associative_recall, the tension labels _load_top_tensions selected, hashes
                      # of the day-residue blocks) -- the raw material core/dream_probe.py's before/after
                      # read and any future re-entry analysis need. 'scenes_detail' threads the PHASE each
                      # scene was generated under (new key on the per-scene dict, _gen_episode) alongside
                      # its own narrative/symbols/tension_source/unresolved_core/movement -- so a reader
                      # no longer has to reconstruct scene-level state from the flattened top-level lists.
                      # 'engine': 'legacy' names which engine wrote this row, so a future 'vault' engine
                      # (Phase 2+) can share this same log file without a reader ever confusing the two.
                      "seed": {
                          "fragment_ids":     list(getattr(self, "_seed_fragment_ids", []) or []),
                          "tension_labels":   list(getattr(self, "_seed_tension_labels", []) or []),
                          "day_block_hashes": list(getattr(self, "_seed_day_block_hashes", []) or []),
                      },
                      "scenes_detail": [
                          {"idx": idx, "phase": s.get("phase"), "narrative": s.get("narrative"),
                           "symbols": s.get("symbols"), "tension_source": s.get("tension_source"),
                           "unresolved_core": s.get("unresolved_core"), "movement": s.get("movement")}
                          for idx, s in enumerate(scenes)
                      ],
                      "engine": "legacy"}
            if DREAM_STAGE_TIMING:   # J-2296: additive key; no existing reader touches it
                try:
                    record["stage_timing"] = self._stage_timing_record()
                except Exception:
                    pass
            _DREAM_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_DREAM_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass
