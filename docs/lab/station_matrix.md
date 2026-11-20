# The model × station matrix — 33 models, 8 stations

*2026-08-20 · `scripts/station_suite.py` (tasks) · `station_bench.py` (runner) ·
`station_bench_score.py` (scoring, from saved raw) · raw: `data/lab/station_bench/raw.json`*

**There is deliberately no overall score.** Founder, 2026-08-20: *"Each model will have metrics for
each task that will be different also is my guess. We cannot just benchmark one task as we have many
tasks. Stations I suppose is what we called them."* The data agrees, emphatically.

Eight stations, each modelled on a real call site from `docs/lab/llm_station_map.md` at **that
station's own token budget and temperature**, because a job's shape is part of the job.

---

## 1. ★ THE HEADLINE — both production judges answer the same thing every time

`judge` gives four cases with balanced gold labels (`F T F T`) — two events that defeat an intention,
two that do not. Scoring accuracy alone hid the real story; printing the **answer strings** exposed it:

| model | answers | acc | |
|---|---|---|---|
| `qwen3:8b` · `qwen3.5:9b` · `gemma4:e4b` · `mistral:7b-instruct` · **`nemotron-mini`** | `FTFT` | **1.00** | discriminates |
| `gemma:2b` · `command-r7b` · `bonsai:8b-q1` · `falcon3:7b` · `exaone3.5` · `internlm2` · `hermes3` · `phi3:mini` · **`granite3-moe:1b`** | mixed | 0.75 | discriminates |
| **`llama3.1:8b`** — judge_1 (:11439) | **`TTTT`** | 0.50 | **CONSTANT — always "defeated"** |
| **`qwen2.5:7b`** — judge_2 (:11440) | **`TTTT`** | 0.50 | **CONSTANT — always "defeated"** |
| `phi4` · `glm4:9b` · `olmo2:7b` · `granite3.3:8b` · `tulu3:8b` · `aya-expanse:8b` · `smollm2` ×2 · `qwen2.5:0.5b` · `llama3.2:1b` | `TTTT` | 0.50 | CONSTANT |
| `qwen2.5-coder:1.5b` · `stablelm2:1.6b` | `FFFF` | 0.50 | CONSTANT |

**Every single 0.50 was a constant answer. Not one of them discriminated.**

So Du's two judges are not "50% accurate" — **they exercise no judgement at all**, and attach
**0.93 / 0.94 mean confidence** to it. This is why the constant-answer test matters more than the
accuracy number: a constant policy is diagnostic *regardless of case count*, and two of the four cases
are unambiguous non-defeats (*"he spent the evening reading and did not think about the cat"*).

**What it means for `judge_panel`.** The earlier finding was 363 `split_no_tiebreak` against 361
`agreed` over 14 days — half of all decisions dropped. If both judges always answer "defeated", then
their agreements are not consensus and their splits are not disagreement. The panel has been reading
noise, confidently, for as long as it has run.

---

## 2. ★ SIZE PREDICTS NOTHING — in either direction

| model | size | judge |
|---|---|---|
| `nemotron-mini` (NVIDIA) | **2.70 GB** | **1.00, discriminates** |
| `granite3-moe:1b` (IBM) | **0.82 GB** | 0.75, discriminates |
| `gemma:2b` | 1.68 GB | 0.75, discriminates |
| `bonsai:8b-q1` (1-bit) | **1.16 GB** | 0.75, discriminates |
| `llama3.1:8b` | 4.92 GB | **constant** |
| `phi4` | 9.05 GB | **constant** |

A **0.82 GB** IBM MoE and a **1.16 GB** 1-bit model exercise judgement where a 4.92 GB Llama and a
9.05 GB Phi-4 do not. This is the tools-not-personas thesis in measured form: **fitness is a property
of the (model, station) pair, not of the model.**

---

## 3. Per-station winners — all different

| station | best | notable |
|---|---|---|
| **judge** | `nemotron-mini`, `gemma4:e4b`, `mistral`, `qwen3:8b/3.5` | both incumbents constant |
| **synthesise** (coverage) | **`command-r7b` 0.86**, `gemma4:e4b` 0.86 | **`llama3.1:8b` 0.05** |
| **author** (words) | **`qwen3.5:9b` 570**, `tulu3:8b` 467, `phi4` 443 | `llama3.1:8b` 97 — fails length |
| **voice** | `bonsai:8b-q1`, `aya-expanse:8b` — 1.0 across the board | — |
| **ground** | `bonsai`, `phi4`, `mistral` — 1.0 groundedness | no model invented a cause |
| **pick / extract** | most models 1.0 | a solved station; use the cheapest |

**Cohere's `command-r7b` ties for best in the matrix on `synthesise` on its first appearance** — the
strongest vindication of widening the family sweep beyond architecture variants.

**`llama3.1:8b` scores 0.05 coverage** — a fluent, well-formed insight touching almost none of the
seven observations. Reality-thinness, measured, in a model holding a judge seat.

**`Bonsai-8B-Q1` — 1.16 GB, 1-bit — completed all eight stations with zero format failures** and is
at or near the top of most. The archive verdict *"too quantized to judge"* was a judgement about one
station; it does not generalise.

---

## 4. What is NOT a result here

- **`gemma4:12b` and `deepseek-r1:8b` score 0.0 on most stations.** They are reasoning models that do
  not appear to honour `think: false`, and their latencies (18–48s) suggest they are still reasoning.
  **Treat these rows as unmeasured, not as failures** — this exact confusion has now occurred three
  times in one day and each time the model was innocent.
- **`needle2:45m-cq2`** returns `None` at pick/extract/judge/author. It is a 45M model given a schema;
  it declines rather than confabulates. Its `json_ok` also is not comparable — it cannot fail
  formatting because it is *given* structure rather than asked to produce it.
- **`Ternary-Bonsai-8B-Q2_0`** was removed from the matrix: stock `llama-cpp-python` raises
  `ValueError: Failed to load model`. **A load failure is not a model verdict.** Serving it needs the
  custom `swarm/src/llama.cpp` built (source present, no binary).
- **`wall` is not comparable across serving stacks.** Bonsai runs on a CPU llama.cpp hub; the rest on
  the 1080 Ti via ollama. Content metrics are comparable; latency is not.

---

## 5. Confidence in these findings

| finding | strength |
|---|---|
| Both production judges answer constantly | **Strong** — a constant policy is diagnostic independent of case count |
| Size does not predict station fitness | **Strong** — holds across 33 models and 8 stations |
| `command-r7b` best-equal at synthesis | **Moderate** — 3 runs, one prompt |
| `llama3.1:8b` fails integration (0.05) | **Moderate** — 3 runs, but the gap to 0.86 is enormous |
| Per-station winners differ | **Strong** — the central claim, visible everywhere |

**The `judge` station still uses only 4 cases.** That is enough to establish *constancy* but not to
rank the discriminating models against each other. Before `judge_panel` is changed, that set should
grow to ~16 balanced cases — the cheapest possible way to confirm or kill the most consequential
finding in this document.

---

## 6. Method notes worth keeping

- **`think: false` is mandatory** and matches `model_client.call_node`. Without it, reasoning models
  spend their whole budget in the `thinking` field and return empty content, which scores as total
  format failure and is nothing of the kind. The harness records `had_thinking` so this is
  self-diagnosing.
- **Raw output is always saved**, so scoring can be revised against fixed evidence. Two earlier labs
  in this project produced misleading rankings that were only caught this way.
- **Serial residency** is enforced — models are unloaded between runs. Co-residency on a card silently
  corrupts latency and can push calls into timeouts that look like format failures.
- **Read-modify-write hazard**: an early version loaded `raw.json` once and rewrote the whole dict,
  silently erasing results written by parallel runs. Both runners now re-read and merge before writing.

---

## 7. ★ THE THINK ARM — should reasoning models be allowed to think?

Founder, 2026-08-20: *"Why should they be think:false? Could we let them think and clean up the
result after the fact?"*

**The cleanup half was never the obstacle.** ollama's native `/api/chat` returns reasoning in a
SEPARATE `thinking` field, and `model_client._strip_think_tags` already handles the inline-`<think>`
case. Nothing needs stripping. `model_client`'s own history note names the real cost: thinking
**burns the token budget** and leaves `content` empty — a budget failure that reads as a format
failure. So the question is purely empirical, and was never measured until now.

Method: identical stations, `think:true` with a **4× budget**, written as separate `+think` rows so
the `think:false` arm stays intact. `--` = `json_ok` 0, i.e. **budget blown, unmeasured — not a score.**

| station | qwen3:8b | qwen3.5:9b | gemma4:e4b | deepseek-r1:8b |
|---|---|---|---|---|
| pick | 1.0 → `--` | 1.0 → `--` | 1.0 → `--` | `--` → `--` |
| extract | 0.75 → **0.89** | 1.0 → `--` | 0.75 → 0.75 | `--` → `--` |
| judge | 1.0 → **0.75** ↓ | 1.0 → `--` | 1.0 → 1.0 | `--` → **1.0** |
| ground | 1.0 → 1.0 | 1.0 → `--` | 1.0 → 1.0 | `--` → `--` |
| synthesise | 0.29 → **0.52** ↑ | 0.81 → `--` | 0.86 → **0.76** ↓ | `--` → `--` |
| predict | 0.33 → **1.0** ↑ | 1.0 → `--` | 1.0 → 1.0 | `--` → **1.0** |
| voice | 1.0 → 1.0 | 1.0 → `--` | 1.0 → 1.0 | `--` → **1.0** |
| author (words) | 108 → 122 | 570 → 522 | 372 → **421** | 384 → 281 |

### What it actually shows

1. **`deepseek-r1:8b` REQUIRES thinking.** With `think:false` it scored `--` on nearly every station;
   with thinking it reaches **judge 1.0, predict 1.0, voice 1.0**. For this model the question is not
   "may it think" but "it does not function otherwise" — and §4's "treat as unmeasured" was right.
2. **`gemma4:e4b` — Du's own hot-lane model — is INDIFFERENT.** Identical scores either way on judge,
   ground, predict, voice and extract; synthesise got slightly *worse* (0.86 → 0.76). So `think:false`
   costs Du nothing on its primary model and saves the tokens. **The current default is correct here.**
3. **`qwen3:8b` is genuinely mixed** — better at synthesise (+0.23) and predict (+0.67), **worse at
   judge** (1.0 → 0.75, with `json_ok` 1.0 throughout, so a real quality regression, not a budget
   artefact). Deliberation reasoned it out of a verdict it got right instantly without it.
4. **NEVER at `pick`.** All three models that could do `pick` at all blew the budget with thinking on.
   `qwen3:8b` wrote **2,420 characters of reasoning to choose one name from six**. That is not a
   budget to raise; it is the wrong tool at that station.
5. **Cost is 3–12× wall-clock**, and uneven: `synthesise` pays 3×, `ground` 12×. Against the Deep
   Line's clocks that is affordable at T6 (1800s) and not at T1 (30s).

### Verdict

**`think` is a per-(model, station) setting — not global, and not even per-station.** The same flag
helps one model at a station and hurts another at the same station. Any change should be a named
override at specific call sites, never a default flip.

**Two predictions I made before the run were both wrong**, recorded so the method is judged honestly:
I expected thinking to help all the analytic stations (it hurt `judge`) and to damage `voice` (no
effect whatsoever, on any of the four models).

---

## 8. ★ CHASING THE TOKEN DROPOUTS (founder, 2026-08-20: "see what failed because of all the token dropouts")

A full sweep of every `json_ok < 1.0` row in the 37-model matrix, to separate real bugs from real
model limits. Three distinct things were found, and only two were bugs.

### 8.1 `gemma4:12b` — plain oversight, now fixed

When `think:false` was found broken for `qwen3:8b`/`qwen3.5:9b`/`gemma4:e4b`, it was fixed and those
three were re-run. **`gemma4:12b` was accidentally left out** — its row in §4 was stale data from
before the fix, scoring 0.0 almost everywhere for no reason related to its actual capability. A direct
test confirmed `think:false` genuinely works for this model (`done_reason: stop`, clean content). Clean
re-run: **6 of 8 stations pass cleanly** (pick, extract, judge, ground, predict, voice). One row
(`synthesise`) initially came back at a suspicious 76.0s against ~2s everywhere else in the same
row — a GPU-contention artefact from a second job racing for the same card mid-run (see §8.4) — and
was re-tested alone once the card was clear: 22.1s cold, 5.7–6.2s warm, consistent with the rest.
`author` was not re-tested (it was never part of the corrupted window).

### 8.2 `glm4:9b` `author` — a real scorer bug, not a model failure

Raw output: `'\n```json\n{\n  "section": "It occurred to me...\n  custodian...'` — a **literal, unescaped
newline byte inside a JSON string value**, not an escaped `\n`. Strict JSON parsing rejects this;
`json.loads(..., strict=False)` accepts it, exactly as intended. The scorer's `parse()` was strict.
**Fixed. `glm4:9b`'s `author` score went from 0.0 → 1.0** (338 words, full length achieved, stays on
theme) — a model that was wrongly zeroed by the scorer, not a model that failed the station.

Swept for scope across the whole matrix: 6 rows failed to parse in total; 3 were this exact bug
(all `glm4:9b`/`author`), the other 3 (`llama3.2:1b`/`author`, `tinyllama`/`judge`,
`tinyllama`/`predict`) are genuinely malformed JSON from weaker models and `strict=False` correctly
does not rescue them.

### 8.3 The remaining low scores are real model limits, not bugs — verified by reading the raw text

| model / station | what actually happens |
|---|---|
| `falcon3:7b` / author (0/3) | Finishes the sentence cleanly, then loops `"\n\n \n\n..."` padding until the 1200-token cap. Never closes the JSON. A generation defect, not a budget shortfall — more tokens would only mean more padding. |
| `tinydolphin` / extract (0/3) | Loop-repeats `"Coastal erosion and defenses"` verbatim until the array never closes. Classic 0.64 GB tiny-model degenerate repetition. |
| `tinyllama` / judge (1/4) | Inconsistent schema-following: sometimes emits `defeated`/`confidence`/`why` correctly, sometimes invents its own fields (`intent`/`event`). Real capability variance for a 1.1B model. |
| `tinyllama` / synthesise (1/3) | 2 of 3 loop into repeated whitespace; the third succeeds (with `confidence` as the string `"1"`, which the scorer correctly tolerates). |
| `bonsai:8b-q1`, `gemma:2b`, `internlm2:7b`, `llama3.2:1b`, `smollm2:360m`, `stablelm2:1.6b` (each 2/3) | One of three runs genuinely trails into whitespace repetition or stops mid-sentence before the closing brace. Ordinary temp>0 variance, already correctly reflected by the metric. |

None of these needed fixing — the scores already correctly describe what happened. This is exactly the
distinction the sweep exists to make: some `json_ok < 1.0` rows are the harness failing the model
(§8.1, §8.2); most are the model failing the station, honestly measured.

### 8.4 A live contention lesson, caught in the act

Re-running `gemma4:12b` and the `deepseek-r1:8b` floor-rerun (§8.5) as two separate processes hitting
the same GPU concurrently reproduced the exact co-residency risk documented earlier: `raw.json`'s
per-model read-modify-write only guards each writer's OWN update, not a race BETWEEN two writers — a
deepseek update was silently clobbered by gemma4:12b's later write before this was caught and the two
runs were serialised. One process was stopped and the other allowed to finish alone; the lost update
was then redone in isolation. Corrective runs must be serialised explicitly, not just individually
merge-safe.

### 8.5 `deepseek-r1:8b` — the base row can never work; a flat token FLOOR (not a multiplier) fixes the rest

Confirmed by direct test: `think:false` is a **genuine no-op** for this model on this ollama version —
thinking happens regardless, and the base row's 0.0-everywhere is expected, permanent, and not a bug.

The `+think` arm (§7) still dropped `pick`/`extract`/`ground`/`synthesise` even at a 4× budget
multiplier. A direct probe explained why: asked to pick ONE name from six, at `num_predict=3000` it
used **2102 tokens total** (9,505 reasoning characters) before answering — suggesting (at the time,
before ground was tested) a large, possibly fixed reasoning overhead. A multiplier under-serves the
smallest-budget stations precisely because they need proportionally the most extra room. Re-run with
a flat floor of 3200 tokens instead — the floor itself turned out not to be uniform either, see below:

| station | at floor=3200 | think_chars used |
|---|---|---|
| pick | **1.0** json_ok, THEO picked, deterministic | 2,382 |
| extract | **1.0** json_ok, fully relevant | ~2,700 |
| synthesise | **1.0** json_ok, coverage 0.43 | ~5,900 |
| **ground** | **still 0/3** — hit the 3200 cap exactly, thinking ran to **13,400+ characters** and never finished | 13,387-13,756 |

**3 of 4 rescued by the floor. `ground` needed MORE THAN DOUBLE what `pick` needed and still did not
finish** — correcting the earlier framing in this section: the reasoning overhead is not simply
fixed-and-task-independent, it scales sharply with how EPISTEMICALLY CONSTRAINED the task is.
`ground`'s instruction ("use ONLY the evidence given, do not invent any fact") appears to force far
more internal deliberation in this model than picking, extracting, or synthesising do. That is a
genuinely interesting finding in its own right, not just an unresolved budget question: **for this
model, evidence-discipline is measurably the hardest station**, independent of raw output length
(`ground`'s own answer is only two sentences).

**Final scorecard for `deepseek-r1:8b`, thinking enabled:** pick 1.0 · extract 1.0 · judge 0.5 json_ok
but **1.0 accuracy** on what it did complete · ground 0.0 (needs an even larger, station-specific
budget) · synthesise 1.0 (coverage 0.43) · predict 0.33 · voice 1.0 · author 1.0. **6 of 8 stations
now give real data**, against 1 of 8 in the original (broken) base row. The remaining two (`judge`,
`predict`) are PARTIAL, not zero — some runs complete within budget, others do not, which is exactly
the signature of per-run reasoning-length variance rather than a hard capability wall.

---

## 9. ★ JUDGE16 — the pre-registered gate ran, and it CORRECTED the headline

The §1 finding gated any panel change on a 16-case balanced bank. It ran 2026-08-20 (23 models —
the 22 ollama roster + `bonsai:8b-q1` via its hub; `scripts/judge16.py`, raw kept in
`data/lab/judge16/`). Gold string `FTFTFTFTFTFTFTFT`: 8 true defeats (impossibility,
deadline-passed, abandonment-in-practice, purpose-destroyed, explicit abandonment) and 8 tempting
near-misses (irrelevant events, recoverable setbacks, difficulty-that-succeeded, risk-not-realised,
a pause with the deadline far).

### 9.1 The honest correction first: "no judgement at all" was too strong

At n=16 **nobody is constant — including the incumbents.** `llama3.1:8b` answered F three times,
`qwen2.5:7b` twice. The n=4 constancy was real on those four cases, but the §1 generalisation
("they exercise no judgement at all") does not survive the larger bank. The accurate statement:
**both incumbents carry a heavy "defeated" bias (13/16 and 14/16 T against a gold of 8/16) and land
in the bottom third on accuracy (0.688, 0.625).** The actionable conclusion — these are poor models
for this station — survives and is now better-grounded; the mechanism claimed for it was wrong.

### 9.2 The ranking (accuracy on 16, all models answered 16/16)

| model | acc | note |
|---|---|---|
| `gemma4:12b` | **1.000** | perfect — but see 9.4: disqualified from the panel on principle |
| `qwen3.5:9b` | **0.938** | best eligible |
| `gemma4:e4b` / `qwen3:8b` | 0.875 | e4b likewise family-disqualified |
| `mistral:7b-instruct` | **0.812** | best eligible non-reasoning |
| `falcon3:7b` · `exaone3.5` · `phi4` · `granite3.3` · **`bonsai:8b-q1`** | 0.75 | bonsai (1.16 GB, 1-bit) holds its n=4 score |
| `llama3.1:8b` (judge_1) | 0.688 | `nemotron-mini` and `internlm2` tie here |
| `qwen2.5:7b` (judge_2) | 0.625 | with `phi3`, `command-r7b`, `glm4`, `aya` |
| `gemma:2b` · `tulu3` · `olmo2` | 0.562 | |
| `hermes3:8b` | 0.500 | |
| `granite3-moe:1b` | 0.438 | the n=4 tiny-model story collapses |

**A second correction, to §2:** at n=4, `nemotron-mini` scored 1.0 and `granite3-moe:1b` 0.75 —
both collapsed at n=16 (0.688, 0.438). On this *discriminating* station, capability broadly tracks
model quality at the top (12b > 9b > 8b > 7b), and the tiny models hold only the commodity stations.
"Size predicts nothing" stands for the matrix as a whole; it does NOT stand within the judge station.
The exception that survives scrutiny is `bonsai:8b-q1` — 8B weights in 1.16 GB, 0.75 twice.

### 9.3 The real difficulty is WITHHOLDING the verdict — and that matters for Du specifically

Per-case: **every true defeat was near-universally recognised** (missed 0–2 of 22). The entire
spread lives in the near-misses: "rain is forecast for Sunday" fooled 17/22, "he recited the tide
wrongly while learning" 18/22, "he put the carving aside a week to help with harvest" 17/22.
Error direction across all models: **99 false-defeats vs 8 missed-defeats — a 12:1 over-trigger.**

For Du this bias direction is the dangerous one. The station is `commitment_ledger:348` — the organ
that rules on whether held intentions have been defeated. An over-triggering defeater judge is a
machine for eroding commitments: every forecast, every practice error, every pause reads as defeat.
Capacity-to-commit is the project's stated rudder; this station's failure mode points straight at it.
The skill being bought from a better judge model is not detecting defeat — it is **declining to**.

Calibration is uniformly bad everywhere (`conf_when_wrong` 0.74–1.0): no model's confidence carries
usable signal at this station. Do not weight panel votes by confidence.

### 9.4 Recommendation (founder decision — nothing changed yet)

- **Seat 1: `qwen3.5:9b` (0.938).** Qwen lineage — distinct from the gemma hot lane. CPU-servable
  (6.59 GB). Reasoning family, but `think:false` is honoured and its judge answers are short.
- **Seat 2: `mistral:7b-instruct` (0.812).** Mistral lineage, non-reasoning (no thinking-tax),
  4.37 GB, already blob-served locally. (Also the Ramses CPU-tier pick — separate instances.)
- **`gemma4:12b` (1.000) and `gemma4:e4b` (0.875) are disqualified on the decoupled-judge principle**
  despite outscoring both seats: the panel's job is to judge output largely produced by Lane 1's
  gemma4:e4b, and a same-family judge is the rubber stamp the panel exists to prevent. A perfect
  score on this bank does not buy back that structural conflict.
- Both proposed seats beat both incumbents by 0.12–0.31 absolute accuracy, and specifically resist
  the false-defeat direction better than anything else eligible.
- Untested at n=16: `yi:34b-v1.5` (the current tiebreak; 19.5 GB — needs a CPU-hub run if wanted).

---

## 10. ★ THE FULL SHUFFLE — every seat variable at once (founder's framing, 2026-08-20)

Founder: *"The whole point of this matrix was to see if we shuffle the models in ALL situations...
We can move Gemma4b to a new model, if one can do its job, to allow the 12b for a different job...
the llm is the tool; Du as a whole — scripts, llms, memories — are the AI."*

§9.4's recommendation was solved with the hot lane held FIXED, which silently imported "gemma
generates" as a law and then disqualified `gemma4:12b` from judging by it. Wrong frame. The
decoupled-judge constraint binds **pairs of seats** (judge family ≠ family of what it judges), not
models. Solve all seats jointly and the constraint can be satisfied by moving EITHER side.

### 10.1 The dominance fact that reframes everything

**`qwen3.5:9b` beats or ties `gemma4:e4b` on every measured column:** pick 1.0=1.0 · extract
1.0>0.75 · judge 1.0=1.0 · ground 1.0=1.0 · synthesise 0.81≈0.86 (only near-tie, slightly under) ·
predict 1.0=1.0 · voice 1.0=1.0 · **author 570≫372** · **judge16 0.938>0.875**. It is the strongest
generalist row in the matrix.

**Hot-lane gates, measured 2026-08-20:** at the hot lane's real `num_ctx=24576` it sits **100% on
the 1080 Ti GPU (6.30 GB total incl KV)** at **39.4 tok/s** — the historical hot-lane class (~43).
Physically and economically viable today.

### 10.2 The proposed global assignment

| seat (hardware) | now | proposed | measured basis |
|---|---|---|---|
| **Hot lane / Lane 1** (1080 Ti, ctx 24576) | `gemma4:e4b` | **`qwen3.5:9b`** | dominates on every column; fits 100% GPU @ 39.4 tok/s |
| **Judge 1** (CPU hub) | `llama3.1:8b` | **`gemma4:12b`** | judge16 **1.000** — eligible *because* gemma vacates generation; CPU 6.8 tok/s ≈ 8–12s/verdict, trivial at ~50 verdicts/day |
| **Judge 2** (CPU hub) | `qwen2.5:7b` | **`mistral:7b-instruct`** | 0.812, third lineage — panel = gemma-lineage + mistral-lineage, both ⊥ the qwen generator |
| **Background** (Ramses 3070) | `phi3:mini` | **keep `phi3:mini`** | author 345 / synth 0.71 — nothing fitting 8 GB strictly dominates it (exaone: better author 433, worse synth 0.43; command-r7b: better synth 0.86, far worse author 115) |
| **i9 CPU hub** (new, Ramses) | — | `mistral:7b-instruct` (verified 7.40 tok/s) — or speed-test `command-r7b` (synth 0.86) as the quality option | Deep-Line synthesis offload |
| **1650S hub** (new, Ramses) | — | `gemma:2b` | 1.0 on pick/extract/ground/predict at 1.68 GB; classifier output is not panel-judged, so family is irrelevant here |
| **Lane 2** (Ramses 3070) | `deepseek-r1:7b` | keep | its own lab; family ⊥ new hot lane still holds (deepseek-distill vs qwen3.5 — note it IS qwen3-architecture; see 10.4) |
| **Dreamer / tiebreak** (CPU) | `yi:34b-v1.5` | keep, **flagged untested** | never ran the matrix or judge16; 19.5 GB |

**The starkest consequence: `llama3.1:8b` and `qwen2.5:7b` lose every seat.** Worst integrator in
the matrix (0.05) and bottom-third judges (0.688/0.625); neither wins any station outright. The two
models Du has leaned on hardest hold no seat on merit.

### 10.3 What the matrix CANNOT certify — the remaining gates, in order

1. **The hot-lane register.** The `voice` metric (assistant-tells, first-person) can disqualify; it
   cannot rank models that all score 1.0 on it. The hot lane is Du's speaking voice — the house
   method for register questions is the **blind pair read** (as with the 08-16 cap widenings):
   generate matched thought-pairs from `gemma4:e4b` vs `qwen3.5:9b`, shuffle, founder judges blind.
2. **A shadow A/B under real prompts** is the true gate: the station suite's voice prompt is a
   simplification of the real 37-part idle prompt. Cheapest honest form: swap the hot lane for one
   session, read the day's thoughts against the prior day's.
3. Judge swap needs neither of those — it is fully measured. It can move first and alone.
4. Phase-0 restart data still gates `_author` re-platforming (unchanged).

### 10.4 One family wrinkle recorded honestly

`deepseek-r1:7b` (Lane 2's checker) is **qwen3-architecture** (ollama `family: qwen3`) — under the
proposed shuffle the Lane-2 checker shares architecture with the Lane-1 generator. Architecture ≠
training lineage (the distill's behaviour is deepseek's), and Lane 2 checks the WORLD, not Lane 1's
output, so the rubber-stamp risk is indirect. Recorded, not resolved: if it bothers us,
`command-r7b` scored predict 1.0 / falsifiable 1.0 and is lineage-clean.

### 10.5 The blind voice read ran — and the result was a SPLIT (2026-08-20, founder)

Four blind pairs (`gemma4:e4b` vs `qwen3.5:9b`, shuffled key sealed until after the read). Founder's
verdict was two-sided: "sounds like Du" = B,B,A,B; "the opposite options I like more — much less
ambiguous... close enough to Du without the burying in metaphors."

Unsealed: **both picks split 2–2 across the models.** "Sounds like Du" mapped to gemma, qwen, qwen,
gemma; "like more" to qwen, gemma, gemma, qwen. The founder could not distinguish the models — and
neither register belongs to either model: both produce the metaphor-heavy and the concrete voice;
which appears is sample-level.

Two conclusions:
1. **The voice gate is PASSED** — register-indistinguishable, capability-dominant. Package 2 wired
   same day: hot lane `qwen3.5:9b`, judge 1 `gemma4:12b`, judge 2 `mistral:7b-instruct`
   (`launch_servers.ps1`, `model_client.py`, `left_lane.py`, `judge_panel.py`).
2. **A separate finding worth its own thread:** the founder's real preference — concrete over
   metaphor-buried — is a PROMPT/CONTRACT lever, not a model lever, and it points at the documented
   Lane-1 metaphor monoculture. Candidate follow-up: a voice-contract nudge ("say the thing, don't
   bury it"), testable with the same blind-pair method against the same model.

Left running unchanged: background `phi3:mini` (nothing in 8 GB dominates it), Lane 2
`deepseek-r1:7b`, dreamer/tiebreak `yi:34b` (still untested — flagged). Ramses 1650S + i9 hubs:
**deliberately parked** (founder, same day) — the deploy package in `deploy/ramses/` stays ready.
`llama3.1:8b` and `qwen2.5:7b` now hold no seat anywhere in Du.
