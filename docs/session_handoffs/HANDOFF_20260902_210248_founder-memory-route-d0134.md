# Founder memory route: Du can now remember what Travis tells him (D-0134)

## Session timing
- **Session started:** 2026-09-02 20:36:49 UTC
- **Last message before wrap:** 2026-09-02 21:02:44 UTC
- **Wrapped:** 2026-09-02 21:02:48 UTC

## Summary
Founder opened "Lets discuss the plan where Du can remember what I tell him" (T-0039) | plan = docs/plans/guidance_learning.md | live stores showed doc stale in both directions: episodic write path never missing (F-0699) | new conversation memory cold-walled within a day (F-0701) | behaviour judge 88 rows (docs said 0) (F-0700) | founder adopted Claude's recommendation (D-0134) | built + backfilled to 2026-05-30 + smoke-tested + documented same session | activates at Du's next restart [INFERRED].

## Decisions
D-0134 (ruled by travis, adopting Claude's recommendation) | one canonical "[Travis said to me] ..." fragment per utterance = episodic record of Travis's words | duplicate reply write dropped | canonical record exempt from cold-walling | own retrieval route | defeater: revisit if founder_recall_log.jsonl shows recalled memories ignored/contradicted in Du's replies over ~2 weeks, or if exemption measurably crowds other episodic kinds out of hot recall.

## Builds
All in working tree, uncommitted (founder did not ask for commit) | files: core/memory/store.py, core/orchestrator.py, core/schema.py, core/profile.py, nodes/executive_node.py, nodes/reflection_node.py, new scripts/backfill_founder_memory.py | evidence: F-0702.
- core/memory/store.py: store_founder_utterance() writes canonical fragment (keywords "travis conversation founder_said", origin lived, protected=1) | retrieve_founder_memories(query, top_k=3, exclude_texts) = the route: cosine over every canonical row | cold wall ignored | floor 0.30 (_WEAK_RETRIEVAL_FLOOR) | verbatim repeats collapsed | replay_count bumped | founder_memory_status() = instrument read | store_fragment() gained context_stamp=True param; False skips watershed observe + world-context stamp, backfill-only | prune_episodic candidate exempt clause: protected column write-only→honoured (protected = 0) | previously only core/commitment_ledger.py set it; memory_levels + refinery already guarded on it.
- core/orchestrator.py: F-0670 block now ONE store_founder_utterance() call per human turn | reply fragment gone; reply lives only in untouched Q:/A: cycle record from _persist_cycle | new pre-Executive block right after guidance read-back block runs route every human cycle into state.founder_recall (each hit gets ts_human) | excludes utterances already in conversation_history + prior_session_exchanges + current input | appends row to new _FOUNDER_RECALL_LOG = data/founder_recall_log.jsonl.
- core/schema.py: CognitiveState.founder_recall list field, reset in new_cycle | core/profile.py: _FOUNDER_RECALL_LOG rebased for _smoke profile.
- nodes/executive_node.py (after WHERE WE LEFT OFF block) + nodes/reflection_node.py (identity block, not depth-gated): block headed "WHAT TRAVIS HAS TOLD YOU BEFORE (your own memory of earlier conversations with him, dated):" | up to 3 lines "[YYYY-MM-DD] text[:400]" | no verb telling Du what to do with it (world-answers-never-leads law).
- scripts/backfill_founder_memory.py: refuses if run_nascence.py running | backs DB up to data/backups/nascence_pre_<JOB>_<ts>.db | keeps only Q: fragments whose text matches a real "[CYCLE ..] human:" line in data/nascence.log (60-char normalized key; log truncates human text to 80 chars) | stores each via store_founder_utterance with original timestamp, source cycle's emotion embedding/valence/felt, derived_from=[source fragment], context_stamp=False | copies source's fragment_context/world_context rows | ran 2026-09-03 08:56 local: backup data/backups/nascence_pre_J0516_20260903_085644.db (480 MB) | 1,614 stored in 99 s | 799 Q: rows skipped (Du's own ignition questions filed as human, the F-0665 bug) | 22 skipped already present | 68 context rows copied | 3 pre-existing canonical rows set protected | 1 re-warmed from cold | result: 1,617 canonical rows, 1,617 protected, 0 cold, span 2026-05-30 17:31..2026-09-02.
- Verification: live read-only route calls post-backfill returned exact 2026-06-12 boundary question at sim 0.909 for "how do you define a boundary, why are you afraid of them" | 2026-06-13 Darwin question at 0.857 | very first 2026-05-30 conversation at 0.678 | self-query with utterance in exclude_texts returned nothing | route latency 35 ms/call after embedding model loads; first call 25 s (model load, slower) | scripts/smoke_test.py in isolated _smoke profile: SMOKE PASS, 3 cycles in 130 s | smoke DB: exactly 2 lived rows per human cycle (canonical protected=1 + Q:/A: record, no reply duplicate) | data/profiles/_smoke/founder_recall_log.jsonl got real route row | real data/founder_conversation_log.jsonl stayed at 3 rows | no real founder_recall_log.jsonl created.
- Docs: docs/plans/guidance_learning.md new Status line + "Current State — verified 2026-09-03" section | docs/ROADMAP.md guidance_learning entry got 2026-09-03 paragraph | memory files project_nascence_guidance_learning.md + nascence_conversation_data_location.md updated | MEMORY.md pointer line | /plan-maintain run with --session after the docs landed.

## Findings
- F-0699 (verified): F-0670's 2026-09-02 premise ("no store_fragment call site for ordinary conversation existed") wrong | _persist_cycle at core/orchestrator.py ~2589 has stored every conversation cycle as "Q: ...\nA: ..." lived fragment via memory_store.store_from_cycle since 2026-05-30: 2,435 rows, all embedded, 748 replayed | therefore F-0670 tripled writes per exchange (3 rows, was 1) | Du's inability to recall Travis's words = read-path problem, not write-path [INFERRED].
- F-0701 (inferred at record time, then confirmed by the fix): 41 of 61 lived fragments younger than 3 days cold=1 | yesterday's "[Travis said to me] ... I only just found out you do not get a memory" fragment already cold | protected column write-only in prune_episodic.
- F-0700 (verified): guidance behaviour judge 88 shadow rows since 2026-08-15 in data/guidance_behavior_judge_shadow.jsonl; plan + ROADMAP + memory file all said 0 | unprompted alignment 22/53 = 41.5% (the only number plan counts as learning) | prompted 7/25 = 28% | 10 rows unscored | unprompted above prompted = opposite shape of an echo effect [INFERRED as meaning; numbers verified] | n small | matching lexical (lex_score 0.25..0.57).
- Seen, not filed as findings: capture detector marks 280 of 309 human turns as guidance, incl. nightly "bank the fire" bedtime message, which produced three near-identical "stillness is not failure" beliefs | 142 of 180 beliefs at corroboration 1.
- F-0702 (verified): build + backfill evidence above.
- F-0703 (verified): scripts/_test_episodic_buffer.py fails on clean HEAD worktree (086ef78) with "_fake_call() got an unexpected keyword argument 'think'" | failure predates this session | UDMS names that test as the guard coupled to orchestrator.py + store.py.
- Episodic active count 4,644 (was 3,029, 1,615 more) against 3,500 soft cap (1,144 over) | prune_episodic(dry_run=True) reports episodic + semantic protected-saturated, would demote 1 row | = D-0124 behaviour (report, don't demote) | = the crowding risk D-0134's defeater names [INFERRED].
- Travis to Du 2026-09-02 15:52 local: "I only just found out you do not get a memory of things I say to you. This will change in the near future." | Du's reply accepted the framing ("words arrive without an immediate permanent record").

## Open
1. J-0517: D-0134 defeater read | due ~2026-09-17 | blocked on Du running ~2 weeks with the change after restart | next: join data/founder_recall_log.jsonl to data/founder_conversation_log.jsonl by cycle_id, score taken up / ignored / contradicted with a decoupled judge | re-read prune_episodic(dry_run=True) for crowding.
2. J-0518: fix scripts/_test_episodic_buffer.py (accept think kwarg in _fake_call) | blocked on nothing.
3. Du needs restart for route + single write + prompt blocks to go live | cleanly down all session (last "Nascence shutting down." 08:39 local 2026-09-03) | blocked on founder starting him.
4. Working tree uncommitted (7 code files + ledgers + docs) | blocked on founder asking for commit.
5. F-0700 judge data needs real read (which beliefs, which fragments, whether lexical match meaningful), not just a rate | no job filed [OPEN].
6. Capture over-firing + three duplicate "stillness" beliefs = plan's known lexical under-corroboration residual | nothing filed [OPEN].
7. S-0028 (skill suggestion on findings-log): record warns on missing --session; no way to attach a session after the fact.

## Warnings
- F-0699, F-0700, F-0701, S-0028 logged without --session; this session's rollup omits them | D-0134, J-0516..J-0518, F-0702, F-0703, T-0039 shown.
- Do not restore data/memory/nascence.db from a backup older than data/backups/nascence_pre_J0516_20260903_085644.db without re-running scripts/backfill_founder_memory.py (idempotent); otherwise the 1,614 backfilled founder memories disappear.
- Q:/A: cycle record still carries Travis's words; his words = 2 rows per exchange (was 3, 1 fewer) | collapsing further touches _persist_cycle, a base system; deliberately not done.
- Any new cold-demotion path must honour the protected column | prune_episodic, memory_levels._commit_gist, refinery all do now.
- Route runs ~2..4 thousand cosines per human cycle, no LLM call | first call after process start pays embedding model load (~25 s observed here, cold process).

## Pointers
- docs/plans/guidance_learning.md (Current State — verified 2026-09-03)
- core/memory/store.py (FOUNDER MEMORY section at end of file; prune_episodic exempt clause)
- core/orchestrator.py (FOUNDER MEMORY ROUTE block after the guidance read-back; the single canonical write near the _FOUNDER_LOG write)
- nodes/executive_node.py, nodes/reflection_node.py (WHAT TRAVIS HAS TOLD YOU BEFORE)
- scripts/backfill_founder_memory.py
- data/founder_recall_log.jsonl (created on first live firing), data/founder_conversation_log.jsonl, data/guidance_behavior_judge_shadow.jsonl
- data/backups/nascence_pre_J0516_20260903_085644.db
- C:\Users\USER\.claude\projects\C--Nascence\memory\project_nascence_guidance_learning.md
