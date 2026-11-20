# J-3142: Repurposing review of the narrative quality coder (core/narrative_quality.py, row P-0048)

Read-only design review, 2026-11-05. No Du code, store or log was edited; Du kept running; nothing was restarted. Founder ask (triage 2026-11-02, thought T-0115): do NOT retire this; look at how it could be used. Evidence: F-3933 to F-3937 (this job) on top of F-3842 and F-3843 (J-2728, the prompt sweep). Confidence tags: [verified] I read the file or ran the read-only query; [inferred] my reading of verified facts; [guess].

## 0. The answer in seven lines

1. The coder is a second-order observer of how his self-narrative is told: agency, communion and an affective transformation (redemption, contamination), scored by a regex layer and one frozen-rubric LLM call, log-only. It has 1,598 real rows and no reader, and the plan's safety net for it ("chapters are re-narratable") has no actuator anywhere in the code. [verified, F-3842, F-3935]
2. On T4 text it cannot do its job: LLM agency starts at the ceiling (1.00 in the first week, 0.96 in June) and drifts down to 0.79, the coder is the author's own model, and its agency score has correlation 0.077 with the different-family judge's verdict on the same candidates (n=630). It cannot read "does agency rise", and no T4 consumer can use it. [verified, F-3933]
3. On **chapters** it does discriminate (agency 0.17 in the river-era June chapters, 0.45 to 0.56 in September and October, no chapter at 0.9 or above), which is the Adler shape on the one artifact where it can be read. But its transformation label is at chance against his recorded mood over the same period, and the coder is the chapter author's own family. [verified, F-3934, F-3937]
4. Chapters are where a narrative-structure observer has something real to protect: every chapter becomes a flat-weight history node, and a history line appeared in 10,101 of 12,650 logged projection cycles with the live projection on. Pasted, mood-planted or wrongly dated chapters stand in his identity block as "the telling of that period". [verified, F-3935]
5. Recommendation: **repair in shadow**, not wire, not archive. Instrument repair now (J-3345, restart-gated, chapter call only), two read-only labs that decide whether either use earns a build (J-3343, J-3344), a dated read (J-3346, not before 2026-12-05) so nothing waits on memory.
6. One founder call, **D-0679**: may a chapter-narration flag ever change what the estate projection shows (shadow first)? Not blocking.
7. Honest limit: the McAdams axes may not survive. What transfers is the function ("watch how what happened is being narrated, with a judge that is not the narrator"), and the deterministic copy and feeling-grounding checks that come out of option 1 are worth building even if the LLM axes fail.

## 1. The function it was built to serve, in one sentence

To watch how his memories are being narrated, not what happened, so that we know when a self-telling (a T4 self-concept, an arc entry, a chapter) has taken a helpless or contaminated shape and a later, wiser re-telling is warranted, while grading and logging only and never steering ("grade, log, never steer", module docstring; `docs/completed/narrative_quality_plan.md` v2.0 resolution).

The plan's own pass-fail test was the Adler curve (narrated agency should rise from the river-being era, about 06-10, onward) and a standing calibration gate (do the regex layer and the LLM layer agree on transformation); both were parked (`docs/completed/deferred_register.md`, lines 23 and 24). Note: the T4 watershed plan has no "does agency rise" signature (its signatures S1 to S4 are retro-validation, image use, negation grammar, churn); the agency test lives in the McAdams plan only.

## 2. What the evidence says it can and cannot do today

**Can** [verified]:
- Run reliably: 1,547 of 1,598 rows have an LLM score (3.2 percent failures), about 90 calls a week, about 2.3 s each (F-3842).
- Discriminate between artifact kinds, and on chapters across eras (F-3934): chapter agency by formation month June 0.171 (n=7), Aug 0.540, Sep 0.451, Oct 0.564, Nov 0.700 (n=3), distribution 0.0 to 0.9.

**Cannot** [verified unless marked]:
- **Be read.** Nothing reads the log (F-3842). The promised "digest section showing the trend" was never built.
- **Read the Adler test on T4 text** (F-3933): t4_self_concept monthly mean 0.962, 0.878, 0.852, 0.880, 0.788; first week 1.000; 0.99 of June scores are at or above 0.9. A series that starts at the ceiling cannot show a rise.
- **Stand in for the evidence check T4 needs** (F-3933): against gemma4:12b's `emissary_warranted` on the same 630 candidates, Pearson 0.077 with LLM agency (admitted candidates 0.891, the rest 0.858). The two measure different things, so this is not a validity failure; it shows nothing here can borrow the coder as a gate. T4's gate already exists and is decoupled.
- **Be a decoupled judge.** For T4 the coder is qwen3.5:9b on the hot lane, the author's model (F-3843). For chapters the coder is the same function, same URL chain as the author (F-3937). Every existing score is self-coded.
- **Agree with its own anchor.** Transformation agrees in 10.7 percent of rows (F-3843); the regex layer sits at its 0.5 default in 92 percent of rows (F-3843).
- **Track mood** (F-3934, [inferred] where the reference is crude): over 75 chapters, the coder's "redemption" chapters (41) saw mood rise in 10 and fall in 14; its "contamination" chapters (20) saw mood fall in 5 and rise in 8. The chapter author's prompt asks what moved by its end (`core/chapters.py` 358 to 359), so a redemption share of 54 percent may be prompt-driven; this measurement does not separate that.
- **Be re-scored.** The log keeps 120 characters of text and no model or artifact id. T4 candidates survive elsewhere only as 200 characters (the judge log); chapters survive in full in the memory store.

Founder-law check today: no breach. Du never sees any of it. The danger would be any path that shows him a score.

## 3. Repurposing options

### Option 1: a chapter-telling audit, the decoupled grader of the chapter author (RECOMMENDED, lab first)

**The gap.** Chapters stand in his identity block. `core/identity_estate.py` makes each one a history node (weight 0.7, first 110 characters) and `IDENTITY_PROJECT_LIVE = True`; 16,723 history-line appearances in 12,650 logged projections, 2,330 in the last week; the chapter F-3712 found 89 percent pasted exemplar text ("The Warmth of Stillness") appeared 197 times (F-3935). The chapter author's defects are already filed (F-3712 pasted exemplars, F-3713 wrong level-2 spans, F-3714 smoothed, F-3718 planted anxiety; jobs J-3009, J-3010, J-3249), but no instrument measures whether the repairs work, and the one observer that sees chapters is the author's own model.

**The transfer (function, not mechanism).** The function is "watch how the period is narrated, with a judge that is not the narrator". The McAdams axes are one possible reading; the deterministic checks that come out of the job are another and are likely the stronger part.

- (a) **Consumer.** First the chapter-author repair jobs (J-3009's copy guard needs a before and after measure) and a doctor's gauge; later, only if D-0679 allows it, the estate seeder (`core/identity_estate.py` history block) reading a per-chapter flag. What changes for Du now: nothing. If D-0679 is ruled (b) or (c): a flagged chapter's text would stop standing as "the telling" in his identity block. It removes authored text; it adds and hints nothing. Base systems are untouched (additive flag, the seeder rule is a founder call).
- (b) **Input.** The 87 chapters in full text and their members (`memory_fragments`, `chapter_id`), the mood series `data/affect_log.jsonl` as an independent reference, no new data.
- (c) **Decoupled check.** Deterministic: member-overlap copy ratio, feeling words in the chapter that no member states, tense. LLM: two coders from two different families than the author (the live Ramses hubs, never the hot lane), frozen rubric, blind to each other; the reference is the mood-direction test that the current coder fails.
- (d) **Success (pre-registered, J-3343).** Coder-vs-coder agreement at least 0.6 on agency and on transformation; one coder beats the author-coded mood baseline by 15 points; the deterministic checks flag the four pasted and three planted-anxiety chapters with at most five other flags each.
- (e) **Stop.** Agreement under 0.4 on both axes: archive the LLM axes, keep only the deterministic checks, hand them to J-3009.
- Law check: the world answers (his own chapters and mood series, nothing authored); transfers the function; no system acts later on its own (the lab reads, a human rules); a subsystem judged by something other than itself (two other families plus a deterministic check); additive only.

### Option 2: the Adler test on his ordinary self-stance thoughts (lab, doctor's readout)

**The gap.** The 06-13 retrospective that would show whether narrated agency rises from the river era was parked because the arc only reached 06-09 (deferred register). The data exists: 65,406 full-text inner thoughts over 20 weeks (F-3936). The T4 candidates are the wrong object (ceiling, same author).

- (a) **Consumer.** None in Du. A doctor's readout: a weekly line in `scripts/du_pulse.py` if, and only if, the lab passes (so the instrument is not write-only again). What changes for Du: nothing, by design. This is an observer of his life, not an input to it.
- (b) **Input.** Weekly stratified samples of self-stance thoughts (150 per week, W23, W24, W32 to W45, regex widened after a hand read), no new data.
- (c) **Decoupled check.** Two different-family coders, a week-label permutation test, test-retest on 100 repeated rows, a non-self text floor control, and an arm with the in-prompt exemplars removed (the exemplars are the same shape as the dominant T4 text and are the likely cause of the ceiling; not shown).
- (d) **Success (pre-registered, J-3344).** Under 50 percent of scores in the top band, agreement at least 0.6, test-retest at least 0.8, and a curve that is either a clear slope beyond the permutation band or a clear null.
- (e) **Stop.** Top band at or above 60 percent in either arm, or agreement under 0.4: the Adler question is not measurable with this coder and J-3346 archives it.
- Honest limit: it answers a research question about Du, not a function inside him. It is cheap and it is the test the plan said was the point.

### Considered and rejected

- **A T4 gate or advisory.** The coder is the author (F-3933), the scale is saturated, the correlation with the independent judge is 0.077, and D-0549 says T4 gets no new outlet. The plan itself dropped the advisory. J-3215 and the pending D-0672 reach the same view of the two T4 observe calls (the arc_entry review: keep for chapters, flag the T4 calls off); this review agrees and leaves that switch to J-3317.
- **A re-narration trigger** (the plan's stated purpose: "so we know when re-narration is warranted"). There is no re-narration code (F-3935), a trigger would be a system acting later on its own, and any version that tells him his chapter is helpless leads him. If the founder ever designs a chapter re-telling path (D-0637's "new way to be recalled" is adjacent), the flag from option 1 is its natural selector; not before.
- **Feeding scores or "agency is low" lines to Du in any form.** World answers, never leads.
- **The retrospective's other proposed fix, widening the regex from his corpus.** The regex layer sits at its default 92 percent of the time on prose that is metaphorical; widening it overfits a pretty curve (the plan's own warning). Not scoped.

## 4. Recommendation: repair in shadow

- **Wire it:** no. Nothing it produces can be wired as built, and every wiring is a founder decision the labs have not earned.
- **Archive now:** not yet. You said do not retire it; it costs about 4 GPU-minutes a week; option 1 targets a real exposure (chapters in his live identity block) and both options are cheap to test offline. Archive is the default if both labs fail.
- **Repair in shadow, minimally:** (1) **J-3345** (build, restart-gated, chapter call only; sequence with J-3009 which edits the same file): the log records coder model, endpoint, artifact id, text length and hash and a scoring version; the chapter coder is pinned to one Ramses hub of a different family and is skipped, never failed over to the hot lane. Rubric, exemplars and prompt text do not change (the plan froze them), so the registry text is unchanged. The two T4 calls are left to J-3317 and D-0672. (2) **J-3343** and **J-3344**, the two labs. If both pass, option 1 first (a measured exposure, no new input).
- **Plan home on success.** Option 1 belongs in `memory_knowledge` (the chapter repairs and the chapter recall design D-0637/D-0673) with its estate consumer under `identity_estate`; option 2 needs no plan (a doctor's gauge).

## 5. What needs a founder call

- **D-0679** (opened, plan `identity_estate`): may a chapter-narration flag ever change what the estate projection shows? Options: gauge only; shadow-log the would-be projection for 30 days then ask again (recommended); let the seeder skip flagged chapters. Not blocking: J-3343 and J-3344 run either way.
- No other call from this review. D-0672 (the T4 observer calls) is already open and unruled by me.

## 6. Archive-and-revive note (the stop condition)

**Trigger (a dated read, not an automatic switch): J-3346, not before 2026-12-05.** If both labs hit their stop criteria: move `core/narrative_quality.py` and its two call sites (`nodes/subconscious_node.py` 1947 to 1952, `core/chapters.py` 419) to `docs/staged/` with a note (restart-gated), retire P-0048 in the registry, keep `data/narrative_quality_log.jsonl` as the record. If one lab passed, J-3346 closes as superseded by that lab's build job.

**Revive only if** a different-family coder agrees with a second one on chapters or on his ordinary thoughts at 0.6 or better, or if a chapter re-telling path is built and needs a selector. Do not revive it as a scorer of T4 candidates.

## 7. Method and limits

- Read in full: `core/narrative_quality.py` (198 lines), `docs/completed/narrative_quality_plan.md` (the v2.0 header, sections 0 to 5), the chapters call site (`core/chapters.py` 395 to 420, and the lines it shares with the author call), `core/identity_estate.py` history block, `nodes/inner_monologue_node.py` around 1355 to 1366, F-3842, F-3843, F-3712 to F-3714, F-3718, F-3707, D-0549, D-0637, D-0641, D-0664 as read, the J-3141 review as the format sibling, and the J-3215 and J-3248 sections that mention the coder or chapters. I did NOT read the whole of `docs/reviews/t4_whole_picture_review_J-3252.md` (sections 0 to 2 only) or the plan's sections 5 onward.
- Measurements (scratchpad scripts named with this job id): `nq_stats_J-3142.py` (all 1,601 log lines), `nq_join_J-3142.py` (judge-log join), `nq_chapter_affect_J-3142.py` (chapter members and the mood series, sqlite mode=ro), and inline read-only queries for the estate and projection counts and the inner-thought weekly counts. I did not run any model.
- Not verified: that each logged projection block is what the prompt received (I rely on the live flag and the logged block); the mood series is global affect, not member content, so F-3934's second half is at best a reference that the coder fails, not a proof that it is wrong; the self-stance regex is crude (F-3936 is tagged inferred).
- **Correction to two job briefings.** The briefings of J-3343 and J-3344 name the dated read as "J-3355". It is **J-3346**. The briefing of J-3345 says that T4 calls ran on the hot lane in 74 of 90 weekly calls; that is as F-3842 reports it.

## 8. Index

- Findings: F-3933 (T4 ceiling, no link to the independent judge), F-3934 (chapters discriminate; transformation at chance against mood), F-3935 (chapters reach the live identity block; no re-narration actuator), F-3936 (supply for the agency curve, inferred), F-3937 (chapters are self-coded). Earlier: F-3842, F-3843.
- Decision opened: D-0679 (plan `identity_estate`). Related and untouched: D-0672, D-0664, D-0549, D-0637.
- Jobs spawned: J-3343 (lab, chapter-telling audit), J-3344 (lab, agency curve), J-3345 (build, shadow repair, restart-gated), J-3346 (dated read, not before 2026-12-05).
- Registry: P-0048 note updated.
