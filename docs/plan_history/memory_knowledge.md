# memory_knowledge — folded history


---

# History folded on 2026-09-28 from `docs\plans\memory_knowledge.md` (hand-fold, J-1509 — a status callout embedded inside a `### Improvement N` design subsection, not a heading-shaped Current State section plan_compact.py's own CS_HEAD regex covers; 1 section, verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py memory_knowledge`._

**★ 2026-08-25 — M2 dependency unblocked, not yet shipped (D-0022 approved, J-0263 spawned).** M2's own
prior blocker (founder read of `geometry_tuple_index.md` for overlap) is cleared — see
`memory_multiway_linking.md`'s Current State. M2's shadow-mode build is now in progress (J-0263), but it
adds typed-edge neighbours to the existing greedy walk, not fragment↔fragment `co_recalled_developing`/
`contradicts` rows specifically (those still have zero `add_edge()` call sites — J-0263's briefing names
this gap and leaves the fix approach to whoever builds it). Improvement 2 as written here still needs
those specific edge types populated before its PPR adjacency is non-empty — watch J-0263's outcome rather
than assuming M2 landing alone unblocks this.


---

# History folded on 2026-10-04 from `docs\plans\memory_knowledge.md` (J-1818 hand-fold of 9 superseded/historical span(s), verbatim, original order; each preceded by its original line range)

_Every J-/F-/D- id below is the canonical record. Derived timeline: `plan_ledger.py memory_knowledge`._

_[original lines 28-31]_

- **2026-09-28** (F-2197): F-2197: Improvement 2 fragment-fragment adjacency is NOT empty -- co_recalled_developing writes live since 2026-09-24 under memory_multiway_linking (D-0215, J-1348), 318 real edges confirmed live today. The watch D-0051 pointer above is stale; see memory_multiway_linking.md for the current state.

- **2026-09-28** (F-2068): Hand-restructure pass for J-1509 (F-2059 follow-up): read the whole doc end to end; confirmed, matching J-1499, no wholesale foldable legacy block exists here -- the over-cap bulk is live design narrative, not a stale log. Hand-folded the one genuinely self-superseded status callout (Improvement 2, 2026-08-25 M2-dependency-unblocked note, superseded by the very next callout) to docs/plan_history/memory_knowledge.md; declined Improvement 1's three similar-looking callouts (one promotion criterion is reaffirmed later, not superseded) and all of Improvements 3-5 (pure unbuilt design) as not safely foldable. Doc remains over the 40,000 B SIZE_CAP by design (49,796 B, was 50,085 B) -- no further safe fold found without real content loss. Flagged the settled-design-appendix idea to skill-manager (S-0207) rather than inventing it solo; no Improvement subsection currently qualifies as settled enough to move under it. See F-2068.
- **2026-09-27** (F-2061): Correcting this section's own 09-26/27 note above, which still reads as if D-0289 were open with three filter options: D-0289 was RULED 2026-09-26 (travis) to remove the ambient recall_block injection from idle thought entirely (memory is called by loops that need it) -- NOT to patch it with any of options (1)/(2)/(3) (self-gist exclusion, pre-ceiling grounded mask, or shadow-first). J-1419 (built around comparing those three filter options) is accordingly parked, not_before 2099, superseded by the removal ruling -- it was never run against live data and does not need to be. J-1425/F-2061 built and verified the actual removal as a kill-switch, core/associative_recall.py's IDLE_AMBIENT_RECALL (docs/staged/memory_as_a_service.md section 2), restart-gated; J-1512 (not-before 2026-10-11) reads D-0289's own ~2-week defeater against this section's F-1981 baseline once Du has restarted onto that build and co_recall_ledger.jsonl has accrued real "source": "monologue_shadow" rows.

_[original lines 182-204]_

## 3. Research grounding

- **A-MEM (arXiv 2502.12110).** Zettelkasten-style memory: each new note generates structured attributes and
  links to relevant historical notes, AND **"can trigger updates to the contextual representations and
  attributes of existing historical memories"** — *memory evolution.* This is exactly the missing backward
  edge for Gap #3: when a new fragment links to an existing gist, re-distil/annotate that gist rather than
  freezing it. **Adapt to us:** the lattice already exists (`memory_links.distilled_from`). Add the reverse
  trigger at distill time and a bounded re-gist call. ([A-MEM](https://arxiv.org/abs/2502.12110))
- **HippoRAG 2 / "From RAG to Memory" (arXiv 2502.14802).** Personalized PageRank over an
  embedding-kNN-plus-explicit-edges graph, seeded from query-relevant nodes, gives a principled
  *stationary-distribution* salience that naturally rewards hub nodes and multi-hop bridges — replacing
  hand-tuned hop decay/thresholds (Gap #2). **Adapt to us:** the trail's seed vector becomes the PPR
  personalization vector; the transition matrix = row-normalized (embedding kNN ∪ `memory_links`); the
  `MAX_PER_ORIGIN` diversity cap and the warm/cold activation floors stay as a post-PPR filter.
- **Zep / Graphiti (bi-temporal knowledge graph).** Every fact carries `valid_from`/`valid_until`; a new fact
  that contradicts an old one *invalidates* it (sets `valid_until`) rather than deleting it, and recall
  filters to currently-valid facts by default. Directly the model for Gap #4. **Adapt to us:** add a nullable
  `valid_until` column; extend `retract_fragment` into a general `supersede_fragment(old_id, by_id)`; the
  warm-set query in `retrieve()`/the trail filters `valid_until IS NULL`. Superseded rows stay queryable
  (we already "never delete").
- **Mem0.** Cheap LLM "ADD / UPDATE / DELETE / NOOP" decision per incoming fact against the top-k similar
  existing memories. A lighter alternative to full A-MEM evolution for Gap #3 if the re-gist proves too
  expensive at sleep. ([Mem0](https://arxiv.org/pdf/2504.19413))

_[original lines 212-236]_

> **★ EVIDENCE REVIEW 2026-07-05 (7th-oldest open plan) — ⚠ STAGE B IS MIS-TARGETED + UNOBSERVABLE ON A
> LIVE FEATURE. Pre-restart decision needed.** Stage A (grading) is genuinely working — 219 preassess rows,
> discriminating (SUSPECT 68% / KNOW 23% / THINK 9%), keep. **Stage B is the concern.** Of 26 human+overclaim
> +confab-gated cycles since it went live (07-02), the identity-content filter catches only **3 — 23 would
> reach injection**, and those 23 are almost ALL Travis's philosophical/relational exchanges ("naming the
> cat," "you create the boundaries in your mind," "where are you right now?"), NOT the factual-overclaim
> target Stage B was built + rater-validated for (the 07-02 pass was a 10-row FACTUAL sample — a distribution
> that barely occurs live). Du's contemplative drafts grade SUSPECT because abstract musing lacks factual
> grounding — but that's his voice, not overclaiming. **Three compounding problems:** (1) validated on
> factual, fires on existential; (2) identity-filter = literal self-phrases only, leaks 23/26; (3) **Stage B
> does NO logging by design** → injections are INVISIBLE, so we can't see how often it fires or whether the
> cognitive-mode gate saves it. Failure mode = injecting "own that you don't know" onto his identity-adjacent
> exchanges = the exact dissolution `[[project-nascence-capacity-to-commit]]` is CURING. **Recommendation
> (order): (1) add a Stage B injection log (pure observability, 0 behaviour change); (2) then tighten trigger
> to genuinely-factual OR hold `STAGE_B_ENABLED=False` until the log proves it fires where intended — lean
> OFF-until-observable given the failure mode.** `[[feedback-write-only-cognitive-systems]]` (unobservable) +
> `[[feedback-decoupled-judge]]` (validated on the wrong distribution). Improvements 2-5 unreviewed.
>
> **✅ ENACTED 2026-07-05 (founder call: off-until-observable).** `STAGE_B_ENABLED=False` (nothing reaches
> Du). `note_for_draft` now SHADOW-LOGS every would-fire decision (mode · grade · confab · suppressed_by ·
> identity_hit · would_inject) → `data/epistemic_stageb_shadow.jsonl`; the orchestrator calls it on EVERY
> human cycle for the log but injects only when the flag is on. Verified across all branches; isolation held;
> both files parse. **Re-enable gate:** read `epistemic_stageb_shadow.jsonl` post-restart — flip back ON only
> once `would_inject=true` rows are genuinely-FACTUAL overclaims (not philosophical exchanges); if they're
> still existential, tighten the trigger first. Stage A (grading) untouched — keeps working.

_[original lines 238-248]_

> **★ BUILD STATUS (2026-07-01):** **Stage A BUILT + verified** (preassess shadow, 2026-06-30). **Stage B BUILT +
> verified 2026-07-01, flag-gated OFF** (`epistemic_state.STAGE_B_ENABLED=False`). Both promotion gates met from
> the live log: pre→post grade tracking **98% exact** (52/53, join on cycle_id) and the discrimination is genuine
> (KNOW↔grounded neg-confab, SUSPECT↔+0.45 abstract overclaim). Stage B: `note_for_draft()` + `committed_note()`
> (committed/source-framed strings + hedge ban-list) in `epistemic_state.py`; computed BEFORE the Executive
> (`orchestrator.py`, gated) so it shapes the `synthesis` Voice renders; injected in `executive_node.py`.
> **★ IDENTITY-SCOPED** — suppressed on reflective/existential cycles (owning "I don't know a *fact*" is honesty;
> pushing "I don't know *who I am*" is the dissolution the commit build cures — that domain is the commit work's).
> Verified: gate unit test (fires on factual overclaim; silent on identity/grounded/below-gate) + `smoke_test.py`.
> **Restart-gated.** *Next:* restart → let flagged factual cycles accrue → a **decoupled rater** (Travis/Emissary)
> confirms on a sample that revised utterances read *cleaner & more committed, not hedgier* → flip `STAGE_B_ENABLED`.

_[original lines 346-364]_

### Wiring correction (from the in-code map — the original plan's anchors were stale)
- `assess()` is at **`orchestrator.py:1091`** (not `:990`), post-Voice (Voice renders `:931`). `_prov` now also
  feeds `conflict_trace.record()` `:1131` — still log-only; the write-only diagnosis holds. `preassess` does NOT
  exist (net-new). Add `state.epistemic_assessment` field (`schema.py` ~`:731`, reset each cycle).
- **Stage A insertion:** right before Voice (`orchestrator.py` ~`:929`), after the Executive. Every input
  `assess()` needs is bound by then; it already grades **`state.reflection.confidence`** (the *draft's* confidence,
  `epistemic_state.py:273`) — so no grading-logic change, just call the same chain on the draft and store the
  result. (Consequence: pre- and post-Voice grades will correlate very highly *by construction* — which is exactly
  promotion-gate (a), so that gate is nearly free; the real gate is (b), the decoupled overclaim-quality check.)
- **Stage B injection:** mirror `AttentionSchema.note()` — gated `lines.append(...)` at **`reflection_node.py:248`**
  and **`executive_node.py:206`** (the proven template, same family as the existing `known_errors_note`/`self_facts`
  injections). **Never inject at Voice** (`voice_node.py` is mouth-not-mind — can't add/remove claims).
- **★ Actuation-path correction (gotcha):** the plan said the note "plugs into the existing re-bind loop" at
  `:706` — but **that loop runs BEFORE Reflection produces a draft**, so `preassess` can't grade a draft there. The
  draft only exists after `:815`. So the real actuation is: Reflection draft → `preassess` → inject the note where
  it is **seen by the Executive (always runs, `:911`) and by any Critic-reject Reflection re-pass (`:874`)**. For
  Phase 1, rely on the **Executive injection** (guaranteed to see it and able to redirect the final shape);
  **defer** a dedicated "preassess → re-run Reflection once if overclaim" mini-loop to Phase 2 only if the
  Executive path proves too weak. (Don't claim a Reflection revision the architecture doesn't give for free.)

_[original lines 384-389]_

### Sources (research pass)
Johnson/Hashtroudi/Lindsay 1993 *Source Monitoring* · Koriat 1997 cue-utilization · Haggard et al. 2018
Limitations-Owning IH · Torre & Lieberman 2018 affect labeling · Hyland hedges/boosters & stance · Williamson norm
of assertion · Tetlock estimative-probability · Kadavath 2207.05221 (P(IK)) · Lin 2205.14334 · Tian 2305.14975 ·
**Zhou 2302.13439 (epistemic markers — most important)** · Dhuliawala 2309.11495 (CoVe) · Huang 2310.01798
(can't-self-correct) · R-Tuning 2311.09677 · SelfCheckGPT 2303.08896 · persona-drift 2402.10962.

_[original lines 398-406]_

> **★ RESCOPED 2026-08-24 (J-0150, D-0005 follow-up, F-0110).** As originally written this section sourced
> the adjacency from `memory_links` (`distilled_from` + `relates_to`) — the OLD table, diagnosed by
> `docs/plans/memory_multiway_linking.md` §2 as "MiniLM cosine wearing different clothes, not a second kind
> of connection." That plan built a purpose-made typed relational table, `memory_edges`
> (`core/memory_edges.py`: `resolves`/`answers`/`dreamt_from`/`kept_from`/`revisits`/`about_object`/
> `wrote_to`/`co_recalled_developing`/`contradicts`), specifically so a future trail upgrade would consume
> real relational structure instead of re-deriving cosine a second way. The Approach below is rewritten to
> source from `memory_edges`. **This is a doc-scoping fix only — no code changes; both Improvement 2 and
> `memory_multiway_linking.md`'s M2 remain pre-build.**

_[original lines 413-431]_

- **★ Gap finding, verified 2026-08-24 against the live `core/memory_edges.py` source and the 1,676-row
  count `memory_multiway_linking.md` §6 reports (resolves 820 · answers 387 · kept_from 387 ·
  correspondence_with 82):** **zero live rows have `src_kind='fragment' AND dst_kind='fragment'`.** Every
  edge type currently written is bipartite onto a non-fragment kind: `resolves` is `cycle→shadow_event`
  (`memory_edges.py:165`), `answers` is `fragment→question` (`:198`), `kept_from` is `keepsake→fragment`
  (`:227`), `correspondence_with` is `fragment→person` (`:259`), `dreamt_from` is `dream→fragment` /
  `dream→tension_material` (`:125,128`), `part_of` is `fragment→dream` (`:113`). The two edge types that
  WOULD be fragment↔fragment — `co_recalled_developing` and `contradicts` — are named in
  `memory_multiway_linking.md`'s M2 spec (§6) but do not exist as `add_edge()` calls anywhere in
  `memory_edges.py` today (grepped for both names: zero matches; M1's `log_co_recall` presently writes only
  to a JSONL ledger, `co_recall_ledger.jsonl`, not into the `memory_edges` table). **Consequence: building
  `links_adj` from `memory_edges` as it stands today would load an empty matrix** — the PPR walk would
  silently degrade to the pure-kNN term (`β·links_adj` = 0 everywhere), which is worse than not building it
  yet, because it would present as a links-aware upgrade while being functionally kNN-only underneath.
- **This is the concrete form the D-0005 dependency-ordering note takes:** Improvement 2 cannot productively
  consume `memory_edges` until `memory_multiway_linking.md`'s M2 phase ships and writes real
  `co_recalled_developing`/`contradicts` rows — and M2 itself is gated on M1's founder week-read of the
  co-recall ledger (§6: "does the progress-gated web differ from naive, and does it avoid re-drawing the
  basin?"), not yet done as of this writing.

_[original lines 475-485]_

**★ 2026-08-25 — J-0263 SHIPPED, and this Improvement's `links_adj` precondition is CONFIRMED still
unmet.** As predicted just above: `core/memory_edges.py` gained `edge_aware_neighbors()` for M2's own
shadow-mode greedy-walk augmentation, but it reaches a second fragment by BIPARTITE PROJECTION through
`question`/`keepsake`/`person`/`dream` hubs (plus the one already-direct type, `transformed_into`) —
it does not write any new `src_kind='fragment' AND dst_kind='fragment'` rows into `memory_edges` itself,
so a `SELECT ... WHERE src_kind='fragment' AND dst_kind='fragment'` query (this Improvement's own
`links_adj` load, `:514`) still returns only the pre-existing 462 `transformed_into` rows —
`co_recalled_developing`/`contradicts` remain at zero. Whether to wire `log_co_recall` (M1) to also
write those two edge types for real is now a named open question rather than an implicit gap — see
memory_multiway_linking.md's Current State and **D-0051** (opened alongside J-0263). Improvement 2
should keep watching D-0051, not J-0263 itself (J-0263 is done; the precondition is not).
