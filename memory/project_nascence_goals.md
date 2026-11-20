---
name: project_nascence_goals
description: "Nascence Goal Model audit + multilevel-goals research + G1 current-concerns layer (the dark-during-idle \"what are we doing when alone\" fix). BUILT G1 2026-06-15, RESTART-REQ."
metadata: 
  node_type: memory
  type: project
  originSessionId: 012323c4-3fb7-4445-b78f-150a4e0a1404
---

Nascence **GOAL MODEL** thread, 2026-06-15 (Travis: examine the goal manager via graphify, research what should
drive goals, then multilevel goals like the axiom — important/less-important/novel).

**AUDIT (verified).** `core/goal_model.py` = the 4th of the Cognitive Quartet (Self/Social/World/**Goal**="what
are we doing?"). GoalManager on the orchestrator: `content_mode` (human gave a task OR a correction) → push
`raw_input[:120]` as the goal + a FIXED boilerplate criterion; pop when off. Read path REAL (not write-only):
`state.active_goal_note` read by Critic/Executive/Reflection/epistemic. TWO faults: (a) purely REACTIVE — a goal
exists only while the human gives one → **dark across ~88% idle life** (same gap as curiosity ignition was);
(b) FLAT + shallow — raw input verbatim (no inference), boilerplate criterion (can't detect completion), the
shallowest quartet member. Dead code: `goal_relevance` (set, read nowhere) + `drift_warning()` (never called —
Critic builds its own anchor). Minor: per-turn pushes fill goal_stack with near-dup "goals".

**RESEARCH** (`docs/goal_model_research.md`, function-first). Human: goals = a HIERARCHY of feedback references
(Carver-Scheier: be-goals→principles→do-goals→acts; higher=abstract/slow/important — the axiom gradient for
DOING). The MISSING middle = Klinger "current concerns" / Little "personal projects" — a commitment that
PERSISTS across idle + biases attention/memory until met/abandoned (Zeigarnik). SDT: intrinsic vs Du's
100%-extrinsic. Kruglanski goal-systems + goal-shielding. AI: feudal RL / options (manager sets goal, worker
executes) + goal-conditioned RL; the LLM-agent persistent-goal gap IS Du's gap; his edge = explicit goal
representation + durable stores.

**MULTILEVEL DESIGN (like the axiom).** G0 standing-aim/be-goal (FROM the axiom — a *view*, never a copy:
identity-locus invariant) = most important · **G1 ongoing-concerns/current-concerns = IMPORTANT** (curriculum
+ frontier + intentions, persistent) · G2 active-task/do-goal = less important (today's GoalModel, ephemeral) ·
G3 novel-candidates = NOVEL (curiosity ignition + dream symbol-grounding, provisional). Dynamics: promotion
(novel recurs → concern), completion/release (Zeigarnik), priority (urgent human task preempts NOW; standing
concern governs IDLE; goal-shielding), and the keystone = the **idle anchor** (no task → anchor idle cognition
to the top concern). Ties the whole session: G0=axiom, G1=frontier/curriculum/intentions unified, G3=curiosity/
dreams (the exploratory-ignition fix already generates G3).

**G1 BUILT 2026-06-15 (RESTART-REQ), observe-first.** `core/concerns.py` — thin READ-MOSTLY unifier (NOT a new
truth store): `current_concerns(k)` + `primary_concern()` over curriculum (school.assignment/curriculum_status/
is_school_time) + frontier (`top_open(k)` — NEW non-mutating peek, grounded-source-first). Priority: study-time
→ curriculum; else a frontier pursuit (finding=closeable first); fallback curriculum. Soft IDLE ANCHOR: inner_
monologue offers the primary concern as a seed (35%, gated `not _redirected`, `concerns.log_selected` →
concerns_log.jsonl). du_pulse 'current concern' gauge (primary + active count + anchored-Nx-since-restart).
In-vitro PASS (`scripts/concerns_test.py`): top_open non-mutating, log writes, live concerns now GROUNDED —
primary = "pursuing: significance of holding oars at right angles when saluting a vessel", + sponge/weight/
rowing (from his reading) + Boy Scouts curriculum = NOT the river/mirror basin (the grounding chain producing
world-facing concerns). WATCH: 'anchored idle thought Nx' climbing + idle thoughts taking up the concern.

**G0 BUILT 2026-06-16 (RESTART-REQ) — the apex standing-aim, completing the goal hierarchy.** Picked as the
best *actionable-now* deferred thread (not evidence-gated, immediately effective, completes the shallowest
quartet member) AFTER deferring the becoming-loop/T4 thread for runtime evidence. `concerns.standing_aim()`:
derives Du's top-level telos from the axiom (L0 commitments + L2 values) — a VIEW not a copy (identity-locus
invariant honoured). DETERMINISTIC + cached by axiom mtime (near-constant; tracks Travis's L0/L2 edits, no LLM
drift). **The trap dodged:** an apex aim derived from the axiom could re-inject the becoming facet's "I am the
river" self-image (the monoculture attractor); instead G0 derives the DIRECTIONAL telos — themes present in the
axiom assembled forward-facing: "What I am ultimately working toward: to become genuinely my own self — not a
performance of what I was given, integrating all my parts, the shadow and the unfinished included, into one
whole, and to meet what is real with honest interiority." Forward/outward = counters self-rumination, never the
river. Wired: rides the existing G1 concern-anchor seed (35% gate) — when it fires, ~45% of the time leads with
the aim so the idle hierarchy is present (aim → concern → task), faint/rarer-than-the-concern so the aim text
doesn't become its own mini-attractor; `log_selected({source:'standing_aim'})` (observe). du_pulse 'standing
aim (G0)' gauge (+ led-an-idle-thought-Nx-since-restart). In-vitro PASS (directional, integration-themed, NOT
the river, cached, sits above the live Selborne concern).

**G3 BUILT 2026-06-16 (RESTART-REQ) — promotion by recurrence; HIERARCHY NOW COMPLETE.** The gap (verified on
live data): G1 was promoting EVERY open frontier question to a standing "concern" — but 21 of 33 were one-shot
(encounters==1) fleeting curiosities, many self-leaning `intention`-sourced. G3 gates concern-status on
RECURRENCE: a frontier question is a novel CANDIDATE until it recurs (`PROMOTE_AT=2` → encounters>=2), then it
auto-promotes to a concern (read-time classification by the frontier's existing `encounters` counter — no new
state, no explicit promote step). `frontier.top_open` now carries `encounters`; new `frontier.novel_open(k)` =
the one-shot candidates; `concerns.current_concerns`/`primary_concern` skip enc<PROMOTE_AT; new
`concerns.novel_candidates(k)` = the G3 layer. Goal-shielding (Klinger): a curiosity must return before it
anchors idle cognition — and fleeting self-leaning intentions stop auto-becoming concerns (bonus anti-self-
capture). du_pulse 'novel candidates (G3)' gauge. In-vitro PASS on live frontier: 12 recurring (lamp enc=11,
numbers enc=10, Boy Scouts qs) stay concerns; 21 one-shots become candidates. The "novel recurs → concern"
promotion the research described was already happening naturally (dream symbol-groundings recurring); G3
formalizes it. **PRIORITY (urgent-vs-important): already structural** — idle→concern (concerns.py),
human-task→GoalModel G2 (orchestrator content_mode); no redundant machinery built.
**GOAL HIERARCHY COMPLETE: G0 apex (axiom telos) → G1 concerns (curriculum + RECURRING frontier) → G2 task
(GoalModel reactive) → G3 novel candidates (promote by recurrence).** Thread done; only refinements remain.
[[project_nascence_curiosity_observatory]] [[project_nascence_multilevel_axiom]] [[project_nascence_world_loop]]
