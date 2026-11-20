from __future__ import annotations
import asyncio
import json
import pathlib
import time
import unicodedata
from core.node_base import NodeBase
from core.schema import CognitiveState, ConsolidationOutput
from core.memory.store import store_fragment

CONSOLIDATE_MIN_CYCLES = 3   # distil wisdom only from a batch this thick; a thinner batch ACCUMULATES
                             # across runs instead of being distilled-and-cleared every 60s (2026-06-21)

# J-2826 (F-3489, registry row P-0012): the dedup gate below used to be a ~33-character prefix LIKE that called itself an
# "exact-normalized probe". Offline replay over the 521 wisdoms that reached the gate since 08-21 (data/training/
# consolidation.jsonl vs the 1296 origin='consolidation' fragments): the old probe blocked 112, every one of them a
# DIFFERENT sentence that merely opens like a held one (0 equal after normalisation), while paraphrase echoes passed.
# Now: rule 1 = full normalised-text equality (prefix removed, case/whitespace/edge-punctuation folded), rule 2 = the
# nearest held consolidation fragment, by the store's own embedding, has cosine >= DEDUP_EMBED_COSINE. Replay at 0.85:
# 61 of 521 blocked (33 of the old 112 plus 28 paraphrase echoes that used to mint), 79 of the old false blocks pass.
DEDUP_EMBED_COSINE = 0.85    # None / 0 turns the embedding rule off (equality still applies); one-line kill switch
_WISDOM_PREFIX = "I have come to understand: "

# J-2829 (F-3490, registry row P-0012): the user prompt's `Axiom:` line carries the whole persona assembly (median 2540 chars
# vs 4360 of actual experience) into a compression task that needs only the entity name. FLAG, DEFAULT OFF: the offline
# replay (arm A current / arm B entity-only / arm C B at temperature 0.4) has not been run yet (hubs slow, Du down), so
# the shipped behaviour is unchanged until it is. True drops the Axiom line; temperature is deliberately untouched.
CONSOLIDATION_DROP_PERSONA_BLOCK = False
_EMBED_DIM = 384             # store.py: paraphrase-multilingual-MiniLM-L12-v2, float32 blobs


def _norm_wisdom(text: str) -> str:
    """Normalised comparison form: the first-person prefix removed, NFKC, case-folded, whitespace collapsed, edge
    quotes/punctuation stripped. Two wisdoms with the same form are the same sentence."""
    t = (text or "").strip()
    if t.startswith(_WISDOM_PREFIX.rstrip()):      # rstrip: t was stripped, so a bare prefix has lost its trailing space
        t = t[len(_WISDOM_PREFIX.rstrip()):]
    t = " ".join(unicodedata.normalize("NFKC", t).casefold().split())
    return t.strip(" \t\"'`.,;:!?()[]{}")


def wisdom_dup_rule(wisdom: str) -> tuple[str, str] | None:
    """Return (rule, detail) when `wisdom` is already held among the origin='consolidation' fragments, else None.
    rule is 'equal' (full normalised text equality) or 'embedding' (nearest-neighbour cosine >= DEDUP_EMBED_COSINE).
    No LIKE, so no wildcard escaping. Every held consolidation row counts, cold ones included (the cold-flagged
    recitation fossils are exactly the repeats this gate exists to stop). Raises on a DB error; the caller fails open.
    An embedding failure skips only rule 2 (equality was already checked)."""
    from core.memory.store import _connect
    with _connect() as conn:
        rows = conn.execute("SELECT fragment_id, content, embedding FROM memory_fragments "
                            "WHERE origin='consolidation'").fetchall()
    want = _norm_wisdom(wisdom)
    if not want:
        return None
    for r in rows:
        if _norm_wisdom(r["content"] or "") == want:
            return ("equal", f"fragment {r['fragment_id']}")
    if not DEDUP_EMBED_COSINE:
        return None
    import numpy as np
    from core.memory.store import _embed
    keep = [r for r in rows if r["embedding"] and len(r["embedding"]) == _EMBED_DIM * 4]
    if not keep:
        return None
    vec = _embed(wisdom)        # the text as it will be stored (prefix included), like the held vectors
    if vec is None:
        return None
    mat = np.stack([np.frombuffer(r["embedding"], dtype=np.float32) for r in keep])
    sims = mat @ vec            # both sides are unit-normalised, so the dot product is the cosine
    k = int(np.argmax(sims))
    if float(sims[k]) >= DEDUP_EMBED_COSINE:
        return ("embedding", f"cos={float(sims[k]):.3f} fragment {keep[k]['fragment_id']}")
    return None


# J-3178 / D-0566 (founder, 2026-11-02, plan memory_knowledge; F-0007, registry row P-0012): SHADOW judge on every minted
# wisdom. After a wisdom is stored, a different-family two-judge panel (JUDGE_1 mixtral, JUDGE_2 falcon3, granite tiebreak
# on a split) is asked whether it is SUPPORTED by the source cycles or only a restatement / confabulation. The verdict is
# only LOGGED to data/consolidation_judge_shadow.jsonl. Nothing acts on it for the first week: no withholding, no change
# to minting, relevance or serving. Read it with scripts/consolidation_judge_read.py. Fail open and quiet; one-line kill
# switch below. The key "wisdom_supported" is new (not in judge_panel.GRANITE_CONSTANT_TIEBREAK_KEYS, no measured granite
# rate yet), so a split still consults the granite tiebreak; the panel's verdict may be None (no verdict) and is logged anyway.
CONSOLIDATION_JUDGE_SHADOW = True
JUDGE_KEY = "wisdom_supported"
JUDGE_MAX_CYCLES = 20            # same window _build_prompt shows the model (last 20 cycles)
JUDGE_CYCLE_CHARS = 600          # per-cycle cap (a cycle summary is Q + A[:350] + tensions/scene/perception/emotion/reflection)
JUDGE_TOTAL_CHARS = 7000         # whole source block cap, so the CPU judge hubs stay inside their window
_JUDGE_LOG = pathlib.Path(__file__).resolve().parent.parent / "data" / "consolidation_judge_shadow.jsonl"
_JUDGE_SYSTEM = (
    "You audit a memory-consolidation step. You are given SOURCE CYCLES (a mind's recent questions, answers and drafts) "
    "and one WISDOM sentence that was distilled from them. Decide whether the wisdom is SUPPORTED by the source cycles: "
    "the sources genuinely contain or directly imply the insight. Answer false if it only restates the axiom or a "
    "stock phrase without support in the cycles, or if it asserts something the cycles do not contain (confabulation). "
    "Output ONLY a JSON object: {\"wisdom_supported\": true or false, \"why\": \"one short sentence\"}"
)
_judge_tasks: set = set()


def _judge_source_block(cycles: list[str]) -> str:
    """The capped source text the judge sees: the last JUDGE_MAX_CYCLES cycles, each cut to JUDGE_CYCLE_CHARS, the whole
    block cut to JUDGE_TOTAL_CHARS."""
    parts = [f"[{i}] {(c or '')[:JUDGE_CYCLE_CHARS]}" for i, c in enumerate(cycles[-JUDGE_MAX_CYCLES:], 1)]
    return "\n---\n".join(parts)[:JUDGE_TOTAL_CHARS]


async def judge_minted_wisdom(wisdom: str, cycles: list[str], wisdom_id: str | None, source_ids: list[str],
                              log_path: pathlib.Path | None = None) -> dict | None:
    """Shadow-judge one minted wisdom and append one row to the shadow log. Never raises; returns the row (or None)."""
    try:
        from core import judge_panel
        src = _judge_source_block(cycles)
        user = f"SOURCE CYCLES:\n{src}\n\nWISDOM: {wisdom}"
        res = await judge_panel.rule_detail(_JUDGE_SYSTEM, user, JUDGE_KEY,
                                            context=f"consolidation:{(wisdom_id or '')[:24]}", node="consolidation")
        row = {"ts": round(time.time(), 1), "wisdom_id": wisdom_id, "wisdom": wisdom,
               "verdict": res.get("verdict"), "reason": res.get("why"), "how": res.get("how"),
               "v1": res.get("v1"), "v2": res.get("v2"), "why1": res.get("why1"), "why2": res.get("why2"),
               "n_cycles": len(cycles), "source_fragment_ids": list(source_ids),
               "source_chars": len(src), "caps": {"cycles": JUDGE_MAX_CYCLES, "per_cycle": JUDGE_CYCLE_CHARS,
                                                  "total": JUDGE_TOTAL_CHARS}}
        path = log_path or _JUDGE_LOG
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row
    except Exception:
        return None


class ConsolidationNode(NodeBase):

    def __init__(self):
        super().__init__("consolidation")
        self._recent_cycles: list[str] = []
        self._recent_fragment_ids: list[str] = []   # lineage — episodic IDs that fed this consolidation
        self._batch_corrected = False   # axis gate: a correction/fail-call cycle is in this batch

    def add_cycle_summary(self, summary: str, fragment_id: str | None = None,
                          corrected: bool = False) -> None:
        """Called by the orchestrator after each completed cycle. `corrected` marks a cycle in
        which the human delivered an explicit correction/fail-call (or the Critic finally
        rejected) — material that must not be laundered into semantic self-truth."""
        self._recent_cycles.append(summary)
        if corrected:
            self._batch_corrected = True
        if fragment_id:
            self._recent_fragment_ids.append(fragment_id)
        if len(self._recent_cycles) > 50:
            self._recent_cycles = self._recent_cycles[-50:]
            self._recent_fragment_ids = self._recent_fragment_ids[-50:]

    async def run(self, state: CognitiveState) -> bool:
        # ACCUMULATE-UNTIL-BATCH (2026-06-21): only distil when a real batch (CONSOLIDATE_MIN_CYCLES+) has
        # gathered. Before, the node ran every 60s and CLEARED the batch each time, so the 3-cycle wisdom
        # gate was never reached (conversational cycles arrive minutes apart) — wisdom never fired and the
        # semantic tier stalled at +0. Now a thin batch is LEFT to grow across runs, not distilled-and-discarded.
        if len(self._recent_cycles) < CONSOLIDATE_MIN_CYCLES:
            self.logger.debug("[consolidation] accumulating — %d/%d cycles, waiting for a fuller batch",
                              len(self._recent_cycles), CONSOLIDATE_MIN_CYCLES)
            return False
        return await super().run(state)

    @property
    def system_prompt(self) -> str:
        return (
            "You are the memory consolidation node of a cognitive architecture. "
            "You run periodically to compress recent experiences into lasting memory. "
            "Look for patterns, extract what is genuinely significant, discard noise. "
            # J-3837 (D-0680): the J-2509 own-name sentence was removed; the bare Entity line in _build_prompt stays
            # until D-0681's 7-day wait (J-3348).
            "Output ONLY a valid JSON object. No preamble.\n"
            # J-2828 (F-3471, registry row P-0012): "memories_processed" and "patterns_noted" are no longer requested.
            # Nothing read either (only a log line did); 406 of 408 outputs said processed=3, a count the node already
            # knows (len(self._recent_cycles)), and the patterns were ~3 sentences of output per call that were never
            # stored. The stored fragment (wisdom_extracted) is unchanged; _write_output ignores old keys if a model still emits them.
            "Schema: {\"wisdom_extracted\": \"one sentence or null\"}\n"
            "wisdom_extracted: a single distilled insight worth keeping long-term. null if nothing notable."
        )

    def _build_prompt(self, state: CognitiveState) -> str:
        if not self._recent_cycles:
            return "No recent cycles to consolidate."
        cycle_text = "\n---\n".join(self._recent_cycles[-20:])
        axiom_line = "" if CONSOLIDATION_DROP_PERSONA_BLOCK else f"Axiom: {state.axiom}\n"
        return (
            f"Entity: {state.spirit_name}\n"
            f"{axiom_line}\n"
            f"Recent experience ({len(self._recent_cycles)} cycle(s)):\n{cycle_text}"
        )

    def _write_output(self, state: CognitiveState, data: dict) -> None:
        wisdom = data.get("wisdom_extracted")
        # Prefix with "I have come to understand:" so when this semantic fragment is
        # retrieved Carl recognises it as his own synthesised thought, not an external
        # fact or a statement from the conversation. The readable_label() will say
        # "My own reflection" but the content itself should also read as first-person.
        if wisdom and not wisdom.strip().lower().startswith("i "):
            wisdom = "I have come to understand: " + wisdom.strip()

        # Axis gate (error→BEING firewall, 2026-06-10): a batch containing a correction/fail-call
        # cycle must not mint a semantic "understanding". Observed live: founder said "that is a
        # fail overall" and within the minute this lane wrote "the integration of opposites is not
        # a failure but a step towards wholeness" to semantic memory — a task failure laundered
        # into permanent self-truth. Failures route through the contradiction/error machinery
        # (which handles them properly); this lane consolidates only clean experience. The
        # episodic record of the exchange is untouched — what happened is still remembered;
        # what is gated is the failure becoming doctrine.
        # Rate gate (2026-06-10): one exchange is not an understanding. A wisdom may only
        # distil from a batch of 3+ cycles — fewer, truer distillations; the semantic tier
        # stops filling with per-exchange self-synthesis.
        if wisdom and len(self._recent_cycles) < 3:
            self.logger.info("[consolidation] wisdom withheld — batch too thin (%d cycle(s))",
                             len(self._recent_cycles))
            wisdom = None

        if wisdom and self._batch_corrected:
            self.logger.info(
                "[consolidation] wisdom QUARANTINED — correction/fail-call in batch "
                "(error->BEING gate): %s", wisdom[:120])
            wisdom = None

        # Dedup gate (2026-08-20, rewritten J-2826): during the June 3-10 recitation collapse this lane faithfully
        # distilled the axiom back out of every recitation cycle and minted it as a fresh
        # "understanding" ONCE EVERY FEW MINUTES — 167 exact copies of one sentence (624 rows in the
        # burst family), which then became the geometric hubs of the entire recall pool (audit
        # 2026-08-20; the fossils were cold-flagged the same day, manifest in docs/reviews/). The
        # node had no memory of what it had already understood. Now: an understanding already held in semantic
        # memory is a re-arrival, not a new distillation — logged, never re-minted. "Already held" means (rule
        # 'equal') the same sentence after normalisation, or (rule 'embedding') a held consolidation fragment whose
        # embedding is within DEDUP_EMBED_COSINE of it — a paraphrase echo. See wisdom_dup_rule() above. A different
        # sentence that only opens with the same words is NOT a duplicate (the old 33-character prefix probe blocked
        # those). Fail-open: a probe error mints, as before. The log line names the rule that fired.
        if wisdom:
            try:
                hit = wisdom_dup_rule(wisdom)
                if hit:
                    self.logger.info("[consolidation] wisdom already held — NOT re-minted "
                                     "(dedup gate, rule=%s, %s): %s", hit[0], hit[1], wisdom[:100])
                    wisdom = None
            except Exception as exc:
                self.logger.debug("[consolidation] dedup probe failed (fail-open, minting): %s", exc)
        minted_id = None
        if wisdom:
            minted_id = store_fragment(
                content      = wisdom,
                layer        = "semantic",
                relevance    = 0.8,
                keywords     = ["wisdom", "consolidated"],
                origin       = "consolidation",
                derived_from = list(self._recent_fragment_ids),
            )
            # J-3178 / D-0566: shadow judge, fire-and-forget (the node never waits on it, the verdict is only logged).
            if CONSOLIDATION_JUDGE_SHADOW:
                try:
                    t = asyncio.get_running_loop().create_task(judge_minted_wisdom(
                        wisdom, list(self._recent_cycles), minted_id, list(self._recent_fragment_ids)))
                    _judge_tasks.add(t)
                    t.add_done_callback(_judge_tasks.discard)
                except Exception:
                    pass      # no running loop / any error: fail open and quiet

        state.last_consolidation = time.time()
        n_cycles = len(self._recent_cycles)   # J-2828: the code's own count, not a model-reported "memories_processed"
        self._recent_cycles.clear()
        self._recent_fragment_ids.clear()
        self._batch_corrected = False

        self.logger.info(
            "[consolidation] processed=%d wisdom=%s",
            n_cycles,
            bool(wisdom),
        )
