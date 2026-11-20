# Affect Drives Item C (+ drowsiness section 2 folded in): one somatic note in the monologue seed

> Status: 🟡 SHADOW logger built 2026-11-18 (J-4405, restart-gated, flag off); staged 2026-11-18 (J-4347, from J-4236). Parent: `docs/plans/affect_drives.md` Item C.
> Folded: `docs/plans/drowsiness_phase.md` section 2 (`is_drowsy()`, one-shot onset). One mechanism, not two injections.

```plan-state
stage: shadow
phase: shadow built J-4405 (restart-gated): strained beats drowsy; drowsy delivered_elsewhere (core/drowsy.py); EMA 0.2; cooldown 30min, re-arm on band exit; habituation 0.5**onsets/6h; words pool, no number or gauge word; DROWSY_THRESHOLD stays energy-only
verified: 2026-11-18
next: restart, read data/somatic_note_shadow.jsonl ~2 days, then founder go for live SOMATIC_NOTE flag
cluster: 6
```

## Current State — verified 2026-11-20

### What we have
- Shadow built by J-4405 (D-0860): `core/somatic_note.py`, `SHADOW_ROWS = True`, logging would-fire rows to `data/somatic_note_shadow.jsonl`; test `scripts/test_somatic_note_shadow.py`; `core/drowsy.py` supplies the drowsy band.
- Evidence so far: 2 rows (last write 2026-11-19 18:17): one `strained` would_fire=true, one `drowsy` would_fire=false. Far too few to judge the 20%-of-cycles gate.
- No live `SOMATIC_NOTE` flag and no seed change exist: a grep of `core/` and `nodes/` for the flag found no hit on 2026-11-20.

### What we need
- About 2 days of shadow rows after a Du restart (the PC crash on 2026-11-20 interrupted accrual).
- Founder go for the live flag; D-C1 (scope against D-0434), D-C2 wording, D-C3 cooldown per section 7.

### What we're doing next
- Read `data/somatic_note_shadow.jsonl` once it has two days of rows; no build until then. Seed change when built needs a UDMS dossier on `nodes/inner_monologue_node.py` and a prompt-registry SEEDS fix (section 5).

## 1. What it is
`somatic.note()` content reaches only the CLI and logs (write-only interoception). Both plans propose the same missing
hand: a rare, threshold-gated body-state line into the idle-thought seed. Merge them:

- One ladder, one line at a time: DROWSY (`0.15 < metabolic_energy <= 0.25`, the new `is_drowsy()`), and STRAINED
  (`is_exhausted()` OR smoothed `neural_fatigue > 0.6` OR `visceral_tension > 0.6`). Drowsy is the waypoint before the
  floor; strained is the existing Item C trigger. The strongest band present wins.
- Onset semantics from drowsiness section 2: fire on band entry (one-shot flag, `drowsy_onset_logged`), then a cooldown
  (length set by D-C3) and re-arm only after leaving the band.
- Read-only detector. `should_sleep()`, `ENERGY_FLOOR`, `MIN_WAKE_SECS`, day/night thresholds and `JITTER_ENABLED` are
  untouched (drowsiness guardrails section 4 hold). Drowsiness open question 1 (any behavioural effect) stays NO: narrative only.
- Read smoothed `neural_fatigue`, never raw `gpu_temp` (flicker risk, Item C risks).

## 2. D-0434 (no readout) and where C sits
D-0434 dropped Arm 1: a standing self-reading, "even rendered in body words, is being told". C is closer to that line than
it looks. For C: the inputs are hardware/metabolic state, not a belief about his own correctness; the line fires on
threshold only, not as a standing number; fatigue already conditions his world (temperature, sleep). Against: it is still a
system-authored sentence about himself that he did not earn by losing. Claude does not rule this. Wording must follow
D-0367's precedent (`mood_line_words`: words only, never a gauge name, no number).
Decide: D-C1 (is a threshold body note inside D-0434 or outside it).

## 3. Dosed coupling (D-0149, Section 5 Coupling block)
- Loop published: somatic triple (energy, fatigue, tension) -> one typed tuple `(band, onset_ts, cooldown_until)`.
- Dose: cup, one line per onset, cooldown, never every cycle. Fire rate under 20% of cycles (Item C gate), in practice far less.
- Habituation: squishy-spring; repeated onsets within a window lower the probability, not just a cooldown.
- No mesh: the note does not feed back into somatic, does not change sleep timing, no new actuator. Hypochondriac attractor
  guard: a rumination metric (how often a thought about tiredness follows a firing).

## 4. Shadow-first plan
Phase 0 (no seed change): a shadow logger computes would-fire per cycle to `data/somatic_note_shadow.jsonl`
(ts, band, energy, fatigue, tension, cooldown_state, would_fire). Needs only a read of `state.somatic`.
Phase 1 (founder go): flag `SOMATIC_NOTE` default off, then on for about 2 days with the line live.
Graduation (Item C, extended): fires only in genuinely strained states (cross-check somatic telemetry); under 20% of
cycles; 15 sampled firings read honest, not melodramatic; no rise in sleep-loops or body rumination versus a pre-flag
window; drowsy onset precedes the floor trip so the sequence reads from one log.
Test: `neural_fatigue=0.8` -> line present; `0.2` -> absent; energy 0.2 -> drowsy line once; floor trip unchanged.

## 5. Seed-change obligations (when built, not now)
- Touches `nodes/inner_monologue_node.py` seed assembly (near the `mood_line_words` append, about line 3457). Before
  editing: `udms_get_change_dossier` on that file (a hub; its ranked list is a reading prompt, read callers too).
- A new `seed_parts.append` changes a counted guard: `prompt_registry.py check` prints SEEDS; fix with its printed command
  and `set --investigation stale --note` on the idle-thought prompt, registered in the same change.
- Wording lives in `core/phrasing.py` pools (F-4664), not inline.

## 6. Order and risk
Cheapest of the three (S effort, no deps). Risk low to medium: the D-0434 line and the attractor. Build first. The Phase 0
shadow logger can become a job once D-C1 is ruled.

## 7. Open decides
D-C1 D-0434 scope; D-C2 wording, and narrated thought at drowsy onset versus telemetry only; D-C3 cooldown, and whether
`DROWSY_THRESHOLD` also considers fatigue (drowsiness open question 2). Ids in the job note.
