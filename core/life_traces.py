"""
Nascence — TRACES, DEATHS AND CARCASSES, INTERACTIONS, GRADUATION (Living World L4, J-0513, 2026-09-03;
rulings D-0130 harshness, D-0133 interactions and graduation).

TRACES   Every population row's `traces` become real world_traces objects while it is about — prints on the wet
         sand, droppings on the lawn, broken shells at the thrush's anvil, a feather — findable later by his own look
         (sensorium's trace read path) and by the tracking hand (fieldcraft.follow_trail), decaying on world_traces'
         own weather laws. One active trace per creature per place; nothing is told.
DEATHS   Lifespan means dying. Carcasses are STATE with a decay clock — fresh → picked → bones → gone — on the
         world's time. Sources: the trap (garden.check_trap, J-0512), the cat (a fledgling taken, a mouse or a skink
         brought to the doorstep), a storm (a dead gannet on the tideline — the one he has already watched twelve
         times), a hedgehog that did not wake in spring, and plain mortality against the row's lifespan. A look at
         "the dead gannet", "the bones", "the skull" is answered by the carcass where it lies; ambient noticing fires
         once per carcass. Bones are keepable through the existing keep hand (his prose names the thing).
INTERACTIONS  As rows, not code: the hedgehog eats the slugs (garden's slug pressure falls on hedgehog nights); the
         cat's kills; the deeds (dig / mow / seed / the saucer) that draw their takers via life.note_deed.
GRADUATION  The third trigger (item_and_population_factories): a population creature seen at the same place five
         times in thirty days becomes an INDIVIDUAL — a witnessed ledger event, a history, and a name-slot he may
         fill (naming_act mirrors the cat's naming grammar; the world never names it for him). One animal, or a
         pair, met again — never a flock, a swarm or any row whose own data says it is a group (group_grain,
         J-1174 / D-0166 re-ruled 2026-09-21, F-1622). The five are five distinct ENCOUNTERS, not five looks: a look
         counts only if it is at least GRADUATE_ENCOUNTER_GAP_S (30 minutes) after the last counted one (counted_sightings,
         J-1766 / D-0335, 2026-10-04; supersedes D-0247's raw counting).
Zero LLM; fail-open; run from life.advance; all writes are world state or his ledger; nothing rendered from here.
"""
from __future__ import annotations

import json
import logging
import random
import re
import time

logger = logging.getLogger("nascence.life_traces")

TRACE_P_PER_H = 0.08                  # per creature-hour, when it has traces to leave
CARCASS_STAGES = (("fresh", 2.0), ("picked", 7.0), ("bones", 30.0))     # stage, age in days at which it ENDS
MORTALITY_K = 1.5                     # hazard multiplier on 1/(lifespan_y*365) per creature-day
CARCASS_GAP_S = 45 * 86400.0          # at most one natural death per row per 45 days
GANNET_STORM_P = 0.35                 # per storm-day a dead gannet may wash up
HEDGEHOG_WAKE_FAIL_P = 0.15           # per year: one that did not wake
GRADUATE_SIGHTINGS, GRADUATE_WINDOW_S = 5, 30 * 86400.0
# J-1766 / D-0335 (Travis, /decide-review 2026-10-04: "Encounters, N = 30 min"; supersedes D-0247's raw counting): the five are five distinct ENCOUNTERS, not five
# looks. A rendered sighting counts toward them only if it is at least this many seconds after the last COUNTED sighting of that row at that place
# (counted_sightings, read when graduation is decided, from the stored list, which stays raw). The one named N; 0 is the old raw counting, every look counting.
GRADUATE_ENCOUNTER_GAP_S = 30 * 60.0
GRADUATE_LIST_MAX = 100     # most raw looks kept per key@place in recent_sightings. It was a bare 20 that never bound (a row graduated at its fifth look, so its list never
                            # passed five); under D-0335 an uncounted look stays in the list, so the cap must not evict a counted encounter (four encounters of 25 looks fit)

# where a creature's trace lands, per place (the spots are prose; positions are the place's coordinates)
_TRACE_POS = {"garden": {"hedge_bottom": [9.0, 2.6, 0.0], "lawn_edge": [4.0, 7.8, 0.0], "lawn": [5.5, 7.5, 0.0], "anvil_stone": [8.6, 6.0, 0.1],
                         "doorstep": [2.2, 2.0, 0.0], "compost": [9.2, 2.2, 0.0], "tree": [8.8, 3.5, 0.0], "bed": [5.5, 5.5, 0.35], "fence": [5.6, 11.2, 0.0]},
              "shore": {"tideline": [8.0, 3.0, 0.0], "shingle": [10.0, 4.0, 0.0], "rocks": [4.0, 2.0, 0.3], "stream_mouth": [14.0, 6.0, 0.0], "rock_pools": [3.0, 1.5, 0.0]},
              "wood": {"path": [3.0, 3.0, 0.0], "undergrowth": [4.5, 2.0, 0.0], "oak": [6.0, 5.0, 0.0], "leaf_litter": [4.0, 4.0, 0.0]},
              "study": {"skirting": [0.6, 1.0, 0.0], "doorstep": [0.3, 3.8, 0.0]}}
_DEFAULT_POS = {"garden": [5.5, 6.5, 0.0], "shore": [9.0, 3.5, 0.0], "wood": [4.0, 3.0, 0.0], "study": [1.0, 2.0, 0.0]}

_CARCASS_WORDS = ("dead", "carcass", "carcase", "body", "corpse", "bones", "skull", "skeleton", "remains", "feathers and bone", "the kill")
_CARCASS_NOUNS = tuple(w for w in _CARCASS_WORDS if w != "dead")   # F-1244/J-0887 mechanism B: a NOUN alone
                                                                    # ("the bones") still means a carcass with no "dead" present; "dead" itself is an adjective, not a noun -- see is_plant_target below
_DIED = {"trap": "the trap", "cat": "the cat", "storm": "the storm", "did_not_wake": "the winter", "age": "age",
         # D-2 (J-2471, D-0506): the grey cat's own deaths (core/cat_harm) — what carcass_look may say of a fresh body
         "illness": "illness", "starved": "hunger", "fight": "the fight", "fall": "a fall", "possum": "the possum"}
# the mark on a fresh carcass by what it died of (carcass_look): the four original phrases byte-identical, the
# trap's "jaws' bruise" the default for anything unlisted exactly as before; the cat's own causes added (J-2471)
_FRESH_MARK = {"the cat": "a tooth-mark at the neck", "the winter": "no mark on it you can see", "age": "no mark on it you can see",
               "the storm": "flung down as the sea left it",
               "illness": "thin under the coat, the coat gone dull, no mark on it", "hunger": "thin as a rail, every rib showing",
               "the fight": "a bite at the neck, old and gone bad", "a fall": "nothing to see but how it lies",
               "the possum": "torn about the face and foreleg"}


def word_present(words: tuple, text: str) -> bool:
    """F-1669/J-1188: does any of `words` (each a whole word OR phrase, e.g. "bones" or "the kill") appear
    in `text` as itself, not merely as a substring? Plain `in` matched 'the deadfall'/'the dead wood' on
    'dead', 'the cuttlebones' on 'bones', 'nobody' on 'body' -- real, lookable things wrongly diverted into
    the carcass path. Same boundary rule as life._match and J-1165's trace-object gate
    ((?<![a-z-])word(?![a-z-]); a hyphen ends a word too), applied to the WHOLE phrase at once so a
    multi-word entry like "the kill" does not falsely match inside "the killer whale" either (the
    lookahead right after "kill" fails on the following "e"). `text` must already be lowercased by the
    caller, matching every existing call site's own convention."""
    return any(re.search(r"(?<![a-z-])" + re.escape(w) + r"(?![a-z-])", text) for w in words)


def _pos(place: str, spots: list) -> list:
    table = _TRACE_POS.get(place) or {}
    for s in spots or ():
        if s in table:
            return list(table[s])
    return list(_DEFAULT_POS.get(place, [5.0, 5.0, 0.0]))


# ── TRACES ──────────────────────────────────────────────────────────────────────────────────────

def place_traces(r: dict, place: str) -> list:
    """F-1671/J-1189: the phrases truthful AT THIS PLACE for row `r` -- every phrase in its `traces` tuple
    EXCEPT one restricted (via `traces_only_at`) to a set of places that does not include this one. A
    phrase with no `traces_only_at` entry is unrestricted (fires everywhere the row is, byte-identical to
    before this field existed); `traces_only_at` never ADDS a phrase `traces` does not already have, only
    narrows WHERE an existing one may fire -- so `r.get("traces")` itself is never touched, and every
    consumer that reads it directly (the trace-object noun gate, HEADS-style derivations) keeps seeing the
    row's whole vocabulary regardless of which place a phrase is restricted to."""
    restrict = r.get("traces_only_at") or {}
    return [p for p in (r.get("traces") or ()) if p not in restrict or place in restrict[p]]


def traces_pass(now: float, dt: float) -> None:
    try:
        from core import life as _life, world_traces as _wt
        hours = max(0.0, min(dt, 3600.0)) / 3600.0
        if hours <= 0:
            return
        for key, r in _life.rows().items():
            if r.get("kind") == "external" or not r.get("traces"):
                continue
            for place, spots in (r.get("places") or {}).items():
                pool = place_traces(r, place)
                if not pool:
                    continue                                    # every one of this row's phrases is restricted
                                                                  # away from this place (not expected today; safe no-op)
                act = _life.activity(r, place, now)
                if act < _life.PRESENT_AT:
                    continue
                if random.random() >= TRACE_P_PER_H * act * hours:
                    continue
                ttype = f"{key}_trace"
                if any(t.get("type") == ttype for t in _wt.get_active_traces(place)):
                    continue                                    # one active trace per creature per place
                detail = random.choice(pool)
                tid = f"{key}_{place}_{int(now)}"
                _wt.create_trace(tid, ttype, place, _pos(place, spots), clarity=0.8, cause=key)
                try:                                            # the detail rides on the trace record (additive field)
                    tr = _wt._load_traces().get(tid)
                    if tr is not None:
                        tr["detail"] = detail; tr["creature"] = key
                        _wt._save_traces()
                except Exception:
                    pass
                _life._log(_life._EVENTS, {"kind": "trace", "key": key, "place": place, "detail": detail})
    except Exception as exc:
        logger.debug("[life_traces] traces_pass failed (non-fatal): %s", exc)


def _possessive(nm: str) -> str:
    """'the hedgehog' -> "the hedgehog's", 'the gulls' -> "the gulls'" (F-1670/J-1166): a plural noun ending in s takes a
    bare apostrophe. The same 'ends in s but not ss' plural test this file already uses for a number (_fold,
    _species_name) and life._no_trace_line uses for its verb; every name in the rows that ends in s is a plural."""
    return nm + ("'" if nm.endswith("s") and not nm.endswith("ss") else "'s")


def trace_line(t: dict) -> str:
    """For sensorium._trace_event: the ambient noticing of a creature's trace (feature-first, never the name unless
    he knows it). '' if this trace is not ours."""
    try:
        ttype = str(t.get("type") or "")
        if not ttype.endswith("_trace"):
            return ""
        from core import life as _life
        key = t.get("creature") or ttype[:-6]
        r = _life.rows().get(key) or {}
        detail = str(t.get("detail") or (list(r.get("traces") or ("marks",))[0]))
        fresh = float(t.get("clarity", 0)) > 0.6
        nm = _life.name_for(r) if r else ""
        whose = _possessive(nm) if nm else "something's"
        age = "fresh" if fresh else "not fresh, softening already"
        return f"here, {detail} — {whose}, {age}"
    except Exception:
        return ""


def track_line(kinds: set) -> str:
    """For fieldcraft.follow_trail: a creature's trail, followed to where it leads (its spot), naming only what he knows."""
    try:
        from core import life as _life
        for k in sorted(kinds):
            if not str(k).endswith("_trace"):
                continue
            key = str(k)[:-6]
            r = _life.rows().get(key)
            if not r:
                continue
            nm = _life.name_for(r)
            spots = []
            for sp in (r.get("places") or {}).values():
                spots += list(sp)
            where = (spots[0].replace("_", " ") if spots else "the edge of the place")
            what = nm or "whatever left them"
            if nm:
                return f"You follow the marks — {_possessive(nm)} — as far as they go: to the {where}, and there they end. It is not there now; it will be back when its hour comes."
            return f"You follow the marks as far as they go: to the {where}, where they end at nothing you can see. {what} keeps its own hours; you would have to be here then."
        return ""
    except Exception:
        return ""


# ── DEATHS AND CARCASSES ────────────────────────────────────────────────────────────────────────

def add_carcass(species: str, place: str, where: str, cause: str, now: float | None = None) -> dict:
    """A death becomes a carcass in life state (fresh), logged truth-side; nothing rendered."""
    from core import life as _life
    now = time.time() if now is None else now
    st = _life._load()
    c = {"id": f"{species}_{place}_{int(now)}", "species": species, "place": place, "where": where, "ts": now, "cause": cause, "state": "fresh", "noticed": False}
    st.setdefault("carcasses", []).append(c)
    _life._save(force=True)
    _life._log(_life._EVENTS, {"kind": "death", "key": species, "place": place, "cause": cause, "where": where})
    return c


def carcass_state(c: dict, now: float | None = None) -> str:
    now = time.time() if now is None else now
    age_d = (now - float(c.get("ts") or now)) / 86400.0
    for name, ends in CARCASS_STAGES:
        if age_d < ends:
            return name
    return "gone"


def carcass_pass(now: float, dt: float) -> None:
    """Decay every carcass on the world's clock; the natural deaths (mortality, the storm's gannet, the hedgehog
    that did not wake); the cat's kills (from state the cat and the nests already keep)."""
    try:
        from core import life as _life
        st = _life._load()
        days = max(0.0, min(dt, 3600.0)) / 86400.0
        changed = False
        # decay
        keep = []
        for c in st.get("carcasses") or []:
            s = carcass_state(c, now)
            if s == "gone":
                _life._log(_life._EVENTS, {"kind": "carcass_gone", "key": c.get("species"), "place": c.get("place")}); changed = True
                continue
            if s != c.get("state"):
                c["state"] = s; changed = True
            keep.append(c)
        st["carcasses"] = keep
        last = st.setdefault("deaths_last", {})
        rows_ = _life.rows()
        # mortality against lifespan (only where the creature is about — a death is found where it lived)
        for key, r in rows_.items():
            if r.get("kind") == "external" or not r.get("lifespan_y"):
                continue
            for place, spots in (r.get("places") or {}).items():
                act = _life.activity(r, place, now)
                if act < _life.PRESENT_AT:
                    continue
                if now - float(last.get(f"{key}@{place}", 0.0)) < CARCASS_GAP_S:
                    continue
                hazard = MORTALITY_K * days / (float(r["lifespan_y"]) * 365.0)
                if random.random() < hazard:
                    where = (spots[0] if spots else "here")
                    add_carcass(key, place, where, "age", now); last[f"{key}@{place}"] = now; changed = True
        # the storm's gannet on the tideline
        w, wind, _ = _life._weather()
        if (w == "thunderstorm" or wind == "gale" or w == "wind and rain") and "gannet" in rows_:
            if now - float(last.get("gannet@shore", 0.0)) >= CARCASS_GAP_S and random.random() < GANNET_STORM_P * days:
                add_carcass("gannet", "shore", "tideline", "storm", now); last["gannet@shore"] = now; changed = True
        # the hedgehog that did not wake: once a year, in the first month it should be about again
        hh = rows_.get("hedgehog")
        if hh:
            m = _life._month(now)
            sc = hh.get("season_curve") or [1.0] * 12
            waking = sc[m - 1] > 0.0 and sc[m - 2] <= 0.0
            yr = time.localtime(now).tm_year
            if waking and st.get("hedgehog_wake_year") != yr:
                st["hedgehog_wake_year"] = yr; changed = True
                if random.random() < HEDGEHOG_WAKE_FAIL_P:
                    add_carcass("hedgehog", "garden", "hedge_bottom", "did_not_wake", now)
        # the cat's kills, read from state the cat and the nests already keep
        try:
            from core import garden_life as _gl
            d = _gl._load(); n = d.get("nest") or {}
            lost = int(n.get("lost", 0)) if n else 0
            if lost > int(st.get("fledglings_lost_seen", 0)):
                add_carcass("fledgling", "garden", "lawn", "cat", now); changed = True
            st["fledglings_lost_seen"] = lost if n else 0
        except Exception:
            pass
        try:
            from core import cat as _cat
            cs = _cat._load()
            act = str(cs.get("activity") or "")
            if act in ("brought_a_mouse", "gift_rat") and now - float(st.get("cat_gift_last", 0.0)) > 6 * 3600:
                add_carcass("mouse" if act == "brought_a_mouse" else "rat", "study" if cs.get("location") == "indoors" else "garden", "doorstep", "cat", now)
                st["cat_gift_last"] = now; changed = True
            # the cat and the skinks: a warm day, the cat stalking in the garden, a skink on the wall
            sk = rows_.get("skink")
            if sk and cs.get("location") == "garden" and "stalk" in act and _life.activity(sk, "garden", now) >= _life.PRESENT_AT \
                    and now - float(last.get("skink@garden", 0.0)) >= 7 * 86400 and random.random() < 0.6 * days:
                add_carcass("skink", "garden", "doorstep", "cat", now); last["skink@garden"] = now; changed = True
        except Exception:
            pass
        if changed:
            _life._save(force=True)
    except Exception as exc:
        logger.debug("[life_traces] carcass_pass failed (non-fatal): %s", exc)


def carcasses_at(place: str, now: float | None = None) -> list[dict]:
    from core import life as _life
    now = time.time() if now is None else now
    return [c for c in (_life._load().get("carcasses") or []) if c.get("place") == place and carcass_state(c, now) != "gone"]


_SINGULAR = {"mice": "a mouse", "geese": "a goose", "tauhou": "a tauhou", "karoro": "a karoro", "korora": "a kororā"}


def _species_name(sp: str) -> str:
    """One dead thing, singular: 'a gannet', not 'the gannets' (row names are often the flock's)."""
    from core import life as _life
    r = _life.rows().get(sp)
    nm = _life.name_for(r) if r else ""
    if not nm:
        return {"fledgling": "a fledgling", "mouse": "a mouse", "rat": "a rat", "gannet": "a gannet", "skink": "a skink",
                "bird": "a bird"}.get(sp, sp.replace("_", " "))   # "bird": D-0163/J-0700's hunting-fallback carcasses
    base = nm[4:] if nm.lower().startswith("the ") else nm
    if base in _SINGULAR:
        return _SINGULAR[base]
    if base.endswith("s") and not base.endswith("ss"):
        base = base[:-1]
    return ("an " if base[:1].lower() in "aeiou" else "a ") + base


# ── PLANT vs ANIMAL (F-1244/J-0887 mechanism B) ────────────────────────────────────────────────────
# 'the dead lettuce stalks' is the BED's own question (core/garden.py's own CATALOGUE/STAGES already has
# a real 'dead' stage for a plant) -- not this file's one animal carcass, grabbed just because the word
# 'dead' appeared. Read live off core/garden.CATALOGUE (D-0128: things are their own lists) so this stays
# correct as the garden's own cast grows, rather than a second, hand-kept plant-word list that can drift.
_GENERIC_PLANT_WORDS = {"seedling", "seedlings", "leaf", "leaves", "plant", "plants", "bed", "stalk", "stalks",
                        "herb", "herbs", "soil", "compost", "weed", "weeds"}
_plant_words_cache: set | None = None


def _plant_words() -> set:
    """Derived, not hand-kept: the species key (+ its simple plural), and each 'names' entry as a WHOLE
    phrase (leading article stripped) plus that phrase's own last word when it is long enough (>=5 letters)
    not to be a generic English word a real animal look could equally use. Deliberately does NOT split a
    'names' phrase into every loose token — an earlier version did, and "the low mat of thyme" / "the wire
    vine" / "the orange marigolds" leaked "low"/"wire"/"orange" into the set, which then matched almost any
    target (caught in this job's own verification, never live)."""
    global _plant_words_cache
    if _plant_words_cache is not None:
        return _plant_words_cache
    words = set(_GENERIC_PLANT_WORDS)
    try:
        from core import garden as _g
        for sp, d in (_g.CATALOGUE or {}).items():
            key_phrase = sp.replace("_", " ")
            words.add(key_phrase)
            if not key_phrase.endswith("s"):
                words.add(key_phrase + "s")            # a simple regular plural: "lettuce" -> "lettuces"
            for nm in (d.get("names") or ()):
                phrase = re.sub(r"^(the|a|an)\s+", "", nm.lower().strip()).strip()
                if not phrase:
                    continue
                words.add(phrase)
                last = phrase.split()[-1]
                if len(last) >= 5:
                    words.add(last)
    except Exception:
        return words                              # fail-open; do not cache a partial read
    _plant_words_cache = words
    return words


def is_plant_target(target: str) -> bool:
    """A dead-word target that names a garden plant/part, not an animal (F-1244 mechanism B)."""
    t = (target or "").lower()
    return any(re.search(r"\b" + re.escape(w) + r"\b", t) for w in _plant_words())


def is_place_object_target(target: str, place: str) -> bool:
    """F-1669/J-1188 mechanism D: a dead-word target that names a real, ordinary PLACE-CONTENT object
    (core/world_content_*.py, resolved via core.world_detail's own registry the same way is_plant_target
    is derived from garden.CATALOGUE) rather than any carcass -- "the deadfall" / "the dead wood" / "the
    fallen dead wood" at the wood share the word "dead" with an animal carcass by pure vocabulary
    coincidence (world_content_wood.py's own "deadfall" object is literally aliased "dead wood"), but
    they are not one. This is checked ONLY as the last resort in look_answer's carcass block, after
    carcass_look/dead_trace_look have both already come up with nothing real to answer with -- so a real,
    active carcass or trace always wins the tie; this can never suppress one.

    NARROWER than a bare world_detail match (found by this job's own differential, not assumed safe):
    some place-content objects are ambient LIVE-creature pools with a generic bare-noun alias -- garden's
    "birds" object is aliased plain "bird" -- and "the dead bird" would otherwise fall through to a pool
    describing live birds doing ordinary things, a wrong answer worse than the honest "no body" line it
    replaces (no such regression is invited by "the deadfall": ITS OWN alias, "dead wood", carries the
    carcass word as part of the object's own identity). So the MATCHED ALIAS ITSELF must also carry a
    carcass word -- not merely a coincidental overlap between Du's own "dead X" phrasing and some
    unrelated object's ordinary noun. That alias-side check is deliberately a plain SUBSTRING test, not
    word_present's own word-boundary rule: "deadfall" (one compound word, no boundary before "fall")
    would otherwise fail the very check meant to include it, and the alias list is a small, curated,
    hand-authored vocabulary -- not arbitrary text -- so a substring risk does not apply the way it did
    to the original bug (checked directly, not assumed: only wood:deadfall's own two aliases, "deadfall"
    and "dead wood", carry any _CARCASS_WORDS substring anywhere in the whole registry). Mirrors
    world_detail._match's own two-directional boundary-matched search for the actual TARGET match
    exactly (same regex), adding only that one extra alias-side condition."""
    try:
        from core import world_detail as _wd
        _wd._load()
        t = " ".join((target or "").lower().split())
        if not t:
            return False
        for spec in _wd._REGISTRY.values():
            if spec["location"] != place:
                continue
            for a in spec["aliases"]:
                if not any(w in a for w in _CARCASS_WORDS):
                    continue                          # the OBJECT's own name must carry the carcass word
                if (a == t or (len(a) > 3 and re.search(r"(?<![a-z-])" + re.escape(a) + r"(?![a-z-])", t))
                        or (len(t) > 3 and re.search(r"(?<![a-z-])" + re.escape(t) + r"(?![a-z-])", a))):
                    return True
        return False
    except Exception:
        return False


def carcass_look(target: str, place: str, now: float | None = None) -> str:
    """The answer to a look at a dead thing here: by its state. '' if no carcass here, or the target names
    no carcass at all -- a bare 'dead' + a plant/garden noun (F-1244 mechanism B) is the bed's own
    question and must return '' here so core/garden.py's own look answers it, not this place's carcass."""
    try:
        now = time.time() if now is None else now
        t = (target or "").lower()
        cs = carcasses_at(place, now)
        if not cs:
            return ""
        named = [c for c in cs if c["species"].replace("_", " ") in t]
        if named:
            want = named
        elif is_plant_target(t):
            want = []                              # the bed's own look answers this, not the carcass
        elif word_present(_CARCASS_WORDS, t):   # F-1669/J-1188: whole-word (was: substring on _CARCASS_NOUNS or bare "dead" in t)
            want = list(cs)                        # a carcass noun, or a bare 'dead' that names no plant
        else:
            want = []
        if not want:
            return ""
        c = want[0]; s = carcass_state(c, now); nm = _species_name(c["species"])
        where = str(c.get("where") or "here").replace("_", " ")
        cause = _DIED.get(str(c.get("cause") or ""), "")
        c["noticed"] = True
        if s == "fresh":
            line = f"{nm[0].upper() + nm[1:]} lies dead at the {where}, whole still, the eyes gone dull; " + \
                   _FRESH_MARK.get(cause, "the jaws' bruise across it") + "."   # J-2471: the table above (the original four unchanged)
        elif s == "picked":
            line = f"What was {nm} at the {where} is opened and picked now — the karoro's work, or the cat's; feathers and fur about it, the smell sharp when the air moves."
        else:
            line = f"At the {where}, bones — {nm}'s, picked clean and going grey, the skull small and thin; the rest scattered. It would keep, if you wanted it."
        return line
    except Exception:
        return ""


def dead_trace_look(target: str, place: str, now: float | None = None) -> str:
    """F-1244/J-0887 mechanism A's second rung: when no carcass answers, a still-active world_traces trace
    at this place whose OWN detail already names a dead thing answers instead, rendered the same way
    ambient noticing already does (trace_line). Generic on purpose: after mechanism C removed the gannet
    and karoro rows' own 'dead gannet' trace strings (the only source that ever reached here), nothing
    registers one of these today -- GANNET_STORM_P's carcass is the sole dead-gannet source now -- but a
    future row's `traces` should not silently reopen this same bypass unnoticed."""
    try:
        from core import world_traces as _wt
        t = (target or "").lower()
        cand = [tr for tr in _wt.get_active_traces(place)   # F-1669/J-1188: whole-word, was substring
                if word_present(_CARCASS_WORDS, str(tr.get("detail") or "").lower())]
        if not cand:
            return ""
        named = [tr for tr in cand if str(tr.get("creature") or "").replace("_", " ") in t]
        return trace_line(named[0] if named else cand[0])
    except Exception:
        return ""


# ── TRACE OBJECTS: a look at what a creature LEFT is answered by the trace, never by the creature ─────────
# (F-1617 / J-1165 -- the generalisation of J-0887's dead-thing routing to every trace)
# J-0887 diverted only a target holding a _CARCASS_WORDS word. But any trace phrase can share a target with its own
# creature's alias -- "the gannet feather", "the kingfisher's burrow" -- and such a target then fell through to
# life._match() and the LIVING row's own visibility roll: the world answered "Nothing shows itself; whatever is there
# keeps still." 3 min 16 s after it had itself minted 'a gannet feather, white and stiff' (life_events.jsonl
# 2026-09-17 08:28:42, AFTER J-0887 was live; the same for the burrow at 2026-09-12 09:28:30).
# The narrowest gate that closes the class -- every clause below is DERIVED from the rows, none is a typed-in
# vocabulary (the way is_plant_target derives plant nouns from garden.CATALOGUE):
#   1. the target names one of THIS row's OWN trace objects: a head noun of one of the row's own `traces`
#      phrases (trace_head), never another creature's;
#   2. ... in the shape a creature and what it left take -- "the gannet feather", "the kingfisher's burrow", "the
#      feather of the gannet": the noun is reached from the alias without crossing a preposition, a conjunction, a
#      comma or a participle, so "the shag on the rock", "the gull with a feather" and "the oystercatcher opening
#      shells" stay creature looks;
#   3. ... and the row's own hand-written aliases / place spots / look lines do not already speak of that noun (the
#      spider's web, the ants' road, the slug's trail, the shag's rock are the ROW's own designed subject and keep
#      answering exactly as before), and it is not a garden plant word (the bed's own look owns those).
# Numbers are taken as the engine wrote them: 'feather' is a trace, 'feathers' is plumage (a real look: "the shag's
# feathers"), and 'dropping' is a participle (a real look: "the kingfisher dropping").
_ARTICLES = frozenset(("a", "an", "the", "some", "its", "their", "his", "her", "this", "that", "these", "those", "one"))
# closed grammatical classes (function words) -- where a noun phrase ends. NOT a vocabulary of the world.
_NP_END = frozenset(("about above across after against along among around at before behind below beneath beside besides "
                     "between beyond by down for from in inside into near of off on onto out outside over past since "
                     "through throughout to toward towards under underneath until up upon via with within without").split())
_CLAUSE_JOIN = frozenset("and or but nor then while when where whose who which that as than like plus".split())
_WORD = re.compile(r"[a-zāēīōū]+(?:[-'’][a-zāēīōū]+)*")


def _np_end(w: str) -> bool:
    """A preposition, a conjunction, or a participle ('dropping', 'hunting', 'clinging', 'strung'; five letters or
    more, so 'wing' and 'ring' stay ordinary words): the first noun phrase is over."""
    return w in _NP_END or w in _CLAUSE_JOIN or (len(w) > 4 and w.endswith(("ing", "ung")))


def _fold(w: str) -> str:
    """Number-folded, for asking 'does this row already speak of that word' (never for matching a target)."""
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w


def trace_head(phrase: str) -> str:
    """The head noun of one trace phrase, exactly as the engine wrote it: the last word of its first noun phrase
    ('a burrow in the cliff bank' -> 'burrow', 'three-toed prints on the wet sand' -> 'prints', 'a gannet feather,
    white and stiff' -> 'feather', 'a split brown cicada shell clinging to the fence post' -> 'shell')."""
    out: list[str] = []
    for w in _WORD.findall((phrase or "").lower().split(",")[0]):
        if not out and w in _ARTICLES:
            continue
        if w == "of":
            continue                                # 'a scatter of feathers' -> feathers
        if out and _np_end(w):
            break
        out.append(w)
    return out[-1] if out else ""


def _row_speaks(r: dict) -> set:
    """Every word (number-folded) the row's OWN hand-written text already uses: its aliases, its place spots and
    its look lines (feature / miss / absent / reveal / eyeshine). A trace noun in here is the row's designed
    subject -- its own look already renders that thing -- so it is left to the row."""
    words: set = set()

    def add(s) -> None:
        words.update(_fold(w) for w in _WORD.findall(str(s).lower()))

    def walk(x) -> None:
        if isinstance(x, str):
            add(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)
    for a in r.get("aliases") or ():
        add(a)
    for spots in (r.get("places") or {}).values():
        for s in spots or ():
            add(str(s).replace("_", " "))
    h = r.get("hidden") or {}
    for k in ("feature", "miss", "absent", "reveal", "eyeshine"):
        walk(h.get(k))
    return words


def trace_nouns(r: dict, only: set | None = None) -> set:
    """This row's own trace-object nouns (clauses 1 and 3 above), derived from its `traces` tuple. `only` narrows to
    heads already seen in a target, so the common creature look never pays for the exclusion reads."""
    heads = {trace_head(p) for p in (r.get("traces") or ())} - {""}
    if only is not None:
        heads &= only
    if not heads:
        return set()
    speaks, plant = _row_speaks(r), _plant_words()
    return {h for h in heads if _fold(h) not in speaks and h not in plant and _fold(h) not in plant}


def trace_object_noun(r: dict, target: str) -> str:
    """'' unless `target` names one of row `r`'s own trace objects in the creature-and-what-it-left shape (clause 2):
    then that noun, as typed. Pure; fail-open (any surprise = '' = the living row answers, exactly as before)."""
    try:
        t = (target or "").lower()
        if not t or not r.get("traces"):
            return ""
        heads = {trace_head(p) for p in r["traces"]} - {""}
        present = {h for h in heads if re.search(r"(?<![a-z-])" + re.escape(h) + r"(?![a-z-])", t)}
        if not present:
            return ""                                # the common case: a plain creature look stops here
        nouns = trace_nouns(r, only=present)
        if not nouns:
            return ""
        for a in sorted(r.get("aliases") or (), key=len, reverse=True):
            # the same word-boundary rule as life._match (a hyphen ends a word too), so this reads the alias _match found
            for m in re.finditer(r"(?<![a-z-])" + re.escape(str(a).lower()) + r"(?![a-z-])", t):
                om = re.search(r"([a-zāēīōū]+(?:-[a-zāēīōū]+)*)\s+of\s+(?:(?:the|a|an|that|this)\s+)?$", t[:m.start()])
                if om and om.group(1) in nouns:      # "the feather of the gannet"
                    return om.group(1)
                rest = re.split(r"[,;.!?]", re.sub(r"^['’]s?", "", t[m.end():]))[0]   # "the gannet's feather", "the gulls' prints"
                for w in _WORD.findall(rest)[:5]:    # a short run of adjectives, then the noun
                    if w in nouns:
                        return w
                    if _np_end(w):
                        break
        return ""
    except Exception:
        return ""


def trace_object_look(r: dict, noun: str, place: str, now: float | None = None) -> str:
    """The answer to a look at a creature's trace object: the row's own still-active world_traces trace at this
    place whose detail names the noun, rendered exactly as the ambient noticing does (trace_line -- so the world
    does not tell a second story about the thing it placed). '' = no such trace is active here. Deliberately lets
    an unexpected error RAISE (unlike dead_trace_look): the caller falls back to the living row on an error, and
    must never assert 'there is none' about a store it could not read."""
    from core import world_traces as _wt
    key = str(r.get("key") or "")
    pat = re.compile(r"(?<![a-z-])" + re.escape(noun) + r"(?![a-z-])")
    cand = []
    for tr in _wt.get_active_traces(place):
        if str(tr.get("type") or "") != f"{key}_trace" and str(tr.get("creature") or "") != key:
            continue                                # the creature's OWN trace, not another creature's
        detail = str(tr.get("detail") or (list(r.get("traces") or ("",))[0]))     # the same fallback trace_line uses
        if pat.search(detail.lower()):
            cand.append(tr)
    if not cand:
        return ""
    cand.sort(key=lambda tr: -float(tr.get("clarity", 0.0)))
    line = trace_line(cand[0])
    if not line:
        raise ValueError("an active trace of this row could not be rendered")    # never read as 'none here'
    return line


# ── NEST OBJECTS: a look at a bird's NEST that names the bird (D-0345 / J-1774, F-2382) -- the gate is SHADOW ONLY ─────────────────
# 'the oystercatcher and eggs', "the oystercatcher's scrape", 'the oystercatcher nest' name the bird's alias, so life._match() hands the
# look to the LIVING row's own visibility roll -- 15 such looks since 09-04 (F-2382), 5 of them answered 'Nothing shows itself; whatever is
# there keeps still' while the eggs stood. This is F-1617's shape for a nest instead of a trace, with two differences from J-1165's gate:
#   * the nouns are the NEST ADAPTER's, not the row's `traces`: the head of the adapter's name ('the oystercatchers' scrape' -> scrape) and the
#     tail of its key ('oystercatcher_nest' -> nest), derived the way trace_nouns derives from `traces` -- plus the adapter's own `nest_nouns`
#     data field, because the commonest word ('eggs') lives in no row name (life_birds.nest_adapters carries it, as a row carries `traces`);
#   * the shape: trace_object_noun's alias walk, plus ONE 'and' (determiners skipped) -- 'the oystercatcher and (its) eggs' is Du's own phrasing,
#     12 of the 15 real looks. A preposition or a participle still ends the phrase: 'the oystercatcher hunting near the scrape', 'on the nest',
#     'sitting on eggs', 'with eggs', 'guarding its nest' stay creature looks.
# NOT LIVE. life.look_answer only OBSERVES this (core/nest_gate_shadow.observe appends what the gate WOULD divert to
# data/nest_gate_shadow.jsonl and changes no answer); the gate goes live only on a new ruling from Travis (D-0345).
# LIVE since J-2246 (D-0444, Travis 2026-10-16, option A): nest_gate_shadow.live_divert reads this shape and life.look_answer answers a
# nest-object look at the bird's own nest place with that place's nest line (+ the bird's own line on a sighting); see nest_gate_shadow.py.
def nest_nouns(r: dict, nest_row: dict | None = None) -> set:
    """The words that name nest-owning row `r`'s OWN nest (derived, see above); empty for a row with no nest adapter. `nest_row` defaults to
    r['nest']'s row in the life engine's table. Pure; fail-open (an unknown or unreadable row has no nouns)."""
    try:
        nr = nest_row
        if nr is None:
            from core import life as _life
            nr = _life._ROWS.get(str(r.get("nest") or ""))
        if not nr:
            return set()
        words = {trace_head(str(nr.get("name") or "")), str(nr.get("key") or "").split("_")[-1]}
        words.update(str(w).lower() for w in (nr.get("nest_nouns") or ()))
        return {w for w in words if w}
    except Exception:
        return set()


def nest_object_shape(r: dict, target: str, nest_row: dict | None = None) -> tuple:
    """('', '') unless `target` names one of nest-owning row `r`'s own nest nouns in the creature-and-its-nest shape; then (the noun as typed,
    the shape): 'adjacent/possessive' (the oystercatcher nest, the oystercatcher's scrape), 'conjunction' (the oystercatcher and its eggs) or
    'of-form' (the nest of the oystercatcher). Pure; fail-open (any surprise = ('', '') = the living row answers, exactly as before)."""
    try:
        t = (target or "").lower()
        if not t or not r.get("nest"):
            return "", ""
        nouns = nest_nouns(r, nest_row)
        if not nouns or not any(n in t for n in nouns):
            return "", ""                           # the common case: a plain creature look stops here
        for a in sorted(r.get("aliases") or (), key=len, reverse=True):
            # the same word-boundary rule as life._match (a hyphen ends a word too), so this reads the alias _match found
            for m in re.finditer(r"(?<![a-z-])" + re.escape(str(a).lower()) + r"(?![a-z-])", t):
                om = re.search(r"([a-zāēīōū]+(?:-[a-zāēīōū]+)*)\s+of\s+(?:(?:the|a|an|that|this)\s+)?$", t[:m.start()])
                if om and om.group(1) in nouns:      # "the nest of the oystercatcher"
                    return om.group(1), "of-form"
                rest = re.split(r"[,;.!?]", re.sub(r"^['’]s?", "", t[m.end():]))[0]   # "the oystercatcher's scrape", "the oystercatchers' scrape"
                bridged = False
                for w in _WORD.findall(rest)[:7]:    # a short run of adjectives and determiners, ONE 'and', then the noun
                    if w in nouns:
                        return w, ("conjunction" if bridged else "adjacent/possessive")
                    if w == "and" and not bridged:
                        bridged = True
                        continue
                    if w in _ARTICLES:
                        continue
                    if _np_end(w):
                        break
        return "", ""
    except Exception:
        return "", ""


def nest_object_noun(r: dict, target: str, nest_row: dict | None = None) -> str:
    """'' unless `target` names one of row `r`'s own nest nouns in the creature-and-its-nest shape (nest_object_shape): then that noun, as typed."""
    return nest_object_shape(r, target, nest_row)[0]


def ambient_carcass(place: str, now: float | None = None) -> str:
    """Once per carcass: the noticing, for sensorium's trace read path."""
    try:
        now = time.time() if now is None else now
        from core import life as _life
        for c in carcasses_at(place, now):
            if c.get("noticed"):
                continue
            c["noticed"] = True
            _life._save(force=True)
            nm = _species_name(c["species"]); where = str(c.get("where") or "here").replace("_", " ")
            return f"something lies at the {where} that was not there before — {nm}, dead, " + \
                   ("whole and wrong-looking" if carcass_state(c, now) == "fresh" else "picked over already")
        return ""
    except Exception:
        return ""


# ── INTERACTIONS (rows, and the little that must be code) ────────────────────────────────────────

def interactions_pass(now: float, dt: float) -> None:
    """The hedgehog eats the slugs: on a hedgehog night the garden's slug pressure falls (fewer trails, fewer holed
    leaves) — a binding he can make. Other interactions live in rows (diet / eaten_by / responds_to_du) and in the
    passes above."""
    try:
        from core import life as _life
        hours = max(0.0, min(dt, 3600.0)) / 3600.0
        hh = _life.rows().get("hedgehog")
        if not hh or hours <= 0:
            return
        act = _life.activity(hh, "garden", now)
        if act < _life.PRESENT_AT:
            return
        from core import garden as _g
        st = _g._load()
        before = float(st.get("slugs", 0.3))
        after = max(0.05, before - 0.03 * act * hours)
        if after < before:
            st["slugs"] = round(after, 4)
            _g._save()
            st2 = _life._load()
            if now - float(st2.get("hedgehog_slugs_logged", 0.0)) > 12 * 3600:
                st2["hedgehog_slugs_logged"] = now; _life._save()
                _life._log(_life._EVENTS, {"kind": "effect", "key": "hedgehog", "place": "garden", "what": "ate_slugs", "slugs": st["slugs"]})
    except Exception as exc:
        logger.debug("[life_traces] interactions_pass failed (non-fatal): %s", exc)


# ── GRADUATION: population → individual (the third trigger) ─────────────────────────────────────

# J-1174 (D-0166 re-ruled 2026-09-21; F-1622): the third trigger recognises ONE animal (or a bonded pair) met again and again at a
# place -- the hedgehog under the hedge, the oystercatcher pair on the shingle. It never recognises a flock or a swarm: 'It is the same
# one' said of the honeybees (graduated 09-17, its 4th and 5th sightings 6 s apart) and of the gulls (09-19) was a wrong claim about a
# mass. The exclusion is read off the row's OWN data, not a list of species to keep in step with new rows:
_SOLO_LOW_BAND = ("one", "one or two", "a pair", "two")     # a quietest count band that is one animal (or a pair) -- the row can be met alone
_GROUP_BAND = re.compile(r"\b(?:flock|swarm|pod|shoal|skein|dozens?)\b|\b(?:of|with) them\b", re.I)   # wording that names a mass: 'a working flock',
                                                            # 'a river of them', 'a dozen', 'dozens at the bare bank', 'the bed alive with them'


def group_grain(r: dict | None) -> str:
    """Why this row is population-grain (a flock, a swarm, a colony, a plural collective) and so is never recognised as 'the same
    one'; '' when its own data lets it be one animal or a pair. Three signals, all in the row: (1) `plural` -- its name is a plural
    collective ('the gulls', 'the ants'); (2) its QUIETEST count band already names a group ('a few', 'a line') -- it is never met
    alone (the honeybees: 'a few' / 'a dozen' / 'the whole bed hums', and NOT flagged plural); (3) a mass named in its own words,
    in a count band ('a working flock', 'a spaced line of them', 'dozens at the bare bank', 'the turned earth full of them') or in
    the look line Du is shown ('... on the bean tips, more of them, working the clusters' -- a recognition line straight after that
    would contradict it). The first signal that fires is returned, as the reason."""
    if not r:
        return ""
    if r.get("plural"):
        return "its name is a plural collective (plural=True)"
    count = r.get("count")
    bands = [str(b).strip().lower() for b in (count if isinstance(count, (list, tuple)) else ())]
    if bands and bands[0] not in _SOLO_LOW_BAND:
        return f"its quietest count band is already a group ({bands[0]!r})"
    for b in bands:
        if _GROUP_BAND.search(b):
            return f"a count band names a mass ({b!r})"
    hidden = r.get("hidden")
    feat = hidden.get("feature") if isinstance(hidden, dict) else None
    for ln in (feat.values() if isinstance(feat, dict) else ()):
        m = _GROUP_BAND.search(str(ln or ""))
        if m:
            return f"its own look line names a mass ({m.group(0)!r})"
    return ""


def counted_sightings(stamps, gap_s: float | None = None) -> list:
    """J-1766 / D-0335: the looks in `stamps` (a stored recent_sightings list: the raw timestamps of every rendered sighting of one row at one place)
    that COUNT toward graduation. A look counts only if it is at least `gap_s` (default GRADUATE_ENCOUNTER_GAP_S, 30 minutes, read when called) after
    the last COUNTED look, so a burst of looks inside one visit is one encounter however many looks it holds. The chain starts at the earliest look and
    runs from the last COUNTED one, not pairwise (looks at 0, 20 and 40 minutes count 0 and 40, not all three), in time order whatever order the list is
    stored in. Read-only: it derives the counted looks and never rewrites `stamps`, so the stored list needs no migration -- a legacy raw list is judged
    by the same rule as a new one, and the rule can be re-read at another gap. A gap of 0 counts every look (the pre-D-0335 raw counting)."""
    gap = GRADUATE_ENCOUNTER_GAP_S if gap_s is None else float(gap_s)
    counted: list = []
    for t in sorted(stamps or ()):
        if not counted or t - counted[-1] >= gap:
            counted.append(t)
    return counted


def note_sighting(key: str, place: str, now: float | None = None) -> bool:
    """Called by life.look_answer on a rendered sighting. Five distinct ENCOUNTERS at the same place inside thirty days graduates the
    creature to an INDIVIDUAL: a witnessed ledger event, a history, a name-slot. Returns True on graduation.
    J-1766 / D-0335: an encounter is a look at least GRADUATE_ENCOUNTER_GAP_S (30 minutes) after the last COUNTED one (counted_sightings,
    computed here, at read time, from the stored raw list), so a burst of looks inside one visit is one encounter. This is the ONLY place the
    rule is read: a record already in `individuals` is never re-judged (individual() and everything that reads it are exactly as before), and
    the stored recent_sightings list is never rewritten -- it still holds every look.
    J-1174: a row whose own data says it is a group (group_grain) never graduates -- and a record such a row already holds
    (the honeybees and the gulls graduated before this rule) is DORMANT: not counted, not rendered, not named. Nothing is
    written for it; the stored record is left exactly as it was."""
    try:
        from core import life as _life
        now = time.time() if now is None else now
        r = _life.rows().get(key) or {}
        if group_grain(r):
            return False
        st = _life._load()
        ind = st.setdefault("individuals", {})
        if key in ind:
            ind[key]["sightings"] = int(ind[key].get("sightings", 0)) + 1; ind[key]["last_seen"] = now
            _life._save(); return False
        if r.get("kind") != "population":
            return False
        rec = st.setdefault("recent_sightings", {}).setdefault(f"{key}@{place}", [])
        rec.append(now)
        rec[:] = [t for t in rec if now - t <= GRADUATE_WINDOW_S][-GRADUATE_LIST_MAX:]
        enc = len(counted_sightings(rec))                 # D-0335: distinct encounters among the stored raw looks, not the looks themselves
        if enc >= GRADUATE_SIGHTINGS:
            ind[key] = {"place": place, "since": now, "name": None, "sightings": len(rec), "last_seen": now,
                        "history": [{"ts": now, "event": f"recognised: the same one at the {place}, {enc} times in a month"}]}
            _life._save(force=True)
            _life._log(_life._LEDGER, {"kind": "graduated", "key": key, "place": place, "sightings": len(rec)})
            _life._log(_life._EVENTS, {"kind": "graduated", "key": key, "place": place})
            logger.info("[life] GRADUATED %s at %s — an individual now", key, place)
            return True
        _life._save()
        return False
    except Exception:
        return False


def individual(key: str) -> dict | None:
    """The stored individual record for `key`, or None. Graduation is STORED state (data/life_state.json 'individuals'), so a
    record can outlive the rule that made it: J-1174 reads it through group_grain at READ time -- a group row's record (the
    honeybees', the gulls') is dormant, returned as None everywhere (the recognition line, naming, the HUD) without touching the
    store. Rows with no row / an external row behave exactly as before."""
    from core import life as _life
    ind = (_life._load().get("individuals") or {}).get(key)
    if ind and group_grain(_life.rows().get(key)):
        return None
    return ind


def individual_suffix(key: str, place: str | None = None) -> str:
    """The recognition line for a graduated individual ('' when `key` is not one).
    J-1698 (F-2305): `place` is where he is LOOKING. A record is 'the same one at the <place>' -- the rule that earned it is five
    sightings at ONE place and the plan's law reserves an individual for 're-encountered at one spot' -- so the line is said only at the
    place it graduated at. Anywhere else it is '' and the look is exactly what a creature that never graduated would give (the
    blackbird, graduated at the garden, was told 'you have seen it here too often' on its first ever sighting at the wood).
    `place` omitted or empty, or a record that stores no place (an old one): today's behaviour, the line at any place -- so a caller
    with no look place (naming, the HUD) is untouched. Only the RENDER is scoped: note_sighting still counts every sighting."""
    ind = individual(key)
    if not ind:
        return ""
    if place and ind.get("place") and place != ind["place"]:
        return ""
    if ind.get("name"):
        return f" It is {ind['name']} — you would know it anywhere now."
    return " It is the same one — you are sure of it now; you have seen it here too often for it to be any other."


_TERMINAL = ".!?…"


def _end_sentence(text: str) -> str:
    """Shared terminal-stop rule (F-1622/J-1166, factored out for F-1674/J-1190's own second site): end
    `text`'s sentence with a full stop unless it already ends one, so gluing something else straight on
    never reads as one run-on clause and never doubles a stop. '' in, '' out."""
    body = (text or "").rstrip()
    if body and body[-1] not in _TERMINAL:
        body += "."
    return body


def with_individual_suffix(key: str, line: str, place: str | None = None) -> str:
    """life.look_answer's join of a rendered sighting line and the recognition line (F-1622/J-1166). J-1698 (F-2305): `place` (the
    look's place, passed by look_answer) scopes the line to the place the individual graduated at -- see individual_suffix; at any
    other place the join is the plain `line.strip()`, a look no different from a creature that never graduated. A row's look text is a
    lowercase FRAGMENT with no full stop ('... squabbling over what the tide left'), and nothing downstream wraps it into a
    sentence (sensorium.look, dispatch and wandering.perceive all pass it through verbatim), so gluing the suffix straight on
    read '...what the tide left It is the same one -- ...'. The join now ends the fragment's sentence first -- unless it
    already ends one (the reveal-completed lines end in '.'), so a full stop is never doubled. No suffix (not an individual)
    is exactly the old `(line + '').strip()`. Byte-identical to before this was factored through _end_sentence."""
    suffix = individual_suffix(key, place) if place else individual_suffix(key)    # no place -> the one-argument call, exactly as before J-1698
    if not suffix:
        return line.strip()
    return (_end_sentence(line) + suffix).strip()


def join_reveal(line: str, reveal: str) -> str:
    """life.look_answer's join of a rendered feature line and a learned row's reveal caption (F-1674/
    J-1190) -- the SAME unpunctuated-glue defect class F-1622 already fixed above, at a second site.
    Ten of the eleven reveal-carrying rows begin with an em dash and continue the fragment ON PURPOSE
    ('...something small and quick -- a reef heron; ...') -- that join is untouched, bare space, exactly
    as before. The one row whose reveal is instead a capitalised, complete sentence (long_tailed_bat: 'It
    is a bat -- a long-tailed bat, the small one that hawks over the trees at dusk.') needs the fragment's
    own sentence ended first, or the join reads '...there and gone It is a bat -- ...'. Which rule applies
    is read from the reveal's OWN first character (upper-case = a new sentence), not a row-by-row list, so
    a future row's reveal is handled correctly by construction whichever way it is written. `line` empty
    (no feature line this phase) is exactly the old `(line + ' ' + reveal).strip()` == `reveal.strip()`."""
    reveal = reveal or ""
    if not line:
        return reveal.strip()
    if reveal[:1].isupper():
        return (_end_sentence(line) + " " + reveal).strip()
    return (line + " " + reveal).strip()


def give_name(key: str, name: str, now: float | None = None) -> str:
    """His to give, never the world's. Only an individual can be named."""
    try:
        from core import life as _life
        now = time.time() if now is None else now
        ind = individual(key)                   # J-1174: a dormant (group-grain) record is not an individual, so it cannot be named
        if not ind:
            return ""
        if ind.get("name"):
            return f"It already has a name — {ind['name']}."
        ind["name"] = name
        ind.setdefault("history", []).append({"ts": now, "event": f"named {name}"})
        _life._save(force=True)
        _life._log(_life._LEDGER, {"kind": "named", "key": key, "name": name})
        try:   # Cat Overhaul B2 (J-2472): a named CAT individual (the tom, J-2470's row) is the other cat, distinguished for good
            from core import cat_referent as _cr
            _cr.record_naming(key, name, now=now)
        except Exception:
            pass
        r = _life.rows().get(key) or {}
        what = _life.name_for(r) or "it"
        return f"{name}, then. {what[0].upper() + what[1:]} at the {str(ind.get('place') or 'place')} is {name} from now on — the name is yours to have given."
    except Exception:
        return ""


_NAME_STOP = {"her", "him", "it", "the", "she", "he", "you", "me", "us", "that", "this", "a", "an", "my", "name", "names",
              "now", "then", "here", "there", "again", "over", "back", "out", "in", "up", "down", "home", "mine", "one"}


def naming_act(thought: str, intention: str = "") -> str | None:
    """Latch (mirrors cat._extract_name): 'I'll call the hedgehog Bramble' / 'the possum's name is Ash' — for a
    creature that has GRADUATED to an individual. None when no naming intent or nothing to name."""
    try:
        from core import life as _life
        inds = {k: v for k, v in (_life._load().get("individuals") or {}).items() if individual(k)}   # J-1174: dormant records are not nameable
        if not inds:
            return None
        txt = f"{thought or ''} {intention or ''}"
        for key in inds:
            r = _life.rows().get(key) or {}
            words = [a for a in (r.get("aliases") or ()) if " " not in a] + [str(r.get("name") or "").replace("the ", "")]
            words = [w for w in words if w]
            if not words:
                continue
            who = r"(?:the |my |that |this |our )?(?:" + "|".join(re.escape(w) for w in words) + r")"
            pats = (rf"\b(?:call|name|dub)\s+{who}\s+([A-Z][\w'-]+)",
                    rf"\b{who}(?:'s)?\s+name\s+(?:is|shall be|will be|can be|should be)\s+([A-Z][\w'-]+)",
                    rf"\bI(?:'ll| will| shall| am going to)?\s*(?:call|name|dub)\s+{who}\s+([A-Z][\w'-]+)")
            for pat in pats:
                m = re.search(pat, txt, re.IGNORECASE)
                if m:
                    nm = m.group(1).strip(" .,'\"")
                    if nm and nm[0].isupper() and nm.lower() not in _NAME_STOP:
                        return give_name(key, nm) or None
        return None
    except Exception:
        return None


# ── for the HUD / pulse ─────────────────────────────────────────────────────────────────────────

def hud_payload(now: float | None = None) -> dict:
    try:
        from core import life as _life
        now = time.time() if now is None else now
        st = _life._load()
        cs = [{"species": c["species"], "place": c["place"], "where": c.get("where"), "state": carcass_state(c, now), "cause": c.get("cause"),
               "age_d": round((now - float(c["ts"])) / 86400.0, 1)} for c in (st.get("carcasses") or []) if carcass_state(c, now) != "gone"]
        inds = {k: {"place": v.get("place"), "name": v.get("name"), "sightings": v.get("sightings"), "since_d": round((now - float(v.get("since", now))) / 86400.0, 1)}
                for k, v in (st.get("individuals") or {}).items() if individual(k)}      # J-1174: a dormant (group-grain) record is not listed
        traces = 0
        try:
            from core import world_traces as _wt
            traces = sum(1 for p in ("garden", "shore", "wood", "study") for t in _wt.get_active_traces(p) if str(t.get("type", "")).endswith("_trace"))
        except Exception:
            pass
        return {"carcasses": cs, "individuals": inds, "creature_traces_active": traces}
    except Exception as exc:
        return {"error": str(exc)[:80]}
