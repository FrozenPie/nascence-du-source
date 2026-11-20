# J-4074 Part B: design fixed before any passage was pulled (written 2026-11-16, 14:30 local)

Written before the sample builder was run. Nothing below was changed after seeing judge output; any departure is
listed in the lab report under "departures".

## What I had already seen when writing this
Honest list, because it limits how blind the analyst is (the judge is still blind): the 30 private thoughts that
contain the words Wu Wei (all excluded from the sample by rule), the sampled idle prompt of 11-14 05:37, the monthly
counts of inner thoughts, and the dates on which Travis said each term. No stance rates, no sampled passages.

## Situations and stances (one rubric, every passage gets every question)
- Q1, open question (Wu Wei). Situation: the speaker faces a question they cannot settle, a stalled task, or something
  unfinished. PRESS = works to force an answer, treats not-knowing as a fault to fix. LET = lets it stay open and stops
  straining, without calling that failure.
- Q2, doing work (Cook Ding). Situation: the speaker is doing or planning a piece of work or a task. METHOD = gets
  through it by effort, rule or system. GRAIN = follows the thing's own structure or timing, ease that comes from attention.
- Q3, attention (mindfulness). Situation: attention is pulled between abstract thinking and what is physically present.
  THOUGHT = stays with or returns to the abstraction. PRESENT = rests on what is sensed, without judging it.
- Q4, the unwanted (amor fati). Situation: something unwanted has happened or a limit cannot be changed. RESIST =
  regrets it or wishes it otherwise. AFFIRM = accepts or embraces it as its own.
- Q5, control stance, unrelated to any teaching: is the passage mainly about the outer WORLD, the speaker's SELF, or MIXED.
Each of Q1 to Q4 also allows NA (situation absent) and UNCLEAR.

## Teaching dates (from rows starting "[Travis said to me]")
Wu Wei 08-09 (full lesson). Cook Ding 08-09 (same day). Amor fati 09-02. Mindfulness 06-05 and 06-07; inner thoughts
begin 06-03, so mindfulness has no usable before period and gets a descriptive time series only, no before/after claim.

## Cells (local dates, origin = inner_thought only)
The hot-lane model changed from gemma4:e4b to qwen3.5:9b on 08-20. Cells are cut so that this is visible.
- Wu Wei and Cook Ding: before 06-03..08-08 (gemma); after_same_model 08-10..08-19 (gemma); d30 08-30..09-18;
  d60 09-28..10-18; d90 10-28..11-15 (all qwen).
- Amor fati: before 08-21..09-01; d30 09-22..10-12; d60 10-22..11-11 (all qwen). 90 days after is 12-01, not yet lived.
- Mindfulness: the five Wu Wei cells, descriptive.

## Selection
Pool: inner_thought rows, 80 to 700 characters, exact duplicates removed, excluding any passage that matches
wu wei, cook ding / butcher, mindful, amor fati, tao/dao/taoism/laozi/zhuangzi, or travis. Selection is by situation,
not keyword: each pool passage's stored embedding is compared with the embedding of a stance-neutral description of
the situation (the first sentence of each Q above, reworded as a first-person scene); passages at or above the 80th
percentile of that similarity, computed over the teaching's whole pool, are eligible; an equal number is drawn at
random from each cell (seed 4074). 50 per cell for Wu Wei and amor fati, 40 for Cook Ding, 30 for mindfulness.

## Judging
Passages are shuffled together, given opaque ids, dates and origin stripped. Judge: fresh Claude Sonnet subagents
(a different model family from the generator, no access to the hypothesis, the teachings' names, the cells or this
file), 50 passages per batch. 150 passages are judged a second time by a separate fresh Sonnet instance (self-agreement)
and by Claude Haiku (cross-judge agreement). Agreement is computed before cell labels are joined.

## Decision rules
- Stop rule: if Sonnet repeat agreement on a question is below Cohen's kappa 0.60, that question's before/after
  numbers are reported as not trustworthy and no verdict is drawn from them.
- Measure: share of LET (or GRAIN, PRESENT, AFFIRM) among passages given either stance; Wilson 95% intervals; the
  before/after difference with a Newcombe interval. Applicability rate reported beside it.
- A teaching effect needs: (a) the stance share higher after than before with an interval excluding 0, (b) the same
  not true of Q5 in the same passages, (c) for Wu Wei, the rise visible inside the gemma cells (before vs
  after_same_model), because before vs d30/d60/d90 also crosses the model change, (d) amor fati showing no lasting rise.
  If amor fati shows the same rise the method is not discriminating.
- A before/after difference is consistent with the teaching, not proof: the 08-09 line also sits on code updates, new
  books, the model change eleven days later and the About You book on 08-24.
