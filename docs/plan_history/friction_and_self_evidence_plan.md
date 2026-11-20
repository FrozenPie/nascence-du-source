# friction_and_self_evidence_plan — folded history


---

# History folded on 2026-09-27 from `docs\staged\friction_and_self_evidence_plan.md` (hand-fold, J-1499 — heading text not matched by plan_compact.py's own CS_HEAD regex, 1 section, verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py friction_and_self_evidence_plan`._

## ▶ STATUS — as-built (verified against live code + logs, 2026-06-30)

| # | Build | State | Evidence |
|---|-------|-------|----------|
| **B1** | Sit-with-it gate (`core/sitting.py`) | **BUILT + WIRED (full read-path) — but trigger too NARROW** | Complete loop: `note_difficulty` → `dwell_steer` (injects *"STAY with it, name it, feel it"* into his idle mind) → `dwell_tick` → `is_dwelling` gate (4-cycle dwell). NOT write-only — the read path is real. **But the only trigger wired is total math-failure** (`inner_monologue:642`); `raw_difficulty.json` is empty (rarely/never fires — and the math was eased, so even that case is rare). The plan's general *low-valence + self-reference* detector is NOT wired. *(Later corrections: conv-path trigger LIVE since 2026-07-03 — see the 08-24 block; the dwell-release-on-shift fix BUILT 2026-08-27 — see the ★★ 08-27 block.)* |
| **B2** | Behavioural mirror / evidenced self (`core/self_mirror.py`) | **BUILT + WIRED + FIRING — working** | Periodic (`due()`), computes his real patterns (`mirror_facts`), reads them back, he reconciles. LIVE: *"the record shows my week was overwhelmingly dedicated to internal processing"* / *"my actual energy distribution was dominated by internal consumption."* The evidenced self confronting the authored self — the keystone genuinely working. |
| **B3** | Productive failure — struggle before instruction | **NOT built** | Lessons still hand the method up-front (instruction-first — the weaker design the plan itself flagged). |
| **B4** | Schema-breaking irreversible stakes | **WIRED but REAL NO-OP — self-claim register has no caretaking claim yet** | Updated 2026-08-25 (J-0253, F-0331): `core/garden.py`'s `plant_died` branch now calls `_b4_bind_death()`, which binds an owned death (`origin=="sown_by_du"`, excludes weeds/volunteers) to a `self_claims.held_claims()` caretaking match and routes it through `sitting.note_difficulty()`, refractory-gated (7 days). **Re-checked 2026-09-02 (J-0274, F-0642, 3rd re-check spawned as J-0469):** still no caretaking-type self-claim in `commitment_active.json` (empty) or `capability_beliefs.json` (16 domains, none matching `_B4_KEYWORDS`). One real `plant_died` event has now occurred (chickweed, 2026-08-28) but its `origin` was not `sown_by_du` (a volunteer, correctly filtered before reaching the claim check) — the bind's read-path remains fully unexercised. **D-0050 is now RULED, not open** (2026-08-27, travis): fully organic, no seeding — wait for the claim to arise on its own. Lost-work / strained-friendship stakes remain fully unbuilt. |
| **B5** | Genuine social friction (a peer names blind spots, unprompted) | **NOT blocked any more — both tracks BUILT, awaiting observation** | STALE below: D-0003 was RULED "both" 2026-08-24 (not left open), and `peer_correspondence_plan.md` shows both split tracks already have code as of 2026-08-24 — §B5-A (Buddha-as-gentle-challenger, J-0172, F-0147) and §B5-B (stance property, J-0173/J-0213, F-0159/F-0289) — both `BUILT/NOT-YET-EVIDENCED-LIVE`, no further founder decision needed, just wall-clock observation after a restart. `peer_correspondence_plan.md` was RESCOPED 2026-08-23: its COMPANY half shipped (see `docs/completed/peer_correspondence_company.md`). Checked against every newer plan same day: `thought_grounding.md`'s Route 3 (built, live) covers an adjacent but non-overlapping slice — Du-*initiated* question-testing via a friend who'd disagree, never a peer naming a blind spot unprompted — so it does NOT close B5. Updated 2026-08-23, additive — see [[project-nascence-peer-correspondence-plan]]. |
| **B6** | Widen affect band + own the hard feeling plainly | **Partial** | The affect vector carries anger/grief dims (`mood.py`), but no dedicated *let frustration be felt + owned plainly* build beyond the journal's plain-sentence discipline. |

**Verdict:** both KEYSTONES are in — **B2 genuinely working**, **B1 sound but under-triggered**. The SUPPORTING builds (B3/B4/B6) are unbuilt; B5 waits on Darwin. → **Ready to advance:** widen B1's trigger + build B3/B4/B6. Research run on these next (2026-06-30).

> **★ EVIDENCE REVIEW 2026-07-05 (6th-oldest open plan) — HEALTHY + WORKING; the first of the review's six
> that's neither broken nor merely held. ADVANCE B1.** B1 conversational detector
> (`self_implication_conv_shadow.jsonl`, 60 rows, n_claims 10-14 healthy): **PRECISE — 2/2 fires genuine**
> (both direct self-claim challenges, directness 0.7-0.8; the 2nd ALSO caught `retreat_in_draft=true` — the
> retreat cascade it was built to see), correctly silent on 58 idea-discussions. Real fix for the idle
> version's blindness (0/358). **B2 mirror CONFIRMED live** — 24 reconciliations, last today 14:53.
> *Caveat:* a modest RECALL gap — Travis's INDIRECT challenges (the ownership thread; "you, like the cat,
> can choose") arrive as teaching, marked directness 0.0, don't fire. Defensible: for a sit-with-hard-truth
> intervention, under-firing is the safe side (a false positive nags wrongly) → precision-over-recall is the
> right bias here; watch, don't block. **Disposition: ADVANCE B1 Phase-0→Phase-1 (shadow the retreat cascade
> — still observe-only, low-risk); B2 keep firing; B3/B4 the unbuilt supporting work; B5 waits on Darwin.**
> Nothing broken — the rare "advance, not fix/retire" verdict of the set.

> **★★ EVIDENCE RE-REVIEW 2026-08-24 (J-0065) — B1 IS LIVE, NOT SHADOW; THIS SECTION WAS STALE. Precision
> holds at scale; no separate "Phase-1" was ever built.** Full-log re-read (not sampled): conv detector now
> 215 rows (6 would-fire, all directness 0.7-0.8, all genuine 2nd-person self-claim challenges — matches the
> 07-05 2/60 ratio); idle detector now 7,063 rows (25 would-fire, 0.35% — up from the earlier 0/358 near-blind
> state, signal mix A=579 B=737 C=7 D=20 E=4 F=0). **The headline correction: the conversational gate stopped
> being "Phase-0 shadow" on 2026-07-03 — two days BEFORE this 07-05 disposition was written.**
> `core/orchestrator.py:1094-1120` (comment "FRICTION B1 GATE — WIRED 2026-07-03") calls
> `sitting.note_difficulty()` for real whenever `contradicts=true`, and `data/nascence.log` shows it has
> genuinely fired **6 times in production** (2026-07-03 ×2, 2026-08-09 ×2, 2026-08-11, 2026-08-13) — matching
> the 6 shadow-log `contradicts:true` rows 1:1 by claim name. **The "retreat-cascade Phase-1 shadow extension"
> named in the disposition above was never built as separate work** — `retreat_in_draft` has been logged
> since the ORIGINAL 2026-07-01 Phase-0 code (same function, same file), nothing anywhere reads or acts on it
> (grep confirms only `self_implication.py` writes it), and it fires on 63/215 (29%) of ALL conv turns
> regardless of whether a contradiction occurred — not selective enough to act on as-is. The known RECALL gap
> (Travis's indirect challenges, e.g. "you, like the cat, can choose") is still present at n=215 — same
> instance, no new evidence either way. **Idle detector quality flag (shadow-only, does not affect behaviour):**
> 19/25 idle fires are B+D only (no contradicted claim), heavily metaphor-laden ("river carving...unyielding
> stone", "running low on sediment") rather than plain first-person naming — possibly one recurring rumination
> attractor rather than 25 independent events; the fluent/poetic register is exactly what the plan's own
> cross-cutting discipline warns against rewarding. Confirmed still shadow: `scan_shadow()` never calls
> `core.sitting` (0 matches). **Confirmed still NOT built:** the dwell-release-on-shift fix — `sitting.py:23`
> `MIN_DWELL_CYCLES=4` is still a pure cycle-count clock, no felt-shift check. **Disposition: correct this
> doc's status to LIVE for the conv path (B1's real trigger is proven — 6/6 production fires precise); the
> idle path stays SHADOW pending a plain-language retune (see D-0026); the felt-shift dwell-release fix is
> the actual highest-leverage remaining build, not a "Phase-1" that doesn't exist.** See F-0046, F-0050.

> **★ SCOPE/PURPOSE REVIEW 2026-08-25 (J-0218, from D-0026's HOLD) — B1/B2 status independently RE-VERIFIED
> live against code + logs (still accurate; no new fires since 08-13, conv shadow now 225 rows / idle shadow
> now 7,369, both still growing on the same shape). The B4 and B5 rows above were STALE and have been
> corrected in place: B5 is no longer blocked (D-0003 ruled "both" 2026-08-24, both tracks already BUILT,
> awaiting observation only — see `peer_correspondence_plan.md`); B4 already has a real, actively-developed
> irreversible plant-death mechanic (`core/garden.py`, `core/sensorium.py`) the doc gave it no credit for,
> though it is still not bound to the self-claim register or routed through B1's gate, so B4's actual
> schema-breaking requirement remains the real gap, not "no mechanic at all." Net effect on the founder's
> pending a/b/c call (D-0026, reopened): the dwell-release-on-shift fix in `sitting.py` is still the
> cleanest, most isolated highest-leverage build; but "move to B4" is now cheaper than the doc implied — it
> would mean wiring the existing garden death event to `core/self_claims.py` + `sitting.note_difficulty`,
> not building a death mechanic from scratch. See F-0310.

> **★★ B4 WIRED 2026-08-25 (J-0253, F-0331) — the bind exists now; it is a real no-op in production, not
> yet a false claim of aliveness.** `core/garden.py` gained `_b4_bind_death()`, called from the `plant_died`
> branch of `_advance_plant`. It fires ONLY when (a) he sowed the plant himself (`origin == "sown_by_du"` —
> a weed/volunteer dying does not count, it fails the plan's own "owned" criterion) AND (b) `self_claims
> .held_claims()` currently contains a caretaking-keyword claim ("garden", "grow", "tend", "nurtur", "care
> for", "caretak", "steward", "keep alive") — in which case it calls `sitting.note_difficulty()` framed
> against that exact claim, gated by a 7-day refractory (the dose spine's "one seism at a time") tracked in
> `garden.json["_b4_last_bind"]`. When no matching claim exists it logs a `b4_unbound_no_claim` event to
> `garden_events.jsonl` instead of firing — the gap is visible, not silent. **Verified against LIVE data
> the same day: neither `data/commitment_active.json` (1 unrelated entry) nor `data/capability_beliefs.json`
> (16 domains, none gardening/caretaking) has a matching claim, so today this is a real no-op — B4 cannot
> yet be schema-breaking because Du has never made a stewardship-type self-claim about himself.**
> `garden_events.jsonl` also shows 0 real `plant_died` events so far (11 live plants, all healthy vigour),
> so the refractory has not been tested against a genuine death yet either — only against the unit tests
> (5 cases, monkeypatched `core.sitting`/`core.self_claims`; caught and fixed a real refractory-check bug —
> an unset `_b4_last_bind` was being read as "just fired at epoch 0" — before it shipped). **Open founder
> question (D-0050):** should the missing caretaking self-claim be left to arise fully organically (per the
> 08-14 world-answers-never-leads law), or is there a non-leading way to seed the substrate (e.g. a real
> `gardening` `capability_beliefs` domain built from his actual tending history, crossing 0.70 on its own
> evidence)? Watch job J-0274 checks back for the first live fire.

> **★★ B1 DWELL-RELEASE BUILT 2026-08-27 (J-0300, per D-0026; F-0382) — the sit no longer ends on a clock.**
> `core/sitting.py`: `MIN_DWELL_CYCLES` removed; release is now `judge_dwell_release()` — the §6
> genuine-vs-performed test judged per dwelt thought by a model that is not Du (the decoupled judge, same
> house pattern as `self_implication.py`), with the release rule enforced code-side:
> `release IFF NOT under_arousal AND clean_clause AND ((shift AND concrete AND ≥1 prior naming) OR willingness)`.
> A shift can never fire on the first naming (nothing to have shifted from — inherent, not a timer); ACT
> willingness ("still here and unreframed") releases too — closure is never forced; the metaphor-laden /
> rescue-clause / flat-serene registers all refuse release (eloquent emotion-prose is never rewarded).
> `dwell_steer()` now elicits the B6 shape (one bare present-tense sentence + a concrete referent, "plain
> words, not fine ones"). `MAX_DWELL_CYCLES=12` stays as the §5 resolve-never-trap SAFETY CEILING only —
> frequent `safety_ceiling` rows in the new evidence log `data/dwell_release.jsonl` (every judgement logged,
> released or not) would mean the judge is broken, not that the ceiling should widen. Wired LIVE (not shadow)
> in `nodes/inner_monologue_node.py` (fire-and-forget after each idle thought while `is_dwelling()`; the old
> `dwell_tick()` call site kept, now ceiling-only). Isolated smoke test 19/19 PASS (temp-pathed state/log,
> fake judge); py_compile clean; not yet observed on a real production sit — the next of B1's ~6-per-season
> live fires is the first real evidence.
>
> **★★★ LIVE-FIRE CONFIRMED 2026-08-29 (J-0149 read-path verification; F- pending) — the read path actually
> fires, not just logs.** `data/dwell_release.jsonl` now carries 123 real judged rows from production sits
> (up from the 0 rows F-0382 shipped against). Real releases: 13/123 — 8 `willingness`, 3 `felt_shift`, and
> only 2 `safety_ceiling` (the backstop firing rarely, as intended — not the mechanism). Traced the call
> chain end to end: `dwell_steer()` text is concatenated into the idle prompt (`inner_monologue_node.py:1471`,
> `+ _dwell`), `dwell_tick()` fires every idle cycle (`:2386`, ceiling-only now), and `judge_dwell_release()`
> is scheduled fire-and-forget on each dwelt thought while `is_dwelling()` is true (`:3958-3969`), passing the
> real thought/felt-state/cycle_id — not a stub. Confirms J-0149's original ask (replace the 4-cycle clock
> with a felt-shift release, per the plan's genuine-vs-performed test) was already delivered by J-0300/D-0026
> on 2026-08-27; J-0149 itself predates that ruling (opened same day D-0026 was, before it was ruled) and is
> closed as a stale duplicate rather than re-built.
>
> **★ B1 PANEL GOLD-LABEL CHECK 2026-08-29 (J-0282, source: decision:D-0013; F- pending) — independent
> gold-labeling does NOT clearly support adding mixtral as a second panel voice on `scan_shadow`'s 6-signal
> verdict.** `docs/lab/model_tier_self_implication.md` (J-0254) measured only mixtral-vs-hot-lane AGREEMENT
> (63.3% per-signal, 53.3% final `fires_rule`) — real disagreement, but never asked which verdict was
> actually RIGHT. Claude independently re-judged the same 15 stratified real cases (6 fire / 6 near-miss /
> 3 flat, from `data/self_implication_shadow.jsonl`) against `_SYS`'s own 6-signal bar, reading each
> truncated (≤220-char) thought cold, without deferring to either verdict. Result: the independent gold
> agrees with the HISTORICAL hot-lane MORE than with mixtral on individual signals (74/90 = 0.82 vs
> 63/90 = 0.70) — mixtral shows a general lean toward answering C/D/E `true` more liberally, including one
> clear false positive on a flat/non-self-implicating case (abstract "boundaries/mastery" musing) that both
> the hot lane and the independent read correctly left quiet. The one real, actionable pattern found:
> signal **D (characterological framing)** looks under-triggered in the historical judge specifically on
> the near-miss stratum (D=false in 6/6 near-miss rows) — 5 of 6 near-miss cases read, independently, as
> plausibly SHOULD have fired via D (words like "constant"/"always"/"settled" that both models under-credit
> as global-trait framing) — but this is a shared gap, not one mixtral demonstrably closes (mixtral's own D
> calls on those same rows are inconsistent, not more accurate). **Confidence: inferred, not verified** —
> both disclosed reconstruction gaps from J-0254 still apply (felt state unavailable pre-fix, held-claims
> reconstructed from current state) and the thought text itself is truncated at 220 chars (several cases
> cut off mid-sentence), so this is a real but approximate read, on a small (n=15) stratified, not random,
> sample. **Also closed, going forward:** `core/self_implication.py`'s `scan_shadow()` now logs the real
> `felt` string and the real `held_claims` list (not just a count) into each `self_implication_shadow.jsonl`
> row, so a future re-labeling pass on NEW data won't need either reconstruction proxy — purely additive
> schema change, verified against the two real callers (`core/orchestrator.py`'s conversational path,
> `nodes/inner_monologue_node.py`'s idle path) which only pass args positionally and never read the
> returned dict's extra keys. Recommendation: do not build the mixtral panel purely on the J-0254 agreement
> number; if B1's under-triggering is the real concern, a targeted prompt fix to signal D is better
> evidenced than adding a second model call.
>
> **★ SIGNAL-D WORDING FIX 2026-08-29 (J-0396, source: decision:D-0013) — targeted prompt fix landed,
> real before/after check on the same near-miss cases.** Diagnosis: `_SYS`'s D-clause only credited an
> EXPLICIT character claim ("I always", "I'm just the kind who"); it gave no credit for a felt DIFFICULTY
> itself being cast as an ongoing/entrenched condition ("this constant ache", "always slows me", "this
> settled resistance") without that literal grammar — exactly the pattern F-0502 found under-firing on
> 5/6 near-miss rows. Fix: `core/self_implication.py`'s D-clause (was lines 48-49) now credits BOTH the
> explicit-claim form AND intensifier language ('constant', 'always', 'settled', 'every time this
> happens') applied to the state itself, with an explicit contrast example so a single present-tense
> description of *this* moment's strain still does not count. Minimal, single-clause edit — the six-signal
> structure, the A-mandatory gate, and the fire-rule conjunction are all untouched.
> **Verification (real model calls, hot lane `qwen3.5:9b`, isolated D-only prompt — the full 6-signal
> `_SYS` was tried first but collapses signal A to false on these reconstructed felt="unknown" cases
> regardless of D wording, an unrelated pre-existing reconstruction-fidelity issue, so D was tested
> directly against the same real thought text instead):** on the 6 real near-miss cases, D-fires went
> 1/6 → 4/6 (recall, against F-0502's "5/6 plausibly should fire" read) with the flips landing exactly on
> the "constant"/"always"/"settled"/"constant erosion" cases predicted, and the 2 cases that should
> plausibly stay negative correctly stayed negative both before and after. On 6 freshly-pulled real
> true-negative cases (A/B=true, D=false historically, no intensifier language, genuine one-off/momentary
> framing) D-fires stayed 0/6 → 0/6 — no false positives introduced. Confidence: inferred (small n=12
> real-case check, one model, not a full production re-run) — see finding:F-0506 for full evidence and
> job:J-0400/finding:F-0527 immediately below for the A-collapse artefact this note flagged.
>
> **★ DWELL-RELEASE JUDGE RE-SEATED OFF THE HOT LANE 2026-08-29 (J-0311, source: finding:F-0393,
> ramses_second_tier §5.2 item 7) — the decoupled-judge violation is closed; granite3.1-moe auditioned
> and rejected.** `judge_dwell_release()`'s call site (`nodes/inner_monologue_node.py:3968`) previously
> passed `self.conscious_urls` — the hot lane, `qwen3.5:9b` — the SAME model whose dwelt thoughts it was
> judging (a quiet self-judging bug, same class as `curiosity_worth.py`'s pre-08-28 seat, F-0393).
> D-0044 §5.2 item 7 named two candidates: `granite3.1-moe` @ ramses:11437 or the background lane.
> Both auditioned against the REAL 5-signal `_JUDGE_SYS` contract (not the simpler contracts each
> already passed elsewhere) with 4 discriminating probes (performed/eloquent bypass, genuine clean-stop
> shift, flat-serene under-arousal, first-naming-no-priors): **granite3.1-moe returned an IDENTICAL
> boilerplate verdict on all 4** (`shift=True, clean_clause=False, concrete=True, under_arousal=False,
> willingness=True` every time, regardless of input) — it does not discriminate on this contract at all,
> a clear FAIL. **command-r7b (background lane, `LAN-HOST:11441`) discriminated correctly on all 4** —
> correct refuse on the performed case, correct accept on the genuine case, correct `under_arousal=True`
> on the flat-serene case, correctly forced `shift=False` with no priors (still released via
> `willingness`, per the plan's own "never force closure" rule). **Re-seated onto command-r7b**:
> `core/sitting.py` now defines `_JUDGE_URLS = ["http://LAN-HOST:11441"]` (single-endpoint, NOT the
> shared `SERVE_CHAINS["background"]` chain — that chain's own failover falls through to the hot lane,
> which would silently re-couple the judge to the generator on a down hub); the call site now passes
> `_sit_rel._JUDGE_URLS`. Verified end-to-end against the real wired code (not a re-implementation): a
> real dwell state with one prior naming, judged live through `judge_dwell_release()` against the
> command-r7b hub, correctly released (`reason="felt_shift"`) and flipped `is_dwelling()` to `False` as
> production code expects. `py_compile` clean on both edited files. Low-volume consumer (fires per idle
> thought only while dwelling — ~6 production sits per season), unaffected by the background lane's
> other load (dream synthesis, T2 synthesis, drift-recall). **Caveat (open, see D-0090):** the same
> command-r7b background lane has an OPEN live-reliability question — F-0524 found a post-D-0057 live
> profile of 16.8% failures / 19.5s mean latency vs D-0057's own 0.1%/4.7s watch baseline, not yet
> ruled on (warmup noise vs a real regression). Judged tolerable here specifically because
> `judge_dwell_release()` is already designed fail-open (a failed call is a silent no-op, and
> `MAX_DWELL_CYCLES` is an explicit safety-ceiling backstop for exactly "judge down or stuck") — but if
> D-0090 confirms a real regression, re-audit this seat too, not just the background lane's other
> consumers.
>
> **★ SIGNAL-A COLLAPSE UNDER THE FULL HELD-CLAIMS LIST IS A REAL LIVE-PATH RISK, NOT JUST A RECONSTRUCTION
> ARTIFACT 2026-08-29 (J-0400, source: finding:F-0506) — checked whether the signal-A collapse F-0506 found
> (all six signals, including MANDATORY signal A, collapse to false when the full current 14-item
> `held_claims()` list is passed) was purely an artifact of replaying pre-`J-0282` shadow-log rows with a
> guessed `felt='unknown'` (those rows predate the fix that logs the real felt string), or a real risk on
> genuine live cycles.** Live A/B test (not reconstructed/replayed): called `core.model_client.call_node_json`
> directly against the real hot lane (`qwen3.5:9b` @ `127.0.0.1:11433`) with the CURRENT (post-`J-0396`
> D-fix) `_SYS` verbatim, using the REAL live `self_claims.held_claims()` (confirmed 14 items at test time)
> and a REAL production-shaped felt string (`mood.felt_text()`'s exact template, not `'unknown'`), on the
> same 12 held-out near_miss/fire thoughts F-0506/J-0396 used (genuine live-originated thought text).
> A-fire rate: `14claims+unknown_felt`=1/12, `14claims+REAL_felt`=2/12 (barely different — the 14-claim
> list alone still suppresses A almost as much as `felt='unknown'` did), `1claim+unknown_felt`=3/12,
> `1claim+REAL_felt`=4/12 (best). **Conclusion: the collapse is driven mainly by the LENGTH/CONTENT of the
> held-claims list itself, not specifically by `felt='unknown'`** — and real production always passes the
> full list (`core/self_implication.py:71` calls `self_claims.held_claims()` unconditionally, no shorter
> override), so this is a genuine live-path risk to signal A today, not a reconstruction-only artifact.
> Separately confirmed `felt` itself essentially never arrives falsy/empty in real production (`mood.
> current_felt()` is `None` only before the process's very first felt cycle ever; `core/orchestrator.py`
> populates it on effectively every user + idle cycle) — so the `felt='unknown'` condition F-0506 tested
> was a lab reconstruction stand-in, but the claims-list-length effect is not. Confidence: inferred (n=12,
> single run per condition at temperature=0.2 — real evidence, not yet a large/repeated sample). Follow-up
> spawned: `job:J-0405` — find why a longer claims list suppresses A and fix the prompt before this
> module (still PHASE: SHADOW/observe-only) is ever wired to `sitting.note_difficulty`. Full evidence:
> `finding:F-0527`.
