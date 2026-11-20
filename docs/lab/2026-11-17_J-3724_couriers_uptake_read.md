# J-3724 courier delivery uptake read (2026-11-17)

Script: `scripts/couriers_uptake_read_J-3724.py` (read-only; measures fixed in its docstring before the run). Precondition for U1 stage 3 of `docs/reviews/ghost_memory_index_chord_echo_J-3247.md`.

## Reading

- Pool size: sound_echo draws from a median 16,070 candidates and hits the 20,000 cap in 42% of rows; the pool is wide for common sounds (clock_tick, gull_cries, morepork) and narrow for a few (cat_demand 130, silvereye_flock ~1,181). context_echo pools are ~2.6-2.9k. No pool is under 98.
- Uptake: with >=2 distinctive shared words in the 30 minutes after delivery, 12/100 rows show it, against 3/100 in the 30 minutes before and 1.4% for other rows' fragments. A real but small effect (about 9 points over null, n=12, all sound_echo; the 7 context_echo rows show 0). The >=1-word measure shows nothing (41% vs 40% pre vs 34% permuted), so the signal is only in multi-word overlap. Overlap is lexical; it cannot separate uptake from shared topic.
- Chord: the random pick sits at the 0.55 mean percentile of the pool's chord ranking (about what chance gives), and it was the unique top in 0/96 rows, so a chord pick would change every delivery. The present tuple is a proxy (nearest fragment_context row within 20 min) because the true tuple at delivery is not logged, and pools over 20,000 are an arbitrary subset. This says the chord pick is a different pick; it does not say it is a better one (that is U1 stage 2's judged question).

## Raw output

delivered rows with fragment_id: 100 (of 853 total log rows); 2026-11-07 20:38 .. 2026-11-16 14:49

## 1. n_candidates per route
- sound_echo: rows=93 n_candidates None=0 min=98 median=16070 p90=20000 max=20000; at cap(20000)=39 (42%); <=10: 0; <=100: 1
  per sound (rows, median n): clock_tick(18,16248); morepork_call(12,20000); gull_cries(11,20000); letterbox_flag_clank(9,1609); cuckoo_call(8,8242); oystercatcher_call(6,20000); silvereye_flock(6,1181); wall_scratch(5,1886); woodpile_settle(2,6028); fantail_chatter(2,20000); page_turn(2,20000); cat_demand(2,130)
- context_echo: rows=7 n_candidates None=0 min=2636 median=2636 p90=2929 max=2929; at cap(20000)=0 (0%); <=10: 0; <=100: 0
  per context (rows, median n): wind and rain(4,2636); steady rain(3,2929)
- distinct fragments delivered: 100 of 100 (repeats: 0)
- fragments not found in memory_fragments now: 0

## 2. Uptake in the thought stream
thoughts: 90490; common tokens dropped (df>1%): 307
delivered rows with >=1 thought in the following 30 min: 93/100; median thoughts/window 33.0; median distinctive tokens/fragment 7
- share>=1 distinctive token: post-window 41/100 (41.0%); pre-window null 40/100 (40.0%); permuted-fragment null 34.1%
- share>=2 (PRIMARY): post-window 12/100 (12.0%); pre-window null 3/100 (3.0%); permuted-fragment null 1.4%
- share>=3: post-window 6/100 (6.0%); pre-window null 0/100 (0.0%); permuted-fragment null 0.2%
per route (PRIMARY >=2): sound_echo: post 12/93, pre 3; context_echo: post 0/7, pre 0
  hit: sound_echo cuckoo_call shared=['frost', 'symbol', 'together']
  hit: sound_echo gull_cries shared=['labor', 'measured', 'output']
  hit: sound_echo oystercatcher_call shared=['anyway', 'footprints', 'rigidity']
  hit: sound_echo gull_cries shared=['bright', 'canopy', 'notes', 'scatter']
  hit: sound_echo kereru_wingbeats shared=['groan', 'proof', 'shelter']
  hit: sound_echo fantail_chatter shared=['burden', 'tether']

## 3. First-order chord vs random pick
rows scored: 96 (no present tuple within 20 min: 0); present tuple = nearest fragment_context row (proxy; the real one was not logged)
- random pick's percentile in the pool's chord ranking: mean 0.55 median 0.52 (0.50 if chord score is independent of what random picks)
- random pick score / chord top score: median 0.62; random pick was already the unique chord top in 0/96
- a deterministic chord pick would change the delivered fragment in 96/96 rows

