# dosed_coupling — folded history


---

# History folded on 2026-09-27 from `docs\staged\dosed_coupling.md` (plan-compact, 32 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py dosed_coupling`._

## Current State — verified 2026-09-24 (J-1291 checkpoint — restart-gate NOT met, both count-halving throttle fixes merged to master but not yet live, left open)

**J-1291 (production read of D-0266/J-1283's `last_decay_ts` throttle for tensions, gated per its own briefing, mirroring J-1173's established precondition-check method) checked its own gate directly rather than assuming it — NOT met (F-1834, verified).** Both throttle fixes are real and on master: `fbd9f83` (J-1283/F-1810/D-0266, tensions' `_apply_decay()`, committed 2026-09-23T19:52:29+12:00) is an ancestor of the `9a6eece` "job-run worktree merge: dosed_coupling" commit (2026-09-23T20:50:35+12:00), and `e37e34e`/`da061f3` (J-1290/F-1829/D-0270, the twin `_apply_pattern_decay()` fix) sit at master's current HEAD (2026-09-24T07:05:48+12:00 / 07:07:26+12:00) — the wt_dosed_coupling worktree itself was clean and already in sync with master before this note, nothing left unmerged. But Du's live process (PID 40268) has run continuously since **before either fix was committed**, confirmed on two independent instruments: `Get-Process -Id 40268`'s own `StartTime` (2026-09-22 16:10:23 local) and `data/nascence.log`'s own boot line ("Identity loaded... name=渡" at 2026-09-22 16:11:04,753, ~41s later — ordinary init lag, not a discrepancy — with no "Nascence shutting down" line since). Du's boot therefore predates `fbd9f83` by ~27h42m, the master merge by ~28h40m, and J-1290's twin fix by ~39h — the running process has neither throttle active yet. Per the briefing's own explicit instruction, the production `data/subconscious_state.json` tensions read was deliberately **not** forced this session — it would only reconfirm F-1631/D-0266's already-documented pre-fix baseline (739/874 idle-tensions at count exactly 1), not test the fix. **J-1291 left in_progress, not done** — re-attempt the same job once Du restarts onto `da061f3` (or later) and accrues at least one real `PATTERN_DECAY_DAYS` (7-day) window since that restart, ideally two, per the briefing's own stated bar. D-0266/D-0270 are both already ruled (no hold, nothing to reopen); no new job spawned — re-attempting this same job is the correct continuation, per this doc's own established convention for every other gate-not-met checkpoint on this plan.

---

## Current State — verified 2026-09-23 (J-1176 stage-1 dry run — demotion fix drafted+verified, not applied; D-0266 opened)

**J-1176 (F-1794, verified; supersedes J-1171) reproduced the silent tension-demotion crash on a fresh real-data copy and drafted the smallest correct fix, including Travis's approved per-scan cap, entirely in scratch — nothing applied to the repo or live state.** Today's numbers (874 tensions, up from F-1631's 868): the same TypeError still reproduces on the same live pattern (72 of 874 resolved tensions carry `resolved_ts=None`; the loop's bare `except: logger.debug` swallows it, silently no-opping the WHOLE classification for every tension that scan — the archive is still frozen at 1,009 rows/`mtime 2026-08-14 21:33:00`, byte-identical to F-1631's own citation); 626 of 874 (71.6%, up from 70.5%) are now eligible. The drafted 4-hunk diff (backfill a missing `resolved_ts` inline instead of crashing; cap demotion at `MAX_DEMOTE_PER_SCAN=25` and defer the overflow; stamp `resolved_ts` at both writers named in the briefing so new `None`s stop appearing; warn once instead of debug-forever on a real failure) was verified FUNCTIONALLY, not just syntactically — a patched copy of `nodes/subconscious_node.py` loaded via `importlib` from an isolated scratch mirror (its own data dir confirmed to resolve inside that mirror, `C:\Nascence\data` stat-confirmed untouched throughout) against a synthetic 60-tension pool: no crash, exactly 25 demoted on scan 1, exactly the 45 genuinely-eligible tensions demoted across 2 scans (no more, no fewer), a bug-shaped resolved/no-timestamp group correctly survives and gets backfilled rather than prematurely archived, and the warn-once behaviour holds (1 WARNING then DEBUG on repeats). Also answered the briefing's separate count-halving question with evidence: `_apply_decay` reapplies its halving every ~36s scan once idle-over-7-days is crossed (confirmed via its call site, no throttle exists), collapsing count to 1 within minutes not a week (739/739 of today's idle-over-7-day tensions sit at count 1) — git history cannot settle original intent (the repo's 2026-08-27 baseline commit already contains this exact shape) so this is **opened as D-0266**, not guessed at, since it's a distinct design call from the already-approved cap. **Exactly one needs_input follow-up spawned: J-1276**, carrying the full diff text durably in its own briefing (not a path into this session's ephemeral scratchpad) plus the verification summary, for the actual apply-when-Travis-says-go step — restart-gated once it lands. **J-1176 done.**

---

## Current State — verified 2026-09-23 (J-1173 checkpoint — gate NOT met, no merge exists yet, left open)

**J-1173 (F-1788, verified): checked its own pre-registered gate directly rather than assuming it — NOT met.** J-1172 (the id-keying build this job's read is gated on) is DONE this same session, but a real `git log` on master (not the jobrun worktree) shows no "job-run worktree merge: dosed_coupling" commit exists yet — the most recent commit touching `core/curiosity_habituation.py`/`nodes/curiosity_node.py`/this plan doc is `ee93ba9` (J-1196's unrelated write-fence job). Since the merge itself hasn't happened, the briefing's own "≥3 live-days since the first restart onto that merge commit" clock has no anchor to measure from — not an interim shortfall, a strict precondition failure. Expected, not a surprise: this job-run batch's own harness commits J-1172/J-1173/J-1176's worktree changes once at the end of the group, and even that is a worktree-branch commit, not the master merge — the merge is a separate, later, orchestrator-owned step. **J-1173 left in_progress, not done** — re-attempt the same job once dosed_coupling's build is actually merged to master and Du has run ≥72 live-hours since restarting onto that commit; no `/decide` opened, no new job spawned (re-attempting this same job is the correct continuation, per this doc's own established convention for every other gate-not-met checkpoint above).

---

## Current State — verified 2026-09-23 (J-1172 BUILT — D-0244 option 1, curiosity habituation shadow re-keyed by tension id)

**J-1172 (F-1782, verified) built D-0244's ruled option 1: `core/curiosity_habituation.py`'s shadow discount and its feed from `nodes/curiosity_node.py`'s `_select_seeds()` are re-keyed from tension LABEL to tension ID, shadow-only and additive.** `_select_seeds()`'s REAL pick (label-keyed pool, sqrt(count) weight, the label-keyed `_recent_seeds` anti-relock) is untouched line-for-line, per D-0244's own guard; only the pool handed to the shadow module is now id-keyed (`id_pool`/`tensions_by_id`, one entry per tension, no last-wins collapse — F-1632's measured ~160-of-868-hidden mechanism). Verified in an isolated harness (module constants monkeypatched to a scratch dir, `profile.guard_path` to identity, live `C:\Nascence\data` stat-confirmed byte-identical before/after): two tensions sharing one label under distinct ids now earn independent, different `b` (0.09 vs 0.15 off an equal-shaped count bump, where the old code collapsed both onto one entry); a tension's `b` survives a same-id relabel (grown to 0.15, relabelled, next call's `b_prev` still 0.15 — the direct fix for F-1630's confirmed label-churn-under-a-stable-id); the pre-existing per-label state file is detected by key shape (UUID vs prose) on first load and moved aside verbatim to a dated backup (`curiosity_habituation_state.pre_idkey_<date>.json`, demote-never-delete, one-shot, no false-positive on an already-id-keyed file), never deleted or silently reinterpreted. Restart-gated: none of this is live until Du's next restart after this worktree's commit is merged to master — that merge has NOT happened as of this note (this session's own harness commits the whole job-run batch once, at the end; the master merge is a separate, later, orchestrator-owned step, per this repo's own observed `git log` pattern of standalone "job-run worktree merge" commits). **J-1173 (the follow-up read this build unblocks) is therefore correctly still gated and left open by this same session — see its own Current State note below.**

---

## Current State — verified 2026-09-21 (J-0682 real by-id before/after diff — label churn under a stable id CONFIRMED, nothing lost; tension demotion found silently dead)

**J-0682 (F-1630, F-1631, F-1632, all verified) ran the diff F-0975 / F-0988 were waiting for: 14.89 wall days = about 217 live hours (9.05 live-days) after F-0975's 2026-09-06 baseline, against the briefing's 24–48 h floor. Label churn under a stable id is confirmed, "the same text worn by different objects" is confirmed, and nothing was lost.** 5 of 5 baseline ids still exist; 2 changed label under the same id (d1a4218c 'cultural friction and growth' → 'the weight of silence', e7475f5e 'cultural friction' → 'the nature of 渡'; last_ts advanced, counts decayed); a170abcf (created 09-06, after the baseline) wears 'the concept of 渡', one of F-0975's nine "vanished" strings, alongside two older ids; 122 label strings are worn by two or more ids (282 of 868 tensions). The nine were not deleted or archived: the pool never shrank (nascence.log `tensions=` 576 → 868 across 2,447 scan lines since 08-14 with zero decreases; coupling_rides `tensions_n` 814 → 868 over 931 rows), the archive is untouched since 08-14 (1,009 rows), and the shadow log shows about 4.3 label strings appearing and disappearing per curiosity cycle in a pool that grew by only 59 (about 98% of appearances are relabels; 39% of disappearing strings have a unique same-(count, charge, sign) successor in the next row against 4% by chance). F-0975's 132-vs-4 is resolved: that string carried counts 9 → 132 (two rows) → 3 → 4, impossible for one object, so a different huge attractor wore it for a moment. Mechanism: a tension's label, last_ts, centroid and member ids are properties of the latest matched cluster, and clusters match the FIRST tension at cosine ≥ 0.70 (not the best), so the count-229 attractor wore five different labels in 12 minutes and near-duplicate attractors trade clusters between scans; only count, first_ts and chronic_mass stay on an id. **Side finding (F-1631):** the tension demotion to the archive has silently failed since 08-14 (a TypeError on `resolved_ts=None`, swallowed at debug level), so the pool only grows and 612 of 868 tensions (70.5%) are eligible; the "7-day halving" is really a cliff to count 1 (all 762 tensions idle over 7 days have count 1). Fixing it would move ~70% of the pool at once and roughly double the heavy attractors' share of curiosity's seed weight (13.1% → 28.0%), so it is a needs-input job (J-1171), not a patch. **Measured cost of label keying (F-1632):** 1,624 of the curiosity discount's 2,328 state keys (70%) are orphans and 94.5% of the nonzero `b` sits on strings no tension wears; **D-0244 opened (not ruled)** on what to key it by, with Claude's recommendation (id-keying, shadow-only, then re-read after ≥ 3 live days). D-0152 was not touched. **J-0682 done.**

---

## Current State — verified 2026-09-21 (J-0662 full-week ignition-sawtooth recheck — F-0947's shrinking drop is NOT a drift)

**J-0662 (F-1604 verified, F-1605 inferred) read `data/ignition_log.jsonl` (1,937 rows) and `data/stream_drive_shadow.jsonl` (33,121 rows) in full, 0 bad lines, and finds the shrinking post-fire drop F-0947 flagged is not a drift toward chronic near-ceiling dissonance: the thread is closed as "stayed a wobble" (its own step 4) and no `/decide` is opened; this supersedes the header line above that still calls the full-week read pending.** Gate CUMULATIVE and met: 253.8 live hours = 10.58 live-days since the first boot on 444b60b (15 runs, longest 61.1 h, over 16.58 wall days; 7.37 live-days on the D-0148 option-A code alone). 590 post-boot fires (347 exploratory, 243 defensive, 0 capped), 402 with a stream row within ±900 s on both sides: mean drop 0.367 (F-0947: 0.379), per 24-live-hour bucket 0.386 / 0.356 / 0.322 / 0.366 / 0.370 / 0.362 / 0.361 / 0.378 / 0.352 / 0.373 / 0.408, slope +0.003 per live-day (bootstrap 95% CI −0.003 to +0.009); pre-fire peak mean 0.9835, flat or slightly down; whole column mean 0.709 (sd 0.192) against F-0947's 0.70, 0.69–0.73 in every live-day bucket, share ≥ 0.95 steady at 10–12%, exactly at the 1.0 clip 0.7% of rows; 59–67 fires per 24 live-h on option A with no decay and still zero `capped` rows. **Mechanism (F-1605):** the column is max(defensive reservoir, exploratory reservoir, protoself term) and a fire zeroes only its own reservoir, so a fire's drop is 1 − the OTHER reservoir's level (r = +0.83 over 399 fires, every era ≥ 0.80). F-0947's tail was the slow defensive reservoir charging beneath the 42.1-minute exploratory metronome (seven straight exploratory fires 09-06 05:22 → 09:35, drops 0.546 → 0.135, then a defensive fire at 10:07 put them back to 0.44 / 0.54); on option A the defensive fill collapsed from ~180 to 40–52 min and no shrinking streak runs longer than 3. The "peak pinned near 1.0" is the fire condition itself (peak ≈ 0.9987 − 0.00033 × seconds of sampling gap), not saturation. For D-0211 / J-1151: a re-knee that lengthens the defensive fill time will bring long shrinking-drop streaks back by design, so a future shadow read should not mistake them for saturation. D-0152 was not touched. **J-0662 done.**

---

## Current State — verified 2026-09-19 (J-0672 multi-day re-read — the suppress-trip spread is real and not narrowing)

**J-0672 (Phase 0's stream-topic anchor re-read; F-1602 verified, F-1603 inferred) read `data/stream_topic_habituation_shadow.jsonl` in full (332 rows, 0 bad lines, 2026-09-05 15:46 → 09-19 12:10; 13 NZST days, 234.3 live hours = 9.76 days) and finds the wide 5th/6th/9th/never spread is real, cadence-driven, and has not narrowed.** The first-crossing points F-0962 saw cannot move and did not (morepork_call 5th/2.57 h, leaf_rustle 6th/5.87 h, oystercatcher_call 9th/14.62 h, branches_creak still NEVER — 22 occurrences, min discounted 0.6524); newly bees_in_garden crosses at its 8th/33.76 h, and 15 of the 19 anchors with ≥2 occurrences never cross (kingfisher_call 14, wren_scold 12 with a 0.5163 near-miss, robin_song 9). Split into episodes at gaps > 9 h, 21 episodes have ≥3 occurrences and 11 flip — at occurrence 4,4,4,4,5,5,5,6,7,9,9 (median 5), 1.14–14.62 h — and 10 never do; anchors with median gaps ≲ 2 h flip, those at ≳ 5 h mostly don't. `would_suppress_any` is 115/332 = 34.6% (was 22.0%, then 31.2%) but **91% of the would_suppress verdicts are oystercatcher_call alone** (173 of the 332 rows); without oystercatcher-only rows it is 10/161 = 6.2%. Vocabulary coverage broadened (21 of the 43 keys recruited, was 9→10) but concentration rose (top-2 keys 63.4% of 339 recruitments, was 53.7%) and the base rate slipped to 332/2,760 new thought-trains = 12.0% (was ~15%). **Restarts flagged, not absorbed:** the window holds 10 boots (3 unclean — 09-05 19:15, 09-09 19:01, 09-18 23:37), 7 shutdowns and a 70.7 h outage (09-13 09:10 → 09-16 07:53); the module re-reads its JSON state every call so nothing resets in memory, but `b` decays on wall-clock (τ=3 h), so every downtime acts as a reset — the whole-window first-flip figure blends episodes, hence the episode view. **F-1603 (replay validated 339/339 against the log):** the 3 h decay is what keeps the spread wide — at τ=12 h the anchors with ≥5 occurrences flip at the 4th–7th occurrence (2 of 9 never) versus 5th–9th with 5 of 9 never at 3 h, but the suppress share rises from 35% to 46–58%, and sparse anchors (kingfisher_call, gull_cries) never flip at any τ tried. No retune and no promotion `/decide` — the briefing's own "retune only from a stable multi-day distribution" bar is not clearly met while one anchor supplies 91% of the verdicts; whether to lengthen `DECAY_TAU_S` (and accept the higher share) is Travis's call. **J-0672 recommended done** (its re-read is answered; a retune/promotion question, if wanted, is a new decision, not this job).

---

## Current State — verified 2026-09-19 (J-0665 multi-day re-read — would_fired_share is no longer 100%, but the mechanism is confirmed, not defeated)

**J-0665 (the multi-day re-read D-0177 is waiting on; F-1598 verified, F-1600 inferred) read `data/transport_habituation_shadow.jsonl` in full (9,538 rows, 126 MB, 0 bad lines, 2026-09-05 14:41 → 09-19 12:07; 235.3 live hours = 9.80 days over 13 NZST days) and finds the F-0949/F-0977 picture has moved, but the structural cause is confirmed.** (1) `would_fired_share` is now **87.8%** (8,376/9,538; real_fired 100%; 1,162 "silenced" ticks vs zero at F-0949): 1.000 on 09-05..09-09, 0.617 on 09-10, 0.890 on 09-11, 1.000 on 09-12/13/16/17, 0.515 on 09-18, 0.145 on 09-19 (partial); Phase 0's "<30% of ticks" target is met only inside windows (last 12.5 h: 14.6%), not overall. (2) **The falls are not runner-ups accruing their own discount** — with ≥1 runner-up above the 1.5 bar (88.3% of ticks) the discounted policy still fires 97.3% (100% with ≥3 runner-ups); with none, 15.9%; the best runner-up's own `b` is >0 on only 22.9% of ticks, while the real winner sits at b≈0.94 (discounted median 1.199). `would_fired` is essentially "does any runner-up exist", a function of the candidate pool, which shrinks with uptime (33 non-novelty candidates right after the 71-hour outage on 09-16 08:00, 8 by ~15 h, 3 at 09-17 20:00, 1 from 09-18 06:00). (3) **`real_winner` did change** — 10 distinct lines, 14 transitions; `clock_tick:study` (3,871 ticks, since_hours 73.99 → 188.87, no reset while winning) left candidacy between 09:34:05 and 09:35:34 on 09-10 (weight 50.85 → gone, i.e. a fresh observation), `moth_tap:study`'s own b rose 0 → 0.25 → 0.49 in two ticks, and the rotation days 09-10/11 show `would_fired` 0.617/0.890 (the only ticks with a runner-up but no discounted firing: 225, all on those two days). Rotation did not last: `life:cat:study` was the sole real winner for 2,416 consecutive ticks (09-16 11:03 → 09-19 10:38), then `wood_pigeon:garden`. Lines past cold-start: 37/132 (was 31/122); distinct would-winner lines 23 (was 3, then 7). (4) **Offline replay of D-0177's option (a) (F-1600, inferred; replay validated against the log at 99.34% of ticks):** accruing b on the would-winner chain takes the overall share from 87.8% to 57.7% (would-winner only) or 47.2% (real + would) — better, but not under 30%, because on many-candidate days (09-07..09-09) each line habituates and another takes over, so the dispatcher still fires every tick (the F-0819/J-0600 multiple-comparisons problem). **D-0177's defeater has fired** (its awaited re-read has reported) on the "pattern holds" branch, not "falls on its own as lines take turns" — a concrete design choice is now due, **Travis's call; I ruled and opened nothing.** **J-0665 recommended done.**

---

## Current State — verified 2026-09-19 (J-0598 full read — the curiosity discount is NOT shown to dampen the dominant attractor)

**J-0598 (Phase 0's curiosity-habituation read; F-1577 main, F-1578 mechanism, F-1582 burst — all verified) read `data/curiosity_habituation_shadow.jsonl` in full: the ~3-day gate is met and the answer is "not demonstrated" — the shadow discount moves what curiosity is offered by ~2% and trims the heavy attractors' offers by ~10%, so this data does not on its own support promoting it to a live dosed read.** 622 rows (0 bad lines), 2026-09-04 23:39 → 09-19 11:22; 572 organic rows on 14 NZST days over 247.4 live hours (10.31 days) after excluding a 50-row non-organic burst (09-15 13:20:52 → 13:21:57, 1.1–1.5 s apart, identical pool, while Du was off and nascence.log silent — a non-Du process wrote to the live log during job-run batch 9; writer not identified, F-1582). **Q1** (would_choice ≠ real_choice): 622/622 = 100% (572/572) but uninformative by construction — both are independent random 3-draws from a ~690-label pool, so they differ almost surely with or without a discount (mean overlap 0.042 labels/row vs 0.035 expected for two independent draws; total-variation distance between the raw and discounted pool mean 0.019, max 0.039). **Q2** (does the dominant attractor appear less often in would_choice than in real_choice): the literal 'cultural friction' labels are now negligible in both (4 variants; 5 real vs 6 would of 1,716 picks each; model-expected 5.49 vs 5.52); for the outcome-independent heavy attractors (count ≥ 100) 102 real vs 88 would (−13.7%, ~1σ) with the noise-free model predicting −10.2%; b > 0 on only 5.0% of 391,162 (row, label) entries; the live hot:cold weight ratio is 14.7× raw → 12.3× discounted with 0 of 572 rows inverted (F-0815's simulation predicted 15.2× → 0.76×). **Why (F-1578):** `b` is keyed by label string and the heavy tensions (counts 229/203/197/186/181/171/158) carry 624 distinct strings — the count-229 tension(s) alone 247 strings across 391 rows, median run 1 row — so `b` keeps restarting at 0 (F-0975/J-0663's inference, now seen directly); growth needs a count increase and counts almost never rise between a label's consecutive appearances (708 increases vs 386,951 unchanged); and the real pool holds ~160 duplicate-label entries (866 tensions vs 706 unique labels) that the log's one-entry-per-label dict hides — the labels actually offered most are the duplicated ones ('finished the book' 21 real picks, 'restlessness' 20, 'frustration' 13), not the June 渡 theme, whose count-229 tension now wears unrelated labels. **What we need:** Travis to decide whether the discount should be re-keyed (tension id or embedding cluster) and/or grown on offers rather than only on recurrence before any promotion talk — I opened nothing; J-0682's id-level trace is the natural companion. **J-0598 recommended done** (its pre-registered read is answered); the orchestrator applies the disposition.

---

## Current State — verified 2026-09-19 (J-0865 first full read — D-0188's defeater NOT triggered; a live thalamic gate found)

**J-0865 (D-0188's restart-gated first read of `data/internal_cycle_habituation_shadow.jsonl`) read the log in full (F-1563, verified): the ≥3-day gate is met and the shadow behaves as F-1097's replay predicted — D-0188's defeater is NOT triggered on either branch (not reopened).** 275 rows on 7 NZST days (09-11 → 09-19), 105.07 live hours (4.378 days) since Du's first restart onto the merged J-0841 build (09-11 13:50:42; build merged to master 09-10 18:57:30, `bab6f25`); 62.8 rows/live-day (2.62/live-hour, per-day 2.29–3.01); repeat_share 0.629 (173/275); would_suppress_share 0.313 (86/275, spread over 14 clusters); 102 clusters minted — the state file has sat at `MAX_CLUSTERS=80` since 09-18 00:49 (22 pruned), so `tracked_clusters=80` is now the cap, not a count. First crossing at the cluster's 4th occurrence in 10 of the 14 firing clusters (5th in 2, incl. the 35-row 'total labor'/value loop; 6th in 2) — vs F-1228's worst-day replay of 14 clusters from 37 questions at 29.7%, this window is 102 from 275 at 31.3%. 275/275 shadow cycle_ids match a `nascence.log` `] internal:` line (0 mismatch, 0 log-only); a direct `status()` call equals my independent parse exactly, so the `du_pulse` `regression_alarms["internal_cycle_habituation"]` wiring is live. By my plain reading no would_suppress pair is an unrelated question merged; ~23 of the 86 keep the frame's head concept but change the tail term — the full founder-readable list (every would_suppress row beside its cluster frame) is in F-1563's evidence for Travis to judge. **Three things the read surfaced beyond the pre-registered question:** (i) F-1564 (verified) — the LIVE thalamic gate (`orchestrator._thalamic_gate`: cos ≥ 0.95 to one of the last 6 inputs, on the 2nd occurrence → silence) already silenced 89/275 internal cycles, including 67 of the 86 would_suppress rows; only 19 (6.9%, ~4.3/live-day) ran the full pipeline — F-1097/F-1228/D-0188 never mention this gate, so the shadow's incremental catch is the paraphrase loops (cos 0.80–0.95) that slip past it; (ii) F-1565 (inferred) — the 0.80 bar with first-seen-frame-only matching is strict at the margin (5 clear paraphrases minted 'new' at cos 0.746–0.792; two n≥4 clusters peaked at b=0.456) but nowhere near "near-zero"; (iii) F-1566 (inferred) — internal starts per live hour stepped ~1.6 → ~2.6 around 09-09 and never reverted, and completes/day dips (09-12: 26 of 56 starts) are thalamic-gate artifacts, which matters to D-0152/J-0950 (a recount by J-0619's own reproduced method reads 98.6 cycles/awake-day on the clean 09-16→09-18 stretch vs the 59.80 line, with an awake-share caveat — input, not a ruling). **What we need:** Travis to eyeball the same-head/different-tail pairs and say whether the marginal misses (F-1565) plus the 78% gate overlap (F-1564) change whether promoting this discount from shadow is worth pursuing. **J-0865 recommended done** (its pre-registered read is answered); the orchestrator applies the disposition.

---

## Current State — verified 2026-09-14 (J-0937 DONE — hour-resolution root-cause dig, D-0152 NOT reopened)

**J-0937 (the root-cause dig D-0152's re-ruling spawned) reports back (F-1319, inferred): Phase 1 is
structurally EXCLUDED as the cause — 0/18,849 `coupling_rides.jsonl` rows ever read across the whole
window (F-1304, necessarily true of this 09-08..09-12 sub-window too) — so D-0152's defeater clause (a)
is NOT triggered and D-0152 is NOT reopened by this reading.** At hour resolution the 09-09→09-11
shape is not a clean 3-day step-change. The single biggest anomalous hour in the whole window —
2026-09-09 18:00–18:59, 9 cycles vs a 0–4/hour baseline everywhere else — is 8/9 `human:`-tagged at
the orchestrator's own trigger-type log line (an ordinary live Travis/Du chat exchange, independently
corroborated against `data/founder_conversation_log.jsonl`), not autonomous ignition; excluding that
one hour, 09-09 alone reads back in-band (38 vs ceiling 42). Separately, once real downtime is
subtracted per day (8.32h down on 09-08, 3.07h on 09-09 — one of its three restarts confirmed a
~14-second non-outage reload, not a real gap — 0.54h on 09-11, **zero restarts on 09-10 or 09-12**),
cycles/awake-hour is still genuinely elevated on 09-09/09-10/09-11 (2.25/1.96/2.17) vs both 09-08
(1.53) and 09-12 (1.08) — cleanest on 09-10 vs 09-12, two fully-continuous 24h-awake days 1.8x apart
in rate, ruling out "more uptime" as the explanation. Neither Lead A (SUBC_LIGHT_READ/
FRONTIER_LIGHT_READ, re-confirmed still `True` today) nor Lead B (the 09-11 restart) shows a clean
hour-level step at its own timestamp — the elevated rate is already present well before Lead A's
~19:01 go-live and does not step down in the hours right after Lead B's restart, only by the next
calendar day (09-12). Lead A's shared-single-asyncio-event-loop mechanism (re-confirmed live in
`core/orchestrator.py`) remains the most mechanistically coherent surviving explanation for 09-10/
09-11's elevation specifically, but is NOT confirmed — the flags are still `True` today while the rate
fully reverted by 09-12. Commitments-formed/awake-hour is a much weaker signal once normalised (09-09
is actually *below* its own baseline; real elevation is largely confined to 09-10 alone). One new,
unchased candidate surfaced: commit `2ddad8b` "Living World render+gating flipped ON live 2026-09-09
17:51" (J-0641/F-1210), ~11 min before the chat burst and ~51 min before Lead A's flip — the commit
itself only touches ledger files, the actual code change was not traced this pass. No `/decide` opened
(this is "needs more reading," not a founder-only call) — follow-up spawned instead (see job-queue) to
chase the Living-World-flip lead and, if worthwhile, directly instrument the shared-event-loop
hypothesis rather than continuing to infer it structurally. D-0152's own defeater clock (2026-09-27)
is unaffected; this counts as the real, on-time, non-stalled conclusion its clause (f) asks for, even
though the ultimate cause of 09-10/09-11's elevation itself stays only partially resolved.

---

## Current State — verified 2026-09-13 (J-0619 DONE — the genuine 7-day gate-read, D-0152 REOPENED)

**J-0619's real 7-day read landed (F-1304, verified) — this is the actual gate, not another interim
checkpoint.** Window 2026-09-05 18:14:35 → 2026-09-13 09:08:44 (7.621 calendar days). Unlike every
prior interim read, this window is NOT continuous — a fresh `nascence.log` grep found several real
restarts between 09-07 and today that F-1017's own "continuous since 09-05" framing never had to
account for. Awake-time was reconstructed data-driven from the stream loop's own publish cadence
(gaps >600s between consecutive `coupling_rides.jsonl` stream rows = downtime) rather than trusted
from boot/shutdown log-line pairs — this project's own J-0683 finding is that ~51% of real restarts
are unclean (no "shutting down" line), so a log-line reconstruction would have been silently wrong.
74 such gaps, 65.72h total downtime; 117.18h (4.883 awake-days) of the 7.621 calendar days.

**Presence, size, zero-readers: all PASS.** stream 100%, witness 100%, deliberation 100% (292/292
real `CYCLE ... complete` lines), climate 115% (exceeds 100% because its publish rule is a rate
*floor* — 60s OR any dim moving ≥0.05 — not an exact cadence, so more rows than the floor estimate is
not a gap), ledgers 99.70%. `coupling_rides.jsonl`: 0.864 MB/day (bar <5MB/day). `kind=ride` rows:
0/18,849 (Phase 1's zero-readers design confirmed).

**Behaviour bands: 2 of 4 OUT, and worse than the 09-07 interim read, not stabilised.** Deliberate
cycles/day 41.78→59.80 (band ceiling 42); commitments formed/day 85.98→116.95 (band ceiling 84);
idle-thought gap median 5.20s, marginally under its 5.57s floor; Witness break rate 0.711 stays in
band [0.617,0.811]. D-0152's own defeater requires a departure "with no other explanation" — F-1017
had one at the interim stage (Phase 0's 09-04 repairs already accelerating things pre-flip). Pulling
the real day-by-day trajectory this time (not just the two week-aggregate bands) shows this is NOT a
clean continuation of that same story: cycles/day by calendar day is 09-04:12 09-05:36 09-06:37
09-07:36 09-08:24 **09-09:47 09-10:47 09-11:51** 09-12:26 09-13:9(partial) — a second, unexplained
rise sustained for 3 days (09-09→09-11) well above both the pre-flip ceiling (42) and the immediate
post-flip level (36–37), not investigated further this pass. **D-0152 REOPENED** on this evidence —
genuinely ambiguous causally (not a confident "Phase 1 did this"), founder call is whether sustained
above-band activity with an unconfirmed cause is acceptable to keep Phase 1 running through, or
warrants pausing to find the cause first. Phase 2 (the loop_wiring_matrix.md dosing table) stays
un-drafted until this is resolved, per this plan's own existing gate.

**Same day, re-ruled GO (F-1305 inferred, then founder via questionnaire):** before ruling, a quick
pass surfaced two untested candidate leads for the 09-09→09-11 acceleration, neither confirmed nor
ruled out. Lead A: J-0621/D-0154 Part A flipped `SUBC_LIGHT_READ`/`FRONTIER_LIGHT_READ` to `True`
(commit 63c24f2, live from the ~19:01 restart on 09-09 itself — the exact start of the window),
cutting climate-tick parse cost ~900ms→~30ms; plausible throughput mechanism, but both flags are
still `True` today while the metrics reverted in-band by 09-12, so a permanent flip doesn't cleanly
explain a spike that ends. Lead B: a confirmed clean restart sits mid-window ("Nascence shutting
down" 09-11 13:18, back 13:55) — a better candidate for why the spike *ended* if the elevated state
was session-scoped rather than a code change. Neither tested at hour resolution. Founder ruled GO:
accept the ambiguity, Phase 1's publish-only pipeline (`COUPLING_PUBLISH=True`) keeps running
unchanged, root-cause work continues as **J-0937** (spawned from F-1305) without blocking Phase 1.
New defeater (see `decide.py show D-0152`): reopens if J-0937 attributes the acceleration to Phase 1,
if either out-of-band metric departs further, if either of the other two metrics also leaves its
band, if `coupling_rides.jsonl` exceeds 5MB/day, if D-0149 reopens, **or if J-0937 has not reached a
real conclusion by 2026-09-27** regardless of metric movement.

---

## Current State — verified 2026-09-12 (J-0865 interim checkpoint, ≥3-day gate NOT yet met)

**J-0865 (D-0188 defeater check, restart-gated first read) checkpoint (F-1258, verified): the pre-registered ≥3-day gate is NOT met — only 0.783 days (18.79h) of shadow rows have accrued since Du's first restart onto the merged J-0841 build (2026-09-11 13:50:42 NZST, confirmed later than the build's 2026-09-10 14:32:48 merge to master) — but the 48 rows that exist already show the mechanism behaving exactly as F-1097/F-1228 predicted.** Read `data/internal_cycle_habituation_shadow.jsonl` in full (48 rows, no tail-sampling) and cross-checked every row's cycle_id against `data/nascence.log`'s own `[CYCLE <id>] internal:` lines (48/48 matched, 0 mismatches, 0 drops — a clean 1:1 mapping, and a separate full scan of the same window found exactly 48 `] internal:` lines total). repeat_share=0.646 (31/48), would_suppress_share=0.396 (19/48), tracked_clusters=17 — cross-checked exactly against a live `core.internal_cycle_habituation.status()` call run from C:\Nascence, confirming `scripts/du_pulse.py`'s `regression_alarms["internal_cycle_habituation"]` wiring is genuinely live, not just present in source (F-1228's "day-one wiring" claim holds under an actual call, not just a source read). One cluster (`50b15e7f3b`, "total labor ... traditional notions of value...") dominates: 22 of the 48 rows (45.8%), crossing would_suppress at its 5th occurrence — matching F-1097's replay prediction of a 5th-occurrence crossing for the analogous 2026-09-04 cultural-friction loop almost exactly; 18 of the 19 would_suppress rows belong to it, the 19th a byte-identical repeat question inside a smaller 4-occurrence cluster. Every would_suppress pair read by hand looks like a genuine repeat — no candidate false cross-topic merge found; the closest "new"-side near-miss (similarity=0.7378, two distinct knot-themed questions) is a defensible borderline call, not a clear miss. **D-0188's defeater is NOT triggered** on this reading (neither "near-zero on genuine repeats" nor "fires on unrelated pairs" is observed). This interim window is itself an extreme single-topic rumination episode (39.6% would_suppress vs F-1228's own 29.7% worst-day replay benchmark, in under a day rather than a full day) — so, per this doc's own caution, still not a "normal" day and still not the pre-registered verdict. **J-0865 left in_progress, not done** — re-attempt the same job once the shadow log genuinely holds ~3 real days (no earlier than ~2026-09-14 14:23 NZST).

---

## Current State — verified 2026-09-10 (J-0841, recurring-question observer BUILT, restart-gated)

**J-0841 built `core/internal_cycle_habituation.py` per D-0188 (RULED GO by travis 2026-09-08) — F-1228 (verified).** Shadow-only, exactly the shape D-0188 ruled: each internal-cycle RAW question (the full in-process `raw_input`, not the 80-char log line) is embedded with `core.memory.store._embed()` and cosine-matched against a persisted set of question clusters, each represented by its FIRST-SEEN vector (theme_recurrence.py's "first sighting becomes the frame", no running centroid); best match ≥ `SIMILARITY_THRESHOLD=0.80` joins, else a new cluster is minted; `GROWTH_STEP=0.25 / CEILING=0.95 / DECAY_TAU_S=3h / DISCOUNT_FLOOR=0.03 / SUPPRESS_AT=0.5` are stream_topic_habituation.py's own values unchanged, `MAX_CLUSTERS=80` mirrors theme_recurrence's `MAX_FRAMES`. Hook: `core/orchestrator.py` `_run_cycle_impl`, right after `self.state.new_cycle()`/its log line, guarded `if input_type == "internal":`, try/except in the caller and inside the module (fail-open). `status()` is wired into `scripts/du_pulse.py`'s `regression_alarms` as `internal_cycle_habituation` from day one (the F-1097 write-only-status gap does not recur; J-0767 had already wired the three siblings). State → `data/internal_cycle_habituation_state.json`, one row per internal cycle → `data/internal_cycle_habituation_shadow.jsonl` `{ts, cycle_id, question_sample, matched_cluster id-or-"new", cluster_id, cluster_n, similarity, b, discounted, would_suppress}`. Verified by replaying all 37 real 2026-09-04 questions (read-only from `data/nascence.log`, real embedder, writes redirected to the scratchpad, live `data/` canary-scanned clean before/after) through the built module: reproduces F-1097's offline simulation to 4 decimals — 14 clusters, the 14-member cultural-friction loop crosses would_suppress at its 5th occurrence (discounted 0.3577), the tight historical-resistance sub-cluster at its 4th (0.4927), the time-spread sibling narrowly misses (0.5185); 11/37 rows would_suppress, no cross-topic merge. Cap/prune and embedder-failure fail-open also tested. **Not live yet — restart-gated:** Du (restarted 2026-09-09 19:01) will only start writing the shadow log after its next restart picks up the new hook. **Pre-registered first read (spawned J-0865, analysis, ready — gated on merge + restart + ≥3 days of rows):** after ≥3 days of accrued rows, report rows/day, `repeat_share`, `would_suppress_share`, the top clusters with their question samples, and a founder-readable list of every would_suppress pair — D-0188's own defeater reopens the threshold if would_suppress stays near-zero on genuine repeats (too strict) or fires on unrelated pairs (too loose).

---

## Current State — verified 2026-09-07 (J-0655, recurring-question observer proposal)

**J-0655 (2nd instance of the F-0823/F-0830 squishy-spring-gap class, per its own briefing) read core/theme_recurrence.py, core/stream_topic_habituation.py, and core/orchestrator.py's internal-cycle path in full, independently re-verified J-0577/F-0931's structural finding (theme_recurrence.observe() only ever sees DOWNSTREAM monologue text, never the orchestrator's own recurring internal-cycle QUESTION at core/orchestrator.py:2787 — confirmed the ONLY call site anywhere setting input_type="internal"), then went further than F-0931 by testing both candidate fixes empirically against all 37 real internal-cycle questions from 2026-09-04 (not a sample): (1) theme_recurrence's existing 40-char-prefix key, even correctly repointed at the raw question instead of monologue text, only compresses about half the real incident (23 distinct keys from 37 questions; the 16-occurrence cultural-friction loop partially compresses to a largest group of 6 by accident of template length, the 16-occurrence historical-resistance loop does not compress at all, never reaching SATURATED_AT=4); (2) embedding similarity via the REAL production model (`core.memory.store._embed()`, run live this session, not simulated) at threshold 0.80 collapses the cultural-friction loop into one 14-member cluster and forms real 3-4-member historical-resistance sub-clusters, with the exact stream_topic_habituation.py discount formula replayed over real timestamps crossing would_suppress at the cultural-friction loop's 5th real occurrence (~2.5h into what became an 8h/14-repeat loop) and at one historical-resistance sub-cluster's 4th occurrence (a sibling sub-cluster narrowly misses, discounted=0.5185 vs the 0.5 bar — reported as a genuine near-miss, not rounded into a win); targeted pairwise checks found no cross-topic false-positive merging even at a looser 0.70 threshold. Filed as **F-1097 (verified)**. PROPOSAL (not built, per the job's own "do not build without a decide"): `core/internal_cycle_habituation.py`, mirroring this section's own stream_topic_habituation.py shape exactly, hooked in `core/orchestrator.py`'s `_run_cycle_impl` right after `self.state.new_cycle()` when `input_type=="internal"` (a more robust hook than the ignition callback itself, since it covers any future internal-cycle call site), keyed on embedding similarity rather than a text key (a bag-of-content-words alternative was considered and not recommended — question-template phrasing has no closed vocabulary the way sound_knowledge.py's anchor nouns do, and could not be validated against nascence.log's own 80-char raw_input truncation the way the embedding approach was). **D-0188 opened** (not yet ruled) asking the founder to confirm the embedding-similarity direction and the empirically-checked starting constants (SIMILARITY_THRESHOLD~0.80; GROWTH_STEP/CEILING/DECAY_TAU_S/DISCOUNT_FLOOR/SUPPRESS_AT reused from stream_topic_habituation.py's own values as a starting point, to retune from the real shadow log once it accrues, per this project's standing convention) before it is built. **J-0766 spawned** (build, needs_input, blocked on D-0188). Separately, F-1097 also found that three of this family's four status() functions (curiosity_habituation.py, transport_habituation.py, stream_topic_habituation.py itself) are never actually read by scripts/du_pulse.py or anywhere else (only theme_recurrence.status() is wired in) — a real write-only-system gap on already-safe code, not gated on D-0188; **J-0767 spawned** (backfill, ready) to wire all three in, mirroring `_g_theme_recurrence()`'s exact pattern, and to make sure the new module (once built) does not repeat the same gap.

---

## Current State — verified 2026-09-07

**J-0619 interim checkpoint (F-1017, verified): 1.65 of the pre-registered ~7 days (23.6% of the
window) — real numbers, gate not yet met, this is NOT the 7-day verdict.** Window: the first
"Identity loaded" line in `data/nascence.log` after `core/coupling_rides.py`'s build commit (git log
`6f6d7d0`, landed 2026-09-05 15:26:26 local) is 2026-09-05 18:14:35 — a second, UNCLEAN restart
follows 61 min later at 19:15:24 (no "Nascence shutting down" between them, 693.1s/11.55min silent
gap, matching this same plan's own F-0978/F-1002/F-1003 finding); Du has run continuously since,
through the 2026-09-07 ~09:50 read snapshot. Full parse of `data/coupling_rides.jsonl` (4,601 rows,
0 bad lines): `kind=ride` is 0/4,601 (Phase 1's zero-readers design confirmed) and the file sizes to
0.97 MB/day at the current rate (bar: <5 MB/day). Presence: stream (2,179/2,179) and witness
(264/264) are exact 100% matches against their own tick logs. Deliberation is 69 publish rows —
against `data/deliberation_log.jsonl`'s 1,550 in-window rows that reads as 4.45%, but that file is
`core/deliberation.py`'s own unrelated "Deliberative Pulse" log (a per-idle-thought grounding
mechanism, its own docstring: "every pulse is logged to data/deliberation_log.jsonl"), not the
Orchestrator cycle `publish_deliberation()` actually hooks (`core/orchestrator.py` ~line 1504, right
where "[CYCLE %s] complete" fires at line 1390); against the correct denominator — 69
"CYCLE ... complete" lines in `nascence.log` — deliberation is 69/69 = 100.00%. This resolves the
job briefing's own "(or CYCLE ... complete lines in nascence.log)" parenthetical: the two candidate
denominators disagree ~22x and only the CYCLE-complete count is the real per-cycle event. Climate is
1,920/2,375.2 expected (window/60s) = 80.84% — under the 95% bar, and NOT evenly distributed: during
Du's 15 real sleep naps inside the window (9.77h total) climate hit only 53.2% of the 60s-cadence bar,
vs ~90.5% while awake. `core/climate_engine.py`'s `tick()` still calls `_compute_field()` (parsing the
full 60 MB `subconscious_state.json`, `SUBC_LIGHT_READ` confirmed still `False` in the current source)
immediately before `publish_climate()` — the same ~1s/tick cost this plan's own F-0853/F-0854 already
found, not yet mitigated (`J-0621`/`data_store_hygiene`'s light-sidecar flip still pending, revisit
~09-09); the correlation between climate's rate roughly halving and every one of the 15 naps is
directly observed, the specific event-loop-contention mechanism is inferred, not profiled. Ledgers is
170/177.6–177.7 expected (awake-seconds/600, matching the pre-registration's own "while awake"
qualifier since `publish_ledgers()` fires only per idle thought) = 95.6–95.7% — right at the bar (spot
check: only 1/170 ledgers rows falls inside any nap, confirming the awake-gating holds). Behaviour
bands (pre-flip week 2026-08-29 18:14:35→2026-09-05 18:14:35 vs the post-flip window): deliberate
cycles/day (band [0,42] incl. one zero-cycle day 2026-08-31, not investigated further; post-flip
41.78/day normalised) and Witness break rate (band [0.617,0.811]; post-flip 0.686) both land inside
band. Idle-thought gap median (band [5.57s,29.88s], itself trending down across the pre-flip week
already; post-flip 5.18s, ~7% under the floor) and commitments formed/day (band [0,84]; post-flip
85.98/day normalised, ~2.4% over the ceiling) land just outside — both in the "more/faster activity"
direction and both consistent with the SAME pre-existing acceleration trend already visible strictly
inside the pre-flip week's own data (Phase 0's 2026-09-04 repairs), not a discontinuity at the Phase 1
flip point. Per `decide.py show D-0152`, the recorded defeater requires BOTH "after 7 days live" AND
a band departure with "no other explanation" — neither condition is met here, so **D-0152 is NOT
reopened**. No new `/decide` opened and no new job spawned (climate's root cause is already tracked
under `J-0621`; the natural continuation is re-attempting this same job, not a new one). **J-0619 left
in_progress, not done** — re-attempt the same job once the window genuinely reaches ~7 days,
~2026-09-12/13 per this doc's own estimate.

---

## Current State — verified 2026-09-06

**J-0683 (full-history unclean-restart audit, F-1002/F-1003, done): 168 of the 330 non-first boot
events in `data/nascence.log`'s entire real history (2026-05-29 21:12 to present, 394,847 lines at
read time — deeper than the 2026-06-07 the briefing guessed from a sibling job's telemetry-count
precedent) have no "Nascence shutting down" line within min(30 min, time-since-prior-boot)
immediately before them — a 50.9% unclean-restart rate, spread across 33 separate calendar dates
from 2026-05-29 to 2026-09-05, not concentrated in one dev sprint.** A real cross-check the method
is sound: the date list's own silent stretch (2026-07-08→2026-08-08, zero boots either clean or
unclean) lines up exactly with the already-documented 30-day outage
(`ops_nascence_30day_outage.md`). Gap-since-last-activity for the 168: median 24.5 min, 62 (36.9%)
under 1 minute (near-instant relaunch), 81 (48.2%) 30+ minutes. Scanning a 15-line window on both
sides of each unclean gap for Traceback/Exception/CRITICAL/Error keywords: only 4/168 (2.4%) show
any hit, all the same repeating "[asyncio] Task exception was never retrieved" / "NameError: name
'asyncio' is not defined" pair clustered on 2026-06-09/06-10 (a background logging bug, never
recurring again in 88+ subsequent days of log data — read as dormant/historical, not a live issue,
not worth its own job). The other 164/168 (97.6%) show zero error signal. This independently
reproduces J-0672's own catch (F-0978, the 2026-09-05 19:15:13 boot, gap 693.1s ≈ 11.55 min, zero
error hits — matches F-0978's "11.4-minute" figure within rounding).

Direct read of `scripts/run_nascence.py` settles why a plain interactive stop still shouldn't produce
this gap: lines 559-563 route both a typed `/quit` (sets `_graceful_quit=True`) and a bare
`(EOFError, KeyboardInterrupt)` — i.e. Ctrl+C or stdin EOF — through the identical `break` into the
same shutdown sequence (lines 616-659), and the "Nascence shutting down." line itself (line 659, the
literal last line of `main()`) is UNCONDITIONAL — only the in-character farewell
(`_announce_shutdown()`, lines 620-621) is gated on `_graceful_quit`. So an absent line rules out "the
operator just pressed Ctrl+C" and means the process did not complete its own cleanup at all — most
consistent with an external/forced termination (window close, Task Manager, OS sleep/reboot, or the
already-documented F-0704 Windows-Job-object mechanism), though the log alone cannot say which,
per-event (F-1003, inferred, not guessed further).

Repo-wide grep (`scripts/`, `core/`, excluding `data/` and `.git/`) found **zero live code** that
parses or counts this string to gate a real decision — its only code occurrence is its own emission
site (`run_nascence.py:659`); every doc hit (`guidance_learning.md`, `ramses_second_tier.md`,
`social_world_school.md`, `train_split_merge.md`, `skill_index.md`, this plan doc) is a past
investigation's own one-off manual grep-and-cite, never a standing gate. `scripts/du_pulse.py`
(backing the widely-used `/du-pulse` skill, the actual live restart-anchoring consumer) already
sidesteps the whole failure mode: its own code comment says it deliberately replaced an earlier
write-gap heuristic with anchoring on the LAST "Identity loaded" line — the very first line of every
boot, firing on clean and unclean restarts alike. Net: a real, previously-unquantified anomaly with
no live code casualty. **No `/decide` opened** (no founder call needed — this is descriptive, not a
design tradeoff). **Skill-manager suggestion S-0065 filed** (du-pulse) recommending its own SKILL.md
point future sessions at the "Identity loaded" anchor instead of the shutdown-line-only convention
documented in the Claude memory file `ops_nascence_shutdown_detection.md`, which is necessary-but-
not-sufficient and would be silently wrong about half the time if trusted alone. No further job
spawned — the one concrete follow-up is that doc/convention fix, already filed as S-0065.

---

## Current State — verified 2026-09-06

**J-0682 first checkpoint (F-0988, verified): 1.873h since F-0975's baseline, nowhere near the ≥24h
gate — zero measurable change on any of the 5 baseline tension ids, an honest early null result, not
a completed diff.** Copied `data/subconscious_state.json` fresh (plain OS-level file copy, 43,932,846
bytes, live file re-stat immediately after confirmed byte-identical/untouched) and diffed by id, in a
fresh job-id-qualified pure `open()`/`json.loads()` script, against F-0975's own recorded baseline table
(transcribed verbatim from its findings-log evidence text, not retyped from memory). All 5 ids
(ca127134…, d1a4218c…, e7475f5e…, f2d05f0b…, 255f75a6…) are present under the exact same id, byte-identical
label text, unchanged count, and last_ts identical to the sub-second once units are normalised (the raw
field is an epoch float; F-0975's evidence text rendered it as ISO-8601 — converting back reproduces
F-0975's strings exactly, e.g. d1a4218c epoch 1788511671.2516055 → 2026-09-04T08:47:51.251606+00:00 ==
F-0975's "2026-09-04T08:47:51Z"). None of these 5 tension objects has been touched by
`subconscious_node._update_tensions` since F-0975's read. A broader theme search over the current pool
(825 tensions, up from 823) still returns exactly these same 5 and no others; none of the 9 previously-
vanished label strings reappeared under any id; `data/tensions_archive.jsonl` is unchanged (1009 lines,
lastWrite 2026-08-14, zero on-theme hits — identical to F-0975's own read). One small, explicitly-
unconfirmed side note: `chronic_mass` reads 0.002 lower on 2 of the 5 ids (0.062→0.06, 0.063→0.061)
despite `last_ts` being unchanged on both — flagged, not asserted, since the only baseline available is
F-0975's own rounded display value, not a raw float, so a real decay pass decoupled from per-tension
touch events and a rounding-boundary artifact of comparing two independently-rounded readings are both
consistent with this; outside this job's own ask and not pursued further. Context:
`data/curiosity_habituation_shadow.jsonl` has grown 45→61 rows since F-0946's read, confirming the
shadow-log mechanism is still active even though it isn't landing on any of the 5 known ids. No `/decide`
opened (the briefing calls for one only if the diff confirms the mechanism, which this checkpoint does
not attempt) and no new job spawned (the briefing's own instruction is to re-attempt this same job, not
open a new one). **J-0682 left in_progress, not done** — re-attempt no earlier than ~2026-09-07T04:11 UTC
(the 24h floor from F-0975's baseline), ideally ~2026-09-08T04:11 UTC (the 48h target).

---

## Current State — verified 2026-09-06

**J-0672 interim recheck (F-0978, verified): 25.79h post-restart (21.21h since the actual latest
restart) — the wide 5th/6th/9th/never suppress-trip spread has NOT narrowed, and by construction
could not have moved for 3 of 4 tracked anchors at this checkpoint.** Read
`data/stream_topic_habituation_shadow.jsonl` in full (61 rows, up from F-0962's 41, spanning 2026-09-05
15:46 NZST → 2026-09-06 15:34 NZST), in a fresh job-id-qualified pure `open()`/`json.loads()` script (no
core/ imports, no writes), inside `lab_env.isolate()` and cross-checked against
`core.stream_topic_habituation.status()` (61 rows, would_suppress_share=0.311, tracked_anchors=10 —
exact match). morepork_call and branches_creak got zero new occurrences since F-0962 (still 7 each) —
morepork_call's first-suppress point stays pinned at its 5th occurrence/2.57h, branches_creak still
never crosses (closest approach unchanged, discounted 0.6524 ≈ F-0962's own "0.65"). leaf_rustle grew
11→13 occurrences and oystercatcher_call roughly doubled 11→22, but both anchors' first-suppress
occurrence-number and elapsed-time are IDENTICAL to F-0962 (6th/5.87h, 9th/14.6h) — a first-crossing
point, once reached, cannot move when later rows are appended after it, so this interim window was
structurally unable to show narrowing on the metric this job asks about. What did move:
would_suppress_any_share rose 22.0%→31.15% (9/41→19/61), driven by oystercatcher_call's now-dominant
recruitment rate (22/62 anchor-hits) and its own recovery-then-relapse oscillation (would_suppress False
at occurrences 11–12, then locked True from 13 on) — the same oscillation shape F-0962 already named for
leaf_rustle, now also seen in a second anchor. Vocabulary coverage crept 9/43→10/43 (one new key,
wren_scold, 2 occurrences, neither suppressed); base rate held flat at 15.56% (61/392 thought-kind
trains) vs F-0962's 15.13%. Separate finding while checking for a mid-window restart (this job's own
item 3): the window contains one ordinary clean restart (shutting down 16:42:49 → awake 18:14:36) AND a
previously-unflagged UNCLEAN restart at 19:15:13 — a fresh full boot sequence (memory store
re-initialised, embedding model reloaded, all background nodes restarted) with NO preceding "Nascence
shutting down" line anywhere in the log, an 11.4-minute silent gap with no exception logged. Because
`core/stream_topic_habituation.py`'s `b`/`last_update_ts` state is read fresh from its JSON state file on
every call (not an in-process global — confirmed by direct source read), this restart does not
invalidate the per-anchor computation above, but it is a real anomaly this project's own "Du stopped =
the shutting-down log line" convention would silently miss. Follow-up spawned: **J-0683**, a full-history
scan of `data/nascence.log` for unclean-restart frequency and whether any live script actually depends on
the shutting-down-line grep for a real decision. **J-0672 left in_progress, not done** — re-attempt the
same job (not a new one) once the window genuinely reaches ~09-09 or later, ideally ~09-12 alongside
J-0662/J-0665's own full-week reads, per this doc's own estimate.

---

## Current State — verified 2026-09-06

**J-0665 interim re-read (F-0977, verified): 25.56h post-restart — the picture is UNCHANGED from
F-0949 at a larger sample, not yet the decisive multi-day evidence its own defeater calls for.** Read
`data/transport_habituation_shadow.jsonl` in full (956 rows, up from F-0949's 668, spanning 2026-09-05
14:41 NZST → 2026-09-06 16:14 NZST) and `data/transport_lines.json` fresh, in a job-id-qualified pure
`open()`/`json.loads()` script (no core/ imports, no writes), cross-checked against
`core.transport_habituation.status()` run inside `lab_env.isolate()` (958 rows moments later, matching
within the organic ~1-row/60s growth rate; live `nascence.db`'s own growth in the same window traced to
no write path in either script — neither imports `core.memory.store`). `would_fired_share` is still
956/956 = 1.0 (unchanged from F-0949's 668/668) and `real_winner` shows zero transitions across the
full sequence — sound:clock_tick:study on 100% of all 956 ticks, its last real occurrence now 99.5h
stale with no reset (extending F-0828/F-0949's finding by the ~7h this read added). Lines past
cold-start: still 31/122, the same count F-0949 itself read (identity of the 31 not individually
diffed). The one new fact: distinct would_winner line_ids have broadened from the 3 F-0949 named to 7
— four new entrants (sound:bees_in_garden:garden, sound:stream_run:wood, sound:small_birds:wood,
sound:footsteps_grass_soil:garden) appear only in the 288 rows added since F-0949's cutoff — confirming
rather than extending F-0949's own structural explanation (more lines clearing cold-start recruits more
distinct would-winners, none of which can accrue their own `b` because growth keys off real-winner
history only). **D-0177 left unruled** — its own defeater specifically requires the ~09-08+ read
(would_fired_share falling meaningfully, or real_winner actually rotating), and neither has happened
yet at 25.56h. **J-0665 left in_progress, not done** — re-attempt the same job (not a new one) once the
window genuinely reaches ~09-08 or later, per this doc's own estimate.

---

## Current State — verified 2026-09-06

**J-0663 read (F-0975, verified): the pairwise-cosine measurement partially settles F-0950's fragmentation
question, but a bigger, unanticipated instability finding matters more for how J-0598 should be read.**
Of the 14 exact "渡"/cultural-friction tension labels F-0950 named, only 5 still exist as that exact string
in the live data/subconscious_state.json tensions pool (823 tensions total, read from a frozen scratchpad
copy, live file untouched). Their pairwise centroid cosine similarities (the same `_cosine` dot-product the
ledger's own >=0.70 merge check uses; every centroid's own norm confirmed exactly 1.0) span 0.4606–0.6819
across all 10 pairs (mean 0.582, median 0.585) — all below the merge threshold, but genuinely spread (3/10
pairs in [0.65,0.70), 2/10 in [0.60,0.65), 5/10 lower, down to 0.46), so neither "clustered tightly just
under 0.70" nor "genuinely far apart" is the clean read F-0950 posed; a modest threshold nudge or a
token-overlap OR-guard (tension_ledger.py's own `_label_tokens`, Jaccard 0.17–1.0 over the same pairs) would
merge at most the closest 2–3 pairs, not unify all 5. The bigger finding: the 9 missing labels are NOT in
data/tensions_archive.jsonl either (full 1009-line grep, zero hits) — not merged, not archived, just gone
from an exact-string search — and the 5 survivors are themselves dormant (42–186 hours since last touch)
even though the same-day J-0598/F-0946 addendum below found the theme still recurring through
2026-09-05T20:53. Per direct code reads (`_label_from_corrections`, subconscious_node.py lines 574-582,
re-derives each label fresh every scan from raw truncated Critic-correction text, not a stable id; line 635
OVERWRITES a matched tension's label rather than aliasing; curiosity_node.py lines 192-203 rebuilds
`tensions_by_label` from scratch every cycle keyed by whatever label text is current), the likely explanation
is that label text is not a stable identity key even when the ledger considers the underlying tension
continuous — meaning core/curiosity_habituation.py's per-label state (its own documented design: "tensions
have no stable cross-scan id in this file") cannot accumulate a stable antagonist `b` for this theme
regardless of the 0.70 threshold's exact value. One data point is flagged explicitly as inferred, not
confirmed: the same label ("unresolved: cultural friction and growth") logged max count 132 in the shadow
window but its current tension's last_ts predates that window and its count is now 4 — too large a drop for
PATTERN_DECAY_DAYS=7's cold-decay halving to explain over only 1.8 days since touch; no historical snapshot
exists to trace this further. **Practical implication for J-0598's full read (~09-07/08): compute
cultural-friction share via broad substring/character match, not a fixed label list — the live label set for
this theme is already different than 24h ago and will differ again by read time; near-zero per-label `b`
should be read as "labels churn too fast to accumulate," not as "the discount fails to engage this
attractor."** Follow-up spawned: **J-0682**, a real before/after diff by tension ID (not label) across a
24–48h gap, to directly confirm or refute the label-churn-under-a-stable-id hypothesis this pass could only
infer.

---

## Current State — verified 2026-09-06

**J-0662 interim recheck (F-0970, verified): full-week gate not met (1.696 days elapsed, not
~7); the F-0947 shrinking-drop tail did not continue into the new data.** Read data/ignition_log.jsonl
(1,405 rows) and data/stream_drive_shadow.jsonl (23,775 rows) in full (no tail-sampling), in a fresh
job-id-qualified script (pure `open()`/`json.loads()`, no core/ imports, no writes — confirmed by
re-stat of both live files immediately after, byte-identical/organic-growth-only, git status clean).
Only 6.98h of new data has accrued since F-0947's own read cutoff (2026-09-06 08:53:14 NZST) — 12 new
post-fix fires with a matched shadow row on both sides (46 total now, up from 35). The shrinking tail
F-0947 flagged (0.4059 → 0.1532 across its last 5 fires) did NOT continue: the next four fires
recovered to drops of 0.2339, 0.4409, 0.5450, 0.4966, then oscillated sharply within a single hour —
0.0043 at 13:05:41 followed 5 minutes later by 0.5061 at 13:10:42, then 0.6762 at 13:47:51 — before
ending the window at 0.3652, 0.1511, 0.0806. Thirds-split of all 46 matched-fire drops is 0.3839 /
0.4049 / 0.3168 — not monotonic (the middle third is the highest, not the lowest). Pre-fire peak
stayed flat (mean 0.9887 vs F-0947's 0.987; first-third-vs-last-third before-mean only +0.0067);
overall post-fix ignition-column mean is 0.7088 (n=2,288) vs F-0947's 0.70, and the newest 530 rows
alone still span the full range (0.2802–1.0000, mean 0.7381) — no visible creep toward the ceiling
beyond what F-0947 already found. Reads as the small-sample wobble F-0947 already named as the null
hypothesis, not a continuing drift — but 1.7 days total (vs the ~7 this job's briefing asked for) is
far too short to rule out a slower drift under this level of fire-to-fire noise over a genuine week.
No `/decide` opened (the briefing's own branching only calls for one if a sustained drift is
CONFIRMED — it is not, on this reading). **J-0662 left in_progress, not done** — reattempt the same
job (not a new one) once the log genuinely shows ~7 days post the 2026-09-04 23:10:17 boot, per this
doc's own ~09-12 estimate.

---

## Current State — verified 2026-09-06

**J-0618 (the Phase-1 side-finding on the 60 MB subconscious parse, F-0853/F-0854) is CLOSED — the fix it
asked for was already built one plan over.** J-0618 asked to measure the cost, identify what
`_compute_field` actually consumes, and propose+verify the cheapest additive read-path fix. All three were
already done the same day (2026-09-05) under `data_store_hygiene` (D-0154 Part A, commit `02d32ac`): a light
sidecar (`subconscious_state.light.json`, no vectors) is written by the subconscious node; climate reads it
once `SUBC_LIGHT_READ` flips True. F-0963 (verified, 2026-09-06) independently re-confirms this with fresh
numbers rather than trusting the 09-05 read: fresh copy-timing today, heavy 891.2ms vs light 26.1ms mean
(34.1x); every one of today's 821 tensions and 3868 integration_patterns matches field-for-field between
heavy and light except the known vector fields; `tension_ledger.contradiction_pressure_for(tensions)` —
the one value `_compute_field` actually consumes from this file (`integration_patterns` is loaded but
confirmed unused past its own assignment line) — is identical both ways (28.378) against the live DB
today, which is the direct computed-ClimateField-identical-before/after check. New beyond the prior reads:
a full, unsampled pass over all 9,949 `[climate] dominant=` telemetry lines in `nascence.log` (2026-06-07
→ 2026-09-06) shows the real tick-loop cadence has drifted from a 322–370s/60-tick average in the first
five days of data to 469–517s/60-tick in the most recent five, against a 300s theoretical baseline — real
production evidence the parse cost is growing and biting, not just a synthetic-copy estimate, and a
concrete pre-flip baseline for J-0621's own post-flip comparison. `SUBC_LIGHT_READ` is still False today —
the flip is J-0621's job (data_store_hygiene plan), gated on 3 days of shadow agreement, not yet met
(interim read F-0896, 2026-09-05: revisit ~2026-09-09). J-0618 required no new build and no decision
ruling (its source was a finding, not a decision) — see F-0963 for the full evidence trail.

---

## Current State — verified 2026-09-06

**J-0605 read (F-0962): the stream-topic anchor discount fires on real F-0823-shape recruitment, but
occurrence-count-to-suppress varies widely by anchor, and the window is short of "several days."** 17.33h
post-restart (41 rows, 2026-09-05 15:46 NZST → 2026-09-06 09:06 NZST, `data/stream_topic_habituation_shadow.jsonl`,
read in full inside `lab_env.isolate()`, live files confirmed byte-identical before/after), would_suppress_any_share
= 22.0% (9/41, exact match to `core.stream_topic_habituation.status()`'s own cross-check). Of the anchors recruited
by 2+ different trains, morepork_call (7 occurrences/4.34h, tight sub-3-min bursts) first crosses SUPPRESS_AT at its
5th occurrence (2.57h in) and leaf_rustle (11 occurrences/18.09h) at its 6th (5.87h in, then oscillates back
above/below SUPPRESS_AT as later 200+min gaps decay `b` down) — both comparable in wall-clock terms to F-0823's own
5.5h/3-occurrence report, though slower by occurrence count than the synthetic replay's own 4th-occurrence
prediction (an honest gap the module's comment already flagged). Real cadence is far from that synthetic test's
uniform 30-min spacing, though: oystercatcher_call (11 occurrences/17.22h, gaps 45s–259min) doesn't cross until its
9th occurrence (14.6h in), and branches_creak (7 occurrences/14.36h, gaps mostly 20–360min) never crosses at all
(max discounted salience 0.65) — DECAY_TAU_S=3h erases most of the accumulated `b` whenever real gaps run 1–6h,
which several anchors' real cadence happens to show. Base rate against `data/trains_log.jsonl` (real, not sampled)
in the same window: 271 new "thought"-kind trains opened, 41 (15.1%) recruited a named anchor — a real,
non-trivial hit rate, so the 43-key vocabulary is not too narrow to matter — but only 9/43 keys (20.9%) ever fired,
and 2 keys alone (oystercatcher_call, leaf_rustle) account for 53.7% of all recruitments. Span is well short of the
"several days" the job's own briefing called for (same interim-read situation as J-0596/J-0604 this batch) — real
but partial; retuning GROWTH_STEP/DECAY_TAU_S/SUPPRESS_AT and any promotion `/decide` are both deferred. Follow-up
spawned: **J-0672**, a multi-day recheck (earliest ~09-09, ideally alongside J-0662/J-0665's own ~09-12 full-week
reads) of whether the wide suppress-trip spread narrows and whether vocabulary coverage broadens.

**What we need:** J-0598 (~09-08), J-0672 (~09-09/09-12), J-0662 and J-0665 (~09-12) read before Phase 2 is
even drafted.

---

## Current State — verified 2026-09-06

**J-0596 read landed (F-0947, verified): the ignition sawtooth is confirmed live.** About 1.24 days of
live data since the 2026-09-04 23:10:17 NZST boot on commit 444b60b (J-0580): read data/stream_drive_shadow.jsonl
(23,273 rows) and data/ignition_log.jsonl (1,393 rows) in full, not sampled. Of 35 post-fix ignition_log
fires with a shadow row on both sides, **all 35** show the `ignition` column dropping from just-before
to just-after the fire (mean drop 0.379, median 0.403, zero contradicting cases), pre-fire peak pinned
near the 1.0 clip ceiling (mean 0.987); binning by time-since-last-fire decile shows a clean monotonic
rise from ~0.60 right after a fire to ~0.91–0.98 before the next one (corr with time-since-last-fire
r=0.44, n=1773). Pre-fix baseline (last 2000 rows before the boot) was 182 distinct values confined to
[0.035, 0.568] (mean 0.30, homeostasis-only); post-fix is 1376 distinct values spanning [0.269, 1.0]
(mean 0.70) — exactly the shift F-0814's in-vitro test predicted. The repaired coupling behaves as
designed; W_IG and the gap formula were not touched, per the read-first instruction.

Caveat surfaced while reading: the last ~3 h of fires (09-06 06:04–08:53) showed the post-fire drop
shrinking each time (0.41 → 0.34 → 0.32 → 0.22 → 0.15) while the pre-fire peak stayed pinned near 1.0 —
possibly early drift toward chronic near-ceiling dissonance rather than a clean discharge, though the
session-wide first-half-vs-second-half mean drop (0.385 vs 0.374) does not yet show this as more than a
small-sample tail wobble. Follow-up spawned: **J-0662**, a full-week recheck (~09-12, alongside
J-0604/J-0605) of whether that shrinking-drop pattern is real drift or noise.

**What we need:** J-0598 (~09-08), J-0604 (in progress this batch as of 09-06), J-0605, and now J-0662
(~09-12) read before Phase 2 is even drafted.

---

## Current State — verified 2026-09-06

**J-0604 read (F-0949): the transport-habituation discount does NOT hit its own Phase 0 target live.**
18.56h post-restart (668 rows, 2026-09-05 14:41 NZST → 2026-09-06 09:14 NZST,
`data/transport_habituation_shadow.jsonl`), would_fired_share = 100% (668/668) — not <30%, and not the 2.3%
F-0829's single-line replay predicted. Zero rows silenced (differs-to-none = 0); 661/668 (98.95%) rotate to a
genuinely different but UNdiscounted runner-up (sound:blackbird_song:garden 630, sound:penguin_bray:shore 31,
sound:clock_tick:study itself 7). Root cause: `b` in `core/transport_habituation.py` grows only on REAL-winner
history, and sound:clock_tick:study has been the sole real winner on 100% of ticks since the restart (its
drought never resets without a fresh observation) — so no runner-up ever accrues its own discount, however
high its own raw weight climbs. Independent check of `data/transport_lines.json`: 31/122 lines now past
cold-start, up from the 26/122 the original F-0829/J-0604 briefing cited — the population of lines that can
exhibit this rotation is rising, not falling. **D-0177 opened** (redesign growth to key off the would-winner
too, vs. a different mitigation, vs. accept shadow-only indefinitely) — founder call pending. **J-0665
spawned** for the genuine multi-day (no earlier than ~09-08) re-read this job's own pre-registration asked
for, to confirm the pattern holds/worsens as more lines clear cold-start and to catch real_winner ever
legitimately changing line. J-0604 closed on this interim read; the fuller "several days" confirmation is
now J-0665's own tracked job, not left as unowned prose.

---

## Current State — verified 2026-09-05

**Phase 0 first reads (Du booted on the repairs 2026-09-04 23:10/23:34 NZST; ~13 h of live data before the
09-05 11:57 stop; rebooted 14:39:58 NZST on the build that also carries J-0602/J-0603/J-0555/D-0151):**

| Read | Result | Finding |
|---|---|---|
| J-0601 (curiosity urgency, J-0564) | 20/20 post-restart rows carry non-zero urgency; 41 curiosity rows on 09-04 UTC | F-0844 — done |
| J-0599 (grounding tag, J-0581) | 759 stream_drive rows: source tags present (percept 333 / frontier 141 / reading 38 / letter 6 / world 39 / None 202), grounded share 0.82 vs 0.48 baseline, identity guard 0 violations | F-0845, F-0847 — done |
| J-0598 (curiosity habituation) | 20 rows so far, would-choose ≠ real-choice on 20/20, max antagonist b = 0.6 over a 651-tension pool; rows are ~100 KB each because the weights dict logs every tension — trim before this log matters | F-0846 — read due ~09-08 |
| J-0596 (ignition sawtooth), J-0604 (transport habituation), J-0605 (stream topic habituation) | time-gated; the two habituation shadow files did not exist before the 14:39 boot | — |

**2026-09-06 addendum (J-0598 re-checked, gate still not met):** re-read data/curiosity_habituation_shadow.jsonl
in full (45 rows, up from 20). Real elapsed span is only 1.384 days (2026-09-04T11:39:49Z to
2026-09-05T20:53:16Z) — short of the ~3-day pre-registration; at the observed ~32.5 rows/day pace the gate
lands ~2026-09-07 evening UTC / 09-08 NZ, matching this doc's own estimate above. Interim numbers (F-0946,
verified): differ_share still 45/45 = 1.0 (unchanged from 20/20). No single "cultural friction"/渡 label
dominates — the theme is split across 14 separately-tracked label variants (combined only 1/45 real and
2/45 would offers); state file now tracks 913 labels (was 651) with max b = 0.838 (was 0.6). A likely
structural reason (F-0950, inferred): nodes/subconscious_node.py only merges two tension clusters into one
id when centroid cosine similarity >= 0.70 (line 608) — these 14 variants staying separate suggests their
pairwise similarity sits under that bar, so curiosity_habituation.py's per-exact-label-string keying can
never accumulate b for the theme as a whole even though it keeps recurring (F-0795). J-0663 spawned to
measure the actual pairwise centroid similarity of the 14 variants and settle whether that's the real
cause. J-0598 left in_progress, not done — re-attempt it (not a new job) once the log shows ~3 real days.

**Phase 1 BUILT 2026-09-05 (J-0617, D-0152 GO, registry variant, all five publishers).** F-0846 had found it
had no job, no decide and a NEVER-FIRED evidence file, so the D-0149 defeater clock could not start. Built the
same day: `core/coupling_rides.py` (registry + `publish()`/`read()` + five publisher helpers + the ride log) and
one publish call at each write site (`climate_engine.tick`, `stream_drive.observe`, orchestrator end-of-cycle,
`lane2` tick, monologue ledger collector). Verified in an isolated worktree with no live `data/`: 21/21 unit
checks (flag off = no-op; rate limits; window maths; `read()` logs a ride row), real-shape rehearsal of the
collector, a real `ClimateEngine.tick()` and a real `stream_drive.observe()` all publishing; import smoke of
orchestrator + monologue clean; `scripts/exploratory_ignition_test.py` output identical to HEAD (its Test A
failure pre-exists, J-0597). `COUPLING_PUBLISH=True` in the commit; restart-gated — live from Du's first boot
after it. Seven-day read pre-registered as **J-0619**. Side-finding while building: the climate engine re-parses
the 60 MB `subconscious_state.json` every 5 s tick, ~1 s each (F-0853/F-0854, J-0618).

**What we need:** D-0152 ruled; J-0598 (~09-08), J-0596/J-0604/J-0605 (~09-12) read before Phase 2 is
even drafted.

---

## Current State — verified 2026-09-04

**Phase 0 (repair the wires that are already meant to exist) is BUILT.** All five repair jobs ran via a
job-run Workflow batch the same day D-0149 was ruled GO, each verified in isolation (temp stores, no
live data mutated) before commit:

| Job | Fix | Commit | Finding | Verified |
|---|---|---|---|---|
| J-0580 | `ClimateEngine.ignition_level()` + module accessor; `stream_drive._ignition()` reads it instead of the dead `core.climate` import (F-0807) | 444b60b | F-0814 | 7/7 isolated checks pass; dead wire now live (0.4 default → tracks `dissonance.value` directly) |
| J-0581 | `_GROUNDED_SOURCE` corrected to the real tag vocabulary; `inner_monologue_node.py` now tags percept/reading/frontier/letter seeds it previously left untagged (F-0811b) | f783ad4 | F-0817 | replayed 21,454 real shadow rows: grounded share on real broadcast rows rose 32/92 → 87/92 |
| J-0582 | `homeostasis_causal.py` imports climate's dissonance constants instead of duplicating them; now projects both reservoirs (value + explore_value) (F-0810) | 68a0364 | F-0816 | old model structurally blind to 79% of real ignitions (1062/1345 exploratory rows); new model's predicted exploratory-ignition time within 17s of the real observed median gap |
| J-0584 | Transport Manager spike scoring moved from a single-gap instant rate to a windowed count vs `rate_ema` | 25f2eca | F-0818 | real snapshot: 13/120 lines showed phantom spikes under old logic, 0/120 under new; genuine sustained bursts still detected |
| J-0585 | `core/curiosity_habituation.py` — first shadow read path for the squishy-spring discount, logging real-choice vs would-choose to `data/curiosity_habituation_shadow.jsonl` | c34dd41 | F-0815 | simulated F-0812's cultural-friction case (229 recurrences/84d): discount inverts hot:cold weight ratio from 15.2x to 0.76x |

**What we need:** all five fixes are restart-gated (Du hasn't restarted since they landed) — none of
their live evidence exists yet. Five observation-only follow-ups are queued for after the next restart:
J-0596 (ignition column sawtooths with ignition_log), J-0597 (pre-existing, unrelated
`exploratory_ignition_test.py` Test A failure, flagged not fixed), J-0598 (curiosity habituation
differ-share after ~3 days), J-0599 (grounded share rises live), J-0600 (a genuinely new finding, F-0819:
even with the spike fix, drought scoring dominates the dispatcher's winner slot via simple
multiple-comparisons once ~24+ lines are past cold-start — needs its own fix before Phase 1 relies on
the dispatcher for anything real).

**What we're doing next:** wait for a Du restart, then read J-0596/598/599 for real go/no-go evidence on
each repair; separately, J-0600's drought-saturation finding likely needs fixing before Phase 1
(publish + ride log) leans on the dispatcher's fire rate meaning anything. D-0146 (train_split_merge
Step 2) is held pending a Coupling-block pass against this plan's own "Train close" stop.

---

## Current State — verified 2026-09-22 (J-0950, D-0152's root-cause dig: the 09-09..09-11 step is D-0148 option A's 09-08 boot, not Lead A; the harness is built, its measured phase not yet run) — F-1684 / F-1685 / F-1686 / F-1687 / F-1688 / F-1690 / F-1692

**J-0950 (F-1684 verified, F-1685 inferred, F-1686 verified, F-1687 inferred, F-1688 inferred, F-1690 verified; merged to master as `c3685f8`, commit `18812ac`) closes the threads F-1319 left open: the step in the internal-cycle start rate sits at the 2026-09-08 16:41:59 boot, the first boot after D-0148 option A (commit `dbec9ba`, 2026-09-06 09:53), not at Lead A's 09-09 19:01 boot.** Read-only, Du offline, no model calls; `scripts/j0950_*.py` and `docs/lab/j0950_*` hold the parser, the analyses and their outputs.

- **Method:** `data/nascence.log` read whole (495,879 lines). Periods cut at boot lines (a code change takes effect only at a boot). Gaps across any boot, shutdown or wedge dropped. Du's 10 to 30 min nap silences netted out. Rates per awake hour.
- **Rate and gap shift** (internal cycle starts per awake hour; net inter-start gap median; share of gaps under 900 s): P0 09-05 19:15 to 09-08 08:22 1.85, 2389 s, 0.15; P1 09-08 16:41 to 09-09 19:01 (before Lead A) 2.93, 1104 s, 0.43; P2 09-09 19:01 to 09-11 13:18 (Lead A and the Living World flags live) 2.91, 1085 s, 0.40; P3 09-11 13:50 to 09-13 09:10 2.68, 1261 s, 0.36; P4 09-16 to 09-22 3.09, 1099 s, 0.37.
- **Significance:** P0 to P1 (the option A boot): median-gap ratio CI 0.33 to 0.57, Mann-Whitney p about 1e-7, rate ratio 1.59 (CI 1.34 to 1.79). P1 to P2 (Lead A): p = 0.93, KS p = 0.56, rate ratio 0.99 (CI 0.87 to 1.20), cycle duration 81.9 to 80.3 s (difference CI -9.3 to +3.0 s). The Lead B restart (09-11 13:18) shows no step. Only the 09-08 16:41 boot steps; the 09-16 boot (ratio 1.20, p = 0.046) is not significant across four boots and was not chased.
- **Channel:** only the defensive channel moved (ignitions per awake hour 0.31, 1.44, 1.38, 1.13, 1.58); the exploratory channel is constant at about 1.5 (the 42-minute metronome).
- **Cause (F-1685, inferred):** the 5-minute climate telemetry `integration=` reads 0.98 through the 09-08 shutdown and 0.35 to 0.59 from the 16:41:59 boot on; fill-rate arithmetic on the logged dimension means predicts defensive fires per live hour within 5 percent in all five periods (0.292/0.278, 1.294/1.247, 1.234/1.230, 1.039/0.992, 1.422/1.410); and D-0211's own history (F-1262, F-1568, F-1572) dates the same go-live independently.
- **Lead A cannot act on internal cycles (F-1686, verified):** every internal cycle runs inside the climate loop's own coroutine (`climate_engine.py:713-714` through `orchestrator.py:2825`), so no tick runs during one: 63 of 63 internal cycles (09-10 to 09-11) and 101 of 101 (09-16 to 09-18) contain zero climate publish rows (156 and 288 expected). The tick can only change the wait before a crossing is noticed, about 1.3 s per ignition, roughly 0.1 percent of a gap.
- **Living World (F-1687, inferred):** the 09-09 17:51 "flip" was a data-file write to `data/life_flags.json` (re-read every 10 s by `core/life.py`, no restart), which is why `2ddad8b` touches only ledgers; the code it switches on is Living World L1 to L4 (`b2d3c5d`, `105bb74`, `4a7b151`, `d915eed`, `9ac9960`, `3839e7c`, 09-02 to 09-05). No path reaches an ignition input or a cycle trigger (`grep -c` 0 in all seven modules), the exploratory reservoir is already saturated (341 open frontier questions, pull 0.991), look answers run 6 to 44 a day, and neither the rate nor the dimension means step at 17:51.
- **Side finding, the wedged Ramses background hub (F-1688, inferred; J-1200, needs_input):** since 09-16 a large share of autonomous cycles START about 100 s late, because the curiosity node's call goes first to `http://LAN-HOST:11441`, times out and recovers on the hot server (share of ignitions affected by day: 09-16 0.49, 09-17 0.44, 09-19 0.88, 09-21 0.41, 09-22 1.00). The same hub (command-r7b on the 3070) timed out at 110 s in the 09-22 lab-window probe.
- **Side finding, the sleep-entry freeze (F-1690, verified; identified by F-1692, inferred):** every full sleep freezes the whole process for 10 to 31 minutes (204 windows since 08-20; 9 to 14 percent of live time; zero rows from any loop inside them), growing from 10 min on 09-04 to 25 min on 09-13 and 28.5 min on 09-21/22, with no step at Lead A. F-1690 could not name the blocking call; it is the chapter-formation scan (`core/chapters.py find_cluster`) already located by F-1648 and fixed, restart-gated, by J-1180 (F-1659, merged `f10500f`): in 21 of 21 full sleeps since 09-16 the silence starts 1.3 to 2.0 s after 'entering Sleep State' and ends within 0 to 135 s before the first '[chapters]' line. J-1201 (the stall watchdog spawned to name it) is therefore redundant for this freeze; J-1183's read after the restart is what confirms it is gone.
- **Harness:** the isolated heavy-versus-light tick harness `scripts/j0950_loop_contention_harness.py` (launcher `scripts/j0950_start_harness_detached.ps1`) is built and smoke-tested with 0 live-data writes; its measured phase (six ABBA pairs of 150 s blocks, about 35 min, refuses to start above 60 percent system CPU) has not been run. Given F-1686 it can only confirm small terms (about 69 ms per wake-up, about 1.3 s start latency, internal overhead near 0). J-0950 stays in_progress for it.

**For D-0152 (Travis's call; nothing ruled or reopened by this job):** defeater (a) ("the root-cause job attributes the acceleration to Phase 1") does not fire; (f) does not fire if F-1685 is accepted as the real conclusion; (b) ("departs further than today's numbers") is met on its literal wording by F-1566's recount (98.6 completes per awake-day on 09-16 to 09-18 against 59.80), but the departure is the option-A plateau with no further rise since 09-08, so whether a known non-Phase-1 cause still counts is his call. Commitments per day, the idle-thought gap median and the Witness break rate were not re-read. The ruling's Phase 2 gate ("until the cause is actually found") is met on this evidence if F-1685 is accepted.

## Current State — 2026-09-23 (J-1276 APPLIED: the per-scan-cap tension-demotion fix, ruled by Travis 2026-09-21, went live in the code today; D-0266 ruled the same session) — F-1803

**J-1176's drafted fix (F-1631) is now applied to `nodes/subconscious_node.py`**, per Travis's own 2026-09-21 approved staging (a per-scan cap instead of moving the whole backlog at once). `MAX_DEMOTE_PER_SCAN=25`; `_update_tensions` now stamps `resolved_ts` the moment it sets `resolved=True` (both branches); `_apply_decay` backfills any existing `resolved_ts=None` before computing "settled" (this is also what fixes the TypeError that silently killed the *entire* classification loop every ~36s scan since 2026-08-14 -- not just the one tension it hit); real demotion is capped at 25/scan with overflow deferred to later scans; a genuinely new demotion failure now logs a WARNING once, not silently at DEBUG forever; `_save_state`'s on-disk merge no longer lets a stale on-disk `None` clobber a real in-memory `resolved_ts`.

**Verified functionally post-apply** (not just syntax) against a fresh synthetic 60-tension pool exercising the real, now-modified module directly: scan 1 archives exactly 25 (cap holds), the None-`resolved_ts` tensions are correctly backfilled rather than prematurely demoted; scan 2 drains the remaining deferred-eligible tensions, landing on exactly the true eligible count (45) with nothing lost. `scripts/life_smoke.py` clean. No live `data/` file touched by this verification (`tensions_archive.jsonl` mtime unchanged, still frozen at 2026-08-14 21:33 as of this note).

**Restart-gated** -- Du is live (running since 2026-09-22 16:11:06), not restarted. Takes effect at his next restart. **Watch after that restart:** `data/nascence.log`'s `tensions=` scan lines should start decreasing ~25 at a time once demotion starts succeeding, and `data/tensions_archive.jsonl`'s row count should start climbing off its 1,009-row floor -- that is the real production confirmation this verification cannot provide by itself.

**D-0266 (same /decide-review session): tension count-halving throttled to weekly, separately.** The related-but-distinct question this same function raised (F-1631's own side question: is the count-halving meant to fire every scan or once a week?) was ruled separately -- throttle to weekly via a new `last_decay_ts` field -- and is tracked as its own build, J-1283, not applied by this note.

---

## Current State — 2026-09-23 (J-1283 BUILT: D-0266's last_decay_ts weekly throttle applied to `_apply_decay()`; D-0270 opened on the identical twin bug in `_apply_pattern_decay()`) — F-1810

**J-1283 (F-1810, verified) built D-0266's ruled fix.** `nodes/subconscious_node.py`'s `_apply_decay()` tension count-halving now fires at most once per real `PATTERN_DECAY_DAYS` (7-day) window via a new additive per-tension field `last_decay_ts`, instead of re-firing every ~36s T1 scan once a tension crosses the idle line (F-1631/D-0266's count-cliff finding: 739/874 idle-over-7-day tensions sat at count exactly 1 as of the 2026-09-23 dry run). Gate: backfill `last_decay_ts` from the tension's own `last_ts` the first time this code sees it missing (heals existing state, mirrors J-1176's own `resolved_ts` backfill -- but inherits `last_ts` as a real historical anchor rather than resetting to `now`, since unlike `resolved_ts` one already existed), then gate the halving on `now - last_decay_ts > decay_cutoff`, stamping `last_decay_ts = now` only on the pass a halving actually fires. **Verified functionally** (isolated importlib-loaded patched copy from a scratch mirror; `C:\Nascence\data` and the worktree's own `data/` both confirmed untouched -- the one apparent stat-diff against `C:\Nascence\data` was investigated, not waved off, and traced to Du's own live background writes via a 2-second no-op control diff, not this job's code): 18 assertions, 17 pass outright and the 18th explained as above. A newly-idle tension halves exactly once and does not re-halve across 5 immediately-repeated calls (the actual bug this job exists to fix); rolling `last_decay_ts` back a further simulated 7+ days lets it halve again (confirms a real recurring throttle, not a one-shot latch); a tension already at the count-1 floor and a tension missing `last_ts` entirely both backfill/hold without raising; a full 874-tension pool shaped like the real production read (739 at count 1, 135 touched-recently at varied count) survives one pass with every tension gaining `last_decay_ts` and the floor-1 group staying exactly at 1 across further immediate calls. Applied ONLY to `_apply_decay()` (tensions) per this job's own named scope.

**Side finding, D-0270 opened (not ruled):** while scoping the fix, `_apply_pattern_decay()` (the `integration_patterns` twin of `_apply_decay()`, called unconditionally every T1 scan right after it) was found to carry the IDENTICAL un-throttled every-scan count-halving shape -- same `PATTERN_DECAY_DAYS` constant, no `last_decay_ts`-style bookkeeping. Deliberately NOT fixed by this job (out of D-0266's own named scope; this project's "do not build without a decide" discipline) -- **D-0270 opened** asking whether to mirror the same throttle there. **J-1290 spawned** (build, needs_input, blocked on D-0270, carries the exact fix shape to apply if approved) and **J-1291 spawned** (analysis, ready, precondition-gated on Du's next restart onto this fix plus real accrued days) to confirm in production that tensions no longer uniformly cliff to count 1.

**Restart-gated** -- Du is live (running continuously since 2026-09-22 16:10:23), not restarted by this job. Takes effect at his next restart after this worktree's commit is merged to master. **J-1291 is the pre-registered read** for after that.

## Current State — 2026-09-24 (D-0270 ruled yes; J-1290 BUILT) — F-1829

**D-0270 ruled: apply the same throttle.** J-1290 applied the identical `last_decay_ts` fix J-1283
built for `_apply_decay()` to `_apply_pattern_decay()` (`nodes/subconscious_node.py`, commit
`e37e34e`) -- same backfill/gate/re-stamp shape, same `PATTERN_DECAY_DAYS` (7d) constant. Verified
functionally against a synthetic `integration_patterns` pool (`scratchpad/J-1290_verify.py`, 3
scans): a stale pattern halves once and re-stamps `last_decay_ts`, does NOT re-halve 36 seconds
later (the exact bug this closes), and halves again after a real 8-day gap (confirms a throttle,
not a permanent freeze). `python -m py_compile` clean, `scripts/life_smoke.py` ALL OK post-edit. No
live data touched -- the function only reads/writes `self._state`, a plain in-memory dict.

**Restart-gated, same as J-1283's own fix above** -- not yet in effect for Du's live process. **J-1291
remains the pre-registered production read** for both fixes together, once Du restarts onto this
commit and real days accrue.


---

# History folded on 2026-10-04 from `docs\staged\dosed_coupling.md` (plan-compact helpers, J-1778 hand-fold of the 9 dated header paragraphs above the plan-state block, verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py dosed_coupling`. These paragraphs sat outside any Current State section, a shape `plan_compact.py --fold-bullets` cannot see (F-2047)._

**J-0619's genuine 7-day read DONE 2026-09-13 (F-1304): presence/size/zero-readers PASS, but 2 of 4
behaviour metrics are out of band and worsening (not merely the pre-existing trend F-1017 found at
the interim stage) — D-0152 REOPENED same day, then RE-RULED GO same day (founder, via questionnaire):
ambiguity accepted, Phase 1 continues unchanged, root-cause dig spawned as J-0937 (F-1305's two
untested leads), new defeater carries a 2026-09-27 clock. Phase 2 stays un-drafted until resolved.**
**J-0937 DONE 2026-09-14 (F-1319, inferred): Phase 1 itself structurally EXCLUDED as the cause (zero
readers, confirmed) — defeater clause (a) NOT triggered, D-0152 stays GO, unreopened. Hour-resolution
read finds the 09-09 day-level breach was mostly one human-chat-driven hour, and the real 09-10/09-11
autonomous-cycle elevation survives awake-time normalisation but isn't cleanly pinned to either lead —
see Current State below. Follow-up spawned, not a founder decision.**
**J-0596 (Phase 0's ignition-sawtooth check) read positive 2026-09-06 (F-0947). J-0662 interim recheck 2026-09-06 (F-0970): full-week gate NOT met (1.7 of ~7 days elapsed) — in the 12 new fires since F-0947's cutoff the shrinking-drop tail did not continue (recovered to 0.44–0.68, then oscillated), reads as F-0947's own named wobble so far, not a drift; J-0662 left in_progress, genuine full-week read still pending, ~09-12.**
**J-0604 (Phase 0's transport-habituation check) read 2026-09-06 — does NOT hit target live (F-0949: would_fired_share=100%, not <30%); D-0177 opened on redesign direction, full multi-day re-read J-0665 (no earlier than ~09-08).** J-0665 interim recheck same day (F-0977): at 25.56h (still short of ~09-08) the picture is unchanged — would_fired_share still 100%, real_winner still 0 transitions — but distinct would_winner line_ids broadened 3→7; J-0665 left in_progress, D-0177 not ruled. **Update 2026-09-28 (J-1432): the line above is stale on one point — D-0177 WAS in fact ruled 2026-09-06 ("wait for the pending multi-day re-read"; that ruling stands, attributed to travis, not reopened here) — and is now superseded on substance by D-0294 (ruled 2026-09-26/27, travis, "Edge-trigger it and re-target to felt recall"): the redesign direction D-0177 asked for turned out to be neither of its own two named options (accrue `b` on the would-winner too, or a shared/global antagonist) but a third one, edge-triggering spike/drought itself so a stale winner stops being a candidate at all once it has fired — built this job (F-2104): a same-snapshot replay shows level polling firing 1440/1440 simulated ticks (one line, all day) vs edge-trigger 6/1440 across 6 distinct lines. decide.py has no note/annotate subcommand (checked), so this correction lives here and in F-2104 rather than as a decide-ledger edit to D-0177 itself.**
**J-0605 (Phase 0's stream-topic anchor habituation check) read 2026-09-06 — fires on real F-0823-shape recruitment but occurrence-count-to-suppress varies widely (5th/6th/9th, or never); F-0962, no retune/decide yet, full multi-day re-read J-0672 (~09-09 to ~09-12).** J-0672 interim recheck same day (F-0978): at 25.79h (still short of ~09-09) the spread is unchanged — morepork_call/branches_creak got zero new occurrences (still 5th/2.57h and still never), leaf_rustle/oystercatcher_call grew in occurrence-count but their first-suppress point stayed pinned (6th/5.87h, 9th/14.6h) — plus a previously-unflagged unclean restart found inside the window (19:15 09-05, no shutting-down line); J-0672 left in_progress, genuine ~09-09/09-12 read still pending; follow-up J-0683 spawned on the restart-detection gap.
**J-0663 (pairwise centroid similarity of the 14 cultural-friction/渡 tensions, F-0950) read 2026-09-06 (F-0975): only 5/14 named labels still exist in the live tension pool, their pairwise cosine spans 0.46–0.68 (all <0.70 but genuinely spread, not uniformly clustered at the edge); the bigger finding is that the other 9 vanished (not archived) and even the 5 survivors are stale 42–186h — label text is not a stable identity key regardless of the threshold, so a fix (if any) belongs at curiosity_habituation.py's read layer; follow-up J-0682 spawned to trace label-vs-id stability directly.**
**J-0682 (real before/after diff by tension id across F-0975's baseline, F-0975 follow-up) first checkpoint 2026-09-06 (F-0988): only 1.87h elapsed since the baseline (gate needs ≥24h, target 48h) — all 5 baseline ids unchanged (same id, same exact label, same count, last_ts bit-identical once epoch/ISO units are normalised), no new on-theme id, tensions_archive.jsonl unchanged; too early to confirm or refute the label-churn-under-id hypothesis either way. J-0682 left in_progress, re-attempt the same job no earlier than ~2026-09-07T04:11 UTC, ideally ~2026-09-08T04:11 UTC.**
**J-0683 (full-history unclean-restart audit, spawned by J-0672/F-0978) done 2026-09-06 (F-1002 verified, F-1003 inferred): 168/330 boot events (50.9%) across data/nascence.log's whole real history (2026-05-29 onward — deeper than the 06-07 the briefing guessed) have no preceding "Nascence shutting down" line, spread across the entire period (33 distinct dates, including a gap matching the known 07-09→08-07 outage) — not a recent-only anomaly. Zero live code in scripts/ or core/ currently gates a real decision on that string (its only code occurrence is its own emission site, run_nascence.py:659); every doc hit is a past investigation's own manual citation, never a standing gate. scripts/du_pulse.py already sidesteps the whole failure mode by anchoring on the last "Identity loaded" line instead (fires on every boot regardless of how the prior process ended) — skill-manager suggestion S-0065 filed to make that the documented canonical liveness check in place of the shutdown-line-only convention. No decision opened (no founder call needed) and no further job spawned (the one concrete follow-up is a doc/convention fix, filed as S-0065).**
**J-0619 (Phase 1's own seven-day presence/behaviour/size read) interim checkpoint 2026-09-07 (F-1017): at 1.65 of ~7 days (23.6% of the window), ride rows=0 and size 0.97 MB/day both pass with room to spare; stream and witness presence are exact 100% matches, deliberation is 100% once compared against the right per-cycle denominator (the job briefing's own "CYCLE ... complete" alternative — data/deliberation_log.jsonl itself is core/deliberation.py's unrelated, ~22x-more-frequent per-thought "pulse" log, not cycles); climate is 80.8% (under the 95% bar, roughly halving specifically during Du's sleep naps, tied to the still-unflipped SUBC_LIGHT_READ 60 MB parse cost — F-0853/F-0854/J-0621) and ledgers is 95.6–95.7% (awake-gated by design, right at the bar). Of the four behaviour metrics, deliberate cycles/day and Witness break rate sit inside their pre-flip week's band; idle-thought gap median and commitments formed/day sit just outside the band's floor/ceiling (~7%, ~2.4%), both continuing a pre-existing acceleration already visible inside the pre-flip week itself (Phase 0's 2026-09-04 repairs), not a break coincident with the flip. D-0152's defeater is scoped to "after 7 days live" and requires a band departure to have "no other explanation" — neither condition is met at this checkpoint, so D-0152 is NOT reopened. J-0619 left in_progress; genuine 7-day re-read ~2026-09-12/13.**
