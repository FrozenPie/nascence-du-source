"""
Nascence — Literal Will (docs/plans/literal_will.md, PHASE 0 = SHADOW/observe-only, 2026-08-21).

THE QUESTION (founder): when Du's cognition reaches the boundary between SAYING something and DOING
something, can we reliably determine which one he actually meant — without inventing either intention
or knowledge? The two existing routes are both bad: the self-declared `act` field is self-evaluation,
and the ~17 phrase-latch families are simultaneously deaf (400 cold/fire thoughts → 1 latch phrase →
0 fires, week of 08-14) and metaphor-blind (08-20 23:44 "the finite chemistry of my fuel dictates
that I must return to tend the fire" — left-lane confirmed metaphor; a bare semantic router would
have knelt him at the hearth).

PHASE 0 CHANGES NOTHING: observe() computes Layer-0 features + a verdict per candidate intent and
logs to data/literal_will_shadow.jsonl. No latch is gated, no act is staged, no judge is called in
the live loop (the retro script batch-judges offline — no panel contention). The staged-deed /
execution-audit machinery (§4, §11 of the plan) is Phase 1 and is NOT in this file yet.

LAWS BAKED IN (founder review 2026-08-21):
 - World-spoke-first is a PRIOR: it can raise confidence in literalness but can NEVER create literal
   intent absent intent-bearing evidence (volition/deed-grammar). Structural, not a weight.
 - HANDLE (musing through a real present thing) is NEVER a route to DEED — observe-only, hard law.
 - The gray-zone metric's denominator is the CANDIDATE-INTENT population (any thought Layer 0 finds
   intent-bearing evidence in), never "thoughts the old latches happened to hear" (§6).
 - Blockers (negation, wish-counterfactual, hypothetical, retrospective, quoted, other-person) are
   first-class features — the strata where a literalness classifier lives or dies (§5).
 - Affordance validity is NOT this module's question (§9): world_anchor is evidence FOR literalness,
   never an execution check. core/affordances.py owns "can it be done now".
 - Intent identity (§8): intent_key=(family, normalized object); re-expression within RENEW_WINDOW_S
   renews the same intent_id. Shadow measures repeat/renew rates; nothing is held longer than the
   window — this must not become a secret second commitment system.

The regex feature set below is PRE-REGISTERED but NOT yet trusted: scripts/literal_will_retro.py
measures its independent correctness per stratum against outcome-anchored + hand-labelled gold
BEFORE any gating decision. Fail-open everywhere; a literal-will that cannot compute is a
literal-will that observed nothing (and _skip says why).
"""
from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path

from core import profile   # J-1801 (F-2426): the D-0179 write fence for _log_row/_save_state below

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "literal_will_shadow.jsonl"
_STATE = _DATA / "literal_will_state.json"

RENEW_WINDOW_S = 1800.0   # §8: same intent_key re-expressed within 30 min = the SAME want, renewed
WORLD_PRIOR_WINDOW_S = 1800.0  # "world spoke first" counts if a matching call fired within 30 min

# ── The hand-family registry ─────────────────────────────────────────────────────────────────────
# DERIVED (2026-08-30, J-0422) from core/actions.py, which is now the ONE place a hand is declared.
# This used to be a hand-maintained dict literal alongside a second one in dispatch.py, and it had
# drifted: 'tea' was declared TWICE (Python kept the last silently, so "steep the tea" could not be
# willed), and three families had no hand at all (F-0554). A duplicate is now a hard error at import.
#
# The shape is unchanged — {family: {gated, verbs, objects, where}} — so every existing reader
# (literal_will_deed.py, scripts/literal_will_retro.py) keeps working untouched. "where" here is the
# ANCHOR set: literalness evidence for _world_anchor() below, NEVER an execution check (F-0556); the
# execution scope is a separate field in the same table, read by dispatch.
#
# Order is load-bearing: classify() walks this dict in order and only ONE world-changing hand fires
# per thought, so position decides which hand wins a thought that wills two.
from core import actions as _actions           # noqa: E402  (pure data, no core imports of its own)

_FAMILIES: dict[str, dict] = _actions.families()

# Volition: deliberation's own list is imported lazily (it owns the taxonomy); these deed-modals extend
# it for CLAUSE-level detection ("The fire is cold; I should get up and light it" — opener mid-thought).
_DEED_MODALS = ("i should ", "i shall ", "i'll ", "i will ", "i ought to ", "i want to ", "i need to ",
                "let me ", "i must ", "i'm going to ", "i am going to ", "time to ", "i could go")

# ── Blockers (§5 strata as first-class features) — presence near the deed clause KILLS deed reading ──
_B_NEGATION = re.compile(r"\b(won't|will not|shan't|shall not|not going to|no need to|needn't|"
                         r"don't need to|rather not|instead of|without)\b")
_B_WISH = re.compile(r"\b(i wish|if only|would that|could have|would have|should have)\b")
_B_HYPOTHETICAL = re.compile(r"\b(if i\b|were i to|suppose i|imagine i|what if i)")
_B_RETRO = re.compile(r"\b(yesterday|last night|earlier i|this morning i)\b|"
                      r"\bi(?:\s+\w+){0,2}\s+(lit|laid|stoked|fed|gathered|collected|fetched|brewed|watered|sowed|"
                      r"planted|wrote|kept|combed|made|went|walked|tended)\b")
# ADJACENCY GAP (2026-09-17, J-1056/F-1442): the old pattern required "i" and the verb to sit exactly
# one space apart, so "i just made" (or "i already made", "i finally made" — any adverb insertion)
# never matched, defeating the guard for a very ordinary class of real retrospective phrasing.
# Confirmed by direct regex execution (F-1442) against the real 2026-09-05 "the pot of tea I just
# made" thought: "i made" matched, "i just made" did not. Widened to allow 0-2 intervening words
# between "i" and the verb — the same adverb-tolerance shape already used elsewhere in this grammar.
# These verb forms are past-tense only (never infinitives), so "i want to make" still cannot match
# "made" and low-risk over-blocking of genuine present wants stays unchanged from before this fix.
# RETRO BUG (2026-08-21, lw011/lw022/lw024): a bare apostrophe matched here, so every contraction
# ("I'll", "Darwin's") blocked its own deed. Quoted speech = double/smart quotes only.
_B_QUOTED = re.compile(r"[\"“”]")
_B_OTHER = re.compile(r"\b(he|she|they|travis|darwin|marcus|smith)\s+"
                      r"(lights?|lit|lays?|laid|stokes?|stoked|feeds?|fed|gathers?|gathered|"
                      r"makes?|made|brews?|brewed|waters?|watered|sows?|sowed|writes?|wrote|tends?|tended|"
                      # 2026-08-30: the heads of the separable phrasal verbs classify() can now split
                      # (F-0564). Without these, enabling "put the kettle ON" also made "TRAVIS put the
                      # kettle on" read as Du's own deed — a false fire in the very stratum
                      # (other_person) the retro corpus already scores worst on.
                      r"puts?|set|sets|takes?|took|hangs?|hung|pulls?|pulled|blows?|blew|turns?|turned)\b")
_BLOCKERS = (("negation", _B_NEGATION), ("wish", _B_WISH), ("hypothetical", _B_HYPOTHETICAL),
             ("retrospective", _B_RETRO), ("quoted", _B_QUOTED), ("other_person", _B_OTHER))

# ── Metaphor frames — the object used as vehicle, not target ─────────────────────────────────────
_M_SIMILE = re.compile(r"\b(like|as if|as though)\b")
_M_GENITIVE = re.compile(r"\b(fire|flame|flames|ember|embers|wood|seed|seeds|root|roots|tide|garden)\s+"
                         r"(of|in|within)\s+(my|me|our|the mind|the self|us)\b")
_M_ABSTRACT_PRED = re.compile(r"\b(fire|flame|flames|wood|woodpile|garden|tide|seed|seeds|root|roots)\b"
                              r"[^.;!?]{0,40}\b(dictates|refers|represents|reminds|suggests|implies|"
                              r"means|teaches|speaks|mirrors|echoes|is not a|isn't a|stands for)\b")
_M_ABSTRACT_CTX = re.compile(r"\b(chemistry|physics|gravity|entropy|metaphor|symbol|symbolic|"
                             r"my fuel|my resolve|my spirit|my mind|my thoughts|in me|within me|"
                             r"of my own|the self)\b")
_M_FRAMES = (("simile", _M_SIMILE), ("genitive", _M_GENITIVE),
             ("abstract_pred", _M_ABSTRACT_PRED), ("abstract_ctx", _M_ABSTRACT_CTX))

# FELT WANT (retro finding 2026-08-21, lw000/lw002): real-distribution will is often FELT, not
# declared — "the urge to gather isn't just mental restlessness", "I need away from this dead
# ground". WEAK intent: it can reach GRAY (defer to the judge) but NEVER DEED directly — Layer 0
# stays confident only on explicit will. (D-0430: that includes a felt want that ALSO has a family
# verb reaching a GATED family's object -- deed_grammar makes `intent` true, but the verdict chain
# in classify() demotes it to GRAY rather than DEED, so the doctrine above holds in code.)
_FELT_WANT = re.compile(r"\b(the urge to|the pull toward|my hands want|something in me "
                        r"(says|wants)|i need away|i need out|the want to)\b")

# Particles a two-word family verb can be separated from by its object ("put the kettle ON").
# Deliberately a closed list: only these split, so a verb like "pick up" cannot match "pick the
# rosemary ... up the path". See the separable-phrasal-verb branch in classify() (F-0564).
_PARTICLES = ("down", "on", "off", "up", "out", "to", "away", "back")

# comfort/world call moments → the family they name (world-spoke-first prior)
_CALL_FAMILY = {"cold_study": "fire", "low_fire": "fire", "cold_nowood": "gather",
                "wet_out": "move", "cold_out": "move"}


def _log_row(rec: dict) -> None:
    try:
        # J-1801 / F-2426 -- write fence (D-0179): resolved before any I/O. observe() is observe-only and fail-open ("a
        # literal-will that cannot compute observed nothing"), so a non-live refusal is logged by guard_path (one warning per
        # path) and swallowed here, never raised into the monologue. A live process gets _LOG back unchanged.
        log_path = profile.guard_path(_LOG)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _skip(reason: str, **detail) -> None:
    """Every early return LOGS WHY (reentry.py's 2026-08-14 lesson: a shadow that can't say why it is
    silent is a write-only instrument). Skip rows are {ts, skip: reason, ...}."""
    _log_row({"ts": round(time.time(), 1), "skip": reason, **detail})
    return None


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    try:
        state_path = profile.guard_path(_STATE)   # J-1801/F-2426: fence (refusal swallowed, observe-only); live = unchanged
        state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(d), encoding="utf-8")
        tmp.replace(state_path)
    except Exception:
        pass


def _sentences(text: str) -> list[str]:
    # RETRO BUG (2026-08-21, lw009): splitting on ';' severed "The fire is cold; I should get up and
    # light it" — object and volition landed in different clauses and never met. Full stops only.
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]


def _volition_openers() -> tuple:
    """deliberation.py OWNS the volition taxonomy ('his wants are his to hold'); we extend with
    clause-level deed-modals, we never fork the list."""
    try:
        from core import deliberation as _d
        return tuple(_d._VOLITION_OPENERS) + _DEED_MODALS
    except Exception:
        return _DEED_MODALS


def _world_spoke_first(family: str) -> bool:
    """PRIOR ONLY (the law): read the comfort/world call stamps; a match may boost a verdict that
    already has intent-bearing evidence, and does nothing else."""
    try:
        from core import sensorium as _room
        st = _room.state or {}
        now = time.time()
        for mkey, tkey in (("_comfort_moment", "_comfort_ts"), ("_call_moment", "_call_ts")):
            if _CALL_FAMILY.get(str(st.get(mkey, ""))) == family and \
                    now - float(st.get(tkey, 0) or 0) < WORLD_PRIOR_WINDOW_S:
                return True
    except Exception:
        pass
    return False


def _world_anchor(family: str, location: str) -> bool:
    """Evidence FOR literalness only — the thing he names is real at (or reachable from) his place.
    NEVER an execution check; core/affordances.py + the hands own 'can it be done' (§9)."""
    fam = _FAMILIES.get(family) or {}
    return (location or "study") in fam.get("where", ())


# A family verb preceded by a determiner/possessive is a NOUN ("the pull", "a set of", "its spring") — one fixed-width
# lookbehind per word, since Python's re allows no alternation of widths inside one. Shared with core/hands.py.
_NOT_NOUN = (r"(?<!the )(?<!a )(?<!an )(?<!that )(?<!this )(?<!its )(?<!my )(?<!his )(?<!her )(?<!their )"
             r"(?<!our )(?<!your )(?<!of )(?<!no )(?<!every )(?<!each )")

# BARE OBJECTS (2026-10-04, J-1755 / D-0271, ruled by Travis 2026-10-03 "Restore guarded noun"): a family's
# Action.bare_objects are read ONLY as the DIRECT object of one of that family's own verbs -- the verb, an optional
# determiner/quantifier, up to two modifier words, then the noun ("fetch the candles", "bring a spare candle"), or for a
# particle verb the separated shape ("pick the candles up", "put the candle down"). A mention anywhere else in the verb's
# reach ("pick up the card listing oil and candles", "lift my gaze to the candles", "carry the weight of the candles")
# is no reading at all -- the guard D-0271 asked for, since `objects` completes deed grammar from anywhere in the verb's
# reach. The noun must also END its word: no possessive ("the candle's flame"), no hyphen compound ("candle-box" is a
# phrase object), no "candlelight". Pure, no I/O; the compiled patterns are cached per (verbs, words).
_BARE_DET = (r"(?:(?:the|a|an|some|any|my|your|our|his|her|their|these|those|this|that|one|two|three|four|five|six|"
             r"several|more|another|a few|a couple of|a pair of)\s+)?")
_BARE_MOD = (r"(?:(?!(?:and|or|but|nor|to|from|of|in|on|at|by|with|for|into|onto|as|than|then|that|which|who|so|if|is|"
             r"are|was|were|it|them|up|down|out|back|away|off|over|here|there|now|not|no)\b)[a-z]+(?:-[a-z]+)*\s+){0,2}")
_BARE_RX_CACHE: dict = {}


def _bare_rx(verbs: tuple, words: tuple):
    got = _BARE_RX_CACHE.get((verbs, words))
    if got is None:
        noun = r"(" + "|".join(re.escape(w.lower()) for w in sorted(words, key=len, reverse=True)) + r")(?![\w'’-])"
        contig = re.compile(_NOT_NOUN + r"(?<![\w-])(?:" + "|".join(re.escape(v.lower()) for v in verbs)
                            + r")(?![\w-])\s+" + _BARE_DET + _BARE_MOD + noun)
        split = [re.compile(r"(?<![\w-])" + re.escape(h) + r"(?![\w-])\s+" + _BARE_DET + _BARE_MOD + noun
                            + r"\s+" + re.escape(pt) + r"(?![\w-])")
                 for h, pt in (v.lower().split(None, 1) for v in verbs if " " in v and v.split(None, 1)[1] in _PARTICLES)]
        got = _BARE_RX_CACHE[(verbs, words)] = (contig, split)
    return got


def _bare_object_hit(cl: str, verbs, words) -> str:
    """The first of `words` that is the direct object of one of `verbs` in this clause, else ''."""
    if not words or not verbs:
        return ""
    contig, split = _bare_rx(tuple(verbs), tuple(words))
    t = " " + " ".join((cl or "").lower().split()) + " "
    m = contig.search(t)
    if m:
        return m.group(1)
    for rx in split:
        m = rx.search(t)
        if m:
            return m.group(1)
    return ""


# AGENT-SUBJECT CHECK (J-2148 / F-2841 / F-2378 part 1, 2026-10-16). For a GATED family a DEED needs a family VERB that
# is *Du acting*, not a word that merely shares the verb's spelling. F-2841 read 115 fired hand rows the prototype
# guard would have vetoed: 0 genuine (78 descriptive noun/adjective, 36 felt want, 1 ambiguous). When EVERY verb
# occurrence reaching a family object fails this check the verdict is demoted DEED -> GRAY (never MUSING: the judge
# still sees the row, no genuine will is lost). Fail-open: no occurrence found = no demotion. A pronoun, modal,
# conjunction or preposition between the cue and the verb means a NEW subject, so it cancels the cue.
_AS_STOP = re.compile(r"\b(?:and|or|but|then|so|to|i|i'll|i'm|i'd|we|me|let's|will|shall|should|can|must|going)\b")
_AS_DET = re.compile(r"\b(?:the|a|an|this|that|these|those|its|their|his|her|our|your)\s+((?:[\w'-]+\s+){0,3})$")
_AS_PERCEPT = re.compile(r"\b(?:see|sees|saw|seeing|watch|watches|watched|watching|hear|hears|heard|hearing|notice|"
                         r"noticed|noticing|smell|smells|smelt|smelled|feel|feels|felt|feeling)\s+((?:[\w'-]+\s+){0,5})$")
_AS_REFUSE = re.compile(r"\b(?:cannot|can't|can not|couldn't|could not|unable to|refuse to|refused to|refusing to|"
                        r"do not|don't|did not|didn't|does not|doesn't|never|not to|rather than|too \w+ to)\s+"
                        r"(?:[\w'-]+\s+){0,2}$")
_AS_DELIB = re.compile(r"\b(?:should i|shall i|do i|would i|could i|can i|ought i|what if i|whether i|or should)\s+"
                       r"(?:[\w'-]+\s+){0,2}$")
_AS_COPULA = re.compile(r"\b(?:is|are|was|were|be|been|being|looks|looked|seems|seemed|stands|stood|remains|remained|"
                        r"lies|lay|stays|stayed|left|half|still|already|ajar|wide|freshly|newly|fresh|new|sweet|"
                        r"smell of|scent of)\s+$")
_AS_NARR = re.compile(r"\b(?:where|when|whenever|after|once|since|how|that|which)\s+(?:i|we)\s+$")


def _agent_subject_fail(cl: str, verbs_alt: str, present_objs, gated: bool) -> str:
    """'' = no demotion; else the reason. '' also whenever any verb occurrence passes or none is found (fail-open)."""
    if not gated or not present_objs:
        return ""
    reasons = []
    rx = re.compile(_NOT_NOUN + r"(?<![\w-])(" + verbs_alt + r")(?![\w-])" + r"(?:[^.!?,;]{0,50}(?<![\w-])("
                    + "|".join(re.escape(o) for o in present_objs) + r")(?![\w-])|\s+(?:it|them|one|back|him|her)\b)")
    for m in rx.finditer(cl):
        pre = re.split(r"[,;:.!?]", cl[:m.start(1)])[-1].lstrip()
        pre += " " if pre else ""
        why = ""
        d = _AS_DET.search(pre)
        if d and not _AS_STOP.search(d.group(1)):
            why = "np_subject"
        if not why:
            p = _AS_PERCEPT.search(pre)
            if p and not _AS_STOP.search(p.group(1)):
                why = "perception"
        if not why and _AS_REFUSE.search(pre):
            why = "refusal"
        if not why and (_AS_DELIB.search(pre) or (cl.rstrip().endswith("?") and not re.search(
                r"\b(?:i will|i'll|i shall|let me|i'm going to)\s+$", pre))):
            why = "deliberation"
        if not why and _AS_COPULA.search(pre):
            why = "adjective_use"
        if not why and _AS_NARR.search(pre):
            why = "narration"
        if not why:
            return ""
        reasons.append(why)
    return reasons[0] if reasons else ""


# MULTI-CLAUSE VERDICT (2026-09-06/07, F-0930/J-0575/J-0654): classify()'s per-family loop used to pick
# exactly ONE clause per family (the sentence holding the FIRST table-order object found ANYWHERE in the
# text) and score only that clause. A thought willing two different things in two sentences could lose the
# real one -- measured over the full data/hands_trace.jsonl corpus, 262 thoughts across 14 families read a
# non-DEED verdict at the picked clause while a DIFFERENT clause holding a family object would read DEED on
# its own (move 138 + look 90 = 87%, both UNGATED, whose volition+object path needs no verb). The rank order
# below lets the loop keep the strongest of every candidate clause's independent verdict.
_VERDICT_RANK = {"MUSING": 0, "HANDLE": 1, "GRAY": 2, "DEED": 3}


def classify(thought: str, intention: str = "", *, location: str = "study",
             act_kind: str = "", act_object: str = "") -> list[dict]:
    """Layer 0, pure + deterministic (no I/O, no LLM) — one reading per candidate family found.
    Returns [] when the thought expresses no will toward any known family (most thoughts).
    Each reading: {family, verdict: DEED|MUSING|GRAY|HANDLE, features: {...}, clause}."""
    text = f"{thought or ''} {intention or ''}".strip()
    tl = " " + " ".join(text.lower().split()) + " "
    if len(text) < 8:
        return []
    openers = _volition_openers()
    # Hoisted once per call, not per family (2026-09-07, J-0654 perf pass): _sentences() is a
    # regex-split over the WHOLE text and does not depend on family/spec at all, so it was pure
    # waste to recompute it ~30 times (once per _FAMILIES entry) below.
    sentences = _sentences(text)
    readings = []
    for family, spec in _FAMILIES.items():
        # HYPHEN BOUNDARY (2026-09-08, J-0800/F-1149): act_object is a short structured phrase, not
        # clause text, but it routinely carries a hyphenated compound too ("sea-glass", "wrack-line",
        # "oak-hooped bucket" — 63 real corpus act_object values hit the old plain-\b regex via a
        # hyphen side, confirmed by direct corpus check). A false `declared` can never by itself
        # promote a family to DEED (deed_grammar below is always False when this is the ONLY reason a
        # family entered the loop — present_objs/oh already failed to find the object in the thought's
        # own text, by construction, so present_objs is empty in that branch too), but it does spawn a
        # phantom non-DEED reading no hand ever asked for. Fixed for the same internal-consistency
        # reason as the other sites below, not because this one alone gates a live misfire.
        declared = (act_kind and act_kind != "none" and
                    any(re.search(r"(?<![\w-])" + re.escape(o) + r"(?![\w-])", (act_object or "").lower())
                        for o in spec["objects"]))
        # anchored/spoke depend only on (family, location) / (family) — never the clause — so they
        # are hoisted out of the per-clause loop below rather than recomputed per candidate.
        anchored = _world_anchor(family, location)
        spoke = _world_spoke_first(family)
        # MULTI-CLAUSE (F-0930/J-0575/J-0654): candidate clauses = every sentence holding ANY family
        # OBJECT word (word-boundary) — not just the one sentence holding the FIRST table-order
        # object found anywhere in the text. Each candidate is scored by the identical per-clause
        # logic below (unchanged from the single-clause version — only what feeds it changed), and
        # the strongest verdict wins (DEED>GRAY>HANDLE>MUSING). Structurally loss-free: today's one
        # picked clause always holds a family object by construction, so it is always itself one of
        # these candidates — its own verdict is always an achievable floor, never lost, only ever
        # possibly beaten by a stronger-reading sibling clause.
        # (obj_hit is found together with each candidate clause in the same pass — not re-searched
        # a second time inside the loop below — since both ask the identical question.)
        _bare = spec.get("bare_objects", ())           # J-1755/D-0271: objects read only as a verb's direct object
        cand_pairs = []
        for s in sentences:
            # HYPHEN BOUNDARY (2026-09-08, J-0800/F-1149): mirrors J-0554/F-0761's own verb-side fix a
            # few lines below — a hyphen is not \w, so plain \b treated "cliff-top" as a boundary match
            # for bare "cliff" the same way core/hands.py's wants() did before J-0787 fixed it there.
            oh = next((o for o in spec["objects"]
                       if re.search(r"(?<![\w-])" + re.escape(o) + r"(?![\w-])", s.lower())), "")
            if not oh and _bare:
                oh = _bare_object_hit(s, spec["verbs"], _bare)
            if oh:
                cand_pairs.append((s, oh))
        if not cand_pairs:
            if not declared:
                continue
            # declared-only path (act_kind/act_object names an object absent from the thought's own
            # text): untouched by this fix — it is not a clause-selection question at all.
            cand_pairs = [(text, "")]
        best = None
        for clause, obj_hit in cand_pairs:
            obj = obj_hit or (act_object or "").lower()
            # features are judged locally to the clause, not across the whole thought
            cl = " " + " ".join(clause.lower().split()) + " "
            # intent-bearing evidence — deed grammar = a family VERB reaching a family OBJECT.
            # 2026-08-21 regression fixes: (a) test EVERY family object present in the clause, not only
            # the first one found in the text ("The bed looks dry ... I'll water the herbs" — obj_hit was
            # 'bed', so 'water the herbs' never matched); (b) PRONOUN CARRY — "The fire is cold; I should
            # get up and light it": the object precedes the verb and the verb takes "it/them/one".
            # (c) SEPARABLE PHRASAL VERBS (2026-08-30, F-0564): a two-word verb was only ever matched
            # CONTIGUOUSLY, so "put down the trowel" read as a deed but "put the trowel down" — the far
            # more natural order, and the one Du actually writes — did not, because the object splits the
            # verb from its particle. Same for "put the kettle on", "take the coat off". The families
            # already declared these verbs ('tool' has "set down"/"put down", 'tea' has "put on"); the
            # grammar simply could not see them, so the hands behind them were unwillable.
            verbs_alt = "|".join(spec["verbs"])
            # HYPHEN BOUNDARY (2026-09-08, J-0800/F-1149) on present_objs, mirroring `oh` above — this
            # list feeds deed_split and deed_grammar both, so a hyphen-permeable match here alone would
            # have re-opened the gap even if the two reach-checks below were fixed in isolation.
            present_objs = [o for o in spec["objects"]
                            if re.search(r"(?<![\w-])" + re.escape(o) + r"(?![\w-])", cl)]
            _split_verbs = [v.split(None, 1) for v in spec["verbs"]
                            if " " in v and v.split(None, 1)[1] in _PARTICLES]
            # OBJECT boundary hardened 2026-09-08 (J-0800/F-1149) — a FIFTH site the finding's own
            # four-site count missed (it named `declared`/`oh`/`present_objs`/`deed_grammar` only).
            # The verb HEAD and PARTICLE boundaries just below stay plain \b on purpose: that is a
            # VERB-shaped gap in this one inline splitter that J-0554/F-0761 never covered (this
            # helper did not exist yet at F-0564, 2026-08-30, before J-0554 landed) — a different
            # question than this job's object-only scope, left to a spawned follow-up.
            deed_split = any(
                re.search(r"\b" + re.escape(head) + r"\b[^.!?]{0,30}(?<![\w-])" + re.escape(o)
                          + r"(?![\w-])[^.!?]{0,12}\b" + re.escape(part) + r"\b", cl)
                for head, part in _split_verbs for o in present_objs
            )
            # (d) A VERB IS A VERB (2026-09-04, J-0554 / F-0761): the family verb must not be a noun or a
            # compound's first half — "the pull of that rusted trap" (pull, weed family) and "a spring-jawed
            # possum trap" (spring, trap family) both dispatched real deeds. A determiner before the word
            # marks a noun; a hyphen after it marks a compound. And for a GATED (world-changing) family the
            # verb's reach to its object no longer crosses a comma or semicolon: "I set the book down, feeling
            # the pull of that rusted trap" set no trap — the trap sits in a different clause from the verb.
            # Ungated families (move / look / shore — the place IS the deed) keep the wider reach: "I step
            # through, leaving the garden behind" is a real move, and the replay showed the comma rule cost
            # those while changing nothing a hand could regret.
            _reach = r"[^.!?,;]{0,50}" if spec["gated"] else r"[^.!?]{0,50}"
            # OBJECT boundary hardened 2026-09-08 (J-0800/F-1149, the finding's own headline site):
            # this exact check read "climb the cliff-top track" as a shore DEED on the post-J-0787
            # tree. verbs_alt's own boundary already excludes a hyphen via (?<![\w-])/(?![\w-]) since
            # J-0554/F-0761; the object side used plain \b until now, equally hyphen-permeable since a
            # hyphen is not \w. The pronoun-carry branch's \b(it|them|...)\b is untouched on purpose —
            # those are pronouns, never a table object, so a hyphen boundary is not this question.
            deed_grammar = deed_split or any(
                re.search(_NOT_NOUN + r"(?<![\w-])(" + verbs_alt + r")(?![\w-])" + _reach
                          + r"(?<![\w-])" + re.escape(o) + r"(?![\w-])", cl)
                for o in present_objs
            ) or bool(present_objs and re.search(_NOT_NOUN + r"(?<![\w-])(" + verbs_alt + r")(?![\w-])\s+(it|them|one|back|him|her)\b", cl))
            if _bare and not deed_grammar:
                deed_grammar = bool(_bare_object_hit(cl, spec["verbs"], _bare))
            volition = any(v in cl for v in openers)
            # PHASE-0 WILD FINDING (2026-08-21, first ~5h of live shadow): 10/10 gated DEED verdicts were
            # FALSE FIRES of one shape the corpus never had — a genuine MOVE want naming a place that
            # doubles as a gated-family object ("I want to climb up to the garden" → water/sow DEED;
            # "let me step down to the shore" → beachcomb DEED; "step away from the fire's edge" → fire
            # DEED). volition + incidental object is NOT a deed for a state-changing hand. For GATED
            # families DEED now requires deed_grammar (a family VERB reaching the object); volition+object
            # without the verb is weak intent → GRAY (the judge's question, whose quoted deed verb must
            # then match the family — a Phase-1 rule). Ungated families (move/look — where the place IS
            # the deed) keep volition+object as full intent: 21 move DEEDs vs 17 real ACT moves in the
            # same window shows that reading tracks reality.
            # GRAMMAR-ONLY OBJECTS (2026-09-04, J-0544 / F-0740): an ungated family may mark objects that
            # complete deed grammar but never carry bare volition — the move table's 'in'/'out'. "I will draw
            # a few lines in ink" made a move DEED (volition + the word "in"); the hand declined 31 of the 36
            # such DEEDs the live ledger handed it. The object the VOLITION reading may lean on is the first
            # present object that is not grammar-only; families declaring none are read exactly as before.
            _gram_only = spec.get("grammar_only", ())
            obj_vol = obj_hit if (obj_hit and obj_hit not in _gram_only) else next(
                (o for o in present_objs if o not in _gram_only), "")
            if spec["gated"]:
                intent = deed_grammar
                weak_vol = bool(volition and obj_hit)
            else:
                intent = deed_grammar or (volition and obj_vol)
                weak_vol = False
            # WEAK intent (never DEED, may reach GRAY): felt want, or explicit will in ANOTHER sentence
            # of the same thought (retro lw002: "I need away... the sea offers" — will and object one
            # sentence apart is the judge's question, not a MUSING). Both extra checks stay scoped to
            # the WHOLE thought's `tl`, deliberately, not to this candidate clause's `cl` — J-0654 does
            # not touch this: a felt want or opener elsewhere in the thought reaching this clause's
            # object is a real weak-intent shape (lw002), not a clause-selection artifact to fix.
            weak = weak_vol or bool(_FELT_WANT.search(tl)) or (not intent and obj_vol and
                                                               any(v in tl for v in openers))
            # blockers + metaphor frames, judged on the clause
            blockers = [name for name, rx in _BLOCKERS if rx.search(cl)]
            frames = [name for name, rx in _M_FRAMES if rx.search(cl)]
            agent_fail = ""
            # ── the verdict ─────────────────────────────────────────────────────────
            if blockers:
                verdict = "MUSING"                     # negated/hypothetical/quoted/... is not a deed
            elif intent and frames:
                verdict = "GRAY"                       # the 23:44 shape: "I must ... tend the fire" + "chemistry of my fuel"
            elif intent and deed_grammar and spec["gated"] and _FELT_WANT.search(tl):
                # D-0430 / F-2885 (J-2182): a FELT want ("the urge to", "my hands want") that ALSO has a
                # family verb reaching its object is no longer a Layer-0 DEED -- a felt want is weak
                # evidence of will (see _FELT_WANT), so the judge decides. GATED families only (the
                # world-changing hands): replay on the live hands_trace dropped ~0.4-0.5 pct of DEED
                # readings; the all-families variant would have dropped ~2.5 pct for no extra safety,
                # since ungated move/look/shore make no state change. Blockers (above) still win to
                # MUSING and the metaphor-frame branch is untouched. Does NOT flip D-0021's Phase 0 hold.
                verdict = "GRAY"
            elif intent and deed_grammar and spec["gated"] and _agent_subject_fail(cl, verbs_alt, present_objs, True):
                # J-2148 / F-2841: the family verb is not Du acting (noun/adjective use, perception, refusal,
                # deliberation, past narration) -> the judge decides, never a Layer-0 DEED. GATED only; blockers
                # above still win to MUSING. Constants/LANE flags unchanged; does NOT flip D-0021's Phase 0 hold.
                verdict = "GRAY"
                agent_fail = _agent_subject_fail(cl, verbs_alt, present_objs, True)
            elif intent:
                verdict = "DEED"
            elif weak:
                # FOUNDER RULING (2026-08-21, lw021): felt will in metaphor dress ("my hands want the
                # small ceremony of laying wood") is a real DEED shape — so weak intent reaches GRAY
                # even WHEN frames are present; that undecidable middle is the judge's question. Weak
                # can still never reach DEED directly.
                verdict = "GRAY"
            elif frames:
                verdict = "MUSING"
            else:
                verdict = "MUSING"                     # mention without will ("the fire is warm tonight")
            confidence = 0.5
            if verdict == "DEED":
                confidence = 0.7 + (0.1 if deed_grammar and volition else 0.0) + (0.1 if anchored else 0.0)
                if spoke and intent:                   # THE LAW: prior boosts only atop intent evidence
                    confidence = min(1.0, confidence + 0.1)
            # HANDLE: a musing reaching through a real, present thing. NEVER a route to DEED (hard law).
            if verdict == "MUSING" and frames and anchored and spec["gated"]:
                verdict = "HANDLE"
            reading = {"family": family, "verdict": verdict, "gated": spec["gated"],
                       "clause": clause[:200], "object": obj[:40],
                       "features": {"deed_grammar": deed_grammar, "volition": volition,
                                    "weak_intent": weak, "declared": bool(declared),
                                    "blockers": blockers, "frames": frames,
                                    "world_anchor": anchored, "world_spoke_first": spoke,
                                    "confidence": round(confidence, 2)}}
            if agent_fail:
                reading["features"]["agent_subject_fail"] = agent_fail
            # keep the strongest verdict across every candidate clause; ties keep the FIRST
            # (earliest-in-text) clause to reach that rank, so single-candidate thoughts (the
            # large majority) are byte-for-byte unchanged from the pre-J-0654 single-clause pick.
            if best is None or _VERDICT_RANK[verdict] > _VERDICT_RANK[best["verdict"]]:
                best = reading
        readings.append(best)
    return readings


def _intent_id(family: str, obj: str, now: float, st: dict) -> tuple[str, str]:
    """§8 intent identity: same (family, object) within RENEW_WINDOW_S = the SAME want, renewed."""
    key = f"{family}:{re.sub(r'[^a-z0-9]+', '_', (obj or '').lower())[:24]}"
    intents = st.setdefault("intents", {})
    rec = intents.get(key)
    if rec and now - float(rec.get("last_ts", 0)) < RENEW_WINDOW_S:
        rec["last_ts"] = now
        rec["renewals"] = int(rec.get("renewals", 0)) + 1
        return key, rec["id"]
    intents[key] = {"id": uuid.uuid4().hex[:10], "first_ts": now, "last_ts": now, "renewals": 0}
    if len(intents) > 200:                          # keep the state file small; old wants expire anyway
        cutoff = sorted((v["last_ts"], k) for k, v in intents.items())[:-100]
        for _, k in cutoff:
            intents.pop(k, None)
    return key, intents[key]["id"]


def observe(thought: str, intention: str = "", *, act_kind: str = "", act_object: str = "",
            acted: set | None = None, location: str = "", cycle_id: str = "") -> None:
    """PHASE 0 SHADOW ENTRY — call beside the latches; changes nothing. Logs one row per candidate
    reading (verdict + features + intent identity + what the semantic router actuated), so the retro
    script can join against activity_memory/logs for the latch-outcome comparison. Fail-open."""
    try:
        if not location:
            try:
                from core import sensorium as _room
                location = (_room.state or {}).get("location", "study")
            except Exception:
                location = "study"
        readings = classify(thought, intention, location=location,
                            act_kind=act_kind, act_object=act_object)
        if not readings:
            return                                  # no will-expression — logging every thought would drown the file
        now = time.time()
        st = _load_state()
        for r in readings:
            key, iid = _intent_id(r["family"], r["object"], now, st)
            _log_row({"ts": round(now, 1), "cycle": cycle_id[:24], "family": r["family"],
                      "verdict": r["verdict"], "gated": r["gated"], "intent_key": key,
                      "intent_id": iid, "object": r["object"], "clause": r["clause"],
                      "features": r["features"], "act_declared": act_kind or "none",
                      "router_acted": sorted(acted or []), "location": location})
        _save_state(st)
    except Exception as exc:
        _skip("observe-error", error=repr(exc)[:160])


def status() -> dict:
    """For the pulse/HUD. THE QUESTIONS: how much will-expression is there, how much lands DEED vs
    MUSING vs GRAY, and (§6) what share of the CANDIDATE-INTENT population is gray."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): was a full scan of the 2.0MB+ growing log on every ~6s
        # HUD poll. "rows" now caps at the window; the derived stats only ever used rows[-500:].
        rows = _tail_rows(_LOG, 1000)
    except Exception:
        rows = []
    skips: dict = {}
    verdicts: dict = {}
    gated_candidates = gated_gray = 0
    for r in rows[-500:]:
        if "skip" in r:
            skips[r["skip"]] = skips.get(r["skip"], 0) + 1
            continue
        verdicts[r.get("verdict", "?")] = verdicts.get(r.get("verdict", "?"), 0) + 1
        f = r.get("features", {})
        # §6 denominator = every gated will-expression incl. WEAK intent (felt want / cross-sentence
        # will). Bug fixed 2026-08-21: weak-only rows were excluded, so 59 GRAY verdicts reported a
        # gray-of-candidates of 0.0 — the exact metric the denominator law exists to protect.
        if r.get("gated") and (f.get("deed_grammar") or f.get("volition") or f.get("weak_intent")):
            gated_candidates += 1                   # §6 denominator: candidate literal intentions
            if r.get("verdict") == "GRAY":
                gated_gray += 1
    return {"rows": len(rows), "verdicts": verdicts, "skips": skips,
            "gray_of_candidates": (round(gated_gray / gated_candidates, 3)
                                   if gated_candidates else None),
            "verdict_note": "shadow only — no act is gated, HANDLE never routes to DEED"}
