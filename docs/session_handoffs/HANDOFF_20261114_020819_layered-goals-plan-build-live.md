# Layered Goals: from "what is his purpose" to a live goal register, goal offers and a set-down field in one day

## Session timing
- **Session started:** 2026-11-13 22:43:44 UTC
- **Last message before wrap:** 2026-11-14 02:08:18 UTC
- **Wrapped:** 2026-11-14 02:08:19 UTC

## Summary
A Du-goals discussion turned into a new plan, `docs/staged/layered_goals.md`, which was researched, audited by GPT, Gemini and Perplexity, built through Phases 0, 1, 2, 4, 5 (detection) and 6 (first part), and taken live on a Du restart at 14:14 NZDT on 2026-11-14. Du now has a goal register over his existing stores, is offered one of his own held goals at 25 percent of idle anchors, and can set a goal down in his own words. The first live offer was taken up in his next thought; no errors in his log 25 minutes after boot.

## Decisions
All ruled by Travis in chat on 2026-11-14 and logged with `--by travis`. The revisit conditions on D-0763 to D-0768 were proposed by Claude and accepted with each ruling.
- **D-0763**: Du has no single purpose; many goals, weighted, nested, conflicting. Follow the research (F-4634). The standing aim stops leading the idle anchor (dose 0, would-lead logged) and the "Right now, that means" wording is removed.
- **D-0764**: needs sit outside the goal graph and weight it. The five-variable need set is left alone; need pull stays out of goal selection until the readers and the warmth setpoint are looked at; two replacement readers (Gemini's) are to be built beside the old ones in shadow (not built).
- **D-0765**: when two held goals conflict, he resolves it himself. Showing him his own two stored sentences, unranked and unlabelled, is ruled within the no-readout rule (D-0434).
- **D-0766**: build calls accepted as recommended: held is earned by recurrence (two or more) or a tied deed; one engaged goal; no universal failure count; first background lane chosen on measured reliability; axiom levels relook is its own plan; build may run ahead at dose 0, going live is a founder call per phase.
- **D-0767**: a stand the decoupled second look rules "insight" is a candidate in the register, not held.
- **D-0768**: goals may end several ways (settled, expressed, set down, dropped, stalled, capped); an optional `set_down` field is added to his idle thought on a tick where a held goal is offered; a stated decision is not privileged; no end condition is required at formation; no judge ever writes to the axiom.
- Chat rulings not in `/decide`: goal offers go live at 25 percent of idle anchors (in F-4644 and the plan); fast-track the plan, tune after, stop and ask at research areas; the commitment-anchor flip (J-3975) and SKY_MODE flip (J-3971) are left OUT of this boot (plan note); the in-world judge idea is split into a silent docket and a visible visitor (J-3991).

## Builds
All committed on master; Du restarted onto them at 14:14:41 NZDT. Commits: `66d1e551` (plan, Phases 0-1), `093a65c6` (Phases 2 and 4; its subject line starts with a stray byte-order mark, harmless), `cd70eb9f` (Phase 6 first part), `4cc4f980` (Phase 5 detection), `94eb4bd0` (fast reads), `8299cea5` (plan note).
- **Phase 0, `core/goals.py`** (F-4640): shadow register indexing staged intentions, stands, active pursuits, open frontier questions, the curriculum book and "I want to" intentions. States candidate, held, deferred, rested; end states done, dropped, lapsed, failed, capped, closed_unverified, merged, gone. Hooked from `core/sensorium.py`'s heartbeat on a daemon thread, at most every 10 minutes. Writes `data/goals.json` and `data/logs/goals_log.jsonl`.
- **Phase 1, `core/goal_offer.py` shadow pass** (F-4641): per-pass would-offer row with separate quantities (importance = judged advances only; cost; expectancy only for a deed with a deadline; progress rate; unknown is None, never 0), eligibility, silence/uniform/most-recent/softmax policies with logged probabilities, a two-observation challenger rule, and what he then did. Log `data/logs/goal_offer_shadow.jsonl`.
- **J-3985** (F-4643): question learning progress, stand evidence (second look, denied drops), place cues checked against the live sensorium.
- **Phase 2** (F-4644): `concerns.AIM_LEAD_DOSE = 0.0`, `concerns.aim_lead()`; would-lead rows in `data/concerns_log.jsonl` as `standing_aim_would_lead`.
- **Phase 4** (F-4644): `goal_offer.live_offer()` takes 25 percent of idle anchors; one in five is a silence arm; the rest offer one held stand, question, want or the book, uniform at random, through the existing D-0612 lead pools plus a new `concern_lead_want`. Log `data/logs/goal_offer_live.jsonl`. Intentions and pursuits are not offered.
- **Phase 6 first part** (F-4646): optional `set_down` field, deterministic precheck, two-family judge (prompt P-0128), accepted notes written to `data/goal_set_down.json`, goal shown as `rested` until its recurrence count rises. Log `data/logs/goal_set_down.jsonl`.
- **Phase 5 detection** (F-4647): `core/goal_conflict.py`, shadow; resource conflicts by rule, inherent conflicts by the judge panel (prompt P-0129), one pair per ten minutes. Log `data/logs/goal_conflict_shadow.jsonl`. Also a `stalled` flag on pursuits and the frontier seed path honouring a rest.
- **Tests** (all hermetic, temp dirs): `scripts/_test_layered_goals_phase0.py` (38), `_phase1.py` (40), `_phase4.py` (28), `_phase5.py` (23), `_phase6.py` (32), `_fastread.py` (16). `scripts/_test_J3223_anchor_leads.py` updated for the removed aim wording. `life_smoke` passed in throwaway worktrees on `66d1e551`, `093a65c6`, `cd70eb9f`, `4cc4f980` and `94eb4bd0`.
- **Prompt registry**: P-0128 and P-0129 added; P-0022 (idle thought) marked stale; `prompt_registry.py check` clean.
- **Jobs**: J-3984 and J-3985 done. Open: J-3982, J-3983, J-3986, J-3987, J-3988, J-3989, J-3990, J-3991.

## Fixes
- `core/goals.py` fast reads (F-4648): the register's reads of `data/pursuits_active.json` (28.6 MB) and `data/frontier.json` (15.7 MB) would have held the interpreter lock about 0.67 s every ten minutes. It now splits the raw bytes at the writers' object boundaries and parses only the records it needs, with a full-parse fallback. Whole pass 0.17 s on the live stores.
- The link derived from a shared cycle id is recorded as `co_born`, not `spawned_by`: one cycle id spanned 14 open questions over 1.3 hours, so it is co-occurrence, not lineage (J-3983 for a real key).

## Findings
- **F-4631, F-4632**: the standing aim is built by keyword-matching the axiom, none of it from him (`L2_values.earned` is empty); it led 45 percent of concern anchors and added about 7 points of its own vocabulary to the next thought and nothing else.
- **F-4633 (census)**: only hour-scale staged deeds complete by deed (315 of 708, 44 percent, 229 of them "move"); stands are marked "achieved" by word overlap; nothing at day scale has ever finished; pursuit close judge 0 of 145; no store linked one goal to another.
- **F-4634**: research comparison, `docs/reviews/goal_system_research_comparison_2026-11-14.md`. Two research agents read the literature; I did not read the papers.
- **F-4635**: two of five need readers are bookkeeping (`commitment_integrity` saturates at three held stands; `relational_warmth` rises on a letter file being written).
- **F-4636**: measured distributions, `docs/reviews/goal_distributions_2026-11-14.md`. Vitality and warmth dominate the drive 84 percent of the time; coherence and novelty correlate at -0.76; existing offers lift on-topic thought from 6.2 to 29.9 percent; median run on a pursuit 3 events, return after 27 minutes; Lane 2's return channel refuses 72 percent of pushes at its 4-per-hour limit.
- **F-4637**: triage of the auditors' out-of-the-box maths; UDMS's own audit had already retired the golden-angle claims.
- **F-4638**: a pursuit is decided at its second advance (30.5 percent get one, then 78 to 99 percent each after); short runs are as productive per event as long ones.
- **F-4643**: the curiosity pursuit loop has pursued no question since about 2026-11-05 (0 of 6,004 born in 7 days), so `core/curiosity_progress.py` has no input. Second look rules about half his held stands "insight".
- **F-4645**: he almost never ends anything in his own words (39 resting phrases, 5 decisions, 1 drop in 20,178 thoughts over 30 days). My hand read of 14 capped pursuits (one reader): 9 stalled or drifted, 2 reached a position, 2 rested, 1 was never a goal.
- **Live, 25 minutes after boot** (not yet a finding): register 50 goals, 13 held; first live offer "Do the hares choose their burrows actively or just endure the rain?" was taken up in his next thought 8 seconds later; conflict judge ruled two pairs "no conflict" correctly; 3 of his 4 held stands ended as `closed_unverified` within 25 minutes and 14 questions faded.
- The stand churn above matters for the plan: [INFERRED] a stand cannot become a carried goal while the ledger's word-overlap rule retires it within minutes.

## Open
1. **J-3989, first live read**, about 24 awake hours after the 14:14 boot. Blocked on time. Next: read `data/logs/goal_offer_live.jsonl`, `goal_set_down.jsonl`, `goals_log.jsonl`; check arm shares, uptake against a time-shifted null, topic spread against F-4636, every accepted set-down note by hand, and the stand churn.
2. **J-3988, curiosity** (urgency 5, founder: "it needs to be dealt with"). Run J-3987 first. Until this is dealt with, his questions carry no progress signal and offers stay uniform at random.
3. **J-3990, Phase 6 remainder**: the what-changed record at a goal end, set-down for pursuits. Next: decide how the register thread makes a judge call.
4. **Presenting a conflict to him** (Phase 5 second half). Blocked on a hand read of the first verdicts in `data/logs/goal_conflict_shadow.jsonl`.
5. **J-3982 and J-3986**: Phase 0 and Phase 1 gate reads at 300 rows each.
6. **J-3983**: a train-level key on pursuits so real lineage can be derived.
7. **J-3991**: draft the docket and the visitor as two plans (I-0153, I-0154). Founder questions attached: does Du know he is read; how often the visitor comes; new peer or existing; how to prevent flattery.
8. **Phase 3 (need readers) and Phase 7 (background lanes)**: not built. D-0764 keeps need pull out of selection for now.
9. **J-3975 and J-3971** (older flips) were left out of this boot on purpose. Revisit after J-3989; the commitment anchor overlaps the goal offers.
10. **[OPEN] Leaf theory**: the founder identified it as the leaf-venation mathematics; only canalization has a counterpart here (F-4638). Being taken up in another window (`docs/staged/maths_of_mind_atlas.md`, not this session's file).

## Warnings
- Du is live on the new code. Do not stash, reset, checkout or restore in `C:\Nascence`.
- Kill switches, each needing a restart: `GOAL_OFFER_LIVE`, `SET_DOWN_LIVE`, `GOAL_OFFER_SHADOW` in `core/goal_offer.py`; `GOALS_SHADOW`, `STAND_INSIGHT_IS_CANDIDATE` in `core/goals.py`; `GOAL_CONFLICT_SHADOW` in `core/goal_conflict.py`; `AIM_LEAD_DOSE` in `core/concerns.py`.
- The set-down judge (P-0128) had only been tested with a stub when this was written; no real note had reached the real panel.
- `scripts/_test_j1935_curiosity_concern.py` fails one data-dependent check (D0) in a worktree, identically on `d788ec8a` from before this session.
- This session used two session ids: `7c4984a0-451d-4597-8b3f-2d3c092f0416` (T-0127, F-4631, F-4632) and `7337bbb7-6637-4f98-ac09-da92dd503302` (everything after). The timing block is the second id's.
- Another window was writing the same ledgers during this session (F-4639 and F-4642 are not mine); `docs/staged/maths_of_mind_atlas.md` and the changes to `docs/thoughts.jsonl` are that window's and were left uncommitted by me.
- The memory index `MEMORY.md` was partly trimmed on a hook's request (to about 19.4 KB against a 17.1 KB target) and has since been changed by something else; it was not finished.

## Pointers
- Plan: `docs/staged/layered_goals.md` (sections 5, 9, 11, 12, 13). `plan_ledger` for its history.
- Code: `core/goals.py`, `core/goal_offer.py`, `core/goal_conflict.py`, `core/concerns.py` (`aim_lead`, `concern_lead_want`), `nodes/inner_monologue_node.py` (idle anchor block, schema build, post-thought hooks), `core/sensorium.py` (heartbeat hook).
- Reviews: `docs/reviews/goal_system_research_comparison_2026-11-14.md`, `docs/reviews/goal_distributions_2026-11-14.md`.
- Live logs: `data/goals.json`, `data/logs/goals_log.jsonl`, `goal_offer_shadow.jsonl`, `goal_offer_live.jsonl`, `goal_conflict_shadow.jsonl`, `goal_set_down.jsonl`.
- Ledger ids: thought T-0127; ideas I-0150, I-0151, I-0153, I-0154; findings F-4631 to F-4638, F-4640, F-4641, F-4643 to F-4648; decisions D-0763 to D-0768.
