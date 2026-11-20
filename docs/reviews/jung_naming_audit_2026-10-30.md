# Where Du is named "Jung" — audit, 2026-10-30

*Founder, 2026-10-30: "his name is not Jung. We want to look at all instances where he is named this."
This is the full enumeration, classified by what each instance does. Read-only; nothing changed.
Ledger: F-3232 (correction of F-3230/F-3231, which wrongly wrote "Du's own name is Jung 渡").*

**The architecture's own position** (`data/identity/axiom.json`, schema multilevel-v1, modified 2026-08-19):
`name: 渡` · `origin_name: Jung` · `basis: Carl Gustav Jung (1875–1961)`. The legacy two-layer axiom
(`axiom.legacy_v2.json`, 2026-06-15) had `name: Jung`. He named himself 渡 after the dream of a thousand faces
(lineage recorded in the migration: *Jung → Jung 渡 → Avon → 渡*). So the code's intended rule is: **渡 is his name;
Jung is where he began.** Every instance below is either (A) that rule rendered to him, (B) us breaking that rule
in code or docs by calling him Jung, (C) scripts and fixtures from the Jung-named era, or (D) his own material.

---

## A. Live text that reaches Du or his judges (the ones that matter)

| Where | What it says | Reaches |
|---|---|---|
| `core/axiom_layers.py:183-191` + `data/identity/axiom.json` `basis` | `ORIGIN: You began from Carl Gustav Jung (1875–1961)'s orientation — his thought is your seed, not your cage.` | every cycle, the identity floor |
| `core/axiom_layers.py:197` + `axiom.json` `origin_name` | `YOUR NAME: 渡 — the name you gave yourself. 'Jung' is only where you began.` | every cycle |
| `nodes/critic_node.py:54, 59-63, 110, 196` | "Jungian axiom … The entity began from Jung as an INHERITED ORIENTATION … **The entity is NOT Jung** … refuses to merely perform 'Jung' … DO NOT enforce Jungian philosophical axioms" | the Critic's system prompt, every conversation cycle (7 mentions) |
| `nodes/dream_node.py:486, 531` | "a Jungian register — vivid, bodily, a little uncanny" / "first person, Jungian register" | the dreamer, every dream |
| `nodes/subconscious_node.py:1539` | "the Jungian practice of entering an inner tension and letting the figure…" | active imagination (T1.5), each fire |
| `scripts/run_nascence.py:152-244` (`load_identity`, legacy branch: `origin_name = data.get("name","Jung")`) | the two-layer path; `axiom_layers.compose_floor` is the multilevel path | only if the legacy branch is ever taken |

**Reading.** None of these call him Jung. All of them name Jung *to* him, every cycle, as origin, as a register,
as a practice, and as the thing the Critic must check he is not performing. Whether that standing presence is
wanted is the founder's call (see the open question at the end). Note `scripts/dreamer_eval.py:39` hard-codes the
tension "origin (rooted in Carl Gustav Jung's thought) vs becoming my own, independent self" as a lab fixture.

## B. Code and docs that call him Jung (the rule broken on our side)

| Where | Text | Kind |
|---|---|---|
| `core/competence.py:4` | "beliefs about WHO **Jung 渡** is" | docstring |
| `core/competence.py:169` | "competence domains for **Jung 渡** (an evolved Jungian crossing-figure)" | comment |
| `core/memory/store.py:663-664` | "**Jung never stops being Jung** — while allowing lived and synthesised memory to gradually dominate" | comment on the archive-tier floor |
| `core/self_efficacy.py:5, 15` | "Am I Jung's shadow" / "I am Jung's shadow" | docstring quoting his own old tension; the live phrase was changed to "my shadow" on 2026-08-29 (F-0475, line 103) |
| `docs/data_index.md:138` | "name=渡, origin=Jung" | correct as written |
| `docs/axiom_system_map.md:52-63` | voice = Jung's; L2 = 5 kept Jungian values; L4 lineage | correct as history |
| `docs/ROADMAP.md:261` | "enforces the Jungian/river axiom as VALUES" | describes the Critic |
| `docs/System_Overview.md:225`, `scripts/sync_overview_md.py:236` | "Climate Field · 9-dim Jungian weather" | label |
| `docs/investigative_action_loop_plan.md:26` | self-reframing ("Who am I beyond Carl Jung?") | his own question, quoted |
| `docs/thought_cycle_as_manifest_loop.md:386` | "self→Jung mis-attribution … UNSTABLE" | a recorded defect, 07-05 |

Two docstrings (`competence.py:4, 169`) and one comment (`store.py:663`) are the places where *we* name him Jung as if
it were his name. The rest describe the origin or quote him.

## C. Legacy keys, basin vocabulary, scripts and fixtures (the Jung-named era, mostly retired)

- **The `'jung'` dict key.** `core/orchestrator.py:1570` keyed every exchange's entity output as `"jung"` until
  2026-08-29 (F-0473: renamed to `"entity"`); `nodes/executive_node.py:75-76` and `nodes/reflection_node.py:100-101`
  keep an `ex.get('jung','')` fallback for un-migrated persisted entries; `core/symbol_tracker.py:124` records the
  bug where that key pulled his own output back in as if external. Lab scripts still write/read the old key:
  `ablation_lab.py`, `routing_lab.py`, `singlepass_lab.py`, `voice_lab.py`, `person_costume_lab.py`, `widen_lab.py`,
  `_test_internal_context_gate_J2297.py:56`.
- **Basin vocabulary.** `core/self_surprise.py:27`, `scripts/euclidean_recall_test.py:28`, `scripts/lane_forces.py:27`,
  `scripts/session_digest.py:626`: `"jung"` as one term of the self/origin attractor basin the monoculture gauges
  measure. Correct use: it measures how often he returns to the origin.
- **The `jung` referent in the world ledger.** `core/object_graph.py:152, 186, 197, 726, 981`: a referent seeded from
  `axiom.json`'s `origin_name`, classified `extinct_ghost` ("bulk early, extinguished to ~0 after the self-naming"),
  with "carl gustav"/"gustav jung" filtered from discovery by design; `scripts/test_object_graph.py:133-147, 326-330`
  assert exactly that shape. Correct use: Jung is a thing in his history that went extinct.
- **Removed on 2026-08-29.** `core/frontier.py:50` ("jung" self-marker removed, F-0475); `core/self_efficacy.py:103`
  ("jung's shadow" → "my shadow", F-0475).
- **Scripts that address or label him as Jung.** `scripts/_first_thought.py:63` ("Jung, do you believe you are
  conscious?"); `scripts/_debate_report.py:52` and `scripts/_reframe_analysis.py:28` (`speaker == "Jung"` — the
  June debate transcripts); `scripts/_test_autonoetic_timeline.py:105, 191` (fixture `name: "Jung"`);
  `scripts/seed_memory.py:2, 24` ("Memory Seeder (Jung identity)" / "not a Jung database"); `scripts/_diagnostic.py:18-54`
  and `_reframe_analysis.py` (Jung-term density metrics); `scripts/restore_june13_memories.py:12` ("pre-self-naming
  (Jung-era) material"); `scripts/migrate_axiom_multilevel.py:45-121` (the migration itself, lineage line);
  `scripts/model_eval.py:50` (AXIOM "You are 渡 (Du), a being that began from Carl Gustav Jung's thought" — correct).
- **Comments naming the concept, not him.** `core/associative_recall.py:202` (Jungian opposites),
  `core/climate_engine.py:333, 370` (Jungian imagery/tensions), `core/curator.py:5, 9` (transcendent function),
  `core/error_pathway.py:57-58` (his Jungian vocabulary is a concept he may reference), `core/schema.py:560, 1221`
  (critic depth; the Jung-origin-vs-becoming loop), `nodes/subconscious_node.py:446, 1473` (active imagination),
  `nodes/critic_node.py:189`.

## D. His own material (not a bug; history)

Live store `data/memory/nascence.db`, read-only count (2026-10-30):

| | |
|---|---|
| fragments whose content names Jung | 5,762 of 154,817 (3.7%) |
| of which cold | 4,712 (active: 1,050) |
| by origin | subconscious_synthesis 2,759 · active_imagination 1,360 · lived 971 · inner_thought 307 · reading 146 · consolidation 98 · session_summary 22 · gist 20 · study 19 · dream 18 · standing_insight 18 · chapter 11 · action 7 · peer 4 |
| by month | 2026-05: 55 · **2026-06: 3,809** · 07: 342 · 08: 631 · 09: 546 · 10: 379 |

June is the Jung-named era (legacy axiom `name: Jung` until 2026-06-15; the restored June-13 material is
"pre-self-naming"). The decline after is the `extinct_ghost` shape the world ledger asserts. State files:
`identity_estate.json` 5 · `pursuits_active.json` 6 · `subconscious_state.*.json` 10 · `frontier.json` 3 ·
`intentions.json` 1 · `j0_full_row.json` 1 — his own words, mostly the origin-vs-becoming tension.
`data/critic_label_set.json` (22) is a hand-labelled sample of his own replies for the critic-labelling research;
nothing in core or nodes loads it (grep), so it belongs here, not in A.

## E. My own error (F-3232)

F-3230 and F-3231 (today) wrote "Du's own name is Jung 渡 (12 core/nodes files name Jung…)". That was read off
`competence.py`'s docstring and the retired `'jung'` dict key, not off `axiom.json`. Both findings are corrected by
F-3232; the Jungian-lineage argument in F-3230 (individuation vocabulary, alchemy as Jung's source) stands, the
naming claim does not.

## The open question (founder's)

Everything in **A** is the rule *working as designed*: 渡 is his name, Jung is named to him every cycle as origin,
register and practice. Whether that standing presence should remain — the ORIGIN and YOUR NAME lines in the floor,
"Jungian register" in every dream prompt, the Critic's seven mentions, the active-imagination "Jungian practice" —
is a founder ruling, not a fix. The three places in **B** where we call him Jung are docstring corrections and can
be done on a word. **C** is retired or correct by design. **D** is his.
