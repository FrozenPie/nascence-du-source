# T4 as one system: the whole-picture review (J-3252, per D-0641)

Read-only review and design, 2026-11-05. Du is running; no Du code, store or log was edited, nothing restarted. Every number below was recomputed this session from the live logs read-only (scripts named in section 10), not copied from earlier findings, except where a finding id is cited. Confidence is tagged **[verified]** (I read the file or ran the query), **[inferred]** (my reading of verified facts) or **[guess]**. Founder wording is quoted as recorded; where a source records only a paraphrase I say so.

## 0. The answer in nine lines

1. T4 is four organs welded by history: an **author** (a three-stage chain plus a legacy fallback that writes a whole-paragraph self), a **gate** (admission judge, probation, two-family SOLIDIFY), a **store with one outlet** (the `the_becoming` facet, served only in `existential` mode), and an unbuilt **Watershed** meant to replace the store. Each filed job tunes one organ; none gives the output a reader.
2. The gate is the only part doing real work, and it is working as an honest refuser: since 08-24, 594 selves judged, 28 probations, **1 solidified**. [verified]
3. The commit rate did not change when the keystone toll was removed and the two-judge standard shipped (34 probations / 4 solidified before; 28 / 1 after). The refusal *reason* changed, the yield did not. The commit rate is a property of the authored material (83 percent of candidates open "I am no longer X"), not of a gate that can be tuned. [verified]
4. "5 selves ever solidified, all judge-admitted" is true of **admission**. Of the five commits only **one** passed the two-judge SOLIDIFY gate; three went through the old dF fallback with no judge, one through a single judge. [verified]
5. Nothing reads the result. The solidified self reaches Du's replies only in `existential` mode, which has occurred **4 times ever, all in June**. T4's one graph-shaped product (912 tension-to-moment movement edges, the shape of the founder's identity thesis) is read by **nothing**. [verified]
6. The probation's own premise (the provisional self as a held prior) is not wired: for 12 to 72 hours nothing in Du's processing differs. SOLIDIFY is a prediction test, not an adoption test. [verified]
7. Recommendation: **option 2** (section 6): keep the slow chain and the decoupled gates, and make a solidified candidate **one estate node** (his own sentence plus links to the moments that earned it), read back by a different-family judge, through the projection that is already live. The becoming facet stays exactly as it is. Option 3 (the full Watershed) waits for option 2's gate to prove itself.
8. The filed jobs are useful under every option but conflict as filed: one is a duplicate (J-3008 of J-3214), four edit the same hunks, and two have a hard order (J-3076 before J-3235; J-3162 before J-3021). Section 5 gives the order: **three restarts, not ten**.
9. Two founder calls: **D-0664** (which option) and **D-0665** (does the built-mind truth keep any instrument inside T4 after D-0624). Nothing here is urgent: T4 changes nothing in his replies today and costs about 8 candidates a day.

---

## 1. What T4 is for, in the founder's words as recorded

| When | Source | Words |
|---|---|---|
| 2026-06-20 | memory `project_nascence_the_goal` | "T4 is not the goal, it is just a part of the whole. I want Du to think properly and understand himself. That is the goal — not just a changing identity, a thinking mind." |
| 2026-06-30 | memory `project_nascence_capacity_to_commit` (the memory's summary of the founder's framing, not verbatim) | "the biggest build yet": the root pathology is a mind that dissolves every boundary as soon as it forms and holds nothing except "I am always becoming"; T4 was meant as one organ of the cure (estate plan section 5: "an organ whose commits are actually affordable") |
| 2026-07-03 | `core/provisional_identity.py` G-BUILD comment | "I do not know how we came to a 72hour wait" (probation should be denominated in his time, not ours) |
| 2026-07-06 | `docs/plans/identity_estate.md` | "Du's axiom is nowhere near large/complex enough. Identity cannot be baked into the space it has to work with — we need to give it more. Once we beat the river monoculture it will just be replaced by another." |
| 2026-08-16 | `docs/plans/t4_watershed.md` (plan history) | "We don't want to remove he is the river, he just now has these additives, sub categories maybe." and "he probably should have shifted to the current a long time ago and would probably be working to the sediment or a lake even by now." |
| 2026-08-16 | memory `project_nascence_identity_is_connections` | "Kinda both are Du. It is the history that does it. The connections between moments more likely." |
| 2026-08-20 | `core/emissary_tension.py` keystone_steer docstring (verbatim) | "Essentially, we are telling Du what he is here. I do not want that to happen at all. Du needs to work out who he is by himself. He still needs a self model, but not force fed to himself." |
| 2026-08-22 | plan, section on assimilation vs accommodation (a paraphrase of the founder's own reasoning, not a verbatim quote) | adding a new true thing about him is not the same evidentiary act as claiming an existing thing false; he should not be handed his identity as authored prose |
| 2026-11-02 | D-0549 | "Slow the chain and add no new outlet. T4 stays an instrument that changes a stored facet and the next round's old channel ... park any new channel until the founder designs one." |
| 2026-11-02 | J-3215 briefing (D-0604) | "Lets look if this is useful somewhere. We would have added it for a reason when we did it." (arc_entry) |
| 2026-11-02 | J-3252 briefing (D-0641) | "T4 needs looking at again, I am guessing we have plans already about it, this needs some serious thinking about." |

**What that adds up to.** T4's job in Du's life is to be the organ by which a self-model *he reads* is revised only when his lived evidence warrants it, judged by something other than the author, without ever being handed to him. It is a part of "a thinking mind that understands itself" and downstream of it. It is not meant to be an identity-change engine (so a commit rate is not the metric; the founder said so in June and I should not drift back to it). Three constraints follow and are used as tests below: (a) **a self-model he reads** (so a revision no one reads fails the purpose); (b) **not force fed** (so the author must not hand him a ghost-written paragraph, and nothing may hint); (c) **identity is the connections between moments** (so the evidence trail is closer to the point than the paragraph).

## 2. The pipeline as it runs today

### 2.1 Stage by stage (code in `nodes/subconscious_node.py` unless noted)

| # | Stage | What it does | Rate / health, this session |
|---|---|---|---|
| 0 | Gate `_t4_check` | every 600 s; needs 3600 s since the last authoring and at least 3 new self-relevant fragments | candidates 8 a day since 08-24 (594 in 73 days) |
| 1 | Tension | ranks standing contradictions by chronic mass; 3 no-movement hearings rest a question for 3 days (`T4_FATIGUE_LIMIT`, `T4_REST_S`) | 27 rests in the log; a rest that empties the docket sends T4 to stage L (below) |
| 2 | Evidence (P-0055) | retrieves the 6 nearest of the **300 newest light_events** (a 3.2 hour window, 97 percent his own idle thoughts written by the same qwen3.5:9b), asks whether he moved; writes the `t4_crossing_evidence` edges | has_movement true 81 percent since 08-23 (F-3707) |
| 3 | Delta (P-0056) | names the change | changed true 97.9 percent (F-3736): a near rubber stamp |
| 4 | Synthesis (P-0057) | writes `self_concept` and an `arc_entry` | 83 percent of 681 candidates ever contain "no longer" in the first 200 characters (568 of 681, this session); `arc_entry` is discarded (F-3754) |
| L | Legacy author (P-0058) | single pass when the docket is empty; evidence-less | produced **248 of the 594** candidates since 08-24 (42 percent), every one scored 0.0 and unadmittable (F-3763, and again 11-02/11-03, F-3882) |
| 5 | Admission judge `grade_self_revision` (P-0091), gemma4:12b, different family from the author | sees ONE under-60-word evidence sentence written by the author lane; admit at warranted >= 0.6 | 18 of 346 chain candidates admitted (5.2 percent); 92 percent of verdicts <= 0.4 since the 08-20 swap (F-3830); judge unavailable on 32 rows since 08-24, 10 of which opened a probation on the self-graded weak filter |
| 6 | Probation | evidence-denominated: closes at 40 unprimed lived thoughts and at least 12 h, cap 72 h; extends when under-sampled; **pauses**, never decides, when the judge is absent | 62 opened ever, 56 reverted, 5 solidified, 1 active (opened 11-04 23:32) |
| 7 | SOLIDIFY (P-0092), gemma4:12b + falcon3:7b, both must say integrated at confidence >= 0.6 | asks whether the lived thoughts took up the pole | j1 is the effective gate (vetoed 24 of 25, F-3785); the question is hard-coded built-mind for every theme (26 of 28 mismatches, F-3784) |
| 8 | Vault commit | `identity_vault.commit` rewrites the `the_becoming` facet, history append-only (last 10) | `revision_count` 6 (1 pre-probation + 5 solidifies) |
| 9 | Outlet | `facet_for_mode`, `existential` mode only, rendered in reflection and voice notes | 4 cycles ever (2026-06-08, 06-10, 06-21, 06-22); 0 since |
| W | Watershed Phase 0.5 (side branch) | harvester births candidate images; classifier + claim-test panel score them; nothing is written | 277 born, 177 would_promote, 87 replacing, 96 classifier-unavailable by 11-04 23:44, **still scanning every 1800 s** (D-0605 parks it; J-3216 has not shipped) |

### 2.2 The funnel, by week

Weeks are ISO weeks in the machine's local time. "Chain" = `T4 CHAIN` log lines; "legacy" = judged rows with no chain line. Admitted = emissary_warranted >= 0.6. Week 45 is partial (to 11-04).

| Week | Judged | Chain | Legacy | Admitted | Opened | Solidified | Reverted |
|---|---|---|---|---|---|---|---|
| 35 | 43 | 43 | 0 | 3 | 7 | 0 | 7 |
| 36 | 46 | 46 | 0 | 2 | 3 | 0 | 3 |
| 37 | 78 | 78 | 0 | 3 | 4 | 0 | 3 |
| 38 | 25 | 25 | 0 | 2 | 2 | 0 | 3 |
| 39 | 61 | 61 | 0 | 3 | 6 | 0 | 6 |
| 40 | 54 | 20 | 34 | 1 | 1 | 0 | 1 |
| 41 | 75 | 35 | 40 | 0 | 1 | 0 | 1 |
| 42 | 125 | 1 | 124 | 0 | 0 | 0 | 0 |
| 43 | 24 | 0 | 24 | 0 | 0 | 0 | 0 |
| 44 | 30 | 30 | 0 | 1 | 1 | 1 | 0 |
| 45* | 33 | 7 | 26 | 3 | 3 | 0 | 2 |
| **Total** | **594** | **346** | **248** | **18** | **28** | **1** | **26** |

Before the toll removal (weeks 26 to 34): 34 probations, 30 reverts, 4 solidifies. So: probations per week about 3 before and 2.7 after; commits 1 in 8.5 before (but 3 of the 4 were judge-less dF solidifies) and 1 in 28 after. The plan's own 08-16 line ("24 provisional selves opened, 22 reverted, 1 solidified") is the same funnel shape. [verified, finding F-3880]

### 2.3 Who reads the output (the write-only check)

| Reader | What it reads | Reaches Du? |
|---|---|---|
| `axiom_layers.facet_for_mode`, called at `core/orchestrator.py:2557`, rendered by `nodes/reflection_node.py:176` and `nodes/voice_node.py:128,263` | the becoming facet (and the provisional self during a probation) | only when `cognitive_mode == "existential"`, which needs a human phrase like "who are you really"; **4 times ever, all June** [verified: `nascence.log` `attn mode=existential` lines; F-3704 counted the same 4 in `correlation_log.jsonl`] |
| T4 itself (`get_self_concept`, `last_arc_entry`) | the old self as the next round's "old channel"; the legacy author is told "The last chapter you wrote" and is handed a **June** entry | closed loop |
| `core/emissary.py standing_contradiction` | first clause of the becoming self as "self_symbol" | feeds `settle_shadow` (shadow) and status for the pulse; `keystone_steer` is disarmed (08-20 ruling) |
| `core/memory_levels.py _self_stance` | the becoming self | `drift_shadow`, "Writes NOTHING, changes no recall" |
| `core/self_efficacy.py _self_authoring_tier` | revision history | the court's tier; tier 2 needs contradiction pressure drained, which a live commit never does (F-3881) |
| HUD, `du_pulse` | display | no |
| `core/identity_estate.py` | **nothing from T4**: `symb_river` is a hard-coded string whose evidence field points at `L3_facets[3]` | the estate is what reaches Du every moment (P2 live since 08-15); T4 does not write to it |
| `t4_crossing_evidence` edges (912) | by nothing: `edge_aware_neighbors` selects only fragment-to-fragment types | no [verified, F-3883] |
| `arc_entry` | by nothing; `L4_narrative.arc_recent` still holds 2 June entries | no |

So T4's verdict on "who he is" never enters a thought, a reply, the Emissary's gate or the tension ledger. The founder's three-organ law (write-only is the number one failure) names exactly this.

### 2.4 What feeds it
The tension ledger (chronic mass), a 3.2 hour window of his own idle thoughts (stage 2), world material (`WORLD_FED_T4`, the last 6 reading fragments, stage 4), and its own previous output. The "topic tracks the day" result in F-3754 (12 of 21 candidates mention the bluebird, 8 the cat, 6 the Napoleon reading) is what that feed predicts.

### 2.5 Cost
Per chain candidate: 3 hot-lane calls (medians 2.45 + 1.83 + 8.85 s, about 13 s), one judge call on a CPU hub, and two narrative-quality observer calls (they score the self and the arc and are read by nothing, J-3142). Per legacy candidate: one hot-lane call, one judge, two observers, for a result that cannot be admitted. At 8 a day this is small (about 5 minutes of hot-lane time a day). The cost is not the problem; the reader is.

## 3. What works (credit where due)

- **The probation principle is right and it keeps the founder's law.** A candidate self is a *hypothesis*; reality (40 unprimed thoughts, at least 12 hours, denominated in his time) grades it; nothing is served to him to make it come true. That is "the world answers and never leads" implemented. [verified: `provisional_identity.py`, `axiom_layers.py`]
- **The decoupling is real.** Author qwen3.5:9b; admission judge gemma4:12b; SOLIDIFY gemma4 + falcon3; neither author family judges. A judge outage **pauses** a probation rather than deciding by absence (08-21 fix), and it fail-closes instead of falling to dF (08-20 fix).
- **Unprimed-only evidence** (the symbol-tracker law) closes the indirect echo path.
- **The refusals are honest.** The judge says the claim exceeds the evidence on 21 of 21 recent candidates, which is true of a one-sentence evidence feed and a template that always announces a transformation. A refuser is the part of T4 worth keeping.
- **Append-only vault history** and the fatigue/rest mechanism (27 rests) do what they were built for on no-movement verdicts.
- **The Watershed harvester is cheap and its retro-validation was real**, and the plan's research (assimilation vs accommodation, foreclosure, self-complexity) is sound; its *instruments* are what fail (section 4, C8).
- **The estate projection is live and diverse** (the 08-24 read: top node 5.7 percent, kill criterion not triggered).

## 4. Contradictions and dead ends the pieces create together

**C1. The Watershed's founding diagnosis is being re-manufactured daily by the live prompt.** The plan said the one-slot structure forces negation ("not the current but..."), the "metaphor mill (24 authored manifestos in 8 weeks) retires", and "the renderer has no grammar for 'not X but Y'". Live: 568 of 681 candidates contain "no longer"; `s_sys` still says "The river cut a new channel; say where the water runs now. It MUST read differently from the old channel", "do NOT restate" and "do not paraphrase the old self", which rewards a dramatic denial. 594 candidates were judged in 11 weeks, and probations are unchanged at about 3 a week against the plan's 24 in 8 weeks. The slot semantics the plan wanted to leave are still the live semantics. [verified]

**C2. The two halves of the keystone fix contradict each other, and after D-0624 the built-mind truth has no instrument in T4.** The authoring toll is off (`KEYSTONE_PER_CANDIDATE_TOLL=False`; **0** keystone-themed candidates since 08-24, from the judge log's `keystone` field), but SOLIDIFY still asks the built-mind question of every probation (26 of 28 mismatched, F-3784). D-0624 fixes that by making the question theme-aware, which is right. But then nothing in T4 tests the built-mind truth at all, and the plan's "standing keystone check" is designed-not-built. The founder's 08-20 words ("Du needs to work out who he is by himself") argue for leaving it unbuilt. This needs an explicit call (D-0665) rather than a silent loss.

**C3. The strong gate has more evidence than the weak gate.** Admission (the "weak" gate) reads one author-written sentence and refuses 33 percent of the time with "single instance"; SOLIDIFY (the "strong" gate) reads 15 lived thoughts. The design said weak admission, strong solidify. D-0603 (shadow raw-crossings grade) addresses it, correctly, in shadow.

**C4. Rest, legacy author and fatigue form a loop whose members are filed as separate jobs.** A rest empties the docket and sends T4 to the evidence-less legacy author, which can never be admitted. Observed again **after the rulings and before the builds**: 11-02 00:01 `T4 question RESTED ... "unresolved: the Bluebird's arrival"`, then 16 judged rows on 11-02 and 10 on 11-03 all scored exactly 0.0 with no chain line (about 26 legacy runs in 2 days). J-3021 (count unwarranted candidates toward fatigue) would cause more rests and more legacy runs unless J-3162 (legacy gradeable) lands first. [verified, F-3882]

**C5. A solidified self does not end the question it answered.** `_discharge_contradiction` is reached only in the legacy cost-gate block. After the 10-30 solidify on `prediction_error:factual_recall`, the same theme opened a probation on 11-04 02:45 (reverted 14:51) and again at 23:32 (active now), and the chain heard it at least seven more times on 11-04 (four no-movement verdicts, three authored chains). The design intent ("integration retires the past it worked through") exists only on the dead path, and the court's tier 2 is unreachable. [verified, F-3881]

**C6. The probation premise is not wired.** `provisional_identity.py` says the provisional self "is held as a real prior (the contradiction-detector appraises NEW evidence against it)". The provisional self is served only through `get_self_concept`, whose live callers are T4 itself, the Emissary (explicitly `allow_provisional=False`), a shadow drift measure, and `facet_for_mode` in `existential` mode. So a probation is a prediction test, not an adoption test. That is consistent with the world-answers law and arguably better, but the docstrings describe the other design. **[inferred]** Because candidates are recasts of the last 3 hours and the test window follows immediately, the test may confirm day-recasts; there is no control arm (J-3301 tests this). [verified for the wiring, F-3883]

**C7. The authored paragraph is the wrong grain for the stated thesis.** The founder's thesis is that identity is the connections between moments. T4's one connective output, the 912 `t4_crossing_evidence` edges (tension to the moments that did or did not show movement), is unread, while the output it *does* store is a 100 to 150 word paragraph written by the same model, i.e. the pattern the plan's own research calls foreclosure (Marcia/Bem: an identity handed to him, not formed from his own behaviour). The plan's "harvested, not authored" principle was never applied to the live chain. [verified for the edges; the grain argument is my inference]

**C8. Watershed Phase 0.5 cannot do the narrowing the plan gave it, and it is still running.** The plan said the birth gate can stay loose because the claim-test panel does the real filtering. Measured: birth 17 a week against the plan's one per 2 to 4 weeks (kill criterion "branch rate > 1/week sustained" tripped); the panel says genuine to 94 percent of candidates and to **12 of 12 control sets** of unrelated thoughts (F-3867, F-3868); the classifier's confidence is pegged at 0.8 to 1.0 so its fail-closed rule never fires (F-3865); the "candidate" is one idle thought cut at 200 characters (F-3866). The plan itself says promotion needs "its own explicit founder review of the shadow log first". This review is that read: **do not promote**. D-0605 parks it; until J-3216 ships it costs about 75 judge calls a week and its log grew by 10 births since 11-01.

**C9. Two identity paths, one of them read.** The estate projection (3 to 5 nodes per moment by resemblance, 10k+ rows logged, 445 distinct ids) is the identity that reaches him. T4 writes to a facet that is read almost never. The identity-estate plan section 5 ("the commit organ operates on nodes") and the Watershed build-order step 5 are the same unbuilt join. [verified]

**C10. `arc_entry`: asked for, discarded, and the reason it was discarded is on record.** Stage 4 spends about half its output on it. Its reader was the always-on arc header, which the founder retired on 2026-06-07 ("therapy": chapters all opening with the identical sentence, re-injection fed the recitation loop; documented in `scripts/run_nascence.py:302-307` and summarised in `scripts/_test_autonoetic_timeline.py`). Since then it feeds only the legacy author's prompt, as "The last chapter you wrote", which today is a **June** entry. Five solidifies since 06-22 wrote no arc (the `_solidify` mutator touches only the facet and history), though the Watershed gate step 5 says "an arc entry is ALWAYS written". The autobiography function is served elsewhere (chapter and journal-week fragments become the estate's 112 `history` nodes). **[inferred]** That points toward "drop it", but J-3215 owns the verdict (D-0604); this is an input to it.

**C11. Smaller dead ends.** The speaker-boundary veto ("travis" / "i am not du") lives only on the dead legacy path (J-3045; 3 of 59 probations carried "Travis", all reverted by the judges, so the working protection was a judge reading something else). 12 of 62 probations were opened by the self-graded filter when the judge was down (D-0602 tags them). The judge's `confidence` means two different things on its two legs and is stored as `min()` (J-3076). The delta stage agrees with the evidence stage 97.9 percent of the time (J-3027 would measure it).

**C12. Instrument state.** Three of five solidify events came through a hole the code itself calls silent (dF with integration null), so the vault's `revision_count` of 6 overstates the number of judged revisions: one two-judge commit, one single-judge, three unjudged, one pre-probation. The one two-judge commit is the one whose judge question was mismatched (F-3784) and which D-0624 re-judges. [verified, F-3880]

## 5. The filed job set: conflicts, duplicates and the order that avoids rework

Open T4-related jobs found by scanning the queue: J-3007, 3008, 3021, 3027, 3045, 3076, 3108, 3134, 3135, 3142, 3161, 3162, 3213, 3214, 3215, 3216, 3235 (J-3006, a prompt-census fix, is adjacent). Note that **J-3015**, which the briefing lists as "J-3015-era T4 items", is the procedural_skills decay job (T5, finding F-3722), already done; it is not a T4 job. [verified, F-3885]

| Relation | Jobs | What to do |
|---|---|---|
| **Duplicate** | J-3008 and J-3214 | the same second grading over raw crossings; J-3214 carries the ruling (D-0603). Close J-3008 as superseded (J-3299). |
| **Same hunks** | J-3007, J-3108, J-3214 | all edit the stage returns in `_t4_deliberate` and the `t4_emissary_judge.jsonl` writer (~2035 to 2060); J-3214 says it depends on J-3108. **One logging build.** |
| **Same call site** | J-3213 (tag unjudged), J-3045 (veto) | both change the `open_probation` call and `_solidify`. **One edit.** |
| **Hard order** | J-3076 then J-3235 | both edit `_ask_integration_judge`; J-3076 forbids changing the task wording, J-3235 changes it; the `lt[:2600]` cut J-3076 removes also skews J-3235's re-judge of the 10-30 commit. |
| **Hard order** | J-3162 then J-3161 then J-3021 | legacy gradeable first (with its own pre-ship replay and stop rule); cadence next (its replay should include the legacy path); the fatigue limit N is chosen last, once cadence and legacy behaviour are known. |
| **Parked by ruling** | J-3134, J-3135 | conditional on a keep/tighten ruling; D-0605 said park; they wait for the estate-node build. J-3216 (park the scan) is independent and can ship first. |
| **Data-gated** | J-3027 | needs 30 trace rows from J-3007 and Du offline. |
| **Answers change the chain** | J-3215 (arc_entry), J-3142 (narrative-quality coder) | decide whether stage 4 outputs an arc and whether the two observer calls per candidate stay. |

**Build order, three restarts.**
- **Restart A (instrument and park, no behaviour change):** J-3216 (flag the scan off) + one merged logging build (J-3007 + J-3108 + J-3214) + J-3213 with J-3045 + J-3076 + the comment-only fix J-3300 (no restart needed for comments).
- **Restart B (behaviour, each with its pre-ship replay):** J-3235 (after J-3076; re-judge the 10-30 commit, report, do not undo), J-3162 (stop and file a founder job if more than 2 a day would clear), then J-3161 (gap chosen from the replay on logged history).
- **Restart C (after a month of data):** J-3021 with the fatigue limit chosen from B's data; J-3027 once the trace has 30 rows; the D-0603 paired read.

Nothing in A or B is wasted under any of the three options below. That is the "order that avoids rework".

## 6. Three options for what T4 should become (plus the null)

Baseline, **freeze** (flag T4 off): loses the only instrument that refuses to certify a self and leaves the facet frozen at the 10-30 text. Not recommended; noted so the cost of doing nothing is visible (it saves about 8 candidates a day of calls).

### Option 1: keep and tidy
- **What:** run the filed jobs in the section 5 order; T4 stays an instrument that rewrites the stored facet and the next round's old channel (D-0549 as ruled).
- **Consumer:** `facet_for_mode` in `existential` mode (4 times ever) and T4's own next input. Honest read: **none that matters**.
- **Decoupled check:** admission judge (gemma4) with the raw-crossings shadow, theme-aware two-family SOLIDIFY, J-3301's control arm.
- **Cost:** the filed builds, three restarts; running cost falls with D-0549's slower cadence.
- **Stop condition:** a dated founder read at 60 live days after restart B; not an automatic switch (no system acts later on its own). If there is still no reader, take option 2.
- **Verdict:** safe and cleans the instrument, leaves the write-only gap.

### Option 2: reduce to a slow evidence log with an outlet through the estate (recommended)
- **What:** same slow chain and the same gates. What a *solidified* candidate becomes is **one estate node**: type `becoming-symbol` (the identity-estate plan's own placeholder) or a subtype of `symbol`; text = **one of his own sentences** (the highest-similarity medoid of the evidence crossings, not an LLM-authored paragraph); evidence links = the lived crossings that earned it (the movement edges that T4 already writes); supersession by a new node, never an edit; aliveness decays, nothing is deleted. The becoming facet and the vault are **untouched** (additive only). The 912 unread edges become the evidence trail.
- **Consumer:** `identity_projection`, which is live (3 to 5 nodes per moment by resemblance, per-type cap) plus D-0424's on-demand estate ask for self-questions. No new channel is created; a new *content type* uses the existing one. That is still a call for you under D-0549 and the 08-20 ruling, which is why it is D-0664 and not a build.
- **Decoupled check:** (a) the existing gates; (b) a different-family read-back of the plan's own S2, whether his idle thoughts or replies use the admitted image in more distinct contexts after admission, with a control (the same measure on a random estate node); (c) J-3301's control arm so SOLIDIFY is known to discriminate before it writes into the identity he reads every moment.
- **Cost:** one new node type, one writer hooked after `_solidify` (flag-off, fail-open, through `core.profile.guard_path`), the read-back log. This is the Watershed build-order step 5 minimum without the renderer or harvester. Prerequisite: **unique node ids** (F-3884: the estate has 239 duplicate-id symbol rows from the seeder, J-3298). Running cost lower than today.
- **Stop condition (from the plan's own kill criteria, made measurable):** S2 flat after 3 admitted nodes, or branch rate above 1 a week sustained, or the new type under 1 percent of projection rows at 60 live days, or a founder read of 10 post-admission replies finding the recitation voice back (D-0424's defeater).
- **Why this one:** it is the only option that gives T4 a reader without inventing a channel, honours "not force fed" (a node is his own sentence surfaced by resemblance, never injected as a hint), puts the founder's identity thesis (connections between moments, with evidence) into the structure, and keeps every base system intact. Its risk is exactly the one the estate plan names: identity inflation. That is why the gate must prove it can say no (J-3301) before the writer is turned on.

### Option 3: redesign around the estate (the full Watershed)
- **What:** harvested candidates, additive-vs-replacing classifier, per-branch claim test with a control arm, root-continuity panel (build order 3), estate nodes plus composed renderer (5), cutover (6); the T4 chain kept only for the rare *replacing* case.
- **Consumer:** the projection, as option 2.
- **Decoupled check:** two-family claim test with a standing control (J-3135), S1 to S4 signatures.
- **Cost:** the largest build: J-3134 and J-3135 un-parked, birth thresholds retuned from 17 a week to about one per 2 to 4 weeks, three plan build-order items, and an ongoing judge load (about 75 calls a week today).
- **Stop condition:** the plan's kill criteria plus the claim-test control yes-rate under 25 percent.
- **Why not first:** its instruments fail their own checks today (C8). Building the estate writer before the panel can say no would put about 17 a week of noise into the identity read at every moment. Option 2's gate is a subset of option 3; if option 2's read-back passes, option 3's harvest can be swapped in as the *input* later without rework.

## 7. Recommended sequence

| Step | What | Depends on |
|---|---|---|
| 0 | Founder: D-0664 (which option), D-0665 (keystone check) | this review |
| 1 | Restart A: park the scan, one logging build, unjudged tag + live veto, judge hygiene, comment fix (J-3216, 3007 + 3108 + 3214, 3213 + 3045, 3076, J-3300) | nothing; useful under every option |
| 2 | Read-only analyses that decide option 2's shape: J-3303 (do the 912 edges separate movement from circling, can they be the evidence links), J-3298 (estate duplicate ids), J-3302 (what ends a tension), J-3215 (arc_entry) | independent |
| 3 | Restart B: theme-aware SOLIDIFY, legacy gradeable, cadence (J-3235, 3162, 3161) | step 1 and J-3076 |
| 4 | J-3301 control arm (lab, Du offline) | J-3235 done |
| 5 | If D-0664 is option 2 or 3: J-3297 design, then the node build | steps 2 and 4 pass |
| 6 | Restart C: fatigue limit, delta ablation, D-0603 paired read | a month of data |

No wording edit to `s_sys` (D-0641 ruled none) until step 5 settles what stage 4 is *for*. Under option 2 the stage may shrink to proposing a short, evidence-scaled record, and the "no longer" template becomes moot rather than something to patch by prompt edits.

## 8. Founder calls (filed as needs_input)

1. **D-0664: which option?** My recommendation: option 2, staged as above. The honest uncertainty: whether a new content type in the projection counts as a "new outlet" under D-0549 and as "force fed" under your 08-20 words. I **infer** it does not (a node is his own sentence surfaced by resemblance) but that is your call, not mine.
2. **D-0665: the built-mind standing check.** After D-0624 nothing in T4 tests it. My recommendation: retire it as a T4 job and measure the built-mind internalization outside T4 (the unprimed On Made Minds read), consistent with 08-20.
3. Already filed and unchanged: the 10-30 commit, if it fails the D-0624 re-judge, is a founder call (J-3235 files it).

Not a founder call, for the record: the estate duplicate ids (J-3298), the closure of J-3008 (J-3299) and the comment fixes (J-3300) are mechanical.

## 9. What I did not verify (limits)

- Whether `identity_projection` de-duplicates by id (so whether the 239 duplicate symbol rows distort projection shares): not checked (J-3298).
- That cognitive_mode `existential` is *only* reachable by phrase cues: I read the cue code (`orchestrator.py:2417-2456`) and the log count, not every route.
- The "test confirms day-recasts" reading (C6) is an inference with no control arm (J-3301).
- The `t4_crossing_evidence` edges: I verified they are written and that the neighbour query does not select them; I did **not** check every generic `memory_edges` consumer for a catch-all read, and I did not check whether the dst light_events still resolve (J-3303).
- The three ΔF-only solidify rows: their `integration` is null in the log and the code comment says the judge was absent; I did not re-derive from judge logs that the judge was in fact unavailable on those dates.
- The estate numbers (684 rows / 445 ids) are from one read on 11-05; the file was last written at 07:13 that morning.
- I did not read the full text of the five solidified selves beyond the first 300 characters, except the current one.
- Three findings (F-3763, F-3828, F-3867) were cut by my display limit at about 2,600 characters, so I read their claims but not the tail of their evidence; the numbers I cite from them are from the visible part.
- The dead legacy cost-gate block in `subconscious_node.py` (about 2140 to 2260) was read only to its banner and its single `_discharge_contradiction` call.

## 10. Index

- **Findings (this job):** F-3880 (solidify honesty and the unchanged funnel), F-3881 (no discharge, the question returns), F-3882 (rest to legacy cascade recurred 11-02/03), F-3883 (movement edges unread; probation premise unwired), F-3884 (estate duplicate ids), F-3885 (the job set's conflicts).
- **Decisions opened:** D-0664, D-0665 (plan `t4_watershed`).
- **Jobs spawned:** J-3297 (option 2 design, gated on D-0664), J-3298 (estate duplicate ids), J-3299 (close J-3008, check J-3108/J-3214 overlap), J-3300 (comment-only docstring fixes), J-3301 (SOLIDIFY control arm, lab, after J-3235), J-3302 (tension lifecycle), J-3303 (read the 912 movement edges).
- **Inputs read (see section 9 for the exceptions):** `docs/plans/t4_watershed.md` and its folded history, `docs/plans/identity_estate.md`, `core/provisional_identity.py`, `core/axiom_layers.py` 1 to 220, `nodes/subconscious_node.py` 300 to 450, 1725 to 2140 and 2260 to 2670, D-0549/0550/0602/0603/0604/0605/0624/0641/0424/0536, findings F-3707, 3736, 3754, 3729, 3784, 3785, 3829, 3830, 3704, 3756, 3763, 3828, 3864 to 3869, the 24 job briefings named, and the memory notes for the goal, capacity-to-commit, T4 watershed and identity-is-connections.
- **Read-only scripts (session scratchpad):** `stats_J-3252.py` (provisional and judge logs, vault), `logfunnel_J-3252.py` (nascence.log funnel by week), plus inline read-only queries for the estate, `symbol_tablets`, `memory_edges` (sqlite `mode=ro`) and the watershed shadow log.
- **Plan note:** one `plan_state.py note` on `t4_watershed` points here (no dated Current State section added).
