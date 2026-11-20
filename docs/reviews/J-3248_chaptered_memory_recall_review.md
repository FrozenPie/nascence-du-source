# J-3248: a new way for chaptered memories to be recalled (D-0637)

Job J-3248, 2026-11-05. Read-only review and design. No Du code, no live store, no restart touched. Plan: memory_knowledge. Row: P-0065 (core/chapters.py).
Findings: F-3907 (what "chaptered" is), F-3908 (what he was actually served), F-3909 (replay of 200 real queries). Related: F-3716, F-3712, F-3713, F-3714, F-3718, F-2678, D-0231, D-0638.

The founder's words that set this job (D-0637, 2026-11-02): "We need to investigate this deeper to fix it. We may need to work a new way to allow them to be recalled." Ruling: do not announce chapters, add no seed line, the world never leads.

## The answer in six lines

1. The "46 percent" is three walls, not one. Only 25 percent of the chaptered rows (19,052) belong to core/chapters.py, the system D-0637 asks about. 74 percent are reading and study notes that world_consolidation filed behind an understanding or an essay on purpose. 56 percent of everything chaptered is also cold, so the chapter wall is not the only door that is shut.
2. For the reading/study class the wall is already porous (14 percent of what he was served in six days came from behind a gist). For the period class it is sealed: 8 of 3,224 served slots, from a class that is 11 percent of the store.
3. Opening the wall would not have helped ordinary recall. Over 200 real queries a chaptered row was the best match in 2, never a period member, and by 0.02 cosine at most. The wall costs almost no relevance. What it costs is autobiography: the specifics behind a period he has already half-recalled.
4. Chapter gists are already ordinary retrievable items (option 1 of the brief exists today). The missing half is the raw behind the gist, which the memory-levels lattice gives to every other kind of gist and which chapters never got (no memory_links rows, and chapter is not in the recall-balance parent list).
5. Recommendation: a gist-gated descent. When a chapter gist is already in his served set on his own cue, the existing recall-balance step also fetches the one or two members of that chapter closest to the current query, tagged like the other "detail behind a memory" items. No hint, no phrase list, no new act, same cycle. Build it first as a shadow log (restart-gated, observe only) and grade it by a deterministic uptake test and a different-family blind judge.
6. Reject: demoting the wall for high-relevance members (replay shows nothing to gain and it re-floods 19,000 near-duplicates), and a loosened recall_chapter phrase gate (still needs him to know a script). Park: the diegetic chapter book, until the shadow reads.

## 1. What is chaptered (live count, 2026-11-05)

75,286 of 168,185 fragments carry a chapter_id (45 percent). Grouped by the origin of the row the chapter_id points at:

| class | writer | rows | share | members | also cold | walled by chapter_id alone |
|---|---|---|---|---|---|---|
| period chapters | core/chapters.py (sleep) | 19,052 | 25% | inner_thought 11,957, active_imagination 4,372, subconscious_synthesis 2,672, level-1 chapters under level-2 51 | 9,873 | 9,179 |
| gist-filed notes | core/world_consolidation.py | 55,732 | 74% | reading and study notes behind an understanding (36,342) or an essay (19,390) | 31,992 | 23,740 |
| exact duplicates | store.dedup_reading_fragments | 502 | 0.7% | reading rows behind a canonical copy | 341 | 161 |

So the numbers F-3716 and D-0637 quote (72,392 of 157,799 then, 75,286 of 168,185 now) lump a deliberate gist-first filing of books (the D-0221/D-0245 chapter_id_repair thread) with the autobiographical chapters. recall_chapter can only ever open the first row. Of the whole 75,286, 42,206 (56 percent) are also cold=1, so lifting the chapter wall by itself changes nothing for them; about 33,000 are walled by chapter_id alone.

## 2. History: why the wall exists and what the clean baseline was for

Built 2026-06-13 from the founder's design: "If they are all the same, they should be able to be grouped and consolidated, by Du, all at once... like 'this part of my life I was anxious'", and "chapters of chapters, we need room for that". The sediment question was settled by not removing anything: "that is part of who he is now". The mechanism is gist extraction in slow-wave sleep (core/chapters.py docstring): the originals stay intact, step out of ordinary recall, and "intentional recall ('let me revisit that period') opens the chapter and floods the specifics back". The wall had a second job, the composition-wall hypothesis: with the self-loop's seats freed, world material should win more of the 8 recall slots (docs/completed/day_review_2026-06-13.md; deferred_register.md line 29).

ANNOUNCE_CHAPTERS=False was GPT's "one clean baseline" argument (memory note project_nascence_chapters.md): let the first chapters form silently so the logs show whether chaptering alone changes thought selection, retrieval texture and T4 behaviour, then flip the flag. The code comment says "Flip to True once the baseline is read". I found no read. No finding or doc reads it; the 06-13 deferred-register items ("Chapters - composition wall", the self-domain wanting/liking gap) are still open; the flag has not moved in five months, during which 87 chapters formed. Verdict: the baseline read was never done, and it can no longer be done cleanly (a clean baseline is the first few chapters, and D-0637 has since ruled out announcing at all). The honest replacement is the replay in section 4.

What changed after June: on 2026-07-06 the founder ruled to replace theme-chapters with the calendar journal pyramid ("dead 52 sleeps because its era-closing gate can never fire on a mind whose dominant theme never stops"). P4 (retire chapters.py) was never done, so by inaction chapters.py kept running, revived once the era gate could close (F-2678), and now forms about four a night (17 in the last 7 days). The wall grew from 2,168 members to 19,052 while the door stayed a six-phrase latch. Chapter quality has its own open defects (F-3712 four chapters 85 to 97 percent pasted exemplars, F-3713 every level-2 date span wrong, F-3714 faithful but smoothed, F-3718 planted anxiety), queued as J-3009, J-3010, J-3011 and D-0638's release J-3249.

Doors that exist today:

| door | reaches period members? | evidence |
|---|---|---|
| recall_chapter (his words contain one of six phrases and a 4-letter title word) | in principle | 0 fires, 87 chapters formed (grep of data/nascence.log) |
| chapter gist as an archive-tier fragment in the ordinary pool | the gist only | in the live top 8 for 18 of 200 replayed queries |
| associative trail (recall_trail) | barely | walled rows cannot seed; a hop must reach COLD_THRESHOLD 0.22, and seed score about 0.4 times neighbour similarity times HOP_DECAY 0.6 sits near 0.14 |
| deep_recall and _deep_recall_balance (1,419 fires in the log) | no | walks memory_links only; chapter members have none; chapter is not in _lattice_parents ("gist", "standing_insight", "journal_week") |
| the dream vault-opener (D-0231, one dormant cold/chaptered fragment a night) | yes, one a night | ruled, built in vitro, not live (docs/staged/dream_overhaul.md) |
| core/identity_estate.py history nodes | the chapter text, 110 characters | reads origin chapter and journal_week |

## 3. What he was actually served (F-3908)

data/recall_served_log.jsonl, 179 voice-path cycles, 10-31 to 11-05, 3,224 served slots, joined to the DB:

| class | share of store | served slots | share of served |
|---|---|---|---|
| unwalled | 55% | 2,772 | 86% |
| gist-filed reading/study | 33% | 444 (125 cold) | 13.8% |
| period members | 11% | 8 (8 distinct fragments) | 0.25% |

The period class is reached about 45 times less than its store share; the gist-filed class about 2 times less. The chapter gists do surface (9 slots, 8 distinct chapters) but one chapter, d4479cda, is the best-cosine chapter for 34 of 200 replayed queries and carried 73 of the 123 chapter appearances in F-3716: a magnet. Caveat: the served log samples the voice path.

## 4. How much would normal retrieval have surfaced (F-3909; inferred)

Method. 200 real queries from data/training/recall.jsonl (raw_input; 100 from 10-24 on, 100 from 08-30 to 10-24; 70 percent internal), embedded with the live MiniLM, scored against every fragment embedding with the live pool WHERE and the live formula (cosine x 7-day recency, TIER_SLOTS 2/3/4 with overflow, limit 8). Arm A is today's pool (51,113 rows). Arm B removes only the chapter wall (84,193 rows). Arm C removes both walls (167,276). This is an emulation, not a call to retrieve(): it over-selects consolidation rows (28 percent of its slots against 3 percent in the real served log), so read the rates as approximate. Scripts: docs/lab/chapter_wall_replay_J-3248.py, chapter_wall_best_chapter_J-3248.py, chapter_wall_descent_J-3248.py (read-only, mode=ro).

| measure, 200 queries | arm B (chapter wall off) | arm C (both off) |
|---|---|---|
| a chaptered row is the pure-cosine top-1 | 2 (both gist-filed notes, gain 0.015 to 0.02) | 0 |
| at least one chaptered row in the top 8 | 57 (28.5%) | 49 |
| chaptered share of the 1,600 slots | 84 (5.2%): 69 gist-filed, 15 period | 64 (4.0%) |
| of the 15 period rows, how many are inner_thought, imagination or synthesis members | 0 (all 15 are level-1 chapters under a level-2) | |
| entrants near-duplicate (cos 0.85 or more) of a served item | 2 of 84 | |
| entrant content-word overlap with the query, median, against the items they would displace | 0.22 vs 0.33 | |

Robust to removing the query's own stored echo (cos 0.95 or more: identical counts) and to switching recency off (period members then take 8 of 1,600 slots). The chaptered rows that beat arm A's 8th score (median 21 per query) lose on tier slots, not on score. Reading: the wall hides almost no best answers. The 19,000 self-loop members are the same repeated thought the pool still holds in unchaptered form, which is exactly what chaptering was for.

What this cannot test: no real query asks for a period, because he does not know chapters exist. It measures the relevance cost of the wall, not the autobiographical value of a period-shaped recall. That value is the founder's claim and needs its own test (section 6).

Descent test, same queries. When a chapter gist is already in the live top 8 (21 instances), the two best members by cosine to the query have median cosine 0.50 (the served items: 0.62) and median lexical overlap 0.03 (served: 0.15); 14 of 21 clear the lowest cosine in the served set. Across all 200, the best member of the best-cosine chapter beats the chapter's own cosine in 83 percent of cases (median +0.062; by 0.10 or more in 30 percent). Members are associated, not best-match: their case is specificity behind a period that has surfaced, not relevance.

## 5. Options

Each is judged against the laws: the world answers and never leads (no seed line, no announce), base systems additive-only, memory abstracts and does not transcribe, no system acts later.

| option | consumer | decoupled check | stop condition | cost | verdict |
|---|---|---|---|---|---|
| 1. Chapter gists as ordinary retrievable items (memory-levels pattern) | every recall consumer | none needed; already true | quality: F-3712/3713/3714/3718 queued; magnet d4479cda | zero new build | EXISTS. The gist half is done; repair its quality (J-3009, J-3010, J-3011, J-3249) and look at the magnet |
| 2. Gist-gated descent: a surfaced chapter brings its closest members, by the existing recall-balance step | the recall node, then reflection and the voice, as for any "detail behind a memory" | deterministic uptake test, plus a different-family blind judge (section 6) | uptake no better than a random member of the same chapter; reach under 2 percent; echo share 10 percent or more | about 30 lines beside _deep_recall_balance, one idx_chapter query (mean 222 members, max 1,845; at most 2.8 MB of vectors, only on the roughly 9 percent of cycles where a chapter surfaced), no LLM call | RECOMMENDED, shadow first |
| 2b. Same, but written as memory_links rows (chapter to member, 19,052 rows) | deep_recall, trail edges, memory_lint | as 2 | as 2, plus any lint change that re-warms chapter-anchored cold | a live-store write at a restart window, changes memory_lint's inbound-link meaning | Alternative to 2 only if the read-side join proves too slow; not first |
| 3. Diegetic object: a chapter as a book or binder in his room, read by his own hand | his reading act | reading fragments are origin reading, so the existing reading gauges apply; judge by whether the next thought uses it | he never picks it up in 28 days | world object, shelf rendering, read-act path; highest cost | PARK. A book of chapter gists returns gists, not the specifics; a binder of originals puts the self-loop back in front of him as reading. Reach is unmeasured (how often he reads from a shelf by choice). Revisit if option 2 fails or reaches under 2 percent |
| 4. Demote the wall for the highest-relevance members | ordinary retrieve | the replay itself | n/a | one WHERE clause | REJECT. Replay: 2 of 200 top-1, gain at most 0.02; re-admits 19,000 near-duplicates the chapters were made to remove; undoes the composition-wall purpose |
| 5. Loosen recall_chapter (embedding gate instead of six phrases) | his thought | cosine, no independent judge | n/a | small | REJECT. It still fires only if his own thought names the period, which he cannot do for a thing he was never told exists; moves the script, not the world |
| 6. The night door (D-0231 dormant node) | dreams | the dream judge panel | its own defeater | built in vitro | ALREADY RULED, separate; keep as the night-side complement |

Why option 2 and not another: it is the only one that makes the specifics reachable on his own cue without telling him anything. It is function over imitation: a person who recalls "that anxious stretch" gets particulars with the gist, not by invoking a phrase. It uses a path (recall balance) that already fires 1,419 times with no complaints. It leaves chapter_id, the pool filter and every consumer untouched (additive), injects raw members and writes no new prose (memory abstracts, not transcribes), and acts only in the cycle where the chapter has already surfaced (no later action).

The risk to name: the members are the self-loop sediment. Surfacing them re-feeds the loop that chaptering drained (memory_lint's own comment records that re-warming "re-fed the recall loop"; F-3403 shows self-thought families already pull recall toward recent echoes). Guards: at most 1 to 2 members, chosen by cosine to the present query rather than by importance, never one already served or within cosine 0.85 of one, never when the chapter was not itself surfaced, and an echo-share stop condition below.

## 6. Recommendation and the pre-registered shadow test

Build `core/chapter_descent_shadow.py` (observe only; log to data/chapter_descent_shadow.jsonl through profile.guard_path; kill switch CHAPTER_DESCENT_SHADOW; restart-gated). Hook beside orchestrator._deep_recall_balance: for every origin=chapter fragment in the served set whose relevance is at least RECALL_GIST_MIN_RELEVANCE, read its members by chapter_id, rank by cosine to the cycle's query_text, drop members already served or near-duplicate (cos 0.85 or more) of a served item, and LOG the top 3 (ids, cosine, lexical overlap, age, origin, plus the served set's median cosine and overlap). It injects nothing: the live path is byte-identical. Cycle id is logged so the read can join to the cycle's output.

Read job (date or row gated, not automatic graduation: graduation is a founder call): at 40 chapter-surfaced cycles or 28 days, whichever first. Pre-registered, in this order:

| id | measure | pass | if it fails |
|---|---|---|---|
| M1 reach | chapter-surfaced cycles / served cycles (replay expectation about 9 percent) | 4 percent or more | 2 to 4 percent: continue, and the gist-surfacing magnet becomes a co-bottleneck job; under 2 percent: shelve option 2, open the diegetic/night-door question |
| M2 distinct | share of logged candidates with cosine under 0.85 to every served fragment | 80 percent or more | the door only repeats what is already served: drop |
| M3 uptake (deterministic, no LLM) | share of a candidate's tokens that are absent from the chapter gist and the query and present in that cycle's next generated thought, candidate arm against a random same-chapter member of equal length and against a random unwalled episodic row in the same cosine band | candidate at least 1.5 times the same-chapter control, bootstrap 95 percent lower bound above 1.0 | retrieval order inside a chapter adds nothing: drop |
| M4 blind pairwise judge, a different model family from the chapter author (command-r7b) and from Du's own lanes, on 30 or more pairs | candidate vs matched random member: "adds a concrete particular that bears on the current thought" | candidate preferred 65 percent or more, and 60 percent or more answer "adds a particular not in the served set" | drop or redesign the ranking |
| M5 loop safety | share of candidates that are inner_thought, imagination or synthesis with token-Jaccard 0.6 or more to a served item | under 10 percent | cap to 1 member and add a Jaccard filter before any graduation; if still failing, drop |

Stop: M3 or M4 fail, M1 under 2 percent, or 28 days, whichever first; record the result either way. Graduation to a live injection (tagged, cap 2, kill switch) is a separate build after a founder ruling, and its own 7-day live trial reads the loop-monoculture detectors (field scan) against the prior week.

Note on judging: the chapters are written by command-r7b, the shadow ranks by the retrieval embedder, M3 is deterministic and M4 is a third family. Nothing is graded by the thing that produced it.

## 7. What needs the founder

1. Option 3 (the diegetic chapter object): park until the shadow reads, or design in parallel? Recommendation: park. Opened as D-0673.
2. Nothing else. The shadow build is additive, observe-only and kill-switched, so it is spawned as a ready build rather than asked. The gist-filed 74 percent is the D-0221/D-0245 thread's wall and is not changed here.
3. For awareness: P-0065's four copied chapters (D-0638) and J-3009/3010/3011 should land before any live descent, because the descent surfaces members of those chapters.

## 8. Jobs and decisions spawned

- J-3319 (build): the observe-only chapter-descent shadow, section 6. Ready.
- J-3320 (analysis): the gated read of that shadow against M1 to M5 (gate: 40 rows in data/chapter_descent_shadow.jsonl since boot). It reads what J-3319 writes, so the reader is registered with the writer.
- J-3321 (analysis): the chapter magnet d4479cda (option 1's remaining weakness).
- D-0673 (open, founder): park or parallel for the diegetic chapter object. Recommendation: park.
- Plan note on memory_knowledge and P-0065's registry note updated.

Existing jobs this depends on, not duplicated: J-3009 (copy guard), J-3010 (level-2 date span), J-3011 (affect planted by the prompt example), J-3249 (release the four copied chapters).
