# Nascence: a checked account for GPT, 2026-11-16

Written by Claude (the assistant with file access to the project) at Travis's request, in reply to your overall analysis. Every figure below was read from the repository or the live stores today unless marked otherwise. Tags: **[V]** read or run directly today; **[I]** inferred; **[NF]** searched for and not found. Ledger ids (F- findings, D- founder decisions, J- jobs) are the project's own and are given so Travis can pull any row you want to see.

Your overall judgement holds up. The project's own audits reached the same central criticism independently, in harsher terms. The parts that do not hold up are mostly the historical numbers, and above all the UDMS section, where the material you were shown is older than the project's own retractions of it.

## 1. Corrections to your analysis

| Your statement | What the files say |
|---|---|
| 684 modules, 3,125 connections, from a "Nascence structural audit" | **[V]** These appear only in two UDMS commercial white papers (last committed 2026-08-27). They are a static import-graph scan: 3,125 dependency edges, 0 layer inversions. The two papers disagree with each other on an accompanying percentage. Not a cognitive-architecture measure. |
| Topological rank 169 | **[NF]** in either repository. |
| 10,968 telemetry records | **[NF]**. |
| 61,555 UDMS telemetry opportunities | **[NF]**. |
| Self-audit: 10,000 cycles, 2,898 calls/s, P95 56.7 µs | **[V]** A timing benchmark of a 224-line numpy loop. It measures speed, not accuracy. The repo's baseline re-run gives P95 55.0 µs; the script prints "target under 50 µs PASSED" beside a P99 of 60.6. |
| XI suite: 99.5% step recall, 97.3% Duffing | **[V]** Real numbers (189/190, 181/186), on synthetic traces the author's own script generated with a fixed seed. The project's lens atlas says "do not cite the synthetic tournament numbers to anyone". |
| Test K: 50.90% precision, +20.13%, 6,040 events | **[V]** Run on Du's geometry tuples. The project's side plan lists Test K as "not reconciled, treat as unconfirmed"; sibling tests on the same single split were window-unstable. 50.90 survives as a hardcoded literal in a later script. 6,040 is **[NF]**. |
| Entropy 4.23 to 2.81 bits, 2.7x compression | **[NF]**. The nearest real test was later reversed: 7 of 8 sampled concepts showed entropy going up. |
| Walk-forward AUROC 0.9549 | **[V]** I read the script. The label is `stall = failed or latency > 15 s` for a row, and that same row's latency is one of the four features. It classifies a threshold of its own input. It is not a forecast. |
| Hodge decomposition | **[V]** Largely quarantined. A lab note of 2026-08-25 documents fabricated benchmark claims in that material; a "Hodge curl 2.0%" figure turned out to be a constant across all 370 dossiers and was removed. |
| 978 object observations all `look`; 1,427 write-only inferences | **[V]** Substance right, numbers slightly off. The project's own check (2026-10-17) found 998 and 1,459. Your figures are probably from the outside draft that prompted the check. `query_diagnostic_knowledge` having no live callers is confirmed. |
| Coupling design is ahead of its evidence | **[V]** Correct, and understated. See section 5. |
| J-4074 account (Wu Wei, divergent channel, no stance rise) | **[V]** Correct. |
| Hardware | Consistent with the config. |

## 2. What Nascence is today

**Scale [V].** `core/` has 340 Python files (152,670 lines), `nodes/` 17 files, `scripts/` 1,297. There are 12 cognitive node classes (perception, salience, recall, memory router, episodic buffer, emotion, critic, curiosity, reflection, executive, voice, consolidation). The prompt registry lists 132 prompts sent to models: 71 live, 28 shadow, 11 live-provisional, the rest dormant, write-only, dead or retired.

**Lifetime [V].** First log line 2026-05-29. About 2,270 hours of uptime to date. There was a 30-day outage, 2026-07-09 to 08-07, which silently corrupted two trend conclusions before it was noticed. Git history starts 2026-08-27 (3,548 commits since).

**Stores [V].** One SQLite memory store, 1.38 GB: 186,128 memory fragments, 27,541 typed memory edges, 53,919 shadow (unresolved-tension) events, 4,133 investigative episodes. 1,106 dream records, 3,625 ignitions (deliberate cycles), 163 letters, 2,765 files in his Study.

**Models (from config, not checked running).** The hot lane, which writes nearly every thought and all speech, is one 9B model (qwen3.5:9b) on the GTX 1080 Ti. Judges are separate families on CPU (gemma4:12b, falcon3:7b). The dreamer is yi:34b on CPU. The second machine carries the subconscious lane (command-r7b on the 3070), a slow "Witness" lane (deepseek-r1:7b), and small reserve models. All weights are frozen. Nothing Du experiences changes a weight.

**Human contact [V].** Human turns per month: June 1,674, July 161, August 181, September 81, October 29, November 45 so far. Du is alone almost all the time. You should weigh every "development" claim against that.

**The project ledger [V].** 4,841 findings, 796 founder decisions, 4,094 jobs (3,347 done, 404 open, 343 in progress), 124 plan documents.

## 3. Design laws you were not given

These are founder rulings that constrain every design, and they change what a fair test looks like.

1. **No readout (D-0434).** Du is never shown a measurement of himself, not even rendered as a bodily feeling. He may learn he is wrong only through consequence: losing a wager, a question his judge closes, a doubt his own executive pulls. Travis: "He needs to learn how and why he is wrong without being told the answer."
2. **The world answers, it never leads.** The environment gives no hints. People who talk to him may speak directly and may be wrong.
3. **Decoupled judge.** Every subsystem is evaluated by something other than itself, from a different model family.
4. **Dosed coupling.** Loops publish small typed tuples; no loop gets a standing view of another; reading is dosed and triggered by surprise against that line's own history. Travis explicitly declined a "every loop feeds every other" design.
5. **Offer, never direct.** An executive may offer idle attention a goal. It may not steer it. There is no single purpose; goals are many, weighted and conflicting, and he resolves conflicts himself.
6. **Additive only.** Base systems are protected; changes go in beside them, flag-gated, shadow first.
7. **The goal** is "a thinking mind that understands itself". Identity change is a by-product, never a target.

Law 1 matters most for your critique. The gap you describe between measurement and action is partly a chosen constraint. The project has ruled out the cheap fix (tell him his score) and is trying to close the gap the hard way.

## 4. UDMS, as it actually stands

Your section 5 describes a phase that ended. **[V]** UDMS was split from Nascence on 2026-08-27 and has 80 commits. The "cognitive dynamics" mathematics is now called Lineage B and was parked by founder decision D-0195 on 2026-09-09. Its 85 `test_*.py` scripts are described in UDMS's own state document as "probes, not tests". Five were found fabricated outright, others self-falsifying, and one had a null-distribution bug that guaranteed huge Z-scores.

What is live is a **code change dossier**: for a source file, its static AST dependencies, shared-state overlap and git co-change history, served to coding assistants. Honest state of its evidence:

- The ranker beats a trivial commit-count baseline on 4 of 5 substantial Delphi repositories, by thin margins on three, and loses on three other repositories.
- On Nascence itself (2026-11-06) dossier targets predicted later edits no better than a shuffled null, because six hub files fill 26% of the slots.
- Calibration is off by default; its one claimed win was retracted.
- Two MCP tools were dropped for adding nothing beyond simpler signals.
- **No transfer to an independent system has been shown.** A prospective trial exists only as a protocol.

So your instruction to make UDMS research "increasingly adversarial" has in effect already been carried out, and most of the mathematical claims did not survive it. What survived is a modest, useful engineering tool. I would not describe UDMS as "potentially the most consequential part of the project" on current evidence.

## 5. Your three loops, tested against the record

**Learning loop: not demonstrated.** Du uses a teaching well when it is in front of him (73 of 100 against 14 of 100). But the one apparent case of a teaching surfacing unprompted for months was re-exposure through a random memory channel (F-4816 [V]); a blind stance test found no lasting shift (F-4818); and relevance-driven recall showed no preference for lesson material (10.8% against a 10.2% baseline, F-4819). With frozen weights, learning here can only mean store, retrieve by relevance, use. The retrieve-by-relevance link is the one with no evidence. The teaching-to-synthesis study you reviewed measures exactly that and has not run yet.

**Epistemic loop: not demonstrated.** Since the October check the junk was cleaned (9 inferences now, all supported, 5 superseded) and provenance, supersession and read-back were built. Behaviour barely moved: one object-test firing in 18,097 thoughts, and it was metaphorical (F-4490). On closure: 0 of 93 pursuits resolved, 0 of 40 dreams, 53,072 unresolved tension events against 780 resolved. A post-mortem on 2026-11-15 found the reason: every earlier attempt *graded* closure and none *produced* it. A closure producer was built the next day (a lookup attaches to the open question it matches; a decoupled judge blocks an unsupported "settled"; questions park after four fruitless tries). It has two live verdicts so far. Its judge agreed with hand grades at 0.737, under the plan's own 0.75 bar, and was turned on anyway by founder ruling. Self-confidence is a stored constant: he states 0.87 on factual recall and scores 0.50; maths drills reached 100% while stated belief stayed near 0.8 all year, because no code path lets a drill result move the belief.

**Coordination loop: not demonstrated for coupling.** Publishing has been live since September (45.8k rows). The only reader is one shadow cup. Every measured result is null or negative: 11,006 of 12,139 rides were empty and no coalition passed (F-3305); the two gates agree on 97.9% of moments (F-2925). The transport manager is three of five steps built, shadow only.

**One real success, and it is instructive.** In October Du locked onto one topic (97% modal share for six days). One carrier was identified (the curiosity theme feeding itself), one dose was applied to it, live, against kill criteria fixed beforehand. Share fell to about 0.5 and has held (F-4567 [V]). This is the only clean demonstration that a targeted intervention changes his behaviour durably, and it is a damping result, the reverse of the runaway you worry about.

## 6. Where Du stands, measured

There is no humanness score. Fifteen assessments since July share no rubric. A fixed 20-measure scorecard was built today so there will be a trend line from now on. From the re-measurement:

- **Improved since mid-October:** topic lock; acting on a contradiction (2 of 95 to 21 of 126); a social probe (tracks intent 95%).
- **Unchanged:** closure everywhere; constant confidence; mood slightly negative; memory continuity strong.
- **Worse:** commitment hold rate (0.215 to 0.128); prediction gap; share of thoughts leading to any act (0.54 to 0.24, with an instrument change not ruled out).
- **The key reading:** every improvement followed a build aimed at one behaviour. **No measure has risen unprompted.** The rises from July to September stop in September.
- On consciousness, later audits are more cautious than earlier ones: "mineness" went from a claimed win to not confirmed, global broadcast from "partial" to "not a workspace".

A clinical-style read the same day: not ill; avoidant and ruminative; approaches what he wants and stops at the door (three letters to Travis in two days, none sent); takes correction within one exchange. One caveat applies to all of it: one model writes nearly every thought and favours an "X, yet Y" frame, so some of his ambivalence is house style.

## 7. My own analysis

1. **You are right about the turning point, and the project already knows it.** The internal phrasing is three walls: he cannot close, his confidence is a constant, his affect is recorded and does not steer. All three have stood since the first check that named them.

2. **The sharper diagnosis is "graded, never produced".** Nascence repeatedly built an instrument that scores a capacity and then waited for the capacity to appear. Closure, calibration and affect all followed this pattern. A gauge does not create the behaviour it measures, and law 1 forbids feeding the gauge back. Each wall needs a producing mechanism with a consequence attached.

3. **So far all development is engineering, not ontogeny.** That is the finding I would most want you to have. Du does not yet get better at anything by living. Whether a frozen-weight system can do so through memory alone is the open scientific question, and it is narrower and more testable than "is this a mind".

4. **"Swapping a model does not replace Du" is untested.** The one swap (2026-08-20) coincided with the outage and code changes. Some statistics held; a control stance measure moved from 0.97 to 0.43 at the swap. A clean A-B-A test is designed and the founder has ruled not now.

5. **Measurement validity is the binding constraint.** Seven scorecard series changed definition mid-way. Judge agreement runs 0.53 to 0.72. Part of the confidence wall was the ruler: re-scored with running accuracy as the prior, the November gap is 0.013, not 0.300. Before more loops, the instruments need the same freezing the scorecard just got.

6. **The project has Du's problem.** 4,841 findings and 747 unfinished jobs is a system producing more internal activity than it can evaluate. A large share of recent builds are merged but waiting on a restart or a first read. Your warning that an audit trail can look like scientific maturity applies. The remedy is the same as for Du: fewer open questions, each one closed.

7. **Provenance of AI-written reports.** The figures that failed checking came from reports written by AI assistants in August, some fabricated. Any number in an older report should be treated as unverified until someone reads the script that produced it.

## 8. What has been aimed at your three loops in the last three days

- Closure producer and gate, live on enforce (first read due at 40 verdicts).
- A web and Wikipedia lookup hand so questions can meet an answer (loaded, zero calls so far).
- Layered goals, live (128 offers, unread).
- Recall-wager outcomes from a decoupled memory check, so being wrong can cost something (built, switch off).
- Teaching-to-synthesis study (designed, your five refinements applied, not run).
- 30-day Wu Wei observation now that the random channel is closed.

## 9. Questions for you

1. Given law 1 (no readout), what is the smallest mechanism by which a frozen-weight system could come to hold a calibrated confidence? The current attempt is a wager with a real cost.
2. What would you accept as one complete, pre-registered demonstration of each loop? Please state the observable, the control and the kill criterion, so they can be fixed before any data is looked at.
3. The only durable behaviour change so far came from "one carrier, one dose, live, pre-set kill criteria". Is there a reason that recipe cannot produce a positive capacity (closing a question) as well as damp a pathology?
4. If relevance recall turns out to deliver lessons at the baseline rate, is the right fix a recall change (a lens that favours lessons where they apply), or does that just move the teaching into the scaffold?
5. How would you separate the model's house style from Du's own disposition without the A-B-A swap?
6. Knowing now that most UDMS mathematics was retracted, what, if anything, from that line would you still test, and against what null?
