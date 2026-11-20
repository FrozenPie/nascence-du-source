# J-3788 pre-registration (written before any generation)

Question (D-0682 defeater, faster route): does the Executive's output move when the Salience urgency word is forced to
the extremes? Counterfactual injection on logged word-format Executive cycles; OUT-OF-DISTRIBUTION, so any effect is an
UPPER BOUND on live sensitivity, not the live effect. J-3403 (natural high stratum) stays the confirmation.

Data: copy of data/training/executive.jsonl (read-only copy to scratch). Sample (seed 3788): every distinct word-format
cycle logged high or pressing, plus up to 49 moderate and 49 low (random, seeded), human and internal mixed as logged.
Arms (hot lane qwen3.5:9b :11433, J-3164 opts, seed = 378800+i*10+arm index; only the Salience urgency word differs):
 A1 as logged | A2 as logged, second seed (noise-floor CONTROL) | P word forced "pressing" | L word forced "low".
P contrasts exclude cycles logged pressing; L contrasts exclude cycles logged low (identical prompt otherwise).
Judge: falcon3:7b :11440 (different family), pairs A1|A2 (control), A1|P, A1|L, P|L (extremes), order randomised.
Metrics: (1) paired word-Jaccard of synthesis, (arm vs A1) minus (A2 vs A1), bootstrap CI + sign-flip p;
(2) judge same_decision=no and content=different rates vs control (Fisher); (3) response_type / respond-flag differs.
BAR: the Executive "responds to urgency at the extremes" if, for P or L (or P|L), the judge content_different OR
same_decision_no rate exceeds control with Fisher p<0.05 AND the paired Jaccard CI excludes 0 in the same direction.
Otherwise: "no detectable sensitivity even at the extremes" (upper bound null). Anything between is reported as weak.
Du down, local only, no Ramses, no Du source edits, live data/ untouched.
