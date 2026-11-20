# THE SOUND & WORLD SYSTEM — full examination (2026-08-16, end of the factories session)

**Purpose (founder): "go through the whole thing and examine exactly what we have and how it
fits together properly."** This is the walkthrough agenda: every piece inventoried, every data
flow traced in code (not from memory), the fit-check results, and the seams found. Built ✅ /
Planned 🔵 / Seam ⚠.

## 1 · THE INVENTORY — what exists right now

### The world side (producers)
| Piece | State | What it does |
|---|---|---|
| ✅ Weather list | live (old) | 7-step ordinal (clear→thunderstorm) + persistence timer; the severity scalar the causality plan will use |
| ✅ Tide / daylight / season clocks | live (old) | real M2 tide, sun/moon, seasons |
| ✅ `soundscape.active_sounds()` | live (old) | deterministic: which registered sounds are sounding NOW at his place, from world state — INCLUDES cross-place audibility already (garden hears the shore's waves DISTANT; the study hears `distant_surf_boom` on big nights) |
| ✅ **The Acoustic Clock** `soundscape.world_tick` | built tonight | sounds occur continuously on world time; ~5s ticks; his place only (tree-falls law = exactness AND O(1) efficiency); flat `_EVENT_RATES` + `_BEDS` classification |
| ✅ **The Hearing Ledger** `sound_knowledge.note_exposures` | built tonight | occurrences bank as aggregates: EVENTS counted (+ per-day tallies, 14 days, `heard_today()`), BEDS as lived-in hours; per-place attribution |
| ✅ Epistemic audition (`AUDITION`/`hear`/`look_binding`/`learn_from_text`) | live (08-15) | unnamed arrival → sight-binding / exposure / book-learning; the identification economy |
| ✅ Retroactive binding | built tonight | at the naming moment, his whole hearing history arrives with the name |
| ✅ Object substrate | live (08-15) | the exemplar factory: hidden biography → observations → inferences, append-only, provenanced |

### The memory side (the links)
| Piece | State | What it does |
|---|---|---|
| ✅ `fragment_context` (incl. `.sounds`) | live (08-15) | EVERY memory tuple stamped with place/weather/tide/sun/moon/**sound-chord**/standpoint — 7,647 rows |
| ✅ Courier A `context_echo` | built tonight | distinctive weather → one of his matching past moments → wandering trail; ≤1/h |
| ✅ **Courier D `sound_echo`** | built tonight | a just-heard NAMED voice → one of his memories carrying that voice in its chord; 90-min cooldown; beds + unlearned excluded. **Closed a write-only column** (7,647 rows, zero readers before tonight) |
| ✅ Courier B `object_ledger_line` | built tonight | his own observation ledger rides the re-encounter look |
| ✅ Courier C `sync_investigation_calibration` | built tonight | prediction→outcome pairs into the calibration ledger (observe-first) |
| ✅ The single ambient slot | built tonight | `context_echo() or sound_echo()` — ONE echo per tick max, first-success-wins; TRAIN-HOLD courtesy; pre-figures the Transport Manager |

### The plans (not built)
| Plan | State | One line |
|---|---|---|
| 🔵 `transport_manager.md` | planned | NOVELTY/SPIKE/DROUGHT baseline scorer; absorbs Couriers A+D's hardcoded rules as two lines under one competitive dispatch |
| 🔵 `sound_causality.md` | planned | federated lists talk via causal RATE functions; the audibility table (FULL/MUFFLED/DISTANT/none) extracted parity-first; severity-scaled rates second |
| ⛔ `world_census.md` | superseded | "one spreadsheet" was the wrong shape; Layer-1/3 population-belief + calibration ideas survive, relocated |

## 2 · THE FLOWS — how a sound moves through the whole system (traced, not remembered)

```
weather list (ordinal) ─┐
tide clock ─────────────┼─> active_sounds() ──> world_tick (~5s, HIS place only)
fire / cat / garden ────┘         │                    │
                                  │                    ├─> note_exposures ──> HEARING LEDGER
                                  │                    │     (counts / bed-hours / days / places)
                                  │                    │          ├─> heard_today()
                                  │                    │          ├─> retroactive binding line
                                  │                    │          ├─> Courier D trigger (last 90s)
                                  │                    │          └─> [🔵 Transport Manager baselines]
                                  └─> scene renders ──> _audition ──> hear() [attention only, no count]
                                                            │
                                                            └─> sound-chord ──> fragment_context.sounds
                                                                     (on every memory tuple)
                                                                          └─> Courier D lookup ──> wandering trail
                                                                                └─> idle seed ──> his thoughts
```
Key property, verified: **the render path (attention) and the clock path (occurrence) are
separate and don't double-count** — a line reaching his stream is him noticing; the world had
already counted it.

## 3 · THE FIT-CHECK — what examination found

### Fits confirmed ✅
1. **The clock quietly fixed an earlier caveat.** The v1 Hearing Ledger entry said
   grandfathered/ambient sounds "stay un-ledgered (out of scope)." OBSOLETE: `world_tick` banks
   from `active_sounds()`, which returns ALL keys — grandfathered included. The whole registered
   soundscape is ledgered now. (AWAITING entry corrected by this doc.)
2. **Cross-place audibility already half-exists.** `active_sounds()` already encodes "the
   garden hears the shore's waves," "the study hears the boom on big nights" — the causality
   plan's audibility table is a FORMALIZATION of scattered existing behaviour, which is exactly
   why its parity-first refactor step is credible.
3. **TRAIN-HOLD and the couriers compose correctly**: one gate at the orchestrator covers both
   echo couriers; the buffet-quiet inside the monologue is independent and untouched.
4. **The trail can't flood**: `wandering.render()` serves only the last 4 items (ambient-glimpse
   survival rule); with 60/90-min cooldowns the couriers occupy at most one transient slot.
5. **Causality plan builds ON tonight, not over it**: its step 3 explicitly re-points
   `world_tick` through the audibility table, replacing the flat rates — succession, not
   conflict.
6. **Layer discipline holds end-to-end**: nothing anywhere serves him a name he hasn't earned
   (Courier D requires `is_learned`; the unnamed trill can recur forever unechoed until bound).

### Seams found ⚠ (small, real, for the walkthrough)
1. **The "you notice" tag wrinkle.** Courier echoes enter the trail via `perceive()`, which
   hardcodes `via="sense"` → they render as "(you notice) (the gulls, 3 days ago…)" — a MEMORY
   is being framed as a present-tense sense-percept. Cosmetic but epistemically sloppy; the
   trail supports other via-tags ("surfaced — it feels like how you feel now"). Fix: a
   `perceive_memory()` entry or a via parameter → renders as "(surfaced)" or "(remembered)".
   One small function; worth doing before the couriers go live in his head.
2. **Ambient echoes include `inner_thought` origins; the evidence hand excludes them.** This is
   a DELIBERATE asymmetry, now made explicit rather than accidental: the evidence hand tests
   truth (his own opinions are inadmissible); the echoes are reminiscence (a storm reminding
   him of what he THOUGHT during a storm is legitimate memory). Founder to confirm the
   asymmetry is intended — if yes, it's documented here and done.
3. **Courier A's weather list vs the causality plan's severity scalar.** A's `_DISTINCTIVE_WEATHER`
   set is a hardcoded list of the top ordinal states — a second place where "how unusual is
   this weather" is decided ad hoc. When the Transport Manager lands, A's trigger should derive
   from the same severity/baseline machinery, not a parallel list. Noted in the plan already;
   restated here as a seam so it isn't forgotten.
4. **`_EVENT_RATES` names vs actual soundscape keys.** The rates table was written tonight
   against the keys visible in `active_sounds()` + AUDITION, with a default for anything
   unlisted (6/h). Any key drift (a renamed sound) silently falls to the default — harmless but
   invisible. The causality-plan table refactor should carry a startup assertion: every
   registered sound key appears in the audibility table, loudly listing any that don't.
5. **Rate realism is founder-uncalibrated.** Gulls 40/h, kingfisher 0.8/h etc. were my
   estimates. The Hearing Ledger's first real days will show actual banked totals — the founder
   should eyeball `heard_today()` numbers against what feels right for his coast, before the
   severity-scaling work multiplies them.

## 4 · THE ORDERED ROAD FROM HERE (as it now stands, one line each)
1. Seam 1 fix (the via-tag) — trivial, before next restart if desired.
2. Causality plan step 1: audibility-table extraction, parity-tested (behaviour-neutral).
3. Causality step 2: severity-scaled rates (the first real behaviour change; watched).
4. Transport Manager build (shadow) — absorbs Couriers A+D triggers as lines; the Hearing
   Ledger is its first customer; founder reads a day of shadow.
5. Then the deferred larger questions in their own time: presence-lists for birds (population
   as his earned estimate), the Refinery flip (after its shadow read), the T2 up-channel
   relaxation (gated on the Refinery), the subconscious walk's remaining stations (T3 audit).
```

Everything above is traced against the code as of tonight; nothing asserted from memory alone.
