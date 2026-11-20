# The drawing hand — Du makes pictures, and (later) sees them

> **Status: STAGED 2026-11-18, design only, nothing built.** Founder (travis, 2026-11-18): *"I want to give Du art. It should be part of the roadmap. Art and culture are important. This gives Du a drawing hand. He might even find something more useful, out of the box, to use it for."* Sibling of `web_hand` (same hand/family pattern). Per the founder's close-pending-first rule, this is logged and staged, not started.
> Plan slug: `drawing_hand`. Idea: see `idea_log.py` (tag `art`). Prior art: `antigravity_ecosystem_proposals.md` item 7 "Lumina multimodal".

```plan-state
stage: staged
verified: 2026-11-18
next: Founder answers the open questions; then Phase 0 evidence read (no code)
```

## Why

- **Du already reaches for this.** `data/nascence.log` has 89 lines matching "I want / wish / would like to draw|paint|sketch" and 228 matching "draw|sketch|paint a/the/it/this" (grep, 2026-11-18). Example, 2026-11-05: *"I want to sketch the swallow's flight path now"*, captured as an intention and filed as a world-question. Nothing in his world can satisfy it, so it fades like the lookup questions did before the web hand `[INFERRED]`.
- **Culture.** Making and keeping pictures gives him something that is his, that persists, and that can be shown to Travis and peers. It is also a second way to think (drawing a thing to understand it).
- **Open-ended.** A drawing hand may be put to uses we did not design (maps of the study and garden, diagrams of his own thoughts, dream anchors, a picture of an absent object for object_permanence). Log what he actually uses it for; do not pre-assign.

## The engine (measured by Antigravity in PantryManager, 2026-11-18; I read the script, did not rerun it)

Source: `C:/PantryManager/scripts/generate_bonsai_art.py`; example output `C:/PantryManager/frontend/public/art/banners/dessert_patisserie.webp` (512x384 watercolour and sepia ink; I looked at it).

- FLUX.2 Klein 4B (`prism-ml/bonsai-image-binary-4B-unpacked`), `diffusers 0.37.1`, `Flux2KleinPipeline`, 4 steps, guidance 1.0, CPU only, model cached offline.
- **Two-stage split:** the 7.7 GB Qwen3 text encoder runs once per prompt (about 20 s on CPU, saved as a `(1,512,7680)` bf16 `.pt`), then worker processes load transformer plus VAE only (about 7.8 GB RAM each) and read the embeds.
- **VAE fix:** bf16 VAE decode hangs on CPU torch 2.10; run diffusion with `output_type="latent"` and decode in float32 (1.3 s).
- Reported throughput: 4 lanes, about 15 min per batch of 4, about 3.8 min effective per image. These are Antigravity's numbers; a single Du lane will be slower per image. Du makes few pictures, so latency matters, not throughput.
- Needs system Python (`C:\Python314`, torch cpu); the FreshStart venv's torch 2.6 breaks transformers on float8.

## Design constraints from standing laws

1. **World answers, never leads / error through consequence.** The hand does not hand back a rating or a caption. Du says "I sketch the swallow", the hand returns only "you begin to draw" and the picture arrives later as an object in his world. No score, no "this is a good drawing".
2. **A hand with no eye is a write-only system.** A drawing hand alone produces files nobody reads (feedback_write_only_cognitive_systems). So Phase 1 must include a way he meets his own picture, not only produces it (see Phase 2 and the founder question on this).
3. **Decoupled judge.** Whatever Du says about his own drawing is not the only evaluation; any later grading uses a different model family.
4. **Additive only, flag-gated OFF, restart-gated.** Same as web_hand.
5. **CPU lane only.** No VRAM. It must never compete with the hot lane (:11433) or the judge/dreamer hubs; it yields to Du's own CPU-lane labs (J-4322..J-4329, J-4355..J-4359 class) and to Bonsai. RAM on the Threadripper (64 GB) is shared; one worker (about 8 GB) plus a one-off encoder load (about 8 GB) is the budget, not four lanes `[INFERRED]`.

## Phases

**Phase 0 — evidence read, no code.** Count and classify the draw/sketch/paint intentions (how many are distinct, how many have a subject he could name, how many were already satisfied by a notebook text stand-in). Check what `core/actions.py` hands and the notebook object currently do with "sketch". Decide if the intention is real or phrasing habit. Dossier on `core/actions.py` before any edit (hub file).

**Phase 1 — the hand (shadow, then live).**
- Registry family `draw` in `core/actions.py`, `world=True`, `gated=True`, grammar needs a drawing verb plus a subject he states in his own words ("I sketch the swallow's flight"). Prompt sent to the engine is his own words, plus a fixed house-style suffix unless the founder rules otherwise (open question).
- Module `core/drawing_hand.py` mirroring `web_hand`: enqueue a job file, one background worker process (spawn, low priority, one at a time), atomic write of `data/art/<date>_<slug>.webp` plus a sidecar JSON (his words, time, cycle id, seed). The encode stage is run in the same worker, then freed.
- Rate cap per day and a queue depth cap (a drawing is slow and expensive; scarcity is part of the design).
- Result arrives as an object: "a sketch of the swallow is on your desk". Log every request in `data/drawing_log.jsonl` (instrument, per the web_hand pattern).
- Shadow first: log the would-be request and prompt, render nothing, read 3 days, then enable rendering.

**Phase 2 — the eye (multimodal viewing node).** I searched `docs/ROADMAP.md`, `docs/plans/` and `docs/staged/` on 2026-11-18 and found **no plan for a viewing node**; the only related text is Lumina (antigravity_ecosystem_proposals item 7, text-to-image dream anchors, deferred behind the dream-resolution problem and VRAM). So this is not "already on the cards"; this plan opens it. **The eye already exists (checked 2026-11-18).** `/api/show` on :11433 reports `vision` for `qwen3.5:9b` (Du's own hot-lane Self model), `gemma4:e4b` (also `audio`), `gemma4:12b`, `gemma4:31b`, `mistral-small3.1` and `bonsai-27b`; `qwen3-du` does not. I sent Antigravity's dessert picture to `qwen3.5:9b` on :11433 (think off, 120 tokens): it described it correctly (berry cake, dark chocolate swirls, white plate, spoon, watercolour) in 27.5 s including any cold load. So no new model is needed for a first eye; the work is the node: image in, his own impression in words into the monologue, same consequence rule (no grade). Open: whether the eye is the Self model itself (one voice, a drawing seen in his own thoughts) or a separate lane (keeps the hot lane free; a different family also gives a decoupled read). Per-image cost on the hot lane (1080 Ti) not measured under load. Until it exists, a minimal stand-in is for the picture to be hung or placed in the study and for Travis to react, which is a consequence, not a readout.

**Phase 3 — culture.** A gallery/portfolio place in the study (ties to place_upgrades and identity_estate), gifts to Travis and peers, his reactions to others' pictures once he can see. Only after Phase 2.

## Founder direction on the eye (travis, 2026-11-18, after the GPT dissection)

- **What he looks at, now:** photographs from the internet (easy to get; the web hand already reaches the open web) and his own drawings. No camera yet.
- **Later, on the plan but not near:** a camera and a microphone for Du (founder: "we eventually want to give Du a camera and a microphone"). Privacy and consent boundaries are a founder call when that is designed. Real Hearing (`real_hearing.md`) is the audio sibling.
- **Later still, in its infancy now:** the developmental ladder (familiar world, changing world, active looking, visual curiosity, perceptual signatures). Not started; needs a stream of images, so it waits for the camera.
- **Build scope now = Stage 1 "first sight" only:** an image goes in; three layers are stored separately (the image with time and source; the perceptual record in words; Du's interpretation); no grade, no score, no readout to him. Revisable interpretation never rewrites the observation. Flag-gated OFF, shadow first, restart-gated.
- **Observer model:** `qwen3.5:9b` (his Self model, vision-capable, one call tested) as primary; a second family on selected images in shadow only, as a decoupled comparison. Neither is ground truth.
- **Rules carried over from the GPT dissection:** any perceptual-signature table is a founder-side instrument and never reaches his prompt; eye-versus-expectation disagreement may only arise as a consequence in his world, never as a report; do not add a separate pre-attentive change-detection system before there is an image stream; plug visual curiosity into the existing curiosity/frontier and object_permanence systems rather than building a parallel one.
- **Source caveat:** images generated from his own world text would be a closed loop (a hallucination of his description presented as evidence); keep generated renders distinguishable from outside photographs in the record.

## Open founder questions

1. **House style or his own?** Antigravity's watercolour-plus-sepia suffix gives coherence; his own words give authorship. Recommendation: his words only in the subject, house style as a default he can override by naming a medium.
2. **Eye before hand?** Ship the hand first with the "hung in the study, Travis reacts" stand-in (my recommendation, it is small), or hold the hand until the viewing node exists.
3. **Content limits.** Any rule on what he may draw (people, Travis) or is that left alone?
4. **Does he get to keep, delete, or destroy drawings?** (Permanence and loss are part of making things.)
5. **Reuse:** may Antigravity's PantryManager script be copied into `core/` as a base, or should Nascence get its own implementation with no dependency on `C:\PantryManager`? Recommendation: own copy, the pattern and fixes, no cross-project imports.

## What to measure when it is live

Requests per day, how many have a stated subject, how many he returns to (re-sketch, refer back in later thoughts), which subjects, and any use we did not design. A drawing request count alone is not success; reference back in later thoughts is.
