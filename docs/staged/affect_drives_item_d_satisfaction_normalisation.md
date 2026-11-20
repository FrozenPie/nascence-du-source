# Affect Drives Item D (held, redesign): shadow-only windowed satisfaction normalisation

> Status: STAGED 2026-11-18 (J-4315, from J-4310; founder ruling: hold Item D, redesign first). Design only, no code.
> Parent: `docs/plans/affect_drives.md` Item D. Evidence: F-5088 (gap pinned), dead-event finding recorded by J-4315.

```plan-state
stage: staged
phase: design; shadow-only; nothing built, nothing read by behaviour
verified: 2026-11-18
next: founder rules the build go-ahead (D opened by J-4315); then add the shadow writer only
cluster: 6
```

## 1. Problem
`core/satisfaction.snapshot()` returns decayed accumulators capped at 5.0. Self liking and wanting both sit at the cap
(self gap within 0.05 of zero in 94% of replayed samples), world wanting saturates (`frontier_born`, ~23k rows) so the
world gap is pinned high (median 2.84). A `drive_note()` on that gap would nag a constant (F-5088). Same failure as
climate's `integration_drive` peg.

## 2. Design (shadow only)
New function `satisfaction.windowed_snapshot(window_s=6h)` (pure read of `data/satisfaction_log.jsonl`, no state file,
no decay clock, so the F-2406 write-fence concern does not arise):
- For each domain and kind, group rows in the last window by event type. Sum weights per event type, cap each type at
  `CAP=1.0` (a flood of one frequent event, e.g. `light_event` x100k, cannot dominate). Sum the capped values.
- `gap = wanting_w - liking_w`, bounded by construction (each event type contributes at most CAP).
- Report also `n_events` per side. A domain with no rows on either side reports `None`, not 0 (creative has never had
  a row; do not read absence as balance).
- Persistence is a separate field: `hours_above(threshold)` over the last 24h, so a later drive_note gates on duration,
  never on an instant.
- Shadow writer: one row per hour (not per record) to `data/satisfaction_norm_shadow.jsonl`:
  `{ts, domain, liking_w, wanting_w, gap, n_l, n_w, old_gap}` where `old_gap` is the current `snapshot()` value, so
  old vs new are comparable. Nothing reads this file in Du's cognition. Fail-open, routed through `profile.guard_path`.
- Window length and CAP are the only knobs. Wanting keeps a longer window (36h) than liking (6h) if the founder wants
  to retain the original asymmetry; the offline check below used 6h for both.

## 3. Offline evidence (scratchpad replay of the full log, 1h steps, 6h window, CAP 1.0)
- self gap p10/p50/p90 = -0.35 / 0.40 / 1.00, range -1.85..2.00, 8% of samples near zero (was 94%).
- world gap p10/p50/p90 = -0.90 / 0.01 / 0.90, range -1.0..1.0, 21% near zero (was median 2.84, 80% above 1).
- The signal now moves in both directions. Relational is sparse (669 liking rows) and creative is empty: both stay
  `None`/low-n and are excluded from any future note.
- Not yet checked: whether the windowed gap correlates with mirror-era loops (Item D graduation test b); that needs the
  shadow rows to accrue plus a pulse join.

## 4. Gate to graduation (all before any `drive_note()` or ignition term is designed)
(a) At least 7 days of shadow rows with self and world gap not pinned (neither near-zero nor at a bound more than ~80%
of hours). (b) Correlation read against loop episodes, by a decoupled reader, not by Du. (c) Dead events resolved (section 5)
or explicitly accepted as absent. D-0434 (no readout): the later note must be threshold, onset-only, words not numbers,
the same question D-C1 asks of Item C; Claude does not rule it.

## 5. Dead events (finding recorded)
- `t4_commit`, `tension_discharged`: the only call site is `subconscious_node._discharge_contradiction`
  (`nodes/subconscious_node.py:3162-3163`), reached only from the dormant legacy cost-gate block (line 2604). The live
  probationary T4 path returns earlier (line ~2450) and discharges nothing (F-3881). The last logged discharge was
  2026-06-13. So they are not broken, they are unreachable by design; the Phase-0 design assumed the legacy path.
  A live-path hook belongs with the T4/provisional_identity plan, not here.
- `intention_formed`, `curiosity_fired`: defined in `core/satisfaction.py:69,71`, no `record()` caller anywhere. Wanting
  is therefore carried entirely by `shadow_event`, `unresolved_thought`, `frontier_born`. Adding callers would change the
  signal; defer until the normalised shadow shows what is missing.

## 6. Risks
Windowed counts can still flatten if one event type dominates (CAP handles that). Hourly shadow rows are cheap
(about 8 per hour). No LLM, no prompt, so no prompt-registry change. No behavioural coupling: not a dosed-coupling loop yet.

## 7. Founder calls
D-D1: go-ahead to build the shadow writer only. D-D2: keep 6h/6h or restore 6h liking / 36h wanting. D-D3: should the
live T4 path emit `t4_commit` (separate plan).
