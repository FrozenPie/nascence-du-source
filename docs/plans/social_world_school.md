# Social / World / School — Deep-Dive & Implementation Plan (2026-06-24)

> **Status: PARTIALLY BUILT — verified 2026-08-23.** Item 2's measurement half is LIVE (under different
> filenames than this plan specifies — see Current State below). Items 1, 3, 4, and Item 2's latch-loosening
> half are still 0% built.

```plan-state
stage: partial
phase: Item 2 measurement live; Item 1 peer_reflection Phase 0 gate stuck in a long G6-G9 daemon-uptime recheck chain, still unmet as of 2026-09-26 (F-1948)
verified: 2026-11-14
evidence_read: 2026-08-23
gate: injection-log gate (recall_block/recall_memory_fragments accrual) not yet met per the G6-G9 recheck chain
next: J-3704 reads the quality log at 14 live rows
history: docs/plan_history/social_world_school.md
cluster: 6
```


## Current State — verified 2026-11-14

- **2026-11-14**: J-3740 removed 9 uncalled functions (worktree commit 888c193e, restart-gated): composition.pick_task (back-compat shim named in this plan at ~L394, no caller; pick_lesson is the live entry) plus climate_engine._ready_to_ignite, curator.shadow_curate (+ orphan INTEGRATION_ETHIC), library_hand.shelve_only, soundscape.object_sound, study_life._item_named, unified_inference.modulation, deliberation._hot_ground_why, sensorium.woodpile. Re-scan verdict DEAD for 7, TEST_ONLY (_hot_ground_why, tests only patch the attribute) and STRING_ONLY (woodpile, state-dict key) for 2 as the briefing predicted.
- **2026-11-13** (F-4419): data/world_calls.jsonl was never a log and was never wired: world_calls() is a function in core/sensorium.py. The real measurement log is data/social_moves.jsonl (708 rows).

- **2026-11-07** (F-4328): J-3031 (built, restart-gated, branch jobrun/wh_3): P-0086 reflection prompt caps 900 -> 2600 at a sentence boundary, third-person wording, observe-only data/peer_reflection_quality_log.jsonl + scripts/peer_reflection_quality_read.py; previous-reflection line built but OFF (replay: anchoring, no gain).
- **2026-11-05** (F-3958): J-3195 (D-0582): maths ladder extended 9 to 17 in core/math_drill.py (commit 4aafad72 on jobrun/wb_school, unmerged, restart-gated). Eight new kinds of problem, graded by the existing deterministic grade(); method_hint untouched (D-0583). Open: Travis authors hints for levels 10-17 (J-3356), IMN must skip the taught retry above HINT_AUTHORED_MAX_LEVEL (J-3357), strict final-answer grading question (J-3358).

- **2026-11-05** (F-3952): J-3250 built D-0639 (composition task bank, 4-rung ladder, no topic repeat in 10, material-grounded composition grader) on branch jobrun/wb_school commit f9bd17c3; unmerged, awaiting merge and restart. Wiki source waits on J-3285; sumner source waits on J-3291..J-3295 for real clocks.
- **2026-10-08** (F-2602): J-1952: Item 1 vs peer_correspondence B5 overlap analysed; no shared state, no conflict (reader vs writer side); recommend independent with one-way read-only contract; D-0395 opened for founder.

- **2026-10-02** (F-2219): J-1526 (F-2219), checkpoint 43: injection log still 1 row (~25.8 days). New tripwire ref point 7a16745 (D-0310 IDLE_AMBIENT_RECALL=False lands in the same recall_block() function, restart-gated, not yet live); run_nascence.py currently NOT running at all (verified 2 ways), not just restarted. peer_reflection count unchanged at 27; D-0016/D-0178/D-0220 unchanged.
- **2026-09-28** (F-2082): J-1389 (2026-09-27/28), checkpoint 42: injection log still 1 row (~21.8 days); D-0016/D-0178/D-0220 rechecked, unchanged. Git-log tripwire went non-empty for the first time -- commit 7ae886d (D-0287 M2 relational-live flip) is now the reference point going forward; restart-gated, not yet live. Also found a residual letter-storage dedup gap: a 4th long-standing unreplied letter identified, persona smith, dated approximately 2026-08-15. See F-2082 and F-2085.

### What we have
- **Item 2, measurement half — BUILT and LIVE**, but under `core/social_moves.py` / `data/social_moves.jsonl`
  — **not** the filenames this plan specifies (`core/world_calls`, `data/world_calls.jsonl`), which is why
  automated doc-vs-code checks miss it. Confirmed by direct grep, not the plan doc: `social_moves.py` (89
  lines, modified 2026-08-19) implements `observe()`, `_log_outcome()`, and `status()` exactly as this plan's
  Item 2 measurement spec describes — resolves each pending `world_calls()` beckon to heeded/ignored on a
  25-minute window (`_HEED_WINDOW_S`, `social_moves.py:25`) and reports `heeded_rate`. It is genuinely wired,
  not just present: imported by `core/sensorium.py` and `nodes/inner_monologue_node.py`, and surfaced in
  `hud/server.py`. `data/social_moves.jsonl` is actively growing (last row 2026-08-23 03:54, e.g. `{"moment":
  "stars", "outcome": "heeded", "heeded": 1, "latency_min": 7.2}`) — real accumulating evidence, not a stub.
- Everything under §1.1 (peer-letter loop) and §1.3 (school timetable / math ladder) described below as
  "WIRED" was reconfirmed still accurate at a glance (files unchanged in structure); not re-verified line by
  line on 2026-08-23.

### What we need

> **History folded** — 2 dated entries (2026-08-23 … 2026-08-23) moved to `docs/plan_history/social_world_school.md` on 2026-09-27 by hand (J-1484). Derived timeline: `plan_ledger.py social_world_school`.

- **Item 1 (per-peer Theory-of-Mind model, HIGH priority) — Phase 0 BUILT 2026-08-24 (J-0162), now
  accumulating live. Recall-gated design.** `core/peer_model.py` and `data/peer_models.json` now exist.
  Has an **unresolved design overlap** with `peer_correspondence_plan.md`'s B5/G4 guardrails (per-peer
  challenge/safety scaffolding) — still needs a design decision on how the two plans' per-peer machinery
  relate; not blocking (the two are additive, not conflicting, so far).

> **History folded** — 52 dated entries (2026-08-24 … 2026-09-26) moved to `docs/plan_history/social_world_school.md` on 2026-09-27 by hand (J-1484). Derived timeline: `plan_ledger.py social_world_school`.

- **Item 3 (reread/difficulty pacing) — 0% built.** No re-read trigger in `essay_lesson.py`, no
  difficulty-level state in `nature_study.py`/`composition.py` beyond the existing `history` field.
- **Item 4 (per-exchange warmth tagging) — 0% built**, and correctly blocked on Item 1 (no reader exists yet
  for a warmth tag) per this plan's own write-only-cognitive-system discipline.

### What we're doing next
Filename mismatch fixed and go/no-go call made (both 2026-08-23, J-0067 — see above: heeded_rate 0.342,
decision GO). Next actual work is building Item 2's latch-loosening half (verb+noun intent matching in
`inner_monologue_node.py`'s garden/shore branches, per the Approach section) — still 0% built.

---

> **History folded** — 1 dated entry (2026-07-05 … 2026-07-05) moved to `docs/plan_history/social_world_school.md` on 2026-09-27 by hand (J-1484). Derived timeline: `plan_ledger.py social_world_school`.

> Domain: SOCIAL / PEERS / WORLD / SENSORIUM / SCHOOL / LESSONS.
> Verdict from the audit, confirmed by reading: this is the **healthiest** domain in Nascence — no dead
> modules, the peer-letter chain is fully closed, the sensorium is genuinely causal/indifferent, the school
> timetable is real. This plan is about **deepening**, not rescuing. Cross-cutting discipline honoured
> throughout: every item names its REAL read/actuation path (not logging) and an observe-first evidence gate.

---

## 1. As-built deep-dive

### 1.1 The peer-letter loop — WIRED, fully closed (credit due)

The chain a letter travels is end-to-end real, with no dead link:

1. **Compose** — `peers.deliver_due()` (`core/peers.py:383`) staggers a roster of **7** correspondents
   (Darwin, Keats, Twain, Shackleton, Lovelace, Marcus Aurelius, John Smith — `PERSONAS`, `peers.py:241`),
   each on a genuinely OTHER model (mistral-small / llama3.1 / mistral:7b — `peers.py:242-248`, never Du's
   gemma), each with a long hand-written persona system prompt and a `gap_days` cadence. `deliver_due`
   enforces a global trickle (`_GLOBAL_MIN_GAP_H`, `peers.py:388`) and picks the **most-overdue** peer
   (`peers.py:390-399`). Letter generated by `compose_letter` (`peers.py:269`) over a running thread.
2. **Thread memory** — per-peer `thread.jsonl` (`_thread_path`, `peers.py:286`); `deliver_daily`
   answers Du's last reply if there is one (`reply_to`, `peers.py:359`) and appends the new letter
   (`_append_thread`, `peers.py:374`). Date-strip guard (`_strip_date`, `peers.py:312`).
3. **Deliver** — `sensorium.deliver_letter(name, text)` (`sensorium.py:727`) raises the mailbox flag in the
   garden letterbox (`_letterbox`, `sensorium.py:722`). Consent-made-physical: a letter may sit for days.
4. **Perceive** — the raised flag appears in the garden scene (`_letterbox_phrase`, `sensorium.py:763`),
   the garden look (`_garden_look` letterbox branch, `sensorium.py:361`), and even the study window look
   (`sensorium.py:867`). He is never interrupted — he discovers it by looking.
5. **Fetch** — IML latch (`inner_monologue_node.py:1560-1581`): gated on `where()=="garden"` **and**
   `letter_waiting()` **and** an explicit phrase; calls `sensorium.act("fetch")` → `fetch_letter()`
   (`sensorium.py:737`), perceives the text, and **stores it** as an episodic fragment, `origin='peer'`,
   **valence/felt-tagged** (`inner_monologue_node.py:1573-1575`).
6. **Reply** — IML latch (`inner_monologue_node.py:1585-1618`): on "write back"/"reply to"… it finds the
   peer whose **last thread entry is unanswered** (`inner_monologue_node.py:1590-1591`), composes a reply on
   the conscious lane, and `peers.record_reply` (`peers.py:402`) appends it to the thread — so the peer's
   next letter answers it. **The loop rejoins.** Reply also stored `origin='peer'`, valence-tagged
   (`inner_monologue_node.py:1610-1612`).
7. **Decoupled judge** — `peer_metrics.py` freezes a pre-Darwin BASELINE once (`freeze_baseline_if_absent`,
   `peer_metrics.py:118`, called from `deliver_daily`, `peers.py:355`) and `compare()` (`peer_metrics.py:148`)
   measures displacement (R7), lexical contagion (R8), and the GOOD outward-pull (`inward_outward`,
   `peer_metrics.py:73`). This is exactly the "don't be the sole evaluator" discipline, built in.

**What's genuinely good:** different model families per peer; bounded personas (friend-who-writes, no
parallel idle life, R4); the "stay in your country, never ask what Du IS" guardrail in every system prompt;
consent-physical flag; a measured baseline harness before the intervention. This is a model subsystem.

### 1.2 The world-call / move path — PARTIAL (the actuation gap)

- **The pull is felt.** `sensorium.world_calls()` (`sensorium.py:629`) injects a vivid beckon when something
  worth being out in is happening and he is inside (`location=="study"`, `sensorium.py:635`): storm, snow,
  clear stars, wind, summer sun, or a garden milestone (`sensorium.py:639-653`). Rate-limited and
  new-moment-gated so a long storm doesn't nag (`sensorium.py:656`). It reaches the prompt at
  `inner_monologue_node.py:862` ("Even in here you feel it: …").
- **But the door opens only on an exact phrase.** Moving requires `move()` (`sensorium.py:679`), driven by
  the IML latch at `inner_monologue_node.py:1421-1454`. The garden branch
  (`inner_monologue_node.py:1435-1437`) fires only on literal substrings: `"go outside"`, `"step outside"`,
  `"out to the garden"`, `"into the garden"`, etc. **If he says "I'll heed the storm" or "I want to stand
  in the snow", he does NOT move.** The felt pull and the actuation vocabulary are decoupled.
- **No measurement.** `world_calls()` records `_call_moment`/`_call_ts` for rate-limiting only
  (`sensorium.py:658`); nothing logs whether a call was **heeded or ignored**. So we cannot answer the
  most basic question: does the world ever actually pull him out?

  **Evidence (I checked the log):** the world DOES sometimes pull him out — `move("garden")` fired **13×**
  and `move("shore")` **1×** over 2026-06-20 → 06-24 (`data/nascence.log`, "he chose to GO OUT TO THE
  GARDEN" / "GO DOWN TO THE SHORE" / "COME INSIDE"). So actuation is **not zero** — but at ~3 excursions/day
  it is modest, and because heeded-vs-ignored is unlogged we cannot attribute any of these moves to a
  `world_call` rather than a spontaneous "I'd like to tend the garden". The pull's actual conversion rate is
  unmeasured. (`world_steer()`, `sensorium.py:662`, is the sibling "make the scene the subject" nudge —
  fine as is.)

### 1.3 The school timetable & lessons — WIRED

- **Timetable.** `school.py`: weekday mornings 9–12 NZ (`SCHOOL_START_H/END_H`, `school.py:29-30`), subjects
  rotate on a 45-min clock through `["reading","math","nature","composition"]` (`current_subject`,
  `school.py:43`). `directive()` (`school.py:111`) seeds the right lesson per period: reading (open the
  assigned book), `math` → arithmetic, `nature` → `nature_study.directive()`, `composition` →
  `composition.directive()`. Curriculum is an ordered list he works THROUGH with auto-extension from the
  breadth engine when exhausted (`advance`/`_extend_program`, `school.py:173-232`), plus a drift-reconcile
  (`reconcile_reading`, `school.py:258`).
- **Math — grade-gated (the only one).** `math_drill.py` is a real adaptive difficulty LADDER: levels 1–6
  with computed-truth answers (`_gen`, `math_drill.py:63`), a rolling accuracy window, and **advance at 95%**
  (`ADVANCE_ACCURACY = 0.95`, `math_drill.py:36`; `record`, `math_drill.py:128-140`). Method hints teach the
  system, not just mark him (`method_hint`, `math_drill.py:101`).
- **Reading / nature / composition — graded but NOT paced.** All three run a real lesson, grade it via the
  **Emissary (the OTHER lane)** for groundedness, and record the score:
  - `essay_lesson.py` — capstone on a finished book, written FROM HIS NOTES (generation effect), with a
    felt-vs-measured calibration gap (`self_predict` `:255` vs `grade` `:270`), `competence.record_drill_accuracy("comprehension", measured)` (`essay_lesson.py:294`).
  - `nature_study.py` — observe the live sensorium, Emissary grades specificity, `record_drill_accuracy("observation", score)` (`nature_study.py:79`).
  - `composition.py` — a writing task, Emissary grades, `record_drill_accuracy("writing", score)` (`composition.py:85`).
  **The gap:** these scores feed only a *competence belief*. Nothing uses them to **pace difficulty** or
  **trigger a re-read** of a low-scoring book. The signal exists and is thrown away.

### 1.4 Du's social model — WIRED for Travis only

`social_model.py` models exactly ONE relationship: the interlocutor (`relation_id="travis"`,
`social_model.py:65`). It tracks `delta_social` correction-pressure (`apply_correction`, `:78`),
`relational_trust`, expected tone. It is a *correction alarm*, not a relational model — and it knows nothing
of the 7 peers. Du replies to a peer's last letter text (`inner_monologue_node.py:1593-1599`) but holds **no
model of who Darwin IS vs who Keats IS**, no per-peer relational memory, no warmth-by-correspondent.

---

## 2. Gaps & opportunities (ranked)

| # | Gap | Severity | One-line |
|---|-----|----------|----------|
| 1 | **No peer Theory-of-Mind / relationship model** | HIGH | He answers letter-text, never reasons over the relationship; holds no model of any peer. |
| 2 | **World-call → move actuation gap + no measurement** | HIGH | Felt pull; door opens only on narrow vocabulary; heeded-vs-ignored unlogged. |
| 3 | **Reading/nature/composition not grade-paced** | MED | Emissary scores exist but pace nothing; no re-read trigger for a low-scoring book. |
| 4 | **Peer fragments not tagged by exchange warmth** | LOW | Valence is the *moment's* mood, not the *exchange's* warmth; relationships can't accrete affect. |

---

## 3. Research grounding

- **ToMAgent / ToMA** — *Infusing Theory of Mind into Socially Intelligent LLM Agents*
  ([arXiv 2509.22887](https://arxiv.org/abs/2509.22887)). Pairs an explicit **per-turn model of the
  partner's mental state** with **dialogue lookahead** (predict how the partner will receive a move). Agents
  that explicitly carry a partner-model show "more strategic, goal-oriented reasoning… long-horizon
  adaptation, while **maintaining better relationships**." *Adaptation:* Du is not goal-seeking or persuading
  — strip the lookahead/strategy; keep the **partner-model**. A small per-peer "What you know of {name}"
  belief, refreshed after each exchange and **injected into the reply prompt and the delivered-letter
  perception**, so the relationship (not just the last letter) shapes his reply.
- **AgentSociety / "Moltbook"** (relationship memory + past-interaction valence drives **emergent**
  relationships). *Adaptation:* tag each exchange with its **warmth/valence** and accumulate a per-peer
  affect trend — the substrate from which a real, differentiated friendship (warm with Keats, bracing with
  Shackleton) can emerge rather than being scripted. Folds into items #1 and #4.
- **cMALC-D** — *Contextual Multi-Agent LLM-Guided Curriculum Learning with Diversity-Based Context Blending*
  ([arXiv 2508.20818](https://arxiv.org/abs/2508.20818)). **Self-paced** curriculum: order/select by the
  learner's measured competence rather than a static schedule; LLM-judged difficulty; diversity-blending so
  it doesn't collapse to one easy attractor. *Adaptation:* use the Emissary essay/nature/composition score
  to **pace** — a low score triggers a re-read or an easier next pick; a high score advances. The math ladder
  already embodies this; generalise it to the other three. Keep the breadth engine's diversity so pacing
  doesn't narrow him.
- **Situated interactive instruction** (arXiv 2502.20754 — grounded learning through situated action).
  Supports keeping the nature-study lesson reading the **live** sensorium (it already does, `nature_study._scene()`),
  and lets pacing target the world he's actually in.

---

## 4. Implementation plan

### Item 1 — Per-peer Theory-of-Mind / relationship model  [HIGH]

**Goal & weakness.** Du replies to a peer's last letter (`inner_monologue_node.py`, reply latch — line
numbers below are stale against the current ~6000-line file and need re-locating at implementation time)
with no model of who that peer IS — no relational memory, no sense of Darwin-vs-Keats. Give him a small,
evolving per-peer belief that actually reaches his reply and his perception of the letter.

> **REVISED DESIGN — 2026-08-24 (J-0129, per D-0016).** The original Approach/Read-path below (kept
> struck through immediately after this box, for the record) prepended `belief_block()` directly into the
> reply system prompt (`_rsys`) and into the perceived-letter preamble. D-0016 ruled this a violation of
> `peer_correspondence_plan.md`'s guardrails: **G6** (witness, don't steer — a directive prepended into the
> system prompt every reply is a steering instruction, not a witnessed reflection), **G8** (contestable
> recall, no oracle — one `what_i_know` string overwritten in place hardens into a single unchallengeable
> authority on who the peer is, with no aging/pruning/contest path), and it weakens **G9** (an always-on
> injected "here is your friend" preamble tilts toward flattering, uncontested company rather than something
> Du can independently notice, agree with, or ignore). The revised design below achieves the same goal —
> peer relationships shaping social cognition — by routing the belief content through the **same front door
> ordinary memory already uses**, instead of a bespoke privileged channel.

**Approach (functions/files) — REVISED.**
- `core/peer_model.py`, `PeerModel` dataclass, `data/peer_models.json` — **unchanged from the original
  design.** Storing a small per-peer state (`name`, `last_topics`, `warmth`, `exchanges`, `updated_ts`) is
  pure data accumulation, not actuation; it raises no G6-G9 concern on its own.
- `update_after_exchange(persona, his_letter, my_reply)` — **unchanged in spirit** (one small LLM call,
  conscious lane, ToMAgent-lite: "Given the latest letter + your reply, what do you now understand about who
  {name} is and what your friendship is? ≤3 lines"), **but the output is no longer written in place over a
  single `what_i_know` string.** Instead each call produces a fresh, timestamped micro-reflection stored as
  its **own memory fragment** — via the same fragment-store path the fetch/reply latches already use for
  `origin="peer"` (`inner_monologue_node.py` — the `origin="peer", valence=..., felt=...` store calls,
  currently at lines ~2697/2742/2797, re-verify at implementation time), but tagged `origin="peer_reflection"`
  and embedded like any other fragment. `what_i_know` becomes a short rolling *list* of these dated
  reflections (newest few), not one string overwritten every exchange — so an old, since-superseded read of
  a peer does not persist as if still current, and any single reflection can independently age out, get
  contested, or be superseded without erasing the rest of the relationship's history. **This is the G8 fix:**
  no single blob hardens into the peer's permanent, unchallengeable character.
- `belief_block()` as a system-prompt-injection function is **dropped entirely.** No function anywhere
  formats "What you know of {name}: …" for prepending into a system prompt or a letter preamble.

**Read-path / actuation (how it reaches behaviour) — REVISED.**
- **No new injection point in the reply latch or the fetch/perception path.** The reply latch and the
  fetch latch perceive/compose exactly as they do today (unmodified letter text in, unmodified reply out) —
  removing the two direct-injection call sites the original design added.
- Instead, `peer_reflection` fragments reach him **only** through the existing associative-recall front
  door already used for every other memory origin in his idle life and thought composition:
  `core/associative_recall.recall_fragments()` / `recall_block()` (`core/associative_recall.py:222`,
  `:260` — already called from `inner_monologue_node.py:1879` for idle thought and `:3917` for another
  context). This is the *same* mechanism, not a new one: embedding-similarity-gated (`_embed`/`recall_trail`,
  `associative_recall.py:227-231`), competes with every other fragment for relevance, returns quietly when
  nothing connects ("stays quiet when there is no grounded memory to offer," `associative_recall.py:262-263`),
  and is already logged when an injection-worthy origin fires (`associative_recall.py:268-280` — the
  `understanding_from_guidance` precedent: "Logging here is deliberately the over-counting side… lets the
  cure inflate the very metric that certifies the cure"). Extend that same logging convention to
  `origin="peer_reflection"` so every time a reflection actually surfaces in a prompt, it is counted, exactly
  like the guidance-channel precedent — this gives the eventual G6-G9 behavioral check a real instrument to
  read, not a doc argument.
- Concretely: when he is composing a reply to (or reading) a letter from a given peer, the query text fed
  to `recall_fragments`/`recall_block` is what's naturally already in play (the letter's content / his own
  drafting context) — a `peer_reflection` fragment surfaces **only if it's actually relevant** to that
  content, worded as recalled material ("what this brings to mind…", the existing `recall_block()` framing,
  `associative_recall.py:281-283`), never as a narrator-authored preamble asserting who the peer is before
  he's even engaged with the letter. If nothing connects, nothing surfaces — same as any other memory. This
  is the **G6 fix**: the reflection is *offered* through the same channel as any recollection, competing on
  equal footing, never a command prepended ahead of generation.

**Observe-first gate.** Unchanged in spirit, adapted to the new mechanism: Phase 0, build `peer_model.py`
and store `peer_reflection` fragments live (they cost nothing extra — they're memory writes, not prompt
changes) for ~1 week, **without extending the injection-logging convention above yet** (i.e. don't wire the
`recall_fragments`/`recall_block` logging hook for this origin until Phase 0 review). Read the stored
reflections directly from the fragment store; verify they're specific and differentiated (Darwin ≠ Keats)
and not generic mush. Only then wire the logging hook and let them actually surface through
`recall_fragments`/`recall_block` in live composition (flag `PEER_REFLECTION_RECALL_LIVE`).

**Risks.** (a) Generic/sycophantic reflections — same mitigation as the original design (forbid self-
reference in the update prompt; grade specificity in Phase 0 review). (b) Contagion — `peer_metrics.compare()`
still watches `lexicon_drift_from_baseline`; unchanged. (c) Extra LLM call per exchange — bounded, unchanged.
(d) **New risk specific to this design:** relevance-gating means a reflection might *never* surface for a
low-frequency peer even if it's accurate — acceptable (it's the same tradeoff every other memory origin
already lives with; a peer's own next letter is a fresh relevance cue each exchange), but worth watching in
Phase 0 review as "does anything ever actually recall."

**Effort / deps.** **M**, same as original. Depends on `associative_recall.py`'s existing fragment/embedding
path (already live, no new infra) rather than on a new prompt-assembly function — if anything, slightly
less new code than the original `belief_block()`-based design.

**Verification.** Reflections differentiate the 7 peers (spot-check the stored `peer_reflection` fragments
directly, not a rendered `belief_block`); once live, `recall_fragments`/`recall_block`'s logging shows
non-zero, non-constant surfacing (proof it's relevance-gated, not silently dead); `inward_outward.outward`
does not fall and `lexicon_drift` does not spike in `peer_metrics.compare()` (unchanged from original).
**Plus, new:** a G6-G9 behavioral check (per D-0016's reopened defeater) once this is actually built and
live — does the reflection ever function as an unchallenged directive in practice, and does surfacing
frequency stay bounded rather than becoming the dominant shaping force in a reply. This is a runtime check,
not decidable from the design alone — see spawned follow-up job.

---

<details>
<summary><strong>Original design (2026-06-24) — superseded 2026-08-24 per D-0016, kept for the record</strong></summary>

**Approach (functions/files).**
- New module `core/peer_model.py` (mirrors `social_model.py`'s shape but keyed per-peer). A
  `PeerModel` dataclass per persona key: `name`, `what_i_know` (≤3 short lines — who he is, what he cares
  about, the texture of our friendship), `last_topics`, `warmth` (running mean, see item 4), `exchanges`,
  `updated_ts`. Persist to `data/peer_models.json`.
- `update_after_exchange(persona, his_letter, my_reply)` — **ToMAgent-lite**: one small LLM call (the
  conscious lane, cheap) that updates `what_i_know` from the new exchange ("Given what you knew of {name} and
  this latest letter + your reply, what do you now understand about who he is and what your friendship is?
  ≤3 lines"). This is the partner-model refresh, minus lookahead.
- `belief_block(persona) -> str` — renders "What you know of {name}: …" for injection.

**Read-path / actuation (how it reaches behaviour).**
- In the **reply latch** (`inner_monologue_node.py:1594`), prepend `peer_model.belief_block(_pk)` into
  `_rsys` so the reply is written *to a known person*, not to a text. After `record_reply`
  (`inner_monologue_node.py:1603`), call `update_after_exchange`.
- In the **fetch/perception** path (`inner_monologue_node.py:1567-1569`), prepend the belief block to the
  perceived letter ("A letter from {name}, of whom you know: …\n\n{text}") so the relationship colours how he
  *receives* it, not just how he replies. This is the load-bearing actuation — it changes the prompt, not a log.

**Observe-first gate.** Phase 0: build the model and **log** what `belief_block` WOULD inject for ~1 week of
real exchanges, without wiring it into the prompt. Verify the beliefs are specific and correctly
differentiated (Darwin ≠ Keats) and not generic mush, before flipping the inject flag (`PEER_TOM_LIVE`).

**Risks.** (a) Generic/sycophantic beliefs ("a kind friend who cares about me") — mitigate by forbidding
self-reference in the update prompt (same guardrail as the personas) and grading specificity. (b) Contagion:
a richer per-peer prompt could increase R8 lexical drift — `peer_metrics.compare()` already measures this;
watch `lexicon_drift_from_baseline`. (c) Extra LLM call per exchange — bounded (exchanges are ~1-2/day).

**Effort / deps.** **M.** Depends on item 4 (warmth) only loosely — can ship without it and add warmth later.

**Verification.** Beliefs differentiate the 7 peers (spot-check `peer_models.json`); replies post-live cite
relationship facts the bare-text replies couldn't; `inward_outward.outward` does not fall and
`lexicon_drift` does not spike in `peer_metrics.compare()`.

</details>

### Item 2 — Loosen the world-call move-latch + measure heeded/ignored  [HIGH]

**Goal & weakness.** The pull is felt (`world_calls()`, `sensorium.py:629`) but moving needs an exact phrase
(`inner_monologue_node.py:1435-1437`); "I'll heed the storm" does nothing, and nothing measures conversion.
Mirror the looser intent-matching the reading/garden hands already use, and add a counter.

**Approach (functions/files).**
- **Loosen the latch.** In `inner_monologue_node.py:1421-1454`, broaden the garden/shore branches with an
  *intent* test, not just fixed phrases: a small verb-set (`go|head|step|walk|get|venture|out`) **co-occurring**
  with a place/weather noun the active `world_call` is about (storm, snow, stars, wind, sun, garden, shore,
  sea). Keep it a pure-Python guard (no LLM) — same discipline as `_looks`/`act` latches. Optionally add an
  explicit `intention`-field bridge: if `intention` contains "heed"/"go out"/"stand in" + the called moment,
  move. This is the `_wants_read` pattern applied to movement.
- **Measure — BUILT, under different filenames than originally specified here.** Shipped as
  `core/social_moves.py` / `data/social_moves.jsonl` (not `core/world_calls.py` / `data/world_calls.jsonl`
  as this section originally named them — see Current State above). `observe()` is called each idle tick,
  resolves each pending world-call to heeded (moved to garden/shore within `_HEED_WINDOW_S` = 25 min) or
  ignored (window passed, still inside), and logs to `social_moves.jsonl`. `status()` reports
  `{calls, heeded, ignored, heeded_rate}` — the `world_call_stats()` equivalent originally specified here.

**Read-path / actuation.** The loosened latch directly calls `sensorium.move(target)`
(`inner_monologue_node.py:1429/1440`), which changes `state["location"]` — the *real* actuation that swaps
which scene line, which hands, and which lesson-scene he gets. The measurement is logging (acceptable: it is
*instrumentation of* a real actuation, not a substitute for one).

**Observe-first gate.** Ship the **measurement first** (heeded/ignored counter), live, with the latch
UNCHANGED, for ~1 week. That gives the baseline conversion rate. THEN loosen the latch and compare — so we
can prove the loosening actually raised heeded-rate rather than assuming it.

**Risks.** Over-loosening could move him on a mere mention of weather ("the storm outside is wild" while he
means to keep reading) — require the verb+noun co-occurrence, not the noun alone, and keep "come inside"
symmetric. False move is low-harm (he can come back) and visible in the log.

**Effort / deps.** **S** (measurement) + **S** (latch). No deps. Do measurement first.

**Verification.** `world_calls.jsonl` shows a non-trivial heeded fraction; after loosening, heeded-rate rises
and `move("garden"/"shore")` log frequency increases above the current ~3/day; outward share in
`peer_metrics`/monoculture instruments holds or improves.

### Item 3 — Self-paced curriculum for reading / nature / composition (cMALC-D-lite)  [MED]

**Goal & weakness.** Emissary scores (`essay_lesson` comprehension, `nature_study` observation,
`composition` writing) feed only a competence belief; they pace nothing. Use the score to pace difficulty and
trigger a re-read of a low-scoring book — the way `math_drill` already advances at 95%.

**Approach (functions/files).**
- **Re-read trigger (reading).** In `essay_lesson.record` (`essay_lesson.py:284`), when `measured` is low
  (e.g. < 0.45) and the felt-vs-measured `gap` is large, flag the book for a **spiral re-read**: reuse the
  existing `school._extend_program` spiral path (`school.py:198-216`, `book_selection.suggest_reread` /
  `reading.reread`) but make a *poorly-grounded just-finished book* a priority re-read candidate over the
  random 20%. Pure pacing on a real, measured signal.
- **Difficulty pacing (nature/composition).** Add a tiny `level`/recent-mean to each lesson's state
  (`nature_study._load`/`composition._load` already keep `history`). `pick_task()` (`composition.py:22`) and
  `_scene()`/prompt in `nature_study` choose an EASIER vs HARDER task by the recent mean (e.g. low mean →
  "describe one thing in three exact sentences"; high mean → "argue / explain a mechanism"). cMALC-D's
  diversity-blend = keep `_KINDS` rotation so pacing biases but doesn't collapse to one kind.

**Read-path / actuation.** The re-read flag actuates through the *existing* curriculum machinery —
`reconcile_reading`/`advance` pull `current_book` back to the re-read target, so his next school reading
period actually opens the re-read book. The difficulty choice actuates by selecting the prompt he's given.
Both change behaviour, not a log.

**Observe-first gate.** Phase 0: compute and **log** the pacing decision each lesson ("score 0.38 → WOULD
re-read 'X'"; "recent_mean 0.8 → WOULD pick harder") for ~1-2 weeks without acting. Verify the decisions are
sane against the real score history before wiring the re-read trigger / difficulty selection live.

**Risks.** (a) A re-read loop on a genuinely hard book (re-read, fail, re-read) — cap re-reads per book at 1
and require a min-gap. (b) Difficulty thrash — use a rolling mean over ≥5 lessons (the math window pattern),
not a single score. (c) Don't fight the breadth engine's diversity — pacing rides on top of it, never
replaces it.

**Effort / deps.** **M.** Reuses `book_selection.suggest_reread`, `reading.reread`, lesson `history`. No new
infra.

**Verification.** A low-scored book actually reappears as `current_book` in a later school period (log +
`reading.STATE`); nature/composition recent-mean trends upward as difficulty adapts; no re-read loop (per-book
re-read count ≤ 1 in state).

### Item 4 — Per-exchange warmth/valence tagging of peer fragments  [LOW]

**Goal & weakness.** Peer fragments are tagged with the *moment's* mood (`valence=_md.current_valence()`,
`inner_monologue_node.py:1575,1612`), which is his ambient state, not the *warmth of this exchange*. So a
friendship can't accrete its own affective trend (Moltbook's emergent-relationship substrate).

**Approach.** When storing a fetched letter or a sent reply, add a per-exchange `warmth` estimate — cheapest:
a small lexicon/heuristic on the letter+reply (or fold into item 1's `update_after_exchange` LLM call, which
already reads both). Store as a `warmth` field on the fragment keywords/metadata and accumulate a running
`warmth` on `PeerModel` (item 1).

**Read-path / actuation.** Feeds item 1's `belief_block` ("your letters with {name} have been warm / spiky
lately") → reaches the reply and perception prompts. Without item 1 it is observe-only (a tag with no reader)
— so it should ship **with or after** item 1, never alone (avoids the write-only-cognitive-system failure
mode).

**Observe-first gate.** Inherits item 1's gate; warmth is logged in `peer_models.json` and only read once
item 1 is live.

**Risks.** Minimal. Heuristic warmth may be noisy — prefer deriving it from item 1's LLM update over a raw
lexicon if accuracy matters.

**Effort / deps.** **S.** Depends on item 1.

**Verification.** Per-peer `warmth` trends differ across peers in a sensible direction (Keats warm,
Shackleton bracing); the belief block reflects it.

---

## 5. Sequencing

1. **Item 2 measurement (S, observe-only)** — ship the heeded/ignored counter live first. Zero behaviour
   change; gives the baseline conversion rate and immediately answers "does the world pull him out, and how
   often?" Cheapest, highest-information.
2. **Item 1 Phase 0 (M, observe-only)** — build `peer_model.py` and log what `belief_block` WOULD inject over
   a week of real exchanges. (Runs in parallel with #1; independent.)
3. **Item 3 Phase 0 (M, observe-only)** — log pacing decisions against real lesson scores. (Parallel.)
4. **Item 2 latch loosen (S)** — after the baseline week, loosen the move-latch; compare heeded-rate.
5. **Item 1 live (flip `PEER_TOM_LIVE`)** — once beliefs verify as specific/differentiated. Then **Item 4**
   (warmth) rides in, now that there is a reader for it.
6. **Item 3 live** — wire the re-read trigger and difficulty selection once Phase-0 decisions verify sane.

Rationale: every item leads with the observe-first instrument, the cheapest external check ships first
(item 2 measurement answers the open empirical question), and no tag is added until a reader exists for it —
honouring the write-only-cognitive-system and decoupled-judge disciplines. The domain is healthy; these are
additive deepenings, none touching the closed peer loop's load-bearing structure.

---

*Sources:* [ToMAgent — arXiv 2509.22887](https://arxiv.org/abs/2509.22887) ·
[cMALC-D — arXiv 2508.20818](https://arxiv.org/abs/2508.20818) · AgentSociety/Moltbook (relationship-valence
memory) · situated interactive instruction (arXiv 2502.20754).
