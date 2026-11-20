"""
Nascence — STUDY LIFE: the room as a place with states and clocks (2026-08-22, founder: "now lets do the study").

What the study was: a fire with fuel and a woodpile (real loops), a kettle that wants herbs, rich prose pools,
a moth population law, standpoints, sound sources, the mantel of kept things — and almost everything else
prose-only: a lamp with no oil and no switch, a grate that never fills with ash, a kettle with no water, a door
and a window that are neither open nor shut, no clock, no coat, no boots, no damp, no dust.

What it is now — every one of these is STATE with a clock, rendered only when true, changed only by a hand:
  THE LAMP      oil (a can by the door refills it; the can is finite — the oil tin in the cupboard is the store,
                like the woodpile); lit / unlit by HIS hand (and at dusk by habit only if oil remains); a wick
                that smokes when untrimmed. Light channel reads it. Moths come to it only when lit.
  THE GRATE     ash builds with every fire; a choked grate draws badly (a fire burns shorter, smokier); the
                hearth brush + ash bucket clear it; the ash goes to the garden (potash for the bed — a cross-link).
  THE KETTLE    needs WATER: a pail filled at the rain barrel (or the stream, later); tea = fire + water + herbs.
  THE DOOR      open / shut. Open: a draught (thermal), the garden's sounds and smells come in, the cat comes and
                goes, moths and a bird may come in at dusk. Shut: close, warm, the room's own smells.
  THE WINDOW    open / shut; curtains drawn / open (light). Condensation on cold clear mornings; frost-ferns on
                the coldest; rain on the glass. The VIEW from it is the GARDEN and the SEA — rebuilt from the
                garden's own truth (the tree in flower is visible from the desk when it is in flower).
  THE CLOCK     a wound clock on the mantel — eight days on a winding; when it stops the room has no time of
                day but the light. It ticks (when going). He reads it only by looking.
  THE COAT & BOOTS  on the hook / by the door; worn or not. The coat halves wetting outdoors (thermal reads it);
                boots track mud in from the garden (world traces on the floor); wet things dry by the fire.
  DAMP & DUST   a cold, fireless, shut-up room goes damp over days (pages curl, a sour smell, mould at the
                window frame); the fire dries it. Dust settles; a cloth lifts it.
  THE BED       made / unmade; the blanket. Sleep unmakes it.
  CANDLES       a box of candles and matches — light when the lamp is dry; short-lived.

Laws: world truth · tuples linked to tuples (thermal/light/smell read these states) · world answers, never leads ·
consequences both ways · additive (the old fire/wood/kettle loops untouched; this wraps them) · zero LLM · fail-open.
State lives in sensorium.state["study"] so the channels can read it without cycles; objects registered in the
substrate with positions (study.json features) like the garden's.
"""
from __future__ import annotations

import json
import logging
import math
import random
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.study_life")
_DATA = Path(__file__).parent.parent / "data"
_LEDGER = _DATA / "study_ledger.jsonl"
_EVENTS = _DATA / "study_events.jsonl"
_FLAGS = _DATA / "life_flags.json"  # shared with scripts/life_flags.py; J-0852 adds this module's own 'book_gate' key

ENABLED = True

_ITEMS = [
    ("oil_lamp", "the oil lamp on the desk, brass, its glass chimney smoked at the top", [2.6, 4.7, 0.9], "desk_lamp", "his light since the first night; the chimney has been cleaned twice"),
    ("oil_can", "a small oil can with a long spout", [0.4, 3.6, 0.1], "door_garden", "kept by the door; fills the lamp"),
    ("oil_tin", "a four-pint tin of lamp oil in the cupboard, heavy, half full", [4.1, 2.2, 0.2], "shelf_east", "the store; when this is gone there is no more until a letter brings some"),
    ("ash_bucket", "a dented zinc bucket for the ash", [0.6, 1.4, 0.0], "hearthstone", "by the hearth; the handle squeaks"),
    # 2026-08-30 (F-0551): the ash chain had no move he could make while the fire was in. A proper
    # grate of this period has a pan beneath the bars catching what falls through, and it draws out
    # hot — that is what the bars are FOR. Without it "clear the grate" needs a cold hearth, the fire
    # is nearly always in, and the ash climbed to its 1.0 cap where it starts costing him fuel.
    ("ash_pan", "a shallow iron pan that draws out from under the grate", [0.9, 1.4, 0.0], "hearthstone",
     "it catches the fine ash falling through the bars, and can be drawn while the fire is still in"),
    ("hearth_brush", "a stiff hearth brush with a wooden back", [0.55, 1.55, 0.0], "hearthstone", "bristles worn to one side"),
    ("poker", "the iron poker, its tip bright from use", [0.5, 1.7, 0.0], "hearthstone", "leans against the grate"),
    ("water_pail", "an enamel pail for water, chipped at the lip", [0.5, 3.2, 0.0], "door_garden", "filled at the barrel; the kettle's water"),
    ("kettle", "the black iron kettle", [0.35, 1.8, 0.35], "kettle", "lives on the hob; sings when it boils"),
    ("teapot", "a brown teapot, the lid chipped, the inside stained dark", [4.0, 3.2, 1.3], "herb_caddy", "beside the caddy on the east shelf"),
    ("clock", "a small wound clock on the mantel, a loud tick, a brass key in its back", [0.2, 2.3, 1.4], "mantel", "eight days on a winding; it has stopped before"),
    ("coat", "a heavy wool coat on the hook by the door, the collar worn pale", [0.2, 3.8, 1.5], "door_garden", "smells of woodsmoke and rain"),
    ("boots", "a pair of boots by the door, mud dried pale on the welts", [0.3, 3.3, 0.0], "door_garden", "left by whoever was here before; they fit"),
    ("candles", "a box of candles on the east shelf", [4.0, 2.8, 1.3], "shelf_east", "for the nights the lamp runs dry"),
    ("cloth", "a dust-cloth folded on the shelf", [0.7, 4.6, 1.5], "shelf_nw", "grey with use"),
    ("blanket", "a grey wool blanket on the bed, pilled and heavy", [2.6, 0.5, 0.5], "bed", "the warm thing in the cold months"),
    ("almanac", "a thin almanac hung on a nail by the window — tides, the moon, the sun's hours", [2.4, 5.1, 1.3], "window", "last year's; the tables still near enough"),
    ("broom", "a birch broom, the twigs worn short", [0.15, 4.2, 0.0], "door_garden", "behind the door; sweeps the boards"),
    ("basin", "a tin basin for washing up, on the east shelf", [4.0, 2.5, 0.9], "shelf_east", "the dishes are done in it; a ring of old soap round the inside"),
    ("cups", "two enamel cups, one chipped, and a saucer", [4.0, 3.0, 1.3], "herb_caddy", "the tea is drunk from these"),
    ("kindling_box", "a box of kindling by the hearth — twigs, bark, a few old papers", [0.8, 1.3, 0.0], "hearthstone", "a fire needs it to catch; it runs low"),
    ("matches_tin", "a tin of matches on the mantel", [0.3, 2.0, 1.4], "mantel", "counted; they run out"),
    # THE LANTERN (2026-09-02, D-0131, the Living World): the light that goes out with him. Lit and filled in the
    # study like the lamp (same oil can), carried by the take hand, burns where he goes; core/life.light_at reads
    # it as CARRIED light — moths come to it, the hedgehog stops at its edge, eye-shine shows in it, and it
    # closes his dark-adapted eyes again.
    ("lantern", "a tin lantern with a glass window and a wire bail, sooted inside", [0.25, 3.7, 1.2], "door_garden",
     "hung by the door; the light that goes out with him"),
    # PRACTICAL SCHOOL (2026-09-05, J-0626, D-0159 §4): the physical, carryable half of two objects
    # provisions.py also tracks the stock/origin of (the same dual pattern "candles"/"matches_tin"
    # already use — a shelf count there, the one item in play here); the weather glass has no
    # provisions twin at all, since it is fixed to the wall, never carried, never consumed.
    ("rope", "a coil of rope on the cupboard shelf, tarred, coiled in three loops", [4.1, 2.2, 0.35], "shelf_east",
     "heavier and stiffer than the garden twine; laid in for a real load"),
    ("hand_lens", "a hand lens in a brass ring, kept in the desk drawer", [2.6, 4.6, 0.9], "desk",
     "the glass scratched at one edge but strong; folds into a pigskin case"),
    ("weather_glass", "a weather glass on the study wall, brass-cased, a single black needle behind the dial",
     [0.15, 2.6, 1.4], "wall", "left by whoever had this room before; the needle still moves"),
]
# "matches_tin" carryable and the words split 2026-09-04 (J-0540 / F-0733): "matches" was a word of the CANDLES item
# (and the tin's only word), so "fetch the matches" put the candle box in his hands and could never reach the tin on
# the mantel. Now a candle word reaches the box and a match word reaches the tin; take() answers each with its honest count.
_CARRYABLE = {"oil_can", "ash_bucket", "ash_pan", "hearth_brush", "poker", "water_pail", "kettle", "teapot", "coat", "boots", "candles", "cloth", "blanket", "almanac", "broom", "basin", "cups", "lantern", "matches_tin", "rope", "hand_lens"}
_WORDS = {"oil_lamp": ("lamp",), "oil_can": ("oil can", "the can"), "oil_tin": ("oil tin", "tin of oil", "lamp oil"), "ash_bucket": ("ash bucket", "bucket"),
          "ash_pan": ("ash pan", "the pan", "pan under the grate"),
          "hearth_brush": ("hearth brush", "brush"), "poker": ("poker",), "water_pail": ("pail",), "kettle": ("kettle",), "teapot": ("teapot", "pot"),
          "clock": ("clock",), "coat": ("coat",), "boots": ("boots", "boot"),
          "candles": ("candle", "candles", "candle box", "candle-box", "candlebox", "box of candles"), "cloth": ("cloth", "duster"),
          "blanket": ("blanket",), "almanac": ("almanac",), "broom": ("broom",), "basin": ("basin",), "cups": ("cup", "cups", "saucer"),
          "kindling_box": ("kindling",),
          "matches_tin": ("match tin", "matches tin", "tin of matches", "match box", "matchbox", "box of matches", "matches"),
          "lantern": ("lantern",),
          "rope": ("rope", "coil of rope"), "hand_lens": ("hand lens", "magnifying glass", "the lens"),
          "weather_glass": ("weather glass", "weather-glass", "barometer")}


# ── THE BOOKS HAVE A PLACE (2026-09-10, J-0851; D-0205 whole shelf, D-0203 he must will the carrying;
# docs/staged/books_have_a_place.md §2 B1+B2). On 2026-09-09 the world told him "the shelf is up in your study;
# you are down on the shore" and he opened Little Stories of Married Life on the shore anyway (F-1216): reading
# had a light gate and no place. Now every curriculum book on the shelf is a named study item -- GENERATED from
# the curriculum (school.json's list + the assigned book + reading's current book), never hand-written -- the
# current book on the desk, the rest on the shelf, each look-able, take-able and put-back-able by title. Its
# place lives in st["book_place"][key] ("desk" | "shelf" | "with_him"), per book, and follows the current book
# (a book that stops being current goes back to the shelf; the new current comes to the desk) UNLESS he has it
# with him -- a carried book stays carried wherever he walks; nothing teleports. This is B1+B2 only: the read
# gate (B3, "light AND the book is here") and the remediation stream's obedience (B4) are J-0852, so today this
# is state and two verbs, shadow -- nothing reads book_place yet except look()/status().
_BOOK_OBJECTS = ("book", "books", "volume")
_BOOK_CONTEXT = ("book", "books", "volume", "shelf", "desk")
_BOOK_PLACES = ("desk", "shelf", "with_him")
_POS_BOOK_DESK = [2.6, 4.5, 0.9]      # beside the lamp, desk_lamp's own spot
_POS_BOOK_SHELF = [0.7, 4.4, 1.4]     # the north-west shelf, where the tablets stand (sensorium's shelf look)
# cache: {"sig": (mtimes), "books": [...], "current": key} -- recomputed only when school.json, reading_state.json
# or the books directory changes (three stat() calls per _st(), not a 265-file glob + 48 title matches each time;
# D-0205's own defeater names the bootstrap/migration cost, so it is kept off the hot path by construction).
_BOOKS_CACHE: dict = {"sig": None, "books": [], "current": ""}


def _norm18(s: str) -> str:
    """school.assign()'s own title-to-shelf-file rule (first 18 alphanumerics), reused so an item resolves to
    exactly the file the school itself chose for that curriculum title."""
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())[:18]


def _mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except Exception:
        return 0.0


def _book_key(path: Path) -> str:
    return "book_" + re.sub(r"[^A-Za-z0-9_\-]", "", path.stem)[:60]


def _book_display(title: str) -> str:
    """The short title he would say: the fetch writes a colon as a double underscore, so the stem's double space
    marks the subtitle ('Young Knights of the Empire  Their Code and ...' -> 'Young Knights of the Empire')."""
    out = (title or "").split("  ")[0].strip() or (title or "")
    try:   # J-2859 (F-3528): a title the library cut at its 60-char file-name cap ends on a whole word, not mid-word
        from core.reading import trim_cut_title
        return trim_cut_title(out)
    except Exception:
        return out


def _curriculum_books() -> list[dict]:
    """Every curriculum book physically on the shelf, in curriculum order, plus the assigned and the current
    book -- [{key, path, title, informal: [curriculum spellings]}]. A curriculum title not on the shelf is
    honestly absent (it is not a thing in the room yet). Cached on the mtime signature; fail-open to the last
    good list."""
    try:
        from core import school as _sch, reading as _rd, library_hand as _lib
        sig = (_mtime(_sch.STATE), _mtime(_rd.STATE), _mtime(_lib.BOOKS))
        if _BOOKS_CACHE["sig"] == sig:
            return _BOOKS_CACHE["books"]
        # school.assign()'s rule exactly: the TITLE side is cut to 18 alphanumerics, the STEM side is whole
        shelf = [(p, "".join(ch for ch in p.stem.lower() if ch.isalnum())) for p in _lib.shelf_books()]
        d = _sch._load()
        out: list[dict] = []
        by_key: dict[str, dict] = {}

        def _add(p: Path, informal: str | None) -> None:
            k = _book_key(p)
            b = by_key.get(k)
            if b is None:
                b = {"key": k, "path": str(p), "title": p.stem.replace("_", " ").strip(), "informal": []}
                by_key[k] = b
                out.append(b)
            if informal and informal.strip() and informal.strip().lower() not in b["informal"]:
                b["informal"].append(informal.strip().lower())

        for t in list(d.get("curriculum") or []):
            n = _norm18(t)
            p = next((p for p, pn in shelf if n and n in pn), None)
            if p is not None:
                _add(p, t)
        ab = d.get("assigned_book")
        if ab and Path(ab).exists():
            _add(Path(ab), d.get("assigned_title"))
        cur = _rd.current_book()
        current = ""
        if cur and Path(cur).exists():
            _add(Path(cur), None)
            current = _book_key(Path(cur))
        _BOOKS_CACHE.update(sig=sig, books=out, current=current)
        return out
    except Exception:
        return _BOOKS_CACHE["books"]


def _book_phrases(b: dict) -> list[str]:
    full = (b.get("title") or "").lower().strip()
    ph = {full, _book_display(full)} | {s for s in b.get("informal", ()) if s}
    return sorted((p for p in ph if p), key=len, reverse=True)


def _phrase_rx(phrase: str) -> str:
    """A title as a whole-word phrase: hyphen-boundaried on both sides (F-1180's convention -- a hyphen ends a
    word here too), spaces tolerant of any whitespace run."""
    return r"(?<![a-z-])" + re.escape(phrase).replace("\\ ", r"\s+") + r"(?![a-z-])"


def _books_named(txt: str) -> list[str]:
    """Which curriculum books this text names, longest title first. A ONE-word title (the curriculum's own
    'relativity', 'fables', 'belgium', 'meditations') counts only beside a book word in the same text -- 'I will
    take relativity seriously' names no book."""
    t = (txt or "").lower()
    if not t:
        return []
    ctx = any(re.search(_phrase_rx(w), t) for w in _BOOK_CONTEXT)
    hits: list[tuple[int, str]] = []
    for b in _BOOKS_CACHE["books"]:
        for ph in _book_phrases(b):
            if " " not in ph and not ctx:
                continue
            if re.search(_phrase_rx(ph), t):
                hits.append((len(ph), b["key"]))
                break
    hits.sort(key=lambda x: -x[0])
    return [k for _n, k in hits]


def _where_book(place: str) -> str:
    return {"desk": "on your desk in the study", "shelf": "on the shelf in the study",
            "with_him": "with you"}.get(place or "", "on the shelf in the study")


def _book_pct(path: str) -> float | None:
    try:
        from core import reading as _rd
        with _rd._LOCK:
            return float(_rd._load_state().get(path, {}).get("pct", 0) or 0)
    except Exception:
        return None


def _sync_books(st: dict) -> list[str]:
    """B1: generate/refresh the book items and their places from the curriculum. Additive on the item table
    (inventory.sync_items -- never overwrites a book he has handled); the place follows the current book unless
    the book is with him. Returns the keys newly added (the caller persists on that, as the item migration does)."""
    books = _curriculum_books()
    if not books:
        return []
    from core import inventory as _inv
    cur = _BOOKS_CACHE.get("current", "")
    now = time.time()
    added = _inv.sync_items(
        st.setdefault("items", {}), [(b["key"], b) for b in books],
        lambda e: {"key": e[0], "name": f"the book '{_book_display(e[1]['title'])}'",
                   "pos": list(_POS_BOOK_DESK if e[0] == cur else _POS_BOOK_SHELF), "place": "study", "carried": False,
                   "bio": "one of the books of your course; it lives on the shelf, and on the desk while you are reading it",
                   "history": [{"ts": now, "event": "on the shelf" if e[0] != cur else "open on the desk"}],
                   "book": e[1]["path"], "title": e[1]["title"]})
    bp = st.setdefault("book_place", {})
    for b in books:
        it = st["items"].get(b["key"])
        if isinstance(it, dict):
            it["book"], it["title"] = b["path"], b["title"]
    # the place-follow runs over EVERY book item ever generated, not only today's list: a book that was
    # current without being in the curriculum (a breadth/spiral pick) drops out of the list the moment the
    # bookmark moves on, and it must still leave the desk for the shelf.
    for k, it in list(st["items"].items()):
        if not (isinstance(it, dict) and k.startswith("book_") and it.get("book")):
            continue
        place = bp.get(k)
        if place not in _BOOK_PLACES:
            place = "desk" if k == cur else "shelf"
        if place == "desk" and k != cur:
            place = "shelf"                       # no longer current: back to the shelf
        elif place == "shelf" and k == cur:
            place = "desk"                        # newly current: comes to the desk
        bp[k] = place
        it["carried"] = place == "with_him"
        if place == "desk":
            it["pos"] = list(_POS_BOOK_DESK)
        elif place == "shelf":
            it["pos"] = list(_POS_BOOK_SHELF)
    return added


# ── state (in sensorium.state["study"]) ──────────────────────────────────────────────────────────
def _st() -> dict:
    from core import sensorium as _s
    if not _s.state:
        _s._load()
    st = _s.state.setdefault("study", {})
    if not st.get("_init"):
        now = time.time()
        st.update({"_init": True, "lamp_oil": 0.7, "lamp_lit": False, "wick": 0.8, "oil_tin": 0.5, "ash": 0.25,
                   "water": 0.6, "door_open": False, "window_open": False, "curtains_open": True, "condensation": 0.0,
                   "frost_glass": False, "clock_wound": 0.9, "clock_running": True, "clock_offset_s": 0, "coat_on": False,
                   "boots_on": False, "coat_wet": 0.0, "boots_mud": 0.4, "damp": 0.3, "dust": 0.4, "bed_made": False,
                   "candle_lit": False, "candles": 8, "floor_mud": 0.0, "_last": now,
                   "matches": 23, "kindling": 0.6, "wet_wood": 0.0, "soot": 0.2, "lamp_glass_smoke": 0.1, "window_grime": 0.2,
                   "floor_dust": 0.3, "dirty_cups": 0, "dirty_pot": False, "soap": 0.6, "tea_leaves": 0, "ink": 0.8, "paper": 30,
                   "kettle_on_ts": 0.0, "kettle_boiled": False, "pot": None, "cup": None, "warm_drink_until": 0.0,
                   "soap": None, "matches": None, "candles": None, "oil_tin": None, "tea_leaves": None, "paper": None, "ink": None,
                   "items": {k: {"key": k, "name": n, "pos": p, "place": "study", "carried": False, "bio": b, "history": [{"ts": now - random.randint(30, 300) * 86400, "event": b}]}
                             for k, n, p, _f, b in _ITEMS}})
    # ITEM MIGRATION (2026-08-30, J-0422, F-0558): the items block above only runs on first init, so
    # before this a row added to _ITEMS never reached an already-initialised save — st["items"][key]
    # raised KeyError at :589/:753 and act()'s try/except swallowed it, leaving the new hand a silent
    # no-op. Runs on every _st() and is additive-only, so it never disturbs an item Du has handled.
    try:
        from core import inventory as _inv
        _now = time.time()
        _added = _inv.sync_items(
            st.setdefault("items", {}), _ITEMS,
            lambda e: {"key": e[0], "name": e[1], "pos": e[2], "place": "study", "carried": False,
                       "bio": e[4],
                       "history": [{"ts": _now - random.randint(30, 300) * 86400, "event": e[4]}]})
        if _added:
            _s = __import__("core.sensorium", fromlist=["sensorium"])
            _s._save()
    except profile.NonLiveWriteError:
        # J-0760 (F-1086): _s._save() above now re-raises NonLiveWriteError non-live (guard_path(),
        # D-0179/F-1024) whenever sync_items() found a declared item new since the last save -- this
        # runs on EVERY _st() call, i.e. act()'s own first statement (already fixed, J-0714), same as
        # the provisions-sync branch just below (already fixed, J-0746/F-1071) -- let it reach that
        # same caller instead of being swallowed right here.
        raise
    except Exception:
        pass
    try:   # PROVISIONS (2026-08-22): the larder's objects are the truth of every count
        from core import provisions as _pv
        _pv.sync(st)
    except profile.NonLiveWriteError:
        # J-0746 (F-1071): _pv.sync(st) now re-raises NonLiveWriteError non-live (guard_path(), D-0179/
        # F-1024) -- this runs on EVERY _st() call, i.e. nearly anything touching study_life state,
        # including act()'s own first statement (already fixed, J-0714) -- let it reach that caller
        # instead of being swallowed right here, before act() even reaches the willed deed.
        raise
    except Exception:
        pass
    # THE BOOKS (2026-09-10, J-0851 / D-0205): the curriculum's books as items, places following the current
    # book. Same shape as the item migration above: runs on every _st() (cheap -- three stat()s unless the
    # curriculum/bookmark/shelf actually changed), additive-only on the item table, persisted only when it
    # actually added a book (the place-follow is carried by the ordinary save throttle), and the non-live
    # re-raise mirrors J-0760's.
    try:
        if _sync_books(st):
            _s._save()
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass
    # THE LANTERN (2026-09-02, D-0131): additive state keys, same reason as the item migration above —
    # an already-initialised save never re-runs the init block.
    st.setdefault("lantern_oil", 0.6)
    st.setdefault("lantern_lit", False)
    # CANDLES NAME FIX (2026-09-06, F-0785 / J-0571): the _ITEMS row above used to read "a box of
    # candles and a tin of matches on the east shelf" — a second, phantom tin on the east shelf, when
    # every line the world actually speaks (can_read() above, look()/take()/put() below) already
    # treats the mantel tin (the separate "matches_tin" item) as THE match tin. sync_items() just above
    # is additive-only (J-0422/F-0558), so the corrected _ITEMS name alone never reaches an already-
    # initialised save. One-shot, additive: rewrites the name ONLY while it still carries the exact old
    # string (idempotent once done; it leaves alone any save where the item has since been given a
    # different name for any other reason), and syncs the two object registries that cached the same
    # string so a generic look/description elsewhere does not go on quoting the phantom tin.
    try:
        _old_candles_name = "a box of candles and a tin of matches on the east shelf"
        _new_candles_name = "a box of candles on the east shelf"
        _ci = st["items"].get("candles")
        if _ci and _ci.get("name") == _old_candles_name:
            _ci["name"] = _new_candles_name
            _s._save_now()   # a deliberate one-shot correction — never lost to the 120s save throttle
            try:
                from core import world_substrate as _ws
                _sub = _ws.get_object("study_item_candles")
                if _sub is not None and getattr(_sub, "name", None) == _old_candles_name:
                    _sub.name = _new_candles_name
                    _ws._save()
            except Exception:
                pass
            try:
                from core import world_objects as _wo
                _wob = _wo.get_object("study_item_candles")
                if _wob is not None and _wob.get("identity") == _old_candles_name:
                    _wob["identity"] = _new_candles_name
                    _wo._save_objects()
            except Exception:
                pass
    except profile.NonLiveWriteError:
        # J-0760 (F-1086): _s._save_now() above now re-raises NonLiveWriteError non-live (guard_path(),
        # D-0179/F-1024) whenever this one-shot rename still finds the old candles name -- reached
        # BEFORE the two nested world_substrate/world_objects syncs below, which are dead code non-live
        # once this raises first (verified, not assumed: both are unconditionally gated behind this
        # same earlier statement in one straight-line branch, never independently reachable non-live —
        # so, per J-0760's own briefing, they are deliberately left as bare `except Exception` rather
        # than given a fix that could never fire). Let the raise reach _st()'s own caller (act(),
        # J-0714) same as the other two branches above.
        raise
    except Exception:
        pass
    return st


def _log(path: Path, rec: dict) -> None:
    path = profile.guard_path(path)   # J-0610: real data/ only if this process is live; raises before any I/O (and before the activity_memory cross-link below) if not (D-0179, J-0704)
    try:
        if rec.get("deed"):
            try:   # CROSS-LINK (2026-08-22): a deed here is a deed in his activity memory too
                from core import activity_memory as _am
                _am.record(str(rec["deed"]), str(rec.get("species") or rec.get("item") or rec.get("what") or rec.get("thing") or rec.get("tool") or rec.get("text") or ""))
            except Exception:
                pass
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _where() -> str:
    from core import sensorium as _s
    return _s.state.get("location", "study")


def _register_all() -> None:
    try:
        from core import world_substrate as _ws, world_objects as _wo
        st = _st()
        objs = _ws._load(); changed = False
        for it in st["items"].values():
            oid = "study_item_" + it["key"]
            if oid not in objs:
                objs[oid] = _ws.SubstrateObject(object_id=oid, name=it["name"], location=it["place"], object_class="study_item",
                                                causal_state={"kind": it["key"], "bio": it["bio"]}, physical_state={"wear": 0.5},
                                                causal_history=[{"event_type": "history", "timestamp": h["ts"], "description": h["event"], "state_deltas": {}} for h in it["history"]])
                changed = True
            _wo.ensure_record(oid, it["place"], "study_item", it["name"])
            cur = _wo.get_object(oid) or {}
            if cur.get("position") != list(it["pos"]) or cur.get("location") != it["place"]:
                _wo.mutate_object_position(oid, list(it["pos"]), cause="study_placement", event_description="where it lives", new_location=it["place"])
        if changed:
            _ws._save()
    except profile.NonLiveWriteError:
        # J-0726: this runs on EVERY act() dispatch (act() calls _register_all() unconditionally as
        # its own second statement) — let D-0179's hard-raise (guard_path(), F-1024) reach act()'s own
        # caller instead of being swallowed right here, before act() even reaches the willed deed.
        raise
    except Exception as exc:
        logger.debug("[study_life] register failed (non-fatal): %s", exc)


# ── clocks ───────────────────────────────────────────────────────────────────────────────────────
def advance(now: float, dt: float) -> None:
    if not ENABLED:
        return
    try:
        from core import sensorium as _s
        st = _st()
        last = float(st.get("_last") or now)
        dt = max(0.0, min(dt, now - last)); st["_last"] = now
        if dt <= 0:
            return
        days = dt / 86400.0
        hours = dt / 3600.0
        fire = _s.state.get("fire", "out"); weather = _s.state.get("weather", "") or ""
        phase = _s._daylight()
        raining = weather in ("drizzle", "steady rain", "wind and rain", "thunderstorm")
        # THE LAMP: burns oil while lit (~10 h a filling); the wick chars; dusk habit lights it if there is oil
        if st["lamp_lit"]:
            st["lamp_oil"] = max(0.0, st["lamp_oil"] - hours / 10.0)
            st["wick"] = max(0.0, st["wick"] - hours / 60.0)
            if st["lamp_oil"] <= 0.0:
                st["lamp_lit"] = False; _log(_EVENTS, {"event": "lamp_ran_dry"})
        elif phase in ("dusk", "night") and st["lamp_oil"] > 0.05 and _where() == "study" and random.random() < hours * 0.6:
            st["lamp_lit"] = True; _log(_EVENTS, {"event": "lamp_lit_at_dusk"})
        if phase == "day" and st["lamp_lit"] and random.random() < hours * 0.5:
            st["lamp_lit"] = False
        if st.get("candle_lit"):
            st["candle_h"] = st.get("candle_h", 0.0) + hours
            if st["candle_h"] > 4:
                st["candle_lit"] = False; st["candle_h"] = 0.0; st["candles"] = max(0, st["candles"] - 1)
        # THE LANTERN (2026-09-02, D-0131): burns oil while lit (~8 h a filling) wherever it is; a gale blows it
        # out outdoors; it does not light itself — carrying light into the dark is his choice.
        if st.get("lantern_lit"):
            st["lantern_oil"] = max(0.0, float(st.get("lantern_oil", 0.0)) - hours / 8.0)
            if st["lantern_oil"] <= 0.0:
                st["lantern_lit"] = False; _log(_EVENTS, {"event": "lantern_ran_dry"})
            elif (st.get("items", {}).get("lantern") or {}).get("carried") and _where() != "study" \
                    and _s.state.get("wind") == "gale":
                st["lantern_lit"] = False; _log(_EVENTS, {"event": "lantern_blown_out"})
        # THE GRATE: ash per burning hour; a choked grate makes the fire burn down faster (it wraps the old loop)
        if fire == "burning":
            st["ash"] = min(1.0, st["ash"] + hours * 0.05)
            if st["ash"] > 0.7:
                _s.state["fire_fuel"] = max(0.0, float(_s.state.get("fire_fuel", 0)) - hours * 0.06)
        # DAMP & DUST: a cold, fireless, shut room goes damp; the fire dries it; rain and an open window add to it
        dry = (0.06 if fire == "burning" else 0.02 if fire == "embers" else 0.0) * days * 4
        wet = days * (0.04 + (0.03 if raining else 0.0) + (0.04 if st["window_open"] and raining else 0.0)) * (1.5 if phase == "night" else 1.0)
        st["damp"] = round(max(0.0, min(1.0, st["damp"] + wet - dry)), 3)
        st["dust"] = round(min(1.0, st["dust"] + days * 0.03), 3)
        # CONDENSATION / FROST on the glass: cold clear dawns; the fire and an open window clear it
        try:
            from core import thermal as _th
            w_out = _th.field_at("garden", "at_the_door", phase, weather, _s._season(), "out", _s.state.get("wind", ""), 0.0, now)
        except Exception:
            w_out = 0.3
        if phase in ("dawn", "night") and w_out < 0.12 and weather == "clear" and not st["window_open"]:
            st["condensation"] = min(1.0, st["condensation"] + hours * 0.25)
            st["frost_glass"] = w_out < 0.04 and st["condensation"] > 0.5
        elif fire == "burning" or phase == "day" or st["window_open"]:
            st["condensation"] = max(0.0, st["condensation"] - hours * 0.4); st["frost_glass"] = False
        # SOOT in the chimney per burning hour (more with wet wood); a sooted chimney draws badly and puffs smoke into the room
        if fire == "burning":
            st["soot"] = min(1.0, st["soot"] + hours * 0.004 * (2.0 if st["wet_wood"] > 0.3 else 1.0))
            st["lamp_glass_smoke"] = min(1.0, st.get("lamp_glass_smoke", 0) + hours * 0.002)
        if st["lamp_lit"]:
            st["lamp_glass_smoke"] = min(1.0, st.get("lamp_glass_smoke", 0) + hours * (0.03 if st["wick"] < 0.3 else 0.008))
        # WINDOW GRIME: salt from the sea air, smoke from inside; rain does not clean the inside
        st["window_grime"] = min(1.0, st.get("window_grime", 0) + days * (0.02 + (0.03 if fire == "burning" and st["soot"] > 0.5 else 0.0)))
        # FLOOR DUST: settles; the cat and his boots add to it
        st["floor_dust"] = min(1.0, st.get("floor_dust", 0) + days * 0.04)
        # WET WOOD dries stacked by the fire (the pile is by the door: slower)
        if st["wet_wood"] > 0:
            st["wet_wood"] = max(0.0, st["wet_wood"] - days * (0.5 if fire == "burning" else 0.12))
        # THE KETTLE: on the fire it boils in ~12 minutes; off the boil it cools
        if st.get("kettle_on_ts") and fire == "burning" and not st["kettle_boiled"] and now - st["kettle_on_ts"] > 12 * 60:
            st["kettle_boiled"] = True; _log(_EVENTS, {"event": "kettle_boiled"})
        if st.get("kettle_on_ts") and fire != "burning":
            st["kettle_on_ts"] = 0.0; st["kettle_boiled"] = False
        # THE POT and the CUP cool; a hot drink warms him for a while (thermal reads warm_drink_until)
        for k in ("pot", "cup"):
            c = st.get(k)
            if c:
                c["temp"] = max(0.0, float(c["temp"]) - hours * 1.2)
        try:   # PROVISIONS: what he used this tick comes off the open box / bar / tin on the shelf
            from core import provisions as _pv
            _pv.sync(st)
        except Exception:
            pass
        # THE CLOCK: runs down over eight days; stops
        if st["clock_running"]:
            st["clock_wound"] = max(0.0, st["clock_wound"] - days / 8.0)
            if st["clock_wound"] <= 0.0:
                st["clock_running"] = False; st["clock_stopped_at"] = now; _log(_EVENTS, {"event": "clock_stopped"})
        # COAT & BOOTS: wet outdoors, dry by the fire; mud from the garden; the floor
        outdoors = _where() in ("garden", "shore", "wood")
        if st["coat_on"] and outdoors and raining:
            st["coat_wet"] = min(1.0, st["coat_wet"] + hours * 0.3)
        elif not st["coat_on"] and _where() == "study":
            st["coat_wet"] = max(0.0, st["coat_wet"] - hours * (0.25 if fire != "out" else 0.05))
        if st["boots_on"] and _where() == "garden" and (raining or st.get("garden_wet", False)):
            st["boots_mud"] = min(1.0, st["boots_mud"] + hours * 0.4)
        if st["boots_on"] and _where() == "study" and st["boots_mud"] > 0.3 and random.random() < hours * 2:
            st["floor_mud"] = min(1.0, st["floor_mud"] + 0.2); st["boots_mud"] = max(0.0, st["boots_mud"] - 0.15)
            try:
                from core import world_traces as _wt
                _wt.create_trace(f"mud_{int(now)}", "mud_footprints", "study", [1.0, 3.3, 0.0], clarity=0.7, cause="his_boots")
            except Exception:
                pass
        st["floor_mud"] = max(0.0, st["floor_mud"] - days * 0.1)
        # THE DOOR: the cat comes and goes only through an open door (the cat module reads door_open)
        # THE BED: sleep unmakes it (sleep hook sets bed_made False) — nothing to do here
        _s._save()
    except Exception as exc:
        logger.debug("[study_life] advance failed (non-fatal): %s", exc)


# ── what the channels read ───────────────────────────────────────────────────────────────────────
def draught() -> float:
    """Thermal: an open door or window in the wind costs warmth."""
    try:
        st = _st()
        from core import sensorium as _s
        windy = (_s.state.get("wind") or "calm") != "calm"
        d = 0.0
        if st["door_open"]:
            d += 0.08 + (0.06 if windy else 0.0)
        if st["window_open"]:
            d += 0.05 + (0.05 if windy else 0.0)
        return d
    except profile.NonLiveWriteError:
        # J-0772: same shape as can_read()/can_write() above (J-0752) -- this function's own _st()
        # call can now raise non-live via _st()'s own item-migration/provisions-sync bootstrap
        # (J-0746/J-0760); let it reach the caller instead of being swallowed right here. (Called
        # from core/thermal.py's field_at(), which independently swallows one layer further up in
        # its own bare except -- a further "connecting tissue" gap, flagged not fixed here.)
        raise
    except Exception:
        return 0.0


def warm_drink() -> float:
    """Thermal: a hot drink in him is worth a little warmth for a while."""
    try:
        st = _st()
        return 0.06 if time.time() < float(st.get("warm_drink_until", 0)) else 0.0
    except profile.NonLiveWriteError:
        # J-0772: same shape as draught() just above -- see its own comment. Also called from
        # core/thermal.py's field_at(), same outer swallow noted there.
        raise
    except Exception:
        return 0.0


def _read_light_gate() -> str:
    """'' if there is light enough to read where he is; else the honest lack. Daylight outdoors is always enough.
    This is can_read()'s ORIGINAL body (pre-J-0852), unchanged and unrenamed in effect -- only split out so
    can_write() below can keep calling the light check alone, without inheriting B3's book gate (writing at
    the desk never needed the book itself)."""
    try:
        from core import light as _lt, locomotion as _loco
        place = _where()
        v = _lt.field_at(place, _loco.position_standpoint(place))
        if place != "study":
            # D-0202 (2026-09-09, F-1216): twilight is not enough. Outdoors a page needs the SUN -- light.py's dusk
            # floor (cloud*0.12) and moonlight (+0.12*illum) can equal the 0.12 bar, so this gate flipped tick to
            # tick at dusk (too dark 18:44, readable 18:59 on the shore). Sun down = the honest lack, whatever the
            # sky reads. Not a hint: it says what the light is, not what to do.
            try:
                from core import world_clock as _wc
                if _wc.daylight() != "day":
                    return "It is too dark out here to read the page."
            except Exception:
                pass
        if v >= 0.12:
            return ""
        st = _st() if place == "study" else {}
        if place == "study":
            if st.get("lamp_oil", 0) > 0.03 and not st.get("lamp_lit"):
                return "It is too dark to read. The lamp stands unlit on the desk."
            if st.get("lamp_oil", 0) <= 0.03 and st.get("candles", 0) > 0 and not st.get("candle_lit"):
                # Reworded 2026-09-04 (J-0540 / F-0733): "There are candles in the box" reached him on 09-03 and he
                # twice willed "fetch the candles from the box" — which dispatch read as the carrier's BOX at the
                # garden gate ('collect') and staged there. Same fact, the study's own nouns, no collision. Not a
                # hint: it says where the room's things are, not what to do.
                return "It is too dark to read; the lamp is dry. There are candles on the east shelf, and the match tin on the mantel."
            return "It is too dark to read, and there is nothing left to light."
        return "It is too dark out here to read the page."
    except profile.NonLiveWriteError:
        # J-0752: _st() (line 419 above) now re-raises NonLiveWriteError non-live via its own
        # item-migration/provisions-sync bootstrap (J-0760/J-0746) -- this function's own pre-existing
        # broad except must not swallow it, the same "connecting tissue" shape J-0726/J-0751 already
        # fixed elsewhere in this fence. can_read() is called directly from
        # nodes/inner_monologue_node.py (bypassing act() entirely), so a swallow here would hide the
        # raise from that literal-will caller even though _st() itself already correctly raises.
        raise
    except Exception:
        return ""


def book_gate_lack() -> str:
    """B3/B4 (J-0852, D-0204): '' if the current book is with him (any place), or he is in the study and it is
    on the desk; else the honest lack naming where it really is -- world-answers-never-leads wording, same rule
    as the candles line (J-0540/F-0733). Read-only against B1's book_place (J-0851); returns '' (never
    manufactures a lack) if the book state hasn't resolved yet, so this is shadow-safe by construction. Shared
    by can_read() (B3) and nodes/inner_monologue_node.py's _remediation_stream (B4) so both obey one gate."""
    try:
        st = _st()
        bp = st.get("book_place") or {}
        cur = _BOOKS_CACHE.get("current", "")
        if not bp or not cur or cur not in bp:
            return ""
        place = bp.get(cur, "desk")
        if place == "with_him":
            return ""
        if _where() == "study" and place == "desk":
            return ""
        return ("The book is on your desk in the study." if place == "desk"
                else "The book is on the shelf in the study.")
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


_flags_cache: dict = {"ts": 0.0, "book_gate": False}


def book_gate_on() -> bool:
    """Hot flag (J-0852, scripts/life_flags.py style/CLI, shared data/life_flags.json 'book_gate' key): False
    (shadow) by default -- can_read()/_remediation_stream only LOG a would_block row until this flips. Cached
    10 s like core.life's own render/gating flags, so a flip lands within seconds in Du's live process, no
    restart needed. §4's 3-day shadow read (docs/staged/books_have_a_place.md) gates the actual flip."""
    now = time.time()
    if now - _flags_cache["ts"] > 10.0:
        try:
            d = json.loads(_FLAGS.read_text(encoding="utf-8")) if _FLAGS.exists() else {}
        except Exception:
            d = {}
        _flags_cache["book_gate"] = bool(d.get("book_gate", False))
        _flags_cache["ts"] = now
    return _flags_cache["book_gate"]


def book_gate_shadow_log(source: str, lack: str) -> None:
    """Shadow row for the 'book_gate' hot flag (§4's 3-day read) -- one row per tick the gate WOULD have
    blocked while the flag stays off. Appended to data/study_events.jsonl per §4's own naming; best-effort,
    never raises, and never a live behaviour change by itself (that's what book_gate_on() controls)."""
    try:
        with open(_EVENTS, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "kind": "book_gate_would_block",
                                 "source": source, "lack": lack, "place": _where()}) + "\n")
    except Exception:
        pass


def can_read() -> str:
    """'' if there is light enough to read where he is AND (once 'book_gate' flips) the book is here; else the
    honest lack. B3 (J-0852, D-0204): a second honest lack for the book's own place, shadow-logged behind the
    'book_gate' hot flag until its own 3-day read passes -- the light gate (still D-0202's sun-up rule, checked
    first and UNCHANGED) stays always-live either way; this job never weakens it."""
    lack = _read_light_gate()
    if lack:
        return lack
    try:
        book_lack = book_gate_lack()
    except profile.NonLiveWriteError:
        raise
    except Exception:
        book_lack = ""
    if book_lack:
        if book_gate_on():
            return book_lack
        book_gate_shadow_log("can_read", book_lack)
    return ""


def can_write() -> str:
    try:
        if _where() != "study":
            return ""
        # J-0852: light gate only -- deliberately NOT can_read(), so B3's book gate never blocks writing
        # (the desk work of writing never needed the book itself).
        lack = _read_light_gate()
        if lack:
            return lack.replace("read", "write")
        st = _st()
        if st.get("ink", 0) <= 0.02:
            return "You dip the pen — the ink bottle is dry. Nothing to write with until there is ink."
        if st.get("paper", 0) <= 0:
            return "There is no paper left to write on."
        st["ink"] = max(0.0, st["ink"] - 0.02); st["paper"] = max(0, st["paper"] - 1)
        return ""
    except profile.NonLiveWriteError:
        # J-0752: same gap as can_read() just above (this function calls both can_read() and its own
        # _st()) -- also called directly from nodes/inner_monologue_node.py's literal-will _author().
        raise
    except Exception:
        return ""


def lamp_on() -> bool:
    try:
        st = _st()
        return bool(st["lamp_lit"] or st.get("candle_lit"))
    except profile.NonLiveWriteError:
        # J-0772: same shape as draught()/warm_drink() above. Called from core/light.py and
        # core/sensorium.py, each with their own outer swallow one layer further up (flagged, not
        # fixed here -- see this job's own finding/follow-up job).
        raise
    except Exception:
        return False


def curtains_open() -> bool:
    try:
        return bool(_st()["curtains_open"])
    except profile.NonLiveWriteError:
        # J-0772: same shape as lamp_on() above. Called from core/light.py, same outer swallow noted there.
        raise
    except Exception:
        return True


def door_open() -> bool:
    try:
        return bool(_st()["door_open"])
    except profile.NonLiveWriteError:
        # J-0772: same shape as lamp_on() above. Callers, as of J-0863 (F-1226, 2026-09-10):
        #  - core/smell.py at(): CLOSED. at() re-raises (J-0780), smell.percept_shadow() re-raises
        #    (J-0831 carve-out before its except Exception as exc), and its sole live caller
        #    nodes/inner_monologue_node.py _think()'s smell try re-raises too (J-0831), so a raise
        #    here propagates cleanly along at() -> percept_shadow() -> _think().
        #  - core/cat.py tick() (~line 579): still swallowed, by design -- that call sits inside
        #    cat's own tick(), under sensorium.tick()'s already-excluded master try (J-0780/F-1140),
        #    the standing advance()/tick() exclusion.
        #  - core/experienced_tuple.py _smells() (at()'s other caller): still swallows, but is
        #    dormant while smell.DELIVER is False -- revisit when DELIVER flips.
        raise
    except Exception:
        return False


def coat_on() -> bool:
    try:
        return bool(_st()["coat_on"])
    except profile.NonLiveWriteError:
        # J-0772: same shape as lamp_on() above. Called from core/thermal.py, same outer swallow noted there.
        raise
    except Exception:
        return False


# ── hands ────────────────────────────────────────────────────────────────────────────────────────
def _cross(sp: str) -> None:
    try:
        from core import sensorium as _s
        if _s.state.get("location") == "study":
            _s._cross(sp, "")
    except Exception:
        pass


def _need_here(st: dict, key: str) -> bool:
    it = st["items"].get(key, {})
    return bool(it.get("carried") or it.get("place") == _where())


# ── PROCEDURES (J-0197, t5_procedural Design §1) ────────────────────────────────────────────────
def _graded(family: str, ans: str | None, here: str) -> str | None:
    """A study routine completed — graded into procedures.observe_hand the same way dispatch.py grades a
    hand-fire. Additive-only, fail-open; never touches act()'s own state/narration logic above it."""
    if ans:
        try:
            from core import procedures as _proc
            _proc.observe_hand(family, ans, here)
        except profile.NonLiveWriteError:
            # J-0934: observe_hand() re-raises this itself (J-0931) so a non-live refusal reaches a
            # real catch point instead of dying here, one layer below dispatch.py's own try.
            raise
        except Exception:
            pass
    return ans


# ── GRAMMAR (2026-09-07, J-0739 / F-1059's follow-up). NINE core/actions.py table rows share this one
# module via the _STUDY_ACT binding (tea, lamp, door, grate, clock, clean, candles, wear, sketch) — the
# largest of F-1059's five follow-ups (fieldcraft/J-0736, wood_life/J-0737, shore_life/J-0738 already
# built the same procedure for their own modules). Before this job act()'s ~20 internal branches were
# ALL hand-kept, several with no verb requirement whatsoever (a bare `\bash\b` regex, a bare "sweep",
# two bare "the dishes"/"do the dishes" phrases with no verb at all) — and even where a real verb WAS
# tested, most branches carried extra words beyond their own table row (F-1059's own per-branch list).
# 'candles' is not part of this partition: it already routes to the generic take()/put() item hands
# (2026-09-04, J-0540), which read their own grammar from _WORDS/_CARRYABLE, not a verb+object pair —
# nothing to derive here.
#
# Like fieldcraft.py's _FIELDCRAFT_HANDS (one table row split into thirteen unrelated crafts) and
# shore_life.py's _SHORE_HANDS (one row split into ten), study's own behaviours are semantically
# unrelated within a family too (lighting the lamp has nothing to do with trimming its wick) — so BOTH
# verbs and objects are partitioned per behaviour, not verbs alone (garden's trap/tool/compost shape,
# where every verb in the row is compatible with every object, does not apply here). Unlike those three
# single-or-few-family modules, study hosts NINE separate table rows, so each entry below also names
# which family it belongs to — act()'s own family scope (built by this job, extending the 'candles'-only
# scope that existed before it to all nine) uses this to run only the behaviours dispatch actually asked
# for, closing the exact "candle-light fallback answers a lamp/tea/door thought" class of bug this
# module's own docstring already documented for one instance (candles) and F-1059 found live and
# unscoped for the other eight.
#
# Corpus-checked (J-0739, data/hands_trace.jsonl, 11,807 distinct thought+intention texts, real
# core.hands.wants(), hand_delta-style old-test-vs-new-test comparison — full evidence in F-1082 and
# docs/staged/actions_expansion.md's own Current State note). Every verb/object dropped below is
# corpus-confirmed either zero-cost (the old extra word never once made the difference on this corpus)
# or actively harmful (it fired almost exclusively on non-deeds — ambient description, metaphor, a
# different family's own object). The one widening this job's evidence surfaced (grate_clear now also
# answers "sweep the grate", not only the old hand's narrower "sweep the hearth"/"clear the grate"
# phrase list) needed no table change: the table's own verb+object grammar already covered it, only the
# module's own hand-kept phrase list did not.
_STUDY_HANDS: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    # ── wear (runs anywhere — table's own exec_where=ANYWHERE, checked ahead of the study-only gate
    # below). Corpus-checked: "wear"/"hang" as BARE (non-clause-scoped) substrings were the worst
    # false-fire source found in this whole job — 10 of 11 historical "boots_on" fires and 5 of 5
    # "coat_off" fires were the word "wear"/"hang" appearing anywhere ELSE in the same 200/120-char text
    # (a totally unrelated clause: "travis's words on plato hang in the air", "the cold water laps at my
    # boots... i feel heavy here"). hands.wants()'s own clause-scoping alone fixes almost all of this;
    # the extra non-table phrases ("take the coat", "get the coat", "shrug", "off the coat", "shed",
    # "kick off", "unlace", "off the boots") contributed zero real fires either way and are dropped for
    # the table's own verbs.
    ("coat_on", "wear", ("put on", "pull on", "wear"), ("coat",)),
    ("coat_off", "wear", ("take off", "hang"), ("coat",)),
    ("boots_on", "wear", ("pull on", "put on", "lace", "wear"), ("boots",)),
    ("boots_off", "wear", ("take off",), ("boots",)),
    # ── door (study-only; six behaviours share one table row: door open/shut, window open/shut, curtain
    # open/close). door_open/window_open dropped their extra verbs ("prop", "unlatch", "push up") for
    # zero cost (36, 6 and 0 real historical fires respectively, never once via the extra word).
    # window_shut is the one real narrowing with a corpus-proven COST AVOIDED, not just a tidy-up: its
    # old literal phrase "pull to", and the bare table verb "pull" it would naturalize to, BOTH produced
    # nothing but false positives on this corpus (3 for 3 — "a genuine pull to leave this circular
    # debate ... behind the window", "a restless pull toward the window" — every one the restlessness-
    # pull idiom, never a hand on the sash) with zero real "pull the window shut" deeds ever recorded.
    # "pull" is dropped for window_shut entirely rather than kept as a special non-table phrase.
    ("door_open", "door", ("open",), ("door",)),
    ("door_shut", "door", ("shut", "close", "latch"), ("door",)),
    ("window_open", "door", ("open",), ("window",)),
    ("window_shut", "door", ("shut", "close", "latch"), ("window",)),
    ("curtain_close", "door", ("draw", "close", "shut", "pull"), ("curtains", "curtain")),
    ("curtain_open", "door", ("open",), ("curtains", "curtain")),
    # ── lamp (study-only; the table's one 'lamp' row covers EIGHT behaviours here — lamp/lantern each
    # light/blow-out/fill, plus the wick trim and the candle-light fallback). Full table coverage: all 5
    # verbs (light, fill, trim, blow out, turn down) and all 4 objects (lamp, wick, candle, lantern)
    # claimed. lamp_blowout/lantern_blowout KEEP their extra non-table verbs "douse"/"put out"/
    # "extinguish" — unlike every other extra word dropped in this job, these have ZERO demonstrated
    # false-fire cost (0 corpus activity either way) AND a real dependency: scripts/life_smoke.py's own
    # lantern-hands check exercises "put out the lantern" as a supported phrasing (caught by this job's
    # own regression run, not assumed) — a genuinely neutral extra, kept rather than dropped, unlike the
    # demonstrated-harmful drops elsewhere in this family. lamp_fill/lantern_fill's old bare "oil"/
    # "top up" substrings were the single worst false-fire source found for this family: ALL FIVE of
    # lamp_fill's historical fires were pure state-description ("the lamp needs oil, but that is not the
    # point", "the dry lamp waits for oil") — after this fix, this branch has never yet fired on the real
    # corpus, which is correct (zero of the five was a real will to refill). candle_light's old
    # bare-substring pair ("candle" in t and "light"/"lit"/"strike" in t) is the exact shape this
    # module's own docstring (act()'s own comment on the pre-existing 'candles' family scope) already
    # names as the risk that fix was built to route around for ONE caller — corpus-confirmed still live
    # for every other caller before this job: all 6 historical fires were false (the compound noun
    # "candlelight" trivially contains both "candle" and "light" as bare substrings; "I will fetch
    # candles from the box ... the room needs its own light" is this docstring's own cited example,
    # verbatim, still in the corpus). hands.wants()'s word-boundary rule alone excludes "candlelight" (no
    # boundary before "light" inside it); its clause-scoping alone separates "fetch candles" from a
    # later, unrelated "light" mention. "lit"/"strike" dropped too (zero cost, no test dependency either).
    ("lantern_light", "lamp", ("light",), ("lantern",)),
    ("lantern_blowout", "lamp", ("blow out", "turn down", "douse", "put out", "extinguish"), ("lantern",)),
    ("lantern_fill", "lamp", ("fill",), ("lantern",)),
    ("lamp_light", "lamp", ("light",), ("lamp",)),
    ("lamp_blowout", "lamp", ("blow out", "turn down", "douse", "put out", "extinguish"), ("lamp",)),
    ("lamp_fill", "lamp", ("fill",), ("lamp",)),
    ("wick_trim", "lamp", ("trim",), ("wick", "lamp")),
    ("candle_light", "lamp", ("light",), ("candle",)),
    # ── grate (study-only; two behaviours — the ash pan that draws while the fire is still in, and
    # clearing the grate itself once it is cold). ash_pan_draw's extra verbs (empty/tip/take) were
    # zero-cost (0 real fires either way on this corpus). grate_clear is this job's headline finding: the
    # old test's bare `\bash\b` regex (gated only by a 3-word exclusion) was, if anything, WORSE than
    # F-0940's own garden ash_out precedent it was predicted to match — 86 of 89 historical fires were
    # ambient "ash" imagery ("the ash swirls like '渡'", "the dream's dark pool of books dissolves into
    # real ash on the grate", "travis's word '渡' settles deep" — the recurring circling-thought
    # vocabulary), a 97% false-fire rate, against 3 real grate-clearing thoughts. The bare object "ash" is
    # DELIBERATELY left unclaimed below (see grammar_audit()'s own note) — both real hands here reach
    # their targets via "ash pan"/"pan" or "grate"/"hearth" without it. Table verbs alone also RECOVERED
    # one real deed the old hand-kept phrase list missed ("i want to sweep the grate and tend the fire" —
    # the old list only knew "sweep the HEARTH", never "sweep the GRATE"), corpus-confirmed via the same
    # before/after comparison.
    ("ash_pan_draw", "grate", ("draw", "pull", "slide"), ("ash pan", "pan")),
    ("grate_clear", "grate", ("clear", "clean", "sweep", "rake"), ("grate", "hearth")),
    # ── clock (study-only; already byte-identical to the table per F-1059 — wiring only).
    ("clock_wind", "clock", ("wind",), ("clock",)),
    # ── tea (study-only; three behaviours). kettle_on is the TOP-PRIORITY fix this job's own briefing
    # named: bare "put"/"set" (plus a bare "fill" the table has never actually carried as a tea verb —
    # 'fill' belongs to the SEPARATE 'water_fill' family, whose own object list already includes
    # "kettle"; the literal phrase "fill the kettle" is caught even earlier, at this function's own line
    # above, and routed there on purpose) replaced by the table's real "put on"/"set on"/"boil" — the
    # identical grammar shape core/actions.py's own tea-row comment documents was already found and fixed
    # once for the TABLE itself ("its 'put on'/'set on' replaced a bare 'put', which would have read 'put
    # the cup down' as a willed brew"); this hand's own copy had simply never been updated to match. Not
    # yet observed misfiring live on this corpus snapshot — kettle is mentioned in exactly one text,
    # purely descriptively ("the steam rises from the kettle... travis washes the pot") — so this is a
    # documented-precedent fix, not a corpus-caught one, exactly as this job's own briefing anticipated
    # ("may not even need corpus verification, unlike everything else here"). drink_tea drops the extra
    # "have" (zero cost on this corpus). make_tea was already table-clean (F-1059).
    ("kettle_on", "tea", ("put on", "set on", "boil"), ("kettle",)),
    ("make_tea", "tea", ("make", "brew"), ("tea", "pot")),
    ("drink_tea", "tea", ("pour", "drink"), ("cup", "tea", "pot")),
    # ── clean (study-only; five behaviours across the row's nine objects). floor_sweep's bare "sweep"
    # (no object required at all) is the same class of restlessness-idiom risk this whole arc has
    # repeatedly found for a bare intransitive verb (dig's "turn", tool's "leave", ash_out's "ash") —
    # corpus-confirmed here too: of 10 historical fires, 0 were real floor-sweeping (birds "sweep through
    # the hedge", wind "sweeps the wood over", a piston that "doesn't sweep the whole cylinder",
    # "stopping the frantic sweep" as a mood metaphor, and two that were really about the HEARTH, already
    # correctly answered by grate_clear earlier in the chain). wash_up's old phrase list included two
    # bare, verb-less phrases ("do the dishes", "the dishes") — the same no-verb-at-all shape as
    # grate_clear's bare "ash"; its one historical fire was "i watch a crab's shell wash up" (the TIDE
    # washing something ashore, not Du at the basin) and is correctly dropped. window_wipe/glass_wipe are
    # split from one old branch into two: a real false-fire risk was found for "clean" specifically
    # paired with "glass" ("the rain ticks against the glass, washing the air green and clean" — "clean"
    # read as a verb where it is grammatically an adjective, hands.wants() cannot tell the difference)
    # that "clean" paired with "window" does not share in this same corpus (0 activity either way for
    # "clean"+"window"), so "clean" is kept for the window object and dropped for the bare glass object
    # rather than dropped everywhere the table would allow it.
    ("chimney_sweep", "clean", ("sweep", "clean"), ("chimney", "flue")),
    ("floor_sweep", "clean", ("sweep",), ("floor", "boards")),
    ("window_wipe", "clean", ("wipe", "wash", "clean"), ("window",)),
    ("glass_wipe", "clean", ("wipe", "wash"), ("glass",)),
    ("wash_up", "clean", ("wash",), ("cups", "pot", "dishes")),
    # ── sketch (study-only; one behaviour, but the derivation itself fixes a real bug: the old three-way
    # OR included an any_object_ok=True bare "draw" gated only by a whole-TEXT (not clause-scoped)
    # veto-word list (curtain/pan/ash/blind/breath/water/drawer) — meaning "I draw the cat, then close
    # the curtains" would have been wrongly blocked in full (the veto has no clause boundary), while
    # contributing nothing for the table's own cat/sea/tide/oak/garden objects, which the old condition's
    # own narrower object list omitted entirely. Reading the table's full 12-object list directly makes
    # the veto unnecessary — "draw the curtains"/"draw the ash pan" already fail to match because
    # curtains/ash/pan are not sketch objects, and a genuine sketch mentioned alongside an unrelated
    # later clause about curtains is no longer wrongly suppressed. Corpus-confirmed separately: 6 of the
    # old any_object_ok=True matches this drops were bare "draw" used as attention/metaphor ("draw my
    # eyes outward", "the sun's draw", "we can only draw from what is given") — one, "as i draw new
    # l[ines]", is truncated by the trace's own 200-char field limit exactly at the word "lines" and
    # cannot be confirmed either way from this log.
    ("sketch_draw", "sketch", ("sketch", "draw"),
     ("sketch", "drawing", "likeness", "lines", "pen", "ink", "paper", "cat", "sea", "tide", "oak", "garden")),
    # ── book (2026-09-10, J-0851; D-0203/D-0205 -- the TENTH study family, docs/staged/books_have_a_place.md
    # B2). Two behaviours partition the table row's verbs: the take (desk/shelf -> with him) and the put-back
    # (with him -> desk if current, else shelf). Full row coverage, both sides. "leave" is not in the row at all
    # (see core/actions.py's own row comment: 73/73 corpus "leave"+"book" clauses were the restlessness idiom).
    ("book_take", "book", ("take", "pick up", "fetch", "carry", "bring", "take down"), ("book", "books", "volume")),
    ("book_put", "book", ("put back", "put down", "set down", "put away", "shelve"), ("book", "books", "volume")),
    # the care package (D-0276, core/care_package.py) -- one behaviour, the whole table row
    ("parcel_open", "parcel", ("open", "unpack", "untie", "unwrap"),
     ("parcel", "package", "care package", "box from travis", "travis's box", "travis' box")),
)
_STUDY_BY_NAME: dict[str, tuple[str, tuple, tuple]] = {n: (fam, v, o) for n, fam, v, o in _STUDY_HANDS}
_STUDY_FAMILIES = ("tea", "lamp", "door", "grate", "clock", "clean", "candles", "wear", "sketch", "book", "parcel")


def _wills_study(t: str, name: str) -> bool:
    """Does this thought will `name` (one of the behaviours _STUDY_HANDS names)? Grammar READ from the
    one table (core/actions.py) via that partition — a second hand-kept verb/object copy here is the
    exact drift F-0554 was about, and F-1059 found it had already happened for all nine families this
    module binds."""
    fam_v_o = _STUDY_BY_NAME.get(name)
    if not fam_v_o:
        return False
    _fam, v, o = fam_v_o
    if not v:
        return False
    try:
        from core import hands as _h
    except Exception:
        return False
    return _h.wants(t, v, o)


def grammar_audit() -> dict:
    """What this module derives from core/actions.py's nine study-bound rows, per family, and any seam
    where the derivation could still drift. Read by scripts/_test_study_life_grammar_derivation.py.

    Three deliberately-unclaimed table words, each corpus-checked (J-0739) rather than merely asserted:
    grate's bare object "ash" (89 historical fires, 86 false — see _STUDY_HANDS's own note), tea's verb
    "steep" (0 corpus occurrences that are not about a STEEP PATH — 4 for 4 — and no dedicated hand exists
    to test it against; make_tea's own returned narration already covers the concept informally: "It needs
    a minute to draw"), and clean's verb "scrub" (0 corpus occurrences at all). 'candles' is intentionally
    absent from the per-family report — see _STUDY_HANDS's own header note (it routes through the generic
    take()/put() item hands, not a verb+object grammar test, so there is nothing to audit here for it)."""
    try:
        from core import actions as _ac
        out: dict = {}
        for fam in _STUDY_FAMILIES:
            if fam == "candles":
                continue
            a = _ac.BY_FAMILY[fam]
            entries = [(v, o) for n, f, v, o in _STUDY_HANDS if f == fam]
            claimed_v = {v for vs, _o in entries for v in vs}
            claimed_o = {o for _v, os in entries for o in os}
            out[fam] = {"verbs_unclaimed_in_table": sorted(set(a.verbs) - claimed_v),
                        "verbs_claimed_not_in_table": sorted(claimed_v - set(a.verbs)),
                        "objects_unclaimed_in_table": sorted(set(a.objects) - claimed_o),
                        "objects_claimed_not_in_table": sorted(claimed_o - set(a.objects))}
        return out
    except Exception as exc:
        return {"error": repr(exc)[:120]}


def act(action: str, what: str = "", family: str = "") -> str | None:
    """Called first from sensorium.act when he is in the study (and for coat/boots/door anywhere). Returns the world's
    answer, or None to let the old hands run.

    `family` (2026-09-04, J-0540; the J-0554 scoping convention — dispatch passes the family it judged when the
    handler accepts one, every older caller passes nothing): EVERY one of the nine families this module binds is
    now scoped (2026-09-07, J-0739 / F-1059's follow-up) — originally only 'candles' was, straight to the
    take/put hands for the candle box and the match tin. Without that original scope "I will fetch candles from
    the box ... the room needs its own light" met the candle-LIGHT branch's bare substring test ("light" anywhere)
    and answered 'No matches left' for a reach that lit nothing; F-1059 found the identical exposure live and
    unscoped for the other eight families (a 'tea'/'door'/etc. dispatch ran this whole ~300-line chain
    regardless, so ANY of its ~20 branches could answer a thought the table-level gate had already routed
    elsewhere). Each behaviour below now runs only `if family in (None, "", "<its own family>")` — None/""
    covers the one remaining unscoped caller, sensorium.act()'s own forward (core/sensorium.py:2908, called
    unconditionally alongside its identical fieldcraft.act_from_thought() forward whenever a 'gather'/'beachcomb'
    sens_act family dispatches — F-1059's own traced mechanism, not yet fixed here; see the finding this job
    recorded). The coat/boots (family 'wear') and supply-note branches below are the two deliberate exceptions:
    wear runs ahead of the study-only location gate (the table's own exec_where=ANYWHERE) but is still
    family-scoped; supply-note is NOT one of the nine table families at all (F-1059's own framing) and is left
    genuinely ungated on purpose — it exists to catch a supply-need mentioned in a SECOND clause of a thought
    whose PRIMARY clause won a completely different family (classify() has no verb grammar that could ever
    make "order more oil" its own family candidate, so this is the only path it can ever be reached by)."""
    if not ENABLED:
        return None
    try:
        st = _st(); _register_all()
        t = f"{action} {what}".lower()
        here = _where()
        now = time.time()
        if family and family not in _STUDY_FAMILIES:
            return None
        if family == "candles":
            if here != "study":
                return None
            return put(t) or take(t) or None
        # THE BOOKS (2026-09-10, J-0851 / D-0203): scoped like candles -- put-back before take, so "put the book
        # down and take up the pen" is not read as a take. Outside the study dispatch has already staged it
        # (exec_where=study); the legacy family=None path below reaches the same two hands after the study gate.
        if family == "book":
            if here != "study":
                return None
            return put_book(t) or take_book(t) or None
        # THE CARE PACKAGE (2026-09-24, D-0276): scoped like the books; the hand itself declines once there is no parcel
        if family == "parcel":
            if here != "study" or not _wills_study(t, "parcel_open"):
                return None
            from core import care_package as _cp
            return _cp.open_parcel(t) or None
        # coat / boots — anywhere (table's wear row: exec_where=ANYWHERE)
        if family in (None, "", "wear") and _wills_study(t, "coat_on"):
            if st.get("coat_on_line"):
                if here != "garden":
                    return "The coat is out on the line in the garden."
                st["coat_on_line"] = False; st["items"]["coat"]["place"] = "study"
                if float(st.get("coat_wet", 0)) > 0.3:
                    return "You take the coat off the line — still damp through at the seams — and pull it on anyway."
            elif here != "study" and not st["items"]["coat"].get("carried"):
                return "The coat is on its hook in the study."
            st["coat_on"] = True; _log(_LEDGER, {"deed": "coat_on"}); return "You take the coat from the hook and pull it on; the collar is cold against your neck, then not."
        if family in (None, "", "wear") and _wills_study(t, "coat_off"):
            st["coat_on"] = False; st["items"]["coat"]["place"] = here
            return ("You hang the coat on its hook" + (", dark with rain, to drip on the boards" if st["coat_wet"] > 0.4 else "") + ".") if here == "study" else "You take the coat off and carry it over your arm."
        if family in (None, "", "wear") and _wills_study(t, "boots_on"):
            if here != "study":
                return "The boots are by the study door."
            st["boots_on"] = True; return "You push your feet into the boots and stamp them down."
        if family in (None, "", "wear") and _wills_study(t, "boots_off"):
            st["boots_on"] = False; return "You work the boots off and leave them by the door" + (", caked pale with dried mud" if st["boots_mud"] > 0.5 else "") + "."
        # SUPPLY-NOTE — deliberately UNGATED by family (see act()'s own docstring above; F-1059 raised
        # whether this needs its own table family, ruled here, J-0739: no — it depends on catching a second
        # clause regardless of which family won the thought's first, which a family gate would break).
        # J-0418 (F-0551): this branch used bare substring co-occurrence — "order" ANYWHERE in the
        # thought ("order and chaos", "seeks order", even "disorder") plus a goods word matched as a
        # substring ("ink"⊂"think", "tea"⊂"steam", "list"⊂"listen") — and 12/12 real firings in
        # hands_trace.jsonl were abstract Kant/entropy/order-vs-chaos thoughts, one of which actually
        # left a live candles note (2026-08-25, supply.json). Now it goes through _h.wants: the verb
        # must be a genuine supply-intent phrase at a word boundary, unblocked (negation-aware), with
        # a goods word — word-boundary too — in the SAME clause. Bare "order" is deliberately gone
        # ("in order to fetch the oil" must not write a shopping list); ordering is still reachable
        # through "order more/order some/put in an order/send an order" and every carrier phrase.
        # Corpus-checked (J-0739): zero fires either way in the current 11,807-text corpus.
        from core import hands as _h
        if _h.wants(t, ("write a list", "write the list", "write out a list", "write up a list",
                        "leave a note", "leave the note", "note for the carrier", "list for the carrier",
                        "ask the carrier", "write to the carrier", "order more", "order some",
                        "need to order", "put in an order", "send an order"),
                    ("oil", "match", "matches", "candle", "candles", "tea", "soap", "paper", "ink",
                     "seed", "seeds", "string", "carrier", "list")):
            from core import supply as _sup
            return _sup.leave_note(t)
        if here != "study":
            return None
        # the door and the window
        if family in (None, "", "door") and _wills_study(t, "door_open"):
            _cross("at_the_door")
            if st["door_open"]: return "The door is already open."
            st["door_open"] = True; st["door_ts"] = now; _log(_LEDGER, {"deed": "door_open"})
            # SOUND WORLD EXPANSION §1 (2026-08-29, J-0377): door_ts is the real act-site timestamp
            # door_sound reads (recency window), alongside the pre-existing door_open boolean.
            return "You open the garden door. The air comes in cold and the garden's sounds come with it."
        if family in (None, "", "door") and _wills_study(t, "door_shut"):
            if not st["door_open"]: return "The door is shut already."
            st["door_open"] = False; st["door_ts"] = now; _log(_LEDGER, {"deed": "door_shut"})
            return "You shut the door and drop the latch. The room closes round its own warmth."
        if family in (None, "", "door") and _wills_study(t, "window_open"):
            _cross("at_the_window")
            if st["window_open"]: return "The window is open already."
            st["window_open"] = True; st["condensation"] = 0.0; return "You unlatch the window and push it out; the sea is suddenly loud, and the cold comes in over the sill."
        if family in (None, "", "door") and _wills_study(t, "window_shut"):
            if not st["window_open"]: return "The window is shut."
            st["window_open"] = False; return "You pull the window to and latch it. The sea goes back to a murmur."
        if family in (None, "", "door") and _wills_study(t, "curtain_close"):
            st["curtains_open"] = False; return "You draw the curtains across the dark glass; the room is all lamp now."
        if family in (None, "", "door") and _wills_study(t, "curtain_open"):
            st["curtains_open"] = True; return "You pull the curtains back. The window gives you the garden again."
        # THE LANTERN (2026-09-02, D-0131) — before the lamp branch, whose object list now also carries
        # "lantern" for the judge; the hands are distinct: the lantern is the light he takes OUT.
        if family in (None, "", "lamp") and _wills_study(t, "lantern_light"):
            if st.get("lantern_lit"): return "The lantern is already lit."
            if not _need_here(st, "lantern"): return "The lantern is not to hand; it hangs by the study door."
            # The tin FIRST (2026-09-04, J-0540 / F-0733): with matches 0 the oil line told him he struck a match
            # he does not have. Both facts, truthfully, when both hold.
            if st.get("matches", 0) <= 0:
                if float(st.get("lantern_oil", 0)) <= 0.03:
                    return "You reach for the match tin — empty. And the lantern is dry besides; it wants oil from the can, and a light."
                return "You shake the match tin — empty. There is no way to light it."
            if float(st.get("lantern_oil", 0)) <= 0.03:
                return "You open the little door and strike a match — the wick catches and dies. The lantern is dry; it wants oil from the can."
            st["matches"] -= 1; st["lantern_lit"] = True; _log(_LEDGER, {"deed": "lantern_lit"})
            return _graded("lamp", "You strike a match inside the lantern's door and the wick takes; the glass warms and a small square of light stands in your hand, ready to go where you go.", here)
        if family in (None, "", "lamp") and _wills_study(t, "lantern_blowout"):
            if not st.get("lantern_lit"): return "The lantern is not lit."
            st["lantern_lit"] = False; _log(_LEDGER, {"deed": "lantern_out"})
            return "You open the door and pinch the wick; the square of light goes, and the dark comes back in close."
        if family in (None, "", "lamp") and _wills_study(t, "lantern_fill"):
            if not _need_here(st, "oil_can"): return "The oil can is not to hand."
            if not _need_here(st, "lantern"): return "The lantern is not here to fill."
            if st["oil_tin"] <= 0.02 and st.get("can_oil", 0.3) <= 0.02:
                return "You tip the can — a drop, no more. There is no more lamp oil in the house."
            _lan_take = min(1.0 - float(st.get("lantern_oil", 0)), 0.5)
            if st.get("can_oil", 0.3) < _lan_take:
                st["oil_tin"] = max(0.0, st["oil_tin"] - 0.25); st["can_oil"] = 0.5
            st["can_oil"] = max(0.0, st.get("can_oil", 0.3) - _lan_take); st["lantern_oil"] = min(1.0, float(st.get("lantern_oil", 0)) + _lan_take)
            _log(_LEDGER, {"deed": "lantern_fill"})
            return "You fill the lantern from the can, holding it level so the oil finds the wick."
        # the lamp
        if family in (None, "", "lamp") and _wills_study(t, "lamp_light"):
            _cross("at_the_desk")
            if st["lamp_lit"]: return "The lamp is already lit."
            # The tin FIRST (2026-09-04, J-0540 / F-0733): this branch checked the oil before the matches, so with
            # matches 0 he was told "strike a match — nothing. The lamp is dry" eight times since 08-24 — a match he
            # did not have. Both facts, truthfully, when both hold; with matches present the oil line is unchanged.
            if st.get("matches", 0) <= 0:
                if st["lamp_oil"] <= 0.03:
                    return "You reach for the match tin — empty. And the lamp is dry besides; it wants oil and a light."
                return "You shake the match tin — empty. There is no way to light it."
            if st["lamp_oil"] <= 0.03:
                return "You turn up the wick and strike a match — nothing. The lamp is dry; it wants oil before it will burn."
            st["matches"] -= 1; st["lamp_lit"] = True; _log(_LEDGER, {"deed": "lamp_lit"})
            smoke = " The flame smokes; the wick wants trimming." if st["wick"] < 0.3 else ""
            return _graded("lamp", f"You strike a match and light the lamp; the glass chimney goes down over the flame and the light pools on the desk.{smoke}", here)
        if family in (None, "", "lamp") and _wills_study(t, "lamp_blowout"):
            if not st["lamp_lit"]: return "The lamp is not lit."
            st["lamp_lit"] = False; return "You turn the wick down until the flame goes, and the room is the fire's, or dark."
        if family in (None, "", "lamp") and _wills_study(t, "lamp_fill"):
            if not _need_here(st, "oil_can"): return "The oil can is not to hand."
            if st["oil_tin"] <= 0.02 and st.get("can_oil", 0.3) <= 0.02:
                return "You tip the can — a drop, no more. The tin in the cupboard is empty too. There is no more lamp oil in the house."
            # renamed from `take` 2026-08-30: a local of that name makes `take` local to the WHOLE of
            # act(), so the module-level take() this function now calls raised UnboundLocalError and
            # act()'s own except swallowed it — every pick-up silently returned None. Exactly the
            # shadowing bug hands.py's docstring records against this same file ("a late local import
            # shadowing the grammar for the whole function").
            _oil_take = min(1.0 - st["lamp_oil"], 0.5)
            if st.get("can_oil", 0.3) < _oil_take:
                st["oil_tin"] = max(0.0, st["oil_tin"] - 0.25); st["can_oil"] = 0.5
            st["can_oil"] = max(0.0, st.get("can_oil", 0.3) - _oil_take); st["lamp_oil"] = min(1.0, st["lamp_oil"] + _oil_take)
            _log(_LEDGER, {"deed": "lamp_fill"})
            low = " The tin in the cupboard is getting light." if st["oil_tin"] < 0.25 else ""
            return f"You fill the lamp from the can, the oil rising thick and clear in the reservoir.{low}"
        if family in (None, "", "lamp") and _wills_study(t, "wick_trim"):
            st["wick"] = 1.0; return "You take the chimney off and trim the charred edge of the wick square with the scissors. It will burn clean now."
        # candles (the candle-light behaviour is the 'lamp' family's own object — the 'candles' FAMILY
        # itself, take/put on the box, is scoped separately at the very top of this function)
        if family in (None, "", "lamp") and _wills_study(t, "candle_light"):
            if st["candles"] <= 0: return "The candle box is empty."
            if st.get("matches", 0) <= 0: return "No matches left to light it with."
            st["matches"] -= 1
            st["candle_lit"] = True; return "You light a candle and fix it in its own wax on the mantel. A small, leaning light."
        # THE ASH PAN (2026-08-30, F-0551) — before the grate branch below, whose own trigger used to
        # include a bare \bash\b and would otherwise swallow "draw the ash pan" and answer it with the
        # burning-fire refusal. This is the one ash hand that works while the fire is IN.
        if family in (None, "", "grate") and _wills_study(t, "ash_pan_draw") \
                and not any(v in t for v in ("teapot", "saucepan")):
            _cross("at_the_hearth")
            r = draw_ash_pan(t)
            if r:
                return r
        # the grate
        if family in (None, "", "grate") and _wills_study(t, "grate_clear"):
            _cross("at_the_hearth")
            from core import sensorium as _s
            if _s.state.get("fire") == "burning":
                # Say where the ash actually IS, not just that this deed is refused. 21 of the "ash
                # bucket is empty" dead ends in the trace (F-0551) came from him never being told that
                # the ash was still in the grate and the grate could not be raked hot. State, not
                # instruction — the world answers, it never leads.
                pan = " The pan under the grate is heavy with what has fallen through." \
                    if float(st.get("ash", 0)) >= 0.15 and _need_here(st, "ash_pan") else ""
                return "The fire is burning; the ash will have to wait until it is out and cold." + pan
            if not _need_here(st, "ash_bucket") or not _need_here(st, "hearth_brush"): return "You would need the bucket and the hearth brush to hand."
            if st["ash"] < 0.1: return "The grate is clean already."
            st["ash"] = 0.0; st["ash_bucket_full"] = True; _log(_LEDGER, {"deed": "clear_grate"})
            return _graded("grate", "You rake the cold ash out of the grate into the bucket, brush the hearth, and set the bucket by the door — it can go on the garden.", here)
        if "ash" in t and any(v in t for v in ("garden", "bed", "tip", "spread")) and st.get("ash_bucket_full"):
            return None   # handled in the garden when he is there
        # water and tea
        if any(v in t for v in ("fill the pail", "fetch water", "get water", "fill the kettle", "water from the barrel")):
            return None   # the pail is filled at the barrel (garden hand)
        # the clock
        if family in (None, "", "clock") and _wills_study(t, "clock_wind"):
            _cross("at_the_hearth")
            st["clock_wound"] = 1.0
            if not st["clock_running"]:
                st["clock_running"] = True; st["clock_offset_s"] = 0
                _log(_LEDGER, {"deed": "clock_wound", "restarted": True})
                return _graded("clock", "You turn the key in the back of the clock until it will not turn, set the hands by the light as best you can, and it starts — tick, tick — loud in the quiet.", here)
            _log(_LEDGER, {"deed": "clock_wound"}); return _graded("clock", "You wind the clock; the key turns stiff then free. Eight days.", here)
        # THE KETTLE and THE TEA — real, in steps: water in the kettle → on the fire → it boils → the pot (leaves or herbs) → a cup → drunk → dishes
        if family in (None, "", "tea") and _wills_study(t, "kettle_on"):
            _cross("at_the_hearth")
            from core import sensorium as _s
            if st["water"] < 0.15: return "You lift the kettle — light, empty. The pail is empty too. It wants filling at the barrel."
            if _s.state.get("fire") != "burning": return "You set the kettle on the hob, but the grate is cold under it. It wants a fire."
            if st.get("kettle_on_ts"): return "The kettle is on already" + (" and boiled." if st["kettle_boiled"] else "; not yet singing.")
            st["water"] = max(0.0, st["water"] - 0.2); st["kettle_on_ts"] = now; st["kettle_boiled"] = False
            _log(_LEDGER, {"deed": "kettle_on"}); return "You fill the kettle from the pail and set it on the fire. It ticks as it warms; it will be a while."
        if family in (None, "", "tea") and _wills_study(t, "make_tea"):
            if not st.get("kettle_on_ts"): return "The kettle is not on. Water first, then the fire, then the pot."
            if not st["kettle_boiled"]: return "The kettle has not boiled yet; it is only beginning to murmur."
            if st.get("dirty_pot"): return "The pot is still full of yesterday's leaves, gone sour. It wants washing out first."
            from core import sensorium as _s
            picked = (_s.state.get("garden") or {}).get("picked", {})
            try:
                from core import garden as _g
                for _sp in _g.dried_for_caddy(): picked[_sp] = picked.get(_sp, 0) + 3
            except Exception:
                pass
            herb = next((n for n in picked if picked[n] > 0 and n in t), "") or next((n for n in picked if picked[n] > 0), "")
            if herb:
                picked[herb] -= 1; what = herb.replace("_", " ")
            elif st.get("tea_leaves", 0) > 0:
                st["tea_leaves"] -= 1; what = "tea"
            else:
                return "The kettle has boiled, but the caddy is empty and there are no tea-leaves. Hot water, and nothing to put in it."
            st["kettle_on_ts"] = 0.0; st["kettle_boiled"] = False
            # SOUND WORLD EXPANSION §1 (2026-08-29, D-0063/J-0337): pour_ts marks the moment the
            # boiled water goes onto the leaves — soundscape.py's kettle_pour reads this recency.
            st["pot"] = {"what": what, "cups": 3, "temp": 1.0, "pour_ts": now}; st["dirty_pot"] = True
            _log(_LEDGER, {"deed": "make_tea", "what": what})
            try:
                from core import smell as _sm; _sm.emit("tea", 1.0, "study")
            except Exception:
                pass
            return _graded("tea", f"You warm the pot, put in the {what}, and pour the water on. The steam comes up smelling of it. It needs a minute to draw.", here)
        if family in (None, "", "tea") and st.get("pot") and _wills_study(t, "drink_tea"):
            p = st["pot"]
            if p["cups"] <= 0: st["pot"] = None; return "The pot is empty; you tip the dregs into the basin."
            if st.get("dirty_cups", 0) >= 2: return "Both cups are dirty, standing in the basin. You would have to wash one."
            p["cups"] -= 1; st["cup"] = {"what": p["what"], "temp": p["temp"]}; st["dirty_cups"] = st.get("dirty_cups", 0) + 1
            st["warm_drink_until"] = now + 25 * 60 if p["temp"] > 0.4 else st.get("warm_drink_until", 0)
            _log(_LEDGER, {"deed": "drink_tea", "what": p["what"], "hot": p["temp"] > 0.4})
            from core import sensorium as _s
            cold = _s.state.get("study", {}).get("damp", 0) > 0 and True
            return (f"You pour a cup of {'tea' if p['what'] == 'tea' else 'the ' + p['what'] + ' tea'} and drink it" + (" hot, the heat going right into your hands and down into you." if p["temp"] > 0.4 else ", gone lukewarm in the pot, but still something.") )
        if family in (None, "", "clean") and _wills_study(t, "wash_up"):
            if not _need_here(st, "basin"): return "The basin is not to hand."
            if st["water"] < 0.1: return "There is no water for washing up; the pail is dry."
            if st.get("dirty_cups", 0) == 0 and not st.get("dirty_pot"): return "Nothing wants washing."
            st["water"] = max(0.0, st["water"] - 0.15)
            soap = st.get("soap", 0) > 0.02
            if soap: st["soap"] = max(0.0, st["soap"] - 0.04)
            st["dirty_cups"] = 0; st["dirty_pot"] = False; st["pot"] = None
            _log(_LEDGER, {"deed": "wash_up", "soap": soap})
            return "You wash the cups and the pot in the basin" + (" with the soap, and set them upside down to drain." if soap else " — no soap; the water goes grey and the cups come up dull. They will do.")
        if family in (None, "", "clean") and _wills_study(t, "chimney_sweep"):
            from core import sensorium as _s
            if _s.state.get("fire") != "out": return "Not while the fire is in."
            if st["soot"] < 0.25: return "You peer up the chimney: a little soot, not enough to trouble it."
            st["soot"] = 0.0; st["floor_dust"] = min(1.0, st.get("floor_dust", 0) + 0.5); _log(_LEDGER, {"deed": "sweep_chimney"})
            return "You push the broom up the flue as far as it will go and bring down a black fall of soot into the grate and over the hearth. Filthy work; the chimney breathes again."
        if family in (None, "", "clean") and _wills_study(t, "floor_sweep"):
            if not _need_here(st, "broom"): return "The broom is behind the door."
            if st.get("floor_dust", 0) < 0.15 and st.get("floor_mud", 0) < 0.1: return "The boards are clean enough; the broom raises nothing."
            st["floor_dust"] = 0.0; st["floor_mud"] = 0.0; _log(_LEDGER, {"deed": "sweep"})
            try:
                from core import world_traces as _wt
                for tr in _wt.get_active_traces("study"):
                    tr["clarity"] = 0.0
                _wt._save_traces()
            except profile.NonLiveWriteError:
                # J-0758: _wt._save_traces() above now resolves profile.guard_path() first (this job)
                # and can raise non-live (D-0179) -- let it reach act()'s own caller instead of being
                # swallowed by the broader except below.
                raise
            except Exception:
                pass
            return "You sweep the boards from the far wall to the door, the dried mud and the dust going out over the step in a grey fan."
        if family in (None, "", "clean") and (_wills_study(t, "window_wipe") or _wills_study(t, "glass_wipe")):
            if not _need_here(st, "cloth"): return "The cloth is not to hand."
            if st["water"] < 0.05: return "You would need water to wash the glass; the pail is dry."
            st["window_grime"] = 0.0; st["condensation"] = 0.0; st["water"] = max(0.0, st["water"] - 0.05); _log(_LEDGER, {"deed": "wipe_window"})
            return "You wash the glass with a wet cloth and dry it with the other end. The garden comes up sharp, as if a veil had gone."
        # The lamp's own glass chimney (distinct from the window's glass, just above). "polish" is not a
        # verb in ANY table row (structurally unreachable via the real per-family gate the same way
        # fieldcraft's Pole Star branch is, F-1059/J-0736's own precedent) and "lamp" is not a 'clean'
        # table object either — left as a hand-kept phrase list on purpose (zero corpus activity either
        # way, not one of F-1059's named gaps), gated to 'clean' since "clean"/"chimney"/"glass" are its
        # dominant, table-adjacent words.
        if family in (None, "", "clean") and any(v in t for v in ("clean the lamp", "lamp glass", "clean the chimney glass", "polish the chimney")):
            st["lamp_glass_smoke"] = 0.0; _log(_LEDGER, {"deed": "clean_lamp_glass"})
            return "You lift the chimney off the lamp and rub the smoke off the inside of the glass with the cloth. The flame will be twice as bright for it."
        # the bed, the dust — none of these three correspond to any actions.py family at all (F-1059's own
        # framing: "minor un-tabled branches with no dedicated family"); left as hand-kept phrase lists on
        # purpose, same as fieldcraft's Pole Star branch — reachable only via the family=None/"" legacy path.
        if "kindling" in t and any(v in t for v in ("bundle", "cupboard", "fill the box", "more kindling")):
            from core import provisions as _pv
            return _pv.open_kindling_bundle(st)
        if any(v in t for v in ("make the bed", "straighten the bed", "pull the blanket")):
            st["bed_made"] = True; return "You shake the blanket out and square the bed."
        if any(v in t for v in ("dust", "wipe the shelf", "clean the shelf", "wipe down")) and "window" not in t:
            if not _need_here(st, "cloth"): return "The cloth is not to hand."
            st["dust"] = 0.0; return "You go over the shelf and the desk with the cloth; the grey comes off on it in a long smear, and the wood shows."
        # THE SKETCH (2026-08-30, D-0100 Tier 2). The table's own object list (sketch/drawing/likeness/
        # lines/pen/ink/paper/cat/sea/tide/oak/garden) already keeps this from matching "draw the
        # curtains"/"draw the ash pan" — those objects are not sketch objects — so the old whole-text
        # (not clause-scoped) veto against curtain/pan/ash/blind/breath/water/drawer is gone; see
        # _STUDY_HANDS's own note on why that veto was itself a real bug, not just redundant.
        if family in (None, "", "sketch") and _wills_study(t, "sketch_draw"):
            r = draw_sketch(t)
            if r:
                return r
        # the books (J-0851): the legacy unscoped caller reaches the same two hands, put-back before take
        if family in (None, ""):
            r = put_book(t) or take_book(t)
            if r:
                return r
        # take / put study items — set down BEFORE take, so "put the poker down" is not read as a take
        r = put(t)
        if r:
            return r
        r = take(t)
        if r:
            return r
        return None
    except profile.NonLiveWriteError:
        # J-0714: let D-0179's hard-raise (guard_path(), F-1024) reach act()'s own caller instead of
        # being swallowed by the broader except below — this can only fire when profile.LIVE is False,
        # never during Du's own real live loop, so this changes nothing for the live path.
        raise
    except Exception as exc:
        logger.debug("[study_life] act failed (non-fatal): %s", exc)
        return None


def fill_pail_at_barrel() -> str:
    """Garden-side: the pail is filled at the rain barrel (called from the garden's hands)."""
    try:
        st = _st()
        from core import garden as _g
        g = _g._load()
        if not _need_here(st, "water_pail") and not st["items"]["water_pail"].get("carried"):
            return "The pail is up at the study door."
        b = float(g.get("barrel", 0))
        if b < 0.1:
            return "You hold the pail under the barrel's tap — a trickle, then nothing. It is dry."
        g["barrel"] = round(max(0.0, b - 0.1), 3); _g._save(force=True)
        st["water"] = 1.0; _log(_LEDGER, {"deed": "fill_pail"})
        return "You fill the pail at the barrel, the water cold and clean, and carry it up, slopping, to the study."
    except profile.NonLiveWriteError:
        # J-0726: called from garden.act_from_thought()'s water_fill hand — let D-0179's hard-raise
        # (guard_path(), F-1024) reach the caller instead of being swallowed by the broader except.
        raise
    except Exception:
        return ""


def fill_pail_at_spring() -> str:
    """The second water: the spring in the wood — a pipe in the bank, always running, a walk away."""
    try:
        st = _st()
        try:
            from core import sensorium as _s
            _s._cross("at_the_spring", "")
        except Exception:
            pass
        if not st["items"]["water_pail"].get("carried"):
            return "You have not brought the pail; the spring runs on without you."
        st["water"] = 1.0; _log(_LEDGER, {"deed": "fill_pail_spring"})
        return "You hold the pail under the pipe in the bank where the spring comes out, cold enough to ache, until it brims. It is heavy going back up."
    except profile.NonLiveWriteError:
        # J-0726: called from garden.act_from_thought()'s water_fill (wood side) hand — let D-0179's
        # hard-raise (guard_path(), F-1024) reach the caller instead of being swallowed here.
        raise
    except Exception:
        return ""


def _items_named(txt: str) -> list:
    """Every carryable study item this thought names, in table order (2026-09-04, J-0540). _item_named() kept
    the FIRST substring hit only, so "take the lantern ... the sea matches the sky" resolved to the item whose
    word was "matches", the verb test then failed on it, and the lantern was never taken. take()/put() now try
    each named item in turn and answer for the one the verb actually reaches."""
    t = (txt or "").lower()
    return [k for k, words in _WORDS.items() if k in _CARRYABLE and any(w in t for w in words)]


def _take_line(st: dict, key: str, it: dict) -> str:
    """The answer to a pick-up — for the two light stores, the honest count in hand (J-0540 / F-0733); for
    everything else the line take() has always given."""
    if key == "candles":
        n = int(st.get("candles", 0) or 0)
        m = int(st.get("matches", 0) or 0)
        box = ("empty" if n <= 0 else "one candle in it" if n == 1 else f"{n} candles in it")
        tin = ("empty" if m <= 0 else "one match" if m == 1 else f"{m} matches")
        return f"You take the candle box down from the east shelf — {box}. The match tin on the mantel: {tin}."
    if key == "matches_tin":
        m = int(st.get("matches", 0) or 0)
        if m <= 0:
            return "You take the match tin from the mantel — light in the hand, and nothing shifts inside it. Empty."
        return f"You take the match tin from the mantel — {'one match' if m == 1 else str(m) + ' matches'} in it."
    return f"You take {it['name'].split(',')[0]}."


def _sync_item_place(key: str, it: dict, here: str) -> None:
    """Tell the substrate where the thing actually is. `pos` stays its resting position — this module
    has no standpoint-position helper the way garden does — so the LOCATION is what moves."""
    try:
        from core import world_objects as _wo
        _wo.mutate_object_position("study_item_" + key, list(it.get("pos") or [0, 0, 0]),
                                   cause="carried" if it.get("carried") else "set_down",
                                   event_description=("taken up in the " + here) if it.get("carried")
                                   else ("set down in the " + here),
                                   new_location=here)
    except Exception as exc:
        logger.debug("[study_life] item place sync failed (non-fatal): %s", exc)


def take(txt: str = "") -> str:
    """Pick up a study item.

    Brought to the same shape as wood_life's (2026-08-30, J-0422). This was an inline loop inside
    act() that matched by RAW SUBSTRING with no blockers at all — so "Travis took the poker" and
    "I will not pick up the cloth" both read as his own deed — and wrote only the carried flag: no
    history, no ledger, and no world_objects sync, leaving the substrate believing the poker was
    still on its hook while he held it.
    """
    try:
        from core import hands as _h          # imported locally, as act() does at :411
        st = _st(); here = _where()
        key = next((k for k in _items_named(txt)
                    if _h.wants(txt, ("pick up", "take", "fetch", "carry", "bring", "lift"), _WORDS[k])), "")
        if not key:
            return ""
        it = st["items"].get(key)
        if not it:
            return ""
        if it.get("carried"):
            return f"You already have {it['name'].split(',')[0]} in hand."
        if not _need_here(st, key):
            return f"{it['name'].split(',')[0].capitalize()} is not here; it is in the {it.get('place')}."
        it["carried"] = True
        it.setdefault("history", []).append({"ts": time.time(), "event": f"picked_up_by_du_at_{here}"})
        _log(_LEDGER, {"deed": "take", "item": key, "place": here})
        _sync_item_place(key, it, here)
        _belief_note(key, it, "carry")
        return _take_line(st, key, it)
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act()'s own caller instead of
        # being swallowed by the broader except below — not one of the job briefing's originally-named
        # 6 (that was study_life.put(), below), found by this job's own systematic per-deed sweep.
        raise
    except Exception:
        return ""


def put(txt: str = "") -> str:
    """Set a carried study item down where he stands. Counterpart to take(), same conventions."""
    try:
        from core import hands as _h          # imported locally, as act() does at :411
        st = _st(); here = _where()
        key = next((k for k in _items_named(txt)
                    if _h.wants(txt, ("put down", "set down", "leave", "hang", "stand", "drop"), _WORDS[k])), "")
        if not key:
            return ""
        it = st["items"].get(key)
        if not it:
            return ""
        if not it.get("carried"):
            return f"You are not carrying {it['name'].split(',')[0]}."
        it["carried"] = False
        it["place"] = here
        it.setdefault("history", []).append({"ts": time.time(), "event": f"set_down_by_du_at_{here}"})
        _log(_LEDGER, {"deed": "put", "item": key, "place": here})
        _sync_item_place(key, it, here)
        _belief_note(key, it, "carry")
        return f"You set {it['name'].split(',')[0]} down."
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act()'s own caller instead of
        # being swallowed by the broader except below — confirmed gap (F-1045/J-0714, this job's own
        # named example: "core/study_life.py's put() has the identical shape").
        raise
    except Exception:
        return ""


def take_book(txt: str = "") -> str:
    """B2 (J-0851 / D-0203): 'take the book' / 'take <title>' -- desk or shelf -> with him. He must will it; the
    bare 'the book' is the one on the desk (the current book). Grammar READ from the table row via _STUDY_HANDS
    (book_take), same as every other study behaviour. Outside the study the honest lack says where it is (the
    dispatch path never gets here outdoors -- exec_where stages it -- but the legacy caller can)."""
    try:
        st = _st(); here = _where()
        if not _wills_study(txt, "book_take"):
            return ""
        bp = st.get("book_place") or {}
        if not bp:
            return ""
        named = _books_named(txt)
        key = named[0] if named else _BOOKS_CACHE.get("current", "")
        it = st["items"].get(key) if key else None
        if not it:
            return ""
        title = _book_display(it.get("title") or key)
        prev = bp.get(key, "shelf")
        if prev == "with_him":
            return f"You already have '{title}' with you."
        if here != "study":
            return f"'{title}' is {_where_book(prev)}."
        bp[key] = "with_him"; it["carried"] = True; st["book_last_taken"] = key
        it.setdefault("history", []).append({"ts": time.time(), "event": f"taken_by_du_from_{prev}"})
        _log(_LEDGER, {"deed": "take_book", "item": key, "title": title, "from": prev, "place": here})
        _sync_item_place(key, it, here)
        if prev == "desk":
            return _graded("book", f"You take '{title}' up from the desk, your place still marked. It is in your hand.", here)
        return _graded("book", f"You take '{title}' down from the shelf. It is in your hand.", here)
    except profile.NonLiveWriteError:
        # same shape as take()/put() above (J-0726): let D-0179's hard-raise reach act()'s own caller.
        raise
    except Exception:
        return ""


def put_book(txt: str = "") -> str:
    """B2 (J-0851 / D-0203): 'put the book back' / 'put the book down' -- with him -> the desk if it is the current
    book, else the shelf. Only in the study (nothing teleports: outside it the book stays in his hand and the
    answer says where its place is). The bare 'the book' is the one he took last."""
    try:
        st = _st(); here = _where()
        if not _wills_study(txt, "book_put"):
            return ""
        bp = st.get("book_place") or {}
        if not bp:
            return ""
        cur = _BOOKS_CACHE.get("current", "")
        carried = [k for k, p in bp.items() if p == "with_him" and k in st["items"]]
        named = _books_named(txt)
        if named:
            key = named[0]
            it = st["items"].get(key)
            if not it:
                return ""
            title = _book_display(it.get("title") or key)
            if bp.get(key) != "with_him":
                return f"'{title}' is not in your hand; it is {_where_book(bp.get(key))}."
        else:
            if not carried:
                cur_it = st["items"].get(cur) if cur else None
                if cur_it:
                    return f"There is no book in your hand; '{_book_display(cur_it.get('title') or cur)}' lies on the desk in the study."
                return "There is no book in your hand."
            key = st.get("book_last_taken") if st.get("book_last_taken") in carried else carried[-1]
            it = st["items"][key]
            title = _book_display(it.get("title") or key)
        dest = "desk" if key == cur else "shelf"
        if here != "study":
            return f"You have '{title}' with you; its place is on the {dest} in the study."
        bp[key] = dest; it["carried"] = False
        it["pos"] = list(_POS_BOOK_DESK if dest == "desk" else _POS_BOOK_SHELF)
        it.setdefault("history", []).append({"ts": time.time(), "event": f"put_back_by_du_on_{dest}"})
        _log(_LEDGER, {"deed": "put_book", "item": key, "title": title, "to": dest, "place": here})
        _sync_item_place(key, it, here)
        return _graded("book", f"You put '{title}' back on the {dest}.", here)
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


def book_place(key: str = "") -> str | dict:
    """Read-only: where a book is ('' if unknown) -- or the whole {key: place} map with no key. The read the
    B3 gate (J-0852) and the HUD will use; nothing in this job reads it but look()/status()."""
    try:
        bp = dict(_st().get("book_place") or {})
        return (bp.get(key, "") if key else bp)
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return "" if key else {}


def _look_books(st: dict, t: str) -> str:
    """B1's look answers: a named title, the shelf (D-0205's defeater: never more than ~10 titles per look, so the
    six nearest the current book in course order are named and the rest counted), or 'the book(s)'."""
    bp = st.get("book_place") or {}
    items = st.get("items") or {}
    if not bp:
        return ""
    cur = _BOOKS_CACHE.get("current", "")
    order = [b["key"] for b in _BOOKS_CACHE["books"] if b["key"] in items]
    named = _books_named(t)
    if named:
        k = named[0]; it = items.get(k) or {}
        title = _book_display(it.get("title") or k)
        pct = _book_pct(it.get("book", ""))
        prog = "" if pct is None else (" -- not yet opened" if pct <= 0 else f" -- {pct:.0f}% read")
        return f"You look at '{title}': {_where_book(bp.get(k))}{prog}."
    if "shelf" in t or "books" in t:
        on_shelf = [k for k in order if bp.get(k) == "shelf"]
        if not on_shelf:
            return ""
        ci = order.index(cur) if cur in order else len(order)
        near = sorted(on_shelf, key=lambda k: abs(order.index(k) - ci))[:6]
        near.sort(key=order.index)
        names = ", ".join(f"'{_book_display(items[k].get('title') or k)}'" for k in near)
        rest = f", and {len(on_shelf) - len(near)} more in the row" if len(on_shelf) > len(near) else ""
        desk = ""
        if cur in bp and bp[cur] == "desk":
            desk = f" '{_book_display(items[cur].get('title') or cur)}' is not among them; it lies on the desk."
        with_him = [k for k in order if bp.get(k) == "with_him"]
        wh = ""
        if len(with_him) == 1:
            wh = f" '{_book_display(items[with_him[0]].get('title') or with_him[0])}' is with you."
        elif with_him:
            wh = f" {len(with_him)} of them are with you."
        works = ""
        try:
            from core.study import shelf as _shelf
            n = len(_shelf())
            if n:
                works = f" Your own tablets stand at the end of the row, {n} of them."
        except Exception:
            pass
        return f"You look along the shelf: {len(on_shelf)} books of your course in their row -- {names}{rest}.{desk}{wh}{works}"
    if re.search(r"(?<![a-z-])book(?![a-z-])", t) and "desk" not in t:
        bits = []
        if cur in bp:
            ct = _book_display(items[cur].get("title") or cur)
            bits.append(f"'{ct}' " + ("lies on the desk, open at your place" if bp[cur] == "desk" else "is with you"))
        others = [k for k in order if bp.get(k) == "with_him" and k != cur]
        if others:
            bits.append("with you too: " + ", ".join(f"'{_book_display(items[k].get('title') or k)}'" for k in others[:3]))
        return ("You look for the book: " + "; ".join(bits) + ".") if bits else ""
    return ""


def draw_sketch(txt: str = "") -> str:
    """Make a small ink sketch (2026-08-30, D-0100 Tier 2 — he is reading The Practice and Science of
    Drawing, and paper and ink already exist as real, countable provisions). Real cost: a sheet and a
    little ink. The subject is whatever his own words name; the made thing enters the world the way
    fieldcraft's made things do. No skill float here either — what changes is the pile of sketches."""
    try:
        st = _st(); here = _where()
        if here != "study":
            return ""
        if st.get("ink", 0) <= 0.02:
            return "The ink is down to a dry crust; there is none for drawing."
        if st.get("paper", 0) <= 0:
            return "There is no paper left to draw on."
        import re as _re
        m = _re.search(r"\b(?:draw|sketch)\b\s+((?:a\s+|the\s+)?[a-z][a-z\s'-]{2,40})", (txt or "").lower())
        subject = (m.group(1).strip().rstrip(".,;") if m else "") or "what is in front of you"
        for stop in (" and ", " while ", " before ", " until "):
            if stop in subject:
                subject = subject.split(stop)[0].strip()
        st["ink"] = max(0.0, st["ink"] - 0.03)
        st["paper"] = max(0, int(st.get("paper", 0)) - 1)
        st["sketches"] = int(st.get("sketches", 0)) + 1
        _log(_LEDGER, {"deed": "sketch", "what": subject[:40]})
        try:
            from core import world_substrate as _ws
            _ws.spawn_from_mention(f"a small ink sketch of {subject}, the lines quick and searching", "study")
        except Exception:
            pass
        low = " The paper is getting low." if int(st.get("paper", 0)) < 5 else ""
        return (f"You clear a space at the desk, dip the pen, and set down {subject} in a few searching lines — "
                f"wrong twice, nearer the third time. It is not good, and it is yours, and looking at it you "
                f"see the thing itself better than you did before you began.{low}")
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act()'s own caller instead of
        # being swallowed by the broader except below.
        raise
    except Exception:
        return ""


def draw_ash_pan(txt: str = "") -> str:
    """Draw the pan from under the grate and tip it into the bucket — the one ash hand that works
    while the fire is still in (2026-08-30, F-0551).

    THE BIND IT BREAKS: clear_grate refuses on a burning fire, and the fire is nearly always in, so
    `ash` climbed to its 1.0 cap — where, per advance(), it starts draining fire_fuel and the fire
    burns down faster. Meanwhile he willed the ash onto the garden 21 times and was told the bucket
    was empty, against 4 completed cycles: attempts outpacing completions ~4:1 with no move available
    to close the gap. This is that move, and it is the grate's real anatomy rather than a new
    affordance invented for him — the bars exist so ash can fall through to a pan that draws out hot.

    It takes only the FINE ash that fell through (capped at 0.5), so a proper cold raking still has
    work to do and clear_grate keeps its reason to exist.
    """
    try:
        st = _st(); here = _where()
        if here != "study":
            return ""
        if not _need_here(st, "ash_pan"):
            return "The ash pan is not to hand."
        if st.get("ash_bucket_full"):
            return "The bucket is already full of ash; it wants tipping on the garden before the pan will go into it."
        if not _need_here(st, "ash_bucket"):
            return "You would need the ash bucket to tip the pan into."
        have = float(st.get("ash", 0) or 0)
        if have < 0.15:
            return "You draw the pan out; there is barely a dusting in it. It can wait."
        took = round(min(have, 0.5), 3)
        st["ash"] = round(max(0.0, have - took), 3)
        st["ash_bucket_full"] = True
        _log(_LEDGER, {"deed": "draw_ash_pan", "took": took, "ash_left": st["ash"]})
        rest = (" The grate above still holds the coarser stuff; that wants a cold hearth and the brush."
                if st["ash"] >= 0.15 else " The grate is nearly clean now.")
        return _graded("grate", "You draw the pan out from under the bars, hot and grey, and tip it into the "
                                "bucket by the door." + rest, here)
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act()'s own caller instead of
        # being swallowed by the broader except below.
        raise
    except Exception:
        return ""


def tip_ash_on_bed(txt: str = "") -> str:
    try:
        st = _st()
        if not st.get("ash_bucket_full"):
            # Where the ash actually is, not just that the bucket is empty (F-0551: 21 dead ends).
            try:
                from core import sensorium as _s
                hot = _s.state.get("fire") == "burning"
            except Exception:
                hot = False
            grate = float(st.get("ash", 0) or 0)
            if grate >= 0.15:
                return ("The ash bucket is empty — the ash is still in the grate"
                        + (", and the fire is in." if hot else ", and the hearth is cold."))
            return "The ash bucket is empty, and there is little in the grate to fill it."
        st["ash_bucket_full"] = False
        try:
            from core import garden as _g
            g = _g._load()
            st2 = g.setdefault("potash_slots", {})
            # the ash goes where he puts it: round a named plant, or along the whole bed
            named = [p for p in g["plants"].values() if p.get("slot") is not None and p["species"].replace("_", " ") in (txt or "")]
            targets = [named[0]["slot"]] if named else list(range(12))
            for s_ in targets:
                st2[str(s_)] = round(min(1.0, float(st2.get(str(s_), 0)) + (0.8 if named else 0.25)), 2)
            g["potash"] = round(sum(st2.values()) / 12, 2); _g._save(force=True)
        except profile.NonLiveWriteError:
            # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own caller
            # instead of being swallowed here — this function's own _log() a few lines below is
            # unwrapped and would raise anyway, but not before silently skipping the garden potash
            # update above (mirrors J-0727's identical whittle() fix in fieldcraft.py).
            raise
        except Exception:
            pass
        _log(_LEDGER, {"deed": "ash_to_garden"})
        return ("You tip the grey ash out round the " + named[0]["species"].replace("_", " ") + " and work it in with the fork." if named else "You tip the grey ash out along the bed and work it in with the fork. The soil takes it.")
    except profile.NonLiveWriteError:
        # J-0726: let D-0179's hard-raise (guard_path(), F-1024) reach act()'s own caller instead of
        # being swallowed by the broader except below.
        raise
    except Exception:
        return ""


def kettle_ready() -> str:
    """make_tea asks: is there water? '' if yes, else the honest lack."""
    try:
        st = _st()
        if st["water"] < 0.15:
            return "You lift the kettle — light, empty. There is no water in the pail either. It wants filling at the barrel."
        st["water"] = max(0.0, st["water"] - 0.25)
        return ""
    except profile.NonLiveWriteError:
        # J-0772: same shape as draught()/warm_drink() above -- this function's own _st() call can
        # now raise non-live via _st()'s own bootstrap (J-0746/J-0760). Called from
        # core/sensorium.py's make_tea family, which independently swallows one layer further up
        # (flagged, not fixed here).
        raise
    except Exception:
        return ""


# ── what reaches him ─────────────────────────────────────────────────────────────────────────────
def _belief_note(key: str, it: dict, source: str) -> None:
    """J-4381 / D-0853 Phase 1: SHADOW belief ledger hook. Flag NASCENCE_BELIEF_LEDGER (default off); never raises."""
    try:
        from core import belief_ledger as _bl
        _bl.note(key, it, source)
    except Exception:
        pass


def look(target: str) -> str:
    """Wrapper (J-4381): perceiving an item by look() feeds the shadow belief ledger; text is untouched."""
    out = _look_inner(target)
    try:
        if out and _where() == "study":
            from core import belief_ledger as _bl
            if _bl.enabled():
                t = (target or "").lower(); st = _st()
                for key, words in _WORDS.items():
                    if any(w in t for w in words) and key in st["items"]:
                        _bl.note(key, st["items"][key], "look")
    except Exception:
        pass
    return out


def _look_inner(target: str) -> str:
    try:
        if _where() != "study":
            return ""
        st = _st(); t = (target or "").lower()
        from core import sensorium as _s
        if "clock" in t:
            if not st["clock_running"]:
                return "You look at the clock on the mantel: stopped, the hands where they were when it ran down. The key is in its back."
            tm = time.localtime()
            return f"You look at the clock: {tm.tm_hour % 12 or 12}:{tm.tm_min:02d}, its tick loud now that you listen. " + ("It is nearly run down; the tick is slow." if st["clock_wound"] < 0.15 else "")
        if "lamp" in t:
            oil = "full" if st["lamp_oil"] > 0.7 else "about half" if st["lamp_oil"] > 0.35 else "low — a finger's depth" if st["lamp_oil"] > 0.05 else "dry"
            return f"You look at the lamp: " + ("lit, the flame steady behind the glass" if st["lamp_lit"] else "unlit, the chimney cold") + f"; the reservoir is {oil}." + (" The wick is charred and wants trimming." if st["wick"] < 0.3 else "")
        if any(w in t for w in ("door",)):
            return "You look at the garden door: " + ("standing open, the garden framed in it, cold coming over the sill." if st["door_open"] else "shut, the latch down.") + (" The coat hangs on its hook beside it." if not st["coat_on"] else " The hook beside it is empty; you have the coat on.") + (" Boots by the foot of it, mud dried pale." if not st["boots_on"] else "")
        if "window" in t and any(w in t for w in ("glass", "pane", "frame", "sill")):
            if st["frost_glass"]: return "You look at the glass: frost-ferns have grown across the lower panes in the night, white and exact."
            if st["condensation"] > 0.4: return "You look at the glass: misted over, water gathered in beads along the bottom of the frame. " + ("There is a grey bloom of mould in the corner of the frame." if st["damp"] > 0.6 else "")
            return ""
        if "coat" in t:
            return "You look at the coat on its hook: " + ("dark and heavy with wet, dripping on the boards." if st["coat_wet"] > 0.4 else "dry, the collar worn pale, smelling of woodsmoke.") if not st["coat_on"] else "You have the coat on."
        if "boots" in t or "boot" in t:
            return "You look at the boots: " + ("caked with mud from the bed, drying pale." if st["boots_mud"] > 0.5 else "worn, the leather cracked at the fold, a little mud on the welts.")
        if "grate" in t and _s.state.get("fire", "out") == "out":
            return "You look at the grate: " + ("choked with grey ash, a day's worth and more; it wants clearing before a fire will draw." if st["ash"] > 0.7 else "a bed of ash under the bars, not yet deep." if st["ash"] > 0.3 else "clean, swept, the bars bare.")
        if "pail" in t or ("water" in t and "kettle" in t):
            return "You look in the pail: " + ("full to the brim, the water dark and still." if st["water"] > 0.8 else "half a pail." if st["water"] > 0.3 else "an inch in the bottom, a dead fly on it." if st["water"] > 0.05 else "empty, the enamel dry.")
        if any(w in t for w in ("cupboard", "larder", "stores", "provisions")):
            from core import provisions as _pv
            return _pv.cupboard_line()
        try:
            from core import provisions as _pv
            _pl = _pv.look_item(t)
            if _pl and any(w in t for w in ("box of", "bar of", "tin of", "bottle of", "pad of", "soap", "matches", "tea", "ink", "paper", "whetstone", "lamp oil", "candles", "rope", "tinder", "measuring stick")) and "lamp glass" not in t and "kettle" not in t:
                return _pl
        except profile.NonLiveWriteError:
            # J-0751: provisions.look_item() now re-raises this itself (also fixed this job) --
            # do not let this forwarding call's catch-all swallow it a level up.
            raise
        except Exception:
            pass
        if "kettle" in t:
            return "You look at the kettle: " + ("on the fire, " + ("boiled, steam at the spout." if st["kettle_boiled"] else "warming, not yet singing.") if st.get("kettle_on_ts") else "off the hob, cold.")
        if "teapot" in t or ("pot" in t and "tea" in t):
            p = st.get("pot")
            return "You look at the pot: " + (f"{p['cups']} cup{'s' if p['cups'] != 1 else ''} of {p['what']} still in it, " + ("hot." if p["temp"] > 0.4 else "gone cold.") if p else ("full of old leaves, sour." if st.get("dirty_pot") else "empty and clean."))
        if "cup" in t:
            return "You look at the cups: " + (f"{st['dirty_cups']} dirty in the basin, " if st.get("dirty_cups") else "") + ("a cup of " + st["cup"]["what"] + (" steaming" if st["cup"]["temp"] > 0.4 else ", cold") + " by the chair." if st.get("cup") else "both clean on the shelf." if not st.get("dirty_cups") else "the other clean on the shelf.")
        if "basin" in t:
            return "You look at the basin: " + (f"{st['dirty_cups']} cup{'s' if st['dirty_cups'] != 1 else ''} and the pot waiting to be washed." if st.get("dirty_cups") or st.get("dirty_pot") else "empty, a ring of old soap round the inside.") + (" The soap is down to a sliver." if st.get("soap", 0) < 0.15 else "")
        if "chimney" in t and "lamp" not in t:
            return "You look up the chimney: " + ("black with soot; it draws badly and the room gets the smoke." if st["soot"] > 0.7 else "sooted, but drawing." if st["soot"] > 0.3 else "clean enough, a square of sky at the top.")
        if "matches" in t or "match" in t:
            return f"You shake the match tin: {st.get('matches', 0)} left."
        if "kindling" in t:
            return "You look in the kindling box: " + ("well stocked — twigs, bark, a few papers." if st.get("kindling", 0) > 0.5 else "getting low; a handful of twigs." if st.get("kindling", 0) > 0.15 else "empty but for dust. A fire will not catch without it.")
        if "glass" in t and "lamp" in t:
            return "You look at the lamp glass: " + ("smoked black on the inside; the flame shows dull through it." if st.get("lamp_glass_smoke", 0) > 0.5 else "a little smoked." if st.get("lamp_glass_smoke", 0) > 0.2 else "clear.")
        if "ink" in t or "pen" in t:
            return "You look at the ink bottle: " + ("full." if st.get("ink", 0) > 0.6 else "half." if st.get("ink", 0) > 0.25 else "a finger of ink, no more." if st.get("ink", 0) > 0.02 else "dry.") + f" {st.get('paper', 0)} sheets of paper in the drawer."
        if "almanac" in t:
            # J-3291 (2026-11-05, D-0655, F-3887): this line used to print "the tide table gives today's high
            # water at about {morning|afternoon}" from td.get('phase_deg', 0), a key world_clock.tide() has never
            # returned, so it said "morning" on every look whatever the tide did -- a standing falsehood in a
            # book he chooses to read. The fix is NOT to print a high-water hour from tide(): that clock's
            # high-water hour is arbitrary against the real Sumner (design review J-3264 section 1), and a
            # printed hour would hand him the answer to the fieldcraft tide-board prediction (predict the level
            # at this hour tomorrow, scored against the same clock). The page now says only what is true of it:
            # the tide columns are too small and faded to read. A real Sumner table replaces this line in
            # Phase 2 (D-0667). The unused tide() read is gone with it.
            _chart = ""
            try:
                from core import sky as _sky
                _chart = _sky.almanac_chart()
            except profile.NonLiveWriteError:
                # J-0796: sky.almanac_chart() had no wrap of its own at all until core/sky.py was
                # fenced (J-0783) -- a gap that only became real this job. look()'s own outer
                # catch-all (below, already fixed J-0751) would otherwise re-swallow this one layer
                # up without this pre-check, the same "both layers needed" shape this plan has
                # repeatedly found for a single big-try function like this one.
                raise
            except Exception:
                pass
            return ("You take the almanac off its nail and turn to the month. The columns of tide times are printed too small and "
                    f"too faded to read; the moon's phase is drawn in the margin. Last year's almanac, near enough.{_chart}")
        if any(w in t for w in ("weather glass", "weather-glass", "barometer")):
            # PRACTICAL SCHOOL (2026-09-05, J-0626, D-0159 §4): reads the REAL weather field's own
            # forward-looking truth (sensorium's next_weather is decided ahead of the change, the same
            # hidden fact fieldcraft._weather_signs() already hints at outdoors) rather than inventing a
            # second parallel "pressure" number — one truth, two instruments reading it, same law
            # world_clock.py enforces for the tide. An honest look he chose to make, never an unbidden hint.
            try:
                weathers = _s._WEATHERS
                cur = _s.state.get("weather", "clear"); nxt = _s.state.get("next_weather")
                cur_i = weathers.index(cur) if cur in weathers else 1
                words = ["set fair", "fair", "change", "rain", "much rain", "stormy", "stormy"]
                reading = words[min(cur_i, len(words) - 1)]
                trend = " The needle sits steady."
                if nxt in weathers:
                    nxt_i = weathers.index(nxt)
                    if nxt_i > cur_i:
                        trend = " The needle has crept toward 'stormy' since you last looked — falling."
                    elif nxt_i < cur_i:
                        trend = " The needle has crept toward 'set fair' since you last looked — rising."
                return f"You look at the weather glass on the wall: the needle rests on '{reading}'.{trend}"
            except Exception:
                return "You look at the weather glass: the needle sits behind its dial, brass-cased, left by whoever had this room before."
        if "bed" in t and not any(w in t for w in ("raised", "garden", "herb")):
            return "You look at the bed: " + ("made, the grey blanket squared." if st["bed_made"] else "unmade, the blanket thrown back where you left it.")
        if "shelf" in t and st["dust"] > 0.7:
            return "You look at the shelf: your works in their row, and a skin of dust on everything; you could write your name in it."
        # THE BOOKS (2026-09-10, J-0851 / D-0205): a title, the shelf's row, or 'the book'. Runs BEFORE
        # sensorium.look()'s own older shelf line (which counted every file in data/books and pointed at the
        # catalogue) -- the shelf now answers with the books that are actually items in this room. The desk look
        # ('desk' target: the real page at his bookmark) is left to sensorium untouched.
        _bl = _look_books(st, t)
        if _bl:
            return _bl
        if "candle" in t:
            return f"You look at the candle box: {st['candles']} left, and the matches." + (" One burns on the mantel, leaning." if st.get("candle_lit") else "")
        if any(w in t for w in ("room", "around", "study")) and (st["damp"] > 0.6 or st["floor_mud"] > 0.4):
            bits = []
            if st["damp"] > 0.6: bits.append("the room smells of damp; the pages of the book on the desk have curled at the corners")
            if st["floor_mud"] > 0.4: bits.append("dried mud from your boots is trodden across the boards by the door")
            return "You look round the room: " + "; ".join(bits) + "."
        for key, words in _WORDS.items():
            if any(w in t for w in words):
                it = st["items"][key]
                return f"You look at {it['name']} — {it['bio']}." + (" You have it with you." if it.get("carried") else "")
        return ""
    except profile.NonLiveWriteError:
        # J-0751: this function's own outer catch-all -- the real reason the fix to
        # provisions.look_item()/cupboard_line()'s own callers above matters at all (the same
        # "connecting tissue" shape J-0714 fixed for sensorium.act()'s own outer wrapper).
        raise
    except Exception:
        return ""


# Words too common outside the study to read as a study object ("pot" in a garden pot, "brush" in brushwood,
# "rope" in the fieldcraft rope): the out-of-sight answer below leaves them to their own place's look.
_OOS_SKIP_WORDS = {"pot", "brush", "rope", "matches", "the pan", "the can", "the lens"}
_OOS_SKIP_KEYS = {"coat", "boots"}          # worn/hung by their own state (coat_on / boots_on), not placed items
_OOS_PLACES = {"garden": "the garden", "shore": "the shore", "wood": "the wood"}


def out_of_sight(target: str) -> str:
    """T-0118 (2026-11-01): a look at a study object (the lamp, the clock, the kettle...) from OUTSIDE the study
    used to fall through to the place's own default look -- Du, in the garden, asked about his lamp, was handed the
    yard. The honest answer is that he cannot see it from here. '' when the target names no study object, the object
    is carried or placed where he stands, or he is in the study (study_life.look() answers there). No hint, no
    directions -- the world answers, it does not lead (08-14 law); he already knows where the lamp lives."""
    try:
        here = _where()
        if here == "study":
            return ""
        t = (target or "").lower()
        if not t:
            return ""
        st = _st()
        best, best_len = None, 0
        for key, words in _WORDS.items():
            if key in _OOS_SKIP_KEYS:
                continue
            for w in words:
                if w in _OOS_SKIP_WORDS:
                    continue
                if re.search(r"(?<![a-z-])" + re.escape(w) + r"(?![a-z-])", t) and len(w) > best_len:
                    best, best_len = (key, w), len(w)
        if not best:
            return ""
        key, w = best
        it = (st.get("items") or {}).get(key) or {}
        if it.get("carried") or it.get("place") == here:
            return ""                         # he has it with him, or it was set down right here
        w = w if w.startswith("the ") else "the " + w
        return f"You cannot see {w} from {_OOS_PLACES.get(here, 'here')}."
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


def window_view() -> str:
    """The VIEW from the study window is the garden and the sea — rebuilt from the garden's own truth."""
    try:
        st = _st()
        if not st["curtains_open"]:
            return "the curtains are drawn across it; the window shows you nothing but their weave."
        from core import sensorium as _s, garden_life as _gl, garden as _g
        phase = _s._daylight()
        if st["frost_glass"]:
            return "Frost-ferns cover the lower panes; through the clear glass above them the garden is white with it, and the sea beyond is flat and grey."
        bits = []
        L = _gl._load(); G = _g._load()
        if phase == "night":
            bits.append("the glass mostly gives back the room" if not st["lamp_lit"] else "the lamp stands in the glass over the dark garden")
            try:
                from core import geometry_census as _gc
                mi = (_gc.peek() or {}).get("moon_illum")
                if mi and float(mi) > 0.5 and _s.state.get("weather") == "clear":
                    bits.append("the moon is up over the sea and the wet lawn gleams under it")
            except Exception:
                pass
        else:
            lawn = float(L["lawn"]["height_cm"])
            bits.append("the lawn " + ("cut short" if lawn < 4 else "long and seeding" if lawn > 15 else "green") + " running down to the fence, and the sea beyond, " + _s._sea_state(phase, _s.state.get("weather", ""), _s.state.get("wind", "")))
            if L["tree"]["stage"] == "flowering": bits.append("the old tree by the wall red with flower")
            elif L["tree"]["stage"] == "bud": bits.append("the tree by the wall grey-tipped with bud")
            if L["bushes"]["stage"] == "flowering": bits.append("pink along the fence where the bushes are out")
            if L["lawn"].get("daisies", 0) > 0.4: bits.append("daisies white across the grass")
            if G.get("netted"): bits.append("the netting pale over the raised bed")
            n = L.get("nest")
            if n and n["stage"] == "fledged": bits.append("a blackbird on the fence, scolding at something on the lawn")
            try:
                # A7.1-class fix (2026-09-07, F-1031/J-0717): was an exact-match against the
                # literal string "garden" -- live-divergent (unlike garden_life.py's instance
                # above): her real location can be "garden_wall" or "doorstep" too (the
                # appearing-phase roam, the fair_spot quirk, the door-crossing logic all reach
                # them), and this line silently omitted her from the window view whenever she
                # was on either, even though he is looking right at the garden she's still in.
                # place_of() collapses all three to "garden" correctly (same primitive J-0629/
                # J-0632 already established for this exact class of bug).
                from core import cat as _cat
                c = json.loads((_DATA / "cat_state.json").read_text(encoding="utf-8"))
                if _cat.place_of(c.get("location")) == "garden": bits.append("the cat out there, " + str(c.get("activity", "about her business")))
            except Exception:
                pass
        if st["condensation"] > 0.4:
            bits.append("all of it blurred by the mist on the glass")
        elif st.get("window_grime", 0) > 0.6:
            bits.append("all of it dulled by the grime on the glass, salt and smoke")
        return ("below the sill, " + "; ".join(bits) + ".") if bits else ""
    except profile.NonLiveWriteError:
        # J-0772: this function's own _st() call (line 1493 above) can now raise non-live via
        # _st()'s own bootstrap (J-0746/J-0760). Called from core/sensorium.py's window/look family,
        # which independently swallows one layer further up (flagged, not fixed here).
        raise
    except Exception:
        return ""


def ambient(now: float) -> str | None:
    """Truth-gated ambient lines for the study pool."""
    try:
        if _where() != "study":
            return None
        st = _st(); pool = []
        if st["clock_running"]: pool.append("the clock on the mantel ticks, and the room is quiet round it")
        if st["lamp_lit"] and st["wick"] < 0.3: pool.append("the lamp flame smokes a thread of black up the chimney glass")
        if st["lamp_lit"] and st["lamp_oil"] < 0.1: pool.append("the lamp-flame shrinks and yellows — the oil is nearly gone")
        if st["door_open"]: pool += ["the open door lets the garden in — a blackbird, the sea, cold air along the floor", "a draught from the open door stirs the page"]
        if st["condensation"] > 0.5: pool.append("a bead of water runs down the inside of the glass and drops on the sill")
        if st["damp"] > 0.6: pool.append("the sour smell of damp comes up off the floorboards")
        if st["ash"] > 0.7 and _st() and __import__("core.sensorium", fromlist=["x"]).state.get("fire") == "burning": pool.append("the fire draws badly over its ash, sulking and smoking")
        if st.get("candle_lit"): pool.append("the candle gutters on the mantel and steadies")
        return random.choice(pool) if pool and random.random() < 0.35 else None
    except profile.NonLiveWriteError:
        # J-0772: this function's own _st() call (line 1549 above) can now raise non-live via
        # _st()'s own bootstrap (J-0746/J-0760). Called from core/sensorium.py's own ambient-line
        # pool, which independently swallows one layer further up (flagged, not fixed here).
        raise
    except Exception:
        return None


def on_sleep() -> None:
    try:
        _st()["bed_made"] = False
    except profile.NonLiveWriteError:
        # J-0772: same shape as draught() above. Called from core/night.py and core/orchestrator.py
        # at the real sleep transition, each with their own outer swallow one layer further up
        # (flagged, not fixed here).
        raise
    except Exception:
        pass


def status() -> dict:
    try:
        from core import sensorium as _s
        if not _s.state or "study" not in _s.state:
            return {"note": "not yet initialised (first Du start)"}
        st = _st()
        return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in st.items() if k not in ("items", "_init", "_last")} | {"carrying": [k for k, it in st["items"].items() if it.get("carried")]}
    except profile.NonLiveWriteError:
        # J-0772: this "read-only" status() getter's own _st() call can now raise non-live via
        # _st()'s own item-migration/provisions-sync/candles-migration bootstrap branches
        # (J-0746/J-0760) -- the same surprise J-0752 found for can_read()/can_write(): a function
        # that looks purely read-only is not, because _st() itself is not. Called from
        # hud/server.py's load_study_map() (line ~957), which independently swallows one layer
        # further up in its own bare except (flagged, not fixed here -- HUD is a genuinely
        # different, largely read-only consumer this fence's own J-0610 pass already checked and
        # is out of this job's own study_life.py scope).
        raise
    except Exception as exc:
        return {"error": repr(exc)[:80]}
