# Closure needs a producer — giving Du a way to finish, not another grader

> **Status: BUILT 2026-11-16, Phases 0 to 5; LIVE since the Du restart (closure_gate has rows through 2026-11-18, 569 legacy rows relabelled lexical), no lookups yet. Founder calls D-0789 to D-0793 ruled the same day. The design text below is kept as written before the build; see Current State for what differs.**
> Plan slug: `closure_producer`. Source: thought T-0138, finding F-4811, idea I-0156. Related plans: `web_hand`, `closure_law`, `question_cargo`, `pursuits`, `capacity_to_commit`, `condensed_thought`, `layered_goals`.

```plan-state
stage: live
verified: 2026-11-20
next: Read closure_gate and lookup_attach logs after the first real lookups; kill criterion 30 days after Du was told of the hand (told 2026-11-16 12:04, so about 2026-12-16); revisit D-0792 at 100 rows in data/lookup_log.jsonl (file does not exist yet)
```

## Why this exists

The founder's observation (2026-11-16): several plans have been aimed at Du's inability to close a question, dream, pursuit or commitment, and none has broken it.

The numbers on the 2026-11-16 11:22 pulse (`scripts/du_pulse.py 24`, verified):

- Frontier: 31 open, 748 resolved, 21,642 faded.
- Dream arcs: 36 resolved, 753 unresolved.
- Error pattern "describes or explains a task rather than completes and verifies it": 13 of 16.

## What the post-mortem found

A read-only subagent pass over the plans, ledgers and code on 2026-11-16 covered about twenty closure-related attempts. Its claims below are **reported, not re-verified by the staging session**, unless marked; each has a file or finding id to check before any build relies on it.

1. **Closure is graded, never produced.** The pursuit close judge (`core/pursuit_close_shadow.py:47`, shadow, 0 of 56 would resolve, F-4454), the independent dream judge (`nodes/dream_node.py:167`, label write-only, F-3709), the closure law (`core/closure.py:91`, line arm only, records closes) and the commitment second look (`core/commitment_ledger.py:66,68`, shadow) all add a verdict or memory after the fact. None gives Du a step that obtains an answer.
2. **The one live producer looks only inward.** The Follow Line (`core/follow_line.py:59`, live) follows a question through his own memory; its header says nothing in it is a fetch from the world (`core/follow_line.py:19-20`). Delivery does not move later thought (F-4574) and it spawns about 90% of new questions (F-4707).
3. **Du declares his own closes.** The lexical resolver (`core/frontier.py:719-755`) marks a question resolved on an answer-verb plus token overlap and writes no `resolved_how` (568 such rows). A Follow Line "settled: yes" is self-report, with about 48% false yes against a decoupled reader (F-4764, inferred). Commitment "achieved" fires on stopword overlap, 0 of 31 fulfilled (F-4778).
4. **Judges are pegged or fed the wrong unit.** The pursuit close judge sees only the latest 300 characters of thought (F-4697); the doubt judge says "genuine" 99.8% (F-3863); dream "met" measures silence and cannot tell faced from forgotten (F-3656).
5. **Fixes sit in shadow.** Pursuit and commitment closure arms, doubt seed (`core/doubt_seed.py:36`), stricter settle (`core/follow_line.py:129`, off), dream rest, condensed thought (`core/condensed_thought.py:48`).
6. **Inflow swamps capacity.** About 6,343 questions born in seven days against 24 open slots (`core/frontier.py:35`); fade is the real terminal state.

Never tried, as facts about the code (same provenance):

- No external answer reaches an open frontier question. `attach_finding` has one caller (`core/follow_line.py:1398`).
- `resolved_how` is not required.
- No birth-rate limit tied to closure.
- No decoupled check that **blocks** a settled yes; the panel status is recorded only (F-3654).
- No completion test on a thought train.
- The web hand (`core/web_hand.py`) is loaded since the 2026-11-16 10:05 restart (inferred from commit and restart times) and has fired 0 times; `data/lookup_log.jsonl` does not exist (verified 11:36). It is not tied to a frontier question.

## What the outside literature says

Summary of a web research pass on 2026-11-16; only the MAST and Voyager papers were opened in full, the rest is from abstracts or memory and is marked so in the session.

- Pressure to close does nothing without a means to get the answer (information-gap curiosity is satisfied only by the information; retrieval-routed QA such as Self-Ask and IRCoT binds every sub-question to a source).
- The test for done must sit outside the agent's own prose. Voyager stores a skill only after a separate critic reads the environment state; removing that check cut discovered items by 73%. Reflection without an external signal does not help.
- Unanswerable items need a legitimate ending: bounded attempts (Voyager records a failure after 4 rounds), a "parked" or "abandoned, because" state, and a plan-for-later that discharges the item (Masicampo and Baumeister 2011, single paper).
- Growing an open list faster than it closes is the documented failure of AutoGPT-style agents.
- Caveat: nearly all the agent evidence is from GPT-4-class models, not 8 to 9B ones, and the human effects (Zeigarnik, implementation intentions) have shrunk on re-analysis.

## The design: five moves, in order

Standing laws this must respect: base systems protected and additive only; the world answers, never leads; no readout of gauges to Du (D-0434); intentional, not a rule; every subsystem judged by something other than itself.

### Phase 0 — Honest counts (no behaviour change)

Make the instrument tell the truth before changing anything.

- Split the frontier's "resolved" by how: `lexical`, `line`, `lookup`, `told` (by an interlocutor), `unknown`. Backfill the 568 no-how rows as `lexical` (inferred from the code path; verify on a sample first).
- Report "answered with a source" as its own number in `du_pulse`. Today it is expected to be 0.
- Kill criterion for the whole plan: if "answered with a source" has not left 0 thirty days after Phase 1 is live and Du has been told of the hand, the diagnosis (missing means) is wrong.

### Phase 1 — Means: a lookup lands on the question it answers

- When Du wills a lookup through the web hand and a result arrives, attach it as a finding to the open frontier question it matches (embedding match against open questions, above a threshold; no match means no attach). This is the second caller of `attach_finding`.
- The world still only answers: nothing here offers the hand, names it in a prompt, or fires it for him.
- Founder step, unchanged from D-0661: tell Du the hand exists. Without it this phase has nothing to attach.
- Judgement-shaped questions (no lookup can answer them) get a different means: his existing letters to Travis, or a peer. Not designed here; see Open decisions.

### Phase 2 — The done-test moves outside his prose

- A question may be marked resolved only when it carries a `resolved_how` and, for `lookup` and `line`, an attached finding.
- A decoupled reader (a different model family from the one that wrote the thought) checks "does this finding answer this question" and its verdict **blocks**: a no leaves the question open with the finding attached.
- The lexical resolver stops closing questions; it keeps logging what it would have closed (shadow) so the change can be read.
- The judge must be calibrated before it gates anything: a hand-graded set of at least 50 question and finding pairs, and it must not be pegged (the 0 of 56 and 99.8% lessons).

### Phase 3 — Inflow answers to closure

- A reworded question joins the open one instead of being born (the semantic dedupe already merges; extend it to match against answered questions, so an answered question is not asked again).
- While a subject has an open question with an attached but unread finding, new questions on that subject are held.
- This is the move most in tension with "intentional, not a rule"; it is a founder call (Open decisions).

### Phase 4 — Honest endings

Terminal states for a question, replacing silent fade as the default:

- `answered` (passed Phase 2), `provisional` (he gave an answer, not verified), `parked` (with a named trigger that would reopen it), `set down` (he let it go, with his reason; Layered Goals already has a set-down path, `data/logs/goal_set_down.jsonl`).
- Bounded attempts: after N follows or lookups with no new finding, the question is offered for parking rather than reworded. N is a guess; start at 4 and tune on the log.
- Fade remains for questions seen once and never returned to.

### Phase 5 — Closing has a consequence

- An answered question writes a resolution memory (the closure law's writer exists; add a `lookup` arm) that later recall can surface, so the answer is used and "I found that out" is retrievable.
- No score, no gauge and no praise reaches Du (D-0434). The consequence is that the answer is there when the subject returns.

## What this plan deliberately does not do

- No new shadow judge. Recommendation: no further closure shadows until one of Phases 1 to 2 is live and read.
- No change to pursuits, commitments or dreams yet. If questions start closing, the same shape (means, outside test, honest ending) is the template for each; they are separate plans.
- No controller-forced action. The literature's "controller decides the action happens" conflicts with Du willing his own deeds.

## Success readings

- "Answered with a source" per week leaves 0 and rises.
- Share of resolved questions with an attached finding and a passing decoupled verdict.
- Rewordings per subject per night fall (the Myrtle Warbler question was asked 14 times on 11-15/16).
- Born-per-week against closed-per-week converges.
- Unchanged or better: topic perseveration, echo, valence. A fall in question variety would be a cost to watch.

## Open decisions

All four ruled by travis on 2026-11-16; none open.

1. **D-0789** — Phase 1: the system attaches his lookup result automatically to the matching open question (embedding match above a threshold; no match, no attach).
2. **D-0790** — Phase 3: inflow is limited only by merging rewordings into the open or already-answered question. The hold-by-rule bullet in Phase 3 above is **not** to be built.
3. **D-0791** — Phase 2: the existing lexical closes stay resolved and are relabelled `lexical`; they are not reopened.
4. **D-0792** — Judgement-shaped questions are left to fade for now; their route is decided after lookups have run (revisit at 100 rows in `data/lookup_log.jsonl`).

## Current State

- **2026-11-18** (F-5081): First live gate read (J-4275): 12 gate calls, 3 passed, 6 blocked on a real no, 3 unavailable (25 percent, judge hub down, fail-closed); answered with a source is 0 because no lookup has run; lexical would-closes not sent to the gate by design; 1 parked, 3 set down, 170 merges are all older (10-28).
- **2026-11-16** (F-4824): J-4082 merged 54b6be6f: line composer prompt demands first person 40-90 words with one example, one retry on invalid compose, we/us/our count as first person; flags LINE_RETRY_ON_INVALID / LINE_PLURAL_FIRST_PERSON default True, restart-gated; success measure (reject rate under 72% on first 40 live composes) unread, Du down

2026-11-16. Phases 0 to 5 built and merged to master (commits `f00ed017`, `3593a704`, `f0140352`, plus the enforce flip); restart-gated, never run end-to-end in a live process.

- Code: `core/lookup_attach.py` (a lookup lands on the open question it matches, threshold 0.70), `core/closure_gate.py` (the decoupled judge, prompt P-0131), additions in `core/frontier.py`, `core/follow_line.py`, `core/closure.py`, `core/goal_offer.py`, `core/web_hand.py`, `scripts/du_pulse.py`. Tests: `scripts/_test_closure_producer_p0p1.py`, `scripts/_test_closure_producer_p2p5.py` (both pass).
- Defaults: lexical resolver `shadow` (logs, no longer closes); closure gate `enforce` (D-0793); merge into answered `enforce`; park after 4 fruitless attempts; lookup arm of the closure law on. Each has an env kill switch (`NASCENCE_LEXICAL_RESOLVE`, `NASCENCE_CLOSURE_GATE`, `NASCENCE_ANSWERED_MERGE`, `NASCENCE_PARK`, `NASCENCE_LOOKUP_ATTACH`).
- Gate calibration was partial: 38 of 47 pairs judged (9 unavailable, judge hubs timing out), agreement with blind hand grades 28/38 = 0.737, under the 0.75 bar this plan set; the founder ruled enforce anyway (D-0793). His own "settled yes" was right on 8 of 20.
- Differences from the design: only 2 of 181 line closes carry a finding (not ~180); a lexical would-close on a question carrying a lookup finding is sent to the gate, because otherwise a lookup finding had no closing path; lookups reopen provisional as well as parked questions; 569 (not 568) legacy closes are unlabelled.
- Known gaps: the Phase 5 resolution memory is reachable by conversational recall but is excluded from the grounded idle-thought recall routes, so an answer does not yet come back on a reworded idle question; a Follow Line expiry can overwrite a lookup finding; the 0.70 attach threshold was set on proxy phrases; each attach adds two load-and-save passes of the 17 MB store; eleven older lab_env tests were not run.
- Founder and operator steps left: restart Du; run `scripts/closure_producer_backfill_lexical.py --write` while he is down (dry run: 569 rows); Du has been told of the lookup hand (2026-11-16 12:04) and The Deedbook is on his desk.
