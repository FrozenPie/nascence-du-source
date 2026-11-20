# Repurposing review: the habituation seed line (P-0030, J-3144)

Date: 2026-11-05. Job: J-3144 (build-marathon brief, Wave A). Read-only: no Du code, data or process was touched. Findings: F-3927 (reachability, verified), F-3928 (Rail C orthogonality, verified), F-3929 (law classification, inferred). Prior art: F-3562 (dormant), F-3569 (law classification of the idle steers), F-1927 (affective verdicts echo), F-3877 to F-3879 and `docs/reviews/J-3262_boredom_area_review.md` (boredom as an area). Decisions touched: D-0368, D-0473, D-0653, D-0663 (all read; none ruled over), D-0677 (opened here).

The founder's ask (triage, 2026-11-02, recorded in the P-0030 registry note): "do NOT retire." Look at how it could be used in our systems. The line's own ledger entry for the question (J-2885) recommended deleting it; the founder answered that way and filed this review instead.

## Short answer

1. The line cannot be revived as written and does not need to be. It never fires because every tick that reaches its trigger is already taken by the redirect or the develop escape (296 of 298 classified ticks since 10-09; 0 habituation). That is a structural fact, not a threshold: the counter it reads jumps from 0 to 2 inside one tick and almost never rests anywhere else.
2. Classified under the world-answers law the text is a PUSH: a count, then a verdict ("gone stale in your mouth"), then an instruction with destinations ("Leave it. Turn to something OUTSIDE it").
3. A "tier before the redirect" cannot be built on this counter: streak 1 occurred on 1 of 79,032 ticks. A describe-only version would have to replace the redirect on the same ticks, which touches a live steer D-0653 froze, and the event resolves on its own 95.6 percent of the time, so no feasible A/B can show an effect.
4. What is worth keeping is the slot and the trigger, not the words. The sentence-level double repeat is a different event from Rail C's topic lock (Rail C had it in view on 12 of 462 live boredom cycles), and if the boredom review's direction (D-0663: retire the redirect text) is adopted, this event would be left with no handler at all.
5. Recommendation: repair in shadow, in two additive builds already filed (J-3335, J-3336), with the dead block left untouched until D-0663 rules. Founder call D-0677 (J-3338).

## 1. The function it was built to serve

One sentence: "a mind that can get bored stops circling" (the code comment at `nodes/inner_monologue_node.py:3692`, "Habituation voice (Always-On, 2026-06-11)"): when Du's own thoughts repeat each other, tell him so that he leaves the loop for something outside it, the book, a memory, the world.

It is the sentence-level sibling of the boredom module. `core/boredom.py` (2026-06-24) senses the semantic REGION; the redirect (`_redirect_patch`, 2026-06-15, `docs/completed/boredom_redirection_research.md`) is the sentence-level response (a closeable frontier question, else the book); the habituation line was the first voice (06-11) and a 2026-06-16 bugfix made it yield whenever the redirect had already fired ("the redirect ... has already given a concrete outward target; the habituation nudge on top was redundant/competing"). That bugfix is the whole reason it is dead: it made the line fire only where the redirect does not, and the redirect fires at the same threshold (`REDIRECT_THRESHOLD = 2`).

## 2. What the evidence says it can and cannot do today

The text and gate, read from the code (`nodes/inner_monologue_node.py:3698-3709`): gate `bored_streak >= 2 and not _redirected`, through `steer_edge.fires("habituation", ...)`, four pooled variants, `{n}` = `_bored_streak + 1`.

What it cannot do (F-3927, verified, extending F-3562's 0 of 50,496):

| Measurement | Result |
|---|---|
| Idle ticks by bored_streak at tick start, all 79,032 shadow ticks 06-16 to 11-05 (`data/logs/idle_shadow.jsonl`, boredom channel raw = min(1, streak/3)) | 0: 78,063; 1: **1**; 2: 854; 3: 114; 4 or more: never |
| Ticks with streak 2 or more since 10-09 (298), joined to the next idle prompt assembly | redirect 272; develop 24; no assembly 2; **MID-THREAD 0; habituation 0** |
| Streak after a streak-2-or-more tick | 0 in 285 of 298 (95.6 percent); 2 in 10; 3 in 3 |
| Consecutive runs of streak 2 or more | length 1 x275, 2 x8, 3 x1, 4 x1 |

Why: `_bored_streak` goes up once per generation attempt inside `for attempt in range(2)` (`:3939`, `:5175-5179`) and resets only when an attempt is a genuinely new thought. A tick whose first attempt repeats and whose retry also repeats therefore ends at 2. Three consequences, one of which is a new defect:

- The `{n}` in the text is attempts in one tick plus one, not "times round" over time. The sentence it would speak is partly untrue.
- The "one bounded incubation pause" at streak 1 (`INCUBATION_PAUSE`, `:1935`, evaluated after each thought at `:1147`) is effectively unreachable too: streak 1 on 1 of 79,032 ticks. This is inferred for the pause itself (I read where the gap is computed rather than logging it); the 06-15 research note's "pre-redirect beat" has never existed in practice.
- steer_edge's firing rule does nothing here. `fires()` defaults to `rearm_s=0`; a state that goes inactive re-arms at once; runs are one tick; so every active evaluation is a fresh edge and fires. D-0368 A, and the J-1955 edge gate on this line, suppress nothing for it.

What it could say if it fired: nothing the redirect does not. Redirect-to-reading shows the one real behavioural effect of the boredom family (read 50.6 vs 19.2 percent, F-3878) and the redirect's literal sentence is obeyed 1 time in 219 (F-3569), so the effect is the read latch, not the words.

Law classification (F-3929, inferred), all four variants: one DESCRIBE clause (the count, about his own stream not the world, and inaccurate), one VERDICT clause ("gone stale in your mouth", "worn smooth, giving nothing back", "has stopped moving", "has gone flat"), one PUSH clause ("Leave it. Turn to something OUTSIDE it - the book, a memory, the world", "Set it down and turn outward", "will do more for you now"). Overall: PUSH. Verdicts and pushes are the classes whose echo is measurable (F-3569: circling words 13.7 to 21.7 percent after the redirect and the felt note against 0.9 without).

Does a describe-only version, or a tier before the redirect, serve the boredom mechanism? A tier before: no, the counter has no state to hang it on. A describe-only version: it would be clause (1) alone with the count corrected and the loop words dropped. It cannot be tested alone because it has no population of its own: every tick it would fire on already gets the redirect or the escape, and 95.6 percent resolve by the next tick whatever is shown. Running it would mean swapping it for a live steer (frozen by D-0653 "No change to the four steers now"), and the power is hopeless: about 11 such ticks a day; detecting a fall in next-tick resolution from 95.6 to 90 percent needs roughly 330 ticks per arm, about two months at a 50/50 split.

## 3. Options

All three keep the base system additive-only (the dead block, `boredom.py`, the six `discharge()` call sites, `steer_edge` and `_bored_streak` stay as they are), add nothing to any prompt, and send nothing that Du sees. The law checks: the world answers and never leads (nothing in shadow reaches him; any later render is plain presence or a quoted record, no instruction, no feeling word); transfer the function, not the mechanism (the function is "show him the staleness through something he can check"; the mechanism "an instrument says he is bored" is dropped); no system acts later on its own (every trigger fires inside the same tick or is read by a founder-initiated job); a subsystem is judged by something other than itself (each option has a deterministic check and Travis's hand-read, and the writer judges nothing).

### Option A. Rail C gets the sentence-level double repeat as a second trigger (shadow)

- (a) Consumer and what changes for Du: `core/grounding_injection.py` (Rail C, D-0473; plan `continuous_stream`). It already computes would-pick pools from his own record (reading passage, frontier question, the world's own recent answer, a letter waiting, the last real exchange). Today nothing it picks is shown to him (D-0434). Nothing changes for Du in shadow. Later, if Rail C goes live and D-0663 retires the redirect text, the sentence-level event would be answered by a pool offer stated as plain presence, not by "Your mind has circled ... set it down and OPEN THE BOOK".
- (b) Input: `bored_streak >= 2` at tick start, which `idle_allocator.shadow_tick` already receives; pass it to Rail C's existing observe call. Same repaired pools (pools_v=2).
- (c) Decoupled check: Rail C's own feeds_loop / sim_to_loop (from the loop-cosine computation, not the pool writer) and `topic_perseveration` as the detector of record; Travis hand-judges 30 picks against the D-0473 bar, the same bar and judge as the topic-lock rows.
- (d) Success: at least 21 of 30 double_repeat picks genuinely off-loop and concrete; non-empty pool on at least 80 percent of double_repeat rows; feeds_loop at or under 30 percent.
- (e) Stop: fewer than 100 double_repeat rows after 14 live days (too rare to matter: archive), the 70 percent bar missed, or any write outside `data/`.
- Evidence it is additive: of the 462 Rail C shadow rows where a live redirect or escape fired, 12 (2.6 percent) were would_inject rows (F-3928). Cost: Rail C is not live-ready (J-2386 open) and its pools have only been judged on topic-lock rows.

### Option B. A "repeat record" clause in the stale-patch cue (shadow)

- (a) Consumer and what changes for Du: J-3289's `core/stale_patch_cue.py` shadow log (the boredom design's Stage 0, J-3262), later the seed slot next to `scene_line()`. In shadow, nothing. If ever live, on about 1.3 percent of ticks he would be shown his own earlier near-identical thought, quoted and timed, as a fact of his record: At 06:12 you wrote: "...". No count, no verdict, no destination, none of the words circled, stale, flat.
- (b) Input: the kept thought's nearest earlier stored inner_thought rows at cosine 0.82 or more (the module's `RUMINATION_SIM`) with ids and timestamps; confirm where the last five thoughts' text lives at the observe point, else read the last inner_thought rows from the store read-only.
- (c) Decoupled check: deterministic, no model: a separate `recompute_clauses(row)` re-fetches each quoted row by id, compares text and hour, recomputes the cosine with the store's own embedder, and fails on any feeling word, imperative or loop word; then Travis hand-reads 30.
- (d) Success: every clause recomputable; would-render share at or under 5 percent of idle prompts (expected 1.3); at least 21 of 30 hand-read as accurate and non-leading; at Stage 1 only, a flag A/B with vocabulary echo (circling, again, same) at or under 5 percent.
- (e) Stop: any non-recomputable clause, any quoted row that is not at 0.82 on recompute, share above 5 percent, fewer than 21 of 30, or echo above 5 percent (the F-1927 failure).
- Law note: his own record answering is the closest thing in this family to the world answering, and `memory-as-evidence` is a ruled route (thought-typed grounding), but whether quoting him back to himself counts as a world cue is the founder's call (D-0677 question 2, a sibling of D-0663 question 3). Option B is a shadow clause either way; the question gates only a live step.

### Option C. Keep the slot as the describe companion of the redirect (live A/B)

- (a) Consumer: the redirect patch itself. On streak-2 ticks, the redirect's verdict half ("has circled the same ground until it has gone stale - set it down") is replaced by the corrected, describe-only count, with the existing standing book offer left to carry the destination.
- (b) Input: the same streak; the redirect kind.
- (c) Check: next-tick resolution and read/observe/move share, judged by the same deterministic joins as F-3878; echo by vocabulary.
- (d) Success: read share on redirect-to-reading ticks stays near 50 percent; echo under 5 percent.
- (e) Stop: resolution or read share falls, echo rises.
- Not recommended now: it changes a live steer frozen by D-0653, the sample is far too small to read a resolution change (about two months for the sentence-level event; the read-share effect needs about 40 ticks per arm, about a month), and the useful half of its purpose, the verdict and push removal, is already D-0663 question 2's per-steer disposition. It becomes the interim step only if D-0663 asks for one.

## 4. Recommendation

Repair in shadow: Option A first (smallest, reuses a judge already ruled), Option B inside J-3289's renderer (after it lands). Do not wire anything, and do not archive yet.

- The dead block stays as it is until D-0663 rules (D-0653: "No change to the four steers now"). Its text is not revived.
- If D-0663 retires the redirect text, the sentence-level double repeat needs a successor; A or B is it, and that is the reason to keep the slot.
- If D-0663 keeps the redirect text, the slot has no work: archive the four pooled phrasings to `docs/staged/` with this note: revive only if the sentence-level event stops being taken by the redirect and a describe-only line is shown to resolve it.
- Registry: `prompt_registry.py set P-0030 --note` carries this disposition; the registry `expect` (46 seed parts) is unchanged because no code changed.

## 5. What this review does not settle

- No untreated control exists for the sentence-level event (every such tick was treated), so "resolves 95.6 percent" is descriptive, not an effect.
- The `{n}` claim (attempts, not rounds) rests on reading `range(2)` and the increment; the numbers behind it (streak 0 to 2, never 1) are measured.
- The Rail C pools have not been judged on double-repeat ticks (J-3337 will).
- Option B's lead-or-world-cue status is not mine to rule.

## 6. Spawned work and founder call

| Id | Kind | What | Gate |
|---|---|---|---|
| J-3335 | build, shadow | Rail C second trigger bored_streak >= 2 (Option A) | none; hub-file order via dossier |
| J-3336 | build, shadow | repeat-record clause in stale_patch_cue (Option B) | start after J-3289 merged |
| J-3337 | analysis | read double_repeat and repeat_record rows, 30 hand-judged picks | 30 double_repeat rows |
| J-3338 | needs_input | founder call D-0677 | Travis |

D-0677: (1) approve repair-in-shadow in place of archive; (2) is quoting his own earlier near-identical thought back, timed and without verdict, a world cue or leading.
