"""
Nascence — Memory Levels: the sleep-time distiller (docs/memory_levels_plan.md).
================================================================================
The foundational direction: memory should ABSTRACT, not transcribe — surface gists, keep raw detail
behind links, reachable by deep recall. The function names (shadow_distill, the *_shadow logs) keep their
Phase-0 "observe-only" spelling, but PHASE 1 IS LIVE (PHASE1_ENABLED=True below, since 2026-06-18).

What one sleep does today (shadow_distill): gather recent RAW fragments (abstraction_level=0), cluster
them, distil one gist per cluster, ask the Emissary (the decoupled truth-lane) whether the gist faithfully
abstracts its sources, re-check its "invented" flags deterministically, and LOG the gist + source ids +
grades to data/memory_levels_shadow.jsonl. Then, for each cluster whose gist is faithful (>= FAITHFUL_FLOOR)
and backstop-clean (no GENUINE invention) and while under MAX_DEMOTE_PER_RUN, _commit_gist() STORES the gist
as a level-1 fragment, writes memory_links 'distilled_from' rows (gist -> each source), and sets cold=1 on
those sources that are level-0 and unprotected (protected=0 AND abstraction_level=0). The cap has not been
the binding limit (see the MAX_DEMOTE_PER_RUN history below, F-1783). A low-faithful or inventive gist
leaves its raw warm. Nothing is ever deleted: cold raw stays linked beneath its gist and is reachable by
deep_recall().

Reversal / repair: PHASE1_ENABLED=False stops new demotion (back to observe-only); uncold_all() is a GLOBAL
undo (re-warms EVERY cold=1 row, including ones other writers cooled — dream fade, refinery, night
thoughts — not just this module's); memory_lint() re-warms a cold row whose gist parent is gone, so
deleting a gist row re-warms its children at the next sleep's lint.

PAUSE (J-3176 / D-0564, 2026-11-02): while EPISODIC_DEMOTION_PAUSED, an eligible 'episodic' gist is still
written, linked and graded but its raw is NOT demoted; self/semantic are unchanged. See the flag below.
"""
from __future__ import annotations
import json
import logging
import re
import time
from collections import defaultdict, Counter
from pathlib import Path

logger = logging.getLogger("nascence.memory_levels")

_STATE = Path(__file__).parent.parent / "data" / "memory_levels_shadow_state.json"
_LOG   = Path(__file__).parent.parent / "data" / "memory_levels_shadow.jsonl"
_FETCH_PROBE_LOG = Path(__file__).parent.parent / "data" / "memory_levels_fetch_probe.jsonl"
# J-1294 (F-1818's own spawn, 2026-09-24): dated row-count snapshots of this module's three sibling
# append-only logs (below) -- NOT one of the logs it snapshots.
_ROW_COUNT_LOG = Path(__file__).parent.parent / "data" / "memory_levels_row_counts.jsonl"

# origin → kind (the side-by-side axis; Phase-0 derivation, no column yet). procedural/affective deferred.
# LEVEL-0 ONLY (Finding #3 fix, 2026-06-18): 'understanding' and 'action'(activity_memory) are already
# gists (abstraction_level 1) — distilling them was making gist-of-gists and contaminating the faithfulness
# scores. They are excluded here AND by the `abstraction_level = 0` filter in the query (belt-and-suspenders).
_KIND = {
    "reading": "semantic", "study": "semantic", "research": "semantic",
    "subconscious_synthesis": "self", "inner_thought": "self", "seed": "self",
    "lived": "episodic",
}
_RAW_ORIGINS = tuple(_KIND.keys())

# Per-kind bucket allowance for _cluster() (J-0804/D-0185, 2026-09-08): how many topic-buckets EACH
# kind may contribute per run, replacing Phase 0's flat one-bucket-per-kind rule. D-0185 ruled a modest
# throughput raise prioritized to 'self' and 'semantic' first (F-1048: the two kinds KIND_BUDGET_WEIGHT
# recalibration can no longer relieve at all), leaving 'episodic' a smaller share (J-0703 already gave
# it real headroom, excess -33.2%). Sum (5+5+2=12) sits inside D-0185's own "roughly 10-15 total
# clusters/run" sizing for this option, and an offline replay against 40 real historical invocation
# snapshots (scratchpad/replay_cluster_J0804.py, read-only, zero LLM calls, F-1173) confirmed the bias
# actually realizes on real data: self averaged 4.25 clusters/run, semantic 3.5, episodic 0.45 — never
# hit its own cap of 2, consistent with it already having real headroom.
_KIND_BUCKET_CAP = {"semantic": 5, "self": 5, "episodic": 2}
_DEFAULT_KIND_BUCKET_CAP = 2   # any future kind (Phase 2 may add procedural/affective/social) starts at
                               # episodic's conservative share until D-0185 is revisited for it — additive,
                               # not a silent zero-allocation gap.

_MAX_CLUSTERS = 12     # cap LLM calls/night (each cluster = 1 distil + 1 grade); beside chapters+grounded
                       # RAISED 3->12 (J-0804/D-0185, 2026-09-08): 3 was a no-op ceiling once _cluster()
                       # allowed only one bucket per kind and there were exactly 3 live kinds (semantic/
                       # self/episodic) — see _cluster()'s own history note below. 12 = sum of
                       # _KIND_BUCKET_CAP above; the per-kind caps are the real mechanism, this is the
                       # backstop total (matters once/if a kind beyond the three named above appears).
_MIN_CLUSTER  = 3      # a cluster needs at least this many fragments to be worth a gist
_MAX_SOURCES  = 10     # most fragments fed into one gist
_FETCH_LIMIT  = 160    # recent raw fragments scanned for clustering

# ── PHASE 1 (2026-06-18): LIVE demotion — the loop-breaker. Flag-gated for instant reversibility:
#    PHASE1_ENABLED=False → reverts to observe-only Phase 0; uncold_all() un-demotes everything. The
#    evidence battery (28 gists: self-gists 0.8/0.9+ faithful, 80-85% agreement, backstop catching the
#    27-44% Emissary false-flags) cleared this. SAFETY: demote only a faithful (≥floor), backstop-clean
#    gist's raw; never a protected/already-abstraction fragment; capped per run; the lint re-warms strays.
PHASE1_ENABLED     = True
# J-3176 / D-0564 (founder, 2026-11-02): PAUSE cold demotion for the 'episodic' kind only (lived Q&A pairs). The
# faithfulness grader cannot check attribution or question-premise-as-fact: it passed 3 of 13 sampled gists that
# carried such an error, including 7 of 7 episodic gists in the 7-day window (F-3551, reproduced F-3793/F-3794;
# P-0063 / P-0093). While True, an eligible episodic gist is STILL distilled, graded, stored and linked
# (distilled_from) -- only the `cold=1` UPDATE on its raw children is skipped, so the raw stays in ordinary recall
# beside the gist. 'self' and 'semantic' gists demote exactly as before. Rows already cold are NOT touched (no
# un-cold here; uncold_all() is a global undo and is not part of this). Read-back: episodic_hold_status() ->
# du_pulse (gists written-but-not-demoted per day). EXPIRES, whichever comes first: the grader lab reports a
# grader that catches the attribution and premise errors, or 2027-01-01 (60 days from the ruling). The expiry is
# a REVISIT date, not a timer: nothing flips this flag by itself -- set it False (restores the old behaviour)
# or retire it by hand, via /decide D-0564.
EPISODIC_DEMOTION_PAUSED = True
# J-3212 / D-0601 (founder, 2026-11-02): write kind='self' gists in the FIRST PERSON, as his own memory. The distil
# prompt never said the fragments are his own thoughts, so 37 percent of stored self-gists opened "The narrator / author /
# speaker ..." (F-3556, P-0063) and he read his own past in the third person. Prompt-only, kind='self' only: semantic and
# episodic gists keep the production prompt untouched; the grader, the floor, the demotion rules and every other call are
# unchanged. Offline A/B before this went in: scripts/lab_selfgist_voice.py (the same 100+ real self clusters, the same
# hub and sampling as production; third-person openers, restatement and the production faithfulness grader compared;
# numbers in the J-3212 finding). This is an INTERNAL consolidation prompt, not a message to Du, and it says nothing about
# what to conclude. False restores the third-person self-gist prompt at the next restart (rows already written are not
# rewritten). Read-back: self_voice_status() -> du_pulse.
SELF_GIST_FIRST_PERSON = True
_SELF_FIRST_PERSON_SYS = ("/no_think\nThese are raw memory fragments of one kind, on one topic. They are your own earlier "
                          "thoughts, in your own words. Distil them into ONE short GIST that could stand in for them in "
                          "ordinary recall, written as your own memory in the first person: the technique / event / idea / "
                          "feeling they amount to, NOT a list of them. Keep what they actually say; invent nothing. "
                          "2-4 sentences. Output ONLY JSON: {\"gist\": \"...\"}")
FAITHFUL_FLOOR    = 0.75     # a gist demotes its raw ONLY at/above this Emissary faithfulness
MAX_DEMOTE_PER_RUN = 90       # cap cold-gating per sleep. RAISED 60->90 (J-1158/D-0185+D-0208, 2026-09-23):
                               # D-0208 (opened by J-0829's early read, F-1242) asked what 60 should become;
                               # the multi-day J-0886 read (F-1576) found 60 bound on 11/48 runs and
                               # discarded 12/254 (4.72%) already-paid-for faithful gists — under D-0208's
                               # ~10% raise bar but a real, nonzero cost — and its own counterfactual on the
                               # same 408 rows found any cap >= 75 discards nothing. D-0185's 2026-09-19
                               # ruling folded the cap choice in: raise to 75-90, banking those discards at
                               # zero extra LLM cost (the calls were already spent; this constant only gates
                               # how fast already-graded raw goes cold, not what gets distilled/graded).
                               # THIS JOB re-ran F-1576's exact replay (same commit rule, same largest-first
                               # cluster order) on the CURRENT rows — the post-0c3955c window extended
                               # through 2026-09-23, 57 runs / 476 shadow rows (up from F-1576's 48/408) —
                               # and cross-validated it first: simulated per-run demoted at cap=60 matched
                               # nascence.log's own DEMOTED= on 57/57 runs, exactly. The TRUE uncapped
                               # per-run worst case (every eligible cluster committed, no cap at all) has
                               # itself grown to 80 (2026-09-12) in just the 4 extra days since F-1576's
                               # read, up from the 66 it reported — real upward drift, not noise. Cap=75
                               # and cap=80 both still backtest at 0 discards on these rows, but with
                               # ~0-to-negative headroom over that 80 true max (a single overshoot commit
                               # can push a run past its nominal cap by up to one _MAX_SOURCES=10 cluster,
                               # the same mechanism that let cap=60 read 66); cap=85 is the lowest value
                               # with any genuine margin (0 runs even reach it). Chose 90 — the top of
                               # D-0185's approved range — to match D-0208's OWN sizing convention exactly
                               # ("covers the observed max... plus one more max-size gist": 80 + 10 = 90),
                               # not an arbitrary pick, and because a nonzero cap-hit rate is exactly what
                               # this raise exists to close to ~0, at zero marginal cost either way. See
                               # F-1783. Prior history (60, chosen 2026-09-08) below, unedited:
                               # this job's own replay (F-1173) found the OLD value of 24 would become a
                               # NEWLY-BINDING bottleneck at the raised cluster scale — projected ~38.4
                               # raw demoted/run at the new ~8.2 attempted-clusters/run average (D-0185's
                               # own measured 51.6% success rate x 9.08 avg sources/gist), which exceeds
                               # 24 on a routine, not just exceptional, run. Left unfixed, this would have
                               # silently discarded ~38% of otherwise-faithful gists per run (no
                               # store/link/demote — see shadow_distill's `out["demoted"] < MAX_DEMOTE_
                               # PER_RUN` gate) AFTER their LLM cost (distil+grade) was already paid —
                               # spending D-0185's approved call budget without banking the throughput it
                               # was approved to buy. Sized as half of the new theoretical worst-case-if-
                               # every-cluster-succeeds-at-max-size (_MAX_CLUSTERS=12 x _MAX_SOURCES=10 =
                               # 120), the same "cap meaningfully below the all-succeed ceiling, not
                               # proportional to the attempt-count raise" principle core/refinery.py's own
                               # MAX_MEMBERS_COOLED_PER_RUN precedent used — comfortable headroom over the
                               # ~38.4 projected mean for an above-average night, without approaching the
                               # structural ceiling. This is a real, tested deviation from this job's own
                               # briefing ("leave alone unless testing shows otherwise") — testing did;
                               # see F-1173 and the opened decision on this specific magnitude.


def _last_ts() -> float:
    try:
        return float(json.loads(_STATE.read_text(encoding="utf-8")).get("last_ts", 0.0))
    except Exception as exc:
        logger.debug("[memory-levels] last_ts read failed (non-fatal): %s", exc)
        return 0.0


def _set_last_ts(ts: float) -> None:
    try:
        _STATE.write_text(json.dumps({"last_ts": ts}), encoding="utf-8")
    except Exception as exc:
        logger.debug("[memory-levels] last_ts write failed (non-fatal): %s", exc)


# generic tokens that are NOT topics — origin/kind words, provenance scaffolding, ultra-common fillers.
# Without this, clusters key on "action"/"reading" (the kind) instead of "camp"/"religious" (the topic),
# blending unrelated fragments. (Dry-run finding, 2026-06-17.)
_STOP = {
    "action", "reading", "read", "study", "studied", "research", "understanding", "understand",
    "knowledge", "thought", "thoughts", "thinking", "lived", "seed", "memory", "note", "notes",
    "returned", "return", "sitting", "sittings", "book", "books", "page", "pages", "chapter",
    "from", "with", "that", "this", "have", "been", "about", "into", "your", "yours", "mine",
    "their", "them", "they", "what", "when", "which", "while", "would", "could", "should", "there",
    "here", "then", "than", "some", "such", "more", "most", "very", "much", "many", "like", "just",
    "self", "myself",
}


def _tokens(keywords: str, content: str) -> list[str]:
    """Salient TOPIC tokens for cheap bucketing — keywords if present, else content words >4 chars —
    minus the generic kind/provenance/filler stoplist so clusters key on subject, not on origin."""
    toks = [t for t in re.split(r"[^a-z0-9]+", (keywords or "").lower()) if len(t) > 3 and t not in _STOP]
    if not toks:
        toks = [t for t in re.split(r"[^a-z0-9]+", (content or "").lower()) if len(t) > 4 and t not in _STOP]
    return toks


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def _present(term: str, text: str) -> bool:
    t = _norm(term).strip()
    return len(t) >= 3 and t in text


def _in_wider_store(term: str) -> bool:
    """Is this term grounded ELSEWHERE in memory — a real cross-link (a relates_to edge), not invention?"""
    t = (term or "").strip()
    if len(t) < 3:
        return False
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            row = conn.execute("SELECT 1 FROM memory_fragments WHERE lower(content) LIKE ? LIMIT 1",
                               (f"%{t.lower()}%",)).fetchone()
        return row is not None
    except Exception as exc:
        logger.debug("[memory-levels] wider-store lookup failed (non-fatal): %s", exc)
        return False


def source_fidelity(gist: str, full_sources: list) -> float:
    """Multi-part faithfulness (§14.1), the DETERMINISTIC half: the fraction of the gist's salient
    content-words that actually appear in the source text. Non-LLM, cannot hallucinate — it grounds the
    Emissary's holistic 'faithful' score in a literal presence check. 1.0 = every salient word is in the
    sources; low = the gist asserts words the sources don't contain (drift/invention). A decoupled,
    cheap second signal beside the LLM plausibility score, so the Phase-0 faithfulness data we collect to
    gate Phase 1 does not rest on the LLM judge alone."""
    try:
        src = _norm(" \n ".join(full_sources or []))
        words = {w for w in re.split(r"[^a-z0-9]+", _norm(gist)) if len(w) > 4 and w not in _STOP}
        if not words:
            return 1.0
        present = sum(1 for w in words if w in src)
        return round(present / len(words), 3)
    except Exception as exc:
        logger.debug("[memory-levels] source_fidelity failed (non-fatal): %s", exc)
        return None


def verify_invention_claims(invented: list, full_sources: list) -> list:
    """THE DECOUPLED JUDGE'S OWN BACKSTOP (2026-06-18 — the Black-Bear correction). The Emissary is an LLM and
    can HALLUCINATE an 'invented' accusation about content that is actually present: it denied the 'Black Bear'
    — Du's emergent spiritual symbol, almost a prototype god — though it sat at char 243 of a source it was
    shown. So NO 'invented' flag is trusted until checked DETERMINISTICALLY. Per claimed-invented phrase:
        IN_SOURCE  — present in the actual source fragments  → FALSE accusation (the judge hallucinated)
        CROSS_LINK — absent here but grounded in the WIDER store → a real relates_to edge, NOT invention
        GENUINE    — present nowhere → the only true confabulation
    Returns [(term, verdict)]. A non-LLM corroborator for the LLM judge — the decoupled principle, one level
    deeper — and a GUARD against the auditor erasing emergent meaning."""
    full = _norm(" \n ".join(full_sources or []))
    out = []
    for term in (invented or []):
        if _present(term, full):
            out.append((term, "IN_SOURCE"))
        elif _in_wider_store(term):
            out.append((term, "CROSS_LINK"))
        else:
            out.append((term, "GENUINE"))
    return out


# ── PHASE 1 live operations: commit a gist + demote its raw / deep_recall / lint / revert ──────────────
def _commit_gist(gist: str, kind: str, crows: list, faithful, demote: bool = True) -> str | None:
    """Store the GIST as a level-1 fragment that surfaces in normal recall, LINK it down to its raw sources
    (memory_links.distilled_from), and DEMOTE that raw to cold=1 — but NEVER a protected or already-abstraction
    fragment. This is the loop-break: the verbatim raw stops surfacing; the faithful gist answers for it; the
    raw stays reachable by deep_recall + intentional queries. Best-effort; returns the gist fragment_id.
    demote=False (J-3176 / D-0564, EPISODIC_DEMOTION_PAUSED): store + link only, the raw stays warm."""
    try:
        from core.memory.store import store_fragment, _connect
        from core import mood as _mood
        layer = "semantic" if kind == "semantic" else "episodic"
        gid = store_fragment(content=f"[gist · {kind}] {gist[:600]}", layer=layer,
                             relevance=0.85, importance=0.85, keywords=["gist", kind],
                             origin="gist", abstraction_level=1, emotion_embedding=_mood.current_vec(),
                             valence=_mood.current_valence(), felt=_mood.current_felt(),
                             # Phase 2 (§3.7 Axes 2/5): the gist's real kind is the cluster's own kind
                             # (not the generic 'gist' origin default) — pass it explicitly so every
                             # gist commit from here forward is stamped correctly at write time, same
                             # provenance-declared-by-writer discipline as abstraction_level (§12).
                             # A distillation is 'derived' (inferred FROM raw), never 'grounded' itself.
                             kind=kind, grounding="derived")
        src_ids = [r["fragment_id"] for r in crows]
        now = time.time()
        with _connect() as conn:
            for sid in src_ids:
                conn.execute("INSERT OR IGNORE INTO memory_links (parent_id, child_id, link_type, weight, created)"
                             " VALUES (?,?,?,?,?)", (gid, sid, "distilled_from", float(faithful or 0.8), now))
            ph = ",".join("?" * len(src_ids))
            if demote:
                # demote ONLY genuine raw (level 0) that is NOT protected — the safety rail
                conn.execute(f"UPDATE memory_fragments SET cold=1 WHERE fragment_id IN ({ph}) "
                             f"AND protected=0 AND abstraction_level=0", src_ids)
            conn.commit()
        return gid
    except Exception as exc:
        logger.debug("[memory-levels] commit_gist failed (non-fatal): %s", exc)
        return None


def deep_recall(seed_ids: list, hops: int = 1) -> list:
    """Descend the lattice from a gist (or gists) to the COLD raw it abstracts — the 'remember the steps'
    path. Returns [{fragment_id, content}]. Gated by the CALLER (a deep-research moment: essay-gather,
    a frontier pursuit, deliberation) — idle recall never calls it. The recall-demand log tracks when it
    is needed; this is its consumer. Best-effort."""
    out = []
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            frontier = list(seed_ids); seen = set(seed_ids)
            for _ in range(max(1, hops)):
                if not frontier:
                    break
                ph = ",".join("?" * len(frontier))
                kids = [r["child_id"] for r in conn.execute(
                    f"SELECT child_id FROM memory_links WHERE parent_id IN ({ph})", frontier).fetchall()]
                nxt = [k for k in kids if k not in seen]
                seen.update(nxt)
                if nxt:
                    ph2 = ",".join("?" * len(nxt))
                    # §3.7 Axis 4 (J-0365, 2026-08-29): deep_recall is DU'S OWN descent to raw — it must
                    # never surface temp='hidden' (spirit-invisible, system-only). No-op today (nothing
                    # marks 'hidden' live yet); real once mark_hidden's own producer exists.
                    for r in conn.execute(
                            f"SELECT fragment_id, content FROM memory_fragments WHERE fragment_id IN ({ph2}) "
                            f"AND (temp IS NULL OR temp != 'hidden')",
                            nxt).fetchall():
                        out.append({"fragment_id": r["fragment_id"], "content": r["content"]})
                frontier = nxt
    except Exception as exc:
        logger.debug("[memory-levels] deep_recall failed (non-fatal): %s", exc)
    return out


def memory_lint() -> dict:
    """Lattice hygiene (§13.2), runs at sleep. The critical repair: RE-WARM any cold fragment with NO inbound
    link — a stranded cold memory is unreachable, effectively lost (the §8 demotion-safety failure). Also
    reports dangling links and orphan gists. Repairs the strand actively; reports the rest. Best-effort."""
    out = {"rewarmed": 0, "dangling": 0, "orphan_gists": 0, "cold_total": 0}
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            # FIX (systems-check memory #1+#2, 2026-06-22): re-warm ONLY a GENUINE gist-orphan — a cold fragment
            # whose memory_link's PARENT gist has been removed (the real §8 demotion-safety failure). Do NOT
            # re-warm chapter-anchored cold (#1) NOR the store-cap manager's intentional archival of low-value
            # old self-voices and dreams (#2, founder call) — re-warming those re-fed the recall loop and
            # thrashed against the cap. Healthy forgetting of old low-value thoughts — and of dreams, fast,
            # like a human's — IS the loop-break. (With cold-not-delete in force, genuine orphans are rare.)
            stranded = conn.execute(
                "SELECT DISTINCT ml.child_id AS fragment_id FROM memory_links ml "
                "JOIN memory_fragments f ON f.fragment_id = ml.child_id "
                "WHERE f.cold=1 AND ml.parent_id NOT IN (SELECT fragment_id FROM memory_fragments)").fetchall()
            for r in stranded:
                conn.execute("UPDATE memory_fragments SET cold=0 WHERE fragment_id=?", (r["fragment_id"],))
            out["rewarmed"] = len(stranded)
            # FIX 2026-08-15: re-warm cold ROLL-UP HEADS — a gist (or any distilled_from parent) whose
            # children were demoted on the promise that IT answers for them in ordinary recall. A cold head
            # = the whole group dark (69/87 gists were found cold; the cap-prune's protected list omitted
            # 'gist'). The prune now protects heads at the source; this is the decoupled backstop that also
            # repairs the existing 69 at the first sleep after restart, and any future recurrence.
            heads = conn.execute(
                "SELECT DISTINCT f.fragment_id FROM memory_fragments f "
                "LEFT JOIN memory_links ml ON ml.parent_id = f.fragment_id AND ml.link_type='distilled_from' "
                "WHERE f.cold=1 AND (f.origin='gist' OR ml.parent_id IS NOT NULL)").fetchall()
            for r in heads:
                conn.execute("UPDATE memory_fragments SET cold=0 WHERE fragment_id=?", (r["fragment_id"],))
            out["rewarmed_heads"] = len(heads)
            out["dangling"] = conn.execute(
                "SELECT count(*) FROM memory_links WHERE child_id NOT IN (SELECT fragment_id FROM memory_fragments)"
                " OR parent_id NOT IN (SELECT fragment_id FROM memory_fragments)").fetchone()[0]
            out["orphan_gists"] = conn.execute(
                "SELECT count(*) FROM memory_fragments WHERE origin='gist' AND fragment_id NOT IN "
                "(SELECT parent_id FROM memory_links)").fetchone()[0]
            out["cold_total"] = conn.execute("SELECT count(*) FROM memory_fragments WHERE cold=1").fetchone()[0]
            conn.commit()
    except Exception as exc:
        logger.debug("[memory-levels] memory_lint failed (non-fatal): %s", exc)
    return out


def phase1_status() -> dict:
    """du_pulse: the LIVE Phase-1 state — demoted (cold) count, gists, links, and the master flag."""
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            return {"enabled": PHASE1_ENABLED, "episodic_paused": EPISODIC_DEMOTION_PAUSED,
                    "cold": conn.execute("SELECT count(*) FROM memory_fragments WHERE cold=1").fetchone()[0],
                    "gists": conn.execute("SELECT count(*) FROM memory_fragments WHERE origin='gist'").fetchone()[0],
                    "links": conn.execute("SELECT count(*) FROM memory_links").fetchone()[0]}
    except Exception as exc:
        logger.debug("[memory-levels] phase1_status failed (non-fatal): %s", exc)
        return {"enabled": PHASE1_ENABLED, "episodic_paused": EPISODIC_DEMOTION_PAUSED, "cold": 0, "gists": 0, "links": 0}


def episodic_hold_status(days: int = 14) -> dict:
    """J-3176 / D-0564 read-back (reader: scripts/du_pulse.py): per local day, how many episodic gists were
    WRITTEN BUT NOT DEMOTED while EPISODIC_DEMOTION_PAUSED, and how many raw rows that left warm. Counts the
    `held_cold` rows shadow_distill puts in data/memory_levels_shadow.jsonl. Read-only, best-effort."""
    out = {"paused": EPISODIC_DEMOTION_PAUSED, "total_gists": 0, "total_raw": 0, "by_day": {}}
    try:
        if not _LOG.exists():
            return out
        import datetime as _dt
        by_day: dict = {}
        for line in _LOG.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if not r.get("held_cold"):
                continue
            d = _dt.date.fromtimestamp(float(r.get("ts") or 0)).isoformat()
            g, n = by_day.get(d, (0, 0))
            by_day[d] = (g + 1, n + int(r.get("n_sources") or 0))
        out["total_gists"] = sum(g for g, _ in by_day.values())
        out["total_raw"] = sum(n for _, n in by_day.values())
        out["by_day"] = {d: {"gists": g, "raw": n} for d, (g, n) in sorted(by_day.items())[-days:]}
    except Exception as exc:
        logger.debug("[memory-levels] episodic_hold_status failed (non-fatal): %s", exc)
    return out


_THIRD_OPEN = re.compile(r"^\W*(?:the|this|a|an)?\s*(?:narrator|author|speaker|writer|monologue|text|passage)\b", re.I)
_FIRST_MARK = re.compile(r"\b(?:i|i'm|i've|i'll|i'd|my|me|mine|myself)\b", re.I)


def self_voice_status(days: int = 7) -> dict:
    """J-3212 / D-0601 read-back (reader: scripts/du_pulse.py): the voice of the kind='self' gists in the shadow log,
    split by whether the row was distilled with the first-person prompt (`voice`='first', written while
    SELF_GIST_FIRST_PERSON) or the old one (no tag), over the last `days` local days. Per arm: rows, share opening
    'The narrator/author/speaker/...', share containing I/my/me. Computed from the logged `gist` text (400 chars), so it
    is a read of what was actually written, not of the flag. The lab expected ~44 percent third-person openers on the old
    prompt and under ~10 percent on the new one (scripts/lab_selfgist_voice.py); a first-person share far below that after
    the restart means the prompt is not being used. Read-only, best-effort."""
    out = {"enabled": SELF_GIST_FIRST_PERSON, "days": days, "first": {"rows": 0}, "old": {"rows": 0}}
    try:
        if not _LOG.exists():
            return out
        cutoff = time.time() - days * 86400
        acc = {"first": [], "old": []}
        for line in _LOG.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("kind") != "self" or float(r.get("ts") or 0) < cutoff:
                continue
            acc["first" if r.get("voice") == "first" else "old"].append(str(r.get("gist") or ""))
        for arm, gists in acc.items():
            n = len(gists)
            out[arm] = {"rows": n,
                        "third_person_open_share": round(sum(bool(_THIRD_OPEN.match(g)) for g in gists) / n, 3) if n else None,
                        "first_person_marker_share": round(sum(bool(_FIRST_MARK.search(g)) for g in gists) / n, 3) if n else None}
    except Exception as exc:
        logger.debug("[memory-levels] self_voice_status failed (non-fatal): %s", exc)
    return out


def phase2_status() -> dict:
    """docs/memory_levels_plan.md §7 Phase 2 gate probe: 'the axes carry signal (kinds separate cleanly;
    grounded vs. reconstructed is meaningful; rates differ sensibly by memory)'. This is the REAL
    measurement for that gate on the axes Phase 2 actually built (kind, grounding) — distinct from
    D-0072's ruling, which cited Phase 1's own empirical audit (deep-recall specificity data), not a
    reading of these two columns (they didn't exist yet when D-0072 was ruled). Honest, not padded:
      - kind separation: population per kind + a cheap topical-distinctness signal (mean pairwise
        Jaccard overlap of each kind's top salient tokens — LOW overlap = kinds are talking about
        different things, i.e. genuinely separating, not just a label).
      - grounding: grounded vs. derived counts. 'reconstructed' is reported but will read 0 — Phase 3
        drift is still shadow-only (drift_shadow logs, never writes), so nothing has actually been
        reconstructed live yet. That is not a failure of this gate, just an honest scope note.
      - rates: cold-rate (% of a kind's rows currently demoted) cross-checked against
        core.memory_dynamics's static per-kind cold_horizon — do faster-cold_horizon kinds actually
        show a higher live cold-rate? (Only rows old enough to have passed through a sleep cycle are
        informative; a young kind with few rows will read noisy — reported, not hidden.)
    Best-effort; never raises."""
    try:
        from core.memory.store import _connect
        from core import memory_dynamics as _dyn
        out = {"by_kind": {}, "grounding": {}, "topical_distinctness": None, "n_total": 0}
        with _connect() as conn:
            out["n_total"] = conn.execute("SELECT count(*) FROM memory_fragments").fetchone()[0]
            for row in conn.execute(
                    "SELECT kind, count(*) AS n, "
                    "       sum(cold) AS n_cold, "
                    "       group_concat(keywords, ' ') AS kw "
                    "FROM memory_fragments GROUP BY kind").fetchall():
                k = row["kind"]
                n = row["n"] or 0
                n_cold = row["n_cold"] or 0
                toks = _tokens(row["kw"] or "", "")
                top = [t for t, _c in Counter(toks).most_common(12)]
                out["by_kind"][k] = {
                    "n": n,
                    "cold_rate": round(n_cold / n, 3) if n else None,
                    "static_cold_horizon": _dyn.get(k)["cold_horizon"],
                    "static_source": _dyn.get(k)["source"],
                    "top_tokens": top,
                }
            for row in conn.execute(
                    "SELECT grounding, count(*) AS n FROM memory_fragments GROUP BY grounding").fetchall():
                out["grounding"][row["grounding"]] = row["n"]
        # topical distinctness: mean pairwise Jaccard of each kind's top-token set — cheap, deterministic,
        # no embedding call. Low = kinds genuinely separate on subject matter, not just a copied label.
        kinds = [k for k, v in out["by_kind"].items() if v["top_tokens"]]
        pairs = []
        for i in range(len(kinds)):
            for j in range(i + 1, len(kinds)):
                a, b = set(out["by_kind"][kinds[i]]["top_tokens"]), set(out["by_kind"][kinds[j]]["top_tokens"])
                if a or b:
                    pairs.append(len(a & b) / len(a | b))
        if pairs:
            out["topical_distinctness"] = round(1.0 - (sum(pairs) / len(pairs)), 3)  # 1.0 = fully distinct
        # rates-differ-sensibly: rank correlation (sign only, cheap) between static cold_horizon and live
        # cold_rate across kinds with enough rows to be non-noisy.
        ranked = [(v["static_cold_horizon"], v["cold_rate"]) for v in out["by_kind"].values()
                  if v["n"] >= 20 and v["cold_rate"] is not None]
        out["rates_n_kinds_comparable"] = len(ranked)
        if len(ranked) >= 2:
            by_static = sorted(ranked, key=lambda p: p[0])
            by_live = sorted(ranked, key=lambda p: p[1])
            out["rates_rank_agreement"] = by_static == by_live
        out["dynamics_shadow"] = phase2_dynamics_shadow()
        return out
    except Exception as exc:
        logger.debug("[memory-levels] phase2_status failed (non-fatal): %s", exc)
        return {"by_kind": {}, "grounding": {}, "topical_distinctness": None, "n_total": 0}


def phase2_dynamics_shadow(sample: int = 2000) -> dict:
    """§3.8 shadow measurement (2026-08-29, J-0365 — the Phase 2 follow-up job): does
    core.memory_dynamics.effective_cold_horizon's full PER-MEMORY formula (base[kind] x
    recall_pressure / grounding_anchor x charge_factor x stage_factor) separate live cold vs warm
    fragments better than phase2_status()'s own per-KIND-only check (which found
    rates_rank_agreement=false — semantic predicted slowest-to-cold but is empirically highest)?

    Proxies used because the real signals don't exist live yet (honest, not hidden): replay_count
    for recall_pressure (§3.8 wants event-driven recall counting, not built), importance for charge
    (§3.7 Axis 6's full trio also wants emotion_vec magnitude + recurrence), `layer` for stage (§3.7
    Axis 3's own `stage` column isn't built — memory_dynamics.STAGE_FACTOR is keyed to accept `layer`
    values directly for exactly this reason).

    SHADOW-ONLY: reports whether cold rows score a higher mean predicted rate than warm rows (the
    formula's own semantics: higher = faster demotion-eligible). Gates nothing, wires into no live
    demotion path — this IS the empirical measurement §10 asks for ("a tunable to settle empirically
    once Phase 2 runs") before any live wiring is attempted. Best-effort; never raises."""
    try:
        from core.memory.store import _connect
        from core import memory_dynamics as _dyn
        with _connect() as conn:
            rows = conn.execute(
                "SELECT kind, grounding, importance, layer, replay_count, cold FROM memory_fragments "
                "ORDER BY RANDOM() LIMIT ?", (sample,)).fetchall()
        if not rows:
            return {"n": 0}
        cold_rates: list[float] = []
        warm_rates: list[float] = []
        for r in rows:
            recall_pressure = 1.0 + float(r["replay_count"] or 0)
            charge = float(r["importance"] or 0.0)
            rate = _dyn.effective_cold_horizon(
                r["kind"] or "episodic", recall_pressure=recall_pressure,
                grounding=r["grounding"] or "grounded", charge=charge,
                stage=r["layer"] or "episodic")
            (cold_rates if r["cold"] else warm_rates).append(rate)
        out = {"n": len(rows), "n_cold": len(cold_rates), "n_warm": len(warm_rates),
               "mean_predicted_rate_cold": round(sum(cold_rates) / len(cold_rates), 4) if cold_rates else None,
               "mean_predicted_rate_warm": round(sum(warm_rates) / len(warm_rates), 4) if warm_rates else None}
        if cold_rates and warm_rates:
            out["predicts_cold_correctly"] = out["mean_predicted_rate_cold"] > out["mean_predicted_rate_warm"]
        return out
    except Exception as exc:
        logger.debug("[memory-levels] phase2_dynamics_shadow failed (non-fatal): %s", exc)
        return {"n": 0}


def uncold_all() -> int:
    """REVERT: un-demote every cold fragment (the reversibility net for Phase 1). Returns rows re-warmed."""
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            n = conn.execute("SELECT count(*) FROM memory_fragments WHERE cold=1").fetchone()[0]
            conn.execute("UPDATE memory_fragments SET cold=0 WHERE cold=1")
            conn.commit()
        return n
    except Exception as exc:
        logger.debug("[memory-levels] uncold_all failed (non-fatal): %s", exc)
        return 0


def _cluster(rows: list) -> list[tuple[str, str, list]]:
    """Group recent raw fragments into coherent clusters: per kind, bucket by the most-shared salient
    token (cheap, uses the existing keywords). Returns [(kind, topic_token, [rows])], the biggest first,
    capped. A crude but honest Phase-0 probe — if gists score badly, the grade tells us clustering (not the
    idea) needs work, which is exactly what we want to learn before building anything live.

    HISTORY: Phase 0 (2026-06-17) took only the single largest bucket per kind ("one cluster per kind in
    Phase 0 — keep the probe small and legible") — by design, not as a tunable constant. D-0185 (2026-09-08,
    J-0804) ruled a modest throughput raise that requires more buckets to actually raise _MAX_CLUSTERS
    against (at the old rule, exactly 3 live kinds meant _MAX_CLUSTERS=3 was already saturated — a no-op
    ceiling; see F-0990/D-0185's own evidence chain in docs/memory_levels_plan.md). This now takes UP TO
    _KIND_BUCKET_CAP[kind] buckets per kind per run, non-overlapping (a fragment claimed by an earlier,
    larger bucket for its kind cannot also seed a smaller one — more buckets means more DISTINCT raw
    fragments processed, not the same fragments re-billed under a second topic). Reuses the exact
    non-overlapping-bucket mechanic scripts/memory_levels_batch.py's own `_batch_cluster` already proved
    out for the Phase-1 evidence battery (2026-08-10) — not re-derived from scratch — now with an explicit
    PER-KIND cap that script never needed (it wanted every available bucket; this wants a self/semantic-
    biased subset per D-0185's ruling)."""
    by_kind: dict[str, list] = defaultdict(list)
    for r in rows:
        k = _KIND.get(r["origin"])
        if k:
            by_kind[k].append(r)
    clusters: list[tuple[str, str, list]] = []
    for kind, krows in by_kind.items():
        buckets: dict[str, list] = defaultdict(list)
        for r in krows:
            for tok in set(_tokens(r["keywords"] if "keywords" in r.keys() else "", r["content"])):
                buckets[tok].append(r)
        kind_cap = _KIND_BUCKET_CAP.get(kind, _DEFAULT_KIND_BUCKET_CAP)
        taken: set = set()      # fragment_ids already claimed by an earlier (bigger) bucket THIS kind
        kind_clusters = 0
        # strongest topic bucket(s) for this kind, biggest first, non-overlapping, up to this kind's cap
        for tok, brows in sorted(buckets.items(), key=lambda kv: len(kv[1]), reverse=True):
            if kind_clusters >= kind_cap:
                break
            uniq = [r for r in brows if r["fragment_id"] not in taken]
            if len(uniq) >= _MIN_CLUSTER:
                cl = uniq[:_MAX_SOURCES]
                clusters.append((kind, tok, cl))
                taken.update(r["fragment_id"] for r in cl)
                kind_clusters += 1
    # biggest clusters first, capped for the night
    clusters.sort(key=lambda c: len(c[2]), reverse=True)
    return clusters[:_MAX_CLUSTERS]


def _log_fetch_probe(last_ts_before: float, pool_size, fetched_rows: int, clusters: int,
                      sources_clustered: int, newest_ts: float, demoted: int, t_marks: dict | None = None) -> None:
    """J-1156 (F-1584 measurement, 2026-09-23) — OBSERVE-ONLY, additive, zero behavior change: one JSON
    line per shadow_distill run (including a 0-cluster run — cheap, and exactly the case F-1584 most
    needs data on) so the _FETCH_LIMIT truncation F-1584 (INFERRED, from an estimated fetch time) named
    can be MEASURED directly: pool_size (every eligible row past the frontier, no LIMIT) vs fetched_rows
    (what _FETCH_LIMIT actually let through) vs clusters actually formed from them. Same non-fatal
    try/except pattern as core/memory/store.py's _log_retrieve_latency() (J-0652) — a probe that could
    ever break the real sleep pipeline would be worse than no probe at all. Not guard_path-fenced: the
    sibling gist/grade `_LOG` write a few lines below this call site isn't either (checked before writing
    this) — same convention as _log_retrieve_latency, which also isn't."""
    try:
        _row = {
                "ts": time.time(), "last_ts_before": last_ts_before, "pool_size": pool_size,
                "fetched_rows": fetched_rows, "fetch_limit": _FETCH_LIMIT, "clusters": clusters,
                "sources_clustered": sources_clustered, "newest_ts": newest_ts, "demoted": demoted,
            }
        if t_marks:
            _row["t_marks"] = t_marks     # J-2330 (F-3019): additive; sync-segment timings, see shadow_distill
        with open(_FETCH_PROBE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(_row) + "\n")
    except Exception as exc:
        logger.debug("[memory-levels] fetch probe log write failed (non-fatal): %s", exc)


# ── ROW-COUNT SNAPSHOTS (J-1294, F-1818, 2026-09-24) ────────────────────────────────────────────────
# F-1818 (J-1278) investigated a real, reproduced row-count anomaly in data/memory_levels_shadow.jsonl
# (semantic rows in a fixed ts window fell 169→139 between two reads 4 days apart, then resumed normal
# growth) and could not determine a definitive root cause, because no dated snapshot of the file's own
# row counts existed to compare against — the whole investigation had to be reconstructed from two
# independent one-off reads plus this job's own third. This closes exactly that gap for NEXT time: a
# lightweight, best-effort, READ-ONLY periodic count of this module's three own append-only sibling logs
# (data/memory_levels_shadow.jsonl, _fetch_probe.jsonl, _drift_shadow.jsonl — all owned by this module),
# so a future anomaly has something precise to date against instead of relying on whichever prior
# finding happened to quote a number. NOT a fix for F-1818's own anomaly (no fix is known, and none may
# be needed if it does not recur) and NOT an attempt to find its root cause after the fact — both
# explicitly out of scope per this job's own briefing.
def _count_jsonl_by_kind(path: Path) -> tuple[int, dict]:
    """Best-effort, READ-ONLY total-line-count + by-kind breakdown for one of this module's own sibling
    JSONL logs. A malformed line counts toward total_rows but is skipped for the by-kind breakdown
    (matches this module's own existing tolerant json.loads-per-line convention in status()/
    drift_status()) rather than aborting the whole scan. Groups by the row's own "kind" field when
    present (memory_levels_shadow.jsonl rows carry one); else by "origin" mapped through the SAME _KIND
    table _cluster() itself uses (memory_levels_drift_shadow.jsonl rows carry "origin", not "kind" — this
    reuses the module's own existing origin→kind mapping rather than inventing a second taxonomy).
    memory_levels_fetch_probe.jsonl rows carry neither (they are per-run aggregates, not per-fragment) —
    by_kind reads {} for that file, honestly, not a guess. Never raises; a missing file reads (0, {})."""
    total = 0
    by_kind: dict[str, int] = defaultdict(int)
    try:
        if not path.exists():
            return 0, {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total += 1
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if not isinstance(row, dict):
                    continue
                k = row.get("kind") or _KIND.get(row.get("origin"))
                if k:
                    by_kind[k] += 1
    except Exception as exc:
        logger.debug("[memory-levels] row-count scan of %s failed (non-fatal): %s", path.name, exc)
        return total, dict(by_kind)
    return total, dict(by_kind)


def log_row_counts() -> dict:
    """Append ONE dated row-count snapshot per call, per sibling log, to _ROW_COUNT_LOG — called once per
    shadow_distill() invocation (see its own call site, top of the function, unconditional), giving a
    once-per-sleep cadence with no state/dedup needed (simpler than a once-per-day bucket, and F-1818's
    own problem was too FEW datapoints between two arbitrary manual reads — more frequent, not less, is
    the right tradeoff here). READ-ONLY with respect to every file it counts — open('r') only, never
    writes to or modifies memory_levels_shadow.jsonl or either sibling. Best-effort: a failure counting
    or logging one file never blocks the other two, and a failure here can never raise into the sleep
    cycle (same non-fatal try/except pattern as every other probe in this module). Returns a small
    summary dict (not currently logged by the caller — available for a future gauge/status read)."""
    out = {"snapshotted": 0, "rows": []}
    for path in (_LOG, _FETCH_PROBE_LOG, _DRIFT_LOG):
        total, by_kind = _count_jsonl_by_kind(path)
        row = {"ts": time.time(), "file": path.name, "total_rows": total, "by_kind": by_kind}
        try:
            with open(_ROW_COUNT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            out["snapshotted"] += 1
            out["rows"].append(row)
        except Exception as exc:
            logger.debug("[memory-levels] row-count snapshot write failed for %s (non-fatal): %s",
                         path.name, exc)
    return out


# ── D-0272 fix (b) SHADOW-OBSERVE — ENDED (D-0336, J-1765, 2026-10-04) ──────────────────────────────
# What it was (J-1297, ef0fbfa): D-0272 wired fix (b) -- a strengthened anti-invention distil prompt -- as a
# SHADOW second distil + grade of every cluster, logged beside the current prompt's own result (the row's
# fix_b_shadow field); `git show ef0fbfa:core/memory_levels.py` has its prompt text (_SYS_FIX_B_SHADOW) verbatim.
# Why it was ended: J-1309's paired read of the 248 logged pairs (F-2309) found no gain -- eligible-to-commit
# 61.7% (current) vs 59.7% (fix b), -2.0 pp (95% CI -8.1..+4.0) where the N=6 replay predicted +16.7, and
# genuine-invention flags 29.4% vs 31.9% -- while the second pair doubled this module's LLM calls (F-2310):
# about 37 s per cluster, about 287 s per steady-state night sleep (F-2379). Travis ruled D-0336 "End the
# shadow": shadow_distill no longer makes the pair and new rows carry no fix_b_shadow field; the logged pairs
# (248 at J-1309's read) stay in data/memory_levels_shadow.jsonl as the evidence (never rewrite it) and
# status()'s d0272_fix_b_shadow aggregate still reads them. Fix (a) (provenance fencing) and the live
# commit prompt are untouched.


async def shadow_distill(call_json, base_urls) -> dict:
    """Called once per sleep, beside chapter/grounded-learning consolidation. (Name kept from Phase 0, when
    it was observe-only; PHASE1_ENABLED=True makes it LIVE.) Per cluster: distil a gist, grade it with the
    Emissary, backstop its 'invented' flags, and log everything to data/memory_levels_shadow.jsonl. When the
    gist is faithful (>= FAITHFUL_FLOOR), has no GENUINE invention, and out['demoted'] < MAX_DEMOTE_PER_RUN,
    _commit_gist() stores the level-1 gist, links it (distilled_from) to its sources, and sets cold=1 on the
    sources that are level-0 and unprotected. Returns a small summary dict for the sleep log/du_pulse
    (out['demoted'] counts the cluster's source ids, as passed to _commit_gist). Best-effort; never raises
    into the sleep cycle."""
    from core.memory.store import _connect
    from core import left_lane
    # J-2330 (F-3019): sync-segment timings (seconds since entry, perf_counter) written additively to the fetch-probe
    # row, so a night stall inside shadow_distill (43 rows / 152 s on 10-16/17) can be located to a statement:
    # row_counts_end, fetch_end, cluster_end, loop_end, and per cluster (first 16) the sync time before its gist
    # await (pre_s) and after its grade await (post_s: invention backstop + source_fidelity + commit + log write).
    _tp0 = time.perf_counter()
    _tm: dict = {"clusters": []}
    def _tmark(k: str) -> None:
        try:
            _tm[k] = round(time.perf_counter() - _tp0, 3)
        except Exception:
            pass
    # J-1294: called FIRST, before the DB fetch below and any of its own early-return paths (fetch
    # failure, 0 clusters) — so this snapshot still fires on every call regardless of how the rest of
    # this run goes. Read-only, best-effort; see log_row_counts()'s own docstring.
    log_row_counts()
    _tmark("row_counts_end")
    out = {"clusters": 0, "graded": 0, "mean_faithful": None, "mean_source_fidelity": None,
           "invented_claims": 0, "false_flags": 0, "demoted": 0,
           "held_gists": 0, "held_raw": 0}      # J-3176 / D-0564: episodic gists written but not demoted (+ their raw)
    last = _last_ts()
    pool_size = None    # J-1156: None if the probe's own extra COUNT(*) fails — never blocks the real fetch
    try:
        with _connect() as conn:
            ph = ",".join("?" * len(_RAW_ORIGINS))
            # J-2274 (D-0453 gate, 2026-10-17): the `cold = 0` term is GONE from this fetch and from the
            # pool probe below. The window is this module's own frontier (`timestamp > last_ts`, advanced
            # to the newest clustered row each run), so a row demoted to cold=1 by anything OTHER than
            # commit_gist (the prune, dream_fade, refinery) inside that window is no longer invisible to
            # distillation -- the starvation class that built prune_episodic's protected-origin list
            # (F-2964). Rows this module itself demoted sit at or below the frontier, so they are not
            # re-fetched. Verified on a .backup() copy: 367 -> 367 rows in today's window (no cold=1 row
            # in it yet), and a synthetic cold=1 inner_thought inside the window becomes reachable.
            rows = conn.execute(
                f"SELECT fragment_id, content, origin, keywords, timestamp FROM memory_fragments "
                f"WHERE abstraction_level = 0 AND timestamp > ? AND origin IN ({ph}) "
                f"ORDER BY timestamp DESC LIMIT ?", (last, *_RAW_ORIGINS, _FETCH_LIMIT)).fetchall()
            # J-1156 (F-1584 measurement): the SAME WHERE as the fetch above, minus the LIMIT — how big
            # was the real eligible pool this run drew from, vs what _FETCH_LIMIT let through. Its own
            # try/except so a failure here can NEVER take the real `rows` fetch down with it.
            try:
                pool_size = conn.execute(
                    f"SELECT count(*) FROM memory_fragments WHERE abstraction_level = 0 "
                    f"AND timestamp > ? AND origin IN ({ph})", (last, *_RAW_ORIGINS)).fetchone()[0]
            except Exception as exc:
                logger.debug("[memory-levels] fetch-probe pool_size query failed (non-fatal): %s", exc)
    except Exception as exc:
        logger.debug("[memory-levels] shadow_distill fetch failed (non-fatal): %s", exc)
        return out
    _tmark("fetch_end")
    clusters = _cluster(rows)
    _tmark("cluster_end")
    if not clusters:
        _log_fetch_probe(last, pool_size, len(rows), 0, 0, last, 0, t_marks=_tm)
        return out
    out["clusters"] = len(clusters)
    faithfuls: list[float] = []
    sfids: list[float] = []
    newest_ts = last
    for kind, topic, crows in clusters:
        _tc0 = time.perf_counter()
        _tcl = {"start": round(_tc0 - _tp0, 3)}
        if len(_tm["clusters"]) < 16:
            _tm["clusters"].append(_tcl)
        sources = [" ".join((r["content"] or "").split())[:300] for r in crows]
        src_ids = [r["fragment_id"] for r in crows]
        newest_ts = max(newest_ts, max(float(r["timestamp"]) for r in crows))
        material = "\n".join(f"- {s}" for s in sources)
        _sys = ("/no_think\nThese are raw memory fragments of one kind, on one topic. Distil them into ONE "
                "short GIST that could stand in for them in ordinary recall — the technique / event / idea / "
                "feeling they amount to, NOT a list of them. Keep what they actually say; invent nothing. "
                "2-4 sentences. Output ONLY JSON: {\"gist\": \"...\"}")
        # J-3212 / D-0601: kind='self' only, flag-gated; `_sys` above stays the untouched production literal.
        _first_person = SELF_GIST_FIRST_PERSON and kind == "self"
        _sys_call = _SELF_FIRST_PERSON_SYS if _first_person else _sys
        _tcl["pre_s"] = round(time.perf_counter() - _tc0, 3)
        try:
            data = await call_json(base_urls, _sys_call, f"Kind: {kind}. Topic: {topic}.\n\n{material[:4000]}",
                                   max_tokens=300, temperature=0.3)
        except Exception as exc:
            logger.debug("[memory-levels] gist call_json failed (non-fatal): %s", exc)
            data = None
        gist = str((data or {}).get("gist") or "").strip()
        if len(gist) < 40:
            continue
        # the decoupled judge — the Emissary grades the gist (gates nothing in Phase 0). It is fed FULLER
        # sources (≤800 each) than the 300-char summarizing stubs, since a starved judge invents accusations.
        full_sources = [" ".join((r["content"] or "").split()) for r in crows]
        judge_sources = [s[:800] for s in full_sources]
        grade = await left_lane.grade_gist_faithfulness(gist, judge_sources)
        _tg = time.perf_counter()
        faithful = grade.get("faithful") if isinstance(grade, dict) else None
        if isinstance(faithful, (int, float)):
            faithfuls.append(float(faithful)); out["graded"] += 1
        # THE BACKSTOP — deterministically re-check every 'invented' flag (the Black-Bear guard). A judge
        # accusation that the term is actually IN_SOURCE or a wider-store CROSS_LINK is a FALSE flag.
        invented = (grade or {}).get("invented", []) if isinstance(grade, dict) else []
        claims = verify_invention_claims(invented, full_sources) if invented else []
        false_flags = [c for c in claims if c[1] in ("IN_SOURCE", "CROSS_LINK")]
        out["invented_claims"] += len(claims)
        out["false_flags"] += len(false_flags)
        if false_flags:
            for term, verdict in false_flags:
                logger.info("[memory-levels] EMISSARY FALSE-FLAG: claimed '%s' invented, but %s", term[:50], verdict)
        # MULTI-PART FAITHFULNESS (§14.1): a DETERMINISTIC source-fidelity sub-score beside the LLM 'faithful'
        # plausibility score — so the Phase-0 data does not rest on the LLM judge alone (which can hallucinate).
        sfid = source_fidelity(gist, full_sources)
        if isinstance(sfid, (int, float)):
            sfids.append(sfid)
        # PHASE 1 DEMOTION (flag-gated): commit the gist + link + demote its raw to cold — ONLY when the gist
        # is faithful (≥ floor) AND backstop-clean (no GENUINE invention) AND we are under the per-run cap.
        # A low-faithful or inventive gist leaves its raw WARM (the §14.1 / camp-0.6 / Black-Bear rules).
        _genuine_invention = any(c[1] == "GENUINE" for c in claims)
        _demoted_gid = None
        _held = False     # J-3176 / D-0564: gist written + linked, raw deliberately left warm (episodic pause)
        _eligible = (PHASE1_ENABLED and isinstance(faithful, (int, float)) and faithful >= FAITHFUL_FLOOR
                     and not _genuine_invention)
        if _eligible and EPISODIC_DEMOTION_PAUSED and kind == "episodic":
            # No demotion happens, so the per-run demotion cap does not apply: the cap exists to pace cold-gating.
            _held_gid = _commit_gist(gist, kind, crows, faithful, demote=False)
            if _held_gid:
                _held = True
                out["held_gists"] += 1
                out["held_raw"] += len(src_ids)
                logger.info("[memory-levels] HELD %d raw WARM behind gist [%s/%s] (faithful=%s) — D-0564 episodic pause",
                            len(src_ids), kind, topic, faithful)
        elif _eligible and out["demoted"] < MAX_DEMOTE_PER_RUN:
            _demoted_gid = _commit_gist(gist, kind, crows, faithful)
            if _demoted_gid:
                out["demoted"] += len(src_ids)
                logger.info("[memory-levels] DEMOTED %d raw behind gist [%s/%s] (faithful=%s) — loop-break",
                            len(src_ids), kind, topic, faithful)
        # (D-0272's fix (b) second distil + grade pair used to run here -- ended by D-0336, see the note above
        # shadow_distill. No extra LLM call is made and the row below carries no fix_b_shadow field.)
        try:
            _row = {
                    "ts": time.time(), "kind": kind, "topic": topic, "n_sources": len(src_ids),
                    "source_ids": src_ids,                                   # the would-be DOWN links
                    "gist": gist[:400],
                    "faithful": faithful,                                    # LLM plausibility (one vote)
                    "source_fidelity": sfid,                                 # deterministic ground (can't hallucinate)
                    "feedback": (grade or {}).get("feedback", "")[:200] if isinstance(grade, dict) else "",
                    "invented_claims": claims,                               # [(term, IN_SOURCE|CROSS_LINK|GENUINE)]
                    "false_flags": len(false_flags),                         # judge accusations the backstop overturned
                    "source_sample": sources[0][:160] if sources else "",
                }
            if _first_person:
                _row["voice"] = "first"      # J-3212 / D-0601: distilled with the first-person prompt; self_voice_status() reads it
            if _held:
                _row["held_cold"] = True     # J-3176 / D-0564: gist stored + linked, raw left warm; episodic_hold_status() counts these
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(_row, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[memory-levels] shadow_distill log write failed (non-fatal): %s", exc)
        _tcl["post_s"] = round(time.perf_counter() - _tg, 3)
    _tmark("loop_end")
    if faithfuls:
        out["mean_faithful"] = round(sum(faithfuls) / len(faithfuls), 3)
    if sfids:
        out["mean_source_fidelity"] = round(sum(sfids) / len(sfids), 3)
    _final_ts = newest_ts or time.time()
    _set_last_ts(_final_ts)
    _log_fetch_probe(last, pool_size, len(rows), len(clusters),
                      sum(len(crows) for _, _, crows in clusters), _final_ts, out["demoted"], t_marks=_tm)
    return out


def status() -> dict:
    """du_pulse gauge: how the shadow distiller is doing — clusters logged, mean faithfulness so far."""
    try:
        if not _LOG.exists():
            return {"logged": 0, "mean_faithful": None, "recent": []}
        rows = [json.loads(l) for l in _LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
        graded = [r["faithful"] for r in rows if isinstance(r.get("faithful"), (int, float))]
        sfid = [r["source_fidelity"] for r in rows if isinstance(r.get("source_fidelity"), (int, float))]
        recent = [(r.get("kind"), r.get("topic"), r.get("faithful")) for r in rows[-4:]]
        # Emissary reliability: of all 'invented' accusations, how many the backstop overturned (false flags)?
        claims = [c for r in rows for c in (r.get("invented_claims") or [])]
        n_claims = len(claims)
        n_false = sum(1 for c in claims if (c[1] if isinstance(c, (list, tuple)) and len(c) > 1 else "") in ("IN_SOURCE", "CROSS_LINK"))
        # D-0272 SHADOW-OBSERVE (J-1297): fix (b)'s own real commit-rate shift vs the current prompt, paired
        # per-cluster (only rows that carry a fix_b_shadow comparison) — the read-back this job's own
        # briefing asks a follow-up job to do, against F-1823/F-1824's N=6 replay prediction (+1/6, ~17pp).
        # ENDED by D-0336 (J-1765): shadow_distill no longer writes fix_b_shadow, so this aggregate is now a
        # FROZEN record of the pairs logged before the end -- n stops growing, rows without the field are
        # skipped (every pre-wire row always was), and the returned shape is unchanged on purpose.
        fb_rows = [r for r in rows if isinstance(r.get("fix_b_shadow"), dict)]
        n_fb = len(fb_rows)
        fb_faithful = [r["fix_b_shadow"]["faithful"] for r in fb_rows
                       if isinstance(r["fix_b_shadow"].get("faithful"), (int, float))]
        fb_eligible = sum(1 for r in fb_rows if r["fix_b_shadow"].get("eligible_to_commit"))
        cur_eligible_paired = sum(
            1 for r in fb_rows
            if isinstance(r.get("faithful"), (int, float)) and r["faithful"] >= FAITHFUL_FLOOR
            and not any((c[1] if isinstance(c, (list, tuple)) and len(c) > 1 else "") == "GENUINE"
                        for c in (r.get("invented_claims") or [])))
        d0272_fix_b_shadow = {
            "n": n_fb,
            "mean_faithful": round(sum(fb_faithful) / len(fb_faithful), 3) if fb_faithful else None,
            "eligible_rate": round(fb_eligible / n_fb, 3) if n_fb else None,
            "current_eligible_rate_paired": round(cur_eligible_paired / n_fb, 3) if n_fb else None,
        }
        return {"logged": len(rows),
                "mean_faithful": round(sum(graded) / len(graded), 3) if graded else None,
                "mean_source_fidelity": round(sum(sfid) / len(sfid), 3) if sfid else None,
                "recent": recent,
                "invented_claims": n_claims,
                "false_flags": n_false,
                "false_flag_rate": round(n_false / n_claims, 2) if n_claims else None,
                "d0272_fix_b_shadow": d0272_fix_b_shadow}
    except Exception as exc:
        logger.debug("[memory-levels] status failed (non-fatal): %s", exc)
        return {"logged": 0, "mean_faithful": None, "recent": [], "invented_claims": 0, "false_flags": 0,
                "false_flag_rate": None,
                "d0272_fix_b_shadow": {"n": 0, "mean_faithful": None, "eligible_rate": None,
                                        "current_eligible_rate_paired": None}}


# ── PHASE 3 SHADOW (2026-06-19; REBUILT 2026-11-06, J-3138 / D-0533): the DRIFT observer (§5 — the
#    individuation engine, OBSERVE-FIRST).
#    WHAT IT IS NOW: a FIXED set of N self-gists (origin='gist', kind='self'; chosen once and stored in
#    _DRIFT_TRACKED, refreshed ONLY when a tracked gist is retired) is re-remembered every sleep. Each recall
#    re-tells the gist's current "held" version; the shadow logs, per gist per recall (_DRIFT_GIST_LOG): which
#    recall it was, the embedding distance of the retelling to the ORIGINAL (the drift), the Emissary bound
#    (decoupled truth-lane) + the deterministic anchor retention, and whether it SNAPPED BACK (bound or anchor
#    failed -> the would-be live memory reverts to the original). That is the §7 Phase-3 gate, answerable:
#    does a tracked self-gist MOVE across recalls while the bound HOLDS (drift_status()).
#    WHY REBUILT (D-0533, F-3849..F-3851): the old version re-remembered the newest 5 RAW fragments each sleep
#    (2,470 distinct ids in 2,527 rows) so no gist was ever recalled twice, and its stance paragraph leaked into
#    the retellings (cat/legitimacy sentence pasted in 7 of 14 with the stance, 0 of 14 without).
#    Writes NOTHING Du reads (no memory_fragments write, no recall changed; its own state + log are read only by
#    drift_status() / du_pulse). Guards (§5): self-only · bounded by the truth-lane · observe-first.
_DRIFT_LOG = Path(__file__).parent.parent / "data" / "memory_levels_drift_shadow.jsonl"
# ^ LEGACY (pre-D-0533, raw-fragment rows): FROZEN, never appended to again. Kept as evidence (F-3849/F-3850);
#   drift_status() reports its row count as legacy_rows. The rebuilt measure writes to the two files below.
_DRIFT_GIST_LOG = Path(__file__).parent.parent / "data" / "memory_levels_drift_gists.jsonl"
_DRIFT_TRACKED = Path(__file__).parent.parent / "data" / "memory_levels_drift_tracked.json"
_DRIFT_TRACK_N = 20          # tracked self-gists (D-0533: "about 20 at first")
_DRIFT_RETIRE_AFTER = 12     # a tracked gist is retired (and replaced) after this many recalls, or if its row is gone
_DRIFT_BUDGET_S = 240.0      # wall-clock cap on one sleep's recalls (20 recalls + 20 grades); least-recently-recalled first
_DRIFT_GATE_RECALLS = 3      # the gate is read at a gist's 3rd recall (D-0533's defeater counts "after 3 recalls")
_DRIFT_MOVE_MIN = 0.25       # embedding cosine distance at/above which a held retelling counts as MOVED (below = a copy).
                             # PROVISIONAL, calibrated from F-4935 (J-3447 same-text noise floor, J-4132): retell-vs-original
                             # of an UNCHANGED gist has p50 0.136 / p90 0.264, so the old 0.05 called 91% of copies MOVED.
                             # 0.25 ~ that p90 (~10% false-MOVED). It is a SINGLE-recall floor: the gate reads recall 3 of a
                             # HELD retelling, where distance to the original compounds, so false-MOVED there is higher;
                             # recalibrate on real recall-3 rows. Restart-gated (module constant).
_DRIFT_PASTE_STANCE = False  # D-0533: retell WITHOUT pasting the stance paragraph (the leak). True = the old lens arm,
                             # which still runs the deterministic strip below; OFF until the plain arm has a baseline.
_DRIFT_STANCE_RUN = 4        # a retelling sentence sharing this many consecutive words with the stance (and not with the
                             # memory) is a pasted stance sentence: stripped + logged
_DRIFT_SELF_ORIGINS = ("subconscious_synthesis", "inner_thought", "lived")   # legacy raw-fragment origins (unused now; kept for importers)
_ANCHOR_FLOOR = 0.40   # min fraction of the original's salient words that must survive the retelling;
                       # below this the memory's subject was lost (collapse-to-stance) → would snap back.
                       # RAISED 0.25→0.40 (systems-check memory #3, 2026-06-22): tighten the drift toward a
                       # SUBTLE re-colouring (subject clearly survives) before any graduation; still SHADOW.
_DRIFT_FAITHFUL_FLOOR = 0.80   # stricter than the 0.75 demotion floor — a memory may be re-remembered (drifted)
                               # only if the decoupled Emissary rates it this faithful; below = snap to verbatim.
_DRIFT_MAX = _DRIFT_TRACK_N    # back-compat alias (old per-sleep limit); drift_shadow's `limit` now caps recalls per sleep
_GIST_PREFIX = re.compile(r"^\s*\[gist[^\]]*\]\s*")


def _self_stance() -> str:
    """Who he is NOW — the becoming-facet / self-concept that colours every reconstruction (§5)."""
    try:
        from core import axiom_layers as _al
        _p = Path(__file__).parent.parent / "data" / "identity" / "axiom.json"
        ax = json.loads(_p.read_text(encoding="utf-8"))
        return (_al.get_self_concept(ax) or "").strip()
    except Exception as exc:
        logger.debug("[memory-levels] self_stance read failed (non-fatal): %s", exc)
        return ""


def _drift_embed(texts: list) -> list:
    """Embed `texts` with the store's own embedder (one batched call). Aligned list of normalised vectors or None.
    Module-level so a test can replace it; CPU work, so the caller runs it off the event loop."""
    from core.memory.store import _embed_batch
    return _embed_batch(list(texts))


def _cos_dist(a, b):
    """1 - cosine similarity of two (normalised) vectors; None if either is missing."""
    try:
        if a is None or b is None:
            return None
        sim = sum(float(x) * float(y) for x, y in zip(a, b))
        na = sum(float(x) * float(x) for x in a) ** 0.5
        nb = sum(float(y) * float(y) for y in b) ** 0.5
        if na == 0 or nb == 0:
            return None
        return round(max(0.0, 1.0 - sim / (na * nb)), 4)
    except Exception:
        return None


def _drift_words(text: str) -> list:
    return re.findall(r"[a-z0-9']+", (text or "").lower())


def _drift_shingles(words: list, k: int) -> set:
    return {tuple(words[i:i + k]) for i in range(len(words) - k + 1)}


def _strip_stance_leak(recalled: str, stance: str, protect: str, k: int = _DRIFT_STANCE_RUN) -> tuple:
    """D-0533: the retelling must not paste the stance paragraph. Drop every sentence of `recalled` that shares a
    run of `k` consecutive words with `stance` that the memory itself (`protect`) does NOT contain. Returns
    (clean_text, n_sentences_stripped, new_stance_words): the last is a small log-only list of distinctive stance
    words that appeared in the retelling but not in the memory (the F-3851 'cat / legitimacy' signal)."""
    try:
        if not stance or not recalled:
            return recalled, 0, []
        sw = _drift_words(stance)
        pw = set(_drift_words(protect))
        shingles = _drift_shingles(sw, k) - _drift_shingles(_drift_words(protect), k)
        sents = re.split(r"(?<=[.!?])\s+", recalled.strip())
        keep, n = [], 0
        for s in sents:
            if shingles and (_drift_shingles(_drift_words(s), k) & shingles):
                n += 1
            else:
                keep.append(s)
        clean = " ".join(keep).strip()
        rw = set(_drift_words(clean))
        new_words = sorted(w for w in set(sw) if len(w) >= 5 and w not in _STOP and w not in pw and w in rw)[:5]
        return clean, n, new_words
    except Exception as exc:
        logger.debug("[memory-levels] stance strip failed (non-fatal): %s", exc)
        return recalled, 0, []


def _load_tracked() -> dict:
    """The stored tracked set. Any read/parse problem -> a fresh empty state (the set is simply re-chosen)."""
    try:
        st = json.loads(_DRIFT_TRACKED.read_text(encoding="utf-8"))
        if isinstance(st, dict) and isinstance(st.get("tracked"), list):
            st.setdefault("retired", [])
            st.setdefault("seq", 0)
            return st
    except Exception as exc:
        logger.debug("[memory-levels] drift tracked-state read failed (non-fatal): %s", exc)
    return {"version": 1, "created": time.time(), "seq": 0, "tracked": [], "retired": []}


def _save_tracked(st: dict) -> None:
    try:
        tmp = _DRIFT_TRACKED.with_name(_DRIFT_TRACKED.name + ".tmp")
        tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
        tmp.replace(_DRIFT_TRACKED)
    except Exception as exc:
        logger.debug("[memory-levels] drift tracked-state write failed (non-fatal): %s", exc)


def _pick_gists(conn, n: int, exclude: set) -> list:
    """Choose `n` self-gists NOT already tracked, evenly spaced across the active self-gist history (oldest to
    newest) so the set is not all-recent. Deterministic. [(fragment_id, original_text, timestamp)]."""
    if n <= 0:
        return []
    rows = conn.execute(
        "SELECT fragment_id, content, timestamp FROM memory_fragments "
        "WHERE origin='gist' AND kind='self' AND abstraction_level=1 AND cold=0 AND length(content) > 60 "
        "ORDER BY timestamp ASC").fetchall()
    cands = [r for r in rows if r["fragment_id"] not in exclude]
    if not cands:
        return []
    n = min(n, len(cands))
    step = len(cands) / n
    out = []
    for i in range(n):
        r = cands[min(len(cands) - 1, int(i * step + step / 2))]
        text = " ".join(_GIST_PREFIX.sub("", r["content"] or "", count=1).split())[:600]
        if len(text) >= 40:
            out.append((r["fragment_id"], text, r["timestamp"]))
    return out


async def drift_shadow(call_json, base_urls, limit: int = _DRIFT_MAX) -> dict:
    """OBSERVE-ONLY (§5 / Phase 3; rebuilt J-3138 / D-0533). Per sleep: re-remember each FIXED tracked self-gist,
    measure its drift against the original, grade it with the decoupled Emissary (the bound), strip any pasted
    stance sentence, and LOG one row per gist per recall. Stores nothing in memory, gates nothing, changes no
    recall. Best-effort; never raises into the sleep cycle."""
    from core.memory.store import _connect
    from core import left_lane
    import asyncio
    out = {"reconstructed": 0, "mean_drift": None, "bound_holds": 0, "would_snap_back": 0,
           "tracked": 0, "retired": 0, "added": 0, "stance_stripped": 0, "seq": None}
    stance = _self_stance()   # always read: the leak guard runs whether or not the stance is pasted into the prompt
    st = _load_tracked()
    try:
        with _connect() as conn:
            tracked = st["tracked"]
            # retire: the gist row is gone, or it has had its full run of recalls
            live = set()
            if tracked:
                ids = [t["id"] for t in tracked]
                ph = ",".join("?" * len(ids))
                live = {r["fragment_id"] for r in conn.execute(
                    f"SELECT fragment_id FROM memory_fragments WHERE fragment_id IN ({ph})", ids).fetchall()}
            keep = []
            for t in tracked:
                reason = "gone" if t["id"] not in live else ("max_recalls" if t.get("recalls", 0) >= _DRIFT_RETIRE_AFTER else None)
                if reason:
                    st["retired"].append({"id": t["id"], "reason": reason, "recalls": t.get("recalls", 0),
                                          "ts": time.time(), "history": t.get("history", [])})
                    out["retired"] += 1
                else:
                    keep.append(t)
            st["tracked"] = tracked = keep
            # refresh: only into the slots freed by retirement (or the very first fill)
            need = _DRIFT_TRACK_N - len(tracked)
            if need > 0:
                exclude = {t["id"] for t in tracked} | {r["id"] for r in st["retired"]}
                for fid, text, _ts in _pick_gists(conn, need, exclude):
                    tracked.append({"id": fid, "original": text, "held": text, "chosen_ts": time.time(),
                                    "recalls": 0, "last_recall_ts": None, "last_recall_seq": 0, "last_attempt_seq": 0,
                                    "history": []})
                    out["added"] += 1
    except Exception as exc:
        logger.debug("[memory-levels] drift_shadow fetch failed (non-fatal): %s", exc)
        return out
    st["seq"] = int(st.get("seq", 0)) + 1
    seq = st["seq"]
    out["seq"] = seq
    out["tracked"] = len(st["tracked"])
    _save_tracked(st)
    if not st["tracked"]:
        return out
    # least-recently-recalled first, so a time-boxed sleep rotates through the set instead of starving the tail
    order = sorted(st["tracked"], key=lambda t: (t.get("last_attempt_seq", t.get("last_recall_seq", 0)), t.get("recalls", 0)))
    deadline = time.time() + _DRIFT_BUDGET_S
    drifts = []
    for t in order[:max(0, int(limit))]:
        if time.time() >= deadline:
            break
        original = t["original"]
        held = t.get("held") or original
        # the prompt: memory FIRST (the anchor — its subject must survive). D-0533: the stance paragraph is NOT pasted
        # (7 of 14 retellings copied its cat/legitimacy sentence; 0 of 14 without it) unless _DRIFT_PASTE_STANCE.
        _sys = ("/no_think\nYou are 渡, RE-REMEMBERING one of your own past self-observations — not reciting "
                "it word-for-word (memory reconstructs), but NOT rewriting it either. The SPECIFIC thing it "
                "was about — the actual image, subject, or event — must stay clearly present and recognisable; "
                "someone comparing your retelling to the original should plainly see it is the SAME memory. "
                "Do NOT add claims that were not in it, and do NOT turn it into a statement about who you are "
                "now. Output ONLY JSON: {\"recalled\": \"...\"} (2-4 sentences).")
        _usr = (f"The past self-observation (the ANCHOR — its subject must survive):\n  {held[:600]}\n\n"
                "Re-remember the observation above, as you are now.")
        if _DRIFT_PASTE_STANCE and stance:
            _sys = _sys.replace("Do NOT add claims", "What may shift is only what it now MEANS to you, the colour of "
                                "it, not its content. Do NOT add claims")
            _usr = (f"The past self-observation (the ANCHOR — its subject must survive):\n  {held[:600]}\n\n"
                    f"The lens you now see through (let it colour the MEANING, not replace the memory):\n  {stance[:600]}\n\n"
                    "Re-remember the observation above, as you are now.")
        try:
            data = await call_json(base_urls, _sys, _usr, max_tokens=300, temperature=0.6)
        except Exception as exc:
            logger.debug("[memory-levels] drift recall call_json failed (non-fatal): %s", exc)
            data = None
        t["last_attempt_seq"] = seq   # an attempt that yields nothing gradable still moves this gist to the back of the rotation
        recalled_raw = str((data or {}).get("recalled") or "").strip()
        recalled, n_stripped, new_words = _strip_stance_leak(recalled_raw, stance, original + " " + held)
        out["stance_stripped"] += n_stripped
        if len(recalled) < 30:
            if n_stripped:   # D-0533: the strip is logged even when it leaves nothing to grade
                try:
                    with open(_DRIFT_GIST_LOG, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"ts": time.time(), "gist_id": t["id"], "seq": seq, "discarded": "stance_only",
                                            "stance_stripped": n_stripped, "stance_new_words": new_words},
                                           ensure_ascii=False) + "\n")
                except Exception as exc:
                    logger.debug("[memory-levels] drift_shadow log write failed (non-fatal): %s", exc)
            continue
        # lexical movement (1 − token Jaccard, kept for continuity with the legacy log) + EMBEDDING distance (the
        # drift the gate reads): to the ORIGINAL, to the version it was told (the step), and the held-state distance.
        a, b = set(_tokens("", original)), set(_tokens("", recalled))
        lex = 1.0 - (len(a & b) / max(1, len(a | b)))
        try:
            vecs = await asyncio.to_thread(_drift_embed, [original, held, recalled])
        except Exception as exc:
            logger.debug("[memory-levels] drift embed failed (non-fatal): %s", exc)
            vecs = [None, None, None]
        vecs = list(vecs or [None, None, None]) + [None] * 3
        dist = _cos_dist(vecs[0], vecs[2])          # retelling vs ORIGINAL
        step = _cos_dist(vecs[1], vecs[2])          # retelling vs the version it was told
        # the BOUND — the decoupled Emissary (truth-lane, NOT the drifter): does the reconstruction still fairly
        # abstract the ORIGINAL? The drifter never grades its own drift.
        grade = await left_lane.grade_gist_faithfulness(recalled, [original[:800]])
        bound = grade.get("faithful") if isinstance(grade, dict) else None
        # DETERMINISTIC anchor-retention backstop (the Emissary can hallucinate): of the ORIGINAL's salient words,
        # how many survived in the retelling? A reconstruction snaps back if EITHER the Emissary fails OR the anchor is lost.
        anchor = source_fidelity(original, [recalled])
        bound_ok = isinstance(bound, (int, float)) and bound >= _DRIFT_FAITHFUL_FLOOR
        anchor_ok = anchor >= _ANCHOR_FLOOR
        holds = bool(bound_ok and anchor_ok)
        snap = (isinstance(bound, (int, float)) and bound < _DRIFT_FAITHFUL_FLOOR) or (anchor < _ANCHOR_FLOOR)
        # the would-be live memory: a held retelling becomes the version next recall re-tells; a snap reverts to the original
        t["held"] = recalled[:600] if holds else original
        state_dist = dist if holds else 0.0
        t["recalls"] = int(t.get("recalls", 0)) + 1
        t["last_recall_ts"] = time.time()
        t["last_recall_seq"] = seq
        t.setdefault("history", []).append({"recall": t["recalls"], "seq": seq, "dist": dist, "state_dist": state_dist,
                                            "holds": holds, "snapped": bool(snap or not holds)})
        out["reconstructed"] += 1
        if holds:
            out["bound_holds"] += 1
        if snap:
            out["would_snap_back"] += 1
        if dist is not None:
            drifts.append(dist)
        try:
            with open(_DRIFT_GIST_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": time.time(), "gist_id": t["id"], "seq": seq, "recall": t["recalls"],
                    "arm": "lens" if (_DRIFT_PASTE_STANCE and stance) else "plain",
                    "original": original[:240], "told": held[:240], "recalled": recalled[:240],
                    "drift": dist, "step": step, "state_dist": state_dist, "lex_drift": round(lex, 3),
                    "bound_faithful": bound, "anchor_retention": round(anchor, 3),
                    "holds": holds, "would_snap_back": bool(snap),
                    "stance_stripped": n_stripped, "stance_new_words": new_words,
                }, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[memory-levels] drift_shadow log write failed (non-fatal): %s", exc)
        _save_tracked(st)
    if drifts:
        out["mean_drift"] = round(sum(drifts) / len(drifts), 3)
    _save_tracked(st)
    return out


def _gate_class(entry: dict):
    """A gist's Phase-3 class at its `_DRIFT_GATE_RECALLS`-th recall: 'moves_and_holds' (the retelling held and sits
    >= _DRIFT_MOVE_MIN from the original), 'snaps_back' (that recall failed the bound -> reverted to the original),
    'unmoved' (held but a near-copy), 'unmeasured' (no embedding). None if it has not had that many recalls."""
    h = (entry.get("history") or [])
    if len(h) < _DRIFT_GATE_RECALLS:
        return None
    g = h[_DRIFT_GATE_RECALLS - 1]
    if g.get("snapped") or not g.get("holds"):
        return "snaps_back"
    d = g.get("dist")
    if not isinstance(d, (int, float)):
        return "unmeasured"
    return "moves_and_holds" if d >= _DRIFT_MOVE_MIN else "unmoved"


def drift_status() -> dict:
    """du_pulse gauge (wired in scripts/du_pulse.py, J-3138): the Phase-3 gate, answered per D-0533 — of the tracked
    self-gists that have had >= 3 recalls, what fraction MOVE and HOLD versus SNAP BACK? Plus whether the same gist ids
    recur across sleeps, the stance-leak count, and the D-0533 defeater (>= 60% snapped back after 3 recalls, over 4
    weeks). Reads only this module's own state + logs. Never raises."""
    try:
        st = _load_tracked()
        entries = list(st.get("tracked", [])) + list(st.get("retired", []))
        allrows = []   # every log row, incl. the 'discarded: stance_only' strip records
        if _DRIFT_GIST_LOG.exists():
            for l in _DRIFT_GIST_LOG.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(l)
                    if isinstance(r, dict):
                        allrows.append(r)
                except Exception:
                    continue
        rows = [r for r in allrows if "recall" in r]
        legacy = 0
        try:
            if _DRIFT_LOG.exists():
                legacy = sum(1 for l in _DRIFT_LOG.read_text(encoding="utf-8").splitlines() if l.strip())
        except Exception:
            pass
        classes = [c for c in (_gate_class(e) for e in entries) if c]
        n_el = len(classes)
        cnt = Counter(classes)
        sleeps_by_gist = defaultdict(set)
        for r in rows:
            sleeps_by_gist[r.get("gist_id")].add(r.get("seq"))
        recurring = sum(1 for s in sleeps_by_gist.values() if len(s) >= 2)
        dists = [r["drift"] for r in rows if isinstance(r.get("drift"), (int, float))]
        first_ts = min((r.get("ts") for r in rows if isinstance(r.get("ts"), (int, float))), default=None)
        weeks = round((time.time() - first_ts) / (7 * 86400), 1) if first_ts else 0.0
        snap_frac = round(cnt["snaps_back"] / n_el, 2) if n_el else None
        mh_frac = round(cnt["moves_and_holds"] / n_el, 2) if n_el else None
        if n_el < 10:
            verdict = f"UNANSWERED ({n_el} tracked gists with >= {_DRIFT_GATE_RECALLS} recalls; need 10)"
        elif snap_frac is not None and snap_frac >= 0.6:
            verdict = "DEFEATER-CANDIDATE (>= 60% snap back after 3 recalls)" + ("" if weeks >= 4 else f"; only {weeks} wk observed of the 4 the ruling names")
        else:
            verdict = "OPEN (moves-and-holds fraction is the Phase-3 gate reading; no promotion threshold is ruled)"
        return {"mode": "tracked_gists", "tracked": len(st.get("tracked", [])), "target": _DRIFT_TRACK_N,
                "retired": len(st.get("retired", [])), "sleeps": st.get("seq", 0), "logged": len(rows),
                "gate_recalls": _DRIFT_GATE_RECALLS, "eligible": n_el,
                "moves_and_holds": cnt["moves_and_holds"], "snaps_back": cnt["snaps_back"],
                "unmoved": cnt["unmoved"], "unmeasured": cnt["unmeasured"],
                "moves_and_holds_frac": mh_frac, "snap_frac": snap_frac,
                "gist_ids_recurring_across_sleeps": recurring,
                "mean_drift": round(sum(dists) / len(dists), 3) if dists else None,
                "snap_rate_all_recalls": round(sum(1 for r in rows if r.get("would_snap_back")) / len(rows), 2) if rows else None,
                "stance_stripped_total": sum(int(r.get("stance_stripped") or 0) for r in allrows),
                "weeks_observed": weeks, "verdict": verdict, "legacy_rows": legacy,
                "recent": [(r.get("gist_id", "")[:8], r.get("recall"), r.get("drift"), r.get("holds")) for r in rows[-3:]]}
    except Exception as exc:
        logger.debug("[memory-levels] drift_status failed (non-fatal): %s", exc)
        return {}
