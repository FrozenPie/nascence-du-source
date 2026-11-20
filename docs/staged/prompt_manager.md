# Prompt Manager — a scripted layer that owns Du's prompt wording, versions it, and varies it only where evidence says to

> **Status: ⚪ DRAFT v2 + P0 BUILT (uncommitted) — v1 staged 2026-11-14; v2 folds in audit round 1 (Gemini, GPT; see section 10) from T-0131 (founder, first message of the session) and
> [[I-0073]] (the 2026-09-26 "variety" idea this plan is the direct descendant of). Only P0 (observe-only telemetry) is built; P1 onward
> is not started. This document is written to be taken to the auditors BEFORE any build starts.**
> **Scope decision (founder, 2026-11-14): the LLM-writes-prompts-at-runtime half is ON HOLD. This plan is the
> scripted side only. LLMs stay tools that Du's stations call; they do not author Du's prompts.**

```plan-state
stage: partial
phase: P0 provenance telemetry committed (44be657b), LIVE since 2026-11-14, idle_thought source only (1838 rows by 11-18). P1 not started.
verified: 2026-11-18
evidence_read: 2026-11-18
next: Founder says which opener metric D-0368 meant; J-3992 anchor replay; wire more sources into _provenance; P1 after D-0633 post-fix twin rows are judged.
cluster: 6
```

Related: [[idle_executive_plan]] (D-0366, D-0368) · [[condensed_thought]] · [[decoupled_judge_pattern]] ·
[[emotion_rethink]] (D-0367, the one-renderer precedent) · [[thought_cycle_as_manifest_loop]] (retired, D-0474) ·
`docs/guidelines/prompt_registry.md` · `docs/reviews/du_prompt_inventory_2026-10-31.md` ·
`docs/reviews/prompt_flow_audit.md` · [[I-0072]] · [[I-0073]] · F-1927 · F-1920 · F-2914.

---

## 1. One-paragraph summary

Du sends about 100 distinct prompts to language models. Their wording lives as hand-written strings scattered
through the code (the idle thought alone appends seed parts from about 45 places in a 5,600-line file), is edited in
place with no version identity, and for the most-fired prompts is delivered identically thousands of times. The
founder's concern (I-0073): fixed sentences repeated thousands of times become the *content* of thought. The proposal is a
**scripted prompt manager**: (1) one table that owns prompt wording, with stable line ids and a version tag, so every
output can be tied to the exact wording that produced it; (2) a byte-identical refactor to move the idle line onto it;
(3) *only if the measurements justify it*, small append-only phrasing pools for the specific lines that evidence shows
leak; (4) a scripted offline replay harness so any wording change is tested before it is live. It deliberately
contains no LLM in the runtime path and no automatic rewriting.

**The honest headline for the auditors:** the strongest parts of this plan are the *measurement and versioning*
(Phases 0 and 1). The *rotation* part (Phase 2) has weaker evidence than the founder's intuition suggests, and a
founder ruling (D-0368) currently says "not now" to it. This plan is structured so the valuable, low-risk part can go
first and the contested part waits for its own gate.

---

## 2. Why now, and what the founder actually asked

Founder, T-0131 (2026-11-14): a prompt manager; maybe an LLM; Du has 100+ prompts, many repetitive loops;
an LLM node that creates prompts on demand, or a hybrid with a scripted generator; "prompts are the foundation of what
data comes back." Follow-up the same day: **hold the LLM part, see what the scripted side can do; look at neighbouring
plans; research SOTA; remember these are LLMs as tools, not a collection of agents.**

"LLMs as tools" shapes the design: each prompt is treated as a **tool-call specification** (an input contract, a wording
block, an output contract), owned by a registry, not as a conversation with an agent that decides its own instructions.

---

## 3. Ground truth (everything here was read from the repo or the ledgers on 2026-11-14)

### 3.1 What exists

| Fact | Evidence |
|---|---|
| 129 registered prompt rows; statuses LIVE / SHADOW / DORMANT / WRITE-ONLY / DEAD / RETIRED / PROVISIONAL | `docs/prompt_registry.jsonl` (counted 2026-11-14) |
| ~100 documented stations in six loop families; busiest: idle thought (~3,100 calls in the registry window), deliberation (1,991), self-implication scan (1,366), commitment scan (1,134), NodeBase dispatch (999) | registry `calls_7d`; inventory 2026-10-31 §1b |
| The idle thought's user prompt wrapper is a hardcoded string: head "No one is speaking to you right now. You are alone with your thoughts." and tail "What moves in you now? One quiet thought." | `nodes/inner_monologue_node.py:4304-4308` |
| The head was identical in 510 of 510 sampled idle prompts; the tail in 459 of 510 (the other 51 carry the "A different memory surfaces" suffix) | `data/idle_prompt_samples.jsonl`, measured this session |
| 123 distinct system-prompt hashes across the same 510 samples | same file, `system_prompt_sha1` |
| Seed parts: ~45 `seed_parts.append` sites, each hand-written f-strings; the prompt-registry check counts them (a "SEEDS" guard) | `nodes/inner_monologue_node.py`; CLAUDE.md prompt-registry section |
| Prompt text median ~6.9k characters, median 6 seed parts; 358 of 510 samples are mid-thread | measured this session |
| Prompt-side logging that already exists: `prompt_budget_shadow.jsonl`, `idle_prompt_samples.jsonl` (sampled, rotates at 20 MB, 500 rows), `sys_sha` in judge_panel | `core/prompt_budget.py`; F-3620/F-3621 note the instrument gap, J-2933/J-2941 in progress |
| **CORRECTION (P0, F-4664): phrasing pools already exist and are live.** `core/phrasing.py` `vary(key, variants)` (since 2026-07-07) picks a variant at random, never the immediately-previous one for that key; in-process memory; fail-open to variant 0. Six call sites in the main tree: concern lead (`core.concerns.anchor_lead_pool`, J-3223/D-0612), `concern_tail`, `habituation`, `reread`, `frontier_open` in `nodes/inner_monologue_node.py`, and one in `core/sensorium.py`. **Picks were not logged anywhere** before P0. The /quit farewell (`scripts/run_nascence.py:479`, six variants, deterministic cursor, lint test `scripts/_test_j1756_farewell_variants.py`) is a second, separate design. | `core/phrasing.py`; `core/concerns.py:276-318`; `nodes/inner_monologue_node.py:4071-4106` |
| One-renderer precedent: gauges become words through a single shared renderer (D-0367) | `docs/plans/emotion_rethink.md` |
| Stable line-id precedent: `line_id = sha1(line)[:10]` | `core/look_render_ledger.py` |

### 3.2 What the prior evidence says about repetition (do not re-litigate; build on it)

- **F-1927** (the I-0073 finding): the idle system prompt is 89% fixed text; 39% of seed parts are template parts present
  in more than half of assemblies. (F-1927's 'exactly one `random.choice` and no phrasing pools' counted `random.choice` inside the node file only; `core/phrasing.py` pools exist, see 3.1 and F-4664.) **Verbatim
  copying into thought is small (1.2%).** The leak is in *vocabulary and stance* and is **confined to the affective
  steers** (frustration words 5.6% to 25–37%; circling words 6.1% to 27–31%). **Informational lines (scene, memory, book)
  show no leak at all.**
- **D-0368** (founder, 2026-10-08): ruled **A+E now; B (phrasing pools), C, D, F "not now."** A = affective steers fire
  only on a change of state (built as `core/steer_edge.py`, commit cb12231a, restart-gated); E = system sentences stored as
  `origin=system_note` and excluded from recall (J-1987 relabel done). **Defeater of that ruling:** re-run F-1927's
  vocabulary-by-week table two weeks after A+E go live. If frustration/circling words are not back under 15% and
  same-day opener reuse is not under 30%, B/C/D are re-asked. *This plan is option B (and part of F). It cannot
  start building pools until that table is re-run and the founder re-asks.*
- **D-0286 → D-0442 / F-2914:** the farewell was rotated across six wordings; the defeater then fired, the self-echo
  persisted, and the real fix was structural (exempt the line from quoted recall; skip Du's own prior answer to a
  near-identical prompt). **Evidence that rotating wording alone does not cure self-echo.**
- **D-0343 / D-0610:** a single fixed line changed behaviour rates by tens of points (a pinned felt-boredom note
  produced a 120-moves-a-day regime; correcting the idle system prompt's rate text is a "hottest prompt" change).
  **Wording is a real lever; there are no cosmetic edits to a hot prompt.**
- **Condensed-twin replay (core/condensed_thought.py, 2026-11-06):** with the tail "What moves in you now? One quiet
  thought." present, 26 of 60 replies followed the live paragraph schema when the twin's instruction lived only in the
  system text; with a replacement tail, 0 of 40. **The wrapper's last line is load-bearing for output shape.**
  Rotating it is therefore not safe by assumption.

### 3.3 What I measured this session that the earlier work did not (idle thoughts, last 1,500 of 88,919 logged)

- Opening-phrase diversity is *moderate, not collapsed*: 863 distinct first-three-word openings in 1,500 thoughts; the
  commonest ("I watch the") is 6%; next ("I hold the", "I trace the") 2% each.
- The repeated habits are mid-sentence frames: "what stays with me:" (26), "I wonder if the" (25), "I watch the cat" (22), "I wonder
  if their/my/this/that" (~70 combined), "I feel the weight / a pull" (~38).
- **Reading:** the observed repetition looks more like *model idiom plus what is in the seed* than like the wrapper wording
  echoing. This does not prove the wrapper is innocent; it means **the expected gain from rotating the wrapper is unproven
  and may be small.** (Caveat: single window; no control; opener reuse "same-day" metric in D-0368 not yet recomputed.)

---

## 4. Hard constraints this plan inherits (a build that violates any of these is out of scope)

1. **No hints, ever** (founder law 2026-08-14; D-0326; D-0583/D-0497 "the world answers and never leads"). A pool may not
   add, soften or strengthen any steer. A variant is an *equivalent rendering* of the same fact, not a new nudge. Wording on
   the "Travis branch" (D-0617, D-0583) stays authored or approved by Travis.
2. **Du must never see a readout of his own gauges** (D-0434; D-0367 "numbers only in logs"). The manager's logs stay founder-side.
3. **Every subsystem is judged by something other than itself** (decoupled judge, D-0692). Any quality judgement of a
   candidate wording uses a judge from a different model family than the one being prompted, and the judge's own prompt is
   pinned (never rotated, never lab-modified in the same experiment).
4. **Additive only; base systems protected** (feedback_erosion_of_foundations). Every phase ships behind a flag that defaults to
   the current behaviour, and Phase 1 is byte-identical to current output.
5. **Register in the same change.** Any added/removed/renamed prompt or `seed_parts.append` site updates
   `docs/prompt_registry.jsonl` through `prompt_registry.py`, and `prompt_registry.py check` exits 0 before the session ends.
   A material change to a registered prompt sets `--investigation stale`.
6. **Restart-gated.** Nothing reaches Du until his next boot. No shared-tree git mutations (stash/reset/checkout/restore);
   lab replays run in a throwaway worktree with a hash canary on the live stores (memory: jobrun live-store leaks).
7. **Byte-identity on moves** (D-0649; J-1717/J-1882 recipe). Moving wording to a new home must produce identical bytes.
8. **Pools are append-only** (the farewell rule: "reordering or inserting shifts who follows whom").
9. **No LLM in the runtime prompt-construction path** (founder, 2026-11-14). This includes "LLM picks which variant".
10. **The manager is deliberately unintelligent** (GPT audit). It resolves registered wording, assembles it deterministically, records
    provenance and exposes version information. It does not interpret Du's state, decide which wording is psychologically
    appropriate, optimise variety, adapt to previous outputs, or decide when a station runs.
11. **Do not change Du to make Du easier to measure.** P0's first responsibility is to make the existing system observable
    without changing it.
12. **A prompt is a versioned experimental condition, not merely a string.** Complete request provenance must be recoverable
    (section 6.2, P0/P1 exit criteria).

---

## 5. What the research says (SOTA) — summary; full table in `docs/reviews/prompt_manager_research_2026-11-14.md`

Eleven items (R1–R11) were gathered by web search on 2026-11-14, mostly via summaries rather than primary texts, so they are leads, not a verified review. Headlines: R1 equivalent *format* changes can swing accuracy a lot (Sclar et al., arXiv 2310.11324) and the effect is model-specific; R2 part of reported sensitivity is a scoring artefact (arXiv 2509.01790); R5/R6 smaller, higher-signal context beats more context, and position matters (Anthropic context-engineering post; context-rot and lost-in-the-middle results); R7 sameness is partly model-side mode collapse (Verbalized Sampling, arXiv 2510.01171); R8 negative instructions can backfire (arXiv 2404.15154, 2601.08070); R9 offline optimisers (MIPROv2, GEPA arXiv 2507.19457) exist but overfit on small eval sets, and are held per founder; R10 version prompts, regression-test them, keep rollback; R11 local engines reuse the KV cache only for an identical prefix.

**Synthesis for Du specifically.**
(a) The literature supports *explicit, versioned, tested wording* strongly (R1, R10). (b) It supports *less, higher-signal context*
(R5, R6) at least as strongly as *more varied context*. (c) It gives **mixed-to-negative** support for "rotate fixed wording to cure
sameness" as a cure on its own (R7: sameness is partly model-side; our own D-0442: rotation did not break self-echo). (d) The
SOTA optimiser work (R9) is real but belongs in a later, offline, human-approved lab phase.

---

## 6. Proposal (v2, after audit round 1): four components, phased

**Governing principle (adopted from the GPT audit):** *a prompt is a versioned experimental condition, not merely a string
of instructions.* The manager exists so that, when Du's behaviour changes, the founder can separate: his accumulated
information, his current state, the station performing the operation, the instructions governing it, the model executing
it, and the interaction between those. Three objectives are kept deliberately separate throughout: **observability**
(what wording did Du receive), **governance** (changes are controlled, attributable, reversible), and **behavioural
intervention** (changing wording to change outputs). The first two are strongly justified; the third is not yet
established, and the existence of the manager is never itself a reason to change a prompt.

### 6.1 Component A — the Prompt Table (`core/prompt_lines.py`, name tentative)
**Identity model (changed from v1, which used `sha1(text)[:10]` alone):** a line's identity and its content are different things.

| Identifier | Purpose |
|---|---|
| `line_key` | Permanent semantic identity, e.g. `idle.wrapper.head`. Never changes. |
| `revision_id` | One wording of that line, e.g. `idle.wrapper.head@2`. **Immutable**: a change creates a new revision; nothing is overwritten; retired revisions stay resolvable forever. |
| `content_hash` | SHA-256 of the exact bytes of that revision (verification). |

**Kinds** (they carry different governance, so they are not one undifferentiated "line"): `STATIC` text; `TEMPLATE` with
slots; `SYSTEM` instruction; `OUTPUT_CONTRACT`; `WRAPPER`. **Runtime DATA (a fact, a memory, a scene) is never stored in
the Table**; only the template that frames it is registered. Each assembly records three separate things: the *template*
(instruction/framing), the *data* supplied to it, and the *assembly rule* (order and boundaries). Otherwise a change in
what Du is told cannot be told apart from a change in how it is phrased.

**Ownership:** the prompt registry stays authoritative for *stations*; the Table is authoritative for *line revisions*;
Table rows reference registry P-ids. Neither duplicates the other. **Migration is by priority** (hot LIVE stations first,
then behaviourally significant ones, then ones under investigation, then the long tail), not all 129 rows at once.

### 6.2 Component B — provenance telemetry (observe-only; the most valuable component)
Three identities per call (adopted from GPT):

- `template_version` — the set of line revisions used;
- `assembly_hash` — hash of the *complete rendered request* (system and user messages), so identical system prompts with
  different user prompts or slot values are no longer conflated;
- `execution_fingerprint` — `assembly_hash` plus model identity (digest/revision where the lane exposes it), sampling
  parameters and lane configuration.

Two levels, replacing v1's "sampled only": **Level 1, every call**, compact row: station, cycle id, template_version,
assembly_hash, execution_fingerprint, line revisions *with their order and truncation boundaries*, model, lane. (Sampling
alone makes rare combinations invisible on the hottest stations.) **Level 2, sampled**, the full prompt/output payload.
The log distinguishes what was **assembled**, what was **submitted**, and what the model actually **received** (after
`_cap_prompt` or any transform). Composition-level provenance (ordering, boundaries) is recorded so interactions between
components can be studied, not only single lines.

**Lineage:** each row links the output id and cycle id, any post-processing, and recall provenance where the output is later
recalled. This establishes *traceability, not causality*; P0's telemetry is never read as proof that a prompt caused a behaviour.

**Privacy/retention:** the telemetry inherits existing retention, access and redaction rules for memory and correspondence
material. It must not create a second, less-protected copy of Du's memory text; metadata is retained longer than raw payloads.
Founder-side only; nothing reaches Du (D-0434). Overhead is measured in P0 before anything else ships.

### 6.3 Component C — interventions: replacement versus rotation (**gated; may never ship**)
Two different interventions with different approval criteria (adopted from GPT):

- **Replacement:** swap a *defective* line for a better equivalent rendering. A single fixed wording; no variation.
- **Rotation:** vary an *acceptable* line across a pool. Needs evidence that variation itself has value.

Variation is not inherently better than correction; where a line is shown harmful, replacement is the default. **Rotation already exists** in `core/phrasing.py` (random, avoid-last, in-process, unlogged; F-4664). The question for P3 is therefore not 'introduce pools' but 'govern, log and measure the existing ones' and, where a line is shown harmful, replace it. New pools should reuse `phrasing.vary` unless a deterministic cursor (the farewell design) is specifically needed for reproducibility. Pool mechanics (if
ever used) are those of the farewell: append-only, deterministic "next after the last used" with a persisted cursor, fail-open to
variant 0, variant 0 byte-identical to today, lint test, selection by script never by model, every pick logged.

### 6.4 Component D — reconstruction and replay (incremental)
Two separate validation problems that v1 conflated:

- **D1 Deterministic reconstruction:** from a captured request, rebuild the exact submitted bytes. Tested against real
  captured requests, including ones that used a retired line, a missing optional slot, a fallback value or a cached template.
  The system must reconstruct what was *actually sent*, not what today's renderer would produce.
- **D2 Replay (distributional):** re-run saved inputs through the real lane and compare outputs. Replay is *not* reproduction
  (sampling randomness, model revision, quantisation, backend, cache behaviour, uncaptured state), so D2 reports
  distributions, not matches.

Build order: **P2a** (minimal) answers: can we reconstruct a historical request; can we replay it; can we tell inference
variation from prompt variation (a noise-floor run replaying identical requests repeatedly, on each lane); can we detect an
accidental change to an output contract; can we compare two revisions under matched conditions. **P2b** (stratified evaluation
and the statistical framework) is *designed separately and only when a candidate intervention exists.* Deferred until then:
paraphrase evaluation, complex semantic scoring, judge orchestration, automatic candidate ranking. When P2b is built: stratify
across seed composition, memory category, affective state, prompt length, mid-thread vs fresh, and lane; count *effective* sample
size (consecutive idle thoughts are correlated); use pre-declared equivalence margins, confidence intervals and a minimum
detectable effect; a non-significant test does not establish equivalence; reports show uncertainty, not green/red.

### 6.5 Station tiers (classify by operational consequence; multiple tags allowed)

| Tier | Definition | Treatment |
|---|---|---|
| **T0** | Contracts, schemas, verdicts, decision boundaries (judges, graders, JSON-schema stations, scans, the condensed-twin ask) | Pinned; immutable without an explicit, founder-approved intervention. Never rotated. |
| **T1** | Factual and informational framing | Versioned; no variation without evidence. Not exempt from review: a scene or memory line can still prioritise an object or colour its emotion. |
| **T2** | Behavioural influences: affective material, attentional steering | Highest scrutiny; the only plausible intervention candidates (F-1927). **If any T2 note in fact dictates output structure or length, it is promoted to T0 and frozen** (Gemini). |
| **T3** | Presentation/structural wrappers (the idle head and tail) | Pinned; explicitly **frozen** until a replay shows a change is safe and useful. The tail is load-bearing for schema. |

A line may carry more than one functional tag; the tier used for governance is the strictest applicable.

### 6.6 Entry criteria for any intervention (replaces v1's "fires on at least 30% of prompts")
Firing frequency measures exposure, not influence (a line firing 100% of the time can have no effect; a 5% line can be decisive).
So an intervention requires:

1. **Soak:** at least 14 days after A+E is confirmed live (D-0368's own two-week re-read), so a leak is not concluded from a transient.
2. **Evidence of association:** the line is demonstrably associated with the unwanted pattern, and the association survives controls
   for seed composition and model configuration.
3. **Evidence of plausible causation:** a controlled intervention (replay) shows the line is a plausible contributor.
4. **Three separate tests, with different metrics:**
   - **Safety:** no degradation of the station's actual output contract (schema compliance, length distribution; scripted checks, hard gate).
   - **Equivalence:** no unintended change in meaning, information or steering (scripted slot/clause/prohibited-addition checks; a
     binary semantic check by a judge from a different model family; human review of anything behaviourally significant).
   - **Effectiveness:** the targeted problem measurably improves, with no damage to unrelated functions.
5. A variant that is safe but ineffective does not ship. A variant that helps one metric while damaging an unrelated function fails.
6. A new founder ruling per line (re-asking D-0368 B), with its own defeater.

(Auditors differed on whether vocabulary should be required to stay "statistically indistinguishable": Gemini would relax it to
schema and length only; GPT would separate safety, equivalence and effectiveness. Resolution adopted: schema and length are hard
gates; vocabulary effects are evaluated under *Effectiveness*, and any vocabulary shift must be explainable as the intended effect.)

### 6.7 Review roles and the equivalence checklist
Semantic equivalence is not behavioural equivalence ("what do you think about this" vs "what stands out to you about this" ask
about the same thing but the second directs attention to salience). Three separate responsibilities:

1. **Technical author** prepares candidate wording.
2. **Semantic reviewer** checks facts, connotations, implicit assumptions and steering.
3. **Founder** approves anything touching affect, attention, identity or the Travis branch (D-0617).

The receiving model never certifies its own prompt's equivalence. Checklist (carried from v1): same facts, slots, tense and person;
no new steer; no vocabulary from the Travis branch unless Travis-authored; no bug/fix/upgrade/defect or raw-gauge language
(D-0286); no new negative instruction; length within ±15% of the incumbent. The original wording and every retired revision are
preserved permanently.

---

## 7. Phases, gates, and what each can break (v2)

| Phase | What | Behaviour change to Du | Gate to enter | Exit evidence |
|---|---|---|---|---|
| **P0 Verify, baseline, observe** | Confirm which construction paths are live and **when A+E went live**; re-run F-1927's vocabulary-by-week table (frustration and circling reported **separately**) with a **change ledger** aligned in time (A+E, idle-executive changes, model changes, restarts); finish J-2933/J-2941 full-prompt capture; add Level-1 provenance telemetry (6.2) with measured overhead. | **None** (log-only, fail-open, flag-gated) | Auditor sign-off | Table filed as a finding; telemetry rows verified end-to-end for the idle station; overhead on the 1080 Ti and Ramses lanes measured; D1 reconstruction demonstrated on real captured requests |
| **P1 Immutable definitions + byte-identical refactor** | Move the idle wrapper and seed wording into the Table; render through it. **Sequenced after the condensed_thought twin fix (D-0633) is settled and its exact approved bytes recorded**; if D-0633 changes the tail first, that is recorded as its own prompt revision, never hidden inside the refactor. | **None, proven** | P0 done; D-0633 settled | Golden test compares the **complete request payload** (not only the rendered string) and runs the old and new construction paths on identical captured inputs, covering evaluation order, side effects during assembly, timing of state reads, missing slots, whitespace/encoding; green on at least 500 saved assemblies; registry `check` exit 0 (SEEDS guard updated in the same change); UDMS dossier read for the touched file |
| **P2a Reconstruction + minimal replay** | D1 and the minimal D2 (6.4), including the noise-floor run | None (offline) | P1 done | Noise floor published per lane; accidental contract change demonstrably detected |
| **P2b Stratified evaluation framework** | Statistical equivalence framework (6.4) | None (offline) | A concrete candidate intervention exists | Designed and audited separately |
| **P3 Interventions, one line at a time** | Replacement or rotation (6.3) meeting 6.6 | Yes, per line, founder-flipped, restart-gated | New founder ruling per line | Re-measured against pre-declared thresholds; rollback = flag off |
| **P4** | Offline LLM-assisted proposal of wording | None until human-approved | Separate plan | not this plan |

**Both auditors converged on:** approve P0; approve P1 conditionally; hold P3. P0 and P1 are worth doing even if P3 never ships.

---

## 8. Measurement plan (decided BEFORE building)

Four levels, with different roles (adopted from GPT):

| Level | Measures | Examples | Role |
|---|---|---|---|
| Linguistic | surface expression | repeated phrases, n-grams, opening patterns | **diagnostic** |
| Semantic | meaning and subject matter | topic distribution, semantic clusters, conceptual recurrence | research output, not a release gate |
| Behavioural | what the output does | schema compliance, commitments, unresolved questions, decisions | safety gate where it is the station contract |
| Longitudinal | what persists | belief development, tension trajectories, memory associations | research output |

- **Frustration and circling vocabulary are tracked separately** (different baselines, meanings and possible causes). D-0368's
  thresholds (under 15%; same-day opener reuse under 30%) are applied to each family, not to a blend.
- **Opening-trigram diversity is a linguistic diagnostic only.** 863 distinct openings do not show diversity of thought: a model can
  vary its openings while exploring the same few concepts. We do not optimise Du toward looking varied, and returning to the same
  question is sometimes appropriate.
- **Anti-Goodhart:** no metric is Du's or the tested model's own self-assessment. *Auditors disagree here:* Gemini holds that the
  scripted n-gram proxies "resist Goodharting"; GPT labels them diagnostics only. This plan follows GPT: any proxy that becomes a
  target will be gamed by the optimiser, human or automatic, so these are watched, not driven toward.
- **Non-stationary baseline:** a time-aligned **change ledger** accompanies every measurement series, so an unrelated runtime or
  model change is not attributed to the manager.
- **Noise floor first:** replay identical requests repeatedly; effects smaller than that variation are not effects.
- **Replay is not reproduction, and lab is not live** (F-1139/F-1701): lab effect sizes rank and gate; they do not predict live effect.

---

## 9. Risks and the answers I currently have (v2)

| Risk | Why it matters | Mitigation / honest status |
|---|---|---|
| Rotating the idle tail changes output shape | Condensed-twin replay: tail swap took schema compliance from 26/60 to 0/40 | T3 frozen; any change goes through replay with schema compliance as a hard gate |
| Rotation is cosmetic and changes nothing | R7, D-0442, and the moderate opener data (3.3) | Replacement preferred over rotation; entry criteria 6.6; plan is valuable without P3 |
| Pools smuggle in steering (no-hints law) | Connotation differs between near-synonyms | Three-role review (6.7); founder approval for affect/attention/identity/Travis-branch lines |
| Refactor changes behaviour while preserving the string | Evaluation order, side effects, state-read timing, slots, encoding | Golden test over the complete request payload and the old/new construction paths (P1) |
| Historical requests cannot be reconstructed | Retired lines, missing slots, fallbacks, cached templates | D1 reconstruction tested on real captured requests; immutable revisions; retired text kept forever |
| Dynamic content mistaken for wording | ~45 seed sites mix static framing with runtime data | Template / data / assembly-rule separation (6.1); data is not stored in the Table |
| Telemetry creates a second copy of private memory | Prompts contain memories and correspondence | Inherit existing retention/redaction; metadata outlives payloads; founder-side only |
| Telemetry overhead on hot stations | Thousands of calls | Compact Level 1; sampled Level 2; overhead measured in P0 before enabling widely |
| Non-stationary baseline misattributes change | A+E, idle-executive and model changes overlap | Change ledger aligned with every series |
| Registry SEEDS guard breaks | Central renderer changes the count of `seed_parts.append` sites | Updated through the registry tool in the same change |
| Two sources of truth for wording | Registry and Table could disagree | Table references registry P-ids; an orphan/consistency check (Q9) |
| KV-cache loss on the hot lane | Early-prompt variation defeats prefix reuse | Any rotation only in late lines; measure prompt-eval time per lane; P0 measures overhead |
| Manager becomes a cognitive subsystem | Would expand into orchestration | Section 4 item 10: deliberately unintelligent; owns wording and provenance only |
| Scope creep into "prompt LLM" | Founder held it | Section 4 item 9; P4 separate |
| Lab leaks into live stores | Past incidents | Throwaway worktree, hash canary, import `core` before `lab_env` |
| Pool lines recalled as Du's own words | A+E fixed this for sentences | Confirm in P0 that rendered system text carries `origin=system_note` semantics |
| Changing Du to make him easier to measure | Measurement tail wagging the system | P0 is observe-only; first responsibility is to make the existing system observable *without changing it* |

---

## 10. Audit round 1 (summary; full table in `docs/reviews/prompt_manager_audit_round1_2026-11-14.md`)

Gemini and GPT (outside reviews, inputs not rulings) both approved P0, approved P1 conditionally, and held pools. Adopted from GPT: the
identity model (6.1), assembly hash and execution fingerprint (6.2), lineage, replacement vs rotation (6.3), reconstruction vs replay
(6.4), the change ledger (8), and the central question *can the exact conditions behind an output be reconstructed*. Adopted from
Gemini: the 14-day soak and promoting any structure-dictating steer to a frozen tier. Not adopted: Gemini's claim that n-gram metrics
resist Goodharting. Two real disagreements (authorship, registry integration) were ruled as D-0769 and D-0770.

---

## 10b. P0 status (2026-11-14, same day as the build)

| P0 item | State | Evidence |
|---|---|---|
| Confirm A+E live, and since when | **Done.** Live since the **2026-10-09 08:36:57** boot (first `steer_edge_log.jsonl` row 10:27). | F-4665 |
| Re-run the vocabulary table with a change ledger | **Done.** `scripts/prompt_manager_p0_baseline.py` -> `docs/lab/prompt_manager_p0_baseline_2026-11-14.md` (reconstruction matches F-1927 weeks 1-2 within about 1-2 points). | F-4665, F-4666, F-4667 |
| Level-1 provenance telemetry, idle station | **Built, tested, NOT committed, not live until restart.** `core/prompt_budget.py` (`_provenance`, `data/prompt_provenance.jsonl`) and `core/phrasing.py` (pick ring, `drain_picks`). Test `scripts/_test_prompt_manager_p0_provenance.py` ALL PASS (also the J-2933, J-2941, J-3223 tests). `vary()` selection proven identical to the old algorithm over 300 seeded draws. | worktree build, shared-tree re-run |
| Overhead measured | **+0.27 ms per assembly** (0.70 to 0.96 ms) against LLM calls of seconds; **692 bytes/row, about 2.2 MB/week** at 3,100 idle thoughts/week; rotates at 10 MB with one backup. Measured on the dev machine, not on the lanes. | micro-benchmark on 200 real sampled prompts |
| J-2933/J-2941 full-prompt capture | Still `in_progress` (jobs not closed by P0). | job ledger |
| Execution fingerprint (model digest, sampling params) | **Not in P0.** They are set at the call site (`inner_monologue_node.py`, currently modified by other work); gap closed in P1. | 6.2 |

**What the re-run says about D-0368's defeater (F-4665, F-4666):** circling is long gone, but it vanished on **09-29, ten days before
A+E**, so A+E cannot be credited. Frustration is under 15% only in the last two weeks (17.6% and 17.1% two to three weeks ago). Opener
reuse: the founder confirmed D-0368's 30% means the **4-word** metric (chat 2026-11-14), which is **met in the latest weeks (27-29%)**,
was missed in the weeks of 10-10 and 10-17 (32%, 34%), and was 22% in the first week; it has not fallen over time. The 3-word figure (45-58%) is not the threshold's metric.
Net: the vocabulary leak has mostly receded for reasons the ledger does not isolate, which weakens the case for pools and strengthens P0/P1.
which weakens the case for pools further and strengthens the case for P0/P1.

**Candidate lead, not a result (F-4667, J-3992):** the 'anchor' idiom fell from about 25% to about 6% after the 11-07 boot, which made a pooled concern-lead rewording live. If one wording change can move an idiom that much, every P3 step needs the 6.6 replay gate.

---

## 11. Founder decisions (filed 2026-11-14)

| Q | Ledger | State | Summary |
|---|---|---|---|
| Q1 sequence vs D-0368 | D-0771 | **RULED** (travis) | Run P0 now (observe-only), re-ask pools/replacement only on its result. Both auditors agree. **P0 is cleared.** |
| Q2 variant authorship | D-0769 | **RULED** (travis) | Claude drafts structural/factual wording; semantic reviewer checks; Travis authors or approves anything touching affect, attention, identity or the Travis branch. Receiving model never certifies equivalence. |
| Q3 freeze T3 | D-0772 | **RULED** (travis) | Freeze the idle wrapper (head and tail) until a replay shows a change safe and useful. Both auditors agree. |
| Q4 Table location | D-0773 | **RULED** (travis) | New `core/prompt_lines.py`, referenced from the registry. Both auditors agree. |
| Q5 Phase 4 | D-0774 | **RULED** (travis) | Record the offline LLM proposer as a separate future plan, not a commitment. Both auditors agree. |
| Q6 registry integration | D-0770 | **RULED** (travis) | Sibling script `scripts/_test_prompt_table_orphans.py` for P0/P1; wire into `prompt_registry.py check` after the P1 golden test passes. Registry-skill extension filed as skill_manager S-0325. |
| Q7 telemetry scope | not filed | proposal | Level 1 on the idle station only until overhead is measured. |

---

## 12. Files this plan expects to touch (blast radius, to be confirmed with the UDMS dossier before P1)

New: `core/prompt_lines.py`; `scripts/prompt_replay.py`; `scripts/_test_prompt_lines_golden.py`; `scripts/_test_prompt_pools_lint.py` (P3 only).
Edited (P0/P1): `nodes/inner_monologue_node.py` (wrapper + seed part wording only; the flagged hot file), `core/prompt_budget.py` (telemetry fields),
`docs/prompt_registry.jsonl` (via tool), possibly `core/condensed_thought.py` (shared tail constant, `_LIVE_TAIL`).
**Ownership (adopted from GPT):** Idle Executive decides when and why a station runs; the Prompt Manager resolves and assembles registered
wording and records provenance; Prompt Budget measures and enforces context constraints; Model Client submits the finished request; the
decoupled judge evaluates outputs. *The system that owns a cognitive operation does not automatically own the wording used to invoke it.*
The Table is the store of literal strings; `idle_executive_plan`'s renderer imports from it and keeps only dynamic assembly and ordering (Gemini).
Also new (P0/P1): `scripts/_test_prompt_table_orphans.py` (consistency between Table line_keys and registry stations; see Q6).

**Not touched:** `core/model_client.py`, any judge/grader prompt, `scripts/run_nascence.py`'s farewell pool (it stays as the reference implementation).
`inner_monologue_node.py` is already modified in the working tree by another change — P1 must be built in a throwaway worktree, not the shared tree.

---

## 13. What would make us drop or reshape this plan

- The re-run table shows leak families already under threshold after A+E → drop pools (P3) permanently; keep P0/P1.
- The replay noise floor is larger than any variant effect → rotation cannot be evaluated; drop P3.
- Telemetry shows the wrapper/steer lines are not what the thoughts echo (e.g. idiom follows seed content) → redirect effort to budget/removal (R5/R6) rather than variation.
- Founder prefers the LLM-proposer route enough to reopen P4 first → this plan's P0/P1 still stand as prerequisites (a proposer needs versioned wording and a replay harness).

---

## 14. Provenance and status trail

- 2026-11-14: raised as T-0131 (first message of session), scoped by the founder to the scripted side; neighbouring-plan
  survey by a read-only subagent (ids verified by reading ledger rows; items it flagged "not verified" are carried here as
  unverified); web research as section 5; local measurements as 3.1/3.3.
- Still unverified: whether the lanes expose logprobs (R3); the registry SEEDS check under a central renderer; the primary texts of R1-R11. (A+E live date: now verified, 10b.)
- 2026-11-14 (later): audit round 1 (Gemini, GPT; see section 10 and the review doc). Outside reviews are inputs, not rulings.
- 2026-11-14 (P0): built and measured; see 10b. Corrected the earlier claim that no pools exist (F-4664).
