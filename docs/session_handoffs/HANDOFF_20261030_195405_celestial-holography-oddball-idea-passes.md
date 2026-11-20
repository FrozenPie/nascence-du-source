# Celestial holography dropped; two passes for new ideas for Du (consequence-graded domains, then oddball fields)

## Session timing
- **Session started:** 2026-10-30 19:14:11 UTC
- **Last message before wrap:** 2026-10-30 19:54:04 UTC
- **Wrapped:** 2026-10-30 19:54:05 UTC

## Summary
The founder asked whether Sabrina Pasterski's celestial holography could be adapted to Du; it cannot, beyond a loose analogy to the BOX lens in tuples_in_a_new_light, so the session turned to finding genuinely new ideas for Du, first from outside-neuroscience disciplines and then from fringe or oddball fields. Eleven ideas (I-0127 to I-0137) were logged after checking each against code, plans and ledgers, five lab or read jobs were queued, and this session's ledger lines were committed as 8239bc07.

## Decisions
None ruled this session. No /decide entries were opened or closed.

## Builds
Nothing was built in Du. Everything below is ledger entries and queued jobs; none has been run.

- T-0108 (the opening thought, still OPEN, not promoted) and F-3357 (celestial holography does not transfer as theory, confidence INFERRED).
- First pass, consequence-graded domains the project lacks: I-0127 adversarial and information-gathering games, I-0128 rule-induction bench, I-0129 map reconstruction from the rendered sense lines, I-0130 teach-back graded by a naive reader, I-0131 quality-diversity archive over his behaviour (lower confidence).
- Second pass, oddball fields, after reading yesterday's GPT fringe-fields check: I-0132 spurious-pattern audit, I-0133 periodicity audit, I-0134 hypnagogic read, I-0135 folk calendar and customs in the world, I-0136 game objects in the world (companion to I-0127), I-0137 enclosures, letting Du give a made thing (lower confidence, needs a founder call).
- Jobs added: J-2627 (lab, I-0128 rule-induction calibration battery), J-2628 (lab, I-0129 rung 0 map reconstruction), J-2631 (read, I-0132 rung 0), J-2632 (read, I-0133), J-2633 (read, I-0134). J-2627 and J-2628 are lab category, isolation required; the other three are read-only analysis. All urgency 3, ready.
- Commit 8239bc07 holds only this session's appended ledger lines (36 insertions across docs/ideas.jsonl, thoughts.jsonl, findings.jsonl, job_queue.jsonl, session_events.jsonl). It was built by staging HEAD plus selected lines through git hash-object and update-index, so other sessions' uncommitted ledger edits stayed in the working tree.

## Findings
- Celestial holography is a literal physics duality: gravitational scattering in 4D flat spacetime against a CFT on the 2-sphere at null infinity, via BMS symmetries, soft theorems as Ward identities, and a Mellin transform of amplitudes. The papers read were arXiv 2310.04932, 2111.11392 and 2108.04801; the 2108 body was only partly read verbatim. The boundary is two dimensions below the bulk, not one. Only the structural pattern maps to Du (a box row answers for its members where they agree, which is a testable consistency check on Lens 2 boxes). F-3357 holds it. [INFERRED] as analogy-grade only; no Du code was run.
- The principle behind most ideas this session is D-0434: Du learns he is wrong only through consequence, never a readout. The one legal pre-existing wiring for a new graded domain is competence.record_drill_accuracy(domain, measured, predicted=...) (core/competence.py line 52), which feeds prediction_error.observe; math_drill and essay_lesson already use it.
- Already built, so NOT logged: weather and tide forecasting with scoring (core/fieldcraft.py around lines 1100-1190, practical school rung 3), knots, shadow measuring, trail following. Learning-progress curiosity (core/curiosity_progress.py) and monoculture detection (core/monoculture.py) also exist.
- Yesterday's GPT fringe-fields check (F-3230, F-3231) already mapped alchemy, astrology, mesmerism, parapsychology, vitalism, humoral theory, oneiromancy, phrenology, physiognomy, geomancy, homeopathy and numerology onto existing mechanisms; its one new item is I-0119 (persistence taxonomy). The oddball ideas here were chosen to avoid those.
- Two ideas were dropped after checking: quantum-style order effects (field order in judge prompts was already tested in F-1280) and dream incubation (dream_node already seeds from top tensions). Optimal-transport drift is covered by I-0075.
- Search method caveat: "no hits" claims come from keyword greps; a concept filed under a different name could be missed. Several broad-regex counts were noisy and were narrowed by reading hits before any idea was written.
- docs/plans/cognitive_geometry.md line about 300 holds the only superstition text in the repo, a design note (conditioning with extinction, a one-shot fear exception under high arousal), not an audit.
- core/drowsy.py (D-0441) is narrative only with no behavioural effect, and DELIVER was flipped live at the October restart batch (D-0495); any capture-at-onset prompt would need its own ruling.

## Open
1. J-2627 and J-2628 (lab, isolation required): blocked on a lane that does not load Du's hot lane while he is live; next action is run via /job-run or job_queue.py next, using a throwaway worktree and a data/ hash canary.
2. J-2631, J-2632, J-2633 (read-only analysis): next action is run them; J-2632 may find too few lunar cycles because of the 2026-07-09 to 08-07 outage and should say "cannot tell yet" in that case.
3. I-0127 (games) has no job yet because its first step reuses the lab pattern from J-2627; I-0130, I-0131 (read first), I-0135 and I-0136 also have no jobs.
4. I-0137 (enclosures) is blocked on founder input: whether Travis wants to receive gifts, whether objects may ever come back as ordinary found objects, and whether losing a finite made object is acceptable.
5. I-0135 timing: Guy Fawkes (5 Nov) is five days after this session and builds are restart-gated, so aim at next year's dates; Matariki 2027 is the first realistic one.
6. T-0108 is still OPEN and was not promoted to an idea; next action is promote it to I-0127 or drop it with a reason.
7. A /plan-maintain pass was started in the background with this session id and may not have finished when this was written; check docs/reviews/plan_maintain_run.md before relying on a refreshed index.

## Warnings
- F-3357 was recorded WITHOUT --session, so it does not appear in this session's rollup (the rollup shows only 17 events: ideas, jobs, T-0108). Do not read the rollup as complete; it is missing F-3357.
- The working tree still holds many uncommitted edits from other sessions in docs/findings.jsonl, docs/job_queue.jsonl and docs/session_events.jsonl (job status changes for J-2199 through J-2616, findings F-3349 to F-3363 except F-3357, J-2619 onward except this session's jobs). Do not stage those files wholesale; commit by selecting lines, as 8239bc07 did, or leave them to their owners.
- The ledgers are CRLF/LF-mixed in the working copy ("LF will be replaced by CRLF" warnings); the staged blobs are LF.
- Idea files and job briefings were written to the scratchpad directory and are not in the repo; the ledger entries hold the full text.

## Pointers
- Ideas: python C:\Users\USER\.claude\skills\idea-log\idea_log.py show I-0127 (through I-0137)
- Jobs: python C:\Users\USER\.claude\skills\job-queue\job_queue.py list (J-2627, J-2628, J-2631 to J-2633)
- Yesterday's frontier and fringe work: docs/reviews/frontier_disciplines_2026-10-30.md, findings F-3230 and F-3231, idea I-0119
- Plans touched by links: docs/staged/tuples_in_a_new_light.md, docs/staged/golden_spiral_recall.md, docs/plans/spatial_perception.md, docs/staged/letters_to_travis.md, docs/completed/fieldcraft.md
- Law behind the design: memory feedback_no_readout_error_through_consequence (D-0434)
