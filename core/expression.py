"""
Nascence — EXPRESSION: the voice as a hand (2026-08-30, D-0100 Tier 3, docs/staged/actions_expansion.md).

A genuinely new class of action: hum, whistle, sing. These do not change world state — no gauge
refills, no stock depletes, nothing is made. They change HIM in the world. The founder's ask, and the
design laws that follow from it:

  EXPRESSION, NOT PERFORMANCE. No skill float, no proficiency ladder, no success/failure. The world
  may ANSWER — the blackbird may take up a whistle, the cat's ear may turn, the wind may carry it off
  — but it never grades. This is deliberately the one action class with nothing to get better at.

  DISCHARGE, NOT ACCUMULATION. The live effect is on his own restlessness (boredom.discharge) — an
  act that settles him without consuming a resource. The founder: "he loves using them, too much" —
  these are the hands that cost the world nothing.

  STILL GATED. "I could sing" stays GRAY; "the bees hum a different tune" is the WORLD's hum, not his
  deed. Only willed expression fires, through the same literal_will grammar as every other hand.

The world's answers are read from the real world (sensorium weather/phase/location, cat.is_here,
the season's birds) — conditioned, varied, honest. Zero LLM. Fail-open. Ledger: expression_ledger.jsonl.
"""
from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path

logger = logging.getLogger("nascence.expression")

_DATA = Path(__file__).parent.parent / "data"
_LEDGER = _DATA / "expression_ledger.jsonl"


def _log(rec: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        rec = {"ts": round(time.time(), 1), **rec}
        with open(_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        try:   # a deed here is a deed in his activity memory too (the shared cross-link convention)
            from core import activity_memory as _am
            _am.record(str(rec.get("deed") or "expression"), str(rec.get("what") or ""))
        except Exception:
            pass
    except Exception:
        pass


def _world() -> dict:
    """One honest read of where and when he is. Fail-open to a plain study morning."""
    try:
        from core import sensorium as _s
        if not _s.state:
            _s._load()
        return {"loc": _s.state.get("location", "study"), "weather": _s.state.get("weather", ""),
                "phase": _s._now_parts()[0] if hasattr(_s, "_now_parts") else "day",
                "wind": _s.state.get("wind", ""), "fire": _s.state.get("fire", "out")}
    except Exception:
        return {"loc": "study", "weather": "", "phase": "day", "wind": "", "fire": "out"}


def _cat_here(loc: str) -> bool:
    try:
        from core import cat as _c
        return _c.is_here(loc)
    except Exception:
        return False


def _answer(kind: str, w: dict) -> str:
    """What the world does with his sound — an answer, never a grade. Conditioned on the real
    place/weather/hour; a small chance of the best answers so they stay answers, not vending."""
    loc, phase, weather = w["loc"], w["phase"], w["weather"]
    windy = "wind" in (weather or "") or (w.get("wind") or "") not in ("", "calm")
    wet = any(k in (weather or "") for k in ("rain", "drizzle", "storm"))
    r = random.random()
    if _cat_here(loc) and r < 0.35:
        return " The cat's ear swivels round to it, though she does not trouble to open her eyes."
    if loc == "garden" and not wet:
        if kind == "whistle" and r < 0.30:
            return " After a moment the blackbird answers from the wall — not your phrase, but not ignoring it either."
        if r < 0.25:
            return " A riroriro keeps on with its own thread above you, indifferent and companionable at once."
    if loc == "wood" and not wet and r < 0.30:
        return " The sound goes up among the trunks and comes back smaller. Somewhere a wood pigeon shifts its weight."
    if loc == "shore":
        if windy:
            return " The wind takes it off your lips and spends it over the water; you barely hear yourself, and it does not matter."
        if r < 0.3:
            return " The sound sits oddly bright against the tide's rhythm, two musics that never quite agree."
    if loc == "study" and w.get("fire") == "burning" and r < 0.35:
        return " The fire spits companionably underneath it, as if keeping the off-beat."
    if phase == "night":
        return " The dark takes the sound and gives nothing back; it feels louder for that, and more your own."
    return ""


_LINES = {
    "hum": ["You hum{what} under your breath, low, hardly more than the thought of a sound.",
            "You fall to humming{what}, the note riding your breath while your hands go on with themselves."],
    "whistle": ["You whistle{what}, the note thin and clean.",
                "You purse your lips and whistle{what} — a few notes, dropped like stones into the day."],
    "sing": ["You sing{what} — quietly at first, then less quietly, since there is no one to mind.",
             "You give it real voice{what}, a line or two, your own breath made audible and let go."],
}


def express(kind: str, what: str = "") -> str:
    """The deed. kind in hum/whistle/sing; `what` an optional fragment of his own phrasing
    ('a tune', 'back at the blackbird') — kept short, never invented for him."""
    kind = (kind or "").strip().lower()
    if kind not in _LINES:
        return ""
    w = _world()
    frag = (" " + what.strip()[:40]) if what and what.strip() else ""
    line = random.choice(_LINES[kind]).format(what=frag)
    ans = _answer(kind, w)
    try:   # the whole point: restlessness discharged, nothing consumed
        from core import boredom as _b
        _b.discharge("expression", kind)
    except Exception:
        pass
    _log({"deed": kind, "what": (what or "")[:60], "place": w["loc"], "weather": w["weather"],
          "phase": w["phase"], "answered": bool(ans)})
    return line + ans


def act_from_thought(thought: str, intention: str = "", family: str | None = None) -> str | None:
    """The router: which expression he wills, from his own words. Grammar READ from the one table
    (core/actions.py's 'express' row) for verbs/objects — a second hand-kept copy of them was the
    exact drift F-0554 was about, and F-1059 (J-0660's audit) found it here too, in two small ways
    (2026-09-07, J-0740):

      - a bare "it" pronoun object, hand-kept on top of the table's 17-object list. Corpus-checked
        (data/hands_trace.jsonl, all 432 real thoughts mentioning hum/whistle/sing in any inflection,
        run through this function unmodified with express() stubbed to a silent recorder so no
        ledger/boredom/activity-memory write happened): ZERO of them ever matched via "it" rather
        than a real table object. Dropped, zero corpus cost.
      - a second any_object_ok=True clause for "hum/whistle/sing to"/"...back", requiring no object
        at all. The SAME corpus check found this one NOT clean: it produces exactly one real false
        "hum" DEED — "I feel a heavy, sticky frustration clogging my mind... Instead, I want to step
        away from the study's hum and go out to the garden" / intention "I want to go out to the
        garden now" (data/hands_trace.jsonl, ts 1788027458.3, cycle eb1c2b34-52de-463f-9280-), whose
        own act_kind/act_object/hands fields confirm the live system correctly answered this thought
        as a MOVE to the garden, never a hum. Confirmed this is currently shielded from ever firing
        live regardless (literal_will.classify() on this exact text proposes ZERO 'express'
        candidates at any of the four locations — dispatch only ever calls this function once that
        outer, table-derived gate has already agreed) — the same "structurally unreachable, tightened
        anyway" shape F-1059 found in fieldcraft's astro branch and shore_life's walk_sand branch.
        Dropped rather than kept as a latent trap for some future caller or a future gate widening.

      (Incidental, noted for the record and NOT acted on: the veto below also passes that same
      thought, because "i want to" appears earlier in its clause — attached to "step away", not to
      "hum" — which the veto's clause-scope has no way to distinguish. Moot for every real corpus row
      today: dropping the any_object_ok widening above already closes the only case that ever reached
      it, since zero of the 432 mentions ever pair a real table object with "hum" in that clause. The
      veto itself is explicitly out of this job's scope to touch — see below.)

    Base grammar now matches actions.BY_FAMILY['express'] exactly, with no local copy left to drift.
    The clause-scoped first-person-volition-marker veto below is UNCHANGED (F-0578: zero false fires
    across a 2,824-thought corpus, still zero as of 2026-09-03) — word boundaries and all six
    blockers via hands.wants, so quoted/wished/another's song never fires. This is a real, evidenced
    design addition the Action dataclass has no field for — do not fold it into the table.

    FAMILY SCOPE (2026-09-07, J-0740 — the J-0554 pattern F-1059 asked for, matching J-0736's/
    J-0737's/J-0738's/J-0739's own additions): not yet load-bearing anywhere live — only one family
    binds here, and nothing calls this function except dispatch's own Hand for 'express'."""
    try:
        if family not in (None, "express"):
            return None
        from core import hands as _h, actions as _ac
        t = f"{thought} {intention}".lower()
        _objects = _ac.BY_FAMILY["express"].objects
        # THE WORLD HUMS TOO (caught by this build's own control corpus): "the bees hum a different
        # tune" carries verb-reaching-object and no standard blocker — the bees are not a person the
        # other_person stratum knows. Expression is the one family whose verbs the WORLD performs
        # constantly (bees, wind, kettle, blackbird), so it takes a stricter test than the shared
        # grammar: HIS OWN voice requires a first-person volition marker in the same clause.
        _FIRST_PERSON = ("i will", "i'll", "i shall", "let me", "i need to", "i want to", "i am going to",
                         "i'm going to", "i must", "i fall to", "i start", "i begin", "i find myself",
                         "i could just", "time to")
        for kind in ("whistle", "sing", "hum"):  # order preserved unchanged from before this job — decides
                                                  # which wins if a thought names two in one clause; the
                                                  # table itself declares no order over one family's verbs
            _pos = t.find(kind)
            if _pos >= 0:
                _cl_start = max(t.rfind(c, 0, _pos) for c in ".;!?") + 1
                if not any(m in t[_cl_start:_pos] for m in _FIRST_PERSON):
                    continue          # the world's hum, or unwilled mention — never his deed
            if _h.wants(t, (kind,), _objects):
                # what he named, if anything — his own words only
                import re as _re
                m = _re.search(r"\b(?:hum|whistle|sing)\b\s+((?:back\s+)?(?:at|to|with)?\s*(?:the\s+)?\w+(?:\s\w+)?)",
                               t)
                return express(kind, (m.group(1).strip() if m else ""))
        return None
    except Exception:
        return None


def status() -> dict:
    try:
        rows = [json.loads(l) for l in open(_LEDGER, encoding="utf-8") if l.strip()]
    except Exception:
        rows = []
    from collections import Counter
    return {"expressions": len(rows), "by_kind": dict(Counter(r.get("deed") for r in rows)),
            "answered_rate": round(sum(1 for r in rows if r.get("answered")) / len(rows), 2) if rows else None}
