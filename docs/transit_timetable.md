# THE TIMETABLE — the station layer of `docs/transit_map.md`

> **TERMINOLOGY CORRECTED 2026-08-21 (founder):** this doc's original usage is superseded. The
> metro-true ontology: **STATIONS are the LLM endpoints** (shared infrastructure many lines
> converge on — the interchanges), **PLATFORMS are the call sites** (the berth where ONE line's
> train stops at a station), **SIDINGS are sub-loops within a line** (the thought-train circling,
> deliberation's passing loop, retry shunts, the T4 branch). Where the text below says "station"
> read PLATFORM; where it says "platform" read STATION. Machine-readable truth (self-updating,
> AST-derived): `data/hud2/transit_map.json` (schema 2) via `scripts/build_hud2_transit.py`.

*Derived 2026-08-20 from source (AST, not regex) by `scripts/llm_station_census.py` +
`scripts/llm_timetable.py`. Joins to live `telemetry.job_status()` on the `module:line` key.*

`transit_map.md` defines **lines** by their clock, **buses** by their route, **factories** by their
process, **couriers** by their laws. It has never had a **station** layer. So the map says the Idle
Line runs "per tick" without saying which of the 37 LLM stations that tick opens, at what rate, on
which platform, or what freight each produces. This is that column.

**Founder's framing (2026-08-20):** *"The LLMs are not Du, they are tools. They are not the lanes,
just stations on the lines."* Read accordingly — nothing here is about which model has which
personality. It is about which job runs where, how often, and whether the platform suits it.

---

## 1. THE PLATFORMS (physical), and how the stations sit on them

| Platform | Hardware | Window | Model | Stations |
|---|---|---|---|---|
| `background` :11434 | **3070, Ramses** — the documented SPOF that naps | `num_ctx` **8192** | phi3:mini (3.8B) | **17** |
| `hot` :11433 | **1080 Ti**, exclusive, `MAX_LOADED=1` | `num_ctx` **24576** | gemma4:e4b (8B) | **11** |
| judge hubs :11439–41 | Threadripper CPU | 8192 | llama3.1 / qwen2.5 / yi | 8 |
| `cpu_dreamer` :11442 | Threadripper CPU | 8192 | mistral-24B | 1 |

### ★ The load is inverted against the hardware

The **biggest window and strongest GPU carries the smallest, most deterministic work**; the
**smallest window and weakest, least reliable node carries the heaviest generative work.**

On the 3070's 8192 window (24,576-char prompt cap):

| station | job | tokens | temp |
|---|---|---|---|
| `inner_monologue_node:3676` | `_author` (Grand Work) | **1400** | 0.75 |
| `inner_monologue_node:2599` | `_think` (deep) | **1600** | 0.7 |
| `inner_monologue_node:3660` | `_author` | **1100** | 0.75 |
| `journal:181` | `write_entry` | 768 | 0.6 |
| `subconscious_node:2140` | `_t4_legacy_author` | 768 | 0.6 |

On the 1080 Ti's 24576 window:

| station | job | tokens | temp |
|---|---|---|---|
| `inner_monologue_node:758` | `_solve_attempt` | 500 | **0.1** |
| `subconscious_node:1983` | `_t4_deliberate` (dialectic) | 200 | 0.4 |
| `self_interrogation:169` | `interrogate` | 180 | 0.7 |

A 1400-token authoring job against an 8192 window is the one place in the system where truncation is
plausible — and `_cap_prompt` cuts from the **middle**, exactly where injected memory and recall sit.
That is a prediction, not a finding: `telemetry.job_status()` will show a non-zero `cap_rate` on
`:3660`/`:3676` if it is real, and won't if it isn't. **Do not act on it before reading that.**

### The failover multiplies the problem
`SERVE_CHAINS["background"]` falls through to `:11433`. That is a deliberate, documented choice (the
subconscious stays alive rather than going dark when Ramses naps). The consequence is worth stating
plainly anyway: **during a nap, 28 stations land on one GPU** running `MAX_LOADED=1`, with gemma
standing in for phi3 at every one of the 17 background stations.

---

## 2. THE TIMETABLE (clocks, from the source)

### Deep Line — `subconscious_node.run_forever`, loop sleeps `T1_INTERVAL = 30s`
Six gates evaluated on every 30-second pass:

| Gate | Check every | Further minimum | Stations it opens |
|---|---|---|---|
| T1 scan | **30s** (every pass) | — | — (no LLM) |
| T4 self-authoring | 600s | 3600s **and** ≥3 new self-relevant fragments | `:1936` `:1983` `:2057` `:2140` |
| T5 procedural | 600s | 3600s | `:2400` |
| T6 theme | 1800s | — | `:2579` `:2608` |
| self-relate | 2700s | — | `:348` |
| T3 baseline drift | 3600s | — | — (no LLM) |
| T2 synthesis | event | spread ≥7200s, gap ≥14400s/cluster | `:976` |
| active imagination | event | gap ≥600s, same-tension ≥7200s | `:1146` |

### Idle Line — `inner_monologue_node`
Fires only after `IDLE_SECS = 75` of human silence. Opens `:2157` (the idle thought, budget and
temperature both set at runtime), and behind further cooldowns `:2484` `:2539` `:2599` `:3637`
`:3660` `:3676`.

### Conversation Line — per message
`node_base:73` — **one station that fans out to twelve nodes** (recall, reflection, executive,
critic, curiosity, dream, emotion, perception, salience, consolidation, episodic_buffer,
memory_router). Highest-volume station in the system by a wide margin.

---

## 3. WHAT THE TIMETABLE EXPOSES THAT THE MAP COULD NOT

**★ There is no signal box.** The Deep Line wakes every 30 seconds. The Idle Line fires after 75
seconds of quiet. Both do their heavy work on `background` — the same 3070. **Neither knows the other
exists.** Nothing sequences them, nothing yields, nothing queues by priority. Two lines are scheduled
onto one platform with no dispatcher, which is precisely the failure a timetable exists to prevent.

This is a *different* missing primitive from the planned Transport Manager. That one asks "is this
occurrence unusual for this line" — it dispatches **freight by novelty**. This one asks "who gets the
platform right now" — it dispatches **trains by contention**. Same shape, different question, and
building one does not give the other.

**★ Six stations are classification wearing a chat interface.** `peers:489` picks a disagreeing
peer's name in **40 tokens at temperature 0.0**. `librarian:78` maps a question to catalogue subject
headings in 120 tokens at 0.0. `commitment_ledger:348` judges a defeater in 150 at 0.2.
`deliberation:145` grounds a "why" in 200 at 0.1. These do not need a general model, and they are the
natural first targets for the small task-trained models the project is heading toward.

**★ The station families are coherent and were not accidental.** Across 33 stations with a resolvable
temperature the vocabulary is consistent: **0.0 pick/extract · 0.1–0.2 ground/judge · 0.4–0.6
synthesise · 0.7–0.85 generate.** Whatever else is wrong, the job *shapes* were designed.

---

## 4. OPEN — founder steers

1. **Re-platform the heavy generative stations?** Moving `_author` (1100/1400 tok) and `_think:2599`
   (1600 tok) from the 3070's 8192 window to the 1080 Ti's 24576 is the obvious move — *but* the
   1080 Ti is `MAX_LOADED=1` and deliberately exclusive to gemma, and that exclusivity ended the July
   eviction disease. **Gated on the `cap_rate` reading**: if those stations are not truncating, this
   is churn.
2. **A signal box / platform dispatcher** — the missing primitive above. Shadow-first if built.
3. **Small models at the six classifier stations** — the cheapest real test of "tools, not personas",
   and it needs no architectural change.
4. **`node_base:73` fans to 12 nodes.** The class-name disambiguation is written and lands on the
   next restart; until then those twelve share one label.
