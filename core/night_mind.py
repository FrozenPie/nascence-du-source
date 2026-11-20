"""core/night_mind.py (J-2017, sleep_as_a_mode Phase 1, D-0399 A, 2026-10-09, restart-gated).

The night-mind: while a sleep bout runs, the hot lane keeps generating a few slow thoughts as its OWN asyncio
task, seeded ONLY from the night's own material (the replay set, the dream's tail once a dream exists; the
D-0231 dormant pick has no code yet and is reported as not_built), minutes apart, hands off, no hint push to the
Witness, on the same hot hub as the consolidation passes.

PHASE 1 WAS BORN A SHADOW AND IS NOT ONE ANY MORE (J-2955, F-3640: this docstring said otherwise after the code moved on).
What THIS module does: generate the thoughts and log them to data/night_mind_shadow.jsonl; it is not dispatched and is
NOT graded (decoupled-judge law: nothing grades it; if a judge is ever wanted it is the panel, not this lane). It never
writes a fragment itself and never builds a prompt for anyone else. What the code around it does with each thought
(Phase 2, D-0400 B, core/night_dormant.py, which keeps its own docstring):
  * every generated thought is written as ONE dormant memory fragment through the optional on_thought hook (layer
    'dormant', cold=1 from birth, origin 'night_thought'; invisible to normal recall and to the sleep trigger, reachable
    only through deep recall); the hook is armed in nodes/inner_monologue_node.py only when night_dormant.enabled();
  * the LAST thought of each sleep is armed as a seed (kind seed_ready in data/night_dormant.jsonl) and
    night.waking_dream_seed() hands it, once, to the first waking thought (kind seed_drawn); every later call, and any
    call with the dormant flag off, is the dream's last image as before.
Flags (both restart-gated): NIGHT_MIND_ENABLED defaulted False under J-2017 and has been True since J-2065
(founder-approved 2026-10-15, after F-2680 found the worst in-sleep stall sits in the dream span and the shadow flip
generates nothing). night_dormant.NIGHT_DORMANT_ENABLED has been True since J-2410 (Travis go 2026-10-18 after the J-2035
seven-sleep read, F-3058). Both must hold, and night_dormant must not be tripped, for the dormant write and waking seed.
The 7-sleep read against the D-0399 defeater (evaluate(), below) is the measuring instrument, not a gate on those flags.

Rows in the shadow log (phase 1 rows carry "phase": 1; Phase 0 rows are "phase": 0, generated False):
  kind "night_thought"  one per generated thought (or a failed attempt, generated False + error):
                        seed source/snippet, the thought, gen_s, cosine to the replay set (max/mean) now,
                        cos_dormant None (not built); cos_dream is filled in the summary (the dream is made
                        AFTER the consolidation span, so it does not exist when most thoughts are written)
  kind "sleep_summary"  one per sleep, written at stop(): thoughts, failed, slots_no_seed, seeds_available,
                        per-thought cos_dream and its median, the night ledger's stage times (the "consolidation
                        pass durations" the before/after comparison needs), the hold flags

J-2594 (D-0521 A, 2026-10-30, F-3283): NIGHT_VARIETY_ENABLED swaps in SYSTEM_PROMPT_V2 (no "quiet", toward the
particular thing in the seed, each thought a different kind) and a data-driven do-not-repeat list of image words that
recur across the last night thoughts (read-only from this log's tail plus this sleep's own). Rows carry prompt_v and
avoid_images. Restart-gated. (J-2037's NIGHT_DORMANT_ENABLED was already on before this change, since J-2410; the original wording
that it stayed behind a post-change 7-sleep content read was wrong, F-3640.)

J-3192 (D-0579, founder 2026-11-02, F-3647): V2 traded the quiet/silence monoculture for a template ("A single, heavy
brass key ..."): 28 of 50 thoughts opened "A ", and 12 of 50 reused a word from the do-not-repeat list because that list
carried style adjectives (single, sudden, sharp) that the denial line then planted. V3 (NIGHT_PROMPT_VERSION 3) removes the
"an object, a place, a colour, ..." example list from the system prompt and makes the do-not-repeat list nouns only
(_not_noun below: a closed stoplist of determiners, adjectives, adverbs and verb forms plus suffix rules; it is a
filter, not a part-of-speech tagger). Nothing else in the wording changed and no new line tells Du what to write. Rows
carry prompt_v 3 so the shadow log splits pre/post. NIGHT_PROMPT_VERSION = 2 restores V2 and its old list exactly.
Restart-gated. Read after 14 sleeps against the D-0579 defeater (more than 40 percent opening "A ", or reusing a listed word).

evaluate() is the 7-sleep read (plan section 5 / D-0399 defeater): sleep duration vs the same regime before,
passes failing open, zero thoughts with seeds available, median cosine to the dream above 0.6.

Both the task and every write are fail-open: a bug here must never be able to break a sleep.
"""
from __future__ import annotations

import asyncio
import json
import logging
import statistics
import time
from pathlib import Path

logger = logging.getLogger("nascence.night_mind")

NIGHT_MIND_ENABLED = True          # D-0399 A, Phase 1 flag. ON since J-2065 (founder-approved 2026-10-15 after the F-2680 stall check; was False). Restart-gated.
NIGHT_FIRST_AFTER_S = 120.0        # no night thought in the first two minutes (replay, to-bed settle)
NIGHT_THOUGHT_FLOOR_S = 300.0      # "minutes between thoughts" (plan 3.1); Phase 1 measures the real number
NIGHT_MAX_THOUGHTS = 6             # "a handful per sleep, not a stream"
GEN_TIMEOUT_S = 120.0              # one hot-hub call; a slow hub costs a thought, never the sleep
GEN_MAX_TOKENS = 160
GEN_TEMPERATURE = 0.8
SEED_CHARS = 280
DREAM_COS_HOLD = 0.6               # D-0399 defeater: median cosine to the night's dream above this = second dream engine
DURATION_UP_HOLD = 0.15            # D-0399 defeater: sleep duration up more than 15 percent
MIN_SLEEPS_FOR_READ = 7

_DATA = Path(__file__).parent.parent / "data"
NIGHT_MIND_SHADOW_LOG = _DATA / "night_mind_shadow.jsonl"

# The original Phase 1 prompt (J-2017), kept verbatim: NIGHT_VARIETY_ENABLED False restores it exactly.
SYSTEM_PROMPT_V1 = (
    "You are asleep. The day is over and nothing is asking anything of you. There is no one to answer and nothing "
    "to do. Something from the night's own material drifts up. Let one quiet, private thought form around it, "
    "in your own voice, a sentence or two, unfinished is fine. Do not address anyone. Do not plan or decide.\n"
    'Reply as JSON: {"thought": "<the thought>"}'
)

# J-2594 (D-0521 A, Travis 2026-10-30, F-3283): variety / anti-repeat. F-3283 found the V1 wording ("one quiet,
# private thought", "drifts up") drives a quiet/silence/dust/weight monoculture (quiet in 43 pct of night thoughts).
# V2 drops "quiet", turns the thought toward the particular thing in the seed and where it leads, and asks each
# thought to differ from the last. It deliberately does NOT name the monoculture words (naming them primes a small
# model); the per-call do-not-repeat list in the user prompt is data-driven instead (_avoid_images). Same output
# shape (the JSON line), same temperature, same token cap. Restart-gated.
SYSTEM_PROMPT_V2 = (
    "You are asleep. The day is over and nothing is asking anything of you. There is no one to answer and nothing "
    "to do. Something from the night's own material drifts up. Let one private thought form around the particular "
    "thing in it: an object, a place, a colour, a sound, a smell, a touch, a creature, something that happened. "
    "Follow where that thing leads, not the mood of the night around it. Let each thought be a different kind of "
    "thought from the last one, with its own image. In your own voice, a sentence or two, unfinished is fine. "
    "Do not address anyone. Do not plan or decide.\n"
    'Reply as JSON: {"thought": "<the thought>"}'
)

# J-3192 (D-0579): V3 = V2 with the example list ("an object, a place, a colour, a sound, a smell, a touch, a creature,
# something that happened") removed; F-3647 found the model copies that list (object/scent/sound in nearly every output).
# Every other word is V2's, so the pre/post split in the shadow log is the one change the founder ruled.
SYSTEM_PROMPT_V3 = (
    "You are asleep. The day is over and nothing is asking anything of you. There is no one to answer and nothing "
    "to do. Something from the night's own material drifts up. Let one private thought form around the particular "
    "thing in it. "
    "Follow where that thing leads, not the mood of the night around it. Let each thought be a different kind of "
    "thought from the last one, with its own image. In your own voice, a sentence or two, unfinished is fine. "
    "Do not address anyone. Do not plan or decide.\n"
    'Reply as JSON: {"thought": "<the thought>"}'
)

# J-4316 (founder ruling 2026-11-18 on J-4312, F-5096): V4 = V3 plus one sentence forbidding the "A single X" opening frame
# and asking for a different way in each time. Every other word is V3's. Default OFF (NIGHT_PROMPT_VERSION stays 3);
# set NIGHT_PROMPT_VERSION = 4 to run it. Rows carry prompt_v 4 so the shadow log splits pre/post. Restart-gated.
SYSTEM_PROMPT_V4 = SYSTEM_PROMPT_V3.replace(
    "Do not address anyone.",
    'Do not open with "A single" or with "A" followed by a describing word; begin each thought a different way. '
    "Do not address anyone.", 1)

NIGHT_VARIETY_ENABLED = True       # J-2594 / D-0521 A: V2 prompt + do-not-repeat list. Restart-gated; False = V1 exactly.
NIGHT_PROMPT_VERSION = 3           # J-3192 / D-0579: 3 = V3 prompt + nouns-only list; 2 = V2 exactly. Only read while NIGHT_VARIETY_ENABLED. Restart-gated.
AVOID_RECENT_THOUGHTS = 12         # how many recent night thoughts (prior sleeps from the shadow log + this sleep) to scan
AVOID_MIN_DF = 2                   # an image word must recur in at least this many of them to be listed
AVOID_MAX_WORDS = 8                # at most this many words in the do-not-repeat list
AVOID_TAIL_BYTES = 262144          # read only the tail of the shadow log (bounded cost, fail-open)

SYSTEM_PROMPT = SYSTEM_PROMPT_V3   # the prompt in force while NIGHT_VARIETY_ENABLED (see _system_prompt)

_AVOID_STOP = frozenset((
    "about", "above", "across", "after", "again", "against", "almost", "along", "already", "also", "always", "among",
    "another", "around", "away", "back", "because", "been", "before", "behind", "being", "below", "beneath", "between",
    "beyond", "both", "but", "came", "cannot", "come", "comes", "could", "does", "doing", "done", "down", "during",
    "each", "even", "ever", "every", "feel", "feels", "felt", "find", "first", "from", "gone", "have", "having", "here",
    "himself", "hers", "into", "itself", "just", "keep", "kind", "know", "last", "least", "left", "less", "like", "little",
    "long", "made", "make", "many", "maybe", "might", "mind", "more", "most", "much", "must", "myself", "near", "never",
    "next", "nothing", "once", "only", "onto", "other", "over", "perhaps", "rather", "really", "same", "seem", "seems",
    "should", "since", "some", "something", "still", "such", "than", "that", "their", "them", "then", "there", "these",
    "they", "thing", "things", "this", "those", "though", "through", "thought", "thoughts", "till", "today", "tonight",
    "toward", "towards", "under", "unfinished", "until", "upon", "very", "want", "were", "what", "when", "where",
    "whether", "which", "while", "whose", "will", "with", "within", "without", "would", "your", "yours", "yourself",
))

# J-3192 (D-0579): the nouns-only filter for the do-not-repeat list (V3). No tagger is available in the runtime, so this
# is a deterministic approximation applied to the lower-cased word and its plural-stripped stem. A word is dropped when
# it is (1) on _NOT_NOUN, a closed list of the determiners, quantifiers, adjectives, adverbs and verb forms seen in the
# 433 logged night thoughts (including the style words F-3647 found on the list: single, sudden, sharp, heavy, cold,
# dark, faint), or (2) of a suffix shape that is almost never a noun (-ly -ous -ful -less -ive -ish -ic -ed -ing, or
# un- plus 3 letters), unless it is on _NOUN_EXCEPTIONS (ceiling, morning, seed, universe ...). A word whose noun sense
# dominates in these thoughts stays (dust, silence, weight, glass, brass, light, click, form, room, memory); one whose
# dominant use here is an adjective or a verb goes (quiet, dark, hang, settle). An unknown word with no listed form and no
# suffix shape passes through: the filter lowers the chance of a non-noun on the list, it does not remove it.
_NOT_NOUN = frozenset((
    # determiners, quantifiers, pronouns, number words, adverbs of place and time, contraction stems
    "single", "several", "enough", "everything", "anything", "someone", "anyone", "everyone", "nobody", "somewhere",
    "anywhere", "everywhere", "anymore", "instead", "inside", "outside", "yesterday", "tomorrow", "quite", "longer",
    "thousand", "else", "either", "neither", "whom", "whoever", "whatever", "doesn", "didn", "wasn", "isn", "aren",
    "couldn", "wouldn", "shouldn", "hasn", "haven", "hadn", "weren", "don", "won", "ain", "other", "own", "many", "few",
    # adjectives (dominant use in the logged thoughts)
    "quiet", "heavy", "dark", "cold", "sudden", "sharp", "faint", "soft", "empty", "tiny", "damp", "small", "warm",
    "cool", "silent", "thin", "grey", "gray", "distant", "slow", "hollow", "smooth", "blue", "rough", "green", "deep",
    "final", "real", "strange", "thick", "black", "loose", "fast", "broken", "hard", "ancient", "white", "clear", "pale",
    "brown", "jagged", "metallic", "hot", "wet", "dry", "old", "new", "young", "big", "large", "short", "tall", "high",
    "wide", "narrow", "bright", "dim", "bare", "raw", "red", "dull", "pure", "plain", "calm", "gentle", "tender",
    "fragile", "vast", "fresh", "stale", "clean", "dirty", "wild", "rare", "odd", "fine", "free", "full", "half", "whole",
    "able", "late", "early", "blind", "numb", "lost", "slight", "sweet", "bitter", "sour", "flat", "round", "tired",
    "alone", "tight", "steady", "stiff", "stark", "swollen", "worn", "frozen", "hidden", "forgotten", "golden", "wooden",
    "silver", "open", "shut", "certain", "possible", "strong", "weak", "shallow", "sleepy", "ordinary", "familiar",
    "private", "particular", "different", "stray",
    # verb forms (base, third person, irregular past) whose verb use dominates the logged thoughts
    "settle", "settles", "linger", "lingers", "hang", "hangs", "hung", "hums", "sits", "sit", "lies", "lie", "looks",
    "look", "curls", "curl", "refuse", "refuses", "dissolve", "dissolves", "rise", "rises", "rose", "remain", "remains",
    "fall", "falls", "fell", "leave", "leaves", "left", "fade", "fades", "breathe", "breathes", "remember", "remembers",
    "break", "breaks", "broke", "bleed", "bleeds", "hear", "hears", "heard", "hold", "holds", "held", "turn", "turns",
    "rest", "rests", "press", "presses", "fill", "fills", "exist", "exists", "wait", "waits", "stop", "stops", "reach",
    "reaches", "cling", "clings", "slip", "slips", "swallow", "swallows", "stand", "stands", "stood", "meet", "meets",
    "read", "reads", "said", "says", "asked", "asks", "used", "uses", "taps", "cuts", "cut", "catches", "catch",
    "caught", "pulls", "pull", "slides", "spins", "watches", "sleeps", "wonder", "wonders", "flickers", "drifts",
    "stretches", "drips", "burns", "glows", "shines", "shone", "feel", "feels", "felt", "seem", "seems", "seemed",
    "come", "comes", "came", "goes", "went", "gone", "become", "becomes", "became", "begin", "begins", "began", "keep",
    "keeps", "kept", "lets", "moves", "needs", "runs", "ran", "sings", "sang", "sinks", "sank", "slows", "shakes",
    "shook", "shows", "take", "takes", "took", "tell", "tells", "told", "think", "thinks", "thought", "tries", "tried",
    "walk", "walks", "walked", "carry", "carries", "carried", "touches", "touched", "whispers", "rustles", "creaks",
    "shimmers", "bend", "bends", "unfold", "unfolds", "gather", "gathers", "scatter", "scatters", "listen", "listens",
    "wake", "wakes", "woke",
))
# nouns (or noun-shaped words) that the suffix shapes below would otherwise drop
_NOUN_EXCEPTIONS = frozenset((
    "ceiling", "morning", "evening", "building", "painting", "string", "spring", "wing", "ring", "king", "darling",
    "sibling", "clothing", "lightning", "pudding", "stocking", "railing", "wedding", "dwelling", "landing", "awning",
    "herring", "offspring", "earring", "feeling", "beginning", "meaning", "ending", "gathering", "drawing", "saying",
    "seed", "weed", "reed", "speed", "creed", "greed", "breed", "feed", "steed", "need", "hundred", "kindred", "shed",
    "sled", "family", "assembly", "belly", "butterfly", "lily", "ally", "jelly", "valley", "reply", "supply", "music",
    "magic", "panic", "topic", "attic", "uncle", "union", "unit", "unity", "universe", "university", "unicorn", "rally",
    "bully", "gully", "folly", "holly", "dolly", "tally", "ivy", "city", "story", "memory", "history",
))
_NOT_NOUN_SUFFIXES = ("ly", "ous", "ful", "less", "ive", "ish", "ic", "ed", "ing")


def _not_noun(w: str) -> bool:
    """True when w must not appear on a nouns-only do-not-repeat list (see the block comment above _NOT_NOUN)."""
    forms = (w, _stem(w))
    if any(f in _NOT_NOUN for f in forms):
        return True
    if any(f in _NOUN_EXCEPTIONS for f in forms):
        return False
    return any(f.endswith(_NOT_NOUN_SUFFIXES) or (f.startswith("un") and len(f) >= 5) for f in forms)


def _prompt_version() -> int:
    """4 = V3 plus the no-"A single" opening line (J-4316, default off); 1 = original, 2 = variety (V2), 3 = V2 without the example list plus the nouns-only list (J-3192, D-0579)."""
    if not NIGHT_VARIETY_ENABLED:
        return 1
    v = int(NIGHT_PROMPT_VERSION)
    return 4 if v >= 4 else (3 if v >= 3 else 2)


def _system_prompt() -> str:
    return {1: SYSTEM_PROMPT_V1, 2: SYSTEM_PROMPT_V2, 3: SYSTEM_PROMPT_V3, 4: SYSTEM_PROMPT_V4}[_prompt_version()]


def _words(text: str, nouns_only: bool = False) -> list[str]:
    out = []
    for w in str(text or "").lower().replace("'", " ").replace("’", " ").split():
        w = "".join(ch for ch in w if ch.isalpha())
        if len(w) >= 4 and w not in _AVOID_STOP and not (nouns_only and _not_noun(w)):
            out.append(w)
    return out


def _stem(w: str) -> str:
    return w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w


def _avoid_images(recent_thoughts, seed: str = "", nouns_only=None) -> list[str]:
    """The do-not-repeat list: image words that recur (document frequency >= AVOID_MIN_DF) across the recent night
    thoughts, most frequent first, at most AVOID_MAX_WORDS. A word that is in the current seed is never listed (the
    thought is asked to form AROUND the seed, so its words must stay free). Pure, deterministic, no model.
    nouns_only (J-3192 / D-0579): None follows the prompt version (on from V3); True drops determiners, adjectives, adverbs
    and verb forms (_not_noun) before counting. The seed's own words are never filtered (they only exclude)."""
    try:
        if nouns_only is None:
            nouns_only = _prompt_version() >= 3
        seed_stems = {_stem(w) for w in _words(seed)}
        df: dict[str, int] = {}
        surface: dict[str, dict[str, int]] = {}
        for t in list(recent_thoughts or [])[-AVOID_RECENT_THOUGHTS:]:
            seen = set()
            for w in _words(t, nouns_only):
                s = _stem(w)
                surface.setdefault(s, {}).setdefault(w, 0)
                surface[s][w] += 1
                if s not in seen:
                    seen.add(s)
                    df[s] = df.get(s, 0) + 1
        ranked = sorted((s for s, n in df.items() if n >= AVOID_MIN_DF and s not in seed_stems), key=lambda s: (-df[s], s))
        return [max(surface[s].items(), key=lambda kv: (kv[1], kv[0]))[0] for s in ranked[:AVOID_MAX_WORDS]]
    except Exception:
        return []


def _recent_logged_thoughts(path, n: int = AVOID_RECENT_THOUGHTS) -> list[str]:
    """Read-only: the last n generated night thoughts from the shadow log's tail (prior sleeps). Fail-open to []."""
    try:
        p = Path(path)
        if not p.exists():
            return []
        with open(p, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - AVOID_TAIL_BYTES))
            raw = fh.read().decode("utf-8", errors="replace")
        out = []
        for line in raw.splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            if isinstance(r, dict) and r.get("kind") == "night_thought" and r.get("generated") and r.get("thought"):
                out.append(str(r["thought"]))
        return out[-n:]
    except Exception:
        return []


def _user_prompt(source: str, seed: str, avoid=None) -> str:
    label = {"replay": "something the day left with you", "dream_tail": "the last image of tonight's dream"}.get(source, "something")
    if avoid:
        return (f"({label}): {seed}\n\nRecent night thoughts kept coming back to: {', '.join(avoid)}. "
                f"Leave those images alone this time and find a different one.\n\nWhat drifts up?")
    return f"({label}): {seed}\n\nWhat drifts up?"


def _median(xs):
    xs = [float(x) for x in xs if x is not None]
    return round(statistics.median(xs), 4) if xs else None


class NightMind:
    """One per sleep. start() inside the running loop; stop() awaits the task, writes the summary row, returns it.

    generate: async callable (system_prompt, user_prompt) -> thought text. The node injects the hot-hub call; tests
    inject a stub. embed: sync callable text -> normalised vector or None (default: the memory store's embedder).
    """

    def __init__(self, generate, sleep_ts: float | None = None, kind: str = "night", replayed=None,
                 embed=None, log_path=None, first_after: float | None = None, floor: float | None = None,
                 max_thoughts: int | None = None, tick: float = 1.0, dreams_fn=None, stages_fn=None, on_thought=None):
        self.generate = generate
        self.sleep_ts = float(sleep_ts if sleep_ts is not None else time.time())
        self.kind = kind
        self.replayed = [str(x) for x in (replayed or []) if x]
        self._embed = embed
        self.log_path = Path(log_path) if log_path else NIGHT_MIND_SHADOW_LOG
        self.first_after = float(NIGHT_FIRST_AFTER_S if first_after is None else first_after)
        self.floor = float(NIGHT_THOUGHT_FLOOR_S if floor is None else floor)
        self.max_thoughts = int(NIGHT_MAX_THOUGHTS if max_thoughts is None else max_thoughts)
        self.tick = float(tick)
        self._dreams_fn = dreams_fn
        self._stages_fn = stages_fn
        self._on_thought = on_thought   # J-2018 (Phase 2): optional sync hook(row)->dict merged into the row; night_dormant.write_night_thought when that flag is on, else None
        self.thoughts: list[dict] = []        # generated rows (with the thought text), kept in memory for the summary only
        self.failed = 0
        self.slots_no_seed = 0
        self.seeds_available = False
        self._slot = 0
        self._last_ts = self.sleep_ts + self.first_after - self.floor
        self._replay_vecs = None
        self._prior_thoughts: list[str] | None = None   # J-2594: prior sleeps' thoughts, read once from the log tail
        self._task: asyncio.Task | None = None
        self._running = False
        self._stopped = False
        self._summary: dict | None = None

    # -- lifecycle ---------------------------------------------------------------------------------
    def set_replayed(self, replayed) -> None:
        try:
            self.replayed = [str(x) for x in (replayed or []) if x]
            self._replay_vecs = None
        except Exception:
            self.replayed = []

    def start(self) -> None:
        if self._task is not None:
            return
        try:
            self._running = True
            self._task = asyncio.get_running_loop().create_task(self._run())
        except Exception as exc:
            self._running = False
            logger.debug("[night_mind] start failed (non-fatal): %s", exc)

    def cancel(self) -> None:
        """Synchronous safety net for a finally block: never leave the task running."""
        self._running = False
        t = self._task
        if t is not None and not t.done():
            try:
                t.cancel()
            except Exception:
                pass

    async def stop(self) -> dict:
        if self._stopped:
            return self._summary or {}
        self._stopped = True
        self._running = False
        t = self._task
        if t is not None:
            try:
                t.cancel()
                await asyncio.gather(t, return_exceptions=True)
            except Exception:
                pass
        try:
            self._summary = await asyncio.to_thread(self._write_summary)
        except Exception as exc:
            logger.debug("[night_mind] summary failed (non-fatal): %s", exc)
            self._summary = self._base_summary()
        return self._summary

    # -- seeds -------------------------------------------------------------------------------------
    def _dream_tail(self) -> str:
        """The night's OWN dream tail, only a dream made during this sleep. A dream from before it is not a seed."""
        try:
            if self._dreams_fn is not None:
                d = self._dreams_fn()
            else:
                from core import night as _night
                d = _night.load_recent_dreams()
            if d and float(d[0].get("ts", 0)) >= self.sleep_ts and (d[0].get("narrative") or "").strip():
                return " ".join((d[0].get("narrative") or "").split())
        except Exception:
            pass
        return ""

    def _pick_seed(self, idx: int):
        """Plan 3.1 order: the replay set, then the dream's tail once a dream exists (alternating once both exist).
        The dormant pick (D-0231) has no code yet: not seeded, reported as not_built."""
        tail = self._dream_tail()
        has_replay = bool(self.replayed)
        if not has_replay and not tail:
            return None
        if tail and (not has_replay or idx % 2 == 1):
            return "dream_tail", tail[-SEED_CHARS:]
        return "replay", self.replayed[(idx if not tail else idx // 2) % len(self.replayed)][:SEED_CHARS]

    # -- embeddings / cosines (worker thread: the embedder holds a lock and can load a model) ------
    def _emb(self, text: str):
        if self._embed is not None:
            return self._embed(text)
        from core.memory.store import _embed
        return _embed(text)

    @staticmethod
    def _cos(a, b) -> float | None:
        try:
            if a is None or b is None:
                return None
            return round(float(sum(float(x) * float(y) for x, y in zip(a, b))), 4)
        except Exception:
            return None

    def _score(self, thought: str) -> dict:
        out = {"cos_replay_max": None, "cos_replay_mean": None, "cos_dormant": None, "embed_ok": False}
        try:
            v = self._emb(thought)
            if v is None:
                return out
            out["embed_ok"] = True
            if self._replay_vecs is None:
                self._replay_vecs = [self._emb(r) for r in self.replayed]
            cs = [c for c in (self._cos(v, rv) for rv in self._replay_vecs) if c is not None]
            if cs:
                out["cos_replay_max"] = round(max(cs), 4)
                out["cos_replay_mean"] = round(sum(cs) / len(cs), 4)
        except Exception as exc:
            logger.debug("[night_mind] scoring failed (non-fatal): %s", exc)
        return out

    # -- the task ----------------------------------------------------------------------------------
    async def _run(self) -> None:
        try:
            while self._running and len(self.thoughts) + self.failed < self.max_thoughts:
                await asyncio.sleep(self.tick)
                now = time.time()
                if now - self._last_ts < self.floor:
                    continue
                self._last_ts = now
                seed = self._pick_seed(self._slot)
                if seed is None:
                    self.slots_no_seed += 1
                    continue
                self.seeds_available = True
                await self._one_thought(now, seed)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.debug("[night_mind] task stopped (non-fatal): %s", exc)

    async def _one_thought(self, now: float, seed) -> None:
        source, snippet = seed
        idx = self._slot
        self._slot += 1
        row = {"ts": round(now, 1), "sleep_ts": round(self.sleep_ts, 1), "kind": "night_thought", "sleep_kind": self.kind,
               "slot": idx, "elapsed_s": round(now - self.sleep_ts, 1), "floor_s": self.floor,
               "seed_source": source, "seed_snippet": snippet[:SEED_CHARS], "seeds_dormant": "not_built",
               "generated": False, "phase": 1}
        avoid = []
        if NIGHT_VARIETY_ENABLED:   # J-2594 / D-0521 A: do-not-repeat list from recent night thoughts (fail-open to none)
            try:
                if self._prior_thoughts is None:
                    self._prior_thoughts = await asyncio.to_thread(_recent_logged_thoughts, self.log_path)
                avoid = _avoid_images(list(self._prior_thoughts or []) + [r["thought"] for r in self.thoughts], snippet)
            except asyncio.CancelledError:
                raise
            except Exception:
                avoid = []
        row["prompt_v"] = _prompt_version()
        row["avoid_images"] = avoid
        t0 = time.perf_counter()
        try:
            text = await asyncio.wait_for(self.generate(_system_prompt(), _user_prompt(source, snippet, avoid)), GEN_TIMEOUT_S)
            text = " ".join(str(text or "").split())
            row["gen_s"] = round(time.perf_counter() - t0, 2)
            if not text:
                raise ValueError("empty thought")
            row["thought"] = text
            row["generated"] = True
            row.update(await asyncio.to_thread(self._score, text))
            self.thoughts.append(row)
            if self._on_thought is not None:   # Phase 2 hook (night_dormant), fail-open: a hook error never costs the thought
                try:
                    extra = await asyncio.to_thread(self._on_thought, dict(row))
                    if isinstance(extra, dict):
                        row.update(extra)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    row["hook_error"] = f"{type(exc).__name__}: {exc}"[:160]
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.failed += 1
            row["gen_s"] = round(time.perf_counter() - t0, 2)
            row["error"] = f"{type(exc).__name__}: {exc}"[:200]
        await asyncio.to_thread(self._append, row)

    # -- writes (shadow log only) ------------------------------------------------------------------
    def _append(self, row: dict) -> bool:
        try:
            from core import profile, shadow_log
            return bool(shadow_log.append(profile.guard_path(self.log_path), row))
        except Exception as exc:     # includes profile.NonLiveWriteError from a non-live importer: refused, swallowed
            logger.debug("[night_mind] shadow row skipped (non-fatal): %s", exc)
            return False

    def _base_summary(self) -> dict:
        return {"ts": round(time.time(), 1), "sleep_ts": round(self.sleep_ts, 1), "kind": "sleep_summary",
                "sleep_kind": self.kind, "phase": 1, "thoughts": len(self.thoughts), "failed": self.failed,
                "slots_no_seed": self.slots_no_seed, "seeds_available": self.seeds_available,
                "replay_n": len(self.replayed), "dormant": "not_built"}

    def _write_summary(self) -> dict:
        s = self._base_summary()
        tail = self._dream_tail()
        s["dream_present"] = bool(tail)
        cos_dream = []
        if tail:
            try:
                dv = self._emb(tail)
                for r in self.thoughts:
                    tv = self._emb(r["thought"])
                    cos_dream.append(self._cos(tv, dv))
            except Exception:
                cos_dream = []
        s["cos_dream"] = cos_dream
        s["cos_dream_median"] = _median(cos_dream)
        s["cos_replay_max_median"] = _median(r.get("cos_replay_max") for r in self.thoughts)
        try:
            st = self._stages_fn() if self._stages_fn is not None else None
            if st is None:
                from core import night as _night
                st = (getattr(_night, "_current", {}) or {}).get("stages", {})
            s["stage_t"] = {k: (v or {}).get("t") for k, v in dict(st).items()}
            s["elapsed_s"] = round(time.time() - self.sleep_ts, 1)
        except Exception:
            pass
        s["hold_dream_engine"] = bool(s["cos_dream_median"] is not None and s["cos_dream_median"] > DREAM_COS_HOLD)
        s["hold_zero_thoughts"] = bool(self.seeds_available and not self.thoughts)
        self._append(s)
        return s


# ----------------------------------------------------------------------------------------------------------------
# the 7-sleep read (the deferred successor job runs this)
# ----------------------------------------------------------------------------------------------------------------
def _read_jsonl(path) -> list[dict]:
    out = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        pass
    except Exception:
        pass
    return out


def evaluate(shadow_rows=None, ledger_rows=None, shadow_path=None, ledger_path=None, baseline_n: int = 14) -> dict:
    """Judge the shadow against the D-0399 defeater over the sleeps that ran the night-mind.

    Duration: median duration_s of the sleeps with a summary vs the median of up to baseline_n ledger rows of the same
    kind BEFORE the first such sleep ("the same regime before"). Passes failing open: proxy = mean number of stages
    the night ledger recorded per sleep, lower than the baseline's means passes were dropped (the node's own
    fail-open handlers swallow the exception, so a missing stage is the visible trace). Read-only."""
    shadow = shadow_rows if shadow_rows is not None else _read_jsonl(shadow_path or NIGHT_MIND_SHADOW_LOG)
    ledger = ledger_rows if ledger_rows is not None else _read_jsonl(ledger_path or (_DATA / "night_log.jsonl"))
    sums = [r for r in shadow if r.get("kind") == "sleep_summary" and r.get("phase") == 1]
    out = {"sleeps": len(sums), "verdict": "insufficient", "holds": [], "notes": []}
    if len(sums) < MIN_SLEEPS_FOR_READ:
        out["notes"].append(f"{len(sums)} of {MIN_SLEEPS_FOR_READ} sleeps with a night-mind summary: not enough to read")
        return out

    def _match(sm):
        best = None
        for L in ledger:
            d = abs(float(L.get("ts", 0)) - float(sm.get("sleep_ts", 0)))
            if d <= 120 and (best is None or d < best[0]):
                best = (d, L)
        return best[1] if best else None

    matched = [(sm, _match(sm)) for sm in sums]
    with_nm = [L for _, L in matched if L]
    first_ts = min(float(s["sleep_ts"]) for s in sums)
    nm_ts = {id(L) for L in with_nm}
    base = [L for L in ledger if float(L.get("ts", 0)) < first_ts - 120 and id(L) not in nm_ts]
    kinds = {sm.get("sleep_kind") for sm in sums}
    base_same = [L for L in base if L.get("kind") in kinds] or base
    base_same = base_same[-baseline_n:]
    d_nm = _median(L.get("duration_s") for L in with_nm)
    d_base = _median(L.get("duration_s") for L in base_same)
    out["duration_median_s"] = {"night_mind": d_nm, "baseline": d_base, "baseline_n": len(base_same)}
    if d_nm and d_base:
        up = d_nm / d_base - 1.0
        out["duration_up_pct"] = round(up * 100, 1)
        if up > DURATION_UP_HOLD:
            out["holds"].append("sleep_duration_up_over_15pct")
    else:
        out["notes"].append("no baseline or no matched ledger rows: duration not judged")
    if with_nm and base_same:
        s_nm = statistics.mean(len(L.get("stages") or {}) for L in with_nm)
        s_b = statistics.mean(len(L.get("stages") or {}) for L in base_same)
        out["stages_per_sleep"] = {"night_mind": round(s_nm, 2), "baseline": round(s_b, 2)}
        if s_nm < s_b - 0.5:
            out["holds"].append("passes_failing_open_more_than_before")
    zero = [sm for sm in sums if sm.get("hold_zero_thoughts")]
    out["sleeps_zero_thoughts_with_seeds"] = len(zero)
    if zero:
        out["holds"].append("zero_thoughts_with_seeds_available")
    meds = [sm.get("cos_dream_median") for sm in sums if sm.get("cos_dream_median") is not None]
    out["cos_dream_median_of_medians"] = _median(meds)
    if meds and _median(meds) > DREAM_COS_HOLD:
        out["holds"].append("median_cosine_to_dream_over_0.6")
    out["thoughts_per_sleep_median"] = _median(sm.get("thoughts", 0) for sm in sums)
    out["verdict"] = "hold" if out["holds"] else "ok"
    return out
