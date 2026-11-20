"""
Nascence — Investigation Deepening Shadow (Phase 0 SHADOW built; Phase 1 frontier-line built 2026-09-28).
Full design: docs/plans/investigation_deepening.md. P0 spawned as J-0177 (source: decision:D-0009,
build plan verified 2026-08-24, F-0114). P1 built as J-1585 (source: decision:D-0308, ruled 2026-09-27).

THE IDEA (Travis, 2026-07-07): journal recaps shouldn't be summaries you retrieve — they should be a
progression ledger. Founder's example: at the rockpools he "thinks about things he already has and
tries to expound on them" — shells, then what's IN the shells, then how beach shells differ from snail
shells, then classification. Each visit should add a rung, not repeat the last one.

THE MACHINERY FINDING (07-07, re-verified 2026-08-24): nothing is place- or activity-cued anywhere.
`chapters.py:recall_chapter()` (~line 291) keys purely on title-word overlap; ordinary
`core/memory/store.py:retrieve()` (~line 522) keys on semantic similarity to whatever query_text is
passed. There is no "you are at the rockpools -> here is your rockpool thread." This module is that
missing place cue, in shadow.

P0: at beachcomb, pull a shore/tideline/rockpool-cued `retrieve()` call — the EXISTING recap/recall
path this plan names, not a new one — and LOG what a "last rung + open edge" framing WOULD draw on.
Injects nothing into Du's perception, state, or narration.

DESIGN CHOICE (2026-08-24, per J-0177's briefing, option (a) of the two offered): log the raw
retrieved fragments transparently, with NO LLM synthesis. P0's own stated goal is just "is there real
place-focused material to work with" — the founder-read gate needs raw candidates to judge that, not a
synthesized line that could itself be the thing under test.

FOUNDER-READ GATE, GRADED (2026-09-27, F-2052, D-0308): the candidate pool is genuinely wide/fresh
(83.7% unique fragment_ids, near-zero consecutive-visit overlap) — the named flat-shells failure is
NOT dominant. But one archived chapter fragment ("The Ocean's Unyielding Grip") recurred verbatim in
61% of all 98 visits, and every other repeating fragment was also from the static archive layer —
caused by retrieve()'s own TIER_SLOTS guaranteeing 2 "archive" tier slots on every call ("permanent
identity, always present", store.py:347) regardless of query, so the same generic archived summary won
those 2 guaranteed slots almost every time. D-0308 (travis, ruled 2026-09-27) cleared P0 for P1 AND
ruled the fix ships as PART of P1's build, not carried forward: exclude archive-layer hits from this
module's own candidate pool (option (a) of the two D-0308 offered) — see observe_beachcomb() below.

P1 (built 2026-09-28, J-1585): `frontier_line()` below reads this module's OWN shadow log (no new
retrieve() call — P0's observe_beachcomb() already ran this cycle's live query) and hands back the
single most relevant non-archive candidate observed since a given `since` timestamp — the raw material
for "capture the open edge" (plan piece 1). core/journal.py's write_entry() (the daily recap) is the
only caller, feeding it into the SAME existing sleep-time journal LLM call as optional material,
governed by that call's own existing "invent nothing" hard rules. Still no live-perception injection —
that remains P2, deliberately ungated by this job.

OBSERVE-ONLY: never touches sensorium.py's returned narration string, `state` dict, or any store
write — read-only against memory_fragments via the existing retrieve(). Logs one row per beachcomb
hit to `data/investigation_shadow.jsonl` (append-only; tests must temp-path `_LOG`, never truncate the
live file — see feedback_test_isolation_live_stores.md). Fail-open throughout: any error is swallowed
(one debug log line), the caller's beachcomb narration is never affected.

RATE-LIMITED: the hook site (`core/sensorium.py:_shore_act()`, the beachcomb/comb/search/gather
branch) is a SYNC, INLINE call on Du's live action path — not async, not off a queue. OBSERVE_COOLDOWN
mirrors pursuits.py's own pattern so a beachcombing streak doesn't retrieve() on every single action.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.investigation_deepening_shadow")

_DATA = Path(__file__).parent.parent / "data"
_P2_LOG = _DATA / "investigation_deepening_p2_shadow.jsonl"   # P2 SHADOW (J-1968/D-0324); tests must temp-path this too
_LOG = _DATA / "investigation_shadow.jsonl"   # tests must temp-path this; never truncate the live file

OBSERVE_COOLDOWN = 90.0     # seconds between shadow observes at the shore hook (mirrors pursuits.py)
RETRIEVE_LIMIT = 6          # fragments pulled per observe (retrieve()'s own tier-mixed slot allocation)
CUE_TAIL_LIMIT = 8          # J-2592 (D-0518): cue-scored (relevance > 0) hits kept from PAST the RETRIEVE_LIMIT cap
# J-2592 (D-0518): P2 SHADOW only - widen P2's would-inject pool with the row's cue_tail. P1's
# frontier_line() (live, the journal recap) still reads `candidates` only. False = pre-J-2592 P2.
P2_USE_CUE_TAIL = True
# J-3810 (D-0711): P2 SHADOW only - narrow the pick: Du's own inner_thought is never an "open thread" handed
# back to him (nonzero relevance is already required by _scored_pool, D-0390 B). P1's frontier_line() (live)
# keeps the unnarrowed rule. Empty frozenset = pre-J-3810 P2.
P2_EXCLUDE_ORIGINS = frozenset({"inner_thought"})

# The place/activity cue itself — this is the thing that doesn't exist anywhere else in the codebase
# (07-07 finding): a query built from WHERE he is and WHAT he's doing, not from his current words.
_QUERY_TEXT = ("shore tideline rockpool beachcombing shells driftwood sea-glass mussel limpet "
               "cuttlebone the beach the tide the rocks")

_last_observe = 0.0


def observe_beachcomb(action: str = "", what: str = "", cycle_id: str = "") -> dict | None:
    """P0 SHADOW hook — call from sensorium.py's beachcomb/comb/search/gather branch, AFTER computing
    the narration to return (this never sees or touches it). Pulls a place-cued retrieve() — the
    EXISTING recap/recall path, no new retrieval logic — and logs the raw candidates: no synthesis, no
    injection, nothing returned that the caller uses. Rate-limited. Never raises."""
    global _last_observe
    try:
        now = time.time()
        if now - _last_observe < OBSERVE_COOLDOWN:
            return None
        _last_observe = now

        from core.memory.store import retrieve
        query_text = _QUERY_TEXT if not what else f"{_QUERY_TEXT} {what}"
        # NOTE (2026-08-24): store.retrieve()'s own `limit` kwarg is dead — never read inside the
        # function body (only TIER_SLOTS governs the tier-mixed slot count), so it is passed here for
        # documentation/forward-compat only. This module enforces its own cap client-side instead.
        frags = retrieve([], [], time_bias="recent", limit=RETRIEVE_LIMIT, query_text=query_text)
        if not frags:
            return None

        # ARCHIVE-RECURRENCE FIX (2026-09-28, D-0308/F-2052, J-1585): retrieve()'s own TIER_SLOTS
        # guarantees 2 "archive" tier slots on EVERY call, "no recency bias... always present"
        # (store.py:347) — for most callers that is the point (permanent identity should always be
        # reachable), but for THIS place-cued query it meant the same static chapter / standing_insight
        # / subconscious_synthesis fragment won those 2 guaranteed slots on virtually every visit
        # regardless of what Du was actually thinking about that day (F-2052: one archive chapter
        # fragment recurred verbatim in 61 of 98 visits). retrieve()'s per-tier result ordering puts
        # archive's slots first, so before this fix they always occupied 2 of the 6 slots the
        # `frags[:RETRIEVE_LIMIT]` cap below then kept. Excluding them here — before that cap — both
        # stops logging that static noise as a "candidate" and frees those slots for genuinely fresh
        # semantic/episodic material instead. D-0308 (travis, ruled 2026-09-27) chose this option (a)
        # over per-fragment de-dup (b): the recurrence is structural (the same 2 slots every call, by
        # design), not incidental, so excluding the tier that's "always present" fixes it at the actual
        # cause instead of papering over repeats one fragment_id at a time. This does NOT touch
        # store.retrieve() itself or its TIER_SLOTS — archive fragments remain fully available to every
        # OTHER caller; only this module's own place-cued candidate pool is affected.
        n_before_archive_filter = len(frags)
        frags = [f for f in frags if getattr(f, "layer", None) != "archive"]
        n_after_archive_filter = len(frags)
        # OBSERVABILITY (2026-10-02, J-1648/F-2220): confirm the D-0308 archive-exclusion fix actually
        # fires on a real live call, directly from nascence.log, without needing a fresh
        # investigation_shadow.jsonl dump replayed by hand — see docs/plans/investigation_deepening.md.
        logger.info("[investigation-deepening-shadow] excluded %d archive-layer candidate(s) of %d retrieved",
                    n_before_archive_filter - len(frags), n_before_archive_filter)
        if not frags:
            _p2_shadow_log(None, action, what, cycle_id, now, n_before_archive_filter - n_after_archive_filter)
            return None
        # J-2592 (D-0518, F-3265): the cue-scored hits that fall PAST the cap below. retrieve() inserts its
        # 5-latest-episodic recency guarantee (score 0.0) at position 1, so after the archive filter the
        # [:RETRIEVE_LIMIT] cap kept 5 zero-score fillers + 1 semantic and cut off every cue-scored episodic
        # hit (116/116 P0 rows read 2026-10-30: S+ E0 E0 E0 E0 E0 or E0 x5 + S+). Logged as an ADDITIVE key;
        # `candidates` (P0's metric pool, P1's frontier_line pool) is byte-for-byte unchanged.
        tail = [f for f in frags[RETRIEVE_LIMIT:] if float(getattr(f, "relevance", 0.0) or 0.0) > 0.0]
        tail = tail[:CUE_TAIL_LIMIT]
        frags = frags[:RETRIEVE_LIMIT]

        def _cand(f) -> dict:
            return {"fragment_id": f.fragment_id, "content": (f.content or "")[:300],
                    "origin": f.origin, "layer": f.layer, "timestamp": f.timestamp,
                    "relevance": round(f.relevance, 4)}

        row = {
            "ts": round(now, 1), "cycle_id": cycle_id, "action": action, "what": (what or "")[:60],
            "query_text": query_text,
            "n_retrieved": len(frags),
            "candidates": [_cand(f) for f in frags],
            "cue_tail": [_cand(f) for f in tail],
        }
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        logger.info("[investigation-deepening-shadow] logged %d shore-cued candidates", len(frags))
        _p2_shadow_log(row, action, what, cycle_id, now, n_before_archive_filter - n_after_archive_filter)
        return row
    except Exception as exc:
        logger.warning("[investigation-deepening-shadow] observe_beachcomb failed (non-fatal): %s", exc)
        return None


def status() -> dict:
    """For the pulse / founder-read gate: how much real place-focused material has accumulated, and is
    the same handful of fragments coming back every visit (the flat-shells failure) or is the pool
    genuinely wide? Read-only over the shadow log; never touches memory_fragments itself."""
    try:
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()]
        if not rows:
            return {"observed": 0}
        seen_frag_ids: set[str] = set()
        repeat_hits = 0
        for r in rows:
            for c in r.get("candidates", []):
                fid = c.get("fragment_id")
                if fid in seen_frag_ids:
                    repeat_hits += 1
                seen_frag_ids.add(fid)
        return {
            "observed": len(rows),
            "unique_fragments_seen": len(seen_frag_ids),
            "repeat_candidate_hits": repeat_hits,
            "last_ts": rows[-1]["ts"],
        }
    except Exception:
        return {"observed": 0}


def frontier_line(since: float = 0.0) -> "dict | None":
    """P1 (2026-09-28, D-0308/J-1585) — "capture the open edge" (plan piece 1): the single most
    relevant candidate this module has actually observed since `since`. Pass write_entry()'s own
    recap-window `since` so the frontier line and the day's deeds cover the identical window.

    Reads ONLY this module's own shadow log — makes no new retrieve() call of its own. P0's
    observe_beachcomb() already ran this cycle's live place-cued query on Du's live action path;
    re-querying here would cost a second store hit for no new signal, and would need lab_env.py
    isolation to test safely. Reading the log we already wrote needs none — it's a plain file read.

    Archive-layer candidates are already excluded at the source (observe_beachcomb()'s own fix,
    above), so every row written from 2026-09-28 onward never contains one — but the check below is
    repeated defensively in case an OLDER row (written before this fix shipped) is still inside the
    window, so a fresh restart doesn't briefly resurface the exact fragment this fix targets.

    Picks by (relevance, ts) descending — relevance is the retrieval scorer's own similarity-to-query
    read (mostly 0.0 with one nonzero slot per row per F-2052; ts breaks ties toward the most recent
    observation). Returns {"fragment_id", "content", "origin", "ts"} or None (nothing observed in the
    window, or every candidate in it was archive-layer). Never raises."""
    try:
        if not _LOG.exists():
            return None
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()]
        if since:
            rows = [r for r in rows if r.get("ts", 0) >= since]
        if not rows:
            return None
        best = _pick_frontier(rows)
        if best is None:
            return None
        return {"fragment_id": best["fragment_id"], "content": best["content"],
                "origin": best["origin"], "ts": best["ts"]}
    except Exception as exc:
        logger.warning("[investigation-deepening-shadow] frontier_line failed (non-fatal): %s", exc)
        return None


# J-2126 (F-2779): recurring STATIC semantic origins - world's-week summaries are not Du's own cue-hit
# material; as the only relevance>0 candidate they were picked as the "open thread" 3/3 recaps.
_STATIC_SEMANTIC_ORIGINS = frozenset({"journal_week"})


def _scored_pool(cands: list) -> list:
    """D-0390 B (J-2006): the candidate pool the open-edge pick may choose from. Drops archive-layer
    candidates (D-0308) AND zero-score candidates (relevance == 0.0). retrieve()'s "recency guarantee"
    (core/memory/store.py ~1167-1210) inserts Du's 5 latest episodic fragments with a hard-coded score
    of 0.0 - they are NOT place-cued hits (F-2578: 520/520 episodic candidates scored exactly 0.0), so
    treating them as an "open thread" made the pick an arbitrary latest thought. Only genuinely
    cue-scored candidates remain. Pure."""
    out = []
    for c in cands or []:
        if c.get("layer") == "archive":
            continue   # D-0308 (defensive; older rows may still carry one)
        if float(c.get("relevance", 0.0) or 0.0) <= 0.0:
            continue   # D-0390 B: recency-guarantee filler, not a cue match
        if c.get("origin") in _STATIC_SEMANTIC_ORIGINS:
            continue   # J-2126: static recurring semantic fragment, not an open thread of Du's own
        out.append(c)
    return out


def _pick_frontier(rows: list, exclude_origins: frozenset = frozenset()) -> "dict | None":
    """The ONE open-edge selection rule, shared by P1's frontier_line() and the P2 shadow (J-1968), so
    P2 cannot drift from P1. D-0390 B (J-2006): over the _scored_pool() candidates only (non-archive,
    relevance > 0), prefer EPISODIC (Du's own material) over semantic, then max (relevance, row ts).
    Returns the winning candidate's fields plus its row "ts", or None - an honest "no open thread"
    when nothing in the window was genuinely cue-scored. Pure."""
    best: "dict | None" = None
    best_key = (-1, -1.0, -1.0)
    for r in rows:
        ts = r.get("ts", 0)
        for c in _scored_pool(r.get("candidates", [])):
            if c.get("origin") in exclude_origins:
                continue   # J-3810 (D-0711): P2-only narrowing
            rel = float(c.get("relevance", 0.0) or 0.0)
            key = (1 if c.get("layer") == "episodic" else 0, rel, float(ts))
            if key > best_key:
                best_key = key
                best = {"fragment_id": c.get("fragment_id"), "content": c.get("content", ""),
                        "origin": c.get("origin", ""), "layer": c.get("layer", ""),
                        "relevance": rel, "timestamp": c.get("timestamp"), "ts": ts}
    return best


# P2 would-inject text: template v0, deterministic, NO LLM. Shadow only - this string is logged and
# never reaches any prompt or narration.
_P2_TEMPLATE = "An open thread you have not finished with: {content}"


def _p2_pool_row(row: "dict | None") -> "dict | None":
    """J-2592 (D-0518): P2's view of one P0 row - `candidates` plus `cue_tail` (deduped by fragment_id)
    when P2_USE_CUE_TAIL, else the row unchanged. Pure."""
    if not row or not P2_USE_CUE_TAIL or not row.get("cue_tail"):
        return row
    seen = {c.get("fragment_id") for c in row.get("candidates", [])}
    extra = [c for c in row.get("cue_tail", []) if c.get("fragment_id") not in seen]
    return {**row, "candidates": list(row.get("candidates", [])) + extra}


def p2_row_from_shadow_row(row: "dict | None", place: str = "shore", cycle_id: str = "",
                           ts: float = 0.0, archive_excluded_n: int = 0) -> dict:
    """Pure: the P2 shadow row for one beachcomb moment, from that moment's P0 shadow row (None when
    nothing non-archive was retrieved). Shared by the live hook and by replays.
    J-2592 (D-0518): the SAME _pick_frontier/_scored_pool rule (archive, zero-score and J-2126 static
    origins all still dropped) over a pool widened by the row's cue_tail when P2_USE_CUE_TAIL; rows
    written before J-2592 carry no cue_tail and replay exactly as before."""
    p2row = _p2_pool_row(row)
    best = _pick_frontier([p2row], exclude_origins=P2_EXCLUDE_ORIGINS) if p2row else None
    return {
        "ts": round(ts or (row or {}).get("ts", 0.0), 1), "cycle_id": cycle_id, "place": place,
        "would_inject_text": _P2_TEMPLATE.format(content=best["content"]) if best else "",
        "source_fragment_ids": [c.get("fragment_id") for c in _scored_pool((p2row or {}).get("candidates", []))
                                 if c.get("origin") not in P2_EXCLUDE_ORIGINS],
        "cue_tail_n": len((row or {}).get("cue_tail", []) or []) if P2_USE_CUE_TAIL else 0,
        "frontier_edge": ({k: best[k] for k in ("fragment_id", "origin", "layer", "relevance", "timestamp")}
                          if best else None),
        "archive_excluded_n": archive_excluded_n,
    }


def _p2_shadow_log(row: "dict | None", action: str, what: str, cycle_id: str, now: float,
                   archive_excluded_n: int) -> None:
    """P2 SHADOW (J-1968, D-0324): append what P2 WOULD inject at this beachcomb moment to
    data/investigation_deepening_p2_shadow.jsonl. Returns nothing; the caller's narration, state and
    prompts are untouched. Runs only on a moment observe_beachcomb() actually observed (past its
    cooldown). Fail-open, with a WARNING (visible at the live INFO level)."""
    try:
        out = p2_row_from_shadow_row(row, place="shore", cycle_id=cycle_id, ts=now,
                                     archive_excluded_n=archive_excluded_n)
        out["action"] = action
        _P2_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_P2_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(out, ensure_ascii=False) + "\n")
        edge = out["frontier_edge"]
        logger.info("[investigation-deepening-p2-shadow] would-inject %s (archive_excluded_n=%d)",
                    ("text from " + str(edge["fragment_id"])) if edge else "NOTHING", archive_excluded_n)
    except Exception as exc:
        logger.warning("[investigation-deepening-p2-shadow] p2 shadow log failed (non-fatal): %s", exc)
