# Task-Constraint Effector — built v1 + spec for the rest
*2026-06-10 · Phase: Error Separation, slice 2 · companion to `docs/error_pathway_charter.md`*

## Why this exists (one paragraph)
The conflict-trace's first live session (2026-06-10) proved the execution gap: dissonance named
Du's failure verbatim ("Describing methodology vs. providing the solution") with zero authority;
the Critic — the only output veto — stands down on direct requests, i.e. on exactly the task
cycles. Every truth signal ran post-emission. The architecture could notice and could not act.
This effector is the first organ empowered to act, deliberately built as the *smallest credible
veto*: deterministic jurisdiction, one bind-don't-slam retry, fail-open everywhere.

## v1 — BUILT (live at next restart)
| piece | file | behaviour |
|---|---|---|
| Constraint extractor | `core/task_constraints.py` `extract()` | v1 jurisdiction: (a) digit-arithmetic the input asks to compute (verbal ops normalised: "9 times 3", "(17 minus 8) times 3"); (b) explicit "at least N words". Anything else → None (silence, not guessing). |
| Deterministic check | `check()` | arithmetic: expected value (safe-AST eval, no `eval()`) present in output as digits **or** English words 0–999 ("twenty-seven"); min-words: 0.85 tolerance. |
| The veto | orchestrator, post-Voice pre-return | on unmet: ONE Voice retry with the constraint **named** (`state.task_constraint_note` → Voice prompt) and room to show working — never the answer handed over, never terse-forcing (terse-forcing is what broke bare-qwen arithmetic). Runs in direct mode by design (that's when the Critic stands down). Fail-open try/except throughout. |
| Honest record | `error_pathway.record("task_constraint_unmet", …)` | constraint still unmet after retry → firewalled error record (charter-admissible deterministic evidence). Never a tension. |
| Measurement | `conflict_trace` signal `task_constraints` | ground-truth probe #2; `ground_truth_acted=True` only when the retry ran AND repaired it — the number this programme exists to move off zero. |

Also built in the same slice (separate organs, same firewall):
- **Human-correction capture** — `error_pathway.detect_human_correction()` (narrow patterns from
  the founder's real correction language; "push back"/stance-teaching/praise verified non-firing)
  → firewalled error record + `state.human_correction_kind`.
- **Consolidation axis-gate** — `ConsolidationNode` quarantines the batch's `wisdom_extracted`
  when a correction/fail-call (or final Critic rejection) cycle is in the batch. Stops the
  observed laundering ("that is a fail overall" → "integration of opposites is not a failure but
  a step towards wholeness" minted to semantic memory within the minute). Episodic record of the
  exchange is untouched — what happened is remembered; the failure becoming doctrine is gated.

## v2+ — SPEC ONLY (build when evidence demands, smallest slice first)
1. **Word-number arithmetic** ("nine times three", "divide … into eight parts"): needs a
   words→int parser for the *input* side. The output side already accepts word forms. Moderate
   value — the founder mostly uses digits.
2. **"Include X" constraints** ("include at least 1 piece of arithmetic"): presence-of-category,
   not presence-of-string — deterministic proxy: does the output contain any digit-expression
   with an operator? Jurisdiction guard: only when the demand is *explicit* ("include/contain/
   must have"). This was the actual miller-story failure class; highest-value v2 item.
3. **Sequence/puzzle tasks** ([3,2,5,1,4] etc.): NOT deterministic from the input alone — out of
   jurisdiction until a task-specific ground truth exists. Do not stretch the regexes to fake it.
4. **Arch-checker pre-emission move** (the original effector plan): same veto pattern — on a
   detected fabrication, one retry with "name only faculties that actually exist, or say you do
   not know". Deferred because today's evidence redirected priority to task non-execution; build
   after the constraint effector proves the retry mechanic in the wild.
5. **Competence feed**: every constraint outcome (met / met-after-retry / unmet) is exactly the
   "external accuracy" event `core/competence.py` Phase 0 wants. Wire as observe-only events;
   later this becomes the vetted record the Self-Efficacy Court can admit.
6. **Pattern Reflection tier** (founder's two-tier design): N error records → a *behavioural*
   tendency in DOING-language ("I tend to describe the method instead of executing it"), routed
   to competence — never to self-concept. Needs a record corpus first; the capture built today
   starts filling it.

## Success criteria (falsifiable)
- Conflict-trace `ground_truth_acted` moves off zero in live sessions (THE flip).
- Founder fail-call rate on explicit-constraint tasks drops (he stops having to say "you have
  not done the task" for arithmetic/word-count asks).
- Zero retry loops on out-of-jurisdiction inputs (the effector stays silent off its turf).
- Consolidation: no semantic "understanding" minted from a correction cycle (grep the fragment
  store against error_records timestamps).

## Failure modes to watch
- **False constraint extraction** → pointless retries, latency. Mitigation: compute-intent gate +
  jurisdiction silence; watch `[constraint] UNMET` lines for nonsense.
- **The retry answer is wrong twice** → recorded honestly, output still ships (no infinite loop,
  no suppression). This is correct: the effector's job is authority, not omniscience.
- **Quarantine over-firing** → legitimate insight suppressed on correction-heavy days. The
  correction detector is precision-tuned (verified against real negatives); if founder teaching
  style changes, re-verify the patterns.
