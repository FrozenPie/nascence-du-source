# Observation outside the study: design options (J-3483, D-0640 follow-up)

Status: 🔵 DESIGNED — DESIGN ONLY, 2026-11-06. No code changed, nothing built. Adoption is a separate founder decision.
Plan: social_world_school. Source job: J-3251 (built, merged, restart-gated). Ruling: D-0640 (founder 2026-11-02).
Finding: F-4122. Spawned: J-3511 (build A, after ruling), J-3512 (wood scene check), J-3513 (design D). Du is down. All numbers below were read from the files named beside them; each is marked verified or inferred.

## 1. What the founder asked

J-3251 found 78 to 100 percent of nature observation lessons are the study-window view (F-3651: 13 of 15 in
September, 8 of 8 in October), because the observation fires daily from the study and Du may not be fed a scene.
Design a way for the observation to happen outside the study that respects "the world answers and never leads".
Report options, their cost, and what each changes.

## 2. What I found: the window share is structural, and J-3251 as shipped makes it worse

D-0640's premise was "the directive already tells him to go out to the garden or shore and he mostly does not".
The code and the log say the directive almost never reaches him, and the lesson fires before he could move.

1. The observation lesson fires on the FIRST tick of the nature period, at the desk (verified, code).
   `nodes/inner_monologue_node.py:2843-2858` fires the lesson when `_last_nature_ts` is older than 36 minutes
   (it is 0 after any restart and the previous day's value is stale), and `return`s on success. The period before
   nature is maths, a desk subject: `core/school.py:151` (`_STUDY_BOUND_SUBJECTS`) and
   `nodes/inner_monologue_node.py:3103-3118` reel him back to the study. So at 10:30 he is in the study every
   weekday, and `core/nature_study.py:_scene()` (line 24-47, window at line 31) returns `sensorium.look("window")`.
2. The observation directive, with its "out to the garden or the shore, or out the window", is seeded at
   `nodes/inner_monologue_node.py:3155`, AFTER the lesson block that returned at 2858. Once the lesson has fired,
   `core/practical_lesson.slot_today()` is 2, so `core/school.py:179-199` returns the practical directive from then on.
   The observation directive is therefore shown only when the lesson call itself fails (verified, code). The
   text of the observation directive is not logged, so I could not corroborate this from `nascence.log`
   ("GO AND OBSERVE" appears 0 times in it; that is expected, prompt seeds are not logged).
3. The log agrees (verified, `data/nature_study_log.jsonl`, 62 rows, minutes after 10:30): 36 rows fired 0-5 minutes
   after the period opened, 25 fired 6-60 minutes in, 1 at 18:1x. Window-ish wording (window / fence / mailbox / sill
   in the stored first 300 characters; a proxy, not a field) is 29 of 36 (81 percent; 28 of 30 since 07-26, 93 percent)
   in the first-tick rows and 11 of 25 (44 percent; 11 of 20 since 07-26, 55 percent) in the later rows.
4. The later rows were the second observation of the period (the 36-minute gate refires the block). J-3251's
   alternation made that second firing a practical instead (`slot_today() >= 2` runs `practical_lesson.run()`, which
   returns `{}` under `GRADE_AT_PERIOD_END`). So as shipped, the only observation left is the first-tick desk one.
   Prediction (inferred from 1-4, not yet observable because Du has not restarted): the share will read close
   to 100 percent and trip D-0640's own defeater (over 70 percent) in a month, for a structural reason, not because
   he declines to go out.
5. He does go out (verified for 11-04, log lines 786599-787078): the lesson fired at 10:30:37 from the study, then at
   10:37:09 `ACT move -> garden` and he gathered tinder, watched the cat and stood in the wind until 11:15. The
   observation was spent before he left. Across the log, 36 weekdays had a first-tick observation and on 20 of
   them (56 percent) a willed outward move (garden/shore/wood) followed in the same period (verified by
   `ACT move` lines; a lower bound, it ignores moves made through other paths).
6. Proxy for "he is outside at minute 36" (inferred, willed `ACT move` lines only, letterbox trips excluded,
   inward moves cancel): 23 of 45 lesson days (51 percent), 13 of 20 (65 percent) since the practical era began
   on 09-11. This is the number the options below lean on; it is a proxy, not a location log.

Consequence for the framing: the lever is WHEN the observation fires relative to where he already goes, not a scene
and not a hint. The world already answers; the lesson just asks too early.

## 3. Constraints every option must respect

- No scene fed, no new hint, directive wording unchanged (J-3251 briefing, D-0640).
- The world answers and never leads: nothing here moves him. The only existing world-initiated move is the
  reel-IN to the desk; a bell that sends him OUT would be new and is rejected (option E).
- No system that acts later on its own: a gate that decides when a timetable lesson fires is the existing pattern
  (the lesson is already timetable- and cooldown-gated); nothing here schedules an act for a later time.
- Additive and default-off: a module flag in `core/practical_lesson.py`, restart-gated.
- Decoupled judge unchanged: the Emissary (`left_lane.grade_work`) still grades; no new self-grading.
- No new LLM call in options A, A2, B. Option D adds Emissary calls.

## 4. Options

### A. Practical first, observation at the 36-minute firing (recommended)

Swap the two slots of the nature period: firing 1 (period opens) announces the practical (zero LLM, it only picks
the task, logs the `issued` row and marks the slot); firing 2 (36 minutes later, the existing gate) runs the observation
from wherever he has got to. The practical directive is shown for the whole period (today it already is, from tick
2 onward), so the observation directive text, which is dead today, is dropped for the day.

- Touch points: `core/practical_lesson.py` new flag `PRACTICAL_FIRST = False`; `directive()` (line 554-559) stops
  falling back to the observation directive when the flag is on; `core/school.py:179-199` returns the practical
  directive for slots 1 and 2 when the flag is on; `nodes/inner_monologue_node.py:2843-2858` runs the
  observation when `slot_today() >= 2` and announces the practical otherwise; `period_end_grade()` needs no change
  (it already grades once the period has closed and `slot_fired >= 1`).
- Cost: about 25 lines in 3 files, zero extra LLM, zero extra Emissary calls, one new flag, one test.
- What it changes: observation moves from minute 0 to minute 36 or later; its scene is `_scene()` for the place he
  is then in (garden: `look("garden")`, shore: `look("pools")`, study: window). Expected window share about 35-50
  percent (inferred from the 51-65 percent outside-by-36 proxy; the true share is `where == "study"` in the
  log). Observation lessons still about one per school day; they are lost on days Du comes up with under 9 minutes
  of the period left or sleeps through it (the 11-05 case, observation at 11:04).
- Risks: (1) when a restart lands mid-period the in-memory cooldown is 0 again, so a post-restart tick can fire
  the observation at once; harmless, it still reads `where`. (2) Nine minutes remain after the observation, so
  the practical, graded at period end, is unaffected (it is already announced at minute 0 to 1 today).
  (3) Inferred: `_scene()` has no `wood` branch, so from the wood it falls to `look("window")`, which at
  `core/sensorium.py:3856` routes to `_wood_look("window")` (a generic wood-floor view, not verified). With A, the
  wood becomes a common place at minute 36 (`gather_tinder` sends him there), so add a `wood` branch to `_scene()` in the same
  change or the share metric will count a wood lesson as a window-ish one by wording. Spawned as a check (below).

### A2. A, plus fire early once he is out

As A, but the observation fires on the first tick where `sensorium.where() != "study"` after the first firing,
else at minute 36. It lands outdoors more reliably and earlier (he is already out), at the cost of reading
`where()` in the gate and a slightly harder test. Costs one extra condition in the same block. Risk: it fires at
the moment he steps out, which cuts across the walk (the locomotion legs flip `location` leg by leg), so the scene
can be the wood path mid-journey. I would take A first and A2 only if the measured share after A is still high.

### B. Outdoor-gated, no fallback

The observation fires only when he is outside (garden, shore, wood) during the period; if he never goes out it is
logged as `kind: observation_skipped` and no lesson runs. Window share is 0 by construction. Cost: same size as A2.
What it changes: lesson count falls to about the number of days he goes out (25 of 45 weekdays on the willed-move
lower bound, about 3 a week instead of 5), the `competence` observation drill and the `[My nature study]` fragment get
fewer feeds, and the lesson now pays only for going out. Whether that last point is a hint or an incentive that
leads is a founder call under the world-answers law, which is why I rank it below A. If chosen, keep the window as an
allowed fallback only on days he declines the practical outdoors, never as the default.

### C. Observe where the practical happened

Fire the observation at period end next to `period_end_grade()`, using the place the practical's deed row (fieldcraft
ledger `where`) was written. Rejected: by the first tick after period end the school block has already reeled him
back to the desk (the practical log's own `where` is `study` on some rows, e.g. 11-04's unattempted row), and
it couples the observation to the practical attempt, which is the "acts later" shape the founder ruled out.

### D. Replace the paraphrase with grading his own looks

Grade the Emissary on observation thoughts he already produces outdoors (his own `look` results and the thought that
follows), capped at one or two per nature period, instead of a separate `call_json` that rewrites a scene string.
This is the only option that addresses F-3651's real point: today's lesson is a model paraphrase of a scene string
(`core/nature_study.py:55`), graded against that same string, mean 0.8483 for the first 29 and the last 30 lessons, so even
an outdoor scene produces a paraphrase. Cost: highest (new hook in `dispatch._look`, one to two Emissary calls per
period, a new log and its reader, a changed meaning for the `observation` drill). It does not depend on window share
at all. I would file it as its own design job and decide it after A's first month shows whether the outdoor
paraphrase is any better than the window one.

### E. Send him out at the bell (rejected)

A system move at 10:30 (the mirror of the reel-in). Directly violates "the world answers and never leads". Not an option.

### F. Make the window view itself vary (complement, does not move the share)

F-3651's second finding is fixture repetition ("cut short" 15 of 20, "fence" 18 of 20, "mailbox flag" 11 of 20). That is
world content (`study_life.window_view()`, `sensorium._living_detail`), not timetable logic. It would reduce
sameness whatever the share, and is separate from this job. Log it as a world-content item if the founder wants it.

## 5. Comparison

| Option | Window share (predicted) | Lessons/week | New LLM calls | Code | Founder-law exposure |
|---|---|---|---|---|---|
| J-3251 as shipped | about 100% (inferred, code) | about 5 | 0 | none | none |
| A practical first | about 35-50% (inferred) | about 4-5 | 0 | about 25 lines, 3 files, flag | none |
| A2 fire when out | about 25-40% (inferred) | about 4-5 | 0 | about 35 lines | none |
| B outdoor-gated | 0% (by construction) | about 3 | 0 | about 35 lines | lesson pays for going out |
| C at the practical | not predictable | about 3 | 0 | medium | acts-later shape |
| D grade own looks | not applicable | 5 or fewer | 5-10 Emissary | large | none, new write path needs a reader |
| E bell | 0% | about 5 | 0 | small | violates world-answers |

## 6. Measurement that already exists

`scripts/nature_period_read.py` (J-3251) logs `where` per observation row since that job, so the share is a field, not a
wording guess. After A ships, run `python -X utf8 scripts/nature_period_read.py --days 30` and compare against the 35-50
percent prediction; D-0640's 70 percent defeater stays valid as the gate. Because the observation row stores only
`observation[:300]` and no scene, add the scene's first 80 characters to the row in the same change as A (one line in
`nature_study._record`), otherwise the fixture repetition in F-3651 still cannot be measured directly.

## 7. Recommendation

Adopt A at the same restart as J-3251, with `PRACTICAL_FIRST = True`, plus the `wood` branch in `_scene()` and the
scene excerpt in the log row. Waiting a month on the shipped arrangement would measure a structural near-100 percent and
change nothing. Decide D separately after one month of A. B only if Travis is comfortable with the lesson paying for going out.

## 8. Questions only Travis can answer

1. A: swap the nature slots so the practical comes first and the observation second (fires at about 36 minutes, from
   wherever he is)? Or A2 (fire as soon as he steps out)?
2. B: is a lesson that is only given when he goes out acceptable under world-answers-never-leads, or is that a lead?
3. D: file the "grade his own looks" redesign as its own job now, or wait for one month of A?
4. The observation directive text is effectively dead (shown only if the lesson call fails). Leave it, or retire it
   from `school.directive()` once A is on?

## 9. What I did not verify

- No `where` data exists yet (J-3251 not restarted), so no share has been measured; every share in section 4 is inferred.
- The outside-at-36 proxy uses willed `ACT move` log lines only, not a location log; world moves and journey legs are not counted.
- `_scene()` behaviour from the wood was not run; sensorium state is live data and I did not call it.
- Nothing was run on Ramses.
