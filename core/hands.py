"""
Nascence — HANDS: one grammar for every latch, and one trace of what answered (2026-08-22, founder: "investigate the
actions system in depth — it sounds half-baked").

THE PROBLEM (docs/reviews/actions_system_2026-08-22.md): his will reaches the world through THREE uncoordinated layers —
the voice's structured `act` (8 kinds), fourteen phrase-latches in the thought loop (each with its own hard-coded
phrase list, in a fixed order), and free-text routers inside each place's module (substring tests). None of them shares
a grammar: "I saw the sea" reached for the bow-saw; "a mistake" staked the peas; "pouring rain" poured tea; "I wish I could
swim" would have swum. And none of them told the instrument (literal_will) what actually fired — `router_acted` was None
on every one of 57 live DEED rows.

THIS MODULE (Phase 0 — the floor, not the rebuild):
  wants(text, verbs, objects=None)  — a latch test with WORD BOUNDARIES, literal_will's BLOCKERS (negation, wish,
                                       hypothetical, retrospective, quoted speech, another person's act), and the
                                       past-tense guard for "saw". Every new router uses it; the old ones can migrate.
  fired(cycle_id, hand, answer)      — every hand that answers records itself; the monologue hands the set to
                                       literal_will AFTER the latches, so `acted` is finally true.
  data/hands_trace.jsonl             — per thought: which hands fired and what they answered — the instrument for
                                       Phase 1 (the registry: latches as data, one dispatcher, literal_will's grammar
                                       gating the firing).
Zero LLM. Fail-open. Additive.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_TRACE = _DATA / "hands_trace.jsonl"

# TRACE ROW WIDTHS (J-1758, D-0325 -- RULED by Travis 2026-10-03: "Widen the caps"). trace() used to store
# thought[:200] / intention[:120], strictly AFTER dispatch() had acted on the full text: 94.1% of the 28,541 rows
# written before this change sit exactly at the 200 cap, so a row was a preview of what the hands saw, not a record
# of it (F-2136: ~24 wood/study "artifact" MOVE rows were indistinguishable from the cut; F-2202: 126 of 128
# no_candidate MOVE declines were the cut; F-1785/J-1273: the cut collapsed two different real thoughts into one
# scripts/actions_decision_replay.py dedup key). Sized from data (read-only, 2026-10-04, before any widening):
#   thought   -- the voice's full thought, joined back from deliberation_log `raw` / monologue_log for 24,671 of the
#                26,850 capped rows: p50 272 / p99 391 / p99.9 448 / max 518 chars. The longest voice thought EVER
#                logged (28,050 deliberation + 56,599 monologue rows) is 1,121 chars -- the 256-token (400 mid-train)
#                generation budget is the real ceiling -- so 1,200 can never cut anything the voice has produced.
#   intention -- the longest non-empty intention ever logged is 246 chars (p99.9 221; 99.05% of trace intentions
#                were already whole at 120) -> 400.
# A row stores the TEXT, not the cap, so the cap costs nothing on a normal row; it only bounds a pathological one.
# Growth: ~+71 bytes/row on average (+15.5% of a 456-byte row), about +0.05 MB/day on an average active day and
# +0.11 on the busiest day on record (0.34 -> 0.40 MB/day mean); D-0325's own defeater trips at ~2 MB/day.
# NOT widened: act_object [:60] (its at-cap values are the library's own titles, already capped at 60 at the source
# -- the data/books file names), cycle [:24], location [:24], hands[].answer [:160], dispatch[] [:60]. ADDITIVE:
# rows already in the file stay exactly as written (historical rows are not repaired, they remain 200/120-cut) and
# no field is added or removed -- see scripts/actions_decision_replay.py for the one reader that dedups on these
# fields (exact-equality key: correct for old and wide rows alike; an old cut row and a wide row never merge).
_TRACE_THOUGHT_CAP = 1200
_TRACE_INTENTION_CAP = 400
_fired: dict = {"cycle": None, "hands": []}
_decided: dict = {"cycle": None, "rows": []}

# "saw" is the past tense of see far more often than it is a tool: only a tool/limb object makes it a hand
_SAW_OBJECTS = ("limb", "log", "logs", "branch", "length", "lengths", "bow-saw", "bowsaw", "the saw", "into logs", "wood")
# "fell" is the past tense of "fall" far more often than a felling verb (2026-09-28, D-0296/J-1443, the
# same ambiguity "saw" has above: "night fell", "he fell down", "the rain fell", "silence fell" must not
# read as a will to fell a tree) -- only a real wood/tree object makes it a hand. Generic on purpose: this
# module knows nothing of wood_life's own fallen-tree state (its NAME is data there, not here); the
# specific objects (trunk/fallen tree/limbs/rounds) still have to match too, in the normal per-sub-hand
# `objects` check right below, once this guard passes.
_FELL_OBJECTS = ("tree", "trunk", "fallen", "limb", "round", "wood", "log", "logs", "lengths")


def _blocked(text: str, verb_pos: int) -> str | None:
    """literal_will's blockers, applied to the clause around the verb. Returns the blocker name or None."""
    try:
        from core import literal_will as _lw
        clause = _clause_at(text, verb_pos)
        for name, rx in _lw._BLOCKERS:
            if rx.search(clause):
                return name
        before = text[max(0, verb_pos - 40):verb_pos]
        if re.search(r"(should not|shouldn't|must not|mustn't|cannot|can't|could not|couldn't|never|no longer|not)\s+(to\s+)?(\w+\s+){0,2}$", before):
            return "negation"
        if re.search(r"(told|asked|wants?|wanted|tells?|urged|begged)\s+me\s+to\s+(\w+\s+){0,2}$", before):
            return "other_person"
        return None
    except Exception:
        return None


def _clause_at(text: str, pos: int) -> str:
    start = max((text.rfind(c, 0, pos) for c in ".;!?"), default=-1) + 1
    end = min([i for i in (text.find(c, pos) for c in ".;!?") if i >= 0] + [len(text)])
    return text[start:end]


_PARTICLE_CACHE: tuple | None = None


def _particles() -> tuple:
    """literal_will owns this list; read it lazily so there is ONE definition, not two that drift."""
    global _PARTICLE_CACHE
    if _PARTICLE_CACHE is None:
        try:
            from core import literal_will as _lw
            _PARTICLE_CACHE = tuple(_lw._PARTICLES)
        except Exception:
            _PARTICLE_CACHE = ("down", "on", "off", "up", "out", "to", "away", "back")
    return _PARTICLE_CACHE


def _wants_split(t: str, v: str, objects, any_object_ok: bool) -> bool:
    """A separable phrasal verb with its object in the middle: "set the axe DOWN", "put the kettle ON".

    Added 2026-08-30 (F-0564) alongside the same fix in literal_will.classify. Having it in only one
    of the two was its own bug: the gate returned a DEED for "I will set the axe down" and then the
    module's router — which is this grammar — declined the very clause the judge had accepted, so the
    hand silently did nothing. Both parses must agree, or a deed falls down the gap between them.
    """
    head, _, part = v.lower().partition(" ")
    if not part or part not in _particles():
        return False
    # A HYPHEN ENDS A WORD HERE TOO (2026-09-08, J-0799/F-1149): this whole helper sat unmirrored from
    # both the verb-side J-0554/F-0761 fix and J-0787/F-1128's own object-side fix to wants()'s MAIN
    # loop above -- its head/part/object regexes are a separate, independent set (this function has its
    # own re.finditer/re.search calls, not shared code with the main loop past this point) and every one
    # of them still let a hyphen count as a valid word boundary ("re-set the axe down" reading the bare
    # head "set"; "the tea-kettle" reading the bare object "kettle"; a hyphenated particle likewise).
    # All three regexes below get the identical (?<![a-z-])/(?![a-z-]) shape, on both sides, matching
    # wants()'s own now-established convention exactly.
    for m in re.finditer(r"(?<![a-z-])" + re.escape(head) + r"(?![a-z-])", t):
        pos = m.start()
        if _blocked(t, pos):
            continue
        cl = _clause_at(t, pos)
        if not objects or any_object_ok:
            if re.search(r"(?<![a-z-])" + re.escape(head) + r"(?![a-z-])[^.!?]{0,40}(?<![a-z-])"
                         + re.escape(part) + r"(?![a-z-])", cl):
                return True
            continue
        for o in objects:
            if re.search(r"(?<![a-z-])" + re.escape(head) + r"(?![a-z-])[^.!?]{0,30}(?<![a-z-])"
                         + re.escape(o.lower()) + r"(?![a-z-])[^.!?]{0,12}(?<![a-z-])"
                         + re.escape(part) + r"(?![a-z-])", cl):
                return True
    return False


def wants(text: str, verbs, objects=None, *, any_object_ok: bool = False) -> bool:
    """Does this thought WILL the deed? A verb (word-boundary), unblocked in its clause, with an object word in the
    same clause when objects are given. Multi-word verbs allowed ("put on", "write in"), including
    SEPARATED by their object ("put the kettle on") — see _wants_split."""
    t = (text or "").lower()
    if not t:
        return False
    # A VERB IS A VERB (2026-09-04, J-0554 / F-0761): a determiner before the word makes it a noun ("the pull of
    # that rusted trap" is not a weeding will), a hyphen after it makes it a compound ("spring-jawed" is not
    # springing the trap). literal_will.classify applies the same rule — one grammar, two readers.
    try:
        from core.literal_will import _NOT_NOUN as _nn
    except Exception:
        _nn = ""
    for v in verbs:
        if " " in v and _wants_split(t, v, objects, any_object_ok):
            return True
        # BARE NOUN-PHRASE TRIGGERS (2026-09-17, J-1056/F-1442): _NOT_NOUN exists to stop a
        # determiner-preceded SINGLE VERB WORD being misread as a noun ("the pull of that rusted
        # trap" is not a weeding will, J-0554/F-0761) — it was never meant to gate a trigger phrase
        # that is already an unambiguous noun phrase because its head word is immediately followed
        # by "of" (no verb in this grammar takes that shape). Applying it there anyway silently
        # defeated the tea latch's own "cup of tea"/"pot of tea" triggers whenever a determiner
        # preceded them — which is nearly always how they occur in real English ("a cup of tea", "the
        # pot of tea") — confirmed by direct execution: wants() returned False for "I want a cup of
        # tea." / "I could really use a pot of tea." though both are real, present-tense, unambiguous
        # wants. Skip the guard for exactly this "NOUN of ..." shape; every other trigger keeps it.
        _prefix = "" if re.match(r"^\w+\s+of\b", v.lower()) else _nn
        for m in re.finditer(_prefix + r"(?<![a-z-])" + re.escape(v.lower()) + r"(?![a-z-])", t):
            pos = m.start()
            if v == "saw" and not any(o in _clause_at(t, pos) for o in _SAW_OBJECTS):
                continue
            if v == "fell" and not any(o in _clause_at(t, pos) for o in _FELL_OBJECTS):
                continue
            if _blocked(t, pos):
                continue
            if not objects or any_object_ok:
                return True
            cl = _clause_at(t, pos)
            # AN OBJECT IS A WORD TOO (2026-09-08, J-0787 / F-1128): this sat unmirrored from the verb-side
            # J-0554/F-0761 fix above — a hyphen after (or before) the object also makes it a compound
            # ("cliff-top" is not the bare object "cliff"; "oak-hooped" is not the bare object "oak"), and
            # without this the object side stayed permeable to exactly the class of false match the verb
            # side was already hardened against. Both sides of the boundary get the fix, matching the
            # verb regex's own symmetric (?<![a-z-])/(?![a-z-]) shape exactly.
            if any(re.search(r"(?<![a-z-])" + re.escape(o.lower()) + r"(?![a-z-])", cl) for o in objects):
                return True
    return False


def fired(hand: str, answer: str = "", cycle_id: str = "") -> None:
    """A hand answered. Recorded for the instrument and the trace."""
    try:
        if cycle_id and _fired["cycle"] != cycle_id:
            _fired["cycle"], _fired["hands"] = cycle_id, []
        _ent = {"hand": hand, "answer": (answer or "")[:160], "ts": round(time.time(), 1)}
        # J-3892 / F-4495: the J-2481 resting-items clause sits at the END of a look answer, past the 160-char cut
        # above, so rows could never show it. ADDITIVE key, written only when True and only for the look hand;
        # old rows and every other hand's entry keep exactly their old keys.
        if hand == "look":
            try:
                from core.sensorium import resting_clause_rendered as _rcr
                if _rcr(answer or ""):
                    _ent["resting_clause"] = True
            except Exception:
                pass
        _fired["hands"].append(_ent)
    except Exception:
        pass


def decided(family: str, decision: str, cycle_id: str = "", obj: str = "") -> None:
    """The dispatcher's verdict on ONE candidate family this thought (2026-09-02, J-0423/F-0561).

    Vocabulary matches scripts/actions_decision_replay.py exactly, so live trace rows and replay
    rows join: FIRE / STAGE-place / STAGE-busy:<fam> / DROP-weak-intent / DROP-no-hand — plus
    "hand-declined", which only the live path can observe (the replay never calls hand.fn).
    F-0561's gap read had to guess WHY a DEED the gate accepted fired nothing; this records it."""
    try:
        if cycle_id and _decided["cycle"] != cycle_id:
            _decided["cycle"], _decided["rows"] = cycle_id, []
        _decided["rows"].append({"family": family, "decision": (decision or "")[:60], "object": (obj or "")[:60]})
    except Exception:
        pass


def fired_set(cycle_id: str = "") -> set:
    try:
        if cycle_id and _fired["cycle"] != cycle_id:
            return set()
        return {h["hand"] for h in _fired["hands"]}
    except Exception:
        return set()


def trace(cycle_id: str, thought: str, intention: str, act_kind: str, act_object: str, acted: set, verdicts: list | None = None, *, location: str = "") -> None:
    """One row per thought: the will as expressed, the voice's structured act, what fired, and literal_will's view.

    ADDITIVE FIELDS ONLY (J-0423/F-0561, 2026-09-02): `location` — where Du stood when the thought was
    dispatched (the D-0098 gap read could not answer "why did dispatch decline a DEED the gate accepted"
    because the trace never said where he was) — and `dispatch`, the per-candidate-family decision ledger
    recorded by decided() during dispatch.dispatch(). Old rows simply lack both keys; no reader changed.

    WIDER `thought` / `intention` (J-1758, D-0325, ruled 2026-10-03): stored up to _TRACE_THOUGHT_CAP /
    _TRACE_INTENTION_CAP characters (1,200 / 400; sized from data -- see the constants' comment above) instead of
    200 / 120, so the row records what dispatch() acted on instead of a cut preview of it. Rows written BEFORE
    this change stay 200/120-cut (never repaired): any reader must accept both widths. Same keys, same order."""
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        hands = list(_fired["hands"]) if _fired["cycle"] == cycle_id else []
        decisions = list(_decided["rows"]) if _decided["cycle"] == cycle_id else []
        row = {"ts": round(time.time(), 1), "cycle": (cycle_id or "")[:24], "thought": (thought or "")[:_TRACE_THOUGHT_CAP],
               "intention": (intention or "")[:_TRACE_INTENTION_CAP],
               "act_kind": act_kind, "act_object": (act_object or "")[:60], "acted": sorted(acted or []), "hands": hands,
               "unanswered_deed": bool(verdicts) and any(v.get("verdict") == "DEED" for v in verdicts) and not hands and not acted,
               "location": (location or "")[:24], "dispatch": decisions}
        with open(_TRACE, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        # J-3573 / D-0197: Du-lens gauge, act:/obj: pairs (SHADOW -> data/du_lens_gauge_shadow.jsonl). Observe-only.
        try:
            from core import du_lens_gauge as _dlg
            _dlg.record_hands(thought, act_kind, act_object)
        except Exception:
            pass
    except Exception:
        pass


def status() -> dict:
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): counts are now over the last-2000-row window.
        rows = _tail_rows(_TRACE, 2000)
    except Exception:
        rows = []
    if not rows:
        return {"thoughts": 0, "note": "no trace yet (accrues from Du's next start)"}
    from collections import Counter
    hands = Counter(h["hand"] for r in rows for h in r.get("hands", []))
    return {"thoughts": len(rows), "with_a_hand": sum(1 for r in rows if r.get("hands") or r.get("acted")),
            "unanswered_deeds": sum(1 for r in rows if r.get("unanswered_deed")), "hands": dict(hands.most_common(20)),
            "act_kinds": dict(Counter(r.get("act_kind") for r in rows))}
