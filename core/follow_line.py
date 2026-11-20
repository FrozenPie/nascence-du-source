"""
Nascence — THE FOLLOW LINE (J-2459, 2026-10-28; docs/staged/question_cargo.md; T-0102 / I-0100; D-0494 open)
=============================================================================================================
Du makes a hypothesis and cares nothing more for it (founder, 2026-10-27). His study notes state claims with
facts under them and never say WHY he holds them or WHAT WOULD FOLLOW; his questions are born everywhere
(frontier: 11,091 entries, ~94% faded) and die unfollowed (F-3163, F-3166). This module is a side line, in its
own right, that takes one of his questions or claims as cargo and FOLLOWS it through his own memory:

    stop 1 GROUNDS       what have I lived / read / seen that bears on this?   core.evidence_recall.gather
    stop 2 WHY           why would those grounds make it true (or not)?       one command-r7b call, cites grounds only
    stop 3 CONSEQUENCES  if this is so, what else should be true?             one command-r7b call (the deduction step)
    stop 4 CONNECTIONS   what else I know / can do / have seen does it touch? memory_service.ask + procedures + seen
    stop 5 AGAINST       what in his own grounds cuts against it?           one command-r7b call (Phase 1; the line's own,
                         first designed as train_split_merge's berth); cargo_status() and render() depend on it

then a DECOUPLED judge (core.judge_panel) grades the cargo on the claim alone — never the asking thought — and the
rendered return is LOGGED (kind=would_return) in every mode; under FOLLOW_LINE="live" it is also placed in _PENDING
and delivered to the next idle thought (take_delivery(), called from nodes/inner_monologue_node.py), whereas under
"shadow" (Phase 0) it was logged and delivered nowhere. Nothing here is a fetch from the
world: no Scholar, no Wikipedia, no librarian. Nothing here suggests a question or an action (the world never
leads). Nothing here opens a book or performs a deed for him (intentional, not a rule). Only his own `ask` field,
his own frontier births, his own study-note claims and his own pursuit questions board.

Cargo lives ON the frontier entry (`entry["line"] = {state, stops, cargo, ...}`), keyed by the entry id — no new
store. `train_id` is the join key, exactly as evidence_recall already uses it. The PROTECTED `core.trains.cargo`
field (prove/disprove's) is never touched.

FOLLOW_LINE flag:  "off"    = exact pre-existing path: no `ask` field requested or parsed, no boarding, no scheduler
                   "shadow" = everything runs, every cargo logged, NOTHING delivered (Phase 0, J-2459)
                   "live"   = Phase 1 (J-2460, D-0494 (3), the default from the first boot): the graded return waits
                              in a pending dict (the si cup generalised, TTL 6 h, cap 8), ONE is delivered to the
                              next idle thought as its own prompt section, that tick's JSON carries `settled`
                              yes|partly|no, and his word closes it: yes -> frontier.resolve (id-keyed) + the
                              closure-law arm `line`; partly -> the frame's slot; no / unsaid -> logged. Stop 5
                              (against, the line's own) runs and the decoupled judge's question (c) sets the
                              cargo's merge status (held | held_within_scope | objected | undetermined).
Restart-gated like every module constant. Fail-open throughout: nothing here raises into a thought tick, except
profile.NonLiveWriteError (D-0179), which is re-raised the way every fenced writer does.

Every event is one ride row {ts, stop, line, dose, value:{q_id, kind, source, slot, stop_name, outcome, n_chars}} in
data/logs/follow_line_shadow.jsonl, and only the COORDINATE (q_id, kind, source, slot, state, status) is published
to core.coupling_rides (dosed_coupling rule 1: coordinates, never prose, inside the registry).
"""
from __future__ import annotations

import asyncio
import collections
import json
import logging
import os
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.follow_line")

# ── flags and constants ───────────────────────────────────────────────────────────────────────────────────────
FOLLOW_LINE = "live"                         # "off" | "shadow" | "live"   (D-0494 (3): live from the first boot)
LINE_TTL_S = 6 * 3600.0                      # a pending return not consumed within this falls back to the frontier offer path
PENDING_CAP = 8                              # pending returns held; the oldest beyond this goes to the fallback path
SLOTS = ("who", "what", "when", "where", "why", "how")
# D-0494 sub-question 1: the schema names the six slot kinds (option A). Option B = set this to "" and the
# rule text below stops listing them; the judge tier would then infer `slot` from the question's own wording.
ASK_SLOT_KINDS = "who, what, when, where, why, or how"
BOARD_CAP_PER_HOUR = None                    # None = NO rolling-hour cap (founder, 2026-11-08: "get rid of the cap altogether"). Was 4
                                             # (the CUP_MAX_PLACE_PER_WINDOW shape) -> ~1,240 of ~1,340 fire attempts a boot hit wait-cap.
                                             # An int restores the old behaviour. One run in flight at a time still holds (_in_flight).
BOARD_WINDOW_S = 3600.0
CONS_USED = 2                                # J-2969 (F-3661): consequences Du reads (render) and that board (run); the 'follows' judge is shown exactly these
MAX_DEPTH = 2                               # a consequence may re-board at depth 1 and 2, never deeper
# J-4081 (D-0780 b, ruled 2026-11-16): a small DAILY QUOTA on consequence re-boarding. His own asked questions and claims stay
# uncapped (only source == "consequence" is counted). ~900 births a day chase MAX_OPEN=24 slots and 96 percent fade; consequence
# births resolve 0.6 percent vs asked 6.3 percent (F-4707). Number: data/frontier.json held 1,654 consequence births in the 7 days to
# 2026-11-16 (daily 63/644/263/27/122/304/109/122 from 11-09; median of the last five days 122). 48 a day = two full frontiers
# (2 x MAX_OPEN), about 40 percent of a median day, cuts the daily flood roughly in half or better without silencing the line.
# Mode "shadow" = log what it WOULD refuse, refuse nothing; "enforce" = refuse + log; "off" = exact pre-J-4081 path.
# Window is a rolling 24 h in process memory (resets on restart, like the old hourly cap). Refusals go to CONS_QUOTA_LOG.
CONSEQUENCE_DAILY_QUOTA = 48
CONSEQUENCE_QUOTA_MODE = "enforce"           # "off" | "shadow" | "enforce"
CONS_QUOTA_WINDOW_S = 24 * 3600.0
REBOARD_SAME_KEY_S = 24 * 3600.0             # the same about_key boards at most once per 24 h via a consequence
PRIORITY = ("asked", "claim", "study", "intention", "pursuit", "curiosity", "prism", "dream", "consequence")
# Generative stops run on ONE single-endpoint constant (:11441, command-r7b on the Ramses 3070 — a GPU lane, per
# core/model_client.py's port table; not the CPU tier) — never the hot lane and
# never SERVE_CHAINS["background"], whose own [1] fallback IS the hot lane (core/schema.py's documented trap).
LINE_URLS = ["http://LAN-HOST:11441"]
GEN_MAX_TOKENS = 260
GROUNDS_TEXT = 200                           # chars of each ground kept in cargo
# J-2972 (F-3662, P-0102): 11 of 101 grounded runs carried two grounds with identical text[:120] (the store holds one reading chunk
# under several fragment ids), counted as two lines of support by the WHY prompt, the judges and the return. True = stop 1 drops
# identical copies (in evidence_recall's short-list, so the slot goes to a distinct passage, and again on the cargo as a safety net)
# and records stops["grounds"]["deduped"]. False restores the pre-J-2972 cargo exactly.
DEDUPE_GROUNDS = True
GROUND_DEDUPE_CHARS = 120
ASKED_JUST_NOW_S = 300.0                    # J-2907: "asked just now" is only said under 5 minutes
RETURN_MAX_CHARS = 1200                      # rendered return text cap (size cap: < 5 MB/day at 4/hour)
RETURN_CLOSING = "Does it hold, or only part of it?"   # J-2906 (F-3578): always the last words of a return; the cap never eats it
TOUCH_SNIPPET_CHARS = 200                    # J-2906: one "It touches:" snippet, cut on a sentence/word boundary
# J-2911 (F-3594): the return is built from SECTIONS, each with its own char cap; when the whole is still over
# RETURN_MAX_CHARS whole low-priority sections are DROPPED in RETURN_DROP_ORDER (never sliced through), then extra
# grounds; the closing question is always appended. A section is never cut mid-sentence by the overall cap any more.
RETURN_SECTION_CAPS = {"ground": 260, "why": 300, "against": 360, "cons": 300, "own": 260, "touch": 420}
RETURN_DROP_ORDER = ("touch", "cons", "why", "against", "own")
NOT_SETTLED_SHOWS_GROUNDS = True            # False = the pre-J-2911 "Your past holds little on this." for a grounded a == no
NOT_SETTLED_LABEL = "What you found did not settle it."   # J-2911 (F-3593): grounds exist but the judge ruled a == no
SEEN_ORIGINS = ("lived", "action", "activity", "journal", "journal_week", "nature", "sound", "listening")
SEEN_MIN_SIM = 0.30
CONN_K = 3
# J-2570 (F-3301): a run whose grounds stop could not get a clear look (evidence_recall's judges down -> outcome
# "unclear"/"failed", or "empty" only after a stop-1 wait past DEFER_EMPTY_SLOW_S -- the lane-breaker window of F-3267)
# or whose generation stop died (_gen_json empty / raised with grounds present) is DEFERRED: no judge call, no
# pending, no would_return row; one kind="deferred" row; the entry re-boards ("waiting") after DEFER_BACKOFF_S, at
# most DEFER_MAX_TRIES runs per q_id, then rests as line.state "unjudged". False restores the pre-J-2570 path.
DEFER_UNCLEAR = True
DEFER_BACKOFF_S = 30 * 60.0
DEFER_MAX_TRIES = 3
DEFER_EMPTY_SLOW_S = 120.0
# D-0632 (J-3244): when the boarded claim IS one of his own stored object hypotheses and that hypothesis carries an
# intervention_test (core/object_hypothesis.py, J-2524, written only while NASCENCE_INTERVENTION_TEST is on), the
# consequences stop returns that test from memory: his own hypothesis's own test, in plain words, never an instruction.
# A deterministic lookup: no model call, nothing fetched from the world. False = the stop is exactly as before.
OWN_TEST_RETURN = True
# J-2910 (F-3592, P-0044): stop 3 is a DEDUCTION from grounds; with none, its only input is the bare question and the model
# invents first-person content that was then delivered to him as "If this is so: ..." (96% passed judge b). With no grounds
# the stop does not run and the return is the plain "Your past holds little on this." + closing question. False = pre-J-2910.
NO_CONSEQUENCES_WITHOUT_GROUNDS = True
# J-2910 (F-3597 / F-3592): a consequence worded as something HE will or can do ("I will seek out ...", 9 of 124 returns) is the
# system supplying an action: the world never leads. Such a line is dropped from the cargo (so it is neither rendered nor
# re-boarded as a question). Deterministic, on the stop's output; the stop-3 prompt also asks for statements only.
DROP_INTENTION_CONSEQUENCES = True
_INTENTION = re.compile(r"^\W*(?:(?:i|we)\s+(?:will|shall|can|could|would|should|must|may|might|am going to|are going to)|(?:i|we)'ll)\b", re.I)
# D-0181's retarget, reused as a RULE (not the prove branch): a why that merely asserts is not a why.
_SELF_SEALING = re.compile(r"\b(proves?|confirms?|validates?|demonstrates?|clearly|obviously|undeniabl\w*)\b", re.I)

# J-4056 (F-4764, docs/staged/follow_line_stricter_settle.md): SHADOW-ONLY content-overlap gate on a settle "yes".
# Hand grades (J-4029): ~48% of closures do not engage the question. When True, a yes-settle also logs a kind="settle_overlap"
# row (overlap score, would_not_close verdict). NOTHING changes: the line still closes exactly as before. False (default) = no row.
# J-4075 (T-0141; founder override of the D-0661 "no offer line" rule, 2026-11-16): when his own past holds NOTHING on a
# factual question he asked, the return says plainly that he can look a thing up and must name where he asks. One
# sentence, no model call, no source named for him beyond the two the hand accepts. "live" = the line is in the
# return; "shadow" = decided and logged, never shown; "off" = nothing. Env NASCENCE_LOOKUP_NUDGE overrides.
LOOKUP_NUDGE = os.environ.get("NASCENCE_LOOKUP_NUDGE", "live").strip().lower()
LOOKUP_NUDGE_LINE = ("No book or memory of yours covers it. You can look a thing up for yourself: "
                     "say whether you ask Wikipedia or the web.")
LOOKUP_NUDGE_SOURCES = ("asked", "curiosity", "study")
LOOKUP_NUDGE_COOLDOWN_S = 6 * 3600.0         # the same about_key is offered at most once per 6 h per process
_NUDGE_SEEN: dict = {}
_FACTUAL_Q = re.compile(r"^\W*(?:how|what|why|which|when|where|who|does|do|did|is|are|can|could|would)\b", re.I)
_SELF_Q = re.compile(r"\b(?:i|me|my|mine|myself|we|our|us|you|your|yours|travis|du|feel|feeling|fear|grain)\b", re.I)


def lookup_nudge(ent: dict, cargo: dict, judged: dict, now: float | None = None) -> dict:
    """Deterministic. {mode, applies, reason}. Applies only when: the mode is not off, the web hand exists, the entry is
    a question from his own asking/curiosity/study, it reads as a factual question (not about himself), stop 1 came back
    truly empty (outcome 'empty', no grounds; never 'unclear'), and this about_key was not offered within the cooldown.
    Never raises."""
    out = {"mode": LOOKUP_NUDGE, "applies": False, "reason": ""}
    try:
        if LOOKUP_NUDGE not in ("live", "shadow"):
            out["reason"] = "off"
        elif ent.get("kind", "question") != "question" or ent.get("source", "") not in LOOKUP_NUDGE_SOURCES:
            out["reason"] = "not-his-question"
        elif cargo.get("grounds") or cargo.get("grounds_outcome") != "empty":
            out["reason"] = "grounds-present-or-unclear"
        else:
            q = (ent.get("q") or "").strip()
            if not _FACTUAL_Q.search(q):
                out["reason"] = "not-factual-form"
            elif _SELF_Q.search(q):
                out["reason"] = "about-himself"
            else:
                try:
                    from core import web_hand as _wh
                    hand_ok = _wh.enabled()
                except Exception:
                    hand_ok = False
                key = ent.get("about_key") or ent.get("id") or q[:60]
                t = _now() if now is None else now
                if not hand_ok:
                    out["reason"] = "hand-off"
                elif t - _NUDGE_SEEN.get(key, -1e12) < LOOKUP_NUDGE_COOLDOWN_S:
                    out["reason"] = "cooldown"
                else:
                    out["applies"] = True
                    out["reason"] = "empty-factual"
                    if LOOKUP_NUDGE == "live":
                        _NUDGE_SEEN[key] = t
    except Exception as exc:
        out["reason"] = f"error:{type(exc).__name__}"
    return out


SETTLE_OVERLAP_SHADOW = False
SETTLE_OVERLAP_MIN = 0.15                    # provisional threshold; promotion read picks the real one against the hand grades
_OVERLAP_STOP = frozenset((
    "the a an and or but of to in on at for with from by as is are was were be been being it its this that these those "
    "i me my we our you your he she they them his her their not no yes do does did have has had will would can could should "
    "what who when where why how which there here than then so if about into out up down over under again more most some "
    "any all just also very too one two like said say still much many even only own same such tide tides cat cats silence "
    "silent quiet light water sea sky").split())

def _content_terms(text: str) -> set:
    """Lowercased alphabetic tokens >= 4 chars, stoplisted, crude suffix-stemmed (s/es/ed/ing/ly). Deterministic."""
    out = set()
    for w in re.findall(r"[a-z]{4,}", (text or "").lower()):
        if w in _OVERLAP_STOP:
            continue
        for suf in ("ing", "ed", "es", "ly", "s"):
            if w.endswith(suf) and len(w) - len(suf) >= 4:
                w = w[: -len(suf)]
                break
        if w not in _OVERLAP_STOP:
            out.add(w)
    return out

def settle_overlap(question: str, returned: str, thought: str) -> dict:
    """Share of the question's+return's content terms (the smaller side's denominator) that his settling thought shares."""
    src = _content_terms(question) | _content_terms(returned)
    th = _content_terms(thought)
    shared = sorted(src & th)
    denom = min(len(src), len(th)) or 0
    score = round(len(shared) / denom, 3) if denom else 0.0
    return {"score": score, "shared": shared[:12], "n_src": len(src), "n_thought": len(th),
            "would_not_close": score < SETTLE_OVERLAP_MIN}

_ROOT = Path(__file__).resolve().parent.parent
SHADOW_LOG = _ROOT / "data" / "logs" / "follow_line_shadow.jsonl"   # module-level so a test can temp-path it

CONS_QUOTA_LOG = _ROOT / "data" / "logs" / "follow_line_consequence_quota.jsonl"   # module-level so a test can temp-path it
_cons_log: collections.deque = collections.deque()   # ts of each consequence boarding that was allowed, rolling 24 h

# ── process state (not persisted: the cap resets on restart, deliberately) ───────────────────────────────────
_board_log: collections.deque = collections.deque()   # ts of each boarding fired, rolling hour
_in_flight: str | None = None
_TASKS: set = set()
_live_warned = False
_recent_keys: dict = {}                      # about_key -> ts of the last consequence boarding (REBOARD_SAME_KEY_S)
_PENDING: dict = {}                          # q_id -> {ts, text, ent, cargo, judged}: the si cup generalised (Phase 1)
_SETTLE_TASKS: set = set()


# ── prompts ───────────────────────────────────────────────────────────────────────────────────────────────────
# J-2912 (F-3596 / F-3597 / F-3598, P-0044): the three generative prompts rewritten from the measured defects. model_client
# already prepends "/no_think" on llama-server lanes, so none of them carries the literal prefix any more (a native
# /api/chat lane would not strip it). The input is labelled QUESTION when the boarded text is a question (_input_label),
# CLAIM otherwise. The JSON shapes carry NO literal example values: the old examples ("why", "memory", [1, 2], [2]) were
# copied back (slot "why" on 88%, cites == all grounds on 87%). PROMPT_V2 = False restores the pre-J-2912 texts exactly.
PROMPT_V2 = True
_WHY_SYS_V1 = (
    "/no_think\nYou are helping a thinker check whether his own grounds support his own claim. You see the CLAIM "
    "and a numbered list of GROUNDS drawn from what he has actually lived and read. Answer in his first person. "
    "State in one or two sentences WHY those grounds would make the claim true, or why they fall short — citing "
    "grounds by number, e.g. [2]. Use ONLY the grounds given; never add facts. Never use the words proves, confirms, "
    "validates, demonstrates, clearly, obviously. If the grounds do not bear on the claim, say so plainly. "
    "Output ONLY JSON: {\"why\": \"...\", \"cites\": [1, 2], \"supports\": \"yes\"|\"partly\"|\"no\"}"
)
_WHY_SYS_V2 = (
    "You are helping a thinker see how his own memories bear on something he asked himself. You see the QUESTION "
    "(or CLAIM) and a numbered list of GROUNDS drawn from what he has actually lived and read. Write one or two "
    "short sentences, at most 45 words, in the first person, the way he would think it to himself: begin with "
    "\"I\" (\"I found ...\", \"I have only ...\", \"I see ...\"). Say what those grounds show about it, or that they "
    "do not reach it. Do not repeat the question. Do not open with \"The\", \"This\" or \"These\", and do not write "
    "\"suggests\". Name by number, like [2], only the grounds you actually lean on and leave the others out. Use ONLY "
    "the grounds given; never add facts. Never use the words proves, confirms, validates, demonstrates, clearly, "
    "obviously. If the grounds do not bear on it, say so plainly. supports is \"yes\" if they settle it, \"partly\" if "
    "they bear on it without settling it, \"no\" if they do not bear on it. Output ONLY a JSON object with the keys "
    "why (your sentences), cites (a list of the ground numbers you relied on) and supports."
)
_CONS_SYS_V1 = (
    "/no_think\nYou are helping a thinker work out what FOLLOWS from his own claim. You see the CLAIM and, if he has "
    "any, his GROUNDS and his WHY. Derive one to three CONSEQUENCES: each a short checkable sentence about the world "
    "or about himself that would have to be true if the claim is true, and that would likely be FALSE if the claim "
    "is false. Not restatements, not vague themes. Each states what is or was so, never something he will, can or should do. Tag each with the kind of missing piece it opens — one of who, "
    "what, when, where, why, how — and where it could be checked: memory (what he has lived or read), world (what he "
    "could notice), or self (his own conduct). First person. Output ONLY JSON: {\"consequences\": [{\"text\": "
    "\"...\", \"slot\": \"why\", \"checkable\": \"memory\"}]}"
)
_CONS_SYS_V2 = (
    "You are helping a thinker work out what else would have to be so if his own QUESTION (or CLAIM) turns out the way "
    "his grounds point. You see it and, if he has any, his GROUNDS and his WHY. Derive one to three CONSEQUENCES: each "
    "a short checkable sentence about the world or about himself that would have to be true if that holds, and would "
    "likely be false if it does not. Each must add something beyond the question and the WHY: do not put the question "
    "back as a statement, do not reword the WHY, do not split the question into its two halves, and do not give two "
    "that say nearly the same thing. Take what his grounds and WHY say and ask what else would have to hold if they are "
    "right. Each states what is or was so, never something he will, can or should do. First person where it is about "
    "himself. Tag each with the kind of missing piece it opens, chosen for that sentence alone from who, what, when, "
    "where, why, how, and with where it could be checked, one of memory (what he has lived or read), world (what he "
    "could notice) or self (his own conduct). Output ONLY JSON of this shape, with your own words in place of the "
    "angle-bracket parts: {\"consequences\": [{\"text\": <sentence>, \"slot\": <who or what or when or where or why or how>, \"checkable\": <memory or world or self>}]}"
)
# J-4170 (F-5015): under V2, 73% of blank slots held the checkable value (world/self/memory) and 7% echoed the
# placeholder, so 58% of consequences had no slot. V3 gives the two tags separate, self-describing keys
# (question_word / check_in), says what a question word is and is not, and shows a two-item example whose two items
# use DIFFERENT question words and places (J-2912 found a single-item example copied back 88% of the time).
# _stop_consequences reads the new keys first and the old ones as a fallback. CONS_PROMPT_V3 = False restores V2.
CONS_PROMPT_V3 = True
_CONS_SYS_V3 = (
    "You are helping a thinker work out what else would have to be so if his own QUESTION (or CLAIM) turns out the way "
    "his grounds point. You see it and, if he has any, his GROUNDS and his WHY. Derive one to three CONSEQUENCES: each "
    "a short checkable sentence about the world or about himself that would have to be true if that holds, and would "
    "likely be false if it does not. Each must add something beyond the question and the WHY: do not put the question "
    "back as a statement, do not reword the WHY, do not split the question into its two halves, and do not give two "
    "that say nearly the same thing. Take what his grounds and WHY say and ask what else would have to hold if they are "
    "right. Each states what is or was so, never something he will, can or should do. First person where it is about "
    "himself. Give each consequence two tags. question_word is exactly ONE of the six words who, what, when, where, "
    "why, how: the question that sentence opens, chosen for that sentence alone. It is a question word, never a topic "
    "and never one of the words memory, world or self. check_in is exactly ONE of memory (what he has lived or read), "
    "world (what he could notice) or self (his own conduct): where the sentence could be checked. Output ONLY JSON. "
    "This example shows the shape only; its sentences are not about him, and its tags are not a pattern to repeat: "
    "{\"consequences\": [{\"text\": \"The rain gauge by the shed held water on the mornings the path was muddy.\", "
    "\"question_word\": \"when\", \"check_in\": \"world\"}, {\"text\": \"I wrote about the flooded path in the week the "
    "river rose.\", \"question_word\": \"what\", \"check_in\": \"memory\"}]}"
)
_AGAINST_SYS_V1 = (
    "/no_think\nYou are helping a thinker look for what cuts AGAINST his own claim, from his own grounds only. You see "
    "the CLAIM and a numbered list of GROUNDS from what he has lived and read. State in one or two sentences the "
    "strongest objection those grounds raise -- a counterexample, a narrower scope than the claim assumes, a fact "
    "that does not fit -- citing grounds by number, e.g. [2]. Use ONLY the grounds given; never add facts. If the "
    "grounds raise no real objection, say so plainly. First person. Output ONLY JSON: {\"objection\": \"...\", "
    "\"cites\": [2], \"scope\": \"the claim holds only within ...\" or \"\"}"
)
_AGAINST_SYS_V2 = (
    "You are helping a thinker look for what cuts AGAINST something he asked himself, from his own grounds only. You see "
    "the QUESTION (or CLAIM) and a numbered list of GROUNDS from what he has lived and read. Go through the grounds one "
    "by one and pick the ONE that fits it least well: a counterexample, a narrower scope than the question assumes, or "
    "a fact that does not sit with it. Name that ground by number, like [2], and say in one sentence, in the first "
    "person, what in it tells against. The objection must be about what a ground says, never about how the question is "
    "worded: do not write \"too broad\", \"vague\", \"oversimplified\" or \"lacks specificity\". Do not say the grounds "
    "support it. If it is a QUESTION, do not turn it into a statement and do not begin \"The claim\"; say what in a "
    "ground makes one tempting answer doubtful. Use ONLY the grounds given; never add facts. A ground that merely "
    "leaves part of it open, or points a different way on one side of it, counts, so one ground is enough even when "
    "the others agree. Leave the objection an empty string, with no cites, only when you have read every ground and "
    "none has a counterexample, a limit or a tension in it. Output ONLY JSON of this shape, with your own words in "
    "place of the angle-bracket parts, writing cites first so you have chosen the ground before you write about it: "
    "{\"cites\": [<the one ground number>], \"objection\": <one sentence, or \"\">, \"scope\": <what it holds only within, or \"\">}"
)
_WHY_SYS = _WHY_SYS_V2 if PROMPT_V2 else _WHY_SYS_V1
_CONS_SYS = (_CONS_SYS_V3 if CONS_PROMPT_V3 else _CONS_SYS_V2) if PROMPT_V2 else _CONS_SYS_V1
_AGAINST_SYS = _AGAINST_SYS_V2 if PROMPT_V2 else _AGAINST_SYS_V1
_JUDGE_A_SYS = (
    "You judge a thinker's own support for his own claim. You see the CLAIM, the GROUNDS he found in his memory, "
    "and his WHY. Answer true only if (1) the grounds genuinely bear on the claim — a lived instance, a fact, a "
    "counterexample, something read about the matter itself, not a merely thematic or word-sharing match — AND "
    "(2) the WHY follows from those grounds rather than restating the claim in other words. When uncertain, "
    "answer false. Answer ONLY JSON: {\"supported\": true} or {\"supported\": false}."
)
_JUDGE_C_SYS = (
    "You judge whether a stated OBJECTION genuinely cuts against a CLAIM, given the GROUNDS it cites. Answer true "
    "only if the objection, read against those grounds, would make a careful thinker narrow or withdraw the claim; "
    "a vague worry, a restatement, or an objection the grounds do not support is false. When uncertain, answer "
    "false. Answer ONLY JSON: {\"cuts\": true} or {\"cuts\": false}."
)
_JUDGE_B_SYS = (
    "You judge whether stated CONSEQUENCES really follow from a CLAIM. A real consequence would have to be true if "
    "the claim is true and would likely be false if the claim is false. A restatement, a vague theme, or something "
    "true regardless of the claim is NOT a consequence. Answer true only if at least one listed consequence is a "
    "real one. When uncertain, answer false. Answer ONLY JSON: {\"follows\": true} or {\"follows\": false}."
)


# ── small helpers ─────────────────────────────────────────────────────────────────────────────────────────────
def enabled() -> bool:
    """True unless FOLLOW_LINE == "off". "shadow" = everything runs and logs, nothing delivered; "live" (Phase 1,
    J-2460, D-0494 (3)) = the return is delivered to the next idle thought and his `settled` word closes it."""
    return FOLLOW_LINE != "off"


def schema_fragment(delivered: bool = False) -> str:
    """The `ask` field for the idle-thought JSON schema line, plus `settled` ONLY on a tick that delivered a return;
    "" when off (exact pre-existing schema)."""
    if not enabled():
        return ""
    return ', "ask": {"q": "", "slot": ""}' + (', "settled": ""' if delivered else "")


def rule_fragment(delivered: bool = False) -> str:
    """The `ask` rule for the idle-thought system prompt, in the register of the `intention` rule; "" when off.
    It describes a channel for HIS voice; it does not ask him to ask (the world never leads). On a tick that
    delivered one of his own returns, the `settled` rule rides along -- a question about his own question."""
    if not enabled():
        return ""
    kinds = (f" slot is the kind of piece you are missing: {ASK_SLOT_KINDS}." if ASK_SLOT_KINDS
             else " slot: leave as \"\".")
    out = ("ask: {\"q\": \"\", \"slot\": \"\"} when this thought asks nothing. When this thought "
           "genuinely asks something you want an answer to and would use one, q is the question in your own "
           "words." + kinds + " ")
    if delivered:
        out += ("settled: something you asked or held earlier came back to you this time. \"yes\" if what came back "
                "settles it for you, \"partly\" if only a part of it, \"no\" if it does not. Your own judgement; "
                "nothing is lost either way. ")
    return out


def parse_settled(data: dict) -> str:
    """"yes" | "partly" | "no" | "" from a parsed idle-thought JSON on a tick that delivered. Never raises."""
    try:
        if not enabled() or not isinstance(data, dict):
            return ""
        s = str(data.get("settled", "") or "").strip().lower()
        return s if s in ("yes", "partly", "no") else ""
    except Exception:
        return ""


def parse_ask(data: dict) -> tuple[str, str]:
    """(q, slot) from a parsed idle-thought JSON; ("", "") when off, absent, malformed, or empty. Never raises."""
    try:
        if not enabled() or not isinstance(data, dict):
            return "", ""
        a = data.get("ask")
        if not isinstance(a, dict):
            return "", ""
        q = str(a.get("q", "") or "").strip()
        slot = str(a.get("slot", "") or "").strip().lower()
        if len(q) < 8:
            return "", ""
        if slot not in SLOTS:
            slot = ""
        return q[:220], slot
    except Exception:
        return "", ""


def _now() -> float:
    return time.time()


def _append(row: dict) -> None:
    """One shadow-log row. Fenced (D-0179): resolved OUTSIDE the fail-open try so the refusal is never swallowed."""
    path = profile.guard_path(SHADOW_LOG)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _ride(stop: str, line: str, dose: str, q_id: str, kind: str, source: str, slot: str,
          stop_name: str, outcome: str, n_chars: int = 0, **extra) -> None:
    """The dosed_coupling §5 ride row: {stop, line, dose, value}. Never raises past the fence."""
    try:
        _append({"ts": round(_now(), 3), "kind": "ride", "stop": stop, "line": line, "dose": dose,
                 "value": {"q_id": q_id, "kind": kind, "source": source, "slot": slot, "stop_name": stop_name,
                           "outcome": outcome, "n_chars": int(n_chars), **extra}})
    except profile.NonLiveWriteError:
        raise
    except Exception:
        pass


def _publish(q_id: str, kind: str, source: str, slot: str, state: str, status: str = "undetermined") -> None:
    """The coordinate only (dosed_coupling rule 1). Never prose. Never raises."""
    try:
        from core import coupling_rides as _cr
        _cr.publish("follow", "follow_line", {"q_id": str(q_id)[:10], "kind": kind, "source": source,
                                              "slot": slot or "", "state": state, "status": status})
    except Exception:
        pass


def _entry(q_id: str) -> dict | None:
    try:
        from core import frontier as _fr
        return _fr.get(q_id)
    except Exception:
        return None


def _set_line(q_id: str, **fields) -> None:
    try:
        from core import frontier as _fr
        _fr.set_line(q_id, **fields)
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[follow_line] set_line failed (non-fatal): %s", exc)


# ── boarding ──────────────────────────────────────────────────────────────────────────────────────────────────
def reboard_ok(key: str, now: float | None = None) -> bool:
    """May consequences of `key` (an about_key) re-board now? Once per REBOARD_SAME_KEY_S per key."""
    return (now or _now()) - _recent_keys.get(key or "", 0.0) >= REBOARD_SAME_KEY_S


def _note_reboard(key: str, now: float | None = None) -> None:
    _recent_keys[key or ""] = now or _now()
    if len(_recent_keys) > 500:
        for k in sorted(_recent_keys, key=_recent_keys.get)[:250]:
            _recent_keys.pop(k, None)


def _cons_quota_check(now: float | None = None) -> tuple[bool, int]:
    """(would_refuse, used_in_window) for one more consequence boarding. Pure of side effects except pruning."""
    now = now or _now()
    while _cons_log and now - _cons_log[0] > CONS_QUOTA_WINDOW_S:
        _cons_log.popleft()
    return len(_cons_log) >= CONSEQUENCE_DAILY_QUOTA, len(_cons_log)


def _log_cons_quota(row: dict) -> None:
    """One would-refuse / refused row. Fenced like _append (path resolved outside the fail-open try)."""
    path = profile.guard_path(CONS_QUOTA_LOG)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def board(q: str, source: str, *, kind: str = "question", slot: str = "", about: str = "",
          asked_by: dict | None = None, allow_self: bool = True, depth: int = 0, guard: bool = True) -> dict | None:
    """A question or claim of HIS boards the line: it becomes (or refreshes) a frontier entry with
    line.state="waiting". Returns the entry or None. Does NOT fire — see fire()/drain_tick(). Every source the
    plan names comes through here: "asked" (the monologue's ask field), "claim" (a new study note's first
    sentence), "pursuit" (a confirmed advance's rewritten open question), "consequence" (stop 3's re-boarding);
    the pre-existing births (curiosity/intention/dream/prism/study) are stamped waiting inside
    frontier.note_question_ex itself and never pass through here. NonLiveWriteError propagates."""
    if not enabled():
        return None
    try:
        from core import frontier as _fr
        q = (q or "").strip()
        if len(q) < 8:
            return None
        key = (asked_by or {}).get("about_key") or ""
        if source == "consequence":
            if depth > MAX_DEPTH:
                _ride("frontier", f"follow_line:board:{source}", "cup", "", kind, source, slot, "board", "skip-depth")
                return None
            if guard and not reboard_ok(key):
                _ride("frontier", f"follow_line:board:{source}", "cup", "", kind, source, slot, "board", "skip-reboard-24h")
                return None
            if CONSEQUENCE_QUOTA_MODE != "off":
                over, used = _cons_quota_check()
                if over:
                    _log_cons_quota({"ts": round(_now(), 3), "mode": CONSEQUENCE_QUOTA_MODE, "quota": CONSEQUENCE_DAILY_QUOTA,
                                     "used_24h": used, "depth": depth, "about_key": key, "q": q[:160],
                                     "outcome": "refused" if CONSEQUENCE_QUOTA_MODE == "enforce" else "would_refuse"})
                    if CONSEQUENCE_QUOTA_MODE == "enforce":
                        return None
        ent = _fr.note_question_ex(q, source, kind=kind, slot=slot, about=about, asked_by=asked_by or {},
                                   allow_self=allow_self, depth=depth)
        if not ent:
            _ride("frontier", f"follow_line:board:{source}", "cup", "", kind, source, slot, "board", "rejected")
            return None
        if source == "consequence":
            if CONSEQUENCE_QUOTA_MODE != "off":
                _cons_log.append(_now())
            if guard:
                _note_reboard(key or ent.get("id", ""))
        _ride("frontier", f"follow_line:board:{source}", "cup", ent.get("id", ""), kind, source, slot, "board",
              "boarded", len(q), depth=depth)
        _publish(ent.get("id", ""), kind, source, slot, "boarded")
        return ent
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[follow_line] board failed (non-fatal): %s", exc)
        return None


def _cap_ok(now: float) -> bool:
    while _board_log and now - _board_log[0] > BOARD_WINDOW_S:
        _board_log.popleft()
    if BOARD_CAP_PER_HOUR is None:                                # uncapped: the log is still kept (status boarded_last_hour)
        return True
    return len(_board_log) < BOARD_CAP_PER_HOUR


def fire(q_id: str) -> bool:
    """Send a boarded entry down the line NOW if the rolling-hour cap allows and nothing is in flight; otherwise
    it stays waiting for drain_tick(). Needs a running event loop (the thought tick, the substrate loop,
    judge_pending's sweep); without one the entry simply waits. Never raises."""
    global _in_flight
    if not enabled() or not q_id:
        return False
    try:
        ent = _entry(q_id) or {}
        kind, source, slot = ent.get("kind", "question"), ent.get("source", ""), ent.get("slot", "")
        now = _now()
        if _in_flight:
            _ride("follow", "follow_line:fire", "cup", q_id, kind, source, slot, "fire", "wait-in-flight")
            return False
        if not _cap_ok(now):
            _ride("follow", "follow_line:fire", "cup", q_id, kind, source, slot, "fire", "wait-cap")
            return False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            _ride("follow", "follow_line:fire", "cup", q_id, kind, source, slot, "fire", "wait-no-loop")
            return False
        _board_log.append(now)
        _in_flight = q_id
        _set_line(q_id, state="fired", fired=now)               # leaves "waiting" NOW, so a run that dies before
        task = loop.create_task(run(q_id))                     # its first stop is never re-drained forever
        _TASKS.add(task)                                         # strong ref (reentry_p2._spawn pattern)
        task.add_done_callback(lambda t, _q=q_id: _done(_q, t))  # the tag rides the callback
        _ride("follow", "follow_line:fire", "cup", q_id, kind, source, slot, "fire", "fired")
        return True
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[follow_line] fire failed (non-fatal): %s", exc)
        return False


def _done(q_id: str, task) -> None:
    global _in_flight
    _TASKS.discard(task)
    if _in_flight == q_id:
        _in_flight = None
    try:
        exc = task.exception() if not task.cancelled() else None
    except Exception:
        exc = None
    if exc is not None:
        logger.debug("[follow_line] run(%s) raised (non-fatal): %s", q_id, exc)


def drain_tick() -> str | None:
    """Called every ~60 s from the substrate loop: if nothing is in flight, fire the highest-priority waiting entry
    (PRIORITY order, newest first within a source -- D-0611). Returns the fired id or None. Never raises."""
    if not enabled():
        return None
    rearm_deferred()
    if _in_flight:
        return None
    try:
        from core import frontier as _fr
        for ent in _fr.waiting_for_line(PRIORITY):
            if fire(ent.get("id", "")):
                return ent.get("id")
            return None                                           # cap / no loop: everything else waits too
        return None
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[follow_line] drain_tick failed (non-fatal): %s", exc)
        return None


# ── J-2570 (F-3301): defer an unjudgeable run instead of judging/delivering an empty cargo ─────────────────────
def grounds_unclear(outcome: str, n_grounds: int, secs: float | None) -> bool:
    """Stop 1 could not get a clear look: evidence_recall said unclear (its judges down), the stop raised, or it
    came back empty only after a wait past DEFER_EMPTY_SLOW_S (an empty reached through a dead lane is not a real
    empty -- the 11:52/11:57 rows of F-3301, 215 s). A fast empty is a real answer: his past holds little."""
    if outcome in ("unclear", "failed"):
        return True
    return outcome == "empty" and not n_grounds and secs is not None and float(secs) > DEFER_EMPTY_SLOW_S


def gen_dead(grounds: list, why: dict) -> bool:
    """Stop 2 died: with grounds present, the why stop raised or _gen_json came back empty (text '' and not
    skipped). Without grounds the why is skipped by design and that is not a failure."""
    if not grounds:
        return False
    return bool(why.get("failed")) or (not (why.get("text") or "").strip() and not why.get("skipped"))


def is_vacuous(row: dict) -> bool:
    """A would_return row whose return came from unclear grounds (pre-J-2570 rows; post-J-2570 these runs are
    deferred and never write would_return). Readers of the shadow log (status(), F-3293-style counts) skip them:
    the verdict he gave on an empty cargo is not evidence about the claim. Uses stop 1's own secs when present,
    the whole-run secs for older rows."""
    if (row or {}).get("kind") != "would_return":
        return False
    sg = (row.get("stops") or {}).get("grounds") or {}
    oc = (row.get("cargo") or {}).get("grounds_outcome") or sg.get("outcome") or ""
    n = len((row.get("cargo") or {}).get("grounds") or []) or int(sg.get("n", 0) or 0)
    return grounds_unclear(oc, n, sg.get("secs", row.get("secs")))


def _defer(q_id: str, ent: dict, reason: str, stops: dict, cargo: dict, t0: float) -> dict:
    """Log one kind="deferred" row (no would_return, no judge, no pending) and park the entry: state "deferred" with
    defer_until = now + DEFER_BACKOFF_S (rearm_deferred() puts it back to "waiting"), or "unjudged" once it has
    been deferred DEFER_MAX_TRIES times. NonLiveWriteError propagates."""
    kind, source, slot = ent.get("kind", "question"), ent.get("source", ""), ent.get("slot", "")
    tries = int((ent.get("line") or {}).get("defer_tries", 0) or 0) + 1
    final = tries >= DEFER_MAX_TRIES
    state = "unjudged" if final else "deferred"
    now = _now()
    row = {"ts": round(now, 3), "kind": "deferred", "q_id": q_id, "q": (ent.get("q") or "")[:220], "kind_cargo": kind,
           "source": source, "slot": slot, "depth": int((ent.get("line") or {}).get("depth", 0) or 0),
           "reason": reason, "tries": tries, "final": final, "grounds_outcome": cargo.get("grounds_outcome"),
           "n_grounds": len(cargo.get("grounds") or []), "stops": stops, "secs": round(now - t0, 1)}
    _append(row)
    _set_line(q_id, state=state, defer_reason=reason, defer_tries=tries, finished=now,
              defer_until=(None if final else now + DEFER_BACKOFF_S))
    _publish(q_id, kind, source, slot, state)
    _ride("follow", "follow_line:defer", "cup", q_id, kind, source, slot, "defer", reason, 0, tries=tries, final=final)
    logger.info("[follow_line] %s/%s '%s' -> %s (%s, try %d/%d)", source, kind, (ent.get("q") or "")[:50], state,
                reason, tries, DEFER_MAX_TRIES)
    return row


def rearm_deferred(now: float | None = None) -> int:
    """Put deferred entries whose backoff has passed back on the line (state "waiting"). Read-only scan of the
    cached frontier; one set_line per re-armed entry. Returns how many. Never raises past the fence."""
    try:
        from core import frontier as _fr
        now = now or _now()
        due = [q.get("id") for q in _fr._load_ro().get("questions", [])
               if q.get("status") == "open" and (q.get("line") or {}).get("state") == "deferred"
               and float((q.get("line") or {}).get("defer_until") or 0.0) <= now]
        for qid in due:
            _set_line(qid, state="waiting", rearmed=now)
        return len(due)
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[follow_line] rearm_deferred failed (non-fatal): %s", exc)
        return 0


# ── the stops (each separately replaceable by a test) ─────────────────────────────────────────────────────────
async def _stop_grounds(q: str, train_id: str | None) -> dict:
    """Stop 1: what have I lived / read / seen that bears on this? evidence_recall's own world-contact filter and
    decoupled per-episode judge; outcome found | empty | unclear (never 'empty' when the judges were down)."""
    from core import evidence_recall as _ev
    res = await _ev.gather(q, train_id=train_id, source="follow_line",     # J-2604: not Route 2 (F-3327)
                           **({"dedupe": True} if DEDUPE_GROUNDS else {}))   # J-2972: identical copies out of the short-list
    grounds = []
    for e in (res.get("episodes") or []):
        grounds.append({"fragment_id": e.get("fragment_id"), "origin": e.get("origin", ""),
                        "age": _ev._age_text(float(e.get("timestamp") or 0.0)) if e.get("timestamp") else "",
                        "strength": e.get("strength", ""), "text": _grounds_cut(e.get("content") or "")})
    out = {"grounds": grounds, "grounds_outcome": res.get("outcome", "unclear")}
    if DEDUPE_GROUNDS:
        grounds, dropped = dedupe_grounds(grounds)
        out["grounds"] = grounds
        out["grounds_deduped"] = int(res.get("deduped", 0) or 0) + dropped
    return out


def _ground_key(g: dict) -> str:
    return " ".join((g.get("text") or "").lower().split())[:GROUND_DEDUPE_CHARS]


def dedupe_grounds(grounds: list) -> tuple[list, int]:
    """J-2972 (F-3662): the safety net behind evidence_recall's own dedupe. Drops a ground whose fragment id was already
    seen or whose text[:GROUND_DEDUPE_CHARS] (whitespace-collapsed, lower-cased) equals an earlier one's; the first
    (strongest, bears before may_bear) is kept, order is kept. Returns (kept, number dropped). Two copies of one passage
    otherwise count as two lines of support in the WHY prompt, the judges and the return (11 of 101 grounded runs)."""
    kept, seen_ids, seen_txt = [], set(), set()
    for g in grounds or []:
        fid, key = g.get("fragment_id"), _ground_key(g)
        if (fid and fid in seen_ids) or (key and key in seen_txt):
            continue
        if fid:
            seen_ids.add(fid)
        if key:
            seen_txt.add(key)
        kept.append(g)
    return kept, len(grounds or []) - len(kept)


def _input_label(q: str) -> str:
    """J-2912 (F-3598): "QUESTION" when the boarded text is a question, else "CLAIM". 167 of 175 delivered entries are
    question-form, and a prompt that calls them a CLAIM makes the model assert them and object to the assertion. Decided
    from the text (a trailing "?") so the stop signatures the tests stub stay as they are. PROMPT_V2 False = always CLAIM."""
    if not PROMPT_V2:
        return "CLAIM"
    return "QUESTION" if (q or "").rstrip().rstrip("\"')]}").endswith("?") else "CLAIM"


async def _gen_json(system: str, user: str) -> dict:
    from core.model_client import call_node_json
    d = await call_node_json(LINE_URLS, system, user, max_tokens=GEN_MAX_TOKENS, temperature=0.3)
    return d if isinstance(d, dict) else {}


async def _stop_why(q: str, grounds: list) -> dict:
    """Stop 2: why would those grounds make it true (or not)? One command-r7b call (:11441), grounds only, cites by index."""
    if not grounds:
        return {"text": "", "cites": [], "supports": "no", "skipped": "no-grounds"}
    user = (f"{_input_label(q)}: {q}\n\nGROUNDS:\n" +
            "\n".join(f"[{i}] ({g.get('origin','')}, {g.get('age','')}) {g.get('text','')}"
                      for i, g in enumerate(grounds, 1)))
    d = await _gen_json(_WHY_SYS, user)
    text = str(d.get("why", "") or "").strip()
    text = _clip_boundary(text, 400) if PROMPT_V2 else text[:400]     # J-2912 (F-3596): 8% were cut mid-phrase at 400
    cites = [int(c) for c in (d.get("cites") or []) if isinstance(c, (int, float)) and 1 <= int(c) <= len(grounds)]
    supports = str(d.get("supports", "") or "").strip().lower()
    if supports not in ("yes", "partly", "no"):
        supports = "no" if not text else "partly"
    out = {"text": text, "cites": sorted(set(cites)), "supports": supports}
    if text and _SELF_SEALING.search(text):
        out["self_sealing"] = True                               # recorded, not rewritten: the judge sees it
    return out


async def _stop_consequences(q: str, grounds: list, why: dict) -> list:
    """Stop 3: if this is so, what else should be true? The deduction step. One command-r7b call (:11441)."""
    user = f"{_input_label(q)}: {q}\n"
    if grounds:
        user += "GROUNDS:\n" + "\n".join(f"[{i}] {g.get('text','')}" for i, g in enumerate(grounds, 1)) + "\n"
    if why.get("text"):
        user += f"WHY: {why['text']}\n"
    d = await _gen_json(_CONS_SYS, user)
    out = []
    for c in (d.get("consequences") or [])[:3]:
        if not isinstance(c, dict):
            continue
        text = str(c.get("text", "") or "").strip()[:220]
        if len(text) < 12:
            continue
        raw = c.get("question_word") or c.get("slot") or ""    # J-4170: V3 keys first, V2 keys as the fallback
        slot = _norm_slot(raw)
        chk = _norm_checkable(c.get("check_in") or c.get("checkable"))
        leak = "" if slot else _norm_checkable(raw)            # J-4170 (F-5015): the checkable value put in the slot field
        if leak and not chk:
            chk = leak                                          # the model's only placement tag; better than the default
        if not slot and leak:
            alt = _norm_slot(c.get("check_in") or c.get("checkable"))
            if alt:
                slot = alt                                      # the two tags swapped: slot word sat in the checkable field
        ent = {"text": text, "slot": slot, "checkable": chk or "memory"}
        if not slot and leak:
            ent["slot_leak"] = "checkable"      # J-4170: counted, not kept as slot_raw noise (73% of slot_raw under V2)
        elif not slot and raw:
            ent["slot_raw"] = str(raw)[:60]      # J-3928 (F-4562): ~60% blank since V2; keep what the model returned
        out.append(ent)
    return out


def _norm_checkable(raw) -> str:
    """J-4170: the value naming exactly ONE of memory/world/self ("World.", "<self>"), else "". Never raises."""
    import re as _re
    try:
        if isinstance(raw, (list, tuple)):
            raw = raw[0] if len(raw) == 1 else ""
        words = set(_re.findall(r"[a-z]+", str(raw or "").lower())) & {"memory", "world", "self"}
        return next(iter(words)) if len(words) == 1 else ""
    except Exception:
        return ""


def _norm_slot(raw) -> str:
    """J-3928: tolerant slot read. A list takes its first usable element; surrounding quotes/punctuation are stripped;
    a value naming exactly ONE slot word ("Why.", "<why>", "why (the reason)") is that slot. Two or more distinct slot
    words (the placeholder echoed back, "who/what") is ambiguous and stays "". Never raises."""
    import re as _re
    try:
        if isinstance(raw, (list, tuple)):
            for r in raw:
                v = _norm_slot(r)
                if v:
                    return v
            return ""
        words = set(_re.findall(r"[a-z]+", str(raw or "").lower())) & set(SLOTS)
        return next(iter(words)) if len(words) == 1 else ""
    except Exception:
        return ""


def drop_intentions(cons: list) -> tuple[list, int]:
    """J-2910: (kept, n_dropped). A consequence that begins "I will / I can / I would / I should ..." names a deed, not a
    state of the world; it is removed. Never raises; everything is kept when DROP_INTENTION_CONSEQUENCES is False."""
    if not DROP_INTENTION_CONSEQUENCES:
        return list(cons or []), 0
    kept = [c for c in (cons or []) if not _INTENTION.match(str((c or {}).get("text", "") or ""))]
    return kept, len(cons or []) - len(kept)


def _own_test_for(q: str) -> dict:
    """D-0632 (J-3244): the stored intervention_test of the hypothesis this claim IS, else {}. BLOCKING (reads the
    substrate file) -- run under off_loop. Deterministic, read-only; the stop never raises past the caller."""
    from core import object_hypothesis as _oh
    from core import world_substrate as _ws
    r = _oh.match_hypothesis(q, _ws.inferences_with_test())
    if not r:
        return {}
    text = _oh.describe_test(r.get("intervention_test") or [])
    if not text:
        return {}
    return {"text": text, "object_id": r.get("object_id", ""), "inference_id": r.get("inference_id", ""),
            "hypothesis": (r.get("hypothesis") or "")[:200], "candidates": list(r.get("intervention_test") or [])[:3]}


async def _stop_own_test(q: str) -> dict:
    """Stop 3b: his own hypothesis's own test, from memory (D-0632). {} when OWN_TEST_RETURN is off, the claim is
    not one of his stored hypotheses, or that hypothesis carries no test."""
    if not OWN_TEST_RETURN:
        return {}
    from core import idle_offloop as _off
    return await _off.off_loop(_own_test_for, q) or {}


def _seen_candidates(q: str, k: int = CONN_K) -> list:
    """What he has SEEN: a similarity read restricted to lived / observation origins (no judge — this stop is
    connections, not evidence). BLOCKING — run under off_loop."""
    import sqlite3
    import numpy as np
    from core.memory.store import _embed, _blob_to_vec, DB_PATH
    qv = _embed(q)
    if qv is None:
        return []
    ph = ",".join("?" * len(SEEN_ORIGINS))
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"SELECT fragment_id, content, origin, timestamp, embedding FROM memory_fragments "
            f"WHERE origin IN ({ph}) AND embedding IS NOT NULL", SEEN_ORIGINS).fetchall()
    if not rows:
        return []
    mat = np.stack([_blob_to_vec(r["embedding"]) for r in rows])
    qn = qv / (np.linalg.norm(qv) or 1.0)
    mn = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9)
    sims = mn @ qn
    out = []
    for i in np.argsort(-sims):
        if len(out) >= k or sims[i] < SEEN_MIN_SIM:
            break
        if _is_conversation_record(rows[i]["content"] or "") or not _snippet(rows[i]["content"] or "", GROUNDS_TEXT):
            continue                                   # J-2911: a conversation record / pure label is not a connection
        out.append({"fragment_id": rows[i]["fragment_id"], "origin": rows[i]["origin"],
                    "text": _snippet(rows[i]["content"] or "", GROUNDS_TEXT), "sim": round(float(sims[i]), 3)})
    return out


def _can_do(q: str, k: int = CONN_K) -> list:
    """What he CAN DO that this touches: persisted+ procedures (his own hands, his own record), matched by token
    overlap with the claim. Cheap, no LLM, no embedding."""
    from core import procedures as _pr
    from core.frontier import _toks
    qt = _toks(q)
    if not qt:
        return []
    d = _pr._load()
    rows = [p for p in (d.get("procedures") or {}).values()
            if _pr._ORDER.index(p.get("rung", "occurred")) >= 1]
    scored = []
    for p in rows:
        st = f"{p.get('key','').split(':',1)[-1].replace('_',' ')} {p.get('statement','')} {p.get('why_I_hold_it','')}"
        ov = len(qt & _toks(st))
        if ov:
            scored.append((ov, p))
    scored.sort(key=lambda t: (-t[0], -float(t[1].get("last_ts", 0))))
    return [{"key": p.get("key", ""), "statement": (p.get("statement") or "")[:160], "rung": p.get("rung", "")}
            for _, p in scored[:k]]


async def _stop_connections(q: str) -> dict:
    """Stop 4: what else I know / can do / have seen does this touch? Six-slot memory ask (loop="follow"),
    procedures, and a lived-origin similarity read. Each ≤ CONN_K, with fragment ids."""
    from core import idle_offloop as _off
    from core import memory_service as _ms
    know = seen = []
    can = []
    try:
        pool = await _off.off_loop(_ms.ask, "follow", what=q, why=q, how=q, k=CONN_K * 2, k_per_slot=CONN_K)
        know = [{"fragment_id": e.get("fragment_id"), "origin": e.get("origin", ""),
                 "text": _snippet(e.get("content") or "", GROUNDS_TEXT), "slots": list(e.get("slots_answered") or [])}
                for e in (pool or []) if not _is_conversation_record(e.get("content") or "")][:CONN_K]   # J-2911
        know = [k_ for k_ in know if k_["text"]]
    except Exception as exc:
        logger.debug("[follow_line] connections/know failed (non-fatal): %s", exc)
    try:
        can = _can_do(q)
    except Exception as exc:
        logger.debug("[follow_line] connections/can_do failed (non-fatal): %s", exc)
    try:
        seen = await _off.off_loop(_seen_candidates, q)
    except Exception as exc:
        logger.debug("[follow_line] connections/seen failed (non-fatal): %s", exc)
    return {"know": know, "can_do": can, "seen": seen}


async def _stop_against(q: str, grounds: list) -> dict:
    """Stop 5 (the line's OWN version until train_split_merge's disprove branch resumes -- founder, 2026-10-27):
    what in the grounds cuts against the claim? One command-r7b call (:11441), grounds only. The STATUS is not set here:
    the decoupled judge's question (c) sets it (the line never grades its own objection)."""
    if not grounds:
        return {"text": "", "cites": [], "scope": "", "skipped": "no-grounds"}
    user = (f"{_input_label(q)}: {q}\n\nGROUNDS:\n" +
            "\n".join(f"[{i}] ({g.get('origin','')}, {g.get('age','')}) {g.get('text','')}"
                      for i, g in enumerate(grounds, 1)))
    d = await _gen_json(_AGAINST_SYS, user)
    text = str(d.get("objection", "") or "").strip()
    text = _clip_boundary(text, 400) if PROMPT_V2 else text[:400]
    if PROMPT_V2 and text.rstrip(". ").lower() in ("none", "no objection", "no real objection", "n/a", "nothing"):
        text = ""                                                     # J-2912: a spelled-out null is the null path
    cites = [int(c) for c in (d.get("cites") or []) if isinstance(c, (int, float)) and 1 <= int(c) <= len(grounds)]
    scope = str(d.get("scope", "") or "").strip()[:200]
    if PROMPT_V2 and not text:
        cites, scope = [], ""                                         # J-2912: an empty objection carries nothing
    elif PROMPT_V2 and not cites:                                     # J-2912: it named its ground in the sentence ("in [2]") but left the list empty
        cites = [int(n) for n in re.findall(r"\[(\d{1,2})\]", text) if 1 <= int(n) <= len(grounds)]
    return {"text": text, "cites": sorted(set(cites)), "scope": scope}


def cargo_status(judged: dict) -> str:
    """held | held_within_scope | objected | undetermined, from the decoupled verdicts only (train_split_merge's
    merge-status vocabulary, D-0181's middle status included). Never from the line's own text."""
    a, c = judged.get("a"), judged.get("c")
    if c == "yes":
        return "objected"
    if c == "partly" or (a == "partly" and c in ("no", "skipped")):
        return "held_within_scope"
    if a == "yes" and c == "no":
        return "held"
    if a == "yes" and c == "skipped":
        return "held_within_scope"          # no objection could even be sought (no grounds for one)
    return "undetermined"


_cuts_count = {"yes": 0, "split_not_cut": 0}   # this process; D-0596 counter, read by status() and the log line below


def _note_cuts(c: str, c_how: str, raw_verdict) -> None:
    """D-0596 counter: cuts judged yes vs a tiebreak-decided yes that no longer counts as a cut. Fail-open."""
    try:
        if c == "yes":
            _cuts_count["yes"] += 1
        elif c_how == "tiebreak" and raw_verdict is True:
            _cuts_count["split_not_cut"] += 1
        else:
            return
        logger.info("[follow_line] cuts judged: yes=%d split-not-cut=%d (D-0596)",
                    _cuts_count["yes"], _cuts_count["split_not_cut"])
    except Exception:
        pass


async def _judge(q: str, cargo: dict, q_id: str = "") -> dict:
    """The decoupled panel, on the claim and the cargo only — never the asking thought. Three questions:
    (a) grounds bear AND the why follows rather than restates; (b) at least one consequence is a real one;
    (c) the objection genuinely cuts against the claim given its grounds (Phase 1, stop 5).
    Each yes | partly | no (partly = the families split with no tiebreak); 'unclear' when the judges were down."""
    from core import judge_panel
    def _map(d: dict, key: str = "") -> str:
        if d.get("how") == "unavailable":
            return "unclear"
        if key == "cuts" and d.get("how") == "tiebreak" and d.get("verdict") is True:
            # D-0596 (J-3206, F-3658): a panel SPLIT is not a cut. For the 'cuts' judge only, a yes that rests on the
            # tiebreak vote (mixtral no, falcon3 yes, granite decides) maps to 'no'; the raw how stays in c_how. The
            # shared tiebreak and the other keys are untouched (J-2953 owns that question).
            return "no"
        if d.get("verdict") is True:
            return "yes"
        if d.get("how") == "split_no_tiebreak":
            return "partly"
        return "no"
    out = {"a": "no", "b": "no", "c": "skipped", "a_how": "", "b_how": "", "c_how": "skipped"}
    grounds, why, cons = cargo.get("grounds") or [], cargo.get("why") or {}, cargo.get("consequences") or []
    against = cargo.get("against") or {}
    if grounds and against.get("text"):
        uc = (f"CLAIM: {q}\n\nGROUNDS:\n" +
              "\n".join(f"[{i}] ({g.get('origin','')}) {g.get('text','')}" for i, g in enumerate(grounds, 1)) +
              f"\n\nOBJECTION: {against.get('text','')}" + (f"\nSCOPE: {against['scope']}" if against.get("scope") else ""))
        dc = await judge_panel.rule_detail(_JUDGE_C_SYS, uc, "cuts", context=f"follow_line:c:{q_id[:8]}")
        out["c"], out["c_how"] = _map(dc, "cuts"), str(dc.get("how", ""))
        _note_cuts(out["c"], out["c_how"], dc.get("verdict"))
        if out["c_how"] == "tiebreak" and dc.get("verdict") is True and out["c"] == "no":
            out["c_split_not_cut"] = True          # lets a replay count the dropped lines straight from the log row
    if grounds and why.get("text"):
        ua = (f"CLAIM: {q}\n\nGROUNDS:\n" +
              "\n".join(f"[{i}] ({g.get('origin','')}) {g.get('text','')}" for i, g in enumerate(grounds, 1)) +
              f"\n\nWHY: {why.get('text','')}")
        da = await judge_panel.rule_detail(_JUDGE_A_SYS, ua, "supported", context=f"follow_line:a:{q_id[:8]}")
        out["a"], out["a_how"] = _map(da), str(da.get("how", ""))
    else:
        out["a"], out["a_how"] = "no", "skipped"
    cons = cons[:CONS_USED]                      # J-2969 (F-3661): judge the set that is shown and re-boarded, not a third that never is
    if cons:
        ub = (f"CLAIM: {q}\n\nCONSEQUENCES:\n" +
              "\n".join(f"[{i}] {c.get('text','')}" for i, c in enumerate(cons, 1)))
        db = await judge_panel.rule_detail(_JUDGE_B_SYS, ub, "follows", context=f"follow_line:b:{q_id[:8]}")
        out["b"], out["b_how"] = _map(db), str(db.get("how", ""))
    else:
        out["b"], out["b_how"] = "no", "skipped"
    return out


# ── the line itself ───────────────────────────────────────────────────────────────────────────────────────────
def _ago_phrase(age_s: float) -> str:
    """J-2907 (F-3564, P-0044): how long ago, in his register, from an age in seconds. A return is delivered at the next idle
    thought, measured median 4.9 h after he asked, so 'just now' is only true for the first minutes. Facts only -- no number
    finer than the hours, nothing that says what to do about it."""
    a = max(0.0, float(age_s or 0.0))
    if a < ASKED_JUST_NOW_S:
        return "just now"
    if a < 3600:
        return "a while ago"
    if a < 86400:
        return "some hours ago"
    d = int(a // 86400)
    return "yesterday" if d < 2 else f"{d} days ago"


def _asked_ts(ent: dict) -> float:
    """When he asked: asked_by.ts (stamped at the ask), else the entry's born. 0.0 = unknown."""
    by = ent.get("asked_by") or {}
    for v in (by.get("ts"), ent.get("born")):
        try:
            if v and float(v) > 0:
                return float(v)
        except (TypeError, ValueError):
            continue
    return 0.0


def _asked_ago(ent: dict, now: float | None = None) -> str:
    """How long ago he asked (an `_ago_phrase`), or 'earlier' when the entry carries no usable timestamp."""
    ts = _asked_ts(ent)
    return _ago_phrase((now if now is not None else _now()) - ts) if ts else "earlier"


def _origin_phrase(ent: dict, now: float | None = None) -> str:
    """Where the question came from, in his own terms, so he knows what it was about however long it took.
    J-2907: for source=asked the phrase carries the AGE at `now` (delivery time, not render time); an entry with no usable
    timestamp says 'asked earlier' rather than claim 'just now'. The other phrases make no claim about time."""
    src, by = ent.get("source", ""), ent.get("asked_by") or {}
    book = (by.get("book_title") or "")[:60]
    about = (ent.get("about") or "")[:60]
    if src == "asked":
        ago = _asked_ago(ent, now)
        return f"asked {ago}" if not about else f"asked {ago}, about {about}"
    if src == "claim":
        return f"held after reading '{book}'" if book else "held after reading"
    if src == "study":
        return f"wondered while reading '{book}'" if book else "wondered while reading"
    if src == "dream":
        return "wondered in a dream"
    if src == "pursuit":
        return f"left open in your pursuit of {about}" if about else "left open in a pursuit of yours"
    if src == "consequence":
        return "found would have to follow from something you hold"
    if src == "intention":
        return "meant to find out"
    return "wondered earlier" if not about else f"wondered earlier, about {about}"


_SENTENCE_END = re.compile(r"[.!?][\"')\]]?(?=\s|$)")


def _clip_boundary(text: str, n: int) -> str:
    """J-2906 (F-3578): cut `text` to at most `n` chars on a SENTENCE end (if one falls in the last 25% of the budget)
    else on a WORD boundary with a trailing "..." -- never mid-word. Whole text returned untouched when it fits."""
    s = (text or "").strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    last = None
    for m in _SENTENCE_END.finditer(cut):
        last = m
    if last is not None and last.end() >= n * 0.75:
        return cut[:last.end()].rstrip()
    room = max(1, n - 3)
    cut = s[:room]
    if not s[room].isspace():
        sp = cut.rfind(" ")
        if sp > 0:
            cut = cut[:sp]
    return cut.rstrip(" ,;:-—") + "..."


def _grounds_cut(text: str) -> str:
    """J-3493 (F-4104): the source cut for a ground's stored text: GROUNDS_TEXT chars of real content cut on a boundary,
    never mid-word. The leading store label is KEPT (the judges read the ground as stored) but does not eat the budget;
    render() strips it. Label-then-boundary: measure the label, then cut the body on a boundary."""
    raw = (text or "").strip()
    body = _strip_store_label(raw)
    idx = raw.find(body[:20]) if body else -1
    lab = idx if 0 < idx <= 200 else 0
    return _clip_boundary(raw, GROUNDS_TEXT + lab)


def _strip_store_label(text: str) -> str:
    """J-2906 (F-3578): a memory row's own store label is bookkeeping, not what he found: a leading
    "[gist · semantic]" / "[Essay — on '...']" / "[From 'Book']" bracket label (balanced, so a title with brackets in it
    survives), a leading "Q:" / "A:" / "Input:" row tag, and the newline + "A:" that joins a question row to its answer. An
    UNBALANCED leading bracket is a label the old 200-char cut sliced through: the whole snippet is label, so ''."""
    s = (text or "").strip()
    for _ in range(4):
        if s.startswith("["):
            depth, end = 0, -1
            for i, ch in enumerate(s):
                if ch == "[":
                    depth += 1
                elif ch == "]":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            if end < 0:
                return ""
            s = s[end + 1:].lstrip()
            continue
        m = re.match(r"(?:Q|A|Input|Output)\s*:\s*", s)
        if m:
            s = s[m.end():]
            continue
        break
    s = re.sub(r"\s*\n\s*(?:A|Q)\s*:\s*", " ", s)
    return re.sub(r"\s+", " ", s).strip()


_COUNTER_TAIL = re.compile(r"\s*[-—–]\s*\d+\s*time\(s\)[^.]*\.?\s*$", re.I)


def _is_conversation_record(text: str) -> bool:
    """J-2911 (F-3595): a stored conversation record is not something his question 'touches': Travis's canonical
    "[Travis said to me] ..." fragment, or a cycle summary "Q: <what was said>\nA: <the reply>" (both origin='lived',
    so the origin cannot tell them apart; the content shape can). Checked on the RAW stored text."""
    s = (text or "").lstrip()
    return s.startswith("[Travis said to me]") or s.startswith("Q:")


def _first_sentence(text: str, n: int) -> str:
    """One clean sentence: up to the first sentence end past 20 chars, cut on a boundary to <= n."""
    s = (text or "").strip()
    for m in _SENTENCE_END.finditer(s):
        if m.end() >= 20:
            s = s[:m.end()]
            break
    return _clip_boundary(s, n)


def _snippet(text: str, n: int) -> str:
    """A memory snippet for the return: store label stripped, the 'N time(s), most recent <date>' counter tail dropped
    (J-2911), then cut on a boundary."""
    return _clip_boundary(_COUNTER_TAIL.sub("", _strip_store_label(text)).strip(), n)


def _did_before(key: str) -> str:
    """J-2906 (F-3578): the can_do clause. A fact about his past stated from the procedure's own NAME (its key), never the
    stored statement (a compiled conversation procedure's statement is a past reply: spliced into 'you have ...' it read
    'you have Travis, observe the environment ...')."""
    name = _clip_boundary(re.sub(r"\s+", " ", (key or "").split(":", 1)[-1].replace("_", " ")).strip(), 60)
    return f"something you have done before: {name}" if name else ""


def _fit_return(items: list, budget: int) -> tuple[str, list]:
    """J-2911 (F-3594): join the return's sections [(name, text)] to <= `budget` chars WITHOUT slicing the whole text.
    Fits as built -> as is. Else each section is held to its own RETURN_SECTION_CAPS (cut on a boundary); still over ->
    whole sections are dropped lowest-priority first (RETURN_DROP_ORDER), then extra grounds from the last; the header and
    any honest label ("Your past holds little...", NOT_SETTLED_LABEL) are never dropped. -> (text, names_dropped)."""
    def _join(its):
        return " ".join(t for _, t in its if t)
    items = [(n_, t_) for n_, t_ in items if t_]
    dropped: list = []
    if len(_join(items)) <= budget:
        return _join(items), dropped
    items = [(n_, _clip_boundary(t_, RETURN_SECTION_CAPS[n_]) if n_ in RETURN_SECTION_CAPS else t_) for n_, t_ in items]
    for name in RETURN_DROP_ORDER:
        if len(_join(items)) <= budget:
            break
        if any(n_ == name for n_, _ in items):
            items = [(n_, t_) for n_, t_ in items if n_ != name]
            dropped.append(name)
    while len(_join(items)) > budget and sum(1 for n_, _ in items if n_ == "ground") > 1:
        last = max(i for i, (n_, _) in enumerate(items) if n_ == "ground")
        items.pop(last)
        dropped.append("ground")
    text = _join(items)
    if len(text) > budget:                                      # unreachable with the caps; never exceed the cap
        text = _clip_boundary(text, budget)
    return text, dropped


def render(ent: dict, cargo: dict, judged: dict, now: float | None = None) -> str:
    """The return, rendered from the cargo's TYPED fields — never a synthesis call. Honest when empty: 'your past
    holds little on this' only when there were no grounds and the judges ruled; 'could not get a clear look' when they
    were down; 'what you found did not settle it' when grounds exist but the judge ruled they do not (J-2911, F-3593:
    the grounds are shown, not withheld). Built per section within RETURN_MAX_CHARS (J-2911, F-3594): whole low-priority
    sections are dropped, never sliced, and the closing question is always kept. States what he found and asks whether
    it holds; never says what to do (the world never leads)."""
    q = _clip_boundary(ent.get("q") or "", 220)
    items = [("head", f"Something you {_origin_phrase(ent, now)}: \"{q}\". You went looking in what you have lived and read.")]
    grounds = cargo.get("grounds") or []
    oc = cargo.get("grounds_outcome", "unclear")

    def _ground_items():
        return [("ground", f"In {g.get('origin','') or 'something you read'}, {g.get('age','') or 'some time ago'}: {_snippet(g.get('text',''), GROUNDS_TEXT)}")
                for g in grounds[:3] if _snippet(g.get('text',''), GROUNDS_TEXT)]
    a_ = judged.get("a")
    if grounds and a_ in ("yes", "partly"):
        items += _ground_items()
        why = cargo.get("why") or {}
        if why.get("text") and why.get("supports") != "no":
            items.append(("why", why["text"]))
    elif grounds and a_ == "unclear":
        items.append(("label", "You could not get a clear look at what bears on it."))
    elif grounds and (NOT_SETTLED_SHOWS_GROUNDS and a_ is not None):
        items += _ground_items()                                  # J-2911: found, judged not to settle it: show them + say so
        items.append(("label", NOT_SETTLED_LABEL))
    elif oc == "unclear":
        items.append(("label", "You could not get a clear look at what bears on it."))
    else:
        items.append(("label", "Your past holds little on this."))
    _ln = cargo.get("lookup_nudge") or {}
    if _ln.get("applies") and _ln.get("mode") == "live" and not grounds:   # J-4075: founder override of D-0661's no-offer rule
        items.append(("lookup", LOOKUP_NUDGE_LINE))
    against = cargo.get("against") or {}
    if against.get("text") and judged.get("c") in ("yes", "partly"):
        items.append(("against", "Against it: " + against["text"] + (f" ({against['scope']})" if against.get("scope") and judged.get("c") == "partly" else "")))
    cons = cargo.get("consequences") or []
    if cons and judged.get("b") in ("yes", "partly") and not (NO_CONSEQUENCES_WITHOUT_GROUNDS and not grounds):
        items.append(("cons", "If this is so: " + " ".join(c.get("text", "") for c in cons[:CONS_USED])))
    own = cargo.get("own_test") or {}
    if own.get("text"):                                         # D-0632: his own hypothesis's own test, from memory
        items.append(("own", "What would tell this from coincidence: " + own["text"] + "."))
    conn = cargo.get("connections") or {}
    # J-2911 (F-3595): one clean sentence each; a stored conversation record (Travis's words, a Q:/A: cycle summary) is skipped.
    know = [_first_sentence(_snippet(k.get("text", ""), TOUCH_SNIPPET_CHARS), TOUCH_SNIPPET_CHARS)
            for k in (conn.get("know") or []) if not _is_conversation_record(k.get("text", ""))][:2]
    seen = [_first_sentence(_snippet(s_.get("text", ""), TOUCH_SNIPPET_CHARS), TOUCH_SNIPPET_CHARS)
            for s_ in (conn.get("seen") or []) if not _is_conversation_record(s_.get("text", ""))][:1]
    touch = [t for t in know + [_did_before(c.get("key", "")) for c in (conn.get("can_do") or [])[:1]] + seen if t.strip()][:3]
    if touch:
        items.append(("touch", "It touches: " + " | ".join(touch)))
    body, _dropped = _fit_return(items, RETURN_MAX_CHARS - len(RETURN_CLOSING) - 1)
    return body + " " + RETURN_CLOSING


async def run(q_id: str) -> dict | None:
    """Walk one boarded entry through the five stops (grounds, why, consequences, connections, against) and the judge;
    log would_return; under FOLLOW_LINE == "live" also place the return in _PENDING for delivery (_place_pending).
    Fail-open: a failed stop records its failure and the line continues; the row always says what happened."""
    ent = _entry(q_id)
    if not ent:
        return None
    q = (ent.get("q") or "").strip()
    kind, source, slot = ent.get("kind", "question"), ent.get("source", ""), ent.get("slot", "")
    train_id = (ent.get("asked_by") or {}).get("train_id")
    depth = int((ent.get("line") or {}).get("depth", 0) or 0)
    t0 = _now()
    cargo: dict = {"grounds": [], "grounds_outcome": "unclear", "why": {}, "consequences": [],
                   "connections": {}, "against": {}, "own_test": {}, "status": "undetermined"}
    stops: dict = {}
    try:
        _set_line(q_id, state="grounds", started=t0)
        _publish(q_id, kind, source, slot, "grounds")
        # stop 1
        t_g = _now()
        try:
            g = await _stop_grounds(q, train_id)
            _dd = int(g.pop("grounds_deduped", 0) or 0)      # J-2972: kept out of the cargo, counted in the stop summary
            cargo.update(g)
            stops["grounds"] = {"n": len(g["grounds"]), "outcome": g["grounds_outcome"]}
            if _dd:
                stops["grounds"]["deduped"] = _dd
        except Exception as exc:
            stops["grounds"] = {"n": 0, "outcome": "failed", "err": str(exc)[:120]}
        stops["grounds"]["secs"] = round(_now() - t_g, 1)
        _ride("follow", "evidence:follow", "bucket", q_id, kind, source, slot, "grounds",
              stops["grounds"]["outcome"], sum(len(x.get("text", "")) for x in cargo["grounds"]))
        if DEFER_UNCLEAR and grounds_unclear(stops["grounds"]["outcome"], len(cargo["grounds"]), stops["grounds"]["secs"]):
            return _defer(q_id, ent, "grounds_unclear", stops, cargo, t0)          # J-2570: never judged, never pending
        _set_line(q_id, state="why"); _publish(q_id, kind, source, slot, "why")
        # stop 2
        try:
            cargo["why"] = await _stop_why(q, cargo["grounds"])
            stops["why"] = {"supports": cargo["why"].get("supports"), "cites": len(cargo["why"].get("cites") or []),
                            "self_sealing": bool(cargo["why"].get("self_sealing"))}
        except Exception as exc:
            cargo["why"] = {"text": "", "cites": [], "supports": "no", "failed": str(exc)[:120]}
            stops["why"] = {"supports": "failed"}
        _ride("follow", "line:why", "bucket", q_id, kind, source, slot, "why", str(stops["why"].get("supports")),
              len(cargo["why"].get("text", "")))
        if DEFER_UNCLEAR and gen_dead(cargo["grounds"], cargo["why"]):
            return _defer(q_id, ent, "gen_dead", stops, cargo, t0)                 # J-2570: the command-r7b lane is down
        _set_line(q_id, state="consequences"); _publish(q_id, kind, source, slot, "consequences")
        # stop 3
        try:
            if NO_CONSEQUENCES_WITHOUT_GROUNDS and not cargo["grounds"]:
                cargo["consequences"] = []                       # J-2910: no grounds, no deduction, no model call
                stops["consequences"] = {"n": 0, "skipped": "no-grounds"}
            else:
                cargo["consequences"] = await _stop_consequences(q, cargo["grounds"], cargo["why"])
                _before = cargo["consequences"]
                cargo["consequences"], n_drop = drop_intentions(_before)
                stops["consequences"] = {"n": len(cargo["consequences"])}
                if n_drop:
                    stops["consequences"]["dropped_intention"] = n_drop
                    _kept = {id(c) for c in cargo["consequences"]}      # J-3928: log WHAT was dropped (J-2910 false-positive read)
                    stops["consequences"]["dropped_texts"] = [str(c.get("text", ""))[:160] for c in _before if id(c) not in _kept]
                _blank = [c.get("slot_raw") for c in cargo["consequences"] if c.get("slot_raw")]
                if _blank:
                    stops["consequences"]["slot_raw_blank"] = _blank[:3]
                _leak = sum(1 for c in cargo["consequences"] if c.get("slot_leak"))
                if _leak:
                    stops["consequences"]["slot_leak_checkable"] = _leak    # J-4170: F-5015's leak, counted per row
        except Exception as exc:
            stops["consequences"] = {"n": 0, "err": str(exc)[:120]}
        _ride("follow", "line:consequences", "bucket", q_id, kind, source, slot, "consequences",
              str(stops["consequences"]["n"]), sum(len(c.get("text", "")) for c in cargo["consequences"]))
        # stop 3b (D-0632, J-3244): his own stored hypothesis's own test, from memory; never fails the line
        try:
            cargo["own_test"] = await _stop_own_test(q)
            if cargo["own_test"]:
                stops["own_test"] = {"inference_id": cargo["own_test"].get("inference_id", ""),
                                     "object_id": cargo["own_test"].get("object_id", ""),
                                     "n": len(cargo["own_test"].get("candidates") or [])}
                _ride("follow", "line:own_test", "bucket", q_id, kind, source, slot, "own_test",
                      cargo["own_test"].get("inference_id", ""), len(cargo["own_test"].get("text", "")))
        except profile.NonLiveWriteError:
            raise
        except Exception as exc:
            cargo["own_test"] = {}
            stops["own_test"] = {"err": str(exc)[:120]}
        _set_line(q_id, state="connections"); _publish(q_id, kind, source, slot, "connections")
        # stop 4
        try:
            cargo["connections"] = await _stop_connections(q)
            c = cargo["connections"]
            stops["connections"] = {"know": len(c.get("know") or []), "can_do": len(c.get("can_do") or []),
                                    "seen": len(c.get("seen") or [])}
        except Exception as exc:
            stops["connections"] = {"err": str(exc)[:120]}
        _ride("follow", "memory_ask:follow", "bucket", q_id, kind, source, slot, "connections",
              json.dumps(stops["connections"], sort_keys=True), 0)
        _set_line(q_id, state="against"); _publish(q_id, kind, source, slot, "against")
        # stop 5 (the line's own; train_split_merge's berth)
        try:
            cargo["against"] = await _stop_against(q, cargo["grounds"])
            stops["against"] = {"n_chars": len(cargo["against"].get("text", "")), "cites": len(cargo["against"].get("cites") or [])}
        except Exception as exc:
            cargo["against"] = {"text": "", "cites": [], "scope": "", "failed": str(exc)[:120]}
            stops["against"] = {"n_chars": 0, "err": str(exc)[:120]}
        _ride("follow", "line:against", "bucket", q_id, kind, source, slot, "against",
              "stated" if cargo["against"].get("text") else "none", len(cargo["against"].get("text", "")))
        if DEFER_UNCLEAR and (stops["consequences"].get("err") or cargo["against"].get("failed")):
            return _defer(q_id, ent, "gen_dead", stops, cargo, t0)                 # J-2570: a later stop raised
        _set_line(q_id, state="judged"); _publish(q_id, kind, source, slot, "judged")
        # the judge
        try:
            judged = await _judge(q, cargo, q_id)
        except Exception as exc:
            judged = {"a": "unclear", "b": "unclear", "c": "unclear", "a_how": "failed", "b_how": str(exc)[:80], "c_how": "failed"}
        stops["judge"] = judged
        cargo["status"] = cargo_status(judged)
        cargo["lookup_nudge"] = lookup_nudge(ent, cargo, judged)
        if cargo["lookup_nudge"]["reason"] not in ("off", "not-his-question"):
            stops["lookup_nudge"] = cargo["lookup_nudge"]
        text = render(ent, cargo, judged)
        row = {"ts": round(_now(), 3), "kind": "would_return", "q_id": q_id, "q": q[:220], "kind_cargo": kind,
               "source": source, "slot": slot, "depth": depth, "train_id": train_id,
               "about_key": ent.get("about_key"), "stops": stops, "judged": judged,
               "cargo": {"grounds": [{k: v for k, v in g.items() if k != "text"} | {"text": g.get("text", "")[:120]}
                                     for g in cargo["grounds"]],
                         "grounds_outcome": cargo["grounds_outcome"], "why": cargo["why"],
                         "consequences": cargo["consequences"], "against": cargo["against"],
                         "own_test": cargo.get("own_test") or {},
                         "connections": {k: [{kk: vv for kk, vv in x.items() if kk != "text"} | {"text": x.get("text", "")[:100]}
                                             for x in (v or [])] for k, v in (cargo["connections"] or {}).items()},
                         "status": cargo["status"]},
               "return_text": text, "secs": round(_now() - t0, 1)}
        _append(row)
        _set_line(q_id, state="would_return", stops=stops, judged=judged, return_chars=len(text),
                  finished=_now(), cargo={"grounds_outcome": cargo["grounds_outcome"],
                                           "why_supports": cargo["why"].get("supports"),
                                           "n_consequences": len(cargo["consequences"]),
                                           "status": cargo["status"]})
        _publish(q_id, kind, source, slot, "would_return", cargo["status"])
        _ride("monologue", "follow_line:return", "bucket", q_id, kind, source, slot, "would_return",
              f"a={judged.get('a')} b={judged.get('b')} c={judged.get('c')}", len(text))
        if FOLLOW_LINE == "live":                                # Phase 1 (J-2460): the return waits for him
            _place_pending(q_id, text, ent, cargo, judged)
        if not cargo["grounds"]:                                 # closure_producer P4: a follow that found nothing
            try:
                from core import frontier as _fr_att
                _fr_att.note_attempt(q_id, False, "follow_no_grounds")
            except profile.NonLiveWriteError:
                raise
            except Exception:
                pass
        # consequence re-boarding (from Phase 0 on: real boardings at the lowest priority; depth-capped; one run's
        # consequences count as ONE re-boarding of their about_key, allowed once per 24 h)
        if judged.get("b") in ("yes", "partly") and depth < MAX_DEPTH and cargo["consequences"]:
            key = ent.get("about_key") or q_id
            if reboard_ok(key):
                for c in cargo["consequences"][:CONS_USED]:
                    try:
                        board(c.get("text", ""), "consequence", kind="claim", slot=c.get("slot", ""),
                              about=ent.get("about", ""),
                              asked_by={"parent_q_id": q_id, "about_key": key, "train_id": train_id, "ts": _now()},
                              allow_self=True, depth=depth + 1, guard=False)
                    except profile.NonLiveWriteError:
                        raise
                    except Exception:
                        pass
                _note_reboard(key)
            else:
                _ride("frontier", "follow_line:board:consequence", "cup", q_id, "claim", "consequence", "",
                      "board", "skip-reboard-24h")
        logger.info("[follow_line] %s/%s '%s' -> grounds %s, why %s, cons %d, judge a=%s b=%s (%.0fs)",
                    source, kind, q[:50], cargo["grounds_outcome"], cargo["why"].get("supports"),
                    len(cargo["consequences"]), judged.get("a"), judged.get("b"), _now() - t0)
        return row
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[follow_line] run(%s) failed (non-fatal): %s", q_id, exc)
        try:
            _set_line(q_id, state="failed", err=str(exc)[:120], finished=_now())
        except Exception:
            pass
        return None


# ── Phase 1: the return, the settle, the close (D-0494 (3), 2026-10-28) ───────────────────────────────────────
def _place_pending(q_id: str, text: str, ent: dict, cargo: dict, judged: dict) -> None:
    """The graded return waits for the next idle thought: the si open-doubt cup generalised to a dict keyed by
    question id, TTL LINE_TTL_S, capped at PENDING_CAP (oldest to the fallback path). Never raises."""
    try:
        _expire_stale()
        _PENDING[q_id] = {"ts": _now(), "text": text, "ent": ent, "cargo": cargo, "judged": judged}
        _set_line(q_id, state="pending")
        _publish(q_id, ent.get("kind", "question"), ent.get("source", ""), ent.get("slot", ""), "pending", cargo.get("status", "undetermined"))
        while len(_PENDING) > PENDING_CAP:
            oldest = min(_PENDING, key=lambda k: _PENDING[k]["ts"])
            _expire(oldest, "cap")
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[follow_line] place_pending failed (non-fatal): %s", exc)


_ASKED_AGO_RE = re.compile(r"^(Something you asked )(?:just now|a while ago|some hours ago|yesterday|\d+ days ago|earlier)")


def _fresh_text(rec: dict) -> str:
    """J-2907: the return text with ONLY its asked-age words refreshed to NOW (the text was rendered when the line finished;
    it is met hours later). Touches nothing else: grounds, cap and closing question stay as rendered. Fail-open."""
    text = rec.get("text") or ""
    try:
        ent = rec.get("ent") or {}
        if ent.get("source") != "asked":
            return text
        ago = _asked_ago(ent, _now())
        return _ASKED_AGO_RE.sub(lambda m: m.group(1) + ago, text, count=1)
    except Exception:
        return text


def _expire_stale(now: float | None = None) -> None:
    now = now or _now()
    for k in [k for k, v in _PENDING.items() if now - v["ts"] > LINE_TTL_S]:
        _expire(k, "ttl")


def _expire(q_id: str, reason: str) -> None:
    """A return he never met falls back to the frontier's EXISTING offer path (p=0.3, 2-hour gap) as the entry's
    finding -- nothing new is pushed, nothing is lost."""
    rec = _PENDING.pop(q_id, None)
    if not rec:
        return
    rec["text"] = _fresh_text(rec)
    try:
        from core import frontier as _fr
        # closure_producer (2026-11-16): a finding his own lookup attached is not overwritten by an unmet return
        # from his own memory; the world's answer stays on the question. The line still expires as before.
        if not _fr.finding_from_lookup(_fr.get(q_id) or {}):
            _fr.attach_finding(q_id, "what you found in your own memory", rec["text"][:600])
        _set_line(q_id, state="expired", expire_reason=reason)
        ent = rec["ent"]
        _publish(q_id, ent.get("kind", "question"), ent.get("source", ""), ent.get("slot", ""), "expired")
        _ride("monologue", "follow_line:return", "bucket", q_id, ent.get("kind", "question"), ent.get("source", ""),
              ent.get("slot", ""), "expired", reason, len(rec["text"]))
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[follow_line] expire failed (non-fatal): %s", exc)


def pending_count() -> int:
    return len(_PENDING)


def take_delivery() -> dict | None:
    """Called ONCE per idle-thought prompt build, before the system prompt: the oldest unexpired pending return,
    consumed (one per thought), or None. The caller appends `text` to the prompt and remembers `q_id` so the same
    tick's `settled` field is parsed. Never raises past the fence."""
    if FOLLOW_LINE != "live" or not _PENDING:
        return None
    try:
        _expire_stale()
        if not _PENDING:
            return None
        q_id = min(_PENDING, key=lambda k: _PENDING[k]["ts"])
        rec = _PENDING.pop(q_id)
        ent = rec["ent"]
        rec["text"] = _fresh_text(rec)                          # J-2907: age the origin phrase at DELIVERY, not at render
        _set_line(q_id, state="delivered", delivered=_now())
        _publish(q_id, ent.get("kind", "question"), ent.get("source", ""), ent.get("slot", ""), "delivered",
                 rec["cargo"].get("status", "undetermined"))
        _ride("monologue", "follow_line:return", "bucket", q_id, ent.get("kind", "question"), ent.get("source", ""),
              ent.get("slot", ""), "delivered", f"age_s={round(_now() - rec['ts'])}", len(rec["text"]))
        _DELIVERED[q_id] = rec
        if len(_DELIVERED) > 32:
            for k in sorted(_DELIVERED, key=lambda k: _DELIVERED[k]["ts"])[:16]:
                _DELIVERED.pop(k, None)
        return {"q_id": q_id, "text": rec["text"], "source": ent.get("source", ""), "q": ent.get("q", "")}
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[follow_line] take_delivery failed (non-fatal): %s", exc)
        return None


_DELIVERED: dict = {}                        # q_id -> the delivered record, kept until settle() reads it


def settle_later(q_id: str, verdict: str, thought: str, cycle_id: str = "") -> None:
    """From the thought tick: schedule settle() as a task (the closure composer runs off-loop). Never raises."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is None:
        return
    try:
        t = loop.create_task(settle(q_id, verdict, thought, cycle_id))
        _SETTLE_TASKS.add(t)
        t.add_done_callback(_SETTLE_TASKS.discard)
    except Exception:
        pass


async def settle(q_id: str, verdict: str, thought: str, cycle_id: str = "") -> dict:
    """What he said about the return he just met (plan §2.7):
      yes    -> frontier.resolve(q_id, how="line") (id-keyed, beside the lexical resolver) and the closure-law arm
                `line`: ONE fragment in his own words from the claim + grounds + why + his settling thought, logged to
                closure_shadow (kind=resolution, arm=line); written to the memory DB only under CLOSURE_WRITE_LIVE.
      partly -> the answered part is recorded under slots[slot] on the entry's about_key; the question stays open.
      no     -> logged; the entry stays open; one re-boarding allowed after a new touch of the same about_key.
      ""     -> he said nothing about it: logged as unsaid; nothing changes.
    Never raises past the fence."""
    rec = _DELIVERED.pop(q_id, None) or {}
    ent = rec.get("ent") or _entry(q_id) or {}
    kind, source, slot = ent.get("kind", "question"), ent.get("source", ""), ent.get("slot", "")
    out = {"q_id": q_id, "verdict": verdict or "unsaid", "resolved": False, "closure": None}
    try:
        from core import frontier as _fr
        if verdict == "yes":
            # closure_producer P2: his yes is a claim; the decoupled gate (core/closure_gate.py) decides whether the
            # entry is resolved. Mode "off" is the old close, byte for byte; "shadow" is the old close plus a log row.
            _gr = None
            try:
                from core import closure_gate as _cg
                _gr = await _cg.settle_yes(q_id, ent, rec.get("text") or "", cycle_id)
                out["resolved"] = bool(_gr.get("resolved"))
                out["gate"] = {k: _gr.get(k) for k in ("verdict", "how", "status", "mode")}
            except profile.NonLiveWriteError:
                raise
            except Exception as exc:
                logger.debug("[follow_line] closure gate failed, old close (non-fatal): %s", exc)
                out["resolved"] = _fr.resolve(q_id, how="line")
            _enforced = bool(_gr and _gr.get("mode") == "enforce")
            _set_line(q_id, state="settled_yes", settled_ts=_now(), settled_cycle=cycle_id[:8])
            try:
                from core import closure as _cl
                from core import idle_offloop as _off
                if _enforced and not out["resolved"]:
                    out["closure"] = {"compose_how": "skipped-gate-not-passed"}   # no resolution memory for an unverified yes
                elif _enforced and _gr.get("how") == "lookup" and _gr.get("entry"):
                    out["closure"] = await _off.off_loop(_cl.record_lookup_answered, _gr["entry"])   # P5: the lookup arm
                else:
                    out["closure"] = await _off.off_loop(_cl.record_line_settled, ent, rec.get("cargo") or {}, thought)
            except profile.NonLiveWriteError:
                raise
            except Exception as exc:
                logger.debug("[follow_line] closure arm failed (non-fatal): %s", exc)
            _publish(q_id, kind, source, slot, "settled_yes", (rec.get("cargo") or {}).get("status", "undetermined"))
        elif verdict == "partly":
            key = ent.get("about_key") or q_id
            part = (thought or "")[:300]
            _fr.fill_slot(key, slot or "what", part, q_id)
            _set_line(q_id, state="settled_partly", settled_ts=_now(), settled_cycle=cycle_id[:8])
            _publish(q_id, kind, source, slot, "settled_partly")
        elif verdict == "no":
            _set_line(q_id, state="settled_no", settled_ts=_now(), settled_cycle=cycle_id[:8])
            _publish(q_id, kind, source, slot, "settled_no")
            _fr.note_attempt(q_id, False, "settled_no")     # closure_producer P4: a follow that did not answer it
        else:
            _set_line(q_id, state="unsaid", settled_ts=_now(), settled_cycle=cycle_id[:8])
        if SETTLE_OVERLAP_SHADOW and verdict == "yes":
            try:
                ov = settle_overlap(ent.get("q") or "", rec.get("text") or "", thought or "")
                _append({"ts": round(_now(), 3), "kind": "settle_overlap", "q_id": q_id, "q": (ent.get("q") or "")[:220],
                         "overlap_score": ov["score"], "shared": ov["shared"], "n_src": ov["n_src"],
                         "n_thought": ov["n_thought"], "gate_verdict": "would_not_close" if ov["would_not_close"] else "close",
                         "original_verdict": "closed" if out["resolved"] else "yes_not_resolved",
                         "threshold": SETTLE_OVERLAP_MIN, "cycle_id": cycle_id[:8]})
            except profile.NonLiveWriteError:
                raise
            except Exception as exc:
                logger.debug("[follow_line] overlap shadow failed (non-fatal): %s", exc)
        _ride("monologue", "follow_line:settle", "cup", q_id, kind, source, slot, "settle", out["verdict"],
              len(thought or ""), resolved=out["resolved"])
        _append({"ts": round(_now(), 3), "kind": "settled", "q_id": q_id, "q": (ent.get("q") or "")[:220],
                 "source": source, "slot": slot, "verdict": out["verdict"], "resolved": out["resolved"],
                 "gate": out.get("gate"),
                 "closure_how": (out["closure"] or {}).get("compose_how") if isinstance(out["closure"], dict) else None,
                 "thought": (thought or "")[:300], "cycle_id": cycle_id[:8],
                 # J-2570: a settle on a return whose grounds were unclear is not evidence about the claim
                 "vacuous": grounds_unclear((rec.get("cargo") or {}).get("grounds_outcome") or "",
                                            len((rec.get("cargo") or {}).get("grounds") or []), None)
                            if rec.get("cargo") else False})
        logger.info("[follow_line] settled %s: %s -> %s", out["verdict"], (ent.get("q") or "")[:50],
                    "resolved" if out["resolved"] else "open")
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[follow_line] settle failed (non-fatal): %s", exc)
    return out


def status() -> dict:
    """Read-only, for du_pulse: what the line has done this process. J-2570: would_return counts ALL rows; every
    breakdown (by_source, judge_*, status, settled) skips vacuous rows (is_vacuous: grounds unclear) and any settle
    that answered one -- those are counted apart under vacuous_*; deferred/unjudged runs are counted by reason."""
    try:
        rows = []
        if SHADOW_LOG.exists():
            with open(SHADOW_LOG, encoding="utf-8") as f:
                for l in f:
                    try:
                        rows.append(json.loads(l))
                    except Exception:
                        pass
        wr, st, vac_wr, vac_st, last_vac = [], [], 0, collections.Counter(), {}
        for r in rows:
            if r.get("kind") == "would_return":
                v = is_vacuous(r)
                last_vac[r.get("q_id")] = v
                if v:
                    vac_wr += 1
                else:
                    wr.append(r)
            elif r.get("kind") == "settled":
                if r.get("vacuous") or (r.get("vacuous") is None and last_vac.get(r.get("q_id"))):
                    vac_st[r.get("verdict")] += 1
                else:
                    st.append(r)
        dr = [r for r in rows if r.get("kind") == "deferred"]
        return {"flag": FOLLOW_LINE, "rows": len(rows), "would_return": len(wr) + vac_wr,
                "vacuous_would_return": vac_wr, "vacuous_settled": dict(vac_st),
                "deferred": dict(collections.Counter(r.get("reason") for r in dr if not r.get("final"))),
                "unjudged": dict(collections.Counter(r.get("reason") for r in dr if r.get("final"))),
                "by_source": dict(collections.Counter(r.get("source") for r in wr)),
                "judge_a": dict(collections.Counter((r.get("judged") or {}).get("a") for r in wr)),
                "judge_b": dict(collections.Counter((r.get("judged") or {}).get("b") for r in wr)),
                "judge_c": dict(collections.Counter((r.get("judged") or {}).get("c") for r in wr)),
                "judge_c_how": dict(collections.Counter((r.get("judged") or {}).get("c_how") for r in wr)),
                "cuts_count": dict(_cuts_count),
                "status": dict(collections.Counter((r.get("cargo") or {}).get("status") for r in wr)),
                "settled": dict(collections.Counter(r.get("verdict") for r in st)),
                "in_flight": _in_flight, "boarded_last_hour": len(_board_log), "pending": len(_PENDING)}
    except Exception as exc:
        return {"flag": FOLLOW_LINE, "error": str(exc)[:120]}
