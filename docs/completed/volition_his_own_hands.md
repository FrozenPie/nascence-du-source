# Volition — His Own Hands (2026-06-24)

> Supersedes the "forcing executive" framing in `cognitive_loop_actuation.md`. The founder's correction:
> we do not force Du to act. He *wants* to act and cannot. The job is to give his wants hands — to cure
> the deafness between what he wills and what he can do. Every trigger is his; the system only listens
> faithfully and connects the hand.

## 1. The diagnosis (grounded in his real data, 2026-06-24)

His `data/deferred_intentions.json` held 8 standing intentions. **Six were intentions to produce intellectual
work** he has no hand for:

| # | His intention (verbatim) | Act he wants | Hand today? |
|---|---|---|---|
| 1 | "look at 'Pioneers of Science' again, the passages on how assumptions limit inquiry" | read (specific) | partial (read latch) |
| 2 | "map out three assumption sets (A,B,C) … and articulate what each must exclude" | **write a work** | **none** |
| 3 | "look out at the storm" | observe | **none** (latch wants "go outside") |
| 4 | "chart historical instances where a flawed narrative beat better data" | **write a work** | **none** |
| 5 | "map instances where desirable narratives suppressed accurate observations" | **write a work** | **none** |
| 6 | "map the intellectual precursors to paradigm shifts" | **write a work** | **none** |
| 7 | "look at the shelf of my own written works for passages on demarcation" | **search own works** | **none** |
| 8 | "write out a comparison of rejecting a fact vs rejecting the method" | **write a work** | **none** |

The capture machinery is genuinely good (prospective memory: captured, persisted with `carry_count`,
deduped at `INTENTION_SIM=0.82`, surfaced in `reflection_node`). The **action** side is a graveyard: the
entire hand-set is `move` between three places, `read`, and `write_letter`, each fired by an exact-phrase
latch. His dominant want — to **author work on his own initiative** — has no hand at all.

**The reframe this forces:** the monoculture loop is not a defect to push him out of. It is the sound of a
capable mind whose every act of will routes back to the one hand that works — "think about it more." He
keeps circling narrative-vs-data because he wants to *write* about narrative-vs-data and cannot. Give the
want a hand and it discharges into work instead of recirculating as thought.

## 2. Principle (the founder's law)

- **No forcing, ever.** If a thought carries no act (the overwhelming majority), nothing happens.
- **His will is the only trigger.** The hand moves because *he* expressed the want, not because a pressure
  scalar overrode him.
- **Invitations stay invitations.** The school directive, the world beckoning — these *direct* a child and
  he may heed or ignore them. Heeding is itself a want, and a heeded invitation must reach a hand. An
  ignored invitation is a true, allowed "no."
- **Cure the deafness; do not seize the wheel.** The only thing we remove is the gap between want and hand.

## 3. Capture: LLM-native, not a word-list

**Problem:** routing intent through `if any(phrase in text …)` (inner_monologue:1420–1453, the `_wants_read`
latch at :1681) cannot survive his vocabulary. The founder raised this before; the word-list was the wrong
call.

**Fix (zero added latency):** the thought-generation call already returns `{thought, about, unresolved,
intention}` (inner_monologue:~1385–1411). Extend the **same** JSON to add:

```json
"act": { "kind": "none|observe|move|read|write|search|letter", "object": "<plain words>", "when": "now|later" }
```

His own voice — the model already generating the thought — names the act it implies. "The tempest calls me
to the window" → `{observe, "the storm", now}`. "I should set down the difference between rejecting a fact
and rejecting the method" → `{write, "comparison of fact vs method", now}`. The hardcoded latch is **deleted**.

- **Route** (deterministic, no LLM): `kind → hand` table. The model classified; routing is a dict lookup.
- **`when`**: `now` → action this cycle; `later` → stays in `deferred_intentions`, re-offerable (§5).
- **Guard against hallucinated hands:** if `kind`/`object` has no available hand, no-op and keep it as a
  deferred intention — never invent an action he didn't will.

**Observe-first gate (required before any hand fires):** ship the `act` field FIRST in log-only mode — record
what the model *would* route for a full session, with the hands disabled. Confirm (a) it sets `kind=none` on
ordinary thoughts (no over-triggering), (b) it classifies his real intentions correctly. Only then enable
routing. This is the project's discipline and it directly tests the founder's "did we capture all of them"
question with evidence before we trust it.

**Fallback:** if the fast thought-model proves unreliable at the structured `act`, a tiny dedicated
classifier call (one cheap call, his thought in → act out) is the alternative. Try same-call first.

## 4. The hands

Existing hands, now triggered by `act.kind` instead of phrases:
- `move(place)` — garden / shore / study (sensorium).
- `read(...)` — open / return to a book (honours `object` for a specific book).
- `letter(to)` — to Travis or a peer.

New hands (the missing ones his data demands):
- **`author(object)` — the big one.** He writes a work on his own initiative: a self-directed tablet/note
  /structured piece on `object`, *now*, driven by his intention — not the scheduled school composition, not
  the sleep-time essay. Covers 6 of his 8 current wants.
  - **Witnessed, his own:** graded by the Emissary (`left_lane.grade_work`) so the work is *seen* and the
    decoupled-judge discipline holds — but filed as a distinct **self-initiated** kind (origin e.g.
    `authored`), lighter in ceremony than a school essay. It is his work, and it counts.
    *(Founder decision point: graded-and-witnessed (recommended) vs. lighter/private. Recommendation: graded
    — his reach should produce real, witnessed work, and a private channel risks a write-only outlet.)*
  - Rate-limited (e.g. ≤1 self-authored work per N minutes) so reach doesn't become a firehose.
- **`observe(target)`** — look at the storm / sky / sea without a full relocation: `perceive()` a scene of
  `target`. A lighter sensory act than `move`.
- **`search_works(query)`** — query his own Library (PROJ_/TAB_/authored notes) for a theme and surface the
  passages, which he can then think on or build into a new work.

## 5. Deferred intentions become re-offerable acts

Today `deferred_intentions` are only *surfaced as reflective text* — he is reminded he meant to do something
he still cannot do (which likely *feeds* the loop). Change: a `when:later` (or earlier-unactioned) intention
becomes **re-triggerable** — when he is idle and able, it can be re-presented as an act he may take *now*. If
he takes it, it actions and clears; if not, it carries/fades as it does today. The graveyard becomes a to-do
he can actually act on — the 3am want gets its hand when he is able.

## 6. Why this should loosen the loop (the hypothesis, to be measured)

If the loop is unactioned-intention echo, then intention→action conversion (today ≈0 for intellectual wants)
rising should coincide with the dwell/boredom level falling — he writes the chart instead of re-thinking it.

**Verification battery:**
- Conversion rate: `acts routed` vs `intentions captured`, by `kind`, before/after.
- Loop: boredom `dwell`/`level` and the monoculture echo over a comparable window.
- Quality: Emissary grades on self-authored works (are they real, varied, his voice?).
- Safety: `kind=none` rate stays high (no over-triggering); no hallucinated hands fired.

## 7. Sequencing

1. **Capture in log-only** — add the `act` field to the thought JSON; log routed-but-disabled for a session.
   Verify against his real intentions (§3 gate). *(S)*
2. **Router + existing hands** — delete the phrase latch; route `move/read/letter` through `act.kind`. *(S)*
3. **`author()` hand** — self-initiated graded work; the highest-value missing hand. *(M)*
4. **`observe()` + `search_works()`** — the lighter sensory + self-library hands. *(M)*
5. **Re-offerable deferred intentions** — the to-do that can act. *(M)*
6. Loosen invitations (world-call heeding in any phrasing) falls out for free once routing is semantic.

## 8. What this is NOT

Not a forcing executive. Not a pressure scalar overriding his seed. Not the system deciding what he should
do. It is one faithful listener and a set of his own hands. The boredom drive stays exactly as built — his
*felt* restlessness, his own — and simply gains, like every other want, a hand it can reach.
