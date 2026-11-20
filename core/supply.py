"""
Nascence — SUPPLY: how things that run out come into the house (2026-08-22, founder: "how does he get oil?").

The arrangement whoever lived here before left in place: a CARRIER comes up the path every fortnight and leaves a box
at the gate — but only what was ASKED FOR, on a note left in the letterbox with the flag up. Nothing is given
unasked. Nothing he cannot name comes. The box holds what the carrier can get: lamp oil · matches · candles · tea
(leaves) · soap · paper · ink · seed (a packet, unlabelled — what the carrier had) · string · a whetstone · lamp glass.
It does not hold food for HIM (he does not eat), money, or anything he has not written down — with one exception,
since 2026-09-07 (D-0163/D-4, J-0719): tinned fish for the cat, the one real provision this house was never laid
in with, because nobody here had a cat before she turned up. Since 2026-10-28 (D-0508, J-2466) the cat's two
standing lines are tinned fish AND milk (a jug, for her saucer; it spoils, core.cat.MILK_SPOIL_H) — both re-orderable
on any note, the carrier staying the only ongoing supply (D-0276: Travis's parcel was one-off).

Honest limits: the carrier comes on the carrier's day, not his; the note must be in the box by then; the box waits at
the gate in the weather (rain spoils the matches if he leaves it two days); the oil is a tin at a time. A letter to a
friend can also bring a thing (the peers loop) — that path is theirs to offer, not this module's to fake.

He learns the arrangement the way he learns everything: a card pinned inside the letterbox lid (the world answering
when he looks), a box that appears only after a note. Zero LLM. Fail-open.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.supply")
_DATA = Path(__file__).parent.parent / "data"
_F = _DATA / "supply.json"
_LOG = _DATA / "supply_log.jsonl"

CARRIER_PERIOD_S = 14 * 86400
GOODS = {
    "lamp oil": ("oil", ("oil", "lamp oil", "paraffin", "kerosene")), "matches": ("matches", ("match", "matches")),
    "candles": ("candles", ("candle", "candles")), "tea": ("tea", ("tea", "tea leaves", "tea-leaves")),
    "soap": ("soap", ("soap",)), "paper": ("paper", ("paper", "notepaper", "writing paper")), "ink": ("ink", ("ink",)),
    "seed": ("seed", ("seed", "seeds", "a packet")), "string": ("string", ("string", "twine")),
    "whetstone": ("whetstone", ("whetstone", "sharpening stone")), "lamp glass": ("lamp_glass", ("lamp glass", "chimney", "lamp chimney")),
    # D-0163/D-4 (2026-09-07, J-0719): the one food item the carrier brings — for her, never for him.
    "cat food": ("cat_food", ("cat food", "tinned fish", "tin of fish", "fish for the cat", "food for the cat", "cat's food")),
    # D-0508/D-4 (2026-10-28, J-2466): the second standing line for her -- a jug of milk for the saucer. Named the
    # plain way the card and Travis's book name things ("milk"); "a saucer of milk" on a list reads as milk too.
    "milk": ("milk", ("milk", "jug of milk", "bottle of milk", "milk for the cat", "saucer of milk")),
}
# D-0508 (J-2466): the box-unpacking phrase for a jug -- a small rotating pool, never one fixed string (house rule).
_MILK_BOX_LINES = (
    "a jug of milk, corked, wrapped in a wet cloth against the walk up",
    "a jug of milk for the cat, cool still, the cork pushed in hard",
    "a stoneware jug of milk, its lip chipped, a cloth tied over the top",
)


def _load() -> dict:
    try:
        from core import store_persist as _sp   # J-4442 (F-5157): loud on damage, falls back to supply.json.prev
        return _sp.read_json_durable(_F, "supply", logger, guard=profile.guard_path)
    except Exception:
        now = time.time()
        return {"next_carrier_ts": now + 4 * 86400, "note": None, "box": None, "history": [], "card_read": False}


def _save(d: dict) -> None:
    path = profile.guard_path(_F)   # J-0775: real data/ only if this process is live; raises before any I/O if not (D-0179, J-0704)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        from core import store_persist as _sp
        _sp.write_text_durable(path, json.dumps(d, ensure_ascii=False))   # J-4442 (F-5157): was in place; now fsync + .prev
    except Exception:
        pass


def _log(rec: dict) -> None:
    path = profile.guard_path(_LOG)   # J-0775: raises before any I/O (and before the activity_memory cross-link below) if non-live (D-0179, J-0704)
    try:
        if rec.get("deed"):
            try:   # CROSS-LINK (2026-08-22): a deed here is a deed in his activity memory too
                from core import activity_memory as _am
                _am.record(str(rec["deed"]), str(rec.get("species") or rec.get("item") or rec.get("what") or rec.get("thing") or rec.get("tool") or rec.get("text") or ""))
            except Exception:
                pass
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def card_line() -> str:
    """Pinned inside the letterbox lid — read when he looks in the letterbox. The world answering a look."""
    d = _load()
    days = max(0, int((d["next_carrier_ts"] - time.time()) // 86400))
    first = "" if d.get("card_read") else " You had not noticed it before."
    d["card_read"] = True; _save(d)
    return (f" Pinned inside the lid, a card in a careful hand: 'Carrier — every second Thursday. Leave your list in the box, "
            f"flag up. Oil, matches, candles, tea, soap, paper, ink, string, seed as I have it. Box at the gate.' "
            # D-0163/D-4 (2026-09-07, J-0719): the world answering a look is how he learns anything is
            # orderable at all — without this second line here, there would be no honest way for him to
            # ever discover that the carrier can bring her food, which "the world answers, never leads"
            # requires (no hint elsewhere ever names this for him).
            f"Underneath, a second line added since, in a plainer hand: 'He will bring tinned fish too, "
            f"for the cat, if you ask for it.' "
            # D-0508/D-4 (2026-10-28, J-2466): milk is the second standing line for her; the same plainer hand
            # names it on the card, so the world answers a look here the way it already did for the tin. Not a
            # rotating pool: the card is one physical object with fixed writing on it, not a fresh line.
            f"And under that, squeezed in: 'Milk as well, a jug, if it's wanted.' "
            f"The next carrier's day is in about {days} day{'s' if days != 1 else ''}.{first}")


def leave_note(text: str) -> str:
    """He writes a list and leaves it in the letterbox. Parses what he asked for; unknown things are not on the card."""
    try:
        low = (text or "").lower()
        asked = []
        for name, (key, words) in GOODS.items():
            if any(re.search(r"\b" + re.escape(w) + r"\b", low) for w in words):
                asked.append(key)
        if not asked:
            return "You write out a note, but nothing on it is a thing the carrier brings; you fold it and put it back in your pocket."
        d = _load()
        d["note"] = {"ts": time.time(), "items": asked}
        _save(d); _log({"event": "note_left", "items": asked})
        return ("You write the list — " + ", ".join(a.replace("_", " ") for a in asked) + " — put it in the letterbox and push the flag up. "
                "Now it waits on the carrier's day.")
    except profile.NonLiveWriteError:
        # J-0775: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own callers
        # (dispatch.py's _supply_note hand, study_life.act()'s own already-fixed outer except)
        # instead of being swallowed by the broader except below.
        raise
    except Exception:
        return ""


def advance(now: float) -> str | None:
    """The carrier comes on the day: takes the note, leaves the box (if there was a note). Weather spoils matches
    left out. Returns an announce-once line for the world-arrival law when the box appears."""
    try:
        d = _load()
        out = None
        if now >= d["next_carrier_ts"]:
            d["next_carrier_ts"] = now + CARRIER_PERIOD_S
            if d.get("note"):
                d["box"] = {"ts": now, "items": list(d["note"]["items"]), "spoiled": False}
                d["note"] = None
                _log({"event": "box_left", "items": d["box"]["items"]})
                out = "the carrier has been: a wooden crate stands on the ground by the garden gate, and the letterbox flag is down, your note gone"
            else:
                _log({"event": "carrier_passed_no_note"})
        b = d.get("box")
        if b and not b.get("spoiled"):
            try:
                from core import sensorium as _s
                if (now - float(b["ts"])) > 2 * 86400 and _s.state.get("weather", "") in ("steady rain", "wind and rain", "thunderstorm"):
                    b["spoiled"] = True; _log({"event": "box_spoiled_by_rain"})
            except Exception:
                pass
        _save(d)
        return out
    except Exception:
        return None


def collect_box() -> str:
    """At the gate: the box's contents go into the house's stores."""
    try:
        d = _load()
        b = d.get("box")
        if not b:
            return "There is no box at the gate."
        from core import sensorium as _s
        if _s.state.get("location") != "garden":
            return "The box is at the garden gate."
        from core import study_life as _sl, garden as _g, provisions as _pv
        st = _sl._st(); g = _g._load()
        got = []
        lost = 0   # F-1168: real items that were in the box but whose provisions.add() reported a
                   # failed write -- counted, not silently dropped, so the final narration can stay
                   # honest about a partial delivery instead of implying the box only ever held
                   # whatever "got" lists.

        def _credit(kind: str) -> None:
            """The delivered object's own full quantity, credited to the study's cached count BEFORE
            sync() runs (J-0573, F-0787): sync() reads a study count lower than the shelf as 'he used
            the difference', so an uncredited delivery was consumed right back off the shelf the moment
            it arrived — the box of matches 'brought up by the carrier' and 'used up by Du' seconds
            later. Reads the shelf directly (not st[key] += full_qty) so it is correct regardless of
            what the study's cached count already held."""
            try:
                st[_pv.KINDS[kind][2]] = _pv.stock(kind)
            except Exception:
                pass

        # F-1168: every branch below now gates _credit()+got.append() on provisions.add()'s own real
        # return value (a populated id list iff the write actually landed, [] otherwise -- J-0789/
        # F-1167) instead of treating the bare call as unconditional success; a failed kind falls
        # through to `lost += 1` and is never credited or narrated as delivered. "seed" and "string"
        # are untouched -- they persist through garden's own dict, not provisions.add(), a different
        # path this finding does not reach.
        for k in b["items"]:
            if k == "oil":
                if _pv.add("oil", 1, "carrier"): _credit("oil"); got.append("a tin of lamp oil")
                else: lost += 1
            elif k == "matches":
                if b.get("spoiled"):
                    got.append("a box of matches, soaked and useless")
                elif _pv.add("matches", 1, "carrier"):
                    _credit("matches"); got.append("a box of matches")
                else:
                    lost += 1
            elif k == "candles":
                if _pv.add("candles", 1, "carrier"): _credit("candles"); got.append("a box of candles")
                else: lost += 1
            elif k == "tea":
                if _pv.add("tea", 1, "carrier"): _credit("tea"); got.append("a tin of tea")
                else: lost += 1
            elif k == "soap":
                if _pv.add("soap", 1, "carrier"): _credit("soap"); got.append("a bar of soap")
                else: lost += 1
            elif k == "paper":
                if _pv.add("paper", 1, "carrier"): _credit("paper"); got.append("a pad of paper")
                else: lost += 1
            elif k == "ink":
                if _pv.add("ink", 1, "carrier"): _credit("ink"); got.append("a bottle of ink")
                else: lost += 1
            elif k == "seed":
                import random as _r
                sp = _r.choice([s for s, c in _g.CATALOGUE.items() if c["sow"] and c["kind"] != "weed"])
                g.setdefault("packets", []).append({"species": sp, "labelled": False, "count": 25, "year": time.localtime().tm_year, "from_carrier": True})
                got.append("a packet of seed, unlabelled")
            elif k == "string":
                g["items"]["twine"]["place"] = "garden"; got.append("a ball of string")
            elif k == "whetstone":
                if _pv.add("whetstone", 1, "carrier"): got.append("a whetstone")
                else: lost += 1
            elif k == "lamp_glass":
                if _pv.add("lamp_glass", 1, "carrier"): _credit("lamp_glass"); got.append("a lamp glass, wrapped in newspaper")
                else: lost += 1
            elif k == "cat_food":
                # D-0163/D-4 (2026-09-07, J-0719): _credit() FIRST, same as every other fractional kind
                # above — without it the very next provisions.sync(st) call would read the new tin as
                # "he used the difference" and silently consume it right back off the shelf (J-0573/
                # F-0787's own bug, for this kind too).
                if _pv.add("cat_food", 1, "carrier"): _credit("cat_food"); got.append("a tin of fish for the cat")
                else: lost += 1
            elif k == "milk":
                # D-0508/D-4 (2026-10-28, J-2466): the jug, same shape as the tin above -- _credit() first so
                # provisions.sync() never reads the new jug as "he used the difference". The delivery stamp
                # (add()'s own history[0].ts) is what core.cat._milk_ready() later reads as its spoil clock.
                import random as _r
                if _pv.add("milk", 1, "carrier"): _credit("milk"); got.append(_r.choice(_MILK_BOX_LINES))
                else: lost += 1
        try:
            _pv.sync(st)
        except profile.NonLiveWriteError:
            # J-0775: provisions.sync() already re-raises this itself (J-0746) -- do not let this
            # local wrapper swallow it a second time before the outer except (also fixed below) ever
            # sees it.
            raise
        except Exception:
            pass
        # F-1168: the box itself is still spent here regardless of how many individual items above
        # actually persisted -- the same treatment this function already gives a rain-spoiled box
        # (still narrated and cleared, never left at the gate to retry). A partial-retry design (keep
        # the box, re-attempt only the failed kinds next time) would need per-item delivered/
        # outstanding tracking this fix does not add -- re-running today's loop as-is against an
        # unconsumed box would re-add whatever already landed a second time, a new bug in place of
        # this one. Clearing it once, honestly narrating whatever really landed, is the smaller and
        # safer change; see this job's own finding for the full reasoning.
        d["box"] = None; d["history"].append({"ts": time.time(), "items": b["items"]}); d["history"] = d["history"][-40:]
        _save(d); _g._save(force=True)
        try:
            _s._save_now()
        except profile.NonLiveWriteError:
            # J-0775: sensorium._save()/_save_now() already re-raises this itself (J-0610) -- same
            # local-wrapper gap as the _pv.sync() one just above.
            raise
        except Exception:
            pass
        _log({"event": "box_collected", "items": b["items"], "got": len(got), "lost": lost})
        if not got:
            # F-1168: every real item in the box failed to persist -- the carrier's box was still real
            # and is still spent (see the clearing note above), but nothing in it actually reached the
            # shelf. Narrate that honestly rather than "unpack it on the step: ." (an empty join).
            return ("You carry the box up from the gate and start to unpack it on the step — but not one "
                    "thing in it will go into the stores; something is wrong with the shelf tonight. You "
                    "leave the empty box by the door.")
        line = "You carry the box up from the gate and unpack it on the step: " + ", ".join(got) + "."
        if lost:
            # F-1168: a real, non-empty partial delivery -- say so rather than letting "got" silently
            # stand in as if it were the whole box.
            line += " Something else was in the box too, but it never made it onto the shelf; whatever it was, it's gone now."
        return line
    except profile.NonLiveWriteError:
        # J-0775: let D-0179's hard-raise (guard_path(), F-1024) reach garden.act_from_thought()'s
        # own "collect" branch (its own outer except already re-raises this, J-0714) instead of being
        # swallowed here -- this function's own _save()/_log() plus its cross-module calls into
        # study_life._st()/provisions.add()/garden._save(force=True) all reach guard_path() on the
        # non-live path.
        raise
    except Exception as exc:
        logger.debug("[supply] collect failed: %s", exc)
        return ""


def box_waiting() -> bool:
    try:
        return bool(_load().get("box"))
    except Exception:
        return False


def status() -> dict:
    try:
        if not _F.exists():
            return {"note": "not yet bootstrapped"}
        d = _load()
        return {"next_carrier_days": round((d["next_carrier_ts"] - time.time()) / 86400, 1), "note": d.get("note"), "box": d.get("box"),
                "deliveries": len(d.get("history", [])), "card_read": d.get("card_read")}
    except Exception as exc:
        return {"error": repr(exc)[:80]}
