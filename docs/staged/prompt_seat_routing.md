# Prompt Seat Routing — send each prompt to the model seat that suits it, instead of by lane

> **Status: 🔵 DRAFT v1 — staged 2026-11-19. Nothing built.** Founder direction (2026-11-19): move away from one "hot loop" model
> and spread model use across Du's prompts according to how well each model does the job. Descends from [[I-0166]]
> (per-prompt benchmarks and seats) and is the sign-off path that `docs/staged/du_prompt_model_benchmark.md` deliberately lacks
> ("benchmark findings never automatically modify prompts or seat assignments").

```plan-state
stage: draft
phase: Design only. Evidence base = the 2026-11-18 screening benchmark (inferred, F-5117) plus F-5118 (Ternary-Bonsai-2 CPU, verified). No code, no table, no live change.
verified: 2026-11-19
evidence_read: 2026-11-19
next: Founder answers recorded in section 8 (2026-11-19); enter them in /decide with defeaters; then P0 (read-only routing table that reproduces today's behaviour exactly).
cluster: 6
```

Related: [[I-0166]] · [[du_prompt_model_benchmark]] · [[prompt_manager]] · [[decoupled_judge_pattern]] · `T-0148` · `F-3063` · `F-3071` · `F-5117` · `F-5118` ·
`D-0354` · `D-0126` · `core/model_client.py` · `docs/prompt_registry.jsonl` · `docs/lab/du_prompt_model_benchmark_results_2026-11-18.md`.

---

## 1. Summary

Today a prompt's model is decided by *which lane its node calls*: `core/model_client.py` maps a port to a model (`:11433` qwen3.5:9b hot on
the 1080 Ti, `:11441` command-r7b on the Ramses 3070, `:11439` gemma4:12b, `:11440` falcon3:7b, `:11442` yi:34b dreamer; judge panel seats
on `:11438`/`:11437`), and `SERVE_CHAINS` gives some lanes a fallback. The 2026-11-18 benchmark showed the same model can be good at one
prompt and bad at another (bonsai-27b: 14/14 on the Defeater bank, constant veto on the Critic bank; command-r7b: 2nd on A4 synthesis,
last on A5 voice). So the unit that should be chosen is **the prompt**, not the lane.

Proposal: one routing table, `prompt_id -> ordered seat chain`, consulted by `model_client`. The default row for every prompt reproduces
today's behaviour exactly; a prompt only moves when a row says so, one prompt at a time, after a shadow period and a founder ruling.

## 2. What this is not

- **Not 104 models.** Seats are resident hardware endpoints. An 11 GB 1080 Ti swap costs 8-140 s (F-3064; qwen3:8b 88 s cold, phi4 141 s), so the
  GPU holds one 8-9B model. The choice per prompt is among roughly 5-7 existing seats plus at most one new CPU seat.
- **Not automatic.** The benchmark never edits the table. A row changes only by `/decide rule` plus an explicit table edit.
- **Not a prompt rewrite.** Prompt wording belongs to [[prompt_manager]]. This plan moves *where* a prompt runs, not *what it says*.
- **Not a change to base systems.** Additive only: the table sits beside the existing lane map; removing it restores today's code path.

## 3. Constraints that shape the design

1. **Hardware seats are few.** Seat list (verify against `core/model_client.py` and `core/judge_panel.py` in P0, do not trust this table):
   hot `:11433` (1080 Ti), background `:11441` (Ramses 3070, sole tenant), `:11439` gemma4:12b (CPU tier), `:11440` falcon3:7b (CPU tier),
   judge seats `:11438`/`:11437`, dreamer `:11442` yi:34b, plus a candidate Ternary-Bonsai-2 CPU `llama-server` seat.
2. **CPU seats compete.** F-2466: one job 34 s alone, 124 s with two CPU jobs at once. A Bonsai-2 seat at 32 of 64 threads (its measured sweet
   spot, F-5118) halves what the other CPU hubs get. Any new CPU seat needs a thread budget written down, not assumed.
3. **Voice is shared.** `P-0022` idle thought, `P-0007` reflection, `P-0010` voice (archetype A5) are one first-person voice. Moving one to a
   different model risks fragmenting it. Default: keep A5 prompts on a single "Self" seat unless a bank shows a clear win *and* voice holds across
   the six context regimes.
4. **Founder Law, cross-family judging.** A judge prompt's seat must differ in model family from the seat of the prompt it judges. Today this is
   kept by hand; with a table it can be linted.
5. **Changing a model confounds metrics.** The 2026-08-20 full shuffle muddied the commitment hold-rate (F-0288). One prompt per change, with a
   before/after read against that prompt's own bank.
6. **D-0354 stays.** `:11441` first attempts go without JSON grammar for ~6x speed, retry with grammar on a miss. Routing by prompt must keep the
   per-port grammar behaviour (the benchmark's 42 tok/s `format=json` number was not the :11441 hardware path; F-5117).
7. **Throughput under concurrency.** A slow seat (Bonsai-2: 17-22 s prefix-cached, 66-84 s cold at 1,100 tokens, ~5 tok/s generation) can only take
   prompts nobody is waiting on synchronously: sleep-time synthesis, defeater and pursuit judging, offline distillation.

## 4. Design

### 4.1 The table
One data file, `data/prompt_seat_table.json` (name to confirm), one row per registered prompt ID (the same IDs as `docs/prompt_registry.jsonl`):

```
P-0037: { seats: ["judge_hermes3", "judge_2_falcon3"], mode: "shadow", since: "...", ruling: "D-xxxx", bank: "defeater_gold_14" }
```

Fields: `seats` (ordered chain, first healthy wins), `mode` (`inherit` | `shadow` | `live`), `ruling` (decision ID, required for `live`),
`bank` (the gold bank that gates it), `family_must_differ_from` (optional prompt ID, drives the Founder Law lint).
`inherit` means "use today's lane map". A missing row is `inherit`.

### 4.2 Resolution order in `model_client`
`call_node*` resolves seat in this order: explicit caller override (tests, labs) -> table row with `mode: live` -> existing lane/port logic.
`shadow` rows do not change the served answer: the incumbent answers, the candidate also runs off the critical path and both outputs are logged.

### 4.3 Shadow runner
Runs the candidate seat on the same assembled prompt in the background, bounded by a rate cap and a CPU thread budget, and writes
`data/prompt_seat_shadow.jsonl` (prompt ID, fixture hash, incumbent seat/model, candidate seat/model, both outputs, wall times, parse result).
Write-only logs are a known failure pattern here, so P2 must include the reader (the scorer in 4.4), not just the writer.

### 4.4 Scoring and gates
Reuse `scripts/du_prompt_benchmark_suite.py`, the frozen fixtures and the gold banks as regression gates. A prompt may be promoted only if,
on its own bank, the candidate (a) is no worse than the incumbent on the prompt's primary criterion, (b) shows no constant-policy collapse
(always-veto, always-pass, always-ADVANCES) and (c) holds the schema. Gold-bank sizes today are 9-14 cases and Stage B is n=10, so every promotion
is labelled `inferred` until the bank is larger. Majority-class baselines are reported beside accuracy (the Defeater bank is 3 legit / 11 illegit, so
"always False" scores 11/14).

### 4.5 Lints (run in `/plan-maintain` or `prompt_registry.py check`)
- every `live` row has a ruling ID and a bank;
- judge prompts: seat family differs from the judged prompt's seat family;
- seat chain contains only seats that exist in the seat list;
- thread budget per CPU seat sums to <= the machine total.

### 4.6 Rollback
Set `mode: inherit` (or delete the row). No code path other than the resolver reads the table, so removal restores today's behaviour.

## 5. Phases

| Phase | What | Gate to leave |
| :--- | :--- | :--- |
| **P0** | Read `model_client.py`, `judge_panel.py`, `SERVE_CHAINS`. Generate the table with every prompt on `inherit`, plus a `seat_of(prompt_id)` reader. Verify it reproduces today's seat for 100% of recent `data/llm_calls.jsonl` rows. | Replay of recent calls shows zero diffs. |
| **P1** | Resolver in `model_client` behind a flag, default OFF. Lints. Registry fields in the prompt registry. | `prompt_registry.py check` green; flag OFF is byte-for-byte today's behaviour. |
| **P2** | Shadow runner + scorer (reader included). First shadow rows only (section 6). | One week of shadow rows scored per prompt. |
| **P3** | Per-prompt promotion, one at a time, each by founder ruling with a named defeater. | Per-prompt before/after on its own bank and one live metric. |
| **P4** | Optional: Ternary-Bonsai-2 CPU seat for slow-clock prompts, after blind A4/A5 scoring. | Thread budget agreed; contention test with Du up. |

## 6. Candidate first moves (all `inferred`; shadow only until ruled)

| Prompt | Candidate | Why (source) | Watch |
| :--- | :--- | :--- | :--- |
| `P-0022` idle thought | `qwen3:8b` on hot seat | Equal voice (4.15 vs 4.13), 4.4 s vs 10.0 s (Stage B) | Voice drift over context regimes; hot-lane VRAM and cold load 88 s |
| `P-0008` critic | `falcon3:7b` (`:11440`) | Best on Travis Critic gold (6/9, V:4 E:7); others collapse to constant veto or pass | n=9; over-calls True on Defeater, so Critic only |
| `P-0037` defeater | `hermes3:8b` or Bonsai-class | 13/14 and 14/14; non-Qwen family | Majority baseline 11/14; 3 legit cases only |
| `P-0100` pursuits | none yet | Sample was the head of J-2996, all R/T, so it did not test discrimination | Needs the full set first |
| `P-0039` twin | keep `qwen3.5:9b` | Tightest twin (~12 words); gemma4:12b (~103) and command-r7b (~200) fail the contract | Keep those two off it |
| A4 synthesis (`P-0005/9/11`) | `command-r7b` stays; Bonsai-2 as slow-seat candidate | A4 scores 4.54 / 4.59 | Bonsai-2 not yet scored blind on A4 |

## 7. Risks

- **Fragmenting Du's voice** across seats (constraint 3). Mitigation: A5 stays on one seat unless a bank and the context-regime test both support a move.
- **CPU contention** degrading judge seats and Du's own hubs. Mitigation: written thread budgets, contention test with Du running before P4.
- **Write-only shadow log.** Mitigation: scorer is part of P2, not a later phase.
- **Metric confounds** from several changes at once. Mitigation: one prompt per change.
- **Bank leakage.** Reusing the same small banks for selection and for the promotion gate overfits. Mitigation: hold out part of each bank; grow banks from labelled live rows.
- **Hidden callers.** `model_client.py` has 18 AST listeners (UDMS). Mitigation: run `udms_get_change_dossier` on it before the P1 edit.

## 8. Founder answers (2026-11-19, ruled in /decide: D-0872 voice, D-0873 hot GPU, D-0874 Bonsai CPU, D-0875 dreamer, D-0876 promotions)

1. **Voice seat:** default only, not a standing rule. A5 prompts stay on one seat unless a bank win AND the six-context voice test both support a move.
2. **Hot GPU:** one resident model. No second resident model.
3. **Bonsai-2 CPU seat:** 16 threads, background-only prompts (sleep synthesis, defeater and pursuit judging) while Du is running. No synchronous callers.
4. **Dreamer seat (`:11442` yi:34b):** protected for now; revisit after the first moves land.
5. **Rulings:** each per-prompt promotion gets its own `/decide` ruling with its own defeater. No batch rulings.

Still to settle: none of the five. Open items are in the Current State below. Each answer needs a defeater when it is entered in `/decide` (e.g. answer 4 revisits once the first two prompt moves have a read).

## Current State — verified 2026-11-19

Draft only. Evidence available: `docs/lab/du_prompt_model_benchmark_results_2026-11-18.md` (screening, inferred), F-5117 (limits), F-5118 (Bonsai-2 CPU).
Not done: any code, the table, the lints, a contention test with Du up, Bonsai-2 blind A4/A5 scoring, full J-2996 Pursuits bank.
