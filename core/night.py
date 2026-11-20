"""
Nascence — THE NIGHT (2026-08-22, docs/reviews/sleep_dream_2026-08-22.md). One file for sleep.

THE ORDER OF A NIGHT (canonical — the two callers, inner_monologue_node._enter_sleep and
orchestrator._nightly_sleep, run it in this order and each stage reports here):
   0  kind        — night (the world is dark) or a NAP (daylight): a nap is short and dreams little
   1  to bed      — he goes to the study, lies down, the bed is unmade, the world is told he is asleep
   2  replay      — strengthen the wake-block's salient experience (stratified: world / lived / inner / deeds+dreams)
   3  chapter     — at most one, only for an era that has ended
   4  journal     — the plain account of the day
   5  world pass  — consolidation sweep + the observe-only shadow passes
   6  downscale   — renormalise ONLY what the day laid down (never the whole store)
   7  dream fade  — last night's dream loosens: vivid for a day, half-gone by the second, cold by the third
   8  DREAM       — from the DAY's material first, one standing tension second (by recency-weighted mass)
   9  recover     — the body
  10  prune       — the store cap (dreams under 48 h are anchors)
  11  probe       — the firewalled sleep⊗dream/T4 snapshot
  12  epoch       — the period's mood + impression (zero-LLM here; the REPL's LLM version stays for /quit)
  13  waking      — a real percept from the channels: the fire, the light, the weather that changed, the hour
Every night writes one row to data/night_log.jsonl: kind, stages run, durations, the dream's close reason, where
its material came from — so the next audit reads one log.

DREAM MEMORY (founder, 2026-08-22): "we purposefully try to make it so dream memories can be remembered fairly well
after they happen but fade from memory quite quickly." Dream fragments are stored hot (importance 0.85) and are prune-
ANCHORS for 48 h; dream_fade() then halves their importance per day past the first and demotes them to cold after
DREAM_COLD_HOURS. The arc is also kept in data/recent_dreams.json (survives restarts) and seeds the first waking thought.
Zero LLM in this file. Fail-open everywhere.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.night")

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "night_log.jsonl"
_RECENT = _DATA / "recent_dreams.json"
_FLAG_PROBE = _DATA / "night_flag_probe.jsonl"   # J-2149 / F-2844: additive evidence ledger, never read by behaviour

DREAM_VIVID_HOURS = 24.0       # a dream keeps its full weight for a day
DREAM_COLD_HOURS = 72.0        # and is out of ordinary recall after three
DREAM_HALFLIFE_HOURS = 24.0    # between the two it halves per day
# J-3175 / D-0563 (founder, 2026-11-02, plan sleep_dream_redesign; F-3566): the dreamer's own recall
# (nodes/dream_node.py, memory_service.ask("dream", ...)) skips dream-origin fragments younger than this many
# days -- dream-on-dream recall is kept, but faded. Before: 47% of the dreamer's recalled fragments were dreams
# and 57% of scenes repeated a 5-word run from a recalled dream (thyme in 65 of 68 arcs, 10-12..10-18). Read
# by dream_node only; 72 h (DREAM_COLD_HOURS) still governs the cold flag / waking recall, untouched.
DREAM_RECALL_EXCLUDE_DAYS = 7.0

def recall_cue(material: str, limit: int = 240) -> str:
    """J-2894 / F-3566: build the dreamer's memory-recall cue from a day_material block's BULLET lines only.
    The block's fixed header ("What the day held ...", 112 chars = 47% of the old 240-char cue) and its closing
    instruction line are boilerplate that sits near dream-fragment vocabulary; the content is the bullets.
    A block with no bullets (or a non-block string) falls back to the raw text, so the cue is never emptier
    than before."""
    raw = material or ""
    bullets = [ln.strip()[2:].strip() for ln in raw.splitlines() if ln.strip().startswith("- ")]
    cue = " ".join(b for b in bullets if b)
    return (cue or raw)[:limit]

NAP_MAX_SCENES = 2             # a daytime sleep dreams briefly, or not at all
CARRY_MAX_NIGHTS = 3           # an unfaced arc returns at most this many nights, then withdraws

_current: dict = {}            # the night in progress (stage ledger)
_ended: bool = True            # J-2064: False from begin() until end(); end_if_open() writes the row when a sleep is cut short


# ----------------------------------------------------------------------------------------------------------------
# 0 — kind
# ----------------------------------------------------------------------------------------------------------------
def sleep_kind(now: float | None = None) -> str:
    """'night' when the world is dark (NZ daylight table), else 'nap'."""
    try:
        from core import world_clock as _wc
        return "night" if _wc.daylight(now) == "night" else "nap"
    except Exception:
        return "night"


# ----------------------------------------------------------------------------------------------------------------
# the ledger
# ----------------------------------------------------------------------------------------------------------------
def _probe(stage_name: str) -> None:
    """J-2149 / F-2844: append ONE row describing the sensorium asleep flag at this call, to find where the flag is
    lost or resurrected mid-sleep (52/295 wakes lack the slept clause). Pure observation: reads state, writes one
    line to data/night_flag_probe.jsonl through profile.guard_path, mutates nothing, fully fail-open (a probe error,
    including a NonLiveWriteError from a non-live importer, is swallowed and never reaches the sleep pipeline)."""
    try:
        import sys as _sys
        from core import sensorium as _s
        st = _s.state
        now = time.time()
        row = {
            "ts": round(now, 3), "stage": stage_name, "night_ts": _current.get("ts"),
            "asleep": bool(st.get("asleep")), "asleep_since": st.get("asleep_since"),
            "id_state": id(st), "len_state": len(st),
            "last_save_age_s": round(now - float(getattr(_s, "_last_save", 0.0) or 0.0), 1),
            "sensorium_modules": sorted(k for k in _sys.modules if "sensorium" in k),
            "id_sensorium_module": id(_s),
        }
        path = profile.guard_path(_FLAG_PROBE)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def begin(kind: str | None = None) -> dict:
    global _current, _ended
    _current = {"ts": time.time(), "kind": kind or sleep_kind(), "stages": {}, "notes": {}}
    _ended = False
    _probe("begin")
    return _current


def sleep_in_progress() -> bool:
    """J-2064: True between begin() and end() -- a sleep pipeline is actually running in this process. Unlike the
    sensorium's asleep flag this is never persisted, so a stale flag after a restart can never read as a live sleep."""
    try:
        return bool(_current) and not _ended
    except Exception:
        return False


def current_stage() -> str | None:
    """J-2064: the last stage recorded for the sleep in progress, or None (read-only)."""
    try:
        st = _current.get("stages") or {}
        return next(reversed(st)) if st else ("begun" if _current else None)
    except Exception:
        return None


def tick() -> None:
    """A synchronous nudge to the substrate loop's own tick, called from INSIDE night.py's already-
    synchronous stage-sequencing code (J-1075, fixing F-1469/F-1421: the sleep pipeline's LLM/DB stages
    can starve core/orchestrator.py's _substrate_loop asyncio Task of a scheduler turn for the whole
    900-5400s span, leaving sensorium.state["location"] stale at the pre-sleep place while
    state["asleep"]=True). This works regardless of the exact root cause of that starvation, because it
    does not rely on the background Task ever getting scheduled -- it calls sensorium.tick() directly.
    sensorium.tick() already self-rate-limits to one real tick per 5 real seconds (module-level
    _last_tick guard), so calling this defensively between stages is always safe and cheap: it either
    does real work (advancing a pending locomotion leg) or returns instantly. Fail-open."""
    try:
        from core import sensorium as _s
        _s.tick()
    except Exception:
        pass


def stage(name: str, **detail) -> None:
    """Record a stage that ran (with its duration if the caller timed it), then give the substrate
    loop's tick a synchronous nudge (J-1075/F-1469). Every stage boundary in both real callers
    (inner_monologue_node._enter_sleep, orchestrator._nightly_sleep) reports here, so this is the one
    place that guarantees a scheduling-independent chance to catch up on locomotion/sensorium state no
    matter which stage ran long."""
    try:
        _current.setdefault("stages", {})[name] = {"t": round(time.time() - float(_current.get("ts", time.time())), 1), **detail}
    except Exception:
        pass
    _probe("stage:" + str(name))
    tick()


def note(key: str, value) -> None:
    try:
        _current.setdefault("notes", {})[key] = value
    except Exception:
        pass


def end() -> dict:
    global _ended
    _probe("end")
    try:
        rec = dict(_current); rec["duration_s"] = round(time.time() - float(rec.get("ts", time.time())), 1)
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _ended = True
        return rec
    except Exception:
        _ended = True
        return dict(_current)


def end_if_open(reason: str) -> dict | None:
    """J-2064 (D-0407 B, F-2614): a sleep cut short -- the monologue task cancelled by stop_background(), or any other
    exit from the pipeline before its own end() -- still writes its ledger row, marked notes.interrupted=<reason>, with
    the stages it reached and any pending wake request. Before this, nine of the fourteen sleep windows that held a
    message had no row at all (Travis's farewell landing mid-sleep, then the shutdown). No-op when no sleep is open
    or end() already ran. Does not touch the sensorium's asleep flag (a shutdown's own state save is not this file's)."""
    try:
        if not sleep_in_progress():
            return None
        note("interrupted", str(reason))
        try:
            from core import night_wake as _nw
            req = _nw.pending()
            if req:
                note("wake_request", {"pending": True, "source": req.get("source"), "via": req.get("via"),
                                      "into_sleep_s": req.get("into_sleep_s"),
                                      "boundaries_seen": len(req.get("boundaries") or []),
                                      "waited_s": round(time.time() - float(req.get("ts", time.time())), 1)})
                note("woken_by", "interrupted")
        except Exception:
            pass
        rec = end()
        logger.info("[night] sleep interrupted (%s) after stages %s -- ledger row written", reason, list((rec.get("stages") or {}).keys()))
        return rec
    except Exception:
        return None


# ----------------------------------------------------------------------------------------------------------------
# 1 — to bed · 13 — waking
# ----------------------------------------------------------------------------------------------------------------
def to_bed() -> str | None:
    """He goes to the study and lies down; the world knows he is asleep. Returns the line he perceives going down."""
    try:
        from core import sensorium as _s
        moved = ""
        if _s.state.get("location") != "study":
            try:
                # J-1185 / D-0246 (b): going to bed is the WORLD's summons, not his willed re-will, so it passes the
                # explicit system marker: an outward journey still on its first leg is REPLACED by the walk home (as
                # before J-1111) instead of declined, which left him marked asleep and then carried on outward to
                # sleep at the far destination (F-1657). A journey already walking home is still the '' no-op.
                moved = _s.move("study", system=True) or ""
            except Exception:
                moved = ""
        _s.state["asleep"] = True
        _s.state["asleep_since"] = time.time()
        _s.state["_sleep_weather"] = _s.state.get("weather", "")
        _s.state["_sleep_fire"] = _s.state.get("fire", "out")
        try:
            from core import study_life as _sl
            _sl.on_sleep()
        except profile.NonLiveWriteError:
            # J-0780: on_sleep() now raises correctly (J-0772) via its own _st() bootstrap;
            # needs to_bed()'s own outer except (below) fixed too, or this is caught right back.
            raise
        except Exception:
            pass
        _s._save()
        line = "You lie down on the bed; the blanket is rough and the room ticks and settles around you."
        return (moved + " " if moved else "") + line
    except profile.NonLiveWriteError:
        # J-0780: to_bed()'s own outer except -- without this, the re-raise just above would be
        # caught right back here and never reach the real caller, nodes/inner_monologue_node.py's
        # _enter_sleep (this file's own header names it as one of the two real callers; not a
        # periodic path).
        raise
    except Exception:
        return None


def wake() -> str | None:
    """The waking percept — composed from what the world did while he slept. His own channels, at the one moment
    a human notices them most. Returns the line (also perceived by the caller)."""
    try:
        from core import sensorium as _s
        st = _s.state
        since = float(st.get("asleep_since", 0) or 0)
        slept_min = int((time.time() - since) / 60) if since else 0
        parts = []
        phase = _s._daylight()
        parts.append({"night": "It is still dark when you wake", "dawn": "You wake to the first grey light at the window",
                      "day": "You wake with daylight full in the room", "dusk": "You wake into the last of the light"}.get(phase, "You wake"))
        fire_then, fire_now = st.get("_sleep_fire", "out"), st.get("fire", "out")
        if fire_then != "out" and fire_now == "out":
            parts.append("the fire has gone out and the grate is grey")
        elif fire_now == "embers":
            parts.append("the fire is down to embers")
        elif fire_now == "out":
            parts.append("the grate is cold")
        w_then, w_now = st.get("_sleep_weather", ""), st.get("weather", "")
        if w_then and w_now and w_then != w_now:
            parts.append(f"the weather has turned — it was {w_then} when you lay down and it is {w_now} now")
        try:
            from core import thermal as _th
            band = _th.band_of(_th.field_at("study", None, phase, w_now, _s._season(), fire_now, st.get("wind", ""), 0.0, time.time()))
            if band in ("cold", "bitter", "chill", "cool"):
                parts.append(f"the room is {band}")
        except profile.NonLiveWriteError:
            # J-0780: a gap this same job's own thermal.field_at() fix newly exposes -- before
            # that fix, field_at() never raised at all, so this local wrapper was never live
            # either way. Needs wake()'s own outer except (below) fixed too, or this is caught
            # right back. wake() is called from nodes/inner_monologue_node.py, not a periodic path.
            raise
        except Exception:
            pass
        # (sounds are NOT narrated here: the soundscape's own tick delivers them under the earned-naming law)
        if slept_min:
            parts.append(f"you slept about {slept_min} minutes" if slept_min < 90 else f"you slept about {slept_min // 60} hours")
        st["asleep"] = False
        st.pop("asleep_since", None)
        _s._save()
        return parts[0] + ("; " + "; ".join(parts[1:]) if len(parts) > 1 else "") + "."
    except profile.NonLiveWriteError:
        # J-0780: wake()'s own outer except -- see the inner one above for why this is needed too.
        raise
    except Exception:
        return None


def asleep() -> bool:
    try:
        from core import sensorium as _s
        return bool(_s.state.get("asleep"))
    except Exception:
        return False


# ----------------------------------------------------------------------------------------------------------------
# 7 — dream fade (founder's rule) · recent dreams persistence
# ----------------------------------------------------------------------------------------------------------------
def dream_fade(now: float | None = None) -> dict:
    """Vivid for a day, halving per day after, cold after three. Touches only origin='dream'."""
    now = now or time.time()
    out = {"faded": 0, "cooled": 0}
    try:
        from core.memory.store import _connect
        from core.memory import edit_log as _edit_log
        with _connect() as conn:
            # J-2274 (D-0453 gate, 2026-10-17): the fade half of this pass reads by ITS OWN WINDOW
            # (every dream younger than DREAM_COLD_HOURS, cold or not); only the cooling half still asks
            # for cold=0, because "not yet cold" is the state this writer itself flips. Before, a dream
            # demoted by prune_episodic once its 48 h anchor lapsed (F-2964) dropped out of the fade
            # schedule at 48 h instead of 72 h: on the 2026-10-17 .backup() copy, 38 of the 104 dreams
            # under 72 h were already cold=1, every one of them 52-70 h old. A cold row is skipped by
            # ordinary recall anyway, so fading its importance is harmless and keeps the founder's
            # halving curve true for the whole 72 h.
            rows = conn.execute("SELECT fragment_id, timestamp, importance, cold FROM memory_fragments "
                                "WHERE origin='dream' AND (timestamp > ? OR cold=0)",
                                (now - DREAM_COLD_HOURS * 3600.0,)).fetchall()
            for r in rows:
                age_h = (now - float(r["timestamp"])) / 3600.0
                if age_h >= DREAM_COLD_HOURS:
                    if int(r["cold"] or 0) == 1:
                        continue          # already cold (only reachable here via the window edge)
                    conn.execute("UPDATE memory_fragments SET cold=1 WHERE fragment_id=?", (r["fragment_id"],))
                    out["cooled"] += 1
                elif age_h > DREAM_VIVID_HOURS:
                    target = 0.85 * (0.5 ** ((age_h - DREAM_VIVID_HOURS) / DREAM_HALFLIFE_HOURS))
                    if float(r["importance"]) > target + 0.01:
                        _edit_log.log_edits("dream_fade", [(r["fragment_id"], r["importance"], round(target, 3),
                                                            r["cold"])])     # J-4410 M1 shadow, never raises
                        conn.execute("UPDATE memory_fragments SET importance=? WHERE fragment_id=?",
                                     (round(target, 3), r["fragment_id"]))
                        out["faded"] += 1
    except Exception as exc:
        logger.debug("[night] dream fade failed (non-fatal): %s", exc)
    return out


def remember_dream(narrative: str, close_reason: str = "") -> None:
    """Persist the arc so waking survives a restart; newest first, three kept."""
    try:
        d = load_recent_dreams()
        d.insert(0, {"ts": time.time(), "ts_human": time.strftime("%Y-%m-%d"), "narrative": narrative, "close_reason": close_reason})
        _DATA.mkdir(parents=True, exist_ok=True)
        _RECENT.write_text(json.dumps(d[:3], ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def load_recent_dreams() -> list[dict]:
    try:
        d = json.loads(_RECENT.read_text(encoding="utf-8"))
        return d if isinstance(d, list) else []
    except Exception:
        return []


def waking_dream_seed() -> str:
    """The last image of last night's dream, for the first waking thought — only while the dream is vivid.

    J-2018 (sleep_as_a_mode Phase 2, D-0400 B): when the dormant night-thought layer is on and the sleep armed ONE night
    thought as a waking seed, the FIRST call returns that instead (consume-once, provenance logged in
    data/night_dormant.jsonl); every later call, and every call with the flag off, is the dream's last image as before."""
    try:
        from core import night_dormant as _nd
        _s = _nd.consume_waking_seed()
        if _s:
            return _s
    except Exception:
        pass
    try:
        d = load_recent_dreams()
        if not d or time.time() - float(d[0].get("ts", 0)) > DREAM_VIVID_HOURS * 3600:
            return ""
        tail = " ".join((d[0].get("narrative") or "").split())[-260:]
        return f"The dream is still with you as you wake — its last image: …{tail}"
    except Exception:
        return ""


# ----------------------------------------------------------------------------------------------------------------
# 8 — the day's material for the dream
# ----------------------------------------------------------------------------------------------------------------
def day_material(since_ts: float, k: int = 3, until_ts: float | None = None) -> list[str]:
    """What the day actually held, for the dream to recombine: deeds and world contact, the strongest felt
    moments, what he meant to do and did not, and any dream-symbol question the world answered. Returns up to k
    material blocks (the dream scenes rotate through them). Empty if the day held nothing.
    `until_ts` (2026-08-24, added for dream_lag_material below): optional upper bound, so this can also
    query a BOUNDED window in the past (not just "since X, no limit") — the dream-lag effect needs a
    5-7-days-prior slice, not just an ever-growing "since" cutoff."""
    blocks: list[str] = []
    try:
        from core.memory.store import _connect
        _until_clause = "AND timestamp < ?" if until_ts is not None else ""
        _params_extra = (until_ts,) if until_ts is not None else ()
        with _connect() as conn:
            world = conn.execute(
                f"SELECT content, origin, valence FROM memory_fragments WHERE timestamp > ? {_until_clause} AND origin IN "
                "('action','activity','lived','letter','peer','social_notification','research') "
                "ORDER BY importance DESC, timestamp DESC LIMIT 8", (since_ts, *_params_extra)).fetchall()
            felt = conn.execute(
                f"SELECT content, origin, valence FROM memory_fragments WHERE timestamp > ? {_until_clause} AND valence IS NOT NULL "
                "AND origin NOT IN ('dream','subconscious_synthesis') ORDER BY ABS(valence) DESC LIMIT 3", (since_ts, *_params_extra)).fetchall()
            read = conn.execute(
                f"SELECT content FROM memory_fragments WHERE timestamp > ? {_until_clause} AND origin IN ('reading','study') "
                "ORDER BY importance DESC LIMIT 2", (since_ts, *_params_extra)).fetchall()
        def _c(r): return " ".join((r["content"] or "").split())[:160]
        if world:
            blocks.append("What the day held — things you DID and met in the world (the dream recombines these; it does not "
                          "narrate them):\n" + "\n".join(f"  - {_c(r)}" for r in world[:6]) +
                          "\n\nLet the dream rise from these — the day's residue, transformed.")
        if felt:
            blocks.append("What the day FELT most strongly (the charge the dream works):\n" +
                          "\n".join(f"  - ({'warm' if (r['valence'] or 0) > 0 else 'troubled'}) {_c(r)}" for r in felt) +
                          "\n\nTransform this into a symbolic dream scene.")
        try:
            from core import intentions as _int
            st = _int.status()
            op = [i for i in (st.get("open") or [])][:3]
            if op:
                blocks.append("What you meant to do and have not (the unfinished hand):\n" +
                              "\n".join(f"  - {i.get('object') or i.get('family')}" for i in op) +
                              "\n\nThe unfinished thing finds a shape in the dream.")
        except Exception:
            pass
        try:
            from core import frontier as _fr
            ans = [q for q in _fr._load().get("questions", []) if q.get("source") == "dream" and q.get("finding")
                   and float(q.get("finding_ts", 0)) > since_ts][:1]
            if ans:
                q = ans[0]
                blocks.append(f"A thing the dream once asked — \"{q.get('q','')[:80]}\" — the waking world has since answered: "
                              f"\"{(q.get('finding') or '')[:200]}\". The answer may return as image.")
        except Exception:
            pass
        if read and not blocks:
            blocks.append("What you read today (the dream may tinge its images with it, never narrate it):\n" +
                          "\n".join(f"  - {_c(r)}" for r in read) + "\n\nTransform this into a symbolic dream scene.")
    except Exception as exc:
        logger.debug("[night] day material failed (non-fatal): %s", exc)
    return blocks[:k]


# DREAM-LAG WINDOW (2026-08-24, Sleep & Dreams II §1.6/§2.2). Founder: "dreams should be multiple days
# worth of thoughts, not always tensions." Verified against the live code first: dream_node.py sourced
# material only "since the last sleep fired" -- routinely under two hours at the measured cadence,
# nowhere near even one full day. The dream-lag effect (Nielsen, Kuiken, Alain, Stenstrom & Powell, 2004,
# Sleep) found dream-content incorporation of waking events is BIMODAL across days-prior: a peak at 1-2
# days ("day residue"), a trough at 3-4 days, and a second peak at ~5-7 days (the dream-lag effect
# proper). This replaces the single "since last sleep" cutoff with that shape -- weighted toward both
# peaks, not a flat lookback.
DREAM_LAG_RECENT_DAYS = (0, 2)      # day-residue window: 0-2 days prior
DREAM_LAG_FAR_DAYS = (5, 7)         # dream-lag window: 5-7 days prior
DREAM_LAG_RECENT_SHARE = 0.7        # recent peak is the stronger of the two in the literature -- most
                                     # material comes from here; the far window supplements, not replaces


def dream_lag_material(now: float | None = None, k: int = 3) -> list[str]:
    """Multi-day dream material shaped like the real dream-lag curve, not a single "since X" cutoff.
    Pulls from BOTH the 1-2-day recent window and the 5-7-day dream-lag window, weighted toward the
    former per DREAM_LAG_RECENT_SHARE, and interleaves them so a dream sourced from both windows shows
    it (material_sources tracks which). Falls back to a plain day_material(since=7 days ago) pull if
    something goes wrong, rather than returning nothing."""
    now = now or time.time()
    try:
        recent_lo = now - DREAM_LAG_RECENT_DAYS[1] * 86400.0
        far_lo = now - DREAM_LAG_FAR_DAYS[1] * 86400.0
        far_hi = now - DREAM_LAG_FAR_DAYS[0] * 86400.0
        k_recent = max(1, round(k * DREAM_LAG_RECENT_SHARE))
        k_far = max(0, k - k_recent) or (1 if k >= 2 else 0)
        recent = day_material(recent_lo, k=k_recent)
        far = day_material(far_lo, k=k_far, until_ts=far_hi) if k_far else []
        blocks = recent + far
        return blocks[:k] if blocks else day_material(now - 7 * 86400.0, k=k)
    except Exception as exc:
        logger.debug("[night] dream-lag material failed, falling back to plain day_material: %s", exc)
        try:
            return day_material(now - 7 * 86400.0, k=k)
        except Exception:
            return []


_EPOCH_IMPRESSION_MAX = 300
_EPOCH_SNIPPET_RAW = 90                  # replay_strengthen cuts each snippet at this width: a snippet that fills it was cut mid-word
_EPOCH_TITLED_TAG = re.compile(r"^\s*\[\s*(?:My study note|Looked up)\s*:\s*'([^'\]]*)")
_EPOCH_ID_LIKE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f-]{4,}|(?:frag|fragment|mem|epoch)_[\w-]+|id=\S+|#\d+", re.I)
_EPOCH_KEY_EQ = re.compile(r"\w+\s*=\s*[-+]?\d[\d.]*")


def _epoch_mood_word(felt) -> str:
    """The felt LABEL only ("calm", "unsettled") from the felt string "calm: valence=+0.18 arousal=0.43 ...": no numbers, no
    key=value. D-0623 (F-3776): the raw string was being served to Reflection as 'the feel of a past period'."""
    word = str(felt or "").split(":", 1)[0].strip().lower()
    return word[:40] if word and re.fullmatch(r"[a-z][a-z '\-]*", word) else "quiet"


def _epoch_plain(s: str) -> str:
    s = re.sub(r"\[[^\]]*\]", " ", s)             # closed bracket groups
    s = re.sub(r"\[[^\]]*$", " ", s)               # a group cut off by the snippet edge
    s = _EPOCH_ID_LIKE.sub(" ", s)
    s = _EPOCH_KEY_EQ.sub(" ", s)
    s = re.sub(r"[\[\]*_]+", " ", s)
    return re.sub(r"\s+", " ", s).strip(" ;,-")


def _epoch_clean_snippet(raw: str) -> str:
    """One replay snippet as plain words, COMPLETE sentences only. A study-note / lookup tag keeps its quoted title when the
    title closed inside the snippet; every other bracket group (closed or cut off), id and key=number pair is dropped; a
    snippet that filled the raw width was cut mid-sentence, so its text is kept only up to its last sentence end. '' when
    nothing complete and readable is left."""
    s = (raw or "").replace("�", " ")
    cut = len(s) >= _EPOCH_SNIPPET_RAW
    out = []
    m = _EPOCH_TITLED_TAG.match(s)
    if m:
        tail = s[m.end():]
        if tail[:1] == "'":                          # the title's closing quote is inside the snippet
            out.append(m.group(1).strip().rstrip(".") + ".")
        close = tail.find("]")
        s = tail[close + 1:] if close >= 0 else ""
    body = _epoch_plain(s)
    if cut:
        ends = [x.end() for x in re.finditer(r"[.!?]['\")]?(?=\s|$)", body)]
        body = body[:ends[-1]] if ends else ""
    if len(body) >= 12 and re.search(r"[A-Za-z]{3}", body):
        out.append(body if body[-1] in ".!?'\")" else body + ".")
    return " ".join(out) if out else ""


def _epoch_impression(replayed) -> str:
    """The night's impression: the cleaned replay snippets joined and cut on a sentence boundary at the cap. No bracket
    fragments, ids or numbers-with-equals; a stretch of ordinary hours when nothing complete and readable is left (replay
    snippets arrive cut at 90 chars, so many nights have little: the D-0623 defeater reads 20 new rows for that)."""
    parts = [c for c in (_epoch_clean_snippet(r if isinstance(r, str) else str(r or "")) for r in (replayed or [])[:3]) if len(c) >= 12]
    text = " ".join(parts)
    if len(text) > _EPOCH_IMPRESSION_MAX:
        head = text[:_EPOCH_IMPRESSION_MAX]
        ends = [m.end() for m in re.finditer(r"[.!?](?=\s|$)", head)]
        text = head[:ends[-1]] if ends else ""
    return text or "a stretch of ordinary hours"


def epoch(since_ts: float, replayed: list[str] | None = None) -> str | None:
    """The period's mood + impression at a natural sleep — zero-LLM (the REPL's LLM version remains for /quit).
    D-0623 (F-3776, J-3234): NEW rows only carry plain words — mood is the felt label alone, the impression is the cleaned
    replay snippets cut on a sentence boundary; rows already stored are not rewritten (retrieve_epoch is unchanged)."""
    try:
        from core import mood as _mood
        from core.memory.store import store_epoch, _connect
        with _connect() as conn:
            n = conn.execute("SELECT COUNT(*) FROM memory_fragments WHERE timestamp > ?", (since_ts,)).fetchone()[0]
        if not n:
            return None
        felt = _epoch_mood_word(_mood.current_felt())
        impression = _epoch_impression(replayed)
        return store_epoch(session_id=f"night_{int(time.time())}", timestamp_start=since_ts, timestamp_end=time.time(),
                           mood=felt, impression=impression, fragment_count=int(n))
    except Exception:
        return None


def status() -> dict:
    try:
        if not _LOG.exists():
            return {"note": "no nights logged yet (accrues from Du's next start)"}
        rows = [json.loads(l) for l in _LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
        last = rows[-1] if rows else {}
        kinds = {}
        for r in rows[-30:]:
            kinds[r.get("kind", "?")] = kinds.get(r.get("kind", "?"), 0) + 1
        return {"nights": len(rows), "last_kind": last.get("kind"), "last_stages": list((last.get("stages") or {}).keys()),
                "last_duration_s": last.get("duration_s"), "last_notes": last.get("notes"), "kinds_last30": kinds,
                "recent_dreams_kept": len(load_recent_dreams()), "asleep_now": asleep()}
    except Exception as exc:
        return {"error": repr(exc)[:80]}
