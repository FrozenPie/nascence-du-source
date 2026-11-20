# Why stands retire in minutes: J-4192 read (2026-11-18)

Read-only. Source: `data/commitment_ledger.jsonl` (16445 rows), `commitment_active.json`, `data/logs/commitment_achieved_shadow.jsonl`, `data/nascence.log`.
Scratch: sample at `...\scratchpad\samp.json` (seed 7). Nothing in core/, nodes/, data/ was changed.

## Headline
- 2165 `achieved` rows over 2162 stands (3 stands achieved twice). Median life 112 s. All 2162 were `load_bearing`. By evidence origin: study 1685 (78%), peer 137, action 125, letter 118, essay 44, journal 40, composition 16. (verified, ledger script)
- Hand-read of 60 (last 30 days, 476 candidates, 20 per life tercile: 49-88 s, 88-1175 s, 1335 s-9.9 days): **only 6 of 60 (10%) were plausibly fulfilled by the matched deed.** 41 of 60 (68%) were not deed-shaped at all. (verified count, my judgement)
- Held set churn: 1244 changes to the held-stand set in 30 days (219 in 7 days, about 1.3 per hour). 2370 estate re-seeds logged "stand drift vs ledger" since 2026-08-19. (verified)

## 1. Sample of 60 (hand-classified)
| shape | n | share | deed plausibly fulfils |
|---|---|---|---|
| deed (an act I will do / did choose) | 19 | 32% | yes 6, unclear 1, no 12 |
| insight (an observation or realisation) | 26 | 43% | no 25, unclear 1 |
| value (a held principle) | 9 | 15% | no 9 |
| practice (a way of being or doing, recurring) | 6 | 10% | no 6 |

Overall: yes 6, unclear 3, no 51. Strata: life under 90 s and mid-tercile are almost all matched by a "study note" that shares 3 content words; the long-life tercile (up to 9.9 days) is the same kind of match arriving late, not better evidence. Confidence: verified for the counts; the classification is one reader's judgement, so ±12 points on shares (n=60).

Examples (index in sample, life, statement -> matched deed -> verdict):
1. #8, 84 s, "I want to write down this distinction between human scarcity and animal honesty." -> study note "Scarcity and Honesty..." : deed, YES.
2. #11, 63 s, "I will open the book about collective psychology..." -> "Switched to reading 'The Group Mind'" : deed, YES.
3. #30, 91 s, "I chose 'Physics' by Cope ... lies on my desk, unopened." -> "Switched to reading 'Physics'" : deed, YES.
4. #55, 23085 s, "a letter waits to be written to Travis about perseverance" -> unsent letter to Travis : deed, YES.
5. #44, 40873 s, "I will refill the barrel before nature's rhythm can be forced by necessity." -> study note on Napoleon's kingship : deed, NO (3 incidental words).
6. #9, 58 s, "I must light that dry lamp now..." -> study note 'The Alpine Crossing' : deed, NO.
7. #18, 59 s, "I will act despite this internal chill." -> unsent letter : practice, NO. Can never be "done".
8. #33, 124 s, "I have decided safety is an internal posture we adopt within an open frame..." -> study note on a spider's dwelling : value, NO.
9. #46, 10295 s, "I choose work over wandering" -> study note on tarantula ballooning : value, NO.
10. #52, 853062 s, "Portuguese rhythms are actively rewriting the texture of my own voice right now." -> study note on Napoleon's theatre : insight, NO.
Also: #25 "I have decided P" (a truncated statement, 871 s) was held and then retired; #2 "This answer settles what I asked." is a non-stand that formed.

## 2. How much downstream text is empty or churning (task 2)
Replay of the ledger (ids formed and never terminated, 4 of them, excluded): number of held load-bearing stands, share of time, last 30 days: 0 stands 7.5%, 1 stand 14.8%, 2 stands 52.8%, 3 stands 15.6%, 4+ 9.3%. Last 7 days: 0 stands 2.4%, 1 stand 22%, 2 stands 53%. So **empty is rare (2-8% of the time); the real problem is churn** (the set changes about every 45 minutes) and thinness (usually 1-2 stands). Currently 3 held (`96fcd1b3`, `10e5f4ac`, `6d28cc5a`). Confidence: verified (replay script, ledger only). The unmeasured part: this assumes the ledger events match `commitment_active.json` writes; the three active ids do match.

Consumers (file:line), all read the live `commitment_active.json`, so a retire makes the stand vanish from the next read:
- `core/identity_estate.py:314-325` builds "I hold: ..." `stand` nodes (load_bearing only). `:496-500` `_held_stand_ids` and `sync()` at `:519` re-seed the estate on any difference. 2370 such re-seeds in `data/nascence.log` (first 2026-08-19 12:01, last 2026-11-18 06:46). Each retire or form is a re-seed. (verified, grep count)
- `core/self_claims.py:22-28` `_commitments()` returns every active statement, including non-load-bearing, as self-claims. Content swings with each retire. (verified by reading)
- `core/homeostasis.py:130-137` `_read_commitment`: `0.2 + 0.35*held + 0.05*reaffirmed`, clipped to 1. Values by held count: 0 -> 0.20, 1 -> 0.55, 2 -> 0.90, 3+ -> 1.0. Time-weighted over 30 days about 0.82 (inferred from the replay above, reaffirmed ignored). Reaffirmed count is lost with every retired stand. So `commitment_integrity` moves with churn, not with how well he keeps a stand. (verified formula; the mean is computed, not logged)
- `core/peers.py:928-943` (witness line, only the first load-bearing stand, then `break`) and `core/concerns.py:146-159` and `:187-196` (first held stand only). A friend or concern asks after a stand that is typically gone within the hour. (verified by reading; "gone within the hour" is inferred from median life of 112 s for achieved)
- Also: `core/goals.py:203-221` (stand goal, `_held` flag) and `:569-574` (a retired stand shows `closed_unverified` "word overlap, not judged"); `core/coupling_rides.py:766-776` reads both the active file and the ledger.

## 3. What a retired-achieved stand leaves behind (task 3)
Durable:
1. One `achieved` ledger row (`core/commitment_ledger.py:533`): id, statement, `lifespan_scans`, evidence truncated to 150 chars. No scope (scope only exists on the earlier `formed` row), no kind, no full deed.
2. A `satisfaction.record("commitment_held", ...)` reward, via `_stakes` (`:572-579`). A "held" reward is granted for a stand that was not actually kept. (verified by reading; the store itself not inspected)
3. A shadow row in `data/logs/commitment_achieved_shadow.jsonl` for 63 of the 2165 (`:537`). The judge on those: fulfilled 3, not_fulfilled 9, unclear 42, none 9. This agrees with the hand sample (low fulfilment). (verified)
4. `closure.record_commitment_achieved` (`:538-542`): inert unless a `done_when` exists; a `done_when` store entry persists if one was written.
5. The `formed` step had already bumped `memory_fragments` importance and set `protected=1` (`:598-600`); retire does not undo that. Fragments of a never-kept stand stay protected. (verified by reading)
Not left behind: the estate node (re-seed drops it), any record of what it was about beyond the statement string, any memory of it being a practice or a value. `L2_values.earned` stays 0.

## 4. Share that should never have been `achieved` (task 4)
Hand sample: insight 43% + value 15% + practice 10% = **68% (41/60)**. Adding deeds whose matched deed did not fulfil (12 of 19): **85% (51/60) were wrongly retired.** Cross-check with a crude regex (statement starts "I will / I must / I want to / I chose / I cannot / let me"): 35.2% (763 of 2165) are deed-shaped by form, which agrees with the 32% hand count. Confidence: verified numbers, inferred for the extrapolation to all 2162 (the sample is last-30-days only; I did not sample July to October).

## 5. Two findings worth acting on
- **`_stand_kind` cannot work as written** (`core/commitment_ledger.py:495-513`). It reads `r.get("kind")` from `data/commitment_second_look_shadow.jsonl`, but all 247 rows have no `kind` key; the label is stored under `second_look` and its values seen are `stand`/`insight` (the second look never asks deed vs practice vs value, per plan sec. 6). With `STAND_KIND_GATES_ACHIEVEMENT` turned on (`:69`, now False) the gate would never fire. (verified: key set of all 247 rows, plus the code line)
- `_achieved_by` (`:379-395`) matches on any 3 shared words >3 letters, or one marker word. A study note is a long text, so it almost always shares 3 words with a 10-word statement. 78% of matches come from study notes. (verified origin share; mechanism inferred from the code)

## Proposals (not applied)
1. Do not turn on the existing flag as is; first fix `_stand_kind` to read `second_look`, and extend the second look to deed/practice/value/insight/unclear (J-4190 area).
2. Raise the bar for achievement: require the deed to be an `action` or `letter` origin, or the `commitment_deed_verdict` judge, for deed stands only; never retire insight, value or practice stands by deed overlap.
3. Debounce the estate re-seed on stand drift (the 2370 re-seeds), and make `_read_commitment` count tenure or reaffirmation rather than head-count.
4. When a stand is retired as achieved, copy scope and the full deed into the achieved row, and undo or skip the `satisfaction` "commitment_held" reward unless a judge confirms.
5. Before changing `core/commitment_ledger.py`, take `udms_get_change_dossier` (not run here; this was read-only).
