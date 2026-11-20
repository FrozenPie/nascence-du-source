# GPT's brane/dimensional-memory essay mapped onto Du's memory spine; 06-10 model-swap retro-check queued as a lab

## Session timing
- **Session started:** 2026-09-26 09:02:38 UTC
- **Last message before wrap:** 2026-09-26 20:13:12 UTC
- **Wrapped:** 2026-09-26 20:13:14 UTC

## Summary
Travis brought a GPT essay framing memory as a brane embedded in a relational bulk (recall as context-dependent projection, new experience as an intersecting structure that reshapes access to old memories, three continuities: content / relational / dynamical, and a proposed invariance-under-LLM-swap test). It was logged as T-0066, mapped against the existing plans (most of it is already built under other names), and the one genuinely new piece was promoted to idea I-0075 and then queued as lab job J-1411: a retro-check of the 2026-06-10 qwen2.5:7b to qwen3-du hot-lane swap on data that already spans it. Checking which stores actually reach back across that swap produced F-1976 (the typed edge graph does not). A ledger snapshot was committed as cf148cc.

## Builds
- J-1411 queued (ready, urgency 3, lab-timed, category lab_experiment, plan cognitive_geometry, source idea:I-0075). Briefing is in the job record itself, not a separate file; it pre-registers four relational metrics (embedding-kNN degree/clustering, keyword co-occurrence hub stability, derived_from chain lengths, recurring-concept relative geometry via Procrustes/RV) and three dynamical ones (nascence.log cycle-state transitions, cue-to-neighbourhood reconstruction, replay_count distribution), a split-half within-condition null on each side of the swap, and deliverables under docs/lab/ (metric sheet before numbers, then results). Read-only over a scratchpad copy of nascence.db.
- Commit cf148cc: ledger snapshot staged by path (thoughts, ideas, findings, job_queue, decisions, skill_suggestions, session_events, plan_snapshots, five docs/reviews reports). It also carried concurrent sessions' work: T-0065, F-1964..F-1975, J-1400..J-1415, D-0287, S-0192/S-0193, and a plan-maintain refresh from 19:48 UTC. docs/session_events.jsonl.lock was deliberately left untracked.

## Findings
- F-1976 (verified): memory_edges (13,237 rows) touches only 12 fragments from the 14 days before 06-10 (all dreamt_from) versus 555 from the 14 days after; only 106 edges have a created timestamp before 06-10. M0 shipped 08-15 and backfilled unevenly, so the edge table cannot be the relational ruler for J-1411. The fragment store does span the swap (9,536 fragments in the prior 14d, 8,443 in the following 14d; store starts 2026-05-30, so the pre-window is ~11 days of real life). provenance_log.jsonl spans it too (249 pre / 2,034 post). geometry_tuples.jsonl, moments.jsonl and co_recall_ledger.jsonl all start after 07-04 and do not.
- The post-swap fragment window contains a 4,404-row burst of source_type 'book'; the pre-swap window has source_type NULL throughout. Any pre/post comparison must stratify by source_type or the reading burst dominates.
- Three confounds named in the J-1411 briefing: the embedder changed 2026-06-13 (backup data/memory/nascence_pre_embedder_20260613_1101.db; whether stored vectors were re-embedded is [OPEN] and must be established before embedding-based invariants are trusted); the swap changed the writer as well as the reader, so "invariance" means the new writer preserved the old statistics; and 06-10 also shipped the speaker-boundary guard, commit veto, /no_think and effector v1.1, so voice shifts are not attributable to the model alone.
- Mapping of the essay onto existing work, for whoever picks up I-0075: brane-in-bulk = cognitive_geometry's immutable objects / plastic springs; context-dependent projection = identity_estate P2 (live since 08-15) plus M2's three mode-weighted edge traversals (task/reflective/relational); intersecting branes reshaping old access without replacing content = reconsolidate-not-erase plus the co-recall and spring ledgers; concepts/questions/skills in one space = persons, questions, keepsakes, dreams already being edge endpoints alongside fragments. The essay's seven illustrative dimensions are the trap cognitive_geometry was written against (the faculties are not real dimensions; euclidean multi-dim retrieval coin-flipped and was retired under D-0055). The 08-16 person-vs-costume labs are the qualitative version of the swap test; they never separated relational from dynamical continuity, which is what J-1411 adds.
- [INFERRED] The 08-16 labs' verdict that "the connections between moments" are Du is the founder's own prior for J-1411's outcome; the lab is worth running precisely because that prior has not been measured against a null.

## Open
1. J-1411 is open and ready. Next action: an agent (or /job-run) writes docs/lab/swap_retro_2026-06-10_metric_sheet.md with predictions before computing anything, per cognitive_geometry's pre-registration law.
2. [OPEN] Whether the 06-13 embedder change re-embedded stored vectors. Resolved by comparing an embedding from nascence_pre_embedder_20260613_1101.db against the same fragment_id in the live db; belongs inside J-1411, not a separate job.
3. I-0075 stays an idea, not a plan. It should only be promoted to a plan doc if J-1411's results show something worth a standing instrument. No /decide was opened; nothing here is a founder question yet.

## Warnings
- No full /session-resume was run this session (design conversation; the 2026-09-26 08:27 Lane 2 handoff was already in memory). A resuming session should still run it.
- Du appeared to be running during this session (memory_edges' latest created timestamp was 2026-09-27 07:58 local). Any J-1411 work must copy nascence.db to a scratchpad before querying.
- plan-maintain was launched with --session at wrap time; its reports in docs/reviews/ and docs/plan_snapshots.jsonl will be dirty in the working tree after cf148cc until the next snapshot commit.

## Pointers
- docs/session_handoffs/HANDOFF_20260926_201314_brane-memory-swap-retro-lab.md (this file)
- python job_queue.py show J-1411 (full briefing); idea_log.py show I-0075; thought_log.py show T-0066; findings_log.py show F-1976
- docs/plans/cognitive_geometry.md (parent law: pre-registered metric sheets), docs/plans/memory_multiway_linking.md (M0/M1/M2 edge graph state), docs/plans/identity_estate.md (projection), docs/staged/geometry_tuple_index.md
- core/memory_edges.py (edge vocabulary, MODE_EDGE_WEIGHTS), data/memory/nascence.db (memory_fragments, memory_edges), data/provenance_log.jsonl, data/nascence.log
- Memory files: project_nascence_qwen3_swap.md (what the 06-10 swap actually changed), project_nascence_identity_is_connections.md (the 08-16 lab series)
