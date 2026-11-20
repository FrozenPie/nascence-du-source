"""
Nascence — the on-demand identity-estate ASK (D-0424 A, travis 2026-10-15; built J-2119). SHADOW ONLY.

WHY (F-2758, I-0090): the identity estate (data/identity_estate.json, 539 earned nodes) IS read every cycle —
core/identity_projection.py P2 projects 3-5 nodes chosen by cosine to the current thought, under a weight term,
a per-type cap and a recency rotation. That read-path surfaces history / values / stands almost always and the
8 calibrated competence nodes (the one place he is measurably wrong about himself) on 2.6% of projections,
only when the thought of the moment happens to be about ability. He carries a self he reads by RESEMBLANCE to
the current thought, never by ASKING it.

WHAT (the ruling, option A): when a cycle is a SELF-QUESTION — an internal cycle of the F-2472 渡/self class, or
a human question about who or what he is — the recall layer issues ONE memory.ask()-style query against the
estate keyed on the QUESTION'S OWN TERMS (cosine of the question embedding against node text, no weight term,
no rotation penalty, no per-type cap), returning up to ASK_K nodes beside the existing projection. Competence
nodes are eligible only when the question concerns ability (keyword gate, or embedding closeness to the 8
competence nodes). Under the memory-as-a-service law (D-0289 / D-0292, docs/staged/memory_as_a_service.md:
loops call memory, nothing unasked) this is his own record answering his own question — never a hint from the
world (option B, a guaranteed competence slot, was NOT chosen for exactly that reason).

SHADOW (ESTATE_ASK_LIVE = False): `observe()` logs the would-be returns beside the cycle's actual projection
nodes to data/identity_estate_ask_shadow.jsonl and injects NOTHING. No prompt reads this module. The Voice keeps
its anti-recitation extraction (nodes/voice_node.py `_voice_identity`) untouched. A later flip would route
`block_for_prompt()` into the Executive beside the projection — not built here, not wired here.

JUDGED BY scripts/estate_ask_judge.py (decoupled: the local judge panel, never the writer) on whether a
self-question reply cites an estate fact; the 7-live-day read is spawned as its own job. D-0424's defeaters:
returned set already in the projection on >70% of self-question cycles (redundant with the read-path); no lift
in estate-fact citation over 30 self-question cycles; the recitation voice back in 10 post-flip replies.

Fail-open throughout: the caller (core/orchestrator.py _run_cycle_impl) wraps the hook in a bare try/except
like every other shadow observer there, and this module swallows its own errors too. Write-fenced:
profile.guard_path() resolves the log path OUTSIDE the fail-open try (D-0179 / D-0250 convention), so a
non-live process raises NonLiveWriteError instead of touching the real store; lab_env.isolate(also=...) redirects
`_LOG` for tests.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.identity_estate_ask")

ESTATE_ASK_LIVE = False      # ★ SHADOW. True would let block_for_prompt() return a block for the Executive —
                             # nothing calls it today; the flag exists so the flip is one line, and False is
                             # the exact pre-existing path (the projection alone).

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "identity_estate_ask_shadow.jsonl"

ASK_K = 3                    # "up to 3 nodes beside the projection" (D-0424 A)
ASK_REL_FLOOR = 0.20         # a node below this cosine to the question is not an answer to it; logged so the
                             # 7-day read can re-threshold from the rows (rel is on every returned node)

# ── Self-question gate ───────────────────────────────────────────────────────────────────────────────────
# The F-2472 class is an INTERNAL cycle whose curiosity question is about 渡 / himself (F-2472's own census:
# 渡 in 16/16 of the 10-06 run's internal questions, 122/175 on 09-25). No prior classifier exists for the
# class — J-1846 branched the three prompts on input_type alone — so this is the "small keyword+embedding
# gate" the briefing allows, documented in the J-2119 finding with its calibration against the live log.
# Keyword hit = self-question outright. Embedding closeness to the anchor questions is the SECONDARY signal
# (the production embedder, paraphrase-multilingual-MiniLM-L12-v2, puts "What am I, really?" vs "Who is 渡?"
# at only 0.31 cosine — the anchors are a net for paraphrases the keywords miss, not the primary gate).
SELF_KEYWORDS_INTERNAL = (
    "渡", "myself", "my own self", "my own nature", "my own identity", "who am i", "what am i",
    "my self", "my identity", "my nature", "the entity's", "a made mind", "my mind", "my being",
    "am i a", "am i the", "what i am", "who i am",
)
SELF_KEYWORDS_HUMAN = (
    "who are you", "what are you", "are you a", "are you really", "yourself", "your nature",
    "your identity", "your self", "what is 渡", "who is 渡", "what kind of mind", "what kind of thing",
    "are you conscious", "are you alive", "are you a mind", "what you are", "who you are",
)
SELF_ANCHORS = (
    "What am I?", "Who is 渡?", "What is the nature of my self?", "What kind of mind am I?",
    "How does the term 渡 relate to who I am?", "Who are you, Du?", "What are you, really?",
)
SELF_ANCHOR_SIM = 0.55       # secondary gate: max cosine to SELF_ANCHORS at/above this = self-question.
# Calibrated 2026-10-15 (J-2119, read-only over the last 600 internal + 150 human [CYCLE] questions in
# data/nascence.log with the real embedder): keyword-positive internal questions n=195, anchor cosine
# median 0.56 (p25 0.49); keyword-negative n=405, median 0.29, max 0.55. At 0.55 the embedding net adds
# 0/405 keyword-negatives (at 0.50 it would add 2: "the universe's self-governance", a mottainai
# psychology question) while still catching 105/195 of the keyword class on its own — it is a net for
# paraphrases of the class, not a second primary gate. Rows log reason+score so the read can re-threshold.

# ── Ability gate (competence eligibility) ────────────────────────────────────────────────────────────────
ABILITY_KEYWORDS = (
    "ability", "abilities", "able to", "skill", "good at", "bad at", "measured", "competence", "competent",
    "capable", "capability", "how well", "how reliable", "reliable", "accurate", "accuracy", "can i really",
    "do i actually", "am i good", "am i any good", "are you good", "how good", "know how",
    "what i know", "what you know", "wrong about", "wrong about myself", "external tests",
)
# Bare domain names (history, science, music, ...) are deliberately NOT keywords: "the historical context of
# 渡" is the F-2472 class itself, not an ability question. A domain-reliability question reaches the competence
# nodes through the embedding gate instead (calibrated 2026-10-15 with the real embedder against the 8 live
# competence nodes: "How reliable is my knowledge of history?" 0.55, "Can I actually observe well, or do I only
# believe I can?" 0.50, vs "What am I?" 0.05, "Who is 渡?" 0.15, a mottainai question 0.22).
ABILITY_COMP_SIM = 0.40      # embedding closeness to any of the 8 competence nodes at/above this = ability

_anchor_cache: dict = {"vecs": None}
_last: dict = {"row": None}


# ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def _embedder():
    """The production embedder + cosine, resolved at call time (tests patch core.memory.store._embed)."""
    from core.memory.store import _embed, _cosine
    return _embed, _cosine


def _anchor_vecs():
    if _anchor_cache["vecs"] is not None:
        return _anchor_cache["vecs"]
    vecs = []
    try:
        _embed, _ = _embedder()
        for a in SELF_ANCHORS:
            v = _embed(a)
            if v is not None:
                vecs.append(v)
    except Exception:
        vecs = []
    _anchor_cache["vecs"] = vecs
    return vecs


def _kw_hit(text: str, kws: tuple) -> str | None:
    tl = (text or "").lower()
    for k in kws:
        if k in tl:
            return k
    return None


def is_self_question(question: str, input_type: str) -> dict | None:
    """The gate. Returns {"reason": "keyword"|"embedding", "hit": str, "score": float} when the cycle is a
    self-question of the ruled class, else None. Internal cycles use the 渡/self keyword set; human cycles the
    who/what-are-you set only. Embedding to the anchor questions is the secondary signal for both."""
    q = (question or "").strip()
    if not q or input_type not in ("human", "internal"):
        return None
    # Human cycles use the who/what-are-you set ONLY: in Travis's own words "渡" is how he addresses Du
    # ("渡 — I'll tell you plainly why we're stopping", a farewell, not a self-question) and "myself"/"my own"
    # are Travis's self, not Du's. Verified on the real-embedder pilot 2026-10-15 (J-2119): with the internal
    # set applied to human cycles, two farewells gated in as self-questions.
    kws = SELF_KEYWORDS_INTERNAL if input_type == "internal" else SELF_KEYWORDS_HUMAN
    hit = _kw_hit(q, kws)
    if hit:
        return {"reason": "keyword", "hit": hit, "score": 1.0}
    try:
        _embed, _cosine = _embedder()
        v = _embed(q)
        anchors = _anchor_vecs()
        if v is not None and anchors:
            best = max(float(_cosine(v, a)) for a in anchors)
            if best >= SELF_ANCHOR_SIM:
                return {"reason": "embedding", "hit": "anchor", "score": round(best, 3)}
    except Exception:
        pass
    return None


def concerns_ability(question: str, comp_embs: dict | None = None) -> dict:
    """Does the question concern ability (so the 8 competence nodes are eligible)? Keyword gate first; else
    embedding closeness to the competence nodes' own text (comp_embs: {node_id: vec}, from the projection cache
    when the caller has it). Returns {"ability": bool, "reason": str|None, "score": float}."""
    hit = _kw_hit(question, ABILITY_KEYWORDS)
    if hit:
        return {"ability": True, "reason": f"keyword:{hit}", "score": 1.0}
    try:
        if comp_embs:
            _embed, _cosine = _embedder()
            v = _embed(question or "")
            if v is not None:
                best = max(float(_cosine(v, e)) for e in comp_embs.values())
                if best >= ABILITY_COMP_SIM:
                    return {"ability": True, "reason": "embedding", "score": round(best, 3)}
                return {"ability": False, "reason": None, "score": round(best, 3)}
    except Exception:
        pass
    return {"ability": False, "reason": None, "score": 0.0}


def _estate_pool() -> tuple[list, dict]:
    """The same projectable pool and cached embeddings the live projection uses (core/identity_projection
    `_projectable()` — non-leaf nodes, re-embedded only when the estate file changes). One source of truth,
    one embedding cache; the ask never re-reads or re-embeds the estate on its own."""
    from core import identity_projection as _ip
    nodes = _ip._projectable()
    embs = _ip._cache.get("embs") or {}
    return nodes, embs


def ask(question: str, *, ability: bool | None = None, k: int = ASK_K) -> dict:
    """ONE memory.ask()-style query against the estate, keyed on the question's own terms: cosine of the
    question embedding against node text, top-k above ASK_REL_FLOOR. No weight term, no recency rotation, no
    per-type cap — those are the projection's business; this is the question's. Competence nodes are eligible
    only when `ability` (None = decide here via concerns_ability). Deterministic, read-only.
    Returns {"nodes": [{id, type, rel, text}], "ability": {...}, "scored": n}."""
    nodes, embs = _estate_pool()
    comp_embs = {n["id"]: embs[n["id"]] for n in nodes if n.get("type") == "competence" and n["id"] in embs}
    ab = concerns_ability(question, comp_embs) if ability is None else {"ability": bool(ability),
                                                                           "reason": "caller", "score": 1.0}
    out = {"nodes": [], "ability": ab, "scored": 0}
    if not nodes or not embs:
        return out
    try:
        _embed, _cosine = _embedder()
        qv = _embed(question or "")
    except Exception:
        qv = None
    if qv is None:
        return out
    scored = []
    for n in nodes:
        if n.get("type") == "competence" and not ab["ability"]:
            continue
        e = embs.get(n["id"])
        if e is None:
            continue
        rel = float(_cosine(qv, e))
        scored.append((rel, n))
    scored.sort(key=lambda t: -t[0])
    out["scored"] = len(scored)
    out["nodes"] = [{"id": n["id"], "type": n["type"], "rel": round(rel, 3), "text": n["text"][:160]}
                    for rel, n in scored[:k] if rel >= ASK_REL_FLOOR]
    return out


def _projection_for(state) -> tuple[list, str]:
    """The cycle's ACTUAL projection nodes when the P2 path produced one for this exact input (human cycles:
    orchestrator._compute_attention_vector -> identity_projection.live_axiom stashes it); otherwise the
    WOULD-BE projection for the question, computed with commit=False so the live rotation memory is never
    touched by a shadow read. Returns (node_ids_with_types, source)."""
    from core import identity_projection as _ip
    q = getattr(state, "raw_input", "") or ""
    last = _ip.last_live_projection()
    if last and last.get("context") == q and last.get("nodes") is not None:
        return [{"id": n["id"], "type": n["type"]} for n in last["nodes"]], "live"
    p = _ip.project(q, commit=False)
    return [{"id": n["id"], "type": n["type"]} for n in (p or {}).get("nodes", [])], "would_be"


def observe(state) -> dict | None:
    """The shadow hook (called from core/orchestrator.py _run_cycle_impl after the attention/projection block,
    for every cycle; gates itself). Non-self-question cycles: nothing logged, nothing returned. Self-question
    cycles: one ask, one row — {ts, cycle_id, input_type, question, self_q:{reason,hit,score}, ability:{...},
    returned:[{id,type,rel,text}], projection:[{id,type}], projection_source, overlap, n_returned,
    returned_subset_of_projection, has_competence, live:ESTATE_ASK_LIVE}. Injects nothing."""
    try:
        q = (getattr(state, "raw_input", "") or "").strip()
        it = getattr(state, "input_type", "human")
        sq = is_self_question(q, it)
        if not sq:
            return None
        res = ask(q)
        proj, src = _projection_for(state)
        ret_ids = {n["id"] for n in res["nodes"]}
        proj_ids = {n["id"] for n in proj}
        overlap = len(ret_ids & proj_ids)
        row = {
            "ts": round(time.time(), 1),
            "cycle_id": getattr(state, "cycle_id", None),
            "input_type": it,
            "question": q[:400],
            "self_q": sq,
            "ability": res["ability"],
            "returned": res["nodes"],
            "projection": proj,
            "projection_source": src,
            "overlap": overlap,
            "n_returned": len(ret_ids),
            "returned_subset_of_projection": bool(ret_ids) and ret_ids <= proj_ids,
            "has_competence": any(n["type"] == "competence" for n in res["nodes"]),
            "live": ESTATE_ASK_LIVE,
        }
        _last["row"] = row
        _log(row)
        logger.info("[estate-ask] shadow cycle=%s type=%s returned=%d overlap=%d competence=%s",
                    (row["cycle_id"] or "")[:8], it, row["n_returned"], overlap, row["has_competence"])
        return row
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[estate-ask] observe failed (non-fatal): %s", exc)
        return None


def block_for_prompt(row: dict | None = None) -> str | None:
    """What a LIVE flip would hand the Executive beside the projection: the returned nodes as plain first-person
    estate lines. Returns None while ESTATE_ASK_LIVE is False — and nothing calls this today, so the prompt path
    is byte-identical to before this module existed."""
    if not ESTATE_ASK_LIVE:
        return None
    row = row or _last["row"]
    if not row or not row.get("returned"):
        return None
    return "What my own record says, asked:\n" + "\n".join(f"- ({n['type']}) {n['text']}" for n in row["returned"])


def _log(rec: dict) -> None:
    path = profile.guard_path(_LOG)   # fence resolved OUTSIDE the fail-open try (D-0179 / D-0250 convention)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def status() -> dict:
    try:
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()]
        n = len(rows)
        subset = sum(1 for r in rows if r.get("returned_subset_of_projection"))
        comp = sum(1 for r in rows if r.get("has_competence"))
        return {"rows": n, "live": ESTATE_ASK_LIVE,
                "by_type": {t: sum(1 for r in rows if r.get("input_type") == t) for t in ("human", "internal")},
                "returned_subset_of_projection": subset, "has_competence": comp,
                "redundant_share": round(subset / n, 3) if n else None}
    except Exception:
        return {"rows": 0, "live": ESTATE_ASK_LIVE}
