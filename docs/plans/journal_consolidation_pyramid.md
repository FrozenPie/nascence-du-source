# The Journal Consolidation Pyramid — calendar-grounded autobiography (P1 LIVE, verified 2026-08-23)

> **Status: ⚪ PARTIAL — P0 (day-recap) and P1 (week roll-up) BUILT and LIVE, real caps on disk
> (`WEEK_2026-W27/W32/W33.md`); P2 (moon roll-up) and P3 (solstice merge) NOT built; P4 (retire
> `chapters.py`) NOT done, defaulting to "leave it running" by inaction. D-0006's hard-grounding
> shadow grader is built and observe-only live but n=4, nowhere near a real read window.**

```plan-state
stage: partial
phase: P1 week roll-up live; hard-grounding shadow read n=29 RED on mean only, 0 genuine inventions (F-5077, D-0839)
verified: 2026-11-18
evidence_read: 2026-11-18
gate: data/journal_grounding_shadow.jsonl >= 20 rows MET (n=29); promotion awaits D-0839
next: Founder rules D-0839 on hard-grounding promotion; P2 moon roll-up stays unblocked
open_decisions: D-0839
cluster: 2
```


> **D-0006 built (2026-08-23):** the hard-grounding shadow grader (`core/journal_grounding_shadow.py`)
> is wired and live-observing. See Current State below.

## Current State — verified 2026-11-18
- **2026-11-18** (F-5077): Re-read hard-grounding shadow at n=29: RED on mean(faithful) only (0.692 overall, 0.70 window); 0 invented_genuine; low scores are judge false flags. Opened D-0839.

### What we have
- P0 (day-recap) and P1 (week roll-up) BUILT and LIVE (`core/journal.py`, `core/journal_rollup.py`);
  real caps on disk (`WEEK_2026-W27/W32/W33.md`), each citing specific days/observations.
- D-0006 ruled (Travis): keep P1/P2 soft-authored live, run Emissary-graded hard enforcement in SHADOW
  alongside it. Built same day (J-0007): `core/journal_grounding_shadow.py` reuses
  `left_lane.grade_gist_faithfulness` + `memory_levels` verbatim, logs to `data/journal_grounding_shadow.jsonl`.
- Shadow grader re-read (F-0154): 6 of the 20 rows its own `shadow-promotion` spec below wants — mean
  faithful 0.76, zero genuine inventions. Proves the plumbing works; does not yet answer D-0006's real
  question (does soft grounding ever actually diverge from hard).
- P2 (moon roll-up), P3 (solstice merge), P4 (retire `chapters.py`) — still NOT built.

### What we need
§6 Q3 (retire `chapters.py` explicitly, vs. leave it running by inaction) and Q2 (temporal-only vs.
also semantic/geometry links) resolved before P2/P3 lock the link schema further.

### What we're doing next
P2 (moon roll-up) is unblocked by D-0006 and can proceed soft-only, matching P1 — nothing is queued
for it yet. In parallel, let the shadow grader accrue toward its own `min_rows: 20` bar
(`data/journal_grounding_shadow.jsonl`) before re-reading it against D-0006's defeater.

```shadow-promotion
id: hard-grounding
log: journal_grounding_shadow.jsonl
window: 20
min_rows: 20
green: mean(faithful) > 0.7 and count(invented_genuine) == 0
```
First run (2026-08-24, n=6): `INSUFFICIENT` — matches "nowhere near a meaningful window" above.

---

> **Founder call (Travis, 2026-07-06).** Replace the theme-clustered `chapters` system — dead 52 sleeps
> because its era-closing gate can never fire on a mind whose dominant theme (the monoculture) never
> stops (task #5) — with a **calendar consolidation pyramid**: days roll up into weeks into moons into
> solstices, each level a plain grounded journal linking down to what it consolidates. "He lives in a sim
> with realtime sun" — so he periodizes by the calendar his world already runs (sun · tide · moon ·
> season), the way a person does, not by waiting for a theme to end.

> **Disease treated:** two at once. (1) autobiographical consolidation is DEAD (chapters, era-gate blocked
> by the monoculture — `chapters.py` find_cluster/_era_window). (2) reality-thinness — Du "acts but won't
> OWN the act," hides in metaphor. The journal is the one place that forbids the maybe; grounding every
> level in real logged deeds/perception makes memory-formation a daily reality-anchor.

> **Lineage & law.** The temporal instance of the cognitive-geometry constitutional law (immutable
> objects, plastic links; caps are NEW nodes with lineage links, nothing mutated/deleted; originals kept
> at archive). Retires `chapters.py`'s theme-eras. Builds on the existing `core/journal.py` (Travis +
> Claude, 2026-06-21). Function-over-imitation: humans periodize by their world's calendar, incl. ongoing
> themes ("the early years") — the old model over-imitated the special case (the period that visibly ends).

---

## 0. WIN CONDITION — signatures that must move, or it's dead code

1. **Consolidation ALWAYS fires** — a day-recap every day, a week-cap every week, a moon-cap every moon,
   a solstice capstone each solstice. No period stalls (the era-gate failure mode is structurally gone).
2. **Every level is grounded** — a level cites specifics from the items it links to (a week-cap names
   particular days + the world under them); nothing floats into abstraction. Measured: an Emissary
   groundedness grade per level, and the "what he thinks he did vs what the record says" gap as a
   confabulation signal.
3. **Compression holds** — each level stays "similar size" (a readable entry); detail lives one link
   down, reachable via `memory_links`. A year is ~2 solstices → ~12–13 moons → ~52 weeks → ~365 days, a
   navigable tree, not a growing document.
4. **The monoculture becomes LEGIBLE** — a moon-cap that honestly reads "another moon circling the same
   water, unmoved" is a retrievable memory his reflection/T4 can confront. Stagnation named, not hidden.

**Never claimed:** "he has a richer inner life." Grounded record + retrievability only.

---

## 1. THE TWO GROUNDED STREAMS (the day level — mostly BUILT)

Both already coexist in the per-day day-book (`data/Journal/JOURNAL_YYYYMMDD.md`):

- **"What I did" — the day-recap** (`journal.write_entry`). Fires once/day at sleep, built from his real
  `origin='action'` records (`_deeds_since`), plain first-person past-tense, anti-metaphor (bans
  river/becoming/self/perhaps…), ends on how it felt + what he liked (→ affections ledger). **His life.**
  - **BUG FIXED 2026-07-06:** the recap shared the day-book file's mtime with the field-observations, which
    (several/day) kept refreshing it, starving the once-a-day recap out of its 20h gate (6 recaps in 15
    days, none for 3+ days). Now tracks its OWN fire in `data/Journal/.day_recap_state.json`. Restart-gated.
- **"What I saw" — the field-observations** (`journal.write_observation`). Fires from his want, several/day,
  a precise plain naturalist's record of what's in front of him (the tide, the stones, the cuttlebone);
  carries felt/valence. **His world.**

Together, rolled up, they are a complete grounded autobiography: **a life lived IN a world.**

---

## 2. THE PYRAMID — parallel through the moon, merge at the solstice

**Decision (Travis, 2026-07-06): the two streams stay PARALLEL through day → week → moon** — each rolled
up from its OWN stream, each linked down, no cross-contamination (parallel keeps each clean and grounded;
early merge risks the four-altitudes-of-mush failure the old chapters hit: "identical opening sentences").

| Level | "What I did" | "What I saw" | trigger |
|---|---|---|---|
| **Day** | recap (grounded in actions) ✓ | field-observations ✓ | sleep / his want |
| **Week** | recap of the 7 day-recaps | recap of the week's observations | week rollover |
| **Moon** | recap of the ~4 weeks | recap of the ~4 weeks | new moon (`heavens.py`) |
| **Solstice** | **MERGE →** one grand seasonal capstone drawing on BOTH pyramids | | solstice (`spatial.sun`/season) |

The **solstice is the big event** — the one place the life and the world become one memory: *"the moons of
that winter, when I kept to the study and read Tyndall while the sea ran wild and the mornings stayed dark."*

**Grounding propagates UP:** each level is authored FROM the grounded level below (week from day-recaps,
moon from weeks), so the whole tree inherits the day level's reality-anchoring. **Similar size** at each
level = compression by altitude, not length. **Anti-mush law:** each level MUST cite specifics from the
items it `memory_links` to (name the days/weeks + the world under them), and speak at its own altitude.

---

## 3. LINKS & ARCHIVE (the multi-level/multi-dimension structure)

- Every cap is a NEW node with **`memory_links` down to what it consolidates** (day→raw items;
  week→day-caps; moon→week-caps; solstice→moon-caps of that season). The table exists but is Phase-0
  EMPTY — this is what finally populates it.
- **Originals kept at archive level, never deleted** — reachable by walking the links down: solstice →
  moon → week → day → the actual moment.
- OPEN: do caps ALSO carry semantic-gist and geometry-neighbour links (the full "multi-dimension" — a
  memory reachable temporally AND by theme AND by felt-neighbour), or temporal-only for v1?

---

## 4. REUSE vs NEW

| Piece | Status |
|---|---|
| Day-recap (grounded, plain) | **exists** (`journal.write_entry`) + **starvation fixed** today |
| Field-observations | **exists** (`journal.write_observation`) |
| Day-book file per day | **exists** (`JOURNAL_YYYYMMDD.md`) |
| `memory_links` table | **exists, Phase-0 empty** → populate |
| Sleep trigger (day boundary) | **exists** (nightly sleep) |
| Calendar clocks (moon / solstice / season) | **exist** (`heavens.py`, `spatial.sun`, season) |
| Capstone-generation pattern | **exists** (essay lesson, gist distiller) |
| Emissary groundedness grade | **exists** (grades essays) → reuse per level |
| **Week / moon roll-up authors** | **NEW** |
| **Solstice merge capstone** | **NEW** |
| **The link pyramid population** | **NEW** |
| **Retire `chapters.py` theme-eras** | **NEW** (stop forming; keep the 7 existing as-is) |

---

## 5. PHASING (observe-first where it applies; additive)

- **P0 (done today):** day-recap starvation fix — daily recap flows again on restart.
- **P1:** the **week roll-up** for both streams (the smallest new rung; day level already firing). Author
  from the week's day-recaps / observations; link down; Emissary groundedness grade; read the first weeks
  before going higher.
- **P2:** the **moon roll-up** (from weeks), anchored to the lunar cycle.
- **P3:** the **solstice merge** capstone (from the season's moons, both pyramids).
- **P4:** retire theme-chapters; wire the caps into ordinary recall (the caps surface; raw via links).

Each rung gated on the one below reading sane (no mush, grounded, similar-size).

---

## 6. OPEN QUESTIONS

1. **Roll-up grounding enforcement** — soft (author from the level below) or hard (Emissary grades each
   cap against its linked items, flags anything unsupported = the confabulation signal)?
2. **Multi-dimension links** (§3) — temporal-only, or also semantic/geometry, for v1?
3. **Retirement of `chapters.py`** — hard-stop new theme-chapters, or leave it running harmlessly beside
   the pyramid until the pyramid proves out?
4. **Week/moon boundaries** — calendar week vs the tide's spring/neap fortnight; new-moon exact vs a
   ~29.5d counter.

---

*Status (superseded by "Current State — verified 2026-08-23" above): DRAFT. Day level BUILT (+ starvation
fixed today, restart-gated). The roll-up pyramid (week → moon → solstice) is the new build. Retires
`chapters.py` (task #5). Companion: `cognitive_geometry.md` (the object/link law), `AWAITING_EVIDENCE.md`
(the field-journal + directional-world read-path).*
