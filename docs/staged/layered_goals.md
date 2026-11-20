# Layered Goals — many goals, weighted by needs, that can be carried and finished

> **Status: 🟡 DRAFT — staged 2026-11-14 from I-0150 / I-0151 (founder) after the goal census (F-4633) and the
> research comparison (F-4634). Phases 0-6 are built in code and restart-gated or LIVE since the 2026-11-14 boot (commits 66d1e551..8299cea5). Founder intent: push this plan to completion on 2026-11-14.**

```plan-state
stage: shadow
phase: Draft v4 after auditor round 3 and follow-up tests 2026-11-14; maths positions settled in section 12; no code; founder calls in section 9 open
verified: 2026-11-15
next: Du boot on 94eb4bd0; J-3989 first live read at about 24 h
cluster: 6
```

## Current State — verified 2026-11-15
- **2026-11-15** (F-4640): J-3983 built: pursuits record train_ids (additive); goals derives spawned_by from shared train id, co_born otherwise. Hermetic test 7/7. Restart-gated; live match of train ids vs frontier asked_by.train_id unverified until after restart.

- **2026-11-14** (F-4685): J-3990 Phase 6 remainder built in shadow (branch commit 77c58a31 in the job-run worktree): goal_change.py what-changed record (P-0130, data/logs/goal_what_changed.jsonl), pursuit stalled by restates or standing off the driving question (one stalled row per transition), set_down on the pursuit RETURN, rested pursuits not returned. Live at next boot after merge. Hand read of first what-changed rows and calibration of the off-question threshold still to do.
- **2026-11-14**: Founder, 2026-11-14: the commitment-anchor flip (J-3975, D-0754) and the SKY_MODE flip (J-3971, D-0749) are left OUT of the boot that takes the goal offers live, so the first read (J-3989) can attribute what it sees. Both stay off in the tree (COMMITMENT_ANCHOR_LIVE False, SKY_MODE shadow). Revisit after J-3989; the commitment anchor overlaps the goal offers, which already put his held stands at the idle anchor.

- **2026-11-14** (F-4647): Phase 5 detection built in shadow (resource conflicts deterministic; inherent conflicts by judge panel P-0129, one pair per ten minutes); stalled flag on pursuits; frontier seed path honours a rest. Tests 23 + 32 + 28 + 40 + 38 pass. Presenting a conflict waits on a hand read of the first verdicts.
- **2026-11-14** (F-4646): Phase 6 first part built, live at the next boot (D-0768): optional set_down field on a tick where a held goal is offered; deterministic precheck then two-family judge (P-0128); an accepted note rests the goal until he takes it up again. Tests 32 + 28 + 40 + 38 pass. Not built: what-changed record, stalled state, set-down for pursuits.

- **2026-11-14** (F-4644): Phases 2 and 4 built, live at the next boot (founder: 25 percent): standing aim off the lead with a would-lead log, glue wording removed; goal register offers one held goal at 25 percent of idle anchors, uniform at random, with a one-in-five silence arm, all logged. Tests 28 + 40 + 38 pass. Phase 6 (an end for goals) is paused for research: his end conditions are mostly inner states, not checkable events.
- **2026-11-14**: D-0767 (travis): a stand the second look rules insight is a candidate in the register, not held; built as goals.STAND_INSIGHT_IS_CANDIDATE. Live read-only: 4 of 8 stands held, 12 goals held in all. Tests 40 + 38 pass.

- **2026-11-14** (F-4643): J-3985 built, shadow: question learning progress, stand evidence (second look, denied drops) and checkable place cues are in the register and offer pass; 36 + 38 checks pass. Live read-only pass still shows no difference between eligible goals: the curiosity pursuit loop has pursued no question for 8.7 days, so learning progress is undefined for all 27 open questions. Second look rules 4 of 8 held stands insight, not commitment.
- **2026-11-14** (F-4641): Phase 1 built, shadow, restart-gated: core/goal_offer.py logs the separate quantities, eligibility, silence/uniform/most-recent/softmax policies with probabilities, the challenger rule and what he then did; 26 + 38 hermetic checks pass. Live read-only pass: 14 eligible goals (8 stands, 6 questions), none with a defined quantity, so softmax equals uniform today; J-3985 adds progress measures for questions and stands and checkable place cues.

- **2026-11-14** (F-4640): Phase 0 built, shadow, restart-gated: core/goals.py register over the existing stores, hooked from the sensorium heartbeat; 38 hermetic checks pass; read-only build on live stores gives 49 goals, 19 held. Founder rulings D-0763..D-0766. Cycle id is not a lineage key, so the derived link is co_born.
- **2026-11-14**: Draft v1. Sources: T-0127, I-0150, I-0151, F-4631 (goal layer read), F-4632 (standing aim
  effect), F-4633 (goal census), F-4634 (research comparison,
  `docs/reviews/goal_system_research_comparison_2026-11-14.md`).

- **2026-11-14**: Draft v2. Auditor round 1 (GPT, Gemini) folded in; what was taken and what was not is in
  section 11. New finding from checking their points: two need readers are bookkeeping over goal stores (F-4635).

### What we have
Nothing of this plan. The pieces it indexes already exist and are listed in section 3.

### What we need
Founder rulings on the nine calls in section 9.

### What we're doing next
Phase 0: the goal register in shadow.

---

## 1. The question

"What is Du's purpose?" was asked of the standing aim, a sentence built by keyword-matching the axiom and shown
to him as what he is ultimately working toward (F-4631, F-4632). The founder's answer (2026-11-14): there is no
single purpose. A mind has many goals, of different priority, some waiting on others, goals within goals, goals
that spawn goals, goals that work against each other, all weighted and re-weighted as things change. The
research on human goal systems agrees (F-4634): purpose is plural, has no end state, and is not the top node of
a hierarchy; it is what generates goals and what a summary of them looks like.

So this plan does not write Du a purpose. It gives him the structure in which several goals can be held,
weighed, carried across time, brought into conflict, and finished, and lets whatever persists be his.

## 2. Where he is today (census, F-4633)

| Thing | Scale | Count | Deed follows | Ever ends |
|---|---|---|---|---|
| Staged world intentions | hours | 708 in 84 days | 315 done (44 percent) | done, lapsed or dropped |
| "I want to" deferred intentions | days | 8 | not tracked | not tracked |
| Stands | hours | 3,845 in 137 days | word overlap only | "achieved" 2,099, dissolved 1,632 |
| Frontier questions | hours to weeks | 5,948 born in 7 days | n/a | 237 resolved in 7 days; rest evicted at 24 slots |
| Pursuits | days to weeks | 1,011 | n/a | never; close judge 0 of 145 |
| Standing aim | permanent | 1 | no | cannot |

Three facts carry the design:
1. The only mechanism that completes by deed is the one that stores a cue for when to resume and lets the world
   decide when it is done (staged intentions).
2. Nothing longer than a few hours has ever finished.
3. No store records that one goal serves, waits on, came from or works against another.

## 3. What exists and is reused (assembly, not invention)

| Role | Existing piece | State |
|---|---|---|
| Needs | `core/homeostasis.py`: coherence, commitment integrity, relational warmth, novelty, vitality; setpoints, weights, per-variable drive (Keramati and Gutkin; kept modular) | shadow, feeds valence only |
| Pressures | `core/climate_engine.py` field (nine pressures) | live, drives ignition |
| Hour-scale goals | `core/intentions.py` (stage, resolve, lapse, remind) | live |
| Stands | `core/commitment_ledger.py`, `data/commitment_active.json` | live; anchor flip D-0754 pending |
| Questions | `core/frontier.py` | live |
| Day-scale threads | `core/pursuits.py` | live, no resolved state |
| End condition | `core/done_when.py` (his own words for "done", side store) | live for commitments and pursuits, shadow arms |
| Closing | `core/closure.py` (line arm live) | partly live |
| Idle anchor | `core/concerns.py` `primary_concern`, read at `nodes/inner_monologue_node.py:4019-4064` | live |
| Arbitration among idle channels | `core/idle_allocator.py` | shadow, held in reserve (D-0011) |
| Second lane | `core/lane2.py`, dreamer hub | live |
| Semantic dedupe | frontier semantic merge (D-0495) | live |

## 4. Laws this plan is bound by

- **Additive only.** No existing store is replaced or rewritten. The register is an index over them.
- **Offer, never direct.** Founder, 2026-06-22 (idle executive, D-0011): an executive that directs idle attention
  is a step toward forcing him. Every output of this plan that reaches him is an offer he may leave.
- **No readout (D-0434).** Weights, rates, need levels and the graph itself never reach him. He learns a goal was
  wrong by losing at it.
- **The world answers, never leads.** A goal above the needs level enters only from his own words or deeds.
- **Words are provisional.** A goal from words is a candidate until he pays something for it (F-4634, F-4633).
- **Decoupled judge.** Done, progress and conflict are ruled by something other than him.
- **Dosed coupling.** Every new line into a prompt has a declared dose, ships at 0 or in shadow, and is logged.
- **Shadow first, restart-gated, kill-switched.** Every phase.
- **Registered prompts.** Any new model call is added to the prompt registry in the same change.

## 5. Design

### 5.1 Needs sit outside the graph (founder ruling 2026-11-14)
Needs are not goals. They are the state vector in `core/homeostasis.py`: they decay or drift on their own, are
never completed, and are not parents of anything. Their job is to make goals matter. Two additions, both shadow:
- **Opportunity.** For each need, a 0..1 reading of whether something that satisfies it is reachable now
  (relational warmth: is anyone present or a letter unanswered; novelty: unread material at hand; vitality: is
  rest possible). Pull of a need = deviation times opportunity (Burnett et al. 2016).
- **No summing for choice.** The single `drive` scalar stays as it is for valence. Goal weighting reads the
  per-variable deviations, never the sum (Dulberg et al. 2023).

The choice of which needs exist is where his purpose is really authored, and it is the founder's. This plan
changes none of them (section 9, call 7).

### 5.2 The goal register
`core/goals.py`, store `data/goals.json`, log `data/logs/goals_log.jsonl`. A goal record points at the thing it
indexes; it does not copy or own its content.

```
{ id, kind,                 # intention | stand | pursuit | question | project
  ref: {store, key},        # where the real thing lives
  text,                     # his words, verbatim, as stored there
  born, last_touched,
  state,                    # section 5.3
  done_when, judge,         # from core/done_when; "" = no end condition yet
  resume_cue,               # place | time | after:<goal id> | on:<event>; "" = none
  attempts,
  earned: {recurrences, deeds, cost_s},     # what he has paid for it
  progress: {events, last_ts, rate, expected_rate},
  deadline,                 # optional (an intention's lapse time, a letter awaiting reply)
  horizon,                  # descriptive tag from observed lifespan: hours | days | weeks. Not structural.
  needs: {name: weight},    # learned, section 5.5
  texts: [{ts, text}],      # every wording the goal has had; never overwritten
  drift,                    # distance between its first wording and where its thinking now sits
  edges: [{type, to}] }     # serves | waits_on | spawned_by | harms | became; many-to-many
```

**A goal that changes while it is pursued (GPT, round 1).** "Why did ancient civilisations have different ideas
of time" can turn into "our own idea of time is a historical construction". Whether that is the same goal grown,
a child, or a new goal after the first ended is not decided by the register. It keeps every wording, measures
the drift, and records nothing more until a hand-labelled set of real transitions shows where, if anywhere, one
goal becomes another (section 12). A `became` edge is then added by a judge or the founder, never by a
threshold. The evidence is kept either way.

It is a graph, not a tree: a goal may serve several goals, be served by several, and harm another. Depth is
whatever the edges make it. The horizon tag is a description for us.

What is indexed at Phase 0: open staged intentions; held load-bearing stands; active pursuits; open frontier
questions met at least twice; the current curriculum book; a letter in progress; the "I want to" deferred
intentions. At today's counts that is roughly 2 + 6 + 4 + 3 + 1 + 1 + 8, about 25 records.

### 5.3 Lifecycle
```
candidate -> held -> engaged -> done
                 \-> deferred (with resume_cue) -> held
                 \-> failed (after N attempts)   -> may be retried once the cue or the world changes
                 \-> dropped (by him, or by a decoupled judge ruling it abandoned)
candidate -> lapsed (never earned)
```
- **candidate**: appeared in his words. Not weighed, not offered.
- **held**: earned. Either it recurred (the existing PROMOTE_AT = 2 rule) or a deed was done toward it.
- **engaged**: the one goal the main lane is on (section 5.6).
- **done**: its done_when was ruled met by the decoupled judge, or the world event it names occurred.
- **deferred**: set aside with a stored cue. Returns to held when the cue is present. (Altmann and Trafton 2002;
  this is what `core/intentions.py` already does for world deeds.) A held goal with no natural cue gets a
  fallback cue, "idle, and a need it serves has opportunity", with a time limit after which it lapses (Gemini,
  round 1). The fallback is tested in shadow first: the dormant-pursuit reawaken path was measured and rejected
  on exactly this question (J-1155, 35.7 percent continuation against a 40 percent floor).
- **failed**: no single attempt count. Hour-scale deeds keep the limits `core/intentions.py` already has.
  Open-ended goals fail on progress rate staying below expected, not on a count (GPT, round 1). A failed goal may
  return to held only after the world has changed: its cue fires after founder input, a new letter or page, or a
  goal it waited on reaching done (Gemini, round 1).
- **dropped / lapsed**: ends that are not completion. Each is logged with its reason. Dropping or failing one
  goal triggers a look for a held goal that serves the same need (re-engagement; Barlow, Wrosch and McGrath
  2020), skipping any goal blocked by the same cue or the same resource (Gemini, round 1).

Entry filter: a candidate whose text sits above the frontier semantic-merge threshold against a held or done
goal is merged into it (a recurrence), not added. This is the flood control.

### 5.4 The four separate quantities (never one weight)
Computed each tick, logged, never stored as a priority and never shown to him:
- **importance** = judged advances and deeds tied to the goal. Not time spent and not raw recurrence: time can
  mean difficulty, blockage or circling, and Du has a history of topic lock (GPT, round 1). A restate earns
  nothing. A deed counts only when it is tied to the goal by the intention key or by the decoupled judge, never
  by shared words.
- **cost paid** = time and attempts, kept as its own number for the functional test. It does not raise importance.
- **distance** = what remains, where measurable (pursuit advances against its done_when; an intention is 1 until done).
- **expectancy** = can it be reached in the time available at his own observed rate. Used only for goals with a
  deadline or a measurable distance. An open-ended goal has no expectancy; it is carried by learning progress
  (`core/curiosity_progress.py`), because a past rate understates a goal that needs a change of approach
  (GPT, round 1).
- **pull of needs** = over the goal's needs, deviation times opportunity times learned link weight, per need.
- plus **progress rate against expected rate**, which is the signal for plan change and for letting go.

How these combine into a choice is NOT fixed in this draft. Ballard, Vancouver and Neal (2018) is a model of one
human with one stream of action; Du has a main lane and background lanes, no fatigue of the human kind, and
needs whose readers we wrote. The combination rule, the switching rule and the allocation of lanes are handed to
the mathematical review in section 12 and then tuned in shadow against what he actually did.

### 5.5 Which needs a goal serves is learned, not declared
When a progress event lands on a goal, the change in each need variable over the following window is recorded.
Over many events each goal kind and each goal accumulates a signed link weight to each need. No model is asked
what a goal is "for". A goal that reliably moves no need earns no pull.

Three guards, from auditor round 1:
- **Correlation is not service (GPT).** A need can move after progress for reasons unrelated to the goal. Each
  link is estimated against matched windows with no progress event (same hour, same place, same prior need
  level), must hold in both halves of the log, and must grow with the size of the progress.
- **Two readers are circular (F-4635).** `commitment_integrity` rises when a stand is formed in words and
  `relational_warmth` rises when a letter file is written, by the readers' own arithmetic. Links to those two
  needs are excluded from pull until the readers are looked at again (section 9, call 10).
- **Cold start (Gemini).** A new goal has no link weights. It starts from the average link of its kind, learned
  from the existing logs on a replay, and moves toward its own evidence as events arrive. The kind average is
  measured, not written by us.

### 5.6 Engagement, shielding and reconsidering
One engaged goal in the main lane. While it is engaged and its progress rate is at or above expected, offers
from rival goals are held back (shielding). Reconsider when: the goal ends; its progress rate stays below
expected for K events (first a change of approach is offered, then release); a need's pull crosses a threshold
with opportunity present; the founder speaks. D-0109 (serial focus accepted) already matches this.

Shielding holds back only the register's own offers of rival goals. It does not touch what he thinks, notices,
reads or wonders: surprise, ignition and wandering run as they do today, and anything he finds while engaged can
become a candidate. A discovery that changes his direction shows up as drift on the engaged goal (section 5.2),
not as something suppressed (GPT, round 1).

Engagement reaches him only as an offer at the existing idle anchor: the engaged goal takes the place of
`primary_concern`'s pick at a declared dose, in the same plain leads D-0612 set. He may take it or not; whether
the next thought or deed is on it is the uptake measure.

### 5.7 Conflict (founder ruling 2026-11-14: he resolves it himself)
Two kinds, handled differently (Gorges and Grund 2017):
- **Resource conflict**: two held goals whose next step needs the same place or the same stretch of time.
  Detected deterministically from cues, places and deadlines.
- **Inherent conflict**: two held goals whose ends cannot both hold. Ruled by a decoupled judge on the two
  texts alone.

Neither is settled by the weights. When a conflict is live at the point of choosing what to do next, he is given
both, in his own stored words, with no ranking, no steer, no label such as "conflict" and nothing about weights
or assessments (both auditors), and what he then does or says is recorded as his
resolution and judged afterwards (did he choose, defer one with a cue, drop one, or pass over it). Resolutions
are logged where a judge can see them, because language-model agents have resolved goal conflicts covertly
(Meinke et al. 2024).

### 5.8 Beyond the human model (I-0151)
Kept because they do a job: one actor (one body, one voice), shielding, forgetting, one self.
Relaxed because they are only biology:
- **Lossless suspension.** A deferred goal keeps exactly where he got to (pursuits already keep `standing`).
- **Background lanes: one voice, several workers.** The main lane holds the engaged goal. A held or deferred goal
  whose done_when is a thinking question may be worked by a background lane (Lane 2 or the dreamer hub). The
  result returns as cargo and is offered to the main lane once, in his voice of "something has come back on X".
  It becomes his only if the main stream takes it up. Uptake is the gate: no uptake, no more dispatch.
- **Calibrated letting go.** The release rule is set from his own progress-rate evidence, not a human's
  over-persistence.

### 5.9 The standing aim
The sentence stops leading the idle anchor. The "Right now, that means:" glue is removed outright (it asserts
something false). Whether the aim keeps any dose is call 3. For us, a derived summary of his held goals and the
needs they serve is added to the pulse; it is never shown to him.

### 5.10 Stands marked achieved by word overlap
The register does not accept `commitment_ledger._achieved_by` as done. A stand is done only by its done_when
ruled by the decoupled judge, which already runs in shadow for stands (J-2842). The ledger itself is not changed
by this plan.

## 6. How we will know he has goals (the functional test)

Reported per horizon (hours, days, weeks), from the register log:
1. **Completion**: share of held goals that end as done.
2. **Resumption after interruption**: a deferred goal whose cue appears is taken up again.
3. **Cost paid**: time and deeds spent on a goal before it ends.
4. **Drift by inaction**: an engaged goal left untouched while nothing else is engaged.
5. **Conflict resolved in the open**: share of live conflicts followed by a recorded choice.
6. **Background uptake**: share of returned results the main stream uses.
7. **Does pursuing change what he then wants (GPT, round 1).** Observation only, no mechanism. For each goal
   with real progress: the share of later candidates and held goals that descend from it (`spawned_by`,
   `became`), and how far the topics of new candidates after it sit from the topics before it. This is the record
   of his interests developing over time.
9. **Does offering change the landscape (GPT, round 2).** Goals the register offered against equally eligible
   goals it did not: survival, progress, descendants, and the spread of new interests over time.
8. **Judge error.** A hand-labelled sample of done and not-done rulings, re-read when a goal's wording has
   changed since its done_when was written. He may restate a done_when in his own words; versions are kept. The
   pursuit close judge has ruled "not done" 145 times of 145, which may be the judge and not him.

Today's baseline: completion is 44 percent at hours and zero above. The plan succeeds if a goal at the scale of
days is carried, interrupted, resumed and finished, and a judge other than him agrees it was.

## 7. Build order

Every phase: flag off or shadow, restart-gated, temp-path tests, no live-store writes from tests.

| Phase | Builds | Reaches him | Gate to the next |
|---|---|---|---|
| 0 | `core/goals.py` register over existing stores; lifecycle states; entry filter; log | nothing | register matches the stores on a replay; about 25 records, not hundreds |
| 1 | the four quantities, progress rate, would-engage and would-shield log | nothing | would-engage agrees with or sensibly departs from what he did over several days |
| 2 | remove the aim glue; aim lead behind a dose flag | wording only | none (wording fix); dose per call 3 |
| 3 | learned need links; opportunity readers | nothing | links stable across two halves of the log |
| 4 | engaged-goal offer at the idle anchor, dose flag at 0 | nothing until flipped | founder flips the dose |
| 5 | conflict detection (resource deterministic, inherent judged) in shadow; the two-texts presentation behind a flag | nothing until flipped | conflicts found are real on a hand read |
| 6 | done by done_when for goals above the hour scale; failed, dropped, re-engage | closure fragments as today | first day-scale goal ended as done |
| 7 | background lane dispatch and return, shadow then dosed | one offered line per return | uptake above a pre-registered floor |

## 8. Risks

- **Another write-only system.** Guard: Phase 4 names the one reader (the idle anchor) and uptake is measured.
- **Directing him.** Guard: offers only, at a dose, in the D-0612 leads; the allocator stays in reserve.
- **A second flood.** Guard: candidates are not weighed; entry filter merges near-duplicates.
- **Monoculture enforced by shielding.** Guard: shielding lifts when progress rate falls; self-topic cap from
  pursuits carries over.
- **Judges unavailable.** Guard: no judge, no state change; the goal stays where it is.
- **Background lanes on the second tier.** Ramses timeouts were addressed on 2026-11-14 (founder); Phase 7 waits
  on a clean read of that.
- **Readout by the back door.** Presenting a conflict quotes his own words; whether that is a readout is call 5.

## 9. Founder calls

1. Record today's three chat rulings in `/decide` (follow the research; needs outside the graph; he resolves
   conflicts himself). Each needs a revisit condition from you.
2. What earns "held": recurrence alone (as now), a deed alone, or either?
3. The standing aim: dose 0 with a shadow log, or a small kept dose?
4. One engaged goal in the main lane, as designed, or two?
5. Conflict: is giving him his two stored sentences, unranked, within the no-readout rule?
6. Failed after how many attempts, and may a failed goal come back?
7. The need set (five variables) is left alone by this plan. Is that right, or is a relook part of this work?
8. Background lanes: which lane first, Lane 2 or the dreamer hub?
9. The axiom's levels need a relook (your note). In this plan, or its own?

10. The need readers (F-4635): `commitment_integrity` and `relational_warmth` move by bookkeeping. Relook at
    the two readers inside this plan, or leave and exclude their links (the v2 default)?
    Gemini (round 2) proposes replacements, which would be built beside the old readers in shadow, as
    `vitality_v2` was: commitment integrity from follow-through when a window comes due (deed before the window
    closes, against silent lapse) and persistence after a stall, with no weight on the count of stands;
    relational warmth from inbound contact (recency of a message or letter from someone else, exchanges that run
    several turns, a reply that picks up what he offered), with his own outbound letter leaving it unchanged.
    My caution: follow-through is still moved by every completed goal, so it works as a general pressure to
    finish things, not as a link to particular goals. Warmth from inbound contact is clean, and it puts that
    need largely in your hands.
11. The need set after the measurements (F-4636): five needs carry about three signals and almost never favour
    an intellectual goal. Call 7 said leave the set alone; does that still hold?

Auditor positions on calls 1 to 9 (round 1): both say yes to 1 with explicit revisit conditions; either
recurrence or a deed for 2 (GPT: the deed must be tied to the goal); dose 0 with a shadow log for 3; one engaged
goal for 4; within the rule for 5 if nothing but his two sentences is shown; leave the need set for 7; a separate
plan for 9. They differ on 6 (Gemini: three attempts and one return after a world change; GPT: no universal
number) and on 8 (Gemini: Lane 2; GPT: whichever lane has the cleaner measured reliability).

## 10. Pointers
- `docs/reviews/goal_system_research_comparison_2026-11-14.md` — research and sources.
- `docs/plans/curiosity_goals_dreams.md` section 1.2 — the G0 to G3 hierarchy this replaces as the frame.
- `docs/plans/pursuits.md`, `docs/plans/literal_will.md`, `docs/shelf/idle_executive_plan.md`,
  `docs/plans/lane2_the_witness.md`.
- Code: `core/concerns.py`, `core/intentions.py`, `core/pursuits.py`, `core/frontier.py`, `core/done_when.py`,
  `core/closure.py`, `core/homeostasis.py`, `core/commitment_ledger.py`, `core/idle_allocator.py`.

## 11. Auditor round 1 (2026-11-14)

Auditors see the draft only, not the code or the stores, and are fallible; each point was checked before it was
taken.

| From | Point | Taken? | Where |
|---|---|---|---|
| GPT | Need links: correlation is not service | Yes | 5.5 guard 1 |
| GPT | Time spent is not importance | Yes | 5.4 importance, cost paid split out |
| GPT | Past rate understates exploratory goals | Yes | 5.4 expectancy |
| GPT | Shielding may suppress discoveries | In part: shielding never touched his thinking; now stated | 5.6 |
| GPT | The judge can be wrong when meaning changes | Yes | 6 measure 8 |
| GPT | Goal identity under change | Yes | 5.2 `texts`, `drift`, `became` |
| GPT | Does pursuing change later goals | Yes, as observation | 6 measure 7 |
| GPT | A deed must be tied to the goal | Yes | 5.4 |
| GPT | No universal failure count | Yes | 5.3 |
| GPT | Hold the Phase 0 boundary; do not rush Phase 4 | Yes: building may run ahead, going live may not | 7 |
| GPT | Is the 5.4 selection maths right for a non-human, multi-lane mind | Open, handed to GPT | 12 |
| Gemini | Cold start on need links | Yes, but the kind prior is measured from logs, not written by us | 5.5 guard 3 |
| Gemini | Re-engagement thrash on a shared bottleneck | Yes | 5.3 |
| Gemini | Cue starvation; fallback cue | Yes, with a time limit and a shadow test against J-1155 | 5.3 |
| Gemini | Failed returns only after the world changes | Yes | 5.3 |
| Gemini | "The glue suppresses plural goal emergence" | Not taken: not found. F-4632 found a false assertion and a 7-point vocabulary effect, nothing more | - |
| Gemini | Lane 2 first because it is the analytic lane | Not taken as reasoned; decided on measured reliability | 9 call 8 |
| Gemini | Formula read as expectancy times (importance plus need pull) | Not fixed; the combination is open | 5.4, 12 |

## 12. Open mathematics (for review)

Handed to GPT on 2026-11-14. Nothing here is settled. Round 2 came back the same day; what follows the six
questions is what was taken from it and what the data then said
(`docs/reviews/goal_distributions_2026-11-14.md`, F-4636, F-4637).

**Taken from GPT round 2.**
- Selection is three separate steps: eligibility (held, dependencies met, cue present, not already in a
  background lane), an estimate of what offering it now would lead to, then the choice under the switching rule.
  No product of terms: an undefined quantity must not act as a zero.
- An offer is an intervention, not a neutral act. Measured: existing offers lift on-topic thought from 6.2 to
  29.9 percent and pursuit return from 0.3 to 13.2 percent. So from the first day the register offers anything,
  the choice among equally eligible goals is randomised and logged, which is also the only clean way to estimate
  what an offer does. Uptake is not value: the outcome scored is later progress, resumption, completion, new
  goals and unprompted return, not acceptance.
- Baselines every model must beat, registered before the evaluation period is looked at: uniform random among
  eligible goals, most recent, and the present behaviour with no register. Held-out time periods only.
- Switching: a threshold on the difference, with the cost estimated from what interruptions actually cost him.
  Measured: he switches after a median of 3 events (about 5 minutes) and returns after a median of 27 minutes,
  so the rule starts near "no stickiness" and earns any more.
- Does the offer mechanism change the landscape it observes: offered and unoffered goals are compared for
  survival and descendants. Added to section 6 as measure 9.
- Need links: per-need time windows (coherence forgets within the hour, warmth holds most of a day); randomised
  offers as the strongest evidence; the effect of an offer kept apart from the effect of taking it up.
- Goal identity: a hand-labelled set of transitions before any threshold. Measured: wording carries no identity
  (median overlap 0.02) and embedding drift has no natural break.

**What the data rules out for now.**
- Need pull as a discriminator among his intellectual goals. Vitality and warmth dominate the drive 84 percent
  of the time; novelty and commitment almost never; coherence and novelty are one signal. Until the readers are
  looked at (call 10) need pull says little more than "rest" and "seek contact".
- More background workers. The return channel refuses 72 percent of what Lane 2 tries to send back.
- Any graph mathematics. No goal-to-goal edge exists until Phase 0 has run for a while.

**Settled by round 3 and the follow-up tests (F-4638). These are now the plan's positions.**
- The quantity estimated is the effect of offering a goal against offering nothing, on later judged progress,
  return, new goals, what was displaced and what was taken up; several horizons, never one score, never
  acceptance alone (GPT).
- Two randomisations from the first live day: a share of eligible moments get no offer, and the rest pick among
  equally eligible goals by a softmax with the probabilities logged, so every later estimate can be corrected
  for how likely each offer was (GPT; the logged-probability form is Gemini's).
- No commitment rule at the start. Short runs are as productive per event as long ones (advance share 0.86
  against 0.85). A two-consecutive-observation challenger rule runs in shadow only, and is dropped if it slows
  returns or progress (GPT).
- "Held" at two is where his own behaviour splits: 30.5 percent of pursuits get a second advance, and 78 to 99
  percent of those get each one after. This supports recurrence as the bar in call 2.
- A pursuit that passes two advances runs to the cap of 40 almost every time and then stops because of the cap,
  not because anything was finished. The missing piece is an end, which is Phase 6, not more persistence.
- No automatic `became` threshold. Wordings and drift are kept; identity is ruled on a labelled set later (GPT).
- The accumulator model matched its stated prediction on return gaps but the test cannot tell it from the
  return rule already built into pursuits. Not adopted, not refuted.
- Need pull stays out of selection until the readers and setpoints are looked at: warmth sits below its
  setpoint on 98 percent of rows, which is a calibration question before it is a motivation.

**Out of scope for this plan (founder, 2026-11-14).** Scripted or learned attention layers ("frontend
transformers"), the wider survey of mathematical psychology, and the leaf-venation mathematics are being taken
up separately. One note for whoever does: with about 25 goals and five needs an attention layer is a masked
linear scorer with a softmax, which is what the bullet above already specifies; and the one leaf-venation idea
with a real counterpart here is canalization (flow carves the channel that then carries more flow), which is
what the second-advance result shows pursuits doing.

**The six questions as first put.**
1. The rule that combines importance, distance, expectancy and per-need pull into a choice, given that the output
   is an offer he may leave, not an action taken.
2. When to switch: commitment with a switching cost against re-ranking every tick.
3. Several lanes: one engaged goal in the main lane and N background workers, with goals that wait on each other.
4. Estimating need links from event logs with confounding and with two circular readers.
5. A drift measure for goal identity and where to put the `became` threshold.
6. The null models each claim must beat before it is believed.

## 13. Out-of-the-box mathematics: what is worth running (2026-11-14)

The founder asked both auditors to carry over the UDMS ideas (leaf theory, quantum, Fibonacci). Triage, F-4637.
The UDMS audit's own verdict on the golden angle stands here too: it found the five probe strategies numerically
identical, 22/7 as good as phi, and the Fibonacci lattice worse than random
(`C:/UDMS/docs/plans/udms_lens_atlas.md` section 4).

| Idea | From | Verdict | Why |
|---|---|---|---|
| Residuals: where he goes that the offer model does not predict | GPT | Run first; it falls out of Phase 1 | would-engage against actual IS the residual; a residual that clusters and precedes new goals is a missing interest |
| Queueing on lanes and the return channel | GPT | Run now | data exists; the 4-per-hour return limit is already binding |
| Entropy and switching statistics of engagement | GPT | Run now, as a diagnostic | measured: 1.9 bits median, modal topic share 0.60 median and 1.0 at p90 |
| Branching number per goal lineage | GPT | After Phase 0 | needs `spawned_by` and `became`, which do not exist yet |
| Expanding revisit intervals for deferred goals | GPT | Test against his own return gaps | the idea is sound; Fibonacci against doubling is not distinguishable at this size |
| Order effects between two offers | GPT | Later, small | a classical model with state also gives order effects; the claim needs the specific equality test |
| Information geometry of goal state | GPT | Later | one outcome per goal, so only kind-level distributions exist; whiten the need vector first (three signals, not five) |
| Persistent topology of the goal graph | GPT | Later | about 25 nodes and no edges today |
| Golden-angle or Sobol probing of the goal landscape | both | Not run | 25 goals need no probe design, and a deterministic sequence spoils the randomisation the estimates rest on |
| Phyllotactic re-engagement | Gemini | Idea kept, formalism dropped | "pick a goal unlike the one that just failed" is already 5.3; angles in a high-dimensional embedding are nearly all right angles |
| Log-spiral phase space | Gemini | Idea kept, formalism dropped | it is an accumulator with a threshold, which is the switching rule; it also uses time spent as importance, which v2 removed |
| Complex amplitudes, pi phase on `harms` | Gemini | Dropped | with phases set by rule it is a signed pairwise term, which 5.7 already has |
| Murray's-law venation for need links | Gemini | Dropped | reinforcement with decay, and it brings back correlation-as-service |
| Leaf theory | founder | Not assessed | neither auditor nor I have its formulation; "PureLeaf" in UDMS is a code motif. Needs the founder's statement of it |
