# J-3767 shock-trace scripts (committed by J-4010)

Read-only scripts behind F-4690..F-4693, committed unchanged (header comment added) so J-3764 can re-run them after pursuit lookup retirement:

- `scripts/j3767_shock_trace_t4_dream.py` - main trace (T4 per-exposure, dream day_material top-6 at core/night.py:419, world-ground reconstruction with `--embed`, wandering streams). Args: `--out DIR --days N`.
- `scripts/j3767_shock_trace_detail.py`, `scripts/j3767_shock_trace_detail2.py` - detail passes (detail2 takes days as argv[1]).

All import `scripts/j2916_shock_trace.py` by the absolute path C:\Nascence\scripts and read C:\Nascence\data; no live writes.

Baseline to compare (30 d to 11-14): dream cites 7/55 shocks vs 7/233 pursuit; shock in day_material top 6 for 51/136 dreams; T4 per-view 4/57 shock vs 1/193 pursuit; wandering appearances per page 0.22 shock vs 7.3 pursuit.

Deviation from the J-4010 briefing: not merged into one file and no synthetic test (instruction was no logic change); syntax-checked only.
