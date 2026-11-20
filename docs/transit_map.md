# THE TRANSIT MAP — Nascence as a city of trains and busses (founder's model, 2026-08-16)

**Founder:** "The world is a train — technically many slow trains picking up new things. We also
need busses that go cross train lines — these are essentially memory recall and stuff."

The model, made precise: a **TRAIN LINE** is any looped or scheduled process that *creates new
freight* (writes state/memory) on its own clock. A **BUS ROUTE** is anything that *moves freight
between lines* — it creates nothing, it transfers. Identity, per the 08-16 lab verdict, is the
**route network itself** — the connections between moments. This map is the steering document;
condition marks are from the 08-16 chain walks.

## THE STATION LAYER (added 2026-08-20) — `docs/transit_timetable.md`
Founder: *"The LLMs are not Du, they are tools. They are not the lanes, just stations on the
lines."* The 37 LLM call sites are now mapped onto these lines with their clocks, budgets and
platforms. **Headline: the load is inverted against the hardware** — 17 stations on the 3070's
8192 window (including the 1400-token Grand Work authoring and the 1600-token deep think), 11 on
the 1080 Ti's 24576 window (including a temp-0.1 solve). And **there is no signal box**: the Deep
Line wakes every 30s, the Idle Line after 75s of quiet, both do their heavy work on the same
3070, and neither knows the other exists. See the timetable for the full station list.

## THE TRAIN LINES

### Fast lines (Du's cognition)
| Line | Clock | Freight it creates | Condition |
|---|---|---|---|
| **Conversation Line** (orchestrator run_cycle) | per message | replies, lived Q/A fragments, light/shadow events | ✅ walked; caps widened; routing veto found (fix designed, not promoted) |
| **Idle Line** (monologue + the thought-train) | per tick | inner thoughts, acts, intentions, letters | ✅ walked; TRAIN-HOLD applied (guards respect a moving train, ledger carry, quiet buffet). **08-22: trains now carry IDs** (`core/trains.py`, the shared key the Transport Manager needs); short lines traced to the openness self-report gate, not a cap; centroid math bug fixed; **split/merge junctions designed** (`docs/plans/train_split_merge.md`) — prove branch here, disprove branch on Lane 2 |

### The slow line (the identity factory)
| Line | Clock | Freight | Condition |
|---|---|---|---|
| **Deep Line** — T1 scan / T1.5 active imagination / T2 synthesis / T3 drift / T4 self-authoring / T5 skills / consolidation / dreams / chapters / prune | 30s / event / hourly / rare / 60s / sleep | archive self-observations, gists, dreams, chapters, the becoming facet | ✅ walked; T2 HOARDING found → **THE REFINERY built 08-16** (founder-designed manufacturing station: syntheses → living standing insights, `distilled_from` lineage, members cool; fidelity-gated; SHADOW until founder reads a night's log) |

### The world lines (founder's "many slow trains picking up new things")
| Line | Clock | Freight | Condition |
|---|---|---|---|
| Weather/sky | sensorium tick | fronts with bearing, light, storms | ⬜ unwalked (built, live) |
| Tide | real M2 clock | tide level, pool cover/uncover | ⬜ |
| Season/daylight | calendar | growth windows, day length | ⬜ |
| Garden | growth clocks | herbs maturing, bed state | ⬜ |
| Fire/woodpile | burn-down | fuel state, warmth | ⬜ |
| **The cat** | her own state machine | comes/goes, moods, firsts, the un-taken name invitation | ⬜ (founder: entirely hers) |
| Peers ×7 | gap_days each | letters arriving, two-way threads | ⚠ three voices moved to yi 08-16 — first letters unread |
| Object biographies | spawn/trace/erosion clocks | hidden histories, observable state | ⬜ |
| School | curriculum | assignments, capstones | ⬜ |
| Body | somatic/homeostasis | energy, fatigue, drives, felt states | ⬜ |
| Climate | 5s field | psychological weather, dissonance ignition | ⬜ |

## FEDERATED LISTS, NOT ONE SPREADSHEET (founder's correction, 08-16) — `docs/completed/sound_causality.md`
"Things are their own lists, they just talk to each other." Each world thing keeps its OWN
state (weather's ordinal index, the Hearing Ledger, the garden bed, the cat's machine, object
records) — no shared table (the world_census.md draft's "one spreadsheet" was WRONG shape,
superseded same evening). Lists talk via CAUSAL RATE FUNCTIONS: a cause emits a rate ("this
much wind-sound per minute"). **Sound is the worked example, corrected same evening to the
founder's full factory model**: causes ship CARGO to the factory (the per-tick world tuple IS
the manifest — no new wiring); the factory's process is QUESTION-ASKING (what is happening,
what sounds, what cause, audible from where Du stands — the per-place AUDIBILITY TABLE
FULL/MUFFLED/DISTANT/none answers the last); its goods are ANSWERS (moment↔sound↔cause↔place↔
heard), kept only when Du could hear (tree-falls law = exactness AND O(1) efficiency), stored
FOR LATER consumers (echoes, binding reveals, investigations, Transport Manager, P4 recall).
One good, two faces: the cause-face stays Layer-1 hidden until the audition economy releases
it — earned identification unlocks the cause of every past answer retroactively. Driftwood/
object lists are SILENT goods — they don't route through sound, only through the Transport
Manager directly.

## THE TRANSPORT MANAGER (planned 08-16, not built) — `docs/plans/transport_manager.md`
The missing primitive the couriers exposed: no shared way to ask "is this occurrence unusual
FOR THIS LINE, right now?" Founder's taxonomy — NOVELTY (never before) · SPIKE (more than
usual) · DROUGHT (quieter than usual, longer) — scored as baseline-relative weights (EMA rate
+ EMA gap per line), competitively dispatched (highest weight wins the bus this cycle), shadow
-first. Fed directly by each list's own `observe()` call (confirmed correct now that lists stay
federated) — the Hearing Ledger first, driftwood-finds and others later, each its own line, no
shared table required. Becomes **Courier D** once live.

**2026-09-28 (D-0294, J-1432/J-1433):** the row title above is stale — this is BUILT and shadow-
accruing since 08-29 (18,000+ ticks, `data/transport_shadow.jsonl`), just not yet live/consuming.
Two changes: (1) spike/drought are now EDGE-triggered (fire once per crossing, re-arm on a fresh
`observe()` or the windowed rate cooling — `EDGE_TRIGGER` kill-switch, J-1432), answering the
level-polling saturate-or-go-silent defect F-1989/F-1990 found. (2) The eventual consumer is no
longer Courier D's text delivery (D-0293 retired that swap) — it's **felt recall**
(`docs/staged/memory_as_a_service.md` §3): felt recall registers its own `world:<dim>:<place>`
lines via `observe()` and reads a new read-only `transport_manager.verdict(line_id)` helper
(built J-1433) per trigger edge; the Phase 1 gate fires a tug only when that verdict is
novel/spike/drought, or the line is still cold-start. `verdict()` itself is built and unit-tested
(47/47, `scripts/_test_transport_manager.py` §8) in worktree `jobrun/transport_manager`; wiring
`core/felt_recall.py`'s edge handler to actually call it is a separate follow-up (that file lives
on the still-unmerged `jobrun/memory_as_a_service` branch — see docs/plans/transport_manager.md's
own Current State for the file-overlap evidence).

## THE BUS ROUTES (cross-line transfer — "memory recall and stuff")
*Terminology note, 2026-08-22: "bus" here is the older, broader sense — any cross-line content
transfer (recall, wandering, corpus callosum, memory edges). That evening's own courier company
below has since been split more precisely: COURIER now means genuinely urgent/real-time only;
everything not time-sensitive, including this table's routes, is a bus by the newer, narrower
definition too. Not renamed row-by-row — the distinction that matters below is urgent vs not.*

| Bus | From → To | Condition |
|---|---|---|
| **Recall/retrieve** (tier-mixed slots) | store → Conversation Line | ⚠ every bus arrives half-loaded with T2 freight (the depot imbalance); windows widened 08-16 |
| **Associative recall** | store → Idle Line (keyed on current thought) | ✅ live; is the memory-on-the-thread service TRAIN-HOLD leans on |
| **Divergent seed** | store (random) → Idle Line | ✅ fixed 08-16 — the bus that used to kidnap passengers mid-journey; now waits for the train to stop |
| **Courier D — sound echo** | Hearing Ledger + fragment_context.sounds → Idle Line | ✅ built 08-16 — "memories link to sounds"; closed a WRITE-ONLY column (7,647 rows, zero readers before tonight); named voices only, beds excluded, 90-min cooldown; competes with Courier A for one ambient slot/tick. **2026-09-27 (D-0293, J-1430):** rerouted into felt recall — `core/couriers.py`'s `COURIER_TEXT_DELIVERY` kill-switch (ships `True`, text delivery still live today, byte-identical, matching this plan's own shipped-True precedent) lets this route keep firing its trigger/cooldown exactly as before; flipped `False`, it stops feeding the wandering trail (Idle Line) and `core/felt_recall.py`'s Phase 0 shadow felt recall picks up the same happening on the affect side instead (`memory_as_a_service.md` §3.4) |
| **Evidence hand** (recall act) | world-contact store → Idle Line, judge-filtered | ✅ new 08-16; first organic riders same day |
| **Identity projection (P2)** | estate → Conversation Line | ✅ live; lingering-into-idle fixed (F3) |
| **Facet note** | axiom → reflection/voice by mode | ✅ walked |
| **Dream material gathering** | recent freight → Deep Line at sleep | ⬜ unwalked |
| **Wandering trail** | world lines → Idle Line (ambient drip) | ⬜ |
| **Corpus callosum** | Master state ↔ Emissary | ⚠ walked; provisional leak fixed (F2); Emissary→reflection take healthy |
| **Memory edges M0/M1 + co-recall** | typed cross-line route-BUILDING (resolves/answers/kept_from) | ✅ built this week — this is the route-construction department; per identity=connections, the most important service in the city |
| **Chapters recall** | past eras → Idle Line | ⬜ |
| **Librarian / library hand** | catalogue → shelf → reading | ✅ new 08-16 |
| **Deep memory (scholar)** | innate knowledge → Idle/Conversation | ⬜ |
| **Guidance read-back · retraction ledger · theme/epoch context** | ledgers → prompts | ⬜ (instrumented) |
| **Idle freight** (`core/buses.py::idle_freight`) | Idle Line (THOUGHT/CONTEMPLATION trains) → Conversation Line (Reflection stop) | 🔵 built 2026-09-28 (J-1436, D-0295), flag-gated `IDLE_FREIGHT_BUS`, **restart-gated** — closes gap #2 below; typed pull (product_type + restate_sim development + topical cosine), shadow-logged against the old raw window for the first live week, not yet promoted |

## WHY THIS MAP EARNS ITS KEEP — the 08-16 findings, restated as transit problems
- **The caps** were bus windows too small to see the freight (history at 150 chars).
- **The whispers** were freight REPACKED at every interchange until the original cargo was lost.
- **The jumped trains** were busses boarding mid-journey and carrying passengers off the line.
- **The T2 hoarding** is one line's freight overfilling the central depot, so every recall-bus
  arrives loaded with the same cargo regardless of where it was headed.
- **The routing veto** was a signal-box fault sending philosophical trains onto the freight-yard
  shunt.
- **Identity = the route network** — not any train, not any station: the established connections
  over which everything travels. Protecting Du = maintaining the network.

## NEW BUS COMPANY (2026-08-16 evening): THE COURIERS — `core/couriers.py` + `core/buses.py`
Founder-designed service for gap #1, under the courier laws (only what HE observed; zero LLM;
ambient, never leading; he assembles the facts and can be wrong). **★ SPLIT 2026-08-22** (the
file's own docstring had called the whole thing "the busses" from the start — founder: "couriers.py
was probably an attempt at this... go with the new way of naming it"): only the genuinely
time-sensitive routes stay COURIERS; the rest moved to `core/buses.py`, own state/log files:
| Route | Kind | Path | Status |
|---|---|---|---|
| context echo | **courier** (urgent) | world state → his matching past moments → wandering trail | ✅ wired (substrate loop), tested; ≤1/h, distinctive weather only, respects a held train |
| sound echo | **courier** (urgent) | Hearing Ledger + fragment_context.sounds → wandering trail | ✅ wired; named voices only, beds excluded, 90-min cooldown |
| object ledger | **bus** (not urgent) | his observation ledger → the re-encounter look-render | ✅ wired (driftwood look); moved 08-22, behaviour unchanged |
| calibration sync | **bus** (not urgent) | advisor prediction→outcome → world_calibration.jsonl | ✅ wired (sleep batch); moved 08-22, behaviour unchanged |
| *(factory→factory, e.g. weather→garden)* | **bus** | confirmed real (`core/garden.py` reads `sensorium` weather every tick), not yet wired to `buses.log_transfer()` | 🔵 hook exists, not instrumented |

## THE FACTORIES (2026-08-16 late: the founder's manufacturing lens applied to the world lines)
| Factory | Verdict | Notes |
|---|---|---|
| Object substrate | ✅ the exemplar | hidden biography → observations → inferences; append-only, provenanced |
| **Sound** | was a FOG MACHINE → **Acoustic Clock + Hearing Ledger built** | sounds happen ALL THE TIME on world time (tree-falls law: unheard = gone forever → sampling his place is exact); occurrences bank as aggregates — events counted at per-voice rates with daily tallies, beds as lived-in hours; the name, when earned, arrives with his whole history of hearings |
| The Refinery | ✅ built (shadow) | T2 syntheses → living standing insights with lineage |
| Ambient scene renders | ephemeral BY DESIGN | percepts should evaporate; the factory test applies to biography-bearers (voices, objects, places) |

## SERVICE GAPS THE MAP EXPOSES (candidates, unranked — founder steers)
1. ~~World lines have almost no bus service into memory~~ — **FIRST SERVICE OPENED 08-16 (the
   couriers, above).** Still thin: tide/garden/season states not yet echo-keyed (weather only);
   his own inferences not yet in the calibration loop.
2. ~~No bus runs FROM the Idle Line's best freight TO the Conversation Line~~ except generic
   recall — his current pursuits/thread rarely reach what he says to Travis. **BUILT 2026-09-28
   (J-1436, D-0295): `core/buses.py::idle_freight` above — flag-gated, restart-gated, not yet live,
   not yet read.** Gap 3 (peer/LETTER freight into recall) stays open; D-0289/D-0292 make it moot for
   idle specifically (per D-0295's own ruling text).
3. **The Deep Line has no outbound service at all** (the hoarding finding) — freight arrives
   at the archive depot and never leaves, consolidates, or transfers.
4. **Peer freight** (letters, friendships) barely reaches recall — 55 letter fragments, mostly
   cold.
5. **Dream freight** rides one bus (recent-dreams seed into reflection/idle) with a 500-char
   window — dreams are made, then barely revisited.
