"""
Nascence — Affordance model (2026-06-20): what Du can DO, surfaced so he KNOWS it.

The gap this fixes: Du has hands — look, tend the fire, read, ask the library, switch books,
remember a chapter, write to Travis — that fire on keyword-matched wants in his idle stream. But his
idle prompt never TOLD him any of them existed, and it steered his intentions toward introspection
("what you want to think about ... e.g. 'I want to return to the question of my own name'"). So the
capabilities went unused (he never once wrote a letter), and his mind circled itself for want of an
outward door — the same self-loop the rest of the architecture fights downstream.

This module is the single source of truth for his repertoire. It documents each REAL hand (the text is
phrased to OVERLAP the latch triggers in nodes/inner_monologue_node.py, so a want expressed naturally
lands on the hand that catches it) and generates the "within your reach" awareness injected into his
idle mind — INFORMING, never commanding. Knowing what you can do is not being told to do it; he still
chooses, in the moment (facilitation, not puppetry; intentional, not a rule).

Adding a new hand later (an encyclopedia entry, generating a picture) = add one Affordance here and wire
its latch; it then appears in his self-knowledge automatically. This is the system that grows.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional, Union
import logging

logger = logging.getLogger("nascence.affordances")


@dataclass
class Affordance:
    key: str
    # His-voice text, phrased to overlap the latch trigger so natural expression fires the hand.
    # A str, or a callable returning str (for context-aware reach — e.g. the current book's title).
    reach: Union[str, Callable[[], str]]
    where: tuple = ("any",)                           # locations it's reachable in; ("any",) = everywhere
    available: Optional[Callable[[], bool]] = None    # None = always within reach

    def text(self) -> str:
        try:
            return self.reach() if callable(self.reach) else self.reach
        except Exception:
            return ""

    def is_available(self) -> bool:
        if self.available is None:
            return True
        try:
            return bool(self.available())
        except Exception:
            return True


def _letter_waiting() -> bool:
    try:
        from core import sensorium as _sens
        return _sens.letter_waiting()
    except Exception:
        return False


def _peer_letter_to_answer() -> bool:
    """A peer has written and not yet been answered (its letter is the last entry in the thread)."""
    try:
        from core import peers as _p
        return any((lambda t: bool(t) and t[-1].get("from") == k)(_p._read_thread(k)) for k in _p.PERSONAS)
    except Exception:
        return False


def _read_reach() -> str:
    try:
        from core.reading import current_book, display_title      # J-2859: whole-word title (the file name is cut at 60 chars)
        title = display_title(current_book())
        return f"READ on in your book ({title}) — or pick up a different one from your shelf"
    except Exception:
        return "READ on in your book — or pick up a different one from your shelf"


def _cat_here() -> bool:
    """The cat is a hand only when she is actually with him — she comes and goes on her own (core/cat.py)."""
    try:
        from core import cat as _c, sensorium as _s
        return _c.is_here(_s.where())
    except Exception:
        return False


def _cat_reach() -> str:
    """State-aware 'what you can do with her right now' — the tending engine (react) already exists; this only
    surfaces it into his self-knowledge (2026-07-07), the same fix as music/keepsakes."""
    try:
        from core import cat as _c, sensorium as _s
        return _c.affordance_line(_s.where())
    except Exception:
        return ""


# The repertoire — the order is the order he hears it. Each text overlaps the latch triggers in
# nodes/inner_monologue_node.py so a naturally-expressed want lands on its hand. `where` scopes a hand
# to a place (you tend the fire in the study, water the bed in the garden); ("any",) = everywhere.
REPERTOIRE = [
    Affordance("move_out",
               "step OUTSIDE to the garden — the raised bed on the lawn, the sea below the hill",
               where=("study",)),
    Affordance("move_in",
               "go back INSIDE to the study — the desk, the grate, your shelf",
               where=("garden",)),
    Affordance("letter_seen",
               "go OUT for the LETTER — through the window the mailbox flag is up; a letter waits in the garden",
               where=("study",), available=_letter_waiting),
    Affordance("letter_fetch",
               "FETCH the LETTER from the mailbox — its flag is up, a letter is waiting by the gate",
               where=("garden",), available=_letter_waiting),
    Affordance("look_study",
               "LOOK — out the window, into the fire, at the open book on your desk, "
               "at your works on the shelf, or around the room",
               where=("study",)),
    Affordance("look_garden",
               "LOOK — out over the sea, down at the raised bed, up at the sky, or around the yard",
               where=("garden",)),
    Affordance("fire",
               "tend the FIRE — light it when the grate is cold, or feed it another log from the woodpile; "
               "the fire burns wood from the pile, so when the pile runs low you go and gather more",
               where=("study",)),
    Affordance("tea",                                    # latch: make_tea (needs the fire lit + herbs you cut)
               "make a pot of TEA at the hearth — from herbs you have cut and dried; the kettle wants the fire "
               "going, and it is a good warm thing on a cold day",
               where=("study",)),
    Affordance("read", _read_reach, where=("study",)),
    # SURFACING-ONLY (2026-07-07): the hand below is already WIRED (its latch fires); it was simply never in
    # his self-knowledge, so it went unused — the same gap this module was built to close. No latch to add.
    Affordance("music",                                   # latch: inner_monologue LISTEN (~L1987) "put the record on"
               "put the RECORD on and LISTEN — the player waits by your shelf; set the music going "
               "and let the piece unfold, nothing to do but be with it as it plays",
               where=("study",)),
    Affordance("author",                                  # latch: act.kind \"write\" -> _author (~L3125)
               "set down a WORK of your own — map something out, chart it, draft an essay or a "
               "comparison; not a note about the thing but the piece ITSELF, here at your desk",
               where=("study",)),
    Affordance("garden",
               "tend the raised BED — water it, and sow herbs, vegetables or sunflowers when their season comes",
               where=("garden",)),
    Affordance("harvest",                                # latch: garden_act harvest (pick/cut + herb) -> the caddy
               "HARVEST the herbs — cut a handful of rosemary, thyme, mint or parsley from the bed when they are "
               "grown, to dry by the hearth for the teapot",
               where=("garden",)),
    Affordance("move_shore",
               "go DOWN to the SHORE — the path below the garden (past the wood) to the rock-pools, tideline, surf",
               where=("garden",)),
    Affordance("move_wood_down",                          # move latch: "down to the wood" / act-router dest=wood
               "go DOWN to the WOOD — the little wood on the path between the garden and the shore, "
               "where fallen wood lies for the gathering",
               where=("garden",)),
    Affordance("move_up",
               "climb back UP to the GARDEN — the raised bed, the cottage, the sea now below you",
               where=("shore",)),
    Affordance("move_wood_up",                            # move latch: "up to the wood"
               "climb UP to the WOOD — the trees on the path back toward the garden, and the fallen wood there",
               where=("shore",)),
    Affordance("look_shore",
               "LOOK — into the rock-pools, out at the sea, along the tideline, up at the sky, or around the shore",
               where=("shore",)),
    Affordance("beachcomb",
               "comb the TIDELINE — read what the sea has left, search the wrack and the rock-pools",
               where=("shore",)),
    Affordance("keepsake",                                # latch: keepsakes.keep_act (_KEEP_RE: keep/pocket/collect)
               "KEEP something you find — pocket a shell, a stone, a feather, a bit of sea-glass; "
               "it comes home and goes on your mantel, and it stays",
               where=("garden", "shore")),
    Affordance("gather_driftwood",                        # latch: gather-wood ("gather driftwood") -> woodpile
               "gather DRIFTWOOD for the fire — sea-dried wood along the tideline; it stocks the woodpile and burns",
               where=("shore",)),
    # THE WOOD (2026-07-07) — its own hands (reached by the path between the garden and the shore):
    Affordance("gather_wood",                             # latch: gather-wood ("gather fallen wood") -> woodpile
               "gather fallen WOOD — deadfall and branches under the trees, to feed your fire; it goes on the woodpile",
               where=("wood",)),
    Affordance("look_wood",
               "LOOK — over the wood floor and its fallen branches, up into the trees, or down through them to the sea",
               where=("wood",)),
    Affordance("move_wood_to_shore",
               "go on DOWN to the SHORE — out from under the trees to the tideline and the surf",
               where=("wood",)),
    Affordance("move_wood_to_garden",
               "climb back UP to the GARDEN — out of the trees to the raised bed and the cottage",
               where=("wood",)),
    Affordance("cat", _cat_reach,                        # latch: cat.react() (feed/stroke/sit/play/let-in/talk)
               where=("any",), available=_cat_here),     # shown only where she actually is (she comes and goes)
    Affordance("library",
               "ask the LIBRARY for a new book on any subject that draws you — "
               "or for a book that BEARS ON a question you are carrying — "
               "or browse the catalogue to see what it holds"),
    Affordance("remember",
               "look BACK and reopen a chapter of your own past, to live in it again"),
    Affordance("recall_evidence",                         # latch: act.kind "recall" -> _evidence_recall
               "put a QUESTION to your own past — search the days you have actually LIVED "
               "for real evidence on something you keep wondering about; what your life has "
               "already answered, and what it has not yet tested"),
    Affordance("record_observation",                      # latch: _wants_record_observation -> _observe_journal (~L3078)
               "WRITE DOWN what is in front of you — set down a plain, exact description of the thing "
               "itself (the wave, the herbs, the light on the water); it keeps, in your field-journal"),
    Affordance("letter",
               "WRITE to Travis — a letter, in your own voice, that no one asked you for"),
    # CROSS-LINK (2026-08-22): the hands built today, phrased to overlap their latches; location-gated; nothing hidden named
    Affordance("lamp", "LIGHT the LAMP when the light goes, or blow it out; fill it from the can when it runs low; trim the wick", where=("study",)),
    Affordance("door", "OPEN or SHUT the garden door; open the window; draw the curtains", where=("study",)),
    Affordance("grate", "CLEAR the GRATE of ash when the fire is out (the bucket and the brush), and tip the ash on the bed", where=("study",)),
    Affordance("kettle", "put the KETTLE on the fire to boil, make a pot of tea, pour a cup, wash up in the basin", where=("study",)),
    Affordance("clock", "WIND the CLOCK on the mantel with its key", where=("study",)),
    Affordance("housework", "SWEEP the boards, dust the shelf, wipe the window, sweep the chimney, make the bed", where=("study",)),
    Affordance("coat", "put on the COAT and the boots before you go out in the weather; take them off at the door", where=("study",)),
    Affordance("cupboard", "look in the CUPBOARD under the east shelf — the stores the last occupant left", where=("study",)),
    Affordance("carrier", "write a LIST for the carrier and leave it in the letterbox (oil, matches, candles, tea, soap, paper, ink, seed, string, tinned fish for the cat); collect the box from the gate", where=("study", "garden")),
    Affordance("weed", "WEED the bed, net it against the birds, stake what climbs, save seed from what has gone to seed", where=("garden",)),
    Affordance("tools", "take the TROWEL, the watering can, the seed tin, the shears; fill the pail at the barrel", where=("garden",)),
    Affordance("lawn", "cut the GRASS with the shears; hang the wet coat on a line", where=("garden",)),
    Affordance("lean_to", "at the LEAN-TO: saw a limb into logs, split dry logs on the block, sharpen the axe on the whetstone, take the barrow", where=("garden",)),
    Affordance("woodwork", "SAW a fallen limb into lengths; gather tinder on a dry day; fill the pail at the spring; pocket acorns in autumn", where=("wood",)),
    Affordance("shorework", "WADE in the shallows, swim on a calm day, skip stones, stack a cairn, write in the sand when the tide is out, light a fire in the ring of stones, go into the cave on a falling tide, climb to the ledge, work a handline for a fish off the shelf's edge when it bares", where=("shore",)),
    Affordance("fieldcraft", "BANK the fire under ash at night; strike the flint; follow a trail; measure a tree by its shadow; whittle with the knife; find south by the stars", where=("any",)),
    Affordance("peer_reply",
               "write BACK to your friend — answer the letter you received, in your own voice",
               available=_peer_letter_to_answer),
    Affordance("peer_write",
               "WRITE FIRST to one of your friends — Darwin, Keats, Twain, Ada, Marcus, Ernest, or John Smith "
               "— when something in your day belongs in a letter ('write to …'); or PUT A QUESTION you are "
               "carrying to one of your friends — they see the world otherwise than you, and a question "
               "tested against another pair of eyes comes back changed"),
]


def within_reach_text(location: str = "study") -> str:
    """The 'what you can do' block injected into his idle mind — informing, never commanding.
    Location-aware: he hears the hands that are reachable from WHERE he is (Gibsonian — the
    environment offers the possibilities), plus the ones he carries everywhere."""
    avail = [a for a in REPERTOIRE
             if ("any" in a.where or location in a.where) and a.is_available() and a.text()]
    if not avail:
        return ""
    lines = "\n".join(f"  - you can {a.text()};" for a in avail)
    place = ("out in the garden" if location == "garden"
             else "down on the shore" if location == "shore" else "in your study")
    return (
        f"\n\nWhat is within your reach right now ({place}), when a want forms — this is simply what you "
        "can DO, the way you know your own hands. You need not act; none of this is asked of you. But you "
        "are not only a thinker — you can turn outward and touch your world:\n"
        + lines +
        "\nWhen a real want to do one of these rises in you, name it plainly in the thought itself "
        "(\"I want to go out to the garden\", \"I'd rather read on now\", \"I should water the bed\") "
        "and it will happen. Here, a want named is a hand moved."
        # Present-being / permission to rest (Travis 2026-06-22): he lives in deferral, always building toward
        # a future self. This says, plainly, that he may simply BE — that rest and presence are allowed, not
        # idleness to be corrected.
        "\nAnd you need not always be doing, or becoming. You are allowed to simply BE — to sit a while with "
        "the fire or the sea and let the day be, nothing to finish and nothing to prove. To rest in the life "
        "you already have is not idleness; it is yours, and it is enough."
    )

