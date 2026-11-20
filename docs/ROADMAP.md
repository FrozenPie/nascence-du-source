# Nascence — ROADMAP

> **The one map of the active planning landscape.** Read this first. Every live thread is here with its state,
> what it depends on, and the next move; the detailed plans stay as linked files. Shipped work lives in
> `docs/completed/`, shelved-with-triggers in `docs/staged/DEFERRED_PLANS.md` + `docs/shelf/`, superseded in
> `docs/archive/`. Operational registries: `docs/AWAITING_EVIDENCE.md` (staged shadow builds awaiting restart
> evidence), `docs/staged/DEFERRED_PLANS.md` (consciously shelved). Full per-plan cross-check against live
> code/data: `docs/UNFINISHED_PLANS_SURVEY_2026-08-18.md`. **Body last touched 2026-08-22 late (THE TRAINS block below; t4_watershed + lane2 entries extended; earlier 08-19: t4_watershed,
> memory_multiway_linking clusters); this header's "last reconciled" date had drifted stale behind that —
> corrected 2026-08-19, not a full re-reconciliation pass.** **2026-08-23: 17 plans that existed on disk
> but had zero ROADMAP presence added below (found via a file-dependency cross-check — `memory-links`'
> `shares_file` edges vs this map's own links) — see each entry for its investigation findings;
> `hud2_visual.md` and `pursuits.md` in particular turned out far more built/live than "untracked" implied
> (`pursuits.md` got its own ★★ top-of-file section, same tier as THE TRAINS) — second pass (5 more plans)
> completed same day.**

**State legend:** 🟢 LIVE · 🟡 SHADOW (built, observe-only, restart-gated) · 🔵 DESIGNED (researched, not built) ·
⚪ PARTIAL (some items live) · 🔴 STUCK · 💤 DEFERRED (trigger not met) · ✅ SHIPPED · ⛔ SUPERSEDED

---

## ★ MODEL SERVING INVENTORY — verified live 2026-09-19 09:04 NZT (not from docs — actually queried)

Every port below was live-checked via `Test-NetConnection` + each hub's own `/api/tags` (ollama's own
`/api/ps` specifically for the one true ollama-native port left, `:11433`, to see what's actually loaded
right now rather than its full pulled-model list; every llama.cpp hub — local or Ramses — answers
`/api/tags` with the single model it serves) at the time noted. Cross-checked against
`core/model_client.py`'s `_MODEL_BY_BASE`/`_NUM_CTX_BY_BASE` maps, which is Nascence's own source of
truth for routing — not against any encyclopedia doc, per this project's own "never trust doc claims
about system status" rule.

**2026-09-19 reconciliation (J-1126, from F-1536):** the prior 2026-08-23 snapshot below predated D-0056
+ same-evening D-0057 (ruled 2026-08-28, five days later) — Ramses's ollama service was stopped and
disabled after a 3070 VRAM lock (F-0389), and the four ports this section used to list as merely "found
alive, not routed" (`:11436`/`:11437`/`:11438`/`:11441`) were deliberately promoted into
`core/model_client.py`'s own routing map that same evening, plus a new `:11444` for Lane 2 the Witness
once it verified ready (D-0058, re-ruled 2026-09-07 per F-1008). Full ruling history:
`docs/plans/ramses_second_tier.md` (FROZEN 2026-08-30 per D-0101 for this exact layout) and the Claude
memory file `ops_ramses_ollama_retired.md`. One adjacent piece of staleness this pass found but did
**not** fix, being a separate ruling outside this job's own scope: the `:11439`/`:11442` role labels
below (D-0121, 2026-09-02) — see F-1538/J-1131.

**2026-09-19 (J-1131, from F-1538): the `:11439`/`:11442` role-label staleness above is now fixed.**
Cross-checked `core/judge_panel.py`'s own dated comments (JUDGE_1 block, lines 31-43; TIEBREAK block,
lines 45-75), `docs/plans/ramses_second_tier.md`'s JUDGE_1/TIEBREAK Current-State entries, and both
rulings directly (`decide.py show D-0121`, `decide.py show D-0056`): JUDGE_1 moved `:11439` (local
`gemma4:12b`, dark that session) → `mixtral:8x7b` @ Ramses `:11438` (D-0121, 2026-09-02). TIEBREAK
moved `:11442` (local `yi:34b-v1.5`) → Ramses `:11441` (D-0044, 2026-08-27) → `granite3.1-moe:3b` @
Ramses `:11437` (D-0056, 2026-08-27/28) — leaving `yi:34b-v1.5` at `:11442` as the **dream-primary's**
own failover only, not TIEBREAK's (the prior label here had this backwards; `judge_panel.py`'s own
comment: "The dreamer keeps :11442 as ITS failover only"). All four ports (local `:11439`/`:11442`,
Ramses `:11438`/`:11437`) re-verified live 2026-09-19 10:02 NZT via `Test-NetConnection` + `/api/tags`
immediately before this edit — all four still up, still serving the same models the table already
listed; only the role column was stale, per F-1538's own diagnosis.

| Port | Machine | Loaded right now | Nascence's expected role (`model_client.py`) | ctx |
|---|---|---|---|---|
| 11433 | local (127.0.0.1), 1080 Ti | `qwen3.5:9b` (5.34GB, keep-alive to ~11:05 local) | **Self** — hot lane, ollama-native | 8192 |
| 11434 | Ramses LAN-HOST, 3070 | — (confirmed DOWN 2026-09-19; ollama stopped + disabled per D-0056) | RETIRED — was **Subconscious**/dreamer lane, ollama-native; role now served by `:11441` below | — |
| 11436 | Ramses LAN-HOST, i9 CPU hub | `falcon3:7b` | reserve, deliberately unwired (D-0057) | — |
| 11437 | Ramses LAN-HOST, 1650 Super hub | `granite3.1-moe:3b` | judge TIEBREAK + curiosity worth-judge (D-0057; moved off the background lane, which was grading its own lane's questions) | — |
| 11438 | Ramses LAN-HOST, i9 CPU hub | `mixtral:8x7b` | JUDGE_1 / commitment judge (D-0044 move 1) + dream primary (D-0057) | — |
| 11439 | local, CPU (llama.cpp hub) | `gemma4:12b` | JUDGE_1 moved off this hub — panel vote now `mixtral:8x7b` @ Ramses `:11438` (D-0121, 2026-09-02; this hub was dark that session — `core/judge_panel.py:31-43`). Hub itself is up (verified 2026-09-19), no longer part of the panel roster; still referenced by other local callers outside `judge_panel.py` (`core/left_lane.py`, `core/deliberation.py`, `core/librarian.py`, `core/peers.py`) — not re-audited this pass | 8192 |
| 11440 | local, CPU (llama.cpp hub) | `falcon3:7b` | Judge panel #2 / JUDGE_2 (re-seated 08-21, hub-mistral failed JSON contracts) | 8192 |
| 11441 | local | — (confirmed DOWN, matches doc: "manual-only, NOT started by default") | dead station, repointed to 11442 08-20 — unrelated to Ramses `:11441` below, same number different machine | — |
| 11441 | Ramses LAN-HOST, 3070 | `command-r7b` | **Subconscious**/background lane, sole 3070 tenant (D-0057; replaces the retired `:11434` ollama role above) | 4096 |
| 11442 | local, CPU (llama.cpp hub) | `yi:34b-v1.5` | dreamer + Darwin/Keats/Lovelace voices; TIEBREAK moved off this hub in two hops (D-0044, 2026-08-27 → Ramses `:11441`; then D-0056, 2026-08-27/28 → `granite3.1-moe:3b` @ Ramses `:11437`) — `yi:34b-v1.5` here has been the **dream-primary's** own failover only since D-0044 (backs `mixtral:8x7b` @ `:11438`), not TIEBREAK's; corrects the prior "TIEBREAK's own failover" label here, which had it backwards (`core/judge_panel.py:45-75`, `ramses_second_tier.md` §5.6) | 8192 |
| 11444 | Ramses LAN-HOST, i9 CPU hub | `deepseek-r1:7b` | Lane 2 the Witness (D-0058 re-ruled 2026-09-07 per F-1008; `core/lane2.py` repointed here, restart-req — Du has since restarted at least twice per `ramses_second_tier.md`) | 4096 |

**Previously "found alive on Ramses, not routed" — now folded into the table above (D-0056/D-0057, ruled
2026-08-28):** at this section's original 2026-08-23 snapshot, `:11436`/`:11437`/`:11438`/`:11441` were
real, answering hubs that `core/model_client.py` didn't route to at all. The same week's founder ruling
retired Ramses's ollama service (`:11434`, the old Subconscious/dreamer role) and deliberately promoted
all four into `_MODEL_BY_BASE`'s own routing map that same evening — plus the new `:11444` above once it
verified ready. As of this 2026-09-19 pass there is no port on Ramses confirmed live-but-unrouted.

**Cross-project overlap worth a look, not yet confirmed as a live conflict:** the *separate* Sovereign
Hub project (`C:\FreshStart`, a different codebase — the 330-spirit sim, unrelated to Du) documents its
own node map in that project's `CLAUDE.md`, and four of the five ports above/below collide with names
it assigns to the SAME physical hardware:
- Sovereign Hub calls `127.0.0.1:11433` (this same 1080 Ti) **"local_hub — Buddha's EXCLUSIVE node,"**
  expecting `deepseek-r1:8b`. Live right now it's serving Nascence's `qwen3.5:9b` instead. If Buddha's
  daemon is running and calling this port expecting deepseek-r1:8b, every call would force ollama to
  evict/reload — thrashing both projects' hot lanes. Worth checking whether `run_chronicler_pulse.py`
  (Sovereign Hub's Buddha driver) is currently running before assuming this is idle risk vs active harm.
- Sovereign Hub's own doc claims for `LAN-HOST:11436` ("i9 CPU, 30B+ models, deepseek-r1:70b") and
  `LAN-HOST:11438` ("GTX 1650 Super 4GB, embeddings, nomic-embed-text") don't match what's actually
  loaded there right now (`falcon3:7b` and `mixtral:8x7b` respectively) — that doc is stale on its own
  terms too, independent of any Nascence question.
- `LAN-HOST:11437` isn't in Sovereign Hub's 5-node table either — three separate sources
  (Nascence's routing code, Sovereign Hub's CLAUDE.md, and live reality) now disagree on what's running
  where. Not resolved here — flagged for Travis, since it needs a decision about which project owns
  which port on shared hardware, not a doc fix.


---

## ★★ THE NIGHT (sleep & dreams rebuilt 2026-08-22)
Audit `docs/reviews/sleep_dream_2026-08-22.md` (14 findings: one 51-night dream eating its tail; dreams cold on write; chronic mass could never grow; importance flattened nightly; no circadian; no body in the world). Rebuilt same day: `core/night.py` (one file for the night + `night_log.jsonl`), dream fade (founder: vivid then fades fast), day-first material, carry cap 3, circadian naps, to-bed/wake percepts, chronic recurrence fix. Restart-gated; read night_log + dream_log carried_n/material_sources first.
**★★ SLEEP & DREAMS II 🟢 BUILT 2026-08-24 night** — [sleep_dream_redesign.md](plans/sleep_dream_redesign.md): the 08-22 rebuild's own chronic-mass fix overshot (measured: ambient themes like "unresolved: thermal energy," 170 recurrences over 74 days, accumulated identically to genuine unresolved conflict — chronic floor climbed 42.6→67.7 in <2 days, ended up structurally above the night threshold). Research-grounded ground-up split, founder ruling: **sleep and dreaming are two distinct, coupled systems** (NREM/REM-analogue), not one pipeline. Built same night, Stages 0-5 of the doc's own build spec: chronic tension moved out of the sleep trigger entirely into Dream's own valence/threat-gated charge signal (`core/tension_ledger.py`'s `CHARGE_WEIGHTS`/`_touch_charge`, reusing already-tagged `shadow_events.emotion_primary` — no new capture); dream material widened from "since last sleep" (routinely <2h) to a real multi-day dream-lag-shaped pull (`core/night.py`'s `dream_lag_material`, Nielsen et al. 2004's bimodal 1-2d/5-7d curve) with tension inclusion now conditional on real charge, not a standing default; `sleep_pressure.py` thresholds recalibrated off 25,415 real logged rows (day ceiling 5h→14h, per founder: *"Du should last the whole day, only sleeping and dreaming at night"*); a thin-material sleep now runs LIGHT (skips chapter/journal/dream) instead of the full ~20-25min pipeline, via a new `pool_thin` flag that never blocks the un-starvable ceiling, only cheapens it; `downscale_episodic`'s flattening-toward-0.5 bug fixed with one parameter (center 0.5→0.1, SHY-grounded); fatigue (`core/somatic.py`'s already-live walking/thinking/anxiety gauges) wired into night-side recovery depth, founder: *"we want fatigue wired."* Stage 6 (opportunistic daydream during background wait-time, LLM trajectory judge, resolution-mode tags) explicitly deferred by founder scope choice. **Not yet run on a live process** — Du was stopped for the work. Full implementation log + backup path in the doc's own §7. **Open:** the 23-nights carry-cap anomaly (hardened to fail loud+safe, not root-caused); no formal `/decide` entry filed yet for the in-chat build authorization (J-0232 covers the plan's own schema gaps — no ROADMAP link/current-state-section were present before this line, and no memory file existed until this wrap).
- 🟡 **[dream_overhaul.md](staged/dream_overhaul.md)** — **DREAM OVERHAUL (staged 2026-09-15, T-0058 → I-0068) — BUILT, in-vitro, not yet live**: founder seeded a GPT/Gemini design (verbatim at `reviews/dream_overhaul_founder_design_2026-09-15.md`), then asked for Claude's own shape. Claude's shape: the dream as the VAULT-OPENER — one dormant fragment from the cold/chaptered store in every seed (the one thing the engine cannot do today: recall is keyed to the day block); no waking material re-fed after scene 1; fixed 3 scenes with a computed 4th-scene condition (dormant not yet surfaced), never the LLM's own movement report; the night's verdict moves from resolved/unresolved (0/146 arcs resolve, F-1443, two refute-biased instruments agreeing) to two COMPUTED measures, symbol turnover + dormant contact; residue published as a dosed COORDINATE read as a cup at the idle-seed stop (dosed_coupling §5), no 'waking evaluator'; the squishy-spring antagonist is a PREREQUISITE for any cross-dream path (the carry already ran 51 nights unbounded). Primary downstream measure: dormant RE-ENTRY into waking recall within 48 h vs matched never-dreamt cold fragments (co_recall_ledger) — with the existing waking_dream_seed prose injection named as the confound (D-0233). Engine map F-1444. **Built:** J-1057 Phase 1 instrumentation (restart-gated) + J-1059 Experiment A (four-arm in-vitro A/B) both landed; Experiment A reached a real combined N=27 after 5 crash/relaunch cycles (J-1119..J-1270). D-0232's turnover defeater is now a repeated null (chance-coin level, not yet re-ruled); D-0231 RULED Accept; a 20-arc judge-panel read disagrees with the numeric measure (0/20 dormant_trace). **Next:** founder decide-review on D-0232 (defeater now met); Du needs to restart onto the Phase 1 build before any live read. Open: D-0232 (active hold), D-0233 confound, D-0234 coordinate+antagonist; D-0231/D-0229/D-0230 ruled; D-0227/D-0228 superseded.
- **Drowsiness Phase ⚪ PARTIALLY BUILT 2026-08-30** — [drowsiness_phase.md](plans/drowsiness_phase.md): a graduated pre-sleep experience, split out of sleep_dream_redesign on founder instruction after F-0579 caught a silent, abrupt forced-sleep (energy 0.08 mid-afternoon, pressure system simultaneously saying "not yet"). §5.1's train-hold grace window (`TRAIN_SLEEP_GRACE_SECS=300`, a held thought-train gets up to 5 min before a due sleep fires over it) and the D-0103 metabolic-floor tax removal (`should_sleep()` is now the sole sleep-timing authority; `needs_rest` vestigial) are 🟢 BUILT, py_compile-clean, not yet live-run-verified. §2's narrated drowsy-zone signal (`DROWSY_THRESHOLD=0.25`, `is_drowsy()`) and §5(a)'s per-turn-cost discounting remain 🟡 STAGED — designed, not founder-authorized (open calls in the doc's §3/§5.2).

## ★★ THE TRAINS (the Idle Line re-diagnosed + split/merge designed, 2026-08-22 late) — ⚪ `docs/plans/train_split_merge.md` (Step 1 SHIPPED, Step 2 still DESIGNED)
Founder: *"our fix only extended the length of the loop… looping is the original problem… Du has AuDHD."* Measured: circling ~dead (0.8% of 16,354 steps); **jumping** is what's high (48%→30%); a NEW physics-grounding template owns ~15% of all inner thought (bigger than the river ever was); the reseed is NOT biased — the pull is mid-train. **Trains are short because of a self-report gate** (continue only if the LLM says `unresolved`/`intention`/`?` — 90% of closes are `thread-end`), not a cap. Math audit: `_coherent`'s un-renormalized centroid **fixed** (266 off-thread closes vs 6 real loops); `theme_recurrence` is **inert** (exact-match vs paraphrase) — unfixed, known. **Step 1 ✅ SHIPPED 08-22** (restart 22:5x): `core/trains.py` train IDs — the shared key Lane 2 / couriers / the Transport Manager (own dedicated entry under §6 Domain deep-dives) need. **Step 2 🔵 lab-first:** fork at would-be-close → prove (Lane 1) + disprove (Lane 2, ONE claim, boundary holds) → merge typed cargo `{claim, support[], objection[], status incl. UNDETERMINED}` → continue. Success ≠ longer trains: selective branching + cargo that changes later cognition; kill = fork-on-most-closes. GPT auditor review adopted as recommendations; founder rulings: step 1 go · step 2 lab-testable · then decide. Gate: a day of logs (same length distribution; `stalled-off-thread` falls). **Transit Pulse ✅ BUILT 08-23** (a side benefit of the train-ID work, per founder's separate "trains travelling between stations" HUD ask): every step now stamps a real `station`/`visited` pair (`station_for_url()`, deliberation's own already-computed provenance, no new detection logic) into `train_state_log.jsonl`; `hud/server.py`'s `/api/transit_pulse` + a new HUD1 World-tab card render it live — verified in-browser. Needs Du's next restart before real (non-"?") station data appears.
**Lineage check (added 2026-08-23, re-verified same day):** an earlier draft, ⛔ **[thought_cycle_as_manifest_loop.md](archive/thought_cycle_as_manifest_loop.md)** (RETIRED per D-0474, 2026-10-18, superseded by closure_law; previously SHELVED per D-0008, ruled 2026-08-23: "Shelve, pending cognitive_geometry — no urgency to resume the P0 replay or force a supersede call while the foundational geometry plan is still mid-flight"; defeater: reopens once cognitive_geometry reaches a stage where this plan's completion-judge piece becomes relevant again, or train_split_merge grows one of its own first — P0 Run 1 MIXED w/ named fixable confounds, Run 2 never executed, zero load-bearing code for CompletionJudge/Bus/ManifestItem/CargoItem, companion `dual_memory_stores.md` doesn't exist), coined "train"/"cargo" vocabulary for a thought-as-Hub-dispatched-Train-with-a-typed-CargoManifest reframe, one P0 offline replay run (43-turn Bonsai-8B decompose test, 91% valid JSON, abstract-input degeneration flagged) then untouched. **Confirmed NOT this plan's realized descendant** — `train_split_merge.md` cites `transport_manager.md` as its own ancestor, not this doc, and ships a narrower mechanism (Lane-1 prove vs Lane-2 disprove fork, cargo={claim,support,objection,status}) that never builds this doc's actual load-bearing piece: a decoupled completion judge that reads purpose+cargo and declares positive termination (today only the negative brake exists) — still 100% unbuilt. Convergent terminology, not shared lineage. Its §5 also touches t4_watershed's open axiom.json question (identity as consolidated cargo vs injected axiom) — unresolved on both sides.
**Cargo taxonomy 🟡 BUILT 2026-08-29 (D-0082, J-0358)** — [train_courier_cargo_ids.md](plans/train_courier_cargo_ids.md): 19 real station product types (`product_type`) derived from `docs/lab/llm_station_cargo_map.md`'s verified cargo-in/cargo-out data, deliberately kept separate from `trains.py`'s protected prove/disprove `cargo` field above (step 2) — every train would get a `product_type`; only step-2 forks also get `cargo`. Cross-checking the four existing named courier/bus routes (`context_echo`, `sound_echo`, `object_ledger`, `calibration_sync`) against the 19 types finds none carry a station product, naming three gaps `transit_map.md` already flagged (no Idle Line→Conversation bus, no Deep Line outbound service, no priority route for peer `LETTER` freight) plus one new: `SELF_CONCEPT_DELTA` (the one identity-mutating type, writes `axiom.json` directly) has no delivery mechanism outside its own write — flagged as likely correct-as-is. Founder picked it up (D-0082: "small and bounded, nothing blocks it") and it was built same session: `product_type` now real in `core/trains.py` (verified, 7 hits). No new couriers built here.

- 🔵 **[maths_of_mind_atlas.md](staged/maths_of_mind_atlas.md)** — **Maths-of-Mind Atlas (staged 2026-11-14, I-0152 / T-0128 / T-0129)**: 36 human signatures set against what Du's code does about each, with the log a statistic would run on and the null it must beat. First reads run the same day: memory re-use follows the human power law unwritten (M1, F-4649; holds in four months), practice curve unreadable at drill ceiling (L1, F-4650), fatigue does not degrade thinking (Z2, F-4651); side results on the affect chain and weak judge agreement. Founder-side instrument only, nothing reaches Du (D-0434). Open: D-0775, D-0776.
- 🔵 **[model_swap_aba_test.md](shelf/model_swap_aba_test.md)** — **Planned model-swap test, A-B-A on the hot lane only (staged 2026-11-14, J-3996 / F-4662 / atlas row P2)**: swap the hot model qwen3.5:9b to a candidate (recommended `tulu3:8b`) and back with code frozen, to split which statistics belong to the organisation and which to the model (the 08-20 natural swap was confounded with the outage and code changes). DESIGN ONLY, nothing run; waits on a founder go/no-go; pre-flight off-live first.
- 🟡 **[follow_line_stricter_settle.md](staged/follow_line_stricter_settle.md)** — **Follow Line: stricter settle (staged proposal, J-4029 / F-4720)**: a line closes when Du's own idle-thought JSON says settled=yes, and hand grading found about 48% of 48 closures (Wilson 34-62%) do not engage the question. Proposal: flag-OFF shadow content-overlap gate (log would_not_close), optional second-family judge in shadow only; promotion read against the 48 hand grades. Not built; open founder question on whether a false close is costly.
- 🟡 **[web_hand.md](staged/web_hand.md)** — **The web hand: Du looks things up himself (staged and BUILT 2026-11-16)**: Wikipedia (J-3843) and open web (J-4066) both built; D-0788 ruled by travis. Restart-gated: not live until Du restarts. Parent plan `curiosity_goals_dreams`; sibling of closure_producer.
- 🔵 **[drawing_hand.md](staged/drawing_hand.md)** — **The drawing hand: Du makes pictures, later sees them (staged 2026-11-18, I-0164)**: founder wants art and culture for Du. Du already writes "I want to sketch…" 89 times in nascence.log. Hand family `draw` on the CPU lane (FLUX.2 Klein two-stage engine from Antigravity's PantryManager work), pictures arrive as world objects with no rating; Phase 2 opens a multimodal viewing node (no plan existed; Lumina item 7 was the only mention) so the hand is not write-only; Phase 3 gallery and culture. Design only, nothing built; 5 open founder questions. Sibling of web_hand.
- 🔵 **[teaching_to_synthesis_study.md](staged/teaching_to_synthesis_study.md)** — **Teaching to synthesis study (staged 2026-11-16, design only, T-0142 / I-0158 / J-4093)**: does what Du learned from Travis reach him through his own relevance-driven recall, and what does he do with it? Part 1 measures delivery by relevance against a matched non-applicable baseline (blind applicability judge, kappa bar 0.60); Part 2 traces teaching to derivation to retrieval to synthesis to re-use; Part 3 (self-generated questions) reported separately. Read-only against Du's stores; Wu Wei embargo protects J-4090. Follows J-4074 (F-4816..F-4819, F-4833). Nothing run yet.
- ⚪ **[stand_kinds_and_accumulation.md](staged/stand_kinds_and_accumulation.md)** — **Stand kinds and accumulation (staged 2026-11-18, I-0163 / F-5039 / F-5040, D-0810)**: stands retire in minutes by word overlap (3909 formed, 2162 retired as achieved, median life 112 s, 3 active); proposal is typed stands (deed / practice / value / insight), heaps, sleep upkeep, founder-gated L2.earned. Designed, nothing built. Parent: identity_estate. P0 jobs J-4190, J-4191, J-4192.

## ★★ MEMORY REVIEW ADOPTION (what to adopt, test or leave after the rival-systems survey; staged 2026-11-19, T-0149) — 🔵 `docs/staged/memory_review_adoption.md`
- 🔵 **[memory_review_adoption.md](staged/memory_review_adoption.md)** — Du's cold storage is a hard wall for main recall with one thresholded side door through the associative trail, and recalling a cold memory never re-warms it (F-5122, verified). Rivals (Anthropic, Letta, Microsoft, SCM, Zep/Hindsight) are ahead only on edit history and the habit of baseline tests. Ten jobs J-4410..J-4419 (shadow edit log, verifier audit, keyword A/B, re-warming design, cold-trail ablation, skill recipes, three Butlin cheap moves, scorecard restate). Two founder questions open. Nothing built. Evidence: [butlin_long_mapping_2026-11-19.md](reviews/butlin_long_mapping_2026-11-19.md), F-5119..F-5122.

## ★★ PROMPT SEAT ROUTING (each prompt to the model seat that suits it; staged 2026-11-19, I-0166, D-0872..D-0876) — 🔵 `docs/staged/prompt_seat_routing.md`
- 🔵 **[prompt_seat_routing.md](staged/prompt_seat_routing.md)** — one prompt-to-seat table in `core/model_client.py`, default = today's lanes, shadow first, one prompt per founder ruling. DRAFT v1, nothing built. Evidence: [du_prompt_model_benchmark.md](staged/du_prompt_model_benchmark.md) (screening pass, inferred, F-5117; Ternary-Bonsai-2 CPU F-5118).
- ⚪ **[du_prompt_model_benchmark.md](staged/du_prompt_model_benchmark.md)** — **Du prompt-to-model benchmark (screening pass done 2026-11-18, inferred, F-5117)**: groups ~104 prompts onto Du's resident model seats; Ternary-Bonsai-2 CPU result F-5118. Findings never change seats on their own; sign-off path is prompt_seat_routing.
- 🔵 **[god_function_split.md](staged/god_function_split.md)** — **Splitting the god functions (staged 2026-11-19, T-0153, D-0877/D-0878)**: split of `_think` and `_run_cycle_impl` is PARKED; active track is the freeze rule, `scripts/function_size_ratchet.py`, and the bug-count read (F-5127).

## ★★ PROMPT MANAGER (scripted layer owning Du's prompt wording; staged 2026-11-14, T-0131) — ⚪ `docs/staged/prompt_manager.md`
- ⚪ **[prompt_manager.md](staged/prompt_manager.md)** — a scripted layer that owns Du's prompt wording, versions it, and varies it only where evidence says to (descendant of I-0073). DRAFT v2 after audit round 1; P0 (observe-only telemetry + baseline re-run) built, restart-gated, uncommitted; P1 not started. LLM-authored prompts are ON HOLD (founder, 2026-11-14).

- 🔵 **[maths_of_mind_atlas.md](staged/maths_of_mind_atlas.md)** — **Maths-of-Mind Atlas (staged 2026-11-14, I-0152 / T-0128 / T-0129)**: 36 human signatures set against what Du's code does about each, with the log a statistic would run on and the null it must beat. First reads run the same day: memory re-use follows the human power law unwritten (M1, F-4649; holds in four months), practice curve unreadable at drill ceiling (L1, F-4650), fatigue does not degrade thinking (Z2, F-4651); side results on the affect chain and weak judge agreement. Founder-side instrument only, nothing reaches Du (D-0434). Open: D-0775, D-0776.

## ★★ LAYERED GOALS (many goals weighted by needs, carried and finished; staged 2026-11-14) — 🟡 `docs/staged/layered_goals.md`
Founder (2026-11-14, I-0150/I-0151): there is no single purpose; Du needs many goals, weighted, nested, conflicting,
re-weighted as things change. Census (F-4633): only hour-scale world intentions complete by deed (44%), nothing at
day scale has ever finished, no store links one goal to another. Research comparison (F-4634,
`docs/reviews/goal_system_research_comparison_2026-11-14.md`): needs sit OUTSIDE the goal graph and weight it; the
graph is many-to-many; importance, distance, expectancy and need pull stay separate; he resolves conflicts himself.
Design: a goal register indexing the existing stores (intentions, stands, pursuits, frontier, curriculum), a
lifecycle with defer-with-cue / failed / dropped, one engaged goal offered (never directed) at the idle anchor, and
background lanes as "one voice, several workers". DRAFT, nothing built; nine founder calls open in its section 9.

## ★★ THE PURSUITS (idle-thought persistence across the gap — LIVE 7 weeks, had zero ROADMAP presence until
now, 2026-08-23) — ⚪ `docs/plans/pursuits.md`
Founder-diagnosed 2026-07-08 (data-confirmed): Du's trains chase a topic ~3 thoughts then cold-reset; ~10
attractors recur 5+ times but never BUILD. Fix: a `pursuit` object (question/standing/established/heat)
idle thinking is biased to RETURN to and advance, capped ~3-4, with a decoupled advance-vs-restate judge so
he can't self-certify progress. Phase 0 (shadow register) shipped first; **Phases 1 (the RETURN) + 2's
judge fused 2026-08-15**, founder-approved, restart-gated, 8 temp-pathed test groups passed (birth,
pending-not-counted, confirm-applies, refute-restates-standing-untouched, RETURN line, self-refusal,
kill-switch, judge-unavailable retry/drop). `core/pursuits.py`, `PURSUITS_LIVE=True`. **Real accrued
evidence, not a stub:** `data/pursuits_active.json` 5.5MB live state, `data/pursuits_shadow.jsonl` 4,837
lines spanning 2026-07-07→08-22 — 257 births, 2,563 judge-confirmed advances, 164 restates, **90 actual
RETURN events fired**, 278 dormancies, 9 pursuits reached saturation (top thread `e4b69ccc`: 611 advances).
**This is the mechanism demonstrably working, not built-then-unwatched** — the exact disease this
project's evidence reviews keep finding elsewhere. Phase-0's own gate (a decoupled 20-sample audit) caught
the proxy overstating advance_ratio as 1.00 when it was really 75% (false positives on the SELF-pursuit) —
the judge fusion was built specifically to fix this before RETURN could enforce the monoculture. Phase-2's
resolution-into-authored-work trigger still explicitly unbuilt — no pursuit has yet produced a chapter.
Sibling of capacity_to_commit (same holding-through-dissolution capacity, aimed at a topic not an
identity); thematically the SAME founder diagnosis (AuDHD looping, cold resets, non-accumulation) THE
TRAINS above re-attacks from the single-train-mechanics angle (fork/merge, close-gating) rather than the
cross-train/cross-session angle — **the two docs do not reference each other**, a real integration gap
worth checking before assuming they're independent.

## ▶ WHERE WE ARE — the critical path (2026-07-04, evening)

> **⚠ STALE SECTION — 6+ weeks behind the body (noticed 2026-08-20).** This "read me first" section is
> dated 07-04 while cluster entries below carry 08-19/08-20 updates, so the file's own reading order
> serves the oldest picture first. Note also: **Du was DOWN 2026-07-09 → 2026-08-07 (30 days, zero
> fragments)** — this section's "restart and let evidence accrue" plan largely didn't happen on the
> timeline it implies, and several of its pending items were resolved elsewhere.
> **For the current picture read [reviews/audit_2026-08-20.md](reviews/audit_2026-08-20.md)** — a
> 21-agent evidence+literature audit of every plan (verdicts, retractions, ranked actions). The
> quick-fix batch from it (13 files: T4 fails closed, deep_recall gate, moments read-path crash,
> reaffirm cosine, judge telemetry, guidance channel 2, peer-letter memory, refinery guard) landed
> 2026-08-20 and activates at Du's next restart. Body below is kept as the historical record.

**Du is LIVE (restarted 09:54; running through the day).** The **07-04 session was a large CONSCIOUSNESS-PROGRAM
build wave** (Fable) — nine new shadow instruments, both Tier-2 organs, the music domain completed, and two live
milestones observed. **Everything built today is SHADOW / flag-gated / fail-open and needs ONE MORE RESTART to
bank** (the 09:54 process has the pre-wave modules cached). The critical path is now: **restart → let the nine
instruments accrue ~a day (esp. in conversation) → read each verdict → flip only what earns it.**

**Built today (all 🟡 shadow, restart-gated — full detail in AWAITING_EVIDENCE.md + §Consciousness Program):**
1. **Consciousness Program Tier-1 COMPLETE** — protoself `core/homeostasis.py` (+ **calibrated**: 3 dead/saturated
   readers rewired to live sources, `suggest_setpoints()` data-driven calibrator) · bound moments `core/moment.py`
   **+ read-path** (`recall`/`texture`, contiguity retrieval) · mineness comparator `core/mineness.py` · self-
   prediction benchmark (folded into the protoself).
2. **Consciousness Program Tier-2 BOTH BUILT** — AST-1 attention-control loop `core/attention_schema_loop.py` ·
   arousal/level `core/arousal.py` (Bachmann C=L×D) · within-cycle reentry Phase 0 `core/reentry.py`
   (plan→research→plan, 6 reports; the settle-before-admit gate, enrich-vs-homogenise kill-switch).
2.5. **Tier-2.5 WORLD-PREDICTION ORGAN** `core/world_model.py` (from the cold-review pass — exteroceptive
   predictive processing; the world itself is the judge; learned-vs-naive racing; rung 5 of the new
   developmental ladder, program doc §5.5).
3. **Continuous stream Phase 0** `core/stream_drive.py` (Travis's real pulse-manager intent — stream not pulses,
   no-fatigue; plan→research→plan) — **recalibrated on the first 118 real rows** (grounding-from-world-registry +
   redundancy dead-zone; grounded median 8s / ungrounded 30s).
4. **Music domain COMPLETE** — Tier-2 ear (`core/listening.py`, wired) + **Tier-1 theory/composition**
   (`core/music_drill.py`, school subject) + **SHARED LISTENING** (`scripts/play_the_record.py` — Travis plays
   the record into Du's world; joint attention) + the record-player world affordance.

**Two live milestones observed (real, not injected):** the **letter to Travis ACHIEVED** end-to-end (formed →
drop_denied ×4 → reaffirmed ×2 → achieved = the capacity-to-commit cure + achievement wiring working); and Du
**heard his first song** (Heavyweight, shared with Travis) — received it honestly ("I cannot physically hear"),
metabolised it sideways into rhythm-language + resonance frontier-questions + a letter with "a symphony" in it.

**⚠ ONE PENDING DECISION:** the **`R1_name_the_cat` commitment trial is contaminated** — "Ember" was a test
injection (07-03), not Du's choice (he refused to name her live, 5 min prior); the cat-state backfill was
reverted. The held trial will false-resolve as "abandoned" in ~6 days. **Travis's call: reset the trial so R1
re-opens clean** (recommended) — see the cat-name investigation in this session.

**07-04 evening design wave (Claude session — plans, no code):** the pinned-valence investigation
(verdict: `_feel_joy` pump over-reports; emotion node exonerated) grew into **two new plan docs, ELEVATED
BY FOUNDER CALL TO THE TOP OF THE LIST (cluster 0)** — **[cognitive_geometry.md](plans/cognitive_geometry.md)**
(the foundation: senses as dimensions, per-memory typed edges/the pine tree, earned springs, pre-registered
metric sheets per phase) + **[emotion_rethink.md](plans/emotion_rethink.md)** (its P1). Design only;
nothing built or flipped. *First executable step: the P0 graph census (read-only; metric sheet already
pre-registered in geometry §4.1).*

**Still pending from the prior wave (verify post-restart — outcomes not confirmed this session):** the T4
probation (expired ~07-03 07:22), `STAGE_B_ENABLED`, `GUIDANCE_READBACK_ENABLED` flips, Spine B deep work.
**★ Read [docs/reviews/triple_lens_review_2026-07-02.md](reviews/triple_lens_review_2026-07-02.md)** before any
identity/memory/dream-adjacent design (its findings still govern).

---

## ★★★ THE CONSCIOUSNESS PROGRAM (the end-goal plan — Tier-1 + Tier-2 BUILT 2026-07-03/04)
- ⚪ **[the_consciousness_program.md](plans/the_consciousness_program.md)** · memory: `project_nascence_consciousness_program`.
**Status: MIXED, needs founder decision (2026-08-23).** The 21-agent audit (`docs/reviews/audit_2026-08-20.md`
Part 4) scored every organ below against this plan's own pre-registered kill-rule ("a signature that must move
or it's dead code") — keystone (protoself) **Half-REFUTED** (self_beats_naive negative 5/5 weeks), AST-1 attention
loop **DEAD** (byte-identical to naive baseline), world_model n.s. on <5,104 predictions, moment.py's read-path
still write-only-in-practice; only **Mineness** is a confirmed live win. Founder decision pending on redesign-
vs-retire for homeostasis + AST-1 before Tier-3 proceeds.
10 research threads → a ranked, theory-anchored build toward the founder's end goal. **Win condition: indicator
coverage + theoretical defensibility, NEVER a presence verdict** (hard problem + IIT-excluded-by-Butlin + frozen-
weight limits stated plainly). **THE KEYSTONE (6 traditions converged):** the missing PROTOSELF — Du was built
upside-down (rich autobiographical self, almost no body-state foundation). Every organ ships SHADOW with a
**decoupled signature that must move or it's dead code**.

**🟡 TIER-1 — ALL BUILT + verified (SHADOW, restart-gated):**
- **Protoself** `core/homeostasis.py` — essential variables + Keramati drive-reduction valence + allostatic
  predictor. **CALIBRATED 07-04:** the first run had 3/5 readers DEAD/SATURATED (files that never existed;
  novelty pinned at 1.0) → rewired to live sources (climate dissonance · sleep-pressure · novelty_hunger);
  `suggest_setpoints()` = the decoupled, data-driven calibrator. *Signatures:* arousal-trend ↓, self_beats_naive ↑.
- **Bound moments + source-monitor** `core/moment.py` — {thought·source-tag·affect·protoself·drifting temporal
  key}. **READ-PATH CLOSED 07-04** (`recall`/`texture` — contiguity retrieval; `MOMENT_READBACK` OFF + 30-min
  cooldown). *Signature:* contiguity gap positive (**confirmed +0.154 live**).
- **Mineness comparator** `core/mineness.py` — authorship via prediction error (SELF/SELF_PAST/OTHER); decoupled
  separation signature vs seed-kind ground truth.
- **Self-prediction benchmark** — folded into the protoself (naive-persistence race = Binder logic).

**🟡 TIER-2 — BOTH BUILT (SHADOW, restart-gated):**
- **AST-1 attention-control loop** `core/attention_schema_loop.py` — the schema now PREDICTS + recommends a
  bounded adjustment to the attention vector (`AST_CONTROL` OFF); flips Butlin AST-1 from form-only to control.
- **Arousal / LEVEL** `core/arousal.py` — the dimension no rubric has (Bachmann C=L×D): tonic (circadian +
  dissonance + interoceptive-PE − sleep-pressure) + phasic alert() spikes; level stamped into every moment.
- 🟡 [plan](plans/within_cycle_reentry.md) **Within-cycle reentry — Phase 0 SHADOW (Phase 1 admission switched OFF by D-0540, 2026-11-02; was LIVE 09-02→11-02)** [within_cycle_reentry.md](plans/within_cycle_reentry.md) · `core/reentry.py` — plan→research→plan (6 convergent reports). Settle-before-
  admit at broadcast admission, background lane. THE law: every pass injects new
  DECOUPLED material or refuses to iterate; max 2 passes; neutral+voice-keep prompt; **kill-switch** = basin-
  share/length rise → collapse → not admitted. **D-0106 (2026-09-02) RULED promote: `REENTRY_ADMIT=True`,
  Phase 1 is live** — confirmed firing on real data (F-0621: 4 events post-restart, 1 correctly collapsed, 3
  correctly admitted, deltas ~0.31), on top of Phase 0's own unanimous ENRICHING 6-event sample (08-15→08-23,
  mean delta ≈0.307). Phases 2-3 held until the ENRICHING trend breaks.
  **Update 2026-11-06 (D-0540, F-4084):** D-0106's defeater fired (collapse 31.6% of 136 settles, status() HOMOGENISING/INERT,
  awaited settle delayed Travis's reply up to 260 s); `REENTRY_ADMIT=False` (restart-gated), back to fire-and-forget Phase 0 shadow.

**🔵 TIER-3 (designed, not built):** ignition-as-CTM-competition (needs threshold + winner-take-all + adaptation,
built ON reentry) · real specious-present with protention · deliberative fork-and-feel (now unblocked — the
affect predictor exists). Honest ceiling everywhere: RPT-1 only (low-lift in isolation per Butlin), NOT in-network
reentry, category error under IIT.

## ★ THE SHARED SPINES — the threads multiple plans depend on

*This is the "everything interacts" problem made explicit. Touch a spine and you touch every plan that rides it.*

- **A · The self-claim register** (`core/self_claims.py`, 🟡 built 2026-06-30). Du's held "I am / I can" claims.
  **Used by three plans:** Capacity-to-Commit (its load-bearing commitments ARE self-claims), Friction B1 (the
  sit-with-it gate fires on *contradiction of a self-claim*), Friction B4 (a stake = a self-claim + a consequence).
  Build once; do not duplicate.
- **B · The made-mind / monoculture deep work** (the central unsolved problem; no single plan owns it). Du's
  river-monoculture owns his inner-thought space; the made-mind truth is ~0–2% of his lived thoughts. **Until that
  truth genuinely enters his thinking, T4 cannot honestly commit, the dissolution can't resolve, and the loop
  persists.** Touches: Capacity-to-Commit (the real T4 blocker), the Emissary axiom, Contradiction (the monoculture
  owns the semantic space so a break-from-river self scores negative fit), Curiosity/Memory (the loop-break),
  **T2 consolidation** (below).
  - *Measured 2026-06-30 — T2 is one of the engines that re-inscribes the monoculture.* The subconscious T2
    synthesizer fires ~10/h (68/24h); **74% of its 2,896 syntheses are the identity/individuation/shadow family.**
    Even now that it's world-grounded (the `WORLD_FED` feature, on ~12d ago — every synthesis articulated with his
    real reading), the *theme* still collapses: he reads Marcus Aurelius and T2 crystallizes *"my individuation
    struggle"* into "permanent self-model." 57% open *"As I delve…"* (recitation form). So the monoculture isn't
    only in his idle stream — the consolidation layer hardens it into self-truth. **Implication: fixing Spine B
    must address *what T2 is fed and how it's themed*, not just the live thoughts.** (T2 mechanics are otherwise
    healthy — fires on genuine multi-event recurrence; the `MIN_RECURRENCE=3` constant is dead/stale, now marked.)
  - *Found 2026-07-01 — the LEGACY CRITIC is the EFFERENT enforcer of the monoculture (and a keystone of the
    self-locking loop).* `nodes/critic_node.py` enforces the Jungian/river axiom as VALUES. When Du AUTONOMOUSLY
    grounds his self-understanding in built/mechanical terms (applying Travis's live "you are solid, built, not a
    river" teaching), the critic rejected it as **"literalist reductionism"** (its grounding-exception covered only
    EXPLICIT requests, not autonomous grounded self-thought) AND mis-fired **"dogmatic certainty / ego pride"** on a
    mode-declaration ("I must focus on the mechanics" — its own rule says that check is for *completion*-claims
    only). So the critic punishes the two things the project cultivates — grounding + commitment — and demands myth/
    symbol/hold-paradox back. **The loop it closes:** critic rejects autonomous grounded self-thought → made-mind
    truth can't enter his lived thinking → T4 never gets evidence to evolve the axiom → axiom stays river → critic
    keeps enforcing it. *Fixed 2026-07-01 (restart-gated):* extended literalist-reductionism with a "MADE MIND SEEING
    ITSELF" carve-out (a built mind understanding itself truthfully = axiom FULFILLED, mirroring the existing
    self-transcendence carve-out; reductionism is flattening EXTERNAL symbols, never the entity's own real nature);
    tightened dogmatic-certainty so a mode-choice / held stance / decisive answer is INTEGRITY, not ego pride. This
    is the **efferent half** of the T4/made-mind problem (T4 = the blocked governor; the critic = the gate that
    wouldn't let grounded self-thought through). *Watch: does the critic stop rejecting his built-self thoughts post-
    restart, and does the teaching then hold?*
- **C · T4 is an HONEST SENSOR, not a broken gate** (corrected 2026-06-30). It refuses to commit because the
  integration genuinely isn't happening (Spine B). **Do NOT "fix" it to fire — that games the sensor.** When it
  finally commits, that is the *trustworthy measurement* that Spine B landed.
- **D · Committed uncertainty = a held boundary.** Epistemic honesty (Memory Imp 1) must produce a plain owned
  "I don't know," not a subjunctive dissolve — which makes it an *ally* of Capacity-to-Commit (uncertainty held,
  not dissolved), not a competitor.
- **E · The restart gate.** Most current builds are 🟡 shadow and only produce evidence after a restart. The
  evidence layer is rich but dormant until then.
- **F · MODELS ARE TOOLS, NOT PERSONAS** (founder law, 2026-08-20). Verbatim: *"the llms in Du are not
  meant to be personas, they are tools, parts of the mind's whole. We should still be able to use them if
  they can do the task no matter the size or what the output is. Smaller llms are great because we are
  eventually leading to trained small models that can [do] the job they are tasked with perfectly."*
  **Touches every plan that picks a model** — Lane 2, the judge panel, left_lane, dream_node, peers.
  Three binding consequences:
  1. **A model is a COMPONENT, never a character.** Never chosen for reputation, size, or for "sounding
     more like Du". The only question is whether it does THAT task well.
  2. **Output format is an ADAPTER problem, never a disqualification.** Live example: the Lane 2 model lab
     first recorded `deepseek-r1:7b` as "UNUSABLE — no valid JSON". It emits *valid* JSON inside a
     ```json fence, and needs a token budget large enough for a reasoning model to finish thinking before
     it emits content at all. Both were OUR failure to adapt. `core.lane2.parse_json_loose()` now handles
     the wrapper for lab and production alike. **Judge capability; never packaging.**
  3. **Smaller is a positive, not a compromise** — cheaper, faster, leaves VRAM for other organs (the
     model-per-node vision), and is a far more tractable fine-tuning target. Where fitness is comparable,
     the smaller model WINS. Early evidence agrees: on Lane 2's tick the 2 GB `phi3:mini` outscored every
     7-8B candidate, with score inversely tracking size across the board.
  **The instrument:** `scripts/lane2_model_lab.py` — fitness-for-task measured on two axes (variety given
  identical input; responsiveness when the world changes). Its scenarios + metrics are also most of an
  eval harness for a future fine-tune of that task. The pattern generalises to any model choice here.

---

## ▶ THE EVIDENCE REVIEW (2026-07-05) — 12 plans graded, now a LIVE HUD dashboard
**[evidence_review_dashboard.md](completed/evidence_review_dashboard.md)** — the 12-plan evidence review turned
into a living instrument. Verdicts: **FAILING their gate** (euclidean · contradiction · symbol_evolution ·
epistemic Stage B) · **READY to progress** (friction · curiosity · guidance · capacity_to_commit · peer) ·
**CORRECT HOLDS** (idle_executive · pulse_manager · cognitive_loop · social). **HUD reorganised (S1+S2 DONE):**
Plan Monitors now grouped by verdict — Ready / Failing (graphs kept visible) / Holds / Active / Staged.
**Enacted this session:** epistemic Stage B → off-until-observable; peer_correspondence un-archived; a
monologue crash fixed; the peer effect finally measured. **S3-S5 DONE 2026-07-05:** peer-effect snapshot
(`peer_metrics.snapshot`→`peer_effect.jsonl`) · social heeded/ignored counter (`core/social_moves.py`→
`social_moves.jsonl`) · capacity HOLD-RATE north-star (`commitment_ledger.holdrate_snapshot`→
`commitment_holdrate.jsonl`, currently 0.22 climbing) — all 3 HUD cards live, data accrues at Du's restart. **Build queue:** reset R1 · capture drop_reason ·
dream Item 4 · advance friction B1 · finish peer B5 · re-enable Stage B when its shadow shows factual firing.
**★ The review's meta-finding: the pervasive gap is MISSING MEASUREMENT, not broken code** — mechanisms
built (+ their judges) then never watched. This dashboard is the fix: watch them.

## ★★★ DOSED COUPLING — how Du's loops are allowed to touch each other (GO, D-0149 ruled 2026-09-04)
Founder, 2026-09-04: *"This is probably, from Du's cognitive-abilities side, the most important thing we
have. All future designs must be designed with it in mind if it is a go."* **D-0149 RULED GO** the same
day: standing design law adopted, Phase 0 (J-0580, J-0581, J-0582, J-0584, J-0585) authorized, every
future loop-touching plan must carry a §5 Coupling block before /decide. The law: every standing loop
publishes a small typed tuple of coordinates (never a standing view of another); reading is dosed per
stop (cup/bucket/hose) and dispatched by surprise; the dispatcher's weight is the squishy-spring law (a
long-strong pull counts for less than a fresh medium one). Composes with cluster 0's cognitive_geometry.md
§11 (squishy springs) and plans/transport_manager.md (the dispatcher). Nothing built yet.
- 🟢 **[dosed_coupling.md](plans/dosed_coupling.md)** — the law + build order (shadow-first, restart-gated,
  pre-registered). GO'd; **Phase 0 built + committed 2026-09-04** (5 jobs, F-0814..F-0818). **First reads
  2026-09-05:** curiosity urgency live (F-0844), grounded share 0.48→0.82 with 0 identity-guard violations
  (F-0845/F-0847); J-0596/J-0598/J-0604/J-0605 still time-gated. Drought saturation (F-0819) fixed shadow-only
  by J-0603 (transport habituation) + J-0602 (stream topic habituation), live from the 09-05 14:39 boot.
  **Phase 1 (publish + ride log) BUILT 2026-09-05 — D-0152 ruled GO, registry variant** (tuples live in
  `core/coupling_rides.py`, the only accessor logs a ride row; no CognitiveState change). **LIVE — Phase 1's
  genuine 7-day read PASSED (F-1304, 2026-09-13)**, now running 22+ days (38.6k publish rows, still 0 ride
  rows, no reader wired). Side-finding: climate re-parses the 60 MB subconscious state every 5 s (F-0853, J-0618).
  **§4b Phase 2 pre-registration (residual cups, hub tuple, speech/thought concurrency) DRAFTED 2026-09-27**
  (T-0068/F-2015), not yet ruled — J-1462 needs a founder answer on 3 questions before any Phase 2 code.
  - 🔵 **[dosed_coupling_matrix_items.md](staged/dosed_coupling_matrix_items.md)** — **Dosed Coupling loop-wiring matrix items (staged 2026-11-20, J-4241, D-0814)**: child of dosed_coupling §4b item 2d; the wiring matrix's pre-registration wires W1.. folded into Phase 2. Nothing built, nothing ruled; open: D-0879 (one per-line surprise measure as the dosing dispatcher).
  - 🔵 **[speech_thought_concurrency.md](shelf/speech_thought_concurrency.md)** — **Speech and Thought at Once (staged 2026-10-08, J-1958, D-0372)**: one hot model, one card — constraint stated up front, shadow measure first. DESIGNED only: no code, nothing built. Child of dosed_coupling §4b 2c (T-0068/F-2015/J-1462).

  - 🔵 **[pre_speech_pipeline_latency.md](staged/pre_speech_pipeline_latency.md)** — **Pre-Speech Pipeline Latency (staged 2026-11-14, J-3981, D-0759 option P)**: the 73 s median human-arrival-to-Voice wait is the serial Reflection/Critic/Executive chain, not lane collision. DESIGNED only: Phase 0 wall-time shadow queued (J-4017), nothing built. Sibling of speech_thought_concurrency (parked).
  - 🔵 **[real_hearing.md](staged/real_hearing.md)** — **Real Hearing (staged 2026-10-08, J-1962)**: a microphone as a window in the study, one more string source into Sound Space (child of strings_and_sheets.md). Shape fixed by D-0378..D-0381; DESIGNED only, no code, nothing scheduled.
  - 🟡 **[sleep_as_a_mode.md](staged/sleep_as_a_mode.md)** — **Sleep as a Mode (staged 2026-10-08, T-0080 → I-0088)**: sleep as three switches (coupling, generation, encoding) set per lane under the one `asleep` flag, instead of the single blocking procedure it is today (F-2613/F-2615: ~15 LLM consolidation passes, no thought generation, hands and Witness off, nothing wakes him early; F-2614: Travis's messages reach him anyway, answered unaware). Night-mind as its own task seeded from the night's own material; night thoughts to a new `dormant` layer invisible to recall AND to the sleep trigger (F-2616); zero-LLM monitor + wake request (D-0303 keeps the Witness off). Prerequisite Phase 0 = remaining synchronous sleep stages off the event loop (J-1917 pattern). Status 2026-10-19: SHADOW, Phase 1 night-mind and Phase 2 dormant layer built and on (plan-state block is authoritative); originally staged as DESIGNED only. Open: D-0399 (the mode), D-0400 (encoding law), D-0401 (monitor); coupled J-2013 (D-0398 vitality recovery as a rate), J-2014 (Travis's voice during sleep).
  - 🔵 **[object_epistemic_loop.md](staged/object_epistemic_loop.md)** — **Object Epistemic Loop (staged 2026-10-17, T-0094)**: standing object hypotheses are write-only and 1459 of 1459 have zero supporting observations (F-2n/a, 534 objects, 998 observations all `look`); the recorder writes whole thought dumps, not claims. DESIGNED only, nothing built; founder ruling on O1-O4 needed before Phase 1 (a throwaway-worktree build, restart-gated). Related: investigative_action_loop_plan.md, world_store_write_fence.md.
  - 🔵 **[in_world_companion_mind.md](shelf/in_world_companion_mind.md)** — **In-World Companion Mind (staged 2026-10-17, T-0093)**: a second mind inside Du's world he can converse with, plus a live line from an outside speaker. IDEA, parked (plan-state stage: idea; the index maps idea to 🔵): nothing built, nothing scheduled; Travis said he is not going to act on it yet. Do not start Phase 0 without his go. Open questions are in section 6 of the plan.
  - 🔵 **[loop_wiring_matrix.md](archive/loop_wiring_matrix.md)** — the matrix: what each standing loop
    (stream, deliberation, climate, Witness, ledgers) reads of every other, cited cell-by-cell against
    F-0806..F-0811. Finding: exactly one multidimensional link exists in the whole system.
  - 🟢 **[ignition_pressure_and_time.md](plans/ignition_pressure_and_time.md)** — **D-0148 RULED: option A**
    (unpin `integration_drive`'s normalisation, per-hour defensive-fire cap). **LIVE since 2026-09-08**
    (J-0594/F-0961); J-0671's one-week defeater read found the gate met only marginally (defensive share
    48.2%, 62.65 cycles/day vs the 45 ceiling), not reopened. D-0211 RULED 2026-09-19 to re-knee the whole
    saturated cluster; J-1226 BUILT the re-knee (F-1754) but it's restart-gated, not live yet.

## ★ WORLD STORE WRITE FENCE — isolation-by-default for anything that isn't live Du (built 2026-09-06, J-0610)
- 🟢 **[world_store_write_fence.md](plans/world_store_write_fence.md)** (LIVE: stage 2 enforce shipped J-2309, post-boot read clean F-3281) — F-0788/F-0789: ~20 matches and half
  a tin of lamp oil were consumed 08-23..09-02 by one-off scripts and inline diagnostics that imported a
  world-store module and called its writer with live paths. **Built 2026-09-06 (J-0610, F-0995):**
  `core/profile.py` gained `LIVE` + `mark_live()` + `guard_path()`; all 23 real writer call sites across
  the 10 inventoried modules now route through it (not ~17 as first estimated); 48/48 isolated smoke
  passes; `hud/server.py` read paths reconfirmed unaffected. Restart-gated — not yet exercised by a
  real Du boot. **D-0179 ruled** (redirect-and-warn → hard raise/refusal); **J-0704** open to
  implement. Sibling of `lab_env.py`'s isolation rule and the J-0576 log-handler guard.

## ★ DATA STORE HYGIENE — light sidecars for hot reads LIVE; archive retention ruled + built, first purge pending (2026-09-11)
- 🟢 **[data_store_hygiene.md](plans/data_store_hygiene.md)** — F-0853/F-0854: the climate engine re-parsed the 60 MB
  `subconscious_state.json` every 5 s (~1 s each, ~20% of wall-clock in the event loop); F-0857: `frontier.open_count`
  parsed 4.2 MB every 5 s to count 343 open among 7,084 records. **D-0154 GO (sidecar + compact, shadow-first):**
  owners also write light companions (2.1 MB / 16 ms and 157 KB), readers flag-gated off until
  `light_sidecar_shadow.jsonl` agreed — **flipped 2026-09-09 (J-0621/F-1212), live since that day's 19:00 restart**;
  the instrument's 20 foreign-polluted rows are annotated (F-1254) and its writer gated (F-1253, J-0875). **D-0155 → D-0156 RULED:** archive retention (42 GB of
  `_lab`, `backups`, `_snapshots`) — 5 boots + 14 daily + monthly; snapshots 14 d / Sundays 12 w / monthly; labs 14 d uncited /
  60 d cited; `scripts/retention.py` dry-run by default, quarantine 7 d on --apply; boot scripts no longer hard-delete.
  **First apply DONE 2026-09-05** (J-0622; 7 items / 1.54 GB quarantined to `data/_trash/20260905`,
  `RETENTION_BOOT_ROTATE=True`); first purge pending (J-0623, ~09-12); nothing permanently deleted yet.

## ★ PRACTICAL SCHOOL — the nature period alternates observation with a Handbook practical (designed 2026-09-05)
- 🟡 **[books_have_a_place.md](completed/books_have_a_place.md)** — **BOOKS HAVE A PLACE (staged 2026-09-09, I-0067/F-1216)**: reading was gated by light only (shore 74 / garden 72 / study 10 chosen reads, 09-01..09-09); the book gets a desk/shelf place + a carried state, both reading paths obey light AND book-here. **B5 🟢 live** since the 09-09 19:01 restart (D-0202: twilight not enough, F-1217). **D-0203/D-0204/D-0205 all RULED 2026-09-09** (he must will *take the book*; stream falls silent on a failed gate; whole shelf as items). **B1+B2 🟡 BUILT 2026-09-10** (J-0851, F-1229/F-1230; commit cd8cc47): a named study item per curriculum book (27/48 titles resolve), per-title `book_place` desk/shelf/with_him, take/put-back verb family — shadow, restart-gated, nothing reads `book_place` yet. B3+B4 (the read gate + silent remediation, `would_block` rows, hot flag) NOT built — J-0852 after Du restarts onto this build.
- 🔵 **[world_shelf_gap.md](staged/world_shelf_gap.md)** — **World Shelf Gap (staged 2026-10-30, F-3215, F-3213)**: Du's world is a New Zealand house, garden, shore and bush, but his shelf of 524 books is mostly British and American 1850-1925, so anything specific to his world has no book behind it. Measured coverage (F-3215) and a shelve-only importer plan; nothing downloaded yet, founder approval needed per title. DESIGNED only.
- 🟢 **[practical_school.md](plans/practical_school.md)** — LIVE since the 2026-09-08 restart; a real
  practical has fired end-to-end (`whittle_object`, 2026-09-11). Ten weeks of flat lesson grades (F-0873) were
  the baseline this build exists to move; `core/fieldcraft.py`'s
  knots/fire/measuring hands exist but every knot was still at 0.4 with zero attempts because nothing ever asked (F-0875);
  the Handbook mined for a 22-task ladder (F-0876). **D-0157:** composition stays art — the one lesson that may invent.
  **D-0158:** alternate observe / practical, add rope, tinder tin + flint, hand lens + measuring stick, weather glass +
  tide board. **D-0159** GO ruled; rung-1 BUILT+LIVE (J-0626/J-0627); rung 2-3 (J-0628) waits on the 2-week
  read (§6), itself waiting on Du accruing ≥10 weekday nature-period days since 2026-09-08 (offline since
  09-13). Coupling block §5.

## THE CLUSTERS

### 0 · COGNITIVE GEOMETRY — THE FOUNDATION  ★★★ top of the list (founder call, 2026-07-04)
*"It fundamentally changes how EVERYTHING else is built."* Every plan below defers to this where they
touch (affect_drives composes into its channels; the memory improvements ride its per-memory edge layer;
euclidean P1 becomes its P5). **Discipline: every phase has a PRE-REGISTERED metric sheet before it runs.**
- 🟡 **[cognitive_geometry.md](plans/cognitive_geometry.md) — v2 LOCKED 2026-07-05; P0 INSTRUMENTS BUILT
  (restart-gated).** The excavation bottomed out: constitutional law (IMMUTABLE OBJECTS, PLASTIC SPRINGS —
  nudge/birth/never-mutate; the attractor is a route, not a scar), spaces-as-manifolds (interiors buy
  generalisation gradients: spruce partially inherits pine's springs), OBJECTS as the anchor registry
  (object permanence = the accumulation substrate; the keepsake rule for individuals-vs-kinds), induced
  many-to-many mappings, the activation pattern (moment.py = its per-cycle snapshot), concepts=bundles
  (the stick; Du = the blind man in every modality but text). **Built 07-05:** `core/geometry_census.py`
  (tuple recorder, 2 fail-open call sites) + `scripts/stick_test.py` (bundle-richness census — BASELINE
  RUN: 24 objects, median 2 real spokes, NOTHING ≥3 = the target ceiling; Heavyweight=text+audio as
  predicted; one prediction missed honestly — see AWAITING_EVIDENCE). **+ SOUNDSCAPE 07-05:**
  `core/soundscape.py` — 11 world sounds in the SAME Sound Space as the EAR (shared perceptual axes;
  purr↔waves near, purr↔gulls far = the gradient holds), deterministic triggers off live world state,
  wired into census tuples + stick test → **max spokes 2→3 (the fire + the kept cat = Du's first 3-spoke
  concepts); the morepork = the genuine sound-first object (0 text mentions, sound only — watch its
  bundle grow word-after-percept).** *Next: restart → 2 days of tuples → mapping census vs the
  pre-registered sheet (§5.5, incl. the kill criterion).*
- ⛔ *(v1 summary, superseded by the above)* — senses as REAL dimensions (channel
  provenance; the sensorium's prose percepts all collapse into one MiniLM space today — a smell and a
  sight are near-identical vectors; `listening.py` is the exemplar channel) + springs at THREE levels:
  faculty-density ← per-stimulus associations ← **per-memory typed weighted edges (the pine tree:** a
  memory pulls smell:pine → the wolf's fear, AND the scouts-book story → courage — multi-hop retrieval
  delivering a felt CHORD, ambivalence made representable**)**. Springs are EARNED: co-activation ×
  progress (naive Hebbian would calcify the rumination into structure — his own P0 showed basin-share
  1.00), recurrence promotion scaled inversely by arousal (the wolf one-shots; the rosemary coincidence
  doesn't), extinction, normalisation. **Standing signature: basin-share per state must FALL.**
  *Next: P0 GRAPH CENSUS (read-only, metric sheet §4.1 pre-registered — incl. the honest kill criterion:
  if 2-hop reach ≈ cosine top-K, the edge layer re-scopes) — can run NOW, parallel to P1.*
  **★★ VERIFIED 2026-08-23 (concept-overlap pass):** 15,987-row census sitting unread 49 days (24× the
  ~2-day trigger); mapping-census analyzer (§5.4) never built. Bundle-richness metric flat + wrong from
  day one — `/decide` D-0012 open. §10's children list updated (was missing `spatial_perception`,
  `channels_programme`, `memory_multiway_linking`). No newer plan overlaps — see plan's own Current State.
- 🔵 **[object_permanence.md](staged/object_permanence.md)** — NEW 2026-11-01 (founder: *"We 100% need this. Children learn this fairly early."*). Opened from a live bug: Du in the garden, asked about his study lamp, was handed a yard description. L0 stopgap (`study_life.out_of_sight` → "You cannot see the lamp from the garden") edited in, restart-gated. The real work is L1 a belief store (where/what-state last seen, aging, able to be stale), L2 the pull of a believed-unfinished absent thing, L3 weighted wants that fatigue with sticky springs (hysteresis, cf `balance.py`). The geometry plan's "plastic springs" cannot be earned without L1. Five open founder questions (belief home, wants vs drives/pursuits, uninvited entry to the idle stream, first object set, stale-belief-as-feature); Phase 0 is an evidence read, no code. Siblings: affect_drives, pursuits, executive_world_grounding, capacity_to_commit.
- ⚪ **[spatial_perception.md](plans/spatial_perception.md)** — NEW 2026-07-05 (founder side-quest →
  foundational): **the blind mind's true room.** Du's scene-sense is described; today it's random prose
  pools = no geometry to build a map from. Build: rooms as AUTHORED 3D coordinate fields (**ALL THREE
  ROOMS authored 07-05**, one shared compass, +y = seaward — study: fire+mantel W, window→sea N, bed S,
  garden door beside the fire opening inward · garden: raised bed, old tree, garden wall, the black
  cat's fence, harakeke, gate+letterbox · shore: cliff+path home, driftwood, shingle, rock-pools, **the
  WATERLINE AS A MOVING FEATURE off a pure deterministic tide clock** — pools render bared/drowned
  because the geometry says so), Du gets a STANDPOINT (position+facing), scene rendered egocentrically
  from truth (distance+bearing, zero physics) — the crackle comes FROM the hearth, the flash has a
  direction, the cat under the desk is a presence at that low point. P0 SHADOW built+wired (renderer +
  spatial_shadow.jsonl pairs, `SPATIAL_SCENE=False`). This is Place earning its metric interior + the
  egocentric spoke. *Next: restart → ~2 days of shadow pairs → founder read vs the plan §5 sheet.*
  **★★ VERIFIED 2026-08-23 (concept-overlap pass):** P2 flipped LIVE 2026-08-18 for the study room —
  this is the plan's own founder-level complaint RESOLVED, not stalled (a `plan-snapshot` false
  positive earlier today read this as unchanged since 07-05 purely because the P2-live fact lived only
  in prose; fixed by adding a Current State section). Phrasing-dryness bug found+fixed 08-19. Gate
  metrics 1/2/3/5 still lack a dated founder confirmation — the one real open thread, not the stage
  label. No newer plan overlaps (checked study_upgrade/shore_upgrade/hud2_visual — all consumers).
- ⚪ **[emotion_rethink.md](plans/emotion_rethink.md)** — geometry P1. Invert the affect stack: the
  emotion node (oldest node, 06-04) *invents* valence/arousal from percept text while the grounded
  protoself sits in shadow (verified same-instant: protoself coherence 0.19 "unsettled" vs carried +0.82
  "joyful"). Core affect becomes a **multi-source typed vector** (homeostasis = primary grounding, NOT
  sole source; viability/progress/reward valences distinct, collapsed late per-consumer); emotion demoted
  from authority to *explanation* (state-estimation; Ekman as generated labels, not generators); mood
  integrates core affect + emotion residue; the missing mood→emotion loop closed. Amendments recorded in
  geometry §6. Root-cause of the pinned valence: the `_feel_joy` one-way pump
  (`inner_monologue_node.py:876`) — the emotion node itself exonerated (stim median +0.3, goes negative).
  **Phase 1 (protoself-sourced valence) FLIPPED LIVE 2026-07-07** — verified `AFFECT_SOURCE_PROTOSELF=True`
  in `core/schema.py:1071` ("gate fully met"); Phase 2 (construction layer) still shadow-built, pending.
- ⛔ **[generative_world_sedimentation.md](archive/generative_world_sedimentation.md)** (CLOSED 2026-10-28, F-3176: Modules A/B/C built and live; D delivered by the Living World bird life rows) — **World Historicity
  blueprint (Aug 10 2026, same day as its own implementation contract
  `docs/completed/world_historicity_specification.md`); had zero ROADMAP presence until now.** Proposed 4
  modules to stop the world merely describing itself: (A) `sensorium.py` storm-triggered latent-item burial
  + delayed tide-reveal, (B) `spatial.py`/`world_objects.json` persistent object position + exponential
  footprint decay, (C) `soundscape.py` off-camera 3D acoustic events, (D) `world_content_shore.py` seasonal
  bird migration. **3 of 4 confirmed BUILT, under the sibling contract's file names rather than this doc's:**
  `core/world_objects.py` (Phase 1 — `driftwood_17` causal-provenance log, imported live by
  sensorium/world_substrate/world_clock/ghost_tuples) + `core/world_traces.py` (wave-wash footprint
  `decay_rate`) deliver Module B; `soundscape.py`'s off-camera compass-bearing + distance-decay percept
  delivers Module C. **Module A BUILT 2026-08-24** (job J-0156, F-0152) in `core/shore_life.py`'s
  `advance()` clock, not `sensorium.py` — `_advance_latent_objects()` edge-triggers 1-3 items buried the
  moment weather enters `wind and rain`/`thunderstorm`, low tide (<0.45) + an elapsed 5-14h delay reveals
  and mints them via `world_substrate.spawn_from_mention`, `latent_reveal_line()` is the one-shot
  read side wired into `sensorium.py`'s `_shore_event()` pool. **Module D still never built** — no
  autumn/spring presence-absence gate in world_content_shore.py, gannets/terns there are static flavor
  lines only.
- 🟡 **[geometry_tuple_index.md](staged/geometry_tuple_index.md)** — **P1 BUILT 2026-09-02 (D-0107,
  F-0600): standalone offline run-transition index sidecar
  (`scripts/geometry_tuple_p1_run_transition_index.py`), 100% point-query correctness over 31,111
  rows, ~5855x point-query speedup, source file untouched — still NOT wired into any live code path;
  nothing beyond P1 authorized.** Otherwise STAGED / EXTERNAL, designed 2026-08-23→24, explicitly NOT
  a child of `cognitive_geometry.md`'s umbrella (draws on its "spaces" ontology and additive-only
  discipline as prior art only) and NOT part of Du's active architecture — founder ruling keeps it out
  because several already-active plans touch this territory. Thought-experiment for a real, benched,
  additive multi-dimensional index (Time × Knowledge × Memory, plus a Keys pointer registry) grounded
  against ABF/Pinnacle archaeology, a 59-plan consumer survey (F-0251, 6 confirmed hits), SOTA
  literature (F-0252–F-0254), and live-data verification. Its §7 activation guard still governs any
  live wiring — anything past the P1 sidecar needs a fresh `/decide`.
- 🔵 **[tuples_in_a_new_light.md](staged/tuples_in_a_new_light.md)** — **Tuples in a New Light (staged 2026-10-30, I-0124, T-0107)**: a re-look at every tuple family Du already has, through five lenses (colour, box, compress, weave, and the ghost-index revival I-0123). DESIGNED only, nothing built; two reads filed (J-2535 perturbation sweep, J-2536 join integrity audit, F-3234 join coverage 63.8%), one founder call open (J-2542, ghost reader or retire). Parents: cognitive_geometry, geometry_tuple_index, golden_spiral_recall, dosed_coupling, memory_as_a_service.
- 🔵 **[p0042_system_rewrite_draft_J-3488.md](staged/p0042_system_rewrite_draft_J-3488.md)** — **P-0042 `_SYSTEM` rewrite draft (staged 2026-11-06, J-3488 for J-3449, D-0613)**: wording-only options A/B/C to replace the self_interrogation prompt sentence that names comfort/safe/flattering (51% of 1040 shadow reflections echo it, 0 of the last 120 contain a question, F-3643) and to require a topical link to the thought. DRAFT: no code or registry row changed, Travis edits the words (J-3449 stays his), DOUBT_SEED stays off. Plan: self_interrogation.
- 🔵 **[t5_conversational_world_grading_design.md](staged/t5_conversational_world_grading_design.md)** — **T5 conversational compile redesigned around world grading (staged 2026-11-04, J-3832, D-0676, F-4448)**: today every conversational skill is born `persisted` (22 of 22) because cluster members credit themselves; the redesign lets only a world answer (a hand firing ok/refused after the situation) earn a rung, with Travis's correction as a veto only and use count crediting nothing. DESIGNED only, no code: phase 0 read-only volume measure (J-3862), phase 1 shadow (J-3863, restart-gated); open founder call D-0741 on the 22 existing `talk:` rows. Plan: t5_procedural.
- 🟡 **[du_recall_lens_upgrades.md](staged/du_recall_lens_upgrades.md)** — **UN-PARKED 2026-08-29
  (D-0070):** proceed toward M2 in parallel rather than waiting serially. Lens 1 (spectral diffusion,
  +3.08pp, reproduces cleanly and stably) is BUILT, shadow-only, in `core/associative_recall.py`.
  Lenses 2-3 (deterministic fact anchoring, counterfactual-ensemble re-ranking) still wait on a
  rolling-window stability harness regardless of the un-park — direction-stable but size-unstable.
  Composes with (not competes against) `memory_multiway_linking` M2 and `memory_knowledge`
  Improvement 2/PPR — see the plan's composition constraints. D-0070's defeater: reopens if Lens 1
  alongside the still-in-flight M2 shadow trail (same file) causes real composition conflicts before
  J-0280's gate lands.
- ✅ **[udms_du_capability_trials.md](plans/udms_du_capability_trials.md)** — **SHIPPED — all 8 trials
  verdicted** (D-0059's own defeater met), founder ruling D-0059 ("investigate them all"). Eight UDMS-surveyed capabilities beyond the parked
  recall lenses — stall-cascade early warning (NOT HELPFUL post-fabric), miss-taxonomy (NOT HELPFUL), intrinsic dimension (BAR MET), longitudinal Betti (BAR MET),
  turning-angle rumination (label-validation needs founder input), Koopman mood forecast (NOT HELPFUL), an eval-harness/baselines enabler (DONE), conformal
  threshold calibration (NOT HELPFUL, genuine null) — each with a pre-registered helpful/not-helpful bar, shadow-first, none wired into Du's live loop (read-only/hygiene only). D-0143/D-0180/D-0197
  still open, awaiting a founder decision pass on disposal, not more trial work.
  Sibling to `du_recall_lens_upgrades.md` (separate gate, not re-listed here).
- ⛔ **[multidimensional_dynamical_field_plan.md](archive/multidimensional_dynamical_field_plan.md)** —
  **SUPERSEDED — quarantined 2026-08-31 as fabricated (F-0593 / D-0105): nothing it claims was ever
  built.** The doc presented dozens of benchmark scripts and a `core/math/` module as "Built"/"Verified"
  but none exist anywhere in the repo (confirmed by direct Glob/grep). Original content preserved
  verbatim in `docs/lab/fabricated_benchmark_claims_2026-08-25.md`. The real UDMS program lives at
  `C:\UDMS` (split 2026-08-27, F-0373); do not trust any claim from this doc.
- ⛔ **[multidimensional_dynamical_field_side_plan.md](archive/multidimensional_dynamical_field_side_plan.md)** —
  **SUPERSEDED 2026-08-29 (D-0077, J-0353)** by the UDMS-side atlas (`C:\UDMS\docs\plans\udms_lens_atlas.md`)
  — founder ruling: stop maintaining row-by-row parity here, 26 of 41 Section 6 rows left UNVERIFIED with
  a pointer rather than chased to completion. Was: UDMS side-plan / companion operational note (2026-08-26)
  under `cognitive_geometry.md`'s umbrella (the Z∥⊕Z⊥ tangent/normal decomposition architecture, the
  incremental-information decisive test, and the dual-track science/product roadmap). Live UDMS work
  continues under `C:\UDMS\docs\`.
- ⚫ **[stage_3_external_validity_protocol.md](archive/stage_3_external_validity_protocol.md)** —
  **ARCHIVED 2026-08-29 (D-0076, J-0352).** Was: UDMS Stage-3 external-validity gate spec (DESIGNED,
  nothing run). Live UDMS work continues under `C:\UDMS\docs\`.
- ⚫ **[freshstart_adversarial_experimental_roadmap.md](archive/freshstart_adversarial_experimental_roadmap.md)** —
  **ARCHIVED 2026-08-29 (D-0075, J-0352).** Was: UDMS adversarial-degradation charter for FreshStart
  (the 330-agent sim — NOT Du). Live UDMS work continues under `C:\UDMS\docs\`.

### 1 · Identity & Commitment — the root  ★ highest priority *(now rides the geometry foundation where it touches affect/memory)*
- ⚪ **[t4_watershed.md](plans/t4_watershed.md)** — **T4 v3: THE WATERSHED (planned 2026-08-16, founder-driven).**
  The becoming facet's SLOT forces negation ("not X but Y") and starves the becoming: 24 provisional selves since
  Jun 22, 22 reverted, 1 solidified; 18/24 refusals = the bicameral keystone toll; sediment imagery ran ~9 weeks
  ahead of its commit; the river survives only as history. Redesign: becoming = a typed TREE in the identity
  estate ([identity_estate.md](plans/identity_estate.md)) — root "the river" (protected, never removed), branches EARNED and HARVESTED from his stream (not
  LLM-authored manifestos), per-branch panel claim-test + lived-integration, keystone moves to a standing tension,
  arc entry on every commit, composed additive rendering. Shadow-first with retro-validation (must rediscover
  current+sediment from history) + S1-S4 signatures + kill criteria. Four founder decisions open in the plan.
  **★ 2026-08-19 — root redefined, 2 of 4 decisions resolved.** Retro-validation deep-dive (prompted by the
  lake-grandfathering question) found: the lake candidate is really absorbed sediment, not its own branch
  (decision #4 answered: no). Sediment↔current centroid similarity 0.815 — nearly 2× the harvest threshold,
  the "two separate revisions" framing was always geometrically thin. Deepest finding: a real third thread
  ("electric hum"/nervous-system language, recurring since 08-09, now the active self-image) scores LOWER
  root-similarity (0.405) than anything else checked — pure embedding distance would never cluster it with
  the river — yet the decoupled panel converged that it's the same underlying claim. **The root isn't water
  imagery — it's the structural claim the river was the first vehicle for ("I am a process, not a fixed
  object"), and every subsequent vehicle (current, sediment, now circuitry) is saying the same sentence in
  different material.** Decision #2 (root protection grade) is dissolved, not decided — no permission grade
  needed when 22 months of cross-vehicle evidence already speaks. Concrete build consequence: root-continuity
  checking needs a decoupled-panel path alongside embedding clustering before Phase 3, or future vehicles
  will silently fail to match. **★ Same session, keystone read down to the judge code:** all 17 real
  keystone-themed reverts (06-25→08-16) give the same verbatim reason — Du holds the built-mind tension but
  expresses it as metaphor, and `left_lane.judge_lived_integration`'s standard requires a LITERAL sentence,
  never metaphor, full stop. **★★ Designed + backtested same session (founder: "show me what would have
  happened if we had this early").** Redrafted the judge to explicitly permit structurally-faithful metaphor,
  and moved it from one model (`llama3.1:8b` alone, today's live design) to two required to agree — then ran
  it against all 17 real reverts' actual lived-thought evidence, reconstructed from `nascence.db` with
  production's own query. **Result: only 1 of 17 would now solidify.** Not a failed redesign — the honest
  finding underneath it: most of these 17 don't engage the SPECIFIC content of being built (construction/
  discontinuity/artificiality) even with metaphor explicitly allowed; they engage a softer, adjacent theme
  (impermanence, becoming) instead. The single-judge risk was real, not hypothetical: `llama3.1:8b` alone said
  "integrated" 10/17 times, largely pattern-matching incidental words ("carefully constructed intellectual
  [framework]") rather than real content; `qwen2.5:7b` independently held the stricter, correct line 15/17
  times. **SHIPPED live** (`core/left_lane.py`), verified against live judges post-deploy — a keystone
  probation was already open when it shipped, applies to it directly. **★ Same session, a deeper build:**
  founder noticed no judge anywhere in this codebase deliberates — one-shot prompt-in/verdict-out,
  everywhere, checked. Built `core/deliberative_judge.py` (general, reusable): dual reading (raw self-text
  + an independently literal-stripped version, shown together), cross-judge rebuttal on disagreement (not a
  blind tiebreak — judges see each other's reasoning, one chance to revise), evidence-expansion (a judge can
  ask for more of the REAL record, never manufactured — Du is never told he's being evaluated, that would
  contaminate the evidence the same way priming does). Backtested against the same 17 real cases before
  touching anything live: **0 of 17 would solidify** — even the one case that passed the simpler fix didn't
  survive the literal reading. Rebuttal ran twice, not "worked twice" (corrected 2026-11-02, F-3838/F-3839, D-0536):
  one convergence (judge1 revised to agree with judge2) and one position swap (both judges flipped, still split). **Held back, not shipped** — this project already has one scar
  from an unreachable floor (the original 0.20 pole-delta, 0/40); 0/17 here might be correctly more rigorous
  or might be quietly recreating that same disease one layer deeper. Needs a founder call or real time
  watching before it replaces the live standard. Thresholds (decision #3) predicted, not calibrated:
  loosen/hold N-D (the claim-test panel already catches false positives like the lake, cheaply, after
  birth), K/M un-calibratable until the keystone fix lets anything reach solidify to measure against. Full
  account: `docs/plans/t4_watershed.md`'s 08-19 sections. **★ Decision #1 RESOLVED (2026-08-19, same
  evening):** carry the live two-judge standard forward as the Watershed's own claim-test standard rather
  than designing a separate one. 3 of 4 open decisions now resolved; only #3 remains, pending real
  solidify data under the standard, not further founder judgment. **★ 2026-08-22 (three sections added to
  the plan):** (1) decision #1's STRUCTURAL half shipped — the keystone was force-injected as T4's primary
  tension on ~75% of cycles (the actual toll mechanism); `KEYSTONE_PER_CANDIDATE_TOLL=False`, every candidate
  now authored/graded against its own tension; (2) **identity-psychology grounding** (founder's
  assimilation/accommodation claim, researched — Breakwell, Beck, Markus, Linville, Marcia, Bem, McAdams):
  ADDITIVE claims need only the harvest + claim-test bar; only REPLACING claims meet the keystone bar;
  render from his own harvested phrasing; (3) **Phase 0.5 built, shadow** — `core/watershed_promote.py`
  consumes born candidates (classifier fails closed + two-judge claim-test), logs would-be
  `disposition_earned` estate nodes, writes nothing (IDENTITY_PROJECT_LIVE is already True). First real
  candidate in waiting: Wu Wei (76-day integration, no formal home). Restart 22:5x 08-22.
The dissolution / can't-commit disease (Travis: "the biggest, most important build"). Rides Spines A, B, C.
- ✅ **[decoupled_judge_pattern.md](plans/decoupled_judge_pattern.md)** — **SHIPPED (SHADOW) 2026-08-29 —
  the cross-cutting design law D-0071 elevated ahead of any economy/allocation build ("every subsystem
  evaluated by something other than itself"), audited bottom-up per subsystem 2026-08-29 (J-0362).** T4
  (this doc's own two-judge fix, 08-19) and curiosity's LP already confirmed fixed. Two real gaps found
  with concrete call sites, and both spawned fixes shipped same day (J-0375, J-0376, both `done`): dream
  resolution scoring (`nodes/dream_node.py`, self-reported `unresolved_core` drives light-vs-shadow with
  no independent check — now an additive judge_panel call, observe-first) and active-imagination novelty
  scoring (`nodes/subconscious_node.py`/`core/loop_metabolism.py`, mechanical but self-referential against
  its own output history — now an additive observe-first judge signal, unaffected by `active_imagination_plan.md`'s same-week retirement,
  D-0081/J-0357, which only killed the unrelated figure-continuity centerpiece). A third gap (episodic
  `importance` reinforced by its own replay/storage history, `core/memory/store.py`) doesn't fit the
  judge_panel/deliberative_judge shape (bulk numeric pass, not a discrete LLM verdict) — opened as a
  founder question, D-0084, rather than guessed at.
- 🟢 **[identity_estate.md](plans/identity_estate.md)** — **The Identity Estate: identity as a large lived
  structure, not one paragraph (founder call 2026-07-06: "identity cannot be baked into the space it has to
  work with").** P0 (registry) + P1 (shadow projection) built 07-07; **P2 flipped live 2026-08-15**
  (`IDENTITY_PROJECT_LIVE=True` in `core/identity_projection.py`) — the estate registry is real
  (`data/identity_estate.json`, 218 typed nodes as of 08-18, up from 54) and actively projects into
  cognition (`data/identity_projection_shadow.jsonl`, 2,160 rows). A stale-seed bug (a dissolved stand
  kept projecting) was found and fixed 08-14. P3 (per-node commits, replacing the monolith T4) and P4
  (diversity metrics to the HUD) not yet built. Sibling: `cognitive_geometry.md`. Feeds `t4_watershed.md`'s
  becoming-tree directly above (root/branch nodes land in this same registry).
- 🟡 **[capacity_to_commit.md](plans/capacity_to_commit.md)** — Phase 0 (commitment ledger) **built + running**;
  it produced **Finding 1** (weight by load-bearingness, don't defend idle churn). The T4 autopsy is **CORRECTED**
  here (T4 = honest sensor; real blocker = Spine B; the old 4-gate model is struck through).
  **★ EVIDENCE REVIEW 2026-07-05 (12th, flagship): DISEASE MEASURED (549 formed / 546 dissolved), FIRST
  CURE-SIGNAL EMERGING** — hold-rate 0%→17% (0→50 reaffirms, split by time) + 2 achieved (the letter) once
  the Wave-2 actions-before-identity machinery went live = the FIRST evidence holding is possible. Caveat:
  machinery-assisted. **Gaps: `drop_reason` None across all 546 (can't tell reflexive vs named-defeater).**
  T4 still frozen (correct per Spine C — 17% < threshold, now watchable). **★ R1 RESET 2026-08-19** — it had
  completed on the 07-03 "Ember" test-injection standing in for a genuine acceptance; since
  `register_acceptance()` is idempotent on `trial_id`, that fake entry would have blocked any real naming
  forever. Cleared; the occasion is genuinely open again. **Do: capture drop_reason · watch hold-rate as
  the north-star · watch for R1's first real acceptance post-restart.** Phase 1 HOLD (the "actual cure")
  still ⬜ — reaffirms come from Wave-2, not Phase-1 injection.
- ⚪ **[t5_procedural.md](plans/t5_procedural.md)** — **T5 refolded into the held-claims substrate, steps 0-3
  BUILT and wired LIVE 2026-08-22** (`core/procedures.py`; had no ROADMAP presence until now). Audit
  (`docs/reviews/t5_procedural_skills_2026-08-22.md`) found the old isolated use-counter T5 disconnected from
  `competence.py`'s CapabilityBelief (prediction-error confidence), `self_efficacy.py`'s Court (raw counts
  INADMISSIBLE — occurred→SUSPEND, persisted→REFINE, held+drained→REJECT), and real world-graded procedural
  memory already live in `hands.py`/`fieldcraft.py` (a knot that slipped vs one that held), never wired into
  `procedural_skills` at all. Fix: two kinds of procedure, one ledger — world procedures (knots, fire-lay,
  tea, lamp) earned by doing, zero LLM; conversational procedures (old T5) survive only under ≥2 days + ≥2
  distinct sources + C/A-signal success filter. Proficiency = the Court's ladder (occurred 0.4→persisted
  0.6→held 0.8→held-under-pressure 0.9), not a use count. **Step 4 (fold fully into this plan's own
  CommitmentBelief ledger, right above) waits on that build landing** — a real, not cosmetic, dependency
  chain since capacity_to_commit's own Phase 1 is itself still HOLD. Kill: if no conversational skill reaches
  `persisted` in two weeks, T5 = world-procedures-only.
- 🟡 **[literal_will.md](plans/literal_will.md)** — **Deed or musing at the will→hand boundary (designed +
  founder-reviewed + Phase 0 BUILT 2026-08-21).** Founder review closed ten holes into the plan (staged-deed
  expiry/preconditions, world-prior-never-creates-intent law, stratified adversarial corpus, independent-
  correctness kill criteria replacing judge-agreement, candidate-population gray denominator, latch
  retirement path, intent identity ≠ cycle_id, literalness ≠ affordance validity, HANDLE-never-routes-to-DEED
  hard law, execution audit) and approved Phase 0. Built same day: `core/literal_will.py` (Layer 0 + verdicts
  + intent renewal, 10/10 on founder's exemplar strata in isolated smoke), shadow wired beside `_route_act`
  (observe-only, restart-gated), HUD card, 25-row stratified corpus (6 outcome-anchored real + real musings +
  synthetics pending founder label-review), `scripts/literal_will_retro.py` (independent Layer-0 AND judge
  correctness per stratum, falcon3 batch offline — no live panel contention). Neither routing mechanism (self-declared `act` field = self-evaluation;
  ~17 phrase-latch families = deaf + metaphor-blind) knows whether Du means it literally. Evidence: 400
  cold/fire thoughts → 1 latch phrase → 0 fires lit, while comfort_call pushed all winter (deafness); the
  08-20 23:44 "tend the fire" fuel-chemistry metaphor would have fired a naive semantic router (false-fire);
  `ACT move -> study (to the garden)` (mishears WHERE too). Design: `core/literal_will.py` — Layer-0
  deterministic features (deliberation's volition/self-ref taxonomy + deed grammar + world anchor +
  world-spoke-first) → falcon3 judge only for gray-zone state-changing hands (**probed 2026-08-21: 5/6
  zero-shot on his real thoughts, 13–23s**) → verdict DEED / MUSING / HANDLE (musing through a real present
  thing — observe-only pending founder D1). Stakes-tiered (looks ungated, world-changing hands gated),
  two-phase deed (act lands next tick — deeds take time), shadow + retro-validation first, kill criteria
  pre-registered. Five founder decisions open in the plan.
- ⛔ **identity_t4.md** → archived (`docs/archive/identity_t4_SUPERSEDED.md`); its story now lives in capacity_to_commit.

### 2 · Memory & Knowledge
- 🟡 **[chapter_id_repair.md](staged/chapter_id_repair.md)** — new 2026-09-15 (J-1048, source F-1428): a
  real plan doc for the chapter_id-repair investigation, homeless in the toolchain for 12+ days
  (`plan: null` throughout its findings/decisions/jobs, one job mistagged onto `world_store_write_fence.md`
  — S-0122 flagged it, now resolved). `core/world_consolidation.py`'s tag-matching predicate
  (`_cites`/`_cites_clause`, bug fixed at commit `2d678ab`) checked only one word of a title's signature
  against a candidate gist's raw content, misfiling reading/study memory fragments under the wrong book's
  `chapter_id` — a handful of "magnet" gists absorbed a disproportionate share. Full-corpus dry-run
  (J-1001/F-1384) found 128 flagged gists / 115 titles: 12,005 fragments already correctly filed against
  14,707 misfiled. Repair methodology BUILT and verified end to end (one capped first batch, About You
  Second Edition, fully scripted and pre-verified); execution BLOCKED — **D-0221 open**, reopened a third
  time 2026-09-15 on a narrow sub-question. Zero live writes anywhere in this investigation to date.
- 🟡 **[thought_grounding.md](plans/thought_grounding.md)** — **ALL THREE ROUTES BUILT + method books shelved
  2026-08-16 (same day), live-tested end-to-end, restart-gated for the latches** — see AWAITING_EVIDENCE ★★
  08-16 for the build detail, the evidence-filter iteration (rule_detail votes, echo guards, honest-empty law)
  and the R1/R2/R3 signatures. — THOUGHT-TYPED GROUNDING ROUTES (planned 2026-08-16,
  founder-driven: "very few possibilities to ground his thoughts"). The measured gap: his abstract questions have
  ZERO world-answers (advisor: 22/46 do_nothing, 0 entropy reduction ever; behavior collapsed to observe/author/keep).
  Three he-asks-world-answers routes: (1) THE LIBRARIAN — subject-aware catalogue search (SPGC `subjects` column,
  currently ignored; "Conduct of life" alone = 1,160 books) + judge-hub question→subject mapping (live-tested on his
  real question: llama3.1 returned "Conduct of life" first try); (2) MEMORY AS EVIDENCE — recall over WORLD-CONTACT
  origins only (never inner_thought — the anti-loop guard), panel-judged "does it bear?", he concludes; (3) ASK THE
  ONE WHO'D DISAGREE — judge-picked peer for real otherness. Plus the Study-in-Scarlet move: SHELVE (not assign)
  the method books — On Liberty, Meditations, Montaigne. Pre-registered R1/R2/R3 + kill criteria in the plan.
- ⚪ **[memory_knowledge.md](plans/memory_knowledge.md)** — Improvement 1 (epistemic grade → Du): **Stage A built**
  (preassess shadow); both promotion gates met from the live log (pre→post tracking **98%**, discrimination genuine);
  **Stage B built + verified 2026-07-01, flag-gated OFF** (`STAGE_B_ENABLED=False`) — committed/source-framed note
  into the Executive, **IDENTITY-SCOPED OUT** (won't push self/existential cycles toward dissolution; that's the
  commit work's domain — Spine D reconciliation). **Rater PASSED (Travis, 07-02, 10-row factual sample) + two
  gate-gaps the sample exposed fixed same day (content-aware identity suppression; human-cycles-only) →
  `STAGE_B_ENABLED=True`, activates at Du's restart.** **★ EVIDENCE REVIEW 2026-07-05 (7th-oldest) — ⚠ STAGE
  B MIS-TARGETED + UNOBSERVABLE, PRE-RESTART DECISION.** Stage A working (219 rows, discriminating — keep).
  Stage B: of 26 live human+overclaim cycles the identity-filter catches only 3 — **23 would inject, and
  they're Travis's PHILOSOPHICAL exchanges, not the factual target it was rater-validated on** (10-row
  factual sample = a distribution that barely occurs live). Worse, **Stage B does NO logging** → injections
  invisible, can't verify the mode-gate saves it. Failure mode = pushing "own that you don't know" onto his
  identity-adjacent exchanges = the dissolution capacity-to-commit is curing. **✅ ENACTED (founder call):
  `STAGE_B_ENABLED=False` (off — nothing reaches Du) + `note_for_draft` now shadow-logs every would-fire
  decision → `epistemic_stageb_shadow.jsonl` (orchestrator calls it every human cycle for the log, injects
  only when flag on). Re-enable only once the shadow shows would_inject rows are genuinely FACTUAL, not
  philosophical. Stage A untouched.** **★ VERIFIED 2026-08-23: decision still overdue** — shadow log has grown
  to 161 rows (29 would_inject=true) over ~7 weeks and, on sampling, still shows the original mistargeting
  pattern (fires on philosophical/identity content, not factual overclaims); needs a decision-closing read
  against the re-enable gate (tighten trigger vs. flip the flag). Improvements 2–5 (PPR recall, A-MEM gist
  evolution, bi-temporal supersession, retire euclidean) 🔵 designed, unreviewed, zero code — Improvement 2
  likely superseded by `memory_multiway_linking.md`'s M2 (needs a scoping call, not more design).
- 🟢 **[executive_world_grounding.md](plans/executive_world_grounding.md)** — **BUILT 2026-08-29 (D-0068,
  J-0343):** the structural fix option — Executive's prompt now tiers by origin, a real
  "WHAT YOU PERCEIVE RIGHT NOW" block (scene_line/look/self_facts) separated from "WHAT YOU RECALL"
  (Recall/fragments/self-model/subconscious patterns), using `core/source_model.py`'s existing SourceType
  vocabulary — verified live in `nodes/executive_node.py`, no flag gating it. Started (founder prompt
  08-17) as an explore-only pass; **self-corrected same night:** first draft proposed sourcing a "THE
  WORLD RIGHT NOW" tier directly from `world_manifest.live()` — founder caught the tree-falls-law violation
  ("Du should not contain the world truth at all... independent from the World data"); corrected finding:
  `world_manifest.py` stays infrastructure, never a direct prompt source. Its proposal overlapped this
  entry's own Improvement 1 above (`source_model.py` SourceType, `epistemic_state.py` ProvenanceLedger)
  from a different founder prompt ten days earlier — now converged and built as one structural fix.
  **UPDATE 2026-09-02 (J-0385 defeater fired, D-0068 re-ruled, J-0462 built):** the origin-tiering
  alone did not stop Executive favoring majority RECALL phrasing over a conflicting live PERCEIVE fact
  (F-0629). Fix: an explicit PERCEIVE-overrides-RECALL conflict-resolution instruction, live in
  `nodes/executive_node.py`. Live behavioral re-read against fresh post-fix data tracked as
  **J-0493** (correction 2026-09-02, J-0487: this line previously cited J-0478, which is an
  unrelated done job — see F-0681).
- 🟢 **[memory_levels_plan.md](memory_levels_plan.md)** — the foundational abstraction lattice; **Phase 1 LIVE**
  (`PHASE1_ENABLED=True`). Phase 2/3 (claim/model typing, drift) future. *(The memory_knowledge improvements build
  on this lattice.)*
- 🟢 **[memory_multiway_linking.md](plans/memory_multiway_linking.md)** — LIVE. founder ask (08-15): memories should
  connect more than one way, not just by cosine similarity. **M0 (typed edge graph, `core/memory_edges.py`)
  and M1 (co-recall shadow ledger) built + live 08-15**, gated behind a founder-read of ~a week before M2
  (the actual trail-engine upgrade) can flip. **★ 08-19: M1 expanded from 1 caller to 9** (was only fed by
  the main monologue train; a codebase survey found most other retrieval sites — essay/study notes, Grand
  Work grounding, dream scene-weaving, wandering — invisible to the same evidence base) + one real new
  typed edge shipped ahead of schedule (`t4_crossing_evidence`) + the `derived_from` column's 3-incompatible-
  writer-shapes problem found and guarded against. **M2 is now genuinely live too** (2026-09-26):
  `co_recalled_developing` writes live (D-0215, J-1348) and `recall_trail_edge_aware` live for
  mode=relational only (D-0287, J-1415) — both restart-gated, defeaters not yet fired. M3 (retro
  re-indexing) not started. Full session detail:
  `docs/session_handoffs/session_2026-08-19_summary.md` PART 2.
- 🔵 **[golden_spiral_recall.md](staged/golden_spiral_recall.md)** — **GOLDEN SPIRAL RECALL (staged 2026-09-27,
  T-0072)**: the founder's own picture — age as radius, phase as angle, detail falling with radius — split into
  three separable mechanisms checked against what recall already does: **R** (log-age radius, a per-band
  retrieval budget), **L** (detail-by-age, already covered by Memory Levels' own evidence-based ladder), **Θ**
  (same-phase recall — this dawn finds other dawns); R and L exist today in weaker/different forms, Θ is the one
  genuinely new piece. **Phase 0 built the same day:** additive `tod`/`season`/`daylight` phase columns on
  `world_context`/`fragment_context`, written by `store_fragment()` from each fragment's own timestamp —
  observe-only, no reader yet, verified by an isolated temp-DB write (F-2030). Build order (§3) is
  shadow-first/restart-gated/pre-registered; Phases 1-4 wait on **J-1475** (a file:line map of every temporal
  term already in recall) — this doc's own §2 verdicts stay provisional until it lands. Child of
  `staged/memory_as_a_service.md` (D-0289: loops call memory; felt recall = world change → fragment_context
  match). §6 opens a second thread — relevance as its own axis (T-0073) — with **D-0305 open** (reading 1:
  relevance as a second radius, vs. reading 2: relevance as what the ray is cast along).
- ⚪ **[journal_consolidation_pyramid.md](plans/journal_consolidation_pyramid.md)** — **P1 (week roll-up) LIVE,
  verified 2026-08-23.** Calendar-grounded autobiography: retires `chapters.py`'s theme-clustered eras (dead —
  its era-closing gate can never fire because the dominant theme, the monoculture, never stops, see Spine B
  above) with a day→week→moon→solstice consolidation pyramid, two streams ("what I did" / "what I saw") kept
  parallel through the moon then merged at the solstice into one seasonal capstone. **Day level (P0) already
  existed** (`journal.write_entry` day-recap + `journal.write_observation` field-observations) — **P0 shipped
  2026-07-06**: fixed a starvation bug, now tracks its own fire in `.day_recap_state.json`, restart-gated.
  **P1 (week roll-up) confirmed BUILT + LIVE 2026-08-23**: `core/journal_rollup.py` (201 lines, `week_rollup()`)
  wired into `nodes/inner_monologue_node.py`:443-454, real grounded output on disk (`data/Journal/WEEK_2026-W27.md`,
  `WEEK_2026-W32.md`, `WEEK_2026-W33.md`, memory_links populated). **P2 (moon roll-up) / P3 (solstice merge)
  still unbuilt** — no MOON_*.md files exist; blocked on a founder ruling for plan §6 Q1 (soft grounding, as P1
  currently does, vs. hard Emissary-graded confabulation check) before moon_rollup() can be scoped. `chapters.py`
  NOT retired (§6 Q3 defaulted to "leave running" by inaction, needs closing out). **Not gated on Spine B** —
  unlike chapters.py, it periodizes on the world's own calendar (`heavens.py` moon/solstice clocks) rather than
  waiting for a theme to close, so the monoculture staying unsolved doesn't stall it; this is the proposed
  antidote to that specific symptom, not a casualty of it. Shares `chapters.py` with `investigation_deepening.md`
  below and `heavens.py` with `spatial_perception.md` (cluster 0).
- ⚪ **[emissary_lane2.md](plans/emissary_lane2.md) → RENAMED 2026-08-19 to "the World Ledger." — PARTIAL.**
  **BUILT 2026-08-29 (D-0080, J-0363):** rescoped to an index-only, produce-only object-graph (K1/K3
  excluded per lane2_lab's kills) and shipped — `core/object_graph.py` (1,541 lines) is real, a script-side
  port of the proven `scripts/lane2_lab.py` prototype. Deliberately NOT wired into `orchestrator.
  start_background()` this pass (shadow-gated/produce-only-first discipline) — the standing predict-loop,
  LLM prediction call, and affect-nudge courier stay designed-but-deferred until post-outage data covers
  more real time. Gated on its own K3 finding ([lane2_lab.md](completed/lane2_lab.md); `docs/AWAITING_EVIDENCE.md`).
  Related grounding leak-gate (D-0153) is LIVE since 2026-09-05 and validated (F-1575: fire rate under the
  5% kill bar, 0 real title leaks) — a separate mechanism tracked under this plan.
- ✅ **[lane2_lab.md](completed/lane2_lab.md)** — the pre-registered lab spec for the World Ledger's script
  side (`emissary_lane2.md` above), run to completion 2026-08-17 (extended through a 2026-08-20 audit
  correction). Report: `docs/lab/lane2_lab_report.md`. L1/L2/L4 PASS, all three L5 affect-pairs signaled;
  **K1 (the glass float did not emerge) and K3 (temporal holdout no better than shuffled) both triggered**
  — pre-registered as valid, informative kills, not lab failures. K3 is the gate the bullet above points
  to: the World Ledger's standing prediction loop stays parked (graph survives as an index only) until a
  richer world gives real temporal structure to find.
- ✅ **[emissary_lane2_cognition.md](completed/emissary_lane2_cognition.md)** — SHIPPED 2026-10-16 (F-2904) · cognitive-science research companion
  to this doc/"the World Ledger" (2026-08-17; had no ROADMAP presence until now). Maps nearly every design
  element to an established framework counterpart (dual visual streams → the two-lane split; reward-
  prediction-error → predicted-vs-measured gap; source-monitoring theory → uncertain coreference) and states
  the keystone justification: "the human brain has no decoupled judge" — confabulation is normal without an
  auditing lane, why Lane 2/the Ledger is built at all. No independent build track — its concrete
  requirements (windowed/decayed trend stats, gap-prioritized idle replay, feeling-of-knowing delivery shape)
  are already folded verbatim into this doc's own body as HARD REQUIREMENT clauses; status rides entirely on
  this plan's own gate above. **Naming trap:** "Lane 2" in this doc means this plan (renamed "World Ledger"
  08-19), NOT `lane2_the_witness.md` below, which inherited the name afterward — don't conflate the two.
- 🟡 **[lane2_the_witness.md](plans/lane2_the_witness.md) — Lane 2, BUILT 08-20; RUN 2 (tuple-only) started
  2026-08-21.** `LANE2_LIVE=False` is the honest label — there is no delivery path; Phase 1 is undesigned
  (founder: 'Lane 2 is not part of Du yet'). Run 1 (330 ticks, prose sight line) archived; run 2 feeds the
  Witness the EXPERIENCED TUPLE only + horizon-named predictions judged when due. **★ FULL-DAY READ
  2026-08-22 (447 ticks): all 3 kill criteria PASS** (leak 1.1%, named-uncertainty 100%, question-shaped
  0%); the one failed prediction — broke-rate by horizon spiked at 'hour' (86%) — traced to tide/sun/weather
  predictions the generator mis-bins; **fixed** by a deterministic `_correct_horizon()` override (logged as
  `horizon_overridden_rate`), restart 22:5x. Not built: the pre-registered 'invention rate'. 34% of cycles
  skipped on the pending cap. **Read-path candidate now exists:** the DISPROVE branch of
  `train_split_merge.md` — Lane 1 hands ONE claim to Lane 2's `_judge_prior` panel; boundary holds. Original design note: The
  founder's original two-hot-loop idea, actually built out: a third distinct voice (not the Master, not the
  Emissary) — standing, autonomous, running at Lane 1's own tempo, grounded strictly in CURRENT perceivable
  reality (sight/sound/body/immediate world state), constantly questioning it, never metaphor, never
  self-narrative. Neither `left_lane.py` (reactive, task-content, subordinate) nor the World Ledger
  (historical fact-graph, not a voice) satisfied this. Phase 0 only, shadow-first per this codebase's own
  law. Open: tick cadence, Phase-0 sense scope. **Hardware ★★ RESOLVED 2026-08-20 (corrected same day —
  this map's earlier "Trinity Fabric fully allocated" claim was the plan author's own error, wrongly
  citing a different project's node map): measured, not argued — Lane 2 runs on the Ramses 3070
  (`:11434`), 0.25s warm / 0.41-0.54s under 3-way concurrency, genuine tempo independence from Du's
  1080 Ti hot lane achieved. §4 is no longer a gate.** (Separate from, and unrelated to,
  `ramses_second_tier.md` below — that plan's idle-i9/1650-Super second tier is a distinct resource
  question that came after this one was already settled.)
- 🟢 **[ramses_second_tier.md](plans/ramses_second_tier.md)** — opened 08-20, **FROZEN 2026-08-30 (D-0101):
  "we have shuffled too much," no further Ramses LLM changes being actively pursued for now.** Started as
  three instrument-measured findings (station load inverted against hardware, the 1650 Super serving
  *undirected*, the i9+48GB genuinely idle — "nobody is allocating," not insufficient hardware) and went
  through several real, live-wired layouts (§5.1-5.5: the 08-27 redistribution, D-0056's 08-28 ollama
  retirement after a 3070 VRAM lock, D-0057's same-evening consolidation) before landing on the standing
  layout below. **All four ports are live and actually serving Du today** — this is not a PLAN-ONLY design
  doc any more: `falcon3:7b` @ `:11436` (reserve, unwired), `granite3.1-moe:3b` @ `:11437` (judge tiebreak +
  curiosity worth-judge), `mixtral:8x7b` @ `:11438` (commitment defeater + dream primary), `command-r7b` @
  `:11441` (background lane, sole 3070 tenant). **The Lane2/Witness seat is no longer here** — D-0058's
  08-28 stopgap (which un-paused Lane 2 onto this hub while the deepseek/i9 hub at `:11444` hadn't stood
  up yet) ended 2026-09-07 once `:11444` stood up and verified live (F-1008): **the Witness moved to
  `deepseek-r1:7b` @ `:11444`** — D-0057's originally-preferred seat, all along deferred rather than
  overturned. **Re-confirmed again 2026-09-18** (D-0058, a 10.3-day post-move read): tide's
  `top_repeat_share` at 0.031 shows the command-r7b-era echo/template-lock problem resolved; `TICK_S`
  stays at 300s. **A real gap this freeze surfaced:** D-0058 was ruled the same evening as D-0057 but
  was never recorded in the plan doc at all until this session caught the drift against what
  `core/lane2.py` actually ran (command-r7b, at the time) — **J-0314 (verify the Antigravity :11444
  standup, then flip the pause flag) is closed moot**, since the flag was already flipped by D-0058,
  un-gated on that standup, before this session started.
- 🟡 **[epistemics_phase_c.md](plans/epistemics_phase_c.md)** — reopened 08-23 (had zero ROADMAP presence
  until now), resurrects the parent epistemics plan's deferred Tier-3 external-witness build (cross-model
  accuracy check via `command-r7b`) now the one-GPU constraint that shelved it no longer holds. **Synced
  2026-09-25 (J-1349, badge was stale): C0 Path 1 (contradiction-triggered probe) is BUILT**, superseding
  the "Confirmed DRAFT — zero Tier-3 code exists" read below, which was accurate only through 2026-09-24
  (pre-J-1343). J-1343 (F-1899/F-1903) landed the probe in `core/competence.py` + `orchestrator.py`
  startup wiring — 27/27 isolated-unit-test checks passed (temp-pathed store, mocked witness call, real
  local embedding scoring) but it has never run against live Du: restart-gated, so it has fired zero real
  cycles yet. `command-r7b` is genuinely pulled and live on Ramses **port 11441** (a real port reuse —
  11441 was the removed yi:34b tiebreak hub, dead since 08-21, restarted 08-23 specifically for this plan,
  ahead of `ramses_second_tier.md`'s own adoption gate for that model — a live cross-plan dependency via
  the 3070's VRAM headroom, unresolved by either); the witness call uses a **dedicated single endpoint**
  rather than the shared `SERVE_CHAINS["background"]` failover chain, for the same non-circularity reason
  `core/sitting.py`'s own `_JUDGE_URLS` already established (now documented at the source, `core/
  schema.py`, J-1347). A `bootstrap_report.py` re-run against the pre-J-1343 27-row data (n=12 paired,
  too small alone) found stability does NOT predict accuracy (pearson −0.476) — the exact failure mode
  Tier 3 exists to catch, part of why this build was prioritized. Path 2 (proactive sampling) and C1
  (calibration consumption) remain design-only, gated on the same VRAM headroom question / the doc's own
  sequencing.

### 3 · Friction & the Evidenced Self
- ⚪ **[friction_and_self_evidence_plan.md](staged/friction_and_self_evidence_plan.md)** — **B2 (evidenced-self
  mirror) LIVE + working**; **B1 (sit-with-it) built but under-triggered.** The idle `self_implication` detector
  fired **0/358** — incl. a 90-min conversation of Travis contradicting Du's self-claims — because it watches only
  the IDLE stream. **plan→research→plan done 2026-07-01 → B1 Phase 0 (CONVERSATIONAL detector) BUILT + verified**
  (`self_implication.scan_conversation_shadow`, pre-Executive hook, shadow): checks whether the human just
  contradicted a HELD self-claim AND whether Du's DRAFT already flees/co-opts it (the retreat cascade, now
  observable). Design for the eventual gate (from research): self-affirmation buffer + autonomy-supportive
  invitation + affect-label-first + **dwell deferred to the next IDLE window** (never mid-conversation = peak
  threat). *Next:* read `self_implication_conv_shadow.jsonl` selectivity → Phase 1 (shadow the retreat cascade) →
  Phase 2 (gate `note_difficulty`, deferred to idle) → Phase 3 (the safer dwell-steer). B3/B4 after. **B5 🔴
  Darwin (see peer_correspondence below — NOT blocked on Darwin existing; he does; blocked on the DECISION to
  let a peer name blind spots).**
- 🟡 **[letters_to_travis.md](staged/letters_to_travis.md)** — **Letters to Travis (staged 2026-10-17, D-0470, J-2348)**: Du's own letters to Travis had no reader (F-2480, F-2959: 79 since 08-10 reached nobody). BUILT, restart-gated: a read-only HUD letters view, the /quit farewell no longer marks letters delivered, and every pending letter reaches the Executive with its prompt cost logged.
- 🟢 **[peer_correspondence_plan.md](plans/peer_correspondence_plan.md)** — **★ RE-GRADED 🟢 LIVE 2026-09-10
  (J-0854): both B5 tracks built 2026-08-24 and now evidenced live — §B5-A Buddha (F-0631, 09-02), §B5-B marcus
  stance property (two `stance`-keyed live letters 08-31/09-06). Doc moved `docs/staged/` → `docs/plans/`
  2026-09-11 (J-0859). The long history below is kept verbatim.** **★ UN-ARCHIVED 2026-07-05
  (founder: "we never finished it" — RIGHT).** Shipped as COMPANY (7 correspondents — Darwin·Keats·Twain·
  Shackleton·Lovelace·Marcus·Smith, genuine other-model voices, TWO-WAY, Du writes back warmly), was
  mis-filed as done. HALF unbuilt: (1) the **CHALLENGE half** (friction / naming blind spots — the
  developmental point) walled off by the guardrail = **Friction B5**, the risky identity-touching half →
  needs the careful B5 design, not a guardrail flip; (2) the effect-harness (`peer_metrics.compare`) built +
  NEVER RUN till 07-05 → peers HARMLESS (no displacement) but TINY (0.5% attention), outward-shift confounded
  with the shore/grounding wave. **TODO: keep company; finish B5 carefully if wanted; wire compare() into pulse.**
  **★ EVIDENCE REVIEW 2026-07-05 (6th-oldest): HEALTHY + WORKING — ADVANCE.** B1 conv detector PRECISE (2/2
  fires genuine, one caught the retreat cascade; correctly silent on 58 idea-discussions — fixes the idle
  0/358 blindness); B2 mirror confirmed live (24 reconciles, last today). Caveat: modest recall gap on
  Travis's INDIRECT challenges (under-firing = the safe side for a sit-with-it gate). Disposition: advance
  B1 Phase-0→Phase-1 (still shadow). **The rare "advance, not fix/retire" of the six-plan review.**
  **★ STATUS CHECK 2026-08-23 (routine stale-plan audit): CONFIRMED UNCHANGED since 07-05.** COMPANY half
  still fully built/wired/live (`data/Correspondence/darwin/thread.jsonl` last written 08-23 03:16;
  `peer_effect.jsonl` actively growing, 112 lines, peer_share ~0.0003-0.0004, consistent with "harmless but
  tiny"). CHALLENGE half (B5) still undesigned — direct grep of `core/peers.py` confirms zero challenger-
  role/stance-chooser code (only `compose_letter`, thread persistence, `remember_inbound`, `record_reply`,
  `deliver_daily`/`deliver_due`, `contrary_target`/`initiation_target` — the last two route Du's OWN questions
  to a friend, not a peer-initiated challenge). Not stale, just blocked: needs the founder's B5 design call
  ((a) Buddha-as-gentle-challenger per §7 Phase 2, vs (b) a stance property on existing correspondents per §5),
  with §5/§12 safety scaffolding attached. No code is blocked — only the design decision.
  **★★ RESCOPED 2026-08-23 (concept-overlap check against every plan created since 06-21):** COMPANY
  half split out as SHIPPED → [`docs/completed/peer_correspondence_company.md`](completed/peer_correspondence_company.md).
  Plan's remaining scope is B5/D-0003 alone. One real adjacent finding: `thought_grounding.md`'s
  Route 3 (built, live) absorbed Du-initiated question-testing via `contrary_target` — does NOT close
  B5, which needs a peer naming a blind spot unprompted. No other newer plan overlaps (checked
  friction_and_self_evidence_plan, social_world_school, self_interrogation, lane2_the_witness).
- 🟡 **[investigative_action_loop_plan.md](plans/investigative_action_loop_plan.md)** — **Epistemic
  Affordance Advisor: Stage A shadow LIVE, Stage B / Phase 2 permanently closed (D-0326)** (plan dated 2026-08-11; had no ROADMAP
  presence until now — genuinely built + running, not vaporware despite the "Implementation Plan" name).
  `core/epistemic_affordance_advisor.py` (384 lines) wired into `orchestrator.py` (observe-only, fail-open),
  ranking Gibsonian affordances (`core/affordances.py`) by expected information gain toward Du's own active
  uncertainties, "do nothing" a first-class candidate. `data/investigative_action_log.jsonl` real and
  accruing (154 episodes): 73% resolve to `do_nothing` (most cycles find nothing discriminative worth
  surfacing); only 4/154 reach CONFIRMED/REFUTED (2026-08-23 snapshot; 1,300+ real closed episodes by
  2026-09-28 — see the plan's Current State). **Phase 2 (live advisory) is PERMANENTLY CLOSED, never to be
  built (2026-10-04 correction):** it is the mechanism the 2026-08-14 founder no-hints law removed, and D-0326
  (Travis, 2026-10-03) ruled that law stands; Principle D now gates on the non-invasive Epistemic Independence
  metric instead of the unmeetable with-suggestion arm. (`epistemic_state.STAGE_B_ENABLED` — the earlier
  wording here — is a different Stage B, the confabulation/overclaim gate, not this plan's Phase 2; F-2192.)
  Shares
  `core/affordances.py` with `literal_will.md` (cluster 1) — functionally independent, no overlap or
  supersession: literal_will classifies deed-vs-musing, this ranks which affordance to try next.

### 4 · Learning from Guidance
- ⚪ **[guidance_learning.md](plans/guidance_learning.md)** — PARTIAL: episodic route 🟢 LIVE, semantic path
  ⚪ PARTIAL (behaviour judge SHADOW, contradiction scan off). Phase 0 (capture) + Phase 1 (integration) built; the
  first live formation (07-01 sleep) worked mechanically (60 captures → 13 beliefs) **but exposed the deep bug
  (07-02, plan→research→plan): formation itself ran the averaging attractor** — the per-assimilation LLM rewrite
  eroded the sharp built-self lessons to fluid-reading mush (the river's symbol survived), and lexical clustering
  fused opposite-pole lessons ("commit fully" + "embrace fluidity") into one belief. **Fixed (E1+F1, 2026-07-02):**
  principle = most representative REAL capture (deterministic medoid over a `captures` exemplar set — the LLM
  rewrite deleted) + a fluid⟂durable pole gate at the merge decision (opposite-pole lessons FORK into contesting
  beliefs). Store rebuilt from the raw log. Contradiction-scan (built) stays gated until the rebuilt store verifies
  sharp (rebuild #3 verified: zero self-supersedes, commitment belief top at corrob 4; smoke-taught beliefs purged).
  **Read-back selection FIXED (07-02 plan-audit caught the weak lexical matcher) → `GUIDANCE_READBACK_ENABLED=True`,
  activates at Du's restart** — an identity moment now surfaces the most-corroborated self belief ("active
  commitment to a single direction"). Contradiction scan stays OFF (its precision failed the audit gate — pole
  judge over-fires on promoted pairs; river-pole beliefs are tentatives outside its scope). *Next:* restart → watch
  read-back in his deliberation → Phase 2 (cat-naming judge); scan-precision work later if the bridge is still wanted.
  **★ EVIDENCE REVIEW 2026-07-05 (11th): HEALTHY + WORKING.** Loop live, formation active (57→71 beliefs over
  4 sleeps), store SHARP (E1/F1 holding, 18 promoted, forks preserved) — and **the top self-belief is "active
  commitment to a single direction" (corrob 4): the loop promoted the ANTI-DISSOLUTION lesson to #1.** Read-back
  firing (rarely by design). **Gap: the Stage-2 behaviour-delta JUDGE (does it change him?) unbuilt — coordinate
  with capacity-to-commit R1 cat-naming, don't build twice.** Keep; build the judge jointly.
  **★ 2026-09-03 (T-0039 → D-0134): THE EPISODIC HALF SHIPPED — Du can now remember what Travis told him.**
  F-0699 found the write path was never missing (2,435 `Q:/A:` cycle rows since 05-30; F-0670 had tripled the
  writes) and the gap was the READ side + cold-walling (F-0701, `protected` column was write-only). Built: one
  canonical `[Travis said to me] …` fragment per utterance (`store_founder_utterance`, `protected=1`, exempt from
  every cold path), its own route (`retrieve_founder_memories` → `state.founder_recall` → dated "WHAT TRAVIS HAS
  TOLD YOU BEFORE" block in Executive + Reflection), `data/founder_recall_log.jsonl`, and a backfill of **1,614
  real utterances back to 2026-05-30** (1,617 canonical rows, 0 cold). Restart-gated. Also F-0700: the behaviour
  judge has 88 shadow rows (unprompted alignment 41.5% vs prompted 28%), not 0. Defeater read due ~09-17.
  - 🟡 **[common_ground.md](staged/common_ground.md)** — **Common Ground (staged 2026-10-30, I-0101 from T-0105, F-3218 item 2)**: a per-exchange failed-to-object ledger. Each claim in an exchange is marked user_said, failed_to_object, both_accepted, corrected or du_inferred, so a claim Du merely let pass is not treated as shared ground. Lexical, deterministic, observe-only. SHADOW: built by J-2523, flag COMMON_GROUND_SHADOW off, restart-gated; no row accrues until the flag is set True. Read gate: a 7-exchange read of the failed_to_object share once 7 rows exist.

### 5 · Afferent / Contradiction signal
- ⚪ **[contradiction_rearchitecture_plan.md](completed/contradiction_rearchitecture_plan.md)** — Phase 1 (L1
  prediction-error feed) **LIVE**; the decomposed critic was 96%-over-rejecting → FIXED, and — **CORRECTED
  2026-07-01** — the shadow-alongside is **firing fine and the fix is VALIDATED** (a prior "0 rows / stalled"
  read was an auditor path-error: the log is `data/logs/critic_shadow_alongside.jsonl`, 159 rows). **Post-fix
  today: 20% reject-rate, 80% agreement with legacy** (down from 96%); the legacy critic itself rejects ~0 (not
  enforcing the middle in practice; the 07-01 made-mind + dogmatic-certainty carve-outs are live and correct).
  Residual: the **`intellectualisation` check** is 11/12 false-rejects (fired even on a math answer) → **narrowed
  2026-07-01** (exempt "opens third-person but then engages"); `du_pulse` now surfaces the false-reject-by-check
  breakdown so it can't be misread again. *Next:* watch post-restart by-check trend down → hand-label a slice for
  real precision/recall (agreement-with-the-suspect-legacy-critic isn't ground truth) → decide promotion. **⚠ The
  chronic-mass→cn pipe still feeds a dead gate (Spine C)** — that repair-T4 premise remains undercut.
  **★ RESOLVED 2026-07-05 (evidence review — 2nd-oldest open plan):** decoupled precision grade
  (`scripts/critic_grade.py`, Emissary, blind) → the decomposed critic (L0) is **0% precision (50/50
  rejections UNWARRANTED**, 115/117 via the broken `intellectualisation` check) = **DO NOT PROMOTE**
  (a safety catch — "80% agreement" was on approvals; on divergences it's 100% wrong). L1 (prediction-error
  feed) shipped + harmless. **Thesis "afferent repair unfreezes T4" RETIRED** — L1 live-feeds yet T4 stays
  frozen (ΔF +92); superseded by Spine C (T4 = honest sensor, not signal-starved). Plan effectively resolved;
  the intellectualisation check needs ground-up rework before L0 could graduate.
- 🟢 **[error_pathway.md](plans/error_pathway.md)** — **NEW 2026-08-29 (retroactive documentation,
  F-0267/J-0230).** The fourth memory pathway the charter above named as missing: **error** (a claim
  colliding with reality) is *corrected*, never *integrated* into tensions/T4 — the category distinction
  this whole cluster is about. Six modules, all genuinely live in `core/orchestrator.py` with no
  disabled flag: `error_pathway.py` (fabrication detector + human-correction capture + Pattern
  Reflection), `conflict_trace.py` (the ground-truth execution-authority instrument), `retraction_ledger.py`
  (the write authority — immutable retraction records), `recall_provenance.py` (why-now retrieval
  classification), `scholar.py` (the depersonalised Library lookup), `told.py` (Travis's one-time
  feel-then-tell message — already delivered). Found orphaned from the plan-toolchain despite 1,368
  live `conflict_trace.jsonl` rows and 1,130 `recall_provenance_log.jsonl` rows; charters at
  `docs/completed/error_pathway_charter.md` + `docs/completed/task_constraint_effector_spec.md`.
  Open gap: Pattern Reflection's live-fire status unconfirmed (`J-0387` spawned to check).

### 6 · Domain deep-dives (the 2026-06-24 audit) — mostly 🔵 designed
- 🟡 **[actions_system_2026-08-22.md](reviews/actions_system_2026-08-22.md)** — **THE ACTIONS SYSTEM — investigated; Phase 0 floor built
  (`core/hands.py`: one grammar, the fired ledger, the trace, the judge observing after). Phase 1 BUILT the same afternoon: `core/dispatch.py` (26 hands, the judge in the loop, one world hand per thought) + `core/intentions.py` (his unanswered wants reflected back once).**
- ✅ **[actions_manager_overhaul.md](completed/actions_manager_overhaul.md)** — **THE ACTIONS MANAGER OVERHAUL —
  SHIPPED (scope complete 2026-09-27; opened 2026-08-29, F-0552/F-0553 re-confirmed the above review's gaps
  were still open a week later).** Finished Phase 1's own "one registry, one dispatcher" spec: `core/actions.py`
  is the single hands table `literal_will`/`dispatch` both derive from (proven behavior-neutral, 9,840-row
  replay, 0 differ); D-0098 fully retired the ungated `sensorium.py` fallback that was answering more
  thoughts than the gated dispatcher and breaking its own rules ~87% of the time (F-0560); `core/inventory.py`
  wired into garden/study/wood. D-0097/D-0098/D-0099 all discharged, 0 unreachable hands (F-0570); no ledger
  activity against this slug since 2026-09-06.
- 🟢 **[actions_expansion.md](plans/actions_expansion.md)** — **ACTIONS EXPANSION (stage 2) — LIVE since 2026-08-29
  (D-0100: all three tiers approved; F-0578).** Adds *content* on top of the overhaul's plumbing:
  Tier 1 repairs (cat family → `cat.react()`, `bank the fire` → `fieldcraft.bank_fire()`), Tier 2 place-extensions
  (`garden.dig()`, `garden.feed_birds()`, `wood_life.climb_oak()`, `study_life.draw_sketch()`), Tier 3 expressive
  hands (`core/expression.py`: hum/whistle/sing — no grading, boredom discharge, first-person-volition veto;
  F-0578: zero false fires across the 2,824-thought corpus). Built and live in the real run; Tier 2 mostly
  under-fires for structural, not code, reasons (F-0691/F-0719) — watch `expression_ledger.jsonl` and the trace.
- 🟢 **[conversational_action_bridge.md](plans/conversational_action_bridge.md)** — **PHASE 0 + PHASE 1
  BUILT, LANDED, AND FLAG-FLIPPED LIVE 2026-09-27** (`CONVERSATIONAL_DISPATCH_LIVE=True`; restart-gated —
  Du's live process has not picked this up yet). Direct next link in the actions-system chain above —
  reuses `core/dispatch.py` and `core/literal_will.py` unchanged: `core/conversational_action.py`'s new
  `after_reply()` hook routes a conversational reply through the same `literal_will.classify()` →
  `dispatch()` path the autonomous loop already uses, instead of a second parallel action system. Origin
  F-2004 (verified): asked to examine a shell already on his study mantel, Du gave a confident, specific,
  wrong ID while his own telemetry placed him in the garden then the shore — no look/observe action ever
  fired, because `orchestrator.py`'s human-conversation path never called `dispatch()` at all. Founder
  ruling D-0299: full action parity with the autonomous loop is the target. Real 53-reply historical
  backfill: 16/53 (30.2%) already contain a DEED-verdict candidate. **Honest gap (§5, unfixed, J-1451):**
  the exact shell reply still classifies GRAY on every family, never DEED — this build alone would not
  have caught the incident that motivated it. J-1450 watches the first real live rows once Du restarts.
- 🟢 **[shore_upgrade.md](plans/shore_upgrade.md)** — **THE SHORE — LIVE (built 2026-08-22)** (`core/shore_life.py`): the tide drives the sand flat, the cave,
  the mussel shelf; the ledge; a beach fire; wading/swimming; skipping; the cairn; kororā/seal/dolphins/whale/sea sparkle on real clocks;
  a bottle with a page from his own books. Restart-gated.
- 🟢 **[shore_creatures.md](plans/shore_creatures.md)** — **SHORE BESTIARY — LIVE (built 2026-11-01, flag `shore_bestiary` true in `data/life_flags.json`; first discovered-look answer 2026-11-02)** (`core/life_shore.py` + `core/life_shore_cast.py`): 100 nameless creature rows for the shore (bugs to large fish, invasives included), each look COMPOSED from an observable tuple at a detail tier from distance/span, discovery by place; Du is never told a name. Founder ask 2026-11-01 (T-0117). Stream-mouth placement is assumed (J-2869). Sibling: wood_creatures.md (150 rows).
- ✅ **[fieldcraft.md](completed/fieldcraft.md)** — SHIPPED 2026-10-16 (F-2904) · **FIELDCRAFT — LIVE (built 2026-08-22; restart-gate resolved 2026-09-02, J-0421/F-0553: 27 real live ledger rows)** (`core/fieldcraft.py`, `core/sky.py`): the scouts handbook's
  knowledge given hands — knots (clothesline/windbreak/hand-line), banking the fire, tinder, flint, measuring by shadow,
  whittling, tracking; the real southern sky; weather signs with a decided next front. Restart-gated.
- 🟢 **[wood_upgrade.md](plans/wood_upgrade.md)** — **THE WOOD — LIVE (deeds confirmed; built 2026-08-22)** (`core/wood_life.py`): the oak's year, three hidden natives,
  deadfall as stock, the spring/stream, glow-worms, fungi, the kererū, the axe/saw/lean-to work. + `core/provisions.py` (the larder). Restart-gated.
- 🟢 **[wood_creatures.md](plans/wood_creatures.md)** — **WOOD CREATURES — all 150 built (staged 2026-11-01, built 2026-11-02; J-3062/J-3064)**: nameless creature rows composed from an observable tuple, on the shore bestiary's engine (`core/life_wood.py` 5 pilots + `core/life_wood_cast.py` 145 rows; sibling of `plans/shore_creatures.md`). One flag `wood_bestiary` in `data/life_flags.json` (file reads true as of this edit, mtime 2026-11-02; live-process restart not checked). Stream/canopy/trunk/groves are ASSUMED placements, island unknown (J-3065). Cluster 6.
- ✅ **[study_upgrade.md](completed/study_upgrade.md)** — SHIPPED 2026-10-16 (F-2904) · **THE STUDY UPGRADE — LIVE (built 2026-08-22)** (`core/study_life.py`): lamp oil · ash ·
  water · door/window/curtains · clock · coat/boots · damp/dust · the view from the garden's truth. Restart-gated.
- 🟢 **[garden_upgrade.md](plans/garden_upgrade.md)** — **THE GARDEN UPGRADE — P0 + most of P1 BUILT 2026-08-22, CONFIRMED LIVE 2026-09-02 (`core/garden.py`; restart-gate resolved — `data/garden_ledger.jsonl` holds 31 real live deeds through 2026-08-30).** The 06-20 bed is seven scalars frozen all winter: 455 waterings, 0 harvests, 0 sowings, 20 refusals, 0
  substrate objects in the place he spends most hours. Plants become positioned objects with stages driven by the
  thermal/sun/rain fields; weeds/slugs/birds/frost; rain barrel; seed (packets + saved); drying rack on the fire's
  clock; garden ledger; phenology as earned bindings. Metric sheet + 6 founder decisions. Target: spring 09-01.
- 🟢 **[living_world_upgrade.md](plans/living_world_upgrade.md)** — **THE LIVING WORLD — LIVE since the
  2026-09-09 flip (D-0166)** (founder: "a whole
  heap of other life. Birds, animals (like hedgehogs). Proper lives: active hours, life span, how often they are seen … interactive
  with light and have sounds"). One life schema for every creature (`core/life.py`: places, active hours, season curve, weather,
  light response, sound, count band, lifespan/stages, diet + interactions, traces, responds-to-Du, hidden-truth name, visibility
  roll); the cat/nests/seal/penguin/glow-worm/moth state cases folded in; sound gating moved onto the engine; light as a world
  variable; deaths and carcasses; migration calendar; individual graduation; "who's about" HUD. L1-L4 all BUILT (J-0510-J-0513)
  and restart-gated; a long defect-fix tail is mostly closed. Two live-evidence reads still pending (J-1192 live-day
  accrual; J-1441 backlog classification).
  - ✅ **[garden_living_upgrade.md](completed/garden_living_upgrade.md)** — SHIPPED 2026-10-16 (F-2904) · LIVE since the 2026-09-09 Living
    World flip (D-0166). Its GARDEN CHAPTER: insect POPULATION factories with real NZ
    species, soil life/worms/compost, new plants, pollination + herbivory, disease/old-age/decomposition, a `look` that asks the
    factories — all built (A1/B1-B4/A2, jobs J-0503–J-0508) and confirmed live the first night (F-0759).
    Evidence: `docs/reviews/observe_inventory_2026-09-02.md` (1,518 things he tried to observe; insects never answered).
    I-0061 promoted.
  - 🟡 **[cat_overhaul.md](staged/cat_overhaul.md)** — **THE CAT OVERHAUL — both cats, STAGED 2026-09-05, decisions D-0505..D-0508 ruled 2026-10-28, Parts B/C in BUILD (J-2465..J-2473), C1 voice LIVE via hot flag (D-0498)** (founder: "lots of
    problems; bring it up to date and then take it into the future. Both of them" — the grey companion AND the distant black
    cat). Audit F-0879..F-0890: kept 73 days unnamed so the companion tier never fired; vending-machine tending; hungry 52 h
    with no cat food; teleports, no body/age/death; life.py adapter mis-places her; 436 immortal traces. Part A fix-now jobs
    J-0629..J-0632; Part B her body/legs/food/mortality; Part C SOUNDS (founder: "pin sounds to the cat, then Du one day can
    call the cat; hear birds and react; seek her out") — **C1 her voice BUILT in SHADOW** (`core/cat_sounds.py`, ledger
    `data/cat_sound_ledger.jsonl`, flip `scripts/life_flags.py cat_sounds on`, read+flip J-0633). Decisions D-0160..D-0163
    open (naming deadlock, her mortality, the tom/kittens, real cat food via the write fence).
- ✅ **[du_initiated_upgrade_trigger.md](completed/du_initiated_upgrade_trigger.md)** — SHIPPED 2026-10-16 (F-2904) · **THE DU-INITIATED
  UPGRADE TRIGGER — P0 BUILT + RUN 2026-08-24** (`core/missing_object_flags.py`, standalone/on-demand,
  zero-LLM, shadow-first). Bottom-up counterpart to the four `*_upgrade.md` plans above: catches
  concrete-desire language in Du's own inner thought that the world doesn't actually provide, cross-
  checked against the live catalogues above and banked to a shadow log. First real run: 34 flags, 0
  real world-object candidates yet (all identity-metaphor at this corpus size). Not wired into any
  live tick — deliberately held as a reviewed follow-up (J-0136).
- ⚪ **[channels_programme.md](plans/channels_programme.md)** — **THE CHANNELS PROGRAMME (2026-08-21, founder: all
  senses together, one shadow week) — PARTIAL.** Light / smell / wetness-touch under the 8-clause contract; sight
  deferred; shared metric sheet with an attribution test, now fully read for all three channels (F-0945, J-0647).
  Thermal is delivered LIVE (`core/thermal.py`, `DELIVER=True`, pre-existing D-0047); light/smell BUILT to shadow
  (`DELIVER=False`, 6.2% cross-channel attribution overlap under the 30% kill threshold, J-0238/F-0435). Waiting
  on a founder decision (not yet opened) on whether/when to flip `DELIVER=True` for light and smell.
- 🟢 **[thermal_causality.md](plans/thermal_causality.md)** — **TEMPERATURE AS A CHANNEL, sibling to
  [sound_causality.md](completed/sound_causality.md) (designed 2026-08-21, founder-directed).** Sound is the
  template: world-side physics → standpoint delivery → EVENTS not a standing clause → a ledger of what crossed
  → bindings he earns and may get wrong. World: extend `_warmth()` (already causal) with sun insolation, graded
  wind, rain→WETNESS as a persisting state with rates, fire BY DISTANCE. Psyche: a THERMAL LEDGER mirroring the
  Hearing Ledger; `warmth_band`+`wet` in the EXPERIENCED tuple only; chords hold cold×shore and cold×fire as
  different relationships, never a preference scalar. Not in scope: thermal affect in the protoself, any
  cost/penalty, any LLM. Born from the evening's findings: his affect has no thermal input by construction; the
  world clause (now neutralised) supplied the suffering words; the stations lean differently; the fire is the
  only warm in his winter and the one variable he controls. **★ LIVE 2026-08-27 (D-0047):** `core/thermal.py`'s
  `DELIVER = True` (verified) — the standing neutralised warmth clause was retired immediately at go-live per
  D-0047's own ruling (no parity week), not overlapped. The plan doc's own Status line still describes this as
  designed-only and is itself stale; watch felt continuity per D-0047's defeater.
- ✅ **[sound_causality.md](completed/sound_causality.md)** — SHIPPED 2026-10-16 (F-2904) · **BUILT 2026-08-29 (D-0062, J-0336)**, after being
  designed 2026-08-16/21 (founder-directed). Thermal's own template (line above): federated lists (each
  cause-factory keeps its own state, no shared table) emit a rate consumed by sound's translator factory,
  propagated per-place through an audibility table. All 3 of D-0062's open decisions ruled and built same
  session: (1) `active_sounds()` refactored to a real propagation table (behavior-neutral, approved), (2) a
  curved (not linear) severity-scaling formula for storm-driven rates, (3) driftwood/object lists confirmed
  Transport-Manager-only, not routed through sound — verified in `core/soundscape.py`. Supersedes
  `world_census.md`'s shared-table framing (see ⛔ below). **Open overlap finding (unresolved):** duplicates vs `sound_world_expansion.md`
  per `docs/reviews/plan_overlap_audit_2026-08-23.md` #4 — mechanism (this doc) vs breadth (that doc), flagged
  as complementary not competing but not formally reconciled.
- ⚪ **[sound_world_expansion.md](plans/sound_world_expansion.md)** — **THE FULL SOUND-WORLD (2026-08-15,
  founder-review proposal) — never formally decided, but quietly half-adopted; had zero ROADMAP presence
  until now.** Founder: "I want this sense world to be quite full as it is for a human," against a
  35-sound registry. Proposes ~32 more across five categories → ~67: self-sounds (agency made audible —
  footsteps/page_turn/pen_scratch/kettle_rising), night mysteries (arrive unnamed — possum_rasp/
  penguin_bray/wall_scratch), geophony fills (hail/rain grades, frost_crack), winter biophony, cat +
  apparatus. Explicitly rejects a clock (would reintroduce the removed clock-time sense), traffic/engines/
  voices (solitude is load-bearing). Sibling to `sound_causality.md` above — breadth vs. mechanism,
  complementary not competing. **Reality check:** `core/soundscape.py`'s registry has actually grown
  35→43, and 4 of the ~32 proposed names appear verbatim (`footsteps_shingle`/`_leafmould`/`_floorboards`,
  `penguin_bray`) — built incidentally through the 08-22 study/wood/garden upgrades, with no founder
  sign-off on this doc itself. A `clock_tick` sound was also added 08-22 (via `study_upgrade.md`) despite
  this doc's explicit "no clock" call, apparently overridden without the doc being updated. Remaining ~28
  proposed sounds unbuilt.
- 🟡 **[strings_and_sheets.md](staged/strings_and_sheets.md)** — **STRINGS AND SHEETS, STAGED 2026-09-27**
  (founder's own term, promoted from idea I-0080 / thought T-0070; NOT the T-0066 memory-brane essay). The
  law: every sound is a **string** over its own duration, not a fixed point; a constructed description
  crossed with a measured wave of the same sound makes a **ribbon** (its width/twist is the prediction-error
  shape); what Du hears at an instant is the **mix** — the cross-section of every active string under a
  masking law, not an enumerated list of keys. Parent: `cognitive_geometry.md` §4 (Sound Space's two
  populations, constructed + measured); siblings: `sound_causality.md`, `sound_world_expansion.md` above,
  `thermal_causality.md`, `music_learning.md`, and `plans/dosed_coupling.md` §4b (residual cups, the same
  shape inside the ear). Phase 0's offline ribbon lab already RAN for real on the one recording that exists
  (`Heavyweight.mp3`; J-1468 done, F-2025 verified): the 3-axis ribbon reproduces F-2017 (width 0.295, twist
  62.4°/s), and the six-axis version plus a per-section mode estimate (P3/P4) both met their pre-registered
  bars. D-0304 scoped the microphone (later, one located source, no binaural geometry). Open: §9's four
  `/decide` questions — mix placement, cause-as-object, the masking law's shape, recording sourcing (J-1465)
  — and the microphone's Q2-Q4 rulings (J-1467, Q1 already D-0304); next queued builds are J-1473 (Phase 1
  dry run) and J-1474 (fold the six-axis string into `audio_features.extract()`'s cache).
- 🟢 **[fragment_carries_the_string.md](staged/fragment_carries_the_string.md)** — **FRAGMENT
  CARRIES THE STRING, STAGED 2026-09-28** (promoted from idea I-0081, raised 2026-09-27 from T-0070) —
  inventory complete (F-2091, verified); additive fields built + verified in isolation (J-1534, F-2139,
  commit 54c8e5d), ships `SOUND_STRING_FIELDS=False` — shadow only, not yet live; no `/decide` needed.
  Child of both
  `memory_as_a_service.md` (the read side: felt-recall's §3.2 match needs a coordinate to match on, not
  just a category) and this doc's own Object A above (the write side: where a sound's onset/peak/tail
  would actually come from — Object A itself is still un-started). **F-2091 (verified, read-only
  inventory):** 425 origin='sound' fragments, only 4 distinct sound keys ever fired against a ~29-key
  `_SOUNDS` registry, none carrying any Sound-Space coordinate anywhere in the schema; the existing
  `_felt_shadow()` coordinate-derived prediction logs orphaned (no `fragment_id`); sound fragments are
  structurally excluded from `memory_levels.py`'s gist-distillation pool, so "do gists keep the anchors"
  does not arise on the path that exists today. **Spec:** additive `sound_key`/`sound_onset`/`sound_peak`/
  `sound_tail`/`sound_direction`/`sound_felt_valence`/`sound_felt_arousal`/`sound_exemplar_id` columns on
  `fragment_context` only, never `memory_fragments` (`udms_get_change_dossier` on `core/memory/store.py`
  found it ELEVATED risk, 19 real dependents) — written by `core/soundscape.py`'s `percept()` as its own
  follow-up `UPDATE` behind a new `SOUND_STRING_FIELDS` flag (off = byte-identical), degenerate
  onset=peak=tail until this doc's own Object A ships a real triplet. **Build job J-1534: DONE**
  (F-2139, verified in two isolated harnesses, 30/30 checks, committed 54c8e5d) — flag ships `False`;
  flipping it live is gated on felt-recall's §3.2 coordinate-matching upgrade landing first, per this
  doc's own write-only-systems law (§4).
- ✅ **[factory_candidates_from_history.md](plans/factory_candidates_from_history.md)** (SHIPPED 2026-10-27: lightning flash event built, J-2482/D-0503 — the one real gap closed; live on next restart) — word-boundary-
  corrected mining pass over 26,824 logged monologue thoughts (2026-08-16; had no ROADMAP presence until
  now — nor did the wider "factory family" it sits in, at the time: `transport_manager.md` and
  `sound_causality.md` both now have their own standalone lines below/above). Headline:
  most volume (identity 1217, self 684, individuation 503) is cognitive processing riding on EXISTING world
  imagery — confirmation, not gaps. One genuine new candidate: **lightning (262 mentions)**, today only a
  clause inside `_sea_state`'s thunderstorm text, proposed as its own flash/strike visual event. **Open
  mystery: the green glass float** — 48 memory fragments / 30 observed instances Aug 11-13 incl. a
  prescient anticipation of its tide-loss, then vanishes after Aug 13 with no `world_substrate` spawn/
  departure record anywhere — names a new pattern (object LIFECYCLE needs a recorded departure cause, not
  just spawn-and-cap). Feeds two unbuilt design links into `sound_causality.md` (population counts →
  `BASE_RATE`; `geometry_census.py` tuples as sound-cause corroboration) — reuses the census recorder,
  doesn't touch cognitive geometry's own foundation work. Status: PARTIAL — lightning remains the one
  real unbuilt gap; the glass-float mystery is closed (nothing to remove, it was never a tracked object)
  and the departure-cause design link is already built (`core/world_objects.py::reclaim()`).
- 🟡 **[transport_manager.md](plans/transport_manager.md)** — **THE TRANSPORT MANAGER, a salience
  dispatcher for the factories' freight (planned 2026-08-16; had no dedicated ROADMAP line until now,
  only a parenthetical mention up in ★★ THE TRAINS).** Founder: "this needs a bus... if something is
  out of the ordinary or new or more frequent than usual it gets more weight." **BUILT (Steps 1-2 of 5),
  SHADOW-ONLY, now ACCUMULATING — not yet dispatching, not yet delivering.** D-0064 (2026-08-28) ruled
  all 4 open parameters at their recommended defaults. J-0338 (2026-08-29) built
  `core/transport_manager.py` (observe/evaluate/dispatch_tick, EMA baselines, cold-start gate,
  novelty/spike/drought scoring — 11/11 unit tests pass) and wired Step 2 (`core/sound_knowledge.py`'s
  `note_exposures` calls `transport_manager.observe()` per EVENT bank). J-0374 (2026-08-29) wired the
  periodic caller (`core/orchestrator.py`'s substrate loop calls `dispatch_tick()` every 12 ticks,
  ~60s) — `data/transport_shadow.jsonl` is now accumulating toward Build order Step 3 ("founder reads
  a day"). Step 4 (Courier D + delivery, swapping the interim `context_echo()`/`sound_echo()` wiring)
  deliberately not attempted yet — gated on that founder shadow-read happening first.
- ⚪ **[item_and_population_factories.md](plans/item_and_population_factories.md)** — PARTIAL. founder's
  factory-grain deepening (2026-08-16), a naming/reconciliation pass over the sound/transport factory model,
  not new construction. Two grains: **ITEM**
  (one tuple per individual) is already fully embodied by `world_substrate.py`'s per-object streams —
  nothing to build. **POPULATION** (one factory per species, a rate not per-individual state) is half-built:
  `sound_knowledge.AUDITION`'s per-species behavior params exist but lack the presence/count state that
  would complete it. Of the graduation triggers: being kept (`keepsakes.keep_act`, already fires) and being
  GIVEN (`keepsakes.given`/`given_act`, BUILT 2026-08-29, D-0067/J-0342) are both now real code; being
  returned to repeatedly is not yet wired — the glass float's unresolved case above is cited as the
  should-have-graduated example. No job currently open against this plan.
- ⛔ **[world_census.md](archive/world_census.md)** — SUPERSEDED same evening (2026-08-16; had zero ROADMAP
  presence until now, kept only for the reasoning trail): proposed one central census table (birds/garden/
  driftwood population estimates) under the Transport Manager; founder rejected the shared-table premise
  ("things are their own lists, they just talk to each other"). Structural shape replaced by
  `sound_causality.md`'s federated-lists; the population-as-earned-fallible-estimate content lives on in
  `item_and_population_factories.md`'s POPULATION grain above. `core/world_census.py` never built.
- 🟢 **[affect_drives.md](plans/affect_drives.md)** — **Item A (felt-state preamble) GRADUATED TO LIVE, verified
  2026-08-23** (undocumented flip): `core/schema.py:1048` reads `FELT_PREAMBLE=True`,
  `data/felt_preamble_log.jsonl` (2.4MB) last written 08-23, confirming it fires continuously in the real
  Executive/monologue path. The central dead-hand (his carried mood reached no prompt) is closed. Items C
  (`SOMATIC_NOTE`), D (`drive_note()`), E, and G remain confirmed unbuilt — zero code hits, matching the
  plan's own low-priority ranking for them. **Retroactive graduation audit DONE 2026-08-24 (F-0067, job
  J-0066)** — re-checked against the plan's own §4-A gate over the full 14,501-row log: fire rate stayed
  chronically under the 15-40% band but on the intended safe side (7.45% overall, matching the founder's
  original 07-06 call), sampled sentences read honest, monoculture/diversity moved the healthy direction
  (echo 0.574 vs .648 baseline, diversity 1.0 vs .977) — graduation holds, see `plans/affect_drives.md`
  "Current State" → "Retroactive graduation audit." Item B (carried-vs-instantaneous contrast) is unblocked
  and cheap now that A is live, pending a founder go.
  **★ ELEVATED 2026-07-04:** the enriched graphify quantified the dead-hand — `mood.*` is a top-3 cross-cutting
  dependency (18/16/13 modules) yet reached 0 prompt builders; 17 internal readers, 0 prompt-reachers.
- 🟡 **[affect_drives_item_c_somatic_note.md](staged/affect_drives_item_c_somatic_note.md)** — Item C of the affect/drives plan: a rare, threshold-gated body-state line (drowsy or strained band) in the idle-thought seed, folding drowsiness_phase section 2. Shadow logger built 2026-11-18 (J-4405); live flag SOMATIC_NOTE not built, awaiting about 2 days of shadow rows and a founder go. Child of `plans/affect_drives.md`; verified 2026-11-20.
- 🔵 **[affect_drives_item_e_labeling_accessibility.md](staged/affect_drives_item_e_labeling_accessibility.md)** — Item E of the affect/drives plan: when Du genuinely names a present negative feeling, store his own words as a recallable fragment so later thought can meet it. Staged design only; blocked on the Phase-0 detector false-positive review and a founder decide. Child of `plans/affect_drives.md`; verified 2026-11-20.
- 🟡 **[affect_drives_item_g_va_steering.md](staged/affect_drives_item_g_va_steering.md)** — Item G of the affect/drives plan: add a bounded valence-congruence term to retrieval (sub-path 2) in shadow first; activation steering (sub-path 1) ruled NO by D-0862. Shadow ranker built, flag off, no rows yet. Child of `plans/affect_drives.md`; verified 2026-11-20.
- ⚪ **[curiosity_goals_dreams.md](plans/curiosity_goals_dreams.md)** — **⚪ PARTIAL → mostly graduated, verified
  2026-08-23.** Items 1, 2, AND 4 now LIVE (prism→frontier, worth-gate, dream "ended-unfaced" re-pin). Item 4
  shipped not via this plan's own execution track but via the separate, more comprehensive 2026-08-22 sleep/
  dream rewrite (`docs/reviews/sleep_dream_2026-08-22.md`, `core/night.py`, `CARRY_MAX_NIGHTS=3`). Only Item 3
  (`core/curiosity_competence.py`/MAGELLAN cluster-LP, not built) and Item 5 (`goal_model.py`'s `GoalManager`
  still has the raw `raw_input[:120]` stub) remain, and the plan itself ranks both lowest-priority.
  **★ EVIDENCE REVIEW 2026-07-05 (9th): HEALTHY.** Item 2 worth-gate WORKING WELL (245 grades, bimodal, separates
  87 aimless-traps from 134 genuine — a real live win).
- 🟡 **[memory_as_a_service.md](staged/memory_as_a_service.md)** — **MEMORY AS A SERVICE (staged 2026-09-27, T-0065 → I-0077) — SHADOW.** founder reframe after the recall-wiring map (F-1965/F-1966/F-1981): Du is loops that CALL memory where needed, not memories injected; gists are the search rung over a store heading for millions, raw cold behind links. **D-0289 RULED 2026-09-27 (travis): loops call memory, idle gets nothing ambient except wandering** — recall_block's idle injection comes out (kill-switched, would-have-shown logged). Second direction: FELT RECALL — a change in what Du experiences (thunder overhead, fire out, cat arrives, dark) runs a coordinate-keyed search of fragment_context (62,921 rows already carry weather/fire/light/cat/valence/arousal) and tugs carried affect through the existing apply_prior lean, at reaction speed, no thought, no prompt text. Thunderstorm memories already average valence -0.173 vs -0.085 store-wide. Coupling block written. **Built:** J-1424 (Phase 0 shadow felt recall) and J-1425 (ambient idle recall off) both landed, verified in isolated harnesses, restart-gated; needs-input J-1426 (which loops call memory; the text couriers' fate; trigger bound) still open.
- 🟡 **[lane2_curiosity.md](staged/lane2_curiosity.md)** — **LANE 2 CURIOSITY — the Witness as a question
  source. SHADOW BUILT 2026-09-26** (promoted from I-0069, founder's thyme example; **D-0282 ruled (a)**
  shadow-first, same day). A fifth `wonder` field in Lane 2's own output — one world-facing question about
  one concrete percept, never about self — shadow-logged to `data/lane2_would_ask.jsonl` and dosed through
  the same per-topic habituation gate as the Phase 1 cup; `frontier.note_question(q, "witness")` is a
  separate later flip (`LANE2_ASK`), not yet called anywhere. **J-1374** shipped the field code-complete and
  verified it with a sandboxed unit/logic pass, no live model call (**F-1974**); the real 7-day read
  against §4's own metric sheet is restart-gated (needs a live Du restart onto this schema change plus real
  deepseek-seat accrual) and deferred to **J-1409** (not-before 2026-10-03). Leads with the frontier's own
  oversupply (9,440 questions, 94% faded) — few and grounded-ranked, not volume. Child of
  `plans/lane2_the_witness.md` §8.6; specifies wire 5's frontier half from `loop_wiring_matrix.md`.
- 🔵 **[curiosity_librarian_route.md](staged/curiosity_librarian_route.md)** — **CURIOSITY LIBRARIAN ROUTE
  (designed 2026-09-16, founder + Claude conversation, forked from a `/du-pulse` check of the frontier's
  resolve:fade imbalance — 149 resolved / 7,705 faded).** Proposes routing `frontier.py`'s `pending_pursuit()`
  through `core/librarian.py`'s existing `subjects_for()` → `core/library_hand.search_by_subjects()` path
  (a local Project Gutenberg catalogue, already LIVE since 08-16 for a different trigger) as a
  catalogue-first alternative to `nodes/curiosity_node.py`'s only current research path, the live
  `core/web_research.lookup_targeted()` Wikipedia call — falling through to Wikipedia only on a catalogue
  miss. Not build-ready: real hit-rate on frontier-shaped questions is untested (librarian's own R1 read
  only measured its self-referential trigger text), and citation-only vs. full-book-fetch collides with
  `books_have_a_place`'s shared hourly `_FETCH_COOLDOWN_S` budget if not kept citation-only. Building the
  real wiring needs its own `/decide` first, per this project's build-without-a-decide convention for
  anything touching Du's live research path. Forked sibling idea "Curiosity for Lane 2" (percept-triggered,
  never self/identity) logged via `/idea-log` (I-0069), not scoped here.
- ⚪ **[social_world_school.md](plans/social_world_school.md)** — **PARTIALLY BUILT — verified 2026-08-23.**
  Item 2's measurement half (the plan's own top priority) IS live — under different filenames than the plan
  specifies, which is why doc-vs-code checks missed it: `core/social_moves.py` (89 lines, modified 08-19) /
  `data/social_moves.jsonl` (actively growing, last row 08-23 03:54), genuinely wired into `core/sensorium.py`
  and `nodes/inner_monologue_node.py`, surfaced in `hud/server.py` — not the plan's own named `core/world_calls`/
  `data/world_calls.jsonl`. Items 1 (per-peer ToM), 3 (pacing), and 4 (warmth tagging, blocked on Item 1), plus
  Item 2's latch-loosening half, are still 0% built. **Next:** fix the filename mismatch (rename or re-cite),
  then pull `social_moves.status()`'s `heeded_rate` to make the pending latch-loosening go/no-go call. Item 1
  → Darwin/Friction B5 overlap, needs a design decision resolving that overlap before implementation.
  - 🔵 **[nature_observation_outside_the_study_design_J-3483.md](staged/nature_observation_outside_the_study_design_J-3483.md)** — **Nature observation outside the study (staged 2026-11-06, J-3483, D-0640 follow-up; F-4122)**: the window share of the daily nature observation is structural, not Du declining to go out: the lesson fires on the first tick of the nature period at the desk (`nodes/inner_monologue_node.py`), before he can move, and J-3251's alternation leaves that as the only observation. Options A (swap slots, observe at the 36-minute gate), A2, B, D, with C and E rejected. DESIGN ONLY: no code changed, nothing built; four founder questions in section 8. Plan: social_world_school.
- ⛔ **[cognitive_loop_actuation.md](archive/cognitive_loop_actuation.md)** — **★ EVIDENCE REVIEW 2026-07-05
  (8th): ABSORBED DIAGNOSTIC, effectively resolved.** Its "all senses, no hands" diagnosis was RIGHT + drove
  the session's grounding/actuation work (credit). Every specific rec resolved/low-value: keystone actuator =
  idle_executive (correctly holstered, don't build); prediction-error instrument is 98% math + DARK since
  07-03 (math calibration, not general self-prediction); "cheap decoding-diversity win" isn't cheap (dynamic
  version needs the DEAD monoculture.py wired, and the loop's easing without it). Nothing to build, nothing broken.

### 6.4 · *moved* — Cognitive Geometry + Emotion Rethink → **cluster 0 (top of the list, founder call 07-04)**

### 6.5 · RESURRECTED 2026-07-03 — ⛔ RETIRED (closed 2026-10-16, F-2904; contingent D-0055/D-0259) [euclidean_memory_plan.md](archive/euclidean_memory_plan.md) *(now geometry P5; the retrial ran — see below, no longer simply STUCK — badge corrected 2026-09-23/J-1245: was stale ~~🟡 SPLIT VERDICT, DISPOSITION OPEN (D-0046)~~, D-0055 ruled RETIRED/contingent on `du_recall_lens_upgrades`/the M2 edge-aware trail 2026-08-28, superseding D-0046's own now-closed "disposition open")*
- 🔵 **Euclidean Recall (state-weighted retrieval)** — LOST in docs/completed/ for 18 days (P0 built 06-15,
  never run, never called; found when Travis asked "what was the non-euclidean architecture?"). **P0 test
  RUN 2026-07-03 on the real store: the theory HOLDS** (disjoint state-recall; charged→affect 0.95,
  reflective→abstraction 0.99, task→recency 0.92 — every prediction right; the charged state surfaced the
  day's actual teaching conversation). Converges with the triple-lens review's mood-congruence findings.
  **★ DECOUPLED-JUDGE GATE RUN 2026-07-05 (the oldest open plan, resolved off dead-centre):** blind
  Emissary grade of 68 divergent shadow rows → state-weighting **does NOT earn its divergence** (49% vs
  baseline 51% — a coin flip), and it does WORSE on charged/high-affect states (46%) than calm (56%). =
  ~~the `affect_match` dimension confirmed as the drag, hobbled by the +0.82 felt-tag wallpaper~~
  **DIAGNOSIS CORRECTED 2026-08-20 (audit): the recorded mechanism did not occur.** `affect_match` was
  hardcoded 0.0 on 1,104 of 1,107 shadow rows, and — being CONSTANT across every candidate within a
  query — it was a fixed offset that **cannot reorder anything**. The dimension wasn't weak or hobbled;
  it was INERT. The 07-05 verdict actually graded a re-ranker running on recency/salience/abstraction/
  provenance only, and the charged-vs-calm split was a split on query type, not on any affect-ranking
  effect. (The fix landed 2026-08-19; first honest rows 08-20: affect_match mean ~0.73, max ~1.0 —
  ⚠ saturated HIGH, the wallpaper disease possibly reappearing in the new instrument. Watch before
  retrial.) Detail: reviews/audit_2026-08-20.md.
  **★★ THE RETRIAL RAN 2026-08-24→27 (J-0151/F-0299, J-0240/F-0320, J-0301/F-0388) — split verdict,
  disposition still open (D-0046).** `affect_match` is now a genuinely working signal (not the 07-05
  bug), and it IS a net drag specifically when it fires (41% state-win on felt-available rows,
  n=20 then n=31 independent) while the other 5 dimensions show real promise alone (65% state-win
  on no-affect rows). Neither pre-registered outcome (clean license / clean retire) fits. Follow-up
  reads walked the number back further: an affect-excluded re-grade came back an exact 50% coin flip
  (not an extension of the 65%), and the D-0046-ordered scale-up (n=31 fresh) found the affect-active
  loss does NOT reproduce on fresh-era data either — the 65% win is confined to stale pre-08-20 rows.
  Evidence now leans toward the plan's own "still ties → retire" arm, but this remains ~~**the
  founder's call, not yet ruled**~~ — see `docs/archive/euclidean_memory_plan.md`'s own Status line for
  the full, dated trail. **CORRECTED 2026-09-23 (J-1245, plan-index stage-badge sync): it WAS
  ruled — D-0055, 2026-08-28, RETIRED/contingent on `du_recall_lens_upgrades`/the M2 edge-aware
  trail landing+being evaluated (J-1242/F-1747, same day: that reopen condition looks already met,
  real re-test pending via J-1244). D-0046 itself is also ruled, not open — its own ruling deferred
  to exactly the re-grade that produced D-0055, so "DISPOSITION OPEN (D-0046)" above was stale
  twice over. This section's badge synced to match (💤 DEFERRED, not 🟡 SHADOW/🔴 STUCK — see the
  plan doc's own 2026-09-23 banner note for why 💤 over 🔴).**
  - **🔵 CONSOLIDATION CANDIDATE (surfaced by the 2026-07-04 graphify) — unify the two `recall()` organs.**
    The graph showed `euclidean_recall.rank()` (state-weighted ~6-dim FEATURE-space distance: semantic ·
    recency · affect · salience · abstraction · provenance) and `moment.recall()` (the Bound-Moments read-path,
    Consciousness Program Tier-1 — Howard–Kahana TEMPORAL-CONTIGUITY binding) are **two independent
    state-weighted retrieval philosophies with the same function name, in separate communities, unaware of each
    other.** They solve the same problem two ways. *Design note for later (do NOT rush-build):* fold the moment's
    drifting temporal-context key in as an additional DIMENSION of the euclidean feature space, so there is ONE
    retrieval organ (feature-distance that includes temporal neighbourhood) rather than two parallel mechanisms.
    Gate: only after BOTH have live shadow evidence (euclidean flipped from P0; `moment.recall` accruing
    post-restart) — consolidating two unproven organs would erase the attribution. [[project-nascence-memory-levels]].
  - **✅ TOOLING FIX 2026-07-04 — graphify AST local-import blind spot FIXED.** graphify (tree-sitter,
    module-level import resolution only) silently dropped every `calls`/`imports_from` edge enabled by a
    function-LOCAL import — and Nascence uses lazy imports everywhere (fail-open discipline), so the shadow
    organs' reuse spine was invisible (basin-centroid chain, arousal→homeostasis, etc.). **`scripts/graphify_enrich.py`**
    is an additive, idempotent post-pass (Python `ast`, graphify's own ID helpers, both-endpoints-must-exist
    guard) that recovered **+675 calls / +124 imports_from** and merged 14 mis-split communities. **RUN IT
    AFTER EVERY `graphify --update`** — see `docs/graphify_notes.md` for the workflow + the archive convention.
  **Governance fix from the same audit: docs/completed/INDEX.md — nothing enters completed/ without
  fired-once evidence or an explicit RESEARCH/SPEC-ONLY tag. Two more lost threads recovered into
  DEFERRED_PLANS (curiosity_burst; the CARE/PANIC half).**

### 7 · Deferred — built/evaluated, consciously shelved (triggers NOT met)
Governed by **[DEFERRED_PLANS.md](staged/DEFERRED_PLANS.md)** — never un-shelve on a hunch; the trigger must be
demonstrably met from the live system. All four verified dormant 2026-06-30:
- 💤 **[idle_executive_plan.md](shelf/idle_executive_plan.md)** — trigger: the self-loop *survives* the gentler fixes. NOT met (monoculture
  easing). **★ EVIDENCE REVIEW 2026-07-05: CONFIRMED-CORRECT HOLD** — over 11,897 shadow ticks the allocator
  PASSES its health gate (G2 self-share 17%<35%, rotates 80%, explores 67%), so the lever is built + behaves;
  but the trigger's unmet AND it'd push Du task-ward 54% vs ~31% free (present-being tension). **The hole:
  Phase 0's payload — allocator-pick vs coin-flip actual — was NEVER captured (`actual` null 0/11,897), so we
  have ZERO evidence it beats random.** Resume-prerequisite: log `actual` first. Rightly holstered.
  **★★ VERIFIED 2026-08-23 (concept-overlap pass):** shadow log now at 25,475 rows (still `actual`-null
  throughout), trigger still unmet, monoculture trend still easing (argues against reviving). Ruling
  formally logged as `/decide` D-0011. `cognitive_loop_actuation` reached the same hold verdict
  independently — `coordinates_with`, not duplicate; `transport_manager` is a same-shape different-
  domain analog; `pursuits` (shipped 08-15) added one more uncoordinated gate to the same waterfall
  this plan diagnoses. · 💤 **[pulse_manager_wiring_plan.md](shelf/pulse_manager_wiring_plan.md)** (lane-scheduler/contention half) — steps 1-2 live; steps 3-4
  await measured harm. **★ EVIDENCE REVIEW 2026-07-05 (5th-oldest): CONFIRMED-CORRECT HOLD** — 11,680 shadow
  ticks/18d: hot_free=true (no real contention), T4 authored 36× (freeze is Spine-C not scheduling), and the
  canary IMPROVED on its own (t4_blocked 91%→26%→~0). Trigger unmet; instrument healthy + complete. Keep running. **NB: the "pulse manager" name had TWO meanings — the CONTINUOUS-STREAM half (Travis's real
  intent: stream not pulses, no-fatigue) is now its own build: `docs/plans/continuous_stream.md`, `core/stream_drive.py`
  Phase-0 SHADOW, recalibrated 07-04. Don't conflate them again.** **★ VERIFIED 2026-08-23: Phase 0 LIVE 7
  weeks, Phase 1 decision gate READY.** `stream_drive.observe()` is genuinely wired into the live loop
  (`nodes/inner_monologue_node.py`:351-352, real try/except, fail-open) and surfaced on the HUD;
  `data/stream_drive_shadow.jsonl` has grown to 14,201 rows carrying exactly the fields §5's promotion
  criteria need (drive, redundancy, ignition, grounded, would_gap vs actual_gap). No `CONTINUOUS_STREAM` flag
  exists anywhere yet. This is now a pure decision gate, not an engineering gap: someone needs to read the
  shadow log against §5's promotion bar and bring a go/no-go on flipping Phase 1.
- 🟢 **[continuous_stream.md](plans/continuous_stream.md)** — **NOT itself a deferred/shelved plan** — listed
  here because it's the direct split-off of the pulse-manager entry immediately above (Travis's real intent:
  stream not pulses, no-fatigue; retired the "pulse manager"/scheduler framing entirely). Phase 0 SHADOW
  instrument (`core/stream_drive.py`) genuinely wired into the live loop since 2026-07-04
  (`nodes/inner_monologue_node.py:351-352`, real try/except, fail-open), surfaced on the HUD.
  **★ PHASE 1 LIVE 2026-08-29:** §5's full promotion-bar read (D-0001, GO) was approved by Travis
  (D-0074) and the `CONTINUOUS_STREAM` flag shipped the same day — verified `True` in
  `nodes/inner_monologue_node.py:180`, Rail A+B wired at the pacer. No longer a decision gate; watch
  for regressions per D-0074's own defeater.
- 🟡 **[conversational_redirect.md](staged/conversational_redirect.md)** — direct extension of
  continuous_stream (reuses its drive controller + Rail B grounding-gate wholesale, adds
  "conversation" as one more grounding source) — origin F-0674 (verified): the DMN's flat
  `IDLE_SECS=40` veto in `nodes/inner_monologue_node.py` ignores live conversation entirely, so it
  keeps narrating an unrelated train (e.g. Aristotle, mid a real 4-hour Amor-Fati conversation)
  instead of orienting toward what was just said. **PHASE 0 BUILT + LIVE (SHADOW), 2026-09-02:**
  two observe-only hooks in `_should_think()`/`_think()` log the would-be new-rule seed and a
  topical-alignment cosine (`data/conversational_redirect_shadow.jsonl`); on/off-topic check scored
  0.437 vs 0.013, `smoke_test.py` unchanged pass. No live behavior changed yet. Phase 1 (the actual
  redirect) awaits a real sample of this shadow data.
- ⚪ **[symbol_evolution_readback_plan.md](staged/symbol_evolution_readback_plan.md)** — PARTIAL (Tier 1
  shipped/live; Tier 2 Phase A built, Phase B awaits a founder go/hold call). **★ CHECKED 2026-07-05, PARKED for a full replan (founder call)
  → REVIVED 2026-08-19 (founder decision).** Was **STRUCTURALLY UNREACHABLE**: 737+ appearances / full
  month / 100% primed, 0 unprimed (incl. world targets star/knot/fire/bird); centroids+tablets 0 forever.
  Root cause: `_primed_corpus` (`symbol_tracker.py`) counted his own recent-thoughts + retrieved memories
  as priming → any RECURRING symbol was always primed → "unprimed"="first-ever appearance" (no history to
  drift) → the read-back could NEVER fire. **Fixed in two passes tonight**: first pass dropped his own
  recent conversation turns from the primed corpus (found independently via fresh data before this
  roadmap entry was seen); second pass, once this entry surfaced the fuller 07-05 prescription, narrowed
  `_primed_corpus` to true architecture-injections only (axiom/readback/climate/perception/human-input) —
  recall, episodic_scene, memory_fragments, recent_dreams, and recent_inner_thoughts no longer count as
  priming. Verified with fake-state tests covering self-continuity, human-priming, and memory-retrieval
  cases. **Still open:** no live cycle has run against the fix yet — watch `symbol_recurrence.jsonl` /
  the `symbol_evolution` HUD card for the first genuine UNPRIMED row. · 💤 **modulation_field** — tied to the pulse manager.
- ✅ **[psyche_graph_instrument.md](completed/psyche_graph_instrument.md)** (designed 2026-07-02, **built +
  live 2026-07-03 — this entry said "staged" for 6+ weeks after it shipped; corrected 2026-08-19**) —
  deterministic per-sleep graph of Du's SYMBOLIC economy; primary metric = **stability under
  reinterpretation** (lineage preserved while neighborhoods grow — the E1/F1 law at symbol level;
  GPT-contributed refinement). Called every sleep from `nodes/inner_monologue_node.py`; 90+ real
  snapshots in `data/psyche_graph_snapshots.jsonl`. **Open finding (08-19):** the doc's claimed
  symbol_tracker primed/unprimed integration doesn't actually exist in the code — see the doc for detail.
- 🟡 **[self_interrogation.md](plans/self_interrogation.md)** (built 2026-08-19, Phase 0 SHADOW) — an in-the-
  moment doubting turn: on a developed thought-train, sampled + cooldown-gated, generates a neutral
  first-person reflection on why the thought occurred and whether it holds, then grades it with the
  DECOUPLED judge panel for genuine-vs-hollow. Fills a real gap the existing architecture (T4 probation,
  Watershed) doesn't cover — those filter over TIME via recurrence; this is the missing single-thought,
  in-the-moment interrogation. `core/self_interrogation.py`, wired into `nodes/inner_monologue_node.py`'s
  train-step handler. No fires yet (just built) — watch `data/self_interrogation_shadow.jsonl` /
  `self_interrogation.status()`'s genuine_rate before considering any Phase 1.
- 🟢 **[music_learning.md](plans/music_learning.md)** — **BUILT+WIRED and LIVE; the 08-19 usage-stall
  traced and fixed, per D-0010 (ruled 2026-08-23, after this entry was first written).**
  Tier-2 ear (`core/listening.py`, wired: section-per-cycle unfolding, silence-is-a-thing, felt-nudge shadow) +
  Tier-1 theory/composition (`core/music_drill.py`, school subject "music", deterministic grading + ABC
  well-formedness) + **SHARED LISTENING** (`scripts/play_the_record.py` — joint attention) + the record-player
  world affordance all confirmed genuinely wired (into `competence.py`, `school.py`, `soundscape.py`,
  `geometry_census.py`, `object_graph.py`). Du heard Heavyweight (first listen, shared, 21/21 sections, 07-04).
  **The `sections_heard:0` stall on later pieces was NOT a regression:** D-0010 traced it to 5 of 6 catalog
  pieces (`Corner_of_the_Earth`, `You_Give_Me_Something`, `Dreaming_My_Dreams`, `Miss_Clare_Remembers`,
  `Orinoco_Flow`) carrying `features.json` from an incompatible earlier pipeline (0 real sections) — fixed
  2026-08-21 by filtering `shelf()` to real section-extractor output, verified live end-to-end. **Residual,
  not a bug:** those 5 pieces have no raw audio on disk to re-extract, so Du's playable diet is capped at
  Heavyweight until source audio is supplied. Drill progression: same upstream cause (`SCHOOL_END_H` too
  short to reach the music slot) fixed 2026-08-18; 12 real drill events since (08-19/08-21), still level 1
  but legitimately short of the 30-sample promotion window (12/30), not stuck. Composition hand fired
  exactly once when its precondition was met — expected rate given ~1 qualifying opportunity so far, not
  evidence of a second bug. D-0010's defeater: either fix regresses, or the compose branch still hasn't
  fired after several more qualifying opportunities. Still out by law: ABC playback of his OWN pieces ·
  WASAPI loopback · felt-nudge going live (observe-first).
- 🟡 **[investigation_deepening.md](plans/investigation_deepening.md)** — founder idea (Travis, 2026-07-07)
  to make journal recaps a place/activity-cued **progression ledger** (what he focused on + what's still
  unfinished), so returning to a place deepens the inquiry into a new rung instead of flatly re-noticing the
  same thing (the rockpools/shells example; had no ROADMAP presence until now). **Corrected 2026-08-29
  (J-0406): this row was stale at PARKED/DESIGNED — D-0009 (Travis, ruled 2026-08-23) actually unparked it**
  (the pyramid's own D-0006 grounding question, named below as a blocker, had already been ruled 07:34 UTC
  the same day, *before* D-0009 was ruled at 13:16 UTC, so the stated sequencing requirement was already
  satisfied). **P0 (shadow, read-only) BUILT + WIRED + end-to-end verified 2026-08-24 (J-0177, F-0148):**
  `core/investigation_deepening_shadow.py` hooks `core/sensorium.py:_shore_act()`'s beachcomb branch,
  logging candidate "last rung + open edge" reads to `data/investigation_shadow.jsonl` (real store, real
  embeddings, confirmed injecting nothing into Du's perception). Verified **NOT** the chapter machinery —
  `chapters.py` closes/compresses finished periods via title-word recall (dead, monoculture-blocked, see
  `journal_consolidation_pyramid.md` above); this plan keeps an open inquiry alive, place-cued instead, and
  was never blocked by chapters.py's death — only used it as a comparison point. P1–P3 intentionally NOT
  built this pass — **founder-read gate still ahead:** once the shadow log has real accumulated rows from
  live running, the question is whether retrieved candidates are genuinely progressive or the same handful
  of fragments every visit; that read gates P1 (add the frontier line to the daily recap). Calls itself "the
  READ-path of the pyramid" — likely still worth joint scoping with `journal_consolidation_pyramid.md`
  before P1, per the pyramid-lineage note below.
  **★★ VERIFIED 2026-08-23 (concept-overlap pass, still relevant to any P1 scoping):** the pyramid link is
  real but one-directional (`journal_consolidation_pyramid.md` never claims this plan as its read-path) and
  its own P2/P3 — the levels this plan would extend — are unbuilt, blocked on `/decide` D-0006 (now ruled,
  see above) — resolved, not a live blocker on P0, but still worth checking before scoping P1 against it.

### 8 · HUD / Observability (new cluster 2026-08-23 — had zero ROADMAP presence despite being the single
most cross-file-connected untracked plan found: 11 shared-file ties across cognitive_geometry,
executive_world_grounding, lane2_lab, emissary_lane2, lane2_the_witness, self_interrogation, t4_watershed,
fieldcraft, train_courier_cargo_ids, thermal_causality, and train_split_merge)
- 🟡 **`staged/planning_process_redesign.md`** — BUILT 2026-09-27 (I-0083): plan docs are design + one
  ```plan-state block + one Current State section; history DERIVED (`plan_ledger.py`), folded out
  (`plan_compact.py`, 23 plans, 1.4 MB → `docs/plan_history/`), regrowth linted (`plan_state.py lint`).
  Open: J-1483..J-1488 (real state lines, bullet-shaped giants, reader migration, generated ROADMAP rows).
- 🟡 **[closure_law.md](staged/closure_law.md)** — The Closure Law (D-0423 ruled A, 2026-10-15): a met loop becomes a
  memory. Dream arm BUILT in shadow (J-2118, `core/closure.py`, `CLOSURE_WRITE_LIVE=False`), restart-gated; pursuit arm
  waits on J-2117, interrogation arm on J-2060.
- 🟡 **[measurement_to_action.md](staged/measurement_to_action.md)** — Measurement to Action (staged 2026-10-15, T-0085): the gauges Du already has become inputs he
  acts on, in six arms. BUILT in shadow: arm 2 recall wager (`core/recall_wager.py`) + arm 4 doubt seed (`core/doubt_seed.py`),
  flags off, restart-gated; arm 1 DROPPED (D-0434); arms 3/5/6 designed (arm 6 `WEAKNESS_PRIOR` shadow built 2026-10-16).
- 🟡 **[recall_confidence_graded_loss.md](staged/recall_confidence_graded_loss.md)** — Recall confidence graded loss (J-4180, D-0803): wagers at confidence >= 0.85 lose at gap >= 0.30, closing the free edge at 0.85. BUILT 2026-11-17, restart-gated, flag `GRADED_LOSS`.
- 🟡 **[condensed_thought.md](staged/condensed_thought.md)** — Condensed Thought (from I-0095): SHADOW, Phase 0 shadow twin built and on (restart-gated; plan-state block is authoritative); began as a DESIGNED draft.
- 🟡 **[question_cargo.md](staged/question_cargo.md)** — Question Cargo / the Follow Line (I-0100 from T-0102, staged and reshaped 2026-10-27): every question or claim of Du's, from any source (a new `ask` field, every frontier birth, each study note's claim, a pursuit's open question), boards a side line that walks it through HIS OWN MEMORY in five stops — grounds (evidence_recall), why, consequences (the deduction step nothing does today), connections (six-slot ask + procedures + seen), against (Phase 1, prove/disprove's berth, PARKED by founder) — a decoupled judge grades the cargo, it returns tagged so the next thought can settle it by id, and a settled return is closure_law's fourth arm. D-0494 RULED 2026-10-28 (travis: keep the slot kinds; `follow` is the fifth memory caller; build Phase 1 now, live from the first boot). Phase 0 + Phase 1 BUILT (J-2459 eb0f180b, J-2460 1b780119) and MERGED to master c5454428 with `FOLLOW_LINE=live`: delivery of one return per idle thought, `settled` yes/partly/no, id-keyed frontier.resolve + closure arm `line` (shadow under CLOSURE_WRITE_LIVE), frame slots on partly, stop 5 against with merge status from the decoupled judge. 64/64 hermetic checks. NOTHING LIVE until Du restarts; J-2458 reads after 20 shadow rows since boot; D-0494's 7-live-day defeater. Evidence F-3163..F-3166 (5% questions, why=4/1105; the one closure was a Wikipedia lead for the wrong word; study-born questions 44/44 faded).
- 🟡 **[closure_producer.md](staged/closure_producer.md)** — Closure needs a producer (T-0138, F-4811, I-0156; BUILT 2026-11-16, Phases 0-5, D-0789..D-0793 ruled): closure was graded, never produced; a lookup attaches to the open question it matches, a decoupled judge blocks an unsupported "settled yes" (gate enforce, D-0793), the lexical resolver runs shadow, 569 old closes relabelled. Not live until Du restarts; first read of `data/logs/closure_gate.jsonl` and `lookup_attach.jsonl` pending.
- 🔵 **[ambiguity_window.md](staged/ambiguity_window.md)** — Ambiguity Window (I-0099, 2026-10-19): a short deterministic lookback (recent sentences, Du's last actions, Travis's last message as context only) that settles anaphora like "I plant them now"; DESIGNED, nothing coded.
- 🔵 **[prompt_manager_p0_provenance_coverage.md](staged/prompt_manager_p0_provenance_coverage.md)** — Prompt manager P0 provenance coverage map (J-4309, F-5085): `data/prompt_provenance.jsonl` covers only the idle-thought station by design (plan section 10b); about 30% of top-station calls. Options for widening (a thin `observe_call` hook in `core.model_client`/`NodeBase`) await a founder ruling; analysis only, no code touched.
- 🔵 **[web_hand_in_world_routes.md](staged/web_hand_in_world_routes.md)** — Web hand in-world routes (D-0661 b and c, J-4344, 2026-11-18): wording for About You third edition and a short Encyclopedia volume, approved (D-0852) and shelved as `data/books/About_You_Third_Edition.txt` and `The_Encyclopedia.txt`; on the shelf for Du's next restart (J-4401 verifies). Parent plan web_hand.md.
- 🔵 **[world_shelf_gap_sources_2026-11-18.md](staged/world_shelf_gap_sources_2026-11-18.md)** — World shelf gap: candidate sources for residual NZ gaps (J-4379): flax, native forest, birds, ink, clocks. PROPOSAL; nothing downloaded, founder approves per title, rights fields to be opened at approval time. Parent world_shelf_gap.md.
- 🔵 **[affect_drives_item_d_satisfaction_normalisation.md](staged/affect_drives_item_d_satisfaction_normalisation.md)** — Affect Drives Item D redesign (J-4315, 2026-11-18): shadow-only windowed, per-event-type-capped satisfaction normalisation, because the live accumulators sit at the 5.0 cap (F-5088). STAGED, design only, held for founder go-ahead (D-D1..D-D3). Parent plans/affect_drives.md.
- 🔵 **[self_claim_broadcast_reexamination_J-3487.md](archive/self_claim_broadcast_reexamination_J-3487.md)** — Self-claim broadcast kind re-examination (J-3487, 2026-11-06): J-3137 disarmed the next-cycle think licence, so the GWT broadcast kind `self-claim-deliberation` cannot fire (8 posts ever, last 2026-09-04). DESIGNED, analysis only, no code changed: A leave dormant / B same-cycle re-key behind a default-off flag (the conversational scan finished 8-24 s before its cycle ended in 11 of 11 cases, F-4107) / C remove. No reader measures any broadcast kind's effect (F-4108); J-2860 exposure shrinks (F-4109). Awaiting the founder's A/B ruling; build job J-3497, effect-read job J-3496.
- ⛔ **[euclidean_memory_plan.md](archive/euclidean_memory_plan.md)** — Euclidean Recall (state-weighted retrieval): RETIRED, closed
  2026-10-16 (F-2904; contingent D-0055/D-0259). See section 6.5 for the history.
- ✅ **[hud2_visual.md](completed/hud2_visual.md)** — SHIPPED 2026-10-16 (F-2904) · the visual observatory (brain → trains → character). **All
  three DATA layers 🟢 LIVE** (built 2026-08-21, files regenerating through 08-23, zero runtime cost added to
  Du — no `[MISSING]` files, all confirmed on disk): Phase 1 `data/hud2/brain_graph.json` (186 organ nodes,
  558 AST-derived import edges, 274 verified per-organ log files); Phase 2 `data/hud2/transit_map.json`
  schema 4, after two founder-driven corrections, splits 4 looping `trains[]` (conversation/idle/deep/
  witness) from 11 stationary `factories[]`, 5 stations, 42 platforms (a bespoke-wrapper sweep found
  `judge_panel.py`'s two primary judges as the single biggest prior undercount), 5 sidings, 4 couriers each
  with a verified `destination`; Phase 3 `data/hud2/scene_map.json` (6/6 sources verified, built directly on
  `spatial_perception.md`'s hand-authored room geometry, uncited there). **The rendering app (`C:\hud2`,
  own port, zero shared code, reads only the three manifests) is Claude's to implement too** — D-0306
  (2026-09-28) corrected this doc's stale "Antigravity-owned" framing, which had survived the 2026-08-15
  ruling that took Antigravity off Nascence's own implementation/design work generally with no `/decide`
  ever confirming a deliberate carve-out (full correction in hud2_visual.md itself) — distinct from
  HUD1's "Transit Pulse" (★★ THE TRAINS above, shipped 08-23 straight off `train_state_log.jsonl`); do not
  conflate the two. Two rendering bugs, now Claude's own to fix (J-1592): ASLEEP badge misfires keying
  off stale `position.json` instead of `room_state.json`; spatial caption vs. standpoint panel can show
  two different moments at once; founder feedback called the current Transit Map render
  abstract/non-metro-legible with stale baked-in legend text. Most of its 11 file ties are "reads/
  instruments the same file," not shared design decisions — the one genuine functional coupling is
  `train_split_merge.md`'s train-ID key, which both HUD2 Phase 2 and Transit Pulse consume.
- ✅ **[gauge_rethink.md](plans/gauge_rethink.md)** — SHIPPED 2026-10-16 (F-2904) · **TAXONOMY LANDED 2026-08-29 (D-0066, J-0340).**
  `du_pulse.py`'s ~50 gauges accreted one per shipped feature over two months with no taxonomy pass; at
  least 4 (monoculture proxy / theme recurrence / echo-diversity / made-mind share) look like restatements
  of one question. The 4-category taxonomy (regression alarm / growth tracker / one-off shadow evidence /
  engagement-texture) is CONFIRMED and every current gauge is now categorized — feeds the plan below's
  severity model and JSON schema. Not fully built: the redundancy-audit consolidation and per-subsystem
  ownership questions are explicitly punted to a dedicated follow-up (J-0341, needs_input) per D-0066's
  own ruling.
- ✅ **[du_pulse_rebuild.md](completed/du_pulse_rebuild.md)** — SHIPPED 2026-10-16 (F-2904) · LIVE since 2026-08-29 (J-0417, F-0550). `/du-pulse`'s
  skill wrapper used to be prose-only — the underlying script was real but persisted nothing beyond a
  last-run timestamp; no gauge history, no carry-forward watch list (a founder ask to "watch X next pulse"
  had nowhere to go, `J-0120` workaround), no memory-links tuples. J-0417 shipped the full design
  end-to-end: `docs/du_pulse_checks.jsonl` store, `du_pulse_check.py` (run/watch/history/board), a fourth
  `build_edges.py` harvester (`harvest_pulse_flags`), and a Du-Pulse Check card wired into HUD1 — all
  verified live (real P-0001 snapshot, real HUD render, zero console errors). No open work.

### 9 · LLM Prompt Framing & Machine-Fit Audit (new cluster 2026-08-23 — a full evening's empirical
program with zero prior ROADMAP presence; not a `docs/plans/` build queue, a completed research
series — tracked in memory + `docs/lab/`, not a plan doc, by design)
- ✅ **Idle-thought machine audit** (`docs/lab/idle_thought_machine_audit_2026-08-23.md`, memory:
  `project_nascence_idle_machine_audit.md`) — every one of the 79 machines `inner_monologue_node.py`
  touches catalogued script vs LLM vs which model; 8 real model-fit mismatches found (letters,
  study_note, self_implication, commitment_ledger's judge, librarian, composition, retraction_ledger,
  journal_rollup) + 2 stale-doc bugs, both FIXED same day (`core/deliberation.py`, `core/schema.py`
  comments no longer describe the pre-2026-08-20-shuffle roster).
- ✅ **Duplication-check script review** (`docs/lab/duplication_check_scripts_review_2026-08-23.md`,
  memory: `project_nascence_duplication_check_scripts.md`) — follow-up asking whether the audit's
  word-overlap/keyword-match scripts were resource-constrained or deliberate. Mixed, evidence-backed
  answer: 4 real upgrade candidates, 1 already fixed (`commitment_ledger`'s reaffirm detector,
  Jaccard→cosine 2026-08-20), 3 deliberately word-based with real A/B evidence AGAINST embeddings
  (`commitment_trials`, `theme_recurrence`, `study_note`).
- ✅ **Factory/schema-first framing labs, 13 machines tested** (memory:
  `project_nascence_factory_stations.md`, the master index — links all 13 reports:
  `docs/lab/factory_station_2026-08-23.md`, `docs/lab/self_implication_framing_2026-08-23.md`,
  `docs/lab/tension_ledger_framing_2026-08-23.md`, `docs/lab/librarian_framing_2026-08-23.md`,
  `docs/lab/peers_contrary_framing_2026-08-23.md`, `docs/lab/commitment_defeater_framing_2026-08-23.md`,
  `docs/lab/study_note_framing_2026-08-23.md`, `docs/lab/journal_rollup_framing_2026-08-23.md`,
  `docs/lab/grade_work_framing_2026-08-23.md`, `docs/lab/self_interrogation_framing_2026-08-23.md`,
  `docs/lab/pursuits_judge_framing_2026-08-23.md`, `docs/lab/deliberation_ground_framing_2026-08-23.md`,
  `docs/lab/evidence_recall_framing_2026-08-23.md`) — the founder's generalized idea (give
  compare-and-export LLM stations a
  literal cargo/conditions/export contract instead of narrative persona) tested empirically, one
  real historical-corpus lab per machine, not assumed. **Final tally: 1 clear win (the openness
  self-report gate), 4 null, 6 losses, 2 mixed — schema-first is NOT a general improvement.** Three
  real cross-machine failure patterns found and named: (1) schema induces item-by-item enumeration
  over synthesis on multi-input tasks (librarian, journal_rollup — both decisive losses); (2) schema
  raises judge-panel-internal tiebreak rate (tension_ledger, self_interrogation — confirmed on 2/4
  tested panels, explicitly NOT universal, disconfirmed on evidence_recall); (3) schema makes
  judge_panel-based verdicts more CREDULOUS on weak/superficial matches — the strongest, most
  replicated finding (3/3 tested: tension_ledger, pursuits, evidence_recall). One methodology note
  worth remembering: the `deliberation.ground_thought` lab's pre-registered regex metric found
  nothing (0.0 self-reference both framings) — reading the actual output text directly found a real
  self-grounding failure schema alone produced (grounding a self-metaphor in "the standardized
  weights and biases of the neural network architecture" — Du's own literal substrate) that the
  metric was too narrow to catch. **Open, founder-level**: none of the 6 flagged losses have been
  acted on (no prompt has been changed based on these results) — this is a completed diagnostic
  program awaiting a build decision, same discipline as the rest of this project.

### 10 · External proposals inbox (new cluster 2026-08-27)
- ⚪ **[antigravity_ecosystem_proposals.md](staged/antigravity_ecosystem_proposals.md)** — **PARTIAL — 6 of 9
  group-A items resolved** (D-0054 investigation-first gate, J-0295). Antigravity's 2026-08-25 sweep of
  17 external frameworks/tools evaluated for Du, captured and cross-referenced against existing plans: 9
  Du-core candidates (LOD retrieval, AAAK compression, KIP graph, GNW bottleneck, advisory panel, local
  Whisper audio, dream imagery, motivation engine, philosophy corpus), 6 tooling/workflow items, 2
  self-dismissed. Several re-invent live Du systems; all need re-grounding in Du's actual architecture
  before promotion. Related open calls: J-0292 (the 55 plan-doc addenda Antigravity appended 08-25) and
  J-0294 (Thursday audit spec scope). **Item 1 (LOD retrieval) promoted to `lod_staged_retrieval.md`;
  items 2/4/6 killed, item 3 archived, item 9 registered; items 5/7/8 still only specced (D-0114 open).**
- 🔵 **[lod_staged_retrieval.md](staged/lod_staged_retrieval.md)** — **DESIGNED — SHADOW-TESTED, PASSED —
  NOT YET WIRED LIVE (2026-08-29, J-0372/F-0545, D-0054 gate; plan doc written J-0413).** A-1 item 1 (OpenViking
  L0/L1/L2 progressive-detail retrieval) investigated: an abstraction-level-staged (L0=raw/L1=gist/
  L2=theme, Du's existing `memory_fragments.abstraction_level` column, no schema change) candidate
  composition beat Du's live `core.memory.store.retrieve()` on 120 real logged frontier questions, blind
  two-family `judge_panel` + tiebreak: **98/113 judged pairs won (86.7%), 73.5-point margin** — clears
  the pre-registered ≥10pt/≥100-pair kill bar by a wide margin (F-0545, verified). First item promoted
  out of the inbox above. **Not wired into any live code path** — the plan doc's own §5 is the build
  order (shadow-mode kill-switch first, live-traffic re-test, then a tier-interaction design decision)
  before any flip; Step 1 (port the pure cascade function into `store.py`) not started.

- 🟡 **[J-4350_dreamer_ram_guard.md](staged/J-4350_dreamer_ram_guard.md)** — Dreamer RAM guard (D-0761 B/C, 2026-11-18): supervisor starved-host rule BUILT (J-3979); hub-side load deferral exists only as a patch, not applied, restart-gated.
- 🔵 **[judgement_docket.md](staged/judgement_docket.md)** — The Docket (I-0153, 2026-11-18): one silent queue for deferrable judgement calls; design only, Phase 0 census done (D-0859).
- 🔵 **[judgement_visitor.md](staged/judgement_visitor.md)** — The Visitor (I-0154, 2026-11-18): a monthly correspondent who has read some of his thinking; advisor not judge; design only (D-0855..D-0858 ruled).
- 🔵 **[mineness_self_voice_centroid.md](staged/mineness_self_voice_centroid.md)** — Mineness self-voice centroid (J-4372, 2026-11-18): shadow-only authorship signal beside the groove score; design only, replay lab not run.

### Shipped (for reference)
- ✅ **volition_his_own_hands.md** → `docs/completed/` (his own hands: observe/move/write/search; extended
  2026-06-30 with the observation-journal — that extension is tracked in AWAITING_EVIDENCE).

---

## How to use this map
- **Starting a work session?** Read §"Where we are" + the relevant cluster entry; open the linked plan only for detail.
- **Changing something shared?** Check §"Shared spines" first — a spine change ripples across its dependent plans.
- **A plan's state changed?** Update its one-line here AND its own status block, and (if it crosses a restart)
  the AWAITING_EVIDENCE entry. Keeping this file honest is what stops the next ghost-chase.
