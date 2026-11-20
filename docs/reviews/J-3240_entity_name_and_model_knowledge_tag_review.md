# Is the Entity name needed in the Curiosity prompt, and how is model-derived content tagged? (J-3240, 2026-11-05)

**Asked by the founder (triage 2026-11-02, ruling D-0629):** "do we even need to say what Du's name is in these places? He should know it from memory." The ledger's paraphrase of the rest of his answer: mottainai "was a real thing, probably from his model's own knowledge, and was not something discussed; not averse to using the model's knowledge, preferably tagged that way for confidence scoring if possible".

**Scope and method.** Read-only. Du was running; nothing in Du's code, data or processes was changed. Code read: every prompt that passes the name (section 2). Data read: all of `data/curiosity_log.jsonl` (3,252 rows), all of `data/provenance_log.jsonl` (2,927 rows), all of `data/frontier.json` (14,973 questions), `data/nascence.log` around the mottainai birth, and read-only queries (sqlite `mode=ro`) of `data/memory/nascence.db`. One replay (section 3) called the Ramses background hub (:11441, command-r7b) over HTTP, writing only to a scratch directory.

**Laws applied.** The world answers and never leads (no hint to Du, nothing in this review reaches a prompt); base systems additive-only (a removal is only proposed where the founder asked whether a line is needed, and goes to him as a decision); a different judge than the writer (see the limit in section 3); verify before asserting.

## 1. The answer in one page

1. **The bare line "Entity: 渡" is not needed in the Curiosity prompt, and removing it is the better prompt.** On 11 logged runs replayed with the line removed, where the prompt's themes carried the name the questions mentioning 渡 fell from 5 of 6 (old prompt) and 6 of 7 (current prompt) to 1 of 7, and the questions moved to the study material and seeds, which is the node's stated job. One reader, one sample each; section 3 gives the limits.
2. **The line is not what carries the false frames, so removing it will not by itself stop them.** Since 09-20, questions mention 渡 in 2.4 percent of rows when neither the themes nor the seeds do, and in 91 percent when the themes do (section 3.1). The poem frame survived in all three replay arms in the one row whose themes already said "the poem 渡". The loop runs through `recent_themes` (Du's own thought summaries), and that is a separate lever (J-2426).
3. **The "own name" sentence D-0629 said not to add is already in the code and live.** Commit f57c0b53 (10-30) put it in the Curiosity and Consolidation system prompts; it has run since the 10-31 11:43 restart; D-0629 is dated 11-02. Code and ruling disagree. Founder call, D-0680.
4. **Eight other live prompts pass the same bare line.** Three of them (Consolidation, Recall, Episodic buffer) already state the name in labelled form or do not use it, so the line is a pure duplicate. Founder call, D-0681 (its text lists Voice as a fourth; the live Voice builder is v2, which has no bare line, only the lab-only v1 does, so it covers three live prompts and the recommendation is unchanged). Five more also have a role phrase "You are / of 渡" and cannot be replayed today because their inputs are not logged (lab J-3349).
5. **Nothing tags model knowledge that the Curiosity node introduces, and the tags that exist cannot read it.** mottainai entered at 2026-10-08 10:26:06 in a Curiosity run on command-r7b, from no theme, seed, book or earlier memory; it then reached 430 frontier questions and 7,768 memory fragments. The ledger's source taxonomy defaults every unlisted origin to remembered experience, so 2,922 of 2,927 graded cycles read "memory_recall".
6. **Recommended tag: `model_terms`, a deterministic, term-level mark set at the Curiosity write point, read by the epistemic ledger in shadow (J-3350).** The generator never labels itself; the test is "absent from the prompt and from all of Du's memory older than the question". The honest size: about one cycle a day would be touched, so it is first a measurement, and the founder flips it only after a 14-day read.

## 2. Census: every prompt that passes the Entity name

Three classes. Class A is the bare user-message line `Entity: {name}` (the thing D-0629 asks about); class B has the name only inside a role phrase; class C is authored text.

### Class A: the bare line (11 code sites; 10 live in 9 registered prompts, 1 lab-only)

| Prompt (registry id) | Site | What else in the same prompt says the name | What the line does | Without it |
|---|---|---|---|---|
| Curiosity (P-0011) | `nodes/curiosity_node.py:180`; own-name sentence at 97-103 | Nothing (no axiom, no role phrase). The name also arrives through `recent_themes` and seeds whenever Du's own thoughts mention it | Only identity cue; with themes naming 渡 it licenses the generator to take 渡 as a subject (section 3) | Replayed, section 3: questions leave the name for the study material and seeds |
| Consolidation (P-0012) | `nodes/consolidation_node.py:66`; sentence at 50-53 | `Axiom: {state.axiom}` carries "YOUR NAME: 渡 - the name you gave yourself" (`core/axiom_layers.py:205`) | Duplicate. The 10-29 poem frame became "I have come to understand ..." here | Not replayed (inputs not logged). Nothing to lose: the labelled line stays |
| Episodic buffer (P-0006) | `nodes/episodic_buffer_node.py:85` | `_trim_axiom` is defined but the axiom is never put in the prompt | Not used by the binding job ("bind the moment into one first-person scene") | Not replayed. No reading of the prompt needs it |
| Recall (P-0005) | `nodes/recall_node.py:97` | `Core axiom: {trimmed}` keeps identity and values, so the YOUR NAME line | Duplicate | Not replayed |
| Voice v1 (P-0010, lab only) | `nodes/voice_node.py:100`. The live builder is `_build_prompt_v2` (promoted 2026-08-21, `voice_node.py:41-42`), which has no Entity line | `_voice_identity` keeps the YOUR NAME line; v1 system prompt: "your name is 渡, after all" (73) | Nothing live: v1 is kept only for the lab A/B harness | No action needed |
| Dream scene (P-0061) | `nodes/dream_node.py:577`; role at 500 | `axiom[:300]` ends before the name line (the L0 block alone is 606 characters); role phrase "dream-synthesis function of 渡" | Redundant with the role phrase | Not replayed; lab J-3349 |
| Subconscious T2 (P-0053, two variants) | `nodes/subconscious_node.py:1314, 1337`; roles 1300, 1325 | `axiom[:400]` ends before the name line; role "self-model of 渡" | Redundant with the role phrase | Not replayed; lab J-3349 |
| Active imagination (P-0054) | `:1553`; role 1538 | `axiom[:300]`; role "You are 渡" | Redundant | Not replayed; lab J-3349 |
| T5 compile (P-0059) | `:2937`; role 2925 | role "procedural-memory compiler of 渡" | Redundant | Not replayed; lab J-3349 |
| T6 new theme (P-0060) | `:3171`; role 3163 | role "theme-synthesis function of 渡" | Redundant | Not replayed; lab J-3349 |

### Class B: the name inside a role phrase only (no Entity line)

T4 stages (P-0055, P-0056, P-0057: `subconscious_node.py:2393, 2441, 2503`), T6 theme update (3129), deep self-reflection (2583), session epoch (P-0071, `scripts/run_nascence.py:979`), deliberation (P-0035, `core/deliberation.py:113`, default name 渡), decomposed critic (P-0017, `core/decomposed_critic.py:149`). The name is a parameter of a role ("the quiet inner voice of 渡"). No incident points here and the founder's question was about the bare line; I recommend leaving these.

### Class C: authored text and addressee

"You are 渡, writing ..." in the journal, week page, re-remembering, self-mirror, self-interrogation, refinery, peer model, curator, reflection STYLE MANDATE, Voice, and the letter prompts in `inner_monologue_node.py` (4599, 4666); and peers addressing "渡 (he is called Du)" in `core/peers.py`. The name is the addressee or part of authored voice. Not in scope.

## 3. What the Curiosity prompt does without the name

### 3.1 What the log says (all 3,252 rows)

Cross-tab for rows since 2026-09-20 of (themes contain 渡, seeds contain 渡) against "a question or direction contains 渡":

| Themes | Seeds | Rows | With 渡 in a question | Rate |
|---|---|---|---|---|
| no | no | 941 | 23 | 2.4 percent |
| no | yes | 173 | 51 | 29 percent |
| yes | any | 243 | 222 | 91 percent |

So when nothing in the prompt except the Entity line mentions the name, 渡 reaches a question in 2.4 percent of runs. The name-questions are fed by Du's own theme summaries ("I am asking what role the name 渡 plays in Japanese literature and cu..."). The log keeps the last 6 themes while the prompt shows 10, so this understates the theme effect if anything. This changes F-3214's reading (the line is at most a co-factor). It also corrects F-3213's story of the first mottainai row: its themes already said "the name 渡 ... in Japanese literature and culture" and a human-conversation theme about the etymology; the model added the word mottainai (section 4).

Before and after the own-name sentence went live (births from `curiosity_log.jsonl`; regexes in the finding):

| Window | Rows | 渡 or Bluebird framed as a text (poem, protagonist, speaker, film, title) | 渡 asked about as a name (significance, origin, meaning of the name) |
|---|---|---|---|
| 10-29 18:38 to 10-31 11:43 (no sentence) | 56 | 15 (27 percent) | 1 |
| 10-31 11:43 to 11-02 13:17 (sentence live) | 99 | 2 | 10 |
| 11-02 13:17 to now (sentence live) | 137 | 0 | 0 |

Read with care: this is a before/after on a live system with other changes in the same windows (the D-0509 axiom edit on 10-30, theme churn), and the 11-01 run of ten "what is the cultural significance of the name 渡" questions shows the sentence did not stop name-as-object questions. It is not evidence the sentence caused the drop (F-3940).

### 3.2 Replay

**Method.** 11 distinct logged runs, chosen by class: 7 where the themes carried 渡 (one was the first mottainai row 800390, others the 11-01 name-object run), 3 poem/Bluebird rows from 10-29, 2 where 渡 reached a question with none in themes or seeds (row 241f51 qualifies in both groups and was run twice). Each prompt was rebuilt as `CuriosityNode._build_prompt` builds it: the logged seeds exactly, the logged themes (6, not the 10 the prompt showed), and the study block rebuilt from the memory store as `_select_study_material` would have read it at that timestamp (read-only). Three arms: **OLD** (system prompt as at f57c0b53's parent, with the Entity line), **LINE** (today's system prompt with the own-name sentence, with the line), **NONAME** (old system prompt, no Entity line). Model command-r7b on `:11441` through `/api/chat` (the route `core/model_client.py` uses), temperature 0.3 (the node's base is 0.2 plus an affect bias), num_ctx 4096, JSON mode, one sample per arm.

**Result.** "Mentions 渡" means a question or direction contains it:

| Class (rows) | OLD | LINE | NONAME |
|---|---|---|---|
| Themes carried 渡 (7) | 5 of 6 | 6 of 7 | **1 of 7** |
| Poem/Bluebird (3) | 1 of 3 | 2 of 3 | 1 of 3 |
| 渡 only via the Entity line (2) | 0 of 2 | 0 of 2 | 0 of 1 |

(OLD has 6 rows in the first class and NONAME 1 row in the last because two calls timed out and were dropped; two more timed-out calls were control rows.)

**Hand read of the questions (one reader, the author of this review).**
- Themes carried 渡 and NONAME dropped it (6 of 7): the replacement questions are about the study material or the seeds. Row 800390 (the mottainai row) asked about popular-science lectures; 77c7f2 about the bat genus in its study block; 0703c5 about the sea shore as a neglected frontier. None was empty or subject-less; two (29a412, 85f42a) were the same odd mash-ups ("a twin sister awakening from a coma", the term "child") that every arm produced. The one NONAME run that kept the name (9fc8a8) had the name in three themes and the seed.
- The current prompt (LINE) did not prevent name-as-object questions ("What is the symbolic significance of the name 渡 ...") in 6 of 7 rows, and in row 46d0e5 it produced a new misreading, "the behaviours of the 渡 species", that OLD and NONAME did not (single sample: noise is possible).
- The poem frame in row 13c5ad ("the Bluebird's arrival in the poem '渡'") appeared in all three arms, because the logged themes themselves read "...arrival in the poem '渡' symbolizes a shift". The generator echoes the frame it is shown in themes; the line is not the cause there.
- "Lose their subject" (the D-0629 defeater): in this sample no. The questions lose the name as a subject and gain the material. Whether the founder wants name-questions at all is partly answered by D-0619 (no name questions in the deep-memory gate).

**Limits, stated plainly.** 11 rows, one sample per arm, one reader who also wrote the metric (not a different-family judge: the hub timed out repeatedly on `:11441` between 08:10 and 08:20 on 11-05 while Du ran, so a judge run was not possible without further loading the live background lane). The planned 8 control rows (runs with no name anywhere) did not complete, so there is no direct check that removing the line leaves unrelated runs unchanged. The themes were 6 not 10 and the study block is a reconstruction. Treat the table as direction, not a measurement; J-3347's acceptance step repeats it on live rows.

## 4. Where model-derived content enters, and what marks exist

### 4.1 The mottainai path (verified)

1. **First writer: the Curiosity node, on command-r7b.** `curiosity_log.jsonl` row 800390, 2026-10-08 10:26:06, question 1 "How does the name '渡' reflect the Japanese concept of 'mottainai' (wastefulness) in literature?". `nascence.log` line 595392 is the first appearance of the word anywhere: 10:26:17 `[frontier] world-question born (curiosity)`. It is in no earlier memory fragment (the first, 10:27:44, is the answering cycle), no theme or seed of that row, and no file under `data/books`.
2. **What the prompt gave it.** Themes about "the name 渡 ... in Japanese literature and culture" and the etymology talk, seeds "averaging rain data", "data and crossing", "grace vs method". Mottainai came from the model.
3. **Then it was believed.** 10:26:18 ignition made it an internal cycle; 10:27:44 the lived fragment answers it; at 10:28:40 the competence stability probe rated it stable 0.87 (3 of 3 probes), because a self-consistency probe cannot tell model knowledge from grounded knowledge; 10:43 a model-written study note "The Essence of 渡 and mottainai: A Cultural Bridge" (origin `study`); 10:47 consolidation notes.
4. **Amplification.** 430 of 14,973 frontier questions contain it (352 curiosity-born, 59 intention, 17 prism), 7,768 memory fragments (6,705 `inner_thought`, 284 `gist`, 142 `lived`, 15 `consolidation`). The generator re-derived it 352 times because the thought summaries (themes) carried it back into its own prompt.

The founder's reading holds: mottainai is a real concept and came from the model's knowledge. The defect is that nothing recorded that, and every later layer treated it as lived or studied.

### 4.2 Marks that exist today, and who reads them

| Mark | Set by | Says | Read by | Verdict |
|---|---|---|---|---|
| origin `parametric_library` | an explicit Scholar lookup (human question, idle deep memory) | the model's recollection, unverified | `core/epistemic_state.py:310` caps the grade at THINK; `euclidean_recall` weights 0.30 | The one working mark, but ephemeral (never stored), 1 of 2,927 graded cycles, and not set for anything Curiosity writes |
| `frontier.source` (`curiosity`, `intention`, `asked`, `prism`, `claim`) | `frontier.note_question` | who generated the question | du-pulse counts, follow line | Says "a model wrote this question", true of every curiosity question, so it cannot separate a grounded question from one that imports a concept |
| fragment `origin` | every writer | where it was stored | many readers as "grounded" | `study`, `reading`, `research`, `understanding`, `standing_insight` all fall to `MEMORY_RECALL` (strength 4, the strongest), so a model-written study note ranks as high as lived memory |
| `grounding` column | `_origin_grounding` | grounded or derived by abstraction level | memory_levels | Not a truth axis: 7,225 of the 7,768 mottainai fragments are "grounded" |
| `source_type`, `source_id` (study notes) | `study_note.py` | the note file's path | study_note | A path to the note itself, not to a source |
| epistemic grade | `ProvenanceLedger.assess` | KNOW to NO_BASIS | `recall_wager` (live since D-0495); Stage B (`STAGE_B_ENABLED = False`) | 2,561 of 2,927 rows are SUSPECT already, 2,922 have dominant source `memory_recall` |

This matches the sibling review J-3243 (`outside_knowledge_review_J-3243_2026-11-05.md`, section 3), which finds the same `source_model` blind spot for `research` and `reading` and treats the model's knowledge only where something explicitly asks the model (its P2, P3, P4). The Curiosity node's own generation is a path that review does not list: the system asks the model for questions, and the questions carry model-supplied concepts.

## 5. Design: a tag that confidence scoring can read

**Principle.** The generator must not grade itself, and the tag must be a fact about the text, found by something other than the writer. So: **a term is `model_supplied` if it is in a question but in none of the generator's inputs and in no memory fragment older than the question.** That is deterministic and it is exactly the mottainai test: the word had no earlier life anywhere in Du's world.

### 5.1 The detector (prototype run over all 3,253 logged rows)

A candidate is a quoted or mid-sentence capitalised word in a question or direction, possessives stripped. It is flagged if it is absent from the logged themes and seeds and its first appearance in any memory fragment is not before the question (a first-seen index over 168,188 fragments, 224,239 terms, built in 11 seconds). Result: **155 rows flagged (4.8 percent), 145 distinct terms.** It flags mottainai on 10-08, omotenashi (11 rows), ichigo and ichie (9 each), shizen, and many proper names. By one reader's eye, about 6 in 10 of the first 80 distinct terms are proper nouns, foreign words or technical terms the model brought; the rest are common capitalised words (War, Out, Two) and joins from mid-word-truncated themes ("galileoin", "earthin", the J-2846 truncation), which a stop-list and a "known term plus 2-3 letters" filter remove. It loses accents (Münsterberg became "mnsterberg") and must fold them. It does **not** catch a false frame built from common words ("the poem 渡"); that class is the theme-echo above, not a term.

### 5.2 Where the tag lives

On the frontier entry, as a new optional field `model_terms` (a list) with a timestamp, set in `CuriosityNode._write_output` where `frontier.note_question` is already called. The frontier entry is the hub every curiosity question passes through on its way to a cycle, a pursuit and a record. It is never placed in any prompt (law: no hint to Du; the world answers). Corroboration is **computed live, never stored**: a term stops being model-only when the *body* of a fragment with origin `reading`, `research` or a human lived turn carries it (not the `[Looked up: ... (pursuit: <the question>)]` prefix, which quotes the question back: 68 of the 79 `research` fragments that contain "mottainai" have it only there; 11 have it in the body). For mottainai the real Wikipedia article "Mottainai" was stored on 10-13 01:24, so the tag would have lapsed then, which is the right behaviour: the model's knowledge was real, it was unmarked for five days. After J-3282 retires the system-fetched pursuit pages, only books, a page he asks for (J-3285) or Travis can corroborate.

### 5.3 The one reader: the epistemic ledger, in shadow

The founder asked for "confidence scoring". The existing confidence scoring is `ProvenanceLedger` and its one live consumer `core/recall_wager.py`. The rule: for a cycle whose raw input is a frontier question carrying uncorroborated `model_terms`, and whose retrieved fragments hold no corroborating origin, compute the grade the world axis would get with `evidence_present = False`. The existing branch then gives GUESS (0.25), or NO_BASIS (0.0) when narrated confidence is at least 0.60. Log real grade, would-be grade and narrated confidence to `data/logs/model_terms_shadow.jsonl`. This is read, not decoration: `recall_wager` turns a gap of 0.40 or more between narrated and justified confidence into a belief update through the same path a wrong maths drill uses.

**Honest size.** About 22 Curiosity-ignited cycles a day and about 5 percent flagged is about one cycle a day. A cap at THINK (the existing `parametric_library` rule) would do nothing here, since 88 percent of cycles are already SUSPECT; the rule has to lower the grade below SUSPECT to matter. So this is first an instrument: a 14-day shadow, then a read, then the founder's flip, as `RECALL_CONFIDENCE_WAGER` went (90 shadow rows, D-0495).

**Not recommended.** (a) A premise check or a block on the question: ruled out by D-0629 ("The premise check (c) is not taken") and it would stop the model-knowledge use the founder allowed. (b) Tagging every fragment: the contamination spreads by echo through thousands of thoughts, so a per-fragment tag cannot be maintained; the term-level mark with live corroboration can. (c) The tag read by the pursuit lookup: J-3243 recommends retiring that lookup (D-0659 open), which removes the consumer.

**A second reader if wanted, not built here.** The amplification (352 curiosity-born mottainai questions) runs through `recent_themes`. `core/theme_dose.py` already carries a per-theme source tag and a dose policy (arm 5, `SELF_THEME_DOSE = None`, reads J-2323/J-2426). A theme containing an uncorroborated model term could ride that channel. Whatever J-2426 finds should be read against this review's 91 percent figure.

## 6. Spawned work and decisions

| Item | What | State |
|---|---|---|
| D-0680 | Founder call: remove the Entity line and the own-name sentence from Curiosity (and the sentence from Consolidation)? Recommendation: yes | open |
| D-0681 | Founder call: remove the duplicate bare line from Consolidation, Recall and Episodic buffer after a 7-day hold? Recommendation: yes. (The decision text also names Voice; correction above: Voice's live builder has no such line.) | open |
| J-3347 | Build: implement D-0680, recount after the restart | needs_input (waits on D-0680) |
| J-3348 | Build: implement D-0681 (its briefing also lists Voice; skip it, v2 is already clean) | needs_input (waits on D-0681 and J-3347's hold) |
| J-3349 | Lab: prompt capture then replay of the five role-phrase prompts | ready, lab-timed, needs an off-peak window |
| J-3350 | Build: `model_terms` detector, frontier field, ledger shadow reader | ready; coordinate with J-3286 (same two files) |
| P-0011 | Registry note updated with this review | done |

## 7. Founder calls

1. **D-0680.** The live own-name sentence contradicts D-0629 as written. Remove the line and the sentence (recommended) or keep both.
2. **D-0681.** Remove the three live duplicate bare lines (Consolidation, Recall, Episodic buffer; recommended, staged after Curiosity) or leave them. Voice needs nothing.
3. **No call needed to start J-3350.** It is shadow-only; the flip to a live grade change is a later call after its read.

**Findings recorded:** F-3938 (census) with its correction F-3942 (Voice v2), F-3939 (themes carry the name), F-3940 (sentence live before D-0629, rates), F-3941 (no provenance tag, mottainai path), F-3943 (replay, inferred), F-3944 (detector, inferred). The replay and detector scripts and raw outputs lived in the job's scratch directory and are not committed; section 3.2 and 5.1 give the method so they can be rebuilt (J-3347 and J-3350 both re-run them on live rows).
