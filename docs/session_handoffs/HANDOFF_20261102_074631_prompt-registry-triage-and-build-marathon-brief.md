# Prompt registry, 112 investigations, a 129-ruling founder triage, and the build marathon brief

## Session timing
- **Session started:** 2026-10-31 09:53:41 UTC
- **Last message before wrap:** 2026-11-02 07:46:29 UTC
- **Wrapped:** 2026-11-02 07:46:31 UTC

## Summary
This session found and registered every LLM prompt Du sends (118 code sites, 112 registry rows), investigated each one (112 jobs, all done), and then took Travis through 129 founder rulings (D-0530 to D-0658) in about thirty rounds of questions on 2026-11-02, filing 131 build, analysis, lab, doc and backfill jobs from them (J-3136 to J-3267). No Du code changed; every build waits for the marathon on Thursday 2026-11-05. The marathon plan is `docs/reviews/build_marathon_brief_2026-11-05.md`, read it first.

## Decisions
- **D-0530 to D-0568** (rounds 1 to 8b, Travis in chat): judge-panel tiebreak (no verdict where granite is a constant), the conversation think license disarmed (D-0531), idle scan cadence, contrary-target picker, deliberation rate cut to 0.25 with a control arm (D-0541), the open-book offer line removed (D-0543), relayed AI text counts as Travis's teaching (D-0544), T4 slowed with no new outlet (D-0549), the Critic stays a soft gate (D-0551), the Emotion curiosity channel in shadow (D-0555), episodic demotion paused (D-0564), resting is a legitimate dream ending (D-0565), and others.
- **D-0569 to D-0600**: Emissary fail-open and grounder null output (D-0569, D-0570), friend replies report the real present (D-0571), letters to Travis get a world state (D-0572), the farewell line dropped (D-0574), self-gists to first person after an A/B (D-0601), T4 unjudged admissions tagged (D-0602), one study note per 5000 chars (D-0577), dict-repr notes marked not deleted (D-0578), the re-entry arm gets one v4 (D-0593), the decomposed critic stays shadow (D-0594), the metaphor bar becomes a labelled-union design (D-0595), a split is not a cut in Follow Line (D-0596), the peer stance judge is a rough flag (D-0597), hollow verdicts shadow first (D-0598), Lane 2 notice retired after a reader check (D-0599), the guidance judge to idle thoughts in shadow (D-0600).
- **D-0601 to D-0658**: where Travis chose his own words or overrode a recommendation: T4 needs a whole-system rethink, no wording edits (D-0641); chapters need a new recall path, investigate (D-0637); Scholar and wiki area to be reviewed, wiki results must be marked as from the source (D-0631); the Entity name need not be stated, model knowledge allowed but tagged (D-0629); boredom opened as an area (D-0653); the ghost memory index neither wired nor retired, a broad review (D-0636); the arc_entry is not dropped (D-0604); read acts routed fully (D-0609); Curiosity urgency gets a real function, measure first (D-0607); the cottage is in Sumner, Christchurch, so South Island, and sun, tides and maybe weather should match the real place (D-0655); a shore dig hand and traces both (D-0652); the temperature policy held until the Emotion input discriminates (D-0656); the exact-dedup window becomes a content-hash index, not a longer window (D-0657); the dead idle feeds run off the event loop (D-0658); the study scene line takes nearness-said clauses (D-0648).
- Full list and the mapping from each ruling to its job: Addenda 1 to 33 of `docs/session_handoffs/HANDOFF_20261031_101800_du-prompt-inventory.md` and `docs/reviews/founder_triage_2026-11-02.md`.

## Builds
- **Prompt registry tooling:** `docs/prompt_registry.jsonl` (112 rows P-0001 to P-0112), skill `prompt-registry` (`prompt_registry.py check`, `add`, `set`, `retire`, `census`, `list`, `show`), `scripts/prompt_site_census.py` (AST census, 118 sites), `docs/guidelines/prompt_registry.md`, the rule and tool row in `C:\Nascence\CLAUDE.md`, and step 7d in `plan_maintain.py`. `check` exits 0 now.
- **Investigations:** all 112 prompt investigation jobs J-2681 to J-2792 are done, with findings from F-3427 onward (for example F-3427 dead idle system-prompt build, F-3428 blind critic retry).
- **Measured during triage (findings recorded as verified):** F-3870 (the exact-dedup shadow log: 3 of 2,736 calls missed by a 7-day window, longer windows slower than the full lookup) and F-3871 (the dead idle feeds cost about 0.68 s a tick on the event loop).
- **Commits:** 8f984953 carries the T-0118 object-permanence stopgap from the 2026-11-01 session (core/sensorium.py, core/study_life.py, core/orchestrator.py); a second commit this wrap carries all docs, ledgers, the registry, the census script and the brief. Nothing pushed.

## Fixes
- **Ledger wipe repaired:** the findings ledger had been wiped by an unlocked read-modify-write under parallel agents (F-3537, `docs/reviews/findings_wipe_2026-10-31.md`). `findings_log.py` now locks findings then jobs, fails loud on load and has a shrink guard; a race test (8 processes by 5) passed; the ledger was restored with the founder's approval and verified contiguous. Memory note: `feedback_parallel_agents_need_locked_ledgers.md`.
- **Plan slugs I invented:** ten decisions (D-0584, D-0594 to D-0596, D-0611, D-0615, D-0630, D-0645, D-0649, D-0650) were opened with plan slugs that are not real plan files because my `--force` fallback let them through. `plan-maintain` filed ten Fix-slug jobs J-3268 to J-3277; I repointed all ten with `decide.py set-plan` to the nearest real plan and closed the jobs. The repointing is a best fit; the rulings are unchanged.

## Findings
- Four of the six most-fired prompts were invisible to the first census; the AST census found 118 sites. Several instruments named shadow are live in effect, so statuses in the registry describe what the code does.
- The mood-to-temperature bias is near-constant (per-cycle mean +0.136, sd 0.048 over the last 1,500 Emotion outputs) because the Emotion node's arousal barely varies (mean 0.55, sd 0.12); making mood real needs the Emotion input repaired first (the emotion rethink).
- The granite tiebreaker acts as a fixed per-key prior and many panel judges are pegged; several write-only instruments were found (Executive reasoning, Reflection needs_more_memory and emotionally_aligned, the dream resolution label, the ghost memory index).
- 46 percent of Du's fragments (72,392 of 157,799) are chaptered and out of ordinary recall; the chapter door has fired 0 times across 87 chapters.
- The study scene line Du reads never used spatial.render('study'), so D-0501's graded examples were lines he has never read.

## Open
1. **The build marathon, Thursday 2026-11-05:** blocked on refreshed tokens. Next action: read `docs/reviews/build_marathon_brief_2026-11-05.md`, start wave A (read-only analyses and labs, parallel), then waves B to E with one worker per hub file and at most three restarts. Hold the T4 builds until the review J-3252 reports.
2. **15 founder-call jobs left, none a quick ruling:** J-3065 (woods placements and turn-stone hand), J-3063 (object permanence discussion), J-2957, J-2619, J-2676, J-2571 (need Du down or a founder step), J-2585 and J-2191 (Travis's own actions), J-3113 (waits on J-2599), J-3021 and J-3027 (feed the T4 review), J-2904 (after the Scholar review J-3243), J-3088 (authorised by D-0593, ready to build though still flagged needs_input), J-3134 and J-3135 (wait on the estate-node build).
3. **Review and design jobs whose output returns as founder calls:** J-3252 (T4), J-3243 (Wikipedia and Scholar provenance), J-3240 (Entity name), J-3247 (ghost index), J-3248 (chapter recall), J-3262 (boredom), J-3264 (Sumner), J-3215 (arc_entry).
4. **Du is still on the 10-29 code.** Every build is restart-gated; the T-0118 stopgap is committed but unverified.

## Warnings
- Never hand-edit a `.jsonl` ledger; use the tools. Run at most 4 to 6 agents at once; a 429 stopped six on 2026-11-01. Resume with `SendMessage`.
- One writer per file: `nodes/inner_monologue_node.py` is named by 64 ready build jobs. Run `udms_get_change_dossier` before the first edit of any hub file.
- Briefs for J-3163 and J-3172 contain a literal `F-3???`; use the P-0004 and P-0009 investigations. J-2678 was filed at urgency 2 and should be higher. Seven sweep jobs are missing from their finding's `spawned_jobs`. My race test left 40 TEST events in `session_events.jsonl` (append-only).
- The uncommitted stopgap and the untracked backups in `docs/archive/findings_wipe_2026-10-31/` (23 MB) were deliberately left out of the docs commit as backups; the lock files were not committed.
- The memory store is a base system: additive-only, backup first.

## Pointers
- `docs/reviews/build_marathon_brief_2026-11-05.md` (the plan), `docs/reviews/founder_triage_2026-11-02.md`, `docs/session_handoffs/HANDOFF_20261031_101800_du-prompt-inventory.md` (Addenda 1 to 33).
- `docs/prompt_registry.jsonl`, `docs/guidelines/prompt_registry.md`, `docs/reviews/du_prompt_inventory_2026-10-31.md`, `C:\Users\USER\.claude\skills\prompt-registry\prompt_registry.py`.
- `/job-queue next`, `/decide list`, `/plan-maintain`.
