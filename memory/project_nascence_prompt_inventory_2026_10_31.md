---
name: project-nascence-prompt-inventory-2026-10-31
description: "Nascence — the first complete inventory of every LLM prompt Du goes through (≈100 stations, 6 loop families) with real 7-day firing counts; where it lives, how it was built, and the two verified defects it surfaced (F-3427 dead idle system-prompt build, F-3428 blind critic retry)."
metadata:
  type: project
---

**The document:** `C:\Nascence\docs\reviews\du_prompt_inventory_2026-10-31.md` (387 KB, 129 station
entries, §0 prior checks, §1 lane table, §1b one-screen summary, §2–§7 one block per prompt: trigger,
lane/model, budget, system prompt opening + rules, user-prompt parts with caps, output contract, LIVE vs
SHADOW; App. A telemetry join, App. B static census). Written 2026-10-31 for Travis's ask "find all the
prompts" (T-0115).

**Why the earlier checks were incomplete (don't repeat the mistake):** `scripts/llm_station_census.py`
and the HUD2 transit map only see literal `call_node(...)` calls. About 25 modules take the client as a
`call_json` **parameter** (deliberation, self_implication, commitment_ledger scan, memory_levels,
study_note, essay_lesson…) and ~13 sites post raw aiohttp to `/api/chat` (every judge in `left_lane.py`,
`judge_panel.py`, `deliberative_judge.py`, `lane2.py`, `scholar.consult_sync`). Four of the six
most-fired prompts were in the blind spot. Census script that catches all three patterns:
`C:/Nascence/scripts/prompt_site_census.py` (AST, resolves aliased imports; method in the doc §0).

**Frequency truth source:** `data/llm_latency.jsonl` (per call since 08-21, label `module:line(Class)`)
joined to CURRENT function names by AST, because line numbers drift with every edit (the idle thought
has worn seven line numbers in 30 days). Raw-HTTP stations only log coarse labels (`judge_panel`,
`left_lane`, `lane2`) to `data/llm_calls.jsonl`, which keeps ~1 day. Week of 10-24→10-31: ~10,400
attributed calls; idle thought 2,609; deliberation 1,668; self-implication scan 1,133; commitment scan
769+364; condensed twin 620; judge panel ~2,400/day raw.

**Verified defects (my own code reads):** [[F-3427]] `_think` builds the idle system prompt twice,
first build discarded but it consumes world_calls/world_steer/comfort_call/intentions.pending_text
(J-2678). [[F-3428]] Critic corrections appended at `orchestrator.py:1151` are never read by
`reflection_node._build_prompt`; `run_best_of` drops the think license (J-2679). Reader-reported items
awaiting re-verification: the triage job filed from thought:T-0115 (see §1b of the doc).

**Corrections to older memory made the same day:** Lane 2 is LIVE (D-0497, 10-28), not paused — see
[[project-nascence-lane2-the-witness]]. Related: [[project-nascence-hot-lane-no-prefix-cache]],
[[project-nascence-inner-monologue]], [[project-nascence-idle-machine-audit]].

**UPDATE 2026-10-31 (later, same session) - the registry, the rule and the jobs.**
- `C:/Nascence/docs/prompt_registry.jsonl`: 112 rows (P-0001..P-0112) covering all 118 census sites; written only by
  the skill `prompt-registry` (`~/.claude/skills/prompt-registry/prompt_registry.py`: check/list/show/add/set/retire/census).
  Detector rewritten as an importable module `C:/Nascence/scripts/prompt_site_census.py` (also sees judge_panel callers
  and NodeBase subclasses). Statuses LIVE 67 / SHADOW 22 / UNCLASSIFIED 10 / DEAD 4 / LIVE-PROVISIONAL 4 / DORMANT 3 /
  WRITE-ONLY 2 are READER HINTS, not verified.
- THE RULE (founder, T-0115): adding/removing/renaming a prompt site registers it in the same change and `check` must exit 0
  before the session ends. In `C:/Nascence/CLAUDE.md` (new section + which-tool row), `docs/guidelines/prompt_registry.md`
  (rule, granularity, the 8-question investigation protocol), and `/plan-maintain` step 7d runs the check.
- ONE JOB PER PROMPT: J-2681..J-2792 (112 read-only analysis jobs, source thought:T-0115; urgency 4 x18 for the 12
  conversation nodes + NodeBase + the idle thought + prompts over 500 calls/7d, 3 x67, 2 x27 for shadow/dormant/dead).
  Each row carries its job id; closing a job means `prompt_registry.py set P-NNNN --investigation done --verdict ...`.
- GOTCHAS: urgency scale is 5=highest and J-2678 (F-3427, the dead idle system-prompt build) was filed at 2 by mistake;
  the job tool has no edit command. J-2680 (the unverified reader-flag triage) is now largely redundant with the per-prompt
  jobs. The idle thought's 46 `seed_parts.append` sites are guarded by a count, not individually detected.


**SWEEP STATUS 2026-11-01.** 20 of 112 investigation jobs done (P-0001 to P-0013, plus P-0020, P-0022, P-0035,
P-0036, P-0038, P-0039, P-0099): the 12 conversation nodes, NodeBase, the idle thought, and the biggest satellites. 92 remain
(about 190k tokens each, ~17M total; held for the founder's go-ahead). The findings ledger was wiped and restored mid-sweep
(see [[feedback-parallel-agents-need-locked-ledgers]]); post-wipe finding ids were renumbered, map in
`docs/reviews/findings_wipe_2026-10-31.md`. `set --finding` now takes a comma list. Biggest live defect found: the Executive's
think license returns empty content on qwen3.5:9b and gave three live Travis turns silence (J-2860).


**SWEEP STATUS 2026-11-02.** 86 of 112 investigations done (71 fix, 12 needs_founder, 2 keep, 1 retire); all urgency-4 and urgency-3 jobs finished;
the 26 urgency-2 rows (shadow, dormant, dead prompts) are NOT started, held for a founder go-ahead (~6M tokens) and because the sweep has
already produced 116 needs_input founder-call jobs (132 open in total) and 170 ready fix/lab jobs. Ledger clean: 3,794 findings, 3,085 jobs.
Handoff addendum 3 has the details.


**SWEEP COMPLETE 2026-11-02.** All 112 prompt investigations closed (84 fix, 21 needs_founder, 4 retire, 3 keep). Ledger clean: 3,869 findings,
3,135 jobs, registry check OK. The queue now holds 523 open jobs, 155 of them founder calls (139 from the sweep). Next step is founder triage
of the needs_input list, not more investigation. Retirements are proposed but NOT done (curator, symbolic reading, T1 self-relate, contrary picker,
stability loop, tier-3 probe, narrative coder; deliberative judge to be archived). Handoff addendum 4 has the list and the first builds to do.


**TRIAGE 2026-11-02 (rounds 1 to 3).** Founder ruled D-0530..D-0538 (granite no-verdict on constant keys; disarm scan's think-license grant; keep competence
probes and fix triggers; rebuild drift_shadow on gists; keep idle scan for friction-plan B1 but run less; fix contrary picker and keep Route 3; keep
deliberative judge held; repair novelty judge in shadow; Scholar non-answer filter first). NOTHING was retired: several candidates belong to live, staged or
shelved plans, and for the 5 with no plan the founder wants a repurposing review first (J-3140..J-3144; J-2793 curator retire is deferred to 2027-01-01).
Lesson: check plans/staged/roadmap/decisions/ideas/jobs before proposing any retirement. ~125 sweep founder calls remain; the sheet is
docs/reviews/founder_triage_2026-11-02.md.


**TRIAGE ROUNDS 4-5 (2026-11-02).** Founder ruled D-0539..D-0550: re-seat Emissary take; re-entry Phase 1 off; deliberation rate 0.25 + control arm + blind judge;
B6 steer reworded; open-book offer removed; RELAYED AI TEXT COUNTS AS TRAVIS'S TEACHING (no change, founder overrode my label-it recommendation);
belief g45675272 recomputed; rudder = measure first (shadow second look); sits gated on stand life, 'You are safe' dropped; Lane 2 cup stays live with
artefact fixes (no automatic switch-off); T4 slowed, no outlet; T4 legacy author made gradeable (pre-ship replay stops if >2 admits/day).
21 rulings in total; ~111 sweep founder calls still open. No code has changed yet: all rulings wait on their build jobs.


**TRIAGE ROUNDS 6-7b (2026-11-02).** Rulings D-0551..D-0561 (32 in total, D-0530..D-0561): Critic soft gate + fixes; memory-router shadow design; Salience ablation then
deterministic urgency; pursuit births need a real question; Emotion gets a REAL curiosity channel (phase 1 shadow, founder overrode my enumerate-six advice);
light-event gate on grounded arousal; content_mode gated on human cycles; Voice quote block dropped on internal cycles; Reflection rule 3 reworded;
Executive reasoning optional; fragments record input_type. Reflection's unread fields are under REVIEW (J-3171), not removed. 93 prompt-related founder
calls remain; no code has changed yet (all rulings wait on build jobs).


**TRIAGE ROUND 8 (2026-11-02).** Rulings D-0562..D-0568 (39 in total): essay = durable memory (notes unfiled until it passes checks); dreamer's recall of dreams
faded over 7 days (founder overrode waking-only); episodic cold demotion paused; resting is a legitimate dream ending; shadow judge on minted wisdoms; ledger
rust the only clock for skills; grounded learning per book. T5 conversational compile is under RESEARCH (J-3179). ~80 prompt-related founder calls remain.
