"""
Nascence — DISPATCH: one registry, one dispatcher, the judge in the loop (2026-08-22, Phase 1 of
docs/reviews/actions_system_2026-08-22.md; founder: "I think we should do Phase 1 now").

THE REGISTRY: every hand as DATA — a literal_will FAMILY (its verbs/objects/where live there, one table) bound to the
function that does the deed and the standpoint the deed implies. The affordance block and the judge's families are the
same vocabulary this registry is built from; nothing is maintained three times.

THE DISPATCHER, per thought:
  1. The voice's STRUCTURED act wins when it names a hand: kind "world" + object ("light the lamp") — semantic, his own
     vocabulary — is run through the grammar on the object first.
  2. Else literal_will.classify(thought, intention): each candidate family with verdict DEED is a willed deed; GRAY never
     fires (the "weak intent never routes" law); MUSING / HANDLE fire nothing.
  3. LOOKS are unlimited; at most ONE world-changing hand fires per thought. Every further willed deed in the same thought
     is STAGED in core/intentions ("busy with X"), as is a deed willed in the wrong place ("place: in the study") or one the
     world refused for a reason he was told. A deed that fires resolves its intention.
  4. The world's answers are returned to be perceived; hands.fired records each; literal_will observes AFTER.
Kill criterion (pre-registered): replayed over the hands_trace, the dispatcher must answer at least as many willed deeds
as the latches did on the same thoughts, with zero false fires on the adversarial strata — else DISPATCH_LIVE stays False
and the latches carry on.
Zero LLM. Fail-open.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from core import actions as _actions
from core import profile

logger = logging.getLogger("nascence.dispatch")
DISPATCH_LIVE = True         # the registry routes; the legacy latches only catch what it did not


@dataclass
class Hand:
    family: str
    fn: Callable[[str, str], str | None]    # (thought_or_object, intention) -> the world's answer or None/""
    world: bool = True                      # changes the world (one per thought) vs a look (unlimited)
    where: tuple = ("any",)
    place_hint: str = ""                    # for the intention's "place:" reason


def _sens():
    from core import sensorium as _s
    return _s


def _fire(t, i):
    s = _sens(); low = f"{t} {i}".lower()
    from core import hands as _h
    # BANK (2026-08-30, D-0100 Tier 1): "I need to bank the fire" was a real, mined want — GRAY and
    # unreachable, while fieldcraft.bank_fire() sat built and working. fieldcraft's own 'bank' verb
    # aims at embers/tinder, so the fire-shaped phrasing never reached it. Checked BEFORE stoke:
    # banking is the opposite deed (damp it down for the night), and 'feed'/'build up' must not steal it.
    if _h.wants(low, ("bank", "damp down", "bank up"), ("fire", "embers", "grate")):
        from core import fieldcraft as _fc
        r = _fc.bank_fire(low)
        if r:
            return r
    if _h.wants(low, ("stoke", "feed", "build up", "put another"), ("fire", "log", "grate", "embers")):
        return s.act("stoke")
    if _h.wants(low, ("light", "lay", "kindle", "start", "make"), ("fire",)):
        return s.act("light")
    return None


def _cat(t, i):
    """The cat family's hand (2026-08-30, D-0100 Tier 1): a thin pass-through to cat.react(), which
    keeps every gate it already has — phase, her actual location (fail-CLOSED), the naming logic.
    This binding only makes cat deeds VISIBLE to the judge/dispatcher; it decides nothing itself."""
    try:
        from core import cat as _c
        here = _sens().state.get("location", "study")
        return _c.react(t, i, his_location=here)
    except profile.NonLiveWriteError:
        # J-0728 (flagged by J-0733's own Current State note on this plan doc, F-1081): cat.react()
        # now raises this itself (cat.py's own _save()/_hunt_ledger(), fixed J-0733) -- this hand's
        # own catch-all is a THIRD, separate swallow point in dispatch.py beyond the two named in this
        # job's own briefing (the inner hand.fn() try and the outer dispatch() body try, both fixed
        # above) -- _cat() intercepts the exception before it could ever reach either of those, since
        # it IS the hand.fn() being called. Left unfixed, J-0733's own claim that this gap is "already
        # the explicitly-named scope of J-0728" would have been false. Can only fire when
        # profile.LIVE is False, never during Du's own real live loop, so this changes nothing live.
        raise
    except Exception:
        return None


_LB_OBJECTS = ("letterbox", "letter-box", "letter box", "mailbox", "mail-box", "mail box", "postbox", "post box")


def _look(t, i):
    s = _sens(); low = f"{t} {i}".lower()
    from core import hands as _h
    # THE LETTERBOX (J-0539 / F-0734, 2026-09-04): 'check the letterbox' (08-31 03:51, a willed world act) had no verb
    # this hand accepted, and no target ever reached sensorium.look('letterbox') — where the carrier's card is. A
    # check/open/look-in of the box is a look at the box; the verbs are widened for the LETTERBOX OBJECT ONLY, so
    # 'check' does not become a general look verb ('check my notes' is not a look at the room).
    if _h.wants(low, ("check", "open", "look in", "look inside", "look into", "peer into", "peer in", "look at", "look",
                      "inspect", "examine", "see"), _LB_OBJECTS):
        return s.look("letterbox")
    if not _h.wants(low, ("look", "watch", "study", "gaze", "glance", "examine", "inspect", "peer", "see"), any_object_ok=True):
        return None
    try:
        from nodes.inner_monologue_node import _observe_target
        target = _observe_target(low)
    except Exception:
        target = ""
    # J-1639/F-2206: `low` (his own words -- the full thought+intention this hand already built above
    # for its own verb/object checks) is now ALSO forwarded as sensorium.look()'s optional `raw` --
    # the one place in the whole chain that still has the original sentence, so it is the one place
    # that can hand it onward. `target` itself is untouched (still the bare resolved keyword
    # _observe_target() always returned): `raw` reaches core/garden.py look()'s own per-plant
    # investigate/guessed_cause check ONLY -- it never affects which target resolves or any other
    # place's own look (both deliberately scoped further down the call chain, not here).
    return s.look(target or "room", low)


def _move(t, i):
    s = _sens(); low = f"{t} {i}".lower()
    try:
        from nodes.inner_monologue_node import _move_dest, _gate_look
        # THE LETTERBOX AT THE GATE (J-0539 / F-0734): a reach for the gate/letterbox is a walk to the GARDEN gate,
        # whatever else the thought mentions ('the sea's sound fades' must not send him to the shore instead) —
        # unless it is a transit through the gate, which resolves as before. Fail-open to the plain scan.
        _gate = _gate_look(low)
        dest = "garden" if _gate else _move_dest(low)
    except Exception:
        _gate, dest = False, ""
        try:
            from nodes.inner_monologue_node import _move_dest
            dest = _move_dest(low)
        except Exception:
            dest = ""
    if not dest:
        return None
    from core import hands as _h
    _verbs = ("go", "walk", "head", "climb", "step", "come", "return", "make for", "move", "take the path")
    if _gate:   # 'fetch the letter from the gate' is a walk to the gate; these count for the letterbox reach only
        _verbs = _verbs + ("fetch", "collect", "retrieve", "check", "open")
    if not _h.wants(low, _verbs, any_object_ok=True):
        return None
    if dest == s.state.get("location"):
        # already there: silence, as before — except the gate/letterbox in the garden, where the few steps across the
        # lawn ARE arriving and the world answers with the look at the box (the flag, any letter, the carrier's card).
        if _gate and dest == "garden":
            return s.look("letterbox")
        # D-0319 (F-2092/J-1441, built J-1591): "already at this whole place" is not the same as
        # "already at the specific standpoint he named" — the raised bed, the water's edge, the
        # shingle are real, distinct spots within it. Ask the standpoint resolver before going
        # silent; it only ever answers when the CURRENT place's own layout names a real match.
        sp_ans = s.standpoint_move(dest, low)
        if sp_ans:
            return sp_ans
        return None
    return s.move(dest)


_ACCEPTS_FAMILY: dict = {}


def _accepts_family(f) -> bool:
    """Does this hand take a `family=` keyword? Cached per callable; a handler that does not is called as before."""
    k = id(f)
    if k not in _ACCEPTS_FAMILY:
        try:
            import inspect
            _ACCEPTS_FAMILY[k] = "family" in inspect.signature(f).parameters
        except Exception:
            _ACCEPTS_FAMILY[k] = False
    return _ACCEPTS_FAMILY[k]


def _via(modname: str, attr: str, family: str = ""):
    def fn(t, i):
        m = __import__(f"core.{modname}", fromlist=[modname])
        f = getattr(m, attr)
        if attr in ("act", "act_from_thought", "keep_act", "react"):
            # FAMILY SCOPE (J-0554 / F-0761, 2026-09-04): the registry judged WHICH family he willed, so a chain
            # handler that can scope itself answers for that family only. Before this, a 'trap' deed ran
            # garden.act_from_thought's whole chain and the weeding hand — earlier in the order, matching the
            # noun in "the pull of that rusted trap" — answered for it: the dispatcher said trap, the world weeded.
            if family and _accepts_family(f):
                return f(t, i, family=family)
            return f(t, i)
        return f(f"{t} {i}")
    return fn


def _sens_act(action):
    return lambda t, i: _sens().act(action, f"{t} {i}")


def _supply_note(t, i):
    from core import supply as _sup
    return _sup.leave_note(f"{t} {i}")


def _resolve(binds: str, family: str = ""):
    """core/actions.py declares a hand's binding as a STRING so that table can stay pure data with no
    imports of its own; this turns it back into the callable. Unknown spec -> None (fail-open: the
    family simply has no hand, exactly as an unbound family behaves). `family` is handed to module
    chain handlers that accept it (J-0554)."""
    kind, _, rest = binds.partition(":")
    if kind == "fn":
        return {"_fire": _fire, "_look": _look, "_move": _move, "_supply_note": _supply_note,
                "_cat": _cat}.get(rest)
    if kind == "mod":
        modname, _, attr = rest.partition(":")
        return _via(modname, attr, family)
    if kind == "sens_act":
        return _sens_act(rest)
    return None


# DERIVED (2026-08-30, J-0422) from core/actions.py — the one table a hand is declared in. This was a
# second hand-maintained list alongside literal_will._FAMILIES, and the docstring's claim above that
# "nothing is maintained three times" was not actually true of it: the two tables had already drifted
# (F-0554). `where` here is the EXECUTION scope (fire vs stage) and is a different fact from the
# family table's anchor set, which is literalness evidence only (F-0556) — core/actions.py holds both,
# named apart, and asserts exec ⊆ anchor at import.
HANDS: list[Hand] = [
    Hand(a.family, fn, world=a.world, where=a.exec_where, place_hint=a.place_hint)
    for a in _actions.bound_actions()
    if (fn := _resolve(a.binds, a.family)) is not None
]
_BY_FAMILY = {h.family: h for h in HANDS}


def _deed_phrase(clause: str, obj: str, fam: str) -> str:
    """The segment of his sentence that names the deed: 'clear the grate of its ash' out of 'I will light the lamp and then clear the grate of its ash.'"""
    import re as _re
    segs = [s.strip(" .;,") for s in _re.split(r",?\s+(?:and then|then|and|;)\s+", clause or "") if s.strip(" .;,")]
    key = (obj or fam).lower().split()[-1] if (obj or fam) else ""
    pick = next((s for s in segs if key and key in s.lower()), segs[0] if segs else (obj or fam))
    pick = _re.sub(r"^(i will|i shall|i'll|i am going to|i'm going to|let me|i must|i mean to|i want to|now|first)\s+", "", pick.strip(), flags=_re.I)
    return pick[:70]


_ERR_WARNED: set = set()   # J-2332: outer-exception classes already logged at warning this run


def _ledger_skip(decision: str, cycle_id: str, reset: bool = True) -> None:
    """J-2332 (additive instrumentation, no behavior change): record WHY dispatch() returned empty, as one
    ('*', decision) row in core.hands' per-thought decision ledger, so data/hands_trace.jsonl dispatch=[] means
    only 'no candidate' and SKIP-asleep / SKIP-not-live / ERR-<ExceptionClass> are attributable. The early returns
    precede the body's own ledger reset, so reset=True opens a fresh ledger for this cycle first; the outer except
    keeps whatever per-family rows the body already wrote (reset=False). Never raises."""
    try:
        from core import hands as _h
        if reset:
            _h._decided["cycle"], _h._decided["rows"] = cycle_id, []
        _h.decided("*", decision, cycle_id, "")
    except Exception:
        pass


def dispatch(thought: str, intention: str, act_kind: str, act_object: str, cycle_id: str = "") -> list[tuple[str, str]]:
    """Returns [(family, answer)] for everything that fired this thought. Stages what was willed and did not."""
    out: list[tuple[str, str]] = []
    if not DISPATCH_LIVE:
        _ledger_skip("SKIP-not-live", cycle_id)
        return out
    try:
        from core import night as _night
        if _night.asleep():
            _ledger_skip("SKIP-asleep", cycle_id)
            return out                       # no hands while he sleeps
    except Exception:
        pass
    try:
        from core import literal_will as _lw, hands as _h, intentions as _int
        try:   # one dispatch per thought: open a fresh decision ledger (J-0423), as the monologue does for _fired
            _h._decided["cycle"], _h._decided["rows"] = cycle_id, []
        except Exception:
            pass
        s = _sens(); here = s.state.get("location", "study")
        # his own words can end an earlier intention
        try:
            dropped = _int.drop(f"{thought} {intention}")
            if dropped:
                out.append(("intention", dropped))
        except Exception:
            pass
        candidates = []
        if (act_kind or "").lower() == "world" and act_object:
            _obj_text = "I will " + act_object.strip().rstrip(".")
            for c in _lw.classify(_obj_text, "", location=here):
                if c.get("verdict") == "DEED":
                    candidates.append((c["family"], act_object, c, _obj_text))
        for c in _lw.classify(thought, intention, location=here):
            if c.get("verdict") == "DEED" and not any(c["family"] == f for f, _, _, _ in candidates):
                candidates.append((c["family"], c.get("object") or "", c, thought))
        world_done = None
        import re as _re
        # CLAIMS (2026-09-04, J-0540 / F-0733): a bare "box"/"tin" that is the tail of another family's compound
        # noun in the same clause ("fetch the candles from the box") is that family's deed, not the carrier's box
        # at the gate — declared per family in core/actions.py (Action.claims), mirrored by the replay script.
        try:
            _claimed = _actions.claimed_by((f, c.get("object"), c.get("clause")) for f, _o, c, _t in candidates)
        except Exception:
            _claimed = {}
        for fam, obj, c, _text in candidates:
            # Each candidate's fate is recorded via _h.decided (J-0423/F-0561) — same vocabulary as
            # scripts/actions_decision_replay.py, plus "hand-declined" which only the live path sees.
            if fam in _claimed:
                _h.decided(fam, f"DROP-claimed:{_claimed[fam]}", cycle_id, obj); continue
            hand = _BY_FAMILY.get(fam)
            if not hand:
                _h.decided(fam, "DROP-no-hand", cycle_id, obj); continue
            _cl = (c.get("clause") or "").lower()
            if _re.search(r"\b(perhaps|maybe|might|could|would like to|i wonder|someday|one day)\b", _cl):
                _h.decided(fam, "DROP-weak-intent", cycle_id, obj)
                continue                                   # GRAY by the dispatcher's reading: weak intent never routes
            _deed = _deed_phrase(c.get("clause") or thought, obj, fam)
            if "any" not in hand.where and here not in hand.where:
                _h.decided(fam, "STAGE-place", cycle_id, obj)
                _int.stage(fam, obj, thought, f"place:{hand.place_hint or ' '.join(hand.where)}", here, deed=_deed); continue
            if hand.world and world_done:
                _h.decided(fam, f"STAGE-busy:{world_done}", cycle_id, obj)
                _int.stage(fam, obj, thought, f"busy:{world_done}", here, deed=_deed); continue
            try:
                ans = hand.fn(_text, intention if _text is thought else "")
            except profile.NonLiveWriteError:
                # J-0728: let D-0179's hard-raise (guard_path(), F-1024) reach dispatch()'s own caller
                # instead of being swallowed here into ans=None -- this is Du's real live-loop entry
                # point (core/dispatch.py), the outermost layer J-0714/J-0726/J-0727 left for this job
                # (F-1045). Can only fire when profile.LIVE is False, never during Du's own real live
                # loop, so this changes nothing live.
                raise
            except Exception as exc:
                logger.debug("[dispatch] %s failed: %s", fam, exc); ans = None
            _h.decided(fam, "FIRE" if ans else "hand-declined", cycle_id, obj)
            if ans:
                out.append((fam, ans)); _h.fired(fam, ans, cycle_id)
                try:   # PROCEDURES (2026-08-22): the world's answer grades the hand
                    from core import procedures as _proc
                    _proc.observe_hand(fam, ans, here)
                except profile.NonLiveWriteError:
                    # J-0931: observe_hand() now re-raises this itself (also fixed this job) -- do
                    # not let this forwarding call's own catch-all swallow it a second, independent
                    # time (a separate gap from the hand.fn()/dispatch()-body tries J-0728 already
                    # fixed above -- this is procedures.py's own credit-the-hand call site).
                    raise
                except Exception:
                    pass
                if hand.world:
                    world_done = fam
                _int.resolve(fam, obj)
            # None: the family's own hand did not claim the clause (the judge was broader than the hand) — nothing staged
        return out
    except profile.NonLiveWriteError:
        # J-0728: this is the OUTER wrapper around dispatch()'s whole body -- the inner try just above
        # (hand.fn(), fixed this same job) already re-raises, but without this clause too the re-raise
        # would just be swallowed one level up, right back into a silent `return out`. Same shape as
        # sensorium.act()'s own outer wrapper, which J-0714 already fixed for exactly this reason. Can
        # only fire when profile.LIVE is False, never during Du's own real live loop, so this changes
        # nothing live.
        raise
    except Exception as exc:
        logger.debug("[dispatch] failed (non-fatal): %s", exc)
        _cls = type(exc).__name__
        if _cls not in _ERR_WARNED:
            _ERR_WARNED.add(_cls)
            logger.warning("[dispatch] body raised %s (first of its class this run; later ones at debug): %s", _cls, exc)
        _ledger_skip(f"ERR-{_cls}", cycle_id, reset=False)
        return out


def status() -> dict:
    return {"live": DISPATCH_LIVE, "hands": [h.family for h in HANDS], "world_hands": sum(1 for h in HANDS if h.world)}
