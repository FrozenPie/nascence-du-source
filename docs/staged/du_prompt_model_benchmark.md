# Du Prompt-to-Model Benchmark Suite

> **Status: ⚪ PARTIAL, SCREENING PASS COMPLETE (`stage: partial`, `--confidence inferred` per `F-5117`, executed 2026-11-18 while Du was down; 1,173 total calls + 555 blind-scored candidates). Full report: `docs/lab/du_prompt_model_benchmark_results_2026-11-18.md`.**
> **Execution Gates:**
> 1. **Shared GPU & Du Ollama Ports (`:11433`–`:11442`):** Blocked until the founder confirms Du is stopped (`--confirm-du-down` + `data/llm_calls.jsonl` recency & process checks).
> 2. **CPU-Only Spare-Port Track (`--cpu-spare-port`, e.g. `:11455`):** Permitted with a thread cap for standalone CPU `llama-server.exe` runs (e.g. `Ternary-Bonsai-2-27B` `PTQ1_0` / `Q2_0`), since it never touches Du's GPU or Ollama ports.
> **Guardrail (Prompt Manager separation):** Benchmark findings never automatically modify prompts or seat assignments.

```plan-state
stage: partial
phase: Stage A + Stage B screening + Ternary-Bonsai-2 16/32-thread & 14-case Defeater Gold complete (1,211 total calls; confidence=inferred per F-5117). Both Ternary-Bonsai-2 PTQ1_0 and Q2_0 scored 14/14 on Defeater Gold at -t 32 on prism\llama-server.exe (17.0s-21.8s prefix-cached P-0038 wall).
verified: 2026-11-18
evidence_read: 2026-11-18
next: Founder reviews docs/lab/du_prompt_model_benchmark_results_2026-11-18.md; optional deeper gold banks for hermes3:8b and falcon3:7b on Defeater/Critic before changing live judge seats.
```

Related: [[I-0166]] · `T-0148` · `F-3063` · `F-3064` · `F-3065` · `F-3071` · `docs/prompt_registry.jsonl` · `docs/guidelines/prompt_registry.md` · `docs/lab/station_matrix.md` · `docs/lab/node_benchmark.md` · `data/lab/du_benchmark_manifest_p0.json` · `data/lab/du_benchmark_fixtures_p0.json` · `scripts/du_prompt_benchmark_suite.py`.

---

## 1. Goal: Prompt-to-Seat Allocation (Not 104 Model Swaps)

Swapping models on an 11 GB 1080 Ti costs **8 to 127 seconds** (`F-3064`). Therefore, the real deliverable of this benchmark is **not** assigning 104 independent models, but **grouping the 104 callable prompts onto Du's ~5–7 resident hardware seats** (per [[I-0166]]):

| Resident Seat ID | Endpoint / Hardware | Current Incumbent | Primary Role |
| :--- | :--- | :--- | :--- |
| `seat_hot_gpu` | `:11433` (1080 Ti 11 GB GPU) | `qwen3.5:9b` | Conscious loop, idle thought, fast low-latency stations |
| `seat_bg_synthesis` | `:11441` (CPU / hub) | `command-r7b:latest` | Background synthesis, subconscious, follow-line, essay *(828/846 JSON parse fails)* |
| `seat_judge_1` | `:11438` (Ramses i9) | `mixtral:8x7b` | Panel judge 1 & commitment defeater *(must be non-Qwen when judging Qwen)* |
| `seat_judge_2` | `:11440` (Local CPU hub) | `falcon3:7b` | Panel judge 2 & Librarian |
| `seat_tiebreak_fast` | `:11437` (Ramses 1650) | `granite3.1-moe:3b` | Panel tiebreak & curiosity worth |
| `seat_left_emissary` | `:11439` (Local CPU hub) | `gemma4:12b` | Left-lane graders, gist faithfulness & Emissary |
| `seat_ternary_bonsai_cpu` | Spare port `:11455` (CPU `llama-server`) | *Candidate (`Ternary-Bonsai-2-27B`)* | Candidate 27B ternary CPU seat (`T-0148` / [[I-0166]]) |

---

## 2. Two-Stage Experimental Structure & Confidence Discipline

49 screening fixtures across 104 prompts are enough to screen archetypes, not to claim `verified` per-prompt winners. Per `CLAUDE.md` rule 4:

1. **Stage A — Archetype Screening (Phases 1–3, `--confidence inferred`):**
   - Screens the candidate slate across **A1–A6** using the 42 standard real fixtures, 6 context-robustness regimes, 1 max-context degradation fixture, and **35 gold-labeled judge cases**.
   - Findings from Stage A are logged strictly as `--confidence inferred`.
2. **Stage B — Deep Per-Prompt Banks (`--phase stage-b`, `--confidence verified`):**
   - Evaluates the top contenders on deeper per-prompt banks where a seat decision actually pays off:
     - **`P-0022` Idle thought** (3,098 calls/7d) — 10-fixture deep bank + 6 context regimes
     - **`P-0035` Deliberation pass 3** (1,991 calls/7d) — 10-fixture deep bank
     - **`P-0038` Commitment scan** (1,134 calls/7d) — 10-fixture deep bank with outcome labels
     - **`P-0039` Condensed-thought twin** (737 calls/7d, SHADOW) — 10-fixture deep bank
     - **Gold-Labeled Judge & Router Banks:** `P-0037` Defeater (14 gold cases), `P-0008`/`P-0017` Critic (11 Travis-labeled gold cases), `P-0100` Pursuits advances (10 gold cases from `J-2996`), `P-0103` Tension resolution (`J-3048`), `P-0102` Follow-line stop-5 (`J-3651`/`J-3653`), `P-0080` Librarian (`model_tier_librarian_lab.py`).

---

## 3. Reconciled Prompt Inventory (132 → 104 Callable Rows / 115 Keys)

| Disposition | Count | Registry Breakdown | Benchmark Role |
| :--- | :---: | :--- | :--- |
| **Directly callable** | **77** | `LIVE` + `LIVE-PROVISIONAL` (`node`, `call`, `judge`, `raw_http`) | Primary benchmark targets |
| **Shadow callable** | **27** | `SHADOW` (`call`, `judge`, `raw_http`) | In-testing benchmark targets |
| **Dispatch wrapper** | **1** | `P-0013` (`NodeBase.run` / `run_best_of` in `conversation`) | Delegates to nodes |
| **Fragment** | **5** | `P-0030`–`P-0033` (`idle_seed`) + `P-0121` (`SHADOW` `judges_lanes` fragment) | Feeds parent prompts |
| **Excluded by status** | **22** | `DORMANT` (9), `WRITE-ONLY` (9), `RETIRED` (2), `DEAD` (2) | Out of scope |
| **Total** | **132** | `77 + 27 + 1 + 5 = 110` in-scope; `110 + 22 = 132` total | **104 callable rows (115 keys/stages)** |

---

## 4. Primary Candidate Model Slate (12 Models — Incumbents + Bonsai + Challengers)

Every call pins `num_ctx` explicitly and records `think` / `reasoning_effort` (`none`, `low`, `xhigh`) so reasoning-token overhead and context-window VRAM spill (`F-3064`) never distort comparisons:

| # | Model | Backend | Pinned `num_ctx` | Reasoning Control | Experimental Role |
| :---: | :--- | :--- | :---: | :--- | :--- |
| 1 | `qwen3.5:9b` | Ollama | `8192` | `think: false` *(+ `true` probe)* | **Incumbent `:11433` hot-lane baseline** |
| 2 | `command-r7b:latest` | Ollama | `8192` | `none` | **Incumbent `:11441` background baseline** (0.86 synthesis coverage, 828/846 JSON parse fails) |
| 3 | `MichelRosselli/bonsai-27b:latest` | Ollama | `4096` *(mandatory per `F-3064`)* | `think: false` | **1-bit 27B (`Q1_0`) on GPU** (4.43 GB in VRAM at 4096 ctx; 39/42 defeater gold `F-3071`, 26/43 decomposer `F-3063`) |
| 4 | `Ternary-Bonsai-2-27B-PTQ1_0.gguf` | PrismML `llama-server` | `4096` | `none` vs `xhigh` | **`T-0148` / [[I-0166]] primary target:** 27B ternary `PTQ1_0` (`bonsai2\models\`, `bonsai2\prism\llama-server.exe`) |
| 5 | `Ternary-Bonsai-2-27B-Q2_0.gguf` | Stock/Prism `llama-server` | `4096` | `none` vs `xhigh` | **`T-0148` / [[I-0166]] primary target:** 27B `Q2_0` (`bonsai2\models\`, `bonsai2\stock\llama-server.exe`) |
| 6 | `falcon3:7b` | Ollama | `8192` | `none` | **Incumbent `:11440` `JUDGE_2` & Librarian baseline** |
| 7 | `gemma4:12b` | Ollama | `8192` | `think: false` *(verify)* | **Incumbent `:11439` Left-lane / Emissary baseline** & non-Qwen judge |
| 8 | `nemotron-mini:latest` | Ollama | `8192` | `none` | 2.7 GB non-Qwen judge/classifier challenger (`1.00 FTFT` on `station_matrix.md`) |
| 9 | `granite3-moe:1b` | Ollama | `8192` | `none` | 0.82 GB MoE fast tiebreak/router floor (`0.75` discriminating on `station_matrix.md`) |
| 10 | `qwen3:8b` | Ollama | `8192` | `think: false` | Stock Qwen3 8B comparison *(note: `qwen3-du` is byte-identical with `num_ctx 8192` per `F-3065`)* |
| 11 | `hermes3:8b` | Ollama | `8192` | `none` | Non-Qwen Llama-family challenger *(replaces stock `llama3.1:8b`, which answered constant `TTTT` on `station_matrix.md`)* |
| 12 | `phi4:latest` | Ollama | `8192` | `none` | Deep synthesis & grounding challenger (`1.0` groundedness, `443w` author on `station_matrix.md`) |

---

## 5. Frozen Fixture & Gold-Bank Summary (124 Fixtures in `du_benchmark_fixtures_p0.json`)

| Archetype | Callable Prompts | Frozen Fixtures | Gold / Deep-Bank Coverage Included |
| :--- | :---: | :---: | :--- |
| **A1 — Classifiers & Routers** | 10 | **22** | 12 node fixtures + **10 `P-0038` Commitment scan Stage-B fixtures** + `P-0080` Librarian contract |
| **A2 — Judges & Evaluators** | 40 | **42** | **14 `P-0037` Defeater gold cases** + **11 Travis-labeled `P-0008` Critic gold cases** + **10 `P-0100` Pursuits `J-2996` gold cases** + 6 standard + 1 max-ctx stress |
| **A3 — Distillation & Closure** | 14 | **13** | 3 `P-0012` Consolidation fixtures + **10 `P-0039` Condensed-thought Stage-B fixtures** |
| **A4 — Reasoning & Synthesis** | 19 | **19** | 9 `Recall`/`Executive`/`Curiosity` fixtures + **10 `P-0035` Deliberation Stage-B fixtures** |
| **A5 — Voice & Imagination** | 15 | **25** | 9 `Reflection`/`Voice`/`Idle` fixtures + **6 Context Robustness regimes (`ctx_1`–`ctx_6`)** + **10 `P-0022` Idle Stage-B fixtures** |
| **A6 — Drills & Knowledge** | 6 | **3** | 3 `P-0024` Drill fixtures |
| **Total** | **104** | **124** | **35 Gold-Bank Judge Cases + 40 Stage-B Deep-Bank Cases + 49 Stage-A Screening Cases** |

*(For A2 Judges, accuracy and constant-answer detection (`TTTT`/`FFFF` trap per `docs/lab/station_matrix.md`) are scored against the **independent gold labels**, never against Du's own incumbent output.)*

---

## Current State — verified 2026-11-20

### What we have
Screening pass complete (2026-11-18, confidence inferred per F-5117): report at `docs/lab/du_prompt_model_benchmark_results_2026-11-18.md`; runner `scripts/du_prompt_benchmark_suite.py` exists. Ternary-Bonsai-2 CPU result is F-5118. The sign-off path for any seat change is `docs/staged/prompt_seat_routing.md` (D-0872..D-0876).

### What we need
Founder review of the report; optional deeper gold banks for hermes3:8b and falcon3:7b on Defeater/Critic before any live judge-seat change; the GPU/Ollama matrix only with Du stopped.

### What we're doing next
Nothing runs automatically; benchmark findings never change seats by themselves. Next step is the plan's own `next:` line (founder review).

## 6. Execution Runbook

```powershell
# 0. Static status check (100% safe anytime)
python scripts/du_prompt_benchmark_suite.py --status

# 1. CPU-Only Spare-Port Track (Ternary-Bonsai-2 via llama-server on :11455 with thread cap)
#    Start PrismML or stock llama-server on :11455 with -t 6 -c 4096 -ngl 0, then:
python scripts/du_prompt_benchmark_suite.py --phase stage-b --cpu-spare-port --base-url http://127.0.0.1:11455 --model-filter Ternary-Bonsai-2

# 2. Full GPU / Ollama Matrix (ONLY AFTER DU IS STOPPED)
python scripts/du_prompt_benchmark_suite.py --phase smoke --confirm-du-down
python scripts/du_prompt_benchmark_suite.py --phase automated --confirm-du-down --repeats 2
python scripts/du_prompt_benchmark_suite.py --phase blind-packets --confirm-du-down --repeats 2
python scripts/du_prompt_benchmark_suite.py --phase stage-b --confirm-du-down --repeats 2
```
