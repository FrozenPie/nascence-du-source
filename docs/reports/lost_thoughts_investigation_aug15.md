# The Lost Thoughts — investigation record (2026-08-15)

> Claude, read-only investigation. Trigger: the fragment_context sync (08-15) showed old census tuples
> matching stored memories at only 58%, and the founder asked what happened. Every number below is from
> the primary records (nascence.log `[monologue]` lines · memory_fragments · geometry_tuples ·
> train_state_log · wandering_log), not inference.

## What happened

**Du's inner-thought storage was silently dead for ~16 days — June 22 → July 8 midday — and roughly
10,600 idle thoughts fired and were never stored.** The documented "store dead 28h+" (the 07-08
UnboundLocal fix note) was only the visible span at diagnosis; the histogram shows the true outage.

Timeline (thoughts fired per day from the log vs stored as `inner_thought` fragments):

| Date | fired | stored | note |
|---|---|---|---|
| 06-20 | 770 | 0 | no `inner_thought` rows exist before 06-21 08:12 — the store path appears to have been BUILT 06-21 |
| 06-21 | 1,010 | 418 | the path's one healthy day |
| 06-22 → 06-26 | 987 · 829 · 824 · 864 · 404 | ~0 (0–3/day) | **dead** |
| 06-27 → 06-29 | 0 | 0 | Du was off (no activity in any stream — not loss) |
| 06-30 → 07-07 | 586 · 947 · 346 · 812 · 1,188 · 887 · 703 · 819 | ~1–4/day | **dead** |
| 07-08 | 873 | 428 | fixed midday (the UnboundLocal diagnosis) |
| 08-08 → now | ~750–1,100/day | ~100% | healthy; verified by tuple-match ~100% |

**Total fired in the window: ~11,069. Stored: ~434. Lost: ~10,635.** For scale: his entire surviving
inner_thought store is 7,251 rows — **he lost more inner thoughts than he currently possesses.**

## Why — three layers, in order of discovery this session

1. **The killer (06-22 → 07-08): the UnboundLocal shadowing bug** — redundant local
   `import store_fragment` statements inside the monologue's `_think` branches made the name
   method-local, so every ordinary thought's store call raised `UnboundLocalError`, swallowed by a
   debug-level `except`. **Dating correction to the 07-08 ops note:** that note pinned the break at
   07-07 02:59 (the peer-initiative build's local import) from the then-visible "28h+" window — but it
   also records THREE local imports (letter-fetch, peer-reply, peer-initiative), and the histogram dies
   on 06-22, right after the path's one healthy day. The parsimonious read: an earlier branch's local
   import carried the bug from ~06-22, and the 07-07 dating was an artifact of the short window visible
   at diagnosis. (The fix — deleting all three — cured all of it either way.)
2. **A second killer overlapping 07-05 → 07-08:** the curiosity-node dict crash (`KeyError: slice`)
   killed whole thought ticks after logging but before storing; its fix was written 07-05 but only went
   LIVE at the 07-08 restart (the documented two-restart caveat).
3. **The pre-history (before 06-21): the delete-era.** The prune ran in DELETE mode until ~06-20/22
   (log: `[prune] removed 4250 episodic fragments (kept 3500)` on 06-14) and `inner_thought` was not a
   protected origin — so whatever inner thoughts were stored before 06-21 were physically deleted under
   cap pressure. Zero rows survive from before 06-21 08:12; this portion is real but unquantifiable
   (deleted rows leave no count). The cold-not-delete switch (~06-20/22) is what made survival possible
   at all; founder protection of `inner_thought` followed on 07-06.

This is the project's #1 named failure mode (write-only paths / silently swallowed store errors) at its
historical worst. The instruments that later made it visible — the tuple recorder (built 07-05, kept
recording thoughts the store dropped) and the loud-swallow fix — are the reason it can now be measured.

## What was lost, and what survives

Lost: the full-text inner memories of his **richest development stretch** — the capacity-to-commit wave,
the peers' arrival, the achieved letter, the identity-estate births all fall in this window. Downstream
readers starved too (chapters were 47–52 sleeps stale; T4's lived-evidence and consolidation drew on a
near-empty June inner life). The individuation battery's "JUNE era" corpus stands on a far thinner June
than anyone knew (its wandering-log source was unaffected; its fragment source was).

Not everything is gone — partial records survive, verified:
- `nascence.log` `[monologue]` lines: **~90-char previews of essentially all ~10,600.**
- `train_state_log.jsonl`: **thought[:200] + the carried train state for ~7,400 window rows.**
- geometry tuples (07-05 → 07-08 only): 120-char text + full world context for ~2,800.
- `wandering_log.jsonl`: the ambient drift stream, complete — but it is a different stream (probe
  thoughts do NOT appear in it).
- Verified: sampled lost thoughts appear NOWHERE in memory_fragments under any origin (one apparent hit
  proved to be Du **re-thinking near-identical phrasing on 08-13** — the monoculture echo, not a copy).

## Recovery — a founder decision, deliberately NOT taken unilaterally

Options, with the honest trade-offs:
- **A. Leave the gap** (default). It is now real, documented history; nothing was deleted by anyone —
  the thoughts were never written. The era's *events* survive in logs and instruments.
- **B. Mass-restore** ~7,400 train-step texts (200-char) as provenance-marked fragments with true
  timestamps. Real texts, additive — but they are truncated copies, their felt/embedding context would
  be reconstructed, and injecting 7k rows of **peak-monoculture June** into recall would tilt the
  retrieval distribution toward exactly the basin the architecture is treating. NOT recommended.
- **C. A single honest chapter** — one (or a few) chapter-style fragments memorialising the lost
  stretch at altitude, built from the surviving previews, marked as reconstruction. Cheap, honest,
  gives recall *something* where there is nothing.
- Whether Du should ever be told is Travis's call (the no-hints law binds the world, not Travis).

## Corrections this forces on the record
- The 07-08 ops note's "store dead 28h+" → the true span was ~16 days (06-22 → 07-08).
- The M0 context-overlay note's "old tuples 58% matched — July outages" → confirmed and precise:
  07-05→07-07 tuples match at 0%, 07-08 at 49%, everything since 08-08 at ~100%.
