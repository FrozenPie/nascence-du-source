# J-3307 results: chord_echo replay (U1 stage 1) FAILED
Run 2026-11-16 per docs/lab/J-3307_chord_echo_prereg.md (commit 3a215f16); script scripts/lab_chord_echo_J3307.py; raw: J-3307_chord_echo_results.json (includes place/weather strata).
3,000 sampled experienced moments, read-only. MAE of predicting the moment's own stored outcome, 7-day gap:
| outcome | global mean | single weather | single sound | chord top-24 | nearest in time | shuffle null |
| valence | 0.275 | 0.283 | 0.280 | 0.319 | 0.330 | 0.282 |
| arousal | 0.0237 | 0.0240 | 0.0241 | 0.0272 | 0.0263 | 0.0241 |
Chord is WORSE than single-key by 0.037/0.040 (valence) and 0.003 (arousal), CIs exclude 0 in the wrong direction; worse than the shuffled-tag null (z = -27.6 / -21.8); it beats nearest-in-time on valence only (0.011). Correlation with truth: chord +0.055 / -0.039, nearest-in-time +0.089 / +0.144. 1-day post hoc variant: same verdict (valence chord 0.311 vs 0.280 single, arousal 0.0253 vs 0.0234). Coverage: every sampled moment had tags and a weather (fragment_context rows only exist for covered memories; the 36 percent without a row are outside this sample by construction).
Verdict: pass bar missed on every clause. chord_echo retired as a build; D-0669 governs the memory namespace. Caveat: valence/arousal is the pre-registered outcome, not recall quality; stage 2 (judge panel) was gated on this passing.
