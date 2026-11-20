# Open-doubt cup (coordinate-only) scored by the position-free absolute judge (2026-10-09)

*J-2054 (from F-2668 / J-2052) · script `scripts/si_open_doubt_cup_judge_J2054.py` · raw `data/lab/J-2054/{ctrl_abs,arm_abs,arm_match}.jsonl`, `summary.json` (live tree, lab dir) · generations = the existing J-2031 gens (`data/lab/J-2031/gens.jsonl`) · nothing wired, nothing enabled; D-0403 (coordinates, never prose) and D-0396 (hold) untouched*

## Verdict: the instrument is valid, and the coordinate-only cup does NOT clear the pre-registered bar (cup engaged 0/30)

Pre-registered bar (D-0396/D-0403): cup-affected >= 30% AND shuffled control <= 11% AND no rise in restate_sim / early close.

| check | result |
|---|---|
| Same-run controls (J-2052 hand-written, 15 fires): own engaged | 15/15 (Wilson 79.6-100) |
| plain | 0/15 (upper 20.4) |
| mismatched | 0/15 (upper 20.4) -> instrument gates re-pass |
| **CUP engaged (both judges >= 4)** | **0/30 (0%, Wilson 0-11.4)  -> bar FAIL (needs >= 30%)** |
| shuffled CONTROL engaged | 3/30 (10.0%, 3.5-25.6) -> <= 11% met on point estimate |
| uncued BASELINE engaged | 0/29 (0%, 0-11.7) |
| rumination guard (J-2031 numbers) | restate_sim base 0.614 / cup 0.593; early close 0.034 / 0.0 -> no rise |
| cue-echo-excluded | cup 0/30 (echo rate 0), control 2/27 |

Mean panel score (mixtral / falcon): baseline 2.45 / 3.21, cup 2.47 / 3.13, control 2.63 / 3.27. Both judges' 4-5 scores are rare on every arm; a typical generated thought is "same scene, no doubt taken up" (2-3).

Paired per fire x sample on summed panel score: cup > control 10/30 (ties 7, losses 13; excluding ties 10/23 = 43.5%, Wilson 25.6-63.2); cup > baseline 11/29 (ties 9, losses 9; excl. ties 11/20 = 55%, 34.2-74.2). Neither lower bound approaches 0.5, and cup does not beat the shuffled control. The only engaged generations (3) were in the shuffled-control arm, none in cup or baseline.

Cross-check, reflection-matching (thought + 3 reflections, own rotated across positions; panel pick needs both judges to agree): picks own reflection baseline 10/29 (34.5%), cup 12/30 (40.0%), control 10/30 (33.3%); 11-15 items per arm with no panel verdict. Chance is 33%; the cup is not distinguishable from baseline or control (Wilson ~25-58% for cup). Matching agrees with the absolute score: no sign of the cue making the next thought answer its own doubt.

## Can the judge discriminate on this data?
Yes on the hand-written controls (the 15 own / plain / mismatched gates re-pass in this run, same prompts, same hubs). On the *generated* thoughts it returns a flat distribution with essentially no 4-5 scores, so it can say "no arm reaches the engaged threshold" but its sensitivity to weaker, real engagement (a generated thought that half-takes up a doubt) is not established: the controls are a hand-written ceiling. The 3 control-arm "engaged" thoughts (10%) are the only ones above the threshold and are consistent with judge noise or incidental overlap (2 remain after echo exclusion), which is exactly the false-positive rate the 11% bar is meant to cap. Read plainly: this replay shows no cup effect; it cannot show that a subtler one is absent.

## Why it is probably real, not just the judge
The gens used the realistic seed (scene, recall, wander items competing); F-2604 had already found 1 affected in 16 live fires, and the cue literally says only "point N" (and N is always the latest ledger point). Cup echo is 0%. The baseline engaged rate is also 0%, so there was headroom: the cue did not move the distribution up.

## Confounds
Generator gemma4:12b (:11439), not live qwen3.5:9b (existing J-2031 gens reused, no new generation); n = 15 fires x 2 samples, 30 per arm, wide intervals (cup upper bound 11.4%, so a true rate >= 30% is excluded for this generator/seed, but not for the live generator); Du live and sharing judge hubs (sequential single stream, 2 s pauses; the judge panel log showed Du's own lane2 calls interleaved, so latencies ~25 s/item; scores are temperature 0 and not latency-sensitive); judges mixtral :11438 + falcon :11440 (generator is a different family); rubric and thresholds imported unchanged from J-2052 (not retuned); matching has 11-15 no-verdict items per arm and leans on shared vocabulary (J-2052: plain thoughts match own 55.6%); the live-like seed fixes the scene/mood/book strings.

## What this does to the plan
On the pre-registered bar the coordinate-only cup is not supported: the D-0396 hold stands and there is no case here for a live cup. This does not refute a stronger cue (the J-2008 v1 "97% affected" was a bare-seed property); any widening beyond coordinates is D-0403's ruled-out territory and a founder question, not taken here.
