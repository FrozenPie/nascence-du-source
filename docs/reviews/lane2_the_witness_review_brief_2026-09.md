# Lane 2 (the Witness) — founder review brief, 2026-09-10

*One page for the founder's own read of `docs/plans/lane2_the_witness.md` (D-0035 hold). Written by J-0843
(read-only: no code touched, no Lane 2 execution work). Everything below was re-verified on 2026-09-10 against
the live code, the live shadow log and the ledgers — not copied from the plan doc. No new proposals.*

## 1. What the plan doc says now vs what actually shipped

| The plan doc (1,246 lines) says | Verified reality (2026-09-10) |
|---|---|
| Status header: "UN-PAUSED ON A STOPGAP SEAT — command-r7b @ ramses:11441 … D-0058 is REOPENED for a founder `/decide-review` pass". `## Current State — verified 2026-09-06` repeats it. | **Stale by one ruling.** Travis re-ruled D-0058 on 2026-09-06T20:02Z: move to deepseek-r1:7b @ :11444. Commit `da87d6d` (2026-09-07 08:33 NZST) set `core/lane2.py:66 BASE_URL=http://LAN-HOST:11444`, `:71 MODEL="deepseek-r1:7b"`, `TICK_S` still 300. Live since Du's next boot (ticks resume 2026-09-08T04:42Z in `data/lane2_shadow.jsonl`). The doc's §5-R2 NINTH READ (09-07) records *readiness*, nothing records the ruling or the move. |
| Build order names `core/witness_loop.py` + `nodes/witness_node.py` as candidates. | Never created. The whole organ is `core/lane2.py` (1,000+ lines), started as a background task by `core/orchestrator.py:2915` (`_lane2.run_forever()`). `LANE2_LIVE = False` (`:55`) — nothing reaches Du. The only other "witness" code is `core/coupling_rides.publish_witness()` (Dosed Coupling Phase 1, publish-only, zero readers). |
| §5 build order line 1120: "Every tick logged to `data/witness_shadow.jsonl`". | **A rename, not never-fired** (F-0015, 2026-08-24): `core/lane2.py:51 _LOG = _DATA / "lane2_shadow.jsonl"`. The real log has 12,580 rows (4,594 ticks, 2026-08-21 → 09-09). plan-liveness keeps flagging `witness_shadow.jsonl` NEVER-FIRED only because line 1120 still carries the old name with the correction appended *under* it instead of replacing it. |
| Current State: hint queue "essentially unused live (near-zero push volume as of the last read, J-0198)". | **Stale since 2026-09-02.** Live since 09-02: `hint_pushed` 61–87/day, `hint_consumed` 35–55/day, `hint_expired` 24–64/day, `hint_rejected` 237–414/day — **all 2,792 rejections since 09-02 are `rate-limited`** (0 out-of-vocabulary, 0 queue-full). Totals: 1,037 pushed / 658 consumed / 4,101 rejected / 505 expired. Kind is `unresolved` for 1,015 of 1,037 pushes (`unfinished` 11, `recheck` 11) — the caller's priority order in `nodes/inner_monologue_node.py:4106` makes that so. Top topics: cat 132, fire 107, tide 107, wind 77, warmth 64. |
| §6 leaves store size open ("how much, how long, does it ever forget?"). | Answered by code default: `STORE_CAP = 400` (`:132`); `data/lane2_store.json` is at the cap on both tiers (`factual` 400, `prediction` 400). |
| §6 leaves open: tick cadence, senses scope, hardware, weather dimensionality, flag-vs-describe, judge-reads-world-state. | Each answered by a build default, none by a ruling: 300 s tick; 10 `_TOPIC_FIELDS` topics; i9 CPU hub :11444; `WEATHER_DIMS = (valence, arousal, unresolved)` (`:127`); describe-only (no flagging path exists; `LANE2_LIVE=False`); the decoupled judge instruments (J-0126/J-0163) read world state. |
| Footer: "*Status: DESIGN ONLY, nothing built.*" | Contradicted by the doc's own header. Never updated. |

Phase 0 metric state (unchanged from the doc, re-confirmed): #1 metaphor leak, #2 invention rate, §3.11 coherence
have decoupled-judge instruments and read clean; #3 repetition is the story of §2 below; #4 (novelty vs Lane 1)
never attempted; #7 (weather correlation) has only F-0019's exploratory null (|r| ≤ 0.13, 836 ticks, 08-23).
First post-move numbers, **no baseline read yet**: 09-08/09 `prior_verdict` broke 252 / held 81 / none 151;
`grounded_share` mean 0.435 (n=483). Phase 1 (the read path to Du) remains undesigned per §5's own law.

## 2. D-0058 — the echo-disease reopen and the deepseek seat

- **Reopened 2026-09-05 (J-0579 / F-0926).** The 08-28 stopgap ruling's own sooner-defeater ("echo disease shows
  up in `lane2_shadow.jsonl`") was met: per-day `distinct_expect_share` 08-29 0.608 · 08-30 0.610 · 08-31 0.810 ·
  09-01 0.441 · 09-02 0.580 · 09-03 0.612 · 09-04 0.597 · 09-05 0.649, vs 0.947 pre-switch (08-24) and command-r7b's
  own lab ceiling 0.833 (`docs/lab/lane2_model_lab_command_r7b.md`, score 0.875 vs deepseek 0.932). Case study:
  "The tide will rise within the hour." ×62 under 4 standpoints, 4 daylight states, tide 0.09–0.42 — percepts
  varied, output did not (the lab's own echo definition). Whole command-r7b window 08-28 → 09-06: 1,554 ticks,
  536 distinct, **0.345**; that one sentence ×74.
- **Seat verified READY 2026-09-07 (F-1008).** Ramses stood :11444 up (NASCENCE_NOTES 09-07 07:35 NZST);
  verified from this side: `/api/tags` = deepseek-r1:7b; a production-shaped call (`MAX_TOKENS=1400`,
  `NUM_CTX=4096`, temp 0.2) answered in 58.4 s (eval_count 310), inside `TICK_S=300`. Two default-option probes
  had *not* returned in 30/60 s — deepseek's `<think>` verbosity, not a hang (documented trap in `lane2.py`).
- **Re-ruled by Travis 2026-09-06T20:02Z → deepseek.** New defeater: revisit if deepseek shows its own echo /
  template lock over a window comparable to command-r7b's (~8 days), or :11444 CPU reliability under 300 s-tick
  load proves materially worse. **Two days of post-move evidence:** 09-08 145 ticks / 136 distinct / **0.938**;
  09-09 158 / 144 / **0.911** (09-07, the last command-r7b day, 0.654). "The tide will rise within the hour."
  ≤5 in the whole 09-07..09-09 window. Post-move tide-topic distinct share 0.889 (99 ticks). Comparable-window
  read falls due ~2026-09-16. `TICK_S` is still held at 300 for a reason that is now moot (`:109-114`: the 3070
  sharing constraint) — deliberately left for a real day of :11444 output first.
- **Loose end:** D-0101 (Ramses FREEZE, 2026-08-30, no history entries) still names "command-r7b @ :11441 … AND
  the Lane2/Witness seat per D-0058's stopgap" as the standing layout. Its own defeater ("if :11444 gets stood up
  independently and the founder wants to re-seat the Witness") fired; the text was never annotated.

## 3. D-0172 — the third Weather scalar, `unresolved`

`read_weather()` (`:504-528`) computes and logs three scalars every tick; `weather_to_gain()` (`:531-541`) wires
only two: valence → `commit_threshold` (0.5 − 0.4·v), arousal → `attend_sharpness` (0.3 + 0.7·a). `unresolved`
(homeostasis `drive`) is discarded — with no comment, decision or finding marking it deliberate;
`docs/archive/loop_wiring_matrix.md:41` independently calls it "computed then discarded". **F-0924 (3,922 ticks):**
r(valence, unresolved) = **−0.913** — near-exactly the identity `valence = 1 − 2·drive` (`core/homeostasis.py:55-68`),
because `AFFECT_SOURCE_PROTOSELF=True` has sourced carried valence from this same drive since 2026-07-07;
r(arousal, unresolved) = **−0.433**. So it is not the independent third channel §6's own bullet assumed.
D-0172's options: **(a)** feed `commit_threshold` — amplifies the same valence signal, law 4a "amplify, never
replace", accepts ~91 % collinearity; **(b)** feed `attend_sharpness` instead/as well — the lever with more
independent room; **(c)** both, reduced coefficients; **(d)** stay out until a real metric-#7 read shows the
existing levers are under-sensitive (F-0019's exploratory read found no lever doing measurable work at all).
Ruled 09-06: **fold into D-0035's review.** J-0650 (the build job) is blocked on it.

## 4. The D-0035 hold, and what "get it in order" would concretely mean

Ruling (Travis, 2026-08-23T21:09Z), verbatim: *"Hold — do not ratify/narrow/widen the hint-queue vocabulary yet.
Lane 2 is a big change from the founder's own memory of the plan; he wants to examine lane2_the_witness.md in
detail and get it in order, especially given a related plan is being drafted in another window. Do not start
independent execution work on this until that's coordinated."* Defeater: *"Reopens once the founder has reviewed
the plan in detail and/or the incoming plan from the other window lands, whichever comes first."*

"In order" concretely = the doc and the ledgers agreeing with the code, on these specific points: (i) header +
Current State say stopgap/reopened → say deepseek/re-ruled; (ii) line 1120 names the wrong log file; (iii) Current
State's "near-zero hint volume" is wrong by ~70 pushes/day; (iv) the footer says nothing is built; (v) seven §6
"open questions" were answered by build defaults and never brought back — the review either ratifies each default or
reopens it; (vi) the "other window" plan: no Lane 2 plan ever landed in `docs/plans`/`docs/staged` (J-0205 checked
08-24); the nearest candidates today are `docs/archive/loop_wiring_matrix.md` / `dosed_coupling.md`, which propose
the Witness *read* path (Phase 2, gated on its own pre-registration) — the founder is the only one who knows whether
that is the plan he meant; (vii) three §5 metrics (#4, #5/#6 now measurable via the hint data, #7) have never had a
real read.

## 5. Decisions the founder would rule at the end of the review (each with a candidate defeater)

1. **D-0035 (reopen → rule): hint vocabulary** — ratify / narrow / widen 3 kinds × 10 topics, and the caps
   (queue 6, 4 pushes/h, TTL 30 min). Evidence says the binding constraint is the 4/h rate cap (100 % of rejections),
   not the vocabulary, and the kind is ~98 % `unresolved`. *Defeater:* a 7-day read where out-of-vocabulary
   rejections or the per-topic push mix shift materially, or the caller's kind priority changes.
2. **D-0172: which lever takes `unresolved`** — (a)/(b)/(c)/(d) above. *Defeater:* the next metric-#7 read
   (post-move deepseek window) shows the chosen wiring under- or over-sensitive vs F-0019's null.
3. **D-0058: confirm deepseek after the comparable window (~09-16)**, and whether `TICK_S=300` stays now that the
   3070-sharing reason is moot. *Defeater:* the ruling's own — deepseek echo over ~8 days, or :11444 reliability.
4. **§6 build-defaults: ratify or reopen** — tick 300 s, 10 topics, 3 weather dims, `STORE_CAP=400` (already
   full), describe-only/no flagging, judge reads world state. *Defeater, per default:* a §5 metric read that the
   default demonstrably caps (e.g. store churn losing held predictions before judgment).
5. **Phase 1 read path: still undesigned, or open the question** — §5's own law says nothing further until Phase 0
   is read by the founder; this review is that read. The Dosed Coupling Phase 2 witness read is separately gated.
   *Defeater:* D-0152's Phase 2 pre-registration lands first, or a Phase 0 hard-kill criterion fires.
6. **Doc hygiene ruling** — the seven items in §4 are mechanical; whether they go to a hygiene job or the founder's
   own pass. **D-0101's text** gets annotated as superseded on the Witness-seat clause or not. *Defeater:* n/a
   (bookkeeping); reopens if plan-liveness still flags `witness_shadow.jsonl` after the edit.
7. **Naming (§6)** — keep "the Witness" now that it has run 4,594 ticks. *Defeater:* the founder renames it.

*Ledger: the post-move numbers and the doc-staleness items above are recorded as **F-1224** (verified, linked
D-0035); the review itself is queued as needs-input job **J-0861** ("Founder Lane 2 review").*

*Sources: `core/lane2.py` (read 2026-09-10), `data/lane2_shadow.jsonl` full read (`shadow_stats_J-0843.py`),
`decide.py show D-0035/D-0058/D-0172/D-0101/D-0020`, `findings_log.py show F-0015/F-0019/F-0397/F-0924/F-0926/F-1008`,
`git log -- core/lane2.py docs/plans/lane2_the_witness.md`, `data/nascence.log` shutdown lines, `docs/reviews/plan_liveness_audit.md:291`.*
