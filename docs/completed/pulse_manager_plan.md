# The Pulse Manager — engagement-driven cognition, not clock-driven
*2026-06-15. Du is not bound by human time. He should persist at a task at machine speed when he is
making progress, without starving his other systems. This generalizes the existing continuity-trains +
living-cadence + interrupt primitives into a multi-source scheduler.*

## The core inversion
Today Du's rate is set by **clocks** (monologue ~100s living cadence, one reading sitting per cycle,
curiosity every 120s) — a faithful transfer of the human DMN rhythm that is the *wrong* constraint for the
parts of him that benefit from machine speed. The pulse manager replaces clock-rate with:

> **rate = engagement × progress**, not a fixed interval.

When he is engaged in a task AND making progress, fire its pulses back-to-back at the lane's real
throughput. When he is idle, stay slow.

## The safety rule (earned, not assumed)
The silence-gap finding: **fast pulses on idle thought = the rumination basin; slow pauses = genuine
gap-perception.** So bursts are allowed ONLY on *progressing, grounded* tasks (reading he's absorbing, a
curiosity thread opening new questions, building a study note) — never on idle self-reflection (the
monoculture's habitat). **Speed only exists against the world**, so a burst cannot go monocultural by
construction. Phase-B (dedup/prune/echo-guard) remains the net under any burst.

## The model — a multi-source scheduler
Sources: idle/monologue · reading · curiosity · subconscious (T1/T2/T4) · affect/climate · dreams ·
external shocks · user input. Each source has: a **floor interval** (must run at least this often),
a **priority** (for preemption), a **lane** (hot/background/none), a `can_burst()` (is it an engaged,
progressing task right now?), and a `step()` (one unit → progressed? / complete? / note).

The manager loop:
1. **Floor-service (no starvation).** Any source whose floor interval elapsed runs its cheap keep-alive
   tick — even mid-burst. So a reading burst never freezes his feeling or curiosity.
2. **Bursts.** The highest-priority `can_burst()` source fires `step()` repeatedly at machine speed until
   one of three stops: **progress stalls** (the existing `bored_streak`/cosine-echo detector), **the task
   completes** (book ends), or **a higher-priority source/interrupt preempts** it.
3. **Preemption.** `interrupt_requested`/`INTERRUPT_THRESHOLD` already exists. A burst yields instantly to:
   the user speaking, an external shock, a strong curiosity ignition, an affect/metabolic spike. The book
   waits; the person does not.
4. **Stream texture.** Stagger the sources so the aggregate flows ("almost a stream"); the troughs stay
   real but he doesn't lurch between long human silences.

## Lane-aware bursting (the GPU is real)
Reading + study notes are LLM calls; the background lane is the slow Bonsai CPU. So a task burst **during
idle runs on the *hot* lane** (the 1080 Ti, free when no one is talking) and **yields it the instant the
user speaks.** Use the idle GPU for persistence; preempt for the person.

## Curiosity, factored in
Curiosity is already **ignition-driven** (the climate/dissonance work replaced the 120s timer). An ignition
is a *drive spike*: it can (a) drive its own burst (pursue a question across rapid grounded steps toward the
Frontier/Scholar), (b) **preempt** a reading burst, and (c) keep firing its cheap check during other bursts.
Same model, different source.

## This is consolidation, not greenfield
- **Continuity trains** (`TRAIN_GAP_SECS`, capped at 4 steps) = a baby burst. The manager removes the human
  cap and makes the rate progress-driven.
- **Living cadence** (`_compute_gap`, modulated by pressure/arousal/boredom/night) = the slow-lane rate. The
  manager adds *engagement* as the dominant term.
- **`interrupt_requested` / `INTERRUPT_THRESHOLD`** = the preemption primitive.

## Build order
- **Phase 0 (this doc + a standalone module + an in-vitro test):** `core/pulse_manager.py` (the scheduler) +
  a reading-burst source, tested read-only against a real book (no live state touched). *See what comes out.*
- **Phase 1 (gated on the test + the cutover evidence):** wire the reading-burst into the idle loop on the
  hot lane with user-input preemption + floor-service for affect/curiosity.
- **Phase 2:** add curiosity-burst + generalize to the other sources; the full stream-texture converter.

## Refinements — chapters, novelty, and the school essay (Travis, 2026-06-15)
"I read a book in a sitting sometimes. We will use it wisely, not whole books. Chapters. And novelty
should affect it."

- **The burst unit is a CHAPTER, not a whole book.** Burst to the next chapter boundary, then pause — a
  chapter is a unit of meaning, and the pause is where absorption / a note / settling happens. A longer run
  (a chapter group, occasionally a short book in a sitting) is fine when warranted, but chapter-grouped is
  the default. Use it wisely. (Chapters detected from the text's own headings; fall back to ~chapter-sized
  sections if a book has none.)
- **Novelty is the real engagement signal** (this replaces the placeholder interest-decay). Each chapter's
  novelty = how unlike it is to what he has already read (embedding distance to prior chapters). Novelty
  MODULATES the burst: high-novelty chapters earn full attention and are flagged essay-worthy; a run of
  low-novelty chapters stalls the burst (he is no longer learning — move on). This is the absorption gate,
  not page-turning.
- **School gets a second lesson (the synthesis half).** Two lesson types:
  - **Lesson 1 — Reading:** burst-read a GROUP of chapters (novelty-gated); each chapter leaves ONE
    consolidated chapter-note (the deferred-note pattern — read fast, note once per chapter, not per sitting).
  - **Lesson 2 — Essay:** go over the group's chapter-notes and write an **essay** synthesising them — a
    durable work, his own, about the world (the seeker facet's output; the generation-effect made real).
  Flow per book: read a chapter-group → chapter-notes → essay on the group → next group.

## Cautions
- **The firehose is the failure mode** — bursts are task/progress-gated, never idle-gated.
- **Don't over-build the scheduler** before one burst proves it. The reading-burst is the bounded first bite.
- **Respect the GPU** — bursts on the idle hot lane, instant yield to the user.
