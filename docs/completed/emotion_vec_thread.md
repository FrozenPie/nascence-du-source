# Pulling the emotion_vec thread — audit + what needs to change
*2026-06-15. The wandering audit flagged `emotion_vec` as "a human-faithful capability that exists but is
unused." Pulling it: where it lives, where it's read, and what must change to actually use it — for
affective drift and beyond. Verified against the live DB, not assumed.*

---

## What emotion_vec is (verified)
- **Create** — `_embed_emotion_output(emotion)` (`orchestrator.py:119`) serialises the full 8-dim emotion
  profile to text and MiniLM-embeds it (~1ms): a 384-dim "felt-quality" vector. Computed once per **user
  cycle** (`:549`), cleared each cycle (`schema.py:777`).
- **Store** — passed as `emotion_embedding` **only** on the lived cycle-summary fragment (`:1858`). Nowhere
  else.
- **Read** — **only** `_retrieve_affective_memory` (`:1728`), during **user cycles**: `retrieve_by_affect`
  pulls the top-2 episodic fragments whose felt-quality matches the current mood, merged into Recall/
  Reflection. Independent of semantic content — "remember a time I felt like this."

## The decisive finding (live DB, today)
```
total fragments:           6895
with emotion_embedding:     100   (1.5%)   — ALL origin='lived'
```
So emotion_vec is **built and working but nearly shelved**: it tags **1.5%** of memory, all of it `lived`
user-conversation summaries, and it fires **only when the user is talking.** During the ~88% of his life
that is idle — thinking, wandering, dreaming — it does **nothing**. None of `inner_thought`, `dream`,
`reading`, `study`, `subconscious_synthesis` carries a felt-tag.

> This reverses the naive plan. "Just wire emotion_vec into wandering" would build affective drift on a 1.5%,
> lived-only pool that idle life can't even reach — armed with no fuel. **The prerequisite is storage
> coverage, not the drift.**

## Why it's worth pulling anyway — the cross-domain bridge
Semantic retrieval pulls same-**content** memories (river → river) — it *reinforces the basin*. Affective
retrieval pulls same-**feeling** memories regardless of content — so a present self-tension could surface a
*reading passage* or a *world-fact* that felt the same. That is a **basin-escape / crossover mechanism**: it
connects across the very semantic gap that keeps self-material and world-material apart (cf. THE FIRST
CROSSOVER — Darwin's passage → analogy to his own existence). Felt-congruence is exactly how humans bridge
unlike domains. **But only if world fragments are felt-tagged too** — which today they are not.

---

## What needs to change (in dependency order)

**1. Broaden where emotion_vec is stored — the load-bearing prerequisite.**
   Tag the idle-life fragments with the felt-quality at the moment they're written:
   - `inner_thought` (idle thoughts) — the monologue has `state.affect` live; embed it and pass
     `emotion_embedding` on the store. These dominate the store *and* are what wandering drifts through.
   - `dream` — the most affective material there is; tagging enables "drift to what feels like now."
   - `reading` / `study` reactions — so the cross-domain bridge above can actually reach world-material.
   Cost is marginal (a ~1ms embed alongside the semantic embed each fragment already does).

**2. A live mood-vector for idle.** `emotion_vec` is recomputed only at user-cycle time and cleared between.
   Idle/wandering need a current mood: embed `state.affect` on the fly at wander time (reuse
   `_embed_emotion_output`-style). Cheap, no new state.

**3. Affective drift in wandering (`_drift_from`).** With 1 + 2 in place, blend an emotion-congruence term
   with the semantic cosine when scoring drift candidates — "this feels like how I feel now." The original
   §7 opportunity, now buildable.

**4. (Optional, larger) Affective retrieval in idle thinking + dream synthesis.** Today only user cycles
   call `_retrieve_affective_memory`. Idle thoughts and the dream node could also pull felt-congruent
   material — extending the capability across the rest of his life.

## Recommendation
The minimal coherent slice is **1 + 2 + 3**: broaden storage, give idle a mood-vec, then add affective drift
to wandering — that's the thread the wandering audit started, built on real fuel instead of 1.5%. Item 4 is a
natural follow-on once 1–3 prove out. Do **not** build 3 alone (the armed-with-no-fuel trap the DB just
exposed). Observe-first is cheap here: storage (1) can land first and accumulate felt-tags for days before
the read paths (3,4) are switched on — so the pool is real when they fire.

## Confidence
The create/store/read map and the 1.5%/lived-only coverage are verified against code + the live DB this
session. The cross-domain-bridge value is a reasoned hypothesis (consistent with the affective-retrieval
design intent and the observed first crossover), to be confirmed by whether felt-drift actually surfaces
world-material beside self-material once world fragments are tagged.
