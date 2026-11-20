# Curiosity end to end, as of 2026-11-14 (J-3988)

Read-only. Every number is from data/frontier.json, data/logs/follow_line_shadow.jsonl and
data/curiosity_worth_log.jsonl read on 2026-11-14 (Du live). Builds on F-4643, F-4672 (J-3987), F-4682 (J-4000, shadow
mech_progress) and the D-0631 review chain (D-0659..D-0662).

## The short version

1. The old curiosity pursuit loop (pick a question, look it up, attach a finding, count progress or a stall) is dead
   and was retired on purpose on 2026-11-05 (J-3282, D-0659). Nothing in the live tree calls `record_pursuit` or
   `pending_pursuit`; the only surviving `attach_finding` caller is the Follow Line, and it attaches an echo of his own
   memory.
2. A different mechanism now does the work a pursuit used to do: **the Follow Line** (`core/follow_line.py`, live since
   10-28, D-0494). It takes a question or claim, follows it through his own memory, has a decoupled judge grade it,
   delivers it to an idle thought, and closes it by his own word (yes, partly, no, unsaid). It is the only live stage
   that moves a question toward an end.
3. The plan docs and the progress code still describe the old loop. `core/curiosity_progress.py` scores a question by
   pursuit counters nothing writes, so learning progress is 0.0 for every open question (30 of 30).
4. The real problem is not the missing lookup. It is that the founder removed the Follow Line boarding cap on
   2026-11-08 and since then 80 percent of all questions born are the Follow Line's own spawn (asked and consequence),
   about 900 a day against 24 open slots, and almost none of them ever finish.

## Stage by stage

| Stage | Where | State | Evidence |
|---|---|---|---|
| Birth from the curiosity node | `nodes/curiosity_node.py` note_question "curiosity" (up to 3 per run) | LIVE | 382 in 7 days, about 55 a day; 11 resolved |
| Birth from the Follow Line: his own asks ("asked"), re-boarded consequences, claims | `core/follow_line.py` board(), `note_question_ex` | LIVE, uncapped since 11-08 (BOARD_CAP_PER_HOUR = None) | 7 days: asked 3,077, consequence 2,011, claim 632 = 5,720 of 6,343 (90 percent, with claims) |
| Birth from prism, dream, study, intention, pursuit | queue prism, dream, study tablets, inner monologue | LIVE, trickle | prism 29, dream 14, study 5, intention 92, pursuit 101 in 7 days |
| Worth (OMNI gate, interestingness) | `core/curiosity_worth.py` shadow_pass from inner_monologue_node | SHADOW, gates nothing | 566 passes ever, 1 to 9 a day; grades the 21 to 24 eligible open questions; every `lp` is 0.0 so it cannot rank by LP; deterministic replacement d2 failed hold-out (F-4537, AUC 0.636) |
| Selection for pursuit (`pending_pursuit`, park rule `is_parked`) | `core/frontier.py`, `core/curiosity_progress.py` | DEAD (zero live callers; park rule only read inside the dead path) | 0 of 6,343 questions born in 7 days has `last_pursued_ts`; newest pursuit 8.9 days old; 2,603 ever pursued |
| Pursuit action (lookup, finding, stall count) | was `curiosity_node._write_output` | RETIRED 11-05 on purpose | code comment at curiosity_node.py ~L371 |
| Finding attached | `frontier.attach_finding` from `follow_line.py:1362` | LIVE but not a research finding | 276 of 300 findings in the last 10 days are the fixed title "what you found in your own memory", landing on faded or resolved questions, none on the open ones |
| Follow Line run (grounds, why, consequences, connections, against, decoupled judge) | `core/follow_line.py` | LIVE | `would_return` 169 to 839 a day on live days (11-08 to 11-14); 29 MB shadow log |
| Delivery to an idle thought and settle | take_delivery in inner_monologue_node | LIVE | settled rows since 11-08: unsaid 1,392, no 389, partly 376, yes 150 (2,307 total) |
| Resolution | `frontier.resolve` by his settled yes, `resolve_if_addressed`, closure arm `line` | LIVE, small | 239 resolved of 6,343 born in 7 days (3.8 percent); 145 by `line`, 97 by older paths |
| Eviction and fade | `MAX_OPEN = 24`, `FADE_AFTER_S` 21 days | LIVE, and the real terminal state | 6,075 of 6,343 (96 percent) born in 7 days are already faded; of all 20,804 faded, 18,004 (87 percent) were met only once |
| Question progress for the goal register | `core/goals._question_progress`, `core/curiosity_progress.mech_progress` | SHADOW (J-4000, branch commit 76d70b1c) | separates 1 of 25 open questions (F-4682); re-ask weight 0 pending D-0777 |

## What the numbers say about what a question is today

- A question is born, almost always by the Follow Line, waits (3,710 of 6,343 born in 7 days are still `waiting`, not
  yet boarded when evicted), and is faded by slot pressure. Only 14 percent get a judged line state (settled yes,
  partly or no = 868) and 3.8 percent resolve.
- By source, 7 days, born / resolved / got a judged line verdict / met more than once:
  - asked 3,077 / 195 / 708 / 576. His own asks are what work: 6.3 percent resolve.
  - consequence 2,011 / 13 / 34 / 230. 0.6 percent resolve. This is the line's own output re-boarded as new questions,
    and it is the largest source of the birth flood. It is one stop of one mechanism feeding itself.
  - claim 632 / 11 / 69 / 62.
  - curiosity 382 / 11 / 28 / 115.
- The 24-slot frontier turns over about every 40 minutes on busy days (ages of the 29 open on the read: all under a
  day). A question has no time to be "carried"; goals like those in layered_goals cannot be built from an object that
  lives minutes.
- The park rule (3 stalls) can never fire now, because stalls are only counted by the retired pursuit.

## What is decided already (not re-asked)

- D-0659: retire the system-initiated lookup; questions are for him to pursue by hand. Done, as built.
- D-0661: the Wikipedia hand is told to him by Travis, a diegetic book line and an encyclopedia object (J-3285). Not a
  prompt offer. So "by hand" is the ruled direction; whether it is built is a separate job, not this one.
- D-0777 (open): does a re-ask count as progress. Not duplicated here.

## What only the founder can rule (opened as decisions)

1. What is the way a question gets worked now. Options: (a) the Follow Line is it, formally: retire the dead pursuit
   machinery from the docs and the progress/worth readers, and make learning progress come from the line's own state
   (settled partly = progress, yes = resolved, no = closed); (b) as (a) plus the Wikipedia hand (J-3285) as his own
   act, with its result marked as from the source (D-0631 principle) and counted as progress only when he acts on it;
   (c) bring back a system-initiated working step of some kind. Recommendation (b); (c) contradicts D-0659.
2. The birth rate. 900 a day against 24 slots, 80 percent the line's own spawn. Options: (a) leave it, accept the
   frontier as a stream not a backlog; (b) cap boarding by source, in particular stop consequence re-boarding or give
   it a small daily quota (his own asks and claims stay uncapped); (c) raise MAX_OPEN so a question lives days. The
   founder removed the hourly cap on 11-08, so this is his call; the evidence for it is the 6.3 vs 0.6 percent
   resolution split. Recommendation (b), consequence quota only.
3. What a question is for once the goal register holds goals. Options: (a) a question is a goal's input, not a goal:
   only a question that survives some span (say two settled partly, or a settled yes) is promoted to a register
   entry, the rest stay a stream; (b) every open question is a register entry (what J-3985 does today, which reads
   28 near-identical rows); (c) questions stay outside the register. Recommendation (a).

## Reading

- Verified: the retirement, the zero callers, the 0.0 LP, the line as the live working stage, and every count above
  (read directly; see F-4707).
- Inferred: that the birth flood is due to the 11-08 cap removal. The log shows births rising from 52 and 592 (11-04,
  11-05) to 1,130 to 1,485 (11-08 to 11-10), but Du was also down on 11-06 and 11-12, so the step is not a clean
  before and after.
- Not examined: whether his asks (`asked`) are good questions; this report counts what happened to them, not their
  quality.
