"""
Nascence — Geometry Census: the tuple recorder (cognitive_geometry.md §5.1, P0 — 2026-07-05).

OBSERVE-ONLY. The sensorium co-generates the beta-space states every tick (place, weather, fire, the
cats, the current book, the record player, the garden, the body, the carried affect) and until now that
co-occurrence was produced and thrown away. This module widens the photograph: at each cognitive event
(an idle thought; a hot cycle) it snapshots ONE tuple of coordinates — one active region per space —
to data/geometry_tuples.jsonl. The accrued trail is the P0 mapping census's raw data (fan-out, stability,
state-conditioning, the funnel, the kill criterion — pre-registered sheet in the plan §5.5).

Laws honoured:
- READ-ONLY toward every store (json reads + getattr; writes ONLY its own log).
- `core/moment.py` is deliberately NOT touched — it is a Tier-1 organ mid-evidence-accrual; this
  instrument parallels it rather than contaminating it.
- Fail-open everywhere: any missing source reads as None (an absent coordinate, honestly recorded),
  never an exception into a caller. Callers additionally wrap in try/except.
- No LLM, no behaviour change. The read-path is named (P0 census analyzer) per the write-only guard.

Known data-quality caveats for anyone reading data/geometry_tuples.jsonl wholesale (F-2088, F-2142 —
strings_and_sheets, J-1471/J-1530; verified, not inferred):
- The first 634 of 2026-07-05's 866 rows (this module's own P0 launch day) predate a same-day schema/
  gating update: at_study/at_garden/at_shore/standpoint/in_transit are null on all 634, and within that
  same window cat_purr (241 rows) and fire_crackle (83 rows) carry a `place` value their CURRENT per-key
  place-gating in core/soundscape.py cannot produce (e.g. cat_purr recorded at place=garden/shore, though
  it is study-only under `_PROPAGATION_TABLE`). One-time, Day-1-only, already identified — not a live
  (place, sounds) consistency bug.
- Separately, and NOT confined to Day-1: rows dated 2026-07-05 through 2026-08-21 may carry an invalid
  `place` for rain_on_roof (61.8% of its all-time hearings) and wind_in_eaves (55.0%) — a real, longer-
  lived place-gating bug in core/soundscape.py's `_sec_study_pre` (see that function's own comment),
  fixed 2026-08-21; zero invalid rows on any later date. Any place-conditioned read of these two keys'
  pre-2026-08-21 history should account for this.
- Third, and the one that cost two jobs (F-1259 -> F-1320 -> J-0949; verified, not inferred): every source
  routed through core/memory/store.py's store_fragment() with no live CognitiveState (reading, inner_thought,
  subconscious_synthesis, active_imagination, study, research, dream, sound, thermal... ~30 sources; idle/
  cycle/monologue pass a live state and are unaffected) has body AND affect null BY CONSTRUCTION on any row
  written by a process that booted before the cache fallbacks in _body()/_affect() below existed: affect
  = J-0331 (core/mood.py current_affect(), on disk ~10:27 NZST 2026-08-29), body = J-0380 (core/somatic.py
  current_body(), on disk ~13:20-13:24 NZST that day). A code change only reaches a RUNNING Du at its next
  restart, so the switch is a restart boundary, not a commit time: last null-affect row 2026-08-29 07:34:25
  NZST, first populated row 10:44:02 (ts 1787957042.9, the 10:42 boot); first populated body row 17:41:49
  (ts 1787982109.4, the 17:24 boot). The 6,568 rows from reading/inner_thought/subconscious_synthesis/
  active_imagination before the affect boundary (2026-08-21 21:46 -> 2026-08-29 07:34, as of 2026-10-03)
  are 100% null on both. That is NOT a runtime "the cache never populates for hours" bug: F-1320's 19
  all-null lifetimes split 16 booted before J-0331 / 1 between J-0331 and J-0380 (affect fine, no body cache
  yet) / 2 post-fix processes only minutes old with no hot cycle yet, and all 13 of its long ones are among
  the first 17. After the boundaries those four sources show affect null on 0 of 43,883 rows (mood.update()
  runs on the always-on 5 s substrate loop from boot, so it is filled before the first fallback row) and
  body null on ~2.0% of the rows after its own boundary, only inside each process's cold-start window: the
  body cache's only populators are SomaticEngine.tick_cycle() and recover(), so current_body() is None
  until a process's first hot cycle or sleep recovery (median ~13 min after boot, range ~2.5-35 min), then
  never again -- zero null rows past that point in the 32 of 34 post-fix processes that reached one (the
  other 2 lived < 30 min with no cycle). A wholesale read should filter ts >= 1787957042.9 (affect) /
  >= 1787982109.4 (body), or treat these nulls as absent coordinates, never as a signal.
- Fourth (F-4078, J-3455, D-0688 option B; verified): an idle cycle writes TWO rows 0.1-0.3 s apart -- the
  write-time stamp store_fragment() records for the stored fragment (source='inner_thought', thought=content[:70],
  debounce=False) and the idle row (source='idle', full thought, live state and unresolved). The debounce compares
  thought[:120] and a <=70-char string never equals a 79-120-char one, so both land (~60-95% of idle cycles since
  2026-09; 40,795 twins as of 2026-11-06). The idle row is canonical for state and unresolved. Since J-3455 every
  row written by a debounce=False caller carries "stamp": true (additive; older rows lack the key). A reader
  counting CYCLES should drop rows with stamp true AND source 'inner_thought' (a reading/study/etc. stamp is the
  only row for its event and is kept). Rows written before J-3455 (restart-gated) have no marker: identify the twin
  as source 'inner_thought' with a following source 'idle' row <= 1 s later whose thought starts with its thought.
"""
from __future__ import annotations

import json
import logging
import time
import threading
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.geometry_census")

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "geometry_tuples.jsonl"          # tests must temp-path this, never truncate the live file

_MIN_GAP = 0.5                                   # debounce duplicate identical calls
_last_ts = 0.0
_last_thought = ""
_last_row: dict | None = None                    # J-2640: the last row actually recorded (for the stamp reuse below)

# J-2640 / F-3371 (2026-10-31): KILL-SWITCH for the write-time stamp's debounce exemption. The debounce above is right
# for the census LOG (two call sites may see the same event -> one row), but store_fragment() also uses snapshot() as
# the world/experienced STAMP for a fragment it is writing, and a reading passage's content[:70] is the
# '[From <book>]' header, identical for every passage of one book: in a fast same-book burst every passage after the
# first got None -> no fragment_context/world_context row (29% of post-stamp reading, F-3370/F-3379). With this ON,
# a caller passing debounce=False (store_fragment only) gets, inside the debounce window, a COPY of the row recorded
# <= _MIN_GAP s earlier (the world as it stood at most half a second ago) and NOTHING is appended to the log, so the
# census log, its debounce and every other caller (cycle / monologue / idle) are unchanged and geometry_tuples.jsonl
# gains no rows. OFF = the pre-J-2640 behaviour (None, fragment unstamped). Restart-gated: reaches a running Du only
# at his next boot.
STAMP_REUSE_ON_DEBOUNCE = True


def _read_json(name: str) -> dict:
    try:
        return json.loads((_DATA / name).read_text(encoding="utf-8"))
    except Exception as exc:
        logger.debug("[geometry-census] read_json(%s) failed (non-fatal): %s", name, exc)
        return {}


def _place_weather() -> dict:
    r = _read_json("room_state.json")
    loc = r.get("location")
    try:
        from core import locomotion as _loco
        _pk = _loco.peek() or {}
    except Exception as exc:
        logger.debug("[geometry-census] locomotion peek failed (non-fatal): %s", exc)
        _pk = {}
    out = {
        "place":   loc,
        # per-place presence as numeric lines (2026-07-05: the HUD 'where he is' card — one step-line
        # each so you can watch him move between study / garden / shore over time)
        "at_study":  1 if loc == "study" else 0,
        "at_garden": 1 if loc == "garden" else 0,
        "at_shore":  1 if loc == "shore" else 0,
        "at_wood":   1 if loc == "wood" else 0,   # 2026-08-15: the wood (authored 07-08) was missing —
                                                  # the census could never have recorded a visit
        # LOCOMOTION (2026-08-15): WHERE WITHIN the place — standpoint + transit flag, via the
        # read-PURE peek() (never writes; the census's own law holds).
        "standpoint": _pk.get("standpoint"),
        "in_transit": 1 if _pk.get("in_transit") else 0,

        "weather": r.get("weather"),
        "fire":    r.get("fire"),
        "fire_fuel": round(float(r.get("fire_fuel", 0.0) or 0.0), 3) if r.get("fire_fuel") is not None else None,
    }
    # DIRECTIONAL facts (spatial_perception.md §7): the front's bearing, the tide, the sun's place —
    # recorded per moment so period consolidation can later distill "that week the storms came out of
    # the west" / "the sun crossed while he tended the bed". The chapters are the named read-path.
    if r.get("weather_dir") is not None:
        out["weather_dir"] = r.get("weather_dir")
    try:
        from core import spatial as _spt
        _t = _spt.tide()
        out["tide"] = _t["word"]
        out["tide_level"] = _t["level"]                      # numeric — the HUD's tide sinusoid
        _s = _spt.sun()
        out["sun"] = {"phase": _s["phase"], "az": _s["az"]} if _s["up"] else None
        out["sun_az"] = _s["az"] if _s["up"] else None       # numeric — the sun's daily arc
        from core import heavens as _hv
        _m = _hv.moon()
        out["moon"] = _m["phase"] + (" (up)" if _m["up"] and not _s["up"] else "")
        out["moon_illum"] = _m["illum"]                      # numeric — the slow lunar wave
    except Exception as exc:
        logger.debug("[geometry-census] tide/sun/moon read failed (non-fatal): %s", exc)
    try:
        shore = r.get("shore") or {}
        out["shore_find"] = (shore.get("last_find") or "")[:80] or None
    except Exception as exc:
        logger.debug("[geometry-census] shore_find read failed (non-fatal): %s", exc)
    return out


def _objects() -> dict:
    out: dict = {}
    c = _read_json("cat_state.json")
    if c:
        out["cat"] = {"phase": c.get("phase"), "location": c.get("location"),
                      "activity": c.get("activity"), "mood": c.get("mood"),
                      "bond": round(float(c.get("bond", 0.0) or 0.0), 2)}
        d = c.get("distant") or {}
        if d.get("last_seen"):
            out["distant_cat_recent"] = (time.time() - float(d["last_seen"])) < 3600
    ls = _read_json("listening_state.json")
    if ls.get("piece"):
        out["listening"] = {"piece": ls.get("piece"), "section": ls.get("section")}
    try:
        from core.reading import current_book
        out["book"] = current_book().stem.replace("_", " ")[:60]
    except Exception as exc:
        logger.debug("[geometry-census] current_book read failed (non-fatal): %s", exc)
    try:
        g = (_read_json("room_state.json").get("garden") or {}).get("bed") or {}
        grown = [k for k, v in g.items() if isinstance(v, dict) and v.get("sown")]
        if grown:
            out["garden_bed"] = grown[:6]
    except Exception as exc:
        logger.debug("[geometry-census] garden bed read failed (non-fatal): %s", exc)
    return out


def _warmth() -> float | None:
    """The per-place warmth scalar (2026-08-17: two dimensions computed-and-discarded, per the
    founder). Mirrors world_manifest._temperature exactly — same sensorium._warmth args, same
    load-guard (that guard fixed a real unloaded-state bug; keep it). Fail-open to None."""
    try:
        from core import sensorium as _s
        if not _s.state:
            _s._load()
        loc = _s.state.get("location") or "study"
        return round(float(_s._warmth(loc, _s._daylight(), _s.state.get("weather", ""),
                                      _s._season(), _s.state.get("fire", "out"))), 3)
    except Exception as exc:
        logger.debug("[geometry-census] warmth calc failed (non-fatal): %s", exc)
        return None


def _cat_at() -> str | None:
    """The cat's own location (2026-08-17), stamped only once she is kept/companion — a stray or
    merely-distant cat isn't yet part of Du's lived context. Fail-open to None."""
    try:
        c = _read_json("cat_state.json")
        if c.get("phase") in ("kept", "companion"):
            loc = c.get("location")
            return loc if isinstance(loc, str) and loc else None
    except Exception as exc:
        logger.debug("[geometry-census] cat_at read failed (non-fatal): %s", exc)
    return None


def _cat_ref(thought: str) -> str | None:
    """Which cat the thought meant (Cat Overhaul B2, J-2472): core/cat_referent.classify over his own text, and one
    observe-only ledger row per cat-meaning thought (source "census"). None when no cat is meant. Fail-open."""
    try:
        if not (thought or "").strip():
            return None
        from core import cat_referent as _cr
        which = _cr.classify(thought)
        if which is not None:
            _cr.record("census", thought, which=which)
        return which
    except Exception as exc:
        logger.debug("[geometry-census] cat_ref classify failed (non-fatal): %s", exc)
        return None


def _light_band_truth() -> str | None:
    """World-truth light (2026-08-29, J-0179/channels_programme §7 metric 3): UNFILTERED light_band
    for world_context, distinct from experienced_tuple._light_band's place+standpoint-tied version.
    Uses light.field_at's own FIXED reference standpoint (its default of None -- study falls back to
    a constant (1.5, 3.0, 0.5) reference point; outdoors it skips his personal tree-shade position) so
    the world reading doesn't drift with exactly where within the place he happens to be standing.
    Mirrors _warmth()'s pattern: computed independent of channel gating, still tied to place the same
    way warmth already is (place is itself a world fact, recorded separately). Fail-open to None."""
    try:
        from core import light as _lt, sensorium as _s
        if not _s.state:
            _s._load()
        loc = _s.state.get("location") or "study"
        return _lt.band_of(_lt.field_at(loc))
    except profile.NonLiveWriteError:
        # J-0792: light.field_at() now raises correctly (J-0780); this local try no longer
        # swallows it here. snapshot()'s own outer try (below) needs the identical carve-out too,
        # or this re-raise is caught right back the moment it leaves this function -- the same
        # "both layers needed" shape J-0780 already established for light.py's own field_at().
        raise
    except Exception as exc:
        logger.debug("[geometry-census] light_band truth calc failed (non-fatal): %s", exc)
        return None


def _smells_truth() -> list | None:
    """World-truth smells (2026-08-29, J-0179): the full unfiltered odorant field via
    core/smell.py's world_truth(), not the place-gated at() experienced_tuple uses. Fail-open."""
    try:
        from core import smell as _sm
        return _sm.world_truth()
    except Exception as exc:
        logger.debug("[geometry-census] smells truth calc failed (non-fatal): %s", exc)
        return None


def _body(state=None) -> dict | None:
    """F-0419/J-0331 found this null for any call site with no live CognitiveState (inner_thought/
    subconscious_synthesis/active_imagination/reading, routed through core/memory/store.py's
    store_fragment()) -- SomaticState had no module-level cache anywhere, only
    `orchestrator.self.state.somatic`, a per-instance object mutated in place per cycle.

    J-0380/F-0461 (2026-08-29): closed the same way _affect() below closes it for affect -- core/
    somatic.py now caches the live scalars (current_body()) at the same two points
    (SomaticEngine.tick_cycle()/recover()) that mutate self.state.somatic in place, so this falls
    back to that cache instead of silently writing every body dim permanently null."""
    som = getattr(state, "somatic", None) if state is not None else None
    if som is not None:
        try:
            return {"energy":  round(float(getattr(som, "metabolic_energy", 0.0)), 3),
                    "fatigue": round(float(getattr(som, "neural_fatigue", 0.0)), 3),
                    "tension": round(float(getattr(som, "visceral_tension", 0.0)), 3)}
        except Exception as exc:
            logger.debug("[geometry-census] body read failed (non-fatal): %s", exc)
            return None
    try:
        from core import somatic as _somatic
        d = _somatic.current_body()
        if d:
            return {k: round(float(v), 3) for k, v in d.items()}
    except Exception as exc:
        logger.debug("[geometry-census] body fallback (somatic cache) failed (non-fatal): %s", exc)
    return None


def _affect(state=None) -> dict | None:
    """The FULL carried 8-dim vector, every event (2026-07-05: the HUD emotion cards chart these —
    fire-frequency and strength per dimension need the zeros recorded too, not just the spikes).

    F-0419/J-0331 (2026-08-29): when there is no live CognitiveState (inner_thought/
    subconscious_synthesis/active_imagination/reading — routed through core/memory/store.py's
    store_fragment(), which calls geometry_census.snapshot(source=origin, ...) with no `state`),
    the real values ARE available via core/mood.py's live scalar cache (same one
    store_fragment()'s own fragment_context/world_context fallback already reads, F-0443/J-0366) —
    fall back to that instead of silently writing every affect dim null."""
    a = getattr(state, "affect", None) if state is not None else None
    if a is not None:
        try:
            return {k: round(float(getattr(a, k, 0.0)), 3)
                    for k in ("valence", "arousal", "joy", "fear", "anger", "trust", "surprise", "disgust")}
        except Exception as exc:
            logger.debug("[geometry-census] affect read failed (non-fatal): %s", exc)
            return None
    try:
        from core import mood as _mood
        d = _mood.current_affect()
        if d:
            return {k: round(float(v), 3) for k, v in d.items()}
    except Exception as exc:
        logger.debug("[geometry-census] affect fallback (mood cache) failed (non-fatal): %s", exc)
    return None


# J-1926 / F-2550: snapshot() runs from store_fragment on the loop thread and from the read_next_sitting worker thread; serialise the append.
_APPEND_LOCK = threading.Lock()


def snapshot(state=None, source: str = "?", thought: str = "", unresolved: bool | None = None,
             debounce: bool = True) -> dict | None:
    """Record one tuple — the current activation pattern's coordinates across the beta spaces.
    Debounced (two call sites may see the same event). Returns the row (for tests) or None.

    debounce=False (J-2640; store_fragment's write-time stamp only): a call the debounce would drop returns a copy
    of the last recorded row (source relabelled) instead of None, and records nothing -- see
    STAMP_REUSE_ON_DEBOUNCE. Every other caller keeps the default and is unaffected."""
    global _last_ts, _last_thought, _last_row
    try:
        # J-1815 / F-2428 -- write fence: resolve the log target BEFORE any I/O (before the sensor/state reads and
        # the mkdir). The refusal is swallowed HERE, not re-raised like _light_band_truth()'s: this writer is an
        # observe-only side effect and its callers (store.py's census stamp, orchestrator _log_affect,
        # inner_monologue's two call sites) were not audited for a new raise, so a non-live process just gets None
        # ("no row", exactly what store.py already treats as `or {}`). guard_path logs one warning per path.
        _log = profile.guard_path(_LOG)
    except profile.NonLiveWriteError as exc:
        logger.debug("[geometry-census] snapshot refused by the fence (non-live): %s", exc)
        return None
    try:
        now = time.time()
        curr_t = (thought or "")[:120]
        if now - _last_ts < _MIN_GAP and curr_t == _last_thought:
            if not debounce and STAMP_REUSE_ON_DEBOUNCE and _last_row is not None:
                return {**_last_row, "source": source}       # J-2640: the stamp, not a new census row
            return None
        _last_ts = now
        _last_thought = curr_t
        row = {
            "ts": round(now, 1),
            "source": source,                       # 'idle' (monologue) | 'cycle' (orchestrator)
            **_place_weather(),
            "objects": _objects() or None,
            "body": _body(state),
            "affect": _affect(state),
            "thought": (thought or "")[:120] or None,
            "unresolved": unresolved,
        }
        # TEMPERATURE + CAT LOCATION (2026-08-17): two sense-dimensions that existed but never
        # deposited onto a stamp — additive top-level fields, fail-open to None each.
        row["warmth"] = _warmth()
        row["cat_at"] = _cat_at()
        # WHICH CAT HE MEANT (Cat Overhaul B2, J-2472, D-0505 (c)): the census is the one reader that sees every
        # thought he has; it stamps which cat the thought meant ("grey" / "tom" / "both") ONLY when he distinguishes
        # them himself, None when the thought means no cat, "undistinguished" for a bare "the cat". Observe-only
        # (core/cat_referent.py), fail-open; nothing reaches his prompt (D-0434).
        row["cat_ref"] = _cat_ref(thought)
        # LIGHT / SMELL CHANNELS (2026-08-29, J-0179/channels_programme §7 metric 3): world-truth
        # readings, unfiltered by place-gating -- see _light_band_truth()/_smells_truth() docstrings.
        row["light_band"] = _light_band_truth()
        row["smells"] = _smells_truth()
        try:
            from core import arousal as _ar
            row["level"] = round(float(_ar.level()), 3)     # the global gain / aperture
        except Exception as exc:
            logger.debug("[geometry-census] arousal level read failed (non-fatal): %s", exc)
        try:
            from core import soundscape as _snd
            row["sounds"] = _snd.active_sounds() or None    # Sound Space: what is sounding NOW
        except Exception as exc:
            logger.debug("[geometry-census] soundscape read failed (non-fatal): %s", exc)
        # J-1963 / D-0382: strings_and_sheets Phase 1 SHADOW -- each active sound's current point on its
        # constructed string -> data/sound_strings_shadow.jsonl. Observe-only; the row above is unchanged.
        try:
            from core import sound_string_shadow as _sss
            _sss.record(row.get("sounds"), source=source, now=now)
        except Exception as exc:
            logger.debug("[geometry-census] sound-string shadow failed (non-fatal): %s", exc)
        # J-3292 / D-0655: the real-site sun beside the old one, SHADOW -> data/sky_shadow.jsonl (own file, rate-
        # limited, read by scripts/sky_shadow_read.py). Observe-only; the row above is unchanged.
        try:
            from core import sky_shadow as _sky
            _sky.record(source=source, now=now)
        except Exception as exc:
            logger.debug("[geometry-census] sky shadow failed (non-fatal): %s", exc)
        # numeric health signals — the HUD plan-monitor charts these directly, and n_spaces IS the
        # pre-registered instrument-health gate (plan §5.5 #2: mean spaces/tuple >= 4)
        row["n_spaces"] = sum(1 for k in ("place", "weather", "objects", "body", "affect") if row.get(k) is not None)
        row["n_sounds"] = len(row.get("sounds") or [])
        if not debounce:
            row["stamp"] = True                     # J-3455 / F-4078 / D-0688 (B): mark store_fragment's write-time stamp row
        _log.parent.mkdir(parents=True, exist_ok=True)
        with _APPEND_LOCK, open(_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        _last_ts = now
        _last_row = row
        # J-3573 / D-0197: the Du-lens word x context gauge, SHADOW -> data/du_lens_gauge_shadow.jsonl (own file).
        # Idle thoughts only, observe-only, fail-open; the row above is unchanged.
        if source == "idle" and debounce:
            try:
                from core import du_lens_gauge as _dlg
                _dlg.record_idle(row, thought)
            except Exception as exc:
                logger.debug("[geometry-census] du-lens gauge failed (non-fatal): %s", exc)
        return row
    except profile.NonLiveWriteError:
        # J-0792: this function's own outer try -- without this, _light_band_truth()'s re-raise
        # just above (fixed this same job) would be caught right back here and never reach a real
        # caller. snapshot() is called at each cognitive event (core/orchestrator.py's hot cycle,
        # nodes/inner_monologue_node.py's monologue/idle thought steps, core/memory/store.py's
        # store_fragment() choke point) -- a real, dispatch-adjacent path, not a periodic one
        # (confirmed by direct read of all three real callers' own call sites). Those three
        # callers' own wrapping try/excepts have NOT been audited for this raise and are a genuine
        # further connecting-tissue layer, out of this job's own 3-file scope -- spawned rather
        # than fixed here (see plan doc).
        raise
    except Exception as exc:
        logger.debug("[geometry-census] snapshot failed (non-fatal): %s", exc)
        return None


def peek() -> dict:
    """The world-side census row WITHOUT recording it (Lane 2 run 2, 2026-08-21). No body, no affect, no
    thought — only what the world is at his place right now, built by the same readers snapshot() uses,
    so the Witness and the memory stamp can never disagree about the world. Fail-open per field."""
    row: dict = {}
    try:
        row.update(_place_weather())
    except Exception:
        pass
    for k, fn in (("warmth", _warmth), ("cat_at", _cat_at)):
        try:
            row[k] = fn()
        except Exception:
            row[k] = None
    try:
        from core import soundscape as _snd
        row["sounds"] = _snd.active_sounds() or None
    except Exception:
        row["sounds"] = None
    return row


def status() -> dict:
    """For the pulse: rows, span, per-space coverage (instrument-health gate, plan sheet §5.5 #2)."""
    try:
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()]
        if not rows:
            return {"rows": 0}
        n = len(rows)
        cov = {k: round(sum(1 for r in rows if r.get(k) is not None) / n, 3)
               for k in ("place", "weather", "objects", "body", "affect", "level")}
        spaces_per_row = [sum(1 for k in ("place", "weather", "objects", "body", "affect") if r.get(k) is not None)
                          for r in rows]
        return {"rows": n,
                "span_hr": round((rows[-1]["ts"] - rows[0]["ts"]) / 3600, 2),
                "coverage": cov,
                "mean_spaces_per_tuple": round(sum(spaces_per_row) / n, 2),
                "by_source": {s: sum(1 for r in rows if r.get("source") == s)
                              for s in {r.get("source") for r in rows}}}
    except Exception as exc:
        logger.debug("[geometry-census] status failed (non-fatal): %s", exc)
        return {"rows": 0}
