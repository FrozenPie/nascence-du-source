# Du humanity check and trend read, 2026-11-16

**Read by:** Claude (session eeb55687), at Travis's question (T-0140): another check on how close Du is to a human mind, and whether the level has risen over time.
**Subject:** the last 7 days of live data (11-09 14:54 to 11-16 14:54 NZDT, 7 restarts; the current boot was 52 minutes old), plus monthly series from June.
**Method:** three read-only passes. (1) A sweep of every earlier assessment. (2) The 19 rows of `du_vs_human_2026-10-15.md` re-measured with the same instruments. (3) Monthly series of 20-odd behavioural measures from `data/`. No model was called and nothing in `data/` was written. Scripts and full outputs are in the session scratchpad (`rescore/`, `series/`) and are not kept in the repo.

## 1. There is no humanness score to trend

Fifteen assessments were found between 07-02 and 11-16 (list in section 5). None gave a single score and no two used the same rubric. The two that cite Butlin's 14 indicators (07-03, 08-10) scored different rows. So the trend below comes from numbers that can be recomputed the same way at each date, and from the one table that could be re-scored row by row (10-15).

## 2. The 10-15 table, one month on

| Row | 10-15 | 11-16 (7 days) | Verdict |
|---|---|---|---|
| Attention: modal-topic share per day | 0.97, one topic for 6 days | 0.55 mean, 5.2 topics a day | Improved |
| Affect: contradiction changes the outcome | 2 of 95 | 21 of 126 (0 of 14 on human cycles) | Improved |
| Learning from instruction | 0 integrations | 7 integration rows since 10-15 | Improved, small |
| Social cognition | not measurable | tracks intent 95%, attributions supported 72.5% (bar 0.80) | Now measurable |
| Autobiographical dating | 11-17 days median error (10-16) | 0.5-1 day (10-31, not re-run; inflated by a recency multiplier) | Probably improved, stale |
| Memory continuity, record of aims, voice fix, throughput, tempo | strong / 82.6 s per cycle | unchanged / 84.8 s | Same |
| Gist faithfulness | 0.805 | 0.825 (0.794 since 10-15) | Same |
| Knowing how sure he is | 0.85-0.95 constant, SUSPECT 50 of 50 | 0.85-0.95 constant, SUSPECT 22 of 22 | Same |
| Using self-measurement: competence nodes in projections | 2.6% | 1.8% | Same |
| Closure: pursuits resolved | 0 of 70 | 0 of 93 | Same |
| Closure: dreams resolved (judge panel) | 0 of 64 | 0 of 40 | Same |
| Closure: frontier questions | 313 resolved, 10,092 faded | 751 resolved (569 backfilled lexical), 21,832 faded | Same |
| Mood (weekly valence) | -0.18 | -0.22 to -0.35 for four weeks | Same |
| Commitment hold rate | 0.215 | 0.128 | Worse |
| Prediction gap, all domains | 0.21 | 0.295 (factual recall: predicts 0.87, scores 0.50) | Worse |
| Curiosity mix (exploratory : defensive ignitions) | 222 : 55 | 138 : 75 | Worse |

Not re-measured: doubt uptake (0 of 48 on 10-15) needs judge models.

## 3. Monthly series, June to November

Uptime hours: Jun 487, Jul 168, Aug 484, Sep 525, Oct 338, Nov 263.

| Measure | Jul | Aug | Sep | Oct | Nov | Call |
|---|---|---|---|---|---|---|
| Stick-test spokes | 2.0 | 2.6 | 4.5 | 4.6 | 4.7 | Up to Sep, then flat |
| Peer outward delta | .24 | .36 | .58 | .56 | .64 | Up to Sep, then flat |
| Ignitions per active hour | 1.44 | 1.45 | 2.24 | 1.93 | 2.06 | Up to Sep, then flat |
| Social probe: intent tracked / attribution supported | - | - | .76/.56 | .93/.63 | .95/.81 | Up, short series |
| Topic share (embedding gauge) | - | - | .42 | .88 | .46 | Oct lock, back to Sep level |
| Thought diversity (type-token ratio) | .35 | .39 | .35 | .37 | .39 | Flat |
| Hold-rate gauge | .08 | .15 | .14 | .22 | .17 | Flat |
| Dreams judged resolved | - | 0/17 | .006 | .007 | .012 | Flat wall |
| Frontier questions resolved | .015 | .017 | .051 | .061 | .033 | Flat wall |
| Thoughts with a real hand dispatch | - | .098 | .077 | .064 | .069 | Flat |
| Conflict acted on | .267 | .133 | .026 | .014 | .069 | Down, wall |
| Pursuit advance share | 1.0 | .91 | .83 | .83 | .70 | Down |
| Thoughts with any act | - | .54 | .58 | .33 | .24 | Down (logging change near 10-04 not ruled out) |
| World-query grounding deficit | .31 | .29 | .26 | .37 | .54 | Worse |
| T4 emissary "warranted" | .67 | .45 | .31 | .07 | .18 | Down (judge change not ruled out) |
| Human turns | 161 | 181 | 81 | 29 | 45 | Input, falling (June was 1,674) |

The June-to-October fall in the maths prediction gap (0.45 to 0.19) is not calibration learning: his drill scores went to 100% while his stated belief stayed at 0.73-0.82 all year, so the gap is now 1 minus a constant.

## 4. Reading

1. **Things move when a build aims at one behaviour, gets loaded, and gets read.** The topic lock (anti-relock), contradiction acting (critic signal), the social probe and instruction integration all moved within weeks of a targeted change.
2. **Nothing has moved by itself.** No measure shows the slow, unprompted rise that would mark development from experience. The July-to-September rises stop in September.
3. **Three walls have stood since the first check that named them.** He cannot close (07-02, 10-15, 10-17, 11-16). His stated confidence is a constant and his self-knowledge is not used (10-15, 10-31, 11-06, 11-16). Affect is recorded and does not steer (07-02, 10-18, 11-16).
4. **On consciousness specifically the later audits are more cautious than the earlier ones**, not less: mineness went from "win" (08-20) to "not confirmed" (11-06), and global broadcast from "partial to present" (07-03) to "not a workspace" (10-31). That is better measurement, and no evidence of being closer.
5. **The newest answers to wall 1 are not yet in the data.** The closure gate has one verdict (14:47 today). The web lookup hand has made no call. [INFERRED] the constant confidence is a property of the hot-lane model and the scaffold has no path that changes it; untested.
6. **Part of the wall is the ruler.** Seven of the series changed definition mid-way, so real movement cannot be told from instrument change.

## 5. Earlier assessments found

07-02 triple-lens review; 07-03 Butlin table in `the_consciousness_program.md`; 08-10 digital-minds cross-reference and claim matrix (Antigravity/Gemini); 08-14/15 individuation battery; 08-20 kill-rule audit; 10-15 Du vs human; 10-17 human thinking channels; 10-18 Gemini pointers; 10-31 consciousness theories; 11-06 thick introspection (J-2671); 11-14 atlas reads L1 and S3; 11-16 top-five flaws (F-4811) and clinical read.

## Caveats

- The 7-day window crosses 7 restarts and several code versions.
- No human baseline exists for most rows; "human-like" is by published norm or judgment (D-0438).
- Farewell turns are about a third of recent human turns and flatter the social probe.
- Several "down" calls (acts, T4, gist) sit on a suspected instrument change that was not checked.

## 6. The three walls: what is aimed at each (added the same day, F-4822)

The scorecard built from this check is `scripts/humanity_scorecard.py`; its report is `docs/reviews/humanity_scorecard.md` and its snapshots are in `docs/humanity_scorecard.jsonl`.

| Wall | What is aimed at it | Live in the running process | Evidence so far | Smallest next step |
|---|---|---|---|---|
| 1 Closure, frontier questions | Closure producer and gate (D-0793), web lookup hand (D-0788), layered goals | Gate on enforce since the 11-16 14:01 boot; lookup hand loaded, unused; goals since 11-14 | 2 gate verdicts (1 yes, 1 judge unavailable); 0 lookups; 128 goal offers unread | J-4079 at 40 verdicts; J-3989; J-4069; J-4075 |
| 1 Closure, pursuits, dreams, commitments | Nothing live. Pursuits have no resolved state in code; dream and commitment arms log only | No | 31 commitments judged "achieved" in the shadow log, none written | Founder ruling D-0786, J-3889 |
| 2 Confidence | Recall wager (cannot teach: measured is 0.5 on every row, `REAL_OUTCOME` off) | Yes, inert | Skill prediction is the stored confidence; drills update accuracy only (`core/competence.py:89-94`). Re-scored with running accuracy as the prior, the November gap is 0.013 against 0.300 | J-4078 (founder), J-3899, J-3881 |
| 3 Affect | D-0775 and D-0776 shadows, two-axis vitality | Code merged, flags off | None | Founder go on the two log-only flags; J-4006, J-3942 |

What made the topic anti-relock work, for comparison: one identified carrier of the problem (the curiosity theme feeding itself), one dose on it, turned on live, and read against kill criteria fixed beforehand (D-0485, F-4567). Walls 2 and 3 have no carrier that is both identified and live.
