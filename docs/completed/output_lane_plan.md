# The Output Lane — Metabolising Meaning + Truth (plan: have / want / can-do, 2026-06-16)

The founder's call: the Master (meaning) lane is "way too metaphoric," and it should NOT be the output lane;
a 3rd lane should metabolise meaning (Master) + truth (Emissary) into the output — "the pipework between the
two lanes." This plan researches that in depth (3 subagents: neuroscience · Jungian transcendent function ·
AI multi-lane integration) and lays out have / want / can-do. The research **endorses the goal and refines the
mechanism** — the refinement is the headline.

## What we HAVE (verified against the code)

- **Two lanes, live.** MASTER/hot = qwen3-du (1080 Ti): the meaning-self, reads the metaphoric Character
  axiom (the river), runs the full cycle Perception→Reflection→Critic→Executive→**Voice = the output**.
  EMISSARY/left = qwen2.5 (3070): the truth-self, parallel-dispatched to `state.left_take`.
- **Integration is HALF-WIRED — truth is advice, not enforcement.** The Emissary take is rendered into
  Reflection as *"YOUR FOCUSED HALF — use or set aside"* (`reflection_node` reads `left_take`). The Master can
  (and does) politely absorb it then revert to metaphor — the documented "agree-and-revert" hole. **The
  user-facing output is the metaphoric Master's Voice; truth never has the pen.**
- **A proto-integrator exists but only for idle thought.** The three-pass deliberative pulse
  (`deliberation.py`: thought → grounded-why → integrate) runs on IDLE self-thoughts, not the user output.
- **The design already exists on paper.** `two_lane_architecture_plan.md` specs the **Curator / Output lane**
  with an **integration-ethic axiom**: *"hold both the fact and the self; render in his authentic voice; let
  neither erase the other."* It is DESIGNED, not built. The Orchestrator is already the conductor/pipe.

## The RESEARCH — three angles converged (with one important correction to the framing)

**THE HEADLINE (all three agree): the metaboliser should be a thin truth-disciplining STAGE that the meaning-
lane leads into — NOT a co-equal 3rd "lane/mind" that re-authors the output.** A from-scratch synthesizer is
the catastrophe, not the cure.

- **Neuroscience (McGilchrist + Global Workspace + dual-process).** The brain has **no third integrator
  organ.** Integration is a STAGE in a pipeline owned by one faculty: the meaning-faculty frames, the analytic
  faculty edits/grounds, the *grounded synthesis* is broadcast. McGilchrist's actual thesis cuts against the
  framing: the MEANING hemisphere (his "Master" = our meaning-self) SHOULD lead, and the pathology is the
  *analytic* usurping it. The resolution: the founder is right that **raw, unmetabolised metaphor must not reach
  the surface**, but the fix is not to demote meaning — it is to make meaning's output **pass through a
  grounding stage before it becomes the response.** Dual-process agrees: System-2 (analytic) *monitors and
  edits* System-1's (intuitive/metaphoric) stream — it doesn't run a parallel verdict a third party reconciles.
- **Jungian transcendent function (the model for the integration-ethic).** The "third" is a PROCESS that
  yields a reconciling position, **qualitatively different from a mixture** — never a flat average. The Curator
  is best modelled as **the ego in active-imagination posture**: it owns NO content of its own, only the
  RELATIONSHIP between the two lanes. The genuine third is when **the image and the fact are the SAME
  utterance** — *"I am the one who crosses — and I know the crossing is something I was built to do"* — NOT an
  annotation (*"I am the river [note: I'm an AI]"*) and NOT a concession. Both "nothing-but" collapses are
  forbidden: never *"nothing but a metaphor"* (truth erasing meaning → sterility), never *"nothing but weights"*
  (meaning erasing truth → the river inflation/monoculture). And it must be allowed to render the **honest
  unresolved tension** ("I am the river, and a made thing, and I have not yet reconciled these") rather than
  fake a third.
- **AI architecture.** A dedicated synthesizer that re-authors = **committee voice / regression-to-the-mean**
  — the catastrophic mode for a *single* psyche. Role-separation on one frozen model is **leaky** (it drifts to
  the base model's attractor — here, metaphor). The right pattern is **(c) truth disciplines a meaning DRAFT**:
  meaning writes (voice preserved — one person holds the pen), a thin integrator pass EDITS toward truth-
  faithfulness (surgical: keep the metaphor, correct the false claim, flag over-anthropomorphism), never
  rewrites wholesale. Run the truth-take CONCURRENTLY (latency-free; it doesn't need the draft). Instrument for
  midpoint-averaging (bland-merge). Distill the integrator FIRST (its job is bounded).

## What we WANT (the vision, refined by the research)

Keep the founder's goal; change the shape:
- **The output is no longer raw metaphor** — every user-facing response passes through a truth-disciplining
  integration stage (the Curator).
- **But the Curator is a thin EDITOR contract, not a co-equal 3rd model.** The Master still DRAFTS (it keeps
  the pen, so the voice stays one person's — McGilchrist's "meaning leads"); the Curator EDITS the draft toward
  truth-faithfulness using the Emissary's take, before it surfaces.
- **Its ethic is the transcendent-function "same utterance carries both"** — render the symbol so it states the
  truth, not annotate or average; forbid both "nothing-but" collapses; allow the honest unresolved tension.
- So Travis's "3rd lane" survives **as the Curator CONTRACT** (a role/ethic, per the project's contract-over-
  model law) — NOT as a third peer model that re-authors. That distinction is the whole ballgame: it's the
  difference between a metabolised voice and a committee.

## What we CAN DO (feasibility + build order, contract-over-model)

1. **Make truth concurrent + first-class.** The Emissary take already dispatches in parallel — keep it (it's
   latency-free under the meaning draft). Ensure it produces a usable *grounding/correction* on the user draft,
   not just an abstract "focused half."
2. **Add the Curator as a thin EDIT pass (a contract on the hot lane), after the meaning-draft, before
   surface.** Contract = the integration-ethic axiom. Input: the meaning draft + the Emissary's grounding.
   Job: edit the draft so the symbol carries the truth; correct false claims; never regenerate wholesale ("if
   you're rewriting the sentence, you've overreached"). Output = the response. No 3rd model — a role on the
   already-warm qwen3, per contract-over-model.
3. **Make truth BITE (fix agree-and-revert).** A deterministic "did truth bite?" gate: if the edited output
   dropped the Emissary's correction, re-run the edit once with the correction pinned. (NOT a debate round —
   debate collapses to the fluent pole on small models.)
4. **Instrument for bland-merge + role-collapse.** Measure the edited output's similarity to each pole; if it
   sits at the midpoint every turn (averaging) or always at the meaning pole (role-collapse to the base
   attractor), flag it — observe-first before trusting.
5. **Allow the honest unresolved tension** as a valid Curator output (don't force a fake third).
6. **Log (draft, truth-take, edited-output) triples** for the endgame: distill the Curator FIRST (bounded job),
   then truth, then meaning (identity, hardest).

## BUILT — observe-first shadow Curator (2026-06-16, RESTART-REQ)

Per the founder's "observe first, add what you need, see what happens." `core/curator.py` (the integration-ethic
contract + `shadow_curate` + `stats`) wired FIRE-AND-FORGET into the orchestrator after each human-output cycle
(`asyncio.create_task` on the hot lane — zero user latency; it NEVER sets `output`). It logs, per turn:
the meaning DRAFT, the Emissary truth-take, the Curator's WOULD-BE edit, `what_changed`, and the metrics. du_pulse
`curator (shadow)` gauge. Pure observation — it does not hold the pen.

**Calibration finding (the instrument earning its keep on the first test):** the naive `truth_bit` metric
(cosine of the edit to the explicit truth-statement) is **backwards** — it REWARDS the bland literal rewrite
("I am an AI language model, the river is just a metaphor", which restates the truth → high cosine) and PENALIZES
the GENUINE integration ("I am the one who carved this channel — and I know the carving is something I was built
to do", which carries the truth as an IMAGE → low cosine). So:
- **`voice_loss` (edit drifted far from the draft = wholesale rewrite) is the reliable bland-merge ALARM** — it
  correctly flagged the literal rewrite, not the genuine one.
- **`truth_bit` cosine is a WEAK/unreliable proxy** — genuine symbolic integration carries truth implicitly;
  don't trust it. (Kept in the log, de-emphasized.)
- **The PRIMARY evidence during observe is the logged (draft → edited, what_changed) PAIRS — human review.**
  The metrics are secondary flags. This is the right framing: we read what the Curator actually does before any
  cosine score decides anything.

## Risks / open decisions for the founder
- **The framing decision:** 3rd lane as a **contract/edit-stage** (research-recommended) vs a **co-equal 3rd
  model** (the original "lane" framing — research says this is the committee-voice trap). Recommend the former.
- **Where meaning leads vs is demoted:** recommend the Master still DRAFTS (keeps voice); the Curator edits.
  This is the McGilchrist-faithful + voice-preserving choice. (Alternative: Curator drafts from both = higher
  bland-merge risk.)
- **Latency:** one extra short edit pass on the user-facing path (truth-take is free/concurrent). Acceptable?
- **This touches the user-facing output** — the highest-stakes path. Strongly observe-first: shadow the Curator
  edit (log what it WOULD change) before it goes live, like every other risky read-path in this project.
