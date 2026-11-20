# What should the conversational T5 compile be? (J-3179, 2026-11-05)

> Status: research deliverable, read-only. No Du code, data store or process was touched. Plan: `docs/plans/t5_procedural.md`.
> Findings: F-3919 (who the compile learns from), F-3920 (the ladder never grades it), F-3921 (first-line parse and "human is not Travis"),
> F-3922 (no world grader for conversation), F-3923 (the approach text is not the attractor), F-3924 (the 2-day gate is a midnight crossing).
> Founder call: D-0676. Follow-up jobs: J-3328, J-3329, J-3330, J-3331, J-3332.

Founder, triage 2026-11-02, closing J-3014: "We probably need to do some research on what we do here."

## Recommendation (one line per question)

1. **What a skill is for:** world know-how graded by the world ("I can bank a fire, it held"). A conversational skill is only worth having if it is interactional know-how with Travis graded by Travis's next turn. What T5 compiles today is neither: it is a topic label distilled from Du's own self-asked questions.
2. **Rule to adopt:** none of the three candidate rules rescues the compile. Requiring 2 human turns gives about 2 skills in 75 days (both goodnight farewells); world-graded only gives 0 (no conversational turn has ever been world-graded); both gives 0.
3. **Control arm and judge:** a live with/without arm cannot be powered for conversation (about 1 recognition a week, about 150 pairs needed). Use the retrospective matched-pair arm that already exists in the logs (164 pairs, first read below shows no effect) judged by judge_panel families that are neither the writer nor the compile model (J-3328). For world procedures the world is the judge and a live arm is powerable (J-3331).
4. **Is "observe the environment" the attractor?** No, on this evidence. Du's answers moved toward environment imagery in the week of 08-20; the first approach saying so is 09-04; recognised answers do not differ from matched unrecognised ones. The approach is a photograph of the voice (F-3923, inferred from a lexicon proxy).
5. **Recommendation: retire the conversational compile and its recognition injection behind a kill-switch flag** (code kept, ledger rows archived not deleted), T5 = world procedures, with a pre-registered re-entry test. Not "require human turns" (same outcome as retiring with an extra parser fix to build first), not "keep with judge and control arm" (cannot be powered), not "redesign" (no mechanism exists to grade a conversational posture).

## 1. What the plan intended, and what a skill is FOR

The plan (`docs/plans/t5_procedural.md`, built 2026-08-22 after the audit `docs/reviews/t5_procedural_skills_2026-08-22.md`) says two things.

- **World procedures** (earned by doing) are the real procedural memory: every hand family, fieldcraft craft and study routine is a procedure keyed by its registry name, graded by the world's own answer ("the knot slips" is a refusal, a success on a later day after a failure is `held`). Zero LLM.
- **Conversational procedures** were to be kept but only "compiled from recurrence across at least 2 days and at least 2 sources (distinct conversations/peers), never from one thread; success-gated by competence's C-signal (no correction followed) and A-signal (bound coherently)", labelled by "the KIND of moment, never how it was received", and read only at rung `persisted`+. The plan's own kill clause: "if after two weeks no conversational skill reaches `persisted` under the new gates, the conversational half is retired (it never measured anything) and T5 = world procedures only."

What a skill is for in Du's life, put plainly: a procedural skill is know-how he has earned by repeated, graded practice that lets him act with less deliberation (a knot, a fire, a way of closing an evening). Two things make it more than a style note: it names something he can DO, and something other than himself has said it worked. The world supplies that for hands. For conversation the only possible grader is a person's next turn.

What the code does instead (all read in full, details in the findings):

| Plan text | Code | Effect |
|---|---|---|
| at least 2 days | `_day()` calendar dates (`procedures.py` 132, `admissible` 204-225) | a midnight crossing; median span of the 22 post-gate compiles is 14.3 h, 15 of 22 are 24 h or less, shortest 3.0 h (F-3924) |
| at least 2 sources = distinct conversations/peers | a source is any 30-minute gap between member timestamps | one afternoon of Du asking himself about one thing is "many sources" |
| success-gated by C-signal and A-signal | only the C-signal (next item is not a correction); A-signal never built | a chain of Du's own questions is always "landed" |
| rung climbs on evidence of use | `compiled()` credits every landed cluster member, `_climb` gives `persisted` at 2 days and 2 successes | every admitted skill is born `persisted`: 22 compiled events, 22 at `persisted`, 22 ledger rows, 0 failures, 0 held (F-3920) |
| kill if none reach `persisted` | none can fail to | the plan's own retirement test is unreachable as built |
| situation, not topic | the compile prompt asks for it; the cluster is a topic | post-gate skills: "Explaining 'mottainai' concept", "Explaining the effect of oil on light and shadows", "Bluebird's arrival in 渡 symbolizes personal growth" |

## 2. How many compile clusters qualify under each candidate rule

Method (read-only; `nascence.db` opened `mode=ro`; embeddings recomputed with the same `paraphrase-multilingual-MiniLM-L12-v2` CPU model): I replayed `_t5_check` and `_t5_compile` at the timestamp of each of the 77 `T5_procedural_skill` rows in `data/subconscious_log.jsonl`: material = lived Q/A with a `Q:` line in the 7 days before, newest 120, oldest-first, `mark_landed` rules, greedy 0.70 seed clustering, largest cluster. Each member was joined to `data/affect_log.jsonl` (timestamp within 3 s and question prefix) for `input_type` human or internal: 3,836 of 3,842 lived fragments matched. Replay check: the replayed size equals the logged `n_sources` exactly for 19 of 22 compiles after the gate; for the 55 earlier compiles (before the 08-22 22:56 gate the window was "since last compile") only 25 match exactly, so pre-gate human counts are approximate. Dates are NZ local (the "10-29" compiles of F-3717 are 10-30 01:23 and 05:40 local; the count is 77, F-3717 said 76, the 11-02 01:41 lamp-oil compile is new).

| Rule | All 77 | Pre-gate 55 | Post-gate 22 |
|---|---|---|---|
| Current gate (3 landed, 2 calendar days, 2 gap-sources, not evaluative) | 53 | 31 | 22 (by construction) |
| (a) at least 2 human-channel members | 15 | 14 | 1 |
| (a2) at least 2 human members on at least 2 days | 4 | 3 | 1 |
| (a3) a2 and at least 2 human sources | 1 | 0 | 1 |
| (b) world-graded only, strict (a conversational turn graded by a world answer through the ledger) | 0 | 0 | 0 |
| (c) a and a loose world proxy (cycle id next to a fired hand) | 0 | 0 | 0 |
| clusters with ZERO human members | 62 | 41 | 21 |
| clusters that are 100% human | 15 | 14 | 1 |

Reading it honestly:

- **The only post-gate "human" cluster is not Travis.** 08-29 "Banking the fire and rest reminder" (9 members over 5 days) is nine copies of the system-composed farewell (`run_nascence.py`: the house name, "it's time to bank the fire and rest for a while. Nothing's wrong..."), which enters on the human channel. 22 lived fragments carry that wording and 21 more carry a "stop for a while" sibling. `input_type == human` is not "Travis typed this", so rule (a) must also exclude system templates (core/orchestrator.py already gates founder canon on `state.founder_canon` for this reason, F-0796; T5 does not use it). Excluding them, post-gate human clusters: **0 of 22**.
- **The 100%-human clusters are 14 early-June ones (06-04..06-07) plus the farewell skill**, when almost every cycle was a human turn (1,212 human against 236 internal lived Q/A in June, 83 against 841 in September).
- **Recognition follows the same split.** Of 193 `procedural skill recognised` lines in `nascence.log`, 166 fired on internal cycles, 25 on human-channel cycles (12 on 06-05..06-07, 13 on the farewell skill 08-29..09-04), 2 unjoinable. **Since 06-08 no skill has been recognised on a turn Travis wrote.** Recognition volume: Jun 32, Jul 28, Aug 43, Sep 38, Oct 52 (all 10-11..10-19 plus one on 10-30), 1 since.
- **World-graded is empty for conversation by construction** (F-3922). The conversational action bridge is the only way a human-turn reply fires a hand: `data/conversational_action_log.jsonl` has 68 rows, 17 deed candidates, 2 dispatches, both `look` or `move`, which `observe_hand` ignores. The loose proxy (cycle id appears beside a fired hand in `hands_trace`) passes 21 of 22 post-gate clusters but measures idle-thought activity stamped with the last cycle id (about 8 rows per cycle id), not a verdict on the answer; with 2 human members required it gives 0.
- **A human-only gate in forward time** (T5 material restricted to Travis-authored turns: no farewell templates, no slash commands, first line over 8 characters; same gate otherwise; swept every 3 hours from 08-22 to 11-05, 597 sweeps, dedupe at cosine 0.85): **2 distinct qualifying clusters in 75 days**, 09-05 "off to bed" and 10-08 "we're going to pause for a while". Both are goodnight farewells. That is a genuinely situational kind of moment (how Du receives an evening closing), but it is a handful in a quarter.
- **Today's human material cannot even form a cluster.** The 7-day window ending 11-05 holds 27 Travis turns, all on 11-01; the largest human-only cluster is 12 members, and it is eleven "渡," salutations plus a "Hello Du", because `recent_lived_inputs` (core/memory/store.py 2559-2582) keeps only the first line of a stored `Q:` and Travis's messages open with the salutation line (35 human fragments have a first line of 8 characters or fewer; F-3921). Any human-turn rule needs that parse fixed first, or it clusters greetings.

## 3. What a recognised skill would change in an answer: control arm and decoupled judge

**Already measurable now, free: the retrospective matched pair.** 166 recognised internal cycles; 164 have at least one unrecognised internal near-duplicate question (cosine at least 0.80, within 14 days) to serve as control (before the skill existed, after its mirror row was deleted by the rust cliff F-3722, or below rung). Outcome: environment-word count in the stored 350 characters of the answer, ENV = `tides?|wind|rain|fire|shore|garden|air|light|shadows?|stones?|sea|river|birds?|grass|sky|embers?|surroundings?|environment|hearth|mud|water|waves?|salt|cold|warm|smell|sound|window|breeze|moss|clay|leaves|trees?|ground|earth|sun|moon|dusk|dawn|rhythm` (40 stems; F-3923's text says 38). Result: recognised minus control = **+0.055 words (95% bootstrap CI -0.147 to +0.262)**, share with at least 2 environment words **-0.058 (CI -0.121 to +0.005)**; per skill the sign is mixed (mottainai +0.20 over 41 pairs, "concept to others" -0.30 over 26). With the line injected, answers to the same question were not detectably more environmental. A crude proxy on truncated text, observational, not randomised; it is a floor of evidence, not a verdict, which is why the judge run below exists.

**Per candidate rule: what a recognised skill would change, and how to measure it.**

| Rule | What a recognised skill changes | Control arm | Judge | Powerable? |
|---|---|---|---|---|
| Current (self-asked material) | the Executive and Reflection prompts gain "A LEARNED WAY YOU HANDLE THIS ... for fluency, not to recite: <his own distilled voice>" | retrospective: the 164 matched pairs. Live arm (below) not recommended | pairwise, judge_panel | live: no. retrospective: yes (164 pairs) |
| (a) at least 2 human turns | how Du closes an evening (a farewell skill), nothing else yet | the same, but N = 2 skills; Travis reads the farewell replies himself | not needed at N this small | no (needs about 150 pairs) |
| (b) world-graded only | the world repertoire line `known_text` ("things you have done before and that held") in idle thought, not an approach line | withhold `known_text` on half of idle thoughts by a deterministic coin | none: the world's answer is the grader (refusal-kind from J-2578 separates skill failures from "already" and "precondition") | yes: about 12 logged world-procedure events a day (944 in 75 days), about 150 outcomes per arm in weeks (J-3331) |
| (c) both | the empty set for conversation; collapses to (b) | as (b) | as (b) | as (b) |

**Live control arm, if the founder wants one for the current rule** (not recommended, specified so the choice is informed). At `_procedural_recognition` after a match passes the gates, a deterministic coin `int(sha1(cycle_id)[:8], 16) % 2` picks `inject` (unchanged) or `withhold` (`active_procedure` left None). Flag `T5_ARM`, default OFF, founder-gated because it removes an existing injection from half of the recognised cycles (nothing is added to any prompt; no hint reaches Du). Log `data/t5_arm_shadow.jsonl`: ts, cycle_id, input_type, skill key, similarity, rung, arm, approach sha, question[:200]; at cycle end append answer[:600], environment-word count, length, first-8-word hash, and cosine of the answer to the centroid of Du's previous 20 answers. Power: a 60/40 preference needs about 152 stable pairs (one-sided alpha 0.05, power 0.8). At 52 recognitions in the best month and 1 in the last 6 days that is more than a year of evidence for the thing most in doubt.

**The decoupled judge (J-3328).** Present Q and two anonymised answers X and Y, order randomised, each pair judged twice with the order swapped; only stable decisions count; the skill text and arm label are never shown. Use `core/judge_panel.rule_detail` with two boolean keys, `x_more_responsive` and `x_less_formulaic`, on JUDGE_1 mixtral:8x7b (Ramses :11438), JUDGE_2 falcon3 (:11440) and TIEBREAK granite (:11437): three families (Mistral, TII, IBM), none the writer (qwen3.5:9b hot lane) and none the compile model (command-r7b background :11441), and none of it is the compile's own cycles. Two cautions from the module itself: the shared tiebreak is measured unfit on some keys (F-3639), so tiebreak-decided and split verdicts count as no verdict; and :11438 is shared with dream-primary and the commitment-defeater, so run quiet and rate-limited. Calibration: 164 null pairs (two unrecognised near-duplicate answers) to measure position bias, length bias and each judge's base rate. Pre-registered read: the skill is supported only if stable preference for with-skill answers is at least 60% with a lower CI bound above 50% AND the null is within 45-55%. Otherwise the null result stands.

## 4. Is "observe the environment" itself the attractor?

I read the 19 approaches compiled from 09-04 on. 14 tell him to observe or draw on the surroundings, nature or a sensory scene ("Look at the surroundings, observe the details, and relate them to the question"; "Travis, observe the environment and consider the implications"; "I anchor my response in immediate sensory details like cold air or quiet gardens"; "I observe the effect of oil on light and shadows, describing how it alters the very physics of darkness"). Two are partial (09-10 observe the subtle influences of relationships; 10-30 tide similes). Three are not (10-03 acknowledge the depth and offer to explore; 10-07 laws as river banks; 10-08 a concise historical explanation). By the same regex as F-3717: 8 of 53 before 08-22, 1 of 5 from 08-22 to 09-03, 14 of 19 from 09-04.

Is that text driving his voice, or reflecting it? Three observations all say reflecting:

1. **Timing.** Share of his internal-cycle answers with at least 2 environment words in the stored answer text: 14.5% June, 10.5% July, 20% August, 56% September, 59% October, 73% November. By week: 6.9% (08-06), 4.8% (08-13), **35.7% (08-20)**, 31.2% (08-27), 57.2% (09-03). The voice moved in the week of 08-20. The first approach in the run is 09-04, two weeks later. (J-3332 asks what moved it; the hot-lane model change of 2026-08-20 named in `core/judge_panel.py`'s header is the first candidate to check.)
2. **Contrast.** The matched-pair result in section 3: no detectable lift in environment imagery when the line was shown.
3. **Mechanism.** `_t5_compile` shows the model the first 6 members of the cluster (oldest first, 200 characters each) of Du's own answers and asks for "the consistent way you handle these". A distillation of the current voice returns the current voice. It adds no information he did not already have.

This does not clear the line of reinforcing the mottainai loop (F-3127: it steers how he answers, not what he asks): the measured effect on environment imagery is about zero, not provably zero, and the attractor sits upstream of T5. Confidence: measurements verified, causal reading inferred (F-3923 is recorded `inferred`).

## 5. Recommendation among the four options

| Option | What the evidence says | Verdict |
|---|---|---|
| Require human turns | in practice about 2 skills per 75 days, both farewells; needs the first-line parse fix (F-3921) and a system-origin exclusion before it works at all; the one post-gate human cluster was a system message | same outcome as retiring, more to build |
| Retire the conversational compile | 62 of 77 clusters had no human member; no recognition on a Travis-authored turn since 06-08; no world grader exists; every skill is born `persisted` so the plan's own kill test cannot fire; the line does not detectably change answers | **recommended** |
| Keep with judge and control arm | judge is available and decoupled; arm cannot be powered (about 1 recognition a week against about 150 pairs); the retrospective arm is the affordable version and is queued as a check on this call, not a precondition | not as a live feature |
| Redesign | nothing grades a conversational posture: 2 conversational dispatches ever, both `look`/`move`; the only candidate is Travis's next turn, and his volume is 27 turns in the last 7 days, all on one day | premature; revisit on volume |

**Recommended change (D-0676, build J-3329, needs founder go-ahead):** one kill-switch constant (default off) that stops `_t5_compile` and its no-LLM "reinforce existing" pass (931 passes since June) and stops `_procedural_recognition` injecting the approach into Reflection and Executive. Keep all code; archive, do not delete, the 22 conversation ledger rows and 3 mirror rows (coordinate with J-3180, D-0567: the ledger's rust becomes the only clock); the world half (`observe_hand`, `known_text`) is untouched. The change removes an injection, adds nothing to any prompt, and is restart-gated, so it needs no hint to Du and respects additive-only.

**Re-entry test (pre-registered, J-3330):** a read-only monthly replay of the human-only gate (full multi-line Q parsed, system templates excluded, 24-hour separation instead of calendar days, sources = distinct conversations) re-opens the conversational compile only if it finds at least 3 distinct qualifying clusters in a month of Travis-authored turns. The D-0676 defeater also reopens it if the retrospective judge run (J-3328) shows a stable at-least-60% preference with CI above 50% and a clean null.

## What needs a founder call

- **D-0676 (opened by this job):** retire the conversational compile and recognition injection (recommended), or require human turns, keep with judge and arm, or redesign. J-3329 (the build) waits on it as `needs_input`.
- Nothing else. D-0567 (ledger rust is the only clock) was ruled 2026-11-02 and is unchanged; J-3180 implements it and is the natural carrier for the archive step.

## Caveats and what I did not do

- Environment-word density is a lexicon proxy over 350 stored characters per answer; the matched pairs are observational. I did not run any LLM judge (the hubs are shared and Du is live); J-3328 does it.
- Pre-gate replays are approximate (window differed); every post-gate number uses the code as it stands and matches logged cluster sizes in 19 of 22 cases (the 3 misses are 1, 3 and 7 members larger, cause not identified).
- `input_type == human` is all I could join; it includes system-composed farewells. I excluded the two templates I found by frequency (22 and 21 fragments); other system or pasted text may remain, which would make the real human figures lower, not higher.
- The scratch scripts (`t5_prep`, `t5_embed`, `t5_replay`, `t5_sweep`, `t5_attractor`, in the session scratchpad) are not preserved in the repo; J-3328 and J-3330 rebuild them from the descriptions above.

## Provenance

Code read in full: `core/procedures.py`, `nodes/subconscious_node.py` 2831-2986, `core/memory/store.py` 2559-2716, `core/orchestrator.py` 1585-1691 and 2656-2708, `core/judge_panel.py` header and `_ask`/`rule_detail`, `docs/plans/t5_procedural.md`, `docs/reviews/t5_procedural_skills_2026-08-22.md`. Data: `data/subconscious_log.jsonl` (77 T5 rows), `data/affect_log.jsonl` (4,072 rows), `data/memory/nascence.db` lived fragments (5,704, 3,842 with a `Q:` line), `data/nascence.log` (193 recognised, 931 reinforce, 87 not-admissible), `data/procedures.json` and `data/procedures_log.jsonl`, `data/hands_trace.jsonl`, `data/conversational_action_log.jsonl`.
