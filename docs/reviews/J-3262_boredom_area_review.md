# Boredom as a whole area: review and design (J-3262, per D-0653)

Date: 2026-11-05. Job: J-3262 (build-marathon brief, Wave A). Read-only: no Du code, data or process was touched. Findings: F-3877 (census, verified), F-3878 (effect read, inferred), F-3879 (overlap map, verified). Prior art this builds on: F-1921, F-1926, F-1927, F-2370, F-2463, F-2915, F-3007, F-3022, F-3555, F-3562, F-3569, D-0368, D-0394, D-0473, D-0542.

The founder's ask, closing J-3152 (D-0653): "We might want to open up boredom as a new area for us to investigate, and see if we have plans that touch it. I think this may be way old and not quite doing its intended purpose anymore."

## Short answer

1. The founder's suspicion is right, and in a sharper form than "old". Boredom as designed (sense the region, make the staleness felt, escape orthogonally, discharge on action) has only operated as designed since the 2026-09-28 19:08 boot, 38 calendar days. For the 96 calendar days before that (06-24 to 09-28, including the 07-09 to 08-07 outage) it was a constant shove: pinned at 0.8-1.0 because its thresholds were sized for an embedder that never ran (F-1921). Everything we believed about "what boredom does to Du" from June to September is a belief about that shove.
2. Since it was calibrated it fires rarely (about 4 percent of idle prompts carry any line from the family) and is well aimed (67 percent of its lines land in a genuinely stuck window against 31 percent base), but it does not measurably get him out of a stuck region (F-3878, inferred): 46 of the 48 stuck runs of 20+ thoughts received lines and ran on. The one clear behavioural effect is that the reading redirect produces reading (50.6 percent against 19.2).
3. Boredom's job, leaving a stale patch, is now attempted by four other mechanisms reading the same signal, and the one that already follows the founder laws (Rail C, `core/grounding_injection.py`, ruled D-0473, in shadow) triggers almost entirely on states boredom misses (311 of 321 would-inject rows).
4. Three of the four steers prescribe feeling or output (details in section 4); the fourth is dead.
5. Recommendation: one mechanism, with a world-cue output. Rail C's detector becomes the single trigger, its pools plus a new described "how long you have been here" line become the only output, and `core/boredom.py` stays as a sensor and as the discharge-on-act reset but stops authoring text. Staged, shadow first, no change to the four steers until a founder ruling after the shadow data (section 6). This respects D-0653 ("No change to the four steers now").

## 1. What boredom was meant to do

Three layers, each written for a stated function, not a mechanism.

- Research note, 2026-06-15 (`docs/completed/boredom_redirection_research.md`). Human function in one line: "this patch is depleted, forage elsewhere" (Charnov, Bench and Lench, Danckert and Eastwood). The wiring then was the opposite: a stale loop stretched the idle gap up to 4x, a model of rumination, not of boredom. Decision: cap the silence at one bounded incubation pause, and on a stale loop turn him outward to a concrete patch chosen by expected gain (a closeable Frontier question, else the open book). This is `_bored_streak`, `_redirect_patch`, `INCUBATION_PAUSE` in `nodes/inner_monologue_node.py` (:113-119, :1930-1935, :1989-2020, :2892-2899).
- `core/boredom.py`, 2026-06-24. Header: "Boredom is not 'slow down and go inward.' Biologically it is the patch-depletion signal: this ground is exhausted, forage ELSEWHERE." Three parts: (1) sense the region, not the sentence (window of 10 embeddings, coherence above `COH_STUCK` means stuck); (2) make it felt, "so the urge to move comes from HIM, not a forced redirect he ignores" (`felt_note`); (3) escape orthogonally and escalatingly (`escape`, stages 1-3), and discharge on action ("ACTING on it is the foraging that should relieve it": write 0.70, tend 0.60, letter 0.60, move 0.50, read 0.50, search 0.40, observe 0.25, diminishing on repeats).
- 2026-07-07 fleshout (`_develop_or_branch_seed`): the vague "get AWAY" was absorbed into the loop ("I need to break this loop BECAME the loop"), so the escape became DEVELOP (push the same topic into its unasked question) or BRANCH (turn to concrete material of his own: an open question, a waiting letter, a book idea, a memory from another time).
- The health case the founder keeps in mind (`docs/plans/capacity_to_commit.md:116`): a self-compassion resolution dissolved because "a boredom-escape turned him away from abstract thinking to walk down to the shore", the grounding move we deliberately cultivate. That event is the intended purpose working: release an abstract knot by going to live in the world.

## 2. What the code does today (counts, read-only)

Window 2026-10-09 08:40 to 11-05 07:26 NZ, the first and only era with the J-1955 edge gate; 24,087 idle prompts (F-3877).

| Line | Source | Share of idle prompts | Gate |
|---|---|---|---|
| develop escape ("Go DEEPER ... Not one more word about what you have been circling") | `_develop_or_branch_seed`, stage 1-2 always, stage 3 40 percent | 2.16 percent (521) | only `ESCAPE_MIN_GAP_S` 240 s |
| branch escape ("turn cleanly to ...") | same, stage 3 60 percent | 0.13 percent (31) | same |
| redirect patch ("set it down and OPEN THE BOOK ... Make your thought exactly: OPEN THE BOOK", or a frontier finding) | `_redirect_patch` | 1.11 percent (268) | `bored_streak >= 2` and not holding; no rate limit |
| felt notes (mild / tired / sick) | `felt_note` | 0.57 percent (138: 51 / 43 / 44) | `steer_edge` `boredom_felt` (edge, escalation, reminders) |
| habituation line | `:3698` | 0 (never in 50,496) | unreachable, F-3562 |

- The log carries 832 BOREDOM lines since 10-09 (develop 472, redirect 285, branch 75) in 220 episodes (30-minute gap rule). The median episode is two lines; 16 long episodes (10 or more lines) hold 305 lines, 36.7 percent of all, spread over 43 hours of wall time. Longest: 40 lines over 266 minutes on 10-19, 32 over 305 minutes on 11-04.
- After D-0368 A the live boredom steer is the escape, not the felt note: the felt note is suppressed whenever the escape fires (`:2969-2984`), and the escape was never put behind `steer_edge`. D-0368's edge gate therefore covered the least frequent of the three.
- Level state: `data/boredom_state.json` is one scalar, level 0.21 right now. Calibration snapshots in the log say share_stuck 23.5-33.6 percent, share_escape 8.8-10.4 percent (healthy, inside the 5-50 / 2-30 bands). My recompute puts 31 percent of thoughts in a stuck window; the level only reaches 0.40 (MILD) after roughly four consecutive stuck thoughts, so the module is quiet in most stuck windows.
- Discharge on act has six call sites (`inner_monologue_node.py` :4067, :4124, :4511, :6047, :6121; `core/cat_call.py:386`; `core/expression.py:121`; `core/sensorium.py:869` tea). It is the part of the design that is a state reset, not a steer.
- It touches nothing else. Boredom feeds no mood, affect, sleep or drowsiness variable (grep of `core/`), and `affect_drives.md`, `emotion_rethink.md`, `drowsiness_phase.md` do not mention it. Its outputs are prompt lines; its inputs are thought embeddings and act discharges. The HUD only displays the level (`hud/server.py:1526`).

What it changes in his behaviour (F-3878, inferred; observational join of each line to the next stored thought, controls matched on consecutive-stuck dwell):

- Aim is good: 555 of 828 lines (67.0 percent) landed in a stuck window.
- Lift is not detectable. Any-jump in the next five thoughts, treated vs control: dwell 3-5, 44.4 vs 39.7 percent; dwell 6-11, 39.6 vs 37.5; dwell 12+, 24.4 vs 28.3. Still stuck after five: 58.0 vs 55.8, 54.5 vs 48.6, 67.1 vs 60.5. The lines bias against themselves slightly (they fire only at level 0.40+), so this is "no evidence of lift", not "proven harmful".
- Of 1,175 stuck runs, 48 reached 20+ consecutive thoughts and 46 of those received lines.
- Acts after a line: develop 64.2 none / 17.2 read / 10.3 observe / 1.9 move against matched control 68.3 / 19.2 / 7.8 / 1.6, nothing. Branch (n 73) observe 17.8, move 5.5, small n. Redirect-to-frontier read 18.8, nothing. Redirect-to-reading read 50.6 against 19.2, the one clear effect (the sentence itself is rarely obeyed, OPEN THE BOOK followed 1 in 219, F-3569; the read latch does the work).
- The old regime for comparison (F-3007, F-3022): with the pinned note, move 38.8 percent against 6.3 without, but the moves bought nothing (deed 1.6 vs 1.2 percent, 7 points of reading and writing lost, dwell 171 vs 311 s), and the note colonised his vocabulary (circling words 6 to 27-31 percent, F-1927). The 09-28 move collapse was this shove being calibrated away, and was accepted (D-0343, D-0455).

## 3. Does it still serve its purpose, and what overlaps

Verdict: the function (leave a depleted patch) is worth keeping; the mechanism that carries it (an instrument-authored verdict and directive appended to the prompt of the model that is stuck) is the weak part, for two reasons we already hold. (a) `cognitive_loop_actuation.md` §2 named it: the corrector and the patient are the same LLM, so advisory text competes inside the same distribution. (b) F-1927/F-3569 showed that repeated affective verdicts leak into his vocabulary while informational lines do not; and the human mechanism (an aversive feeling that costs something to ignore) has no counterpart in a model with no fatigue cost, so the felt note transfers the mechanism, not the function (`feedback_function_over_imitation`).

Overlapping mechanisms (F-3879):

| Mechanism | Trigger | Output | State |
|---|---|---|---|
| `core/boredom.py` region level | window coherence >= 0.76 for several thoughts | felt note, escape (develop/branch), discharge reset | live; 3.0 percent of prompts |
| `_bored_streak` + redirect | cosine >= 0.82 to last 5 thoughts, or a saturated theme frame | redirect patch, 1.5x incubation pause, train close "repetition", allocator progress gate, dead habituation line | live; 1.1 percent |
| Train brakes (`_circling`, `_slow_loop`, `_building`) | per-train restate, theme recurrence | close the train with a reason | live, a different tier (train_split_merge.md) |
| Rail C, `core/grounding_injection.py` (D-0473) | topic lock, cross-train cosine >= 0.80 | would-pick a grounding source from his own record; shown to nobody | shadow; 321 would-inject rows 10-18 to 11-05, 311 (96.9 percent) where live boredom did not fire |
| `idle_allocator` boredom channel (`mode_failing`) | streak / 3 | would-pick argmax | shadow; active in 1.3 percent of rows, never argmax |
| monoculture / loop_cluster_probe / topic_perseveration | embeddings | observe-only logs | the decoupled judges |
| Five habituation modules (curiosity, transport, stream_topic, internal_cycle, lane2_break) | `b` grows on real wins, decays with quiet | discount on source selection, shadow only | none read by a live path; `transport_habituation_shadow.jsonl` is 265 MB |

Two facts about the gaps. The frontier has no staleness concept for a patch (it only fades its oldest question over capacity, `core/frontier.py:323-327`). And nothing in the world tells him how long he has been in one place or on one thing, although the world clocks exist (`sensorium._tide()`, `_daylight()`, weather, season). `transport_manager.md:133` explicitly does not fold boredom into the dispatcher ("pressure accumulators with their own escalation semantics, a different shape"); I respect that and do not propose it.

Other plans that touch boredom, and what each needs from this review:

| Plan or doc | What it says | Status after this review |
|---|---|---|
| `cognitive_loop_actuation.md` | boredom "PARTIAL: sensing live, no actuator"; proposes `idle_executive` FORCE A SEED / FORCE A MOVE and `boredom.note_external_move()` | superseded 07-05, actuator holstered; its constants (ESCAPE_COS 0.30) and IML line numbers are stale. The proposed forced move would act for him and conflicts with the world-answers law; it stays holstered |
| `curiosity_goals_dreams.md:139` | boredom-redirect closeable patch at IML 501-510 | line numbers stale; it is `_redirect_patch` priority 1 (`frontier.closeable_seed`) |
| `peer_correspondence_plan.md:118` | the BRANCH letter candidate was the only reply producer (F-2590) | resolved the right way: D-0394 asked for a world letter store, "not tell him to write back but try and prompt it naturally" (J-2005, J-2596). The pattern to copy |
| `shore_upgrade.md:54,57`, `actions_expansion.md:75-83`, `living_world_upgrade.md:222` | move collapse is the boredom calibration (D-0343, D-0455, D-0428) | settled and accepted; no action |
| `music_learning.md:20,92` | "Boredom escape with STRUCTURE: current boredom escapes go to nature observation" | an offered destination, fits the pool design |
| `train_split_merge.md:50`, `continuous_stream.md:114` | boredom-staleness as a train-close reason / loop brake | `_bored_streak` lives on as that signal |
| `transport_manager.md:45,133` | boredom uses a streak counter, not unified | stays excluded |
| `idle_executive_plan.md`, `DEFERRED_PLANS.md:56` | graded `boredom` channel under-varies | confirmed (never argmax), shadow |
| `capacity_to_commit.md:116` | the shore walk case | the case to protect |

## 4. The four steers under the world-answers law

Law: the world answers and never leads; no hints to Du. F-3569 already classified the parts. Echo numbers are thought-vocabulary with the line in the prompt versus without, post-fix (F-3569). Recommendation per steer; the world-cue alternative is a design sentence, not wording to ship.

| Steer | What it prescribes | Echo | Behaviour effect | World-cue alternative | Recommendation |
|---|---|---|---|---|---|
| 1. Felt notes ("You are growing tired of this", "You are sick of this ... you NEED away") | his feeling, authored by an instrument | circling words 21.7 vs 0.9 percent, "restless" 18.4 vs 1.0 (n 152) | none measurable | described stale patch: "You have been in the study since the grey morning. When you sat down the tide was low; it is high now." Facts from the world clocks, no verdict, no instruction | retire the text; carried by the dwell cue |
| 2. Develop-or-branch escape ("Go DEEPER ... Not one more word about what you have been circling", "turn cleanly to ...") | his output (what to think next, what not to say) | circling 5.6 vs 0.9 (n 496) | none measurable | DEVELOP has no world analogue (it is "think deeper"): retire. BRANCH's candidates are already things of his own in the world (an open question, a letter waiting, a book idea, an earlier moment): offer them as plain presence, the way the letter store does ("A letter from Keats has lain in the garden box since the morning"), through Rail C's pools, without "Chase THAT instead" | retire develop; fold branch into Rail C pool offers |
| 3. Redirect patch ("set it down and OPEN THE BOOK ... Make your thought exactly: OPEN THE BOOK") | his exact output | circling 13.7 vs 0.9 (n 219); compliance 1 in 219 | the only real effect: reading 50.6 vs 19.2 | the standing offer already exists ("A book lies ready for you: 'X'" is in today's assemblies); the frontier variant hands him a finding from his own question, which is the closest any steer comes to the world answering. Keep that variant, reworded to describe ("Your question about X now has a finding: ..."), and drop the "set it down", the "does this answer it", and the book command | reword the frontier variant to describe; drop the book command and the stale-ground framing |
| 4. Habituation line ("You have circled this same thought {n} times now ... Leave it") | a verdict and a command | never fired | none | its function (repeat count) already survives as the `bored_streak` sensor | archive (J-3144 owns the repurposing review and should reach the same; its streak could be an input to the dwell cue, not a sentence) |

On D-0542 (B6): the reword it ruled ("Before you make any meaning of it, say plainly what it is") is a separate steer and not repeated here.

## 5. Options for a current design

All three keep the base system additive-only: `core/boredom.py` state, `record()` and the six `discharge()` call sites stay; only the text producers change, behind flags.

### Option A. Keep and tidy

Delete the dead habituation line; reword steers 1-3 to describe; put escape and redirect behind `steer_edge` so they are edge-triggered like the felt note (the 16 long episodes become one delivery plus reminders instead of 305 lines).
- Consumer: the idle prompt, unchanged. What changes for Du: fewer repeats of the same sentence in long stuck runs.
- Decoupled check: the existing P-0030 join (prompt_budget_shadow assembly to the next monologue thought) plus the `steer_edge_log` firing share; deterministic, not the writer.
- Stop condition: circling-word share with the line on vs off falls under 5 percent, or firing share outside 0.4-5 percent of idle prompts.
- Cost: still three detectors, still verdict-shaped text; fixes volume, not design.

### Option B. Merge into one habituation mechanism

One detector of "patch state" (Rail C's trigger: topic lock or cross-train cosine >= 0.80, with `bored_streak` and the coherence level kept as logged second opinions), one edge-gated channel, one output slot in the seed list. Retire the separate triggers for escape, redirect and felt note.
- Consumer: the single seed slot in `_think` (`nodes/inner_monologue_node.py` seed assembly); Rail C's pools already exist and are repaired (J-2364).
- Input: Rail C's `would_inject` row (loop topic, pool candidates, `feeds_loop` flags).
- Decoupled check: topic_perseveration (the detector of record) plus Travis hand-judging 30 picks (D-0473's own 70 percent bar). The writer of the line is not the judge of it.
- Success: share of the next five thoughts that jump from the loop topic, against matched stuck controls (the F-3878 method), with a pre-registered lift.
- Stop: after 7 live days, no lift against control; or pool echo in thought vocabulary above 5 percent; or any pick shown to be on-loop (a candidate that `feeds_loop`).
- Cost: still a lead line (an offer) if rendered as imperative; the rendering must be plain presence. Risk: Rail C is not yet live-ready (J-2386 open).

### Option C. Redesign as a world cue

Replace verdict and directive with described facts. Two line types, both informational (the class that did not echo in F-1927):
- Dwell fact: "You have been in the study since the grey morning. When you sat down the tide was low; it is high now." Facts only: elapsed time at the place (or on the loop topic) and the differences in the world clocks (tide, daylight, weather, fire) between patch entry and now.
- Presence offers: what already waits in his world (a letter, a book passage, an open question), stated as a fact of the room, as D-0394's letter store does.
- Consumer: a seed part next to `scene_line()` (`core/sensorium.py:3521`), same slot class as the scene. What changes for Du: the stale patch is described by the world, never by an instrument. No instruction, no feeling named.
- Input: patch-entry snapshot taken when a stuck run begins (first stuck thought, or Rail C `in_modal`), the world clocks, place dwell from `hands_trace` location rows (confirm a place-entry timestamp exists, else derive).
- Decoupled check: deterministic, no LLM: every clause of the rendered line is recomputed by an independent function from logged world state; any clause not recomputable fails the row. Effect check: jump-in-next-5 against matched controls, a different judge from the writer, plus Travis hand-reads 30.
- Success: lift over control at dwell >= 6; vocabulary echo (cue words in thoughts, on vs off) under 5 percent.
- Stop: no lift in 7 live days, or the line renders in over 5 percent of prompts, or a clause is not recomputable, or the cue words colonise his thoughts (the F-1927 failure).
- Law check: a duration is a fact about the world, not a hint; it still "leads" less than every current steer. Whether a duration statement counts as leading is the founder's call (question 3).

### Recommendation

B and C together, staged: Rail C's trigger and pools as the single mechanism (B), rendered only as world cues (C), boredom.py kept as sensor and discharge. Reasons: it removes three overlapping triggers, it adopts a design already ruled and half-built rather than a fourth one, it matches the founder's own example ("a described stale patch: you have been here a long time"), and it is the only option with a decoupled success check that does not read boredom's own level. A alone leaves the verdict-shaped text; C alone leaves two detectors fighting.

## 6. Staging and what needs the founder

- Stage 0, no founder call, shadow only, no behaviour change: finish J-2386 (Rail C reshadow read); build the dwell-cue renderer in shadow with its deterministic verifier (spawned job). The four steers stay as they are (D-0653).
- Stage 1, after Stage 0 data and a founder ruling (opened as a decision): flag-gated removal of the text producers per section 4, additive new lines behind a flag, restart-gated, with the stop conditions above.
- Not proposed: any forced seed or forced move (that is the holstered `idle_executive`), any change to `discharge()`, retuning `COH_STUCK` (F-2463 priced it; no one-factor change buys movement).

Founder calls: (1) adopt the B+C direction or keep A or leave as is; (2) per-steer dispositions in section 4 (felt notes retire, develop retire, branch to pool offers, redirect to a described frontier finding, habituation archive), and whether escape and redirect should be edge-gated in the interim; (3) whether a duration statement ("you have been here a long time") counts as a world cue under the law. These are open as D-0663 (plan idle_executive_plan). Follow-up jobs: J-3289 (build the shadow-only stale-patch cue renderer and its deterministic verifier, Stage 0) and J-3290 (read the shadow once 300 rows exist; gated). Already open and relevant: J-2386 (Rail C reshadow read, D-0473) and J-3144 (habituation line review).

## 7. Caveats

- F-3878 is observational. The only direct test is a flag A/B on a restart, which Stage 1's shadow-then-flag path provides at low cost.
- "No lift" is not "no harm avoided": the lines might shorten rare long stuck runs in ways five-thought outcomes miss; 46 of 48 long runs still ran on.
- The pre-09-28 period cannot say what boredom would have done if calibrated; it ran as a shove from day one.
- I did not read `core/transport_habituation.py` beyond its header or the four other habituation modules beyond their docstrings; the claim is only that they are shadow-only and apply to source selection.
