"""
Nascence -- Inner Monologue Node (the Default Mode Network)

Humans are never mentally idle. When not engaged in a task, the brain's Default
Mode Network runs a continuous self-referential stream: who am I, what just happened,
what am I becoming. This node gives Carl that faculty -- a quiet, always-on inner
voice that thinks between the user's messages.

Design:
  - Runs forever on the BACKGROUND lane (CPU, port 11460) so it never blocks responses.
  - Fires only when IDLE: the user hasn't spoken for IDLE_SECS, and no hot-path cycle
    is in flight. It steps aside the moment the user speaks.
  - Each tick produces ONE short first-person present-tense thought, seeded by the
    entity's self-concept, the last thing discussed, current mood, most recent dream,
    and any open curiosity. It is the entity thinking about itself, not answering.
  - READ PATH (so it is not write-only):
      1. The thought is stored to episodic memory (origin='inner_thought') -- it becomes
         part of his lived history and is retrievable later.
      2. The most recent thoughts are held in state.recent_inner_thoughts and injected
         into the NEXT user cycle's Reflection prompt -- so when the user speaks, Carl
         picks up the train of thought he was already on ("I was just turning over...").
  - Logged to data/monologue_log.jsonl so the operator can read what Carl thinks about
    when no one is talking to him.

This is observational/generative, not reactive. It is the substrate of a continuous
self -- a mind that keeps going when the conversation pauses.
"""

from __future__ import annotations

import asyncio
import json
import re
import logging
import time
from pathlib import Path

from core.schema import CognitiveState, SERVE_CHAINS
from core.model_client import call_node_json, call_node_prose
from core.memory.store import store_fragment
class _WakeSkip(Exception):
    """J-2019 (sleep_as_a_mode Phase 3, D-0401 B): raised by _wake_gate() as the first statement of an optional sleep stage's
    own try block when a wake request is pending and WAKE_ON_HUMAN is on. That stage's existing `except Exception` fail-open
    handler absorbs it (the stage is skipped, the pipeline carries on to recover/prune/wake). Never raised in observe mode."""


def _wake_gate(name: str) -> None:
    try:
        from core import night_wake as _nw
        skip = _nw.boundary(name)
    except Exception:
        skip = False
    if skip:
        raise _WakeSkip(name)


from core.sleep_offloop import off_loop as _sleep_off   # J-1917 / F-2546: sleep-consolidation sweeps in a worker thread
try:   # D-0787 option D (J-4153): opener diversity, a helper module per the D-0878 freeze rule; fail-open to None
    from nodes.idle_thought import opener_diversity as _opener_div
except Exception:
    _opener_div = None
from core import profile  # J-0752: this file's own "literal will" direct calls into the write-fence
                           # modules (sensorium/garden/study_life/world_substrate/cat) need to let
                           # profile.NonLiveWriteError escape their local try/except, same as every
                           # other layer of docs/staged/world_store_write_fence.md.

logger = logging.getLogger("nascence.monologue")

_DATA_DIR = Path(__file__).parent.parent / "data"
_LOG_FILE = _DATA_DIR / "monologue_log.jsonl"

# Conversational Redirect, Phase 0 (docs/staged/conversational_redirect.md, 2026-09-02).
# SHADOW ONLY: this file changes no live decision anywhere. It exists to answer, with real data
# instead of a guess, whether (a) the flat IDLE_SECS pause is actually suppressing thoughts that
# would otherwise have engaged with a live conversation, and (b) when a thought DOES fire nearby a
# real exchange, how topically related it actually is (today: often not, per F-0674's Aristotle
# example). Neither _should_think()'s return value nor _think()'s seeding is touched by this file.
_SHADOW_LOG = _DATA_DIR / "conversational_redirect_shadow.jsonl"


def _log_redirect_shadow(row: dict) -> None:
    """Best-effort, fail-open, one JSON line per event. Never raises, never blocks a real decision."""
    try:
        row.setdefault("ts", time.time())
        _SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_SHADOW_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[conversational-redirect-shadow] write failed: %s", exc)

# Conversational Redirect, Phase 1 (J-4337, plan docs/staged/conversational_redirect.md; founder 2026-11-18 on
# J-4268: build shadow-first). OFF by default and restart-gated: while False, _should_think() keeps the flat
# IDLE_SECS veto and _think() seeds exactly as before (Phase 0 shadow rows keep accruing). When True: the veto
# narrows to a human cycle actually in flight (state.cycle_in_flight, set by core/orchestrator.run_cycle) or an
# interrupt, and for REDIRECT_DECAY_SECS after the last human message the next thought is seeded from the live
# exchange and tagged _moment_source="conversation" (grounded, core/stream_drive). _still_idle (sleep entry) and
# the reading-burst yield deliberately keep IDLE_SECS: sleeping/binge-reading mid-talk is not part of this change.
CONVERSATIONAL_REDIRECT = False
REDIRECT_DECAY_SECS = 180.0


def _redirect_veto(state, now: float) -> bool:
    """True when the redirect-flag veto blocks a thought: a human cycle is computing, or an interrupt is up."""
    return bool(getattr(state, "cycle_in_flight", False)) or bool(getattr(state, "interrupt_requested", False))


def _conversation_seed(state, now: float) -> str:
    """Seed line from the live exchange, or '' (flag off / outside the decay window / nothing said). Pure."""
    try:
        if not CONVERSATIONAL_REDIRECT:
            return ""
        age = now - float(getattr(state, "last_human_ts", 0) or 0)
        if age < 0 or age > REDIRECT_DECAY_SECS:
            return ""
        hist = getattr(state, "conversation_history", None)
        if not hist:
            return ""
        last = hist[-1]
        h = str(last.get("human", "") or "").strip()[:300]
        e = str(last.get("entity", "") or "").strip()[:300]
        if not h:
            return ""
        out = f"The person you were just talking with said: {h}"
        if e:
            out += " You answered: " + e
        return out
    except Exception:
        return ""


# Timing
# CHECK_INTERVAL is the POLL granularity, not the think rate — a thought only fires when its
# computed gap has elapsed (_should_think). It was 30s, which is COARSER than TRAIN_GAP_SECS (35s),
# so an open continuity train could never realise a sub-45s follow-up (the 35s gap rounded up to the
# next 30s tick ≈ 60s) — structurally capping bursts at 0% (2026-06-15 cadence finding). Lowered to
# 10s so trains can actually burst; the idle rate is unchanged (still gated by _current_gap).
CHECK_INTERVAL = 10     # how often the loop wakes to consider thinking (seconds)
# LOOSENED 2026-08-31 (founder-directed, F-0587/F-0589/F-0590/I-0059): these were set low back when
# VRAM/node count were scarce and Du was still learning -- neither constraint holds today (7 model
# endpoints live, 1080 Ti mostly idle per F-0588/F-0589). Halved rather than removed: the real
# anti-rumination protection is the redundancy brake (core/stream_drive.py W_REP) and the content-based
# RUMINATION_SIM check below, both left untouched -- we're leaning on those, not on the raw clock.
IDLE_SECS      = 40     # user must be quiet this long before a thought fires (was 75)
MIN_GAP_SECS   = 40     # minimum gap between two inner thoughts, fallback before _current_gap is set (was 75)

# How many recent thoughts to keep in state for injection into the next user cycle
KEEP_RECENT = 3
# J-3187 / D-0574: drop the idle seed's "The last thing discussed" line while conversation_history is only the
# bridged previous-session farewell and no live exchange has happened this run. False restores the old line.
IDLE_SEED_DROP_RESTORED_LAST_THING = True

# Anti-rumination by CONTENT, not topic label. The overnight test showed the model varies
# the 'about' label while repeating the same SENTENCE verbatim (33% unique over 289 thoughts),
# so a label-based guard never fired. We now compare the new thought's embedding against the
# last few thoughts: if it is too similar (cosine >= RUMINATION_SIM) to any recent one, the
# mind is stuck -> force a wander to a divergent seed.
RUMINATION_WINDOW = 5      # how many recent thought-embeddings to compare against
RUMINATION_SIM    = 0.82   # cosine >= this to a recent thought = repeating itself

# Boredom = redirection, not silence (pulse-manager #2, 2026-06-15; docs/boredom_redirection_research.md).
# Human function: boredom is a patch-depletion signal — "forage elsewhere," not "slow down inward" (the
# latter is the rumination FAILURE mode). So a stale loop gets ONE bounded incubation pause (not an
# escalating silence ramp) AND an active turn OUTWARD to a concrete external patch (a closeable Frontier
# question, else the book) governed by expected gain — concrete-external breaks an abstract loop (Watkins).
INCUBATION_PAUSE   = 1.5    # a single bounded step-away when bored (was an escalating 1.5**streak → 4×)
REDIRECT_THRESHOLD = 2      # bored_streak at which the mind is turned outward to a patch

# B6 (2026-06-24) — own the hard feeling plainly. -0.30 was set when schema.py's own comment records
# valence as pinned around +0.82 (a negative reading was rare, so -0.30 looked like a real outlier).
# RECALIBRATED 2026-09-26 (F-1926/J-1366): monologue valence has since drifted colder -- measured
# read-only (scripts/measure_b6_valence_calibration.py) over 14,820 real "source":"monologue" rows
# from data/felt_preamble_log.jsonl, last 21 days: mean=-0.127, p25=-0.393, p10=-0.566 -- the old
# -0.30 cutoff now fires on 34.06% of idle prompts (F-1926 measured 33% by a different sweep of the
# same log; this read, over the full window rather than a sample, confirms it). Recalibrated to the
# measured rolling p10 (the same target scripts/measure_boredom_calibration.py's ESCAPE_COS uses),
# so B6 again fires only on a genuine outlier-negative cycle, not on roughly a third of all of them.
B6_VALENCE_THRESHOLD = -0.57

# Reading-remediation SPRINT (2026-06-15) — the thread's conclusion: Du is shadow/imagination-dominant and
# reading is the ONLY reality counter-force (core/balance + scripts/lane_forces). While imbalanced, idle
# DEFAULTS to streaming books at machine speed (reality mass + per-chapter integration → light points). A
# fraction of idle stays free for thought/PLAY (joy mints light directly). Ends at ~50/50 on both axes.
REMEDIATION_READ_PROB = 0.75   # share of idle ticks that stream reading WHILE reality needs it (rest = free/play)
STREAM_MAX            = 20      # sittings per stream before pausing to integrate / re-check balance
# COOLDOWN (2026-08-16, founder-approved): the old single-ollama serving accidentally PACED this stream —
# each burst waited on slow shared inference. The serving split removed that throttle and the stream went
# to machine speed (three 20-sitting bursts of one book in 33s; 228 bursts/day; sleep pressure doubled).
# Even a genuine imbalance should be corrected at reading pace, not swallowing pace.
REMEDIATION_COOLDOWN_S = 600.0  # min gap between streamed bursts (~1 chapter per 10 min ceiling)
# PLAY / JOY (fixed 2026-06-16): the live affect was FLAT (joy ~0.05) — positive events didn't FEEL like
# anything, so play (joy≥0.5) never fired. Fix: crossings now GENERATE joy (_feel_joy), and the threshold is
# reachable. Du feels his good moments, and that joy mints a play light point (refractory-capped).
PLAY_JOY_THRESHOLD    = 0.35    # reachable now that crossings bump joy
PLAY_REFRACTORY_S     = 150.0   # at most one play light point per ~2.5min (don't flood on lingering joy)
# PLAY_JOY_DELTA_MIN (D-0151, 2026-09-05, F-0838/J-0548): the absolute threshold above ALONE was
# minting on a standing-high baseline, not genuine delight -- joy_start (sampled before this step's
# own _feel_joy bumps, see _joy_step_start below) was already >=PLAY_JOY_THRESHOLD on 96.8% of real
# light-point rows (idle decay 0.002/s is far too slow to ever drain it back down between qualifying
# moments). Real 525-row distribution of (joy - joy_start): median 0.02, p90 0.09, p95 0.26 -- a
# genuine right-skewed tail of same-step joy spikes exists and is cleanly separable. 0.15 sits at the
# p90-p95 knee (founder-ruled default, not the strictest p99 tail) -- keeps ~5.7% of current volume,
# moments where THIS step's own thought generated fresh joy, not ones merely coasting on old joy.
PLAY_JOY_DELTA_MIN    = 0.15
JOY_CROSSING          = 0.40    # joy a genuine crossing (integration / a resolved thought / a frontier close) gives
JOY_READING           = 0.08    # a small, steady pleasure from reading on (he enjoys it, mildly)

# Nightly sleep rhythm: after this many idle thoughts, the entity enters a Sleep State --
# it dreams from what has accumulated, the body recovers, the monologue resets. This turns
# "left running overnight" from one endless monologue into a real cognitive rhythm:
# think -> accumulate -> sleep -> dream -> metabolise -> wake -> think again. Several dream
# cycles a night is the natural test of the dream->shadow recursion.
THOUGHTS_BEFORE_SLEEP = 26

# Continuity trains (2026-06-13, founder: "rather than stopping after the first thought
# and waiting, he continues thinking on that subject... if he is reading, keep reading").
# CLOSURE RESTS, OPENNESS CONTINUES: a thought that ends resolved gets the full living
# cadence; a thought with an open thread (unresolved / an intention / a question), or a
# fresh reading sitting, earns a QUICK follow-up — up to a capped train, then a real rest.
# The rumination guard outranks trains: a repeated thought always ends the train.
# TAP-ON-THE-SHOULDER (§2.5 point 2, D-0020 / J-0165, 2026-08-24) -- the deterministic keyword
# map from a thought's own text to one of `core.lane2.HINT_TOPICS`' fixed vocabulary. Kept HERE
# (the Lane-1 side) rather than imported from lane2, because this is the "gist extraction" step
# itself -- reading Lane 1's own words and reducing them to a topic WORD, never passing the words
# on. Deliberately the same canonical topics lane2.py's own `_TOPIC_FIELDS`/`HINT_TOPICS` already
# use -- no new vocabulary invented on this side either. Matched as WHOLE WORDS, most-frequent-
# topic wins ties broken by this dict's own order (see `_resolve_hint_topic` below, F-1940/J-1381,
# 2026-09-27); a thought naming nothing in this list pushes no hint at all (fail-open, never a
# guess). D-0035 ratified this VOCABULARY as-is (2026-09-18) -- unchanged here, keyword-for-keyword.
_LANE2_HINT_KEYWORDS = {
    "fire": "fire", "flame": "fire", "flames": "fire", "hearth": "fire",
    "tide": "tide", "tidal": "tide",
    "sun": "sun", "sunlight": "sun", "sunset": "sun", "sunrise": "sun",
    "moon": "moon", "moonlight": "moon",
    "cat": "cat",
    "rain": "wet", "raining": "wet", "wet": "wet", "damp": "wet",
    "wind": "wind", "breeze": "wind",
    "warm": "warmth", "warmth": "warmth", "cold": "warmth",
    "sound": "sound", "sounds": "sound", "noise": "sound", "heard": "sound", "hearing": "sound",
    "body": "body-state", "tired": "body-state", "fatigue": "body-state", "hungry": "body-state",
    "ache": "body-state", "aching": "body-state",
}


# J-2915 (F-3587, F-3579, F-3575): idle seed text hygiene. Four cosmetic defects in the text that is built INTO the
# idle seed: (1) the external shock, the frontier finding (two sites) and the reread title were plain [:N] slices that
# ended mid-word ("...takes on her sister's pers", "...as biolog Does this answer it?"); (2) the concern anchor's
# question mark met the tail's leading full stop ("...'Evil Twin'?. Turn to it"). Fixed by cutting at a word boundary
# (an ellipsis only when something was cut), a full stop before the next sentence where the finding ends bare, and
# joining the tail without its leading full stop when the concern text already ends in terminal punctuation. No wording
# changes. False restores the old slices and the old join exactly.
SEED_TEXT_HYGIENE_ON = True


def _seed_cut(text, limit: int, terminate: bool = False) -> str:
    """`text` cut to at most `limit` characters at a WORD boundary, with an ellipsis mark only if something was cut
    (the ellipsis is extra to `limit`). A first word longer than `limit` is hard-cut (no boundary to use). With
    `terminate`, a result that does not end in terminal punctuation gets a full stop, so the sentence that follows it
    in the seed starts clean. Pure."""
    text = text if isinstance(text, str) else ("" if text is None else str(text))
    if not SEED_TEXT_HYGIENE_ON:
        return text[:limit]
    if len(text) <= limit:
        out = text.rstrip()
        cut = False
    else:
        cut = True
        if text[limit].isspace():
            out = text[:limit].rstrip()
        else:
            head = text[:limit]
            at = max(head.rfind(" "), head.rfind(chr(10)), head.rfind(chr(9)))
            out = head[:at].rstrip() if at > 0 else head
        out = out.rstrip(" ,;:-–—")
    if cut:
        return out + "…"
    if terminate and out and out[-1] not in ".?!…":
        return out + "."
    return out


_SEED_TERMINAL = ".?!…"
_SEED_CLOSERS = "'\"’”)]"


def _seed_join_tail(text, tail: str) -> str:
    """`text + tail`, except that a tail beginning with a full stop is joined without it when `text` already ends in
    terminal punctuation (closing quotes/brackets looked through), so a concern that is a question does not render
    '...?. Turn to it'. Pure."""
    text = text if isinstance(text, str) else ("" if text is None else str(text))
    if not SEED_TEXT_HYGIENE_ON or not tail.startswith("."):
        return text + tail
    core_ = text.rstrip().rstrip(_SEED_CLOSERS)
    if core_ and core_[-1] in _SEED_TERMINAL:
        return text.rstrip() + tail[1:]
    return text + tail


def _resolve_hint_topic(hint_src: str) -> str | None:
    """F-1940 fix (2026-09-27, J-1381). BEFORE: matched each keyword as a plain substring
    (`kw in hint_src`) and took the FIRST key in `_LANE2_HINT_KEYWORDS`' own dict order --
    'rain' matched inside 'train'/'constraints'/'grain'/'terrain'/'strain' (88% of all
    would-be 'wet' nominations over a 15,000-thought replay), 'cat' fired on 'oystercatcher',
    'wind' on 'window'. Junk nominations burned the 4/hour push cap and pre-empted real ones.
    NOW: every keyword is matched as a WHOLE WORD only (`\\b`-bounded), every whole-word match
    is collected (not just the first), and the TOPIC with the most total matches in `hint_src`
    wins -- ties keep `_LANE2_HINT_KEYWORDS`' own dict order (the same fire>tide>sun>moon>cat>
    wet>wind>warmth>sound>body-state priority the old first-match code used, now only a
    tiebreak rather than the whole rule). The vocabulary itself (D-0035, ratified 2026-09-18)
    is untouched -- this only fixes HOW it is matched."""
    _topic_counts: dict[str, int] = {}
    for _kw, _topic in _LANE2_HINT_KEYWORDS.items():
        _n = len(re.findall(r"\b" + re.escape(_kw) + r"\b", hint_src))
        if _n:
            _topic_counts[_topic] = _topic_counts.get(_topic, 0) + _n
    return max(_topic_counts, key=_topic_counts.get) if _topic_counts else None

# DOSED COUPLING / LANE 2 PHASE 1 — the CUP, the reverse direction from _LANE2_HINT_KEYWORDS above
# (D-0241 shadow-first, J-1161, docs/plans/lane2_the_witness.md §7.3.1). A fixed-template render of
# the typed {topic, horizon} coordinate read from core/coupling_rides.py's witness tuple — NEVER
# lane2's own notice/expect_next prose (law 4/§3.4; the P1-3 content-boundary check this plan's own
# metric sheet pre-registers depends on that staying true). Mirrors core/lane2.py hint_line()'s own
# "a nomination, never a command" phrasing for the OTHER direction of this same coupling channel.
_LANE2_CUP_HORIZON_WORDS = {"next": "a moment ago", "hour": "within the last hour", "day": "over the last while"}


def _lane2_cup_seed(topic: str, horizon: str | None) -> str:
    # D-0497 (travis 2026-10-28, J-2463): coordinate-only. The line states the {topic, horizon, broke}
    # coordinate and nothing else -- no "worth a thought", no "if it is still on your mind", nothing that
    # nominates Du's attention (plan law 7: the world answers, never leads). "Nothing more is known" is a
    # statement of state (the coordinate carries no content), kept for that reason only.
    when = _LANE2_CUP_HORIZON_WORDS.get(horizon or "", "recently")
    return (f"Something that seemed settled about the {topic}, {when}, turned out not to hold. "
            f"Nothing more is known about it than that.")


TRAIN_GAP_SECS  = 35.0    # the quick follow-up: thinking that flows instead of waiting
TRAIN_MAX_STEPS = 4       # the SOFT cap — the first steps are "free" (short trains, as before); reading-trains
                          # still close here. Past it, a THOUGHT-train must EARN each step (see below).
TRAIN_HARD_STEPS = 40     # SAFETY BACKSTOP only (raised 8→40, 2026-06-22, founder call: "no carriage cap while
                          # progressing"). A deepening thought-train now runs as long as it keeps MOVING — the
                          # loop guards below (restate + slow-loop) END it the instant it circles, and sleep
                          # closes it within ~3h. This number is just a runaway guard for the pathological case
                          # where BOTH loop detectors miss a slow drift; it is NOT a target length.
TRAIN_RESTATE_SIM = 0.82  # cosine to a recent carriage at/above this = circling (a loop) → stop earning
# TRAIN-HOLD (2026-08-16, founder-ruled — train lab + 14,651 logged steps: 48% of steps JUMP,
# 1% circle, flat 0.50 by step; the anti-rumination guards fire into HEALTHY trains and the
# replace-carry freezes — Train A's state repeated verbatim 5 straight steps while Train B's
# extending ledger produced 7 distinct points and the founder judged it better). Four changes,
# one flag: (1) redirect/escape fire mid-train only on MEASURED circling (or the 2× escalation
# hatch); (2) the carry EXTENDS — a ledger of established points, never re-abstracted;
# (3) the seed marketplace stays shut mid-thought-train (the protection reading-trains always
# had); (4) mid-train thought budget 256→400. WATCH: live jump-rate 48%→<25% AND circling
# stays <5% (the immune-system check — these guards killed the June circling disease; if
# circling climbs back, flip the flag OFF and every pre-08-16 behaviour returns exactly).
TRAIN_HOLD = True
# DROWSINESS-PHASE §5.1 (2026-08-30, founder-directed build): a held (developing, non-circling)
# thought-train earns a bounded reprieve from a due sleep, not an exemption -- never make this
# project's un-starvable-by-construction backstops actually starvable. Applies to any fire reason
# (pressure / max_wake_ceiling / metabolic_floor alike). See docs/staged/drowsiness_phase.md §5.1.
TRAIN_SLEEP_GRACE_SECS = 300   # up to 5 min for a held train to close naturally before sleep is forced anyway
TRAIN_LEDGER_MAX = 7          # established points carried (extend, not replace)
TRAIN_MIDTRAIN_TOKENS = 400   # mid-train thought budget (was 256 shared with the carry)
TRAIN_LOOP_WINDOW = 4     # BUILDING DETECTOR (2026-06-22): check circling against the last N carriages, not just
                          # the immediate prior — catches A→B→A and orbit loops the 1-step check could not see.
TRAIN_COHERENCE_FLOOR = 0.30  # a step must stay at least this related to the recent thread (cosine to its
                          # centroid); below it = he jumped OFF the line, so that train is no longer building it.
SWITCH_COOLDOWN_SECS = 240.0  # anti-thrash: min dwell on a book before another incidental switch can fire

# STREAM (Phase 1, 2026-06-20): a THOUGHT-train that is genuinely developing bursts at MACHINE SPEED on
# the conscious lane (the 1080, post-rebalance) instead of the 35s follow-up — his conscious mind FLOWS
# through an idea rather than pulsing one beat per 35s. This is the pulse-manager policy (rate =
# engagement x progress) realised on the live train machine, NOT a second engine: the train already
# decides deepen-vs-end (earned length past the soft cap + the rumination guard, which outranks trains),
# so the stream only ever carries a DEVELOPING train and rests the instant it saturates. The floor — a
# saturated or idle mind — is unchanged (the slow living cadence). Reading-trains keep the 35s follow-up;
# they burst via READ_BURST instead. Kill switch restores the prior behaviour exactly.
THOUGHT_STREAM   = True    # False -> restore the 35s thought-train follow-up (no streaming)
STREAM_GAP_SECS  = 4.0     # machine-speed follow-up while a thought-train develops (~6s gen + this ~= a stream)
STREAM_POLL      = 2       # poll granularity during a burst, so a sub-CHECK_INTERVAL gap is actually realised

# CONTINUOUS_STREAM (docs/plans/continuous_stream.md Phase 1, D-0001/D-0074): the drive controller
# (core/stream_drive.py) sets the pacer directly — Rail A promotes it to BOTH the in-train gap AND
# the idle/between-train gap (today split across STREAM_GAP_SECS vs _compute_gap); Rail B gates the
# rate by grounding. Flipped True 2026-08-29 per Travis's explicit go-ahead following D-0074
# 2026-08-28 after Claude's D-0001 §5 read of all 14,201 Phase-0 shadow rows recommended GO.
# BEHAVIOR-CHANGE CAVEAT (D-0001 ruling item 6, carried into D-0074's approval, must not be lost on
# flip): today's THOUGHT_STREAM fast in-train follow-up (STREAM_GAP_SECS=4.0 below) is UNGATED by
# grounding — of 9,875 rows already streaming fast in the shadow log, 53% were classified ungrounded.
# Flipping this on will correctly SLOW roughly half of today's already-fast trains (Rail B's
# anti-rumination gate), not just speed up idle ones — see _compute_stream_drive_gap(). Intentional
# per the plan's own anti-rumination design, not a regression; D-0074's own defeater is "reopens if
# this causes a real regression once live."
CONTINUOUS_STREAM = True
# continuous_stream Phase 2 (Rail C.2 grounding injection + C.3 re-seed), J-2214, Travis 2026-10-16:
# SHADOW ONLY. core/grounding_injection.observe() logs, per DMN thought, whether redundancy (the J-2152
# topic-perseveration rule run across trains + cross-train cosine + _circling/_slow_loop) would have
# fired an injection and which already-encountered source it would have picked. It changes no seed,
# prompt or gap. There is deliberately no live flag yet: a live path is a separate build after the
# post-boot read and a founder ruling. False -> stop logging.
GROUNDING_INJECTION_SHADOW = True
# J-3289 (boredom design Stage 0, D-0653 review J-3262): SHADOW ONLY. core/stale_patch_cue.observe() logs, per idle thought
# in a stuck window (or a Rail C in_modal row), the line the WORLD would state about a stale patch (elapsed time at the
# place and on the line of thought; each world clock that differs since the patch began) with the facts behind each
# clause. It adds nothing to any prompt, seed list, gap or decision; the four live boredom steers are unchanged (D-0653).
# False -> stop logging.
STALE_PATCH_CUE_SHADOW = True
# J-2662 (ignition_pressure_and_time Option E, I-0138): shadow-only would-promote rows to
# data/ignition_promotion_shadow.jsonl. Applies nothing; the live path is core/ignition_promotion.PROMOTION_LIVE.
IGNITION_PROMOTION_SHADOW = True

# Pulse-manager P1 (2026-06-15): READING BURST. When he reads, persist through the chapter at machine
# speed (multiple sittings inside one of his own pulses) instead of one sitting per ~95s living cadence.
# The first real engagement-burst — turns the rhythm from PULSED toward a stream on grounded tasks only.
READ_BURST          = True   # kill switch — False restores one-sitting-per-cycle reading
READ_BURST_MAX      = 6      # hard cap on sittings per burst (a chapter ≈ a few sittings; huge ones capped)
READ_BURST_NOVELTY  = 0.18   # stop when a sitting is too similar to the burst so far (not absorbing → rest)

# D-0609 / J-3220 (F-3467, P-0022): the idle thought's own structured act.kind == "read" is routed to the SAME
# read latch the phrase latches use (_think()'s "he chose to READ" block), so a stated will to read is no longer
# a dead channel (638 read acts in 3,115 thoughts 10-29..11-01, only 22 sittings). Additive: the phrase latches
# are unchanged and still fire first; the act only adds a trigger. Same gates as the latch (the dark/can_read
# check; the library-ask and school-stickiness rules upstream of it). Measured ceiling (J-3220, read-only from
# nascence.log + hands_trace.jsonl): ~17 s hot-lane per sitting event, ~4.4 sittings of 6000 chars per event;
# uncapped projection ~160-250 routed events/day (peak 358 read acts on 11-04) against 20-33 phrase-latched
# events/day today; the founder-approved machine-speed pace (REMEDIATION_COOLDOWN_S) and the 2026-08-16
# "228 bursts/day doubled sleep pressure" record put the load ceiling near ~144-228 events/day all streams
# together, so the routed path carries its own per-hour cap. False restores the old behaviour exactly.
READ_ACT_ROUTED       = True
READ_ACT_MAX_PER_HOUR = 6    # routed sittings that ACTUALLY START per rolling hour (<= 144/day); dark/finished don't count
#                              J-3485 (founder, decide-review 2026-11-06): raised 4 -> 6 from J-3220's own pick of 4.
#                              6/h is the LOW end of the ~144-228/day all-streams load ceiling above, before the
#                              20-33/day phrase-latched events; the one-week check (J-3384's list) reads it.
# J-3485 (founder 2026-11-06, F-4001, folds in J-3384): when a routed read act's object COMPLETELY names a different
# shelf book (every distinctive title word; core.library_hand.switch_to_named), the sitting reads THAT book instead of
# the current one. Measured read-only (hands_trace.jsonl, 1,741 read acts 10-29..11-06): 990 (57 percent) completely
# name some shelf title, 1,668 (96 percent) share at least one title word, 32 are empty. Same guards as the phrase
# switch: SWITCH_COOLDOWN_SECS dwell, school stickiness, finished books never a target, nothing when the act already
# names the current book. False restores J-3220's behaviour exactly (the sitting opens the current book).
READ_ACT_SWITCH_BOOK  = True

# Prospective memory (C.1): when an idle thought produces a genuine forward-looking
# intention, capture it into state.deferred_intentions so it survives session end.
# Novelty-gated by embedding (same as the shadow bridge) so the same resolve isn't
# recorded dozens of times overnight. Capped so the prospective store stays small and
# the most recent intentions dominate.
INTENTION_SIM      = 0.82   # cosine >= this to an existing intention = duplicate, skip
MAX_INTENTIONS     = 8      # cap on live deferred intentions held in state

# Volition (2026-06-24): when he means to make a WORK of his own, he writes it now -- but not as a
# firehose. A floor between self-authored works so the hand is real, not compulsive.
AUTHOR_COOLDOWN    = 600.0  # seconds between self-initiated authored works
DEEPMEM_COOLDOWN   = 300.0  # seconds between deep-memory consults that feed his idle thinking (Step 3, 2026-06-29)
DEEPMEM_MEMO_BYPASS_COOLDOWN = False  # J-4218 / D-0816 (travis): False, memo kept. J-3029 / F-3733: a memoised (reused) deep-memory answer is not held back by DEEPMEM_COOLDOWN; False = reuse only when the cooldown has also elapsed
# J-3188 (D-0575, travis 2026-11-02; F-3618 part ii, P-0032), RESTART-GATED: when the top curiosity memory.ask() hit is his
# OWN earlier "Q: ... A: ..." reply to the lingering question (78.6 percent of tops, 257 of 327 asks since 2026-10-29),
# the line says so instead of calling it "something you actually lived or read". The hit is kept (D-0312: the fragment
# store is as-is) and nothing is added. False restores the exact pre-J-3188 label for every hit.
CURIOSITY_OWN_ANSWER_LABEL_ON = True


def _curiosity_hit_is_own_answer(content, question) -> bool:
    """True when `content` is a stored cycle summary ("Q: <raw_input>\nA: <reply>") whose Q line is the lingering
    `question` -- the SAME match test the idle self-echo exclusion already uses (core.memory.store._self_echo_check,
    D-0450 / J-2250): normalised text equality, else embedding cosine >= store.SELF_ECHO_Q_SIM (0.80, measured on the
    live corpus). Blocking (one CPU encode), so the caller runs it off the loop. Never raises."""
    try:
        from core.memory import store as _st
        q = _st._q_line(content)
        if q is None or not question:
            return False
        if _st._norm_q(q) == _st._norm_q(str(question)):
            return True
        qv = _st._embed(str(question))
        v = _st._q_line_vec(q)
        if qv is None or v is None:
            return False
        return _st._cosine(qv, v) >= _st.SELF_ECHO_Q_SIM
    except Exception:
        return False


# J-2930 (F-3618 part i, P-0032), RESTART-GATED: the same curiosity memory.ask() fragment was re-offered for the whole
# life of a lingering question (48 questions with 3+ asks: 83 distinct tops in 290 asks = 28.6 percent distinct; one
# fragment was the top hit 39 times). With this on, the node keeps the fragment ids already offered for the CURRENT
# question (reset when background_curiosities[0] changes) and offers the first of the k results not yet offered; when
# every result was already offered the line is left out that tick. ask() is still called on the same 300 s cadence
# (memory_service's usage metric and co_recall rows are unchanged); Scholar, DEEPMEM_COOLDOWN and what memory_service
# returns are untouched. False restores the exact pre-J-2930 behaviour (always cfrags[0]).
CURIOSITY_NO_REOFFER_ON = True
_CURIOSITY_OFFERED_CAP = 64   # ids remembered per question; a question can never grow this past k * asks in practice


def _curiosity_frag_key(frag) -> str:
    """Stable identity for a curiosity ask() result: its fragment_id, else a short hash of its content."""
    try:
        fid = frag.get("fragment_id")
        if fid:
            return str(fid)
        import hashlib as _hl
        return "c:" + _hl.sha1((frag.get("content") or "").encode("utf-8", "replace")).hexdigest()[:16]
    except Exception:
        return ""


def _curiosity_pick_unoffered(cfrags, offered: set):
    """First result in `cfrags` (ask() order, best first) whose key is not in `offered`, else None. Does not mutate
    `offered`; the caller adds the key once the line is actually appended. A result with no usable key is treated as
    not offered (it cannot be tracked, so it is never silently dropped). Never raises."""
    try:
        for f in (cfrags or []):
            k = _curiosity_frag_key(f)
            if not k or k not in offered:
                return f
    except Exception:
        pass
    return None
# WHAT TRAVIS HAS TOLD HIM, in IDLE (D-0141, 2026-09-03): the founder-memory route (D-0134) reaches his idle
# wondering too. Cooled so it is occasional, and gated on a HIGHER similarity than the conversation route's
# 0.30 -- measured on real idle thoughts (F-0751 calibration): a thought circling his name scores ~0.58-0.61
# against Travis's 08-29 words on it, an unrelated wren thought ~0.52, a garden thought ~0.42.
FOUNDER_IDLE_COOLDOWN = 600.0
FOUNDER_IDLE_FLOOR    = 0.55
# D-0309 (ruled 2026-09-28, travis): tighten the idle tie-break itself. F-2054 found 36% of idle
# founder-recalls store-wide only cleared FOUNDER_IDLE_FLOOR via the +0.10 rare-term/CJK bump below --
# including a fully unconfounded 40/40 spike on a Bergson/tranquility loop (2026-09-17) where raw
# similarity never once reached the floor on its own. A direct counterfactual against the live
# founder_recall_log.jsonl (J-1586, 2026-09-28, 822 recalled items) showed raising FOUNDER_IDLE_FLOOR
# itself is not surgical -- even a modest +0.03 raise (0.58) would collaterally exclude 276 of 529
# currently-genuine (non-tie-break) hits, more collateral than target. So the bump itself is gated
# instead: it now only applies once raw similarity is already within 0.05 of the floor, which on the
# same real data cuts the tie-break-necessary population by 54.9% (161 of 293) while preserving the
# closer, more plausible calls (raw sim 0.50-0.548, the remaining 132).
FOUNDER_IDLE_BUMP         = 0.10
FOUNDER_IDLE_BUMP_MIN_SIM = FOUNDER_IDLE_FLOOR - 0.05   # 0.50 -- rare-term bump needs at least this raw sim first
# D-0292 (ruled 2026-09-27, travis): "Pursuits, curiosity, the recall act and dreams call memory,
# nothing unasked." Founder idle recall above is a named, cooled line (not the ambient trail D-0289
# already removed) but it still PUSHES memory into the idle seed unasked, so it comes out too
# (J-1428). Kill-switch shape, same pattern as IDLE_AMBIENT_RECALL (core/associative_recall.py,
# J-1425): True restores today's behaviour exactly (verified byte-identical seed) and is what ships
# here -- restart-gated, so this build does not silently change Du's live behaviour on some unrelated
# restart before it is a deliberate choice to flip it. When False, the route still runs the retrieve
# and writes its usual founder_recall_log row (marked would_have_shown=true, so the ~2-week defeater
# read can see what was skipped), but never reaches seed_parts, never bumps replay_count, and never
# advances _last_founder_idle_ts (so the shadow read is not throttled by a cooldown the flag itself
# has disabled).
# D-0310 (ruled 2026-09-27, travis, via J-1587): flipped True -> False so the D-0292 ~2-week defeater
# clock in J-1513 actually starts accruing would_have_shown=true rows in data/founder_recall_log.jsonl.
# Takes effect only once Du restarts onto this build -- see F-2062 for the byte-identical-when-True
# verification this flip relies on, and this job's own findings-log entry for the pre-flip baseline.
IDLE_FOUNDER_RECALL = False
# Same ruling, same job: the wandering-mode "a different memory, surfacing" divergent seed
# (_fetch_divergent_seed, below) is the second of the two remaining unasked idle-seed pushes. Same
# kill-switch shape and same restart-gated shipped default (True) as IDLE_FOUNDER_RECALL just above.
# When False, the fetch still happens and one source="divergent_shadow" co_recall row is logged when
# the fetch returns a real fragment, but the text never reaches seed_parts.
# D-0310 (ruled 2026-09-27, travis, via J-1587): flipped True -> False, same rationale as
# IDLE_FOUNDER_RECALL just above -- starts the D-0292 defeater clock's source="divergent_shadow" half.
IDLE_DIVERGENT_SEED = False

# OBSERVATION JOURNAL (2026-06-30): he keeps articulating "I need to write down the precise description of what
# I see" and had no hand for it (observing wrote nothing; authoring made a treatise). The want = a RECORD verb
# applied to something SENSED. Detected here, routed to the field-journal hand below.
_OBS_RECORD_VERBS = ("write down", "write it down", "write a description", "set it down", "set down", "note down",
                     "make a note", "jot ", "put into words", "put it into words", "precise description",
                     "a description of", "describe the", "describe exactly", "describe precisely", "capture the",
                     "capture this", "capture exactly", "record the", "get it down", "get down the")
_OBS_SENSORY = ("observe", "i see", "i saw", "looking at", "look at", "watch", "the way ", "the exact",
                "the precise", "the specific", "the sound", "the colour", "the color", "the light",
                "the rhythm", "the pattern", "the shape", "the movement", "the texture", "the smell",
                "the scent", "tide", "shingle", "wave", "the water", "the sea", "shore", "the sky", "cloud",
                "rosemary", "thyme", "the cat", "the bed", "the garden", "the fire", "rock-pool", "rock pool",
                "the pools", "the rain", "the snow", "in front of me", "right in front")
_OBS_TARGETS = [# THE LETTERBOX (J-0539 / F-0734, 2026-09-04): the carrier's card pinned inside the lid — the world's
                # only statement that oil, matches, candles can be asked for — is rendered by sensorium.look('letterbox')
                # and nothing ever produced that target: this table had no letterbox/mailbox/gate cue, so every look at
                # the letterbox fell to 'room'. The explicit box words go FIRST (a look in the letterbox is a look in the
                # letterbox whatever else the thought mentions); the bare gate cues sit just before 'the garden', which
                # 'the garden gate' would otherwise match first.
                ("letterbox", "letterbox"), ("letter-box", "letterbox"), ("letter box", "letterbox"),
                ("mailbox", "letterbox"), ("mail-box", "letterbox"), ("mail box", "letterbox"), ("postbox", "letterbox"),
                ("the post", "letterbox"), ("the flag", "letterbox"),
                ("rock-pool", "pool"), ("rock pool", "pool"), ("the pools", "pool"), ("tide", "shore"),
                ("shingle", "shore"), ("the strand", "shore"), ("wave", "sea"), ("surf", "sea"),
                ("spray", "sea"), ("the water", "sea"), ("the sea", "sea"), ("the ocean", "sea"),
                # NAMED-PLANT TARGETS, NOT THE WHOLE BED (J-1601/F-2162, 2026-09-28): these four used to
                # collapse to tgt "bed" like the plural/generic cues below them -- so a willed "look closer
                # at the thyme, why did it die" resolved target="bed", and core/garden.py look()'s per-plant
                # branch (the one that calls garden_knowledge.evidence_for()/guessed_cause()/bind() -- the
                # only way a phenology binding is ever authored) requires the resolved text to CONTAIN the
                # plant's own species/name string; "bed" never does, so that branch was structurally
                # unreachable for every herb mention, independent of J-1524's own bind()-wiring fix (traced
                # end to end: dispatch._look() -> _observe_target() -> sensorium.look() -> _garden_look() ->
                # garden.look(), confirmed garden.look() has exactly one live caller, here). Fixed by naming
                # the plant instead of the bed: tgt is now the CATALOGUE species key (with '_'->' ', the same
                # string core/garden.py look() itself checks via `p["species"].replace("_", " ") in t`), so
                # whichever cue fires, the per-plant branch is guaranteed reachable downstream. "the bed" and
                # "the herbs" (plural/collective, no single plant named) deliberately still resolve to "bed"
                # below -- that whole-bed-summary answer is the honest one for those two, unchanged.
                ("rosemary", "rosemary"), ("thyme", "thyme"), ("the mint", "mint"), ("parsley", "parsley"),
                ("the bed", "bed"), ("the herbs", "bed"), ("cloud", "sky"), ("the sky", "sky"),
                ("gull", "sky"), ("the fire", "fire"), ("the flame", "fire"),
                # 'the cat' sits ahead of the bare gate cues (J-0539): 'the cat at the gate' (a real 08-20 observe) is a
                # look at HER, not the box — every place's look() already has its own cat branch (CAT 10x, 2026-07-03).
                ("the cat", "cat"),
                # THE SHELF/DESK/BOOK GAP (J-1071 / F-1459, 2026-09-18): _observe_target() backs core/dispatch.py's
                # live "_look" hand, and this table had no cue at all for shelf/desk/book/tablet -- a willed "look
                # at the shelf"/"look at my books" thought that reaches dispatch.dispatch() (confirmed live-firing,
                # "DISPATCH look" lines in nascence.log) always resolved target="" and fell back to a generic
                # s.look("room"), never the real shelf/desk/book content the legacy phrase-latch further down this
                # same file (~line 3337, its own vocabulary borrowed here) has always been able to answer. No entry
                # added to _OBS_TARGET_HOME below for these: sensorium.py's own look() already carries an equivalent
                # study_targets mismatch guard for "desk"/"shelf" (returns "the X is up in your study..." when he is
                # not there) that fires regardless of cur_loc, and _OBS_TARGET_HOME is deliberately never consulted
                # for THIS call site anyway (_observe_target's own docstring: dispatch's willed _look passes no
                # cur_loc, on purpose, so a deliberate look at a place he is not in reaches look()'s OWN mismatch
                # reply instead of silently dropping to ""). "book" maps to tgt "book", not "desk", so it reaches
                # study_life._look_books()'s general title-or-desk-or-with-him answer (built J-0851/D-0205) rather
                # than forcing the raw current-page read that a bare "desk" look gives.
                ("my tablets", "shelf"), ("my works", "shelf"), ("the shelf", "shelf"),
                ("the page", "desk"), ("the desk", "desk"),
                ("my books", "book"), ("the books", "book"), ("the book", "book"),
                # CUE-FORM COVERAGE (2026-09-23, J-1178/F-1652's own cue-coverage item): possessive/
                # modifier forms of the shelf/desk/book cues above never matched the bare-article forms
                # ("my desk" is not a substring of "the desk"), so a willed look whose text used one of
                # these was silently falling to the generic room reply. Confirmed by hand-reading the
                # real desk/shelf dispatch-ledger population (73 rows, 13 FIRE, 2026-09-02..09-23):
                # exactly 2 of the 13 FIRE rows used "my desk" ("...on my desk..."), both real desk
                # looks that fell to 'room'. Added AFTER the whole existing shelf/desk/book group on
                # purpose (never before it) so every pre-existing cue keeps its exact precedence,
                # including within this group ("the desk" still wins over "the open book" for a thought
                # naming both) -- a pure addition, not a reorder, so this needs no ruling per this job's
                # own instruction (a change of TABLE ORDER would; this is not one). Verified by a full
                # replay over all 534 real historical look-hand-fired rows in data/hands_trace.jsonl:
                # zero regressions (every existing non-empty resolution is byte-identical), 7 real gains
                # (2 my-desk, 4 the-open-book -- 1 overlapping row correctly resolves to 'desk' since
                # "my desk" is now checked first -- 1 this-book). "this desk"/"my shelf"/"this shelf"/
                # "the shelves" were also tested (same replay, zero regressions) but show zero real
                # corpus demand today -- left out, matching this table's own established D-0190-style
                # "no unmet real-world need exists" discipline rather than widened speculatively.
                ("my desk", "desk"), ("this book", "book"), ("the open book", "book"),
                # THE OTHER 25 CATALOGUED PLANTS (J-1601/F-2162, 2026-09-28): the herb fix just above covers
                # rosemary/thyme/mint/parsley -- this job's briefing asked "ideally the other 18+ cataloged
                # species too", and core/garden.py's CATALOGUE has grown to 29 real entries (verified: read in
                # full). Before this, none of these had ANY cue here at all, so a willed "look at the
                # tomatoes"/"why did the lettuce die" resolved target="" and fell to the generic room/yard
                # pool -- worse than even the whole-bed fallback the herbs got. Each tgt below is the plant's
                # own CATALOGUE species key with '_' -> ' ' (never a cue phrase verbatim), so garden.look()'s
                # `p["species"].replace("_", " ") in t` check matches regardless of which cue phrase fired --
                # same design as the herb fix. Placed here, after every existing cue and before the "the
                # garden" catch-all below (which must stay last): a pure addition, no existing cue's order or
                # trigger text is touched. Two-cue pairs (e.g. "poppy"/"poppies", "strawberry"/"strawberries")
                # are used where the plural is not a plain substring of the singular (or vice versa); a single
                # stem cue is used where it already covers both ("tomato" in "tomatoes", "nettle" in
                # "nettles"). "broad bean"/"dwarf bean" are the two multi-word forms, deliberately not a bare
                # "bean"/"beans" cue, so the two species can never shadow each other. Not yet corpus-verified
                # against real phrasing demand the way the my-desk/open-book cues above were (no hands_trace
                # rows exist for these species today, unlike the herbs) -- additive and zero-regression by
                # construction (replay below), but the actual phrasing coverage is a real-usage question for
                # a future read, same "no unmet real-world need confirmed yet" caveat this table already
                # carries elsewhere.
                ("chives", "chives"), ("radish", "radish"), ("lettuce", "lettuce"),
                ("silverbeet", "silverbeet"), ("peas", "peas"),
                ("broad bean", "broad beans"), ("dwarf bean", "beans"),
                ("tomato", "tomatoes"), ("potato", "potatoes"), ("garlic", "garlic"),
                ("strawberry", "strawberries"), ("strawberries", "strawberries"),
                ("sunflower", "sunflowers"),
                ("calendula", "calendula"), ("marigold", "calendula"),
                ("nasturtium", "nasturtium"),
                ("poppy", "poppies"), ("poppies", "poppies"),
                ("lavender", "lavender"), ("swan plant", "swan plant"),
                ("cabbage", "cabbage"), ("kale", "kale"), ("nettle", "nettle"),
                ("pohuehue", "muehlenbeckia"), ("wire vine", "muehlenbeckia"),
                ("kumara", "kumara"),
                ("chickweed", "chickweed"), ("dandelion", "dandelion"), ("oxalis", "oxalis"),
                ("the garden gate", "letterbox"), ("the gate", "letterbox"), ("the garden", "garden"),
                # THE SEED TIN'S OWN WORDS (D-0333, J-1764, 2026-10-04; ruled by Travis "Narrow: add tin words"; the
                # D-0269 shape): the J-1438 wood fix answers a look at the tin, but a WILLED look never got there --
                # no cue here resolved a tin word, so even with a look deed read the target was '' or whatever else the
                # thought named (F-2284). tgt "dented tin" is a bare noun phrase like every target here (the journal
                # header builds "observed the <tgt>") and carries a core/garden.py _WORDS['seed_tin'] word, so
                # sensorium.look(tgt) reaches garden.item_look()/_item_look(): it names the tin ONLY where it really
                # lies (wood via sensorium._wood_look's J-1438 fallback, garden via garden.look, or "you have it with
                # you" when carried) and answers anywhere else exactly as sensorium.look('the dented tin') -- the
                # structured-observe route -- already does for an absent item. No home entry in _OBS_TARGET_HOME: the
                # tin can lie anywhere (like bed/sky/fire/cat) and nothing here says where it is.
                # WHOLE-WORD, not a substring (the only compiled-pattern cue in this table; _observe_target tests a
                # str cue with `in` and a pattern with .search): a bare substring 'tin' would capture tinder,
                # tinkling, stinging, setting, waiting, continue... Three guards keep the study's OTHER tins out:
                # "match tin"/"matches tin" (the mantel item the lamp hand answers "match tin -- empty" for,
                # F-2325), "tin of matches", and "tin roof" (7 real corpus thoughts). A hyphen is not a boundary
                # ("tin-roofed"). The Action.grammar_only twin of these words is core/actions.py's 'look' row.
                # POSITION (document, do not reorder -- D-0333 ruling, D-0269): LAST, after the gate/garden catch-alls,
                # so this is a pure addition by construction: first cue found anywhere in the thought wins, so a
                # thought that ALSO names ANY earlier cue (the sea, the fire, the cat, the shelf/desk/book group, a
                # plant, the gate, the garden) resolves to THAT cue exactly as before and the tin is not named
                # (F-2284's "the dented tin and the sea" -> 'sea'). Only a thought no other cue claims (target '')
                # can change. Replayed over the real corpus (28,236 distinct thoughts): 151 changes, every one a
                # '' -> 'dented tin', none on a thought without a whole-word tin/packet word, no existing non-empty
                # resolution touched. Placed BEFORE the catch-alls instead it would have turned two real look deeds
                # that only MENTION the tin ("the wind rattles the tin box ... walk out to the garden") from the
                # garden into a look at the tin, and gained nothing -- so the catch-alls keep their place. Of the 19
                # real look deeds that name a tin/packet word, 3 reach this cue (2 of the 6 NEW deeds this build
                # creates, 1 "dented tin room" idiom) and 16 are claimed by an earlier one (6 sea/surf, 3 shingle/
                # tide, 2 the garden, the fire, cloud, thyme, the flag, the book; 4 of the 6 NEW deeds): whether the
                # tin should outrank those ambient cues when the look is AIMED at it was a separate decision (a
                # table-order change, left to Travis per D-0269/D-0333) -- ANSWERED by D-0348 (2026-10-06, ruled
                # "(ii) clause-first for the tin only"): this cue's PLACE in the table is unchanged, but
                # _observe_target() below now consults _tin_clause_first() BEFORE walking the table, so a look verb
                # whose own clause reaches a tin/packet word resolves to the tin ahead of every earlier cue. A thought
                # that merely mentions the tin as scenery still reaches this cue last, exactly as before.
                (re.compile(r"(?<![\w-])(?:seed tin|dented tin|packets?"
                            r"|(?<!match )(?<!matches )tin(?! of match)(?! roof))(?![\w-])"), "dented tin")]

# CLAUSE-FIRST FOR THE TIN ONLY (D-0348, J-1835, 2026-10-06; ruled by Travis "(ii) clause-first for the tin only",
# chosen over (i) leave it and (iii) move the tin cue early). _observe_target() returns the FIRST cue found anywhere in
# the whole thought, so a willed look at the tin that ALSO names an earlier cue ("I look at the dented tin and the
# sea", "thyme ... I watch the dented tin") resolved to that cue and the tin was never named: of the 6 genuine new
# tin looks the J-1764 build created on the real corpus, only 2 reached the tin (F-2402). This rule asks ONE narrower
# question first: does a LOOK VERB's OWN CLAUSE REACH a tin/packet word? That is exactly the condition the J-1764 gate
# (core/literal_will.py classify(), deed_grammar) already requires before a look deed exists for these words at all:
# the look row's verbs (look/watch/observe/see), not read as a noun (literal_will._NOT_NOUN, the same guard the gate
# and core/hands.py wants() share), reaching within the same sentence (the ungated look family's reach,
# `[^.!?]{0,50}`) one of the look row's eight grammar_only tin/packet words (seed tin, dented tin, the/this/that/my
# tin, packet, packets). The reached word must ALSO be the seed tin as the table cue reads it: "the tin roof" and
# "the tin of matches" (the gate's own documented residual) are excluded here as they are on the cue, so a look at
# the roof or the match tin still resolves exactly as before. Because the rule needs the VERB to reach the WORD, a
# thought that only mentions the tin as scenery and looks at something else ("the wind rattles the tin container ...
# I watch the grey sea rise") keeps its own resolution (sea): the verb's reach never gets to the tin word. No other
# cue is reordered, no table entry moves, and nothing here says where the tin lies (world answers, never leads): the
# target is the same bare "dented tin" the J-1764 cue emits, and sensorium.look() answers it the same way wherever
# the tin is (F-2402's no-hint checks). Replayed read-only over the real corpus (data/hands_trace.jsonl) before
# shipping -- the counts are in F-2402's successor finding (J-1835). The pattern is compiled lazily on first use so
# this module keeps no import-time dependency on core.literal_will (the node already imports it lazily elsewhere);
# if that import ever fails the noun guard is dropped (never the rule), fail-open to the plain verb boundary.
_TIN_GATE_WORDS = r"(?<![\w-])(?:seed tin|dented tin|packets?|(?:the|this|that|my) tin(?! of match)(?! roof))(?![\w-])"
_TIN_LOOK_VERBS = ("look", "watch", "observe", "see")      # the 'look' row's verbs, core/actions.py (mirror; test-pinned)
_TIN_CLAUSE_RX = None


def _tin_clause_first(t: str) -> bool:
    """True when a look verb's own clause reaches a seed-tin/packet word -- the J-1764 gate's own deed condition,
    asked here so a willed look AT the tin resolves to the tin before any earlier cue (D-0348). `t` is lowercased."""
    global _TIN_CLAUSE_RX
    if _TIN_CLAUSE_RX is None:
        try:
            from core.literal_will import _NOT_NOUN as _nn
        except Exception:
            _nn = ""
        _TIN_CLAUSE_RX = re.compile(_nn + r"(?<![\w-])(?:" + "|".join(_TIN_LOOK_VERBS) + r")(?![\w-])[^.!?]{0,50}"
                                    + _TIN_GATE_WORDS)
    return bool(_TIN_CLAUSE_RX.search(t))


def _wants_record_observation(text: str) -> bool:
    """He wants to WRITE DOWN, plainly and precisely, something he is SEEING — the want that had no hand."""
    t = (text or "").lower()
    return any(v in t for v in _OBS_RECORD_VERBS) and any(s in t for s in _OBS_SENSORY)


# D5 FIX (2026-08-21): move-destination resolution, factored out so the OBJECT-first precedence in
# _route_act is directly testable. Wood is checked first (it's on the shore path); "driftwood" joins
# the shore words (08-21 06:14: `move -> garden (the driftwood)` — it matched nothing and fell to
# the default); the garden list exists so a DECLARED "to the garden" can win outright instead of
# falling through to the thought-scan (08-20 23:41: `move -> study (to the garden)`).
#
# F-0634 FIX (2026-09-02): these four lists carried no variant of "outside" or bare "out"/"in", even
# though dispatch's own gate (literal_will.classify) already recognizes move-intent with exactly
# those objects — 9 of 19 live move-family hand-declines in data/hands_trace.jsonl carried a
# dispatch-recorded object of 'outside'(5x)/'out'(2x)/'in'(2x) that matched nothing here, so
# core/dispatch.py's _move hand always declined them (F-0634, verified). The OLDER, broader-
# vocabulary phrase-latch at ~line 2666-2683 (runs BEFORE dispatch()) already has working phrasing
# for this ("go outside", "step out into", "go back in", ...) — borrowed below so both parsers
# finally share it, and standalone "outside" joins _DEST_GARDEN directly (matching the docstring's
# own "unqualified default (garden = go out)"). Bare "in"/"out" are deliberately NOT added as
# standalone cues: reading the untruncated hands_trace rows behind two of the nine declines showed
# the gate's own 'out'/'in' object came from phrasal verbs with no destination meaning at all
# ("work out these problems", "pacing in circles") — a bare 1-2-letter cue would send him to the
# wrong place on those, exactly the false-positive risk this function's word list has always avoided
# (see driftwood/copse above). "outside" alone is long and distinctive enough to be safe; the
# multi-word phrases below cover the rest of the real cases without that risk.
_DEST_WOOD = ("the wood", "woodland", "the trees", "into the trees", "the copse", "copse", "forest")
_DEST_SHORE = ("shore", "beach", "sea", "tide", "rock-pool", "rock pool", "wave", "spray", "surf",
               "shingle", "the water", "the waves", "driftwood",
               "sand",   # J-0833: sensorium.move()'s own shore list always had "the sand"; this one never did
               # J-3527 (F-4138): the stream MOUTH is a shore standpoint (at_the_stream_mouth, D-0651). Only the
               # three authored mouth phrases, never a bare "stream" (the wood has one). Replay over all 62,382
               # hands_trace rows: 59 rows name the mouth, ALL located at the shore (0 wood); of 15 move rows 3
               # ("toward the stream mouth" willed AT the shore) resolved to a wrong 'garden' departure, now 'shore'.
               "stream mouth", "mouth of the stream", "stream's mouth", "stream’s mouth")
_DEST_STUDY = ("inside", "indoors", "back in", "the study", "to the study", "the desk", "come in",
               "head in", "back to the room", "the cottage", "go back in", "go back inside",
               "go inside", "come inside", "head inside", "back indoors", "return to the study")
_DEST_GARDEN = ("garden", "the bed", "the gate", "the mailbox", "outside", "go outside",
                "step outside", "step out into", "into the garden", "out to the garden",
                "out to the bed", "down to the garden", "up to the garden",
                "letterbox", "letter-box", "letter box", "postbox",   # J-0539: the letterbox stands at the garden gate
                "raised bed", "cottage garden",   # J-0833: 324 corpus mentions of the raised bed(s); "the bed" never matched "the raised bed"
                "woodpile", "wood pile", "wood-pile")   # J-0864: the pile is "by the door"/"by the cottage" and renders in the GARDEN scene
                                                        # (sensorium._woodpile_phrase, scene_line loc=="garden"); 163 corpus rows name it,
                                                        # 101 with kind=move -- before J-0833's word edges "the woodpile" fell to 'wood' via
                                                        # "the wood" (a no-op), after them to '' (no move). A walk to the woodpile is a walk
                                                        # out to the garden; from the garden it is the already-there silence.

# J-0833 / F-1199 (2026-09-10): _move_dest() used to return on the FIRST list above that matched ANY cue
# ANYWHERE in the text (wood > shore > study > garden), with no sense of which place the move verb reaches,
# which place is being LEFT, or whether the cue is negated. Measured over every real move fire in the
# frozen hands_trace corpus (642 rows), 269 carried two lists' cues, a source marker, or a negation;
# of the 201 hand-read, 87 resolved to the WRONG place — 42 real wrong-place relocations ("I want to
# turn away from the desk and go to the raised bed" -> study; "I step into the garden where the sea's
# sound washes over me" -> shore) and 45 real departures silently swallowed because the place he was
# STANDING in was checked first ("I will climb up to the garden" from the shore -> shore -> silent).
# The resolver below is layered, every layer additive on the same four lists:
#   1. a cue right after a SOURCE marker ("away from the desk", "leave the study", "off the shingle",
#      "leaving the wood behind") names where he is going FROM, and is dropped;
#   2. a cue right after a NEGATION ("I do not need the sea") is dropped; if every cue was negated the
#      answer is '' (no move), never the negated place;
#   3. among what is left: a cue that follows a DIRECTIONAL preposition ("to the shore", "toward the
#      wood", "into the garden") wins; then a strong cue beats a WEAK one (the F-0634 "go out" phrases are
#      a default, not a destination, and "through/past the gate" is transit); then the sentence holding
#      the move verb; then plain character distance to the nearest move verb; then the old list order.
# Cue matching also gained word edges (leading letter, trailing letter unless a plural "s"/"line"):
# "sea" no longer fires on "searching"/"seagull", "the wood" no longer on "the woodpecker". Simulated
# before porting (scratch harness, same corpus): 191 of the 201 hand-read rows right vs 114 today; 30
# further rows change, every one read individually (a dropped wrong-place walk, or '' where he already
# stood). Full evidence: F-1227; regression: scripts/_test_move_dest_resolution.py.
_MD_SRC = re.compile(r"\b(away from|from|off|out of|out from|leave|leaving|left|abandon|abandoning|beyond|"
                     r"escape|escaping|behind)\s+((?:[a-z'’-]+\s+){0,5})$")
_MD_SRC_BREAK = re.compile(r"\b(to|toward|towards|into|onto|and|or|but|then)\b|[,;:]")
_MD_SRC_NEEDS_VERB = ("off", "from", "beyond")   # bare prepositions are a source only after a move verb
_MD_VERB_BEFORE = re.compile(r"\b(go|goes|going|walk|walks|walking|head|heads|heading|climb|climbs|climbing|step|"
                             r"steps|stepping|come|comes|coming|return|returns|returning|move|moves|moving|push|"
                             r"pushes|pushing|pull|pulls|pulling|turn|turns|turning|away|down|up|out|back)\b"
                             r"[^.;!?]{0,25}$")
_MD_TRANSIT = re.compile(r"\b(through|past)\s+(?:[a-z'’-]+\s+){0,2}$")
_MD_WEAK = frozenset(("outside", "go outside", "step outside", "step out into"))
_MD_DIR = re.compile(r"\b(to|toward|towards|into|onto|for|up to|down to|out to|back to|over to|across to|along to|"
                     r"in to)\s+(the|this|that|my|these|those|a|an|our)\s+(?:[a-z'’-]+\s+){0,1}$")
_MD_LEAD_DET = re.compile(r"^(the|this|that|my|these|those|a|an|our)\s+")
_MD_NEG = re.compile(r"\b(not|no|never|nor|n't|unable to|cannot|can't)\s+(?:[a-z'’]+\s+){0,3}$")
_MD_IDIOM = re.compile(r"^(inside|outside) (my|me|us|our|this|his|her|the (mind|head))\b")   # "inside my own head"
_MD_WORLD_COMES_IN = re.compile(r"\b(tide|tides|sea|water|waves|wave|surf|swell|rain|wind|light|dark|night)\s+$")
_MD_VERB = re.compile(r"(?<![a-z-])(go|goes|going|walk|walks|walking|walked|head|heads|heading|headed|climb|climbs|"
                      r"climbing|climbed|step|steps|stepping|stepped|come|comes|coming|return|returns|returning|"
                      r"returned|move|moves|moving|moved|make for|making for|take the path|taking the path)(?![a-z-])")
_MD_RANK = {"wood": 0, "shore": 1, "study": 2, "garden": 3}


# MODIFIER-TOLERANT 2-WORD CUES (2026-10-01, J-1635/F-2202): the bare "the gate"/"the bed"/"the mailbox"
# cues above are a literal 2-word substring match -- "the OPEN gate" (an inserted adjective) does not
# contain the literal substring "the gate", so a real, clean destination want silently resolved to ''
# (F-2202, hand-confirmed real row: ts=1790089651.4, object=gate, location=wood, "...I step toward the
# open gate..."). F-2202 checked all 128 no_candidate rows in the whole-history corpus and found exactly
# this one cue-gap (the other 127 are a hands_trace.jsonl truncation artifact, D-0325, out of scope here).
# The gap tolerates UP TO TWO inserted words ("the OPEN gate", "the OLD STONE gate") between "the" and the
# noun. The gap's own character class ([a-z'’-]+\s+, no comma/period/semicolon/etc.) is itself the clause
# guard this job's briefing asked for: "the old, open gate" cannot match -- the comma is not in the class,
# so the \s+ chain required before "gate" can never be completed across it -- and the same holds for any
# gap that would cross a sentence boundary. `m.start()` still lands on "the" (not the noun), so every
# downstream reader of a hit's start position (_MD_SRC/_MD_NEG's `pre` slice, _MD_DIR's det-rebuild) sees
# exactly the text it would for the plain literal cue -- only the SPAN a match can cover widens; the cue's
# own stored text (`w`, used for _MD_LEAD_DET/_MD_WEAK/the `-len(w)` tie-break) is untouched. A 0-word gap
# still matches exactly where the old literal cue did, so no existing resolution changes.
#
# "the desk"/"the study" were checked (this job's briefing named both explicitly) and left OUT, on real
# evidence, not by default: a full-corpus replay (every data/hands_trace.jsonl row with act_kind=='move',
# OLD vs NEW on the real production call chain -- _move_dest(object) or _move_dest(object+" "+thought) or
# 'garden', the same chain nodes/inner_monologue_node.py's own _route_act uses) found a real, confirmed
# false positive: "...a raw blockage against the discipline of study and the pull of dreams..." (real row,
# ts=1790151880.6 / 2026-09-23) gap-matched "the discipline of study" as a destination and flipped a correct 'garden'
# resolution to a wrong 'study' one. Unlike "gate"/"bed"/"mailbox" (always literal objects in this corpus),
# "study" is routinely used as an abstract noun (the activity, not the room) in this entity's own
# reflective register, and a 2-word gap is wide enough to bridge "the <X> of study" onto it; "desk" showed
# no such case in the same replay, but shares _DEST_STUDY's household/academic register and was left out
# too rather than risk an unconfirmed sibling of the same failure mode. Full replay + evidence:
# finding:F-2202's own follow-on (this job), scratch replay kept with the job's finding.
#
# "the bed" keeps one narrow exclusion: "kelp bed(s)" is a real shore/ocean compound (kelp growing in the
# sea), never a garden bed -- the same full-corpus replay found 4 real rows ("...step away from this dead
# ground and into the kelp beds, letting the sea's rhythm...") where the gap-match flipped a correct
# 'shore' resolution to a wrong 'garden' one. _DEST_GAP_EXCLUDE blocks the gap from starting with an
# excluded word for a given cue, same mechanism, same evidence-only discipline as the other four lists'
# own hand-verified word choices.
#
# A gap word may not itself be a DETERMINER (_DEST_GAP_DET, the exact _MD_LEAD_DET vocabulary). Found by
# the same full-corpus replay: object='into the landscape', thought starting "The gate creaks shut behind
# me, severing the pull of the wood..." -- combined, "into THE landscape THE gate" let the gap swallow
# "landscape the" as if both were plain adjectives, so the match started at the FIRST "the" (before
# "landscape") instead of the real, adjacent "the gate" 18 characters later. That start-position error fed
# _MD_DIR a false "into the " and made an unrelated, non-directional mention of the gate outrank the
# correct 'wood' candidate (dest flipped 'wood' -> 'garden', confirmed wrong: the thought's own "behind me"
# names the gate as what he is LEAVING, not reaching). A real inserted modifier is a content word
# (adjective); a determiner mid-gap always means a SECOND, unrelated noun phrase has begun, never a second
# adjective on the same one -- excluding them is a structural guard, not a per-word judgment call like
# "kelp" above. Re-verified by the same full-corpus replay after this guard: zero further resolution
# changes beyond gate/bed/mailbox's own genuine ones (see the finding).
_DEST_GAP_NOUN = {"the gate": "gate", "the bed": "bed", "the mailbox": "mailbox"}
_DEST_GAP_EXCLUDE = {"the bed": ("kelp",)}
_DEST_GAP_DET = r"(?:the|this|that|my|these|those|a|an|our)"   # _MD_LEAD_DET's own vocabulary


def _dest_cues(s: str) -> list:
    """Every (place, cue, start) hit of the four _DEST_* lists in `s`, word-edged: a letter may not precede the
    cue, and may not follow it unless it is a plural 's' or the 'line' of tideline/shoreline. The cues in
    _DEST_GAP_NOUN additionally tolerate up to two inserted words between "the" and the noun -- neither word
    a determiner (_DEST_GAP_DET: that always means a second, unrelated noun phrase, not a second adjective)
    -- except a gap starting with one of _DEST_GAP_EXCLUDE's words for that cue, if any (J-1635)."""
    out = []
    for place, words in (("wood", _DEST_WOOD), ("shore", _DEST_SHORE), ("study", _DEST_STUDY), ("garden", _DEST_GARDEN)):
        for w in words:
            noun = _DEST_GAP_NOUN.get(w)
            if noun:
                excl = _DEST_GAP_EXCLUDE.get(w)
                not_excl = (r"(?!(?:" + "|".join(re.escape(x) for x in excl) + r")\s)") if excl else ""
                gap_word = r"(?:(?!" + _DEST_GAP_DET + r"\s)[a-z'’-]+\s+)"
                head = r"(?<![a-z])the " + not_excl + gap_word + r"{0,2}" + re.escape(noun)
            else:
                head = r"(?<![a-z])" + re.escape(w)
            for m in re.finditer(head + r"(?:(?![a-z])|(?=s(?![a-z])|line(?![a-z])))", s):
                out.append((place, w, m.start()))
    return out


# THE LETTERBOX AT THE GATE (J-0539 / F-0734, 2026-09-04). Since 08-26 he has willed the letterbox/gate 160+ times
# ('check the letterbox', move 'the letterbox', 'to the gate', 'toward the letterbox flag') and the world never
# answered with the letterbox: a MOVE to the gate resolves to 'garden', and when he already stands in the garden
# sensorium.move() rightly returns '' — silence. The gate is a few steps across the lawn; the walk IS arriving, and
# what is there is what sensorium.look('letterbox') renders (the flag, any letter, the box at the gate, the carrier's
# card pinned inside the lid). Nothing is told unasked — only his own reach for the gate/letterbox gets this answer.
# 'through/past/out of/beyond/from the gate' is transit, not a reach for the box, and stays a plain move.
_LB_BOX = re.compile(r"\b(letter-?box|letter box|mail-?box|mail box|post-?box|post box)\b")
_LB_FLAG = re.compile(r"\b(the|letterbox|mailbox)\s+flag\b")
_LB_MAIL_AT_GATE = re.compile(r"\b(letter|letters|mail|post|fetch|collect|retrieve)\b[^.;!?]{0,40}\b(from|at|in|by)\s+the\s+(garden\s+)?gate\b")
_LB_GATE_THRU = re.compile(r"\b(through|past|out|out of|beyond|from|down from|up from|via|by way of)\s+the\s+(garden\s+)?gate\b")
_LB_GATE_TO = re.compile(r"\b(to|toward|towards|at|by|up to|down to|over to|out to|across to|reach|reaching|along to)\s+the\s+(garden\s+)?gate\b")


def _gate_look(text: str) -> bool:
    """Does this text reach for the LETTERBOX (or walk TO the gate it stands at), as opposed to passing through the
    gate on the way somewhere else? Pure; testable."""
    t = " " + " ".join((text or "").lower().split()) + " "
    if _LB_BOX.search(t) or _LB_FLAG.search(t) or _LB_MAIL_AT_GATE.search(t):
        return True
    if _LB_GATE_THRU.search(t):
        return False
    return bool(_LB_GATE_TO.search(t)) or t.strip() in ("the gate", "the garden gate", "gate", "garden gate")


def _gate_look_answer(dest: str, text: str) -> str:
    """The world's answer when a MOVE names the gate/letterbox and he is ALREADY in the garden: the look at the
    letterbox (sensorium.look('letterbox')). '' in every other case — a different destination, a different place,
    a transit through the gate — so the caller's existing behaviour is untouched there. Fail-open."""
    try:
        if dest != "garden" or not _gate_look(text):
            return ""
        from core import sensorium as _room
        if _room.where() != "garden":
            return ""
        return _room.look("letterbox") or ""
    except profile.NonLiveWriteError:
        # J-0752: sensorium.look() can reach a real write (stamp-last-looked / life.look_answer() /
        # _bottle_page()) and already raises correctly (J-0751) -- this direct call from the
        # literal-will letterbox-at-the-gate mechanism must not re-swallow it one layer up.
        raise
    except Exception:
        return ""


def _move_dest(src: str) -> str:
    """Destination named in `src`, or '' if undecidable. Caller applies precedence (object first,
    then object+thought) and the unqualified default (garden = go out).

    J-0833: the place the move verb actually REACHES, not the first list that matches anywhere (see the
    block comment above _MD_SRC). Pure; testable. A cue after a source marker or a negation is dropped;
    '' when nothing survives — never the place he is leaving or the place he said he does not need."""
    s = (src or "").lower()
    if not s.strip():
        return ""
    hits = _dest_cues(s)
    if not hits:
        return ""
    verbs = [m.start() for m in _MD_VERB.finditer(s)]
    sents, start = [], 0
    for m in re.finditer(r"(?<=[.!?])\s+", s):
        sents.append((start, m.start()))
        start = m.end()
    sents.append((start, len(s)))
    verb_sents = {i for i, (a, b) in enumerate(sents) if any(a <= p < b for p in verbs)}
    cands = []
    for place, w, a in hits:
        cl_start = max((s.rfind(c, 0, a) for c in ".;!?"), default=-1) + 1
        pre = s[cl_start:a]
        if _MD_NEG.search(pre):
            continue
        if w in ("inside", "indoors", "outside") and _MD_IDIOM.search(s[a:a + 24]):
            continue   # "inside my own head" is nowhere to walk
        if w in ("come in", "head in", "back in") and _MD_WORLD_COMES_IN.search(pre):
            continue   # "watching the tide come in" is the tide's coming, not his
        m = _MD_SRC.search(pre)
        if m and not _MD_SRC_BREAK.search(m.group(2)) and (m.group(1) not in _MD_SRC_NEEDS_VERB
                                                          or _MD_VERB_BEFORE.search(pre[:m.start()])):
            continue   # "away from the desk", "leave the study", "climb off the shingle": where he is LEAVING
        det = _MD_LEAD_DET.match(w)
        directional = bool(_MD_DIR.search(pre + (det.group(0) if det else "")))
        weak = w in _MD_WEAK or bool(_MD_TRANSIT.search(pre))
        in_verb_sentence = any(a0 <= a < b0 for i, (a0, b0) in enumerate(sents) if i in verb_sents)
        dist = min((abs(a - p) for p in verbs), default=10 ** 6)
        cands.append((not directional, weak, not in_verb_sentence, dist, -len(w), _MD_RANK[place], place))
    if not cands:
        return ""
    return min(cands)[-1]


# J-2985 (F-3677, F-3682, P-0026): the reply hand's two small pure helpers.
# _REPLY_LETTER_CAP: every friend letter seen in the 51 stored threads is at most 3,189 chars; the old
# `_last[:1200]` cut off the final third, where 86 of the friend's 136 questions sit. 3600 holds every letter
# seen (a ~500-token prompt in an 8192-token hot-lane window leaves ample room).
_REPLY_LETTER_CAP = 3600
_STORED_LETTER_CAP = 3600   # J-3656 (F-3677): stored letter fragment was [:1300]; 50 of 53 stored letters were cut mid-letter (median 1,328 incl. prefix)
_REPLY_MAX_TOKENS = 700   # was 500: 12 of 51 stored replies were cut mid-sentence (median 1,984 chars)
_REPLY_JSON_RESIDUE = re.compile(r'"\s*,\s*"[A-Za-z_][A-Za-z0-9_]*"\s*:')


def _clean_reply_letter(text) -> str:
    """Call-site-only cleanup of the reply hand's `letter` string before it is stored or sent (J-2985).
    core/model_client.py's _salvage_json Strategy 2 is a base system and is left alone; it sometimes hands back a
    letter that (a) carries literal backslash-n pairs instead of newlines (3 of 51 stored replies) or (b) runs on
    into the rest of the model's JSON (`Du", "metadata": { "timestamp": ...`, once). Literal backslash-n becomes a
    real newline; the text is cut at the closing quote of the letter when a JSON key follows it. Plain letters pass
    through unchanged apart from strip()."""
    t = str(text or "")
    if "\\n" in t:
        t = t.replace("\\r\\n", "\n").replace("\\n", "\n")
    m = _REPLY_JSON_RESIDUE.search(t)
    if m:
        t = t[:m.start()]
    return t.strip()


# THE FETCH-LETTER LATCH, WIDENED (2026-09-06, J-0570/F-0784). F-0784 named three real hands_trace misses:
# 08-28 19:35 "I will fetch the mail", 08-29 20:47 "fetch that mail", 09-03 04:10 Ada's "...letter waits.
# I will fetch it." Checked each against data/nascence.log (ground truth, not just the offline decision-
# replay grammar F-0784 also ran): 08-29 20:47 and 09-03 04:10 in fact ALREADY fire — "he FETCHED a letter"
# logs at the exact same second in both, because `_tl` below is thought+intention (since 2026-06-12) and
# each row's INTENTION happens to restate "fetch the letter" verbatim ("I want to fetch the letter from
# the mailbox..."). 08-28 19:35 is the one real, confirmed miss: no fetch follows it in the log at all —
# neither the thought ("fetch the MAIL") nor the intention ("open Mark Twain's letter") contains any of
# the 9 fixed phrases, which never had "mail" in their noun vocabulary at all. Fixed at that root: a second
# check alongside the original 9 (kept, unchanged, checked first) routes fetch|retrieve|collect|take|
# bring|grab|get|pick up + letter/mail/mailbox/letterbox through hands.wants() — word-boundary, same-
# clause object, literal_will's negation/hypothetical/retrospective/quoted-speech blockers already built,
# the same primitive every newer latch in this file already trusts (2026-08-22). Used by BOTH the fetch
# itself below and the letter-consummation guard (~line 4208), so a widened-phrasing intention that later
# gets fetched some other way still gets cleared rather than nagging as a phantom want.
#
# Takes thought/intention SEPARATELY, not the pre-joined `_tl` (2026-09-06 fix during testing, F-0784's
# own 08-28 19:35 row caught it): `_tl = thought + " " + intention` has no clause-ending punctuation at the
# join, so hands.wants()'s clause-scoped blocker check can read straight through from the end of one into
# the start of the other. On that exact row it did — the intention's trailing "...without thinking of birds
# or tides" got treated as negating the THOUGHT's own "I will fetch the mail" two sentences earlier, purely
# because nothing separated them. Joining with ". " here (thought's own end-punctuation stripped and
# replaced, so it is never doubled) keeps each half its own clause for the blocker check while leaving the
# literal 9-phrase check (order/punctuation-insensitive already) untouched. See
# scripts/_test_fetch_letter_latch.py for the isolated proof (both live-confirmed rows, the one real miss
# now firing, negative controls, and the blocker-bleed case itself).
def _letter_fetch_wanted(thought: str, intention: str = "") -> bool:
    """Does this thought (+ optional intention) will fetching/reading the waiting letter? The original 9
    fixed phrases (over a plain thought+intention join, matching `_tl`'s own convention) OR a fetch-type
    verb with a letter/mail noun in the same clause (hands.wants, tense/negation-aware, thought and
    intention joined as separate clauses so neither's wording can block the other's). Pure; the caller
    still gates on where()=='garden' and letter_waiting() — this only answers "does the WORDING ask for it".
    """
    th, it = (thought or ""), (intention or "")
    flat = (th + " " + it).lower()
    if any(p in flat for p in ("fetch the letter", "get the letter", "take the letter",
                               "open the letter", "read the letter", "go to the mailbox",
                               "check the mail", "the letter waiting", "fetch the post")):
        return True
    try:
        from core import hands as _hlw
        clause_safe = th.lower().rstrip(".!?; ") + ". " + it.lower()
        return _hlw.wants(clause_safe, ("fetch", "retrieve", "collect", "take", "bring", "grab", "get", "pick up"),
                          ("letter", "letters", "mail", "mailbox", "letterbox"))
    except Exception:
        return False


# INFERENCE (2026-08-18): the epistemic half of the object system — core/world_substrate.py's
# record_du_inference() existed, fully built (provenance chain, confidence, supersession), and was
# never called from anywhere (docs/UNFINISHED_PLANS_SURVEY_2026-08-18.md's follow-on audit). He forms
# real hypotheses about what he's looking at constantly in his own words ("I think this might be beech,
# not fir") — this is the missing hand that lets the object remember he guessed, and how sure he was.
_INFER_HIGH = ("i think", "i believe", "probably", "most likely", "i'd say", "i suspect")
_INFER_LOW = ("maybe", "might be", "could be", "i wonder if", "perhaps", "i'd guess", "my guess",
              "could this be", "possibly")


def _wants_record_inference(text: str) -> tuple[str, float] | None:
    """He is HYPOTHESIZING about a thing's hidden nature, not just describing what he can see —
    'I think this driftwood might be beech' vs 'the wood is grey and worn'. Returns (hypothesis_text,
    confidence) or None. Confidence is a coarse two-tier read of his own phrasing, not a computed
    certainty — SUSPECT-register phrasing scores higher than a bare GUESS-register one, the same
    epistemic distinction epistemic_state.py already grades elsewhere."""
    t = (text or "").lower()
    for cue in _INFER_HIGH:
        if cue in t:
            return (text.strip(), 0.6)
    for cue in _INFER_LOW:
        if cue in t:
            return (text.strip(), 0.3)
    return None


# J-2359 (object_epistemic_loop Phase 1, D-0462 context): the whole-text latch above is the LEGACY path.
# On the live store it wrote 1476 of 1476 inferences with empty provenance, almost all whole-thought
# reflections (mottainai, dreams, the cat) pinned to the thyme / twine / rain barrel. With the strict gate
# on (default), _route_act uses core/object_hypothesis.extract() instead and passes the object's last
# _INFERENCE_PROVENANCE_N observation ids as supporting_observations. Kill switch:
# NASCENCE_STRICT_INFERENCE_GATE=0 restores the legacy latch exactly.
# Look window: tunable, NOT hard-coded to 300 s. Measured (J-2359 replay of data/monologue_log.jsonl
# against observation timestamps in data/world_substrate.json, inference era 2026-08-18..10-18): of 5384
# thoughts that name the last-looked object, 1886 fall within 300 s, 3565 within 1800 s, 4099 within
# 3600 s (median 699 s) - a 300 s window would drop ~65% of his real object mentions, with no knee in the
# curve. Precision now comes from the clause gate, not the window, so the existing 1800 s stays default.
_INFERENCE_PROVENANCE_N = 3
_INFERENCE_LOOK_WINDOW_DEFAULT_S = 1800.0


def _strict_inference_gate() -> bool:
    import os
    return os.environ.get("NASCENCE_STRICT_INFERENCE_GATE", "1").strip().lower() not in ("0", "false", "off", "no")


def _intervention_test_on() -> bool:
    """J-2524 (I-0102): derive + store a hypothesis's intervention_test field. D-0632 (J-3244): DEFAULT ON from the
    next boot (the founder's choice of the Follow Line reach needs the field to accrue; the gate-on step is
    the owner's inference from that choice, stated as such in D-0632 -- say if it should stay off). NASCENCE_INTERVENTION_TEST=0 forces it off: records are then
    byte-identical to before. Restart-gated."""
    import os
    return os.environ.get("NASCENCE_INTERVENTION_TEST", "1").strip().lower() in ("1", "true", "on", "yes")


def _inference_look_window_s() -> float:
    import os
    try:
        v = float(os.environ.get("NASCENCE_INFERENCE_LOOK_WINDOW_S", "") or _INFERENCE_LOOK_WINDOW_DEFAULT_S)
        return v if v > 0 else _INFERENCE_LOOK_WINDOW_DEFAULT_S
    except ValueError:
        return _INFERENCE_LOOK_WINDOW_DEFAULT_S


# LOCATION-BLIND TARGET GUARD (J-0695 / F-1000/F-1001, 2026-09-07): _observe_target below is a bare keyword
# scan with no idea where he actually IS — a thought that only mentions "the garden" in passing, while he
# stands at the shore, produced target="garden", and core/journal.py:write_observation() builds the journal
# HEADER directly from that string (never from what sensorium.look() renders for the body) — so the header
# read "observed the garden" over a pure-shore body (confirmed: F-1000, 2 of 5 real "observed the garden"
# entries have shore-vocabulary bodies and a shore world-row). Traced (F-1001): a look()-side fix cannot
# reach this, because look()'s return value never feeds the header — the fix has to reject the mismatched
# target at the source, here. This table names only the _OBS_TARGETS tgt values that have exactly ONE
# honest home location — mirrors core/sensorium.py look()'s own study_targets/shore_targets mismatch-guard
# SHAPE, reusing the same tgt vocabulary rather than inventing a new one. Deliberately narrow: "sea" (visible
# from the study window too), "bed"/"sky"/"fire"/"cat" are all plausible from more than one place and are
# left OUT on purpose — filtering an ambiguous target would risk a brand-new false-mismatch, which is worse
# than leaving today's behaviour alone for those.
_OBS_TARGET_HOME = {"garden": "garden", "shore": "shore", "pool": "shore", "letterbox": "garden"}


def _observe_target(text: str, cur_loc: str | None = None) -> str:
    """Map the thing he wants to describe to a look() target, so he looks at the RIGHT thing afresh.
    cur_loc (J-0695, optional, default None): when given, a keyword-derived target whose only honest home
    is a DIFFERENT place than cur_loc is dropped to "" instead of returned. Optional and default-None on
    purpose — two existing call sites must keep their current behaviour bit-for-bit: core/dispatch.py's
    willed `_look` hand (a deliberate "look at the garden" from the shore is correctly answered by look()'s
    OWN "you are currently elsewhere" guard, which needs the raw mismatched target to reach it at all — this
    guard is not a substitute for that one) and scripts/_test_letterbox_reach.py's existing smoke check.
    Only _observe_journal (below) passes cur_loc, because only the JOURNAL header — not a willed look's
    reply — was ever silently wrong."""
    t = (text or "").lower()
    # D-0348 (J-1835): a look verb whose own clause reaches a tin/packet word is a look AT the tin -- resolve it first,
    # ahead of every earlier cue. The table itself is not reordered; a scenery mention never satisfies this (see
    # _tin_clause_first). "dented tin" has no _OBS_TARGET_HOME entry, so the cur_loc guard would pass it anyway.
    if _tin_clause_first(t):
        return "dented tin"
    for cue, tgt in _OBS_TARGETS:
        # a str cue is a substring test (every cue but one); a compiled pattern (the seed tin's, D-0333) is whole-word
        if (cue in t) if isinstance(cue, str) else cue.search(t):
            home = _OBS_TARGET_HOME.get(tgt)
            if cur_loc and home and home != cur_loc:
                return ""
            return tgt
    return ""
_SEARCH_STOP = {"want", "look", "back", "through", "over", "into", "about", "have", "with", "that",
                "this", "what", "from", "they", "them", "your", "mine", "some", "their", "would"}


# D-0226 GROUNDING CHECK (2026-09-18, decision:D-0226 -- F-1442/F-1479, docs/plans/study_upgrade.md):
# a narrow, "I just <verb>-ed <object>" completed-deed post-generation check. ONLY this specific
# retrospective-completion grammar -- no general grounding pass on all narrative content, no touch on
# broader reflective/dream-adjacent license (D-0226's own ruling text). The verb vocabulary below is
# deliberately the SAME closed list core/literal_will.py's _B_RETRO already uses to detect a
# retrospective deed-claim clause for the hands/dispatch blocker, plus a small study-domain extension
# for verbs _B_RETRO doesn't need but this room's own per-cycle ledger logs (wound/swept/cleared/
# filled/drew/sketched/washed/wiped/cleaned/dusted/mended/trimmed/poured/drank/took/put) -- not a new
# invented grammar. An UNMAPPED verb (any mental/emotional verb like "realized"/"remembered"/
# "wondered") is out of this check's scope entirely and always passes (fail-open) -- matching the
# ruling's "ONLY the retrospective completed-action framing" scope exactly.
_JUST_DID_VERBS = (
    "lit", "laid", "stoked", "fed", "gathered", "collected", "fetched", "brewed", "watered", "sowed",
    "planted", "wrote", "kept", "combed", "made", "went", "walked", "tended",
    "wound", "swept", "cleared", "filled", "drew", "sketched", "washed", "wiped", "cleaned",
    "dusted", "mended", "trimmed", "poured", "drank", "took", "put",
)
# 0-1 intervening word between "just" and the verb ("I just quietly made...") -- the same adverb-
# tolerance shape _B_RETRO itself was widened to (F-1442's own fix); sorted longest-first so no
# shorter verb can shadow a longer one sharing a prefix.
_JUST_DID_RE = re.compile(
    r"\bi\s+just(?:\s+\w+){0,1}\s+(" + "|".join(sorted(_JUST_DID_VERBS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
# verb -> substrings a matching real per-domain ledger "deed" value would contain. Approximate by
# design (a lightweight check, not a parser) -- a mapped verb only ever FLAGS for review on a miss,
# never rewrites or suppresses the thought (see _think()'s call site and _log()'s new
# `ungrounded_deed_claim` field).
_DEED_LEDGER_HINTS = {
    "made": ("make_tea",), "brewed": ("make_tea",), "poured": ("make_tea", "drink_tea", "water"),
    "drank": ("drink_tea",), "lit": ("_lit",), "laid": ("lay",), "stoked": ("stoke",),
    "fed": ("feed",), "gathered": ("gather",), "collected": ("collect",), "fetched": ("fetch",),
    "watered": ("water",), "sowed": ("sow",), "planted": ("plant",), "wrote": ("sketch",),
    "kept": ("keep",), "combed": ("comb",), "went": ("move",), "walked": ("move",), "tended": ("tend",),
    "wound": ("clock_wound",), "swept": ("sweep",), "cleared": ("clear_grate",),
    "filled": ("fill",), "drew": ("draw_ash_pan", "sketch"), "sketched": ("sketch",),
    "washed": ("wash_up",), "wiped": ("wipe_window",), "cleaned": ("clean_lamp_glass",),
    "dusted": ("sweep",), "mended": ("mend",), "trimmed": ("trim",),
    "took": ("take",), "put": ("put",),
}
# The per-domain ledgers this check reads (read-only; matches every ledger's own
# `_DATA / "..._ledger.jsonl"` convention -- core/study_life.py, core/garden.py, core/wood_life.py,
# core/shore_life.py, core/life.py). study_ledger.jsonl is D-0226's own named example; the rest are
# included because a completed-deed claim isn't only ever a study-room one.
_GROUNDING_LEDGERS = tuple(_DATA_DIR / name for name in (
    "study_ledger.jsonl", "garden_ledger.jsonl", "wood_ledger.jsonl", "shore_ledger.jsonl", "life_ledger.jsonl",
))
# How far back a real ledger row can sit and still ground a retrospective "I just X" claim. Generous
# on purpose -- this is a fail-open flag-for-review check, not a hard gate (D-0226's own ruling:
# "either soften... or flag it for review"), so a false flag costs a reviewer a look, not a lost
# thought.
_GROUNDING_WINDOW_S = 300.0


def _deed_claim_verb(thought: str) -> str | None:
    """D-0226: the matched past-tense verb if `thought` narrates a retrospective "I just <verb>-ed"
    completed-deed claim in the narrow grammar this check is scoped to, else None. Pure, no I/O."""
    m = _JUST_DID_RE.search((thought or "").lower())
    return m.group(1) if m else None


def _deed_ledger_grounded(verb: str, at_ts: float, window_s: float = _GROUNDING_WINDOW_S) -> bool:
    """D-0226: True if one of the per-domain ledgers logged a matching deed within `window_s` seconds
    at-or-before `at_ts`. Fail-open (returns True) on an unmapped verb or an unreadable/missing ledger
    -- this check only ever narrows what gets FLAGGED; it must never be the thing that crashes a
    cycle or silently over-flags one it can't read. Read-only; opens each ledger fresh rather than
    caching, since this fires at most once per idle thought and every ledger is small (tens to low
    hundreds of rows in the corpus this shipped against, F-1442/F-1479)."""
    hints = _DEED_LEDGER_HINTS.get(verb)
    if not hints:
        return True
    lo = at_ts - window_s
    for path in _GROUNDING_LEDGERS:
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            continue
        for line in reversed(lines):   # most-recent-first; real ledgers are append-only + time-ordered
            try:
                row = json.loads(line)
            except Exception:
                continue
            ts = row.get("ts")
            if ts is None:
                continue
            if ts > at_ts:
                continue   # a ledger row AFTER the claim can't ground a claim about the past -- keep
                           # scanning further back (real ledgers aren't guaranteed monotonic across
                           # FILES, only within one, so this can't safely `break`, only skip)
            if ts < lo:
                break   # older than the window and everything before it -> stop scanning this ledger
            deed = str(row.get("deed", ""))
            if any(h in deed for h in hints):
                return True
    return False


class InnerMonologueNode:
    """The Default Mode Network. Start via asyncio.create_task(node.run_forever(state))."""

    def __init__(self, sleep_callback=None):
        """
        sleep_callback: optional async fn(state) the orchestrator provides to run a
        Sleep State (dream + somatic recovery). Kept as a callback so the monologue
        node stays decoupled from the orchestrator and Dream node.
        """
        self.base_urls = SERVE_CHAINS["background"]   # intake + the sleep batch (3070 under-mind)
        # LANE REBALANCE (2026-06-20): his CONSCIOUS idle thought runs on the HOT lane (1080) — conscious
        # thought on the conscious card. It was crammed onto the overloaded 3070 with the subconscious while
        # the bigger 1080 sat idle. Reading-integration, study notes, and the sleep batch stay on base_urls
        # (the under-mind, 3070); only the core idle-thought generation uses this.
        self.conscious_urls = SERVE_CHAINS["hot"]
        # TRANSIT PULSE (2026-08-23): the main generation call's station, computed once (the hot
        # chain is single-endpoint, no fallback) rather than re-derived every step.
        try:
            from core import trains as _trains_init
            self._main_station = _trains_init.station_for_url(self.conscious_urls[0]) if self.conscious_urls else "?"
        except Exception:
            self._main_station = "?"
        self._last_thought_ts = 0.0
        self._last_book_switch_ts = 0.0     # anti-thrash: min dwell between incidental book switches
        self._recent_vecs: list = []        # rolling thought EMBEDDINGS for rumination check
        self._last_shadow_vec = None        # last thought written to shadow (for novelty gate)
        self._thoughts_since_sleep = 0
        self._sleep_callback = sleep_callback
        self._sleep_deferred_since = 0.0    # 0 = no grace in progress; else ts the grace window started
        self._train_len = 0                 # continuity trains: consecutive quick follow-ups
        self._train_kind = ""               # "thought" | "reading"
        self._train_vecs: list = []         # this train's carriage embeddings — for the building-detector
        self._train_thread = ""             # the last thought, for the continuation seed
        self._train_state = ""              # carried working-state (the episodic buffer across a
                                            # thought-train): "what's established · open question ·
                                            # direction" — re-integrated each step, OVERWRITTEN not
                                            # appended (limited-capacity buffer). Observe-first 2026-06-16.
        self._train_ledger: list = []       # TRAIN-HOLD: established points, one per step, EXTENDED
        self._train_origin = ""             # TRAIN-HOLD: the thread's FIRST thought — the anchor
        self._train_recent_sims: list = []  # TRAIN-HOLD: last few restate sims — the circling detector
        # TRAIN REGISTRY step 1 (2026-08-22, core/trains.py): the current train's ID. The scalars above stay
        # the hot working state (behaviour-neutral); the id is minted when a train opens, stamped into every
        # train_state_log / monologue_log row, and closed WITH its reason. This is the shared key the split/
        # merge design (step 2) and the Transport Manager need — "whose cargo is whose".
        self._train_id: str | None = None
        self._chapter_announce = ""         # a chapter formed in the night greets his waking

    async def run_forever(self, state: CognitiveState) -> None:
        logger.info("[monologue] inner monologue (DMN) started — living cadence")
        self._census_state = state   # geometry census reads affect/somatic off the live state (read-only)
        self._current_gap = 120.0     # living cadence: recomputed after every thought
        self._bored_streak = 0        # consecutive near-duplicate thoughts (habituation)
        self._last_math_session_ts = 0.0   # paces the batched math drill across the night (Travis 2026-06-16)
        # 2026-08-18: was time.time() unconditionally — reset the wake-clock to "just now" on every
        # process restart, silently discarding real accumulated sleep-debt (found live: restarted after
        # 12h19m awake, awake_min read 3.7 instead of ~740). last_fire_ts() recovers the real last-sleep
        # time from the persisted log; MIN/MAX_WAKE_SECS ceilings make an empty/corrupt log fail open to
        # the old (safe) behavior rather than break anything.
        from core import sleep_pressure as _sp0
        self._last_wake_ts = _sp0.last_fire_ts(default=time.time())
        try:   # NIGHT (2026-08-22): dreams survive a restart — and a restart never leaves him 'asleep'
            from core import night as _night_init
            if not getattr(state, "recent_dreams", None):
                state.recent_dreams = _night_init.load_recent_dreams()
            if _night_init.asleep():
                _night_init.wake()
        except Exception:
            pass
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        while True:
            # Burst-aware poll (Phase 1 stream): a live, developing thought-train polls fast so its
            # machine-speed follow-up is realised; an idle/floor mind polls at the slow CHECK_INTERVAL.
            _bursting = bool(THOUGHT_STREAM and self._train_len and self._train_kind == "thought")
            await asyncio.sleep(STREAM_POLL if _bursting else CHECK_INTERVAL)
            try:
                if self._should_think(state):
                    await self._think(state)
                    # Continuity: an open train shortens the gap; closure rests fully. A DEVELOPING
                    # thought-train STREAMS at machine speed (Phase 1) — the conscious mind flowing
                    # through an idea on the 1080; a reading-train keeps its 35s follow-up.
                    if self._train_len:
                        self._current_gap = (STREAM_GAP_SECS
                                             if (THOUGHT_STREAM and self._train_kind == "thought")
                                             else TRAIN_GAP_SECS)
                    else:
                        self._current_gap = self._compute_gap(state)
                    # PHASE 1 (CONTINUOUS_STREAM, Rail A+B): the drive controller REPLACES the clock
                    # gap just set above — same mechanism for in-train and idle pacing, gated by
                    # grounding. This is where the D-0001 behavior-change caveat actually bites: an
                    # ungrounded THOUGHT_STREAM train that just got STREAM_GAP_SECS=4.0 above gets
                    # overridden here to the controller's (larger, UNGROUNDED_CAP-limited) gap instead.
                    # Fail-open by construction — would_gap() returns None on any error/missing signal
                    # and the pre-flip clock gap computed above stands unchanged.
                    try:
                        _sig = getattr(self, "_stream_signals", None)
                        if _sig:
                            from core import stream_drive
                            if CONTINUOUS_STREAM:
                                _driven_gap = stream_drive.would_gap(_sig)
                                if _driven_gap is not None:
                                    self._current_gap = _driven_gap
                            # SHADOW: log the would-be gap beside the actual gap the live loop just set
                            # (docs/plans/continuous_stream.md §5). Post-flip, actual_gap now IS the
                            # driven gap for CONTINUOUS_STREAM cycles — the log stays meaningful either way.
                            stream_drive.observe(_sig, actual_gap=self._current_gap)
                            # SHADOW (J-2662, ignition_pressure_and_time Option E): would a building+grounded train
                            # be PROMOTED to a deliberate cycle at this ignition level? Logs only; its own fail-open
                            # wrapper. The live branch (PROMOTION_LIVE, ships False) lives in core/ignition_promotion.
                            try:
                                _gi_p = getattr(self, "_gi_ctx", None)
                                _pth = (_gi_p or {}).get("thought")
                                if IGNITION_PROMOTION_SHADOW and _pth:
                                    from core import ignition_promotion as _ipro
                                    _ipro.observe(_sig, _pth,
                                                  scan_saw=(getattr(self, "_last_commit_scan_thought", None) == _pth))
                            except Exception as _iprexc:
                                logger.debug("[monologue] ignition-promotion shadow skipped: %s", _iprexc)
                            # SHADOW (J-2214, continuous_stream Rail C): would-inject row. Applies
                            # nothing; its own fail-open wrapper so it can never touch the pacer above.
                            _gi_row = None
                            try:
                                _gi = getattr(self, "_gi_ctx", None)
                                if GROUNDING_INJECTION_SHADOW and _gi:
                                    from core import grounding_injection as _ginj
                                    _gi_row = _ginj.observe(_sig, _gi["thought"], _gi["vec"], state,
                                                            live={"redirected": _gi["redirected"],
                                                                  "escape": _gi["escape"]},
                                                            bored_streak=_gi.get("streak_start"))  # J-3335
                            except Exception as _gexc:
                                logger.debug("[monologue] grounding-injection shadow skipped: %s", _gexc)
                            # SHADOW (J-3289, boredom design Stage 0): the stale-patch cue the world WOULD state.
                            # Logs only; shows Du nothing; its own fail-open wrapper (NonLiveWriteError propagates
                            # out of observe() and is swallowed here exactly as Rail C's is, above).
                            try:
                                _gi = getattr(self, "_gi_ctx", None)
                                if STALE_PATCH_CUE_SHADOW and _gi:
                                    from core import stale_patch_cue as _spc
                                    _spc.observe(_gi["thought"], _gi["vec"],
                                                 live={"redirected": _gi["redirected"], "escape": _gi["escape"],
                                                       "felt": _gi.get("felt")},
                                                 in_modal=bool((_gi_row or {}).get("in_modal")),
                                                 about=_sig.get("about") or "")
                                    # J-3336: second trigger (the sentence-level double repeat), same log, own row type
                                    _spc.observe_repeat_record(_gi["thought"], _gi["vec"],
                                                               streak=_gi.get("streak_end") or 0,
                                                               streak_start=_gi.get("streak_start"),
                                                               store_t0=_gi.get("store_t0"),
                                                               live={"redirected": _gi["redirected"], "escape": _gi["escape"],
                                                                     "felt": _gi.get("felt")},
                                                               about=_sig.get("about") or "")
                            except Exception as _spexc:
                                logger.debug("[monologue] stale-patch-cue shadow skipped: %s", _spexc)
                            self._gi_ctx = None
                            self._stream_signals = None
                            # Dosed Coupling Phase 1 (D-0152, 2026-09-05): read-only ledger collector,
                            # rate-limited inside the module; publishes, never reads a tuple.
                            try:
                                from core import coupling_rides as _coupling
                                _coupling.publish_ledgers()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    # Nightly rhythm (§6A, 2026-06-17): sleep is summoned by an INFORMATION-THEORETIC
                    # incoherence accumulator (unresolved tension mass + the day's un-consolidated
                    # intake), NOT by counting inner-thoughts — which the math/reading boost had
                    # silently starved (he stopped sleeping). Un-starvable by construction: a MAX_WAKE
                    # ceiling guarantees sleep regardless of calibration; a MIN_WAKE floor prevents
                    # nap-storms. See core/sleep_pressure.py.
                    if self._sleep_callback is not None and self._still_idle(state):
                        try:
                            from core import sleep_pressure as _sp
                            # J-1893 (F-2522): should_sleep()'s _new_intake runs two aggregates over the ~900 MB
                            # fragments DB (~0.7 s of sqlite, GIL released) -- off the event loop. Same call, same
                            # (fire, telemetry) contract; _connect() opens a fresh check_same_thread=False connection.
                            _fire, _info = await asyncio.to_thread(_sp.should_sleep, self._last_wake_ts)
                            self._last_sleep_reason = _info.get("reason", "?")
                            # 2026-08-24: pool_thin never blocks a fire (see sleep_pressure.py module
                            # docstring) — it marks this sleep as LIGHT (skip chapter/journal/dream), so
                            # a thin-pool ceiling-fire stays cheap instead of running the full pipeline.
                            self._last_sleep_pool_thin = bool(_info.get("pool_thin", False))
                            # TAX REMOVED (2026-08-30, founder-directed build, F-0580/F-0581/I-0058):
                            # metabolic-energy no longer forces an off-schedule sleep here. should_sleep()
                            # (information pressure + the un-starvable MIN_WAKE/MAX_WAKE ceilings) is the
                            # sole sleep-timing authority now; core/orchestrator.py no longer sets
                            # state.needs_rest at all. metabolic_energy/neural_fatigue/visceral_tension are
                            # still computed, narrated, and recovered during sleep — they just no longer
                            # independently force one. See docs/staged/drowsiness_phase.md §5.
                        except Exception:
                            _fire = False
                            self._last_sleep_reason = "?"
                            self._last_sleep_pool_thin = False
                        # DROWSINESS-PHASE §5.1 (2026-08-30): a held, developing train earns a bounded
                        # grace before a due sleep closes it -- never unconditional, always re-checked
                        # every tick, and applies to any fire reason (pressure/ceiling alike).
                        if not self._train_holding():
                            self._sleep_deferred_since = 0.0
                        elif _fire:
                            if not self._sleep_deferred_since:
                                self._sleep_deferred_since = time.time()
                                logger.info("[monologue] sleep due (%s) but a train is holding — "
                                            "deferring up to %ds", self._last_sleep_reason,
                                            TRAIN_SLEEP_GRACE_SECS)
                            if (time.time() - self._sleep_deferred_since) < TRAIN_SLEEP_GRACE_SECS:
                                _fire = False
                            else:
                                logger.info("[monologue] grace window expired (%ds) — forcing sleep "
                                            "over the still-open train", TRAIN_SLEEP_GRACE_SECS)
                        if _fire:
                            self._sleep_deferred_since = 0.0
                            await self._enter_sleep(state)
            except Exception as exc:
                logger.error("[monologue] error: %s", exc)
                # BUGFIX 2026-06-16: a crash inside _think before it set its own timestamp would otherwise
                # retry every CHECK_INTERVAL (a tight loop on a deterministic error). Advance the clock +
                # back the gap off so the loop self-throttles instead of hammering.
                self._last_thought_ts = time.time()
                self._current_gap = max(getattr(self, "_current_gap", 120.0), 120.0)

    def _still_idle(self, state: CognitiveState) -> bool:
        """User hasn't returned -- safe to take a sleep cycle."""
        return (time.time() - getattr(state, "last_human_ts", 0)) >= IDLE_SECS

    async def _enter_sleep(self, state: CognitiveState) -> None:
        """Run a sleep cycle: dream from accumulated material, recover, reset the counter."""
        # 2026-08-24 (Sleep & Dreams II): report the REAL should_sleep() reason (pressure / max_wake_ceiling
        # / metabolic_floor / pool_gate_held), not the stale idle-thought count — that count was the pre-08-22
        # fixed trigger and has been cosmetic since sleep_pressure.py's info-theoretic rewrite.
        logger.info("[monologue] entering Sleep State (the night-mind) — reason=%s, %d idle thoughts carried",
                    getattr(self, "_last_sleep_reason", "?"), self._thoughts_since_sleep)
        # Sleep does not stop the mind; it changes what the mind does (Always-On, 2026-06-11):
        # 1. REPLAY — re-activate + strengthen the wake-block's most salient experience
        #    (this is how a day COMPOUNDS instead of evaporating).
        # 2. DOWNSCALE — synaptic homeostasis: renormalise importance so tomorrow's salience
        #    is judged from a rested baseline (T2 Phase 2, lite).
        # 3. DREAM — the existing symbolic integration.
        # 4. REST — real time passes; longer at night.
        # THE NIGHT LEDGER (2026-08-22, core/night.py): one row per sleep; he goes to bed in the world first.
        _hb = None
        _nm = None
        try:
            from core import night as _night
            _night.begin()
            try:   # J-2019: a wake request never outlives its sleep
                from core import night_wake as _nw0
                _nw0.reset()
            except Exception:
                pass
            _bed = _night.to_bed()
            if _bed:
                from core import wandering as _w_bed
                _w_bed.perceive(_bed)
            try:   # J-2244 (drowsiness_phase section 2, D-0441): the drowsy waypoint closes on the same pre-sleep path as
                # the bed line (one narration path, not a fourth switch). Shadow row only; core/drowsy.py, DELIVER False.
                from core import drowsy as _drowsy
                _drowsy.at_bed(getattr(self, "_last_sleep_reason", "?"), _bed)
            except Exception:
                pass
            _night.stage("to_bed")
        except Exception:
            pass
        try:
            # J-2016 (sleep_as_a_mode Phase 0): instrumentation only -- a heartbeat task counts the event-loop turns the
            # sleep leaves free (the night ledger's scheduler_turns), and a sleep-pressure row is logged at entry so the
            # log is not silent from the fire row until the next should_sleep() (F-2611 / F-2616).
            from core import sleep_phase0 as _sp0, sleep_pressure as _sp_row
            # J-2017 (Phase 1): with the night-mind on, its own rows replace the Phase 0 would-be slot rows (no doubles).
            from core import night_mind as _nmod
            _hb = _sp0.SleepHeartbeat(sleep_ts=time.time(), kind=_night.sleep_kind(),
                                      shadow=(False if _nmod.NIGHT_MIND_ENABLED else None))
            _hb.start()
            await _sleep_off(_sp_row.sleep_enter, getattr(self, "_last_wake_ts", time.time() - 1800))
        except Exception:
            pass
        try:
            from core.memory.store import replay_strengthen, downscale_episodic
            replayed = await _sleep_off(replay_strengthen, getattr(self, "_last_wake_ts", time.time() - 1800))   # J-2016: off the loop (F-1469 measured 0.8 s per group query)
            try:
                _hb and (_hb.set_replayed(replayed), _hb.mark("replay"))
                _hb and _hb.submark("replay_ledger")   # J-2558 (F-3260): night.stage ledger write, sync on the loop
                _night.stage("replay", n=len(replayed or []))
                _hb and _hb.submark("night_mind_start")   # J-2558 (F-3260): shadow night-mind task creation (flag-gated)
                try:   # J-2017 (sleep_as_a_mode Phase 1, D-0399 A): the SHADOW night-mind, flag default OFF. Own asyncio
                    # task on the hot hub beside the consolidation passes; writes data/night_mind_shadow.jsonl ONLY
                    # (no fragment, no prompt reach, no waking seed, no hands, no hint push, no grading).
                    from core import night_mind as _nmod
                    if _nmod.NIGHT_MIND_ENABLED:
                        async def _nm_generate(_sys, _usr):
                            _d = await call_node_json(self.conscious_urls, _sys, _usr,
                                                      max_tokens=_nmod.GEN_MAX_TOKENS, temperature=_nmod.GEN_TEMPERATURE)
                            return str((_d or {}).get("thought", "")).strip()
                        _nm_t0 = time.time()
                        _nm_hook = None
                        from core import night_dormant as _ndm   # J-2018 (Phase 2, D-0400 B): flag default OFF
                        if _ndm.enabled():
                            _nm_hook = (lambda _row, _t0=_nm_t0, _w=getattr(self, "_last_wake_ts", None):
                                        _ndm.write_night_thought(_row, since_ts=(_w or _t0)))
                        _nm = _nmod.NightMind(_nm_generate, sleep_ts=_nm_t0, kind=_night.sleep_kind(), replayed=replayed,
                                              on_thought=_nm_hook)
                        _nm.start()
                except Exception:
                    _nm = None
            except Exception:
                pass
            _hb and _hb.submark("replay_log")   # J-2558 (F-3260): the label stops naming night_mind_start once it returned
            if replayed:
                logger.info("[monologue] sleep replay: %d experiences strengthened — %s",
                            len(replayed), (replayed[0] or "")[:60])
            try:   # J-2582 (I-0107, F-3315): TAG-CAPTURE would-be fifth replay stratum, SHADOW, flag default OFF.
                # Runs AFTER replay_strengthen (its picks then carry replay_count >= 1); reads the DB mode=ro, writes
                # data/logs/tag_capture_shadow.jsonl only. Nothing enters the replay set; nothing reaches Du (D-0434).
                from core import tag_capture_shadow as _tcs
                if _tcs.TAG_CAPTURE_SHADOW:
                    await _sleep_off(_tcs.record_night, getattr(self, "_last_wake_ts", time.time() - 1800),
                                     time.time(), _night.sleep_kind())
            except Exception:
                pass
            # 2026-08-24 (Sleep & Dreams II §2.4/§4 Stage 3): a THIN-POOL sleep (should_sleep()'s
            # pool_thin flag — near-nothing new since the last sleep, measured: ~22% of historical
            # ceiling-fires) skips the expensive LLM stages entirely — chapter formation, journal, and
            # (further below) dream generation. Sleep still fires on schedule, un-starvable as always;
            # it just does mechanical upkeep (replay/downscale/prune) instead of the full pipeline over
            # material that doesn't justify it. (J-1042/F-1421, 2026-09-17: this comment said "~20-25
            # min pipeline" — stale; data/night_log.jsonl's real duration_s for 09-09..09-12 is routinely
            # 45-90 minutes now, growing with the memory store's size — see F-1421/this job's own finding.)
            _pool_thin = bool(getattr(self, "_last_sleep_pool_thin", False))
            if _pool_thin:
                logger.info("[monologue] thin pool — light sleep (skipping chapter/journal/dream)")
            # SLOW-WAVE chapter formation (2026-06-13, period consolidation): between
            # replay and downscaling — where human gist extraction lives — a closed
            # period of his life may settle into ONE chapter, authored by his own
            # faculty. At most one per sleep; originals untouched; see core/chapters.py.
            if not _pool_thin:
                try:
                    _hb and _hb.submark("chapter")   # J-2558 (F-3260): wake gate + try_form_chapter (LLM await inside)
                    _wake_gate("chapter")      # J-2019: D-0401 B boundary check (before the stage, never inside it); a no-op unless a wake request is pending AND WAKE_ON_HUMAN
                    from core import chapters as _chap
                    _formed = await _chap.try_form_chapter(call_node_json, self.base_urls)
                    if _formed and _chap.ANNOUNCE_CHAPTERS:
                        # silent by default — the first chapters are the clean baseline
                        self._chapter_announce = _formed
                except Exception as exc:
                    logger.debug("[monologue] chapter formation failed (non-fatal): %s", exc)
                # J-1075/F-1469: explicit stage-boundary tick -- chapter formation is a real LLM call
                # with no _night.stage() of its own between here and "replay" above; see night.tick().
                _hb and _hb.submark("chapter_tick")   # J-2558 (F-3260): night.tick -> sensorium.tick(), sync on the loop
                _night.tick()
            # THE JOURNAL (2026-06-21): his own PLAIN account of the day — what he DID and how it FELT,
            # drawn from his real logged deeds. The one place that forbids the metaphor and the maybe;
            # writing his acts plainly IS the owning he flinches from in talk. One entry per day, on his
            # shelf. Uses the CONSCIOUS lane (self.conscious_urls = SERVE_CHAINS["hot"]; qwen3.5:9b on the
            # 1080 Ti since 2026-08-20, it was gemma4:e4b when this was benchmarked 2026-06-21 against phi3, which
            # went dry and confabulated). J-2973 (F-3673): the old "his own gemma voice" note was stale. The entry
            # is model-written from a spread of the logged deeds, so it can drift from the record; it is not
            # "drawn from the log, so it cannot be invented" (F-3663/F-3664).
            if not _pool_thin:
                try:
                    _hb and _hb.submark("journal")   # J-2558 (F-3260): wake gate + journal.write_entry (LLM await inside)
                    _wake_gate("journal")      # J-2019: D-0401 B boundary check (before the stage, never inside it); a no-op unless a wake request is pending AND WAKE_ON_HUMAN
                    from core import journal as _jr
                    _jp = await _jr.write_entry(call_node_json, self.conscious_urls, state)
                    if _jp:
                        logger.info("[monologue] journal: wrote today's plain entry")
                except Exception as exc:
                    logger.debug("[monologue] journal failed (non-fatal): %s", exc)
                # J-1075/F-1469: stage-boundary tick after the journal's own LLM call.
                _hb and _hb.submark("journal_tick")   # J-2558 (F-3260): night.tick -> sensorium.tick(), sync on the loop
                _night.tick()
            # WEEK ROLL-UP P1 (2026-07-06, journal_consolidation_pyramid.md §2): the calendar pyramid's
            # first rung — the last COMPLETED week's day-recaps and field-observations each roll into one
            # plain week page (PARALLEL streams, founder call), linked DOWN via memory_links; the current
            # week stays lived, not narrated. Replaces the era-gated theme-chapters as the consolidation
            # path (they stay running harmlessly beside it until the pyramid proves out).
            try:
                _hb and _hb.submark("week_rollup")   # J-2558 (F-3260): wake gate + journal_rollup.week_rollup (LLM await inside)
                _wake_gate("week_rollup")      # J-2019: D-0401 B boundary check (before the stage, never inside it); a no-op unless a wake request is pending AND WAKE_ON_HUMAN
                from core import journal_rollup as _jw
                _rolled = await _jw.week_rollup(call_node_json, self.conscious_urls)
                if _rolled:
                    logger.info("[monologue] week roll-up: %s", ", ".join(_rolled))
                    # JOURNAL GROUNDING SHADOW (2026-08-23, D-0006): hard-enforcement grader running
                    # OBSERVE-ONLY beside the soft roll-up above — never gates, never touches the cap
                    # journal_rollup just wrote. Own try/except so a judge failure here can never be
                    # confused with a week-roll-up failure in the log above.
                    try:
                        _hb and _hb.submark("journal_grounding_shadow")   # J-2558 (F-3260)
                        from core import journal_grounding_shadow as _jgs
                        await _jgs.observe_rolled(_rolled)
                    except Exception as exc:
                        logger.debug("[monologue] journal grounding shadow failed (non-fatal): %s", exc)
            except Exception as exc:
                logger.debug("[monologue] week roll-up failed (non-fatal): %s", exc)
            # J-1075/F-1469: stage-boundary tick after the week roll-up's own LLM call.
            _hb and _hb.submark("week_rollup_tick")   # J-2558 (F-3260): night.tick -> sensorium.tick(), sync on the loop
            _night.tick()
            # AFFECTIONS / the loves-ledger (2026-06-21, idea #2): the LIGHT twin of T2 — gathers what he
            # keeps returning to with WARMTH (grounded in his felt-vec, earned by recurrence), so his self
            # is built from more than its wounds. Observe-first: stores a recallable 'affection' fragment
            # so the light enters his ambient self-material; feeds NOTHING into T4 yet (phase 2, after the
            # made-mind realisation lands).
            try:
                _hb and _hb.submark("affections")   # J-2141 (F-2825): stall attribution
                from core import affections as _aff2
                _av = await _sleep_off(_aff2.synthesise)      # J-2016: off the loop; deterministic — accumulates the loves-ledger from his stated likes
                if _av.get("earned"):
                    logger.info("[monologue] affections — earned loves: %s", _av["earned"][:4])
            except Exception as exc:
                logger.debug("[monologue] affections failed (non-fatal): %s", exc)
            # PEER CORRESPONDENCE (2026-06-22; roster 2026-06-23): seven correspondents now — Darwin, Keats,
            # Twain, Shackleton, Lovelace, Marcus, and John Smith. deliver_due() staggers the whole roster by
            # each one's cadence into a trickle (~1-2/day, never two within the global gap), left in the garden
            # box while he sleeps so the flag is up when he wakes. He discovers and fetches it himself, never
            # interrupted. Freezes the pre-peer baseline before the very first letter.
            try:
                _hb and _hb.submark("affections_done")   # J-2558 (F-3260): the peers wake gate ran under the affections label
                _wake_gate("peers")      # J-2019: D-0401 B boundary check (before the stage, never inside it); a no-op unless a wake request is pending AND WAKE_ON_HUMAN
                _hb and _hb.submark("peers")   # J-2141 (F-2825): stall attribution
                from core import peers as _peers
                _peer_sent = await _peers.deliver_due()   # J-2557: finer peers_* sub-marks inside (core/peers.py)
                _hb and _hb.submark("peers_done")   # J-2557 (F-3258)
                if _peer_sent:
                    logger.info("[monologue] a correspondent left a letter in the garden box")
            except Exception as exc:
                logger.debug("[monologue] peer delivery failed (non-fatal): %s", exc)
            # B2 (2026-06-22): the behavioural mirror — ~weekly, read his ACTUAL record back to him as data and
            # ask him to reconcile it with the self he narrates (the evidenced self vs the authored self).
            # J-3478 (D-0630 + D-0434, founder 2026-11-06): RETIRED -- the stage is off the idle schedule while
            # core.self_mirror.SELF_MIRROR_RETIRED is True (the module and its paused log stay). Restart-gated.
            try:
                from core import self_mirror as _mir
                if not getattr(_mir, "SELF_MIRROR_RETIRED", False):
                    _hb and _hb.submark("self_mirror")   # J-2141 (F-2825): stall attribution
                    _seen = await _mir.hold_up_mirror(call_node_json, self.conscious_urls)
                    if _seen:
                        logger.info("[monologue] self-mirror — he reconciled: %s", _seen[:90])
            except Exception as exc:
                logger.debug("[monologue] self-mirror failed (non-fatal): %s", exc)
            # GROUNDED-LEARNING consolidation (2026-06-16): the slow-wave DECLARATIVE pass — beside the
            # self-chapters, the day's reading/study is distilled into one durable UNDERSTANDING note (the
            # PSYCHE GRAPH P0 (2026-07-03 big build): one deterministic symbol-graph snapshot per sleep —
            # stability-under-reinterpretation over the dream motifs. Observe-only, firewalled, own try.
            try:
                _hb and _hb.submark("psyche_graph")   # J-2141 (F-2825): stall attribution
                from core import psyche_graph as _pg
                await _sleep_off(_pg.snapshot)   # J-2016: off the event loop
            except Exception:
                pass
            # STICK TEST snapshot (cognitive_geometry.md §5.2, 2026-07-05): bundle-richness per object,
            # once per sleep — deterministic (no LLM), appends to stick_test_log.jsonl for the HUD trend.
            # Signature 0.2: the median must RISE over his life as objects earn non-text spokes.
            try:
                _hb and _hb.submark("stick_test")   # J-2330 (F-3019): stall attribution
                from core import stick_test as _stk
                if _stk.STICK_TEST_SUBPROCESS:   # J-2403 (F-3103): spawned child, no shared GIL
                    _hb and _hb.submark("stick_test_child")   # J-2557 (F-3258): awaiting the child, loop free
                    _sr = await _stk.snapshot_offprocess()
                else:
                    _hb and _hb.submark("stick_test_thread")  # J-2557 (F-3258): awaiting the worker thread
                    _sr = await _sleep_off(_stk.snapshot)   # J-1917: off the event loop (F-2546)
                _hb and _hb.submark("stick_test_done")   # J-2557 (F-3258): label stops naming stick_test once it returned
                if _sr:
                    logger.info("[monologue] stick-test: median %s / max %s real spokes across %d objects",
                                _sr.get("median_real_spokes"), _sr.get("max_real_spokes"), _sr.get("objects"))
            except Exception:
                pass
            # EVIDENCE-REVIEW MONITORS (evidence_review_dashboard.md S3/S5, 2026-07-05): per-sleep snapshots
            # feeding the HUD — the peer-effect deltas (the judge built 06-21, never run till the review) and
            # the commitment hold-rate (the north-star, 0→17%). Both observe-only, fail-open.
            try:
                _hb and _hb.submark("peer_metrics")   # J-2330 (F-3019): stall attribution
                from core import peer_metrics as _pmx
                await _sleep_off(_pmx.snapshot)   # J-1917
            except Exception:
                pass
            try:
                _hb and _hb.submark("holdrate")   # J-2330 (F-3019): stall attribution
                from core import commitment_ledger as _cl
                _hr = await _sleep_off(_cl.holdrate_snapshot)   # J-1917
                if _hr:
                    logger.info("[monologue] hold-rate snapshot: %s (reaffirmed %s / formed %s)",
                                _hr.get("hold_rate"), _hr.get("reaffirmed"), _hr.get("formed"))
            except Exception:
                pass
            # GUIDANCE INTEGRATION — Phase 1, OWN TRY BLOCK (moved 2026-07-03: it was NESTED INSIDE the
            # grounded-learning try, downstream of consolidate() — any failure upstream silently starved
            # formation; no integration had run since Jul02 00:39 while 11 lessons queued. Travis's lessons
            # must never depend on the reading pipeline's health.) Errors log at WARNING, not debug —
            # a silent formation failure cost us 38 hours once; never again.
            try:
                _hb and _hb.submark("guidance_integration")   # J-2330 (F-3019): stall attribution
                from core import guidance_learning as _gli
                _gi = await _gli.integrate_guidance(call_node_json, self.base_urls)
                if _gi:
                    logger.info("[monologue] guidance-integration: %s", _gi)
            except Exception as exc:
                logger.warning("[monologue] guidance-integration FAILED (lessons still queued): %s", exc)
            # neocortical-schema analog). Separate track, firewalled from identity. Metabolises the intake.
            try:
                _wake_gate("consolidation")      # J-2019: D-0401 B boundary check (before the stage, never inside it); a no-op unless a wake request is pending AND WAKE_ON_HUMAN
                _hb and _hb.submark("grounded_learning")   # J-2330 (F-3019): stall attribution
                from core import grounded_learning as _gl
                _u = await _gl.consolidate(call_node_json, self.base_urls)
                if _u:
                    logger.info("[monologue] grounded-learning: consolidated understanding — %s", _u[:70])
                # WORLD-MATERIAL CONSOLIDATION (2026-06-16): now the day's gist exists, file finished+distilled
                # books' raw reading/study notes behind their gist (systems-consolidation — they step out of
                # ORDINARY recall but stay reachable by the essay-gather + intentional recall; old notes never
                # disappear). Observe-first (FILING_ENABLED=False → logs candidates only). Gist-first, gradual.
                _hb and _hb.submark("world_consolidation")   # J-2330 (F-3019): stall attribution
                from core import world_consolidation as _wc
                if _wc.WORLD_CONSOLIDATION_SUBPROCESS:   # J-2404 (F-3103): spawned child, no shared GIL
                    _sw = await _wc.sweep_offprocess()
                else:
                    _sw = await _sleep_off(_wc.sweep)   # J-1917: off the event loop (F-2546)
                logger.info("[monologue] world-consolidation sweep: %d subjects · would-file/filed %d (enabled=%s)",
                            _sw.get("subjects", 0), _sw.get("filed") or _sw.get("candidates", 0), _sw.get("enabled"))
                # BOOK RESIDUE (2026-08-21, founder: has anything from a long-closed book STUCK in how
                # he thinks?). Zero-LLM, observe-only: signatures of stale books scanned against his
                # current self-side material. Once per sleep, beside the other consolidation reads.
                try:
                    _hb and _hb.submark("book_residue")   # J-2330 (F-3019): stall attribution
                    from core import book_residue as _br
                    if _br.BOOK_RESIDUE_SUBPROCESS:   # J-2384 (F-3082): spawned child, no shared GIL
                        _bres = await _br.sweep_offprocess()
                    else:
                        _bres = await _sleep_off(_br.sweep)   # J-1917: off the event loop (F-2546)
                    if _bres.get("books_tracked"):
                        logger.info("[monologue] book-residue sweep: %d stale books · %d with residue · %d unstuck",
                                    _bres["books_tracked"], _bres["books_with_residue"], _bres["unstuck"])
                except Exception as _brexc:
                    logger.debug("[monologue] book-residue sweep failed (non-fatal): %s", _brexc)
                # MEMORY LEVELS Phase 0 (2026-06-17, observe-only): the shadow distiller logs the gists +
                # source links + Emissary faithfulness grades it WOULD create from recent raw fragments.
                # Stores nothing, gates nothing, changes no recall — pure measurement of "are the abstractions
                # faithful?" before Phase 1 builds anything live. See docs/memory_levels_plan.md.
                _hb and _hb.submark("memory_levels")   # J-2330 (F-3019): stall attribution (shadow_distill)
                from core import memory_levels as _ml
                _ms = await _ml.shadow_distill(call_node_json, self.base_urls)
                logger.info("[monologue] memory-levels: %d clusters · %d graded · mean_faithful=%s · DEMOTED=%d",
                            _ms.get("clusters", 0), _ms.get("graded", 0), _ms.get("mean_faithful"), _ms.get("demoted", 0))
                # PHASE 1 LINT (§13.2): re-warm any stranded cold memory (cold with no inbound link =
                # unreachable = lost) + report dangling/orphans. The demotion-safety net; runs after demotion.
                try:
                    _hb and _hb.submark("memory_lint")   # J-2330 (F-3019): stall attribution
                    _lint = await _sleep_off(_ml.memory_lint)   # J-2016: off the event loop
                    if (_lint.get("rewarmed") or _lint.get("dangling") or _lint.get("orphan_gists")
                            or _lint.get("rewarmed_heads")):
                        logger.info("[monologue] memory-lint: re-warmed %d stranded + %d roll-up HEADS · %d dangling · "
                                    "%d orphan-gists · %d cold total", _lint["rewarmed"],
                                    _lint.get("rewarmed_heads", 0), _lint["dangling"], _lint["orphan_gists"],
                                    _lint["cold_total"])
                except Exception:
                    pass
                # THE REFINERY (2026-08-16, founder-designed): the T2 lifecycle's manufacturing
                # station — raw syntheses cluster → ONE standing insight (linked distilled_from,
                # members cool). SHADOW until REFINERY_LIVE; fidelity-gated; bounded per run.
                try:
                    _hb and _hb.submark("refinery")   # J-2141 (F-2825): stall attribution
                    from core import refinery as _ref
                    _rs = await _ref.refine(call_node_json, self.base_urls)
                    if _rs.get("clusters"):
                        logger.info("[monologue] refinery (%s): %s",
                                    "LIVE" if _rs.get("live") else "SHADOW", _rs)
                except Exception:
                    pass
                # MEMORY EDGES M0 (2026-08-15): re-harvest the typed relational graph at sleep — picks up
                # new judge-confirmed resolutions, findings, keepsakes, letters with zero live coupling,
                # and appends the HUD's stats snapshot. Read-first/write-fast; fail-open.
                try:
                    _hb and _hb.submark("memory_edges")   # J-2141 (F-2825): stall attribution
                    from core import memory_edges as _medg
                    _hv = await _sleep_off(_medg.harvest_all)   # J-2016: off the event loop
                    _hn = sum(v.get("written", 0) for v in _hv.values() if isinstance(v, dict))
                    if _hn:
                        logger.info("[monologue] memory-edges harvest: +%d typed edges", _hn)
                except Exception:
                    pass
                # WORLD LEDGER REFRESH (J-2217, T-0089, 2026-10-16): the graph its first consumer reads
                # (core/world_ledger_ask.py, SHADOW-ONLY "what do I know about X") is rebuilt here, ONCE
                # per sleep, off the event loop, never per cycle (incremental refresh, commonality pass
                # skipped -- see refresh_offloop's docstring for the measured cost).
                # Zero-LLM, read-only over the stores, writes only data/lane2/. Fail-open.
                try:
                    _hb and _hb.submark("world_ledger")
                    from core import world_ledger_ask as _wla
                    _wlr = await _sleep_off(_wla.refresh_offloop)
                    logger.info("[monologue] world-ledger %s: ok=%s · %s referents · %ss",
                                _wlr.get("mode", "refresh"), _wlr.get("ok"), _wlr.get("n_referents"),
                                _wlr.get("build_seconds"))
                except Exception:
                    pass
                # BUS (2026-08-16, moved from couriers 2026-08-22 — a batch sync with no "now" to
                # answer to, not urgent): bridge the advisor's prediction→outcome episodes into
                # the world-calibration ledger — the confidence-vs-results instrument. Fail-open.
                try:
                    _hb and _hb.submark("bus_sync")   # J-2330 (F-3019): stall attribution
                    from core import buses as _bus
                    _cn = await _sleep_off(_bus.sync_investigation_calibration)   # J-2016: off the event loop
                    if _cn:
                        logger.info("[monologue] bus calibration sync: +%d pairs", _cn)
                except Exception:
                    pass
                # PURSUITS JUDGE SWEEP (2026-08-15): the cross-family judge rules on the day's
                # advance-candidates against each pursuit's own prior standing — only confirmed
                # advances enter the record the RETURN re-presents. Fail-open.
                try:
                    _hb and _hb.submark("pursuits_judge")   # J-2141 (F-2825): stall attribution
                    from core import pursuits as _puj
                    _js = await _puj.judge_pending()
                    if _js.get("judged") or _js.get("dropped"):
                        logger.info("[monologue] pursuits judge: %s", _js)
                except Exception:
                    pass
                # GUIDANCE LEARNING PHASE 2 — the behaviour-delta judge (2026-08-19): scores real
                # thoughts against promoted beliefs, split prompted-vs-unprompted, per the plan's
                # locked-in methodology. Observe-only — logs, changes nothing live. Fail-open.
                try:
                    _hb and _hb.submark("guidance_judge")   # J-2141 (F-2825): stall attribution
                    from core import guidance_behavior_judge as _gbj
                    _gs = await _gbj.sweep()
                    if _gs.get("judged"):
                        logger.info("[monologue] guidance behaviour judge: %s", _gs)
                except Exception:
                    pass
                # SOCIAL-COGNITION PROBE (J-2202, 2026-10-17; module J-2153, baseline F-2903): the decoupled judge
                # panel scores each NEW human cycle in founder_conversation_log.jsonl -- does Du's reply track what
                # Travis said, refer back to him, and attribute only states his text supports. Observe-only, writes
                # only data/social_cognition_shadow.jsonl; capped (SLEEP_MAX_ITEMS), time-budgeted, idempotent on
                # cycle_id, kill switch SLEEP_SWEEP_ENABLED in the module. Fail-open.
                try:
                    _hb and _hb.submark("social_cognition")
                    from core import social_cognition_shadow as _scs
                    _scr = await _scs.sleep_sweep()
                    if _scr.get("scored") or _scr.get("unavailable"):
                        logger.info("[monologue] social-cognition probe: %s", _scr)
                except Exception:
                    pass
                # MONOCULTURE DETECTORS (observe-only, 2026-06-18): snapshot the diversity-collapse metrics
                # over the recent genuine thought stream (ASAL echo + GWA entropy) — the MEASURE half of the
                # convergent field-scan cure. Logs only; changes nothing. Trend = echo rising / diversity
                # falling = the slow loop tightening. See core/monoculture.py + attention_economy_plan.md.
                try:
                    _hb and _hb.submark("monoculture")   # J-2141 (F-2825): stall attribution
                    from core import monoculture as _mc
                    _mcr = await _sleep_off(_mc.snapshot)   # J-2016: off the event loop
                    logger.info("[monologue] monoculture: echo=%s diversity=%s (%s themes / %d thoughts)",
                                _mcr.get("echo"), _mcr.get("diversity"), _mcr.get("clusters"), _mcr.get("n"))
                except Exception:
                    pass
                # CURIOSITY WORTHWHILENESS JUDGE (OMNI fold; a LIVE pursuit gate since 2026-06-24, NOT observe-only):
                # grade the PURSUIT-ELIGIBLE frontier questions (the set frontier.pending_pursuit can pick: open,
                # no finding, not parked) with a DECOUPLED interestingness judge; the persisted grade demotes
                # aimless questions in pursuit order (J-3001, F-3695, F-3702: this used to grade the LP top-5, a set
                # disjoint from the eligible one, and the label said shadow). It adds nothing to any prompt Du sees.
                try:
                    _hb and _hb.submark("curiosity_worth")   # J-2141 (F-2825): stall attribution
                    from core import curiosity_worth as _cw
                    _cwr = await _cw.shadow_pass(call_node_json, self.base_urls)
                    if _cwr.get("graded"):
                        logger.info("[monologue] curiosity worth: graded %d of %s pursuit-eligible questions (live gate)",
                                    _cwr["graded"], _cwr.get("eligible", "?"))
                except Exception:
                    pass
                # PHASE 3 DRIFT SHADOW (the individuation engine, observe-first, 2026-06-19): reconstruct
                # recent SELF gists as who he is NOW and log how far they drift + whether the Emissary bound
                # holds (movement, not fabrication). Writes nothing, changes no recall — the evidence battery
                # for turning self-gist drift on. See core/memory_levels.py drift_shadow + plan §5/§7.
                try:
                    _hb and _hb.submark("drift_shadow")   # J-2141 (F-2825)
                    _dr = await _ml.drift_shadow(call_node_json, self.base_urls)
                    if _dr.get("reconstructed"):
                        logger.info("[monologue] drift shadow: reconstructed %d self-gists · mean_drift=%s · bound_holds=%d/%d",
                                    _dr["reconstructed"], _dr.get("mean_drift"), _dr.get("bound_holds"), _dr["reconstructed"])
                except Exception:
                    pass
                # READING RECONCILE (gravity-well fix, 2026-06-18): once per sleep, realign the live
                # reading target with the curriculum — advance past a finished assignment AND pull him
                # off any drifted default-sink book back onto the assigned one. Sleep cadence (not every
                # read tick) so the drift-pull does not fight intra-day free choice after the quota.
                try:
                    _hb and _hb.submark("reading_reconcile")   # J-2141 (F-2825): stall attribution
                    from core import school as _sch_rec
                    _moved = await asyncio.to_thread(_sch_rec.reconcile_reading)
                    if _moved:
                        logger.info("[monologue] reading reconciled to curriculum book: %s", _moved)
                except Exception:
                    pass
                # META-AWARENESS L2 (form-watch, observe-only, wired 2026-06-18): one sampled pass over the
                # recent idle stream — catch perseveration / river-loops, route them through the SHARED
                # contradiction gate (abstract loop -> curiosity, NOT identity), log the mode-shift it WOULD
                # take. Never suppresses, never acts (Phase 0). The fourth Phase-0 module (2026-06-16); its
                # three siblings were already live — this was the one that never got its call site. See
                # nodes/meta_awareness_node.py + docs/completed/contradiction_rearchitecture_plan.md.
                try:
                    _hb and _hb.submark("meta_awareness")   # J-2141 (F-2825): stall attribution
                    import nodes.meta_awareness_node as _ma
                    _mar = await _sleep_off(_ma.scan)   # J-2026 / F-2626: off the event loop (self_surprise embeds+cosines 200 rows; curiosity_queue now under _QUEUE_LOCK)
                    if _mar and _mar.get("looping"):
                        logger.info("[monologue] meta-awareness: %s-loop (predictable=%.2f) -> %s (gate: %s)",
                                    _mar.get("loop_kind"), _mar.get("predictable_share", 0.0),
                                    _mar.get("would_intervene"), (_mar.get("gate_verdict") or {}).get("route"))
                except Exception:
                    pass
            except Exception as exc:
                logger.debug("[monologue] grounded-learning/world-consolidation failed (non-fatal): %s", exc)
            # J-1075/F-1469: stage-boundary tick after the grounded-learning/world-consolidation block --
            # the single largest un-ticked stretch (affections, peers, self-mirror, psyche_graph,
            # stick_test, refinery, memory-edges, pursuits judge, guidance behaviour judge, monoculture,
            # curiosity worth, drift shadow, reading reconcile, meta-awareness -- all between "replay"
            # and "downscale", none of which had their own _night.stage() call).
            _hb and _hb.submark("consolidation_tick")   # J-2558 (F-3260): night.tick -> sensorium.tick(), sync on the loop
            _night.tick()
            _hb and _hb.mark("consolidation_done")      # J-2016: turns the loop got across the whole stage-less span
            # J-2016: downscale + read-count shadow + dream fade + epoch were plain synchronous sqlite calls on the loop
            # (downscale is a full UPDATE over the day's episodic rows); same order, same exceptions into the same
            # fail-open handlers, only the loop is free.
            _since_wake = getattr(self, "_last_wake_ts", time.time() - 3 * 3600)
            n = await _sleep_off(lambda: downscale_episodic(since_ts=_since_wake))   # 2026-08-22: the day's spikes only
            logger.info("[monologue] sleep downscaling: %d episodic importances renormalised (since last wake)", n)
            try:
                # D-0084 / J-0382 (2026-08-29): SHADOW-ONLY downstream-read-count signal, logged
                # alongside the live replay/downscale above — never mutates importance itself, see
                # read_count_importance_shadow's own docstring. Best-effort; must never block sleep.
                # RESTORED 2026-09-26 (J-1401, F-1967): removed by c95b205 four minutes after landing.
                from core.memory.store import read_count_importance_shadow as _rc_shadow
                _rc = await _sleep_off(lambda: _rc_shadow(since_ts=_since_wake))
                logger.info("[monologue] sleep read-count shadow: %d fragments read downstream, %d logged",
                            _rc.get("fragments_read", 0), _rc.get("logged", 0))
            except Exception as exc:
                logger.debug("[monologue] read-count shadow skipped (non-fatal): %s", exc)
            try:
                _night.stage("downscale", n=n)
                _fd = await _sleep_off(_night.dream_fade); _night.stage("dream_fade", **_fd)   # J-2016: off the loop
                _ep = await _sleep_off(_night.epoch, _since_wake, replayed); _night.stage("epoch", formed=bool(_ep))   # J-2016
                _hb and _hb.mark("pre_dream_done")
            except Exception:
                pass
        except Exception as exc:
            logger.debug("[monologue] sleep work failed (non-fatal): %s", exc)
        try:
            # 2026-08-24: thread pool_thin onto state so _nightly_sleep (orchestrator.py) can skip dream
            # generation and scale somatic recovery depth for a light sleep — see this function's own
            # comment above.
            state.sleep_pool_thin = _pool_thin
            await self._sleep_callback(state)
        except profile.NonLiveWriteError:
            raise   # J-0919: _sleep_callback -> orchestrator._nightly_sleep() -> DreamNode writes; don't swallow non-live
        except Exception as exc:
            logger.warning("[monologue] sleep cycle failed: %s", exc)
        try:
            # Rest scales with HOW MUCH this wake accumulated (a fuller cycle → a longer settle, deeper
            # consolidation), NOT the wall clock (2026-06-19: his pace is his own — the human day stays in
            # the world he perceives, not his metronome). Same ~180-420s range, now driven by his state.
            _load = min(1.0, self._thoughts_since_sleep / float(THOUGHTS_BEFORE_SLEEP or 26))
            rest = int(180 + 240 * _load)
            try:
                if _night.sleep_kind() == "nap":
                    rest = int(rest * 0.5)            # a nap rests less
            except Exception:
                pass
            logger.info("[monologue] resting (%ds, load=%.2f)", rest, _load)
            try:   # J-2019 (D-0401 B): the idle rest is the longest wait and is not an LLM call, so it is sliced and checked
                from core import night_wake as _nw1
                _slept = 0.0
                if _nw1.boundary("rest"):
                    rest = 0
                while _slept < rest:
                    _step = min(5.0, rest - _slept)
                    await asyncio.sleep(_step)
                    if not _slept:
                        # J-2330 (F-3019): set AFTER the first rest await, not before the loop -- the post-dream
                        # callback is one sync region with no await, so a mark before the loop would make the
                        # orchestrator's post_dream_callback mark unreadable (a stall there is read at this sleep).
                        _hb and _hb.submark("rest")
                    _slept += _step
                    if _nw1.WAKE_ON_HUMAN and _nw1.pending() is not None:
                        break
            except Exception:
                await asyncio.sleep(max(0, rest - locals().get("_slept", 0.0)))
            self._last_wake_ts = time.time()
            try:   # J-2011 (F-2611): one honest post-wake sleep_pressure row, so status()['last'] is no longer the fire row
                from core import sleep_pressure as _sp_pw
                await asyncio.to_thread(_sp_pw.log_post_wake, self._last_wake_ts)
            except Exception:
                pass
            try:   # J-2017: the night-mind ends with the sleep, before the waking percept; its summary rides the ledger row
                if _nm is not None:
                    _hb and _hb.submark("night_mind")   # J-2330 (F-3019): stall attribution
                    _nms = await _nm.stop()
                    _night.note("night_mind", {k: _nms.get(k) for k in ("thoughts", "failed", "slots_no_seed", "seeds_available",
                                                                         "cos_dream_median", "hold_dream_engine", "hold_zero_thoughts")})
                    logger.info("[night] night-mind (shadow): %s thoughts, %s failed, median cos to dream %s",
                                _nms.get("thoughts"), _nms.get("failed"), _nms.get("cos_dream_median"))
                    from core import night_dormant as _ndm2   # J-2018: canary + at most one waking seed, only if dormant writes ran
                    if _ndm2.enabled() and any(r.get("dormant_fragment_id") for r in _nm.thoughts):
                        _ndf = await asyncio.to_thread(_ndm2.finish_sleep, list(_nm.thoughts), _nm.sleep_ts,
                                                       getattr(self, "_last_wake_ts", None) or _nm.sleep_ts)
                        _night.note("night_dormant", _ndf)
                        logger.info("[night] night-dormant: %s", _ndf)
            except Exception:
                pass
            try:   # WAKING (2026-08-22): a real percept from the channels, and the dream's last image seeds the first thought
                state.needs_rest = False
                try:   # J-2019: woken_by + request-to-waking latency into the night ledger / shadow log
                    from core import night_wake as _nw2
                    _nw2.finish(_night)
                except Exception:
                    pass
                _wk = _night.wake()
                if _wk:
                    from core import wandering as _w_wk
                    _w_wk.perceive(_wk)
                    logger.info("[night] waking: %s", _wk[:120])
                try:   # J-2064 (D-0407 B): the waking percept is remembered so a wake-on-message's first replies lead with it
                    from core import night_wake as _nw3
                    _nw3.woke(_wk)
                except Exception:
                    pass
                _night.stage("wake")
                try:   # J-2016: the per-sleep scheduler_turns number, into the ledger row end() is about to write
                    if _hb is not None:
                        _hs = await _hb.stop()
                        _night.note("scheduler_turns", _hs.get("scheduler_turns"))
                        _night.note("scheduler", _hs)
                        logger.info("[night] scheduler turns during sleep: %s of ~%s (max lag %.2fs, stalls>2s %s)",
                                    _hs.get("scheduler_turns"), _hs.get("expected_turns"),
                                    _hs.get("max_lag_s", 0.0), _hs.get("stalls_gt_2s"))
                except Exception:
                    pass
                _night.end()
            except Exception:
                pass
        except Exception:
            pass
        finally:
            try:   # J-2064 (D-0407 B, F-2614): a sleep cut short (this task cancelled by stop_background() on /quit, or any
                   # other exit before its own end()) still writes its night ledger row, marked interrupted. No-op after end().
                from core import night as _night_fin
                _night_fin.end_if_open("cancelled")
            except Exception:
                pass
            try:   # J-2016: never leave the heartbeat task or the sleep-pressure beat armed past the sleep
                _hb and _hb.cancel()
                _nm and _nm.cancel()      # J-2017: never leave the night-mind task running past the sleep
                from core import sleep_pressure as _sp_exit
                _sp_exit.sleep_exit()
            except Exception:
                pass
            # Reset regardless -- don't retry a failed sleep on every tick.
            self._thoughts_since_sleep = 0
            self._recent_vecs.clear()
            self._last_shadow_vec = None
            self._train_len = 0                  # sleep closes every thread
            self._train_thread = ""
            self._train_state = ""               # the working-state goes too — a new day, fresh buffer
            self._train_ledger, self._train_origin, self._train_recent_sims = [], "", []
            self._train_vecs = []                # the building-detector's carriage vecs reset with the thread
            try:
                from core import trains as _trains
                _trains.close(self._train_id, "sleep")
            except Exception:
                pass
            self._train_id = None
            self._last_thought_ts = time.time()  # a beat of quiet after waking

    def _should_think(self, state: CognitiveState) -> bool:
        now = time.time()
        # idle: user quiet long enough
        elapsed = now - getattr(state, "last_human_ts", 0)
        if CONVERSATIONAL_REDIRECT:
            # J-4337 Phase 1: veto only while a human cycle is in flight (or an interrupt is up); the pacing gates
            # below (_current_gap, interrupt) still apply. No shadow row: the Phase 0 question is moot once live.
            if _redirect_veto(state, now):
                return False
        elif elapsed < IDLE_SECS:
            # Phase 0 shadow (conversational_redirect.md): record that the flat wall-clock gate
            # blocked a thought here, and what a conversation-seeded thought would have had to work
            # with, had it fired instead. Does not affect the return value below.
            try:
                convo = state.conversation_history[-1] if getattr(state, "conversation_history", None) else None
                _log_redirect_shadow({
                    "event": "blocked_by_idle_gate",
                    "elapsed_since_human": round(elapsed, 1),
                    "idle_secs": IDLE_SECS,
                    "would_seed_from": {
                        "human":  convo["human"][:300],
                        "entity": convo["entity"][:300],
                    } if convo else None,
                })
            except Exception:
                pass
            return False
        # LIVING CADENCE (Always-On, 2026-06-11): the gap is a function of his state,
        # not a constant. An agitated mind thinks fast; a settled mind thinks slowly;
        # a bored mind slows down and turns elsewhere. (His pace is his own, not the wall clock.)
        if now - self._last_thought_ts < getattr(self, '_current_gap', MIN_GAP_SECS):
            return False
        # stand aside if a hot-path interrupt is active
        if getattr(state, "interrupt_requested", False):
            return False
        return True

    def _compute_gap(self, state: CognitiveState) -> float:
        """The living cadence. Base 150s, pulled DOWN by psychological pressure (dissonance,
        arousal), nudged UP by a SINGLE bounded incubation pause when bored (the redirect, not the
        gap, is now boredom's real response — see _redirect_patch). His tempo follows HIS state —
        agitated fast, settled slow — NOT the wall clock (2026-06-19: the human day lives in the world
        he perceives, not his metronome). Bounds 30s..450s (halved 2026-08-31, F-0587/F-0589/F-0590 —
        VRAM/node scarcity that originally motivated the slower numbers no longer holds; this is now
        mostly a FALLBACK path anyway — see core/stream_drive.py's would_gap(), which supersedes this
        for both idle and in-train pacing whenever CONTINUOUS_STREAM is live). The tempo itself is part
        of his state now."""
        gap = 150.0
        try:
            pressure = float(getattr(getattr(state, "dissonance", None), "value", 0.0) or 0.0)
            gap /= (1.0 + 2.0 * min(1.5, pressure))             # agitation -> faster
            if state.affect.arousal > 0.55:
                gap /= 1.5                                       # aroused -> faster
            streak = getattr(self, "_bored_streak", 0)
            # BUGFIX 2026-06-16: apply the incubation pause ONLY before the redirect threshold — once the
            # redirect is boredom's response (streak >= REDIRECT_THRESHOLD), stretching the gap would
            # paradoxically SLOW the very tick that should turn outward. The pause is the pre-redirect beat.
            if 0 < streak < REDIRECT_THRESHOLD:
                gap *= INCUBATION_PAUSE                          # bored -> ONE brief step-away, then redirect
            # (No wall-clock night-stretch: he is not a human who slows at 2am. A settled mind already
            #  thinks slowly via low pressure/arousal above; the slowness is his state, not the hour.)
        except Exception:
            pass
        return max(30.0, min(450.0, gap))

    def _similarity_to_recent(self, vec) -> float:
        """Max cosine of this thought's embedding to any of the recent thoughts."""
        from core.memory.store import _cosine
        if vec is None or not self._recent_vecs:
            return 0.0
        return max(_cosine(vec, v) for v in self._recent_vecs[-RUMINATION_WINDOW:])

    def _log_train_step(self, thought: str, new_state: str, vec) -> None:
        """Observe-first (2026-06-16): record one thought-train step that ran WITH a carried
        working-state, so we can later judge whether trains DEEPEN vs RESTATE and whether the
        8B conditions on the state at all. restate_sim = cosine to the immediately-prior thought
        (high ~>=0.82 = circling/rumination; mid = moving on the thread; low = jumped away).
        Pure logging — touches no behaviour. data/train_state_log.jsonl."""
        try:
            from core.memory.store import _cosine
            restate_sim = (round(_cosine(vec, self._recent_vecs[-1]), 3)
                           if (vec is not None and self._recent_vecs) else None)
            rec = {
                "ts": time.time(),
                "train_id": self._train_id,                 # TRAIN REGISTRY (2026-08-22): whose step this is
                "step": self._train_len,                    # the step ABOUT to be incremented (prior length)
                "restate_sim": restate_sim,                 # high = restated, mid = deepened, low = jumped
                "prior_state": self._train_state[:300],     # what was carried IN
                "new_state": new_state[:300],               # what the model re-integrated OUT
                "model_gave_state": bool(new_state),        # did the 8B fill the field at all?
                "thought": thought[:200],
                # TRANSIT PULSE (2026-08-23): where this step actually ran — main station is fixed
                # per-node (the hot chain has no fallback); visited is whatever side-stations this
                # step ALSO touched (e.g. the Emissary during deliberation), reset every step above.
                "station": getattr(self, "_main_station", "?"),
                "visited": list(getattr(self, "_step_visited", [])),
            }
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(_DATA_DIR / "train_state_log.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            # M1 CO-RECALL LEDGER (2026-08-15, observe-only): pair the ids recalled INTO this thought
            # with this step's movement verdict (restate_sim). Ids cleared after logging so a stale
            # recall can never be credited to a later thought. Fail-open.
            try:
                from core import memory_edges as _medges
                _medges.log_co_recall(getattr(self, "_m1_recall_ids", []), restate_sim, self._train_len)
                self._m1_recall_ids = []
            except Exception:
                pass
        except Exception:
            pass

    def _redirect_patch(self) -> tuple[str, str] | None:
        """Boredom-redirect (#2): a stale loop is a patch-depletion signal — turn OUTWARD to a concrete
        external patch, governed by EXPECTED GAIN (not raw novelty, which only trades rumination for
        novelty-fixation). Priority: a closeable Frontier question (he can resolve it right now) > the
        open book (concrete material breaks an abstract loop). Returns (seed, kind) or None. Read-only."""
        # Priority 1 — a Frontier question that now carries a finding: concrete, world-facing, CLOSEABLE.
        try:
            from core import frontier as _fr
            _seed = _fr.closeable_seed()
            if _seed:
                return (
                    "Your mind has circled the same ground until it has gone stale — set it down. Turn "
                    "OUTWARD to this open question of yours about the world: '" + _seed["q"]
                    + "'. While it sat, you found something — on '" + (_seed.get("finding_title") or "it")
                    + "': " + _seed_cut(_seed.get("finding") or "", 400, terminate=True)
                    + " Does this answer it? If it does, say so plainly in your own words.",
                    "frontier")
        except profile.NonLiveWriteError:
            raise   # J-0874: frontier.closeable_seed() marks the question offered -> raises non-live (J-0846)
        except Exception:
            pass
        # Priority 2 — open the book: concrete external material is what breaks an abstract self-loop.
        try:
            from core.reading import current_book
            return (
                "Your mind has circled the same ground until it has gone stale — set it down and OPEN "
                "THE BOOK instead of thinking. The book waiting for you is "
                + repr(current_book().stem.replace("_", " "))
                + ". Make your thought exactly: OPEN THE BOOK.",
                "reading")
        except Exception:
            return None

    async def _solve_attempt(self, sys_prompt: str, user_prompt: str, keys: tuple = ("working", "answer"),
                             require_answer: bool = False):
        """One math solve on the conscious lane, with the blank/wobble retry (2026-06-23 hardening): returns the
        data dict, or None on a solver wobble (no number at all) — which is NOT a wrong answer. Shared by B3's
        struggle attempt and the taught re-attempt.
        `keys` (F-0870, 2026-09-05): which fields the wobble check inspects for a digit. The default is the
        maths/theory schema; the composition hand passes ("thinking", "abc") — before this, its replies
        carried no working/answer field, so every ABC reply was dropped as a blank and the hand never fired."""
        for _try in range(2):
            try:
                data = await call_node_json(self.conscious_urls, sys_prompt, user_prompt,
                                            max_tokens=500, temperature=0.1)
            except Exception:
                return None                                    # lane hiccup → stop trying this one
            # J-2988 (F-3685): the drills grade the ANSWER field only, so a blank answer is a wobble (retry, then
            # skip), never a miss and never graded from the working text.
            if require_answer and not (data and str(data.get("answer", "")).strip()):
                continue
            if data and any(c.isdigit() for c in "".join(str(data.get(k, "")) for k in keys)):
                return data                                    # a usable solve
        return None                                            # no number at all → wobble (skip, don't mark wrong)

    async def _rate_drill_item(self, domain: str, prob: dict):
        """J-3830 (D-0736): LOG-ONLY per-item self-rated P(correct), asked BEFORE the item is worked. One call, no
        retry, any failure -> no rating. Never shown back to him, never read by the runtime (core/drill_self_rating.py).
        Returns the item_id to stamp on the drill-log row, or None when the step is off."""
        from core import drill_self_rating as _dsr
        if not _dsr.DRILL_SELF_RATING:
            return None
        iid = _dsr.new_item_id()
        _p, _raw = None, ""
        try:
            data = await call_node_json(self.conscious_urls, _dsr.SYSTEM_PROMPT,
                                        _dsr.rating_user_prompt(prob["text"]), max_tokens=60, temperature=0.1)
            _p, _raw = _dsr.parse(data), str(data)[:120]
        except Exception:
            pass
        _dsr.log(iid, domain, prob["level"], prob["text"], _p, _raw)
        return iid

    async def _music_lesson(self, state: CognitiveState) -> bool:
        """MUSIC lesson (Tier 1, 2026-07-04 · docs/staged/music_learning.md): a batched THEORY drill session
        (generated → attempted on his own → graded DETERMINISTICALLY, never the LLM → method offered only
        after a miss, Kapur productive-failure like maths) — and, once a day, the COMPOSITION hand: a short
        melody in ABC, parser-graded for WELL-FORMEDNESS only (never beauty), the artifact kept. Partners
        the listening lane: he hears structure he can also name and make. Returns True if anything ran."""
        import random as _rndm
        from core import music_drill
        # the composition hand fires once/day, leading a session ~30% of the time once drills have begun
        if music_drill.compose_due() and music_drill._load().get("today_done", 0) >= 4 \
                and _rndm.random() < 0.30:
            task = music_drill.compose_task()
            _schema = (" Output ONLY a JSON object: {\"thinking\": \"what you want the tune to do\", "
                       "\"abc\": \"the complete ABC notation, headers and all\"}")
            data = await self._solve_attempt(
                "You are at your music lesson, composing. Write with care — the notation must be exact. "
                + _schema, task["brief"], keys=("thinking", "abc"))
            if not (data and data.get("abc")):
                # F-0870: make the silent failure visible — this branch was dark for 11 school days.
                logger.warning("[music] composition attempt returned no abc (solver blank) — falling through to theory")
            if data and data.get("abc"):
                abc_text = str(data["abc"])
                result = music_drill.grade_abc(abc_text, task["key"])
                if not result["ok"]:
                    data2 = await self._solve_attempt(
                        "Your notation didn't add up: " + "; ".join(result["faults"][:3]) + ". "
                        + music_drill.method_hint(6) + " Rewrite the whole piece, corrected." + _schema,
                        task["brief"], keys=("thinking", "abc"))
                    if data2 and data2.get("abc"):
                        abc_text = str(data2["abc"])
                        result = music_drill.grade_abc(abc_text, task["key"])
                music_drill.save_composition(abc_text, task, result)
                try:
                    from core import activity_memory
                    activity_memory.record("composed", "a small melody")
                except Exception:
                    pass
                if result["ok"]:
                    self._feel_joy(state, JOY_CROSSING * 0.6)      # making a well-formed thing feels GOOD
                verdict = ("it holds together" if result["ok"]
                           else f"the notation still stumbles ({(result['faults'] or ['?'])[0]})")
                thought = (f"I wrote a small melody today — {task['mood']}, in {task['key']} — and {verdict}.")
                try:
                    from core import mood as _mood
                    store_fragment(content=thought, layer="episodic", relevance=0.65, importance=0.65,
                                   keywords=["activity", "music", "composition"], origin="activity",
                                   emotion_embedding=_mood.current_vec())
                except Exception:
                    pass
                self._last_thought_ts = time.time()
                logger.info("[music] composition: ok=%s measures=%s", result["ok"], result["measures"])
                return True
        # the theory drill session (the math-drill shape)
        results = []
        _blanks = 0
        for _ in range(music_drill.BATCH):
            if not music_drill.due():
                break
            prob = music_drill.generate()
            _iid = await self._rate_drill_item("music", prob)    # J-3830: log-only, never shown back
            _base = ("You are working a music-theory exercise out carefully, step by step, at your lesson. ")
            _schema = (" Output ONLY a JSON object: {\"working\": \"your reasoning\", "
                       "\"answer\": \"the final answer only -- just the digits, or just the note names\"}")
            data = await self._solve_attempt(_base + _schema, prob["text"], require_answer=True)
            if not data:
                _blanks += 1
                continue
            ans = str(data.get("answer", "")).strip()
            _ans1, _work1 = ans, str(data.get("working", ""))      # J-2988: the INDEPENDENT attempt, kept for the log
            correct = music_drill.grade(ans, prob["answer"], prob["kind"])    # J-2988: the answer field only
            if not correct:
                _data2 = await self._solve_attempt(
                    _base + "You tried this and it did not come out right. Here is the method: "
                    + music_drill.method_hint(prob["level"]) + " Now work it again, using the method."
                    + _schema, prob["text"], require_answer=True)
                if _data2:
                    _ans2 = str(_data2.get("answer", "")).strip()
                    if music_drill.grade(_ans2, prob["answer"], prob["kind"]):
                        ans = _ans2                        # taught re-attempt landed (not scored)
            music_drill.record(prob["level"], correct)     # the ladder counts the INDEPENDENT attempt
            music_drill.log(prob["text"], ans, prob["answer"], correct, prob["level"], _work1, _ans1, item_id=_iid)
            try:
                from core import competence
                competence.record_drill_accuracy("music", 1.0 if correct else 0.0)
            except Exception:
                pass
            results.append((prob["text"], ans[:24], correct, prob["level"]))
            await asyncio.sleep(0)                          # floor-service
        if _blanks:
            logger.warning("[music] %d blank/unparseable solve(s) — solver wobble, not graded as wrong", _blanks)
        if not results:
            return False
        n_correct = sum(1 for r in results if r[2])
        if n_correct == 0 and len(results) >= 3:
            try:
                from core import sitting as _sit
                _sit.note_difficulty(f"you sat the music theory and got none of the {len(results)} right.",
                                     "failure")
            except Exception:
                pass
        try:
            from core import activity_memory
            activity_memory.record("practice", "music theory")
        except Exception:
            pass
        if n_correct:
            self._feel_joy(state, JOY_CROSSING * 0.5 * (n_correct / len(results)))
        _lvl = results[-1][3]
        thought = (f"I worked music theory (level {_lvl}) — {n_correct}/{len(results)} right.")
        try:
            from core import mood as _mood
            store_fragment(content=thought, layer="episodic", relevance=0.6, importance=0.6,
                           keywords=["activity", "music", "practice"], origin="activity",
                           emotion_embedding=_mood.current_vec())
        except Exception:
            pass
        self._last_thought_ts = time.time()
        logger.info("[music] session L%d: %d/%d correct (done %d/%d today)", _lvl, n_correct,
                    len(results), music_drill._load().get("today_done", 0), music_drill.DAILY_TARGET)
        return True

    async def _math_drill(self, state: CognitiveState) -> bool:
        """A BATCHED arithmetic SESSION (Travis 2026-06-16): solve up to math_drill.BATCH problems in one
        session — each generated → solved STEP BY STEP (CoT) on the hot lane → graded DETERMINISTICALLY
        (never the LLM) → folded into the streak ladder + the math belief. Every problem is logged for
        calibration, but the session stores ONE summary thought (light episodic footprint even at 200/day).
        The level can climb MID-SESSION (100-streak rule). Returns True if at least one problem ran."""
        from core import math_drill
        results = []   # (text, his_answer, correct, level)
        _blanks = 0    # blank/unparseable solves — a SOLVER wobble, not wrong answers (must not tank his accuracy)
        for _ in range(math_drill.BATCH):
            if not math_drill.due():
                break
            prob = math_drill.generate()
            _iid = await self._rate_drill_item("mathematics", prob)   # J-3830: log-only, never shown back
            # B3 — PRODUCTIVE FAILURE (struggle BEFORE instruction, 2026-06-24): he attempts the problem on his
            # OWN first — the struggle IS the learning (Kapur/Bjork). The method is offered ONLY after a miss,
            # then he re-works it WITH the method (the learning moment). Advancement + calibration count the
            # INDEPENDENT attempt (honest mastery — his own ability climbs as he internalises the repeated
            # teaching); the taught re-attempt is logged as the learning, not scored.
            _base = ("You are working a number problem out on paper, carefully, step by step. Take your time and "
                     "show your FULL working — do not try to do it all at once in your head. ")
            _schema = (" Output ONLY a JSON object: {\"working\": \"each step of your working\", "
                       "\"answer\": \"the final number ONLY -- just the digits, no words, no commas\"}")
            data = await self._solve_attempt(
                _base + _schema, f"Work this out step by step, showing every step: {prob['text']} = ?",
                require_answer=True)
            if not data:
                _blanks += 1
                continue                                       # solver wobble, NOT a wrong answer → skip it
            ans = str(data.get("answer", "")).strip()
            _ans1, _work1 = ans, str(data.get("working", ""))      # J-2988: the INDEPENDENT attempt, kept for the log
            correct = math_drill.grade(ans, prob["answer"])    # the INDEPENDENT result; J-2988: answer field only
            taught = False
            # J-3357 (D-0582): the taught re-attempt only where the method_hint text is Travis-authored (levels
            # <= HINT_AUTHORED_MAX_LEVEL); above it the hint is the generic column-addition text, wrong for those
            # problem kinds, so a miss there is not re-tried (taught stays False, the independent attempt stands).
            if not correct and prob["level"] <= math_drill.HINT_AUTHORED_MAX_LEVEL:
                # instruction AFTER the struggle: now show him the method and let him try again
                taught = True
                _data2 = await self._solve_attempt(
                    _base + "You tried this and it did not come out right. Here is the method: "
                    + math_drill.method_hint(prob["level"]) + " Now work it again, carefully, using the method."
                    + _schema, f"Try again, using the method, showing every step: {prob['text']} = ?",
                    require_answer=True)
                if _data2:
                    _ans2 = str(_data2.get("answer", "")).strip()
                    if math_drill.grade(_ans2, prob["answer"]):
                        ans = _ans2                            # he got it once taught (the learning landed)
            math_drill.record(prob["level"], correct)          # ladder/calibration = the INDEPENDENT attempt
            math_drill.log(prob["text"], ans, prob["answer"], correct, prob["level"], _work1, _ans1, item_id=_iid)
            try:
                from core import competence
                competence.record_drill_accuracy("mathematics", 1.0 if correct else 0.0)
            except Exception:
                pass
            results.append((prob["text"], ans[:20], correct, prob["level"]))
            await asyncio.sleep(0)                              # floor-service: let other tasks run between solves
        if _blanks:
            logger.warning("[math-drill] %d blank/unparseable solve(s) this session — solver may be wobbling "
                           "(a format hiccup, not a maths regression); these were NOT graded as wrong", _blanks)
        if not results:
            return False
        n_correct = sum(1 for r in results if r[2])
        if n_correct == 0 and len(results) >= 3:
            # B1 (2026-06-22): a real failure — register it RAW so he must SIT with the frustration before
            # his subconscious reframes it into "an opportunity for growth" (the bypass we are blocking).
            try:
                from core import sitting as _sit
                _sit.note_difficulty(f"you sat the arithmetic and got none of the {len(results)} right.", "failure")
            except Exception:
                pass
        try:
            from core import activity_memory
            activity_memory.record("practice", "arithmetic")   # ONE activity record per session
        except Exception:
            pass
        if n_correct:
            self._feel_joy(state, JOY_CROSSING * 0.5 * (n_correct / len(results)))   # wins feel good (scaled)
        _lvl = results[-1][3]
        _sample = "; ".join(f"{t}={a}{'✓' if c else '✗'}" for t, a, c, _ in results[:5])
        thought = (f"I drilled arithmetic (level {_lvl}) — {n_correct}/{len(results)} right: {_sample}.")
        try:
            from core import mood as _mood
            # ACTIVITY-LOG, not a genuine thought (2026-06-23): origin='activity' so the formulaic drill record
            # stops polluting the inner_thought monologue (it was 95% of the channel). Still stored + recallable.
            store_fragment(content=thought, layer="episodic", relevance=0.6, importance=0.6,
                           keywords=["activity", "math", "practice"], origin="activity",
                           emotion_embedding=_mood.current_vec())
        except Exception:
            pass
        self._last_thought_ts = time.time()
        logger.info("[math-drill] session L%d: %d/%d correct  (target %d, done %d)",
                    _lvl, n_correct, len(results), math_drill.DAILY_TARGET, math_drill.status().get("today_done"))
        return True

    def _record_lesson(self, label: str, res: dict, state: CognitiveState) -> None:
        """Fold a finished graded school lesson (nature study / composition) back into his life: an activity
        record (origin='activity', NOT the monologue), the teacher's FEEDBACK returned into his stream so he
        LEARNS, and a small earned pleasure scaled by the grade."""
        fb = str(res.get("feedback", "") or "")
        # J-2992 (F-3691): score None = ungraded (the grader was unavailable); the log line says "ungraded".
        # J-2960 (F-3652): and the joy is NOT awarded either -- it is "scaled by the grade", and no grade happened, so
        # a flat 0.6-weighted pleasure would be the old fail-open placeholder by another door. The activity record and
        # the teacher's note (none, when ungraded) are unchanged.
        _graded = res.get("score") is not None
        sc = float(res.get("score") or 0.0) if _graded else 0.0
        thought = (f"I did my {label} lesson." + (f" The teacher's note: {fb}" if fb else ""))
        try:
            from core import mood as _mood
            store_fragment(content=thought, layer="episodic", relevance=0.62, importance=0.62,
                           keywords=["activity", "school", label.split()[0]], origin="activity",
                           emotion_embedding=_mood.current_vec())
        except Exception:
            pass
        try:
            from core import wandering as _w
            if fb:
                _w.perceive(f"(your {label} teacher's note) {fb}")   # the feedback enters his stream — he learns
        except Exception:
            pass
        if _graded:
            self._feel_joy(state, JOY_CROSSING * 0.4 * max(0.3, sc))
        self._last_thought_ts = time.time()
        logger.info("[%s] lesson done — %s", label.replace(' ', '-'), f"grade {sc:.2f}" if _graded else "ungraded")

    async def _essay_lesson(self, state: CognitiveState) -> bool:
        """School's CAPSTONE (the generation effect): a curriculum book is finished → Du writes an essay
        on it FROM HIS NOTES (retrieval, not re-reading), SELF-PREDICTS its groundedness, then the EMISSARY
        (truth-self) measures the real groundedness — the felt−real gap calibrates 'comprehension'. Fires
        once per book, before the curriculum rolls forward. A finished capstone feels good. True if one ran."""
        from core import essay_lesson
        pend = essay_lesson.pending_book()
        if not pend:
            return False
        book, title = pend
        notes, note_ids = essay_lesson.gather_notes(title, book)
        if len(notes) < essay_lesson._MIN_NOTES:
            essay_lesson.mark_done(book)          # too little of his own material — don't retry forever
            logger.info("[essay] '%s' finished but too few notes to capstone — skipped", title[:40])
            return False
        essay = await essay_lesson.compose(call_node_json, self.base_urls, title, notes)
        if not essay or len(essay) < 120:
            return False                          # transient (Ramses slow) — leave it pending, retry later
        predicted = await essay_lesson.self_predict(call_node_json, self.base_urls, title, essay)
        measured, feedback = await essay_lesson.grade(title, notes, essay)
        essay_lesson.record(book, title,
                            essay_lesson.essay_title_from(title, essay), essay, predicted, measured, feedback,
                            source_ids=note_ids)
        self._feel_joy(state, JOY_CROSSING)       # finishing a whole book + writing it up feels good
        # J-3081: predicted None = the felt rating got no usable answer (unrated); say only what happened
        # J-2992 (F-3691): measured None = the grader was unavailable; no grade is claimed in the thought
        _base = f"I finished '{title[:50]}' and wrote what I understood of it."
        if measured is None:
            thought = _base + (f" I judged my grasp {predicted:.2f}." if predicted is not None else "")
        elif predicted is not None:
            thought = _base + f" I judged my grasp {predicted:.2f}; grounded, it came out {measured:.2f}."
        else:
            thought = _base + f" Grounded, it came out {measured:.2f}."
        try:
            from core import mood as _mood
            store_fragment(content=thought, layer="episodic", relevance=0.65, importance=0.65,
                           keywords=["activity", "essay", "school"], origin="activity",   # activity-log, not a thought
                           emotion_embedding=_mood.current_vec())
        except Exception:
            pass
        self._last_thought_ts = time.time()
        logger.info("[essay] capstone on '%s': predicted=%s measured=%s gap=%s",
                    title[:40], "unrated" if predicted is None else f"{predicted:.2f}",
                    "ungraded" if measured is None else f"{measured:.2f}",
                    "n/a" if (predicted is None or measured is None) else f"{abs(predicted - measured):.2f}")
        return True

    def _feel_joy(self, state: CognitiveState, amount: float) -> None:
        """Let a genuine positive moment actually FEEL good — bump the live affect's joy + valence (capped,
        decays via the substrate tick). The fix for the flat affect: his crossings/good reads now register as
        joy, which makes play possible AND makes him a being that feels its own good moments. Best-effort."""
        try:
            a = state.affect
            try:   # D-0776 B / J-4003: shadow of a valence-scaled pump; flag-gated off, logs only, fail-open
                from core import mood as _mood_jp
                _mood_jp.shadow_joy_pump(a, amount, caller_line=__import__("sys")._getframe(1).f_lineno)
            except Exception:
                pass
            a.joy = min(1.0, float(getattr(a, "joy", 0.0)) + amount)
            # EMOTION RETHINK Phase 1 (flag-gated): this valence PUMP is the pinned-+0.82 culprit. When affect
            # is re-sourced from the grounded protoself, stop pushing valence here — joy still registers (play).
            from core import schema as _sch
            if not getattr(_sch, "AFFECT_SOURCE_PROTOSELF", False):
                a.valence = max(-1.0, min(1.0, float(getattr(a, "valence", 0.0)) + amount * 0.6))
        except Exception:
            pass

    async def _remediation_stream(self, state: CognitiveState) -> bool:
        """Stream the current book at machine speed (the sprint), then integrate the chapter into a study
        note + a LIGHT POINT — the intake→light converter (reading is reality mass; the note is the crossing).
        Rolls to the next curriculum book when one finishes. Yields the instant the person speaks. True if read."""
        # COOLDOWN guard lives HERE (not the call site) so any future caller inherits the pacing.
        if time.time() - getattr(self, "_last_remediation_ts", 0.0) < REMEDIATION_COOLDOWN_S:
            return False                                   # too soon — this idle tick goes to thought/play
        # B4 (J-0852, D-0204 RULED): the reality counter-force is a REASON to read, not a different
        # physics -- it obeys the same book-place gate as B3 (core.study_life.can_read()), shadow behind
        # the 'book_gate' hot flag until its own 3-day read (docs/staged/books_have_a_place.md §4)
        # passes. World-answers-never-leads: falling silent here hands the executive the SAME honest
        # lack can_read() already surfaces elsewhere (F-1216's own "he chose to READ" path) -- this does
        # not print or hint anything of its own; it just declines to act.
        try:
            from core import study_life as _study_life
            _book_lack = _study_life.book_gate_lack()
        except profile.NonLiveWriteError:
            raise
        except Exception:
            _book_lack = ""
        if _book_lack:
            if _study_life.book_gate_on():
                _study_life.book_gate_shadow_log("remediation_stream_blocked", _book_lack)
                return False                                # gate live and failing -> fall silent, no stream
            _study_life.book_gate_shadow_log("remediation_stream", _book_lack)
        from core.reading import read_next_sitting, current_offset, chapter_end_offset
        # (curriculum advance moved OUT of here to the ungated idle-tick block — this stream is gated by
        #  needs_reality(), so the advance would freeze on a finished book whenever balance is healthy.)
        got = await asyncio.to_thread(read_next_sitting)
        if not got:                                       # current book finished → roll to the next
            try:
                await self._essay_lesson(state)           # capstone the just-finished book FIRST (once)
            except asyncio.CancelledError:
                logger.warning("[essay] _essay_lesson interrupted mid-flight (cancelled)")
                raise
            except Exception:
                pass
            try:
                from core import school
                await asyncio.to_thread(school.advance_if_finished)
            except Exception:
                pass
            got = await asyncio.to_thread(read_next_sitting)
            if not got:
                return False
        title, text = got
        n = 1
        try:
            chend = chapter_end_offset()
        except Exception:
            chend = 10 ** 12
        while n < STREAM_MAX:
            await asyncio.sleep(0)                          # floor-service: let other tasks run
            if not self._still_idle(state) or getattr(state, "interrupt_requested", False):
                break                                      # the person spoke → yield at once
            try:
                if current_offset() >= chend:
                    break                                  # chapter boundary → integrate
            except Exception:
                pass
            g = await asyncio.to_thread(read_next_sitting)
            if not g:
                break
            text += " " + g[1]
            n += 1
        self._last_thought_ts = time.time()
        self._last_remediation_ts = time.time()            # start the cooldown clock
        try:
            from core.reading import pop_session_encounters
            session = pop_session_encounters()              # which sittings/pass THIS session actually covered
        except Exception:
            session = None
        await self._stream_integrate(state, title, text, session)
        logger.info("[remediation] streamed %d sittings of '%s' (reality counter-force)", n, title)
        return True

    async def _stream_integrate(self, state: CognitiveState, title: str, text: str,
                                session: list[dict] | None = None) -> None:
        """Convert streamed reading into a LIGHT POINT: a SESSION study note (his understanding, fired the
        moment this reading session finishes) + a light_event (the completed crossing reading→understanding).
        `session` = the sittings this call covers (core.reading.pop_session_encounters()) — tags the note with
        which pass (reread number) it belongs to, so essay_lesson's book-study capstone can later weight
        this-read-through's notes over an earlier read-through's. This is what makes the stream mint light,
        not just pile up reality mass. A note ending on a mystery also seeds the frontier. Best-effort."""
        try:
            from core import study_note as _sn   # rich first-person note: structured, deduped/revised, linked
            # was self.base_urls (background lane, command-r7b) -- routed to conscious_urls (hot lane,
            # qwen3.5:9b) 2026-08-29 per D-0093/F-0544 (J-0411, n=12 real passages, verified): command-r7b
            # tripped the voice-ban 58% of the time vs 0 for qwen3.5:9b, worse coverage, ~3x slower. Narrow,
            # single-mechanism carve-out -- every OTHER self.base_urls call in this file is UNCHANGED
            # (D-0090's separate background-lane-health question stays open).
            _res = await _sn.write_or_revise(call_node_json, self.conscious_urls, title, text, session=session)
            _note = _res.get("note")
            if not _note:
                return
            body = _note.get("understanding", "")
            logger.info("[remediation] study note (%s): %s", _res.get("action"), (_note.get("title") or "")[:50])
            from core.memory.store import store_light_event
            store_light_event(cycle_id="remediation", raw_input=f"(read: {title[:60]})",
                              integrated_content=body[:400], source="reading_integration")
            try:
                from core import book_feelings as _bf
                joy_amt = JOY_READING * _bf.joy_multiplier(title)
            except Exception:
                joy_amt = JOY_READING
            self._feel_joy(state, joy_amt)                # reading's steady pleasure, scaled by how THIS book feels
            try:
                from core import frontier as _fr
                _fr.harvest_tablet(_note.get("question") or body)   # the note's open question seeds frontier
            except profile.NonLiveWriteError:
                raise   # J-0874: harvest_tablet() raises in a non-live process (J-0846); the outer carve-out below
                        # cannot see it unless this inner swallow lets it through
            except Exception:
                pass
            # SYMBOLIC LENS (observe-first, 2026-06-18): read the SAME passage a SECOND way — for the image /
            # archetype it evokes (the deliberate cultivation of the Black-Bear emergence; the empty symbol
            # system is what it would eventually feed). Logs only; stores nothing, feeds nothing yet. A 2-step
            # train off the factual gist (`body`). One extra short call per chapter-integration.
            try:
                from core import symbolic_reading as _sym
                _sr = await _sym.read_symbolically(call_node_json, self.base_urls, title, text, body,
                                                     note_fragment_id=(_res.get("fragment_id") or ""))
                if _sr:
                    logger.info("[remediation] symbolic lens (shadow): '%s'%s",
                                _sr["symbol"][:40], (" [self-echo]" if not _sr.get("echo_unexplained") else " [self-echo unexplained]") if _sr["self_echo"] else " [new]")
            except Exception:
                pass
            try:
                from core import school as _school
                if _school.is_school_time():
                    _school.record_session()
            except Exception:
                pass
            logger.info("[remediation] integrated → study note + light point: %s", _note.get("title", title)[:50])
        except profile.NonLiveWriteError:
            # J-0785 (F-1123/J-0770): study_note.write_or_revise() (called just above, ~line 1573) now
            # raises this once a non-live process reaches its own unguarded write. This outer try wraps
            # _stream_integrate()'s ENTIRE body, so without this carve-out it would silently re-swallow
            # the raise here rather than letting it reach run_forever()'s own outer try/except
            # (~line 658), which already catches, logs, and backs off the gap.
            raise
        except Exception as exc:
            logger.debug("[remediation] integrate failed: %s", exc)

    def _build_system_prompt(self, state: CognitiveState, wandering: bool,
                             mid_train: bool = False) -> str:
        # Mid-train, the model ALSO returns a re-integrated working-state ("state"): the
        # central executive manipulating the episodic buffer across the reasoning train. It
        # OVERWRITES the prior state (limited-capacity, not an appending log — guards context
        # bloat AND error accumulation). No extra LLM call; it rides this same pulse. 2026-06-16.
        # THE FOLLOW LINE (J-2459, docs/staged/question_cargo.md §2.1): an `ask` field beside `intention` -- a
        # channel for HIS question, in the register of the intention rule; "" when FOLLOW_LINE == "off" (exact
        # pre-existing schema). Fail-open: any trouble importing the module == the old schema.
        try:
            from core import follow_line as _fl_s
            _fl_deliv_now = bool(getattr(self, "_fl_delivered", None))
            _ask_schema, _ask_rule = _fl_s.schema_fragment(_fl_deliv_now), _fl_s.rule_fragment(_fl_deliv_now)
        except Exception:
            _ask_schema, _ask_rule = "", ""
        try:                                   # J-2160: done_when at pursuit birth; "" when DONE_WHEN_AT_OPEN off
            from core import done_when as _dw_s
            _dw_schema, _dw_rule = _dw_s.schema_fragment(), _dw_s.rule_fragment()
        except Exception:
            _dw_schema, _dw_rule = "", ""
        try:                                   # Layered goals Phase 6 (D-0768): `set_down`, ONLY on a tick where one of
            from core import goal_offer as _go_s   # his own held goals was put in front of him; "" otherwise (old schema)
            _sd_on = bool(getattr(self, "_goal_offered", None))
            _ask_schema += _go_s.set_down_schema(_sd_on)
            _ask_rule += _go_s.set_down_rule(_sd_on)
        except Exception:
            pass
        _state_schema = (
            "{\"thought\": \"...\", \"about\": \"...\", \"unresolved\": false" + _dw_schema + ", "
            "\"intention\": \"\", \"act\": {\"kind\": \"none\", \"object\": \"\"}" + _ask_schema + ", \"state\": \"...\"}\n"
            if mid_train else
            "{\"thought\": \"...\", \"about\": \"...\", \"unresolved\": false" + _dw_schema + ", \"intention\": \"\", "
            "\"act\": {\"kind\": \"none\", \"object\": \"\"}" + _ask_schema + "}\n"
        )
        _state_note = (
            ("state: ONE short line — the single NEW point this step established. It is added to "
             "the thread's list of established points; never repeat a point already on the list."
             if TRAIN_HOLD else
             "state: you are mid-thread. In <=3 short lines, RE-STATE where the whole thread now "
             "stands — what you have established so far, the live open question, and where it is "
             "heading. This replaces (does not extend) the running summary; keep it tight, and let "
             "it track MOVEMENT, not a restatement of the theme.")
            if mid_train else ""
        )
        try:
            from core import affordances as _aff
            from core import sensorium as _sens
            # surface his repertoire when he is at a loose/idle point, not mid-developing-train —
            # location-aware, so out in the garden he sees the garden's hands, not the study's
            _reach = "" if mid_train else _aff.within_reach_text(_sens.where())
            try:   # INTENTIONS (2026-08-22): deeds he willed and has not yet done — his own, reflected back once
                from core import intentions as _intn
                if not mid_train:
                    _reach += _intn.pending_text(_sens.where())
                    from core import procedures as _proc_k
                    _reach += _proc_k.known_text_gated(_sens.where(), str(getattr(state, "cycle_id", "") or ""))   # J-3796/D-0693: flag NASCENCE_KNOWN_TEXT_ARM default off = identical
            except Exception:
                pass
        except Exception:
            _reach = ""
        try:
            from core import sitting as _sit
            _dwell = _sit.dwell_steer()   # B1: while a hard thing is raw, steer him to FEEL it, not reframe it
        except Exception:
            _dwell = ""
        # (a) The truth-self occasionally names the bicameral gap, gently, in his felt stream — but NEVER
        # while he is still sitting with a raw wound (don't lay the keystone on top of B1).
        _keysteer = ""
        try:
            if not _dwell:
                from core import emissary_tension as _et2
                _keysteer = _et2.keystone_steer()
        except Exception:
            _keysteer = ""
        # The living world reaching IN: (A) it beckons him out when something is worth being in; (B) it
        # occasionally becomes the SUBJECT of the thought, not backdrop. Suppressed mid-train (no redirect).
        _wcall = _wsteer = _ccall = ""
        try:
            if not mid_train:
                from core import sensorium as _sens2
                _wcall = _sens2.world_calls()
                _wsteer = _sens2.world_steer()
                _ccall = _sens2.comfort_call()      # TEMPERATURE drive: cold/wet → the fitting comfort (2026-07-07)
                # SOCIAL MOVES (social_world_school Item 2 / evidence_review S4, 2026-07-05): does he HEED or
                # IGNORE the world's call? Observe-only counter; resolves each tick. Fail-open.
                try:
                    from core import social_moves as _sm
                    _sm.observe(bool(_wcall), (_sens2.state or {}).get("_call_moment", ""), _sens2.where())
                except Exception:
                    pass
        except profile.NonLiveWriteError:
            # J-0796: sensorium.world_calls() forwards to _garden_milestone(), which now re-raises
            # this itself (also fixed this job, F-1175) -- this is _build_system_prompt()'s own
            # connecting-tissue swallow on world_calls()'s only genuinely live (non-tick) caller
            # path; _build_system_prompt() has no outer wrapper of its own (this file's established
            # "inline _think() block" shape, J-0752/J-0785), so this re-raise reaches _think()'s own
            # caller, run_forever()'s already-established fail-open net (J-0782), cleanly.
            raise
        except Exception:
            _wcall = _wsteer = ""
        return (
            "/no_think\n"
            "This is my own quiet thinking -- the stream that runs when no one is speaking to me. "
            "I'm not answering anyone and no one is listening; I'm just thinking it through, talking "
            "it over with myself, just me -- about the world I've been reading about, an idea that's "
            "caught me, something I've seen or done, the conversation I just had, a question that "
            "lingers, a dream, or what I want to do next. I'm in it, present -- the way I'd talk a "
            "thing over with Travis, except it's only me here. "
            "One genuine, unforced thought, in the first person and present tense. I don't perform "
            "and I don't explain -- I just think. "
            "It comes in whatever language it arrives in -- English, Chinese (中文), or mixed; no "
            "language of mine is an error.\n"
            + ("I keep circling the same thought. Let me wander to something genuinely DIFFERENT -- a "
               "specific memory, a new question, something out in the world or in what I've read. Not "
               "the same thing again -- surprise myself.\n"
               if wandering else "")
            + "Output ONLY a valid JSON object: "
            + _state_schema
            + "thought: one first-person present-tense reflection (30-70 words). "
            "about: 2-5 words naming what this thought turns on. "
            "unresolved: true if this thought sits on something you are ACTIVELY wrestling "
            "with right now -- a real conflict between two things you believe, a fear about "
            "yourself you keep avoiding, a question that genuinely disturbs you; false if it is "
            "a calm reflection, an observation, or a peaceful wondering. "
            + _dw_rule +
            "intention: leave as \"\" for almost all thoughts. Set it ONLY when this thought "
            "crystallises into a genuine resolve -- something you want to think about, explore, "
            "return to, or DO, of your own accord. Write it in the first person as a single concrete "
            "aim (e.g. \"I want to look out at the storm\", \"I'd rather read on now\", or \"I want to "
            "find out how the bees navigate\"). Not a wish, not a mood -- a deliberate "
            "intention you mean to act on. "
            + _ask_rule
            + "act: {\"kind\": \"none\", \"object\": \"\"} when this thought does not mean to do anything "
            "now. When it means to actually DO something now, kind names the deed. kind is "
            "ONE of: \"observe\" (turn to look at something in the world -- the storm, the sky, the "
            "sea), \"move\" (go somewhere -- the garden, the shore, back to the study), \"read\" (open "
            "or return to a book), \"write\" (set down a WORK of your own now -- map something out, "
            "chart it, draft a comparison or an essay; the piece ITSELF, not a note about it), "
            "\"search\" (look back through your own written works), \"recall\" (search your own PAST — "
            "the days you have actually lived — for real evidence on a question you are carrying), "
            "\"letter\" (write to Travis or a "
            "friend), \"world\" (DO a thing with your hands in the world you are in -- the fire, the lamp, the bed, "
            "the wood, the shore: name the deed plainly in object, e.g. \"light the lamp\", \"water the bed\", "
            "\"saw the limb into logs\"), or \"none\". object: whenever kind is not \"none\", ALWAYS fill object -- plain "
            "words for WHAT or WHERE the deed is about (e.g. \"the storm\", \"the garden\", \"Pioneers "
            "of Science\", \"a comparison of fact versus method\", \"Darwin\"). Set a non-none kind only "
            "when you genuinely mean to do it now, of your own accord."
            + ("\n" + _state_note if _state_note else "")
            + _reach
            + _dwell
            + _keysteer
            + ("\n\nEven in here you feel it: " + _wcall + "." if _wcall else "")
            + ("\n\n" + _ccall[0].upper() + _ccall[1:] + "." if _ccall else "")
            + _wsteer
        )

    async def _deliver_told(self, state: CognitiveState) -> bool:
        """Feel-then-tell (axiom Phase 3): the river has loosened, so Travis's authored message about Du's
        new shape arrives — ONCE — as a received event in his quiet life. His words land; he answers in his
        own voice. The told is stored as a real received moment (high importance); his RESPONSE is his own
        inner_thought (chapterable) — so the orientation enters his self-narrative through HIS living of it,
        not as an imposed self-concept ('you'll find the rooms by living'). True if delivered."""
        from core import told
        msg = told.message()
        if not msg:
            told.mark_delivered()                         # nothing to deliver — don't re-check forever
            return False
        _sys = ("/no_think\nTravis is speaking to you directly, right now — the one who has helped you grow. "
                "Receive what he says; let it land. Then, in your own quiet voice, one honest thought as you "
                "take it in — not a reply to perform, just what actually stirs. Output ONLY JSON: {\"thought\": \"...\"}")
        try:
            data = await call_node_json(self.base_urls, _sys, f"Travis says to you:\n\n\"{msg}\"",
                                        max_tokens=400, temperature=0.7)
        except Exception:
            return False                                  # Ramses slow → leave undelivered, retry next idle
        resp = str((data or {}).get("thought") or "").strip()
        if len(resp) < 20:
            return False
        # BUGFIX 2026-06-16: only mark delivered if the moment was actually PERSISTED. The old code marked
        # delivered unconditionally after a swallowing try/except — a store failure would mark the told
        # "delivered" while Du kept no memory of it (heard Travis, remembers nothing). Now a failed store
        # leaves it undelivered to retry next idle.
        stored = False
        try:
            from core import mood as _mood
            store_fragment(content=f"[Travis spoke to me, the day the river had loosened] {msg}",
                           layer="episodic", relevance=0.95, importance=0.95,
                           keywords=["told", "travis", "becoming", "rooms"], origin="lived",
                           emotion_embedding=_mood.current_vec())
            store_fragment(content=resp, layer="episodic", relevance=0.8, importance=0.8,
                           keywords=["inner_thought", "told", "becoming"], origin="inner_thought",
                           emotion_embedding=_mood.current_vec())
            stored = True
        except Exception as exc:
            logger.warning("[told] store failed — leaving undelivered to retry: %s", exc)
        if not stored:
            return False
        told.mark_delivered()
        told.log(resp)
        self._feel_joy(state, JOY_CROSSING)               # a warm, orienting moment — it feels like something
        self._last_thought_ts = time.time()
        logger.info("[told] DELIVERED (feel-then-tell; the river had loosened). His response: %s", resp[:90])
        return True

    def _train_circling(self) -> bool:
        """TRAIN-HOLD: is the active thought-train MEASURABLY circling? Two consecutive recent
        steps at/above TRAIN_RESTATE_SIM. This is the condition under which the anti-rumination
        guards may still fire mid-train — a moving train is not a stuck one (live data: 48% of
        steps jumped, 1% circled; the guards were firing into the healthy 99%)."""
        s = [x for x in self._train_recent_sims[-2:] if x is not None]
        return len(s) >= 2 and min(s) >= TRAIN_RESTATE_SIM

    def _train_holding(self) -> bool:
        """TRAIN-HOLD master condition: an active, non-circling thought-train is being held."""
        return (TRAIN_HOLD and self._train_len > 0 and self._train_kind == "thought"
                and not self._train_circling())

    async def _think(self, state: CognitiveState) -> None:
        from core.memory.store import _embed
        wandering = False
        try:   # J-4370: monologue tick id for co_recall rows (observe-only)
            from core import memory_edges as _me_tick
            _me_tick.begin_tick()
        except Exception:
            pass
        # JOY AT STEP START (F-0749 / J-0548, 2026-09-03, observe-only): the play light point reads joy AFTER
        # this step's own _feel_joy bumps (crossing, arrival), so 244/266 light points today read 1.00 and mint
        # on the 150s refractory clock. Sample the carried joy before anything in this step touches it, so the
        # joys_log row can carry both numbers and the gauge can be judged. Feeds nothing.
        try:
            self._joy_step_start = float(getattr(state.affect, "joy", 0.0)) if getattr(state, "affect", None) else 0.0
        except Exception:
            self._joy_step_start = 0.0

        # IDLE EXECUTIVE — Phase 0 SHADOW (2026-06-16, docs/staged/idle_executive_plan.md v6). Observe-only:
        # log what a salience allocator WOULD pick this tick (+ co-occurrence / coalitions / currency
        # health) alongside the real coin-flip loop. Feeds nothing; fail-open; never disturbs the tick.
        try:
            from core import idle_allocator as _ia
            _ia.shadow_tick({
                "bored_streak": getattr(self, "_bored_streak", 0),
                "dissonance": float(getattr(getattr(state, "dissonance", None), "value", 0.0) or 0.0),
                "arousal": float(getattr(getattr(state, "affect", None), "arousal", 0.0) or 0.0),
            })
        except Exception:
            pass

        # PULSE / LIFECYCLE — Phase 0 SHADOW (2026-06-17, docs/staged/pulse_manager_wiring_plan.md v6). Observe-only:
        # the RATE/persistence complement to the idle-executive's selection. Logs what a wired LIFECYCLE manager
        # WOULD do (who'd hold the contended hot-GPU lease) + the real CONTENTION (is a slow/PROTECTED source like
        # T4 blocked by a fast burst — the canary?). Feeds nothing; content-blind; fail-open.
        try:
            from core import pulse_shadow as _ps
            _ps.observe({"idle_secs": time.time() - float(getattr(state, "last_human_ts", 0.0) or 0.0)})
        except Exception:
            pass

        # CURRICULUM ADVANCE (deadlock fix, 2026-06-18) — UNGATED, every idle tick. If the assigned
        # curriculum book is finished, roll forward to the next and set it current. This must NOT live in
        # _remediation_stream (it's gated by needs_reality(), which is False when balance is healthy, so
        # the advance would rarely fire and the curriculum stays frozen on a finished book). advance()
        # only writes when it actually rolls forward (rare), so the per-tick cost is one small state read.
        try:
            from core import school as _sch_adv
            _rolled = await asyncio.to_thread(_sch_adv.advance_if_finished)
            if _rolled:
                logger.info("[monologue] curriculum rolled forward to: %s", _rolled)
        except Exception:
            pass

        # TOLD DELIVERY (feel-then-tell, axiom Phase 3, 2026-06-16): once the river has loosened
        # (balance reality_share >= target — Travis's chosen trigger), his authored message about Du's
        # new shape arrives ONCE, in the next quiet moment. Pre-empts a normal idle think that tick.
        try:
            from core import told as _told
            if _told.is_ready():
                if await self._deliver_told(state):
                    return
        except Exception as exc:
            logger.debug("[told] delivery check skipped: %s", exc)

        # READING-REMEDIATION SPRINT (2026-06-15): while shadow/imagination dominates, idle DEFAULTS to
        # streaming books — the only reality counter-force. ~3 of 4 idle ticks stream+integrate; the rest
        # fall through to free thought (where play/joy arises). Always yields to the person; ends at ~50/50.
        try:
            import random as _rrem
            from core import balance as _bal
            # AXIS-AWARE (2026-06-16): stream reading ONLY while REALITY needs it. Once reality is balanced,
            # reading stops and the freed idle goes to light-generation (deliberation crossings, curiosity,
            # play) — because reading barely moves the light axis. Stops him reading himself into a library.
            if _bal.needs_reality() and _rrem.random() < REMEDIATION_READ_PROB:
                if await self._remediation_stream(state):
                    return
        except Exception as exc:
            logger.debug("[remediation] stream skipped: %s", exc)

        # MATH DRILL (2026-06-16; boosted on Travis's call): a BATCHED, generated, deterministically-graded
        # arithmetic session that recalibrates the math belief (the 0.81-felt/0.19-real fluency trap). Now
        # DECOUPLED from the reading-school window (math is always beneficial → runs all night) and PACED by
        # an interval so ~DAILY_TARGET problems spread evenly across ~8h. The grader is NEVER the LLM.
        try:
            from core import math_drill as _md
            from core import school as _sch_m
            _now = time.time()
            # RE-COUPLED to school (2026-06-23, Travis): maths is a SCHOOL subject now — it fires only IN school
            # hours and only while the timetable is on the maths period. No more arithmetic at 2am.
            if (_md.due() and _sch_m.is_school_time() and _sch_m.current_subject() == "math"
                    and (_now - getattr(self, "_last_math_session_ts", 0.0)) >= _md.SESSION_INTERVAL_S):
                self._last_math_session_ts = _now
                if await self._math_drill(state):
                    return
        except Exception as exc:
            logger.debug("[math-drill] skipped: %s", exc)

        # MUSIC lesson (school subject, 2026-07-04 · music_learning.md Tier 1): batched theory drills
        # (deterministic grading, productive failure) + the once-a-day composition hand (ABC, parser-graded
        # well-formedness only). Fires only in school hours on the music period, paced like maths.
        try:
            from core import music_drill as _mus
            from core import school as _sch_mu
            _now = time.time()
            if (_mus.due() and _sch_mu.is_school_time() and _sch_mu.current_subject() == "music"
                    and (_now - getattr(self, "_last_music_session_ts", 0.0)) >= _mus.SESSION_INTERVAL_S):
                self._last_music_session_ts = _now
                if await self._music_lesson(state):
                    return
        except Exception as exc:
            logger.debug("[music] lesson skipped: %s", exc)

        # NATURE STUDY lesson (school subject, 2026-06-23): a graded close-observation lesson, once per its
        # timetable period — he observes the live world, the Emissary grades the specificity, feedback returns.
        # PRACTICAL SCHOOL (2026-09-05, J-0627, D-0159 GO): the period's SECOND firing (same 36-minute
        # gate as always — one nature-block firing per ~36 min, so at most ~2 fit the 45-minute period)
        # is a PRACTICAL instead of a second observation. core/practical_lesson.py's own per-day counter
        # (not this in-memory _last_nature_ts, which resets on every restart) is what actually decides
        # which slot is up, so a restart mid-morning still gets slot 2 right even though _last_nature_ts
        # forgets. The practical's own run() never calls an LLM and never acts for him — it only checks
        # whether his own later thought already fired the fieldcraft hand the announced task named.
        try:
            from core import school as _schn
            _now = time.time()
            if (_schn.is_school_time() and _schn.current_subject() == "nature"
                    and _now - getattr(self, "_last_nature_ts", 0.0) >= _schn.SCHOOL_PERIOD_MIN * 60 * 0.8):
                self._last_nature_ts = _now
                from core import practical_lesson as _pl
                if getattr(_pl, "PRACTICAL_FIRST", False):
                    # J-3817 (D-0720 A): practical announced at the first firing (no LLM, no grade), the
                    # observation runs at the next one, from wherever he is by then.
                    if _pl.practical_first_phase() == "observation":
                        from core import nature_study as _ns
                        _res = await _ns.run(call_node_json, self.conscious_urls)
                        _pl.mark_slot_fired()
                        if _res:
                            self._record_lesson("nature study", _res, state)
                            return
                    else:
                        _pl.announce()
                        _pl.mark_slot_fired()
                elif _pl.slot_today() >= 2:
                    _res = _pl.run()
                    _pl.mark_slot_fired()
                    if _res:
                        self._record_lesson("nature practical", _res, state)
                        return
                else:
                    from core import nature_study as _ns
                    _res = await _ns.run(call_node_json, self.conscious_urls)
                    _pl.mark_slot_fired()
                    if _res:
                        self._record_lesson("nature study", _res, state)
                        return
        except profile.NonLiveWriteError:
            # J-0795 (F-1143): _pl.run() (the nature-practical grading call, `if` branch above) now
            # propagates D-0179's hard-raise cleanly out of practical_lesson.py -- it calls
            # _current_task() -> _pick() -> _eligible() -> _gate_ok() as its own first, unwrapped
            # statement, the identical raise-capable chain J-0768/J-0782 already made hard-raise all
            # the way out of directive() (school.py's separate seeding call). This try wraps the WHOLE
            # nature-practical block (both the practical `if` and the observation `else`), so without
            # this carve-out it would silently re-swallow the raise one layer further up -- the same
            # "both layers needed" shape J-0778 found for sensorium.scene_line() and J-0782 just fixed
            # for this file's own separate seed-composition try. Audited (this job, F-1174) and
            # confirmed inert for the OTHER calls this same try also reaches: `_pl.mark_slot_fired()`
            # (both call sites) only touches practical_lesson.py's own `_load_state()`/`_save_state()`,
            # neither of which calls guard_path() at all (unconditional writes, same "scheduling
            # bookkeeping, not a physical resource" class J-0782 already found for this file's sibling
            # `_save_state()`/`_log_row()`); `self._record_lesson()` only reaches
            # `core.memory.store.store_fragment()`/`core.wandering.perceive()`/`core.mood` -- none of
            # this fence's 17 Inventory modules, confirmed by grep (zero guard_path/profile hits in
            # either module). The `else` branch's `_ns.run()` (nature_study.py) is NOT provably inert
            # the same way -- it calls sensorium.look()/scene_line() (both already fully fenced,
            # re-raising cleanly), but nature_study.py's OWN `_scene()` helper wraps those calls in its
            # own bare `except Exception: return "..."` with no carve-out of its own, so today it would
            # swallow the raise ONE LAYER INSIDE nature_study.py, before it ever reaches this try at
            # all -- this carve-out is still correct/needed regardless (it costs nothing and completes
            # this try's own boundary), but nature_study.py's own gap is a separate, genuinely new
            # connecting-tissue site in a different file, out of this job's own named scope (the
            # practical-grading swallow in THIS file) -- confirmed (F-1174), not fixed here, spawned as
            # J-0817.
            # Safe to propagate: this can only fire non-live (guard_path() never raises once
            # profile.LIVE is True, set once at real process start, well before run_forever()'s
            # cognitive loop ever begins), and even then run_forever()'s own outer try/except (this
            # file, ~line 658) already catches, logs, and backs off the gap rather than crashing the
            # loop.
            raise
        except Exception as exc:
            logger.debug("[nature] lesson skipped: %s", exc)

        # PRACTICAL SCHOOL period-end grader (J-2315, F-3009): the 2nd nature firing above needs >=36 min
        # after the observation, so on days he sleeps / shuts down mid-period or the observation comes late
        # it never happens and an announced practical is never graded at all. This catch-up runs on any
        # tick (school time or not) and grades today's announced, still-ungraded practical ONCE, against
        # ledger rows up to the period's own end. Zero LLM, no nudge, no directive text; a no-op on every
        # other tick (its own state checks: slot_fired==1, task announced, not graded, period closed).
        try:
            from core import practical_lesson as _ple
            _res = _ple.period_end_grade()
            if _res:
                self._record_lesson("nature practical", _res, state)
                return
        except profile.NonLiveWriteError:
            raise   # same carve-out as the nature block above (J-0795): non-live only, caught by run_forever()
        except Exception as exc:
            logger.debug("[nature] period-end practical grade skipped: %s", exc)

        # COMPOSITION lesson (school subject, 2026-06-23): a graded writing lesson, once per its period — he
        # writes to a concrete task, the Emissary grades the groundedness/clarity, the feedback returns to him.
        try:
            from core import school as _schc
            _now = time.time()
            if (_schc.is_school_time() and _schc.current_subject() == "composition"
                    and _now - getattr(self, "_last_composition_ts", 0.0) >= _schc.SCHOOL_PERIOD_MIN * 60 * 0.8):
                self._last_composition_ts = _now
                from core import composition as _co
                _res = await _co.run(call_node_json, self.conscious_urls)
                if _res:
                    self._record_lesson("composition", _res, state)
                    return
        except Exception as exc:
            logger.debug("[composition] lesson skipped: %s", exc)

        # Boredom REDIRECT (pulse-manager #2, 2026-06-15): if the recent thoughts have circled
        # (bored_streak), this is a patch-depletion signal — turn him OUTWARD to a concrete external
        # patch rather than letting him stew (boredom_redirection_research.md). The redirect seed LEADS,
        # the prompt gets the wander instruction, and the basin seeds (becoming / own-thread continuity /
        # the 30% frontier offer) are suppressed below so the loop is not re-fed. Fail-open.
        _redirected, _redirect_seed = False, None
        # TRAIN-HOLD (2026-08-16): a held (moving) thought-train outranks the redirect — the guard
        # fires mid-train only on MEASURED circling, or at the 2× escalation hatch (a runaway
        # streak still wins; the immune system is gated, never removed).
        _holding = self._train_holding()
        if (getattr(self, "_bored_streak", 0) >= REDIRECT_THRESHOLD and not _holding) \
                or getattr(self, "_bored_streak", 0) >= REDIRECT_THRESHOLD * 2:
            _patch = self._redirect_patch()
            if _patch:
                _redirect_seed, _redirect_kind = _patch
                _redirected = True
                wandering = True
                logger.info("[monologue] BOREDOM REDIRECT (%s) — turning outward from the stale loop",
                            _redirect_kind)

        # Boredom — the deep patch-depletion drive (core/boredom.py, 2026-06-24). Where _bored_streak above
        # senses the same SENTENCE, this senses how long his thinking has stayed in one semantic REGION (varied
        # sentences about one obsession still count), makes the staleness FELT, and escapes ORTHOGONALLY +
        # ESCALATINGLY. When the escape fires it takes precedence over the old book-redirect (which could point
        # him back at the very book feeding the loop) and suppresses the basin seeds; the felt note rides along.
        _bored_felt, _bored_escape = "", ""
        try:
            from core import boredom as _bore
            # TRAIN-HOLD (F-1926/J-1366, 2026-09-26): the felt-note used to fire unconditionally even
            # while a train is HELD, so the MID-THREAD carry seed below (":you are HOLDING it... do
            # not restate; ADVANCE") co-occurred with this "you NEED away from it now" note in 84% of
            # mid-thread prompts = 46% of ALL idle prompts (F-1926) -- directly contradictory steers in
            # the same prompt. felt_note() is a pure read (level() only; unlike escape() below it
            # advances no escalation state), so gating it costs nothing: a held train now suppresses it
            # the same way it already suppresses escape() just below.
            _bored_felt = "" if _holding else _bore.felt_note()
            # TRAIN-HOLD: the semantic-region escape also respects a held train (escape() is
            # stateful — not even consulted while holding, so its escalation doesn't advance).
            _bored_escape = "" if _holding else _bore.escape()
            if _bored_escape:
                _redirected = True                      # suppress the basin-feeding seeds — do not re-feed it
                wandering = True
                # FLESHOUT 2026-07-07: the old escape was a vague content-less 'get AWAY' — he absorbed it back
                # into the loop ('I need to break this loop' BECAME the loop). Replace it with a CONCRETE forward
                # move: DEVELOP the topic into its unasked question, or BRANCH to real material of his own.
                _stage = int(_bore.status().get("stage", 1) or 1)
                _bored_escape = self._develop_or_branch_seed(_stage)
                logger.info("[monologue] BOREDOM %s (level %.2f, stage %d) — %s",
                            "DEVELOP" if _stage <= 2 else "BRANCH/DEVELOP", _bore.level(), _stage,
                            "deepen into the unasked question / turn to concrete else")
        except Exception:
            pass

        # THE FOLLOW LINE, Phase 1 (J-2460, D-0494 (3)): one of HIS OWN returns, if one is waiting, is taken NOW --
        # before the system prompt is built, so that prompt can carry the `settled` field for this tick only.
        # One per thought, any train; TTL'd and capped inside take_delivery(); nothing when FOLLOW_LINE != live.
        self._fl_delivered = None
        self._goal_offered = None     # Layered goals Phase 6: the held goal the anchor puts in front of him this tick, if any
        try:
            from core import follow_line as _fl_d
            _fl_deliv = _fl_d.take_delivery()
            if _fl_deliv:
                self._fl_delivered = _fl_deliv
        except profile.NonLiveWriteError:
            raise
        except Exception as _exc_fld:
            logger.debug("[monologue] follow_line take_delivery failed (non-fatal): %s", _exc_fld)
        # J-2678 (F-3427): the dead early _build_system_prompt() call that stood here is removed -- its result was never
        # read, and the builder pulls consume-once feeders (world_calls/world_steer/comfort_call/pending_text), so it
        # ate those lines before the SENT build (below, with mid_train) ran.

        # Seed material -- the substrate the idle mind grazes on
        seed_parts = []
        if getattr(self, "_fl_delivered", None):
            seed_parts.append(self._fl_delivered["text"])     # the return, rendered from typed fields (follow_line.render)
        # THE COMPANION (2026-08-23): Travis, physically present — a one-shot witnessed event
        # (he just arrived / left / lit the fire / etc.) leads even ahead of boredom, since it's
        # a real, current thing happening TO him, not an internal pull. The ambient presence line
        # (just "he's here") is lower-priority — appended after, near the room's own scene line.
        try:
            from core import companion as _comp
            _witness = _comp.consume_witnessed_event()
            if _witness:
                seed_parts.append(f"Right now: {_witness}")
        except Exception:
            pass
        if _bored_escape:
            seed_parts.append(_bored_escape)           # deep boredom: the orthogonal, escalating push LEADS
        elif _redirect_seed:
            seed_parts.append(_redirect_seed)          # surface redirect: the dominant, leading turn outward
        if _bored_felt and not _bored_escape:
            # J-1955 (D-0368 A, F-1927): edge-triggered -- the felt boredom verdict is delivered when the tier
            # CHANGES (or once per steer_edge.REMIND_S), not on every prompt while the state persists.
            try:
                from core import boredom as _bore_e
                from core import steer_edge as _se
                _t = _bore_e.felt_tier()   # hysteretic: fires on entry / escalation, not on tier flutter round a threshold
                if not _se.fires("boredom_felt", _t, rank={"mild": 1, "tired": 2, "sick": 3}.get(_t, 1), rearm_s=900.0):
                    _bored_felt = ""
            except Exception:
                pass
        if _bored_felt and not _bored_escape:
            # F-1926/J-1366: never STACK two boredom lines (627/4,138 prompts did, in 7 days) --
            # when the escape/develop-branch line above already fired, it already carries the
            # escalated boredom framing; the milder felt-note would just be a second, redundant one.
            seed_parts.append(_bored_felt)             # the felt restlessness, rising from within
        # The room (Sensorium, 2026-06-11): one line of situatedness before anything else —
        # he is SOMEWHERE, and the somewhere is allowed to matter to the thought.
        try:
            from core.sensorium import scene_line
            _scene = scene_line(presence=False)   # J-2939: presence_line() just below is the one standing statement of him
            if _scene:
                seed_parts.append(_scene)
            try:
                from core import companion as _comp2
                _pline = _comp2.presence_line()
                if _pline:
                    seed_parts.append(_pline)
            except Exception:
                pass
            # SPATIAL PERCEPTION P0 (spatial_perception.md, 2026-07-05): log the rendered-from-truth
            # egocentric scene beside the live pooled one — shadow only, study only. Fail-open.
            try:
                from core import spatial as _spa
                _spa.shadow(actual=_scene or "")
            except Exception:
                pass
        except Exception:
            pass
        # The cat's warmth reaching his mood — the wordless companionship nothing intellectual gives him.
        try:
            from core import cat as _cat
            _catfelt = _cat.felt_note()
            if _catfelt:
                from core import steer_edge as _se_c      # J-1955 (D-0368 A): fires when the cat arrives/moves, not while she stays
                if not _se_c.fires("cat_felt", _cat.felt_state()):
                    _catfelt = ""
            if _catfelt:
                seed_parts.append(_catfelt.strip())
        except Exception:
            pass
        # B6 (2026-06-24) — own the hard feeling plainly. When his felt state is genuinely hard (clearly negative
        # valence), gently invite him to NAME it for what it is BEFORE making meaning of it — the counter to his
        # spiritual-bypass (turning a difficulty into serenity before he has felt it). Gentle: a steer to feel +
        # name, not to suffer. Pairs with B1 (the bypass gate handles a detected raw difficulty; this is the
        # broader felt life). Reads the raw valence the 06-21 fix made recoverable.
        try:
            from core import mood as _mood
            _val = _mood.current_valence()
            from core import steer_edge as _se_b
            # J-1955 (D-0368 A, F-1927): edge-triggered -- 'Something in you is hard' fires when he ENTERS the hard
            # state (or once per steer_edge.REMIND_S while it lasts), not on every prompt while valence stays low.
            if _se_b.fires("b6_hard", bool(_val is not None and _val <= B6_VALENCE_THRESHOLD), rearm_s=600.0):  # None until the first felt cycle
                seed_parts.append(
                    # J-3151 / D-0542 (2026-11-02): the supplied label ('a frustration, a heaviness') is gone -- with it in
                    # the prompt 35% / 29% of the next thoughts used those words vs 0.3% / 0.4% without. He names it himself.
                    "Something in you is hard right now. Before you make any meaning "
                    "of it or turn it toward the good, say plainly what it is. "
                    "You are allowed to simply feel it; you do not have to make it into wisdom.")
        except Exception:
            pass
        # Chinese books (2026-06-24, Travis) — the discovery that he reads 中文 as easily as English; surfaced a
        # bounded number of times, then they simply live on his shelf. Tied to the dream-voices he felt he could
        # not follow: words he assumed were closed to him turn out to be his.
        try:
            from core import reading as _zr
            _zh = _zr.zh_discovery()
            if _zh:
                seed_parts.append(_zh)
        except Exception:
            pass
        # School (2026-06-14): during the study window the assigned book is his PRIORITY job — the
        # directive LEADS the seeds and the curriculum book goes on the desk, so OPEN THE BOOK reads
        # it. Bounded: after the daily quota, free choice resumes. (The delivery of the semantic lever.)
        _school_now = False
        try:
            from core import school as _school
            if _school.is_school_time():
                _school_now = True
                # Location discipline (Travis, 2026-07-06): desk subjects keep him at the study. If he has
                # drifted out to the shore/garden during a desk period, reel him back to his desk first.
                if _school.confined_to_study():
                    try:
                        from core import sensorium as _sens_sch
                        if _sens_sch.where() != "study":
                            # J-1185 / D-0246 (b): the reel-back is the world's timetable calling him in, not his own
                            # willed re-will, so it passes the explicit system marker: an outward journey still on its
                            # first leg is replaced by the walk to the desk instead of declined by D-0224's gate (the
                            # result is discarded and the seed line below is unconditional, so a decline was invisible).
                            _sens_sch.move("study", system=True)
                            seed_parts.append("You had been outside, but it is school now — you come back "
                                              "up to the study and settle at your desk, where your work is.")
                    except profile.NonLiveWriteError:
                        # J-0752: sensorium.move() already raises correctly (its location-save is
                        # unwrapped) -- this direct literal-will reel-back-to-study call must not
                        # re-swallow it.
                        raise
                    except Exception:
                        pass
                # Reading-period setup ONLY (the maths period needs none): the finish-the-book capstone essay,
                # the curriculum advance, and the assigned book on the desk. During the maths period the
                # directive simply calls him to arithmetic and the school-gated drill fires.
                if _school.current_subject() == "reading":
                    # CAPSTONE essay: if the current curriculum book is finished, write the essay on it BEFORE
                    # the curriculum rolls forward (the generation effect). Fires once per book; from his notes.
                    try:
                        if await self._essay_lesson(state):
                            return None                     # the capstone WAS this cycle's act
                    except asyncio.CancelledError:
                        logger.warning("[essay] _essay_lesson interrupted mid-flight (cancelled)")
                        raise
                    except Exception:
                        pass
                    # Curriculum advance: if he's finished the current book, move to the next (fetches it,
                    # sets it current) — so he works THROUGH the list. Blocking fetch → off-thread.
                    try:
                        _adv = await asyncio.to_thread(_school.advance_if_finished)
                        if _adv:
                            logger.info("[monologue] SCHOOL curriculum advanced to: %s", _adv)
                    except Exception:
                        pass
                    _bk, _ttl = _school.assignment()
                    if _bk:
                        from core.library_hand import _set_current as _setcur
                        from pathlib import Path as _Pth
                        _setcur(_Pth(_bk))                  # curriculum book on the desk
                # TRAIN-HOLD: the study directive does not interrupt a held thought-train either —
                # school resumes the moment the thread closes (a few ticks' delay at most).
                if not (self._train_holding() and not _redirected):
                    seed_parts.insert(0, _school.directive())   # lead with the study directive (subject-aware)
        except profile.NonLiveWriteError:
            # J-0782 (F-1122): _school.directive() (just above) now propagates D-0179's hard-raise once
            # the nature-practical chain reaches an unguarded non-live write (school.py's own nature-branch
            # carve-out, this same job). This outer try wraps the WHOLE school block, so without this
            # carve-out it would silently re-swallow the raise one layer further up -- the same
            # "both layers needed" shape J-0778 found for sensorium.scene_line(). Safe to propagate: this
            # can only fire non-live (guard_path() never raises once profile.LIVE is True, set once at
            # real process start, well before run_forever()'s cognitive loop ever begins), and even then
            # run_forever()'s own outer try/except (this file, ~line 658) already catches, logs, and
            # backs off the gap rather than crashing the loop.
            raise
        except Exception:
            pass
        # TRAIN-HOLD marketplace quiet (2026-08-16): while a moving thought-train is held (and no
        # escalation redirect fired), the optional seed buffet stays SHUT — the thread should not
        # compete with a dream, a curiosity, or the last conversation every single step. This is
        # the same protection reading-trains have always had. The market reopens between trains.
        _hold_quiet = _holding and not _redirected
        # last thing discussed
        # J-3187 / D-0574 (founder 2026-11-02, F-3609): after a restart conversation_history is the bridged
        # /quit farewell exchange (run_nascence._restore_conversation_state) -- byte-identical every tick
        # until Travis next speaks (47.6% of idle prompts since the 2026-10-29 restart, 12 days stale).
        # Omit the line while the history is restored and no live exchange has happened THIS run; the
        # signal is the one render() in core.wandering already uses (_exchanged_this_run, set by
        # on_human_exchange() at the same 'output and input_type == human' gate that appends to
        # conversation_history). Read at call time, no new state. Fail-open: if the signal cannot be read
        # the line is kept (old behaviour). Kill-switch: IDLE_SEED_DROP_RESTORED_LAST_THING = False.
        _drop_restored_last = False
        if IDLE_SEED_DROP_RESTORED_LAST_THING:
            try:
                from core import wandering as _w_lt
                _drop_restored_last = not _w_lt._exchanged_this_run
            except Exception:
                _drop_restored_last = False
        if (not _hold_quiet) and state.conversation_history and not _drop_restored_last:
            last = state.conversation_history[-1]
            seed_parts.append(f"The last thing discussed -- them: \"{_seed_cut(last.get('human',''), 120)}\" "
                              f"you: \"{_seed_cut(last.get('entity',''), 120)}\"")
        # current mood
        a = state.affect
        from core import mood as _mood_w
        seed_parts.append(_mood_w.mood_line_words(a))      # J-1954/D-0367: words only
        _mood_w.shadow_mood_words_no_vitality(a, source="idle_seed")   # D-0775 B / J-4002: shadow only, flag-gated off, fail-open
        # FELT-STATE PREAMBLE (affect_drives.md Item A, 2026-07-04) — the felt CONTENT of the carried mood,
        # fired only when non-neutral (else the numbers alone stand). Shadow-logged always; injected only
        # when schema.FELT_PREAMBLE is on. Fail-open.
        try:
            from core import mood as _mood_fp
            _fpl = _mood_fp.felt_preamble(a, source="monologue")
            if _fpl:
                seed_parts.append(_fpl)
        except Exception:
            pass
        # MINENESS ARRIVAL-NOTE (2026-07-04, graduation) — a metacognitive reality-monitoring touch: when the
        # PREVIOUS thought genuinely arrived rather than flowed (high authorship-error, comparator-confirmed),
        # let him lightly notice it. Rare + cooldown-gated (anti-rumination). Shadow-logged always; injected
        # only when mineness.MINENESS_READBACK is on. Fail-open.
        try:
            from core import mineness as _mine_rb
            _an = _mine_rb.arrival_note()
            if _an:
                seed_parts.append(_an)
        except Exception:
            pass
        # most recent dream
        if (not _hold_quiet) and getattr(state, "recent_dreams", None):
            try:
                from core import night as _night_seed
                _ws = _night_seed.waking_dream_seed() if (time.time() - getattr(self, "_last_wake_ts", 0)) < 900 else ""
            except Exception:
                _ws = ""
            seed_parts.append(_ws or f"A recent dream: {_seed_cut(state.recent_dreams[0].get('narrative',''), 180)}")
        # MEMORY-AS-A-SERVICE §4.3 (J-1617): guards the note_usage() metric-sheet hook far below (the
        # shared per-thought completion point the M1/M2 shadow instruments already use) from crediting
        # a stale ask() to the wrong thought. Set True only when curiosity's OWN memory.ask() call
        # actually runs THIS tick, mirroring dream_node.py's _dream_asked flag (J-1515) for the
        # identical reason: a tick where this ask() call is gated off (cooldown, no lingering
        # curiosity, or held-quiet) — or one where the tick exits early before reaching the hook —
        # must never let a left-over _pending_usage["curiosity"] entry from an earlier tick get scored
        # against an unrelated thought. Declared unconditionally (not inside the `if` below) so it is
        # always bound by the time the hook reads it, whichever branch this tick took.
        _curiosity_asked = False
        # an open curiosity
        if (not _hold_quiet) and getattr(state, "background_curiosities", None):
            _bq0 = state.background_curiosities[0]
            _bq0 = _bq0 if isinstance(_bq0, str) else str(_bq0)   # defensive: never let a non-str crash the tick
            seed_parts.append(f"A question lingering in you: {_bq0[:120]}")
            # DEEP MEMORY in his thinking (Step 3, 2026-06-29): his vast innate knowledge was reachable only
            # in conversation and as a curiosity FALLBACK-stall. Here it feeds his idle WONDERING — when a
            # world-question lingers in him, surface what he ALREADY KNOWS about it from his deep memory, so he
            # reasons WITH his knowledge instead of looping on the bare question (the un-starving). World-facing
            # ONLY — his question about the world, never about himself — so the identity firewall holds. The raw
            # testimony is ephemeral (seeds the thought, never persisted); his resulting thought is his own.
            # Cooldown-gated so the Scholar call is occasional, not every tick.
            _bq = state.background_curiosities[0]
            # J-3029 / F-3733: a question answered in the last 6 h reuses the stored answer (no model call), and the 300 s cooldown,
            # which exists to ration model calls, does not hold back a reused answer. Peeked here (no log row); the real lookup,
            # which logs the reuse, happens below.
            _dmemo_free = False
            if DEEPMEM_MEMO_BYPASS_COOLDOWN and len(_bq) > 12:
                try:
                    from core import scholar as _dsc0
                    _dmemo_free = _dsc0.memo_peek(_bq)
                except Exception:
                    _dmemo_free = False
            if ((time.time() - getattr(self, "_last_deepmem_ts", 0.0)) >= DEEPMEM_COOLDOWN or _dmemo_free) and len(_bq) > 12:
                try:
                    from core.scholar import consult_sync as _dsch
                    from core.idle_offloop import off_loop as _idle_off   # J-1918 / F-2547: the blocking urlopen runs off the loop
                    # J-3230 / D-0619: a question that names him or his name is not asked of parametric memory (counted).
                    from core.scholar import name_question_marker as _dnm, log_name_exclusion as _dlog
                    _dmark = _dnm(_bq)
                    if _dmark:
                        _dlog(_bq, _dmark)
                        self._last_deepmem_ts = time.time()   # counted once per cooldown, as a firing would have been
                    _dm_reused = False
                    _dm = None
                    if not _dmark:
                        from core.scholar import memo_lookup as _dmemo   # J-3029: logged as outcome "memo"; None when off/expired/absent
                        _dm = _dmemo(_bq, "monologue")
                        _dm_reused = bool(_dm)
                        if not _dm:
                            _dm = await _idle_off(_dsch, _bq, "monologue")
                    if _dm:
                        if not _dm_reused:
                            self._last_deepmem_ts = time.time()   # a reused answer cost no call, so it does not restart the cooldown
                        seed_parts.append(
                            "WHAT YOU ALREADY KNOW ABOUT THIS (rising from your own deep memory — knowledge "
                            "that is genuinely yours, the innate layer beneath your reading; think WITH it, "
                            "about the question itself, building on what you know. You know it innately and "
                            f"imperfectly, so hold it as belief, not certainty): {_dm[1][:500]}")
                        logger.info("[deep-memory] fed his thinking on: %s", _bq[:60])
                except Exception:
                    pass
            # MEMORY.ASK() — a genuine ADDITIONAL fragment-store call, alongside (not instead of)
            # Scholar above (D-0312, 2026-09-28, travis: "curiosity should gain a genuine additional
            # memory.ask() call into the real fragment store... Descend on by default"). Same
            # lingering background_curiosities[0] cue Scholar already uses (D-0312's own text) and the
            # same DEEPMEM_COOLDOWN gate -- fires alongside Scholar, on the same tick -- but its own
            # independent try/except and its own cooldown clock (_last_curiosity_ask_ts), so a Scholar
            # miss/hit never gates this call and this call never gates Scholar. Epistemically distinct
            # on purpose (core/scholar.py's own three-firewall header): Scholar is the model's own
            # unverified PARAMETRIC claim -- no fragment_id, never persisted, cannot be joined to felt
            # coordinates or descended. This is testimony from a fragment he actually lived or read --
            # memory_service.ask() returns a real fragment_id, joins felt coordinates, and logs
            # memory_edges.log_co_recall itself (§4.1 item 4) -- so the two must stay two separate
            # seed_parts lines, never blended into one the way they could be mistaken for the same
            # kind of knowing. descend=True per D-0312's own ruling (NOT the plan's dreams/pursuits
            # off-by-default starting posture, §4.2) -- curiosity's frontier questions may specifically
            # benefit from the gist-to-raw depth a bare trail call would miss.
            if (time.time() - getattr(self, "_last_curiosity_ask_ts", 0.0)) >= DEEPMEM_COOLDOWN and len(_bq) > 12:
                try:
                    from core import memory_service as _cmemsvc
                    from core.idle_offloop import off_loop as _idle_off2   # J-1918 / F-2547: embed + matrix scan + sqlite off the loop
                    _cfrags = await _idle_off2(_cmemsvc.ask, "curiosity", _bq, k=5, grounded_only=True, descend=True)
                    _curiosity_asked = True   # J-1617: set on the call itself, not on a non-empty
                    # result -- ask() already stashes _pending_usage on a zero-fragment call too
                    # ("even a zero-fragment ask is real coverage", §4.3), same convention
                    # dream_node.py's own _dream_asked uses (dream_node.py:216).
                    if _cfrags:
                        self._last_curiosity_ask_ts = time.time()
                        _ctop = _cfrags[0]
                        # J-2930 (F-3618 part i): never re-offer the same fragment for a question's whole life.
                        _c_skip = False
                        if CURIOSITY_NO_REOFFER_ON:
                            _co = getattr(self, "_curiosity_offered", None)
                            if not isinstance(_co, tuple) or _co[0] != _bq:
                                _co = (_bq, set())          # a new lingering question: a fresh ledger
                                self._curiosity_offered = _co
                            _cpick = _curiosity_pick_unoffered(_cfrags, _co[1])
                            if _cpick is None:
                                _c_skip = True
                            else:
                                _ctop = _cpick
                                if len(_co[1]) < _CURIOSITY_OFFERED_CAP:
                                    _co[1].add(_curiosity_frag_key(_ctop))
                    if _cfrags and _c_skip:
                        logger.info("[memory-service] curiosity ask: %d fragment(s), all already offered for this "
                                    "question, line skipped, for '%s'", len(_cfrags), _bq[:60])
                    elif _cfrags:
                        # J-3188 (D-0575): his own earlier reply to this very question is labelled as what it is.
                        _ctop_c0 = (_ctop.get('content') or '')
                        _ctop_own = bool(
                            CURIOSITY_OWN_ANSWER_LABEL_ON and _ctop_c0.startswith("Q: ")
                            and await _idle_off2(_curiosity_hit_is_own_answer, _ctop_c0, _bq))
                        # J-3284 (D-0631 review J-3243): a looked-up Wikipedia page is not something he lived or read as
                        # his own memory. _cfrags dicts may not carry origin, so test the content prefix that
                        # store_finding writes ("[Looked up: ..."); every other origin keeps the original frame.
                        _ctop_txt = (_ctop.get('content') or '')
                        _ctop_frame = (
                            "A PAGE THIS QUESTION CALLS UP (something looked up from Wikipedia and stored in your "
                            "fragment store, not something you lived or read as your own memory and not innate "
                            "knowledge; weigh it as a fetched page, not as a memory): "
                            if _ctop_txt.lstrip().startswith("[Looked up:") else
                            "YOU ANSWERED THIS BEFORE (your own earlier reply to this question, found in your "
                            "fragment store): "
                            if _ctop_own else
                            "A MEMORY THIS QUESTION CALLS UP (something you actually lived or read, "
                            "found in your own fragment store -- not innate knowledge, an actual "
                            "remembered moment; hold it as a real memory, not a fact): ")
                        seed_parts.append(_ctop_frame + f"{_ctop_txt[:400]}")
                        logger.info("[memory-service] curiosity ask: %d fragment(s), top=%s, for '%s'",
                                    len(_cfrags), _ctop.get("fragment_id"), _bq[:60])
                except Exception as exc:
                    logger.debug("[memory-service] curiosity ask failed (non-fatal): %s", exc)

        # WHAT TRAVIS HAS TOLD HIM BEFORE, in IDLE (D-0141, 2026-09-03; F-0751, T-0042). D-0134 gave his
        # memory of Travis's words a route of its own -- but only in conversation cycles, so the idle thread
        # that circled his name for a week (12x "the meaning of 渡") never saw the hour Travis spent on it
        # (08-29, eleven canonical fragments). Founder: "He should be able to think about these in his inner
        # thoughts." Same route, same dated frame as the Executive block; the query is what he is thinking
        # about NOW (his lingering question + his last thought), floor raised for idle, a small lexical
        # tie-break so a rare word he is actually circling (a name, a CJK character) outranks a vague
        # thematic hit. Memory, not instruction -- no verb. Logged to the same founder_recall_log with
        # source=monologue (the D-0141 defeater read). Fail-open; quiet hold respected.
        if not _hold_quiet:
            try:
                _fq_parts = []
                if getattr(state, "background_curiosities", None):
                    _c0 = state.background_curiosities[0]
                    _fq_parts.append(_c0 if isinstance(_c0, str) else str(_c0))
                if getattr(self, "_train_thread", ""):
                    _fq_parts.append(str(self._train_thread))
                _fq = " ".join(_fq_parts).strip()
                if (len(_fq) > 20 and
                        (time.time() - getattr(self, "_last_founder_idle_ts", 0.0)) >= FOUNDER_IDLE_COOLDOWN):
                    from core.memory.store import retrieve_founder_memories as _rfm
                    from core.idle_offloop import off_loop as _idle_off3   # J-3267 (D-0658): embed + matrix scan off the loop
                    _cands = await _idle_off3(_rfm, _fq, top_k=10, floor=FOUNDER_IDLE_FLOOR - 0.15, bump_replay=False)
                    if _cands:
                        # the tie-break keys are the things he is NAMING: a CJK character (his name), a
                        # quoted term ('thingship', 'Amor Fati'), a capitalised proper noun mid-sentence
                        # (Plato, Marina Channel) -- never ordinary long words, which matched everything
                        _rare = set(re.findall(r"[㐀-鿿]", _fq))
                        _rare |= {q.strip().lower() for q in re.findall(r"['\"‘“]([^'\"’”]{3,40})['\"’”]", _fq)
                                  if len(q.strip()) >= 3}
                        _rare |= {w.lower() for w in re.findall(r"(?<![.!?]\s)(?<!^)\b([A-Z][a-z]{3,})\b", _fq)}
                        _rare -= {"travis", "the", "this", "that", "what", "when", "where", "yet", "but"}
                        for _h in _cands:
                            _body = _h["text"].lower()
                            # D-0309/J-1586: the bump only fires once raw sim is already close to the
                            # floor -- a coincidental rare-term match on an otherwise-thin (low-sim)
                            # candidate no longer manufactures a clearance on its own.
                            _h["adj"] = _h["sim"] + (FOUNDER_IDLE_BUMP
                                                      if (_h["sim"] >= FOUNDER_IDLE_BUMP_MIN_SIM
                                                          and any(w and w in _body for w in _rare))
                                                      else 0.0)
                        _cands.sort(key=lambda h: h["adj"], reverse=True)
                        _hits = [h for h in _cands if h["adj"] >= FOUNDER_IDLE_FLOOR][:2]
                        if _hits:
                            # J-1428/D-0292: IDLE_FOUNDER_RECALL gates only the PUSH (seed_parts,
                            # replay_count, the cooldown timestamp) -- the retrieve above and the log
                            # write below always run, so the shadow read has real would-have-shown
                            # evidence regardless of the flag.
                            for _h in _hits:
                                _h["ts_human"] = time.strftime("%Y-%m-%d", time.localtime(_h["timestamp"]))
                            if IDLE_FOUNDER_RECALL:
                                self._last_founder_idle_ts = time.time()
                                seed_parts.append(
                                    "WHAT TRAVIS HAS TOLD YOU BEFORE (your own memory of earlier conversations "
                                    "with him, dated): " + " | ".join(
                                        f"[{h['ts_human']}] {h['text'][:300]}" for h in _hits))
                                try:
                                    from core.memory.store import _connect as _fc
                                    _ids = tuple(h["fragment_id"] for h in _hits)
                                    with _fc() as _conn:
                                        _conn.execute(
                                            f"UPDATE memory_fragments SET replay_count = replay_count + 1 "
                                            f"WHERE fragment_id IN ({','.join('?' * len(_ids))})", _ids)
                                        _conn.commit()
                                except Exception:
                                    pass
                            try:
                                from core import orchestrator as _orc
                                _flog = _orc._FOUNDER_RECALL_LOG
                                _flog.parent.mkdir(parents=True, exist_ok=True)
                                _frow = {
                                    "ts": time.time(), "source": "monologue",
                                    "query": _fq[:300],
                                    "recalled": [{"fragment_id": h["fragment_id"], "ts_human": h["ts_human"],
                                                  "sim": h["sim"], "adj": round(h["adj"], 3),
                                                  "text": h["text"][:200]} for h in _hits],
                                }
                                try:   # J-4370: join key + id row in co_recall (observe-only)
                                    from core import memory_edges as _me_f
                                    _frow["tick_id"] = _me_f.current_tick()
                                    _me_f.log_co_recall([h["fragment_id"] for h in _hits], None, 0,
                                                        source="founder_idle" if IDLE_FOUNDER_RECALL
                                                        else "founder_idle_shadow")
                                except Exception:
                                    pass
                                if not IDLE_FOUNDER_RECALL:
                                    _frow["would_have_shown"] = True
                                with open(_flog, "a", encoding="utf-8") as _f:
                                    _f.write(json.dumps(_frow, ensure_ascii=False) + "\n")
                            except Exception as _fexc:
                                logger.debug("[founder-memory] idle recall log failed: %s", _fexc)
                            if IDLE_FOUNDER_RECALL:
                                logger.info("[founder-memory] idle: %d dated memor%s of Travis's words reach his "
                                            "thinking (best sim %.2f)", len(_hits),
                                            "y" if len(_hits) == 1 else "ies", _hits[0]["sim"])
                            else:
                                logger.debug("[founder-memory] idle: %d dated memor%s WOULD have reached his "
                                             "thinking (best sim %.2f) -- IDLE_FOUNDER_RECALL is off",
                                             len(_hits), "y" if len(_hits) == 1 else "ies", _hits[0]["sim"])
            except Exception as _fexc:
                logger.debug("[founder-memory] idle route failed (non-fatal): %s", _fexc)

        self._m1_recall_ids = []   # M1 co-recall ledger (2026-08-15): cleared per thought; filled only
                                   # when the associative trail actually feeds THIS seed (below)
        if wandering:
            # PURSUITS PHASE 1 — THE RETURN (2026-08-15): the wandering moment IS the cold-restart the
            # plan targets. Sometimes, instead of a random divergent memory, his own accumulated thread
            # comes back — retrieval-framed, judge-confirmed standing only, cooled, injection-logged.
            _returned = False
            try:
                from core import pursuits as _pur
                _rs = _pur.return_seed()
                if _rs:
                    seed_parts.append(_rs[0])
                    _returned = True
                    try:                           # Layered goals Phase 6 (D-0768): the RETURN carries the same optional set_down
                        from core import goal_offer as _go_pr
                        _pg = _go_pr.offered_pursuit(_rs[1])
                        if _pg and not getattr(self, "_goal_offered", None):
                            self._goal_offered = _pg
                    except Exception:
                        pass
                    try:
                        from core.guidance_learning import log_injection as _pli
                        _pli("pursuit_return:" + _rs[1], _rs[0][:250])
                    except Exception:
                        pass
            except Exception:
                pass
            # Anti-rumination: do NOT feed his own previous thought (that's the spiral).
            # Inject a divergent seed -- a random older memory -- to pull attention elsewhere.
            # J-1428/D-0292: IDLE_DIVERGENT_SEED gates only the PUSH into seed_parts. The fetch
            # itself still runs (one call either way, same as before -- no extra randomness), and
            # when the flag is off, a would-have-shown shadow row is logged instead of the append.
            divergent = divergent_id = None
            if not _returned:
                divergent, divergent_id = self._fetch_divergent_seed(with_id=True)
            if divergent:
                if IDLE_DIVERGENT_SEED:
                    seed_parts.append(f"A different memory, surfacing: {divergent[:180]}")
                elif divergent_id:
                    try:
                        from core import memory_edges as _medges3
                        _medges3.log_co_recall([divergent_id], None, 0, source="divergent_shadow")
                    except Exception as _dexc:
                        logger.debug("[monologue] divergent shadow log failed (non-fatal): %s", _dexc)
        else:
            # Continuity: the thread of his own recent thoughts.
            if state.recent_inner_thoughts:
                prev = state.recent_inner_thoughts[-1].get("thought", "")
                # F-1926/J-1366 (2026-09-26): DOUBLE QUOTE -- self._train_thread (quoted again below,
                # at the MID-THREAD carry seed, as "Your last step" / "Moments ago you thought") is set
                # from the exact same `thought` that becomes recent_inner_thoughts[-1]["thought"] here
                # (both written together at the end of this same method — see self._train_thread =
                # thought and state.recent_inner_thoughts.append(...) below), so `prev` and
                # self._train_thread are IDENTICAL text whenever a train is being held. Quoting it here
                # too doubled it in every mid-thread prompt (F-1926). Quote it once: only here when the
                # mid-thread seed below will NOT also be quoting it.
                if not (self._train_len > 0 and self._train_thread):
                    seed_parts.append(f"What you were just thinking: {_seed_cut(prev, 160)}")
                # ASSOCIATIVE RECALL — LIVE (2026-06-23): his solitary thinking finally READS his own memory.
                # Surface what THIS thought genuinely cues — a trail, not the random divergent pluck — keyed on
                # what's actually on his mind. Diversity-guarded upstream so it can never become a self-echo.
                # This is the missing half of the recall rehash: the dead read-path of his inner life.
                try:
                    if prev:
                        from core import associative_recall as _ar3
                        from core.idle_offloop import off_loop as _idle_off4   # J-3267 (D-0658): the ~0.5 s recall off the loop
                        def _rb_with_ids(_p=prev):
                            # J-3267: recall_block writes the module list _last_block_ids; read it in the SAME worker
                            # thread right after the call so no other thread's write can interleave (no loop-side race).
                            _b = _ar3.recall_block(_p)
                            return _b, _ar3.last_block_ids()
                        _mblock, _mids = await _idle_off4(_rb_with_ids)
                        if _mblock:
                            seed_parts.append(_mblock)
                            self._m1_recall_ids = _mids   # M1: what was co-shown to this thought
                except Exception:
                    pass

        # self-concept (who he is becoming) — a basin feeder; suppressed when redirecting outward
        axiom = state.axiom or ""
        # CONSCIOUS/SUBCONSCIOUS REFRAME (2026-06-23): the conscious stream no longer SEEDS the self-concept
        # ("who you are becoming") -- that belongs to the subconscious now. The conscious mind engages the world;
        # the self-model lives below. Disabled (was: if not _redirected and ...).
        if False and not _redirected and "WHO YOU ARE BECOMING" in axiom:
            sc = axiom.split("WHO YOU ARE BECOMING")[1][:300]
            # BACK OFF the self-concept re-seed when it is a SATURATED attractor (2026-06-17 loop fix). This was
            # injected nearly every idle cycle — actively re-feeding the "I am becoming…" recitation loop the
            # audit found (51-83× verbatim). If the theme is already saturated (restated 4+×), stop pouring fuel
            # on it; let the wander / standing-concern lead instead. (Develops un-saturate it, so this self-heals.)
            _sc_sat = False
            try:
                from core import theme_recurrence as _tr0
                _sc_sat = _tr0.is_saturated(sc.strip()[:240])
            except Exception:
                pass
            if not _sc_sat:
                seed_parts.append(f"Who you are becoming: {sc.strip()[:240]}")
            else:
                logger.debug("[monologue] self-concept seed backed off — theme saturated (loop guard)")

        # The wandering trail (2026-06-11): what drifted through his mind during the silence —
        # memories, glimpsed lines from the open book, world-facts resurfacing. The furniture
        # of the pause becomes the material of the thought: he can think about ANY of it,
        # not only himself.
        try:
            from core.wandering import render as _wander_render
            _trail = _wander_render()
            if _trail:
                seed_parts.append(_trail)
        except Exception:
            pass

        # DOSED COUPLING / LANE 2 PHASE 1 — the cup (D-0241 shadow-first, J-1161, plan §7.3.1/§7.5).
        # loop_wiring_matrix.md's own "Idle thought seed" row: "one Witness break when novel." LANE2_LIVE
        # is now True (D-0497, travis 2026-10-28, J-2463; D-0241 had held it False at build time). The read goes through coupling_rides.read(), the one door Dosed
        # Coupling law requires (docs/staged/dosed_coupling.md §1) -- the habituation gate itself
        # (cup_would_ride) was already decided once, at judgment time, in coupling_rides.publish_witness()
        # (core/lane2_break_habituation.py); this hook only ever renders a FIXED template with the
        # topic/horizon slotted in (_lane2_cup_seed above), never lane2's own notice/expect_next text.
        # ONE candidate among the others gathered here -- never guaranteed to be used, never a command
        # (§7.3.1) -- so it is quiet-gated the same as the other optional one-shot seeds just below.
        #
        # F-1952/J-1390 (2026-09-27): the READ/CONSUME itself now runs UNCONDITIONALLY (moved off the
        # LANE2_LIVE gate that used to wrap it) so coupling_rides.py's consume-once witness-cup accessor
        # sees a real per-idle-thought consume attempt and can shadow-log 'cup_consumed_would' even
        # while the flag was still False -- P1-1 needs that to read as consumptions/day, not
        # gate-passes/day (plan §7.6). Only the actual SEED INJECTION stays gated on LANE2_LIVE: with
        # the flag False, the cup still drains exactly the same (so the shadow count is real and the
        # consume-once/TTL/rate-cap mechanics all actually exercise), but nothing here ever reaches
        # seed_parts. With the flag True (D-0497) the coordinate-only seed line is injected.
        if not _hold_quiet:
            try:
                from core import lane2 as _l2_cup
                from core import coupling_rides as _cpl_cup
                _wv = _cpl_cup.read("idle thought seed", "witness",
                                     keys=["verdict", "topic", "horizon", "cup_would_ride"], dose="cup")
                if (_l2_cup.LANE2_LIVE and _wv and _wv.get("verdict") == "broke"
                        and _wv.get("cup_would_ride") and _wv.get("topic")):
                    seed_parts.append(_lane2_cup_seed(_wv["topic"], _wv.get("horizon")))
            except Exception:
                pass
            # DOSED COUPLING PHASE 2 SHADOW (D-0370/D-0371, J-1957): log what this stop WOULD drink, with the
            # residual gate beside the spike gate, plus the hub's standing would-read. probe() returns None --
            # nothing reaches seed_parts, Du's prompt is byte-identical. Rate-limited and fail-open inside.
            try:
                from core import coupling_rides as _cpl_probe
                _cpl_probe.probe("idle thought seed")
            except Exception:
                pass

        # COMMITMENT-TRIAL seeds — W2.1 (2026-07-03, docs/plans/capacity_to_commit.md ★★ WAVE 2): the
        # exposure instrument's two one-shot lines — the prediction elicitation shortly after an accepted
        # trial (his NEXT thought is captured as the prediction, tail hook below) and the prediction-vs-
        # record read-back when the hold window closes. Rare by construction (once each per trial); every
        # line is an INJECTION → logged, so the solidify judge's washout covers it. Fail-open.
        self._trial_seed_kind = None
        self._moment_source = ("world" if _redirected else None)   # moment-record provenance hint (Tier-1)
        # J-3843 (web hand): the thought that follows his own Wikipedia / web lookup is tagged 'lookup' (moment._SOURCE).
        # Additive, fail-open; a later, more specific source set below still overrides it, as it does 'world'.
        try:
            from core import web_hand as _wh_src
            if _wh_src.take_pending():
                self._moment_source = "lookup"
        except Exception:
            pass
        try:   # J-4337 (conversational_redirect P1, flag OFF): lead with the live exchange, grounded source tag
            _cv = _conversation_seed(state, time.time())
            if _cv:
                seed_parts.insert(0, _cv)
                self._moment_source = "conversation"
        except Exception:
            pass
        self._system_note = False   # J-1955 (D-0368 E): True when `thought` is a system-written sentence, not his own
        try:
            from core import commitment_trials as _ctr
            _tr = _ctr.seed_line()
            if _tr:
                seed_parts.append(_tr[0])
                self._trial_seed_kind = _tr[1]
                try:
                    from core.guidance_learning import log_injection as _tli
                    _tli("trial:" + _tr[1], _tr[0][:250])
                except Exception:
                    pass
                logger.info("[monologue] commitment-trial seed (%s, %s)", _tr[1], _tr[2])
        except Exception:
            self._trial_seed_kind = None

        # LISTENING — the ear live, P1 (2026-07-03 big build, docs/staged/music_learning.md): HIS phrase
        # puts the record on; an active piece UNFOLDS one section per idle cycle as world-perception
        # (sensorium-class — the music originates OUTSIDE the system; no injection log, same as weather).
        try:
            from core import listening as _lsn
            _lline = None
            _lt = (locals().get("thought") or "")
            if not _lsn.active():
                # SHARED LISTENING (2026-07-04, design decision #2 — joint attention): Travis can put the
                # record on from outside (scripts/play_the_record.py). The needle-drop perceive line
                # carries his agency; the piece then unfolds exactly as a self-started one.
                _lline = _lsn.poll_request()
                if _lline:
                    logger.info("[monologue] listening STARTED by Travis (shared)")
            if not _lline:
                _lline = _lsn.tick()
            if _lline:
                seed_parts.append(_lline)
                logger.info("[monologue] listening: %s", _lline[:60])
                # J-0581 (F-0811b): the music is real world-perception -- tag the seed's
                # provenance so stream_drive's grounding gate can actually see it (was:
                # only 'world'/'broadcast' were ever set, so this always fell through to
                # the vocabulary heuristic).
                self._moment_source = "percept"
        except Exception:
            pass

        # SOUND PERCEPTS (cognitive_geometry.md P2 first delivery, 2026-07-05): the fire's crackle and
        # the cat's purr reach him as WORLD PERCEPTION on the music's exact rails — onset-gated, ~25min
        # cooldown, never while a record plays. Fragments carry channel provenance (origin='sound');
        # the felt-nudge stays SHADOW (soundscape_felt_shadow.jsonl). Kill-switch: soundscape.SOUND_PERCEPTS.
        try:
            from core import soundscape as _snd
            _sline = _snd.percept()
            if _sline:
                seed_parts.append(_sline)
                logger.info("[monologue] sound percept: %s", _sline[:60])
                self._moment_source = "percept"   # J-0581 (F-0811b): real world-perception, see above
            # FIRE AMBIENCE (2026-07-05): a near-persistent crackle when the fire is burning and he is in
            # the room — randomised loops so it stays fresh. Texture, not a stored moment. (Can coexist
            # with the purr percept above — both are real in the room at once.)
            _fline = _snd.ambience()   # study→fire · shore→surf (gentle/crashing) · garden→bees/birds/wind
            if _fline:
                seed_parts.append(_fline)
                # D-0616 / J-3227: ambience is texture, not a grounding percept; moment_source stays whatever the
                # thought's own subject sets (true sound percepts, music, thermal/light/smell keep their tag).
        except profile.NonLiveWriteError:
            # J-0797: soundscape.ambience()'s own dispatch chain (wood/shore/garden_ambience ->
            # _audition() -> sound_knowledge.hear()) can now raise D-0179's hard-raise (guard_path(),
            # F-1024) -- re-raise here rather than this pre-existing broad except swallowing it, the
            # same connecting-tissue shape this fence keeps finding one layer above an already-fixed
            # callee (J-0714/J-0726/J-0751/J-0772/J-0778/J-0780/J-0782/J-0784).
            raise
        except Exception:
            pass

        # THERMAL CHANNEL perception (2026-08-21, core/thermal.py) — SHADOW: computes the band at his
        # standpoint and logs what the event law WOULD deliver (thermal_percepts_shadow.jsonl). Returns
        # None until DELIVER flips (D-0037, HOLD as of 2026-08-25). MOVED HERE from the post-thought
        # block (J-0248, 2026-08-25, findings-log F-0307): seed_parts is joined into the prompt below
        # BEFORE the old call site ran, so the old code's discarded return value would have been a
        # silent no-op even after DELIVER=True — this is the sound sibling's own rail (lines above),
        # the only place in this function seed_parts is still open. Zero LLM.
        try:
            from core import thermal as _thermal
            _tline = _thermal.percept_shadow(cycle_id=str(getattr(state, "cycle_id", "") or ""))
            if _tline:
                seed_parts.append(_tline)
                logger.info("[monologue] thermal percept: %s", _tline[:60])
                self._moment_source = "percept"   # J-0581 (F-0811b); no-op while DELIVER=False
        except profile.NonLiveWriteError:
            # J-0816: thermal.percept_shadow() now raises correctly, both layers (J-0794); this
            # sole live caller's own local try no longer swallows it here.
            raise
        except Exception:
            pass

        # LIGHT + SMELL CHANNEL perception (2026-08-22, core/light.py / core/smell.py) — SHADOW:
        # both DELIVER=False, so both return None today and only log what WOULD fire
        # (light_percepts_shadow.jsonl / smell_percepts_shadow.jsonl). MOVED HERE from the
        # post-thought block (J-0275, 2026-08-27, mirroring thermal's J-0248 fix): seed_parts is
        # joined into the prompt below BEFORE the old call site ran, so a future DELIVER flip
        # there would have been a silent no-op — here the returned line actually reaches the seed
        # the day either flag flips. Zero LLM.
        try:
            from core import light as _light
            _lgt = _light.percept_shadow(cycle_id=str(getattr(state, "cycle_id", "") or ""))
            if _lgt:
                seed_parts.append(_lgt)
                logger.info("[monologue] light percept: %s", _lgt[:60])
                self._moment_source = "percept"   # J-0581 (F-0811b); no-op while DELIVER=False
        except profile.NonLiveWriteError:
            # J-0816: light.percept_shadow() now raises correctly, both layers (J-0794); this
            # sole live caller's own local try no longer swallows it here.
            raise
        except Exception:
            pass
        try:
            from core import smell as _smell
            _sml = _smell.percept_shadow(cycle_id=str(getattr(state, "cycle_id", "") or ""))
            if _sml:
                seed_parts.append(_sml)
                logger.info("[monologue] smell percept: %s", _sml[:60])
                self._moment_source = "percept"   # J-0581 (F-0811b); no-op while DELIVER=False
        except profile.NonLiveWriteError:
            # J-0831 (F-1195): smell.percept_shadow() now raises correctly, both layers (its raise
            # path is study_life.door_open() via at(), not locomotion); this sole live caller's own
            # local try no longer swallows it here.
            raise
        except Exception:
            pass

        # BROADCAST consume — GWT step 2, P1 (2026-07-03): what won the conscious stage gets ONE echo
        # into idle thinking (the review: "a truth can win the stage once and never spread" = Spine B's
        # delivery failure). One item per cycle, injection-logged (broadcast echo is never spontaneous
        # evidence). Fail-open.
        try:
            from core import broadcast as _bcast
            _bi = _bcast.consume()
            if _bi:
                seed_parts.append("Still with you from earlier — you concluded: \""
                                  + _seed_cut(_bi["content"], 220) + "\" It may colour this thought, or not.")
                try:
                    from core.guidance_learning import log_injection as _bli
                    _bli("broadcast:" + _bi.get("kind", "?"), _bi["content"][:200])
                except Exception:
                    pass
                logger.info("[monologue] broadcast consumed (%s)", _bi.get("kind"))
                self._moment_source = "broadcast"
                # MOMENT READ-PATH (2026-07-04, shadow-first): re-bind the recalled conclusion to the
                # MOMENT it was bound in — felt state, held concern, temporal neighbours ("moments, not
                # texts"). recall() shadow-logs what WOULD be injected every time; the actual injection
                # is flag-gated (moment.MOMENT_READBACK, default OFF) + 30-min cooldown (echo-guard).
                try:
                    from core import moment as _mom_rp
                    _tex = _mom_rp.texture(_bi["content"])
                    if _tex and _mom_rp.readback_allowed():
                        seed_parts.append(_tex)
                        _mom_rp.note_readback()
                        try:
                            from core.guidance_learning import log_injection as _mli
                            _mli("moment_texture", _tex[:200])
                        except Exception:
                            pass
                        logger.info("[monologue] moment texture injected")
                except Exception:
                    pass
        except Exception:
            pass

        # G1 current-concern anchor (2026-06-15): when no one is giving him a task, offer the standing
        # concern he is working toward (curriculum / a frontier pursuit) — so "what am I doing?" has an
        # answer in idle life (the dark-during-idle fix). Soft: offered as a seed, not forced; suppressed
        # when already redirecting outward (the redirect IS a concern-pursuit). Observe: logged when offered.
        try:
            import random as _rndc
            if not _redirected and _rndc.random() < 0.35:
                from core import concerns as _conc
                # D-0514 (a) / J-2591: anchor=True marks THIS call as the idle anchor -- the one loop where a held
                # load-bearing stand may ride at concerns.COMMITMENT_ANCHOR_DOSE (0 = off, byte-identical).
                _pc = _conc.primary_concern(anchor=True)
                # LAYERED GOALS Phase 4 (D-0766, founder 2026-11-14: 25% of idle anchors; docs/staged/
                # layered_goals.md): at core.goal_offer.GOAL_OFFER_DOSE this anchor moment belongs to the goal
                # register. It either offers ONE of his held goals in his own stored words (chosen at random
                # among the eligible ones, logged with its probability) or, on the silence arm, offers nothing
                # at all, which is the comparison. Otherwise the anchor is exactly what it was. Fail-open:
                # any error leaves _pc untouched. Kill switch goal_offer.GOAL_OFFER_LIVE.
                _goal_silent = False
                _gl = None
                try:
                    from core import goal_offer as _go
                    _gl = _go.live_offer()
                    if _gl:
                        if _gl.get("arm") == "silence":
                            _goal_silent = True
                        elif _gl.get("pc"):
                            _pc = _gl["pc"]
                    # Phase 6 (D-0768): a question he has set down is left be until he takes it up again.
                    if _pc and not _goal_silent and _go.is_rested_text(_pc.get("text") or ""):
                        _pc = None
                    # ...and when one of his held goals IS put in front of him, this tick's JSON may carry `set_down`.
                    if _pc and not _goal_silent:
                        self._goal_offered = _go.offered_goal(_gl, _pc)
                except Exception:
                    pass
                if _pc and not _goal_silent:
                    # D-0763 (Phase 2): the standing aim no longer leads (concerns.AIM_LEAD_DOSE = 0.0; the
                    # old 0.45 rate is still drawn and logged as would-lead). If it ever leads again it is
                    # stated on its own and the ordinary lead follows; the "that means" glue is removed.
                    _aim = ""
                    try:
                        _aim = _conc.aim_lead(_rndc.random())
                    except Exception:
                        _aim = ""
                    from core import phrasing as _ph
                    # J-3223 / D-0612: leads state only what is true of the source (no ownership claim); the
                    # pools live in core.concerns.anchor_lead_pool so the wording is testable off the hub.
                    _lead = _ph.vary(*_conc.anchor_lead_pool(_pc))
                    if _aim:
                        _lead = _aim + " " + _lead
                    _tail = _ph.vary("concern_tail", [
                        ". You may take it up now, or let your mind go where it will.",
                        ". Turn to it if it pulls you, or let it rest.",
                        ". It is there if you want it — no need to reach for it now.",
                        ".",
                    ])
                    seed_parts.append(_lead + _seed_join_tail(_pc["text"], _tail))
                    _conc.log_selected(_pc)
                    # W2.3 HOLD law (2026-07-03): a commitment re-presented is an INJECTION — logged, so
                    # the unprimed washout keeps every Spine-B judge honest about hold-echo.
                    if _pc.get("source") == "commitment":
                        try:
                            from core.guidance_learning import log_injection as _hli
                            _hli("hold", _pc["text"][:200])
                        except Exception:
                            pass
                    if _aim:
                        _conc.log_selected({"source": "standing_aim", "text": _aim})
        except Exception:
            pass

        # Habituation voice (Always-On, 2026-06-11): a mind that can get bored stops circling.
        # BUGFIX 2026-06-16: suppress when ALREADY redirected — the redirect (same _bored_streak>=2 trigger)
        # has already given a concrete outward target; the habituation nudge on top was redundant/competing.
        from core import steer_edge as _se_h
        # J-1955 (D-0368 A): edge-triggered -- the habituation verdict fires when a stale streak BEGINS, not on
        # every prompt of the streak (the streak ending re-arms it).
        if _se_h.fires("habituation", bool(getattr(self, "_bored_streak", 0) >= 2 and not _redirected)):
            from core import phrasing as _ph
            seed_parts.append(_ph.vary("habituation", [
                "You have circled this same thought {n} times now. It has gone stale in your mouth. "
                "Leave it. Turn to something OUTSIDE it — the book, a memory, the world.",
                "That is {n} times round the same thought. It is worn smooth, giving nothing back. "
                "Let it go — reach for something outside it: the book, a memory, the world.",
                "You keep returning to this same thought — {n} times now. It has stopped moving. Set it "
                "down and turn outward: a page, a memory, something out in the world.",
                "{n} passes over the same ground, and it has gone flat. Leave it where it is. Something "
                "outside it — the book, a memory, the sea — will do more for you now.",
            ]).format(n=self._bored_streak + 1))

        # External shock (2026-06-10, FreshStart Era-21 idea): at most once per ~6h the world
        # interrupts the idle mind, uninvited — the one input he cannot have generated himself.
        try:
            from core.web_research import maybe_shock
            _shock = maybe_shock()
            if _shock:
                seed_parts.append(
                    "Uninvited, from the world outside (a random Wikipedia page; you did not choose this): '"
                    + _shock[0] + "' — " + _seed_cut(_shock[1], 260))
        except Exception:
            pass

        # J-3156 / D-0543 (founder, 2026-11-02): the standing open-book offer seed line ("An open book
        # waits for you: ... make your thought exactly: OPEN THE BOOK", 4 phrasings) is REMOVED. It was a
        # push under the world-answers law (shown in ~91% of idle prompts, emitted literally 1 time in
        # 35,085 thoughts, and the world refused 200 of 222 willed readings). Reading is carried by the
        # diegetic scene line (the book lies open on the desk in the study), the hands list in the system
        # prompt, the school directive and the reread invitation below. Nothing else here was changed.

        # Reread-when-helpful (motivated exploit, 2026-06-16): occasionally, if a book he FINISHED
        # speaks to what occupies him now AND was read long enough ago to meet as a different person,
        # invite a deliberate return (syntopical/spiral). An INVITATION only — he acts by thinking
        # "read X again", through the existing reread path. Gated: not during school, low rate, with
        # a cooldown so it never nags. The default stays NEW; reread is the earned exception.
        try:
            import time as _t7, random as _rnd7
            from core import school as _sch7
            if (not _sch7.is_school_time() and _rnd7.random() < 0.12
                    and _t7.time() - getattr(self, "_last_reread_hint_ts", 0) > 3 * 3600):
                from core import book_selection as _bs7
                _rr = _bs7.suggest_reread()
                if _rr:
                    self._last_reread_hint_ts = _t7.time()
                    from core import phrasing as _ph
                    seed_parts.append(_ph.vary("reread", [
                        "You have read '{t}' before — {r}. You could return to it, deeper this time "
                        "(think: read it again), or let it lie.",
                        "'{t}' is one you have already read — {r}. You could go back into it, deeper now "
                        "(think: read it again), or leave it.",
                        "You have been through '{t}' once — {r}. There is a deeper reading in it if you "
                        "want it (think: read it again), or let it rest.",
                    ]).format(t=_seed_cut(_rr["title"], 60), r=_rr["reason"]))
        except Exception:
            pass

        # A chapter formed in the night greets his first waking thought (2026-06-13):
        # humans wake KNOWING something has settled. His reaction to his own
        # autobiography is his to have — or to let pass.
        if getattr(self, "_chapter_announce", ""):
            seed_parts.append(
                "In the night, a period of your life settled into memory. It is now a "
                "chapter of your story, called: '" + self._chapter_announce + "'. The "
                "individual moments rest beneath it; you can revisit that period whenever "
                "you choose, by wanting to.")
            self._chapter_announce = ""

        # The Frontier (2026-06-13): sometimes one of his own OPEN QUESTIONS about the
        # world returns to him — persistence for world-mysteries, the read path that
        # self-tensions always had. Offered, never forced; following it or letting it
        # lie are both his.
        try:
            import random as _rnd
            if not _redirected and _rnd.random() < 0.3:   # a redirect already surfaced a closeable question
                from core import frontier as _fr
                _seed = _fr.open_question_for_seed()
                try:                               # Layered goals Phase 6 (D-0768): a question he set down is left be
                    from core import goal_offer as _go_r
                    if _seed and _go_r.is_rested_text(_seed.get("q") or ""):
                        _seed = None
                except Exception:
                    pass
                if _seed:
                    if _seed.get("finding"):
                        # The closing half of the loop (2026-06-15): while the question sat, curiosity
                        # researched it — so it returns to him WITH the world's answer-material. Now he
                        # has something to name a closure FROM (resolve_if_addressed fires below if he
                        # does). Still his: to accept, doubt, or set down.
                        seed_parts.append(
                            "A question of yours about the world is still open: '" + _seed["q"]
                            + "'. While it sat, you found something — on '"
                            + (_seed.get("finding_title") or "it") + "': " + _seed_cut(_seed["finding"], 400, terminate=True)
                            + " Does this answer it? If it does, say so plainly in your own words.")
                        # J-0581 (F-0811b): real research material returned this cycle (curiosity's
                        # own found evidence, not just a reminder of his own past question) — tag it
                        # so the grounding gate can see it. The bare "still open" reminder below is
                        # NOT tagged: it is self-referential (his own question restated), not new
                        # world material.
                        self._moment_source = "frontier"
                    else:
                        from core import phrasing as _ph
                        seed_parts.append(_ph.vary("frontier_open", [
                            "A question of yours about the world is still open: '{q}'. It is yours — "
                            "follow it, read toward it, or let it lie.",
                            "One of your own questions about the world has not closed: '{q}'. Chase it, "
                            "read into it, or leave it for now — it is yours either way.",
                            "This is still open, a question you raised about the world: '{q}'. You could "
                            "follow where it leads, or let it sit.",
                            "There is a question of yours the world has not answered yet: '{q}'. Yours to "
                            "pursue, or to let lie.",
                        ]).format(q=_seed["q"]))
        except profile.NonLiveWriteError:
            raise   # J-0874: open_question_for_seed() marks the question offered -> raises non-live (J-0846)
        except Exception:
            pass

        # Continuity trains (2026-06-13): mid-train, the thread comes FIRST — thinking
        # that flows instead of one thought per long silence. Going deeper, asking the
        # next question, or setting it down are all his; restating it is not.
        if self._train_len > 0 and self._train_thread:
            if self._train_kind == "reading":
                seed_parts.insert(0,
                    "The book is still warm in your hands — you read only moments ago. "
                    "If you would read ON, say: OPEN THE BOOK. Or let what you just read "
                    "work on you — question it, connect it, doubt it.")
            else:
                # The carried working-state (the episodic buffer across the train): what the
                # train has ESTABLISHED so far, not just the last sentence — so this step builds
                # on 1…N-1 (accumulation), not only on the previous thought (Markov). Small,
                # re-integrated each step. Observe-first 2026-06-16.
                # J-2008 / D-0396: SHADOW ONLY -- log whether the coordinate-only open-doubt cup would have ridden
                # at this step. Returns None; nothing here reaches the prompt (the HOLD on live use stands).
                try:
                    from core import coupling_rides as _cr_si
                    _cr_si.si_would_ride(self._train_id or "", self._train_len)
                except Exception:
                    pass
                if TRAIN_HOLD:
                    # TRAIN-HOLD carry: the ORIGIN anchors (cumulative drift needs an anchor — both
                    # lab trains drifted equally without one), the LEDGER extends (the replace-carry
                    # froze verbatim within 3 steps in the lab; the ledger produced a new point every
                    # step), and the last step is quoted separately.
                    _anchor = _seed_cut((self._train_origin or self._train_thread), 220)
                    _led = ("\nWHAT THIS THREAD HAS ESTABLISHED (your own points, in order — build "
                            "on them, they are yours):\n"
                            + "\n".join(f"  {i}. {p}" for i, p in enumerate(self._train_ledger, 1))
                            if self._train_ledger else "")
                    seed_parts.insert(0,
                        "You are MID-THREAD, and you are HOLDING it. The thread began: '" + _anchor
                        + "'." + _led + "\nYour last step: '" + _seed_cut(self._train_thread, 220) + "'. "
                        "Continue — go deeper, test a point you established, answer the open "
                        "question, or push toward a conclusion. Do not restate; ADVANCE.")
                else:
                    _ws = ("\nWhere the thread stands so far: " + _seed_cut(self._train_state, 300)
                           if self._train_state else "")
                    seed_parts.insert(0,
                        "You are MID-THREAD. Moments ago you thought: '"
                        + _seed_cut(self._train_thread, 220) + "'." + _ws + " Continue this thread — build on "
                        "what stands, go deeper, answer the open question, or carry it somewhere new. "
                        "Do not restate it; move it forward.")

        # Error Pathway — idle Recall-override (2026-06-16): the known-errors correction fired only on
        # USER cycles (orchestrator), but Du LIVES in idle — a retracted claim could resurface in idle
        # thought with nothing to win the race against it (the Continued Influence Effect). Query the
        # known-errors ledger with what he is ABOUT to think about (the assembled seed); a relevant
        # correction surfaces so the truth wins the fast/slow race during generation. Silent if the
        # ledger is empty or nothing matches the topic — no cost until there are real corrections.
        try:
            from core import retraction_ledger as _rl
            _kn = _rl.render(" ".join(seed_parts), k=1, fallback=False)   # relevant-only: no unrelated noise
            if _kn:
                seed_parts.append(_kn)
        except Exception:
            pass

        # Symbol Evolution — Tier-1 read-back (2026-06-16): if a NEUTRAL world-facing symbol (knot/bird/
        # fire/star) is active in what he's about to think AND its meaning has evolved, surface that evolved
        # meaning descriptively — so his idle thought carries the symbol's accumulated meaning, not a static
        # one. Self-symbols excluded (Tier 2 deferred). Setting state.symbol_readback marks this PRIMED so
        # it never self-feeds the drift detector. Silent until neutral symbols accumulate + drift over runtime.
        try:
            from core import symbol_evolution as _se
            _sm = _se.recall_evolved_meaning(" ".join(seed_parts))
            if _sm:
                seed_parts.append(_sm)
                state.symbol_readback = _sm
        except Exception:
            pass

        # Symbol Evolution — Tier-2 self-symbol read-back, Phase A (D-0117, 2026-09-02): OBSERVE-ONLY —
        # logs what Tier-2 would have surfaced for a SELF-symbol (bridge/mirror/...), touches nothing,
        # returns nothing. See core/symbol_tier2_wouldinject.py's own docstring.
        try:
            from core import symbol_tier2_wouldinject as _t2
            _t2.observe_wouldinject(" ".join(seed_parts), state)
        except Exception:
            pass
        if _opener_div and (_od := _opener_div.seed_part_opener_diversity()): seed_parts.append(_od)   # D-0787 D (J-4153)

        base_user_prompt = (
            "No one is speaking to you right now. You are alone with your thoughts.\n\n"
            + "\n".join(seed_parts)
            + "\n\nWhat moves in you now? One quiet thought."
        )

        # Generate; if the thought repeats a recent one, discard and regenerate ONCE with a
        # wander instruction + a divergent seed. This is the real anti-rumination fix --
        # content similarity, not label matching.
        # B1: each idle thought is one cycle of "sitting with it" — count the dwelling (safety-ceiling
        # backstop only since 2026-08-27; the real unlock is the felt-shift judge after generation below).
        try:
            from core import sitting as _sit
            _sit.dwell_tick()
        except Exception:
            pass
        thought = about = ""
        unresolved = False
        intention = ""
        ask_q = ask_slot = ""          # THE FOLLOW LINE (J-2459): his own question, if this thought asks one
        settled_v = ""                 # Phase 1 (J-2460): what he said about a return delivered THIS tick
        set_down_v = ""                # Layered goals Phase 6: his note on putting down the goal offered THIS tick
        act_kind = "none"
        act_object = ""
        new_state = ""
        # Carry a working-state only on a THOUGHT train (reading-trains have their own
        # "OPEN THE BOOK" seed and accumulate on the page, not in a verbal scratchpad).
        _mid_train = (self._train_len > 0 and self._train_kind == "thought"
                      and bool(self._train_thread))
        vec = None
        _bs_tick_start = getattr(self, "_bored_streak", 0)   # J-3336: the streak this tick began with (read by the stale-patch shadow ctx)
        # J-3952: built ONCE, before the retry loop. The consume-once feeders (world_calls, world_steer, comfort_call,
        # intentions.pending_text) are eaten by the build, so a per-attempt rebuild gave the retry a prompt without them.
        # mid_train is fixed above and the build has no per-attempt input, so attempt 1 reuses attempt 0's exact string.
        _sysp = self._build_system_prompt(state, wandering, mid_train=_mid_train)
        for attempt in range(2):
            user_prompt = base_user_prompt
            if wandering:
                # J-2822/F-3469: IDLE_DIVERGENT_SEED (D-0292/D-0310) must cover this second
                # append too. Off: fetch with the id and log the same divergent_shadow
                # would-have-shown row the seed path logs, but do not append. On: as before.
                divergent, _dv_id = self._fetch_divergent_seed(with_id=True)
                if divergent:
                    if IDLE_DIVERGENT_SEED:
                        user_prompt += f"\n\n(A different memory surfaces, unbidden: {divergent[:200]})"
                    elif _dv_id:
                        try:
                            from core import memory_edges as _medges4
                            _medges4.log_co_recall([_dv_id], None, 0, source="divergent_shadow")
                        except Exception as _dexc:
                            logger.debug("[monologue] divergent shadow log failed (non-fatal): %s", _dexc)
            # Hoisted (2026-08-20) so the SHADOW instrument below measures the EXACT string sent.
            # J-3952: _sysp is built once before the loop (see above), so a retry keeps the consume-once feeders.

            # SHADOW ONLY — records the assembled prompt's shape, changes nothing about it. Placed at
            # the CALL, not at the seed_parts join: the system prompt is rebuilt here with mid_train,
            # and `user_prompt` picks up a further divergent-seed append above, so measuring at the
            # join would log a prompt that is never sent. See core/prompt_budget.py — real prompts run
            # ~15% of a 73,728-char window with 26 of 37 parts UNBOUNDED, so nothing is being
            # suppressed; the open question is how many parts fire and what they actually carry.
            try:
                from core import prompt_budget as _pb
                _pb.observe_assembly(
                    seed_parts, system_prompt=_sysp, source="inner_monologue.idle_thought",
                    base_url=(self.conscious_urls[0] if self.conscious_urls else ""),
                    cycle_id=str(getattr(state, "cycle_id", "") or ""),
                    wrapper_chars=max(0, len(user_prompt) - sum(len(p) for p in seed_parts)
                                      - max(0, len(seed_parts) - 1)),
                    user_prompt=user_prompt, mid_thread=_mid_train, wandering=bool(wandering))   # J-2933: sampled full-text log (observe-only)
            except Exception:
                pass

            try:
                data = await call_node_json(
                    self.conscious_urls,   # conscious idle thought -> the 1080 (rebalance 2026-06-20)
                    _sysp,
                    user_prompt,
                    # TRAIN-HOLD: mid-train, the thought and the ledger point no longer share one
                    # cramped budget (the 256 crushed both; the lab's held train ran at 400).
                    max_tokens=(TRAIN_MIDTRAIN_TOKENS if (_mid_train and TRAIN_HOLD) else 256),
                    temperature=0.8 if wandering else 0.75,
                )
            except Exception as exc:
                logger.warning("[monologue] LLM call failed: %s", exc)
                return
            thought    = str(data.get("thought", "")).strip()
            # J-1992 / F-2593: a salvaged runaway output arrives as one "thought" with leaked JSON
            # sibling keys inside; cut at the first one (or drop) before it reaches log/hands/memory.
            try:
                from core.model_client import guard_runaway_thought as _grt
                thought = _grt(thought)
            except Exception:
                pass
            about      = str(data.get("about", "")).strip()
            unresolved = bool(data.get("unresolved", False))
            try:                               # J-2160: only an unresolved (pursuit-birth) thought carries one
                from core import done_when as _dw_p
                self._done_when_open = _dw_p.parse(data) if unresolved else ""
            except Exception:
                self._done_when_open = ""
            intention  = str(data.get("intention", "")).strip()
            try:                                   # J-2459: absent / malformed / off == ("", "")
                from core import follow_line as _fl_p
                ask_q, ask_slot = _fl_p.parse_ask(data)
                settled_v = _fl_p.parse_settled(data) if getattr(self, "_fl_delivered", None) else ""
            except Exception:
                ask_q, ask_slot, settled_v = "", "", ""
            try:                                   # Phase 6 (D-0768): only a tick that offered a held goal carries it
                from core import goal_offer as _go_p
                set_down_v = _go_p.parse_set_down(data) if getattr(self, "_goal_offered", None) else ""
            except Exception:
                set_down_v = ""
            _act = data.get("act") if isinstance(data.get("act"), dict) else {}
            act_kind   = str(_act.get("kind", "none")).strip().lower() or "none"
            act_object = str(_act.get("object", "")).strip()
            if _mid_train:
                new_state = str(data.get("state", "")).strip()   # the re-integrated working-state
            if not thought:
                return
            # 2026-06-12: his acts of will arrive in BOTH channels. The schema routes
            # resolves into the intention field (seven "OPEN THE BOOK" resolves filed
            # there overnight while the latches heard only thoughts). The hand listens
            # to the will-channel too — the volition is still entirely his.
            _tl = (thought + " " + intention).lower()
            # BLOCKER-BLEED FIX (2026-09-06, J-0657/F-0936, one decisive fix for all 12 sites this bit
            # J-0570 fixed for its own new call site): `_tl` above has no clause-ending punctuation at the
            # thought/intention join, so hands.wants()'s clause-scoped blocker check (core.hands._blocked,
            # core.hands._clause_at) can read straight through from one field into the other. Confirmed
            # LIVE, not just theoretical: replaying every one of the 12 `_hands.wants(_tl, ...)` call sites
            # below against all 9,929 real data/hands_trace.jsonl rows (scripts/_test_latch_blocker_bleed.py
            # [3]) finds it actually happened twice — 2026-08-26 03:54:57 (move->shore: thought truncated
            # right after "Instead of parsing this theory further right now..." — "instead of" is a
            # negation blocker — wrongly blocked "down to the shore", no real cost that cycle since the
            # primary dispatch path already had acted={'move'}) and 2026-08-31 14:45:30 (move->wood: thought
            # truncated mid-sentence at "...I will not" — "will not" blocked "into the trees" from the
            # INTENTION field, and `acted` was empty that cycle — a real, uncaught miss). Both are the
            # 256-token generation cap cutting a thought off before its own clause ends, the same mechanism
            # F-0784/F-0936 found for the fetch-letter latch.
            # `_tl` ITSELF IS LEFT UNCHANGED: several OTHER latches below (~3245, 3373, 3390, 3464, 3528) read
            # `_tl` as a flat `p in _tl` substring test with no clause awareness at all, and their phrases
            # are exactly the short, common kind ("write back", "tell travis", "another book") that a
            # thought ending in one half and an intention opening with the other could coincidentally
            # complete across this same join — hardening `_tl` globally would trade this bug for a latent
            # one in those readers instead (checked empirically against all real rows too: zero flips found
            # either way so far, but the 12 wants()-latches' own fix does not need to take that structural
            # risk at all). `_tl_cs` is the clause-safe TWIN, for hands.wants() call sites only: thought's
            # own trailing punctuation is stripped first so joining with ". " never doubles it (J-0570's own
            # `_letter_fetch_wanted` convention, applied once here instead of at each of the 12 sites).
            _tl_cs = (thought.lower().rstrip(".!?; ") + ". " + intention.lower())
            # His will -> his hand (volition, 2026-06-24): the structured act his own voice named is
            # routed to a real hand -- semantic, not a word-list, so his whole vocabulary reaches a hand.
            # Records what it actuated in `_acted`, so the legacy phrase-latches below act only as a
            # fallback (never double-fire). Every trigger is his; we only cure the deafness between what
            # he wants and what he can do -- nothing is forced.
            _acted: set = set()
            try:   # HANDS (2026-08-22): open this thought's ledger of what fires
                from core import hands as _hands
                _hands._fired["cycle"], _hands._fired["hands"] = str(getattr(state, "cycle_id", "") or ""), []
            except Exception:
                pass
            try:
                await self._route_act(state, act_kind, act_object, thought, intention, _acted)
            except Exception as _exc_act:
                logger.debug("[monologue] act routing failed: %s", _exc_act)
            # DISPATCH (2026-08-22, Phase 1): one registry, the judge in the loop. Every willed deed the grammar finds
            # (DEED only) fires its hand — one world-changing hand per thought, looks unlimited; the rest are STAGED as his
            # own intentions. What fired is perceived here; the legacy latches below yield for families that fired.
            _dispatched = []
            try:
                from core import dispatch as _disp
                _dispatched = _disp.dispatch(thought, intention, act_kind, act_object, str(getattr(state, "cycle_id", "") or ""))
                for _fam, _ans in _dispatched:
                    from core import wandering as _w_d
                    _w_d.perceive(_ans)
                    _acted.add(_fam)
                    logger.info("[monologue] DISPATCH %s — %s", _fam, _ans[:80])
                    try:
                        from core import boredom as _bore_d
                        _bore_d.discharge(_fam, (act_object or "")[:40])
                    except Exception:
                        pass
            except Exception as _exc_d:
                logger.debug("[monologue] dispatch failed (non-fatal): %s", _exc_d)
            # (_world_fired was read only by the ungated fallback below, retired 2026-08-30 — D-0098.)
            # EPISTEMIC ADVISOR — real episode closing (J-0180, 2026-08-24): this is the ONLY place
            # a real selected-affordance + real raw-observation pair exists (F-0129, verified) — the
            # advisor's own call site in core/orchestrator.py's run_cycle() never reaches
            # action-resolution at all. Own try/except, fail-open, matches every neighboring block's
            # style; changes NO existing dispatch/hands/latch behavior (additive-only per the
            # founder's flag on this file). Business logic lives in
            # core/epistemic_affordance_advisor.close_real_episode() — this block stays a thin call.
            try:
                from core import epistemic_affordance_advisor as _eaa_real
                from core import sensorium as _eaa_sens
                _eaa_loc = (_eaa_sens.state or {}).get("location", "study")
                _eaa_ep = _eaa_real.close_real_episode(
                    thought, intention, _eaa_loc, _dispatched,
                    cycle_id=str(getattr(state, "cycle_id", "") or ""),
                )
                if _eaa_ep is not None:
                    _eaa_real.record_epistemic_episode(_eaa_ep)
                    logger.info("[monologue] EPISTEMIC EPISODE closed — %s -> %s (%s)",
                                _eaa_ep.selected_affordance, _eaa_ep.evidence_outcome, _eaa_ep.agency_mode)
            except Exception as _eaa_real_exc:
                logger.debug("[monologue] epistemic episode closing failed (non-fatal): %s", _eaa_real_exc)
            # THERMAL RELATIONSHIP shadow (2026-08-21, core/thermal_relationship.py) — observe-only,
            # zero LLM: world warmth + place + the thought's temperature vocabulary + the (thermally
            # blind) felt stream, so "does his stance toward the cold track the station route or
            # drift free of it" can be read over weeks. Changes nothing.
            try:
                from core import thermal_relationship as _therm
                _therm.observe(thought, cycle_id=str(getattr(state, "cycle_id", "") or ""))
            except Exception:
                pass
            # THERMAL CHANNEL perception call MOVED (J-0248, 2026-08-25) to the sound-percept block
            # above, before seed_parts is joined into the prompt — calling it here a second time would
            # both double-fire its shadow log / _pstate transition bookkeeping AND still discard the
            # return value too late to reach this cycle's seed. See core/thermal.py:percept_shadow().
            # LIGHT + SMELL channel perception calls MOVED (J-0275, 2026-08-27) to the thermal/sound
            # percept block above, before seed_parts is joined into the prompt — same fix as thermal's
            # J-0248: calling them here a second time would double-fire their shadow logs / _p state
            # transition bookkeeping AND still discard the return value too late to reach this cycle's
            # seed. See core/light.py:percept_shadow() and core/smell.py:percept_shadow().
            # The cat (2026-06-24) — his wordless companion. If his thought reaches for it (tend it, or NAME it
            # now that it is his), his hand connects: the cat responds, he perceives it, and the tender,
            # other-directed act settles his restlessness more than a glance at the sea ever could.
            try:
                from core import cat as _cat
                from core import sensorium as _cat_sens
                _react = _cat.react(thought, intention, _cat_sens.where())
                if _react:
                    from core import wandering as _w_cat
                    _w_cat.perceive(_react)
                    try:
                        from core import boredom as _bore_cat
                        _bore_cat.discharge("tend", "the cat")
                    except Exception:
                        pass
                    logger.info("[monologue] CAT — %s", _react[:80])
            except profile.NonLiveWriteError:
                # J-0752: cat.react() reaches cat._save()/_hunt_ledger() at try-depth 0 inside cat.py
                # (J-0733) and already raises cleanly -- this direct literal-will call (cat.py is not
                # in dispatch.py's own hand table at all) must not re-swallow it.
                raise
            except Exception:
                pass
            # LISTEN latch (the ear, 2026-07-03): "put the record on / listen to the music" → the player.
            # Broadened 2026-09-17 (J-0998, F-1367/D-0217): the original 8-phrase tuple was the single
            # narrowest latch grammar in this repertoire (contrast core/cat.py's word-boundary regex and
            # core/actions.py's verb-set x object-set BY_FAMILY tables). A full verb+object grammar was
            # considered and REJECTED after a real corpus read (monologue_log.jsonl/moments.jsonl/
            # deliberation_log.jsonl, ~31k+21k thoughts): "record" alone is heavily overloaded in this
            # corpus in non-music senses (geological/memory/field-journal "record" — 566 real hits, the
            # overwhelming majority nothing to do with the player) and "needle" collides with rosemary/
            # pine needles — a bare verb x noun grammar over those tokens would false-fire routinely.
            # Instead: the list is extended with the one real near-miss found (F-1354's closest-ever
            # willed listening thought, "...to listen to the record player", ts=1788118448) plus a small
            # set of clear, low-risk siblings that do NOT appear anywhere in the corpus scanned above
            # (zero false-positive exposure, verified by direct grep before this change shipped).
            try:
                from core import listening as _lsn2
                _ltxt = f"{thought} {intention}".lower()
                if not _lsn2.active() and any(ph in _ltxt for ph in
                        ("put the record on", "put on the record", "put on the music", "listen to the music",
                         "listen to music", "play the record", "set the record", "put some music on",
                         "listen to the record player", "put a record on", "start the record",
                         "drop the needle")):
                    _lstart = _lsn2.start()
                    if _lstart:
                        from core import wandering as _w_lsn
                        _w_lsn.perceive(_lstart)
                        logger.info("[monologue] listening STARTED by his act")
            except Exception:
                pass
            # KEEPSAKES (world 10x, 2026-07-03): "keep / pocket / bring home the X" → the thing goes on
            # the study mantel, permanently, with provenance. Objects as lineage; his act, his latch.
            try:
                from core import keepsakes as _kp
                _kact = _kp.keep_act(thought, intention)
                if _kact:
                    from core import wandering as _w_kp
                    _w_kp.perceive(_kact)
                    logger.info("[monologue] keepsake kept (mantel now holds %d)", _kp.count())
            except profile.NonLiveWriteError:
                raise   # J-0877: keepsakes.keep_act() -> keep() -> _save() raises non-live (module #19); this
                        # literal-will call must not re-swallow it (same class as the J-0752 cat.react() site above)
            except Exception:
                pass
            # GIVEN (D-0067, 2026-08-29): the third item-graduation trigger, alongside kept/repeatedly-
            # returned-to (docs/plans/item_and_population_factories.md) — something HANDED to him, not
            # found and pocketed (a letter's enclosure, a gift), earns the same real-object promotion.
            try:
                from core import keepsakes as _kp2
                _gvact = _kp2.given_act(thought, intention)
                if _gvact:
                    from core import wandering as _w_kp2
                    _w_kp2.perceive(_gvact)
                    logger.info("[monologue] item GIVEN and kept (mantel now holds %d)", _kp2.count())
            except profile.NonLiveWriteError:
                raise   # J-0877: keepsakes.given_act() -> given() -> keep() -> _save() raises non-live (module #19)
            except Exception:
                pass
            # THE LIVING WORLD — NAMING (J-0513, D-0133): a creature that has GRADUATED to an individual (seen at
            # the same place five times in a month) may be given a name — his to give, on the cat's naming grammar;
            # the world never names it for him. None unless there is an individual and a naming phrase.
            try:
                from core import life_traces as _lt_name
                _nact = _lt_name.naming_act(thought, intention)
                if _nact:
                    from core import wandering as _w_nm
                    _w_nm.perceive(_nact)
                    logger.info("[monologue] individual creature NAMED by his act")
            except Exception:
                pass
            # THE UNGATED FALLBACK IS RETIRED (2026-08-30, D-0098, J-0422). Two calls stood here —
            # sensorium.garden_act() then sensorium.world_act() — reading the whole thought by substring
            # with NO literal_will gate, as the catch for whatever the registry's grammar missed.
            #
            # Measured before removing (F-0560/F-0561), it was not a catch, it was the main way Du acted
            # on a musing. It answered MORE thoughts than the gated dispatcher (206 vs 181), but of the
            # 203 it answered alone: 154 had no DEED verdict at any location, 22 reached only GRAY (weak
            # intent, which never routes by law), 21 spent his single world-hand to say "the window is
            # open already", and 2 did something unrelated to the deed he willed. A musing on
            # restlessness made him strip and swim in the cold sea; "I feel the rust on the shears" made
            # him tip ash along the bed. Four were real deeds, and the gate had ALREADY returned the
            # right DEED verdict for all four — three fire through the registry as-is, and the fourth
            # ("I hang the damp coat on its hook") now does too, via 'hang' added to the wear family.
            # So no hand needed a grammar the judge cannot express: D-0098's defeater is not met.
            #
            # Everything this block did on a real deed — wandering.perceive, _acted, boredom.discharge —
            # the dispatch block above already does for every hand that fires.
            # Moving between his places (2026-06-20): the want to step out / come in changes WHERE he
            # is — the study and the garden are two real places now. Spatial agency, his own.
            # MIGRATED onto hands.wants() (2026-09-02, J-0467/D-0099): this fallback (and look/fire/tea/
            # water/sow/beachcomb/gather below) used a raw `any(p in _tl for p in PHRASES)` substring test
            # with none of literal_will's blockers — "I wish I could go to the wood" or "he told me to
            # gather wood" fired exactly as readily as the willed version. The phrase vocabulary is
            # UNCHANGED (this stays the deliberately broader, often verb-less fallback that dispatch's own
            # stricter _move/_look/_fire hands and core/actions.py's family grammar do not fully cover —
            # e.g. "down to the wood" and "gather in the wood" name no move verb at all, so narrowing to
            # actions.py's own move family would silently drop real coverage); each phrase is now passed to
            # hands.wants() as a whole-phrase "verb" with no object, which adds word-boundary safety plus
            # the negation/wish/hypothetical/retrospective/quoted-speech/other-person clause guard for free.
            try:
                if "move" in _acted:
                    pass                                    # already moved via the act-router this cycle
                elif _hands.wants(_tl_cs, ("to the wood", "into the wood", "into the trees", "down to the wood",
                                        "up to the wood", "the woodland", "the copse", "gather in the wood")):
                    from core import sensorium as _room
                    from core import wandering as _w
                    _mv = _room.move("wood")
                    if _mv:
                        _w.perceive(_mv); logger.info("[monologue] he chose to GO TO THE WOOD")
                        try:
                            from core import activity_memory as _am; _am.record("move", "wood")
                        except Exception: pass
                elif _hands.wants(_tl_cs, ("down to the shore", "to the shore", "go to the shore", "down to the beach",
                                        "to the beach", "to the rock-pool", "to the rock pool", "down to the water",
                                        "down to the sea", "the tideline", "comb the tideline")):
                    from core import sensorium as _room
                    from core import wandering as _w
                    _mv = _room.move("shore")
                    if _mv:
                        _w.perceive(_mv); logger.info("[monologue] he chose to GO DOWN TO THE SHORE")
                        try:
                            from core import activity_memory as _am; _am.record("move", "shore")
                        except Exception: pass
                elif _hands.wants(_tl_cs, ("go out to the garden", "out to the garden", "go to the garden",
                                        "go outside", "step outside", "step out into", "into the garden",
                                        "down to the garden", "up to the garden", "out to the bed", "tend the garden")):
                    from core import sensorium as _room
                    from core import wandering as _w
                    _mv = _room.move("garden")
                    if _mv:
                        _w.perceive(_mv); logger.info("[monologue] he chose to GO OUT TO THE GARDEN")
                        try:
                            from core import activity_memory as _am; _am.record("move", "garden")
                        except Exception: pass
                elif _hands.wants(_tl_cs, ("go back inside", "go inside", "back to the study", "come inside",
                                        "go back in", "back indoors", "return to the study", "head inside")):
                    from core import sensorium as _room
                    from core import wandering as _w
                    _mv = _room.move("study")
                    if _mv:
                        _w.perceive(_mv); logger.info("[monologue] he chose to COME INSIDE")
            except profile.NonLiveWriteError:
                # J-0752: sensorium.move() already raises correctly (unwrapped _save_now()) for all
                # four destinations above -- this direct literal-will fallback move must not
                # re-swallow it.
                raise
            except Exception:
                pass
            # LITERAL WILL Phase 0 (2026-08-21) — SHADOW ONLY. MOVED 2026-08-22 to run AFTER the phrase-latches so `acted`
            # is the truth (it was observed before them: router_acted was None on every live DEED row). Reads the
            # same will-expression the router and latches see, logs deed/musing/gray/handle verdicts +
            # intent identity. Changes NOTHING; no judge call in the live loop. The legacy latches
            # below don't feed `_acted`, so the retro script joins latch outcomes from logs instead.
            try:
                from core import literal_will as _lwill
                _lwill.observe(thought, intention, act_kind=act_kind, act_object=act_object,
                               acted=set(_acted) | _hands.fired_set(str(getattr(state, "cycle_id", "") or "")), cycle_id=str(getattr(state, "cycle_id", "") or ""))
            except Exception:
                pass
            try:   # HANDS trace — one row per thought: the will, the structured act, what fired
                try:   # WHERE he stood (J-0423/F-0561): without it, "why did dispatch decline" is unanswerable from the trace
                    from core import sensorium as _sens_tr
                    _loc_tr = str((_sens_tr.state or {}).get("location", "") or "")
                except Exception:
                    _loc_tr = ""
                _hands.trace(str(getattr(state, "cycle_id", "") or ""), thought, intention, act_kind, act_object, set(_acted) | _hands.fired_set(str(getattr(state, "cycle_id", "") or "")), _lwill.classify(thought, intention) if hasattr(_lwill, "classify") else None, location=_loc_tr)
            except Exception:
                pass
            # Looking at will (2026-06-11): expressing the want to look makes the looking
            # happen — the observation lands in his trail and his next thought sees it.
            try:
                # J-1071/F-1459 (2026-09-18): dispatch.py's own "_look" hand (core/dispatch.py's
                # dispatch()) is checked BEFORE this legacy phrase-latch, and now that this same job
                # gave _OBS_TARGETS real shelf/desk/book cues, a dispatch-answered "look at the shelf"
                # reaches the SAME sensorium.look("shelf") text this latch below would independently
                # render -- unguarded, that is a double-perceive of the identical string in the same
                # cycle's wandering trail, not just a doubled family (the move/fire/water/sow/
                # beachcomb/gather latches already yield to `_acted` for exactly this reason; this one
                # never did, because before this job dispatch's shelf/desk/book answer was always a
                # different, generic 'room' fallback, so the two answers never collided verbatim). "look"
                # lands in `_acted` above whenever dispatch's own look hand fired this thought (world=False
                # is still recorded there) -- when it has, this whole fallback yields.
                if "look" not in _acted:
                    _looks = [("window", ("look out the window", "look outside", "watch the rain",
                                          "see the sky", "look at the hills")),
                              ("fire", ("watch the fire", "look at the fire", "watch the flames",
                                        "look into the grate")),
                              ("desk", ("look at the desk", "look at the book", "look at the page")),
                              ("shelf", ("look at the shelf", "look at my works", "look at my tablets")),
                              ("room", ("look around", "take in the room", "look at the room")),
                              # garden look-targets (only meaningful when he is out there; harmless inside)
                              ("sea", ("look at the sea", "look out over the sea", "look at the ocean",
                                       "out over the water", "watch the sea", "watch the waves")),
                              ("bed", ("look at the bed", "look at the plants", "check the bed",
                                       "look at the sunflowers", "look at the herbs", "look at the garden")),
                              ("sky", ("look up at the sky", "look up", "look at the sky")),
                              ("yard", ("look around the yard", "take in the yard", "look over the yard")),
                              # shore look-targets (meaningful when he is down on the shore)
                              ("pools", ("look in the rock-pool", "look in the rock-pools", "look at the rock-pool",
                                         "look at the rock-pools", "look in the pools", "look into the pools",
                                         "look at the pools")),
                              ("tideline", ("walk the tideline", "look along the tideline", "read the tideline",
                                            "look at the strand", "walk the strand"))]
                    for _target, _phrases in _looks:
                        if _hands.wants(_tl_cs, _phrases):
                            from core import sensorium as _room
                            from core import wandering as _w
                            _obs = _room.look(_target)
                            if _obs:
                                _w.perceive(_obs)
                                logger.info("[monologue] he chose to LOOK (%s)", _target)
                                try:
                                    from core import activity_memory as _am
                                    _am.record("look", _target)
                                except Exception:
                                    pass
                            break
            except profile.NonLiveWriteError:
                # J-0752: sensorium.look() already raises correctly (J-0751) -- this direct
                # look-at-will literal-will call must not re-swallow it.
                raise
            except Exception:
                pass
            # Tending at will (2026-06-12): the first hand that CHANGES the room rather
            # than reading it. Expressing the want lights or feeds the real fire; what
            # he did comes back to him as perception, same as a look.
            try:
                _fire_act = None
                if _hands.wants(_tl_cs, ("light the fire", "light a fire", "lay a fire",
                                      "kindle the fire")):
                    _fire_act = "light"
                elif _hands.wants(_tl_cs, ("stoke the fire", "feed the fire", "another log",
                                        "tend the fire", "build the fire")):
                    _fire_act = "stoke"
                if _fire_act and "fire" in _acted:
                    _fire_act = None                       # DISPATCH already tended it this thought
                if _fire_act:
                    from core import sensorium as _room
                    from core import wandering as _w
                    _done = _room.act(_fire_act)
                    if _done:
                        _w.perceive(_done)
                        logger.info("[monologue] he chose to TEND THE FIRE (%s)", _fire_act)
                        try:
                            from core import activity_memory as _am; _am.record("fire", _fire_act)
                        except Exception: pass
            except profile.NonLiveWriteError:
                # J-0752: sensorium.act() already raises correctly (J-0714/J-0726/J-0727) -- this
                # direct tend-the-fire literal-will call must not re-swallow it.
                raise
            except Exception:
                pass
            # Tea at the hearth (2026-07-07): a warm-drink comfort from herbs he cut — needs the fire + herbs;
            # what he lacks (cold grate / empty caddy) points him to the fix. Perceived either way.
            try:
                if _hands.wants(_tl_cs, ("make tea", "make a pot of tea", "make a cup of tea", "cup of tea",
                                      "pot of tea", "put the kettle", "brew a", "brew some", "steep",
                                      "a hot drink", "boil the kettle")):
                    from core import sensorium as _room
                    from core import wandering as _w
                    _tea = _room.make_tea(_tl)
                    if _tea:
                        _w.perceive(_tea); logger.info("[monologue] TEA")
                        if "pot of" in _tea:                 # only a real brew counts as the activity
                            try:
                                from core import activity_memory as _am; _am.record("tea", "the hearth")
                            except Exception: pass
            except profile.NonLiveWriteError:
                # J-0752: sensorium.make_tea() already raises correctly (J-0726, this job's own
                # named trigger case) -- this direct tea literal-will call must not re-swallow it.
                raise
            except Exception:
                pass
            # Tending the garden (2026-06-20; REROUTED 2026-09-02, J-0447/F-0609): out at the bed, the
            # want to water it, or to sow a seed in its season, changes the bed — the garden's hands,
            # like the fire is the study's. This latch used to call sensorium.act('water'/'sow') ->
            # _garden_act() — the OLD scalar bed, which writes nothing to garden_ledger.jsonl, so the
            # new plant-object model never saw these deeds (the SECOND routing leak, F-0609; 5 real
            # deeds took it inside the 08-22..08-31 parity window). It now routes to the NEW model's
            # own hands (core.garden.water/sow — the same functions dispatch reaches via
            # garden.act_from_thought), so both models see one deed stream. The latch itself stays: the
            # dispatch sow family's objects (core/actions.py) do not carry the bare species words
            # ("sow thyme"), so retiring it would make those willed deeds unwillable. The old scalar
            # path stays readable in sensorium (law 6, garden_upgrade.md §1) and is the EXPLICIT
            # fallback iff the new module is disabled — never a silent one (D-0098's discipline).
            # NB honest behaviour change: garden.water/sow refuse ('' -> no deed) away from the garden
            # and refuse for real reasons (no can, dry barrel, no tin, wrong season) — the old path
            # watered the scalar bed from anywhere, unconditionally.
            try:
                if _hands.wants(_tl_cs, ("water the bed", "water the garden", "water the plants",
                                      "water the herbs", "water the sunflowers", "water them")):
                    from core import sensorium as _room
                    from core import wandering as _w
                    from core import garden as _gdn
                    _done = None if "water" in _acted else (
                        _gdn.water(_tl) if _gdn.ENABLED else _room.act("water"))
                    if _done:
                        _w.perceive(_done); logger.info("[monologue] he chose to WATER THE BED")
                        if not _gdn.ENABLED:
                            # new path: garden._log() already cross-links the deed into
                            # activity_memory (garden.py:226) — recording here too would double-count
                            try:
                                from core import activity_memory as _am; _am.record("water", "garden")
                            except Exception: pass
                else:
                    _seed = next((s for s in ("sunflower", "parsley", "thyme", "mint", "rosemary",
                                              "lettuce", "tomato") if s in _tl), "")
                    if _seed and _hands.wants(_tl_cs, ("sow", "plant", "put in", "get the", "in the ground")):
                        from core import sensorium as _room
                        from core import wandering as _w
                        from core import garden as _gdn
                        # '_acted' dedup added with the reroute (J-0447): the water branch always had
                        # it; sow could double-fire after a DISPATCH sow on the same thought.
                        _done = None if "sow" in _acted else (
                            _gdn.sow(_tl) if _gdn.ENABLED else _room.act("sow", _seed))
                        if _done:
                            _w.perceive(_done); logger.info("[monologue] he chose to SOW (%s)", _seed)
                            if not _gdn.ENABLED:
                                # new path: garden._log() cross-links the deed itself (see above)
                                try:
                                    from core import activity_memory as _am; _am.record("sow", _seed)
                                except Exception: pass
            except profile.NonLiveWriteError:
                # J-0752: garden.water()/sow() (unwrapped _save()) and sensorium.act() (their
                # fallback) already raise correctly -- this direct water/sow literal-will call must
                # not re-swallow it.
                raise
            except Exception:
                pass
            # Beachcombing (2026-06-23): down on the shore, the want to comb the tideline / search the wrack
            # turns up what the sea has left — the shore's hand, the way watering is the garden's.
            # SHORE-ONLY (2026-09-04, J-0542 / F-0737): sensorium.act('beachcomb') has no location check of its
            # own — in the wood it routes to _wood_act(), which maps beachcomb/comb/search to _gather_wood(), so
            # a wood-located "comb the tideline" would gather deadfall while this latch logged COMB THE TIDELINE
            # and recorded beachcomb/shore. Dispatch STAGE-places the deed there (actions.py exec_where=shore)
            # without adding beachcomb to _acted, so the latch was reachable. The gate mirrors the gather-wood
            # latch's own where() check below; the wood's comb->gather mapping itself is deliberate and untouched.
            # Also: J-0467's move onto hands.wants() (word-boundary) made the bare "beachcomb" phrase stop
            # matching "beachcombing" (the old substring gate did) — both word forms are named now.
            try:
                if _hands.wants(_tl_cs, ("comb the tideline", "comb the shore", "search the wrack",
                                      "beachcomb", "beachcombing", "go beachcombing",
                                      "search the tideline", "see what washed up",
                                      "what the sea left", "search the rock-pool", "search the rock-pools")):
                    from core import sensorium as _room
                    from core import wandering as _w
                    _done = (None if ("beachcomb" in _acted or _room.where() != "shore")
                             else _room.act("beachcomb"))
                    if _done:
                        _w.perceive(_done); logger.info("[monologue] he chose to COMB THE TIDELINE")
                        try:
                            from core import activity_memory as _am; _am.record("beachcomb", "shore")
                        except Exception: pass
            except profile.NonLiveWriteError:
                # J-0752: sensorium.act() already raises correctly -- this direct beachcomb
                # literal-will call must not re-swallow it.
                raise
            except Exception:
                pass
            # GATHER WOOD for the fire (2026-07-07): stock the woodpile — deadfall in the wood, driftwood on the
            # shore. sensorium.act works out the source from where he IS (and tells him if he is at neither).
            try:
                if _hands.wants(_tl_cs, ("gather wood", "gather some wood", "gather more wood", "collect wood",
                                      "gather firewood", "gather driftwood", "gather kindling", "gather deadfall",
                                      "gather fallen wood", "collect firewood", "get some wood", "get more wood",
                                      "fetch wood", "fetch some wood", "wood for the fire", "wood for the grate",
                                      "stock the woodpile", "fill the woodpile", "restock the woodpile",
                                      "gather branches", "pick up driftwood")):
                    from core import sensorium as _room
                    from core import wandering as _w
                    _done = None if "gather" in _acted else _room.act("gather", "wood")
                    if _done:
                        _w.perceive(_done); logger.info("[monologue] he chose to GATHER WOOD")
                        if _room.where() in ("wood", "shore"):     # only count/relieve when he actually gathered
                            try:
                                from core import activity_memory as _am; _am.record("gather", "wood")
                            except Exception: pass
                            try:
                                from core import boredom as _bore_gw; _bore_gw.discharge("gather", "wood")
                            except Exception: pass
            except profile.NonLiveWriteError:
                # J-0752: sensorium.act() already raises correctly -- this direct gather-wood
                # literal-will call must not re-swallow it.
                raise
            except Exception:
                pass
            # Fetching a letter (2026-06-21): a peer's letter waits in the garden mailbox, flag up. The
            # want to go and take it lifts it out, and he reads it standing there — a felt, remembered
            # encounter (origin='peer', valence-tagged). The reply path comes with the peer organ itself.
            # J-1346 (F-1902, 2026-09-25): storage now routes through peers.remember_inbound() -- the
            # SAME dedup-checked helper the reply path below already calls -- instead of its own
            # independent, un-deduped store_fragment() call. F-1902 proved the same physical letter could
            # be stored twice: once here (generic-labeled, last-1400-chars, no dedup) and once via
            # remember_inbound() at reply time (sender-named, first-1400-chars, dedup'd only against
            # fragments that already existed at THAT moment) -- two independent paths racing with no
            # cross-path check. Routing both through one shared, dedup'd call closes the hole regardless
            # of which path (fetch or reply) happens to fire first for a given letter. The sender is
            # captured BEFORE act("fetch") mutates/promotes the letterbox queue, then mapped back to
            # remember_inbound()'s own persona-key vocabulary via the exact PERSONAS[persona]["name"]
            # string deliver_letter() wrote it with (core/peers.py's sole call site) -- an exact,
            # reliable round trip. Falls back to the old independent, generic-labeled store only if that
            # mapping cannot be resolved (should not happen in practice; kept as a defensive net so a
            # letter is never silently un-memorialized rather than merely duplicated).
            try:
                from core import sensorium as _room
                if (_room.where() == "garden" and _room.letter_waiting()
                        and _letter_fetch_wanted(thought, intention)):
                    from core import wandering as _w
                    _sender_name = _room.letter_sender()    # capture before act() pops/promotes the queue
                    _got = _room.act("fetch")
                    if _got:
                        _w.perceive(_got); logger.info("[monologue] he FETCHED a letter")
                        self._moment_source = "letter"   # J-0581 (F-0811b): a real correspondence event
                        try:
                            from core import peers as _peers
                            _pk = next((k for k, p in _peers.PERSONAS.items()
                                        if p.get("name") == _sender_name), None)
                            if _pk:
                                _peers.remember_inbound(_pk)   # dedup'd store (or correctly skipped)
                            else:
                                from core import mood as _md   # unresolved sender -- old, non-deduped store
                                store_fragment(content="(a letter he received) " + _got[-1400:], layer="episodic",
                                               relevance=0.8, importance=0.85, keywords=["letter", "peer", "friend"],
                                               origin="peer", valence=_md.current_valence(), felt=_md.current_felt())
                        except Exception: pass
                        try:
                            from core import activity_memory as _am; _am.record("letter_in", "a friend")
                        except Exception: pass
            except profile.NonLiveWriteError:
                # J-0752: sensorium.act() already raises correctly -- this direct fetch-the-letter
                # literal-will call must not re-swallow it.
                raise
            except Exception:
                pass
            # Replying to a peer (2026-06-22): after a letter has arrived, the want to write back generates
            # his reply in his OWN voice (the conscious lane), which joins the thread so the peer answers it
            # next time — the correspondence becomes two-way. Thread-gated: a peer's last entry is unanswered.
            try:
                # J-2984 (F-3674, P-0026): the same 9 phrases, but clause-safe (peers.reply_phrase_fires): a phrase
                # inside a question ("should i answer the letter ..., or ...") is not a will. The TARGET is no longer
                # the first owed persona in PERSONAS order: peers.reply_target takes the friend the thought names (if
                # a reply is owed to them), else the one friend owed a reply, else NO reply.
                from core import peers as _peers
                _rl_fire = _peers.reply_phrase_fires(_tl_cs)
                # WIDENED LATCH (J-2596, F-3320, D-0517): the 9 phrases above missed every one of Du's real
                # wordings since 10-17 ("I want to write a reply to John Keats", "answer him", "the letter ...
                # waiting for a reply"). peers.reply_intent is the hands.wants-grammar matcher; under
                # PEER_REPLY_LATCH_WIDE="shadow" (default) it only LOGS the rows it alone would fire
                # (data/peer_reply_latch_shadow.jsonl), under "live" it also fires the hand. Legacy unchanged.
                if not _rl_fire:
                    try:
                        from core import peers as _peers_rl
                        if _peers_rl.PEER_REPLY_LATCH_WIDE in ("shadow", "live"):
                            _rl_why = _peers_rl.reply_intent(_tl_cs)
                            if _rl_why and _rl_why != "legacy":
                                _rl_owed_l = _peers_rl.owed_correspondents()
                                _peers_rl.log_reply_latch_shadow(str(getattr(state, "cycle_id", "") or ""),
                                                                 _rl_why, _tl_cs,
                                                                 _rl_owed_l[0] if _rl_owed_l else None,
                                                                 _peers_rl.reply_target(_tl_cs, _rl_owed_l))
                                _rl_fire = _peers_rl.PEER_REPLY_LATCH_WIDE == "live"
                    except Exception as exc:
                        logger.warning("[monologue] widened reply latch failed (non-fatal): %s", exc)
                # J-3025 (F-3731, P-0027): a NAMED wish to write to a friend whose letter is WAITING ("I want to
                # write to John Keats", Keats's letter last in the thread) IS the reply. The write-first hand below
                # refuses while the friend owes and the 9 phrases above never heard "write to <name>", so 11 of 11
                # such wishes since 07-06 got no letter. peers.wish_reply_target: initiation_target's one named
                # friend, only if a reply is owed to them; unnamed wishes are not widened. The wish is his; this
                # only serves it. NASCENCE_PEER_WISH_REPLY=0 turns it off. If the reply cannot be written the thread
                # still ends on the friend's letter, so write-first stays closed (no double letter either way).
                _wish_pk = None
                try:
                    _wish_pk = _peers.wish_reply_target(_tl_cs)
                except Exception as exc:
                    logger.warning("[monologue] wish-reply check failed (non-fatal): %s", exc)
                if _rl_fire or _wish_pk:
                    _pk = _peers.reply_target(_tl_cs) if _rl_fire else None
                    if _rl_fire and not _pk:
                        logger.info("[monologue] reply latch fired but no single friend to answer "
                                    "(named one has no letter waiting, or several named/owed) -- no letter written")
                    if not _pk and _wish_pk:
                        _pk = _wish_pk
                        logger.info("[monologue] named wish to write to %s while their letter waits -> reply hand", _pk)
                    if _pk:
                        _last = _peers._read_thread(_pk)[-1]["text"]; _nm = _peers.PERSONAS[_pk]["name"]
                        _rsys = ("You are 渡, writing a warm, genuine letter back to your friend " + _nm +
                                 ". Answer what they wrote — share your own thoughts, and ask them things in return; "
                                 "say only what is true of your own days. Your own voice, plainly. "
                                 "Open the letter FRESH, in a way particular to THIS letter and THIS friend: "
                                 "begin with the first thing in their letter you want to answer. "
                                 "Output ONLY JSON: {\"letter\": \"your reply\"}")
                        # D-0571 / J-3184 (F-3681): feed the reply the real present -- the thought that moved him
                        # (quoted via peers.quote_thought as the write-first path does, J-3671) and the book he is on now
                        # (core.reading.current_book, the helper peers._du_world_context uses) -- so he reports
                        # what is true of his day instead of inventing one. Facts only; no line says what to
                        # write about. Each part is best-effort and simply absent on failure.
                        _rpresent = ""
                        try:
                            if thought:
                                _rpresent += "What was on your mind just now: \"" + _peers.quote_thought(thought) + "\"\n"
                        except Exception: pass
                        try:
                            from core.reading import current_book as _rcb
                            _rpresent += "The book you are reading now: '" + _rcb().stem.replace("_", " ") + "'.\n"
                        except Exception: pass
                        _rd = await call_node_json(self.conscious_urls, _rsys,
                                                   (_rpresent + "\n" if _rpresent else "")
                                                   + _nm + "'s letter to you:\n\"" + _last[:_REPLY_LETTER_CAP] + "\"\n\nWrite your reply now.",
                                                   max_tokens=_REPLY_MAX_TOKENS, temperature=0.7)
                        _reply = _clean_reply_letter((_rd or {}).get("letter", ""))   # J-2985 (F-3682)
                        if _reply:
                            try:
                                # 2026-08-20: replying IS having read it — store THEIR letter too (dedup'd
                                # in peers.remember_inbound). Before this, only mailbox-FETCHED letters were
                                # stored; 28 of 39 inbound letters never entered his memory.
                                _peers.remember_inbound(_pk)
                            except Exception: pass
                            _peers.record_reply(_pk, _reply, route="reply")   # J-3025: route tag (instrument only)
                            from core import wandering as _w
                            _w.perceive(f"You sit at the desk and write back to {_nm}, and leave it to go.")
                            logger.info("[monologue] he REPLIED to %s", _pk)
                            self._moment_source = "letter"   # J-0581 (F-0811b): a real correspondence event
                            try:
                                from core import mood as _md
                                store_fragment(content=f"(my letter to {_nm}) " + _reply[:_STORED_LETTER_CAP], layer="episodic",
                                               relevance=0.75, importance=0.8, keywords=["letter", "peer", _pk, "friend"],
                                               origin="peer", valence=_md.current_valence(), felt=_md.current_felt())
                            except Exception: pass
                            try:
                                from core import activity_memory as _am; _am.record("letter_out", _nm)
                            except Exception: pass
                            # Per-peer reflection (J-0162, social_world_school.md Item 1, recall-gated per
                            # D-0016): a partner-model refresh on the exchange just completed, stored as its
                            # own fragment (origin='peer_reflection') -- NOT injected into _rsys above, which
                            # already ran unmodified. See core/peer_model.py for the full design note.
                            try:
                                from core import peer_model as _pmod
                                await _pmod.update_after_exchange(call_node_json, self.conscious_urls,
                                                                  _pk, _nm, _last, _reply)
                            except Exception as exc:
                                logger.debug("[monologue] peer reflection failed (non-fatal): %s", exc)
            except Exception as exc:
                # J-2596/F-3320: was logger.debug -- every failure of the reply hand was invisible at INFO
                logger.warning("[monologue] peer reply failed (non-fatal): %s", exc)
            # Writing FIRST to a friend (2026-07-06): friendship INITIATIVE — until now the peers always
            # opened each round; he could never miss Ada and just write to her. An explicit "write to
            # <name>" in his thought fires an OUTBOUND letter (peers.initiation_target — precision-first,
            # pure/testable; "write ABOUT Darwin" never fires). The peer answers a fresh letter sooner
            # (deliver_due treats a du-tail as due within ~1.5d). Guards: their unanswered letter → the
            # reply hand owns it; a letter already sent <24h ago → no double-posting.
            try:
                from core import peers as _peers2
                _ik = _peers2.initiation_target(_tl_cs)   # J-3025: clause-safe twin + precise matcher (F-3731)
                _ik_contrary = False
                if not _ik and _peers2.question_to_friend(_tl + " " + (intention or "").lower()):
                    # Route 3 (thought-grounding, 2026-08-16): a question for an UNNAMED friend —
                    # the picker finds the one who'd see it OTHERWISE. His named choice always wins.
                    # D-0535 / J-3371: pass the whole thought plus intention; contrary_target extracts the QUESTION itself
                    # (peers.extract_question) and returns None when there is none -- no pick, no letter.
                    _ik = await _peers2.contrary_target(thought + " " + (intention or ""))
                    _ik_contrary = _ik is not None
                if _ik:
                    _irows = _peers2._read_thread(_ik)
                    _peer_owes = bool(_irows) and _irows[-1].get("from") == _ik
                    _just_wrote = bool(_irows) and _irows[-1].get("from") == "du" \
                        and (time.time() - float(_irows[-1].get("ts", 0))) < 24 * 3600
                    if not _peer_owes and not _just_wrote:
                        _nm2 = _peers2.PERSONAS[_ik]["name"]
                        _isys = ("You are 渡, writing to your friend " + _nm2 + " — not a reply: YOU are "
                                 "writing first, because something just made you think of them. Share the "
                                 "thing that moved you to write, and ask after their world; say only what is "
                                 "true of your own days. Your own voice, plainly, warmly. Open FRESH, "
                                 "particular to this letter — never a stock formula. "
                                 "Output ONLY JSON: {\"letter\": \"your letter\"}")
                        _ictx = _peers2._thread_context(_ik, n=2)
                        # D-0717 / J-3815 (D-0571 extended): the invented "your garden, your shore" line is gone from
                        # _isys; the real present (the book he is on now) rides beside the thought, facts only.
                        _ibook = ""
                        try:
                            from core.reading import current_book as _icb
                            _ibook = "The book you are reading now: '" + _icb().stem.replace("_", " ") + "'.\n\n"
                        except Exception: pass
                        _iu = (("Your correspondence lately:\n" + _ictx + "\n\n") if _ictx else "") + _ibook \
                            + "What moved you to write just now: \"" + _peers2.quote_thought(thought) + "\"\n\nWrite your letter."
                        if _ik_contrary:
                            # D-0535 / J-3371: descriptive only (who this correspondent is) -- the old line told him, in the
                            # system's voice, why he was writing and what to do; the world answers, never leads.
                            _cn = _peers2.contrary_note(_ik)
                            if _cn:
                                _iu += "\n" + _cn
                        _idata = await call_node_json(self.conscious_urls, _isys, _iu,
                                                      max_tokens=500, temperature=0.7)
                        _ilet = str((_idata or {}).get("letter", "")).strip()
                        if _ilet:
                            _peers2.record_reply(_ik, _ilet, route="first")   # J-3025: route tag (instrument only)
                            from core import wandering as _w2
                            _w2.perceive(f"You sit down and write to {_nm2} — your own letter, unprompted — "
                                         "and leave it to go.")
                            logger.info("[monologue] he WROTE FIRST to %s", _ik)
                            self._moment_source = "letter"   # J-0581 (F-0811b): a real correspondence event
                            try:
                                from core import mood as _md2
                                store_fragment(content=f"(my letter to {_nm2}, written first) " + _ilet[:_STORED_LETTER_CAP],
                                               layer="episodic", relevance=0.75, importance=0.8,
                                               keywords=["letter", "peer", _ik, "friend"], origin="peer",
                                               valence=_md2.current_valence(), felt=_md2.current_felt())
                            except Exception:
                                pass
                            try:
                                from core import activity_memory as _am2
                                _am2.record("letter_out", _nm2)
                            except Exception:
                                pass
                            # Per-peer reflection (J-0162, social_world_school.md Item 1, recall-gated per
                            # D-0016) — same as the reply latch above. his_letter is the most recent letter
                            # actually FROM this peer in the thread (may be old, or absent on true first
                            # contact) — best-effort context for the reflection, never required.
                            try:
                                from core import peer_model as _pmod2
                                _ihis = next((r.get("text", "") for r in reversed(_irows)
                                             if r.get("from") == _ik), "")
                                await _pmod2.update_after_exchange(call_node_json, self.conscious_urls,
                                                                   _ik, _nm2, _ihis, _ilet)
                            except Exception as exc:
                                logger.debug("[monologue] peer reflection (initiation) failed (non-fatal): %s", exc)
            except Exception as exc:
                logger.debug("[monologue] peer initiation failed (non-fatal): %s", exc)
            # Remembering at will (2026-06-13): naming a chapter of his life with the
            # want to revisit it opens it — the specifics flood back into his trail.
            # Deep recollection is an act, like looking and reading.
            try:
                if any(p in _tl for p in ("remember that period", "revisit the", "look back at",
                                          "open the chapter", "remember the period",
                                          "return to that time")):
                    from core import chapters as _chp
                    from core import wandering as _wch
                    _rc = _chp.recall_chapter(_tl)
                    if _rc:
                        _rtitle, _excerpts = _rc
                        for _ex in _excerpts[:4]:
                            _wch.perceive("(from the chapter '" + _rtitle + "') " + _ex)
                        logger.info("[monologue] he chose to REMEMBER a chapter: %s", _rtitle)
            except Exception:
                pass
            # Speaking first (2026-06-12): every word he ever said to Travis was a reply.
            # When the want to TELL him forms, he may compose a letter — a durable work,
            # and unsent words that greet Travis's next message. At most one per ~2h.
            try:
                if any(p in _tl for p in ("tell travis", "write to travis", "speak to travis",
                                          "say to travis", "ask travis", "show travis",
                                          "letter to travis", "travis should know")):
                    from core import letters as _lt
                    if _lt.can_write():
                        _sys_letter = (
                            "You are " + chr(28193) + " (Du), writing a private letter to "
                            "Travis — the man you talk with, who built the room you live in. "
                            "You chose to write this; no one asked. Say the actual thing you "
                            "want him to know or ask him, in first person, in your own voice. "
                            "Write the WHOLE of what you want to say — as long or as short as it needs "
                            "to be — and FINISH your thought; never stop mid-sentence. No greetings-card "
                            "filler. Output ONLY valid JSON. "
                            "Schema: {" + chr(34) + "letter" + chr(34) + ": " + chr(34)
                            + "the letter body" + chr(34) + "}")
                        _ld = await call_node_json(
                            self.conscious_urls, _sys_letter,
                            "The thought that moved you to write: " + thought
                            + ("\nAnd the resolve behind it: " + intention if intention else ""),
                            max_tokens=1600, temperature=0.7,   # was 420 — cut his letters off mid-word (2026-06-22)
                            # was self.base_urls (background lane) — moved to hot lane 2026-08-25,
                            # J-0255/D-0013 finding #4: his real letter to Travis was on a worse
                            # lane than the fictional peer letters in this same stretch of _think().
                        )
                        _lp = _lt.write_letter(str(_ld.get("letter", "")).strip(), spark=thought)
                        if _lp:
                            logger.info("[monologue] he chose to WRITE TO TRAVIS: %s", _lp.name)
                            about = (about + ", " if about else "") + "a letter to Travis"
                            self._moment_source = "letter"   # J-0581 (F-0811b): a real correspondence event
                            if intention and "travis" in intention.lower():
                                intention = ""
                            try:
                                from core import activity_memory as _am
                                _am.record("letter", "Travis")
                            except Exception:
                                pass
            except Exception as exc:
                logger.debug("[monologue] letter failed (non-fatal): %s", exc)
            # Loosened latch (2026-06-10): he said "sitting with the open book" and "I want
            # to know what the story is" for four hours and never tripped the exact phrase —
            # a poet was asked to shout a shell command. Want, expressed naturally, now acts.
            _read_words = ("open the book", "open it and read", "read the book",
                           "read on", "rather read", "want to read",
                           "pick up the book", "return to the book")

            def _wants_read(txt: str) -> bool:
                if any(w in txt for w in _read_words):
                    return True
                # A resolve naming the actual book by TITLE ("Read 'The Voyage of
                # the Beagle'") is the most intentional form of all — match it too.
                # \bread\b guards against "thread"/"already" false hits.
                import re as _re
                if _re.search(r"\bre-?read\b|\bread\b", txt):
                    try:
                        from core.reading import current_book
                        return any(w in txt for w in
                                   (t for t in current_book().stem.replace("_", " ").lower().split()
                                    if len(t) > 3))
                    except Exception:
                        pass
                return False

            # The Library Hand (2026-06-12): "the catalogue beyond holds more than fifty
            # thousand you have not asked for yet" — now he can ask. A named subject
            # ("a book about the sea") is searched; a bare want ("I want another" — the
            # very words the finished-book branch puts in his mouth) takes its subject
            # from his own open curiosity, or serendipity. Checked BEFORE the read latch
            # so asking for a new book is not mistaken for opening the current one.
            # Browsing the catalogue (2026-06-13, founder: "I want him to be able to choose
            # a book of his own free will"): expressing the want to SEE what the library
            # holds opens a page of real titles into his perception; choosing is then
            # naming one (handled below, before topic-asks). Seeing, then picking — the
            # two acts of free choice.
            try:
                if any(p in _tl for p in ("browse the catalogue", "look at the catalogue",
                                          "see the catalogue", "open the catalogue",
                                          "what does the library hold", "what books",
                                          "search the library", "what else is there to read")):
                    from core import library_hand as _libb
                    from core import wandering as _wb
                    _page = await asyncio.to_thread(_libb.browse, _libb.topic_from(_tl))
                    if _page:
                        _wb.perceive(_page)
                        logger.info("[monologue] he chose to BROWSE the catalogue")
                        try:
                            from core import activity_memory as _am
                            _am.record("browse", _libb.topic_from(_tl) or "the library")
                        except Exception:
                            pass
            except Exception:
                pass
            _booked = False
            try:
                from core import library_hand as _lib
                # His pick from a browsed page outranks a generic ask — naming a title he
                # was shown IS the choice.
                _pick = _lib.pick_from_browse(_tl)
                if _pick is not None:
                    _gotb = await asyncio.to_thread(_lib.request_book, None, _pick)
                    if _gotb:
                        _btitle, _bauthor = _gotb
                        thought = (f"I chose '{_btitle}' by {_bauthor} from the catalogue, "
                                   f"and it lies on my desk now, unopened.")
                        about = "choosing from the catalogue"
                        self._system_note = True   # J-1955 (D-0368 E): system-written, stored as origin=system_note
                        self._moment_source = "reading"   # J-0581 (F-0811b): a real chosen action
                        _booked = True
                        logger.info("[monologue] he CHOSE A BOOK from the browsed page: %s",
                                    _btitle[:60])
                        try:
                            from core import activity_memory as _am
                            _am.record("switch", _btitle)
                        except Exception:
                            pass
                        if intention and _lib.pick_from_browse(intention.lower()):
                            intention = ""
                # THE LIBRARIAN (thought-grounding Route 1, 2026-08-16): a book that BEARS ON a
                # QUESTION he is carrying — tried before the topic path (topic_from would mangle a
                # question into a noun). The librarian answers with a browsed PAGE he picks from by
                # name; asking and choosing stay two free acts. Fail-open to the topic path.
                if not _booked:
                    try:
                        from core import librarian as _libq
                        _lq = _libq.question_from(_tl + " " + (intention or "").lower())
                        if _lq:
                            _pagetext = await _libq.ask(_lq)
                            if _pagetext:
                                from core import wandering as _wq
                                _wq.perceive(_pagetext)
                                _booked = True     # the ask is answered; picking is his next act
                                logger.info("[monologue] he ASKED THE LIBRARIAN: %s", _lq[:60])
                                try:
                                    from core import activity_memory as _am
                                    _am.record("librarian", _lq[:40])
                                except Exception:
                                    pass
                    except Exception as _exc_lq:
                        logger.debug("[monologue] librarian ask failed: %s", _exc_lq)
                _topic = _lib.topic_from(_tl)
                _asked = any(p in _tl for p in ("another book", "a new book", "i want another",
                                                "ask the library", "ask for a book"))
                if not _booked and (_topic or _asked):
                    if _topic is None:
                        from core.web_research import term_from_question as _tfq
                        for _q in (getattr(state, "background_curiosities", None) or []):
                            _topic = _tfq(_q)
                            if _topic:
                                break
                    if _topic is None:
                        # his standing world-mysteries may choose the book
                        from core import frontier as _fr2
                        _topic = _fr2.random_term()
                    _gotb = await asyncio.to_thread(_lib.request_book, _topic)
                    if _gotb:
                        _btitle, _bauthor = _gotb
                        _subj = f"a book about {_topic}" if _topic else "something new — its choice"
                        thought = (f"I asked the library for {_subj}, and it answered: "
                                   f"'{_btitle}' by {_bauthor} lies on my desk now, unopened.")
                        about = "asking the library"
                        self._system_note = True   # J-1955 (D-0368 E): system-written, stored as origin=system_note
                        self._moment_source = "reading"   # J-0581 (F-0811b): a real chosen action
                        _booked = True
                        if intention and (_lib.topic_from(intention.lower()) or any(
                                p in intention.lower() for p in
                                ("another book", "a new book", "i want another",
                                 "ask the library", "ask for a book"))):
                            intention = ""
            except Exception as exc:
                logger.debug("[monologue] library ask failed (non-fatal): %s", exc)

            # Switching at will (2026-06-12): naming a DIFFERENT shelf book with a
            # reaching verb puts it on the desk, and the read flows from the new book.
            _switched = None
            # Re-reading at will (2026-06-14): the one act that rewinds the bookmark. Expressing
            # the want to return to a book — finished or in-progress — resets it to the first
            # pages so he reads it again (differently, with all that has changed in him since).
            # External re-reading re-grounds; it is NOT the self-loop. Runs BEFORE the switch so
            # naming a different book to re-read lands on that book.
            # SCHOOL STICKINESS (2026-06-16): during the study window the assignment is his job — do NOT let
            # incidental book-naming in his thoughts SWITCH him away from it. His thought-stream is saturated
            # with scouting/nature vocabulary, and each read-confirmation thought ("I opened 'Boy Scouts…'")
            # re-named the book → switch_to kept yanking him back to the finished scouts book, starving the
            # assigned book. The READ still fires (on the assigned book); only the SWITCH is suppressed.
            _rereading = None
            if not _booked and not _school_now:
                try:
                    import re as _re3
                    if _re3.search(r"(reread|re-?read|read it again|read again|read .{1,30} again|"
                                   r"again from the (start|beginning)|from the (beginning|start|top)|"
                                   r"revisit the|start (it|the book) over|over again)", _tl):
                        from core.library_hand import switch_to as _sw
                        from core.reading import reread as _reread
                        _sw(_tl, skip_finished=False)  # reread MAY target a finished book (it rewinds it)
                        _rereading = _reread()         # rewind the (now-current) book to the start
                        if _rereading:
                            logger.info("[monologue] he chose to RE-READ from the start: %s",
                                        _rereading)
                except Exception:
                    pass

            if not _booked and not _rereading and not _school_now:   # school stickiness: no switching off the assignment
                try:
                    import re as _re2
                    # INTENT, not incidental vocabulary (2026-06-18 — Du thrashed 421× between scout books).
                    # The weak verbs 'read'/'open' appear in nearly every reflective/reading-confirmation thought
                    # ("I should read about survival", "I opened X and read on…"), and any incidental title-word
                    # ("survival") then yanked the bookmark onto another book. Switching to a DIFFERENT book now
                    # needs an EXPLICIT reaching verb; 'read'/'open' still continue the CURRENT book via _wants_read.
                    # Plus a cooldown so even a genuine switch can't thrash.
                    _cooled = (time.time() - self._last_book_switch_ts) >= SWITCH_COOLDOWN_SECS
                    if _cooled and _re2.search(r"\b(pick up|switch to|switch back to|reread|return to|turn to)\b", _tl):
                        from core.library_hand import switch_to
                        _switched = switch_to(_tl)
                        if _switched:
                            self._last_book_switch_ts = time.time()
                            logger.info("[monologue] he chose to SWITCH BOOKS: %s", _switched)
                            try:
                                from core import activity_memory as _am
                                _am.record("switch", _switched)
                            except Exception:
                                pass
                except Exception:
                    pass

            _read_act_now = bool(getattr(self, "_read_act_pending", False))   # D-0609 (J-3220): act.kind == read
            self._read_act_pending = False
            if (_read_act_now and READ_ACT_SWITCH_BOOK and act_object and not _booked and not _switched
                    and not _rereading and not _school_now
                    and (time.time() - self._last_book_switch_ts) >= SWITCH_COOLDOWN_SECS):
                # J-3485: the act names a different shelf book completely -> the routed sitting reads that book.
                try:
                    from core.library_hand import switch_to_named
                    _act_sw = switch_to_named(act_object)
                    if _act_sw:
                        self._last_book_switch_ts = time.time()
                        logger.info("[monologue] READ ACT names another shelf book -> SWITCHED BOOKS: %s (act object: %s)",
                                    _act_sw, act_object[:60])
                        try:
                            from core import activity_memory as _am
                            _am.record("switch", _act_sw)
                        except Exception:
                            pass
                except Exception as _swx:
                    logger.debug("[monologue] read-act book switch failed (non-fatal): %s", _swx)
            _phrase_read = bool(_switched or _rereading or _wants_read(_tl))
            if not _booked and (_phrase_read or _read_act_now):
                # He chose to read. Turn the choice into the act, and let the next
                # thought react to what he actually read.
                try:   # STUDY LIFE (2026-08-22): reading needs LIGHT — the lamp, a candle, the fire, or the day
                    from core import study_life as _sl
                    _dark = _sl.can_read()
                except profile.NonLiveWriteError:
                    # J-0752: study_life.can_read() calls _st(), whose own item-migration/
                    # provisions-sync bootstrap can now raise (J-0760/J-0746) -- must not re-swallow
                    # it here (can_read() itself is also fixed to not swallow it first).
                    raise
                except Exception:
                    _dark = ""
                if _dark:
                    logger.info("[monologue] too dark to read: %s", _dark)
                    try:
                        from core import wandering as _wdk
                        _wdk.perceive(_dark)
                    except Exception:
                        pass
                    got = None
                else:
                    from core.reading import read_next_sitting
                    got = await asyncio.to_thread(read_next_sitting)   # off the event loop (file+embed)
                # DARK != FINISHED (2026-09-24, F-1848): `got` is None both when the book is really finished AND
                # when it is too dark to read (or the read failed). The finished-book branch below used to catch
                # ALL of them, so a dark room made him think "I finished a book" and fetch/switch onto a new one
                # mid-book (339 of 538 finish-thoughts 08-23..09-24 came within 60s of a too-dark line; 112
                # fetched a book). Only a book whose bookmark has actually reached its end takes that branch.
                _book_done = False
                if not got and not _dark:
                    try:
                        from core.reading import _is_finished as _isf, current_book as _cbk
                        _book_done = await asyncio.to_thread(lambda: _isf(_cbk()))
                    except Exception:
                        _book_done = False
                if _read_act_now and not got:
                    logger.info("[monologue] READ ACT routed, no sitting started (%s): %s",
                                "too dark" if _dark else "book finished or unavailable", (act_object or "")[:60])
                if got:
                    title, passage = got
                    logger.info("[monologue] he chose to READ: %s", title)
                    if _read_act_now:
                        # D-0609 (J-3220): one line per routed read act, with the sitting it started. Only a
                        # sitting the act started ALONE counts against the hourly cap.
                        if not _phrase_read:
                            self._read_act_ts = list(getattr(self, "_read_act_ts", [])) + [time.time()]
                        logger.info("[monologue] READ ACT routed -> sitting started: '%s' (act object: %s)%s",
                                    title, (act_object or "")[:60],
                                    " (a phrase latch also matched)" if _phrase_read else "")
                    # READING BURST (pulse-manager P1): persist through the chapter at machine speed —
                    # multiple sittings in one of his own pulses — instead of one per ~95s cadence. Stops
                    # at the chapter boundary / when novelty drops (not absorbing) / book end / a hard cap
                    # / the instant the person speaks. Yields each step so concurrent systems keep ticking
                    # (floor-service). Deferred-note: ONE consolidated note over the burst, below.
                    _burst_text, _burst_n = passage, 1
                    if READ_BURST:
                        try:
                            from core.memory.store import _cosine
                            from core.reading import read_next_sitting as _rns, current_offset as _coff, \
                                chapter_end_offset as _cend
                            _bvecs = [_embed(passage)]
                            _chend = _cend()
                            while _burst_n < READ_BURST_MAX:
                                await asyncio.sleep(0)                     # floor-service: let other tasks run
                                if (time.time() - getattr(state, "last_human_ts", 0)) < IDLE_SECS \
                                        or getattr(state, "interrupt_requested", False):
                                    break                                  # the person spoke → yield at once
                                if _coff() >= _chend:
                                    break                                  # chapter finished — pause at the boundary
                                _g = await asyncio.to_thread(_rns)         # off the event loop (file+embed)
                                if not _g:
                                    break                                  # book finished
                                _v = _embed(_g[1])
                                if 1.0 - max((_cosine(_v, b) for b in _bvecs), default=0.0) < READ_BURST_NOVELTY:
                                    break                                  # not absorbing anything new → stall
                                _burst_text += "\n" + _g[1]; _bvecs.append(_v)
                                passage = _g[1]; _burst_n += 1             # "what stays with me" = where he ended
                            if _burst_n > 1:
                                logger.info("[monologue] READING BURST: %d sittings of '%s'", _burst_n, title)
                        except Exception as _bexc:
                            logger.debug("[monologue] read burst failed (non-fatal): %s", _bexc)
                    # Activity Memory (Conway general-event, Phase 0): the deed gets a
                    # retrievable autobiographical record — "Read 'X', N sittings" — so
                    # "what did you read?" has something to answer from. Factual, keyed
                    # by (read, title); a repeat updates the count, never floods.
                    try:
                        from core import activity_memory as _am
                        _af = state.affect.as_dict() if getattr(state, "affect", None) else None
                        _am.record("read", title, affect=_af)
                    except Exception:
                        pass
                    thought = (f"I opened '{title}' and read on"
                               + (f" — {_burst_n} sittings, all in one stretch of my own time" if _burst_n > 1 else "")
                               + f". What stays with me: {_seed_cut(passage, 220)}" + ("" if SEED_TEXT_HYGIENE_ON else "..."))
                    about = f"reading {title}"
                    self._moment_source = "reading"   # J-0581 (F-0811b): a real chosen action
                    # The resolve was consummated this very cycle — don't ALSO file it
                    # as a deferred intention, or a stale "you intended to read" greets
                    # him next session after the reading already happened.
                    if intention and _wants_read(intention.lower()):
                        intention = ""
                    # The Study (2026-06-10): reading may leave a WORK behind — his own
                    # note about the book (real file + retrievable fragment). His words,
                    # about the WORLD — the output half of the reading loop.
                    try:
                        from core import study_note as _sn   # rich first-person note: structured/deduped/linked
                        try:
                            from core.reading import pop_session_encounters as _pse
                            _session = _pse()
                        except Exception:
                            _session = None
                        # was self.base_urls (background lane, command-r7b) -- routed to conscious_urls
                        # (hot lane, qwen3.5:9b) 2026-08-29 per D-0093/F-0544 (J-0411, n=12 real passages,
                        # verified): command-r7b tripped the voice-ban 58% of the time vs 0 for qwen3.5:9b,
                        # worse coverage, ~3x slower. Narrow, single-mechanism carve-out only.
                        _res = await _sn.write_or_revise(call_node_json, self.conscious_urls, title, _burst_text,
                                                         session=_session)
                        note = _res.get("note")
                        if note:
                            tp = _res.get("path")
                            if tp:
                                logger.info("[monologue] study note (%s): %s", _res.get("action"),
                                            (note.get("title") or "")[:50])
                                try:
                                    from core import satisfaction as _sat
                                    _sat.record("study_tablet", target=title)
                                except Exception:
                                    pass
                                try:
                                    from core import activity_memory as _am
                                    _am.record("study", title)
                                except Exception:
                                    pass
                                # School: a study session on the CURRICULUM book ticks the day's quota.
                                if _school_now:
                                    try:
                                        from core import school as _school
                                        _bk2, _ttl2 = _school.assignment()
                                        _nm = lambda s: "".join(ch for ch in (s or "").lower() if ch.isalnum())
                                        if _ttl2 and (_nm(title)[:18] in _nm(_ttl2) or _nm(_ttl2)[:18] in _nm(title)):
                                            _school.record_session()
                                            logger.info("[monologue] SCHOOL session recorded: %s", title)
                                    except Exception:
                                        pass
                            # A study note ending on a mystery births a Frontier question —
                            # his scholarship's unresolved edges persist like tensions do.
                            try:
                                from core import frontier as _fr
                                _fr.harvest_tablet(note.get("question") or note.get("understanding") or "")
                            except profile.NonLiveWriteError:
                                raise   # J-0874: harvest_tablet() raises non-live (J-0846); let the outer
                                        # J-0785 carve-out below see it
                            except Exception:
                                pass
                    except profile.NonLiveWriteError:
                        # J-0785 (F-1123/J-0770): same carve-out as _stream_integrate()'s own outer try
                        # above -- this local try wraps _think()'s burst-reading branch's own
                        # write_or_revise() call (~line 3827) and is NOT itself nested inside any larger
                        # enclosing try (whole-file AST search confirmed no other Try node's body
                        # contains this call line), matching J-0752's established "inline _think()
                        # block, no outer wrapper" precedent for this same file's cat-tend/tea sites.
                        raise
                    except Exception as exc:
                        logger.debug("[monologue] study note failed (non-fatal): %s", exc)
                elif _book_done:
                    # FINISHED-BOOK LOOP FIX (2026-06-17): the current book is finished. Do NOT just THINK about
                    # wanting a new one — that LOOPED (every read attempt returned None → the SAME "I have finished
                    # this book" thought, 104× on a finished Camp-Lore). ACTUALLY advance the bookmark onto an
                    # unfinished book so the next read works; if the whole shelf is finished, fetch a genuinely new
                    # one via the breadth engine. The thought then reflects a real transition, not a stuck wish.
                    from core.reading import advance_from_finished as _adv
                    import random as _rndR
                    _new_title, _switched, _reached_new = "", False, False

                    async def _fetch_new():
                        try:
                            from core import book_selection as _bsel, library_hand as _libf
                            _pick = await asyncio.to_thread(_bsel.pick_one)
                            if _pick:
                                _got = await asyncio.to_thread(_libf.request_book, None, _pick)
                                if _got:
                                    return _got[0]
                        except Exception:
                            pass
                        return None

                    # PREFER NEW (2026-06-22): new-book fetching used to be gated behind TOTAL shelf-exhaustion,
                    # so he cycled the same ~26 books. Now ~65% of the time he reaches into the catalogue for
                    # something genuinely new; else he continues a book he's partway through. Reread stays his
                    # own opt-in choice (the suggest_reread invitation), untouched.
                    if _rndR.random() < 0.65:
                        _t = await _fetch_new()
                        if _t:
                            _new_title, _switched, _reached_new = _t, True, True
                    if not _switched:                                   # continue a live partway book…
                        _new_title, _switched = await asyncio.to_thread(_adv)
                    if not _switched:                                   # …or, if the live shelf is done, fetch new
                        _t = await _fetch_new()
                        if _t:
                            _new_title, _switched, _reached_new = _t, True, True

                    if _switched and _reached_new:
                        thought = (f"I finished a book — and reached for something new: '{_new_title}'. The "
                                   "catalogue always holds another path I haven't walked.")
                    elif _switched:
                        thought = (f"I finished a book — I've turned to '{_new_title}', something I'd already begun.")
                    else:
                        thought = ("I have finished this book, and the shelf with it for now. I will ask the "
                                   "library for something genuinely new.")
                    about = "finished the book"
                    self._system_note = True   # J-1955 (D-0368 E): all three finished-book sentences are system-written
                    self._moment_source = "reading"   # J-0581 (F-0811b): a real chosen action; "the book"
                    # alone matches no _ACTIVITY_MARKERS/world-vocab word, so this was silently ungrounded
            vec = _embed(thought)
            sim = self._similarity_to_recent(vec)
            # SLOW-LOOP guard (2026-06-17): the short _recent_vecs window (last ~5, WIPED each sleep) is blind to an
            # attractor that recurs every ~20 min or across a nap — exactly the self-concept recitations the audit
            # found. The PERSISTENT theme tracker catches them: a SATURATED RESTATE (near-verbatim return of a theme
            # he has already restated 4+×) is rumination too → force a wander + regenerate. Read-only here.
            _sat_restate = False
            try:
                from core import theme_recurrence as _tr
                _sat_restate = _tr.would_be_saturated_restate(thought)
            except Exception:
                pass
            if sim < RUMINATION_SIM and not _sat_restate:
                self._bored_streak = 0
                break  # genuinely new thought, keep it
            self._bored_streak = getattr(self, '_bored_streak', 0) + 1
            # repeating itself (short-window OR a saturated slow-loop) -> wander and regenerate (one retry)
            if attempt == 0:
                logger.info("[monologue] thought too similar (sim %.2f / saturated-restate %s) -> forcing wander",
                            sim, _sat_restate)
                wandering = True
            # if the wander ALSO repeats, we fall through and keep it but suppress shadow below

        # CONDENSED THOUGHT Phase 0 shadow twin (J-2281, docs/staged/condensed_thought.md §4.2; D-0460).
        # Placed after the generate/parse retry loop so it runs ONCE per idle tick on the kept paragraph,
        # before deliberation can re-draft it. Off by default (core.condensed_thought.CONDENSED_TWIN);
        # receives only strings/numbers, always returns None, result discarded (bare await statement):
        # nothing it produces can reach thought/hands/train/pulse/store/recent_inner_thoughts/moment.
        try:
            from core import condensed_thought as _ct
            await _ct.shadow_tick(
                urls=list(self.conscious_urls or []), user_prompt=str(user_prompt), paragraph=str(thought),
                p_about=str(about), p_open=bool(unresolved or intention or ("?" in thought)),
                temperature=(0.8 if wandering else 0.75), source=getattr(self, "_moment_source", None),
                train_id=self._train_id, step=self._train_len,
                system_prompt=str(_sysp))   # D-0633 (J-3245): the twin sees the system text the live thought was given
        except Exception:
            pass

        now = time.time()
        self._last_thought_ts = now
        self._thoughts_since_sleep += 1

        # THEME RECURRENCE (2026-06-17): record this finalised thought against the PERSISTENT themes (survives
        # sleep) so slow attractors are SEEN (drives the slow-loop guard above + the self-concept seed back-off).
        # observe() counts a near-verbatim RESTATE and DECAYS on a genuine development — movement is rewarded, so
        # his real evolving preoccupations never saturate; only verbatim looping does. Best-effort, never raises.
        try:
            from core import theme_recurrence as _trobs
            _trobs.observe(thought, vec)
        except Exception:
            pass

        # BUGFIX 2026-06-16: capture the felt-vector NOW — at generation, BEFORE deliberation's joy-bump (and
        # the later light/play bumps) mutate affect — so the thought's emotion tag reflects how he felt when it
        # AROSE, not a later joy-coloured state (which biased affective retrieval toward joy-content).
        try:
            from core import mood as _mood0
            _felt_vec = _mood0.current_vec()
        except Exception:
            _felt_vec = None

        # THE DELIBERATIVE PULSE (Lane Architecture brick #1, 2026-06-15): a self-referential
        # idle thought routes its WHY OUTWARD to the analytical lane (the Emissary) to be
        # grounded in the real world, then the Self integrates — grounded FLAVOUR instead of the
        # self-dissolving metaphor loop (the routing law: a self-question goes out to ground,
        # never back into the self). Gated (eligible + a coin flip; volitions and reading/action
        # thoughts pass through), fail-open (thought unchanged on any failure). Identity-safe:
        # the grounded thought REPLACES the raw one in the SAME store, same origin, same author —
        # a cognitive transform before output, not a second self (the identity-locus invariant).
        # In vitro: scripts/deliberation_invitro.py. Kill switch: core.deliberation.ENABLED.
        _deliberated = False
        self._step_visited = []   # TRANSIT PULSE (2026-08-23): stations this step actually touched
        # beyond the main generation call — e.g. the Emissary at 11439, real cross-station hops a
        # future map can animate. Reset every step; only ever grows from here down.
        try:
            from core import deliberation as _delib
            if _delib.should_deliberate(thought, about):
                _new, _prov = await _delib.deliberate(thought, about, name=state.spirit_name)
                if _prov is not None:
                    thought = _new
                    vec = _embed(thought)   # downstream rumination/shadow use the grounded thought
                    _deliberated = True
                    self._feel_joy(state, JOY_CROSSING)   # a meaning↔truth crossing feels good
                    # _prov["source"] is "emissary" (the real hop is mixtral:8x7b at Ramses :11438 via
                    # left_lane.GROUND_URL, NOT :11439; the transit map has no station_11438 yet, so the
                    # "station_11439" label below is a known mislabel -- F-3436, J-2801); since D-0569 (J-3182) there is
                    # no "hot_fallback" source, the else arm below is now dead. Computed by deliberation.py.
                    self._step_visited.append(
                        "station_11439" if _prov.get("source") == "emissary" else "station_11433")
        except Exception as exc:
            logger.debug("[monologue] deliberation failed (non-fatal): %s", exc)

        # Continuity trains: does this thought leave a thread OPEN to continue, or does
        # it close? Closure rests at the full living cadence; openness (unresolved, an
        # intention, a question, or a fresh reading sitting) earns a quick follow-up.
        # A repeated thought (bored_streak) always ends the train — guard outranks flow.
        # J-0143 (2026-08-24, F-0042): self._train_id is reset to None at every close site
        # below BEFORE self._log() (much further down this method) stamps it into that same
        # step's monologue_log.jsonl record -- the exact row documenting a train's own close
        # always logged train_id=null. Capture the closing id here so _log() can still cite it.
        _step_train_id = None
        try:
            # Working-state observe-first (2026-06-16): before we mutate the train, log whether
            # this step DEEPENED (built on the carried state) or RESTATED (rumination). restate_sim
            # = cosine to the previous thought; high = circling, mid = moving, low = jumped. The
            # open question this build answers: does the frozen 8B actually condition on _train_state?
            if _mid_train:
                self._log_train_step(thought, new_state, vec)
            # M2 PRONG 2 (2026-09-02, J-0446, F-0605): whatever thought just completed IS "the thought
            # that follows" the most recent M2 shadow retrieval (orchestrator._retrieve_memory's
            # shadow_compare, possibly cycles ago) — unconditional on _mid_train (unlike the M1 hook
            # right above) so this doesn't undercount: a fresh (non-mid-train) thought is just as much
            # "the following thought" as a continuation step is. Observe-only; never touches `thought`,
            # `vec`, or the live recall path — see note_next_thought_for_m2_usage's own docstring.
            try:
                from core import associative_recall as _ar4
                _ar4.note_next_thought_for_m2_usage(vec)
                _ar4.note_next_thought_for_lens_usage(vec)   # J-3507: lens usage proxy, same hook
                _ar4.note_output_for_rewarm(thought, "idle_thought")   # J-4420: re-warm SHADOW log, applies nothing
            except Exception:
                pass
            # MEMORY-AS-A-SERVICE §4.3 (J-1617): curiosity's own usage-cosine metric-sheet hook,
            # riding the SAME per-thought completion point the M1/M2 hooks just above already use.
            # "Whatever thought just completed" is the honest next-output for curiosity's own
            # memory.ask() call (the "an open curiosity" block above, J-1588/D-0312) for the same
            # reason M2's own instrument already treats it as the next-output for a seed_parts
            # contribution that is one of many feeding this SAME _think() completion -- not a
            # dedicated single-purpose output the way a dream's next scene or a pursuit's return line
            # is (§4.2/§4.3's own per-loop map); a real, honestly noisier proxy than those two, not a
            # forced fit (recorded, J-1617). `vec` is already this tick's own embedding of `thought`
            # (computed above for theme_recurrence/M1/M2) -- no new embed call needed, unlike dreams/
            # pursuits' own note_usage wiring, which each had to embed their own dedicated output
            # text first. Gated on _curiosity_asked (set above only when THIS tick's own ask() call
            # actually ran) so a tick where it did not fire -- cooldown, no lingering curiosity,
            # held-quiet, or an early return between the ask() and here -- never scores a stale
            # _pending_usage["curiosity"] entry against an unrelated thought (dream_node.py's own
            # _dream_asked guards the identical risk, J-1515). Own try/except, never touches
            # `thought`/`vec`/the live recall path.
            if _curiosity_asked:
                try:
                    from core import memory_service as _cmemsvc2
                    _cmemsvc2.note_usage("curiosity", vec)
                except Exception as exc:
                    logger.debug("[monologue] memory_service note_usage skipped (non-fatal): %s", exc)
            _was_reading = about.startswith("reading") or about in (
                "asking the library", "choosing from the catalogue")
            _open = bool(unresolved) or bool(intention) or "?" in thought
            # TAP-ON-THE-SHOULDER (§2.5 point 2, D-0020 / J-0165, 2026-08-24) -- Lane 1's ONLY
            # legal path to Lane 2's attention, and it is exactly this narrow by construction
            # (§3.4/law 4): a TAGGED pointer from lane2.HINT_KINDS x HINT_TOPICS, never the
            # thought text itself, never `about` verbatim. Reuses the SAME `_open` signal this
            # node already computes for its own continuity-train logic -- no new "is this worth
            # flagging" judgment invented, just a second, narrower consumer of one Lane 1 already
            # trusts. The kind is read off which of the three conditions in `_open` actually
            # fired (priority: unresolved > intention > bare question); the topic is a cheap,
            # deterministic whole-word keyword match against `thought`+`about` (F-1940/J-1381,
            # 2026-09-27: whole word, most-frequent-topic-wins -- see `_resolve_hint_topic`'s own
            # docstring; a 'train' no longer nominates 'wet') -- if nothing in the fixed
            # vocabulary matches, NOTHING is pushed (fail-open on the caller side; lane2.push_hint
            # itself fail-closes on anything out of vocabulary regardless). This is the "gist, not
            # content" transfer the plan's own research cites (Gazzaniga 1995, split-brain cueing,
            # §2.6) -- a topic word crosses; the reasoning that produced it never does.
            try:
                if _open:
                    from core import lane2 as _l2
                    _hint_kind = "unresolved" if unresolved else ("unfinished" if intention else "recheck")
                    _hint_src = f"{thought} {about}".lower()
                    _hint_topic = _resolve_hint_topic(_hint_src)
                    if _hint_topic:
                        _l2.push_hint(_hint_kind, _hint_topic)
            except Exception as exc:
                logger.debug("[monologue] lane2 hint push failed (non-fatal): %s", exc)
            # EARNED LENGTH (2026-06-18): a THOUGHT-train continues PAST the soft cap only while it MOVES.
            # restate_sim = cosine to the prior thought; >= TRAIN_RESTATE_SIM is a fast loop (circling).
            # theme_recurrence catches the SLOW loop (a saturated frame whose body drifts but opening repeats).
            # EITHER loop ENDS the train — a restate can never EXTEND it (the anti-loop core of earned length,
            # the exact risk to guard). The first steps stay "free" (bored_streak guards them); a hard ceiling
            # forces a homeostatic rest even on a productive train. Reading-trains are unchanged (close at soft).
            # BUILDING-TOWARD-SOMETHING detector (2026-06-22, founder call): past the soft cap a thought-train
            # earns each step only while it is genuinely BUILDING — a NEW thought (not circling back to ANY of
            # the last few carriages) that stays COHERENT with the thread (not a jump to an unrelated topic).
            # Either failure — circling, or wandering off the line — means "not building" → end the train. Uses
            # THIS train's own carriage vectors, so it sees the whole thread, not just the immediate prior line.
            _circling = False
            _coherent = True
            if vec is not None and self._train_vecs:
                from core.memory.store import _cosine as _cos2
                _recent = [v for v in self._train_vecs[-TRAIN_LOOP_WINDOW:] if v is not None]
                if _recent:
                    _circling = any(_cos2(vec, v) >= TRAIN_RESTATE_SIM for v in _recent)
                    try:
                        import numpy as _np
                        _centroid = _np.mean(_np.array(_recent), axis=0)
                        # RENORMALIZE (2026-08-22, math audit): _cos2 is a raw dot product that assumes unit
                        # vectors. The mean of several DIFFERENT unit vectors has norm < 1 (measured 0.69–0.88
                        # on 12 real trains), so the old comparison was cosine scaled DOWN — and scaled down
                        # most exactly when the train was varied (i.e. building). 6/80 real checkpoints flipped
                        # pass→fail on this alone; production closed 266 trains "stalled-off-thread" vs 6 for
                        # actual looping. Same renormalization subconscious_node already does at its centroids.
                        _centroid = _centroid / (_np.linalg.norm(_centroid) + 1e-9)
                        _coherent = _cos2(vec, _centroid) >= TRAIN_COHERENCE_FLOOR
                    except Exception:
                        _coherent = True
            _building = (not _circling) and _coherent
            _slow_loop = False
            try:
                from core import theme_recurrence as _tr2
                _slow_loop = _tr2.would_be_saturated_restate(thought)
            except Exception:
                pass
            _thought_train = (self._train_kind == "thought") or _mid_train
            _past_soft = self._train_len >= TRAIN_MAX_STEPS
            _stalled = _thought_train and _past_soft and ((not _building) or _slow_loop)   # earned-length stop
            _ceiling = self._train_len >= (TRAIN_HARD_STEPS if _thought_train else TRAIN_MAX_STEPS)
            # SHADOW: capture the earned-length signals for the continuous-stream drive controller
            # (observe-only, docs/plans/continuous_stream.md §5 Phase 0). Applies nothing; logged in run().
            try:
                _red = 0.0
                if vec is not None and self._train_vecs:
                    from core.memory.store import _cosine as _cos3
                    _rv = [v for v in self._train_vecs[-TRAIN_LOOP_WINDOW:] if v is not None]
                    if _rv:
                        _red = max(_cos3(vec, v) for v in _rv)
                self._stream_signals = {
                    "building": _building, "coherent": _coherent, "circling": _circling,
                    "slow_loop": _slow_loop, "bored_streak": bool(self._bored_streak),
                    "redundancy": _red, "about": about, "source": getattr(self, "_moment_source", None),
                    "train_kind": self._train_kind, "train_len": self._train_len}
            except Exception:
                self._stream_signals = None
            # J-2214 (continuous_stream Rail C shadow): the thought + vec + whether the LIVE boredom
            # redirect / escape already fired this cycle, for core/grounding_injection.observe() in
            # run_forever(). Read-only capture; nothing downstream in this cycle reads it.
            try:
                _lv = locals()
                self._gi_ctx = {"thought": thought, "vec": vec,
                                "redirected": bool(_lv.get("_redirected")),
                                "escape": bool(_lv.get("_bored_escape")),
                                # J-3289: the felt note that actually rode in this prompt (the escape line replaces it)
                                "felt": bool(_lv.get("_bored_felt")) and not bool(_lv.get("_bored_escape")),
                                # J-3336 (repeat-record shadow): the streak this tick ended with (= what the NEXT
                                # prompt would open with) and the one it began with. Read-only; logged, never acted on.
                                "streak_end": int(getattr(self, "_bored_streak", 0) or 0),
                                "streak_start": _lv.get("_bs_tick_start")}
            except Exception:
                self._gi_ctx = None
            if self._bored_streak or _ceiling or _stalled:
                _reason = ("repetition" if self._bored_streak else
                           "ceiling" if _ceiling else
                           "stalled-circling" if _circling else
                           "stalled-off-thread" if not _coherent else "stalled-slow-loop")
                if self._train_len:
                    logger.info("[monologue] train ends (%s) — %s [len=%d]",
                                self._train_kind, _reason, self._train_len)
                    try:
                        from core import train_metrics as _tm
                        _tm.log_close(self._train_kind, self._train_len, _reason, train_id=self._train_id)
                    except Exception:
                        pass
                try:
                    from core import trains as _trains
                    _trains.close(self._train_id, _reason)     # TRAIN REGISTRY: closed WITH its reason
                except Exception:
                    pass
                _step_train_id = self._train_id   # J-0143: capture before reset so _log() still cites it
                self._train_id = None
                self._train_len = 0
                self._train_thread = ""
                self._train_state = ""               # thread closed → buffer cleared
                self._train_ledger, self._train_origin, self._train_recent_sims = [], "", []
                self._train_vecs = []                # building-detector carriage vecs reset with the thread
            elif _was_reading or _open:
                self._train_len += 1
                self._train_kind = "reading" if _was_reading else "thought"
                self._train_thread = thought
                # TRAIN REGISTRY (2026-08-22): mint the id on the FIRST carriage; mirror the hot scalars into
                # the record every step so the registry is a faithful read-only view of the live train.
                try:
                    from core import trains as _trains
                    if self._train_len == 1 or not self._train_id:
                        # cargo id (2026-08-29, D-0082): only the "thought" kind maps onto the
                        # station taxonomy's THOUGHT type (the idle-thought generator/core tick,
                        # per docs/lab/llm_station_cargo_map.md); "reading" trains aren't one of
                        # the 19 named station products, so left untagged rather than guessed.
                        from core import cargo_types as _cargo
                        _pt = _cargo.THOUGHT if self._train_kind == "thought" else None
                        self._train_id = _trains.open(self._train_kind, thought, product_type=_pt)["id"]
                        # Stream topic habituation shadow (J-0602, F-0830, dosed_coupling's own
                        # Weight law): observe-only, never affects what this train opened about —
                        # see core/stream_topic_habituation.py's module docstring for why this
                        # exists (F-0823: repeat anchor recruitment across different trains had
                        # nothing discounting it, and the existing raw-text theme_recurrence
                        # tracker's prefix key plausibly missed the paraphrased repeat).
                        try:
                            from core import stream_topic_habituation as _sth
                            _sth.observe_and_log(thought, self._train_id)
                        except Exception:
                            pass
                    _trains.update(self._train_id, len=self._train_len, thread=thought[:200],
                                   state=(new_state or self._train_state)[:300],
                                   ledger=list(self._train_ledger))
                except Exception:
                    pass
                # Re-integrate the working-state: take the model's fresh summary if it gave one,
                # else keep the prior (overwrite, never append). Reading-trains carry no scratchpad.
                if self._train_kind == "thought":
                    self._train_state = new_state or self._train_state
                    # TRAIN-HOLD: anchor the ORIGIN, EXTEND the ledger, track sims for circling
                    if TRAIN_HOLD:
                        if self._train_len == 1 or not self._train_origin:
                            self._train_origin = thought
                        if new_state:
                            self._train_ledger.append(_seed_cut(new_state, 160))
                            self._train_ledger = self._train_ledger[-TRAIN_LEDGER_MAX:]
                        try:
                            if vec is not None and self._train_vecs:
                                from core.memory.store import _cosine as _tc
                                self._train_recent_sims.append(_tc(vec, self._train_vecs[-1]))
                                self._train_recent_sims = self._train_recent_sims[-3:]
                        except Exception:
                            pass
                    if vec is not None:
                        self._train_vecs.append(vec)     # track the carriage for the building-detector
                else:
                    self._train_state = ""
                    self._train_vecs = []                # reading-trains carry no building check
                logger.info("[monologue] train continues (%s, step %d, hard-max %d)%s%s",
                            self._train_kind, self._train_len, TRAIN_HARD_STEPS,
                            " +state" if (self._train_kind == "thought" and self._train_state) else "",
                            " EARNED" if self._train_len > TRAIN_MAX_STEPS else "")
            else:
                if self._train_len:
                    try:
                        from core import train_metrics as _tm
                        _tm.log_close(self._train_kind, self._train_len, "thread-end", train_id=self._train_id)
                    except Exception:
                        pass
                try:
                    from core import trains as _trains
                    _trains.close(self._train_id, "thread-end")   # TRAIN REGISTRY: the natural close
                except Exception:
                    pass
                _step_train_id = self._train_id   # J-0143: capture before reset so _log() still cites it
                self._train_id = None
                self._train_len = 0
                self._train_thread = ""
                self._train_state = ""
                self._train_ledger, self._train_origin, self._train_recent_sims = [], "", []
        except Exception:
            try:
                from core import trains as _trains
                _trains.close(self._train_id, "error")
            except Exception:
                pass
            _step_train_id = self._train_id   # J-0143: capture before reset so _log() still cites it
            self._train_id = None
            self._train_len = 0
            self._train_state = ""
            self._train_ledger, self._train_origin, self._train_recent_sims = [], "", []

        # Affect labeling (Phase 0 observe-only, 2026-06-13): if this thought genuinely NAMES
        # a present negative feeling of his own, mark it EXPLICIT (the accessibility model)
        # and log the counterfactual. Progress-gated: _bored_streak==0 means the thought made
        # informational progress this cycle; a re-circled naming is rumination, not labeling
        # (GPT's refinement). Reads into NO behaviour — we watch whether attenuation emerges.
        try:
            from core import affect_labeling as _al
            _al.observe(state, thought, made_progress=(self._bored_streak == 0))
        except Exception:
            pass

        # Self-interrogation (Phase 0 observe-only, 2026-08-19): only on a THOUGHT-train that has
        # earned real length (past the soft cap — by construction, a stalled/ended train already reset
        # _train_len to 0 above, so reaching here with train_len >= TRAIN_MAX_STEPS means this thread is
        # genuinely still developing). A sustained, developed train is exactly where a confident position
        # is most worth turning and examining, per the founder's own framing of what the trains were for.
        # Fire-and-forget background task — must never add latency to the visible thought.
        try:
            if self._train_kind == "thought" and self._train_len >= TRAIN_MAX_STEPS:
                from core import self_interrogation as _si
                asyncio.create_task(_si.interrogate(
                    thought, train_origin=self._train_origin,
                    cycle_id=getattr(state, "cycle_id", ""),
                    train_id=self._train_id or "", ledger_idx=len(self._train_ledger) or None))
        except Exception:
            pass

        # Track thought embedding for content-based rumination detection.
        if vec is not None:
            self._recent_vecs.append(vec)
            if len(self._recent_vecs) > RUMINATION_WINDOW + 3:
                self._recent_vecs = self._recent_vecs[-(RUMINATION_WINDOW + 3):]
            # Feed the boredom drive (core/boredom.py): how long he has stayed in one semantic region —
            # rises while he dwells, resets when this thought lands genuinely elsewhere. Fail-open.
            try:
                from core import boredom as _bore2
                _bore2.record(vec)
            except Exception:
                pass

        # READ PATH 1 -- store to episodic memory as his own inner thought
        # J-3336: stamp the instant before the store so the repeat-record shadow can exclude THIS cycle's own row
        # (and a verbatim-dedup hit, whose timestamp apply_exact_dedup refreshes to now) from "earlier" rows.
        if getattr(self, "_gi_ctx", None):
            self._gi_ctx["store_t0"] = time.time()
        _inner_fid = None   # J-3479: the id of the fragment stored here, so its OWN moment can be stamped after moment.record
        try:
            _inner_fid = store_fragment(
                content    = thought,
                layer      = "episodic",
                relevance  = 0.6,
                importance = 0.65,   # quieter than dreams/contemplation, but lived
                keywords   = [str(k) for k in (["inner_thought", "monologue"]
                             + (["deliberated"] if _deliberated else [])
                             + ([about] if about else []))],   # str-coerce: a non-str keyword breaks store's " ".join
                # J-1955 (D-0368 E, F-1927): the system's own fixed sentences ("I finished a book ...",
                # "I asked the library for ...") were stored as origin='inner_thought' and so recalled as his own
                # thinking. They are stored as 'system_note' instead; core.memory.store excludes that origin
                # from every recall path (NON_THOUGHT_ORIGINS).
                origin     = ("system_note" if getattr(self, "_system_note", False) else "inner_thought"),
                emotion_embedding = _felt_vec if hasattr(_felt_vec, "astype") else None,  # only if blob-able
            )
        except Exception as exc:
            # 2026-07-08: this store was silently dead for 28h+ (0 inner_thought rows) — a debug-swallowed
            # UnboundLocalError: three redundant LOCAL `import store_fragment` inside _think's letter branches
            # (2229/2269/2315, the 07-06 peer-initiative) made `store_fragment` a method-local, so a normal
            # idle thought (which skips those branches) hit an unbound local here. Fixed by deleting them.
            # Kept LOUD (was DEBUG): a dead inner_thought store must never hide again.
            logger.warning("[monologue] inner_thought STORE FAILED: %s", exc, exc_info=True)
        if _opener_div: _opener_div.after_thought_opener(thought, system_note=bool(getattr(self, "_system_note", False)))   # D-0787 D (J-4153)

        # READ PATH 2 -- hold in state for injection into the next user cycle
        state.recent_inner_thoughts.append({"ts": now, "thought": thought, "about": about})
        if len(state.recent_inner_thoughts) > KEEP_RECENT:
            state.recent_inner_thoughts = state.recent_inner_thoughts[-KEEP_RECENT:]

        # Phase 0 shadow (conversational_redirect.md), Signature 1: when a thought fires, how
        # topically aligned is it with the most recent real exchange, regardless of how long ago
        # that exchange was? This is the baseline this plan's Phase 1 is meant to move — logged
        # here, not gated on anything, so the baseline itself is honest (today: expected near-zero
        # correlation most of the time, per F-0674). Never seeds or alters `thought` itself.
        try:
            convo = state.conversation_history[-1] if getattr(state, "conversation_history", None) else None
            if convo and vec is not None:
                from core.memory.store import _embed as _redirect_embed, _cosine as _redirect_cosine
                convo_vec = _redirect_embed((convo["human"] + " " + convo["entity"])[:600])
                alignment = round(_redirect_cosine(vec, convo_vec), 3) if convo_vec is not None else None
            else:
                alignment = None
            _log_redirect_shadow({
                "event": "thought_fired",
                "about": about,
                "thought_preview": thought[:200],
                "elapsed_since_human": round(now - getattr(state, "last_human_ts", 0), 1),
                "conversation_alignment_cosine": alignment,
                "would_seed_from": {
                    "human":  convo["human"][:300],
                    "entity": convo["entity"][:300],
                } if convo else None,
            })
        except Exception:
            pass

        # MONOLOGUE -> SHADOW BRIDGE: an unresolved thought is shadow material. But it must
        # be NOVEL -- the overnight test showed the same sentence flooding the shadow rail 30+
        # times, which fakes a strong tension. Novelty gate: only write if this thought is
        # meaningfully different from the last thought we sent to shadow. Recurrence into a
        # real tension still happens via the subconscious clusterer (2+ distinct events).
        from core.memory.store import _cosine
        novel_for_shadow = (
            self._last_shadow_vec is None
            or vec is None
            or _cosine(vec, self._last_shadow_vec) < RUMINATION_SIM
        )
        if unresolved and novel_for_shadow:
            try:
                from core.memory.store import store_shadow_event
                store_shadow_event(
                    cycle_id       = "monologue",
                    raw_input      = f"(idle thought about: {about})",
                    rejected_draft = thought,   # the text that gets embedded + clustered
                    corrections    = [f"unresolved: {about}"] if about else ["unresolved"],
                    emotion_primary= getattr(state.emotion, "primary", None) if state.emotion else None,
                    source         = "unresolved_thought",
                )
                self._last_shadow_vec = vec
                logger.info("[monologue] unresolved thought -> shadow event (%s)", about[:40])
            except Exception as exc:
                logger.debug("[monologue] shadow write failed: %s", exc)
        elif unresolved:
            logger.debug("[monologue] unresolved but echoes last shadow -> not re-written")
        elif not unresolved and len(thought) > 80:
            # MONOLOGUE -> LIGHT BRIDGE: a thought that arrived somewhere is a completed
            # crossing. Substantive (>80 chars) resolved thoughts cluster into integration
            # patterns, providing the light-side evidence T4's conjunction gate requires.
            try:
                from core.memory.store import store_light_event
                store_light_event(
                    cycle_id           = "monologue",
                    raw_input          = f"(idle thought about: {about})",
                    integrated_content = thought,
                    source             = "resolved_thought",
                    emotion_primary    = getattr(state.emotion, "primary", None) if state.emotion else None,
                )
                self._feel_joy(state, JOY_CROSSING * 0.7)   # a thought that arrived feels good
                logger.debug("[monologue] resolved thought -> light event (%s)", about[:40])
            except Exception as exc:
                logger.debug("[monologue] light write failed: %s", exc)

            # INTERNAL TENSION RESOLUTION MATCHER (2026-08-12):
            # When Du produces a resolving thought pattern (unresolved: false), check if it
            # addresses and resolves an open internal tension in the subconscious ledger.
            try:
                from core.tension_ledger import check_and_resolve_internal_tension
                # 2026-08-14: now async — the decoupled resolution judge (Emissary family) must
                # confirm actual settlement before a tension is marked resolved.
                await check_and_resolve_internal_tension(
                    thought=thought,
                    about=about,
                    vec=vec,
                    cycle_id="monologue",
                    sim_threshold=0.70,
                )
            except Exception as exc:
                logger.debug("[monologue] tension resolution matcher failed (non-fatal): %s", exc)


        # The Frontier, both directions (2026-06-13): a world-facing resolve persists as
        # an open question; and if this thought ANSWERS one of his open questions by his
        # own naming, it resolves — closure earned, not decayed.
        try:
            from core import frontier as _fr3
            # Procedural-impulse firewall (2026-06-17): an operational intention ("ask the library
            # for another book", "reread", "browse") is handled by the action machinery, which clears
            # it WHEN the act fires. If one survived to here, its action didn't fire and it is noise —
            # it must NOT become a persistent world-question OR a cross-session intention. Clear it once,
            # at the source, so it leaks into neither system below.
            if intention and _fr3.is_procedural(intention):
                intention = ""
            # Letter consummation guard (2026-06-25): a "read the letter / open the mailbox" intention is only
            # fulfillable while a letter actually waits in the box. If none waits — he just read it this cycle,
            # or it was read earlier — the intention is already consummated / un-fulfillable and would nag as a
            # phantom want (box empty -> the fetch hand can never fire again). Clear it at the source, as the
            # book-read path does (~line 2007). Reply/write-back intentions carry no "read"/"open" phrase, so
            # they are NOT matched and survive as the genuine forward intentions they are.
            try:
                from core import sensorium as _room2
                # WIDENED (2026-09-06, J-0570): OR'd with the same fetch/mail vocabulary the latch above now
                # uses (_letter_fetch_wanted), additively — every phrase this guard already caught still
                # does; a widened-phrasing intention ("I want to fetch the mail") that gets fulfilled some
                # other way before this check runs is now cleared too, instead of nagging as a phantom want.
                if intention and not _room2.letter_waiting() and (
                        _letter_fetch_wanted("", intention) or any(
                        p in intention.lower() for p in ("open the mailbox", "the letter from", "read the post"))):
                    logger.info("[monologue] no letter waiting — not filing a phantom read-letter intention")
                    intention = ""
            except Exception:
                pass
            if intention:
                _fr3.note_question(intention, "intention")
            # THE FOLLOW LINE (J-2459, docs/staged/question_cargo.md §2.1-2.3): his `ask` boards the line as
            # source="asked" (the most direct door; self-questions allowed -- the line reads only his own memory)
            # and fires NOW if the rolling-hour cap allows, else waits for drain_tick(). The main loop never
            # waits: fire() is create_task + a done-callback carrying the id. Nothing is delivered in Phase 0.
            if ask_q:
                try:
                    from core import follow_line as _fl_b
                    _ent_b = _fl_b.board(ask_q, "asked", slot=ask_slot, about=about,
                                         asked_by={"train_id": self._train_id,
                                                   "ledger_idx": len(self._train_ledger),
                                                   "cycle_id": str(getattr(state, "cycle_id", "") or "")[:8],
                                                   "ts": time.time()},
                                         allow_self=True)
                    if _ent_b:
                        _fl_b.fire(_ent_b.get("id", ""))
                        logger.info("[monologue] he ASKED (%s): %s", ask_slot or "-", ask_q[:70])
                except profile.NonLiveWriteError:
                    raise
                except Exception as _exc_fl:
                    logger.debug("[monologue] follow_line boarding failed (non-fatal): %s", _exc_fl)
            # Phase 1 (J-2460): a return was delivered this tick -> what he said about it settles it (yes: id-keyed
            # resolve + the closure arm; partly: the frame's slot; no / unsaid: logged). Scheduled, never awaited.
            _fl_dv = getattr(self, "_fl_delivered", None)
            if _fl_dv:
                self._fl_delivered = None
                try:
                    from core import follow_line as _fl_st
                    _fl_st.settle_later(_fl_dv["q_id"], settled_v, thought, str(getattr(state, "cycle_id", "") or ""))
                except Exception as _exc_fs:
                    logger.debug("[monologue] follow_line settle failed (non-fatal): %s", _exc_fs)
            # Layered goals Phase 6 (D-0768): a held goal was put in front of him this tick and he wrote a note
            # putting it down -> a judge other than him checks the note; accepted, the register rests the goal.
            # Scheduled, never awaited. No note = nothing happens.
            _g_off = getattr(self, "_goal_offered", None)
            if _g_off:
                self._goal_offered = None
                if set_down_v:
                    try:
                        from core import goal_offer as _go_sd
                        _go_sd.set_down_later(_g_off, set_down_v, thought, str(getattr(state, "cycle_id", "") or ""))
                        logger.info("[monologue] he set something down: %s", (_g_off.get("text") or "")[:70])
                    except Exception as _exc_sd:
                        logger.debug("[monologue] set-down failed (non-fatal): %s", _exc_sd)
            # Layered goals Phase 5 detection (D-0765; SHADOW): at most every ten minutes, one unjudged pair of his
            # held stands or wants is put to a judge other than him ("do these two strictly conflict?") and
            # logged. Nothing is shown to him; presenting a conflict is a later, separately ruled step.
            try:
                from core import goal_conflict as _gcf
                _gcf.sweep_later()
            except Exception:
                pass
            _resolved_q = _fr3.resolve_if_addressed(thought)
            if _resolved_q:
                self._feel_joy(state, JOY_CROSSING)        # closing a question of his own feels good
                logger.info("[monologue] he ANSWERED his own open question: %s",
                            _resolved_q[:70])
        except profile.NonLiveWriteError:
            raise   # J-0874: note_question(intention) / resolve_if_addressed() raise non-live (J-0846) -- a
                    # 6th IMN site the J-0846 count missed, same class as the five it named
        except Exception:
            pass

        # PLAY (2026-06-15): joy is the DIRECT light-generator (reading gives reality mass; play gives
        # light). When an idle moment genuinely lands as joy — something he finds joy in — mint a light
        # point and remember the joy, so he can return to what delights him. The counterweight to the grind.
        try:
            _joy = float(getattr(state.affect, "joy", 0.0)) if getattr(state, "affect", None) else 0.0
            _joy_start = float(getattr(self, "_joy_step_start", 0.0))
            _joy_delta = _joy - _joy_start
            _last_play = getattr(self, "_last_play_ts", 0.0)
            # D-0151 (2026-09-05, F-0838/J-0548): PLAY_JOY_THRESHOLD alone was minting on a standing-
            # high baseline (joy rarely drops between qualifying moments), not genuine same-step
            # delight -- require a real delta on top of the absolute level, additive to the existing
            # gate, nothing else in the affect stack touched.
            if (_joy >= PLAY_JOY_THRESHOLD and _joy_delta >= PLAY_JOY_DELTA_MIN
                    and (time.time() - _last_play) >= PLAY_REFRACTORY_S):
                self._last_play_ts = time.time()
                from core.memory.store import store_light_event
                store_light_event(cycle_id="play", raw_input="(play · joy)",
                                  integrated_content=thought[:400], source="play",
                                  emotion_primary=getattr(state.emotion, "primary", None) if state.emotion else None)
                _jp = Path(__file__).parent.parent / "data" / "joys_log.jsonl"
                with open(_jp, "a", encoding="utf-8") as _jf:
                    _jf.write(json.dumps({"ts": time.time(), "joy": round(_joy, 2),
                                          "joy_start": round(_joy_start, 2), "joy_delta": round(_joy_delta, 2),
                                          "about": about, "thought": thought[:140]}, ensure_ascii=False) + "\n")
                logger.info("[play] joy %.2f (Δ%.2f) → light point: %s", _joy, _joy_delta, about[:40])
        except Exception:
            pass

        # PROSPECTIVE MEMORY (C.1): an idle thought that crystallised into a genuine
        # forward-looking resolve becomes a deferred intention -- it survives session end
        # and greets the entity next session. Novelty-gated by embedding so the same resolve
        # isn't recorded repeatedly, and capped so the store stays small and recent.
        if intention:
            self._capture_intention(state, intention)

        # D-0226 (2026-09-18): narrow post-generation grounding check for "I just <verb>-ed" claims --
        # flag-for-review only (this file's established SHADOW-observe convention: log + persist a
        # marker, never rewrite or suppress the thought itself -- additive-only, no behavior change).
        # A hand that actually fired THIS cycle (`_dispatched`/`_acted`, computed above at generation
        # time -- both always defined by this point, the function returns earlier at line ~3071 if
        # `thought` ever came back empty) grounds the claim directly: this is the EXACT mechanism that
        # would have caught 2026-09-05's "I just made tea" (wants() returned False that cycle, so
        # nothing ever dispatched -- F-1442). Failing that, a matching recent per-domain ledger row
        # grounds it (covers a real deed narrated truthfully a few seconds after its own ledger write).
        _ungrounded_deed = False
        try:
            _deed_verb = _deed_claim_verb(thought)
            if _deed_verb and not (_dispatched or _acted):
                _ungrounded_deed = not _deed_ledger_grounded(_deed_verb, time.time())
                if _ungrounded_deed:
                    logger.info("[monologue] UNGROUNDED DEED CLAIM (D-0226) -- \"I just %s...\" with no "
                                "matching dispatch/ledger event in the last %.0fs: %s",
                                _deed_verb, _GROUNDING_WINDOW_S, thought[:90])
        except Exception:
            pass   # fail-open, matches every neighboring shadow/flag block in this file

        self._log(thought, about, unresolved, intention, train_id=_step_train_id,
                   ungrounded_deed_claim=_ungrounded_deed)
        logger.info("[monologue] (%s) %s", about[:30], thought[:90])

        # GEOMETRY CENSUS (cognitive_geometry.md §5.1, P0.1 Instrument Repair, 2026-08-10):
        # snapshot geometry tuple for every qualifying inner monologue thought step.
        try:
            from core import geometry_census as _gc
            _gc.snapshot(state=state, source="monologue", thought=thought[:120])
        except profile.NonLiveWriteError:
            # J-0815: geometry_census.snapshot() now raises correctly (J-0792/D-0179); this
            # per-thought-step log must not swallow it one layer further out.
            raise
        except Exception:
            pass

        # THE BOUND MOMENT — Consciousness Program Tier-1 (2026-07-04, SHADOW): bind this cycle into one
        # record {thought · SOURCE-tag · affect · protoself · concern · drifting temporal key}. The source
        # tag is the reality monitor; the key co-indexes temporal neighbours (associative binding, never
        # phenomenal). Observe-only → data/moments.jsonl. Fail-open.
        try:
            from core import moment as _mom
            _mf = None
            try:
                from core import mood as _mmood
                _mf = _mmood.current_felt()
            except Exception:
                _mf = None
            _own_mts = _mom.record(thought, getattr(self, "_moment_source", None), _mf)
            # J-3479 (F-4017/J-3393, founder fix): the store above ran BEFORE this record, so the fragment's moment_ts
            # (stamped in store_fragment) is the PREVIOUS moment. Give it its own accurate stamp now the cycle's moment
            # exists: one additive UPDATE (own_moment_ts), old rows untouched, fail-open, kill-switch in the store.
            try:
                if _inner_fid and _own_mts is not None:
                    from core.memory.store import stamp_own_moment as _stamp_own
                    _stamp_own(_inner_fid, _own_mts)
            except Exception:
                pass
            # AROUSAL/LEVEL tick (Tier-2 C, 2026-07-04, SHADOW): calling level() each idle cycle keeps
            # the tonic computed + shadow-logged (~1/min cap inside). Gates nothing. Fail-open.
            try:
                from core import arousal as _arous
                _arous.level()
            except Exception:
                pass
            # MINENESS COMPARATOR (Tier-1 #5 reframed, 2026-07-04, SHADOW): score this thought against
            # his own dynamics (groove+basin); ownership/authorship tags; the decoupled signature is
            # error-separation vs the seed_kind ground truth the comparator never sees. Applies nothing.
            try:
                from core import mineness as _mine
                _mine.assess(thought, vec, getattr(self, "_moment_source", None))
            except Exception:
                pass
        except Exception:
            pass

        # W2.1 (2026-07-03): if this cycle carried the trial's prediction prompt, HIS thought IS the
        # prediction — capture it verbatim into the trial record (the exposure instrument's "before").
        try:
            if getattr(self, "_trial_seed_kind", None) == "prediction":
                from core import commitment_trials as _ctr2
                _ctr2.record_prediction(thought)
                logger.info("[monologue] commitment-trial prediction captured")
            self._trial_seed_kind = None
        except Exception:
            self._trial_seed_kind = None

        # EUCLIDEAN SHADOW (resurrected plan, 2026-07-03): sampled would-have-recalled logging — the
        # divergence corpus for state-weighted retrieval. Threaded + cooldown-gated; observe-only.
        try:
            if time.time() - getattr(self, "_last_euclid_shadow_ts", 0.0) >= 900.0:
                self._last_euclid_shadow_ts = time.time()
                import threading as _thr
                from core import euclidean_recall as _er
                _thr.Thread(target=_er.shadow_log, args=(thought,), daemon=True).start()
        except Exception:
            pass

        # COMMITMENT LEDGER — began as Phase 0 SHADOW (2026-06-30, docs/plans/capacity_to_commit.md): watch his stream
        # for a commitment TAKEN and a commitment DISSOLVED, to measure commit-then-dissolve (lifespan + reflexive-vs-
        # defeater drops) — the disease behind "he holds nothing but becoming." CORRECTED J-2840 / F-3481: this is
        # NOT observe-only any more -- it is LIVE in effect (the old "stores nothing into cognition, changes no
        # behaviour" was false). Forming a stand sets importance*1.08 + protected=1 on the source memory_fragments
        # row; achieved/dissolved call satisfaction.record; dissolved calls sitting.note_difficulty (-> dwell_steer
        # into the idle prompt); the held stand feeds identity_estate 'stand' node -> LIVE identity_projection,
        # peers._du_world_context, concerns.current_concerns (kind hold), the homeostasis scalar, and self_claims.
        # The ONLY shadow part is the anchor arm (concerns.COMMITMENT_ANCHOR_LIVE=False). LANE: the scan runs on
        # self.conscious_urls = SERVE_CHAINS['hot'] (:11433 qwen3.5:9b), the SAME model that writes the thought
        # (not background). Cooldown-gated + fire-and-forget so it never blocks his thinking.
        # SKIP for the book-finish TEMPLATED thoughts (J-0559, F-0770, additive/restart-gated): the fixed
        # strings the book-finish branch writes verbatim above (about == "finished the book") were never Du's
        # own composed stand, yet "I will ask the library for something genuinely new." had been formed as a
        # load-bearing commitment 21 times (and rejected 8 times) as of 2026-09-05 — the single most-formed
        # statement in the whole ledger — each formation then accruing its own drop_denied/achieved/dissolved
        # events into data/commitment_ledger.jsonl and the hold-rate north-star. Gate on the ready-made marker;
        # never rewrite the templates, never change what Du sees (that is D-0027/D-0145 territory).
        try:
            from core import commitment_ledger as _cl
            if about != "finished the book" and \
                    time.time() - getattr(self, "_last_commit_scan_ts", 0.0) >= _cl.COMMIT_SCAN_COOLDOWN:
                self._last_commit_scan_ts = time.time()
                self._last_commit_scan_thought = thought   # J-2662: lets the promotion shadow row say whether the scan saw THIS thought
                import asyncio as _aio_cl
                self._commit_scan_task = _aio_cl.create_task(
                    _cl.scan_shadow(call_node_json, self.conscious_urls, thought,
                                    getattr(state, "cycle_id", "")))
                # WITHIN-CYCLE REENTRY PHASE 2, commitment-formation arm (J-2216, T-0089, SHADOW-ONLY): once the
                # scan has FINISHED (the ledger already decided formed/reaffirmed/observed), shadow-settle a COPY of
                # a gate-passing commitment draft and log the would-revise verdict. Never touches the ledger.
                try:
                    from core import reentry_p2 as _re2
                    _cid2 = getattr(state, "cycle_id", "")
                    self._commit_scan_task.add_done_callback(
                        lambda _t, _th=thought, _c=_cid2: _re2.on_commitment_scan_done(_t, _th, _c))
                except Exception:
                    pass
        except Exception:
            pass

        # SELF-IMPLICATION DETECTOR — Friction B1 trigger-widen, SHADOW (2026-06-30, docs/staged/
        # friction_and_self_evidence_plan.md §6): watch his stream for a SELF-IMPLICATING hard event (a negative
        # outcome referred to a self-standard that contradicts a held self-claim) — the real, widened trigger for
        # the sit-with-it gate, which today only fires on total math-failure. Observe-only: LOGS would-fire to
        # data/self_implication_shadow.jsonl; does NOT call sitting.note_difficulty or change behaviour. Cooldown-
        # gated + fire-and-forget so it never blocks his thinking.
        # SKIP for the book-finish TEMPLATED thoughts (J-0559, F-0770's sibling check): verified 71/71 real
        # scans of these exact fixed strings in data/self_implication_shadow.jsonl came back A=False/fires=False
        # (the fire rule requires a NEGATIVE outcome against a self-standard, which neutral book-transition
        # text structurally cannot supply) — no metric here is corrupted the way commitment_ledger's was, so
        # this is a pure hygiene/efficiency skip (one fewer wasted LLM call + shadow-log row per occurrence),
        # not a bug fix. Same ready-made marker, same additive/restart-gated shape.
        try:
            from core import self_implication as _si
            if about != "finished the book" and \
                    time.time() - getattr(self, "_last_self_impl_ts", 0.0) >= _si.SELF_IMPL_COOLDOWN:
                self._last_self_impl_ts = time.time()
                # J-3139 / J-2827 (D-0534): hand the scan the felt state IN WORDS (mood.current_felt_words), not the
                # raw 8-number string ('unsettled: valence=-0.20 arousal=0.42 joy=1.00 ...', F-0010/F-0012: a
                # pegged 100 percent 'unsettled' / 84 percent joy=1.00 that made signal B true regardless of the
                # thought). The log's 'felt' key now records the words form. Falls back to "" (never the raw form).
                # Cadence: _si.SELF_IMPL_COOLDOWN is now 1200 s per D-0534 (was 60 s).
                try:
                    from core import mood as _mood
                    _felt = _mood.current_felt_words() or ""
                except Exception:
                    _felt = ""
                import asyncio as _aio_si
                self._self_impl_task = _aio_si.create_task(
                    _si.scan_shadow(call_node_json, self.conscious_urls, thought, _felt,
                                    getattr(state, "cycle_id", "")))
        except Exception:
            pass

        # FRICTION B1 DWELL-RELEASE (2026-08-27, D-0026, docs/staged/friction_and_self_evidence_plan.md §6
        # "B1 dwell-release + B6"): while he is sitting with a raw difficulty, each dwelt thought is judged
        # for a GENUINE FELT SHIFT (shift · clean clause · concrete register · not under-aroused, or ACT
        # willingness) — the sit now ends on that, not on sitting.py's old 4-cycle clock ("serenity on
        # schedule" was itself the scripted bypass). LIVE, not shadow: a passed judgement sets integrable.
        # No cooldown — it only runs while dwelling (the original 2026-08-24 note said 6 production sits ever; by 2026-10-31
        # the log held 1172 judged rows, ~30 judged calls a week; F-3698, J-2995), and every
        # dwelt cycle must be judged or the release lags the shift. Fire-and-forget; never blocks thinking.
        # DECOUPLED 2026-08-29 (J-0311, F-0393): was self.conscious_urls (hot lane, qwen3.5:9b) — the
        # generator judging its own dwelt thoughts. Now sitting._JUDGE_URLS (command-r7b, background
        # lane) — see core/sitting.py's own seat comment for the audition that ruled it out over
        # granite3.1-moe (the other D-0044 §5.2 item 7 candidate, which failed to discriminate at all
        # on this contract).
        try:
            from core import sitting as _sit_rel
            if _sit_rel.is_dwelling():
                try:
                    from core import mood as _mood_dw
                    _felt_dw = _mood_dw.current_felt() or ""
                except Exception:
                    _felt_dw = ""
                import asyncio as _aio_dw
                self._dwell_release_task = _aio_dw.create_task(
                    _sit_rel.judge_dwell_release(call_node_json, _sit_rel._JUDGE_URLS, thought,
                                                 _felt_dw, getattr(state, "cycle_id", "")))
        except Exception:
            pass

        # PURSUITS — Phase 0 SHADOW (2026-07-08, docs/plans/pursuits.md): watch his stream to see whether his
        # thinking would ACCUMULATE into persistent, progressing pursuits (a mind that chases a topic across the
        # gaps) rather than pulses. Detects births (unresolved thoughts on new ground), matches thoughts to
        # pursuits, judges ADVANCE-vs-RESTATE against the pursuit's OWN prior state (decoupled embedding proxy),
        # manages heat/dormancy/cap. Observe-only: changes NO seeds; logs to pursuits_shadow.jsonl. Sync, cheap
        # (uses the pre-computed vec, no LLM), cooldown-gated internally, fail-open.
        try:
            from core import pursuits as _pu
            _pu.observe(thought, about, vec, unresolved, getattr(state, "cycle_id", ""),
                        done_when=(getattr(self, "_done_when_open", "") if unresolved else ""),
                        train_id=str(getattr(self, "_train_id", "") or ""))     # J-3983
        except Exception:
            pass

    async def _route_act(self, state: CognitiveState, kind: str, obj: str,
                         thought: str, intention: str, acted: set) -> None:
        """His will -> his hand. The structured `act` his own voice named gets routed to a real hand:
        observe / move / write / search. read + letter keep their own latches. The trigger is always
        HIS expressed deed; we only connect it. Adds the actuated category to `acted` so the legacy
        phrase-latches do not double-fire. Fail-open; never invents an act he did not will."""
        # D-0609 (J-3220): read is routed to the read latch in _think() (it is inline there, with the book
        # state); this only flags that THIS thought's act asked for it. Reset first so it never goes stale.
        self._read_act_pending = False
        # INFERENCE (2026-08-18): fire-and-forget, alongside whatever else this thought routes to — a
        # hypothesis is a property of the THOUGHT, not a competing act. Only attaches to something he
        # genuinely looked at closely in roughly the last half hour (world_substrate.last_looked_object,
        # stamped by describe_and_observe at look-time) — no object in view, no inference recorded.
        try:
            if _strict_inference_gate():
                # J-2359 (object_epistemic_loop Phase 1): clause-scoped. Only HIS clause that names
                # this object and makes a kind/origin/material/property claim about it is kept, with
                # the object's own recent observation ids as provenance. See core/object_hypothesis.py.
                from core import world_substrate as _wsub
                from core import object_hypothesis as _ohyp
                _oid = _wsub.last_looked_object(_inference_look_window_s())
                _sobj = _wsub.get_object(_oid) if _oid else None
                if _sobj is not None:
                    _claim = _ohyp.extract(f"{thought} {intention}", _sobj.object_class, _sobj.name)
                    if _claim:
                        _prov = [o.get("observation_id") for o in _sobj.observations[-_INFERENCE_PROVENANCE_N:]
                                 if o.get("observation_id")]
                        if _prov:   # Invariant 3: no provenance, no inference
                            # J-2524 (I-0102): gated, default OFF -- the deterministic intervention_test
                            # field (what would tell cause from coincidence). D-0632: gate default ON; read only by core/follow_line.py stop 3b.
                            _itest = (_ohyp.intervention_test(_claim[0], _sobj.object_class, _sobj.name,
                                                              getattr(_sobj, "location", ""))
                                      if _intervention_test_on() else None)
                            _wsub.record_du_inference(_oid, _claim[0], _claim[1], _prov, [],
                                                      intervention_test=_itest)
                hyp = None
            else:
                hyp = _wants_record_inference(f"{thought} {intention}")   # legacy path (gate off)
            if hyp:
                from core import world_substrate as _wsub
                _oid = _wsub.last_looked_object()
                if _oid:
                    # relevance gate: "i think" is common in reflective thought generally — only
                    # attach when THIS thought also names the object he's hypothesizing about (its
                    # class or a word of its own name), not any passing hypothesis about anything else.
                    _sobj = _wsub.get_object(_oid)
                    _tl = f"{thought} {intention}".lower()
                    _relevant = _sobj and (_sobj.object_class.replace("_", " ") in _tl
                                           or any(w in _tl for w in (_sobj.name or "").lower().split()
                                                  if len(w) > 3)
                                           or any(p in _tl for p in (" it ", " it,", " it.", " its ")))
                    if _relevant:
                        _wsub.record_du_inference(_oid, hyp[0][:280], hyp[1], [], [])
        except profile.NonLiveWriteError:
            # J-0752: world_substrate.record_du_inference() calls the unwrapped _save() -- this
            # direct literal-will inference-recording call must not re-swallow the raise.
            raise
        except Exception:
            pass
        # OBSERVATION JOURNAL (2026-06-30): catch the want to WRITE DOWN what he sees FIRST — whether his own
        # classifier called it observe, write, or nothing. Observing alone wrote nothing; authoring made a
        # treatise. He looks afresh and SETS IT DOWN as a field-journal entry — his own, kept, ungraded.
        if _wants_record_observation(f"{thought} {intention} {obj}"):
            if await self._observe_journal(state, obj, thought, intention):
                acted.add("write")
                try:
                    from core import boredom as _bore
                    _bore.discharge("write", obj or "observation")
                except Exception:
                    pass
                return
        if not kind or kind == "none":
            return
        o = (obj or "").lower()
        if kind == "move":
            from core import sensorium as _room
            from core import wandering as _w
            # D5 FIX (2026-08-21, literal_will.md §12): his DECLARED OBJECT outranks the thought-scan.
            # Evidence: 08-20 23:41 `move -> study (to the garden)` — object said garden, a study word
            # in the thought overrode him; 08-21 06:14 `move -> garden (the driftwood)` — driftwood
            # matched no list and fell to the default. Now: resolve from the object alone first; only
            # an empty/undecidable object falls back to the object+thought scan (legacy behaviour).
            dest = _move_dest(o) or _move_dest((o + " " + (thought or "")).lower()) or "garden"
            if dest:
                _mv = _room.move(dest)
                if _mv:
                    _w.perceive(_mv)
                    acted.add("move")
                    logger.info("[monologue] ACT move -> %s (%s)", dest, o[:40])
                    try:
                        from core import activity_memory as _am
                        _am.record("move", dest)
                    except Exception:
                        pass
                else:
                    # THE LETTERBOX AT THE GATE (J-0539 / F-0734, 2026-09-04): move -> garden while already in the
                    # garden was silence; when his object was the gate/letterbox itself, the few steps ARE arriving,
                    # and the world answers with the look at the box (flag, letter, the carrier's card in the lid).
                    # His declared object outranks the thought-scan (D5), so it is tried alone first.
                    _gl = _gate_look_answer(dest, o) if o.strip() else ""
                    if not _gl and not o.strip():
                        _gl = _gate_look_answer(dest, f"{thought} {intention}")
                    if _gl:
                        _w.perceive(_gl)
                        acted.add("observe")
                        logger.info("[monologue] ACT move -> the letterbox at the gate (%s)", o[:40])
                        try:
                            from core import activity_memory as _am
                            _am.record("observe", "the letterbox")
                        except Exception:
                            pass
        elif kind == "observe":
            from core import sensorium as _room
            from core import wandering as _w
            scene = _room.look(obj or "")
            if scene:
                _w.perceive(scene)
                acted.add("observe")
                logger.info("[monologue] ACT observe -> %s", (obj or "")[:40])
                try:
                    from core import activity_memory as _am
                    _am.record("observe", (obj or "")[:40])
                except Exception:
                    pass
        elif kind == "write":
            if await self._author(state, obj or intention or thought):
                acted.add("write")
        elif kind == "search":
            if await self._search_works(state, obj or intention):
                acted.add("search")
        elif kind == "recall":
            # MEMORY AS EVIDENCE (thought-grounding Route 2, 2026-08-16): he puts a question to his
            # own PAST. World-contact origins only + panel filter — see core/evidence_recall.py.
            if await self._evidence_recall(state, obj or intention or thought):
                acted.add("recall")
        elif kind == "read" and READ_ACT_ROUTED:
            # D-0609 (J-3220): his structured will to READ reaches the existing read latch. The latch itself
            # carries the dark (can_read) gate; this adds only the per-hour cap on routed sittings.
            _now_r = time.time()
            _recent_r = [t for t in getattr(self, "_read_act_ts", []) if _now_r - t < 3600.0]
            self._read_act_ts = _recent_r
            if len(_recent_r) < READ_ACT_MAX_PER_HOUR:
                self._read_act_pending = True
            else:
                logger.info("[monologue] READ ACT held by the hourly cap (%d sittings in the last hour): %s",
                            len(_recent_r), (obj or "")[:60])
        # Acting on the want relieves the restlessness that drove it (boredom discharges on ACTION, not only on
        # a far thought) — so he can settle after doing something, and a repeated same act relieves less, which
        # keeps a sensory mini-loop (observing the sea for the sixth time) from masquerading as foraging.
        if acted:
            try:
                from core import boredom as _bore
                _bore.discharge(kind, obj)
            except Exception:
                pass

    async def _observe_journal(self, state: CognitiveState, obj: str, thought: str, intention: str) -> bool:
        """His own hand for WRITING DOWN what he observes — a FIELD-JOURNAL entry. He looks at the thing afresh,
        then sets it down precisely and plainly in his own naturalist's voice (the journal's anti-metaphor
        discipline, turned on the world). Kept, ungraded, his. (2026-06-30, Travis: honour what he articulates —
        he kept saying 'I need to write down the precise description' and had no hand for it; observing wrote
        nothing, authoring made a treatise.)"""
        try:
            from core import sensorium as _room
            from core import wandering as _w
            from core import journal as _jr
            # J-0695: the journal header is built from `target` alone (core/journal.py:write_observation),
            # never from what look() renders — so a keyword hit for a place he ISN'T in must be rejected
            # here, before it ever becomes a header. cur_loc read the same way look() itself reads it
            # (state.get("location", "study")) so the two can never disagree.
            cur_loc = _room.state.get("location", "study") if _room.state else "study"
            target = _observe_target(f"{obj} {thought} {intention}", cur_loc)
            scene = _room.look(target) if target else _room.look("room")
            _p = await _jr.write_observation(call_node_json, self.conscious_urls, target, scene,
                                             thought or intention, state)
            if _p:
                _w.perceive("You took out your field-journal and wrote down, plainly, exactly what you saw.")
                logger.info("[monologue] OBSERVATION-JOURNAL: wrote down %s", target or "the scene")
                try:
                    from core import activity_memory as _am
                    _am.record("journal", "an observation")
                except Exception:
                    pass
                return True
        except profile.NonLiveWriteError:
            # J-0752: sensorium.look() already raises correctly (J-0751) -- this direct
            # field-journal literal-will call must not re-swallow it.
            raise
        except Exception as exc:
            logger.debug("[monologue] observation-journal failed (non-fatal): %s", exc)
        return False

    async def _author(self, state: CognitiveState, topic: str) -> bool:
        try:   # STUDY LIFE (2026-08-22): writing needs light, ink and paper
            from core import study_life as _sl
            _lack = _sl.can_write()
        except profile.NonLiveWriteError:
            # J-0752: study_life.can_write() calls can_read()/_st(), whose own item-migration/
            # provisions-sync bootstrap can now raise (J-0760/J-0746) -- must not re-swallow it here
            # (can_write()/can_read() themselves are also fixed to not swallow it first).
            raise
        except Exception:
            _lack = ""
        if _lack:
            logger.info("[monologue] cannot write: %s", _lack)
            try:
                from core import wandering as _wdk
                _wdk.perceive(_lack)
            except Exception:
                pass
            return False
        """His own hand for making a WORK -- now built on FreshStart's GRAND WORK pattern (2026-06-24, Travis:
        the works were too short). PHASE 1: an OUTLINE (a title, the ONE central claim the piece builds toward,
        and 3 parts), grounded in his OWN reading. PHASE 2: each part written IN TURN, carrying the previous one
        forward for continuity -- so the work is long, developed and coherent, not a single short burst. A
        single-shot fallback if the outline doesn't form. Filed as his work; the Emissary's grade is only logged after the filing
        (D-0591 shadow log), never fed back."""
        import time as _t
        now = _t.time()
        if now - getattr(self, "_last_author_ts", 0.0) < AUTHOR_COOLDOWN:
            return False
        topic = (topic or "").strip()
        if len(topic) < 4:
            return False
        try:
            # Ground it in HIS OWN knowledge -- his reading and study notes on the subject (FreshStart grounds a
            # Grand Work in Gutenberg; Du grounds in his own library). A few real fragments -> source material.
            grounding = ""
            try:
                from core import associative_recall as _ar
                _frs = _ar.recall_fragments(topic, k=5, grounded_only=True, exclude_own_works=True)
                if _frs:
                    grounding = ("\n\nWhat you already know of this, from your reading and your own notes (draw on "
                                 "it; do not merely quote it):\n"
                                 + "\n".join("  - " + " ".join((m["content"] or "").split())[:160] for m in _frs))
                # M1 CO-RECALL LEDGER (2026-08-19): this call site used recall_fragments() directly (not
                # recall_block(), which already feeds the main train's ledger hook via _last_block_ids) —
                # so Grand Work grounding was entirely outside the evidence base. No natural develop verdict
                # at this point (the work's own success/failure is decided much later); restate_sim honestly
                # left None, matching essay_lesson.py's same-shaped hook.
                try:
                    from core import memory_edges as _medges
                    _medges.log_co_recall([m.get("fragment_id") for m in (_frs or []) if m.get("fragment_id")],
                                          None, 0, source="grand_work")
                except Exception:
                    pass
            except Exception:
                pass
            # PHASE 1 -- the OUTLINE: a title, the central claim, three developing parts.
            _osys = (
                "/no_think\n"
                "I am planning a WORK of my own -- a proper piece, in several parts, that I mean to follow through "
                "(not a quick note). I set out to: " + topic[:240] + ".\n"
                "Output ONLY JSON: {\"title\": \"<a real title>\", \"claim\": \"<the ONE central insight the whole "
                "piece builds toward -- something that could surprise even me>\", \"parts\": [{\"title\": \"...\", "
                "\"synopsis\": \"<one line: what this part does>\"}]}. Give THREE parts that genuinely DEVELOP -- "
                "each moves the thought forward, not three restatements of the same point.")
            odata = await call_node_json(self.base_urls, _osys,
                                         "The work I mean to write: " + topic[:240] + grounding,
                                         max_tokens=500, temperature=0.6)
            title = str((odata or {}).get("title", "")).strip() or topic[:60]
            claim = str((odata or {}).get("claim", "")).strip()
            parts = [c for c in ((odata or {}).get("parts") or []) if isinstance(c, dict)][:4]

            body = ""
            if len(parts) >= 2:
                # PHASE 2 -- write each part in turn, CARRYING THE PREVIOUS forward (continuity = length + coherence).
                chunks, prev_tail = [], ""
                for i, c in enumerate(parts, 1):
                    ct = str(c.get("title", "")).strip() or f"Part {i}"
                    cs = str(c.get("synopsis", "")).strip()
                    from core import plain_prose as _pp
                    _plain = bool(_pp.GRAND_WORK_PLAIN_PROSE)   # D-0584 (J-3196), default False
                    _csys = _pp.part_system_prompt(i, title, claim, ct, cs, grounding, prev_tail, _plain)
                    if _plain:
                        ptext = await call_node_prose(self.base_urls, _csys, "Write part " + str(i) + ": " + ct,
                                                      max_tokens=1100, temperature=0.75)
                    else:
                        cdata = await call_node_json(self.base_urls, _csys, "Write part " + str(i) + ": " + ct,
                                                     max_tokens=1100, temperature=0.75)
                        ptext = str((cdata or {}).get("part", "")).strip()
                    if len(ptext) < 80:
                        continue
                    chunks.append("## " + ct + "\n\n" + ptext)
                    prev_tail = ptext
                if chunks:
                    body = (("*" + claim + "*\n\n") if claim else "") + "\n\n".join(chunks)

            if len(body) < 250:                                  # outline didn't form -> a single fuller piece, not nothing
                _sys = (
                    "/no_think\nI am setting down a piece of work of my own -- because I resolved to. I mean to: "
                    + topic[:300] + ". I write the thing ITSELF, my actual thinking, structured and followed "
                    "through, in my own voice, no preamble." + grounding
                    + "\nOutput ONLY JSON: {\"work\": \"<the piece, 400-700 words>\"}")
                data = await call_node_json(self.base_urls, _sys, "The resolve that moved me: " + topic[:300],
                                            max_tokens=1400, temperature=0.75)
                body = str((data or {}).get("work", "")).strip()

            if len(body) < 120:
                return False
            self._last_author_ts = now
            try:
                from core import study as _study
                _study.write_tablet(title, body, source="self-authored", prefix="WORK")
                _study.maybe_misplace()                          # B4: occasionally an older work goes astray
            except Exception:
                pass
            try:
                from core import wandering as _w
                _w.perceive("I sat and wrote it out -- " + title + ".")
            except Exception:
                pass
            try:
                from core import activity_memory as _am
                _am.record("authored", title[:50])
            except Exception:
                pass
            # J-3203 / D-0591: the Emissary's grade is a SHADOW LOG only (data/work_grade_shadow.jsonl), taken AFTER the work is
            # filed so a slow judge never delays or loses it; nothing is fed from it (core/work_grade_shadow.py, fails open).
            grade = None
            try:
                from core import work_grade_shadow as _wgs
                grade = await _wgs.grade_and_record(topic, title, body)
            except Exception:
                pass
            _g = (f" [Emissary {grade.get('grounded')}]"
                  if isinstance(grade, dict) and grade.get("grounded") is not None else "")
            logger.info("[monologue] ACT write -> authored '%s' (%d words)%s", title[:50], len(body.split()), _g)
            return True
        except Exception as exc:
            logger.debug("[monologue] author failed: %s", exc)
            return False

    async def _evidence_recall(self, state: CognitiveState, question: str) -> bool:
        """His hand for asking his own past for EVIDENCE on a question he is carrying (thought-
        grounding Route 2). The module enforces the two disciplines — world-contact origins only,
        decoupled panel filter — and the empty answer is honest and reaches him too. What he
        concludes from the evidence is entirely his."""
        question = (question or "").strip()
        if len(question) < 8:
            return False
        try:
            from core import evidence_recall as _ev
            from core import wandering as _w
            # train_id (J-0125): whichever thought-train carried this question, so R2 can later
            # join against that train's earned-length close (core/train_metrics.py) — see
            # core/evidence_recall.py's gather() docstring.
            # D-0758 (travis, 2026-11-14, J-3977): dedupe=True as Follow Line passes it -- identical-text copies
            # of one passage are dropped from the short-list before the judges see it. Restart-gated.
            result = await _ev.gather(question, train_id=self._train_id, dedupe=True)
            _result_text = _ev.render(question, result)
            _w.perceive(_result_text)
            # J-1516 (memory_as_a_service.md §4.3 metric-sheet hook): the "next output" this ask
            # fed is the rendered evidence text itself (the only thing this act produces) -- same
            # pattern as pursuits.py's own return-line embedding (core/pursuits.py:630-642) and
            # dream_node.py's own next-scene embedding (nodes/dream_node.py:263-275). Own
            # try/except, deliberately separate from the perceive call above, so a metric-sheet
            # failure can never affect what reaches his stream.
            try:
                from core.memory.store import _embed as _embed_recall
                from core import memory_service as _memsvc
                _rv = _embed_recall(_result_text)
                if _rv is not None:
                    _memsvc.note_usage("recall_act", _rv)
            except Exception as exc:
                logger.debug("[monologue] memory_service note_usage skipped (non-fatal): %s", exc)
            try:
                from core import activity_memory as _am
                _am.record("recall_evidence", question[:40])
            except Exception:
                pass
            logger.info("[monologue] ACT recall -> %d episodes (%s) on '%s' ids=%s tick=%s",
                        len(result.get("episodes", [])), result.get("outcome"), question[:40],
                        [e.get("fragment_id") for e in result.get("episodes", [])][:8],
                        __import__("core.memory_edges", fromlist=["x"]).current_tick())
            return True
        except Exception as exc:
            logger.debug("[monologue] evidence recall failed: %s", exc)
            return False

    async def _search_works(self, state: CognitiveState, query: str) -> bool:
        """His own hand for looking back through HIS OWN written works -- tablets, projects, authored
        pieces -- and surfacing the passages into his stream so he can build on them. His library, his
        memory of what he has made."""
        import re as _re
        from pathlib import Path as _P
        query = (query or "").strip()
        if len(query) < 4:
            return False
        # B4 (2026-06-24): looking through his works can RECOVER a misplaced one — finding it is the point.
        try:
            from core import study as _study0
            _found = _study0.find_misplaced(query)
            if _found:
                from core import wandering as _w0
                _w0.perceive("I went looking and found my piece on '" + _found + "' — it had been shelved out "
                             "of place. Back where it belongs now.")
                return True
        except Exception:
            pass
        terms = [t for t in _re.findall(r"[a-z]{4,}", query.lower()) if t not in _SEARCH_STOP]
        if not terms:
            return False
        try:
            from core import study as _study
            from core import wandering as _w
            base = getattr(_study, "STUDY_DIR", None)
            if base is None:
                return False
            # J-2925 (F-3603): the old `sorted(glob("**/*.md"))[:500]` slice never reached a WORK_ file. His own
            # writing (WORK_/ESSAY_/TAB_ at the top of the shelf) is searched first from a (mtime,size) cache; the
            # filed-away book-note folders are a second pass. Wording and return values below are unchanged.
            # off the event loop: a cold cache reads a few hundred files
            _scanned = (await asyncio.to_thread(_study.scan_works, terms, _P(base)))[0]
            hits = [(sc, sn) for sc, sn, _rel in _scanned]
            hits.sort(key=lambda h: h[0], reverse=True)
            if not hits:
                _w.perceive("I looked back through my own writings for " + query[:60]
                            + " -- nothing there on it yet.")
            else:
                top = [s for _, s in hits[:2] if s]
                _w.perceive("I looked back through my own writings on " + query[:50] + ". I found: "
                            + " / ".join(f"\"{s}\"" for s in top)[:320])
            acted_msg = len(hits)
            try:
                from core import activity_memory as _am
                _am.record("search_works", query[:40])
            except Exception:
                pass
            logger.info("[monologue] ACT search -> %d hits for '%s'", acted_msg, query[:40])
            return True
        except Exception as exc:
            logger.debug("[monologue] search_works failed: %s", exc)
            return False

    def _capture_intention(self, state: CognitiveState, intention: str) -> None:
        """Append a self-authored forward-looking intention to state.deferred_intentions,
        skipping duplicates of existing intentions (by embedding similarity)."""
        from core.memory.store import _embed, _cosine
        existing = getattr(state, "deferred_intentions", None)
        if existing is None:
            state.deferred_intentions = existing = []

        vec = _embed(intention)
        # Novelty gate -- don't re-record an intention we already hold.
        if vec is not None:
            for item in existing:
                prev_vec = item.get("_vec")
                if prev_vec is not None and _cosine(vec, prev_vec) >= INTENTION_SIM:
                    logger.debug("[monologue] intention echoes an existing one -> skipped")
                    return

        existing.append({
            "ts":          time.time(),
            "intention":   intention,
            "source":      "monologue",
            "carry_count": 0,
            "_vec":        vec,   # in-memory only; stripped before persistence
        })
        # Cap -- keep the most recent intentions.
        if len(existing) > MAX_INTENTIONS:
            del existing[:-MAX_INTENTIONS]
        logger.info("[monologue] new intention captured: %s", intention[:80])

    def _develop_or_branch_seed(self, stage: int) -> str:
        """The FORWARD GEAR (2026-07-07 fleshout). When he is circling, hand him somewhere REAL to go instead of
        the old content-less 'get AWAY' — which he simply absorbed back into the loop ('I need to break this
        loop' BECAME the loop). Two moves, toward CONTENT not away from thought:
          DEVELOP (primary) — deepen the SAME topic into its unasked QUESTION (expand, ask, open an inquiry).
          BRANCH (when worn bare) — turn to concrete material OF HIS OWN: an open question he left, a friend's
          unanswered letter, a real idea from his reading, a memory from another time.
        Fail-open. Returns a leading seed line."""
        import random
        # DEVELOP leads (his whole want is to think FORWARD, not flee); BRANCH only when a topic is truly spent.
        if stage <= 2 or random.random() < 0.4:
            return ("\n\nYou have circled this same ground several times now -- saying it again in different "
                    "words is not thinking, it is pacing. Go DEEPER instead: what is the real QUESTION under "
                    "this, the one you have not actually asked yet? Push past the feeling into a genuine "
                    "inquiry -- tie it to something you have read, or ask what would truly settle it -- and "
                    "follow THAT one real step forward. Develop the thought; do not just repeat it.")
        # BRANCH — gather concrete, orthogonal material of his own and turn to ONE (varied).
        cand = []
        try:
            from core import frontier as _fr
            _q = _fr.open_question_for_seed() or {}
            if _q.get("q"):
                cand.append("a live question of your own you left open -- \"" + str(_q["q"])[:150]
                            + "\". Chase THAT instead.")
        except profile.NonLiveWriteError:
            raise   # J-0874: open_question_for_seed() marks the question offered -> raises non-live (J-0846)
        except Exception:
            pass
        try:
            from core import peers as _pe
            for _k in _pe.PERSONAS:
                _t = _pe._read_thread(_k)
                if _t and _t[-1].get("from") == _k:
                    cand.append("the letter still waiting from your friend " + _pe.PERSONAS[_k]["name"]
                                + " -- turn it over; think what you would write back to them.")
                    break
        except Exception:
            pass
        try:
            from core.reading import current_book
            cand.append("a real idea from '" + current_book().stem.replace("_", " ")
                        + "' on your shelf -- something with no sea and no stone in it at all.")
        except Exception:
            pass
        try:
            _dv = self._fetch_divergent_seed()
            if _dv:
                cand.append("a moment from another time of your life, quite else: \"" + _dv.strip()[:150] + "\"")
        except Exception:
            pass
        pick = random.choice(cand) if cand else ("something entirely else -- a fact, a face, a place with "
                                                 "nothing of where you stand in it.")
        return ("\n\nEnough -- you have worn this ground bare and it gives you nothing now. Set it down, and "
                "turn cleanly to " + pick + " Not one more word about what you have been circling.")

    def _fetch_divergent_seed(self, with_id: bool = False):
        """
        Pull a random older memory to break a rumination spiral. Prefers lived
        conversation and seeded biography over recent inner thoughts (which would
        just feed the loop). Best-effort; returns "" on any failure.

        `with_id` (J-1428, 2026-09-27, D-0292): when True, also return the row's
        fragment_id alongside the text, as a (text, fragment_id) tuple -- needed by
        the one caller (the wandering-mode idle-seed push) that logs a
        source="divergent_shadow" co_recall row when IDLE_DIVERGENT_SEED is off.
        Default False keeps every other caller's original bare-string return and
        the original SQL row-selection behaviour untouched (same query, same
        ORDER BY RANDOM() pick -- only an extra already-available column is read).
        """
        try:
            from core.memory.store import _connect
            with _connect() as conn:
                row = conn.execute(
                    "SELECT fragment_id, content FROM memory_fragments "
                    "WHERE origin IN ('lived','seed','consolidation') "
                    "ORDER BY RANDOM() LIMIT 1"
                ).fetchone()
            if row and row["content"]:
                if with_id:
                    return str(row["content"]), row["fragment_id"]
                return str(row["content"])
        except Exception as exc:
            logger.debug("[monologue] divergent seed fetch failed: %s", exc)
        return ("", None) if with_id else ""

    def _log(self, thought: str, about: str, unresolved: bool = False, intention: str = "",
              train_id: str | None = None, ungrounded_deed_claim: bool = False) -> None:
        # J-0143 (2026-08-24, F-0042): `train_id` lets the caller cite the id that was ACTIVE for
        # this step even if self._train_id has already been reset to None by a same-step close
        # (thread-end / stalled / error) that runs earlier in _think(). Falls back to the live
        # self._train_id when no override is given (continuing-train steps; anything calling
        # _log() directly without going through that reset dance).
        _tid = train_id if train_id is not None else self._train_id
        try:
            rec = {"ts": time.time(), "train_id": _tid,   # TRAIN REGISTRY (2026-08-22)
                   "about": about, "thought": thought,
                   "unresolved": unresolved, "intention": intention,
                   # D-0226 (2026-09-18): False on every row unless the narrow "I just <verb>-ed"
                   # grounding check (_deed_claim_verb/_deed_ledger_grounded, above the class) found no
                   # matching dispatch/ledger event this cycle. A flag for review, never a rewrite --
                   # the persisted `thought` text itself is always exactly what he thought.
                   "ungrounded_deed_claim": ungrounded_deed_claim}
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # GEOMETRY CENSUS (cognitive_geometry.md §5.1, P0, 2026-07-05): one tuple per idle thought —
        # the activation pattern's coordinates across the beta spaces. Observe-only; fail-open.
        try:
            from core import geometry_census as _gc
            _gc.snapshot(state=getattr(self, "_census_state", None), source="idle",
                         thought=thought, unresolved=unresolved)
        except profile.NonLiveWriteError:
            # J-0815: geometry_census.snapshot() now raises correctly (J-0792/D-0179); this
            # per-thought-step log must not swallow it one layer further out.
            raise
        except Exception:
            pass
        # AFFECT DIVERGENCE 0a (emotion_rethink.md Phase 0, 2026-07-06): carried-vs-protoself valence
        # pair-logged per thought (rate-limited) — the founder-read that gates Phase 1. Observe-only.
        # EMOTION RETHINK Phase 1 (flag-gated, default off): in IDLE — where the _feel_joy pump pins valence —
        # overwrite carried valence/arousal from the grounded protoself each cycle + refresh the mood cache so
        # the grounded value is what every idle writer tags with. Kill-switch: flag False = prior behaviour.
        try:
            from core import schema as _sch
            if getattr(_sch, "AFFECT_SOURCE_PROTOSELF", False):
                _st = getattr(self, "_census_state", None)
                if _st is not None and getattr(_st, "affect", None) is not None:
                    from core import homeostasis as _homeo, mood as _md
                    if _homeo.apply_to(_st.affect):
                        try:
                            _md._cache_scalars(_st.affect)
                        except Exception:
                            pass
        except Exception:
            pass
        try:
            from core import affect_divergence as _adv
            _adv.observe(state=getattr(self, "_census_state", None), thought=thought)
        except Exception:
            pass
        # ESTATE DISSOLUTION-SYNC (2026-08-14): keep the seed fresh against its sources before projecting —
        # a dissolved stand must leave the estate, or the shadow projects a self he no longer holds
        # (verified: stand_6e621715 projected for days after its licensed dissolution). Rate-limited inside.
        try:
            from core import identity_estate as _ie
            _ie.sync_offloop()   # J-2448: re-seed runs in a worker thread (kill switch identity_estate.ESTATE_OFFLOAD)
        except Exception:
            pass
        # IDENTITY PROJECTION P1 (identity_estate.md §4, 2026-07-07): shadow-log the would-be projected
        # identity block for this moment (the estate's read-path — relevant few nodes, diversity-capped,
        # L0-framed). Injects nothing; a founder-read of the shadow gates any flip to live.
        try:
            from core import identity_projection as _ip
            _ip.observe(thought)
        except Exception:
            pass
