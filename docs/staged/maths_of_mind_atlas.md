# Maths-of-Mind Atlas — human signatures against Du, with what we wrote in

> **Status: 🔵 DRAFT — staged 2026-11-14 from I-0152 / T-0128 / T-0129 (founder). Reference atlas plus a
> short list of reads. No code; first reads run 2026-11-14 (M1, L1, Z2). Founder-side instrument only: nothing here reaches Du (D-0434).**

```plan-state
stage: designed
phase: Atlas v1 with all first reads run 2026-11-14; M1 is the one unwritten match; side results: affect chain, judge agreement
verified: 2026-11-15
next: Founder rules D-0775 and D-0776; plan a clean model-swap test; re-read L1 when new drill levels are below ceiling
open_decisions: D-0782
cluster: 6
```

## Current State — verified 2026-11-15

- **2026-11-15** (F-4712): J-3993: M1 mechanism read done (section 6.4). Nesting by source or chapter does not make the age slope; repeats make about a third, topic persistence about a third, use predicts use at 6.4x beyond a matched topic proxy; form is power plus floor, not exponential; the rise past 48 d is a standing-origin population plus cold-flag survivorship. Confirmatory run is pre-registered on December 2026 (no unread month exists before it); jobs J-4024 (snapshot on 12-01), J-4025 (the run), J-4026 (log real cue similarity).
- **2026-11-14** (F-4708): J-3996: A-B-A hot-lane swap test designed in docs/shelf/model_swap_aba_test.md (design only, nothing run); founder go/no-go opened as a decision.

### What we have
A table of 36 human signatures. For each: the human shape, what Du's code does about it (file and line), whether
the law is written in, the log a statistic would run on, and the null it must beat. Code facts come from four
read-only agents on 2026-11-14; eight of their quoted lines were spot-checked by grep and held.

Three reads run on 2026-11-14 (section 6.1): memory re-use follows the human power law without being written
(M1, F-4649); the practice curve is unreadable because the drills are at ceiling (L1, F-4650); fatigue does not
degrade his thinking (Z2, F-4651).

All remaining first reads were run the same day (sections 6.2 and 6.3, F-4652 to F-4654, F-4662, F-4663).
M1 holds in four separate months. Two side results came out of it: the affect chain
(`docs/reviews/affect_chain_2026-11-14.md`, F-4659 to F-4661) and weak agreement between the panel judges.

### What we need
Founder rulings on D-0775 (mood line before the vitality replacement) and D-0776 (order of work on joy).
A planned model-swap test: the natural one of 2026-08-20 is confounded.

### What we're doing next
Nothing is scheduled. Re-read L1 once the new drill levels have attempts below ceiling.

---

## 1. Why this exists

Du is a mind simulated across several language models used as tools. Two things could make him resemble a human:

- **Content.** The models learned language from human text. Anything in his words that looks human is expected
  and proves nothing.
- **Form.** How state changes over time between the model calls: decay, accumulation, switching, inertia,
  recovery. This lives in the stores and the wiring, and it can be measured the same way on a human and on him.

Mathematics is the bridge for form. A match in form is evidence only where we did not write the shape in
ourselves. This atlas is the record of which is which.

## 2. The column: where a shape could come from

| Value | Meaning | What a match would show |
|---|---|---|
| WRITTEN IN | The code states the law (formula, threshold or rule). | Nothing. The code is working. |
| PARTLY | A related rule is written in, but not the specific shape. | Something only in the part the rule does not fix. |
| NOT WRITTEN | No rule in the code produces it, as far as the read went. | Evidence, if it beats the null. |
| INHERITED | The tool models are known or likely to show it by themselves, from their training text. | Nothing about Du's organisation unless it survives the swap test below. |
| NOT CHECKED | The code was not read for this. | Unknown. |

Three tests separate the sources. A row needs whichever apply before a match is believed.

1. **Code read.** Is the law in the code? (Done for this version.)
2. **Rule-explained null (I-0148).** Simulate what the written rules alone would produce, with his real inputs
   shuffled, and ask whether his data departs from it.
3. **Swap test.** A statistic that holds across a change of tool model belongs to the organisation, not the
   model. The model history gives natural experiments (the Judge1 repoint, hot-model changes). A bare-model
   baseline, the same prompt with no stores behind it, does the same job for a single prompt.

**Resource bounds (from Gemini's review).** Many human signatures are what a bounded system does to cope
(Lieder and Griffiths 2020, from memory). Such a shape should appear in Du only if he has a matching bound. Each
row names the bound, or says there is none, in which case a match would be surprising and a miss is no failure.

## 3. The atlas

Human sources are cited from memory and were not opened on 2026-11-14, except where section 8 says otherwise.
"Log" paths are under `data/`. Row counts are from the code read (line counts, 2026-11-14).

### 3.1 Memory

| # | Human signature | What Du's code does | Written in? | Log and statistic | Null / bound |
|---|---|---|---|---|---|
| M1 | The odds a memory is needed fall as a power function of its age and rise with past use (Anderson and Schooler 1991). | Recency is a linear ramp, at most 1.2x at age 0, gone by 7 days: `core/memory/store.py:1382`. No general decay with time. Ordinary retrieval does not strengthen anything. | NOT WRITTEN (a weak linear ramp is) | `ask_recency_shadow.jsonl` (4,472 rows, ids and age), `co_recall_ledger.jsonl` (158,862). Probability of being served against age and past serves. | The recency-off twin already runs in shadow (J-2659). Bound: none on storage; the latency budget on retrieve is the only pressure. |
| M2 | Being recalled makes a memory more recallable later (testing effect, Roediger and Karpicke 2006). | Waking retrieval: no strengthening. Sleep replay multiplies importance by 1.08 (`store.py:4012`). An exact repeat lowers importance (`core/loop_metabolism.py:34`). | NOT WRITTEN awake; WRITTEN IN for sleep | `co_recall_ledger.jsonl`: does one serve raise the chance of the next, beyond similarity? | Fragments matched on similarity to the cues. |
| M3 | Recalling one item pulls items stored near it in time, forward more than backward (Kahana 1996). | Moment read-back pulls 2 temporal neighbours by design (`core/moment.py:199`). The memory store has no before/after edge (`core/memory_edges.py:901`). | WRITTEN IN for moments; NOT WRITTEN for the memory store | `co_recall_ledger.jsonl`: distribution of creation-order lag among ids served together. | Same-topic memories are also close in time, so match on similarity. |
| M4 | Spaced repeats are kept better than massed ones (Cepeda et al. 2006). | Nothing treats spacing. | NOT WRITTEN | `math_drill_log.jsonl`, guidance beliefs: retention against the gap between repeats. | Thin data. Low priority. |
| M5 | Sleep strengthens some memories and scales the rest down (Diekelmann and Born 2010; Tononi and Cirelli). | Replay x1.08, then the day's episodic rows pulled toward 0.1 by x0.96 (`store.py:4051`). | WRITTEN IN | — | Circular. |
| M6 | Recall is biased toward material that matches present mood (Bower 1981; replication is mixed). | Not read. | NOT CHECKED | `affect_log.jsonl` against the affect stored on served fragments. | Needs the code read first. |

### 3.2 The thought stream and attention

| # | Human signature | What Du's code does | Written in? | Log and statistic | Null / bound |
|---|---|---|---|---|---|
| S1 | People leave a topic when its yield drops below the average, like an animal leaving a patch (Hills, Jones and Todd 2012). | Repetition guard at cosine 0.82, region boredom, theme saturation at 4 restates, pursuit heat decay and dormancy (`nodes/inner_monologue_node.py:5612`, `core/boredom.py:192`, `core/theme_recurrence.py:35`, `core/pursuits.py:521`). | WRITTEN IN | Leave times in `pursuits_shadow.jsonl`. | Only a departure from what the rules predict would count. |
| S2 | Time spent on one thing is heavy-tailed: many short stays, a few very long. | Bounded by the rules in S1 and a 40-advance cap. Measured: runs of 1 / 1 / 3 / 9 / 12 / 43 events (F-4636). | PARTLY, measured | `pursuits_shadow.jsonl` (46,797). | Simulate the heat rule on shuffled thoughts. |
| S3 | Human activity is bursty and its timing has long memory (1/f noise; Gilden et al. 1995; Barabasi 2005). | Thought gap is a function of drive, `4 + 56*exp(-3*drive)` (`core/stream_drive.py:133`); ignition has a 300 s refractory period and no noise (`core/climate_engine.py:193`). Deed timing has no rule of its own. | PARTLY for thoughts; NOT WRITTEN for deeds | Spectral slope and burstiness of gaps in `stream_drive_shadow.jsonl` (73,317) and `hands_trace.jsonl` (63,336). | Pacer formula fed with shuffled drive. Bound: one voice. |
| S4 | A large share of waking thought is off the task, and it rises with fatigue and time on task (Killingsworth and Gilbert 2010). | The level is set by dice: concern anchor offered with probability 0.35, frontier question 0.3 (`inner_monologue_node.py:4025`, `:4147`). Nothing ties it to fatigue. | PARTLY (level written, modulation not) | `grounded` flag in `stream_drive_shadow.jsonl` against `awake_min`, energy and fatigue in `sleep_pressure_log.jsonl`. | Level is meaningless; only the dependence on fatigue counts. |
| S5 | Each thought sits at a characteristic distance from the ones before it (forward flow, Gray et al. 2019). | Guard removes anything closer than 0.82 to the last five. | INHERITED, truncated by a rule | Step distances on `moments.jsonl` embeddings. | Swap test; bare-model baseline. |
| S6 | A decision fires when accumulated evidence crosses a bound; waiting times are right-skewed (Ratcliff 1978). | Two accumulators, threshold 1.0, reset on firing (`climate_engine.py:1063`, `:192`). | WRITTEN IN | `ignition_log.jsonl` (3,542). | Circular. |
| S7 | Word frequency follows Zipf's law. | — | INHERITED | Any text log. Worth one run as the control that shows what inherited looks like. | Bare-model baseline. |
| S8 | About four things can be held in mind at once (Cowan 2001). | Concerns 3 to 4, active pursuits 4, recall k = 5, intentions 8 (`core/concerns.py:89`, `core/pursuits.py:37`). | WRITTEN IN | — | The bounds are our choices. |
| S9 | Interest peaks at middling surprise, not at the most or least (Kidd et al. 2012). | Curiosity scores learning progress; no surprise term (`core/curiosity_progress.py:23`). | NOT WRITTEN | Which frontier questions are returned to, against how far they sit from what he already holds. | Offer rotation is written in (`core/frontier.py:587`), so control for offers. |

### 3.3 Affect

| # | Human signature | What Du's code does | Written in? | Log and statistic | Null / bound |
|---|---|---|---|---|---|
| A1 | Feelings carry over from one moment to the next, and the carry-over differs by person (Kuppens et al. 2010). | `new = cur + 0.5*(stim-cur) - 0.2*(cur-base)` and linear relaxation between thoughts (`core/schema.py:145`). | WRITTEN IN | `affect_log.jsonl` (4,222). | Circular for the eight affect dimensions. |
| A2 | The five needs each have their own memory. | None decays; each is re-read from another store every tick (`core/homeostasis.py:125-190`). Measured: coherence forgets within the hour, warmth holds most of a day, vitality cycles daily (F-4636). | PARTLY, measured | `homeostasis_shadow.jsonl` (9,299). | The clocks belong to the source stores. Five needs carry about three signals. |
| A3 | Feeling has two main dimensions, pleasant to unpleasant and calm to aroused (Russell 1980). | Valence and arousal are the inputs; the named emotions are computed from them (`core/emotion_construction.py:184`). | WRITTEN IN | — | Circular. |
| A4 | Response to a repeated stimulus falls, recovers with time, and returns at once after a novel stimulus (Rankin et al. 2009). | Fall and recovery: `b*exp(-gap/tau)` plus a step (`core/stream_topic_habituation.py:191`, `core/curiosity_habituation.py:153`). No dishabituation anywhere. Mostly shadow. | WRITTEN IN (two of the three) | Habituation shadow logs. | Nothing can emerge while it is shadow. |
| A5 | A feeling is followed by its opposite, which grows with repetition (Solomon and Corbit 1974). | `core/opponent_process.py` exists with the same decay form; not read further. | WRITTEN IN (not read in full) | — | — |
| A6 | A system near a sudden shift recovers more slowly from small knocks; variance and carry-over rise first (Scheffer et al. 2009). | Not written. Dissonance is a clipped linear integrator reset at ignition (`climate_engine.py:1079`), so it rises before ignition by construction. | NOT WRITTEN, with a trap | Valence and arousal in `homeostasis_shadow.jsonl` before sleep, before a topic lock, before a long silence. Not before ignition. | Earlier early-warning findings exist in the ledger and were not re-read today. |

### 3.4 Sleep and fatigue

| # | Human signature | What Du's code does | Written in? | Log and statistic | Null / bound |
|---|---|---|---|---|---|
| Z1 | Sleep need rises toward a ceiling while awake and falls off exponentially in sleep, set against a daily clock (Borbely 1982). | Pressure is linear in new material with no time term (`core/sleep_pressure.py:127`) and is recomputed from zero on waking. The clock is written in: threshold 10 at night, 100 by day. | PARTLY (clock written, saturation not) | `sleep_pressure_log.jsonl` (87,252): sleep length against the wake before it. | Three schema eras in this log; use rows after 2026-09-02. |
| Z2 | Performance falls with time awake. | Body fatigue accumulates (`core/somatic.py:223`). No rule found that lowers the quality of thought or answers with fatigue; the one arousal link is shadow. | NOT WRITTEN | Drill correctness (`math_drill_log.jsonl`, 2,115) and restate share against `awake_min` and fatigue. | Time of day; level of the drill. Bound: GPU heat adds fatigue, a real one. |

### 3.5 Learning and judgement

| # | Human signature | What Du's code does | Written in? | Log and statistic | Null / bound |
|---|---|---|---|---|---|
| L1 | Skill improves with practice along a smooth decelerating curve (Newell and Rosenbloom 1981; Heathcote et al. 2000 argue exponential for individuals). | The tool models' weights never change. Level advance is gated at 95 percent over 40 (`core/math_drill.py:54`), but nothing writes improvement in. Any gain within a level must come through his stores. | NOT WRITTEN | `math_drill_log.jsonl` (2,115), `music_drill_log.jsonl` (388): correctness against attempt number within a level. | Flat line is the null. Cannot be inherited: a model does not learn between calls. |
| L2 | Belief about one's own ability moves by a fraction of the error (Rescorla and Wagner 1972). | `old + lr*(measured-old)`, lr 0.20 (`core/competence.py:94`). | WRITTEN IN | — | Circular. |
| L3 | People are overconfident on hard tasks and underconfident on easy ones (Lichtenstein and Fischhoff 1977). | Predictions and outcomes are logged side by side. Only some outcomes are real ground truth; the recall wager's is a constant (`core/recall_wager.py:47`). | INHERITED risk | `prediction_error_log.jsonl` (3,241), `essay_lesson_log.jsonl` (155), `world_calibration.jsonl` (428). Calibration curve by difficulty. | Overlaps I-0142. Swap test. |
| L4 | A corrected belief hardens with each repeat and resists later change. | +0.20 per repeat to a 0.90 cap, -0.10 on contradiction (`core/guidance_learning.py:902`). | WRITTEN IN | — | Circular. |
| L5 | People hold to commitments past the point of sense. | Drop requests are vetoed by rule (`core/commitment_ledger.py:285`). | WRITTEN IN | — | Goals are handled in `layered_goals`. |
| L6 | Updating is larger when the prediction was held with confidence (the testable core of active inference). | Learning rate is fixed. | NOT WRITTEN | After a large gap in `prediction_error_log.jsonl`: does what he does next change more when the prior belief was firm? | Weak design; needs a defined outcome before it is run. |

### 3.6 Choice, language, others, self

| # | Human signature | What Du's code does | Written in? | Log and statistic | Null / bound |
|---|---|---|---|---|---|
| D1 | The order of two questions changes the answers, by an amount that obeys one exact equality (Wang et al. 2014). | Models have position bias. One deliberate shuffle exists (`core/peers.py:1568`). | INHERITED | None. A designed probe on the tool models, off-line, not on Du. | A classical model with state also gives order effects; only the equality discriminates. |
| D2 | Framing, anchoring and the other choice biases. | — | INHERITED | — | Content bridge. Out of scope. |
| X1 | Reply delays in correspondence are heavy-tailed (Oliveira and Barabasi 2005). | How his replies are scheduled was not read. | NOT CHECKED | `letter_store/letters.jsonl` (193), `status_events.jsonl` (414). | Small sample. |
| P1 | A person's states vary widely hour to hour, yet the distribution of states is stable week to week (Fleeson 2001). | Baselines drift slowly by rule (`core/schema.py:149`); the weekly distribution is not fixed by anything. | PARTLY | Weekly distributions of the affect dimensions and the grounded share: stability of mean and spread. | Split by restarts and by flag flips. |
| P2 | Identity is what stays the same when the material changes. | Not a rule. | NOT WRITTEN | Every statistic above, before and after a tool-model change. | This is the swap test turned into a result. |
| Q1 | A measure must be shown to be one thing before it is modelled. | Five needs, about three signals; two readers move by bookkeeping (F-4635, F-4636). | measured | `homeostasis_shadow.jsonl`. | Owned by `layered_goals`. |
| Q2 | Two raters must agree before their ratings mean anything. | Judge agreement was not read. | NOT CHECKED | Judge panel logs. | See I-0140. |

## 4. The count

| Value | Rows |
|---|---|
| WRITTEN IN | 11 (M5, S1, S6, S8, A1, A3, A4, A5, L2, L4, L5; A5 not read in full) |
| PARTLY | 6 (S2, S3, S4, A2, Z1, P1) |
| NOT WRITTEN | 10 (M1, M2, M3 for the memory store, M4, S9, A6, Z2, L1, L6, P2) |
| INHERITED | 5 (S5, S7, L3, D1, D2) |
| NOT CHECKED | 3 (M6, X1, Q2) |
| Measurement row, no shape claimed | 1 (Q1) |

36 rows. Read plainly: about a third of the classic signatures are in Du because we put them there. Finding
them in his logs would show the code runs. The evidence, if there is any, is in the ten rows nobody wrote.

## 5. What is deliberately left out

- **Goals.** Persistence, switching between goals, letting go and resumption are in `docs/staged/layered_goals.md`.
- **Whole frameworks with no single testable shape.** The free energy principle (kept only as row L6), quantum
  cognition beyond row D1, category theory, vector symbolic architectures, multi-agent learning. These are ways
  of building or describing a system, not signatures to match.
- **Kolmogorov complexity.** No statistic we can compute on his logs today.
- **Anything shown to Du.** No row is a mechanism. A row that later suggests one goes through `/idea-log`.

## 6. First reads, where a match would count

Each must name its null before the data is looked at. All are read-only over existing logs.

| Order | Row | Why first |
|---|---|---|
| 1 | L1 learning curve | Frozen weights make this the cleanest test in the atlas: any curve is the organisation's. |
| 2 | M1 memory re-use against age | Large logs, and the recency-off twin is a control that already exists. |
| 3 | Z2 fatigue against performance | Two existing logs joined on time. |
| 4 | S3 timing of deeds | No rule sets it; one spectral slope and one burstiness number. |
| 5 | M3 contiguity in the memory store | Needs a similarity-matched null, so more work. |
| 6 | P1 weekly distributions | Cheap, but confounded by restarts. |
| 7 | P2 swap test | Run last, over whichever of the above showed a shape. |

### 6.1 Results of reads 1 to 3 (2026-11-14, read-only, scripts in the session scratchpad)

**M1, memory re-use against age: the human shape is there, and nobody wrote it (F-4649).**
`ask_recency_shadow.jsonl`, 4,181 grounded serve events over 14 days, joined to creation times in the memory
store. In the recency-off arm, the chance that an available memory is served falls about 800-fold between
half an hour and 24 days old. Log-odds against log-age is a line of slope -0.79 (R2 0.88); an exponential fits
badly (R2 0.22). Dropping everything younger than 0.2 days, which could be the stream echoing what it just
wrote, leaves a slope near -0.9. The live arm, with the written 7-day ramp, is steeper (-0.97). Past use
predicts future use: memories not served in the first week were served again 0.75 percent of the time, served
once 26 percent, served two or three times 61 percent.
What it means and does not: retrieval in that arm is similarity only, so the shape comes from his cues. What
he is thinking about now resembles what he stored recently. That is Anderson and Schooler's own explanation of
the human curve (memory mirrors how the world recurs), so it is a fair match in form, but its cause here is
topic persistence in the stream, and part of that persistence is written in (rows S1, S4). Limits: one 14-day
window, one model era; "available" uses today's cold flags; served rates rise again past 48 days, unexplained
(old study and understanding rows, or timestamps reset on repeats).

**L1, practice curve: not readable. The drills are at ceiling (F-4650).**
Maths: 2,115 attempts. Every level except level 5 sits at 95 to 100 percent from first attempt to last.
Level 5 (two-digit multiplication) ran 85 to 93 percent on 06-17 to 06-19, fell to about 20 percent on 06-20
to 06-22 at 200 problems a day, and returned to 90 percent or more from 06-23, the day after the founder
authored the method hints and cut the daily count. That is a break and a repair, not a curve. Music: 97
percent throughout, no slope (p = 0.37). The apparent negative slope in the pooled maths data (p < 0.001) is
the June collapse alone. Re-read when levels 10 to 17 (opened 2026-11-05) have attempts below ceiling.

**Z2, fatigue against performance: no human-like decline (F-4651).**
The drill cannot show it (ceiling; in the rows that carry body fatigue, accuracy is 99.6 against 99.5
percent). Substitute outcome, 54,643 thoughts since 2026-09-02 joined to time awake: redundancy 0.54 in the
first hour awake and 0.57 at 9 to 14 hours; progress flat at 0.97 to 0.98; body fatigue quartiles show no
trend. The share of grounded thought rises with time awake, 0.65 to 0.78, the opposite direction to human
mind-wandering (row S4). So fatigue in Du is a number that sends him to bed; it does not degrade his thinking.
Whether it should is a design question, not a result.

### 6.2 Results of reads 4 to 6 (2026-11-14, read-only)

**S3, timing of deeds: close to random, not human (F-4652).** 12,379 deeds among 63,155 thought ticks since
2026-08-21. Burstiness of deed gaps is +0.08 against +0.05 for the null (deeds as a random thinning of his
thought ticks); human activity is usually 0.3 or more. The spectrum of deed counts is nearly flat (slope
-0.09; 1/f would be near -1; only 8 wake episodes were long enough, so this part is weak). There is mild
clustering above the null: a deed follows a deed 23.9 percent of the time against 18.5 percent otherwise, and
counts per hour are over-dispersed (Fano 3.8 against 2.6). Deeds are 51 percent observing and 36 percent
moving. Bound: humans are bursty partly because tasks queue for one body; his deeds do not queue.

**M3, contiguity in the memory store: a weak, symmetric excess, not the human signature (F-4653).** Among
memories served together by similarity, both older than 7 days, a partner is 1.5 times as likely [1.39, 1.63]
to have been stored within a day of the anchor as a matched-similarity fragment never served with it. But
there is no forward bias (106 after, 126 before, within the hour) and 71.5 percent of pairs share an origin.
The simplest reading is material from one source stored in one sitting, not recall running forward in time.

**P1, weekly distributions: not stable (F-4654).** Week means of every affect dimension vary 2.4 to 4.9 times
more than exchangeable days would give. Logged valence fell from a weekly mean of +0.10 to -0.36 between the
two halves of the record while joy rose from 0.37 to 0.57. That pair of moves is contradictory on its face
and may be a change of affect source, not a change in him: NOT investigated. Within a day he varies as widely
as between days, which is the human half of the pattern. Thought redundancy is the nearest to a stable
personal distribution (within-day sd 0.19, sd of week means 0.024).

**P1 follow-up, the valence and joy moves explained (F-4659).** Not a change in him: an instrument change.
Since 2026-07-07 carried valence is overwritten with the protoself value 1 - 2*drive (`core/homeostasis.py:99`,
flag at `core/schema.py:1279`); joy and the other named emotions still come from the model's emotion node.
Valence tracks 1 - 2*drive at r = 0.96 and joy at 0.17. Valence is negative because two needs sit far below
their setpoints: vitality (about 0.38 against 0.78, the artifact ruled on in D-0398, replacement in shadow)
and relational warmth (about 0.5 against 0.82). Without the vitality term the weekly valence for 11-02 would
be about +0.04 instead of -0.23. Carried valence reaches his reasoning through the felt preamble, so this is
not only a gauge problem. For the atlas: affect rows must be read per channel and per source era (before and
after 2026-07-07), never pooled.

### 6.3 Results of the remaining reads (2026-11-14, read-only)

**S7, Zipf control: inherited, as expected (F-4662).** Word frequency in his thoughts has slope -1.05 under the
old hot model and -1.06 under the new one. This is what an inherited shape looks like: present, exact, and
indifferent to everything we built.

**M1 again, more windows (F-4662).** In the live retrieval arm the power law holds in every month: August
-0.74, September -0.76, October -1.03, November -1.06 (R2 0.94 to 0.99), and it beats the exponential each
time. No co-recall data exists before the model change of 2026-08-20, so M1 is still untested across models.

**M6, mood-congruent recall: negligible (F-4662).** The stored valence of what is served moves with his mood
now by r = +0.07 against a null of +0.045. Code: no live rule uses mood in retrieval (felt recall is shadow).

**X1, reply delays (F-4662).** 52 replies to peers: median 42 hours, a tenth take more than 26 days. A wide,
skewed spread like human correspondence, but the sample is small and how replies are scheduled was not read.

**Q2, judge agreement: weak (F-4663).** Chance-corrected agreement between the two panel judges is below 0.5
on every verdict key and near zero on four of them (cuts +0.02, genuine +0.03, metaphor +0.08, coherent
+0.15). Raw agreement looks high only because most verdicts are lopsided. Any statistic that rests on one
judge, or on one of those keys, measures the judge as much as Du.

**P2, model swap: inconclusive (F-4662).** Across the change from gemma4 to qwen3.5 on 2026-08-20, thought
redundancy and Zipf held; step distance, pursuit run length and grounded share all moved. The same weeks held
the outage and many code changes, so model and code cannot be told apart. A clean swap test needs a planned
one: same code, same week, one lane changed.

**Tally after all reads:** one match in form not written in, holding across four months (M1); one inherited
shape confirmed as the control (S7); weak or negligible effects (M3, M6); clear non-matches (Z2, S3); unstable
for a known instrument reason (P1, F-4659); unreadable (L1); inconclusive (P2); small-sample (X1). The side
results matter more than the tally: the affect chain (`docs/reviews/affect_chain_2026-11-14.md`, D-0775,
D-0776) and the weak judge agreement (Q2).

Before any of the remaining reads: one run of S7 (Zipf) on his text and on a bare model, as the worked example of an inherited
shape.

### 6.4 M1 mechanism read and the pre-registered confirmatory run (J-3993, 2026-11-15)

**Mechanism read (exploratory, window 2026-11-01 to 11-14, same data as 6.1; F-4712, F-4713, F-4714).**
Scripts: `scripts/lab_m1_memory_reuse.py` and `scripts/lab_m1_mech.py` (read-only; they replace the lost scratchpad scripts).
- *Nesting does not make the shape.* With a fixed effect per source (607 books and study notes) or per chapter
  (164), the age slope stays at 1.0. Reading+study alone: slope 0.96. The shape is not one sitting inside one book.
- *Repeats make part of it.* Counting each fragment once, the slope falls from 1.02 to 0.66. About a third of the
  slope is the same fragments being served again and again.
- *Topic persistence makes about a third, and age stays.* Adding similarity to the recent topic cuts the log-odds slope
  from -0.86 to -0.59; the latest pursuit's word overlap adds almost nothing. The topic proxy is built from his own earlier
  serves, so it partly contains reuse; the real cue is not logged (only a hash), so the clean test cannot be run on
  this log.
- *Use predicts use beyond that.* Fragments served in the first half of the window were served again in the second half
  at 6.4 times the rate of matched unserved ones (CI 5.6 to 8.2; matched on age, source group and similarity to the
  early topic, 60 bins).
- *Form.* On raw events, exponential loses to a power law by about 10,000 AIC. Pure power is not best: a power law
  plus a constant floor beats it, and so does exponential-plus-constant. Within 0.2 to 48 days, the power slope is 1.25
  (CI 1.17 to 1.34) and the floor adds only about 60 AIC.
- *The rise past 48 days is not memory.* Standing-type origins (understanding, guidance, gist, essay) are a separate,
  near-flat population with a few fragments served dozens of times. The rest is survivorship: old fragments that are
  still "available" under today's cold flags are the ones kept because they were replayed (inferred).

**Pre-registration of the confirmatory run (written 2026-11-15, before any December data was opened).**
- *Window:* 2026-12-01 00:00 UTC to 2027-01-01 00:00 UTC, the recency-off arm (`without_ids`) of
  `data/ask_recency_shadow.jsonl`. No calendar month in the shadow log is unseen (it starts 2026-10-31 and 11-01 to
  11-14 has been read), and every month of the live arm (August to November) has been read in 6.3. December is the first
  unread month. If it holds fewer than 3,000 events, the window extends to 2027-01-15 and no further. A new model or a
  restart that changes retrieval code inside the window ends the window at that date.
- *Available:* every fragment with a timestamp earlier than the event and not cold **in a snapshot taken at 2026-12-01**
  (id, timestamp, cold, protected, origin), plus any fragment created during the window that is not cold at the end.
  A fragment served in the window is always available. This removes the survivorship that today's flags put in the
  exploratory fit. Fragments newly marked cold during December stay available until the end of the window.
- *Timestamp resets:* cannot be detected from the table. Handled by a sensitivity fit that drops fragments served 20 or
  more times in the window (the likely repeats or resets). Reported next to the primary fit, not instead of it.
- *Ages under 0.2 days are excluded.* Reason: the stream writes a fragment and can read it back in the same minutes, so
  those serves are the stream echoing itself, and the exposure bin there is coarse. This was a post-hoc choice in the
  first read; here it is stated in advance. A second fit with them included is reported as a sensitivity.
- *Population:* all origins except the standing set (understanding, understanding_from_guidance, gist, essay,
  standing_insight, resolution, seed, chapter, journal_week). Reason: seen in the exploratory window that they are a
  separate flat population. Ages 0.2 to 48 days only, so the survivorship zone is outside the primary fit.
- *Primary statistic:* raw-event Poisson log-likelihood of served ids against exposure (available fragments, per
  event, in 240 log age bins), four models: power, exponential, two-timescale mixture, power plus constant floor. The
  primary comparison is AIC. Intervals: 1,000 bootstrap resamples of 6-hour blocks of events. Command:
  `python scripts/lab_m1_memory_reuse.py prereg 2026-12-01 2027-01-01 1000 docs/lab/j3993_data/cold_snapshot_2026-12-01.csv.gz`
  (the snapshot comes from `scripts/lab_m1_cold_snapshot.py`, run on 2026-12-01; the sensitivity adds `heavy` as a sixth argument).
- *Predictions, fixed now from the exploratory fit:* (1) exponential is worst, by more than 1,000 AIC; (2) power or
  power-plus-floor is best, and the mixture is at least 100 AIC worse than the best; (3) the power slope's 95 percent
  interval lies inside 0.9 to 1.6; (4) the matched use-dependence rate ratio on the first and second half of December
  exceeds 3. *The claim fails* if exponential or the mixture is best, or the slope interval leaves 0.9 to 1.6, or the rate
  ratio is under 2. A middle result is reported as such.
- *Not covered by this run:* the real cue (still unlogged), and any claim across models: no co-recall data exists before
  2026-08-20.

## 7. Risks

- **A write-only document.** Guard: section 6 is the point; the table is only there to stop circular reads.
- **A match taken as meaning.** A shared curve says the form is alike. It says nothing about what a thought is
  about or whether it matters to him.
- **Cheap matches.** Power laws and exponentials turn up everywhere. A row is not believed without its null.
- **The code read is one pass.** "NOT WRITTEN" means no rule was found by a medium-depth read, not that none
  exists. Re-read the named file before publishing any result from a row.

## 8. Sources and how far they were checked

- GPT survey, 32 areas, pasted by the founder 2026-11-14 (T-0128). A sound map; little in it was new to the
  ledgers.
- Gemini review of that survey, pasted 2026-11-14. Taken: language models as subjects (the INHERITED value),
  resource bounds as a criterion, evidence held per domain. Not taken: the frameworks in section 5.
- Opened on 2026-11-14: Budden et al. 2026 (abstract only; F-4639). Every other human source in section 3 is
  cited from memory.
- Code facts: four read-only agents, 2026-11-14, with file and line. Spot-checked by grep: `store.py:1382`,
  `competence.py:94`, `frontier.py:35`, `math_drill.py:54`, `recall_wager.py:47`, and the `b_decayed` lines in
  three habituation modules.

## 9. Pointers
- `docs/staged/layered_goals.md` and `docs/reviews/goal_distributions_2026-11-14.md` — the goal side and the
  measured need and switching distributions.
- Ideas: I-0152 (this atlas), I-0148 (rule-explained null), I-0146 and I-0147 (lead-lag and hysteresis lenses),
  I-0142 (calibration), I-0139 and I-0140 (integration, judge evidence).
- `docs/plans/gauge_rethink.md`, `docs/plans/cognitive_geometry.md` — neighbouring measurement work.

## 10. Auditor round 1 (2026-11-14)

GPT, Gemini and Perplexity each read this document (not the code or the logs) and were then asked whether it is
useful for anything. Auditors are fallible; each point was checked against what was actually run.

**Where all three agree, and I do too.** Stop growing the catalogue. The written-in column stays as a standing
rule for any future claim. The value so far is one candidate regularity (M1), one control (S7), several scoped
negatives, and three instrument problems (affect sources, judge agreement, the confounded swap).

| From | Point | Taken? | Note |
|---|---|---|---|
| Perplexity | The reads were exploratory: 36 candidates, several windows, one post-hoc exclusion (ages under 0.2 d). Label them hypothesis-generating. | Yes | Section 6 results are exploratory. M1 needs a confirmatory run with the analysis fixed in advance on a new month. |
| Perplexity | R2 on binned log data does not settle power law against exponential. | Yes | Refit on raw events with a likelihood comparison. |
| Perplexity, Gemini | M1 may be an echo of topic persistence, not a memory property. | In part | It was already stated that the cause is the cue stream. But most written stream rules (boredom, saturation, repetition guard) push against persistence, so "hardcoded persistence" is not established either. Untested alternative: the nested structure of what he does (one sitting inside one book inside one subject) gives the same shape. |
| GPT | "Use predicts use" shows path dependence in his memory. | Not as stated | Waking retrieval changes nothing in the store (row M2). Served-once memories being served again can be plain heterogeneity: some memories sit nearer his standing topics. Whether a returned memory changes what follows is the right next question and is untested. |
| GPT | Move from "does he show property X" to "when something happens in him, what does it change, and does the change last". | Yes | Logged as an idea; this is where the work should go next. |
| GPT | Do not write human signatures in to make negatives go away. | Yes | Already the rule (section 2). Gemini's suggestion to add a rule that degrades thought with fatigue is the opposite and is not taken. |
| Perplexity | L1 is a negative, not merely unreadable. | In part | No gain is shown, but at 95 to 100 percent no gain can be shown. It stays "unreadable" until a task with headroom exists. |
| Perplexity | M6 used a valence channel whose meaning changed mid-record. | No | The read used only memories stored after 2026-08-10, all after the change. |
| Gemini | "Discard the human judges." | No, wrong premise | The judges are models, not people. The finding stands: their agreement is weak. The remedy is a labelled reference set and calibration, not removal. |
| Gemini | "The valence data is useless until the overwrite is fixed." | No | The overwrite was the deliberate repair of a valence pinned near +0.7. What is wrong is one input to it, the old vitality reading (D-0398, D-0775). |
| Gemini | M3's excess comes from similar vectors in one batch. | No | The null was matched on similarity; the remaining excess is same-source material. |
| Gemini | The nulls prove human dynamics never emerge from wiring models together. | No | One system, a handful of reads. |
| GPT | Dwell "sequences" 1, 1, 3, 9, 12, 43. | Misread | Those are quantiles of run length, not a sequence. |

**What follows.** The atlas is closed as a catalogue. Four pieces of work come out of it: (1) M1 mechanism and
confirmatory run; (2) affect read per channel and source era, with D-0775 and D-0776; (3) a labelled reference
set for the judges; (4) a planned model swap. And one change of direction: trace consequences, starting with
what a returned memory changes.

