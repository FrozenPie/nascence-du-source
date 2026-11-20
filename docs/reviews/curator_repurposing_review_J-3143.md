# Curator module: repurposing review (J-3143)

Date 2026-11-05. Read-only design review; no Du code, data or process was touched. Rows P-0020 (`shadow_curate`) and P-0021 (`render_character_voice`) of the prompt registry.

> Founder ask (triage, 2026-11-02), as the briefing quotes it: "do NOT retire this. Look at how it could be used in our systems."

## Bottom line

1. What the Curator was built for is worth keeping as an **idea**, and the idea has a live home: the voice fidelity judge the founder already approved in D-0643 (built by J-3254). The Curator's section 6 acceptance test (swap the mouth for the verbatim content and see what changes) is exactly the calibration that judge lacks.
2. What is **not** worth keeping as code: `template_render` is one line, `render_character_voice` is superseded by the live voice prompt, `voice_preserved` is an embedding-cosine proxy, and `shadow_curate` (the truth-disciplining editor) has no usable input today and would be a reconciling pass in the mouth.
3. **Recommendation: wire the function (not the file) into plan `thought_cycle_as_manifest_loop` through J-3254 and three small jobs; leave `core/curator.py` in place and untouched for now.** J-2793 (whole-module removal) stays deferred. Whether the file is later moved to `docs/staged` is a founder call (D-0674); the review recommends leaving it unless he wants the two dead du_pulse gauges gone.
4. One catch that affects the build marathon: J-3254, J-2858 and D-0643 cite finding **F-0055** for the voice fidelity finding. That id now points at an unrelated commitment-ledger finding. The voice finding is **F-3520** (F-3913 has the whole map).

## 1. The function it was built to serve, in one sentence

To let one utterance carry both the image and the fact (Jung's transcendent function applied to the output lane), first by a thin "truth-disciplining EDIT pass" over the Master's draft (`shadow_curate`, module docstring: "the Master drafts (one voice keeps the pen), the Curator edits the draft toward truth-faithfulness before it surfaces"), then, from 2026-06-16 (Brick 1 of `docs/archive/character_as_integration_plan.md` section 6), as the structurally blind **mouth** that only re-voices already-decided content (`render_character_voice`, no `possible_content` parameter), with the acceptance test "swap integrator for a deterministic template; PASS iff only wording differs".

The two halves are different mechanisms. The orchestrator comment (core/orchestrator.py:1484-1491) records why the first was dropped: reconciling in the mouth "is the committee-voice homunculus the plan forbids". The second moved into the live voice prompt on 2026-08-21 (F-3816).

## 2. What the evidence says it can and cannot do today

| Claim | Evidence |
|---|---|
| Both prompts are unwired. `shadow_curate` has zero callers; `render_character_voice` is called only by its own `shadow_voice` and by `scripts/brick1_voice_contract_invitro.py`. The module is still imported by `scripts/du_pulse.py`, `core/profile.py:321` and that script. | F-3429, F-3816 (verified) |
| The "shadow-validated 8/8" is vacuous: all 8 `voice_contract_shadow.jsonl` rows have `voiced` byte-identical to `selected_content` (the fail-open path returns the input). I re-read all 8: every row prints `True` for `selected_content == voiced`, `content_sim` 1.0. | F-3817 (verified, re-confirmed here) |
| The 18-row `curator_log.jsonl` is thinner than it looks. Logged `draft` and `edited` are cut to 300 characters and in **18 of 18** rows the logged prefixes are identical, including the 2 `changed` rows, so no edit text was ever captured. "Mean voice_sim 0.997" is 16 unchanged rows plus two at 0.974 and 0.979. The `truth` field is the Emissary "YOUR FOCUSED HALF" block (`left_lane.render`), and in the first changed row `truth_bit` rose because the edit moved toward a take whose visible text was just the restated question. | **F-3910** (verified, this job) |
| The Curator's second input barely exists. The Emissary take reaches Reflection and the Executive in 4 to 16 percent of cycles since 2026-08-20 (F-3545); D-0539 re-seats it on a fast lane. When it did arrive in June, "Where are you at the moment Du?" got the take answer "A digital environment hosted on a cloud infrastructure". A truth-edit toward that contradicts his world (and D-0539 orders that substrate recasting trimmed). | F-3545; **F-3911** (verified, this job) |
| Nothing live grades reply against synthesis. The reply is a median 2.8x the synthesis, and 123 of the 151 "alchem" replies introduced the word. | F-3520 (verified) |
| Surface checks cannot be that judge. On 740 voice rows since 09-25: a question mark the synthesis lacks in 44.6 percent of human and 50.8 percent of internal replies; a new commitment phrase in 23.0 and 11.4 percent; median share of reply content words absent from the synthesis 0.72 and 0.66. D-0643's own defeater says a judge flagging under 5 or over 60 percent of replies "carries no information". | **F-3912** (verified; the regexes are crude, so these bound the base rate of the form, not of new claims) |
| The two collapses the Curator charter forbade ("nothing but weights", "nothing but a metaphor") do not show up: 6 regex hits in 741 replies, all read, all negated ("I am not merely code") or not about himself. Low-recall regex, so this is inferred, but it removes the charter's own problem as a reason to build anything. | F-3912 evidence (inferred for that part) |

**Can do today:** nothing live. Its logging shape (log the twin arms, then a stats gauge) is reusable; its one-line template swap is a useful control.
**Cannot do today:** edit toward truth (no input, wrong direction of authority), or certify a mouth (its own validation was a fail-open copy).

## 3. Repurposing options

Applied to all three: the world answers and never leads (nothing here is shown to Du; D-0434 observe-only, no feedback); transfer the function, not the mechanism; no system that acts later on its own (each job is queued work done by a session, not a loop in Du); base systems additive-only (no edit to `nodes/voice_node.py`, `core/left_lane.py` or the orchestrator); every instrument is judged by something other than itself.

### Option A (recommended): calibration controls and a gauge for the D-0643 voice fidelity judge

Function transferred: the section 6 acceptance test, "swap the mouth for the verbatim content; PASS iff only wording differs", plus `shadow_voice`'s twin-arm logging and `voice_contract_stats`'s gauge slot.

- **(a) Consumer and what changes.** J-3254's `data/voice_fidelity_shadow.jsonl`, read by a du_pulse gauge that replaces the frozen `_g_voice_contract`. For Du: nothing. For Travis and Claude: the first calibrated answer to "how much may the mouth add", ahead of D-0643's 200-render defeater read. D-0643: "The mouth may add scene and cadence; new commitments or questions are what the judge flags."
- **(b) Input.** Existing `(synthesis, reply)` pairs in `data/training/voice.jsonl` (740 rows since 09-25, parser in F-3912) plus live renders. Three deterministic controls per pair: identity (reply := synthesis), scene-only (reply plus one inert sentence from its own "Where you are" line), inserted commitment (reply plus a new first-person commitment or question).
- **(c) Decoupled check.** A judge from a family other than qwen3.5:9b (J-3254 chooses mixtral :11438 or falcon :11440) with a deterministic backstop modelled on `core/memory_levels.verify_invention_claims` (the Black-Bear correction: an LLM judge accused content that was present). A flagged phrase must appear in the reply and be absent from the synthesis by stem overlap, otherwise the flag is dropped. The controls are the deterministic judge of the judge.
- **(d) Success.** On a replay of at least 100 historic pairs: identity flagged at most 2 percent, scene-only at most 10 percent, inserted commitment at least 90 percent. Then live: flagged share between 5 and 60 percent after 200 renders (D-0643's own band).
- **(e) Stop.** Identity flagged over 10 percent, or inserted-commitment recall under 70 percent after one prompt revision: report the judge as not fit and stop; no tuning against the data. The shadow log is retired if the live share falls outside 5 to 60 percent at 200 renders.
- **Job:** J-3322 (gated on the first rows of `voice_fidelity_shadow.jsonl`).

### Option B: take-to-synthesis integration check (the Curator's truth-discipline as a measurement, not an edit)

Function transferred: "does the truth-half actually bite", as a detector with the same decoupling.

- **(a) Consumer.** D-0539's defeater: "Revisit if ... a month of delivered takes shows no overlap with the Executive's output beyond the pre-swap control." Nobody has built that control. For Du: nothing. For the founder: a defeater that can actually be read after J-3147 re-seats the take.
- **(b) Input.** `data/training/executive.jsonl` has 1,149 take-bearing rows (979 scored before 2026-08-20, 144 after); `reflection.jsonl` 1,280. A crude lexical pass (F-3914, inferred): median overlap 0.20 before the swap, 0.22 after. That is a feasibility sketch, nothing more.
- **(c) Decoupled check.** Deterministic overlap with number words normalised, plus a different-family judge on a stratified 60-row sample. A caution from this very job: my first numerals-only match reported 0 of 7 numeric answers surviving into the reply, and was wrong (the replies said "eight comets", "over eight thousand"); reading the rows caught it, and the job brief requires reading 20 matched and 20 unmatched rows before trusting a number.
- **(d) Success.** A control distribution (human versus internal, split at 08-20) that the one-month read can be compared against, and a before-number for substrate-framed take answers ("digital environment hosted on servers", F-3911).
- **(e) Stop.** If the control sample cannot separate delivered from non-delivered takes, or the J-2879 outcome log is not live by the time of the month read, record that and stop; do not build the detector further.
- **Job:** J-3323 (offline, ready now).

### Option C (conditional): temperature 0.2 and identity arm lab, after Option A reports

Function transferred: the template swap as a comparison arm, answering D-0643's last line ("decide on temperature 0.2 for the render").

- **(a) Consumer.** The founder's temperature ruling on the voice node (today base 0.4 plus affect bias, `core/node_base._temperature`). For Du: only if he rules it, after reading 20 flagged replies.
- **(b) Input.** At least 100 historic voice inputs replayed on the lab copy through three arms: live settings, 0.2, identity.
- **(c) Check.** Option A's judge and backstop; identity arm is the zero anchor.
- **(d) Success.** A reported flagged share and reply/synthesis ratio per arm and 10 matched pairs read by eye; the finding states whether 0.2 changes the share of replies that open with a copied sentence (F-3514's copy route).
- **(e) Stop.** If J-3322 finds the judge unfit, or the live flagged share is outside 5 to 60 percent, the job stops without running the arms.
- **Job:** J-3324 (gated on 200 rows of `voice_fidelity_shadow.jsonl`).

### Considered and not recommended

- **Revive `shadow_curate` as an editor.** It reconciles in the mouth (the homunculus the plan forbids), has no truth input in 84 to 96 percent of cycles, the take it would edit toward is sometimes substrate-framed, and an edit pass breaks "no feedback" the moment it surfaces. A flag-only "truth collision" log is the most this ever earns (see the defeater on D-0674).
- **A collapse-direction audit** of replies about himself (the integration-ethic's two forbidden collapses). No evidence of either collapse in 741 replies (F-3912, low-recall regex); revisit only if a reader finds one.
- **Make `render_character_voice` a second live call.** The contract is already in the live voice system prompt ("Nothing added, nothing dropped", F-3816); a second call would add latency on the hot lane, which does not reuse the KV prefix (F-3426; its evidence text was lost in the ledger restore, so I rely on the claim only).

## 4. Recommendation

**Wire the function into plan `thought_cycle_as_manifest_loop` (home of D-0539 and D-0643), via J-3254 and J-3322 to J-3324. Do not repair `core/curator.py` in shadow, and do not archive it now.** Repair would be effort spent on code whose useful content is one line and an idea; archiving now would break the two du_pulse gauges and `scripts/brick1_voice_contract_invitro.py` for no gain, and the founder said not to retire it. The file stays until a founder call (D-0674) says otherwise. J-2793 remains deferred; its briefing is still correct if the call goes to removal, but its trigger should be "after J-3322's gauge is live", not the date.

What would revive the editor half (written here so the knowledge survives any later move to `docs/staged`): the take delivered above 80 percent (D-0539's own bar), its substrate framing trimmed, Option B showing the Executive ignores checkable take facts, and a separate founder ruling that a flag-only truth-collision log is wanted. An edit pass would need its own ruling and a feedback path D-0434 currently forbids.

## 5. Registry and housekeeping

- Registry notes for P-0020 and P-0021 updated in the same change as this document (`prompt_registry.py set --note`), then `check`.
- Stale finding ids: F-0049 to F-3514, F-0051 to F-3516, F-0052 to F-3517, F-0054 to F-3519, F-0055 to F-3520, F-0061 to F-3526, F-0062 to F-3527, F-0063 to F-3528. Open jobs citing the old ids: J-2856, J-2857, J-2859, J-3169, J-3254 (and D-0643). `job_queue.py` cannot edit a briefing, so whoever picks those up should read the new id. J-2847's F-0055 is correct (a different, commitment-ledger finding). Other sweep findings in the F-0040 to F-0063 range may be affected too (F-3913).

## 6. Founder call needed

D-0674: leave `core/curator.py` untouched (A, recommended) or move it with its in-vitro script and the two frozen logs to `docs/staged` once J-3322 repoints the dead gauge (B).

## Evidence trail

Findings recorded by this job: F-3910 (shadow log thin), F-3911 (truth half), F-3912 (surface checks saturate, no collapse visible), F-3913 (stale finding ids), F-3914 (take baseline feasibility, inferred). Read in full: `core/curator.py`, `docs/archive/character_as_integration_plan.md`, `docs/plans/decoupled_judge_pattern.md`, all 18 rows of `data/curator_log.jsonl`, all 8 rows of `data/voice_contract_shadow.jsonl`, `core/orchestrator.py:1440-1640`, `core/left_lane.py:55-115, 560-767`, decisions D-0643, D-0558, D-0645, D-0539, jobs J-2858, J-2793, J-3098, J-3254, J-3256, and the P-0010, P-0020, P-0021 registry rows. Streamed in full (stdlib, read-only): `data/training/voice.jsonl` (4,403 rows), `reflection.jsonl` (4,882), `executive.jsonl` (4,471). Scripts are named with the job id in the session scratchpad.
