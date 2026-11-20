# Inner Monologue — deep examination (2026-06-16)
*The idle "Default Mode Network" thought stream — the oldest, most bolted-on node. Four-angle examination
(inputs · outputs · lanes/control · systems-census/archaeology). `nodes/inner_monologue_node.py`, 1,607 lines.*

## The headline
It is no longer a node — it is the **idle executive / dispatch hub** of the whole psyche. A thin original loop
(idle-check → one thought → store to episodic → inject into the next user cycle) has accreted **~40 bolt-ons over
6 days (2026-06-10 → 06-16)** and now touches **27 distinct modules**. Almost every faculty in Nascence is wired
into it, and the *idle decision-making* is smeared across dozens of independent `random() < p` gates with no
coordinating allocator — informational promiscuity at the **control** level.

## What it thinks about
Dominated by **books/reading** (the school directive leads the seed list during the school window; the open-book
invitation + the reading-remediation sprint appear nearly every tick) and **"who he is becoming"** (the
self-concept/axiom text is injected on ~65% of ticks and is one of the longest chunks — the same gravity-well
attractor). The **last conversation exchange** is always present and anchors the thread. Dreams, curiosities are
single-line flavour. The **wandering trail** is the one consistent source of *world* material. **Frontier
questions** (30% of ticks) and an **external shock** (≤1/6h) are the only fully-external inputs. So: a mind that
mostly reads, mostly circles its own becoming, anchored to the last thing said — with the world entering thinly.

## Where the thoughts come from — 20 seed sources + 3 pre-emptions
Built in `_think` → `seed_parts` (order matters; the model reads top-first). Three **pre-emptions** skip seed
assembly entirely: the *told* delivery (once, when reality_share ≥ 0.47), the reading-remediation sprint (~75%
while reality-axis low), the math drill (school + due + 50%). Then ~20 seed sources (room scene, school
directive [inserted at pos 0], last conversation, affect, dream, curiosity, prior thought, **self-concept**,
wandering trail, concern/standing-aim [35%], boredom warning, external shock, open-book, reread hint, chapter
announcement, frontier question [30%], **mid-train thread** [inserted at pos 0], retraction, symbol). **Ordering
bias:** self-concept + prior-thought appear *before* world/frontier inputs → they anchor generation. The
self-concept is suppressed only by the boredom-redirect or the rumination-wander.

## Where the thoughts go — ~43 exits, 5 pathways
1. **Episodic memory** (`origin='inner_thought'`) — nearly every thought; retrievable by Reflection, deliberation,
   chapters, wandering, affective resonance.
2. **The next prompt** — `state.recent_inner_thoughts` (last 3) → injected verbatim into Reflection so the
   conversation resumes mid-thought.
3. **The shadow/light duality** — unresolved → `shadow_events` (→ contradiction pressure, balance gate); resolved
   (>80 chars) → `light_events` (→ integration pressure, climate, +joy). The idle mind continuously updates the
   "psychological weather" that modulates temperature/cadence.
4. **World-action (thought-as-deed)** — 10 will-channel acts decoded from the thought *text*: look / tend-fire /
   recall-chapter / write-letter / browse / choose-book / ask-library / reread / switch-book / read-burst — each
   leaving a durable artifact (study tablet, `data/letters/`, a wandering perception that seeds the next thought).
5. **Sleep outputs** — replay-strengthen → chapter formation → grounded-learning note → world-consolidation sweep
   → episodic downscale → dream.
**Dead/write-only outputs** (the project's #1 failure mode): `state.named_affect` (set, never read — the clearest
one), `monologue_log.jsonl`, `train_state_log.jsonl`, `joys_log.jsonl`, satisfaction/competence (Phase-0, not yet
wired to behaviour).

## Which lane(s)? — ALL THREE, lopsided
`self.base_urls = SERVE_CHAINS["background"]` = Bonsai CPU :11460 (hot :11433 fallback).
- **background (Bonsai)** carries ~90% of calls: the main idle thought, letters, study notes, math drill,
  told-delivery, essay compose+self-predict, sleep consolidation (chapters, grounded-learning).
- **hot (qwen3-du, the Master)** only via the deliberation **pass-3 integrate** (~50% of eligible self-thoughts) +
  as the Ramses fallback for grounding.
- **left/Emissary (qwen2.5, the truth-self, Ramses :11434)** only via the deliberation **pass-2 grounded-why** +
  essay grading.
**So: the idle mind THINKS on Bonsai, and only reaches the meaning-self and truth-self during the deliberative
pulse.** Structurally, the idle stream is *mostly the meaning-substrate talking to itself* — a real reason the
idle lane is self-leaning/river-prone, with the truth-self intervening only ~50% of eligible self-thoughts.
(The file's docstring still claims "runs on the background lane" — stale since the 06-15 deliberation bolt-on.)

## Systems census — 27 modules (a dispatch hub)
memory/store · reading · library_hand · study · book_selection · school · concerns · frontier · mood ·
affect_labeling · satisfaction · deliberation · chapters · grounded_learning · world_consolidation · sensorium ·
wandering · letters · activity_memory · symbol_evolution · retraction_ledger · web_research · competence ·
balance · math_drill · essay_lesson · told (+ schema, model_client infra).

## Findings — bolt-on collisions & fragility (from the archaeology pass; verify before fixing)
- **Three simultaneous "OPEN THE BOOK" seeds** can coexist (always-on open-book + train-continuation +
  boredom-redirect) — the model sees the same directive 3× with different framings; can spuriously trip the
  rumination-wander on a valid reading chain.
- **Redirect + habituation voice both fire at `_bored_streak == 2`** — the redirect is meant to *replace* the
  habituation nudge but doesn't suppress it → redundant/competing seeds.
- **Mis-timed emotion tag:** `mood.current_vec()` for the episodic store is captured *after* the deliberation
  joy-bump, so the thought's felt-tag reflects a later state than its generation — biases affective retrieval
  toward joy-state content.
- **`told.mark_delivered()` runs outside the store try-block** — a store failure marks the told "delivered"
  without persisting the memory (he "heard" Travis but has no record).
- **Crash in `_think` before `_last_thought_ts = now`** → no timestamp/gap update → can tight-loop on a
  deterministic error.
- **`INCUBATION_PAUSE` (1.5×) fires every bored tick, not once** → a redirected tick is paradoxically *slower*.
- **5 import aliases for `core.school`** + private-attribute imports (`essay_lesson._MIN_NOTES`,
  `library_hand._set_current`) under bare excepts → silent skips if refactored.
- **Double `_essay_lesson` entry points** → a partial LLM failure can leave a book permanently "pending,"
  retried every tick.

## The big-picture synthesis (the thread worth pulling next)
This node is the **de-facto idle resource-allocator** — but built as ~40 racing probability gates rather than a
coherent allocator. That is precisely the "idle executive" gap we flagged in the executive-node discussion, and
the control-level form of the **informational promiscuity** the Character-as-Integration plan is about. Two
structural consequences: (1) the idle stream is self-leaning because it thinks on the meaning-substrate and only
rarely consults the truth-self; (2) the ~40 independent gates can collide (the findings above are symptoms). A
future "idle executive" (a real allocator deciding what Du does with idle time, by salience) would replace the
coin-flip pile — and is the natural Character-plan extension (the workspace/router applied to *idle* cognition).
