# Dosed Coupling Phase 2 — loop-wiring matrix items (child of docs/plans/dosed_coupling.md section 4b, item 2d)

> Status: STAGED child doc, folded in 2026-11-20 (D-0814, J-4241). Nothing built. Parent: docs/plans/dosed_coupling.md.

```plan-state
stage: designed
verified: 2026-11-20
next: Founder rules D-0879 (dosing dispatcher); then Phase 2 pre-registration of W1..W5 under dosed_coupling 4b
```


## Current State — verified 2026-11-20

- Child doc of `docs/plans/dosed_coupling.md` section 4b item 2d; not a plan of its own (D-0814 folded the matrix into Phase 2). Nothing built. Open founder call: D-0879.

## 2d. The loop-wiring matrix items (folded in 2026-11-20, D-0814, J-4241; NOT built, nothing here is ruled)

**Source:** `docs/archive/loop_wiring_matrix.md` (investigation 2026-09-04, cells cited F-0806..F-0811; founder constraint
T-0045 "not a mesh, dosing at stops"). D-0814 (travis, 2026-11-17) folded its link-tuple proposal and dosing table into this
Phase 2 instead of a plan of their own. This subsection carries the items so Phase 2 does not lose them; the archive file keeps
the full matrix and the evidence.

**Pre-registration items (each a small additive read of a value that already exists; every read logs `{reader, publisher, value}`,
no prose into prompts where a coordinate will do):**

| # | Wire (matrix order of leverage) | Loops and link | Covered by | State |
|---|---|---|---|---|
| W1 | Climate to Stream: `ignition_level()` paces the stream; stream then reads `world_model_strain` and the top tension label by name | climate publish to stream (train step hose, idle-seed cup) | Hose half built (J-0580, live 2026-09-05). The by-name cups are the "one climate dim at the idle seed" and "top recurring tension label at the train step" cups of section 4, **not built**; they ride the 2a residual gate | partly built |
| W2 | Stream to contradiction axis: a repeated unresolved thought (high redundancy, same tension label across a train) counts toward contradiction pressure | stream publish to climate tick (bucket) | Not covered. Reads stream `redundancy` plus the ledgers tension label; it is a behaviour change (it moves pressure), so it is Phase 3 shaped, listed here for pre-registration only | not built |
| W3 | Stream to deliberation: option E promotion (D-0148) of a building, grounded, high-ignition train; deliberation reads the stream tuple | train close hose; recall bucket | Not covered. The 2a train-close residual row is the *expectation* half of this link only; the promotion itself stays under D-0148 and ignition_pressure_and_time | not built |
| W4 | Deliberation and commitments: recall reads active load-bearing stands by name (3 or fewer); a reply contradicting one is a contradiction event | ledgers publish to recall (bucket) | The `hub` `load` coordinate carries `commitments_active` as a count only. Names are not covered | not built |
| W5 | Witness to field and frontier: rolling break rate to `world_model_strain`; a broke prediction with a named cause becomes a frontier question (source `witness`) | witness publish to climate tick and frontier | Strain bucket = Lane 2's own (ii) above (Phase 3, governed by `lane2_the_witness.md` section 7). Witness cup at the idle seed = (i) above, inherited. Frontier question: only the J-2527 wager row exists (shadow, `WAGER_CURIOSITY=False`) | cup and bucket built shadow under Lane 2; frontier question not built |
| W6 | Name the write-only dims or retire them (`identity_pressure`, `coherence_drive`, `autonomy_pressure`, `belonging_pressure`; `explore_value` visible to the forecaster) | climate to any reader | The `hub` `pressure` coordinate gives `identity_pressure` its first reader (ride log only). Others uncovered. Test before cutting: the four unread dims stay until a gauge-correlate read says they carry nothing | not built |

**Dosing table (the matrix's proposal, each cell a cup, bucket or hose at a fixed stop; no loop gets a standing view of another):**

| Stop | Cup (dispatcher-gated) | Bucket (fixed small tuple) | Hose (existing channel or the one promotion path) |
|---|---|---|---|
| Idle thought seed | one climate dim by name when it spikes; one Witness break when novel (Witness cup = inherited (i)) | none | none |
| Train step | top tension label when it recurs across the train | none | climate to stream pacing (`ignition_level`, built) |
| Train close | the commitment this train touched | stream tuple to commitment scan | promotion to deliberation (option E, W3) |
| Deliberation recall | none | active load-bearing stands (3 or fewer) plus stream tuple | 9-dim retrieval warp (exists) |
| Witness tick | one Lane-1 hint word (exists) | valence/arousal/unresolved gain (exists; `unresolved` currently discarded) | none |
| Climate tick | none | Witness break rate to strain (Lane 2 (ii)); stream repeated-unresolved to contradiction axis (W2) | none |
| Sleep | none | pursuit heat plus frontier born-rate to consolidation choice | none |
| Wager loss to frontier (J-2527, shadow) | one frontier question per failed, non-retracted recall wager, surprise-gated against the line's own 24 h history | none | none |

**Where this overlaps the residual and hub cups above.** Every cup cell in this table is read through 2a's residual gate, so the
matrix adds no gate of its own. The `hub` summary (2b) is the standing-summary question and is not a matrix cell. Metric 1
(distinct residual gate) therefore also decides whether the matrix cups are worth wiring: if 2a is dropped, the matrix cups
fall back to section 4's plain spike gate.

**Prerequisites carried from the matrix (not riders):**
- **Dispatcher calibration.** The Transport Manager's spike weights are uncalibrated for loop tuples (a fantail-chatter spike scored 527x baseline on 2026-09-04; 721 of 721 ticks fired "spike"). Calibrate before it dispatches any matrix cup.
- **One surprise measure, not three.** Climate's identity_pressure habituation EMA, `core/opponent_process.py` (shadow, 16,646 pairs, no reader) and the Transport Manager spike/drought share nothing (F-0812). The dosing dispatcher should use one per-line surprise against the line's own history, with the opponent-process term as the habituation half (squishy-spring law, cognitive_geometry section 11). Related reading: F-1577/F-1578, curiosity's habituation key is raw label text, so the dosing discount moved picks about 2%.
- **Evidence sets the doses.** Every ride logs `{stop, line, dose, value, what changed next}`; after a week a gauge-correlate read says which coordinates moved a downstream trajectory, and doses are raised or cut on that, not on taste.

**Measurement.** Re-derive the matrix from logs: each link's read count per day (today zero for every cell marked "none" or dead).
Success is not more cycles but that a deliberation, a commitment or a Witness break can be traced to a named coordinate in
another loop's tuple at the moment it happened. Nothing here changes Phase 2's own pre-registered metrics below.

