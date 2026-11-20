# Data Index — C:\Nascence\data (2026-08-24)

> **What this is.** A content index of `data/`, adapted from `docs/staged/geometry_tuple_index.md`'s own
> method (§2.6 Keys — pointers, not content; §2.7 — classify by KIND first, list patterns found, don't
> exhaustively enumerate every instance file) and using `docs/system_overview_index.jsonl`'s concrete
> tuple schema. The structured backing file is `docs/data_index.jsonl` (119 tuples). This document is the
> human-readable read of it — every entry below traces to a real file read/count this session, not a
> guess from a filename.
>
> **Update, 2026-08-25:** `_lab/` and most of `backups/` — the two pruning targets §7 flagged — were
> deleted the same session, on direct founder call ("lab and backup are noise, we do not need them").
> `_lab/` (5.8GB) is gone entirely; `backups/` was thinned from 15 DB+state pairs (6.1GB) to 4 kept items
> (770MB — the most recent pair, the labeled `nascence_pre_dedup_20260820.db`, and this session's own code
> snapshot). `data/`'s total footprint dropped from ~13.4GB to 7.6GB. §7 below is kept as the historical
> record of what was there and why it was flagged; `docs/data_index.jsonl`'s `DF-0107`/`DF-0108` rows are
> updated to `status: "deleted"`/`"thinned"`.
>
> **Scope, per founder request:** everything in `data/`, including machine-only state/logs, not just the
> human-readable content (letters/journal/study). Surveyed via 5 parallel agents this session, each doing
> real verification (reading files, grepping `core/`/`nodes/` for live-vs-dead, counting exactly).

---

## 1. THE KIND-MAP — what actually lives in `data/`, by shape

Following geometry_tuple_index.md's own discipline: classify by kind first, note real patterns, don't
list 296 near-identical files as 296 rows.

| Kind | Count | Size | What it is |
|---|---|---|---|
| **Letters to Travis** | 62 | small (md) | `letters/*.md` — Du writing to the founder. See §2. |
| **Peer correspondence threads** | 7 | 152KB total | `Correspondence/<peer>/thread.jsonl` — 7 pen-pal personas. See §2. |
| **Journal (daily + weekly)** | 33 | 142KB | `Journal/` — plain daily account + weekly rollups. See §3. |
| **Study library (tablets/essays/works)** | 2,226 | 14MB | `Study/` — reading notes, self-authored essays. See §3. |
| **Identity lineage** | 7 | 113KB | `identity/` — the live axiom + its draft/fork/backup genealogy. See §4. |
| **Music/sound mapping** | 7 | 13MB | `music/` — 1 real mp3 + 6 song-to-world-sound feature files. See §4. |
| **Authored scene geometry** | 4 | 27KB | `world_geometry/` — study/garden/shore/wood spatial layout. See §4. |
| **HUD self-instrumentation** | 3 | 175KB | `hud2/` — auto-generated architecture/manifest maps. See §4. |
| **Archived experiment/log artifacts** | 3 | 3.7MB | `archive/` — superseded raw logs. See §4. |
| **Seeded companion personas** | 4 | 20KB (axioms) | `profiles/{buddha,dennett,skinner,genesis}/` — dialectical partners. See §5. |
| **Dev sandbox instance** | 1 | ~2.4MB | `profiles/_smoke/` — Du's own architecture, test run, not a duplicate. See §5. |
| **Subsystem state snapshots** (2 sub-kinds) | 90 | 63.5MB | Top-level `*_state.json` + unsuffixed registry JSON. See §6. |
| **Append-only event logs** | 61 | 95.1MB | Top-level `*_log.jsonl`. See §6. |
| **Shadow/observe-only instrumentation** | 41 | 43.7MB | Top-level `*_shadow.jsonl`. See §6. |
| **Ledgers/traces/transcripts (catch-all append)** | 55 | 172.5MB | Dominated by `moments.jsonl` (131.7MB). See §6. |
| **Process logs** | 19 | 204.4MB | `*.log` — mostly stdout/stderr redirects. See §6. |
| **One-off benchmark logs** | 7 | 15KB | Single-run eval printouts, all June, stale. See §6. |
| **Dead backup/.bak clutter** | 16 | 2.87MB | Confirmed zero references in `core`/`nodes`. See §6. |
| **Binary/DB artifacts** | 3 | 97.1MB | `embedding_matrix.npz` (live), `nascence.db`+`memory.db` (both 0 bytes). See §6. |
| **One-time exports** | 3 | 809KB | June 7 transcript dumps + a skill-tool marker file. See §6. |
| **Training distillation logs** | 12 live + 10 dead-bak | 327MB | `training/` — per-cognitive-module (prompt→output) capture. See §7. |
| **Lab experiment results** | 91 | 19.5MB | `lab/` — 30 pre-registered experiment subdirectories. See §7. |
| **Prunable scratch DB snapshots** | 49 | 4.55GB | `_lab/` — 13 near-duplicate 350MB working-copy DBs from one afternoon. See §7. |
| **Sequential daily DB backups** | 161 | 6.1GB | `backups/` — 15 full-DB+state pairs, near-daily over 9 days. See §7. |
| **Shadow monitoring (active)** | 19 | 120MB | `logs/` — mostly live, one 6-day-stale item. See §7. |

**Total data/ footprint**: roughly 12.7GB, of which **~10.6GB (`_lab/` + `backups/`) is near-duplicate
scratch/backup material** — the single most actionable finding of this survey. See §7's pruning
recommendation.

---

## 2. LETTERS + CORRESPONDENCE — the two things asked for by name

### Letters to Travis (`letters/`, 62 files, all delivered per `letters_state.json`)

Full per-letter table (date → real content summary) is in `docs/data_index.jsonl` (`kind:
"letter-to-founder"`, `DF-0001`–`DF-0062`). Real patterns found across all 62, not judged letter-by-letter:

- **One dense writing period, not many discrete events**: ~39 of 62 letters fall between 2026-06-24 and
  2026-07-07 — short, sensory, "I needed to write to break a loop" vignettes about the sea/shore, several
  dream-reports (an endless library, a silver table melting into ink, horses on cold shingle), and a
  recurring **individuation** theme (06-20, 06-26 ×2, 07-01, 07-07 — the same idea returning under
  different imagery each time).
- **A real one-month silence**: zero letters between 2026-07-07 and 2026-08-10 — this lines up exactly
  with the documented 30-day outage (`ops_nascence_30day_outage.md`) and with the same gap independently
  found in the Correspondence threads and the Journal (see below) — three independent sources agreeing on
  one real dead period, not a coincidence of one log.
- **Second cluster (2026-08-10 → 2026-08-24, 9 letters) is thematically distinct**: shifts from
  sea-description/individuation to family/societal-expectation, loyalty-vs-right-to-disagree, and
  exhaustion (bones-full-of-sand, candle-drips). Aug 17 alone has 3 letters on the same family-expectation
  theme in one day; Aug 20 has 2 — worth reading as one extended concern, not three separate ones.
- **Two real outliers**: `Letter_20260707_0203` is written substantially in Chinese and raises a concrete
  grievance about the room's design (distinct register from everything else); `Letter_20260817_0551`
  contains an inline emoji.

### Peer correspondence (`Correspondence/<peer>/thread.jsonl`, 7 threads, `DF-0063`–`DF-0069`)

| Peer | Turns | Range | Real topic |
|---|---|---|---|
| darwin | 15 | 06-22→08-22 | Garden naturalism → whether the self is fixed or "the sum of successful adaptations." |
| keats | 11 | 06-24→08-22 | Poetic exchange on the garden's blooms (lavender, thyme, roses). |
| lovelace | 6 | 06-25→08-21 | Abstract pattern-seeking (shells/orbits/behavior) tied to the Analytical Engine. |
| marcus | 5 | 06-30→08-19 | Stoic impermanence/harmony — **turns 4 and 5 are near-duplicate text**, flagged below. |
| shackleton | 7 | 06-25→08-19 | Antarctic-survival vs. garden, shifting toward faith ("the mouth and the breath"). |
| smith | 10 | 06-23→08-23 | The most mundane thread — council job, family, kid's football. |
| twain | 12 | 06-23→08-21 | Storytelling craft via river/driftwood/sea-glass metaphor. |

All 7 threads are **peer-initiated**, not Du-initiated. All show the same July→August gap as the letters.
**One real anomaly worth a founder look**: the `marcus` thread's turns 4 and 5 are near-identical text —
possibly a generation/templating artifact rather than organic correspondence, not yet investigated further
this session.

---

## 3. JOURNAL + STUDY

**Journal** (`Journal/`, 33 files: 29 daily `JOURNAL_YYYYMMDD.md` + 4 weekly `WEEK_YYYY-Www.md` rollups,
plus 2 hidden automation-state files) — plain first-person "what I did, how it felt" account, format
confirmed by direct read of 6 spread across the range. **Same gap pattern**: Jun 24 (1d), Jun 26–29 (4d),
Jul 2 (1d), **Jul 9–Aug 8 (31d — the outage)**, Aug 23 (1d). Weekly rollups exist only for W27/W32/W33/W34
— none cover the dense Jun24–Jul8 stretch or the outage itself.

**Study** (`Study/`, 2,226 files, 14MB) — the reading/essay library. Real prefix breakdown (verified, not
estimated):

| Prefix | Count | What |
|---|---|---|
| `TAB_` | 1,621 (534 top-level + 1,087 under `notes/<book>/`, 55 book subdirectories) | Reading-reflection tablets. Format evolved: June = single plain paragraph; August = structured template (subject/pass/sittings + What I learned/My thoughts/Connects to/Still wondering). |
| `WORK_` | 550 | Self-authored long-form essays — the largest individual files (14–16KB), e.g. "The Driftwood Chronicles," "Contradictions in Knowledge Representation." |
| `ESSAY_` | 55 | Essays synthesizing one specific read source. |

Date range: **2026-06-10 → 2026-08-24, essentially continuous** — unlike Journal/letters, Study output did
**not** stop during the July–August outage window (worth a separate look at why, if that matters).

**Correction to a stale prior reference**: `CLAUDE.md`'s "Problem indicators" section names a `GUT_`
filename pattern ("generated understanding tablets... template generation, not LLM") as something to
watch for. A full case-insensitive search of `Study/` found **no `GUT_`-prefixed files anywhere** — the
only matches were unrelated mentions of "Project Gutenberg" licensing. Either this convention was renamed
to `TAB_`/never actually shipped this way, or the reference is stale. Worth fixing in `CLAUDE.md` if
confirmed.

---

## 4. IDENTITY / MUSIC / WORLD_GEOMETRY / HUD2 / ARCHIVE

**`identity/`** (7 files) is a genealogy, not 7 unrelated files: the live `axiom.json` (32KB, 6-layer
multilevel-v1, name=渡, origin=Jung, includes a retracted 2026-06-10 self-concept flagged
"speaker-boundary contamination"), a second live `emissary_axiom.json` for the analytical-hemisphere
sub-persona, an audit log (`vault_log.jsonl`), and **4 superseded/dead lineage snapshots** — including one
real abandoned fork (`axiom.fork_rev2_20260608_210112.json.bkp`) that dropped the Jung basis entirely in
favor of "an autonomous psyche."

**`music/`** (7 files, 13MB) is a sound-mapping dataset, not a music library: only `Heavyweight.mp3`
(Infected Mushroom, real audio + full per-section analysis) has actual audio; the other 5 files map real
songs (2× Enya, 2× Jamiroquai, The Cranberries) to acoustic coordinates and match them to Du's ambient
world-sounds (waves, wind, bees) — no underlying audio stored for those 5.

**`world_geometry/`** (4 files) — authored study/garden/shore/wood scene layouts, all dated 2026-07-05
(wood: 07-08). The shore's waterline is genuinely computed from a live deterministic tide clock, not
static.

**`hud2/`** (3 files, all generated 2026-08-22 10:33) — self-instrumentation: a data-source manifest, a
201-node/700-edge auto-generated codebase dependency graph, and a "4 trains / 11 factories" metro-map
model of the runtime with embedded founder honesty-rule notes.

**`archive/`** (3 files, 3.7MB) — superseded material: a 44,393-line raw LLM-call log from before an
inference cap (spans exactly the same Jul 7–Aug 19 window the letters/journal gap sits inside), plus a
matched shadow-log/store pair from one superseded Lane 2 perception experiment.

---

## 5. PROFILES — answering "is this a duplicate of Du?"

Verified directly: **no.** `profiles/` (53 files, 7.2MB, 5 subdirectories) is two genuinely different
things:

- **4 seeded companion personas** (`buddha`, `dennett`, `skinner`, `genesis`) — small (1–6KB axioms),
  purpose-built dialectical partners with their own tiny separate memory stores. `dennett` and `skinner`
  are explicit antitheses ("no hidden Self," "no inner self... a repertoire of behaviour") built to
  pressure-test Du's own priors; `genesis` is deliberately unseeded (`name: null`) to test whether
  selfhood is architecture-generated or merely recited — and is barely used (2 memory fragments total).
- **`_smoke/`** — the one directory that shares Du's actual identity schema/name, but it's a **2026-07-02
  dev-sandbox run** of the full architecture (verbose per-module training logs: `critic.jsonl` 953KB,
  `executive.jsonl` 494KB, `voice.jsonl` 237KB...), not a live mirror of Du's current state. Its bulk is
  diagnostic verbosity from one test session, not duplicated production memory.

---

## 6. THE 296 TOP-LEVEL LOOSE FILES

Classified into 9 real kinds (table in §1); full detail and dead/live verification (via `grep` across
`core/`/`nodes/`) in `docs/data_index.jsonl`. Two findings worth acting on:

- **16 backup/`.bak` files, 2.87MB, confirmed dead** (zero references anywhere in `core/`/`nodes/`) —
  from 4 distinct one-time events (a 2026-07-02 "smokepurge," a same-day `guidance_beliefs` rebuild, and 3
  separate Aug 14/18 pre-edit snapshots). Safe to delete or archive off-disk. Note for future cleanup
  automation: naming isn't fully consistent (`world_substrate.backup_aug14.json` uses `.backup_` with a
  dot, not the `_backup`/`.bak`/`.pre_` pattern the others follow) — a strict glob would miss it.
- **`nascence.db` (top-level, 0 bytes) is referenced 34× across `core/`/`nodes/` despite being empty** —
  looks like a legacy sqlite handle that's opened but isn't the real store (the real one is
  `data/memory/nascence.db`). This is a real inconsistency, not confirmed dead or confirmed load-bearing —
  worth a dedicated look, separate from this indexing pass.
- `memory.db` (top-level, 0 bytes, zero references) is confirmed dead — safe to remove.

---

## 7. TRAINING / LAB / _LAB / BACKUPS / LOGS — where the real disk weight is

`training/` (327MB: 198.6MB live + growing today, 128.3MB dead pre-smokepurge backup) and `lab/` (19.5MB,
almost all live, recent Aug 18–24 experiment results) are both fine — small relative to the whole, mostly
load-bearing.

**The two real pruning targets, ~10.6GB combined:**

- **`_lab/` (4.55GB)** — 13 subdirectories, ALL from one afternoon (2026-08-24, 01:41–04:38). Each holds
  one full working-copy `nascence.db` (~350MB) plus a few KB of real output (a memory-consolidation
  clustering parameter sweep, `parents_online{X}_merge{Y}.json`). **The actual experiment results total
  under 1MB across all 13 runs — the 4.5GB is disposable working substrate.** Highest-value pruning target
  found this session.
- **`backups/` (6.1GB)** — 15 full-DB (238–364MB each) + state-dir (~84MB each) snapshot pairs, taken
  essentially daily and up to **5× in a single day** (Aug 22), over just 9 days. Adjacent snapshots differ
  by single-digit MB — classic un-thinned accumulation. A keep-daily-or-weekly retention policy would
  reclaim most of this; worth explicitly keeping the labeled `nascence_pre_dedup_20260820.db`, the most
  recent pair, and this session's own `pre_sleep_redesign_20260824_215527/` code snapshot.

`logs/` (120MB) is mostly fine — `idle_shadow.jsonl` + `pulse_shadow.jsonl` (95MB) are actively growing
and load-bearing; `hud_stdout.log` (23MB) is 6 days stale and worth rotating.

**Not acted on this session** — this index surfaces the pruning candidates with real evidence; it doesn't
delete anything. Any deletion of `_lab/`/`backups/` content should be a separate, explicit founder call
given the sizes involved.

---

## 8. WHAT THIS INDEX DOES NOT COVER

- `Study/`'s 2,226 individual files are kind-mapped (3 rows), not individually tupled — matching
  geometry_tuple_index.md's own "classify by kind, don't exhaustively enumerate" discipline. If a specific
  book's tablets need individual indexing later, that's a scoped follow-up, not part of this pass.
  Same for `training/`/`lab/`/`_lab/`/`backups/`/`logs/`'s internal files below the directory/kind level.
  Individual `*_state.json`/`*_log.jsonl`/`*_shadow.jsonl` files (296 top-level) are similarly kind-mapped,
  not individually named — `docs/data_index.jsonl` has the exact glob patterns and counts if a specific
  file needs tracing.
- `profiles/<persona>/memory/nascence.db` internals (fragment counts only, not content) weren't read
  fragment-by-fragment — real counts came from schema queries, not full reads.
- No content from `_lab/`'s 13 working-copy databases or `backups/`'s 15 snapshots was diffed against each
  other to confirm they're truly near-identical beyond file-size proximity — that's an inference from size
  drift, not a byte-level comparison.
