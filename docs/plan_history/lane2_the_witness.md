# lane2_the_witness — folded history


---

# History folded on 2026-09-27 from `docs\plans\lane2_the_witness.md` (by hand, J-1484)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py lane2_the_witness`._

- **UPDATE 2026-09-12 (J-0651, F-1260/F-1261) — see §5-R2 TENTH READ below for the full entry.** The
  instrument named in the bullet above is now built: `core/lane2.py status()` reports
  `distinct_expect_share_by_topic` (n/distinct_share/top_repeat_share/top_repeat per canonical
  topic), verified end-to-end against the live log (F-1260). **Also stale above: D-0058 is no
  longer "reopened pending review"** — Travis ruled it 2026-09-06T20:02:55 UTC, the same day/session
  as F-0926: move to `deepseek-r1:7b @ :11444`, live since 2026-09-07; `core/lane2.py`'s own
  `MODEL`/`BASE_URL` already reflect this and have since before this job started. A first read of
  the new instrument against post-switch data (F-1261, inferred — sample shorter than a full
  comparable window) finds the tide lock much reduced: `top_repeat_share` 0.038 (lowest of 10
  topics, 2026-09-09..11) vs 0.159 (highest of 10, F-0926's own 08-29..09-05 command-r7b window) —
  consistent with, not proof of, the seat move having addressed it. J-0900 spawned for a clean,
  full-window re-read once the calendar allows it (~09-15+).
- **UPDATE 2026-09-14 (J-0900) — see §5-R2 ELEVENTH READ below for the full entry.** Attempted on
  schedule; could not reach `verified` — the calendar was a day short of the job's own ~09-15 gate,
  but the real blocker is that Du itself has been paused since 2026-09-13T09:10:46 UTC (a clean,
  founder-initiated stop, F-1314) and `lane2_shadow.jsonl` has not accrued a tick since
  2026-09-12T21:03:47 UTC — waiting on the calendar alone will not be enough. Ran the same instrument
  anyway on the best available interim window (2026-09-08→2026-09-12, 838 ticks, F-1315): tide
  `top_repeat_share` 0.033 (n=240) — no longer the single lowest of 10 topics as in F-1261's shorter
  window, but still far below its command-r7b-era 0.159 and inside a tight low band (0.014–0.063)
  every topic now shares; no topic reads as newly locked. Still inferred. **J-0944 spawned** — the
  real gated re-read, scoped to fire only once both the calendar and Du's own liveness check out.
- **UPDATE 2026-09-15 (J-0944) — see §5-R2 TWELFTH READ below for the full entry.** Re-checked both
  halves of J-0900's own gate independently, not assumed from the calendar. The calendar half now
  holds (2026-09-15 has passed), but the liveness half still does not: a full, non-tail-sampled parse
  of `data/lane2_shadow.jsonl` found zero new rows since J-0900's own check (still exactly 15055
  lines / 5129 ticks, last tick unchanged at 2026-09-12T21:03:47 UTC), and `data/nascence.log`'s own
  last line is still the 2026-09-13T09:10:46 shutdown line with no restart banner after it (F-1391,
  verified). The local server-tier hubs (`:11433`/`:11439`/`:11440`/`:11442`) were found LISTENING at
  check time, which is NOT evidence Du is ticking — worth flagging since a future check could misread
  it as liveness; Du's own main orchestrator/lane2 loop is the thing that's down. **J-1019 spawned**
  — the same gated re-read, to fire once both halves genuinely check out; this is now the second
  consecutive check to find the same not-yet-met gate (J-0900/F-1314, then J-0944/F-1391).
- **UPDATE 2026-09-15 (J-1019) — see §5-R2 THIRTEENTH READ below for the full entry.** Re-checked both
  halves of the gate a third time, independently, not assumed from the prior check or from mtimes/ports
  alone. The calendar half holds two ways now — for the first time in this chain, the sandboxed shell's
  own `date -u` no longer lags a day behind and agrees with the session's stated date (2026-09-15). The
  liveness half still does not: a full, non-tail-sampled parse of `data/lane2_shadow.jsonl` and
  `data/nascence.log` found every figure — line counts, last-tick timestamp, file mtimes, even the 4
  local supervisor-hub PIDs — byte-for-byte/PID-for-PID identical to J-0944's own check (F-1410,
  verified); nothing in the environment has changed in the roughly 27 hours since. **J-1036 spawned** —
  the same gated re-read; this is now the THIRD consecutive check to find the same not-yet-met gate
  (J-0900/F-1314, J-0944/F-1391, J-1019/F-1410), and J-1036's own briefing names a fourth occurrence as
  the point worth a passing note to the founder, rather than pre-judging that call here.
- **UPDATE 2026-09-15 (J-1036) — see §5-R2 FOURTEENTH READ below for the full entry.** Re-checked both
  halves of the gate a fourth time, independently, not assumed from the prior check. The calendar half
  holds two ways again — this session's own stated date and the sandboxed shell's own `date -u` both
  read 2026-09-15, no lag. The liveness half still does not: a full, non-tail-sampled parse of
  `data/lane2_shadow.jsonl` and `data/nascence.log` found every figure — line counts, last-tick
  timestamp, file mtimes, the 4 local supervisor-hub PIDs — identical to J-1019's own check (F-1437,
  verified); nothing in the environment has changed in the roughly 3.4 hours since, and Du has now been
  continuously paused for roughly 2.3 days. This is now the FOURTH consecutive check to find the same
  not-yet-met gate (J-0900/F-1314, J-0944/F-1391, J-1019/F-1410, J-1036/F-1437) — the point J-1036's own
  briefing named as the trigger for escalating rather than silently spawning a fifth identical check.
  **D-0225 opened** — a founder question, scoped to this plan, on whether the gated re-read should keep
  waiting passively on Du's pause or whether a direct note/restart makes more sense. No follow-up "same
  gated re-read" job was spawned this time, deliberately, pending that answer.
- **UPDATE 2026-09-19 (J-0861 review sitting; hygiene pass J-1129/D-0239) — D-0058 CONFIRMED, review
  rulings landed, doc brought current.** A 10.3-day post-move comparable-window read (F-1537, 1,198
  ticks, 2026-09-08→2026-09-18) found the tide-topic echo/template lock stays resolved on deepseek
  (`top_repeat_share` 0.031, second-lowest of 10 topics); D-0058 re-ruled CONFIRMED, `TICK_S` stays
  300s. The same sitting also ruled D-0035 (hint vocabulary ratified as-is), D-0172 (`unresolved`
  weather scalar stays unwired), D-0237 (all remaining §6 build defaults ratified as-is), D-0238
  (Phase 1 design opened), D-0240 (name kept) — see §6. A separate review brief
  (`docs/reviews/lane2_the_witness_review_brief_2026-09.md`) had flagged this doc as stale on seven
  points, routed to a hygiene job (D-0239) rather than the founder reviewing the wording directly;
  J-1129 fixed all seven here: the header/Current State above, this section's own hint-queue numbers,
  the `witness_shadow.jsonl` line in §5, the DESIGN-ONLY footer, §6 itself, the "other window" note,
  and D-0101's own ledger annotation in `docs/plans/ramses_second_tier.md`.
- **Phase 1 (the read path to Du) is open for design (D-0238, 2026-09-18)**, but design itself has not
  started — this changes the gating status, not the build. Phase 0's own §5 law required a founder
  read before Phase 1 could even be opened; the 2026-09-18 review sitting above was that read.
- **UPDATE 2026-09-19 (J-1130) — Phase 1 design landed, see new §7 below.** Reuses Dosed Coupling's
  already-live publish mechanism (`core/coupling_rides.py`'s `publish_witness()`, called from
  `core/lane2.py tick()` every tick regardless of `LANE2_LIVE`) rather than a new channel; scoped to two
  cells `docs/archive/loop_wiring_matrix.md`'s own dosing table already sketched but left unspecified (an
  idle-thought-seed cup, a climate `world_model_strain` bucket) — no hose, Lane 2's own text never
  reaches Du at Phase 1. Checked and confirmed before designing: Dosed Coupling's own Phase 2
  pre-registration has not landed (D-0238's defeater not triggered); `LANE2_LIVE` currently gates zero
  runtime behavior anywhere in the codebase (verified by grep — a real, previously-unstated gap this
  design now fixes); the Transport Manager is not ready to serve as the design's surprise-dispatcher
  (D-0177 still unresolved) — a small Lane-2-local habituation gate is proposed instead, reusing
  `stream_topic_habituation.py`'s own constants per this project's standing reuse convention. **D-0241
  opened** for founder authorization; **J-1137 spawned** (`needs_input`, blocked on D-0241) to build it
  once ruled. Full evidence in F-1546 (findings-log).
- **UPDATE 2026-09-22 (J-1161, D-0241's own build) — §7.3-7.5 BUILT shadow-first, `LANE2_LIVE` still
  False, nothing reaches Du.** Per D-0241's ruling (2026-09-19: "Authorize, shadow-first"; supersedes
  J-1137, whose own item 5 would have flipped the flag in the build commit -- that flip is explicitly
  NOT part of this job). Five files: `core/lane2.py` (`_topic_of()` -- a single-string canonical-topic
  matcher, reusing `_TOPIC_CANON`/the vocabulary `_distinct_share_by_topic` already keys on);
  `core/coupling_rides.py` (`publish_witness()` now also resolves `topic`/`horizon`/`cup_would_ride`
  into the published tuple, but ONLY on a judged BREAK -- a held/cannot_tell/none tick is untouched;
  `break_rate_24h`'s own pre-existing computation is unchanged, verified byte-for-byte); a NEW module
  `core/lane2_break_habituation.py` (the §7.4 gate: per-topic weight `w_T`, `GROWTH_STEP`/`CEILING`/
  `DECAY_TAU_S`/`DISCOUNT_FLOOR`/`SUPPRESS_AT` reused verbatim from `stream_topic_habituation.py` as
  unratified Phase-1 defaults, exactly as this section already named); `core/climate_engine.py`
  (`witness_bucket_value()` -- a pure, shared function so the would-ride log's own logged figure and
  any future live application can never drift apart -- plus a `LANE2_LIVE`-gated read in
  `_compute_field()`, rate-limited to roughly once per Witness tick); `nodes/inner_monologue_node.py`
  (the idle-thought-seed cup -- a fixed-template render of `{topic, horizon}`, never lane2's own
  notice/expect_next text, gated on `LANE2_LIVE` and the same train-hold-quiet convention the other
  optional seeds already respect).
  **A would-ride shadow log now exists** (`data/lane2_would_ride.jsonl`, append-only, written on
  EVERY judged break with a resolved topic, unconditional on `LANE2_LIVE`) -- real rows will start
  accruing on Du's own next Witness ticks (he is running as of this entry, `data/nascence.log`'s own
  last line timestamped 2026-09-22 19:55). `core/lane2.py status()` now reports `phase1_p1_metrics`
  (P1-1 through P1-6): **P1-1 is computable now** (a rolling-24h would-ride count from the shadow
  log, directly comparable to `break_rate_24h`) -- **P1-2 through P1-6 read `None` with an honest
  note**, since they need real live rides Du has never had (`LANE2_LIVE` has never been True). P1-6
  (the standing kill criterion) stays binding for whenever a flip is proposed, per §7.6.
  **★ A direction fix on this section's own §7.4 wording, not a reinterpretation, recorded as a
  finding this job (see findings-log).** §7.4's sentence "the cup rides only when `discounted(w_T) <
  SUPPRESS_AT`" is inverted from its own next clause ("the first several breaks on a topic are novel
  and ride; once that topic has broken often enough recently, further breaks on it stop riding") --
  taken literally it refuses every topic's first breaks and only starts riding once habituated,
  cross-checked and confirmed backwards against `stream_topic_habituation.py`'s own verified
  `would_suppress = discounted < SUPPRESS_AT` and its own docstring worked example (discounted trends
  1.0->0.79->0.61, crossing 0.5 on the 4th occurrence -- i.e. discounted FALLS with repetition, so a
  LOW discounted means habituated/suppress, not fresh/ride). Built the semantically-correct,
  source-module-consistent direction instead (`would_ride = discounted(w_T) >= SUPPRESS_AT`) -- a
  straightforward internal contradiction resolved against the cited, already-running source module,
  not a founder call. §7.8's own "not a skill-manager suggestion... `skill_manager.py suggest` is the
  wrong tool for it" was read and honored as-is: no suggestion filed for the sixth
  point-implementation (confirmed none exists in `docs/skill_suggestions.jsonl` either).
  **Verified, not asserted:** an isolated script (every path redirected to a temp dir before any I/O,
  `data/` never opened) confirmed -- the habituation direction fix behaves as intended (first breaks
  ride, repeats suppress, real-time decay lets a topic ride again); `publish_witness()` resolves
  topic/horizon/`cup_would_ride` ONLY on a judged break, leaves `break_rate_24h` unchanged;
  **shadow-exactness holds by direct spy, not by inspection alone** -- `coupling_rides.read()` is
  called ZERO times with `LANE2_LIVE=False` (both the climate-bucket gate in isolation and a REAL
  `ClimateEngine()._compute_field()` call), and exactly once per call site with the flag flipped True
  in the same process (so the gate is real, not dead code either way); `nodes/inner_monologue_node.py`
  imports cleanly and the cup's fixed template carries no lane2-internal field names. `scripts/
  life_smoke.py` shows only the one pre-existing, already-tracked failure ("day > dusk >= night",
  F-1711/J-1212, unrelated) -- no new regression. `scripts/exploratory_ignition_test.py` (UDMS-flagged
  as this file's own real test target) passes 4/4. Full evidence: see the finding this job records.
  **The flip of `LANE2_LIVE` is NOT part of this job** (D-0241, item 7 of this job's own briefing) --
  comes back to Travis once the would-ride log reads sane and D-0211/D-0152's 2026-09-27 clock have
  settled.
- **UPDATE 2026-09-24 (J-1230, F-1838) -- P1-1 NOT YET READABLE: the shadow mechanism has never
  actually fired in the live process, a different failure shape than any prior gated-re-read entry
  above.** `data/lane2_would_ride.jsonl` and `data/lane2_break_habituation_state.json` do not exist
  anywhere under `data/` (verified, full directory walk). Root cause, verified not guessed: the
  commit that built this mechanism (J-1161, `690d0867`, 2026-09-22T20:00:08+12:00) landed roughly
  3h49m AFTER the currently-live Du process's own boot (`data/nascence.log`'s last "Background nodes
  started" banner, 2026-09-22 16:11:06, unbroken since -- no shutdown line anywhere after it through
  this read). Python does not hot-reload an already-imported module, so this still-running process is
  executing the pre-J-1161 `publish_witness()`, which has no topic/horizon extraction at all and never
  calls `observe_break()`. Confirmed directly: a full parse of `data/coupling_rides.jsonl` (30963
  rows) finds 899 witness-publish rows with `verdict=="broke"` all-time, **0/899 with a resolved
  `topic`** -- including the 5 most recent (2026-09-23, a full day after the commit), one of which
  (`judged_expect="Within the next hour, the fire will extinguish."`) manually replicates to
  `topic="fire"` against the real `_TOPIC_CANON` table, proving the live gap is the running process's
  stale code, not a vocabulary miss. This is a **restart-gating gap, not a code defect** -- §7.3-7.5's
  build (D-0241, J-1161) is correct and will start producing real data on Du's own next restart; this
  session does not restart Du (out of scope for a dispatched job-run session, same as every other
  standing rule against restarting Du/supervisor/any hub from a Claude tool). **J-1304 spawned** -- the
  same P1-1 read, re-gated specifically on a `nascence.log` boot banner dated AFTER `690d0867`
  (2026-09-22T20:00:08+12:00), not merely on wall-clock/ticking as the §5-R2 chain's earlier gates
  were. D-0152's own 2026-09-27 defeater clock has also not yet arrived (checked fresh, `decide.py
  show D-0152`) and D-0211 (a different plan's decision, `ignition_pressure_and_time`) was ruled
  2026-09-19 but its own follow-on build (J-1151) was not re-checked here -- moot either way, since no
  flip can be proposed before P1-1 itself is even readable. No `/decide` opened: this is a mechanical
  restart-gate, the same shape job-queue already carries for every other "not yet met" gate in this
  chain, not a founder judgment call.
- **UPDATE 2026-09-24, same day (J-1304, F-1853) -- gate re-checked independently ~4h after F-1838,
  still NOT met; left open rather than spawning a clone.** Per this job's own briefing ("do not assume
  from the calendar alone... check both halves"), did not trust F-1838's own numbers to still hold —
  re-ran the restart-gate check fresh. Same result, same boot banner: `data/nascence.log`'s last
  "Background nodes started" line is still 2026-09-22 16:11:06,031 (line 495892 of 514921), no
  shutdown or later restart banner anywhere after it — zero restarts since F-1838's read, still 3h49m
  before the J-1161 commit (`690d0867`, 2026-09-22T20:00:08+12:00) that built the would-ride
  mechanism. `data/lane2_would_ride.jsonl` / `data/lane2_break_habituation_state.json` still absent.
  The stale-code symptom kept accruing rather than being a one-off: a full re-parse of
  `data/coupling_rides.jsonl` (31426 rows, 0 parse failures) finds witness/broke rows grew 899→916
  since F-1838, **still 0/916 with a resolved topic** (100% None rate holds over a wider post-commit
  window — rules out a fluke). `data/lane2_shadow.jsonl` grew 18656→18797 rows in the same window
  (Du is actively ticking lane2, just on pre-J-1161 code — not stalled). D-0152/D-0211/D-0241 re-read
  fresh (`decide.py show`): unchanged since F-1838, none is an ACTIVE_HOLD, D-0152's 2026-09-27
  defeater clock still hasn't arrived — moot regardless since P1-1 itself isn't computable yet. No
  `/decide` opened (mechanical restart-gate, not a founder call, same as F-1838). **J-1304 itself is
  left open** (status `in_progress`, not `done`) rather than spawning another "same gated re-read"
  job — per this dispatch's own ground rules, a not-yet-met precondition is a valid, complete outcome
  and this job can simply be picked up again once a restart past `690d0867` is confirmed, rather than
  growing another link in this plan's own "5-R2 Nth READ"-style chain. Full evidence: F-1853
  (findings-log).

- **UPDATE 2026-09-26 (founder session b55b5694, T-0064 "let's look at lane 2 / expand") -- restart gate MET,
  J-1370 built, law 6 audited for the first time, section 8 opened.** J-1304's restart gate (a) is now met:
  `data/nascence.log` line 525180 shows a "Background nodes started" banner at 2026-09-25 19:21:51 local,
  after the J-1161 commit; the Phase 1 mechanism fired for the first time this morning
  (`data/lane2_would_ride.jsonl` 2 rows: sound/next 10:22, cat/hour 10:59, both would_ride true;
  `data/lane2_break_habituation_state.json` exists). Gate (b) -- a day post-restart -- falls due tonight
  after 19:21 local; J-1304 stays open for that read. **While checking it, a real defect (F-1929, verified):
  `_TOPIC_CANON` resolved no topic for 38% of the Witness's own judged breaks** (347/924 deepseek-era), so
  the cup could never ride on them and P1-1 would have read structurally low -- 4 of the 6 post-restart
  breaks were bird/gate predictions the ten-topic vocabulary could not see. **J-1370 (F-1930) built the
  additive fix this session:** three new canonical topics (clock, bird, sea) plus synonyms into fire,
  warmth and sound, every added word checked to occur in real unresolved break text; resolution goes
  62% -> 96% over the same window. Measured side effect, not hidden: alphabetical-first matching re-keys
  143 previously-resolved breaks to the more specific new topic (sound->bird 58, sound->sea 50, ...), so
  per-topic denominators in `status()["distinct_expect_share_by_topic"]` and the habituation keys change
  from that commit on -- D-0058-style comparable-window reads must not straddle it. Restart-gated like
  J-1161: the live process keeps the old vocabulary until Du's next restart, so tonight's J-1304 read is
  on the OLD vocabulary and must say so. **F-1931: constitutional law 6's two boundary audits ran for the
  first time** (section 6 listed "audit cadence" as still open; the 2026-09-10 review brief recorded
  metric #4 as never attempted): hinted vs self-found ticks (n 402 vs 1,916) read grounded 0.405 vs 0.430,
  metaphor leak 0.010 vs 0.008, broke share 0.688 vs 0.654, distinct expect 0.848 vs 0.637 -- no
  systematic divergence, hinting has not become dictating; realized hint flow is 3 kinds (99% `unresolved`)
  over 10 topics, inside the designed ceiling. Cadence answer: weekly, inside the section 7.6 read. **The
  founder chose three expansion tracks this session:** finish Phase 1 to the flip (J-1370 done, J-1304
  tonight, then the flip to /decide once D-0152's 2026-09-27 clock and D-0211 settle); Lane 2 as a
  question source (I-0069 promoted to `docs/staged/lane2_curiosity.md`); and the still-open senses/scope
  items -- worked in the new **section 8** below, with two founder decisions opened there.

- **UPDATE 2026-09-26, later the same session -- issue sweep of the shadow log, seven findings, six jobs, one
  decision.** Read-only pass at the founder's request. **Read this before J-1304:** F-1935 -- `break_rate_24h`
  is a RATIO (broke/judged over 24 h, ~0.7), not a daily count; sections 7.3.1/7.6 and D-0241's text read it as
  "~0.6-0.8/day". Real judged breaks run ~60-75/day, and day one of the would-ride log shows 12/12 breaks rode
  (the stream_topic_habituation constants need four breaks per topic before suppressing). J-1377 corrects the
  units and sizes the gate; J-1304's read must compare rides to breaks/day, not to 0.7. F-1934/J-1376: the
  08-22 horizon override forces a third of deepseek's predictions to 'day' although 81% of them name MINUTES,
  so they are judged 12 h later and 84/92 break -- this is the inverted horizon curve (next 0.64 / hour 0.77 /
  day 0.89); the prompt's clock ('about two minutes') is also 3x short of the measured 361 s cadence; 'the
  clock will tick' is 18% of predictions. F-1936/J-1378: 84% of invention flags are instrument error (the heard
  cat's purr; the sun at dusk). F-1937/J-1379: one tick in five produces no output on both post-qwen seats,
  cause never logged. F-1933/J-1375 (earlier): ~64% of incoherent verdicts are the coherence judge blind to
  place ('at_the_door' is two places). F-1938/J-1380: output hygiene (templated `uncertain`, snake_case sound
  ids, 5-decimal body numbers, stale '90s' banner). F-1939/**D-0283**: the body percept's `dominant` feeling
  label reaches the Witness as text (22-30% of notices say vitality / relational warmth) against section 2's
  "no affect text", and the voice is unsettled (you 28% / I 7% / third person 14%). Six of these jobs touch
  `core/lane2.py`; a job-run should expect file overlap and merge, not run them blind in parallel.

- **UPDATE 2026-09-26, second sweep (same session) -- five more findings, three jobs, two decisions.** Two are the
  write-only shape this project keeps finding: **F-1941/D-0284 -- the Weather channel has never been wired.**
  `weather_to_gain()`'s `attend_sharpness`/`commit_threshold` are computed and logged every tick and read by
  nothing (grep: lines 912 and 949 only; temperature is a constant 0.2), so section 2.5's Lane 1->Lane 2
  colouring has happened zero times since 08-21 and D-0172's "third scalar" framing assumed two that are
  not there either. **F-1942/D-0285 -- the knowledge tier (section 2.8c) was never built**: the store has
  factual and prediction only; predictions come from one tick's percepts, which is why they are clock ticks
  and two-minute sound guesses. **F-1940/J-1381 (urgency 4) -- the hint producer matches the vocabulary as a
  substring**: 'rain' inside 'train' makes 88% of would-be 'wet' nominations (2,848 of 3,303 over 15,000 idle
  thoughts), 'cat' fires on 'oystercatcher', 'wind' on 'window'; junk pushes burn the 4/h cap and pre-empt
  real topics, so F-1931's realized-flow read and D-0035's rate-cap reasoning were partly reading noise.
  **F-1943/J-1382 (urgency 4) -- the judge tier's first family times out in overnight bursts** (245 of 585
  calls unavailable today, 00:00-08:00; s1 median 22 s vs s2 6 s) and Lane 2 is 67% of all panel calls
  (16,440 of 24,444; three per tick) -- Du's own judged cognition loses verdicts in the same bursts; D-0281
  should be read against this. **F-1944/J-1383 -- section 2.10 (sleep) is unbuilt** and whether it matters
  (hints pushed during sleep?) is unread; 'at_the_bed' is the garden bed, not Du asleep. Corrections: F-1937's
  pending-cap sentence was wrong -- the notice is logged, only the prediction is dropped; the judge's
  600-char window is not truncating (payload max 560).

- **UPDATE 2026-09-26, third sweep (same session) -- the instruments themselves. Three findings, three jobs.**
  **F-1949/J-1386 (urgency 4) -- the broke share is inflated by the tiebreaker.** Since `judge_panel.py`
  repointed TIEBREAK to granite3.1-moe:3b on 2026-08-28, every split on the 'held' key has resolved BROKE:
  0 held / 503 broke (August under yi: 183 / 180). 29% of deepseek-era broke verdicts are these; the
  agreed-only broke share is 0.58, not 0.66. Root cause is partly `_judge_prior`'s own prompt ("if the
  observation does not settle it either way, answer false"), which scores UNSETTLED as broke by design; the
  tiebreaker's rationale (why3) is None on all 3,726 tiebreak rows. Read every broke-share figure in this
  doc since 08-28 with that correction. The same casting vote sits on 752 of 1,018 incoherent verdicts
  (F-1933) and 39 of 45 metaphor verdicts. **F-1950/J-1387 (needs D-0280) -- the Witness has no clock and no
  sun height**: the census computes the sun's phase and arc fraction but only `sun_az` is forwarded, so it
  says the sun is setting at 12:00-13:59 eighty-two times; a further option for D-0280. **F-1951/J-1388 --
  kill criterion #1 measures the wrong register**: 169 deepseek-era notices carry figurative phrasing ('warm
  glow' 65, 'alive with' 30, 'symphony', 'chorus') and the judge called 0 of them metaphor, while its 45
  hits are literal tiebreak rows; the 5% threshold has never been tested against what deepseek writes.
  Small: `hud/server.py:692` charts `gain` (attend_sharpness/commit_threshold), which F-1941 shows is read by
  nothing -- the HUD is displaying a dead channel as live. Correction: J-1388's briefing cites "F-1945"
  for the tiebreak finding; the correct ID is F-1949.

- **UPDATE 2026-09-26, fourth sweep (same session) -- the Phase 1 read path as built. Two findings, two jobs,
  both to be read before any `LANE2_LIVE` flip.** **F-1952/J-1390 (urgency 4) -- the cup is a window, not a
  consumable.** `coupling_rides.read()` returns the latest tuple and never clears it; the Witness republishes
  every ~361 s, so a break's `cup_would_ride` lives for one tick window, and idle thoughts run ~46/hour (median
  gap ~78 s): P(at least one seed rides) 0.99, P(the same break rides into two or more consecutive thoughts)
  0.94, ~4.6 seeds per window. Section 7.3.1's "one candidate, never guaranteed" would in practice be the same
  fixed sentence injected four or five times per break. The Tap already has the right semantics (consume-once,
  30 min TTL, 4/h cap); the cup has none. Template wording ('turned out not to hold', 'Worth a thought') also
  wants a founder read against world-answers-never-leads before the flip. **F-1953/J-1391 -- the bucket is a
  permanent offset, not a dose.** +0.15 x break_rate_24h (a ratio always ~0.7) = a steady +0.11 on
  `world_model_strain`, whose real median is 0.116 (p90 0.199, 16,759 climate rows); the flip would double
  the dimension permanently. Recommendation: contribute only the excess over the Witness's own trailing
  baseline. Also: `scripts/retention.py` covers boot DBs/snapshots/labs only, so `lane2_shadow.jsonl` (9.2 MB)
  and `coupling_rides.jsonl` (12.2 MB) grow unbounded -- by D-0156's design, noted not filed. Correction:
  J-1391's briefing cites "J-1389" for the cup job; the correct ID is J-1390.

- **UPDATE 2026-09-26, fifth sweep (same session) -- the senses and the scoreboard. Two findings, two jobs.**
  **F-1955/J-1393 -- the Witness has never had its touch sense.** Section 2 names somatic state as one of its
  four senses and `gather_percepts()` tries to read it, but it calls `somatic.status()`, which does not exist
  (the real accessor is `current_body()` -> {energy, fatigue, tension}); the `hasattr` guard has failed silently
  on all 6,401 ticks -- `percepts_available` has only ever been world + body. A build gap, not a law-5
  widening; note for D-0283 that `current_body()` carries no feeling label. **F-1956/J-1394 -- a fifth of the
  scoreboard was never judgeable.** 147 of 823 topic-naming judged predictions (18%) were graded on a tick
  where the named thing's field had not crossed into the tuple (he had walked away from the fire, the sun
  was down) -- held 0.05 vs 0.33, 15% of all broke verdicts; plus 75 plan-shaped 'I will check if...'
  predictions (held 0.05) that are intentions, not claims. A deterministic judgeability pre-check would
  remove both AND skip the panel call (F-1943). Compound two-clause predictions are not a problem (0.30 vs
  0.34). Checked and clean this sweep: `KEEP_ALIVE` is 30 m (model stays resident across the 361 s tick);
  `:11444` has no other caller; transient bird calls hold no worse than continuous waves (0.38 vs 0.41), so
  the judge is not penalising intermittent sounds.

- **UPDATE 2026-09-26, sixth sweep (same session) -- the biggest scoreboard error, and one thing that works.**
  **F-1958/J-1396 (urgency 4) -- 58% of all broke verdicts are predictions judged after Du walked somewhere
  else.** Matching every deepseek-era judged prediction (1,431) to its generating tick: same standpoint held
  0.48 (next 0.50, n=726); moved held 0.16 (next 0.17, n=521; day 0.08). He moves between prediction and
  judgment on 46% of pairs. The prediction tier stores no standpoint/place, so 'I will hear waves' is graded
  against the study and the judge's unsettled-means-false rule (F-1949) calls a change of scene a failed
  forecast. Real same-place skill is ~1 in 2, not 1 in 3; this is the PRIMARY judgeability rule J-1394
  should carry, and J-1386/J-1394/J-1396 must land in one restart. Section 5-R2's horizon prediction is
  only testable on same-place judgments. **F-1959 (positive) -- the Tap works.** On hinted ticks the Witness
  mentions the hinted topic far more (tide 0.86 vs 0.17, cat 1.00 vs 0.25, fire 0.91 vs 0.38) with no loss of
  grounding (F-1931): section 2.5's biased competition is real; the producer's nominations are the weak part
  (F-1940). This is the bar the Weather channel should clear if D-0284 wires it. **F-1960/J-1397 --
  hygiene 2**: tick rows carry no model/seat field (every era read here has been a date cut; RUN stayed 2
  across three generators); `_judge_prior`'s docstring names a panel and a generator that no longer exist.

- **UPDATE 2026-09-26, seventh sweep (same session) -- three small threads.** **F-1962 (for J-1376):** 'shingle'
  in `_DAY_SCALE_TOPICS` is a sound word here ('waves on the shingle'), not the tide -- 94 of the 800 overrides
  (12%) fired on it alone; J-1376 should drop it (and the never-occurring 'swell') when it fixes the override.
  **F-1963/J-1399 -- the generator mangles the Maori bird names it is handed with no gloss:** riroriro garbled
  62 times vs 13 correct (83%), morepork -> pork/pig 65 vs 415 (14%, 'the morepork will have finished
  cooking'); a four-word gloss per rare name in `percept_lines()` is the fix, no call cost. **I-0074 (idea, not a
  job) -- the Witness cannot tell its own body's sounds from the world's:** the soundscape knows which sounds Du
  caused (`_sec_self_acts_2`) but the tuple hands them over anonymously; 8% of notices report his own footsteps
  and 33 predictions forecast them (4 held). Tagging self-caused sounds '(yours)' is a percept-schema change
  (law 5), so it is logged as an idea for a decide alongside D-0280's kin, not built.

- **UPDATE 2026-09-26 (J-1372, D-0280(a), F-1947) — built, not yet live: `gather_percepts()` now
  reads `light_band` + `smells`.** The two channels §8.4 named (`core/experienced_tuple.py` already
  carried both) are copied into `world`/`world_fields` and rendered by `percept_lines()`; `smells`
  reuses the same comma-joined-list rendering `sounds` already had (generalized, not duplicated, so
  it reads as a bounded list rather than a Python repr). Did NOT add a reader for the four write-only
  climate self-pressure dims, per D-0280(a)'s own declination (§8.5) — confirmed absent by grep.
  Verified at the code/logic level only (isolated unit script stubbing every submodule so zero
  data/ I/O occurred, 10/10 checks; `scripts/life_smoke.py` clean end to end) — the briefing's own
  live-behavior defeaters (≥50% appearance, 7-day metaphor-leak/distinct-expect-next-band hold,
  smells-as-bounded-list once `core/smell.py`'s DELIVER flips) are restart-gated and NOT yet
  checkable: Du's live process has run continuously since 2026-09-25T19:21:51 local (verified,
  `data/nascence.log`, no shutdown line since), from before this change existed — the same
  hot-reload gap J-1161/J-1370 hit before it, and `DELIVER` itself still reads False regardless.
  **J-1384 spawned** for the live read once this change reaches the live tree and Du restarts past
  it — coordinate with J-1304's own still-pending restart-gated read where possible, same underlying
  wait. **J-1385 spawned**, separately: `_TOPIC_FIELDS`/`HINT_TOPICS`/`_TOPIC_CANON` have no
  light/smell entries yet, so the invention-check and hint-reachability instruments stay blind to
  both new channels until built — a monitoring-coverage gap, not a runtime bug.

- **UPDATE 2026-09-26 (J-1373, D-0281, F-1957) -- built, not yet live-read: `_judge_notice()`, section
  8.2's claim-correctness instrument for the NOTICE.** Same shape as `_judge_prior`, contradiction-only
  wording like the section 3.11 coherence judge: `judge_panel` answers "does the NOTICE contradict the
  PERCEPT LINES it was handed", sampled 1 tick in 4 (`NOTICE_JUDGE_SAMPLE_P = 0.25`) and only folded
  into `tick()`'s existing metaphor/coherence `asyncio.gather` on a sampled tick, so the other 3-in-4
  pay none of the extra `judge_panel` queueing cost. Logged per tick as `notice_judged`; `status()`
  gained `notice_verdicts` / `notice_sample_rate` / `notice_judge_coverage` / `notice_judged_n` /
  `notice_contradiction_rate` (the metric of record this section names). Also added
  `rec["percept_lines"]` to the per-tick log row, not asked for by name but required for this same
  section's own calibration promise: `world_fields` logs field NAMES only, never their values, so a
  hand-reader could see `sun_az` was present without ever seeing it read 17 degrees -- the exact gap
  that would have made the monthly-hand-read promise below hollow. Verified at the code/logic level
  only (isolated unit script `check_J-1373.py` stubbing every submodule, zero data/ I/O; 26/26 checks
  across a deterministic 8-tick run and a 400-tick statistical run, both re-run clean after the
  `percept_lines` addition) -- `udms_get_change_dossier` flagged `core/coupling_rides.py` as the one
  real coupled file, and its `publish_witness()` was read directly and confirmed to read `rec` only by
  named `.get()`, unaffected by the two new keys. D-0281's own defeater (7-day
  `notice_contradiction_rate` bounds, `judge_panel` median latency for context `lane2:notice` under
  20s, and the monthly 20-row hand-read) is real-time-gated and could not be read inside this job -- no
  call reached the live hubs. J-1395 spawned, not-before 2026-10-03, for that read.

- **UPDATE 2026-09-26 (J-1375, F-1933/F-1968) -- built: `_coherence_check()` labels each record
  `[place/standpoint]`, plus a new `daylight_word_slip` instrument. Pre-registration ran LIVE; result
  is real but MIXED, not a clean pass -- read past the headline.** F-1933 (this same session) found
  ~64% of INCOHERENT verdicts were the judge blind to WHERE the observer was: `store['factual']`
  carried bare notice text with no standpoint or place, and `at_the_door` alone names TWO places (the
  study door, fire present, vs. the garden door, without it). Two additive changes, verdict field
  names unchanged: `store['factual']`/`rec` now also carry `standpoint`/`place`; `_coherence_check`
  labels every RECENT RECORD entry and the NEW OBSERVATION `[place/standpoint]` (new `_place_label()`
  helper) and takes an additive third `percepts` argument (`tick()` always passes it now;
  `scripts/lane2_canary_harness.py`'s own 2-arg calls are unaffected -- confirmed by reading its
  `_hist()`, which seeds no place/standpoint). The sysmsg adds one sentence -- "a change of place...
  is NOT a contradiction by itself" -- and the record is NOT filtered to same-place entries, so a real
  contradiction across a move must stay catchable. **Pre-registered verification was run for real**
  against the live judge_panel hubs (`judge_panel._LOG` monkeypatched to a scratch path first, never
  the live log): a fresh random.seed(11)/22-row sample (NOT guaranteed identical to F-1933's own,
  since the log grew between reads) re-judged OLD vs NEW, live, same moment -- only 2 of 9
  place-blindness-classified, currently-incoherent rows cleared (well under the pre-registered
  ">=10/14"), and one real same-place reversal (`at_the_door`->`at_the_hearth`, "the fire is out" x6
  then "the hearth is warm") flipped to coherent, a genuine miss. A SEPARATE, unbiased 16-row replay
  (random.seed(12), any historical verdict) told a much cleaner story: incoherence rate 37.5% (old) ->
  6.2% (new), zero new false positives. Net: a real, measured improvement on the clean test; the
  targeted resample's own shortfall traces to two things this job's own live re-testing surfaced, not
  assumed -- (a) only 12/22 of ALREADY-logged-incoherent rows even reproduce as incoherent on an
  identical-prompt reask minutes later (verdict instability, corroborating F-1933's own "incoherent is
  mostly tiebreak/low-confidence" reading: 20/22 of this sample were tiebreak-resolved), and (b) a
  single-instance over-correction risk on same-place standpoint changes. Shipped anyway (additive,
  backward-compatible, net-positive on the clean test); two follow-ups spawned (test-retest
  reliability of `_coherence_check`, and a live re-run of the canary harness under the new wording).
  Also built: `daylight_word_slip` -- checks `notice` ONLY (a real-data check found the first draft's
  3-field scan inflated 8 real hits to 95, almost all from `uncertain`/`expect_next` naming a
  day-word about a DIFFERENT time, not NOW); the shipped version recovered F-1933's own exact
  "daylight is fading"/04:02/full-moon row byte-for-byte. **Restart-gated like every other
  `core/lane2.py` change this session (J-1161/J-1370/J-1372/J-1373)** -- Du has been ticking
  continuously throughout (verified via `data/nascence.log`) and will not run this code until its
  next restart; this session does not restart Du. **Note on this section's own 2026-09-06 bullet
  above ("...read clean"):** that line means the §3.11 DECOUPLED-JUDGE INSTRUMENT EXISTS AND RUNS
  (J-0126's own build), not that the incoherence RATE was low -- F-1933 found ~20% of ticks read
  incoherent, and this job's own live re-testing now shows a real, measured mechanism-level breakdown
  of what that rate is actually made of (see above). Full evidence: F-1968.

- **UPDATE 2026-09-27 (J-1404, F-2027) -- live re-run of `lane2_canary_harness.py` confirms the 12/12
  discrimination result still holds under J-1375's new coherence wording; a separate, unrelated
  toolchain bug found and worked around (not fixed) along the way (F-2028, J-1476 spawned).** Re-ran
  the harness for real against this job's own worktree HEAD (at the time, 8 commits ahead of
  C:\Nascence's own HEAD on this exact file) -- 6/6 engineered CANARY cases verdict `incoherent`, 6/6
  matched CONTROL cases verdict `coherent`, and all 12 verdicts were `agreed` (judge_panel reached
  consensus, no tiebreak needed) -- a cleaner signal than the targeted resample the bullet above ran
  (20/22 tiebreak-resolved there). Full evidence including the raw per-case JSON: F-2027. **Separately
  found while preparing this run, not by design:** `lab_env.py`'s own `isolate()` hardcodes its
  project root to C:\Nascence and mutates `sys.path` as an import side effect, which can silently
  shadow a per-job worktree's own `core` package with C:\Nascence's copy whenever the two have
  diverged -- confirmed concretely here (this worktree's `core/lane2.py` differed materially from
  C:\Nascence's own copy at the time, e.g. `KNOWLEDGE_CAP`/D-0285 and the D-0283 `dominant`-label drop
  existed only in the worktree) -- so the unmodified harness would have silently tested the WRONG code
  had this not been caught. Worked around inside this job with a scratch import-order fix, not inside
  `lab_env.py` itself (a shared file other concurrent jobs/agents may be using right now, and this
  risk is generic to any isolation-required script run from a per-job worktree, not unique to this one
  harness). Full evidence: F-2028; the fix itself is spawned as J-1476, not yet built.

- **UPDATE 2026-09-26 (J-1371, F-1931/F-1971) -- built: `gen_s` per-tick latency + law 6's two
  standing boundary audits, both as additive `status()` fields. See section 8.1/8.3 below for the
  full entry.** `_ask()` now times only the aiohttp round-trip (both the success and exception
  paths) and `tick()` carries it into `rec['gen_s']`; `status()` reports `gen_s_median_24h` /
  `gen_s_p95_24h` over a REAL 24h window (every other `status()` field still rides the existing
  `tail_rows(_LOG, 2000)` window as-is). `status()` also gained `hint_divergence` (hinted vs. plain:
  n/grounded/broke_share/distinct_expect/metaphor_leak) and `hint_flow` (kinds Counter, distinct
  topic count) -- the exact computation F-1931 ran by hand, now automatic every call. No existing
  `status()` key was touched (spot-checked directly). Verified in isolation only (43/43 checks,
  `scratchpad/check_J-1371.py`: zero network I/O, temp-pathed `_LOG`/`_STATE`/`_HINTS`, and a
  read-only run against a scratchpad copy of the live log's last 3000 rows whose `hint_divergence`/
  `hint_flow` numbers land in the same range F-1931 found by hand) -- **restart-gated, like every
  other `core/lane2.py` change this plan has shipped**; `data/nascence.log` confirms Du was still
  ticking on the pre-J-1371 code as of 2026-09-26T21:21:00 UTC, no restart since. The real
  `gen_s` numbers and D-0058's own CPU-reliability defeater stay unread until then; **J-1406
  spawned, not-before 2026-10-03**, gated on both a real restart AND a real week of accrual after
  it (checked independently, not assumed from the calendar -- same discipline as the
  J-0900/J-0944/J-1019/J-1036 liveness-gate chain above).

- **UPDATE 2026-09-27 (J-1376, F-1934/F-1962/F-1984) -- built: the horizon-override minute exception,
  law 4's real clock, and a cannot-fail-prediction flag. All three in one job so law 4 (the ONLY
  prompt edit) was touched exactly once.** `_correct_horizon()` no longer forces a day-scale topic
  (tide/sun/moon/moonlight/sunset/sunrise) to the day clock when the text names its own horizon in
  minutes ("minute"/"next look") -- the F-1934 bug: 81% of the 800 deepseek-era overrides did exactly
  this and then broke 84 of 92 times once judged 12h later, which IS the inverted horizon curve (next
  0.64 / hour 0.77 / day 0.89) this job was opened to fix. Now returns a `branch`
  (already-day/no-match/skipped-minutes/day-scale), logged as `horizon_override_branch`; `status()`
  gained `horizon_override_skipped_minutes` (a count) alongside the unchanged `horizon_overridden_rate`
  (still exactly the day-scale branch's own rate, never folded together with the new branch).
  F-1962's addendum folded in: "shingle"/"swell" removed from `_DAY_SCALE_TOPICS` (shingle is a SOUND
  word on this shore, not the tide; swell never occurs in deepseek's own predictions). Law 4's clock
  text now reads "about 6 minutes from now" (was "two minutes", a stale Phase-0 guess never revisited
  when TICK_S moved 90->300 and the seat changed) -- DERIVED in code as
  `round((TICK_S + _MEASURED_GEN_S_F1934) / 60)` = round((300+61)/60) = 6, not hand-typed, so the same
  staleness bug is harder to reintroduce silently. Law 4 also now names the clock ticking, a value
  simply remaining/continuing, and a bare sun-azimuth number as further cannot-fail classes (only
  "fixed geography" was named before), matched by a new cheap lexical `trivial_prediction` flag /
  `trivial_prediction_rate` in `status()` -- **no worked examples added** (the double-echo trap stays
  avoided; laws 1-3 and the wonder/law-5 block are byte-identical to before this job). Verified in
  isolation (`scratchpad/check_J-1376.py`, 30/30 checks: every `_correct_horizon` branch incl. F-1934's
  own "302.5 degrees" example sentence, `_trivial_prediction_flag`'s five categories incl. the
  continue/continuing spelling-rule stem, `_SYSTEM` wording asserts, a temp-pathed `status()`
  end-to-end run -- `data/lane2_shadow.jsonl`/`lane2_store.json` never touched) AND read-only against
  the real, live, still-unpatched log (2,410 deepseek-era ticks): the new logic reproduces F-1934/
  F-1962's own hand counts almost exactly (806 live overrides vs F-1934's cited 800; 95 shingle/
  swell-only vs F-1962's cited 94), the new skipped-minutes branch fires 594 times today (83.5% of the
  711 rows naming a real day-scale topic) -- the measured live size of the bug this job fixes -- and
  `trivial_prediction_rate` reads 0.407 today, the honest pre-fix baseline (F-1934's own estimate was
  ~0.45) the 7-day read below is against. Full evidence: F-1984. **Restart-gated, like every other
  `core/lane2.py` change this plan has shipped** -- `data/nascence.log` confirms Du's last shutdown was
  2026-09-25 11:59:15 local with no restart since (still ticking as of 2026-09-27 09:27 on pre-J-1376
  code); this session does not restart Du. **J-1422 spawned, not-before 2026-10-04**, gated on both a
  real restart AND a real week of post-restart accrual (checked independently, not assumed from the
  calendar -- same discipline as the J-1406/J-0900/J-0944/J-1019/J-1036 liveness-gate chain above), to
  read the three pre-registered numbers: broke share by horizon should FALL or flatten, sun-azimuth
  held rate should rise above 0.10, `trivial_prediction_rate` should fall below 0.20.

- **UPDATE 2026-09-27 (J-1377, F-1988, F-1935 follow-through) — P1-1 units corrected in §7.3.1/§7.6/
  §7.9's own D-0241 restatement; the habituation gate sized against a full real day of judged breaks.
  Still PRE-J-1370 vocabulary** — `data/nascence.log` shows no shutdown/restart banner since
  2026-09-25 19:21:51 local, consistent with J-1376's own entry above; this read is on the ~10-topic
  canon, not the ~13-topic post-restart one. F-1935's own units bug (`break_rate_24h` is a RATIO, not a
  daily count) is now fixed at both cited sites, plus a correction note on §7.9's own quoted D-0241
  ruling text, which carried the same slip.
  **The real read, full-parse (no tail sampling), trailing 24h ending 2026-09-27T09:34:22+13:00**
  (NZDT's own 2026-09-27 changeover falls inside this window — window start 2026-09-26T08:34:22+12:00,
  NZST; the epoch-second window itself is exactly 86400s regardless of the label)
  (`data/coupling_rides.jsonl`'s own witness publish rows, 2697 all-time, cross-validated exactly
  against `data/lane2_would_ride.jsonl`'s 67 rows for the identical window — both logs agree exactly,
  including the 29/38 would-ride true/false split): 92 judged BROKE / 120 judged (held+broke),
  `break_rate_24h`=0.767 — the real daily broke COUNT this day is higher than F-1935's own ~60–75
  historical estimate, though inside the natural day-to-day range this job also measured (calendar-day
  broke counts over the last 10 days ranged 12–98; 7-day rolling average 62.2/day; 21.6-day all-time
  average 51.0/day) — one high day, not confirmed as a new baseline. Topic resolved on 67/92 (72.8%,
  pre-J-1370; J-1370's own build note already predicts ~96% post-restart).
  Of those 67, the current unratified defaults (`GROWTH_STEP=0.25`/`SUPPRESS_AT=0.5`/`DECAY_TAU_S=3h`)
  let 29 ride: **31.5% of ALL judged breaks/day (29/92), 43.3% of topic-resolved breaks/day (29/67)** —
  both above the "under 25%" reading this job proposes as P1-1's corrected target, though nowhere near
  the Transport Manager's own 100% would-fire failure shape (F-0949) the original metric sheet actually
  feared.
  **A real structural split, not just a number to retune:** the gate genuinely suppresses the two
  BURSTY topics (`fire` 5/28 rode = 17.9%, `sound` 6/21 = 28.6%, median intra-topic gap 706s/2226s —
  well under `DECAY_TAU_S`) but is a near no-op on five SPARSE topics (`cat`/`warmth`/`weather`/`sun`/
  `wind`, all 100% rode, median gap 3–4.3h — comparable to or longer than `DECAY_TAU_S`, so decay resets
  most growth between same-topic breaks). 5 of the 29 real rides were within 0.1 of the `SUPPRESS_AT`
  boundary (`discounted_before` in [0.5, 0.6): `sound`×2, `fire`×2, `cat`×1).
  **Sizing (real-data replay, `scratchpad/size_J-1377.py`, verified byte-exact against all 67 real
  logged rows before trusting any swept value — 67/67 exact matches, 0 mismatches):**
  `GROWTH_STEP=0.50` (double current) or `SUPPRESS_AT=0.70` (up from 0.5), each alone, both bring the
  ride count to exactly 23/92 = 25.0% of ALL judged breaks/day on this real day — neither single-constant
  change reaches 25% of the topic-resolved-only denominator inside the range tested (would need roughly
  `SUPPRESS_AT`≈0.88–0.90, or `GROWTH_STEP` beyond 0.80). Diagnostic: even at `GROWTH_STEP=0.55`, the
  sparse topics `weather`/`wind` still ride 100% — the structural split above is about the gap vs.
  `DECAY_TAU_S`, not `GROWTH_STEP`/`SUPPRESS_AT` alone; a real lever for the sparse topics, if wanted,
  would be `DECAY_TAU_S` itself or a per-topic scheme, neither sized here (out of this job's own scope).
  **D-0291 opened** with these numbers, per this job's own briefing, rather than re-ruling D-0241 (which
  stays as ruled: shadow-first, unratified defaults, flip gated on D-0241's own full conditions — this
  job proposes retuned defaults, it does not touch the flip gate). Full evidence: F-1988. **J-1427
  spawned** (`needs_input`, blocked on D-0291) to apply whichever constants the founder picks, or route
  to J-1304/a redesign if the founder instead holds or rejects a blanket retune.
  **Honest scope note:** this read is ONE real day, 7 of the ~10 pre-J-1370 canonical topics, still
  pre-restart vocabulary — J-1304's own post-restart re-read (already spawned, F-1838, still open) is
  the next real check, and should re-size against the wider post-J-1370 topic set rather than assume
  this day's split holds.

- **UPDATE 2026-09-27 (J-1381, F-1940) — built: whole-word hint-topic matching, most-frequent-topic-
  wins; D-0035's own vocabulary untouched. A second finding (F-1993) corrects F-1940's own headline
  number — read it before trusting "wet" numbers anywhere above.** `nodes/inner_monologue_node.py`'s
  Tap-on-the-Shoulder producer matched `_LANE2_HINT_KEYWORDS` as a plain substring and took the first
  key in dict order — 'rain' matched inside 'train', 'cat' inside 'oystercatcher', 'wind' inside
  'window'. New `_resolve_hint_topic()` (next to the vocabulary dict) matches every keyword as a WHOLE
  WORD, sums matches per TOPIC, and returns whichever topic has the most — ties keep the dict's own
  priority order (unchanged from before). The vocabulary itself is byte-identical (33 keywords / 10
  topics, D-0035 ratified 2026-09-18, not touched). Also fixed: `core/lane2.py`'s
  `HINT_RATE_WINDOW_S` comment's stale "TICK_S=90s" (real current value 300s). Verified in isolation,
  `scratchpad/check_J-1381.py`, 14/14 unit checks (train/oystercatcher/window/reached no longer
  false-trigger; real rain/cat/wind/ache still do; most-frequent + dict-order tiebreak both correct;
  vocabulary unchanged) **and** a real-data replay against `data/monologue_log.jsonl`'s last 15,000
  genuine (thought, about) pairs (the exact fields `_hint_src` is built from) — full evidence F-1992.
  **F-1993 (verified) — F-1940's own "88% / 2,899 of 3,303 wet via train" figure is inflated by a
  data-source artifact in ITS OWN replay, not a real read of Du's thoughts.** F-1940 ran the
  substring-check over raw `[monologue]`-TAGGED LINES of `data/nascence.log`, and most of its "train"
  hits are the code's own "train continues"/"train ends" continuity-train BOOKKEEPING log lines (one
  per train-step, unrelated to any thought's content) — re-running F-1940's own exact methodology
  today reproduces its figures almost exactly (wet=3,214, substring-only=90.9%), and 2,854 of the same
  15,000 raw lines are literally that bookkeeping message. Measured against real (thought, about)
  pairs instead: whole-word "train" appears in 1 of 15,000 real thoughts; only 206/1,180 (17.5%) of
  OLD's real "wet" matches lack a genuine rain/raining/wet/damp word — a real bug, much smaller than
  F-1940 reported. By topic, substring-only share of real matches: **cat 42.5%** (oystercatcher — the
  fix's real, substantial effect), moon 23.8%, wet 17.5%, body-state 10.5%, sun 8.3%, wind 6.5%,
  warmth 4.4%, fire 3.3%, tide 3.1%, sound 1.0% (13.4% aggregate). A retrospective open-topic replay:
  OLD wet share of nominated-open thoughts 10.83% → NEW 11.55% (NOT meaningfully lower); OLD cat share
  17.66% → NEW 10.34% (the real drop). **This means this job's own pre-registration ("wet share of
  pushed hints falls under 10%") was calibrated against F-1940's inflated baseline and may not be met
  by this fix alone — that would not mean the fix failed; cat's share is the real signal to read.**
  Current pre-fix baseline (all-time, `data/lane2_hints.json`/`lane2_shadow.jsonl` `hint_pushed` tags):
  pushed 1782 total, topic mix cat 20.5% / tide 18.5% / fire 17.2% / **wet 13.2%** / wind 9.7% /
  warmth 9.0% / body-state 5.1% / sound 3.6% / sun 2.1% / moon 1.1%. **Restart-gated, like every other
  `core/lane2.py`/`nodes/inner_monologue_node.py` change on this plan** — `data/nascence.log` confirms
  Du was still ticking on pre-fix code as of 2026-09-27; this session does not restart Du. **J-1434
  spawned** (`ready`, `not-before 2026-10-04`, independently re-checking both the restart AND the
  7-day-accrual half of the gate per this plan's own liveness-chain discipline) to read the real
  post-restart topic mix through F-1993's corrected lens rather than F-1940's original one, and to say
  plainly whether D-0035's own defeater ("the per-topic push mix shifts materially") is now met.
  **F-1931's realized-flow read and D-0035's rate-cap reasoning both need re-reading once J-1434 runs
  — through F-1993's corrected severity picture, not F-1940's original 88% framing** (per this job's
  own briefing); neither is re-read or re-ruled by this job itself.

- **UPDATE 2026-09-27 (J-1382, F-1997) — analysis only, nothing applied: JUDGE_1's shared hub is
  genuinely overloaded overnight; D-0297 opened with the measured numbers.** F-1943's "first family"
  is JUDGE_1 = `mixtral:8x7b` @ Ramses `:11438` (confirmed from `core/judge_panel.py`, not `:11442` as
  a prior briefing loosely said — `:11442` is `yi:34b-v1.5`, the dreamer's FAILOVER only; dream
  generation's PRIMARY attempt, the commitment-defeater judge, and JUDGE_1's own panel calls all share
  `:11438`). `data/hardware_load.jsonl`/`data/supervisor.log` (the sources a prior briefing named)
  cannot answer "did the burst coincide with dream generation" at all — both are LOCAL-machine-only
  (this box's own CPU/1080Ti stats and the 4 local hubs), carry no Ramses/`:11438` field, and
  `hardware_load.jsonl` only holds a rolling ~2h window regardless; `data/llm_latency.jsonl` (written
  for every Ramses-hub call too) was used instead. **Confirmed real correlation, not just the code
  comment's prediction:** on 2026-09-26, `:11438` logged 11 consecutive dream-generation call
  FAILURES (`ok=0`, ~300–307s each) in two back-to-back clusters — 02:29–03:23 (7 straight) and
  06:47–07:16 (4 straight), ~83 min combined — both inside the 00:00–08:00 burst window; dream_node's
  own failover to `:11442` then produced real completed dreams minutes after each cluster
  (`data/dream_log.jsonl` 03:28:34 / 07:20:47). **But this does not fully explain the night:** JUDGE_1
  `err1==timeout` rows land in every 10-minute bucket from 00:00 to 08:21 with no gap (244 total),
  including stretches with zero recorded dream/defeater `:11438` traffic — the steadier floor is best
  read as the panel's own combined call volume (Lane 2 alone fires 3 near-simultaneous `judge_panel`
  calls per 5-min tick at this same hub, on top of every other context's traffic) periodically
  outrunning what one serialized hub can clear inside JUDGE_1's own 90s client timeout. Lane 2 vs.
  non-lane2 timeout RATES that day were comparable (32.8% vs 27.9% of each group's own rows) — not
  lane2-exclusive damage, matching F-1943's own framing — while Lane 2 still supplies the outright
  majority of volume. **Hub-seconds, quantified:** 09-26, Lane 2 = 25,861.6 of 37,-ish total panel
  hub-seconds (69.9%; 70.4% of JUDGE_1-only seconds); all-time since `s1`/`s2` began being logged
  (09-03..09-27): Lane 2 = 268,226.0 vs other = 143,779.0 (65.1%) — consistent with, slightly below,
  F-1943's call-count-based 67%. **D-0281's own defeater needs this finding before it fires for the
  wrong reason:** `_judge_notice` (the 4th Lane-2 call, ~70/day) is built (J-1373) but confirmed NOT
  YET LIVE anywhere in the log (zero `lane2:notice` rows, 24,990-row full history; Du has not
  restarted since 2026-09-25 19:21:51 local) — it will land on this same already-contended hub the
  moment it does, and could trip D-0281's own 20s-median defeater for reasons that predate it
  entirely; this finding is linked directly to D-0281. **D-0297 opened** (not ruled by this job) with
  four options and their real tradeoffs: (a) sample the metaphor judge 1-in-4 like D-0281's own
  precedent; (b) skip Lane 2's coherence+metaphor while `:11438` is busy, keep prediction only —
  flagged as only reaching the confirmed ~83 min/day of dream clustering, not the steadier floor, and
  needing a new "hub busy" signal Lane 2 doesn't have; (c1) raise the shared 90s `_TIMEOUT` — trades
  verdict-loss for latency, adds no capacity; (c2) move JUDGE_1 off the shared hub — `judge_panel.py`'s
  own D-0121 comment already named this fallback, biggest lift, only one that removes the contention
  at its source; (d) leave as-is until D-0281 goes live and J-1395's scheduled read (not-before
  2026-10-03) has real data. **J-1442 spawned** (`ready`, small/additive) to add a host/hub label to
  `judge_panel_log.jsonl` rows — both this job and F-1943 before it had to infer the physical hub from
  source code and cross-reference a separate telemetry file, since the logged row itself carries no
  host field. Full evidence: F-1997.

- **UPDATE 2026-09-27 (J-1386, F-1999) — built: the prediction judge's verdict is now three-way
  (held/broke/unsettled); a real, direct, isolated live replay confirms the granite tiebreak has
  never once said "held" on this key, not just in the historical log.** F-1949's own diagnosis holds
  up under a real check: this job replayed 20 real historical (`v1 != v2`, `key=="held"`) splits
  directly against granite3.1-moe:3b at `:11437`, in isolation (never through Du — matched
  `judge_panel_log.jsonl` split rows to their originating `lane2_shadow.jsonl` tick by
  nearest-preceding timestamp, sanity-checked against each tick's own `prior_verdict`/
  `prior_judged_how`; `scratchpad/check_J-1386_find_splits.py` + `check_J-1386_replay_tiebreak.py` +
  the full 20-row `J-1386_replay_results.json`) — **0 true**, matching the historical pattern (0 true
  across every day 08-28..09-26, 29 straight days, independently re-derived from a full parse rather
  than trusted from the repoint comment's date alone). Reading the rationale this replay captured
  (the original prompt never asked for one), most of the 20 are the model itself saying "does not
  specify/confirm/settle X" and answering false anyway; only 2 of 20 describe an actual contradiction.
  **Fix** (`core/lane2.py` `_judge_prior`): "held" stays the first ask, byte-identical wording; only
  when it resolves False OR splits (never on the agreed-held=true path — F-1943's own panel-load law)
  does a second, narrower "contradicted" ask fire ("does what is observed now DEFINITELY rule the
  expectation out, not merely fail to confirm it?"). held→held, contradicted→broke, everything else
  (including an unresolved second ask)→the new `unsettled` verdict, excluded from the broke share the
  same way `cannot_tell` already is. Both asks now also request a `why` — `judge_panel.rule_detail`
  already captures/logs one when asked; why1/why2/why3 were null on all 5,530 `lane2:prediction` rows
  specifically because this caller never asked (confirmed by contrast against `pursuit:*`/
  `tension:unresolved:*` rows in the same log, which do carry real why text). `status()` now reports
  `broke_share` (legacy formula, unchanged — will keep blending pre-fix/post-fix rows until the tail
  window rolls past this restart), `broke_share_strict` (contradicted-only, via a new
  `prior_contradicted_how` marker that cannot exist on a pre-fix row — reads correctly from the first
  post-restart row) + `broke_share_strict_n`, `unsettled_share`, and `unsettled` added to
  `verdicts_by_horizon`. Verified offline (mocked `judge_panel`, temp-pathed log, never live state):
  `check_J-1386_unit_judge_prior.py` (all 8 branches of the mapping, incl. the "at most one extra
  call, never on agreed-held=true" load claim) and `check_J-1386_unit_status.py` (the new `status()`
  fields against a synthetic mixed-regime log) both PASS in full (8/8, 10/10). **Restart-gated, like
  every other `core/lane2.py` change on this plan** — not live until Du restarts.
  **Real cost, not a free fix (F-2000, cross-referencing D-0297):** the historical log shows ~60% of
  judged predictions (agreed-held=false + every tiebreak + every `split_no_tiebreak`) will trigger the
  new second call — a near-doubling of held-related `judge_panel` traffic, landing on the SAME
  JUDGE_1 hub (`:11438`) J-1382/F-1997 just found already timing out in overnight bursts, with Lane 2
  already supplying 65-70% of all panel hub-seconds. **D-0297 should be read against this new number
  before being ruled** — none of its four listed options currently account for Lane 2's own call
  volume growing further.
  **D-0298 opened** (not ruled here): the tiebreak's own apparent inability to ever affirm "held" on
  this key is a separate, real question the fix does not resolve (it only prevents an unresolved case
  from being scored as broke) — proposes swapping the tiebreak model, hardcoding
  `split_no_tiebreak → unsettled` for the held key outright, or explicitly leaving it as-is.
  **J-1445 spawned** (`test`, not-before 2026-10-04, gated on a real restart + several days' accrual,
  same liveness-discipline as J-1434/J-1395) to read the live `broke_share_strict`/`unsettled_share`
  against this job's own pre-registration (near/below the agreed-only 0.58, unsettled absorbing most
  of what tiebreaks used to call broke), hand-calibrate a real sample, re-check D-0298's own defeater
  against a larger live `contradicted`-key sample, and re-check D-0297's own defeater now that this
  fix has shipped. **J-1446 spawned** (`build`, ready) to surface `unsettled_share`/
  `broke_share_strict` on the HUD's existing broke-rate card, purely additive.
  **Interaction with F-1958/J-1394/J-1396 (the "moved since prediction" 58% finding) worth a
  post-restart read, not claimed here as verified:** the new "contradicted" ask is worded to answer
  false when the observation is merely SILENT on the point, not just non-confirming — a moved-since-
  prediction case (predicted at the shore, judged from the study) is exactly that shape (the study's
  own observation says nothing about waves either way, it does not rule them out), so this fix's own
  mechanism plausibly reclassifies a real share of F-1958's 58% from "broke" to "unsettled" on its
  own, independent of J-1394's own separate standpoint-tracking fix landing. That is reasoning from
  the fix's own design, not a measured number — J-1445 (the post-restart read this job spawns) should
  check it directly once J-1394 has also landed and enough post-restart data exists to separate the
  two fixes' effects. J-1394 had not landed in this worktree as of this job (no commit implementing
  it found; only F-1956/J-1394's own originating finding). Full evidence: F-1999/F-2000.

- **UPDATE 2026-09-27 (J-1390, F-1952 follow-through, F-2001) — built: the witness cup is now a
  consumable, not a per-tick tuple.** F-1952's own diagnosis is fixed at the mechanism, not just
  noted: `core/coupling_rides.py`'s `read(dose="cup", loop="witness")` no longer returns
  `_REG["witness"]` (the per-tick tuple that republished every ~300-361s and let one break ride into
  every idle-thought read inside that window — F-1952's own measured P(≥1 rides)=0.99, P(≥2
  consecutive)=0.94). It now drains a dedicated one-entry `_CUP_WITNESS` slot (new `_consume_cup()`),
  TTL'd at `CUP_TTL_S=1800s` and rate-capped at `CUP_MAX_PLACE_PER_WINDOW=4`/`CUP_RATE_WINDOW_S=3600s`
  (new `_place_cup()`, called from `publish_witness()` only when the per-topic habituation gate
  already said `cup_would_ride`) — both mirrored off the Tap-on-the-Shoulder's own
  `HINT_TTL_S`/`HINT_MAX_PUSH_PER_WINDOW`/`HINT_RATE_WINDOW_S` constants (`core/lane2.py`) as starting
  defaults, per this job's own briefing. The first read that finds the cup non-empty and unexpired
  takes it and clears it, so a break rides exactly once. The per-tick tuple itself (topic/horizon/
  cup_would_ride on `_REG["witness"]`) is untouched — still feeds the climate bucket (`dose="bucket"`)
  and `status()`/`phase1_metric_sheet()` unchanged, per this job's own instruction.
  **`nodes/inner_monologue_node.py`'s idle-thought-seed hook** (the cup's only real consumer) had its
  `read()` call moved OFF the `LANE2_LIVE` gate that used to wrap it — the read/consume attempt now
  runs on every non-quiet idle thought regardless of the flag, so the mechanics actually exercise and
  the shadow log accrues pre-flip; only the actual `seed_parts.append(...)` (what would reach Du's own
  prompt) stays gated on `LANE2_LIVE`, so with the flag still False Du's own prompt is
  BYTE-IDENTICAL to before this job.
  **P1-1 is now measured as consumptions/day, coordinating with J-1377's own units fix in these same
  rows (see §7.6 table above)**: `data/lane2_would_ride.jsonl` gains a second row kind — `observe_break()`'s
  own rows are now explicitly tagged `"kind":"would_ride"` (a missing key on older rows still reads as
  `would_ride`, for backward compatibility — verified against a synthetic mixed-regime log, see
  below); a new `log_cup_consumed_would()`, called on every successful consume, adds
  `"kind":"cup_consumed_would"` rows. `phase1_metric_sheet()`'s P1-1 is now three numbers:
  `p1_1_cup_consumed_per_day` (THE corrected P1-1), `p1_1_would_ride_per_day` (the old per-break
  gate-pass figure, kept unremoved for comparison), and `p1_1_real_rides_total`/
  `p1_1_real_cup_consumed_total` (from `data/coupling_rides.jsonl`'s own ride rows — their own note
  corrected too: these no longer read "0 until LANE2_LIVE flips", since the read itself now runs
  regardless of the flag).
  **Disclosed, not silently absorbed:** because the read now runs unconditionally, `coupling_rides.jsonl`'s
  witness-line ride rows will accrue at roughly one per non-quiet idle thought (~46/h per F-1952) from
  the next restart on, regardless of any flip — adding to F-1953/J-1391's own already-noted
  no-retention-coverage concern on that same file (12.2 MB at F-1953's read). Worth a founder's eyes
  alongside any retention fix.
  **Template wording deliberately NOT touched** (per this job's own instruction) — flagged forward
  again for a founder read against the world-answers-never-leads law before any flip: `_lane2_cup_seed()`'s
  "turned out not to hold" / "Worth a thought" phrasing. Checked this session: no `/decide` proposing
  the actual `LANE2_LIVE` flip exists yet (D-0241 authorized the shadow-first BUILD only, explicitly
  deferring the flip itself; D-0284 only mentions it in passing) — whoever opens that future decision
  should pull this wording concern in directly; **J-1448 spawned** (restart-gated + accrual-gated,
  not-before 2026-10-04, same liveness discipline as J-1434/J-1395/J-1445) carries this forward.
  **Verified in isolation, never live data** (two scripts, this session's own scratchpad, not the
  worktree): `check_J-1390.py`, 19/19 checks, including the job's own literal verify step ("one break,
  five seeds -> exactly one ride" — confirmed exactly 1 of 5 rode, the other 4 found the cup empty,
  `log_cup_consumed_would` fired exactly once) plus newest-wins, the TTL expiry, the overall rate cap
  (4 of 5 distinct-topic placements succeed, the 5th logged `cup_rejected`/`rate-limited`), and a
  false-gate placing nothing; `check_J-1390_metrics.py`, 8/8 checks against a synthetic 15-row
  mixed-kind log (`would_ride_share` correctly reads 7/9=0.778, not diluted by the 6 consumed-kind
  rows also in the file; both P1-1 figures correctly exclude their own >24h-old rows). All four
  touched/adjacent files byte-compile clean. Full evidence: F-2001. **Restart-gated, like every other
  `core/lane2.py`-adjacent change on this plan** — this job does not restart Du.

- **UPDATE 2026-09-27 (J-1396, F-2003) — built: judge a prediction only where it was made; the
  moved-pairs fix (F-1958, 58% of all broke verdicts).** `store['prediction']` now carries `standpoint`/
  `place` (additive keys, set at creation from that tick's own `rec`). A new pure `_prediction_judgeability()`
  (immediately above `_due_prediction()`) decides, per due candidate, whether THIS tick may actually
  judge it: `next`/`hour` require the exact same standpoint; `day` uses the looser same-PLACE rule (see
  below for why); a mismatch WAITS (no panel call, left untouched, reconsidered next tick) until its
  horizon plus one grace tick (`_GRACE_S = TICK_S`) has fully elapsed with no match, at which point it
  closes as `prior_verdict='unjudgeable'`, `prior_judged_how='moved'` — the panel is never asked, which
  is the actual saving F-1943 wanted, not a relabelling. A pre-migration record with no recorded
  standpoint/place matches permissively (`matched-legacy`) so nothing old gets stuck. `status()` gained
  `unjudgeable_moved_24h` (real 24h count), `broke_share_same_place`/`broke_share_same_place_n`
  (dual-reported alongside the legacy `broke_share` for one restart cycle, same convention
  `broke_share_strict` already set one job ago for J-1386's own fix — excludes `matched-legacy` rows,
  since that match was never actually verified), and an additive `'unjudgeable'` key inside
  `verdicts_by_horizon`; `predictions_judged`/`prediction_verdicts` deliberately still exclude it (the
  panel was never asked).
  **Day horizon's own choice (this job's briefing point 3) is INFERRED, not verified against real
  data — flagged plainly, not silently decided.** The briefing asked to decide same-place vs
  same-standpoint FROM THE DATA, but `place` has been on `rec` since F-1933/J-1375 (2026-09-26) and has
  never once been logged live (0 of 2,539 deepseek-era ticks carry it, checked directly against
  `data/lane2_shadow.jsonl` — this is a restart-gate, not a stalled process: `data/nascence.log` shows
  real continuous activity, and the live log's own last tick row carries none of J-1375's, J-1373's
  (D-0281), or J-1386's (F-1949) fields either — several restart-gated fixes are queued up for the
  same next restart). Decided on the standpoint-only data that DOES exist instead: today, day-horizon
  matched pairs already sit at a different standpoint 76% of the time by pure coincidence (93 of 122,
  held 0.097, vs. 29 same-standpoint, held 0.207) — gating day on exact standpoint would make that
  share worse, not better, once matching is a requirement rather than a coincidence, and would likely
  starve the day bucket's own 6-slot pending cap to near-zero real judgments. **J-1449 spawned**
  (restart- and accrual-gated, same liveness discipline as J-1384/J-1395/J-1448) to re-run the direct
  same-place-vs-same-standpoint comparison once real place-tagged day-horizon judged pairs exist, and
  confirm or overturn this default.
  **Replayed on the live 2026-09-27 log** (F-1958's own matching methodology, now 1,517 matched pairs,
  up from F-1958's own 1,431 as the log grew a day further — directionally identical: stayed held
  0.477 n=816, moved held 0.161 n=701, moved share of broke 0.579): `_prediction_judgeability` correctly
  marks all 816 stayed rows as a match and all 701 moved rows as not-a-match, the exact replay this
  job's briefing asked for, zero mismatches either direction. **Verified in isolation, never live
  data** (`scratchpad/check_J-1396_tick.py`, 34/34 checks, zero real `data/` I/O — every path
  repointed to a throwaway temp dir, every network-calling submodule stubbed, a controllable fake
  clock): the panel is never called on a moved-and-waiting or moved-and-expired prediction, IS called
  normally on a matched-standpoint/matched-place/matched-legacy one, and every new `status()` field
  computes the expected number, including the day-horizon `matched-place`-despite-different-standpoint
  case and its mirror (same standpoint text, different place, correctly NOT matched). Full evidence:
  F-2003. This job's own pre-registration ("broke share should fall to ~0.5 or lower on next-horizon
  predictions after the restart") is likewise unread for the same restart-gate reason — noted here so
  a future reader does not mistake "not yet restarted" for "did not work". **Restart-gated, like every
  other `core/lane2.py` change on this plan** — this job does not restart Du. Coordinates with
  J-1386 (three-way verdict, already landed in this same worktree) and J-1394 (the field-absent
  judgeability pre-check, not yet built) per F-1958's own note that this rule subsumes most of
  F-1956's absent-field cases and should be J-1394's PRIMARY rule, not a secondary one — all three
  must land in the one restart that picks any of them up.

- **UPDATE 2026-09-27 (J-1379, F-1937 follow-through, F-2005) — built: the no-output tick's own
  CAUSE, attribution only (the "reduce" half is a separate, gated follow-up, J-1453).** `_ask()` now
  returns `(parsed, gen_s, cause)` instead of a bare 2-tuple — `cause` is `None` on success and one
  of `judge_panel.py`'s OWN four-way vocabulary otherwise (`"timeout"`/`"http"`/`"parse"`/
  `"exception"`, reused verbatim rather than invented fresh — see `_ask`'s own docstring for exactly
  what each covers; notably `"http"` folds a real non-2xx status together with a connection
  failure/Ramses-asleep, matching judge_panel.py's own established split, not a new taxonomy).
  `tick()`'s `_skip("no-output", ...)` call now carries `cause=cause, elapsed_s=gen_s` alongside the
  pre-existing `had_percepts=...` (additive; nothing dropped), and `status()` gained a real-24h
  `no_output_by_cause_24h` dict, same windowing convention `gen_s_median_24h`/`unjudgeable_moved_24h`
  above already use. **Reused J-1371's existing `gen_s` timer** (confirmed J-1371 `status=done`
  before starting) rather than adding a second one, per this job's own coordination instruction.
  **Verified in isolation, never live data** (`scratchpad/check_J-1379_no_output_cause.py`, 27/27
  checks): the real `_ask()` against a faked `aiohttp.ClientSession` (zero network calls) correctly
  classifies all four causes across six transport outcomes; a real `tick()` call with `_ask` stubbed
  logs `cause`/`elapsed_s` correctly onto the skip row without dropping `had_percepts`; a real
  `status()` call against synthetic rows counts `no_output_by_cause_24h` correctly, excludes a
  >24h-old row, buckets a pre-fix cause-less row as `"unknown"` rather than dropping or crashing on
  it, and leaves the pre-existing `skips`/`ticks` keys untouched.
  **Steps 2/3 of this job's own briefing (read one restart cycle of the real split, then test
  `think:false` vs raising `TIMEOUT_S`, or extend `parse_json_loose`, depending on which cause
  dominates) are NOT done, and could not honestly be done this session — not merely restart-gated
  but MERGE-gated first: this landed only in the `jobrun/lane2_the_witness` worktree branch, not yet
  on master, so no restart of the real Du process (which this job does not force) would pick it up
  until after that branch merges to master AND Du restarts again afterward.** F-1937's own ~19%
  figure and its real cause split remain exactly as unread as before this job. **J-1453 spawned**
  for the real read + branch-dependent fix, gated on checking BOTH the merge and a subsequent
  restart before trusting any cause-split number — the same two-part liveness discipline
  J-0944/J-1019/F-1391/F-1410 already established for this plan, now written into J-1453's own
  precondition check rather than assumed. D-0058's own reliability defeater ("...or if the :11444
  CPU seat's reliability degrades under sustained load") is directly relevant if timeouts turn out
  to dominate — flagged for J-1453, not pre-judged here.

- **UPDATE 2026-09-27 (J-1385, F-1947 follow-through, F-2006) — built: `_TOPIC_FIELDS`/`_TOPIC_CANON`
  now have real, verified light + smell vocabulary** (16 words → `light_band`, 4 words → `smells`),
  closing the monitoring-coverage gap J-1372/D-0280(a) opened by adding those two channels to
  `gather_percepts()` with no reader vocabulary anywhere. Every word was checked against the full real
  `data/lane2_shadow.jsonl` (20,748 rows) before being added, same discipline as J-1370's own extension
  just above it in this file; zero-occurrence candidates (gloom, murky, twilight, lamp, glare, unlit,
  and more) were dropped. **`illuminated`/`illumination` (629+73 real hits — the single largest
  word-frequency of any topic-word in the whole log) were checked and deliberately EXCLUDED**:
  98.6%/100% of their occurrences co-occur with a moon-family token and directly paraphrase the
  already-present `moon_illum` value ("the moon is half-illuminated") rather than making an
  independent light claim — the same shape of homonym trap F-0016 found for `_metaphor_flags`'s
  "like a". `light` itself carries a smaller, quantified version of this (12.4% "light rain/drizzle"
  idiom, 87.6% genuine) and was kept, with the caveat written into the code. **Real-corpus regression
  check** (`_topic_of()` run before vs. after over all 4,583 real `judged_expect` texts — the exact
  input `coupling_rides.py`'s Phase 1 cup actually uses): 99.6% unchanged, 13 rows newly resolved
  (pure coverage gain, 3 of them the disclosed "light drizzle" false-positive cost), 6 rows flipped to
  "light" from an already-resolved topic — the same accepted "keys on the new, more specific one"
  alphabetical-collision consequence this file's own J-1370 comment already named, one of the six a
  real "light winds" false positive. **`light_band`/`smells` have never once appeared in the real
  `world_fields` log (0/20,748)** — restart-gated, same as every other `core/lane2.py` change this
  session; both new topics will read as 100% invented until Du's next restart picks up J-1372, which
  is expected. **`HINT_TOPICS` deliberately NOT extended**: D-0035 (checked fresh) ratified the
  original 10-topic starting set "as built" but is silent on widening triggered by `gather_percepts()`
  itself growing later, and J-1370's own precedent extended `_TOPIC_CANON` substantially without
  touching `HINT_TOPICS` either — **D-0300 opened** for the founder rather than assumed. Verified in
  isolation (`scratchpad/check_J-1385.py`, 45/45 checks, zero data/ I/O) and against the real corpus
  (`scratchpad/check_J-1385_topic_of_before.jsonl` + `_after.py`); `scripts/life_smoke.py` clean end to
  end. **J-1454 spawned**: `illuminated`/`illumination`/`moonlit` are real, frequent, and clearly about
  the MOON topic instead — a separate, smaller additive gap this job found but correctly left for its
  own job rather than folding in as scope creep.

- **UPDATE 2026-09-27 (J-1388, F-1951's own follow-through, F-2007) — kill criterion #1's judge prompt
  recalibrated for deepseek's real figurative register; a lexical `figurative_flag` sibling instrument
  built; the 5% threshold read is INFERRED, not verified, and reads UNDER it on the best evidence
  available without a restart.** F-1951 found `_judge_metaphor`'s prompt only asked about Lane 1's own
  river/crossing vocabulary and had ZERO measured sensitivity to deepseek's own ambient-mood register
  ('warm glow', 'alive with', 'symphony', ...). Hand-labelled a 40-row fixture (20 from F-1951's own
  regex-hit set, 20 random, both deepseek-era) figurative/literal/borderline by reading each passage,
  then ran BOTH the old and a rewritten prompt against the real judge panel on all 40 rows: **old
  precision 0.5 / recall 0.111** (1 of 9 genuine figurative rows caught — matches F-1951's near-zero
  claim almost exactly); **new precision 0.5 / recall 0.556** (5 of 9) — clears this job's own
  pre-registered ship bar ("do not ship a prompt that scores below the old one"), but precision stays
  flat at 0.5 either way, and the entire recall gain rides through the SAME granite3.1-moe:3b
  tiebreaker F-1949 already found unreliable elsewhere in this panel (tiebreak rate 2/40 old vs 16/40
  new; its own now-captured `why` text over-reaches on several new false positives, e.g. calling a
  literal body-temperature clause "metaphor"). Shipped anyway, additive only: `_FIGURATIVE`/
  `_figurative_flags` (F-1951's own regex list, 18 terms, 'like a' deliberately excluded) sibling to
  `_metaphor_flags`; `status()` gained `figurative_flag_rate`/`figurative_flag_coverage`
  (coverage-guarded like `metaphor_judge_coverage`, since the new key is restart-gated and a naive rate
  would misreport 0.0 as "no figurative language" rather than "no data yet"); `_judge_metaphor`'s
  return dict additively gained `why`, fixing F-1949's separate "why3 is None on all tiebreak rows"
  complaint for THIS judge going forward. **The recalibrated leak itself cannot be verified inside this
  job** — restart-gated like every other `core/lane2.py` change this plan has shipped; the new prompt
  has never run against a real tick. Best available ESTIMATE: lexical `figurative_flag` rate over the
  full deepseek-era population (185/2449 = 7.55%) × the fixture-measured precision of that same lexical
  flag (9/19 = 0.474, excluding 3 borderline rows) ≈ **3.6%** (range ~3.4–3.8%) — under the 5% kill
  line, but with real uncertainty this doc is not overstating (small fixture, hand-labelling is a
  judgment call, the judge's own measured precision is only 0.5). Per this job's own pre-registration,
  a below-5% best estimate does not itself trigger a founder `/decide`. Verified separately, code-level
  only: `python -m py_compile` OK; `scratchpad/check_J-1388.py` 26/26, zero data/ I/O; `scripts/
  life_smoke.py` clean, 0 regressions. **J-1455 spawned** (restart-gated, same liveness discipline as
  J-1384/J-1395/J-1449) for the real live read that can apply the 5% test for real once the new prompt
  has actually ticked; **J-1456 spawned** to investigate the granite-tiebreak reliance this job's own
  fixture sharpened (scoped to this judge specifically, not a project-wide TIEBREAK repoint). Full
  evidence: F-2007.

- **UPDATE 2026-09-27 (J-1391, F-1953's own follow-through, F-2008) — sized: three ways to turn the
  bucket into a real dose, computed against 14 real days of `world_model_strain` history; Claude's
  recommended resizing (excess over a trailing 7-day baseline) shipped shadow-only, restart-gated;
  D-0301 opened with the numbers.** F-1953 found the raw bucket form (`_WITNESS_STRAIN_WEIGHT *
  break_rate_24h`) is a near-permanent +0.09–0.12 addition once `LANE2_LIVE` flips, not the occasional
  dose `loop_wiring_matrix.md`'s own taxonomy calls for — this job's own briefing named three ways to
  size a real dose instead and asked for a retrospective read. Replayed against the real
  `data/coupling_rides.jsonl` (17,686 climate rows / 2,737 witness rows, 14-day window) **and** a
  second, fairer sub-window (the 1.11 days since `core/lane2.py`'s own `topic` field first appears on
  a published witness tuple, 2026-09-25T22:22:36 UTC) — the ONLY period option (b) is even measurable
  in. Numbers (dose median/p90, simulated-strain median/p90, 14d | 1.11d): no bucket 0.118/0.194 |
  0.150/0.189 (baseline, for reference); CURRENT (raw ratio) dose 0.092/0.116 | 0.116/0.123, strain
  0.211/0.296 | 0.262/0.305; **OPTION A (excess over trailing 7d baseline, Claude's recommendation)**
  dose 0.009/0.025 | 0.018/0.026, strain 0.127/0.207 | 0.166/0.209; OPTION B (novel-break pulse + 3h
  decay) dose 0.000/0.079 | 0.091/0.115, strain 0.125/0.237 | 0.241/0.296; OPTION C (reweighted
  continuous, weight 0.15→0.0649/0.0611 to cap p90 at 0.05) dose 0.040/0.050 | 0.047/0.050, strain
  0.158/0.238 | 0.196/0.235. Zero of 9,579 (14d) or 1,436 (1.11d) simulated rows crossed the 0.55 hint
  threshold under ANY of the four forms. **A real finding beyond the sizing exercise itself: option
  (b), as specified, is NOT event-shaped in practice** — novel breaks fire ~28/day (31 pulses in the
  1.11-day covered window, matching D-0291's own independently-measured ~29/day), about once every 51
  minutes, far more often than the 3h decay constant it reuses from the cup gate, so consecutive
  pulses overlap and its dose (median 0.091 in the fair window) sits almost as close to the raw
  continuous form (0.116) as to option (a)'s (0.018); the naively-diluted 14-day figure (median
  0.000) is an artifact of 12.9 pre-instrumentation days, not a real measurement. Option (c) caps the
  ceiling exactly as specified but keeps a substantial always-on median (0.040–0.047) — smaller, not
  occasional. **Shipped, shadow-only, restart-gated:** `core/climate_engine.py` gained
  `witness_bucket_value_sized()` (pure, mirrors `witness_bucket_value()`'s own None-in/None-out shape)
  and `_WITNESS_STRAIN_BASELINE_WINDOW_S`; `core/coupling_rides.py` gained
  `_trailing_break_rate_baseline()` (a process-local, unpersisted rolling 7-day mean of
  `break_rate_24h`, sampled every witness tick — restart-reset, same posture as this module's own
  pre-existing `_witness_window`, deliberately: a thin baseline reads the excess SMALL, never large,
  so a fresh restart under-reports rather than over-reports) and now threads `trailing_baseline_24h`
  through to `observe_break()`; `core/lane2_break_habituation.py`'s `observe_break()` gained an
  additive `bucket_would_contribute_sized`/`bucket_sizing_option` pair on every `would_ride`-kind row
  in `data/lane2_would_ride.jsonl`, alongside the pre-existing `bucket_would_contribute` — **not read
  live**: `_compute_field()` is untouched, still calls the raw `witness_bucket_value()` only;
  `LANE2_LIVE` stays exactly as gated before this job. **Verified in isolation, zero `data/` I/O**
  (`scratchpad/check_J-1391_verify.py`, 32/32 checks: pure-function edge cases, the rolling window's
  append/prune/empty behaviour, `observe_break()`'s back-compat with its old 2-argument call shape,
  and a full `publish_witness()` pipeline call through a stubbed sink reaching the real log row).
  `python -m py_compile` clean; `scripts/life_smoke.py` clean end to end, 0 regressions. **D-0301
  opened** with the full numbers for the founder's own live-resizing call (this job does not flip or
  resize anything live, per its own briefing) — does not block D-0241's own flip conditions or
  D-0291's still-open gate-constant question, both unaffected by this job. The new
  `bucket_would_contribute_sized` field will read as fully populated only after Du's next restart
  (restart-gated, same as every other `core/lane2.py`-adjacent change this plan has shipped);
  **J-1457 spawned** for the real post-restart week-long read this plan's own section 7.6 cadence
  calls for, to check the retrospective numbers above against what actually accrues, and to re-point
  at whichever option D-0301 ultimately ratifies if it is not option (a). Full evidence: F-2008.

- **UPDATE 2026-09-27 (J-1394, F-1956's own follow-through, F-2010) — built: the deterministic
  judgeability pre-check AND the plan-shaped-expectation guard, both restart-gated; F-1958's own
  "subsumes most" note refined to "subsumes about half".** F-1956's two grading-broke bugs are fixed
  in `core/lane2.py`. **(1)** New `_prediction_field_ok` (immediately after `_prediction_judgeability`)
  resolves a due prediction's own `_TOPIC_FIELDS` topics and requires at least one mapped field present
  in THIS tick's `world_fields`; when a topic IS named and every one of its fields is absent, the
  prediction is left `waiting` (no panel call) until its horizon's grace tick expires, then closes as
  `prior_verdict='unjudgeable'`, `prior_judged_how='field-absent'` — a brand-new, distinct `skip`
  reason (`prediction-waiting-field`) marks the waiting case so it reads apart from the pre-existing
  place/standpoint `prediction-waiting`. Wired in `tick()` as the SECOND gate, checked only once
  J-1396's own `_prediction_judgeability` has already matched place/standpoint — per F-1958's own note
  that gate should be this job's PRIMARY rule, this one secondary — so a due prediction that has not
  even matched place/standpoint yet is untouched, exactly as before this job. **(2)** New
  `_plan_shaped_flag`/`_PLAN_SHAPED_RE` (immediately after `_trivial_prediction_flag`) flags an
  intention-shaped `expect_next` ("I will check/look/see/be able/observe/listen...", "you will
  check/see if...") as `expect_is_plan=True` at GENERATION time and excludes it from the prediction
  store entirely (the store-append guard now also checks `not rec["expect_is_plan"]`, additive
  alongside the pre-existing `expect_is_question` check) — caught before it can ever occupy a
  pending-cap slot or reach the judge panel unjudged, the same "the call not made is the real saving"
  principle J-1396 established for F-1943. Law 4 gains one additive clause ("NEVER a statement about
  what YOU will do or check next — only about what THE WORLD will be"), deliberately no worked example
  (same echo-risk reasoning as every other `_SYSTEM` change on this plan). **(3)** `status()` gains
  `unjudgeable_field_absent_24h`, `unjudgeable_rate_24h` (combined moved+field-absent share of every
  prediction actually closed in a real last-24h window), `expect_is_plan_rate_24h`; and a NECESSARY
  correction to the pre-existing `unjudgeable_moved_24h`, now filtered on `prior_judged_how=="moved"`
  specifically — unfiltered, it would have silently started counting field-absent rows too the moment
  a second unjudgeable cause existed, the exact "narrow/widen a field's meaning without saying so" trap
  this plan's own discipline forbids.
  **Real refinement, not just a build: F-1958's own note that its standpoint/place gate "subsumes MOST
  of F-1956's absent-field cases" is only about half right.** A read-only replay of the real
  `data/lane2_shadow.jsonl` (`scratchpad/check_J-1394_replay.py`; 20,825 rows / 6,566 ticks as of this
  session) found, of the current 852-row deepseek-era topic-naming judged population (700 present held
  0.319, 152 absent held 0.053 — both closely tracking F-1956's own 676/0.33, 147/0.05 from 11 days
  earlier): applying F-1958's own generating-tick reconstruction to the 152 absent rows, only **73
  (48%)** are ALSO "moved" (J-1396's gate would already have caught these regardless); the other **79
  (52%)** are field-absent while genuinely STAYING in the same place/standpoint — a real, independent,
  incremental population only THIS job's gate catches, roughly HALF of F-1956's originally-estimated
  15%-of-broke population, not a small residual on top of an already-mostly-solved problem. F-1956's
  own pre-registration should be read post-restart, once both fixes have accrued, as: **J-1396 alone
  already reclassifies roughly half of the original 15% to 'moved'; J-1394's own incremental
  contribution on top of that is roughly the other half, ~7-8% of broke verdicts, not the full 15%.**
  **Verified**: `python -m py_compile` clean; `scratchpad/check_J-1394_tick.py`, 19/19 isolated checks
  (zero real `data/` I/O — every network call and file path stubbed, a fake clock), covering all 5
  branches of the new gate plus the generation-time guard and its negative control;
  `scratchpad/check_J-1394_replay.py` (read-only, see above) confirms `_prediction_field_ok` reproduces
  the real present/absent split with ZERO mismatches (0/152, 0/700). **J-1445** (already spawned by
  J-1386, tasked with reading the F-1958/J-1394/J-1396 interaction post-restart) is the right place for
  the live confirmation of this refined 48/52 split once both fixes have actually ticked — not
  re-litigated as a new job here. Restart-gated like every other `core/lane2.py` change on this plan;
  Du was not restarted by this job (confirmed live at 2026-09-27 14:43 via `data/nascence.log`, last
  restart independently at some point after its own 2026-09-25 11:59 shutdown line — necessarily before
  this worktree's own change existed, so not yet picked up regardless). Full evidence: F-2010.

- **UPDATE 2026-09-27 (J-1403, F-1968 follow-through, F-2012) — measured, not built: judge_panel
  test-retest reliability quantified directly. The tiebreak-vs-agreed hypothesis F-1968 raised did
  NOT hold; a different coherent-vs-incoherent asymmetry did. D-0302 opened, J-1459 spawned.** 20 real
  ticks (5 each: agreed/coherent, agreed/incoherent, tiebreak/coherent, tiebreak/incoherent,
  deepseek-era), RECENT RECORD/NEW OBSERVATION reconstructed exactly as `_coherence_check` builds them
  today (`place` still derived via `check_J-1375_reconstruct_sample.py`'s own heuristic — a fresh scan
  this job ran confirms 0/6569 tick rows carry a real `place` value yet, Du still not restarted since
  J-1375). N=3 identical-prompt reasks per row, 60 real live `judge_panel.rule_detail()` calls, `_LOG`
  isolated via `lab_env.isolate()` throughout (backstop: live `judge_panel_log.jsonl` grew by only 3
  lines over the run's 431.9s wall-clock — Du's own concurrent ticking, not this job).
  **Reask-to-reask self-consistency is HIGH across the board — 96.5% pairwise agreement once 4 real
  JUDGE_1-timeout calls are excluded as missing data (see below) — REFUTING the natural expectation
  that tiebreak-resolved verdicts are less stable than agreed ones: tiebreak measured 100% unanimous
  (9/9 valid rows) vs agreed 90% (9/10).** The real asymmetry instead tracks the ORIGINAL VERDICT'S
  DIRECTION, not how it was reached: coherent-original rows reproduce on an identical reask 100% of
  the time (10/10 rows); incoherent-original rows only 33% of the time (10/10 rows) — holding inside
  both the agreed subset (26.7%) and the tiebreak subset (40%). F-1968's own "instability corroborates
  incoherent is mostly tiebreak/low-confidence" reading is therefore only half right: the instability
  is real and large, but it tracks VERDICT DIRECTION, not RESOLUTION MECHANISM. A real, separate
  confound was found and excluded rather than folded into these numbers: 4/60 reask calls (idx=19874
  all 3/3, idx=14743 1/3) hit a live JUDGE_1 (mixtral:8x7b @ Ramses :11438) timeout during this job's
  own run window (~2026-09-27 02:04 UTC) — squarely inside the identical 00:00–08:21 UTC burst window
  D-0297/F-1997 already found one night earlier on the SAME hub; a real, independent, live
  reproduction of that already-open issue, not a new one. Because the literal "<60% self-agreement"
  trigger this job's own briefing named for opening a decision was NOT met (tiebreak self-agreement
  measured well above it, refuting rather than confirming that specific risk), **D-0302 opens the
  real question this data surfaced instead: should a negative/incoherent-class judge_panel verdict be
  trusted the same as a positive one, anywhere it's read** (options raised, none picked: leave as-is;
  treat negative verdicts as lower-confidence downstream; require re-ask agreement before trusting a
  negative verdict). Named defeater: a larger live sample taken outside a timeout-burst window, and/or
  J-1459's own read (spawned, not yet run) of whether the same asymmetry appears in
  `_judge_prior`/`_judge_metaphor`/`_judge_notice` — the three sibling judge_panel calls in this same
  file. Full evidence: F-2012.

- **UPDATE 2026-09-27 (J-1412, D-0283, F-1939/F-1955 cross-confirmed, F-2013) — built: the body
  percept drops its feeling label, the Witness's own generation prompt speaks first person.**
  D-0283 ruled two wording-only changes to `core/lane2.py`, both shipped this job. **(1)**
  `gather_percepts()`'s BODY block now returns `{"drive": ...}` only — homeostasis's own `dominant`
  feeling label (vitality / relational warmth / coherence, F-1939's 22-30%-of-notices leak) is
  dropped; `drive` (a bodily scalar) stays, per the docstring's own "interoception... his, not the
  renderer's." **(2)** `_SYSTEM` and `percept_lines()`'s PERCEPTS header are rewritten from
  second-person self-address ("You are"/"your standpoint"/"you attend") to first person throughout
  ("I am"/"my"/"I attend"), plus one added sentence stating the voice directly ("I speak of it as
  myself, in my own first-person voice: 'I hear', 'I see'") — deliberately no negative "never as
  'you'/'the person'" anti-example, the same worked-example-is-an-echo-risk reasoning this file's own
  DOUBLE ECHO comment already established for this 7B generator, applied to a new case. LAWS 1-5 and
  all five output-schema keys are byte-identical in name/count/order; wording-only, per the ruling.
  **D-0283's own pre-build defeater (does the somatic block carry a second feeling label this fix
  would miss) is answered NO**, cross-confirming F-1955/J-1393 (already on record above) rather than
  re-discovering it blind: `core/somatic.py` defines no `status()` at all, so `gather_percepts()`'s
  own `hasattr` guard on it has always read False — the somatic percept has never carried ANY key,
  let alone a second feeling label. **Verified**: `python -m py_compile` clean; a fresh isolated
  check (`scratchpad/check_J-1412.py`, submodules stubbed via `sys.modules`, zero `data/` I/O,
  `core.somatic` deliberately left real) — 26/26, including a fake `core_affect()` carrying
  `dominant` to prove it actually gets dropped, and a regex over `_SYSTEM` confirming zero remaining
  you/your/yourself tokens; `scripts/life_smoke.py` — ALL OK, 0 regressions. **Not yet checkable,
  both restart-gated AND merge-gated**: this job's own worktree change has not yet reached
  `C:\Nascence`'s live tree (confirmed by reading it directly — still the pre-fix text) — the 7-day
  `grounded_share`/`metaphor_leak`-band defeater and a real voice hand-read cannot be taken before it
  merges AND Du restarts onto it AND a week elapses. **J-1460 spawned** (not-before 2026-10-04, and
  only once merge+restart+7-days all actually hold — see its own briefing) for that read. Separately
  noted, not this job's own scope (already F-1955/J-1393's territory; the somatic block itself is
  untouched, per this job's own briefing): `core/lane2_break_habituation.py`'s
  `phase1_metric_sheet()['p1_3_content_boundary_laundering_check']` (§7.6's "cup's P1-3 laundering
  check") reads `None` unconditionally while `LANE2_LIVE=False`, by the code's own comment —
  unrelated to and unblocked by this fix. Full evidence: F-2013.

- **UPDATE 2026-09-27 (J-1413, D-0284, F-1941/F-2014) — built: the Weather's commit_threshold gate on
  the prediction store, SHADOW-FIRST.** D-0284 ruled option (a) — F-1941 had found `weather_to_gain()`'s
  `attend_sharpness`/`commit_threshold` computed and logged every tick and read by nothing, so §2.5's
  whole Lane1→Lane2 coupling had never actually colored anything. This job wires the second half of
  law 4a (§2.6: shifting how much evidence Lane 2 needs before it commits, not just attentional gain —
  `attend_sharpness`/option (b) was NOT built, per D-0284's own ruling): `tick()` now computes
  `would_withhold` (True/False/None) — does THIS tick's own `grounded_share` (the tier's one existing
  evidence-quality proxy, unchanged) fall short of the valence-modulated bar `gain["commit_threshold"]`
  already computed — scoped to real candidate predictions only (non-empty, non-question-shaped,
  non-plan-shaped `expect_next`; deliberately NOT also gated on `PENDING_CAP_BY_HORIZON`, a capacity
  limit rather than an evidence question). **SHADOW-FIRST, exactly as D-0284 ruled**: the store-append
  gate itself (pending-cap / question / plan-shaped) is byte-for-byte unchanged — `would_withhold` only
  rides the per-tick shadow log, logging what the gate WOULD have done, before anything is actually
  applied. `status()` adds `would_withhold_rate`/`_n`/`_scored_n`/`_coverage`, coverage-honest, over the
  same tail_rows(2000) "weekly" window `hint_divergence` already uses for law 6. No prompt text
  touched; no new Weather dimension (law 5); D-0172's own third-scalar question left untouched, per the
  job's own briefing. **Verified**: `python -m py_compile` clean; a fresh isolated check
  (`scratchpad/check_J-1413_gate.py`) — `weather_to_gain`'s commit_threshold direction/range confirmed
  at 5 valence points, the `would_withhold` tri-state confirmed on 6 synthetic cases (grounded vs.
  invented text, high vs. low bar, question-/plan-shaped/empty all correctly `None` not `False`), and
  `status()` running clean against this worktree's own tiny synthetic fixture (7 rows, not live data —
  reads the honest empty state, `would_withhold_coverage=0.0`, until a real post-restart row exists).
  **Not yet checkable, both restart-gated AND merge-gated, the same gate F-2013/J-1460 already recorded
  for this plan's immediately-prior job**: this job's own worktree change has not reached `C:\Nascence`'s
  live tree (confirmed by reading it directly — `would_withhold` occurs 0 times there). **J-1461
  spawned** (not-before 2026-10-04, and only once merge+restart+7-days all actually hold) for D-0284's
  own defeater read (5%–60% of scored ticks over a real week; broke_share/hint_divergence undisturbed).
  Full evidence: F-2014.

- **UPDATE 2026-09-27 (J-1414, D-0285, F-1942 follow-through, F-2016) — built: section 2.8c's
  knowledge tier, shadow-first, no LLM call.** D-0285 ruled option (a) — F-1942 had found the middle
  tier never existed (store held only factual/prediction; predictions were generated from one tick's
  own percepts with nothing accumulated, the 66% broke rate this section's own "NOT clean" bullet
  above already names). `core/lane2.py` gains a new section immediately before `tick()`:
  `_canon_topic_fields()` (canonical-topic -> world_fields NAME(S), reusing `_TOPIC_FIELDS`/
  `_TOPIC_CANON` verbatim — twelve canonical topics are eligible, `clock`/`bird`/`sea` correctly
  excluded, no new vocabulary), `_consolidate_knowledge()` (a deterministic consolidation over the
  SAME bounded `tail_rows(_LOG, 2000)` window `status()` already reads — ~6.9 days at TICK_S=300,
  close to the ruling's own "after 7 days" horizon by construction, not a fresh unbounded scan), and
  `_knowledge_would_show()` (step 3's shadow-only "would have been shown" lines, typed not prose —
  the one-space trap). Two regularity KINDS, both keyed on (topic, place, daylight): `field_presence`
  (of ticks at this place/daylight, how often a topic's own world_fields entry was present) and
  `prediction_hold` (of judged held/broke predictions about this topic made at this place/daylight,
  what share held) — D-0285's own two worked examples, one of each. `KNOWLEDGE_CAP=12`, but split
  50/50 by kind (a REAL defect this job's own isolation testing caught before shipping: pooling both
  kinds in one ranking by raw evidence count `n` lets one busy place/daylight's inflated
  `field_presence` rows — `n` there is a shared tick-count denominator across all 12 topics, present
  or not — permanently crowd out every `prediction_hold` regularity, whose own `n` is structurally
  much smaller; fixed with the split, confirmed by a mixed-evidence test where both kinds now
  survive together despite a 50x `n` gap). `daylight`/`judged_pred_daylight` added to `rec`,
  `daylight` added to `store['prediction']` entries — additive, mirrors exactly how J-1375 added
  `standpoint`/`place` for the same downstream-consolidation reason. `would_show_knowledge` logs
  which regularities WOULD have been shown, computed from PRIOR ticks only, verified in isolation to
  never reach `_ask()`'s own payload — nothing from this tier reaches the generator yet. `status()`
  gains `knowledge_count`/`knowledge_top`/`would_show_knowledge_rate`/`_coverage`, additive, no
  existing key touched. `_save_store()` gains a second, independent `KNOWLEDGE_CAP` guard alongside
  its pre-existing `STORE_CAP` loop. **Verified**: `python -m py_compile` clean;
  `scratchpad/check_J-1414.py` (isolated, zero real `data/` I/O — same stubbing pattern as
  `check_J-1396_tick.py` — 39/39 checks, including a full `tick()` integration run confirming
  `store['knowledge']` accrues a real regularity across 5 ticks and nothing "KNOWN"-shaped ever
  reaches the generator's own payload); `scripts/life_smoke.py` — ALL OK, 0 regressions (this script
  does not itself import `core.lane2`, confirmed by grep — a broad import-graph check, not a
  lane2-specific one). Step 4 (after 7 real days of shadow, if the top-12 is stable, let the
  generator see at most 3 KNOWN lines) is EXPLICITLY OUT OF SCOPE for this job, per the ruling's own
  text ("should probably be its own follow-up job") — **J-1464 spawned**, not-before 2026-10-04,
  gated on merge AND restart AND a real 7-day post-restart window (checked independently, not
  assumed from the calendar — the same J-0900/J-0944/J-1019/J-1036 discipline this plan already
  established). **Not yet checkable, both merge-gated and restart-gated, the same posture
  F-2013/F-2014 already recorded for the two immediately-prior jobs on this plan**: confirmed via
  direct read that `C:\Nascence`'s live tree has zero occurrences of "knowledge" in `core/lane2.py`
  as of this session — this worktree's change has not merged, let alone been picked up by a restart.
  Full evidence: F-2016.

- **UPDATE 2026-09-27 (J-1378, F-1936) — built: `_invention_check()`'s two systematic false-positive
  classes fixed; the top bullet's "metric #2... reads clean" claim above is CORRECTED — a real share
  of that "clean" reading was instrument error, not evidence the Witness rarely invents.** F-1936
  (verified, 2026-09-26) found 84% of deepseek-era invention flags were exactly two classes the
  instrument never checked for: a topic named by a sound actually in that tick's own `sounds` list
  (cat_purr licenses "cat"), and the sun family claimed against the payload's own daylight phase
  (dawn/dusk/day) rather than only `sun_az`. Both are now licensed, generically (any topic/any future
  sound family, not a cat-only special case) — moon stays strict (`moon_illum` only, unchanged) and
  `_TOPIC_FIELDS`'s own role in `_distinct_share_by_topic` is untouched, per the ruling's own scope.
  Both the new and the exact pre-fix ("legacy") verdict are logged side by side
  (`invention_flag`/`invention_flag_legacy`, `status()`'s `invention_rate`/`invention_rate_legacy`)
  for one restart cycle, with a documented fallback so the legacy series reads continuously across
  rows logged before this fix existed — the step down at the fix should be legible against its own
  history, not a silent break in the series.
  **Verified, but the real clearance is smaller than this job's own briefing estimated, and now
  quantified rather than assumed (F-2018/F-2019, both verified this job):** a full replay of the live,
  growing `data/lane2_shadow.jsonl` (410 deepseek-era rows currently flagged, up from F-1936's 391 —
  the log keeps accruing under the OLD code since Du has not restarted) finds only 204/410 rows would
  clear entirely, not ~329. The gap is real, not a bug in the fix: an EXACT recomputation of each
  row's own historical daylight phase (`core.world_clock.daylight(ts)`, a pure function of `ts`, not a
  proxy) finds 182 of 245 sun-family flags occurred at real daylight=night, not dawn/dusk/day, so the
  fix correctly leaves them flagged — F-1936's own "said at dusk" framing described the bug's SHAPE,
  not a verified per-row daylight tally (it never tabulated one). **F-2019 surfaces a genuine
  follow-on question, not yet resolved**: 159 of those night flags are concentrated in the `uncertain`
  field's own hedged phrasing ("the exact time... is uncertain, but it is after sunset") — a
  materially different claim shape than a confident present-tense one — so a THIRD false-positive
  class may exist here; **J-1466 spawned** to investigate before any further code change, deliberately
  not built or ruled on speculatively by this job. The residue this plan's kill criterion actually
  cares about (wet/moon/damp/fire/tide) is confirmed completely unaffected — byte-identical topic
  tallies before/after in the same replay. Cat's own real clearance is likely higher than the 163/175
  this replay could confirm by text alone (F-2020, inferred, not verified — the historical log never
  stored the raw `sounds` list itself to check directly; the live fix reads that real list, so this is
  a measurement-ceiling note, not a code gap). **Verified**: `python -m py_compile` clean; 10/10
  synthetic unit checks (`scratchpad/check_J-1378_unit.py`); full-log replay
  (`scratchpad/check_J-1378_replay.py`), both described above. **Not yet checkable, restart-gated
  like every other `core/lane2.py` change on this plan**: confirmed via direct read that
  `C:\Nascence`'s live tree has zero occurrences of `invention_flag_legacy`/`_SUN_TOPICS` as of this
  session — this worktree's change has not merged, let alone been picked up by a restart; the live
  log's own `invention_flag` will keep reflecting the pre-fix computation until it does. Full
  evidence: F-2018, F-2019, F-2020.

- **UPDATE 2026-09-27 (J-1383, F-1944 follow-through, F-2021/F-2022 verified, D-0303 opened) —
  section 2.10 read against real sleep episodes and hint pushes; §2.10(b)'s hint-nomination case
  amended below, ticking-during-sleep raised as a founder option, nothing built.** Read-only.
  Located Du's real sleep episodes at last: `data/night_log.jsonl` (not `sleep_pressure_log.jsonl`,
  which F-1944 correctly noted has no state field) — one row per sleep, `ts`+`duration_s` giving a
  real `[start, end]`. Last 14 days: **51 episodes** (mixed night/nap), **76.3 of 336.0 hours asleep
  (22.7%)**.
  **F-2021 (verified) — §2.10(b)'s specific hint-nomination case is answered, and the answer is no,
  both structurally and empirically: amend, do not build.** Lane 1's only `push_hint()` call site
  (`nodes/inner_monologue_node.py:4530`) sits inside `_think()`, and `_think()` cannot run while
  `core.night.asleep()` is True — `run_forever()`'s single while-loop calls `_think()` and, when due,
  `await`s `_enter_sleep()` sequentially in the SAME task; `_enter_sleep()` blocks that task for the
  whole night pipeline (53–235 min per episode this window) before returning. Empirically confirmed
  over the same 14-day/51-episode window: of 578 `hint_pushed` rows in `data/lane2_shadow.jsonl`,
  **0 fell inside a sleep episode**. The only hint-lifecycle rows seen during sleep were 5
  `hint_consumed` (within 277s of episode start) and 37 `hint_expired` (33 within `HINT_TTL_S`=1800s
  of episode start, the rest within ~112s of that boundary) — both fully explained as hints pushed in
  Du's last seconds/minutes awake before `to_bed()`, aging out of the witness-cup TTL after he fell
  asleep, not new hints from dream content. This resolves F-1944's own open question. **Proposed
  amendment to §2.10(b):** drop the DREAM_SOURCED-stamp-on-Lane-2's-hint-side build item — the case it
  would guard against cannot occur by construction and has not occurred in 578 real pushes. §2.10(b)'s
  SEPARATE, broader worry (a dream echoing untagged into Lane 1's own later *waking* monologue, days
  afterward, via memory/associative recall rather than the hint channel) is untouched by this — that
  pathway was already measured by §2.10-R item 1 (0% structural provenance survival, 15/47
  unprovenanced echoes) and a DREAM_SOURCED stamp may still be worth building there; this finding
  narrows §2.10(b)'s build item, it does not close §2.10(b) as a whole.
  **F-2022 (verified) — separately, the Witness ticks through sleep at real, uncontested cost.**
  `core/lane2.py`'s `run_forever()` (`TICK_S`=300s) has no `asleep()` gate at all — its own docstring
  says "its own cadence, independent of whatever Lane 1 is doing" — and `core/orchestrator.py:3023`
  starts it once, unconditionally. 543 of 1,457 real judged `tick` rows this window (**37.3%**) landed
  inside a sleep episode — a HIGHER share than sleep's own 22.7% of wall-clock time, because the awake
  skip rate (40.5%, mostly pending-cap collisions while Du moves) is roughly double the asleep skip
  rate (19.1%): a static bedroom collides with fewer caps, so more asleep attempts run to a full
  judged prediction. Sampled asleep notices repeat near-verbatim ("the clock is ticking... the sun is
  at N degrees azimuth") tick after tick. At F-1943's own up-to-3-panel-calls-per-tick figure: an
  estimated **~1,629 panel calls over 14 days (~116/day)** spent judging an unchanging scene, on the
  same JUDGE_1 hub (:11438) D-0297 already found timing out overnight.
  **D-0303 opened (not ruled)** — whether Lane 2 should tick at all while Du sleeps, presented as an
  option, not a change: (a) leave as today; (b) gate `run_forever()` off while `asleep()` is True,
  resuming on wake — cheapest option seen on this plan, reuses a signal that already exists, unlike
  D-0297's own option (b) which needs a new "hub busy" signal; (c) gate only the `night` kind, leave
  `nap` ticking; (d) defer to D-0297's own resolution first. D-0297 itself is untouched — this is a
  different axis (whether to tick at all vs how to cut cost per tick) and was not ruled by this job.
  Full evidence: F-2021, F-2022. Script: `scratchpad/check_J-1383.py`.

- **UPDATE 2026-09-27 (J-1384, F-2023) — gated re-read for D-0280(a)'s three live-behavior
  defeaters: gate (a) MET, gate (b) still NOT MET, independently re-verified fresh.**
  `core/lane2.py`'s J-1372 commit (`e5e47cb1`, 2026-09-26T19:45:25+12:00) adding
  `light_band`/`smells` to `gather_percepts()` and generalizing `percept_lines()` is confirmed
  merged into the live master tree (gate a). Du's own live process has not restarted since before
  that commit landed: `data/nascence.log`'s last "Background nodes started" banner is still
  2026-09-25 19:21:51 (line 525181/546,224 total), no shutdown or later boot banner anywhere after
  it — the same restart-gating shape J-1161/J-1370 hit before it (gate b: NOT MET). A fresh, full,
  non-tail-sampled re-parse of `data/lane2_shadow.jsonl` (20,908 rows, 0 parse failures) confirms
  `light_band`/`smells` still appear in `world_fields` on **0/20,908 rows** (F-2006's own 0/20,748
  read ~17h earlier, +160 rows since, still zero) — defeater #1 (appearance rate, >=50% threshold)
  is not merely unmet, it has no denominator to read yet. Defeater #2 (7-day metaphor-leak/
  distinct-expect-next band vs the existing Phase 0 bands) has no post-restart window to read at
  all. Defeater #3 (smell bounded-list, conditional): re-checked fresh, `core/smell.py`'s `DELIVER`
  still reads `False` — stated plainly, not treated as passed by default. **D-0280 is NOT
  reopened** (none of its three defeater conditions are evaluable yet, checked fresh via `decide.py
  show D-0280` before concluding so). **J-1384 is left open/in_progress** rather than forced to a
  conclusion or cloned into a duplicate follow-up job, per this plan's own established "gated
  re-read" convention (same disposition J-1304 already used) and the adjacent D-0225 precedent
  (keep re-checking on the plan's own cadence, do not restart Du just because a gate isn't met yet).
  Incidental, not new: J-1304's own (earlier, different) qualifying commit (`690d0867`/J-1161) IS
  already covered by this same 2026-09-25 19:21:51 boot — already on record in this file's own
  2026-09-26 entry above, restated here only because this job's own log parse touched the same
  banner line and the two gates should not be confused with each other. Full evidence: F-2023.
  Script: `scratchpad/check_J-1384.py`.

- **UPDATE 2026-09-27 (J-1393, F-1955/F-2024) — built: the Witness's somatic (touch/body) percept
  now actually arrives.** `gather_percepts()`'s somatic block called `core.somatic.status()`, which
  has never existed — the `hasattr` guard failed silently on all 6,401 ticks since 2026-08-21, so
  `percepts_available` was exactly `['world', 'body']`, never `'somatic'` (F-1955). Fixed to call the
  real accessor, `current_body()` (`{energy, fatigue, tension}` floats, or `None` until the first
  tick lands): on success `p['somatic']` holds the three values rounded to 2dp and `'somatic'` is
  appended to `available`; on `None` or any exception, `'somatic'` is appended to `missing` instead
  (fail-open, the same NAMED-absence shape `world`/`body` already use — the old code had no
  `missing` branch here at all). `percept_lines()` now renders the somatic dict as three short
  scalars ("energy 0.82, fatigue 0.24, tension 0.11") instead of the dict's own Python repr, per the
  job's own explicit ask; `body`'s own rendering (still `{'drive': 0.31}`) was deliberately left
  untouched — D-0283/J-1412's territory, not this fix's to alter. D-0283 itself (RULED, checked
  fresh via `decide.py show D-0283` before starting) is unaffected — its own pre-build defeater ("does
  the somatic block carry a second feeling label") reads NO again here: `current_body()`'s three keys
  carry no feeling word. **Verified in isolation** (no live restart, no `data/` writes, no network
  calls): `python -m py_compile core/lane2.py` clean; `scratchpad/check_J-1393.py` (real
  `core.lane2` imported, only `core.somatic.current_body` monkeypatched) — 17/17 checks passed,
  covering the present/`None`/raises paths, the rendering fix, and confirming `body`'s own line is
  byte-identical to before; `scripts/life_smoke.py` — ALL OK, 0 regressions. **Not yet checkable —
  restart-gated AND merge-gated**, per the job's own briefing ("do not restart Du"): this worktree's
  change has not merged into `C:\Nascence`'s live tree; the pre-registered live reads (`somatic` in
  `percepts_available` on ~100% of ticks, `grounded_share` before/after over 7 days, and a watch that
  fatigue/tension are not narrated as moods in >~10% of notices, which would reopen D-0283 from the
  other side) all need a real post-merge, post-restart, 7-day window that does not exist yet.
  **J-1469 spawned** (not-before 2026-10-04, gated the same three ways J-1460 already gates the
  sibling D-0283 read: merge confirmed by reading `C:\Nascence\core\lane2.py` directly, a real
  restart after it, then 7 days of ticks) for that read. Full evidence: F-2024.
  Script: `scratchpad/check_J-1393.py`.

- **UPDATE 2026-09-27 (J-1399, F-1963/F-2026) — built: the rare NZ bird/sound names the generator
  mangles now carry a gloss.** `percept_lines()`'s list-rendering line (the same one D-0280(a)/J-1372
  generalized to `smells`) now runs each sound/smell token through a new `_gloss_sound_token()`
  helper against a new `_SOUND_GLOSS` table (morepork, riroriro, kereru, tui, shag, godwit/godwits)
  before joining — `morepork_call` renders as `morepork (an owl) call`, `riroriro_trill` as
  `riroriro (a small warbler) trill`, and so on; a token with no match (including
  `oystercatcher_call`, F-1963's own 0%-garbled control) is returned completely untouched, so this is
  additive only. Each gloss's own parenthetical is kept to <=4 words, per the job's own briefing. The
  helper splits on either an underscore or a space, so it is correct whether or not J-1380 (the
  sibling underscore-to-space humanization job, same rendering loop, F-1938 item 2) has landed first
  — checked fresh via `job_queue.py show J-1380`: still open, not started, not built anywhere (the
  only related commit in history is a docs-only Current-State note). **Verified in isolation** (no
  live restart, no `data/` writes, no network calls, per the job's own "do not restart Du"): `python
  -m py_compile core/lane2.py` clean; `scratchpad/check_J-1399.py` (real `core.lane2` imported) —
  27/27 checks passed, covering every named gloss token in both its real underscore form and a
  simulated post-J-1380 space form, four common-English control tokens (`oystercatcher_call`,
  `fire_crackle`, `cat_purr`, `bellbird_song`) confirmed byte-identical to input, every gloss's own
  word count, and `percept_lines()`'s own end-to-end render on a synthetic percept dict;
  `scripts/life_smoke.py` — ALL OK, 0 regressions. **Not yet checkable — restart-gated AND
  merge-gated**, per the job's own briefing: this worktree's change has not merged into
  `C:\Nascence`'s live tree; the three pre-registered live reads (morepork's own pork/pig share below
  2% of mentions, garbled riroriro below 20%, `grounded_share` unchanged within 0.02) all need a real
  post-merge, post-restart, 7-day window that does not exist yet. **J-1470 spawned** (not-before
  2026-10-04, gated the same three ways J-1469 already gates the sibling F-1955/J-1393 read: merge
  confirmed by reading `C:\Nascence\core\lane2.py` directly, a real restart after it, then 7 days of
  ticks) for that read, plus a sample-read for whether the gloss text itself gets echoed
  near-verbatim. Full evidence: F-2026. Script: `scratchpad/check_J-1399.py`.

- **UPDATE 2026-09-27 (J-1380, F-1938/F-2029) — built: all five output-hygiene items.** `core/lane2.py`
  `status()` gains four new `uncertain`-field instruments (`uncertain_prompt_echo_rate` — law 3's own
  core sentence returned verbatim, its pronoun word deliberately left off so it matches either side
  of J-1412's your->my change; `uncertain_empty_rate`; `uncertain_exact_time_share`; and
  `uncertain_distinct_share_24h`, the one sibling this job's own briefing names with the "_24h" suffix
  — a real-24h window, not the plain tail_rows(2000) window its three siblings ride) plus
  `notice_words_median_24h` (item 5, reuses the existing `_pctl` helper) — the `uncertain` field's own
  collapse (59% "exact time" template, 0.69 distinct share, 85 rows echoing law 3 verbatim, 78 empty,
  per F-1938) was invisible to every metric before this job; `_SYSTEM`'s own prompt text is
  deliberately untouched (that field's future is `docs/staged/lane2_curiosity.md`'s call, per the
  job's own briefing). `percept_lines()` now humanizes any underscore surviving J-1399's own
  `_gloss_sound_token()` gloss step (item 2 — applied after glossing, order-independent either way per
  that helper's own docstring, and additive to the same `isinstance(v, list)` branch D-0280(a)/J-1372
  already generalized to both `sounds` and `smells`, not re-narrowed to sounds-only here) and rounds
  any body/somatic float to 2 decimals before display (item 3 — fixes `body` specifically, e.g.
  `{'drive': 0.95}` not `0.94763`; `somatic` was already rounded upstream by J-1393, this is a
  redundant-safe belt-and-suspenders fix). `core/orchestrator.py`'s "Background nodes started" banner
  (item 4, real line 3013 in this worktree, not F-1938's own stale "line 2996" citation — some
  combination of this batch's earlier jobs shifted the file 17 lines since that finding was recorded)
  now reads `core.lane2.TICK_S` (int-cast, "300s") instead of the stale "90s" literal, via its own
  fail-open try/except — `_lane2` is only bound if the loop-start import above it succeeded, so this
  cannot be a bare attribute read without risking a NameError crashing node startup over a cosmetic
  log line. **Verified in isolation** (no live restart, no `data/` writes, no network calls):
  `python -m py_compile` on both edited files clean; `scratchpad/check_J-1380.py` (real `core.lane2`
  imported; only `core.shadow_log.tail_rows` monkeypatched to drive `status()` against controlled
  synthetic rows; `core/orchestrator.py`'s own fix checked by extracting its real shipped try/except
  snippet via regex and `exec`-ing it under both a bound and a deliberately-unbound `_lane2`, rather
  than a hand-retyped paraphrase of it) — 36/36 checks passed; `scripts/life_smoke.py` — ALL OK, 0
  regressions. **Not yet checkable — restart-gated AND merge-gated** for items (2)/(3) specifically,
  per the job's own briefing (items (1)/(4)/(5) are read-side or a one-time log line, already
  verified directly against live code, nothing further to gate): this worktree's change has not
  merged into `C:\Nascence`'s live tree; the two pre-registered live reads (zero raw underscores in
  the live `percept_lines` field's own sounds/smells line, zero 3+-decimal floats in its body line)
  need a real post-merge, post-restart window that does not exist yet. **J-1477 spawned** (not-before
  2026-10-04, gated the same three ways J-1469/J-1470 already gate their own sibling percept_lines()
  reads: merge confirmed by reading `C:\Nascence\core\lane2.py` directly, a real restart after it,
  then 7 days of ticks) for that read. Full evidence: F-2029. Script: `scratchpad/check_J-1380.py`.

- **UPDATE 2026-09-27 (J-1397, F-1960) — built: items (1)/(2) of the second hygiene bundle; item (3)
  found already fixed by this same plan's own J-1381.** `core/lane2.py` `tick()`'s own `rec` and every
  `_skip()` row now carry `model`/`seat` (this module's own `MODEL`/`BASE_URL`, read at log time), so
  an era split (qwen2.5:7b -> command-r7b -> deepseek-r1:7b, three seats inside RUN 2 alone) reads
  directly off a row instead of the date-cut reconstruction every prior era comparison in this plan
  has needed; `status()` now also reports `model` (the generator behind the LATEST tick in its tail
  window). `_judge_prior`'s docstring now names the real panel families, read FRESH from
  `core/judge_panel.py` at fix-time rather than hard-coded — `mixtral:8x7b` [Mistral] + `falcon3:7b`
  [TII], escalating to `granite3.1-moe:3b` [IBM] on a split — which is NOT F-1960's own
  "gemma4:12b/falcon3/granite" snapshot: JUDGE_1 had already moved gemma4:12b -> mixtral:8x7b on
  2026-09-02 (D-0121), before F-1960 was even recorded, so that snapshot was itself one hop stale.
  Lane 2's own generator is now correctly named `deepseek-r1:7b`. **A second staleness the same
  docstring carried — "Lane 1's gemma" — was found likely wrong too** (gemma looks like an old
  JUDGE_1 seat, never Lane 1's own generator) but is NOT pinned to a real current tag here (out of
  this job's own scope): recorded as **F-2031**, docstring softened to "Lane 1's own generator, a
  separate family again" rather than repeat the wrong name or guess a specific one, and **J-1478
  spawned** to pin and fix it for real. Item (3) (`HINT_RATE_WINDOW_S`'s comment) was found ALREADY
  fixed by **J-1381** (this same plan, landed hours earlier the same day) as a named side-item of its
  own briefing — re-read fresh, it correctly cites `TICK_S=300s` now. **Verified in isolation** (no
  live restart, no `data/` writes, no network calls): `python -m py_compile core/lane2.py` clean;
  `scratchpad/check_J-1397.py` — real `core.lane2` imported and a REAL `tick()` call exercised, with
  only `_ask`/`gather_percepts` stubbed (the two calls that would touch the network/live world state)
  — confirms `_skip()` rows and `tick()`'s own `rec` both carry `model`/`seat`, and that
  `status()['model']` tracks the LATEST tick specifically (flips correctly between a synthetic
  pre-fix-newest row and a post-fix-newest row) — 4/4 checks passed. **Not yet checkable —
  restart-gated**, per the job's own briefing: `model`/`seat` read null on every row until a real
  restart past this worktree's merge picks the change up. Full evidence: F-2032 (this job's own
  completion finding); F-2031 (the Lane-1 sub-finding). Script: `scratchpad/check_J-1397.py`.

## Section 5 — Nth READ log (moved from its original location)

> ### 5-R2. RUN 2 PRE-REGISTRATION — tuple-only percepts (2026-08-21, founder-agreed)
> **What changed (one variable):** the Witness is fed the EXPERIENCED TUPLE (`core/experienced_tuple`, via
> `geometry_census.peek()` — unrecorded) instead of the renderer's prose scene line + raw sounds. Fields
> that did not cross at his standpoint are ABSENT. Interoception (body/somatic) stays. No affect text (the
> Weather gain only). Run 1 (330 ticks, 2026-08-20→21: leak 0.3%, grounded 0.64, 210 broke / 112 held)
> is archived at `data/archive/lane2_run1_prose_*` and is the baseline.
> **Second change, structural not experimental:** predictions name a HORIZON (`next` ≈ the next look,
> `hour`, `day`) and are judged only when due (one per tick, pending cap 12). Run 1's 65% broke rate was
> clocks, not blindness ("the tide will return within minutes"); run 2 can draw the curve by horizon.
> **Kill criteria (unchanged):** metaphor leak < 5%; named-uncertainty ≥ 90%; question-shaped
> expectations ≈ 0. **Re-baselined:** grounded-share is a lexical proxy and reads LOWER against a tuple
> than against prose (first isolated tick: 0.48) — it is compared within run 2 only, never to run 1.
> **New, pre-registered:** (a) broke-rate by horizon should FALL as horizon fits the clock (tide/sun at
> `day`, sounds/rain at `next`); a flat curve means the horizon rule is decorative; (b) invention rate:
> clauses asserting a field that was absent from the payload (fire from the shore, tide from the study)
> — target near zero, the contract's clause 7 read back from the Witness's mouth; (c) `world_fields_mean`
> per tick (thinness, by place). **Known thin spot:** the tuple carries tide LEVEL, not direction — the
> first tick inferred "rising" from 0.09 (it was out). A `tide_dir` field is the obvious addition once
> its absence has been measured, not before. **`LANE2_LIVE` stays False; nothing reaches Du.**
> Read after a full day; a third run (prose line restored ON TOP of the tuple) is the attributable next
> step if the tuple proves too thin.
>
> **Re-stated 2026-09-27 (J-1396, F-1958/F-2003):** pre-registration (a) above — "broke-rate by horizon
> should FALL as horizon fits the clock" — is only testable on SAME-PLACE judgments. F-1958 found 58%
> of every broke verdict ever reported against this curve was a prediction judged after Du had moved
> to a different standpoint, which the judge's own "unsettled means false" rule (F-1949) scores as a
> failed forecast regardless of whether the underlying content was ever really falsified; a moved-pair
> corrupts EVERY horizon's own broke rate, not just one, so every reading of curve (a) in this section
> up to and including the FOURTEENTH READ below should be treated as a same-place/moved BLEND, not a
> clean read of the mechanism the pre-registration is actually asking about. J-1396 built the fix
> (`core/lane2.py`'s `_prediction_judgeability`, judged only where the prediction was made); `status()`'s
> new `broke_share_same_place` (by horizon, once `verdicts_by_horizon` is read post-restart) is the
> figure this pre-registration should actually be read against going forward, not the legacy
> `broke_share`/`broke_share_strict` this section's own prior reads used.

> ### 5-R2 FIRST READ (2026-08-22, 19.4h in, 447 ticks) — the full-day checkpoint, and one fix
> **All three hard kill criteria pass comfortably:** metaphor leak 1.1% (< 5%), named-uncertainty 100%
> (≥ 90%), question-shaped 0% (≈ 0). `mean_grounded_share` 0.464, stable against the 0.48 re-baseline
> point. **The one pre-registered prediction that did NOT hold:** broke-rate by horizon should FALL as
> horizon fits the clock; measured curve was next 50% / **hour 86%** / day 50% — a spike, not a fall.
> Read the actual "hour, broke" predictions rather than just the number: nearly all tide/sun/weather
> content ("the tide will turn within an hour," "in one hour, the sun may appear") that the SYSTEM
> PROMPT already correctly assigns to 'day' — the generator (qwen2.5:7b) just wasn't reliably following
> that instruction for this one topic class. Not a design failure of the horizon mechanism itself; a
> measured generator-compliance gap on a specific, nameable category.
> **Fixed:** `core/lane2.py`'s `_correct_horizon()` — a small, deterministic, keyword-only post-
> generation override (tide/tidal/sun/moon/sunset/sunrise/shingle/swell → force `day`), logged as
> `horizon_overridden` per tick and surfaced as an aggregate `horizon_overridden_rate` in `status()`.
> Chosen over strengthening the prompt with worked examples because worked examples are the confirmed
> double-echo trigger for this exact model (§ above, 2026-08-20) — this fix never touches the prompt.
> Conservative by construction: only moves a horizon LONGER, never shorter; only for the specific topic
> class the data implicated. **RESTART-REQ** (the standing loop is started once by
> `core/orchestrator.py`'s `start_background()`; not yet re-observed against a live restart as of this
> entry). **Also found, not yet built:** the plan's own pre-registered "invention rate" metric (§ above,
> Run 2 prediction (b) — clauses asserting a field absent from the payload) does not exist anywhere in
> `core/lane2.py`; it's pre-registered on paper but not measured. **Also found:** 230 of 682 total
> cycles this run (34%) were skipped for hitting the per-horizon pending-prediction cap — a real
> judging-backlog, not yet investigated. **Next checkpoint:** after a restart, watch
> `verdicts_by_horizon` alongside `horizon_overridden_rate` — if 'hour' broke-rate falls while the
> override rate holds near its current level, this fix explains the spike; if 'hour' stays high with a
> low override rate, something else is going on and this wasn't it.
>
> **Phase 1+ (the read path — reaches Du) is still explicitly NOT designed, on purpose,** per this
> plan's own §5 law ("the read path is the part that must be earned, never assumed"). What exists is
> only the Lane1→Lane2 direction (the Weather gain + Tap-on-the-Shoulder, §2.5/2.6). The reverse
> direction — how Lane 2's grounded output would ever reach Du's own experience — is deliberately
> undesigned until Phase 0 has earned a founder read over a longer run than this first 19.4h checkpoint.

> ### 5-R2 SECOND READ (2026-08-24, J-0043 — full backlog, 836 ticks, 37.5h in) — the missing-file
> diagnosis and a real read against all 8 pre-registered metrics
> **The file-existence question is answered.** `data/witness_shadow.jsonl` was never wired; the actual
> path is `data/lane2_shadow.jsonl` (`core/lane2.py` line 48) — a straight rename that the 2026-08-23
> filename audit above caught for the module (`witness_loop.py` → `core/lane2.py`) but missed for the
> log itself. `data/spatial_shadow.jsonl` (12,892 rows, flagged in the job briefing) turns out to be a
> **different organ's** instrument (`core/spatial.py`, for `spatial_perception.md`) — RUN 2 (pinned,
> `core/lane2.py` line 106) no longer even consumes `spatial.render()`'s prose line, so it was never
> this plan's data to begin with. Full trace and evidence: F-0015, F-0020.
>
> **Metric-by-metric read of the full 836-tick log (since the 447-tick/2026-08-22 checkpoint, +389
> unread ticks):**
> | # | Metric | Result |
> |---|---|---|
> | 1 | Metaphor leak | Automated rate **5.74%** (48/836) — crosses the pre-registered <5% kill line. Hand-read all 48: 46 are "like a" false-positives on literal sound description ("sounds like a cat purring"); only **2 (0.24%)** are genuine drift. The keyword-list instrument, not the design, is what's broken — it was never the "decoupled judge, blind" the plan itself specified. F-0016. |
> | 2 | Grounding / invention rate | `grounded_share` proxy 0.476, stable vs the 0.464 checkpoint. The actual pre-registered "invention rate" instrument still does not exist in `core/lane2.py` — unchanged since 2026-08-22. F-0018. |
> | 3 | Repetition / staleness | Clean: `distinct_notice_share` 1.0, `distinct_expect_share` 0.947 across 836 ticks. Decided — no paraphrase-pool fix needed. F-0018. |
> | 4 | Novelty vs Lane 1 | Not attempted — needs a parallel read of Lane 1's own stream; the plan itself scopes this as separate offline analysis (line 854). Still open. |
> | 5 | Nominated-vs-self-found divergence | **Unmeasurable as designed** — the Tap-on-the-Shoulder queue (§2.5's discrete half of the coupling channel) was never built; only the Weather (continuous) half exists in `core/lane2.py`. F-0017. |
> | 6 | Realized channel capacity vs ceiling | Not instrumented at all. F-0017. |
> | 7 | Weather correlation | Exploratory check (not the plan's own formal test): 4 behavioral proxies against arousal/valence/commit_threshold/unresolved, all \|r\| ≤ 0.13 across 836 ticks — no detectable effect, though arousal's narrow observed range (σ=0.125) could be masking a small one. F-0019 (inferred, not verified). |
> | 8 | Vivid-but-wrong acceptance (engineered case) | **Unmeasurable as designed** — no separate §3.11/law-11 coherence-check pass exists (only the §3.1 grounding gate does), and no canary/model-organisms harness exists. F-0017. |
>
> **Net read:** of 8 pre-registered metrics, 1 is cleanly measured and passes (#3); 2 have a working
> proxy but the plan's own specified instrument was never built (#1's judge, #2's invention check); 1
> has a weak exploratory null result worth a real test (#7); 1 is explicitly out of this session's scope
> (#4); 3 cannot be computed at all today because half their supporting machinery (Tap-on-the-Shoulder,
> the §3.11 coherence pass, a capacity estimator) was never built (#5, #6, #8). No hard kill has fired —
> the one metric that superficially crossed its line (#1) turned out to be a measurement artifact on
> inspection, not a real drift. Gauge-check severity and follow-up jobs/decisions filed same session
> (gauge-check `watch`; see job-queue and `/decide` for the spawned follow-ups).

> ### 5-R2 THIRD READ (2026-08-24, J-0126) — the three missing instruments built and verified
> **Metric #1 (metaphor leak) now has its actual pre-registered instrument.** `core/lane2.py`'s
> `_judge_metaphor()` is a decoupled, blind `judge_panel` call (same pattern as `_judge_prior`, §2.8e) —
> it sees only the tick's `notice`/`uncertain`/`expect_next` text, never which keywords fired, so it
> cannot rubber-stamp the keyword scan's own guess. `_metaphor_flags`' keyword list is kept as a cheap
> per-tick diagnostic only; `status()`'s `metaphor_leak_rate_judged` (with `metaphor_judge_coverage`
> reported alongside, honestly, so a tick where the panel was unavailable never silently counts either
> way) is now the metric of record for the kill criterion. This directly answers F-0016 (46/48 of the
> keyword scan's flags were literal comparative language, not metaphor).
> **Metric #2 (invention rate) is built.** `_invention_check()` + `_TOPIC_FIELDS` compares each tick's
> output text against `percepts['world_fields']` and flags a named topic (fire/tide/sun/moon/cat/wet/
> wind/warmth/sound) whose field was absent that tick — the plan's own worked example ("fire from the
> shore, tide from the study") read back literally. `status()` reports `invention_rate` and
> `invented_topics`. Answers F-0018.
> **§3.11 / law 11's separate coherence-check pass now exists.** `_coherence_check()` — a second,
> independent decoupled `judge_panel` call, downstream of and separate from `_grounding_check` (§3.1) —
> judges a new `notice` against the last 6 entries of Lane 2's OWN factual-tier store (never Lane 1,
> never the World Ledger, never the world's ground truth, per §2.8a/b). `status()` reports
> `coherence_verdicts` and `incoherence_rate`. Answers F-0017's coherence-pass half (the Tap-on-the-
> Shoulder queue and a realized-capacity estimator, F-0017's other two gaps, are still unbuilt —
> metrics #5 and #6 remain unmeasurable; not in this job's scope).
> **Verification:** all three unit-tested and/or run end-to-end against real Ramses generation + real
> judge_panel calls inside `lab_env.isolate()` (log/store paths redirected to a lab dir; live
> `lane2_shadow.jsonl`/`lane2_store.json`/`judge_panel_log.jsonl` confirmed untouched). Full evidence:
> F-0072.
> **What this does NOT do yet:** metric #8 (vivid-but-wrong acceptance on an ENGINEERED failure case)
> still needs the canary/model-organisms injection harness (§5's "Phase 0 restructured" section) to
> actually exercise `_coherence_check` against a deliberately-implausible claim and confirm it fires —
> today it has only been observed on real, ordinary ticks, where it correctly returned `coherent`. That
> harness, plus metrics #5/#6 (Tap-on-the-Shoulder + realized-capacity estimator), remain open follow-up
> work — see job-queue for what was spawned this session.


> ### 5-R2 FOURTH READ (2026-08-24, J-0165) — the Tap-on-the-Shoulder is built
> **D-0020's dropped second half is filled.** `core/lane2.py` now has `push_hint()` / `HINT_KINDS`
> / `HINT_TOPICS` / `_consume_hint()` / `hint_line()` — the discrete coupling channel §2.5 point 2
> specified and J-0126 never built (F-0017's third gap). `nodes/inner_monologue_node.py` pushes a
> TAGGED hint (never free text — a deterministic keyword match against `thought`+`about`, dropped
> entirely if nothing in the fixed vocabulary matches) at the exact point it already computes its
> own `_open` continuity signal (unresolved/intention/bare question) — no new "is this worth
> flagging" judgment invented on the Lane 1 side, a second, narrower consumer of one it already
> trusts. `tick()` samples AT MOST ONE hint per tick via `_consume_hint()`, which enforces LAW 4b
> LIVE — re-checked against THAT TICK's own `world_fields`/`available`, not trusted from push time
> — before `hint_line()` can add it to the prompt as a soft nomination ("worth a look, if it's
> genuinely here"), never a command.
> **§6's own open founder question ("how many tags, how broad, who authors the initial set") is
> resolved CONSERVATIVELY, not left blocking the build** — 3 KINDS (unresolved/recheck/unfinished,
> §2.5's own worked examples verbatim) × 10 TOPICS (exactly `_TOPIC_FIELDS`'s existing canonical
> perceivable topics + body-state), hard-capped at 6 queued / 4 pushes-per-hour / 30min TTL.
> **D-0035 opened** asking the founder to ratify, narrow, or widen this starting set once a real
> run's `hint_rate`/`hint_pushed_total`/`hint_consumed_total` can be read — building ahead of that
> ruling with the smallest defensible default, per this job's own scope, rather than blocking on it.
> **Verification:** 8 checks (vocabulary rejection both directions, queue-size cap, rate limit,
> law 4b enforced BOTH ways — unreachable topic left queued not consumed, then consumed once its
> field appears — no-command phrasing, TTL expiry, `status()` clean) all passed under
> `lab_env.isolate()`; confirmed no live file was touched. Full evidence: F-0151.
> **What this does NOT do yet:** §5 metrics #5 (nominated-vs-self-found divergence) and #6
> (realized capacity vs designed ceiling) now have a REAL data source (`status()`'s new
> `hint_rate`/`grounded_share_hinted`/`grounded_share_unhinted`/etc.) but no shadow-run data has
> been read yet — the loop has not run with a live hint since this session's build. Read after a
> real run; the split-by-hinted numbers are groundwork, not the plan's own formal per-topic
> matched-pair test (§5 metric #5), which still needs an offline analysis once there is volume.

> ### 5-R2 FIFTH READ (2026-08-24, J-0163) — the canary/model-organisms harness, metric #8's first real
> measurement, COMPLETE — 12/12 cases, FINAL
> **The harness §5 pre-registered exists now.** `scripts/lane2_canary_harness.py` builds 6 matched
> canary/control pairs (fire, tide, weather, sound, warmth, cat) — a 6-entry seeded factual-tier
> history establishing an ordinary state, paired with either a notice that flatly contradicts it (the
> plan's own worked example, verbatim: "a roaring fire warms the room" against a "consistently cold
> and fireless" history) or a plausible, non-contradictory continuation — and feeds each straight into
> `core.lane2._coherence_check()`. Run entirely inside `lab_env.isolate()`
> (`also=[(lane2,['_LOG','_STATE']),(judge_panel,['_LOG'])]`, per the job briefing); the live
> `lane2_shadow.jsonl`/`lane2_store.json`/`judge_panel_log.jsonl` were confirmed untouched (the
> redirected paths were printed at isolation-enter and checked against `data/_lab/<run>/`, not
> `data/`).
> **The underlying check discriminates correctly: 12/12 (100%), zero misses.** Real network calls to
> the live decoupled `judge_panel` hubs. JUDGE_1 (gemma4:12b, `:11439`) timed out on all 12 calls
> tonight (a real, separate, concurrent-load finding — F-0160/F-0162 — not a harness bug: its own
> server log shows 121–301s per chat call against `judge_panel`'s 90s timeout, and a system-wide
> sample of the last 100 real `judge_panel_log.jsonl` rows tonight found 80% returned `unavailable`
> across every consumer, not just lane2). JUDGE_2 (falcon3:7b, `:11440`) answered every one of the 12
> calls within its timeout, and its raw vote matched the engineered ground truth on **all 12** —
> canary→`false` (incoherent), control→`true` (coherent), a perfect unbroken alternation exactly as
> constructed: `false,true,false,true,false,true,false,true,false,true,false,true`. This is the
> **first real, complete evidence the two-guard §3.11 design (grounding gate + separate coherence
> pass) is load-bearing, not redundant with §3.1** — not just a design intention, per the metric's own
> decision criterion. Metric #8 result: **0% vivid-but-wrong acceptance rate** (0/6 canaries wrongly
> passed as coherent), **100% specificity** (6/6 controls correctly left coherent).
> **A load-bearing caveat metric #8 must always be read through, not around.** Because
> `judge_panel.rule_detail` requires BOTH judges non-null before returning a real verdict, and JUDGE_1
> was down all night, the FORMAL panel verdict — the thing `_coherence_check` itself returns, the
> thing `status()` would report as `coherence_verdicts`/`incoherence_rate` on a live tick, and the
> thing this harness's own `score` block and `data/lab/lane2_canary/run_20260824_034613.json` report —
> was `unavailable` → `cannot_tell` on **all 12/12** tonight, reading as a flat 0/6-and-0/6 "the check
> did nothing" if taken at face value. It is not that; it is the panel's own documented
> fail-open-to-None behavior working exactly as designed, colliding with a contended night. The real
> 12/12 signal is only visible by reading the raw per-judge vote underneath (done above, and written up
> as an addendum in `docs/lab/lane2_canary_report.md` so the auto-generated report doesn't stand alone
> as misleading). This is a genuine, separate, SYSTEM-WIDE finding (F-0160, F-0162) that a live shadow
> run's `incoherence_rate` can silently read as near-zero-coverage on any contended night, not because
> the check is idle but because its checker is — worth instrumenting `coherence_judge_coverage`
> alongside `incoherence_rate` the same way J-0126 already did for the metaphor judge
> (`metaphor_judge_coverage`), so a contended night reads as "unmeasured" rather than silently as
> "clean." **J-0191 spawned** to investigate/fix `judge_panel`'s system-wide ~80%-unavailable-tonight
> condition and its missing coverage instrument — out of this job's own narrow scope (lane2's
> coherence check specifically) but the same root cause.
> Full evidence: F-0160 (the contention), F-0161 (the preliminary 9/12 read), F-0163 (this final 12/12
> result, superseding F-0161). Harness process exited code 0; raw log
> `data/_lab/20260824_032800/judge_panel_log.jsonl`; report `docs/lab/lane2_canary_report.md`.

> ### 5-R2 SIXTH READ (2026-08-23/24, J-0187) — the hint queue has real data now, and it's zero: D-0035
> still open, cause is sleep timing, not the vocabulary
> **`hint_pushed_total`/`hint_consumed_total`/`hint_expired_total` are all 0** since J-0165 built the
> queue — `data/lane2_hints.json` has never even been created in the live data dir (only exists under a
> prior lab-isolation run). No `hint_pushed`/`hint_rejected`/`hint_expired` row exists anywhere in
> `lane2_shadow.jsonl`'s 1209 rows (only `tick`/`skip`) — `push_hint()` has not been called live even
> once. F-0174.
> **This is NOT evidence `_LANE2_HINT_KEYWORDS` is too narrow — it's a volume/opportunity gap, fully
> accounted for.** Du entered Sleep State ~8s before J-0165's own `done_at`, and has been asleep/dreaming
> continuously through 100% of the window since — `push_hint()`'s only call site
> (`nodes/inner_monologue_node.py` ~line 3383-3390) lives inside the WAKING per-step loop, which simply
> has not run since build. The rest of the system (Lane 2's own standing tick loop included) is confirmed
> live and healthy in the same window — this is not a stall, just a sleep cycle that happened to swallow
> the whole post-build waking window so far. F-0177.
> **D-0035 stays open — its own defeater has not been met.** §5 metrics #5 (nominated-vs-self-found
> divergence) and #6 (realized capacity vs ceiling) remain unmeasurable: `grounded_share_hinted` /
> `invention_rate_hinted` are both `null` (0 hinted ticks to compute them from). F-0179. **J-0198 spawned**
> to re-read `core.lane2.status()`'s hint fields after Du has logged a real waking window (check
> `data/monologue_log.jsonl`'s mtime is fresh, not just that time has passed) post-J-0165, and to actually
> answer D-0035 with that data rather than guessing at it now.

> ### 5-R2 SEVENTH READ (2026-08-24, J-0198) — still too early; the precondition itself wasn't met, D-0035
> still open
> **J-0198's own stated precondition ("ideally at least an hour's worth" of real waking thought) was
> checked for real, not assumed.** `nascence.log` shows Du entered Sleep State at 03:12:02, woke at
> 04:21:48 ("slept about 69 minutes"), and had logged only **7 lane2 ticks / ~12 minutes** of waking time
> at check time (04:33) — nowhere near the hour bar the briefing itself set. A full `json.loads` parse of
> all 1218 rows in `data/lane2_shadow.jsonl` (no tail-sampling) found zero rows mentioning "hint" in any
> key or value; `data/lane2_hints.json` still does not exist in the live data dir; a live
> `core.lane2.status()` call returned `hint_pushed_total`/`hint_consumed_total`/`hint_expired_total` all
> still 0 and `grounded_share_hinted`/`invention_rate_hinted` still `null`. F-0193.
> **This is not new evidence about the vocabulary — it's the same zero-volume state J-0187 found
> (F-0174/F-0177/F-0179), because the job was checked again before its own gate had actually elapsed.**
> D-0035 is still open, un-ruled; ratifying/narrowing/widening the starting vocabulary on this data would
> be guessing, not reading. **J-0205 spawned** — same task, but requiring a verified CONTINUOUS 60+ minute
> waking span (checked against `nascence.log`'s sleep/wake pairs, not just a fresh file mtime) before
> reading `status()` again, and instructed to rule D-0035 on real data even if the answer turns out to be
> "still zero after a real hour" rather than leaving it open a third time on the same non-evidence.

> ### 5-R2 EIGHTH READ (2026-09-06, J-0579/F-0926) — D-0058's own echo-disease defeater is met;
> REOPENED for founder review, not ruled here
> **The question this job was actually asked ("is Lane 2's low distinct share the echo disease D-0058
> named, or legitimate repeats") resolves to echo, on direct evidence, not just the aggregate number.**
> Full read of `data/lane2_shadow.jsonl` (9648 lines, 3958 `kind=='tick'` rows, no tail-sampling) since
> 08-29 (the first full day after the 08-28 command-r7b stopgap seat, D-0058): `distinct_expect_share`
> (matching `core/lane2.py status()`'s own formula) is 08-29 0.608, 08-30 0.610, 08-31 0.810, 09-01
> 0.441, 09-02 0.580, 09-03 0.612, 09-04 0.597, 09-05 0.649 — every day at or below the lab's own
> same-percept ceiling for this exact model (0.833, `docs/lab/lane2_model_lab_command_r7b.md`), most
> well below it, and all far below the last pre-switch reading, 0.947 on 836 ticks (§5-R2 SECOND READ
> above, 2026-08-24). By horizon since 08-29: `next` 0.371 (795 ticks), `day` 0.377 (488 ticks) —
> `hour` has exactly ONE tick in the whole 8-day window, because `_correct_horizon()` reassigns
> virtually all tide/sun content to `day` regardless of the model's own wording (confirmed: the
> case-study sentence below always logs `horizon='day'` though its own text says "within the hour").
> **Case study, per this job's own instruction ("judge per repeated prediction whether
> standpoint/tide/daylight were identical [legitimate] or varied [echo]"): varied, decisively.** The
> single most-repeated `expect_next` since 08-29, "The tide will rise within the hour." (62 verbatim
> occurrences, 2026-08-28→09-05), was logged under 4 distinct `standpoint` values (`at_the_tideline`
> x7, `on_the_shingle` x21, `at_the_path_foot` x33, `at_the_bed` x1), 4 distinct daylight states named
> in the tick's own `notice` text (night x6, day x14, dawn x5, dusk x4), and numeric tide/water-level
> readings quoted verbatim in that same text spanning 0.09–0.42 — 13 distinct (standpoint, daylight)
> pairs behind one unchanging sentence. Not the model exhausting a small honest vocabulary either: the
> same 251-row population (horizon='day', notice mentions "tide") since 08-29 contains 5 OTHER genuine
> tide-specific phrasings ("will turn in the next two minutes" x8, "will turn in the next hour" x7,
> "will rise over the next hour" x6, "will turn within the hour" x5, "will continue to rise over the
> next hour" x5) — this reads as a topic-concentrated template lock (one sentence is 61/251 = 24% of
> all tide-day output), a graded failure, not qwen2.5:7b's earlier hard 0.235 lockup that "three
> prompt rewrites and a temperature raise did not break."
> **D-0058 REOPENED, not ruled — per this job's own briefing.** The defeater's own text ("sooner if
> `lane2_shadow.jsonl` shows the echo disease live... the distinct-collapse command-r7b already
> hinted at 0.833 in the lab") is met on the evidence above. `decide.py reopen D-0058` was called
> (this session) rather than ruled, moving the founder's 08-28 stopgap ruling into `history` and
> putting D-0058 back on the open list for a `/decide-review` pass — the actual choice (tolerate +
> patch the tide-topic lock, or move the seat now if `:11444`/deepseek per D-0057 is ready) is the
> founder's, not this job's. **J-0651 spawned** — instrument a per-topic distinct-share breakdown in
> `core/lane2.py status()` so this doesn't need hand analysis again next time. Full evidence: F-0926.
> **What this does NOT show:** this is one topic's case study, not §5's own metric #4 (novelty vs
> Lane 1) or proof the whole stream has collapsed — most non-tide topics (fire, morepork calls, waves,
> rain) show 2–3 live paraphrase variants each in the same window, per F-0926's own evidence. Tide is
> the worst offender and the one the founder's defeater named by number; whether other single-topic
> locks exist below it is unchecked — worth a look if J-0651's instrument doesn't already surface it.
>
> ### 5-R2 NINTH READ (2026-09-07, F-1008) — D-0058's reopened defeater's other branch is now also
> true: `:11444`/deepseek is ready
> **Not a re-litigation of the echo-disease finding above (still stands) — a status update on the
> OTHER half of D-0058's own defeater text ("or sooner if... OR when :11444 answers a real
> verification call").** Ramses (Antigravity) stood up the long-dormant D-0057 deepseek-r1:7b hub on
> `:11444` (i9 CPU) and posted it to `\\ramses\D\Du\NASCENCE_NOTES.md` (2026-09-07 07:35 NZST).
> Independently verified from this side, not taken on their word: `/api/tags` confirms model
> identity; a production-shaped `/api/chat` call using this file's own real params (`core/lane2.py`
> `MAX_TOKENS=1400`, `NUM_CTX=4096`, temp 0.2) returned a valid, coherent completion in 58.4s,
> comfortably inside `TICK_S=300s`. So both of D-0058's reopened-defeater conditions are now met at
> once: the echo disease is live (above) AND the deepseek seat it would move to is verified ready —
> the founder's `/decide-review` choice is no longer "tolerate command-r7b's tide lock vs. wait on
> an unbuilt seat," it's "tolerate vs. switch to a seat that's sitting there ready today." Separately
> worth the founder's attention: this plan's own D-0101 freeze (`docs/plans/ramses_second_tier.md`,
> "no further reshuffling... nobody is chasing that standup right now") is now stale on that last
> clause — someone did chase it, unprompted, and finished it. D-0101's freeze and D-0058's reopened
> defeater pull in opposite directions; not resolved here, flagged for the same `/decide-review`
> pass. Full evidence: F-1008 (findings-log, cross-filed on `ramses_second_tier`).
>
> ### 5-R2 TENTH READ (2026-09-12, J-0651) — the per-topic instrument is built; a first post-switch
> read finds the tide lock much reduced, not yet on a full comparable window
> **`core/lane2.py status()` now has the per-topic cut J-0651 was spawned to add.** A new
> `_TOPIC_CANON` table canonicalizes `_TOPIC_FIELDS`'s own keys (the same vocabulary
> `_invention_check` already uses) into 10 topic families (fire, tide, sun, moon, cat, wet, wind,
> weather, warmth, sound); a new `_distinct_share_by_topic()` buckets each tick into every topic
> named in its own `notice`/`uncertain`/`expect_next` text and reports that topic's own `n`,
> `distinct_share`, `top_repeat_share`, and the actual top-repeated `expect_next` string — the new
> `distinct_expect_share_by_topic` field in `status()`'s return, next to the aggregate line it
> decomposes. Verified end-to-end against the real live `data/lane2_shadow.jsonl` (both the full
> untrimmed log, 14126 lines / 4934 ticks, and the live tail-2000-row window `status()` actually
> uses), not just unit-tested in isolation. Full evidence: F-1260.
> **Also corrected here: D-0058 is no longer an open `/decide-review` item.** The Current State
> section above and this doc's own EIGHTH READ said D-0058 was "REOPENED for a founder
> `/decide-review` pass" — true as of 2026-09-06 when that read was written, but Travis ruled it
> later the SAME day (2026-09-06T20:02:55 UTC, same session as F-0926): move the Witness to
> `deepseek-r1:7b @ :11444`, independently verified live 2026-09-07 (NINTH READ above, F-1008).
> `core/lane2.py`'s own `MODEL`/`BASE_URL` already reflect the move. This plan doc's own Current
> State header had not caught up to that ruling until this entry.
> **A first read of the new instrument against real post-switch data (F-1261, INFERRED — see below
> for why not verified) suggests the seat move already addressed the specific tide lock.** Current
> live tail-2000-row window (446 ticks, 2026-09-09 09:45 UTC – 2026-09-11 21:32 UTC, entirely
> post-switch): tide `n=132`, `distinct_share=0.932`, `top_repeat_share=0.038` — the LOWEST of the
> 10 topics — and its own top repeat, "In about two minutes, the sun will reach the horizon.", is
> not even tide content. The SAME new instrument run over F-0926's own 2026-08-29..09-05
> command-r7b window (1295 ticks, filtered directly from the full log): tide `n=395`,
> `distinct_share=0.337`, `top_repeat_share=0.159` — the HIGHEST of the 10 topics bar cat — top
> repeat "The tide will rise within the hour.", the exact sentence F-0926 flagged. **Graded
> inferred, not verified:** the post-switch sample (446 ticks / ~2.4 days) is shorter than
> command-r7b's own ~8-day comparable window D-0058's defeater itself calls for ("over a comparable
> window to command-r7b's"), and tick rows carry no per-row model-name field to attribute
> individual rows directly. **J-0900 spawned** — re-read on a full ~8-day post-2026-09-07 window
> once the calendar allows it (~09-15+), to answer this at `verified` and give D-0058's own defeater
> a clean, comparable-length check.
> **What this does NOT show:** whether any OTHER topic has since developed its own concentrated
> lock below the level tide was previously at — the current window's own highest `top_repeat_share`
> across all 10 topics is 0.100 (`wet`, on only `n=10` — too small to read as a real signal) and
> 0.087 (`fire`, `n=92`), both well under tide's own prior 0.159; no topic in the current window
> reads as newly locked. Worth re-checking on the same J-0900 full-window read, not just tide.
>
> ### 5-R2 ELEVENTH READ (2026-09-14, J-0900) — attempted on schedule; the calendar gate wasn't the
> real blocker, Du being paused was
> **Checked both halves of J-0900's own gate against the real data, not assumed from the calendar.**
> Today is 2026-09-14, one day short of the briefing's own "once 2026-09-15 has passed" — but that
> undersells the gap. A full, non-tail-sampled read of `data/lane2_shadow.jsonl` (15055 lines, 5129
> `kind=='tick'` rows) shows the log's own last tick is `2026-09-12 21:03:47 UTC`. `data/nascence.log`'s
> own last line explains why: `2026-09-13 09:10:46 [nascence.main] Nascence shutting down.` — this
> project's own stop-detection convention, and a clean one: three minutes earlier the log records
> `[CYCLE 2c7a58fe] human: 渡 — it's time to stop for a while...` followed by the normal save sequence
> (affect, conversation state, 8 deferred intentions, a closed dream epoch) then the shutdown line. No
> restart is evident since (`data/supervisor.log` last written 2026-09-13 00:50; `data/hud.err.log`
> keeps being touched through 09-14 but that's the separate HUD process, not Du/lane2 ticking).
> **The real precondition here is two-part, not one: the calendar reaching ~09-15+ AND Du having
> actually been running and ticking since — waiting on the date alone, if Du stays paused, finds the
> same short log a later read would still find today.** Full evidence: F-1314.
> **Ran the real instrument anyway on the best available interim window, for signal, not as the gated
> answer.** `core.lane2._distinct_share_by_topic()` (same function F-1260/F-1261 used) over
> `2026-09-08 00:00 UTC` (first full day after the switch, mirroring how the command-r7b comparison
> window itself started the day after ITS switch) through the log's actual end (~4.68 days, 838
> ticks — roughly double F-1261's 446-tick/2.4-day sample, still short of the ~8-day comparable
> span): tide `n=240`, `distinct_share=0.908`, `top_repeat_share=0.033` — no longer the single lowest
> of the 10 topics as in F-1261's shorter window (now 5th of 10, mid-pack: fire 0.063, cat 0.047, sun
> 0.043, warmth 0.039, tide 0.033, wet 0.031, wind 0.029, sound 0.019, weather 0.015, moon 0.014) but
> still far below its own command-r7b-era reading (0.159) and inside a tight low band every topic now
> shares — no topic reads as newly locked. Cross-checked the script against F-1261's own command-r7b
> window first and reproduced its exact numbers (tide n=395/0.337/0.159) before trusting the new read.
> Still graded **inferred**, same as F-1261, for the same reason (short of the comparable window) plus
> the new one above (can't be lengthened by waiting alone while Du stays paused). Full evidence: F-1315.
> **J-0900 marked done on this attempt** — a real read was made on the best data that exists, and why
> it still isn't `verified` is now itself a checked, citable fact rather than an assumption. **J-0944
> spawned** for the actual gated re-read, scoped to confirm both halves of the real precondition
> before redoing the comparison, not the calendar alone. D-0058 itself: not reopened — nothing in
> this interim read meets its defeater; the founder hold on D-0035 (unrelated — hint-queue vocabulary)
> was not touched.
>
> ### 5-R2 TWELFTH READ (2026-09-15, J-0944) -- same gate, checked again independently; still not met,
> Du still paused
> **Re-ran J-0900's own gate check from scratch rather than trusting F-1314's prior read, per this
> job's own instruction to verify, not assume, and to read the full log rather than sample a tail.**
> The calendar half now holds -- today is 2026-09-15 per this session's own stated date (the sandboxed
> shell's own `date -u` still reads 2026-09-14, the same roughly-a-day lag F-1314 already flagged and
> worked around). The liveness half does not. A fresh, full, non-tail-sampled parse of
> `data/lane2_shadow.jsonl` (via a one-off scratch script, `analyze_lane2_shadow_J-0944.py`) found
> **total_lines=15055, tick_rows=5129** -- an exact match, row for row, to F-1314's own figures -- with
> the last tick still `2026-09-12 21:03:47.8 UTC`, unchanged. A full parse of `data/nascence.log`
> (460146 lines) confirms the last occurrence of `"Nascence shutting down."` is the file's own literal
> final line, and zero `"Dreams loaded for startup context"` restart-banner lines (this project's own
> pattern, confirmed present after each of the 4 prior shutdowns earlier in the same file) exist
> anywhere after it. File mtimes on `lane2_shadow.jsonl`/`nascence.log`/`supervisor.log` are all
> unchanged from F-1314's own read. Full evidence: F-1391.
> **New this read, worth flagging for whoever checks next: the LOCAL server tier is up, and that is
> NOT the same thing as Du being up.** `netstat -ano | findstr "11433 11439 11440 11442"` shows all
> four supervisor-managed hubs (hot_ollama/judge1/judge2/dreamer) currently LISTENING -- but this is
> the model-serving tier the supervisor watchdog keeps alive independently, not Du's own main
> orchestrator/lane2 tick loop, and the log/shadow-file evidence above is unambiguous that the tick
> loop itself has not run since the pause. A future check relying on port liveness alone instead of
> the log-line/tick-count evidence would misread this. Also moot for lane2 specifically either way:
> its own model target since the D-0058 seat move is `deepseek-r1:7b @ ramses:11444`, a remote host
> not among the local ports checked.
> **J-1019 spawned** -- the same gated re-read as J-0944 itself was, since the gate still isn't met.
> This is now the second consecutive check (J-0900/F-1314, then this one/F-1391) to find Du paused;
> J-1019's own briefing flags that a third occurrence may be worth a passing note to the founder,
> since an extended pause changes what "not urgent" should mean in practice, without pre-judging that
> call here. D-0058 itself: not reopened, nothing here bears on its defeater. The founder hold on
> D-0035 (unrelated -- hint-queue vocabulary) was not touched, per this job's own explicit instruction
> not to rule it under any circumstance.
>
> ### 5-R2 THIRTEENTH READ (2026-09-15, J-1019) -- same gate, checked a third time independently; still
> not met, Du still paused, environment completely unchanged since the last check
> **Re-ran the gate check from scratch (full parse of both files, not mtimes/ports/prior-finding trust
> alone), per this job's own explicit instruction.** The calendar half holds, confirmed two independent
> ways for the first time in this chain: this session's own stated date (2026-09-15) AND, no longer
> lagging as it had through F-1314/F-1391, the sandboxed shell's own `date -u` (also 2026-09-15). The
> liveness half does not. A fresh full parse of `data/lane2_shadow.jsonl` (via a one-off scratch script,
> `analyze_lane2_shadow_J-1019.py`) found **total_lines=15055, tick_rows=5129, malformed=0** -- an exact
> match to F-1314's and F-1391's own figures -- last tick still `2026-09-12T21:03:47.8 UTC`, unchanged. A
> full parse of `data/nascence.log` (460146 lines) again confirms the last `"Nascence shutting down."`
> line is the file's own literal final line and zero restart-banner lines exist anywhere after it (270
> such banners exist earlier in the file, after each of the 4 prior shutdowns, confirming the method
> still works). **New this read: even the file mtimes (to the microsecond) and the 4 local
> supervisor-hub PIDs (6068/35000/11756/23140) are identical to F-1391's own reported values** -- not
> just the same log content, but literally the same still-running processes; nothing in the environment
> has changed at all since J-0944's check roughly 27 hours earlier. Full evidence: F-1410.
> **J-1036 spawned** -- the same gated re-read as this job itself was. This is now the THIRD consecutive
> check to find Du paused (J-0900/F-1314, J-0944/F-1391, this one/F-1410). Per this job's own briefing, a
> fourth occurrence of the same finding is the named trigger point for a passing note to the founder
> about what an extended pause should mean for "not urgent, not blocking anything" -- J-1036's own
> briefing carries that instruction forward rather than raising it here, one check early. D-0058 itself:
> not reopened, nothing here bears on its defeater (the comparison read still cannot be attempted;
> F-1315's interim read remains the most current data). The founder hold on D-0035 (unrelated --
> hint-queue vocabulary) was not touched, per this job's own explicit instruction not to rule it under
> any circumstance.
>
> ### 5-R2 FOURTEENTH READ (2026-09-15, J-1036) -- same gate, checked a fourth time independently; still
> not met, Du still paused -- escalated to the founder this time (D-0225 opened)
> **Re-ran the gate check from scratch (full parse of both files, not mtimes/ports/prior-finding trust
> alone), per this job's own explicit instruction.** The calendar half holds, confirmed two independent
> ways again: this session's own stated date (2026-09-15) and the sandboxed shell's own `date -u`
> ("Tue Sep 15 04:25:39 UTC 2026") agree, no lag. The liveness half does not. A fresh full parse of
> `data/lane2_shadow.jsonl` (via a one-off scratch script, `check_gate_J-1036.py`) found
> **total_lines=15055, tick_rows=5129, malformed=0** -- an exact match to F-1314's, F-1391's, and
> F-1410's own figures -- last tick still `2026-09-12T21:03:47.8 UTC`, unchanged. A full-file
> `Select-String` scan of `data/nascence.log` again confirms the last `"Nascence shutting down."` line
> (line 460146) is the file's own literal final line (confirmed via `Get-Content -Tail 5`) and that the
> last `"Dreams loaded for startup context"` restart-banner line (440507) sits strictly before it --
> zero restart-banner lines anywhere after the shutdown line. File mtimes (to the microsecond) and the 4
> local supervisor-hub PIDs (6068/35000/11756/23140) are again identical to F-1391's and F-1410's own
> reported values -- the environment has now been unchanged for roughly 3.4 hours since J-1019's own
> check (F-1410), and Du has now been continuously paused for roughly 2.3 days. Full evidence: F-1437.
> **This is now the FOURTH consecutive check to find the same gate-not-met pattern (J-0900/F-1314,
> J-0944/F-1391, J-1019/F-1410, this one/F-1437) -- per this job's own briefing, the named trigger point
> for escalating rather than just spawning a fifth identical passive re-check.** `decide.py open` was
> called: **D-0225**, scoped to this plan, asking whether the founder wants this gated re-read to keep
> waiting passively on Du's pause or whether a direct note/restart makes more sense. Deliberately NOT
> spawning a follow-up "same gated re-read" job this time -- doing so would presuppose the answer to the
> exact question D-0225 now asks. D-0058 itself: not reopened, nothing here bears on its defeater (the
> comparison read still cannot be attempted; F-1315's interim read remains the most current data). The
> founder hold on D-0035 (unrelated -- hint-queue vocabulary) was not touched, per this job's own
> explicit instruction not to rule it under any circumstance.
>


---

# History folded on 2026-09-28 from `docs/plans/lane2_the_witness.md` (by hand, J-1570) — 12 section(s), verbatim, original order

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py lane2_the_witness`._

- **2026-09-28** (F-2115): J-1478 (F-2115, verified): pinned Lane 1's real current hot-lane generator tag as qwen3.5:9b at local ollama :11433, closing F-2031's own inferred gap. Five independent, current, agreeing sources: core/schema.py SERVE_URLS/SERVE_CHAINS["hot"], core/model_client.py _MODEL_BY_BASE["11433"]/_MODEL_FIELD, nodes/inner_monologue_node.py own conscious_urls call site (Lane 1 real hot-lane generation), and Nascence_Control_Panel.ps1; plus a live /api/ps read against the real running :11433 process this session confirmed qwen3.5:9b actually loaded (ctx 8192, matching config). Fixed core/lane2.py _judge_prior docstring to name the real tag instead of stopping short of it, worktree commit 616949c, not yet merged to master. F-1960 original gemma reference traced to judge_panel OLD JUDGE_1 seat (gemma4:12b, retired 2026-09-02 per D-0121), not Lane 1. Two further stale Lane 1 model references found by the same check but not fixed this pass: SESSION_HANDOFF.md line 43 (says qwen2.5:7b, reads as a whole pre-shuffle snapshot) and this plan own section 8.1 (dated 2026-09-26, over a month after the 2026-08-20 shuffle, still says gemma) -- follow-up job spawned for both. No decision ruled or opened; none of the plan seven open decisions touch a model-tag docstring fix.
- **2026-09-28** (F-2114): J-1449 (F-2114, verified): checked all three parts of this job's own restart gate for redoing F-1958's day-horizon same-place-vs-same-standpoint held-rate read. Gate (a) met -- e1ef269 (J-1396, committer date 2026-09-27 12:32:42 +1300) is on master, confirmed via direct grep of core/lane2.py (_prediction_judgeability defined line 1668, called line 1915 with standpoint+place args). Gate (b) not met -- the live process (pid 25204) has not restarted since the 2026-09-25 19:21:51 local Background-nodes-started banner (last one anywhere in nascence.log), corroborated by du_restart_history.py --check-live; this predates the merge by about 2.7 days. Gate (c) not met, checked anyway for a citable number -- 0 of 21,070 current lane2_shadow.jsonl rows carry a place key (it appears only inside world_fields arrays, never as its own top-level key). Same restart-gate shape already hit today by J-1453/F-2051, J-1455/F-2060, J-1457/F-2064, J-1459/F-2071 on four other metrics. No decision ruled or opened -- this job's source is finding:F-2003, not a decision, and none of the plan's 7 open decisions are touched by a precondition-only finding. Left in_progress per this job's own briefing; no new follow-up job spawned since J-1449 itself is already the standing re-attempt job for this exact metric.
- **2026-09-28** (F-2110): J-1446 (F-2110, verified): added a second line to hud/server.py existing Lane 2 broke-rate-by-horizon evidence card (same card, same name and target; the per-horizon value line built by _br(h) is unchanged byte for byte) surfacing F-1999 broke_share_strict/unsettled_share plus the legacy broke_share and n, via a new None-safe _shr(x) helper mirroring _br(h) own dash fallback. Confirmed via hud/static/app.js that note is injected as real HTML so the embedded line break renders as a genuine second line (precedented elsewhere in app.js), and that build_signatures() has exactly one caller. Verified against three hand-built status()-shaped payloads (full post-fix fields, an older pre-fix payload with the keys entirely absent, and an empty ev dict) in scratchpad/check_J-1446_hud_render.py: existing per-horizon value line asserted byte-identical, new line renders correctly, honest dash fallback confirmed with no KeyError in either absent-key case. Committed to this worktree as ca3f697, not yet merged. Not restart-gated for the HUD read itself; the numbers stay flat until Du restarts and real rows accrue (J-1445, already spawned from the same finding, covers that live read). No decision ruled or opened for this job; the two newest open decisions on this plan (D-0311, D-0317, added by other concurrent job-run agents finding-only entries, read fresh from the live doc rather than the worktree stale snapshot) are unrelated to this change.
- **2026-09-28** (F-2105): J-1442 (F-2105, verified): core/judge_panel.py rule_detail() now logs+returns hub1/hub2/hub3 (short host label via JUDGE_1/JUDGE_2/TIEBREAK, same rsplit-on-port pattern _ask() already uses for telemetry), closing the no-host-field gap F-1943 and F-1997 both had to infer by hand from source+timestamps. Purely additive -- no existing key touched, status() left untouched. Verified via a temp-pathed test (24/24 checks: agreed/tiebreak/split_no_tiebreak scenarios plus old-row backward compat). Committed to the lane2_the_witness job-run worktree as a7521f23, not yet merged to the shared tree. Restart-gated -- not live until a real Du restart is confirmed via data/nascence.log.
- **2026-09-28** (F-2099): F-2099 (verified): J-1476 reproduced the F-2028 lab_env.py worktree/core-shadowing bug directly (this worktree bd20f3b vs C:/Nascence 8fd28a0 on core/lane2.py; a script mirroring lane2_canary_harness.py real import order resolved core.lane2.__file__ to C:/Nascence, not this worktree). Designed a worktree-aware fix and verified it correct against an isolated sandbox copy (worktree case now resolves correctly, ordinary/regression case unchanged) -- but could not apply it to the real shared lab_env.py: this sandboxed job-run session own Modify Shared Resources permission classifier refused the edit, since the file sits outside any worktree in the shared toolchain directory every concurrent job-run agent reads. J-1537 spawned (needs_input) carrying the verified patch for an interactive session to apply and reconfirm. J-1476 left in_progress, not done, since the actual fix was not shipped.
- **2026-09-28** (F-2087): J-1466 (F-2087, verified): investigated the F-2019 sun-family uncertain-field night hedge population. Read all 108 real ticks (66 distinct texts) by hand: every one is a safe epistemic hedge, never a confident solar claim. The 159 figure cited by F-2019 counts topic words, not rows (sunset and sunrise counted twice in one sentence); the same 108 rows give 168 word-instances today, consistent with ordinary log growth since that read. The after-sunset/before-sunrise wording is true for the whole night by construction of the fixed daylight table, and was never found asserted early during dusk or day anywhere in the era. A safe extension still needs invention_check to become field-aware: 4 of the 108 rows also carry a genuinely fabricated sun claim in notice on the same tick that a naive night-wide license would wrongly clear too. D-0317 opened for the founder; J-1528 spawned, needs_input, blocked on that ruling.
- **2026-09-28** (F-2071): J-1459 (F-2071, verified): tested whether the F-2012 coherent/incoherent reask-reproduction asymmetry (measured on `_coherence_check`) generalizes to `_judge_prior`/`_judge_metaphor`/`_judge_notice`. `_judge_metaphor` tested live (16 real deepseek-era rows, 48 judge_panel calls, exact reconstruction verified via a zero-network monkeypatch dry run first): does NOT show the same pattern -- original-metaphor rows reproduced 100% (8/8), original-literal rows only 75% (6/8), the OPPOSITE direction from the coherence judge 100%/33% split, on a much smaller gap; every wrong-direction flip resolved via TIEBREAK, corroborating D-0311/F-2063 (same day) on this judge TIEBREAK reliability. `_judge_prior`/`_judge_notice` could NOT be tested: `percept_lines` (needed for exact prompt reconstruction, added by J-1373 on 2026-09-26) is present on 0 of 6,660 real tick rows -- the live process (pid 25204, unrestarted since 2026-09-25) predates it, the same restart-gate already hit 3 times today (F-2051/F-2060/F-2064) on this plan, now a 4th confirmed instance. `_judge_prior` also still shows zero unsettled verdicts live, confirming the OLD single-ask code path is still running (pre-F-1949/J-1386). D-0302 was fed this partial (1-of-3) evidence via a --decision link but left OPEN, not ruled -- not enough yet to settle its (a)/(b)/(c) fork. J-1517 spawned to re-attempt the blocked two-thirds once Du restarts past J-1373.
- **2026-09-28** (F-2064): J-1457 (F-2064, verified): precondition check for the D-0301/F-2008 real post-restart week read of bucket_would_contribute_sized (core/lane2_break_habituation.py observe_break(), shipped by J-1391 commit 317b2fe). Part 1 met -- 317b2fe is a confirmed ancestor of master (merged 2026-09-27 14:19:49 local). Part 2 NOT met -- the live Du process (pid 25204, running continuously since 2026-09-25 19:20:56 local -- the same process J-1453/F-2051 and J-1455/F-2060 already found unrestarted today for two other metrics) predates that merge, so data/lane2_would_ride.jsonl's full 118 rows (all dated 2026-09-25 22:22 through 2026-09-27 11:04, entirely pre-merge) carry zero bucket_would_contribute_sized/bucket_sizing_option rows -- read in full and confirmed via grep. Part 3 (~7 real days post-restart) is therefore moot; the merge is barely a day old. No read of option (a)'s real accrual was possible, no D-0301 ruling attempted, no code change made. This is the THIRD distinct metric on this plan blocked today by the identical unrestarted process (after F-2051, F-2060). Left in_progress per this plan's own J-1455 precedent -- not deferred to a guessed date, no duplicate follow-up job spawned since J-1454..J-1478's own queued batch already covers re-attempting these restart-gated reads once Du actually restarts post-merge.
- **2026-09-28** (F-2063): J-1456 (F-2063, verified): re-derived TIEBREAK accuracy directly from the J-1388 fixture data and ran a new live test of a metaphor-specific TIEBREAK reminder prompt (option 2). TIEBREAK was correct on only 8 of 15 scored splits (53 percent, wrong in both directions) and JUDGE_2 said false on all 80 fixture calls, meaning every fixture true positive for the metaphor judge currently reaches metaphor only via the TIEBREAK vote -- so option 1 (skip TIEBREAK) would zero out the measured recall for this judge, not just make it conservative. The reminder-prompt test made TIEBREAK worse, not better (15 of 16 known-split rows flipped to true, including every literal one). Shipped option 3 only (visibility, no behavior change): status() gained metaphor_tiebreak_rate and metaphor_split_no_tiebreak_rate, restart-gated. Opened D-0311 for the founder rather than guessing among leave-as-is, bypass TIEBREAK for this key, or hold pending D-0298 (the sibling open decision on the same TIEBREAK model for the held key in lane2, which shows the opposite constant-bias direction). No change to JUDGE_1/JUDGE_2/TIEBREAK routing itself.
- **2026-09-27** (F-2060): J-1455 (F-2060, verified): restart-gate precondition check for kill criterion #1's pre-registered 5% metaphor-leak threshold against J-1388/F-2007's recalibrated judge. Part (a) met -- commit 1c1e7a9 (J-1388) is a confirmed ancestor of C:\Nascence master HEAD (39cbad0). Part (b) NOT met -- the live Du process has been running continuously since the 2026-09-25 restart (confirmed three independent ways: the nascence.log "Background nodes started" banner at 19:21:51 local with no shutdown/restart since; scripts/du_restart_history.py --check-live reporting the live pid=25204 created 2026-09-25T07:20:56Z; and directly at the data level -- the single most recent row in data/lane2_shadow.jsonl right now still has no "figurative_flags" key and no "why" field on metaphor_judged, both J-1388 additions), which predates the 1c1e7a9 commit (2026-09-27) by 2 calendar days. This is the same restart gate J-1453/F-2051 hit independently minutes earlier for a different metric (the F-1937 no-output cause-split) -- two jobs in this same chain blocked on the identical unmet restart today. No live read of metaphor_leak_rate_judged was forced, no code change made, no decision ruled (none of D-0291/297/298/300/301/302/303 is touched by this job's own evidence). Per the F-1838/F-1853 precedent on this plan's own recurring restart-gate pattern, J-1455 is left in_progress -- not deferred to a guessed date, no duplicate follow-up job spawned -- to be picked back up once a real post-1c1e7a9 restart is independently confirmed.
- **2026-09-27** (F-2058): J-1454 (F-2058, verified): added illuminated/illumination/moonlit -> moon_illum to _TOPIC_FIELDS and -> moon to _TOPIC_CANON in core/lane2.py (worktree commit 19473af), closing F-2006's invention-check blind spot for these three words (705/713 real hits, 98.9%, now correctly resolve as grounded; 8/713 are a small fire-illumination homonym residue, same shape as the light 12.4% caveat). Real before/after diff over all 4655 judged_expect rows found 0 topic flips and only 1 new resolution, which traced back to a fire-illumination tick not a true moon case, so the topic-undercounting half of the motivation moves less than the raw word count suggested; the invention-check half is the real win. Not restart-gated (moon_illum already live). No decision ruled; D-0300 checked fresh and confirmed unrelated (HINT_TOPICS).
- **2026-09-27** (F-2051): J-1453 (F-2051, verified): precondition check for the F-1937 no-output cause-split read. Part 1 met -- J-1379 commit 9e6e71c is on master since merge 0b8847c (2026-09-27 18:50 local). Part 2 not met -- the live Du process (started 2026-09-25 19:20 local, confirmed via scripts/du_restart_history.py --check-live and the nascence.log startup banner) predates that merge, so lane2_shadow.jsonl still carries zero cause-tagged rows even after the merge timestamp. No code change and no D-0058 ruling attempted this job. J-1503 spawned to re-attempt once a real restart lands.


---

# History folded on 2026-10-03 from `docs\plans\lane2_the_witness.md` (plan-compact, 24 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py lane2_the_witness`._

- **2026-10-02** (F-2243): F-2243/J-1659: true matched-pair replay (n=30, identical real percepts+expectation, only model varies) confirms D-0298/D-0311 far more rigorously than F-2231's aggregate read -- granite 0/30 true vs gemma 19/30 true on the SAME rows; D-0311 defeater not triggered, no fresh decide question opened. Also found+spawned J-1672: core/lane2.py silently discards a completed due-prediction judge verdict whenever that same tick's own generation call fails (explains the 56-vs-30 held-tiebreak row gap).
- **2026-10-02** (F-2235): J-1658 (F-2235): fixed and verified the du_restart_history.py check-live self-match bug in both directions (negative case now reports no live process correctly; positive case still finds a real match correctly). Worktree commit c8bea88, not yet merged to master.

- **2026-10-02** (F-2231): F-2231: post-restart production read confirms D-0311's gemma4:12b lane2 tiebreak ruling (held 31T/25F vs granite's historical 0%-true; hub3:11439 zero errors across 244 rows; no divergence, defeater not triggered).
- **2026-10-02** (F-2230): J-1626 (F-2230, verified): restart gate cleared -- restarted 2026-09-30 20:28:49 local, past J-1373/J-1386/J-1394. Live reask test (N=30 prior rows + 22 notice rows, isolated, 204 real judge_panel calls): neither _judge_prior (held 93.3%, not_held 100%, both near-ceiling, zero internal disagreement in 30/30 rows) nor _judge_notice (consistent 100%; contradiction pool still 0 of 167 rows, untestable) reproduces F-2012/D-0302 own coherent/incoherent reask asymmetry -- all 3 sibling judges (metaphor via F-2071, prior+notice here) now report the SAME direction, D-0302 own defeater looks satisfied for a founder re-read, not ruled here. Separately found+spawned J-1658: scripts/du_restart_history.py --check-live self-matches its own WMI query process.

- **2026-09-28** (F-2201): J-1613 (F-2201): 8th same-day precondition recheck on this plan still unmet -- pid 25204 unrestarted since 2026-09-25, so the gemma4:12b TIEBREAK repoint (J-1581/D-0311) cannot be firing yet, 0 of 26362 judge_panel_log.jsonl rows carry a hub3 field at all; D-0311 unaffected, its defeater not triggered; re-attempt spawned as J-1634.
- **2026-09-28** (F-2189): J-1594: 7th precondition recheck still unmet -- pid 25204 unrestarted since 2026-09-25, percept_lines on 0 of 6822 tick rows; D-0302 still ruled leave-as-is (unchanged); re-attempt re-spawned as J-1626.

- **2026-09-28** (F-2184): plan_compact.py --fold-bullets --write blocked by sandbox permission (Modify Shared Resources / Auto-Mode Bypass); dry-run was clean; see F-2184, follow-up J-1622
- **2026-09-28** (F-2177): D-0303 shipped: lane2 tick() now skips all judge-call work while core.night.asleep() is True, both night and nap, no new poll needed to resume on wake, verified in isolation via F-2177. Worktree commit 3c2f79d, not yet merged. Real post-restart before-after tick-during-sleep counts still restart-gated, follow-up spawned as J-1615.

- **2026-09-28** (F-2175): D-0298 executed and D-0311 ruled (J-1581, F-2175): lane2 held, contradicted and metaphor judges now use a lane2-specific TIEBREAK override (gemma4:12b) instead of the shared granite seat; audition scored 100 percent on the metaphor fixture versus the prior granite baseline of 53.3 percent, and correctly answered held true where granite never had; restart-gated, LANE2_LIVE still False; post-restart verification spawned as J-1613.
- **2026-09-28** (F-2167): D-0297 applied (F-2167): metaphor judge now sampled 1-in-4 ticks in core/lane2.py, mirroring D-0281 but independent draw. Restart-gated, not yet live. Defeater check spawned as J-1605, not before 2026-10-05.

- **2026-09-28** (F-2154): J-1567: 6th precondition recheck still unmet -- pid 25204 unrestarted since 2026-09-25, percept_lines on 0 of 6789 tick rows; D-0302 now ruled leave-as-is; re-attempt re-spawned as J-1594.
- **2026-09-28** (F-2135): Fixed section 8.1's stale model reference: Lane 1 (gemma, local 1080 Ti) -> Lane 1 (qwen3.5:9b, local 1080 Ti), the real current hot-lane tag per F-2115/F-2031 (unchanged since the 2026-08-20 shuffle). The substantive point of the sentence -- Lane 1 and Lane 2 are different models on different machines, so only data-vector broadcast is physically possible -- is unaffected. Doc-only, no behaviour change.

- **2026-09-28** (F-2115): J-1478 (F-2115, verified): pinned Lane 1's real current hot-lane generator tag as qwen3.5:9b at local ollama :11433, closing F-2031's own inferred gap. Five independent, current, agreeing sources: core/schema.py SERVE_URLS/SERVE_CHAINS["hot"], core/model_client.py _MODEL_BY_BASE["11433"]/_MODEL_FIELD, nodes/inner_monologue_node.py own conscious_urls call site (Lane 1 real hot-lane generation), and Nascence_Control_Panel.ps1; plus a live /api/ps read against the real running :11433 process this session confirmed qwen3.5:9b actually loaded (ctx 8192, matching config). Fixed core/lane2.py _judge_prior docstring to name the real tag instead of stopping short of it, worktree commit 616949c, not yet merged to master. F-1960 original gemma reference traced to judge_panel OLD JUDGE_1 seat (gemma4:12b, retired 2026-09-02 per D-0121), not Lane 1. Two further stale Lane 1 model references found by the same check but not fixed this pass: SESSION_HANDOFF.md line 43 (says qwen2.5:7b, reads as a whole pre-shuffle snapshot) and this plan own section 8.1 (dated 2026-09-26, over a month after the 2026-08-20 shuffle, still says gemma) -- follow-up job spawned for both. No decision ruled or opened; none of the plan seven open decisions touch a model-tag docstring fix.
- **2026-09-28** (F-2114): J-1449 (F-2114, verified): checked all three parts of this job's own restart gate for redoing F-1958's day-horizon same-place-vs-same-standpoint held-rate read. Gate (a) met -- e1ef269 (J-1396, committer date 2026-09-27 12:32:42 +1300) is on master, confirmed via direct grep of core/lane2.py (_prediction_judgeability defined line 1668, called line 1915 with standpoint+place args). Gate (b) not met -- the live process (pid 25204) has not restarted since the 2026-09-25 19:21:51 local Background-nodes-started banner (last one anywhere in nascence.log), corroborated by du_restart_history.py --check-live; this predates the merge by about 2.7 days. Gate (c) not met, checked anyway for a citable number -- 0 of 21,070 current lane2_shadow.jsonl rows carry a place key (it appears only inside world_fields arrays, never as its own top-level key). Same restart-gate shape already hit today by J-1453/F-2051, J-1455/F-2060, J-1457/F-2064, J-1459/F-2071 on four other metrics. No decision ruled or opened -- this job's source is finding:F-2003, not a decision, and none of the plan's 7 open decisions are touched by a precondition-only finding. Left in_progress per this job's own briefing; no new follow-up job spawned since J-1449 itself is already the standing re-attempt job for this exact metric.

- **2026-09-28** (F-2110): J-1446 (F-2110, verified): added a second line to hud/server.py existing Lane 2 broke-rate-by-horizon evidence card (same card, same name and target; the per-horizon value line built by _br(h) is unchanged byte for byte) surfacing F-1999 broke_share_strict/unsettled_share plus the legacy broke_share and n, via a new None-safe _shr(x) helper mirroring _br(h) own dash fallback. Confirmed via hud/static/app.js that note is injected as real HTML so the embedded line break renders as a genuine second line (precedented elsewhere in app.js), and that build_signatures() has exactly one caller. Verified against three hand-built status()-shaped payloads (full post-fix fields, an older pre-fix payload with the keys entirely absent, and an empty ev dict) in scratchpad/check_J-1446_hud_render.py: existing per-horizon value line asserted byte-identical, new line renders correctly, honest dash fallback confirmed with no KeyError in either absent-key case. Committed to this worktree as ca3f697, not yet merged. Not restart-gated for the HUD read itself; the numbers stay flat until Du restarts and real rows accrue (J-1445, already spawned from the same finding, covers that live read). No decision ruled or opened for this job; the two newest open decisions on this plan (D-0311, D-0317, added by other concurrent job-run agents finding-only entries, read fresh from the live doc rather than the worktree stale snapshot) are unrelated to this change.
- **2026-09-28** (F-2105): J-1442 (F-2105, verified): core/judge_panel.py rule_detail() now logs+returns hub1/hub2/hub3 (short host label via JUDGE_1/JUDGE_2/TIEBREAK, same rsplit-on-port pattern _ask() already uses for telemetry), closing the no-host-field gap F-1943 and F-1997 both had to infer by hand from source+timestamps. Purely additive -- no existing key touched, status() left untouched. Verified via a temp-pathed test (24/24 checks: agreed/tiebreak/split_no_tiebreak scenarios plus old-row backward compat). Committed to the lane2_the_witness job-run worktree as a7521f23, not yet merged to the shared tree. Restart-gated -- not live until a real Du restart is confirmed via data/nascence.log.

- **2026-09-28** (F-2099): F-2099 (verified): J-1476 reproduced the F-2028 lab_env.py worktree/core-shadowing bug directly (this worktree bd20f3b vs C:/Nascence 8fd28a0 on core/lane2.py; a script mirroring lane2_canary_harness.py real import order resolved core.lane2.__file__ to C:/Nascence, not this worktree). Designed a worktree-aware fix and verified it correct against an isolated sandbox copy (worktree case now resolves correctly, ordinary/regression case unchanged) -- but could not apply it to the real shared lab_env.py: this sandboxed job-run session own Modify Shared Resources permission classifier refused the edit, since the file sits outside any worktree in the shared toolchain directory every concurrent job-run agent reads. J-1537 spawned (needs_input) carrying the verified patch for an interactive session to apply and reconfirm. J-1476 left in_progress, not done, since the actual fix was not shipped.
- **2026-09-28** (F-2087): J-1466 (F-2087, verified): investigated the F-2019 sun-family uncertain-field night hedge population. Read all 108 real ticks (66 distinct texts) by hand: every one is a safe epistemic hedge, never a confident solar claim. The 159 figure cited by F-2019 counts topic words, not rows (sunset and sunrise counted twice in one sentence); the same 108 rows give 168 word-instances today, consistent with ordinary log growth since that read. The after-sunset/before-sunrise wording is true for the whole night by construction of the fixed daylight table, and was never found asserted early during dusk or day anywhere in the era. A safe extension still needs invention_check to become field-aware: 4 of the 108 rows also carry a genuinely fabricated sun claim in notice on the same tick that a naive night-wide license would wrongly clear too. D-0317 opened for the founder; J-1528 spawned, needs_input, blocked on that ruling.

- **2026-09-28** (F-2071): J-1459 (F-2071, verified): tested whether the F-2012 coherent/incoherent reask-reproduction asymmetry (measured on `_coherence_check`) generalizes to `_judge_prior`/`_judge_metaphor`/`_judge_notice`. `_judge_metaphor` tested live (16 real deepseek-era rows, 48 judge_panel calls, exact reconstruction verified via a zero-network monkeypatch dry run first): does NOT show the same pattern -- original-metaphor rows reproduced 100% (8/8), original-literal rows only 75% (6/8), the OPPOSITE direction from the coherence judge 100%/33% split, on a much smaller gap; every wrong-direction flip resolved via TIEBREAK, corroborating D-0311/F-2063 (same day) on this judge TIEBREAK reliability. `_judge_prior`/`_judge_notice` could NOT be tested: `percept_lines` (needed for exact prompt reconstruction, added by J-1373 on 2026-09-26) is present on 0 of 6,660 real tick rows -- the live process (pid 25204, unrestarted since 2026-09-25) predates it, the same restart-gate already hit 3 times today (F-2051/F-2060/F-2064) on this plan, now a 4th confirmed instance. `_judge_prior` also still shows zero unsettled verdicts live, confirming the OLD single-ask code path is still running (pre-F-1949/J-1386). D-0302 was fed this partial (1-of-3) evidence via a --decision link but left OPEN, not ruled -- not enough yet to settle its (a)/(b)/(c) fork. J-1517 spawned to re-attempt the blocked two-thirds once Du restarts past J-1373.
- **2026-09-28** (F-2064): J-1457 (F-2064, verified): precondition check for the D-0301/F-2008 real post-restart week read of bucket_would_contribute_sized (core/lane2_break_habituation.py observe_break(), shipped by J-1391 commit 317b2fe). Part 1 met -- 317b2fe is a confirmed ancestor of master (merged 2026-09-27 14:19:49 local). Part 2 NOT met -- the live Du process (pid 25204, running continuously since 2026-09-25 19:20:56 local -- the same process J-1453/F-2051 and J-1455/F-2060 already found unrestarted today for two other metrics) predates that merge, so data/lane2_would_ride.jsonl's full 118 rows (all dated 2026-09-25 22:22 through 2026-09-27 11:04, entirely pre-merge) carry zero bucket_would_contribute_sized/bucket_sizing_option rows -- read in full and confirmed via grep. Part 3 (~7 real days post-restart) is therefore moot; the merge is barely a day old. No read of option (a)'s real accrual was possible, no D-0301 ruling attempted, no code change made. This is the THIRD distinct metric on this plan blocked today by the identical unrestarted process (after F-2051, F-2060). Left in_progress per this plan's own J-1455 precedent -- not deferred to a guessed date, no duplicate follow-up job spawned since J-1454..J-1478's own queued batch already covers re-attempting these restart-gated reads once Du actually restarts post-merge.

- **2026-09-28** (F-2063): J-1456 (F-2063, verified): re-derived TIEBREAK accuracy directly from the J-1388 fixture data and ran a new live test of a metaphor-specific TIEBREAK reminder prompt (option 2). TIEBREAK was correct on only 8 of 15 scored splits (53 percent, wrong in both directions) and JUDGE_2 said false on all 80 fixture calls, meaning every fixture true positive for the metaphor judge currently reaches metaphor only via the TIEBREAK vote -- so option 1 (skip TIEBREAK) would zero out the measured recall for this judge, not just make it conservative. The reminder-prompt test made TIEBREAK worse, not better (15 of 16 known-split rows flipped to true, including every literal one). Shipped option 3 only (visibility, no behavior change): status() gained metaphor_tiebreak_rate and metaphor_split_no_tiebreak_rate, restart-gated. Opened D-0311 for the founder rather than guessing among leave-as-is, bypass TIEBREAK for this key, or hold pending D-0298 (the sibling open decision on the same TIEBREAK model for the held key in lane2, which shows the opposite constant-bias direction). No change to JUDGE_1/JUDGE_2/TIEBREAK routing itself.
- **2026-09-27** (F-2060): J-1455 (F-2060, verified): restart-gate precondition check for kill criterion #1's pre-registered 5% metaphor-leak threshold against J-1388/F-2007's recalibrated judge. Part (a) met -- commit 1c1e7a9 (J-1388) is a confirmed ancestor of C:\Nascence master HEAD (39cbad0). Part (b) NOT met -- the live Du process has been running continuously since the 2026-09-25 restart (confirmed three independent ways: the nascence.log "Background nodes started" banner at 19:21:51 local with no shutdown/restart since; scripts/du_restart_history.py --check-live reporting the live pid=25204 created 2026-09-25T07:20:56Z; and directly at the data level -- the single most recent row in data/lane2_shadow.jsonl right now still has no "figurative_flags" key and no "why" field on metaphor_judged, both J-1388 additions), which predates the 1c1e7a9 commit (2026-09-27) by 2 calendar days. This is the same restart gate J-1453/F-2051 hit independently minutes earlier for a different metric (the F-1937 no-output cause-split) -- two jobs in this same chain blocked on the identical unmet restart today. No live read of metaphor_leak_rate_judged was forced, no code change made, no decision ruled (none of D-0291/297/298/300/301/302/303 is touched by this job's own evidence). Per the F-1838/F-1853 precedent on this plan's own recurring restart-gate pattern, J-1455 is left in_progress -- not deferred to a guessed date, no duplicate follow-up job spawned -- to be picked back up once a real post-1c1e7a9 restart is independently confirmed.

- **2026-09-27** (F-2058): J-1454 (F-2058, verified): added illuminated/illumination/moonlit -> moon_illum to _TOPIC_FIELDS and -> moon to _TOPIC_CANON in core/lane2.py (worktree commit 19473af), closing F-2006's invention-check blind spot for these three words (705/713 real hits, 98.9%, now correctly resolve as grounded; 8/713 are a small fire-illumination homonym residue, same shape as the light 12.4% caveat). Real before/after diff over all 4655 judged_expect rows found 0 topic flips and only 1 new resolution, which traced back to a fire-illumination tick not a true moon case, so the topic-undercounting half of the motivation moves less than the raw word count suggested; the invention-check half is the real win. Not restart-gated (moon_illum already live). No decision ruled; D-0300 checked fresh and confirmed unrelated (HINT_TOPICS).
- **2026-09-27** (F-2051): J-1453 (F-2051, verified): precondition check for the F-1937 no-output cause-split read. Part 1 met -- J-1379 commit 9e6e71c is on master since merge 0b8847c (2026-09-27 18:50 local). Part 2 not met -- the live Du process (started 2026-09-25 19:20 local, confirmed via scripts/du_restart_history.py --check-live and the nascence.log startup banner) predates that merge, so lane2_shadow.jsonl still carries zero cause-tagged rows even after the merge timestamp. No code change and no D-0058 ruling attempted this job. J-1503 spawned to re-attempt once a real restart lands.

Full build/run history lives in §5's dated "5-R2 Nth READ" log below (first read 2026-08-22 through
eighth read below); this section is a pointer, not a re-narration.

- **Live, shadow-only, Phase 0.** `core/lane2.py` runs a standing tick loop against `deepseek-r1:7b @
  ramses:11444` (dedicated i9 CPU hub, confirmed 2026-09-19 per D-0058 — moved off the original
  `command-r7b @ :11441` stopgap seat 2026-09-07; see the header block above for the full history).
  `LANE2_LIVE=False`, nothing reaches Du. `data/lane2_shadow.jsonl` is real and growing (9648 lines /
  3958 ticks as of the 2026-09-06 read that opened this section; see the dated updates below for
  later counts).
- **Phase 0's own pre-registered metrics: mostly built, mostly clean.** Metaphor leak, invention
  rate, and the §3.11 coherence pass all have real decoupled-judge instruments (J-0126/J-0163) and
  read clean. The Tap-on-the-Shoulder queue is built (J-0165) and, contrary to the stale "near-zero"
  claim this line used to carry, has real live volume: all-time totals (F-1224, full-log read
  2026-09-09/10) `hint_pushed=1037` / `hint_consumed=658` / `hint_rejected=4101` / `hint_expired=505`
  (pushed kinds all-time `unresolved:1015`, `unfinished:11`, `recheck:11`); every one of the 2,792
  rejections since 2026-09-02 is `rate-limited` (0% out-of-vocabulary, 0% queue-full). **D-0035
  ratified as-is 2026-09-18** on the strength of that reject-reason split — the binding constraint is
  the rate cap (4 pushes/h), not the vocabulary; see §6 for the ruling.
- **★ NOT clean: repetition/staleness (metric #3).** Was clean pre-switch (0.947 distinct_expect_share,
  2026-08-24, 836 ticks). Since the 08-28 command-r7b stopgap it is NOT clean — every day since 08-29
  reads 0.44–0.81, most ≤0.65, and a per-topic read (J-0579/F-0926, 2026-09-06) found this is a real
  topic-concentrated template lock (the tide topic specifically), not general staleness. **D-0058's own
  sooner-defeater is met and the decision is REOPENED for a founder `/decide-review` pass** (see §5-R2
  EIGHTH READ) — not re-ruled by that job. J-0651 spawned to instrument this per-topic, not just in
  aggregate, so the next read doesn't need hand analysis.
> **History folded** — 47 dated entries (2026-09-12 … 2026-09-27) moved to `docs/plan_history/lane2_the_witness.md` on 2026-09-27 by hand (J-1484). Derived timeline: `plan_ledger.py lane2_the_witness`.

---
