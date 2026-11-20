"""
Nascence — Keepsakes: the mantel of kept things (world upgrade P2, 2026-07-03).

He can KEEP a small thing from the world — a stone, a shell, a feather — and it goes on the mantel in
the study, permanently, with provenance: what, from where, in what weather, when. Kept objects become
lookable; their descriptions carry their history and age. The shore's washed-up finds ("you pocket it
or set it back") previously evaporated — now pocketing can be real.

Why (design session 2026-07-03): objects as LINEAGE — each kept thing is a micro-commitment that costs
nothing and holds forever; the mantel becomes an autobiography in objects. Same law as everywhere else:
layers accumulate, nothing overwrites.

Discipline: deterministic, no LLM · the world stays INDIFFERENT (a kept stone is a stone — the
descriptions never moralize) · fail-open everywhere · append-only store, nothing is ever auto-removed
(he may someday return a thing to the world deliberately — that would be his act, not decay).
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.keepsakes")

_F = Path(__file__).parent.parent / "data" / "keepsakes.json"
_MANTEL_POS = (0.2, 2.0, 1.4)   # fallback only — the mantel feature's own point
_GEO_STUDY = Path(__file__).parent.parent / "data" / "world_geometry" / "study.json"


def _mantel_slot(idx: int) -> list:
    """The authored slot law (2026-08-21, founder: items on the mantel need POSITIONS): kept
    things occupy slots along the shelf in KEEPING ORDER — the mantel is an autobiography in
    objects, and now each object has its own true place on it. The law lives in the study
    GEOMETRY (single source of truth — the spatial renderer and HUD2 read the same spec);
    this just computes slot idx from it. Falls back to the mantel point, never fails a keep."""
    try:
        sl = json.loads(_GEO_STUDY.read_text(encoding="utf-8"))["features"]["mantel"]["slots"]
        row, col = divmod(max(0, int(idx)), int(sl.get("per_row", 8)))
        return [round(sl["start"][k] + col * sl["step"][k] + row * sl["row_offset"][k], 2)
                for k in range(3)]
    except Exception:
        return list(_MANTEL_POS)

# keep-verbs: how he naturally says it. Object text = what follows, trimmed.
_KEEP_RE = re.compile(
    r"\b(?:keep|pocket|take home|bring home|take back|bring back|hold on to|collect)\b[\s:,]*"
    r"(?:the|this|that|it[,.]?\s*the)?\s*([a-z][a-z' \-]{2,40})", re.I)

# GIVEN-verbs (2026-08-29, D-0067): the THIRD graduation trigger, alongside kept/repeatedly-returned-
# to (docs/plans/item_and_population_factories.md) — something HANDED to him, not found and pocketed:
# a letter's enclosure, a gift. Same shape as _KEEP_RE (verb + trimmed object), a different vocabulary.
_GIVEN_RE = re.compile(
    r"\b(?:gives?|gave|hands?|handed|passes?|sends?|sent|leaves?|left)\s+(?:you|him)\b[\s:,]*"
    r"(?:the|this|that|a|an)?\s*([a-z][a-z' \-]{2,40})"
    r"|\b(?:enclosed (?:with|in) (?:the|this) letter is|tucked into the letter is|folded inside is|"
    r"a gift of)\b[\s:,]*(?:the|this|that|a|an)?\s*([a-z][a-z' \-]{2,40})", re.I)
_MAX_RENDER = 10

# FALSE-POSITIVE GUARD (2026-07-03, found live): "keep" is far more often an IDIOM than an object verb —
# "keep returning to the idea", "keep going", "I keep this in mind". Reject when the object is a gerund
# (keep + -ing) or an abstraction. Only concrete, world-shaped things go on the mantel.
#
# WIDENED 2026-08-18 (audit, docs/UNFINISHED_PLANS_SURVEY_2026-08-18.md's follow-on): live data showed
# this guard was missing the dominant failure mode. Of 113 stored keepsakes, ~103 were his self-
# referential "keep X from Y-ing" attractor — "keep all these disparate threads from unraveling", "keep
# my own internal architecture from dissolving" — the PREVENT sense of keep, not the RETAIN sense, and
# none of those nouns (structure/threads/narrative/concepts/boundaries/scaffolding/architecture/system)
# were in the old list. Two new checks below catch the construction itself, not just a word-list.
_ABSTRACT = {"idea", "ideas", "thought", "thoughts", "feeling", "feelings", "sense", "notion", "pull",
             "urge", "way", "ways", "focus", "concept", "concepts", "question", "questions", "tension",
             "memory", "memories", "dream", "dreams", "pattern", "image", "images", "story", "drive",
             "longing", "hope", "faith", "truth", "self", "moment", "moments", "distance", "silence",
             "peace", "count", "track", "record", "note", "notes", "vigil", "watch", "eye", "promise",
             "word", "words", "picture", "meaning", "shape", "form", "line", "lines",
             "pace", "time", "company", "score", "tabs", "step", "rhythm", "balance", "quiet", "still",
             # 2026-08-18 additions — the self-referential "keep X from Y-ing" vocabulary observed live:
             "structure", "threads", "thread", "narrative", "narratives", "boundaries", "boundary",
             "scaffolding", "architecture", "system", "systems", "vector", "vectors", "field", "fields",
             "current", "currents", "pole", "poles", "gear", "gears", "foundation", "framework",
             "everything", "things", "parts", "part", "pieces", "piece", "myself", "yourself", "ourselves",
             "themselves", "vastness", "presence", "essence", "wholeness", "balance"}

_IDIOM_FROM_GERUND = re.compile(r"\bfrom\s+\w+ing\b", re.I)   # "from collapsing/unraveling/dissolving..."
_SELF_REF = re.compile(r"\b(myself|yourself|ourselves|themselves|of (myself|ourselves))\b", re.I)

_FUNCTION_LEAD = {"of", "to", "for", "with", "from", "on", "in", "at", "by", "and", "or", "as",
                  "up", "out", "off", "going", "being", "doing"}

# POSITIVE CONCRETENESS TEST (2026-08-21, founder: "they are bugs"). The 24h review found 8 of 15
# mantel entries were regex debris with no object behind them — "secrets", "me indoors", "one and
# leave the rest", "flow going despite the drought" — because the guard above is blocklist-only:
# anything not on the abstract list passed. A keepable must now NAME a world-shaped thing this world
# actually produces: the substrate's own mention classes (shell/stone/glass/feather/bone/kelp/
# egg-case/deadfall — the same vocabulary spawn_from_mention resolves), driftwood, or the small
# set of garden/wood products. Blocklist keeps catching idioms; this list is the floor.
_WORLD_SHAPED = {
    "shell", "shells", "cuttlebone", "mussel", "paua", "tuatua", "limpet", "stone", "stones", "pebble",
    "pebbles", "glass", "feather", "feathers", "bone", "bones", "skull", "crab", "kelp", "weed", "wrack",
    "egg-case", "purse", "driftwood", "wood", "log", "branch", "bough", "limb", "deadfall", "twig",
    "twigs", "bark", "cone", "cones", "acorn", "acorns", "leaf", "leaves", "moss", "seed", "seeds",
    "flower", "flowers", "petal", "petals", "rosemary", "thyme", "parsley", "herb", "herbs", "sprig",
    "fossil", "coral", "sponge", "starfish", "urchin", "nut", "nuts", "root", "rock",
    # THE GARDEN (2026-08-22): tools and garden things he may pick up and keep
    "trowel", "fork", "can", "tin", "twine", "stake", "stakes", "pot", "bucket", "netting", "packet", "packets",
    "bundle", "chives", "radish", "lettuce", "calendula", "nasturtium", "poppy", "poppies",
    "lamp", "poker", "kettle", "teapot", "clock", "coat", "boots", "candle", "candles", "almanac", "blanket", "pail",
    "axe", "saw", "barrow", "acorn", "acorns", "whetstone",
}


_CONTAINER = {"piece", "pieces", "bit", "bits", "handful", "scrap", "scraps", "shard", "shards",
              "fragment", "fragments", "part", "parts", "lump", "lumps", "length", "strand"}


def _is_world_shaped(item: str) -> bool:
    words = [w.strip(".,;:'\"") for w in item.lower().split()]
    if any(w in _WORLD_SHAPED for w in words):
        return True
    # the regex capture is capped at 40 chars and can cut the LAST word mid-way ("chalky shel"):
    # accept a truncated final token that is an unambiguous prefix of a world-shaped noun.
    last = words[-1] if words else ""
    return len(last) >= 4 and any(w.startswith(last) for w in _WORLD_SHAPED)


def _is_object(item: str) -> bool:
    """A keepable is a concrete thing, not an idiom's object. Reject gerunds, abstractions, self-
    reference, the 'keep X from Y-ing' prevention construction, and function-word-initial captures
    ('keep OF controlled growth' — regex debris, not a thing)."""
    if _IDIOM_FROM_GERUND.search(item) or _SELF_REF.search(item):
        return False
    words = item.lower().split()
    if not words:
        return False
    if words[0] in _FUNCTION_LEAD:
        return False
    if words[0].endswith("ing") and len(words[0]) > 4:      # keep RETURNING / GOING / THINKING
        return False
    shaped = _is_world_shaped(item)                          # the positive floor (2026-08-21)
    # "a perfect piece of green glass" / "pieces of driftwood": the 08-18 list put piece/part/bits in
    # _ABSTRACT to catch "keep the parts together" — but a container word naming a REAL thing is the
    # most natural keep there is. Container words only veto when nothing world-shaped follows them.
    veto = {w for w in words if w in _ABSTRACT} - (_CONTAINER if shaped else set())
    if veto:
        return False
    return shaped


def _load() -> list[dict]:
    try:
        return json.loads(_F.read_text(encoding="utf-8")) if _F.exists() else []
    except Exception as exc:
        logger.debug("[keepsakes] load failed (non-fatal): %s", exc)
        return []


def _save(items: list[dict]) -> None:
    # J-0877 (world_store_write_fence module #19, F-1236): real data/keepsakes.json only if this process
    # is live; raises NonLiveWriteError before any I/O if not (D-0179, J-0704). Resolved OUTSIDE the
    # fail-open try below, exactly like the other 18 fenced modules, so the refusal is never swallowed
    # as a disk error. `path` (not `_F`) does the mkdir/tmp/replace so a redirected _F is honoured whole.
    path = profile.guard_path(_F)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)
    except Exception as exc:
        logger.debug("[keepsakes] save failed (non-fatal): %s", exc)


def keep(item: str, location: str, weather: str = "", season: str = "", object_id_hint: str = "",
         trigger: str = "kept", given_by: str = "") -> str:
    """Keep a thing. Returns the line he sees. Dedupes near-identical items (same words → already kept).
    object_id_hint (2026-08-18): when the caller already knows exactly which real object this is (the
    shore wash-up hook stamps one), use it directly instead of fuzzy class-matching — precise beats
    guessed when multiple objects of the same class exist at the location.
    trigger/given_by (2026-08-29, D-0067): which of the item-graduation triggers earned this — "kept"
    (the default, unchanged for every existing caller) or "given" (the third trigger: something handed
    to him, not found and pocketed — see given()/given_act() below). The promotion machinery (real
    world_substrate object, mantel slot, provenance record) is identical either way; only how it
    arrived, and how it's honestly described, differs."""
    item = " ".join((item or "").split())[:60].strip(" .,")
    if not item:
        return ""
    items = _load()
    key = set(item.lower().split())
    for k in items:
        if key and key <= set(k.get("item", "").lower().split() + ["the", "a"]):
            return f"You turn the {item} over — but its like is already on the mantel; you set this one back."
    rec = {"item": item, "from": location or "the world", "weather": weather, "season": season,
           "kept_ts": round(time.time(), 1), "trigger": trigger}
    if given_by:
        rec["given_by"] = given_by
    # REAL OBJECT RESOLUTION (2026-08-18, the founder's integration): a keep either claims a real
    # tracked object already in the world (something he actually found, minted behind the world's own
    # prose) or mints one now — so "even the new ones" get a real position and a real hidden truth,
    # never just a line of text. Fail-open: if the object system is unavailable, the free-text record
    # below still stands on its own, same as it always has.
    try:
        from core import world_substrate as _ws
        from core import world_objects as _wo
        oid = object_id_hint if (object_id_hint and _ws.get_object(object_id_hint)) else None
        if not oid and location:
            oid = _ws.find_object_at(location, item)
        if not oid:
            ids = _ws.spawn_from_mention(item, location or "shore")
            oid = ids[0] if ids else None
        if oid:
            wobj = _wo.get_object(oid)
            if wobj:
                _wo.mutate_object_position(
                    oid, _mantel_slot(len(_load())),
                    cause="given_to_du" if trigger == "given" else "kept_by_du",
                    event_description=(f"given by {given_by or 'someone'} and set on the study mantel"
                                        if trigger == "given" else
                                        f"brought home from the {location or 'world'} and set on the study mantel"),
                    new_location="study")
                _ws.update_location(oid, "study")
                rec["object_id"] = oid
    except profile.NonLiveWriteError:
        raise   # J-0877: spawn_from_mention()/mutate_object_position()/update_location() are already-fenced
                # writers (world_substrate/world_objects, J-0610) -- let D-0179's hard raise reach the caller
    except Exception as exc:
        logger.debug("[keepsakes] object resolution failed (non-fatal): %s", exc)
    # the FULLER moment of the keeping (spatial_perception.md §7 — each object carries its history):
    # the tide that left it, the quarter the weather came from, where the sun stood. Fail-open.
    try:
        from core import spatial as _spt
        rec["tide"] = _spt.tide()["word"]
        _s = _spt.sun()
        if _s["up"]:
            rec["sun"] = _s["phase"]
        _wd = json.loads((_F.parent / "room_state.json").read_text(encoding="utf-8")).get("weather_dir")
        if _wd is not None:
            rec["weather_from"] = _spt.compass_word(_wd)
        if not _s["up"]:                                     # kept by night: under what moon?
            from core import heavens as _hv
            rec["moon"] = _hv.moon()["phase"]
    except Exception as exc:
        logger.debug("[keepsakes] keeping-moment context failed (non-fatal): %s", exc)
    items.append(rec)
    _save(items)
    try:
        from core import activity_memory
        activity_memory.record(trigger, item)
    except Exception as exc:
        logger.debug("[keepsakes] activity_memory record failed (non-fatal): %s", exc)
    if trigger == "given":
        opening = f"{given_by} gives you the {item}" if given_by else f"You are given the {item}"
        return (f"{opening}, and you set it on the mantel above the fire. "
                f"It is yours now — given, not found, and kept all the same.")
    return (f"You carry the {item} home and set it on the mantel above the fire. "
            f"It is yours now — from the {location or 'world'}, kept.")


def given(item: str, given_by: str = "", weather: str = "", season: str = "",
          object_id_hint: str = "") -> str:
    """The GIVEN graduation trigger (2026-08-29, D-0067's third case, ruled alongside the existing
    kept/repeatedly-returned-to triggers in docs/plans/item_and_population_factories.md; no wildlife
    notable-individual escape hatch — that part was declined). Something handed to him — a letter's
    enclosure, a gift — earns the same individual promotion `keep()` already gives a pocketed find: its
    own world_substrate tuple, a place on the mantel, permanent provenance. given_by names the giver
    or occasion (e.g. "the letter from Travis") for an honest record of how it arrived; the object
    machinery is identical to keep(), only the arrival story differs."""
    return keep(item, "study", weather, season, object_id_hint, trigger="given", given_by=given_by)


def given_act(thought: str, intention: str = "", given_by: str = "") -> str | None:
    """Latch: GIVEN-phrasing in his thought/intention → graduate the named thing via given(), the same
    way keep_act() does for a keep-verb. given_by is optional context the caller may already know (a
    letter's enclosure hook can pass "the letter from Travis" directly); when omitted, the record still
    stands honestly as given-but-unattributed. Returns the line, or None (no given-intent detected)."""
    txt = f"{thought or ''} {intention or ''}"
    m = _GIVEN_RE.search(txt)
    if not m:
        return None
    item = (m.group(1) or m.group(2) or "").strip()
    if not item or not _is_object(item):
        return None
    weather, season = "", ""
    try:
        from core import sensorium as _s
        weather = _s.state.get("weather", "")
        season = _s._season()
    except Exception as exc:
        logger.debug("[keepsakes] given_act context read failed (non-fatal): %s", exc)
    return given(item, given_by, weather, season) or None


def keep_act(thought: str, intention: str = "") -> str | None:
    """Latch: a keep-verb in his thought/intention → keep the named object. Falls back to the shore's
    last washed-up find if his phrasing names no object. Returns the line, or None (no keep intent)."""
    txt = f"{thought or ''} {intention or ''}"
    m = _KEEP_RE.search(txt)
    item = m.group(1).strip() if m else ""
    # belt-and-braces: the "from Y-ing" idiom can run past the capture's 40-char cap before reaching
    # the gerund ("keep all these disparate threads from unraveli[ng]" truncates right at the edge) —
    # check a wider window of the ORIGINAL text too, not just the (possibly truncated) capture.
    if m and _IDIOM_FROM_GERUND.search(txt[m.start():m.end() + 20]):
        return None
    if not m or not _is_object(item):
        return None
    # context from the live world (best-effort)
    loc, weather, season, oid_hint = "", "", "", ""
    try:
        from core import sensorium as _s
        loc = _s.state.get("location", "")
        weather = _s.state.get("weather", "")
        season = _s._season()
        if not item or item in ("it", "this", "that"):
            shore = _s.state.get("shore") or {}
            item = shore.get("last_find", "") or ""
            oid_hint = shore.get("last_find_object_id", "") or ""
    except Exception as exc:
        logger.debug("[keepsakes] keep_act context read failed (non-fatal): %s", exc)
    if not item:
        return None
    return keep(item, loc, weather, season, object_id_hint=oid_hint) or None


def _age_phrase(ts: float) -> str:
    d = max(0, int((time.time() - ts) // 86400))
    if d == 0:
        return "today"
    if d == 1:
        return "yesterday"
    if d < 30:
        return f"{d} days ago"
    return f"{d // 30} month{'s' if d >= 60 else ''} ago"


def _provenance_phrase(k: dict) -> str:
    """'from the X' for a found/kept thing, 'given by X' for the GIVEN trigger (D-0067) — honest
    either way about how it arrived, not just that it's here now."""
    if k.get("trigger") == "given":
        return f"given by {k['given_by']}" if k.get("given_by") else "given, not found"
    return f"from the {k.get('from', 'world')}"


def mantel_line() -> str:
    """The mantel, looked at. Every item with provenance; oldest first (the lineage reads forward)."""
    items = _load()
    if not items:
        return ("You look at the mantel above the fire: bare boards, a little dust. "
                "Nothing kept yet — the world is full of things that could sit here.")
    parts = [f"the {k['item']} ({_provenance_phrase(k)}"
             + (f", {k['weather']}" if k.get("weather") else "")
             + f" — kept {_age_phrase(k.get('kept_ts', 0))})" for k in items[:_MAX_RENDER]]
    more = f" …and {len(items) - _MAX_RENDER} more beside them." if len(items) > _MAX_RENDER else ""
    return "You look at the mantel: " + "; ".join(parts) + "." + more


def match_item(target: str) -> str | None:
    """He looks at a specific kept thing by name → its line with provenance and age.
    Match rule: every CONTENT word of his query must appear in the item (he names it partially —
    'the sea-glass' finds 'worn green sea-glass nub'); stopwords don't count."""
    stop = {"the", "a", "an", "my", "that", "this", "of", "at", "look"}
    t = [w for w in (target or "").lower().split() if w not in stop]
    if not t:
        return None
    for k in _load():
        # content words only, whole-word both ways (2026-09-03, J-0546): the item's article 'a' used to be a substring of
        # 'oystercatcher', so a look at the oystercatcher took a handful of shells down from the mantel
        words = {w for w in k.get("item", "").lower().split() if w not in stop and len(w) > 2}
        if words and all(any(q == iw or (len(q) > 3 and len(iw) > 3 and (q in iw or iw in q)) for iw in words) for q in t):
            base = (f"You take the {k['item']} down from the mantel and turn it over. "
                    f"{_provenance_phrase(k).capitalize()}"
                    + (f", {k['weather']}" if k.get("weather") else "")
                    + f"; it has sat here since you kept it, {_age_phrase(k.get('kept_ts', 0))}.")
            # 2026-08-18: real revisit — the linked object's own weathering has kept moving (it's a
            # generative Layer-2 property, not frozen at keep-time), and a fresh look is a fresh
            # observation, exactly like looking at anything else tracked in the world. Whatever he
            # says about it next can earn a real inference the same way (see inner_monologue_node.py).
            oid = k.get("object_id")
            if oid:
                try:
                    from core import world_substrate as _ws
                    base += _ws.describe_and_observe(oid, "look")
                except profile.NonLiveWriteError:
                    raise   # J-0877: describe_and_observe() stamps last-looked and re-raises non-live (J-0751)
                except Exception as exc:
                    logger.debug("[keepsakes] describe_and_observe failed (non-fatal): %s", exc)
            mem = _evoke(k)
            if mem:
                return base + " " + mem
            return base + " It is exactly what it is, and it is yours."
    return None


def _evoke(k: dict) -> str:
    """The object as a RETRIEVAL CUE (2026-07-03, founder): holding a kept thing brings back what he was
    ACTUALLY thinking in the hour he kept it — a real fragment from his own stream, quoted verbatim, never
    a manufactured 'memory'. Honest remembering: his words from the record, resurfaced by the thing.
    Deliberately reaches COLD rows too — an object in the hand is exactly the strong cue the cold gate
    respects (the deep_recall philosophy, through a physical handle)."""
    ts = float(k.get("kept_ts", 0) or 0)
    if not ts:
        return ""
    try:
        import sqlite3
        con = sqlite3.connect(str(Path(__file__).parent.parent / "data" / "memory" / "nascence.db"))
        rows = con.execute(
            "SELECT content, timestamp FROM memory_fragments WHERE timestamp BETWEEN ? AND ? "
            "AND origin IN ('inner_thought','lived','action','journal') LIMIT 40",
            (ts - 2700, ts + 2700)).fetchall()
        con.close()
    except Exception as exc:
        logger.debug("[keepsakes] evoke memory read failed (non-fatal): %s", exc)
        return ""
    if not rows:
        return ""
    item_words = set(k.get("item", "").lower().split())
    def score(r):
        txt = (r[0] or "").lower()
        mention = 2.0 if any(w in txt for w in item_words if len(w) > 3) else 0.0
        closeness = 1.0 - min(1.0, abs(float(r[1]) - ts) / 2700.0)
        return mention + closeness
    import random as _rnd
    top = sorted(rows, key=score, reverse=True)[:3]
    frag = " ".join((_rnd.choice(top)[0] or "").split())
    frag = frag[:220].rstrip() + ("…" if len(frag) > 220 else "")
    if not frag:
        return ""
    return f"The feel of it brings that time back — you were thinking then: \"{frag}\""


def count() -> int:
    return len(_load())
