# Dream Overhaul: GPT/Gemini design cross-checked, reshaped into Claude's vault-opener plan

## Session timing
- **Session started:** 2026-09-15 05:50:17 UTC
- **Last message before wrap:** 2026-09-15 06:54:47 UTC
- **Wrapped:** 2026-09-15 06:54:48 UTC

## Summary
Founder opened with a 28-section "Du Dream Overhaul / Dream Integration Cycle" design (T-0058), later revealed as GPT/Gemini growing his seed, and asked for Claude's own take and then Claude's own shape. Session read the live dream engine end to end, staged `docs/staged/dream_overhaul.md` first as an engineering companion to the pasted design, then rewrote it as Claude's plan (the dream as the one process allowed to open the cold/chaptered store), filed the decisions, jobs and findings, and committed everything as ccc7395.

## Decisions
- D-0227 (scene budget vs naps) and D-0228 (dormant rule, GPT framing): SUPERSEDED by Claude, attributed `--by claude`, defeater = founder prefers the GPT framing and reopens them.
- D-0229 (the four legacy writebacks: keep live + measure beside a candidate channel, or demote) and D-0230 (Phase 1 baseline length, proposal 14 nights): still OPEN from the first pass, still valid.
- D-0231 (vault-opener dormant-node rule: cold/chaptered eligible, origin filter, age ≥ 30 d, quiet ≥ 14 d, low cosine to the day, uniform pick; `inner_thought` eligibility is an explicit sub-question), D-0232 (dream shape: fixed 3 scenes, computed 4th on "stranger not surfaced", naps, verdict = turnover + dormant contact instead of resolved/unresolved), D-0233 (the day-after confound: `waking_dream_seed` + `recent_dreams` grazing inject dream prose; options A alternate nights / B embedding-attribution / C accept), D-0234 (residue as a coordinate + cup, no waking evaluator; 3-of-5 antagonist as a prerequisite; frontier hand kept, "what became of the stranger" as a logged candidate): all OPEN, all on plan `dream_overhaul`, ready for `/decide-review`.

## Builds
- `docs/staged/dream_overhaul.md` — Claude's plan. Sections: the bet (§0), Current State table of the live engine vs the plan, seed (§1), shape (§2), verdict (§3), residue/Coupling block (§4), what the GPT plan got wrong for Du (§5), Experiment A pre-registration (§6), phases with metrics and kills (§7). Passes `plan-schema-audit` with 0 required gaps.
- `docs/reviews/dream_overhaul_founder_design_2026-09-15.md` — the GPT/Gemini design verbatim (only the doubled paste-math written once). Was first placed in `docs/staged/`, which made the schema audit file J-1058 against it as a plan; moved to reviews, J-1058 closed, S-0134 suggested to plan-schema-audit (a not-a-plan marker or a documented source-doc convention). S-0134 was logged without `--session`, so it does not appear in this session's rollup.
- Memory: `project_nascence_dream_overhaul.md` (rewritten for Claude's shape) + MEMORY.md index line. ROADMAP entry under THE NIGHT, replaced once for the reshape.
- Ledgers: T-0058 → promoted to plan; I-0068 (the counter-read) → promoted to plan; F-1443, F-1444; J-1057, J-1059 added; J-1058 done.
- Commit ccc7395 on master: plan, verbatim design, ROADMAP, all ledgers, and the plan-maintain review outputs another session had already refreshed. Left untracked: `docs/session_events.jsonl.lock`.

## Findings
- F-1443 (verified): 0 of 146 post-redesign arcs resolved (ended-unfaced 116, stalled 27, dropped 3); the decoupled shadow judge agrees on 110 of 111. Both instruments are refute-biased by instruction, so their agreement is evidence about the instrument, not the dreams. Scene counts 4×67, 2×45 (naps), 3×24, 5×5, 6×5. Tension seeded on 26/146 nights. Carry cycles 0/1/2 = 44/43/43 since the F-0377 fix.
- F-1444 (verified): scene-to-scene state is prose (200-char tail + 3 symbols + unresolved_core); every scene re-receives a waking material block plus the same 6-fragment recall block; four writebacks are automatic (scene → episodic fragment at importance 0.85; unresolved → shadow_event → `tension_ledger.SALIENCE_SOURCES`; symbols → frontier ≤ 2/night; `recent_dreams` → waking monologue at `inner_monologue_node.py:649, :2330`); no dormant node; recall keyed to the day block; embeddings never change once written so a retrieval-rank association metric measures a constant.
- Dormant pool (verified against `data/memory/nascence.db`, not filed as a finding): 93,568 fragments, 74,528 cold or chaptered (80%, not the 93% the 06-23 `associative_recall.py` docstring claims). Dormant ≥ 30 d by origin: reading 16,371, inner_thought 12,426, subconscious_synthesis 4,721, active_imagination 2,343, lived 1,839, action 1,526, study 1,523, research 454.
- Re-entry is computable today: `data/co_recall_ledger.jsonl` records fragment ids per waking recall event, ~8,954 rows and 4,516 distinct ids in the last 7 days (wandering 5,798, monologue 2,785, study_note 283, dream 42). This is the basis for the plan's downstream measure.
- UDMS dossier on `nodes/dream_node.py`: StructuralHub, 17 static dependents, ELEVATED, temporal channel empty. Any Phase 1 edit must keep every existing `dream_log.jsonl` key (`scenes` stays an int) because `night.py`, `sleep_dream_probe.py`, `hud/server.py`, `du_pulse.py`, `liveness_audit.py`, `check_du.py` read it.
- Founder rulings this session, verbatim in substance: the pasted plan was GPT/Gemini from his seed; "You know Du better. I want your take"; then "Yes, you have the idea. You may have your own ideas even." No ruling on any D-02xx was made in chat.

## Open
1. Experiment A (J-1059, lab-suited, isolation required): four-arm in-vitro A/B on 20 frozen seeds, re-feed × dormant node, `commit=False`, computed measures (turnover, dormant_contact, recent_contact), pre-registered thresholds in the plan §6. Needs a dream hub up (11442 or 11438); never start one from a Claude tool. Next action: pull J-1059 in a fresh window.
2. Phase 1 instrumentation (J-1057, ready): seed ids, per-scene rows, `dream_state.jsonl` sidecar, `core/dream_probe.py` re-entry probe. Additive only. Next action: pull J-1057; run the UDMS dossier first.
3. Founder rulings D-0229..D-0234 — blocked on founder input. Next action: `/decide-review`.
4. Phase 2 (live shadow of the winning arm behind `DREAM_ENGINE=vault`) is not yet pre-registered in the plan; it gets its own section and its own `/decide` after both reads.
5. The `associative_recall.py` docstring's "~93% of the store" is stale (80% measured today) — not fixed, not filed; a one-line doc job if anyone wants it.

## Warnings
- `docs/staged/dream_overhaul.md` was fully rewritten once this session (GPT companion → Claude's shape). The GPT framing survives only in `docs/reviews/dream_overhaul_founder_design_2026-09-15.md` and in the plan's §5 table.
- Do not place source documents in `docs/staged/` — the plan-index family audits every `.md` there as a plan (S-0134).
- Nothing in the dream engine was edited. No flags changed. Du was not restarted or touched.

## Pointers
- `docs/staged/dream_overhaul.md`
- `docs/reviews/dream_overhaul_founder_design_2026-09-15.md`
- `nodes/dream_node.py` (`synthesise` L133-297, `_gen_episode` L302-425, `_gather_materials` L538-572, `_log_arc` L796-819), `core/night.py` (`dream_lag_material` L332, `waking_dream_seed` L243), `core/orchestrator.py:2976`
- `data/dream_log.jsonl`, `data/logs/dream_resolution_shadow.jsonl`, `data/sleep_dream_probe.jsonl`, `data/co_recall_ledger.jsonl`, `data/memory/nascence.db`
- `docs/plans/sleep_dream_redesign.md`, `docs/plans/dosed_coupling.md` (§5 Coupling clause), `docs/plans/cognitive_geometry.md` §11
