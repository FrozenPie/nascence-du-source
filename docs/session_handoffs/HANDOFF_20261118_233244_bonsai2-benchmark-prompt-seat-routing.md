# Ternary-Bonsai-2 look, Antigravity prompt-to-model benchmark review, and the Prompt Seat Routing plan

## Session timing
- **Session started:** 2026-11-18 06:18:18 UTC
- **Last message before wrap:** 2026-11-18 23:32:43 UTC
- **Wrapped:** 2026-11-18 23:32:44 UTC

## Summary
The founder asked whether prism-ml's Ternary-Bonsai-2-27B had been tested; it had not (only the older 1-bit bonsai-27b, J-2207/J-2218). The local CPU run was handed to Antigravity, whose results I reviewed twice, and the session ended by staging `docs/staged/prompt_seat_routing.md` (route each prompt to the best model seat instead of by lane) with five founder rulings.

## Decisions
- D-0872 (voice prompts P-0022/P-0007/P-0010 stay on one seat by default, not a standing rule), D-0873 (one resident model on the hot 1080 Ti seat), D-0874 (Ternary-Bonsai-2 CPU seat: 16 threads, background-only prompts while Du runs), D-0875 (dreamer :11442 yi:34b protected for now), D-0876 (each per-prompt promotion gets its own /decide ruling). All five ruled by travis in chat (AskUserQuestion), recorded 2026-11-19 NZ time; the defeaters were written by me and travis has not read them. Reopen with `decide.py reopen` if any is wrong.

## Builds
- Plan `docs/staged/prompt_seat_routing.md` (stage: draft, nothing built); I-0166 promoted to it. ROADMAP section "PROMPT SEAT ROUTING" added; memory file `project_nascence_prompt_seat_routing.md` added. Commit 6ab18984 holds the plan, Antigravity's benchmark report (`docs/lab/du_prompt_model_benchmark_results_2026-11-18.md`), its plan (`docs/staged/du_prompt_model_benchmark.md`), its runner `scripts/du_prompt_benchmark_suite.py`, and the ledgers.
- Antigravity ran the benchmark (1,173+ calls, 555 blind-scored candidates) with Du down; raw results are in `data/lab/du_benchmark/` (not in git).

## Findings
- F-5117 [inferred]: Antigravity's first recommendation to drop `:11441` from `_NO_GRAMMAR_FIRST_PORTS` contradicted D-0354 (no JSON grammar on first attempt, ~6x faster, retry with grammar); the 828 logged "failures" are retried misses. Gold banks (9-14 cases) and Stage B (n=10) are screening only. Antigravity accepted the corrections and retracted it.
- F-5118 [verified]: Ternary-Bonsai-2-27B on the 64-thread CPU: prefill scales ~linearly 8 to 32 threads (Q2_0 6.35 to 22.2 tok/s), generation saturates ~5-6 tok/s, cold 1,122-token P-0038 takes 66 s (Q2_0) / 84 s (PTQ1_0) at 32 threads, ~17-22 s with the system prompt cached. 14/14 on the Defeater bank for both quants, but the bank is 3 legit / 11 illegit so always-False scores 11/14. Evidence: `data/lab/du_benchmark/results_bonsai2_thread_scaling.json`, `results_bonsai2_defeater_gold14.json`.
- Benchmark takeaways (all inferred): no model wins every judge station (bonsai-27b 14/14 Defeater but constant veto on Critic; command-r7b strong on A4 synthesis, last on A5 voice; falcon3:7b best on Critic 6/9; hermes3:8b 13/14 Defeater); qwen3:8b matched qwen3.5:9b on idle-thought voice at ~4.4 s vs ~10 s; gemma4:12b and command-r7b fail the P-0039 twin condensation contract.
- The P-0100 Pursuits bank sample was the first 10 J-2996 cases, all gold R or T, so it tested over-calling ADVANCES, not discrimination.
- [INFERRED] The CPU generation speed limit looks memory-bandwidth-bound; prefill is compute-bound and still scaling at 32 threads (64 not tried).

## Open
1. The Pursuits bank needs the full J-2996 set before any `P-0100` move. Next: Antigravity re-scores with all cases.
2. Ternary-Bonsai-2 has no blind A4/A5 quality score. Next: run it on the existing blind packets at 16 threads on a spare port.
3. Contention test with Du running (all CPU numbers were taken with Du down). Needed before D-0874's CPU seat is stood up.
4. Plan P0 (read-only prompt-to-seat table, replay recent `data/llm_calls.jsonl` with zero diffs). Not started; run `udms_get_change_dossier` on `core/model_client.py` first (18 AST listeners).
5. `plan-maintain` filed backfill jobs J-4408 (du_prompt_model_benchmark) and J-4409 (prompt_seat_routing) for missing current_state/shadow_promotion_spec fields; the roadmap link and memory file were added after that pass and a final re-run with `--session` was still pending at wrap.
6. Ternary-Bonsai-2 files and runtimes are in this session's scratchpad `bonsai2\` folder and in Antigravity's copy; a re-download is ~13 GB if the scratchpad is cleared.

## Warnings
- Du was stopped for the benchmark; the report says `qwen3.5:9b` was restored warm on :11433. Check Du's liveness before assuming it is up.
- Commit 6ab18984 deliberately left untracked: `docs/06. Just the Way You Are.mp3`, `docs/findings.jsonl.lock`, `docs/prompt_registry.jsonl.lock`, `docs/ledger_backups_20261117/`.
- F-5117 was recorded without `--session`, so it is missing from the session rollup. The handoff cites it by hand.
- Antigravity's benchmark seat table lists a few endpoints loosely (e.g. `:11441` as "CPU / hub"; model_client.py comments say Ramses 3070). Verify against `core/model_client.py` and `core/judge_panel.py` in P0.
- Nothing in Du's code or lane map was changed this session.

## Pointers
- `docs/staged/prompt_seat_routing.md`, `docs/staged/du_prompt_model_benchmark.md`, `docs/lab/du_prompt_model_benchmark_results_2026-11-18.md`
- `core/model_client.py` (lane map ~line 36-126, `_NO_GRAMMAR_FIRST_PORTS` line 279), `core/judge_panel.py`
- `data/lab/du_benchmark/` (raw results, blind packets, locked scores), `scripts/du_prompt_benchmark_suite.py`
- Thought T-0148, idea I-0166, findings F-5117/F-5118, decisions D-0872..D-0876, D-0354, jobs J-4408/J-4409.
