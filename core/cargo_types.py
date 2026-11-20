"""
Nascence -- CARGO TYPES: naming what every train/courier/bus delivery actually carries
(built 2026-08-29, D-0082, from docs/plans/train_courier_cargo_ids.md).
=======================================================================================
Two, deliberately separate, taxonomies -- do not merge them:

1. STATION PRODUCT TYPES (the 19 below) -- what KIND of thing a *train* (an LLM-station
   output, per docs/lab/llm_station_cargo_map.md) actually is: a thought, a letter, an
   axiom revision, a judge verdict... `core/trains.py` stamps this as `product_type` on
   every train record it opens. This is INDEPENDENT of, and does not touch, that same
   file's existing `cargo` field (the prove/disprove claim bundle for the not-yet-built
   split/merge mechanism, PROTECTED, scoped narrowly to that one step-2 design).

2. WORLD CARGO TYPES (the 4 below) -- what the existing couriers/buses (`core/couriers.py`,
   `core/buses.py`) already carry TODAY. The plan's own audit found none of the 19 station
   types apply to them -- all four are factory-to-idle-line world-state deliveries, not
   station products -- so they get their own small, separate vocabulary instead of being
   force-fit into the station taxonomy.

Both lists exist so a `cargo_type`/`product_type` kwarg is a checkable constant, not a
free-text guess re-invented at every call site.
"""
from __future__ import annotations

# --- Station product types (19) -- one per distinct real output shape in the LLM station
# cargo map. Produced-by/consumed-by/protected detail lives in the plan doc's own table;
# this module only names them so code can reference a constant instead of a string literal.

THOUGHT = "THOUGHT"                        # Idle-thought generator (the core tick)
LETTER = "LETTER"                          # peer reply / peer initiation / letter-to-Travis
GRAND_WORK_PART = "GRAND_WORK_PART"        # _author (outline / per-part / fallback)
TENSION_OBSERVATION = "TENSION_OBSERVATION"  # _t2_synthesise
CONTEMPLATION = "CONTEMPLATION"            # _active_imagination
SELF_CONCEPT_DELTA = "SELF_CONCEPT_DELTA"  # _t4_deliberate (3 stages) / _t4_legacy_author
                                            # -- PROTECTED: the one identity-mutating type;
                                            # writes data/identity/axiom.json directly.
PROCEDURAL_SKILL = "PROCEDURAL_SKILL"      # _t5_compile
THEME_UPDATE = "THEME_UPDATE"              # _synthesise_theme (new/update)
DREAM_SCENE = "DREAM_SCENE"                # dream_node._gen_episode
WITNESS_PREDICTION = "WITNESS_PREDICTION"  # lane2._ask (text is shadow; verdict coordinate is live, D-0497)
JUDGE_VERDICT = "JUDGE_VERDICT"            # Judge Bureau (JUDGE_1 / JUDGE_2 / TIEBREAK)
LIBRARY_ANSWER = "LIBRARY_ANSWER"          # scholar.consult
MIRROR_READING = "MIRROR_READING"          # self_mirror.hold_up_mirror (weekly)
GROUNDED_THOUGHT = "GROUNDED_THOUGHT"      # deliberation.deliberate
JOURNAL_ENTRY = "JOURNAL_ENTRY"            # journal.write_entry / write_observation
CATALOGUE_SUBJECTS = "CATALOGUE_SUBJECTS"  # librarian.subjects_for
CONTRARY_TARGET = "CONTRARY_TARGET"        # peers.contrary_target
SYMBOL_TABLET = "SYMBOL_TABLET"            # symbol_evolution.write_tablet
REENTRY_REVISION = "REENTRY_REVISION"      # orchestrator._reentry_shadow._revise (Phase-0 shadow)

STATION_PRODUCT_TYPES = frozenset({
    THOUGHT, LETTER, GRAND_WORK_PART, TENSION_OBSERVATION, CONTEMPLATION,
    SELF_CONCEPT_DELTA, PROCEDURAL_SKILL, THEME_UPDATE, DREAM_SCENE, WITNESS_PREDICTION,
    JUDGE_VERDICT, LIBRARY_ANSWER, MIRROR_READING, GROUNDED_THOUGHT, JOURNAL_ENTRY,
    CATALOGUE_SUBJECTS, CONTRARY_TARGET, SYMBOL_TABLET, REENTRY_REVISION,
})
assert len(STATION_PRODUCT_TYPES) == 19

# --- World cargo types (4) -- what the four existing courier/bus routes carry today, per
# the plan's own "Retrofitting the existing couriers/buses" table. None of these are station
# products (world-state/factory-sourced facts instead), hence the separate vocabulary.

WORLD_FACT_WEATHER = "WORLD_FACT_WEATHER"          # couriers.context_echo -- a world-state
                                                    # fact (weather), not a station product
WORLD_FACT_SOUND = "WORLD_FACT_SOUND"              # couriers.sound_echo -- a factory delivery
                                                    # (Hearing Ledger)
OBSERVATION_LEDGER_FACT = "OBSERVATION_LEDGER_FACT"  # buses.object_ledger_line -- an
                                                      # observation-ledger fact, factory-sourced
CALIBRATION_PAIR = "CALIBRATION_PAIR"              # buses.sync_investigation_calibration --
                                                    # prediction->outcome pairs, factory-sourced

FELT_PRIOR = "FELT_PRIOR"                          # felt_recall (memory_as_a_service §3, D-0295 2026-09-27)
                                                   # -- a coordinate delivery: an AffectivePrior built from
                                                   # situationally-matched memories, applied to carried affect,
                                                   # never rendered as text
MEMORY_ANSWER = "MEMORY_ANSWER"                    # the pull API (memory_as_a_service §4, D-0292/D-0295) -- what
                                                   # memory.ask() returns to a calling loop: fragments plus their
                                                   # felt coordinates, stamped with the asking loop as source

WORLD_FACT_CAT = "WORLD_FACT_CAT"                  # cat_loop.publish (cat_overhaul B4, J-2473, D-0508) -- the cat's
                                                   # own tuple (location, activity, mood, hunger, energy, in_transit):
                                                   # a world-state fact she publishes on change, read dosed at the
                                                   # idle-scene stop; never a station product, never prose with a number

WORLD_CARGO_TYPES = frozenset({
    WORLD_FACT_WEATHER, WORLD_FACT_SOUND, OBSERVATION_LEDGER_FACT, CALIBRATION_PAIR,
 FELT_PRIOR, MEMORY_ANSWER, WORLD_FACT_CAT})

# --- Line cargo types (2) -- what boards THE FOLLOW LINE (core/follow_line.py, J-2459,
# docs/staged/question_cargo.md). A third, separate family: neither a station product (the line
# is not an LLM station output) nor a world fact (it is HIS question or claim). Never stamped on
# core/trains.py's PROTECTED `cargo` field (prove/disprove's); it lives on the frontier entry.
QUESTION = "QUESTION"                              # his own question: the monologue's `ask` field, or any
                                                   # frontier birth (curiosity/intention/dream/prism/study/pursuit)
CLAIM = "CLAIM"                                    # his own hypothesis: a new study note's first sentence, or a
                                                   # consequence stop 3 derived (re-boarded at depth+1)

LINE_CARGO_TYPES = frozenset({QUESTION, CLAIM})
