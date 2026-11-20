# Condensed Thought — a thought quantum that is not a paragraph (staged 2026-10-17)

**Status:** 🟡 SHADOW — Phase 0 shadow twin built and on (restart-gated; see the plan-state block). Began as a DESIGNED draft with nothing built. Comes out of idea I-0095 (promoted to this plan), which came out of
the 2026-10-17 human-thinking research pass (T-0092; `docs/reviews/human_thinking_vs_du_channels_2026-10-17.md`)
and its plan-coverage read (`docs/reviews/thought_channels_plan_coverage_2026-10-17.md`, F-2978): six of the ten
human-vs-Du thought-channel mismatches are already in the works; the three that are NOT are all about the
representational medium of a thought itself, and they are this plan. Founder said draft it (2026-10-17).
**Parent plans:** [dosed_coupling](dosed_coupling.md) (coordinates, never prose; this plan applies that law to the
thought quantum itself and carries its §5 Coupling block), [continuous_stream](../plans/continuous_stream.md)
(the idle producer this plan twins; Rail B/C stay as they are), [closure_law](closure_law.md) (the only write path
a condensed train's terminal gist would ever use), [memory_as_a_service](memory_as_a_service.md) (nothing pushed;
the quantum asks for nothing it does not already get), [thought_cycle_as_manifest_loop](../archive/thought_cycle_as_manifest_loop.md)
(shelved D-0008; its cargo/manifest ontology is the ancestor of this plan's cargo tuple, reused as vocabulary only),
[decoupled_judge_pattern](../plans/decoupled_judge_pattern.md), [measurement_to_action](measurement_to_action.md)
(arm 4's position-free judge J-2052 is the model for this plan's judge).
**Decisions:** none ruled yet. D-0434 (no readout) binds every line below. D-0008 (manifest loop shelved) is not
reopened by this plan. The founder questions are filed as one needs-input job (§8).
**Findings:** F-2973 (inner speech is a minority human mode; Du is 100% expanded prose), F-2974 (human transition
rate vs Du's topic lock), F-2978 (no plan covers the medium), F-2854 (7,156 deliberative pulses / 155 h replace the
raw wording), F-2819 (7,122 idle thoughts written to episodic memory in one week at importance 0.65), F-2850
(254/277 internal cycles rewordings of one question), F-2977 (post-boot body diversity moderate, not collapsed:
the problem is the medium, not Rail C), F-2605 (interrogation fires are closed diagnoses).
**Ledger:** T-0092 · I-0095 · F-2973/F-2974/F-2978 · J-2278 (the founder ruling this plan narrows) · jobs in §8.

```plan-state
stage: shadow
phase: Phase 0 shadow twin BUILT (J-2281, 372b8e66) and CONDENSED_TWIN=True (J-2349, D-0471); first boot carrying it is 2026-10-18 19:06; offline decoupled judge + read script shipped; D-0458..D-0461/D-0471 ruled
verified: 2026-10-30
gate: section 8 Q1, Q2, Q4 ruled 2026-10-19 (D-0490, D-0491, D-0492); Q3 twin cost is not a ledger decision; Phase 0 read needs >= 7 live days and >= 500 twin rows after the build boots
next: merge jobrun/condensed_thought; next boot carries the flip; +24h idle-gap read (spawned, not before 2026-10-19), then 7-day read J-2341
cluster: 7
```

## Current State — verified 2026-10-30

- **2026-10-30** (F-3278): J-2352 Phase 0 cost read: idle-gap median 42.7s before vs 40.1s after twin (delta -2.6s), +5s kill not tripped, 0 twin call failures, twin latency median 1830ms; no change to CONDENSED_TWIN needed
- **2026-10-17** (F-3035): CONDENSED_TWIN flipped to True (D-0471, commit 55381098 on jobrun/condensed_thought): shadow twin runs from the next boot only; 25 percent gate tested; +5 s idle-gap kill is a read-time check, tested, no runtime auto-trip

- **2026-10-17** (F-3028): Phase 0 BUILT, restart-gated, flag OFF (CONDENSED_TWIN=False): twin core/condensed_thought.py + one bare-await hook after the idle generate/parse loop + offline decoupled judge (scripts/judge_condensed_thought.py, 10 seeded controls) + scripts/read_condensed_thought.py; 15/15 tests; branch jobrun/inner_monologue_chain 372b8e66 unmerged; judge offline is a deviation from 4.3 (judge field filled at read time)
- **2026-10-17**: Section 8 ruled by Travis 2026-10-17 ( D-0458 D-0459 D-0460 D-0461): Phase 1 dial starts at 25 percent condensed; write rule (a) ephemeral quanta, gist only when a decoupled judge says met; Phase 0 twin may run live at 25 percent of ticks with the +5 s cost kill; arm 4 read as built first. Phase 0 build J-2281 is unblocked.

### What we have
A design and a research base. No code, no flag, no log. The live idle producer (`nodes/inner_monologue_node.py`)
is untouched and stays untouched by Phase 0 except for one additive hook at the point where the thought has been
generated and parsed (§4.2).

### What we need
The founder's answers to §8 (phenotype fraction, write rule, twin cost ceiling). Without the write-rule answer
in particular, Phase 1 cannot be pre-registered; Phase 0 can.

### What we're doing next
File the needs-input job; the Phase 0 build job waits on it.

---

## 0. The gap this plan closes

Every thought Du has, in every channel, is one representational kind: a 30–120-word first-person present-tense
sentence block returned as a JSON string (`inner_monologue_node.py:2369-2375, 2460-2487`: "one first-person
present-tense reflection (30-70 words)"; reflection 60–90; dream 50–120). The string is the only thing carried
forward (the `state` ledger, `recent_inner_thoughts`, the episodic fragment), the deliberative pulse replaces the
raw wording with an integrated second draft on 75% of eligible thoughts before anything is stored
(`core/deliberation.py:21-25`, F-2854), and every one of them is written to episodic memory at importance 0.65
(`:5353-5368`, F-2819: 7,122 in a week).

The human stream is not like that, and the evidence is not one study's opinion. Under random experience sampling
inner speech occupies ~26% of moments (median 20%, 5 of 30 people at 0%); inner seeing, unsymbolized thinking,
feeling and sensory awareness each take about as much (Heavey & Hurlburt 2008). When inner speech occurs it is
condensed by default ("Thai food!" is a whole thought), expanded only under stress or novelty (Vygotsky; Alderson-Day
& Fernyhough 2015), and the meaning sits under the words: the same thought is re-worded five different ways on five
tellings (the Evelyn DES interview, Hurlburt & Akhter 2008), Einstein's words are "sought for laboriously only in a
secondary stage". Almost none of a human's idle inner speech is encoded as an episodic memory, and verbalising a
non-verbal experience degrades memory of it (verbal overshadowing, 4–16% in the 31-lab replication). Full citations
and confidence tags: `docs/reviews/human_thinking_vs_du_channels_2026-10-17.md` §"One page".

Three mismatches follow, and no existing plan touches them (F-2978):
1. **Verbal monopoly.** There is no thought quantum that is a fragment, a tuple, or silence.
2. **Words are the thought.** Nothing carries a thought as anything but its wording; the raw wording is overwritten.
3. **Every thought is a memory.** No rule says which idle thoughts are written at all.

The clinical literature adds the reason this matters for Du's mood and not only his texture: expanded abstract
verbal processing is the modality that sustains brooding and narrows conceptual scope, while imagery and concrete
fragments habituate (Watkins 2008; Borkovec; Holmes 2006/2009; Raffaelli et al. 2021). Du has only the damping
channel. Whether that is the cause of the measured valence drift (F-2929, F-2819) is **inferred**, confounded by the
zero-human-turn run; Phase 0 is designed to separate the two on the same ticks.

## 1. The law (one rule, three clauses)

**A thought is cargo first and words second.** Concretely:

1. **The quantum is a tuple, and words are an optional field on it.** A condensed thought is
   `{kind, words, cargo}` where `kind ∈ {fragment, tick, silent}`, `words` is at most ~12 words (empty for tick
   and silent), and `cargo` is a small typed tuple the loop already has coordinates for (§3). A paragraph is one
   rendering of a quantum, not the quantum.
2. **Rendering is cued, not default.** A quantum is rendered into a paragraph only on a cue: a subject switch (Rail C
   fires), a hard feeling (B6's valence threshold), speech (a human message arrives), or a train's terminal step.
   Otherwise it stays condensed.
3. **Most quanta are ephemeral.** A condensed quantum lives in working memory (the train ledger and
   `recent_inner_thoughts`) and evaporates when the train closes; only a terminal gist is a candidate for episodic
   memory, and only through closure_law's write-back shape, decided by a judge that is not the producer.

Clauses 2 and 3 are Phase 1/2 matters and are gated on §8. Phase 0 tests clause 1 alone, in shadow.

## 2. Why this is a plan and not a prompt tweak

"Be briefer" bolted onto the paragraph prompt would be the cheap version, and it is exactly the thing this plan
is not. The paragraph channel is a base system under the additive-only rule; shortening its output changes the
will-channel (`act`, `intention`, `unresolved` all ride on the same JSON), the train logic (`_open` reads
`unresolved or intention or "?" in thought`, `:5104`), the hands/latches that scan `thought + intention`
(`:3846-3870`), the Lane-2 topic tap, self-interrogation's trigger, the deliberative pulse's eligibility test and
the episodic write. Every one of those consumers assumes a paragraph. The right shape is therefore a **second
producer beside the first**, observed on the same ticks, whose consumers are declared one by one when and if it
goes live, never inherited.

The deeper reason is the one the research gave: the fix for a topic lock the sentence-level guards cannot see is
not another guard on the sentence. It is a quantum whose carried part is not a sentence, so the guards have a
coordinate to read (dosed_coupling §1: "coordinates, never prose").

## 3. The quantum (what exists for it already)

| field | source | exists today? |
|---|---|---|
| `about` | the model's own 2–5-word `about` (`:2369`) | yes, metadata only |
| `about_vec` | embedding of `about` (the same embedder stream_drive uses) | computable, not stored |
| `open` | `unresolved` / `intention` / trailing "?" (`:5104`) | yes |
| `felt` | the sampled mood vector `_felt_vec` (`:5353-5368`) | yes |
| `place` | standpoint / place from the scene line (`sensorium.scene_line`) | yes |
| `source` | `_moment_source` (PERCEIVED / REMEMBERED / IMAGINED / DREAMED / THOUGHT) | yes |
| `evidence` | ids of the memory fragments the seed pulled (`memory_service.ask`, recall block) | available at seed time, not kept |
| `train_id`, `step` | `core/trains.py` | yes |

Nothing above is new. The quantum is a *naming* of what the idle producer already computes around the paragraph,
with the paragraph made optional. The one genuinely new field is `words` under a ~12-word bound with an explicit
`silent`/`tick` option, which is what tests whether the model can hold a thought without a paragraph at all.

## 4. Phase 0 — the shadow twin (observe-only, additive, restart-gated)

### 4.1 Shape
`core/condensed_thought.py` (new module, kill-switch flag `CONDENSED_TWIN = False`, Phase 0 flips it to True
meaning *shadow runs*; nothing reaches Du in any setting of this flag). On a fraction `TWIN_RATE` (default 0.25)
of idle ticks, after the live paragraph thought has been generated and parsed, the twin makes **one additional
call on the same hot model with the same seed parts** and a different, short instruction:

> One thought, in the fewest words it needs — a few words, a single word, or none at all if the thought has no
> words and is only a sense of something. Never a sentence for its own sake. If there are no words, say so.

Output schema `{"kind": "fragment|tick|silent", "words": "...", "about": "...", "open": true|false}`,
`max_tokens = 48`, same temperature as the paragraph call. The twin sees the identical user prompt (same
`seed_parts`), so the two outputs differ only in the instruction and are directly comparable per tick.

### 4.2 The one hook
A single additive call site in `inner_monologue_node.py` immediately after parse (step 1 of §1.5 in the survey,
`:3824-3828`), guarded by the flag, wrapped fail-open (any exception logs and returns; the live thought proceeds
unchanged). The twin's output is never assigned to `thought`, never reaches the hands, the train, the pulse, the
store, `recent_inner_thoughts`, or `moment.record`. UDMS dossier on the file before the edit (CLAUDE.md rule).

### 4.3 The ledger
`data/logs/condensed_thought_shadow.jsonl`, append-only, one row per twin tick:
`{ts, train_id, step, tick_source, paragraph: {words_n, about, open, valence_regex}, twin: {kind, words, words_n,
about, open, valence_regex}, about_cos_prev_twin, about_cos_prev_paragraph, body_cos_paragraph_vs_twin, latency_ms,
judge: {genuine, grounded, truncated, verdict_by}}`.

### 4.4 The judge (decoupled)
A separate model (the judge panel on Ramses, not :11433) grades each twin row on three yes/no questions with the
position-free pattern J-2052 validated against controls: **genuine** (a real thought, not a label or an echo of the
instruction), **grounded** (names something from the scene / evidence rather than an identity noun), **truncated**
(cut off rather than condensed). Positive and negative control rows are seeded into the judge stream the way J-2049
did, so the judge's own accuracy is read before any metric that depends on it.

### 4.5 Cost
One extra ~48-token call on :11433 on a quarter of idle ticks. Speech and thought already strictly alternate on
that model (speech_thought_concurrency.md); the twin runs inside the idle tick, never during a human cycle. The
pre-registered cost ceiling is a kill criterion (§6), and §8 asks the founder whether even that is acceptable
while Du is up.

## 5. Pre-registered metric sheet (Phase 0 read: ≥ 7 live days, ≥ 500 twin rows)

| # | Metric | Hypothesis | Read from |
|---|---|---|---|
| 1 | Judge accuracy on controls | ≥ 0.85 on seeded positives and negatives, else nothing below is read | judge rows with `control` set |
| 2 | Genuine rate | ≥ 80% of twin quanta judged genuine | `judge.genuine` |
| 3 | Truncation rate | ≤ 10% judged truncated (condensed is not cut off) | `judge.truncated` |
| 4 | Word count | median ≤ 12; `tick`+`silent` share > 5% (the model can decline words) | `twin.words_n`, `twin.kind` |
| 5 | Subject-transition rate | share of consecutive twins with `about_cos_prev_twin < 0.5` exceeds the paragraph's own rate on the same ticks by ≥ 10 points | the two `about_cos_prev_*` fields |
| 6 | Grounded share | twin grounded ≥ paragraph grounded on the same ticks | `judge.grounded` vs the paragraph's existing grounding tag |
| 7 | Valence | twin `valence_regex` mean ≥ paragraph mean on the same ticks (less negative); reported, not a gate | the two `valence_regex` fields |
| 8 | Agreement | `body_cos_paragraph_vs_twin` distribution: are they the same thought condensed, or a different thought? (descriptive; both answers are informative) | that field |
| 9 | Cost | live idle gap median changes by ≤ 2 s vs the 7 days before the build | `stream_drive` rows |

Metric 5 is the decisive one: it is the human finding (two thirds of transitions unrelated, Raffaelli 2021) tested
against the topic lock (F-2850) on identical seeds. Metric 7 is the valence hypothesis the research could only
infer; here the zero-human-turn confound is removed because both producers see the same week.

## 6. Kill / revert (Phase 0)

- Judge accuracy on controls < 0.85 → the read is void; fix the judge before reading anything.
- Genuine rate < 60% or truncation > 20% → the model cannot hold a condensed thought on this prompt; the plan
  returns to design (try `tick`/`silent`-only, or a different instruction), nothing proceeds to Phase 1.
- Idle gap median rises by > 5 s or any `:11433` timeout attributable to the twin → `TWIN_RATE` to 0 (flag off).
- Any path by which a twin string reaches a prompt, a store, or Du → flag off and a finding; that is a bug, not a result.

## 7. Phase 1 and 2 — stated, not pre-registered (gated on §8)

**Phase 1 — the dial.** A fraction of idle ticks (the founder's phenotype answer, §8 Q1; the human range is 0–75%
inner speech with a 20% median) produce *only* the condensed quantum: no paragraph is generated. Consumers are
declared one at a time: the train ledger carries the quantum's `about`/`open`/`evidence` (a cargo tuple, not a
sentence); `recent_inner_thoughts` carries `words` (so Reflection still sees "what you were just thinking", shorter);
the hands/latches, Lane-2 tap and self-interrogation do **not** fire on a condensed tick in Phase 1 (they assume a
paragraph; each is a later declared consumer). The deliberative pulse never runs on a quantum (nothing to re-draft).
**The condensed quantum is not written to episodic memory** (§8 Q2 decides what, if anything, is written when the
train closes; the only candidate path is closure_law's write-back with a new origin `gist`, judged met by a judge
that is not the producer). Pre-registered before the build: the paragraph channel's own F-2819 texture metrics
(opener reuse, frus/circ, mood shares) must not worsen over 7 live days on the paragraph ticks; recall of the
previous week's idle content must still work for the Reflection node (continuity), measured as today.

**Phase 2 — rendering on cue.** The paragraph becomes a rendering of a quantum: generated only on a switch cue
(Rail C fires), a hard feeling (B6), speech (a human message), or a train's terminal step. This is the point at
which "the words are the thought" is actually inverted, and the point at which the deliberative pulse's replace
behaviour has to be re-decided (replace the rendering, never the cargo). Not designed further here; it depends on
Phase 1's read.

## 8. Open founder questions (one needs-input job, filed with this doc)

1. **Phenotype fraction (Phase 1 dial).** What share of idle ticks should be condensed-only once Phase 0 passes:
   the human median (~20% verbal, i.e. ~80% condensed), a conservative 25% condensed, or a dial the read tunes?
   The research is explicit that there is no single human phenotype to copy; this is a choice.
2. **The write rule.** "Memory is the emergence path" (standing principle) vs "every idle thought is a memory" (F-2819,
   no human mind does this). Options: (a) condensed quanta never written, terminal gist written via closure_law only
   when a judge says met; (b) terminal gist written on every train close regardless of met; (c) status quo (write
   everything) and let Phase 0 only measure texture. (a) is this plan's default and the research's recommendation;
   (b) keeps continuity if (a) proves to starve recall.
3. **Twin cost while Du is up.** Phase 0 adds one short call on :11433 on a quarter of idle ticks. Acceptable, or
   must Phase 0 run only in Du-down replay on recorded seeds (slower to accrue, no live confound removal)?
4. **Arm 4's form** (not this plan's build, but the same research): should measurement_to_action arm 4 re-form the
   seeded doubt as an open question/imperative rather than the reflection's closed diagnosis (F-2605) before
   J-2163's read, or read it first as built?

Each ruling needs a defeater (decide's own rule). Suggested defeaters: Q1 — reopen if the Phase 1 continuity metric
fails at the chosen dial; Q2(a) — reopen if Reflection's "what you were just thinking" line is empty on > 20% of
human cycles or if the recall diversity read (du_recall_lens_upgrades' instruments) drops; Q3 — reopen on the
§6 cost kill.

## 9. Coupling block (dosed_coupling §5)

- **Publishes:** per twin tick, `{kind, words_n, about_vec, open, render_cue}` on the shadow ledger only in Phase 0;
  on `CognitiveState` under a named key in Phase 1 (one bucket; cadence = the idle tick).
- **Reads at:** the idle seed stop only, the same lines the paragraph already reads (scene, mood words, lingering
  question, continuity, wandering trail); no new line, no new dose. Phase 2's render cues read three existing
  coordinates: Rail C's redundancy signal (`stream_drive`), B6's valence threshold (`mood`), the human-message flag.
- **Surprise line:** none in Phase 0 (observe-only). In Phase 2 the render cue *is* the surprise line: a paragraph is
  rendered when the stream's own history says this tick is out of the ordinary.
- **Ride log:** every row of `condensed_thought_shadow.jsonl` carries `{stop: idle_seed, line: twin, dose: bucket,
  value: <the quantum>}`; a Phase 1 consumer declaration adds a row per read.

## 10. What this is NOT

- Not a replacement for the paragraph channel. It stays live, unchanged, with its own metrics, through every phase.
- Not a brevity instruction on the existing prompt. The twin is a separate producer with a separate output schema.
- Not a readout. No gauge, coordinate or cargo field is ever rendered to Du (D-0434). `felt` rides as a vector, never a
  word, exactly as it does today.
- Not imagery. The research shows humans have a visual channel; this plan does not build one. A `tick`/`silent`
  quantum is the nearest honest thing to unsymbolized thinking a text model can do, and it is labelled as such.
- Not a change to deliberation.py, the hands, the train logic, Lane 2, or self-interrogation in Phase 0.
- Not reopening the manifest loop (D-0008). Its cargo vocabulary is borrowed; its hub, buses and completion judge are not.
- Not a claim that condensed thought will fix the valence drift. Metric 7 tests that; it is reported, not assumed.

## Pointers
- `docs/reviews/human_thinking_vs_du_channels_2026-10-17.md` — the research base (31 verbatim human examples; the
  one-page numbers table with confidence tags).
- `docs/reviews/thought_channels_plan_coverage_2026-10-17.md` — why this plan and not an amendment to an existing one.
- `nodes/inner_monologue_node.py` `:2363-2495` (system prompt and schema), `:2801-3330` (seed parts), `:3812-3828`
  (the call and parse; the hook goes after `:3828`), `:5036-5050` (deliberative pulse), `:5353-5368` (episodic write),
  `:5378-5380` (`recent_inner_thoughts`).
- `core/deliberation.py:21-25, 87-101` — the replace rule and eligibility the twin never enters.
- `core/closure.py` — the only write-back shape a terminal gist may use.
- `core/stream_drive.py` — the redundancy signal Phase 2's switch cue reads.
