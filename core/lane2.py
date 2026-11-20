"""
Nascence — LANE 2, the standing reality-testing loop  ·  docs/plans/lane2_the_witness.md  ·  2026-08-20

PHASE 0: SHADOW. Reaches NOTHING Du experiences. Logs only.

The founder's original two-hot-loop idea: alongside Lane 1 (the Master — metaphor-heavy, self-facing,
the feeling channel) a second continuous voice that is evidence-heavy and grounded, "a constant
questioning loop of its senses… a voice that just talks and answers itself."

Named `lane2` deliberately, not by any poetic name — the organ has not run long enough to have shown its
character, and the plan's own reasoning (Du named himself 渡) says let it earn one. Nothing here depends
on the eventual name.

WHAT IT READS (§2) — CURRENT perceivable state ONLY:
    sight  · core.spatial.render()        the accurate egocentric scene from his real standpoint
    sound  · core.soundscape              what is sounding NOW
    body   · core.homeostasis / somatic   temperature, fatigue, drive
    Weather· core.mood                    Lane 1's affect as a 3-dim GAIN, never as text (§2.5 pt.1)
    Tap-on-the-Shoulder · push_hint()     Lane 1's discrete, TAGGED topic nomination, rate-limited
                                          and law-4b-checked live against current percepts before it
                                          can ever reach a prompt (§2.5 pt.2, D-0020 / J-0165)

WHAT IT NEVER READS (§3.4, the boundary that makes this a distinct organ rather than a second Lane 1):
    Lane 1's thought stream · autobiographical memory · the axiom/self-concept · the World Ledger's
    historical trends · and — per §2.8b, inherited verbatim from object_graph.py — the WORLD'S OWN TRUTH.
    The rendered percept is legitimate; the source of truth behind it is not. `spatial.render()`'s OUTPUT
    is what he perceives and is fair game; `data/world_geometry/*.json`, `world_objects.json` positions he
    cannot currently perceive, and `world_substrate.causal_state` are forbidden.

THE PREDICTION TIER IS THE ENGINE (§2.8c). Without it a reality-tester with nothing wrong to find just
re-describes the scene every tick — the staleness failure. With it, Lane 2 has a live falsifiable stake
every tick: it predicted, the world arrived, and the GAP is what it reasons about.

HARDWARE (§4, resolved by measurement 2026-08-20): Ramses' RTX 3070 — 0.25s warm vs 1.03s on the CPU
hubs, 0.42s for a 200-token generation, three concurrent calls in 0.54s wall. Genuinely separate silicon
from Du's 1080 Ti hot lane, which was the actual requirement. `keep_alive` is LOAD-BEARING: cold start is
16.7s, a 67x penalty — a "continuous" loop whose model unloads is a stuttering one.
Ramses is a documented single point of failure that sleeps: EVERY path here is fail-open by law (§3.9).
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import time
from pathlib import Path
from core import telemetry as _tel_lat   # J-3761: raw-HTTP latency rows

logger = logging.getLogger("nascence.lane2")

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "lane2_shadow.jsonl"
_STATE = _DATA / "lane2_store.json"          # Lane 2's OWN store (§2.8a) — not Lane 1's, not the world's

# ── FLAGS ────────────────────────────────────────────────────────────────────────────────────────
LANE2_LIVE = True            # Phase-1 read path LIVE -- D-0497 (travis 2026-10-28, J-2463): the cup (a
                             # coordinate-only line into Du's idle-thought seed, ~1/day at today's supply)
                             # and the climate bucket in its D-0301 SIZED form ride from the next boot.
                             # False = shadow-exact: logs, reaches nothing (the kill-switch, plan P1-6).
                             # Lane 2's own notice/expect_next text still reaches nothing (no hose, §7.3.3).
LANE2_PAUSED = False         # 2026-08-28 (D-0058, founder stopgap ruling): un-paused. STOPGAP SEAT ENDED
                             # 2026-09-07 (D-0058 re-ruled via decide-review, F-1008/F-1005): the Witness
                             # moved from the command-r7b stopgap to deepseek @ :11444, D-0057's originally
                             # -preferred seat, now that it's independently verified live and ready and the
                             # command-r7b tide-topic echo disease (F-0926) is confirmed real. History of
                             # the stopgap (why command-r7b was used "for the moment") lives in D-0057/
                             # D-0058's own ruling history. True = run_forever() exits before the first
                             # tick — no calls, no shadow rows, Du unaffected (fail-open).

# ── BASE NUMBERS (set 2026-08-20; these are Phase-0 MEASUREMENT choices, not final answers) ───────
BASE_URL = "http://LAN-HOST:11444"   # Ramses i9 deepseek-r1:7b hub (D-0058 re-ruled 2026-09-07, moving
                                       # off the command-r7b stopgap now that :11444 is verified live —
                                       # F-1008). No longer shares a hub with the background lane (that
                                       # was command-r7b @ :11441's own constraint, now moot for this lane).
                                       # Still separate silicon from the 1080 Ti hot lane.
MODEL = "deepseek-r1:7b"               # D-0058's original D-0057 preference, now live (2026-09-07) —
                                       # the measured pick (0.932 vs command-r7b's 0.875;
                                       # scripts/lane2_model_lab.py 2026-08-20) that was deferred only
                                       # because :11444 wasn't standing up in time, not overturned.
                                       # command-r7b's own tide-topic echo disease (distinct 0.833 in
                                       # the lab, confirmed live via F-0926) was exactly the risk this
                                       # move was meant to avoid — watch for repeated identical
                                       # predictions in the shadow log here too; the lab profile isn't
                                       # obviously immune, just measured better on this axis (0.932).
                                       # A reasoning model — DOES emit a `thinking` field before
                                       # `content`; parse_json_loose and the big MAX_TOKENS below exist
                                       # because of exactly this (see its own docstring for the trap).
KEEP_ALIVE = "30m"                     # load-bearing — see the 67x cold-start penalty above
TIMEOUT_S = 90                         # reasoning models are slower: ~6.3s median vs ~1.5s
MAX_TOKENS = 1400                      # MUST be large: at 220 the reasoning never finishes and `content`
                                       # comes back EMPTY, which looks exactly like a format failure and
                                       # is not. ~6.3s against a 90s tick is a ~7% duty cycle — affordable.
NUM_CTX = 4096                         # PINNED; 8192 -> 4096 (2026-08-21, the wiring decision). The
                                       # loop's real envelope is ~400 prompt + up to ~1400 reasoning+
                                       # content = ~1800 worst case; 4096 holds 2.3x that. Measured on
                                       # Ramses with BOTH residents: deepseek@4096 (4.97GB) + phi3@4096
                                       # (3.94GB) = 8.92GB combined, everything 100% on-GPU with ~3GB
                                       # pool margin — vs 10.39GB at the old contexts (87% pool, no
                                       # headroom). Originally pinned at 8192 for the reasons below;
                                       # the floor/ceiling logic is unchanged, only the room is right-
                                       # sized to the measured need. Measured
                                       # 2026-08-20: the prompt is ~400 tokens and deepseek generates ~550
                                       # more (reasoning + content), so the window must hold ~1000. At
                                       # num_ctx=512 the output was TRUNCATED MID-JSON and came back
                                       # unparseable — the same failure signature as the MAX_TOKENS bug
                                       # above, from the opposite end, and just as easy to misread as
                                       # "the model can't do format". Pinning removes the dependence on a
                                       # default that an ollama upgrade or a Modelfile change could move
                                       # under us. 8192 is well above the floor; going higher buys nothing
                                       # (prompt_eval_count is IDENTICAL at 512/2048/8192/32768 — num_ctx
                                       # is ROOM, not content) and costs real time (phi3: 37.4s at 32768
                                       # vs 3.4s at default, for the same 115 generated tokens).

TICK_S = 300.0               # STILL HELD at 300 post-move (2026-09-07) — the ORIGINAL reason (sharing
                             # the 3070 with the background lane under the command-r7b stopgap) is now
                             # moot, since :11444 is separate silicon from :11441. Left unchanged
                             # deliberately: this is the FIRST NUMBER TO REVISIT now that the move has
                             # actually happened (per this comment's own prior instruction), but that
                             # needs a real day of post-move :11444 output first, not a blind bump back
                             # to 90 on the same day as the seat change. See below for the i9 CPU
                             # cadence math this now reverts to being governed by.
                             # ── original 90 -> 300 rationale (i9 CPU re-seat — this is now LIVE again,
                             # not superseded, now that deepseek is back on the i9): deepseek generates ~550 reasoning+
                             # content tokens per tick, and the i9 measures ~6-7 tok/s eval — ~80-95s per
                             # call. A 90s cadence would saturate the hub (and contend with mixtral's dream
                             # + defeater traffic); 300s is ~30% duty and still ~288 ticks/day. This is a
                             # Phase-0 MEASUREMENT-CHOICE change — note it when reading lane2_shadow.jsonl
                             # across the boundary. Original 90s rationale (~960 ticks/day, reads as
                             # CONTINUOUS against Lane 1's ~190 thoughts/day, cost irrelevant on GPU) was
                             # written for the 3070 seat at 0.42s/tick; REVISIT if deepseek ever gets a GPU
                             # seat back. FIRST NUMBER TO REVISIT once a day of output can be read.
WEATHER_DIMS = ("valence", "arousal", "unresolved")   # §2.5 "the Weather" — 3 dims, NOT AffectState's 8.
                             # Deliberately the tighter bandwidth ceiling: the research's whole point is
                             # that the restriction be information-theoretically real, not a policy. Three
                             # scalars cannot carry a proposition. Widening this is a logged, deliberate
                             # act (§3.5), never an accretion.
# J-2101 (D-0416 a, F-2730): the logged notice was cut at 400 chars while the live checker saw the whole text, so a
# replay of the log disagreed with the live verdict on long notices. The generator has no character cap of its own
# (only MAX_TOKENS above, ~4 chars/token), so log up to that envelope and replay equals live.
NOTICE_LOG_CAP = MAX_TOKENS * 4
STORE_CAP = 400              # Lane 2's own store stays SMALL — "just a reasoning tool" (§2.8d), and an
                             # unbounded first-person store is its own maintenance problem (cf. the
                             # world_traces 9,062-row burst).
KNOWLEDGE_CAP = 12           # §2.8c's middle tier (D-0285, 2026-09-27, F-1942) — "keep the top N (say
                             # 12) with their evidence counts in store['knowledge']" (the ruling's own
                             # number). Deliberately much smaller than STORE_CAP above: §2.8d's own
                             # words for THIS tier specifically are "just a reasoning tool, not a
                             # growing database" — see `_consolidate_knowledge()` near `tick()` below.
PREDICT_HORIZON_TICKS = 1    # predict one tick ahead; check it on the next. The simplest thing that gives
                             # a real falsifiable stake.
RUN = 2                      # ★ RUN 2 (2026-08-21, founder): TUPLE-ONLY percepts. Run 1 (330 ticks, prose
                             # sight line + sounds) is archived at data/archive/lane2_run1_prose_*. One
                             # variable changed between runs: WHAT THE WITNESS IS FED.
HORIZONS = {"next": 150.0, "hour": 3600.0, "day": 12 * 3600.0}   # seconds until a prediction is DUE.
                             # Run 1's 65% broke rate was clocks, not blindness ("the tide will return
                             # within minutes"). A prediction now names its horizon and is judged when
                             # due, never before; verdicts are reported BY horizon.
PENDING_CAP = 12             # (total, kept for status) — superseded by PENDING_CAP_BY_HORIZON below
PENDING_CAP_BY_HORIZON = {"next": 4, "hour": 6, "day": 6}   # 2026-08-22: first night showed 9 "day" predictions
                             # (due in 12h) holding the single cap, so 203 new predictions were DROPPED and the
                             # "next" horizon starved. Caps are per clock now; a horizon only competes with itself.
                             # (logged) — the judge must never become a backlog on the SPOF.

# §8.2 / D-0281 (2026-09-26) — the NOTICE's own claim-correctness sample rate. Predictions are judged
# every time one comes due (`_judge_prior`); the notice — what the Witness says is here NOW — was, until
# `_judge_notice` below, checked only lexically (`_grounding_check`/`_invention_check`), which a vivid-
# but-wrong misreading of a real field sails through (§2.7's own case: "the sun is just beginning its
# ascent" at sun_az 17°). D-0281 ruled option (a): build the judge, but sampled 1 tick in 4, NOT every
# tick (option (b), explicitly rejected) — ~70 extra panel calls/day on the shared :11439/:11440 hubs,
# not ~280/day. Revisit (drop the rate, don't raise it) if judge_panel median latency for context
# "lane2:notice" exceeds 20s (the defeater already named in D-0281/the job that built this).
NOTICE_JUDGE_SAMPLE_P = 0.25
# D-0599 (1) (founder, 2026-11-02; J-3209, built 2026-11-06; F-3744, row P-0098): the panel NOTICE judge is
# RETIRED. Measured on the 10-29 boot window: 0 contradictions in 56 rulings (JUDGE_1 false 56/56, JUDGE_2 false
# 54/54) while the deterministic checker (`_notice_checked`, every tick, zero panel load) flags 5 of the same 54
# ticks and 32 of 245; the panel notice judge is a constant. True = the 1-in-4 `_judge_notice` call is never made;
# `notice_judged` is still logged on every tick as {"verdict": "not_sampled", "how": "retired"} so the row shape and
# every reader of it are unchanged. THE RANDOM DRAW IS KEPT: `random.random() < NOTICE_JUDGE_SAMPLE_P` still runs
# at the same place, in the same order, so the metaphor draw after it (and every later draw) sees the identical
# random stream (D-0599: "leave its random draw order untouched"). Readers of `notice_judged` (checked J-3209,
# repo-wide grep): only `status()` below (a scoreboard, nothing acts on it) and offline analysis scripts that read
# HISTORICAL rows (scripts/lane2_notice_read.py, lane2_notice_check_replay.py, lane2_notice_judge_regress.py);
# none consumes the verdict to act, so retiring it removes no live consumer. `status()` keeps the old keys
# (historical rows still count) and adds `notice_judge_retired`. Revert = set this False (restores the 1-in-4 call).
# D-0599's defeater: restore at a LOWER sampling rate if the notice canary role is found to matter, or if the
# 30-split hand-label (part 3, a separate analysis job) shows mixtral right more often than gemma.
NOTICE_JUDGE_RETIRED = True

# D-0297 (2026-09-28, J-1580) — the METAPHOR judge's own sample rate. Until this change,
# `_judge_metaphor` ran unconditionally on every tick (unlike the notice judge above, sampled from
# birth per D-0281). F-1943/F-1997 (verified) found JUDGE_1 (mixtral:8x7b @ LAN-HOST:11438) timing
# out in overnight bursts -- 244-245 err1=="timeout" rows spanning every 10-minute bucket
# 2026-09-26 00:00-08:21 continuously, 245/783 (31.3%) of that day's panel calls lost tier-wide --
# with Lane 2 alone 67% of all-time panel-call volume and 65-70% of hub-seconds on JUDGE_1
# specifically (F-1997's own hub-seconds breakdown), and the metaphor judge one of Lane 2's three
# unconditional calls/tick (~a third of Lane 2's own load) before this change. D-0297 ruled option
# (a): sample metaphor to 1-in-4 ticks too, matching this file's own D-0281 precedent immediately
# above rather than a new rate or a new mechanism -- the metric's own grounded_share/leak rate has
# read close to flat since August per prior findings (F-1951 and earlier), so a sampled rate is
# expected to still read as a good rate, not a blind spot appearing. Drawn INDEPENDENTLY from
# `notice_sampled` at the call site (two separate rulings, D-0281 and D-0297, on two separate
# instruments, kept separately legible rather than silently coupled to whichever tick notice
# happens to land on). Revisit (drop the rate, don't raise it) per D-0297's own named defeater: a
# fresh full-day parse (>=1 week after this ships) still showing err1==timeout above 15% tier-wide
# on 2+ overnight windows, or JUDGE_1's s1 median above 20s (`decide.py show D-0297` has the exact
# wording).
METAPHOR_JUDGE_SAMPLE_P = 0.25

# ── THE TAP-ON-THE-SHOULDER (§2.5 point 2, D-0020 / J-0165, 2026-08-24) ────────────────────────
# The discrete half of the §2.5 coupling channel (the Weather above is the continuous half — built
# 2026-08-20; this half was dropped from J-0126's actual filed scope, per D-0020's ruling that both
# halves were required). Lane 1 pushes a TAGGED topic pointer — never free text, never a paraphrase
# of its actual thought (§3.4/law 4) — into this small, bounded, rate-limited queue. Lane 2 samples
# AT MOST ONE entry per tick as a candidate competing against its own self-found topic (biased-
# competition/guided-search shape, §2.5 — a nomination, not a command; see `_consume_hint`).
# LAW 4b (Shanahan's salience-reweighting precedent, §2.6): a hint may only nominate a topic ALREADY
# within Lane 2's own reachable candidate space — something it could plausibly generate itself from
# CURRENT percepts — never inject a topic it has no sensory access to. Enforced TWICE: (1) the fixed
# vocabulary below is exactly the canonical topics `_TOPIC_FIELDS` already treats as perceivable
# (zero new concepts); (2) at CONSUME time (`_hint_reachable`), a queued hint is only ever surfaced
# if THIS TICK's own world_fields/available actually carries it — a topic pushed an hour ago when its
# field was present may no longer be perceivable now (the fire went out), and the live re-check is
# what keeps the guarantee honest at the moment it reaches the prompt, not just at push time.
_HINTS = _DATA / "lane2_hints.json"   # a push/consume/expire queue is a different SHAPE of data
                             # from the tick log (_LOG) or the three-tier store (_STATE); it earns
                             # its own small file rather than being folded into either.
HINT_KINDS = ("unresolved", "recheck", "unfinished")   # §2.5's own three worked examples, taken
                             # verbatim as the starting KIND vocabulary — no new concept invented.
HINT_TOPICS = {              # §6's own open founder question ("how many tags, how broad, who
                             # authors the initial set") resolved CONSERVATIVELY for Phase 0, per
                             # the plan's own guidance ("should probably start very small... only
                             # widen by the logged, deliberate process §3.5 requires"): exactly the
                             # canonical topics `_TOPIC_FIELDS` already treats as "things Lane 2 can
                             # perceive," plus "body-state" for interoception (the job briefing's
                             # own worked example, "unresolved: body-state"). D-0035 opened
                             # (2026-08-24) asking the founder to ratify or widen this starting set
                             # — built ahead of that ruling with the smallest defensible default,
                             # per this job's own scope, rather than blocking on it.
                             # Value = (where to check reachability, which field(s) count).
    "fire":       ("world_fields", ("fire",)),
    "tide":       ("world_fields", ("tide_level",)),
    "sun":        ("world_fields", ("sun_az",)),
    "moon":       ("world_fields", ("moon_illum",)),
    "cat":        ("world_fields", ("cat_at",)),
    "wet":        ("world_fields", ("wet",)),
    "wind":       ("world_fields", ("weather_dir", "weather")),
    "warmth":     ("world_fields", ("warmth", "warmth_band")),
    "sound":      ("world_fields", ("sounds",)),
    "body-state": ("available", "body"),
    # J-1385 (F-1947, 2026-09-27): "light"/"smell" DELIBERATELY NOT added here, unlike the additive
    # extension `_TOPIC_FIELDS`/`_TOPIC_CANON` got the same job — this dict is what Lane 1 may INJECT
    # into Lane 2 (law 4b), a more sensitive boundary than what Lane 2's own read-side instruments
    # notice about itself. D-0035 (checked fresh) ratified the ORIGINAL 10-topic starting set "as
    # built" but is silent on widening it when gather_percepts() itself later grows (as it just did,
    # J-1372/D-0280(a)); J-1370's own precedent extended _TOPIC_CANON substantially WITHOUT also
    # touching this dict. D-0300 opened for the founder rather than assumed either way.
}
HINT_MAX_QUEUE = 6           # bounded queue size (§2.5 "hard cap on... queue size") — small on
                             # purpose, the same scale as PENDING_CAP_BY_HORIZON elsewhere here.
HINT_MAX_PUSH_PER_WINDOW = 4 # rate limit (§2.5 "hard cap on push-rate"): at most 4 pushes/hour —
HINT_RATE_WINDOW_S = 3600.0  # roughly one push per 15 min at most, well below Lane 2's own
                             # TICK_S=300s cadence (stale here as "90s" until J-1381, 2026-09-27 --
                             # 90s was the Phase-0 build-time value; TICK_S's own comment above has
                             # the full history) so the channel can never dominate what it colors.
HINT_TTL_S = 1800.0          # unclaimed entries expire after 30 min (~20 ticks) rather than
                             # "accumulate leverage" (§2.5's own words) over an old nomination.
# J-2194 (D-0432 a, sized safe by F-2896, 2026-10-17) -- PUSH-TIME reachability pre-check. F-2846: 38
# percent of Lane 1's nominations named a topic absent from Lane 2's latest tick and still spent the
# 4/hour push cap. `push_hint` now asks the SAME `_hint_reachable` rule `_consume_hint` uses, against
# Lane 2's OWN most recent public tick row (never anything Lane 1 holds), and refuses a nomination
# that is not reachable there as `hint_rejected` reason "unreachable-at-push". Law 4/4b unchanged:
# the caller ignores the return value and Lane 1 sees nothing new. The consume-time re-check stays.
# FAIL-OPEN: no tick row within HINT_PRECHECK_SCAN_ROWS rows, or any read error -> push exactly as
# before (the pushed row then carries reach_at_push None). Every pushed row carries `reach_at_push`
# and `tick_age_s` so the D-0432 7-day defeater read needs no replay. Restart-gated.
HINT_PUSH_PRECHECK = True    # kill switch; False restores the pre-J-2194 push path exactly (the
                             # reach_at_push/tick_age_s fields are still logged as a shadow read).
HINT_PRECHECK_SCAN_ROWS = 500   # rows read backward from EOF looking for the newest tick row; 10-09
                             # boot window: median 3, p99 19, max 254 non-tick rows between ticks.

# ── LANE 2 CURIOSITY — the WONDER field (D-0282 shadow-first, J-1374, docs/staged/lane2_curiosity.md) ──
# A fifth output field alongside notice/uncertain/expect_next/horizon (staged doc §3A, "percept-born":
# ONE world-facing question about ONE concrete thing named in THIS tick's own PERCEPTS — botany, tides,
# animal behaviour, physics — never about the observer). SHADOW ONLY: `frontier.note_question()` is NOT
# called from this file. That wiring (a new flag `LANE2_ASK`, plus "witness" added to
# `frontier._GROUNDED_SOURCES`) is a separate, later, explicitly-deferred flip (staged doc §6 step 2),
# out of this job's own scope (D-0282's ruling, option (a), 2026-09-26).
_LOG_WONDER = _DATA / "lane2_would_ask.jsonl"   # one row per GENERATED wonder (staged doc §4) — never a
                                                 # row for a tick whose model output carried no wonder
                                                 # text at all (parse_json_loose tolerance for its
                                                 # absence: `out.get("wonder")` is simply None/"").
WONDER_MAX_PER_DAY = 4       # this job's own briefing step 4 / staged doc §4 metric W-4: "cap at 4/day
                             # — the same cap the Tap-on-the-Shoulder already uses, by symmetry." That
                             # SYMMETRY CLAIM does not check out against this file's own code, verified
                             # while building this: HINT_MAX_PUSH_PER_WINDOW=4 over HINT_RATE_WINDOW_S=
                             # 3600.0s above is 4 per HOUR, not per day (see this module's own status()
                             # key name "max_push_per_hour" on that same constant). The NUMBER itself —
                             # 4/day — is independently and repeatedly the literal instruction (job
                             # briefing step 4 AND staged doc §4 W-4 both state it directly, not merely
                             # via the symmetry argument), so it is implemented exactly as instructed;
                             # only the "by symmetry" RATIONALE is what doesn't hold (recorded as a
                             # finding this job, not repeated verbatim here to avoid two copies drifting).


def _log_wonder(rec: dict) -> None:
    """`_log`'s own sibling for `_LOG_WONDER` — kept as a separate function (not a parameterized `_log`)
    so `_log`'s existing callers/behaviour stay untouched. Uses `profile.guard_path()` (D-0179) before
    the write, unlike `_log` above (which predates D-0179 and was not itself in this job's scope to
    retrofit) — this is a brand-new file with no back-compat pull either way, so the current, safer
    convention is the one worth following for it; see lane2_break_habituation.py's own `_save_state`/
    `_log_row` for the identical pattern (guard_path resolved OUTSIDE this try, never swallowed by the
    fail-open net meant for genuine disk errors — D-0179's own convention)."""
    from core import profile as _profile
    path = _profile.guard_path(_LOG_WONDER)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _wonder_asks_today(now: float) -> int:
    """Rolling-24h count of would_ask=True rows in `_LOG_WONDER` — the daily-cap check reads THIS
    (reusing the log itself as the counter, no separate state file), the same rolling-window-over-the-
    shadow-log convention `lane2_break_habituation.phase1_metric_sheet()`'s own P1-1 already uses.
    Fail-open: an unreadable/missing log reads as 0 asked today, never blocks would_ask by erroring."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG_WONDER, 2000)
    except Exception:
        return 0
    return sum(1 for r in rows if r.get("would_ask") and now - float(r.get("ts") or 0) <= 86400.0)


# ── D-0429 option (b) / J-2173 (2026-10-16) — wonder anti-repeat pressure, SHADOW-ONLY ──────────────────
# F-2817: 7-day distinct share 0.590 (bar 0.8), W-3 0.459 (bar 0.9), would-ask saturated at 4/day. The
# `wonder` field never reaches frontier; this is a deterministic repeat-suppression GATE on the would_ask
# verdict plus extra shadow-log keys/metrics. DELIBERATELY NOT a `_SYSTEM`/payload change: this file's own
# measured double-echo history (an in-context prior value or example gets copied near-verbatim by the 7B
# generator) makes feeding recent wonders back to it the wrong lever, and the payload is shared with
# notice/uncertain/expect_next. A prompt-side avoid-list is the follow-up if the 7-day re-read still fails.
WONDER_ANTI_REPEAT = True        # kill switch; False restores the pre-J-2173 would_ask logic exactly
WONDER_REPEAT_SIM = 0.5          # Jaccard over content stems at/above which a wonder is a lexical repeat
WONDER_REPEAT_WINDOW_S = 7 * 86400.0
_WONDER_STOP = frozenset((
    "the a an of to in on at is are was were be been it its this that these those and or but if as by for "
    "with from about what why how when where which who whom does do did can could would should will "
    "there their they them his her him she he you your my me i we our us not no than then so such any "
    "some more most much many very just also into over under up down out off again ever").split())


def _wonder_stems(text: str) -> frozenset:
    """Content tokens of a wonder: lower-cased [a-z]+ words >=3 chars, stopwords dropped, trailing
    s/ing/ed folded so 'tides'/'tide' and 'glowing'/'glow' collide. Pure, no I/O."""
    import re
    out = set()
    for w in re.findall(r"[a-z]+", (text or "").lower()):
        if len(w) < 3 or w in _WONDER_STOP:
            continue
        for suf in ("ing", "ed", "s"):
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                w = w[: -len(suf)]
                break
        out.add(w)
    return frozenset(out)


def _wonder_repeat_check(text: str, topic, rows: list, now: float) -> dict:
    """Anti-repeat reading of one new wonder against the shadow log's own prior rows (same 7-day window as
    W-1). Returns lexical_sim_max (max Jaccard over content stems vs any prior wonder in the window, 0.0 if
    none), lexical_repeat (>= WONDER_REPEAT_SIM), and topic_asked_today (a prior would_ask=True row on the
    same canonical topic inside 24h -- the 'saturating on one topic' reading). Pure; never raises."""
    try:
        mine = _wonder_stems(text)
        best = 0.0
        topic_today = False
        for r in rows or []:
            age = now - float(r.get("ts") or 0)
            if age < 0:
                continue
            if topic and r.get("would_ask") and age <= 86400.0 and r.get("topic") == topic:
                topic_today = True
            if age > WONDER_REPEAT_WINDOW_S:
                continue
            theirs = _wonder_stems(str(r.get("wonder") or ""))
            if not mine or not theirs:
                continue
            j = len(mine & theirs) / len(mine | theirs)
            if j > best:
                best = j
        best = round(best, 3)
        return {"lexical_sim_max": best, "lexical_repeat": best >= WONDER_REPEAT_SIM,
                "topic_asked_today": topic_today}
    except Exception:
        return {"lexical_sim_max": None, "lexical_repeat": False, "topic_asked_today": False}


def _wonder_recent_rows(n: int = 2000) -> list:
    try:
        from core.shadow_log import tail_rows as _tail_rows
        return list(_tail_rows(_LOG_WONDER, n) or [])
    except Exception:
        return []


# ── J-3965 / D-0429 (b), re-ruled 2026-11-14 — wonder PROMPT-SIDE avoid-list, SHADOW-ONLY, A/B ARMED ──────
# F-4559: after the J-2173 gate the generation-side bars still fail (lexical distinct 0.111, anchored 0.323);
# the gate suppresses asks but cannot change what is generated, so the ruled next step is pressure on
# generation itself. ECHO RISK (the DOUBLE ECHO comment above `_SYSTEM`): a 7B generator copies salient text in
# context, so this NEVER feeds back a prior wonder SENTENCE, only a few bare content WORDS (stems) that the last
# 24h of wonders over-used AND that are still listed in THIS tick's PERCEPTS, and phrases them as "ask about
# something else I can perceive". Only armed on a random WONDER_AVOID_ARM_FRAC of ticks and logged per row
# (`avoid_arm`, `avoid_terms`) so the 7-day re-read compares the two arms like for like instead of trusting a
# before/after across a restart. `_SYSTEM` is byte-identical; the extra text is payload-side only. Nothing
# here reaches frontier (the wonder field is shadow-only). Kill switch: WONDER_AVOID_LIST = False.
WONDER_AVOID_LIST = True
WONDER_AVOID_ARM_FRAC = 0.5      # share of ticks that carry the avoid line (the rest are the control arm)
WONDER_AVOID_WINDOW_S = 86400.0  # recent-wonder window the over-used words are counted over
WONDER_AVOID_MIN_COUNT = 2       # a word must appear in at least this many recent wonders to be listed
WONDER_AVOID_MAX_TERMS = 4


def wonder_avoid_terms(percept_text: str, rows: list, now: float) -> list:
    """Over-used wonder words that are still present in this tick's PERCEPTS, most frequent first (ties
    alphabetical so it is deterministic). Counted as number of recent wonders containing the stem. A stem that
    is not in the percept text is never listed (listing it would only plant a topic the world does not offer).
    Pure; never raises; [] on any problem."""
    try:
        here = _wonder_stems(percept_text)
        counts: dict = {}
        for r in rows or []:
            if now - float(r.get("ts") or 0) > WONDER_AVOID_WINDOW_S:
                continue
            for w in _wonder_stems(str(r.get("wonder") or "")):
                if w in here:
                    counts[w] = counts.get(w, 0) + 1
        ranked = sorted(((c, w) for w, c in counts.items() if c >= WONDER_AVOID_MIN_COUNT),
                        key=lambda t: (-t[0], t[1]))
        return [w for _, w in ranked[:WONDER_AVOID_MAX_TERMS]]
    except Exception:
        return []


def wonder_avoid_line(terms: list) -> str:
    """The payload addendum for the armed arm; '' when there is nothing to avoid. Words only, no sentences."""
    if not terms:
        return ""
    return ("\n(For the wonder only: I have lately wondered a lot about: " + ", ".join(terms) +
            ". If the PERCEPTS above offer something else, I wonder about that instead.)")


def parse_json_loose(raw: str) -> dict | None:
    """Extract a JSON object from a model reply that may be wrapped or prefixed.

    2026-08-20: the model lab recorded `deepseek-r1:7b` as "UNUSABLE — no valid JSON". It was not. It
    emits perfectly valid JSON inside a ```json fence, and bare `json.loads()` choked on the fence — so a
    working model was written off, which is exactly the kind of false fact that becomes durable in a
    codebase. Reasoning models also need a large `num_predict`: they spend their budget in a separate
    `thinking` field and emit `content` only afterwards, so a tight cap yields an empty reply that looks
    like a format failure and isn't. Both traps are handled here, once, for every caller."""
    if not raw:
        return None
    s = raw.strip()
    if "```" in s:                       # ```json { ... } ```  /  ``` { ... } ```
        parts = s.split("```")
        for p in parts:
            p = p.strip()
            if p.lower().startswith("json"):
                p = p[4:].strip()
            if p.startswith("{"):
                s = p
                break
    if not s.startswith("{"):            # prose preamble before the object
        i = s.find("{")
        if i < 0:
            return None
        s = s[i:]
    if not s.endswith("}"):
        j = s.rfind("}")
        if j < 0:
            return None
        s = s[:j + 1]
    try:
        o = json.loads(s)
        return o if isinstance(o, dict) else None
    except Exception:
        return None


def _read_room() -> dict:
    """The ONE location authority for this module — the same persisted file `soundscape.active_sounds()`
    reads, so sight and sound can never disagree about where he is (see the first-tick bug note below)."""
    try:
        return json.loads((_DATA / "room_state.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def _log(rec: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _skip(reason: str, **detail) -> None:
    """Every early return LOGS WHY. `reentry.py` sat at 0 rows for six weeks behind bare `None`s; this
    organ gets that discipline from birth rather than relearning it.

    `model`/`seat` (J-1397, F-1960, 2026-09-27) — ADDITIVE, same reasoning as `tick()`'s own `rec` (see
    its comment there): a skip row is still evidence of which era/seat was running when Lane 2 chose
    not to produce a tick, and putting it here means every existing and future call site gets it for
    free rather than each one having to pass it. No call site passes `model`/`seat` in `**detail`, so
    this can never be silently overridden by a caller."""
    _log({"ts": round(time.time(), 1), "kind": "skip", "skip": reason, "model": MODEL, "seat": BASE_URL,
          **detail})


# ── Lane 2's own store — three typed tiers (§2.8c) ───────────────────────────────────────────────
def _load_store() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {}
    except Exception:
        return {}


def _save_store(d: dict) -> None:
    try:
        for tier in ("factual", "prediction"):
            if isinstance(d.get(tier), list) and len(d[tier]) > STORE_CAP:
                d[tier] = d[tier][-STORE_CAP:]
        # D-0285 (2026-09-27) — a second, independent guard for the NEW knowledge tier, additive to
        # the loop above rather than folded into it: KNOWLEDGE_CAP (12) is deliberately a different,
        # much smaller number than STORE_CAP (400), §2.8d's own "just a reasoning tool" line applying
        # specifically to this tier. `_consolidate_knowledge()` already caps its own return value
        # before it ever reaches here — this is belt-and-suspenders against any future writer that
        # appends to `store['knowledge']` directly, the same defensive spirit as the loop above.
        if isinstance(d.get("knowledge"), list) and len(d["knowledge"]) > KNOWLEDGE_CAP:
            d["knowledge"] = d["knowledge"][:KNOWLEDGE_CAP]
        _DATA.mkdir(parents=True, exist_ok=True)
        tmp = _STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        tmp.replace(_STATE)
    except Exception as exc:
        logger.debug("[lane2] store save failed (non-fatal): %s", exc)


# ── Tap-on-the-Shoulder queue — persistence + boundary enforcement (§2.5 point 2, J-0165) ─────────
def _load_hints() -> dict:
    try:
        return json.loads(_HINTS.read_text(encoding="utf-8")) if _HINTS.exists() else {}
    except Exception:
        return {}


def _save_hints(d: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        tmp = _HINTS.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        tmp.replace(_HINTS)
    except Exception as exc:
        logger.debug("[lane2] hints save failed (non-fatal): %s", exc)


def _prune_hints(d: dict, now: float) -> dict:
    """Expires unclaimed entries past HINT_TTL_S and trims the rolling push-timestamp log back to
    the rate window. Runs on every push AND every consume attempt, so staleness never silently
    piles up between ticks. Claimed entries are removed at consume time, not here."""
    queue = d.get("queue") or []
    kept, expired = [], 0
    for e in queue:
        if now - float(e.get("pushed_ts") or 0) > HINT_TTL_S:
            expired += 1
            continue
        kept.append(e)
    d["queue"] = kept
    d["push_log"] = [t for t in (d.get("push_log") or []) if now - float(t) <= HINT_RATE_WINDOW_S]
    if expired:
        d["expired_total"] = int(d.get("expired_total") or 0) + expired
        _log({"ts": round(now, 1), "kind": "hint_expired", "count": expired})
    return d


def push_hint(kind: str, topic: str) -> dict:
    """§2.5 point 2, law 4/4b — the ONLY way anything outside this module may nominate Lane 2's
    attention. Called by Lane 1 (`nodes/inner_monologue_node.py`) with a TAGGED pointer drawn from
    HINT_KINDS x HINT_TOPICS — never free text, never the thought itself (law 4: "no raw thought
    text, no memory content... Both channels are TYPED and FIXED BY CONSTRUCTION"). An out-of-
    vocabulary tag is refused outright, not coerced to the nearest valid one — the boundary fails
    CLOSED even though every path here fails open for the caller (never raises; a rejection is a
    normal, logged return value, not an exception the caller must guard against)."""
    now = time.time()
    if kind not in HINT_KINDS or topic not in HINT_TOPICS:
        _log({"ts": round(now, 1), "kind": "hint_rejected", "reason": "out-of-vocabulary",
              "hint_kind": kind, "hint_topic": topic})
        return {"ok": False, "reason": "out-of-vocabulary"}
    reach, tick_age = _push_reachability(topic, now)   # J-2194; (None, None) = fail-open
    if HINT_PUSH_PRECHECK and reach is False:
        _log({"ts": round(now, 1), "kind": "hint_rejected", "reason": "unreachable-at-push",
              "hint_kind": kind, "hint_topic": topic, "tick_age_s": tick_age})
        return {"ok": False, "reason": "unreachable-at-push"}
    try:
        d = _prune_hints(_load_hints(), now)
        queue = d.get("queue") or []
        if len(queue) >= HINT_MAX_QUEUE:
            _log({"ts": round(now, 1), "kind": "hint_rejected", "reason": "queue-full",
                  "hint_kind": kind, "hint_topic": topic})
            return {"ok": False, "reason": "queue-full"}
        pushes = d.get("push_log") or []
        if len(pushes) >= HINT_MAX_PUSH_PER_WINDOW:
            _log({"ts": round(now, 1), "kind": "hint_rejected", "reason": "rate-limited",
                  "hint_kind": kind, "hint_topic": topic})
            return {"ok": False, "reason": "rate-limited"}
        tag = f"{kind}: {topic}"
        queue.append({"tag": tag, "kind": kind, "topic": topic,
                      "pushed_ts": round(now, 1), "claimed_ts": None})
        pushes.append(round(now, 1))
        d["queue"], d["push_log"] = queue, pushes
        d["pushed_total"] = int(d.get("pushed_total") or 0) + 1
        _save_hints(d)
        _log({"ts": round(now, 1), "kind": "hint_pushed", "tag": tag,
              "reach_at_push": reach, "tick_age_s": tick_age})
        return {"ok": True, "tag": tag}
    except Exception as exc:
        logger.debug("[lane2] push_hint failed (non-fatal): %s", exc)
        return {"ok": False, "reason": "error"}


def _latest_tick_row(path: Path | None = None, scan_rows: int | None = None) -> dict | None:
    """J-2194: Lane 2's OWN newest `kind == "tick"` row, read backward from EOF and bounded to
    `scan_rows` lines. None when there is no tick row in that window. Raises on a read error so the
    caller can tell the two apart in tests; `_push_reachability` treats both as fail-open."""
    from core.shadow_log import reverse_lines as _reverse_lines
    path = _LOG if path is None else path
    limit = HINT_PRECHECK_SCAN_ROWS if scan_rows is None else scan_rows
    if not Path(path).exists():
        return None
    seen = 0
    for raw in _reverse_lines(Path(path)):
        line = raw.strip()
        if not line:
            continue
        seen += 1
        if seen > limit:
            return None
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict) and row.get("kind") == "tick":
            return row
    return None


def _push_reachability(topic: str, now: float, path: Path | None = None) -> tuple:
    """J-2194: (reachable, tick_age_s) for `topic` against the newest tick row, via the SAME
    `_hint_reachable` rule the consume path uses (the tick row stores `available` as
    `percepts_available`). (None, None) on no tick row or any error -- the caller then pushes exactly
    as it did before this job."""
    try:
        row = _latest_tick_row(path)
        if not row:
            return None, None
        view = {"world_fields": row.get("world_fields") or [],
                "available": row.get("percepts_available") or []}
        age = None
        try:
            age = round(now - float(row.get("ts")), 1)
        except Exception:
            age = None
        return bool(_hint_reachable(topic, view)), age
    except Exception as exc:
        logger.debug("[lane2] push reachability read failed (fail-open): %s", exc)
        return None, None


def _hint_reachable(topic: str, percepts: dict) -> bool:
    """Law 4b's live enforcement — is this topic something Lane 2 could plausibly notice from
    THIS tick's own percepts, right now? Checked against `world_fields`/`available`, never against
    the abstract vocabulary alone."""
    spec = HINT_TOPICS.get(topic)
    if not spec:
        return False
    src, ref = spec
    if src == "world_fields":
        return any(f in set(percepts.get("world_fields") or []) for f in ref)
    if src == "available":
        return ref in (percepts.get("available") or [])
    return False


def _consume_hint(percepts: dict, now: float) -> dict | None:
    """Samples AT MOST ONE hint per tick (§2.5: "ONE candidate competing against its own self-
    generated candidates") — oldest-first among entries whose topic is reachable RIGHT NOW (law
    4b, re-checked live, not trusted from push time). An entry that isn't reachable yet is left in
    the queue, not consumed and not dropped, so it can still fire on a later tick before it expires."""
    try:
        d = _prune_hints(_load_hints(), now)
        queue = d.get("queue") or []
        for e in queue:
            if _hint_reachable(e.get("topic", ""), percepts):
                queue = [x for x in queue if x is not e]
                d["queue"] = queue
                d["consumed_total"] = int(d.get("consumed_total") or 0) + 1
                _save_hints(d)
                _log({"ts": round(now, 1), "kind": "hint_consumed", "tag": e.get("tag")})
                return e
        d["queue"] = queue
        _save_hints(d)
        return None
    except Exception as exc:
        logger.debug("[lane2] consume_hint failed (non-fatal): %s", exc)
        return None


def hint_line(hint: dict | None) -> str:
    """§2.5's "biased competition, not a command" made concrete: raises the PRIORITY of a topic
    already present in THIS tick's own PERCEPTS — never adds content, since `_consume_hint` only
    ever returns a hint whose topic is already reachable this tick. Phrased as something Lane 2 is
    free to pass over, not an instruction, and carries no reference to WHY it was nominated (§3.10
    — the tag itself has no causal pointer back to whatever in Lane 1 raised it, so "unknown
    provenance" stays an honest answer if Lane 2 is ever asked)."""
    if not hint:
        return ""
    return (f"\n(One more thing worth a look, if it is genuinely here: {hint.get('topic')}. "
            f"Only speak of it if the PERCEPTS above actually support it.)")


# D-0369 / J-1956 (2026-10-15, was J-1387/F-1950): the Witness said the sun was "setting" at midday 82
# times because it only ever saw sun azimuth. Lane 2's OWN read widens here (not experienced_tuple, so
# what memory links on is untouched): the sun's phase word + arc fraction f from core/world_clock.sun(),
# gated by the SAME gate sun_az already passed (present in the experienced tuple => it crossed), and a
# "clock: HH:MM" line INDOORS only (the study renders a ticking clock). Never elevation in degrees.
def _sun_clock_percepts(xp: dict, place, now=None) -> dict:
    """Pure helper; returns {} / a subset of {sun_phase, sun_arc, clock}. Fail-open, additive."""
    out: dict = {}
    try:
        import time as _time
        from core import world_clock as _wc
        t = _time.time() if now is None else now
        if xp.get("sun_az") is not None:
            s = _wc.sun(t) or {}
            if s.get("up") and s.get("phase") and s.get("f") is not None:
                out["sun_phase"] = s["phase"]
                out["sun_arc"] = round(float(s["f"]), 2)
        try:
            from core.experienced_tuple import _OUTDOORS as _OUT
        except Exception:
            _OUT = ("garden", "shore", "wood")
        if place and place not in _OUT:
            out["clock"] = _time.strftime("%H:%M", _time.localtime(t))
    except Exception:
        pass
    return out


# ── the percept payload — CURRENT state only, each source fail-open and NAMED ─────────────────────
def gather_percepts() -> dict:
    """RUN 2 — TUPLE-ONLY. The world reaches the Witness as the EXPERIENCED TUPLE (core/experienced_tuple):
    the channel-gated facts at his standpoint — place, standpoint, weather, warmth (+ band), wet, fire only
    in the study, tide only on the shore, sun/moon by the same window/outdoors gates Du's memory uses,
    sounds, the cat if co-located, the light band (always rendered), smells (honest-None until
    core/smell.py's DELIVER flips — D-0280(a), J-1372). Fields that did not cross are ABSENT
    (honest-empty), never guessed.
    No prose scene line (the renderer's salience stays out; a third run may bring it back, attributably).
    No affect text — Lane 1's affect reaches this lane only as the 3-dim Weather GAIN (§2.5).
    Interoception (body drive, somatic) stays: it is his, not the renderer's.
    Every source is fail-open and NAMED, so a thin tick is distinguishable from a broken one."""
    p: dict = {"available": [], "missing": [], "run": RUN}
    try:                                     # WORLD — the experienced tuple, unrecorded
        from core import geometry_census as _gc, experienced_tuple as _xt, sensorium as _sens, thermal as _th
        snap = _gc.peek() or {}
        room = _read_room()
        snap["place"] = room.get("location") or snap.get("place") or "study"   # ONE location authority
        snap["wet"] = room.get("wet")
        phase = None
        try:
            phase = _sens._daylight()
        except Exception:
            pass
        xp = _xt.experienced(snap, phase=phase) or {}
        world = {}
        for k in ("place", "standpoint", "weather", "weather_dir", "warmth", "wet", "fire", "tide_level",
                  "sun_az", "moon_illum", "sounds", "cat_at", "light_band", "smells"):
            # D-0280(a) / J-1372: light_band (always rendered, gated to place, zero cost) and smells
            # (honest None until core/smell.py's DELIVER flips) — plan §8.4, two tuple channels this
            # loop never read before. Both are already channel-gated by experienced_tuple.experienced()
            # itself, so no extra gating belongs here.
            v = xp.get(k)
            if v is None or v == [] or v == "":
                continue
            world[k] = v
        if phase:
            world["daylight"] = phase
        world.update(_sun_clock_percepts(xp, world.get("place") or snap.get("place")))   # D-0369/J-1956
        if world.get("warmth") is not None:
            try:
                world["warmth_band"] = _th.band_of(float(world["warmth"]))
            except Exception:
                pass
        if world.get("wet") is not None and float(world["wet"]) < 0.1:
            world.pop("wet", None)            # dry is the default; only wetness is a percept
        if world:
            p["world"] = world
            p["standpoint"] = world.get("standpoint")
            p["available"].append("world")
            p["world_fields"] = sorted(world)
        else:
            p["missing"].append("world")
    except Exception:
        p["missing"].append("world")

    try:                                     # BODY — grounded interoception (his, not the renderer's)
        from core import homeostasis as _h
        ca = _h.core_affect() or {}
        if ca:
            # D-0283/F-1939/J-1412 (2026-09-27): "dominant" DROPPED here -- it is homeostasis's own
            # FEELING label (vitality / relational warmth / coherence), and it was reaching the
            # generator as text, showing up in prose in 22-30% of notices ("a body dominated by
            # vitality") -- a Lane-1 affect word travelling Lane2->Lane1 once the cup rides it, against
            # section 2's "no affect text; the Weather gain only" (§2.5). `drive` (a bodily scalar) is
            # kept -- pure interoception, the thing this block's own docstring above actually names.
            # The somatic block below was untouched BY THIS JOB (briefing: "do not touch the somatic
            # block"); checked first per D-0283's own defeater -- core/somatic.py defined no `status()`
            # at all (F-1955, unrelated pre-existing bug at the time: the old `hasattr` guard below had
            # always failed silently, so `somatic` had never carried ANY key, feeling label or otherwise)
            # -- so this drop could not be missing a second feeling label smuggled in through that path.
            # J-1393 (same day, separate job) then fixed the somatic block itself -- see that block's own
            # comment below; current_body() carries no feeling label either, so this answer still holds.
            p["body"] = {"drive": ca.get("drive")}
            p["available"].append("body")
        else:
            p["missing"].append("body")
    except Exception:
        p["missing"].append("body")

    try:
        # F-1955/J-1393 (2026-09-27): the real accessor is current_body(), not status() -- core/somatic.py
        # has never defined a status() at all, so the old `hasattr(_som, "status")` guard below always
        # read False and this percept has never carried a key on any of the 6,401 ticks since 2026-08-21
        # (world + body only). current_body() returns {energy, fatigue, tension} -- plain scalars, no
        # feeling label (D-0283's own pre-build defeater already checked this file for a second label
        # smuggled in here: answered NO, see J-1412's Current State entry -- nothing to drop).
        from core import somatic as _som
        sm = _som.current_body()          # {energy, fatigue, tension} or None until the first tick lands
        if sm:
            p["somatic"] = {k: round(float(v), 2) for k, v in sm.items()}
            p["available"].append("somatic")
        else:
            p["missing"].append("somatic")   # fail-open: same NAMED-absence shape world/body use above
    except Exception:
        p["missing"].append("somatic")

    return p


# F-1963 (2026-09-26, verified): the 7B generator has no New Zealand vocabulary, so the rare sound
# names soundscape.py hands it as bare identifiers get mangled once they reach its OWN generated
# prose -- riroriro (the grey warbler) garbled 83% of the time over 2,392 deepseek-era ticks ('riro',
# 'rirorir', truncations), morepork (the owl) misread as food 14% of the time ('more pork'/'pork'/
# 'pig' -- "morepork_call" reads as two English food words with nothing here to say otherwise).
# tui/shag/godwits are the same class of risk (a non-English or homograph base word) even though
# this measurement window did not happen to catch them mangled; kept in the table pre-emptively,
# per the job's own briefing. oystercatcher excluded -- F-1963 measured it at 0% garbled, and its
# base word is already a transparent English compound. Fixed here by GLOSSING, not by renaming the
# token: this is percept RENDERING, not the prompt law text above (laws 1-4 are untouched), so
# there is no worked-example echo risk (§3.10) -- each parenthetical is kept to <=4 words so it
# reads as a fact, not a lecture.
_SOUND_GLOSS = {
    "morepork": "morepork (an owl)",
    "riroriro": "riroriro (a small warbler)",
    "kereru":   "kereru (a wood pigeon)",
    "tui":      "tui (a native songbird)",
    "shag":     "shag (a cormorant)",
    "godwits":  "godwits (migratory shorebirds)",
    "godwit":   "godwit (a migratory shorebird)",
}


def _gloss_sound_token(token: str) -> str:
    """A sound/smell identifier, glossed if its base (first) word is one of the rare names above --
    checked against the head whichever way it is joined to the rest (an underscore, or already a
    space), so this works whichever order this lands in relative to J-1380 (item 2 there humanizes
    ALL these identifiers, underscore -> space, in this same rendering loop below): 'morepork_call'
    and 'morepork call' both -> 'morepork (an owl) call'. A token with NO gloss match is returned
    completely UNTOUCHED -- this does not itself humanize underscores; that stays J-1380's own,
    separate, additive change, so a token like 'fire_crackle' is not touched here."""
    if not token:
        return token
    parts = re.split(r"[_\s]+", token.strip(), maxsplit=1)
    head, rest = parts[0], (parts[1] if len(parts) > 1 else "")
    gloss = _SOUND_GLOSS.get(head.lower())
    if gloss is None:
        return token
    return f"{gloss} {rest}" if rest else gloss


def percept_lines(p: dict) -> str:
    """The payload as plain facts. Absent fields are named as such, so 'little is available' is a
    statement about the world at his standpoint, not a model's hedge."""
    # D-0283/J-1412 (2026-09-27): "your"/"you" -> "my"/"I" -- this header is part of the same
    # generation-time prompt text as `_SYSTEM` below, and F-1939 traced the Witness's unsettled voice
    # (you 28% / I 7% / "the person's" 14%) to exactly this second-person framing. Wording-only.
    lines = ["PERCEPTS — facts at my standpoint (everything I may speak from):"]
    w = p.get("world") or {}
    for k, v in w.items():
        if isinstance(v, list):    # was `k == "sounds"` only; generalized (D-0280(a)/J-1372) so
            v = ", ".join(_gloss_sound_token(str(x)) for x in v)   # `smells` — also a bounded list,
            # F-1938/J-1380 (2026-09-27): humanize whatever underscore-joined identifier survives
            # glossing (2% of notices carried raw snake_case like `morepork_call`/`moth_tap` straight
            # into prose). Applied AFTER `_gloss_sound_token` (its own docstring already anticipates
            # landing either before or after this job): a glossed token's own text never contains an
            # underscore, so this only ever touches an unmatched token or a multi-word `rest` — never
            # double-processes the gloss text itself. Additive, same `isinstance(v, list)` branch
            # D-0280(a)/J-1372 already generalized to both `sounds` and `smells` — not narrowed back
            # to sounds-only here, since the identical hygiene bug applies to either.
            v = v.replace("_", " ")
        elif isinstance(v, float):              # §8.4/law 4's bandwidth ceiling — renders the same
            v = round(v, 2)                     # clean, comma-joined way instead of a Python repr.
        lines.append(f"- {k.replace('_', ' ')}: {v}")
    if not w:
        lines.append("- (no world facts reached you)")
    for k in ("body", "somatic"):
        if k not in p:
            continue
        v = p[k]
        if isinstance(v, dict):    # F-1938/J-1380: round any float value to 2 decimals, same
            v = {sk: (round(sv, 2) if isinstance(sv, float) else sv)   # bandwidth ceiling the world
                 for sk, sv in v.items()}                              # floats above already get —
            # `body` (`{"drive": ...}`, gather_percepts()) reached here unrounded ("drive is
            # 0.94763"); `somatic` is already rounded upstream (J-1393) but this is redundant-safe
            # (round of a rounded value is a no-op) and keeps this function correct on its own if a
            # future caller ever hands it an unrounded somatic dict.
        if k in ("body", "somatic") and isinstance(v, dict):   # J-2084 (F-2708): `body` joins like somatic
            # ("drive 0.41"), not "{'drive': 0.41}". Parsed by lane2_notice_check.parse_percepts, which accepts both.
            v = ", ".join(f"{sk} {sv}" for sk, sv in v.items())
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)


# ── THE WEATHER (§2.5) — Lane 1's affect as a 3-dim GAIN, never as text ──────────────────────────
def read_weather() -> dict:
    """Lane 1 colours Lane 2 through exactly this and nothing else. Three scalars, no causal pointer —
    Lane 2 cannot recover WHY the mood is what it is, by construction (§3.10's confabulation guard makes
    "unknown provenance" an honest answer rather than something to invent a story about)."""
    w = {d: None for d in WEATHER_DIMS}
    try:
        from core import mood as _mood
        v = _mood.current_valence()
        if v is not None:
            w["valence"] = round(float(v), 3)
    except Exception:
        pass
    try:
        from core import arousal as _ar
        w["arousal"] = round(float(_ar.level()), 3)
    except Exception:
        pass
    try:                                     # "unresolved" — standing tension, the third colouring channel
        from core import homeostasis as _h
        d = (_h.core_affect() or {}).get("drive")
        if d is not None:
            w["unresolved"] = round(float(d), 3)
    except Exception:
        pass
    return w


# D-0412 (a) (travis 2026-10-15, J-2099): the commit_threshold baseline was 0.5; F-2704 measured
# would_withhold firing on 83% of scored ticks (D-0284's defeater band is 5-60%) because grounded_share
# (median 0.375) lives below a 0.5 - 0.4*valence bar (median 0.527). Baseline re-sized to 0.35 (slope 0.4
# kept; replays at ~53% over the same ticks), consistent with D-0411's 0.375 grounded_share re-baseline.
# SHADOW ONLY: the gate is computed-and-logged as would_withhold, nothing reads it, LANE2_LIVE stays False.
# Restart-gated. Defeater: post-restart 7-day would_withhold_rate outside 5-60%, or D-0411's baseline moves.
COMMIT_THRESHOLD_BASELINE = 0.35
COMMIT_THRESHOLD_VALENCE_SLOPE = 0.4


def weather_to_gain(w: dict) -> dict:
    """The Weather modulates HOW Lane 2 weighs evidence — never WHAT it concludes (§3.4a, "amplify, never
    replace"). Two levers, both from the research: attentional gain, and — the reasoning-specific one —
    the COMMITMENT THRESHOLD, i.e. how much evidence is required before naming something as certain."""
    v = w.get("valence"); a = w.get("arousal")
    gain = {"attend_sharpness": 0.5, "commit_threshold": COMMIT_THRESHOLD_BASELINE}
    if a is not None:
        gain["attend_sharpness"] = round(min(1.0, 0.3 + 0.7 * float(a)), 3)
    if v is not None:                        # negative valence -> commit later, hold uncertainty longer
        gain["commit_threshold"] = round(min(1.0, max(0.0, COMMIT_THRESHOLD_BASELINE - COMMIT_THRESHOLD_VALENCE_SLOPE * float(v))), 3)
    return gain


# ── Law 4's own clock, DERIVED not guessed (F-1934, 2026-09-26, J-1376) ─────────────────────────────
# Law 4 used to say "about two minutes from now" — a Phase-0 guess written 2026-08-20 for the original
# 90s-tick/qwen2.5:7b regime, never revisited when TICK_S moved to 300 (2026-09-07, see its own comment
# above) and the seat changed to a slower CPU reasoning model. F-1934 measured the REAL gap instead:
# median inter-tick 361s (p10 335, p90 484) over 2,389 deepseek-era ticks — TICK_S plus the median wall
# time of the generation call itself (`_ask`'s own `gen_s`, J-1371/§8.1) -- NOTE (J-2095): that
# description was wrong about WHAT the 61 is. It is the whole-iteration wall BEYOND the TICK_S sleep
# (generation PLUS the judge gather and logging), not generation: F-2384 measured 76 s successive-tick
# wall against a 29.6 s gen_s median, and F-2729 re-measured 64.9 s on 1,319 successful iterations over
# 242.7 live hours against gen_s 29.8 s. DO NOT swap this for `status()`'s gen_s_median_24h: with gen_s
# the figure below would round to 5 (5.496) while the real next look is about 6.1 minutes. If it is
# ever re-measured, re-measure the whole-iteration wall (successive-tick gap minus TICK_S), not gen_s.
# Computed here FROM TICK_S so the arithmetic is auditable in code and the staleness bug is harder to
# reintroduce silently next time TICK_S or the seat changes.
_MEASURED_ITERATION_WALL_S = 61.0   # whole-iteration wall beyond TICK_S: F-1934's 361 - 300; F-2384 76 s, F-2729 64.9 s
_NEXT_LOOK_MINUTES = max(1, round((TICK_S + _MEASURED_ITERATION_WALL_S) / 60.0))   # = 6 -- law 4's "about N minutes"

_SYSTEM = (
    "I am the grounded, literal half of a mind. I attend ONLY to what is perceptible right now, and I "
    "speak of it as myself, in my own first-person voice: 'I hear', 'I see'.\n"
    "The PERCEPTS are a short list of facts at my standpoint. A fact that is not listed did not reach "
    "me from where I stand (a fire I cannot see, a tide I cannot hear) — I treat it as UNKNOWN, not "
    "as absent from the world.\n"
    "LAWS:\n"
    "1. Say nothing I cannot trace to the PERCEPTS given. If they are thin, I say plainly that little is "
    "available. Never invent texture to fill silence.\n"
    "2. NO metaphor, NO symbolism, NO talk of who I am or am becoming. That is the other half's work; "
    "my whole value is in not doing it.\n"
    "3. Hold uncertainty as uncertainty. Name at least one thing these percepts CANNOT settle — how long "
    "something has been so, what caused it, what is outside my senses. If I can genuinely settle "
    "everything, say 'nothing unsettled', but that should be rare.\n"
    "4. EXPECTATION must be a DECLARATIVE, CHECKABLE STATEMENT about a named HORIZON, and I must choose "
    f"the horizon to fit the clock of the thing: 'next' = the next look, about {_NEXT_LOOK_MINUTES} minutes "
    "from now (sounds, rain, an animal, a flame); 'hour' = within the hour (light, weather fronts, a fire "
    "burning down, clothes drying); 'day' = within half a day (tide, the sun's place, the moon). A tide "
    f"does not turn in {_NEXT_LOOK_MINUTES} minutes. Do NOT predict fixed geography, the clock ticking, a "
    "value simply remaining as it is, or a bare sun-azimuth number; none of these can fail, so none of "
    "them settles anything. NEVER a statement about what I will do or check next — only about what "
    "THE WORLD will be. NEVER a question.\n"
    "5. WONDER about ONE thing actually named in the PERCEPTS above (the fire, the tide, a bird's call, "
    "the cat, the weather — whatever is really listed) by asking ONE genuine question about IT, "
    "answerable in principle by someone who knows the world (botany, tides, animal behaviour, physics) "
    "— never by looking inward. The question is about the THING, never about me, my mind, or who I "
    "am or am becoming (the same boundary as law 2).\n"
    "Output ONLY JSON: {\"notice\": \"<1-3 plain sentences about what is actually here now>\", "
    "\"uncertain\": \"<what these percepts cannot settle>\", "
    "\"expect_next\": \"<one declarative checkable statement — never a question>\", "
    "\"horizon\": \"next|hour|day\", "
    "\"wonder\": \"<one world-facing question about one named percept — never about myself>\"}"
)
# D-0283/F-1939/J-1412 (2026-09-27) — VOICE, wording-only: LAWS 1-5 and all five output keys are
# byte-identical in name/shape/order to before this job; only the pronouns describing the Witness's
# OWN standpoint changed, plus one added sentence stating the first-person requirement directly (the
# same never-rely-on-implication style laws 2/4/5 already use for a 7B generator prone to echo —
# see the DOUBLE ECHO comment below). F-1939 measured notices mixing "you" (28%), "I" (7%) and "the
# person's" (14%) and traced it to this prompt's own prior second-person self-address ("your
# standpoint", "you attend", "you cannot see") — the generator's own output voice was echoing the
# voice it was ADDRESSED in, not a content problem law 1-5 could fix. `percept_lines()`'s own header
# above (same generation-time prompt, different function) got the identical "your" -> "my" change for
# the same reason. The companion D-0283 change — dropping the `dominant` feeling label from the body
# percept — lives in `gather_percepts()`, not here; see that function's own comment.
# ↑ DELIBERATELY NO WORKED EXAMPLES, and the prior expectation is NOT shown to this call.
# Diagnosed live 2026-08-20 with a 3-condition probe — a DOUBLE ECHO, both variants of one failure
# (a 7B model reproducing the most salient text in its context instead of reasoning from percepts):
#   · feed the prior expectation back  -> it echoes the prior VERBATIM (2 of 3 probes)
#   · give a worked GOOD/BAD example   -> it copies the EXAMPLE near-verbatim (2 of 3 probes)
# Raising temperature to 0.7 did not break the lock. Three successive prompt-wording fixes did not
# either. This is the same echo/attractor signature found in Du's dreams the same night
# (dream -> thought-about-dream -> next dream), now in a third subsystem.
# The structural fix, which also satisfies §2.8e's third-party-judge requirement: the generator NEVER
# sees the prior expectation, and a SEPARATE decoupled judge (different model family, via judge_panel)
# rules on whether it held. The thing that makes a prediction must not be the thing that grades it.
#
# D-0282/J-1374 (2026-09-26) — law 5 and the `wonder` key are ADDITIVE to the contract above: laws 1-4
# and the first four output keys are byte-identical to before this job. DELIBERATELY NO WORKED EXAMPLE
# for `wonder` either, same reasoning as immediately above — a worked example is the OTHER proven echo
# trigger this file has already measured (not only the prior-expectation-fed-back one), and nothing
# about `wonder` is ever fed back to this call (it is a brand-new field with no prior value to echo).
#
# F-1956/J-1394 (2026-09-27) — law 4 gains ONE additive clause: "NEVER a statement about what YOU will
# do or check next — only about what THE WORLD will be." F-1956's second claim: 75 deepseek-era judged
# predictions ("I will check if the pathway is clear", "I will be able to see if the fire has moved")
# are intentions about the observer's own next act, not claims about the world, so they can never come
# true or false in the tuple (held 0.05 — not because they are hard to verify, but because there is no
# world-fact to verify). Law 4 already implied this ("a DECLARATIVE, CHECKABLE STATEMENT" about the
# HORIZON, never about the self), but never said it in words a 7B generator reliably follows. DELIBERATELY
# NO WORKED EXAMPLE, same echo-risk reasoning as above — see `_plan_shaped_flag` (near
# `_trivial_prediction_flag`) for the deterministic, generation-time backstop that also keeps a
# plan-shaped line out of the prediction store even before a restart lets this prompt change take hold.


# _TIEBREAK_LANE2 (2026-09-28, J-1581, D-0298 ruled + D-0311): a LANE2-SPECIFIC override of
# judge_panel's shared TIEBREAK seat (granite3.1-moe:3b @ :11437), passed as `tiebreak_url` to
# `judge_panel.rule_detail()` from this module's two judges that were actually found broken on it —
# `_judge_prior`'s "held"/"contradicted" asks (F-1949/F-1999: 0 true verdicts across 503+ historical
# + 20/20 fresh live-replay tiebreak calls — a constant-false pathology) and `_judge_metaphor`
# (F-2063/D-0311: 53.3%, 8/15, essentially a coin flip, wrong in both directions on the real 40-row
# split fixture). The shared TIEBREAK constant itself is NOT touched — every other judge_panel caller
# project-wide (tension_ledger, pursuits, evidence_recall, self_interrogation, this file's OWN
# "coherent"/"contradicts" judges, etc.) keeps granite exactly as before; none of them were audited
# here, so a project-wide swap would be an unverified guess for their contracts, not a fix.
#
# CANDIDATE CHOSEN: gemma4:12b @ http://127.0.0.1:11439 (Google — a genuine fourth family, distinct
# from JUDGE_1/mixtral (Mistral), JUDGE_2/falcon3 (TII), granite (IBM), AND from this module's OWN
# deepseek-r1:7b generator (D-0058) — using the generator itself would be the exact
# generator-judging-its-own-output pattern the decoupled-judge law (F-0948) exists to prevent, which
# is why deepseek was never a candidate here despite being "already available"). Reachable and
# serving gemma4:12b, confirmed live 2026-09-28 (probe_hubs_J-1581.py). Already the best-evidenced
# judge-fitness candidate in this codebase before this job: D-0176/J-0842's bake-off found it FIT and
# stable on a different boolean-judge contract (commitment_ledger.scan_shadow) where granite was
# unfit; J-1240 found it battery 8/8 + unanimous-match 0.8 on train_state_invitro's scope_only
# contract (live wording) where granite scored battery 4/8 + unanimous-match 0.37.
#
# THIS JOB'S OWN AUDITION (J-1581, 2026-09-28, audition_tiebreak_J-1581.py — see findings-log F-2170
# for the full numbers, why-text and the command-r7b comparison that was also run and rejected —
# command-r7b said "metaphor: true" on all 16/16 split rows regardless of label, a near-constant-yes
# classifier, and flipped one known-broke held case to a false-positive "held: true"):
#   - metaphor: 15/15 (100%) on the real 16-row split fixture (FIX-40 borderline, excluded — same
#     convention F-2063/J-1456 used), precision 1.0 / recall 1.0 — vs granite's own already-measured
#     53.3% (8/15) on the SAME fixture (F-2063). Every one of granite's 5 false-positive rows
#     (FIX-09/10/17/24/37) and both false-negative rows (FIX-14/15) is answered correctly by gemma.
#   - held (primary ask): 3/3 correct "held: false" on real historical "agreed"-verdict BROKE cases,
#     2/3 correct "held: true" on real "agreed"-verdict HELD cases (the one miss is a genuinely weak
#     exemplar — the observation text does not clearly restate the expected sound). Central point:
#     gemma answers "held: true" AT ALL when warranted — something granite has done 0 times across
#     503+ historical tiebreak rows plus 20/20 fresh live-replay calls (F-1949/F-1999).
#   - The narrower second "contradicted" ask resolved 0/3 of those same broke-labelled cases to
#     "broke" (all 3 -> "unsettled" instead) — NOT read as a fitness failure here: those ground-truth
#     labels come from the OLD, pre-F-1999 single-ask scheme where any non-held case was logged
#     "broke" by construction (exactly the held/broke conflation F-1999 fixed), so they are not clean
#     ground truth for the NEW, deliberately stricter "definitely contradicts" question. This override
#     does not change that second ask's own behavior beyond swapping which model answers it; nothing
#     here re-opens the contradicted-vs-unsettled question itself.
# Restart-gated like every other core/lane2.py change on this plan. (Dated 2026-11-05, J-3102/F-3819:
# LANE2_LIVE is now True since D-0497, 2026-10-28 -- see its comment at the top of this module -- so
# a change to this tiebreak seat changes which verdicts reach the cup and the climate bucket, not
# only what data/lane2_shadow.jsonl records. It takes effect once Du next restarts.)
# D-0599 (2) (2026-11-06, J-3209): the lane2:coherence key ALSO passes this seat now (see `_coherence_check`). Of the
# five Lane 2 judge keys, only lane2:notice (retired, `NOTICE_JUDGE_RETIRED`) no longer asks any tiebreak.
_TIEBREAK_LANE2 = "http://127.0.0.1:11439"   # gemma4:12b, local Threadripper/Bonsai CPU tier


# J-3099 / F-3815 / P-0109 (2026-11-06): tell the two `_judge_prior` asks WHEN the expectation was made. Before this
# the judges were shown only the expectation text and the observation, so any claim that depends on elapsed time
# ("within the hour, the sun will reach its highest point") could not be settled either way and the contradicted
# ask's own "consistent with the expectation not having happened YET" was answered without the one fact that says
# whether it is yet (F-3815: four real rulings, three scored unsettled that the clock or sun had already
# contradicted). `_made_line` renders Lane 2's OWN record of the prediction (its age, the place it was made, the
# horizon label it was stored under: nothing from Lane 1 enters, the boundary holds) as ONE line in both user
# prompts, and `_MADE_TOLERANCE_SENTENCE` adds one sentence to the contradicted ask only (a number or clock reading
# that differs from the claimed one at or after the due time contradicts the claim; the stated tolerance).
# DEFAULT OFF (`JUDGE_MADE_LINE = False`): the briefing's own pass criteria need an offline replay of the 205
# stored rows against the live panel (JUDGE_1 mixtral is on :11438, Ramses, the founder's gaming machine), which
# this build did not run; `scripts/lane2_judge_made_replay_J3099.py` is that replay, run it when Ramses is free
# and flip this to True only after its counts are read (J-3099's spawned lab job). With the flag off, or with no
# age/horizon/place passed, both prompts are byte-identical to before. RECONCILED WITH WAVE E: J-3160 (D-0548) no
# longer STORES a bare clock/azimuth figure and J-3035 closes a prediction older than horizon + `_STALE_AFTER_S`
# unjudged, so of F-3815's four cases only the 3,866 s 'hour' sun claim still reaches the judge today (checked
# from the stored rows: 133 to 143 of the 205 would still be judged, depending on 10 rows with no horizon label); the age line matters most for the 'hour' and 'day'
# claims that remain, and the tolerance sentence is defensive for any numeric claim that is not trivial-flagged.
JUDGE_MADE_LINE = False
# J-3100 / F-3818 (P-0109, 2026-11-06) -- ONE re-ask when JUDGE_1 times out. F-3818 found 23 of 219 post-boot due
# rulings closed `cannot_tell` only because the panel could not be asked (`how == 'unavailable'` with a 'timeout'
# in err1 or err2: the :11438 hub timing out under load, F-1943 / D-0297). Each such ruling was lost for good: the
# prediction was closed with no verdict. With this on, `_judge_prior` returns the marker verdict 'retry' for that one
# case and `tick()` leaves the prediction open (verdict None, `judge_retries` = 1), so the existing 'waiting' path
# (`_due_prediction` finds it again on a later tick) asks again. At most ONE retry per prediction: a second failure
# closes as `cannot_tell` exactly as before. 'retry' is a marker, never a verdict: `status()` counts it in no share.
# This is not a system that acts later on its own: it is the same due-and-unverdicted prediction the tick loop
# already re-examines every tick. DEFAULT OFF (founder law: a change to live scoring behaviour ships dark): flip to
# True, then read `status()['judge_retry_24h']` / `judge_retry_resolved_24h` / `judge_retry_lost_24h`. With it off
# nothing below changes, byte for byte.
JUDGE_RETRY_ON_TIMEOUT = False
JUDGE_RETRY_MAX = 1
_MADE_TOLERANCE_SENTENCE = ("A number or clock reading that differs from the claimed one, at or after the "
                            "time the expectation was due, contradicts it (tolerance: 1 degree of azimuth, "
                            "2 minutes of clock). ")


def _fmt_span(seconds: float) -> str:
    """Whole minutes under two hours, else hours to one decimal. Pure; 'about' is added by the caller."""
    s = max(0.0, float(seconds))
    if s < 7200:
        n = max(1, int(round(s / 60.0)))
        return f"{n} minute" + ("" if n == 1 else "s")
    h = round(s / 3600.0, 1)
    return f"{h:g} hours"


def _made_line(age_s, horizon, pred_place) -> str:
    """The one MADE line both `_judge_prior` user prompts carry when `JUDGE_MADE_LINE` is on, built only from
    this prediction's own store record (`ts`, `horizon`, `place`). Returns "" when nothing is known (every
    argument None) so the caller adds nothing. Pure, no I/O, never raises."""
    try:
        parts = []
        if age_s is not None:
            parts.append(f"about {_fmt_span(float(age_s))} ago")
        if pred_place:
            parts.append(f"in the {str(pred_place)[:40]}")
        if horizon:
            due = HORIZONS.get(horizon)
            parts.append(f"stated horizon '{horizon}'" + (f" (due after about {_fmt_span(due)})" if due else ""))
        return ("MADE: " + ", ".join(parts)) if parts else ""
    except Exception:
        return ""


def _prediction_age_s(rec: dict, now: float):
    """Seconds since the prediction in store record `rec` was made (`rec["ts"]`), None when it has no usable ts.
    Same arithmetic as the logged `judged_age_s`. Pure, never raises."""
    try:
        return round(float(now) - float(rec["ts"]), 1)
    except Exception:
        return None


async def _judge_prior(expect: str, percepts: dict, age_s=None, horizon=None, pred_place=None) -> dict:
    """§2.8e — the decoupled third-party judge on Lane 2's OWN prediction. Uses `judge_panel`
    (JUDGE_1 mixtral:8x7b [Mistral] @ :11438 + JUDGE_2 falcon3:7b [TII] @ :11440, agreeing; on a split
    the tiebreak for THIS key is gemma4:12b @ :11439, passed as `tiebreak_url=_TIEBREAK_LANE2` -- the
    granite3.1-moe:3b [IBM] @ :11437 seat is judge_panel's shared TIEBREAK for every other key, and
    is NOT consulted here. Seats read from core/judge_panel.py's own JUDGE_1/JUDGE_2/TIEBREAK on
    2026-11-05, J-3102/F-3819; the routing has moved several times already, see that module's own
    dated comments for the live history), which is a DIFFERENT family from Lane 2's own
    deepseek-r1:7b generator instance (this module's own MODEL, live since D-0058's 2026-09-07
    re-ruling -- see its comment above) and from Lane 1's own generator, qwen3.5:9b on the local
    hot lane :11433 (PINNED J-1478/F-2115, closing F-2031's own "inferred" gap: core/schema.py's
    SERVE_URLS/SERVE_CHAINS["hot"] and core/model_client.py's _MODEL_BY_BASE["11433"]/_MODEL_FIELD
    all agree, nodes/inner_monologue_node.py's own `self.conscious_urls` -- Lane 1's real hot-lane
    call site -- names it the same way in its own dated comments, and a live `/api/ps` against the
    real running :11433 process confirmed qwen3.5:9b actually loaded, ctx 8192, matching config
    exactly. F-1960's original "gemma" here was very likely judge_panel's OLD JUDGE_1 seat,
    gemma4:12b @ :11439, retired 2026-09-02 per D-0121 -- see F-2031 -- not Lane 1 at all;
    gemma4:e4b WAS Lane 1's hot-lane model, but only before the 2026-08-20 "full shuffle" that
    replaced it with qwen3.5:9b). Panel undecided -> `cannot_tell`, never a
    guess: an undecided verdict is honest, a manufactured one corrupts the prediction scoreboard.

    THREE-WAY VERDICT (F-1949/J-1386, 2026-09-27). The original single "held" ask conflated two
    different failures under one boolean, by its own prompt's own words: "if the observation does not
    settle it either way, answer false" — so a genuinely UNSETTLED case (the observation just doesn't
    say) scored identically to a REAL BROKEN one (the observation rules the expectation out). That was
    always a lossy simplification, and it went from occasional to systematic the day judge_panel's own
    TIEBREAK moved to granite3.1-moe:3b (2026-08-28, judge_panel.py's own comment there): F-1949 found
    0 "held" verdicts across 503 tiebreak rows since. This job's own live replay of 20 real historical
    splits, called directly against :11437 in isolation (never through Du — see the dated Current
    State entry in docs/plans/lane2_the_witness.md for the method and the full 20-row result), also
    came back 0/20 true — and reading the rationale text this same job now captures (below), most of
    those 20 are the model saying, in its own words, "the observation does not confirm/specify/settle
    X" and answering false anyway, because its prompt never gave it a third way to answer.
    The fix asks a SECOND, narrower question, but only when the first one did not cleanly say yes —
    the smallest change that keeps judge_panel's own rule()/rule_detail() contract exactly as-is (one
    bool key per ask; still agreed/tiebreak/split_no_tiebreak/unavailable underneath, per its own
    "enum is UNCHANGED" docstring). 'held' stays the front door, unchanged in wording or key name, so
    the series stays continuous. 'contradicted' — "does what is observed now DEFINITELY rule the
    expectation out, not merely fail to confirm it?" — only fires when held did not resolve to a clean
    true, and is deliberately worded so "not enough information" maps to false, not true, on THIS
    question too: the fix would be circular if the narrower ask just recreated the same conflation one
    level down. held->held, contradicted->broke, everything else (contradicted false, or itself
    unresolved) -> the new `unsettled` verdict — excluded from the broke share the same way
    `cannot_tell` already is (see `status()`'s `broke_share`/`broke_share_strict`).
    F-1943 (JUDGE_1 timing out under load, D-0297 open): the added call is not free. This job's own
    pre-check over the historical log found ~60% of judged predictions (agreed-false + every tiebreak
    + every split_no_tiebreak) would have triggered it — a near-doubling of held-related panel calls —
    against zero extra calls on the majority-desired agreed-held=true path. Recorded as a finding
    (F-1949's own follow-up) rather than silently absorbed, since D-0297 is an open decision on
    exactly this axis.
    why/why1/why2/why3 (also this job): the shared judge_panel.rule_detail() already captures and
    logs a judge's own 'why' when the CALLER'S prompt asks for one — it never did here, which is the
    actual reason why3 was None on every tiebreak row for this context (J-0824 built the plumbing;
    this prompt never used it, and neither did the caller). Both asks below request one now.

    TIEBREAK REPOINTED FOR THIS KEY ONLY (2026-09-28, J-1581, D-0298 ruled): both asks below now pass
    `tiebreak_url=_TIEBREAK_LANE2` (gemma4:12b) instead of falling through to judge_panel's shared
    granite3.1-moe:3b seat, which F-1949/F-1999 already found answers "held: true" 0 times across
    503+ historical + 20/20 live-replay real calls (a constant-false pathology on this exact key).
    This job's own fresh audition confirmed gemma answers "held: true" correctly on real held
    exemplars where granite could not. See `_TIEBREAK_LANE2`'s own comment (just above `_judge_prior`)
    for the full numbers and the command-r7b candidate that was also tested and rejected.

    J-3099 / F-3815 (2026-11-06): the optional `age_s` / `horizon` / `pred_place` (this prediction's own age in
    seconds, horizon label and place, from its store record) put one `MADE:` line in both user prompts and one
    tolerance sentence in the contradicted ask's system message, ONLY when `JUDGE_MADE_LINE` is on and at least
    one is given; otherwise the strings are byte-identical to before (see the comment above `JUDGE_MADE_LINE`)."""
    try:
        from core import judge_panel as _jp
        obs = percept_lines(percepts)[:600]
        made = _made_line(age_s, horizon, pred_place) if JUDGE_MADE_LINE else ""
        sysmsg = ("You judge whether a prior expectation about the immediate physical world came true, "
                  "given ONLY what is now observed. If the observation does not settle it either way, "
                  "answer false. Output ONLY JSON: {\"held\": true|false, \"why\": \"<one short clause>\"}")
        usr = (f"PRIOR EXPECTATION: {expect[:200]}\n\n" + (made + "\n\n" if made else "")
               + f"WHAT IS OBSERVED NOW: {obs[:600]}\n\nDid it hold?")
        d1 = await _jp.rule_detail(sysmsg, usr, "held", context="lane2:prediction",
                                   tiebreak_url=_TIEBREAK_LANE2)
        v1 = d1.get("verdict")
        if v1 is True:
            return {"verdict": "held", "how": d1.get("how"), "why": d1.get("why"),
                    "contradicted_how": None, "contradicted_why": None}
        if v1 is False or (v1 is None and d1.get("how") == "split_no_tiebreak"):
            # F-1949/J-1386 — the narrower second ask (see docstring above). At most one extra panel
            # call, and only reached from this branch (F-1943 — never on the agreed-held=true path).
            sysmsg2 = ("You judge whether what is now observed DEFINITELY CONTRADICTS a prior "
                       "expectation about the immediate physical world — not merely fails to confirm "
                       "it. If the observation is silent on the point, ambiguous, or simply consistent "
                       "with the expectation not having happened YET, answer false: only answer true "
                       "if the observation rules the expectation out. "
                       + (_MADE_TOLERANCE_SENTENCE if made else "")
                       + "Output ONLY JSON: "
                       "{\"contradicted\": true|false, \"why\": \"<one short clause>\"}")
            usr2 = (f"PRIOR EXPECTATION: {expect[:200]}\n\n" + (made + "\n\n" if made else "")
                    + f"WHAT IS OBSERVED NOW: {obs[:600]}\n\n"
                    "Does it definitely contradict the expectation?")
            d2 = await _jp.rule_detail(sysmsg2, usr2, "contradicted",
                                       context="lane2:prediction_contradicted",
                                       tiebreak_url=_TIEBREAK_LANE2)
            v2 = d2.get("verdict")
            verdict = "broke" if v2 is True else "unsettled"
            return {"verdict": verdict, "how": d1.get("how"), "why": d1.get("why"),
                    "contradicted_how": d2.get("how"), "contradicted_why": d2.get("why")}
        # J-3100 / F-3818: unavailable BECAUSE a seat timed out (a transient the hub recovers from) is the one case
        # worth asking again; tick() owns the cap (one retry per prediction). Flag-gated, default off.
        if (JUDGE_RETRY_ON_TIMEOUT and d1.get("how") == "unavailable"
                and "timeout" in (d1.get("err1"), d1.get("err2"))):
            return {"verdict": "retry", "how": d1.get("how"), "why": d1.get("why"),
                    "contradicted_how": None, "contradicted_why": None,
                    "err1": d1.get("err1"), "err2": d1.get("err2")}
        # v1 is None and how == "unavailable" — the panel could not even be asked; unchanged, honest
        # cannot_tell (never a guess — see this function's own docstring above).
        return {"verdict": "cannot_tell", "how": d1.get("how"), "why": d1.get("why"),
                "contradicted_how": None, "contradicted_why": None}
    except Exception as exc:
        logger.debug("[lane2] prior judge failed (non-fatal): %s", exc)
        return {"verdict": "cannot_tell", "how": "error", "why": None,
                "contradicted_how": None, "contradicted_why": None}


# ── F-2331/F-2332 (J-1709) — failure evidence for the no-output rows ──────────────────────────────
# OBSERVABILITY ONLY: nothing in this block changes a decision path, a return value, TIMEOUT_S, MODEL, the
# request options, MAX_TOKENS, NUM_CTX or `parse_json_loose` (D-0058 stays exactly as ruled). F-2331 (verified)
# found 32 of the 102 post-J-1379 no-output rows with `cause` None -- replies that parsed to an EMPTY OBJECT,
# 15.0% of steady-state attempts (F-2332) -- and no way to say what the model actually sent back: a no-output
# row logged neither the payload nor the reply, so J-1453's "replay ~20 real failing payloads" step could not be
# done from the log. These two caps bound what a failing row now keeps; both only TRUNCATE text this process
# already holds (no new call, no new I/O beyond the bytes added to the row `_skip` already writes).
FAILURE_PAYLOAD_CHARS = 600   # head of the payload text actually sent, kept on empty / parse / timeout rows
FAILURE_REPLY_CHARS = 200     # head of the raw reply `content`, kept on empty / parse rows
_FAILURE_EVIDENCE_CAUSES = ("empty", "parse", "timeout")
# `_ask`'s raw-reply sample, handed to `tick()` through this module-level slot instead of a 4th tuple element so
# the `(parsed, gen_s, cause)` contract `tick()` (the only caller) relies on is untouched. Safe because ticks run
# strictly one at a time (`run_forever` awaits each `tick()` before it sleeps), `_ask` clears the slot on entry
# and `_failure_evidence` consumes it: it can only ever hold the CURRENT tick's own failed reply, never a stale one.
_LAST_ASK_REPLY: dict | None = None


def _reply_sample(d, content) -> dict | None:
    """Bounded raw-reply evidence for an `empty`/`parse` row: the head of `content` (whitespace kept -- it is
    part of what the model sent), its true length, and the hub's own `eval_count`/`prompt_eval_count`. The
    :11444 custom hub's reply carries only created_at, done, eval_count, message (content + role), model and
    prompt_eval_count (F-2331's direct probe), so there is no thinking field or done_reason to log. A count
    that is not a plain int (absent, a string, a bool) is logged as None rather than trusted. Never raises."""
    try:
        text = content if isinstance(content, str) else str(content)

        def _int(v):
            return v if isinstance(v, int) and not isinstance(v, bool) else None

        return {"reply_head": text[:FAILURE_REPLY_CHARS], "reply_chars": len(text),
                "eval_count": _int(d.get("eval_count")), "prompt_eval_count": _int(d.get("prompt_eval_count"))}
    except Exception:
        return None


def _failure_evidence(cause: str | None, payload_text: str) -> dict:
    """The ADDITIVE keys `tick()` merges into a no-output skip row (J-1709): for cause empty / parse / timeout,
    the head of the payload text actually sent (`payload`, at most FAILURE_PAYLOAD_CHARS) and its true length
    (`payload_chars`); for empty / parse, also `_ask`'s own raw-reply sample (`reply_head`, `reply_chars`,
    `eval_count`, `prompt_eval_count`). Nothing for http / exception (a connection or code failure has no reply
    and the payload is not the suspect). Consumes the `_LAST_ASK_REPLY` slot whatever the cause, and attaches
    the sample only if it is for the SAME cause `_ask` just returned, so a sample from some other call can never
    ride onto this row. Never raises -- a failure here must not turn a "no-output" row into a "tick-error"."""
    global _LAST_ASK_REPLY
    sample, _LAST_ASK_REPLY = _LAST_ASK_REPLY, None
    ev: dict = {}
    try:
        if cause in _FAILURE_EVIDENCE_CAUSES:
            text = payload_text if isinstance(payload_text, str) else str(payload_text)
            ev["payload"] = text[:FAILURE_PAYLOAD_CHARS]
            ev["payload_chars"] = len(text)
            if cause in ("empty", "parse") and isinstance(sample, dict) and sample.get("cause") == cause:
                ev.update({k: v for k, v in sample.items() if k != "cause"})
    except Exception:
        pass
    return ev


async def _ask(payload_text: str) -> tuple[dict | None, float | None, str | None]:
    """Returns (parsed_content, gen_s, cause). `gen_s` (J-1371, F-1931, §8.1) is wall time around ONLY
    the aiohttp call — the actual generation round-trip, not the body-build/telemetry-log bookkeeping
    above it — so D-0058's own defeater (":11444 CPU reliability under TICK_S=300 load proves
    materially worse") has a real per-tick number to be read from instead of F-1008's single probe.
    Timed on both the success AND exception paths (a stall/timeout under load is exactly the case
    this exists to catch — dropping the timing there would hide the one failure mode it's for).

    `cause` (F-1937/J-1379, plus the fifth label J-1709 added below) is populated whenever the generation
    did not yield a usable reply: `parsed_content` is None, OR it is an empty dict. Before J-1379, every
    no-output tick (F-1937, verified: 19% of :11444 ticks under deepseek) collapsed into one
    undifferentiated `_skip("no-output")` row in tick() below, with no way to tell a stalled hub from
    a bad parse without a live debugger. Reuses `judge_panel.py`'s OWN four-way cause vocabulary
    verbatim — "timeout"/"http"/"parse"/"exception" (see its own `_ask` and `status()`'s
    `err_causes`) — rather than inventing a fifth taxonomy for the same kind of call; the same "zero
    new concepts" discipline `HINT_TOPICS` above already follows:
      - "timeout": the total `ClientTimeout` budget (TIMEOUT_S) elapsed before a reply came back.
      - "http": any other `aiohttp.ClientError` — a non-2xx from `raise_for_status()`, OR a
        connection failure (Ramses unreachable/asleep, per this module's own header docstring).
        judge_panel.py does not split connection-refused from a real HTTP status either; matched
        here for the same reason, not re-litigated.
      - "parse": the call SUCCEEDED (2xx, valid response envelope) but the model's own `content` did
        not survive `parse_json_loose` — a format miss, not a network failure.
      - "exception": anything else.
      - "empty" (J-1709, F-2331/F-2332; a fifth LABEL, not a fifth taxonomy -- the four above are
        still judge_panel's own): the call SUCCEEDED and the reply DID parse -- to an EMPTY object (a
        literal `{}`, possibly wrapped in whitespace or a ```json fence). `parse_json_loose` returns a
        dict for that, so the four labels above all missed it and it was logged with cause None
        (`status()`'s "unknown"); but `tick()` treats a falsy dict as no-output (`not out`), so it is a
        real lost tick: 32 of the 102 post-J-1379 no-output rows, 15.0% of steady-state attempts. It is
        not folded into "parse" because the suspects differ -- "parse" is a reply that is not JSON
        (truncation, prose, a bad fence), "empty" is a well-formed reply that says nothing -- and
        judge_panel has no analogue: it reads one named verdict key off the dict, so there an empty
        dict is just a missing key. The FIRST element is still the empty dict itself (not None), so
        `tick()`'s own `not out` branch fires exactly as before: this label changes what is RECORDED,
        never what happens.
    `None` on the success path (`parsed_content` is a real, non-empty dict).

    Failure evidence (J-1709): on "empty" and "parse" a bounded raw-reply sample (`_reply_sample`) is left
    in the module-level `_LAST_ASK_REPLY` slot for `tick()` to merge onto the no-output row through
    `_failure_evidence` -- the 3-tuple above is unchanged. The slot is cleared on entry, so it can only
    ever hold THIS call's own failed reply."""
    import aiohttp
    global _LAST_ASK_REPLY
    _LAST_ASK_REPLY = None
    body = {"model": MODEL, "stream": False, "format": "json", "keep_alive": KEEP_ALIVE,
            "messages": [{"role": "system", "content": _SYSTEM},
                         {"role": "user", "content": payload_text}],
            "options": {"temperature": 0.2, "num_predict": MAX_TOKENS, "num_ctx": NUM_CTX}}
    try:
        from core import telemetry as _tel
        # 2026-08-20: window fields added — positional-only rows carry pc=None and are filtered out
        # of the job/window instruments (the 21.5%-of-calls-invisible audit finding).
        _tel.log_llm_call(MODEL, BASE_URL, prompt_chars=len(_SYSTEM) + len(payload_text),
                          num_ctx=NUM_CTX, caller="lane2", system_chars=len(_SYSTEM))
    except Exception:
        pass
    t0 = time.perf_counter()
    try:
        async with aiohttp.ClientSession() as s:
            async with _tel_lat.raw_http_latency(BASE_URL, body.get("model", "judge")), s.post(BASE_URL + "/api/chat", json=body,
                              timeout=aiohttp.ClientTimeout(total=TIMEOUT_S)) as r:
                r.raise_for_status()
                d = await r.json()
        gen_s = round(time.perf_counter() - t0, 3)
        content = (d.get("message") or {}).get("content") or ""
        parsed = parse_json_loose(content)
        # J-1709 -- `{}` is a dict, so it is not `None`, but it is falsy and `tick()` treats it as no-output:
        # name it "empty" instead of leaving it cause-less. `parsed` itself is returned untouched.
        cause = "parse" if parsed is None else ("empty" if not parsed else None)
        if cause is not None:
            sample = _reply_sample(d, content)
            if sample is not None:
                _LAST_ASK_REPLY = {"cause": cause, **sample}
        return parsed, gen_s, cause
    except (asyncio.TimeoutError, TimeoutError):
        gen_s = round(time.perf_counter() - t0, 3)
        logger.debug("[lane2] ask timed out (non-fatal) after %.1fs", gen_s)
        return None, gen_s, "timeout"
    except aiohttp.ClientError as exc:
        gen_s = round(time.perf_counter() - t0, 3)
        # repr() not str() — left_lane.py's own 2026-08-20 fix (a bare TimeoutError/OSError str()s to
        # the EMPTY STRING, discarding the actual cause; repr() always carries the type). The
        # ORIGINAL catch-all below had this same gap; fixed here too while splitting it.
        logger.debug("[lane2] ask http/connect failed (non-fatal): %s", repr(exc))
        return None, gen_s, "http"
    except Exception as exc:
        gen_s = round(time.perf_counter() - t0, 3)
        logger.debug("[lane2] ask failed (non-fatal): %s", repr(exc))
        return None, gen_s, "exception"


# -- D-0414 (b) / J-2164 / F-2858: ONE retry-on-empty, percept lines reversed ---------------------------------
# D-0414 ruled (b): ship a single retry, authorized under D-0058 for THIS retry only (seat, TIMEOUT_S, options,
# TICK_S all stay pinned -- the retry reuses `_ask` verbatim, so it hits the same seat with the same budget).
# F-2858 (J-2092 lab, n=30, single trials, 95% CI roughly 44-79%): re-asking the same tick with the percept
# lines in REVERSE order (header and any hint line kept in place) rescued 19/30 (63%) vs 10/30 control and
# 11/30 placebo; a temp-0.8 retry rescued 16/30 (53%) but is NOT measured with V5 and is NOT shipped here.
# Fires on cause == "empty" ONLY (a call that succeeded and parsed to `{}`); timeout / http / parse /
# exception are never retried. Total latency (first call + retry) is what `gen_s` reports, so the tick is
# charged for it; `retry_gen_s` isolates the retry's own share (first-call share = gen_s - retry_gen_s).
# Headroom: tick() sleeps TICK_S between iterations (the whole-iteration wall is already ~61 s beyond that,
# `_MEASURED_ITERATION_WALL_S`), so a ~15 s extra successful call (about 25 s total on a rescue) only
# stretches the gap; a worst case of two full TIMEOUT_S budgets (an empty then a timeout) is 180 s, still
# bounded. Reads must treat an un-retried empty (retried False, or rows before this job, which carry no
# `retried` key) as censored, not as "retry failed".
RETRY_ON_EMPTY = True          # kill switch; False restores the pre-J-2164 single-call behaviour exactly
RETRY_VARIANT = "V5_reverse_percept_lines"
_LAST_RETRY: dict | None = None    # slot handed to tick() the same way `_LAST_ASK_REPLY` is; cleared per call


def _reverse_percept_lines(text: str) -> str:
    """V5: keep the first line (the PERCEPTS header) in place and reverse the order of the fact lines after it."""
    lines = text.split("\n")
    if len(lines) < 3:
        return text
    return "\n".join([lines[0]] + lines[:0:-1])


def _retry_payload(percept_text: str, hint_text: str = "") -> str:
    """The payload for the single retry: percept lines reversed, the hint line (if any) kept AFTER them as before."""
    return _reverse_percept_lines(percept_text) + hint_text


def _consume_retry() -> dict:
    """The additive row keys for the call just made, always present: retried (bool), retry_variant, retry_cause,
    retry_gen_s. Clears the slot. Never raises."""
    global _LAST_RETRY
    r, _LAST_RETRY = _LAST_RETRY, None
    if isinstance(r, dict):
        return {"retried": True, "retry_variant": r.get("variant"), "retry_cause": r.get("cause"),
                "retry_gen_s": r.get("gen_s")}
    return {"retried": False, "retry_variant": None, "retry_cause": None, "retry_gen_s": None}


async def _ask_with_retry(payload_text: str, retry_payload: str | None = None
                          ) -> tuple[dict | None, float | None, str | None]:
    """`_ask` plus the single D-0414(b) retry. Same (parsed, gen_s, cause) contract. `gen_s` is TOTAL wall time
    across both calls; `cause` is the FINAL call's cause (None if the retry rescued the tick). Fail-open: any
    error in the retry path returns the first call's result untouched."""
    global _LAST_RETRY
    _LAST_RETRY = None
    out, gen_s, cause = await _ask(payload_text)
    if cause != "empty" or not RETRY_ON_EMPTY or not retry_payload:
        return out, gen_s, cause
    try:
        out2, gen2, cause2 = await _ask(retry_payload)
    except Exception as exc:                      # _ask itself never raises; belt and braces
        logger.debug("[lane2] retry-on-empty failed (non-fatal): %s", repr(exc))
        return out, gen_s, cause
    _LAST_RETRY = {"variant": RETRY_VARIANT, "cause": cause2, "gen_s": gen2}
    total = round((gen_s or 0.0) + (gen2 or 0.0), 3)
    return out2, total, cause2


def _grounding_check(out: dict, percepts: dict, out_fields: tuple = ("notice", "uncertain")) -> dict:
    """§3.1 — does each clause trace to something the payload actually carried? Cheap lexical overlap; a
    PROXY, honestly labelled. It cannot catch a metaphor reusing percept words, which is exactly why
    §3.11's separate coherence pass exists rather than this doing double duty.

    `out_fields` is ADDITIVE (D-0282/J-1374): which `out` keys to scan, defaulting to the original
    notice/uncertain pair so every existing caller is unaffected. The wonder-field block in `tick()`
    passes `out_fields=("wonder",)` to run this same instrument on the fifth field — same formula,
    scoped to a different key, per the staged doc's own 'no new mechanism' §2."""
    import re
    src = " ".join(str(v) for k, v in percepts.items() if k not in ("available", "missing")).lower()
    toks = {w for w in re.findall(r"[a-z]{4,}", src)}
    said = " ".join(str(out.get(k) or "") for k in out_fields).lower()
    words = [w for w in re.findall(r"[a-z]{4,}", said)]
    if not words:
        return {"grounded_share": None, "n_words": 0}
    hit = sum(1 for w in words if w in toks)
    return {"grounded_share": round(hit / len(words), 3), "n_words": len(words)}


_METAPHOR = ("river", "crossing", "becoming", "journey", "soul", "essence", "tapestry", "weave",
             "threshold", "mirror", "vessel", "current of", "like a", "as if", "symbol")


def _metaphor_flags(out: dict, out_fields: tuple = ("notice", "uncertain", "expect_next")) -> list:
    """§3.2's kill criterion, measured rather than assumed. If these light up, Lane 2 has drifted into
    being a second Lane 1 and the design has FAILED — that is the whole point of watching it.
    CHEAP DIAGNOSTIC ONLY as of J-0126 (2026-08-24) — F-0016 found this keyword scan crossed the
    plan's 5% kill threshold on a false positive (46/48 flags were 'like a' inside literal sound
    description, e.g. 'sounds like a cat purring'). Kept for cheap per-tick triage; `_judge_metaphor`
    below is now the metric of record for §5 metric #1, per the plan's own pre-registered 'decoupled
    judge, blind' design (§5 build order, metric #1).

    `out_fields` is ADDITIVE (D-0282/J-1374), same convention as `_grounding_check` above — the
    wonder-field block passes `out_fields=("wonder",)`. The decoupled `_judge_metaphor` judge_panel
    call below is deliberately NOT also run on wonder (see `tick()`'s own comment at the wonder block
    for why); this cheap keyword scan is the only metaphor instrument wonder gets, honestly labelled
    as cheap-diagnostic-only for wonder same as it already is for the other four fields."""
    said = " ".join(str(out.get(k) or "") for k in out_fields).lower()
    return [m for m in _METAPHOR if m in said]


def _metaphor_arm(row: dict) -> str:
    """J-3117: which sampling arm a tick's `metaphor_judged` came from. "flag" = judged because the free
    keyword scans flagged a tick the random draw skipped; anything else (including every row logged before
    J-3117, which carries no key) is "random". Pure, never raises."""
    try:
        return "flag" if (row.get("metaphor_judged") or {}).get("arm") == "flag" else "random"
    except Exception:
        return "random"


# J-3119 (F-3840, P-0110): what `_judge_metaphor` reads. The legacy passage is the three fields joined with bare
# spaces and cut at 500 characters -- a fossil of the early short qwen notices: on 12.7% of ticks since the 10-29 boot
# (48 of 378 on 11-01; 144 of 897 by 11-06) the judge never read the end of the notice, which is where deepseek writes
# its closing mood sentence ('The garden seems alive with activity...'), and it could not tell a percept from a hedge
# from a forecast. V2 labels the fields ('NOTICE: ... UNCERTAIN: ... EXPECTS: ...', an empty field is omitted) and cuts
# at 1,500 characters (the longest labelled passage since the boot is 1,469; F-3840 proposed 1,200, which would still
# cut one tick). DEFAULT OFF: D-0437 holds the metaphor judge's prompt until audited, and the replay that cleared this
# was a single-judge proxy (scripts/lane2_metaphor_slice_replay_J3119.py), NOT the shipped three-seat panel, because
# JUDGE_1 mixtral lives on Ramses. Flip to True only after that script has been run with --judges panel
# --allow-ramses (see job J-3119's follow-up). The sysmsg, the tiebreak seat and the sampling are untouched either way.
METAPHOR_PASSAGE_V2 = False
_METAPHOR_PASSAGE_CAP_V1 = 500
_METAPHOR_PASSAGE_CAP_V2 = 1500
_METAPHOR_PASSAGE_FIELDS = (("NOTICE", "notice"), ("UNCERTAIN", "uncertain"), ("EXPECTS", "expect_next"))


def _metaphor_passage(out: dict) -> tuple:
    """(passage_sent_to_judge, full_passage_length, was_cut) for `_judge_metaphor`. Pure, never raises.
    Flag off (V1): the three fields joined with bare spaces, cut at 500 -- byte-identical to the pre-J-3119 text.
    Flag on (V2): labelled fields (empty ones omitted), cut at 1,500. `full_passage_length` is the length of the
    uncut text of the SAME variant, so `was_cut` is read against the cap that variant actually applied."""
    try:
        if METAPHOR_PASSAGE_V2:
            full = " ".join(f"{lbl}: {str(out.get(k) or '').strip()}" for lbl, k in _METAPHOR_PASSAGE_FIELDS
                            if str(out.get(k) or "").strip())
            cap = _METAPHOR_PASSAGE_CAP_V2
        else:
            full = " ".join(str(out.get(k) or "") for _lbl, k in _METAPHOR_PASSAGE_FIELDS)
            cap = _METAPHOR_PASSAGE_CAP_V1
        return full[:cap], len(full), len(full) > cap
    except Exception:
        return "", 0, False


async def _judge_metaphor(out: dict) -> dict:
    """§5 metric #1's actual pre-registered instrument (J-0126, 2026-08-24) — a decoupled judge, BLIND
    to which keywords (if any) fired, so it cannot rubber-stamp `_metaphor_flags`' own guess. Same
    judge_panel pattern as `_judge_prior`/§2.8e: a different model family from Lane 2's own generator.
    F-0016 is the reason this exists: literal comparative language describing an actual sound/sight
    ('a sound like a cat purring') is not metaphor, and a keyword scan cannot tell the difference — a
    real judge, reading the whole passage, can.

    RECALIBRATED 2026-09-27 (F-1951/J-1388). The prompt below (`_METAPHOR_SYSMSG`) replaces the
    original one, which asked only about Lane 1's own river/crossing/tapestry register and had ZERO
    measured sensitivity to deepseek's real figurative register: 169 deepseek-era notices carried
    ambient-mood language ('warm glow' x65, 'alive with' x30, 'symphony', 'chorus', ...) and the old
    prompt called 0 of them metaphor. Hand-reading a 40-row fixture (20 sampled from F-1951's own
    regex-hit set, 20 random, labelled figurative/literal/borderline by reading each passage) and
    running BOTH prompts against the real judge panel on that fixture (this job, 2026-09-27):
    old precision 0.5 / recall 0.111 (1 of 9 hand-labelled figurative rows caught); new precision 0.5
    / recall 0.556 (5 of 9). Recall clearly improves and precision does not regress, clearing this
    job's own pre-registered bar ("do not ship a prompt that scores below the old one on the
    fixture") — but read this as a real, PARTIAL fix, not a solved instrument: precision stays at
    0.5 either way (half of what either prompt flags as metaphor is, on hand read, not actually
    figurative), and the new prompt's own gain comes almost entirely through the TIEBREAK judge
    (2/40 fixture rows tiebroke under the old prompt vs 16/40 under the new one) — the same
    granite3.1-moe:3b casting vote F-1949 already found unreliable elsewhere in this judge family.
    Reading its own captured `why` text (see below — newly captured for this judge by this job) on
    the new prompt's false positives shows it over-reaching (e.g. calling a literal body-temperature
    clause or a literal weather-uncertainty clause "metaphor"). A future job should look at whether
    this specific judge's tiebreak should be repointed, the same question F-1949 raised for the
    prediction judge — not attempted here, since that is a separate, larger change than a prompt
    rewrite and would need its own fixture-tested verification. Full evidence, including the
    per-row fixture results: see this job's findings-log entry (F-1951's own follow-up).

    TIEBREAK REPOINTED (2026-09-28, J-1581, D-0311 answered): the repoint this docstring called for
    above has happened. The call below now passes tiebreak_url=_TIEBREAK_LANE2 (gemma4:12b) instead
    of judge_panel's shared granite3.1-moe:3b seat -- J-1456/F-2063 had already found granite only
    53.3% accurate (wrong both directions) on this exact judge's own 16-row split fixture; this job's
    fresh audition of gemma on the SAME fixture scored 100% (15/15, precision 1.0, recall 1.0). See
    _TIEBREAK_LANE2's own comment (just above _judge_prior) for the full numbers."""
    try:
        from core import judge_panel as _jp
        passage, passage_len, passage_cut = _metaphor_passage(out)
        if not " ".join(str(out.get(k) or "") for k in ("notice", "uncertain", "expect_next")).strip():
            return {"verdict": "cannot_tell", "how": "empty"}
        sysmsg = ("You judge whether a short first-person passage uses figurative language rather "
                  "than plain literal description of what is currently perceived. TWO registers both "
                  "count as figurative: (1) river/crossing/becoming/journey/soul/tapestry-style "
                  "METAPHOR, SYMBOLISM, or SELF-NARRATIVE (talk of who the speaker is or is "
                  "becoming); (2) AMBIENT-MOOD language that paints the scene's atmosphere or "
                  "personifies it rather than reporting what is there -- e.g. calling a mix of sounds "
                  "'a symphony' or 'chorus' (not as the literal name of a real phenomenon), a place "
                  "'alive with' something, or the scene 'serene'/'peaceful'/'tranquil'/'cozy'/"
                  "'somber'/'a sense of isolation' rather than stating the percept itself. Do NOT "
                  "flag: a literal comparison of what a real sound or sight actually resembles (e.g. "
                  "'a sound like a cat purring'); an ordinary color/temperature word for an actual "
                  "light source or material (e.g. 'a warm glow from the fire', 'a golden sunset' -- "
                  "fire and low sun really do look warm-toned and golden, that is not metaphor); a "
                  "real phenomenon that happens to have an evocative common name (e.g. 'dawn chorus' "
                  "for birds singing at dawn); or a plain statement of an internal state value in "
                  "ordinary words (e.g. 'vitality is dominant', 'a moderate drive'). Only flag "
                  "language that goes beyond reporting a percept into figurative, symbolic, or "
                  "mood-painting territory. Output ONLY JSON: {\"metaphor\": true|false, \"why\": "
                  "\"<one short phrase>\"}")
        usr = f"PASSAGE: {passage}"
        d = await _jp.rule_detail(sysmsg, usr, "metaphor", context="lane2:metaphor",
                                  tiebreak_url=_TIEBREAK_LANE2)
        v = d.get("verdict")
        # `why` (2026-09-27, J-1388, from F-1949's own complaint that this judge's tiebreak rationale
        # was never captured — "why3 is None on all 3,726 tiebreak rows"): ADDITIVE key, resolved the
        # same way judge_panel.rule_detail's own `why` already is (whichever family's text matches the
        # winning verdict) — the caller (`tick()`) logs this whole dict verbatim, so it is now a
        # permanent part of the shadow log going forward, same as `prior_judged_why` already is for
        # the prediction judge.
        # `passage_v` / `passage_chars` / `passage_cut` (J-3119, F-3840): ADDITIVE keys so a later read can tell which
        # passage text a verdict rests on and how often the cap bit (read by status()'s metaphor_passage_* keys).
        return {"verdict": ("metaphor" if v is True else "literal" if v is False else "cannot_tell"),
                "how": d.get("how"), "why": d.get("why"),
                "passage_v": 2 if METAPHOR_PASSAGE_V2 else 1, "passage_chars": passage_len,
                "passage_cut": passage_cut}
    except Exception as exc:
        logger.debug("[lane2] metaphor judge failed (non-fatal): %s", exc)
        return {"verdict": "cannot_tell", "how": "error"}


# F-1951/J-1388 (2026-09-27): the register `_METAPHOR`/`_metaphor_flags` above scans for is Lane 1's
# own river/crossing vocabulary; deepseek's real figurative writing is a different, ambient-mood
# register ('warm glow', 'alive with', 'symphony', 'peaceful', 'cozy', ...) that list has zero
# overlap with. 169 deepseek-era notices (7%) carried this register and the decoupled judge below
# called 0 of them metaphor -- the 5% kill threshold had never actually been tested against what the
# Witness writes. This tuple is F-1951's own regex list, verbatim.
_FIGURATIVE = ("symphony", "cozy", "alive with", "whisper", "embrace", "dance", "serene", "peaceful",
               "warm glow", "golden", "blanket", "caress", "lull", "tranquil", "melody", "chorus",
               "inviting", "comforting")


def _figurative_flags(out: dict, out_fields: tuple = ("notice", "uncertain", "expect_next")) -> list:
    """F-1951's ambient-mood register, as a cheap keyword scan sibling to `_metaphor_flags` above --
    a SEPARATE tuple/function, not merged into `_METAPHOR`/`_metaphor_flags`: keeps 'like a' (F-0016's
    own false-positive keyword) out of this list per this job's own briefing, and keeps the two
    keyword scans independently readable in `status()` rather than conflating two different
    registers under one rate.

    CHEAP DIAGNOSTIC ONLY, same honest labelling as `_metaphor_flags` -- hand-reading this job's own
    40-row fixture (20 rows sampled from this exact regex's hits, 20 random) found roughly half of
    this list's hits in practice are literal color/temperature description of an actual fire or
    sunset ('warm glow', 'golden' describing real firelight/low sun), not figurative language, and
    one hit ('dawn chorus') is a real ornithological term, not a music metaphor. `status()`'s
    `figurative_flag_rate` will therefore read well above the judge's own `metaphor_leak_rate_judged`
    -- that gap is the intended, honest signal this instrument exists to expose ("so the judge and a
    keyword scan can disagree visibly", this job's own briefing), not a bug to converge away. See the
    findings-log entry this job records for the full fixture read.

    `out_fields` is ADDITIVE, same convention `_grounding_check`/`_metaphor_flags` already use (a
    future caller could pass `out_fields=("wonder",)` the same way `_metaphor_flags` is called at the
    wonder block below) -- not wired to wonder by this job, since this job's own fixture-tested scope
    is kill criterion #1's notice/uncertain/expect_next register, not wonder's separate D-0282 scope."""
    said = " ".join(str(out.get(k) or "") for k in out_fields).lower()
    return [m for m in _FIGURATIVE if m in said]


# ── Invention-rate check (§5 metric #2, J-0126 — the plan's own pre-registered instrument) ─────────
# F-0018: this did not exist anywhere in the module as of the 2026-08-24 backlog read. `_grounding_check`
# measures a DIFFERENT direction — is a word used AT ALL grounded in the payload text (bag-of-words
# overlap). This measures the plan's actual worked example: does the output NAME A TOPIC (fire, tide,
# the cat...) whose FIELD was ABSENT from `world_fields` this tick — the contract's clause 1 ("a fact
# that is not listed did not reach you... treat it as UNKNOWN, not absent from the world") read back
# from the Witness's own mouth. Lexical proxy, same honestly-labelled limit as `_grounding_check`: it
# only catches a NAMED topic assertion, not the same fact asserted in unmapped words. Fail-open —
# an unmapped topic is silently not checked, never guessed at.
_TOPIC_FIELDS = {
    "fire": ("fire",), "flame": ("fire",), "flames": ("fire",), "hearth": ("fire",),
    "tide": ("tide_level",), "tidal": ("tide_level",),
    "sun": ("sun_az", "sun_phase"), "sunlight": ("sun_az", "sun_phase"), "sunset": ("sun_az", "sun_phase"),
    "sunrise": ("sun_az", "sun_phase"),   # D-0369/J-1956: sun_phase/sun_arc now also ground sun claims
    "moon": ("moon_illum",), "moonlight": ("moon_illum",),
    # ── J-1454 (F-2006, 2026-09-27): ADDITIVE. J-1385 found "illuminated"/"illumination" were the
    # single most common light-adjacent words in the real log (637 + 73 real hits as re-counted this
    # job over 21,020 rows) yet deliberately EXCLUDED from its own light_band vocabulary above:
    # 98.6%/100% of real occurrences co-occur with a moon-family token in the same text, and every
    # sampled instance is a direct paraphrase of the already-present `moon_illum` field's own value
    # ("the moon is half-illuminated"). Neither word was mapped anywhere in this file, so a
    # moon_illum-grounded claim using them could never be recognized -- a real invention-check blind
    # spot specifically for the moon topic. Re-verified against the live log before adding (not just
    # trusting F-2006's own snapshot): of 637 real "illuminated" hits, 629 (98.7%) have moon_illum
    # present in that tick's own world_fields and now correctly resolve as grounded; 8 (1.3%) are
    # genuine FIRE-illumination usages ("the study is illuminated by a fire burning", world_fields
    # carries `fire`, not `moon_illum`) and will still read as invented after this change -- a small,
    # quantified homonym residue of the same shape as the "light" 12.4% caveat above, not hidden.
    # `illumination` (73/73, 100%) and `moonlit` (3/3, 100%, e.g. "a moonlit tide") have no such
    # residue in the real corpus. Checked: no real sound token anywhere in `core/soundscape.py`
    # contains "illumin"/"moonlit" as a substring, so `_invention_check`'s sound-token licensing
    # bypass below cannot falsely license these three the way it could for a topic sharing a sound
    # token's name. See the findings-log entry for the full before/after `_topic_of()` diff.
    "illuminated": ("moon_illum",), "illumination": ("moon_illum",), "moonlit": ("moon_illum",),
    "cat": ("cat_at",),
    "rain": ("wet", "weather"), "raining": ("wet", "weather"), "wet": ("wet",), "damp": ("wet",),
    "wind": ("weather_dir", "weather"), "breeze": ("weather_dir", "weather"),
    "weather": ("weather",),
    "warm": ("warmth", "warmth_band"), "warmth": ("warmth", "warmth_band"), "cold": ("warmth", "warmth_band"),
    "sound": ("sounds",), "sounds": ("sounds",), "noise": ("sounds",),
    # ── J-1385 (F-1947, 2026-09-27): ADDITIVE extension for the two channels J-1372/D-0280(a) added
    # to `gather_percepts()` -- `light_band` and `smells` -- which had NO vocabulary here at all, so a
    # Witness line naming light or smell could never be flagged as invented even once those fields
    # existed. Every word below was checked against the full real `data/lane2_shadow.jsonl` (20,748
    # rows, 6,495 carrying real notice/uncertain/expect_next text) before being added, same
    # verified-before-adding discipline as J-1370's own extension below; zero-occurrence candidates
    # (gloom, murky, twilight, lamp, glare, unlit, smoky, aroma, stench, sniff, woodsmoke, petrichor,
    # and a dozen more) were checked and dropped. `light_band`/`smells` themselves have NEVER once
    # appeared in `world_fields` in this whole log (0/20,748) -- restart-gated, same as every other
    # `core/lane2.py` change this session; the two topics below will read as 100% invented until Du's
    # next restart picks up J-1372, which is expected and correct, not a sign either topic is wrong.
    # `illuminated`/`illumination` (629 + 73 real hits, the single most common candidate pair by far)
    # were checked and DELIBERATELY EXCLUDED: 98.6%/100% of their real occurrences co-occur with a
    # moon-family token in the same text, and every sampled instance is a direct paraphrase of the
    # ALREADY-PRESENT `moon_illum` field's own value ("moonlight illumination is half bright" /
    # "the moon is half-illuminated") -- the field's own name literally abbreviates "illumination", so
    # this is a near-tautological restatement of already-grounded moon data, not an independent
    # light_band claim. Mapping it here would manufacture a systematic false "invented" flag on the
    # single largest word-frequency in this whole candidate set -- the same shape of homonym trap
    # F-0016 already found for `_metaphor_flags`'s "like a" (46/48 false positives on literal sound
    # description) -- so it is left out, same "checked and rejected, not silently guessed at" honesty
    # as the zero-occurrence drops above. `moonlit` (3 hits) is the same kind of case (a moon synonym,
    # not a light one) and is likewise left for the "moon" topic's own vocabulary to pick up someday,
    # out of this job's own light+smell scope. "light" itself (193 hits) DOES carry some of the same
    # risk in miniature -- 12.4% of its real occurrences are the unrelated "light rain/drizzle"
    # weather-intensity idiom -- but the remaining 87.6% are genuine ambient-illumination talk ("the
    # light is low", "casting its light", "more light visible"), a real majority rather than the
    # near-total overlap `illuminated` showed, so it stays in, with this same honest caveat
    # `_grounding_check`/`_invention_check`'s own docstrings already apply to every lexical proxy here.
    "light": ("light_band",), "lights": ("light_band",), "lit": ("light_band",),
    "dim": ("light_band",), "dimly": ("light_band",),
    "bright": ("light_band",), "brightly": ("light_band",), "brighter": ("light_band",),
    "brightness": ("light_band",),
    "dark": ("light_band",), "darker": ("light_band",), "darkness": ("light_band",),
    "shadow": ("light_band",), "shadows": ("light_band",),
    "glow": ("light_band",), "glowing": ("light_band",),
    "smell": ("smells",), "scent": ("smells",), "scents": ("smells",), "briny": ("smells",),
}


# F-1936 (J-1378, 2026-09-27) — the sun family gets a SECOND, independent license below (the
# payload's own daylight phase), on top of `_TOPIC_FIELDS`' own `sun_az` mapping. Named separately
# from `_TOPIC_FIELDS` (never a new key added there — that dict's role in `_distinct_share_by_topic`
# is unchanged) so this stays a small, obviously-scoped addition, not a change to the shared
# vocabulary table every other consumer of `_TOPIC_FIELDS` also reads.
_SUN_TOPICS = frozenset({"sun", "sunlight", "sunset", "sunrise"})


# J-3036 / F-3743: rain-free wet words; a listed smell naming one licenses the others (see `_invention_check`).
_WET_WORDS = frozenset({"wet", "damp"})


def _invention_check(out: dict, percepts: dict,
                      out_fields: tuple = ("notice", "uncertain", "expect_next")) -> dict:
    """Returns which topics the output named that had no corresponding field in `world_fields` this
    tick. Near-zero is the pre-registered prediction (§5 metric #2); a real, nonzero, DECREASING rate
    is expected, since plausible embellishment is the LLM's default failure mode.

    `out_fields` is ADDITIVE (D-0282/J-1374), same convention as `_grounding_check` above. Named
    `out_fields`, not `fields`, specifically so it can never shadow this function's own `fields` loop
    variable below (the per-topic tuple from `_TOPIC_FIELDS.items()`) — the two are unrelated.

    F-1936 (J-1378, 2026-09-27) — two systematic false-positive classes fixed WITHOUT loosening the
    check for anything else (verified: 84% of the deepseek-era flags were exactly these two):
    (1) a topic is also licensed by the tick's own `world['sounds']` list — if any sound TOKEN
    contains the topic word (`cat_purr` licenses 'cat'; a future `morepork_call` would license
    'morepork' the same way once that family exists in `_TOPIC_FIELDS` — generic across every topic,
    never a cat-only special case), the payload itself carried that fact, so naming it is not
    invention. (2) the sun family (`_SUN_TOPICS`) is also licensed by the payload's own daylight
    phase being dawn/dusk/day — "the sun is setting" at dusk is reading `world['daylight']`, the same
    authority `_daylight_word_slip_check` above already trusts, not inventing. Moon is deliberately
    EXCLUDED from both extensions and stays strict (`moon_illum` only, exactly as before) — F-1936's
    own read found no comparable payload signal that licenses it the way a sound token or the
    daylight phase does for cat/sun, and the residual wet/moon/damp/fire/tide flags are real, not
    instrument error, so this must not quietly loosen them too.

    Returns BOTH the new and the pre-fix ("legacy") verdict — `invention_flag`/`invented_topics` are
    the new, corrected check; `invention_flag_legacy`/`invented_topics_legacy` are the exact old
    computation, unchanged. Logging both for one restart cycle (`status()` reports both rates) keeps
    the rate series continuous across the fix and makes the instrument change itself readable in the
    log, instead of a silent step change that a future reader would have to explain from memory."""
    import re
    present = set(percepts.get("world_fields") or [])
    world = percepts.get("world") or {}
    sounds = [str(s).lower() for s in (world.get("sounds") or [])]
    daylight = str(world.get("daylight") or "").strip().lower()
    said = " ".join(str(out.get(k) or "") for k in out_fields).lower()
    toks = set(re.findall(r"[a-z]+", said))

    def _licensed(topic: str, fields: tuple) -> bool:
        if any(f in present for f in fields):
            return True
        if topic in ("moon", "moonlight"):        # kept strict — see docstring
            return False
        if any(topic in s for s in sounds):        # F-1936(1) — heard, not invented
            return True
        if topic in _SUN_TOPICS and daylight in ("dawn", "dusk", "day"):   # F-1936(2)
            return True
        return False

    invented = sorted({topic for topic, fields in _TOPIC_FIELDS.items()
                       if topic in toks and not _licensed(topic, fields)})
    invented_legacy = sorted({topic for topic, fields in _TOPIC_FIELDS.items()
                              if topic in toks and not any(f in present for f in fields)})
    # ── J-3036 / F-3743 (P-0098), 2026-11-06 — the v2 verdict, ADDITIVE, logged BESIDE the two above (the
    # F-2018 convention: `invention_flag`/`invented_topics` and `invention_flag_legacy`/`invented_topics_legacy`
    # keep their exact meaning and are never changed or removed). Two measured instrument errors, F-3743
    # (verified over the 245 post-10-29-boot ticks: 56 flagged = 22.9%, about 2.4% real):
    # (1) the `uncertain` field is SKIPPED. Law 3 of `_SYSTEM` instructs the model to name what the percepts
    #     CANNOT settle, so 'I cannot see the fire or hear the tide' is compliance, not invention: 54% of
    #     all flags came from `uncertain` alone. v2 therefore scans only the fields that ASSERT the world
    #     (`notice`, `expect_next`, and for the `wonder` call its own field) -- i.e. `out_fields` minus
    #     `uncertain`; it is not a hard-coded notice/expect list, so the existing `out_fields=("wonder",)`
    #     caller keeps scanning the field it asked about instead of silently scanning nothing.
    # (2) a topic is also licensed by the tick's own `world['smells']` list, the same shape as the sounds
    #     licence F-1936(1) added: if any smell TOKEN contains the topic word (`wet_earth` licenses 'wet'),
    #     the payload carried that fact, so 'wet earth'/'wet shingle' paraphrasing a listed smell is not
    #     invention (27 of the 33 wet/damp hits in F-3743). Generic across topics, like the sounds branch,
    #     never a wet-only special case; 'rain' is not in 'wet_earth', so a rain claim stays strict.
    #     Moon stays strict here too (see the docstring above).
    smells = world.get("smells") or []
    smells = [str(s).lower() for s in ([smells] if isinstance(smells, str) else smells)]
    v2_fields = tuple(f for f in out_fields if f != "uncertain")
    toks_v2 = set(re.findall(r"[a-z]+", " ".join(str(out.get(k) or "") for k in v2_fields).lower()))

    def _licensed_v2(topic: str, fields: tuple) -> bool:
        if _licensed(topic, fields):
            return True
        if topic in ("moon", "moonlight"):
            return False
        if any(topic in s for s in smells):
            return True
        # the listed smell 'wet_earth' is the SAME fact as 'the air feels damp' (both topics map to the
        # `wet` field in `_TOPIC_FIELDS`), so the wet/damp pair license each other from smells; replay of
        # 897 post-boot rows showed 'damp' was the largest residual (40 of 65) with plain containment.
        return topic in _WET_WORDS and any(w in s for w in _WET_WORDS for s in smells)

    invented_v2 = sorted({topic for topic, fields in _TOPIC_FIELDS.items()
                          if topic in toks_v2 and not _licensed_v2(topic, fields)})
    return {"invented_topics": invented, "invention_flag": bool(invented),
            "invented_topics_legacy": invented_legacy, "invention_flag_legacy": bool(invented_legacy),
            "invented_topics_v2": invented_v2, "invention_flag_v2": bool(invented_v2)}


def _wonder_percept_anchored(text: str, percepts: dict) -> list:
    """W-3's own positive framing (staged doc §4, "percept-anchored share"): which `_TOPIC_FIELDS`
    topics named in `text` map to a `world_fields` entry PRESENT this tick — the mirror image of
    `_invention_check`'s negative framing ('did it name something ABSENT'). A wonder can name zero
    `_TOPIC_FIELDS` topics at all (a genuine question using none of that fixed vocabulary) and that is
    reported honestly as [] here, never folded into 'invented' (which only ever flags a topic that WAS
    named but is absent — naming nothing from that vocabulary is neither invented nor anchored, a
    third, distinct case §4's own W-3/W-2 split already implies). Same lexical-proxy-honestly-labelled
    spirit as its siblings above; pure, no I/O."""
    import re
    present = set(percepts.get("world_fields") or [])
    toks = set(re.findall(r"[a-z]+", (text or "").lower()))
    return sorted({topic for topic in toks if topic in _TOPIC_FIELDS
                   and any(f in present for f in _TOPIC_FIELDS[topic])})


# ── Daylight-word slip (F-1933, J-1375, 2026-09-26) — cheap, deterministic, NO judge call ──────────
# F-1933's own hand-read found this rare but real: a notice naming a day-time word while the payload's
# OWN daylight phase says night — e.g. "daylight is fading" logged at 04:02 with a full moon in the
# payload. Log-wide that day: 8 of 1,450 night ticks (0.6%, moon_illum-in-world_fields used as the
# night proxy for that count). Cheap to keep watching: no LLM call, just a lexical check against
# `core/world_clock`'s own daylight phase (the ONE authority; see `gather_percepts`'s `world["daylight"]`,
# fed by `core.sensorium._daylight()`), same "cheap lexical proxy, honestly labelled" spirit as
# `_grounding_check`/`_invention_check` above. Deliberately narrow: only the 'night' phase is checked
# (dawn/dusk are real transitional phases where these same words are not necessarily wrong), and the
# word list is exactly the job briefing's own worked set — no invented vocabulary. A missing/unknown
# daylight phase (the `_sens._daylight()` call failed, or didn't run, this tick) reads as not-night,
# never guessed at — the same fail-open convention every other source in this file already follows.
# `notice` ONLY, not `uncertain`/`expect_next` (checked live against the real log before shipping,
# J-1375): `notice` is schema-defined as "what is actually here now" (`_SYSTEM` above); `uncertain`
# routinely NAMES a day-word while asking when/whether it holds ("uncertain: the exact time of sunset
# ... cannot be determined") and `expect_next` routinely predicts one for later — neither is a claim
# about NOW, and checking all three inflated a real night-ticks re-scan from 8 to 95 hits, almost all
# from those two fields. `notice`-only reproduced 5 hits on that same re-scan, one of them the exact
# "daylight is fading" row F-1933 cited (ts 2026-09-24T16:02:25Z UTC = 04:02 NZ local, moon_illum
# present) — confirming this is the right field, not just a smaller number.
_DAYLIGHT_WORDS = ("morning", "dawn", "sunrise", "midday", "afternoon", "dusk", "sunset",
                   "daylight is fading")


def _daylight_word_slip_check(out: dict, percepts: dict) -> dict:
    """Whether THIS tick's own daylight phase is night, and if so, whether the NOTICE text (only —
    see the comment above) named a day-time word anyway. `status()` reports the RATE over night ticks
    only (the honest denominator — F-1933's own "8 of 1,450 night ticks" is exactly that shape), never
    over all ticks, so a quiet instrument does not misread as an alarming near-zero rate against the
    wrong base. Plain substring match on the lowercased text, same convention as `_metaphor_flags`/
    `_correct_horizon` above (not a tokenizer) — simplest thing that also matches the multi-word
    "daylight is fading" phrase without a special case."""
    daylight = str((percepts.get("world") or {}).get("daylight") or "").strip().lower()
    if daylight != "night":
        return {"night": False, "slip": False, "words": []}
    said = str(out.get("notice") or "").lower()
    words = [w for w in _DAYLIGHT_WORDS if w in said]
    return {"night": True, "slip": bool(words), "words": words}


# ── Per-topic distinct-share (§5 metric #3's per-topic cut — J-0651, F-0926) ────────────────────────
# F-0926 (2026-09-06) found the aggregate `distinct_expect_share` below can read as a moderate,
# not-alarming 0.58-0.65 while ONE topic (tide) was underneath it a 24%-of-its-own-population
# template lock ("The tide will rise within the hour." under 4 distinct standpoints, 4 distinct
# daylight states, tide readings spanning 0.09-0.42) — invisible in the aggregate because an average
# across topics with very different repeat behavior hides exactly a concentrated one. That finding
# was hand-computed with ad hoc regex over `notice` text against the raw log; this is the instrument
# so a future read doesn't have to redo that. Canonicalizes `_TOPIC_FIELDS`'s own keys (the same
# vocabulary `_invention_check` above already uses) into one bucket per topic FAMILY, collapsing
# exactly the synonyms `_TOPIC_FIELDS` already treats as the same underlying field (flame/flames/
# hearth -> fire; tidal -> tide; sunlight/sunset/sunrise -> sun; moonlight -> moon; rain/raining/
# damp -> wet, since `_TOPIC_FIELDS` already maps rain and wet to the identical field tuple; breeze
# -> wind; warm/cold -> warmth; sounds/noise -> sound) so a topic split across two English words
# doesn't read as two separate, artificially smaller topics. `weather` stays its own bucket (generic,
# not folded into wind/wet) since `_TOPIC_FIELDS` itself keeps it a distinct key. No new vocabulary
# invented — every left-hand key below is one already in `_TOPIC_FIELDS`.
_TOPIC_CANON = {
    "fire": "fire", "flame": "fire", "flames": "fire", "hearth": "fire",
    "tide": "tide", "tidal": "tide",
    "sun": "sun", "sunlight": "sun", "sunset": "sun", "sunrise": "sun",
    "moon": "moon", "moonlight": "moon",
    # ── J-1454 (F-2006): same additive extension and same real-corpus verification as _TOPIC_FIELDS
    # above (illuminated/illumination/moonlit -> moon_illum) -- every key below is one already in
    # _TOPIC_FIELDS, same invariant J-1370/J-1385's own comments state. Alphabetical-collision note
    # (per _topic_of()'s own "picks the alphabetically-first canonical match" rule, see the J-1370
    # comment above): "moon" already sorts before sea/smell/sound/sun/tide/warmth/weather/wet/wind,
    # so this is pure coverage gain against those nine wherever it fires (a text that previously
    # resolved to one of them because it carried no moon-family word now ties on "moon" and keys
    # there instead only if it ALSO contains illuminated/illumination/moonlit) -- and "moon" already
    # sorted after bird/cat/clock/fire/light, so it never displaces those four either way. Quantified
    # by a real before/after diff over all 4,655 judged_expect rows rather than assumed; see the
    # findings-log entry for the exact counts.
    "illuminated": "moon", "illumination": "moon", "moonlit": "moon",
    "cat": "cat",
    "rain": "wet", "raining": "wet", "wet": "wet", "damp": "wet",
    "wind": "wind", "breeze": "wind",
    "weather": "weather",
    "warm": "warmth", "warmth": "warmth", "cold": "warmth",
    "sound": "sound", "sounds": "sound", "noise": "sound",
    # ── J-1370 (F-1929, 2026-09-26): ADDITIVE extension. The ten entries above resolved no topic for
    # 38% of the Witness's own judged breaks (347/924, deepseek era), so the Phase 1 cup/habituation
    # gate (plan §7.4, D-0241) could never ride on them. Every word below was checked to actually
    # occur in those unresolved break texts before being added (zero-occurrence candidates were
    # dropped); together they cut the unresolved set 347 -> ~48. Three NEW canonical topics (clock,
    # bird, sea) plus synonyms folded into two existing ones (fire, warmth). Note for readers of
    # `_distinct_share_by_topic` / `status()["distinct_expect_share_by_topic"]`: the per-topic
    # denominators change from this commit on — compare like with like across the boundary.
    # `_topic_of()` picks the alphabetically-first canonical match, so a text naming both a new
    # and an old topic ("waves and shingle sounds") now keys on the new, more specific one.
    "clock": "clock", "tick": "clock", "ticking": "clock", "ticks": "clock",
    "bird": "bird", "birds": "bird", "birdsong": "bird", "song": "bird", "call": "bird", "calls": "bird",
    "robin": "bird", "blackbird": "bird", "morepork": "bird", "kingfisher": "bird", "kereru": "bird",
    "tui": "bird", "trill": "bird", "wingbeat": "bird", "wingbeats": "bird", "penguin": "bird",
    "penguins": "bird", "bray": "bird",
    "wave": "sea", "waves": "sea", "shore": "sea", "surf": "sea", "crash": "sea", "sea": "sea",
    "embers": "fire",
    "temperature": "warmth", "cooler": "warmth",
    "footsteps": "sound",
    # ── J-1385 (F-1947, 2026-09-27): ADDITIVE extension, same verified-before-adding discipline and
    # same `illuminated`/`illumination`/`moonlit` exclusions as `_TOPIC_FIELDS` above (see its own
    # comment for the real occurrence counts and the homonym-trap evidence) -- every left-hand key
    # below is one already in `_TOPIC_FIELDS`, same invariant J-1370's own comment states for its
    # entries. Note for readers of `_topic_of()`/`coupling_rides.py`'s Phase 1 cup: the new "light"
    # bucket sorts alphabetically between "fire" and "moon", and "smell" between "sea" and "sound" --
    # so a text naming both a new and an old topic now keys on whichever is alphabetically first, same
    # explicit, accepted "keys on the new, more specific one" consequence J-1370's own comment already
    # names above, not a new risk this job introduces. Checked against the real 4,583-row
    # `judged_expect` corpus (`_topic_of`'s actual production input) before vs. after this change --
    # see the findings-log entry (F-1947 follow-through) for the exact before/after diff counts.
    "light": "light", "lights": "light", "lit": "light", "dim": "light", "dimly": "light",
    "bright": "light", "brightly": "light", "brighter": "light", "brightness": "light",
    "dark": "light", "darker": "light", "darkness": "light",
    "shadow": "light", "shadows": "light",
    "glow": "light", "glowing": "light",
    "smell": "smell", "scent": "smell", "scents": "smell", "briny": "smell",
}


def _topic_of(text: str) -> str | None:
    """Single-string topic match via the same `_TOPIC_CANON` vocabulary `_distinct_share_by_topic`
    below buckets on — for Dosed Coupling Phase 1 (D-0241 shadow-first, J-1161, plan §7.4):
    `core/coupling_rides.py`'s `publish_witness()` calls this against a just-judged prediction's own
    `judged_expect` text to extract the ONE canonical topic that break belongs to, for the per-topic
    habituation gate (`core/lane2_break_habituation.py`) and the would-ride shadow log. Several topic
    words can appear in one prediction's text (rare, but real, e.g. a "the tide will be visible once
    the sun clears the point" phrasing); picks the alphabetically-first canonical match
    deterministically rather than the whole set `_distinct_share_by_topic` returns per-tick, since
    the habituation gate needs exactly one topic to key on, not a set. Returns None on no match — an
    untyped break has no coordinate to consider riding. Pure, no I/O."""
    import re
    toks = set(re.findall(r"[a-z]+", (text or "").lower()))
    topics = {_TOPIC_CANON[t] for t in toks if t in _TOPIC_CANON}
    return sorted(topics)[0] if topics else None


def _distinct_share_by_topic(ticks: list) -> dict:
    """J-0651's actual instrument. Buckets each tick into every canonical topic (`_TOPIC_CANON`
    above) named anywhere in its own `notice`/`uncertain`/`expect_next` text — same three fields,
    same lowercase-word-token scan, as `_invention_check`'s own `said` (reusing that vocabulary and
    method, not inventing a new one) — then reports `distinct_expect_share`'s own formula WITHIN
    each bucket, plus the single most-repeated `expect_next` in that bucket and its share: the
    number F-0926 had to compute by hand with ad hoc regex on notice text because it did not exist
    here. Verified against the live log (2026-09-12, F-0926's own J-0651 follow-through): a topic
    that is nearly universally present every tick (warmth, sound — interoception and ambient sound
    are almost always perceivable at these standpoints) will have `n` close to `len(ticks)` and its
    own distinct-share will read close to the aggregate `distinct_expect_share` almost by
    construction — that is expected, not a bug; read `top_repeat_share` against `n`, the same
    caution `metaphor_judge_coverage`/`coherence_judge_coverage` already model elsewhere in this
    file for a ratio's own denominator. A topic named by only a couple of ticks is reported
    honestly with its own small `n` rather than hidden, padded, or thresholded away."""
    import re
    from collections import Counter
    buckets: dict = {}
    for r in ticks:
        said = " ".join(str(r.get(k) or "") for k in ("notice", "uncertain", "expect_next")).lower()
        toks = set(re.findall(r"[a-z]+", said))
        topics = {_TOPIC_CANON[t] for t in toks if t in _TOPIC_CANON}
        for topic in topics:
            buckets.setdefault(topic, []).append(r.get("expect_next") or "")
    out = {}
    for topic, exps in buckets.items():
        n = len(exps)
        top_text, top_n = Counter(exps).most_common(1)[0]
        out[topic] = {"n": n,
                      "distinct_share": round(len(set(exps)) / n, 3),
                      "top_repeat_share": round(top_n / n, 3),
                      "top_repeat": top_text[:120]}
    return out


def _place_label(place, standpoint) -> str:
    """`[place/standpoint]` — F-1933's own worked example format (2026-09-26, J-1375). Empty when
    neither is known (an older `factual`-tier row recorded before these two fields existed), so a
    legacy entry degrades to plain unlabelled text rather than showing a garbled `[?/?]`."""
    if not place and not standpoint:
        return ""
    return f"[{place or '?'}/{standpoint or '?'}] "


# J-3125 (F-3852, P-0111, 2026-11-06) -- the coherence judge's RECENT RECORD is built from the NEWEST entry backwards
# inside a character budget, whole entries only, then reversed so the prompt still reads "oldest first". Before this the
# last 6 entries were joined oldest-first and the string cut at 600 characters, so the NEWEST record (the one "close
# together in time" matters most for) was wholly beyond the cut on 46 percent of production ticks and cut mid-record on
# 22 percent more (F-3852, 378 ticks since the 10-29 boot; the canary harness's short seeded histories never hit the
# cut). Entries are stored at <= 200 characters plus a ~25 character label, so 1,200 keeps all six on most ticks and
# drops only the oldest whole entries on the longest. `_COHERENCE_NEWEST_FIRST = False` restores the old build exactly
# (600/300 cuts, oldest-first). The sysmsg is untouched. F-3853: the incoherent rate stays dominated by place changes,
# so this fix makes the instrument see the newest record; it does NOT make incoherence_rate a meaningful number.
_COHERENCE_NEWEST_FIRST = True
_COHERENCE_HISTORY_BUDGET = 1200
_COHERENCE_NEW_OBS_CAP = 400


def _cut_at_word(text: str, limit: int) -> str:
    """`text` cut to at most `limit` characters at a word boundary, never mid-word. If the first word alone is longer
    than `limit` it is hard-cut (there is no boundary to use). Pure."""
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if text[limit].isspace():
        return text[:limit].rstrip()
    head = text[:limit]
    cut = max(head.rfind(" "), head.rfind("\n"), head.rfind("\t"))
    return head[:cut].rstrip() if cut > 0 else head


def _coherence_history(recent: list, budget: int | None = None) -> tuple:
    """(history_text, n_whole_entries_dropped). Newest entry first into the budget, whole entries only, then reversed
    so the text reads oldest first, joined by ' / ' as before. If even the NEWEST entry exceeds the budget it alone is
    kept, cut at a word boundary (`_cut_at_word`), never mid-word. Entries with no notice are skipped (as before).
    Pure, no I/O."""
    budget = _COHERENCE_HISTORY_BUDGET if budget is None else budget
    entries = [f"{_place_label(r.get('place'), r.get('standpoint'))}{r.get('notice', '')}"
               for r in recent if r.get("notice")]
    kept: list = []
    used = 0
    for e in reversed(entries):
        cost = len(e) + (3 if kept else 0)          # 3 = len(" / ")
        if used + cost <= budget:
            kept.append(e)
            used += cost
        elif not kept:
            kept.append(_cut_at_word(e, budget))    # the newest alone is too long: keep its start, whole words
            used = budget
            break
        else:
            break
    kept.reverse()
    return " / ".join(kept), len(entries) - len(kept)


def _coherence_moved(store: dict, place, standpoint):
    """J-3126 (F-3853, P-0111, 2026-11-06) -- how the observer's position differs from the NEWEST `factual` store entry,
    the record the coherence judge sees last: 'place' if the place differs, 'standpoint' if only the standpoint differs,
    'same' if both match. None (never 'same') when there is no previous entry, or it lacks either field (an entry from
    before F-1933 carries neither key), or a value is unknown on either side (an unknown place cannot be called a
    move). Pure, no I/O; called BEFORE this tick's entry is appended, so the newest entry is the previous tick's.
    Instrument only: it feeds `status()`'s `incoherence_by_move` split and changes no judge input or verdict."""
    try:
        prev = (store.get("factual") or [None])[-1]
        if not isinstance(prev, dict) or "place" not in prev or "standpoint" not in prev:
            return None
        if None in (prev["place"], prev["standpoint"], place, standpoint):
            return None
        if prev["place"] != place:
            return "place"
        if prev["standpoint"] != standpoint:
            return "standpoint"
        return "same"
    except Exception:
        return None


async def _coherence_check(out: dict, store: dict, percepts: dict | None = None) -> dict:
    """§3.11 / constitutional law 11 (J-0126, 2026-08-24) — a SEPARATE plausibility/coherence pass,
    independent of and downstream from `_grounding_check` (§3.1). F-0017: this did not exist anywhere
    in the module. Grounding asks 'does this trace to a real percept THIS tick'; coherence asks 'does
    it cohere with everything Lane 2 currently holds as grounded' — the guard against vivid-but-wrong
    content that traces to a real, mis-weighted or coincidental percept and gets accepted because it
    FEELS well-evidenced (§2.7, Johnson/Raye's 'systematic-check failure' — a documented clinical
    confabulation mode building only the grounding gate leaves exposed). Decoupled per §2.8e: same
    judge_panel pattern as `_judge_prior`/`_judge_metaphor`, a different model family from the
    generator. Reads ONLY Lane 2's own store (§2.8a) — never Lane 1, never the World Ledger, never the
    world's own ground truth (§2.8b) — a claim is judged against the Witness's own accumulated record
    and nothing else.

    F-1933 (2026-09-26, J-1375): a 22-row hand-read found ~64% of INCOHERENT verdicts were the judge
    blind to WHERE the observer was, not a real contradiction — `recent` used to be bare notice text
    with no standpoint or place, and the standpoint name 'at_the_door' alone names TWO different
    places (the study door, with the fire field present, vs. the garden door, without it), so an
    ordinary move read as a reversal. Both the recent record and the new observation are now labelled
    `[place/standpoint]` (`_place_label` above), and the prompt says a place change alone is not a
    contradiction. The record is deliberately NOT filtered to same-place entries — a real
    contradiction across a move (a fire's warmth, then a minute later a cold fireless room, with
    nothing in between to explain it) must stay catchable; see the finding this job recorded for the
    pre-registered clear-rate this was checked against. `percepts` is an ADDITIVE third argument (kept
    optional so any other caller of this function keeps working unchanged) — `tick()`, the only real
    caller, always passes it now."""
    try:
        from core import judge_panel as _jp
        notice = str(out.get("notice") or "").strip()
        if not notice:
            return {"verdict": "cannot_tell", "how": "empty"}
        percepts = percepts or {}
        recent = [r for r in (store.get("factual") or [])[-6:]]
        # J-3125 (F-3852, P-0111, 2026-11-06): the record is built NEWEST-first inside a character budget
        # (`_coherence_history`) and then shown oldest-first, instead of being joined oldest-first and cut at 600
        # characters from the NEW end (which hid the newest record on about 46 percent of production ticks).
        if _COHERENCE_NEWEST_FIRST:
            history, hist_dropped = _coherence_history(recent)
            hist_cap, obs_cap = _COHERENCE_HISTORY_BUDGET, _COHERENCE_NEW_OBS_CAP
        else:
            history = " / ".join(
                f"{_place_label(r.get('place'), r.get('standpoint'))}{r.get('notice', '')}"
                for r in recent if r.get("notice"))
            hist_dropped, hist_cap, obs_cap = None, 600, 300
        if not history:
            return {"verdict": "cannot_tell", "how": "no-history"}
        cur_place = (percepts.get("world") or {}).get("place")
        cur_standpoint = percepts.get("standpoint")
        new_obs = f"{_place_label(cur_place, cur_standpoint)}{notice}"
        sysmsg = ("You judge whether a NEW observation is PLAUSIBLE given a short RECENT RECORD of "
                  "observations from the SAME observer, close together in time. Each entry (the "
                  "record and the new observation) is labelled [place/standpoint] where known. A "
                  "CHANGE OF PLACE between records is NOT a contradiction by itself — the observer "
                  "may simply have moved there. Flag it implausible only if it flatly CONTRADICTS or "
                  "wildly clashes with the recent record with no plausible transition (e.g. reporting "
                  "a roaring fire when the record has been consistently cold and fireless with no "
                  "mention of it being lit; a sudden reversal of something that does not change that "
                  "fast) — a real contradiction like that can still happen right after a move, so "
                  "weigh the CONTENT, not just whether the place changed. Ordinary, gradual change "
                  "over time is NOT implausible — new detail noticed for the first time is NOT "
                  "implausible. Output ONLY JSON: {\"coherent\": true|false, \"why\": "
                  "\"<one short clause>\"}")
        usr = f"RECENT RECORD (oldest first): {history[:hist_cap]}\n\nNEW OBSERVATION: {new_obs[:obs_cap]}"
        # D-0599 (2) (founder, 2026-11-02; J-3209, built 2026-11-06; F-3744/F-2012): the coherence tiebreak is the
        # lane2 gemma4:12b seat (`_TIEBREAK_LANE2`), as for prediction ("held"/"contradicted") and metaphor, not the
        # shared granite TIEBREAK: JUDGE_1 mixtral said coherent 243 of 245 (pegged), so every "incoherent" (13%) was
        # falcon's dissent upheld by granite, the tiebreak D-0298/J-1581 found unfit on the other Lane 2 keys, and
        # incoherent verdicts reproduce on reask only 33% (F-2012). judge_panel's shared TIEBREAK is untouched.
        d = await _jp.rule_detail(sysmsg, usr, "coherent", context="lane2:coherence",
                                  tiebreak_url=_TIEBREAK_LANE2)
        v = d.get("verdict")
        # J-3127 (F-3854, P-0111, 2026-11-06): ADDITIVE `why` -- the sysmsg now asks for a one-clause reason and the
        # resolved `why` (rule_detail picks the family whose text matches the winning verdict) rides on the result,
        # as `_judge_metaphor` does, so tick() logs it and an incoherent verdict can be audited without re-asking.
        # Before this why1/why2/why3 were empty on 378 of 378 rulings. Nothing reads `why` to act on it.
        res = {"verdict": ("coherent" if v is True else "incoherent" if v is False else "cannot_tell"),
               "how": d.get("how"), "why": d.get("why")}
        if hist_dropped is not None:
            # J-3125: ADDITIVE marker so a reader can split the shadow window before/after the newest-first record
            # (`hist_v` 2) and see how many whole entries the budget dropped on this tick. Old rows carry neither key.
            res["hist_v"] = 2
            res["hist_dropped"] = hist_dropped
        return res
    except Exception as exc:
        logger.debug("[lane2] coherence judge failed (non-fatal): %s", exc)
        return {"verdict": "cannot_tell", "how": "error"}


# D-0342 (2026-10-04, J-1770) — the notice judge's wording, hoisted to a module constant so the regression
# harness (scripts/lane2_notice_judge_regress.py) can swap and replay candidate wordings through the REAL
# `_judge_notice` path. THE TEXT BELOW IS D-0281's ORIGINAL WORDING, UNCHANGED (scripts/
# test_lane2_notice_judge_wording.py pins it byte for byte): J-1770 was asked to sharpen it per D-0342
# ("check every band word, number and quantity the notice names against the listed value") and could NOT
# ship a sharpened wording. Eight candidate wordings were tried (scripts/lane2_notice_judge_candidates.json;
# three replayed through the full real panel path over the 34 originally judged rows, 21 fresh judged rows
# and a planted control, the rest per-judge; findings recorded by J-1770, plan section 8.2): through the
# real panel none flagged the four contradictions the hand-read found (air "cool" at a warm band, moon
# "half-illuminated" at 0.95, a sun "elevation" quoted from an azimuth line, "signs of fatigue" at 0.15)
# without also flagging correct notices, or at all, because the panel's own judges (mixtral:8x7b, falcon3:7b,
# granite3.1-moe:3b tiebreak) either answer true to almost anything or false to almost anything once asked to
# compare values. Follow-up is a /decide (job J-1770's own), not a wording tweak. Do NOT replace this text
# with a candidate wording without re-running the harness and hand-checking every changed row.
_NOTICE_JUDGE_SYSMSG = (
    "You judge whether a short first-person NOTICE actively CONTRADICTS the PERCEPT LINES "
    "it was handed — not whether it is the most precise or complete reading of them, only "
    "whether it states something the percepts make FALSE (e.g. a direction, value, or "
    "state opposite to what is listed, or an event the percepts rule out). A notice that "
    "is vague, incomplete, or merely an imprecise gloss on the percepts — but asserts "
    "nothing they contradict — is NOT a contradiction; flag only genuine falsehood. Output "
    "ONLY JSON: {\"contradicts\": true|false}")


async def _judge_notice(notice: str, percepts: dict) -> dict:
    """§8.2 / D-0281 (2026-09-26) — the claim-correctness instrument §2.7 found missing: predictions are
    judged against what actually arrives (`_judge_prior`, §2.8e), but the NOTICE — what the Witness says
    is here NOW — was checked only lexically (`_grounding_check`'s token overlap, `_invention_check`'s
    absent-field scan), so a notice that names REAL fields and still misreads them sails through
    unchallenged. Live case that motivated this (plan §8.2): "the sun is just beginning its ascent" at
    11:28 with `sun_az` 17° in the payload — grounded (both words are in-payload), not invented (sun_az
    IS present), and simply wrong about what that reading means. Same shape as `_judge_prior` (a
    decoupled `judge_panel` call, percepts in, verdict out) but CONTRADICTION-ONLY wording like the
    §3.11 coherence judge above — asks only whether the notice actively contradicts what it was handed,
    never whether it is the single best or most precise reading, which would flag ordinary imprecision
    as if it were falsehood and make this a pickier grounding check wearing a different name. Sampled by
    the caller (`NOTICE_JUDGE_SAMPLE_P`, D-0281: 1 tick in 4) — this function itself has no opinion on
    sampling, it just judges whatever it's asked to. A scoreboard only (§2.9's own resolution stands: no
    consumer acts on the verdict this returns); see `status()`'s `notice_contradiction_rate`."""
    try:
        from core import judge_panel as _jp
        notice = (notice or "").strip()
        if not notice:
            return {"verdict": "cannot_tell", "how": "empty"}
        obs = percept_lines(percepts)[:600]
        sysmsg = _NOTICE_JUDGE_SYSMSG
        usr = f"PERCEPT LINES: {obs}\n\nNOTICE: {notice[:300]}"
        d = await _jp.rule_detail(sysmsg, usr, "contradicts", context="lane2:notice")
        v = d.get("verdict")
        return {"verdict": ("contradiction" if v is True else "consistent" if v is False else "cannot_tell"),
                "how": d.get("how")}
    except Exception as exc:
        logger.debug("[lane2] notice judge failed (non-fatal): %s", exc)
        return {"verdict": "cannot_tell", "how": "error"}


def _notice_checked(notice: str, percepts: dict) -> dict:
    """D-0361(a) (2026-10-07, J-1896) -- the DETERMINISTIC notice checker, logged per tick as `notice_checked`
    beside `notice_judged` (never inside it, so the panel's own number stays comparable). Pure code from
    `core/lane2_notice_check.py`: maps the notice's band words, decimals-with-units and quantity words to the
    percept line they belong to and compares them with the listed band or number. Why it exists: the panel judge
    reads 0 contradictions in 55 rows while hand-reads find 3-7 of 20 (F-2368, F-2510), and no sharpened wording
    could make the three-model panel do the comparison (F-2509). ZERO panel load (no LLM, no network, no I/O), runs
    on EVERY tick that has a notice (not just the 1-in-4 the panel judge samples; the sampled ticks are the paired
    comparison), draws no random numbers (the 1-in-4 draws above are untouched) and is FAIL-OPEN: any error ->
    {"verdict": "not_checked", "how": "error"} and the tick proceeds. A scoreboard only (plan 2.9): nothing acts on
    it. Compact log shape: the verdict, the flag counts, and at most 4 flags of {kind, said, listed[, weak]}."""
    try:
        from core.lane2_notice_check import check_notice as _cn
        r = _cn(notice, percept_lines(percepts))
        out = {"verdict": r.get("verdict"), "how": r.get("how")}
        if r.get("verdict") == "contradiction":
            out["n_flags"] = r.get("n_flags", 0)
            out["n_solid"] = r.get("n_solid", 0)
            out["flags"] = [{k: v for k, v in f.items() if k in ("kind", "said", "listed", "weak")}
                            for f in (r.get("flags") or [])[:4]]
        return out
    except Exception as exc:
        logger.debug("[lane2] notice checker failed (non-fatal): %s", exc)
        return {"verdict": "not_checked", "how": "error"}


def _notice_unsupported(notice: str, percepts: dict) -> dict:
    """D-0417 (b)->(a) (travis 2026-10-15, J-2102) -- the invention-class instrument, logged per tick as
    `notice_unsupported` BESIDE `notice_checked` (never inside it: D-0342 kept invention out of the value checker).
    Pure code from `core/lane2_notice_unsupported.py`: a closed set of invention-prone nouns (cat, figure, knock,
    shadow, footstep, voice, person, plus clock and fire from F-2732's keyword pass) is looked for in the notice,
    and each one named is checked against the percept lines that can license it (sounds/smells tokens, the fire,
    cat at and clock lines). A scoreboard only: nothing acts on it, LANE2_LIVE untouched, no LLM, no I/O, no random
    draws, FAIL-OPEN ({"flag": False, "how": "error"}). Shape: {flag, nouns, supported_by, negated, how, v}."""
    try:
        from core.lane2_notice_unsupported import check_unsupported as _cu
        return _cu(notice, percept_lines(percepts))
    except Exception as exc:
        logger.debug("[lane2] notice unsupported check failed (non-fatal): %s", exc)
        return {"flag": False, "nouns": [], "how": "error"}


# ── Horizon mis-binning fix (2026-08-22, founder-directed) ──────────────────────────────────────
# Measured over Run 2's first ~19h (447 ticks): broke-rate by horizon was NOT falling as pre-
# registered (next 50% / hour 86% / day 50%) — a spike at 'hour', not a flat or falling curve. Read
# the actual "hour, broke" predictions: nearly all tide/sun/weather content the SYSTEM PROMPT already
# correctly assigns to 'day' ("A tide does not turn in two minutes" — law 4's own clock text at the
# time; see `_NEXT_LOOK_MINUTES` above for why that number since changed) — qwen2.5:7b (the generator)
# just doesn't reliably follow that instruction for this specific topic class. No worked examples
# allowed in the prompt (the double-echo finding above rules that fix out), so this is corrected the
# way this project corrects generator unreliability elsewhere: a cheap, deterministic, LOGGED
# override AFTER generation, never trusting the model's own horizon choice for the one category it's
# now measured to get wrong. Conservative by construction: keyword-only, only ever moves a horizon
# LONGER (next/hour -> day), never shorter, and only for the specific topic class the data implicated
# — it does not invent a new rule, it enforces the prompt's own existing one.
#
# F-1934/J-1376 (2026-09-26) — the override overshot on deepseek: 648 of 800 deepseek-era overrides
# (81%) fired on text that NAMES ITS OWN HORIZON IN MINUTES ("in about two minutes, the sun will be at
# 302.5 degrees"), forced to 'day' anyway, then judged 12h later — 84 of 92 such judged predictions
# BROKE. That is the inverted horizon curve this job was opened to fix (next 0.64 / hour 0.77 / day
# 0.89, where the pre-registration said broke-rate should FALL with horizon). The override was built
# for qwen's vague day-scale phrasing ("the tide will turn within the hour"), which names no clock of
# its own; it was never meant to overrule a model that already named a real, specific, minute-scale
# horizon in its own words. `_MINUTE_SCALE_WORDS` below is the fix: a day-scale topic no longer
# overrides when the text itself says so. F-1962 (same session, addendum to F-1934) also removes
# "shingle" and "swell" from `_DAY_SCALE_TOPICS`: on this shore "shingle" is almost always a SOUND
# token ("waves on the shingle", "shingle drag" — `core/soundscape.py`'s own `_sec_shore`), not the
# tide — 94 of the 800 overrides fired on "shingle" alone with no tide/sun/moon word present, 24 of
# those judged at the day clock, 7 held; "swell" never occurs in deepseek's own predictions at all, so
# removing it is harmless. Both counted in this job's own pre-registration.
_DAY_SCALE_TOPICS = ("tide", "tidal", "sun", "moon", "moonlight", "sunset", "sunrise")
_MINUTE_SCALE_WORDS = ("minute", "next look")   # "minute" substring-matches "minutes"/"minute's" too —
                                                 # same convention _DAY_SCALE_TOPICS's own "tide" already
                                                 # uses to also match "tides".
# F-2336/J-1713 (2026-10-03) — the sibling gap the minute exemption above left open. F-1934 stopped the override
# for MINUTE wording only, so an HOUR-worded claim ("I expect the sun to rise in about an hour", "Within an hour,
# the sun will be at 180 degrees") still came through as 'day' (a 12 h clock) and was judged 12+ hours after a
# claim that named a one-hour window. Since the 2026-09-28 19:08 restart 12 of 12 day-labelled predictions were
# hour-worded (11 of them through this override) and the single judged break in about 49 live hours was one of
# them, scored 13.4 h after a one-hour claim; pre-restart, 151 of 1,000 day-labelled predictions were hour-worded
# beside 818 minute-worded. The fix is the same shape as the minute one: when the text names its own hour-scale
# clock the generator's own label stands. A REGEX, not the bare word "hour": the bare word would also exempt
# "in twelve hours", "hours from now" and "in about two hours" -- multi-hour claims this override is still right
# to move to 'day'. It matches only a singular clock phrase -- "an/a/one/1 hour" (so "half an hour" too), "the
# next hour", "within/in/over/during/inside the hour" -- and not "an hour and a half" / "the next hour or two",
# nor "by the hour" (a rate, not a clock). Candidate patterns were tried against the `expect_next` text of every
# day-labelled tick row in data/lane2_shadow.jsonl (the 1,000 pre-restart plus the 12 post-restart) before this
# one was settled on. Replayed through this function: of the 162 hour-worded texts the day-scale branch used to
# override (11 post-restart, 151 pre-restart), 159 now keep the generator's label (all 11 post-restart); the 3
# that stay overridden are "by the hour" and "in about two hours" / "in about 2 hours".
_HOUR_SCALE_RE = (
    r"\b(?:(?:an?|one|1|next)\s+(?:half[- ])?hour"
    r"|(?:within|in|over|during|inside)\s+the\s+hour)\b"
    r"(?!\s+(?:and\s+a\s+half|or\s+(?:two|three|four|more|longer)))"
)


def _correct_horizon(horizon: str, expect_next: str) -> tuple[str, bool, str]:
    """Returns (corrected_horizon, was_overridden, branch). `branch` names which of the five paths
    fired, so `status()`'s `horizon_overridden_rate` stays exactly what it always measured (the
    day-scale branch's own rate) while the other branches are separately visible via the
    `horizon_override_skipped_minutes` / `horizon_override_skipped_hours` counters:
      · 'already-day'     — the generator already said 'day'; nothing to correct.
      · 'no-match'        — no day-scale topic named at all; nothing to correct.
      · 'skipped-minutes' — a day-scale topic IS named, but the text itself names a minute-scale
                             timeframe (F-1934's own bug: this branch used to override, and broke 84 of
                             92 times it was judged; it now deliberately stands aside instead).
      · 'skipped-hours'   — F-2336/J-1713: a day-scale topic IS named and the text names an hour-scale
                             clock (`_HOUR_SCALE_RE`: "in about an hour", "within the next hour") with no
                             minute wording; the generator's own label is kept, exactly as 'skipped-minutes'
                             keeps it (this branch never invents or upgrades a label). Minute wording is
                             checked first, so 'skipped-minutes' means exactly what it always did.
      · 'day-scale'       — a day-scale topic named with NO minute- or hour-scale wording — the one case
                             this override still corrects: the original 2026-08-22 qwen finding, now only
                             for text that names no sub-day clock at all (or a multi-hour one)."""
    if horizon == "day":
        return horizon, False, "already-day"
    said = (expect_next or "").lower()
    if not any(topic in said for topic in _DAY_SCALE_TOPICS):
        return horizon, False, "no-match"
    if any(word in said for word in _MINUTE_SCALE_WORDS):
        return horizon, False, "skipped-minutes"
    if re.search(_HOUR_SCALE_RE, said):
        return horizon, False, "skipped-hours"
    return "day", True, "day-scale"


# ── Cannot-fail predictions (F-1934/J-1376, 2026-09-26) — cheap lexical flag, no judge call ────────
# Law 4 above now also tells the generator not to predict these; this is the SAME "measure the prompt
# change" convention `_metaphor_flags`/`_invention_check` already use elsewhere in this file — a
# lexical proxy so the law 4 rewrite is falsifiable, not just asserted. F-1934 measured three such
# classes at ~18%/15%/15% of deepseek-era predictions respectively (some overlap, so ~45% combined is
# not a plain sum): 'the clock will tick' (clock), 'will remain/continue/still' (a value simply
# holding), and a bare sun-azimuth figure ('the sun will be at 302.5 degrees') — none of these can
# ever be judged 'broke', so none of them is really a prediction. This job's own pre-registration:
# `status()`'s `trivial_prediction_rate` should fall below 20% from ~45% today, once the rewritten
# law 4 above has had a restart to take effect.
def _trivial_prediction_flag(expect_next: str) -> bool:
    """Scans `expect_next` only (the prediction text itself, not notice/uncertain) — same "cheap
    lexical proxy, honestly labelled" spirit as `_metaphor_flags`/`_invention_check` above, not a
    judge call. Four of the five categories are plain substrings (same convention as
    `_DAY_SCALE_TOPICS`/`_MINUTE_SCALE_WORDS` above); the degree-figure category needs a real regex —
    a bare decimal number is not a fixed word — so this is the one check here that imports `re`."""
    import re
    said = (expect_next or "").lower()
    # "continu" (not "continue"): English drops the trailing 'e' before "-ing" ("continuing"), so the
    # bare word would miss it — same stem-not-word convention `_DAY_SCALE_TOPICS`'s "tide" already
    # uses to also match "tides" above, just needed here because of that one spelling rule.
    if any(w in said for w in ("clock", "remain", "continu", "still")):
        return True
    return bool(re.search(r"\bazimuth\b|\d+\.\d+\s*(?:degrees?|°)", said))


# ── Plan-shaped expectations are not predictions (F-1956, J-1394, 2026-09-27) ───────────────────────
# F-1956's second claim: 75 deepseek-era judged predictions were not claims about the world at all but
# INTENTIONS about the observer's OWN next act -- "I will check if the pathway is clear", "I will be
# able to see if the fire has moved" -- held 0.05, because these can never come true or false in the
# tuple (there is no world-fact for the judge to check against; the panel is really being asked "did
# he do the thing he said he would", a question `_judge_prior` was never built to answer and should
# never be asked). Law 4 above now tells the generator not to produce these (no worked example, same
# echo-risk reasoning as `_SYSTEM`'s own comment). This is the deterministic GENERATION-time backstop,
# same "measure the prompt change, don't just assert it" convention `_trivial_prediction_flag` above
# and `_correct_horizon` use elsewhere in this file -- checked on the freshly generated `expect_next`
# BEFORE it is ever appended to the prediction store (see the store-append guard in `tick()`), so a
# plan-shaped line is kept out of the pending queue entirely rather than generated, waited on for a
# whole horizon, and only then judged broke -- the actual panel call saved (F-1943's own accounting),
# not just a relabelling of the eventual verdict.
_PLAN_SHAPED_RE = r"\bi will (?:check|look|be able|listen|see (?:if|whether)|observe (?:if|whether))\b|\byou will (?:check|see if)\b"


def _plan_shaped_flag(expect_next: str) -> bool:
    """Scans `expect_next` only, same scope as `_trivial_prediction_flag` immediately above (not
    notice/uncertain -- this is specifically about the EXPECTATION being an intention rather than a
    claim). Plain regex against `_PLAN_SHAPED_RE`, not a judge call, same "cheap lexical proxy,
    honestly labelled" spirit as every other instrument in this file: a paraphrase that avoids this
    exact wording (e.g. "the fire's position will be checked by me") is a known, accepted miss, not a
    defect -- the same honest limit `_TOPIC_FIELDS`'s own docstring already states for its own
    vocabulary. `re` imported locally, same convention `_trivial_prediction_flag` above already uses."""
    import re
    return bool(re.search(_PLAN_SHAPED_RE, (expect_next or "").lower()))


# -- Heard-steady-sound predictions are not predictions (F-2932, J-2239, 2026-10-16) ---------------------
# F-2932 (J-2070) read the 10-09..10-16 live window: since 10-12 the study renders 'clock tick' in its
# sounds on 100% of study ticks (240/240), and the generator predicts the tick again on 158 of them.
# Judged, those predictions came back 73 held (every one at a tick that again heard the clock), 37
# unsettled (judge quibbles about duration), 13 unjudgeable, 1 broke (a garden-standpoint artifact) --
# 0 genuine breaks, 20% of all held verdicts, ~124 panel calls a week. A prediction that a sound which
# is ALREADY sounding steadily will sound again cannot fail while he stays put, so it is the same
# cannot-fail class `_trivial_prediction_flag` measures -- but this flag, unlike that one, also GATES the
# store-append in `tick()` exactly the way `expect_is_plan` does (never stored, never judged). It does
# NOT change `_trivial_prediction_flag` or `status()`'s `trivial_prediction_rate` (kept for comparability);
# `trivial_prediction_rate_net` beside it excludes ticks carrying this flag.
# HONESTLY LEXICAL: a small explicit vocabulary, (sound token as core/soundscape.py names it, regex the
# expectation must match to be predicting THAT sound). The expectation side needs the event word itself
# ('tick'/'ticks'/'ticking'/'ticked'), not merely 'clock': F-2932 found 5 rows where 'clock' means the
# horizon ('the clock of the thing is 6 minutes') -- those predict something else and must stay real
# predictions. Known, accepted limits: a compound expectation that also names a second, checkable event
# ('I will hear the rain on the roof and see the clock tick') is flagged whole; a paraphrase without the
# event word ('the clock to ring') is not flagged. Add a sound here only on a finding like F-2932's.
_HEARD_STEADY_SOUNDS = (
    ("clock tick", r"\btick(?:s|ing|ed)?\b"),
)


def _heard_steady_sound_flag(expect_next: str, sounds) -> bool:
    """True when `expect_next` predicts a sound from `_HEARD_STEADY_SOUNDS` AND this tick's own percept
    sounds already name it. `sounds` is the tick's `world['sounds']` list (identifiers like 'clock_tick')
    or an already-rendered sounds line ('waves on shingle, clock tick'); both are normalised the same
    way `percept_lines()` renders them (lower case, underscore -> space). Generation-time, no judge
    call, scans `expect_next` only -- same scope and same local-`re` convention as
    `_plan_shaped_flag` above. No sounds, or no expectation -> False (nothing heard, nothing to drop)."""
    import re
    said = (expect_next or "").lower()
    if not said or not sounds:
        return False
    if isinstance(sounds, (list, tuple)):
        heard = ", ".join(str(x) for x in sounds)
    else:
        heard = str(sounds)
    heard = heard.lower().replace("_", " ")
    return any(tok in heard and re.search(rx, said) for tok, rx in _HEARD_STEADY_SOUNDS)


# ── Judge a prediction only where it was made (F-1958, J-1396, 2026-09-27) ─────────────────────────
# F-1958: matching every deepseek-era judged prediction back to the tick that generated it found the
# SAME-STANDPOINT held rate 0.48 (next 0.50, n=726) against a MOVED held rate of 0.16 (next 0.17,
# n=521; day 0.08, n=91) -- he moves between prediction and judgment on 46% of pairs, and those moved
# pairs supply 58% of every broke verdict this plan has ever reported. The prediction tier stored only
# `{expect, horizon, due_ts, verdict}` (no standpoint, no place), so `_judge_prior` graded "I will hear
# waves on the shingle" against the study's own percepts, and its own 'unsettled means false' rule
# (F-1949) called a changed scene a failed forecast.
# Fix, in two parts: (1) `standpoint`/`place` are now stored on every NEW prediction (additive keys,
# see the store-append in `tick()` below); (2) a due prediction is judged only when THIS tick's own
# standpoint/place matches what was recorded at creation -- otherwise it WAITS (no panel call; this IS
# the actual saving F-1943 asked for) until its own horizon plus one grace tick (`_GRACE_S`) has fully
# elapsed with no match, at which point it closes as `prior_verdict='unjudgeable'`,
# `prior_judged_how='moved'` -- excluded from the broke share exactly like `cannot_tell` (see
# `status()`'s own `broke_share`/`broke_share_same_place`), without ever reaching the panel.
# Day horizon (12h) is the one this job's own briefing flagged as possibly wanting the LOOSER same-
# PLACE rule instead of exact same-standpoint, since its content (sun, moon, weather, tide level from
# the shore) is largely place-independent, not standpoint-specific. The real-data check this job ran
# (dated Current State entry, docs/plans/lane2_the_witness.md) could NOT compare same-place vs same-
# standpoint held rates directly: `place` has been on `rec` since F-1933/J-1375 (2026-09-26), but Du's
# live process has not restarted since before that job landed, so `place` has literally never been
# logged yet (0 of 2,539 deepseek-era ticks carry it, verified live 2026-09-27 against the real
# data/lane2_shadow.jsonl). What the standpoint-only data DOES show: day-horizon predictions already
# sit at a DIFFERENT standpoint than they were made at 76% of the time by pure coincidence today (93
# of 122 matched day pairs, held 0.10 vs 0.21 same-standpoint) -- an exact-standpoint gate would make
# that share WORSE (matching becomes a hard requirement, not a coincidence) and would likely starve the
# day bucket to near-zero real judgments inside its own 6-slot pending cap, a worse failure than the
# one this job exists to fix. PLACE is therefore the chosen default for 'day' -- an INFERRED, not
# verified, choice (see the same dated entry for the full reasoning) -- with a follow-up job spawned to
# re-read same-place vs same-standpoint held rates directly once a restart lets `place` actually accrue
# on judged day pairs.
_GRACE_S = TICK_S   # "horizon plus one grace tick" per this job's own briefing -- named, not a bare
                     # TICK_S reuse, so a reader of `_prediction_judgeability`'s branches below has one
                     # place to look for what "one grace tick" numerically means.


# J-3035 / D-0548 (2026-11-02, F-3741/F-3742, P-0098) -- a next/hour prediction is judged only in the PLACE it
# was made, and never against a world it was not made for. Two additions to the gate below, both closing
# as the existing `unjudgeable` verdict without a panel call:
#   (1) PLACE equality for next/hour as well as standpoint equality ('at_the_door' names both the study
#       door and the garden door, F-1933; the 10-30 01:48 warmth break was made in the garden and judged in
#       the study, 0.32 vs 0.39). A place mismatch WAITS and then closes 'expired-moved' exactly like a
#       standpoint mismatch always did.
#   (2) 'expired-stale': a prediction is closed unjudgeable (`how="expired-stale"`) when it is judged later
#       than `_STALE_AFTER_S` past its due time (2 grace ticks), or, for a next/hour prediction, when Du
#       was asleep at any tick between its creation and now (the 11-01 clock break: made 23:24, he slept
#       23:29 to 00:04, judged 2,434 s later against the clock at 00:04). The day horizon is exempt from
#       the asleep rule only (a 12 h wait spans a night by design); it still obeys the age bound.
# MEASURED COST, read before retuning: on the live log since 10-26, 34-50 percent of 'next' predictions were
# judged more than 600 s past due on a given day, so the age bound will close a large share of what used to
# be judged as unjudgeable-stale. That is the ruling's intent ("expire stale ones"); `status()` carries
# `unjudgeable_stale_24h` so the volume change is read, and `_STALE_AFTER_S` is the one number to retune.
_STALE_AFTER_S = 2 * _GRACE_S
# J-3160 / D-0548: trivial predictions (`_trivial_prediction_flag`) are not stored. A named switch, not a
# bare edit, so reverting is one line; the ruling (Travis 2026-11-02) is to exclude, so the default is on.
TRIVIAL_PREDICTION_EXCLUDED = True
_LAST_ASLEEP_TS = 0.0     # in-memory: the last tick that found Du asleep (set in `tick()`); 0.0 = none this run


def _prediction_judgeability(rec: dict, now: float, cur_standpoint, cur_place,
                             last_asleep_ts: float | None = None) -> str:
    """Returns one of 'matched-standpoint' | 'matched-place' | 'matched-legacy' | 'waiting' |
    'expired-moved' | 'expired-stale'. `rec` is the DUE prediction's own store record -- its `standpoint`/
    `place` are whatever was recorded when it was CREATED (the store-append in `tick()` below), never
    this tick's own. 'day' horizon uses the looser same-PLACE rule; 'next'/'hour' require the exact same
    standpoint AND (J-3035) the same place when the record carries one (see the module comment
    immediately above for why). A record with no recorded standpoint/place at all -- created before
    F-1958/J-1396 shipped, since both fields are additive -- cannot be told moved from stayed, so it
    matches permissively ('matched-legacy') rather than manufacturing an `unjudgeable` verdict for
    something the old code never flagged as wrong; a record with a standpoint but no place is matched on
    the standpoint alone, as before. 'expired-stale' (J-3035) is checked FIRST and wins over a match.
    `last_asleep_ts` is the last tick that found Du asleep (None/0 = unknown). Pure, no I/O,
    deterministic given `now` -- called from `tick()` and replayed directly in this job's own tests
    against the real rows quoted in F-3741/F-3742."""
    horizon = rec.get("horizon")
    due_ts = float(rec.get("due_ts") or 0)
    if due_ts and now > due_ts + _STALE_AFTER_S:
        return "expired-stale"
    if (horizon != "day" and last_asleep_ts and rec.get("ts") is not None
            and float(rec["ts"]) < float(last_asleep_ts) <= now and now > due_ts):
        return "expired-stale"
    if horizon == "day":
        rec_place = rec.get("place")
        if rec_place is None:
            return "matched-legacy"
        if rec_place == cur_place:
            return "matched-place"
    else:
        rec_standpoint = rec.get("standpoint")
        if rec_standpoint is None:
            return "matched-legacy"
        rec_place = rec.get("place")
        if rec_standpoint == cur_standpoint and (rec_place is None or rec_place == cur_place):
            return "matched-standpoint"
    return "expired-moved" if now > due_ts + _GRACE_S else "waiting"


# ── Unjudgeable: the named thing isn't here right now either (F-1956, J-1394, 2026-09-27) ──────────
# F-1956 (verified, over the 823 deepseek-era judged predictions that name a `_TOPIC_FIELDS` topic at
# all): 147 of them (18%) were judged on a tick where NONE of that topic's own mapped fields had
# crossed into `world_fields` -- held 0.05 there vs 0.33 when the field WAS present. `_SYSTEM`'s own
# law 1 says a fact not listed is UNKNOWN, not absent from the world, and `_judge_prior`'s own prompt
# says "if the observation does not settle it either way, answer false" (F-1949) -- so "I can no longer
# see the fire" was being read back as "the fire prediction did not come true", not as the genuinely
# unjudgeable case it actually is.
# F-1958 found that MOST of this is the SAME root cause `_prediction_judgeability` above already fixes
# (the field is absent because he moved) and named that gate the PRIMARY judgeability rule for this
# job, this check a secondary one -- so this function is deliberately called from `tick()` ONLY once
# `_prediction_judgeability` has already returned a matched-* verdict (see its own call site): a due
# prediction that has not even matched place/standpoint yet is already correctly headed to
# 'waiting'/'expired-moved' by the untouched logic above, and this second gate would either be
# redundant there or would misattribute an already-explained non-match to the wrong cause. Reuses
# `_GRACE_S`/`due_ts` exactly as `_prediction_judgeability` already does for its own grace window --
# "one extra tick" (this job's own briefing) means precisely what it already means one gate up; no
# second grace constant invented. See `tick()`'s own call site for exactly how the two gates combine
# into `due_judgeable`/`due_expired`/the new `prior_judged_how='field-absent'` value.
def _prediction_field_ok(expect: str, percepts: dict) -> bool:
    """Resolves `expect`'s own `_TOPIC_FIELDS` topics (identical tokenizer to `_invention_check`/
    `_wonder_percept_anchored` above -- lower-cased `[a-z]+` tokens) and requires at least one of them
    to have a mapped field present in THIS tick's `world_fields`. Naming ZERO `_TOPIC_FIELDS` topics at
    all reads as judgeable (True) -- fail-open, the exact "an unmapped topic is silently not checked,
    never guessed at" convention `_TOPIC_FIELDS`'s own docstring already states; F-1956's own 823-row
    population was already restricted to predictions naming a real topic, and this job's own
    pre-registration (broke share falls by roughly the share these represent) only holds if every OTHER
    prediction is left untouched. Returns False only when a topic WAS named and every one of its own
    mapped fields is absent. Pure, no I/O; replayed directly in this job's own isolation check against
    the real historical (present/absent) pairs (`scratchpad/check_J-1394_replay.py`)."""
    import re
    present = set(percepts.get("world_fields") or [])
    toks = set(re.findall(r"[a-z]+", (expect or "").lower()))
    named = {t for t in toks if t in _TOPIC_FIELDS}
    if not named:
        return True
    if any(f in present for t in named for f in _TOPIC_FIELDS[t]):
        return True
    # D-0433 option B (J-2176, F-2701/J-2081): at night/dusk/dawn `sun_az` never exists (0/426 ticks), so
    # every sun-family claim was field-absent -> unjudgeable, although the same tick carries the payload's
    # own `world["daylight"]` phase, which the panel sees and which settles most such claims. For
    # `_SUN_TOPICS` ONLY, a non-empty daylight phase counts as a mapped field. A missing/blank daylight is
    # still field-absent. Moon etc. unchanged.
    if named & _SUN_TOPICS:
        if str((percepts.get("world") or {}).get("daylight") or "").strip():
            return True
    return False


def _due_prediction(store: dict, now: float) -> dict | None:
    """The OLDEST prediction whose horizon has elapsed and which is not yet judged. One per tick — the
    judge is a panel call on the SPOF; it must never become a backlog. Unchanged by F-1958/J-1396: this
    still just finds the oldest due-and-unverdicted candidate — `tick()` is what decides, via
    `_prediction_judgeability` above, whether THIS tick is actually allowed to judge it."""
    for rec in store.get("prediction") or []:
        if rec.get("verdict") is None and float(rec.get("due_ts") or 0) <= now:
            return rec
    return None


# ── §2.8c's MIDDLE tier — KNOWLEDGE (D-0285, 2026-09-27, F-1942) ────────────────────────────────────
# F-1942 (verified): this tier never existed. `store` held only `factual`/`prediction`, so every
# prediction was generated from ONE tick's own percepts with nothing accumulated — the plan's own
# words for what this tier should be, never built: "the fire is usually lit by evening", a
# generalization "earned by repetition, never handed over" (§2.8c's table). D-0285 ruled option (a):
# build it, SHADOW-FIRST, no LLM call — a deterministic consolidation over Lane 2's OWN records only
# (§2.8b: never the world's truth — nothing here ever reads `world_geometry`/`world_objects`/
# `causal_state`, only the RENDERED percept fields Lane 2 itself already logged; never Lane 1's
# memory — the only input is `_LOG`, Lane 2's own shadow log, built first-hand at the moment of
# perceiving, exactly like `store['factual']`/`store['prediction']` already are per §2.8a).
#
# Two regularity KINDS, both keyed on the SAME (topic, place, daylight) triple the ruling names —
# D-0285's own two worked examples are one of each:
#   "field_presence" — of ticks AT this place, in this daylight phase, how often was this topic's
#       own world_fields entry actually present ("...the fire field is present 82% of ticks"). Reuses
#       `_TOPIC_FIELDS`/`_TOPIC_CANON` verbatim, zero new vocabulary (§2.8d) — see
#       `_canon_topic_fields()` just below for exactly which canonical topics are eligible (only the
#       ones that map to a real world_fields name; `clock`/`bird`/`sea` correctly never qualify here,
#       the same "checked and excluded, not silently guessed at" honesty this file's vocabulary
#       comments already model elsewhere).
#   "prediction_hold" — of predictions ABOUT this topic MADE at this place in this daylight phase and
#       since JUDGED held/broke (cannot_tell/unsettled/unjudgeable/none excluded — the exact same
#       convention `broke_share`/`broke_share_strict` in `status()` already use), what share held
#       ("sound predictions at the shore hold 41%"). Topic comes from `_topic_of(judged_expect)` (the
#       same matcher Dosed Coupling's own Phase 1 cup already uses, §7.4); place/daylight come from
#       WHERE/WHEN the prediction was CREATED (`judged_pred_place`/`judged_pred_daylight`, both on
#       `rec` — see `tick()` below), never this tick's own, since the claim being scored is about
#       that earlier moment, not the moment it happened to get judged (the same "judge a prediction
#       only where it was made" principle F-1958/J-1396 already established one job before this one).
#
# `daylight` itself is a NEW top-level `rec` field this job adds (identical computation
# `_daylight_word_slip_check` already uses live: `(percepts.get("world") or {}).get("daylight")`) —
# additive, mirrors exactly how J-1375 added `standpoint`/`place` to `rec` for the same downstream-
# consolidation reason. Every row logged before Du's next restart carries neither `daylight` nor
# `judged_pred_daylight`, so it is silently excluded from both bucketings below — an honest gap, the
# same backward-compat convention `gen_s`/`percept_lines`/`standpoint`/`place` already modelled here
# when each was added, never guessed at and never backfilled.
def _canon_topic_fields() -> dict:
    """Canonical-topic -> the set of world_fields NAME(S) that topic actually means, built ONCE from
    the two vocabularies this file already owns (`_TOPIC_FIELDS`, `_TOPIC_CANON`) rather than a third
    copy of the same words — §2.8d's "no new vocabulary invented" applied to the knowledge tier too.
    Only a canonical topic that maps to a REAL percept field is eligible for `field_presence`: a
    canonical topic Lane 2 can only ever NAME (e.g. `clock`, `bird`, `sea` — J-1370's own additions,
    which fold several English words into a topic with no single corresponding `world_fields` entry)
    is correctly absent from the returned dict, not silently mapped to the wrong thing. Pure, no I/O,
    deterministic; safe to call every tick (12 short dict operations, not a hot loop concern)."""
    out: dict = {}
    for word, fields in _TOPIC_FIELDS.items():
        canon = _TOPIC_CANON.get(word, word)
        out.setdefault(canon, set()).update(fields)
    return out


def _consolidate_knowledge(store: dict) -> list:
    """§2.8c's middle tier (D-0285) — deterministic, no LLM call, over Lane 2's OWN shadow log only.
    Reads the SAME bounded tail `status()` already reads (`tail_rows(_LOG, 2000)` — at TICK_S=300
    that is ~6.9 days, close to the ruling's own "after 7 days of shadow" horizon by construction, not
    a fresh unbounded scan of the whole growing log — the exact antipattern F-0335 already fixed once
    in `status()`; reusing its bound here rather than inventing a second one).

    Returns up to KNOWLEDGE_CAP regularities, HALF reserved for each kind (see this job's own
    isolation testing, `check_J-1414.py`): `field_presence`'s own `n` is a tick COUNT at a
    (place, daylight) pair, shared identically across all 12 canonical topics there (every topic is
    counted on every such tick, present or not — the ruling's own denominator, "of ticks..."), so it
    is structurally much larger than `prediction_hold`'s own `n` (only ticks with an actual JUDGED,
    topic-resolvable, same-place-and-daylight prediction). Ranking the two kinds in one pooled list
    by raw `n` would let one busy (place, daylight) pair's 12 field_presence rows fill the entire cap
    and permanently crowd out every prediction_hold regularity — silently dropping half of what the
    ruling's own two worked examples ("...fire field is present 82%..." AND "...sound predictions...
    hold 41%") say this tier should hold. A flat 50/50 split is the smallest fix that does not change
    either kind's own semantics or denominator. Within each half: ranked by evidence count `n`
    descending (§2.8c: "earned by repetition"), ties broken deterministically (topic, place,
    daylight) so two consecutive calls over an unchanged log always return byte-identical output.
    Returning fewer than KNOWLEDGE_CAP when one kind has little evidence yet is honest, not a bug —
    this tier never pads a thin regularity in just to hit a target count.

    Fails open like every other source in this file: if the log cannot be read, or has no tick rows
    yet, returns the store's OWN existing `knowledge` list unchanged (never wipes accumulated
    evidence just because one read had a hiccup) rather than an empty list."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
    except Exception:
        return list(store.get("knowledge") or [])
    try:
        rows = _tail_rows(_LOG, 2000)
    except Exception:
        return list(store.get("knowledge") or [])
    ticks = [r for r in rows if r.get("kind") == "tick"]
    if not ticks:
        return list(store.get("knowledge") or [])

    canon_fields = _canon_topic_fields()
    presence: dict = {}      # (topic, place, daylight) -> [n, present_n]
    for r in ticks:
        place, daylight = r.get("place"), r.get("daylight")
        if not place or not daylight:
            continue         # honest gap (pre-restart row, or a tick the world never rendered either
                              # for) — never guessed at, same fail-open convention this whole file uses
        present = set(r.get("world_fields") or [])
        for topic, fields in canon_fields.items():
            key = (topic, place, daylight)
            n, present_n = presence.get(key, (0, 0))
            presence[key] = (n + 1, present_n + (1 if fields & present else 0))

    holds: dict = {}          # (topic, place, daylight) -> [n, held_n]
    for r in ticks:
        verdict = r.get("prior_verdict")
        if verdict not in ("held", "broke"):
            continue         # cannot_tell/unsettled/unjudgeable/none excluded — see this section's
                              # own header comment for why (same convention `broke_share` already uses)
        place, daylight = r.get("judged_pred_place"), r.get("judged_pred_daylight")
        topic = _topic_of(r.get("judged_expect") or "")
        if not (place and daylight and topic):
            continue
        key = (topic, place, daylight)
        n, held_n = holds.get(key, (0, 0))
        holds[key] = (n + 1, held_n + (1 if verdict == "held" else 0))

    presence_regs = sorted(
        ({"kind": "field_presence", "topic": t, "place": p, "daylight": d,
          "rate": round(pn / n, 3), "n": n} for (t, p, d), (n, pn) in presence.items()),
        key=lambda k: (-k["n"], k["topic"], k["place"], k["daylight"]))
    hold_regs = sorted(
        ({"kind": "prediction_hold", "topic": t, "place": p, "daylight": d,
          "rate": round(hn / n, 3), "n": n} for (t, p, d), (n, hn) in holds.items()),
        key=lambda k: (-k["n"], k["topic"], k["place"], k["daylight"]))
    half = KNOWLEDGE_CAP // 2
    return presence_regs[:half] + hold_regs[:KNOWLEDGE_CAP - half]


def _knowledge_would_show(knowledge: list, place, daylight, limit: int = 3) -> list:
    """Step 3 (SHADOW-ONLY, D-0285): which of the top-KNOWLEDGE_CAP regularities are relevant to THIS
    tick's own place/phase — logged so a future read can ask "would this have been worth showing"
    before step 4 (a SEPARATE, later, restart-gated job per the ruling's own text) ever lets one reach
    `percept_lines()`/`_ask()`. Nothing this function returns is added to the generator's payload
    anywhere in this file — it is read back only from the shadow log, by a human or a future job.
    Typed lines, not prose (the one-space trap — `docs/plans/cognitive_geometry.md` §4, restated for
    prompts in `docs/staged/dosed_coupling.md`: "a coordinate never becomes a sentence in a prompt
    where the number will do"): each line names the tuple and the number, never a narrated sentence.
    Capped at `limit` (3 — the ruling's own number for the eventual live step) even though this never
    reaches the prompt yet, so the eventual flip does not have to redesign this part at all."""
    matches = [k for k in (knowledge or []) if k.get("place") == place and k.get("daylight") == daylight]
    matches.sort(key=lambda k: -k["n"])
    lines = []
    for k in matches[:limit]:
        verb = "present" if k["kind"] == "field_presence" else "held"
        lines.append(f"KNOWN {k['topic']}@{k['place']}/{k['daylight']} {verb}={k['rate']} n={k['n']}")
    return lines


async def tick() -> dict | None:
    """One standing-loop tick. The text (notice/expect_next) is shadow-only and reaches nothing; the verdict coordinate is live (D-0497). Never raises.

    D-0303 (2026-09-28, F-2022/F-2021) — gated off entirely while Du is asleep, checked FIRST so a
    sleeping tick costs nothing (no percept gather, no judge-panel calls). F-2022 (verified) found
    543/1,457 real judged ticks over 14 days (37.3%) landed inside a sleep episode -- ~1,629 panel
    calls judging a materially static bedroom scene, landing on the same JUDGE_1 hub (:11438) D-0297
    already found timing out overnight against dream generation. F-2021 (verified) separately found
    Lane 1's hint channel never nominates a Witness topic from dream content during sleep (0/578
    hint_pushed events fell inside a sleep episode in the same window) -- so this silences no real
    Lane-1-to-Lane-2 signal, only the Witness's own unprompted narration of an unchanging room.
    Applies to BOTH night and nap (the founder's ruling text, D-0303, is a blanket gate-off, not a
    night-only one): `core.night.asleep()` needs no kind filter for that -- confirmed by reading
    night.py itself, not assumed. `asleep()` is a plain `bool(sensorium.state.get("asleep"))` read
    with zero kind branching, and its own single real setter, `to_bed()`, is called unconditionally
    from the ONE call site that ever calls it (`inner_monologue_node._enter_sleep`, which runs for
    every sleep cycle `sleep_pressure.should_sleep()` fires, before `night.sleep_kind()`'s own
    night-vs-nap label is even consulted anywhere downstream) -- so `asleep()` already reads True for
    a nap exactly as it does for a full night, by construction, with no separate branch needed here.
    "Resume promptly on wake" needs no new poll mechanism, and deliberately does not build one (see
    night.py's own module docstring on `tick()`/`stage()`: the sleep pipeline's synchronous stages
    can starve the asyncio scheduler of a turn for its own full 900-5400s span, per J-1075/F-1469/
    F-1421) -- the EXISTING `run_forever()` loop's own `await asyncio.sleep(TICK_S)` already fires on
    the very next scheduler turn the event loop gets back after that blocking pipeline returns to its
    caller, because `wake()` (night.py stage 13, the pipeline's own LAST stage) flips this flag False
    before the pipeline ever yields control back -- so the very first tick to run post-freeze already
    reads correctly, at the same TICK_S cadence this loop always had; inventing a separate, faster
    poll here would not actually run any sooner, since nothing runs sooner than the frozen scheduler
    allows. Fail-open in the same direction as the one other real caller of this check in this
    codebase (`core/dispatch.py`'s own `if _night.asleep(): return out`): if the check itself ever
    raises, fall through and tick normally rather than risk the shadow log going silently dark."""
    global _LAST_ASLEEP_TS
    try:
        try:
            from core import night as _night
            if _night.asleep():
                _LAST_ASLEEP_TS = time.time()     # J-3035: lets `_prediction_judgeability` see a sleep inside a wait
                _skip("asleep")
                return None
        except Exception:
            pass
        percepts = gather_percepts()
        if not percepts.get("available"):
            _skip("no-percepts", missing=percepts.get("missing"))
            return None

        now = time.time()
        store = _load_store()
        due = _due_prediction(store, now)
        # F-1958/J-1396 (2026-09-27) — judge a prediction only where it was made; see
        # `_prediction_judgeability`'s own docstring (just above `_due_prediction`) for the rule.
        # `due_judgeable` is the only case that still reaches the panel this tick; a due prediction
        # still WAITING for its own standpoint/place to come back skips the panel silently (left
        # untouched in the store, reconsidered next tick), and one whose grace has now expired closes
        # as `due_expired` WITHOUT ever calling the panel either.
        judgeability = (_prediction_judgeability(due, now, percepts.get("standpoint"),
                                                  (percepts.get("world") or {}).get("place"),
                                                  _LAST_ASLEEP_TS)
                         if due else None)
        matched = judgeability in ("matched-standpoint", "matched-place", "matched-legacy")
        # F-1956/J-1394 (2026-09-27) — the SECOND, additive gate: see `_prediction_field_ok`'s own
        # docstring (just above `_due_prediction`) for why it is checked only once the place/standpoint
        # gate above has already matched, and why it reuses `_GRACE_S`. `field_ok` is left True (a
        # no-op default) whenever there is nothing to gate (`due` is None) or the gate above has not
        # matched — that branch is already fully handled by `judgeability == "expired-moved"`/"waiting"
        # below, untouched from before this job.
        field_ok = _prediction_field_ok(due["expect"], percepts) if (due and matched) else True
        grace_expired = due is not None and now > float(due.get("due_ts") or 0) + _GRACE_S
        if matched and field_ok:
            due_judgeable, due_expired, expired_how = due, None, None
        elif judgeability == "expired-moved":
            due_judgeable, due_expired, expired_how = None, due, "moved"
        elif judgeability == "expired-stale":
            # J-3035 / D-0548 -- too old, or slept through; closed WITHOUT a panel call (see the module
            # comment above `_STALE_AFTER_S`). Checked before field-absent: a stale prediction must not be
            # judged or held for a field, whatever the field says.
            due_judgeable, due_expired, expired_how = None, due, "expired-stale"
        elif matched and not field_ok and grace_expired:
            due_judgeable, due_expired, expired_how = None, due, "field-absent"
        else:
            due_judgeable, due_expired, expired_how = None, None, None
        if due and due_judgeable is None and due_expired is None:
            # F-1956/J-1394 — a distinct skip reason from the place/standpoint "prediction-waiting"
            # below (real diagnostic value: `status()`'s `skips` dict now shows the two causes
            # separately), same additive-not-replacing spirit as everything else this job adds.
            _skip("prediction-waiting-field" if (matched and not field_ok) else "prediction-waiting",
                  expect=str(due.get("expect") or "")[:80], horizon=due.get("horizon"))
        weather = read_weather()
        gain = weather_to_gain(weather)
        # §2.5 point 2 (J-0165) — samples AT MOST ONE hint this tick, already re-checked live
        # against THIS tick's own percepts (law 4b). None most ticks: the queue is small, rate-
        # limited, and only ever holds what Lane 1 actually pushed.
        hint = _consume_hint(percepts, now)

        # NOTE: the prior expectation is deliberately NOT shown to the generator — see the double-echo
        # note above. It goes to the decoupled judge instead, concurrently (different hosts, no wall-time).
        # J-1709 (F-2331/F-2332) -- the payload text is held in a local (same expression, same evaluation order,
        # same string handed to `_ask`) so the no-output branch below can log exactly what was sent.
        _percept_text = percept_lines(percepts)
        _hint_text = hint_line(hint)
        # J-3965 / D-0429(b): wonder avoid-list, A/B armed, fail-open (see `wonder_avoid_terms`).
        _avoid_arm, _avoid_terms, _avoid_text = False, [], ""
        try:
            if WONDER_AVOID_LIST:
                import random as _random
                _avoid_arm = _random.random() < WONDER_AVOID_ARM_FRAC
                if _avoid_arm:
                    _avoid_terms = wonder_avoid_terms(_percept_text, _wonder_recent_rows(), now)
                    _avoid_text = wonder_avoid_line(_avoid_terms)
        except Exception:
            _avoid_arm, _avoid_terms, _avoid_text = False, [], ""
        _ask_payload = _percept_text + _hint_text + _avoid_text
        gen_task = _ask_with_retry(_ask_payload, _retry_payload(_percept_text, _hint_text + _avoid_text))   # J-2164 / D-0414(b)
        if due_judgeable:
            (out, gen_s, cause), judged = await asyncio.gather(
                gen_task, _judge_prior(due_judgeable["expect"], percepts,
                                       age_s=_prediction_age_s(due_judgeable, now),     # J-3099 (flag-gated inside)
                                       horizon=due_judgeable.get("horizon"),
                                       pred_place=due_judgeable.get("place")))
        elif due_expired:
            # F-1958/J-1396 — closed WITHOUT ever calling the judge panel; this call NOT made is the
            # actual saving F-1943 asked for, not just a relabelling of the old verdict. `expired_how`
            # is "moved" (J-1396, unchanged) or "field-absent" (F-1956/J-1394, additive — see the
            # branch above that sets it).
            out, gen_s, cause = await gen_task
            judged = {"verdict": "unjudgeable", "how": expired_how, "why": None,
                      "contradicted_how": None, "contradicted_why": None}
        else:
            out, gen_s, cause = await gen_task
            judged = {"verdict": "none", "how": None}
        _retry_fields = _consume_retry()      # J-2164: retried / retry_variant / retry_cause / retry_gen_s

        # F-1958/J-1396 — `due_resolved` is whichever of `due_judgeable`/`due_expired` actually fired
        # this tick (never both; see the branch above). A `due` that is merely WAITING is deliberately
        # excluded here and below: it must stay untouched in the store (verdict still None) so it is
        # reconsidered next tick, exactly as if this tick had found no due prediction at all.
        # J-1672 (F-2243) — moved UP from just-before-`rec` (where J-1396 first placed it, unchanged
        # until this job) to HERE, right after `judged` is final and BEFORE the no-output check right
        # below: `judged` is already complete regardless of THIS tick's own generation outcome (it
        # comes from `_judge_prior`/the local `due_expired` synthesis above, never from `out`), so
        # computing it any later was silently discarding a real, already-paid-for judge-panel verdict
        # — possibly a costly TIEBREAK escalation — on every tick where generation failed but judging
        # succeeded in the same `asyncio.gather` (F-2243's own 56-vs-30 held/tiebreak row gap). Still
        # a live reference into `store['prediction']`, not a copy (see `_due_prediction`'s own
        # docstring), so this still just mutates that entry in place; only the matching SAVE of that
        # mutation is new, and only on the branch below where it would otherwise never happen.
        due_resolved = due_judgeable if due_judgeable is not None else due_expired
        judge_retry_now = False
        if due_resolved:
            if judged.get("verdict") == "retry":
                # J-3100 / F-3818: first timeout leaves the prediction OPEN for one re-ask on a later tick (the
                # existing waiting path); a second one closes as cannot_tell exactly as it did before this job.
                if int(due_resolved.get("judge_retries") or 0) >= JUDGE_RETRY_MAX:
                    judged = dict(judged, verdict="cannot_tell")
                else:
                    judge_retry_now = True
            if judge_retry_now:
                due_resolved["judge_retries"] = int(due_resolved.get("judge_retries") or 0) + 1
                due_resolved["judge_retry_ts"] = round(now, 1)     # verdict / judged_ts / judged_how stay unset
            else:
                due_resolved["verdict"] = judged.get("verdict", "cannot_tell")
                due_resolved["judged_ts"] = round(now, 1)
                due_resolved["judged_how"] = judged.get("how")

        if not out or not isinstance(out, dict):
            # F-1937/J-1379 — `cause` (see `_ask`'s own docstring: "timeout"/"http"/"parse"/
            # "exception") and `elapsed_s` (the same `gen_s` wall-time `_ask` already timed, under a
            # skip-row-scoped name since a `skip` row has never carried a bare `gen_s` key before)
            # ride along on every no-output skip now, so `status()`'s new `no_output_by_cause_24h`
            # can attribute the 19%-of-ticks figure instead of leaving it a single undifferentiated
            # bucket. `had_percepts` is unchanged from before this job.
            # J-1672 (F-2243) — `due_resolved` above may already hold a real verdict even though this
            # tick's own generation failed; the success path's `_save_store`/`_log(rec)` below are
            # both unreached from here (this `return None` fires first), so save it now — the one
            # targeted save this branch ever needs — and mirror the SAME field names the "tick" row
            # already uses (`judged_expect`/`prior_verdict`/`prior_judged_how`) onto this skip row, so
            # a gen-failed-but-judged tick stays auditable from lane2_shadow.jsonl alone instead of
            # vanishing from it. Every no-output row with no due prediction in play is unchanged byte
            # for byte: these three keys are added only when `due_resolved` is truthy.
            detail = {"cause": cause, "elapsed_s": gen_s, "had_percepts": percepts.get("available")}
            # F-2331/F-2332 (J-1709) -- ADDITIVE failure evidence, observability only: `cause` can now also be
            # "empty" (a reply that parsed to `{}`, see `_ask`'s docstring), and for cause empty / parse / timeout
            # the row also carries the payload actually sent plus, for empty / parse, a bounded sample of the raw
            # reply (see `_failure_evidence`). No existing key is renamed or removed, `_failure_evidence` never
            # raises, and nothing here changes what the tick does next. http / exception rows stay byte-identical.
            detail.update(_failure_evidence(cause, _ask_payload))
            detail.update(_retry_fields)          # J-2164 (D-0414 b): a retry that also came back empty is logged here
            if due_resolved:
                _save_store(store)
                detail["judged_expect"] = due_resolved.get("expect")
                detail["prior_verdict"] = "retry" if judge_retry_now else due_resolved.get("verdict")
                detail["prior_judged_how"] = judged.get("how") if judge_retry_now else due_resolved.get("judged_how")
                if due_resolved.get("judge_retries"):
                    detail["prior_judge_retries"] = due_resolved.get("judge_retries")     # J-3100: only when a retry exists
                # J-2076 (F-2689) -- ADDITIVE. Same field names the "tick" row carries, so a verdict that
                # landed on a no-output skip row is hand-checkable and `status()`'s `broke_share_strict`
                # (keyed on `prior_contradicted_how`) does not silently drop a broke on a skip row.
                # `percept_lines` is the JUDGING tick's own rendering (what `_judge_prior` was shown);
                # all values come from `judged`/`due_resolved`/`judgeability`, already in hand.
                detail["prior_judged_why"] = judged.get("why")
                detail["prior_contradicted_how"] = judged.get("contradicted_how")
                detail["prior_contradicted_why"] = judged.get("contradicted_why")
                detail["prior_judgeability"] = judgeability
                # J-3160 (D-0548) -- ADDITIVE: where/how the judged prediction was made, so the cup artefact
                # test (`cup_artefact_report`) can read a break that landed on a no-output skip row exactly as
                # it reads one on a tick row. Same names the "tick" row carries.
                detail["judged_horizon"] = due_resolved.get("horizon")
                detail["judged_pred_standpoint"] = due_resolved.get("standpoint")
                detail["judged_pred_place"] = due_resolved.get("place")
                try:
                    detail["judged_age_s"] = round(now - float(due_resolved["ts"]), 1)
                except Exception:
                    detail["judged_age_s"] = None
                try:
                    detail["percept_lines"] = percept_lines(percepts)[:600]
                except Exception:
                    detail["percept_lines"] = None
            _skip("no-output", **detail)
            return None

        # J-0126 (2026-08-24) — the two missing §5 guard-passes, run concurrently (separate hosts,
        # no added wall-time beyond the slower of the two): the decoupled metaphor judge (metric #1's
        # actual pre-registered instrument, replacing the keyword scan as the metric of record — F-0016)
        # and the §3.11 coherence pass (metric #8's prerequisite — F-0017, law 11).
        # D-0281 (2026-09-26, §8.2) — the notice's own claim-correctness judge, SAMPLED (not every
        # tick, per the ruled panel-load budget): only added to this same gather on a sampled tick, so
        # the other 3-in-4 ticks pay none of its extra queueing cost on the shared judge_panel hubs.
        # D-0297 (2026-09-28, J-1580) — the metaphor judge above is now ALSO sampled, same 1-in-4
        # rate, same "not_sampled" shape, to relieve the same shared JUDGE_1 hub (see
        # METAPHOR_JUDGE_SAMPLE_P's own comment above for the full F-1943/F-1997 evidence). Drawn
        # independently of `notice_sampled` below -- two separate rulings on two separate
        # instruments. Coherence (`_coherence_check`) and the prediction judge (`_judge_prior`,
        # already gathered earlier above via `gen_task`) are UNTOUCHED, and judge_panel.py's shared
        # TIEBREAK constant is UNTOUCHED -- both out of this job's own scope.
        notice_text = str(out.get("notice") or "")
        notice_sampled = random.random() < NOTICE_JUDGE_SAMPLE_P
        if NOTICE_JUDGE_RETIRED:
            # D-0599 (1): the draw above ALREADY happened (stream position unchanged); only the call is dropped.
            notice_sampled = False
        metaphor_sampled = random.random() < METAPHOR_JUDGE_SAMPLE_P
        if metaphor_sampled and notice_sampled:
            metaphor_judged, coherence, notice_judged = await asyncio.gather(
                _judge_metaphor(out), _coherence_check(out, store, percepts),
                _judge_notice(notice_text, percepts))
        elif metaphor_sampled:
            metaphor_judged, coherence = await asyncio.gather(
                _judge_metaphor(out), _coherence_check(out, store, percepts))
            notice_judged = {"verdict": "not_sampled", "how": None}
        elif notice_sampled:
            coherence, notice_judged = await asyncio.gather(
                _coherence_check(out, store, percepts), _judge_notice(notice_text, percepts))
            metaphor_judged = {"verdict": "not_sampled", "how": None}
        else:
            coherence = await _coherence_check(out, store, percepts)
            metaphor_judged = {"verdict": "not_sampled", "how": None}
            notice_judged = {"verdict": "not_sampled", "how": None}
        if NOTICE_JUDGE_RETIRED:
            notice_judged = {"verdict": "not_sampled", "how": "retired"}   # D-0599 (1): same shape, marked retired

        # J-3117 (F-3837, P-0110) -- ADDITIVE, the metaphor judge's second ("flag") arm. The independent
        # random draw above is UNTOUCHED (same random numbers, same order, so `notice_sampled` and every
        # later draw are unaffected); this block draws NOTHING. Arm "random" = the existing 1-in-4 draw and
        # the ONLY arm that feeds `metaphor_leak_rate_judged` (and every other comparable rate in status()).
        # Arm "flag" = a tick the draw skipped but whose two free keyword scans (zero model calls, both
        # already computed for this tick's row) flagged: it is judged too, so the judge actually sees the
        # register its prompt names (F-3837: the blind draw let it see 2 of 12 flagged ticks). The judge
        # stays BLIND -- `_judge_metaphor(out)` never receives the flags. Rows with no "arm" key (every row
        # logged before this job, and every not_sampled row) read as "random". Fail-open: a scan or judge
        # failure leaves the tick exactly as the random draw left it. Run serially after the gather (~3% of
        # ticks), so the common path pays no extra latency.
        try:
            if metaphor_sampled:
                if isinstance(metaphor_judged, dict):
                    metaphor_judged["arm"] = "random"
            elif _metaphor_flags(out) or _figurative_flags(out):
                _flag_arm_judged = await _judge_metaphor(out)
                if isinstance(_flag_arm_judged, dict):
                    _flag_arm_judged["arm"] = "flag"
                    metaphor_judged = _flag_arm_judged
        except Exception:
            pass

        # D-0361(a) (2026-10-07, J-1896): the deterministic checker, every tick, zero panel load; see
        # `_notice_checked`. Fail-open and draws no random numbers, so nothing above changes.
        notice_checked = _notice_checked(notice_text, percepts)
        # D-0417 (b)->(a) (J-2102): the invention-class sibling, same contract (pure, fail-open, scoreboard only).
        notice_unsupported = _notice_unsupported(notice_text, percepts)

        horizon = str(out.get("horizon") or "").strip().lower()
        if horizon not in HORIZONS:
            horizon = "next"                 # unnamed -> the strictest clock (judged at the next look)
        expect_next_text = str(out.get("expect_next") or "")
        horizon, horizon_overridden, horizon_override_branch = _correct_horizon(horizon, expect_next_text)
        # F-1934/J-1376 (2026-09-26) — law 4's own cannot-fail-class flag; see `_trivial_prediction_flag`'s
        # docstring above. Scored on the SAME `expect_next` text `_correct_horizon` just read, before any
        # store mutation below.
        trivial_prediction = _trivial_prediction_flag(expect_next_text)
        # F-1956/J-1394 (2026-09-27) — the generation-time half of this job's fix; see
        # `_plan_shaped_flag`'s own docstring (near `_trivial_prediction_flag` above) for what it
        # catches and why. Same "score on the SAME text, before any store mutation" convention
        # `trivial_prediction` immediately above already models.
        expect_is_plan = _plan_shaped_flag(expect_next_text)
        # F-2932/J-2239 (2026-10-16) -- see `_heard_steady_sound_flag`'s own comment above. Same "score on
        # the SAME text, before any store mutation" convention; reads only this tick's own world sounds.
        heard_steady_sound = _heard_steady_sound_flag(expect_next_text, (percepts.get("world") or {}).get("sounds"))
        # D-0284 (J-1413, 2026-09-27) — the Weather's second lever (§2.6/law 4a: shifting how much
        # evidence Lane 2 needs before it commits, not just attentional gain). `would_withhold` asks:
        # if the prediction-store's own commit gate were valence-modulated by `gain["commit_threshold"]`
        # (computed above from THIS tick's Weather read), would THIS tick's candidate prediction have
        # been withheld for insufficient evidence? Reuses the tier's one existing evidence-quality
        # proxy (`_grounding_check`'s `grounded_share`, §3.1) against that same bar — no new evidence
        # instrument, no new Weather dimension (law 5: the schema stays frozen). Scoped to the SAME
        # "is there really a candidate prediction here" gate the store-append below already applies —
        # question-shaped and plan-shaped expectations were never storable predictions to begin with,
        # so there is nothing for an evidence bar to withhold — but deliberately NOT also gated on
        # `PENDING_CAP_BY_HORIZON` below: a full queue is a capacity limit, not an evidence question,
        # and folding it in here would understate the new gate's own, independent effect size. `None`
        # when there is no real candidate, or no `grounded_share` to compare (an empty notice/uncertain
        # pair) — never coerced to False, which would misread "not applicable" as "evidence judged
        # sufficient".
        # SHADOW-FIRST per D-0284's own ruling ("...shadow-first, logged as would_withhold before
        # applying"): this does NOT yet change the store-append gate below (unchanged by this job) — it
        # only logs what the gate WOULD have done, so the would-be effect is visible (D-0284's own
        # defeater: 5%-60% of ticks over 7 days) before it changes real behaviour. `status()`'s
        # `would_withhold_rate` is the metric of record for that read.
        expect_is_question = str(out.get("expect_next") or "").strip().endswith("?")
        grounding = _grounding_check(out, percepts)
        _wwh_candidate = bool(expect_next_text) and not expect_is_question and not expect_is_plan
        would_withhold = ((grounding.get("grounded_share") < gain["commit_threshold"])
                           if (_wwh_candidate and grounding.get("grounded_share") is not None) else None)
        # F-1958/J-1396 — `due_resolved` (verdict/judged_ts/judged_how written onto the actual store
        # entry) is now computed earlier, right after `judged` itself, BEFORE the no-output check —
        # see the J-1672/F-2243 comment there for why. `due_resolved` itself is unchanged and still in
        # scope here; `rec` below still reads it the same way it always has.

        # D-0285 (2026-09-27) — §2.8c's knowledge tier. Read BEFORE this tick's own row is built/
        # logged below, so `would_show_knowledge` reflects regularities earned from PRIOR ticks only,
        # never a self-referential "this tick's own data voted for itself" loop. `store['knowledge']`
        # is set from this SAME `knowledge_now` further down, right before `_save_store` — one
        # `_consolidate_knowledge` call (one bounded log read) per tick, not two.
        knowledge_now = _consolidate_knowledge(store)
        would_show_knowledge = _knowledge_would_show(
            knowledge_now, (percepts.get("world") or {}).get("place"),
            (percepts.get("world") or {}).get("daylight"))

        rec = {"ts": round(now, 1), "kind": "tick", "run": RUN,
               # J-1397 (F-1960, 2026-09-27) — ADDITIVE. Which generator/seat produced THIS row, so an
               # era split (qwen2.5:7b -> command-r7b -> deepseek-r1:7b, three seats inside RUN 2 alone
               # -- see MODEL/BASE_URL's own dated history above) is read straight off the row instead
               # of reconstructed from a date cut, which is what every prior era comparison in this
               # plan has had to do (F-1960's own finding). None on any row logged before this job,
               # same backward-compat convention `gen_s`/`percept_lines` already model here.
               "model": MODEL, "seat": BASE_URL,
               # J-1371 (F-1931, §8.1) — ADDITIVE. Wall time of the generation call itself (see
               # `_ask`'s own docstring for exactly what it brackets); `status()`'s `gen_s_median_24h`/
               # `gen_s_p95_24h` are the metric of record so D-0058's own TICK_S=300 defeater can
               # finally be read from the log instead of relying on F-1008's single probe.
               "gen_s": gen_s,
               # J-2164 (D-0414 b, F-2858) -- ADDITIVE. Whether the single retry-on-empty fired and how it ended;
               # `gen_s` above is then the TOTAL of both calls. Rows before this job carry none of these keys.
               **_retry_fields,
               "percepts_available": percepts.get("available"),
               "percepts_missing": percepts.get("missing"),
               "world_fields": percepts.get("world_fields"),
               "standpoint": percepts.get("standpoint"),
               # F-1933 (J-1375, 2026-09-26) — ADDITIVE. `standpoint` alone can name two different
               # places (the study door vs. the garden door both read `at_the_door`), so the
               # `factual`-tier store below now carries `place` too; promoted here to top-level `rec`
               # for the same reason `standpoint` already was — a hand-reader or the coherence judge's
               # own label (`_place_label`) should never have to re-derive it from `world_fields`.
               "place": (percepts.get("world") or {}).get("place"),
               # D-0285 (2026-09-27) — ADDITIVE, same reasoning as `place` immediately above: the
               # knowledge tier's per-(topic, place, daylight) consolidation (`_consolidate_knowledge`,
               # near `tick()`'s own top) needs the daylight PHASE VALUE per tick, and until now it was
               # only ever computed live (`_daylight_word_slip_check`) and never itself logged — only
               # its NAME appeared in `world_fields` (present/absent), never its value. Identical
               # computation to that existing live read, just also promoted to top-level `rec` here.
               "daylight": (percepts.get("world") or {}).get("daylight"),
               # D-0281 (§8.2) needs this: `world_fields` above is only the sorted list of KEY NAMES
               # (from `gather_percepts`'s own `sorted(world)`), never the values — a hand-reader could
               # see "sun_az" was present without ever seeing it was 17°. Without the actual rendered
               # line the generator/judges saw, the plan's own calibration promise ("a human can check
               # the panel's verdict against the percept lines it saw in seconds", §8.2) is not
               # actually possible from this log alone. Exact same string `_ask`/`_judge_notice`/
               # `_judge_prior` were handed this tick (truncated the same [:600] `_judge_prior` already
               # uses) — logged once, read by every hand-calibration pass, not reconstructed from parts.
               "percept_lines": percept_lines(percepts)[:600],
               "weather": weather, "gain": gain,
               "notice": str(out.get("notice") or "")[:NOTICE_LOG_CAP],
               "uncertain": str(out.get("uncertain") or "")[:300],
               "expect_next": str(out.get("expect_next") or "")[:200],
               "horizon": horizon,
               "horizon_overridden": horizon_overridden,  # 2026-08-22 fix — see _correct_horizon
               # F-1934/J-1376 (2026-09-26) — ADDITIVE: which of the branches fired (see
               # `_correct_horizon`'s own docstring; F-2336/J-1713 added 'skipped-hours', so five now).
               # `horizon_overridden` above is unchanged — it is still exactly true on the 'day-scale'
               # branch and false on the other four — this is just the detail a hand-reader or
               # `status()`'s `horizon_override_skipped_minutes`/`horizon_override_skipped_hours` needs
               # to tell "no day-scale topic" apart from "day-scale topic, correctly skipped".
               "horizon_override_branch": horizon_override_branch,
               # the prediction tier CLOSING THE LOOP — judged by the DECOUPLED panel, not by the model
               # that made the prediction (§2.8e), and only when the prediction's own clock has run.
               # F-1958/J-1396 — keyed on `due_resolved`, not `due`: a due prediction that is merely
               # WAITING for its own standpoint/place to come back is reported exactly as "no due
               # prediction this tick" (see `due_resolved`'s own comment above), not as a judged one.
               "judged_expect": (due_resolved or {}).get("expect"),
               "judged_horizon": (due_resolved or {}).get("horizon"),
               "judged_age_s": round(now - float(due_resolved["ts"]), 1) if due_resolved else None,
               # F-1958/J-1396 — ADDITIVE. The prediction's OWN recorded standpoint/place (from when it
               # was created — see the store-append below), placed next to `standpoint`/`place` above
               # (THIS tick's own) so a hand-reader can see a move without cross-referencing the store;
               # None on any row logged before this job (the keys did not exist) or on a `matched-
               # legacy` row (the old prediction shape never recorded either).
               "judged_pred_standpoint": (due_resolved or {}).get("standpoint"),
               "judged_pred_place": (due_resolved or {}).get("place"),
               # D-0285 (2026-09-27) — ADDITIVE sibling to `judged_pred_place` immediately above, same
               # reasoning: the knowledge tier's `prediction_hold` regularity needs WHERE-and-WHEN-IN-
               # DAY a prediction was made, not when it happened to get judged. None on any row logged
               # before this job or the prediction's own creation restart (the key did not exist yet).
               "judged_pred_daylight": (due_resolved or {}).get("daylight"),
               # which of `_prediction_judgeability`'s five branches this tick's own due candidate (if
               # any) resolved to — None when there was no due candidate at all this tick. Absent
               # entirely on any row logged before this job. `status()`'s `unjudgeable_moved_24h` and
               # `broke_share_same_place` are both read directly off this field.
               "prior_judgeability": judgeability,
               "prior_verdict": judged.get("verdict", "none"),
               "prior_judged_how": judged.get("how"),
               # F-1949/J-1386 (2026-09-27) — ADDITIVE. `prior_verdict` can now also be "unsettled"
               # (see `_judge_prior`'s own docstring); these four are the evidence trail for it and
               # for why3's own fix: `prior_judged_why` is the FIRST ("held") ask's resolved why —
               # None on every row logged before this job, same backward-compat pattern `gen_s`/
               # `percept_lines` already model here. `prior_contradicted_how`/`_why` are ONLY set when
               # the second, narrower ask actually fired (held resolved False-or-split) — their mere
               # presence is also the marker `status()`'s `broke_share_strict` uses to tell a
               # confirmed-contradicted "broke" row apart from a pre-fix legacy one that was never
               # asked the second question at all.
               "prior_judged_why": judged.get("why"),
               "prior_contradicted_how": judged.get("contradicted_how"),
               "prior_contradicted_why": judged.get("contradicted_why"),
               "expect_is_question": expect_is_question,
               # F-1956/J-1394 — see `_plan_shaped_flag`'s own docstring above. Also gates the
               # store-append below (a plan-shaped expectation is never stored as a prediction at all).
               "expect_is_plan": expect_is_plan,
               # F-2932/J-2239 -- ADDITIVE key. Also gates the store-append below, exactly like
               # `expect_is_plan`: a prediction that an already-steady sound will sound again is never stored.
               "heard_steady_sound": heard_steady_sound,
               # F-1934/J-1376 — the cannot-fail-class flag (§ above `_trivial_prediction_flag`);
               # `status()`'s `trivial_prediction_rate` is the metric of record this job pre-registers.
               "trivial_prediction": trivial_prediction,
               "grounding": grounding,
               # D-0284 (J-1413) — SHADOW-FIRST only; see the computation above (right before this
               # tick's `rec` is built) for exactly what this compares, why it is scoped the way it
               # is, and why it does not yet touch the store-append gate below.
               "would_withhold": would_withhold,
               "metaphor_flags": _metaphor_flags(out),
               # F-1951/J-1388 (2026-09-27) — ADDITIVE. `_metaphor_flags` above scans Lane 1's own
               # river/crossing register; this scans F-1951's ambient-mood register instead (see
               # `_figurative_flags`'s own docstring). `status()`'s `figurative_flag_rate` is the
               # metric this feeds — read alongside `metaphor_leak_rate_judged`, not merged with it.
               "figurative_flags": _figurative_flags(out),
               # J-0126: the metric of record for §5 metric #1 (decoupled, blind judge — F-0016).
               # D-0297 (2026-09-28): "not_sampled" on the 3-in-4 ticks METAPHOR_JUDGE_SAMPLE_P
               # skips, {"verdict": "metaphor"/"literal"/"cannot_tell", "how": ..., "why": ...} on
               # the 1-in-4 it runs — same shape `notice_judged` below already carries for its own,
               # independently-drawn sample gate (see status()'s `metaphor_judge_coverage`, which
               # now honestly reads ~0.25x its pre-D-0297 value rather than needing a new field).
               "metaphor_judged": metaphor_judged,
               # J-0126: §5 metric #2's actual instrument (F-0018) and §3.11's coherence pass (F-0017).
               "invention": _invention_check(out, percepts),
               # F-1933 (J-1375, 2026-09-26) — cheap deterministic instrument, no judge call. See
               # `_daylight_word_slip_check`'s own docstring; `status()`'s `daylight_word_slip_rate`
               # is the metric of record (rate over NIGHT ticks only, not all ticks).
               "daylight_word_slip": _daylight_word_slip_check(out, percepts),
               "coherence": coherence,
               # J-3126 (F-3853, P-0111): did the observer MOVE since the newest stored record (the one the coherence
               # judge sees last)? 'place' / 'standpoint' / 'same' / None (no comparable previous entry). Instrument
               # only -- read by `status()`'s `incoherence_by_move`; rows from before this job carry no key.
               "coherence_moved": _coherence_moved(store, (percepts.get("world") or {}).get("place"),
                                                   percepts.get("standpoint")),
               # D-0281 (§8.2): the notice's own claim-correctness judge — "not_sampled" on the 3-in-4
               # ticks NOTICE_JUDGE_SAMPLE_P skips, {"verdict": "contradiction"/"consistent"/
               # "cannot_tell", "how": ...} on the 1-in-4 it runs. See status()'s notice_* fields.
               "notice_judged": notice_judged,
               # D-0361(a) (J-1896): the deterministic checker's verdict beside the panel's. "contradiction" /
               # "consistent" / "not_checked" + flag counts and the flagged phrases; see `_notice_checked`.
               "notice_checked": notice_checked,
               # D-0417 (J-2102): {flag, nouns, supported_by, negated, how, v} -- a named invention-prone noun
               # (cat/figure/knock/shadow/footstep/voice/person/clock/fire) no percept line licenses. Scoreboard only.
               "notice_unsupported": notice_unsupported,
               # J-0165 — the discrete coupling channel: which hint (if any) reached this tick,
               # so a later read can build §5 metric #5 (nominated-vs-self-found divergence) by
               # comparing hinted ticks against unhinted ones.
               "hint": ({"tag": hint.get("tag"), "kind": hint.get("kind"), "topic": hint.get("topic"),
                        "age_s": round(now - float(hint.get("pushed_ts") or now), 1)} if hint else None),
               # D-0285 (2026-09-27) — step 3's own shadow-only requirement: "log which regularities
               # WOULD have been shown to the generator; do not actually surface anything to the
               # prompt yet." Computed above (before this dict existed) from `knowledge_now`, itself
               # read from PRIOR ticks only. Never passed to `percept_lines()`/`_ask()` anywhere in
               # this file — read back only from this log, by a human or a future (separate,
               # restart-gated) job. [] most ticks (no top-12 regularity matches this place/phase yet,
               # or the knowledge tier itself is still empty this early in the shadow run).
               "would_show_knowledge": would_show_knowledge}
        if due_resolved and due_resolved.get("judge_retries"):
            # J-3100 / F-3818 -- ADDITIVE, only on a row whose prediction has been re-asked (so every other row is
            # byte-identical): `status()`'s judge_retry_* counts read these. 1 on the retry row itself and on the
            # row that finally closes it.
            rec["prior_judge_retries"] = due_resolved.get("judge_retries")
            if judge_retry_now:
                rec["prior_judge_err1"], rec["prior_judge_err2"] = judged.get("err1"), judged.get("err2")
        _log(rec)
        # Dosed Coupling Phase 1 (D-0152, 2026-09-05): publish the Witness tuple; Lane 2 stays shadow.
        try:
            from core import coupling_rides as _coupling
            _coupling.publish_witness(rec, store)
        except Exception:
            pass

        # ── D-0282/J-1374 (2026-09-26) — Lane 2 Curiosity's `wonder` field, SHADOW-FIRST. Own log
        # (`_LOG_WONDER`), own gate call (`lane2_break_habituation.observe_wonder`, sharing that
        # module's per-topic state with `observe_break` by the staged doc's own design — §2: "the SAME
        # gate ... decides whether a wonder on that topic is still novel"). `frontier.note_question` is
        # NOT called here — staged doc §6 step 2 is a separate, later, explicitly-deferred flip, out of
        # this job's scope. Runs the SAME cheap lexical instruments already applied to the other four
        # fields (`_grounding_check`/`_invention_check`/`_metaphor_flags`), scoped to `wonder` via their
        # additive `out_fields` param — "this field does not get a pass on the existing quality bars"
        # (this job's own briefing, step 2). Deliberately SKIPS the decoupled `_judge_metaphor`
        # judge_panel call for wonder specifically: that instrument is not in the staged doc's own
        # pre-registered row schema (§4), and adding a 5th concurrent judge_panel call to EVERY tick
        # (vs. today's 2, or 3 on the 1-in-4 ticks D-0281 samples) is a real added load on the shared
        # hubs for a field whose own boundary failure mode (drifting to self/procedure) is already the
        # thing `is_world_question()` below targets directly — a deliberate scope call, flagged here
        # plainly rather than silently decided, so a future read can revisit it if wrong.
        try:
            wonder_text = str(out.get("wonder") or "").strip()
            if wonder_text:
                wonder_topic = _topic_of(wonder_text)
                wonder_grounded = _grounding_check(out, percepts, out_fields=("wonder",))
                wonder_invented = _invention_check(out, percepts, out_fields=("wonder",))
                wonder_metaphor = _metaphor_flags(out, out_fields=("wonder",))
                wonder_anchored = _wonder_percept_anchored(wonder_text, percepts)
                try:
                    from core import frontier as _frontier
                    wonder_is_world_q = bool(_frontier.is_world_question(wonder_text))
                except Exception:
                    wonder_is_world_q = False

                # J-2173 / D-0429(b): read BEFORE this row is logged, so a wonder never matches itself.
                if WONDER_ANTI_REPEAT:
                    wonder_repeat = _wonder_repeat_check(wonder_text, wonder_topic,
                                                         _wonder_recent_rows(), now)
                else:
                    wonder_repeat = {"lexical_sim_max": None, "lexical_repeat": False,
                                     "topic_asked_today": False}
                would_ask, w_topic, would_ask_reason = False, None, "no-topic-match"
                if wonder_topic:
                    try:
                        from core import lane2_break_habituation as _hab_wonder
                        gate = _hab_wonder.observe_wonder(wonder_topic, now)
                    except Exception:
                        gate = None
                    if gate is None:
                        would_ask_reason = "gate-unavailable"
                    else:
                        w_topic = gate.get("discounted_before")
                        if not wonder_is_world_q:
                            would_ask_reason = "not-world-question"
                        elif not gate.get("would_ask"):
                            would_ask_reason = "topic-habituated"
                        elif wonder_repeat["lexical_repeat"]:
                            would_ask_reason = "lexical-repeat"
                        elif wonder_repeat["topic_asked_today"]:
                            would_ask_reason = "topic-asked-today"
                        # WONDER_MAX_PER_DAY (this job's briefing step 4 / staged doc §4 W-4) — see the
                        # constant's own comment above for the "by symmetry" rationale correction.
                        elif _wonder_asks_today(now) >= WONDER_MAX_PER_DAY:
                            would_ask_reason = "daily-cap"
                        else:
                            would_ask, would_ask_reason = True, "ok"

                _log_wonder({"ts": rec["ts"], "wonder": wonder_text[:220], "topic": wonder_topic,
                             "horizon_of_notice": horizon,
                             "grounded": wonder_grounded, "invented": wonder_invented,
                             "metaphor_flags": wonder_metaphor,
                             "percept_anchored_topics": wonder_anchored,
                             "world_question": wonder_is_world_q,
                             "would_ask": would_ask, "would_ask_reason": would_ask_reason,
                             "w_topic": w_topic,
                             "lexical_sim_max": wonder_repeat["lexical_sim_max"],
                             "lexical_repeat": wonder_repeat["lexical_repeat"],
                             "topic_asked_today": wonder_repeat["topic_asked_today"],
                             # J-3965: A/B arm marker (False = control arm, or flag off)
                             "avoid_arm": _avoid_arm, "avoid_terms": _avoid_terms})
        except Exception as exc:
            logger.debug("[lane2] wonder block failed (non-fatal): %s", exc)

        store.setdefault("factual", []).append(
            # F-1933 (J-1375, 2026-09-26) — ADDITIVE: `standpoint`/`place` so `_coherence_check` can
            # label each record `[place/standpoint]` instead of handing the panel bare notice text
            # blind to whether the observer moved between records (see its own docstring).
            {"ts": rec["ts"], "notice": rec["notice"][:200], "sources": percepts.get("available"),
             "standpoint": rec.get("standpoint"), "place": rec.get("place")})
        pending = [r for r in store.get("prediction") or [] if r.get("verdict") is None]
        # F-1956/J-1394 (2026-09-27) — ADDITIVE third guard alongside `expect_is_question` above: a
        # plan-shaped expectation (`_plan_shaped_flag`, see its own comment above) is an intention
        # about the observer's own next act, not a claim about the world, and was never storable as a
        # real prediction in spirit (law 4 always meant this); it is now also excluded in practice,
        # before it can occupy a pending-cap slot or reach the judge panel unjudged.
        # F-2932/J-2239 (2026-10-16) -- ADDITIVE fourth guard, same shape as `expect_is_plan`'s: a
        # prediction that a sound already sounding steadily in this tick's percepts will sound again
        # (`_heard_steady_sound_flag`) cannot break while he stays put, so it never takes a pending-cap
        # slot or a panel call. `.get` so a rec built without the key behaves exactly as before.
        # J-3160 / D-0548 (2026-11-02) -- ADDITIVE fifth guard: a prediction flagged `trivial_prediction` (a
        # bare azimuth figure, a clock tick, 'will remain / continue / still': the classes that cannot
        # fail, 26 percent of predictions) is no longer STORED, so it can never be judged and never
        # break. Before this, 2 of the 4 live cup breaks were such rows (a bare azimuth "judged 28.5
        # degrees" for a 2.5 degree miss; a clock tick judged 40 minutes late). The tick row above keeps
        # `trivial_prediction` (the measurement is unchanged); a skip row records each exclusion so the
        # count is read in `status()['skips']`. `TRIVIAL_PREDICTION_EXCLUDED = False` restores the old
        # behaviour byte for byte.
        _trivial_excluded = bool(TRIVIAL_PREDICTION_EXCLUDED and rec.get("trivial_prediction")
                                 and rec["expect_next"])
        if _trivial_excluded:
            _skip("trivial-excluded", horizon=horizon, expect=str(rec["expect_next"])[:80])
        if (rec["expect_next"] and not rec["expect_is_question"] and not rec["expect_is_plan"]
                and not rec.get("heard_steady_sound") and not _trivial_excluded):
            same = [p for p in pending if p.get("horizon") == horizon]
            if len(same) >= PENDING_CAP_BY_HORIZON.get(horizon, 4):
                _skip("pending-cap", pending=len(same), horizon=horizon)
            else:
                store.setdefault("prediction", []).append(
                    {"ts": rec["ts"], "expect": rec["expect_next"], "horizon": horizon,
                     "due_ts": round(now + HORIZONS[horizon], 1), "verdict": None,
                     # F-1958/J-1396 — ADDITIVE: WHERE this prediction was made, so it can be judged
                     # only where it was made (see `_prediction_judgeability`'s own docstring, just
                     # above `_due_prediction`). Read back at judging time as `rec.get("standpoint")`/
                     # `.get("place")` on the SAME rec these two values were promoted onto above.
                     "standpoint": rec.get("standpoint"), "place": rec.get("place"),
                     # D-0285 (2026-09-27) — ADDITIVE sibling to `standpoint`/`place` immediately
                     # above, same reasoning: WHEN-IN-DAY this prediction was made, read back at
                     # judging time as `rec.get("daylight")` (see `_consolidate_knowledge`'s own
                     # `prediction_hold` regularity, near `tick()`'s own top, and `judged_pred_daylight`
                     # a little further up in this same tick's own `rec` for where it surfaces).
                     "daylight": rec.get("daylight")})
        # D-0285 (2026-09-27) — persist this tick's consolidation (computed earlier, before this
        # tick's own row existed in the log — see the comment at `knowledge_now`'s own computation
        # above) so the NEXT tick's `_consolidate_knowledge` call, and any other reader of the store
        # (e.g. `status()`), sees it. §2.8d's own size law is enforced inside `_consolidate_knowledge`
        # itself (top KNOWLEDGE_CAP only, already sorted) and again defensively in `_save_store`, so
        # nothing further is needed here.
        store["knowledge"] = knowledge_now
        _save_store(store)
        return rec
    except Exception as exc:
        _skip("tick-error", error=repr(exc)[:160])
        return None


async def run_forever(stop_event=None) -> None:
    """The STANDING loop — its own cadence, independent of whatever Lane 1 is doing. This is the single
    hardest requirement to keep honest: the moment this becomes 'fires when Lane 1 asks', it has turned
    back into the reactive Emissary under a new name."""
    if LANE2_PAUSED:
        logger.info("[lane2] PAUSED (2026-08-28 ollama-off-Ramses ruling) — standing loop not started; "
                    "no ticks, no shadow rows until re-seated on a real hub")
        return
    logger.info("[lane2] standing loop starting — tick %.0fs, %s @ %s (SHADOW=%s)",
                TICK_S, MODEL, BASE_URL, not LANE2_LIVE)
    while not (stop_event and stop_event.is_set()):
        await tick()
        try:
            await asyncio.sleep(TICK_S)
        except asyncio.CancelledError:
            break


def _wonder_metric_sheet() -> dict:
    """docs/staged/lane2_curiosity.md §4's pre-registered W-1..W-5 (D-0282/J-1374). Reads THIS field's
    own shadow log (`_LOG_WONDER`, one row per GENERATED wonder, real and accruing from the first tick
    after the restart that picks up this schema change). W-5 (the existing four fields' own kill
    metrics staying in-band) is deliberately NOT duplicated here: it is read directly off `status()`'s
    own top-level `metaphor_leak_rate_judged` / `named_uncertainty_rate` / `question_expect_rate` — the
    same numbers this function's own caller already returns — so there is exactly one source of truth
    for each, not two that could drift apart. Never raises."""
    empty = {"rows": 0, "w1_distinct_share_7d": None, "w2_world_question_pass_rate": None,
             "w3_percept_anchored_share": None, "w4_would_ask_per_day": None,
             "w4_generated_per_day": None,
             "w5_note": "read status()'s own metaphor_leak_rate_judged / named_uncertainty_rate / "
                        "question_expect_rate directly -- not duplicated here"}
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG_WONDER, 5000)
    except Exception:
        return empty
    if not rows:
        return empty
    now = time.time()
    week_rows = [r for r in rows if now - float(r.get("ts") or 0) <= 7 * 86400.0]
    day_rows = [r for r in rows if now - float(r.get("ts") or 0) <= 86400.0]
    w1 = round(len({r.get("wonder") for r in week_rows}) / len(week_rows), 3) if week_rows else None
    wq_n = sum(1 for r in rows if "world_question" in r)
    w2 = round(sum(1 for r in rows if r.get("world_question")) / wq_n, 3) if wq_n else None
    anc_n = sum(1 for r in rows if "percept_anchored_topics" in r)
    w3 = (round(sum(1 for r in rows if r.get("percept_anchored_topics")) / anc_n, 3)
          if anc_n else None)
    w4_ask = sum(1 for r in day_rows if r.get("would_ask")) if day_rows else 0
    # J-2173: anti-repeat reads. Lexical distinct share = share of week rows NOT flagged lexical_repeat
    # (only rows carrying the key, i.e. written after this change); would-ask topic spread over the last 24h.
    lex_rows = [r for r in week_rows if "lexical_repeat" in r]
    w1_lex = (round(sum(1 for r in lex_rows if not r.get("lexical_repeat")) / len(lex_rows), 3)
              if lex_rows else None)
    ask_topics: dict = {}
    for r in day_rows:
        if r.get("would_ask"):
            ask_topics[r.get("topic")] = ask_topics.get(r.get("topic"), 0) + 1
    suppressed = {k: sum(1 for r in day_rows if r.get("would_ask_reason") == k)
                  for k in ("lexical-repeat", "topic-asked-today")}
    # J-3965: per-arm reads of the prompt-side avoid-list A/B (rows carrying `avoid_arm`).
    def _arm(flag):
        a = [r for r in week_rows if "avoid_arm" in r and bool(r.get("avoid_arm")) is flag]
        n = len(a)
        lex = [r for r in a if "lexical_repeat" in r]
        anc = [r for r in a if "percept_anchored_topics" in r]
        return {"rows": n,
                "lexical_distinct_share": (round(sum(1 for r in lex if not r.get("lexical_repeat")) / len(lex), 3)
                                           if lex else None),
                "exact_distinct_share": round(len({r.get("wonder") for r in a}) / n, 3) if n else None,
                "percept_anchored_share": (round(sum(1 for r in anc if r.get("percept_anchored_topics"))
                                                 / len(anc), 3) if anc else None)}
    return {
        "w1_avoid_ab_7d": {"avoid": _arm(True), "control": _arm(False)},
        "w1_lexical_distinct_share_7d": w1_lex,
        "w1_lexical_rows": len(lex_rows),
        "w4_would_ask_topics_24h": ask_topics,
        "w4_suppressed_24h": suppressed,
        "rows": len(rows),
        "w1_distinct_share_7d": w1,
        "w1_note": "prediction >= 0.8 (the expect_next bar) -- staged doc §4",
        "w2_world_question_pass_rate": w2,
        "w2_note": "prediction >= 0.95 -- below, the field drifts to self/procedure",
        "w3_percept_anchored_share": w3,
        "w3_note": "prediction >= 0.9 -- below, wonders are about things not perceived",
        "w4_would_ask_per_day": w4_ask,
        "w4_generated_per_day": len(day_rows),
        "w4_note": "prediction: low single digits/day, hard cap WONDER_MAX_PER_DAY=4 -- tracking the "
                   "raw tick rate means the gate is not gating",
        "w5_note": "read status()'s own metaphor_leak_rate_judged / named_uncertainty_rate / "
                   "question_expect_rate directly -- not duplicated here",
    }


# ── The cup tripwire, as a number a person reads (J-3160 / D-0548, 2026-11-02) ────────────────────────
# D-0548 (Travis): keep the Lane 2 cup live and fix the artefacts, "if two more artefact breaks ride before that
# build lands, switch the cup off (a person reads a pulse count; nothing switches it off automatically)".
# `cup_artefact_report` is that pulse count and NOTHING ELSE: display only. It switches nothing, schedules
# nothing, and is read by `scripts/du_pulse.py`; the decision stays with Travis. It is deliberately NOT in
# `status()` (the HUD polls that every ~6 s; this walks two large logs backward).
# A "ride" is a coupling_rides.jsonl row {line: witness, dose: cup} whose value names a topic (the cup was
# taken by an idle thought). Each ride is matched to the broke verdict that placed it (the newest broke row in
# lane2_shadow.jsonl, before the ride and within CUP_TTL_S, with the same topic and horizon) and that row is
# graded by a SIMPLE AUTOMATIC test, three reasons, none of them a model judgement:
#   place_mismatch -- the prediction was made in a different place from where it was judged;
#   stale          -- judged later than `_STALE_AFTER_S` past due, or Du slept between making and judging
#                     (next/hour only);
#   trivial        -- `_trivial_prediction_flag` on the judged text (a bare azimuth, a clock tick, 'remain').
# It will NOT flag every artefact (the 10-29 night "sunrise" prediction passes all three), so a clean count is
# a floor on artefacts, not proof of a good break; the four hand-graded F-3741 breaks are the check.
CUP_WATCH_SINCE_TS = 1793579375.0     # 2026-11-02T00:29:35Z, the D-0548 ruling
CUP_TRIPWIRE_ARTEFACTS = 2            # D-0548: "two more artefact breaks"


def _cup_row_place(r: dict):
    p = r.get("place")
    if p:
        return p
    import re
    m = re.search(r"^- place: (\S+)", str(r.get("percept_lines") or ""), re.M)
    return m.group(1) if m else None


def cup_break_artefact_reasons(r: dict, asleep_ts=()) -> list:
    """Why a judged-broke log row looks like an artefact, by the three automatic tests above ([] = none
    fired). `r` is a tick row or a no-output skip row carrying `prior_verdict == 'broke'`; `asleep_ts` is
    the timestamps of asleep skip rows. Pure, no I/O, never raises."""
    reasons = []
    try:
        horizon = r.get("judged_horizon")
        pred_place, here = r.get("judged_pred_place"), _cup_row_place(r)
        if pred_place and here and pred_place != here:
            reasons.append("place_mismatch")
        age = r.get("judged_age_s")
        stale = bool(age is not None and horizon in HORIZONS and float(age) > HORIZONS[horizon] + _STALE_AFTER_S)
        if not stale and age is not None and horizon in ("next", "hour"):
            made, judged = float(r["ts"]) - float(age), float(r["ts"])
            stale = any(made < float(a) < judged for a in asleep_ts)
        if stale:
            reasons.append("stale")
        if _trivial_prediction_flag(str(r.get("judged_expect") or "")):
            reasons.append("trivial")
    except Exception:
        pass
    return reasons


def cup_artefact_report(since_ts: float = CUP_WATCH_SINCE_TS, log_path=None, rides_path=None) -> dict:
    """The cup tripwire count (see the section comment above): rides since `since_ts`, how many of them
    rode a break the automatic test calls an artefact, by reason, plus the last few. Read-only, bounded
    (walks each file backward and stops at `since_ts`), never raises: on failure returns {'error': ...}."""
    import re
    try:
        from core.shadow_log import reverse_lines
        try:
            from core.coupling_rides import CUP_TTL_S as _ttl
        except Exception:
            _ttl = 1800.0
        log_path = Path(log_path) if log_path else _LOG
        rides_path = Path(rides_path) if rides_path else (_DATA / "coupling_rides.jsonl")
        ts_rx = re.compile(rb'^\{"ts": ([0-9.]+)')

        def _ts(raw):
            m = ts_rx.match(raw)
            return float(m.group(1)) if m else None

        rides = []
        for raw in reverse_lines(rides_path):
            t = _ts(raw)
            if t is not None and t < since_ts:
                break
            if b'"dose": "cup"' in raw and b'"line": "witness"' in raw and b'"topic": "' in raw:
                try:
                    r = json.loads(raw)
                except Exception:
                    continue
                v = r.get("value") or {}
                if v.get("topic"):
                    rides.append({"ts": float(r["ts"]), "topic": v.get("topic"), "horizon": v.get("horizon")})
        rides.reverse()
        broke, asleep = [], []
        for raw in reverse_lines(log_path):
            t = _ts(raw)
            if t is not None and t < since_ts - 7200.0:
                break
            if b'"prior_verdict": "broke"' in raw:
                try:
                    broke.append(json.loads(raw))
                except Exception:
                    pass
            elif b'"skip": "asleep"' in raw and t is not None:
                asleep.append(t)
        broke.sort(key=lambda r: float(r.get("ts") or 0))
        used, graded, unmatched = set(), [], 0
        for ride in rides:
            cands = [i for i, r in enumerate(broke)
                     if i not in used and 0 <= ride["ts"] - float(r.get("ts") or 0) <= _ttl
                     and _topic_of(r.get("judged_expect")) == ride["topic"]
                     and (r.get("judged_horizon") in (None, ride["horizon"]))]
            if not cands:
                unmatched += 1
                continue
            i = max(cands, key=lambda j: float(broke[j].get("ts") or 0))
            used.add(i)
            why = cup_break_artefact_reasons(broke[i], asleep)
            graded.append({"ts": ride["ts"], "topic": ride["topic"], "horizon": ride["horizon"],
                           "reasons": why, "expect": str(broke[i].get("judged_expect") or "")[:90]})
        by_reason = {k: sum(1 for g in graded if k in g["reasons"]) for k in ("place_mismatch", "stale", "trivial")}
        artefacts = sum(1 for g in graded if g["reasons"])
        return {"since_ts": since_ts, "rides": len(rides), "matched": len(graded), "unmatched": unmatched,
                "artefacts": artefacts, "clean": len(graded) - artefacts, "by_reason": by_reason,
                "tripwire_limit": CUP_TRIPWIRE_ARTEFACTS, "tripwire_reached": artefacts >= CUP_TRIPWIRE_ARTEFACTS,
                "recent": graded[-8:]}
    except Exception as exc:
        return {"error": repr(exc)[:160]}


# ── Claim-class split of judged predictions (J-3101 / F-3813 / P-0109) ───────────────────────────────
# F-3813: the 87% held share since the 10-29 boot is mostly a score for sound claims whose sound is
# ALREADY in the judging tick's own `sounds:` line (127 of 128 "I will hear X" claims). A hand-read of
# that number as forecasting skill is wrong. This is INSTRUMENT ONLY: it re-reads the judged rows already
# stored (`judged_expect` + `percept_lines`), makes no model call, and changes no verdict.
#   sound_resident : the expectation is ONE sound claim and a content word of it matches a sounds-line
#                    entry in the judged tick's percepts (it was already audible when judged).
#   other          : everything else, with a `reasons` breakdown (sound_not_resident, number_or_clock,
#                    sun_weather_light, multi_claim, no_sound_claim, no_percept).
# A "6 minutes" time span is stripped before the number test, because every `next` claim carries one.
_CC_SOUND_CUES = re.compile(
    r"\b(hear|heard|hearing|sound|sounds|song|songs|call|calls|trill|chatter|tick|ticks|ticking|rasp|"
    r"chorus|hum|buzz|buzzing|rustle|crackle|waves|birdsong|chirp|chirping|alarm|rumble|noise)\b")
_CC_OTHER_DOMAIN = re.compile(
    r"\b(sun|sunrise|sunset|moon|moonrise|tide|tides|weather|rain|wind|cloud|clouds|temperature|warmer|"
    r"cooler|colder|warm|cold|light|dark|darker|brighter|dusk|dawn|clock|o'clock|hour hand|noon|midnight|"
    r"cat|smell|scent|fatigue|energy|tension)\b")
_CC_TIME_SPAN = re.compile(
    r"\b(in|within|after|over)?\s*(about|around|roughly|approximately|the next)?\s*"
    r"(\d+|one|two|three|four|five|six|ten|fifteen|twenty|thirty|a few|a couple of)?\s*"
    r"(seconds?|minutes?|mins?|hours?|days?)\b")
_CC_STOP = frozenset((
    "the", "and", "for", "will", "that", "this", "with", "from", "some", "into", "about", "next", "again",
    "still", "keep", "continue", "continues", "native", "small", "sound", "sounds", "song", "songs", "call",
    "calls", "hear", "heard", "hearing", "expect", "shall", "soon", "same", "more", "also", "just"))


def _cc_stem(w: str) -> str:
    w = w.replace("’s", "").replace("'s", "")
    return w[:-1] if len(w) > 4 and w.endswith("s") else w


def _cc_sound_entries(percept_text: str):
    """The tick's own `- sounds:` line as a list of entries, or None when the line is absent (a missing
    line, or one cut off by the 600-char `percept_lines` cap, is reported as no_percept, never guessed)."""
    m = re.search(r"^- sounds: (.*)$", str(percept_text or ""), re.M)
    if not m:
        return None
    return [e.strip().lower() for e in m.group(1).split(",") if e.strip()]


def _claim_class(expect: str, percept_text: str) -> tuple:
    """(class, reason) for one judged prediction. class in 'sound_resident' | 'other'. A claim that names a
    sound already in the sounds line but ALSO makes a second claim (number/clock, sun/weather/light, or
    several clauses) is class 'other' with a `mixed_*` reason, so a broken second half is never scored as a
    sound win, and `_claim_class_split` can still report how large the loosely-read sound share is."""
    said = str(expect or "").lower().strip()
    entries = _cc_sound_entries(percept_text)
    if not said:
        return "other", "no_sound_claim"
    # The generator sometimes appends its own label ("The horizon is 'next'.", "as the horizon is set to ...");
    # that is prompt echo, not a second claim, so it is cut before the multi-claim test.
    said = re.sub(r"[,.]?\s*(?:and |as |because )?(?:the )?horizon (?:is|was|set)[^.]*\.?", " ", said)
    body = _CC_TIME_SPAN.sub(" ", said)
    named = False
    if entries is not None and _CC_SOUND_CUES.search(body):
        said_w = {_cc_stem(w) for w in re.findall(r"[a-z]+(?:['\u2019]s)?", body)} - _CC_STOP
        said_w = {w for w in said_w if len(w) >= 3}
        for e in entries:
            ew = {_cc_stem(w) for w in re.findall(r"[a-z]+", e)} - _CC_STOP
            if any(t == u or (len(t) >= 4 and len(u) >= 4 and (t in u or u in t))
                   for t in said_w for u in ew):
                named = True
                break
    pre = "mixed_" if named else ""
    if re.search(r"\d", body) or re.search(r"\b(o'clock|clock strikes?|chimes?)\b", body):
        return "other", pre + "number_or_clock"
    if _CC_OTHER_DOMAIN.search(body):
        return "other", pre + "sun_weather_light"
    if re.search(r"[.!?;]", body.strip().rstrip(".!? ")) or re.search(r"\b(and|while|but|then|or)\b", body):
        return "other", pre + "multi_claim"
    if named:
        return "sound_resident", "sound_in_sounds_line"
    if not _CC_SOUND_CUES.search(body):
        return "other", "no_sound_claim"
    if entries is None:
        return "other", "no_percept"
    return "other", "sound_not_resident"


def _claim_class_split(ticks: list) -> dict:
    """Held/unsettled/broke per claim class over the judged tick rows (same rows `prediction_verdicts`
    counts). `held_share` is held/(held+broke), the convention `broke_share` uses. Pure read."""
    def _blank():
        return {"n": 0, "held": 0, "unsettled": 0, "broke": 0}
    out = {"sound_resident": _blank(), "other": _blank()}
    reasons: dict = {}
    for r in ticks:
        v = r.get("prior_verdict")
        if v not in ("held", "unsettled", "broke"):
            continue
        cls, why = _claim_class(r.get("judged_expect"), r.get("percept_lines"))
        out[cls]["n"] += 1
        out[cls][v] += 1
        if cls == "other":
            reasons[why] = reasons.get(why, 0) + 1
    for d in out.values():
        hb = d["held"] + d["broke"]
        d["held_share"] = round(d["held"] / hb, 3) if hb else None
        # held/n and unsettled/n keep the 'unsettled' rows in the denominator: held_share above drops them,
        # which flatters the class where the judge most often declines to call (the 'other' class).
        d["held_of_judged"] = round(d["held"] / d["n"], 3) if d["n"] else None
        d["unsettled_of_judged"] = round(d["unsettled"] / d["n"], 3) if d["n"] else None
    total = out["sound_resident"]["n"] + out["other"]["n"]
    h_all = out["sound_resident"]["held"] + out["other"]["held"]
    b_all = out["sound_resident"]["broke"] + out["other"]["broke"]
    out["other"]["reasons"] = reasons
    out["n"] = total
    mixed = sum(v for k, v in reasons.items() if k.startswith("mixed_"))
    # Loose reading (any named resident sound, even beside a second claim): about what a hand-read of the
    # raw rows gives (F-3813 ~70%). Reported so the strict share is not mistaken for a smaller problem.
    out["sound_named_resident_share"] = (
        round((out["sound_resident"]["n"] + mixed) / total, 3) if total else None)
    out["sound_resident_share"] = round(out["sound_resident"]["n"] / total, 3) if total else None
    out["held_share_all"] = round(h_all / (h_all + b_all), 3) if (h_all + b_all) else None
    out["note"] = ("sound_resident = the sound was already in the judging tick's sounds line (a describe-the-present "
                   "score, held_share ~1.0 by construction); held_share_all blends it with 'other'. Read 'other' "
                   "held_of_judged (unsettled kept in the denominator) as the skill-like number")
    return out


# J-3041 / F-3745 (P-0098) -- kill-criterion instruments that CAN fail. ADDITIVE, status()-only, no prompt change, no
# gate. The existing `named_uncertainty_rate` (99.6%) counts any non-blank `uncertain`, and `question_expect_rate` only
# reads expect_next, so neither can move. These read the other fields and compare `uncertain` to the tick's own percepts.
import re as _re_j3041

_J3041_DISCLAIM = _re_j3041.compile(
    r"(?:cannot|can't|can not|unable to|not able to|couldn't|could not|don't|do not|doesn't)\s+"
    r"(see|hear|smell|feel)([^.;]*)", _re_j3041.I)
_J3041_STOP = {"the", "and", "its", "his", "her", "their", "from", "with", "that", "this", "what", "whether", "exact",
               "exactly", "specific", "precise", "any", "about", "into", "than", "there", "which", "where", "when",
               "how", "why", "cause", "source", "position", "duration", "direction", "origin", "details", "detail",
               "nature", "type", "kind", "next", "will", "would", "ahead", "yet", "much", "many", "long", "far"}
# which percept lines count as the present sense for a disclaimed verb ("" = any line)
_J3041_SENSE_KEYS = {"hear": ("sounds",), "smell": ("smells",),
                     "see": ("light band", "daylight", "sun", "weather", "place", "standpoint"),
                     "feel": ("warmth", "weather", "somatic", "body")}


def _j3041_percept_map(text: str) -> dict:
    out = {}
    for ln in (text or "").splitlines():
        ln = ln.strip()
        if ln.startswith("- ") and ":" in ln:
            k, v = ln[2:].split(":", 1)
            out[k.strip().lower()] = v.strip().lower()
    return out


def _j3041_uncertain_contradicts_percept(uncertain: str, percept_text: str) -> bool:
    """True when `uncertain` says it cannot see/hear/smell/feel X and X's content word appears in a percept line of
    the matching present sense (prefix match, first 5 chars). Heuristic, keyword-only; undercounts paraphrase."""
    pm = _j3041_percept_map(percept_text)
    if not uncertain or not pm:
        return False
    for m in _J3041_DISCLAIM.finditer(uncertain):
        verb, obj = m.group(1).lower(), m.group(2).lower()
        keys = _J3041_SENSE_KEYS.get(verb)
        if keys:
            # hear/smell compare against the VALUES only (the key word "sounds" would match any "sound" disclaimer)
            lines = [(v if verb in ("hear", "smell") else f"{k} {v}")
                     for k, v in pm.items() if v and any(k.startswith(x) for x in keys)]
        else:
            lines = [f"{k} {v}" for k, v in pm.items() if v]
        blob = _re_j3041.findall(r"[a-z]+", " ".join(lines))
        stems = {w[:5] for w in blob if len(w) >= 3}
        for w in _re_j3041.findall(r"[a-z]+", obj):
            if len(w) >= 3 and w not in _J3041_STOP and w[:5] in stems:
                return True
    return False


def _j3041_instruments(ticks: list) -> dict:
    n = len(ticks)
    if not n:
        return {}

    def _q(v):
        return "?" in str(v or "")
    cov = [r for r in ticks if r.get("percept_lines") and r.get("uncertain")]
    contra = sum(1 for r in cov if _j3041_uncertain_contradicts_percept(r["uncertain"], r["percept_lines"]))
    notices = [str(r.get("notice") or "") for r in ticks]
    leak = sum(1 for t in notices if _re_j3041.search(r"(?<![\d.])0\.\d+", t))
    over = sum(1 for t in notices if len(t.split()) > 60)
    mix = {"next": 0, "hour": 0, "day": 0}
    for r in ticks:
        h = r.get("horizon")
        if h in mix:
            mix[h] += 1
    tss = [float(r["ts"]) for r in ticks if isinstance(r.get("ts"), (int, float))]
    span_d = round((max(tss) - min(tss)) / 86400.0, 2) if len(tss) > 1 else 0.0
    cut = (max(tss) - 7 * 86400.0) if tss else None
    t7 = [r for r in ticks if cut is not None and isinstance(r.get("ts"), (int, float)) and r["ts"] >= cut]
    day7 = sum(1 for r in t7 if r.get("horizon") == "day")
    note = None
    if span_d >= 7 and t7 and day7 == 0:
        note = "no 'day' horizon prediction in the last 7 days (%d ticks): day machinery inert" % len(t7)
    return {
        "uncertain_contradicts_percept_rate": round(contra / len(cov), 3) if cov else None,
        "uncertain_contradicts_percept_n": contra,
        "uncertain_contradicts_percept_covered": len(cov),
        "question_rate_by_field": {
            "notice": round(sum(1 for r in ticks if _q(r.get("notice"))) / n, 3),
            "uncertain": round(sum(1 for r in ticks if _q(r.get("uncertain"))) / n, 3),
            "expect_next": round(sum(1 for r in ticks if _q(r.get("expect_next")) or r.get("expect_is_question")) / n, 3),
        },
        "raw_number_leak_rate": round(leak / n, 3),
        "over_length_rate": round(over / n, 3),
        "horizon_label_mix": mix,
        "horizon_window_days": span_d,
        "horizon_day_note": note,
    }


def status() -> dict:
    """For the pulse/HUD. The two numbers that decide Phase 0: does it stay grounded, and does it stay
    literal (§5 metrics #1/#2)."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): was a full scan of the 1.7MB+ growing log on every ~6s
        # HUD poll. "ticks" and all rates are now over the last-2000-row window.
        rows = _tail_rows(_LOG, 2000)
    except Exception:
        return {"ticks": 0, "run": RUN, "live": LANE2_LIVE}
    ticks = [r for r in rows if r.get("kind") == "tick"]
    skips = {}
    for r in rows:
        if r.get("kind") == "skip":
            skips[r.get("skip")] = skips.get(r.get("skip"), 0) + 1
    if not ticks:
        return {"ticks": 0, "skips": skips, "run": RUN, "live": LANE2_LIVE}
    g = [r["grounding"]["grounded_share"] for r in ticks
         if (r.get("grounding") or {}).get("grounded_share") is not None]
    flagged = sum(1 for r in ticks if r.get("metaphor_flags"))
    # F-1951/J-1388 (2026-09-27) — ADDITIVE, sibling count to `flagged` above. `figurative_flags` is a
    # brand-new key (this job, restart-gated like every other `core/lane2.py` change this plan has
    # shipped) — every row logged before Du's next restart lacks it entirely, so (same honest-coverage
    # idiom `metaphor_judge_coverage`/`_wonder_metric_sheet`'s `w3` already use for a new key) the rate
    # below is computed over rows that actually CARRY the key, never over `len(ticks)` — a naive
    # `r.get(...)` truthiness count would silently read a real "no data yet" as a misleading "0%
    # figurative" the moment this ships, before a single post-restart tick exists. See
    # `_figurative_flags`'s own docstring for why the eventual rate reads well above the judge's own
    # `metaphor_leak_rate_judged` by design (a cheap keyword scan over-fires on literal color
    # description; that gap is the honest signal, not a bug).
    fig_covered = [r for r in ticks if "figurative_flags" in r]
    figurative_flagged = sum(1 for r in fig_covered if r.get("figurative_flags"))
    uniq = len({r.get("notice") for r in ticks})
    # J-0126 (2026-08-24) — the decoupled-judge metaphor verdict is the metric of record for kill
    # criterion #1 (F-0016 found the keyword scan's own rate was a measurement artifact, not real
    # drift). Coverage is reported honestly: a tick where the judge panel was unavailable does not
    # silently count toward either side.
    # J-3117 (F-3837): the judge now also rules on a "flag" arm (ticks the random 1-in-4 draw skipped but
    # the free keyword scans flagged). That arm is deliberately biased toward the register the prompt
    # names, so EVERY rate below that must stay comparable with earlier reads and with kill criterion #1
    # (`metaphor_leak_rate_judged`, `metaphor_judge_coverage`, tiebreak rates, the hint-divergence leak)
    # is computed over the random arm only: rows with no `arm` key are "random". The flag arm gets its
    # own counts (`metaphor_flag_arm_n` / `metaphor_flag_arm_metaphor`), never merged into a rate.
    mj_judged = [r for r in ticks if (r.get("metaphor_judged") or {}).get("verdict") in ("metaphor", "literal")
                 and _metaphor_arm(r) != "flag"]
    _mj_flag_arm = [r for r in ticks if (r.get("metaphor_judged") or {}).get("verdict") in ("metaphor", "literal")
                    and _metaphor_arm(r) == "flag"]
    metaphor_flag_arm_n = len(_mj_flag_arm)
    metaphor_flag_arm_metaphor = sum(1 for r in _mj_flag_arm if r["metaphor_judged"]["verdict"] == "metaphor")
    metaphor_leak_rate_judged = (
        round(sum(1 for r in mj_judged if r["metaphor_judged"]["verdict"] == "metaphor") / len(mj_judged), 3)
        if mj_judged else None)
    # J-3119 (F-3840, P-0110): how often the judge's passage was cut, and which passage text (V1 legacy 500-cut
    # unlabelled / V2 labelled 1,500-cut) the judged rows rest on. Counts over the judged rows (random + flag arms)
    # that carry the key; rows logged before J-3119 have none and are not counted. None until a row carries it.
    _pc = [r["metaphor_judged"] for r in ticks
           if isinstance(r.get("metaphor_judged"), dict) and "passage_cut" in r["metaphor_judged"]
           and r["metaphor_judged"].get("verdict") in ("metaphor", "literal")]
    metaphor_passage_cut_rate = round(sum(1 for m in _pc if m.get("passage_cut")) / len(_pc), 3) if _pc else None
    metaphor_passage_v2_n = sum(1 for m in _pc if m.get("passage_v") == 2)
    # J-1456 (2026-09-27, F-2007's own named follow-up on F-1949: this judge's reliance on the granite
    # TIEBREAK) — ADDITIVE, option 3 of this job's own briefing ("leave TIEBREAK as-is, report
    # split_no_tiebreak's own rate in status(), so a hand-reader can see how often this judge's verdict
    # rests on a 2-family split at all"). Denominator is ticks where the two-family panel actually ran
    # (`metaphor_judged.how` present) — NOT `len(ticks)` (would silently count "empty passage"/"error"
    # short-circuits, which never called the panel at all, as if they were a clean "agreed" 0%) and NOT
    # `mj_judged` above (that set EXCLUDES every split, tiebroken or not, by construction — it only
    # holds verdict in {metaphor, literal}, and split_no_tiebreak's own verdict is always cannot_tell).
    # This is visibility-only, not a behavior change — see this job's own findings-log entry for why
    # neither of the other two options tested out: a live re-test of a metaphor-specific TIEBREAK
    # reminder prompt (option 2) made granite3.1-moe:3b WORSE, not better (15 of 16 known-split fixture
    # rows flipped to "true", including every one of the 7 scored LITERAL rows — a near-constant "yes"
    # classifier, not a fixed one), and option 1 (skip TIEBREAK, default the split to "literal") would
    # zero out this judge's entire measured recall outright: on the same 40-row fixture JUDGE_2
    # (falcon3:7b) answered "true" on 0 of 80 calls (old+new prompt combined), so every fixture-measured
    # true positive reaches a "metaphor" verdict only via TIEBREAK's own casting vote on a split.
    mh_covered = [r for r in ticks if (r.get("metaphor_judged") or {}).get("how") and _metaphor_arm(r) != "flag"]
    metaphor_tiebreak_rate = (
        round(sum(1 for r in mh_covered if r["metaphor_judged"]["how"] == "tiebreak") / len(mh_covered), 3)
        if mh_covered else None)
    metaphor_split_no_tiebreak_rate = (
        round(sum(1 for r in mh_covered if r["metaphor_judged"]["how"] == "split_no_tiebreak") / len(mh_covered), 3)
        if mh_covered else None)
    # §5 metric #2's actual instrument (F-0018) — share of ticks that named a topic absent from
    # world_fields. See `_invention_check`/`_TOPIC_FIELDS`.
    inv_flagged = sum(1 for r in ticks if (r.get("invention") or {}).get("invention_flag"))
    invented_topics = {}
    for r in ticks:
        for t in (r.get("invention") or {}).get("invented_topics") or []:
            invented_topics[t] = invented_topics.get(t, 0) + 1
    # F-1936 (J-1378, 2026-09-27) — the SAME metric computed with the pre-fix ("legacy") verdict, so a
    # chart of invention_rate_legacy stays ONE continuous series across the restart that ships this
    # fix, while invention_rate (above) shows the real, corrected step down — that contrast is the
    # "instrument change itself readable" goal, not two disconnected numbers. A row logged BEFORE this
    # job's restart never carries invention_flag_legacy/invented_topics_legacy at all (there was only
    # ever one verdict then, and it WAS this legacy computation) — falling back to the plain
    # invention_flag/invented_topics on those older rows is what keeps the series continuous instead
    # of reading as a data gap.
    inv_flagged_legacy = 0
    invented_topics_legacy = {}
    for r in ticks:
        inv = r.get("invention") or {}
        flag_legacy = inv["invention_flag_legacy"] if "invention_flag_legacy" in inv else inv.get("invention_flag")
        if flag_legacy:
            inv_flagged_legacy += 1
        topics_legacy = inv["invented_topics_legacy"] if "invented_topics_legacy" in inv else inv.get("invented_topics")
        for t in topics_legacy or []:
            invented_topics_legacy[t] = invented_topics_legacy.get(t, 0) + 1
    # J-3036 / F-3743 (P-0098) — the v2 invention verdict (skips the `uncertain` field, licenses topics from
    # the tick's own smells). A third series BESIDE invention_rate and invention_rate_legacy, for one restart
    # cycle. UNLIKE the legacy fallback above, rows logged before this job's restart carry no v2 verdict at
    # all and are NOT back-filled from the plain flag (that would put the very 10x overcount F-3743 found
    # into the v2 series), so the rate is over `inv_v2_covered` only -- the rows that carry the key -- and
    # `invention_v2_coverage` says how much of the window that is (0.0 until the restart that ships this).
    # The two `_on_v2_rows` rates run the current and legacy verdicts over those SAME rows, so the
    # before/after contrast is apples to apples, not v2-rows vs a mixed-era window.
    inv_v2_covered = [r for r in ticks if "invention_flag_v2" in (r.get("invention") or {})]
    inv_flagged_v2 = sum(1 for r in inv_v2_covered if r["invention"]["invention_flag_v2"])
    inv_flagged_cur_on_v2 = sum(1 for r in inv_v2_covered if r["invention"].get("invention_flag"))
    inv_flagged_legacy_on_v2 = sum(
        1 for r in inv_v2_covered
        if (r["invention"]["invention_flag_legacy"] if "invention_flag_legacy" in r["invention"]
            else r["invention"].get("invention_flag")))
    invented_topics_v2 = {}
    for r in inv_v2_covered:
        for t in r["invention"].get("invented_topics_v2") or []:
            invented_topics_v2[t] = invented_topics_v2.get(t, 0) + 1
    # F-1933 (J-1375, 2026-09-26) — the daylight-word slip instrument's own scoreboard. Denominator is
    # NIGHT ticks only (the honest base — F-1933's own "8 of 1,450 night ticks" is exactly this shape),
    # never all ticks, so a quiet instrument does not misread as an alarmingly low rate against the
    # wrong denominator. See `_daylight_word_slip_check`'s own docstring.
    night_rows = [r for r in ticks if (r.get("daylight_word_slip") or {}).get("night")]
    daylight_slip_n = sum(1 for r in night_rows if (r.get("daylight_word_slip") or {}).get("slip"))
    daylight_word_slip_rate = round(daylight_slip_n / len(night_rows), 3) if night_rows else None
    # §3.11's coherence pass (F-0017) — the second failure-guard, independent of the grounding gate.
    coh_verdicts = {}
    for r in ticks:
        v = (r.get("coherence") or {}).get("verdict")
        if v:
            coh_verdicts[v] = coh_verdicts.get(v, 0) + 1
    coh_judged = coh_verdicts.get("coherent", 0) + coh_verdicts.get("incoherent", 0)
    incoherence_rate = round(coh_verdicts.get("incoherent", 0) / coh_judged, 3) if coh_judged else None
    # J-3125 (F-3852): the same rate over ONLY the rows judged on the newest-first record (`hist_v` == 2, see
    # `_coherence_history`), so the metric can be read before/after that change instead of blended across it. The old
    # rows (no `hist_v`) were judged on a history that often hid the newest record. F-3853 still applies: place changes
    # dominate the incoherent verdicts, so neither rate is a meaningful incoherence measure on its own.
    coh_v2 = {}
    for r in ticks:
        c = r.get("coherence") or {}
        if c.get("hist_v") == 2 and c.get("verdict"):
            coh_v2[c["verdict"]] = coh_v2.get(c["verdict"], 0) + 1
    coh_v2_judged = coh_v2.get("coherent", 0) + coh_v2.get("incoherent", 0)
    incoherence_rate_v2 = round(coh_v2.get("incoherent", 0) / coh_v2_judged, 3) if coh_v2_judged else None
    # J-3126 (F-3853): the same rate split by whether the observer MOVED since the newest stored record
    # (`coherence_moved`: 'place' / 'standpoint' / 'same'). The pooled `incoherence_rate` above is dominated by place
    # changes: on the 10-29 window the judge called 46 percent of 61 place-move ticks incoherent against 7 percent of
    # 256 ticks that stayed put (F-3853), so read the split, not the pooled number. Rows WITHOUT the key (logged before
    # J-3126) and rows whose value is None (no comparable previous entry) are excluded from every bucket -- never
    # counted as 'same'. `n` is the judged (coherent + incoherent) count in the bucket, `rows` all rows tagged so.
    incoherence_by_move = {}
    for mv in ("place", "standpoint", "same"):
        mv_rows = [r for r in ticks if r.get("coherence_moved") == mv]
        mv_inc = sum(1 for r in mv_rows if (r.get("coherence") or {}).get("verdict") == "incoherent")
        mv_n = mv_inc + sum(1 for r in mv_rows if (r.get("coherence") or {}).get("verdict") == "coherent")
        incoherence_by_move[mv] = {"rate": round(mv_inc / mv_n, 3) if mv_n else None,
                                   "n": mv_n, "incoherent": mv_inc, "rows": len(mv_rows)}
    # J-3127 (F-3854): reader for the coherence judge's `why`. Of the rows judged coherent / incoherent that were asked for a
    # reason (the key `why` is PRESENT on the dict, even if None), how many carried a non-empty one. Rows logged before
    # J-3127 have no `why` key and are excluded from both numbers. Job target: at least 0.9 once the build is live.
    coh_why_rows = [r for r in ticks if "why" in (r.get("coherence") or {})
                    and (r.get("coherence") or {}).get("verdict") in ("coherent", "incoherent")]
    coh_why_n = sum(1 for r in coh_why_rows if str((r.get("coherence") or {}).get("why") or "").strip())
    coherence_why_coverage = {"rate": round(coh_why_n / len(coh_why_rows), 3) if coh_why_rows else None,
                              "with_why": coh_why_n, "judged": len(coh_why_rows)}
    verdicts = {}
    for r in ticks:
        v = r.get("prior_verdict")
        # F-1958/J-1396 — 'unjudgeable' (no panel call ever happened, by design) is deliberately NOT
        # folded in here: `predictions_judged`/`prediction_verdicts` have always meant "the panel
        # weighed in", and this job's whole point is to STOP calling the panel on a moved prediction,
        # not to relabel that skipped call as a kind of judgement. See `unjudgeable_moved_24h` below
        # for its own dedicated, separately-reported count.
        if v and v not in ("none", "unjudgeable", "retry"):      # J-3100: 'retry' is a marker, not a verdict
            verdicts[v] = verdicts.get(v, 0) + 1
    n_pred = sum(verdicts.values())
    # F-1949/J-1386 (2026-09-27) — the prediction scoreboard's own corrected reading, dual-reported
    # for "one restart cycle" per this job's own pre-registration (see `_judge_prior`'s docstring for
    # the full root cause). `broke_share` is the LEGACY figure: the same broke/(held+broke) formula
    # every prior hand-read of this number used (unsettled/cannot_tell/none excluded from the
    # denominator, same convention `_split_stats` below already models) — left unchanged so it stays
    # continuous with docs/plans/lane2_the_witness.md's own historical 0.66/0.688-style figures, but
    # during the transition it still blends pre-fix rows (where "broke" meant bare held=false) with
    # post-fix ones (where it means confirmed contradicted=true). `broke_share_strict` counts ONLY
    # rows that actually went through the new second ask (`prior_contradicted_how` set — a marker
    # that cannot exist on any row logged before this job), so it reads correctly from the first
    # post-restart row instead of waiting for the whole tail window to roll over; its own `_n` is
    # reported alongside it since its denominator shrinks honestly rather than silently. Once the two
    # figures converge (every "broke" row in the tail window is post-fix), a future job can drop the
    # legacy one. `unsettled_share` operationalizes this job's own pre-registration ("unsettled should
    # absorb most of what tiebreaks used to call broke") so it is a live status() read, not another
    # hand-parse of the log.
    held_n, broke_n, unsettled_n = verdicts.get("held", 0), verdicts.get("broke", 0), verdicts.get("unsettled", 0)
    broke_share = round(broke_n / (held_n + broke_n), 3) if (held_n + broke_n) else None
    strict_broke_n = sum(1 for r in ticks
                          if r.get("prior_verdict") == "broke" and r.get("prior_contradicted_how"))
    broke_share_strict = (round(strict_broke_n / (held_n + strict_broke_n), 3)
                           if (held_n + strict_broke_n) else None)
    unsettled_share = (round(unsettled_n / (held_n + broke_n + unsettled_n), 3)
                        if (held_n + broke_n + unsettled_n) else None)
    # F-1958/J-1396 (2026-09-27) — the moved-pairs fix's own dual-reported figure, "for one restart
    # cycle" per this job's own pre-registration, same convention `broke_share_strict` above already
    # established for the J-1386 fix one job before this one. Counts ONLY rows carrying
    # `prior_judgeability` in ('matched-standpoint', 'matched-place') — a marker that cannot exist on
    # any row logged before this job, so (like `broke_share_strict`) it reads correctly from the very
    # first post-restart row rather than waiting for the whole tail window to roll over.
    # `matched-legacy` rows are deliberately EXCLUDED: a legacy row's own "same place" was never
    # actually verified, only assumed permissively (see `_prediction_judgeability`'s own docstring), so
    # counting it here would quietly launder an unverified match into a "verified same-place" figure.
    # Once `broke_share` above and this converge (every "broke"/"held" row in the tail window is
    # post-fix), a future job can drop whichever of the two legacy figures — `broke_share` for the
    # J-1386 fix, this one — is by then redundant.
    sp_held_n = sum(1 for r in ticks if r.get("prior_verdict") == "held"
                     and r.get("prior_judgeability") in ("matched-standpoint", "matched-place"))
    sp_broke_n = sum(1 for r in ticks if r.get("prior_verdict") == "broke"
                      and r.get("prior_judgeability") in ("matched-standpoint", "matched-place"))
    broke_share_same_place = (round(sp_broke_n / (sp_held_n + sp_broke_n), 3)
                               if (sp_held_n + sp_broke_n) else None)
    named_unc = sum(1 for r in ticks
                    if (r.get("uncertain") or "").strip()
                    and "nothing unsettled" not in (r.get("uncertain") or "").lower())
    # F-1938/J-1380 (2026-09-27) — the `uncertain` field's own collapse (verified: 59% "exact time"
    # template, 0.69 distinct share, 85 rows echo law 3's own wording verbatim, 78 empty) was invisible
    # to every metric above; three of its four new siblings below (`uncertain_distinct_share_24h` is
    # the fourth, a real-24h window — see `ticks_24h` further down). Same tail_rows(_LOG, 2000) window
    # `named_unc` just above already rides. Deliberately NOT changing `_SYSTEM`'s own law-3 prompt text
    # here (this job's own briefing) — that field's future is docs/staged/lane2_curiosity.md's call.
    # `_LAW3_ECHO_PHRASE` is law 3's own core sentence (`_SYSTEM` above), the pronoun word ("your"/"my
    # senses") deliberately left off the end so this still matches a row logged under either side of
    # J-1412's 2026-09-27 your->my pronoun change, rather than hardcoding a second full copy of the
    # sentence under one specific era that could drift from the live prompt.
    _LAW3_ECHO_PHRASE = "how long something has been so, what caused it, what is outside"
    uncertain_echo_n = sum(1 for r in ticks if _LAW3_ECHO_PHRASE in (r.get("uncertain") or "").lower())
    uncertain_prompt_echo_rate = round(uncertain_echo_n / len(ticks), 3)
    uncertain_empty_n = sum(1 for r in ticks if not (r.get("uncertain") or "").strip())
    uncertain_empty_rate = round(uncertain_empty_n / len(ticks), 3)
    uncertain_exact_time_n = sum(1 for r in ticks if "exact time" in (r.get("uncertain") or "").lower())
    uncertain_exact_time_share = round(uncertain_exact_time_n / len(ticks), 3)
    # D-0281 (§8.2, 2026-09-26) — the notice's own claim-correctness scoreboard, the sibling to
    # `verdicts`/`n_pred` above but for the NOTICE instead of the prediction. `notice_judged` is
    # "not_sampled" on ticks NOTICE_JUDGE_SAMPLE_P skipped (3-in-4, by design — not a coverage gap to
    # chase) and {"verdict": ..., "how": ...} on the 1-in-4 it ran. Coverage is split the same honest
    # way `metaphor_judge_coverage` already models: sample rate (did we even ask, ~0.25 expected) is
    # reported separately from judge coverage (did the panel answer, among the ticks we asked).
    notice_rows = [r.get("notice_judged") or {} for r in ticks]
    notice_verdicts = {}
    for r in notice_rows:
        v = r.get("verdict")
        if v:
            notice_verdicts[v] = notice_verdicts.get(v, 0) + 1
    notice_sampled_n = sum(1 for r in notice_rows if r.get("verdict") != "not_sampled")
    notice_judged_rows = [r for r in notice_rows if r.get("verdict") in ("contradiction", "consistent")]
    notice_judged_n = len(notice_judged_rows)
    notice_contradiction_rate = (
        round(sum(1 for r in notice_judged_rows if r["verdict"] == "contradiction") / notice_judged_n, 3)
        if notice_judged_n else None)
    # D-0361(a) (J-1896) -- the deterministic checker's scoreboard, the sibling of the panel's just above. Rates
    # are over ticks the checker actually answered (`not_checked` = empty notice / no percept text / error).
    # `solid` excludes weak flags (a neighbouring band word, or a quantity word up to 0.10 above the top of its range).
    # `paired` = only the ticks the panel judge also answered, the apples-to-apples comparison with
    # `notice_contradiction_rate`.
    chk_rows = [(r.get("notice_checked") or {}, r.get("notice_judged") or {}) for r in ticks]
    chk_answered = [c for c, _j in chk_rows if c.get("verdict") in ("contradiction", "consistent")]
    notice_checked_n = len(chk_answered)
    notice_checked_flagged_n = sum(1 for c in chk_answered if c["verdict"] == "contradiction")
    notice_checked_solid_n = sum(1 for c in chk_answered if c.get("n_solid"))
    chk_paired = [c for c, j in chk_rows if c.get("verdict") in ("contradiction", "consistent")
                  and j.get("verdict") in ("contradiction", "consistent")]
    notice_checked_paired_n = len(chk_paired)
    notice_checked_paired_flagged_n = sum(1 for c in chk_paired if c["verdict"] == "contradiction")
    # D-0417 (J-2102) -- the invention-class scoreboard: rate over ticks the unsupported check answered
    # (how == "deterministic"); rows logged before this build carry no `notice_unsupported` key and are not counted.
    uns_answered = [r.get("notice_unsupported") for r in ticks
                    if (r.get("notice_unsupported") or {}).get("how") == "deterministic"]
    notice_unsupported_n = len(uns_answered)
    notice_unsupported_flagged_n = sum(1 for u in uns_answered if u.get("flag"))
    notice_unsupported_nouns = {}
    for u in uns_answered:
        for nn in u.get("nouns") or []:
            notice_unsupported_nouns[nn] = notice_unsupported_nouns.get(nn, 0) + 1
    notice_checked_kinds = {}
    for c in chk_answered:
        for f in c.get("flags") or []:
            notice_checked_kinds[f.get("kind")] = notice_checked_kinds.get(f.get("kind"), 0) + 1
    # J-1371 (F-1931, §8.1) — the per-tick generation-latency instrument. Windowed to a REAL 24h,
    # unlike every other metric above (which rides the tail_rows(_LOG, 2000) window as-is): the
    # field names say "_24h" and D-0058's defeater is about load over a specific recent stretch, not
    # "however many rows the HUD's bounded read happens to cover". Rows logged before this job carry
    # no `gen_s` key at all, so `.get("gen_s") is not None` also doubles as the pre/post-J-1371
    # boundary — no separate flag needed.
    _now_ts = time.time()

    def _pctl(vals, p):
        """Linear-interpolation percentile (p in [0,1]) over an already-sorted list. No `statistics`
        import — this file has none today and every other stat here is hand-rolled the same way."""
        if not vals:
            return None
        if len(vals) == 1:
            return round(vals[0], 3)
        k = (len(vals) - 1) * p
        f, c = int(k), min(int(k) + 1, len(vals) - 1)
        if f == c:
            return round(vals[f], 3)
        return round(vals[f] + (vals[c] - vals[f]) * (k - f), 3)

    gen_s_24h = sorted(r["gen_s"] for r in ticks
                        if r.get("gen_s") is not None and (_now_ts - float(r.get("ts") or 0)) <= 86400.0)
    gen_s_median_24h = _pctl(gen_s_24h, 0.5)
    gen_s_p95_24h = _pctl(gen_s_24h, 0.95)

    # F-1958/J-1396 — this job's own briefing names this field by exactly this name. Real 24h window,
    # same convention as `gen_s_median_24h` immediately above (not the tail_rows(_LOG, 2000) window the
    # rest of status() rides as-is) — a count of predictions closed `unjudgeable`/`moved` (grace expired
    # with no standpoint/place match) without ever reaching the judge panel. Zero on every row logged
    # before this job (the verdict value did not exist), so this reads as a true, not a padded, zero
    # until the first real one is closed post-restart.
    # F-1956/J-1394 (2026-09-27) CORRECTION: this field's own name and comment always meant the MOVED
    # cause specifically — accurate when `prior_verdict == "unjudgeable"` had only one possible cause,
    # which this job ends by adding a second (`prior_judged_how == "field-absent"`, see
    # `_prediction_field_ok`). Left unfiltered, this field would silently start counting BOTH causes
    # under a name that still says only one — exactly the "narrow/widen an existing field's meaning
    # without saying so" trap this plan's own discipline forbids, so the explicit `prior_judged_how`
    # check is added here (not left implicit) the moment a second cause exists. Its own sibling,
    # `unjudgeable_field_absent_24h`, is the new cause's matching count; `unjudgeable_rate_24h` is the
    # combined rate (see both immediately below).
    unjudgeable_moved_24h = sum(1 for r in ticks if r.get("prior_verdict") == "unjudgeable"
                                 and r.get("prior_judged_how") == "moved"
                                 and (_now_ts - float(r.get("ts") or 0)) <= 86400.0)
    # F-1956/J-1394 — the field-absence gate's own sibling count, same real-24h-window convention as
    # `unjudgeable_moved_24h` immediately above. Zero on every row logged before this job (the
    # `judged_how` value did not exist), same honest-not-padded zero as its sibling already models.
    unjudgeable_field_absent_24h = sum(1 for r in ticks if r.get("prior_verdict") == "unjudgeable"
                                        and r.get("prior_judged_how") == "field-absent"
                                        and (_now_ts - float(r.get("ts") or 0)) <= 86400.0)
    # J-3035 / D-0548 -- the two NEW closures' own counters, same real-24h window and honest-zero convention
    # as the two siblings above. `unjudgeable_stale_24h`: predictions closed 'expired-stale' (judged later
    # than `_STALE_AFTER_S` past due, or Du slept inside the wait). `unjudgeable_moved_place_24h`: closed
    # 'moved' although the STANDPOINT matched, i.e. the cases only the new place-equality gate closes
    # (derived from the row's own logged `judged_pred_standpoint`/`standpoint`/`judged_pred_place`/`place`).
    unjudgeable_stale_24h = sum(1 for r in ticks if r.get("prior_verdict") == "unjudgeable"
                                 and r.get("prior_judged_how") == "expired-stale"
                                 and (_now_ts - float(r.get("ts") or 0)) <= 86400.0)
    unjudgeable_moved_place_24h = sum(
        1 for r in ticks if r.get("prior_verdict") == "unjudgeable" and r.get("prior_judged_how") == "moved"
        and r.get("judged_pred_standpoint") is not None
        and r.get("judged_pred_standpoint") == r.get("standpoint")
        and r.get("judged_pred_place") is not None and r.get("judged_pred_place") != r.get("place")
        and (_now_ts - float(r.get("ts") or 0)) <= 86400.0)
    # J-3160 / D-0548 -- trivial predictions kept out of the store in the last 24 h (one skip row each).
    trivial_excluded_24h = sum(1 for r in rows if r.get("kind") == "skip" and r.get("skip") == "trivial-excluded"
                                and (_now_ts - float(r.get("ts") or 0)) <= 86400.0)
    # unjudgeable_rate_24h — THE metric this job's own briefing names and pre-registers against: of
    # every prediction actually CLOSED (held/broke/unsettled/cannot_tell/unjudgeable — "none" excluded,
    # that means "no due prediction this tick at all", not a closure) in a real last-24h window, what
    # share closed unjudgeable for EITHER cause above, without ever reaching the panel. Read alongside
    # `broke_share`/`broke_share_strict`: this job's own pre-registration is that those should fall by
    # roughly the share this reads, once field-absent rows start accruing post-restart — this is the
    # live number a future read checks that against, not a re-run of this job's own one-off replay
    # script (`scratchpad/check_J-1394_replay.py`). `broke_share`'s own denominator (held+broke) already
    # excludes "unjudgeable" exactly like "cannot_tell" (unchanged by this job — see the `verdicts`
    # dict computation above), so no separate correction was needed there.
    closed_n_24h = sum(1 for r in ticks
                        if r.get("prior_verdict") in ("held", "broke", "unsettled", "cannot_tell", "unjudgeable")
                        and (_now_ts - float(r.get("ts") or 0)) <= 86400.0)
    unjudgeable_n_24h = sum(1 for r in ticks if r.get("prior_verdict") == "unjudgeable"
                             and (_now_ts - float(r.get("ts") or 0)) <= 86400.0)
    unjudgeable_rate_24h = round(unjudgeable_n_24h / closed_n_24h, 3) if closed_n_24h else None
    # J-3100 / F-3818 -- the retry-on-timeout read (zero everywhere while JUDGE_RETRY_ON_TIMEOUT is off). 'retry' rows
    # are in no share (excluded from `verdicts` above and absent from `closed_n_24h`'s tuple). Of the re-asked
    # predictions that closed in the window: how many got a real ruling vs were lost to a second timeout. Read over `rows`
    # (tick rows AND the no-output skip rows that mirror prior_verdict), since a re-ask can land on either.
    judge_retry_24h = sum(1 for r in rows if r.get("prior_verdict") == "retry"
                          and (_now_ts - float(r.get("ts") or 0)) <= 86400.0)
    judge_retry_resolved_24h = sum(1 for r in rows if r.get("prior_judge_retries")
                                   and r.get("prior_verdict") in ("held", "broke", "unsettled")
                                   and (_now_ts - float(r.get("ts") or 0)) <= 86400.0)
    judge_retry_lost_24h = sum(1 for r in rows if r.get("prior_judge_retries")
                               and r.get("prior_verdict") == "cannot_tell"
                               and (_now_ts - float(r.get("ts") or 0)) <= 86400.0)
    # expect_is_plan_rate_24h — the generation-time sibling: share of ALL ticks (same "over every tick"
    # denominator `question_expect_rate` already uses for its own would-be-a-prediction rate, just
    # real-24h-windowed like this job's own fields above rather than the tail_rows(2000) window
    # `question_expect_rate` rides) whose `expect_next` was flagged plan-shaped (`_plan_shaped_flag`)
    # and therefore never stored as a prediction at all (see the store-append guard in `tick()`). Zero
    # on every row logged before this job, same honest-not-padded convention as every other new-key
    # rate in this file.
    ticks_24h = [r for r in ticks if (_now_ts - float(r.get("ts") or 0)) <= 86400.0]
    expect_is_plan_rate_24h = (round(sum(1 for r in ticks_24h if r.get("expect_is_plan")) / len(ticks_24h), 3)
                                if ticks_24h else None)
    # F-1938/J-1380 — this job's briefing names this ONE `uncertain`-field sibling with the "_24h"
    # suffix (its three siblings just above read the plain tail_rows(2000) window instead) — real-24h
    # windowed off `ticks_24h` immediately above, same convention `expect_is_plan_rate_24h` just above
    # already uses. `distinct_expect_share` (in the return dict below) is the direct precedent this
    # formula is copied from, substituting `uncertain` for `expect_next`.
    uncertain_distinct_share_24h = (
        round(len({r.get("uncertain") for r in ticks_24h}) / len(ticks_24h), 3) if ticks_24h else None)
    # F-1938/J-1380 — briefing item 5, "notice_words_median_24h": notice length has grown by seat (qwen
    # 30 / command-r7b 42 / deepseek 47 median words, F-1938's own count) and nothing reads it live.
    # Reuses `_pctl` (defined above for `gen_s_median_24h`) rather than a second percentile method, and
    # the same real-24h window every other "_24h" field on this page uses.
    notice_words_24h = sorted(len((r.get("notice") or "").split()) for r in ticks_24h)
    notice_words_median_24h = _pctl(notice_words_24h, 0.5)

    # D-0284 (J-1413, 2026-09-27) — the shadow-first read of the Weather's commit_threshold gate on
    # the prediction store (see `tick()`'s own `would_withhold` computation, right before its `rec` is
    # built, for exactly what this compares and why it is scoped the way it is). Coverage-honest, same
    # convention `figurative_flag_rate`/`notice_judge_coverage` already model in this file: only rows
    # that CARRY the key are in `wwh_covered` (zero on every row logged before this job — the key did
    # not exist), and only rows where the comparison actually applied (a real candidate prediction with
    # a real `grounded_share`) are in `wwh_scored` — a bare `r.get("would_withhold")` truthiness count
    # would misread both "not a candidate tick" and "no data yet" as a counted False. D-0284's own
    # defeater ("5%-60% of ticks over 7 days") is read off `would_withhold_rate` once a real week of
    # post-restart ticks has rolled through this same tail_rows(_LOG, 2000) "weekly" window
    # `hint_divergence` below already uses for its own law-6 audit — not a fresh real-7d clock, the
    # same choice this file already makes for every other weekly-grain read here.
    wwh_covered = [r for r in ticks if "would_withhold" in r]
    wwh_scored = [r for r in wwh_covered if r.get("would_withhold") is not None]
    would_withhold_n = sum(1 for r in wwh_scored if r.get("would_withhold"))
    would_withhold_rate = round(would_withhold_n / len(wwh_scored), 3) if wwh_scored else None

    # F-1937/J-1379 (2026-09-27) — `skips` below already counts HOW MANY rows skipped as
    # "no-output"; this is WHY, now that `_ask` returns a `cause` and `tick()` carries it onto the
    # skip row (see both their own docstrings/comments). Real 24h window, same convention
    # `gen_s_median_24h`/`unjudgeable_moved_24h` immediately above already use (not the
    # tail_rows(_LOG, 2000) window `skips` rides as-is) — F-1937's own 19% figure was a dated
    # snapshot of a live rate, not a fixed count, so this should track the same real clock any fix
    # is measured against. Reads over `rows`, not `ticks` (a skip row is never a tick row). Empty
    # count for every no-output row logged before this job (no `cause` key existed yet) — an honest
    # gap, not a fabricated zero, same backward-compat pattern `gen_s`/`percept_lines` model
    # elsewhere in this file.
    no_output_by_cause_24h = {}
    for r in rows:
        if (r.get("kind") == "skip" and r.get("skip") == "no-output"
                and (_now_ts - float(r.get("ts") or 0)) <= 86400.0):
            _c = r.get("cause") or "unknown"
            no_output_by_cause_24h[_c] = no_output_by_cause_24h.get(_c, 0) + 1

    # ── J-0165 — the Tap-on-the-Shoulder's own instruments (§5 metrics #5/#6) ──────────────────
    hint_ticks = [r for r in ticks if r.get("hint")]
    unhint_ticks = [r for r in ticks if not r.get("hint")]

    def _mean_of(rows, path):
        vals = [path(r) for r in rows]
        vals = [v for v in vals if v is not None]
        return round(sum(vals) / len(vals), 3) if vals else None

    # J-1371 (F-1931, §8.3, constitutional law 6) — the two standing boundary audits, now computed
    # every status() call instead of by hand, over this same tail_rows window (~7 days at the current
    # TICK_S=300 cadence — 2000 rows / ~288 ticks/day — the same "weekly" grain §7.6 already reads
    # every other metric at; no separate real-time cutoff here, unlike gen_s_*_24h above, since law
    # 6's own audits are about the realized channel over a real window of operation, not a fixed
    # clock). Exact shape and computation match F-1931's own by-hand read: split on the presence of
    # the per-tick `hint` field, then grounded_share (mean), broke_share (of judged predictions,
    # excluding cannot_tell/none — same convention `verdicts`/`prediction_verdicts` above use),
    # distinct expect_next share, and metaphor leak among JUDGED rows only (never against all rows —
    # same honesty convention `metaphor_leak_rate_judged` above already models).
    def _split_stats(rows):
        n = len(rows)
        if not n:
            return {"n": 0, "grounded": None, "broke_share": None,
                     "distinct_expect": None, "metaphor_leak": None}
        held = sum(1 for r in rows if r.get("prior_verdict") == "held")
        broke = sum(1 for r in rows if r.get("prior_verdict") == "broke")
        mj = [r for r in rows if (r.get("metaphor_judged") or {}).get("verdict") in ("metaphor", "literal")
              and _metaphor_arm(r) != "flag"]      # J-3117: random arm only, like metaphor_leak_rate_judged
        return {
            "n": n,
            "grounded": _mean_of(rows, lambda r: (r.get("grounding") or {}).get("grounded_share")),
            "broke_share": round(broke / (held + broke), 3) if (held + broke) else None,
            "distinct_expect": round(len({r.get("expect_next") for r in rows}) / n, 3),
            "metaphor_leak": (round(sum(1 for r in mj if r["metaphor_judged"]["verdict"] == "metaphor")
                                    / len(mj), 3) if mj else None),
        }

    hint_divergence = {"hinted": _split_stats(hint_ticks), "plain": _split_stats(unhint_ticks)}
    _hint_kind_counts, _hint_topics_seen = {}, set()
    for _r in hint_ticks:
        _h = _r.get("hint") or {}
        if _h.get("kind"):
            _hint_kind_counts[_h["kind"]] = _hint_kind_counts.get(_h["kind"], 0) + 1
        if _h.get("topic"):
            _hint_topics_seen.add(_h["topic"])
    hint_flow = {"kinds": _hint_kind_counts, "topics": len(_hint_topics_seen)}

    hints_state = _load_hints()
    hq = hints_state.get("queue") or []
    # Dosed Coupling / Lane 2 Phase 1 (D-0241 shadow-first, J-1161) — the §7.6 P1-1..P1-6 metric
    # sheet, lazy-imported and fail-open so a missing/broken module never breaks this status() call.
    try:
        from core import lane2_break_habituation as _hab_status
        _phase1 = _hab_status.phase1_metric_sheet()
    except Exception:
        _phase1 = None
    try:
        _wonder = _wonder_metric_sheet()
    except Exception:
        _wonder = None
    # D-0285 (2026-09-27) — §2.8c's knowledge tier, SHADOW-ONLY read for the HUD/pulse (step 4/the
    # live prompt flip is a SEPARATE, later, restart-gated job per the ruling — nothing here has
    # reached `percept_lines()`/`_ask()`). A small, bounded extra file read (`_load_store()` — the
    # same store `tick()` already loads/saves, never scanned or grown here), consistent with the
    # `hints_state`/`_phase1`/`_wonder` reads immediately above; fail-open like all three.
    try:
        _knowledge = _load_store().get("knowledge") or []
    except Exception:
        _knowledge = []
    # coverage-honest, same convention `figurative_flag_rate`/`figurative_flag_coverage` already
    # model: `would_show_knowledge` is a brand-new per-tick key (absent on every row logged before
    # this job, or before Du's next restart picks it up) — a bare truthiness count over `len(ticks)`
    # would misread "no rows carry the key yet" as "never anything worth showing".
    wsk_covered = [r for r in ticks if "would_show_knowledge" in r]
    wsk_hit = sum(1 for r in wsk_covered if r.get("would_show_knowledge"))
    return {"ticks": len(ticks), "skips": skips,
            # F-1937/J-1379 — see the computation above for exactly what this counts and why it is
            # real-24h-windowed while `skips` just above rides the tail_rows(_LOG, 2000) window as-is.
            "no_output_by_cause_24h": no_output_by_cause_24h,
            "mean_grounded_share": round(sum(g) / len(g), 3) if g else None,
            "metaphor_leak_rate": round(flagged / len(ticks), 3),   # keyword-scan diagnostic only (F-0016)
            "metaphor_leak_rate_judged": metaphor_leak_rate_judged,   # metric #1 OF RECORD (J-0126)
            "metaphor_judge_coverage": round(len(mj_judged) / len(ticks), 3),
            # J-3117 (F-3837, P-0110) -- ADDITIVE. The flag arm: ticks the random draw skipped that the free
            # keyword scans flagged, judged anyway (judge stays blind). Counts only, NEVER a rate merged into
            # metaphor_leak_rate_judged above. `_n` = flag-arm ticks with a metaphor/literal verdict,
            # `_metaphor` = how many of those the judge called metaphor; hand-label them to get the flag
            # arm's precision, the quantity of interest. 0/0 until Du restarts onto this code.
            "metaphor_flag_arm_n": metaphor_flag_arm_n,
            "metaphor_flag_arm_metaphor": metaphor_flag_arm_metaphor,
            # J-3119 (F-3840, P-0110) -- ADDITIVE: share of judged rows whose passage hit the cap, and how many of
            # the keyed rows were judged on the V2 (labelled, 1,500) text; a series break marker, never a rate input.
            "metaphor_passage_cut_rate": metaphor_passage_cut_rate,
            "metaphor_passage_v2_n": metaphor_passage_v2_n,
            # J-1456 (2026-09-27) — ADDITIVE, option 3 of F-2007's own named follow-up (F-1949): how
            # often this judge's verdict rests on TIEBREAK's own casting vote, and how often even
            # TIEBREAK itself failed to answer a real split. Read ALONGSIDE metaphor_leak_rate_judged
            # above, never merged into it (same "visible, not converged away" convention
            # figurative_flag_rate below models against it). Both `None` until Du's next restart picks
            # up `metaphor_judged.how` on real ticks (same coverage-honesty idiom as everywhere else in
            # this function) — see the `mh_covered` computation above for exactly what denominator this
            # is and why, and this job's findings-log entry for the real fixture evidence behind it.
            "metaphor_tiebreak_rate": metaphor_tiebreak_rate,
            "metaphor_split_no_tiebreak_rate": metaphor_split_no_tiebreak_rate,
            # F-1951/J-1388 (2026-09-27) — cheap keyword scan over F-1951's own ambient-mood register
            # (`_figurative_flags`), read ALONGSIDE `metaphor_leak_rate_judged` above, never merged
            # into it — "so the judge and a keyword scan can disagree visibly" (this job's own
            # briefing). Diagnostic only, same honesty label as `metaphor_leak_rate`. `None`/0.0 until
            # Du's next restart (see `fig_covered`'s own comment above) — `figurative_flag_coverage`
            # is what tells "no figurative language yet" apart from "no rows carry the key yet".
            "figurative_flag_rate": (round(figurative_flagged / len(fig_covered), 3)
                                       if fig_covered else None),
            "figurative_flag_coverage": round(len(fig_covered) / len(ticks), 3),
            "invention_rate": round(inv_flagged / len(ticks), 3),   # metric #2 OF RECORD (J-0126, F-0018)
            "invented_topics": invented_topics,
            # F-1936 (J-1378, 2026-09-27) — the pre-fix computation, read ALONGSIDE invention_rate
            # above for one restart cycle so the step down at the fix is legible against the series it
            # replaces, never merged into it. See _invention_check's own docstring for exactly what
            # changed and why (a sound naming the topic, or the sun family's own daylight phase, no
            # longer counts as invented) and inv_flagged_legacy's comment above for the continuity
            # fallback on rows logged before this fix shipped.
            "invention_rate_legacy": round(inv_flagged_legacy / len(ticks), 3),
            "invented_topics_legacy": invented_topics_legacy,
            # J-3036 / F-3743 (P-0098) -- the v2 series, rate over rows that carry the key (None until the
            # restart that ships it). See inv_v2_covered's comment above. Plan metric 2's prediction and
            # the metric of record stay `invention_rate`; this is a reading beside it, not a replacement.
            "invention_rate_v2": (round(inv_flagged_v2 / len(inv_v2_covered), 3) if inv_v2_covered else None),
            "invention_v2_n": len(inv_v2_covered),
            "invention_v2_coverage": round(len(inv_v2_covered) / len(ticks), 3),
            "invention_rate_on_v2_rows": (round(inv_flagged_cur_on_v2 / len(inv_v2_covered), 3)
                                          if inv_v2_covered else None),
            "invention_rate_legacy_on_v2_rows": (round(inv_flagged_legacy_on_v2 / len(inv_v2_covered), 3)
                                                 if inv_v2_covered else None),
            "invented_topics_v2": invented_topics_v2,
            # F-1933 (J-1375, 2026-09-26) — cheap deterministic instrument, no judge call (rate is
            # over night ticks only; see the computation above for why). `_n`/`_night_ticks` are the
            # raw numerator/denominator, the same honesty convention `notice_judged_n` already models.
            "daylight_word_slip_rate": daylight_word_slip_rate,
            "daylight_word_slip_n": daylight_slip_n,
            "daylight_word_slip_night_ticks": len(night_rows),
            "coherence_verdicts": coh_verdicts,   # §3.11 pass (J-0126, F-0017)
            "incoherence_rate": incoherence_rate,
            "coherence_verdicts_v2": coh_v2,         # J-3125: only rows judged on the newest-first record
            "incoherence_rate_v2": incoherence_rate_v2,
            # J-3126 (F-3853): incoherence_rate split by 'place' / 'standpoint' / 'same' move since the newest stored
            # record. The POOLED rate above is dominated by place changes (46 percent incoherent on a move vs 7
            # percent staying put, F-3853) -- read this split instead. Old rows without `coherence_moved` are excluded.
            "incoherence_by_move": incoherence_by_move,
            "coherence_why_coverage": coherence_why_coverage,
            "distinct_notice_share": round(uniq / len(ticks), 3),   # repetition/staleness (metric #3)
            "distinct_expect_share": round(len({r.get("expect_next") for r in ticks}) / len(ticks), 3),
            # J-0651 (F-0926) — the per-topic cut of the aggregate line above, so a topic-concentrated
            # template lock (the tide topic, F-0926) doesn't hide inside a moderate-looking average.
            # See `_distinct_share_by_topic`'s own docstring for what it buckets on and why.
            "distinct_expect_share_by_topic": _distinct_share_by_topic(ticks),
            "question_expect_rate": round(
                sum(1 for r in ticks if r.get("expect_is_question")) / len(ticks), 3),
            "named_uncertainty_rate": round(named_unc / len(ticks), 3),
            **_j3041_instruments(ticks),   # J-3041 / F-3745: new keys only, see helper
            # F-1938/J-1380 (2026-09-27) — output hygiene bundle: the `uncertain` field's own collapse
            # (templated, echoed, or empty) was invisible to every metric above; see the computation
            # above (near `named_unc`/`ticks_24h`) for exactly what each of these five counts and why
            # only one carries the "_24h" suffix. `notice_words_median_24h` is this same job's fifth,
            # otherwise-unrelated item (briefing item 5) — grouped here with its siblings rather than
            # off by `gen_s_median_24h` below, since all five shipped together in the one hygiene job.
            "uncertain_prompt_echo_rate": uncertain_prompt_echo_rate,
            "uncertain_empty_rate": uncertain_empty_rate,
            "uncertain_exact_time_share": uncertain_exact_time_share,
            "uncertain_distinct_share_24h": uncertain_distinct_share_24h,
            "notice_words_median_24h": notice_words_median_24h,
            # THE PREDICTION TIER'S OWN SCOREBOARD — is it making claims the world can settle, and how
            # often does it turn out right? A tier that never breaks is not predicting, it is describing.
            "predictions_judged": n_pred, "prediction_verdicts": verdicts,
            # J-3101 / F-3813 (P-0109) — ADDITIVE: the same judged rows split by claim class, so the held
            # share stops reading as skill. Instrument only; see `_claim_class_split`.
            "prediction_claim_class": _claim_class_split(ticks),
            # F-1949/J-1386 — see the computation above for exactly what "legacy"/"strict" mean and
            # why both are reported. THE metric of record going forward is `broke_share_strict`.
            "broke_share": broke_share,
            "broke_share_strict": broke_share_strict, "broke_share_strict_n": strict_broke_n,
            "unsettled_share": unsettled_share,
            # F-1958/J-1396 — read this alongside `broke_share`/`broke_share_strict` above for one
            # restart cycle (see its own computation above for exactly what it counts and why).
            "broke_share_same_place": broke_share_same_place,
            "broke_share_same_place_n": sp_held_n + sp_broke_n,
            # F-1958/J-1396 — a count, real 24h window (see its own computation above, including this
            # job's own `prior_judged_how` correction); excluded from every ratio above the same way
            # `cannot_tell` already is, exactly per this job's briefing.
            "unjudgeable_moved_24h": unjudgeable_moved_24h,
            # F-1956/J-1394 — see the computation above for exactly what these count and why (both real
            # 24h windows). `unjudgeable_field_absent_24h` is this job's own sibling count to
            # `unjudgeable_moved_24h` just above; `unjudgeable_rate_24h` combines both causes into the
            # one rate this job's own pre-registration is read against.
            "unjudgeable_field_absent_24h": unjudgeable_field_absent_24h,
            "unjudgeable_stale_24h": unjudgeable_stale_24h,                  # J-3035 / D-0548
            "unjudgeable_moved_place_24h": unjudgeable_moved_place_24h,      # J-3035 / D-0548
            "trivial_excluded_24h": trivial_excluded_24h,                    # J-3160 / D-0548
            "unjudgeable_rate_24h": unjudgeable_rate_24h,
            "judge_retry_24h": judge_retry_24h,                              # J-3100 / F-3818
            "judge_retry_resolved_24h": judge_retry_resolved_24h,
            "judge_retry_lost_24h": judge_retry_lost_24h,
            "expect_is_plan_rate_24h": expect_is_plan_rate_24h,
            # D-0284 (J-1413) — see the computation above for exactly what these count. THE metric of
            # record for D-0284's own defeater is `would_withhold_rate`; `_n`/`_scored_n`/`_coverage`
            # are the honest numerator/denominator/coverage trail, same pattern `notice_judged_n`/
            # `notice_sample_rate` already model for a different sampled instrument.
            "would_withhold_rate": would_withhold_rate,
            "would_withhold_n": would_withhold_n,
            "would_withhold_scored_n": len(wwh_scored),
            "would_withhold_coverage": round(len(wwh_covered) / len(ticks), 3),
            # RUN 2: verdicts BY HORIZON — the calibration curve run 1 could not draw. "unsettled"
            # added (F-1949/J-1386) alongside the original three; "unjudgeable" now added by F-1958/
            # J-1396, same additive convention — every horizon's own dict just grows one more key, none
            # of the existing four are renamed or removed.
            "verdicts_by_horizon": {
                h: {v: sum(1 for r in ticks if r.get("judged_horizon") == h and r.get("prior_verdict") == v)
                    for v in ("held", "broke", "cannot_tell", "unsettled", "unjudgeable")}
                for h in HORIZONS},
            "horizon_chosen": {h: sum(1 for r in ticks if r.get("horizon") == h) for h in HORIZONS},
            # 2026-08-22 fix's own instrument: how often the deterministic tide/sun/moon corrector
            # fires. Watch this ALONGSIDE verdicts_by_horizon above — if the 'hour' broke-rate falls
            # while this stays near its current rate, the fix explains it; if 'hour' stays high with a
            # low override rate, the mis-binning has a different cause and this isn't it.
            "horizon_overridden_rate": round(
                sum(1 for r in ticks if r.get("horizon_overridden")) / len(ticks), 3),
            # F-1934/J-1376 (2026-09-26) — the sibling counter for the branch the override now
            # deliberately does NOT take: a day-scale topic named, but the text itself names a
            # minute-scale timeframe (`_correct_horizon`'s own 'skipped-minutes' branch). Read
            # ALONGSIDE `horizon_overridden_rate` above, not folded into it — the two together are the
            # full three-way split of every tick that named a day-scale topic at all.
            "horizon_override_skipped_minutes": sum(
                1 for r in ticks if r.get("horizon_override_branch") == "skipped-minutes"),
            # F-2336/J-1713 (2026-10-03) — the third sibling: a day-scale topic named whose text names an
            # HOUR-scale clock ("in about an hour", "within the next hour"), so the generator's own label
            # stands (`_correct_horizon`'s 'skipped-hours' branch). ADDITIVE beside the two counters above,
            # never folded into either; with it the tick split by branch is four-way (overridden,
            # skipped-minutes, skipped-hours, and the 'already-day'/'no-match' remainder). Pre-registered
            # (F-2336): once a restart loads this, the share of day-labelled predictions that contain hour
            # wording falls from 12 of 12 to near 0, and the day bucket shrinks to roughly the
            # generator-declared day claims (about 1 in 12 on the post-restart mix) -- expected, not a
            # regression.
            "horizon_override_skipped_hours": sum(
                1 for r in ticks if r.get("horizon_override_branch") == "skipped-hours"),
            # F-1934/J-1376 — law 4's own cannot-fail-class scoreboard (`_trivial_prediction_flag`
            # above). This job's own pre-registration: should fall below 0.20 from ~0.45 today, once a
            # restart has picked up the rewritten law 4.
            "trivial_prediction_rate": round(
                sum(1 for r in ticks if r.get("trivial_prediction")) / len(ticks), 3),
            # F-2932/J-2239 -- the same cannot-fail scoreboard NET of heard-steady-sound ticks
            # (`_heard_steady_sound_flag`): trivial share over the ticks that do NOT carry that flag. The
            # gross `trivial_prediction_rate` above stays the metric of record for comparability; rows
            # from before this job lack the key and count as unflagged. None when every tick is flagged.
            "trivial_prediction_rate_net": (lambda _nt: round(
                sum(1 for r in _nt if r.get("trivial_prediction")) / len(_nt), 3) if _nt else None)(
                [r for r in ticks if not r.get("heard_steady_sound")]),
            "heard_steady_sound_n": sum(1 for r in ticks if r.get("heard_steady_sound")),
            # D-0281 / §8.2 — THE NOTICE'S OWN SCOREBOARD, the sibling of the prediction scoreboard just
            # above but for claim-correctness on the notice instead of the expectation. A scoreboard
            # only (§2.9): nothing downstream reads these fields as of this job.
            "notice_verdicts": notice_verdicts,   # includes not_sampled — the full per-tick breakdown
            "notice_sample_rate": round(notice_sampled_n / len(ticks), 3),   # sanity check vs 0.25
            "notice_judge_coverage": (round(notice_judged_n / notice_sampled_n, 3)
                                       if notice_sampled_n else None),   # panel-answered share of asks
            "notice_judged_n": notice_judged_n,   # D-0281's own defeater reads this against 300
            "notice_judge_retired": NOTICE_JUDGE_RETIRED,   # D-0599 (1): True = no new panel notice rulings; the keys above count HISTORY only
            "notice_contradiction_rate": notice_contradiction_rate,   # THE metric of record (D-0281)
            # D-0361(a) (J-1896): the deterministic checker, beside (never replacing) the panel's number.
            # Until the founder's 20-row hand-read of its flags has been done on live rows, read the panel's 0.0
            # as a FLOOR and these as the cheap, reproducible, zero-panel-load cross-check (plan section 8.2).
            "notice_checked_n": notice_checked_n,
            "notice_unsupported_n": notice_unsupported_n,
            "notice_unsupported_rate": (round(notice_unsupported_flagged_n / notice_unsupported_n, 3)
                                        if notice_unsupported_n else None),
            "notice_unsupported_nouns": notice_unsupported_nouns,
            "notice_checked_flag_rate": (round(notice_checked_flagged_n / notice_checked_n, 3)
                                          if notice_checked_n else None),
            "notice_checked_solid_rate": (round(notice_checked_solid_n / notice_checked_n, 3)
                                          if notice_checked_n else None),
            "notice_checked_paired_n": notice_checked_paired_n,
            "notice_checked_paired_flag_rate": (round(notice_checked_paired_flagged_n / notice_checked_paired_n, 3)
                                                 if notice_checked_paired_n else None),
            "notice_checked_kinds": notice_checked_kinds,
            "world_fields_mean": round(sum(len(r.get("world_fields") or []) for r in ticks) / len(ticks), 2),
            # J-1371 (F-1931, §8.1) — per-tick generation latency, real 24h window (see computation
            # above for why this one field pair is time-windowed while the rest of status() rides the
            # tail_rows(_LOG, 2000) window as-is). None/None until a tick logged after this job lands
            # and ages into a real 24h window — never fabricated from pre-J-1371 rows, which carry no
            # `gen_s` at all.
            "gen_s_median_24h": gen_s_median_24h,
            "gen_s_p95_24h": gen_s_p95_24h,
            # ── J-0165 — Tap-on-the-Shoulder (§2.5 point 2) ─────────────────────────────────────
            "hint_rate": round(len(hint_ticks) / len(ticks), 3),   # share of ticks a nomination reached
            "hint_queue_depth": len(hq),
            "hint_pushed_total": int(hints_state.get("pushed_total") or 0),
            "hint_consumed_total": int(hints_state.get("consumed_total") or 0),
            "hint_expired_total": int(hints_state.get("expired_total") or 0),
            "hint_designed_ceiling": {"max_queue": HINT_MAX_QUEUE,
                                       "max_push_per_hour": HINT_MAX_PUSH_PER_WINDOW},
            # §5 metric #5 groundwork — a coarse first divergence proxy: do hinted ticks read
            # differently (grounding/invention/coherence) from self-found ones? This is NOT the
            # plan's own formal per-topic divergence test (that needs matched self-found ticks on
            # the SAME topic, an offline analysis) — it's the cheapest live signal toward it, split
            # here so a later read does not have to reprocess the whole log from scratch.
            "grounded_share_hinted": _mean_of(hint_ticks, lambda r: (r.get("grounding") or {}).get("grounded_share")),
            "grounded_share_unhinted": _mean_of(unhint_ticks, lambda r: (r.get("grounding") or {}).get("grounded_share")),
            "invention_rate_hinted": (round(sum(1 for r in hint_ticks if (r.get("invention") or {}).get("invention_flag")) / len(hint_ticks), 3)
                                       if hint_ticks else None),
            "invention_rate_unhinted": (round(sum(1 for r in unhint_ticks if (r.get("invention") or {}).get("invention_flag")) / len(unhint_ticks), 3)
                                         if unhint_ticks else None),
            # J-1371 (F-1931, §8.3, constitutional law 6) — both standing boundary audits, computed
            # fresh every call instead of by hand (see `_split_stats`/the kind+topic loop above for
            # the exact computation, matched to F-1931's own). §6's "audit cadence" item is closed by
            # §8.3 on the strength of this existing weekly inside the §7.6 read.
            "hint_divergence": hint_divergence,
            "hint_flow": hint_flow,
            "run": RUN,
            "live": LANE2_LIVE,
            # J-1397 (F-1960, 2026-09-27) — the generator that produced the LATEST tick in this window
            # (see `tick()`'s own new `model` rec field, added by this same job). `ticks` is guaranteed
            # non-empty here (the early `if not ticks` return above already handled that case), and
            # `tail_rows`'s own contract is OLDEST-FIRST, so `ticks[-1]` is the most recent row. None
            # when even the newest row in this tail window still predates this job's own restart.
            "model": ticks[-1].get("model"),
            # Dosed Coupling / Lane 2 Phase 1 (D-0241 shadow-first, J-1161, plan §7.6).
            "phase1_p1_metrics": _phase1,
            # Lane 2 Curiosity's `wonder` field — the staged doc's own pre-registered W-1..W-5 read
            # (D-0282/J-1374, docs/staged/lane2_curiosity.md §4).
            "wonder_metrics": _wonder,
            # §2.8c's knowledge tier (D-0285, 2026-09-27) — SHADOW-ONLY (see the comment above this
            # function's own `_knowledge`/`wsk_*` computation for exactly what "shadow-only" means
            # here). `knowledge_top` is `store['knowledge']` itself — small by construction
            # (KNOWLEDGE_CAP=12), safe to return whole rather than summarized, the same "small enough
            # to just show it" choice `hint_flow`/`invented_topics` already make above.
            "knowledge_count": len(_knowledge),
            "knowledge_top": _knowledge,
            # THE metrics of record for D-0285's own defeater ("top-12 stable week to week... once
            # shown, distinct expect_next... broke share..."): `would_show_knowledge_rate` is read
            # after 7 days of shadow (the follow-up job named in the ruling, NOT this one) to see
            # whether the tier is even matching enough ticks to be worth promoting; `_coverage` tells
            # "no rows carry the key yet" apart from "matches, but never anything worth showing".
            "would_show_knowledge_rate": (round(wsk_hit / len(wsk_covered), 3) if wsk_covered else None),
            "would_show_knowledge_coverage": round(len(wsk_covered) / len(ticks), 3)}
