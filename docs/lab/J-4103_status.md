# J-4103 pass 2: blocked, judge hubs still saturated
Probes 2026-11-17: mixtral :11438 28 s trivial, falcon3 :11440 41 s, gemma :11439 67 s (real prompts about 200 s each in the J-3309 script, same as pass 1).
Two judge workers (j1, j2, N,A05,B) ran about 35 min: cache grew by 0 rows beyond the 3+3 from pass 1 (all outputs stalled/timeout). Need ~1200 calls; infeasible.
Alternate families: granite :11437 (1 s) and command-r7b :11441 (2 s) answer fast but both picked the WRONG set on an obvious 1-vs-0 relevance probe (x_better false when Paris-for-capital set was X), so they fail sanity and are not usable as judges.
Caches in docs/lab/J-3309/judge_cache_*.jsonl resume unchanged. No verdict; still INCONCLUSIVE. Live data untouched (read-only mode=ro).
