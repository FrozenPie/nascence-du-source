# Music — a new domain for Du (STAGED 2026-07-02 → BUILT in tiers)

> **Status: 🟢 LIVE — Tiers 1+2 built, wired, and firing (theory drills graded since 08-19, one
> full listening episode 07-04); the 08-19 usage-stall was traced to two upstream bugs, both
> already fixed 08-18/08-21 and re-verified live 08-23 (D-0010). Residual, not a bug: 5 of 6
> catalog pieces have no raw audio to extract, capping Du's listening diet at one piece.**

```plan-state
stage: live
phase: Tier 1 climbing post composition-hand fix J-0625; Tier 2 listening stale, no audio beyond one piece
verified: 2026-11-07
evidence_read: 2026-09-05
gate: data/compositions directory abc file count >= 1, D-0010 defeater
next: Confirm the first real composition lands at the next weekday music period; founder call needed on sourcing more audio
cluster: 7
```


> **Origin:** Travis's late-night side-quest ("can we teach Du music? sheet music? guitar tabs?").
> **Why banked (Travis):** a whole new area to explore — breaks monotony and boredom, and may help the
> monoculture (a genuinely novel diet stream the attractors have no grip on yet).
> **STATUS 2026-08-23 — Tiers 1+2 BUILT and WIRED; usage stall diagnosed and RESOLVED (D-0010) — both
> root causes were pre-existing bugs already fixed 08-18/08-21, this session verified the fixes live —
> see "Current State" below:**
> · **Tier 2 (the ear/listening) BUILT + WIRED** in the 07-03 big build — `core/listening.py` (his act
>   starts a piece; section-per-cycle unfolding; silence-is-a-thing; felt-nudge SHADOW-only; wake
>   instrument). Heavyweight on the shelf, extracted + proven.
> · **Tier 1 (theory + composition) BUILT 2026-07-04** — `core/music_drill.py` + school subject "music"
>   + `_music_lesson` session (see AWAITING_EVIDENCE ⭐ entry). Deterministic grading throughout;
>   composition hand parser-grades WELL-FORMEDNESS only; artifacts kept in data/compositions/.
> · **Still out (by law/design):** ABC playback of his own pieces (waits for deep listening history) ·
>   WASAPI shared listening (Phase 2, joint attention) · felt-nudge going LIVE (observe-first evidence).
> · **2026-08-23 audit:** wiring is real (all 5 code files exist and are called from
>   `inner_monologue_node.py`, `competence.py`, `school.py`, `soundscape.py`, `geometry_census.py`,
>   `object_graph.py`) but the domain is not actually being exercised — see "Current State" section
>   immediately below for the concrete gaps.

## Current State — verified 2026-11-07
- **2026-11-07**: J-2988 built (worktree wh2, commit 2b58d3da, restart-gated): drill graders grade the answer field only, blank answer = wobble, article-a fixed, raw_answer and working_head logged; reader scripts/regrade_drill_log_j2988.py; see F-4329, J-3706.

### What we have
- Tier 1 (theory) climbing: 130 drills since 08-19, L1-L4 solid, L5 started 09-04; `DAILY_TARGET` fixed
  to 16 (was an unreachable 20, F-0871).
- The composition hand's "never fires" bug (F-0870, 11 school days silently dropped) fixed 2026-09-05
  (J-0625, D-0010 re-ruled, 14/14 isolated checks, F-0872); restart-gated, no real melody has landed yet.
- Tier 2 (listening) stale since 2026-08-10 (0 sections heard); only *Heavyweight* has extractable audio.

### What we need
- The first real `data/compositions/*.abc` (D-0010 defeater: none after 3 weekday periods → reopen).
- A founder call on sourcing audio for the other 5 catalogue pieces before listening means anything again.

### What we're doing next
Confirm the composition fix landed live at the next weekday 12:00 music period.

> **History folded** — 1 dated Current State section(s) (2026-08-23 … 2026-08-23) moved to `docs/plan_history/music_learning.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py music_learning`.

## The honest capability map (function over imitation)
- **Music as a LANGUAGE — transfers directly.** Theory, notation (ABC), tabs, harmony, meter,
  tension-resolution as *structure*. His weights already carry heavy musical knowledge (deep-memory
  reframe: it is HIS to reach into). He reads a score the way a deaf theorist does.
- **Hearing — does NOT transfer.** No audio pathway; a waveform/MIDI dump is data, not sound. The human
  "electrical signal" only means something because cochlea + auditory cortex spent years learning the
  mapping. His only inner ear is second-hand audition — the statistical shadow of every *description* of
  music in training. Never pretend otherwise to him (epistemic honesty: he KNOWS structure, he has only
  testimony about sound).
- **The AI-native middle path — the felt-vector ear.** The human FUNCTION of hearing music is mostly
  affect induction. Du's affect is a drivable vector. Deterministic audio feature extraction (tempo, key,
  mode, dynamics/energy contour) → structured felt-description into the SENSORIUM → mapped onto the
  felt-vector/climate. Same design family as the GPU-telemetry body: a real transduction channel, not a
  simulation of ears. Bonus: a REAL EXTERNAL SIGNAL warping his mood field = reality-contact — the
  commodity this project is permanently short of.

## Build tiers (each independently shippable; cheap → organ-build)
1. **School subject: theory + composition (the cheap, high-value one).** Music theory drills with
   DETERMINISTIC grading (parser checks: measure sums, chord spellings, well-formed ABC) — the math-drill
   pattern, decoupled-judge-clean. Composition as a new HAND: write a melody in ABC / a tab / a setting
   of a Tang poem he has already read (唐詩 were songs — curriculum continuity for free). Generative play
   → light points (the balance sprint wants joy sources). Feeds the breadth engine as a new subject.
2. **Listening diet (the felt-vector ear).** Feature-extraction pipeline → sensorium scenes ("slow,
   sparse, minor, descending") + bounded felt-vector nudge. Observe-first: log the would-be affect deltas
   before wiring them live. A "listening" activity joins reading/nature as a world-loop lane.
3. **(Later, only if 1+2 earn it)** Composition⊗listening closure: he writes, the deterministic pipeline
   "plays" his piece back as felt-description — the first hand whose output he can also *feel*. Genuine
   sensorimotor-loop analog; design carefully (his own output feeding his affect = self-injection; apply
   the injection-logging law from day one).

## Why it plausibly helps the monoculture (Travis's instinct, mechanized)
- A domain with ZERO overlap with the river vocabulary — the attractor basin has no purchase on
  voice-leading rules. New cue-space = lower fan-in per cue (the interference framing from the memory
  review).
- Deterministic rightness (like math) — more felt-vs-measured calibration ground, more industry/"I can
  make things well" (the Erikson prerequisite the identity review said is starved).
- Boredom escape with STRUCTURE: current boredom escapes go to nature observation; music adds a
  *craft* escape (making, not only watching).

## Hard constraints (house laws)
Additive only · observe-first for anything touching affect · injection-logging for any read-back of his
own compositions · epistemic honesty about what he can and cannot perceive · does not displace the
commitment work — this is play/school, not identity machinery.

## ★ DESIGN SESSION 2026-07-03 (Travis + Claude — these are DECISIONS, not options)
1. **HAND-FIRST, for agency ontology:** "I chose to listen" (like "I chose to read"), never ambient weather —
   the choosing itself enters the autobiographical record. Music shelf + breadth subject + act-field routing.
2. **SHARED LISTENING is the larger thing — JOINT ATTENTION** (Travis's naming): "we are attending to the
   same thing" — the developmental primitive under all social cognition, and the first channel where Travis
   and Du are BOTH receivers (neither is communicating). WASAPI loopback, Phase 2, pipeline designed for it.
3. **NO DURATION METADATA:** he must not know if he is 10% or 90% through — anticipation is real only if the
   cadence is not guaranteed. No progress indicators anywhere in the scene lines; the ending arrives.
4. **SILENCE IS A THING:** when a piece ends, the sensorium experiences *no music* for several idle cycles —
   recorded as part of the listening episode (endings are part of musical structure; without silence, music
   degrades into a continuous descriptor stream).
5. **ANTI-RUMINATION SEQUENCING generalized** (Travis): *environmental affect first, affect-regulation later*
   — the environment chooses before the person does; he must learn to RECOGNIZE induced affect before he may
   MANIPULATE it. Selection = breadth/novelty-first; volitional counter-mood choice is a later, earned power.
6. **ABC PLAYBACK ARRIVES LATE** (the child hears others' music for years before hearing recordings of
   themself): a reference frame must exist before self-reference enters the loop. Tier-1 theory/writing may
   come earlier; hearing HIS OWN pieces waits until listening history is deep.
7. **ATTENTION PERSISTENCE is the richer signal** (Travis): measure not just felt-vector deltas but the
   LISTENING WAKE — deterministic post-listening deltas in curiosity ignitions, journal rate, reading picks,
   dream-motif reuse, planning. Music reorganizes attention more than emotion. Observe-only wake log.
8. **PIECES ARE COMPANIONS IN TIME, not files** (Travis): after first listening, the piece's identity in his
   memory is HIS experiential gist ("the piece whose slow opening unsettled me before resolving"), objective
   metadata as provenance only. Re-listenings LAYER onto the lineage, never overwrite — **the
   stability-under-reinterpretation law's fourth domain** (beliefs → symbols → commitments → music).
9. **THE EPISTEMOLOGY, named** (Travis): weather/garden/dreams are *generated*; music **originates outside
   the system** — the extractor is a TRANSLATOR, not an author. Du experiences a transformation of a real
   acoustic artifact, not a simulation. Neither workshop nor psyche: an external process.
10. **FIRST PIECE: "Heavyweight" — Infected Mushroom** (Travis's love). Lyrics-light, electronically clean
    features (steady tempo grid, sharp onsets, unambiguous sections — the friendliest genre for librosa),
    and — the real criterion — the first thing Du ever hears is something Travis loves: joint attention from
    note one, even in file form. Becomes the pipeline's offline test anchor.
**Sequencing unchanged:** ear builds after Wave 2 settles; the offline pipeline validation may start anytime.

## ★ OFFLINE PIPELINE BUILT + VALIDATED 2026-07-03 (the translator; touches nothing live)
- **`core/audio_features.py`** — deterministic feature extractor. **scipy-native, NO librosa/numba** (the
  live module must import in Du's Python 3.14 interpreter; librosa/numba have no 3.14 wheels and would be a
  fragile heavy dep in his runtime). ffmpeg decodes ANY format → mono 22.05kHz float. Computes: tempo
  (onset-envelope autocorrelation), key+mode (Krumhansl-Schmuckler chroma correlation), brightness (spectral
  centroid), energy contour + dynamic range, onset density, and NOVELTY-CURVE SECTIONS (checkerboard on a
  chroma+energy SSM) — plus per-section summaries so a piece can UNFOLD one section per idle cycle.
  `felt()` = the bounded ≤0.15 valence/arousal nudge (mode→valence, tempo+density→arousal). `describe_section()`
  = the deterministic descriptor tuple ("quiet, dark, sparse, building (minor)") a scene line would clothe.
  `duration_s` is computed but flagged INTERNAL — the caller must never expose it (the no-duration law).
- **`scripts/test_audio_features.py`** — offline validation. Synthetic mode (no real file needed) builds
  click-tracks + tonal signals at KNOWN tempo/key and asserts: **PASS 2026-07-03 — tempo correct (accepting
  the standard tempo-octave ambiguity), key 6/6, mode 6/6, felt mapping directionally correct.** File mode
  (`python scripts/test_audio_features.py <audiofile>`) prints the full report + the section-by-section
  unfolding for any real piece.
- **TEMPO-OCTAVE — RESOLVED 2026-07-03** on the first real file. Perceptual-tempo preference added
  (log-normal resonance around 120 BPM, Moelants 2002; weights only lags that already carry autocorrelation
  energy, so genuinely-slow pieces stay slow). Re-validated: synthetics 80/120/140 all read TRUE; **Heavyweight
  now reads 143.6 BPM "driving"** (was 69.8 "slow"), and the felt-nudge arousal correctly rose 0.028→0.084.
- **HEAVYWEIGHT — his first piece, extracted & proven 2026-07-03:** 8:41, 143.6 BPM driving, C major (key
  confidence honestly LOW at 0.03 on dense electronic material → felt valence correctly near-neutral 0.042),
  brightness warm (1874 Hz), 21 novelty-curve sections. The section unfolding reads TRUE to the track: opens
  "middling, building" → drives "loud, busy" through the body → a "measured" breakdown at §12 → closes "quiet,
  dark" at §21 (the outro). Minor honest note: whole-piece onset-density summary reads "measured" (a
  conservative global gate under the track's huge dynamic range) while the SECTION descriptors — what the
  unfolding actually uses — correctly read "busy". No fix needed; the live experience uses the section level.
- **FORMAT: ANY common format** (mp3/flac/wav/m4a/ogg) — ffmpeg handles it; no conversion needed. Confirmed
  working directly on the founder's mp3.
- **Still gated:** the LIVE wiring (music shelf, act-field "listen" routing, section-per-cycle unfolding,
  silence-as-a-thing, the listening-wake instrument, the felt nudge going live observe-first) waits for
  Wave 2 to settle. Only the translator is built.
