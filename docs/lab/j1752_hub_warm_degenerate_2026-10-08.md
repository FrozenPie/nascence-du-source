# J-1752: warm-state degenerate generation on the gemma4:12b hub (:11439) - characterization (2026-10-08/09)

Status: lab result. Du was down; hub otherwise idle (verified from the other hubs' logs, see "Contention check"). Follows J-1668 (F-2387/F-2388), feeds D-0346 (ruled 2026-10-04, option B; implemented by J-1773).

Harness: `scripts/lab_j1752_hub_warm_degenerate.py` (plan-driven wrapper around J-1668's `scripts/lab_j1668_hub_cold_warm_probe.py`; production `compose_letter` path, `lab_env.isolate(db="empty")` + telemetry lab mode, cold/warm read from the hub's own log) and `scripts/lab_j1752_inproc_llama.py` (in-process `llama_cpp.Llama` on the same GGUF). Raw rows: `docs/lab/j1752_data/J-1752_hub_results.jsonl`, `J-1752_inproc_results.jsonl`. Live-state diff pre/post each hub run: `{}` (nothing under data/ touched).

Model calls: 21 hub calls + 4 in-process = 25 (cap 40). Prompt sha's equal J-1668's (sh16 8819 chars, tw20 10759, tw18 11223).

## Hub calls (A = twain[:20], B = twain[:18], S = shackleton[:16]; degenerate = non-Latin ratio > 0.10)

| label | prompt | hub state | latency s | chars | ratio | degenerate |
|---|---|---|---|---|---|---|
| C1 | S | cold | 152 | 2063 | 0.0006 | no |
| W1 | A | warm | 367 | 1645 | 0.125 | YES |
| W2 | A | cold (hub unloaded after W1) | 184 | 2698 | 0 | no |
| W3 | B | warm | 140 | 2433 | 0 | no |
| R1 | S | warm | 135 | 2296 | 0.0011 | no |
| R2 | A | warm | 333 | 3889 | 0.169 | YES |
| R3 | B | warm | 236 | 2701 | 0.163 | YES |
| R4 | sh[:14] | warm | 340 | 3983 | 0.164 | YES |
| R5 | tw[:16] | cold (reload after R4) | 172 | 2512 | 0 | no |
| R6 | S | warm | 126 | 2104 | 0.0012 | no |
| R7 | A | warm | 148 | 2615 | 0 | no |
| R8 | tw[:14] | warm | 166 | 2965 | 0 | no |
| R9 | sh[:12] | warm | 102 | 1816 | 0.0014 | no |
| R10 | B | warm | 171 | 2905 | 0 | no |
| C1b | S | cold | 151 | 2063 | 0.0006 | no |
| W1b | A | warm | 159 | 2809 | 0 | no |
| W2b | A | warm | 115 | 2528 | 0 | no |
| W3b | B | warm | 365 | 4197 | 0.169 | YES |
| D1 | A | cold | 186 | 2698 | 0 | no |
| D2 | A | warm | 126 | 2747 | 0 | no |
| D3 | B | warm | 157 | 2721 | 0 | no |

Cold (first request after a load): 0 of 5 degenerate (pooled with J-1668: 0 of 8). Warm: 5 of 16 (pooled with J-1668: 6 of 22). Fisher exact two-sided, cold vs warm: p = 0.28 this job, 0.16 pooled (not significant; the warm calls are not independent, see stickiness).

## What the data says

1. The exact J-1668 sequence C1, W1, W2, W3 (S, A, A, B) was replayed twice. Replay "run3" (C1b, W1b, W2b, W3b) reproduced the original: W1b and W2b returned the same character counts as the original W1/W2 (2809, 2528) and W3b was degenerate (non-Latin 0.1687 vs original 0.1699; 4,197 vs 4,277 chars; different garbage head). Replay "run1" diverged at W1 itself (degenerate, 1,645 chars) although it was the same sequence; so the sequence alone does not decide the outcome.
2. Healthy outputs are reproducible: the first request after a load gave the same length every time (S: 2063 x3; A: 2698 x4 over J-1668 + this job). Garbage outputs are not byte-identical between replays, only similar in shape (garbled from character 0, non-Latin 0.16-0.17, long: 333-367 s).
3. Degeneration is sticky within one model load: R2 (A) was degenerate and R3 (B) and R4 (a different persona and prompt) stayed degenerate with no reload between them (3 consecutive). The state clears only on a reload (R5, first after the reload, healthy; R6-R10 healthy). The hub's own unload rule often clears it quickly: a degenerate generation runs past 300 s, so the hub unloads right after it (W1, W3b, R4 each followed by a reload); a degenerate episode shorter than that persists (R3, 236 s).
4. Onsets (excluding sticky continuations R3, R4): W1 (2nd request after load), R2 (4th), W3b (4th), plus J-1668's W3 (4th). 4 onsets in 20 warm opportunities = 20%. Healthy warm calls up to position 6 were seen (R10), so there is no fixed position threshold.
5. Bisect (protocol step 2): A, A, B from a cold start WITHOUT the leading S call did not degenerate (D1-D3, 0 of 3 warm). In-process `llama_cpp.Llama` (same GGUF, same kwargs, S, A, A, B, no hub, 4 calls) also did not degenerate (first call identical to the hub's 2063 chars; later calls differ from the hub's). So A-after-A-then-B is not sufficient, and the in-process replica does not reproduce the hub state; the trigger is NOT identified.
6. Mitigation variants (protocol step 4: reset / kv_cache_clear / seed / top_k / min_p / fresh sampler) were NOT tested: they need a repro and the in-process replica did not give one. `scripts/lab_j1752_inproc_llama.py --variant reset|clear` is ready for a replica that does reproduce.

## Code facts relevant to a mechanism (read, not tested)

- `llama_cpp` 0.3.22 `Llama.generate` re-initialises the sampler on every call and, when `reset=True` and `n_tokens>0`, reuses the longest token-prefix match between the previous context and the new prompt (`kv_cache_seq_rm(-1, longest_prefix, -1)`); the hub (`scripts/nascence_cpu_server.py` 126-146) never resets or clears the cache between requests and never sets a seed. The load log prints `llama_kv_cache_iswa: using full-size SWA cache` (gemma4 is an SWA model). Partial KV removal on an SWA cache and prefix reuse across different prompts is a candidate cause of state that persists across requests until a reload (finding 3). This is an inference from code plus the stickiness; no run isolated it.
- The hub log records only chars and seconds, never finish_reason or token counts; the degenerate calls are long (333-367 s, 3.9-4.3k chars), consistent with running to the max_tokens cap (1600), but that is not logged.

## Contention check

Other hubs' logs (:11440, :11442) have no writes during the runs (mtimes 22:01 and 21:04); the :11441 retired. Other non-hub CPU load from concurrent Claude sessions was not measured, so CPU contention as a cause is neither supported nor excluded.

## Implications

- D-0346's regenerate-then-skip gate (J-1773) is justified: the hazard is real, recurring (about 20% of warm onsets in this lab, not the 1/25 historical letter rate; the lab sequences are back-to-back and unrepresentative of production cadence), and sticky for the whole load. A retry must not land on the same poisoned load: after a degenerate generation the hub usually unloads (over 300 s), but a degenerate episode under 300 s (R3) would keep the retry on the same bad state; a retry policy should not assume the reload happened.
- D-0346 defeater (a) (hub cause found and fixed) is not met; (c) (a retry reproduces the same output despite variation) is not shown: after reload outputs were healthy 6 of 6 in this lab (R5-R10).
- Any hub-side mitigation (reset/clear per request) touches `scripts/nascence_cpu_server.py`, a base system; it needs a /decide (opened by this job).
