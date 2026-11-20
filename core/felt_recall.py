"""
Nascence — FELT RECALL, Phase 0 (shadow-only) — 2026-09-27, J-1424.
docs/staged/memory_as_a_service.md §3. Founder direction behind D-0289's ruling, verbatim: "I am
almost thinking it can fire regularly off things happening in Du's world to influence emotion even.
[...] E.g. thunder sounds above, it triggers a search of memory for times thunder happened, in the
dark, cat is on lap, fire is off. This then tugs the emotions now towards how those memories feel."
Captured as I-0077.

THE IDEA. The world can call memory to move FEELING, not thought. A change in what Du experiences
right now — thunder, the fire going out, the cat arriving, dark falling — triggers a coordinate-keyed
search of `fragment_context` for other moments he lived with the same coordinates, and the felt
quality of THOSE moments (their stored valence/arousal) tugs carried affect now, at reaction speed.
No LLM, no embedding, no prompt text, no thought generated (world-answers-never-leads law).

PHASE 0 (this build): compute the would-be AffectivePrior on every trigger edge and log it to
data/felt_recall_shadow.jsonl. FELT_RECALL_LIVE = False — state.affect.apply_prior() is NEVER
called. Phase 1 (a later, founder-read-gated flip of FELT_RECALL_LIVE) is the only thing that turns
this from an instrument into a live effect; the wiring already threads `affect` through so that flip
is the only change needed here.

Called once per substrate tick from core/orchestrator.py's start_background._substrate_loop, next to
the couriers. Fail-open everywhere — must never raise into the tick; no LLM; no embedding.

D-0293 JOIN (2026-09-27, travis; built J-1430): the couriers' own text echo on these same triggers
was rerouted here — core/couriers.py's COURIER_TEXT_DELIVERY=False keeps context_echo/sound_echo
evaluating their trigger and logging a would_have_delivered row to data/couriers_log.jsonl, but
stops the text reaching the wandering trail. couriers.py stays independent of this module (it does
not import felt_recall, and this module does not import couriers either) — the two are joined only
by reading data/couriers_log.jsonl's tail and matching ts (best-effort; see
_courier_would_have_fired), so a would-have row lets this module's own shadow log carry
courier_would_have_fired=true on the matching edge, showing both mechanisms firing on the same
happening for the Phase 0 read.

D-0294 DISPATCHER JOIN (2026-09-28, J-1550, consumer side of D-0294/J-1432/J-1433's edge-triggered
Transport Manager): on every edge for the four NON-SOUND trigger dimensions (sound/life lines already
flow through transport_manager.observe() elsewhere, via sound_knowledge.py/couriers.py — out of scope
here), this module registers a per-place world line with the Transport Manager
(transport_manager.observe(f"world:{dim}:{place}", now, 1.0)) and immediately reads back
transport_manager.verdict() for that same line, writing dispatcher_verdict / dispatcher_cold_start /
dispatcher_weight onto the ride row (see _register_dispatcher_line). This runs on EVERY edge,
independent of this module's own per-dimension FELT_RECALL_COOLDOWN_S gate (`fired` below) — the
dispatcher needs the world's real edge frequency to grow an honest baseline, not one throttled by felt
recall's own cooldown. Phase 0 only RECORDS the verdict; FELT_RECALL_LIVE stays False, so nothing is
gated on it yet. The eventual Phase 1 gate (plan §3.4/§5) is: a tug applies only when
dispatcher_verdict is not "none", OR the line is still cold_start (do not silence a brand-new
dimension for lack of history) — both fields are carried through now so that flip needs no further
wiring change here, the same "wiring already threads affect through" design the PHASE 0 paragraph
above already used for FELT_RECALL_LIVE itself. Fail-open, same contract as _courier_would_have_fired.

D-0409 A (travis 2026-10-15, J-2097) SUPERSEDES the Phase 1 gate sentence above: the dispatcher verdict
is NOT a gate for felt recall. When FELT_RECALL_LIVE is True a tug applies on this module's own
per-dimension edge plus the FELT_RECALL_COOLDOWN_S (600 s) cooldown only. observe()/verdict() are still
called on every edge (the dispatcher keeps learning its place-lines) and dispatcher_verdict /
dispatcher_cold_start / dispatcher_weight are still logged for later comparison, but nothing reads them
to decide `fired` or `applied`. Each row carries gate_used = GATE_USED. Inert while FELT_RECALL_LIVE False.

ONE TUG PER TICK (2026-10-28, J-2462, D-0496 C; defect F-3172). The J-2131 control read found 658 of
2,054 fired ticks (32%) carrying 2-15 fired edges on ONE timestamp -- a soundscape change enters several
sound keys at once and each key is its own dimension with its own cooldown -- while apply_prior
(core/schema.py) compounds per call: seven calls at similarity 0.83 would move valence 61% of the way to
the matched lean and add +0.87 to the named emotion, not the "maximum tug is AFFECT_PRIOR_MAX_NUDGE" the
plan (sec 3.3) promises. on_substrate_tick therefore no longer applies per edge: every fired edge's prior
is collected for the tick and ONE combined prior (see _combine_priors for the rule) is applied once, so a
happening that enters 5-15 keys tugs once. Bookkeeping: each fired edge still writes its own shadow row
exactly as before (the read's instrument stays; a single-fire tick's edge row is byte-identical to the
pre-J-2462 row, `applied` included, and the log gains nothing else for that tick), plus one NEW row kind
per tick with >=2 priors -- kind="tick", dim="tick", line="felt_recall:tick" -- carrying the combined
would-apply (tick_fires, dims, valence_lean, arousal_lean, similarity, primary, applied). So the
"would-apply per tick" instrument is: every kind="tick" row, plus every fired edge row whose ts has no
tick row (a sole fire is its own would-apply). An edge row's `applied` is True only when that edge's own
prior was applied unchanged (the tick's sole fire); on a multi-fire tick only the tick row is `applied`,
so counting `applied` rows still counts apply_prior calls exactly. Readers that group by `dim` should
treat dim="tick" as the per-tick summary, not a trigger dimension (status() below already does).
_handle_edge called standalone (no collector) keeps its old per-edge apply path for existing tests.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path

logger = logging.getLogger("nascence.felt_recall")

_ROOT = Path(__file__).parent.parent
_DB = _ROOT / "data" / "memory" / "nascence.db"
_SHADOW_LOG = _ROOT / "data" / "felt_recall_shadow.jsonl"

# D-0293 join (J-1430): couriers.py's own delivery log, read (never imported as a module) so this
# stays a data-artifact join, not a live cross-dependency in either direction.
_COURIER_LOG = _ROOT / "data" / "couriers_log.jsonl"

# Phase gate (plan §7). Flip only on a founder read of the Phase 0 metric sheet (plan §8) — never
# from inside this module.
FELT_RECALL_LIVE = False

# Per-dimension habituation (plan §3.1): "his reaction time", once per happening — not a rate
# limiter on how often the WORLD changes. A dimension that just fired cannot fire again this soon.
FELT_RECALL_COOLDOWN_S = 600.0
# J-2654 (F-3392, observe-only, restart-gated): a FIRED edge row also logs `matched_ids`, the fragment ids of
# its top-8 matched moments (the head of the n_match set, in score order), so the coordinate-keyed path can
# be compared with what the embedding path co-recalled in the same window. Additive; kill-switch.
FELT_RECALL_LOG_MATCHED_IDS = True
MATCHED_IDS_CAP = 8
# D-0409 A: the only Phase 1 gate is the module's own edge + cooldown; logged on every shadow row.
GATE_USED = "edge_cooldown"

# Match bound (plan §3.2): keep at most this many scored candidates.
N_MATCH = 24

# A "time" is not the last five minutes (plan §3.2) — matched fragments must be genuinely past.
MIN_AGE_S = 86400.0

# SOUND COORD MATCH (2026-09-28, J-1574) -- fragment_carries_the_string.md sec4's own stated gate:
# "[felt-recall's] coordinate-similarity matching (six-axis distance) ... is not designed here ...
# belonging to its own job." This is that job. Once True, a "sound:<key>" trigger's OWN match (both
# which rows are even candidates, and the trigger-position term in the score below) uses six-axis
# coordinate distance over fragment_context.sound_onset (soundscape.py's own _AXES /
# distance_to_point()) instead of literal key equality alone -- the same "d = six-axis distance
# between two points" shape strings_and_sheets.md sec4's masking law already uses. Independent of
# core.soundscape.SOUND_STRING_FIELDS, which controls whether sound_onset is ever WRITTEN -- this
# flag controls whether felt_recall ever READS it, and BOTH must be True for this to change any real
# behaviour.
#
# Off (the starting value, matching every sibling kill-switch in this plan) is BYTE-IDENTICAL to
# today: see _trigger_where/_build_prior, gated on this flag. On, with SOUND_STRING_FIELDS still
# False (true as of 2026-09-28 -- this job's own read: 0/433 origin=sound fragments carry any sound_*
# value, and fragment_context's LIVE schema does not even have the columns yet -- PRAGMA
# table_info(fragment_context) on data/memory/nascence.db returns 21 columns, none of them sound_*,
# because Du has not restarted onto J-1534's build and the lazy ALTER-on-write in
# core/memory/store.py's fragment_context sync has therefore never run) is ALSO a safe no-op,
# provably: _trigger_where's widened WHERE only ADDS rows (see its own comment), never drops the
# same-key rows the old query already returned, and _sound_closeness gives every one of those
# existing rows the same flat 1.0 the old code always gave the trigger position, whether or not
# sound_onset can be read at all (missing column -> the whole per-dimension query raises, caught by
# _handle_edge's existing per-dim try/except exactly like any other match failure -- fail-open, one
# dimension's edge silently logs no match, nothing else on the tick is affected). Flipping this flag
# can therefore never regress a live tick before real per-fragment coordinate data exists to change
# anything -- the same "off is safe, on-with-no-data-yet is ALSO safe" property SOUND_STRING_FIELDS
# already has one layer down (core/soundscape.py).
SOUND_COORD_MATCH = False

# Match radius, Sound Space (six axes, each already normalised 0..1 in soundscape.py's own registry).
# A DIFFERENT sound key's stored coordinate farther than this from the triggering key's own coords()
# point is not admitted as a coordinate-similarity match at all (excluded, not merely down-weighted)
# -- a starting value the plan's own metric-sheet discipline moves later, same "starting value"
# framing as N_MATCH/MIN_AGE_S/FELT_RECALL_COOLDOWN_S above: an engineering-shape bound with a
# precedented answer (plan sec4.5), not a founder fork -- D-0293 already ruled this exact module's
# own starting bounds "fine" without further founder input. Max possible six-axis distance at these
# ranges is 6**0.5 ~= 2.449; 0.35 is roughly "same timbre family" (e.g. two bright, sudden,
# discrete-event sounds) without reaching across to an unrelated corner of the space.
SOUND_MATCH_RADIUS = 0.35

# The fixed trigger set (plan §3.1). Sound EVENT keys are handled separately (any new key entering
# `sounds` since last tick — see _dim_edges) because they are keyed by NAME, not by a single column.
TRIGGER_DIMS = ("weather", "fire", "light_band", "cat_at")

# The coordinate set §3.2's scoring reuses for every candidate row, whichever dimension triggered:
# "score by count of OTHER current coordinates that also match (weather, fire, light_band, cat_at
# present/absent, place)". cat_at is compared by presence/absence, not exact place-string equality
# (a candidate whose cat was elsewhere is not a "cat absent" twin of a candidate with no cat at all
# recorded either way; presence/absence is the coarser, honest read of what plan §3.2 asks for).
_MATCH_COORDS = ("weather", "fire", "light_band", "cat_at", "place")

# D-0293 join (J-1430): couriers run just before this module in the same substrate-tick iteration
# (core/orchestrator.py's _substrate_db_work -- J-3305 moved both onto one worker thread, in ONE call:
# `_cour.context_echo() or _cour.sound_echo()` immediately followed by `_felt.on_substrate_tick(...)`, so
# they stay strictly ordered and never overlap), so a matching would-have row's ts sits comfortably under one 5s tick period away
# from `now` — 2.0s leaves headroom for the DB calls in between while staying well short of the
# next tick, so it can't accidentally pair with a DIFFERENT tick's courier row.
SAME_TICK_WINDOW_S = 2.0
# Which felt_recall trigger dimension each courier route's own trigger corresponds to (route A/D
# from core/couriers.py's own docstring) — "same ts" alone would pair any edge with any courier
# fire; this narrows the join to the SAME happening, not just the same tick. "sound:" is a prefix
# match against felt_recall's own "sound:<key>" dim naming (_dim_edges).
_ROUTE_TO_DIM = {"context_echo": "weather", "sound_echo": "sound:"}


def _courier_would_have_fired(now: float, dim: str) -> tuple[bool, str | None]:
    """Best-effort join (D-0293/J-1430): did a courier log a would-have-delivered row for THIS
    happening (route<->dim match, plan §3.1) within this same tick? Reads only the tail of
    data/couriers_log.jsonl — couriers run immediately before this module every tick (see module
    docstring), so a matching row, if any, is always near the end of the file; never imports
    core.couriers. Fail-open: any error or no match returns (False, None)."""
    try:
        if not _COURIER_LOG.exists():
            return False, None
        with open(_COURIER_LOG, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 8192))
            tail = f.read().decode("utf-8", errors="ignore")
        lines = [ln for ln in tail.splitlines() if ln.strip()]
        for line in reversed(lines[-25:]):
            try:
                row = json.loads(line)
            except Exception:
                continue
            if not row.get("would_have_delivered"):
                continue
            if abs(row.get("ts", 0.0) - now) > SAME_TICK_WINDOW_S:
                continue
            want = _ROUTE_TO_DIM.get(row.get("route", ""))
            if want is None:
                continue
            if dim == want or (want.endswith(":") and dim.startswith(want)):
                return True, row.get("fragment_id")
    except Exception as exc:
        logger.debug("[felt_recall] courier join failed (non-fatal): %s", exc)
    return False, None


def _register_dispatcher_line(dim: str, place, now: float) -> dict | None:
    """D-0294 consumer side (job J-1550): register this edge with the Transport Manager and read back
    its verdict, right now, for line_id f"world:{dim}:{place}". Call only for dim in TRIGGER_DIMS
    (non-sound) — sound/life lines are out of scope here, already registered elsewhere under their own
    naming (sound_knowledge.py/couriers.py).

    Called on EVERY edge, regardless of this module's own per-dimension cooldown (`fired` in
    _handle_edge) — observe() must see the world's real edge frequency to grow an honest baseline, not
    one throttled by felt recall's own cooldown (job briefing: "on every edge (value changed)").
    verdict() is read-only and never consumes anything (see its own docstring: it never sets
    novelty_fired=True or *_armed=False the way dispatch_tick() does), so calling it here on every edge
    changes nothing about how dispatch_tick() or any other consumer of transport_manager's state
    behaves. Needs no branching on transport_manager.EDGE_TRIGGER — verdict()'s own candidate list
    already reflects whichever mode is active.

    Returns transport_manager.verdict()'s own dict ({"verdict", "weight", "cold_start"}), or None on
    any failure (missing/unimportable module, disk error, ...) — fail-open, matching every other
    optional enrichment in this module (_courier_would_have_fired is the sibling pattern). The caller
    leaves the ride row's dispatcher_* fields at their None default when this returns None.
    """
    try:
        from core import transport_manager as _tm
    except Exception:
        return None
    try:
        line_id = f"world:{dim}:{place}"
        _tm.observe(line_id, now, 1.0)
        return _tm.verdict(line_id)
    except Exception:
        return None

# In-process only (module-level, not a state file): a restart naturally has no "previous tick" and
# no live cooldown clock, which is correct — Phase 0 is restart-gated, so the defeater clock and the
# habituation clock both properly start fresh at Du's next restart onto this build.
_prev_tuple: dict | None = None
_last_fired: dict[str, float] = {}
_baseline_cache: dict = {"ts": 0.0, "value": None}
_BASELINE_CACHE_S = 3600.0   # "store-wide mean, cache hourly" (job briefing)


def _current_tuple() -> dict:
    """The tick's OWN read of the current experienced tuple — core.geometry_census.peek() (the
    read-only, unrecorded census row; "built by the same readers snapshot() uses") piped through
    core.experienced_tuple.experienced(), exactly the idiom core/lane2.py's gather_percepts() already
    uses for a read-only per-tick tuple. This is deliberately NOT geometry_census.snapshot() — that
    call debounces/logs a real census tuple at each COGNITIVE event and must not be double-called
    (job briefing: "reuse whatever the tick already computes; do not add a second census call")."""
    from core import geometry_census as _gc, experienced_tuple as _xt, sensorium as _sens
    snap = _gc.peek() or {}
    phase = None
    try:
        phase = _sens._daylight()
    except Exception:
        pass
    return _xt.experienced(snap, phase=phase) or {}


def _dim_edges(prev: dict, curr: dict) -> list[tuple[str, object, object]]:
    """Which trigger dimensions actually crossed an edge this tick (plan §3.1: edge, not level — "it
    is *still* thundering" never re-triggers). Returns (dim, prev_value, curr_value) tuples."""
    out: list[tuple[str, object, object]] = []
    for dim in TRIGGER_DIMS:
        pv, cv = prev.get(dim), curr.get(dim)
        if cv == pv:
            continue
        if dim == "fire" and (pv is None or cv is None):
            continue      # a room change (fire unrendered <-> rendered), not a fire transition
        if dim == "light_band" and cv not in ("dark", "dim"):
            continue      # plan §3.1: the trigger is ARRIVING at dark/dim, not leaving it
        if dim == "weather" and cv is None:
            continue
        # cat_at: None->somewhere (arrives) and somewhere->None (leaves) are both real edges here —
        # no extra guard beyond cv != pv.
        out.append((dim, pv, cv))
    # New sound EVENT keys: any key entering `sounds` since last tick. Plan §3.1's own examples
    # ("thunder, morepork, rain_on_roof") include a key soundscape.py classes as a continuous bed
    # (rain_on_roof) elsewhere (couriers.sound_echo's TEXT-echo gate excludes beds so it never
    # narrates something constantly present) — this module deliberately does not import that
    # bed/rate gate: felt recall never speaks, so a bed sound's own ARRIVAL (it just started
    # raining) is still a genuine, once-per-happening world change, and each key's own
    # FELT_RECALL_COOLDOWN_S already stops a habitual, continuously-present sound from re-firing
    # every tick regardless.
    prev_sounds = set(prev.get("sounds") or [])
    curr_sounds = set(curr.get("sounds") or [])
    for key in sorted(curr_sounds - prev_sounds):
        out.append((f"sound:{key}", None, key))
    return out


def _trigger_where(dim: str, value) -> tuple[str, tuple]:
    """The coordinate-keyed WHERE clause for one trigger (plan §3.2). `dim` is always drawn from the
    fixed TRIGGER_DIMS tuple or the 'sound:<key>' shape _dim_edges builds — never external input."""
    if dim.startswith("sound:"):
        key = dim.split(":", 1)[1]
        if SOUND_COORD_MATCH:
            # Widened, never narrowed (J-1574): the left side of the OR is byte-identical to the
            # line below, so every row the old query would have returned still comes back. The right
            # side additionally admits a DIFFERENT key's row that stored its own sound_onset point --
            # _build_prior's own per-row closeness (not this WHERE clause) is what actually judges
            # and, if too far, excludes it; SQLite has no six-axis-distance operator to filter on here.
            return "(sounds LIKE ? OR sound_onset IS NOT NULL)", (f'%"{key}"%',)
        return "sounds LIKE ?", (f'%"{key}"%',)
    if value is None:
        return f"{dim} IS NULL", ()
    return f"{dim} = ?", (value,)


def _coord_match_count(row: sqlite3.Row, curr: dict, coords: list[str]) -> int:
    n = 0
    for c in coords:
        cv = curr.get(c)
        rv = row[c]
        if c == "cat_at":
            if (rv is not None) == (cv is not None):
                n += 1
        elif rv is not None and rv == cv:
            n += 1
    return n


def _sound_closeness(dim_key: str, same_key: bool, sound_onset_json) -> float | None:
    """Trigger-position match strength for a 'sound:<key>' dim once SOUND_COORD_MATCH is True (plan
    sec3.2 upgrade, J-1574). `same_key` is the OLD `sounds LIKE '%"<key>"%'` test, decided by the
    caller against the row's own `sounds` column -- a row that passes it is always a full match (1.0),
    the exact-key guarantee the old code gave every returned row, never narrowed by this addition,
    whatever its own stored coordinate says. A row that only entered the pool via the widened OR
    branch (a different key, or no key at all) counts only if its own stored `sound_onset` point is
    within SOUND_MATCH_RADIUS of the triggering key's own coords() point -- None (the caller drops
    the candidate entirely) if there is no stored point to measure (SOUND_STRING_FIELDS off, a
    pre-J-1534 row, or a column that does not exist yet on a not-yet-restarted DB -- see
    SOUND_COORD_MATCH's own comment) or it is too far. Never fabricates a closeness for a row with
    nothing to measure -- this project's 'an empty answer must be true, not silent' discipline
    (evidence_recall.py's own outcome='unclear' vs 'empty' split), one layer up."""
    if same_key:
        return 1.0
    if not sound_onset_json:
        return None
    try:
        point = json.loads(sound_onset_json)
    except Exception:
        return None
    try:
        from core import soundscape as _snd
        d = _snd.distance_to_point(dim_key, point)
    except Exception:
        return None
    if d is None or d > SOUND_MATCH_RADIUS:
        return None
    return max(0.0, 1.0 - d / SOUND_MATCH_RADIUS)


def _primary_for(valence: float) -> str:
    """Reuse the exact label<->valence convention core.memory.store.emotional_prior() uses
    (_VALENCE_HINT) rather than inventing a second one — nearest label by valence (job briefing:
    "primary via the same _VALENCE_HINT convention store.emotional_prior uses")."""
    try:
        from core.memory.store import _VALENCE_HINT as _hint
    except Exception:
        return "neutral"
    if not _hint:
        return "neutral"
    return min(_hint, key=lambda k: abs(_hint[k] - valence))


def _build_prior(dim: str, value, curr_tuple: dict):
    """Plan §3.2 match + §3.3 dose. Read-only URI connection over fragment_context. Returns
    (AffectivePrior_or_None, n_kept, mean_match_fraction_or_None, kept_fragment_ids).

    kept_fragment_ids (added 2026-09-28, J-1562, golden_spiral_recall.md Phase 2): the SAME kept/
    scored rows' own fragment_ids, in their existing ranked order -- so a caller can hand felt
    recall's own "current recall" top-3 to the Theta shadow ray for comparison without this function
    running its match query twice. Purely additive: every existing field/ordering is unchanged.

    Scoring (matches the plan's own worked example exactly: "thunder+dark+fire-out=3"): every
    candidate already matched the trigger dimension itself (worth 1), plus one more for each OTHER
    coordinate in _MATCH_COORDS it also shares with the current tuple. n_w (job briefing's
    "min(1,n_w/N_MATCH)") is the COUNT of rows kept (breadth of evidence, capped by N_MATCH);
    mean_match_fraction is the mean, over those kept rows, of score/max_possible_score (quality of
    the match) — orthogonal terms, multiplied. This split was not fully spelled out by the plan text
    (it names both quantities but not their exact construction) and is a documented, reasoned choice,
    not an arbitrary one — flagged as such in this job's finding for the Phase 0 read.

    SOUND_COORD_MATCH addendum (J-1574): for a "sound:<key>" dim only, when that flag is True, the
    trigger position's own contribution stops being a flat 1 and becomes _sound_closeness's
    continuous 0..1 score (1.0 for the same key, distance-based for a different one, the candidate
    dropped entirely if that cannot be measured or is too far) — max_score is unchanged (closeness
    still tops out at 1.0, same as the old flat term), so mean_fraction/similarity/the weighted mean
    below all stay on the exact same scale and need no change themselves. Every other dim, and this
    dim with the flag off, is completely untouched (sound_mode below is False in both cases).
    """
    where_sql, params = _trigger_where(dim, value)
    now = time.time()
    sound_mode = dim.startswith("sound:") and SOUND_COORD_MATCH
    select_cols = "weather, fire, light_band, cat_at, place, valence, arousal, tuple_ts"
    if sound_mode:
        select_cols += ", sounds, sound_onset"
    conn = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT fragment_id, {select_cols} "
            f"FROM fragment_context WHERE {where_sql} AND tuple_ts < ? "
            f"AND source NOT LIKE 'census_world%' AND valence IS NOT NULL",
            (*params, now - MIN_AGE_S),
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return None, 0, None, []
    others = [c for c in _MATCH_COORDS if c != dim]
    max_score = 1 + len(others)
    # Tie-break by recency (most-matching first; among equal scores, most-recent first) rather than
    # leaving ties in SQLite's own arbitrary scan order -- verified this matters: with no other
    # coordinates specified, every candidate ties on score, and an unordered top-24 slice landed on
    # an unrepresentative, even sign-flipped, mean valence versus the population (see this job's
    # finding). Not a random sample (couriers.py's context_echo/sound_echo use ORDER BY RANDOM() for
    # a single pick; here we KEEP N_MATCH of them and weight the mean by score, so a deterministic,
    # recency-biased tie-break is the more defensible choice than either arbitrary DB order or reroll
    # on every tick).
    if sound_mode:
        dim_key = dim.split(":", 1)[1]
        needle = f'"{dim_key}"'
        scored_kept = []
        for r in rows:
            same_key = needle in (r["sounds"] or "")
            closeness = _sound_closeness(dim_key, same_key, r["sound_onset"])
            if closeness is None:
                continue   # too far, or nothing stored to measure -- excluded, not guessed
            scored_kept.append((closeness + _coord_match_count(r, curr_tuple, others), r))
        scored = sorted(scored_kept, key=lambda sr: (-sr[0], -sr[1]["tuple_ts"]))
    else:
        scored = sorted(
            ((1 + _coord_match_count(r, curr_tuple, others), r) for r in rows),
            key=lambda sr: (-sr[0], -sr[1]["tuple_ts"]),
        )
    if not scored:
        return None, 0, None, []    # J-3305: was a 3-tuple (every other path returns 4); only reachable with SOUND_COORD_MATCH
    kept = scored[:N_MATCH]
    kept_ids = [r["fragment_id"] for _, r in kept]
    n = len(kept)
    fractions = [s / max_score for s, _ in kept]
    mean_fraction = sum(fractions) / n
    similarity = min(1.0, n / N_MATCH) * mean_fraction
    total_w = sum(s for s, _ in kept) or 1
    valence = sum(s * r["valence"] for s, r in kept) / total_w
    arousal = sum(s * (r["arousal"] if r["arousal"] is not None else 0.5) for s, r in kept) / total_w
    primary = _primary_for(valence)

    from core.schema import AffectivePrior
    prior = AffectivePrior(
        similarity=round(similarity, 3), valence=round(valence, 3), arousal=round(arousal, 3),
        primary=primary, source=f"felt_recall:{dim}", cue=f"{dim}={value} x{n}",
    )
    return prior, n, round(mean_fraction, 3), kept_ids


def _affect_now(affect) -> dict:
    """The felt state AT this tick — read off the real AffectState object when the caller passed one
    (the substrate loop always does), else fall back to core.mood's cache (same freshness/provenance
    core/memory/store.py's own outside-a-node fallback already relies on)."""
    try:
        if affect is not None:
            return {"valence": round(float(affect.valence), 3), "arousal": round(float(affect.arousal), 3)}
    except Exception:
        pass
    try:
        from core import mood as _mood
        v, a = _mood.current_valence(), _mood.current_arousal()
        return {"valence": round(v, 3) if v is not None else None,
                "arousal": round(a, 3) if a is not None else None}
    except Exception:
        return {"valence": None, "arousal": None}


def _get_baseline_valence() -> float | None:
    """Store-wide mean valence, cached hourly (job briefing)."""
    now = time.time()
    if _baseline_cache["value"] is not None and (now - _baseline_cache["ts"]) < _BASELINE_CACHE_S:
        return _baseline_cache["value"]
    val = None
    try:
        conn = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT AVG(valence) FROM fragment_context WHERE valence IS NOT NULL "
                "AND source NOT LIKE 'census_world%'"
            ).fetchone()
            val = round(row[0], 4) if row and row[0] is not None else None
        finally:
            conn.close()
    except Exception:
        val = None
    _baseline_cache["ts"] = now
    _baseline_cache["value"] = val
    return val


def _log_row(row: dict) -> None:
    try:
        _SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_SHADOW_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _handle_edge(dim: str, prev_value, curr_value, curr_tuple: dict, affect, now: float,
                 collector: list | None = None) -> dict:
    """One trigger, evaluated once (job briefing: "Log EVERY evaluated trigger (fired or not)").
    `fired` = the per-dimension cooldown had elapsed, so the match+dose actually ran; on cooldown,
    the edge is still logged (value/prev_value/affect_now/baseline_valence real) but the match query
    is skipped — a chattering key (a persistent gull, a held-open door) still costs one row per edge,
    never one SQL query per edge.

    `collector` (J-2462): when the tick loop passes a list, a built prior is appended to it as
    (dim, prior, row) INSTEAD of being applied here -- on_substrate_tick combines the tick's priors
    and applies one. With no collector (standalone calls, the pre-J-2462 tests) the old per-edge
    apply path runs unchanged."""
    fired = (now - _last_fired.get(dim, 0.0)) >= FELT_RECALL_COOLDOWN_S
    row: dict = {
        "ts": round(now, 1),
        "stop": "substrate_tick",
        "line": f"felt_recall:{dim}",
        "dose": "cup",
        "dim": dim,
        "value": curr_value,
        "prev_value": prev_value,
        "fired": fired,
        "gate_used": GATE_USED,
        "n_match": None,
        "match_fraction_mean": None,
        "valence_lean": None,
        "arousal_lean": None,
        "primary": None,
        "applied": False,
        "affect_now": _affect_now(affect),
        "baseline_valence": _get_baseline_valence(),
    }
    if not fired:
        return row
    _last_fired[dim] = now
    try:
        prior, n_match, mean_fraction, kept_ids = _build_prior(dim, curr_value, curr_tuple)
    except Exception as exc:
        logger.debug("[felt_recall] match failed for %s (non-fatal): %s", dim, exc)
        prior, n_match, mean_fraction, kept_ids = None, 0, None, []
    row["n_match"] = n_match
    row["match_fraction_mean"] = mean_fraction
    if FELT_RECALL_LOG_MATCHED_IDS:
        row["matched_ids"] = [i for i in (kept_ids or [])[:MATCHED_IDS_CAP] if i]
    if prior is not None:
        row["valence_lean"] = prior.valence
        row["arousal_lean"] = prior.arousal
        row["primary"] = prior.primary
        if collector is not None:
            collector.append((dim, prior, row))      # J-2462: the tick applies one combined prior
        elif FELT_RECALL_LIVE and affect is not None:
            try:
                affect.apply_prior(prior)
                row["applied"] = True
            except Exception as exc:
                logger.debug("[felt_recall] apply_prior failed (non-fatal): %s", exc)
    # GOLDEN SPIRAL / T-0072 Phase 2 (2026-09-28, J-1562, docs/staged/golden_spiral_recall.md §3): cast
    # the phase ray at this SAME trigger and log it to the theta shadow log -- observe-only, nothing
    # rides on the result, never raises into the tick. Runs only when `fired` (this point in the
    # function), matching the moment felt recall's OWN "current recall" (kept_ids, above) actually
    # exists to compare against -- a cooldown-skipped edge has no current recall to diff the ray
    # against, so it is not a "felt-recall trigger" in the sense this comparison needs.
    try:
        from core import theta_shadow as _theta
        _theta.log_ray(f"felt_recall:{dim}", kept_ids[:3], now_ts=now)
    except Exception as exc:
        logger.debug("[felt_recall] theta shadow failed (non-fatal): %s", exc)
    return row


def _combine_priors(fires: list):
    """J-2462: ONE prior for the tick from every fired edge's prior. `fires` = [(dim, prior, row)].

    Rule: valence and arousal are the mean of the per-edge priors weighted by each prior's own
    `similarity` (its match strength -- an edge that matched 24 close moments outweighs one that
    matched 3 loose ones; equal weights if every similarity is 0 or missing); the combined
    `similarity` is the MAX over the edges, never the sum, so apply_prior's own
    w = AFFECT_PRIOR_MAX_NUDGE x similarity stays capped at what ONE edge could have done -- a
    happening that enters 11 sound keys is one happening, and its tug is bounded like one.
    `primary` is re-derived from the combined valence via the same _VALENCE_HINT convention each
    edge used. Alias keys that built identical priors (kereru_wingbeats == wood_pigeon, ...) collapse
    to the same point under the mean, as they should. A single fire is returned as-is -- the exact
    object the edge built -- so a one-edge tick is byte-identical to the pre-J-2462 behaviour."""
    if len(fires) == 1:
        return fires[0][1]
    priors = [p for _, p, _ in fires]
    sims = [max(0.0, float(getattr(p, "similarity", 0.0) or 0.0)) for p in priors]
    total = sum(sims)
    weights = sims if total > 0 else [1.0] * len(priors)
    total = sum(weights)
    valence = sum(w * float(p.valence) for w, p in zip(weights, priors)) / total
    arousal = sum(w * float(p.arousal) for w, p in zip(weights, priors)) / total
    from core.schema import AffectivePrior
    dims = [d for d, _, _ in fires]
    return AffectivePrior(
        similarity=round(max(sims), 3), valence=round(valence, 3), arousal=round(arousal, 3),
        primary=_primary_for(valence), source="felt_recall:tick",
        cue=f"tick x{len(fires)}: " + "+".join(dims),
    )


def _tick_row(fires: list, prior, affect, now: float) -> dict:
    """The per-tick summary row (new row kind, J-2462): what the tick WOULD apply (Phase 0) or DID
    apply (Phase 1) as one prior. dim="tick" so readers grouping by dim see it as the summary."""
    return {
        "ts": round(now, 1),
        "stop": "substrate_tick",
        "line": "felt_recall:tick",
        "dose": "cup",
        "kind": "tick",
        "dim": "tick",
        "value": None,
        "prev_value": None,
        "fired": True,
        "gate_used": GATE_USED,
        "tick_fires": len(fires),
        "dims": [d for d, _, _ in fires],
        "n_match": None,
        "match_fraction_mean": None,
        "valence_lean": prior.valence,
        "arousal_lean": prior.arousal,
        "similarity": getattr(prior, "similarity", None),
        "primary": prior.primary,
        "applied": False,
        "affect_now": _affect_now(affect),
        "baseline_valence": _get_baseline_valence(),
    }


def on_substrate_tick(affect=None) -> None:
    """Call once per substrate tick (core/orchestrator.py start_background._substrate_loop, next to
    the couriers). `affect` is the live CarriedAffect (self.state.affect) — passed through now so
    Phase 1 needs no further wiring change, only FELT_RECALL_LIVE flipped. Fail-open: must never
    raise into the tick; no LLM; no embedding.

    J-2462: edge rows are built in the loop, the tick's priors are combined into ONE and applied
    once (FELT_RECALL_LIVE only), then the edge rows are logged in edge order followed by one
    kind="tick" row -- see the module docstring's ONE TUG PER TICK paragraph."""
    global _prev_tuple
    try:
        curr = _current_tuple()
    except Exception as exc:
        logger.debug("[felt_recall] current-tuple read failed (non-fatal): %s", exc)
        return
    if not curr:
        return   # this tick's read failed outright -- skip silently, keep the last known-good tuple
    prev = _prev_tuple
    _prev_tuple = curr
    if not prev:
        return   # first good tick since (re)start -- nothing to diff against yet
    now = time.time()
    try:
        edges = _dim_edges(prev, curr)
    except Exception as exc:
        logger.debug("[felt_recall] edge detection failed (non-fatal): %s", exc)
        return
    fires: list = []      # J-2462: (dim, prior, row) for every edge that built a prior this tick
    rows: list = []       # J-2462: edge rows, logged after the tick's one apply (edge order kept)
    for dim, pv, cv in edges:
        try:
            row = _handle_edge(dim, pv, cv, curr, affect, now, collector=fires)
            # D-0293 join (J-1430): additive fields, always present so the shadow log's schema
            # stays stable whether or not a courier fired.
            row["courier_would_have_fired"] = False
            row["courier_fragment_id"] = None
            try:
                fired, frag_id = _courier_would_have_fired(now, dim)
                row["courier_would_have_fired"] = fired
                row["courier_fragment_id"] = frag_id
            except Exception:
                pass
            # D-0294 dispatcher join (J-1433/J-1550): additive fields, always present (same schema-
            # stability reasoning as the courier fields above). Non-sound TRIGGER_DIMS only — sound/
            # life lines already flow through transport_manager.observe() elsewhere (out of scope
            # here); a "sound:<key>" edge leaves these at their None default. Runs on every edge
            # regardless of `fired` above (see _register_dispatcher_line's own docstring for why).
            row["dispatcher_verdict"] = None
            row["dispatcher_cold_start"] = None
            row["dispatcher_weight"] = None
            if dim in TRIGGER_DIMS:
                try:
                    v = _register_dispatcher_line(dim, curr.get("place"), now)
                    if v is not None:
                        row["dispatcher_verdict"] = v.get("verdict")
                        row["dispatcher_cold_start"] = v.get("cold_start")
                        row["dispatcher_weight"] = v.get("weight")
                except Exception:
                    pass
            rows.append(row)
        except Exception as exc:
            logger.debug("[felt_recall] edge handling failed for %s (non-fatal): %s", dim, exc)
            continue
    # J-2462: ONE tug per tick. Combine every fired edge's prior, apply once (Phase 1 only), mark
    # a sole fire's own edge row `applied` (byte-identical to the per-edge path it replaces), then
    # log the edge rows in edge order followed by the tick row.
    tick_row = None
    if fires:
        try:
            prior = _combine_priors(fires)
            # A sole fire's edge row is its own would-apply: no tick row, log byte-identical to before.
            tick_row = _tick_row(fires, prior, affect, now) if len(fires) >= 2 else None
            if FELT_RECALL_LIVE and affect is not None:
                try:
                    affect.apply_prior(prior)
                    if tick_row is not None:
                        tick_row["applied"] = True
                    if len(fires) == 1:
                        fires[0][2]["applied"] = True
                except Exception as exc:
                    logger.debug("[felt_recall] apply_prior failed (non-fatal): %s", exc)
        except Exception as exc:
            logger.debug("[felt_recall] tick combine failed (non-fatal): %s", exc)
            tick_row = None
    for row in rows:
        _log_row(row)
    if tick_row is not None:
        _log_row(tick_row)


def status() -> dict:
    """For the HUD/pulse and the >=7-day Phase 0 read (plan §8): per-dimension edge/fire counts and
    mean lean, straight off the shadow log. Read-only."""
    try:
        rows = [json.loads(l) for l in _SHADOW_LOG.read_text(encoding="utf-8").splitlines() if l.strip()] \
            if _SHADOW_LOG.exists() else []
    except Exception:
        rows = []
    if not rows:
        return {"rows": 0, "live": FELT_RECALL_LIVE}
    from collections import defaultdict
    by_dim: dict = defaultdict(lambda: {"edges": 0, "fired": 0, "n_match_sum": 0, "valence_lean_sum": 0.0, "valence_lean_n": 0})
    tick_rows = 0
    for r in rows:
        if r.get("kind") == "tick":          # J-2462: per-tick summary, not a trigger dimension
            tick_rows += 1
            continue
        d = by_dim[r.get("dim", "?")]
        d["edges"] += 1
        if r.get("fired"):
            d["fired"] += 1
        if r.get("n_match"):
            d["n_match_sum"] += r["n_match"]
        if r.get("valence_lean") is not None:
            d["valence_lean_sum"] += r["valence_lean"]
            d["valence_lean_n"] += 1
    span_hr = round((rows[-1]["ts"] - rows[0]["ts"]) / 3600, 2) if len(rows) > 1 else 0.0
    return {
        "rows": len(rows), "live": FELT_RECALL_LIVE, "span_hr": span_hr, "tick_rows": tick_rows,
        "by_dim": {
            k: {"edges": v["edges"], "fired": v["fired"],
                "mean_n_match": round(v["n_match_sum"] / v["fired"], 2) if v["fired"] else None,
                "mean_valence_lean": round(v["valence_lean_sum"] / v["valence_lean_n"], 3) if v["valence_lean_n"] else None}
            for k, v in by_dim.items()
        },
    }
