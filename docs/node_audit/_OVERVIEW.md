# Node Audit — overview (2026-06-16)

15 nodes examined (one Sonnet subagent each; per-node reports in this folder). The 16th node,
`meta_awareness_node`, was built this session and is excluded. Built/updated from file mtime + dated
in-code comments.

## The map

### Hot path — fires on every user cycle (lane: `hot`, qwen3-du :11433)
| Node | Position | Built | Last upd | State | Flesh-out priority — key gap |
|---|---|---|---|---|---|
| perception | Wave 1, every input | 05-30 | 05-30 | minimal-complete | **MED** — ignores `conversation_history` → misclassifies short continuations ("Why?", "That too") |
| emotion | Wave 2 | 06-04 | 06-04 | thin-complete | LOW-MED — blind to `state.affect` baseline (appraises each percept in a vacuum) |
| salience | Wave 2 | 05-30 | 05-30 | complete | LOW — stable, correct |
| memory_router | Wave 2 | 05-30 | 05-30 | minimal-complete | LOW-MED — no schema validation; blind to salience focus terms |
| recall | post-router (gated; rebind loop) | 06-08 | 06-08 | fleshed | LOW |
| episodic_buffer | post-recall (gated; rebind loop) | 06-04 | 06-04 | fleshed | MED — `_trim_axiom` dead code; no goal/concern stream |
| reflection | pre-critic, best-of-N | ~early | 06-12 | fleshed | MED — `needs_more_memory` emitted but **never consumed** |
| critic | post-reflection | 06-10 | 06-10 | fleshed | LOW (legacy) / **HIGH** (decomposed replacement, Phase 2) |
| executive | post-critic | 06-11 | 06-12 | fleshed | MED — facet-blind (`facet_note` absent from its prompt); no schema validation |
| voice | final output | 06-10 | 06-15 | fleshed | **HIGH** — Curator promotion is the designed next step (gated on shadow evidence) |

### Background / idle (lane: `background`, Bonsai :11460)
| Node | Fires | Built | Last upd | State | Flesh-out priority — key gap |
|---|---|---|---|---|---|
| inner_monologue | idle DMN, always-on | 06-10 | 06-16 | massively fleshed (1606 L) | LOW — over-built (a NameError in the new reread-hint path was fixed this session) |
| subconscious | background T1–T6, always-on | 06-07 | 06-16 | massively fleshed (2192 L) | MED — verify T5 (procedural) & T6 (themes) **read-paths**; verify prediction_error end-to-end |
| dream | sleep cycle | 06-15 | 06-15 | fleshed | LOW |
| consolidation | background, 60 s | 06-10 | 06-10 | fleshed | MED — `patterns_noted` is a **dead output** (logged, never used) |
| curiosity | dissonance-ignition | 06-09 | 06-15/16 | fleshed | **HIGH** — the contradiction gate routes `"curiosity"` verdicts that **nothing consumes** (wiring gap) |

## The cross-cutting theme: dead read-paths (the project's #1 failure mode)
Multiple independent audits surfaced the same pattern — **a signal is computed/stored but never read back**:
- curiosity: gate's `"curiosity"` route is logged, never forwarded to `add_theme`
- reflection: `needs_more_memory=True` never triggers a re-fetch
- consolidation: `patterns_noted` parsed, never persisted/routed
- subconscious: T5 procedural skills & T6 themes — storage without a confirmed hot-path read
- executive: `facet_note` not injected into its prompt (facet-blind)
- episodic_buffer: `_trim_axiom` defined, never called

This is the "write-only cognitive systems" failure mode. A sweep closing these is high-leverage and cheap.

## Recommendation — next to flesh out: **curiosity_node**
It is the one node that is (a) buildable now (not gated on runtime evidence, unlike Voice/Curator and the
decomposed critic, which both wait on shadow data), and (b) the natural completion of *this session's* work:
the contradiction gate now correctly routes abstract/poetic self-talk to `"curiosity"` instead of identity —
but that verdict dead-ends in a log. Wiring it into `curiosity.add_theme` closes the B/C convergence loop
(abstract tension → explore by reading, never identity pressure) and deepens the curiosity engine into a real
explore-arm. Strong secondary: a small sweep of the dead read-paths above.
