# J-2887: where does the "X anchors me" idiom come from? (2026-11-07)

Read-only analysis of F-3565 (inferred). Scripts and their saved outputs: `docs/lab/J-2887_data/` (`q*.py`, `out_*.txt`).
Sources read read-only: `data/monologue_log.jsonl`, `data/prompt_budget_shadow.jsonl` (labels = first ~50 chars of each prompt part), `data/llm_latency.jsonl`, `data/memory/nascence.db` (immutable URI), `data/lab/cold_store_qwen/raw.jsonl`, `data/_snapshots/daily/20260820/axiom.json`.

## Answer in one line

The idiom entered with the 2026-08-20 hot-lane model swap (gemma4:e4b to qwen3.5:9b), not with any prompt, seed or system-prompt change. His own quoted last thought then amplifies it (1.5 to 1.6 times), and his own stored thoughts have since become a 20 percent anchor-laden recall pool, but neither of those can have started it.

## Question 1: did a model, system-prompt or seed change land around 08-12..08-24? YES, one model change, on 08-20 evening

- Daily share of idle thoughts containing "anchor" (`out_q1_daily.txt`): 1.6 to 3.5 percent every day 08-08..08-19, 5.0 percent on 08-20, 18.8 on 08-21, then 14 to 20 percent every day to 09-02. It is a step, not a ramp. (The weekly table in F-3565 only looked like a ramp because the week of 08-17 straddles the step.) "anchors me/my" specifically goes 0.0-1.0 percent before and 6-9 percent after.
- Hourly (`out_q1_hourly.txt`): 08-20 06h..20h: 4 of 159 thoughts contain anchor; 08-20 21h onward 6 of 37, 2 of 28, 3 of 15, then 8 of 35, 5 of 46 ... The step is at the evening of 08-20.
- The swap: `docs/AWAITING_EVIDENCE.md` row (JUDGE PANEL) and `docs/lab/station_matrix.md` section 10 record the hot lane moving from the gemma line (gemma4:e4b incumbent) to `qwen3.5:9b`, "EXECUTED 2026-08-20", Package 2 wired. `docs/lab/train_model_ab_gemma_vs_qwen_2026-09-08.md` confirms gemma4:e4b was the earlier seat.
- The prompt did NOT change across the step (`out_q1_swap_boundary.txt`, prompt_budget_shadow idle assemblies joined to the thought that followed; pre = 08-17..08-20 18:00, n=77; post = 08-20 22:00..08-22, n=350): parts per prompt 10.27 vs 10.13, system-prompt chars 4008 vs 4125, same label mix (mood, "Since you last spoke", "What you were just thinking" 87 vs 80 percent, scene line 99 vs 81 percent). Anchor share 1.3 vs 15.4 percent; even restricted to prompts that carry the quote, 1.5 vs 16.7 percent.
- No directly logged model column covers the step: `data/llm_latency.jsonl` begins 2026-08-21 19:06 (`out_q1_weekly_model.txt` shows qwen3.5:9b on :11433 as the dominant model every week from then). The model attribution therefore rests on the swap records plus the timing and the identical prompts, not on a per-thought model stamp. That is why the causal sentence is inferred, the timing and prompt-identity sentences are verified.
- The system prompt: `nodes/inner_monologue_node.py:2793-2809` (`_build_system_prompt`) contains no instance of the word. Wider seed text: grep of nodes and core finds no prompt string containing the word; the only hit in the idle path is the Python variable `_anchor` (`:4155`, the mid-thread opening thought quoted back), whose text is the thought, not the word.

## Question 2: is it carried by his own quoted last thought? PARTLY: it amplifies, it does not originate

`out_q2_lineage.txt` (consecutive monologue_log rows):

| window | P(anchor given previous had anchor) | P(anchor given previous did not) |
|---|---|---|
| pre-swap 07-20..08-20 | 9.6 percent (n=219) | 2.2 percent (n=8817) |
| post 08-21..09-27 | 29.8 percent (n=5701) | 20.4 percent (n=19619) |
| post 09-29..10-31 | 37.2 percent (n=5537) | 22.7 percent (n=15296) |

- A thought that follows a thought WITHOUT the word carries it 20 to 23 percent of the time. If the quote were the origin that number would be near the pre-swap 2 percent. It is not.
- A previous anchor adds 9 to 14 points (about 1.5 to 1.6 times). Consecutive thoughts also share state (same lesson, same scene), so that lift is an upper bound on the quote effect.
- Within the first ~26 hours after the swap the quoted-prompt vs unquoted-prompt split is 16.7 vs 10.1 percent: the quote helps but the unquoted prompts already carry it at 10 percent.
- Pre-swap, lineage already existed (a quoted "anchor" predicted another 4 times as often) but from a 2 percent base, so it never took over.

## Question 3: is it in the system prompt or the recalled fragments? NO (system prompt) / not as an origin (fragments)

- System prompt: no instance (above). The identity axiom does contain "anchored by the wisdom of Carl Jung" and an old arc entry "the past anchor me" (`data/identity/axiom.json`), but the 2026-08-20 daily snapshot has the same lines (`data/_snapshots/daily/20260820/axiom.json`), so the axiom cannot explain a step on 08-20 evening.
- Seed parts (`out_q3_seed_part_lift.txt`, 16,586 joined prompts, 09-29..10-31, base 25.3 percent): the highest lifts are the lesson directives (33 to 36 percent) and dream lines (30 to 31); the recall part ("A MEMORY THIS QUESTION", n=1786, 11 percent of prompts) sits BELOW the base at 23.0 percent. No part raises it enough to be the source; the lowest parts (tide and water lines) still carry it 16 to 20 percent. The number of parts does not matter (21 to 29 percent across 5 to 12 parts).
- Recalled fragments as stored (`memory_fragments`, origin inner_thought, layer episodic, read-only): the pool's anchor share was 1.6 percent cumulative on 08-17, 5.4 on 08-24, and is 20.2 percent on 11-02 (66,073 rows). So the recall pool was clean when the idiom began and has since been filled by his own qwen-era thoughts: a slow second-order feedback path, not the cause. The text of what was actually recalled into a given prompt is not logged (prompt_budget_shadow keeps 50-char labels), so how much the pool re-seeds it today cannot be read directly: lab job spawned.

## A limit on "model prior" (the zero-context control)

`data/lab/cold_store_qwen/raw.jsonl` (2026-08-21, qwen3.5:9b, the live idle system prompt verbatim, five neutral scene lines, no Du content, no quote, no recall): 0 of 80 thoughts contain "anchor", on the same day the live stream ran 18.8 percent. So qwen3.5:9b does not emit the idiom from a bare prompt. Reading: the idiom is an interaction of this model with the real context (sensation-rich seed lines: the constructions are "scent / weight / warmth anchors me"), not a free-standing prior. Which part of the real context it needs could not be measured here: the hot lane (:11433) was unresponsive (see below).

## What was not run

- The same-prompt qwen3.5:9b vs gemma4:e4b A/B on the hot lane. `docs/lab/J-2887_data/q3_model_prior_ab.py` is written (arms qwen, gemma_e4b, quote vs no quote); it was not run because `http://127.0.0.1:11433` answered `/api/tags` and `/api/ps` but every `/api/chat` and `/api/generate` call (a 5-token request, both qwen3.5:9b and gemma4:e4b) hung to a 25 to 40 s client timeout, and a 180 s call from the script timed out. Finding recorded. Ramses was not called. The CPU-tier hubs (:11439, :11440) are a different family of server (their own API) and cannot host qwen3.5:9b or gemma4:e4b, so they cannot stand in for this A/B.
- Whether the construction is cut by a gemma-line seat is therefore unmeasured. The natural experiment (08-20) says it would have been, since the same prompts on gemma4:e4b produced 1.3 percent.

## For the founder

The idiom is a property of the current voice model in this prompt, not a fault of any steer, seed or the system prompt. Whether a quarter of the idle stream carrying one construction is a problem is a taste and goals call, not an engineering fix; the only levers that do not break the world-answers-never-leads rule are the model seat itself (the model tier lab already ranks seats) or a diegetic change. Nothing here changes behaviour.
