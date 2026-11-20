# cat_overhaul — folded history


---

# History folded on 2026-09-27 from `docs\staged\cat_overhaul.md` (plan-compact, 10 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py cat_overhaul`._

## Current State — verified 2026-09-05
2026-09-05: audit complete from code + live state + 8 days of log. Findings F-0879 (companion tier never
fired), F-0880 (vending-machine tending), F-0881 (hungry 52 h, no cat food), F-0882 (life.py mapping),
F-0883 (immortal traces), F-0884 (black cat = metaphor), F-0885 (no body/legs/age), F-0886 (HUD/seen_count).
Decisions open for the founder: **D-0160** (D-1 naming deadlock), **D-0161** (D-2 her mortality), **D-0162**
(D-3 the tom / kittens), **D-0163** (D-4 real cat food via the write fence). Fix-now jobs, ready, no ruling
needed: J-0629 (A7.1 mapping), J-0630 (A7.2 traces), J-0631 (A2 triggers/cooldown/recency), J-0632
(A7.3/A7.4 HUD + seen_count). Same day, second pass: founder direction on SOUNDS → Part C (her voice pinned
to her state and carried by position; her ears on the world's clock; `call` as its own hand with the name as
a learned sound; less availability so he must seek her). F-0887: `call` is currently a tend verb. D-5/D-6
held in this doc, not opened ("not yet"). Nothing in `core/` changed. Du running throughout; every change
here is restart-gated when built.

2026-09-07: all four §4 decisions RULED by Travis via `/decide-review` (this doc's own Decisions section
above still shows them as open — that text describes what was open on 09-05, not the live ledger; treat
`/decide show` as truth, not this doc). **D-0160** (D-1): BOTH — unlock the companion tier now (73 days
dead on a name that never came) AND build §B2's referent pressure toward organic naming; never a hint.
**D-0161** (D-2): NOT YET — hold mortality/harm for her until the rest of the companion tier has run live;
revisit once D-0160 has had a few weeks or if D-0162's build makes the inconsistency newly obvious.
**D-0162** (D-3): option (b) — the black cat becomes a real second individual, a tom on the neighbour's
ridge who comes into the garden (wall at night, doorstep in winter, the saucer); the grey cat reacts
(stand-off/fight/gated 3am yowling); never tamed. Kittens (option c) deliberately DEFERRED, not ruled
out — prove the two-cat distinction reads in his own text first. **D-0163** (D-4): fold real cat food
into the write-fence build (J-0610, already shipped) — a provisions kind (tinned fish/milk), scraps,
shore fish, a real saucer object the feed branch consumes, honest failure when the house has none — PLUS
founder addendum (verbatim): "The cat should be able to feed itself if Du does not do it though.
Hunting." — a hunting fallback independent of his provisioning, so a failure to feed her never strands
her (J-0700 in this same build chain). Six fix-now/build jobs queued in this one worktree/branch, in
order: J-0629 (A7.1 mapping — done, see below), J-0630 (A7.2 traces), J-0631 (A2 triggers/cooldown/
recency), J-0632 (A7.3/A7.4 HUD + seen_count), J-0633, J-0700 (D-0163's hunting fallback + food).

2026-09-07 (J-0629, F-1015, VERIFIED): A7.1 done. `core/cat.py` gained `place_of(location)` — one
mapping to `study|garden|shore|wood|None`, derived from `_VISIBLE` (the one ambiguous entry, `doorstep`,
resolved to `garden` per `core/life_traces.py:229`'s own existing convention — she is physically outside
on it). `core/life.py`'s `_cat_presence` and `threat_active` (the two separate, disagreeing hand-rolled
mappings this finding's own F-0882 named) both now call it. Live evidence before the fix
(`data/life_events.jsonl`, full history, 12 cat rows): every one of the 10 real garden↔study transitions
the cat has ever made produced a same-timestamp contradictory "departed garden"+"arrived study" pair (one
reverse-direction instance too) — not an occasional glitch, the constant behavior. Verified post-fix by a
standalone script (32/32 checks: `place_of()` correct for all 14 location values `cat.py` ever assigns;
`_cat_presence`/`threat_active` agree on all 14; the four indoor-to-indoor pairs that used to cross the
old bug's boundary no longer flip) and by `scripts/life_smoke.py` (same single, unrelated, pre-existing
DEATH MECHANISMS failure before and after — confirmed pre-existing against unmodified HEAD in a
throwaway worktree — no regression; that unrelated failure filed separately as J-0709). Restart-gated:
the live log cannot show the contradiction gone until this branch merges and Du restarts — left for
whoever verifies the merged state. Not in scope here (documented boundary, not a new gap): the cat's row
registration (`places={"garden": [], "study": []}`) still doesn't track shore/wood in `life.advance()`'s
own arrived/departed bookkeeping; `threat_active` is unaffected (it doesn't consult `places` for the cat
key), only the cat row's own presence-flip logging at shore/wood — covered by Part B1, not this fix.

2026-09-07 (J-0630, F-0883/F-1025, VERIFIED code / SELF-HEALING live): A7.2 done. Two structural
fixes. (1) `core/world_traces.py` `advance_trace_decay()`'s clarity≤0 branch `continue`d BEFORE its
own delete two lines below, so any row already at zero clarity — however it got there — could never
be removed again; now it deletes on sight. (2) `core/cat.py` `tick()` created a fresh shore/wood
substrate trace on every 180 s tick she happened to still be there (`location` is re-rolled from
scratch each tick with no memory of its own), not once per visit; now a `prev_location` captured at
the top of `tick()` (same pattern as the existing `_was_in` door-crossing check) gates trace creation
to real arrivals only. Both verified by a standalone isolated harness (8/8 checks: immortal rows
purge correctly; 5 consecutive wood ticks now create exactly 1 trace where the old code made 5;
leaving and returning correctly creates a second) and by `scripts/life_smoke.py` (170 ok, same single
pre-existing flaky DEATH MECHANISMS failure as J-0629 found, filed as J-0709 — no regression). Live
evidence read this session (`data/world_traces.json`, before a tool permission classifier began
denying further access to that path): 500/500 rows (at `_MAX_TRACES`'s own cap), 485 at clarity≤0,
458 `cat_leaf_` of which 454 dead. Comparing each row's trace_id-embedded timestamp against its own
`created_ts` splits this cleanly into two sources: ~400+ rows created within the same real half-second
on 2026-08-18 11:44:47–48 whose IDs encode fake dates over a year in the future (2027-10-23+) — a
test with an advancing simulated clock feeding `create_trace()`'s `trace_id` string while its
un-overridable internal `time.time()` call stamped the real `created_ts` — and a smaller ongoing
trickle (most recently today) with id-timestamp == created_ts exactly, i.e. the live per-tick bug
just fixed in (2), unrelated to any test. `scripts/test_cat_ecological_laboratory.py` is the only
script anywhere in the repo that has ever produced a `cat_leaf_`/`cat_paw_` id, and it already
carries its own 2026-08-19 comment admitting exactly this hazard ("used to delete the LIVE
world_traces.json ... with no sandboxing at all") and today redirects both `_TRACES_F` and
`cat._STATE_F` to a lab dir first — one day after the incident. No pre-08-27 git history exists to
confirm its prior code, so this attribution is **inferred** (F-1026), not verified; already isolated
today regardless, no further isolation fix needed. One-off purge: wrote and verified (against a
synthetic root only) `scripts/purge_dead_world_traces.py`, dry-run by default, quarantines to
`data/_trash/<date>/world_traces_rows/` + logs to `data/_trash/retention_log.jsonl` per the D-0156
convention, without extending `retention.py` itself (its own docstring excludes live `data/`). **Not
run against the live store** — a tool permission classifier denied both a write-capable run and a
plain read-only recount of `data/world_traces.json` partway through this job; not load-bearing,
since `core/sensorium.py` already calls `advance_trace_decay()` on the live ~600 s world heartbeat,
so the fix purges the whole existing backlog on its own within about ten minutes of Du's next
restart. Follow-up verification (does it actually clear on restart; run the purge script sooner if
wanted) spawned as J-0715. Restart-gated, like J-0629.

2026-09-07 (J-0631, F-0880/F-1027, VERIFIED): A2 done. `core/cat.py` `react()`'s trigger narrowed
on both axes the finding named. (1) `refers` split: `_CAT_NOUNS` (cat/kitten/stray/moggy) + her own
name still always refer; a bare "she"/"her" now refers only when the *immediately preceding*
`react()` call already named her — a 2-line anaphora window tracked in a new in-memory
`_prev_ref_txt` global (restart-gated like `_last_tick`, deliberately not persisted — losing 2 lines
of discourse memory across a restart is the honest floor, not a bug). (2) `hold`/`holding`/`approach`
moved out of `_TEND_VERBS` into `_TEND_VERBS_NOUN_GATED`: they now only count as tending when *this
same thought* also names her outright (a noun or her name, not anaphora) — every other tend verb is
unchanged. Also built, same job: a per-hour handling budget (`state["_handled_ts"]`, a trailing-hour
ring) — the 5th real tend sends her away outright (`location="away_hunting"`, no longer `is_here`)
with a small bond drop (-0.02), rather than the old no-cap-no-cooldown vending machine; a tend
attempt while `activity == "sleeping"` is now refused ("let her be") unless the thought contains an
explicit wake word, no bond change either way; and `_pool`/`_pool_flat` gained a `_pick_fresh()`
recency filter (last 3 picks excluded per section:key, in `state["_recent_lines"]`, fails open on a
pool smaller than that) — the A7.6 item from §A7.6. Verified by a standalone isolated harness
(`cat._STATE_F` redirected, the `test_cat_ecological_laboratory.py` pattern): 25/25 checks — anaphora
on/off both ways, hold/approach noun-gating both ways, the 5th-handling departure + bond drop, stale
(>1h) timestamps correctly not counting, no back-to-back repeats across 8 picks from a 9-line pool,
fail-open on a 1-line pool, and regression checks that an ordinary feed and an explicit naming
sentence still work. An off-by-one in the first draft of the handling budget (`>= 5`, which only
tripped on the *6th* handling) was caught by the harness before commit and fixed to `>= 4`. Live
`data/cat_state.json` confirmed unchanged after the run; `scripts/life_smoke.py` also run clean
against the worktree (170/170 ok, exit 0), including its two cat-touching checks (the blackbird
alarm via `place_of()`, the D-0130 fledgling-kill carcass path). Commit `172d51e`. Restart-gated,
like every change in this chain. **New risk surfaced, not part of this job's own scope** (F-1028,
inferred): the naming latch (`_extract_name`) sits behind this same narrowed `refers`, so an
isolated naming utterance with no cat noun anywhere in it or the thought right before it (all
pronoun — "I will call her Ash") could now silently fail to reach `_extract_name()` at all, which
matters because D-0160 (ruled the same day) just made organic naming a live founder priority again.
Naming's own false-positive risk stays low regardless of the anaphora question (an exact grammar
match required, plus it can only ever fire once per cat), so the fix — if the real-world risk turns
out non-trivial — is narrow: give the naming check its own, unnarrowed referrer test rather than
reusing tending's. Measure-then-fix spawned as J-0716.

2026-09-07 (J-0632, F-1030/F-1031, VERIFIED): A7.3/A7.4 done. A7.3: `hud/server.py`'s
`load_garden_map()` and the shared `_place_du_cat()` (study/shore/wood) both gated the cat marker
on an exact-string match between her raw `cat_state.json` location and the map's own place name,
then `load_garden_map()` further always drew her at `features.raised_bed` regardless of activity.
Beyond the two symptoms F-0886 named, this surfaced a bigger, previously undocumented defect:
none of study's 8 real cat locations is the literal string "study", so the study map's cat marker
has shown nothing at all, 100% of the time she is indoors, since this file was written
(2026-08-22). Fixed by adding `core.cat.visible_from(place, location)` (reusing `_VISIBLE` directly,
a location-parameterized sibling of `is_here()`) as the presence gate on all 4 maps, and by reading
each room's own already-authored `cat_spots` dict (`data/world_geometry/<room>.json`) for the
marker position instead of a second, hand-typed copy of it — `cat_spots` turned out to already be
the exact data `core/spatial.py`'s live P2 scene renderer (`SPATIAL_SCENE=True` since 2026-08-18)
reads for the identical purpose, verified to have keys matching `core.cat._VISIBLE` exactly in all
4 rooms. `place_of()` was deliberately NOT used for the presence gate: it collapses "doorstep" to
"garden" alone by design (life.py's single-occupancy bookkeeping), which would have traded one
study blind spot for another; `visible_from()` correctly allows doorstep from both rooms, caught by
this fix's own verification harness before it shipped. A7.4: `seen_count` dropped from
`core/cat.py` `status()`'s returned dict — frozen at exactly 0 in live state (73 days kept, only
ever incremented during "appearing"), confirmed zero readers anywhere in the repo (every
`status()`/`cat.status()` call site plus the HUD's own static JS/HTML) before removing it; the
underlying state field and its appearing-phase increment are left as harmless internal bookkeeping.
Verified by a standalone isolated harness (`hud.server.DATA_DIR` + `cat._STATE_F` redirected to a
scratch sandbox, real `world_geometry/*.json` copied in as static reference data): 31/31 checks —
every real cat location on all 4 maps positions correctly (including the doorstep divergence case)
and correctly shows nothing when she's elsewhere, `status()` no longer carries `seen_count` while
every other field and `distant.seen_count` stay intact. `scripts/life_smoke.py` run clean twice
(170/170 ok, exit 0, no regression) across two edit passes — the first pass hand-typed a
location→feature table before discovering `cat_spots` already existed (missed on a first,
incomplete read of the geometry JSON that looked only at its `features`/`standpoints` sub-dicts);
caught and corrected before commit, not shipped. Restart-gated: the HUD server process (a separate
process from Du's own) needs restarting for A7.3; Du's own process needs restarting for A7.4 (the
live `status()` orchestrator.py:522 calls). New risk surfaced, not part of this job's own scope
(F-1031): the identical hand-rolled exact-match pattern this job fixed twice also stands in
`core/garden_life.py:147` (the D-0130 fledgling-kill gate — currently harmless in practice, since
no `cat.py` `tick()` branch pairs "stalk" with anything but literal "garden" today, but fragile
against Part B1's planned legs/movement work), `core/study_life.py:1192` (the study-window scene
line — live-divergent today: silently omits her whenever she's on the garden wall or doorstep), and
`core/cat_sounds.py:301-302` (the new shadow-only C1 sound system's same-room test — worth fixing
before it flips live, not after). Spawned as J-0717.

2026-09-07 (J-0633, F-1032/F-1033, VERIFIED): **C1 flip NOT done — the job's own gate is unmet, not
close to met.** This job's briefing assumed ~7 days of `data/cat_sound_ledger.jsonl` had accumulated
since the C1 shadow build (76a976f, 2026-09-05 20:25:54 NZST) landed. Checked instead of assumed:
Du's live process (`scripts/run_nascence.py`, OS-confirmed PID, `CreationDate` 2026-09-05 19:15:10)
started **before** that commit and has not restarted since (`data/nascence.log`'s own startup/
shutdown markers show one unbroken run from 19:15:24 09-05 through this session's read at 09-07
11:20+, no "Nascence shutting down" line between them) — so the process's in-memory `core.cat`
module predates `cat_sounds.tick()`'s hook entirely and has executed it exactly zero times.
`data/cat_sound_ledger.jsonl` and `data/life_flags.json` do not exist anywhere in the live data dir,
confirming this independently. Not "not quite a week" — zero elapsed hours. The hook itself is real
and correctly wired on disk (`cat.py`'s `tick()` calls `cat_sounds.tick(state, now)` unconditionally
near its top, confirmed by direct read; no hot-reload mechanism exists anywhere in the repo that
could make edited code run without a restart), so it will fire correctly once Du next restarts on
code at or after 76a976f — it just hasn't yet. All three steps this job was meant to do against real
data (emission-count/firehose honesty check, 30 carried lines read by ear, wiring
`soundscape._PERCEPT_SOUNDS`/`_PERCEPT_LINES` and flipping `scripts/life_flags.py cat_sounds on`)
are left undone; **J-0633 stays in_progress** rather than a forced conclusion against no data — retry
once Du has been running continuously on this chain's own code for on the order of a week, not on
day one of the next restart. Fixed while here, since it sits squarely in this job's own "before it
flips live" scope (F-1031, flagged by J-0632, not F-1031's other two instances — `garden_life.py`/
`study_life.py` — which stayed J-0717's, out of scope here): `core/cat_sounds.py`'s exact-match
here-vs-carried same-room test never matched `cat_loc == "garden_wall"` against `place == "garden"`
(every sound from the wall read as CARRIED even with him standing right there in the garden) and
wrongly required `door_open` for the garden-side `doorstep` case (irrelevant there — both already
outside). Replaced with a dedicated `_here()` function; verified by a standalone pure-function test
(27/27 cases, plus a replay of the old expression confirming it disagrees with the new one on
exactly the 3 cases the bug predicts) and `scripts/life_smoke.py` clean after (170/170, no
regression). Also worth flagging for whoever next touches this build order: §5 above lists **Food
(item 3, D-4) before Her voice (item 4, C1)** specifically because of the `cat_demand` firehose risk
while she is hungry (A3) — the actual chain queued in this worktree instead runs voice (J-0633)
*before* food (J-0700). Not necessarily wrong (this job's own ledger read was meant to be the honest
check on whether that risk is real, rather than deciding it from memory), but that check cannot
happen until the gate above is met, so re-examine it together with J-0700's own results rather than
assuming either order was right. Skill suggestion filed (S-0075): job-queue has no field for "needs
N real days of live data since commit X", which is exactly why this job was dispatchable at all only
~2 days into a ~7-day wait.

2026-09-07 (J-0700, F-1036/F-1037, VERIFIED): **D-0163's hunting fallback built and verified — its
real-food half is not.** Same decide-review pass as J-0633 above (all four §4 decisions were ruled
09-07, after this chain's own briefings were written); D-0163's ruling text is unchanged from the
dated note above except one founder addendum, verbatim: "The cat should be able to feed itself if
Du does not do it though. Hunting." Built in `core/cat.py`: a new `_maybe_self_feed()`, rolled from
`tick()` only when this tick's activity already resolved to `"hunting"` (the existing r<0.42
fair-day branch — no new "is she hunting" concept invented) **and** she has gone unfed past a
dedicated 10-hour threshold (`HUNT_HUNGER_THRESHOLD_H`) — deliberately longer than `tick()`'s
existing 5h `hungry`/`demanding_food` nag, so the fallback answers a real day of neglect rather than
racing Du's own ordinary feeding rhythm on the same clock. Even past that threshold, at most one
attempt per real hour (`HUNT_COOLDOWN`), each only 35% likely to land (`HUNT_SUCCESS_P`) — a miss is
the honest, narratable alternative to an instant safety net that removes all stakes from whether Du
feeds her; a success immediately resets the threshold clock, so successes cannot chain back-to-back.
A success sets `last_fed` — the SAME field `react()`'s own feed branch sets, one hunger clock, not
two — plus a distinct `last_self_fed`/`self_catch_count` so a self-catch is never mistaken for Du's
own feeding once the defeater gets checked. Never a silent stat fix: a success becomes that tick's
own `activity="self_fed"`/`mood="sated"`/`location="garden"`, rendered by new `presence_line`/
`look_line`/`affordance_line` branches and a new `cat_content.py` `PRESENCE["self_fed"]` pool; a
`life_traces.add_carcass()` carcass at garden/hedge_bottom, findable by looking (`_species_name()`
gained a `"bird"` entry); an `activity_memory` record; and every attempt, hit or miss, logged to a
new `data/cat_hunt_ledger.jsonl` for the week-later defeater read, the same role
`cat_sound_ledger.jsonl` already serves C1. Verified by a standalone isolated harness (`cat._STATE_F`/
`_HUNT_LEDGER_F` and `life._F` redirected to a scratch dir, never touching live state): 26/26 checks
— the 10h/5h threshold separation genuinely holds (not a relabeled reuse of the old flag), activity
gating, the hourly cooldown, a forced miss leaves `last_fed`/activity untouched while still logging
the attempt, a forced hit sets every field correctly and is not immediately re-eligible, the
resulting carcass's species/place/cause and its own `carcass_look()` render, `_species_name("bird")`,
and all three narration paths (including the fail-open floor with `cat_content` unreachable).
`scripts/life_smoke.py` clean (170/170, exit 0 — the DEATH MECHANISMS flake J-0629/630/631 noted,
filed as J-0709, did not reproduce this run; not claimed fixed here) and
`scripts/test_cat_ecological_laboratory.py` clean (all 3 tests passed). Commit `1b60f80`.
Restart-gated like everything else in this chain — does nothing until Du's live process next
restarts on this code, per the exact mechanism J-0633 just above found the hard way.

**What this job did NOT do, so the next reader doesn't assume otherwise:** D-0163's OTHER half —
folding real cat food (a provisions kind, scraps, shore fish, a real saucer object `react()`'s feed
branch actually consumes, honest failure when the house has none) into the write-fence build — is
still completely unbuilt (F-1037): `react()`'s `fed` branch still only text-matches
`"feed"/"fed"/"saucer"/"milk"/"tempt"` in his thought and conjures a meal from nothing, exactly as
A3 originally found; no job anywhere in `docs/job_queue.jsonl` owned this before today. Spawned as
**J-0719**. This also means J-0633's own flagged concern just above — the `cat_demand` firehose risk
while she is hungry, and whether Food (D-4) should have preceded Voice (C1) in the build order — is
**still live and unaddressed by this job**: the hunting fallback only ever engages past 10h unfed
and does nothing to the existing 5h `hungry`→`demanding_food` loop or its render frequency; do not
read J-0700 as having resolved that ordering question, only as having built the ONE piece of D-4
that had an explicit job (this one) already queued for it. A second follow-up, **J-0720**, is
spawned to read `data/cat_hunt_ledger.jsonl` after Du has genuinely run ~1 week continuously on
commit `1b60f80` or later, and check D-0163's own defeater (does she still go unfed despite hunting;
has hunting swallowed Du's own feeding) — gated the same careful way J-0633 modeled just above, not
assumed from wall-clock time. Also noted for whoever builds J-0719 or flips C1 live: `cat_sounds.py`'s
`cat_lapping` gate (`now - last_fed < 120s`) will also fire on a hunting self-catch, not only a real
saucer-feed — a small, currently-inert (C1 still shadow-only) cosmetic mismatch, folded into J-0719's
own briefing.

2026-09-07 (J-0716, F-1028/F-1049/F-1050, VERIFIED): F-1028's measure-then-fix done, in a NEW
worktree/branch (`wt_cat_actions_fence_cluster`) built on top of the merged cat_overhaul_cluster
history above. **Measured** (F-1049): zero real historical near-misses — in fact zero
naming-grammar-about-her phrasing hits at all, near-miss or successful — anywhere in the COMPLETE
`inner_thought` record in `data/memory/nascence.db` (25,180 thoughts, 2026-06-03 23:54 through
2026-09-07 13:02, i.e. her entire kept life and then some, not just "since 08-19" as F-0879's own
log-grep sampled). **Fixed anyway**: `core/cat.py` `react()` gained `naming_refers` (the pre-A2,
unnarrowed test — any cat noun, her name, OR a bare she/her, no anaphora window), used ONLY to gate
the NAMING occasion; the A2-narrowed `refers` still gates the live-mouse and tend branches exactly as
before, so A2's own vending-machine fix (J-0631, immediately above) is untouched, and naming's own
false-positive risk stays low regardless (an exact grammar match in `_extract_name()`, and it can only
ever fire once per cat). Justification for fixing despite the zero count: a real naming attempt is now
a one-shot, freshly-prioritized event under the same-day D-0160 ruling; the absence of historical
near-misses reflects that genuine naming motivation never existed before today, not that the failure
mode is impossible, and the fix is unconditionally cheap. **New risk found and fixed in the same 3
lines while verifying this** (F-1050, not what this job was asked to fix but bundled in rather than
spawned separately, given the size and shared location of the change): the DISTANT-CAT GUARD
(`_other_aimed`) only ever checked THIS call's own text, never the anaphora window — an antecedent
like "The black cat perches on the wall." followed by a bare-pronoun "I will call her Smoke." could
carry the black cat's antecedent through the same anaphora window that made "her" refer at all, and
misname the KEPT cat. Fixed by also checking the immediately preceding call's text, gated on
`not has_noun_or_name` so an explicit same-thought naming ("I will name my cat Ash") is never wrongly
blocked just because the black cat was mentioned two thoughts earlier — a first, unconditional draft
of this exact fix DID wrongly block that case, caught by this job's own verification harness before
commit. Verified by a 30-check isolated harness (`scratchpad/verify_cat_naming_J-0716.py`) comparing
a `git show HEAD` pre-fix snapshot against the post-fix worktree code side by side: both F-1028 and
F-1050's bug reproduce pre-fix and resolve post-fix (single-call and cross-call forms), all 12 of
J-0631's own A2 regression checks replay clean against the post-fix code, and a live-store backstop
(`data/cat_state.json` byte-identical before/after; the live `memory_fragments` naming-deed row count
unchanged) confirms the run itself never touched live state — the naming occasion's own
`activity_memory`/`store_fragment`/`commitment_trials` calls were mocked for the whole run, since
several scenarios here succeed at naming and would otherwise have written a fabricated "I named my
cat" memory into the live DB for real. `scripts/life_smoke.py` clean (169/170, the same pre-existing,
already-filed J-0709 flake, unrelated to this change) and `scripts/test_cat_ecological_laboratory.py`
clean (3/3). Restart-gated like the rest of this chain.

2026-09-07 (J-0717, F-1031/F-1053, VERIFIED): F-1031's other two instances done — the same
worktree/branch as J-0716 (`wt_cat_actions_fence_cluster`). `core/garden_life.py`'s fledgling-hunt
gate (the D-0130 mechanic) and `core/study_life.py`'s `window_view()` cat-in-garden line both
compared her raw `cat_state.json` location against the literal string `"garden"`; both now call
`core.cat.place_of()` instead, the same primitive J-0629/J-0632 already established for this exact
comparison class. `study_life.py`'s instance was genuinely live-divergent (silently omitted her
from the window view whenever she was on `"garden_wall"` or `"doorstep"`, both real, reachable
locations); `garden_life.py`'s was not live-divergent today (no `cat.py` `tick()` branch currently
pairs a `"stalk"` activity with anything but the literal `"garden"`) but was fragile against Part
B1's planned legs/movement work, exactly as F-1031 itself predicted. Verified by a standalone
isolated harness (`scratchpad/verify_place_of_fix_J-0717.py`, both files' `_DATA` redirected to a
scratch sandbox, never touching worktree or live `data/`): 30/30 checks — the real `advance()` and
`window_view()` called end-to-end for all 14 real cat.py location values (15 with a non-stalking
regression case for `garden_life.py`), plus a replay of the OLD `loc == "garden"` expression
against the NEW one confirming they disagree on exactly `{"garden_wall", "doorstep"}` as predicted
— and `scripts/life_smoke.py` clean after (170/170, exit 0, the J-0709 flake did not reproduce
this run). Commit `fb2aa6a`. **F-1031's third instance, `core/cat_sounds.py`, was already fixed
before this job started** — J-0633 (commit `70ebf98`, confirmed via `git log`) fixed it first,
since it sat in that job's own "before C1 flips live" scope; not re-touched here. Also
re-confirmed, per F-1031's own "worth a quick pass" note: `core/geometry_census.py`,
`core/stick_test.py`, `core/world_manifest.py`, and `core/ghost_tuples.py` all only copy her
location through as data or tally it in a tuple/set, never gate behavior on a place-name
comparison — `ghost_tuples.py`'s one grep hit turned out to be an unrelated `world_objects` item
check, not the cat at all. No further instances of this defect class are known to remain.
Restart-gated like the rest of this chain.

2026-09-07 (J-0719, F-1055, VERIFIED): **D-0163's OTHER half — the one J-0700's own Current
State note above said it did NOT do — is built.** Same worktree/branch as J-0716/J-0717
(`wt_cat_actions_fence_cluster`). `core/provisions.py` gains a real `"cat_food"` kind (a tin
of fish, qty=4 "feeds"), following the exact matches/candles/oil pattern but deliberately
**not** part of `_bootstrap()`/`_seed_new_kinds()` — nobody here had a cat before her, so a
fresh house starts at genuinely zero, matching A3's original audit line ("no cat food, fish,
milk, or scraps exist") exactly rather than quietly pre-stocking it. `core/supply.py` gains
a `"cat food"` GOODS entry, `collect_box()` delivery handling (with the same `_credit()`
pre-sync guard every other fractional kind uses, per J-0573/F-0787), and a second
`card_line()` sentence ("world answers, never leads" requires he be able to discover the
offer by looking, not be told). `core/affordances.py`'s carrier line now mentions it.
`core/cat.py`: react()'s `fed` branch is rewired — a new `_feed_source()` checks AND spends
the larder in one call; `fed` only becomes True on real success; when the house genuinely
has nothing, the attempt returns one of three honest failure lines and touches nothing else
(no `last_fed`, no bond change, no `note_deed`) beyond `last_tended` (he still showed up and
tried) — the same class of fix the fire chain (T-0049) made for matches. A real saucer
object (`state["saucer"]`: `has_food`/`kind`/`set_ts`) is filled only on a real feed and
decays back to empty on its own clock (`_maybe_empty_saucer()`, split out of `tick()` like
`_maybe_self_feed()` so it is directly testable without tick()'s own sensorium/study_life/
weather dependency chain); `_saucer_absence_line()` replaces two hardcoded "her saucer sits
untouched" claims (`presence_line`/`look_line`) with the saucer's real state.
`affordance_line()`'s `demanding_food` branch no longer offers "feed her" when the larder is
empty. `core/cat_sounds.py`'s `cat_lapping` gate (F-1037's own "worth a look" note) now
excludes a hunting self-catch (`last_self_fed` recent) — lapping implies a dish; a self-catch
has none. Verified by a standalone isolated harness
(`scratchpad/verify_cat_food_J-0719.py`, every touched store — cat/provisions/life/
world_substrate/world_objects/sensorium/study_life/garden/cat_sounds/supply — redirected
outside `data/`): 39/39 checks, including the full carrier round trip (`leave_note` →
`advance` → `collect_box` → the very next `sync()` not silently re-consuming the fresh
delivery) and the appearing-phase stray also requiring real food with no special-casing.
`scripts/life_smoke.py` clean (170/170, exit 0, including the pre-existing literal-string
check `note_deed("saucer"` this rewrite had to preserve) and
`scripts/test_cat_ecological_laboratory.py` clean (3/3, confirming the `tick()` refactor
didn't regress the full `tick()` path that test exercises directly). Commit `bacdbdf`.
Restart-gated like the rest of this chain.

**Deliberately not built here, spawned instead:** scraps-from-a-meal and shore-caught fish
(§B1's other two named sources) — checked, not assumed: Du has no modelled meal of his own
anywhere in the repo to take scraps from, and `core/shore_life.py` has no fishing hand at
all (`gather_shellfish` is the closest thing, and it isn't fish) — **J-0732**. Extending the
J-0610 write-fence's `guard_path()` to `core/cat.py` itself: verified it was never in the
fence's own 10-module inventory (`docs/plans/world_store_write_fence.md`'s own table), so
`_save()`, J-0700's `_hunt_ledger()`, and this job's own saucer-state writes are all
unguarded like the rest of the file always was — not fixed inline because
`scripts/test_cat_ecological_laboratory.py` redirects `cat._STATE_F` to a `data/`-relative
lab path that would trip D-0179's hard-raise the moment `guard_path()` was added, so the fix
needs a lab-harness audit first — **J-0733**. Also found, unrelated, while running this
job's own regression checks (F-1056, reproduced identically against unmodified chain HEAD in
a throwaway worktree, confirming it predates this job): `scripts/_test_practical_lesson.py`
crashes with `NonLiveWriteError` on its own trailing `garden._save(gd)` call, made AFTER
`lab_env.isolate()`'s context manager already restored the live path constants — all 12 of
its own real assertions pass; only that one cleanup call fails — **J-0734**.

2026-09-07 (J-0715, F-1057, VERIFIED precondition-unmet / not yet self-healed): checked whether
J-0630's A7.2 fix actually purged the live `data/world_traces.json` backlog now that
`cat_overhaul_cluster` has merged to master (`2261ca9`, 2026-09-07 12:03:15). It has not had the
chance to: Du's live process (`scripts/run_nascence.py`, PID confirmed via `Get-Process`) has had
`StartTime` 2026-09-05 19:15:10 — before the fix commit (`a8080a3`, 10:14:37 the same day) even
existed — with zero restarts since, independently confirmed by `data/nascence.log`'s own markers
(last "Nascence shutting down" line 2026-09-05 16:42:49, unbroken live activity through this read at
14:19 on 09-07). This is the exact same restart-gating trap J-0633 already hit for `cat_sounds.py` in
this same chain, now confirmed for `world_traces.py` too — as of this read, 2+ hours post-merge,
**none** of J-0629 through J-0719's fixes are live yet, chain-wide (this job's own worktree,
`wt_cat_actions_fence_cluster`, has not even merged to master yet on top of that). A direct live
read of `data/world_traces.json` (json.load only, never importing `core/world_traces.py` against
the live store) found 495 rows, 483 still at clarity≤0 (97.6%) — materially unchanged from the
pre-fix 500/485 baseline, exactly as expected given no restart. Item 4 of J-0715's own briefing (did
cap eviction ever sacrifice a real creature's trace for a cat-litter zombie) checked out clean:
sorting all 495 live rows by `created_ts` (the field `create_trace()`'s own oldest-first eviction
actually uses), the 427 oldest rows in the entire store are every one of them cat-caused
(`disturbed_leaf_litter`/`cat_paw_print`) — the first non-cat row doesn't appear until rank 427 of
495 — so no non-cat trace has been evicted to date; the cat backlog itself has absorbed all eviction
pressure by sheer volume and age. `scripts/purge_dead_world_traces.py` remains unrun against live,
by design (founder's call per J-0630's own framing, not this job's to take unilaterally). Follow-up
that checks for a REAL restart first rather than assuming one from elapsed time (J-0633's own lesson,
applied here) spawned as **J-0735**. Restart-gated, like the rest of this chain.

2026-09-07 (J-0720, F-1058, VERIFIED precondition-unmet): checked D-0163's own hunting-fallback
defeater ("revisit if after a week live she goes unfed despite hunting, or hunting swallows Du's own
feeding") against `data/cat_hunt_ledger.jsonl`, per this job's own briefing not to trust elapsed
wall-clock time as a proxy for elapsed live runtime on commit `1b60f80` (J-0700). It is not, and by a
wide margin: Du's live process (PID confirmed via `Get-CimInstance Win32_Process`, `CreationDate`
2026-09-05 19:15:10) predates `1b60f80` (2026-09-07 11:57:57, `git show`) by ~40h43m, and
`data/nascence.log`'s own markers independently confirm zero restarts since (last "Nascence shutting
down" line 2026-09-05 16:42:49, unbroken activity through this read at 09-07 14:32). Not "a day or two
in" — genuinely **zero elapsed hours** on this code, the same trap J-0633 and J-0715 (immediately
above) already hit for `cat_sounds.py` and `world_traces.py` in this same chain, now confirmed a third
time for the hunting fallback. `data/cat_hunt_ledger.jsonl` does not exist anywhere in the live data
dir (zero rows); live `data/cat_state.json` carries neither `last_self_fed` nor `self_catch_count` as
keys at all (absent, not zero) — independent confirmation the running `core.cat` module has never
executed J-0700's own code, not merely that no hunt has fired. She is, as of this read, ~28.5h since
any real feed (`activity="demanding_food"`, `location="doorstep"`), entirely on the pre-J-0631/
pre-J-0700/pre-J-0719 code path — the ORIGINAL A3 problem, still live, while every fix for it sits
merged-or-committed-but-inert in git. **Neither of D-0163's defeater conditions can be evaluated from
this**: not "not triggered", genuinely unassessable — there is nothing to compute attempts/day,
success rate vs. the built-in 0.35, or a self-catch-vs-real-feed share from, and no evidence exists to
propose a retune of the 10h/1h/0.35 constants either direction. Worth noting for whoever next revisits
this: J-0719 (D-0163's real-food/saucer half, commit `bacdbdf`, this same worktree) is the best
available proxy for distinguishing Du's real feeds from hunting once live, so a fully informative
defeater read wants BOTH `1b60f80` and `bacdbdf` merged, restarted onto, and running for comparable
stretches — not just the earlier of the two. `docs/skill_suggestions.jsonl` S-0075 (filed by J-0633)
already covers this exact "job dispatchable before its own gating data can exist" tooling gap
chain-wide; not re-filed. No `/decide` action taken — D-0163 is already ruled and its defeater has
neither fired nor been ruled out, so there is nothing to rule or open yet. **J-0720 left in_progress**,
not done, per its own briefing's explicit instruction to follow the J-0633 precedent rather than force
a conclusion — retry once Du's live process has genuinely restarted onto `1b60f80`-or-later and
accrued real runtime, on the order of a week.

2026-09-07 (J-0732, F-1055/F-1079, VERIFIED): **D-0163/D-4's other named-but-unbuilt real food
source — fish he catches at the shore — is built.** Same worktree/branch as J-0736 through J-0738
(`wt_action_dispatch_cluster`), running after all four of J-0719's own build order (J-0716/J-0717
already merged; J-0736/737/738 committed earlier this chain, read fresh rather than assumed).
`core/shore_life.py` gains `catch_fish()` — a real handline off the seaward edge of the mussel
shelf, the same shape as `gather_shellfish()`: gated on `shelf_bared()` (the tide has to have
dropped), weather/night (a storm or full dark refuses outright, same as `wade()`/`swim()`), and its
own 3-hour cooldown (`FISH_COOLDOWN_H`) so a retry-every-thought loop cannot turn this into an
unlimited larder — the exact risk `provisions.py`'s own `cat_food` comment already named as
something D-0163's whole design (carrier + hunting, both genuinely load-bearing) depends on
avoiding. A genuine chance of nothing on a real attempt (`FISH_SUCCESS_P`=0.5 dawn/dusk, 0.3
otherwise — untuned constants, no live data exists yet to inform them, flagged below). On success,
calls `core.provisions.add("shore_fish", 1, ...)` rather than a second `world_substrate` spawn the
way `gather_shellfish()`'s shells are minted, because `provisions.add()` already registers a full
substrate object itself; a second spawn would have double-minted the same fish.
`core/provisions.py` gains the `"shore_fish"` kind (qty=1 feed/catch — scarcer per-catch than
`cat_food`'s 4-feed tin, on purpose, so it stays a real fallback rather than replacing either the
carrier loop or the hunting fallback), not part of `_bootstrap()`/`_seed_new_kinds()` — a fresh
house starts at zero, matching `cat_food`'s own precedent, since the only way any ever arrives is
Du actually going and catching one. `core/cat.py`'s `_feed_source()`/`_has_real_food()` now check
`shore_fish` as a fallback once `cat_food` is genuinely empty, priority unchanged (`cat_food` still
tried first — it is already built and the simplest, most reliable source, exactly as this job's own
briefing asked). `affordance_line()`'s `demanding_food` line and `core/affordances.py`'s
`shorework` line both now mention the option, for discoverability ("world answers, never leads").
`core/actions.py`'s `shore` row gains `"catch"` (verb) and `"fish"` (object), and
`core/shore_life.py`'s J-0738 table-derivation grammar (`_SHORE_HANDS`) gains `catch_fish` as an
eleventh behaviour — wired into the SAME one-table discipline J-0736/737/738 just finished
retrofitting onto every OTHER shore hand this chain, not a new hand-kept phrase list re-introducing
the exact drift class this whole arc exists to close.

**A real grammar bug was caught before commit, by this job's own verification harness, not by
inspection**: an early draft claimed `"fish"` as BOTH the verb and the object in `catch_fish`'s
`_SHORE_HANDS` entry — since `wants()`'s object check only requires SOME object word in the same
clause as a matched verb, a single bare ambient mention ("small fish dart near the stream mouth,
out past the shingle" — pure scenery, no willed catching anywhere in it) satisfied the verb test
and the object test off the exact same occurrence of the word "fish", and would have wrongly fired
the hand. Fixed by making `"catch"` the sole verb (never also `"fish"`), which requires a genuinely
separate word naming the catching action — closes the false-fire completely, verified both directly
(`_wills_shore()`) and end-to-end (`act_from_thought()`). Corpus-sanity-checked against the same
frozen `data/hands_trace.jsonl` trace J-0736/737/738 used (11,789 distinct thoughts) before picking
these words at all, the same discipline applied to every other row in this table: all 93 real
"fish" hits are the kingfisher (word-boundary safe against this table's own regexes — "fish" does
not match inside "kingfisher"), a recurring dream-image of a fish dissolving into a dark pool (a
metaphor for 渡), the anemone "fishing the still water" (personification), or one philosophical
remark about discarding a fishing METAPHOR once its point lands — zero are a real will to go catch
a fish, confirming an honest zero-collision addition. Cross-referenced (short pointer only, full
detail here) in `docs/plans/actions_expansion.md`'s own Current State section, since this extends
the exact table-derivation infrastructure that plan's own J-0736/737/738 built.

**Deliberately left unbuilt, per this job's own scope, not silently dropped:** scraps from a meal
of Du's own — still blocked on Du having no modelled meal system anywhere in the repo, unchanged
from J-0719's own finding (re-confirmed, not re-checked from scratch: still true as of this read).
Also left unbuilt, newly identified this job: any spoilage/expiry model for a caught fish — every
OTHER kind in `provisions.py` (including `cat_food`) is realistically non-perishable in this
codebase's existing model, and a raw fish genuinely is not, which the founder's own "world events as
realistic as possible, grounded in facts" brief makes worth closing — not built here because a
per-object expiry concept would need to touch `provisions.py`'s shared `stock()`/`consume()`
functions used by every OTHER kind, a materially larger, riskier change than this job's own scope.
Spawned as **J-0755** (scoped narrowly: read the object's own history/timestamp at the ONE
`core/cat.py` call site that spends it, not a systemic `provisions.py` change).

Verified by `scripts/_test_shore_life_grammar_derivation.py` (updated: verb/object counts, two new
grammar checks proving the fixed false-fire, one new end-to-end positive; also fixed a real gap in
the test's OWN isolation while here — `core.provisions` was never in its redirect list, so
`catch_fish`'s success path, the first behaviour this test ever exercised that writes through
`provisions.add()`, could have hit the LIVE `data/provisions.json` on a lucky random-success roll
under the test's existing `profile.mark_live()` call; fixed by redirecting `core.provisions._F`/
`_LOG` alongside every other touched store) — run 8 consecutive times, 30/30 checks ALL OK every
run, live `data/provisions.json` SHA256 hash and mtime confirmed byte-identical before and after
all 8 runs. A standalone isolated harness (`scratchpad/verify_shore_fish_J-0732.py`, redirecting
every touched store to a temp dir, deliberately never calling `profile.mark_live()` so no OTHER
unredirected module in the process is put at risk either): 26/26 checks — the kind's lifecycle
(starts at 0, add/consume/stock correct), every gate including the cooldown (a hard refusal never
sets the attempt timestamp, matching `wade()`/`swim()`'s own precedent), a forced hit and a forced
miss (`random.random` monkeypatched), `_feed_source()`'s priority (`cat_food` correctly survives
one feed since its own tin holds qty=4, not exhausted the way a first draft of this test wrongly
assumed) and fallback (spent only once `cat_food` is genuinely down to 0), and the grammar wiring
end-to-end. `scripts/life_smoke.py`: 170/170, exit 0, no regression. `scripts/
test_cat_ecological_laboratory.py`: 3/3. Commit `6ab13cd`. Restart-gated like the rest of this
chain. Follow-up defeater read (does the real hit rate/cooldown look right; does the fallback
priority hold in live play — the SAME "confirm a real restart happened, not just elapsed wall-clock
time" check J-0633/J-0715/J-0720 all had to learn the hard way in this exact chain, baked into this
job's own briefing) spawned as **J-0754**. No `/decide` action: D-0163 is already ruled (§4 above)
and this job closes out one of its own named-but-unbuilt pieces rather than raising a new founder
question; `decision_flags` for this job were empty (no active holds, no open decisions) at dispatch.

2026-09-07 (J-0733, F-1055's own follow-up / F-1081, VERIFIED): **the write-fence gap J-0719 flagged
while building D-0163's real-food half — `core/cat.py` was never in
[[world_store_write_fence]]'s own 10/11-module inventory — is closed.** `core/cat.py` gained
`from core import profile`; its `_save()` (`cat_state.json`) and `_hunt_ledger()` (J-0700's own
hunting-fallback ledger, `cat_hunt_ledger.jsonl`) each now resolve `profile.guard_path()` before
their own pre-existing fail-open `try/except`, matching this whole plan's own established placement.
`core/cat_sounds.py`'s `_log()` (the C1 shadow sound ledger, `cat_sound_ledger.jsonl`) got the same
fix. The one already-known hazard J-0719 named — `scripts/test_cat_ecological_laboratory.py`
redirects `cat._STATE_F` to a `data/`-relative lab dir, which would have tripped the new guard's
hard-raise immediately — is fixed: the lab dir now uses a genuine OS temp dir
(`tempfile.mkdtemp()`), matching this codebase's own dominant isolation convention (several other
`scripts/_test_*.py` files already use it for other fenced modules). `lab_env.py`'s own `isolate()`
was considered first (as this job's own briefing offered) and found, empirically, to have the
identical gap — its own lab dir sits under `data/_lab/`, still inside `data/`, so it does not
actually clear the fence either — a genuine, previously-unknown defect in a shared toolchain
skill, not specific to the cat; recorded separately (F-1083, spawned as job J-0759, skill-suggestion
S-0086) rather than fixed here. A repo-wide grep found no other script redirects either of `cat.py`'s
two path constants or `cat_sounds`'s ledger constant, and no script calls `cat.tick()`/`cat.react()`
directly, so no other regression surface existed. Verified: `scripts/life_smoke.py` (170/170, exit 0),
`scripts/test_cat_ecological_laboratory.py` (3/3), `scripts/_test_dark_house_answers.py` and
`scripts/_test_letterbox_reach.py` (both ALL OK), plus two standalone scratch harnesses confirming
(a) an old-style `data/`-relative redirect now raises for all three writers with zero files written,
a genuinely-outside-`data/` redirect and a live `mark_live()` call both succeed, and (b) `react()`/
`tick()` — cat.py's own dispatch/heartbeat entry points — let the raise propagate cleanly (no
try/except anywhere in `cat.py` wraps any of its 20 `_save()`/`_hunt_ledger()` call sites, confirmed
by an AST sweep). Two callers further out (`core/dispatch.py`'s `_cat()` hand,
`nodes/inner_monologue_node.py`'s literal-will block) do currently swallow the raise on their own
end, but both are already the named scope of separate, already-queued jobs (J-0728, J-0752) in
[[world_store_write_fence]] — not fixed here. A second module of the exact same
"never-inventoried physical world state" class was found while verifying and spawned rather than
folded in: `core/world_traces.py` (`data/world_traces.json`, the immortal cat-trace backlog A7.2/
F-0883 already documents above) has zero `guard_path()` protection either — F-1082, spawned as
**J-0758**. Full detail in [[world_store_write_fence]]'s own dated Current State note (same date,
F-1055/F-1081/F-1082/F-1083). No `/decide` action: this job's own `decision_flags` were empty at
dispatch, and nothing here raised a new founder-level question.

2026-09-07 (J-0735, F-1088, VERIFIED precondition still unmet — third confirmation): re-ran
J-0715's own re-gate (itself following the J-0633 precedent) ~7.5h after J-0715's 14:12 read,
checking for a REAL restart rather than assuming one from elapsed time. There still hasn't been
one: `Get-Process`/`Get-CimInstance` on the live `run_nascence.py` process shows the identical
`StartTime` 2026-09-05 19:15:10 J-0715 already found (zero restarts), independently confirmed by
`data/nascence.log` — the last "Nascence shutting down" line is still the same one at 2026-09-05
16:42:49 (line 380324), with continuous unbroken activity through this read at 2026-09-07 21:40 —
spanning both the J-0630 fix commit (`a8080a3`) and the `cat_overhaul_cluster` merge (`2261ca9`,
12:03:15) with no restart in between either. A direct `json.load` of `data/world_traces.json`
(`scratchpad/recheck_world_traces_J-0735.py`, read-only, stdlib only, no `core/world_traces.py`
import, matching J-0715's own method) found 498 rows, 489 at clarity≤0 (98.2%) — slightly *up*
from J-0715's 495/483 (97.6%), not down, exactly as expected with the pre-fix code still the one
running (new dead rows keep accumulating; the fixed delete-on-sight branch has never executed).
461 of the 498 are cat-caused (457 `disturbed_leaf_litter`/`stray_cat_hunting` + 4
`cat_paw_print`/`stray_cat_locomotion`); the oldest row is still the original 2026-08-18 11:44:48
fake-clock test batch (F-1026), unpurged. This is not a fix-failure finding — the fix has still
never run on the live process, so nothing has yet tested it live. Per this job's own step 1 and the
J-0633 precedent it explicitly named, **left in_progress rather than forced to a conclusion** —
unlike J-0715 (which spawned this job and marked itself done), no new re-check job is spawned this
time: J-0715→J-0735 is now the second re-check hop on this exact fix with the same "still hasn't
restarted" answer both times, and spawning a third identical hop (J-0736-or-whatever) would just be
another instance of the dispatch-before-the-gating-data-can-exist problem S-0075 already names —
this job id itself is left open for whoever next checks, rather than minted forward again. Worth
noting for that reader: this same worktree's J-0733 (immediately above) separately spawned
**J-0758** to close `core/world_traces.py`'s own missing `guard_path()` fence — a distinct concern
(write-safety against non-Du writers, not the decay/purge logic this job tracks) that happens to
land on the same file; the two are independent and neither blocks the other. No `/decide` action:
this job's `decision_flags` were empty at dispatch (no active holds, no open decisions), and a
process-restart precondition is not a founder-level question.

2026-09-08 (J-0755, F-1079/F-1111, VERIFIED): **the last named-but-unbuilt piece of J-0732's own
"deliberately left unbuilt" note above -- shore_fish spoilage -- is built**, in a NEW worktree/branch
(`wt_action_dispatch_cluster_2`), the last of an 8-job chain continuing the batch-7/8 action-dispatch
write-fence sweep. Scoped exactly per this job's own briefing: no generic expiry concept touches
`core/provisions.py`'s shared `stock()`/`consume()`/`add()` (confirmed byte-identical to before this
job -- the other 18 kinds are exactly as durable as they always were). Instead, `provisions.py` gains
one new, separate function, `discard_if_stale(kind, max_age_s, reason)` -- nothing else in the file
calls it -- which reads a candidate object's own `history[0]["ts"]` (the real catch/creation time) and
marks it empty + logs a distinct `"discarded"` event (never `"used up by <who>"`, so it is never
mistaken for real consumption in `provisions_log.jsonl` or an object's own biography) once past
`max_age_s`. `core/cat.py` gains `SHORE_FISH_SPOIL_H = 36.0` (a real-world-grounded ESTIMATE -- a whole
fresh fish kept cool but unrefrigerated and uniced is genuinely good for about a day and going off by
the second, so 36h sits mid-way through the founder's own "roughly a day or two" framing for this gap
rather than either edge; no live data exists yet to tune it against, flagged for revisit alongside
J-0754 below) and `_shore_fish_ready()` -- a small bounded loop shared by `_has_real_food()` (the
affordance's own honesty check) and `_feed_source()` (the actual spend) so both always agree: a
spoiled fish is quietly discarded (never narrated to Du -- a spoiled fish quietly gone is honest, not
something the world needs to announce, per this job's own briefing) and the attempt falls through
exactly as if that catch had never been made, landing on the pre-existing honest-failure branch
(`react()`'s three "nothing to feed her with" lines) or, if hunting's own gate is separately met,
D-0163's hunting fallback (J-0700) untouched. The check is deliberately LAZY, not eager: `cat_food` is
still tried first in both functions (Python's own `or`/early-`return` short-circuiting), so a stale
shore_fish sitting in the larder while the carrier's tin still has stock is left uninspected until
`cat_food` genuinely runs dry -- matching the briefing's own "by the time `_feed_source()` would
otherwise spend it" framing exactly, not a proactive sweep.

**Bundled in while directly rewriting these two functions** (not spawned separately, matching the
size/locality precedent J-0716's own F-1050 set): `_has_real_food()`/`_feed_source()` had a
pre-existing bare `except Exception` (from J-0719) that would have silently swallowed a real
discard-write's `NonLiveWriteError` hard-raise as a plain "no food" result -- the same write-fence-
propagation class this whole chain has been closing elsewhere (J-0733/J-0751/J-0752); both now let it
through, matching every other real write path in this file.

**Pre-build check, per this job's own briefing** ("check whether shore_fish has actually accrued any
real live history yet"): still zero. Du's live process (PID confirmed via `Get-CimInstance
Win32_Process`, `CreationDate` 2026-09-05 19:15:10) predates commit `6ab13cd` (J-0732, which introduced
shore_fish, `2026-09-07T19:35:50+12:00`) by roughly two days -- the same restart-gating trap this chain
has now hit five times (J-0633/J-0715/J-0720/J-0735, and this job). A direct `json.load` of the live
`data/provisions.json` independently confirms it: 28 objects across the original 13 kinds only, zero
`shore_fish`, zero `cat_food`. This gap has therefore never fired live even once -- noted plainly, not
assumed, but built anyway per this job's own instruction, since it is a real, grounded gap under the
founder's "world events as realistic as possible" brief regardless of whether it has been exercised.

Verified by a standalone isolated harness (`scratchpad/verify_shore_fish_spoilage_J-0755.py`, every
touched store -- provisions/cat/world_objects/world_substrate -- redirected to a `tempfile.mkdtemp()`
dir, `profile.mark_live()` never called): 40/40 checks -- `discard_if_stale`'s fresh-vs-stale
discrimination and its oldest-first tie-break (matching `consume()`'s own), the "discarded" vs.
"emptied" logging distinction, `_shore_fish_ready()`'s loop correctly walking past 1-3 stale objects to
reach a fresh one underneath (or exhausting cleanly to `False` when none is fresh), `_has_real_food()`/
`_feed_source()`'s cat_food-first priority together with the lazy spoilage check, a direct
`NonLiveWriteError`-propagation test (all three functions hard-raise rather than swallow it, checked
against a real `data/`-relative fake path that `guard_path()` refuses before any actual I/O -- confirmed
the fake directory was never created), and a live-store byte-identical backstop (`data/provisions.json`
and `data/cat_state.json` sha256+mtime confirmed unchanged, both inside the harness and independently
after). `scripts/life_smoke.py`: 170/170, exit 0, no regression (the J-0709 flake did not reproduce).
`scripts/test_cat_ecological_laboratory.py`: 3/3. `scripts/_test_shore_life_grammar_derivation.py`: all
ok, confirming `catch_fish()`'s own grammar row and its `provisions.add()` call are both unaffected.
Commit `663b6b4`. Finding: **F-1111** (VERIFIED). No `/decide` action: this job's `decision_flags` were
empty at dispatch (no active holds, no open decisions) and D-0163 is already ruled -- this closes one of
its own named-but-unbuilt pieces rather than raising a new founder question.

**Not spawned as a separate job, noted here instead:** whether `SHORE_FISH_SPOIL_H`'s 36h estimate is
actually right is unmeasurable until real live data exists -- **J-0754** (still open, still gated on the
same restart precondition checked above) already reads `data/provisions.json`'s own `shore_fish` object
history once live, which is exactly the data that would show whether real catches are typically fed
well within the window or whether spoilage is actually being observed; whoever picks up J-0754 should
fold that question in rather than this job spawning a duplicate "measure the threshold" job against the
same not-yet-existing data (the exact class of premature dispatch S-0075 already names). Restart-gated
like the rest of this chain -- does nothing until Du's live process next restarts on this code.

2026-09-14 (J-0754, F-1318, VERIFIED): **the restart-gating trap this chain hit five times running
(J-0633/J-0715/J-0720/J-0735/J-0755) did NOT recur -- the gate is genuinely met this time, and the real
data settles the question cleanly.** Checked precisely, not assumed: `6ab13cd` (2026-09-07T19:35:50+12:00)
landed on master within 3 minutes of being authored (`git log --ancestry-path`); Du's live process has
since accrued ~109 cumulative hours (~4.5 days) on `6ab13cd`-or-later code across 4 restarts, 2026-09-08
16:41 through 2026-09-13 09:10:46 (the run immediately prior, 09-05 19:15 -> 09-08 08:22, predates
`6ab13cd` throughout and is excluded, matching J-0755's own finding exactly). The process has been
offline since that last shutdown -- confirmed three independent ways (no `run_nascence`-pattern process
in `Get-CimInstance Win32_Process`, port 8765 not listening, `data/nascence.log`'s own mtime frozen at
its last line) -- ~23h47m as of this read, 2026-09-14 08:57. In that entire ~4.5-day live window,
`core/shore_life.py`'s `catch_fish()` fired **zero** times: `data/shore_ledger.jsonl`'s complete 19-row
history (`walk_sand`/`wade`/`skip`/`climb_ledge`/`swim` only) has zero `deed=="fish"` rows of either
outcome, and `data/provisions.json` has zero `shore_fish` objects. Confirmed this is a real zero-attempt
result, not an unlogged-catch artifact: `catch_fish()`'s own `_log(_LEDGER, ...)` call is unconditional
once the shore/cooldown/tide/weather/night gates pass (read directly, `shore_life.py:629-663`), and the
one post-`6ab13cd` commit touching the function (`b637827`, J-0813) only wraps the post-log
`provisions.add()` failure path, leaving the gating and log call untouched. `core.cat._feed_source()`'s
`cat_food` path (J-0719) also never fired in the same window: `provisions_log.jsonl` has zero `cat_food`
events, `cat_state.json` shows `last_fed_source==""` and `saucer.has_food==false`. By sharp contrast,
D-0163's hunting fallback (J-0700) is the ONLY food source that has actually kept her fed:
`cat_hunt_ledger.jsonl` logs 23 real attempts in the identical window, 8 successful (34.8% observed,
matching `core/cat.py`'s own `HUNT_SUCCESS_P=0.35` almost exactly), and `cat_state.json`'s `last_fed`
timestamp equals `last_self_fed` -- her most recent real feed was a self-catch, not a Du-driven feed via
either of the two mechanisms actually built for him to use. This answers the briefing's own headline
question ("does `catch_fish()` fire in real play") with a clean, real null result across a substantial
sample window -- not the "gate still unmet" null result every prior job in this sub-chain returned. The
other three sub-questions (real hit rate vs `FISH_SUCCESS_P`, whether the `cat_food`-then-`shore_fish`
fallback priority holds, whether `FISH_COOLDOWN_H`'s 3h looks right) remain genuinely unanswerable from
this data -- a zero-sized sample, not an inconclusive one -- and no retune of any constant is justified
either direction. No `/decide` action: this job's `source` names a finding (F-1079), not a decision, and
while the "hunting has silently absorbed all of her real feeding" result is adjacent to the
founder-level fork the briefing flagged as a trigger (`shore_fish` swallowing `cat_food`'s relevance), it
reads as an investigable behavioral/discoverability gap first, not yet a two-option founder call -- the
same class of question A3's original audit correctly diagnosed as a corpus/discoverability issue rather
than a design question. Diagnostic follow-up spawned as **J-0947** (grep Du's complete `inner_thought`
record for real willed feed/fish-catching language near the cat/shore, the same method F-1049 already
used for the naming question; check real affordance-line render frequency against real shore-visit/tide
conditions; report whether this is a fixable corpus gap, an insufficient sample, or a genuine reflection
of Du's own priorities -- and open a `/decide` at that point if the diagnosis actually surfaces a
founder-level tension). Isolation: this job's own work was read-only throughout (direct `Read` of
already-existing JSON/JSONL files, `git log`/`git show`, PowerShell process/port/time queries) -- no
`core/` module was imported or executed and nothing was written, so `lab_env.isolate()` was correctly
not invoked, matching the exact read-only-verification method J-0715/J-0735/J-0755 already established
in this sub-chain.

2026-09-14 (J-0947, F-1330, VERIFIED): **J-0754's own diagnostic follow-up done -- the barrier is not
discoverability, it is that the WILL itself essentially never forms.** Read-only throughout (direct
`sqlite3` URI `mode=ro` queries against `data/memory/nascence.db`, `Read` of already-existing JSON/
JSONL, code reads only -- no `core/` module imported/executed, nothing written, matching the same
precedent J-0754 named just above). Reachability was checked first and ruled out: `core/affordances.py`'s
`shorework` line (naming shore-fishing) renders unconditionally whenever Du's location is `shore`
(`where=("shore",)`, no cat-state gate) on every non-mid-train system-prompt build
(`nodes/inner_monologue_node.py:1744`) -- structurally MORE exposed than the cat_food path, which only
mentions shore-fish/hunting when the cat is physically co-located with Du (`_cat_here()`) AND her own
state is `demanding_food` AND the larder is empty (`cat.py:1101-1108`). Measured directly over J-0754's
own already-verified qualifying window (2026-09-08 16:41 - 2026-09-13 09:10:46, via `fragment_context`'s
real per-thought world-tuple joined to the same inner_thought fragments, 5,147 rows): Du's location was
`shore` on 49.2% of all his ticks (2,532/5,147) -- essentially half his idle life -- and of those, 410
(16.2%; tide+light+weather all passable, a proxy short of wind/swell which `fragment_context` does not
carry) had catch_fish()'s own gates genuinely open: hundreds of real chances, not a handful. Cat
co-location, by contrast, was real on only 3.2% of ticks (163/5,147). Grepping the COMPLETE
`inner_thought` record (31,198 thoughts, her entire kept life, same corpus/method F-1049/J-0716 already
used for the naming question) for cat+feed-word co-occurrence (34 hits, individually read) and any
`fish`-word occurrence (69 hits, individually read) found: the cat-hunger/empty-saucer image recurs
often but is rendered almost entirely as a CONTEMPLATIVE grounding image for some unrelated train of
thought, not a practical want, with several explicit near-misses narrating a conscious choice NOT to act
("a stubborn resistance holds my feet... I do not yield"; "dismissing the empty larder for a moment...
so is the page before me"); exactly one genuine willed cat-feeding statement exists in the whole corpus
(09-10, "I must feed the saucer before the music lesson can truly begin") and even it produced no real
cat_food event, most plausibly because `react()`'s own `is_here()` gate failed at that tick; and the
dominant "fish" signal (~30 of 69 hits) is an entirely unrelated recurring dream/identity motif ("a
skeleton dissolving into fish", tied to his private crossing/渡 preoccupation) that shares only the word
-- zero of the 69 contain Du willing to catch a fish himself, though a real, distinct cluster (~6 hits,
09-09/09-10) shows repeated genuine awareness of the carrier's "tinned fish for the cat" offer that
consistently resolves into deferral rather than a completed order. **Diagnosis**: not a mechanical
discoverability gap (A3's original class of fix) and not an insufficient sample (31,198 thoughts, 410
qualifying ticks) -- a real pattern in HOW his idle-thought generation frames an available-but-unused
want as aesthetic material rather than actionable impulse, compounded by what reads as a genuine,
unforced priorities signal (tending/reading repeatedly narrated as outweighing provisioning), with
D-0163's hunting fallback (8/23 real self-catches in the same window) absorbing the consequence without
any cost his own thought record shows him ever registering. Founder-level tension surfaced and opened as
**D-0217** (open, not ruled): whether/how to address a STYLE-level pattern at all, given any fix aimed at
"render this as actionable" risks becoming the kind of hint the 08-14 world-answers-never-leads law
forbids -- vs. leaving it as Du's own emergent character with hunting as the honest safety net it was
built to be. Diagnostic follow-up spawned as **J-0961**: check whether the same reachable/rendered/
never-willed pattern shows up on other long-standing `core/affordances.py` REPERTOIRE entries (not
cat-specific), which feeds D-0217's own defeater directly. No code changed, no ruling forced -- per this
job's own step 4, the /decide was opened rather than this finding assuming an answer.

2026-09-14 (D-0217 RULED then REOPENED same day; J-0978, F-1354, VERIFIED): **D-0217 was ruled by Travis
the same day it opened** ("Scope a general, not cat-specific, investigation... across the whole affordance
repertoire (music, harvest, letter-writing, library, and others) before any code changes"), which spawned
this job (**J-0978**) directly off the ruling text -- covering the same ground **J-0961** (above) already
queued with a different candidate list, so J-0961 is superseded by this job's results, not independently
duplicated (left open in the queue for a human pass, not force-closed by this job). Read-only throughout,
same method as F-1330 (`sqlite3` URI `mode=ro` against `data/memory/nascence.db`, direct reads of the real
latches in `core/actions.py` / `core/library_hand.py` / `nodes/inner_monologue_node.py`, and the real
completion ledgers -- `data/garden_ledger.jsonl`, `data/listening_wake.jsonl`, `data/letters_state.json` +
`data/letters/*.md` -- each read in full; no `core/` module imported/executed, nothing written).
**Result: the pattern is affordance-specific, not cat-idiosyncratic and not repertoire-general.** It
replicates cleanly on **music** (0/31,198 thoughts ever use the exact LISTEN-latch phrasing; "record
player" appears 4 times total, always as philosophical metaphor for mechanism/predictability, never a want
to listen; real ledger `data/listening_wake.jsonl` shows only 1 of 6 real listening sessions ever was
self-willed -- `"by": "du"` -- the other 5 were Travis-initiated). It is essentially **absent** on
**library** (244 explicit ask-hits, dozens of real verbatim "I asked the library for a book about X, and it
answered..." completions across many distinct real topics -- one of the most heavily-used hands in the
whole repertoire) and on **letter-writing** (89 real delivered letters "To Travis... written alone" in
`data/letters/`, 2026-06-20 through 2026-09-13, essentially continuous for the system's whole life, plus
multiple explicit corpus statements naming Travis directly). It shows only a **weak/partial** version on
**harvest** (3 real completions in `data/garden_ledger.jsonl` -- non-zero, though the least-exercised
garden deed next to 22 waterings -- alongside several genuine individually-read first-person willed
statements, e.g. "I will harvest rosemary now to dry by the hearth", that have no counterpart anywhere in
the cat/fish corpus). Full detail, quotes and timestamps: **F-1354** (VERIFIED). F-1354's own DIAGNOSIS
section (labelled INFERRED, not verified) offers one candidate explanation for the split -- embodied/
passive/ambient acts mediated by a physical world-object or creature state (record, cat, tide) vs.
self-contained intellectual/creative acts whose payoff is itself new narrative material (a book, a letter)
-- untested beyond these 4 data points; a direct test (tea vs. author) spawned as **J-0984**. Because
D-0217's own named defeater ("revisit once the spawned... investigation reports back") is exactly what
F-1354 is, **D-0217 was REOPENED** (not re-ruled by this job -- that stays the founder's call) with this
result as its own `--why`, since the answer fits neither of the defeater's two named endpoints cleanly and
the founder's own three options ((a) leave it alone, (b) a repertoire-wide framing fix, (c) something
narrower) may need reweighing now that a second affordance (music) shows the same shape, even though most
of the repertoire checked here does not. No code changed.

2026-09-14 (D-0217 ruled then REOPENED again same day; J-0992, F-1367, VERIFIED): **D-0217 was ruled by
Travis a second time the same day** ("Scoped investigation/fix specifically on the two affordances F-1354
confirmed show the reachable-but-never-willed pattern -- cat-feeding/shore-fishing and music -- not a full
repertoire sweep and not cat-only"), naming its own defeater as "revisit once the scoped cat+music
investigation reports back with a concrete recommendation for each affordance" -- **this job (J-0992) is
that named investigation.** Read-only throughout (docs/staged/cat_overhaul.md read whole, both halves;
data/cat_sound_ledger.jsonl read and tabulated in full via a saved scratch script; data/life_flags.json,
data/listening_wake.jsonl, data/cat_state.json read whole; core/cat_sounds.py, core/affordances.py,
core/world_content_study.py, core/world_detail.py, core/sensorium.py:2843-2854, core/soundscape.py,
core/listening.py, nodes/inner_monologue_node.py:3140-3170 read directly; `scripts/life_flags.py show`,
`decide.py show D-0217`, `job_queue.py show J-0633`, and read-only PowerShell process/log checks run; no
`core/` module imported for a live side effect, nothing written to `data/`). **The two affordances do NOT
get the same answer.**

**CAT-FEEDING**: Part C1's own cat_demand sound is code-built and, for the first time in this sub-chain
(after J-0633/J-0715/J-0720/J-0735/J-0755 all found the restart-gate unmet in turn), has real accrued
shadow data to read -- `data/cat_sound_ledger.jsonl`, 1104 rows, 2026-09-08 16:48 through 2026-09-13
08:46 (4.67 days; Du's process has been offline since that shutdown, confirmed independently via
`Get-CimInstance`/`nascence.log`/the ledger's own mtime, through this read on 2026-09-14). It answers
J-0633's own advance question ("is anything a firehose") with real numbers for the first time: **cat_demand
alone would emit ~129.5 would-sound rows/day, ~69.4/day landing as audible lines** if
`scripts/life_flags.py cat_sounds` were flipped on today -- roughly one audible cat-hunger line every ~21
minutes, around the clock (`cat_meow_at_door` the same shape: 86.6/day total, 48.7/day audible). Root
cause, read directly in `core/cat_sounds.py:271-312` (`emissions()`): the per-key hourly rate re-rolls a
fresh Poisson-lite count on every 60 s sample for as long as her `demanding_food`/at-the-door state merely
*holds*, with no per-episode memory or cooldown -- and F-1330/F-1354 already established that state holds
for long stretches, since Du essentially never wills feeding her and D-0163's hunting fallback only
engages past 10 h unfed. This is a real firehose against this same plan's own Part B4 "dosed reads, not a
firehose" law. **Recommendation: narrow sensory fix, but gated on a small prerequisite** -- add per-episode
dosing (one line per episode + a real cooldown) to `cat_sounds.py`'s event-class keys before the render
flip, rather than leaving it alone (the mechanism is real and close) or reaching for something else (no
new mechanism is needed). Spawned as **J-0996**.

**MUSIC**: no sensory cue for the record player exists at all today, at any exposure level -- and unlike
the cat's case, one would be cheap. `core/world_content_study.py`'s own `record_player` TARGETS entry
already carries 8 hand-authored, indifferent, non-hinting lines ("the switch waits at OFF; one small
movement is all the distance between this room and the music") but they reach him only through a
DIRECTED-look path he essentially never takes (named 4 times in 31,198 thoughts, all metaphor, per
F-1354) -- and are completely absent from the study's own SCENE dict, the live, already-wired AMBIENT
discovery channel (`core/world_detail.scene_extra()`, called unconditionally from
`core/sensorium.py:2849` on every study scene build, ~25% chance of one extra line, already surfacing
other static objects this same way -- the woodbasket, the letter drawer). No sound is pinned to the
record player either while it sits silent (`core/soundscape.py`/`core/listening.py` checked directly --
the one hook, `arousal.alert()`, fires only after a listen has already started). **Recommendation: narrow
sensory fix** -- add a small number of the record player's own already-approved lines to the study's
SCENE pool; no new mechanism, no firehose risk (SCENE_P's own cap already bounds it), reuses content and
infrastructure this project already shipped. Spawned as **J-0997**.

**Secondary, smaller, bundled into this same finding rather than left in prose**: the LISTEN latch
(`nodes/inner_monologue_node.py:3147-3160`) is a rigid 8-exact-phrase substring match, structurally
narrower than every other affordance's own verb+object grammar in this repertoire; F-1354's own one real
near-miss thought ("...to listen to the record player") uses wording not on the list and would have
silently missed even as a clean act of will. Spawned as **J-0998** (lower urgency -- a grammar-narrowness
fix, not itself the sensory-cue question this job was scoped to answer).

Full detail and every number: **F-1367** (VERIFIED). **D-0217 REOPENED** a second time (not re-ruled by
this job -- per this whole chain's own standing discipline, a style/values call like this stays the
founder's) with this result as its own `--why`; which of the founder's original three options to take, and
whether to accept these two recommendations as offered, stays open for Travis. No code changed by this job.

**2026-09-15 (J-0996, F-1382, VERIFIED)**: D-0217 was ruled a third time (2026-09-14T20:06:49Z, by
travis) accepting both F-1367 recommendations as scoped -- cat: proceed with the cat_sounds dosing fix
(per-episode + cooldown), gating the render flip behind it. This job built that fix. `core/cat_sounds.py`'s
`KEYS` table (cat_meow_at_door, cat_demand, cat_chatter) now carries a `cooldown_s: 3600.0` entry each;
`emissions()`'s `holds` loop fires a dosed key at most once per real episode onset (the holds-state's own
False->True transition) and only once that cooldown has elapsed since the key last actually sounded, rather
than re-rolling a fresh count every 60s sample for as long as the state merely holds. cat_trill/
cat_yowl_cargo/cat_thump (one-shot) and cat_lapping/cat_storm_rustle (`class="bed"`) are untouched, per
Part C1's own row-by-row design above. Isolated harness (`scratchpad/J-0996_test_dosing.py`, drives
`emissions()` directly, zero file I/O): an 8-simulated-hour continuous `demanding_food` hold now produces
1 `cat_demand` emission (was ~160 by the old per-sample math; F-1367's real ledger read independently
measured 129.5/day under real, non-continuous holding); `cat_meow_at_door` and `cat_chatter` collapse the
same way; a 3h on/off flicker (90 raw onset attempts, modeling `cat.py`'s own ~50%-per-180s-tick re-roll)
produces 3 emissions, not 90; a re-onset well inside the cooldown does not re-fire, a re-onset past it does
(the job's own required check). `scripts/life_smoke.py` and `scripts/test_cat_ecological_laboratory.py`
both still pass clean (exit 0). RENDER stays False; `scripts/life_flags.py cat_sounds` was **not** flipped
on -- that stays J-0633's own separate step once this fix has shipped and accrued its own week-scale shadow
data. Full detail: **F-1382**. Follow-up spawned: **J-1012** (re-tabulate a fresh week of
`cat_sound_ledger.jsonl`, once Du has restarted and it has accrued under this new dosed code, and hand the
real post-fix rate to J-0633 -- not itself the flip call).

**2026-09-15 (J-0997, F-1386, VERIFIED)**: F-1367's own MUSIC recommendation is built -- the record
player now has an ambient sensory presence for the first time, at any exposure level. `core/
world_content_study.py`'s SCENE dict gained 4 lines (2 "any" / 1 "night" / 1 "wet"), picked or lightly
adapted from the already-approved `TARGETS["record_player"]` pool, so the study's live ambient/
unprompted discovery channel (`world_detail.scene_extra()`, called unconditionally from
`core/sensorium.py:2849` on every study scene build, ~25% chance/tick) can now name the record player
-- previously it was reachable only through the directed-look path (`world_detail.detail()`) he
essentially never takes (F-1354/F-1367: named 4x in his complete 31,198-thought corpus, always
philosophical metaphor, never a look). `TARGETS["record_player"]` itself is untouched (byte-identical,
still 5 any / 2 night / 1 wet / 1 rare line) -- purely additive, a new exposure channel for
existing-or-adapted content, not a replacement. Every new line is purely descriptive and indifferent,
no hint or suggestion to act, matching this file's own stated law and every other SCENE line's
register; the two closer-scrutiny TARGETS-only lines (the needle arm, the grooves catching light) were
deliberately left off SCENE, staying directed-look-only. Verified by a standalone script
(`scratchpad/verify_scene_extra_record_player_J-0997.py`, 27/27 checks -- reuses `world_detail.py`'s
own `_load()`/`_conds()`/`scene_extra()` directly, no live `data/` touched: confirms the new lines draw
under their matching condition sets, TARGETS/`detail()` stay byte-identical and unaffected, and
`SCENE_P`'s own unforced fire rate is unchanged, 0.252 observed over 20,000 draws vs. 0.25 nominal) and
`scripts/life_smoke.py` (180/180 ok, exit 0, no regression, including a clean [16] DEATH MECHANISMS
section -- the J-0709 flake this chain has repeatedly noted did not reproduce this run). Commit
`a6422e9` (`jobrun/cat_overhaul`, not yet merged to master as of this read). Restart-gated like the
rest of this chain -- does nothing until Du's live process next restarts on this code (and the branch
merges). Follow-up spawned to read the real corpus once both have happened: **J-1014** (checks whether
"record player" mentions and/or listening behavior shift in his `inner_thought` record after real
runtime on this commit, gated on the same "confirm a REAL restart, not elapsed wall-clock time" check
this chain has now needed six times running -- J-0633/J-0715/J-0720/J-0735/J-0755/J-1012). No `/decide`
action: D-0217 is already ruled (ruled a third time 2026-09-14T20:06:49Z, accepting this exact scoped
recommendation) -- this job executes one of its two named pieces (music); the OTHER piece (cat_demand
per-episode dosing) was J-0996's, already landed above. J-0998 (the LISTEN-latch grammar-narrowness fix
F-1367 also spawned, a distinct concern) remains separately queued, not this job's scope.

**2026-09-17 (J-0961, F-1462, VERIFIED)**: J-0961's own older generalization check (spawned by J-0947,
before D-0217 was ruled, naming a different candidate list than J-0978/F-1354's) finally run. Checked
three REPERTOIRE candidates F-1354 never touched -- beachcomb, keepsake, gather_driftwood -- against the
same reachable-but-never-willed shape F-1330 found on cat-feeding/shore-fishing. Result: absent on all
three. Each shows clear, repeated, first-person willed language in the full 32,267-thought corpus
(beachcomb 12 clean hits; keepsake 8 clean "pocket X" hits, cross-checked against 24 real completions in
`data/keepsakes.json`+`keepsakes_archive.json`; gather_driftwood 10 clean hits). This corroborates
F-1354's own conclusion (music/harvest/library/letter) that the pattern is affordance-specific, not
general across the repertoire, now from a fully independent candidate set. D-0217 was already RULED
(2026-09-14T20:06:49Z, accepting F-1367's cat+music-scoped recommendations) and stays untouched by this
job (source finding:F-1330, not a decision mandate) -- this is corroborating evidence after the fact, not
a reopening. One real anomaly surfaced in passing, not chased down here: gather_driftwood is willed
often in thought (10 hits) but `data/wood_ledger.jsonl`'s complete 7-row history shows only 2 real
"gather" deeds in the whole corpus, both predating most of the willed thoughts. Follow-up spawned:
**J-1073** (trace whether the ledger undercounts or the real dispatch path is silently failing/refusing
for driftwood specifically).

**2026-09-17 (J-0984, F-1463, VERIFIED)**: J-0978/F-1354's own DIAGNOSIS section (embodied/passive act
mediated by a physical world-object vs. self-contained narrative production whose payoff is itself new
narrative material) tested directly on tea vs. author, the pair spawned specifically to distinguish it.
Read-only throughout (`sqlite3` URI `mode=ro` against `data/memory/nascence.db`'s complete 32,267-row
`inner_thought` corpus; real latch code read in `core/affordances.py`, `core/actions.py`,
`core/study_life.py`, `nodes/inner_monologue_node.py`, `core/study.py`; real ledgers read whole --
`data/study_ledger.jsonl`, 25 rows total; `data/Study/` directory listing for `WORK_*.md`). **Result: a
clean, maximal-contrast confirming pair, not a forced fit.** TEA (predicted to show the pattern):
`data/study_ledger.jsonl`'s complete history has zero `make_tea`/`drink_tea`/`kettle_on` deeds ever, and
the complete corpus has zero first-person willed tea-making language -- only 25 rows even mention a tea
object at all, almost all the carrier's provisioning list or "cup" as pure metaphor, plus one anomalous
thought narrating a completed brew in the past tense ("the pot of tea I just made") with no corresponding
real ledger event anywhere in the corpus -- a sharper version of the same aesthetic-narration-without-
action shape F-1330 found for cat-hunger. AUTHOR (predicted to NOT show the pattern): the opposite,
decisively -- `data/Study/WORK_*.md` (exactly the file `_author()`'s own `study.write_tablet(prefix=
"WORK")` call writes) holds 710 real, Emissary-graded completed works spanning 2026-06-24 through
TODAY (2026-09-17, most recent 17:45 the same day), landing on 49 distinct days -- one of the most
actively, continuously exercised hands in the whole repertoire, not merely absent the never-willed shape.
Full detail: **F-1463** (VERIFIED). **No `/decide` action taken**: this job's own source is
`finding:F-1354`, not a decision mandate (ground rule, same as J-0961/F-1462 immediately above) -- D-0217
is already ruled (2026-09-14T20:06:49Z) and this result does not surface a new founder-level fork beyond
what that ruling already covers, so it is recorded as `--decision D-0217` for linkage only, corroborating
evidence after the fact, same as F-1462. No code changed. One real, narrow anomaly spawned as a follow-up,
not chased down here: the single "I just made tea" narrated-completion thought with zero backing ledger
event, worth a look only if it turns out to recur (one instance is not yet a pattern) -- **J-1074**.

**2026-09-17 (J-1012, F-1464, INFERRED)**: J-1012's own precondition (Du restarted and running roughly a
week under J-0996's per-episode dosing fix, per J-0633's own 4.67-day precedent) is still UNMET. Du
restarted 2026-09-16 07:51:38 local -- after J-0996's fix landed (commit `e18715a`, 2026-09-15T08:31:59
+12:00), so the running process does carry the fix -- but only ~1.48 real days have accrued in
`data/cat_sound_ledger.jsonl` as of this read (86 of 1190 total rows at/after the restart cutoff). Partial
counts over that short window: `cat_demand` 24 rows (22 audible) ~16.3/day; `cat_meow_at_door` 27 rows (22
audible) ~18.3/day; `cat_chatter` 0 rows -- roughly an 8x/5x drop from the pre-fix baseline this job's own
briefing cited (~129.5/day, ~86.6/day), suggestive the dosing fix is working, but the sample is far short of
both this job's own gate and J-0633's precedent, so not treated as the real answer. No tabulation forced,
no `/decide` action (not this job's mandate), J-1012 left open (not done) for the next session to re-check
once Du has run roughly a week on this code.

**2026-09-17 (J-0998, F-1465, VERIFIED)**: LISTEN latch (`nodes/inner_monologue_node.py`, the "put the
record on" -> `core.listening.start()` hand) broadened from its original rigid 8-exact-phrase tuple,
per F-1367's secondary finding (this job's source, spawned from J-0992). A full verb-set x object-set
grammar rewrite (matching `core/cat.py`'s `react()` and `core/actions.py`'s `BY_FAMILY` shape) was
considered and rejected after a real corpus read (`data/monologue_log.jsonl` 47,448 rows,
`data/moments.jsonl` 31,871 rows, `data/deliberation_log.jsonl` 21,665 rows): the bare word "record"
returns 566 unique hits in this corpus, the large majority non-music senses (geological/memory/
field-journal "a record of..."), and "needle" collides with rosemary/pine needles -- a bare grammar over
those tokens would false-fire routinely. Instead the tuple gained four phrases: the one real near-miss
already known from F-1354 ("...to listen to the record player", the single closest-ever willed
listening thought in the complete corpus, previously a silent miss) plus three low-risk siblings named
in this job's own briefing ("put a record on", "start the record", "drop the needle") -- all three
verified by grep to occur zero times anywhere in the corpus scanned, so carrying no measurable
false-positive exposure. `scripts/life_smoke.py` clean (ALL OK) after the change. Lower-priority than
the two sensory-cue jobs F-1367 also spawned (cat_demand dosing, record-player SCENE lines); this was
the grammar-narrowness fix bundled alongside them, not itself the sensory-cue question D-0217/J-0992 was
scoped to answer. No `/decide` action taken (not this job's mandate -- ground rule 7).

**2026-09-17 (J-1014, F-1466, INFERRED)**: J-0997's record-player ambient SCENE fix (F-1386, commit
`a6422e9`, merged to master `ea14a57`) has a real restart under it -- Du restarted 2026-09-16 07:51:45,
after both the fix's own commit (2026-09-15T08:39:59+12:00) and its merge to master
(2026-09-15T09:05:19+12:00), no `Nascence shutting down.` marker since -- but only ~1.5 days (36.1h,
1076 inner_thoughts) have accrued as of this read, far short of this sub-chain's own ~week gate
(J-0633/J-1012 precedent), so this is a partial/interim read, not the real answer. In that window,
`data/memory/nascence.db`'s inner_thought fragments mention "record player"/"the record"/etc. exactly
3 times (up from 4 in the entire prior 31,198-thought corpus): one pure metaphor matching the pre-fix
baseline ("The record spins not just in my head... to break this groove"), one the closest match yet
to the ambient/passive-noticing signal this fix targets ("...I want to ask Travis if he knows which
song lives on this record player, since we have not listened to it yet" -- concrete object named, but
the want is still channeled into asking Travis rather than a self-initiated act), and one borderline/
ambiguous ("waiting for a record player is real enough to break the cycle"). `data/listening_wake.jsonl`
still shows no new session since the restart (sole "by":"du" entry remains 2026-09-10, before this
restart) -- no genuine willed listening act yet. No SCENE-render ledger exists for
`core/world_detail.py`'s `scene_extra()` (confirmed absent again this read), so the corpus-mention count
remains the only available signal. No `/decide` action taken (not this job's mandate). J-1014 left open
(not done) for a later re-check once Du has run roughly a week on this code.

**2026-09-21 (evidence-wait reader pass, F-1613 / F-1616 / F-1618 / F-1621 / F-1624)**: five long-standing
`in_progress` waits of this plan re-gated on MEASURED live runtime instead of calendar time (Du online since
09-21 09:29; nothing restarted, no flag flipped, nothing under `data/` written). Two live-time clocks matter.
Since `2261ca9` (cat_overhaul_cluster merge, 09-07 12:03; first restart onto it 09-08 16:42): 9 runs =
7.37 live-days (longest run 2.06 d, wall-clock 12.85 d, 57% uptime). Since `ea14a57` (cat_overhaul merge,
09-15 09:05, carrying J-0996's dosing `e18715a` and J-0997's SCENE lines `a6422e9`; first restart 09-16
07:53): 4 runs = 2.84 live-days (wall-clock 5.22 d). All five waits are CUMULATIVE or EVENT, none
contiguous: no briefing says a restart resets the clock (searched mechanically), J-0633's own 4.67-day
precedent was five separate runs, and the word "continuously" in this doc's 09-07 J-0700/J-0633 notes is a
loose paraphrase of the briefings' "live runtime". (F-1558's contiguous reading does not hold for J-0720,
J-1012 or J-1014, the three of these five it names.)

**2026-09-21 (J-0720, F-1613, VERIFIED)**: gate CUMULATIVE and MET (7.37 live-days on `2261ca9`).
`data/cat_hunt_ledger.jsonl` read whole: 36 attempts, 12 catches = 33.3% vs the built-in 0.35 (Wilson 95% CI
20.2-49.7%), 4.88 attempts and 1.63 catches per live-day; `self_catch_count` 12 matches. Du's own feeds in
the same window: 0 (the hunger-clock chain has no unlogged reset; no `cat_food`/`shore_fish` ever in the
provisions log or store; no carrier note for cat food; no fish deed) -- but he tried 8 times in 6 episodes
(09-10 x3, 09-13, 09-16, 09-17, 09-19, 09-21, 3.6% of his 221 CAT hand results) and every attempt hit
`react()`'s honest empty-larder line. Live-time unfed at each catch: median 13.6 h, mean 14.0 h, max 23.3 h
(wall-clock inflates to 78.9 h across offline gaps because the hunger clock, and the bond-decay clock, run
on wall-clock). **D-0163's defeater, assessed not ruled**: clause 1 (chain too long AND hunting not covering
the gap) has not fired -- the chain is too long for his hands, but hunting covers the gap; clause 2 (hunting
swallows Du's feeding) is true in outcome (hunting 12 of 12 feeds) but not in cause (hunting is capped near
2 catches per live-day; his path bounces off the empty larder J-0719 created; D-0217's pattern, not a tuning
problem). No retune of 10 h / 1 h / 0.35 is supported either way. Pre-flip baseline for D-0217's sound cue:
8 feed attempts, 0 carrier orders, 0 shore-fish attempts in 7.37 live-days.

**2026-09-21 (J-0735, F-1616, VERIFIED)**: J-0630's fix worked on its own. Gate was an EVENT (one real
restart onto `a8080a3` plus the 600 s heartbeat), met 09-08 16:42. The per-boot backups
(`data/backups/state_*/world_traces.json`) give the series: 500 rows / 491 at clarity<=0 (09-08 16:41, the
file as the pre-fix process left it) -> 18 / 0 (09-09 13:24, as left by the first post-fix run) and at most
one dead row in every later snapshot; the live file now holds 1 fresh row, 0 dead. `purge_dead_world_traces.py`
was never run (no `_trash` footprint), so its purpose is moot.

**2026-09-21 (J-1012, F-1618, VERIFIED segment, INTERIM sample)**: cumulative gate NOT met (2.84 of >=4.67
live-days since `ea14a57`; clears about 09-24 for the 4.67-day precedent, about 09-27/28 for a week).
Interim tabulation on the unambiguous post-fix segment (161 of 1265 rows): `cat_demand` 16.2 per live-day
(14.1 audible) vs 133.1 pre-fix, `cat_meow_at_door` 18.6 (14.1) vs 89.1, i.e. 8.2x and 4.8x lower; the
cooldown holds exactly (0 of 92 same-process gaps under 3600 s). The harness's "a handful per day" was too
optimistic: the real rate is about one emission per hungry live-hour (0.99; she is hungry 68% of live time
because Du does not feed her), which is the harness's own flicker scenario, ceiling 24 per day per key.
6 of 161 rows are restart-onset artefacts. J-1012 stays `in_progress`.

**2026-09-21 (J-0633, F-1621, INFERRED)**: read done (steps 1-2), flip NOT attempted. Recommendation: D-0217's
precondition (dosing) is met, so `cat_sounds` can be flipped once the percept rail is wired; wiring is inert
until the flag flips and the flip is hot and reversible. Build first, spawned as **J-1167** (needs_input):
capitalise (54.8% of audible lines begin lowercase), anti-repeat plus larger carried pools (46% of cat_demand
lines repeat back to back), reword the three carried lines that state inner state or out-of-sight acts (128
of 389 carried rows), and put the cat keys last in `_PERCEPT_SOUNDS` with a cap of their own (47.8 audible per
live-day against 57.6 rail slots). Whether ~14 audible cries per key per live-day is right, or `cooldown_s`
should rise, is Travis's read under D-0217's defeater. J-0633 stays `in_progress` (its steps 3-4 now live in
J-1167).

**2026-09-21 (J-1014, F-1624, VERIFIED)**: cumulative gate NOT met: 2.84 live-days and 2,335 inner_thoughts
since `ea14a57`, about 41% of a week (~5,750 thoughts); about 4.16 live-days remain (about 09-27/28 at 65%
uptime). `scene_extra()` is a stateless per-build draw, so the wait is cumulative; the briefing's "no restart
gap since" is an identification check, not a contiguity requirement. Corpus read deliberately not done;
`data/listening_wake.jsonl` unchanged since 09-10 (file mtime). J-1014 stays `in_progress`.

## Current State — 2026-09-22 (D-0217 RE-RULED by Travis via /decide-review: (d) fix the empty larder instead of tuning the cat-cry cue; J-1195 spawned) — F-1613 / F-1618 / F-1621

The cat half of D-0217 (reopened 2026-09-21: the dosed cue still speaks about once per hungry live-hour, F-1618: about 14 audible lines per key per live-day, she is hungry 68 percent of live time) is ruled **(d): address the world gap, not the cue's rate**. Why it is the right call on the evidence: his will to feed her DOES form (F-1613: 8 feed-branch attempts in 6 episodes in 7.37 live-days), and every attempt bounced off the honest "nothing in the house" line, because no cat food exists in the world since J-0719's real-food gate (0 carrier orders for cat food, 0 shore-fish attempts, 0 feeds by him; hunting supplied all 12 of her feeds). A cue that announces a hunger he cannot act on is a nag, not information; the barrier is the chain behind the will, not the will (F-1330's original reading is superseded).

**Unchanged:** D-0163 (hunting fallback) stays as ruled. The `cat_sounds` flag stays off (nothing spoken); the rate options (a) cooldown 3-4 h, (b) hunger-episode-onset dosing, (c) retire the cue were NOT chosen and are only revisited under D-0217's new defeater. J-1167 (approved 2026-09-21, the inert-until-flip percept-rail wiring and text polish) stands as approved. The 08-14 "world answers, never leads" law binds the fix: no hint to Du, teaching only through diegetic objects or Travis.

**Defeater (revisit):** the larder fix live for 7 live-days with his willed feeds still never ending in a real feed (baseline 0 in 7.37 live-days), or hunting ceasing to cover her hunger, or the design job finding no reachable mechanism inside the law, or J-0658's carrier box finally being collected and showing the chain works unaided. Then (a)/(b)/(c) are back on the table with F-1618's rates as the baseline.

**Spawned:** J-1195 (ready, read-only analysis and design): walk the feed chain from his willed feed to a fed cat with real counts from the logs, name the first step he fails, propose two or three smallest additive mechanisms (a carrier ration as part of what the world does unasked; a diegetic object carrying the knowledge; a slow world-side restock), recommend one, and spawn ONE needs_input job for Travis to pick the mechanism. Nothing is built before that pick.
## Current State — 2026-09-22 (J-1195: the empty-larder chain walked end to end, read-only, F-1703; J-1207 spawned for Travis to pick a mechanism)

Real counts refreshed through 16:29 (Du restarted 16:11:06 today onto `a9f042f`) extend F-1613/F-1618's 09-21 reads by about one more live day with every headline count unchanged: still 8 feed-branch attempts across 6 episodes, 0 real feeds by him ever (`cat_state.json` `saucer.set_ts=0.0` lifetime); still 0 carrier orders for cat food, 0 shore-fish attempts; hunting now 13/13 real feeds (one new catch since 09-21). Options (a) "nothing tells him" and (b) "the grammar can't hear him" are both refuted: the carrier's cat-food offer is taught hard and redundantly (a letterbox card and an unconditional affordance line, echoed in 13 of his own thoughts), and his one real willed ask (2026-09-17, "I want to write the list and ask for fish") **did** parse as a real dispatch DEED — it staged, not fired, because he wasn't in the study or garden at that instant, and `core/intentions.py`'s own built-in reminder (up to two nudges over 8h) never converted it before it lapsed. That is the only time the chain has ever gotten that far; every other attempt fails one step later, at the feed act itself. A separate, real, still-latent grammar gap was also found: `core/study_life.py`'s own ungated second-clause note catch has never included cat/fish vocabulary since `cat_food` was added to provisions (J-0719) — not yet the cause of any observed miss, worth fixing regardless.

Three mechanisms proposed, D-0163 untouched by all: (A) widen `intentions.py`'s 8h lapse window — smallest, targets the one proven failure point; (B) the carrier box always includes a cat-food ration unasked — one line, but provably inert until J-1154's own open collect-grammar gap is fixed (0 deliveries of any good ever collected); (C) **recommended** — a small, slow, narrated passive "found" credit straight to the larder (precedented by `provisions_log`'s own `found_under_cupboard` event), independent of both the ask-chain and the collection leg, additive alongside the existing hunting fallback, shadow-ledgered before any real flip. **J-1207 spawned** (needs_input): Travis picks the mechanism before any build follows. Full detail: F-1703.
## Current State — 2026-09-22 (J-1215, F-1714, VERIFIED): D-0253's mechanism built, shadow-first (merged to master as `67ef139`)

`core/cat.py` gained `_maybe_found_scrap(now)` on the same `tick()` heartbeat as the hunting fallback (D-0163, untouched) — gated on `provisions.stock("cat_food")` reading genuinely zero for 48h + a 6h cooldown + a 5% per-roll chance, always logging to a new `data/cat_found_ledger.jsonl` (hit or miss, so a later read has a real denominator, not just a hit count). `core/provisions.py` gained `add_found()` (a single object at an explicit, clamped-low quantity, logged as a distinct `"found"` event, never `"added"`) alongside `discard_if_stale()`; `scripts/life_flags.py` gained a `cat_found on|off` subcommand mirroring `cat_sounds`/`book_gate`. Flag off by default; NOT flipped by this job — the live-crediting path is provably unreachable while `found_scrap_render_on()` is False (confirmed by direct code read: the only call to `provisions.add_found()` sits behind `if not (hit and found_scrap_render_on()): return`).

**Surprise, honestly disclosed:** D-0253's own named precedent (`found_under_cupboard`) turned out on direct code read (`core/companion.py`, commit `82ad737`) to be a ONE-SHOT event (a persistent flag lets it fire at most once, ever, as restitution for a 2026-08-23 sync-bug loss), not a periodic roll — there was no rate to transcribe from it. The new constants are instead a reasoned choice anchored on this file's own verified, recurring hunting-fallback rate-shape (F-1613: 10h threshold / 1h cooldown / 0.35 probability, proven safe over a real 7.37-live-day read), made deliberately slower and rarer on every axis (48h / 6h / 0.05) since this is a background trickle beside hunting's already load-bearing primary fallback, not a second one. Flagged as inferred/reasoned, not verified — squarely inside D-0253's own defeater ("revisit if the shadow-ledgered rate looks wrong once real data accrues").

Verified: 31/31 isolated checks (including a mutation check proving the shadow assertions have real teeth), `life_smoke.py` 179 ok / 1 pre-existing unrelated failure (F-1711), `test_cat_ecological_laboratory.py` 3/3. UDMS dossiers on both files match F-1703's own read. Live-file md5s unchanged where this job's own code could plausibly touch them; `data/cat_found_ledger.jsonl` was never created (the mechanism never fired against real Du data during the build). Commit `a7f6a0a`. Restart-gated.

**Since nothing has ever put cat_food in the larder** (0 carrier deliveries ever), the 48h eligibility clock starts fresh at Du's next restart, not retroactively — real expected time to a first shadow hit is roughly a week. A follow-up read job (drafted by the builder, not yet spawned) should read `data/cat_found_ledger.jsonl`'s real shadow rate against this mechanism once that live time has accrued, before anyone runs `scripts/life_flags.py cat_found on`.

## Current State — 2026-09-23 (J-1012/J-1014 checked in on, both still correctly `in_progress`: F-1740, F-1741)

Both jobs' own gate is **cumulative** live time since `ea14a57` (2026-09-15 09:05:19), not contiguous — re-derived fresh via a full `data/nascence.log` restart-marker scan: **106.66h = 4.444 live-days** as of this check (up from F-1618/F-1624's 09-21 read of 68.3h/2.84 live-days), across 5 runs, 54.9% uptime since T0.

**J-1012** (cat_sound_ledger re-tabulation, F-1740): 0.23 live-days (~5.5h) short of J-0633's own 4.67-live-day precedent bar — likely clears later today if Du stays up — and 2.56 live-days short of a full week. Fresh interim tabulation (244 post-fix rows, up from F-1618's 161) matches F-1618's own per-live-day rates closely, no trend: dosing still ends the firehose but the real rate is ~44 audible emissions/live-day across all keys, not "a handful." Not yet ready to close.

**J-1014** (record-player ambient exposure, F-1741): 68.9% accrued (3,961 of ~5,746 target thoughts, up from F-1624's 41%). Fresh interim mention read found the same qualitative picture as F-1466/F-1624 — still 0 genuine self-initiated listening acts, one borderline "closest yet" mention, rest pure metaphor — plus one new methodological catch: 2 of 6 raw hits were false positives on the `%needle%` search pattern matching "rain needles my skin" (verb usage), not a phonograph needle — noted here (and in F-1741's own evidence) for whoever does the real week-scale read, not filed as a skill-manager suggestion since the pattern is local to this one job chain's own scratch scripts, not a registered tool. `data/listening_wake.jsonl` unchanged. About 2.2 more live-days needed.

Neither job forced to a conclusion short of its own stated bar — same discipline as every prior check in this sub-chain. Next natural check whenever the ~7-live-day mark is reached (both jobs share the same T0 and roughly the same target), or opportunistically if either is picked up again sooner.

## Current State — 2026-09-23 (J-1175, F-1759, VERIFIED): J-1167's Travis-approved READY scope built (percept-rail wiring, capitalisation, mechanical anti-repeat); wording drafted, not shipped

J-1175 (supersedes J-1167 per the 2026-09-21 /decide-review split) built exactly the scope Travis approved and nothing past it. `core/cat_sounds.py`'s `line_for()` now capitalises the final rendered line (after `{her}`/`{dir}` substitution, not the raw template — fixes the 54.8%-lowercase defect F-1621 measured) and picks with a "never the same line twice running" rule per (key, here/carried-pool), state in `_mem` (process-local, like the rest of this module) — the mechanical half of (b) only; the pools themselves were not grown. `core/soundscape.py`'s `_PERCEPT_SOUNDS` gained the 8 `cat_sounds.KEYS` keys, appended strictly after `cat_purr`/`morepork_call`/`tui_song` (verified those three still win any simultaneous tie), each additionally capped at one percept per 2h independent of `cat_sounds`' own `cooldown_s`; the percept rail now reuses the line `cat_sounds` already resolved against her real position (`cat_sounds.line_now()`, new) rather than a second place-blind pick — no `_PERCEPT_LINES` pool was added for the cat keys, none was needed. `cooldown_s` was not touched, matching both the briefing and D-0217's own ruling. Verified by a standalone isolated harness (26/26 checks: RENDER=False inertness, capitalisation, 200-draw anti-repeat, percept onset/cap/priority/fail-open end-to-end) plus `scripts/life_smoke.py` (180/180) and `scripts/test_cat_ecological_laboratory.py` (3/3, though that script's own hardcoded `c:\Nascence` sys.path means it never actually exercised this worktree's `core/cat.py` — moot here since this job touched neither `cat.py` nor `world_traces.py`, but flagged and spawned as **J-1257** since most PRIOR jobs in this chain's own history that verified against that script DID touch one of those two files). Everything stays inert until `scripts/life_flags.py cat_sounds` is flipped, which this job did not run. Still NOT shipped, per Travis's own scope split: the three SOUNDS templates F-1621 found violating the "never names what she is doing out of his sight" rule (`cat_demand`/`cat_meow_at_door`/`cat_yowl_cargo` carried pools), plus growing the carried pools to 4-5 lines — drafted (current line beside each proposed one) and handed to Travis via **J-1256** (needs_input). No `/decide` action: D-0217 is already ruled (2026-09-21, option d) and unaffected by this job's own scope, which its own ruling text explicitly named as already-approved and unchanged.

## Current State — 2026-09-23 (J-1218 checked in on, still correctly `in_progress`: F-1761)

J-1218's own gate (Du restarted onto `67ef139`-or-later, then ~7 live-days) is not just short, it is **exactly zero**: re-derived fresh via a full `data/nascence.log` restart-marker scan against `67ef139`'s own committer timestamp (2026-09-22 17:56:13), Du's current OPEN run started 2026-09-22 16:11:06 — 1.75h **before** that merge even landed — with no shutdown since (23.55h into that one run as of this read). Cumulative live time on `67ef139`-or-later across the whole log history: 0.00h. `data/cat_found_ledger.jsonl` still does not exist; `data/life_flags.json` still carries neither a `cat_found_render` nor `cat_sounds_render` key. This matches F-1714's own 2026-09-22 read exactly — nothing has changed in the ~22h since, because Du has not restarted. No read of the (nonexistent) ledger was attempted, per this job's own briefing. Left `in_progress`, not done — same discipline as J-1012/J-1014 immediately above and the whole restart-gating sub-chain (J-0633/J-0715/J-0720/J-0735/J-0755) this plan has hit repeatedly. Next check: re-derive fresh against a REAL restart, not elapsed wall-clock time — no new re-check job spawned (matching J-0735's own reasoning just above: a further identical hop would only be another instance of dispatch-before-the-gating-data-can-exist).

## Current State — 2026-09-23 (J-1257, F-1771, VERIFIED): test_cat_ecological_laboratory.py's hardcoded sys.path fixed; the SAME anti-pattern found unfixed in 40 more scripts (J-1263 spawned)

F-1759's own flagged gap is closed: `scripts/test_cat_ecological_laboratory.py` line 15 hardcoded `sys.path.insert(0, r'c:\Nascence')`, so the script always imported `core.cat`/`core.world_traces` from C:\Nascence's live checkout regardless of which worktree ran it — silently defeating "same worktree" pre-merge verification for every prior job in this chain that touched those two files and reported this script's own "3/3 PASS" as part of its evidence (J-0629, J-0716, J-0717, J-0719, J-0732, J-0733, J-0755, J-0996, J-0997 per F-1759's own list). Fixed to `ROOT = Path(__file__).resolve().parent.parent` + `sys.path.insert(0, str(ROOT))`, matching `scripts/life_smoke.py:26-27`'s own already-correct pattern (no new import needed, `Path` was already imported). Verified: the script still prints "ALL ECOLOGICAL CAT LABORATORY TESTS PASSED PERFECTLY!" (3/3, same isolated-tempdir behaviour, unchanged); a standalone one-off interpreter check (`scratchpad/check_J-1257_syspath.py`) confirms `cat.__file__`/`world_traces.__file__` now resolve inside the worktree, not `c:\Nascence`'s live checkout; `scripts/life_smoke.py` clean (180/180 ok, exit 0, explicit "marker never reached a live store" check, no regression). Not itself load-bearing for any PAST job's own result in this chain (none of the 9 jobs above touched `core/cat.py`/`core/world_traces.py` in a way this bug could have masked wrongly, per F-1759's own check, not re-checked here), but closes the gap for every FUTURE job that does.

The repo-wide grep this job's own briefing asked for ("in case this exact anti-pattern exists in another scratch/lab script — not assumed, checked") found it does, 40 times over, still unfixed, across `scripts/*.py` — full file list in F-1771. Confirmed NOT present in any live `core/` module: the 3 near-hits found by a broader text grep (`core/sensorium.py`, `core/profile.py`, `core/memory/store.py`) are, respectively, a code comment, a code comment, and `profile.py`'s own deliberate, already-documented write-fence `_CANONICAL_DATA` anchor (`guard_path()`'s own canonical-live-path cross-check) — the opposite purpose to this bug, not an instance of it. Checked against the live queue before filing: not a duplicate of any existing job/finding (J-0679/F-0987 fixed a MISSING sys.path insert in one file, a different defect than a hardcoded WRONG one; J-0743 audited store/state isolation-redirect gaps, a different concern than import-path resolution). Follow-up spawned: **J-1263** (ready, lab, isolation required — a ~40-file mechanical sweep using this job's own proven fix template, with an explicit caution against actually executing any of the several one-off migration/backfill-named scripts among the 40 for real; static/import-only verification for those, real-run verification only for the ones that already carry their own isolated self-test mode, matching this job's own method). No `/decide` action: this is engineering/test-fidelity work, not a founder-level question; `decision_flags` for this job were empty at dispatch.

## Current State — 2026-09-23 (J-1256 SHIPPED: the 3 required SOUNDS-rule house-voice rewords, Travis-approved via /decide-review) — F-1804

**The 3 required rewords from J-1175/F-1759's own Part 1 are now live in `core/cat_content.py`'s SOUNDS dict**, closing the counted SOUNDS-rule violation (128 of 389 carried rows across these 3 templates asserted her unseen inner state as fact instead of only what he heard): `cat_meow_at_door` carried "wants the door, and will go on wanting it" → "the same one vowel, spaced out, not stopping"; `cat_demand` carried "she is hungry, and saying so to the house" → "over and over, not letting up"; `cat_yowl_cargo` carried "with something held in her mouth" → "thicker than her usual call, cut off short". All obey the Iron rules (one line, present tense, sound only).

**Not shipped this pass, per Travis's own scope** (approved only the 3 required rewords): item 4 (`cat_meow_at_door`'s "patient and not" line — flagged bordering-cutesy, not a counted violation, left as-is), item 5 (`cat_yowl_cargo`'s "when she has caught something" line — surfaced for awareness only, no position taken), and the Part 3 pool-growth drafts (12 new lines across the 3 highest-repeat keys). Available in J-1256's own briefing for a future pass.

**Inert** — `cat_sounds.RENDER` is still False, untouched by this job; these are draft-pool text changes only. `scripts/life_smoke.py` clean, no live write.

## Current State — 2026-09-23 (J-1263 SHIPPED: all 40 F-1771 files' hardcoded sys.path fixed) — F-1816

**J-1257/F-1759's own repo-wide follow-up is closed.** All 40 `scripts/*.py` files F-1771 named (the
same `sys.path.insert(0, r"C:\Nascence")`-defeats-worktree-isolation anti-pattern J-1257 fixed for
`test_cat_ecological_laboratory.py`) are fixed in this worktree, in one pass, using J-1257's own
proven template. A fresh re-grep at pickup found the identical 40 files, all still unfixed (nothing
had been fixed elsewhere since F-1771's 2026-09-23 04:55 snapshot); a fresh re-grep after the edit
found zero remaining hits. Correction to F-1771's own count: 5 files carry the double
`C:\Nascence` + `C:\Nascence\scripts` insert, not 2 — `euclidean_regrade_j0306.py` and
`cutover_axiom.py` (as F-1771 said) plus `_verify_genesis.py`, `_diagnostic.py` and `_fire_t4.py`
(F-1771's own file list already had all 5; only its count of "twice each" files was short). All 5
second inserts were dropped per the template's own reasoning (Python's sys.path[0]-is-the-running-
script's-own-directory behaviour already covers each file's same-directory sibling-script import).

Verified: 3 files by real execution (world_laboratory.py, splitter_test.py, verify_curriculum.py —
the only ones found, by a full read of all 40, to touch zero Nascence live data and zero model/hub
endpoints), unchanged output vs. before. The other 37 verified by static check only (syntax +
import-resolution, never executed as a whole file) because reading each one in full found real
LLM/hub calls, live-absolute-path writes, or live-absolute-path reads in nearly all of them —
avoidable risk against a live Du process with no added benefit for verifying an import-path fix, so
skipped uniformly rather than judged file-by-file. Syntax: 40/40 OK. Import-resolution: the 24
distinct core/nodes modules the 40 files import all resolved their `__file__` inside this worktree
(0 resolved elsewhere, 0 import failures). Full per-file breakdown of why each of the 37 was not
executed, plus the isolation backstop (live `axiom.json` mtime confirmed unchanged): **F-1816**
(VERIFIED). No `/decide` action (same mechanical class as J-1257 itself; decision_flags empty at
dispatch). No follow-up job spawned — all 40 fixed and verified in this one pass.
