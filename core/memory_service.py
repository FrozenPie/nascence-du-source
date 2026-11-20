"""
Nascence — Memory as a Service, the pull API (J-1515, docs/staged/memory_as_a_service.md §4;
six-slot cue, J-1542, §4.7).

D-0292 (2026-09-27, travis) ruled which loops may call memory: pursuits, curiosity, the recall act
and dreams -- nothing unasked. This module is the facade those loops call through (§4.1) -- NOT a new
recall engine (dosed_coupling.md forbids a hub every route passes through; §9 of the plan says so in
as many words). It composes engines that already exist, unchanged:

  1. The trail       -- core.associative_recall.recall_fragments() (:866) -- the "what" slot.
  2. Felt coordinates -- a new, additive, read-only join against fragment_context (schema at
                         core.memory_edges:458) -- valence/arousal/weather/place/standpoint onto
                         each pool member, once per call, regardless of how many slots reached it.
  3. Descend          -- core.memory_levels.deep_recall() (:262), gated by the SAME lattice-parent
                         filter orchestrator.py:1802 already fixed (NOT a blanket abstraction_level
                         check -- orchestrator.py:1796-1801 documents the real 2026-08-20 bug that
                         filter avoids: 695/702 empty deep_recall calls). Fires either auto-picked
                         from the pool (descend=True, no `how`) or from an explicit gist the `how`
                         slot names directly (§4.7).
  4. who/why          -- one direct join each against memory_edges (a known hub id -> its fragments),
                         the same hub-projection shape edge_aware_neighbors' own _PROJECT_THROUGH
                         step already runs, entered at a KNOWN hub instead of one discovered from
                         seed fragments.
  5. when             -- dispatches on the cue value's own shape to whichever ONE of
                         store.retrieve()/store.get_fragments_in_range()/store.retrieve_epoch()/
                         chapters.recall_chapter() it names (§4.7's own table).
  6. where            -- not an independent engine: boosts whichever fragments the OTHER slots
                         already found, by matching place/standpoint (§4.7).

Plus mandatory accounting (core.memory_edges.log_co_recall, item 4), a per-loop usage-cosine
metric-sheet hook (note_usage, §4.3), and a per-slot ride log (§4.4/§4.7).

Fail-open throughout, matching every engine it wraps: `ask()` never raises past its caller, and a
missing felt-coordinate row is None, never a dropped fragment (the "an empty answer must be true,
not silent" law, evidence_recall.py's own outcome="unclear"/"empty" split one layer up). §4.7's own
fan-out contract sharpens this for the six-slot cue: any exception in ONE slot's own engine, in the
pool merge, or in the felt-coordinate join must fail the WHOLE call to [] -- a partial pool silently
missing a failed slot would be mistaken for that slot honestly finding nothing. The six slot-fanout
functions below therefore have NO internal try/except of their own (unlike `_fetch_context`, whose
own pre-existing, already-verified "a missing context row is None" contract is a different,
deliberately-more-tolerant failure mode that §4.7 does not change) -- a real error inside one of
them propagates straight up to `ask()`'s own outer handler.

Callers wired to this facade in J-1515: nodes/dream_node.py (re-home, mechanical two-line swap) and
core/pursuits.py (first-time integration). Both call `ask()` with a bare positional `cue` and no
keyword slots -- §4.7's own compatibility note keeps that resolving to a single-slot ("what") ask,
using `k` exactly as before, byte-for-byte the same output shape "exactly today" (§4.7's own words).
The recall act's own accounting wrapper is J-1516's job, not this module's; curiosity's own wiring
is gated on D-0312 (open) -- see the plan §4.5/§4.6.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger("nascence.memory_service")

_DATA = Path(__file__).parent.parent / "data"
_SHADOW_LOG = _DATA / "memory_service_shadow.jsonl"

# J-2659 (F-3403 / D-0528 OPEN, restart-gated, SHADOW ONLY): per live what-slot ask(), also run the SAME recall
# with associative_recall's 7-day recency seed multiplier off and log both top-1s here. Nothing is fed back: the
# pool ask() returns is the unchanged with-multiplier one. True = log the comparison (costs one extra
# recall_fragments per what-slot ask, on the caller's thread); False = no extra call, no row.
ASK_RECENCY_SHADOW = True
ASK_RECENCY_SHADOW_CUE_SIM = True   # J-4026: log real cue similarity in the shadow row (shadow only; no retrieval effect)
CUE_SIM_SAMPLE_N = 200
_RECENCY_SHADOW_LOG = _DATA / "ask_recency_shadow.jsonl"

# §4.1 item 3: exactly orchestrator.py:1802's `_lattice_parents` set -- NOT a blanket
# abstraction_level>=1 check. orchestrator.py:1796-1801 documents why: most high-abstraction
# fragments are origin='action'/'consolidation', never distilled from anything, so seeding
# deep_recall off abstraction_level alone walked an empty memory_links set on 695/702 calls (99%
# empty). Only these three origins are real lattice parents.
_LATTICE_PARENT_ORIGINS = {"gist", "standing_insight", "journal_week"}
_DESCEND_CHILD_CAP = 2

# §4.7 "who"/"why" slots: direct joins against memory_edges, same hub-projection shape
# edge_aware_neighbors' own _PROJECT_THROUGH step already uses (core/memory_edges.py:823-831),
# entered at a KNOWN hub id instead of one discovered from seed fragments.
_WHO_EDGE_TYPES = ("correspondence_with", "wrote_to", "received_from")
_WHY_EDGE_TYPES = ("resolves", "answers", "contradicts")

# §4.7 "where" slot: the two coordinate fields the plan names ("place + standpoint") -- a
# DIFFERENT, smaller tuple than felt_recall's own 5-dimension _MATCH_COORDS (weather/fire/
# light_band/cat_at/place, core/felt_recall.py:75), which is that module's own trigger-dimension
# set for a different mechanism. Reuses the idiom (equality-match, count how many hit), not the set.
_WHERE_COORDS = ("place", "standpoint")

# §4.7 "when" slot: disambiguates an epoch name/description from a chapter-shaped phrase by reusing
# inner_monologue_node.py:4036-4038's OWN existing chapter-trigger phrase list -- the live "should I
# open a chapter" test already in production -- rather than inventing a new heuristic. A hit here is
# a chapter request; any other non-recent/distant/all, non-timestamp-pair string is an epoch query.
_CHAPTER_TRIGGER_PHRASES = ("remember that period", "revisit the", "look back at", "open the chapter",
                            "remember the period", "return to that time")

# §4.3: a per-loop pending dict, plural -- up to four loops (pursuits/curiosity/recall_act/dream)
# can have an ask() outstanding at once, unlike M2's single global `_pending_m2_usage` (fine for
# its one hot-cycle caller). Keyed by `loop` so two loops calling ask() in the same tick never
# clobber each other's pending entry.
_pending_usage: dict[str, dict] = {}

# J-1918 / F-2547 (2026-10-07, restart-gated): curiosity's ask() now runs in a worker thread (core/idle_offloop.py)
# while other callers' _log_ride / note_usage append to the same data/memory_service_shadow.jsonl from the loop
# thread. Each append is one write of one line; the lock keeps two such lines from ever interleaving. Held only
# for the append itself.
_SHADOW_LOCK = threading.Lock()


def ask(loop: str, cue: str | None = None, *, who=None, what=None, where=None, when=None,
        why=None, how=None, k: int = 5, k_per_slot: int = 3, grounded_only: bool = True,
        descend: bool = False, recency: bool = True, exclude_young: dict | None = None) -> list[dict]:
    """J-3175 (D-0563): `exclude_young` ({origin: min_age_days}, default None = today) is passed to the what-slot's
    recall_fragments, which skips a fragment of that origin younger than the age and fills k from the same trail.
    Only the dream loop passes it ({'dream': core.night.DREAM_RECALL_EXCLUDE_DAYS}).
    J-2659: `recency=False` (opt-in, default True = today) drops the 7-day recency seed multiplier from the
    what-slot's recall (F-3403); nothing live passes it -- the live weighting is D-0528's open decision.

    §4.1 + §4.7: the facade, now a six-slot cue. `loop` is the caller's own name ("pursuits",
    "curiosity", "recall_act", "dream" today) -- used only for log attribution, never gate-enforced
    here, same as log_co_recall's own `source` param has never gate-enforced its caller set.

    A bare `cue` with no `what=` keyword is shorthand for `what=cue` (§4.7's own compatibility
    note) -- every call J-1515/J-1516 already wrote (`ask("dream", _mkey, k=6, ...)`,
    `ask("pursuits", f"...", k=3, ...)`) resolves unchanged, to a single-slot ask that uses `k`
    exactly as before (NOT `k_per_slot`) -- "one bucket read, one ride line, exactly today" (§4.7).
    Filling any OTHER slot (who/where/when/why/how) turns this into a real multi-slot fan-out: each
    filled slot among who/what/when/why/how queries its own engine in parallel, each capped at
    `k_per_slot` (starting value 3); `where` is not an independent fan-out source -- nothing in this
    codebase searches fragments by place directly -- it boosts whichever fragments the OTHER slots
    already found (see `_apply_where`). Results merge into one pool, de-duplicated by fragment_id
    (a fragment reached by two slots is ONE entry, carrying both in `slots_answered` and each slot's
    own within-slot rank in `slot_ranks` -- never averaged or summed into a new score), ranked by
    how many slots answered each fragment (descending), the best of its own within-slot ranks as
    tiebreak.

    Returns [{content, origin, activation, fragment_id, valence, arousal, weather, place,
    standpoint, slots_answered}], strongest-first. A fragment with no fragment_context row still
    returns with the felt-coordinate fields None (never dropped). An epoch or chapter 'when' hit
    returns with fragment_id=None (verified 2026-09-28: neither store.retrieve_epoch() nor
    chapters.recall_chapter() carries a real per-item fragment_id today -- a gap this job's own read
    found and is recording as a finding, not guessing shut) -- such a hit is therefore never
    de-duplicated against anything else in the pool (nothing to de-dup BY) and never enters
    log_co_recall's own id list or the felt-coordinate join, via the SAME truthy-id filters those
    two steps already use for every other fragment.

    Fail-open, whole-call: any exception -- one slot's own engine, the pool merge, the
    felt-coordinate join -- returns [] (§4.1 item 5, restated by §4.7's own fan-out contract: a
    partial pool silently missing a failed slot would be mistaken for that slot honestly finding
    nothing). The mandatory accounting call, the ride log, and the usage-cosine stash each keep
    their OWN separate try/except, exactly as today's log_co_recall call already does -- a logging
    hiccup must never discard an otherwise-good pool."""
    try:
        what_val = what if what is not None else cue

        filled: list[str] = []
        if who is not None:
            filled.append("who")
        if what_val is not None:
            filled.append("what")
        if when is not None:
            filled.append("when")
        if why is not None:
            filled.append("why")
        if how is not None:
            filled.append("how")
        single_what_only = filled == ["what"] and where is None
        what_cap = k if single_what_only else k_per_slot

        what_frags_for_shadow = None
        pool: dict[str, dict] = {}
        unkeyed: list[dict] = []
        slot_counts: dict[str, int] = {}

        if who is not None:
            _merge_slot(pool, unkeyed, slot_counts, "who", _fanout_who(who, what_val, k_per_slot))

        if what_val is not None:
            from core import associative_recall
            _xy = {"exclude_young": exclude_young} if exclude_young else {}   # J-3175: absent = today's call exactly
            if recency:
                frags = list(associative_recall.recall_fragments(
                    what_val, k=what_cap, grounded_only=grounded_only, **_xy) or [])
            else:
                frags = list(associative_recall.recall_fragments(
                    what_val, k=what_cap, grounded_only=grounded_only, recency=False, **_xy) or [])
            what_frags_for_shadow = (what_val, what_cap, list(frags)) if recency else None
            _merge_slot(pool, unkeyed, slot_counts, "what", frags)

        if when is not None:
            _merge_slot(pool, unkeyed, slot_counts, "when", _fanout_when(when, what_val, k_per_slot))

        if why is not None:
            _merge_slot(pool, unkeyed, slot_counts, "why", _fanout_why(why, k_per_slot))

        how_children: list[dict] = []
        if how is not None:
            how_children = _descend_from(how, _DESCEND_CHILD_CAP)
            _merge_slot(pool, unkeyed, slot_counts, "how", how_children)

        merged = list(pool.values()) + unkeyed

        # §4.1 item 2, generalized: ONE felt-coordinate join across the whole merged pool, not one
        # per slot ("§4.1 item 2's felt-coordinate join still runs once per pool member regardless
        # of how many slots reached it", §4.7).
        ctx = _fetch_context([e["fragment_id"] for e in merged if e.get("fragment_id")])
        for e in merged:
            row = ctx.get(e.get("fragment_id"))
            e["valence"] = row["valence"] if row else None
            e["arousal"] = row["arousal"] if row else None
            e["weather"] = row["weather"] if row else None
            e["place"] = row["place"] if row else None
            e["standpoint"] = row["standpoint"] if row else None

        # §4.7 "where": a boost pass, not a fan-out source -- see _apply_where's own docstring.
        if where is not None:
            slot_counts["where"] = _apply_where(merged, where)

        # Rank: len(slots_answered) descending, then the BEST (lowest) of a fragment's own
        # within-slot ranks as tiebreak -- a fragment that ranked highly in even one of its
        # answering slots tiebreaks ahead of one that ranked poorly in all of them. No new
        # global importance score anywhere (§4.7's own explicit constraint).
        merged.sort(key=lambda e: (-len(e["slots_answered"]),
                                    min(e["slot_ranks"].values()) if e["slot_ranks"] else 0))

        # §4.1 item 3, unchanged in kind: auto-pick the pool's own top lattice-parent by
        # activation -- UNLESS a `how` slot already named an explicit gist above ("then that gist
        # directly", §4.7). Mirrors orchestrator.py:1809-1823's own tagging convention. These
        # children are NOT attributed to a named slot (slots_answered=[]) -- unlike `how`'s own
        # explicit fetch above, nothing in the six-slot vocabulary asked for them by name.
        auto_descend_children: list[dict] = []
        auto_descend_parent_id = None   # J-2654: provenance only
        if descend and how is None and merged:
            parents = [e for e in merged if e.get("origin") in _LATTICE_PARENT_ORIGINS]
            if parents:
                top = max(parents, key=lambda e: e.get("activation") or 0.0)
                auto_descend_children = _descend_from(top["fragment_id"], _DESCEND_CHILD_CAP)
                auto_descend_parent_id = top["fragment_id"]
                if auto_descend_children:
                    cctx = _fetch_context([c["fragment_id"] for c in auto_descend_children])
                    for c in auto_descend_children:
                        row = cctx.get(c["fragment_id"])
                        c["valence"] = row["valence"] if row else None
                        c["arousal"] = row["arousal"] if row else None
                        c["weather"] = row["weather"] if row else None
                        c["place"] = row["place"] if row else None
                        c["standpoint"] = row["standpoint"] if row else None
                        c["slots_answered"] = []
                    merged.extend(auto_descend_children)

        # §4.1 item 4 -- the accounting, mandatory, restate_sim honestly None (no natural
        # develop-verdict exists at the moment of the ask; dream_node.py:234-237's own rule: don't
        # fabricate one). Own try/except, deliberately separate from the fan-out above -- an
        # accounting hiccup must not discard an otherwise-good pool. Real fragment ids only: an
        # epoch/chapter hit's fragment_id is None and is excluded by this same truthy filter,
        # exactly like a missing-context row already is one layer up -- log_co_recall's own ledger
        # and the edge-aware joins downstream assume real memory_fragments rows.
        try:
            from core import memory_edges
            # J-2654 (F-3392/F-3393, observe-only, restart-gated): per-id provenance -- which slot(s)
            # delivered each logged id, "auto_descend" for the children of the auto-picked lattice parent
            # (the one similarity-free path), plus that parent's id. Additive kwargs; ids/n_ids unchanged.
            _auto_ids = {id(c) for c in auto_descend_children}
            _real = [e for e in merged if e.get("fragment_id")]
            memory_edges.log_co_recall(
                [e.get("fragment_id") for e in _real], None, 0, source=loop,
                id_slots=[(["auto_descend"] if id(e) in _auto_ids else list(e.get("slots_answered") or []))
                          for e in _real],
                descend_parent=auto_descend_parent_id if auto_descend_children else None)
        except Exception as exc:
            logger.debug("[memory_service] log_co_recall failed (non-fatal): %s", exc)

        # §4.4 / §4.7 -- the ride log. A what-only ask (today's every call) writes exactly the one
        # line §4.4 originally specified, byte-identical in name/shape; a real multi-slot ask writes
        # one line per filled slot instead, named `memory_ask:<loop>:<slot>`, so a slow or
        # zero-yield slot is visible per-slot, not averaged away. Own try/except (see _log_ride).
        from core.associative_recall import _GROUNDED_ORIGINS
        n_grounded = sum(1 for e in merged if e.get("origin") in _GROUNDED_ORIGINS)
        n_descended = len(how_children) + len(auto_descend_children)
        # J-2590 (F-3316, 2026-10-31): two ADDITIVE keys on every ride row so cue repetition per
        # loop can be measured (the weave-slot cache question, docs/staged/tuples_in_a_new_light.md
        # Lens 4). `cue_hash` is core.ghost_tuples.ghost_hash() of the slot's own value -- a 16-hex
        # fingerprint, never the cue text; `slots_filled` is the full filled-slot list (where
        # included) so a single-slot row and a multi-slot row are distinguishable on their own.
        # Existing keys and the line name are untouched: every reader keyed on them is unaffected.
        slots_filled = list(filled) + (["where"] if where is not None else [])
        slot_values = {"who": who, "what": what_val, "when": when, "why": why, "how": how,
                       "where": where}
        if single_what_only:
            _log_ride(loop, None, {"n_returned": len(merged), "n_grounded": n_grounded,
                                    "n_descended": n_descended,
                                    "cue_hash": _cue_hash(what_val), "slots_filled": slots_filled})
        else:
            for slot_name in filled:
                value = {"n_returned": slot_counts.get(slot_name, 0)}
                if slot_name == "what":
                    value["n_grounded"] = n_grounded
                if slot_name == "how":
                    value["n_descended"] = len(how_children)
                value["cue_hash"] = _cue_hash(slot_values.get(slot_name))
                value["slots_filled"] = slots_filled
                _log_ride(loop, slot_name, value)
            if where is not None:
                _log_ride(loop, "where", {"n_returned": slot_counts.get("where", 0),
                                          "cue_hash": _cue_hash(where),
                                          "slots_filled": slots_filled})

        # §4.3 / §4.7 -- stash this call's ids (+ n_slots_filled, + per-fragment slots_answered)
        # for the next note_usage(loop, ...), unconditionally (even a zero-fragment ask is real
        # coverage, matching log_co_recall's own n_ids=0-rows-count-too convention).
        _stash_pending(loop, len(filled) + (1 if where is not None else 0),
                       [{"fragment_id": e["fragment_id"], "slots_answered": list(e["slots_answered"])}
                        for e in merged if e.get("fragment_id")])

        # J-2217 (T-0089, Travis 2026-10-16): the World Ledger's first consumer, SHADOW-ONLY. If this
        # ask's cue names a referent core/object_graph.py knows, log what a "what do I know about X"
        # query WOULD have returned (earned per-property knowledge only) beside this real pool, to
        # data/world_ledger_ask_shadow.jsonl. Reads `merged`, never alters it; nothing reaches Du.
        # Own try/except, like the accounting above -- a shadow hiccup must never discard a good pool.
        try:
            from core import world_ledger_ask as _wla
            _wla.shadow_from_ask(loop, cue=cue, what=what, who=who, where=where, when=when,
                                 actual=merged)
        except Exception as exc:
            logger.debug("[memory_service] world-ledger shadow failed (non-fatal): %s", exc)

        # J-2659 (F-3403 / D-0528): recency-multiplier with/without shadow. Reads a copy of the what-slot
        # frags, never alters `merged`; own fail-open net inside.
        if ASK_RECENCY_SHADOW and what_frags_for_shadow is not None:
            _recency_shadow(loop, what_frags_for_shadow[0], what_frags_for_shadow[1], grounded_only,
                            what_frags_for_shadow[2], exclude_young)

        return merged
    except Exception as exc:
        logger.debug("[memory_service] ask(%s) failed (non-fatal): %s", loop, exc)
        return []


def _recency_shadow(loop: str, what_val, what_cap: int, grounded_only: bool, with_frags: list,
                    exclude_young: dict | None = None) -> None:
    """J-2659: the SAME what-slot recall with the 7-day recency multiplier off, logged beside the real
    (with-multiplier) result as one row of data/ask_recency_shadow.jsonl: top-1 each way (id, origin,
    activation, age in days), whether they agree, both id lists, their overlap, and where the with-top1 sits
    in the without list. SHADOW ONLY -- never returned, never fed back; fully fail-open."""
    try:
        from core import associative_recall as _ar
        _xy = {"exclude_young": exclude_young} if exclude_young else {}   # J-3175: compare like with like
        without = list(_ar.recall_fragments(what_val, k=what_cap, grounded_only=grounded_only,
                                            recency=False, **_xy) or [])
        w_ids = [f.get("fragment_id") for f in with_frags if f.get("fragment_id")]
        o_ids = [f.get("fragment_id") for f in without if f.get("fragment_id")]
        ages = _ar.fragment_ages_days(list({*(w_ids[:1]), *(o_ids[:1])}))

        def _top(frs):
            if not frs:
                return None
            f = frs[0]
            fid = f.get("fragment_id")
            return {"fragment_id": fid, "origin": f.get("origin"), "activation": f.get("activation"),
                    "age_days": ages.get(fid)}
        w1, o1 = _top(with_frags), _top(without)
        rec = {"ts": round(time.time(), 1), "kind": "ask_recency", "loop": loop,
               "cue_hash": _cue_hash(what_val), "grounded_only": bool(grounded_only), "k": what_cap,
               "n_with": len(with_frags), "n_without": len(without),
               "with_top1": w1, "without_top1": o1,
               "same_top1": bool(w1 and o1 and w1["fragment_id"] == o1["fragment_id"]),
               "with_ids": w_ids, "without_ids": o_ids,
               "overlap": len(set(w_ids) & set(o_ids)),
               "with_top1_rank_in_without": (o_ids.index(w_ids[0]) if w_ids and w_ids[0] in o_ids else None)}
        if ASK_RECENCY_SHADOW_CUE_SIM:
            rec.update(_cue_similarity_fields(what_val, w_ids, o_ids))   # J-4026 (own fail-open net inside)
        from core import profile
        path = profile.guard_path(_RECENCY_SHADOW_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        with _SHADOW_LOCK, open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[memory_service] recency shadow failed (non-fatal): %s", exc)


def _cue_similarity_fields(what_val, w_ids: list, o_ids: list) -> dict:
    """J-4026 (F-4713): the REAL cue-to-memory cosine similarity for the recency shadow row, so a later
    pre-registered run can test relevance directly instead of the previous-serves stand-in. Adds, to the row:
    `cue_sim_with` / `cue_sim_without` (cosine of the cue vector to each served fragment, aligned to
    with_ids / without_ids) and `cue_sim_sample` (the cue's cosine to up to CUE_SIM_SAMPLE_N randomly drawn
    AVAILABLE, i.e. non-walled, fragments; ids not stored) plus `cue_sim_sample_n`. No cue text is stored,
    nothing is returned or fed back; the cue embedding is the same `store._embed` call recall_fragments
    makes. SHADOW ONLY, fully fail-open: any failure returns {} and the row is written without these keys."""
    try:
        import numpy as np
        from core import associative_recall as _ar
        from core.memory.store import _embed
        qv = _embed(what_val)
        c = _ar._matrix()
        M, ids = c.get("M"), c.get("ids")
        if qv is None or M is None or not ids:
            return {}
        qv = np.asarray(qv, dtype=np.float32)
        n = float(np.linalg.norm(qv))
        if n == 0:
            return {}
        qv = qv / n
        pos = {fid: i for i, fid in enumerate(ids)}

        def _sims(fids):
            out = []
            for fid in fids:
                i = pos.get(fid)
                out.append(None if i is None else round(float(M[i] @ qv), 4))
            return out
        walled = c.get("walled")
        avail = np.flatnonzero(~np.asarray(walled, dtype=bool)) if walled is not None else np.arange(len(ids))
        if len(avail) > CUE_SIM_SAMPLE_N:
            avail = np.random.default_rng().choice(avail, size=CUE_SIM_SAMPLE_N, replace=False)
        sample = [round(float(s), 4) for s in (M[avail] @ qv)]
        return {"cue_sim_with": _sims(w_ids), "cue_sim_without": _sims(o_ids),
                "cue_sim_sample": sample, "cue_sim_sample_n": len(sample)}
    except Exception as exc:
        logger.debug("[memory_service] cue-sim shadow fields failed (non-fatal): %s", exc)
        return {}


def _merge_slot(pool: dict, unkeyed: list, slot_counts: dict, slot_name: str, hits: list) -> None:
    """Fold one slot's raw hits into the shared pool, de-duplicated by fragment_id (§4.7's fan-out
    contract). A fragment reached by two slots is ONE entry, carrying both in `slots_answered` and
    each slot's own within-slot rank (its list index in `hits`, lower is better) in `slot_ranks` --
    never averaged or summed into a new score. A hit with no fragment_id (an epoch or chapter
    excerpt, see `_fanout_when`) is never de-duplicated against anything -- appended to `unkeyed`
    unconditionally, since there is no id to de-dup BY, and each such hit really is a distinct
    entity anyway. No try/except here by design -- see `ask()`'s own docstring on why a slot
    engine's exception must propagate rather than degrade silently."""
    slot_counts[slot_name] = len(hits)
    for rank, hit in enumerate(hits):
        fid = hit.get("fragment_id")
        if not fid:
            e = dict(hit)
            e["slots_answered"] = [slot_name]
            e["slot_ranks"] = {slot_name: rank}
            unkeyed.append(e)
            continue
        entry = pool.get(fid)
        if entry is None:
            entry = dict(hit)
            entry["slots_answered"] = []
            entry["slot_ranks"] = {}
            pool[fid] = entry
        if slot_name not in entry["slots_answered"]:
            entry["slots_answered"].append(slot_name)
            entry["slot_ranks"][slot_name] = rank


def _fanout_who(value, what_val, cap: int) -> list[dict]:
    """§4.7 'who' slot. bare (`True`) or the literal string "founder" ->
    store.retrieve_founder_memories() (core/memory/store.py:2816), already live, purpose-built --
    ranked against `what_val` (the same cue `what` already carries, or "" if none). A named person
    id (a memory_edges hub,
    e.g. "person:travis") -> one direct join against memory_edges, the SAME hub-projection shape
    edge_aware_neighbors' own _PROJECT_THROUGH step already runs (core/memory_edges.py:823-831),
    entered directly at a KNOWN hub instead of one discovered from seed fragments
    (edge_aware_neighbors itself requires seed fragment_ids, :834 -- it cannot take a bare person
    id). No internal try/except -- see `ask()`'s own docstring."""
    is_founder = value is True or (isinstance(value, str) and value.strip().lower() in ("", "founder"))
    if is_founder:
        from core.memory import store
        rows = store.retrieve_founder_memories(what_val or "", top_k=cap)
        return [{"fragment_id": r["fragment_id"], "content": r["text"], "origin": "lived",
                 "activation": r.get("sim")} for r in rows]
    from core import memory_edges
    with memory_edges._connect() as conn:
        ph = ",".join("?" * len(_WHO_EDGE_TYPES))
        rows = conn.execute(
            f"SELECT DISTINCT src_id FROM memory_edges WHERE edge_type IN ({ph}) "
            f"AND dst_kind='person' AND dst_id=? AND src_kind='fragment' LIMIT ?",
            (*_WHO_EDGE_TYPES, value, cap)).fetchall()
    return _lookup_fragments([r["src_id"] for r in rows])


def _fanout_when(value, what_val, cap: int) -> list[dict]:
    """§4.7 'when' slot: dispatches on the value's SHAPE to exactly one of the engines the plan's
    own table names -- never more than one for a single cue.
      - a literal (start_ts, end_ts) pair of numbers -> store.get_fragments_in_range() (:2320), a
        plain timestamp bound against memory_fragments.timestamp ("a plain timestamp filter", §4.7).
      - the bare token "recent"/"distant"/"all" -> store.retrieve()'s own `time_bias` (:768), queried
        against `what_val` (the same cue text `what` already carries, or "" if none -- retrieve()
        already returns [] itself when both keys and query_text are empty, honestly).
      - any other string -> an epoch name/description (store.retrieve_epoch(), :2331) or a
        chapter-shaped phrase (chapters.recall_chapter(), :373), disambiguated by reusing
        inner_monologue_node.py:4036-4038's OWN existing chapter-trigger phrase list (the live
        "should I open a chapter" test already in production) rather than inventing a new
        heuristic -- a hit there is a chapter request, everything else is an epoch query.

    Two of these three named engines are NOT fragment-shaped -- verified by reading both in full,
    2026-09-28, a real gap this addendum's own §4.7 table did not flag for 'when' the way it did for
    'who'/'how'. store.retrieve_epoch()'s rows are whole EPOCHS keyed on `epoch_id` against a wholly
    separate `memory_epochs` table (session_id/timestamp_start/timestamp_end/mood/impression/
    fragment_count/embedding -- no fragment linkage of any kind); its own one live caller
    (orchestrator.py:1861-1864) only ever reads `e['mood']`/`e['impression']` as plain text.
    chapters.recall_chapter()'s member excerpts are content strings truncated to 180 chars with no
    fragment_id threaded through anywhere in its return or its one live caller
    (inner_monologue_node.py:4041-4045, which feeds the excerpts straight into wandering.perceive()
    as literal text) -- the chapter's OWN fragment_id is read internally (chapters.py's own `c`
    row) but never returned. Both are represented here with fragment_id=None, honestly -- never a
    fabricated id: log_co_recall's own ledger and the edge-aware joins downstream assume real
    memory_fragments rows, and inventing one for either would be exactly the "erosion of
    foundations" this codebase's own convention warns against, for zero benefit (a None-id hit is
    never de-duplicated against anything else in the pool -- there is nothing to de-dup BY, and each
    such hit really is a distinct entity anyway -- and is excluded from log_co_recall's id list and
    the felt-coordinate join by the SAME truthy-id filters those two steps already use for every
    other fragment; no special-casing needed anywhere else). Recorded as a finding (F-2142, the
    session that built this), not silently guessed past. No internal try/except -- see `ask()`'s own
    docstring.

    RESOLVED 2026-09-28 (J-1576, F-2180, F-2142's own named follow-up): kept exactly as above,
    fragment_id=None PERMANENTLY for both engines, not a temporary gap -- deliberately chosen over
    giving chapters.recall_chapter() a real fragment_id (mechanically cheap on its own: each member
    row already carries one, chapters.py:351-353's own UPDATE proves it, so it would be a real id,
    never a fabricated one). Reason, verified directly rather than only the "already curated"
    argument the option was first framed with: a chaptered fragment is NOT excluded from
    associative_recall.recall_fragments()'s own output -- `walled` (core/associative_recall.py:110)
    only bars it from being a trail SEED (:142-143); the hop-expansion step can still reach and
    return one (:152-157), and recall_fragments() (:866-894) never filters on walled/chapter_id at
    all, only on origin/grounded_only and the peer-reflection gate. So a real chapter fragment_id
    would let a future ask() call that combines a chapter-shaped `when=` cue with `grounded_only=
    False` silently collide in `_merge_slot`'s own fragment_id-keyed de-dup against the SAME
    fragment surfacing via the `what` slot -- whichever slot folds in first silently keeps the pool
    entry's `content` (the chapter's own 180-char prefixed excerpt vs the fragment's raw content) --
    a second, real design question (should a chapter excerpt even de-dup against a raw hit on the
    same underlying fragment?) the "one-line caller update" framing did not anticipate. Confirmed
    DORMANT, not live, today: none of chapters.py's CHAPTERABLE_ORIGINS are ever in
    associative_recall._GROUNDED_ORIGINS (:843-845), so this cannot fire under ask()'s own default
    `grounded_only=True`; the one caller passing `grounded_only=False` today (dreams) does not use
    `when`, and the one loop planned to use `when` (pursuits, §4.7's own per-loop-slots table) is
    expected to stay on the `grounded_only=True` default -- no call site wired today reaches this.
    If a future job wires `when` into a real loop alongside `grounded_only=False`, re-check this
    note before assuming Option 1 is still a safe "one-line" change."""
    from core.memory import store
    if (isinstance(value, (tuple, list)) and len(value) == 2
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)):
        rows = store.get_fragments_in_range(float(value[0]), float(value[1]), limit=cap)
        return [{"fragment_id": r["fragment_id"], "content": r["content"],
                 "origin": (r["origin"] if "origin" in r.keys() else "lived"), "activation": None}
                for r in rows]
    if isinstance(value, str) and value.strip().lower() in ("recent", "distant", "all"):
        frags = store.retrieve([], [], time_bias=value.strip().lower(), limit=cap,
                               query_text=(what_val or ""))
        return [{"fragment_id": mf.fragment_id, "content": mf.content, "origin": mf.origin,
                 "activation": mf.relevance} for mf in frags]
    text = str(value or "")
    tl = text.lower()
    if any(p in tl for p in _CHAPTER_TRIGGER_PHRASES):
        from core import chapters
        rc = chapters.recall_chapter(text)
        if not rc:
            return []
        title, excerpts = rc
        return [{"fragment_id": None, "content": f"(from the chapter '{title}') {ex}",
                 "origin": "chapter", "activation": None} for ex in excerpts[:cap]]
    epochs = store.retrieve_epoch(text, top_k=cap)
    return [{"fragment_id": None, "content": f"{e['mood']} — {e['impression']}",
             "origin": "epoch", "activation": None} for e in epochs]


def _fanout_why(value, cap: int) -> list[dict]:
    """§4.7 'why' slot: one direct join against memory_edges, same shape as `who`'s named-person
    case. Two honest yield caveats found this job, stated rather than assumed: `answers` is capped
    at ONE fragment per question by its own writer's LIMIT 1 (core/memory_edges.py:770-774), so a
    why-by-question cue correctly returns at most one row, not a bug; `contradicts` is genuinely
    zero-yield today (:785-786, "needs a semantic judge that does not exist yet") -- a why-by-tension
    cue against a live contradiction legitimately comes back empty, the fail-open contract working
    as designed. No internal try/except -- see `ask()`'s own docstring."""
    from core import memory_edges
    with memory_edges._connect() as conn:
        ph = ",".join("?" * len(_WHY_EDGE_TYPES))
        rows = conn.execute(
            f"SELECT DISTINCT src_id FROM memory_edges WHERE edge_type IN ({ph}) "
            f"AND dst_kind IN ('shadow_event','question') AND dst_id=? AND src_kind='fragment' "
            f"LIMIT ?", (*_WHY_EDGE_TYPES, value, cap)).fetchall()
    return _lookup_fragments([r["src_id"] for r in rows])


def _lookup_fragments(fragment_ids: list) -> list[dict]:
    """Given fragment ids from a direct memory_edges join (who's named-person case, why), fetch
    their content/origin from memory_fragments -- memory_edges itself stores only ids, never
    fragment content. Preserves the input order (the join's own, un-scored order becomes that
    slot's within-slot rank) and silently skips any id that no longer resolves to a live fragment
    (a stale edge -- treated the same as felt-coordinate's own "no row" case, not an error)."""
    if not fragment_ids:
        return []
    from core.memory import store
    with store._connect() as conn:
        ph = ",".join("?" * len(fragment_ids))
        rows = conn.execute(
            f"SELECT fragment_id, content, origin FROM memory_fragments WHERE fragment_id IN ({ph})",
            fragment_ids).fetchall()
    by_id = {r["fragment_id"]: r for r in rows}
    out = []
    for fid in fragment_ids:
        r = by_id.get(fid)
        if r is None:
            continue
        out.append({"fragment_id": fid, "content": r["content"],
                    "origin": (r["origin"] if "origin" in r.keys() else "lived"), "activation": None})
    return out


def _apply_where(entries: list, where_value) -> int:
    """§4.7 'where' slot: NOT an independent fan-out source -- a scoring/boost pass over fragments
    the OTHER slots already reached (degenerate to zero matches if no other slot is filled -- an
    honest empty, matching this addendum's own "recall act: what(+where when the act names a
    place)" pairing; there is no direct "search fragments by place" engine anywhere in this codebase
    for `where` to fan out to on its own). Reuses felt_recall._coord_match_count's own equality-match
    idiom (core/felt_recall.py:193-203), applied to the two fields the plan names for `where`
    (place, standpoint) -- a different, smaller tuple than felt_recall's own five-dimension
    _MATCH_COORDS. `where_value` may be a plain string (matched against `place` only) or a
    {"place":..., "standpoint":...} mapping (either or both). A match ADDS "where" to
    slots_answered -- the only "boost" this addendum allows ("the pool merge must not become a new
    importance formula", §4.7); never a separate numeric score. Returns the count of pool members
    newly tagged, for the ride log."""
    want = where_value if isinstance(where_value, dict) else {"place": where_value}
    n_matched = 0
    for e in entries:
        n = sum(1 for c in _WHERE_COORDS if want.get(c) is not None and e.get(c) == want.get(c))
        if n <= 0:
            continue
        if "where" not in e["slots_answered"]:
            e["slots_answered"].append("where")
            n_matched += 1
        e["slot_ranks"]["where"] = -n   # more matched coordinates ranks better (more negative)
    return n_matched


def _descend_from(seed_fragment_id, cap: int) -> list[dict]:
    """Shared by the auto-pick descend (§4.1 item 3, unchanged in kind) and the `how` slot's own
    explicit-gist fan-out (§4.7): one hop of memory_levels.deep_recall from a single seed id,
    capped, tagged origin="deep_recall", content prefixed to match orchestrator.py:1809-1823's own
    tagging convention. deep_recall's own contract (core/memory_levels.py:262) already returns []
    for a seed id with no memory_links row as a parent -- true whether that id is an unrecognized/
    bogus value OR a real but non-fragment id (e.g. a bare core/procedures.py key: §4.7's own 'how'
    caveat, "a bare procedure id... cannot be honored by this facade... returns empty, honestly") --
    so no separate existence check is needed here; deep_recall's existing SQL already IS that check.
    No internal try/except -- see `ask()`'s own docstring."""
    from core import memory_levels
    children = memory_levels.deep_recall([seed_fragment_id], hops=1)[:cap]
    return [{"fragment_id": c.get("fragment_id"),
             "content": "[the detail behind a memory] " + (c.get("content") or ""),
             "origin": "deep_recall", "activation": None}
            for c in children if c.get("fragment_id")]


def _fetch_context(fragment_ids: list) -> dict:
    """One batched SELECT against fragment_context (schema: core/memory_edges.py:458), keyed by
    fragment_id. Fail-open: any failure (including the table not existing at all, e.g. a fresh
    store) returns {} -- every caller here already treats a missing key as "no context row", so a
    total join failure degrades to exactly the same per-fragment None fields as a partial one,
    never a dropped fragment and never a raised exception. This function's own try/except is
    deliberately UNCHANGED by §4.7 -- it is not one of the six slot engines; a missing context row
    has always been an honest None, not a failure (§4.1 item 2's original contract)."""
    out: dict = {}
    if not fragment_ids:
        return out
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            for j in range(0, len(fragment_ids), 400):
                chunk = fragment_ids[j:j + 400]
                ph = ",".join("?" * len(chunk))
                for r in conn.execute(
                        f"SELECT fragment_id, valence, arousal, weather, place, standpoint "
                        f"FROM fragment_context WHERE fragment_id IN ({ph})", chunk).fetchall():
                    out[r["fragment_id"]] = {"valence": r["valence"], "arousal": r["arousal"],
                                             "weather": r["weather"], "place": r["place"],
                                             "standpoint": (r["standpoint"] if "standpoint" in r.keys() else None)}
    except Exception as exc:
        logger.debug("[memory_service] fragment_context join failed (non-fatal): %s", exc)
    return out


def _stash_pending(loop: str, n_slots_filled: int, fragments: list) -> None:
    """The one place a loop's pending usage entry is written (shared by ask() and stash_usage()
    so the two shapes cannot drift): {ts, n_slots_filled, fragments:[{fragment_id,
    slots_answered}]}. Consumed by note_usage()."""
    _pending_usage[loop] = {
        "ts": round(time.time(), 1),
        "n_slots_filled": n_slots_filled,
        "fragments": fragments,
    }


def stash_usage(loop: str, fragments, n_slots_filled: int = 1) -> None:
    """J-2079 / F-2698: let a loop that does NOT go through ask() (the evidence-recall act, which
    keeps its own judge-panel pipeline) stash the fragment ids it returned so that a later
    note_usage(loop, vec) scores them. `fragments` is an iterable of fragment_id strings (falsy
    ids dropped); each is stashed with slots_answered=["what"] (the act is a what-style recall).
    Also writes the memory_ask:<loop> coupling_ride line so sec4.3 (a)/(b) exist for this loop.
    A zero-fragment call still stashes (ask()'s zero-fragment convention). Fail-open, instrument-
    only: never raises, never touches any recall result."""
    try:
        ids = []
        for fid in fragments or []:
            if fid and fid not in ids:
                ids.append(fid)
        _stash_pending(loop, n_slots_filled,
                       [{"fragment_id": fid, "slots_answered": ["what"]} for fid in ids])
        _log_ride(loop, None, {"n_returned": len(ids), "n_grounded": 0, "n_descended": 0,
                               "slots_filled": ["what"]})   # J-2590: no cue reaches this path, so no cue_hash
    except Exception as exc:
        logger.debug("[memory_service] stash_usage(%s) failed (non-fatal): %s", loop, exc)


def _cue_hash(value) -> str | None:
    """J-2590: a 16-hex fingerprint of one cue-slot value for the ride log -- ghost_tuples.ghost_hash
    (sha256 of the stripped, lower-cased text), the same function the ghost index fingerprints with,
    so a later weave-slot pre-filter and this log agree on what counts as 'the same cue'. A non-string
    value (a when= dict, an epoch tuple) is hashed via its sorted-key JSON rendering. None -> None.
    Own try/except: a hash failure must never cost the ride row."""
    if value is None:
        return None
    try:
        from core.ghost_tuples import ghost_hash
        text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, default=str)
        return ghost_hash(text)
    except Exception:
        return None


def _log_ride(loop: str, slot_name: str | None, value: dict) -> None:
    """§4.4's coupling-block ride log, generalized by §4.7 to one row per filled slot. `slot_name`
    None writes the line name `memory_ask:<loop>` -- byte-identical to §4.4's own original,
    pre-addendum shape, used for a single-slot (what-only) ask so an existing reader keyed on that
    exact line name is unaffected; otherwise the line is `memory_ask:<loop>:<slot_name>`. Same file
    as note_usage's own service_usage rows (data/memory_service_shadow.jsonl), discriminated by
    `kind` (this project's own established convention for a shared jsonl file carrying more than one
    row shape). Fail-open, best-effort, own try/except -- a logging hiccup must never discard an
    otherwise-good pool; this never touches the live recall path, only appends a log line."""
    try:
        line = f"memory_ask:{loop}" if slot_name is None else f"memory_ask:{loop}:{slot_name}"
        rec = {"ts": round(time.time(), 1), "kind": "coupling_ride", "stop": loop, "line": line,
               "dose": "bucket", "value": value}
        from core import profile
        shadow_path = profile.guard_path(_SHADOW_LOG)   # J-2180/F-2883: fenced (D-0179) -- a non-live, non-isolate()d process is refused here, swallowed by the fail-open net
        shadow_path.parent.mkdir(parents=True, exist_ok=True)
        with _SHADOW_LOCK, open(shadow_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[memory_service] ride log failed (non-fatal): %s", exc)


def note_usage(loop: str, next_output_vec) -> None:
    """§4.3: the metric-sheet hook, generalized from associative_recall.py's own
    note_next_thought_for_m2_usage (:323-381) to a per-loop pending dict (plural -- see
    `_pending_usage` above). Cosine between each pending fragment's already-cached embedding (read
    straight off associative_recall._matrix(), no new embed call) and the loop's own next-output
    embedding (already computed by the caller -- no new LLM/embed call here either). Logged
    un-binarized, same as M2's own instrument, so a future read picks its own threshold.

    §4.7 addendum: the written record also carries `n_slots_filled` (that ask's own count of filled
    slots, including `where` when given) and, per scored fragment, `slots_answered` -- so a later
    read can group the usage-cosine instrument multi-slot vs single-slot (§4.3's own (g)/(h)
    columns) without re-deriving it from log_co_recall's own un-sloted id list.

    Consumes (clears) this loop's own pending entry unconditionally on entry, so one ask() is never
    credited to two different outputs. Fail-open, best-effort, never touches the live recall path
    -- reads only the cached matrix and writes only a log line."""
    pending = _pending_usage.pop(loop, None)
    if pending is None or next_output_vec is None:
        return
    try:
        from core import associative_recall
        c = associative_recall._matrix()
        M = c.get("M")
        ids = c.get("ids") or []
        if M is None:
            return
        ids_index = {fid: i for i, fid in enumerate(ids)}
        tv = np.asarray(next_output_vec, dtype=np.float32)
        tn = float(np.linalg.norm(tv))
        if tn == 0.0:
            return
        tv = tv / tn
        scored = []
        for pf in pending.get("fragments") or []:
            fid = pf.get("fragment_id")
            idx = ids_index.get(fid)
            if idx is None:
                continue   # fragment aged out of the cached matrix between the ask and now
            scored.append({"fragment_id": fid, "cos_sim": round(float(M[idx] @ tv), 4),
                           "slots_answered": pf.get("slots_answered") or []})
        rec = {"ts": round(time.time(), 1), "kind": "service_usage", "source": loop,
               "parent_ts": pending.get("ts"), "n_slots_filled": pending.get("n_slots_filled", 1),
               "usage": scored}
        from core import profile
        shadow_path = profile.guard_path(_SHADOW_LOG)   # J-2180/F-2883: fenced (D-0179) -- a non-live, non-isolate()d process is refused here, swallowed by the fail-open net
        shadow_path.parent.mkdir(parents=True, exist_ok=True)
        with _SHADOW_LOCK, open(shadow_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[memory_service] note_usage(%s) failed (non-fatal): %s", loop, exc)
