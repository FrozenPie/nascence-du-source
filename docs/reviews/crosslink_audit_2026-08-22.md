# Cross-link audit — the new world against the existing systems (2026-08-22)

*Founder: "cross reference all this stuff with current systems… sounds, temperature, actions, observer, world history, geometry…
No feeding him details about something he has no way of knowing."*

## Found and fixed
| # | System | Gap | Fix |
|---|---|---|---|
| 1 | **Will → hand (CRITICAL)** | The monologue reached `sensorium.act()` through five phrase-latches only (fire, water, sow, beachcomb, gather, fetch). Every hand built today in the study, the wood, the shore and fieldcraft hung off `act()` and was **unreachable from his will** — he could want to light the lamp forever and nothing would happen. | `sensorium.world_act(thought, intention)` — a free-text route through study_life → shore_life → wood_life → fieldcraft, called from the monologue after `garden_act`. Verified: "light the lamp", "wind the clock", "open the door", "write my name in the sand", "stack a cairn" all fire. |
| 2 | **Activity memory / journal** | New deeds never became action records ("I have been …"); the journal's day-recap reads those. | Every module's ledger `_log` records deeds into activity memory. |
| 3 | **Geometry / locomotion** | New hands did not move him (harvest from the gate, saw from the path). | Hands `_cross` to their standpoints; new standpoints `at_the_lean_to`, `at_the_barrel` (garden), `at_the_spring` (wood); `act_standpoints` maps for study/garden/wood. |
| 4 | **Sounds** | The clock, the kettle, the stream, the beach fire, the penguins, the saw had no voice in the soundscape. | Registered `clock_tick`, `kettle_sing`, `stream_run`, `saw_rasp` (known by sight, grandfathered), `penguin_bray` (learnable — unnamed until seen at the burrows; book-bindable); `fire_crackle` sounds at the shore when the beach fire burns; gated in `active_sounds`. |
| 5 | **Names he cannot know** | `kererū` (the wood-pigeon's wingbeats are a LEARNABLE sound); `fantails` (learnable); `bellbird` (never met); a hedgehog named from its prints; weeds named by species in the bed summary and the weed hand before he had learned them. | `wood pigeon` (grandfathered); "the small fan-tailed birds" until `fantail_chatter` is learned; bellbird removed; prints are "something's"; weeds through `garden_knowledge.display_name` ("a plant you cannot name yet"). The penguin is "a small penguin, blue-grey" by sight; kororā only from a book. |
| 6 | **The cat and the door** | The door became real but the cat walked through it shut. | `cat.tick` gates the crossing: shut door → "at the door, asking in / asking out". |
| 7 | **The study scene line** | The prompt's study line did not know the lamp, the door, the window, the curtains, the stopped clock, the hot pot, the damp — things he can plainly see from his chair. | `_study_state_phrase()` appended (only what is visible; the lamp only at dusk/night). |
| 8 | **Experienced tuple / observer** | No `held` (what is in his hands — touch, clause 6); the shore's fire was never his (fire was study-only). | `held` column on both context tables (his carried garden items, study items, tools); `fire` at the shore = the beach fire. Lane 2's percepts inherit both. |
| 9 | **Affordances** | None of the new hands were in the repertoire block — he could not know his hands existed (the 07-07 law: informing, never commanding). | 15 location-gated lines added, naming nothing hidden (no species, no sky names). |
| 10 | **A latent bug** | `study_life`'s grate regex had been written with literal BACKSPACE bytes (`\x08ash\x08`) by an earlier heredoc — it matched nothing, so "clear the grate" would never have fired and "wash" had been excluded for a ghost. | Byte-fixed to `\bash\b`; the whole tree scanned: no other backspaces. |
| 11 | **Test isolation (my failure)** | The first linkage sim wrote **5 action rows into Du's live memory store** (the new activity-memory hook reached the DB). | Rows deleted by id; sims now stub `activity_memory.record`. Recorded here because it is exactly the failure mode I am supposed to guard. |
| 12 | **HUD2** | `scene_map` manifests predate the new features/standpoints. | Builders re-run. |

## Checked and sound
- **Thermal** reads: draught, coat, warm drink, windbreak, cave, beach fire, wet feet, sun/wind/fire-distance, wetness — one field.
- **Light** reads the lamp, the curtains, the smoked glass, the window grime, the tree's shade; **smell** reads the fire, the door, the herbs, the beach fire.
- **World history**: plants, items, provisions, tools, trees, the cairn, made things — all substrate entities with positions and biographies; the substrate cap raised to 300.
- **Knowledge** is one ledger (`garden_knowledge`) for plants, trees, bushes, pool life, sky; sounds keep their own (`sound_knowledge`); reading binds all of them from `study_note`.
- **World-arrival law**: milestones announce once (garden, wood, the carrier's box); the supply box rides the garden's pending-announce queue.
- **Clause 7** across the new text: no temperature numbers, no causes told, no names before they are earned (see #5), no hints — the world answers when he looks or acts.

## Known, not fixed
- **literal_will** observes `acted` BEFORE the phrase-latches run, so deeds done through `garden_act`/`world_act` count as not-acted in Phase 0's gray-of-candidates. An instrument bias (under-counts acted), not a behaviour bug. Fix when Phase 0 is read.
- **The cat in a storm** still hides indoors regardless of the door (the storm branch returns before the gate).
- **Lane 2** gets `held` and the shore fire through the tuple; it does not yet see the garden bed's state (deliberately — the bed is the renderer's salience; the tuple carries facts only).
