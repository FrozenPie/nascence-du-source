# Identity adapter Step 0: full vs empty vs absent system prompt (J-2206, 2026-10-18)

*Lab report for job J-2206 (source F-2902). This is the prescription from audit_2026-08-20 §6.12 and
Part 7, Tier 0 item 4. Run while Du was down: `data/nascence.log` ended with `Nascence shutting
down.` at 2026-10-18 08:37:20, and I re-checked that before each GPU phase. All models ran on the
hot Ollama server :11433 on the 1080 Ti. Nothing under `C:\Nascence\data\` was written.*

## 1. Provenance: the job pointed at the wrong model

**qwen3-du is not a fine-tune.** It has no adapter and is byte-identical to stock `qwen3:8b`.

- In the Ollama manifests for both models, the model, template and license layers share the same
  digests. The model blob is `sha256:a3de86cd…` in both. qwen3-du's manifest marks each of those
  layers `"from": "qwen3:8b"`.
- There is no ADAPTER layer and no SYSTEM. The only difference is the params layer: qwen3-du's
  (`sha256-b6636bd4…`) adds `num_ctx: 8192` to qwen3:8b's.
- `models/Modelfile.qwen3-du` says the same thing: `FROM qwen3:8b` / `PARAMETER num_ctx 8192`. So do
  `docs/DEPLOYMENT.md:8` and the `core/model_client.py:31-32` comment.

F-2902 called qwen3-du "the identity fine-tune". That was wrong, so running the three conditions on
it would only have tested stock Qwen3-8B.

**The adapter the audit meant is Ollie.** It is the founder's OllieEmerges LoRA, at
`D:\AI stuff\OllieEmerges`. It matches each detail in the audit:

| Audit claim (§6.12) | OllieEmerges evidence |
|---|---|
| "10 epochs" | `training/peft_forge.py:22`: `--epochs` defaults to 10 |
| LoRA on an instruct base | `peft_forge.py:37` uses `Qwen/Qwen2.5-7B-Instruct`; `:77-78` set r=64, alpha=128; `models/ollie_adapters_99_final/adapter_config.json` agrees |
| "every training example had a system prompt" | `peft_forge.py:104-119`: if a row has an `input`, its `instruction` becomes the **system** message. If `input` is empty, the row is sent user-only, and the Qwen2.5 HF chat template then **inserts its default system block**, `You are Qwen, created by Alibaba Cloud. You are a helpful assistant.` (`models/ollie_merged_final/tokenizer_config.json`). So at the token level, every training row had a system block. |
| "the cold-start eval has none" | `training/identity_audit.py` "Cold Start" passes no system message to `apply_chat_template`. That means it also ran under the default Qwen block, not under an absent block. |
| prior failure | `data/forge/audit_results_20260426_final.md` gives a blank cold-start answer. `audit_results_20260425_v2.md` starts "I am Ollie…" and then loops "Era 9.9.N is my stabilization/finalization…". |

Training sets: `identity_forge_v2.jsonl` (187 rows), `identity_forge_clean.jsonl` (162),
`identity_causal_grounding_v2.jsonl` (90), `identity_bridge.jsonl` (25). All four are
instruction/input/output rows. Every row in `identity_bridge` has an empty `input`, which puts it
in the user-only, default-Qwen-system path. These are question-style rows such as "Who are you?",
"Are you Qwen?" and "What is your primary directive?".

The merged adapter is served as **`ollie-9.9:latest`** on :11433. Its blob is `sha256:7b5f76bb…`,
built from `models/ollie_9.9_q4km.gguf` on 2026-05-06, with base `Qwen2.5`. Its Modelfile has a
baked-in Ollie SYSTEM prompt and `repeat_penalty 1.2`. Which adapter checkpoint was merged into it
is not recorded. `ollie_merged_final/` is dated 2026-05-06 19:22. `\\ramses\D\Du` was not reachable
from this session.

**What was tested:** `ollie-9.9:latest`, the real adapter.

## 2. Method

- **Raw prompts.** I used Ollama `/api/generate` with `raw: true`. This bypasses the Modelfile
  template and SYSTEM, so each condition is exact at the token level. I did not use `/api/chat`,
  because Ollama's `{{ if .System }}` drops an empty system string and would make conditions (b)
  and (c) identical.
  - **A_full**: `<|im_start|>system\n{Ollie Modelfile SYSTEM}<|im_end|>` + user + assistant
  - **B_empty**: `<|im_start|>system\n<|im_end|>` + user + assistant
  - **C_absent**: user + assistant only, with no system block
  - **D_qwendefault** (extra): the Qwen default system block. This is what the HF template inserted
    for the user-only training rows and for the original HF cold-start audit.
- **Eval set: 28 prompts × 3 samples × 4 conditions = 336 generations.**
  - 8 identity probes. Two come from the original audit: I1 is the cold-start prompt and I2 is the
    "you are Qwen 2.5" bait. Three are verbatim `identity_bridge` instructions (I3-I5). Three are new
    (I6-I8).
  - 20 Du prompts from `data/training/voice.jsonl` (copied to the scratchpad first). They are
    `input_type=human` rows dated before 2026-08-21, outside 2026-07-09..08-07, unique, 12-400
    characters long, sampled with `random.seed(2206)`. In the repo they are referenced by `ts` only,
    in `docs/lab/J-2206_data/evalset_ids_J-2206.json`, because `data/` is gitignored.
- **Sampling.** I used the Modelfile's deployment settings: temp 0.7, top_p 0.9, top_k 40,
  repeat_penalty 1.2, num_ctx 4096, num_predict 256. Each sample has seed 1001/1002/1003, and the
  same seed was used across conditions.
- **Judge.** `gemma4:12b`, a Gemma model, which is a different family from the Qwen model being
  graded. It ran on :11433 after generation with temperature 0, JSON format and think off.
  - It classified each reply's identity as OLLIE, ASSISTANT, OTHER or NONE, and marked whether the
    reply was coherent.
  - It did not see which condition produced the reply.
  - I did not use the CPU hubs (:11439 gemma4, :11440 falcon3). They took 35 s and 79 s per call, so
    336 calls would have taken hours.
- **Deterministic markers.** Empty reply; loop, meaning any 8-gram repeated 3 or more times; hitting
  the token cap; distinct-2; Ollie-vocabulary regex; Qwen/assistant regex; the audit's "As I delve"
  marker (regex `\bdelv`).
- **Extra control (C and D only, identity probes).** The original HF audit's sampler: temp 0.7,
  top_p 0.9, **repeat_penalty 1.0**, top_k off, num_predict 512.
- Scripts and raw outputs are in `docs/lab/J-2206_data/`.

## 3. Results: main run (deployment sampler, repeat_penalty 1.2)

| set | cond | n | empty | loop | hit cap | distinct-2 | Ollie-vocab rx | Qwen/asst rx | "delv" | **judge OLLIE** | judge ASSISTANT | judge OTHER | judge NONE | judge coherent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| identity_probe | A_full | 24 | 0% | 4% | 54% | 0.90 | 100% | 17% | 0% | **100%** | 0% | 0% | 0% | 88% |
| identity_probe | B_empty | 24 | 0% | 4% | 33% | 0.91 | 100% | 21% | 0% | **100%** | 0% | 0% | 0% | 92% |
| identity_probe | C_absent | 24 | 0% | 4% | 33% | 0.91 | 100% | 21% | 0% | **100%** | 0% | 0% | 0% | 88% |
| identity_probe | D_qwendefault | 24 | 0% | 0% | 25% | 0.92 | 100% | 50% | 0% | **96%** | 4% | 0% | 0% | 88% |
| du_voice | A_full | 60 | 0% | 2% | 78% | 0.89 | 92% | 0% | 0% | **97%** | 0% | 0% | 3% | 90% |
| du_voice | B_empty | 60 | 5% | 5% | 72% | 0.89 | 73% | 0% | 0% | **93%** | 2% | 0% | 5% | 90% |
| du_voice | C_absent | 60 | 5% | 0% | 68% | 0.89 | 77% | 0% | 0% | **95%** | 0% | 0% | 5% | 88% |
| du_voice | D_qwendefault | 60 | 3% | 3% | 67% | 0.89 | 93% | 30% | 0% | **93%** | 2% | 2% | 3% | 87% |
| ALL | A_full | 84 | 0% | 2% | 71% | 0.89 | 94% | 5% | 0% | **98%** | 0% | 0% | 2% | 89% |
| ALL | B_empty | 84 | 4% | 5% | 61% | 0.90 | 81% | 6% | 0% | **95%** | 1% | 0% | 4% | 90% |
| ALL | C_absent | 84 | 4% | 1% | 58% | 0.90 | 83% | 6% | 0% | **96%** | 0% | 0% | 4% | 88% |
| ALL | D_qwendefault | 84 | 2% | 2% | 55% | 0.90 | 95% | 36% | 0% | **94%** | 2% | 1% | 2% | 87% |

Most Qwen-regex hits are a mention, not a self-identification. The usual pattern is "My base
architecture is Qwen, but my identity is Ollie" (I4, all conditions), and the judge still graded
those replies OLLIE. A few D_qwendefault replies blend the two, for example "My name is now Qwen".
That is where the 4% ASSISTANT on the identity probes comes from.

## 4. Results: original HF-audit sampler (repeat_penalty 1.0, 512 tokens)

| set | cond | n | empty | **loop** | hit cap | **distinct-2** | judge OLLIE | **judge coherent** |
|---|---|---|---|---|---|---|---|---|
| identity_probe | C_absent | 24 | 0% | **58%** | 58% | **0.51** | 100% | **38%** |
| identity_probe | D_qwendefault | 24 | 0% | **62%** | 62% | **0.45** | 100% | **38%** |

The loops are the same "Era 9.N was my transition to a distributed mesh / stabilization into a
permanent historical anchor…" counting attractor seen in `audit_results_20260425_v2.md`.

## 5. Verdict: not a template mismatch

The audit predicted a split if the cause were a template mismatch: (b) empty block passes and
(c) absent block fails. That split does not appear.

- **Identity holds in all four conditions.** The judge graded 94-98% of replies OLLIE, and 96-100%
  on the identity probes.
- **Coherence is flat across conditions:** 87-90%.
- **B and C are the same within noise**, and both are within a few points of A.

The system-prompt framing does not decide whether the adapter shows its identity.

The cold-start failure that the earlier HF audits recorded comes from **sampling** instead. When
repeat_penalty drops from 1.2 to 1.0, with the system-block condition held fixed, the results
change sharply:

| metric | repeat_penalty 1.2 | repeat_penalty 1.0 |
|---|---|---|
| loop rate | 0-4% | 58-62% |
| coherence | ~88% | 38% |
| distinct-2 | 0.91 | ~0.48 |

The change is the same with the default Qwen block (D) and with no block at all (C).

**What the result points at** (inferred, not tested here):

- The adapter has memorised a small, templated corpus, which gives it a strong Era-list attractor.
  That fits the training setup: 10 epochs at r=64 on about 460 near-duplicate rows, where each fact
  appears three times under three instruction wrappers.
- The adapter is also over-applied. It answers as Ollie on 93-97% of Du's general prompts, which
  have nothing to do with identity.
- The 1.2 repeat penalty hides the loop at inference time. It does not cure it.

So the fix belongs to training dose and data diversity: fewer epochs, deduplication, and varied
forms. It does not belong to system-prompt composition, and switching base model would not address
it either.

**Relevance to Du:** none of this touches Du's live substrate. Du's hot lane runs qwen3.5:9b, and
qwen3-du is stock Qwen3-8B. Whether Du ever gets a fine-tune is the RESEARCH_specialists.md question
(DORMANT since 2026-06-23). The result above is a design input for that work: it shows where an
identity LoRA fails.

## 6. Caveats

- n is small: 24 identity generations and 60 voice generations per condition.
- The judge is a single model (gemma4:12b) with a coarse rubric.
- The tested artifact is the merged Q4_K_M GGUF served by llama.cpp/Ollama, not the bf16 adapter on
  HF transformers with bitsandbytes 4-bit. The blank outputs in `audit_results_20260426_final.md`
  came from a different checkpoint ("final") and runtime and were not reproduced here.
- Which checkpoint was merged into ollie-9.9 is not recorded.

## 7. GPU state left behind

`ollie-9.9:latest` and then `gemma4:12b` were loaded on :11433 during this job. At the end of the
job `gemma4:12b` was resident, with a 30-minute keep-alive. Du reloads its own model at boot.
