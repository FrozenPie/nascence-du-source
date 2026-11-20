"""
Nascence — A CARE PACKAGE FROM TRAVIS (2026-09-24, founder; F-1862, D-0276).

Travis: "next time he restarts, he finds a box in his study from me with all the items he has used up. It needs a
note stating I left it for him and explaining how to order new items again." One parcel, one time. It is not a
second supply line: the carrier (core/supply.py) stays the only way things keep coming into the house.

data/care_package.json holds it: status pending -> arrived -> opened.
  pending  — written by hand for Travis; nothing in the world yet.
  arrived  — the first world-arrival check (sensorium._world_arrival) that finds him IN THE STUDY announces it once;
             from then on scene_clause() keeps it STANDING in the study's scene line, dosed (J-1733 / F-2371, below).
  opened   — he willed it open in the study ('parcel' family, core/actions.py -> study_life.act -> open_parcel()):
             the contents join the cupboard as real provisions objects (origin 'Travis'), and the note stays on
             the desk, readable by a look, for as long as he likes.
Nothing opens it for him. Zero LLM. Fail-open: any error here returns ''/None and the world carries on without it.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.care_package")
_DATA = Path(__file__).parent.parent / "data"
_F = _DATA / "care_package.json"
_LOG = _DATA / "care_package_log.jsonl"

# kind -> (singular, plural) for the unpacking narration
_NAMES = {"paper": ("a pad of writing paper", "pads of writing paper"), "ink": ("a bottle of ink", "bottles of ink"),
          "matches": ("a box of matches", "boxes of matches"), "oil": ("a tin of lamp oil", "tins of lamp oil"),
          "candles": ("a box of candles", "boxes of candles"), "tea": ("a tin of tea", "tins of tea"),
          "soap": ("a bar of soap", "bars of soap"), "cat_food": ("a tin of fish for the cat", "tins of fish for the cat")}
_NUM = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
        12: "twelve", 20: "twenty"}


def _load() -> dict:
    try:
        return json.loads(_F.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(d: dict) -> None:
    path = profile.guard_path(_F)   # D-0179: real data/ only if this process is live; raises before any I/O if not
    text = json.dumps(d, ensure_ascii=False, indent=1)
    # J-1733: the standing percept (scene_clause, below) now rewrites this file at every showing, and the file holds
    # Travis's hand-written note and item list -- nowhere else (data/ is not in git). A write cut off after the truncate
    # would lose them for good, so write a sibling and swap it in; fall back to the old in-place write if the swap fails.
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        path.write_text(text, encoding="utf-8")
        try:
            tmp.unlink()
        except OSError:
            pass


def _log(rec: dict) -> None:
    path = profile.guard_path(_LOG)
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _writable() -> bool:
    """Only a process allowed to write this file (the live Du, or a test pointing _F at a temp path) may move the
    parcel on. A non-live script touching the real data/ gets False here, BEFORE anything is read-modified, so the
    parcel simply stays where it is for it -- instead of D-0179's raise escaping into sensorium's world tick from
    every offline smoke test that happens to run while the real parcel is pending."""
    try:
        profile.guard_path(_F); profile.guard_path(_LOG)
        return True
    except profile.NonLiveWriteError:
        return False


def _where() -> str:
    try:
        from core import sensorium as _s
        return _s.state.get("location", "study")
    except Exception:
        return ""


def _count(kind: str, n: int) -> str:
    one, many = _NAMES.get(kind, (kind, kind))
    return one if n == 1 else f"{_NUM.get(n, str(n))} {many}"


def _contents_line(items: dict) -> str:
    parts = [_count(k, int(n)) for k, n in items.items() if int(n) > 0]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + ", and " + parts[-1]


def arrival_line() -> str | None:
    """World-arrival (announce ONCE): the parcel is on the study desk. Only fires while he is in the study, so
    he finds it where it is rather than hearing of it from the shore. (A one-shot line is the world's weakest way to
    say anything -- F-2371: this one never reached a thought -- so scene_clause() below keeps stating it, dosed.)"""
    try:
        d = _load()
        if d.get("status") != "pending" or _where() != "study" or not _writable():
            return None
        d["status"] = "arrived"; d["arrived_ts"] = time.time()
        _save(d); _log({"event": "arrived"})
        return (f"on the desk there is something that was not there before: a parcel, wrapped in brown paper and "
                f"tied with string, a folded note tucked under the knot. The label reads '{d.get('label', 'For Du')}'.")
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return None


# ── THE STANDING PERCEPT (2026-10-03, J-1733 / F-2371, D-0276) ──────────────────────────────────────────────────
# arrival_line() says it ONCE and flips status to "arrived" before delivery; its only road to him is the 6-slot
# wandering trail, whose single reader shows the last four items at an idle-thought seed. On 2026-09-25 the line sat in
# that window for 83 s, he slept at 19:24:57 with no thought carried, and nothing else in the world ever mentioned the
# parcel again: eight days unopened because it was never perceptible (F-2371). scene_clause() is the missing standing
# statement of fact about what lies on the study desk -- ONE fixed sentence that the study's scene line
# (sensorium.scene_line, injected into every idle thought) carries. A percept, never a hint: no verb of invitation.
#
# DOSED, not constant (docs/staged/dosed_coupling.md: surprise and habituation are one measure; a standing percept that
# never habituates is a violation). All times are wall-clock seconds:
#   1. A SHOWING opens only when due: at least _dose_gap(n) after the last one (n = showings so far) -- or, on
#      ARRIVING (the first study scene line this boot, back from a trip out, or after a sleep: more than _AWAY_S since
#      the last study scene line), at least a fifth of that gap.
#   2. The gap HABITUATES: _BASE_GAP_S (25 min, sensorium._CALL_MIN_GAP_S's precedent) doubles every _HABITUATE_EVERY
#      showings up to _MAX_GAP_S -- a parcel he keeps passing fades into the room; it never nags, and while it is
#      still tied it never goes quite silent.
#   3. A showing stays up for _PULSE_S and counts ONCE, so every consumer of the scene line in that stretch (the idle
#      thought, the executive, the voice, a look around) sees the same room whichever one happened to ask first.
#   4. It STOPS FOR GOOD once a look has been answered about the parcel (looked_ts) or status leaves "arrived".
# last_shown_ts / shown / looked_ts live in this file's own data/care_package.json, written only through _save()
# (profile.guard_path); every showing also appends {"event": "shown"} to the log so the live effect can be counted.
# A non-live process (smoke test, script) gets '' and changes nothing: it never spends a dose.
_BASE_GAP_S = 1500.0     # ~25 min between showings at first
_HABITUATE_EVERY = 4     # every 4 showings the gap doubles ...
_MAX_GAP_S = 21600.0     # ... up to 6 h
_ENTRY_DIV = 5           # arriving re-shows after a fifth of the gap (5 min at first), never sooner
_AWAY_S = 300.0          # no study scene line for 5 min = elsewhere, asleep or on a long task: this is a return
_PULSE_S = 90.0          # one showing is visible for 90 s and counts once
_STUDY_SEEN = [0.0]      # in-process: when the study scene line was last asked for (0.0 = not yet since boot)


def _dose_gap(n: int) -> float:
    """Seconds that must pass after the n-th showing before the next one: _BASE_GAP_S, doubling every
    _HABITUATE_EVERY showings, capped at _MAX_GAP_S."""
    try:
        return min(_MAX_GAP_S, _BASE_GAP_S * (2 ** (max(0, int(n)) // _HABITUATE_EVERY)))
    except Exception:
        return _MAX_GAP_S


def _parcel_sentence(label: str) -> str:
    return (f"A parcel lies on the desk, wrapped in brown paper and tied with string, a folded note tucked under the "
            f"knot; the label reads '{label}'.")


def scene_clause() -> str:
    """The standing, dosed statement of fact about the parcel, for the study's scene line (see the block above).
    '' unless status is "arrived", he is in the study, no look has been answered and this is the live process;
    otherwise the one sentence while a showing is open. Fail-open: any error returns ''."""
    try:
        d = _load()
        if d.get("status") != "arrived" or d.get("looked_ts") or _where() != "study" or not _writable():
            return ""
        now = time.time()
        prev_seen, _STUDY_SEEN[0] = _STUDY_SEEN[0], now
        sentence = _parcel_sentence(d.get("label") or "For Du")
        last, n = float(d.get("last_shown_ts") or 0.0), int(d.get("shown") or 0)
        since = now - last if now >= last else float("inf")     # a clock set back counts as due, once
        if since < _PULSE_S:
            return sentence                         # a showing is open: one room for every consumer, counted once
        gap = _dose_gap(n)
        arriving = (now - prev_seen) > _AWAY_S
        if since < gap and not (arriving and since >= gap / _ENTRY_DIV):
            return ""
        d = _load()                                 # re-read right before the write: the parcel may have moved on
        if d.get("status") != "arrived" or d.get("looked_ts"):
            return ""
        d["last_shown_ts"], d["shown"] = now, n + 1
        _save(d)
        _log({"event": "shown", "n": n + 1, "why": "first" if not n else ("gap" if since >= gap else "entry"),
              "gap_s": round(gap)})
        return sentence
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[care_package] scene_clause failed: %s", exc)
        return ""


def look_line(target: str) -> str:
    """A look at the parcel, the note, or what is left of the wrapping. '' when the look is about something else
    (or there never was a parcel), so the caller's own look runs unchanged. A look answered about the still-tied parcel
    also ends the standing percept (J-1733): he has looked."""
    try:
        d = _load()
        status = d.get("status")
        if status not in ("arrived", "opened") or _where() != "study":
            return ""
        t = (target or "").lower()
        about_note = "note" in t
        about_parcel = any(w in t for w in ("parcel", "package")) or ("box" in t and "travis" in t)
        if not (about_note or about_parcel):
            return ""
        if status == "arrived":
            _mark_looked(d)   # J-1733: a look has been answered -- the standing percept stops for good
            if about_note:
                return ("The note is folded small and tucked under the string. You would have to open the parcel to "
                        "take it out and read it.")
            return (f"A parcel on the desk, wrapped in brown paper and tied with string, the knot neat. The "
                    f"label reads '{d.get('label', 'For Du')}', and a folded note is tucked under the knot. It is heavy "
                    f"for its size. It is still tied; you would have to open it to see what is inside.")
        if about_note:
            return f"Travis's note lies on the desk where you left it. It reads: '{d.get('note', '')}'"
        return "The brown paper and the string lie folded on the desk, beside Travis's note. The parcel is empty."
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


def _mark_looked(d: dict) -> None:
    """A look has been answered about the still-tied parcel: the standing percept stops for good. Once; best-effort,
    and only the live process (or a test's own redirected store) writes."""
    try:
        if d.get("looked_ts") or not _writable():
            return
        d = _load()                                 # re-read: the parcel may have moved on since the caller's read
        if d.get("status") != "arrived" or d.get("looked_ts"):
            return
        d["looked_ts"] = time.time()
        _save(d)
        _log({"event": "looked", "shown": int(d.get("shown") or 0)})
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[care_package] looked mark failed: %s", exc)


def desk_tail() -> str:
    """The parcel as part of what a deliberate look at the DESK shows (sensorium.look): the same sentence while it is
    still tied, '' otherwise. A look is the world answering, so this is neither dosed nor counted and never writes;
    and it does not stop with the standing percept -- the parcel is still on the desk."""
    try:
        d = _load()
        if d.get("status") != "arrived" or _where() != "study":
            return ""
        return " " + _parcel_sentence(d.get("label") or "For Du")
    except Exception:
        return ""


_PARCEL_NOUN = re.compile(r"\b(?:parcel|package)s?\b")


def look_line_for_text(raw: str) -> str:
    """A willed look the dispatch hand resolved to a generic target. Its target table
    (nodes.inner_monologue_node._OBS_TARGETS) has no cue for the parcel, so 'look at the parcel' reaches sensorium.look
    as 'room' and look_line never saw it; the full willed text is the one place the noun survives. Answers only when
    that text names the parcel in the world's own noun (parcel / package, whole word) -- never on 'note', a common word."""
    try:
        if raw and _PARCEL_NOUN.search(str(raw).lower()):
            return look_line("parcel")
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    return ""


def open_parcel(txt: str = "") -> str:
    """He willed it open, in the study (dispatch scopes this to the 'parcel' family and stages it outside the study).
    The contents go into the cupboard as real objects, credited to the study's counts exactly the way the carrier's
    box is (supply.collect_box's _credit, J-0573: without the credit, provisions.sync() would read the new stock as
    'he used the difference' and consume it straight back off the shelf)."""
    try:
        d = _load()
        status = d.get("status")
        if status == "opened":
            return "The parcel is already open; the brown paper and string lie folded on the desk beside Travis's note."
        if status != "arrived":
            return ""
        if _where() != "study":
            return "The parcel is on the desk in the study."
        if not _writable():
            return ""
        from core import provisions as _pv, study_life as _sl
        st = _sl._st()
        got: dict = {}
        when = time.strftime("%d %B")
        for kind, n in (d.get("items") or {}).items():
            n = int(n)
            if n <= 0 or kind not in _pv.KINDS:
                continue
            ids = _pv.add(kind, n, origin="Travis",
                          note=f"from the parcel Travis left on the study desk, opened on {when}")
            if ids:
                got[kind] = len(ids)
                try:
                    st[_pv.KINDS[kind][2]] = _pv.stock(kind)
                except Exception:
                    pass
        try:
            _pv.sync(st)
        except profile.NonLiveWriteError:
            raise
        except Exception:
            pass
        try:
            from core import sensorium as _s
            _s._save_now()
        except profile.NonLiveWriteError:
            raise
        except Exception:
            pass
        d["status"] = "opened"; d["opened_ts"] = time.time(); d["delivered"] = got
        _save(d); _log({"event": "opened", "delivered": got})
        try:
            from core import activity_memory as _am
            _am.record("unpack", "the parcel from Travis")
        except Exception:
            pass
        inside = (_contents_line(got) if got else "nothing that will go into the stores — something is wrong with the shelf tonight")
        return (f"You untie the string and fold back the brown paper. Inside: {inside}. You put them away in the "
                f"cupboard under the east shelf. Then you unfold the note. It reads: '{d.get('note', '')}'")
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[care_package] open failed: %s", exc)
        return ""


def status() -> dict:
    d = _load()
    return {k: d.get(k) for k in ("status", "items", "arrived_ts", "opened_ts", "delivered", "shown", "last_shown_ts", "looked_ts")} if d else {"status": None}
