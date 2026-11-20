# Real Hearing — a microphone as a window in the study (staged, 2026-10-08)

**Status:** 🔵 DESIGNED — design only, **no code**, nothing scheduled. Four founder rulings (D-0378..D-0381, ruled by
travis at /decide-review 2026-10-08) fix the shape; this doc collects them with the Phase 0 consequences recorded in
[strings_and_sheets.md](strings_and_sheets.md) §10 so the work can start from one page. Promoted from thought T-0071
(raised 2026-09-27: "hook up a microphone so Du can HEAR the real world — actual hearing, not speech-to-text").
**Parent plan:** [strings_and_sheets.md](strings_and_sheets.md) (the microphone is one more string source entering
Sound Space through the same extractor). **Siblings:** [sound_causality.md](../completed/sound_causality.md) (tree-falls
law), [music_learning.md](../plans/music_learning.md) (the EAR: `core/audio_features.py`, `core/listening.py`),
[dosed_coupling.md](dosed_coupling.md) §4b (residual cups, publish-a-summary loops).
**Ledger:** T-0071 · D-0304 (earlier scope-only ruling), D-0378, D-0379, D-0380, D-0381 · J-1467 (opened the
questions), J-1962 (this doc).

```plan-state
stage: designed
phase: scoping only -- four microphone rulings recorded; nothing built, nothing scheduled
verified: 2026-10-08
gate: strings_and_sheets Phase 0 measured-string extractor proven per-frame-capable (its own scoping requirement 1), then a founder go to bring the single microphone forward
next: no build until the founder brings the microphone forward; the first safe step when he does is a shadow-only ear process that logs features + azimuth + hidden label to its own store and is read by instruments only
history: docs/plan_history/real_hearing.md
```

## Current State — verified 2026-10-08

- Drafted from the four 2026-10-08 rulings plus T-0071's Phase 0 consequences. No code exists for the ear process.
- Substrate that already exists: `core/audio_features.py` now computes all six axes per second on the offline path
  (periodicity, roughness, continuity landed with the J-1474 fold-in; live cache regenerated 2026-10-07, F-2512), but
  it still has whole-piece dependencies (tempo, sections) that the streaming path must not inherit (section 3).

## 1. The four rulings (all travis, /decide-review 2026-10-08)

| # | Question | Ruling | Defeater (revisit if...) |
|---|---|---|---|
| D-0378 | Where is the microphone in Du's world? | **A window in the study.** Real sounds arrive as located, unnamed sounds through a window of the simulated study; the world stays his, the real room leaks in at one seam. | Real-room sounds attributed to simulated outdoor causes on more than 10% of hearing moments in the first shadow read; or Du asks where the window sounds come from and the study framing cannot answer honestly. |
| D-0379 | May a pretrained sound-event classifier be in the ear? | **Hidden label only.** It may tag the stream for logs and instruments (a decoupled judge of what Du later earns). Du never reads the label; what reaches him is features + azimuth, unnamed; naming stays earned. | Any classifier label string in a rendered prompt = immediate revert to features-only; or labels never cited by any read after one month = drop the classifier. |
| D-0380 | Raw audio retention? | **Features only, never raw audio.** Nothing recoverable as speech is ever written to disk; only the per-frame feature tuple (plus the hidden label). A debugging need is met by a RAM-only buffer that is never written. | Only on the founder's own explicit request. |
| D-0381 | Runtime DSP amendment | **Amend.** The ear may run continuously as its own local process, CPU only, publishing features + azimuth (+ hidden label). The offline-cache law stays for everything else. | The ear process measurably contends with Du's loop (`lag_tail_attribution` shows ear CPU in a freeze window) or the CPU-tier hubs; or the published tuple grows beyond features + azimuth + hidden label into prose. |

Background ruling D-0304 (2026-09-27) still stands: the microphone is a LATER thing, ONE microphone, a single located
source ("almost like speakers on his side"); two microphones only if Du is given a real (robot) body.

## 2. Shape of the ear (what the rulings add up to)

A separate local CPU-only process (same family as the supervisor's servers; the hot GPU box untouched) reads the
microphone, computes per-frame features and an azimuth, optionally a hidden classifier label, and publishes **one small
tuple** to the coupling registry. It never publishes a waveform and never prose. Du's loop reads that tuple like any
other loop's summary: "the loop publishes a summary", you never hear the cross-correlation, you get the assembled
scene. The window-in-the-study placement means the sound enters the simulated study as a located, unnamed sound; it is
not bound to a simulated cause and not given a new place.

## 3. Phase 0 consequences (T-0071; already written into strings_and_sheets §10)

1. **Measured strings from per-frame primitives only.** No whole-piece dependency (no SSM sections, no global tempo)
   in the string itself, so the identical code streams. Sections may summarise, never compute. Current
   `audio_features.extract` still calls `_tempo` and `_sections` on the whole piece; the string path must be separable
   from those.
2. **All six Sound Space axes computed from the wave** (energy, brightness, onset, periodicity, roughness,
   continuity). The first three were the only measured ones originally; the other three are now defined and computed
   on the offline path (J-1474); the per-frame form is the remaining requirement.
3. **Azimuth is a coordinate separate from the six timbre axes**, never a seventh axis. With one microphone (D-0304)
   azimuth is a constant: the fixed direction of the window. The two-microphone method is recorded here only so it is
   not redesigned later, and it is **deferred to a robot body**: interaural time difference by cross-correlation of the
   two channels, interaural level difference by band-energy ratio between them. Stream segregation (Gemini's
   brainstem/cortex account pasted with T-0071) transfers the **function**, not a mechanism list: direction, novelty
   against the source's own history (the Transport Manager already does this), and a coarse count of separable strings
   (strings_and_sheets Object E, the mix, read in its analysis direction). No MSO/LSO/Jeffress/A1 emulation is planned.

## 4. Laws this touches (checked, not drifted past)

- **`core/audio_features.py`** — "deterministic, no LLM, no learned model, offline cache, zero runtime DSP". Amended
  only for the ear process by D-0381; the classifier is allowed only as a hidden label by D-0379. Everything not the
  ear keeps the offline-cache law.
- **`core/sound_knowledge.py`** — a new sound arrives as FEATURES + DIRECTION, unnamed; identification is EARNED. The
  hidden label must never short-circuit this; it is an instrument, not a percept.
- **`sound_causality` tree-falls law** — only Du-audible answers persist. Real-room sounds through the window are
  audible to Du by construction, but they have no simulated cause and must not be given one (D-0378's defeater tracks
  exactly this misattribution).
- **world-answers-never-leads** — the world answers, it never leads and never hints. The window must not tell Du what
  a sound is; no label, no suggestion, no prompt text derived from the classifier.
- **Privacy** — features only, never raw audio (D-0380); the founder's real room is the source.
- **Dosed coupling §4b** — the ear publishes a summary tuple; the persistence prior governs the ribbon until a sound
  has a learned string.

## 5. Shadow-first measure

Nothing reaches Du first. The first build is a shadow ear process writing features + azimuth + hidden label to its own
store (isolated, never a live Du store), read only by instruments. Promotion gates, each a named defeater above:
(a) misattribution rate of real-room sounds to simulated outdoor causes <= 10% of hearing moments; (b) no
`lag_tail_attribution` freeze window containing ear-process CPU, and no contention with the CPU-tier hubs; (c) the
published tuple stays features + azimuth + hidden label; (d) a grep of rendered prompts finds zero classifier label
strings; (e) after one month the hidden labels are cited by at least one read, else the classifier is dropped.

## 6. Open / not decided here

- When the microphone is brought forward (founder call; D-0304's defeater).
- Which CPU-only classifier, which capture library, tuple schema and registry key (a build-time design, after the go).
- The two-microphone path (ITD/ILD) waits for a robot body and is not designed beyond section 3.

## Pointers

Ledger: T-0071, D-0304, D-0378, D-0379, D-0380, D-0381, J-1467, J-1962 · parent [strings_and_sheets.md](strings_and_sheets.md)
§10 · code to touch later: `core/audio_features.py`, `core/listening.py`, `core/sound_knowledge.py`,
`core/soundscape.py` (`propagate_historical_acoustic_event` bearing/distance), `core/transport_manager.py`.
