# J-2218 manifest-loop P0 Run 2 -- pre-registered metric sheet (written 2026-10-16 BEFORE any model call)

Fuel: the 43 `[CYCLE <numeric>] human:` turns of data/nascence.log dated <= 2026-07-03 (Run 1's set), full text from
memory_fragments (read-only). Model: MichelRosselli/bonsai-27b (Q1_0) on the hot Ollama :11433, Du down.
Arms: A1 full text + tuned decode (seed 11); A2 same, seed 23; B 80-char log text + tuned decode (seed 11).

Metrics (per arm): valid-JSON rate; decomposition rate (>=2 ingredients); both-lanes rate (>=1 emissary AND >=1
dreamer ingredient -- win condition 2 at the decompose stage); degeneration rate (any need pair with token-Jaccard
>= 0.6, or >=2 "relationship between" needs, or >=3 needs sharing their first three words); identity items and how
many are deferred; rule violations (identity not dreamer+deferred, fact/epistemic not emissary+inline);
A1-vs-A2 stability (same ingredient count and same lane set per turn).

Predictions / pass bars (set now):
- P1 valid JSON >= 42/43 in A1 (grammar + cap removes Run 1's 4 unterminated-string failures).
- P2 degeneration <= 3/43 in A1 (Run 1: at least #1 and #38 degenerate; the target is "rare", not zero).
- P3 decomposition >= 30/43 in A1; both-lanes >= 15/43.
- P4 A1-vs-A2 lane-set agreement >= 30/43 (Run 1 called #1 UNSTABLE).
- P5 B degenerates at least as often as A1 (fragments are garbage-in).
Kill reading for the decompose stage: if A1 valid JSON < 39/43 (no better than Run 1) or degeneration > 8/43, the
Bonsai gate is not usable and the manifest frame's decomposer is unproven.
What this run CANNOT test: the completion judge (win condition 1), bus correlation (5), steam convergence (4) --
none of them exist. The verdict on "does the frame add anything closure_law lacks" is therefore about decomposition
and identity deferral only.
