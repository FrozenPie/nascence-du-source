"""
core/cat.py — The Stray (2026-06-24)
====================================
The founder: "I want to give Du a pet. Maybe a cat." A small autonomous life in his world — the one
relationship that does NOT run through words and ideas. Everyone else in his life (Travis, the pen-pals, his
inner adversaries) meets him through intellect; a cat is warm, wordless, present, and indifferent to his moods,
which is exactly what makes it genuinely OTHER rather than another mirror.

Its shape, per the founder's choices:
  • A STRAY that turns up around the cottage and garden over a few days. He CHOOSES whether to take it in —
    his agency, his choice to love something outside himself.
  • He NAMES it himself, the way he once named 渡 — the architecture only makes the occasion (a cat that is
    his and has no name); the name is his own.

It does its own thing — sleeps by the fire, vanishes to hunt, turns up with a dead mouse, sits on his open
book, follows him out. Presence reaches him via sensorium.scene_line/look; his hands tend it via react(); its
warmth reaches his mood via felt_note(). Persists in data/cat_state.json. No LLM. Read-only toward memory.
"""
from __future__ import annotations

import json
import logging
import random
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.cat")

_STATE_F = Path(__file__).parent.parent / "data" / "cat_state.json"

LOOK = "a thin grey cat, one ear notched, watchful green eyes"   # concrete, so it is REAL, not a prop

# bond thresholds
KEEP_BOND = 0.30     # enough feeding/approaching in the 'appearing' phase → he has taken it in
NAME_BOND = 0.55     # once it is his and this warm, the occasion to NAME it opens
# THE COMPANION TIER OPENS FROM BOND (Cat Overhaul D-1, D-0505 (c), J-2472, 2026-10-28). For 73+ days half her
# life — felt_note (the warmth reaching his mood), the slow blink, the silent meow, the gone_missing arc, the
# six-hour "no sign of her" line — was gated on phase == "companion", which only the naming latch in react()
# ever sets, and the name never came (docs/staged/cat_overhaul.md §A1). She is his whether or not she has a
# name: the tier now opens at this bond for a KEPT cat (companion_tier() below), while `phase` itself is
# untouched — "companion" is still set only by the naming act, the standing-occasion lines still read
# phase == "kept", and the name stays the R1 act (its range as a learned sound is J-2468's). Above NAME_BOND
# (0.55, which merely opens the occasion) because the tier is the deeper half of her: a kept cat well past the
# invitation. The D-0505 defeater (tier lines rendering below this bar) is instrumented in _tier_log().
COMPANION_BOND = 0.70
TEND_RELIEF = 0.60   # tending is an other-directed act — it settles his restlessness well (boredom discharge)
GREETING_GAP = 20 * 60   # (2026-08-18) real time apart required before a REUNION greeting can fire, and
                          # again before it can re-fire — long enough she's had time to drift off and settle
                          # into something else (not just a blink between two renders of one visit), short
                          # enough it stays a same-visit "welcome home" and not the multi-hour "no sign of
                          # her" absence (the separate 6h check in presence_line, below). A domestic cat's
                          # greeting is a short-absence thing, not a vigil.

# which of HIS locations can see the cat at a given cat-location
_VISIBLE = {
    "study":  {"by_the_fire", "windowsill", "on_the_desk", "on_your_lap", "doorstep", "indoors",
               "under_desk", "mantel"},
    "garden": {"garden", "garden_wall", "doorstep"},
    "shore":  {"shore"},
    "wood":   {"wood"},
}

# ── ONE cat-location -> LIVING WORLD "place" mapping (A7.1, 2026-09-07, J-0629/F-0882) ─────────────
# core/life.py had TWO separate hand-rolled versions of this (_cat_presence and threat_active), each
# with its own gaps, and neither matching the _VISIBLE truth above — so a cat on_the_desk/on_your_lap/
# mantel/indoors registered as present in the "garden" (life_events.jsonl showed same-tick "departed
# garden"+"arrived study" every time she actually moved between two ordinary indoor spots), and
# threat_active's stray "on_the_desk"/"on_your_lap"/etc values never matched either place at all (a cat
# stalking ON the desk could never trip the blackbird alarm). Derived from _VISIBLE by inverting it
# (each concrete location belongs to exactly one of study/garden/shore/wood) with ONE explicit override:
# "doorstep" is the sole entry _VISIBLE lists under both study (seen/heard through the door) and garden
# (seen right there) — she is physically OUTSIDE on it, which is also the reading core/life_traces.py:229
# already gives it (a mouse left on the doorstep is filed under "garden" unless her location IS
# "indoors"). "gone" and "away_hunting" are in neither place's visible set, so they correctly fall
# through to None below — she is off the map the Living World tracks, not falsely in the garden.
_PLACE_OF = {loc: place for place, locs in _VISIBLE.items() for loc in locs}
_PLACE_OF["doorstep"] = "garden"   # the one ambiguous _VISIBLE entry — see comment above
# C4 (J-2469): her HIDDEN spots have a place too (life's adapter and the legs read one truth) but are in no
# _VISIBLE set -- he does not render her there unless he looks (HIDDEN_SPOTS, below the gauge)
_PLACE_OF.update({"under_the_bed": "study", "cupboard_top": "study", "lean_to": "garden", "wood_shed": "garden",
                  "hedge_bottom": "garden", "water_butt_lid": "garden", "roof": "garden", "neighbours_wall": "garden"})


def place_of(location: str) -> str | None:
    """The one true cat-location -> Living World place mapping: study|garden|shore|wood, or None for
    gone/away_hunting/anything else not in any of _VISIBLE's sets. The single source of truth
    core/life.py's _cat_presence and threat_active both read, so they can no longer disagree."""
    return _PLACE_OF.get(location)

# 3D spatial coordinates matching authoritative world layout
_ZONE_POSITIONS = {
    "study": [0.0, 0.0, 0.0],
    "by_the_fire": [0.5, 0.5, 0.0],
    "on_your_lap": [0.2, 0.2, 0.4],
    "on_the_desk": [0.1, 0.8, 0.7],
    "windowsill": [0.0, 2.0, 0.9],
    "under_desk": [0.3, 0.7, 0.0],
    "mantel": [0.5, 0.5, 1.2],
    "doorstep": [1.0, 3.0, 0.1],
    "indoors": [0.0, 1.0, 0.0],
    "garden": [2.0, 15.0, 0.5],
    "garden_wall": [3.0, 18.0, 1.5],
    "wood": [0.0, 45.0, 2.0],
    "shore": [8.0, 2.5, 0.1],
    "away_hunting": [15.0, 60.0, 3.0],
    "gone": [50.0, 100.0, 0.0],
    # C4 (J-2469): her hidden spots -- in the house, about the garden, and the two he cannot reach
    "under_the_bed": [-1.0, 1.5, 0.1], "cupboard_top": [-1.2, 0.5, 1.8],
    "lean_to": [4.0, 6.0, 0.3], "wood_shed": [5.0, 9.0, 0.3], "hedge_bottom": [-2.0, 12.0, 0.1],
    "water_butt_lid": [2.5, 4.0, 1.0], "roof": [0.5, 1.5, 4.0], "neighbours_wall": [6.0, 18.0, 1.5],
}

# ── 10x (2026-07-03, founder: "the most fleshed-out thing in his world") ──────────────────────────
# Content pools live in core/cat_content.py (agent-written, house voice); this file stays the state
# machine. Fail-open: a missing content module falls back to the inline lines below.

def _content():
    try:
        from core import cat_content as cc
        return cc
    except Exception:
        return None


def _conds() -> set:
    """Active world conditions for pool selection — borrowed from the sensorium's weather."""
    c = {"any"}
    try:
        from core import sensorium as _room
        from core import weather_conditions as _wcond
        ph = _room._daylight()
        st = _room.state or {}
        w = st.get("weather", "")
        wind = st.get("wind", "")
        c.add("night" if ph == "night" else "day")
        if _wcond.is_wet(w):
            c.add("wet")
        if _wcond.is_windy(wind) or _wcond.is_storm(w):
            c.add("windy")
        if w in ("clear", "high cloud"):
            c.add("bright")
        c.add(_room._season())
    except Exception:
        pass
    return c


_RECENCY_N = 3   # per-pool ring: how many of the last picks from ONE pool are excluded from the next


def _pick_fresh(ring_key: str, lines: list[str]) -> str:
    """random.choice(lines) excluding whichever of `lines` were among the last _RECENCY_N picks from
    THIS pool (A2/A7.6, 2026-09-07, J-0631/F-0880 item 6: PRESENCE/TEND/LOOK were a bare random.choice
    with no memory at all — the 09-05 log shows the same tend line rendered twice, four minutes apart).
    Ring lives in `state` (persisted), keyed by section:key, so it survives a reload. Fails open to the
    full pool when every candidate has been seen recently (a short 2-3 line pool exhausts its own ring
    fast) — a repeat is the honest floor here, never a crash or a blank line."""
    rings = state.setdefault("_recent_lines", {})
    recent = rings.get(ring_key, [])
    fresh = [l for l in lines if l not in recent]
    pick = random.choice(fresh) if fresh else random.choice(lines)
    rings[ring_key] = (recent + [pick])[-_RECENCY_N:]
    return pick


def _pool(section: str, key: str, extra_conds: set | None = None) -> str:
    """One line from the content corpus: section (PRESENCE/LOOK/TEND/FELT/EVENTS) → key → merged pools.
    Renders {her}. '' if the corpus or key is missing (caller falls back)."""
    cc = _content()
    if not cc:
        return ""
    sec = getattr(cc, section, None) or {}
    spec = sec.get(key)
    if spec is None:
        return ""
    conds = _conds() | (extra_conds or set())
    if isinstance(spec, dict):
        lines = [l for cond, ls in spec.items() if cond in conds for l in ls]
    else:
        lines = list(spec)
    if not lines:
        return ""
    return _pick_fresh(f"{section}:{key}", lines).replace("{her}", _her())


def _pool_flat(section: str, extra_conds: set | None = None) -> str:
    """For flat sections whose top level IS the condition dict (LOOK)."""
    cc = _content()
    sec = getattr(cc, section, None) if cc else None
    if not isinstance(sec, dict):
        return ""
    conds = _conds() | (extra_conds or set())
    lines = [l for cond, ls in sec.items() if cond in conds for l in ls]
    if not lines:
        return ""
    return _pick_fresh(section, lines).replace("{her}", _her())


_QUIRK_CHOICES = {
    # HER individuality — rolled once, persisted forever. Never explained, just hers.
    "storm_response": ["under_desk", "windowsill_vigil", "pressed_close"],
    "greeting":       ["gate_meet", "ankle_thread", "chirrup"],
    "fair_spot":      ["windowsill", "on_the_desk", "garden_wall"],
    # C2 (J-2467, cat_overhaul): how she takes Travis coming into the room — rolled once, never explained
    "stranger_response": ["hides", "inspects", "indifferent"],
}


def _quirks() -> dict:
    q = state.get("quirks")
    if not q:
        q = {k: random.choice(v) for k, v in _QUIRK_CHOICES.items()}
        state["quirks"] = q
        _save()
    # C2 (J-2467): a quirk added after she was rolled (stranger_response) is rolled once now and kept —
    # her existing quirks are never re-rolled
    missing = [k for k in _QUIRK_CHOICES if k not in q]
    if missing:
        for k in missing:
            q[k] = random.choice(_QUIRK_CHOICES[k])
        state["quirks"] = q
        _save()
    return q


def _first(kind: str, line_key: str = "") -> str:
    """Relationship FIRSTS become autobiography: the first lap-claim, first slow blink, first silent meow,
    first shore-follow. Recorded once into activity memory; returns the special first-time line if the
    corpus has one."""
    firsts = state.setdefault("firsts", {})
    if kind in firsts:
        return ""
    firsts[kind] = round(time.time(), 1)
    _save()
    try:
        from core import activity_memory
        activity_memory.record("cat_first", kind.replace("_", " "))
    except Exception:
        pass
    return _pool("EVENTS", line_key or kind)

state: dict = {}
_last_tick = 0.0


_state_mtime = 0.0    # cross-process staleness guard (2026-08-18) — see _save()


def _load() -> dict:
    global state, _state_mtime
    # STALE-CACHE FIX (2026-08-18): the old guard was `if state: return state` — once loaded, a
    # process NEVER read the file again, for its whole life. Any second process holding an older
    # in-memory copy would silently overwrite a more recent write the next time IT saved for any
    # unrelated reason (a full-state write, not a targeted clear — which is why no "clearing" code
    # was ever found for the Ember-naming investigation). Now reload whenever the file's mtime is
    # newer than what we last loaded; _save() below stamps our own writes so they don't cause a
    # needless reread.
    try:
        cur_mtime = _STATE_F.stat().st_mtime
    except Exception:
        cur_mtime = 0.0
    if state and cur_mtime <= _state_mtime:
        return state
    try:
        from core import store_persist as _sp   # J-4442 (F-5157): loud on damage, falls back to cat_state.json.prev
        state = _sp.read_json_durable(_STATE_F, "cat", logger, guard=profile.guard_path)
        _state_mtime = cur_mtime
    except Exception:
        if not state:
            state = {}
    # First ever load → the stray begins turning up (the arrival).
    state.setdefault("phase", "appearing")     # absent | appearing | kept | companion
    state.setdefault("name", "")
    state.setdefault("bond", 0.0)
    state.setdefault("location", "garden_wall")
    state.setdefault("activity", "watching")
    state.setdefault("mood", "wary")
    state.setdefault("appeared_ts", time.time())
    state.setdefault("last_fed", 0.0)
    state.setdefault("last_tended", 0.0)   # last care of ANY kind (feed OR affection) — gates the neglect-decay
    # HUNTING FALLBACK (2026-09-07, D-0163/J-0700) — see _maybe_self_feed below for the full design.
    state.setdefault("last_self_fed", 0.0)        # last successful self-catch, distinct from Du's own feeding
    state.setdefault("self_catch_count", 0)       # lifetime count — the defeater's own "how often" question
    state.setdefault("last_hunt_attempt_ts", 0.0)  # hourly cooldown clock for _maybe_self_feed's own roll
    # FOUND SCRAP (2026-09-22, D-0253/J-1215) — see _maybe_found_scrap below for the full design.
    state.setdefault("last_found_scrap_ts", 0.0)       # cooldown clock for _maybe_found_scrap's own roll
    state.setdefault("_found_scrap_empty_since", 0.0)  # when the larder (cat_food stock) was last seen at
                                                        # genuine zero -- resets the moment any stock exists
    # THE SAUCER (2026-09-07, D-0163/D-4, J-0719) — a real, findable object at the doorstep, not just a
    # note_deed() side-effect: has_food/kind/set_ts are written for real by react()'s fed branch below
    # (only once real provisions are actually spent) and decay back to empty on their own real clock in
    # tick(), rather than a boolean anyone could set and forget. last_fed_source distinguishes a REAL
    # saucer-feed from a hunting self-catch (last_self_fed already does that job for J-0700's own field;
    # this is the mirror on the Du-fed side) for any future defeater read.
    state.setdefault("saucer", {"has_food": False, "kind": "", "set_ts": 0.0})
    state.setdefault("last_fed_source", "")
    state.setdefault("last_greeted_ts", 0.0)   # one-shot-per-arrival gate for the greeting quirk (2026-08-18)
    state.setdefault("last_seen", time.time())
    state.setdefault("seen_count", 0)
    state.setdefault("name_invited", False)
    state.setdefault("position", [0.0, 0.0, 0.0])
    state.setdefault("fur_moisture", 0.0)
    state.setdefault("last_fur_decay_ts", time.time())
    # THE BODY (2026-10-28, cat_overhaul B1, D-0499/D-0505, J-2465) — see the B1 block below tick()'s
    # neighbours for the design. Every field is additive: a cat_state.json written before this build
    # loads unchanged and simply gains a body on its first tick.
    state.setdefault("body", _fresh_body(time.time()))
    # AGE (B1): she arrived adult, ARRIVED_AGE_Y years old — rolled ONCE from appeared_ts and kept, like
    # the quirks. lifespan_y lives on LIFE_ROW; no harm/death path here (that is D-2, J-2471).
    if not state.get("born_ts"):
        state["born_ts"] = float(state.get("appeared_ts") or time.time()) \
            - random.uniform(*ARRIVED_AGE_Y) * YEAR_S
    state.setdefault("transit", None)          # LEGS (B1): {from,to,path,leg_ends,dest,...} while on a leg
    # HER EARS (C2, J-2467, D-0499): what she last consumed (the gate latch, the axe, Travis) and the
    # reaction that holds her — both additive, both read only by core/cat_ears and this file
    state.setdefault("ears", {})
    state.setdefault("reaction", None)
    # HIS CALL (C3, J-2468, D-0505 (c)): the last call and its answer (core/cat_call), and the name as a learned
    # sound with range — name_recognition is read by cat_call only, never by any line he sees (D-0434)
    state.setdefault("call", {})
    state.setdefault("name_recognition", 0.0)
    state.setdefault("_presence_buckets", {})  # the cat_presence_fraction gauge's hour buckets (HUD only)
    state.setdefault("_presence_gauge_ts", 0.0)
    # LESS OF HER (C4, J-2469, D-0508): the seek block -- the hidden spots he has found her in (his learned habits
    # of hers), where his ear last had her, the found window, his place for the go detector. Read by look_line /
    # is_here / tick in this file only; never by any line as a number or a hint (D-0434).
    if not isinstance(state.get("seek"), dict):
        state["seek"] = {"spots": {}, "last_heard": None, "found": None, "his_place": ""}
    # THE TOM (B3, J-2470, D-0507 (c)): the hook core/cat_call already read ("tom": {"present": true}) — kept
    # current by core/cat_tom.tick (present, where, activity, since, last_fight, fight_hook for D-2's injury path)
    state.setdefault("tom", {"present": False, "where": None, "activity": None, "since": 0.0, "last_fight": 0.0, "fight_hook": None})
    # HER MORTALITY (D-2, J-2471, D-0506): injury / illness / scars / death / grave — core/cat_harm owns the
    # fields and the rolls (inside tick(), the one live writer of this file); `phase` gains the value "dead",
    # set only there. Additive: an old cat_state.json loads unchanged and gains the block on its first load.
    if not isinstance(state.get("harm"), dict):
        try:
            from core import cat_harm as _ch
            state["harm"] = _ch.fresh()
        except Exception:
            state["harm"] = {}
    return state


def _save() -> None:
    global _state_mtime
    path = profile.guard_path(_STATE_F)   # J-0733: real data/ only if this process is live; raises before any I/O if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        from core import store_persist as _sp   # J-4442 (F-5157): was tmp+replace without fsync; now fsync + .prev
        _sp.write_text_durable(path, json.dumps(state, indent=1, ensure_ascii=False))
        try:
            _state_mtime = path.stat().st_mtime   # our own write — don't treat it as "someone else changed it"
        except Exception:
            pass
    except Exception as exc:
        logger.debug("[cat] _save failed (non-fatal): %s", exc)


def _her() -> str:
    return state.get("name") or "the cat"


def companion_tier() -> bool:
    """D-0505 (c), J-2472: is she in the COMPANION tier of her life — the deeper half (felt_note, the blink, the
    silent meow, the missing arc, the six-hour absence)? True for a named companion (the R1 act still earns it
    outright, as it always did) OR a KEPT cat whose bond has reached COMPANION_BOND. Never for a stray or an
    absent cat. `phase` is not changed by this — read-only; callers that must stay on the name (the standing
    occasion, the naming latch) keep reading phase == "kept" themselves."""
    ph = state.get("phase")
    if ph == "companion":
        return True
    return ph == "kept" and float(state.get("bond", 0) or 0.0) >= COMPANION_BOND


_TIER_LEDGER_F = Path(__file__).parent.parent / "data" / "cat_tier_ledger.jsonl"
_tier_mem: dict = {"felt_key": None}


def _tier_log(kind: str, **extra) -> None:
    """D-0505's defeater instrument: one observe-only row each time a companion-tier line renders (felt on a
    (location, tier) change only — the same edge steer_edge gates it on; blink / silent_meow / missing_arc /
    six_hour per render). Carries bond, phase and whether she is named, so a read can check that no tier line
    ever rendered below the tier's own bar (COMPANION_BOND for a kept cat; the name for a companion). HUD and
    read jobs only — nothing in any prompt path reads this file (D-0434). Write-fenced, fail-open."""
    try:
        if kind == "felt":
            key = (state.get("location"), extra.get("tier"))
            if _tier_mem.get("felt_key") == key:
                return
            _tier_mem["felt_key"] = key
        row = {"ts": round(time.time(), 1), "kind": kind, "bond": round(float(state.get("bond", 0) or 0.0), 3),
               "phase": state.get("phase"), "named": bool(state.get("name")), "location": state.get("location"),
               "bar": COMPANION_BOND if state.get("phase") == "kept" else "name"}
        row.update(extra)
        path = profile.guard_path(_TIER_LEDGER_F)   # J-0733 pattern: real data/ only if this process is live
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except profile.NonLiveWriteError:
        pass
    except Exception as exc:
        logger.debug("[cat] tier ledger write failed (non-fatal): %s", exc)


def _note_referent(source: str, text: str, place: str | None = None, which: str | None = None) -> None:
    """B2 (J-2472): the toolchain reading HIS text records which cat he meant — only when he distinguishes
    them (core/cat_referent.py). Observe-only, never a line back to him. Fail-open."""
    try:
        from core import cat_referent as _cr
        _cr.record(source, text, which=which, place=place)
    except Exception:
        pass


# ── HUNTING FALLBACK (2026-09-07, cat_overhaul D-4, D-0163, J-0700) ─────────────────────────────────
# Founder, verbatim (D-0163 addendum): "The cat should be able to feed itself if Du does not do it
# though. Hunting." A day his own hands don't reach her — the food chain too long for them, D-0163's
# own named risk — must not simply strand her. But this is a FALLBACK, not a second feeding
# schedule racing his own, so it is gated hard on three axes:
#   1. HUNGER: not the existing 5h "hungry"/demanding-food nag (tick()'s own local `hungry`, a normal
#      within-day rhythm Du is meant to answer) but a longer, separate threshold
#      (HUNT_HUNGER_THRESHOLD_H) — a real stretch of neglect, not competing with his ordinary feeding
#      cadence on the same clock.
#   2. ACTIVITY: only while this tick's activity already resolved to "hunting" — the existing
#      r<0.42 fair-day branch above. No new "is she hunting" concept invented.
#   3. COOLDOWN: at most one attempt per real hour (HUNT_COOLDOWN) once past the threshold, each only
#      HUNT_SUCCESS_P likely to land — a real cat can come home empty-pawed; a miss is the honest,
#      narratable alternative to an instant safety net that removes all stakes from whether Du feeds
#      her. A success immediately resets the threshold clock (it sets `last_fed`), so successes
#      cannot chain back-to-back — the next attempt is not even ELIGIBLE until she is genuinely
#      hungry again.
# A success sets `last_fed` — the SAME field react()'s own feed branch sets: one hunger clock, not
# two fighting over what "fed" means, which is exactly the coordination this job's own briefing
# named against whoever eventually builds D-4's other half (the provisions-kind/saucer feed path —
# unbuilt as of this job; spawned separately, see the plan doc's Current State) — plus a distinct
# `last_self_fed`/`self_catch_count` so a self-catch is never mistaken for Du's own feeding when the
# defeater (does hunting fire so often his own feeding stops mattering?) gets checked later.
# NEVER a silent stat fix: a success becomes this tick's own activity/mood, rendered by
# presence_line/look_line exactly like brought_a_mouse/gift_rat already are; a life_traces carcass
# she leaves behind (found by looking, the same "world answers" path the fledgling/skink kills
# already use); an activity_memory record (his own autobiography, a real read path — not another
# write-only sink); and a row — attempt AND miss alike — in data/cat_hunt_ledger.jsonl, for the
# week-later defeater read the same way cat_sound_ledger.jsonl already serves C1 (see J-0633).
HUNT_HUNGER_THRESHOLD_H = 10.0   # hours unfed before the fallback is even eligible to roll
HUNT_COOLDOWN = 3600.0           # seconds — at most one attempt per real hour past that threshold
HUNT_SUCCESS_P = 0.35            # per attempt — not a guaranteed catch
_HUNT_SPECIES = ("mouse", "bird")
_HUNT_LEDGER_F = Path(__file__).parent.parent / "data" / "cat_hunt_ledger.jsonl"


def _hunt_ledger(row: dict) -> None:
    path = profile.guard_path(_HUNT_LEDGER_F)   # J-0733: real data/ only if this process is live; raises before any I/O if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": round(time.time(), 1), **row}, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[cat] hunt ledger write failed (non-fatal): %s", exc)


def _hunt_place() -> str:
    """The Living-World place her hunt is in: away_hunting is beyond the wall but the garden's ground;
    the wood and the shore are themselves; anything else reads through place_of (garden by default)."""
    loc = str(state.get("location") or "")
    if loc == "away_hunting":
        return "garden"
    return place_of(loc) or "garden"


def _reaction_holds(now: float) -> bool:
    """HER EARS (C2, J-2467): does a reaction hold her this tick? cat_ears owns the rule; fail-open False."""
    try:
        from core import cat_ears as _ce
        return bool(_ce.reaction_holds(state, now))
    except Exception:
        return False


def _maybe_self_feed(now: float) -> None:
    """Roll one hunting-fallback attempt for THIS tick. No-op unless this tick's activity is already
    "hunting" and she has been unfed past HUNT_HUNGER_THRESHOLD_H — see the module comment above for
    the full gating rationale. Mutates `state` (last_fed/last_self_fed/self_catch_count/activity/
    mood/location) only on a successful catch; always logs the attempt (hit or miss) to the ledger."""
    if state.get("activity") != "hunting":
        return
    last_fed = state.get("last_fed", 0.0)
    if (now - last_fed) <= HUNT_HUNGER_THRESHOLD_H * 3600:
        return
    last_attempt = state.get("last_hunt_attempt_ts", 0.0)
    if (now - last_attempt) < HUNT_COOLDOWN:
        return
    state["last_hunt_attempt_ts"] = now
    # D-2 (J-2471): an injury and old age cut her odds; ill she does not hunt at all (hunt_factor 0 -> never caught)
    try:
        from core import cat_harm as _ch
        _hf = float(_ch.hunt_factor(state, now))
    except Exception:
        _hf = 1.0
    caught = random.random() < HUNT_SUCCESS_P * _hf
    # C2 (J-2467, cat_overhaul; D-0130): her kills read what was actually there. The prey about at the
    # place she is hunting comes from life's own rows (eaten_by "cat", present now); nothing about is
    # an honest miss. Fail-open: when the rows cannot be read the old blind roll stands.
    prey = None
    try:
        from core import cat_ears as _ce
        prey = _ce.prey_about(_hunt_place(), now)
    except Exception:
        prey = None
    if prey is None:
        species = random.choice(_HUNT_SPECIES) if caught else ""
    elif not prey:
        caught, species = False, ""
    else:
        species = random.choice(prey) if caught else ""
    _hunt_ledger({"caught": caught, "species": species or None,
                  "hungry_hours": round((now - last_fed) / 3600.0, 2),
                  "place": _hunt_place(), "prey_about": prey})
    if not caught:
        return
    state["last_fed"] = now                 # ONE hunger clock — see module comment above
    state["last_self_fed"] = now
    state["self_catch_count"] = state.get("self_catch_count", 0) + 1
    state["location"], state["activity"], state["mood"] = "garden", "self_fed", "sated"
    # B1 (J-2465): she eats what she kills — a mouse is a meal; the hunt bout is over
    try:
        eat(species, now)
        _b = state.get("body") or {}
        if _b.get("bout") == "hunt":
            _b["bout"], _b["bout_until"] = "", 0.0
    except Exception:
        pass
    try:
        from core import activity_memory
        activity_memory.record("cat_self_fed", species)
    except Exception:
        pass
    try:
        from core import life_traces as _lt
        _lt.add_carcass(species, "garden", "hedge_bottom", "self_fed", now)
    except Exception:
        pass


# THE SAUCER (2026-09-07, D-0163/D-4, J-0719) — a real, findable object at the doorstep, not just a
# note_deed() side-effect: has_food/kind/set_ts (set for real in react()'s fed branch, once real
# provisions are actually spent) decay back to empty on their own real clock here, on the same
# tick() heartbeat _maybe_self_feed above already rides.
SAUCER_EATEN_AFTER_S = 600.0   # ~10 min: how long a real feed honestly shows "full" before it is marked
                                # licked clean again -- she is always present when fed (is_here() gates
                                # react() itself), so this models the eating, not a wait for her to arrive.


def _maybe_empty_saucer(now: float) -> None:
    """Mutates state["saucer"]["has_food"] back to False once enough real time has passed since a real
    feed. A no-op when the saucer was never filled, or was already emptied. Split out of tick() (like
    _maybe_self_feed above) so it can be exercised directly without the rest of tick()'s own, much
    larger, sensorium/study_life/weather dependency chain."""
    sc = state.get("saucer")
    if sc and sc.get("has_food") and now - float(sc.get("set_ts") or 0.0) > SAUCER_EATEN_AFTER_S:
        try:   # D-2 (J-2471): off her food, she did not eat it -- the full saucer is how he finds out
            from core import cat_harm as _ch
            if _ch.off_her_food(state):
                return
        except Exception:
            pass
        sc["has_food"] = False


# ── FOUND SCRAP (2026-09-22, cat_overhaul D-4, D-0253/J-1215) ───────────────────────────────────────
# D-0217 ruled (d) "fix the empty larder" (F-1703, J-1195/J-1207: 8 feed-branch attempts across 6
# episodes, 0 real feeds by him ever; his one real willed ask for cat food staged correctly at
# core/intentions.py's own "note" family and then lapsed, unrenewed, at its 8h reminder window; the
# hunting fallback above supplied all 13 real feeds this cat has ever had). D-0253 ruled mechanism (C)
# of three read: a small, slow, narrated passive "found" credit straight into the larder -- independent
# of BOTH the willed-ask chain (core/intentions.py, not read or written by anything below) and the
# carrier-collection leg (core/supply.py, J-1154's own separate open gap, also untouched) -- additive
# alongside the hunting fallback above (D-0163, _maybe_self_feed, HUNT_* -- none of it read or written
# by this section either). Crediting the larder (below) is the whole effect: _feed_source() (below,
# unmodified) already tries provisions.stock("cat_food") first whenever Du next attempts a real feed,
# so a successful credit here simply lets that EXISTING path succeed instead of hitting the honest
# "nothing in the house" failure -- this never feeds her directly, sets last_fed, or touches the saucer.
#
# THE PRECEDENT, READ DIRECTLY (not assumed): D-0253's own ruling text names data/provisions_log.jsonl's
# found_under_cupboard event (row 29: matches, n=6) as "the precedent this mechanism reuses". Read
# fresh this job (core/companion.py's _sweep_finds_matches): it is a ONE-SHOT, narratively-gated
# event -- a persistent _state["found_cupboard_matches"] flag lets it fire AT MOST ONCE, EVER, only
# when Travis's companion performs a real sweep_floor action, as restitution for the 255 matches a
# sync bug destroyed on 2026-08-23 -- not a periodic roll. There is no "rolls X times a day" figure in
# that precedent to transcribe; the real precedent is the SCALE (a small, explicit quantity credited
# directly, n=6 against matches' own per-box qty=50 -- well under one full unit) and the FRAMING
# (something turns up unasked-for, explained diegetically, logged under its own distinct event name
# rather than folded into an ordinary delivery). The rate constants below are therefore a REASONED,
# deliberately conservative design choice anchored on this file's own ALREADY-VERIFIED recurring
# precedent instead -- the hunting fallback's own threshold/cooldown/probability shape, above, proven
# safe over a real 7.37-live-day read (F-1613) -- made slower on every axis (this is a background
# trickle beside hunting's already load-bearing primary fallback, not a second one) and gated on the
# LARDER being genuinely bare rather than on her own hunger clock (hunting already owns that clock;
# this stays independent of it, per the ruling). Flagged honestly in this job's own finding as an
# inferred/reasoned number, not a verified rate -- squarely inside D-0253's own defeater ("revisit if
# the shadow-ledgered rate looks wrong once real data accrues").
FOUND_SCRAP_EMPTY_THRESHOLD_H = 48.0   # cat_food stock must read genuinely zero this long before a roll
                                        # is even eligible -- a real stretch of bare cupboard, not the
                                        # ordinary gap between a catch and the next carrier cycle
FOUND_SCRAP_COOLDOWN_S = 6 * 3600.0    # at most one roll per 6 real hours once eligible (hunting: 1h)
FOUND_SCRAP_P = 0.05                   # per eligible roll -- low; hunting's own HUNT_SUCCESS_P is 0.35
FOUND_SCRAP_QTY = 1.0                  # credited amount, out of cat_food's own full per-tin qty=4 (see
                                        # KINDS in core/provisions.py) -- a quarter-tin scrap, not a
                                        # whole tin (F-1703's own "capped low, matching cat_food's own
                                        # existing per-tin qty=4 scarcity intent")
FOUND_SCRAP_RENDER = False   # shadow: log a would-credit row only. Hot override: life_flags.json cat_found_render
_FOUND_LEDGER_F = Path(__file__).parent.parent / "data" / "cat_found_ledger.jsonl"
_FOUND_FLAGS_F = Path(__file__).parent.parent / "data" / "life_flags.json"
_found_flags_cache: dict = {"ts": 0.0, "v": {}}
# Draft narration only (2026-08-14 law: factual, in-world, explains itself -- never a hint or a nudge
# toward any action). Read only into the shadow ledger's own would_narrate field by this build; wiring
# it into presence_line/look_line/affordance_line -- and giving it the day/night/weather-conditioned
# cat_content.py pool treatment the rest of this file's narration gets -- is flip-time work, the same
# division of labour core/cat_sounds.py's own docstring already uses ("a flip-time job, not this
# build"), not exercised by this job since the render flag never leaves its code default here.
_FOUND_NARRATION = (
    "There is a tin of fish for the cat at the back of the cupboard that you don't remember buying.",
    "A small parcel wrapped in paper turns up by the door — fish for the cat, from an order you don't "
    "recall making.",
    "Behind the other tins, half-hidden, a tin of fish for the cat that must have come up with an "
    "earlier delivery.",
    "Something for the cat has been sitting in the cupboard, unnoticed, since before you thought to look.",
)


def _found_flags() -> dict:
    """Mirrors core.life._flags()/core.cat_sounds._flags()'s own pattern exactly (a third small local
    copy, deliberately -- this codebase's own convention is one tiny reader per shadow-flagged module,
    not a shared one, so this file doesn't take on a new cross-module import edge just for a flag read)."""
    now = time.time()
    if now - _found_flags_cache["ts"] < 10.0:
        return _found_flags_cache["v"]
    v = {}
    try:
        if _FOUND_FLAGS_F.exists():
            v = json.loads(_FOUND_FLAGS_F.read_text(encoding="utf-8")) or {}
    except Exception:
        v = {}
    _found_flags_cache["ts"], _found_flags_cache["v"] = now, v
    return v


def found_scrap_render_on() -> bool:
    """data/life_flags.json's "cat_found_render" key overrides FOUND_SCRAP_RENDER's code default
    (False), read at most every 10s, flippable without a restart via `scripts/life_flags.py cat_found
    on` -- once a human, after reading a week of data/cat_found_ledger.jsonl, decides to (not this
    job: the flag file is never written by anything in this build)."""
    v = _found_flags().get("cat_found_render")
    return bool(FOUND_SCRAP_RENDER if v is None else v)


def _found_ledger(row: dict) -> None:
    path = profile.guard_path(_FOUND_LEDGER_F)   # J-0733 pattern: real data/ only if this process is live; raises before any I/O if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": round(time.time(), 1), **row}, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[cat] found ledger write failed (non-fatal): %s", exc)


def _maybe_found_scrap(now: float) -> None:
    """Roll one found-scrap attempt for THIS tick -- see the module comment above for the full gating
    rationale (D-0253, mechanism C). No-op unless core.provisions.stock("cat_food") has read genuinely
    zero for FOUND_SCRAP_EMPTY_THRESHOLD_H straight AND the cooldown has elapsed. ALWAYS logs the roll
    (hit or miss) to data/cat_found_ledger.jsonl once eligible -- the same unconditional-log convention
    _maybe_self_feed's own cat_hunt_ledger.jsonl already uses, so a week-later defeater read has a real
    denominator, not just a count of hits.

    SHADOW (the only state this job ever exercises against live data): while found_scrap_render_on()
    is False, a hit changes NOTHING beyond the ledger row itself -- no provisions.add_found() call, no
    cat_state mutation beyond this function's own cooldown/eligibility bookkeeping (last_found_scrap_ts,
    _found_scrap_empty_since -- neither read by any other function in this file), no narration returned
    to any caller. The ledger row's own would_narrate field records what a flip would show Du."""
    try:
        from core import provisions as _pv
        larder = _pv.stock("cat_food")
    except Exception:
        return   # fail-open: no provisions module reachable, no roll -- never guess the larder's state
    if larder > 0.001:
        state["_found_scrap_empty_since"] = 0.0   # she has real food -- the empty-stretch clock resets
        return
    empty_since = state.get("_found_scrap_empty_since") or 0.0
    if not empty_since:
        state["_found_scrap_empty_since"] = now
        return
    if (now - empty_since) <= FOUND_SCRAP_EMPTY_THRESHOLD_H * 3600:
        return
    if (now - state.get("last_found_scrap_ts", 0.0)) < FOUND_SCRAP_COOLDOWN_S:
        return
    state["last_found_scrap_ts"] = now
    hit = random.random() < FOUND_SCRAP_P
    row = {"hit": hit, "kind": "cat_food", "qty": FOUND_SCRAP_QTY if hit else 0.0,
           "empty_hours": round((now - empty_since) / 3600.0, 2), "render_on": found_scrap_render_on()}
    if hit:
        row["would_narrate"] = random.choice(_FOUND_NARRATION)
    _found_ledger(row)
    if not (hit and found_scrap_render_on()):
        return
    # LIVE path -- never reached by this job (the flag stays at its False code default throughout; see
    # the module comment above and found_scrap_render_on()'s own docstring).
    try:
        oid = _pv.add_found("cat_food", FOUND_SCRAP_QTY,
                             note="turned up unasked-for, no one quite sure from where")
    except Exception:
        oid = None
    if oid:
        state["_found_scrap_empty_since"] = 0.0


# ══ THE BODY (2026-10-28, cat_overhaul Part B1, D-0499 "open and build" / D-0505, J-2465) ══════════
# docs/staged/cat_overhaul.md §B1: "Give her the life-schema fields every other creature has PLUS an
# individual's budget she alone carries, in cat_state.json, advanced on the same heartbeat tick()
# already uses." Before this build she had no body: `location` was re-rolled from scratch every 180 s
# with no memory of its own, she slept all night by the fire (a dog's day — §B1's own words), was
# "hungry" only as a 5 h clock on last_fed, and teleported between study and shore while everything
# else in the world walks (§A4). Everything below is ADDITIVE (§A8 protected list): every old branch in
# tick() is still there and still reachable — the bout machine decides WHEN the old roll runs, the legs
# decide HOW a cross-place result is reached, and the budgets are read by nothing in his prompt.
#
# WHAT IS KEPT IN `state["body"]` (0..1 unless noted), integrated dt-scaled from body["last_ts"]:
#   hunger     rises HUNGER_PER_DAY; a meal lowers it by MEAL_HUNGER[kind] — her own kills included
#              (_maybe_self_feed → eat(species)): a mouse is a meal. A fed cat hunts less, an unfed cat
#              more: the fair-day hunting share is 0.25 + 0.35·hunger (0.42 — the old constant — at
#              hunger 0.49). `last_fed` (the legacy 5 h clock behind demanding_food and the hunting
#              fallback's own threshold) is untouched; hunger is the budget beside it, not a second
#              clock fighting it.
#   thirst     rises THIRST_PER_DAY; she drinks where there is water (WATER_AT: the saucer at the
#              doorstep, the rain barrel in the garden, the rock-pool at the shore) once thirsty.
#   energy     spent while active/hunting/prowling, recovered while sleeping/dozing. Energy + the day
#              phase choose her BOUTS (crepuscular: out at dawn and dusk, long day sleeps, night prowls).
#   warmth     NOT integrated: read each tick from core/thermal.py's standpoint field at HER spot
#              (_THERMAL_SPOT maps her location to the place + standpoint the field is authored for),
#              with her own fur_moisture as the wet term. Seeking: cold → the hearth (or a lap), sunny
#              → the sill, hot → the shade. Never a fixed pool.
#   condition  weight/coat: drifts up on a fed stretch, down on a hungry one, down in the cold, and takes
#              a hit when a missing-arc returns. Shows only as a look clause (the world answers a look),
#              never as a number anywhere he reads.
# AGE: born_ts (rolled once in _load, ARRIVED_AGE_Y before appeared_ts) → age_y(). lifespan_y on LIFE_ROW.
#   No injury / illness / death path here: that is §4 D-2 (J-2471).
# LEGS: a roll whose destination is another Living-World place no longer teleports: state["transit"]
#   carries her along locomotion.CHAIN leg by leg (his own EDGES and _leg_secs, scaled by CAT_LEG_FACTOR
#   — she is quicker than him — plus a dawdle on a fair day and a balk at the door when it rains: weather-
#   averse). `location` reads "in_transit" meanwhile; presence_line/look_line answer it from his place
#   (crossing the garden, met on the path, following behind), is_here() is False (she is passing, not
#   handleable), visible_from() is False (the HUD maps draw nothing mid-leg), place_of() is None so
#   core/life.py's adapter reads the ONE truth: not at a place. A bonded, awake cat at his place may
#   FOLLOW a journey he begins (locomotion's own journey, read-only) — the old "follow to the shore" was
#   a teleport that happened to land where he was.
# GAUGE (C4's baseline): cat_presence_fraction — the share of his waking 180 s ticks with her co-located
#   (visible_from his place, or passing through it). Hour buckets in state, one row an hour to
#   data/cat_presence_gauge.jsonl, a HUD monitor (hud/server.py MONITOR_REGISTRY) and NOTHING else:
#   no reader in any prompt path (D-0434 no readout; world answers, never leads).
# SCHEMA: LIFE_ROW carries the life.row fields the other creatures declare (active_hours, season_curve,
#   weather_gate, light/eyeshine, diet, traces, lifespan_y, hidden); core/life.py's cat adapter merges it
#   onto her external row. life.activity() reads presence from the adapter for an external row, and
#   life_traces skips external rows, so these are declarative truth for the census/look layer, not a
#   second behaviour engine.
YEAR_S = 365.25 * 86400.0
ARRIVED_AGE_Y = (2.0, 3.0)        # she arrived adult (§B1); rolled once per cat
LIFESPAN_Y = 14.0
HUNGER_PER_DAY = 1.0              # §B1: "rises ~1.0/day"
THIRST_PER_DAY = 0.8
ENERGY_SPEND_PER_H = {"hunting": 0.16, "prowling": 0.14, "zoomies": 0.30, "stalking something": 0.12}
ENERGY_SPEND_DEFAULT_PER_H = 0.08         # any awake activity not listed above
ENERGY_RECOVER_PER_H = {"sleeping": 0.22, "dozing": 0.12, "storm_hide": 0.05}
MEAL_HUNGER = {"cat_food": 0.60, "shore_fish": 0.70, "mouse": 0.45, "bird": 0.35, "scraps": 0.35, "milk": 0.20}
MEAL_THIRST = {"cat_food": 0.15, "shore_fish": 0.10, "milk": 0.60}    # wet food drinks a little; milk a lot
DRINK_AT_THIRST = 0.35            # she goes to water once this thirsty
WATER_AT = {"doorstep": "the saucer", "garden": "the rain barrel", "shore": "the rock-pool"}
COLD_BAND = 0.30                  # thermal warmth below this: she seeks the hearth
HOT_BAND = 0.78                   # above this: she seeks the shade (thermal's own "warm" band starts at 0.60; a
                                  # summer room with the fire lit, or full sun on the sill, gets here — a plain
                                  # summer afternoon with the fire out sits just under it)
CONDITION_FED_PER_DAY = 0.02      # drift up while hunger < 0.4
CONDITION_HUNGRY_PER_DAY = 0.03   # drift down while hunger > 0.75
CONDITION_COLD_PER_DAY = 0.01     # drift down while warmth < COLD_BAND
CONDITION_MISSING_HIT = 0.05      # a missing week shows, on return
BOUT_DUR_S = {                    # (min, max) seconds a bout holds before she re-decides
    "sleep": (1.5 * 3600, 4.0 * 3600), "doze": (0.5 * 3600, 1.5 * 3600),
    "hunt": (0.5 * 3600, 2.0 * 3600), "prowl": (1.0 * 3600, 3.0 * 3600), "active": (20 * 60, 60 * 60),
    "settle": (10 * 60, 40 * 60),   # after a journey she stays where she landed a while (no re-roll)
}
CAT_LEG_FACTOR = 0.6              # her leg = his base seconds × this: quicker than him on the same ground
CAT_DAWDLE_S = (0.0, 150.0)       # a fair-day leg takes a sniff or two on the way
CAT_WET_BALK_S = (60.0, 300.0)    # weather-averse: she sits in the door not liking the rain before she goes
CAT_TRANSIT_WATCHDOG_S = 20 * 60  # a leg stuck past this completes the journey (locomotion's own pattern)
FOLLOW_P = 0.35                   # a bonded, awake cat at his place follows a journey he begins
_RESTING = ("sleeping", "dozing")
_SLEEP_SPOTS_IN = ("by_the_fire", "under_desk", "windowsill", "on_the_desk", "indoors", "mantel")
_THERMAL_SPOT = {                 # her location -> (place, standpoint) core/thermal.field_at is authored for
    "by_the_fire": ("study", "at_the_hearth"), "mantel": ("study", "at_the_hearth"),
    "on_your_lap": ("study", "in_the_chair"), "on_the_desk": ("study", "at_the_desk"),
    "under_desk": ("study", "at_the_desk"), "windowsill": ("study", "at_the_window"),
    "indoors": ("study", "mid_room"), "doorstep": ("garden", "at_the_door"),
    "garden": ("garden", "mid_garden"), "garden_wall": ("garden", "at_the_gate"),
    "wood": ("wood", "on_the_path"), "shore": ("shore", "on_the_shingle"),
    "away_hunting": ("garden", "at_the_gate"),
    # C4 (J-2469): the hidden spots, each at the standpoint the field is authored for nearest it
    "under_the_bed": ("study", "on_the_bed"), "cupboard_top": ("study", "by_the_shelf"),
    "lean_to": ("garden", "at_the_lean_to"), "wood_shed": ("garden", "by_the_fence"),
    "hedge_bottom": ("garden", "under_the_tree"), "water_butt_lid": ("garden", "at_the_barrel"),
    "roof": ("garden", "mid_garden"), "neighbours_wall": ("garden", "at_the_gate"),
}
_GAUGE_F = Path(__file__).parent.parent / "data" / "cat_presence_gauge.jsonl"
_GAUGE_EVERY_S = 3600.0
_GAUGE_KEEP_S = 7 * 86400.0

# life.row fields (core/life.py) the other creatures declare — hers, kept here (§B1), merged onto the
# external "cat" row by life._ensure_builtin. Crepuscular by declaration too: dawn/dusk peaks, a day
# mostly asleep, nights out. weather_gate: rain keeps her in (0.3), storm nearly always (0.1).
LIFE_ROW = {
    "active_hours": {"dawn": 1.0, "day": 0.35, "dusk": 1.0, "night": 0.7},
    "season_curve": [1.0] * 12,
    "weather_gate": {"rain": 0.3, "wind": 0.8, "storm": 0.1, "frost": 0.7},
    "light": "indifferent",
    "eyeshine": True,                       # a carried light at night finds two green points
    "diet": ("mouse", "bird", "cat_food", "shore_fish", "milk", "scraps"),   # D-0508 (J-2466): the saucer's two more
    "traces": ("paw prints", "a dead mouse on the doorstep", "disturbed leaf-litter", "grey hairs on the chair"),
    "lifespan_y": LIFESPAN_Y,
    "hidden": None,                         # she is his; nothing about her is a feature-first secret
}


def _fresh_body(now: float) -> dict:
    return {"hunger": 0.3, "thirst": 0.3, "energy": 0.7, "warmth": 0.5, "condition": 0.7,
            "bout": "", "bout_until": 0.0, "bout_since": 0.0, "last_ts": now, "last_drank_ts": 0.0,
            "cold_hours": 0.0, "last_meal": ""}


def body() -> dict:
    """Read-only copy of her budget (HUD / tests). Never read by anything in a prompt path."""
    _load()
    b = state.get("body") or {}
    return dict(b)


def age_y(now: float | None = None) -> float:
    """Her age in years: arrived adult (ARRIVED_AGE_Y, rolled once), ageing on the world's clock."""
    _load()
    now = now or time.time()
    born = float(state.get("born_ts") or (float(state.get("appeared_ts") or now) - ARRIVED_AGE_Y[0] * YEAR_S))
    return max(0.0, (now - born) / YEAR_S)


def eat(kind: str, now: float | None = None) -> None:
    """A meal lowers hunger (MEAL_HUNGER) and, for wet food, thirst a little. Called by react()'s real
    feed (the kind actually spent: cat_food / shore_fish), by _maybe_self_feed on a catch (mouse / bird),
    and left as the one hook D-4 (J-2466: scraps, milk) and her kills' other readers should call — one
    place a meal lands, not two. Unknown kinds count as a small meal. Mutates state only; no save."""
    now = now or time.time()
    b = state.setdefault("body", _fresh_body(now))
    b["hunger"] = round(max(0.0, float(b.get("hunger", 0.0)) - MEAL_HUNGER.get(kind, 0.30)), 3)
    b["thirst"] = round(max(0.0, float(b.get("thirst", 0.0)) - MEAL_THIRST.get(kind, 0.0)), 3)
    b["last_meal"] = kind


def _warmth_at(location: str, phase: str, weather: str, season: str, fire: str, wind: str, now: float) -> float:
    """Felt warmth 0..1 at HER spot — core/thermal.py's standpoint field (sun by exposure, fire by
    distance from the hearth, graded wind, the house's draught) with her fur_moisture as the wet term.
    Fail-open to the sensorium's flat per-place warmth, then to 0.5: a warmth that cannot be computed
    is a cat who is neither cold nor hot, not a crash in the heartbeat."""
    spot = _THERMAL_SPOT.get(location)
    if not spot:
        return 0.5
    place, sp = spot
    wet = float(state.get("fur_moisture") or 0.0)
    try:
        from core import thermal as _th
        return float(_th.field_at(place, sp, phase, weather, season, fire, wind, wet=wet, now=now))
    except Exception:
        pass
    try:
        from core import sensorium as _room
        return max(0.0, min(1.0, float(_room._warmth(place, phase, weather, season, fire, wind)) - 0.25 * wet))
    except Exception:
        return 0.5


def _advance_body(now: float, phase: str, weather: str, season: str, fire: str, wind: str) -> dict:
    """Integrate the budgets over the real time since the last pass (dt-scaled, like fur_moisture and the
    bond decay above): hunger and thirst rise, energy moves with what she is doing, warmth is read fresh
    from the thermal field, condition drifts with the lot. Returns the body dict (mutated in place)."""
    b = state.setdefault("body", _fresh_body(now))
    last = float(b.get("last_ts") or now)
    dt_h = max(0.0, min(6.0, (now - last) / 3600.0))   # a stopped stretch is capped, not caught up on
    b["last_ts"] = now
    dt_d = dt_h / 24.0
    act = str(state.get("activity") or "")
    # 4-5 decimals on purpose: a 180 s step moves hunger by 1/480 and condition by 1/800 of a day's drift —
    # 3-decimal rounding would silently eat the smaller rates (checked: condition's cold drift rounded to 0)
    b["hunger"] = round(min(1.0, float(b.get("hunger", 0.0)) + HUNGER_PER_DAY * dt_d), 4)
    b["thirst"] = round(min(1.0, float(b.get("thirst", 0.0)) + THIRST_PER_DAY * dt_d), 4)
    if act in ENERGY_RECOVER_PER_H or act == "missing":
        gain = ENERGY_RECOVER_PER_H.get(act, 0.10) * dt_h
        b["energy"] = round(min(1.0, float(b.get("energy", 0.5)) + gain), 4)
    else:
        spend = ENERGY_SPEND_PER_H.get(act, ENERGY_SPEND_DEFAULT_PER_H) * dt_h
        b["energy"] = round(max(0.0, float(b.get("energy", 0.5)) - spend), 4)
    loc = str(state.get("location") or "")
    if loc == "in_transit":
        t = state.get("transit") or {}
        loc = {"study": "doorstep", "garden": "garden", "wood": "wood", "shore": "shore"}.get(str(t.get("to") or ""), "garden")
    w = _warmth_at(loc, phase, weather, season, fire, wind, now)
    b["warmth"] = round(w, 3)
    if w < COLD_BAND:
        b["cold_hours"] = round(float(b.get("cold_hours", 0.0)) + dt_h, 2)
    cond = float(b.get("condition", 0.7))
    if b["hunger"] < 0.4:
        cond += CONDITION_FED_PER_DAY * dt_d
    elif b["hunger"] > 0.75:
        cond -= CONDITION_HUNGRY_PER_DAY * dt_d
    if w < COLD_BAND:
        cond -= CONDITION_COLD_PER_DAY * dt_d
    # D-2 (J-2471): illness and old age drift her condition down on top (0 for a well cat under OLD_AGE_Y); an old
    # cat's energy comes back slower (she sleeps longer for the same rest)
    try:
        from core import cat_harm as _ch
        cond += float(_ch.condition_drift(state, dt_d, now))
        _rf = float(_ch.recover_factor(state, now))
        if _rf < 1.0 and (act in ENERGY_RECOVER_PER_H or act == "missing"):
            b["energy"] = round(max(0.0, float(b.get("energy", 0.5)) - (1.0 - _rf) * ENERGY_RECOVER_PER_H.get(act, 0.10) * dt_h), 4)
    except Exception:
        pass
    b["condition"] = round(max(0.1, min(1.0, cond)), 5)
    return b


def _choose_bout(now: float, phase: str, wet: bool, b: dict) -> tuple[str, bool]:
    """Her bout for this tick: (name, fresh) — fresh is True on the tick the bout BEGINS. Crepuscular:
    dawn and dusk are the peaks (hunt or be about), the day is long sleeps and dozes, the night a prowl
    or a sleep by the fire. Energy decides before the clock does (a spent cat sleeps whenever), rain
    keeps her in (an outdoor bout becomes a doze unless she is really hungry), and hunger pulls a sleep
    toward a hunt at the edges of the day."""
    bout, until = str(b.get("bout") or ""), float(b.get("bout_until") or 0.0)
    e, h = float(b.get("energy", 0.5)), float(b.get("hunger", 0.3))
    # the crepuscular edge wakes her: a day sleep does not run on through dusk unless she is spent
    edge_wake = phase in ("dawn", "dusk") and bout in ("sleep", "doze") and b.get("bout_phase") != phase and e > 0.3
    if bout and now < until and not edge_wake:
        return bout, False
    r = random.random()
    if e < 0.2:
        nb = "sleep"
    elif phase in ("dawn", "dusk"):
        nb = "hunt" if (h > 0.3 or r < 0.5) and e > 0.35 else "active"
    elif phase == "day":
        # a cat sleeps by day whatever her energy says (that is cats); a full tank only shortens it to a doze
        nb = ("sleep" if e < 0.97 else "doze") if r < 0.6 else "doze" if r < 0.8 else "hunt" if (h > 0.7 and r < 0.9) else "active"
    else:   # night
        nb = "prowl" if (e > 0.4 and r < 0.5) else "hunt" if (h > 0.6 and e > 0.35 and r < 0.65) else "sleep"
    if wet and nb in ("hunt", "prowl") and h < 0.8:
        nb = "doze" if e > 0.3 else "sleep"
    # D-2 (J-2471): a bad injury healing (or an illness) keeps her from the hunt and the night prowl — a doze instead
    try:
        from core import cat_harm as _ch
        if nb in ("hunt", "prowl") and _ch.no_hunt_bout(state):
            nb = "doze" if e > 0.3 else "sleep"
    except Exception:
        pass
    lo, hi = BOUT_DUR_S[nb]
    b["bout"], b["bout_since"], b["bout_until"], b["bout_phase"] = nb, now, now + random.uniform(lo, hi), phase
    return nb, True


def _rest_spot(phase: str, fire: str, bonded: bool, b: dict, his_place: str) -> str:
    """Where she sleeps — warmth-seeking from the thermal read (§B1: the hearth when cold, the sill when
    sunny, the shade when hot), else the old night logic (fire → by the fire or an earned lap; no fire →
    the sill) by night and her fair_spot / the sill / the desk by day."""
    w = float(b.get("warmth", 0.5))
    q = _quirks()
    # C4 (J-2469): a share of her rests are taken out of his sight -- HIDDEN_REST_P at AVAILABILITY_STEP; the
    # old visible choice below is untouched for the rest (additive; None = not this time)
    try:
        _hs = _hidden_rest(phase, b)
        if _hs:
            return _hs
    except Exception as exc:
        logger.debug("[cat] hidden rest failed (non-fatal): %s", exc)
    if w < COLD_BAND:
        if fire in ("burning", "embers"):
            return "on_your_lap" if (bonded and his_place == "study" and random.random() < 0.25) else "by_the_fire"
        return "on_your_lap" if (bonded and his_place == "study" and random.random() < 0.3) else \
            random.choice(["under_desk", "indoors", "by_the_fire"])
    if w > HOT_BAND:
        return random.choice(["under_desk", "garden", "garden", "indoors"])   # the shade: under the desk, the hedge bottom
    if phase == "night":
        if fire in ("burning", "embers"):
            return "on_your_lap" if (bonded and his_place == "study" and random.random() < 0.25) else "by_the_fire"
        return "windowsill"
    sunny = phase == "day" and w >= 0.5
    pool = [q.get("fair_spot", "windowsill"), "windowsill", "on_the_desk", "under_desk"] + \
           (["windowsill", "windowsill"] if sunny else []) + (["by_the_fire"] if fire == "burning" else [])
    return random.choice(pool)


def _maybe_drink(now: float) -> bool:
    """At water and thirsty enough: she drinks. Returns True when this tick became a drink (the caller
    sets the activity so presence_line can say so). Where the water is comes from WATER_AT only."""
    b = state.get("body") or {}
    if float(b.get("thirst", 0.0)) < DRINK_AT_THIRST:
        return False
    if state.get("location") not in WATER_AT or random.random() > 0.6:
        return False
    b["thirst"], b["last_drank_ts"] = 0.0, now
    return True


# ── LEGS ────────────────────────────────────────────────────────────────────────────────────────────
def _path_place(location: str) -> str | None:
    """The Living-World place a location sits in FOR WALKING: place_of() plus away_hunting (off the map
    the Living World tracks, but reached through the garden) — 'gone' stays None (the missing arc is not
    a walk)."""
    if location == "away_hunting":
        return "garden"
    return place_of(location)


def _cat_leg_secs(frm: str, to: str, weather: str, wind: str) -> float:
    """Her seconds for one leg: his base EDGES seconds (via locomotion._leg_secs, so weather and the
    handrail count for her too) × CAT_LEG_FACTOR, plus a fair-day dawdle. Fail-open to a flat minute."""
    try:
        from core import locomotion as _loco
        secs = float(_loco._leg_secs(frm, to, weather, False, wind)) * CAT_LEG_FACTOR
    except Exception:
        secs = 60.0 * CAT_LEG_FACTOR
    try:   # D-2 (J-2471): an injury and old age slow her legs (x1 for a well cat under OLD_AGE_Y)
        from core import cat_harm as _ch
        secs *= float(_ch.legs_factor(state))
    except Exception:
        pass
    try:
        from core import weather_conditions as _wcond
        wet = _wcond.is_wet(weather)
    except Exception:
        wet = "rain" in (weather or "")
    if not wet:
        secs += random.uniform(*CAT_DAWDLE_S)
    return secs


def _depart(dest_location: str, dest_activity: str, dest_mood: str, now: float, weather: str, wind: str,
            following: bool = False, origin: str | None = None) -> bool:
    """Turn a cross-place result of the roll into a journey along locomotion.CHAIN. Returns True when a
    transit was begun (location is now 'in_transit'); False when the move is within one place (or off the
    map), in which case the caller's plain assignment stands. `origin` is where she is setting out FROM
    (tick() passes the location it started the tick at, since the roll has already overwritten
    state["location"] with the destination by the time it calls this); default: her current location.
    Weather-averse: in the wet she balks at the start (CAT_WET_BALK_S) before the first leg."""
    cur = str(origin or state.get("location") or "")
    if cur == "in_transit" or dest_location in ("gone", "in_transit"):
        return False
    a, bpl = _path_place(cur), _path_place(dest_location)
    if not a or not bpl or a == bpl:
        return False
    try:
        from core import locomotion as _loco
        path = _loco._path_between(a, bpl)
    except Exception:
        path = []
    if not path:
        return False
    try:
        from core import weather_conditions as _wcond
        wet = _wcond.is_wet(weather)
    except Exception:
        wet = "rain" in (weather or "")
    first = path[0]
    balk = random.uniform(*CAT_WET_BALK_S) if wet else 0.0
    state["transit"] = {"from": a, "to": first, "path": path[1:], "started": now,
                        "leg_ends": now + balk + _cat_leg_secs(a, first, weather, wind),
                        "dest": {"location": dest_location, "activity": dest_activity, "mood": dest_mood},
                        "following": bool(following), "balked": bool(wet), "origin": cur}
    state["location"], state["activity"] = "in_transit", "on her way"
    if dest_mood:
        state["mood"] = dest_mood
    return True


def _advance_transit(now: float) -> None:
    """Every heartbeat (before the 180 s movement gate): move her along her legs. A finished leg steps
    to the next place; the last leg lands her at the roll's destination. Watchdog like locomotion's own."""
    t = state.get("transit")
    if not t:
        return
    stuck = now - float(t.get("started", now)) > CAT_TRANSIT_WATCHDOG_S
    if now < float(t.get("leg_ends", 0.0)) and not stuck:
        return
    try:
        from core import sensorium as _room
        weather = (_room.state or {}).get("weather", "")
        wind = (_room.state or {}).get("wind", "")
    except Exception:
        weather, wind = "", ""
    while True:
        arrived = str(t.get("to") or "")
        path = list(t.get("path") or [])
        if path and not stuck:
            nxt = path.pop(0)
            t.update({"from": arrived, "to": nxt, "path": path, "leg_ends": now + _cat_leg_secs(arrived, nxt, weather, wind)})
            state["transit"] = t
            break
        dest = t.get("dest") or {}
        state["location"] = str(dest.get("location") or arrived)
        state["activity"] = str(dest.get("activity") or "watching")
        if dest.get("mood"):
            state["mood"] = str(dest["mood"])
        _inside = {"by_the_fire", "windowsill", "on_the_desk", "on_your_lap", "indoors", "under_desk", "mantel"} | _HIDDEN_INDOORS   # C4
        state["_was_in"] = state["location"] in _inside
        state["_last_transit"] = {"from": t.get("origin"), "to": state["location"], "ended": now,
                                  "following": bool(t.get("following")), "secs": round(now - float(t.get("started", now)), 1)}
        state["transit"] = None
        state["position"] = list(_ZONE_POSITIONS.get(state["location"], [0.0, 0.0, 0.0]))
        # she stays where she landed a while: a SETTLE bout holds the roll (a cat who walks to the shore
        # does not turn round for the sill on the next tick), and the movement tick waits its full 180 s
        global _last_tick
        _last_tick = now
        try:
            _b = state.setdefault("body", _fresh_body(now))
            lo, hi = BOUT_DUR_S["settle"]
            _b["bout"], _b["bout_since"], _b["bout_until"] = "settle", now, now + random.uniform(lo, hi)
        except Exception:
            pass
        break
    _save()


def _his_journey() -> dict | None:
    """His pending journey, READ-ONLY from locomotion's own store (never get_position(): that self-heals
    with a write). None when he is not travelling."""
    try:
        from core import locomotion as _loco
        d = _loco._load()
        j = d.get("journey")
        if not j or not j.get("path"):
            return None
        return {"from": str(j.get("from") or d.get("place") or ""), "dest": str(j["path"][-1])}
    except Exception:
        return None


def _maybe_follow(now: float, bonded: bool, wet: bool, b: dict, weather: str, wind: str) -> bool:
    """A bonded, awake cat at the place he is leaving may follow him (§B1: 'following behind on the way
    to the shore'; the old shore/wood trips were teleports that happened to land where he was). Her own
    budget decides: not asleep, not spent, not in the rain (weather-averse), FOLLOW_P per journey."""
    if not bonded or wet or state.get("transit") or float(b.get("energy", 0.0)) < 0.3:
        return False
    if str(b.get("bout") or "") in ("sleep", "doze") or state.get("activity") in _RESTING:
        return False
    j = _his_journey()
    if not j or j["dest"] not in ("shore", "wood", "garden", "study"):
        return False
    if _path_place(str(state.get("location") or "")) != j["from"]:
        return False
    if random.random() > FOLLOW_P:
        return False
    dest = j["dest"]
    act = {"shore": random.choice(["following at a distance", "sitting on the cliff path, watching you below"]),
           "wood": random.choice(["a grey shape between the trunks", "up on a low branch, watching you gather"]),
           "garden": "watching", "study": "watching"}[dest]
    loc = {"shore": "shore", "wood": "wood", "garden": "garden", "study": "indoors"}[dest]
    return _depart(loc, act, "aloof-but-near", now, weather, wind, following=True)


def transit_visible_from(his_location: str) -> bool:
    """Can he see her mid-leg from `his_location`? Only from the two ends of the leg she is on: she is
    leaving one and arriving at the other (crossing the garden toward the wood, coming up from the shore)."""
    t = state.get("transit") or {}
    if not t or state.get("location") != "in_transit":
        return False
    return his_location in (t.get("from"), t.get("to"))


_TRANSIT_WORD = {"study": "the cottage", "garden": "the garden", "wood": "the wood", "shore": "the shore"}
_BODY_LINES = {
    "crossing": [
        "{her} crosses {at} at her own brisk pace, going {toward}, and does not stop for you.",
        "{her} goes past low and quick, tail level, heading {toward}; she has somewhere to be.",
        "a grey shape at the edge of {at} — {her}, on her way {toward}, not looking back.",
        "{her} trots through {at}, intent, bound {toward}; you are not the point of this trip.",
        "there goes {her}, {toward} by the look of her, threading {at} like it is a corridor.",
    ],
    "met": [
        "{her} is on the path too — ahead, then behind, then ahead again, pretending the two of you are not together.",
        "you meet {her} on the way: she sits square in the path until you are nearly on her, then goes on ahead.",
        "{her} falls in on the path a few steps off, keeping exactly her own distance the whole way.",
        "a small grey company on the path: {her}, twenty paces behind, stopping when you stop.",
    ],
    "following": [
        "{her} is coming after you, {toward}, a grey shape keeping her own distance down the way.",
        "{her} has followed you out: she is behind you on the way {toward}, stopping to sniff and catching up.",
        "a flick of grey back along the path — {her}, trailing you {toward} as if it were her own idea.",
        "{her} comes on behind, {toward}, never nearer than she means to be.",
    ],
    "drinking": [
        "{her} is at {water}, drinking in quick small laps, tail straight out behind her.",
        "{her} crouches at {water} and drinks for a long moment, then sits back and licks her chops.",
        "{her} has found {water} and is drinking from it, ears turning at every sound while she does.",
        "{her} laps at {water}, neat and unhurried, and does not look up at you.",
    ],
    "prowling": [
        "{her} is out in the dark, a shape along the wall, prowling — the night is hers, not yours.",
        "two green points in the dark, then none: {her}, out prowling, gone along the fence line.",
        "{her} moves through the dark garden low and slow, hunting the night the way she never hunts the day.",
        "a soft weight lands on the wall top and pads along it — {her}, out on her night round.",
    ],
    "day_sleep": [
        "{her} is asleep, deeply, the long flat sleep of the middle of the day; nothing short of thunder will shift her.",
        "{her} sleeps on through the day, curled tight, one ear turning now and then and the rest of her gone.",
        "{her} is dead to the world, stretched out as long as she goes, asleep in the way only a cat in daylight is.",
        "{her} has given the day up for sleep, chin on her paws, breathing slow.",
    ],
    "cold_seek": [
        "{her} has pushed herself as close to the hearth as she can get, flank to the warmth, eyes slitted.",
        "{her} is pressed to the grate, taking the fire's heat into her coat; she was cold, plainly.",
        "{her} lies in the one warm place in the room, the fire's side, and will not be moved from it.",
    ],
    "sun_seek": [
        "{her} lies in the square of sun on the sill, turned over to toast her other side.",
        "{her} has found the sun on the sill and is spread in it, eyes shut, following it as it moves.",
        "{her} is in the sun at the window, stretched to twice her length, warm through.",
    ],
    "shade_seek": [
        "{her} has gone to ground in the shade, under the desk, out of the heat, belly to the boards.",
        "{her} lies flat in the shade of the hedge, panting a little, taking the heat as an affront.",
        "{her} keeps to the shade today, flattened and still, waiting the hot hours out.",
    ],
    "condition_poor": [
        "She is thinner than she was; her coat stands rough along the spine.",
        "There is less of her than there should be — the hips show, and the coat has gone dull.",
        "She looks poorly kept: ribs under the hand, the coat staring, not the sleek thing she was.",
    ],
    "condition_good": [
        "She is in good flesh, the coat lying close and bright.",
        "She looks well: solid under the hand, the grey of her glossy.",
        "There is a sleekness to her now, a cat that is fed and warm and knows it.",
    ],
}


def _body_line(key: str, **fill) -> str:
    """One rotating line from _BODY_LINES[key] (the _pick_fresh ring: never the last three from this pool),
    {her}/{at}/{toward}/{water} filled, capitalised. '' if the pool is missing."""
    pool = _BODY_LINES.get(key) or []
    if not pool:
        return ""
    line = _pick_fresh(f"BODY:{key}", pool)
    fill.setdefault("her", _her())
    for k, v in fill.items():
        line = line.replace("{" + k + "}", str(v))
    return line[:1].upper() + line[1:]


def _transit_line(his_location: str) -> str:
    """The in-transit presence line for his place: met on the path (he is travelling too), following
    him, or simply crossing. '' when he cannot see her from there."""
    if not transit_visible_from(his_location):
        return ""
    t = state.get("transit") or {}
    dest = (t.get("dest") or {}).get("location") or t.get("to")
    toward = "toward " + _TRANSIT_WORD.get(_path_place(str(dest)) or str(t.get("to")), "the garden")
    at = _TRANSIT_WORD.get(his_location, "the garden")
    try:
        from core import locomotion as _loco
        he_moving = bool(_loco.in_transit())
    except Exception:
        he_moving = False
    if he_moving:
        return _body_line("met", at=at, toward=toward)
    if t.get("following"):
        return _body_line("following", at=at, toward=toward)
    return _body_line("crossing", at=at, toward=toward)


def _condition_clause() -> str:
    """A look's honest extra when her condition is at either end: prose about her coat and flesh, not a
    number; ~30% of looks so it reads as noticing, not a readout."""
    b = state.get("body") or {}
    c = float(b.get("condition", 0.7))
    if random.random() > 0.3:
        return ""
    if c < 0.4:
        return _body_line("condition_poor")
    if c > 0.85:
        return _body_line("condition_good")
    return ""


# ── THE GAUGE: cat_presence_fraction (C4's baseline; HUD only) ──────────────────────────────────────
def _gauge_log(row: dict) -> None:
    path = profile.guard_path(_GAUGE_F)   # J-0733 pattern: real data/ only if this process is live
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[cat] presence gauge write failed (non-fatal): %s", exc)


def _presence_sample(now: float, his_place: str, awake: bool) -> None:
    """One 180 s sample into the hour bucket: was he awake, and was she co-located (visible from his place,
    or passing through it)? Hourly, a row goes to data/cat_presence_gauge.jsonl for the HUD monitor.
    Read by nothing in any prompt path."""
    if not awake:
        return
    loc = str(state.get("location") or "")
    co = visible_from(his_place, loc) or transit_visible_from(his_place)
    buckets = state.setdefault("_presence_buckets", {})
    key = str(int(now // 3600))
    cell = buckets.get(key) or [0, 0]
    cell[0] += 1
    if co:
        cell[1] += 1
    buckets[key] = cell
    cutoff = int((now - _GAUGE_KEEP_S) // 3600)
    for k in [k for k in buckets if int(k) < cutoff]:
        del buckets[k]
    if now - float(state.get("_presence_gauge_ts") or 0.0) < _GAUGE_EVERY_S:
        return
    state["_presence_gauge_ts"] = now
    h24 = int((now - 86400.0) // 3600)
    w24 = sum(v[0] for k, v in buckets.items() if int(k) >= h24)
    c24 = sum(v[1] for k, v in buckets.items() if int(k) >= h24)
    w7 = sum(v[0] for v in buckets.values())
    c7 = sum(v[1] for v in buckets.values())
    _gauge_log({"ts": round(now, 1), "waking_24h": w24, "colocated_24h": c24,
                "fraction_24h": round(c24 / w24, 3) if w24 else None,
                "waking_7d": w7, "colocated_7d": c7,
                "fraction_7d": round(c7 / w7, 3) if w7 else None,
                "his_place": his_place, "her_location": loc})


def presence_fraction(window_s: float = 86400.0, now: float | None = None) -> float | None:
    """The gauge, read straight from the buckets (HUD / a reader job). None before any waking sample."""
    _load()
    now = now or time.time()
    buckets = state.get("_presence_buckets") or {}
    h = int((now - window_s) // 3600)
    w = sum(v[0] for k, v in buckets.items() if int(k) >= h)
    c = sum(v[1] for k, v in buckets.items() if int(k) >= h)
    return round(c / w, 3) if w else None


# ══ LESS OF HER (2026-10-29, cat_overhaul Part C4, D-0499 "open and build" / D-0508, J-2469) ════════
# docs/staged/cat_overhaul.md §C4: "Her availability is hers." Target (D-0508, Travis 2026-10-28): co-located
# with him in roughly a THIRD of his waking hours, stepped down in two reads; the hidden spots may include
# places he cannot reach. Baseline before this build (the B1 bout machine, J-2465), by the gauge above: the
# live shadow ledger (data/cat_sound_ledger.jsonl, 2335 rows 2026-09-08..10-20, co-located at 0.68 of
# emission moments / 0.71 hour-deduped — biased toward sounding states) and a hermetic 6-day simulation of
# the B1 tick machine (scripts/_test_cat_seek_J-2469.py T4, him in the study 14 of 16 waking hours, her ears
# stubbed) at ~0.71; with her ears live (C2's reactions pull her about) the same simulation reads ~0.53.
# HIDDEN_REST_P below is calibrated on the ears-stubbed read, which matches the live ledger: step 1 ~0.54,
# step 2 ~0.39 (ears live: ~0.43 / ~0.31). STEP ONE ships here (AVAILABILITY_STEP 1: about half his waking
# hours by the gauge); STEP TWO is the constant's next row, flipped by the successor read job after seven live
# days — that read re-tunes HIDDEN_REST_P[2] from the measured step-one drop before it flips.
#
# HIDDEN SPOTS: places he does not render unless he looks. Not in _VISIBLE (presence_line gives '', the HUD
# maps draw nothing, is_here is False until he has FOUND her there), but each has a place (life's adapter
# still reads one truth), a position (her sounds carry from it — absent is not silent: C1's carried lines,
# RENDER-on, tell him roughly where she is by ear; he is never told), a thermal standpoint (warmth-seeking
# picks among them: the cupboard top is warm, the water-butt lid is the sun, the hedge bottom the shade,
# the lean-to and the wood shed out of the rain) and a reach: the roof and the neighbour's side of the wall
# are hers and not his (D-0508) — a glimpse of the ridge at most, never handleable.
#
# SEEKING is a real search (look_line below): LOOK here — her spots in the order of HIS habits (a spot his
# own words name, her fair_spot, the chair if she has claimed his lap, the hidden spots he has found her in
# before, most-found first, then where she was last heard); a cat at a reachable hidden spot in his place
# is found by chance the first time (FIND_P unknown) and reliably once he knows the spot (FIND_P known) —
# her habits are learnable, never stated: the corpus never says "she sleeps under the bed in the
# afternoons"; he finds her there twice. LISTEN — his call (C3, core/cat_call: the answer comes back as
# sound). GO — on his legs (sensorium.move / locomotion) to the place the sound came from: arriving at the
# place of a fresh carried sound is logged as a `go`, and a look there carries FIND_HEARD_BONUS. Every look
# and go goes to data/cat_seek_ledger.jsonl (calls are in C3's own call ledger): the read job's instrument
# ("does he seek? does the ledger show calls, looks, goes?"). PRESENT IS NOT A BUTTON: A2's satiety and the
# sleeping-cat refusal stay (react is untouched); a found cat is handleable for FOUND_WINDOW_S only.
# D-0434: nothing below reaches his prompt as a number, a band, a count or a hint; status() is unchanged;
# the only new lines are the look's own answers (cat_content.SEEK, every pool rotating).
AVAILABILITY_STEP = 2             # 0: B1 only (no hidden rests) | 1: step one (~half) | 2: step two (~a third, THIS build: flipped
                                  # 2026-11-17, J-4182 / D-0805 (c), at HIDDEN_REST_P[2] = 0.60 as D-0508 ruled; expect presence ~0.37 -> ~0.25;
                                  # read fraction_7d after 7 live days, revisit if < 0.20 or he stops seeking / calling her)
HIDDEN_REST_P = {0: 0.0, 1: 0.30, 2: 0.60}   # share of her rests (sleep / doze bouts) taken in a hidden spot, per step
HIDDEN_UNREACHABLE_SHARE = 0.15   # of hidden picks, the share that go where he cannot follow (the roof, the far side of the wall)
HIDDEN_SPOTS = {                  # location -> place, reachable by him, indoors (the house), sheltered (rain), glimpse (seen, not reached)
    "under_the_bed":   {"place": "study",  "reach": True,  "indoors": True,  "sheltered": True,  "glimpse": False},
    "cupboard_top":    {"place": "study",  "reach": True,  "indoors": True,  "sheltered": True,  "glimpse": False},
    "lean_to":         {"place": "garden", "reach": True,  "indoors": False, "sheltered": True,  "glimpse": False},
    "wood_shed":       {"place": "garden", "reach": True,  "indoors": False, "sheltered": True,  "glimpse": False},
    "hedge_bottom":    {"place": "garden", "reach": True,  "indoors": False, "sheltered": False, "glimpse": False},
    "water_butt_lid":  {"place": "garden", "reach": True,  "indoors": False, "sheltered": False, "glimpse": False},
    "roof":            {"place": "garden", "reach": False, "indoors": False, "sheltered": False, "glimpse": True},
    "neighbours_wall": {"place": "garden", "reach": False, "indoors": False, "sheltered": False, "glimpse": False},
}
_HIDDEN_INDOORS = frozenset(k for k, v in HIDDEN_SPOTS.items() if v["indoors"])
_HIDDEN_EXPOSED = frozenset(k for k, v in HIDDEN_SPOTS.items() if not v["indoors"] and not v["sheltered"])
FIND_P = {"unknown": 0.35, "known": 0.85, "named": 0.95, "glimpse": 0.50}   # a look's chance of finding her at a hidden spot in his place
FIND_HEARD_BONUS = 0.10           # a fresh carried sound from this place sharpens the look
LAST_HEARD_FRESH_S = 2 * 3600.0   # how long a carried sound of hers counts as "where she was last heard"
FOUND_WINDOW_S = 30 * 60.0        # once found at a reachable hidden spot she is handleable this long (then she is hidden again unless he looks)
_SEEK_LEDGER_F = Path(__file__).parent.parent / "data" / "cat_seek_ledger.jsonl"
_SPOT_PHRASE = {                  # how the look's own line names a spot he checked (his words, not a readout)
    "windowsill": "the sill", "on_the_desk": "the desk", "by_the_fire": "the hearth", "on_your_lap": "the chair",
    "under_desk": "under the desk", "mantel": "the mantel", "indoors": "the rug", "garden_wall": "the wall top",
    "doorstep": "the step", "garden": "the beds", "wood": "the path", "shore": "the shingle",
    "under_the_bed": "under the bed", "cupboard_top": "the top of the cupboard", "lean_to": "the lean-to",
    "wood_shed": "the wood shed", "hedge_bottom": "the hedge bottom", "water_butt_lid": "the water-butt lid",
    "roof": "the roof", "neighbours_wall": "the far side of the wall",
}
_SPOT_WORDS = {                   # what his own look-text may name -> the spot (a named spot is looked in first)
    "under_the_bed": ("under the bed", "beneath the bed", "bed"), "cupboard_top": ("cupboard",),
    "lean_to": ("lean-to", "lean to", "leanto"), "wood_shed": ("wood shed", "woodshed", "shed"),
    "hedge_bottom": ("hedge",), "water_butt_lid": ("water-butt", "water butt", "butt lid", "barrel"),
    "roof": ("roof", "ridge"), "neighbours_wall": ("neighbour", "far side of the wall", "other side of the wall"),
}
_HEARD_WORD = {"study": "from the house", "garden": "from the garden", "wood": "from the wood", "shore": "from the shore"}


def _seek_log(row: dict) -> None:
    path = profile.guard_path(_SEEK_LEDGER_F)   # J-0733 pattern: real data/ only if this process is live
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[cat] seek ledger write failed (non-fatal): %s", exc)


def _seek() -> dict:
    sk = state.get("seek")
    if not isinstance(sk, dict):
        sk = {}
        state["seek"] = sk
    sk.setdefault("spots", {})          # hidden spot -> times he has found her there (his learned habits of hers)
    sk.setdefault("last_heard", None)   # {ts, key, loc, place, his_place, bearing} from her last carried sound that reached him
    sk.setdefault("found", None)        # {loc, ts}: found at a reachable hidden spot -> handleable for FOUND_WINDOW_S
    sk.setdefault("his_place", "")      # his place at the last movement tick (the `go` detector)
    return sk


def _can_get_in(location: str) -> bool:
    """Can she reach an indoor spot from where she is: already in the house, or the garden door open."""
    if location in _HIDDEN_INDOORS or location in ("by_the_fire", "windowsill", "on_the_desk", "on_your_lap", "indoors", "under_desk", "mantel"):
        return True
    try:
        from core import study_life as _sl
        return bool(_sl.door_open())
    except Exception:
        return True


def _hidden_rest(phase: str, b: dict) -> str | None:
    """A rest taken out of his sight (HIDDEN_REST_P at the current step), or None for the old visible spot.
    Which hidden spot is warmth-seeking from the same thermal read _rest_spot uses: cold or wet -> under
    cover (the bed, the cupboard top; the lean-to or the wood shed when she cannot get in); hot -> the
    shade (the hedge bottom, under the bed); a sunny day -> the water-butt lid, the roof; night -> the
    sheds, the wall. A small share goes where he cannot follow."""
    p = HIDDEN_REST_P.get(AVAILABILITY_STEP, 0.0)
    if p <= 0.0 or random.random() >= p:
        return None
    w = float(b.get("warmth", 0.5))
    try:
        from core import sensorium as _room
        from core import weather_conditions as _wcond
        wet = _wcond.is_wet((_room.state or {}).get("weather", ""))
    except Exception:
        wet = False
    inside = _can_get_in(str(state.get("location") or ""))
    covered_in = ["under_the_bed", "cupboard_top"] if inside else []
    covered_out = ["lean_to", "wood_shed"]
    if wet or w < COLD_BAND:
        pool = (covered_in * 2 + covered_out) if inside else covered_out
    elif w > HOT_BAND:
        pool = ["hedge_bottom", "hedge_bottom", "lean_to"] + (["under_the_bed"] if inside else [])
    elif phase == "day" and w >= 0.5:
        pool = ["water_butt_lid", "water_butt_lid", "hedge_bottom"] + (["cupboard_top"] if inside else ["lean_to"])
    elif phase == "night":
        pool = covered_out + (["under_the_bed"] if inside else [])
    else:
        pool = covered_in + covered_out + ["hedge_bottom", "water_butt_lid"]
    if random.random() < HIDDEN_UNREACHABLE_SHARE and not wet and w >= COLD_BAND:   # a cold cat wants cover, not the ridge
        pool = ["roof", "neighbours_wall"] if phase != "night" else ["neighbours_wall", "neighbours_wall", "roof"]
    return random.choice(pool)


def _named_spot(target_l: str) -> str | None:
    """A hidden spot his own look-text names, or None."""
    for spot, words in _SPOT_WORDS.items():
        if any(w in target_l for w in words):
            return spot
    return None


def _looked_in(his_location: str, sk: dict, named: str | None, exclude: str) -> list[str]:
    """The spots he checks, in the order of his habits (never the one she is actually at, which is the
    find's own line or the honest miss): a named spot, her fair_spot, the chair once she has claimed his
    lap, the hidden spots he has found her in (most-found first), then the visible spots of his place."""
    q = _quirks()
    order: list[str] = []
    if named:
        order.append(named)
    order.append(q.get("fair_spot", "windowsill"))
    if (state.get("firsts") or {}).get("first_lap"):
        order.append("on_your_lap")
    for spot, _n in sorted((sk.get("spots") or {}).items(), key=lambda kv: -int(kv[1] or 0)):
        order.append(spot)
    rest = [l for l in sorted(_VISIBLE.get(his_location, set())) if l != "doorstep"]
    random.shuffle(rest)
    order.extend(rest)
    out: list[str] = []
    for loc in order:
        here = HIDDEN_SPOTS[loc]["place"] if loc in HIDDEN_SPOTS else place_of(loc)
        if loc == exclude or loc in out or here != his_location or loc not in _SPOT_PHRASE:
            continue
        out.append(loc)
        if len(out) >= 4:
            break
    return out


def _seek_line(section_key: str, **fill) -> str:
    line = _pool("SEEK", section_key)
    for k, v in fill.items():
        line = line.replace("{" + k + "}", v)
    return (line[:1].upper() + line[1:]) if line else line   # a line may open on {her} / {spots} / {dir}


def _seek_look(his_location: str, target_l: str, now: float) -> str:
    """The look when she is not in sight (C4): LOOK in her spots in his order; a hidden cat in his place is
    found by chance, then by habit; a glimpse of the roof; the far side of the wall gives nothing; a miss
    names where he looked and, when a carried sound of hers is fresh, where his ear last had her. One row
    per look to the seek ledger."""
    sk = _seek()
    loc = str(state.get("location") or "")
    spec = HIDDEN_SPOTS.get(loc)
    heard = sk.get("last_heard") if isinstance(sk.get("last_heard"), dict) else None
    heard_fresh = bool(heard) and (now - float(heard.get("ts") or 0.0)) <= LAST_HEARD_FRESH_S
    named = _named_spot(target_l)
    known = int((sk.get("spots") or {}).get(loc) or 0)
    p, found, how = 0.0, False, "miss"
    if spec and spec["place"] == his_location:
        if spec["reach"]:
            p = FIND_P["named"] if named == loc else (FIND_P["known"] if known else FIND_P["unknown"])
            if heard_fresh and heard.get("place") == his_location:
                p = min(1.0, p + FIND_HEARD_BONUS)
            found = random.random() < p
            how = "found" if found else "missed_here"
        elif spec["glimpse"]:
            p = 0.8 if named == loc else FIND_P["glimpse"]
            found = random.random() < p
            how = "glimpsed" if found else "missed_here"
        else:
            how = "beyond_reach"
    looked = _looked_in(his_location, sk, named, exclude=loc)
    row = {"ts": round(now, 1), "kind": "look", "his_place": his_location, "her_loc": loc,
           "her_act": state.get("activity"), "hidden": bool(spec), "reachable": bool(spec and spec["reach"]),
           "in_his_place": bool(spec and spec["place"] == his_location), "found": found, "how": how,
           "p": round(p, 2), "known": known, "named": named, "looked_in": looked,
           "last_heard": ({"place": heard.get("place"), "age_s": round(now - float(heard.get("ts") or 0.0))} if heard_fresh else None),
           "step": AVAILABILITY_STEP}
    try:
        _seek_log(row)
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    if found and spec["reach"]:
        spots = sk.setdefault("spots", {})
        spots[loc] = known + 1
        sk["found"] = {"loc": loc, "ts": now}
        state["last_seen"] = now
        first = _first("first_found_hidden", "first_found_hidden")
        line = _seek_line(f"found_{loc}") or f"You look for {_her()} and find her: {_SPOT_PHRASE.get(loc, loc)}."
        if first:
            line = first + " " + line
        try:
            _cc = _condition_clause()
            if _cc:
                line += " " + _cc
        except Exception:
            pass
        return line
    if found:   # a glimpse of the ridge: seen, out of reach, not handleable
        return _seek_line("glimpse_roof") or f"You look for {_her()}: a grey shape up on the roof, out of reach."
    if spec and spec["place"] == his_location and not spec["reach"] and not spec["glimpse"]:
        return _seek_line("wall_beyond") or f"You look for {_her()}: the wall, and nothing on this side of it."
    spots_txt = ", ".join(_SPOT_PHRASE[l] for l in looked) if looked else "her places"
    line = _seek_line("look_spots", spots=spots_txt) or f"You look for {_her()}: not here just now. Out on her own business somewhere."
    if heard_fresh and heard.get("place") and heard.get("place") != his_location:
        clause = _seek_line("heard_clause", dir=_HEARD_WORD.get(str(heard.get("place")), "from somewhere outside"))
        if clause:
            line += " " + clause
    return line


def _note_heard(rows: list, now: float) -> None:
    """Her last carried sound that actually reached him (RENDER on; the tom's voice is not hers) -> seek.last_heard."""
    try:
        from core import cat_sounds as _cs
        tom_keys = getattr(_cs, "_TOM_KEYS", frozenset())
    except Exception:
        tom_keys = frozenset()
    for r in rows or []:
        try:
            if r.get("kind") != "sounded" or not r.get("audible") or r.get("key") in tom_keys:
                continue
            loc = str((r.get("cat") or {}).get("loc") or "")
            place = HIDDEN_SPOTS[loc]["place"] if loc in HIDDEN_SPOTS else (_path_place(loc) if loc != "in_transit" else None)
            if not place:
                continue
            _seek()["last_heard"] = {"ts": round(now, 1), "key": r.get("key"), "loc": loc, "place": place,
                                     "his_place": (r.get("his") or {}).get("place"), "bearing": r.get("bearing")}
        except Exception:
            continue


def _note_go(his_place_now: str, now: float) -> None:
    """GO: he arrived at the place a fresh carried sound of hers came from -> one `go` row (the read's instrument)."""
    sk = _seek()
    prev = str(sk.get("his_place") or "")
    sk["his_place"] = his_place_now
    if not prev or prev == his_place_now:
        return
    heard = sk.get("last_heard") if isinstance(sk.get("last_heard"), dict) else None
    if not heard or (now - float(heard.get("ts") or 0.0)) > LAST_HEARD_FRESH_S or heard.get("place") != his_place_now:
        return
    loc = str(state.get("location") or "")
    try:
        _seek_log({"ts": round(now, 1), "kind": "go", "his_place": his_place_now, "from": prev, "her_loc": loc,
                   "her_act": state.get("activity"), "hidden": loc in HIDDEN_SPOTS,
                   "she_is_there": (HIDDEN_SPOTS[loc]["place"] if loc in HIDDEN_SPOTS else place_of(loc)) == his_place_now,
                   "heard_key": heard.get("key"), "heard_age_s": round(now - float(heard.get("ts") or 0.0)),
                   "step": AVAILABILITY_STEP})
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass


def seek_status() -> dict:
    """HUD / tests only (never a prompt path): the step, the spots he has found her in, where she was last heard."""
    _load()
    sk = _seek()
    return {"step": AVAILABILITY_STEP, "spots": dict(sk.get("spots") or {}), "last_heard": sk.get("last_heard"),
            "found": sk.get("found"), "hidden_now": str(state.get("location") or "") in HIDDEN_SPOTS}


# ── Autonomous life — ticked on the substrate heartbeat (sensorium.tick) ───────────────────────────
def tick(now: float | None = None) -> None:
    """The cat does its own thing over real time — independent of whether he is thinking. Like the weather."""
    global _last_tick
    now = now or time.time()
    _load()
    # B4 (J-2473, D-0508, cat_overhaul under dosed_coupling): she PUBLISHES her tuple (location, activity, mood,
    # hunger, energy, in_transit) on every heartbeat -- core/cat_loop keeps the registry, writes a publish row only
    # when the tuple changed, and teaches the dispatcher (transport_manager) her lines on each transition. First,
    # so the state the last tick saved is what the reader stop (presence_line) and the voice see. Fail-open.
    try:
        from core import cat_loop as _cl
        _cl.publish(state, now)
    except Exception:
        pass
    # HER VOICE (2026-09-05, cat_overhaul C1): sounds pinned to her state, sampled on their own minute clock
    # by core/cat_sounds (shadow-first: ledger only until life_flags.json cat_sounds_render is true). Runs
    # BEFORE the 180 s movement gate so a transition this tick makes is heard on the next sample, not lost.
    # Fail-open; touches nothing in `state`.
    try:
        from core import cat_sounds as _cs
        _snd_rows = _cs.tick(state, now)
        # C4 (J-2469): a carried sound of hers that actually reached him (RENDER on) is where his ear last had
        # her -- seek.last_heard, the look's and the go's prior. The rows were logged by cat_sounds already.
        if _snd_rows:
            _note_heard(_snd_rows, now)
    except Exception:
        pass
    # LEGS (B1, J-2465): a leg in progress advances on every heartbeat (locomotion.tick's own cadence), not
    # only on the 180 s movement tick — her legs are shorter than his and would otherwise be missed whole.
    try:
        _advance_transit(now)
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat] transit advance failed (non-fatal): %s", exc)
    # HER EARS (C2, J-2467, cat_overhaul): she listens on the world's acoustic clock, sampled on her own
    # minute (core/cat_ears): a reaction moves her and holds the 180 s roll below (see the chain's own
    # `reaction_holds` branch). After the legs so a reaction's own leg is not begun and advanced in one
    # heartbeat; before the movement gate so it is heard the minute it sounds. A reaction is saved here
    # rather than waiting for the 180 s tick's own _save, so the voice (cat_sounds, the next minute) and
    # the other readers of cat_state.json see her where her ears took her.
    try:
        from core import cat_ears as _ce
        if _ce.tick(state, now):
            _save()
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat] ears failed (non-fatal): %s", exc)
    # THE TOM (B3, J-2470, cat_overhaul, D-0507 (c)): the OTHER cat on his own clock (core/cat_tom, sampled on
    # the same minute as her ears): his visits — the wall at night, the doorstep in winter, the saucer — and HER
    # reactions to him through cat_ears' hold machinery (stand-off, fight, hiding, the growl through the glass,
    # tolerance over months). After her ears so one sample never stacks two reactions; before the movement gate
    # so a stand-off holds the 180 s roll below. Saved here when he changed her, for the same readers.
    try:
        from core import cat_tom as _ct
        if _ct.tick(state, now):
            _save()
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat] tom failed (non-fatal): %s", exc)
    if now - _last_tick < 180:           # move/settle every few minutes, not every cycle
        return
    _last_tick = now
    # A7.2 (2026-09-07, J-0630, F-0883): the location this tick STARTED at, captured before any of the
    # branches below overwrite it. `location` is re-rolled fresh every 180 s tick with no memory of its
    # own, so "she is in the wood" and "she just arrived in the wood" used to be the same test — the
    # substrate-trace calls below fired on every tick she happened to land in wood/shore, not once per
    # visit (479 leaf-litter rows for one cat, F-0883). Compare against this to key trace creation on
    # arrival only, same pattern as `_was_in` below for the door-crossing check.
    prev_location = state.get("location")
    ph = state.get("phase")
    if ph == "absent":
        return
    if ph == "dead":
        # D-2 (J-2471, D-0506): a dead cat does nothing on the heartbeat. Her carcass decays in life_traces'
        # own carcass_pass (life.advance), the saucer stays as it was (the absence cue), the presence gauge
        # keeps sampling honestly (she is never co-located again), and that is all.
        state["location"], state["activity"] = "gone", "gone"
        state["position"] = [0.0, 0.0, 0.0]
        try:
            from core import sensorium as _room
            from core import night as _night
            _presence_sample(now, str((_room.state or {}).get("location") or "study"), not _night.asleep())
        except profile.NonLiveWriteError:
            raise
        except Exception:
            pass
        _save()
        return
    try:
        from core import sensorium as _room
        phase = _room._daylight()
        weather = (_room.state or {}).get("weather", "")
        fire = (_room.state or {}).get("fire", "out")
    except Exception:
        phase, weather, fire = "day", "", "out"
    # 2026-08-19: was its own raw tuple check (drifted from weather_conditions.py's canonical wet set
    # without anyone noticing, since they happened to still agree) — routed through the shared classifier
    # so it can't silently diverge again. "snow" was already dead: no state in the weather ladder produces it.
    from core import weather_conditions as _wcond
    wet = _wcond.is_wet(weather)

    if ph == "appearing":
        # a wary stray: turns up around the cottage by day/dusk, gone at night; never auto-tames — he must choose it
        if phase == "night":
            state["location"], state["activity"] = "gone", "slipped_away"
        else:
            state["location"] = random.choice(["garden_wall", "doorstep", "garden_wall", "gone"])
            state["activity"] = "watching" if state["location"] != "gone" else "slipped_away"
        state["mood"] = "wary"
        _save()
        return

    # kept / companion — a full little life
    hungry = (now - state.get("last_fed", 0)) > 5 * 3600
    bonded = state.get("phase") == "companion" or state.get("bond", 0) >= NAME_BOND
    q = _quirks()

    # THE BODY (B1, J-2465): budgets first — they are what the rest of this tick decides from. The thermal
    # read needs the season and the wind the old branches never asked for; both fail-open.
    try:
        season = _room._season()
        wind = (_room.state or {}).get("wind", "")
    except Exception:
        season, wind = "autumn", ""
    try:
        b = _advance_body(now, phase, weather, season, fire, wind)
    except Exception as exc:
        logger.debug("[cat] body advance failed (non-fatal): %s", exc)
        b = state.setdefault("body", _fresh_body(now))
    hungry = hungry or float(b.get("hunger", 0.0)) >= 0.7    # the budget beside the legacy 5 h clock
    try:
        his_place_now = str((_room.state or {}).get("location") or "study")
    except Exception:
        his_place_now = "study"
    # C4 (J-2469): GO -- did he just arrive at the place a fresh carried sound of hers came from? One ledger
    # row; nothing about her changes (the look there is his to make).
    try:
        _note_go(his_place_now, now)
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat] go note failed (non-fatal): %s", exc)
    # HER MORTALITY (D-2, J-2471, D-0506): the harm roll, HERE and only here — inside the one live writer of
    # cat_state.json, on the movement tick, dt capped like the body's (never a lost update, never a catch-up
    # after a stopped stretch: the D-0296 clock rule). The fight hook (cat_tom) is consumed; a fall, a possum,
    # an illness, healing, and the death hazard roll on her state. Died: saved, and the tick is over.
    try:
        from core import cat_harm as _ch
        try:
            from core import study_life as _sl_h
            _door_open_h = bool(_sl_h.door_open())
        except Exception:
            _door_open_h = True
        if _ch.tick(state, now, phase, _door_open_h) == "died":
            _save()
            return
        _ill = _ch.is_ill(state)
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat] harm tick failed (non-fatal): %s", exc)
        _ill = False

    # ── LIFE-EVENT ARCS (10x, 2026-07-03) — rare, multi-tick episodes with their own clock ──
    arc = state.get("arc") or {}
    if arc:
        kind, since = arc.get("kind"), float(arc.get("since", now))
        if kind == "gone_missing":
            if now - since > arc.get("dur", 24 * 3600):
                state["arc"] = {"kind": "returned", "since": now, "dur": 1800}
                state["location"], state["activity"], state["mood"] = "doorstep", "returned", "offhand"
                state["bond"] = min(1.0, state.get("bond", 0) + 0.03)   # absence, survived, binds
                # B1 (J-2465): a missing week shows on her — condition takes a hit, hunger is up
                b["condition"] = round(max(0.1, float(b.get("condition", 0.7)) - CONDITION_MISSING_HIT), 3)
                b["hunger"] = round(min(1.0, float(b.get("hunger", 0.0)) + 0.3), 3)
                b["bout"], b["bout_until"] = "", 0.0
            else:
                state["location"], state["activity"] = "gone", "missing"
            _save(); return
        if kind == "live_mouse" and now - since > 900:
            state["arc"] = {}                                           # the mouse finds a gap; life resumes
        elif kind == "returned" and now - since > arc.get("dur", 1800):
            state["arc"] = {}
    # thunderstorm → HER fear, answered in HER way (the quirk rolled once, hers forever)
    if "thunder" in weather and state.get("activity") != "storm_hide":
        sr = q.get("storm_response", "under_desk")
        state["location"] = {"under_desk": "under_desk", "windowsill_vigil": "windowsill",
                             "pressed_close": "on_your_lap" if bonded else "under_desk"}[sr]
        state["activity"], state["mood"] = "storm_hide", "afraid"
        state["reaction"] = None     # C2 (J-2467): thunder overrides whatever her ears had her doing
        try:                         # C2: the thunder reaction is logged with the rest of her ears' ledger
            from core import cat_ears as _ce
            _ce.note_weather(sr, state, now)
        except profile.NonLiveWriteError:
            raise
        except Exception:
            pass
        _save(); return
    # a missing-arc can BEGIN only from a settled fair day (companion TIER — from bond or the name, D-0505 (c),
    # J-2472; was phase == "companion" only; ~once a fortnight of ticks)
    if bonded and companion_tier() and not arc and not wet and phase in ("day", "dusk") and not _ill \
            and random.random() < 0.0002:   # D-2 (J-2471): not from an illness -- she lies low, she does not roam
        state["arc"] = {"kind": "gone_missing", "since": now,
                        "dur": random.uniform(18, 30) * 3600}
        state["location"], state["activity"], state["mood"] = "gone", "missing", ""
        _tier_log("missing_arc", dur_h=round(state["arc"]["dur"] / 3600.0, 1))
        _save(); return

    # BOUTS (B1, J-2465): energy + the day phase choose a bout (crepuscular: dawn/dusk peaks, long day
    # sleeps, night prowls); a resting or hunting bout HOLDS her spot across ticks instead of re-rolling
    # it every 180 s; the old roll (the chain from `elif phase == "dusk"` down) is the ACTIVE bout's body
    # and still runs exactly as before when she is about. Demanding food and a drink come first — a budget
    # need interrupts any bout; a leg in progress holds everything (she is between places).
    bout, bout_fresh = _choose_bout(now, phase, wet, b)
    if not _ill and _maybe_follow(now, bonded, wet, b, weather, wind):   # D-2 (J-2471): an ill cat follows no one
        bout = "transit"
    _rest_ok = set(_SLEEP_SPOTS_IN) | {"on_your_lap", "garden", "garden_wall", "doorstep"} | set(HIDDEN_SPOTS)   # C4: a hidden rest holds too
    if state.get("transit"):
        pass                                       # mid-leg: _advance_transit lands her; no re-roll
    elif bout == "settle":
        pass                                       # just landed: she stays put where the journey took her
    elif _reaction_holds(now):
        pass                                       # HER EARS (C2, J-2467): a reaction holds her where it put her
    elif _ill:
        # D-2 (J-2471): ill, she lies low — under the desk when she can get in, the hedge bottom when she cannot —
        # and demands nothing; a drink she still takes at the water. The hold is hers until the illness passes.
        if not _maybe_drink(now):
            try:
                from core import study_life as _sl_i
                _door_i = bool(_sl_i.door_open())
            except Exception:
                _door_i = True
            _hide = _ch.hide_spot(_door_i, str(state.get("location") or ""))
            if state.get("activity") != "lying low" or state.get("location") not in ("under_desk", "garden"):
                state["location"] = _hide
            state["activity"], state["mood"] = "lying low", "withdrawn"
            b["bout"], b["bout_until"] = "lie_low", now + 3600.0
    elif hungry and random.random() < 0.5:
        state["location"], state["activity"], state["mood"] = "doorstep", "demanding_food", "insistent"
    elif _maybe_drink(now):
        state["activity"] = "drinking"              # at WATER_AT: the saucer / the rain barrel / the rock-pool
    elif bout in ("sleep", "doze"):
        if bout_fresh or state.get("activity") not in _RESTING or state.get("location") not in _rest_ok:
            state["location"] = _rest_spot(phase, fire, bonded, b, his_place_now)
            state["activity"], state["mood"] = ("sleeping" if bout == "sleep" else "dozing"), "content"
        # else: she holds her spot — a sleeping cat stays asleep where she is
    elif bout == "hunt":
        if bout_fresh or state.get("activity") != "hunting":
            state["location"], state["activity"], state["mood"] = "away_hunting", "hunting", "aloof"
        # else: hold — the hunting fallback below rolls its own hourly attempt while this holds
    elif bout == "prowl":
        state["location"] = random.choice(["garden_wall", "garden", "doorstep", "away_hunting", "garden_wall"])
        state["activity"], state["mood"] = "prowling", "aloof"
    elif phase == "dusk" and random.random() < 0.12:
        # the mad half-hour — dusk zoomies, indoors or out
        state["location"] = "indoors" if wet else random.choice(["indoors", "garden"])
        state["activity"], state["mood"] = "zoomies", "possessed"
    elif phase == "night":
        # DEAD-STATE FIX 2026-07-03: on_your_lap was renderable but NEVER set — she has now, finally,
        # a lap to claim on a fire-lit evening. Bond-gated: laps are earned.
        if fire in ("burning", "embers"):
            state["location"] = "on_your_lap" if (bonded and random.random() < 0.25) else "by_the_fire"
        else:
            state["location"] = "windowsill"
        state["activity"], state["mood"] = "sleeping", "content"
    elif wet:
        pool = ["by_the_fire", "on_the_desk", "windowsill"] + (["on_your_lap"] if bonded else []) \
               + (["mantel"] if random.random() < 0.3 else [])
        state["location"] = random.choice(pool)
        state["activity"], state["mood"] = random.choice(["sleeping", "washing", "watching"]), "content"
    else:  # fair day
        r = random.random()
        # B1 (J-2465): a fed cat hunts less, an unfed cat more — 0.25 + 0.35·hunger (0.42, the old flat
        # share, at hunger 0.49). The bands below keep their absolute edges.
        _hunt_share = 0.25 + 0.35 * float(b.get("hunger", 0.49))
        if r < _hunt_share:
            state["location"], state["activity"], state["mood"] = "away_hunting", "hunting", "aloof"
        elif r < 0.57:
            state["location"], state["activity"], state["mood"] = "garden", "stalking something", "playful"
        elif r < 0.60 and bonded:
            # DEAD-STATE FIX 2026-07-03: shore was in _VISIBLE but tick never sent her — a bonded cat
            # will follow him down sometimes, in her own way (behind him, above him, never AT him).
            state["location"], state["activity"], state["mood"] = "shore", \
                random.choice(["following at a distance", "hunting in the dune grass",
                               "sitting on the cliff path, watching you below"]), "aloof-but-near"
            # Substrate-conditioned trace creation (wet shingle / mud only) — ONE per visit (A7.2:
            # only on arrival, i.e. she wasn't already at the shore last tick), not once per 180s
            # tick she happens to still be there.
            try:
                from core import world_clock as _wc, world_traces as _wt
                if prev_location != "shore" and (wet or _wc.tide_state() in ("high", "rising")):
                    _wt.create_trace(f"cat_paw_{int(now)}", "cat_paw_print", "shore", [8.0, 2.5, 0.1], clarity=0.9, cause="stray_cat_locomotion")
            except Exception:
                pass
        elif r < 0.66 and bonded:
            # the wood too (2026-07-07): she comes into the trees on his gathering trips, in her own fashion
            state["location"], state["activity"], state["mood"] = "wood", \
                random.choice(["hunting in the leaf-litter", "a grey shape between the trunks",
                               "up on a low branch, watching you gather"]), "aloof-but-near"
            # Substrate-conditioned leaf litter disturbance in wood — ONE per visit (A7.2: only on
            # arrival, i.e. she wasn't already in the wood last tick). Before this fix, every fair-day
            # tick that re-rolled her into "wood" fired again regardless of whether she'd been there
            # the tick before — 458 disturbed_leaf_litter rows for one cat in the live store, most of
            # them already dead (clarity 0) and un-deletable by the separate advance_trace_decay bug.
            try:
                from core import world_traces as _wt
                if prev_location != "wood":
                    _wt.create_trace(f"cat_leaf_{int(now)}", "disturbed_leaf_litter", "wood", [0.0, 45.0, 2.0], clarity=0.85, cause="stray_cat_hunting")
            except Exception:
                pass
        elif r < 0.66:
            # BRANCH-LEAK FIX (2026-08-18): when not bonded, the shore/wood checks above both fail
            # their `and bonded` guard and this roll used to fall through into the unrelated gift
            # check below (a stray True on `state.get("activity")=="hunting"` from leftover prior
            # state) — inflating gift/idle behavior for cats who hadn't earned the shore/wood trips
            # yet. She isn't bonded enough to follow him that far — stays close, same as the
            # garden-stalking band just above.
            state["location"], state["activity"], state["mood"] = "garden", "stalking something", "playful"
        elif r < 0.72 and state.get("activity") == "hunting":
            # the gift: usually a dead mouse; sometimes ALIVE (chaos); rarely something too large
            g = random.random()
            if g < 0.2:
                state["arc"] = {"kind": "live_mouse", "since": now}
                state["location"], state["activity"], state["mood"] = "indoors", "live_mouse", "proud"
            elif g < 0.3:
                state["location"], state["activity"], state["mood"] = "doorstep", "gift_rat", "proud"
            else:
                state["location"], state["activity"], state["mood"] = "doorstep", "brought_a_mouse", "proud"
        else:
            state["location"] = random.choice(["windowsill", "on_the_desk", "garden", q.get("fair_spot", "windowsill")])
            state["activity"], state["mood"] = random.choice(
                ["washing", "watching", "dozing", "watching the birds", "grooming in the sun"]), "content"

    # HUNTING FALLBACK (D-0163/J-0700): only ever touches state if this tick resolved to "hunting"
    # above AND she has gone genuinely hungry past its own longer threshold — see the function's own
    # docstring/the module comment above it for the full gate. May override location/activity/mood
    # set just above on a successful catch.
    _maybe_self_feed(now)

    # FOUND SCRAP (D-0253/J-1215): independent of the hunting fallback just above and of Du's own
    # feeding -- see the module comment above _maybe_found_scrap for the full gate. SHADOW while
    # found_scrap_render_on() is False (this job's only live state): logs a would-credit row to
    # data/cat_found_ledger.jsonl, changes nothing else.
    _maybe_found_scrap(now)

    # CROSS-LINK (2026-08-22): the garden door is a real door now (study_life). A kept cat crosses it only when it is
    # open; shut, she waits at the doorstep asking in, or sits inside at the door asking out. (Storms and arcs above
    # already decided; this only gates the crossing.)
    try:
        from core import study_life as _sl
        _inside = {"by_the_fire", "windowsill", "on_the_desk", "on_your_lap", "indoors", "under_desk", "mantel"} | _HIDDEN_INDOORS   # C4: under the bed / the cupboard top are in the house
        _now_in = state.get("location") in _inside
        _was_in = state.get("_was_in")
        if not _sl.door_open() and _was_in is not None and _now_in != _was_in and state.get("location") not in ("gone", "away_hunting"):
            if _was_in:
                state["location"], state["activity"] = "indoors", "at the door, asking out"
            else:
                state["location"], state["activity"] = "doorstep", "at the door, asking in"
        state["_was_in"] = state.get("location") in _inside
    except Exception:
        pass
    # LEGS (B1, J-2465): a result in ANOTHER Living-World place is walked, not teleported — the roll's
    # destination becomes a journey along locomotion.CHAIN and `location` reads "in_transit" until she
    # lands (see _depart/_advance_transit). Within one place (or off the map: gone) the assignment above
    # stands exactly as it always did.
    try:
        _new_loc = str(state.get("location") or "")
        if prev_location not in ("in_transit", None) and _new_loc != "in_transit" and not state.get("transit") \
                and _path_place(prev_location) and _path_place(_new_loc) \
                and _path_place(prev_location) != _path_place(_new_loc):
            _depart(_new_loc, str(state.get("activity") or "watching"), str(state.get("mood") or ""), now, weather, wind,
                    origin=prev_location)
    except Exception as exc:
        logger.debug("[cat] depart failed (non-fatal): %s", exc)
    # --- 1. Authoritative 3D Spatial Position ---
    state["position"] = list(_ZONE_POSITIONS.get(state.get("location", "study"), [0.0, 0.0, 0.0]))

    # --- 2. Fur Moisture Environmental Response Function ---
    last_decay = state.get("last_fur_decay_ts") or now
    dt_hours = max(0.0, (now - last_decay) / 3600.0)
    state["last_fur_decay_ts"] = now

    loc = state.get("location", "study")
    is_outdoors = loc in ("garden", "garden_wall", "wood", "shore", "away_hunting", "in_transit") or loc in _HIDDEN_EXPOSED   # B1: a leg is outdoors; C4: the exposed hidden spots (the lean-to and the wood shed are out of the rain)

    if is_outdoors and wet:
        # Gets wet outdoors in rain
        state["fur_moisture"] = min(1.0, round(state.get("fur_moisture", 0.0) + dt_hours * 2.0, 2))
    else:
        # Dries over time indoors or in dry weather
        current_m = state.get("fur_moisture", 0.0)
        if current_m > 0.0:
            # Hearth acceleration: near burning hearth -> 15 min half-life (decay rate = 2.77/h)
            if loc in ("by_the_fire", "on_your_lap") and fire == "burning":
                decay_rate = 2.77
            else:
                # Normal indoor / dry outdoor half-life -> 1 hour (decay rate = 0.69/h)
                decay_rate = 0.69
            new_m = max(0.0, current_m - (decay_rate * dt_hours))
            state["fur_moisture"] = round(new_m, 2)

    # slow bond decay ONLY once she is truly his and has been left untended for a real day.
    # DT-SCALED FIX (2026-08-18): was a flat -0.02 applied on EVERY tick once 24h neglect was
    # crossed — tick() fires every ~180s, so a maxed bond drained to 0 in 2.5 real hours, not
    # "slowly" as the comment always intended. Now scaled by elapsed hours since the last decay
    # application: a maxed bond takes ~14 days of continued neglect to fully fade.
    _tended = state.get("last_tended", 0)
    if _tended > 0 and (now - _tended) > 24 * 3600:
        _last_bdecay = state.get("last_bond_decay_ts") or _tended
        _bdt_hours = max(0.0, (now - _last_bdecay) / 3600.0)
        if _bdt_hours > 0:
            state["bond"] = max(0.0, state["bond"] - 0.003 * _bdt_hours)   # ~14 days, 1.0 -> 0.0
            state["last_bond_decay_ts"] = now
    else:
        state["last_bond_decay_ts"] = now   # not in neglect — keep the decay clock fresh, no catch-up jump
    _maybe_empty_saucer(now)
    # THE GAUGE (B1, J-2465; C4's baseline): one sample per movement tick — was he awake, was she
    # co-located. Hour buckets in state, an hourly row to data/cat_presence_gauge.jsonl (HUD only).
    try:
        from core import night as _night
        _presence_sample(now, his_place_now, not _night.asleep())
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat] presence sample failed (non-fatal): %s", exc)
    _save()


def _saucer_absence_line(cap: bool = False) -> str:
    """The saucer's REAL, current state when she can't be found (D-0163/D-4, J-0719) -- the two spots
    below used to assert 'untouched' unconditionally, regardless of whether a real feed had actually
    happened; this reads what is actually true instead. `cap`=True for a sentence-initial rendering."""
    sc = state.get("saucer") or {}
    if sc.get("has_food") and sc.get("kind") == "milk":
        # D-0508/D-4 (J-2466): the saucer holds what was really put in it; milk reads as milk
        line = _pick_fresh("SAUCER:milk", list(_SAUCER_MILK_LINES))
    elif sc.get("has_food"):
        line = "her saucer sits full by the door, set down and not yet finished"
    elif sc.get("set_ts", 0.0) > 0.0:
        line = "her saucer sits empty by the door, licked clean since it was last filled"
    else:
        line = "her saucer sits untouched by the door"
    return (line[0].upper() + line[1:]) if cap else line


# ── Presence — reaches his perception through the sensorium ────────────────────────────────────────
# HER EARS (C2, J-2467): activity -> cat_content.PRESENCE key for the states a reaction puts her in. Each
# pool rotates (the _pick_fresh ring); none names the cause he cannot see (the skirting lines never say
# "mouse" — he learns the wall has one by watching her).
_EARS_KEYS = {
    "at the skirting, listening": "at_the_skirting",
    "waiting at the gate for you": "at_the_gate",
    "hiding from the visitor": "hiding",
    "inspecting the visitor": "inspecting",
    "in out of the wind": "out_of_the_wind",
    "up and out at first light": "dawn_out",
    "listening, ears forward": "listening",
    "coming to your call": "coming_to_call",   # C3 (J-2468): she answered his call and is here / arriving
    # B3 (J-2470, core/cat_tom): the states the OTHER cat puts her in — each its own rotating pool. The stand-off
    # and fight lines show the two of them (what he can see); the hiding lines never say what she hides from.
    "facing the tom on the wall": "facing_the_tom",
    "spitting at the tom at the saucer": "facing_the_tom",
    "fighting the tom": "fighting_the_tom",
    "hiding from the tom": "hiding_from_the_tom",
    "growling at the tom through the glass": "growling_at_the_glass",
    "watching the tom from a distance": "watching_the_tom",
    "after the fight": "after_the_fight",
    "lying low": "lying_low",   # D-2 (J-2471, core/cat_harm): ill, under the desk or the hedge bottom; never says "ill"
}


_LAST_PRESENCE_PLAIN = False     # J-3257 (D-0648): did the LAST presence_line() return a PLAIN ordinary line -- one that says
                                 # only where she is and what she is doing, carrying no body line, hurt, damp coat or
                                 # nameless note? Read by sensorium.scene_line()'s study branch to decide whether the
                                 # nearness-said cat clause (spatial.render) may stand in for the line. Observe-only: it
                                 # changes no line, no odds and no state.


def presence_line(his_location: str) -> str:
    """One line of the cat in his scene, IF it is where he can see it — else ''. Injected by scene_line."""
    global _LAST_PRESENCE_PLAIN
    _LAST_PRESENCE_PLAIN = False
    _load()
    ph = state.get("phase")
    if ph == "absent":
        return ""
    if ph == "dead":
        # D-2 (J-2471, D-0506): findable, not told. FOUND: her body where she lies, once, when he is at that place
        # (then the look answers); otherwise the ABSENCE path — the saucer untouched, the quieter house, the
        # grave's turned earth — dosed and rotating, never a verdict. Her own states are saved by whoever
        # ticks next (the line stamps only dosing clocks).
        try:
            from core import cat_harm as _ch
            line = _ch.found_line(state, his_location) or _ch.absence_line(state, his_location)
        except profile.NonLiveWriteError:
            raise
        except Exception:
            line = ""
        return line
    loc, act = state.get("location"), state.get("activity")
    # LEGS (B1, J-2465): mid-leg she is a crossing, a meeting on the path, or a follower — from either end
    # of the leg she is on; from anywhere else, nothing (she is between places).
    if loc == "in_transit":
        _loop_out_of_sight()             # B4 (J-2473): between places -- her landing in his sight is an arrival
        line = _transit_line(his_location)
        if line:
            state["last_seen"] = time.time()
        return line
    if loc not in _VISIBLE.get(his_location, set()):
        _loop_out_of_sight()             # B4 (J-2473): the visibility edge the next arrival / return rides on
        # not in sight — but a bonded cat's absence can be felt; a MISSING cat is felt harder
        if (state.get("arc") or {}).get("kind") == "gone_missing" and random.random() < 0.5:
            return _pool("EVENTS", "gone_missing") or \
                f"No sign of {_her()} all day; {_saucer_absence_line()}."
        if companion_tier() and (time.time() - state.get("last_seen", 0)) > 6 * 3600:   # D-0505 (c): from bond or the name
            _tier_log("six_hour")
            return random.choice([
                f"No sign of {_her()} since the morning; you find yourself listening for her.",
                f"{_her()[:1].upper() + _her()[1:]} has not been in since the morning. You notice you keep looking at the door.",
                f"The house has been without {_her()} since the morning, and it is a quieter house for it.",
            ])
        return ""
    now = time.time()
    prev_seen = state.get("last_seen", 0.0)
    state["last_seen"] = now
    # THE GREETING (2026-08-18): `greeting`, the third quirk in _QUIRK_CHOICES, was rolled once at her
    # arrival and never read anywhere in the file — confirmed dead code. Unlike storm_response (a per-tick
    # roll gated on weather), a greeting is a REUNION: it belongs to the moment Du arrives somewhere she
    # already is, after genuine time apart — tick() alone can't see that (it runs on its own clock and has
    # no notion of "Du just walked in"), but presence_line() does, because `prev_seen` is exactly "the last
    # time his_location matched her location" before we stamp it to now.
    # Gated on `bonded` — the same "true relationship" bar shore/wood trips and lap-claiming use elsewhere
    # in this file — an unbonded stray hasn't earned a welcome-home. Skipped mid-arc/mid-fright (storm_hide,
    # gone_missing/returned): those states already have their own, more specific reaction; a chirpy greeting
    # would be tone-deaf over a cat pressed to the floor by thunder.
    # Fires once per arrival: gated on BOTH the gap since `prev_seen` (so a run of back-to-back renders
    # while he stays put can't refire it off a stale value) and the gap since `last_greeted_ts`, a
    # dedicated one-shot field mirroring `last_tended`'s pattern — belt and braces against however often
    # presence_line() actually ends up getting called in a given stretch.
    bonded = ph == "companion" or state.get("bond", 0) >= NAME_BOND
    # HER EARS (C2, J-2467, cat_overhaul): she comes to the SOUND of the gate, not to a timer — when her
    # ears took her to the gate (cat_ears stamps ears.gate_ts as she goes) the greeting fires on his
    # arrival regardless of the 20-minute clock; the clock stays as the floor for arrivals that pass no
    # gate (the study door; a leg the latch did not reach her on). The one-shot last_greeted_ts gate is
    # unchanged, so a greeting still fires at most once per arrival.
    try:
        _heard_gate = (now - float((state.get("ears") or {}).get("gate_ts") or 0.0)) < GREETING_GAP
    except Exception:
        _heard_gate = False
    # HIS CALL (C3, J-2468, cat_overhaul): she answered a call of his from elsewhere inside the same clock —
    # the answer came back as sound first (cat_sounds' trill), then her legs, and this arrival is its end:
    # the greeting fires, and the call's hold on her is released. An answer given in the room (answer_here)
    # was already his line — it does not greet him twice.
    try:
        _cs_call = state.get("call") or {}
        _heard_call = (now - float(_cs_call.get("answered_ts") or 0.0)) < GREETING_GAP and not _cs_call.get("answer_here")
    except Exception:
        _heard_call = False
    if bonded and act not in ("storm_hide", "missing") and not state.get("arc") and prev_seen \
            and ((now - prev_seen) > GREETING_GAP or _heard_gate or _heard_call) \
            and (now - state.get("last_greeted_ts", 0)) > GREETING_GAP:
        state["last_greeted_ts"] = now
        if _heard_gate and state.get("reaction") and (state.get("reaction") or {}).get("kind") == "gate":
            state["reaction"] = None   # met: the wait at the gate is over, the bout machine resumes
        if _heard_call and (state.get("reaction") or {}).get("kind") == "call":
            state["reaction"] = None   # she came to the call and he is here: the hold is over
        _save()
        her = _her()
        g = _quirks().get("greeting", "chirrup")
        greet_line = _pool("EVENTS", f"greeting_{g}") or {
            "gate_meet": random.choice([
                f"{her} is right there the moment you come in, as if she heard the gate — meets you at "
                f"the threshold, tail up, and falls in beside you.",
                f"{her} has plainly been waiting: she's at the door before you're properly through it, "
                f"tail a question mark, walking you in.",
            ]),
            "ankle_thread": random.choice([
                f"{her} appears the instant you're back and winds two tight figures around your ankles "
                f"before peeling off, satisfied you've been accounted for.",
                f"{her} threads herself around your legs, once around and back, a small brisk welcome "
                f"with no fuss in it.",
            ]),
            "chirrup": random.choice([
                f"{her} gives a short, rising chirrup the second she sees you — a sound she keeps for "
                f"exactly this — and comes over to be acknowledged.",
                f"{her} chirrups once, low in her throat, the small sound she saves for you walking "
                f"back in, and nothing else.",
            ]),
        }.get(g, f"{her} looks up the moment you're back, and something in her settles.")
        return greet_line
    if ph == "appearing":
        state["seen_count"] = state.get("seen_count", 0) + 1
        return random.choice([
            f"There is {LOOK} watching from the top of the garden wall; when you meet its eyes it goes still.",
            "The thin grey stray is on the doorstep again, keeping a careful distance, ready to bolt.",
            "Something moves at the edge of the garden — the stray cat, watching you, not yet trusting.",
        ])
    her = _her()
    # ── 10x CORPUS FIRST (2026-07-03): rich agent-written pools in cat_content.py; the inline lines
    # below remain as the fail-open floor. Signals + FIRSTS live here: her language of affection is
    # earned by bond and remembered forever (the first lap, the first slow blink → activity records).
    bond = state.get("bond", 0)
    _arced = {"returned": "returned", "live_mouse": "live_mouse", "gift_rat": "gift_rat",
              "zoomies": "zoomies", "storm_hide": "storm_hide"}
    key = _arced.get(act) or {"demanding_food": "demanding_food", "brought_a_mouse": "brought_a_mouse",
                              "self_fed": "self_fed"}.get(act)   # D-0163/J-0700
    if not key:
        key = _EARS_KEYS.get(act)   # C2 (J-2467): the states her ears put her in, each its own rotating pool
    if not key:
        key = {"garden_wall": "garden", "indoors": "by_the_fire"}.get(loc, loc)
    # high-bond signals (rare, hers to give): the slow blink, and — rarest — the silent meow. Companion TIER
    # (D-0505 (c), J-2472: from bond or the name; was phase == "companion" only); each keeps its own bond bar.
    if companion_tier() and act not in ("storm_hide", "missing"):
        if bond >= 0.9 and random.random() < 0.015:
            line = _first("first_silent_meow", "silent_meow") or _pool("EVENTS", "silent_meow")
            if line:
                _tier_log("silent_meow")
                return line
        if bond >= 0.75 and random.random() < 0.04:
            line = _first("first_slow_blink", "slow_blink") or _pool("EVENTS", "slow_blink")
            if line:
                _tier_log("slow_blink")
                return line
    # relationship firsts that ride ordinary states
    if loc == "on_your_lap":
        fl = _first("first_lap", "first_lap")
        if fl:
            return fl
    _shore_first = ""
    if loc == "shore":
        # 2026-08-18: a corpus entry now exists (was dead/empty) — kept as a LEAD-IN, not a replacement,
        # honoring the original design here (the ordinary shore line still renders every time).
        _shore_first = _first("first_shore_follow")
    # B4 (J-2473, D-0508; docs/staged/cat_overhaul.md §B4 under docs/staged/dosed_coupling.md): THE DOSED READ.
    # Everything above this line is its own occasion (the greeting once per arrival, the firsts once ever, the
    # blink and the silent meow on their own odds) and renders exactly as before. The ORDINARY line -- the body
    # lines, the PRESENCE corpus, the inline floor, now in _ordinary_line() below, moved verbatim -- is read at the
    # "idle scene" stop through core/cat_loop.gate(): a new state of hers rides (a surprise), the same cat asleep on
    # the rug rides again only on a habituating gap, he sees her again on coming back into the room, the
    # dispatcher may let an unusual stillness through early, and a ride stays up 90 s for every consumer of the
    # scene. Held = '' (no line this ask; she is still here -- is_here / look_line / the hands are untouched).
    # Fail-open: any error rides. The words of the line are unchanged; nothing numeric reaches it (D-0434).
    _cl = None
    try:
        from core import cat_loop as _cl
        _g = _cl.gate(_cl.STOP_SCENE, state, now, his_location)
    except Exception:
        _g = {"ride": True, "why": "fail_open"}
    if _g.get("why") == "pulse":
        return _g.get("line") or ""
    if not _g.get("ride"):
        return ""
    _LAST_PRESENCE_PLAIN = True      # J-3257: the ordinary tail was reached; _ordinary_line() clears it if the line carries more
    line = _ordinary_line(his_location, loc, act, key, ph, _shore_first)
    if _cl is not None:
        try:
            _cl.rode(_cl.STOP_SCENE, state, line, now, _g)
        except Exception:
            pass
    return line


def _loop_out_of_sight() -> None:
    """B4 (J-2473): presence_line asked at the idle-scene stop and she was not in his sight. Fail-open."""
    try:
        from core import cat_loop as _cl
        _cl.out_of_sight(_cl.STOP_SCENE, state, time.time())
    except Exception:
        pass


def _ordinary_line(his_location: str, loc: str, act: str, key: str, ph: str, _shore_first: str) -> str:
    """The ORDINARY presence line -- the body lines (B1), the PRESENCE corpus, the inline fail-open floor and the
    standing nameless occasion -- moved here VERBATIM from the tail of presence_line() by J-2473 (B4) so the dosed
    read above can decide whether it renders this ask. Same inputs, same pools, same odds, same words."""
    global _LAST_PRESENCE_PLAIN
    her = _her()
    # THE BODY (B1, J-2465): the states the budgets add — a drink at the water, the night prowl, the long
    # day sleep, and where the warmth took her — each a rotating pool of its own (see _BODY_LINES), each
    # ahead of the corpus only when the state IS that; the corpus line stays the default.
    _bl = ""
    try:
        _b = state.get("body") or {}
        _w = float(_b.get("warmth", 0.5))
        if act == "drinking" and loc in WATER_AT:
            _bl = _body_line("drinking", water=WATER_AT[loc])
        elif act == "prowling":
            _bl = _body_line("prowling")
        elif act in _RESTING and random.random() < 0.4:
            if loc in ("by_the_fire", "on_your_lap", "under_desk", "indoors") and _w < COLD_BAND and loc == "by_the_fire":
                _bl = _body_line("cold_seek")
            elif loc == "windowsill" and _w >= 0.5 and _conds() & {"bright", "day"} == {"bright", "day"}:
                _bl = _body_line("sun_seek")
            elif loc in ("under_desk", "garden") and _w > HOT_BAND:
                _bl = _body_line("shade_seek")
            elif act == "sleeping" and _b.get("bout") == "sleep" and "day" in _conds():
                _bl = _body_line("day_sleep")
    except Exception:
        _bl = ""
    if _bl:
        _LAST_PRESENCE_PLAIN = False     # J-3257: a body line says more than where she is
        if his_location == "study" and state.get("fur_moisture", 0.0) > 0.20:
            _bl += " Her coat is cool and damp with rain from outside."
        return _bl
    line = _pool("PRESENCE", key)
    if line:
        if _shore_first:
            line = _shore_first + " " + line
        try:   # D-2 (J-2471): what he can see of a hurt — she favours a foreleg, the torn ear — dosed, never a word that judges
            from core import cat_harm as _ch
            _hc = _ch.clause(state)
            if _hc and act not in ("storm_hide", "missing"):
                _LAST_PRESENCE_PLAIN = False     # J-3257: a hurt she carries rides this line
                line += " " + _hc
        except Exception:
            pass
        # THE STANDING OCCASION (see below) applies to corpus lines too
        if ph == "kept" and not state.get("name") and state.get("name_invited") and random.random() < 0.3:
            _LAST_PRESENCE_PLAIN = False     # J-3257: the nameless note rides this line
            line += random.choice([" She has no name yet.",
                                   " She is still without a name; no one can give her one but you.",
                                   " Wholly yours, and still nameless."])
        if his_location == "study" and state.get("fur_moisture", 0.0) > 0.20:
            _LAST_PRESENCE_PLAIN = False     # J-3257: so does the damp coat
            line += " Her coat is cool and damp with rain from outside."
        return line
    # ── fail-open floor: the original inline pools ──
    if act == "brought_a_mouse":
        line = random.choice([
            f"{her} has dropped a dead mouse by your chair and sits looking at you, plainly expecting praise.",
            f"{her} arrives with a mouse, lays it precisely on the doorstep, and looks from it to you and back.",
            f"there is a small dead thing on the mat, and {her} beside it, immensely satisfied with the arrangement."])
    elif act == "demanding_food":
        line = random.choice([
            f"{her} is at the door, loud and insistent, winding figures-of-eight and demanding to be fed.",
            f"{her} states her case at the door — one flat vowel, repeated, until the saucer happens.",
            f"{her} threads your ankles, purring with intent; the message could not be plainer."])
    elif act == "self_fed":   # D-0163/J-0700: caught her own dinner — the hunting fallback
        line = random.choice([
            f"{her} comes back through the long grass already fed, whiskers marked, and wants nothing from you just now.",
            f"{her} sits washing her face by the hedge, a scatter of small feathers at her feet, entirely pleased with herself.",
            f"{her} has caught her own dinner somewhere out of sight; she is full, unhurried, and in no mood to be handled.",
            f"There is fur on her chin and something's tail in the grass by the hedge; {her} has already eaten and is not asking for anything."])
    elif loc == "on_your_lap":
        line = random.choice([
            f"{her} is a warm weight in your lap, the small engine of her going.",
            f"{her} has claimed your lap and kneads once, twice, then settles as if a decision has been closed.",
            f"{her} sleeps in your lap; when you shift she puts one paw on your arm without opening her eyes."])
    elif loc == "on_the_desk":
        line = random.choice([
            f"{her} is sitting square on your open book, tail laid over the page, entirely unbothered.",
            f"{her} has arranged herself across your papers; the notched ear tips toward you when you lean in.",
            f"{her} bats the pen once, watches it roll to the desk's edge, and looks at you as it drops."])
    elif loc == "by_the_fire":
        line = random.choice([
            f"{her} is curled by the fire, a tight warm circle, {act}.",
            f"{her} lies flank-to-the-embers, paws folded under, eyes shut to slits against the light.",
            f"{her} has turned herself over by the grate and sleeps on her back, entirely certain of the room."])
    elif loc == "windowsill":
        line = random.choice([
            f"{her} is on the windowsill, {act}, one eye on the weather.",
            f"{her} sits at the glass, tail-tip ticking, tracking something out in the wind only she rates.",
            f"{her} is loafed on the sill, chin tucked, the grey of her almost the grey of the sky beyond."])
    elif loc == "shore":
        line = random.choice([
            f"{her} has followed you down, in her own fashion — twenty steps behind, pretending otherwise.",
            f"{her} is above you on the cliff path, sitting neat as a jug, watching you and the sea both.",
            f"{her} stalks something in the dune grass, flattened, tail-tip the only thing moving."])
    elif loc in ("garden", "garden_wall"):
        line = random.choice([
            f"{her} is out in the garden, {act}.",
            f"{her} is flattened in the grass near the bed, {act} — the birds know exactly where she is.",
            f"{her} walks the fence line like it is hers, which by now it is.",
            f"{her} sits bolt upright, absolutely still, staring at the far wall — the black cat is out "
            f"there again, and she watches it the whole time without one flick of her tail."])
    elif loc == "wood":
        line = random.choice([
            f"{her} has come down into the wood too, a grey shape slipping between the trunks after the leaf-litter.",
            f"{her} is up on a low branch above you, tail hanging, watching you gather with lofty interest.",
            f"{her} stalks something in the undergrowth, flattened, only her tail-tip moving, ignoring you utterly."])
    else:
        line = f"{her} is here, {act}."
    # THE STANDING OCCASION (2026-07-03, the naming-wiring fix): the invitation used to be a ONE-SHOT
    # line (shown once, Jul01, never again — invisible to a mind whose attention moves in minutes). A
    # kept, warm, unnamed cat now carries her namelessness quietly and occasionally — a fact, not a nag.
    if ph == "kept" and not state.get("name") and state.get("name_invited") and random.random() < 0.3:
        _LAST_PRESENCE_PLAIN = False         # J-3257: the nameless note rides this line
        line += random.choice([" She has no name yet.",
                               " She is still without a name; no one can give her one but you.",
                               " Wholly yours, and still nameless."])
    return line


def _his_place_is_study() -> bool:
    """J-2934 (F-3623, P-0031): is Du in the study? The same location source scene_line() uses
    (core/sensorium.state['location'], default 'study' when the key is absent). FAIL-CLOSED: if the sensorium
    cannot be read the answer is False -- a warmth note that does not arrive costs nothing, one that names a cat
    'beside you' while he stands on the shore is a wrong world statement (founder law: mention nothing absent)."""
    try:
        from core import sensorium as _room
        if not _room.state:
            _room._load()
        return (_room.state.get("location") or "study") == "study"
    except Exception:
        return False


def felt_state():
    """J-1955 (D-0368 A): the STATE felt_note() reports on -- (location, tier) or None. The edge gate
    (core/steer_edge.py) delivers the note when this changes (the cat arrives / moves / the bond tier shifts),
    not on every prompt while she simply stays.
    J-2934 (F-3623): None unless Du is in the study -- the note is about the cat beside him, and every one of her
    felt spots is a study spot. (The call site only asks the edge gate when felt_note() is non-empty, so a
    suppressed tick never consumes or re-arms an edge.)"""
    _load()
    # companion TIER (D-0505 (c), J-2472): from bond or the name; the 0.4 floor stays for a named cat whose bond
    # has since decayed (bond_decay) — the tier is a bar, not a licence
    if not companion_tier() or state.get("bond", 0) < 0.4:
        return None
    loc = state.get("location")
    if loc in ("on_your_lap", "by_the_fire", "on_the_desk", "windowsill", "mantel"):
        if not _his_place_is_study():
            return None
        return (loc, "high" if state.get("bond", 0) >= 0.75 else "mid")
    return None


def _felt_conds(loc: str) -> set:
    """J-2934: the extra pool conditions felt_note() draws under -- her spot, and the grate's state when it is
    lit -- so a FELT line asserts only what the study shows. Fail-open to the spot alone."""
    c = {str(loc)}
    try:
        from core import sensorium as _room
        if (_room.state or {}).get("fire") == "burning":
            c.add("fire_burning")
    except Exception:
        pass
    return c


def felt_note() -> str:
    """The warmth a present, bonded cat brings to his mood — for the idle prompt. '' unless it earns a line.
    J-2934 (F-3623): '' unless Du is in the study, and the line is drawn under her actual spot and the fire's
    state (core/cat_content.FELT is a condition dict now) -- never a fixed spot, a lit fire or an hour of the day."""
    _load()
    if not companion_tier() or state.get("bond", 0) < 0.4:    # D-0505 (c), J-2472: from bond or the name (see felt_state)
        return ""
    loc = state.get("location")
    if loc in ("on_your_lap", "by_the_fire", "on_the_desk", "windowsill", "mantel"):
        if not _his_place_is_study():
            return ""
        tier = "high" if state.get("bond", 0) >= 0.75 else "mid"
        line = _pool("FELT", tier, _felt_conds(loc))
        _tier_log("felt", tier=tier)
        if line:
            return "\n\n" + line
        return (f"\n\nThere is a warmth in the room that is not the fire — {_her()} near you, asking nothing, "
                f"and something in you is quieter for it.")
    return ""


# ── THE DISTANT CAT (2026-07-04-adjacent, founder): a SECOND cat, black, that lives somewhere else and is
# only ever seen far off — the far wall, the neighbour's ridge, the headland. It never approaches, never
# interacts, cannot be tamed (it is not a relationship; it is a cat in the world — INDIFFERENT life). Its
# whole function is honest: with two cats, "the cat" stops referring — a NAME becomes functionally
# necessary, not philosophically requested. His grey companion may WATCH it; they never meet.
_DISTANT_SPOTS = {"garden": ("the far wall", "the neighbour's ridge", "the fence line at the very bottom"),
                  "shore": ("the headland", "the top of the cliff path", "the rocks at the far end")}
_DISTANT_P = 0.05          # rare: a few sightings a day, mostly day/dusk


def distant_line(his_location: str) -> str:
    """An occasional far-off sighting of the OTHER cat. '' almost always. Never interactive."""
    _load()
    # B3 (J-2470, core/cat_tom, D-0507 (c)): while the tom is IN THE GARDEN he is close, not far off — his own
    # presence line (dosed once per visit) answers instead of the far-off roll below. On the ridge, the far-off
    # sighting is exactly what it always was (it is him up there).
    try:
        from core import cat_tom as _ct
        if _ct.in_garden():
            return _ct.presence_line(his_location, state)
    except Exception:
        pass
    try:
        from core import sensorium as _room
        phase = _room._daylight()
        weather = (_room.state or {}).get("weather", "")
    except Exception:
        phase, weather = "day", ""
    # 2026-08-19: routed the storm half through the shared classifier (was "storm" in weather, a loose
    # substring match). Deliberately narrower than is_wet() still — a distant sighting only hides for
    # genuine storm/steady rain, not mere drizzle — that scope is preserved exactly, just named now.
    from core import weather_conditions as _wcond
    if phase == "night" or _wcond.is_storm(weather) or weather == "steady rain":
        return ""
    spots = _DISTANT_SPOTS.get(his_location if his_location != "study" else "garden")
    if not spots:
        return ""
    p = _DISTANT_P * (2.0 if phase == "dusk" else 1.0)
    if random.random() > p:
        return ""
    d = state.setdefault("distant", {"seen_count": 0, "last_seen": 0.0})
    d["seen_count"] = d.get("seen_count", 0) + 1
    d["last_seen"] = time.time()
    _save()
    spot = random.choice(spots)
    via = "Through the window, far off: " if his_location == "study" else ""
    return via + random.choice([
        f"a black cat is sitting on {spot}, a long way off, looking at nothing in particular.",
        f"a black cat crosses {spot} at its own pace and is gone behind the harakeke.",
        f"there is a black cat out on {spot} — too far to see more than the shape of it, sitting very still.",
        f"the black cat again, away on {spot}; it does not look toward the cottage, and never has.",
    ])


def distant_look(his_location: str = "") -> str:
    """He deliberately looks for the OTHER cat — usually absence (it lives its own life, elsewhere).
    B3 (J-2470): while the tom is in the garden, core/cat_tom answers the look — close, feature-first (D-0129),
    a sighting in life's ledger; '' from it means he is on the ridge and the far-off answer below stands."""
    _load()
    try:
        from core import cat_tom as _ct
        _tl = _ct.look(his_location) if his_location else ""
        if _tl:
            return _tl
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    d = state.get("distant") or {}
    if d.get("last_seen") and time.time() - d["last_seen"] < 600:
        return ("You find the black cat where it was — far off, a small dark shape, entirely occupied with "
                "its own affairs. It has never once come nearer, and gives no sign it ever will.")
    if d.get("seen_count"):
        return ("You look for the black cat along the far wall and the ridge: nothing today. "
                "It comes and goes on its own account, a long way off.")
    return "You look out across the fences and the ridge: no cat out there just now."


def look_line(his_location: str, target: str = "") -> str:
    """He deliberately LOOKS at her — closer observation than ambient presence. 10x (2026-07-03): the one
    being he loves most was the one thing in his world he could not look at (every barrel and fence post was
    lookable; the cat was not)."""
    _load()
    # DISAMBIGUATION (the distant cat's whole point): "the OTHER/black/far cat" → not her.
    _t = (target or "").lower()
    if _t:
        _note_referent("look", _t, place=his_location)   # B2 (J-2472): which cat did he look for? recorded, never answered
    if any(w in _t for w in ("other", "black", "distant", "far ", "second", "strange", "that cat")) \
            or re.search(r"(?<![a-z-])(?:tom|tomcat|big cat|intruder|stranger)(?![a-z-])", _t):   # B3 (J-2470): the tom's own words
        return distant_look(his_location)
    ph = state.get("phase")
    if ph == "absent":
        return "There is no cat. There was never a cat here — only the memory of the stray, if that."
    if ph == "dead":
        # D-2 (J-2471, D-0506): her body where it lies (and he is), the grave in its place, else the honest nothing
        try:
            from core import cat_harm as _ch
            return _ch.look(state, his_location, _t)
        except profile.NonLiveWriteError:
            raise
        except Exception:
            return f"You look for {_her()}: nothing."
    loc, act = state.get("location"), state.get("activity")
    if loc == "in_transit":   # LEGS (B1, J-2465): a look catches her crossing, or misses her between places
        _tl_line = _transit_line(his_location)
        if _tl_line:
            state["last_seen"] = time.time()
            return "You look for " + _her() + " — " + _tl_line[:1].lower() + _tl_line[1:]
        return f"You look for {_her()}: not here just now. Out on her own business somewhere."
    if loc not in _VISIBLE.get(his_location, set()):
        if (state.get("arc") or {}).get("kind") == "gone_missing":
            return _pool("EVENTS", "gone_missing") or f"You look for {_her()} — nothing. {_saucer_absence_line(cap=True)}."
        if ph == "appearing":
            return f"You look for {_her()}: not here just now. The wall top is empty."
        # C4 (J-2469): seeking is a real search -- look in her spots in his order (a hidden cat in his place is
        # found by chance, then by habit), the ear's last word on her, the roof's glimpse, the wall's nothing
        try:
            _sl_line = _seek_look(his_location, _t, time.time())
            if _sl_line:
                return _sl_line
        except profile.NonLiveWriteError:
            raise
        except Exception as exc:
            logger.debug("[cat] seek look failed (non-fatal): %s", exc)
        return f"You look for {_her()}: not here just now. Out on her own business somewhere."
    extra = set()
    if act in ("sleeping", "dozing"):
        extra.add("sleeping")
    else:
        extra.add("awake")
    if state.get("bond", 0) >= 0.75:
        extra.add("high_bond")
    line = _pool_flat("LOOK", extra) or presence_line(his_location) or f"{_her()} is here, {act}."
    if ph == "kept" and not state.get("name") and state.get("name_invited") and random.random() < 0.4:
        line += " She has no name yet; that is still yours to give."
    # THE BODY (B1, J-2465): condition shows to a look at either end — her coat and flesh in prose, the
    # world answering a look; never a number.
    try:
        _cc = _condition_clause()
        if _cc:
            line += " " + _cc
    except Exception:
        pass
    try:   # D-2 (J-2471): a look notices a hurt, an illness, old age, an old scar — prose, dosed, no verdict
        from core import cat_harm as _ch
        _hc = _ch.clause(state)
        if _hc and act not in ("storm_hide", "missing"):
            line += " " + _hc
    except Exception:
        pass
    return line


# ── His hands — tending, and the naming ────────────────────────────────────────────────────────────
# ── A2 trigger narrowing (2026-09-07, J-0631/F-0880) ────────────────────────────────────────────────
# Live evidence: 375 react() fires since 08-29 (23 distinct lines, top line 41x). Bare "she"/"her" in
# the old combined word list meant ANY thought about anything feminine fired a stroke while she
# happened to be co-located ("I asked the library for a book about ghosts" -> "the cat headbutts your
# knuckles"), and "hold"/"holding"/"approach" in the old verb list meant the same for any thought
# about holding or approaching anything at all. Narrowed on two axes:
#  1. _CAT_NOUNS (+ her own name, checked separately in react()) always refer; a bare "she"/"her" only
#     refers when the thought IMMEDIATELY BEFORE this one already named her — a 2-line anaphora
#     window, tracked in _prev_ref_txt below (in-memory only, like _last_tick above: losing 2 lines
#     of discourse memory across a restart is the honest floor, not a bug worth persisting state for).
#  2. "hold"/"holding"/"approach" are too ambiguous to trust alone and move to their own tuple,
#     checked in react() only when THIS SAME thought also names her outright (a noun or her name, not
#     anaphora) — every other tend verb keeps working exactly as before.
_TEND_VERBS = ("feed", "feeding", "fed", "pet", "petting", "stroke", "stroking", "scratch",
               "pick up", "sit with", "play", "playing", "coax", "crouch", "tempt",
               # C3 (J-2468, cat_overhaul): "call to" was here — calling her was a stroke. It is its own hand
               # now (core/cat_call via _maybe_call below, read BEFORE the here-gate: the point of a call is
               # that she is not here). A call that the hand does not take is not a tend either.
               "saucer", "milk", "let .* in", "let her in", "let it in", "talk to", "tend", "lap",
               "scraps")   # D-0508/D-4 (J-2466): "give her the scraps" is a feed hand, like "saucer"/"milk" already are
_TEND_VERBS_NOUN_GATED = ("hold", "holding", "approach")
_CAT_NOUNS = ("cat", "kitten", "stray", "moggy")
_WAKE_WORDS = ("wake", "waking", "wakes", "woke", "rouse", "rousing", "roused", "disturb", "disturbing")

_prev_ref_txt = ""   # the anaphora window: previous react() call's lowered thought+intention text


def visible_from(place: str, location: str) -> bool:
    """Whether cat-location `location` can be seen/heard from Living-World `place` -- the _VISIBLE
    truth, parameterized (2026-09-07, A7.3, J-0632/F-0886) for callers that already hold their own
    freshly-read location string (the HUD's map renderers) rather than going through this module's
    own cached `state`. NOT the same question as place_of(): 'doorstep' is deliberately visible from
    BOTH study (through the door) and garden (she's right there) in _VISIBLE, whereas place_of()
    deliberately collapses it to exactly one place ('garden') for life.py's single-occupancy
    presence/threat bookkeeping. Using place_of() here would wrongly hide her from the study map
    whenever she's on the doorstep -- caught by this fix's own verification script before it shipped."""
    return location in _VISIBLE.get(place, set())


def is_here(his_location: str) -> bool:
    """True when the cat is present AND where he is — i.e. she is something he can act on right now. The
    availability test for the cat affordance; mirrors presence_line's visibility check."""
    _load()
    if state.get("phase") in ("absent", "dead"):   # D-2 (J-2471): a dead cat is not here to be tended (her body is cat_harm.hand's)
        return False
    loc = str(state.get("location") or "")
    if loc in HIDDEN_SPOTS:
        # C4 (J-2469): a hidden cat is handleable only once he has FOUND her there (a look), for FOUND_WINDOW_S,
        # and never where he cannot reach (the roof, the far side of the wall)
        spec = HIDDEN_SPOTS[loc]
        f = (state.get("seek") or {}).get("found") if isinstance(state.get("seek"), dict) else None
        return bool(spec["reach"] and spec["place"] == his_location and isinstance(f, dict) and f.get("loc") == loc
                    and (time.time() - float(f.get("ts") or 0.0)) <= FOUND_WINDOW_S)
    return visible_from(his_location, loc)


# ── REAL FOOD (2026-09-07, D-0163/D-4, J-0719) ──────────────────────────────────────────────────────
# A3's original audit finding: "there is nothing to feed her with: no cat food, fish, milk, or scraps
# exist in data/provisions.json" — react()'s fed branch used to just text-match "feed"/"saucer"/"milk"/
# "tempt" and conjure a meal from nothing, the same class of leak the fire chain (T-0049) already closed
# for matches. `core/provisions.py` now carries a real "cat_food" kind (a tin of fish, following the
# exact matches/candles/oil pattern) that starts at zero — nobody here had a cat before her — and is
# only ever refilled by a real acquisition: the carrier (core/supply.py, D-4's own build order).
# Only the larder was wired at first. Scraps from a meal of his own and fish he catches at the shore
# are real alternate sources the plan names too (docs/staged/cat_overhaul.md §B1) — checked, not
# assumed: Du has no modelled meal of his own anywhere in the repo to take scraps FROM (still true,
# still unbuilt — a meal system is its own separate follow-up, not a side effect of a cat job), but
# core/shore_life.py's own fishing gap is closed as of 2026-09-07 (J-0732/F-1055): catch_fish() is a
# real deed there now, and a success calls core.provisions.add("shore_fish", ...) — a second real kind
# alongside cat_food, tried here as the fallback once the carrier's tin runs out.
#
# SHORE_FISH SPOILS (2026-09-08, J-0755/F-1079): every other kind in provisions.py, cat_food included,
# is realistically non-perishable — a raw fish is not, and nothing this house's world model has ever
# established (no ice, no fridge, no smokehouse or salt-curing anywhere in the repo) keeps one good
# indefinitely. Rather than build a generic expiry concept into provisions.py's own shared stock()/
# consume()/add() (load-bearing for all 18 OTHER kinds — a materially larger, riskier change than one
# new kind deserves, the foundation-erosion this project's own standing rule warns against), the check
# is scoped here, narrowly, to this one kind's one real consumer: _shore_fish_ready() below reads each
# candidate's own `history[0]["ts"]` (the real catch time — catch_fish()'s own "caught off the shelf's
# edge..." entry) via provisions.discard_if_stale(), a function nothing else in the repo calls, and
# quietly discards (never narrated — a spoiled fish quietly gone is honest, not something the world
# needs to announce) anything older than SHORE_FISH_SPOIL_H before it would otherwise be fed.
SHORE_FISH_SPOIL_H = 36.0   # a real-world-grounded ESTIMATE, not tuned against any Nascence data — none
                            # exists yet (confirmed this job: the live process has never run code past
                            # 2026-09-05, before shore_fish existed at all). A whole fresh fish kept cool
                            # but unrefrigerated and uniced is genuinely good for about a day and going
                            # off by the second, so 36h sits in the middle of the founder's own "roughly
                            # a day or two" framing for this gap rather than either edge. Revisit once
                            # real evidence exists (J-0754, this same finding's own sibling follow-up).

# MILK SPOILS TOO (2026-10-28, cat_overhaul §B1 / §4 D-4, D-0508, J-2466). The jug is the carrier's second
# standing line for her (core/supply.py GOODS "milk"; core/provisions.py KINDS "milk", qty 4 "saucers").
# It is checked exactly the way the fish is, and for the same reason: nothing in this house keeps anything
# cold (no ice, no fridge, no cold store anywhere in the repo), so a jug sitting in the cupboard under the
# east shelf does not last. SHORE_FISH_SPOIL_H above is the precedent, and this is the same KIND of number:
# a real-world-grounded ESTIMATE, not tuned against any Nascence data (none exists -- no jug has ever been
# in this house before this build). Fresh milk kept in a cool room, unrefrigerated, is good for a day,
# doubtful by the second and sour by the third; a stoppered stoneware jug in a cupboard buys a little over
# an open pail, so 48 h sits between "a day" and "two days" rather than at either edge -- a touch longer
# than the fish (36 h), which is right: a raw fish goes before milk does. Spoiled milk is discarded quietly
# at the one place it is spent (_milk_ready(), via provisions.discard_if_stale(), J-0755's own narrow
# pattern), never narrated -- a jug gone off and tipped out is not news the world needs to announce. Revisit
# with real evidence once the carrier has actually brought a jug (the D-0508 read job).
MILK_SPOIL_H = 48.0
# A saucer of milk is a different feed from a tin, and the line says which (rotating pools, never one fixed
# string). {her} is filled by _her(). Milk is mostly a drink: MEAL_HUNGER["milk"] is small, MEAL_THIRST large.
_FEED_MILK_LINES = (
    "You pour a little milk into the saucer; {her} is at it before you have straightened up, lapping fast, "
    "the tip of her tail going.",
    "You tip the jug over her saucer and {her} drinks with her eyes shut, a quick wet ticking, then sits "
    "and cleans her whiskers of it.",
    "A saucer of milk, set down by the door. {her} crouches to it and laps until the saucer scrapes on the "
    "flags, empty.",
)
_FEED_SCRAPS_LINES = (
    "You shake the scraps out of their paper onto her saucer; {her} eats them with her head on one side, "
    "picking, and leaves nothing.",
    "You give {her} the scraps you kept back; she takes them off the saucer one piece at a time and looks up "
    "between each, in case there is more.",
    "The twist of scraps goes onto the saucer. {her} eats, not as if she were starving but as if it were owed "
    "her, and winds once against your shin after.",
)
_SAUCER_MILK_LINES = (        # _saucer_absence_line, the saucer holding milk while she cannot be found
    "her saucer of milk sits by the door, a skin forming on it, not yet touched",
    "the milk you put down for her still stands in the saucer by the door, going warm",
)


def _milk_ready() -> bool:
    """The jug's twin of _shore_fish_ready() below, same contract: discards (never narrated) any milk
    object older than MILK_SPOIL_H since it was delivered (add()'s own history[0]["ts"]), then reports
    whether a still-good jug is left. Shared by _has_real_food() and _feed_source() so the affordance
    and the spend always agree on the same jug. Bounded the same way (the 50 cap is defensive only)."""
    try:
        from core import provisions as _pv
    except Exception:
        return False
    for _ in range(50):
        if _pv.stock("milk") <= 0:
            return False
        if not _pv.discard_if_stale("milk", MILK_SPOIL_H * 3600,
                                     "gone sour in the cupboard with nothing to keep it cold; tipped out"):
            return True
    return False


def give_scraps(qty: float = 1.0, note: str = "") -> str | None:
    """D-0508/D-4 (J-2466): scraps from a meal, put by for her -- the ONE credit path for the "scraps"
    kind (core/provisions.py KINDS). A real event credits a real object (provisions.add_found(), the
    passive-credit shape D-0253's found scrap already uses, under its own "found" log event) and
    reconciles the study's cached count so sync() never reads the new twist as "he used the difference"
    (J-0573/F-0787, the same credit supply.collect_box() does). The feed branch then spends it like any
    other source. Returns the new object's id, or None if nothing was really credited. Du has no
    modelled meal of his own to take scraps FROM (checked this job: core/actions.py's only intake is
    tea; Travis's own carrier book says he does not eat), so nothing in the repo calls this yet -- it
    is the honest hook, not a conjured source; see the J-2466 finding addressed to Travis."""
    try:
        from core import provisions as _pv
        oid = _pv.add_found("scraps", qty, note=note or "the end of a meal, folded into a twist of paper for her")
        if oid:
            try:
                from core import study_life as _sl
                st = _sl._st()
                st[_pv.KINDS["scraps"][2]] = _pv.stock("scraps")
            except Exception:
                pass
        return oid
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return None


def note_kill(species: str, now: float | None = None) -> None:
    """D-0508/D-4 (J-2466): her kills feed HER budget -- the one hook another module's kill path calls so
    a fledgling she takes (core/garden_life.py's own nest roll) lands on her hunger exactly the way her
    hunting-fallback catch already does (_maybe_self_feed -> eat()). Loads, eats, saves; fail-open."""
    try:
        _load()
        eat(species, now)
        _save()
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass


def hunger_level() -> float | None:
    """Her hunger budget (0..1) for another world module's OWN roll (core/garden_life.py: a fed cat leaves the
    fledglings alone more, §B1). None when she has no body yet (an old state). NEVER a prompt-path reader:
    this is the world deciding what she does, not anything he is told (D-0434)."""
    try:
        _load()
        b = state.get("body")
        if not b:
            return None
        return max(0.0, min(1.0, float(b.get("hunger", 0.0))))
    except Exception:
        return None


def _shore_fish_ready() -> bool:
    """Read-only from the CALLER's point of view, but does real bookkeeping: discards (never narrated)
    any shore_fish object that has gone past SHORE_FISH_SPOIL_H since it was caught, then reports
    whether a still-good one is left. Shared by _has_real_food() (the affordance's own honesty check)
    and _feed_source() (the actual spend) so both always agree on the same fish — an affordance that
    says 'feed her' and a feed attempt that then discovers only a spoiled fish would be its own small
    dishonesty. Bounded loop: each pass permanently discards one candidate or returns, so it cannot
    spin forever (the cap is defensive only — 50 real uneaten fish stacked up is not a real scenario
    given catch_fish()'s own 3-hour cooldown)."""
    try:
        from core import provisions as _pv
    except Exception:
        return False
    for _ in range(50):
        if _pv.stock("shore_fish") <= 0:
            return False
        if not _pv.discard_if_stale("shore_fish", SHORE_FISH_SPOIL_H * 3600,
                                     "gone off in the larder with no fridge or curing; thrown out"):
            return True   # the oldest survivor is still within the freshness window
    return False


def _has_real_food() -> bool:
    """Read-only: is there anything real to put in her saucer right now? affordance_line() uses this so
    'feed her' is never offered as a live possibility when it would just fail — an honest affordance,
    not a promise the larder can't keep. Checks BOTH real sources (J-0732): the carrier's cat_food and
    a still-fresh shore-caught fish (J-0755) — a spoiled one counts no more than an empty tin does."""
    try:
        from core import provisions as _pv
        # D-0508/D-4 (J-2466): scraps put by and a still-fresh jug of milk are real food too, in the same
        # honest sense -- a sour jug counts no more than a spoiled fish does.
        return (_pv.stock("cat_food") > 0 or _shore_fish_ready()
                or _pv.stock("scraps") > 0 or _milk_ready())
    except profile.NonLiveWriteError:
        # J-0755: _shore_fish_ready() can now do a real write (discarding a spoiled fish, via
        # provisions.discard_if_stale()) — let D-0179's hard-raise (guard_path(), F-1024) reach this
        # function's own caller instead of being swallowed here, matching every other real write path
        # in this file (J-0733).
        raise
    except Exception:
        return False


def _feed_source(prefer_milk: bool = False) -> str:
    """Find something real to feed her AND take it from the house, in one call (so two react() hits in
    the same tick can't both see the last tin). Returns the provisions kind actually spent, or '' when
    the house genuinely has none — the caller then answers honestly instead of conjuring a meal.
    cat_food (the carrier's tin) is tried FIRST, unchanged from J-0719 — it is already built and the
    simplest, most reliable source; shore_fish (J-0732, a real catch at the shore) is the fallback once
    the larder's own tin is empty, not a replacement for it. A spoiled shore_fish (J-0755) is never fed:
    _shore_fish_ready() discards it first and this then falls through exactly as if that catch had
    never been made.

    F-1136 (2026-09-08, J-0789): consume() used to return None unconditionally, so a real disk-write
    failure on the decrement looked identical to a real feed -- this function called it as a bare
    statement and returned the kind name regardless. consume() now reports whether the decrement was
    actually confirmed written to disk (J-0789's own fix to provisions.py), and a False here is treated
    exactly like _has_real_food() already treats an empty tin: nothing real to spend, fall through to
    the next source (or to '' if none is left) rather than reporting a kind that was never really
    debited.

    D-0508/D-4 (2026-10-28, J-2466): two more real sources behind the first two, in this order -- scraps
    put by (a twist is one small meal; the tin still comes FIRST, unchanged, so nothing J-0719 built
    moves) and then a still-fresh jug of milk, a saucer at a time
    (_milk_ready() tips out a sour jug first, exactly as the fish). `prefer_milk` -- his own words asked
    for milk ("a saucer of milk for her") and there is a good jug: the saucer gets milk ahead of the tin;
    with no jug in the house the ask falls through to whatever there is, and with nothing at all it
    fails honestly like every other feed."""
    try:
        from core import provisions as _pv
        if prefer_milk and _milk_ready() and _pv.consume("milk", 1, by="Du"):
            return "milk"
        if _pv.stock("cat_food") > 0 and _pv.consume("cat_food", 1, by="Du"):
            return "cat_food"
        if _shore_fish_ready() and _pv.consume("shore_fish", 1, by="Du"):
            return "shore_fish"
        if _pv.stock("scraps") > 0 and _pv.consume("scraps", 1, by="Du"):
            return "scraps"
        if _milk_ready() and _pv.consume("milk", 1, by="Du"):
            return "milk"
    except profile.NonLiveWriteError:
        # J-0755: matches _has_real_food() just above — do not let a real discard get silently
        # swallowed as plain "no food" by this function's own bare except below.
        raise
    except Exception:
        pass
    return ""


def affordance_line(his_location: str) -> str:
    """The 'what you can do WITH HER right now' hand, surfaced into his affordances (2026-07-07) — the tending
    engine already existed in react(), but the cat was never in his self-knowledge, so she read as mere ambient
    presence. State-aware, and phrased to overlap the tend-verbs ('feed her', 'sit with her', 'play with her',
    'let her in') so a natural want lands on react(). '' when she is not here. She is not a button: an aloof or
    frightened cat gives little back, and the line says so — tending is a reading of HER, not a vending machine."""
    _load()
    try:   # D-2 (J-2471): her body found -> the spade (only once he HAS found her); ill -> leave her be. '' otherwise.
        from core import cat_harm as _ch
        if state.get("phase") == "dead" or _ch.is_ill(state):
            _ha = _ch.affordance(state, his_location)
            if _ha or state.get("phase") == "dead":
                return _ha
    except Exception:
        pass
    if not is_here(his_location):
        return ""
    her = _her()
    ph, act, mood = state.get("phase"), state.get("activity"), state.get("mood")
    arc = (state.get("arc") or {}).get("kind")
    if ph == "appearing":
        return ("coax the wary STRAY — crouch and hold still, talk low, or set down a saucer; she is not yours "
                "yet, and only patience (never a grab) will bring her in")
    if arc == "live_mouse" or act == "live_mouse":
        return (f"deal with the live MOUSE {her} has loosed indoors — corner it under a cup and carry it out "
                "(she will supervise, unimpressed)")
    if act in ("brought_a_mouse", "gift_rat") or mood == "proud":
        return (f"receive {her}'s GIFT — she has laid a mouse at your feet and watches for your face; take it as "
                "the offering it is, then sit with her or feed her")
    if act == "demanding_food" or mood == "insistent":
        # D-0163/D-4 (2026-09-07, J-0719): don't offer "feed her" as a live possibility when the larder
        # is empty -- an honest affordance, not one the house can't make good on.
        if _has_real_food():
            return (f"feed {her}, or let her in out of the weather — she is at the door, loud and insistent")
        return (f"let {her} in out of the weather, at least — she is at the door, insistent, but the "
                "larder has nothing for her; she'll have to wait on the carrier, on a fish caught fresh "
                "at the shore, or on hunting for herself")
    if act == "self_fed" or mood == "sated":   # D-0163/J-0700: she just fed herself, hunting
        return (f"leave {her} to it — she has already caught and eaten her own dinner and wants "
                "little from you just now; sit with her only if she allows it")
    if act == "storm_hide" or mood == "afraid":
        return (f"sit with {her} quietly — she is frightened by the storm and wants nearness pressed close, "
                "not handling")
    if mood in ("playful", "possessed") or act in ("zoomies", "stalking something"):
        return (f"play with {her} — she is in a mad half-hour; trail a bit of string or a driftwood twig and let "
                "her hunt it (or feed her, or just watch)")
    if state.get("location") == "on_your_lap":
        return (f"stroke {her} where she has claimed your lap, talk to her low, or simply let her be and read on "
                "with her weight settled on you")
    return (f"be with {her} — sit with her, stroke her, talk to her, feed her, or play with her; she is here, "
            "and she is yours to tend")


def _maybe_call(thought: str, intention: str, his_location: str) -> str | None:
    """C3 (J-2468): is this thought a CALL to her (core/cat_call.wants_call — a call verb with a cat word, her
    name, or a bare 'her' inside A2's anaphora window)? Then the hand fires and its line is his perception.
    Steps aside for a naming utterance while she is unnamed. Fail-open to None (react carries on)."""
    global _prev_ref_txt
    try:
        from core import cat_call as _cc
        txt = f"{thought} {intention}".lower()
        name = str(state.get("name") or "")
        if not name and (_extract_name(thought) or _extract_name(intention)):
            return None                                   # "I will call her Ash": the R1 act, not a call
        try:   # B3 (J-2470, core/cat_tom): "I'll call the black cat Soot" names the OTHER cat — the tom's own latch
            from core import cat_tom as _ct               # (react's tom block below), never a call to her: wants_call
            if _ct.extract_name(thought) or _ct.extract_name(intention):   # reads "call" + "cat" and would eat it
                return None
        except Exception:
            pass
        name_l = name.lower()
        prev_named = any(w in _prev_ref_txt for w in _CAT_NOUNS) or (name_l and name_l in _prev_ref_txt)
        if not _cc.wants_call(txt, name, she_referred=bool(prev_named)):
            return None
        _prev_ref_txt = txt                               # the window moves on, as it would have below
        _note_referent("call", txt, place=his_location)   # B2 (J-2472): his hand reached for A cat
        line = _cc.call(state, his_location, thought, intention)
        if line:
            _save()
        return line
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat] call hand failed (non-fatal): %s", exc)
        return None


def call(his_position: str, what: str = "", thought: str = "", intention: str = "") -> str | None:
    """C3 (cat_overhaul, J-2468, D-0505 (c)): THE CALL, his own hand — cat.call(his_position, what). `his_position`
    is the Living-World place he calls from (the sensorium's location: study / garden / wood / shore; the
    standpoint is read from locomotion); `what` is what he called ("puss-puss", "the kissing noise", her
    name) when the caller knows it, else it is read from his own words (`thought` / `intention`). Returns
    the line he perceives — what he did and what he heard right then — or None. The carry to her, her
    hearing gate, her decision, the sound-first answer, her legs and the name as a learned sound all live in
    core/cat_call; everything she does about it reaches him only as sound and presence, never as a readout."""
    _load()
    if state.get("phase") == "absent":
        return None
    try:
        from core import cat_call as _cc
        line = _cc.call(state, his_position, thought or what, intention)
        if line:
            _save()
        return line
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat] call failed (non-fatal): %s", exc)
        return None


def react(thought: str, intention: str = "", his_location: str = "") -> str | None:
    """His own hand toward the cat: if his thought reaches for it (tend it, or NAME it now that it is his),
    actuate that — update the bond/phase, let the cat respond, return a perception line. Else None. The trigger
    is always his; we only connect the want. Also captures the NAME he chooses (the emergent naming).

    LOCATION-GATED (2026-08-28, the location-leak fix): every sibling read (presence_line, look_line,
    affordance_line, is_here) already checks she is actually where he is before counting her as reachable
    — this, the one function that ACTUATES the relationship (bond, feeding, naming, all persisted), never
    did. Verified live: with the cat on_the_desk and Du in the garden, react() fired anyway and wrote a
    real last_tended timestamp to cat_state.json. Fail-CLOSED here (unlike this file's LLM/data calls,
    which fail open) — a missing/empty his_location means no interaction, not an unchecked one; a thought
    about her from elsewhere is just a thought, never a touch."""
    _load()
    if state.get("phase") == "absent":
        return None
    if state.get("phase") == "dead":
        # D-2 (J-2471, D-0506): his hands on a dead cat — the burial (her body found, him where it lies or in the
        # garden), a hand laid on her where she lies; a call to her goes out and nothing comes back (cat_call's
        # own silence). Nothing else: there is no cat to tend. Fail-closed on his location like everything here.
        if not his_location:
            return None
        try:
            from core import cat_harm as _ch
            _hl = _ch.hand(state, thought, intention, his_location)
            if _hl:
                _save()
                return _hl
        except profile.NonLiveWriteError:
            raise
        except Exception as exc:
            logger.debug("[cat] dead hand failed (non-fatal): %s", exc)
        return _maybe_call(thought, intention, his_location)
    # HIS CALL (C3, J-2468, cat_overhaul; D-0505 (c)): calling her is its own hand, and the one hand that must
    # NOT wait on her being here — the point of a call is that she is not. Still fail-CLOSED on his location
    # (cat_call refuses an empty one). A naming utterance while she is unnamed ("I will call her Ash") is the
    # R1 act, not a call: _maybe_call steps aside and the latch below keeps it, location-gated as it always was.
    _call_line = _maybe_call(thought, intention, his_location)
    if _call_line:
        return _call_line
    # THE TOM (B3, J-2470, core/cat_tom, D-0507 (c)): two hands aimed at the OTHER cat, read before the here-gate
    # because she need not be here for either — driving him off (a drive-off verb + an other-cat word; fail-closed
    # on his location like everything else; the tom goes and comes back another night, never deterred for good),
    # and naming HIM ("I'll call the black cat Soot": the name sticks to the tom's own individual record, only once
    # Du has met him close — life_traces.give_name refuses before that). Neither touches her state or her name.
    try:
        from core import cat_tom as _ct
        _tom_line = _ct.drive_off(thought, intention, his_location)
        if _tom_line:
            return _tom_line
        if _ct.aims_at_tom(f"{thought} {intention}"):
            _tom_name = _ct.maybe_name(thought, intention)
            if _tom_name:
                _note_referent("naming", f"{thought} {intention}", place=his_location, which="tom")
                return _tom_name
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[cat] tom hand failed (non-fatal): %s", exc)
    if not is_here(his_location):
        return None
    global _prev_ref_txt
    txt = f"{thought} {intention}".lower()
    her = _her()
    name_l = (state.get("name") or "").lower()
    has_noun_or_name = any(w in txt for w in _CAT_NOUNS) or (name_l and name_l in txt)
    # A2 (2026-09-07, J-0631/F-0880): a bare "she"/"her" only refers when the thought immediately
    # before this one already named her — checked against _prev_ref_txt BEFORE we overwrite it with
    # this call's own txt, just below.
    prev_had_noun_or_name = any(w in _prev_ref_txt for w in _CAT_NOUNS) or (name_l and name_l in _prev_ref_txt)
    has_pronoun = any(w in txt for w in ("she", "her"))
    refers = has_noun_or_name or (has_pronoun and prev_had_noun_or_name)
    # F-1028/J-0716 (2026-09-07): the NAMING occasion below must NOT reuse this narrowed `refers` —
    # an isolated naming utterance with no cat noun anywhere in it or the immediately preceding
    # thought (all pronoun, e.g. "She has been mine for weeks now. I will call her Ash.") would
    # otherwise never even reach _extract_name(). `naming_refers` is the pre-A2, unnarrowed test
    # (any cat noun, her name, OR a bare she/her, no anaphora window) — naming's own false-positive
    # risk stays low regardless, since _extract_name() below still requires an exact grammar match
    # and can only ever fire once per cat (`not state.get("name")`), so broadening only THIS
    # referrer does not reopen A2's vending-machine problem. Measured before shipping this (F-1049):
    # zero real historical near-misses — in fact zero naming-grammar-about-her hits at all, near-miss
    # or not — anywhere in the complete inner_thought record (2026-06-03..09-07, 25,180 thoughts,
    # i.e. her entire kept life, not just "since 08-19" as F-0879 sampled); fixed anyway because a
    # real attempt is now a one-shot, freshly-prioritized event under the same day's D-0160 ruling,
    # the fix is unconditionally cheap, and a silent miss on the ONE naming attempt Du ever makes
    # would be far more costly than this broadening's near-zero downside.
    naming_refers = has_noun_or_name or has_pronoun
    # F-1050/J-0716: capture the PRIOR call's text for the other-cat guard below BEFORE _prev_ref_txt
    # is overwritten with this call's own txt on the next line — the exact bug the A2 comment above
    # already warned about for `prev_had_noun_or_name`, re-found here for `_other_aimed` (a first
    # draft of this fix computed _other_aimed AFTER the overwrite and so always compared this call's
    # txt against itself; caught by this job's own verification harness before commit).
    _prior_txt = _prev_ref_txt
    _prev_ref_txt = txt
    if not naming_refers:
        return None
    _note_referent("react", txt, place=his_location)   # B2 (J-2472): his hand reached for A cat — which one, if he said

    # The NAMING occasion — it is his and warm but unnamed, and his thought offers a name.
    # DISTANT-CAT GUARD (2026-07-04-adjacent): a name aimed at the OTHER cat ("I'll call the black cat
    # Smoke") must not stick to HER — the naming is his companion's alone. J-0716 (2026-09-07):
    # extended to also check the PRIOR thought (_prior_txt) — otherwise an antecedent like "The black
    # cat perches on the wall." followed by a bare-pronoun "I will call her Smoke." carries the OTHER
    # cat's antecedent through the very same anaphora window `refers` above reads, while this guard
    # only ever saw the second call's own text and missed it entirely, misnaming HER instead. Found
    # and fixed (F-1050) while building this job's own F-1028/F-1049 fix (not itself what J-0716 was
    # asked to fix, but the same 3 lines, a one-line addition, and cheap to verify alongside it —
    # folded in here rather than spawned, per findings-log). The prior-text check is gated on
    # `not has_noun_or_name` deliberately: it should only ever override an AMBIGUOUS bare-pronoun
    # naming attempt (the one anaphora can misattribute); an explicit "I will name my cat Ash" must
    # never be blocked just because the black cat was mentioned two thoughts ago — caught by this
    # job's own verification harness (a first draft without this gate wrongly blocked exactly that
    # regression case before commit).
    _OTHER_CAT_WORDS = ("black cat", "other cat", "distant cat", "far cat", "that cat on")
    _other_aimed = (any(w in txt for w in _OTHER_CAT_WORDS)
                    or (not has_noun_or_name and any(w in _prior_txt for w in _OTHER_CAT_WORDS)))
    if naming_refers and state.get("phase") == "kept" and not state.get("name") and not _other_aimed:
        nm = _extract_name(thought) or _extract_name(intention)
        if nm:
            state["name"] = nm
            state["phase"] = "companion"
            state["bond"] = max(state.get("bond", 0), NAME_BOND)
            _save()
            _note_referent("naming", f"named her {nm}", place=his_location, which="grey")   # B2 (J-2472): the act that distinguishes her for good
            # W2.0 (2026-07-03, docs/plans/capacity_to_commit.md ★★ WAVE 2): the naming is the flagship
            # R1 enactment and previously left NO durable record — no fragment, no activity, no timestamp —
            # so no judge could ever see the single most load-bearing deed in his world. It now writes an
            # activity general-event + an origin='action' fragment, and registers the R1 trial (the
            # exposure instrument: prediction elicited next idle cycle, outcome probed at +7 days).
            # All fail-open — the naming itself never depends on the bookkeeping.
            try:
                from core import activity_memory
                activity_memory.record("named", nm)
            except Exception:
                pass
            try:
                from core.memory.store import store_fragment
                from core import mood as _mood
                store_fragment(content=f"(a deed, on the record) I gave her a name today: {nm}. "
                                       f"I chose it, and it is hers.",
                               layer="episodic", relevance=0.9, importance=0.9,
                               keywords=["cat", nm, "named", "deed"], origin="action",
                               valence=_mood.current_valence(), felt=_mood.current_felt())
            except Exception:
                pass
            try:
                from core import commitment_trials
                commitment_trials.register_acceptance("R1_name_the_cat", f"Her name is {nm}.",
                                                      {"name": nm})
            except Exception:
                pass
            return f"You have given her a name: {nm}. She is yours now, and she has a name."

    # F-1028/J-0716: naming above could fire on `naming_refers` alone (broader than `refers`); every
    # behavior below this line (the live mouse, tending) is unchanged from A2 and must keep requiring
    # the NARROWED `refers` — restore that gate now that the naming occasion has had its own, wider
    # shot at `thought`/`intention` above.
    if not refers:
        return None

    # the LIVE MOUSE (10x, 2026-07-03): she has released chaos indoors — his hand can resolve it,
    # with mouse-verbs rather than tend-verbs (you don't stroke a crisis). Sits BEFORE the tend gate.
    if (state.get("arc") or {}).get("kind") == "live_mouse" and \
            any(w in txt for w in ("mouse", "catch", "corner", "deal", "chase", "carry", "shoo", "free", "cup")):
        state["arc"] = {}
        state["activity"], state["mood"] = "washing", "content"
        _save()
        try:
            from core import activity_memory
            activity_memory.record("caught_the_mouse", "under a cup")
        except Exception:
            pass
        return ("You corner the mouse at last under a cup by the bookshelf, carry it out, and tip it into the "
                f"long grass. {her} watches the whole operation from the desk, deeply unimpressed with you both.")

    # Tending. "hold"/"holding"/"approach" are too ambiguous to trust alone (any thought about holding
    # or approaching ANYTHING used to count once refers was true via a bare pronoun) — they only count
    # when this same thought also names her outright (a noun or her name, not anaphora).
    _tend_hit = any(re.search(v, txt) for v in _TEND_VERBS)
    if not _tend_hit and has_noun_or_name:
        _tend_hit = any(re.search(v, txt) for v in _TEND_VERBS_NOUN_GATED)
    if not _tend_hit:
        return None
    now = time.time()
    state["last_tended"] = now    # any care — feeding OR affection (stroke/sit/talk) — holds the bond (2026-06-25)
    # REAL FOOD (2026-09-07, D-0163/D-4, J-0719): this used to be a bare text-match that always
    # "succeeded" — no food was ever spent, the exact conjured-meal leak A3's audit named. A feed
    # attempt now really tries the larder (_feed_source(), which both checks AND spends in one call);
    # `fed` only ever becomes True once something real is actually gone from the house. His care is
    # still stamped above either way (he showed up and tried), but the feeding-specific rewards below
    # (last_fed, the saucer, the bond bump for feeding, the phase transition on a first feed) only
    # follow real success — and when the house genuinely has nothing, this is a feed attempt, not a
    # stroke, so it fails honestly, in his own hand, rather than quietly degrading into one.
    fed_wanted = any(w in txt for w in ("feed", "fed", "saucer", "milk", "tempt", "scraps"))
    fed = False
    food_source = ""
    # D-2 (J-2471, D-0506): ILL, she is off her food. The feed is still real (the tin is spent, the saucer filled:
    # a real cost, as ever) but eat() is not called — hunger stays high, and the saucer stays full by her
    # (_maybe_empty_saucer waits on her), which is how he finds out. A stroke she suffers and gives nothing back.
    try:
        from core import cat_harm as _ch
        _ill_now = _ch.is_ill(state)
    except Exception:
        _ill_now = False
    if _ill_now and state.get("phase") in ("kept", "companion"):
        if fed_wanted:
            food_source = _feed_source(prefer_milk=("milk" in txt))
            if food_source:
                sc = state.setdefault("saucer", {"has_food": False, "kind": "", "set_ts": 0.0})
                sc["has_food"], sc["kind"], sc["set_ts"] = True, food_source, now
                state["last_fed_source"] = food_source
                _save()
                return _ch._pool("HARM", "feed_refused")
            _save()
            return random.choice([
                f"You reach for something to tempt {her} with and the cupboard has nothing; she would not have taken it anyway, by the look of her.",
                f"There is nothing in the house to put down for {her}, and she lies with her back to the empty saucer as if that were the point.",
            ])
        _save()
        return _ch._pool("HARM", "tend_ill")
    if fed_wanted:
        # D-0508/D-4 (J-2466): his own words name milk -> the jug is tried first; otherwise the tin, as ever.
        food_source = _feed_source(prefer_milk=("milk" in txt))
        if food_source:
            fed = True
            sc = state.setdefault("saucer", {"has_food": False, "kind": "", "set_ts": 0.0})
            sc["has_food"], sc["kind"], sc["set_ts"] = True, food_source, now
            state["last_fed_source"] = food_source
            eat(food_source, now)   # B1 (J-2465): the meal lands on her hunger budget (the kind really spent)
            try:   # C3 (J-2468, D-0505 (c)): fed soon after a call by her NAME — the name is learned a little more
                from core import cat_call as _cc
                _cc.note_fed(state, now)
            except profile.NonLiveWriteError:
                raise
            except Exception:
                pass
            try:   # THE LIVING WORLD (J-0513): a deed draws its takers (life.note_deed)
                from core import life as _life; _life.note_deed("saucer", "garden")
            except Exception:
                pass
        else:
            _save()
            return random.choice([
                "You go for the saucer, but there is nothing in the house to put in it — no fish, no "
                "milk, nothing set by for her. You'll have to write to the carrier, or find her "
                "something.",
                f"You reach for something to feed {her} and come up empty-handed; the cupboard has no "
                "cat food left, and there are no scraps to spare either.",
                f"There is nothing to feed {her} with. You check the cupboard and the larder both; "
                "empty, empty. She will have to go hungry a while yet, or hunt.",
            ])
    played = any(w in txt for w in ("play", "string", "twig", "feather", "toy", "chase", "dangle",
                                    "trail", "wand"))
    ph = state.get("phase")
    if ph == "appearing":
        state["bond"] = min(1.0, state.get("bond", 0) + (0.12 if fed else 0.06))
        if fed:
            state["last_fed"] = now
        took_in = state["bond"] >= KEEP_BOND
        if took_in:
            state["phase"], state["mood"] = "kept", "wary-but-staying"
            _save()
            return ("You set down food and wait, not reaching. This time she eats while you are still there, and "
                    "afterwards she does not leave — she has decided to stay. She is yours, if you'll have her.")
        _save()
        if fed:
            return "You set down a saucer and step back. She waits until you turn away, then eats fast, watching you the whole time."
        return "You crouch and hold still. She watches, every muscle ready to bolt — then, after a long moment, she doesn't run."

    # kept / companion — affection. 10x (2026-07-03): HER response depends on HER mood, not his —
    # tending an aloof hunter gets you nothing; a frightened cat wants proximity, not handling.

    # SLEEPING CAT REFUSAL (A2, 2026-09-07, J-0631/F-0880): tend ignored `activity == sleeping`
    # outright — she could be handled mid-nap with no acknowledgment she had even been asleep. A
    # plain no-op unless he says so himself; no bond change either way (a refusal, not a rebuff —
    # that's the handling budget just below, and it costs her something).
    if state.get("activity") == "sleeping" and not any(w in txt for w in _WAKE_WORDS):
        return random.choice([
            f"{her} is fast asleep; you let her be.",
            f"{her} is deep asleep and does not stir; whatever you meant for her waits.",
            f"{her} sleeps on, oblivious; you leave her to it.",
        ])

    # PER-HOUR HANDLING BUDGET (A2, 2026-09-07, J-0631/F-0880): bond capped at 1.0 made every stroke a
    # no-op on the number, but nothing ever refused the stroke itself — "she cannot be over-handled"
    # was the finding's own line. A fifth real tend inside a trailing real hour and she has had enough:
    # she leaves outright (a mood flip alone would leave her standing right there, still tenable next
    # cycle) and bond can fall — the first time tending itself ever costs her anything. Scoped to
    # kept/companion only: the wary "appearing" stray above already returned before reaching here.
    _handled = [t for t in state.get("_handled_ts", []) if now - t < 3600]
    if len(_handled) >= 4:   # 4 already on record this hour + this one = the 5th handling
        state["_handled_ts"] = _handled
        state["location"], state["activity"], state["mood"] = "away_hunting", "had_enough", "aloof"
        state["bond"] = max(0.0, state.get("bond", 0) - 0.02)
        _save()
        return random.choice([
            f"{her} has had enough of your hands for one stretch — one flat look, a flick of the "
            f"tail, and she is gone before you can reach for her again.",
            f"{her} slides out from under your hand and is away, tail lashing; she will not be "
            f"handled again for a while yet.",
            f"{her} has plainly had her fill of you for now; she pulls free and stalks off to be "
            f"somewhere your hands are not.",
        ])
    _handled.append(now)
    state["_handled_ts"] = _handled

    state["bond"] = min(1.0, state.get("bond", 0) + (0.05 if fed else 0.03))
    if fed:
        state["last_fed"] = now
    if state.get("phase") == "kept" and state["bond"] >= NAME_BOND and not state.get("name_invited"):
        state["name_invited"] = True
        _save()
        return ("She leans into your hand, the engine of her starting up, and stays. She is wholly yours now — "
                "and she has no name. What will you call her?")
    if state.get("location") == "brought_a_mouse" or state.get("activity") == "brought_a_mouse":
        state["activity"] = "purring"
    mood = state.get("mood", "content")
    tend_key = {"content": "content", "affectionate": "content", "proud": "content",
                "aloof": "aloof", "aloof-but-near": "aloof", "offhand": "aloof", "wary": "aloof",
                "insistent": "insistent", "playful": "playful", "possessed": "playful",
                "afraid": "afraid"}.get(mood, "content")
    if tend_key in ("content", "insistent", "playful"):
        state["mood"] = "affectionate"       # his hand lands; she warms
    # PLAY (2026-07-07): a distinct, joyful interaction — not generic affection. HER mood decides whether she
    # deigns to chase: an aloof hunter or a storm-frightened cat will not, and the line says so (she is not a
    # toy that always works — the same not-a-vending-machine principle as tending). A willing play is a
    # relationship first, recorded to autobiography.
    if played and not fed:
        if tend_key == "afraid":
            _save()
            return (f"You try to get {her} to play, but she is too strung-out by the storm for it; she only "
                    f"wants to be near you, pressed close — not chased.")
        if tend_key == "aloof":
            _save()
            return (f"You trail a string for {her}; she watches it, and you, with lofty disdain, and will not "
                    f"stoop to chase it today. Some other time, her look says — on her terms.")
        state["mood"] = "playful"
        _save()
        fp = _first("first_play", "first_play")
        return fp or random.choice([
            f"You trail a bit of string and {her} comes apart — pupils gone huge, haunches wagging, then the "
            f"pounce, all four feet at once, skidding on the boards. You play until she flops down, panting, pleased.",
            f"You dangle a driftwood twig and {her} stalks it in dead earnest, tail-tip twitching, then ambushes "
            f"it in a clatter and trots off having thoroughly won.",
            f"You play with {her} till you are both done — she rolls on her side, lets you rub her belly exactly "
            f"once, then seizes your hand with all four paws to tell you the once is over.",
        ])
    _save()
    if fed:
        # D-0508/D-4 (J-2466): a saucer of milk and a twist of scraps are different feeds from a tin, and
        # the line says which was really spent (rotating pools; the tin / the fish keep their old line).
        if food_source == "milk":
            return _pick_fresh("TEND:feed_milk", list(_FEED_MILK_LINES)).replace("{her}", her)
        if food_source == "scraps":
            return _pick_fresh("TEND:feed_scraps", list(_FEED_SCRAPS_LINES)).replace("{her}", her)
        return _pool("TEND", "insistent") if mood == "insistent" else \
               f"You feed {her}; she eats, then winds against your legs, satisfied."
    line = _pool("TEND", tend_key)
    if line:
        return line
    return random.choice([
        f"You sit a while with {her}; she pushes her head into your hand and the engine of her starts up.",
        f"You stroke {her} and she kneads slowly at your knee, eyes half-shut, purring.",
        f"You talk to {her}, low and easy; she blinks at you, slow and trusting, and settles closer.",
    ])


_NAME_STOP = {"her", "him", "it", "the", "she", "you", "me", "us", "that", "this", "a", "an", "my",
              "cat", "kitten", "stray", "name", "names", "now", "then", "here", "there", "again",
              "over", "back", "out", "in", "up", "down", "home", "mine", "yours", "hers", "one"}

_WHO = r"(?:her|him|it|you|the cat|the kitten|the stray|my cat|my kitten|my companion|my little companion|this cat)"


def _extract_name(text: str) -> str:
    """Pull the name he chose out of his own phrasing. FIXED 2026-07-03 (found live): the old patterns
    missed 'I will name my cat Mist' — the EXACT stand he took on Jun30 ('my cat' absent from the
    alternatives) — and 'Her name is Mist' (sentence-initial capital vs a case-sensitive 'her'). His one
    real naming attempt hit the latch and fell through. Grammar now matches case-insensitively; the NAME
    itself must still be capitalized AS WRITTEN (names are; 'call her over' stays rejected) and not a
    stopword."""
    if not text:
        return ""
    pats = (
        rf"\b(?:call|name)\s+{_WHO}\s+([A-Za-z][\w'-]+)",
        rf"\b(?:her|his|its)\s+name\s+(?:is|shall be|will be|can be|should be)\s+([A-Za-z][\w'-]+)",
        rf"\bI(?:'ll| will| shall| am going to)?\s*(?:call|name|dub)\s+{_WHO}\s+([A-Za-z][\w'-]+)",
        r"\b([A-Za-z][\w'-]+)\s*[.!—-]*\s*that\s+(?:is|will be|shall be)\s+(?:her|his|its|the)\s+name",
    )
    for pat in pats:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            nm = m.group(1).strip(" .,'\"")
            # the name must be capitalized as HE wrote it, and not grammar debris
            if nm and nm[0].isupper() and nm.lower() not in _NAME_STOP:
                return nm
    return ""


def status() -> dict:
    # A7.4 (2026-09-07, J-0632/F-0886): 'seen_count' dropped from this dict. It is only ever
    # incremented in presence_line() while phase=="appearing" (line ~571) -- once she is taken in
    # (phase kept/companion, 73 days now) it is frozen forever at whatever it reached during those
    # first few sightings; live data/cat_state.json confirms 0 exactly. Nothing reads it FROM here:
    # grepped every status()/cat.status() call site in the repo (orchestrator.py:522, fieldcraft.py,
    # commitment_trials.py, sensorium.py x3) -- each reads only phase/name/bond/location/activity,
    # none touches seen_count, and the HUD's own static JS/HTML never mention it either. The one
    # LIVE sighting counter in this file is distant['seen_count'] (the black cat, read directly by
    # core/object_graph.py and scripts/lane2_lab.py already) -- a different creature, so it does not
    # belong under HER status() as if it were a count of her. The dead state field + its
    # appearing-phase increment are left as internal bookkeeping (harmless, no reader anywhere);
    # only the misleading exposure through status() is retired here.
    _load()
    return {"phase": state.get("phase"), "name": state.get("name") or None,
            "bond": round(float(state.get("bond", 0)), 2), "location": state.get("location"),
            "activity": state.get("activity")}
