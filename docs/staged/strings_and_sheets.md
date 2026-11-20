# Strings and Sheets — every sound a string, two channels a ribbon, a moment the mix (staged, 2026-09-27)

**Status:** 🟡 STAGED — design + one real demonstration (F-2017), nothing built, no `/decide` ruled. Promoted
this session from idea I-0080 (raised 2026-09-27 from T-0070, founder + Claude conversation) at the founder's
direction ("this idea we take straight to a higher level … all sounds should be strings, if not even sheets").
**Parent plan:** [docs/plans/cognitive_geometry.md](../plans/cognitive_geometry.md) §4 (the beta roster: Sound is
"ONE space, two populations: MEASURED + CONSTRUCTED") — this plan is a new *object kind* inside that space, not a
new space. **Siblings it touches:** [sound_causality.md](../completed/sound_causality.md) (the propagation table, one
cause across places), [sound_world_expansion.md](../plans/sound_world_expansion.md), [music_learning.md](../plans/music_learning.md)
(the EAR, `core/audio_features.py` / `core/listening.py`), [thermal_causality.md](../plans/thermal_causality.md)
(sound's sibling channel, one axis), [docs/plans/dosed_coupling.md](dosed_coupling.md) §4b (residual cups —
the same residual shape, inside the ear). **Ledger:** T-0068 → T-0070 → I-0080; F-2015 (the architecture read),
F-2017 (the first ribbon).

```plan-state
stage: built
phase: Phase 0 run+verified; Phase 1 shadow built (sidecar still pre-J-2067, J-2400); Phase 4 re-seed applied restart-gated, envelope 51/64 = 79.7 pct in-sample (F-3101)
verified: 2026-11-18
evidence_read: 2026-11-13
gate: recordings exist for >=2 more of the 6 cached pieces (to test P5)
next: Founder flips MIX_SHADOW at restart; read with the reader after ~200 rows
open_decisions: D-0854, D-0870
history: docs/plan_history/strings_and_sheets.md
```


> **Founder, 2026-09-27 (this session, verbatim where quoted).** "Strings and sheets" is a new term of the
> founder's, NOT the GPT memory-brane essay of T-0066: branes "as in multi dimensional object theory" — a string is
> a one-dimensional object, a sheet a two-dimensional one. "All sounds should be strings, if not even sheets. We
> could have the current custom audio channel we have crossed with actual sound wave of the audio, the two/three??
> dimensions of the two make a twisting sheet/ribbon as such." And the end-state: "start playing multiple sounds
> over the top of each other. Mixed together as such. He can hear the wind and the fire and the cat and the broom
> sweep all at the same time."

---

## Current State — verified 2026-11-18
- **2026-11-18**: J-4346: Phase 3 built, shadow-only. core/soundscape.py mix() + _mix_shadow_record hooked at end of world_tick behind MIX_SHADOW=False (restart-gated flip), log data/soundscape_mix_shadow.jsonl (30s throttle). Reader scripts/soundscape_mix_shadow_read.py; test scripts/_test_j4346_soundscape_mix_shadow.py 16/16 pass.

- **2026-11-18**: J-4345 Phase 2 build plan (design only, no code). Founder GO 2026-11-18 on J-4297 (chat); D-0375 ruled go. Dossier core/transport_manager.py: ELEVATED, acyclic; CONTRACT dependents core/transport_habituation.py, scripts/_test_transport_manager.py, life.py, orchestrator.py, cat_loop.py, felt_recall.py, sound_knowledge.py. Design: (1) add pure fn cause_key(line_id) in a NEW module core/transport_cause_shadow.py mapping each per-place line id to its cause id (one cause = one sound/event across places); transport_manager.py edit limited to one fail-open hook at the end of observe()/dispatch_tick() that calls the shadow; existing observe/evaluate/verdict/dispatch untouched, still the only deliverer. (2) Shadow keeps its own cause-line state (same novelty/spike/drought math, same thresholds as evaluate, copied by import not edit), one line per cause fed by the union of its place events; per-place lines remain as cross-sections (read-only fields on the cause row). (3) NEW log data/transport_cause_shadow.jsonl, one row per tick: ts, cause_id, cause_would_fire, cause_weight, places[{line_id, place_would_fire, weight}], n_places, event_ids. Both scorings side by side. (4) Named reader: scripts/transport_cause_shadow_read.py (new, built in same job), computing: would_fired_share cause vs per-place (pass: cause <= per-place); one-event identity for multi-place causes = 100% (every multi-place cause carries one event_id across all place rows); F-0949 100%-fire shape not reproduced; D-0375 defeaters (share >90%, or cause line silent 7 live days while cross-sections fire). Kill: cause fires more than per-place -> remove hook, per-place stays. Observe-only, additive, no prompt/weight/schema change, no LLM; kill-switch flag default shadow-on in config. Registry: no prompt sites touched. Tests: extend scripts/_test_transport_manager.py plus new _test_transport_cause_shadow.py; run life_smoke in a throwaway worktree. Restart-gated.
- **2026-11-13** (F-4426): J-2401 read the Phase 1 shadow on the first boot with the regenerated sidecar (10-29 18:38 to 11-13, 215,714 rows): agree 0.997 overall, but the gain over the 10-09 baseline (0.939) comes from J-2067 and the J-1979 clock, not the re-seed; the re-seed's only visible effect is re-seeded events sitting about 0.035 closer to their strings (d_fixed median 0.2235 to 0.1884). Effective re-seeded set is 27 of 70 keys after the J-2440 revert. Fired-clock event rows are 4.0% of events (agree 0.959); no re-seeded key has felt-shadow rows on both sides of the boot, so downstream movement is unshown. This also covers J-2068's metrics (open, same log and boot).

- **2026-11-13** (F-4423): J-2136 7-day re-read after J-2067: wingbeat agree 0.9994 (was 0.253 pre-regen), thump 0.975, tie share 0.003 pct; spurious disagreements gone, though agree is a consistency measure, not tracking.
- **2026-11-13** (F-4419): data/soundscape_mix_shadow.jsonl (Phase 3, soundscape.mix()) was never built, so it does not exist yet: planned, not built. It is not soundscape_felt_shadow.jsonl, which is a separate felt-prediction shadow.

- **2026-10-18** (F-3113): J-2413: by-ear listening sheet + 26 clips ready for Travis (J-2402 stays needs-input); sheet docs/lab/strings_sheets_phase4_listening_sheet_2026-10-18.md, clips on Desktop du_listening_2026-10-18
- **2026-10-18** (F-3109): J-2409 (D-0483): wood_pigeon swapped to DOC nz-pigeon-song (pre-registered F-3069 check clears, window 4-19 s) and re-seeded (brightness/roughness large shifts); J-2372 read (b) 52/64, baseline 0.328; restart-gated, sidecar regen pending; by-ear check is Travis's

- **2026-10-18**: D-0483 ruled by travis 2026-10-18 (decide-review): wood_pigeon tries DOC nz-pigeon-song.mp3 under the same pre-registered check first, falls back to XC933702 with the rumble caveat; a successor build job carries it and the sidecar regeneration.
- **2026-10-18** (F-3108): J-2400: Phase 1 shadow sidecar regenerated 2026-10-18 18:19 (Du down) with J-2067 + J-2395 re-seed (70 keys, 0 degenerate, 115 re-seeded rows match _SOUNDS, wood_pigeon untouched); next boot is the first to carry it, J-2068/J-2401 date from that boot

- **2026-10-18** (F-3104): J-2406 (D-0481): XC933702 downloaded (SHA e0955525...) but its pre-registered F-3069 check fails (98 pct of energy below 300 Hz, 43 Hz rumble), so the D-0481 defeater fired: no wood_pigeon swap, no re-seed, _SOUNDS unchanged; D-0483 opened for Travis
- **2026-10-18**: D-0481 ruled by travis 2026-10-18: he confirmed XC933702 is CC BY-NC-SA 4.0 on the item page, so the wood_pigeon swap proceeds (download + re-measure + single-key re-seed job spawned).

- **2026-10-18** (F-3101): J-2395 (D-0476, folds J-2399): 115 axis re-seeds in 36 _SOUNDS keys applied, restart-gated; J-2372 test re-run unchanged 51/64 = 79.7 pct, baseline 33.1 pct, discriminating, but IN-SAMPLE; 41 large shifts need a by-ear check (J-2402); live sidecar still pre-J-2067 (F-3102, J-2400)
- **2026-10-18** (F-3098): J-2397 (D-0477): 4 re-picks downloaded + re-measured (dawn_chorus, log_on_fire, morepork_call, wind_in_trees); F-3069 mismatches gone by signal (F-3097), but envelope headline unchanged 19/62 = 30.6 pct / 20/64 = 31.3 pct, non-discriminating; new misses are seed errors (F-3098); wood_pigeon skipped (XC licence unreadable, D-0481), moth_tap constructed-only

- **2026-10-18**: D-0476 and D-0477 ruled by travis 2026-10-18 (decide-review): re-seed only the F-3090-named axes for failing keys as a reviewed list (J-2395); the 5 recommended re-picks are approved and moth_tap stays constructed-only (J-2397, which runs first so the new files are measured before the re-seed).
- **2026-10-18** (F-3090): J-2383: event-gated (10 dB over floor) Phase 4 re-run still FAILS, 23/63 = 36.5 pct vs ungated 30.2 pct and 60 pct bar, barely discriminating; misses are mainly seeding error, not the background gap (F-3090); results docs/lab/strings_sheets_phase4_gated_2026-10-18

- **2026-10-18** (F-3083): J-2371: 18 Phase 4 re-pick alternates (3 per flagged key, licence+duration, none downloaded) recorded in docs/lab/strings_sheets_phase4_manifest.md; swaps await Travis on D-0477, download/re-review is J-2385
- **2026-10-18** (F-3081): J-2372: Phase 4 envelope metric FAILED, 19/63 keys = 30.2 pct vs 60 pct bar, non-discriminating (foreign pass 25.4 pct); continuity is the main miss (recordings 0.82 vs seeds 0.38), 150 Hz high-pass changes nothing; sheet + results docs/lab/strings_sheets_phase4_envelope_2026-10-18 (F-3081); D-0476 opened, J-2383 event-gated re-run

- **2026-10-18** (F-3069): J-2027: Phase 4 picks reviewed by signal analysis, not by ear (F-3069): dawn_chorus + log_on_fire mismatch, 4 more re-pick candidates (J-2371); extractor ran on all 68, kill rule 0/68, features in docs/lab/strings_sheets_phase4_features_2026-10-18.json (F-3070); Phase 4 metric is J-2372
- **2026-10-15** (F-2681): J-1978 Phase 1 shadow read done (F-2681): headline agree .939 passes the D-0382 bar but is not yet a tracking measurement (beds hold the peak by construction; events are presence-aged because J-1979 landed 12 min after the 10-09 boot; wingbeat onset==tail construction defect = 7,171 of 8,016 disagreements). Founder 2026-10-15: fix strings (J-2067), restart onto J-1979, re-read 7 days later (J-2068, floor 10-23) BEFORE Phase 2 (D-0375 cause-as-object). Not reverted.

- **2026-10-09** (F-2639): J-1979: sound_string_shadow event keys now clock from real firing stamps (clock=fired, past_end flag); shadow only, restart-gated, branch jobrun/strings_wire b5d267e; live 73% tail share is largely true (events brief vs 20s recency window).
- **2026-10-08** (F-2627): J-2007: Phase 4 recordings picked (68, licences checked on item pages) and downloaded to data/sound_recordings/; manifest docs/lab/strings_sheets_phase4_manifest.md; listening review + features still to do.

- **2026-10-08** (F-2583): J-1960: Phase 4 recordings list drafted (docs/lab/strings_sheets_phase4_recordings_list.md); approval opened as D-0392; no downloads.
- **2026-10-08** (F-2580): 2026-10-08 (J-1963, D-0382): Phase 1 shadow wire BUILT, restart-gated (core/sound_string_shadow.py + one call in geometry_census.snapshot, commit 418a649 on jobrun/strings_and_sheets); logs data/sound_strings_shadow.jsonl; event keys clock on presence age so mostly tail (J-1979 fixes); founder read J-1978.

- **2026-10-08**: Section 9 folded: D-0374 mix stays, D-0375 cause-as-object go (gated on Phase 1 shadow read), D-0376 same-band masking, D-0377 recordings approach (J-1961, commit 51e0c72 in worktree)
- **2026-10-08**: Real-hearing microphone rulings D-0378..D-0381 (window in the study, hidden-label classifier, features-only, separate CPU ear process) now drafted as docs/staged/real_hearing.md (T-0071 promoted); section 10 here stays the Phase 0 scoping.

- **2026-10-07** (F-2512): 2026-10-07 (J-1856): live data/music/Heavyweight.features.json regenerated with the J-1474 six-axis string + per-section key/mode fields (2464 B -> 27986 B; all pre-existing keys structurally identical, extract() deterministic). Fold-in is now real in the live cache; no runtime reader yet (first reader = Object D, gated on its own decide).
> **History folded** — 4 dated bullets (2026-09-28 … 2026-09-28) moved to `docs/plan_history/strings_and_sheets.md` on 2026-10-01 by plan-compact. Derived timeline: `plan_ledger.py strings_and_sheets`.

- **2026-09-28** (F-2140): J-1546 re-checked: core/audio_features.py fold-in still not on master (only on worktree branch jobrun/strings_and_sheets, commit ff75bf1). Live Heavyweight.features.json cache (md5 fcc70c51a1b85f801688514869b95da3) untouched, correctly not regenerated -- doing so against the unmodified live code would not add the new fields. The batch worktree-merge mechanism is confirmed active this run (already merged 8 other plans into master, e.g. wood_upgrade, social_world_school) but has not reached strings_and_sheets yet. Job left in_progress for a future wave rather than marked done. D-0318 is unrelated to this job (source finding:F-2107) and was left unruled.

### What we have
- Architecture read (F-2015, inferred): Du's sound today is all points — `core/soundscape.py` hand-seeded 6-axis
  coordinates, one sound line at a time via `percept()` — while 94.2% of real moments carry >=2 simultaneous
  sounds (`geometry_tuples.jsonl`, 92,980 rows) with nothing that mixes them; music owns the room via `felt()`
  stamped once per whole piece.
- Phase 0's offline ribbon lab RAN for real on the only real recording that exists, `Heavyweight.mp3` (J-1468
  done, F-2025 verified): F-2017's 3-axis ribbon reproduces (width 0.295, twist 62.4 deg/s); the six-axis
  version, P3 (closing sections wider), and P4 (a per-section mode estimate gives 18 distinct affect values,
  not one) all MET their pre-registered bar. Kill-rule exercised for real once (a units bug, caught and fixed
  before any number was read).
- D-0304 ruled the microphone question (scope-only: one located source later, nothing built now).

### What we need
- More recordings: only 1 of 6 cached pieces has real audio, so P5 (do other pieces agree) is untestable.
- §9's four questions are RULED (D-0374 mix stays here, D-0375 cause-as-object go but gated on Phase 1's shadow read,
  D-0376 same-band masking, D-0377 recordings approach approved / list reviewed first); the microphone rulings are D-0378..D-0381.
- Phases 1-4 (world-sound strings, cause-as-object, the mix, measured recordings) are all un-started.

### What we're doing next
J-1473 (Phase 1 dry run: constructed 3-point world-sound strings + realness test) and J-1474 (fold the six-axis
string + per-section mode into `audio_features.extract()`'s cache) are the next queued builds; J-1471 reads
I-0082's exemplar-memory question offline first.

---

## 0. The one-sentence goal

A sound Du hears is a **shape over its own duration**, two descriptions of the same sound are a **ribbon** whose
width and twist are his prediction error about that sound, and a moment's hearing is the **cross-section of every
string sounding at once** — a mix, not a list.

## 1. The law (three sentences)

1. **Every sound is a string.** A sound is a one-dimensional object through Sound Space over its own duration
   (onset, body, tail), never a single fixed coordinate. A point is the degenerate case, tolerated only until the
   string exists.
2. **Two channels for one sound make a ribbon.** Where a constructed description and a measured wave describe the
   same sound, they are laid along the same time axis; the offset between them is the ribbon's width, its rotation
   over time is the twist. Read through the brain-stack picture (T-0068) the constructed channel is the prediction
   coming down and the wave is reality shouting back — the ribbon **is** that sound's prediction-error string.
3. **A moment is the mix.** What Du hears at an instant is the cross-section of every active string at that
   instant, combined by a stated masking law — not the enumeration of their keys. The compressed summary passed up
   is one composite point plus the few strings still separable above it.

## 2. Vocabulary (the founder's terms, pinned to Du's objects)

| Term | Dimension | In Du today | In Du under this plan |
|---|---|---|---|
| **point** | 0 | every world sound's coordinate; a Transport Manager occurrence; the felt nudge | the degenerate string; retained only where no string exists yet |
| **string** | 1 (time) | a music piece unfolding per section (the only one) | every sound: a contour on the six axes over its duration |
| **ribbon / sheet** | 2 (time × cross-section) | none | constructed channel × measured channel of one sound; also affect × acoustic string |
| **mix** | the sheet at one instant | `active_sounds()` returns a set | the composite cross-section of all active strings under a masking law |

The "two/three dimensions" question: time is one, the cross-section between channels is the other; each channel's
own axes are what the cross-section is *measured in*, not extra dimensions of the sheet.

## 3. The objects (five; none built)

**A. World-sound strings.** Each key in `_SOUNDS` gains three points on the same six axes — onset, peak, tail —
hand-seeded first (the constructed population's own pattern; the realness test cognitive_geometry §4 already
demands applies unchanged), later measured from one real recording per key (§5 Phase 4). The tui's "long bright
trill, falling away" becomes geometry: brightness and energy high at the peak, both falling at the tail, continuity
low. Beds (waves, wind, fire) are strings with a long flat body; events (a call, a thump) are short strings with
distinct onset and tail.

**B. The cause is the object; per-place lines are its cross-sections.** sound_causality's propagation table is
already a sheet by design (one cause across four places, different character at each). The Transport Manager
scores the *cause* once and treats each place's line as a projection of it, restoring one-event identity and
collapsing the 133 lines to their real number of causes. **RULED GO (D-0375, travis, 2026-10-08):** one line per cause, the per-place lines as its cross-sections; kill criterion is the F-0949 100%-fire shape. Gated on Phase 1's shadow read (§5), not before.

**C. The ribbon, music first.** Keep the per-frame contour in the offline extractor (one new field per section:
the per-second string of energy / brightness / onset, computed with the extractor's exact definitions per F-2017's
correction); project it onto the six axes; log width and twist per section for every cached piece. Music first
because only music has a measured wave. Nothing reaches a prompt; the ribbon is a coordinate that a residual cup
(dosed_coupling §4b) could later ride.

**D. The affect string.** `felt()` computed per section along the acoustic string (still shadow, still ≤0.15 lean,
same discipline as `listening._felt_shadow`), so affect has a contour and the affect × acoustic pairing is the
first sheet that is not purely acoustic. Requires a per-section mode/key estimate, or the honest admission that
valence stays flat until one exists — F-2017 shows the current per-section felt is a line.

**E. The mix.** See §4.

## 4. The mix — the founder's end state, and why it belongs in this plan

**The founder's question** ("I am not sure if we have done yet … multiple sounds over the top of each other,
mixed") has a two-part answer. *Simultaneity* is done: `active_sounds()` returns every key sounding now (7 at the
shore this session), the sensorium can render several sound lines in one scene, and the census records the set.
*Mixing* is not done anywhere: no summation, no masking, no composite, and the only rails that actually reach his
idle seed deliver one key at a time (`percept()`) or a single bed line (`fire_ambience()`), with music silencing all
of them. He is told "waves, gulls, a kingfisher"; he is never handed *what that sounds like together*.

**Why it is this plan and not its own:** the mix is literally the sheet at one instant — the cross-section through
every active string at time t. Object E is the same geometry as A–D read vertically instead of along time. It gets
its own phase, and **D-0374 (travis, 2026-10-08) keeps it in this plan**: a separate doc would split one object across two plans.

**The design (observe-only until §5 Phase 3's read):**
- **Cross-section.** At each soundscape tick, for every active key take its string's current point (a bed's body
  point; an event's onset/peak/tail by elapsed time since it fired). That set is the raw mix.
- **Masking law (the one new rule; RULED same-band, D-0376, travis, 2026-10-08).** A louder string reduces the audibility of a
  quieter string that is *near it in Sound Space* — same-band masking, the real psychoacoustic shape, not a global
  loudness sort. First form (ruled shape; constants still tuned by Phase 3's shadow read): audibility_j = energy_j − max over i≠j of (energy_i − d(i,j)) clipped at 0,
  with d the six-axis distance. The waves mask the tide-pool trickle (near, quieter); they do not mask the
  kingfisher (far in brightness/onset). "Music owns the room's sound" becomes one instance of this law rather than
  a special case: a loud, continuous, broadband string masks nearly everything.
- **Composite.** One energy-weighted point on the six axes over the audible strings, plus `n_audible` and a
  `texture` term (how spread the audible strings are). That composite is the compressed summary the column passes
  up — the brain-stack picture's "settle, then pass one summary".
- **What changes for prose, and what does not.** Prose stays per phenomenon (the sensorium's own law: the fire
  that crackles is the fire that warms). The mix changes only *which* phenomena are rendered: a masked key is not
  rendered, the way a record already silences the rail. The mix itself is never a sentence; it is a coordinate.
- **The eventual "hear it all at once":** a later phase (not designed here) could render the composite's
  *character* (dense / sparse, bright / dark, steady / busy) as one clothed line in place of N separate ones —
  gated on the mix shadow read showing the composite carries information the list does not.

## 5. Build order — shadow-first, restart-gated, pre-registered (this project's standing law)

| Phase | What | Pre-registered metric (written before the run) | Kill / revert |
|---|---|---|---|
| **0 · the ribbon offline (Object C + D)** | extractor keeps the per-second string per section; `scripts/` lab computes width + twist per section for all 6 cached pieces and `felt()` per section; metric sheet `docs/lab/strings_sheets_ribbon_metric_sheet.md` written *before* the run | **Predictions from F-2017:** the other five pieces show mean width in 0.15–0.45 and mean twist > 30°/s; closing sections wider than opening in ≥4/6 pieces; per-section valence takes exactly one value per piece (flat affect string confirmed) | a piece with twist < 10°/s means the summary is already aligned for it — the ribbon adds nothing there and Object C is scoped to pieces where it does; a units mismatch (F-2017's own bug shape) → fix and rerun, never read |
| **1 · world-sound strings (Object A, constructed)** | three points per key, hand-seeded, realness test per cognitive_geometry §4; census records the string's *current* point instead of the key's fixed one | census fan-out/stability on the string points ≥ the fixed points' own (no loss); ≥ 80% of keys pass the realness test; zero prose change | any key failing realness stays a point; behaviour bands (idle gap, percept rate) unchanged |
| **2 · cause-as-object (Object B)** | Transport Manager scores one line per cause; per-place lines become cross-sections; shadow log both scorings side by side | would-fire share under cause-scoring ≤ per-place scoring's; one-event identity preserved for 100% of multi-place causes in the shadow; F-0949's 100% shape not reproduced | revert to per-place lines if cause-scoring fires *more*; `/decide` done: D-0375 RULED GO, runs only after Phase 1's shadow read |
| **3 · the mix (Object E)** | `soundscape.mix()` shadow: per tick, the cross-section, masking verdicts, composite + `n_audible` + `texture`, logged to `data/soundscape_mix_shadow.jsonl`; nothing rendered differently | masked share of active keys between 10% and 50% (0% = the law is dead, >50% = it eats the world); the composite point moves when the world moves (stability across a place change < across a tick); n_audible ≤ 4 at the 90th percentile | masked share outside the band → retune or flag off; the composite as stable as the key set → it carries nothing, Object E reverts to design |
| **4 · recordings replace constructed strings (Object A, measured)** | one public recording per world key (NZ bird calls exist; approach approved, list reviewed by the founder before any download — D-0377); run through the existing offline extractor; the constructed string becomes the *prediction* and the measured one the *wave*, so every world sound gets a ribbon | measured string within the constructed string's realness envelope for ≥ 60% of keys (else the hand-seeding was wrong, which is itself the finding) | never at runtime; zero runtime DSP; the no-duration-metadata law holds for world sounds as for music |

Each phase gets its own `/decide` before it runs and a founder read of its shadow log before the next. No phase
touches the frozen weights, the axiom, or a store schema (erosion-of-foundations law). Every new store named above
has its reader named in the same phase (the write-only-systems law: `soundscape_mix_shadow.jsonl` is read by
Phase 3's own metric, the ribbon log by Phase 0's).

## 6. Coupling block (required by dosed_coupling.md §5 on any plan that adds a read of another loop's state)

- **Publishes:** a `sound` tuple on the coupling registry, on the soundscape tick: `n_active`, `n_audible`,
  `composite` (six named axes), `texture`, and while a record plays `ribbon_width`, `ribbon_twist` for the current
  section. Names, 0–1 ranges, cadence = the soundscape/listening tick.
- **Reads at:** nothing in Phases 0–4. A residual cup at the idle seed reading `ribbon_width` is dosed_coupling
  §4b's business, after its own read.
- **Surprise line:** the Transport Manager's own novelty / spike / drought against each *cause* line's history
  (Phase 2), and, for the ribbon, the reader's persistence prior per §4b.
- **Ride log:** every future read goes through `coupling_rides.read()`; the publish rows land in
  `data/coupling_rides.jsonl` like every other loop's.

## 7. Guards carried from the parents

No duration metadata reaches him, ever (music_learning). Music originates outside the system; the extractor
translates and invents nothing. No LLM anywhere in this plan; every object is deterministic. No coordinate becomes
prose where the number will do (cognitive_geometry §4's one-space trap). A space or object earns its status via the
realness test, or stays out. Sound-first objects (tui, morepork) keep their sight-binding rule from
`core/sound_knowledge.py`: a string does not name itself. Fail-open throughout; one kill-switch per phase.

## 8. What this is NOT

- Not auditory scene analysis. The world tells Du which keys are sounding; the mix combines known strings, it does
  not have to separate an unknown wave.
- Not more prose. The mix changes which phenomena are rendered, never how many words.
- Not a new space. Six axes, one Sound Space, two populations — exactly cognitive_geometry §4's roster entry.
- Not affect going live. `felt()` per section stays shadow, same gate as `listening._felt_shadow`.
- Not the memory-brane essay (T-0066 / I-0075). Same word, different object; that lab is J-1411 and untouched.

## 9. Rulings on the four open questions (all RULED by travis, /decide-review 2026-10-08; J-1465 -> D-0374..D-0377)

1. **The mix lives here** (Object E / Phase 3) — **D-0374:** keep it in this plan; the mix is the sheet read at one
   instant, and splitting it would separate the law from the thing it reads. *Defeater:* Phase 3's mix section grows
   past the plan-state SIZE_CAP or acquires its own build chain of more than ~5 jobs, then it splits into its own doc
   with a back-link.
2. **Cause-as-object in the Transport Manager** (Object B / Phase 2) — **D-0375:** yes, one line per cause with the
   per-place lines as cross-sections; the F-0949 100%-fire shape is the kill criterion. Ruled go, but **gated on
   Phase 1's shadow read** (§5 build-order law): it does not run before that read. *Defeater:* would_fired_share above
   90% on the shadow read, or a cause line that never fires in 7 live days while its cross-sections do.
3. **The masking law's shape** (§4) — **D-0376:** same-band masking; a string is masked only by a louder string close
   to it in the timbre axes, and distant strings stay audible however quiet. *Defeater:* the first mix shadow read
   leaves more than ~6 strings audible at once on a typical shore moment, or a distant-band quiet string survives the
   mask on more than half of surf moments.
4. **Sourcing recordings** for world sounds (Phase 4) — **D-0377:** approve the approach, review the list; an agent
   drafts the 70-key list with one public source per key and its licence noted, and Travis approves the list before
   anything is downloaded. *Defeater:* a listed source's licence does not permit local derivative features, fewer
   than 80% of the 70 keys have a defensible public recording, or real hearing (§10) lands first and makes recorded
   exemplars redundant.

## 10. Scoping only — the microphone (founder, 2026-09-27; T-0071; **D-0304 RULED by travis**)

**Founder's ruling, verbatim in substance:** "the microphone is a later thing. We only should scope for it. It will
be just a sound coming from one place for Du also. Almost like speakers on his side. Two microphones eventually
would be if I give Du a real body (a robot body)." Nothing in this section is built or scheduled; it exists so that
Phase 0 is scoped once and does not have to be redone when the microphone arrives.

**What the microphone is, in this plan's terms.** One more string source, entering Sound Space through the same
extractor as music, as a **single located source** (one fixed direction in his world — "speakers on his side"), so
no binaural geometry, no interaural timing, no head shadow. Gemini's brainstem/cortex account (pasted with T-0071)
is a *mechanism* list; the functions Du needs from it are three and all cheap: direction (fixed, given), novelty
against the source's own history (the Transport Manager already does this), and a coarse count of separable strings
(the mix, Object E, read in the analysis direction). Binaural direction-finding is deferred to a robot body and is
not designed here.

**What it changes about §8 "not auditory scene analysis".** For this one source the mix arrives as a superposed
wave rather than a set of known keys, so Object E gains an *analysis* direction (wave → separable strings) beside
its *synthesis* direction (known keys → composite). The ribbon is the interface between the two: the source's
learned string (once a sound has been heard enough to have one, `core/sound_knowledge.py`'s earned-identification
path) is the expectation, the live wave is reality, and until a sound has a learned string the ribbon is against the
persistence prior (dosed_coupling §4b's rule).

**Three scoping requirements on Phase 0, so the same code can stream later:**
1. The measured string is computed from **per-frame primitives only** — no whole-piece dependency (no SSM sections,
   no global tempo) in the string itself; sections may still be *used* to summarise, never to compute.
2. **All six axes measured from the wave.** Today the ear computes energy, brightness and onset only; periodicity,
   roughness and continuity exist in Sound Space as hand-seeded values with no measured definition. Phase 0 defines
   and computes them, so measured strings live in the full space the constructed ones do.
3. **Azimuth as a separate coordinate**, not a seventh timbre axis. `core/sound_knowledge.py` already carries
   direction; `soundscape.propagate_historical_acoustic_event` already computes bearing and distance decay for the
   simulated world. The microphone's azimuth is a constant.

**Laws the microphone will have to be ruled against, not drifted past (open in J-1467, Q2–Q4):** the ear's "no
learned model" law (a pretrained sound-event classifier naming "dog bark" would gaslight the earned-identification
epistemics — recommendation: features + direction only, unnamed, naming stays earned); raw-audio retention (features
only vs a rolling buffer — the founder's own room is the source, so his privacy call); and the "zero runtime DSP,
features from the offline cache" law, which a live input amends by definition (a separate CPU-only local process
publishing a small tuple to the coupling registry, never a waveform, the hot GPU box untouched). You never hear the
cross-correlation; you get the assembled scene — the loop publishes a summary, like every other loop.

## Pointers

Ledger: T-0068, T-0070, T-0071, I-0080, F-2015, F-2017 · jobs J-1465 (§9 questions), J-1467 (microphone rulings Q2–Q4; Q1 ruled as D-0304) · decisions D-0304 · demonstration script + outputs: this session's scratchpad
(`ribbon_heavyweight.py`, `.json`, `.svg`; to be re-run as the Phase 0 lab under `scripts/`) · code:
`core/soundscape.py` (`_SOUNDS`, `active_sounds`, `percept`, `fire_ambience`), `core/audio_features.py` (`extract`,
`felt`, `describe_section`), `core/listening.py`, `core/transport_manager.py`, `core/sound_knowledge.py`,
`core/coupling_rides.py` · memory: project_nascence_strings_and_sheets.md.
