# Du Prompt-to-Model Benchmark Suite — Screening Results, Re-Scored Gold Banks & F-5117 Audit Corrections

*Executed 2026-11-18 (Du down, `data/nascence.log` last line `20:16:57 Nascence shutting down.`) · 1,173 total inference calls across Phases 1–3, Stage B 10-fixture Banks, and CPU Ternary-Bonsai-2 · Confidence level: **`inferred`** (screening pass; see Section 1.2 & `F-5117`).*

Related: `docs/staged/du_prompt_model_benchmark.md` · `F-5117` · `D-0354` · [[I-0166]] · `T-0148` · `F-3063` · `F-3064` · `F-3071` · `docs/prompt_registry.jsonl` · `data/lab/du_benchmark_manifest_p0.json` · `data/lab/du_benchmark_fixtures_p0.json`.

---

## 1. Executive Summary & `F-5117` Methodological Corrections

We benchmarked **12 primary models** (10 via Ollama on the 1080 Ti `:11433` + 2 `Ternary-Bonsai-2-27B` GGUFs via CPU `llama-server.exe` on `:11455`) across **124 frozen real Du fixtures** spanning all **6 cognitive archetypes (`A1`–`A6`)**, **35 independent gold-labeled judge cases**, **6 Context Robustness regimes (`ctx_1`–`ctx_6`)**, and **40 Stage B fixtures** (`10` each on `P-0022`, `P-0035`, `P-0038`, `P-0039`).

### 1.1 Four Corrections Incorporated From `F-5117`

1. **`D-0354` Correction (`_NO_GRAMMAR_FIRST_PORTS` on `:11441`):**
   - **Retracted** the v1 recommendation to remove `:11441` from `_NO_GRAMMAR_FIRST_PORTS`.
   - Under `D-0354`, `:11441` runs on the Ramses lane where omitting JSON grammar on attempt 0 cuts median latency from `10.3s` to `1.7s` (`59` vs `9.4 tok/s`), and parse misses automatically retry with grammar on attempt 1. Thus, the 828 rows in `data/llm_json_parse_fail.jsonl` (`attempt: 0, g: 0`) are **retried first attempts, not lost calls**. Our benchmark ran `command-r7b` on the local 1080 Ti `:11433` (`42.3 tok/s` with `format="json"`), a different hardware path that did not measure the Ramses grammar penalty `D-0354` weighed.
2. **Re-Scored All Emitted JSON Schemas on `P-0037` Defeater Gold & `P-0100` Pursuits `J-2996` Gold:**
   - Re-scoring the saved `results_automated.json` across every emitted JSON structure (`{"thought": "A"}`, `{"result": "ADVANCES (A)"}`, `{"thoughts": [{"advance": true, ...}]}`, `{"evaluation": {"legitimacy": ...}}`, and `command-r7b`'s full-sentence `"judgment"`) eliminated all false `"key mismatch"` zeros:
     - **`phi4:latest` on `P-0037` Defeater Gold jumped from `3/14` to `11/14 (T:1, F:10)`** once its nested `{"evaluation": {"legitimacy": bool}}` schema was unwrapped.
     - **`command-r7b:latest` on `P-0037` Defeater Gold moved to `7/14 (T:6, F:8)`**.
     - On **`P-0100` Pursuits `J-2996` Gold** (where the 10 unambiguous cases sampled from the head of `J-2996` are all gold `R` or `T`, with `0` `A`), `qwen3:8b` (`A:9, R:0, T:0`), `gemma4:12b` (`A:8, R:0, T:2`), `falcon3:7b` (`A:6, R:0, T:0`), and `hermes3:8b` (`A:6, R:1, T:0`) were **not** failing JSON keys — they were **over-calling `ADVANCES (A)`** on restatements and tangents! Only **`MichelRosselli/bonsai-27b` (`4/10` exact 3-way, `7/10` binary non-A: `A:3, R:2, T:5`)**, **`command-r7b` (`3/10` exact, `7/10` binary non-A: `A:1, R:7, T:0`)**, **`qwen3.5:9b` (`4/10` exact, `5/10` binary: `A:3, R:3, T:2`)**, and **`phi4` (`3/10` exact, `5/10` binary: `A:2, R:0, T:5`)** resisted the "everything advances" bias.
     - Meanwhile, **`nemotron-mini` (`echoed input x5`)** and **`granite3-moe:1b` (`echoed input x11`)** genuinely failed `P-0037` and `P-0100` by echoing the input JSON dict back without emitting a verdict key.
3. **Confidence Level Set to `inferred` (`stage: partial` Screening Pass):**
   - With `n=9..14` on the gold banks and `n=10` per prompt on Stage B (`0.02–0.1` rubric differences), small rank gaps (such as `13/14` vs `14/14` on Defeater, or `6/9` vs `4/9` on Critic) sit within sampling noise. All rankings in this report are **`--confidence inferred`** screening results to guide deeper per-seat tests.
4. **`Ternary-Bonsai-2-27B` CPU Thread-Scaling, Unconfounded Binary & 14-Case Defeater Gold Completed (`T-0148` / `F-5117` #2 Resolved):**
   - We ran an unconfounded **6-way thread-scaling & build-isolation matrix** (`16` vs `32` threads, `PTQ1_0` vs `Q2_0`, `prism` vs `stock` `llama-server.exe`, `--reasoning-budget 0`) on the full **`1,122`-token real `P-0038` Commitment Scan prompt** (`core.commitment_ledger._SCAN_SYS + _dw_scan_fragment()`), followed by the **full 14-case `P-0037` Defeater Gold Bank** and a **resident prefix-cached `P-0038` repeat (`cache_prompt: true`)** at `-t 32` on `prism\llama-server.exe` (`results_bonsai2_thread_scaling.json`, `results_bonsai2_defeater_gold14.json`):
     - **Linear thread scaling (`8 → 16 → 32` threads):** Prefill jumped **3.5–3.6×**, from `4.45 → 8.74 → 16.12 tok/s` on `PTQ1_0` and `6.35 → 12.33 → 22.19 tok/s` on `Q2_0`.
     - **Unconfounded binary & quant comparison (`prism\llama-server.exe` at `-t 32`):** `prism` beats `stock` even on `Q2_0` (`5.03–5.30` vs `4.19–4.64 tok/s` gen). On the same `prism` binary, **`PTQ1_0` generates 14% faster (`5.73–5.81` vs `5.03–5.05 tok/s`)**, while **`Q2_0` prefills 38% faster (`22.19` vs `16.12 tok/s`)**.
     - **Resident prefix caching (`cache_prompt: true`) cuts ~1,100-token `P-0038` latency by >3×:** Because the ~788-token `_SCAN_SYS` system prompt stays cached in the `llama-server` KV slot, call 0 (cold KV, `1,088` tok evaluated) took `52.54s` (`Q2_0`) / `71.29s` (`PTQ1_0`), whereas **call 1 (warm KV prefix, `300` new user tokens evaluated) dropped to `16.98s` (`Q2_0`) and `21.79s` (`PTQ1_0`)**!
     - **Full 14-Case `P-0037` Defeater Gold Bank:** **Both `Ternary-Bonsai-2-27B-PTQ1_0` and `Ternary-Bonsai-2-27B-Q2_0` scored `14/14 (100%, T:3 F:11)`** at `-t 32` (`21.4s` median wall on `Q2_0`, `23.9s` median wall on `PTQ1_0`), matching 1-bit `MichelRosselli/bonsai-27b` (`14/14`).

---

## 2. Re-Scored Phase 1 & Phase 2 Hardware + Gold-Bank Matrix (644 Calls, `confidence: inferred`)

| Model | Backend / `num_ctx` | VRAM % | Cold Load | Warm Wall (Med) | Gen `tok/s` | Phase 2 Valid JSON | `P-0037` Defeater Gold (14: 3T / 11F) | `P-0008` Travis Critic Gold (9 strict: 4V / 5E) | `P-0100` Pursuits `J-2996` Gold (10: 0A / 5R / 5T) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`MichelRosselli/bonsai-27b`** (`Q1_0`) | Ollama `4096` | **100%** | `11.9s` | `4.98s` | `26.6` | 57/60 (95.0%) | **14/14 (100%)** `(T:3, F:11)` | `4/9` `(V:0, E:11 const veto)` | **4/10, bin 7/10** `(A:3, R:2, T:5)` |
| **`hermes3:8b`** | Ollama `8192` | **100%** | `39.6s` | `2.36s` | `53.0` | **60/60 (100%)** | **13/14 (92.9%)** `(T:4, F:10)` | `3/9` `(V:4, E:7 discrim)` | `0/10, bin 1/10` `(A:6, R:1, T:0)` |
| **`qwen3:8b`** | Ollama `8192` | **100%** | `88.3s` | `1.91s` | `45.3` | 59/60 (98.3%) | **12/14 (85.7%)** `(T:1, F:13)` | `4/9` `(V:9, E:2)` | `0/10, bin 0/10` `(A:9, R:0, T:0)` |
| **`gemma4:12b`** *(`:11439`)* | Ollama `8192` | **100%** | `6.0s` | `2.57s` | `28.5` | 58/60 (96.7%) | **12/14 (85.7%)** `(T:1, F:13)` | `4/9` `(V:0, E:11 const veto)` | `2/10, bin 2/10` `(A:8, R:0, T:2)` |
| **`qwen3.5:9b`** *(`:11433`)* | Ollama `8192` | **100%** | `23.3s` | `2.83s` | `38.6` | 57/60 (95.0%) | **11/14 (78.6%)** `(T:1, F:12)` | `3/9` `(V:6, E:5 discrim)` | **4/10, bin 5/10** `(A:3, R:3, T:2)` |
| **`phi4:latest`** (14B) | Ollama `8192` | **85.1%** | `140.7s` | `6.56s` | `18.2` | 57/60 (95.0%) | **11/14 (78.6%)** `(T:1, F:10)` | `4/9` `(V:10, E:1 const pass)` | `3/10, bin 5/10` `(A:2, R:0, T:5)` |
| **`falcon3:7b`** *(`:11440`)* | Ollama `8192` | **100%** | `3.8s` | **`1.61s`** | `49.1` | **60/60 (100%)** | `8/14 (57.1%)` `(T:9, F:5)` | **6/9 (66.7%)** `(V:4, E:7)` | `0/10, bin 0/10` `(A:6, R:0, T:0)` |
| **`command-r7b:latest`** *(`:11441`)* | Ollama `8192` | **100%** | `14.8s` | `2.75s` | `42.3` | **60/60 (100%)** | `7/14 (50.0%)` `(T:6, F:8)` | `4/9` `(V:10, E:1 const pass)` | `3/10,` **bin 7/10** `(A:1, R:7, T:0)` |
| **`nemotron-mini:latest`** | Ollama `8192` | **100%** | `19.1s` | `1.70s` | `68.8` | 56/60 (93.3%) | `0/14` *(echoed input x5)* | `1/9` `(V:5, E:3)` | `0/10` *(echoed input)* |
| **`granite3-moe:1b`** | Ollama `8192` | 88.1% | `4.1s` | **`1.39s`** | **`146.7`** | 46/60 (76.7%) | `0/14` *(echoed input x11)* | `1/9` `(V:6, E:4)` | `0/10` *(echoed input)* |
| **`Ternary-Bonsai-2-27B-Q2_0`** | `prism` CPU `-t 32` | 0% (CPU) | `4.5s` | **`21.4s` Def / `17.0s` cached P38** | `5.04` (`pe 22.19`) | **16/16 (100%)** | **14/14 (100%)** `(T:3, F:11)` | *not run* | *not run* |
| **`Ternary-Bonsai-2-27B-PTQ1_0`** | `prism` CPU `-t 32` | 0% (CPU) | `4.6s` | **`23.9s` Def / `21.8s` cached P38** | **`5.81`** (`pe 16.12`) | **16/16 (100%)** | **14/14 (100%)** `(T:3, F:11)` | *not run* | *not run* |

---

## 3. Phase 3 Blind Open-Ended Evaluation & Stage B 10-Fixture Banks (523 Calls, `confidence: inferred`)

- **Blinding & Evaluator Controls:**
  - Phase 3 (`252` blinded outputs) locked at SHA-256 `be07862b127c792b...` prior to unblinding; duplicate-control agreement **9/9 (100.0%)**.
  - Stage B (`303` blinded outputs across 40 fixtures) locked at SHA-256 `0ce7ba307cde4393...` prior to unblinding; duplicate-control agreement **14/14 (100.0%)**.

| Model | Phase 3 Overall (1–5) | Phase 3 Adequacy % | **A3** Distill (`P-0012`) | **A4** Synthesis (`P-0005/09/11`) | **A5** Voice (`P-0007/10/22`) | **Ctx `1..6` Robustness** | **Stage B `P-0022` Idle (10)** | **Stage B `P-0035` Delib (10)** | **Stage B `P-0039` Twin Words** | **Stage B `P-0038` Scan JSON** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`gemma4:12b`** | **4.28** | **92.6%** | `3.67` | `4.31` | **4.38** | `4.50` | `4.15` (`14.0s`) | `3.20` (`11.1s`) | ~103w *(fail)* | **10/10** (`0.39s`) |
| **`qwen3:8b`** | `4.25` | **85.2%** | `3.78` | `4.48` | `4.21` | `4.25` | `4.15` (**`4.4s`**) | `3.18` (`8.2s`) | **~18w** (`1.1s`) | **10/10** (`0.45s`) |
| **`falcon3:7b`** | **4.33** | `77.8%` | **4.33** | `4.52` | `4.22` | `4.42` | **4.17** (`5.8s`) | `3.28` (`5.9s`) | **~25w** (`1.3s`) | 9/10 (`1.60s`) |
| **`hermes3:8b`** | `4.30` | `77.8%` | `4.11` | `4.28` | **4.35** | **4.61** | `4.13` (**`4.7s`**) | `3.10` (**`4.2s`**) | **~17w** (`1.4s`) | **10/10** (`0.47s`) |
| **`qwen3.5:9b`** | `4.23` | `74.1%` | `3.83` | `4.39` | `4.22` | `4.17` | `4.13` (`10.0s`) | **3.30** (`9.5s`) | **~12w** (`1.4s`) | **10/10** (`0.79s`) |
| **`bonsai-27b` (`Q1_0`)** | `4.19` | `70.4%` | `3.78` | **4.59** | `4.03` | `4.00` | `4.03` (`16.0s`) | `3.28` (`14.3s`) | **~19w** (`4.1s`) | **10/10** (`1.30s`) |
| **`command-r7b`** | `4.09` | `51.9%` | `3.83` | **4.54** | `3.88` | `3.95` | `3.63` (`6.6s`) | `3.27` (`8.9s`) | ~200w *(fail)* | **10/10** (`2.94s`) |

---

## 4. What Is Actionable Now vs. What Needs Deeper Follow-Up (`F-5117`)

1. **`P-0039` Condensed-Thought Twin (`--confidence inferred`, strong effect size):**
   - Keep `gemma4:12b` (~103 words) and `command-r7b` (~200 words) off `P-0039`; both failed the condensation contract, whereas `qwen3.5:9b` (~12w), `hermes3:8b` (~17w), `qwen3:8b` (~18w), and `bonsai-27b` (~19w) obeyed it.
2. **Hot Lane (`:11433` — `qwen3:8b` vs `qwen3.5:9b`):**
   - `qwen3:8b` scored within noise of `qwen3.5:9b` on `P-0022` Idle Thought voice (`4.15` vs `4.13`) while cutting median warm wall time from `10.0s` to `4.4s` (and `0.45s` vs `0.79s` on `P-0038`), though it over-called `ADVANCES (A)` on `P-0100` Pursuits (`A:9/10` vs `qwen3.5:9b`'s `A:3, R:3, T:2`). Worth a founder-gated live A/B test on the hot lane.
3. **Judge Seats (`A2` — `hermes3:8b`, `falcon3:7b`, `bonsai-27b`):**
   - No model wins every judge station (confirming [[I-0166]]):
     - `bonsai-27b` (`14/14` Defeater, `7/10` binary Pursuits) and `gemma4:12b` (`12/14` Defeater) both collapsed into **100% constant veto (`V:0, E:11`)** on `P-0008` Critic.
     - `command-r7b` and `phi4` (`11/14` Defeater) both collapsed into **nearly constant pass (`V:10, E:1`)** on `P-0008` Critic.
     - `hermes3:8b` (`13/14` Defeater, `V:4, E:7` Critic) and `falcon3:7b` (`6/9` Critic, `V:4, E:7`) discriminated on Critic, but both over-called `ADVANCES (A)` on `P-0100` Pursuits (`A:6/10`).
   - **Next step:** Run a deeper gold bank on `hermes3:8b` and `falcon3:7b` for the Defeater and Critic seats before changing any live judge seat.
4. **`Ternary-Bonsai-2-27B` CPU Seat Ruling On Hold Pending Thread-Scaling Probe:**
   - Run the unconfounded **16- / 32-thread scaling probe** (on this 64-logical-CPU Threadripper) using a **~1,000-token real `P-0038` prompt** and the **same `prism\llama-server.exe` binary** for both `PTQ1_0` and `Q2_0`.
