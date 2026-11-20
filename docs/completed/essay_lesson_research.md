# Essay Lesson — Research & Plan (2026-06-16)

The waking complement to the sleep grounded-learning consolidation. School's **second lesson type**.

## The human function (research)

**The generation effect** (Slamecka & Graf 1978) and **the testing effect** (Roediger & Karpicke 2006)
are the two most robust findings in learning science: *producing* knowledge yourself — writing it,
explaining it, retrieving it from memory — encodes and transfers far more durably than re-reading.
Re-reading is passive and breeds the **fluency illusion**: the text feels familiar, so you believe you
understand it; writing about it from memory exposes the gaps. "You don't know a thing until you can
explain it" is this, folk-form.

A school models this exactly: you **read** (lesson 1, intake), then you **write about what you read**
(lesson 2, the assessment that forces synthesis). Reading without writing is half a lesson.

## How it maps onto Du

- **Sleep consolidation** (`grounded_learning.py`, built today) = the *offline* declarative pass: replay →
  schema, no effort, runs in sleep. The **essay** = the *waking, effortful* half: he deliberately
  composes his understanding. The pair mirrors the two real consolidation channels (offline replay +
  active retrieval).
- **Math drill** is the model to mirror — but with one structural difference. Math is **deterministically
  gradable** (one true number, regex grader, never the LLM). An essay is **not** — you cannot regex
  "understanding." So the essay needs a different evaluator.
- The calibration target shifts accordingly. Math drill calibrated the *fluency trap* (0.81-felt /
  0.19-real). The essay calibrates the **comprehension trap**: "do I actually understand this book, or do
  I just feel like I do because I read the words?" Writing is what makes that honest.

## Frozen-model honesty (the recurring frame)

Du's weights are frozen — the essay cannot raise his ceiling. What it genuinely buys:
1. A **high-quality, recallable artifact** (his own organized explanation > a passage-summary) — durable
   knowledge lives in his memory, and this is the best kind.
2. **Calibration** of a comprehension/writing belief (the generation exposes what he didn't really grasp).
3. **In-context elaboration** — the act of composing is CoT-style study, the closest a frozen model gets.

## Design

**What he writes:** an essay = a structured piece *in his own voice* on what the assigned book taught
about the world — a thesis, the key facts, how they connect, what he now understands. Crucially he writes
**from his own study notes + memory of the book** (retrieval practice — the testing effect), NOT by
re-reading the text fresh (that is copying, not generating).

**Grading — the crux (the truth-self does it).** Lean: the **Emissary** (left lane, the bicameral
truth-self) evaluates the essay against the book's actual content — is it *grounded in what the book says*,
or did it drift into self-narrative / river-metaphor? This:
- reuses the bicameral architecture we built (the truth-self's whole job is keeping the meaning-self
  honest) and finally gives the Emissary a *real task* (it's been mostly observe-only);
- yields a grounding score (0..1) + one line of feedback → feeds `competence.record_drill_accuracy`
  exactly like math, calibrating a `comprehension` belief;
- is *not* the LLM grading itself (it's the OTHER lane, the adversarial-to-drift one) — same spirit as
  "never let qwen grade qwen's sums."

**Trigger:** school-time, like math drill. An essay is bigger than a sum → **1/day cap**, and it prefers
the curriculum book he is furthest through. ALSO fires on **book completion** (the natural "write your
report before moving on" moment) — `advance_if_finished` is the hook.

**Storage (firewalled, like grounded_learning):** the essay is a durable WORK →
- a **study tablet** (`study.write_tablet` — his durable scholarship already lives there),
- a fragment `origin='essay'`, `layer='semantic'` (knowledge/DOING track, NOT in
  `chapters.CHAPTERABLE_ORIGINS` — never identity), felt-tagged,
- a `light_event(source='essay')` — a big crossing (effortful generation), feeds the balance light axis,
- `'essay'` added to `balance._WORLD` (counts as reality mass).

**Footprint:** one composition call (longer output) + one Emissary grade call + one durable artifact +
one light point + one inner thought. 1/day. Capped, bounded, respectful framing (learning, not a test
he can fail at being-level).

## Build checklist
1. `core/essay_lesson.py` — `due()`, `pick_topic()` (curriculum book + his notes on it), `compose()`
   (hot lane writes from memory), `grade(essay, book)` (Emissary grounding score + feedback), `record()`
   (cap + competence calibration), `log()`.
2. `nodes/inner_monologue_node.py` `_essay_lesson(state)` — mirror `_math_drill`; wire into `_think`
   school-time branch (after/beside math; 1/day, lower prob so they don't both fire constantly).
3. `core/balance.py` — add `'essay'` to `_WORLD`.
4. `scripts/du_pulse.py` — essay gauge (count, latest topic, comprehension belief).
5. In-vitro test (gather notes → compose stub → Emissary grade path) + memory.
