# Fragment Carries the String — sound-fragment inventory + additive-field spec (staged, 2026-09-28)

**Status:** 🟢 LIVE since the 2026-09-28 restart (flag on; sec6 read done 2026-11-18, F-5078) — inventory complete (F-2091, verified); additive fields built + verified in isolation (J-1534, F-2139, commit 54c8e5d); `SOUND_STRING_FIELDS` flipped `True` (J-1614, F-2191, 2026-09-28) now that §4's gate is met (J-1574, F-2176); not yet live pending Du's restart (§6); no `/decide` needed
(no founder-level fork found; see §7). Promoted from idea **I-0081** ("the fragment carries the string",
raised 2026-09-27 from T-0070). **Parent plans:** [memory_as_a_service.md](memory_as_a_service.md) (the read
side: §3.2 felt-recall's match needs a coordinate to match on, not just a category), which is itself the
plan this job (J-1472) is filed under; [strings_and_sheets.md](strings_and_sheets.md) Object A (the write
side: where a sound's onset/peak/tail would actually come from). **Sibling idea:** I-0082 (the sound loop with
exemplar memory) — this doc's `sound_exemplar_id` field is the join point, not a rebuild of that idea.
**Ledger:** F-2091 (this job's inventory, verified) · code read in full: `core/soundscape.py`,
`core/memory/store.py`, `core/memory_levels.py`, `core/mood.py`.

```plan-state
stage: live
phase: LIVE since the 2026-09-28 restart: 8 sound-string columns populated on 489/489 sound fragments; sec6 read DONE 2026-11-18 (F-5078): coverage 100%, 24 distinct keys, onset=peak=tail degenerate, sound_felt_valence vs live mood r=-0.0005
verified: 2026-11-18
evidence_read: 2026-11-18
gate: sec6 read done. SOUND_COORD_MATCH in felt_recall.py stays False until the founder rules (J-4305)
next: Founder ruling on SOUND_COORD_MATCH (J-4305)
cluster: 6
```

## Current State — verified 2026-11-18

- **2026-11-18** (F-5078): J-4284 sec6 read run on live data (489 rows since the 2026-09-28 restart, not 30 days from a later restart): coverage 100% vs 89.2% bar PASS; 24 distinct sound_key vs 4 (rise from the 2026-10-29 cat/sound-world merge); onset=peak=tail 489/489, direction/exemplar NULL as specified; memory_fragments.valence/felt now populated 489/489; sound_felt_valence vs live mood r=-0.0005 (null, a finding about the _felt_shadow formula). Status line above predates this: the flag has been live since 09-28.
- **2026-09-28** (F-2191): J-1614 flipped SOUND_STRING_FIELDS True (sec4 gate met via J-1574 F-2176); re-verified in isolation 25 of 25 checks; live DB still has no sound-string columns, Du not yet restarted

- **2026-09-28** (F-2176): J-1574 designed, built and isolation-verified felt-recall sec3.2 coordinate-distance matching, SOUND_COORD_MATCH in core/felt_recall.py, commit f9683d9, F-2176 verified 37 of 37 checks; sec4 gate now satisfied, no decide needed, engineering-shape call precedented by D-0293.
- **2026-09-28** (F-2139): J-1579: ROADMAP.md, the Status line, and the memory file all said DESIGNED / nothing built, disagreeing with this plans plan-state block which already said built. Synced all three to BUILT, shadow flag off, matching J-1534 done per F-2139. plan-index no longer flags a mismatch here.

- **2026-09-28** (F-2091, J-1472): Inventory run (read-only, live `nascence.db`, mode=ro) found 425
  origin='sound' fragments total, only 4 distinct sound keys ever recorded (tui_song, morepork_call,
  cat_purr, fire_crackle), none carrying any Sound-Space coordinate anywhere in the schema (all 17 tables
  scanned). `_felt_shadow()` already computes a coordinate-derived felt prediction today but logs it
  orphaned (no fragment_id); 17 other origins already thread live mood into `store_fragment()`'s existing
  `valence=`/`felt=` params but `soundscape.percept()` does not. Sound fragments are structurally excluded
  from `memory_levels.py`'s gist-distillation pool (`_RAW_ORIGINS` has no `'sound'`), so the "do gists keep
  the anchors" question does not arise on the path that exists today. `strings_and_sheets.md`'s own Object A
  (the thing that would actually produce distinct onset/peak/tail values) is Phase 1, un-started — this
  doc's spec ships the field shape now, degenerate (onset=peak=tail) until Object A lands, real once it does,
  with zero further schema change either time. `udms_get_change_dossier` run on `core/memory/store.py` per
  this job's briefing (ELEVATED risk, 19 real dependents) — see §5 for how that shaped the write-site choice.
  No `/decide` opened: no founder-level values fork found, see §7.

### What we have
- A real inventory (F-2091, verified) of every sound-origin fragment that has ever been written.
- A field spec (§2), a write site (§3), a named reader with an explicit not-yet-ship gate (§4), the
  memory_levels answer (§5 — folded into inventory above), and a pre-registered read (§6).

### What we need
- J-1534 (spawned, `ready`) to actually build §3, verified in isolation before the flag ever goes live.

### What we're doing next
Nothing further from J-1472 itself — the doc and its build job (J-1534) are the deliverable. The next actor
is whoever picks up J-1534.

## 0. The one-sentence answer

Nothing a sound fragment carries today says what the sound *sounded like* — only that a key fired, in what
words, and (89% of the time) what the wider world looked like at that moment; the additive fields below let a
later reader ask "was this a bright, sudden, rough sound" instead of only "was this specifically a
`morepork_call`."

## 1. What already exists (verified 2026-09-28, F-2091, read-only)

| Piece | Where | State |
|---|---|---|
| The write path | `core.soundscape.percept()` → `core.memory.store.store_fragment(origin="sound", ...)` (`soundscape.py:1391-1463`, call at `1458-1460`) | LIVE, the only origin='sound' writer |
| The six axes | `_AXES = (brightness, energy, onset, periodicity, roughness, continuity)` (`soundscape.py:46`) | LIVE, but one static point per key, not a contour |
| Per-key coordinate | `_SOUNDS[key]["coords"]`, read via `coords(name)` (`soundscape.py:809-811`) | LIVE — hand-seeded, fixed, **not** onset/peak/tail (that is Object A, unbuilt) |
| The coordinate-derived felt prediction | `_felt_shadow(sound, kind)` (`soundscape.py:1351-1364`) — `would_valence`/`would_arousal` from `coords()` | LIVE but orphaned: logs to `data/soundscape_felt_shadow.jsonl` keyed by `ts`/`sound`/`kind`, **no `fragment_id`** |
| The live-mood felt state | `core.mood.current_valence()`/`current_felt()`/`current_arousal()` (`mood.py:121-141`) | LIVE, already threaded into 17 other `store_fragment()` call sites' `valence=`/`felt=` kwargs — **not** sound's |
| The store's own unused columns | `memory_fragments.valence REAL`, `.felt TEXT` | LIVE columns, 0/425 populated for origin='sound' |
| Per-fragment world tuple | `fragment_context` (21 cols): place/weather/fire/light_band/cat_at/**sounds** (JSON list of ALL active keys)/valence/arousal/… | LIVE, 379/425 (89.2%) coverage for sound fragments; `sounds` is categorical (key membership), never a number |
| The felt-recall matcher | `memory_as_a_service.md` §3.2 — `SELECT fragment_id, valence, arousal FROM fragment_context WHERE <trigger dim = current value> AND …` | SHADOW-BUILT (J-1424, `FELT_RECALL_LIVE=False`); matches on categorical dimension equality only — no coordinate field exists for it to do distance-matching on, for any origin |
| The gist-distillation gate | `memory_levels._RAW_ORIGINS` (`memory_levels.py:36-41`) | LIVE — `'sound'` is not a member; sound fragments never become gists via this path |
| Object A (the actual string shape) | `strings_and_sheets.md` §3.A — "each key in `_SOUNDS` gains three points … onset, peak, tail" | **UN-STARTED** (that plan's own Phase 1) |

**The population, concretely (F-2091):** 425 fragments, 2026-07-04 → 2026-09-27 (~85 days, ~5/day), 4 distinct
keys ever fired (tui_song 152, morepork_call 150, cat_purr 122, fire_crackle 1) against a `_SOUNDS` registry
of ~29 keys, 16 distinct prose lines total (heaviest repeat 61×). So today's answer to "what shape did this
sound have" is: none — only which of 4 keys, in which of a small number of rotating sentences.

## 2. The additive fields

All new columns land on **`fragment_context`**, not `memory_fragments` (§3 explains why), `ALTER TABLE …ADD
COLUMN` style, old rows NULL — the exact pattern already used for `wet`/`light_band`/`smells`/`held`/`tod`/
`season`/`daylight` (store.py's own "THERMAL / LIGHT / SMELL / PHASE channels: additive, old rows NULL"
comment, `store.py:706-712`). Populated **only** for origin='sound' rows; NULL for every other origin,
exactly like those channels are NULL wherever they don't apply.

| Field | Type | Value today | Value once Object A ships |
|---|---|---|---|
| `sound_key` | TEXT | `chosen` (e.g. `"morepork_call"`) — promoted out of `memory_fragments.keywords`'s free-text `"sound <key> <object>"` shape into a directly queryable column (this job's own inventory script needed a fragile `keywords.split()[1]` parse to get this; a real reader should not have to) | unchanged |
| `sound_onset` | TEXT (JSON, six axes) | `json.dumps(coords(chosen))` | the string's real onset point |
| `sound_peak` | TEXT (JSON, six axes) | `json.dumps(coords(chosen))` — **identical to onset**, the honest degenerate case | the string's real peak point |
| `sound_tail` | TEXT (JSON, six axes) | `json.dumps(coords(chosen))` — **identical to onset** | the string's real tail point |
| `sound_direction` | TEXT or NULL | `NULL` — nothing to derive a direction from while onset=peak=tail | derived (zero new computation) once onset≠tail: e.g. per-axis sign of `tail - onset`, or one word for the dominant swing ("rising"/"falling"/"steady") — **not** compass bearing (that is `propagate_historical_acoustic_event`'s azimuth, a different, spatial concept `percept()` never calls; see §2a) |
| `sound_felt_valence`, `sound_felt_arousal` | REAL | `_felt_shadow()`'s own `would_valence`/`would_arousal` (`soundscape.py:1357-1358`), **the same computation**, just also returned to the caller and threaded onto the row instead of only appended to the orphaned jsonl | unchanged — still coordinate-derived, still a prediction, not a measurement |
| `sound_exemplar_id` | TEXT or NULL | `NULL` — I-0082's exemplar codebook does not exist yet | once I-0082 ships, the id of the nearest exemplar in that sound key's codebook; this column is the reserved join point, not a redesign of I-0082 |

**Separately, no new column needed:** `soundscape.percept()`'s existing `store_fragment()` call should also gain
`valence=core.mood.current_valence(), felt=core.mood.current_felt()` — the already-existing, already-unused
`memory_fragments.valence`/`.felt` columns, and the exact convention 17 other origins already follow (§1).
This is **the live felt state at write time** — a different signal from `sound_felt_valence` above (the
sound's own coordinate-predicted nudge). Both are real, both already computed elsewhere in this codebase
today, carrying both costs nothing additional, and §6's pre-registered read can then ask a genuinely new
question: does a sound's *shape* predict what he actually felt, or not?

### 2a. Why not azimuth/compass direction

`core.soundscape.propagate_historical_acoustic_event()` (`soundscape.py:1468-1508`) does compute a real
compass bearing, but only for `core.cat_sounds`'s and `core.sensorium`'s spatial cat-sound events — it is
never called from `percept()`, and world sounds (tui, morepork, fire, rain, …) have no positional model in
this codebase today. Naming that "direction" here would misrepresent a field `percept()` cannot honestly
populate. `sound_direction` above is a shape-trend word, not a bearing; the microphone's own azimuth concept
(`strings_and_sheets.md` §10) is explicitly future and explicitly a *different* coordinate ("Azimuth as a
separate coordinate, not a seventh timbre axis") — this spec does not touch it.

## 3. Where written

**`core/soundscape.py`'s `percept()` only** — the sole origin='sound' writer (§1) — behind a new module-level
flag, `SOUND_STRING_FIELDS = False` at first build, matching the kill-switch shape this plan's own sibling
jobs (J-1424/J-1425/J-1428/J-1430) already use: **off is byte-identical to today's behaviour, additively**.
Sequence inside the existing `if store:` block, *after* the existing `store_fragment()` call already returns
`fragment_id`:

1. Build the six-axis dict once: `c = coords(chosen) or {}`.
2. If `SOUND_STRING_FIELDS`: issue one `UPDATE fragment_context SET sound_key=?, sound_onset=?, sound_peak=?,
   sound_tail=?, sound_felt_valence=?, sound_felt_arousal=? WHERE fragment_id=?` — **never an INSERT**. If no
   `fragment_context` row exists yet for this `fragment_id` (§1: ~11% of the time, when
   `geometry_census.snapshot()` returned falsy), the UPDATE matches zero rows and does nothing — a silent,
   correct no-op, not a fabricated partial row. This is the same "an empty answer must be true, not silent"
   discipline `evidence_recall.py` already states for itself, one layer over.
3. Wrapped in the same `try/except: pass` `percept()` already uses for its own store block — a failure here
   can never cost the prose write or raise past the caller.
4. **Why `fragment_context`, never `memory_fragments`, and why a separate `UPDATE` from `soundscape.py`
   itself, never a new kwarg on `store_fragment()`:** `udms_get_change_dossier("core/memory/store.py")` (run
   this job, F-2091) returned `risk_tier: ELEVATED`, archetype `HIDDEN_HISTORICAL_DEPENDENCY`, and 19 real
   CONTRACT-layer (static-AST, not inferred) dependents — `core/orchestrator.py` (PMI 4.11 bits, lift 17.2×),
   `nodes/inner_monologue_node.py` (PMI 2.19 bits), `core/memory_levels.py`, `core/associative_recall.py`,
   `core/memory_edges.py`, `core/soundscape.py` itself, and 13 more, plus a named test target
   (`scripts/_test_episodic_buffer.py`). Changing `store_fragment()`'s signature or insert statement is real,
   shared-contract risk for 19 files that have nothing to do with sound. Issuing the new columns' write from
   inside `soundscape.py` as a follow-up `UPDATE` keyed on the `fragment_id` `store_fragment()` already
   returns touches `store.py`'s data (a table it owns) but never its code contract — no other caller of
   `store_fragment()` sees a different signature, a different required argument, or a different return
   shape. `fragment_context`'s own columns are already routinely extended this way (§2's cited precedent);
   `memory_fragments`'s 27-column, 19-dependent surface is not a place to add sound-only fields.
5. Restart-gated, like every sibling job in this plan: the flag is read once at import/module scope, not
   re-checked mid-cycle.

## 4. Who reads them

**Nobody, yet — and that is a stated gate, not an oversight.** The one named, concrete candidate reader is
`memory_as_a_service.md` §3.2's felt-recall matcher, *once it is upgraded* from categorical trigger-dimension
equality (today: "does `sounds` contain the key `thunder`") to coordinate-similarity matching (six-axis
distance, the same shape `strings_and_sheets.md` §4's masking law already uses: `d` = six-axis distance
between two points). That upgrade is **not designed here** and is **not this job's scope** — J-1472's briefing
is inventory + spec, explicitly "no build," and felt-recall's own Phase 0 (J-1424, already shadow-built and
verified, F-2057) shipped its match logic *before* this doc existed, reading only `fragment_context.valence`/
`.arousal` plus the categorical dimensions. Wiring these new columns into that matcher is real, separate
design work (a coordinate-distance query needs its own bound, its own realness test per `cognitive_geometry.md`
§4, and its own pre-registered read) belonging to its own job, the same way `memory_as_a_service.md` §4.5 filed
curiosity's fork as D-0312 rather than guessing an answer inline.

**Per this project's write-only-systems law** (`feedback_write_only_cognitive_systems` — verify a method is
actually CALLED before trusting it does anything): `SOUND_STRING_FIELDS` must stay `False` — the columns may
be built and shadow-logged, but not treated as "the plan is progressing" — until either (a) the
coordinate-matching upgrade to felt-recall's §3.2 is itself a real job with a briefing, or (b) a `gauge-check`/
`plan-liveness` pass finds these columns still unread after a stated window, at which point they are flagged
for removal rather than left silently orphaned (the exact fate `_felt_shadow()`'s own jsonl should arguably
also be checked against — it has had no fragment_id join and no named reader for longer than this doc has
existed). **This doc's own build job (§7) must name this gate explicitly in its own briefing, not just here.**

## 5. The `memory_levels` interaction — do gists keep the anchors?

**No — the question does not arise on the path that exists today, because sound fragments never reach a
gist.** `memory_levels._RAW_ORIGINS` (`memory_levels.py:36-41`) = `("reading", "study", "research",
"subconscious_synthesis", "inner_thought", "seed", "lived")`; `'sound'` is absent. `shadow_distill()`'s own
candidate fetch (`memory_levels.py:673`, confirmed at line 674: `origin IN ({ph})` parametrized by exactly
that tuple) never selects an origin='sound' row, and the one live `origin="gist"` writer (`memory_levels.py:
237`) is fed only from that fetch. A sound-origin fragment therefore stays raw (`abstraction_level=0`,
`grounding='grounded'`) forever under today's code — which also means these new coordinate columns are never
at risk of being silently dropped at a consolidation boundary the way `valence`/`felt`/`emotion_embedding`
already are for the origins that *do* get distilled (memory_levels.py's own fetches at lines 286/673/897 never
select those three columns either — raw is the anchor, distillation reads `content`/`origin`/`keywords`/
`timestamp` only, nothing else). **If a future plan ever adds `'sound'` to `_RAW_ORIGINS`** (there is no such
proposal today), that same gap would apply immediately: the new columns would need to be explicitly added to
whichever query feeds the distiller, or they vanish at the gist boundary by default, silently, the same way
everything else not in that four-column SELECT already does.

## 6. Pre-registered read (once `SOUND_STRING_FIELDS = True` and built)

This writer fires **~5×/day** (F-2091: 425 fragments / ~85 days) — an order of magnitude slower than the
substrate-tick and idle-loop writers `memory_as_a_service.md`'s own metric sheets assume (§4.3/§8 there use
"≥ 7 live days"). Reading this at 7 days would see on the order of 35 new rows; that is too thin to say
anything about diversity given only 4 keys have *ever* fired. **Read at ≥ 30 live days** (expect ~150 new
sound-origin fragments):

(a) **Coverage.** Share of new sound-origin fragments with non-null `sound_key`/`sound_onset`. Pre-committed
    bar: within 5 points of the existing 89.2% `fragment_context`-row baseline (F-2091) — if far below, the
    `UPDATE`-after-the-fact approach (§3) has a bug (e.g. a timing gap between the two writes), not a
    coverage ceiling that was already there.
(b) **Distinctness.** Count of distinct `sound_key` values seen. Compare to F-2091's historical 4 — if still
    ≤ 4, that is not a failure of this spec; it is the pre-existing percept-diversity limit (`_PERCEPT_SOUNDS`'
    onset/renotice gating, `_PERCEPT_COOLDOWN_S`) restated, worth its own separate finding if it surfaces
    again, not re-litigated here.
(c) **The two "felt" signals, compared.** Correlation between `memory_fragments.valence` (the live mood at
    write time, §2's separate recommendation) and `fragment_context.sound_felt_valence` (the coordinate-
    derived prediction) across the accumulated sample. High correlation says the hand-seeded coordinates are
    already a reasonable proxy for lived affect (useful groundwork for §4's future coordinate-matching); low
    or no correlation is itself a real, citable finding about `_felt_shadow()`'s own soothing formula
    (`soundscape.py:1356-1358`), not a defect in this spec.
(d) **`sound_direction` stays NULL.** A data-integrity check only, while onset=peak=tail (§2) — it should
    never be non-null before Object A ships a real triplet; if it is, something is reading a stale or wrong
    assumption.

**Kill criterion:** if (a) sits below ~50% (well under the 89.2% baseline) after 30 days, flip
`SOUND_STRING_FIELDS` back to `False` and debug the write site before re-enabling — the same "never costs a
write" fail-open discipline this plan uses everywhere else. Nothing about (b)/(c) is a kill condition; they
are what the read is *for*.

## 7. Founder question — checked for, not found

This job's ground rules require opening a `/decide` if something here needs the founder's call rather than
guessing. Checked and **not filed**, because each candidate fork resolves to an engineering-shape choice with
a clear, precedented answer already stated above, not a values fork:

- Onset=peak=tail degenerate today vs. waiting for Object A — resolved by `strings_and_sheets.md`'s own
  stated law #1 ("a point is the degenerate case, tolerated only until the string exists"); not a new
  question.
- Which "felt" signal to carry — resolved by "both, additively" (§2): they cost nothing together and answer
  different questions (§6c makes that difference the actual point of the read).
- `sound_exemplar_id` before I-0082 is ruled or built — resolved by making it a nullable, independent,
  reserved column (§2): this spec does not depend on I-0082 shipping, and does not pre-empt it.
- Where the new columns live — resolved by the UDMS dossier's own ELEVATED-risk finding on `store.py` (§3.4).

**Build job:** `J-1534` (spawned by J-1472, `ready`, kind `build`, isolation required) — the briefing is this
doc's §2/§3/§4/§6 in full, plus the explicit instruction to re-run `udms_get_change_dossier` on
`core/memory/store.py` for itself before touching anything nearby, and to verify in an isolated harness
before ever flipping `SOUND_STRING_FIELDS` to `True` against the live store, the same way J-1424/J-1425/
J-1428/J-1430 already did. It is independent of `memory_as_a_service.md` §4.6's own J-1515/J-1516 (different
function, different table) — coexisting `ready` jobs on one plan is what job-queue is for, not a race.

## 8. What this is not

Not a schema change to `memory_fragments` (§3.4). Not a rebuild of I-0082's exemplar codebook — `sound_exemplar_id`
is a reserved join, nothing more. Not a change to felt-recall's already-shadow-verified match logic (§4) —
that upgrade is real, separate, future work. Not a new measurement or new runtime DSP — every value here is
either already computed today (`coords()`, `_felt_shadow()`, `mood.current_valence()`) or a zero-cost
derivation off values already computed (`sound_direction`, once Object A lands). Not a claim that gists lose
something they used to keep — §5 found they never had it, for sound, on the path that exists today.
