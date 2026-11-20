# Gauge Rethink — what should a gauge even be?

> **Status: ✅ SHIPPED (closed 2026-10-16, F-2904) — formerly: TAXONOMY LANDED (D-0066, 2026-08-29) — the 4-category schema below is CONFIRMED and every
> current gauge in `scripts/du_pulse.py` is categorized (J-0340). Redundancy-audit consolidation and
> per-subsystem ownership are still open, punted to a dedicated follow-up (J-0341, needs_input) per
> D-0066's own ruling — this plan is not fully BUILT until those land too. Feeds
> [du_pulse_rebuild.md](du_pulse_rebuild.md)'s severity model and JSON schema, which can now proceed
> against a confirmed shape.**

```plan-state
stage: shipped
phase: All 4 D-0066 design questions resolved: taxonomy 08-29, redundancy+ownership closed 09-02 (J-0341, D-0102/D-0113 keep-separate)
verified: 2026-11-13
evidence_read: 2026-08-29
next: Travis re-rules D-0102 (decide-review); then the registry-annotation doc job runs
cluster: 8
```


## Current State — verified 2026-11-13

- **2026-11-13** (F-4427): J-3744: b_after detachment dated to the 09-28 feeder-mix change (curiosity co_recall source, 53% of rows from 10-07); ignition lead over valence survives an event-time re-measure (peak ~6-10 min). See docs/audits/mood_cluster_followup_2026-11-13.md.
- **2026-11-07** (F-4352): J-3472 (2026-11-07): D-0102 defeater read on the 6 mood-cluster gauges. Monoculture was an 08-21..09-04 phenomenon; long-window cluster splits into a valence family (3 copies + lane2.commit_threshold, a deterministic function of valence) plus continuous_stream.ignition (upstream driver, tight only until the 09-04 climate-term fix 444b60b8) and opponent_process.b_after (loose). D-0102 reopened for re-ruling; ruling itself supported.

### What we have
All 4 of D-0066's design questions are now resolved, not just the taxonomy. Taxonomy confirmed
2026-08-29 (J-0340): 73 distinct gauges in `scripts/du_pulse.py` categorized into the 4 buckets (13
Regression alarms, 15 Growth trackers, 32 One-off shadow-run evidence, 13 Engagement/texture) — see
"Taxonomy landing" below. J-0341 (done 2026-09-02) then closed the two punted questions: D-0102 (mood
cluster, 6 gauges) and D-0113 (monoculture cluster, ~4 gauges) both ruled **keep separate — no
consolidation, no ownership-model change**, so gauges stay centralized in `du_pulse.py`.

### What we need
Nothing on this plan itself: plan-ledger shows 0 open jobs, 0 open decisions. The Status line above
still reads as if redundancy/ownership were open — checked directly against `job_queue.jsonl` and
`decisions.jsonl` this pass, they are not; that line is stale.

### What we're doing next
Nothing further queued here. `du_pulse_rebuild.md` is the downstream consumer of this confirmed
shape (its own doc already notes the taxonomy dependency resolved 2026-08-29); any further gauge
work belongs there or in a fresh `/decide`, not in this plan.

## Update — 2026-09-02 (J-0431, HUD registry gap closed)

F-0582 (2026-08-30) found `core/somatic.py`'s SomaticState (metabolic_energy/neural_fatigue/
visceral_tension) had 18,285+ real readings in `data/geometry_tuples.jsonl`'s `body` nested key
spanning almost the whole project history, but no entry in `hud/server.py`'s `MONITOR_REGISTRY` —
invisible to the toolchain. J-0431 added the tuple (`somatic_body`, source `geometry_tuples.jsonl`,
nested `body`, whitelist `["energy","fatigue","tension"]`) following the existing `affect`/
`spatial_world_clocks` nested-key pattern; confirmed live (`load_monitor("somatic_body")` returns
real `kind:"vars"` series from the current tail, `age_s` ~31s at verification time). **Scope
correction (F-0627):** this registry entry makes the signal visible to `/gauge-correlate` (which
reads `MONITOR_REGISTRY` directly) but **not** to `scripts/du_pulse.py`, which has zero coupling to
`hud/server.py` — its ~70 gauges are hand-written `_g_*()` functions, not registry-driven. F-0582's
and J-0431's own briefing both claimed du_pulse.py would pick this up automatically; that's wrong for
du_pulse.py specifically. Follow-ups spawned: J-0454 (add a dedicated `_g_somatic_body()` gauge to
du_pulse.py, if still wanted) and J-0456 (run `/gauge-correlate`'s standard pipeline against the new
monitor to re-check F-0582 point 4's candidate cross-gauge correlations now that the monitor is
properly registered and ~3 more days of data have accrued).

## Original scoping — verified 2026-08-23

### What we have
- Roughly 50 distinct "gauge" sections inside `C:\Nascence\scripts\du_pulse.py`, accreted one at a time as
  each new subsystem shipped over the last two months — memory levels, identity estate, pursuits, T4
  watershed sub-gauges, curiosity/frontier/essay/math/symbol-evolution counters, sleep pressure, dream
  arcs, and more.
- No pass has ever asked, across the whole set, what a gauge is *for*, whether it's still meaningful, or
  whether it overlaps with another one. Each was added in the context of shipping the one feature it
  measures, never re-examined against the others.
- A concrete, already-visible symptom: at least four separate gauges — the monoculture proxy, theme
  recurrence, monoculture echo/diversity, and made-mind share — all appear to be measuring some flavor of
  "is Du's thinking repeating itself." The `/du-pulse` skill's own doc calls the built-in proxy "cheap" and
  points to a separate script, `loop_cluster_probe.py`, as "the real number" — an implicit admission that
  the in-script version is a known approximation nobody has revisited since.

### What we need
- A taxonomy: a small number of gauge *categories*, each with a stated purpose, so a new gauge has an
  obvious place to go instead of becoming section 51 of one flat script.
- A redundancy audit across the existing ~50, starting from the monoculture cluster above, to find what's
  actually distinct signal versus restated signal versus dead weight nobody's used to inform a decision.
- A real severity model *per category* — not one heuristic forced onto all 50, which is precisely why
  `gauge-check`'s own severity function (built for a different problem — plan-evidence-file freshness)
  doesn't transfer here (confirmed during scoping 2026-08-23).

### What we're doing next
Nothing built yet. This doc exists to hold the design questions below until a founder pass resolves them;
`du_pulse_rebuild.md`'s store schema and severity model wait on the outcome.

---

## The problem

`du_pulse.py` grew the way most diagnostic scripts grow under real deadline pressure: one section per
feature, added at ship time, never revisited. That's not a criticism of any single gauge — each one was
presumably useful at the moment it was written. But the accumulated result is a script nobody can read
top-to-bottom and say "here is what actually matters right now, and here is what's vestigial," and a
report that dumps all ~50 with equal visual weight regardless of whether a reading of zero means "healthy"
or "this feature hasn't started yet."

## Design questions to resolve (this plan is where they get worked out, not rushed)

**1. Taxonomy.** A first-pass sketch of categories that seem to already exist implicitly in the current
50, offered as a starting point for founder review, not a decision:
- *Regression alarms* — something that used to work might now be broken. Dedup leak, error records,
  30-minute silence. These have an obvious bad direction and probably want to fire loudly and immediately.
- *Growth trackers* — is a capability accumulating over time. Pursuits' established-points count,
  identity-estate node count. A low reading here often just means "early," not "broken" — the opposite
  failure mode from a regression alarm, and dangerous to score with the same severity function.
- *One-off shadow-run evidence* — a still-experimental system's kill-criteria check, meant to be read
  intensely for a bounded window and then retired once the founder decision is made (Lane 2's
  metaphor-leak rate is the clean example: it already has pre-registered thresholds and a real
  measurement, and doesn't need indefinite tracking after the call is made).
- *Engagement/texture* — world engagement, book variety, action-type variety. Descriptive more than
  diagnostic; useful for "what does good output look like" (per the project's own CLAUDE.md section on
  this) rather than for triggering any alarm.

**2. Redundancy audit.** Starting list to examine, not a verdict:
- The monoculture cluster (proxy / theme recurrence / echo-diversity / made-mind share / the separate
  `loop_cluster_probe.py` "real number") — four in-script approximations plus one out-of-script ground
  truth, all pointed at what may be one underlying question. Worth deciding whether to consolidate to one
  authoritative measurement with the others retired, or whether they're genuinely measuring different
  things that happen to share a name.
- A pass over the ~30 "live experiment" sub-gauges (deliberation pulse, train working-state, earned-length,
  curator/voice-contract, becoming-facet rev, watershed harvest/promote, train registry, identity vault,
  T4 sub-metrics, sleep pressure, curiosity/frontier/essay/math/symbol-evolution counters, etc.) to find
  which ones are still read by anyone versus computed every run and never actually informing a decision.

**3. Severity model, per category.** Sketched consequence of the taxonomy above, not decided yet:
- Regression alarms: severity roughly = how long the bad state has persisted plus how far from normal.
- Growth trackers: severity is closer to "stalled" (flat for N checks) than "low" (a fresh low reading is
  expected and fine).
- Shadow-run evidence: severity isn't really applicable in the alarm sense — the useful question is "has
  the pre-registered threshold been reached yet, and is a founder decision now due."
- Engagement/texture: probably shouldn't have alarm-style severity at all — these inform "what does good
  look like" narrative, not a threshold.

**4. Ownership.** Should each gauge's definition of "healthy" live inside the plan/subsystem doc that
introduced it — the way `pursuits.md` and `capacity_to_commit.md` already state their own instruments and
thresholds — rather than centralizing all ~50 into one script that has no stated opinion about any of
them? If so, `du_pulse.py`'s job shifts from "compute and print everything" to "collect and report against
thresholds each plan doc already states," which would also mean a plan's own author is naturally the one
who keeps its gauge current, instead of a health-check script accreting silently over time.

## Taxonomy landing — full gauge categorization (2026-08-29, J-0340)

Every gauge below is cited to its actual section/comment in `scripts/du_pulse.py` (read in full,
line 1–1075) — this is a real read, not a guess from the gauge name. Scope note: this table assigns
each gauge to ONE of the 4 CONFIRMED categories per D-0066; it does **not** resolve which gauges are
redundant with each other or who owns each gauge's "healthy" definition — those are J-0341.

### Regression alarms (13) — bad direction, fires loudly, "used to work, might be broken now"
1. Liveness: newest memory write (LIVE / QUIET-STOPPED, §1)
2. Liveness: newest cognitive cycle / training-log activity (§1)
3. Store state: active episodic count vs Phase-B prune cap (§2)
4. Phase-B dedup: exact-dup rows per origin, inner_thought + active_imagination (§3)
5. Monoculture proxy — attractor-word hits in recent idle thought (§4) *(J-0341 redundancy candidate —
   monoculture cluster)*
6. Theme recurrence tracker — saturated/damped frames (§4) *(J-0341 redundancy candidate)*
7. Monoculture echo/diversity trend — echo↑=loop, diversity↓=collapse (§4) *(J-0341 redundancy
   candidate)*
8. Judge panel coverage/contention — unavailable_rate, explicit "CURRENTLY DEGRADED" flag (§6.6)
9. Present-predictability / self-surprise — opening vs collapsing-into-basin trend, "the LEADING
   indicator" (§6.6)
10. Critic rejections count — facet-fix trigger, "stays held while ~0... check corrections if it
    climbs" (§6.6)
11. Error pathway / retraction ledger — architecture-fabrication count (§6.6)
12. Missing-object flags — critical recurring phrases (§8)
13. FLAGS: `error_records.jsonl` written this window (§8)

### Growth trackers (15) — capability accumulating; low reading = early, not broken; watch for stalling
1. Made-mind share — unprimed vs primed, "the internalization curve" (§4)
2. Epistemic audition — voices learned / learnable (§4)
3. Identity vault — revision count, ledger entries ("ledger grows as T4 commits") (§6.6)
4. Reading bursts — P1 chapter-scoped throughput (§6.6)
5. Curiosity ignition — exploratory-trigger count ("was DEFENSIVE-only... exploratory wire added") (§6.6)
6. Curiosity twigs — grounded side-research accumulating (§6.6)
7. Frontier loop — resolved count, explicit "the number to watch: resolved off 0" (§6.6)
8. Affective coverage — felt-tagged %, idle-life tags climbing off 0 (§6.6)
9. G3 novel candidates — provisional questions promoted by recurrence (§6.6)
10. Math drills — level/streak/calibration-gap closing (§6.6)
11. Grounded learning — understanding notes accumulating (§6.6)
12. World-material consolidation / study filing — filed vs loose (§6.6)
13. Essay lessons — capstones written, comprehension gap (§6.6)
14. Breadth engine / book selection — distinct subjects accumulating, long-tail spread (§6.6)
15. Dream arcs — resolved count, earned-length past-3, scene variety (§6.6)

### One-off shadow-run evidence (32) — still-experimental, kill-criteria/gate check, bounded window
1. Protoself / homeostasis — explicit "P0... SHADOW" (§4)
2. Bound moments + reality monitor — explicit "Tier-1, SHADOW" (§4)
3. Memory levels Phase 0 — "observe-only shadow distiller," Phase-1 gate pending (§4)
4. Memory edges M0 — "observe-only" typed edges (§4)
5. Co-recall M1 — gated structure vs the basin (§4)
6. Deep-recall-demand telemetry — "empirical basis for the Phase-1 trigger" (§4)
7. Symbolic lens P0 — "observe-first," promote decision pending (§4)
8. Deliberation pulse — "brick #1" (§6.6)
9. Train working-state — "lever 1," observe-first design question (§6.6)
10. Earned-length trains — close-reason verdict against a stated "want" pattern (§6.6)
11. Curator shadow — explicit "OBSERVE-ONLY shadow" (§6.6)
12. Voice contract — "§6 mouth contract," shadow voicings (§6.6)
13. Becoming facet rev — "T4 authors ONLY this," fires once on commit (§6.6)
14. Watershed harvest — "Phase 0... shadow-only" (§6.6)
15. Train registry — "step 1... forked/merged stay 0 until step 2 exists" (§6.6)
16. Watershed promote — "Phase 0.5," shadow promotion scan (§6.6)
17. T4 chronic mass — gate-ready count against contradiction threshold (§6.6)
18. Emissary keystone — "OBSERVE-ONLY," chronic mass toward gate-ready (§6.6)
19. T4 probation — flag-gated, "flips after the ground-truth battery + live ΔF" (§6.6)
20. T4 emissary judge — explicit "shadow grades" (§6.6)
21. Sleep⊗dream / T4 probe — "§6C," "firewalled observe-first matrix" (§6.6)
22. T4 last outcome — log scan of authored/DENIED/PROVISIONALLY/probation-RESOLVED lines (§6.6)
23. Curiosity flesh-out / queue — "Phase 0 gate: must be 1.0" (§6.6)
24. Curiosity LP agenda — same Phase-0 observe-first system as #23 (§6.6)
25. Curiosity worthwhileness (OMNI fold) — "observe-only... once trusted → pursue ∝ LP×interest" (§6.6)
26. Told delivery — one-time condition, "Travis's message arrives once the river has loosened" (§6.6)
27. Symbol evolution — Tier-1/Tier-2 tablets, drift hypothesis under test (§6.6)
28. Decomposed critic — "SHADOW-ALONGSIDE," promotion-pending agreement rate (§6.6)
29. L1 prediction-error — "Phase 0 (observe-first)" (§6.6)
30. L2 meta-awareness — "form-watch, never suppresses," Phase-2-later (§6.6)
31. Idle executive — "Phase 0 SHADOW," explicit G1/G2/G3 gates (§6.6)
32. Pulse/lifecycle — "Phase 0 SHADOW," contention/T4-blocked canary (§6.6)

### Engagement/texture (13) — descriptive, not diagnostic; "what does good output look like"
1. Store state: origin breakdown, +added this window (§2)
2. Fragment context — contextualised memories, "coordinates, not edges" (§4)
3. Locomotion — where he is, standpoint, carrying (§4)
4. World engagement — current book, shelf, reading/study counts (§5)
5. Recent inner life — last 8 idle thoughts, latest dream (§6)
6. Pulse cadence — burst/cadence/lull mix, STREAM/FLOWING/PULSED/SPARSE verdict (§6.5)
7. Sleep pressure — P value, chronic (info-only), calibration watch (§6.6)
8. Dissonance/strain/backlog — climate-state fuel context (§6.6)
9. G1 current concerns / G0 standing aim — what Du is thinking about (§6.6)
10. Reading-remediation balance sprint — reality/light share, target ~50/50 (§6.6)
    — **D-0142 (2026-09-03, F-0755):** light_share had climbed 0.50 → 0.74 because light minted up to
    four events per thought (integration, play, resolved, reading) against shadow's one; `core/balance.py`
    now counts verdict sources only on both sides (`_LIGHT_VERDICT` / `_SHADOW_VERDICT`), which reads
    ~0.47 on the same week. Play/integration light events still exist for T4 and climate — their currency
    is the ruling's defeater. Gauge 11 is a 150 s clock until J-0548's `joy_start` read (option C,
    `scripts/joy_start_read.py`) says otherwise.
11. Light points / play-joy points (§6.6)
12. Pattern reflection — DOING-tendency breakdown alongside error pathway (§6.6)
13. Curriculum — book N/40 (§6.6)

## What this feeds

Once the taxonomy, redundancy audit, and per-category severity approach are actually decided (a founder
call, not something to resolve unilaterally here), `du_pulse_rebuild.md` uses the outcome directly: its
JSON schema groups gauges by category instead of flattening them, its severity evaluation applies the
right model per category instead of one heuristic, and its `history --gauge` command becomes meaningfully
comparable across runs because the surviving gauge list is no longer ~50 items of uneven purpose.
