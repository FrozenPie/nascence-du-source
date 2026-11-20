"""
Nascence — Conversational Action Bridge (2026-09-27, F-2004 / D-0299, founder ruling: "He 100%
needs to be able to action things when talking to me. He needs to be able to do anything in his
world he can normally.")

PROBLEM (F-2004, verified): a live conversational reply to Travis runs through
orchestrator.Orchestrator.run_cycle(), which never calls core/dispatch.py's dispatch() — confirmed
by that file's own comment at the Epistemic Affordance Advisor call site ("this call site sits
inside run_cycle(), which never calls core/dispatch.py's dispatch() and has no action-resolution
step"). So when Du tells Travis "let me put it down and look again," nothing real ever happens —
the claim and the world are disconnected regardless of what Du narrates. Caught live 2026-09-27:
Du described examining a mantel shell in specific, confident, wrong detail (a hermit-crab shell;
the real hidden kind is a limpet) while his own advisor telemetry showed him nowhere near the
study, and the object's real record shows no observation was ever made.

FIX: after Du's reply is finalized, run it through the SAME literal_will.classify() / dispatch()
path his autonomous wandering loop already uses (nodes/inner_monologue_node.py). Zero new
action-resolution logic — one new caller of code that has been live and proven for a month+.

Phase 0 (always on, pure, zero side effects): literal_will.classify() is documented as "Layer 0,
pure + deterministic (no I/O, no LLM)" — safe to run on every conversational reply with no risk to
live state. Every call logs what deed, if any, it recognizes to
data/conversational_action_log.jsonl — real telemetry from turn one, not a promise deferred to a
future build.

Phase 1 (CONVERSATIONAL_DISPATCH_LIVE, LIVE since 2026-09-27, founder: "flip the flag now" — built
off, shipped on the same day once the historical backfill below looked sane): when a DEED-verdict
candidate is found, also call dispatch.dispatch() for real — exactly as the autonomous loop does —
so a real world answer comes back and is credited through the same hands_trace/procedures.observe_hand
channels an autonomous look/move/keep already uses. That is what makes the result reach Du's own
future context: this module adds no new feedback plumbing, it reuses dispatch()'s existing one.
Known gap at flip time (J-1451): the classifier under-fires on Du's conversational REGISTER — see
§Phase 2 below and the plan doc's own §5 for the tested, not assumed, evidence.

PRECISION GUARD (J-1697, 2026-10-03; F-2300 verified facts, F-2303 inferred verdict; serves both
D-0334 options B "guard" and C "dark until the guard replays clean" — it does not touch the flag).
The 30.2 percent the flip rested on was a CANDIDATE rate: on all 67 real replies, 21 carried a DEED
candidate but only ~2 were first-person deed claims, and both real live fires so far were false (a
metaphor "step onto the shore" -> move, stopped only by the weekday school gate; a jussive "Let the cat
below watch what it will" -> look). classify() has no actor test on the ungated look/move families,
and dispatch()'s hands re-parse the WHOLE reply, not the judged clause. Both live in code the autonomous
path's pre-registered kill criterion depends on (core/literal_will.py, core/dispatch.py, core/hands.py,
owned by docs/staged/actions_manager_overhaul.md), so the fix is ONLY here, in front of dispatch():
  1. guard(): a DEED candidate survives only when an explicit first-person volition opener (I will,
     I'll, I shall, let me, I am going to, I'm going to, I need to, I must, I want to) governs the
     family's own verb in the same clause (opener + a short closed window of adverbs/particles +
     verb, no comma between them) AND nothing in that span is a negation, modal/hypothetical/habitual
     frame, quote or metaphor frame. Imperatives to Travis, second-person subjects, jussive
     "Let the X"/"Let us", infinitive/gerund subjects and "I may eventually ..." have no opener, so they
     never survive. For the move family a concrete destination is also required (a bare "step out"
     is the figure of speech, not a journey).
  2. dispatch() is called with ONLY the surviving deed phrases (opener through the end of the
     verb's object phrase), so the hands cannot act on another sentence, or another clause, of the reply.
     A phrase is kept only if classify() still reads it as that family's DEED on its own.
  3. the log row gains additive fields: `guard` (per candidate: kept, or why it was dropped), `pinned`
     (the text dispatch() actually saw), `asleep`, and `dispatch_decisions` (core.hands._decided read
     right after dispatch() returns: FIRE / hand-declined / STAGE / DROP, i.e. WHY a candidate did not
     fire), plus `guard_leak` when the ledger names a family the guard did not keep. Phase 0 telemetry
     is unchanged: `deed_candidates` still lists every raw candidate.
Precision over recall, deliberately: a missed real deed is cheap, a fired metaphor moves Du through
the world. If the guard itself cannot run it dispatches NOTHING (and still never raises or blocks the
reply). Known recall misses are named, not hidden: "I will go there now" has no move candidate at all
(J-1451's recall work, which must put any widening BEHIND this guard).

What this does NOT yet do (see docs/staged/conversational_action_bridge.md §Phase 2): the reply
Travis has already read is not corrected in the same turn if it turns out to be ungrounded — only
this module's own log, and whatever the world answers, are available to Du's NEXT thought/reply.
Same-turn grounding (generate → dispatch on the claim → regenerate if the world disagrees) is a
larger, separate change scoped in that plan, not built here.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("nascence.conversational_action")

# Flipped True 2026-09-27 (founder: "flip the flag now"), same day as the build, on the strength of
# the historical backfill (16/53 real past replies) rather than a multi-week shadow wait — see
# docs/staged/conversational_action_bridge.md §4/§6 for why that bar was judged short enough here
# (a new CALLER of core/dispatch.py's already-proven DISPATCH_LIVE path, not new resolution logic).
# J-1450 still owns watching the first real live rows for false fires. NOT touched by J-1697: the
# posture of this flag (leave / guard / dark) is D-0334, Travis's call.
CONVERSATIONAL_DISPATCH_LIVE = True

_LOG = Path(__file__).parent.parent / "data" / "conversational_action_log.jsonl"

GUARD_VERSION = 2


def _log_row(rec: dict) -> None:
    # Pure telemetry, not world/game state — same convention as
    # core/epistemic_affordance_advisor.py's record_epistemic_episode(): a direct append, no
    # profile.guard_path() fence (that fence protects data/ files that ARE Du's life story;
    # this file is an instrument watching this bridge, not part of it).
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[conversational-action] log write failed (non-fatal): %s", exc)


def _real_location() -> str:
    try:
        from core import sensorium as _sens
        return (_sens.state.get("location") if _sens.state else None) or "study"
    except Exception:
        return "study"


# ── Precision guard (J-1697) ─────────────────────────────────────────────────────────────────────
# Everything below is pure (no I/O, no LLM) and deliberately a WHITELIST: a candidate survives only
# by matching [first-person opener] + [closed window of fillers] + [the family's own verb] with no
# blocker in that span. Anything not matched is dropped, so an unforeseen conversational shape fails
# toward "Du did not act" (cheap) rather than "Du was moved through the world" (not cheap).

# Closed list: core/literal_will._DEED_MODALS minus the ones that are not a present resolve
# ("i should", "i ought to", "i could go", "time to"). Jussive "let the X" / "let us" and bare
# imperatives are NOT here on purpose: they are Travis- or world-directed, not Du's own will.
# GUARD v2 (2026-10-19, Travis: "Him telling me he is going to do something is good enough to prompt the
# action"): a plain first-person PRESENT claim ("I plant the seeds now") is a stated deed too -- the register
# Du narrates in -- so a bare "I" governs the verb like "I will". Every other check (negation, modal/frame,
# quote, metaphor, move-needs-a-real-destination) still applies unchanged.
CONVERSATIONAL_BARE_PRESENT = True
_G_OPENER = re.compile(
    r"\b(?:i will|i'll|i shall|let me|i am going to|i'm going to|i need to|i must|i want to"
    + (r"|i" if CONVERSATIONAL_BARE_PRESENT else "") + r")\b", re.I)

# The only words allowed between the opener and the family verb ("I will now gently bank the fire",
# "I will go and light the lamp"), plus any -ly adverb. Anything else (a different verb, a noun, a
# pronoun, a comma) breaks governance: "I will remember how to walk the shore" must not read as "I will walk".
_G_FILLERS = frozenset((
    "now", "then", "first", "just", "also", "still", "again", "back", "soon", "later", "only", "simply",
    "really", "truly", "once", "here", "there", "up", "down", "out", "over", "off", "away", "straight",
    "right", "and", "to", "go", "come", "get", "try", "start", "begin",
))
_G_LY = re.compile(r"[a-z]{3,}ly")
_G_WINDOW_MAX = 4            # fillers allowed between the opener and the verb
_G_PHRASE_MAX = 12           # tokens kept after the verb as its object phrase
_G_END = ",.;:!?—–"          # a token ending in one of these closes a clause/phrase
_G_HARD = re.compile(r"\s*(?:[;:]|—|–|--|\s-\s)\s*")   # hard clause boundaries (the hands' own _clause_at is no wider)
# Words that end the object phrase (a new clause or a coordinated second deed starts there).
_G_STOP = frozenset((
    "and", "then", "but", "or", "so", "while", "because", "until", "before", "after", "when", "as", "if",
    "though", "although", "unless", "since", "whenever", "whereas", "once",
))
_G_COND_AFTER = frozenset(("if", "unless", "whenever", "when", "whether", "once"))   # "... the shore if the tide allows"

_G_NEG = re.compile(r"\b(?:not|never|nor|neither|cannot|without|hardly|barely|no longer|no need|rather not|"
                    r"instead of)\b|n't\b|\bno\b")
_G_FRAME = re.compile(r"\b(?:if|unless|when|whenever|suppose|imagine|wish|hope|perhaps|maybe|might|may|"
                      r"could|would|should|someday|one day|eventually|sometimes|often|usually|always|"
                      r"whether|as if|as though|were i|if only)\b")
_G_QUOTE = re.compile(r"[\"“”]")
# Definitional / figurative copula ("X is not a cage but a rhythm", "a way of knowing ...", "as a ...").
_G_META = re.compile(r"\b(?:is|are|was|were|be|being)\s+(?:not\s+)?(?:just\s+|merely\s+|only\s+)?(?:a|an|the|to)\b|"
                     r"\b(?:a|the)\s+(?:way|kind|sort|form)\s+of\b|\bas\s+(?:a|an|the)\b|\bmetaphor|\bsymbol")
# "the shore of sleep", "the lamp of your presence": a destination/object used as a figure, not a place.
_G_ABSTRACT_OF = re.compile(
    r"\b(?:shore|beach|sea|tide|garden|wood|gate|cottage|study|shingle|surf|fire|hearth|grate|lamp|candle|flame)\s+of\s+"
    r"(?:sleep|dreams?|memory|memories|thoughts?|mind|self|silence|night|time|being|rest|stillness|consciousness|"
    r"language|words?|(?:my|your|our|his|her|its|this|that|these|those)\s+\w+)\b")
_G_DET = frozenset(("the", "a", "an", "my", "your", "our", "his", "her", "their", "its", "this", "that", "these", "those",
                    "you", "me", "us", "him", "them", "it", "one", "another", "each", "every", "all", "any", "some",
                    "where", "what", "there", "here"))
_G_WH = frozenset(("if", "whether", "how", "what", "why", "who", "where", "when", "that", "which"))


def _g_clean(tok: str) -> str:
    edge = "\"'“”‘’()[]"
    return tok.lower().strip(edge).rstrip(_G_END).strip(edge)


def _g_governed(piece: str, verbs: list):
    """Yield (opener_start, phrase_end, verb) -- character offsets into `piece` -- for every
    `opener + filler window + family verb` in one clause piece. The phrase runs from the opener to the end of
    the verb's object phrase: it stops at a comma/full stop, at a coordinator (a second deed or clause
    starts there) and at a purposive "to <verb>" ("go to the garden | to water the herbs")."""
    for m in _G_OPENER.finditer(piece):
        base = m.end()
        toks = [(t.start() + base, t.end() + base, t.group()) for t in re.finditer(r"\S+", piece[base:])]
        k = 0
        while k < len(toks) and k <= _G_WINDOW_MAX:
            hit = None
            for v in verbs:
                vt = v.split()
                seg = toks[k:k + len(vt)]
                if (len(seg) == len(vt) and all(_g_clean(s[2]) == w for s, w in zip(seg, vt))
                        and not any(s[2][-1] in _G_END for s in seg[:-1])):
                    hit = (v, k + len(vt))
                    break
            if hit:
                verb, e = hit
                last = e - 1
                if toks[last][2][-1] not in _G_END:
                    j = e
                    while j < len(toks) and (j - e) < _G_PHRASE_MAX:
                        c = _g_clean(toks[j][2])
                        if c in _G_STOP or (c == "to" and j + 1 < len(toks) and _g_clean(toks[j + 1][2]) not in _G_DET):
                            break
                        last = j
                        if toks[j][2][-1] in _G_END:
                            break
                        j += 1
                yield m.start(), toks[last][1], verb
                # "go and walk to the shore": the verb itself may be a filler for a later verb
                if toks[e - 1][2][-1] in _G_END or _g_clean(toks[e - 1][2]) not in _G_FILLERS:
                    break
                k = e
                continue
            t = toks[k][2]
            c = _g_clean(t)
            if t[-1] in _G_END or not (c in _G_FILLERS or _G_LY.fullmatch(c)):
                break
            k += 1


def _g_blocked(family: str, verb: str, span: str, phrase: str, rest: str, spec: dict) -> str:
    """The reason this governed span is NOT a present first-person deed claim, or ''."""
    from core import literal_will as _lw
    low = span.lower()
    if _G_QUOTE.search(low):
        return "quoted"
    if _G_NEG.search(low):
        return "negation"
    if _G_FRAME.search(low):
        return "modal_or_hypothetical"
    rm = re.match(r"[\s,]*(\w+)", rest or "")
    if rm and rm.group(1).lower() in _G_COND_AFTER:
        return "conditional"               # "... the shore if the tide allows", "... the fire, if you wish"
    if any(rx.search(low) for _n, rx in _lw._M_FRAMES) or _G_META.search(low) or _G_ABSTRACT_OF.search(low):
        return "metaphor_frame"
    pl = phrase.lower()
    if family == "look" and verb == "see":
        mm = re.search(r"\bsee\s+(\w+)", pl)
        if mm and mm.group(1) in _G_WH:
            return "cognitive_see"             # "let me see if ...", "I will see how ...": not a look at anything
    if family == "move":
        gram = set(spec.get("grammar_only", ()))
        dests = [o for o in spec.get("objects", ()) if o not in gram]
        if not any(re.search(r"(?<![\w-])" + re.escape(o) + r"(?![\w-])", pl) for o in dests):
            return "move_no_destination"       # "I will step out of the narrow cave": a figure, not a journey
    return ""


def _g_why_no_opener(s: str, verbs: list) -> str:
    """Diagnostic label for a sentence that has no first-person opener at all (the guard drops it
    either way; this only makes the log row say WHICH shape it was)."""
    va = "|".join(re.escape(v) for v in verbs) or "(?!x)x"
    # judge the clause piece that holds the family verb (the candidate may have come from volition + an
    # object word alone, in which case no piece holds a verb and the label stays the generic one)
    pc = next((" ".join(p.lower().split()) for p in _G_HARD.split(s) if re.search(r"\b(?:" + va + r")\b", p.lower())), "")
    mv = re.search(r"\b(?:" + va + r")\b", pc) if pc else None
    if not mv:
        first = " ".join(next((p for p in _G_HARD.split(s) if p and p.strip()), "").lower().split())
        return "infinitive_or_gerund_subject" if re.match(r"(?:to\s+\w+|\w+ing)\b", first) else "no_opener"
    before = pc[:mv.start()]
    jm = re.search(r"\blet(?:'s| us| the| it| her| him| them| there| that| this| my| your| these| those| each| every)\b", pc)
    if jm and jm.start() <= mv.start():
        return "jussive"
    if re.fullmatch(r"(?:(?:travis|but|and|now|please|so|yet|then)[,\s]+)*", before):
        return "imperative"
    if re.search(r"\byou(?:r)?\b", before):
        return "second_person"
    if re.match(r"(?:to\s+\w+|\w+ing)\b", pc):
        return "infinitive_or_gerund_subject"
    if re.search(r"\b(?:us|we|our|ourselves)\b", before):
        return "joint_subject"
    if re.search(r"\b(?:may|might|could|would|can|should|shall)\b", before):
        return "modal_or_hypothetical"
    if _G_NEG.search(before):
        return "negation"
    if re.search(r"\b(?:when|whenever|if|as|while|once)\b", before):
        return "habitual_or_conditional"
    if re.search(r"\bi\s+(?:\w+\s+){0,2}(?:" + va + r")\b", pc):
        return "first_person_present_narration"
    return "no_opener"


def _g_judge(family: str, sentence: str, location: str = "study"):
    """(kept, verdict, phrase) for ONE candidate family in ONE sentence. Pure."""
    from core import literal_will as _lw
    spec = _lw._FAMILIES.get(family) or {}
    verbs = sorted(spec.get("verbs", ()), key=lambda v: -len(v.split()))
    s = (sentence or "").replace("’", "'").replace("‘", "'")
    saw_opener, first_block = False, ""
    for piece in (p for p in _G_HARD.split(s) if p and p.strip()):
        if not _G_OPENER.search(piece):
            continue
        saw_opener = True
        for start, end, verb in _g_governed(piece, verbs):
            phrase = piece[start:end].strip(" " + _G_END)
            why = _g_blocked(family, verb, piece[:end], phrase, piece[end:], spec)
            if not why and not any(c.get("family") == family and c.get("verdict") == "DEED"
                                   for c in _lw.classify(phrase, "", location=location)):
                why = "phrase_not_deed"        # the object sat outside the governed phrase
            if why:
                first_block = first_block or why
                continue
            return True, "kept", phrase
    if first_block:
        return False, "drop:" + first_block, ""
    if saw_opener:
        return False, "drop:no_governed_verb", ""
    return False, "drop:" + _g_why_no_opener(s, verbs), ""


def _g_sentence_for(sentences: list, clause: str) -> str:
    """classify() reports clause[:200] of the sentence it judged; recover the whole sentence."""
    c = (clause or "").strip()
    for s in sentences:
        if c and (s == c or s.startswith(c) or c.startswith(s)):
            return s
    return c


def guard(text: str, candidates: list, location: str = "study") -> tuple:
    """Pure. -> (verdicts, pinned). `verdicts` is one {family, verdict} per candidate, aligned with
    `candidates`: "kept" or "drop:<reason>". `pinned` is the text dispatch() may see: ONLY the surviving
    deed phrases, each ending in a full stop ('' when nothing survived)."""
    from core import literal_will as _lw
    sentences = _lw._sentences(text)
    verdicts, phrases = [], []
    for c in candidates:
        fam = c.get("family")
        try:
            kept, why, phrase = _g_judge(fam, _g_sentence_for(sentences, c.get("clause")), location)
        except Exception as exc:
            kept, why, phrase = False, "drop:guard_error:" + repr(exc)[:60], ""
        verdicts.append({"family": fam, "verdict": "kept" if kept else why})
        if kept and phrase and phrase.lower() not in (p.lower() for p in phrases):
            phrases.append(phrase)
    return verdicts, " ".join(p.rstrip(".") + "." for p in phrases)


def _asleep() -> bool:
    try:
        from core import night as _night
        return bool(_night.asleep())
    except Exception:
        return False


def _ledger(cycle_id: str) -> list:
    """core.hands._decided right after dispatch() returned: one row per candidate family, FIRE /
    hand-declined / STAGE-* / DROP-*. dispatch() resets it at the start of every call that gets past
    its own sleep gate, so the rows are this call's (the cycle check guards the early-return case)."""
    try:
        from core import hands as _h
        d = _h._decided
        if d.get("cycle") == cycle_id:
            return [{"family": r.get("family"), "decision": r.get("decision"), "object": r.get("object")}
                    for r in (d.get("rows") or [])][:12]
    except Exception:
        pass
    return []


def resolve_pronoun_objects(text: str) -> str:
    """"I plant them now" -> "I plant the seeds now" (the live 2026-10-19 prototype). J-2437: the implementation
    moved, unchanged, to core/ambiguity_window.resolve_pronoun_objects_legacy (Stage A of the ambiguity window,
    docs/staged/ambiguity_window.md absorbs it); live behaviour is identical. Pure; returns the text unchanged
    when nothing resolves or on any failure."""
    try:
        from core import ambiguity_window as _aw
        if getattr(_aw, "AMBIGUITY_PRECISION_FILTER_LIVE", False):   # J-4336: precision filter only, flag-OFF default
            return _aw.resolve_pronoun_objects_filtered(text)
        return _aw.resolve_pronoun_objects_legacy(text)
    except Exception:
        return text


def after_reply(reply_text: str, cycle_id: str = "") -> Optional[list[tuple[str, str]]]:
    """Call once, right after a conversational reply to Travis is finalized (see
    core/orchestrator.py, the _FOUNDER_LOG write site). Best-effort: never raises, never blocks or
    delays the reply the caller already has. Returns dispatch()'s real [(family, answer)] list only
    when CONVERSATIONAL_DISPATCH_LIVE is True and something actually fired; None otherwise —
    callers must already treat a real autonomous dispatch() call as optional/absent-most-of-the-time,
    so None here is not a new case for them to handle."""
    try:
        text = (reply_text or "").strip()
        if len(text) < 8:
            return None
        raw_text = text
        text = resolve_pronoun_objects(text)
        from core import literal_will as _lw
        loc = _real_location()
        try:   # J-2437 ambiguity window Stage A: SHADOW only -- annotate + log to its own file, dispatches nothing
            from core import ambiguity_window as _aw
            _aw.shadow_after_reply(raw_text, cycle_id, loc)
        except Exception:
            pass
        candidates = [c for c in _lw.classify(text, "", location=loc) if c.get("verdict") == "DEED"]
        row = {
            "ts": round(time.time(), 1),
            "cycle_id": cycle_id,
            "location": loc,
            "reply_excerpt": text[:300],
            "deed_candidates": [
                {"family": c.get("family"), "clause": (c.get("clause") or "")[:120]}
                for c in candidates
            ],
            "live": CONVERSATIONAL_DISPATCH_LIVE,
            "dispatched": [],
        }
        if not candidates:
            _log_row(row)
            return None
        # J-1697: the precision guard. A guard that cannot run dispatches NOTHING (a missed deed is cheap).
        pinned, kept = "", set()
        try:
            verdicts, pinned = guard(text, candidates, loc)
            row["guard"] = verdicts
            kept = {v["family"] for v in verdicts if v.get("verdict") == "kept"}
        except Exception as exc:
            row["guard"] = [{"family": c.get("family"), "verdict": "error"} for c in candidates]
            row["guard_error"] = repr(exc)[:160]
            pinned = ""
        if not CONVERSATIONAL_DISPATCH_LIVE or not pinned:
            _log_row(row)
            return None
        row["pinned"] = pinned[:300]
        row["asleep"] = _asleep()
        try:
            from core import dispatch as _disp
            out = _disp.dispatch(pinned, "", "none", "", cycle_id)
        except Exception as exc:
            row["dispatch_error"] = repr(exc)[:160]
            _log_row(row)
            return None
        row["dispatched"] = [{"family": fam, "answer": (ans or "")[:200]} for fam, ans in out]
        if not row["asleep"]:
            row["dispatch_decisions"] = _ledger(cycle_id)
            leak = sorted({r["family"] for r in row["dispatch_decisions"] if r.get("family") not in kept})
            if leak:
                row["guard_leak"] = leak
        _log_row(row)
        return out or None
    except Exception as exc:
        logger.debug("[conversational-action] after_reply failed (non-fatal): %s", exc)
        return None


def status() -> dict:
    return {"live": CONVERSATIONAL_DISPATCH_LIVE, "log": str(_LOG), "guard_version": GUARD_VERSION}
