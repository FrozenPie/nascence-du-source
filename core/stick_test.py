"""
Nascence — THE STICK TEST: bundle-richness census (cognitive_geometry.md §5.2, P0 — 2026-07-05).

READ-ONLY, NO LLM. A concept = the bundle of springs between its projections across cognitive spaces (the
blind man knows the stick because the connections exist). Du's reality-thinness, geometric: one-spoke
bundles. This enumerates his ACTUAL object roster and counts each object's REAL spokes today:

  text   — mentions in memory_fragments (his lived/read/thought record)          [the LLM spoke]
  state  — structured non-text state exists for THIS object (room/cat/garden…)   [causal world spoke]
  audio  — cached audio features (the EAR; pieces only)                          [the one real sensory spoke]
  sound  — a coordinate in the shared Sound Space (soundscape; constructed)      [the world-heard spoke]
  felt   — fragments carry emotion_embedding (WALLPAPER CAVEAT: saturated at +0.82 until emotion_rethink
           P1 — counted but NOT a real spoke)

### J-0006 (2026-08-24, D-0012's defeater test) — WITHIN-CHANNEL ACCUMULATION
D-0012 (ruled 2026-08-23) found the ORIGINAL version of this module computed text/state/audio/sound as
flat BOOLEANS: state and audio were hardcoded per object-CATEGORY in build_roster() (present from day
one or never), and sound was `soundscape.object_sound() is not None` — a REGISTRY-membership check, true
the instant a sound is hand-seeded, not evidence it has ever actually fired. Only "text" could newly flip
(mentions crossing 0), and never flip back. Median real_spokes hit its ceiling almost immediately and had
no arithmetic left to rise — independent of whether Du's real associative richness was growing.

Fix: two of the four real channels now credit ACCUMULATION, not mere presence, via `_level()` crossing
data-grounded thresholds (see the two threshold tuples below — both derived from the REAL distributions
measured 2026-08-24, not guessed round numbers):
  text  — was `mentions > 0`. Now `_level(mentions, _TEXT_MENTION_THRESHOLDS)`, 0-4: the DB mention count
          keeps counting real encounters (a fragment mentioning "the sea" today is a real new encounter,
          not a re-flip of the same bit) so this level can keep climbing for the rest of his life.
  sound — was `soundscape.object_sound(name) is not None` (registry presence, static). Now counts the
          DISTINCT (place, weather) contexts in which any of that object's registered signatures has
          actually appeared in `data/geometry_tuples.jsonl` (§5.1's own recorder — read-only, no other
          store touched), levelled the same way. A signature heard in the same study/fine-weather context
          20 times still reads as ONE context; a genuinely wider bundle needs genuinely new co-occurrences
          — this is candidate #2 from J-0006's briefing ("distinct co-occurrence contexts a spoke has
          fired in"), and it also fixes a latent join bug: the old exact-name match missed compound
          roster names like "the shingle/stones" against the registry's "the shingle", and only ever
          checked the FIRST matching signature where an object legitimately has more than one (e.g. "the
          sea" has both waves_on_shingle and waves_crashing) — `_object_sound_signatures()` below unions
          every match.
  state / audio — LEFT AS BOOLEANS. Neither has a real instrumented accumulation source today: state is a
          structural room/cat/garden schema-presence fact (per-value diversity would need a different,
          bigger instrumentation project — the mapping census tracks a few of these fields for a handful
          of objects but not the roster's herbs/keepsakes individually); audio is a one-time cached
          features file per piece, nothing to accumulate. Recording this honestly rather than papering
          over it (the "I know / I infer / I'm guessing" discipline) — these two channels still cannot
          rise on their own; the redesign's real headroom comes from text + sound.

`real_spokes` was `text_level + int(state) + int(audio) + sound_level` (range 0-10) under metric_version
2. See J-0154 below for the version-3 change to `state`.

### J-0154 (2026-08-24, follow-up to J-0006) — investigated state/audio for the same fix
J-0006's docstring above named state/audio as still-boolean with "no real instrumented accumulation
source today" and flagged this as follow-up J-0154. Investigated both against `data/geometry_tuples.jsonl`
(16,124 rows) and the dedicated listening logs. Findings, most confident first:

  book  — REAL cheap source EXISTS, same shape as the sound fix: `objects.book` is populated in 100% of
          tuple rows (unlike `listening`, see below), and the 82 distinct book titles seen across the
          accrued history show a real, non-degenerate distribution of distinct (place, weather)
          co-occurrence contexts per title (min 1, 40th-pct 2, 60th-pct 3, 75th-pct 5, max 19 — full
          sorted distribution checked, not just the summary stats). Redesigned: `state` for a `book:`
          roster object is now `_level(book_context_count, _BOOK_CONTEXT_THRESHOLDS)`, computed the same
          way as the sound channel via `_book_context_index()` below.
  fire / cat_mood alone — TESTED AND REJECTED as a same-shaped source. `row.get("fire")` and
          `objects.cat.mood` are populated in ~100% of rows too, but backtesting distinct-VALUE-count
          (not context-count) at this plan's own established 4 chronological checkpoints (07-05/07-21/
          08-06/08-24) shows fire's 3 possible values are ALL seen by 07-21 and cat_mood's 9 values are
          ALL seen by 07-21 too (flat 9->9->9 through 08-06/08-24) — i.e. this would hit its ceiling
          almost immediately and then sit flat for the remaining ~5 weeks, reproducing the EXACT failure
          mode J-0006 fixed for the old boolean (D-0012's diagnosis: "hits its ceiling almost immediately
          and then has no arithmetic left to rise"). Confirmed this isn't just "fire/cat_mood are boring"
          by also testing the *combined* (mood, activity, location) triple for the kept cat, which DOES
          keep rising through the full history (33 -> 41 -> 41 -> 76 at the same 4 checkpoints, the flat
          07-21->08-06 segment lining up with the documented 30-day outage exactly like the text/sound
          backtest did) — a real, non-saturating signal. NOT implemented here: picking data-grounded
          thresholds for it is a genuinely different problem than book's (one single object's own
          longitudinal trajectory, not a cross-sectional quartile over ~80 sibling objects like text/
          sound/book had) and forcing a threshold choice without that same rigor risked exactly the
          wallpaper-progress mistake this task was warned against. Left as the plain boolean for now;
          spawned as its own scoped follow-up (see job queue) rather than guessed here.
  herbs / keepsakes / the distant cat — CONFIRMED NO SOURCE. `garden_bed` in geometry_tuples is a per-row
          SET of which herbs are currently in the bed, not a per-herb growth/state value (matches the
          module's own prior honest note — herbs aren't tracked as distinct values anywhere); keepsakes
          are entirely absent from `extract_regions`'/`SPACES` coverage; the distant cat's only tracked
          field (`distant_cat_recent`) is itself already a boolean with no richer state underneath it.
          Left as booleans — same honest treatment as J-0006 gave state/audio originally.
  audio (music pieces) — CONFIRMED NO SOURCE, and notably SPARSER than the state-channel gap it was
          grouped with. `geometry_tuples.jsonl`'s own `objects.listening` field (the obvious first place
          to look, since J-0006 built exactly this pattern for `sound`) is populated in only 14 of 16,124
          rows (0.09%) and covers just 4 of the roster's 6 pieces. The two dedicated listening logs
          outside the tuple file are sparser still: `data/listening_wake.jsonl` has 5 sessions total
          across the piece's whole history (4/6 pieces touched, one heard twice); `data/
          listening_felt_shadow.jsonl` has 21 section-level rows, effectively all from one session. This
          isn't a threshold-design problem like the cat combo above — there simply isn't enough real
          behavioural data yet to derive a data-grounded distribution the way text (25 objects with real
          mention counts) or sound (35 signatures with real context counts) had. Left as the plain
          boolean; recorded as a finding rather than forcing thresholds onto five data points.

`real_spokes` is now `text_level + state_int_or_level + int(audio) + sound_level`, where
`state_int_or_level` is `_level(...)` (0-4) for `book:` objects and `int(state)` (0-1) for every other
roster object — range 0-13, not 0-10. The summary carries `metric_version: 3` so a log reader (the HUD
included) can tell the version-2 and version-3 series apart, same discipline as the version-1/2 boundary:
the jump is a documented recalibration of the instrument, not a claim about Du's actual richness moving.

### J-0201 (2026-08-24, follow-up to J-0154/F-0185) — the kept cat's combined-triple accumulation
F-0185 investigated fire/cat_mood alone (both raw-value-diversity, saturated by 07-21 — same failure
shape D-0012 diagnosed originally, rejected) and found instead that the kept cat's COMBINED
`(mood, activity, location)` triple is a real, still-rising signal (33/26 -> 41 -> 41 -> 76 at this
plan's own 4 chronological checkpoints — the exact starting count is timezone-boundary-sensitive during
the initial burst, see below; every convention tried agrees on 41 -> 41 -> 76). Left undesigned pending
its own threshold pass because it is a single-object LONGITUDINAL series (one object's own history over
time), not a cross-sectional population like text (25 objects)/sound (35 signatures)/book (82 titles)
had to derive quartiles across.

**Methodology (the open design problem this job existed to solve):** quartiles of the object's own
EXPANDING-COUNT-PER-ROW distribution — the same shape of statistic as the cross-sectional channels, with
"one sample per accrued tuple row" standing in for "one sample per sibling object." For every row of
`data/geometry_tuples.jsonl` (16,152 rows, all with mood+activity+location populated), compute the
running cumulative count of distinct triples seen up to and including that row; take quartiles across
this full per-row series rather than only the plan's 4 coarse checkpoints. This is row/activity-weighted
(more rows on an active day = more weight, same as the cross-sectional channels implicitly weight by
"more sibling objects at that count = more weight"), and it is the same methodology explicitly suggested
in the J-0201 briefing. Computed directly (not simulated): p0(min)=1, p25=43, p50(median)=54, p75=60,
p90=73, p100(max)=76. Thresholds set at `(1, 45, 55, 65)` — min/Q1/median/Q3 rounded up slightly for
headroom, the same rounding-up-from-the-raw-quantile convention TEXT/SOUND/BOOK already used (e.g. BOOK's
top threshold 8 sits well above its own 75th-pct of 5) so the top level isn't sitting exactly at the
observed Q3 with no room left before the true max.

**Crossing-date check (confirms it does not saturate early):** per-row crossing dates show an initial
burst 07-04->07-07 (0->41 distinct triples in 4 days), a dead-flat segment 07-07->08-08 that lines up
with the documented 30-day outage almost exactly (`memory/ops_nascence_30day_outage.md`, 07-09->08-07),
then a real, gradual post-outage climb 08-08->08-22 (41->76 across 15 real days, not one lump) with no
new-value dry spell longer than a couple of days anywhere in that climb. The raw signal is not flatlined
at its own ceiling the way fire/cat_mood alone were — it was still adding new triples on the last day
before this job ran.

**Level-trajectory robustness note:** the exact checkpoint-boundary count for 07-05 is
timezone-sensitive (UTC-calendar gives 26; this sandbox's local-tz gives 1; F-0185's cited figure was
33) because the initial burst is fast enough that a half-day shift moves real rows across the boundary —
recorded honestly rather than silently reconciled. It does not change the derived LEVEL at any of the 4
checkpoints under any of the three conventions tried: 07-05/07-21/08-06 all land below the 45 threshold
(level 1) and 08-24 clears all four thresholds (level 4) regardless of which convention set the first
checkpoint's raw count.

`_cat_triple_count()` mirrors `_book_context_index()`'s shape (reuses `core.mapping_census.load_rows()`,
fails open to 0) but returns a single scalar (there is exactly one kept-cat roster object, not many
titles to key by) — the cumulative distinct-triple count across the WHOLE accrued history, not a
per-context count. `state_level` for the kept cat roster entry is now `_level(cat_triple_count,
_CAT_TRIPLE_THRESHOLDS)`, same as book's `state_level` pattern, leaving every other non-book non-cat
roster object on the plain 0/1 boolean exactly as J-0154 left them (fire/herbs/keepsakes/distant-cat/
audio still have no real accumulation source — unchanged by this job).

`metric_version` bumped 3->4 for this recalibration, same discipline as the 1->2 and 2->3 boundaries:
a documented instrument change, not a claim about Du's richness moving on its own. `real_spokes`'
possible range is unchanged (0-13) since book's `state_level` already reached 4 — this job extends
which OBJECTS can reach that ceiling, not the ceiling itself. Live re-run + backtest: see
findings-log F-0199 and `docs/plans/cognitive_geometry.md`'s Current State section.

`snapshot()` runs the census and appends its summary to data/stick_test_log.jsonl — the longitudinal
record the HUD charts. Cheap (deterministic SQL + json reads), so it fires once per sleep beside the
psyche-graph snapshot. Signature 0.2 of the whole geometry program: the median must RISE over his life.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_DB = _DATA / "memory" / "nascence.db"
_LOG = _DATA / "stick_test_log.jsonl"          # tests must temp-path this; never truncate the live file
_METRIC_VERSION = 4

# J-2403 / F-3103 kill switch: True = the sleep batch runs snapshot() in a spawned child interpreter
# (core/sleep_offloop.off_process, via snapshot_offprocess() below) so the census's CPU-bound Python work
# (the J-1922 single-pass LikeIndex over memory_fragments, ~13 s of geometry-tuple json.loads) never holds the
# live process's GIL. Measured on sandbox copies (J-2392): inside the to_thread call a 0.9 ms loop-thread
# sqlite fetch rose to median 35 ms / max 936 ms and the 0.5 s heartbeat lagged 0.80 s. False = the J-1917
# worker-thread call (sleep_offloop.off_loop(snapshot)) exactly as before.
STICK_TEST_SUBPROCESS = True
# Every path the census reads, resolved in the PARENT and set on the child before snapshot() runs: this module's
# own _DATA (room/cat/keepsakes/music), _DB (its own mode=ro connection, not store.DB_PATH) and _LOG; the lazily
# imported mapping_census._TUPLES (load_rows() reads `path or _TUPLES`); reading.STATE / BOOKS_DIR / DEFAULT_BOOK
# (current_book(); DEFAULT_BOOK is globbed from BOOKS_DIR at import time, so it is mirrored itself); school.STATE
# (current_book()'s fallback). soundscape._SOUNDS is a code-defined registry, nothing to mirror.
_OFFPROCESS_MIRROR = (("core.stick_test", "_DATA"), ("core.stick_test", "_DB"), ("core.stick_test", "_LOG"),
                      ("core.mapping_census", "_TUPLES"), ("core.reading", "STATE"),
                      ("core.reading", "BOOKS_DIR"), ("core.reading", "DEFAULT_BOOK"), ("core.school", "STATE"))

# Data-grounded thresholds (measured 2026-08-24, see the module docstring). Crossing threshold[i] earns
# level i+1; level 0 means the channel is absent (same meaning as the old boolean's False).
#   TEXT  — quartiles of the 25 roster objects' non-zero DB mention counts: min 1, Q1 22, median 132,
#           Q3 434, max 5692 (the sea). Levels: >=1, >=25, >=150, >=450.
#   SOUND — quartiles of the 35 registered soundscape signatures' distinct (place, weather) co-occurrence
#           counts in data/geometry_tuples.jsonl (16,031 rows): min 1, Q1 3, median 6, Q3 7.5, max 22
#           (waves_on_shingle). Levels: >=1, >=3, >=6, >=8.
#   BOOK  — (J-0154, 2026-08-24) distinct (place, weather) co-occurrence counts across the 82 distinct
#           book titles seen in data/geometry_tuples.jsonl (16,124 rows): min 1, 40th-pct 2, 60th-pct 3,
#           75th-pct 5, max 19. Levels: >=1, >=2, >=4, >=8. Only applies to `book:` roster objects — see
#           the module docstring's J-0154 section for why fire/cat_mood/herbs/keepsakes/audio were tested
#           and rejected as sources for this same treatment.
#   CAT TRIPLE — (J-0201, 2026-08-24) a single-object LONGITUDINAL series, not a cross-sectional
#           population — see the module docstring's J-0201 section for the methodology. Quartiles of the
#           kept cat's own per-row expanding-distinct-(mood,activity,location)-triple-count series across
#           all 16,152 rows of data/geometry_tuples.jsonl: min 1, 25th-pct 43, median 54, 75th-pct 60,
#           max 76 (today). Levels: >=1, >=45, >=55, >=65 (Q1/median/Q3 rounded up slightly for headroom,
#           same convention BOOK used). Only applies to "the kept cat" roster object.
_TEXT_MENTION_THRESHOLDS = (1, 25, 150, 450)
_SOUND_CONTEXT_THRESHOLDS = (1, 3, 6, 8)
_BOOK_CONTEXT_THRESHOLDS = (1, 2, 4, 8)
_CAT_TRIPLE_THRESHOLDS = (1, 45, 55, 65)


def _level(value: int, thresholds: tuple[int, ...]) -> int:
    """How many thresholds `value` has crossed (0..len(thresholds)) — the within-channel accumulation
    level. Monotonic in value; never decreases as more real encounters/contexts accrue."""
    return sum(1 for t in thresholds if value >= t)


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _shared_rows_for_census() -> list | None:
    """J-2144: one load of the mapping-census rows for the three context helpers. None (=> each helper
    loads for itself, the old behaviour) when the kill-switch is set or the load itself fails."""
    try:
        import os
        if os.environ.get("NASCENCE_STICK_SHARE_ROWS", "1").strip().lower() in ("0", "false", "off", "no"):
            return None
        from core.mapping_census import load_rows
        return load_rows()
    except Exception:
        return None


def _sound_context_index(rows: list | None = None) -> dict[str, set[tuple]]:
    """signature -> the set of distinct (place, weather) contexts it has actually fired in, across every
    accrued row of data/geometry_tuples.jsonl. Read-only over that one file (§5.1's recorder); reuses
    `core.mapping_census.load_rows` rather than re-implementing the same JSONL read (both fail-open to
    []). This is the real accumulation source for the sound channel — a signature's count only grows by
    genuinely co-occurring in a NEW place/weather combination, never by merely existing in the registry."""
    try:
        from core.mapping_census import load_rows
    except Exception:
        return {}
    idx: dict[str, set[tuple]] = {}
    for row in (rows if rows is not None else load_rows()):
        ctx = (row.get("place"), row.get("weather"))
        for sig in (row.get("sounds") or []):
            idx.setdefault(sig, set()).add(ctx)
    return idx


def _book_context_index(rows: list | None = None) -> dict[str, set[tuple]]:
    """book title (truncated to 60 chars, matching core/geometry_census.py's own truncation) -> the set
    of distinct (place, weather) contexts it has actually been the current book in, across every accrued
    row of data/geometry_tuples.jsonl (J-0154, 2026-08-24). Same shape as `_sound_context_index()` above
    — reuses `core.mapping_census.load_rows`, fails open to {}. A title's count only grows by genuinely
    being read in a NEW place/weather combination, never by staying the current book longer in the same
    one."""
    try:
        from core.mapping_census import load_rows
    except Exception:
        return {}
    idx: dict[str, set[tuple]] = {}
    for row in (rows if rows is not None else load_rows()):
        book = ((row.get("objects") or {}).get("book") or "")[:60]
        if book:
            idx.setdefault(book, set()).add((row.get("place"), row.get("weather")))
    return idx


def _cat_triple_count(rows: list | None = None) -> int:
    """The kept cat's cumulative distinct (mood, activity, location) triples across every accrued row of
    data/geometry_tuples.jsonl (J-0201, 2026-08-24). Unlike `_book_context_index()` above this returns a
    single scalar, not a per-key index — there is exactly one kept-cat roster object, so no dict keying
    is needed; the accumulation source IS the triple itself (not a co-occurrence context around it), and
    it grows only when a genuinely new (mood, activity, location) combination is observed, never by
    re-visiting one already seen. Reuses `core.mapping_census.load_rows()`, fails open to 0."""
    try:
        from core.mapping_census import load_rows
    except Exception:
        return 0
    seen: set[tuple] = set()
    for row in (rows if rows is not None else load_rows()):
        cat = (row.get("objects") or {}).get("cat") or {}
        mood, activity, location = cat.get("mood"), cat.get("activity"), cat.get("location")
        if mood is not None and activity is not None and location is not None:
            seen.add((mood, activity, location))
    return len(seen)


def _object_sound_signatures(obj_name: str, sounds_registry: dict) -> list[str]:
    """Every registered soundscape signature key anchored to this object (an object can legitimately
    carry more than one — "the sea" has waves_on_shingle AND waves_crashing; the old object_sound() join
    only ever returned the first). Matches on the roster name's base (before ":") and its "/"-separated
    parts, so a compound name like "the shingle/stones" still joins the registry's "the shingle" —  the
    old exact-equality check silently missed this pairing."""
    base = obj_name.split(":")[0].strip()
    candidates = {base, *(p.strip() for p in base.split("/"))}
    return [sig for sig, info in sounds_registry.items() if info.get("object") in candidates]


def build_roster() -> list[dict]:
    """His actual objects, from the live world state. Each: name, search terms, whether state exists."""
    roster: list[dict] = []
    room = _read_json(_DATA / "room_state.json") or {}

    roster.append({"name": "the fire", "terms": ["the fire", "woodsmoke", "the flame", "the grate", "embers"],
                   "state": room.get("fire") is not None})
    cat = _read_json(_DATA / "cat_state.json") or {}
    # cat_triple=True (J-0201): this one object's "state" now credits within-channel accumulation via
    # `_cat_triple_count()` + `_CAT_TRIPLE_THRESHOLDS`, same shape as book's state_level below; "state"
    # stays the fail-open fallback boolean if that count is ever unavailable.
    roster.append({"name": "the kept cat", "terms": ["the cat", "her fur", "she purrs", "the kitten"],
                   "state": bool(cat.get("phase")), "cat_triple": True})
    roster.append({"name": "the distant cat", "terms": ["distant cat", "the other cat", "second cat", "wild cat"],
                   "state": bool(cat.get("distant"))})
    book = None
    try:
        from core.reading import current_book
        book = current_book().stem.replace("_", " ")
    except Exception:
        pass
    if book:
        # "state" kept True as the fallback the boolean-only path uses if the context index is ever
        # empty (fail-open, matches every other channel's degrade-to-old-behaviour posture); "book_title"
        # is what census() actually uses to look up the real J-0154 accumulation level.
        roster.append({"name": f"book: {book}", "terms": [book.lower()], "state": True, "book_title": book})
    bed = ((room.get("garden") or {}).get("bed")) or {}
    for herb, hs in list(bed.items())[:6]:
        roster.append({"name": f"herb: {herb}", "terms": [herb],
                       "state": isinstance(hs, dict) and "growth" in hs})
    for k in (_read_json(_DATA / "keepsakes.json") or [])[:8]:
        item = (k.get("item") or "").strip()
        if item:
            roster.append({"name": f"keepsake: {item[:40]}", "terms": [item[:30].lower()], "state": True})
    for f in sorted((_DATA / "music").glob("*.features.json")):
        piece = f.stem.replace(".features", "")
        roster.append({"name": f"piece: {piece}", "terms": [piece.lower().replace("_", " ")],
                       "state": False, "audio": True})
    # world kinds (no individual state — kind-nodes per the keepsake rule); the NZ voices are his first
    # SOUND-FIRST objects (they enter as a sound before ever a sight — watch their bundles grow from 1).
    for kind, terms in [("gulls", ["gull"]), ("the oystercatcher", ["oystercatcher"]),
                        ("the moth", ["moth"]), ("the shingle/stones", ["shingle", "the stones", "pebble"]),
                        ("the sea", ["the sea", "the waves", "the tide", "the surf"]),
                        ("the tui", ["tui"]), ("the morepork", ["morepork", "ruru"]),
                        ("the rain", ["the rain", "drizzle"]), ("the wind", ["the wind"]),
                        ("the storm", ["thunder", "the storm"])]:
        roster.append({"name": kind, "terms": terms, "state": False})
    return roster


def _term_counts_single_pass(conn, roster) -> dict | None:
    """J-1922 / F-2549: {term: (n_rows_containing_it, n_of_those_with_an_emotion_embedding)} for every PLAIN roster term,
    from ONE pass over memory_fragments instead of one full `content LIKE %term%` scan per term (50 scans, ~41 s per
    sleep). Same semantics as the SQL it replaces (core/like_scan.py: ASCII-only case folding, NUL-truncated text, NULL
    never matches), counted per term exactly as before (a term repeated across objects is simply looked up again). Any
    term that is not a plain substring pattern (a LIKE wildcard, empty) is left out of the result and the caller runs
    the old SQL for it. Returns None (caller runs the old SQL for everything) when the kill switch is off or anything
    about the data is not exactly reproducible; never raises."""
    try:
        from core import like_scan
        if not like_scan.SWEEPS_SINGLE_PASS:
            return None
        needles = []
        for obj in roster:
            for t in obj["terms"]:
                s = f"{t}"
                if like_scan.is_plain_needle(s) and s not in needles:
                    needles.append(s)
        counts = {s: [0, 0] for s in needles}
        if not needles:
            return {}
        cur = conn.execute("SELECT content, emotion_embedding IS NOT NULL AS has_emb FROM memory_fragments")
        while True:
            chunk = cur.fetchmany(20000)
            if not chunk:
                break
            idx = like_scan.LikeIndex([r[0] for r in chunk])
            flags = [r[1] for r in chunk]
            for s in needles:
                n = f = 0
                for i in idx.iter_matches(s):
                    n += 1
                    f += flags[i]
                counts[s][0] += n
                counts[s][1] += f
        return {s: (v[0], v[1]) for s, v in counts.items()}
    except Exception:
        return None


def census() -> dict:
    """Read-only bundle census over the roster. Returns {rows, summary}. Fail-open to empty on DB error."""
    try:
        conn = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)   # READ-ONLY, enforced
    except Exception:
        return {"rows": [], "summary": {}}
    conn.row_factory = sqlite3.Row
    try:
        from core import soundscape as _snd
    except Exception:
        _snd = None
    sounds_registry = getattr(_snd, "_SOUNDS", {}) if _snd is not None else {}
    # J-2144: load the geometry-tuple rows ONCE and hand the same list to all three helpers (was 3 separate
    # load_rows() calls = ~13 s of json.loads). Kill-switch: NASCENCE_STICK_SHARE_ROWS=0 restores per-helper loads.
    shared_rows = _shared_rows_for_census()
    sound_ctx_idx = _sound_context_index(shared_rows) if sounds_registry else {}
    book_ctx_idx = _book_context_index(shared_rows)   # J-0154: only non-empty for `book:` roster objects
    cat_triple_n = _cat_triple_count(shared_rows)     # J-0201: scalar, only used for the "the kept cat" roster entry
    rows = []
    roster = build_roster()
    single = _term_counts_single_pass(conn, roster)   # J-1922: ONE table pass for every plain term, or None
    for obj in roster:
        mentions, felt = 0, 0
        for t in obj["terms"]:
            if single is not None and f"{t}" in single:
                n_t, f_t = single[f"{t}"]
                mentions += n_t
                felt += f_t
                continue
            r = conn.execute(
                "SELECT COUNT(*) n, SUM(CASE WHEN emotion_embedding IS NOT NULL THEN 1 ELSE 0 END) f "
                "FROM memory_fragments WHERE content LIKE ? COLLATE NOCASE", (f"%{t}%",)).fetchone()
            mentions += r["n"] or 0
            felt += r["f"] or 0
        text_level = _level(mentions, _TEXT_MENTION_THRESHOLDS)
        state_flag = bool(obj.get("state"))
        audio_flag = bool(obj.get("audio"))
        sound_contexts: set[tuple] = set()
        if sounds_registry:
            for sig in _object_sound_signatures(obj["name"], sounds_registry):
                sound_contexts |= sound_ctx_idx.get(sig, set())
        sound_level = _level(len(sound_contexts), _SOUND_CONTEXT_THRESHOLDS)

        # J-0154/J-0201: `book:` objects and "the kept cat" get a real accumulation level; every other
        # object keeps the plain 0/1 boolean (fire/herbs/keepsakes/distant-cat/audio all TESTED and found
        # to have no comparably real source — see the module docstring).
        book_title = obj.get("book_title")
        book_contexts = len(book_ctx_idx.get((book_title or "")[:60], set())) if book_title else 0
        is_cat_triple = bool(obj.get("cat_triple"))
        if book_title:
            state_level = _level(book_contexts, _BOOK_CONTEXT_THRESHOLDS)
        elif is_cat_triple:
            state_level = _level(cat_triple_n, _CAT_TRIPLE_THRESHOLDS)
        else:
            state_level = int(state_flag)

        spokes = []
        if text_level:
            spokes.append(f"text(L{text_level}:{mentions})")
        if book_title:
            if state_level:
                spokes.append(f"state(L{state_level}:{book_contexts}ctx)")
        elif is_cat_triple:
            if state_level:
                spokes.append(f"state(L{state_level}:{cat_triple_n}triples)")
        elif state_flag:
            spokes.append("state")
        if audio_flag:
            spokes.append("audio")
        if sound_level:
            spokes.append(f"sound(L{sound_level}:{len(sound_contexts)}ctx)")
        if felt:
            spokes.append("felt(WALLPAPER)")   # counted but flagged; NOT a real spoke until P1
        real_spokes = text_level + state_level + int(audio_flag) + sound_level
        rows.append({"object": obj["name"], "mentions": mentions, "spokes": spokes,
                     "real_spokes": real_spokes, "text_level": text_level, "sound_level": sound_level,
                     "sound_contexts": len(sound_contexts), "state": state_flag, "state_level": state_level,
                     "audio": audio_flag})
    conn.close()
    reals = sorted(r["real_spokes"] for r in rows)
    summary = {"objects": len(rows),
               "metric_version": _METRIC_VERSION,
               "median_real_spokes": reals[len(reals) // 2] if reals else 0,
               "mean_real_spokes": round(sum(reals) / max(1, len(reals)), 2),
               "max_real_spokes": max(reals) if reals else 0,
               "at_1_spoke": sum(1 for x in reals if x <= 1),
               "at_2_spokes": sum(1 for x in reals if x == 2),
               "at_3plus": sum(1 for x in reals if x >= 3)}
    return {"rows": rows, "summary": summary}


def snapshot(res: dict | None = None) -> dict | None:
    """Run the census (or reuse a precomputed one) and append its summary to the longitudinal log.
    Called once per sleep beside psyche_graph.snapshot(). Fail-open — never raises into the sleep hook."""
    try:
        if res is None:
            res = census()
        summ = res.get("summary") or {}
        if not summ:
            return None
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **summ}) + "\n")
        return summ
    except Exception:
        return None


def _snapshot_dict() -> dict:
    """Zero-arg, always-a-dict form of snapshot() for the off_process child (J-2403): off_process needs a dict
    RESULT, and snapshot() returns None when the census came back empty (DB unreadable) or the write failed."""
    return snapshot() or {}


async def snapshot_offprocess() -> dict | None:
    """snapshot() in a spawned child (J-2403 / F-3103): same paths (see _OFFPROCESS_MIRROR), same D-0353 fence
    state, same stick_test_log.jsonl row (the child appends it, as the in-process call does). Returns the same
    summary dict snapshot() would, or None where snapshot() returns None -- and on a child failure, which
    off_process logs at WARNING (in-process, snapshot() swallows its own errors and returns None too)."""
    from core import sleep_offloop
    res = await sleep_offloop.off_process("core.stick_test", "_snapshot_dict", zero={},
                                          mirror=_OFFPROCESS_MIRROR)
    return res or None
