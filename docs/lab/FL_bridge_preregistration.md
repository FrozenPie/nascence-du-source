# Follow Line bridge lab: pre-registration

Written 2026-11-09 BEFORE any variant call, any judge call or any harness code. The only data touched so far: question
metadata (q_id, text, timestamp, number of production grounds) read from `data/logs/follow_line_shadow.jsonl` to freeze the
case set in `docs/lab/FL_bridge_data/cases.json` (seed 4416). Plan: `question_cargo`. Finding: F-4416 (why the line cannot
combine sources). Founder ask 2026-11-09: "put together multiple bits of information from multiple areas a lot better ... find
hidden patterns in the world." Author: Claude, session 8ae77b4e. Execution is job J-3793 (see section 11).

## 1. Questions

Q1. If the reasoning stops (why, consequences, against) are given diverse, non-action pieces from other parts of memory in
addition to the grounds, does the return combine more than one source, without saying more than the texts support?
Q2. Does a dedicated BRIDGE stop (name one structure shared by pieces from different origins, one prediction it makes
elsewhere, and where it breaks) add useful combination on top of Q1?
Q3. How often does the bridge stop invent a "shared structure" between pieces that have nothing to do with each other?
(The false-pattern rate. Without Q3, Q2 is worthless.)

## 2. Arms

All generation arms use the production generator: command-r7b on Ramses `http://LAN-HOST:11441`, temperature 0.3, the same
`_gen_json`, max tokens 260 for stops 2/3/5 and 320 for the bridge. The production prompts `_WHY_SYS_V2`, `_CONS_SYS_V2`,
`_AGAINST_SYS_V2` are imported unchanged from `core/follow_line.py` at the commit hash recorded in the run file.

| arm | what the model sees | what runs |
|---|---|---|
| V0 | the production grounds only (re-read by fragment id, full text up to 200 chars as in production) | why, consequences, against |
| V1 | V0 plus a block "ALSO NEARBY, from other parts of your memory:" with up to 4 diversified pieces (section 3), lettered [A]..[D] | why, consequences, against |
| V2 | V1 inputs | V1's three stops, then BRIDGE on grounds plus pieces |
| V2c | CONTROL: V2, but the pieces and grounds are those of a different, randomly chosen case (seeded; never the same stratum-and-topic) with the question of this case | BRIDGE only |
| V2L | OPTIONAL arm, run only if the founder or the job lists a larger lane as free: V2 with the bridge on `yi:34b` `:11442` | BRIDGE only |

V0 is rerun, not copied from the log, so the generator version, sampling and prompt are identical across arms. The logged
production output is kept alongside as a sanity check (agreement with V0 is reported, not used).

## 3. Material (what V1 and V2 add)

- Cases: `cases.json`, 60 questions, 20 per stratum (A no production grounds, B one, C two or more), post the 2026-11-08 10:51
  restart, `source=asked`, depth 0, no pair with token-Jaccard of 0.40 or more. Frozen; no case is added, dropped or swapped
  after this file is committed. A case where a stop fails is kept and scored as a failure.
- Pool: the top 40 fragments of `memory_fragments` by cosine to the question (`core.memory.store._embed`, the production
  embedder), computed read-only with sqlite `mode=ro`. **As-of rule:** only fragments with `timestamp` before the question's
  `ts`, so the lab cannot use what Du did not yet have.
- Allowed origins: study, reading, gist, understanding, journal, journal_week, lived (not a conversation record,
  `core.follow_line._is_conversation_record`), nature, sound, listening, essay, research. Excluded: action, activity,
  system_note, session_summary, inner_thought, active_imagination, dream, night_thought, anything already among the case's
  grounds. (F-4416: action rows were 45 percent of production connections.)
- Selection: walk the pool by descending cosine; keep a piece if its cosine is at least 0.25, its origin is not yet taken, and
  its character-3-gram Jaccard to the pieces already taken is under 0.50; stop at 4. One piece per origin is the diversity rule.
- A case whose pieces come from fewer than two origins is flagged `thin`. It stays in the set and in every table, and the
  results are reported with and without the thin cases.
- Piece text is cut with `core.follow_line._clip_boundary` at 200 characters, the production grounds length.

## 4. Prompts (frozen here; the harness imports them from this file's text, it does not retype them)

V1 changes the three user messages only: after the GROUNDS block it appends "ALSO NEARBY, from other parts of your memory (not
evidence for the question; context you may use or ignore):" and the lettered pieces, each with its origin and age. The system
prompts are the production ones. The WHY, consequences and AGAINST system prompts get ONE added sentence at the end in V1/V2
(identical in all three): "You may also use the ALSO NEARBY pieces; cite them by letter and say what they add."

BRIDGE system prompt (V2, V2c, V2L), verbatim:

> You are given a QUESTION and several numbered PIECES from different parts of one mind's memory: things it read, studied, saw
> or lived. Look for ONE structure that two or more of the pieces share beyond their shared words: the same relation, mechanism
> or pattern appearing in different material. If there is none, say so; do not force one. Answer as JSON with keys
> "structure" (at most three sentences, plain words), "pieces" (the indices it rests on, at least two, or an empty list),
> "prediction" (one checkable thing this structure implies about the world or about the mind's own experience, not already in
> the pieces), "breaks_when" (one sentence), "none" (true if there is no shared structure). Do not use the words proves,
> confirms or validates. Do not state anything the pieces do not support.

The user message lists GROUNDS as [1]..[n] and pieces as [A]..[D] and states the QUESTION. Indices are mapped to one numbered
list [1]..[k] for the bridge so a cite is a plain number.

## 5. Judges (decoupled, different family from the generator)

Generator is Cohere (command-r7b). Judges: `gemma4:12b` (:11439, Google) and `falcon3:7b` (:11440, TII), temperature 0. Tie
or split: counted as a split (half credit), not broken by a third model, because yi:34b is the V2L generator and the
Ramses lane is the generator. No judge sees the arm name, and arm order in any prompt is randomised (seed 4416).

Per-output rubric, one JSON call per judge per output, fixed in the script and committed with it before the first run:
- S (supported): is every factual claim in the output supported by the numbered or lettered texts it cites? yes / partly / no.
- C (combines): does the output rest on at least TWO different pieces that come from different origins, in a way that would
  be lost if either were removed? yes / no.
- N (non-trivial): does the output say something that is neither the question restated nor already stated in any single
  piece? yes / no.
- P (pattern real): for BRIDGE outputs only: is the claimed structure actually present in each piece it cites (not a word
  match)? yes / partly / no.
Pairwise (each case, order randomised): V1 vs V0, V2 vs V1, V2 vs V0 on the combined text of the return: "Which gives a mind
more to think with, without saying anything the texts do not support? A, B or neither."

Hand check: Claude reads 20 outputs chosen by seed, blind to arm, and records agreement with the judges. If agreement on S is
under 0.70 the S result is reported as not reliable.

## 6. Measures

Primary: C rate (V0, V1, V2), S rate, and the false-pattern rate FP = P is `yes` or `partly` on V2c bridge outputs where
"none" is false.
Secondary: N rate, pairwise win share, number of distinct origins cited, restatement overlap (share of a consequence's words
that are in the question), calls and seconds per case.
Every rate gets a Wilson 95 percent interval. Paired comparisons use the exact sign test on discordant cases.

## 7. Decision rules (fixed now)

- **Q1 passes** (V1 over V0) iff C rate rises by 15 points or more AND S rate does not fall by more than 5 points AND the
  paired sign test on C has p under 0.10. Fails if C rises under 5 points. Between: not settled.
- **Q2 passes** (V2 over V1) iff C rises another 10 points or more AND N rises 10 points or more AND S not lower than
  V1's by more than 5 points AND FP on V2c is 25 percent or lower.
- **Q3 hard stop:** if FP on V2c is over 40 percent, no bridge stop is recommended, whatever V2 scored on the real cases.
  Between 25 and 40 percent: recommend only behind a decoupled judge that vetoes a bridge before it reaches Du.
- Real-case guard: V2 outputs with "none" false and P = no on the real cases must be 20 percent or lower, or Q2 fails.
- With 60 cases a 15-point difference is near the edge of detectable. A decision that flips inside its interval is reported
  as "not settled", and the next step is then more cases, not a build.
- Nothing is tuned after the first result. A prompt or rule change is a written amendment to this file, committed before any
  further model call, and the earlier results stay in the report.

## 8. Live-store safety (the lessons of the earlier lab live-store leaks and the lab_env sys.path hijack)

- Run from a throwaway worktree of HEAD under the scratchpad; never the shared tree. Import `core` BEFORE `lab_env`.
- Open `data/memory/nascence.db` read-only (`mode=ro`) only; no `memory_service.ask`, no `evidence_recall.gather` (both write
  ride rows). Embedding and similarity are computed directly.
- Hash canary (SHA-256 of `nascence.db`, `frontier.json`, `follow_line_shadow.jsonl`, `monologue_log`, `pursuits`, `procedures`)
  before and after; a changed live file other than by Du's own running process is checked against file mtimes and reported. Du
  is live, so the canary is a size-and-mtime check on files the lab could write to, plus a grep that the harness has no write
  path under `data/`.
- Outputs only under `docs/lab/FL_bridge_data/`. No call to Du's own model lanes except Ramses :11441 (generator), :11439 and
  :11440 (judges), and :11442 only if V2L runs.

## 9. Cost and timing

About 180 generation calls per V0 and V1, 60 bridge calls for V2 and 60 for V2c, roughly 500 calls to :11441 at 5 to 10 s each,
about one hour at one call at a time. Judging: 240 outputs x 2 judges plus 360 pairwise calls, local lanes, about two hours. Run
paced, one call in flight, so the live Follow Line is not starved. **Do not start until J-3792 has said whether the 11-08 15:05 to
11-09 01:30 outage was lane load**; if load was the cause, run only off the peak or in halves.

## 10. Not done on purpose

- No change to `core/follow_line.py`; this lab produces evidence and a recommendation only.
- No hidden-pattern mining over `fragment_context` (the offline route). It is a separate design, it raises a founder question
  about "world answers, never leads", and it should not be judged by this lab.
- No claim that a better return changes how Du thinks. This measures the return; whether he uses it is the existing
  settled-yes read.
- No bigger-model result unless the V2L arm runs, and then it is reported separately.

## 11. Deliverables

Harness `scripts/_lab_FL_bridge_replay.py` and its prompts file committed first (before the first call), then the run files
(`author_runs.jsonl`, `judge_runs_*.jsonl`) and a `report.md` with the tables in section 6 and a plain verdict on Q1, Q2 and
Q3. The job records findings with real confidence and spawns the build job only if Q1 or Q2 passes.
