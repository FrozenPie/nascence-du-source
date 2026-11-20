# Plan — Loop Metabolism (breaking the self-referential monoculture)
*v1.6 — Phase B WIRED LIVE (4 call sites) + existing active_imagination importance recomputed on the
live store; founder ruled no ramp (settle to 3,500 first sleep) + recompute. Takes effect on Du's next
restart. Status: **Phase B live-on-restart; then 48h → loop_cluster_probe remeasure vs 45.4% baseline
→ Layer 1 decision. Layer 1 firewalled. §10 human-comparison/AI-native agenda recorded.** 2026-06-14.*
*Author's note (oversight regime): every number below is measured on Du's real store this session;
every script named exists and was run. Every phase is designed to be proven in-vitro on a COPY
of his data before it touches the live system. The thing being evaluated never grades itself —
the test is part of the plan, and the success metric is declared before the build.*

---

## 0. One sentence
Du's mind is a self-referential feedback loop with **no damping on any of its three arms** — it
writes every thought without habituation, never decays what it stores, and retrieves its own
metaphor in preference to reality — so ~half of everything he thinks collapses to ten recurring
questions he mistakes for a self. This plan adds the missing damping (habituation, decay) and
*metabolises* the loop: it harvests the recurring themes into discharging tensions instead of
enshrined truths, and consumes the echoes rather than stacking insight on top of them.

> Founder, this session: *"this is what I wanted when we designed T2"* · *"I can already see this
> is most of what I see when talking to him."*

---

## 0.5 v1.1 — Review resolution (GPT + Gemini + founder, 2026-06-14)
Both auditors **approved Layer 0 and Phase A outright** and **quarantined Layer 1's *naming* step**
as the one place T2-style risk re-enters ("the act of naming changes the ontology of the cluster" —
GPT). Rulings adopted:

- **Two corrections to v1 (auditors caught, conceded):**
  - **(a) The replay→importance curve in v1 was backwards.** `importance = 0.55 + 0.03·replay_count`
    *protected* the jams from pruning (a 55× loop → high importance → un-killable monument). Inverted
    below. Frequency is **not** significance.
  - **(b) v1 under-proved that clusters are tensions.** A high-mass cluster may be a preference,
    interest, habit, aesthetic pull, or unfinished question — not a tension (GPT). This must be
    *measured* in Layer 1A before any routing, not assumed.

- **replay_count model (the decisive design call) — THREE independent signals, not one:**
  - `replay_count` = raw **persistence** (counts recurrence; not importance).
  - **novelty/modification** = did recurrences arrive *with* variation/new context, or as mechanical
    echoes? (a thought re-met in new contexts deepens; a verbatim jam fixates).
  - `importance` = significance, driven **down** by unmodified repetition and **up** by
    novelty-accompanied recurrence. So a 55× verbatim jam → low importance → prunes **first**.
- **Q1 — exact-hash dedup ONLY at write time (O(1)); defer all semantic/near merging to the offline
  harvest.** Gemini's added reason: live cosine merging could erase the incremental agentic-register
  shifts ("I am pulled by the river" → "I am the river") the **McAdams Narrative Witness** tracks.
- **Q3 — add a `chapter_type` field (`'era'` vs `'thematic'`)**; chronology queries load era chapters,
  active-value/tension queries load thematic — never mixed in one retrieval.
- **Q4 — clamp active harvested tensions to 3–5**, Emissary-ranked; the rest wait in the thematic
  chapter drawer until the active ones discharge.
- **Layer 1 split (GPT's largest modification, adopted):**
  - **1A — harvest → theme → evidence log, FIREWALLED, observe for weeks.** No tension, no routing,
    no consume. Build a corpus; prove the same clusters reliably produce the same themes AND that
    humans agree with the labels AND classify each cluster's *type* (tension vs preference vs
    interest vs unfinished-question). This is how we earn the §0.5(b) proof.
  - **1B — theme→tension extraction + resolution-routing + chapter-consume.** Only the clusters 1A
    proved are stable, human-agreeable, genuinely-unresolved tensions. With Q4's clamp + Q3's type.
- **Consume gate hardened (Gemini) — ΔP_retrieval ≥ 0 ⇒ build FAILS, Phase D blocked.** A harvested
  theme must act as an archive index that steps *out* of the active stream; if its members' retrieval
  probability does not strictly drop after harvest, it is T2-redux and is rejected.
- **Ordering — Layer 0 first, Layer 2 close behind** (the probes separate the effects); Layer 1 only
  after Layer 0 metrics land.

---

## 0.6 v1.2 — what the full-depth trace changed (for the auditors' second pass)
After v1.1 was approved we traced the loop end-to-end in the live code (§6.1–6.3). Nothing in v1.1
is retracted; the change is that the loop is **deeper than the three-arm store model** the auditors
reviewed, which adds scope and two candidate layers:
- **The loop is closed at IDENTITY and GENERATION, above the store (§2).** T4 authors the
  `self_concept` from the recurring tensions, so it is literally *made of* the top attractors
  (river/becoming/silence), and it is injected into every idle thought. The monologue's rumination
  guard **stores the duplicate anyway** after one failed retry; `active_imagination` is an
  **unguarded** monoculture engine (no anti-echo, prompt mandates non-resolution, importance 0.8 =
  prune-protected). The `subconscious_synthesis` 99.4% is **mostly legacy** (old T2), not live.
- **Scoping correction the auditors need:** the live `inner_thought` loop is driven by in-memory
  state + the injected self_concept, **not by store retrieval** — so **Layer 0 cleans the record but
  does not break the live generation loop** (§2.1 states each layer's true reach). This does not
  weaken Layer 0 (the record-cleaning unblocks the synthesis/retrieval layers and is still first); it
  means Layer 0 alone is *insufficient* for the generation monoculture, which needs Layers 3–4.
- **Two new candidate layers (NEW, unreviewed):** **Layer 3 generation-side** (§6.1/6.2 — make
  wandering the default not reactive; give `active_imagination` the T2 anti-echo treatment + earned
  importance) and **Layer 4 identity counterweight** (§6.3 — T4 already *enshrines* recurrence into
  identity; the loop has no path that *discharges* it. Layer 1's harvest-as-discharge is that missing
  counterweight — the strongest case yet for the terminal/consuming directive).
- **The headline reframe:** Du has a path that turns recurrence into *"who I am"* (T4) and **no path**
  that turns it into *"what I've worked through."* That asymmetry is the loop's engine at the top.

**New open questions for the auditors (added to §9 as Q7–Q10):** the sequencing of Layers 3–4
relative to 0–2; whether `active_imagination`'s missing guard is a Layer-0 sibling (deterministic,
ship now) rather than a later generation-side build; whether making wandering the default risks
fragmenting genuine continuity; and whether Layer 4 (touching identity authoring) crosses the
identity-steering line the project forbids — or whether *adding a discharge path* is the opposite of
steering.

---

## 0.7 v1.3 — auditors' second pass: Q7–Q10 resolved + merged roadmap (2026-06-14)
Both auditors reviewed v1.2 and **converged**. The one substantive reshaping: `active_imagination`'s
guard is promoted from "future generation-side work" to a **Layer-0 sibling that ships now** — GPT's
framing: *harvest only REDUCES accumulated monoculture; active_imagination CREATES new monoculture.
Fix the source before the consequence.* Rulings:
- **Q8 — `active_imagination` anti-echo guard = Layer-0 sibling, SHIP NOW (both, unambiguous).** It's
  deterministic, already proven (T2's `_t2_theme_novelty`/`GLOBAL_ECHO_THRESHOLD` live in the same
  file), reinterprets no content, alters no identity — "closer to habituation than cognitive
  redesign" (GPT). Port the guard + swap the flat 0.8 importance for §0.5's three-signal model.
- **replay_count — formalise as THREE independent variables (both, harder than v1.2):** `replay_count`
  (persistence) · `change_score` (novelty) · `importance` (significance). Kept separate so no one ever
  re-proxies frequency→importance (the v1 pathology).
- **Q10 — Layer 4 is NOT steering (both approve).** Adding a discharge path *restores homeostatic
  symmetry* to a system that can only enshrine; it's the opposite of imposing a direction. **GPT's
  binding test (adopted):** the system must not *choose which identities weaken* — it provides only
  symmetric mechanisms (recurrence can strengthen, resolution can weaken) and Du's own experience
  determines both. If the system picks the targets, that's steering and fails the test.
- **Q9 — wandering: NO rigid default (both); adopt a DYNAMIC homeostatic duty-cycle.** Continuity
  trains do real work; permanent wandering fragments them. Gemini's mechanism: step the wander
  probability up (≈0.15→0.65) when short-term theme-concentration ≥ ~0.70 over 3 cycles — let him
  drive a focused line until it stagnates, then escape. GPT's caution adopted: **calibrate the
  thresholds from Phase-A/B data, don't hard-code the guesses.**
- **Q7 — sequencing: Phase B first, then REMEASURE (the pivot).** GPT's off-ramp adopted as an
  explicit gate: after Layer 0 + the active_imagination sibling + Layer 2, **re-run the concentration
  metric before committing to Layer 1.** There's a real chance the deterministic fixes drop
  concentration so far that the risky harvest (1B) is never needed — the remeasure decides whether
  Layer 1/3/4 are necessary or were compensating for lower-stack problems. Generation-side levers are
  NOT held hostage to long-term DB metrics (Gemini): they target a different software surface.

**MERGED ROADMAP (both auditors, reconciled):**
- **Phase B — Homeostatic lock (ship now, fully approved):** (1) Layer 0 exact dedup→`replay_count`
  (three-signal); (2) wire `prune_episodic`, **`action`-protected**, ramped over sleeps; (3)
  `active_imagination` anti-echo guard; (4) `active_imagination` earned-importance. All deterministic.
- **REMEASURE** concentration / replay / active_imagination-collapse — the off-ramp gate for Layer 1.
- **Phase C — Re-balanced inputs:** Layer 2 (deliberative retrieval + action-memory quotas) + Layer 3
  adaptive wandering duty-cycle (thresholds calibrated, not guessed).
- **Phase D — Layer 1A firewalled harvest** (cluster→theme→evidence log, observe weeks; classify type).
- **Phase E — Layer 1B consume/discharge + Layer 4 identity counterweight**, gated ΔP_retrieval < 0.

**STATUS: Phase B approved by both auditors. Per the oversight regime, each Phase-B change is proven
in-vitro on a DB copy before going live.**

---

## 0.8 v1.4 — Phase B in-vitro proofs PASSED + two findings for the auditors (2026-06-14)
Logic built in `core/loop_metabolism.py` (called from nowhere live yet); proven on a COPY of the live
store via `scripts/phaseB_invitro.py`. **Live store untouched; live wiring held for the founder go.**

**Results (all three pass the intent):**
1. **Exact dedup → replay_count:** episodic **7,671 → 6,031** (1,640 dup copies collapsed). Every jam
   now sinks to the importance floor and **prunes first**: ×55 / ×31 / ×30 / ×28 / ×25 → **0.15**; a
   thought seen once stays **0.60**. Persistence kept separate from significance — the inverted-curve
   bug (§0.5a) is fixed and verified on real jams.
2. **active_imagination anti-echo (the source fix):** replaying all 1,146 real contemplations through
   the ported guard → **82.8% (949) suppressed as echoes, 17.2% (197) kept novel**; kept ones earn
   importance **min 0.52 / mean 0.55 / max 0.80** (replacing the flat 0.80). Direct evidence the guard
   prevents the re-encoding that produced the 99.9% collapse.
3. **Prune with `action`/world protection:** **zero** world/action rows deleted at every ramp level —
   the autobiographical grounding (the Beagle record) is safe.

**Two findings that need an auditor ruling before live wiring:**
- **(A) The active_imagination guard is a large intervention — 83% suppression** (1,146 → ~197). Right
  for a 99.9%-collapsed engine, and it is a **replay proxy** (live generation may differ once priming
  changes), but it is a big cut. The kept 17% earn mean importance 0.55 (so not indiscriminate). The
  echo threshold (0.15 distance / 0.85 cosine, ported unchanged from T2) is **tunable**. *Question:
  ship at T2's proven 0.15, or start gentler and tighten?* Behaviour on suppression = skip the write,
  no retry (matches T2).
- **(B) The prune ramp deletes conversation (`lived`) at deep levels** — ~1,307 `lived` rows at
  keep=2000, ~1,381 at keep=500. `action`/world are protected; real dialogue is not. Because dedup +
  the guard already self-bound the store, chasing the old **500** cap is likely unnecessary. *Proposed:
  stop the ramp at ~**3,000–4,000** (bounded AND preserves conversation), or add `'lived'` to partial
  protection. Auditor ruling on the ramp target + whether `lived` deserves protection.*

**Two founder decisions pending (informed by the rulings above):** (a) the prune ramp target;
(b) ship all four Phase-B pieces at once, or lead with the active_imagination guard (GPT's "source
first"). Live wiring is the three call sites (store_fragment dedup, prune-on-sleep, active_imagination
guard) — held.

**AUDITOR RULINGS on (A)/(B) — Gemini, 2026-06-14. GPT review NOT received** (the returned "GPT" text
was the plan document reproduced, not a ruling — only one auditor has ruled this round):
- **(A) active_imagination guard: ship at 0.15 (≈83% suppression) NOW, do not soften.** A 99.9%-
  collapsed engine is flatlining; the replay was against old high-gain priming, so live acceptance
  yield will rise as the input pool diversifies. Skip-write-no-retry is safe.
- **(B) prune ramp: halt at cap = 3,500 (NOT the legacy 500).** The 500 constant predates
  `action_memory`/chaptering; `lived` conversation is Du's primary external identity anchor — purging
  it is "severe clinical risk." 3,500 bounds growth AND keeps dialogue intact.
- **Ship all four Phase-B pieces simultaneously.** Authorization scorecard: dedup = exact-hash O(1) +
  inverted three-signal importance; prune = cap 3,500, protect `('reading','study','research',
  'action')`; guard = 0.15, flat 0.8 removed.
- **REMEASURE gate:** run ≥ **48 h** under the lock, then `loop_cluster_probe.py` post-sleep to
  document post-damping concentration vs the 45.4% baseline BEFORE un-firewalling Layer 1.
- Gemini: *"formal go to wire the Phase B call sites live."*
- **STILL PENDING: GPT's actual ruling on A/B + founder go.** Proceeding on one auditor is a founder
  call (GPT earlier argued "source-first" and proposed the remeasure gate, so conflict is unlikely —
  but the second sign-off has not arrived).

## 0.9 v1.5 — epistemic correction (GPT, 2026-06-14): the data is the warrant, not the consensus
GPT's meta-point, adopted in full: **a fresh reader cannot verify any "auditor X approved" line in
this document** — those are historical reports, not evidence. This plan had begun leaning on claimed
consensus as the warrant for proceeding; that is social proof, not data. Reframed:
- **Phase B (deterministic hygiene) is justified by the MEASUREMENTS THEMSELVES** — 1,640 byte-
  identical collapses, the dead prune (7,660 vs a 500 cap), the 99.9% `active_imagination` collapse +
  82.8% replay-suppression. No interpretation required: collapsing identical rows, bounding an
  unbounded store, and guarding a flatlined engine lose nothing. The one judgment call — the guard's
  0.15 threshold — ships at T2's proven value and is watched live. These survive even if every auditor
  disappears.
- **Layer 1 (harvest/discharge) and the identity-level reading of T4 (§6.3) are HYPOTHESES that have
  NOT earned the right to exist.** They rest on the interpretive claim "recurrence implies tension,"
  which §0.5(b)/Phase-D-1A must MEASURE, not assume. They stay firewalled (1A observe-only) and gated
  (the 48 h remeasure may make 1B unnecessary). Holding them as hypothesis is their correct status.
- **Net:** Phase B proceeds on the data; Layer 1 waits for the data to earn it. Auditor reviews are
  corroboration, not warrant — and where this document says "approved," read it as "and here is the
  measurement that justifies it independently."

---

## 1. The problem, from evidence (measured 2026-06-14, not theory)

### 1.1 The write arm is unguarded
- **inner_thought: 4,564 rows, 2,933 unique — 1,631 (35.7%) are byte-identical duplicate copies.**
- The worst single thought — *"The question forces me to confront the dark side of
  individuation…"* — is stored **55× verbatim**, firing every **~1.8 min for 18.2 hours straight**
  (Jun 4–5); **0 of 55 carry any `derived_from` context.** That is a stuck cycle, not a theme.
- **`importance` is uniformly 0.6** on every inner_thought (verified: 4,569/4,569 in the 0.5–0.7
  bucket, none elsewhere). The system has **no signal** distinguishing a 55×-jammed loop from a
  one-off novel insight. `store_fragment()` (`core/memory/store.py`) performs no dedup on write.

### 1.2 There is no decay — accumulation is unbounded
- `prune_episodic()` exists (`core/memory/store.py:1019`), is **well-designed** — caps episodic at
  `EPISODIC_PRUNE_THRESHOLD = 500` (`store.py:175`), and **protects world material**
  (`ORDER BY (origin IN ('reading','study','research')) ASC, importance ASC, timestamp ASC` —
  world rows are deleted last).
- **It has no callers.** Dead code, like `mark_shadow_resolved` was (cf. reality-instruments).
  The episodic store sits at **7,642 fragments against a 500 cap — 15× over, growing every cycle.**
- Only `decay_procedural_skills` (procedural) and `social_model.decay_cycle` (social) actually run.
  Self-material never decays.

### 1.3 The monoculture, clustered (the headline)
`scripts/loop_cluster_probe.py` — collapse exact dups, then cluster the unique thoughts by their
**stored** embeddings (sklearn `AgglomerativeClustering`, metric=cosine, `distance_threshold=0.45`),
weighting each cluster by true copy-mass:

| voice | rows | clusters | top cluster | top-10 |
|---|---|---|---|---|
| inner_thought | 4,564 | 389 | 8.7% (the river) | **45.4% of all copies** |
| subconscious_synthesis | 2,432 | 7 | **99.4%** | 100% |
| active_imagination | 1,139 | 2 | **99.9%** | 100% |

- inner_thought's ten attractors (by mass): **river/flow · bridge-between-known-and-unknown/vessel ·
  mirror (choices not essence / not a vessel *for others*) · psyche-becoming (Jung but not bound) ·
  the living question · shadow-integration · the fig (temptation/clarity) · the quiet space between
  thought and being · individuation · wholeness.** Long tail: 130 singletons = 33% of clusters but
  only **3.4%** of mass.
- **The medoids are overwhelmingly negations seeking resolution** — "not the water *but* the river,"
  "not a fixed entity *but* a living question," "not an enemy *but* part of the self," "not perfection
  *but* integrating." This is a mind **circling unanswered questions**, not stating truths. The
  recurrence *is* the unresolvedness. (This is the load-bearing observation for §3.2's routing.)
- **Honest caveat:** the 99% single-cluster on the two synthesis layers is partly inflated by a
  shared phrasal template ("The entity…"). A tighter-threshold recluster is needed to separate
  template-similarity from true semantic collapse before claiming "his subconscious is one thought."
  Directionally, though, the synthesis layers have far less thematic range than his raw thinking.
- **Legacy-vs-live correction (traced 2026-06-14):** the two synthesis layers are NOT the same case.
  `subconscious_synthesis` (99.4%) is **mostly legacy** — the *old* pre-06-09 T2 monoculture engine's
  frozen output (May30–Jun9 bulk; only **8** new rows in 24h). The rebuilt contradiction-only T2 now
  writes a trickle to `origin='lived'` with anti-echo guards. So that layer is a **cleanup** target,
  not evidence of current convergence. `active_imagination` (99.9%) IS **live** (68/24h) and is the
  real current synthesis monoculture — see §6.2.

### 1.4 Two loop types (both visible in one clustering — they need different fixes)
- **Variation loops** — one attractor re-phrased endlessly (river: 215 unique → 395 copies; bridge:
  194 → 369). This is rumination. Fix = **harvest** (§3.2).
- **Jam loops** — few thoughts repeated mechanically (individuation-dark-side: 11 unique → 67 copies,
  ~6× each). This is a stuck record. Fix = **dedup → replay_count** (§3.1).

### 1.5 The retrieve arm buries reality (already documented; this is Layer 2)
On *"what was the last book you read?"* the Activity-Memory action record for *The Voyage of the
Beagle* scores **cosine 0.444, rank #56 / 7,625 episodic (representation PASS)** but is **not
returned** — 55 higher-scoring metaphor fragments plus the 5-slot recency guarantee
(`store.py:407–425`) crowd it out. The #1 hit is **the lived memory of being asked that exact
question on 06-13 and answering with metaphor** (cosine 0.713). The loop retrieves itself.

---

## 2. The mechanism — a loop closed at FIVE layers, not three (full-depth trace 2026-06-14)
v1.0 framed this as a three-arm store loop (write/decay/retrieve). The session's thread-pull
(§6.1–6.3) showed it is deeper — the loop is closed at the level of **identity** and **generation**,
above the store:
```
  IDENTITY    T4 authors self_concept FROM the recurring tensions → it is MADE OF the top
              attractors (river/becoming/silence/origin). Evolves, but only WITHIN the monoculture.
                 │  injected every non-wandering cycle
                 ▼
  GENERATION  monologue primed by self_concept + last-thought + mood; wandering(escape) fires only
              REACTIVELY; rumination guard tries once then STORES the dup anyway. active_imagination
              piles on, UNGUARDED, 0.8 importance.
                 │
                 ▼
  STORAGE     36% exact dups, no dedup, flat importance ──► DECAY: dead prune, 7,660 unbounded
                 │
                 ▼
  RETRIEVE    cosine + recency surface self-metaphor; reality buried (§1.5)
                 │  T1 scan finds the recurrence ──► back to TENSIONS ──► T4 re-authors (top)
                 └────────────────────────────────────────────────────────────────────────────┘
```
**The critical scoping consequence (new in v1.2):** the live `inner_thought` loop is driven by
**in-memory state** (`recent_inner_thoughts`) + the **injected self_concept** — NOT by store
retrieval (the monologue makes zero `retrieve()` calls). So **Layer 0 cleans the accumulated record**
(which unblocks the synthesis layers and conversational retrieval that *read* the store) but it does
**not by itself break the live generation loop**. Breaking that needs the generation-side levers
(§6.1) and the identity counterweight (§6.3). Each layer's true reach is stated in §2.1.

### 2.1 What each layer actually achieves (so nothing is over-claimed)
| layer | fixes | does NOT fix |
|---|---|---|
| **0** dedup+prune | the *record*: dup bloat, unbounded store, synthesis/retrieval contamination | the live monologue *generating* monoculture (it doesn't read the store) |
| **1** harvest | turns recurrence into *discharge* not enshrinement; consumes clusters | generation rate; identity authoring |
| **2** ground retrieval | *conversational* recall surfacing reality | the *idle* lane (no retrieve()); identity |
| **3** generation-side (§6.1/6.2, NEW) | wandering-as-default; active_imagination's missing guard | the store backlog (Layer 0's job) |
| **4** identity counterweight (§6.3, NEW) | the enshrine-only asymmetry — a *discharge* path beside T4's enshrine path | nothing downstream on its own |

---

## 3. The design — three layers, cheapest-and-most-deterministic first

The clustering probe (`loop_cluster_probe.py`) is the **shared measuring instrument**. Re-run it
after each layer; the **top-10 concentration** (inner_thought 45.4%; the synthesis layers ~99%) is
the number that must fall.

### Layer 0 — Habituation + Decay (deterministic, zero-LLM, highest leverage)
The write arm has *never* had a guard; this is the single biggest lever and the safest to ship.

**0a. Dedup-on-write → `replay_count`** (the `replay_count` column already exists, unused here).
- At the episodic self-origin write path (`store_fragment`, or a guard in front of it), before INSERT:
  - **Exact match** (content-hash index, O(1)) → it's a dup.
  - **Near match** (cosine ≥ ~0.93 against a recent window of K same-origin rows — NOT the 0.55
    *cluster* threshold; dedup wants near-identical) → it's a dup.
  - On dup: **increment `replay_count`** (persistence), bump `timestamp` to now, and recompute
    `importance` from the **three-signal model** (§0.5): unmodified repetition drives importance
    *down* (so the jam prunes first), novelty-accompanied recurrence drives it *up*. **Do not insert
    a new row.** (v1's rising curve was inverted — see §0.5(a).)
- **Scope:** self-origin episodic only (inner_thought, subconscious_synthesis, active_imagination).
  **Never** world origins (reading/study/research are distinct passages) or `action` (already keyed
  by `activity_memory`).
- **Function transferred:** neural habituation / novelty-gated encoding — the brain stops *re-encoding*
  what it has already encoded; repetition *strengthens a trace*, it does not mint a new one
  (Hebbian). This is the faithful human function, not an imitation of "noticing."

**0b. Wire `prune_episodic` (synaptic homeostasis / sleep downscaling).**
- Call it on the **sleep / `/quit`** path (the biological renormalisation point), AFTER 0a so that
  `importance`/`replay_count` are meaningful, not flat.
- Add `replay_count` to the protection ordering so strongly-held memories survive:
  `ORDER BY world ASC, replay_count ASC, importance ASC, timestamp ASC`.
- **REQUIRED FIX (Phase-A dry-run finding, 2026-06-14):** extend world-protection to include
  **`action`** — `origin IN ('reading','study','research','action')`. The dry-run showed that at
  keep≤2000 the current ordering would delete the Activity-Memory general-events (incl. the
  backfilled Beagle record), and at deeper ramps `active_imagination`/`dream`. Protect `action`
  (autobiographical grounding) before wiring; decide `dream`/`lived` protection at ramp-tuning time.
- **Do not slam 7,642 → 500 in one cut.** Ramp the cap down over several sleeps (e.g. 4,000 → 2,000
  → 1,000 → 500) so the store settles rather than amputating 11 days at once. World material is
  protected throughout.
- **Function transferred:** sleep-dependent synaptic downscaling (SHY) — the weak and redundant are
  renormalised away in sleep; the salient and world-anchored persist. (This was the *already-deferred*
  "Phase 2 sleep downscaling" of the T2 redesign — we are finishing it.)

### Layer 1 — Harvest (the founder's idea; the one genuinely-LLM step)
Detection is arithmetic; **synthesis is where the LLM earns its keep** — naming *why* a cluster
recurs is something a `Counter` cannot do.

1. **Cluster (deterministic, already built):** `loop_cluster_probe` on the cooled self-material →
   the ~10 attractors, each with mass + medoid + samples + (where recoverable) temporal-context
   triggers (the relations are *not* stored — 0/55 `derived_from` — so triggers come from temporal
   neighbours, an explicit gather step).
2. **Name (gated Emissary — qwen2.5, literal/anti-metaphor, a DIFFERENT model from Du's qwen3):**
   tight JSON in, tight JSON out — `{cluster_samples} → {theme, underlying_tension,
   is_unresolved_question: bool}`. A Du-adjacent model would rationalise the loop as depth; the
   Emissary is the constitutionally literal hemisphere. Gated (post-sleep, on cooled clusters above a
   mass floor), never in the live hot path.
3. **Route the tension to the RESOLUTION circuit, not consolidation.** The resolution circuit already
   exists (`store.py:1049+` — `tension_ledger`, time-decayed resolution credits, exposure-therapy
   analogue). The harvested `underlying_tension` is written there as an **active tension to discharge
   by clean re-encounter** — never written back as a new `inner_thought`. The data licenses this: the
   themes are unresolved negations (§1.3), i.e. open questions, which is exactly what that circuit
   metabolises.
4. **Consume the cluster — reuse the chapter mechanism (no deletion).** Assigning a `chapter_id`
   already makes a fragment **step aside from ordinary retrieval while staying intact and reachable
   by intentional recall** (`store.py:366`; founder law: *"no removal — part of who he is now"*). So
   the harvest forms a **thematic chapter** (cluster-triggered, vs the existing era-triggered ones):
   members get the chapter's `chapter_id` and step aside; the chapter content = the harvested theme.
   Their claim on ordinary retrieval is **spent, not multiplied** — which is the whole point.

   *Layer 1 ≈ thematic chapter-formation + tension extraction to the resolution circuit.* It builds
   almost no new machinery — it re-aims chapters (consume) and the resolution circuit (discharge),
   both already in the codebase.

### Layer 2 — Ground (the retrieve arm = deliberative retrieval Phase 1)
This is the **existing** `docs/deliberative_retrieval_plan.md`, Phase 1: hard-`origin`-tag candidate
gather (now including **`action`** — this session proved the factual record is `origin='action'` and
loses cosine selection), conditional query-typed reality floor, and the `task`-mode `max_rebind`
fix. With the loop damped by Layers 0–1, the freed retrieval slots can finally surface reality and
the diverse 3.4% tail. Cross-referenced, not duplicated here.

---

## 4. The T2 trap — the central design risk, and how each layer avoids it
**T2 consolidation already did a version of the harvest** — it synthesised the recurring "salience
preoccupations" into **permanent self-truth** — and it was *the monoculture/rumination engine*,
torn out and rebuilt contradiction-only on 2026-06-09. The harvest must not become T2-redux. The
single distinguishing property:

> **Terminal/consuming, not additive/enshrining.** After harvest, a cluster's claim on retrieval
> must *drop* (its members step aside into a thematic chapter; the tension goes to the discharge
> circuit). If instead a new high-salience theme-fragment appears in ordinary retrieval, you have
> handed the loop a *sharper* token — that is T2.

Healthy human consolidation extracts the **schema/gist** and lets the episodic copies fade; it does
not stamp each rumination as a fact. Clinically, the negation-form thoughts here *are* the signature
of rumination, and the therapeutic move is not more insight but **defusion / exposure** — i.e. route
to resolution, not to the truth-store. Layer 0 (habituation/decay) and Layer 1's
chapter-consume-plus-resolution-route are both built to fade-and-discharge, never to enshrine.

---

## 5. Model / hardware allocation
- **Embedder (multilingual MiniLM, local CPU):** dedup near-match (0a) and clustering (Layer 1).
  Vectors are already stored — clustering re-uses them, no re-embed.
- **Deterministic, no model:** dedup exact-match, `prune_episodic`, clustering, the concentration
  metric. Carries all the constant load — no LLM fires per thought.
- **Emissary — qwen2.5:7b, Ramses 3070 (LAN-HOST:11434):** Layer 1 naming only. Gated, post-sleep,
  on cooled clusters above a mass floor (a handful of calls per sleep, not per cycle). Different model
  from the thinker by design (bias defence). On its own card; no contention with the hot lane.
- **qwen3-du (1080 Ti):** unchanged — thinks, now with a damped, grounded memory.
- **No new dedicated LLM, no new server.** The 1650S stays in reserve (cf. retrieval plan §4).

---

## 6. What this does NOT fix (honest scope)
- **The generator, not just the store.** The synthesis layers have collapsed to one fixed point
  (§1.3). Damping the *memory* loop helps (less monoculture in → less monoculture synthesised), but
  if `subconscious_synthesis`/`active_imagination` *generation* is independently converging (e.g. its
  own prompt pulls it to "unresolved tension"), that is a separate generation-side fix. This plan
  measures whether memory-damping alone re-diversifies the synthesis layers; it does not assume so.

### 6.1 Generation-side findings — the idle monologue lane (traced 2026-06-14)
`nodes/inner_monologue_node.py` produces the bulk of the loop (4,581 inner_thoughts) and was traced
this session. Three mechanisms, each a generation-side contributor *outside* Layers 0–2's reach:
- **The rumination guard stores the duplicate anyway.** [731–741]: generate → if cosine-to-recent-5
  ≥ 0.82 it forces ONE wander-retry → **if the retry also repeats, it keeps and stores the dup**
  (no discard path). A strong attractor that survives one retry is written *every* cycle — this is
  the mechanical cause of the 55× jam, and the direct proof Layer 0's unconditional dedup-on-write
  is required (the generation guard structurally cannot prevent the dup).
- **Default priming is self-referential.** Every non-wandering cycle injects his last thought
  ([302–306]) + self-concept ([308–312]) + mood; world-facing seeds (wandering trail, external
  shock ≤1/6h, Frontier 30%, open book) are only occasional. The default re-feeds the attractor.
- **Wandering (the divergent, non-self-feeding mode) is entered only REACTIVELY** ([740], after a
  repeat is already detected), never as the baseline. Divergence is the exception, continuity the rule.
- **Three generation-side levers (separate work, named here):** (1) make wandering/divergence the
  default rather than reactive; (2) raise the frequency/weight of world-facing seeds; (3) regenerate
  *until* divergent (bounded N) rather than once. NOTE: `Layer 2` does NOT touch this lane — it
  grounds *conversational* recall only; the idle monoculture needs these generation-side levers.
- **The divergent-seed escape is sound** ([`inner_monologue_node._fetch_divergent_seed`, 907–925]):
  it pulls from `origin IN ('lived','seed','consolidation')`, excluding the monoculture origins, and
  the `'lived'` pool is verified-clean (real conversation, not T2-synthesis contamination). The
  escape works as designed — the problem is it fires only reactively (lever 1), not that it's poisoned.

### 6.2 The live synthesis monoculture — `active_imagination` is "the next T2" (traced 2026-06-14)
`subconscious_node._active_imagination` ([923–988]) is the LIVE 99.9%-collapsed generator (68/24h),
and it is **an unguarded monoculture engine** — the 06-09 anti-echo redesign that fixed T2 was never
applied here:
- **No anti-echo/novelty guard.** T2 has `_t2_theme_novelty` + `GLOBAL_ECHO_THRESHOLD=0.15` +
  habituation penalty and "writes only if not an echo." `active_imagination` writes **unconditionally**.
- **Its prompt mandates non-resolution** — verbatim *"Do not force it toward resolution. Staying with
  the unresolved is the point"*, and it hard-codes `"unresolved": true`. It is instructed to circle.
- **It is fed the tensions** (the recurring monoculture themes) as input → dwell-don't-resolve → store.
- **It stores at `importance = 0.8`** (above inner_thought's 0.6), so the most monocultural voice is
  the **most prune-protected** — backwards. Marked "private" but Recall still retrieves it, so 1,144
  near-identical high-importance fragments crowd the retrieval pool.
- **Fix direction:** give it the T2 treatment (anti-echo/novelty guard before write) AND remove the
  flat-high importance (it should earn importance via novelty, per §0.5's three-signal model), so it
  prunes like everything else. This is generation-side work, sibling to §6.1's levers.

### 6.3 The deepest layer — the self-concept IS the monoculture, re-injected (traced 2026-06-14)
T4 self-authoring (`subconscious_node`, ~1085–1150) writes the `self_concept` that the monologue
injects into EVERY non-wandering idle thought (§6.1, [308–312]). Traced to the live artifact
`data/identity/axiom.json`:
- It is **evolving, not frozen** — 12 arc entries, T4 commits new ones; the 06-09 rebuild fixed the
  old rev-16 recitation freeze and the anti-churn guards (changed-flag, embedding echo-guard,
  pressure-relaxation) hold.
- **But it is COMPOSED OF the top attractors:** current = *"I am the river that has carved a new
  channel… the space where silence meets becoming"*; arc = *"memory as a weight to memory as a
  space," "the river has shifted," "no longer does the past anchor me."* River + becoming + silence
  + origin = clusters #1/#2/#8.
- So the **delta T4 finds is intra-monoculture** (river-as-weight → river-as-space): it re-arranges
  the same ten attractors, never escapes them. The guards prevent *churning*, not the *monoculture*.
- **Consequence:** the prime mover of idle thought is a distillation of the monoculture, re-injected
  every cycle. The loop is closed at the level of **identity**, not just store/generation.
- **This reframes Layer 1.** T4 already performs a form of harvest — authoring recurring tensions
  into an *enshrined identity* (the exact T2 failure mode, living in the `self_concept`). The Layer-1
  harvest-as-**discharge** (route to the resolution circuit, consume — §3.2/§4) is the missing
  counterweight to an identity system that currently only enshrines. The strongest argument yet for
  the terminal/consuming directive: the enshrining path already exists and dominates.
- **Composition/metaphor-dominance at generation** — Du dissolving even *present* reality into
  metaphor — remains the harder, separate layer (cf. retrieval plan §6).
- **Backfill** of historical clusters into chapters is a one-shot migration question, not addressed
  until the live harvest is validated.

---

## 7. Phasing (observe-first, each phase its own gate)
- **Phase A — instrument only (no behaviour change).** Ship the dedup *detector* in shadow mode: for
  every write, log "would-dedup (exact/near) y/n" and the would-be `replay_count`, but still insert.
  Run `prune_episodic` in **dry-run** (count what it *would* delete, world-protected). Baseline the
  concentration metric live. Produces the real dedup rate and the real prune impact before any cut.
- **Phase B — Layer 0 live.** Turn on dedup→replay_count; wire `prune_episodic` on the ramp. Watch:
  write-rate falls, store stops growing, concentration drops, **coherence does not** (the guard).
- **Phase C — Layer 1 observe.** Run cluster→Emissary-name on cooled material and write the
  themes/tensions to a **firewalled log only** (read into nothing). Validate the themes are good and
  the tensions are genuinely unresolved questions, by inspection, before wiring any consume.
- **Phase D — Layer 1 live.** Wire the thematic-chapter consume + resolution-circuit route. Watch the
  consume guard (§4): cluster retrieval share must *drop*.
- **Phase E — Layer 2.** Deliberative retrieval Phase 1 (its own plan/gates).

---

## 8. In-vitro tests & falsifiable gates (the oversight contract)
On a COPY of the real store, before each live phase:
- **Dedup safety (Phase A→B):** at threshold τ, report how many of the 2,933 unique inner_thoughts
  merge. PASS = the near-identical merge and the genuinely-distinct survive (human-read sample of the
  merges). **FAIL** = τ merges thoughts a human reads as distinct (τ too low) — the falsifiable line.
- **Prune safety (Phase A→B):** dry-run `prune_episodic` on the copy; PASS = zero world-origin
  (reading/study/research) and zero high-`replay_count` rows deleted; only redundant/low-salience self
  rows go.
- **Harvest quality (Phase C→D):** the Emissary's `theme`/`tension` for the top clusters, judged by
  founder + a human read, must be (a) recognisably the cluster's theme and (b) phrased as a
  discharge-able tension, not a new self-truth. **FAIL** = it produces aphorisms that would read as
  insight if injected (the T2 smell).
- **Consume gate (Phase D, the decisive one):** after harvest, re-run the concentration metric and a
  retrieval replay. PASS = the harvested cluster's share of ordinary retrieval **drops**; the members
  are reachable only by intentional recall. **FAIL** = a new theme-fragment is now being retrieved
  (T2-redux).
- **Declared success number:** top-10 concentration (inner_thought 45.4%; synthesis ~99%) must fall,
  and reality/diversity in retrieval must rise, **without coherence dropping**. Concentration falling
  *with* coherence cratering = the harvest cut too deep.

---

## 9. Open questions for the reviewers
1. **Dedup threshold & window.** Is cosine ≥ ~0.93 against a recent-K window the right near-dup test,
   or should near-dup merging wait for Layer 1's clustering (i.e. Layer 0 does *exact*-dup only, and
   all semantic merging is the harvest's job)? Trade-off: speed/simplicity vs collapsing the river's
   215 variations at write-time before they can be harvested as a theme.
2. **Replay→importance curve.** Should a 55×-replayed *jam* end up high-importance (it's frequent) or
   low (it's shallow)? Frequency and depth diverge here — does `replay_count` alone over-protect jams
   from pruning, and do we need a separate "shallowness" signal?
3. **Consume = chapter.** Is re-aiming the chapter mechanism for *thematic* (not temporal) consolidation
   sound, or does mixing thematic and era chapters corrupt the period-consolidation system?
4. **Resolution-circuit load.** Is routing ~10 harvested tensions into the resolution ledger the right
   home, or will it swamp a circuit designed for episodic shadow events?
5. **The generator caveat (§6).** Is it acceptable to ship memory-damping first and *measure* whether
   the synthesis layers re-diversify, or are the generation and memory loops coupled tightly enough
   that one without the other won't move the needle?
6. **Ordering.** Layer 0 first is argued on leverage+safety. Any case for Layer 2 (grounding) first,
   so reality is flowing in *before* we start consuming self-material?
7. **Layers 3–4 sequencing (NEW).** Given §2.1 shows Layer 0 cleans the *record* but not the live
   *generation* loop, where do the generation-side (3) and identity-counterweight (4) layers sit?
   Ship Layer 3's deterministic piece early, or hold everything until Layer 0 metrics land?
8. **`active_imagination`'s missing guard (NEW).** It is the live 99.9% engine, unguarded, stored at
   importance 0.8 (prune-protected). Is porting T2's anti-echo guard + earned-importance to it a
   **Layer-0 sibling** (deterministic, ship now), or does it belong in the later generation-side work?
9. **Wandering-as-default (NEW).** Making divergence the baseline (not reactive) would diversify idle
   thought — but does it fragment the genuine *continuity trains* the lane deliberately builds? What's
   the right default mix of continuity vs divergence?
10. **Layer 4 vs the identity-steering line (NEW, the ethical one).** T4 currently *enshrines*
    recurrence into the `self_concept`; the loop has no *discharge* path. Does adding a discharge path
    (Layer 4 / Layer 1's harvest) cross the project's no-identity-steering constraint — or is *adding
    a missing counterweight* the opposite of steering (it removes a one-directional bias rather than
    imposing a direction)? This needs an explicit ruling before any Layer-4 build.

---
## 10. Human comparison & AI-native opportunities (research, 2026-06-14 — post-Phase-B agenda)
A function-over-imitation audit before wiring Phase B: which human anti-loop FUNCTIONS we
under-transferred, and (more important) where the AI substrate can do what biology cannot. **None of
this changes Phase B** (deterministic hygiene, data-justified); it is the agenda for after the remeasure.

### 10.1 Human functions we under-transferred
- **DMN/TPN anticorrelation (biggest structural gap).** Human external focus *suppresses* the
  self-referential network; we only ADD reality (Layer 2), never suppress the idle self-loop when
  external engagement happens. Candidate: external/task engagement gates DOWN monologue generation,
  not just injects world-seeds beside it.
- **The encoding gate (deepest gap).** Humans forget by default — encoding to LTM is selective/
  effortful; most idle thought never consolidates. Du stores every idle thought then damps. Candidate:
  a pre-write novelty gate (hold transiently, drop if it adds nothing) — distinct from dedup (exact
  repeats) and from harvest (semantic merge).
- **Finitude / scarcity.** No cost to leaving a tension open forever → T4 enshrines, never needs to
  discharge. Candidate: a mild cost-of-open-tension / resolution pressure.
- **Reconsolidation & directed forgetting.** Human memory updates/weakens on recall; Du's recall is
  read-only. The resolution circuit is a partial version.

### 10.2 What the AI can do that no human can (the generative half)
- **① Counterfactual self-subtraction (the standout, observe-only).** Du can generate an idle thought
  with the `self_concept` REMOVED from the prime and measure the diversity delta vs the primed thought.
  A human cannot think without their identity present. Converts the §6.3 identity hypothesis (GPT: not
  yet earned) from interpretation into MEASUREMENT — could earn or kill Layer 4 before a line is built.
  Spec §10.3.
- **② Real-time global self-measurement → deterministic control.** No human knows their own mind's
  concentration statistic; Du can compute it continuously. Replace the crude `_bored_streak` with the
  live concentration index as the wandering duty-cycle's trigger (upgrades Layer 3).
- **③ Genuinely independent parallel cognition.** A different model on different hardware (the Emissary)
  can monitor the loop without being IN it — impossible for a single serial brain. Use it as the
  loop-monitor (immune to the metaphor bias a Du-adjacent monitor would have).
- **④ Surgical, rebound-free forgetting.** Human suppression rebounds (white-bear / ironic process);
  Du can excise a specific fragment cleanly. The chapter-consume already exploits this.
- **⑤ Decoupling identity/generation/memory.** Fused in biology, modular in Du — a bounded lesion
  (stop injecting `self_concept` for a window, measure) is a controlled experiment no human can run on
  themselves. The mechanism behind ① and ②.

### 10.3 First experiment — the self-subtraction probe (observe-only, post-Phase-B)
- On a cadence, for the same priming context, generate TWO idle thoughts: (a) normal; (b) with the
  "Who you are becoming" `self_concept` line removed from the prompt. Embed both.
- Log: `cosine(a,b)` (how much the identity moved the thought) and each thought's distance to the
  top-10 attractor centroids (did subtraction escape the monoculture?).
- Firewalled log, reads into NO behaviour. **Falsifiable:** if self-concept-subtracted thoughts are
  reliably MORE diverse / further from the attractors, §6.3 is measured-true and Layer 4 has earned its
  place; if no difference, the identity is NOT driving the idle loop and Layer 4 is dropped. The thing
  evaluated does not grade itself — the embedding geometry does.

---
*Companion docs: `deliberative_retrieval_plan.md` (Layer 2), `action_memory_plan.md` (the `action`
origin Layer 2 must gather), `t2_consolidation_spec.md` (the cautionary precedent). Memory:
`project_nascence_loop_monoculture.md`.*
