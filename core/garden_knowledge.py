"""
Nascence — GARDEN KNOWLEDGE: what he knows about his plants is EARNED (2026-08-22; the sound_knowledge
pattern applied to the bed; docs/plans/garden_upgrade.md §2.4 "earned bindings").

Three things are never told and must be earned:
  1. IDENTITY — an unlabelled packet, a volunteer from the seed bank: "something" until it declares itself.
     A seedling's two round leaves say nothing; true leaves say a little (a guess with weight); flowering or
     fruit says everything (the reveal). Watching accumulates weight the way missed glimpses do for a bird.
     READING binds too: a book that ties a plant's name to its look (the sanctioned diegetic channel).
  2. CAUSE — why the lettuce died, why the tips browned, why the leaves are holed. The world never says.
     The INVESTIGATE hand hands him the EVIDENCE (the ledger: what he did, what the weather did, what he
     saw) and he authors a binding — a hypothesis with a confidence — which may be wrong. Later outcomes
     revise it: if the same state recurs after the same evidence, the binding firms; if not, it weakens.
  3. HABIT — when a plant flowers, when it dies back, how long a cut takes to fill — learned by living
     through it: the first witnessed flowering of a species is an event; the second is knowledge.

Grandfathered (he has lived with them for months, named): rosemary, thyme, mint, parsley, sunflowers, lettuce,
tomatoes — the old bed's seven. Everything else enters unnamed.

Ledger: data/garden_knowledge.json (append-only events, auditable). Zero LLM. Fail-open. Kill-switch
GARDEN_EPISTEMICS=False renders every plant named.
"""
from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.garden_knowledge")

_DATA = Path(__file__).parent.parent / "data"
_F = _DATA / "garden_knowledge.json"

GARDEN_EPISTEMICS = True
_LEARN_AT = 1.0
GRANDFATHERED = {"rosemary", "thyme", "mint", "parsley", "sunflowers", "lettuce", "tomatoes", "harakeke"}

# what each species looks like at each stage BEFORE it is known — features, never the name; and the
# stage at which it declares itself (reveal), plus book words that can bind it.
UNKNOWN_LOOKS = {
    "shoot": ["two round seed-leaves on a pale stem", "a pair of seed-leaves, no more", "a green loop of stem pushing up, leaves still folded"],
    "leaf": {
        "radish": "rough, lobed leaves, a little hairy", "lettuce": "soft pale-green leaves, crinkled at the edge",
        "silverbeet": "glossy dark leaves with a thick pale rib", "peas": "grey-green leaves in pairs, a tendril already reaching",
        "broad_beans": "thick grey-green leaves on a square stem", "tomatoes": "ferny, sharp-smelling leaves", "beans": "heart-shaped leaves in threes",
        "potatoes": "dark crumpled leaves pushing up in a clump", "garlic": "flat grey-green blades", "strawberries": "leaves in threes, toothed, on red stems",
        "sunflowers": "big rough heart-shaped leaves", "calendula": "soft, slightly sticky pale leaves", "nasturtium": "round leaves like small lily-pads, the stem at the centre",
        "poppies": "a rosette of grey, cut, bristly leaves", "chives": "fine hollow green spears", "chickweed": "small pointed leaves on weak sprawling stems",
        "dandelion": "a flat rosette of toothed leaves", "oxalis": "clover-like leaves that fold at night", "thyme": "tiny grey-green leaves on wiry stems",
        "mint": "square stems, leaves in pairs, a sharp smell when brushed", "parsley": "curled dark leaves on long stalks", "rosemary": "needle leaves, dark above, pale beneath",
    },
    "reveal": {  # the stage at which the plant DECLARES itself to anyone who looks
        "radish": "established", "lettuce": "established", "silverbeet": "established", "peas": "flowering", "broad_beans": "flowering",
        "tomatoes": "flowering", "beans": "flowering", "potatoes": "flowering", "garlic": "established", "strawberries": "flowering",
        "sunflowers": "flowering", "calendula": "flowering", "nasturtium": "flowering", "poppies": "flowering", "chives": "flowering",
        "chickweed": "flowering", "dandelion": "flowering", "oxalis": "flowering", "thyme": "flowering", "mint": "established",
        "parsley": "established", "rosemary": "established",
    },
    "book": {  # name-words + look-words a text must carry to teach it
        "radish": (("radish",), ("root", "red", "peppery", "crisp")), "silverbeet": (("silverbeet", "silver beet", "chard"), ("rib", "stalk", "leaf")),
        "peas": (("pea", "peas"), ("tendril", "pod")), "broad_beans": (("broad bean", "broad beans", "fava"), ("pod", "black and white", "flower")),
        "calendula": (("calendula", "marigold"), ("orange", "petal", "flower")), "nasturtium": (("nasturtium",), ("round leaf", "peppery", "orange", "trumpet")),
        "poppies": (("poppy", "poppies"), ("petal", "red", "seed head")), "chives": (("chive", "chives"), ("onion", "hollow", "purple")),
        "chickweed": (("chickweed",), ("sprawl", "star", "weed")), "dandelion": (("dandelion",), ("yellow", "clock", "seed")),
        "oxalis": (("oxalis", "sorrel"), ("clover", "fold", "bulb")), "strawberries": (("strawberry", "strawberries"), ("runner", "red", "fruit")),
        "potatoes": (("potato", "potatoes"), ("tuber", "earth up", "haulm")), "garlic": (("garlic",), ("clove", "bulb", "blade")),
        "beans": (("dwarf bean", "french bean", "beans"), ("pod", "heart-shaped")),
    },
}


def _load() -> dict:
    try:
        return json.loads(_F.read_text(encoding="utf-8"))
    except Exception:
        return {"events": [], "known": {}, "bindings": [], "witnessed": {}}


def _save(d: dict) -> None:
    path = profile.guard_path(_F)   # J-0783: real data/ only if this process is live; raises if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _weight(d: dict, species: str) -> float:
    return float((d.get("known") or {}).get(species, 0.0))


def is_known(species: str) -> bool:
    if not GARDEN_EPISTEMICS or species in GRANDFATHERED:
        return True
    return _weight(_load(), species) >= _LEARN_AT


def _add(d: dict, species: str, via: str, w: float, note: str = "") -> bool:
    before = _weight(d, species)
    d.setdefault("known", {})[species] = min(1.0, before + w)
    d.setdefault("events", []).append({"ts": round(time.time(), 1), "species": species, "via": via, "w": w, "note": note[:80]})
    d["events"] = d["events"][-600:]
    return before < _LEARN_AT <= d["known"][species]


# ── IDENTITY: how a plant is named in his eye ───────────────────────────────────────────────────
def display_name(species: str, stage: str, plant_id: str = "") -> tuple[str, bool]:
    """(name-as-he-sees-it, known?). Looking at a plant at its reveal stage LEARNS it (the declaration);
    looking earlier earns a little weight (exposure) and returns a features-only description."""
    try:
        from core.garden import CATALOGUE
        cat = CATALOGUE.get(species) or {}
        true_name = (cat.get("names") or (species,))[0]
        if is_known(species):
            return true_name, True
        d = _load()
        reveal_at = UNKNOWN_LOOKS["reveal"].get(species, "flowering")
        order = ("seed", "shoot", "leaf", "established", "flowering", "seeding")
        if stage in order and order.index(stage) >= order.index(reveal_at) if reveal_at in order else False:
            if _add(d, species, "declared", 1.0, f"{plant_id} at {stage}"):
                _save(d)
                return true_name + " — you know it now, seeing it like this", True
            _save(d)
            return true_name, True
        _add(d, species, "exposure", 0.08, f"{plant_id} at {stage}")
        _save(d)
        if stage == "shoot":
            return "a seedling you cannot name yet — " + random.choice(UNKNOWN_LOOKS["shoot"]), False
        feat = UNKNOWN_LOOKS["leaf"].get(species, "leaves you do not recognise")
        return f"a plant you cannot name yet — {feat}", False
    except profile.NonLiveWriteError:
        # J-0783: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own caller
        # instead of being swallowed by this pre-existing broad except.
        raise
    except Exception:
        return species.replace("_", " "), True


def learn_from_text(text: str) -> list[str]:
    """A book or his own note ties a plant's name to its look → learned (the diegetic channel)."""
    out: list[str] = []
    try:
        if not GARDEN_EPISTEMICS or not text:
            return out
        low = text.lower()
        d = _load()
        for sp, (names, looks) in UNKNOWN_LOOKS["book"].items():
            if _weight(d, sp) >= _LEARN_AT:
                continue
            if any(n in low for n in names) and any(l in low for l in looks):
                if _add(d, sp, "read", 1.0, low[:80]):
                    out.append(sp)
        if out:
            _save(d)
    except profile.NonLiveWriteError:
        # J-0783: same — let the raise reach this function's own caller.
        raise
    except Exception:
        pass
    return out


# ── HABIT: witnessed firsts become knowledge ────────────────────────────────────────────────────
def witness(species: str, event: str) -> bool:
    """He was THERE (looking at the bed) when it happened. First time = an event; second = habit.
    Returns True if this is the first witnessing."""
    try:
        d = _load()
        key = f"{species}:{event}"
        w = d.setdefault("witnessed", {})
        w[key] = int(w.get(key, 0)) + 1
        _save(d)
        return w[key] == 1
    except profile.NonLiveWriteError:
        # J-0783: same — let the raise reach this function's own caller.
        raise
    except Exception:
        return False


def habit_line(species: str) -> str:
    """What he has seen this plant do, in his own record — for look()."""
    try:
        d = _load()
        w = d.get("witnessed") or {}
        seen = [k.split(":", 1)[1].replace("_", " ") for k, n in w.items() if k.startswith(species + ":") and n >= 1]
        if not seen:
            return ""
        return " You have seen it " + ", ".join(seen[:3]) + " before."
    except Exception:
        return ""


# ── CAUSE: bindings he authors from evidence, revisable ─────────────────────────────────────────
def evidence_for(plant_id: str, species: str) -> str:
    """The INVESTIGATE hand's answer: facts, no cause. What he did to it, what the weather did, what he saw."""
    try:
        from core import garden as _g
        st = _g._load()
        p = st["plants"].get(plant_id)
        lines = []
        now = time.time()
        # his deeds on the bed (ledger)
        deeds = []
        try:
            for l in open(_g._LEDGER, encoding="utf-8"):
                r = json.loads(l)
                if now - float(r.get("ts", 0)) < 14 * 86400:
                    deeds.append(r)
        except Exception:
            pass
        wat = [r for r in deeds if r.get("deed") == "water"]
        if wat:
            lines.append(f"you have watered the bed {len(wat)} time{'s' if len(wat) != 1 else ''} in the last fortnight"
                         + (f", {sum(1 for r in wat if not r.get('needed'))} of them when the soil was already wet" if any(not r.get("needed") for r in wat) else ""))
        else:
            lines.append("you have not watered the bed in the last fortnight")
        # the world's events on this plant
        evs = []
        try:
            for l in open(_g._EVENTS, encoding="utf-8"):
                r = json.loads(l)
                if r.get("plant") == plant_id and now - float(r.get("ts", 0)) < 21 * 86400:
                    evs.append(r)
        except Exception:
            pass
        fr = [r for r in evs if r.get("event") in ("frost_burned",)]
        sl = [r for r in evs if r.get("event") in ("slug_damage", "eaten_by_slugs")]
        # D-0278/J-1350: eaten_by_birds used to be lumped into `sl` above, so investigating a plant that
        # was ONLY ever bird-bitten (no real slug event at all) came back with a fabricated "wet nights,
        # silver trails" story -- false evidence pointing at the wrong cause, the opposite of what the
        # INVESTIGATE hand is for (law 5: evidence, never a told cause, but it must be TRUE evidence).
        bd = [r for r in evs if r.get("event") == "eaten_by_birds"]
        if fr:
            lines.append("its leaves browned after a clear, still, very cold dawn")
        if sl:
            lines.append("the holes in its leaves appeared after wet nights; there were silver trails on the soil")
        if bd:
            lines.append("pieces are bitten clean out of it, not holed the way a slug leaves them — you have seen a bird about the bed")
        if p:
            if float(st.get("moisture", 0.5)) < 0.2:
                lines.append("the soil round it is dry and pale")
            if float(st.get("weeds", 0)) > 0.5:
                lines.append("weeds have closed in round it")
            if p.get("cut_back"):
                lines.append("it was cut not long ago")
            if p["stage"] == "dead":
                lines.append("it is dead")
        return "What you can put together: " + "; ".join(lines) + "." if lines else ""
    except Exception:
        return ""


# J-1524/F-2082: the SAME cause-tag vocabulary is used both to recognise a hypothesis Du HIMSELF already
# authored (guessed_cause(), below -- feeds bind()) and to score whether a real recurring world event
# agrees with a stored hypothesis (revise(), below, unchanged in behaviour) -- ONE definition so the two
# readings can never drift apart (the same lesson core/hands.py's own module docstring names for
# literal_will's verb list: "read it lazily so there is ONE definition, not two that drift").
_CAUSE_WORDS = {
    "frost": ("frost", "cold", "freeze"), "wet_nights": ("slug", "snail", "wet", "damp"),
    "dry_soil": ("dry", "thirst", "water"), "weeds": ("weed", "crowd", "choke"),
    # D-0278/J-1350: new preceding tag, fired by garden.py's advance() on a real
    # eaten_by_birds event -- lets a binding he authors ("I think a bird's at them")
    # firm the same way a frost/slug binding already can. Internal scoring only:
    # these words are never injected into any rendered text.
    "birds": ("bird", "peck", "pecked", "blackbird", "net", "netting"),
}


# J-1657/F-2229: trigger vocabulary for "he is investigating, not just looking" -- previously duplicated
# inline inside core/garden.py's look() (its own `if any(w in rt for w in (...))` gate, which decides
# whether to fetch evidence_for() at all). Now the ONE definition both that gate and guessed_cause()'s
# own same-neighbourhood check below read, so the two can never drift apart -- same discipline this
# module already applies to _CAUSE_WORDS above (shared by guessed_cause() and revise()).
_INVESTIGATE_WORDS = ("closer", "investigate", "examine", "why", "what happened", "inspect")


def _clauses(text: str) -> list[str]:
    """Split `text` into small units: on sentence-enders (. ! ?) AND on the SAME mid-sentence
    connectives core/dispatch.py's own _deed_phrase() splits a willed clause on (and / then / and then
    / ; , each optionally preceded by a comma). Sentence punctuation is added here because, unlike
    _deed_phrase()'s own caller (which always hands it one clause literal_will already isolated),
    guessed_cause() below receives the WHOLE raw thought+intention text, which can run to several
    unrelated sentences (J-1657/F-2229)."""
    import re as _re
    parts = _re.split(r"[.!?]+\s+|,?\s+(?:and then|then|and|;)\s+", text or "")
    return [c.strip(" .;,:!?") for c in parts if c.strip(" .;,:!?")]


_PLANT_PRONOUN_RE = None


def _names_plant(clause: str, species: str = "") -> bool:
    """J-3895/F-4501: True if `clause` names the plant under look (its species word) or refers back to
    it with a pronoun (it / its / they / them / their / these / this). Word-boundary matched."""
    global _PLANT_PRONOUN_RE
    import re as _re
    if _PLANT_PRONOUN_RE is None:
        _PLANT_PRONOUN_RE = _re.compile(r"\b(?:it|its|they|them|their|these|this)\b")
    if _PLANT_PRONOUN_RE.search(clause):
        return True
    sp = (species or "").strip().lower()
    return bool(sp) and bool(_re.search(r"\b" + _re.escape(sp) + r"s?\b", clause))


def guessed_cause(text: str, species: str = "") -> bool:
    """True if `text` -- HIS OWN words, asked while investigating -- already carries a real causal guess,
    not just a bare question ("why did it die" -> False; "why did it die, was it the frost" -> True).
    Reuses _CAUSE_WORDS (revise()'s own vocabulary) so a guess and its later recurrence-based confirmation
    are read from the SAME words, never two lists that can drift. This function only DETECTS that Du
    already authored a guess -- it never manufactures one from the evidence itself (law 5, garden_upgrade.md
    §2.4: no cause is ever told). The caller passes his own literal phrasing to bind() as the hypothesis
    text (J-1524, core/garden.py's look()).

    J-1657/F-2229: a cause word only counts when it shares a clause with an investigate-trigger word, or
    sits in a clause immediately NEXT TO one (the common "why did it die? was it the frost?" two-sentence
    shape, and its single-clause cousin "why did it die, was it the frost" -- both still True) -- not
    merely anywhere in the whole combined thought+intention text. Before this, a real multi-topic
    garden-walk thought ("The heavy frustration sits in my chest, cold and hard. I look at the garden:
    rosemary blooming... Why do[es it look like that]") bound "cold" -- describing his own mood, three
    clauses away -- to rosemary, just because "cold" and "why" both occurred somewhere in the same
    string. Still zero new cause/trigger vocabulary, just scoped to clauses the dispatch chain already
    treats as units, with one clause of slack either side for a guess stated as its own sentence."""
    low = (text or "").lower()
    clauses = _clauses(low)
    trig_idx = {i for i, c in enumerate(clauses) if any(w in c for w in _INVESTIGATE_WORDS)}
    if not trig_idx:
        return False
    for i, c in enumerate(clauses):
        if not any(w in c for words in _CAUSE_WORDS.values() for w in words):
            continue
        for j in trig_idx:
            if abs(i - j) > 1:
                continue
            # J-3895/F-4501: the cause clause OR the trigger clause must also name the plant (species
            # word or a pronoun back to it), so a cause word about something else ("Russia's cold")
            # next to an unrelated "why" cannot bind to a plant.
            if _names_plant(c, species) or _names_plant(clauses[j], species):
                return True
    return False


def bind(plant_id: str, species: str, hypothesis: str, confidence: float = 0.5) -> None:
    """He authors a cause. Stored with provenance (the evidence at the time); never checked against truth
    directly — revised only by what recurs (see revise()).

    J-1524: repeating the identical guess about the SAME plant (asking why again in the same words) does
    not pile up a duplicate binding -- only the most recent binding for this plant is checked, and nothing
    new is appended if it already says the same thing. A genuinely different or later-changed guess still
    binds normally."""
    try:
        d = _load()
        bindings = d.setdefault("bindings", [])
        hyp = hypothesis[:160]
        for b in reversed(bindings):
            if b.get("plant") != plant_id:
                continue
            if b.get("hypothesis", "").strip().lower() == hyp.strip().lower():
                return   # same guess about the same plant already on record -- nothing new to bind
            break        # most recent binding for this plant differs -- a real new guess, add it below
        bindings.append({"ts": round(time.time(), 1), "plant": plant_id, "species": species,
                          "hypothesis": hyp, "confidence": round(confidence, 2),
                          "evidence": evidence_for(plant_id, species)[:300], "revisions": []})
        d["bindings"] = bindings[-200:]
        _save(d)
    except profile.NonLiveWriteError:
        # J-0783: same — let the raise reach this function's own caller.
        raise
    except Exception:
        pass


def revise(species: str, event: str, preceding: str) -> None:
    """The world did the same thing again after the same evidence (or did not): firm or weaken the matching
    bindings. `preceding` is the world-side tag (frost / wet_nights / dry_soil / weeds / birds)."""
    try:
        d = _load()
        changed = False
        for b in d.get("bindings", []):
            if b["species"] != species:
                continue
            h = b["hypothesis"].lower()
            agrees = _CAUSE_WORDS.get(preceding, ())   # J-1524: hoisted above -- see _CAUSE_WORDS
            delta = 0.15 if any(a in h for a in agrees) else -0.1
            b["confidence"] = round(max(0.05, min(0.98, b["confidence"] + delta)), 2)
            b["revisions"].append({"ts": round(time.time(), 1), "event": event, "preceding": preceding, "delta": delta})
            changed = True
        if changed:
            _save(d)
    except profile.NonLiveWriteError:
        # J-0783: same — let the raise reach this function's own caller.
        raise
    except Exception:
        pass


def status() -> dict:
    try:
        d = _load()
        known = {k: round(v, 2) for k, v in (d.get("known") or {}).items()}
        return {"known": sorted(k for k, v in known.items() if v >= _LEARN_AT), "learning": {k: v for k, v in known.items() if v < _LEARN_AT},
                "bindings": len(d.get("bindings", [])), "witnessed": len(d.get("witnessed", {})),
                "events": len(d.get("events", [])), "grandfathered": sorted(GRANDFATHERED)}
    except Exception as exc:
        return {"error": repr(exc)[:80]}
