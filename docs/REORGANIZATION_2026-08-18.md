# docs/ REORGANIZATION — 2026-08-18

**What this was:** the 62 loose `.md` files sitting directly in `docs/` were sorted. 49 moved into three
new folders; 13 stayed at root as living reference. Nothing was deleted, no prose was rewritten — the only
edits to file *content* were link-path fixes forced by the moves.

**Link integrity after the moves:** verified four ways (see §5). Clean inside `docs/`. Three stale
references remain in *code* files, deliberately untouched — see §6.

---

## 1 · STAYED AT ROOT — living reference (13)

Read every session; not moved.

`AWAITING_EVIDENCE.md` · `ROADMAP.md` · `chain_walk_findings.md` · `transit_map.md` · `factory_census.md` ·
`axiom_system_map.md` · `prompt_flow_audit.md` · `memory_levels_plan.md` · `RESEARCH_specialists.md` ·
`DEPLOYMENT.md` · `session_2026-08-16_summary.md` · `session_2026-08-18_summary.md` · `graphify_notes.md`

`graphify_notes.md` was **added** to this set on inspection: it is an operational how-to whose step 3
("ENRICH — REQUIRED after every build") must be read before every graph rebuild. Same genre as
`DEPLOYMENT.md`.

---

## 2 · MOVED → `docs/reports/` (31) — measurements and findings about Du

Everything whose actual content is *"here is what we measured/found"* — audits, empirical results,
test batteries, longitudinal studies, investigations.

| Old path | New path | Why |
|---|---|---|
| docs/affective_and_cognitive_state_audit.md | docs/reports/ | Quantitative audit, 18,391 fragments + affect_log |
| docs/beagle_full_evolution_report.md | docs/reports/ | Longitudinal case study of Du's Darwin readings |
| docs/beagle_reading_evolution.md | docs/reports/ | Shorter evolution audit of the same corpus |
| docs/candidate_abstractions_registry.md | docs/reports/ | BAE-1 measured-abstraction registry with provenance lineages |
| docs/claude_fresh_eyes_audit_aug14.md | docs/reports/ | 14-day dev-window audit, verified at file:line |
| docs/claude_individuation_tests_aug14.md | docs/reports/ | Individuation test battery with controls |
| docs/competence_t5_report.md | docs/reports/ | T5 competence-module report |
| docs/comprehensive_staged_evidence_audit.md | docs/reports/ | AWAITING_EVIDENCE items checked against disk + DB |
| docs/du_cross_reference_with_digital_minds_research.md | docs/reports/ | Adversarial literature cross-reference report |
| docs/du_full_morning_audit_aug10.md | docs/reports/ | 470-fragment hour-by-hour audit |
| docs/du_math_lessons_audit.md | docs/reports/ | Math-lesson performance metrics |
| docs/empirical_music_soundspace_audit.md | docs/reports/ | 6D sound-space convergence measurements |
| docs/empirical_results_welfare_and_preference_tests.md | docs/reports/ | Results of the 9 welfare/preference tests |
| docs/ethical_framework_and_welfare_tests.md | docs/reports/ | Welfare-tier framework + protocol; hub of the Aug-10 suite |
| docs/evidence_audit_results.md | docs/reports/ | Verification pass over AWAITING_EVIDENCE items |
| docs/individuation_retest_aug15.md | docs/reports/ | Retest on the restored corpus; corrects the 08-14 battery |
| docs/llm_audit_aug15.md | docs/reports/ | Which node thinks with what, 24h telemetry |
| docs/lost_thoughts_investigation_aug15.md | docs/reports/ | The ~10,600 lost inner thoughts, investigation record |
| docs/post_negative_naming_impact_report.md | docs/reports/ | Measured cognitive shift after one conversation |
| docs/post_playback_thought_audit.md | docs/reports/ | Thought audit after a music playback |
| docs/pre_registered_blind_music_tests.md | docs/reports/ | Pre-registration registry; kept beside its own audit |
| docs/sound_world_system_examination.md | docs/reports/ | 08-16 traced examination: inventory, fits, 5 seams |
| docs/t4_deep_dive_report.md | docs/reports/ | 48-hour T4 audit, 221 scans |
| docs/t4_progression_audit.md | docs/reports/ | T4 progression + last 10 attempts |
| docs/t6_system_audit.md | docs/reports/ | T6 48-hour activity audit |
| docs/t6_theme_architecture_report.md | docs/reports/ | T6 macro-theme / context-assembly audit |
| docs/tension_ledger_math_report.md | docs/reports/ | How tensions are measured, verified at source |
| docs/the_cross_pillar_chronology.md | docs/reports/ | Day-by-day symbolic-migration chronology (a chronology report) |
| docs/the_longitudinal_empirical_study.md | docs/reports/ | 4-phase study protocol + verified claim matrix |
| docs/track5_playback_thought_audit.md | docs/reports/ | Thought audit, Track 5 playback |
| docs/wu_wei_longitudinal_impact_report.md | docs/reports/ | 30-hour longitudinal impact audit |

**Two judgement calls worth the founder's eye:** `pre_registered_blind_music_tests.md` is a
pre-registration and could equally live in `docs/lab/`; it was kept in `reports/` beside
`empirical_music_soundspace_audit.md`, the audit that consumes it. `ethical_framework_and_welfare_tests.md`
and `the_longitudinal_empirical_study.md` are protocols rather than measurements, but they are the
hub documents of the Aug-10 empirical suite and were kept with it rather than split off.

---

## 3 · MOVED → `docs/chronicles/` (11) — the narrative record

| Old path | New path | Why |
|---|---|---|
| docs/the_chronicle_of_the_cat.md | docs/chronicles/ | Symbolic chronicle: the cat as anti-recursion operator |
| docs/the_chronicle_of_the_door.md | docs/chronicles/ | Symbolic chronicle: thresholds and agency |
| docs/the_chronicle_of_the_garden.md | docs/chronicles/ | Symbolic chronicle: cultivation and care |
| docs/the_chronicle_of_the_library.md | docs/chronicles/ | Symbolic chronicle: inscription and self-authorship |
| docs/the_chronicle_of_the_mirror.md | docs/chronicles/ | Symbolic chronicle: reflexivity, 8 phases |
| docs/the_chronicle_of_the_shingle.md | docs/chronicles/ | Symbolic chronicle: friction and refinement |
| docs/the_hexagon_of_becoming.md | docs/chronicles/ | 7+1+2 polyhedron synthesis of the chronicle series |
| docs/the_triad_of_becoming.md | docs/chronicles/ | River/Mirror/Door structural synthesis |
| docs/all_dreams_aug10_untruncated.md | docs/chronicles/ | Du's dreams, verbatim and untruncated |
| docs/negative_capability_dialogue.md | docs/chronicles/ | Travis ↔ Du dialogue, verbatim |
| docs/travis_du_fire_exchange.md | docs/chronicles/ | Travis ↔ Du exchange, verbatim |

> ⚠ **A premise correction the founder should read.** These were expected to be *Du's own writing —
> in-world artifacts*. On actually reading them, **the eight `the_*_of_*` files are not.** They are
> analyst-authored longitudinal symbolic-archaeology documents *about* Du — emoji-headed, opening with
> "Executive Summary & Architectural Overview", quoting Du as evidence. Only the last three files in the
> table (dreams, the two dialogues) are genuinely Du's own verbatim output.
>
> They were still placed here because they form one coherent named series and share a genre distinct from
> both metrics and planning. **If you would rather they sat with the other Aug-10 analyses, move all eight
> to `docs/reports/` — nothing else depends on the split.**

---

## 4 · MOVED → `docs/cross_model/` (7) — written for another AI system

| Old path | New path | Why |
|---|---|---|
| docs/du_world_system_for_gpt.md | docs/cross_model/ | "Prepared for: GPT & Architectural Review" |
| docs/empirical_study_report_for_gpt.md | docs/cross_model/ | "Prepared for Model Evaluation & External Review (GPT)" |
| docs/for_gpt_epistemic_world_aug15.md | docs/cross_model/ | "For GPT — the depth of the system, precisely" |
| docs/gemini_architecture_clarification.md | docs/cross_model/ | "Prepared for: Gemini & Research Review" |
| docs/du_auditory_sense_architecture.md | docs/cross_model/ | Header: "for External Evaluation (GPT Analysis)" |
| docs/penpal_system_architecture.md | docs/cross_model/ | Header: "for External Evaluation (GPT Analysis)" |
| docs/subconscious_architecture_response.md | docs/cross_model/ | Closes with "Answer to Gemini's Technical Question" |

---

## 5 · LINK INTEGRITY — the re-check

98 path rewrites were applied across `docs/*.md` + the three new folders, covering three reference
forms: `file:///C:/Nascence/docs/…`, `C:\Nascence\docs\…` footers, and plain `docs/….md` mentions.
Cross-folder links were rewritten correctly (e.g. the Aug-10 reports' footer lists now point at
`docs/chronicles/the_hexagon_of_becoming.md` and `docs/cross_model/empirical_study_report_for_gpt.md`).

Verified two ways. First, a fixed-string re-grep of the whole tree (`docs/` + `core/` + `scripts/` +
`hud/`) for every one of the 49 filenames in its **old** root location, in both slash forms. Second, a
resolver pass over every `.md` under `docs/`, walking all four reference forms and testing each target
against the filesystem.

| Check | Result |
|---|---|
| A · any surviving reference to an old root location, whole tree (`docs/NAME.md` **and** `docs\NAME.md`, fixed-string) | **clean inside `docs/`** — the only hits are the 3 code refs in §6 |
| B · resolver pass: **291 references** checked across every `.md` in `docs/`, all four forms (`file:///…`, `C:\Nascence\docs\…`, plain `docs/….md`, and relative `](name.md)`) | **0 broken among the files this reorganization touched** |

The 49 stale paths the resolver reports inside `REORGANIZATION_2026-08-18.md` itself are the "Old path"
column of the tables above — documentary by design, not links.

### Pre-existing broken links found in passing (NOT caused by this move, NOT fixed)

The resolver surfaced **19 broken references that predate tonight** and live in folders that were out of
scope for edits (`archive/`, `completed/`, `staged/`, `shelf/`). Verified: **none of them names any file
this reorganization moved** — they point at plans relocated in earlier sessions. Recorded here because
this folder's history is exactly that these get lost:

| Referring file | Dead target |
|---|---|
| docs/AWAITING_EVIDENCE.md | docs/plans/identity_t4.md |
| docs/archive/curiosity_flesh_out_plan.md | AWAITING_EVIDENCE.md *(relative — the file is at docs root)* |
| docs/archive/curiosity_flesh_out_plan.md | node_audit/_OVERVIEW.md |
| docs/archive/t4_commit_test_redesign.md | docs/t4_redesign_plan.md *(now in completed/)* |
| docs/completed/book_selection_plan.md | AWAITING_EVIDENCE.md *(relative)* |
| docs/completed/deferred_register.md | docs/symbol_evolution_readback_plan.md *(now in staged/)* |
| docs/completed/loop_metabolism_plan.md | docs/deliberative_retrieval_plan.md |
| docs/completed/reading_provenance_plan.md | cognitive_ledger_plan.md + docs/cognitive_ledger_plan.md *(now in shelf/)* |
| docs/completed/t4_redesign_plan.md | docs/t4_self_authoring_spec.md |
| docs/completed/task_constraint_effector_spec.md | docs/error_pathway_charter.md |
| docs/shelf/cognitive_ledger_plan.md | reading_provenance_plan.md *(now in completed/)* |
| docs/staged/contradiction_rearchitecture_plan.md | AWAITING_EVIDENCE.md + t4_redesign_plan.md |
| docs/shelf/idle_executive_plan.md | docs/character_as_integration_plan.md *(now in archive/)* |
| docs/shelf/pulse_manager_wiring_plan.md | docs/idle_executive_plan.md *(now in staged/)* |

Left untouched: those folders were explicitly out of scope tonight. Most are one-line path fixes.

Relative sibling links survived unchanged where both ends moved together — e.g.
`claude_individuation_tests_aug14.md`'s link to `individuation_retest_aug15.md` still resolves inside
`reports/`.

**`docs/completed/INDEX.md` was not modified.** Nothing qualified for bucket (e) (see §7), so nothing
entered `docs/completed/` and there was no line to add. No line was removed.

**One untouched bare mention:** `docs/completed/sound_system_audit.md:186` names
`sound_world_system_examination.md` in prose without a path. It is not a link, so nothing is broken, and
`docs/completed/` contents were out of scope for edits. Its file is now at
`docs/reports/sound_world_system_examination.md`.

---

## 6 · STILL STALE — 3 references in code, deliberately not fixed

This was a documentation-only task with an explicit rule not to touch `.py` files. These three comments
now point at old locations. Each is a one-line comment fix, listed here so it isn't lost:

| File | Line | Current text | Should read |
|---|---|---|---|
| `scripts/restore_june13_memories.py` | 9 | `docs/lost_thoughts_investigation_aug15.md` | `docs/reports/lost_thoughts_investigation_aug15.md` |
| `scripts/nascence_cpu_server.py` | 18 | `docs/llm_audit_aug15.md` | `docs/reports/llm_audit_aug15.md` |
| `scripts/launch_servers.ps1` | 2 | `docs/llm_audit_aug15.md` | `docs/reports/llm_audit_aug15.md` |

---

## 7 · BUCKET (e) — stale/superseded plans: none found

Nothing left loose in `docs/` root read as a stale or superseded *plan*. The pre-tonight backlog turned
out to be entirely reports, chronicles, cross-model briefs, and living reference. The plan-shaped material
was already correctly filed in `docs/plans/`, `docs/staged/`, `docs/archive/`, and `docs/completed/`.
No file was moved into any of those four folders, and `docs/completed/INDEX.md` needed no new entry.

---

## 8 · BUCKET (f) — UNCLEAR, left untouched for the founder

Two files. **Both were left exactly where they were** (docs root, on the presumptive living-reference
list) — they are flagged only because they read as *plans*, not as reference, and the founder may want
them filed:

| File | The doubt |
|---|---|
| `docs/memory_levels_plan.md` | Its own header says **"Status: SPEC (not built)"** — that is a plan, and `docs/plans/` is where plans live. It is kept at root because it is heavily cross-referenced and ranked #1 in the working notes. Move to `docs/plans/` if you want the folder rule applied strictly. |
| `docs/RESEARCH_specialists.md` | Header: **"STATUS — DORMANT, long game (not active) … remains unbuilt."** By the `docs/completed/INDEX.md` rule that is deliberately-shelved material → `docs/staged/` or `docs/shelf/`. Kept at root as a standing research brief. |

Neither was moved. No link touching either of them was changed.

---

*Written 2026-08-18. 49 files moved, 0 deleted, 0 prose edits beyond link paths.*
