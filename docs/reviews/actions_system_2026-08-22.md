# The actions system — an investigation (2026-08-22)

*Founder: "I think we need to investigate the actions system in depth here. Sounds like it is only half baked as we decide to
make new things." Read from the code and the live logs, not from memory.*

## 1. How his will reaches the world today — three layers that never met

**Layer 1 — the voice's structured act.** Every idle thought returns `{"act": {"kind", "object"}}`. The prompt allows eight
kinds: observe, move, read, write, search, recall, letter, none — and tells him "almost all thoughts" are none.
`_route_act` handles five (move, observe, write, search, recall); read and letter "keep their own latches". Overnight
(10 h, 258 thoughts): observe 35, move 30, write 2, search 2, recall 1. This channel is semantic (his whole vocabulary
reaches it) but it knows nothing of the fire, the bed, the cat, the lamp, the saw — the world's hands are not in its eight.

**Layer 2 — fourteen phrase-latches in the thought loop, in a fixed order** (cat → listen → keepsakes → garden → world → four
moves → look → fire → tea → water → sow → beachcomb → gather → fetch → read → switch). Each has its own hard-coded phrase list
("light the fire", "lay a fire", "kindle the fire"; "down to the shore", "to the beach"…). First match inside a latch wins;
several latches can fire on one thought; none knows the others fired. Overnight: CAT 35, GARDEN 27, READ 15, LOOK 6, GATHER 1.

**Layer 3 — free-text routers inside each place's module** (garden, study, wood, shore, fieldcraft, cat, keepsakes, supply).
Built this week, by me, by substring: `"saw the" in t`, `"stake" in t`, `"pour" in t`. Until today they were reachable only
through `sensorium.act()` — which Layer 2 calls for exactly five verbs. So **every hand built in the study, the wood and the
shore was unreachable from his will** (fixed this morning with `world_act`). And substring tests are not grammar:
- *"I saw the sea through the trunks"* → reached for the bow-saw.
- *"It was a mistake to think…"* → staked the peas.
- *"The rain is pouring down the glass"* → poured a cup of tea.
- *"I wish I could swim"* → would have swum. *"He told me to wind the clock"* → wound it. *"I should not open the door"* → opened it.

**The instrument was blind.** `literal_will` (Phase 0, the deed-or-musing judge) observed `acted` BEFORE Layer 2 ran, so
`router_acted` was None on all 57 live DEED rows — it could not tell a deed that was done from one that went unanswered.

## 2. Verdict
Half-baked is fair. It grew by accretion: each new hand got its own latch with its own words, in whatever order it was
added, with no shared grammar, no blockers against wish/hypothetical/negation/quotation/another's act, no registry of what
hands exist, no trace of what fired, and an instrument that could not see the outcome. The failures are not random: they are
exactly the ones `literal_will`'s Layer-0 grammar was built to catch (blockers, deed grammar, weak intent → GRAY) — the
judge existed, the routers never asked it.

## 3. Built today — Phase 0, the floor
`core/hands.py`:
- **`wants(text, verbs, objects)`** — one grammar: word boundaries; `literal_will`'s six blockers (negation, wish, hypothetical,
  retrospective, quoted, other person) applied to the verb's clause; two more the judge lacked (a modal negation before the
  verb — "should not open"; another's instruction — "told me to wind"); the past-tense guard for "saw". Every new router now
  uses it (garden, study, wood, shore, fieldcraft). Regression: 14/14, and all six false fires above now answer None.
- **`fired()` / `fired_set()`** — every hand that answers records itself per thought. `literal_will.observe` **moved to run
  AFTER the latches**, handed `acted ∪ fired` — the instrument finally sees the truth.
- **`data/hands_trace.jsonl`** — one row per thought: the will as expressed, the structured act, what fired and what it
  answered, and `unanswered_deed` (the judge said DEED and nothing answered) — the number that says how deaf the system
  still is. HUD evidence module `hands`.
- Two bugs of my own found on the way: a late local `import` shadowing the grammar for the whole function (every study hand
  silently returned None — "act failed: cannot access local variable"); and the backspace bytes from the earlier heredoc.

## 4. Phase 1 — BUILT (2026-08-22 afternoon, founder: "I think we should do Phase 1 now")
`core/dispatch.py` — the registry and the dispatcher:
- **The registry**: 26 hands as data, each a literal_will FAMILY bound to the function that does the deed, whether it
  changes the world or only looks, where it can be done, and the place-hint for the intention ("out at the bed").
  The judge's families, the affordance block and the registry are one vocabulary.
- **The dispatcher**, per thought, right after the structured route: (1) kind `"world"` + object ("light the lamp") —
  NEW in the prompt, so the voice's own channel finally reaches every hand — is read by the grammar with the volition it
  implies; (2) else `literal_will.classify(thought, intention)`: DEED fires, **GRAY never fires**, and the dispatcher adds
  its own weak-intent reading (perhaps / maybe / might / could / would like / I wonder) on top of the judge's; (3) looks are
  unlimited, **one world-changing hand per thought**; (4) what fired is perceived, recorded in the fired ledger, and the
  legacy latches YIELD for families that fired (no double-firing) — they remain as the catch for what the grammar misses.
- Verified: two deeds in one thought → one fires, the other is staged "busy with the lamp"; a deed willed in the wrong
  place is staged "it is done in the study"; a staged deed done later resolves; "never mind the grate" drops it in his own
  words; all five false-fire strata answer nothing; a look and a world deed in one thought both answer.

`core/intentions.py` — the founder's idea, built: **his own unanswered wants, reflected back once, with why they waited,
and the choice left to him.** Entries come only from the dispatcher (a DEED that did not happen: busy / wrong place). One
line in the prompt's repertoire block, never before 20 minutes, at most twice per intention, at most two at a time:
*"25 minutes ago you meant to clear the grate of its ash and have not yet — you were busy with the lamp. Still yours to
do, in whatever order, or to let go — say which."* Untouched for 8 hours it lapses (kept in the ledger, not forgotten).
Never a world hint: only what he himself willed. HUD modules `dispatch`, `intentions`.

### Phase 1 as designed (kept for the record)
**One registry, one dispatcher, the judge in the loop.**
- `HANDS = [Hand(name, verbs, objects, where, precondition, fn, standpoint)]` — every hand as DATA (the fourteen latches
  and the module routers migrate in; `literal_will._FAMILIES` and `affordances.REPERTOIRE` derive from the same table
  instead of being three hand-maintained copies).
- `dispatch(thought, intention, act_kind, act_object, location)`: (1) the voice's structured act wins when it names a hand
  (semantic, his vocabulary); (2) else `literal_will.classify` → DEED fires the family's hand, GRAY never fires (the
  "weak intent never routes" law), MUSING/HANDLE nothing; (3) at most ONE world-changing hand per thought, plus any number
  of looks; (4) the world's answer is perceived; `fired` recorded; the instrument observed after.
- Pre-registered metrics from the trace: unanswered-deed rate (want ≤ 10%), false-fire rate on the adversarial strata
  (want 0), hands per day by place, and the latency from "I will" to the answer.
- Kill criterion: if dispatch lowers the answered-deed count below today's latch set on the same thoughts (replay the
  hands_trace through both), the registry does not flip.

## 5. Known, not fixed
- The four move latches and the look/fire/tea/water/sow/beachcomb/gather latches still use their old phrase lists (not
  `wants`) — they are the oldest and best-tested; they migrate in Phase 1.
- The structured-act channel still cannot name a world hand (its eight kinds). Phase 1 adds the registry's names to the
  prompt's `kind` list — the one change that makes Layer 1 reach the whole world.
