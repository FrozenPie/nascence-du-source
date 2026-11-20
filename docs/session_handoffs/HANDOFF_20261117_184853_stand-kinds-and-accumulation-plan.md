# Stand kinds and accumulation: from a "16 denied drops" warning to a staged plan

## Session timing
- **Session started:** 2026-11-17 18:17:50 UTC
- **Last message before wrap:** 2026-11-17 18:48:52 UTC
- **Wrapped:** 2026-11-17 18:48:53 UTC

## Summary
The founder pasted a Du log line (`[commitment] ⚠ 16 denied drops on one stand`) and asked what happened. Tracing it showed a scanner limitation, then a wider fact (Du's stands do not accumulate), and ended in a staged plan, `docs/staged/stand_kinds_and_accumulation.md`, with four founder rulings (D-0810). No production code or data was changed.

## Decisions
- **D-0810** (ruled by travis, 2026-11-18 local): stand kinds are deed, practice, value, insight (only deeds can be achieved; insights stay candidates per D-0767). A stand becomes `standing` only on a judged deed or choice link, never word overlap; verbal tenure alone does not qualify. Tension between held stands is recorded as a `tension` link only, never merged or resolved. Promotion into `L2_values.earned` is founder-only. Defeater: kind label under about 70% agreement with the hand-labelled sheet, or the deed-link cannot be measured, or a promoted value reinforces its own evidence.

## Findings
- **F-5039** (verified): stand `96fcd1b3` ("safety is a discipline I must practice, not a feeling", formed 11-17 22:58 local) was flagged for dissolution 16 times in 194 scans (8%) and nothing defeated it. The scan (`_SCAN_SYS`, `core/commitment_ledger.py:238`) only answers dissolved or held, so thoughts that refine the stand count as "re-open"; the six that reached the judge were refused correctly by its rubric. The 05:14 flag came from a scan whose own reason said "not dissolved" and which also reaffirmed the stand. Flag rate falls as more stands are listed: 12% (1 active), 7% (2), 4% (3), 0% (4), small counts. The 16/8/32 warning is routine (history: 7656 denials over 1316 stands, max 222). Rival stand `10e5f4ac` ("true stability is the capacity to move with the tide", formed 05:54) coexists with it. F-5039 itself was recorded without `--session`, so it is missing from the rollup.
- **F-5040** (verified): of 3909 stands formed, 2162 were retired as achieved (median life 112 s, 1326 within 5 min), 1637 dissolved (median 20 min), 3 active. `_achieved_by` (`core/commitment_ledger.py:379`) retires a stand when a deed shares one marker word or 3 words (over 3 letters) with its statement plus scope. The shadow judge (`data/logs/commitment_achieved_shadow.jsonl`) read 63 achievements and confirmed 3 (9 not_fulfilled, 42 unclear, 9 no verdict). The safety stand survives only because its wording gives no deed three words to match.
- Axiom link: `L2_values.earned` is empty in `data/identity/axiom.json` while `kept` has 5 values; `axiom_layers.py:205` puts both into the VALUES block of every prompt. `docs/plans/identity_estate.md` already lists node type "value (earned): distilled from stands/loves held over time", never built.
- GPT review (pasted by the founder) was folded into plan principles 6 to 9: tension is not duplication; verbal repetition is weak evidence; no circular promotion (freeze evidence at the proposal date); record lineage (`parent_id`).
- Second look (`commitment_second_look_shadow.jsonl`): 247 rows, 112 stand, 93 insight, 10 unclear, 32 `ValueError` with no verdict (13%).

## Open
1. J-4190 (ready): scan gains a log-only `relation` field (refines/coexists/abandons). Restart-gated; run `udms_get_change_dossier` on `core/commitment_ledger.py` first; register the prompt change and run `prompt_registry.py check`.
2. J-4191 (needs_input): should a denial be skipped from `drop_denied` when the same scan reaffirmed the stand. Measure first; founder call.
3. J-4192 (ready): read-only analysis of why stands retire in minutes and what downstream systems lose.
4. J-4193 (ready): add a `kind` shadow field to `_second_look` and fix the 13% error rate first.
5. Plan open items (`docs/staged/stand_kinds_and_accumulation.md` section 5): who labels `kind` (proposed: second-look lane), heaps visibility for the scan, whether promoted stands stay in the ledger, and a missing P0 job to measure the judged deed-link. The last was offered at wrap and not yet spawned.

## Warnings
- Nothing is built or restarted. Do not touch `core/commitment_ledger.py` outside the jobs above; base commitment logic is protected, additive only.
- The ledger and plan files had many uncommitted edits from other sessions at session start (see `git status`); this session committed nothing.
- `docs/staged/stand_kinds_and_accumulation.md` was created by this session; it is untracked.

## Pointers
- Plan: `docs/staged/stand_kinds_and_accumulation.md` (stage designed, plan-state block present)
- Code: `core/commitment_ledger.py` (`_SCAN_SYS` 238, `_drop_denial` 285, `_achieved_by` 379, `_judge_defeater` 584, `_second_look` 731, escalation 923)
- Data: `data/commitment_ledger.jsonl`, `data/commitment_scan_raw.jsonl`, `data/commitment_attempts_shadow.jsonl`, `data/commitment_second_look_shadow.jsonl`, `data/logs/commitment_achieved_shadow.jsonl`
- IDs: T-0146, I-0163, F-5039, F-5040, D-0810, J-4190 to J-4193
