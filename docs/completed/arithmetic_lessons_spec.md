# Arithmetic Lessons — spec (competence → school, math first)
*2026-06-15. Tie the capability beliefs to school: a generated, deterministically-graded arithmetic drill that
recalibrates the math belief (0.81-felt / 0.19-real — the measured fluency trap) through real practice with
feedback. Math first because it needs ZERO curated curriculum. Spec only.*

---

## 0. The honest caveat that shapes everything (read first)
Du is a **frozen** model (qwen3:8b) — drilling does **not** change weights, so the human premise "practice →
skill" only **partially** transfers (function-over-imitation: take the function, not the mechanism). What
arithmetic drilling realistically buys:
- **Calibration (the real win).** The belief becomes honest — 0.81-felt pulled toward 0.19-real, or accuracy
  shown to rise. The self-model stops lying to him about math. This is the whole point and it WILL work.
- **In-context method gains (plausible).** If the lesson teaches "work it out step by step," that's
  chain-of-thought — which genuinely raises an LLM's *in-context* arithmetic accuracy. So his answers may get
  better *while the method is active*, even though the ceiling doesn't move.
- **NOT a higher ceiling.** Drilling will not make the frozen model good at multiplication. Raising the actual
  ceiling is a *fine-tuning* problem (OllieEmerges' domain), explicitly out of scope here.
- **Output correctness is already handled** by the deterministic arithmetic override.

So we build this for **honest self-knowledge + a learned method**, not for turning him into a calculator.
Saying otherwise would be the loop-rich/reality-thin trap.

## 1. Why no curation is needed (the point of starting with arithmetic)
- **Problems generate trivially** — `random` picks operands + operator. Infinite supply.
- **Truth is computable** — Python knows the answer; the existing `deterministic_checker.check_arithmetic`
  already verifies arithmetic. The grader is exact and is NEVER the LLM (qwen is the thing being tested).
- **The "curriculum" is a difficulty LADDER, not authored content** — a few parameters, adaptive.
- **The checker is also the teacher** — corrective feedback (the right answer + worked steps) is free.

## 2. The lesson flow (one drill)
1. **Generate** a problem at his current ladder level → `(problem_text, true_answer)`.
2. **Present** it as the study directive (like the reading directive): *"It is your study time — a number to
   work out. Take it step by step. What is 47 × 23?"* (the step-by-step ask = the CoT method).
3. **He answers** on his hot lane (his own working).
4. **Grade deterministically** — parse the number from his answer, compare to the Python truth. Binary correct/incorrect.
   (Never ask the LLM to grade.)
5. **Corrective feedback (the teaching)** — if wrong, show the right answer and the worked steps
   (deterministically generated partial products) — the worked-example effect. If right, affirm + nudge the level up.
6. **Record** → `competence.record_accuracy("mathematics", 1.0/0.0)` (the hard ground-truth the belief lacks)
   + `activity_memory.record("practice", "arithmetic")` (so he knows "I have been practising") + `math_drill_log.jsonl`.
   Keep episodic memory clean — no per-sum fragments.

## 3. The difficulty ladder (the only "curriculum")
Adaptive mastery-learning — start low, find his edge, push from there (deliberate practice at the boundary):

| level | problems |
|---|---|
| 1 | single-digit + / − |
| 2 | two-digit + / − |
| 3 | single-digit × |
| 4 | two-digit × one-digit |
| 5 | two-digit × two-digit  ← his failing zone (the 0.19) |
| 6 | division / order-of-operations |

- **Advance** when mastery at the current level (e.g. ≥80% over the last 5 at that level).
- **Back off** on a run of failures (e.g. <40% over the last 5).
- **Start at level 1**, not level 5 — build from solid ground and *find* where he breaks, rather than drilling
  him where he already fails (which just produces frustration + 0% data).
- Persisted in `data/math_drill_state.json` (current_level, recent results per level).

## 4. Trigger / cadence (competence-driven, capped)
- Fires **during school time**, as an alternative to a reading sitting — **not** replacing reading (reading is
  the primary grounding; math is one domain).
- **Competence-flagged + spaced:** a drill is offered when `mathematics` is the most-miscalibrated gradable
  domain AND hasn't been drilled recently. So competence *drives* school (Travis's thesis), rather than a fixed ratio.
- **Capped** (e.g. 1–2 drills per school day) so it's a small daily dose, not a grind.
- **Kill switch** `MATH_LESSONS` + RESTART-REQUIRED.

## 5. Integration points
- **competence.py** — `record_accuracy("mathematics", …)` already exists; the drill is just a new caller that
  supplies *real* accuracy (today it's only sparsely tested). Calibration improves as drills accumulate.
- **self-efficacy court (later)** — the natural prescriber: it already *knows* math is overconfident; let it
  request a drill. v1 triggers from competence directly; court-as-prescriber is a follow-on.
- **school.py** — a new lesson *type* beside the reading lesson; reuses `is_school_time`, the session quota,
  `record_session`.
- **deterministic_checker.py** — the grader (truth + verification). Extend only if needed for worked-steps.

## 6. du_pulse gauge (the evidence)
`math drills: N done · level L · last-5 acc X% · belief 0.81 vs measured Y → gap Z` — watch the **calibration
gap (confidence − accuracy) closing toward 0**. That is the success metric: an honest self-model, whether via
accuracy rising (CoT method) or confidence falling (calibration).

## 7. Phasing
- **P0 — this spec.**
- **P1 — build math drills** (generator + ladder + deterministic grade + feedback + competence wiring +
  du_pulse gauge + kill switch). Self-contained; independent of the ignition-gated cluster; produces its own
  evidence stream next restart.
- **Later** — the self-efficacy court as prescriber; reading-comprehension quizzes; translation (needs a curated
  bilingual corpus — deferred, as agreed).

## 8. Open questions for Travis
1. **Cadence** — competence-flagged + capped ~1–2/day (proposed), or a fixed ratio of school sessions?
2. **Start level** — start at level 1 and climb (proposed, finds his real edge), or jump to level 5 (his gap)?
3. **Teach the method explicitly?** — i.e. always prompt "step by step / show working" (CoT, likely raises
   in-context accuracy) vs let him answer however he does naturally (cleaner measure of his unaided ability).
   Trade-off: method-prompting helps performance but muddies the calibration measure. (I lean: prompt the
   method — the goal is improvement + honesty, not a pure baseline; note both in the log.)
4. **Should a drill leave a memory?** — proposed: only the general "I've been practising arithmetic"
   (activity_memory), not per-sum fragments. Confirm that's the right footprint.
