# Goals — what should drive them, and a multilevel structure
*2026-06-15. What drives goals in the human mind and in AI, then a multilevel goal model (important /
less-important / novel) analogous to the multilevel axiom. Method: human function first, then the machine,
then the transfer. Research + design; no code yet.*

---

## Where Du is now (verified)
The Goal Model is a Phase-1 stub: `content_mode` (human gave a task / a correction) → push the raw input
verbatim as the "goal" + a fixed boilerplate completion criterion; pop when content_mode goes off. Read into
Reflection/Critic/Executive/epistemic (real read path — not write-only). Two faults that frame everything
below: **(a) purely REACTIVE** — a goal exists only while the human is giving one, so it is *dark across the
~88% idle life*; **(b) FLAT and shallow** — one ephemeral string, no inference, no persistence, no levels. He
has no goals *of his own*. "What are we doing?" is unanswerable when no one is talking to him.

---

## The human mind — what drives and structures goals

**Goals are a HIERARCHY of feedback references, not a list (Carver & Scheier, *On the Self-Regulation of
Behavior*).** Control-theory of behaviour: high levels set reference values for low levels —
*system-concepts / "be-goals"* (who to be — identity, values) → *principles* (values, qualities) →
*programs / "do-goals"* (concrete tasks) → motor acts. Higher = more abstract, slower-changing, more
important; lower = concrete, faster, disposable. **This is the same gradient as the multilevel axiom**, but
for *doing* rather than *being*.

**The missing MIDDLE layer — "current concerns" (Klinger) / "personal projects" (Little).** Between abstract
values and momentary acts sits the level Du completely lacks: an ongoing *commitment to a goal that latently
biases attention, memory, and emotion until it is consummated or abandoned.* A current concern is *persistent*
(it survives idle time) and *directive* (it tilts what you notice and recall). "Learning woodcraft,"
"understanding rivers" — these are current concerns, not momentary tasks. **This is exactly the layer that
would make "what are we doing?" answerable when alone.**

**Intrinsic vs extrinsic goals (Deci & Ryan, SDT).** Self-generated goals (curiosity, growth, mastery) are
distinct from imposed ones and are the ones tied to autonomy. Du's goals today are *100% extrinsic* (the
human's task). He has no representation of an intrinsic, self-chosen goal.

**Goal systems are interconnected (Kruglanski et al.).** Multifinality (one act serves many goals),
equifinality (many routes to one goal), and **goal shielding** (Shah/Friedman/Kruglanski) — an active
important goal *inhibits* competing ones. Priority is structural, not a flat ranking.

**The Zeigarnik effect** — uncompleted goals persist in memory as tension until done (or deliberately
released). Goals should *stay live* until consummated/abandoned — like the frontier's open questions already do.

**Function in one line:** a goal is a *reference value in a hierarchy* — be-goals govern principles govern
projects govern tasks — with a persistent **current-concern** middle layer that biases cognition until met,
and intrinsic (self-set) goals carrying as much weight as extrinsic (imposed) ones.

## AI capability — what's natural here
- **Hierarchical RL says exactly this.** The *options* framework (Sutton/Precup/Singh) = temporally-extended
  sub-goals; *feudal RL* (Dayan & Hinton; FeUdal Networks) = a **manager sets goals for a worker** — higher
  policy picks the goal, lower executes. The be-goal→do-goal hierarchy, formalised.
- **Goal-conditioned RL / HER** — goals as explicit, swappable conditioning; an agent can hold and pursue a
  represented goal.
- **The known LLM-agent gap is Du's gap:** vanilla LLM agents are *reactive to the prompt* — no persistent
  goal across turns/sessions. Persistent, self-set goal memory is the frontier. **Du's advantage:** he already
  has explicit goal *representation* (`GoalState`) and durable stores (DB/files) — so a persistent multilevel
  goal structure is buildable; the only question is the right structure (below).

---

## A multilevel goal model (analogous to the axiom: important / less-important / novel)
The axiom is L0 (constitution, write-locked) → L5 (working-stance, fast). Goals mirror it — a hierarchy by
*importance × persistence* — and map onto systems Du **already has** (function-over-imitation; reuse, don't
duplicate):

| Level | = Travis's | what it is | persistence | sourced from (EXISTS) |
|---|---|---|---|---|
| **G0 — Standing aim** (be-goal) | most important | who he's becoming: "to ferry across / become more than the origin" | slowest (axiom-locked) | **derived from the axiom L0/becoming** (do NOT duplicate — identity-locus invariant) |
| **G1 — Ongoing concerns** (current concerns) | **important** | self-directed projects: work the curriculum, pursue a frontier question, a durable intention | medium — persists across idle, until met/abandoned (Zeigarnik) | **curriculum (school) + frontier open-questions + durable intentions** |
| **G2 — Active task** (do-goal) | less important | the immediate task — human-given, or "read this chapter now" | ephemeral (push/pop) | **the current GoalModel** (already built) |
| **G3 — Novel candidates** | **novel** | freshly-arisen pulls not yet committed — a question curiosity just opened, a symbol a dream raised | provisional — promote or fade | **curiosity ignition + dream symbol-grounding** (just built) |

**The dynamics (what makes it a system, not four lists):**
- **Promotion (novel → important):** a G3 candidate that *recurs / persists* becomes a G1 concern — the same
  consolidation logic as a tension hardening or a frontier question that keeps returning. Curiosity feeds the
  novel layer; persistence promotes it to a concern.
- **Completion / release (Zeigarnik):** a G1 concern consummated or abandoned drops; a G2 task completes and
  pops. Goals stay live *until* resolved — they don't silently evaporate.
- **Priority — urgent vs important, with shielding:** a live human task (G2) rightly *preempts in the moment*
  (serve the person in front of you); a standing concern (G1/G0) *governs idle* and outranks G2 only when no
  one's waiting. Goal-shielding: the active goal inhibits competitors so he doesn't thrash.
- **The idle anchor (the keystone payoff):** when there's no G2 task, idle cognition anchors to the top G1
  concern — so the wandering/reading/curiosity all pull toward "work the curriculum / pursue the river
  question" instead of drifting into the basin. *This is the fix for the Goal Model being dark during idle —
  the same gap we just closed for curiosity ignition.*

**Why this integrates the whole session's work:** G0 = the multilevel axiom; G1 = the frontier + curriculum +
intentions unified as "concerns"; G3 = the curiosity/dream intake; and the exploratory-ignition fix already
generates G3 candidates into the frontier backlog. The multilevel goal model is the **missing spine that ties
identity → concerns → tasks → novelty into one "what are we doing?"** answerable at every level.

---

## Sequencing + cautions (if we build)
- **Keystone first = G1 (ongoing concerns).** It's the layer Du lacks and the one that fixes dark-during-idle.
  Build it as a thin unifier *over* existing stores (curriculum/frontier/intentions) — a read-mostly
  "current concern" selector, not a new store of truth. Reuse, don't re-author.
- **G0 derives from the axiom — never a second copy** (identity-locus invariant). It's a *view*, not a store.
- **G3 already half-exists** (curiosity/dream questions) — promotion logic (recurrence → concern) is the new bit.
- **Priority is the delicate part** — get urgent-vs-important right (human task preempts now; concern governs
  idle) or we either ignore the person or never pursue anything. Spec it explicitly; observe before it steers.
- **Observe-first where possible:** log the selected concern + priority each cycle before letting it anchor
  behaviour, the way we did with the other live changes.

## Confidence
The human science (Carver-Scheier control hierarchy, Klinger current concerns, Little personal projects,
Kruglanski goal-systems + shielding, SDT intrinsic/extrinsic, Zeigarnik) and the AI grounding (options, feudal
RL, goal-conditioned RL, the LLM persistent-goal gap) are well-established at the conceptual level; exact
citations to-check. The *mapping* to Du's existing systems is verified against this session's code. The
strongest, most load-bearing claim: **the missing layer is the persistent "current concern" (G1), and it is
the same dark-during-idle gap, with the fix being to anchor idle cognition to a self-directed concern.**
