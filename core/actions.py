"""
Nascence — ACTIONS: the one table every hand is declared in (2026-08-30, J-0422,
docs/staged/actions_manager_overhaul.md, founder rulings D-0096..D-0099).

WHY THIS EXISTS. dispatch.py's docstring already claimed "the affordance block and the judge's families
are the same vocabulary this registry is built from; nothing is maintained three times." It was not true:
a hand was declared in TWO hand-maintained tables — its grammar in `literal_will._FAMILIES`, its binding
and execution scope in `dispatch.HANDS` — and the drift that invites had already happened (F-0554):
  - 'tea' was declared TWICE in the _FAMILIES literal (lines 57 and 77). Python keeps the last silently,
    so the first definition's verbs were dead and "steep the tea" could not be willed.
  - three families ('author', 'letter', 'travis') had no hand at all, so a DEED verdict for them was
    dropped by dispatch with a bare `continue` — neither fired nor staged (32 real occurrences in the
    replayed trace).
This module is that one table. Both consumers now DERIVE from it, so a hand is declared once, in one
place, and the shapes that used to drift are checked at import.

THE TWO LOCATION FIELDS ARE NOT THE SAME FACT (F-0556 — this was got wrong once already, and the
old code's shared field name `where` is exactly why):
  anchor      — LITERALNESS EVIDENCE. Feeds a +0.1 confidence bonus on an already-decided DEED
                (literal_will.py:332) and the MUSING->HANDLE promotion (:336). It NEVER decides whether
                a DEED is produced, and it is NEVER an execution check.
  exec_where  — EXECUTION SCOPE. Fire here; anywhere else the willed deed is STAGED as an intention
                ("that is done in the wood or on the shore"). ("any",) means anywhere.
'gather' differing between the two is CORRECT, not drift: gathering wood is literally plausible anywhere
on the property, but it is only executable in the wood or on the shore. The invariant that does hold is
containment — exec_where SUBSET-OF anchor — and it is asserted below.

Pure data. Zero imports from core (so nothing here can go circular); bindings are declared as STRINGS and
resolved by dispatch.py, which owns the callables. Zero LLM.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

ALL_LOCATIONS = ("study", "garden", "shore", "wood")
ANYWHERE = ("any",)


@dataclass(frozen=True)
class Action:
    """One hand, declared once.

    binds — how dispatch resolves the callable:
        "fn:<name>"                 a function dispatch defines itself (_look, _move, _fire, _supply_note)
        "mod:<module>:<attr>"       core.<module>.<attr>(thought, intention)
        "sens_act:<action>"         sensorium.act("<action>", text)
        ""                          declared with NO hand — see `note` for why
    """
    family: str
    verbs: tuple
    objects: tuple
    anchor: tuple                    # literalness evidence only — never an execution check
    exec_where: tuple = ANYWHERE     # where the hand can actually fire; else STAGE
    world: bool = True               # changes the world (one per thought) vs a look (unlimited)
    gated: bool = True               # plan §10 stakes tier
    place_hint: str = ""             # the intention's "place:" reason when staged
    binds: str = ""
    note: str = ""
    # CLAIMS (2026-09-04, J-0540 / F-0733): ((family, object), ...) — a bare object word another family reads
    # as ITS thing, when it is in fact the tail of this family's compound noun in the same clause. "fetch the
    # candles from the box" is one deed: the candle BOX on the east shelf, not the carrier's box at the gate,
    # and the 'collect' candidate it also makes (fetch + 'box') is dropped, not staged at the gate. Only a
    # candidate in the SAME clause is claimed; a thought that wills two things in two sentences keeps both.
    claims: tuple = ()
    # GRAMMAR-ONLY OBJECTS (2026-09-04, J-0544 / F-0740): objects that make a candidate and can complete DEED
    # GRAMMAR (a family verb reaching them — "step out", "head back in") but do NOT, on their own, turn bare
    # volition into a deed. Only matters for an UNGATED family, where volition + any object is otherwise full
    # intent: the move table's bare 'in'/'out' made every willed clause containing the word "in" a move DEED
    # ("I will draw a few lines in ink"), which the hand then declined 86% of the time (hands_trace ledger).
    grammar_only: tuple = ()
    # CLAIMS TRIGGERS (2026-09-24, J-1296 / F-1822 / D-0271): the word set claimed_by()'s independent
    # second pass checks a to-be-claimed clause against, for a claiming family whose OWN candidate is
    # itself absent from the DEED list -- see claimed_by()'s own docstring. Defaults to `objects` when
    # empty, so a family that has not separately narrowed this from its own DEED vocabulary (every
    # family today, including 'candles' while D-0267's PART 1 stays held per D-0271) is unaffected,
    # byte-for-byte. Exists because a family whose `objects` narrows (a future PART 1) such that some
    # clause no longer completes ITS OWN deed_grammar produces NO reading there at all -- classify()
    # drops the family outright, not even GRAY (F-1822, confirmed empirically) -- so its claim on that
    # clause silently stopped firing too, freeing the family it claims from to (mis)fire on the bare
    # word instead: the exact bug class `claims` exists to close, reopened for the narrowed phrasings.
    claims_triggers: tuple = ()
    # BARE OBJECTS (2026-10-04, J-1755 / D-0271, ruled by Travis 10-03: "Restore guarded noun"): nouns this family reads
    # ONLY as the DIRECT object of one of its own verbs -- the verb, an optional determiner/quantifier and up to two
    # modifier words, then the noun ("fetch the candles", "bring a spare candle", "pick the candles up") -- and never as a
    # free-standing word elsewhere in the clause. `objects` completes deed grammar from anywhere in the verb's reach, which
    # is why a bare "matches" read "I pick up the card listing oil and matches" as a deed (F-1591/F-1792); a bare object
    # makes no reading at all unless the adjacency holds, so "the candle drips wax" / "a list of candles" read nothing and
    # "I must fetch the candles from the shelf" reads again. Consumed by literal_will.classify through
    # families()["bare_objects"] (its _bare_object_hit); empty for every other family, which reads byte-for-byte as before.
    bare_objects: tuple = ()

    @property
    def bound(self) -> bool:
        return bool(self.binds)


_S = ("study",)
_G = ("garden",)
_SH = ("shore",)
_ALL = ALL_LOCATIONS
_STUDY_ACT = "mod:study_life:act"
_GARDEN_ACT = "mod:garden:act_from_thought"

# ORDER IS LOAD-BEARING. classify() walks this table in order, dispatch walks the candidates in the order
# classify returns them, and only ONE world-changing hand fires per thought — so position decides which
# hand wins a thought that wills two. This sequence reproduces the live dict's insertion order exactly,
# including 'tea' at index 1 (a re-assigned dict key keeps its FIRST position and its LAST value, which is
# why the duplicate was invisible).
ACTIONS: tuple[Action, ...] = (
    # 'bank'/'damp down' added 2026-08-30 (D-0100 Tier 1): "I need to bank the fire" was mined from
    # the unanswered-deed rows — GRAY and unreachable while fieldcraft.bank_fire() sat built.
    Action("fire", ("light", "lay", "kindle", "stoke", "feed", "tend", "build", "bank", "damp down"),
           ("fire", "grate", "hearth", "flame", "flames", "ember", "embers", "log"),
           anchor=_S, exec_where=_S, place_hint="in the study, at the hearth", binds="fn:_fire"),
    # 'steep' restored here (F-0554): it was declared in the shadowed first 'tea' entry and lost. The rest
    # of this entry is the surviving (line-77) definition deliberately — its "put on"/"set on" replaced a
    # bare "put", which would have read "put the cup down" as a willed brew.
    Action("tea", ("put on", "set on", "boil", "make", "brew", "pour", "drink", "steep"),
           ("kettle", "tea", "pot", "cup"),
           anchor=_S, exec_where=_S, place_hint="in the study", binds=_STUDY_ACT),
    # chives/silverbeet/lettuce/radish added 2026-09-04 (J-0543, F-0738): the crops garden.harvest() actually
    # cuts (kind herb|veg in its CATALOGUE) lived only in the hand's own copy of this list, so "pick some
    # lettuce" could never be a DEED at the gate. The hand now reads THIS row (no copy); "leaves" was dropped
    # with it — its one corpus hit was "the air smells of damp earth and cut leaves".
    Action("harvest", ("harvest", "pick", "cut", "snip", "clip"),
           ("herb", "herbs", "rosemary", "thyme", "mint", "parsley", "sprig",
            "chives", "silverbeet", "lettuce", "radish"),
           anchor=_G, exec_where=_G, place_hint="out at the bed", binds=_GARDEN_ACT),
    # "lantern" added 2026-09-02 (D-0131, the Living World): the carried light. Lit and filled in the study like
    # the lamp; carried out by the take hand; it burns where he goes and is read by core/life.light_at.
    Action("lamp", ("light", "fill", "trim", "blow out", "turn down"), ("lamp", "wick", "candle", "lantern"),
           anchor=_S, exec_where=_S, place_hint="in the study", binds=_STUDY_ACT),
    Action("door", ("open", "shut", "close", "latch", "draw", "pull"),
           ("door", "window", "curtains", "curtain"),
           anchor=_S, exec_where=_S, place_hint="in the study", binds=_STUDY_ACT),
    # "draw"/"pull"/"slide" + "pan" added 2026-08-30 (F-0551) for the ash pan — the hand that works
    # while the fire is in, where clear/rake need a cold hearth.
    Action("grate", ("clear", "clean", "sweep", "rake", "draw", "pull", "slide"),
           ("grate", "ash", "hearth", "ash pan", "pan"),
           anchor=_S, exec_where=_S, place_hint="in the study", binds=_STUDY_ACT),
    Action("clock", ("wind",), ("clock",),
           anchor=_S, exec_where=_S, place_hint="in the study", binds=_STUDY_ACT),
    # "walk" added 2026-09-07 (J-0738, F-1059's follow-up): shore_life.py's own walk_sand() branch tested a
    # bare eight-phrase list with NO verb this table could see at all ("barefoot"/"bare feet" have no verb
    # whatsoever) -- structurally unreachable via classify()'s own per-family gate (which requires a TABLE
    # verb reaching a table object; literal_will._FAMILIES is this table, confirmed via `from core import
    # actions as _actions; _FAMILIES = _actions.families()` at literal_will.py:66). Corpus-checked (J-0738,
    # data/hands_trace.jsonl, 11,760 distinct thoughts, real core.hands.wants()): 10 real, DISTINCT thoughts
    # will walking onto/across the sand ("I walk where the chalky sand yields to wet grit", "I want to walk
    # barefoot across the exposed sand", "I want to walk down to the wet sand where..."), every one
    # independently confirmed by the VOICE'S OWN structured act (act_kind='move' on 9 of 10, 'observe' on
    # the 10th, act_object literally naming the sand/tideline/shore in every case) -- yet NONE of them could
    # ever produce a 'shore' DEED before this fix, at the gate or via dispatch's own synthetic act_object
    # path (deed_grammar needs a shore VERB in the clause; "walk" was not one, and 'move' family's own
    # object list has no "sand"). This is the same "hand exists, grammar table cannot see it" shape as the
    # unanswered cat-door/dig deeds that originally motivated D-0100/this whole plan -- confirmed via direct
    # evidence, not inference. "walk" is already a verb in the SEPARATE 'move' family (own object list has
    # no "sand"), so this adds no new cross-family collision on the object this job widens.
    # "catch"/"fish" added 2026-09-07 (J-0732, F-1055): docs/staged/cat_overhaul.md's own §B1 named a second
    # real food source for the cat, alongside the carrier's tin (J-0719), that this table could not see at
    # all -- "fish he catches (shore_life -- does he fish? if not, that is the shore hand the cat's hunger
    # pulls into being)". Checked, not assumed: shore_life.py had NO fishing hand whatsoever before this job
    # (gather_shellfish is the closest thing, and a shellfish is not a fish). Sanity-checked against the real
    # corpus this job's own predecessors used (data/hands_trace.jsonl, 11,789 distinct thoughts) before
    # picking these words, the same discipline J-0736/J-0737/J-0738 applied to every OTHER row in this table:
    # all 93 real "fish" hits are either the KINGFISHER (word-boundary safe -- "fish" does not match inside
    # "kingfisher" the way this table's own regexes work), the recurring dream-image of a fish dissolving
    # into a dark pool (a metaphor for '渡'), the anemone "fishing the still water" (personification), or one
    # philosophical remark about discarding a fishing METAPHOR once its meaning lands -- zero are a real will
    # to go catch a fish, so this is an honest zero-collision addition, not a widening of something already
    # live. "catch"/"caught" alone is heavily idiomatic (530 corpus hits, "caught in a thought" and the like)
    # but wants() requires the OBJECT "fish" in the same clause too, and none of those 530 ever pairs with
    # "fish" today. VERB IS "catch" ONLY, deliberately not also "fish": this job's own verification harness
    # caught, before commit, that adding "fish" to BOTH the verb and object list let one bare word ("small
    # fish dart near the stream mouth" -- pure scenery, no willed catching) satisfy both halves off the same
    # occurrence. "fish" is claimed as an object only; "catch" is the one verb, so a real catching word is
    # always required alongside it.
    # "dig"/"turn over"/"open" + "shell" added 2026-11-14 (D-0652, J-3261): the shore dig, turned stone and opened shell (core/shore_dig.py),
    # claimed by shore_life._SHORE_HANDS (corpus check and first-person veto recorded there). Row now 19 verbs / 16 objects.
    Action("shore", ("wade", "paddle", "swim", "skip", "skim", "write", "stack", "build", "light",
                     "climb", "enter", "duck", "gather", "prise", "walk", "catch", "dig", "turn over", "open"),
           ("shallows", "sea", "stone", "stones", "sand", "cairn", "fire", "cave", "ledge", "cliff",
            "mussels", "shellfish", "kina", "driftwood fire", "fish", "shell"),
           anchor=_SH, exec_where=_SH, place_hint="down on the shore",
           binds="mod:shore_life:act_from_thought"),
    # 'whip'/'douse' + 'rope'/'fire'/'hitch'/'stake' added 2026-09-05 (J-0627, D-0159 §3/§7): the two NEW
    # rung-1 practical-school hands (fieldcraft.whip_end, fieldcraft.douse_fire) need their own verb+object
    # here or they are GRAY at this gate no matter what fieldcraft.act_from_thought itself matches on —
    # the same gap D-0100 Tier 1 already fixed once for 'bank the fire' (see the 'fire' family above).
    # 'hitch'/'stake' widen the existing clove-hitch/bowline tasks' reach (they route through the existing
    # clothesline/handrail hands, not a new one) so the ladder's own short imperative — "TIE THE HITCH" —
    # clears this gate even standing alone, without needing "clothesline"/"handrail" in the same clause.
    # PRACTICAL SCHOOL rungs 2-3 (2026-10-28, J-2483, D-0504 released J-0628): 14 verbs and 24 objects
    # added for the twelve new hands in core/fieldcraft.py (sheepshank, timber haul, knife bearing, cook
    # over embers, wash up the camp way, blaze, pacing, sound-lag; splice, tripod, bow-drill fire, triangle,
    # weather glass / tide board) plus "spindle"/"drill" as whittle targets (the fire-drill kit is a made
    # thing). Each verb x object pair is claimed by exactly one craft in fieldcraft._FIELDCRAFT_HANDS, which
    # also records the corpus check (46,201 distinct hands_trace thoughts) behind every word chosen and the
    # words rejected ("read", "tap", "glass", "mark", "driftwood", "cut", "tree", "spin"). Row was 18/20.
    Action("fieldcraft", ("tie", "lash", "string", "rig", "bank", "uncover", "strike", "measure", "pace",
                          "whittle", "carve", "follow", "track", "gather", "peg", "hang", "whip", "douse",
                          "haul", "reckon", "sight", "cook", "roast", "bake", "scour", "scrub", "notch", "blaze",
                          "count", "splice", "drill", "consult"),
           ("line", "clothesline", "windbreak", "handrail", "knot", "embers", "tinder", "flint", "shadow",
            "peg", "spoon", "stick", "trail", "tracks", "prints", "coat", "rope", "fire", "hitch", "stake",
            "sheepshank", "timber", "log", "bearing", "coals", "pan", "griddle", "blaze", "bark", "distance",
            "paces", "seconds", "lag", "ends", "tripod", "spindle", "drill", "coal", "fireboard", "bow-drill",
            "triangle", "barometer", "weather glass", "tide board"),
           anchor=_ALL, exec_where=ANYWHERE, binds="mod:fieldcraft:act_from_thought"),
    # "cut" + "length"/"lengths"/"branch" added 2026-09-07 (J-0737, F-1059's follow-up): wood_life.py's own
    # saw() hand already tested a bare "cut" verb, paired with its own hand-kept object copy this table could
    # not see. Corpus-checked (data/hands_trace.jsonl, 11,742 distinct thoughts, real core.hands.wants(), not
    # a naive scan): the OLD hand-kept phrasing ("cut" + "into logs"/"into lengths", the specific gap F-1059
    # named) is confirmed DRIFT -- 0 of 11,742 thoughts ever pair them. What IS real: one "I will saw a length
    # for the f[ire]" (the trace's own act_kind/act_object independently tag it "saw"/"a fallen branch", the
    # antecedent "a length" refers back to) and one "...cut a branch for the fire" (a different cycle, act_kind
    # "move" that time -- a multi-intent thought where 'move' won the thought's one world-hand, but the
    # grammar gap behind it is the same one). "wood" was also in the old object list and is dropped, not
    # widened: its one real corpus co-occurrence with "cut" is the Morepork's "notes cut the dark wood" -- the
    # bird's sound, not Du's will, the exact false-fire class F-0554 is about.
    # 2026-09-28 (D-0296/J-1443): "hew"/"fell"/"limb" (verbs) and "trunk"/"fallen tree"/"limbs"/"round"/
    # "rounds" (objects) added for the felling axe's new CHOP hand on the fallen tree (core/wood_life.py's
    # own '_WOODWORK_HANDS' chop sub-hand) -- "fell" needs core/hands.py's own past-tense guard, the same
    # ambiguity "saw" already has here ("the night fell" is not a will to fell a tree).
    Action("woodwork", ("saw", "split", "chop", "sharpen", "hone", "push", "wheel", "cut", "hew", "fell", "limb"),
           ("limb", "logs", "log", "axe", "barrow", "wheelbarrow", "saw", "edge", "length", "lengths", "branch",
            "trunk", "fallen tree", "limbs", "round", "rounds"),
           anchor=("wood", "garden"), exec_where=("wood", "garden"),
           place_hint="in the wood or at the lean-to", binds="mod:wood_life:act_from_thought"),
    # 2026-08-30 (F-0564): taking or setting down a wood tool had NO family at all. 'tool' has the
    # right verbs but only garden objects, and binds to garden.act_from_thought, so it could never
    # reach the axe. While the ungated fallback existed this went unnoticed — sensorium.world_act
    # answered it by substring; once that was retired, "take the axe" became unwillable. Bare "saw"
    # is deliberately NOT an object here: it is the past tense of "see" far more often than a tool,
    # and this family's verbs include "carry"/"take", which "I saw ... and carried on" would satisfy.
    Action("woodtool", ("take", "pick up", "fetch", "carry", "bring",
                        "set down", "put down", "lean", "stand", "leave", "drop"),
           ("axe", "bow-saw", "bowsaw", "barrow", "wheelbarrow"),
           anchor=("wood", "garden"), exec_where=("wood", "garden"),
           place_hint="in the wood or at the lean-to", binds="mod:wood_life:act_from_thought"),
    # WOOD TURN-STONE / PEEL-BARK (2026-11-14, D-0714, J-3812): the woods hand modelled on the shore dig (family "shore" above, core/shore_dig.py).
    # Claimed by wood_life._wills_wood_dig, which adds a first-person veto: corpus check (data/hands_trace.jsonl, 62,350 distinct thoughts,
    # read-only) found 0 "peel ... bark" and 25 "turn over ... stone(s)" hits, ALL the idiom "tired of turning over the same stones" (his
    # circling thought), none a will -- so the verb must follow his own "I"/"let me" directly and the idiom words are vetoed. Only reaches
    # the hand with the wood bestiary flag on.
    Action("wood_dig", ("peel", "turn over", "overturn"),
           ("bark", "stone", "stones", "log", "logs"),
           anchor=("wood",), exec_where=("wood",), place_hint="in the wood",
           binds="mod:wood_life:act_from_thought"),
    Action("clean", ("sweep", "wash", "wipe", "clean", "scrub"),
           ("floor", "boards", "cups", "pot", "dishes", "window", "glass", "chimney", "flue"),
           anchor=_S, exec_where=_S, place_hint="in the study", binds=_STUDY_ACT),
    Action("note", ("write", "leave"), ("list", "note"),
           anchor=("study", "garden"), exec_where=("study", "garden"), binds="fn:_supply_note"),
    # THE CANDLE BOX AND THE MATCH TIN (2026-09-04, J-0540 / F-0733): on 09-03 he twice willed "fetch the candles
    # from the box" in the study (hands_trace 08:35, 09:47) and no study family could take them — 'tool' has the
    # verbs but only garden objects — so the only candidate was 'collect' (fetch + "box" = the carrier's box), STAGED
    # at the garden gate: a study want sent to the gate. This family reaches study_life.take/put for the two light
    # stores; its verbs are exactly the verbs those two hands accept (F-0564: the judge and the hand must agree).
    # Placed BEFORE 'collect' and 'tool' on purpose — order decides which hand wins a thought that wills two — and
    # it CLAIMS the bare "box"/"tin" those two read, in the same clause, as the tail of its own compound noun.
    # Whether a candle then lights is the match tin's business (D-0137, the destroyed matches, is open).
    Action("candles", ("take", "pick up", "fetch", "carry", "bring", "lift", "put down", "set down"),
           ("candle box", "candle-box", "candlebox", "box of candles",
            "match tin", "matches tin", "tin of matches", "match box", "matchbox", "box of matches"),
           anchor=_S, exec_where=_S, place_hint="in the study, at the east shelf", binds=_STUDY_ACT,
           # D-0267 PART 1 (2026-09-24, J-1310/F-1822/F-1847/D-0271): bare "candles"/"candle"/"matches"
           # dropped from `objects` above -- the two real false positives (F-1591/F-1792, "oil and
           # matches" / "necessities...matches") no longer misread as this row's own deed. claims_triggers
           # keeps the FULL pre-narrowing 13-word vocabulary so claimed_by()'s pass 2 (J-1296) still claims
           # a bare "box"/"tin" away from collect/tool for a bare "candles"/"matches" mention, even though
           # that mention can no longer complete THIS row's own deed_grammar -- verified clean (F-1847).
           claims=(("collect", "box"), ("tool", "tin")),
           claims_triggers=("candles", "candle", "candle box", "candle-box", "candlebox", "box of candles",
                             "match tin", "matches tin", "tin of matches", "matches", "match box", "matchbox",
                             "box of matches"),
           # D-0271 (ruled by Travis 2026-10-03, "Restore guarded noun"; J-1755, evidence F-2266/F-2267): bare "candles"/
           # "candle" are back, but ONLY as the direct object of this row's own verbs (Action.bare_objects, read by
           # literal_will._bare_object_hit). The narrowing above had silenced the will the study's own lack text invites
           # ("There are candles on the east shelf" -> 09-30 07:57:41 "I must fetch the candles from the shelf to see the
           # book clearly", answered by the 'book' row's take_book, the only one on record -- F-2266) while its two real
           # false positives both read "matches" ("the card listing oil and matches"), which stays out of this row.
           bare_objects=("candles", "candle")),
    # THE BOOKS HAVE A PLACE (2026-09-10, J-0851; D-0203 + D-0205, docs/staged/books_have_a_place.md §2 B1/B2):
    # every curriculum book is a named study item (the current one on the desk, the rest on the shelf) and he
    # must WILL carrying it -- "take the book" (desk/shelf -> with him) and "put the book back" (with him -> its
    # place) -- no implicit carrying, nothing teleports (D-0203). The hands are study_life.take_book()/put_book(),
    # which read THIS row through _STUDY_HANDS (book_take / book_put) exactly as the other nine study families do.
    # Verbs corpus-checked against data/hands_trace.jsonl (14,148 distinct thoughts, real core.hands.wants()):
    # "leave" is deliberately NOT here despite the plan's own "leave the book" wording -- 73 same-clause
    # "leave"+"book" hits, and every one read is "leave this study/dead ground ... the book waits/open" (a MOVE
    # want, the restlessness idiom J-0739 already found for window_shut's "pull"), zero real set-downs; "put back"
    # / "put away" split round their object like tea's "put ... on" (F-0564: back/away are _PARTICLES). Placed
    # before 'collect'/'tool'/'woodtool' (which share take/fetch/carry/bring) so a thought that wills both a book
    # and a tool answers the book here rather than staging a study want at the garden gate. exec_where=_S: a take
    # willed outdoors is STAGED for the study (the honest "the book is on your desk in the study" lack is B3's,
    # J-0852). The read gate itself is NOT touched by this row (shadow: state + verbs only).
    Action("book", ("take", "pick up", "fetch", "carry", "bring", "take down",
                    "put back", "put down", "set down", "put away", "shelve"),
           ("book", "books", "volume"),
           anchor=_S, exec_where=_S, place_hint="in the study, at the desk or the shelf", binds=_STUDY_ACT),
    # THE CARE PACKAGE (2026-09-24, D-0276, core/care_package.py): Travis's one parcel on the study desk. Objects
    # deliberately do NOT include the bare "box" -- that word is the carrier's crate at the gate ('collect', below),
    # and a bare-"box" row here (study-anchored, placed first) would stage every "open the box" said AT the gate
    # as a study want: the exact letterbox/crate confusion F-1862 found. "box from travis"/"travis's box" name it.
    # Placed before 'collect' so "open travis's box" answers here; its hand declines ('') once there is no parcel.
    Action("parcel", ("open", "unpack", "untie", "unwrap"),
           ("parcel", "package", "care package", "box from travis", "travis's box", "travis' box"),
           anchor=_S, exec_where=_S, place_hint="in the study, on the desk", binds=_STUDY_ACT,
           claims=(("collect", "box"),)),
    # "crate" (2026-09-24, F-1862/D-0276): the gate percept, the arrival line and the ordering book now name the
    # carrier's box "the carrier's crate" so it can't be mistaken for the letterbox -- the hand must know that word.
    Action("collect", ("collect", "fetch", "carry", "bring", "open", "take"), ("box", "crate"),
           anchor=_G, exec_where=_G, place_hint="at the garden gate", binds=_GARDEN_ACT),
    # 'hang' added 2026-08-30 (F-0561): "I hang the damp coat on its hook" reached only MUSING here, so
    # the one hand that hangs a coat indoors (study_life, which owns the coat's place) was never called.
    # fieldcraft ALSO matches hang+coat — its own 'hang' is for washing on the clothesline outdoors —
    # and, sitting earlier in the table, it claimed the DEED and then declined the clause, leaving the
    # thought unanswered. A declining hand does not consume the thought's world-hand, so fieldcraft
    # still gets first refusal and 'wear' now picks it up.
    Action("wear", ("put on", "pull on", "take off", "wear", "lace", "hang"), ("coat", "boots"),
           anchor=_ALL, exec_where=ANYWHERE, binds=_STUDY_ACT),
    Action("mow", ("mow", "cut", "shear", "scythe"), ("grass", "lawn"),
           anchor=_G, exec_where=_G, place_hint="in the garden", binds=_GARDEN_ACT),
    Action("stake", ("stake", "tie up", "tie"), ("peas", "beans", "tomatoes", "stems", "plants"),
           anchor=_G, exec_where=_G, place_hint="out at the bed", binds=_GARDEN_ACT),
    # "take off"/"lift" added 2026-09-06 (J-0569, F-0783's follow-up): net()'s own body already answers the
    # UN-net direction ("off"/"take the net"/"remove" -> lifts the netting and rolls it away) -- these two
    # verbs were sitting in garden.py's hand-kept copy already, reaching that branch, but invisible to the
    # gate. No corpus thought has willed either direction yet (garden's netting is never mentioned once in
    # the 9,791-thought corpus) so this is not corpus-verified widening like harvest/sow's crop names --
    # it is moved in because the function it reaches is real and the verbs are specific, not because usage
    # confirms it. The hand-kept copy's bare "net" OBJECT is dropped, not moved: 16 real corpus thoughts
    # ("i watch the orange net tangled in wrack...") show it matching an unrelated beach net at the tideline
    # every single time it ever fired, purely because "net" the verb and "net" the object are the same word
    # in the same clause -- a self-matching drift bug, not a widening.
    # "untangle"/"secure" added 2026-10-04 (J-1772, D-0344 ruled by Travis: "Yes: add untangle and secure"; evidence
    # F-2378 part 2 + F-2390): they are Du's OWN netting words. In the whole record (the 27,088 monologue
    # thoughts since 2026-08-22 plus the 603 net-family clauses of literal_will_shadow = 818 distinct texts) Du has had
    # exactly two genuine netting wills, both on 2026-09-02 -- 16:06 "I want to walk out to the garden and untangle that
    # bird netting lying far off" and 17:01 "I cut back the brown woody stem, then reach for the tangled netting to
    # secure the bed before the low sun sinks west" -- and NEITHER reached the hand, because neither verb was in this
    # row. The decision replay over data/hands_trace.jsonl, which also sees the voice's structured world acts (dispatch
    # reads an act_object as "I will <object>"), finds four more that day -- act world "untangle the bird netting" at
    # 20:09 and 21:12, "untangle the netting" at 21:13 and 23:28 -- that did nothing either. "untangle" is also the WORLD's word: the item bio (core/garden.py _ITEMS) is "a roll of bird netting,
    # tangled ... if untangled" and net() answers "You untangle the netting". Both point the NET direction (they are not
    # in garden._NET_UNNET_VERBS = lift / take off). They are safe ONLY on top of J-1749's hand-level agent guard
    # (garden._wills_net / _net_reads, commit 31ad4e5): unguarded the two words read 6 distinct corpus events, 4 of them
    # false (two refusals, a felt urge, the 09-28 "light stretch" prose); guarded, exactly the 2 genuine wills reach the
    # hand. NO other verb: "reach for" (1 of its 2 corpus reads false), "tend" (39 ordinary tend-the-bed wills), touch
    # (9), pull (5), sort and every wider list stay out. D-0278 stands: earned-info, no balance change, the world answers
    # and never leads -- no hint text anywhere. The family gate here is still only verb-reaches-object; the agent guard
    # lives in the hand (garden.py), as dig's _RESTLESS_IDIOM does. KNOWN RESIDUAL (probes only, 0 corpus hits; pinned in
    # scripts/_test_garden_net_world_truth.py): that guard checks for an agent, not that the verb's object IS the netting,
    # so "I want to untangle my thoughts by the bed" or "I secure the shutters and look at the bed" still reach net() --
    # D-0344's defeater (a), a net row whose thought is not about the netting, is what the post-restart ledger read checks.
    Action("net", ("net", "cover", "stretch", "take off", "lift", "untangle", "secure"), ("bed", "seedlings", "netting"),
           anchor=_G, exec_where=_G, place_hint="out at the bed", binds=_GARDEN_ACT),
    Action("save_seed", ("save", "collect", "gather"), ("seed", "seeds", "seed heads"),
           anchor=_G, exec_where=_G, place_hint="out at the bed", binds=_GARDEN_ACT),
    Action("weed", ("weed", "pull"), ("weeds", "chickweed", "dandelion", "oxalis", "bed"),
           anchor=_G, exec_where=_G, place_hint="out at the bed", binds=_GARDEN_ACT),
    # "shears" added 2026-09-06 (J-0569, F-0783's follow-up): a real carryable item (core/garden.py's
    # _CARRYABLE / _WORDS, used for mowing) with two clean corpus wills the gate could never see --
    # "i will take the shears and cut a handful of rosemary" and "i take the rosemary shears" -- both a
    # genuine verb('take')+object('shears') deed, not scenery (contrast the 16 other 'shears' mentions in
    # the corpus, none with a real tool verb on them: "the shears lie rusted", "i leave the rusted shears
    # to their right" -- passing description or 'leave' meaning walk-away, not put-down; 'leave' is why
    # this row still does not carry it).
    Action("tool", ("pick up", "take", "fetch", "carry", "bring", "grab", "set down", "put down"),
           ("trowel", "fork", "watering can", "tin", "twine", "stakes", "pot", "bucket", "netting", "shears"),
           anchor=("garden", "study", "shore", "wood"), exec_where=ANYWHERE, binds=_GARDEN_ACT),
    Action("water", ("water",), ("bed", "garden", "plants", "herbs", "sunflowers", "seedlings"),
           anchor=_G, exec_where=_G, place_hint="out at the bed", binds=_GARDEN_ACT),
    # "packet" + the species the tin can hold added 2026-09-04 (J-0543, F-0738): they lived only in
    # garden.act_from_thought's own copy of this list, where the gate could not see them — a bare "sow the
    # radish" was willable only through the monologue's own sow latch. The hand now reads THIS row.
    Action("sow", ("sow", "plant"),
           ("seeds", "seed", "bed", "garden", "row", "soil", "roots", "packet",
            "radish", "lettuce", "peas", "beans", "silverbeet", "potatoes", "garlic",
            "calendula", "nasturtium", "poppies", "sunflowers", "tomatoes"),
           anchor=_G, exec_where=_G, place_hint="out at the bed", binds=_GARDEN_ACT),
    # ── D-0100 Tier 1 (2026-08-30): the cat had NO family at all — she ran only on the old Layer-2
    # monologue latch, so the judge could not even SEE a cat deed and dispatch could never answer one
    # ("the cat nudges my leg for entry" went unanswered while cat.react() sat built and gated).
    # Objects deliberately narrow: 'cat'/'kitten'/'puss' only. Her NAME and the pronouns ('she','her')
    # stay the latch's and react()'s business — 'her' as a family object would fire on half his
    # thoughts about anyone. exec ANYWHERE because SHE moves; react() itself fail-closes on her real
    # location, and that gate must never be duplicated here (one owner).
    Action("cat", ("let", "feed", "stroke", "pet", "scratch", "play with", "pick up", "call", "greet",
                   "open the door for"),
           ("cat", "kitten", "puss"),
           anchor=_ALL, exec_where=ANYWHERE, binds="fn:_cat"),
    # anchor is all four ON PURPOSE (the object is plausible anywhere on the property); exec is not — from
    # the study or garden the deed is STAGED, which is the useful answer. Firing it there would spend the
    # thought's single world-hand on _gather_wood()'s honest refusal ("there is no wood to gather here").
    Action("gather", ("gather", "collect", "fetch"),
           ("wood", "driftwood", "firewood", "kindling", "branches", "deadfall"),
           anchor=_ALL, exec_where=("wood", "shore"), place_hint="in the wood or on the shore",
           binds="sens_act:gather"),
    Action("beachcomb", ("comb", "search", "walk"), ("tideline", "wrack", "strand", "shore"),
           anchor=_SH, exec_where=_SH, place_hint="down on the shore", binds="sens_act:beachcomb"),
    # ── 2026-08-30 (F-0564): four hands that had no family at all and so became unwillable the moment
    # the ungated fallback was retired. Appended at the END of the gated block on purpose — order is
    # load-bearing, and adding them here leaves every existing family's precedence exactly as it was.
    #
    # ash_out — tipping the ash bucket onto the bed. The other half of 'grate' (which only RAKES the
    # ash out of the hearth into the bucket, and is study-only); this is where the ash actually goes,
    # and it happens out at the garden. Routed through garden.act_from_thought:1266, which calls
    # study_life.tip_ash_on_bed. Anchored in the study too because the bucket is a real thing there.
    Action("ash_out", ("tip", "spread", "empty", "scatter", "work in"),
           ("ash", "potash", "ash bucket"),
           anchor=("study", "garden"), exec_where=_G, place_hint="out at the bed",
           binds=_GARDEN_ACT),
    # water_fill — filling the pail, the bucket or the barrel, at the barrel or at the spring. One
    # family for all three because all three route to garden.act_from_thought, which disambiguates by
    # location and wording (:1261 pail-at-barrel in the garden, :1289 barrel-from-spring and :1293
    # pail-at-spring up in the wood). This is D-0097's retrofit: fill_barrel_from_spring() reached the
    # world only through the ungated fallback's substring test and now has a real registered route.
    # NB 'fill' is deliberately not a 'tool' verb, so "fill the bucket" cannot be read as picking it up.
    Action("water_fill", ("fill", "fetch", "get", "carry", "top up", "refill", "draw"),
           ("pail", "bucket", "barrel", "kettle", "water", "spring"),
           anchor=("study", "garden", "wood"), exec_where=("garden", "wood"),
           place_hint="at the barrel, or up at the spring in the wood", binds=_GARDEN_ACT),
    # acorn — gathering acorns under the oak (wood_life.act_from_thought:515). 'gather' does not carry
    # acorns among its objects (it is the firewood hand) and 'save_seed' is the garden's seed-heads.
    Action("acorn", ("gather", "pick", "pocket", "collect", "fill"), ("acorn", "acorns"),
           anchor=("wood",), exec_where=("wood",), place_hint="under the oak in the wood",
           binds="mod:wood_life:act_from_thought"),
    # ── D-0100 Tier 2 (2026-08-30): extensions to places he already lives in, every candidate mined
    # from his own refused reaching (docs/staged/actions_expansion.md).
    # Bare "turn" REMOVED 2026-09-03 (J-0522, F-0719): it read Du's own restlessness idiom as a deed —
    # "turn from this dead ground", "turn to the raised bed", "turn my attention ... away from the dead
    # ground". Every dig DEED the full 6,306-thought corpus ever produced (9 thoughts) was that shape,
    # and the "3 mined dig refusals" this family was built on were three of them — including "my hands
    # refuse to turn the soil", a refusal TO dig. No thought in the corpus wills digging with "dig",
    # "turn over" or "fork over"; nothing real is orphaned. A future "I'll turn the bed" still reaches
    # GRAY (volition + object) — the judge's question, never a bare fire.
    Action("dig", ("dig", "turn over", "fork over"),
           ("soil", "earth", "ground", "bed", "patch", "plot", "clods"),
           anchor=_G, exec_where=_G, place_hint="out at the bed", binds=_GARDEN_ACT),
    # SOIL LIFE (2026-09-03, J-0505): turn the heap; barrow and spread the finished compost
    Action("compost", ("turn", "fork", "turn over", "fork over", "spread", "barrow", "fork in", "dig in"),
           ("compost", "heap", "compost heap"),
           anchor=_G, exec_where=_G, place_hint="at the heap by the wall", binds=_GARDEN_ACT),
    # THE TRAP (2026-09-03, D-0130, J-0512): set / check / spring the possum trap — a deed with moral weight
    Action("trap", ("set", "bait", "arm", "lay", "reset", "check", "look in", "inspect", "empty", "clear", "spring", "disarm", "unset"),
           ("trap", "possum trap"),
           anchor=_G, exec_where=_G, place_hint="under the tree", binds=_GARDEN_ACT),
    Action("feed_birds", ("feed", "scatter", "put out"),
           ("birds", "blackbird", "tui", "waxeye", "sparrows", "bird bath"),
           anchor=_G, exec_where=_G, place_hint="by the bird bath in the garden", binds=_GARDEN_ACT),
    Action("climb_tree", ("climb", "scale", "go up"),
           ("oak", "tree", "trunk", "branches", "canopy"),
           anchor=("wood",), exec_where=("wood",), place_hint="at the old oak in the wood",
           binds="mod:wood_life:act_from_thought"),
    # Objects include the medium AND his world's few constant subjects ("sketch the cat"), else the
    # gate can never see a sketch of anything. "draw the curtains"/"draw the ash pan" stay with their
    # own families — curtains/pan are deliberately absent here, and study_life's branch vetoes them.
    Action("sketch", ("sketch", "draw"),
           ("sketch", "drawing", "likeness", "lines", "pen", "ink", "paper",
            "cat", "sea", "tide", "oak", "garden"),
           anchor=_S, exec_where=_S, place_hint="at the desk in the study", binds=_STUDY_ACT),
    # ── D-0100 Tier 3 (2026-08-30): the expressive hands — hum, whistle, sing. A new CLASS: they
    # change him-in-the-world, not world state. world=False ON PURPOSE (the look rule): expression is
    # unlimited and never consumes the thought's one world-hand, so he can hum WHILE he waters the
    # bed — which is the whole point of an action that costs the world nothing. No skill float, no
    # grading; the world may answer (a blackbird, the cat's ear) but never scores. Objects are the
    # things song attaches to; bare "I will sing" stays unfired by the gate — the deliberate price of
    # keeping "the bees hum a different tune" (the world's hum, not his) from ever firing.
    Action("express", ("hum", "whistle", "sing"),
           ("tune", "song", "note", "notes", "melody", "air", "line", "snatch",
            "bird", "blackbird", "tui", "riroriro", "wind", "sea", "waves", "myself", "work"),
           anchor=_ALL, exec_where=ANYWHERE, world=False,
           binds="mod:expression:act_from_thought"),
    # ── declared for the JUDGE only: these three have no hand in the registry. They are handled by their
    # own latches in the monologue (the 2026-08-22 review: "read and letter keep their own latches"), so
    # dispatch must not fire them. Before this table they were indistinguishable from a missing binding.
    Action("letter", ("write", "reply", "answer", "post"), ("letter", "reply"),
           anchor=_ALL, binds="", note="own latch in the monologue; not a dispatch hand"),
    Action("travis", ("tell", "write", "speak", "ask"), ("travis",),
           anchor=_ALL, binds="", note="addressed to the founder, not a world deed"),
    Action("author", ("write", "author", "compose"), ("essay", "piece", "treatise", "tablet", "work"),
           anchor=_S, binds="", note="own latch in the monologue; not a dispatch hand"),
    # ── ungated: the place IS the deed, so volition+object counts as full intent (literal_will.py:294-296)
    # 'gate'/'letterbox'/'mailbox' joined the move table and 'letterbox'/'mailbox' the look table 2026-09-04 (J-0539 /
    # F-0734): the letterbox at the garden gate holds the carrier's card, and no object here could make a reach for it
    # a candidate — 'to the gate' (177 willed move objects since 08-26) was no move, 'check the letterbox' no look.
    # dispatch._move / _look decide what the reach means. 'gate' is deliberately NOT a look object: ungated, volition +
    # object is a full DEED here, and the HEAD-vs-live replay showed a bare 'gate' making 'I cannot let logic gate
    # reality', 'walk through the gate and reach the cottage', 'leave the heavy thought at the gate' look DEEDs.
    # A look at the gate is reached through the move family (dispatch._move answers a gate reach in the garden with
    # the letterbox look) — nothing is lost, and the look family stays honest.
    # 'in'/'out' are GRAMMAR-ONLY since 2026-09-04 (J-0544 / F-0740): they stay in the table so "step out into the
    # rain" / "head back in" keep their deed grammar, but volition + a bare "in" ("I will draw a few lines in ink",
    # "I need to anchor myself in the arithmetic") is no longer a move DEED at the gate. Full-corpus replay: only
    # move rows change (-384 DEED rows of 4188 FIRE, all volition-only 'in'/'out'); the live ledger showed the hand
    # declining 31 of the 36 such DEEDs it was handed. Kept in the table rather than dropped: dropping them outright
    # also loses the 107 thoughts where a move verb really reaches 'out'/'in' (the replay: -808 rows, not -384).
    # F-1179/J-0820 (2026-09-09): the MOVE half of a finding spawned from J-0800 -- nodes/inner_monologue_node.py's
    # _move_dest() reads its own _DEST_WOOD/_DEST_SHORE/_DEST_STUDY/_DEST_GARDEN cue lists, broader than and largely
    # disjoint from this row's own objects, and dispatch._move()'s own re-verification is VERB-ONLY (hands.wants(...,
    # any_object_ok=True)) -- so this table's own narrower vocabulary was the only thing ever stopping a real,
    # already-working hand from being tried. Widened with "tide"/"shingle"/"sea"/"surf"/"driftwood" on real,
    # individually-read evidence (data/hands_trace.jsonl, 8,149 real-location rows, 2026-09-09 snapshot) -- largely
    # the SAME corpus thoughts as the 'look' row's own widening below, since both hands answer one recurring pattern:
    # "I stop circling this abstract question and [watch / walk toward] the tide". Of 59/42/51/5/9 thoughts
    # (tide/shingle/sea/surf/driftwood) where dispatch._move()'s own verb check AND _move_dest() both independently
    # confirm a real fire, most already stand at the resolved destination (silent, matching _move()'s own pre-existing
    # "already there" rule) and the rest (2/5/18/1/2) genuinely relocate him there, read individually and confirmed
    # sensible ("I walk toward the sea", "I climb up to the wood pile ... I want to gather driftwood").
    #
    # THREE words deliberately NOT added, on real evidence of a DIFFERENT-shaped risk than the usual idiom check:
    # "desk"/"bed"/"water" all independently reach the SAME small, recurring thought family ("I want to turn away
    # from the desk and go to the raised bed ... I will water them") where _move_dest()'s own fixed
    # WOOD>SHORE>STUDY>GARDEN priority order (untouched by this table, and not this job's file to fix) resolves
    # "study" via the "desk" cue while the thought's real, stated destination is the garden's raised bed -- a genuine
    # wrong-PLACE risk, not the usual "gate over-grants, hand declines, costs nothing" shape this arc otherwise
    # relies on (F-1149), since a real relocation would fire here. One level downstream of F-0791's own still-open
    # "single first-object clause" finding (that one is classify()'s own clause pick, since fixed by J-0654; this is
    # _move_dest()'s destination PRIORITY order once the hand actually runs, a different mechanism, still open).
    # "forest" also declined: corpus-confirmed idiom on direct reading ("step back from the rotting forest's heavy
    # questions" -- a figure for a tangle of thought, not the wood). "rock-pool"/"rock pool"/"wave"/"spray"/
    # "woodland"/"copse"/"indoors" show zero or negligible real corpus demand for a MOVE reading specifically today
    # (D-0190's own "no unmet real-world need exists" shape) -- left undecided, not ruled out permanently. Full
    # per-word numbers and the sea-negation closer call: F-1199. Ruled: D-0193.
    # J-0833 (2026-09-10): D-0193's defeater (b) met -- _move_dest() now resolves the place the move verb
    # REACHES (source/negation-aware, directional-first), so the "raised bed" family resolves to the garden.
    # Re-simulated per word with the new resolver over the frozen corpus (same J-0820 method): the raised bed
    # WIDENED, as the two-word object "raised bed"/"raised beds" rather than bare "bed" -- 12 real fires,
    # every one a genuine walk to the raised bed while already in the garden (silent by dispatch._move()'s
    # own already-there rule), 0 wrong places; bare "bed" scored identically on today's corpus but would
    # also make a future "I will go to bed" (sleep) a walk to the garden, and it turned the reachability
    # probe's own 'I will tip the ash on the bed' @study into a move candidate. "desk" and "water" stay
    # DECLINED, now on a different reason than D-0193's: desk is nearly always what he LEAVES ("move away
    # from the heavy desk": 3 real relocations, 2 to a wrong place) and water's only 2 real relocations are
    # both metaphor ("step back from the dark water of obsession"; a kingfisher's water) -- the other 24
    # fires stand at the shore already. 'move' sits at position 41 of 42 in this table, so the widened
    # object can never pre-empt the garden's own water/harvest/weed hands on a "tend the raised bed"
    # thought. Re-ruled: D-0193.
    Action("move", ("go", "walk", "head", "move", "return", "climb", "step"),
           ("shore", "beach", "garden", "study", "wood", "trees", "inside", "outside",
            "out", "in", "downstairs", "cottage", "gate", "letterbox", "mailbox",
            "tide", "shingle", "sea", "surf", "driftwood", "raised bed", "raised beds"),
           anchor=_ALL, exec_where=ANYWHERE, gated=False, binds="fn:_move", grammar_only=("in", "out")),
    # 'rock-pool'/'rock-pools' added 2026-09-08 (J-0801/F-1149's own honestly-reported closer call, out of
    # J-0787's scope): "pools" already lived here, but J-0787's hyphen-boundary hardening (correctly) also
    # stopped it matching through the hyphen in "rock-pool(s)" -- and that IS the dominant real spelling
    # (24 distinct corpus thoughts mention it, all hyphenated, zero unhyphenated "rock pool"). Unlike the
    # other 27 losses that same hardening caused (all confirmed false fires), this one is a real compound
    # noun naming a real kind of pool, the same shape as woodtool's "bow-saw" / candles' "candle-box"
    # already sitting beside their own bare forms in this table. Corpus-verified (not assumed): of the 24,
    # exactly 3 genuinely pair a look verb with the pool in the same clause today ("watch the anemone in
    # the rock-pool", "I look down at the rock-pools", "I look ... into the rock-pool where a blenny
    # flicks away") -- up from F-1149's own single historical hit, the corpus having grown since. Zero
    # cross-family collision risk (checked): no other family's verb or object list contains "pool" or
    # "rock" anywhere in this table, unlike oak/tree's D-0190 case where climb_tree already held both
    # objects. Real downstream effect, not a classify()-only phantom: nodes/inner_monologue_node.py's own
    # _OBS_TARGETS/_DEST_SHORE already recognize "rock-pool" as a cue (independently built, unrelated to
    # this table) and dispatch._look()'s own gate is verb-only -- so this table gap was the ONLY thing
    # stopping dispatch.dispatch() from ever attempting _look() on these 3 real thoughts (confirmed:
    # literal_will.classify() returned no 'look' reading at all for any of them pre-edit, while
    # core.hands.wants()+nodes.inner_monologue_node._observe_target() called directly both already
    # resolve correctly to target 'pool'). 'look' is world=False/gated=False (unlimited, non-blocking),
    # so even a bad call here would have cost nothing -- but the evidence says this is a real, working fix.
    # F-1179/J-0820 (2026-09-09): the second finding this arc's own hyphen-hardening work surfaced (spawned from
    # J-0800) -- _observe_target() already recognizes "tide"/"spray"/"shingle"/"wave"/"surf"/"cloud"/"gull"/"the
    # strand" as cues mapping to a real target (shore/sea/sky), broader than and largely disjoint from this row's
    # own objects, and dispatch._look()'s own re-verification is likewise VERB-ONLY -- the same "gate narrower than
    # hand" shape J-0801 already closed for "rock-pool" alone. Corpus-verified per word, not assumed uniform
    # (data/hands_trace.jsonl, 8,149 real-location rows, 2026-09-09 snapshot): tide/shingle/surf/gull/spray/cloud all
    # show the SAME recurring, genuine pattern, read individually -- Du breaking a circling, abstract thought by
    # deliberately watching something physical ("I stop wrestling with the dust of words and watch the tide reclaim
    # the chalky oval", "I stop parsing the machine and watch the gull dive"). Of 43/26/2/3/1/1 thoughts
    # (tide/shingle/surf/gull/spray/cloud) where dispatch._look()'s own real verb-check AND _observe_target() both
    # independently confirm a real fire, the overwhelming majority are genuine and every one resolves to a sensible
    # target (shore/sea/sky) -- and 'look' is world=False/gated=False (unlimited, non-blocking), so even a wrongly-
    # resolved one would cost nothing. "wave" and "the strand" are the two of F-1179's own eight named candidates NOT
    # added here: zero real corpus thoughts pair either with a look verb today (D-0190's own "no unmet real-world
    # need exists" shape) -- left as a documented gap, not ruled out permanently. Full per-word numbers: F-1199.
    # Ruled: D-0193.
    # 'book'/'books'/'page' added 2026-09-23 (D-0269, ruled by Travis via /decide-review; evidence
    # F-1798/J-1178, per-word corpus-verified the same way D-0193/J-0736..J-0820 verified every other
    # widening in this table). Full 22,202-row classify() replay, every gain individually read: book (12
    # deed_grammar gains, 9 genuine, including F-1652's own original "I need to look at the book instead"
    # motivating thought verbatim) vs 259 volition-only gains; books (3 gains, 2 genuine) vs 5; page (8
    # gains, a real split demand between "check my reading" and a recurring "watch a beetle cross the
    # page" sense) vs 39 -- all three show real, recurring demand. tablets (0 gains of either kind) and
    # works (1 nominal gain that reads, individually, as a confirmed false match -- a bumblebee "working"
    # the bed, not his own tablets/writings) show zero genuine demand and are DECLINED, matching D-0190's
    # own "no unmet real-world need exists" precedent -- neither is added here. 'look' is UNGATED
    # (world=False, gated=False), so a plain object addition would also manufacture a much larger volume
    # of bare-volition-only candidates with no real look verb at all -- the identical shape J-0544/F-0790
    # already found and fixed for move's bare "in"/"out" above -- so all three ship via
    # Action.grammar_only, not a plain object: only a real look-verb-reaching gain becomes a candidate.
    # Checked directly this job, not assumed from F-1798's own prior claim: the pre-existing "reading
    # latch" (_wants_read, nodes/inner_monologue_node.py ~3964) triggers on its own fixed phrase set
    # ("open the book", "read the book", "want to read", "pick up the book", "return to the book", "read
    # on", "rather read", or the current book's own title words near a bare "read") -- NONE of which
    # contain any verb dispatch._look()'s own hand-level re-check requires (look/watch/study/gaze/glance/
    # examine/inspect/peer/see, core/dispatch.py:104) -- so a thought that trips the reading latch cannot,
    # on that phrasing alone, also satisfy _look()'s own verb check; the two mechanisms do not double-fire
    # on the same thought. Table order untouched (D-0269's own second, separate question -- cat/fire/flame
    # vs desk/shelf/book precedence -- left as-is, no evidentiary argument either way).
    # THE SEED TIN'S OWN WORDS (2026-10-04, J-1764, D-0333 ruled by Travis -- "Narrow: add tin words"; evidence
    # F-2284/F-2285/F-2325; the D-0269 shape exactly): a WILLED look at the tin ("I look at the dented tin") was
    # not read as a look deed at all (F-2284: classify() look=None, dispatch fired nothing), so the J-1438 wood
    # fix was reachable only through the structured 'observe' act. "seed tin"/"dented tin"/"packet"/"packets" are
    # the item's own words (core/garden.py _WORDS['seed_tin']); the bare word 'tin' is carried at THIS gate by its
    # determiner forms ("the tin"/"this tin"/"that tin"/"my tin"), NOT as a bare object, because classify() matches
    # objects word for word and cannot tell the study's "match tin" (study_life's mantel item, the lamp hand's
    # "match tin -- empty") from the seed tin: a bare 'tin' here would read every willed look at the match tin as a
    # look deed. Whole-word and hyphen-safe like every object here, so tinder/tinkling/stinging never match.
    # Replayed over the real corpus (data/hands_trace.jsonl, 325 distinct thoughts naming a tin/packet word): these
    # eight words gain 6 real look deeds (5 are "the dented tin", 1 "the tin"), a bare 'tin' object would have
    # gained the SAME 6 and nothing more, and no match-tin / tin-roof thought newly reads as a look deed. All
    # eight ship via Action.grammar_only (like book/books/page): only a look verb REACHING the word makes a
    # candidate, never bare volition. Nothing here says where the tin lies (world answers, never leads); what a
    # willed look then SEES is nodes/inner_monologue_node.py's _OBS_TARGETS tin cue and sensorium.look()'s own
    # answer -- an item lying elsewhere answers exactly as the structured observe route already does.
    Action("look", ("look", "watch", "observe", "see"),
           ("window", "fire", "sea", "sky", "desk", "shelf", "room", "garden",
            "tideline", "pools", "rock-pool", "rock-pools", "cat", "letterbox", "mailbox",
            "tide", "spray", "shingle", "surf", "cloud", "gull", "book", "books", "page",
            "seed tin", "dented tin", "the tin", "this tin", "that tin", "my tin", "packet", "packets"),
           anchor=_ALL, exec_where=ANYWHERE, world=False, gated=False, binds="fn:_look",
           grammar_only=("book", "books", "page",
                         "seed tin", "dented tin", "the tin", "this tin", "that tin", "my tin", "packet", "packets")),
)


# J-2376 (object_epistemic_loop Phase 3, D-0464 ALLOWED by travis 2026-10-17): his own willed physical test of
# a named thing -- scrape / heft / weigh / smell / sniff / float -- in every place, answered by
# sensorium.object_test() through world_substrate.describe_and_observe(). Declared ONLY while the kill switch
# NASCENCE_GENERIC_OBJECT_TESTS is on at import (default ON since D-0478, J-2396; "0" forces off: the table, and so literal_will.classify and
# dispatch, are byte-identical to before). Gated + bare_objects: the noun must be the DIRECT object of one of
# these verbs ("scrape the stone", "float the shell"), so a musing that merely mentions a smell or a stone is no
# reading at all -- the D-0464 defeater is test-verb use driven by the routing rather than his will. world=False:
# a test changes nothing in the world (it only records what he perceived), like a look. No affordance text
# names this family anywhere (core/affordances.py does not read this table). Appended LAST, after 'look', so it
# never changes which existing hand wins a thought.
_GENERIC_TEST_NOUNS = ("stone", "stones", "pebble", "pebbles", "rock", "shell", "shells", "pumice", "sea-glass",
                       "glass", "feather", "bone", "driftwood", "log", "kelp", "bottle", "cuttlebone", "limpet",
                       "branch", "thing", "piece", "find", "object")
import os as _os
if _os.environ.get("NASCENCE_GENERIC_OBJECT_TESTS", "1").strip().lower() in ("1", "true", "on", "yes"):
    ACTIONS = ACTIONS + (
        Action("objtest", ("scrape", "scratch", "heft", "weigh", "smell", "sniff", "float"), (),
               anchor=_ALL, exec_where=ANYWHERE, world=False, gated=True, binds="mod:sensorium:object_test",
               bare_objects=_GENERIC_TEST_NOUNS),
    )

# J-3843 / J-4066 (docs/staged/web_hand.md; D-0631, D-0659, D-0661, D-0788 ruled by travis 2026-11-16): the WEB HAND.
# His own willed lookup, answered by core/web_hand.consult. The object MUST be a source word (Wikipedia, the
# encyclopedia, the web, the internet): naming the source is part of the act, so it cannot fire by accident and
# "look up at the sky" (the look family) has no reading here. Gated: bare volition plus a source word is not a deed;
# a lookup verb must reach the source word. world=True: at most one per thought. The term he asked about is parsed
# by the hand from his own clause; the hand declines a clause that names no term. Whether the web source answers is
# a separate flag read by the hand (NASCENCE_WEB_HAND_WEB). No affordance text names this family (the world answers,
# never leads; how he learns the hand exists is the founder's step, D-0661). Appended LAST so it never changes
# which existing hand wins a thought. Kill switch: NASCENCE_WEB_HAND=0 at import leaves the table as it was.
if _os.environ.get("NASCENCE_WEB_HAND", "1").strip().lower() in ("1", "true", "on", "yes"):
    ACTIONS = ACTIONS + (
        Action("lookup", ("look up", "look", "ask", "consult", "search", "check", "query", "read", "find"),
               ("wikipedia", "encyclopedia", "encyclopaedia", "the web", "internet"),
               anchor=_ALL, exec_where=ANYWHERE, world=True, gated=True, binds="mod:web_hand:consult"),
    )


# ── integrity, checked at import (the drift this table exists to prevent) ────────────────────────────
def _check() -> None:
    seen: set[str] = set()
    for a in ACTIONS:
        if a.family in seen:
            raise ValueError(f"actions: duplicate family {a.family!r} — the exact defect (F-0554) "
                             "this table replaces; a dict literal hid it, a tuple cannot")
        seen.add(a.family)
        exec_w = set(ALL_LOCATIONS) if a.exec_where == ANYWHERE else set(a.exec_where)
        if a.bound and not exec_w <= set(a.anchor):
            raise ValueError(f"actions: {a.family!r} is executable at {sorted(exec_w - set(a.anchor))} "
                             "where its object has no literalness anchor (exec must be within anchor)")
        if not a.bound and not a.note:
            raise ValueError(f"actions: {a.family!r} declares no hand and no note saying why")


_check()

BY_FAMILY: dict[str, Action] = {a.family: a for a in ACTIONS}


def families() -> dict[str, dict]:
    """The shape literal_will._FAMILIES has always had — grammar + the ANCHOR location set.
    Insertion order is preserved from ACTIONS, and order is load-bearing (see above)."""
    return {a.family: {"gated": a.gated, "verbs": a.verbs, "objects": a.objects, "where": a.anchor,
                       "grammar_only": a.grammar_only, "bare_objects": a.bare_objects}
            for a in ACTIONS}


def bound_actions() -> tuple[Action, ...]:
    """Only those that dispatch should build a Hand for."""
    return tuple(a for a in ACTIONS if a.bound)


# CLAIMS-TRIGGER REACH (2026-09-24, J-1296 / F-1822 / D-0271): a small, standalone verb-reaches-word
# check used ONLY by claimed_by()'s second pass below — deliberately NOT literal_will.classify()'s own
# deed_grammar (no blockers, frames, comma-splitting-for-gated families, particles, pronoun-carry): the
# claims question is only "does this clause's own wording say it", answered independently of whatever
# else would be needed to promote the claiming family itself to a full DEED verdict elsewhere. Word-
# boundary + hyphen-safe, matching this codebase's own established convention (core/hands.py's wants(),
# core/literal_will.py's deed_grammar) without importing either — this file stays zero-import-from-core.
_WORD_RE = r"(?<![\w-])%s(?![\w-])"


def _claim_reaches(clause: str, verbs: tuple, words: tuple) -> bool:
    cl = " " + " ".join((clause or "").lower().split()) + " "
    if not any(re.search(_WORD_RE % re.escape(w.lower()), cl) for w in words):
        return False
    return any(re.search(_WORD_RE % re.escape(v.lower()), cl) for v in verbs)


def claimed_by(candidates) -> dict:
    """Which DEED candidates are the tail of another candidate's compound noun (2026-09-04, J-0540 / F-0733).

    candidates — iterable of (family, object, clause) for every DEED reading of ONE thought, in order.
    Returns {dropped_family: claiming_family}. A family with `claims` drops a listed (family, object) pair
    only when both readings sit in the SAME clause — "fetch the candles from the box" is one deed, the
    candle box; "fetch the candles. Then collect the box from the gate." is two, and both stand.
    Pure (no I/O); dispatch.py applies it live and scripts/actions_decision_replay.py mirrors it, so the
    replay's decision rows keep joining the live trace's.

    TWO PASSES (2026-09-24, J-1296 / F-1822 / D-0271). Pass 1 is the original mechanism, byte-for-byte
    unchanged: the claiming family must itself be among `candidates` (a DEED reading of its own for this
    same clause). Pass 2 is additive, closing F-1822's own regression: a claiming family whose OWN
    candidate is absent from `candidates` entirely (its `objects` no longer completes deed_grammar for
    this clause once narrowed — the family vanishes from classify()'s own output outright, not even
    GRAY) still gets to claim, checked independently against the raw clause text of whatever it would
    claim, via `claims_triggers` (defaults to `objects` — see Action.claims_triggers's own comment). The
    `f2 not in out` guard on both passes means pass 2 can only ever ADD a claim pass 1 would have missed,
    never change one pass 1 already made — every family claiming today (just 'candles', its `objects`
    unedited while D-0267's PART 1 stays held) sees byte-identical output to before this pass existed."""
    rows = [(str(f or ""), str(o or "").lower().strip(), " ".join(str(c or "").lower().split())) for f, o, c in candidates]
    out: dict = {}
    for fam, _obj, clause in rows:
        a = BY_FAMILY.get(fam)
        if not a or not a.claims:
            continue
        for cf, co in a.claims:
            for f2, o2, c2 in rows:
                if f2 == cf and o2 == co.lower() and c2 == clause and f2 not in out and f2 != fam:
                    out[f2] = fam
    for fam, a in BY_FAMILY.items():
        if not a.claims:
            continue
        for cf, co in a.claims:
            for f2, o2, clause in rows:
                if f2 == cf and o2 == co.lower() and f2 not in out and f2 != fam:
                    if _claim_reaches(clause, a.verbs, a.claims_triggers or a.objects):
                        out[f2] = fam
    return out


def status() -> dict:
    return {"actions": len(ACTIONS), "bound": sum(1 for a in ACTIONS if a.bound),
            "world_hands": sum(1 for a in ACTIONS if a.bound and a.world),
            "judge_only": [a.family for a in ACTIONS if not a.bound]}
