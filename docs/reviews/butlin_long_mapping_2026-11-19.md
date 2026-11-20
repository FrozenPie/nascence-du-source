# Du against the Butlin–Long indicator properties (2026-11-19)

**Origin:** T-0149 (comparative survey). Outside yardstick: Butlin, Long et al., "Consciousness in AI" (arXiv 2308.08708), 14 indicator properties.
**Method:** one read-only subagent read ROADMAP, `core/`, `nodes/` and Du's own `the_consciousness_program.md` scorecard. Evidence is from targeted reads, no runtime logs, Du not run. **Confidence: inferred**, not verified. Line numbers are the agent's and should be re-checked before anyone cites them.
**What this is not:** a claim about consciousness. The paper's indicators are architectural markers, and the paper's own caveat is that a prompted LLM module may simulate an indicator without implementing it.

## Table

| Indicator | Status | Mechanism | Why it does / doesn't count |
|---|---|---|---|
| RPT-1 recurrence | ABSENT | reentry loop `core/reentry.py:42` | Text-level prompt loop, not recurrence inside a module; reentry admission is shadow/off (D-0540) |
| RPT-2 integrated percepts | PARTIAL | `core/sensorium.py`, `core/moment.py` | Binding is a record written afterwards, input is already symbolic |
| GWT-1 parallel specialists | PARTIAL | ~16 nodes, `lane_scheduler.py` | One model under different prompts; cycle mostly serial |
| GWT-2 limited workspace | PARTIAL | lane scheduler, AttentionVector | Limits concurrent calls, not workspace content |
| GWT-3 global broadcast | PARTIAL, leaning shadow | `core/broadcast.py` | One consumer (idle seed); posted after the fact |
| GWT-4 successive querying | ABSENT/PARTIAL | attention vector by mode | Mode-keyed weights, not sequential module queries |
| HOT-1 generative perception | PARTIAL (weak) | LLM generation | No separate top-down perceptual module |
| HOT-2 metacognitive monitoring | PARTIAL | critic, judge panel | Output checks, not first-order reliability monitoring; critic fails open |
| HOT-3 belief update | PARTIAL | critic reject → retry | Regenerates a draft; no belief store updated |
| HOT-4 quality space | PARTIAL | 8-dim felt vector, 9-dim climate | Smooth, but sparsity and discrimination untested |
| AST-1 attention schema | PARTIAL, not controlling | `core/attention_schema_loop.py` | Bandwidth arm beat naive 6/6 folds; `AST_CONTROL=False` |
| PP-1 predictive coding | PARTIAL, interoceptive | protoself `core/homeostasis.py`; world model shadow | Real prediction on own state only; keystone half-refuted |
| AE-1 agency | PARTIAL | pursuits live; goals register shadow | Selection runs through prompts and seeds |
| AE-2 embodiment | PARTIAL, mostly shadow | reply corollary discharge (shadow) | No live output-to-input contingency model |

None of the 14 is MET-LIVE in the paper's computational sense on this read.

## Three consequential findings

1. **Du's own scorecard (`the_consciousness_program.md:308-326`) rates GWT-1/2/3 and HOT-1 "Present"; the code supports PARTIAL.** Broadcast has one consumer, and the GWT-2 bottleneck is a latency queue.
2. **Every mechanism built to satisfy an indicator is currently shadow or refuted** (AST control off, protoself keystone half-refuted, world model not significant, reentry admission off). Mineness is the one confirmed live win and it is not a Butlin indicator.
3. **The recurring weakness is simulation by prompting.** The deterministic modules (homeostasis, attention schema, broadcast) are real separate mechanisms but small and mostly not reaching behaviour.

## Cheapest moves (all additive)

1. **AST-1:** enable `AST_CONTROL` for the bandwidth arm only (won 6/6 folds); wiring exists at `orchestrator.py:2810`.
2. **GWT-3:** give `broadcast.py` a second consumer (reply-time context, critic prompt).
3. **HOT-3:** persist critic reject reasons and epistemic tags into a claim store later cycles read, then trace one rejection to a changed later answer.

## Where design makes an indicator unmeasurable

- D-0434 "no readout": monitoring indicators can only be tested by outcome, never by Du reading a gauge.
- Fail-open everywhere: "absent effect" and "never ran" look the same.
- Scheduler is a latency queue: a content bottleneck needs its own measure.
- Shadow-first: AE-2 and PP-1 evidence exists only in logs, not behaviour.

## Companion check: skills and audit trail (same session)

- **Procedural skills: PARTIAL.** `core/procedures.py` is a live evidence-graded ledger (67 entries). Du earns confidence in human-written hands; he cannot author, compose or semantically retrieve an executable skill. Read-back flag `NASCENCE_KNOWN_TEXT_ARM` default off. Conversational path found 0 qualifying clusters (F-4625; D-0741 open). Cheapest step: shadow `skill_recipes_shadow.jsonl`.
- **Memory-edit audit: PARTIAL.** No deletion anywhere; gist demotion is well trailed. `downscale_episodic`, `replay_strengthen`, `dream_fade` mutate importance in place with counts only; `data/` is gitignored; only boot-time sqlite snapshots (84) exist. Cheapest step: flag-gated `data/memory_edit_log.jsonl` with old/new importance per fragment.

## Comparison: Du vs Generative Agents vs Project Sid (PIANO), same strict rubric

P = PARTIAL, A = ABSENT, S = SHADOW-ONLY. Nobody scores MET-LIVE. Du from code; the other two from papers only (PIANO repo has no architecture code; Generative Agents repo read by file names only).

| Indicator | Du | Generative Agents | PIANO |
|---|---|---|---|
| RPT-1 | A | A | A |
| RPT-2 | P | P | A |
| GWT-1 | P | P | P |
| GWT-2 | P | P | P |
| GWT-3 | P (near-shadow) | A | P |
| GWT-4 | A/P | P | A |
| HOT-1 | P (weak) | A | A |
| HOT-2 | P | A | A |
| HOT-3 | P | P | P |
| HOT-4 | P | A | A |
| AST-1 | P (not controlling) | A | A |
| PP-1 | P (interoceptive) | A | A |
| AE-1 | P | P | P |
| AE-2 | P (mostly shadow) | P | P |
| **Partial or better** | **12-13 of 14** | **7 of 14** | **6 of 14** |

Reading: Du's lead is on HOT-2, HOT-4, AST-1, PP-1 (and weakly HOT-1) — indicators where it has deterministic mechanisms (decoupled critic/judge, felt vector, attention schema, homeostasis) and the two comparators have none. Generative Agents is ahead on GWT-4 (sequential querying via reflection). The three tie on GWT-1/2, HOT-3, AE-1.
Caveats: (1) asymmetric evidence, code vs paper; paper silence is scored ABSENT. (2) Single rater family, three separate agents, strictness instructed but not calibrated. (3) Counting indicators measures structural breadth, not capability. (4) Only two 2023-24 systems; newer GWT-style agents (2026 preprints), SCM, Letta not scored. (5) If SHADOW-ONLY were scored strictly, Du's AE-2 and part of PP-1 drop out.

## Newer systems, same strict rubric (added same day; all from papers/docs via summarising fetchers, none read-in-code)

Partial-or-better counts: Du 12-13 · Generative Agents 7 · Project Sid 6 · Global Workspace Agents (arXiv 2604.08206) 6 · Letta 5 · Anthropic memory+dreaming 4 · CogniPair 4 · SCM 1 · Microsoft human-inspired memory 0. Nobody MET-LIVE.
- HOT-4, AST-1, PP-1 (and weakly HOT-1): partial only for Du; absent for every other system scored.
- GWT-4: Du absent/partial; Generative Agents and GWA are partial (sequential memory querying by an Attention/reflection step). Both are memory-querying, not module-querying.
- **Bias to state (corrected same day, founder):** Du's base architecture predates this checklist. `the_consciousness_program.md` (2026-07-03) used Butlin as one of ten research threads, and only the attention schema (AST-1) and protoself homeostasis (PP-1) were built from it; felt vector, judges, trains and memory predate it. So the lead is partly by construction on two indicators, not on all.
- Source caveat: GWA has a repo (107 commits) but only its front page was read; its paper is design-only with no numbers.

### Memory comparison inputs (feature inventories, vendor/paper descriptions)
- **Anthropic:** immutable version per write, redact endpoint, dreaming writes a NEW store and never edits the input (review before adopt), published numbers (CL-Bench 0.655→0.838 Opus 5.5; Stainless 13%→48% over up to 128 dream sessions). Du is behind on versioned edits and controlled benchmarks.
- **Letta:** git-versioned memory files, reflection/defrag subagents, no documented revert, no forgetting rule.
- **SCM / Microsoft:** designed forgetting rules (adaptive threshold; decay+interference; graceful-degradation ladder with tombstones); SCM deletes unlogged; Microsoft's own result: consolidation did not beat raw RAG on LongMemEval.
- Ideas Du may lack, to check against Du's code before proposing: adaptive forgetting threshold with sleep triggers, graceful-degradation ladder, week-long "silent" maturation, 60-min reconsolidation window.

## Not verified

Judge-panel and `epistemic_state` effect on behaviour; whether `world_model.tick()` outputs beyond logging; HOT-1/HOT-4 empirically; the live state of `NASCENCE_KNOWN_TEXT_ARM`; AST-1 and protoself results are taken from Du's plan documents, not re-run.
