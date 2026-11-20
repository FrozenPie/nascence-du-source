# Open-doubt cup (coordinate-only) -- shuffled-control lab replay

*Run 2026-10-09 00:45 · J-2008 · D-0396 · script `scripts/si_open_doubt_cup_replay.py` · raw `data/lab/si_open_doubt_cup_replay/raw.jsonl` · nothing wired into Du*

**Verdict: FAIL the D-0396 pre-registered bar** on 40 genuine fires (seeded sample of the genuine fires whose train, ledger and next step could be rebuilt).

| arm | judged | affected | affected rate (95% CI) | mean restate_sim | early-close proxy | cue echo |
|---|---|---|---|---|---|---|
| baseline (no cup) | 40 (+0 no verdict) | 39 | 0.975 (0.871, 0.996) | 0.701 | 0.15 | None |
| CUP (true coordinate) | 40 (+0 no verdict) | 39 | 0.975 (0.871, 0.996) | 0.686 | 0.075 | 0.275 |
| CONTROL (shuffled coordinate) | 40 (+0 no verdict) | 39 | 0.975 (0.871, 0.996) | 0.663 | 0.075 | 0.3 |

| bar clause | result |
|---|---|
| cup-affected rate >= 30% | True |
| shuffled control <= 11% | False |
| no rise in restate_sim (tol +0.02) | True |
| no rise in early-close proxy (tol +5 pts) | True |

Control coordinate equalled the true coordinate in 0 fires (one-point ledgers have no other point to shuffle to); those control rows are really a second cup sample.

## Reading it

- **The cup adds nothing measurable here.** CUP − BASELINE = 0.0 pts; CUP − CONTROL = 0.0 pts. All three arms sit at the ceiling, so the 30% clause is met trivially and the 11% control clause is failed trivially; neither says anything about the cue.
- **Why the ceiling.** In the replayed seed the doubted point is the LAST item of the 'established points' ledger the step already sees, so even the uncued step continues it. The live counterfactual (F-2604) found 1 affected of 16 on the real next thought; the replay's ~97% uncued rate is a property of the reconstructed seed plus the judge, not evidence the live step engages doubts.
- **Judge negative control.** Scoring each reflection against the baseline thought of a DIFFERENT fire returned 'affected' on 12/40 (30%). A control that mismatched already exceeds the pre-registered 11% control bar, so this judge cannot pass the control clause under any seed; the bar as written is unattainable with this instrument, independent of the cup.
- **What this does and does not show.** A coordinate (flag + ledger index) adds no detectable engagement over the uncued step in this harness; it does NOT show that a prose cup would do better or worse, and the harness cannot separate engagement from topical vocabulary. D-0396's defeater (control within 5 points of the cup) is met.

## Caveats
- Seed block only (live seed also carries recall etc.); condensed system prompt; train_state_log truncates thoughts to 200 chars; one sample per arm per fire (BASELINE is the sampling-noise floor).
- `affected` can still be vocabulary echo; the cue-echo column is the share of thoughts that literally repeat 'doubt' / 'point N'.
- The early-close proxy is the live earned-length test (circling or off-thread) recomputed on the replayed thought, not an observed close.
