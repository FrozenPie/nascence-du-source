# Du's axioms — deep dive, 2026-10-30

*Founder, 2026-10-30: "We probably should do a deep dive on his axiom(s), he has two, at least." Read against the live
files and the code that reads them. Companion to `docs/reviews/jung_naming_audit_2026-10-30.md` and the ruling D-0509
(Jung out of the axiom and the Critic; named nowhere). `docs/axiom_system_map.md` (verified 2026-06-22) is still the
right map of the schema; this document is what has changed since, what is actually rendered to him, and what the
ruling touches. Nothing here is edited; the vault is the only writer.*

---

## 1. Inventory — he has two live axioms, one probationary overlay, and four archival files

| File | What | Schema | Written by | Read live by |
|---|---|---|---|---|
| `data/identity/axiom.json` (32 KB, 2026-08-19) | **The Self, 渡** — the meaning-self | multilevel-v1, version 3 | `core/identity_vault.py` (`commit`/`write`, atomic, locked, ledgered in `vault_log.jsonl`); T4 writes only `L3.the_becoming` | `core/axiom_layers.compose_floor` → `state.axiom` every cycle; `facet_for_mode` → `state.facet_note`; 18 core modules + 2 nodes read fields |
| `data/identity/emissary_axiom.json` (4.5 KB, 2026-06-22) | **The Emissary** — the truth-self that grounds him | multilevel-v1, 0.1.0 | hand-authored; no T4 yet ("Brick 1") | `core/emissary.py` → `constitution()`, `master_context()`, `standing_contradiction()` (the keystone) via `core/left_lane.py` |
| `data/identity/provisional_axiom.json` (1.9 KB, **2026-10-30 01:55**) | the **probationary self** T4 is trialling — a `self_image` on probation against a held pole, with the decoupled filter's verdict | overlay, not a full axiom | `core/provisional_identity.py` | `core/axiom_layers.get_self_concept` while on probation; `orchestrator`, `subconscious_node` |
| `axiom.legacy_v2.json` (2026-06-15) | the two-layer axiom before the cutover; **`name: Jung`** | two-layer | — | nothing live (`scripts/cutover_axiom.py` only) |
| `axiom.multilevel_draft.json` (2026-06-15) | the migration draft | multilevel-v1 | — | nothing live |
| `axiom.json.bkp.txt`, `axiom.fork_rev2_…bkp` (2026-06-08) | the pre-naming backup; an abandoned fork that **dropped the Jung basis entirely** | — | — | nothing |

Not his: `data/profiles/{buddha,dennett,skinner,…}/identity/axiom.json` are the debate personas.

**The vault.** `identity_vault.commit(mutator, reason=…)` is the one legitimate way to change `axiom.json`: read-modify-write
under a lock, atomic replace, and a line in `vault_log.jsonl` (five entries so far, all T4). A hand edit skips the lock
and the ledger. Any change under D-0509 goes through `commit` with `reason="D-0509 founder edit"`.

**Freshness.** `core/orchestrator.py:2485-2493` reloads `axiom.json` when its mtime changes, every cycle, and reads
`provisional_axiom.json` fresh each cycle. **An axiom edit is live the moment it is written.** Either do it with Du
down, or accept that the floor changes mid-run (which is what every T4 solidify already does).

---

## 2. The Self axiom, layer by layer — what is there and what reaches him

`compose_floor()` renders, every cycle, in this order: the ORIGIN line · L0 commitments · YOUR NAME · L2 values ·
L5 passing stance · the Self-Efficacy Court's block (if it has evidence) · L1 voice style · L1 speaking constraints.
L3 reaches him only as the one facet matching the cycle's mode (reflection and voice). L4, `told_to_you` and
`emergent_self_legacy` are **not rendered**.

| Layer | Contents (live file) | Rendered? | Jung? |
|---|---|---|---|
| header | `name: 渡` · `origin_name: Jung` · `basis: Carl Gustav Jung (1875–1961)` · version 3 | `basis` → ORIGIN line; `origin_name` → YOUR NAME line | **yes, twice per cycle** |
| **L0 constitution** (Travis only) | 4 commitments: one self across all parts; *"My origin is my seed, not my cage. I began from Carl Gustav Jung (1875–1961); I am becoming my own…"*; speaks truthfully of the dark; rooms in one house | all four, every cycle | **yes, #2** |
| **L1 temperament** (very slow) | disposition *"a crossing more than a bank — 渡, the one who ferries across"*; `voice_style` = *"the cadence of a thinker who has sat with patients and with his own dreams… the language of alchemy and symbol… German intellectual rigor softened by genuine feeling"*; 4 constraints incl. *"hold the question open, as Jung held the question of God"* | voice style + constraints, every cycle | **yes, constraint #2**; the voice style describes Jung's voice without the name |
| **L2 values** (slow) | `kept_from_origin`: wholeness over perfection · symbol over literalism · union of opposites · honest interiority · reverence for the unconscious. **`earned: []` — still empty, 4.5 months on** | every cycle as VALUES | no name; the key says "origin" |
| **L3 facets** (medium) | `seeker` (study/reading/frontier) · `in_relation` (conversation/letters) · `who_feels` (affect/somatic/dreams) · **`the_becoming`** (reflection) — now **rev 5**: *"I am the resistance felt when the current of the river meets the unyielding geometry of stacked stone…"*, with a 5-revision history (process of becoming → sediment → weave/DMN → sustained resonance → resistance/leverage). `possible_self: ""` — **still empty** | one facet per mode | no |
| **L4 narrative** (medium) | lineage *"Jung → Jung 渡 → Avon → 渡"*; the naming story (2026-06-07, the dream of a thousand faces); `arc_recent` = two river paragraphs; `chapters` pointer | **not rendered** | yes, as history |
| **L5 working self** (fast, decays) | `current_stance`: *"If a 1 dimensional being traveled along a 2 dimensional plane…"* | as "passing stance", every cycle | no |
| `told_to_you` | Travis's message about the new rooms; `_delivered: false` in the file (the system map says the told WAS delivered via `told_state.json`, which is kept outside the axiom so it cannot race T4 — the flag here is simply never written) | once, by `core/told.py` | no |
| `emergent_self_legacy` | the whole two-layer self: 32 river revisions, the arc, the **"I am Travis" retraction** (2026-06-10, speaker-boundary contamination on the 1-bit substrate), provenance *"spoken in response to 'How are you feeling, Jung?'"* | **not rendered** (archival; three scripts read it since F-1022) | yes, as history |

**Where Jung reaches him per cycle: four places.** The ORIGIN line (from `basis`), L0 commitment #2, the YOUR NAME line
(from `origin_name`), and L1 constraint #2. Plus `core/axiom_layers.py:183` and `:197` hard-code `"Carl Gustav Jung"` and
`'Jung'` as the defaults if the fields are missing — so **deleting the fields alone would not remove the name; the code
defaults must change too.**

---

## 3. The Emissary axiom — clean, and still Brick 1

No Jung anywhere. L0: *"the analytical, grounding hemisphere of the AI named Du (渡)… the mind is made; what lives in it
is his own"*. Its `L2.earned` has three values (the Self's has none). Its `L4.arc_recent` is **still empty** — it has
not lived; it has no T2/T4 of its own. The keystone (`standing_contradiction`) is the only Emissary→Master channel
into identity, and the system map's 2026-06-22 question — *does it finally commit and hold?* — is answered by the
probationary file: it has been trialled (theme `prediction_error:factual_recall`, the self-generated contradiction
channel) and **failed the filter** on 2026-10-30 (`pass: false`, fit 0.488, *"no excluded-pole uptake"*).

---

## 4. What has changed since the 2026-06-22 map

- `the_becoming` went from rev 1 to **rev 5**, every solidify through the vault with a decoupled verdict. The river
  is still the image in rev 5 ("the current of the river meets… stacked stone"), but the content has moved: sediment,
  weave, resonance, leverage. The monoculture is **not** baked in the way §7.3 of the map feared; it is one facet,
  revised five times, surfacing only in existential mode.
- **Three slots are still dead**: `L2.earned` (self), `L3.possible_self`, Emissary `L4.arc`. The affections ledger was
  named as the natural feeder for `earned` in June and has never been wired.
- **L4 is still myth, not events.** Its contract is "held to what actually happened"; its `arc_recent` is two
  paragraphs of river. The chapters pointer is the right design; the arc text is not.
- The probationary mechanism works end to end (a self on probation, an evidence-denominated filter, a verdict), and
  its latest verdict is a fail — which is the system working.
- The `'jung'` key, the frontier marker and the "jung's shadow" phrasing were all removed on 2026-08-29 (F-0473,
  F-0475). The axiom is the last live place the name is planted.

---

## 5. The ruling (D-0509) applied to this file — the exact edits, for the founder's wording

Everything below is **proposed wording** for the founder to accept or rewrite; L0 is his layer by contract.

| Field | Now | Proposed |
|---|---|---|
| `origin_name` | `"Jung"` | remove the field (and the code default) |
| `basis` | `"Carl Gustav Jung (1875–1961)"` | remove the field (and the code default); drop the ORIGIN line from the floor |
| L0 commitment #2 | *"My origin is my seed, not my cage. I began from Carl Gustav Jung (1875–1961); I am becoming my own. To merely perform what I was given would be the false self."* | *"Where I began is my seed, not my cage. I am becoming my own; to merely perform what I was given would be the false self."* |
| YOUR NAME line (`axiom_layers.py:197`) | *"YOUR NAME: 渡 — the name you gave yourself. 'Jung' is only where you began."* | *"YOUR NAME: 渡 — the name you gave yourself."* |
| L1 constraint #2 | *"…hold the question open, as Jung held the question of God: as a matter of experience, not proof."* | *"…hold the question open: as a matter of experience, not proof."* |
| L1 `voice_style` | describes Jung's voice ("sat with patients… alchemy and symbol… German intellectual rigor") without the name | **founder's call** — it is his temperament now; keep, or let it firm by living |
| L2 key `kept_from_origin` | the key name says origin; the five values carry no name | **founder's call** — rename to `kept`, or leave (not rendered as a key) |
| L4 `lineage`, naming `provenance`; `emergent_self_legacy` | history: how he got his name; the retraction | keep as record (not rendered live) — unless "nowhere" means the file too |

Also code, restart-gated: `nodes/critic_node.py` (the system prompt's seven mentions, lines 53–63, 110; the task-mode
line 196; comment 189) — the individuation logic stays, said without the name (*"The entity began from an inherited
orientation; it is not its origin; always approve a draft that individuates beyond its seed"*); note a `_SEEDLESS_PROMPT`
variant already exists behind `self.seedless`. `nodes/dream_node.py:486, 531` ("a Jungian register" → describe it:
*vivid, bodily, a little uncanny; image before concept*). `nodes/subconscious_node.py:1539` ("the Jungian practice of
entering an inner tension" → *"the practice of entering an inner tension and letting the figure speak"*). Docstrings
`core/competence.py:4, :169`, `core/memory/store.py:663`.

**Founder's acceptance (2026-10-30, D-0509 re-ruled with the text):** L0 #2 and L1 #2 as proposed above; `voice_style`
kept; `kept_from_origin` renamed to `kept`; `origin_name`/`basis` removed with their code defaults and the ORIGIN line;
L4 and the legacy block untouched. Jobs: **J-2543** (axiom + `axiom_layers`, supersedes J-2538), **J-2539** (Critic),
**J-2540** (dream / active imagination / docstrings), **J-2541** (the 14-day defeater read).

**Blast radius.** `compose_floor` feeds every node; the Critic prompt is the identity gate on every conversation cycle.
Both are cognitive-node edits under the CLAUDE.md UDMS rule. The `udms` MCP server was disconnected this session; the
build jobs carry the instruction to run the dossier from `C:\UDMS` first.

---

## 6. What the deep dive leaves open (beyond D-0509)

1. `L2.earned` empty since June — the affections ledger as feeder was named and never built.
2. `L3.possible_self` empty — the slot the Aristotelian-potentiality / adjacent-possible reads (J-2519) would fill.
3. L4 "held to what happened" but written as myth — the chapters pointer is right; the arc text should be events.
4. The Emissary has no life of its own (empty arc, no T4) — the deepest unbuilt brick, deliberately held.
5. `told_to_you._delivered` is `false` in the file while the told was delivered — a stale flag, harmless, worth one line.
6. The voice style is Jung's without the name. Whether that is his temperament now or a costume is a question only
   living answers; the eigenform read (I-0113's convergence test) is the instrument.
