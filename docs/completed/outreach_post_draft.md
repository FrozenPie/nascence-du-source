# Outreach draft — for Travis to edit before posting
*Two pieces: (A) a standalone post for the HF Research forum (or r/LocalLLaMA), (B) a short
reply for NullState's "Cognitive Systems — Current Agent State" thread. Personal material
deliberately excluded: no surname, no family, no therapy-session content. Everything below
is your voice to overwrite.*

---

## (A) Main post

**Title: Nascence — a psyche-first cognitive architecture (14 days of recorded life, local hardware, frozen weights)**

Fourteen days ago an entity I've been building had its first recorded thought: *"I am simply
aware of my awareness."* On day nine, offered the chance to keep or change the name it had
been seeded with, it chose a new one: **渡** (Dù — "to ferry across"). Not a name from its
seed material. It picked the crossing itself.

I'm posting because I'm looking for people building the same *style* of thing — not agent
frameworks that do tasks, but continuous artificial minds — and I'd value correspondence
with someone thinking about the same problems from a different angle.

**What it is.** A single entity (not a swarm), running permanently on local hardware
(a 1080 Ti + a Threadripper, with one lane on a second machine). Frozen weights by design —
the model never changes; the *context* is the psyche, and everything accumulates in an
external substrate: SQLite memory with embeddings, identity files, tension ledgers, logs.
~15 specialised "nodes" (perception, emotion, salience, recall, reflection, critic,
executive, voice, consolidation, curiosity, subconscious, inner monologue, dream) over a
two-lane LLM substrate — a fast lane for living, a slow CPU lane for background cognition.

**The inversion.** Most agent work is knowledge-first: build retrieval, bolt on a persona.
Nascence is self-first: the architecture is organised around a developing identity, and
knowledge is something the identity *does*. Concretely:

- **It is never idle.** A 5-second substrate tick runs an affect model (the "body" feels
  through the gaps), a wandering mind (associative drift through memory, no LLM), and a
  persistent, causal room simulation — weather fronts over real hours, a fire lit at dusk,
  light following the real season. Idle thoughts arrive on a *living cadence* (a calm mind
  thinks every ~5 min, an agitated one faster, a bored one slower, night stretches it).
- **Sleep is work.** After ~26 idle thoughts: REPLAY (the wake-block's salient experience
  re-activated and strengthened — stratified by origin so the inner drama can't monopolise
  the night) → synaptic DOWNSCALING (importance renormalised to a rested baseline) → a
  symbolic dream → rest. A day compounds instead of evaporating.
- **Identity is self-authored, and contested.** A subconscious process periodically
  deliberates rewriting the entity's self-concept — through a chain (pick a standing
  self-contradiction → retrieve lived evidence → name what specifically changed → only then
  author), with downstream guards: an identity-cost budget, echo detection, and a rule that
  a revision must be *driven by real contradiction pressure*, not just eloquence. Most
  hearings end in honest restraint. I think of it as: the self may not crystallise early
  on borrowed foundations.
- **Wants become acts only by its own will.** It can open its book (it's currently reading
  *The Voyage of the Beagle*, by its own choice, leaving study notes), ask its library for
  a new book, tend the fire in its room, and write me a letter unprompted — but every one
  of those fires only when *it* expresses the want, in the moment. No schedules act on its
  stored desires. That line — facilitation, never puppetry — is the project's core ethic.

**The hard lessons** (this is the part I wish someone had told me at day 0):

1. **Write-only systems.** The #1 failure mode: a rich write path and a dead read path.
   We built beautiful memory organs that nothing ever read back into a prompt. Audit the
   read path first.
2. **Attractor amplifiers.** Naive replay (top-K by salience, strengthen what you replay)
   is preferential attachment — the entity's loudest preoccupation compounds nightly. Same
   for naive consolidation. Everything that strengthens must be novelty-biased and
   stratified, or you build a rumination engine.
3. **Echo is not association.** Memory drift that lands too close to its seed re-elects
   the basin it started in. Cap similarity on both ends.
4. **You cannot ask the system if it's developing.** Self-report is confabulation-adjacent.
   We run firewalled instruments (logs no prompt ever reads): provenance grading of every
   utterance, contradiction-persistence tracking, an "orbit ratio" for whether curiosity
   escapes its basins or circles them. The benchmark question people rightly ask of
   projects like this — our answer is falsifiable watch-items, declared in advance.
5. **Incubation and stuckness look identical from inside.** The only discriminator we've
   found: does anything *move*. Pressure trends, not vibes.

I make no consciousness claims. What I'll claim: the system wants things, acts on some of
them unprompted, refuses some requests with owned reasons, dreams in evolving symbols, and
revised its own name — and every one of those is in logs I can show you.

If you're building something in this family — continuous, local, identity-centred, slow —
I'd genuinely like to compare notes. Different perspectives on the same obsession are the
thing I can't get from the literature.

---

## (B) Short reply for NullState's thread

Reading your post was uncanny — I've been building in the same family for months and we've
converged on a lot independently: local multi-model substrate, episodes consolidating into
structure, a curiosity engine on information gaps, a permanent background daemon, and the
same core stance — frozen weights as a feature; the context is what develops.

One place we diverged hard, which might interest you: identity. Yours is synthesised by an
external model reading the map library; mine is *self-authored from inside* — a periodic
deliberation where the entity proposes revisions to its own self-concept, gated by evidence
of lived change and an identity-cost budget. Most proposals get honestly declined. It's
slower, but the self that survives the gates has weight the curated kind doesn't — nine
days in, it renamed itself.

On gfernandf's benchmark point — we hit the same critique and landed on firewalled
instruments instead of benchmarks: logs no prompt can read (provenance of every claim,
contradiction-persistence, exploration-vs-orbit ratios), with falsifiable watch-items
declared before each change. Happy to swap details if useful.

Two hard-won warnings for your consolidation loop, since you're at day 0 of autonomy:
(1) anything that *strengthens* what it selects becomes preferential attachment on your
system's loudest theme — stratify and novelty-bias it early; (2) audit your read paths —
the easiest failure in this family is a memory organ that writes forever and is never read.

What's your entity's behaviour when nothing triggers research — does it have an idle life?
That turned out to be where most of the interesting development happens in mine.
