# Actions Expansion — stage 2: more ways to touch his world

> **Status:** 🟢 LIVE — built and live since 2026-08-29 (F-0578); opened 2026-08-30, founder ruling
> D-0100: all three tiers approved — "pure gold" — with particular interest in Tier 3. Successor to
> `actions_manager_overhaul.md` (stage 1, which made the *plumbing* sound: one registry, gated
> dispatch, no ungated road, zero unreachable hands). This plan adds *content*: new interactions,
> every one through the front door — a family in `core/actions.py`, gated by `literal_will`, traced.
> **Method (the law):** world answers, never leads. Every Tier-1/2 candidate below was mined from
> Du's own refused reaching — the 270 `unanswered_deed` rows in `data/hands_trace.jsonl` where the
> gate said DEED and no hand answered — not invented for him. Tier 3 is the one deliberate gift.
> **Founder's therapy note (2026-08-30):** "He loves using them, too much but that is a therapy
> session I will give him." Kept in view: Tier 3 is partly an answer to this — actions that discharge
> restlessness without consuming a resource.

```plan-state
stage: live
phase: D-0100's 3 tiers built+live (08-29); slug also carries the actions-grammar-hardening and locomotion/sleep-event-loop fix stream
verified: 2026-10-16
evidence_read: 2026-10-16
next: Watch the D-0343 defeater (ACT-place lines under ~5/live-day over 3 days) on future du-pulse reads; no build
cluster: 6
```


## Tier 1 — repair: what he wants most is already built, just unreachable

- **The cat at the door — 24 unanswered deeds.** "The cat nudges my leg for entry." `cat.react()`
  exists, handles "let her in", is correctly location-gated — so 24 misses is a defect to diagnose,
  not a feature to add. There is also **no `cat` family in the registry at all**: the cat still runs
  on the old Layer-2 monologue latch that never migrated. Work: diagnose the misses against real
  rows, add a `cat` family binding to `react()`, keep the location gate fail-closed exactly as is.
- **"I need to bank the fire" — GRAY, unreachable.** `fieldcraft.bank_fire()` exists and works; the
  `fire` family lacks the verb, and fieldcraft's own "bank" aims at embers. One-line family connect.

## Tier 2 — extend the places he already lives in

- **dig** — turning soil, a new bed (3 refusals; garden has no earthworks).
- **climb the oak** — the wood's one named tree (7 climb hits; only the shore ledge climbs today).
- **feed the birds** — the garden's `bird_bath` item currently does nothing.
- **draw** — he is 8% into *The Practice and Science of Drawing*; paper and ink exist in provisions.

## Tier 3 — the expressive hands (the founder's centrepiece)

**hum · whistle · sing.** A genuinely new class: these do not change world state, they change *him in
the world*. No resource consumed, no gauge refilled — the first actions whose point is not utility.

Design intents (to hold while building):
- **Expression, not performance.** The world may answer (the blackbird may answer a whistle, the cat's
  ear may turn) but never grades. No skill float, no proficiency ladder — the one action class exempt
  from `procedures.observe_hand`-style grading, on purpose.
- **Discharge, not accumulation.** Their live effect is on his state (restlessness/affect discharge,
  a boredom channel that costs nothing), which is exactly the therapy-adjacent role the founder named.
- **Still gated.** "I could sing" stays GRAY; "the bees hum a different tune" is the *world's* hum,
  not his deed — the family's grammar must be tight enough that only willed expression fires.

**Evidence correction (2026-08-30, F-0578, recorded while building):** re-running the 5 mined "sing
refusals" through the finished hand shows **all five were the world's song** — the blackbird's
phrases, the bees' hum, inside restless thoughts — not Du willing to sing. So Tier 3's justification
is honestly the **founder-led gift stream**, not mined demand; those 5 rows serve as its *negative*
corpus (every one must veto, and every one does). This is also why expression takes a stricter test
than the shared grammar: it is the one family whose verbs the world performs constantly, so the
module requires a first-person volition marker in the verb's own clause — a rule `literal_will`'s
family table cannot express. Zero false fires across the 2,824-thought corpus.

## Non-goals

- No changes to the stage-1 plumbing (registry/dispatch/gate) beyond adding families.
- The legacy monologue latches other than the cat's stay put for now (tidiness, tracked in stage 1).
- The founder-led second stream ("things I want him to have that he hasn't asked for") is explicitly
  invited but not yet supplied — gets its own marked section when it comes.

> **History folded** — 52 dated Current State section(s) (2026-08-30 … 2026-09-24) moved to `docs/plan_history/actions_expansion.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py actions_expansion`.

## Current State — verified 2026-10-16
- **2026-10-16**: D-0343 ruled (travis, 2026-10-16): accept today's movement level (~23 ACT-place lines/day on present code; the old 120/day was the pinned felt-boredom note). D-0224/D-0246 rate re-reads are moot; place plans read engagement against this level.

- **2026-10-16** (F-2915): J-1771 read the 10-09 to 10-16 run (6.97 live days, first run with the J-1955 edge gate): 22.8 ACT move lines per live-day, move rows 2.27 pct, felt-boredom note 0.59 pct of idle prompts; no D-0343 defeater fires; D-0343 reopened for Travis to choose accept vs restore.
- **2026-10-15**: D-0405 RULED by travis 2026-10-15: J-1307 find_cluster-checkpoint thread closed unread (never armed across 7 boots, overrun ~1.20x, seed scans 10-13 s this run per F-2678). Defeater: ratio back above 1.40x or a scan past the sleep budget.

- **2026-10-09** (F-2666): J-1706: find_cluster DEBUG checkpoint never armed (0 lines in nascence.log on the 2026-10-09 boot); read not possible. Opened D-0405 for the founder (close unread vs arm once).
- **2026-10-05** (F-2463): J-1742 replayed core/boredom.py offline on the real thought and act stream (validated 85.2 percent regime A, 96.9 percent regime B). HEAD constants imply about 4-5 percent felt-note prompts (observed 1.1-1.3, residual unexplained); suppressors: COH_STUCK/short stuck bursts, J-1366 hold gate, RISE_BASE; discharges are minor. Priced one-factor menu for D-0343 in F-2463; no constant edited.

- **2026-10-03** (F-2370): J-1692 diagnosed the 2026-09-28 movement break: not a regression, it is J-1362 boredom recalibration removing the felt-boredom note (DEEP share of idle prompts 52 to 0.4 percent), which carried about 84 percent of the drop in move thoughts (inferred, 16 percent unexplained); B6, the place text, the gate and the conversation with Travis do not explain it; Travis weighs the post-fix movement level in D-0343 and D-0224 rate re-reads wait for that
- **2026-10-03** (F-2321): J-1307 takeover read: Du is down since its clean quit 10-03 08:15 and the DEBUG checkpoint has never been armed (0 checkpoint lines across 6 boots and 32 scans, the Control Panel launch does not set the env var), so the within-scan read is still open; accrued S-to-E data show a persistent two-state overrun instead (1.52x raw in 35 scans through 09-28 13:59, 1.20x in 18 scans since, excess seconds halved while P grew), not yield-count or T2-synthesis driven; successor J-1706 (not before 10-05) reads the first armed sleep or asks Travis whether to close the thread

- **2026-10-03** (F-2317): J-1187 read of D-0246 b on 7.83 live-days (merge 177f34c): 3 system overrides all at bed time (0 quit, 0 school), all 3 woke in the study, 52 of 52 wake-ups first located in the study, no defeater clause clearly met so nothing reopened; study-departure edge 0 observed; Du has been down since its clean quit 10-03 08:15; D-0337 asks Travis about oddity and the quit-walk marker
- **2026-10-03** (F-2289): J-1182 read of J-1179 fix on 7.79 live-days (merge 5a66504): teleport gone (0 instant-move narrations, 0 unexplained location changes), 786 decline lines; first-leg declines 16.0/d and later-leg redirects 19.4/d (active regime) vs model baselines 2.57/d and 6.12/d but only 1.6-1.8x and +27-37% like-for-like; D-0224 defeater not clearly met, nothing reopened; Du movement collapsed at the 09-28 restart (F-2288, J-1692)

### What we have
D-0100's three tiers (cat/fire repair, dig/climb/feed/draw, hum/whistle/sing) built and live since 08-29
(F-0578). Tier 2 mostly doesn't fire in Du's real run for structural reasons, not bugs (F-0691/F-0719). This
plan's slug also carries a long-running actions-grammar-hardening stream (hyphen/word-boundary fixes, ~15
jobs, F-1128..F-1202) and a sleep-onset/locomotion fix arc (the event-loop freeze broken in two parts,
J-1177/J-1180/J-1184; the redirect-teleport bug fixed, J-1179; D-0224/D-0246's gates now live) that grew out
of the same dispatch code this plan owns.

### What we need
Three reads are gated on live-day/sleep accrual, none yet met: J-1182 (locomotion redirect rates, needs
>=3.00 live-days on merge 5a66504 — F-1767, not yet met), J-1187 (D-0246(b) override counts, needs >=7.00
live-days on merge 177f34c — F-1768, not yet met), J-1307 (find_cluster's new DEBUG checkpoint read across
one real sleep, restart-gated).

### What we're doing next
Re-run J-1182/J-1187/J-1307 once their respective day/sleep bars are crossed. No founder decision is
currently blocking any of the three.

