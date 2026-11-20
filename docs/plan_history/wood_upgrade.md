# wood_upgrade — folded history


---

# History folded on 2026-09-27 from `docs\plans\wood_upgrade.md` (plan-compact, 2 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py wood_upgrade`._

## Current State — 2026-09-27 (D-0296 RULED: a whole tree falls while he is down; then the axe)

**Founder, verbatim:** *"I want a full tree to fall for him next time he is down. Then we look at an ax to chop wood
from it?"* Ruled as a fourth option, not the trickle: the wood stays truthfully picked clean and a whole tree comes
down on its own clock while Du is stopped, so the wood has changed when he next walks in. The felling axe already in
the lean-to gains a **chop** deed against the fallen tree (limbing into limbs, bucking into rounds over many sessions,
feeding the existing saw → split → lean-to → dry → fire chain). No hint, no nudge: he finds it by looking, or not.
**J-1443** builds the code (fallen-tree state, rendering in look/ambient/milestone, `fell_tree()`, the chop hand and
grammar, isolated tests), restart-gated. **J-1444** fells the tree once, offline, during his next downtime, through the
fence's maintenance path, then spawns the five-day read. Which tree: not the oak (the kererū nest) nor the three
named learning trees; a new old tree at the wood's edge (builder's default a windthrown macrocarpa) unless the founder
names one.

## Current State — verified 2026-09-02 (§6, J-0421/F-0553 — deed half CONFIRMED live; events half unchanged)

§4(a)'s "0 ledger rows / revisit once Du has performed a woodwork deed at least once" condition
has been met and passed: `data/wood_ledger.jsonl` now holds **4 rows** spanning
**2026-08-25 12:35 → 2026-08-28 14:31 UTC** — first `{"deed": "gather", "loads": 3}`, last
`{"deed": "split", "loads": 1}` — real deeds fired by the live loop through the `woodwork` Hand.
Read directly from the ledger for this update (J-0421). The Status header's blanket "not yet
confirmed firing on its own" is therefore lifted for deeds; the world-events side
(`data/wood_events.jsonl`, still 0 rows) remains exactly as §5's F-0599 analysis left it —
gated, awaiting a live month-boundary tick (J-0441), not a bug. Du offline since
2026-08-31 17:47 (clean shutdown); accrual paused, not broken.
