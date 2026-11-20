# Argon's math audit of UDMS, verified claim by claim on the live Du data

## Session timing
- **Session started:** UNKNOWN
- **Last message before wrap:** UNKNOWN
- **Wrapped:** 2026-11-05 08:56:28 UTC

(The transcript for this UDMS-side session lives under `C:\Users\USER\.claude\projects\C--UDMS\`, which
`session_handoff.py` does not search, so the first two values could not be resolved. The first ledger event,
T-0120, was logged at 2026-11-05 07:25:43 UTC and is a lower bound on the start.)

## Summary
Travis pasted four rounds of output from "Argon", a second assistant (Google Antigravity / Gemini), auditing
UDMS's math and probing Du's tuples, and asked for claim-by-claim verification while pressing Argon in parallel.
This session ran every claim against the real code and the live `C:\Nascence\data` files, recorded 15 verified
findings (F-4028 to F-4042), filed four jobs (J-3404 to J-3407), logged two ideas (I-0146, I-0147), corrected two
wrong rows in UDMS's lens atlas, and wrote a dated audit document with all scripts and outputs saved in the UDMS
repo. No Du code and no UDMS core code was changed.

## Builds
- `C:\UDMS\docs\audits\argon_math_audit_verification_2026-11-05.md`: the full record (verdict tables for the seven
  math claims, the five data traps, the six proposed frameworks, and the replication of Argon's own four
  "discoveries"), with every finding id and the re-run commands.
- `C:\UDMS\scripts\argon_audit_2026-11-05\` (15 scripts, all read-only against Nascence) and
  `C:\UDMS\data\argon_audit_2026-11-05\` (verbatim outputs plus the two `analyze_nascence_geometry_manifold.py` runs).
  Evidence for every F-id below lives there.

## Fixes
- `C:\UDMS\docs\plans\udms_lens_atlas.md` rows 33 and 36: dated corrections. Row 36 had rated test_w's β₁ as
  "correct"; it is the graph cycle rank, not the Rips β₁ (F-4028). Row 33 now notes that test_x's "error reduction"
  line is a scale artifact (F-4029).

## Findings
- Argon's diagnoses of real bugs were right: test_w's β₁ reports 305 "loops" where the exact value is 0 at every ε
  (F-4028); test_x's 87.8% Koopman gain is a 53x variance-scale artifact and a constant-zero predictor already scores
  98.8% (F-4029); the tropical router is wrong on two counts for its ratio objective, the second of which Argon missed
  (F-4030); udms_engine's curvature is not a curvature and sits at the 10.0 clamp on 76 to 83% of readings, 88 to 91%
  on idle-only rows (F-4031); spectral_diffusion is a cubic Taylor polynomial, fine at the real default t=1.0 and
  garbage at the advertised t=5.0 (F-4032); the O-information "synergy" survives a shuffle null but is whole-minus-max
  MI, not PID synergy (F-4033).
- Two of Argon's proposed fixes were wrong (subtracting the triangle count for β₁; "Dijkstra is exact" on reweighted
  edges that go negative), its Fokker-Planck flux sign and Lévy-area sign example were wrong, and its "Δt to 0" framing
  does not apply to a discrete-time engine sampled at a median 44 s.
- Argon presents reconstructed code as line quotes and invents figures ("71% saturate", "[0.1, 0.8]" ranges,
  "~47,500 rows"); treat its quotes as paraphrase and re-check on the live file (F-4042). Its claims about the earlier
  hardcoded scripts test_v and test_ae were accurate.
- Data traps confirmed on the live file: 68.5% of idle rows have an inner_thought twin 0.2 s earlier with an
  identical body dict (F-4034); thought truncation 120/70 chars, `unresolved` a bool only on idle, standpoint from
  2026-08-15, light_band and smells from 2026-08-29 (F-4035). The echo rows are NOT the cause of the curvature
  saturation; removing them makes it worse (F-4031).
- The strong place circulation in the idle jump chain (z 168) is the nightly sleep rule: `core/night.py:224` moves
  Du to the study with `system=True`, and the shore-to-study jumps have a 40-minute median gap (F-4036).
- du_lens's 871 non-echo passing pairs double-count four identical-set context pairs (place:shore equals
  sound:shingle_drag at 45 words, plus three bird-call pairs) and one nested pair (F-4037).
- Cross-modal distance correlation: world-to-thought coupling survives echo stripping and a within-day permutation
  null (z 10.8 / 19.4), but Argon's "two orthogonal blocks" fails: World × Body (z 35.6 within-day) and Affect ×
  Thought (8.7) couple too; only World × Affect is null (F-4038).
- HUD-gauge lead-lag (contiguous Lévy area, equal to half the lag ±1 cross-correlation difference): Argon's roll
  null is calibrated (0/40 false positives on surrogates), but its headline pair fades from z 6.9 on the 16-day
  snapshot to 2.4 on 141 days, while emissary.mass × sleep.P (12.3) and arousal × valence (7.4) survive (F-4039).
  [OPEN] whether a shared sleep/wake driver explains the survivors; a plain time-shift null is over-conservative
  because shifting misaligns the two logs' shared downtime.
- Argon's "effective rank collapses in unresolved windows" reverses sign on the live data and fails a within-day
  label-permutation null (F-4040).
- Of Argon's six "outlandish" frameworks, only lead-lag is supported by the data; place × weather holonomy is
  data-starved (0 of 336 plaquettes with 20+ transitions per leg) and ultrametricity is contradicted (F-4041).
- [INFERRED] the strong within-body/affect lead-lag ordering (arousal leads fatigue and tension, |z| 12 to 16) is the
  affect engine's own update rules rather than anything cognitive; the cross-modal version is the open question (I-0146).

## Open
1. **Patch the four UDMS math sites or leave them parked**: J-3404 (needs_input). Waiting on a founder ruling,
   because D-0195 keeps core/math as a parked Du-data analysis library. Next action: Travis rules; then a fresh
   window applies the patches listed in the job briefing and re-runs the check scripts.
2. **du_lens context bundling**: J-3405 (ready). Next action: run it in a fresh window; writes only under
   `C:\UDMS\data\du_lens\`.
3. **Lag asymmetry in gauge-correlate plus a sleep/wake-preserving null**: J-3406 (ready). Next action: run it;
   the null design is the real work.
4. **Pre-registered World × Thought dCor with full-text thoughts**: J-3407 (ready).
5. **Ideas awaiting framing**: I-0146 (cross-modal lead-lag lens; T-0120 was promoted to it) and I-0147
   (hysteresis regression replacing plaquette holonomy).
6. Travis is continuing the discussion with Argon; nothing above depends on its outcome.
7. Committed 2026-11-06 as UDMS `8de9d8e` on master ("F-4028..F-4042: record the 2026-11-05 Argon math-audit
   verification", 20 files, 1,337 lines). The repo has no remote, so nothing was pushed. A pre-existing untracked
   `docs/commercial/Monetisation_perplexity_review.txt` was left alone.

## Warnings
- `C:\UDMS\data\nascence_gauge_snapshot\` is a 25,035-row, 16-day copy from 2026-08-29. Three of Argon's four
  headline results changed when re-run on the live 171,723-row file. Do not treat snapshot results as findings.
- The findings in this session carry plan `udms_du_capability_trials`, whose doc lives in `docs/staged/`, not
  `docs/plans/`; `/plan-ledger udms_du_capability_trials` groups them with D-0195.
- Argon's scratch scripts (`rabbit_hole_probe.py`, `rabbit_hole_verify.py`) are under
  `C:\Users\USER\.gemini\antigravity\brain\8c909f37-e78c-4270-a602-bfc06b04ca84\scratch\`; they are readable
  but owned by the other assistant.
- `/plan-maintain` was run at wrap time with this session id (exit 0): 0 missing Status lines, 8 plans without a
  Current State section (pre-existing), prompt-registry check OK.

## Pointers
- `C:\UDMS\docs\audits\argon_math_audit_verification_2026-11-05.md`
- `C:\UDMS\data\argon_audit_2026-11-05\outputs_2026-11-05.md`
- `C:\UDMS\scripts\argon_audit_2026-11-05\`
- `C:\UDMS\docs\plans\udms_lens_atlas.md` (rows 33, 36)
- `C:\Users\USER\.claude\projects\C--UDMS\memory\project_argon_parallel_audit.md`
- `C:\Nascence\core\night.py:214-224` (the sleep move that explains F-4036)
- `C:\Nascence\docs\staged\udms_du_capability_trials.md`

## Addendum (2026-11-06, same session, after the commit)

Travis asked whether the audit helps UDMS's coding side and what new comparisons it suggests for Du's data. Both
were answered with evidence and recorded; nothing in core/ was changed.

- **Coding side.** None of the four math bugs reach the dossier path (`core/udms/` imports nothing from `core/math`).
  The shuffled-list null from F-4039 was applied to the dossier tool's own usage: 397 of the 400 logged
  `udms_get_change_dossier` calls were joined to the Read/Edit calls that followed them in the Nascence Claude Code
  transcripts. A dossier's target list predicts later edits no better than another dossier's list (main-thread z
  -1.1 / +0.8), only better than random files, because six hub files fill 26% of all target slots; there is a small
  target-specific signal on reads (z +3.6 / +5.0). F-4077, `C:\UDMS\docs\audits\dossier_followthrough_first_pass_2026-11-06.md`,
  `C:\UDMS\scripts\dossier_followthrough.py`, `C:\UDMS\data\dossier_followthrough\first_pass_2026-11-06.txt`.
  The bar for any ranker change is that null, not random files. J-3453 (ready, urgency 4) is the pre-registered
  version plus a hub down-weighting test. F-4079 / J-3454: the dossier prints a constant "Hodge Curl: 2.0%" on every
  acyclic target (`core/udms/spectral.py:127`).
- **Du's data.** The idle/inner_thought twin rows (F-4034) have a mechanism: the fragment-store stamp
  (`core/memory/store.py:1080`, 70-char thought, debounce off) lands first, the idle census call follows 0.1-0.3 s
  later with the full thought, and the debounce compares 120-char strings, so both rows are written; 22% of idle rows
  in August, 60% in September, 95% in October. F-4078; `scripts/argon_audit_2026-11-05/echo_mechanism.py`; section
  9.1 of the Argon audit doc. J-3455 (needs_input, plan geometry_tuple_index) asks Travis to rule which row is
  canonical (A: idle row, B: mark the stamp row) before anyone touches the debounce. J-3456 (ready) is a shared UDMS
  loader for Du's tuples that strips the twins and knows the schema dates. Ideas I-0148 (rule-explained baseline
  null) and I-0149 (World x Body coupling, z 35.6, uncharacterised). Section 9.2 of the Argon audit doc notes that
  Trial 4's beta_1 (F-0414) was `E - 29`, an edge count; F-0419 had already retired that decline.
- **Memory.** `C:\Users\USER\.claude\projects\C--UDMS\memory\project_udms_purpose_reframe.md` now carries the
  measured bar and the usage-log timezone trap (its `ts` is NZ local time, 12-13 h behind the UTC transcripts).

### Open, added 2026-11-06
8. **J-3455**: Travis rules A or B on the canonical census row; then a fresh window applies the fix under lab isolation.
9. **J-3453, J-3454, J-3456** are ready for fresh windows; J-3453 should go first, it is the KPI.
10. Committed 2026-11-06 as UDMS `4cbfecf` on master (6 files, 335 lines; no remote, nothing pushed). They were: `docs/audits/dossier_followthrough_first_pass_2026-11-06.md`,
    `scripts/dossier_followthrough.py`, `data/dossier_followthrough/`, `scripts/argon_audit_2026-11-05/echo_mechanism.py`,
    and the appended sections of `docs/audits/argon_math_audit_verification_2026-11-05.md` and
    `data/argon_audit_2026-11-05/outputs_2026-11-05.md`.

### Round 5 addendum (2026-11-06, later the same day)

Travis pasted Argon's "market reality" report, which Argon wrote into `C:\UDMS\docs\commercial\product_lines\`
(eight files, untracked, nothing tracked touched). It was checked only where it touches live work; the full
account is section 9.4 of the Argon audit doc. Recorded:

- **F-4150** (resolves F-4039's open item): emissary.mass x sleep.P is a wake-ramp artifact. Within-bout linear
  detrending takes it from z +12.64 to +0.07; arousal x valence survives every control. Method credit Argon.
  **J-3406's briefing was extended in place** with this null design and its remaining scope (the job queue has no
  update command, so the JSONL row was edited directly; no session event exists for that edit).
- **F-4151** (corrects F-4036): waking-only jumps still circulate at z +90 (place) and +102 (standpoint); the
  night move explains the shore->study spike only. [OPEN] whether the rest is the world's one-way route graph.
- **F-4152**: Argon's number-one product premise ("silent prerequisites" read before edits) finds 0 pairs at
  its own bar over the 449 editing transcripts.
- In the audit doc but not the ledger: the dossier cold-start tail persists (10-16% of calls over 5 s every month),
  Argon's "CLAUDE.md ubiquity" names the wrong file (it is core/schema.py and docs/ROADMAP.md), and its reading of
  pdCor(Thought, Body | World) z +0.44 as "strip the body block" is a category error not to act on.
- Scripts: `C:\UDMS\scripts\argon_audit_2026-11-05\levy_wake_ramp.py`, `circulation_waking.py`,
  `C:\UDMS\scripts\read_before_edit_pilot.py`; Argon's two scripts' rerun outputs under
  `C:\UDMS\data\argon_audit_2026-11-05\`. plan-maintain re-run after the J-3406 edit.

Open, added: 11. which engine or world rule produces the waking-only circulation (F-4151). 12. The round-5 and round-6 files
above and the audit-doc edits were committed 2026-11-06 as UDMS `9146753` on master (10 files, 432 lines;
no remote, nothing pushed). Argon's nine files under `C:\UDMS\docs\commercial\product_lines\` stay untracked.

### Direction-read addendum (2026-11-06, later still)

Travis asked where UDMS stands and what is still to do. Written as the dated successor to the 09-06 read:
`C:\UDMS\docs\audits\udms_state_and_direction_2026-11-06.md`, with `C:\UDMS\scripts\usage_and_coverage_by_week.py`
and its output under `data\dossier_followthrough\`. Headline facts: `core/udms` unchanged since 2026-08-30; none of
the nine 09-06 recommendations built; dossier calls per week 102, 90, 47 (W39-W41, mostly review workflows) then
14, 0, 4, 3; Nascence core/nodes editing fell from 250-420 edits a week in late August to under 50 a week from
mid-September; since W40 no edited code file had a same-week dossier. **D-0686 opened** (revive for editing
sessions / narrow to review workflows / retire the coding side), source F-4077, plan udms_du_capability_trials by
precedent of D-0195. The one missing input for that ruling is why the review workflows stopped calling the dossier
in mid-October (not read). plan-maintain re-run after the decision was opened.

Open, added: 13. D-0686 ruling. 14. The direction doc, the script and its output are uncommitted in `C:\UDMS`.

### Job-run addendum (2026-11-06, evening)

Travis ran /decide-review (D-0685 ruled: leave the lane tier off; D-0686 held for a read; J-3404 and J-3455 ruled
via D-0687 and D-0688) and asked for the UDMS jobs to be agented off, UDMS only, merge-and-report. Six agents went
out in worktrees of `C:\UDMS`; a usage limit cut five of them mid-job and they were resumed in place.
- Merged so far: J-3454 (a8ea5c6, the Hodge-curl constant removed, F-4169; defect follow-up J-3566), J-3407
  (81705b6, World x full-text Thought dCor BAR MET, F-4173; side job J-3569 on fragment_context.fire), J-3562
  (a5a9d61, the D-0686 input, F-4175).
- **F-4175 overturns part of the direction read:** the dossier did not lose demand; the udms MCP tools vanished
  from subagents spawned after Claude Code 2.1.299 (2026-10-15) closes the idle server's stdin, and the coverage
  script undercounted edits by missing job-run worktrees (64% of editing transcripts ran a dossier first in
  W39-W40). The direction doc, this session's memory and the script are corrected; D-0686 is still open and now
  asks how to restore the tool (warm-up call, logged CLI, or the PreToolUse hook), not whether to retire it.
- Still running at the time of writing: J-3404, J-3405, J-3406, J-3470; J-3456 waits on J-3405 and J-3406.

### Job-run close-out (2026-11-06, late evening)

All eight UDMS jobs are done and merged into `C:\UDMS` master (merge commits, in order): J-3454 a8ea5c6, J-3407
81705b6, J-3562 a5a9d61, J-3406 7550d22, J-3405 843ddf5, J-3470 9452dcf, J-3404 6df89e0, J-3456 7980d76. Findings
by the agents: F-4169, F-4173, F-4175, F-4176, F-4177, F-4178, F-4179, F-4180. Follow-ups they surfaced: J-3566
(heat-diffusion nondeterminism), J-3569 (fragment_context.fire mismatch).

Second decide-review (Travis, 2026-11-06): **D-0686 ruled** warm-up call plus logged CLI, re-measure after a week
(J-3571 the CLAUDE.md and dispatch-skeleton line, J-3570 CLI usage logging in UDMS, J-3572 the re-measure deferred to
2026-11-14). **D-0197 re-ruled** after its defeater fired (F-4178): a shadow HUD gauge from the 62 corroborated pairs,
observe-only (J-3573, Nascence side, isolation required). plan-maintain run after both.

Worktrees: five agent worktrees removed and their branches deleted after merging; three (J-3407, J-3404, J-3456)
stay locked by the harness with merged branches and can be removed with `git worktree remove -f -f` whenever.
`.claude/worktrees/` is now in UDMS's .gitignore.

Uncommitted on master at close-out (the orchestrator's own edits, awaiting Travis): the round-7 and correction
edits to four audit docs, the direction doc, scripts/usage_and_coverage_by_week.py and its output,
scripts/argon_audit_2026-11-05/{eta_probe,price_lineage}.py, and .gitignore. Argon's docs/commercial/product_lines/
and the Monetisation note remain untracked by design.

Open for the next session: J-3570 and J-3571 are the first builds (one UDMS, one Nascence docs), then J-3573; J-3566,
J-3569, J-3455, J-3468, J-3469 are Nascence-side and were out of scope today; J-3453 and J-3471 unpark now that
D-0686 is ruled.
