# Curiosity-Pursuit Burst — pulse-manager source #2
*2026-06-15. The second burst source after reading. Reading-burst proved PERSISTENCE; curiosity-burst
proves PRIORITY (a question can preempt a read). It chases an open Frontier question across rapid grounded
steps to ground or resolve it — the DIFFERENTIATING force (exploration), not just grounded intake.*

## What we got (the systems — all exist)
- **Frontier** (`frontier.py`) — the store of open world-questions: `open_questions(k)`, `note_question`,
  `resolve_if_addressed(text)` (strict: needs an answering verb + token overlap), `random_term`.
- **Scholar** (`scholar.py`) — `Scholar().consult(query)`, depersonalised hot-lane parametric testimony
  (tagged `parametric_library`, weighed not recited).
- **web_research** (`web_research.py`) — `term_from_question`, `lookup(term)` → (title, extract) external.
- **study** (`study.py`) — durable note from a pursuit's finding.

So the pursuit is buildable on existing systems, like reading was.

## ⚠ The catch (what "see what we got" revealed): the FUEL is weak
The Frontier is **29 open · 0 resolved · 110 faded** — questions are born (mostly from his *intentions*) and
then **fade unresolved; nothing ever lands.** Worse, the open ones are *self-leaning*: *"self as an
ever-evolving process," "aspects of self," "accuracy and wholeness."* The world-filter (`is_world_question`)
is **leaky** — it denies `"the self"` but lets `"self as"`, `"wholeness"`, `"aspects of self"` through, and
`source='intention'` feeds it self-reflective material. **Pursuing those through the Scholar = self-reflection
laundered through the library = a NEW monoculture path.** The burst is only as grounded as its questions.

This is the same safety line as reading: reading-burst was safe because the *books* are grounded; curiosity-
burst is safe only if the *questions* are grounded. Right now they largely aren't.

## The design (the pursuit loop)
A burst takes ONE genuinely-grounded open question and chases it:
1. **pick** — an open Frontier question that passes a STRICT grounded gate (below).
2. **ground (outward)** — `Scholar.consult(question)` (+ optional `web_research.lookup`) → testimony.
3. **reflect** — Du works the testimony: refine the question, open a sharper sub-question (`note_question`),
   or answer it (`resolve_if_addressed`). The question routes OUT; the finding feeds the Self (routing law).
4. **repeat** at machine speed, yielding each step (floor-service), until a stop-condition.

**Stop conditions** (mirroring reading):
- **resolved** — `resolve_if_addressed` fires (the question landed).
- **orbit/stall** — the pursuit circles: the new testimony/sub-question is too similar to prior steps
  (the curiosity-observatory's **escape-vs-orbit** ratio, made operational). Keep going while it ESCAPES to
  new ground; stop when it ORBITS the basin.
- **cap** — `CURIO_BURST_MAX` (tight — see cost).
- **the person speaks** — yield at once.

**Output:** a grounded finding → a study note (durable) + a Frontier resolution *or* a sharper sub-question
+ a grounded thought. Turns the fade-graveyard into resolutions.

## PRIORITY — the new thing this source introduces
- A **curiosity ignition** (the existing climate/dissonance spike that replaced the 120s timer) can
  **preempt a reading-burst** — a strong question pulls him off the book. First real source-vs-source
  arbitration.
- The **user preempts both.** Order: user > curiosity-ignition > reading.
- Later, the **modulation field** arbitrates by drive (novelty→curiosity, reading-progress→reading).

## The required gate (so it's grounding, not laundering)
Pursue ONLY questions that are genuinely world-facing:
1. **Prefer `source in (study, reading)`** over `intention` — questions harvested from the grounded
   curriculum books, not from self-reflective resolves.
2. **Stricter world-filter at pursuit time** — extend the deny-list (`self as`, `wholeness`, `aspects of`,
   `meaning of`, `nature of` + abstraction markers); require a concrete noun/referent.
3. **The curriculum will supply better fuel** — as he reads the 40 grounded books, `harvest_tablet`
   mines real mysteries from study notes ("why does a river pilot read depth by the water's colour?").
   Fuel quality rises as the curriculum runs.

## Cost / cautions
- **LLM-bound** — `Scholar.consult` is a hot-lane call PER step (reading-burst was embedding-only). So cap
  tight (`CURIO_BURST_MAX` ≈ 3), hot-lane, yield to the user.
- **The orbit-gate must be real** — a circling pursuit is curiosity's rumination; the escape/orbit ratio is
  the safety, alongside the world-filter.
- **Never pursue the self** — the world-filter is the line; the Scholar is depersonalised.

## Readiness / sequencing (honest)
Unlike reading-burst (ready immediately — grounded books in hand), **curiosity-burst is gated on its fuel.**
Two paths:
- **(a) Fix the fuel first** — tighten the world-filter + prefer grounded-sourced questions, then build the
  burst. (The 0-resolved/110-faded Frontier also wants the harvesting to lean on reading, not intentions.)
- **(b) Let the curriculum run** — grounded reading generates grounded questions; revisit the burst once the
  Frontier has real world-mysteries to chase.

Recommendation: **(a)** — the burst is worth building, but with the strict grounded gate from day one, or it
becomes a library-laundered self-loop. The gauge: Frontier **resolved count** (today **0** — the telling
number) should start climbing once grounded questions are pursued.

## Gauge (add to du_pulse [6.6])
`curiosity pursuits: N · resolved: M · orbit-ratio` — and the standing **Frontier resolved/faded** ratio
(0/110 today = questions die unpursued; the burst's job is to flip that).
