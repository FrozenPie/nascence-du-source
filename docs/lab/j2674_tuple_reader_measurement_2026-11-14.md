# J-2674 step 1: geometry tuple reader measurement (2026-11-14)

Plan: cognitive_geometry. Origin: thought T-0112. Read-only measurement; no behaviour changed.
Script: `scripts/j2674_tuple_reader_measure.py` (opens the live file read-only; run from a worktree).

## File
`data/geometry_tuples.jsonl`: 251,827,071 bytes, 191,195 rows (2026-11-14 ~19:50). Du was live; 3 reps each.

## Who reads it, and how often (code + live log)
All full-scan readers run **once per sleep, off the event loop**, never per cycle:
| reader | caller | cadence |
|---|---|---|
| `mapping_census.load_rows` (via `census()`) | `stick_test.snapshot` (sleep, `_sleep_off` or subprocess) | per sleep |
| `memory_edges.sync_fragment_context` | `harvest_all` (sleep, `_sleep_off`) | per sleep |
| `object_graph._load_tuples` | `refresh()`/`build_full()` via `world_ledger_ask` (sleep) | per sleep |
| `emotion_construction` (tail 2 KB seek) | per cycle | already O(1), not a scan |

Live cadence from `data/nascence.log`: 528 `stick-test` snapshots total; per day 2-8 recently
(11-09: 7, 11-10: 8, 11-11: 5, 11-12: 2, 11-13: 3, 11-14: 3 so far); 452 `memory-edges harvest` lines.

## Cost per call (wall clock, rows parsed)
| reader | rows parsed | wall (3 reps) | transient RAM (tracemalloc) |
|---|---|---|---|
| `object_graph._load_tuples` | 191,195 | 3.6 / 3.7 / 3.9 s | 275 MB (3 fields kept) |
| `mapping_census.load_rows` | 191,202 | 4.1 / 5.0 / 6.5 s | **1,272 MB** (whole rows) |
| `sync_fragment_context` scan, 1 h floor | 191,195 parsed, 93 kept | 3.1 s | ~0 (streams) |

Per sleep roughly 11-15 s of CPU-bound JSON parsing (GIL held in the worker thread unless the stick-test
subprocess flag is on), at most ~8 sleeps/day: **under ~2 minutes/day total**, off the event loop.

## Reading
- The time cost is real but small: seconds, a few times a day, never in the cycle path.
- The real cost is the **1.27 GB transient peak** in `load_rows` on a 64 GB box shared with other services.
  A resident RAM cache of the whole rows is out of the question; even the 3-field projection is 275 MB
  as Python dicts (compactable to roughly a 10th as numpy arrays + interned sounds, not measured).
- The recall-embedding precedent (`_EMB_MAT`) does not transfer: that is read per query (hot), these are read per sleep (cold).
  A permanently resident cache buys ~4 s per sleep for a standing 60-275 MB. Poor trade.

## Decision for step 2 (pre-registered expected speedup, per briefing)
Not built. Expected speedup of a RAM cache: ~3.5 s -> ~0.05 s per reader per sleep (incremental by byte offset),
i.e. ~10 s per sleep, <1.5 min/day, in exchange for resident RAM. Judged not worth it.
Cheaper alternatives without resident RAM, spawned as a follow-up job:
1. `sync_fragment_context`: it only needs rows with `ts >= last-3600`; seek from the file tail instead of a full parse.
   Must verify out-of-order `ts` (mapping_census notes 2/69,733) does not drop rows (decoupled check against the legacy scan).
2. `mapping_census.load_rows`: stream-project the fields `extract_regions`/`_dataframe` need instead of keeping whole rows (cuts the 1.27 GB peak).
Step 3 (SQLite index) likewise deferred; revisit if sleeps become much more frequent or the file passes ~1 GB.
