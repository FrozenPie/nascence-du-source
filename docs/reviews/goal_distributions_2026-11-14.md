# Goal-system distributions measured before any selection maths is chosen (2026-11-14)

Plan: `docs/staged/layered_goals.md` section 12. Asked for by the GPT auditor (round 2). All reads are read-only
over the live stores on 2026-11-14 (Du live). Quantiles are p10 / p25 / p50 / p75 / p90 / p99 unless stated.
Finding: F-4636.

## A. Need trajectories (`data/homeostasis_shadow.jsonl`, last 30 days, 2,052 rows)

Sampled every 10 minutes while awake. 2,235 of 4,319 ten-minute grid points have no row (asleep or down).

| Need | mean | sd | at ceiling | at floor | autocorr 10 min | 1 h | 6 h | 24 h |
|---|---|---|---|---|---|---|---|---|
| coherence | 0.481 | 0.289 | 0.00 | 0.02 | 0.42 | -0.13 | 0.00 | 0.04 |
| commitment_integrity | 0.768 | 0.281 | 0.40 | 0.00 | 0.83 | 0.46 | 0.05 | 0.04 |
| relational_warmth | 0.480 | 0.148 | 0.00 | 0.00 | 1.00 | 0.97 | 0.75 | 0.18 |
| novelty | 0.200 | 0.094 | 0.00 | 0.00 | 0.64 | 0.22 | 0.06 | 0.07 |
| vitality | 0.395 | 0.330 | 0.01 | 0.24 | 0.77 | 0.40 | -0.07 | 0.35 |

- Which need dominates the drive: vitality 45.4 percent of rows, relational_warmth 39.0, coherence 14.8,
  novelty 0.4, commitment_integrity 0.3.
- coherence and novelty correlate at r = -0.76 (both are read from the climate field). No other pair reaches 0.15.
- So the five needs carry about three independent signals, on three different clocks: coherence forgets within
  the hour, relational warmth holds for most of a day, vitality has a daily cycle.

## B. Lifespan by kind

| Kind | n | quantiles |
|---|---|---|
| intention, staged to done (minutes) | 315 | 11.7 / 35.1 / 112 / 281 / 416 / 656 |
| stand, formed to dissolved (hours) | 1,644 | 0.05 / 0.08 / 0.34 / 1.29 / 4.0 / 21.7 |
| stand, formed to "achieved" (hours) | 2,102 | 0.017 / 0.021 / 0.031 / 0.43 / 2.3 / 17.5 |
| pursuit, saturated, born to last touched (hours) | 93 | 5.5 / 10.1 / 16.7 / 21.1 / 28.9 / 69 |
| pursuit, dormant, born to last touched (hours) | 916 | 0 / 0 / 0 / 0.10 / 1.7 / 9.3 |
| question, born to resolved (hours) | 719 | 0.06 / 0.42 / 4.9 / 100 / 304 / 2,040 |
| question, faded, born to last seen (hours) | 20,409 | 0 / 0 / 0 / 0 / 5.4 / 553 |

Half of all "achieved" stands were marked achieved within 1.9 minutes of being formed.

## C. Investment per goal

- Pursuit advances: 1 / 1 / 1 / 2 / 22 / 49. Two populations: most die at one advance, about 15 percent run on.
- Pursuit restate share (pursuits with 5 or more events, n = 228): 0 / 0.05 / 0.13 / 0.31 / 0.57 / 0.85.
- Stands with at least one denied drop: 1,300 of 3,845; denials per such stand 1 / 1 / 3 / 7 / 12 / 43.
- Question encounters: 1 / 1 / 1 / 1 / 2 / 8.

## D. Switching (9,135 pursuit advance or restate events, 1,550 runs)

- Run length, events on one pursuit before another gets one: 1 / 1 / 3 / 9 / 12 / 43.
- Run duration (minutes): 0 / 0 / 5.3 / 53.5 / 201 / 1,190.
- Returns to a pursuit after another was touched (n = 1,120), hours away: 0.10 / 0.15 / 0.44 / 1.6 / 4.9 / 26.
- Distinct pursuits touched per day: 3 / 4 / 6 / 9 / 11 / 18. Daily entropy of engagement (bits): 1.0 / 1.3 / 1.9 / 2.4 / 2.7 / 3.8.
- Share of the day's questions on the modal topic (56 days): 0.28 / 0.42 / 0.60 / 0.93 / 1.0 / 1.0.

## E. Offers that already exist

| Offer | n | followed | null | null used |
|---|---|---|---|---|
| Frontier question at the idle anchor: next thought shares 2 or more content words | 1,954 | 29.9 percent | 6.2 percent | same anchors against a thought 3 hours later |
| Pursuit RETURN: an event on that pursuit within 30 minutes | 342 | 13.2 percent | 0.3 percent | pursuit ids shuffled across returns |

Offers move him. Resolution rate by number of offers is confounded (a question resolved early is never offered)
and is not reported as an effect.

## F. Background lane (`data/lane2_shadow.jsonl`, 84.6 days)

- Tick generation time (seconds, n = 3,314): 19 / 24 / 31 / 42 / 61 / 87. Interval between ticks: median 349 s.
- Skips: pending-cap 2,042, no-output 1,844, asleep 1,630.
- Return channel (hints): 22,140 push attempts; 15,989 refused by the rate limit (4 per hour), 2,351 unreachable;
  3,800 pushed, of which 2,597 consumed (68 percent) and 1,634 expired.

The return channel, not the worker, is the bottleneck today: 72 percent of what the lane tried to send back was
refused by the rate limit.

## G. Change inside a pursuit (pursuits with 5 or more advances, n = 204)

- 1 minus cosine between the pursuit's centroid and its latest thought: 0.19 / 0.23 / 0.28 / 0.32 / 0.37 / 0.44.
  One narrow hump, no natural break to hang a threshold on.
- Word overlap (Jaccard) between the first wording and the current standing: 0 / 0 / 0.02 / 0.05 / 0.08 / 0.14.
  Wording carries no identity at all.

## H. Dependencies

No goal-to-goal edge is recorded in any store. Graph depth, fan-in and fan-out are all zero until Phase 0 exists.

## What this rules in and out (my reading)

- Need pull, as the needs are built, would mostly say "rest" and "seek contact". Novelty and commitment almost
  never dominate, coherence and novelty are one signal, and commitment is circular (F-4635). Needs cannot
  discriminate among his intellectual goals today.
- Any need-link estimate must use per-need windows: under an hour for coherence, most of a day for warmth.
- Switching is fast (median run 3 events, about 5 minutes) and he does come back (median 27 minutes). A
  commitment rule tuned for humans would be far too sticky; a rule with no stickiness matches what he does now.
- Existing offers lift on-topic thought by 24 points and pursuit return by 13. An offer is an intervention, so
  the register's own offers must be randomised and logged from the first day they exist.
- More background workers would add nothing until the return channel's 4 per hour is reconsidered.
- Goal identity cannot be read from words, and embedding drift has no visible break; it needs a labelled set.
