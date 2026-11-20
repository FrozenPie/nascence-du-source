# J-3205: labelled-union evaluation of the Lane 2 metaphor prompts (D-0595)

Date 2026-11-05, Du down. Lab only: no Du code, prompt, store or sampling rate changed. Script `scripts/lab_metaphor_union.py`
(HTTP to the three judge hubs only; writes under `docs/lab/` only). Test `scripts/_test_J-3205_union.py`.

## Result in one paragraph

On the stored deepseek era (2,768 ticks with a passage, 2026-09-28 to 11-05) the union of ticks that the two keyword scans, the flag arm, or
production's own stored v1 panel rulings (including any single judge voting True) mark as possibly figurative is **131 ticks (4.7 percent)**.
Adding a seeded random control sample of 90 non-union ticks (0 positives found in it, 95 percent upper bound 4.1 percent) the frame is 221 ticks, all
blind-read. A pre-label by Claude (a model, labelled as pre-label only, NOT the founder or a hand-read by Travis) finds **12 clear positives (strict)
and 28 clear-or-arguable (inclusive)** in the union: the strict count sits exactly on D-0595's floor of 12 (target 12 to 20), the inclusive count is above
the range. **v2 fails the pre-registered bar on recall**: strict recall 3/12 = 25 percent against v1's 7/12 = 58 percent (inclusive 3/28 = 11 percent
against 15/28 = 54 percent). v2's precision is 3/3 but on three verdicts (Wilson 44 to 100 percent), so it cannot be called a pass. The recall result does
not depend on the labels: **every tick v2 marked (3) is also marked by v1 (30), and v2 marked nothing v1 did not**, so on this union v2's recall is at
most v1's under any labelling, and it can only tie if all 27 of v1's extra marks are negatives (my labels say 4 of them are strict positives). v1's own
precision on the same union is 23 percent strict (7/30, Wilson 12 to 41) and 50 percent inclusive (15/30), also under 70.

## Design (what was built, and the one thing that differs from the ruling's letter)

D-0595: hand-label every tick any prompt, either keyword scan or the flag arm marks as possibly figurative; require precision >= 70 percent AND recall >=
v1's on that union, with the number of positives stated in advance (12 to 20); defeater: fewer than 12 labelled positives.

* Era: ticks with model deepseek-r1:7b and ts >= 2026-09-28: 2,772, of which 4 have an empty passage; 2,768 usable. (The job text says about 2,500; the log holds 2,772.)
* Frame sources, all zero model cost: `kw_metaphor` 36 ticks, `kw_figurative` 43, `flag_arm` 77 (F-3837's arm B was never built, so in this era its members are
  by definition the keyword-flagged ticks; it adds nothing beyond the two scans), `v1_stored_panel` 14 (production's own panel said metaphor on a sampled tick),
  `v1_stored_anyjudge` 62 (JUDGE_1, JUDGE_2 or the tiebreak voted True even when the ruling was literal). Join of the stored panel rulings to ticks:
  `judge_panel_log.jsonl` lane2:metaphor row is the first at or after the tick-start ts; 711 of 711 sampled ticks match on verdict and how.
* **v1 and v2 were not run on all 2,768 ticks.** About 5,500 panel runs on the shared CPU hubs measured 11 to 20 s each, 15 to 30 hours. Instead both prompts were
  run through a production-shaped panel (JUDGE_1 mixtral@Ramses :11438, JUDGE_2 falcon3 :11440 concurrent, gemma4:12b :11439 tiebreak on a split, same payload as
  `core/judge_panel._ask`, temperature 0, num_predict 200) on the whole frame, plus the 90-tick control sample to find prompt-marked ticks outside the union.
  v1 uses production's own stored ruling where one exists (100 frame ticks) and a replay elsewhere. The control found 2 v1 marks (both literal on my labels) and 0 v2 marks, so the
  union that was scored is 133 ticks; 0 of 90 control ticks is a positive. This bounds, but does not eliminate, positives outside every mark (95 percent upper
  bound 4.1 percent of the 2,637 non-union ticks, up to about 108 ticks, point estimate 0). A full-era sweep is spawned as a follow-up if the labels justify it.
* Fidelity of the replay (34 v1 replays on ticks production already ruled): 29 of 32 metaphor/literal verdicts reproduced; the 3 differences are all stored metaphor ->
  replay literal (tiebreak flips; F-2876 saw 2 of 10). So the replayed v1 marks are, if anything, slightly under-counted. `J-3205_data/fidelity.json`.
* Passages: first 500 chars of notice + uncertain + expect_next as the shadow log holds them (it truncates; F-2876's limit 1).

## Labels (read this before the numbers)

The labelling sheet is blind (shuffled, no marks, no judge output): `docs/lab/J-3205_data/labelling_sheet.md` and `.csv`, key in `labelling_key.jsonl`.
Travis has not labelled it. The labels used here are `prelabels_claude.jsonl`: a model hand-read, blind to marks, of a different family from the author (deepseek) and from
every judge (mixtral, falcon, gemma), flagged PRE-LABEL ONLY. Labels F = clearly figurative (metaphor, symbol, self-narrative, or ambient-mood that paints or personifies the
scene), A = arguable, L = literal (including sensor-field restatements, real sound names, real fire or sun colour, "dawn chorus", "cicada chorus", "calm sea hush").
Strict = F only; inclusive = F or A. The pre-label is deliberately strict (a conventional "the sun begins its journey" is A, not F). Every number below must be re-run with Travis's labels:
`python scripts/lab_metaphor_union.py score --labels <labels.csv or .jsonl>`.

## Numbers (pre-label, union of 133 incl. control marks, 221 blind-read)

| | flagged | TP strict | precision strict (Wilson) | recall strict (Wilson) | TP incl | precision incl | recall incl |
|---|---|---|---|---|---|---|---|
| v1 (production prompt; stored ruling where it exists, replay else) | 30 | 7 | 23.3% (11.8 to 40.9) | 58.3% (32.0 to 80.7) | 15 | 50.0% (33.2 to 66.8) | 53.6% (35.8 to 70.5) |
| v2 (J-2212 candidate) | 3 | 3 | 100% (43.8 to 100) | 25.0% (8.9 to 53.2) | 3 | 100% (43.8 to 100) | 10.7% (3.7 to 27.2) |
| kw_metaphor scan | 36 | 2 | 5.6% | 16.7% | 11 | 30.6% | 39.3% |
| kw_figurative scan | 43 | 12 | 27.9% | 100% | 18 | 41.9% | 64.3% |
| flag arm (any keyword) | 77 | 12 | 15.6% | 100% | 27 | 35.1% | 96.4% |

Positives in the union: 12 strict, 28 inclusive (0 and 0 among the 90 control ticks). Bar (precision >= 70 percent AND recall >= v1's): v2 precision yes (3 verdicts), recall NO, so **FAIL**;
v1 fails precision. The paired difference is one-sided: v2 loses 4 of v1's 7 strict TPs and 12 of its 15 inclusive TPs, and gains none (exact sign test p = 0.125 strict, p about 0.0005 inclusive).
Keyword recall of 100 percent on strict is by construction partly circular (the union is built from the keyword hits and all 90 control ticks were negative), not evidence the scan is sensitive off-union.

Where v1 stands on its own (not what D-0595 asked, but it is what production does): of the 14 stored production verdicts, 2 are strict positives and 4 inclusive (14 percent, 29 percent), against F-2955's 18.5/37.0 on the 128 splits. Of the 16 replayed v1 marks, 5 strict and 11 inclusive.
The replayed ticks are enriched by the keyword frame, so these two rates are not comparable to each other.

Both prompts miss the same 5 strict positives: the "alive with" and "symphony of the morning" ambient-mood passages (L154, L066, L179, L116, L011) are called literal by v1 and by v2 on the panel, although both prompts name that register explicitly.
v2 loses ground on exactly the passages its exemptions did not target ("alive with", the sun's "journey"); it kept only L001, L075, L207.

## How many positives the stored era yields (the number D-0595 asked for)

Strict 12 (0.43 percent of 2,768 ticks, 9.2 percent of the union), inclusive 28 (1.0 percent). F-3837's hand read of 378 post-boot ticks found about 7 (1.9 percent); the pre-label agrees on that window
(5 of F-3837's 6 mood-painting passages are F or A here, 4 of them F; the sixth, 11-02 04:36 'golden hue' from a rising sun, is L). 12 is not "fewer than 12", so the D-0595 defeater does not fire on the pre-label, but it is on the line: a stricter labeller would trip it. If Travis's strict count is under 12,
the fallback is option (c) (tiebreak alone), filed as the needs_input job below.

## Recommendation

1. Do not swap v2 into `_judge_metaphor`: it fails the ruled bar (recall) and the failure is independent of whose labels are used, because v2's marks are a strict subset of v1's.
2. Travis's 221-row labelling pass (about 20 minutes, CSV) is the only thing that can change the strict count or the verdict; everything here is conditional on it.
3. If a rewrite is still wanted, F-3844's percept-grounded variant (v1 sysmsg + the tick's own percept names appended as "the world's own names, never figurative") is the untested candidate; this frame is reusable for it (spawned).
4. The cleaner lever on the visible failure (precision 23 percent) is the tiebreak/panel, not the wording: JUDGE_1 mixtral raises most of the false positives and gemma already reverses 5 of 6 (F-3844); that is a founder decision (spawned needs_input, with the labels).

## Limits

Pre-labels are a model's; 12 strict positives is a small base (Wilson recall 8.9 to 53.2 for v2); v1 mixes production rulings with replays; v1 and v2 never ran on the 2,637 non-union ticks except the 90-tick control;
shadow-log passages are truncated; no keyword list tuned; the labelled union is a sampling frame for these two prompts, a new candidate that marks ticks outside it needs the control extended.

## Files

`scripts/lab_metaphor_union.py` (build, run, sheet, score), `scripts/_test_J-3205_union.py`, `docs/lab/metaphor_union_ticks.jsonl` (221 frame rows with marking sources),
`docs/lab/J-3205_data/` (`panel_runs.jsonl` 377 panel runs, `labelling_sheet.md/.csv`, `labelling_key.jsonl`, `prelabels_claude.jsonl`, `score_prelabels_claude.json`, `fidelity.json`, `build_summary.json` with the sha256 of the two log snapshots).
