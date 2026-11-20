# Research Brief — Trained Specialist Nodes

> **STATUS — DORMANT, long game (not active) [2026-06-23].** The per-node specialist-model plan — one Bonsai
> BitNet base + swappable LoRA adapters per node, successor to the original "cognitive swarm" origin — remains
> **unbuilt**: teacher corpora quietly accumulate (`data/training/<node>.jsonl`) but no adapters are trained or
> wired. The lanes moved instead to **many full models, one per role** (gemma / phi3 / llama / mistral). Kept as
> the long-game optimisation (distilled heads for Emotion/Salience are the highest-leverage first step), NOT an
> active plan. Surfaced by the 2026-06-23 graphify audit as a documented-but-unimplemented concept.

> **2026-06-10 note:** still the long game, and the raw material is now accumulating — every successful node
> call is logged as a teacher example to `data/training/<node>.jsonl` (12 per-node corpora, `core/training_log.py`).
> Substrate is now qwen3-du; node count 15.

*Roadmap 1.0: "Replace prompt-engineered nodes with QAT 1-bit micro-models per function. Same base → compatible latent spaces."*
*Researched 2026-05-30. Status: research, not yet started.*

---

## TL;DR

The naive reading — "replace all 15 nodes with 1-bit micro-models" — is wrong in two ways, and the corrected version is **more achievable than it sounds**:

1. The nodes are not uniform. Some need no LLM at all; only three need real language generation. Segment them.
2. We don't train from scratch and we don't need a separate model per node. **Bonsai is already a BitNet-format ternary model**, so it can be LoRA-fine-tuned directly. The "same base" isn't just for latent compatibility — it means **one base model + tiny swappable adapters**, not ten models.
3. The training data problem is already solved: **the prompt-engineered nodes are the teachers.** Every cycle they run, they generate (input → output) pairs. The scaffold writes its own replacement's training set.

---

## 1. The task, corrected: segment nodes by what they actually need

The fifteen nodes have radically different output complexity. Treating them uniformly is the central mistake.

| Node | Output | Real need | Specialist approach | Difficulty |
|---|---|---|---|---|
| **Emotion** | 8 floats | regression | distilled MLP head OR LoRA | ★ easiest |
| **Salience** | score + few terms + bool | regression + tiny gen | distilled head / small LoRA | ★ easy |
| **Perception** | enum labels + entities + 1 line | classification + short gen | small LoRA | ★★ |
| **Memory Router** | search keys + enum | short structured gen | small LoRA | ★★ |
| **Critic** | bool + bool + corrections | judgment + short gen | small LoRA | ★★ |
| **Executive** | synthesis paragraph | free generation | LoRA on shared base | ★★★ |
| **Voice** | styled prose | free generation | LoRA on shared base | ★★★ |
| **Reflection** | long internal prose | free generation | LoRA on shared base | ★★★ hardest |
| Consolidation | wisdom + patterns | free gen (background) | LoRA (low priority) | ★★ |
| Curiosity | questions (background) | free gen (background) | LoRA (low priority) | ★★ |

**The insight:** Emotion, Salience, and arguably Perception don't need a generative LLM at all. Their output is essentially a fixed-shape vector. A distilled regressor/classifier on top of the embedding we already compute (MiniLM, 384-dim) can produce an emotion vector in **sub-millisecond** time, versus a full 8B forward pass. That's the highest-leverage, lowest-risk win in the entire system.

The free-generation nodes (Reflection, Executive, Voice) are where "1-bit micro-model" genuinely applies — and where the "same base" rationale matters most.

---

## 2. "Same base → compatible latent spaces" — what it really buys

Two distinct benefits, often conflated. Only one is easy.

**Benefit A — one base, many adapters (easy, real, available today).**
If every generative specialist is a **LoRA adapter on the same Bonsai base**, then:
- The base model loads into VRAM **once** (~1.9GB, as now).
- Each node's specialization is a **LoRA adapter of a few MB**, hot-swapped per call.
- Ten "specialist models" cost ≈ one base + ten tiny adapters, not ten full models.
- llama.cpp / the BitNet ecosystem already support adapter loading and hot-swap.

This is a serving-efficiency and quality win available with current tooling. It is the practical meaning of "same base" for the next 6–12 months.

**Benefit B — shared latent space for activation passing (hard, future, Direction stage 6).**
Because adapters share the base's weights and embedding space, intermediate activations from one node are *interpretable* to another — the precondition for the direct latent-state propagation in the Direction section (replacing JSON transport with tensor passing). This is genuinely research-stage and should not be conflated with Benefit A. Keeping one base **keeps the door open** to it; it does not deliver it.

---

## 3. The data problem is already solved — self-distillation from the scaffold

This is the elegant core of the whole plan.

The prompt-engineered nodes running today **are the teacher models.** Every thought cycle, each node produces a (prompt → structured output) pair that is, by construction, in-domain (Jung-specific, this entity's actual conversations). To build a training set we simply **log those pairs.**

```
Emotion node, cycle N:  input="<perception summary>"  →  output={joy:.1, fear:.7, ...}
                        ^ training example, for free, in-distribution
```

After a few weeks of real conversation, each node has hundreds-to-thousands of labelled examples. Then:
- **Distillation (SFT):** train the student (MLP head or LoRA) to reproduce the teacher's outputs. Well-established; specialized students routinely match or beat the generalist teacher on the narrow task ("distilling step-by-step", Google 2023; broadly confirmed 2025).
- **Reward/selection distillation (2025):** keep only high-quality teacher outputs (e.g. Critic-approved cycles, non-truncated drafts) as training targets. The system already scores these — the best-of-N hedge picks the best Reflection; that pick is a clean training label.

**Immediate action this enables:** add per-node output logging *now* (a JSONL append in `NodeBase.run`), so the dataset starts accumulating from the very next conversation. Cheap, safe, and it means by the time we want to train, the data already exists. This is the single most important near-term step.

---

## 4. Tooling state (2026, grounded)

- **Bonsai is already BitNet-format ternary** (our `Ternary-Bonsai-8B-Q2_0` = TQ2_0 ≈ 2.06 bit; `Q1_0` ≈ 1-bit). This is the format the BitNet fine-tuning tools expect — **no conversion, no train-from-scratch.**
- **Tether QVAC "fabric" — LoRA fine-tuning for BitNet b1.58** (released 2025): first GPU-accelerated BitNet fine-tuning, LoRA rank 8 / alpha 16, seq 512. A 1B BitNet fine-tunes on ~18k tokens in ~1.3 hrs *on a phone* — trivial on our hardware. **Caveat: Vulkan/Metal backends, no CUDA; docs don't list Pascal.** The 1080 Ti supports Vulkan, so it *may* work — unverified. CPU fine-tuning on the Threadripper is the reliable fallback (QVAC was CPU-first before GPU).
- **Microsoft BitNet** — official 1-bit inference framework + QAT recipes; STE training, RMSNorm. The reference path if QVAC doesn't fit.
- **"An Extra RMSNorm is All You Need for Fine-Tuning to 1.58 Bits"** (arXiv 2505.08823, 2025) — relevant if we ever want to convert a non-BitNet model down to ternary.
- **In-house experience:** the founder's OllieEmerges project already runs a LoRA fine-tuning pipeline (`peft_forge.py`, Qwen 2.5 base) with an identity-audit protocol. The training muscle and tooling literacy already exist here.

---

## 5. Hardware feasibility on this rig

- LoRA adapters are **a few MB each** — negligible storage and VRAM.
- Fine-tuning effort: a 1B-class BitNet LoRA on tens of thousands of tokens is ~1 hour on a phone; far less on the Threadripper/1080 Ti. Even the 8B base is feasible for LoRA (not full) fine-tuning.
- The distilled classifier heads (Emotion/Salience) train in **seconds-to-minutes** on CPU — they're tiny MLPs on precomputed embeddings.
- Serving: one Bonsai base + swappable adapters fits comfortably in the 11GB already in use.

No new hardware required. The CUDA-vs-Vulkan question only affects *training speed* of the LoRA path, and CPU is an acceptable fallback for an offline, one-time-per-node training job.

---

## 6. Honest risks & unknowns

- **Distillation copies the teacher's flaws.** If the prompt-engineered Emotion node is biased or miscalibrated, the student inherits it. Curate training data (use Critic-approved / non-truncated cycles only).
- **Over-specialization of generative nodes.** A Voice LoRA over-fit to a narrow style loses range. Mitigate: low LoRA rank, diverse training data, hold-out evaluation.
- **Latent-state propagation (Benefit B) is not free.** llama.cpp's server doesn't expose per-layer activations; realizing it needs a custom inference wrapper. Keep it as a separate, later research line — don't let it block the easy wins.
- **QVAC is young; Vulkan-on-Pascal is unverified.** The CPU fallback de-risks this, but expect setup friction on the GPU path.
- **Specialists freeze behavior.** A prompt-engineered node can be edited in seconds; a trained node requires retraining. Only specialize nodes whose behavior has *stabilized*. This is an argument for doing it later, not first — which matches the roadmap ordering.

---

## 7. Recommended path

**Phase 0 — instrument now (this week). ✅ DONE 2026-05-30.**
Per-node output logging is live: `core/training_log.py` writes one JSONL line per node call to `data/training/<node>.jsonl`, capturing (user_prompt → output) plus raw_input, cycle_id, system_prompt, and a `hedged` flag. Best-effort (never breaks a cycle); toggle with `NASCENCE_TRAINING_LOG=0`. Verified end-to-end: a single cycle wrote clean teacher examples for all 8 hot-path nodes. The dataset now accumulates automatically from every real conversation.

**Phase 1 — prove distillation on Emotion (the direction doc's pick).**
After enough logged cycles: train a tiny MLP regressor on MiniLM embeddings → 8-float emotion vector. No LLM. Validate it matches the teacher and runs sub-millisecond. This proves the whole self-distillation pipeline end-to-end on the easiest, highest-leverage node. Ties directly into the shared-state-tensor work (Direction stage 3): a fast numerical emotion node is exactly what modulatory affect propagation wants.

**Phase 2 — LoRA-specialize one generative node (Voice or Critic).**
Use QVAC fabric (or Microsoft BitNet) to LoRA-fine-tune the Bonsai base on logged, curated outputs. Serve as base + adapter. Establishes the "one base, many adapters" serving pattern.

**Phase 3 — roll out remaining nodes as their behavior stabilizes.**
Adapter per node, hot-swapped. Reserve the free-generation nodes for last, since they're hardest and benefit most from a large, mature training set.

**Later / separate line — latent-state propagation (Benefit B).**
Only once adapters share a base and the architecture has settled. Needs a custom inference wrapper. This is the bridge to the Direction document's stage 6.

---

## Why the roadmap puts this last is correct

Specializing a node *freezes* it. A prompt-engineered node is editable in seconds; a trained one needs retraining. So specialization should follow stabilization — which is exactly why this sits behind shared-state modulation (stage 3) and affect persistence (stage 4) in the developmental sequence. The one exception is **logging**, which costs nothing and should start immediately so the data is waiting when the rest is ready.

---

*Sources: BitNet b1.58 (arXiv 2402.17764), BitNet b1.58 2B4T report (arXiv 2504.12285), Microsoft/BitNet (github.com/microsoft/BitNet), QVAC fabric LoRA-for-BitNet (huggingface.co/blog/qvac/fabric-llm-finetune-bitnet, github.com/tetherto/qvac-fabric-llm.cpp), "Extra RMSNorm for 1.58-bit fine-tuning" (arXiv 2505.08823), distilling step-by-step (Google Research 2023), reward distillation (arXiv 2502.19557).*
