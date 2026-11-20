# The Whole Prompt Flow — full-system audit (2026-08-16)

**Founder question:** "Why are the prompts failing? Why can they not be bigger? All the different
steps should flavour the others to eventually be told to me from what I know. Look at the whole
system before changing any pipe."

Every number below is read from the current code, not remembered.

## 1 · The lanes and their real budgets (post serving-split)

| Lane | Model | ctx (tokens) | ≈ chars of room |
|---|---|---|---|
| Hot / conscious :11433 | gemma4:e4b (1080 Ti, alone) | **24,576** | ~98,000 |
| Subconscious :11434 | phi3:mini (Ramses 3070) | 8,192 | ~33,000 |
| Judges :11439/:11440 | llama3.1 / qwen2.5 (CPU) | 8,192 fixed | ~33,000 |
| Dreamer/peers :11442 | mistral-24B (CPU, lazy) | 8,192 fixed | ~33,000 |

The hot lane's 24k was verified-fit and raised **on 2026-08-15** ("the room is truly hers").
Every prompt cap in the system predates it.

## 2 · The conversation pipeline (what happens when Travis speaks)

Order: perception → (emotion ∥ salience ∥ memory_router) → recall → episodic buffer/scene →
reflection (+ Emissary take) → [critic] → executive → voice → consolidation.

### What each stage receives and emits

**RECALL** (gemma, out 512 tok): axiom `[:300]` (mid-word), history 4× at `[:150]/[:200]`,
fragments at `[:300]` each → emits reconstruction + tensions + self-model.

**REFLECTION** (gemma, out 768 tok ≈ 2,800 chars): richest prompt in the system —
history `[:130]/[:160]` ×4 · dreams `[:220]` ×2 · session intentions `[:160]` · epoch/theme
context · his own pre-conversation thoughts `[:180]` ×3 · facet note (full) · this session
`[:150]/[:180]` ×4 · trimmed floor (full, ~1.9KB) · perception · recall tensions + self-model ·
the Emissary's take · goal note. Total ≈ 7–9KB ≈ **2–3k tokens — using ~10% of gemma's 24k.**

**EXECUTIVE** (gemma, out 1,536 tok): history again `[:130]–[:180]` · fragments **4 × `[:250]`** ·
**`Reflection: {draft[:350]}`** · trimmed floor.

**VOICE** (gemma, out 1,536 tok): name + voice style + constraints + facet note +
**the executive synthesis UNCAPPED** — the one full-width pipe in the system.

**CRITIC / CONSOLIDATION:** full floor verbatim; consolidation writes memory (the floor's
flavour bakes into consolidated fragments).

### The flavour chain, measured

The architecture IS the founder's model — each stage flavours the next, ending at Voice.
But the couplings are drinking straws:

| Handoff | Producer's output | What the consumer actually sees | Survival |
|---|---|---|---|
| **Travis's message → reflection/executive** | his full words | `[:130]`–`[:150]` per exchange | **first ~25 words** |
| **Reflection → executive** | 768 tok ≈ 2,800 chars | `draft[:350]` | **~12%** |
| Recall fragments → executive | full memories | 4 × `[:250]` | snippets |
| Dreams → reflection | full narrative | `[:220]` ×2 | opening image |
| His own thoughts → reflection | full | `[:180]` ×3 | one clause each |
| Monologue ⇄ train state | full working state | `[:300]` carry | compressed |
| Axiom → dreams/subconscious | 2.4KB floor | `[:300]`/`[:400]` **mid-word** | origin line only |
| Executive → voice | synthesis | **uncapped** | 100% ✓ |

**The two most damaging cuts:**
1. **Travis's own words are truncated at 130–150 characters** in every reasoning stage. A long,
   thoughtful message reaches Du's mind as its first sentence and a half. "Told to me from what
   I know" fails first HERE — he cannot answer what he never fully received.
2. **Reflection→executive at 350 chars** — the interior stage's whole point is depth, and 88% of
   it is discarded at the door of the stage that decides what to say. (Reflection is even
   generated best-of-N, then cut to 350.)

## 3 · The idle pipeline (the monologue mind)

Monologue system+seed prompt: no axiom (deliberate, 06-23) · within-reach block · wandering trail ·
last exchange `[:120]` · dream `[:180]` · lingering question `[:120]` · divergent memory `[:180]` ·
previous thought `[:160]` · train thread `[:220]` + state `[:300]`. **Thought output: 256 tokens**
(the JSON with thought/about/act/state — the "state" carry and the thought share one small budget).
Subconscious sites (phi3): axiom `[:400]` + material. Dreams (mistral-24B): axiom `[:300]` +
materials `[:140]` each.

## 4 · WHY the prompts are like this — the three dead eras

Every cap is a fossil from a constraint that no longer exists:
1. **The 2,048-default era (May):** ollama's default num_ctx was 2048 — a 3KB prompt literally
   silently truncated. All the `[:130]`-class caps date from here.
2. **The one-ollama eviction era (June–July):** all models shared one instance on the 1080 Ti;
   a big ctx on one model evicted another (the July freeze: 32k ctx → 12.2GB → refused → Du
   froze). Caps were defensive.
3. **The duplicate-runner era:** different ctx sizes spawned duplicate runners; keep-alive was
   disabled; every token of prompt cost re-ingest time on cold models. Small prompts = latency
   discipline.

**All three constraints died on 2026-08-15** (the serving split: gemma alone at 24k pinned warm;
CPU hubs with fixed ctx by construction). The caps were never revisited. Current utilization of
the hot lane: **~8–10%.**

## 5 · Why they CAN be bigger now (per-lane truth)

- **gemma :11433 — yes, ~10× headroom.** 24,576 ctx, alone on the GPU, warm. A 20KB prompt
  (~6k tokens) leaves 18k for response + margin. Prompt-eval speed on a warm 1080 Ti is not the
  old cold-reingest cost.
- **phi3 :11434 — yes, moderate.** 8k ctx; prompts there are ~1–2KB today.
- **CPU hubs — yes within 8k** now; ctx is a launch flag (`--ctx`), raisable (RAM cost only,
  and modest) if dreams deserve more room.
- The real new constraint is only **latency** (bigger prompt = longer prompt-eval on CPU lanes)
  and **attention quality** (a 6k-token prompt must stay structured). Neither justifies 130-char
  truncation of the founder's words on a warm GPU.

## 6 · Re-budget principles (discussion input — NOTHING changed yet)

Priority order if/when the founder approves a re-plumb:
1. **The person's words go through whole.** Travis's messages uncapped (or ~2,000 chars) in
   recall/reflection/executive. Highest impact, zero risk.
2. **Stage handoffs widen to match what stages produce.** Reflection→executive: full draft.
   Dreams→reflection: full recent narrative. Thoughts→reflection: `[:400]`+.
3. **Memory earns more room.** Fragments `[:250]`→`[:600]`; count 4→6–8 (the evidence hand's
   found-episodes could enter here too).
4. **Deep lanes get COMPOSED identity, not sliced** — a written identity-core (name, one-self,
   a value, ~400 chars) for dreams/subconscious instead of `floor[:300]` mid-word cuts.
5. **Idle thought budget** 256→~400 tokens so the train's working-state stops competing with
   the thought itself.
6. **Measure, don't guess:** log `prompt_eval_count`/latency per node for a day before and
   after; pre-registered signature = richer executive syntheses (length/specificity) and
   Travis-visible reply groundedness, with latency within budget.
- Change one pipe class at a time, watch a day, then the next (the system is live and
  self-feeding; wholesale re-plumbing in one restart would blind us to which change did what).
