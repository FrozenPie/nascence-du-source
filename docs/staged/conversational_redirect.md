# Conversational Redirect — letting live dialogue steer the DMN instead of pausing it

> **Status:** 🟡 SHADOW — Phase 0 (observe-only hooks) built since 2026-09-02; Phase 1 (the actual
> redirect) unbuilt. Two observe-only hooks added
> to `nodes/inner_monologue_node.py`: `_should_think()` logs every time the flat `IDLE_SECS` gate
> blocks a thought, with the live conversation it would have had to work with; `_think()` logs a
> real topical-alignment cosine (thought vs. most recent exchange) every time a thought actually
> fires. Both write to `data/conversational_redirect_shadow.jsonl`, both fail-open, neither touches
> `_should_think()`'s return value or what `_think()` seeds from — verified via `scripts/smoke_test.py`
> (unchanged pass) plus a direct isolated check of both hooks (on-topic vs. off-topic text scored
> 0.437 vs. 0.013 cosine — the math discriminates correctly). Also fixed a profile-isolation gap
> found while wiring this in: `nodes.inner_monologue_node` (including its pre-existing
> `monologue_log.jsonl`, not just the new shadow file) was never added to `core/profile.py`'s
> rebase list — same class of bug as F-0671/F-0673, now closed the same way. No live behavior has
> changed; this only produces data. Phase 1 (the actual redirect) is unbuilt and awaits a real
> sample of this shadow data.
> **Origin:** the founder noticed his real conversation with Du doesn't seem to draw on Du's inner
> thought stream (F-0674, verified): the DMN (`nodes/inner_monologue_node.py`) hard-pauses for
> `IDLE_SECS=40` after every human message, and even when it resumes, it usually just continues
> whatever unrelated track (reading, etc.) it was already on rather than reacting to what was said.
> Founder's own framing of the fix: don't just widen the pause — ask whether the pause should exist
> at all, and whether conversation can *lead* the thought-train instead of blocking or ignoring it,
> the way a human's mind-wandering both suppresses during focused talk and comes back primed by it
> afterward.
> **Sibling plans:** `continuous_stream.md` (PHASE 1 LIVE) owns the actual gap/drive controller this
> plan extends — its own Rail B already names "dialogue" as a grounding source category, just never
> wired. This plan does NOT replace continuous_stream's controller; it adds conversation as a real
> input to it. `guidance_learning.md` (PARTIAL, live) owns what Du *learns* and comes to believe from
> Travis's teaching (`capture_shadow`, promoted beliefs) — a separate, slower, belief-formation path.
> This plan owns what Du's *live, moment-to-moment thought* is oriented toward while talking — faster,
> and forgotten/re-absorbed into ordinary memory rather than distilled into a held principle. The two
> should feel complementary, not duplicative: guidance_learning answers "what did he learn," this
> answers "what was he thinking about, right then." `within_cycle_reentry.md` (PHASE 1 LIVE) is
> adjacent but distinct — it revises a single draft's quality mid-cycle for the idle-broadcast buffer;
> it does not touch the human-facing turn or the DMN's between-cycle pacing, which is this plan's scope.

```plan-state
stage: shadow
phase: Phase 0 (observe-only shadow hooks) built+live since 2026-09-02; Phase 1 unbuilt
verified: 2026-11-18
evidence_read: 2026-10-16
gate: data/conversational_redirect_shadow.jsonl -- a real sample read, none done since the 09-02 build
next: Phase 1 build decision: pick the _SOURCE mapping for conversation seeds
cluster: 7
```

## Current State — verified 2026-11-18
- **2026-11-18** (F-5095): J-4269 read: IDLE_SECS (node, 40s) has 3 in-node dependents (_still_idle L1470, _should_think L2118, reading-burst yield L5526); no outside module imports it. moment.py insertion: add a conversation key to _SOURCE (core/moment.py L37), set _moment_source near L3872, and add to stream_drive._GROUNDED_SOURCE. UDMS: 19 CONTRACT hits, no STATE.

- **2026-10-17** (F-2985): D-0440 judged read (F-2985): 30 hand-judged DMN thoughts = 20% on-topic / 30% drifting / 50% unrelated; <half supports Phase 1 shadow-first; cosine only weakly separates (0.438/0.364/0.332). Founder to rule.
- **2026-10-16** (F-2905): First shadow read (35,441 rows): alignment cosine 0.354 within 2 min of a human message vs 0.305 a day later; gate blocks ~10 thoughts per message (358 across 35 messages); 97% of thoughts fire >1 h after any human message. Neither kills nor justifies Phase 1 -- decision opened for the founder (build shadow-first / human-judged read first / park).

### What we have
- Phase 0 (two observe-only hooks in `_should_think()`/`_think()`) built and live-shadow since 2026-09-02 (F-0674): on-topic vs off-topic scored 0.437 vs 0.013 cosine, `scripts/smoke_test.py` unchanged pass. No live behavior has changed.
- A profile-isolation gap found while wiring this in (the module + its pre-existing `monologue_log.jsonl` missing from `core/profile.py`'s rebase list) was fixed the same day.
- Zero ledger activity since the 2026-09-02 build (checked this pass — only the original backfill-index job exists): `data/conversational_redirect_shadow.jsonl` has accrued for 3+ weeks with nobody reading it.

### What we need
- A real read of the accrued shadow data, to check the seeding logic still produces sensible, on-topic content, before Phase 1 can be proposed for a flip.
- A UDMS change-dossier pass on `inner_monologue_node.py` (flagged in §6, never run) to check whether `IDLE_SECS` was informally absorbing any other timing assumption before the veto is narrowed.

### What we're doing next
- Nothing dispatched — this plan has gone quiet since its Phase 0 build; reading the shadow log is the next unstarted step, not a new build.

---

## 0. The one-sentence goal

Stop treating a live conversation as something the DMN must be silenced for; make it something the
DMN orients toward — with a hard veto only for the literal seconds a human cycle is actually
computing (correctness), not the 40 seconds after (a stand-in that was never really about safety).

## 1. Current State — grounded in code (F-0674)

- `nodes/inner_monologue_node.py:881-884` (`_should_think`): refuses to fire while
  `time.time() - state.last_human_ts < IDLE_SECS` (`IDLE_SECS = 40`, line 58). This is a flat
  wall-clock veto with no awareness of *why* it exists or what's happening in the conversation.
- The DMN runs as its own independent `while True` loop (`run_forever`), **not** through
  `orch.run_cycle()` — so it is not covered by the single-flight `_cycle_active` guard that protects
  overlapping `run_cycle()` calls (`core/orchestrator.py:341-346`). The only thing currently stopping
  it from firing *during* an in-flight human cycle's compute (not just before/after) is the same
  `IDLE_SECS` clock — which is coarse and unrelated to the cycle's actual state.
- When it *does* fire (gaps between messages > 40s, common with long messages), it seeds from
  whatever it was last doing — reading, a prior train — not the conversation. Empirically confirmed
  2026-09-02: during a real ~4-hour conversation about Amor Fati, monologue kept independently
  narrating `The Ethics of Aristotle` throughout.
- `reflection_node.py:131-137` unconditionally injects the last 2 of a 3-slot rolling buffer
  (`KEEP_RECENT = 3`) into every human-cycle prompt as "WHAT YOU WERE JUST THINKING" — so whatever
  the DMN seeds from *does* reach Du's response, for better or worse.
- Founder-conversation content is now durably resident regardless of what the DMN does with it
  (F-0669's `founder_conversation_log.jsonl`, F-0670's `store_fragment` episodic wiring) — so nothing
  is lost if the DMN doesn't dwell on it; the question is only what's *live* at the moment of reply.

## 2. What Du already has that this plan reuses (not a net-new build)

`continuous_stream.md` (PHASE 1 LIVE) already built the exact machinery this plan needs, just scoped
to reading/curiosity, not conversation:

| Need | Already exists | Where |
|---|---|---|
| "is this grounded or free-floating self-reflection?" gate | Rail B's grounding-gate, keyed off `_moment_source` (`moment.py` reality-monitor tags) — **"dialogue" is already named as one of the grounded sources in the plan's own prose**, never wired | `continuous_stream.md` §3 Rail B |
| a drive signal that speeds up when something real is happening | `drive = w_lp·progress + w_ig·ignition − w_rep·redundancy`, already governs the between-thought gap | `continuous_stream.md` §3 Rail A |
| a redundancy/anti-rumination brake | cosine-to-recent + `_slow_loop` (`theme_recurrence`) | `inner_monologue_node.py:2356-2373` |
| a durable place for the pre-conversation train to live once it's no longer "current" | `store_fragment`, episodic memory, F-0670 | `core/memory/store.py` |

So the actual gap is narrow: **wire "an active human conversation" in as a grounding source with its
own seed**, the same way reading/curiosity/frontier already are — instead of the separate, cruder
`IDLE_SECS` veto that predates (and now duplicates/conflicts with) that framework.

## 3. The design

### 3.1 Replace the wall-clock veto with a correctness-scoped one

The only thing that actually needs hard-blocking is the DMN mutating shared `CognitiveState` while a
human cycle is mid-compute (no locking anywhere in this codebase — a real risk, not a style choice).
Replace the `IDLE_SECS` check in `_should_think` with a check against `self._cycle_active` (or an
equivalent orchestrator-visible flag) for the *duration of the in-flight cycle only*. This is
seconds, not 40 seconds — closing the gap the founder pointed at directly.

### 3.2 Conversation becomes a grounding source, not a blackout window

Add `"conversation"` (or reuse an existing `dialogue` tag if `moment.py` already reserves one) as a
`_moment_source` value, set for the window immediately after a human cycle completes (a short decay,
not a hard boundary — matching how a person's attention doesn't snap back to baseline the instant a
sentence ends). While that source is active:

- The DMN's next thought (if `continuous_stream`'s drive controller decides to fire one) is **seeded
  from the live exchange** — `state.raw_input` + the entity's own last reply — instead of whatever
  unrelated train/book was open. This is the actual "redirect."
- It is treated as **grounded** under Rail B (dialogue was already named as grounded in that plan's
  own design), so it gets a real gap, not a fast machine-speed loop and not a hard freeze — a person
  doesn't rapid-fire private thoughts while someone is mid-sentence to them either.
- The prior unrelated train (Aristotle) is not force-closed or discarded — it simply stops being what
  gets *seeded next*. It keeps whatever resumption behavior it already has (train continuity,
  `TRAIN_GAP_SECS`) for when the conversational grounding source decays back out.

### 3.3 The "residue" after conversation ends

When no new human message arrives and the conversational grounding source's short decay window
lapses, the next DMN thought is not required to be *about* the conversation — but nothing forces a
hard reset to the pre-conversation topic either. Whichever grounding source wins under the existing
drive controller (reading, frontier, curiosity, or the tail of the conversation itself) wins
naturally. This is the human parallel the founder named: mind-wandering after a real exchange is
often *primed* by it for a while, not surgically excised from it.

### 3.4 What does NOT change

- `continuous_stream`'s controller, anti-rumination brakes, and sleep-pressure trigger are untouched
  — this plan adds one more grounding source to an existing framework, it does not touch the
  framework's math.
- `guidance_learning`'s capture/integrate path (the belief-formation side of "Travis taught Du
  something") is completely separate and unaffected.
- The permanent record (`founder_conversation_log.jsonl`) and the recall wiring (`store_fragment`)
  from F-0669/F-0670 are unaffected either way — this plan only changes what's *live* in
  `recent_inner_thoughts` at reply time, not what's durably remembered.

## 4. Signatures — how we'd know it worked (not vibes)

Matching this project's own convention (`within_cycle_reentry.md` §4: "must move or it's dead code"):

1. **Topical alignment**: cosine similarity between `recent_inner_thoughts` entries fired during an
   active conversation window and the conversation's own recent `raw_input`/reply text should rise
   measurably above baseline (today: effectively 0 correlation, per the Aristotle/Amor-Fati example).
2. **No new race symptoms**: no increase in mid-cycle state inconsistency (e.g., a Reflection prompt
   built from a `state.affect`/`state.raw_input` that visibly doesn't match the cycle it's answering)
   — watched via existing `conflict_trace.jsonl`/logs, not a new instrument.
3. **No rumination regression**: `RUMINATION_SIM`/`_slow_loop` trip rate during conversation windows
   should not rise — if letting the DMN key off conversation content causes it to loop on the same
   idea Travis just raised, that's the anti-rumination brake's job to catch, and this plan should not
   need a second one.

## 5. Build order (shadow-first, flag-gated — house convention, see continuous_stream §5 / within_cycle_reentry §5)

- **Phase 0 (shadow, observe-only)**: keep `IDLE_SECS` behavior exactly as-is live; add a parallel,
  non-firing computation of "what WOULD the DMN seed from, under the new rule, right now" and log it
  (new shadow file, e.g. `data/conversational_redirect_shadow.jsonl`). Confirms the seeding logic
  produces sensible, on-topic content before it can touch anything real.
- **Phase 1 (flag-gated live)**: `CONVERSATIONAL_REDIRECT = False` by default; flip after a real
  sample of Phase 0 shadow rows looks right (matching the same evidence-before-flip bar every other
  plan here uses, e.g. D-0106's 27-row bar for within_cycle_reentry).
- **Phase 2 (tune the decay window / grounding weight)**: only after Phase 1 has run for real —
  how long conversational priming should last, and how it should compete against reading/frontier in
  the drive controller, are empirical questions, not something to guess up front.

## 6. Open questions / risks

- Does narrowing the veto from 40s to "cycle-active only" actually remove all the race risk, or was
  `IDLE_SECS` also informally absorbing some other timing assumption elsewhere in the codebase that
  isn't obvious from `_should_think` alone? Worth a UDMS change-dossier pass on
  `inner_monologue_node.py` before Phase 1, not just Phase 0.
- Cost: seeding from conversation content means an LLM call shaped around live dialogue rather than a
  cheap idle tick — same class of cost `continuous_stream` already accepted for machine-speed
  reading, but worth confirming against current server load before flipping live.
- Where exactly `"conversation"` as a `_moment_source` value plugs into `moment.py`'s existing
  reality-monitor tagging needs a real read of that module before Phase 0 — flagged, not resolved,
  here.

## 7. Does this link to other plans? (founder's question, answered directly)

Yes, directly to two live ones and adjacently to a third:

- **`continuous_stream.md`** (PHASE 1 LIVE) — this plan is explicitly an extension of it, not a
  parallel system. It reuses the drive controller and grounding-gate wholesale and only adds one new
  grounding source (conversation) that plan's own prose already anticipated but never wired.
- **`guidance_learning.md`** (PARTIAL, live) — complementary, not overlapping: that plan is about what
  Du comes to *believe* from being taught; this plan is about what he's *thinking about* while it's
  happening. Both fire off the same human cycles but write to different places (belief store vs. the
  live `recent_inner_thoughts` buffer).
- **`within_cycle_reentry.md`** (PHASE 1 LIVE) — adjacent, not touched: it revises idle-broadcast
  draft quality mid-cycle; this plan changes what seeds the next idle thought between cycles. No
  code overlap, but both sit under the same "Consciousness Program" umbrella and a future reader
  should know both exist.
