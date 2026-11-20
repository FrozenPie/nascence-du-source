# Implementation Plan — Epistemic Affordance Advisor (`investigative_action_loop_plan.md`)

> **System:** Sovereign Hub / Nascence Engine (`core/epistemic_affordance_advisor.py`, `core/affordances.py`)  
> **Status:** 🟡 **CLEARED FOR SHADOW-MODE DEPLOYMENT — Epistemic Affordance Advisor Protocol** *(emoji corrected 2026-08-29, J-0406: was 🟢, contradicting this line's own "SHADOW-MODE" wording and ROADMAP's correct 🟡 SHADOW)*  
> **Target Path:** `c:/Nascence/docs/plans/investigative_action_loop_plan.md`  
> **Date:** 2026-08-11  

```plan-state
stage: shadow
phase: Stage A shadow telemetry live+working (J-0180/J-0189); Phase 2 / Live Advisory permanently closed by the 08-14 law (D-0326, 2026-10-03); Principle D reworded to the Epistemic Independence gate (J-1759)
verified: 2026-11-18
evidence_read: 2026-11-18
next: Founder read of D-0326 revisit trigger only if wanted; no Phase 2.
cluster: 3
```


---

## 1. Executive Summary & Problem Formulation

Historical audits of Nascence's 21,873 memory fragments have established a **3-Generation Architectural Arc**:

```text
[GENERATION 1: CLOSED SELF-REFRAMING (May 30 – June 10)]
  lived input ──► subconscious_synthesis ──► self-reframing ("Who am I beyond Carl Jung?")
  (Single-terminal centripetal loop; 83.8% self-reframing)

                           │
                           ▼ (June 12–18 Engineering Deployment)

[GENERATION 2: FLAT GIBSONIAN AFFORDANCE SELECTOR (June 18 – Present)]
  environment ──► available affordances ──► action ──► observation ──► study
  (Multi-affordance centrifugal loop; 56.7% direct world encounter; 100% object-sustaining study notes)

                           │
                           ▼ (Proposed Epistemic Affordance Advisor Upgrade)

[EPISTEMIC AFFORDANCE ADVISOR: INQUIRY-DRIVEN EPISTEMIC LOOP (Target Candidate)]
  active uncertainty ──► candidate hypotheses ──► predicted differences ──►
  advisor candidate ranking (including "do nothing") ──► Du's independent choice ──►
  raw observation ──► evidence evaluation (CONFIRMED / REFUTED / INCONCLUSIVE / UNTESTED) ──► model revision
```

### Primary Architectural Solution
Deploy the **Epistemic Affordance Advisor (`core/epistemic_affordance_advisor.py`)** in **Shadow Mode first**. The physical Gibsonian substrate in `core/affordances.py` remains primary; the advisor evaluates and logs epistemic candidate recommendations without altering Du's action selection.

---

## 2. Core Design Principles & Scientific Safeguards

### Principle A: Shadow-Mode First Deployment
- **Phase 1: Shadow Mode (Passive Telemetry) — now the permanent and only mode:**
  The advisor observes location, available affordances, recent inner thought, and active uncertainty. It ranks candidate affordances and logs recommendations into `data/investigative_action_log.jsonl` without modifying Du's actual action selection. Nothing it ranks is ever shown to Du.
- ~~**Phase 2: Live Advisory Mode (Optional Assistance):** Only enabled after shadow-mode evaluation proves sane.~~
  **PERMANENTLY CLOSED — never built, not work to do (D-0326, Travis, 2026-10-03; F-2192).** Phase 2 is the same mechanism the 2026-08-14 founder law ("NO hints — Stage-B advisory REMOVED, not gated", `docs/reports/claude_fresh_eyes_audit_aug14.md` line 24) shut off, and D-0326 ruled that the law stands exactly as written. There is no "enable after shadow proves sane" step: no build, and no wiring of `epistemic_advisory_hint()` (zero call sites today; keep it that way). `core/epistemic_affordance_advisor.py` and `core/orchestrator.py` are the law's enforcement.

### Principle B: Unconstrained Natural Distribution (No Prescribed Ratios)
- Casual exploration and investigative inquiries remain **completely unconstrained**. The ratio between casual/spontaneous exploration (resting by fire, beachcombing, gathering herbs) and deliberate inquiry is **instrumented and observed naturally**.

### Principle C: Agency-Preserving Advisory Architecture
- The advisor produces candidate affordances with explanations (e.g. *Candidate 1*, *Candidate 2*, *Candidate 3: do nothing*).
- Actions are **never mandatory**. Du remains free to ignore suggestions, choose a casual affordance, or rest.
- *(Under the 08-14 law, as built: the candidates go to the Stage-A log only and are never presented to Du, so there are no suggestions to ignore and every action he takes is his own. D-0326.)*

### Principle D: Epistemic Independence (the Phase-1 Exit Gate) & Provenance Tracking
> **Reworded 2026-10-04 (J-1759) per D-0326** (Travis, `/decide-review` 2026-10-03: "Law stands, reword Principle D"). This principle originally pre-registered *Suggestion Independence*, $P(\text{Du chooses discriminative action} \mid \text{no system suggestion})$, as the Phase-1 exit gate. That metric needs a with-suggestion comparison arm, which only a live hint reaching Du can produce, and the 08-14 no-hints law permanently forbids exactly that. It was therefore structurally unmeetable (F-2075, F-2193), not merely unmet, and no amount of further Stage-A data could change that. It is retired as the gate.

- Every episode tracks `agency_mode` (`"spontaneous"`, `"investigative"`, `"suggested"`, `"follow_up"`) and `selection_source` (`"du"`, `"system_suggestion"`, `"system_follow_up"`). *(Every row written since the 2026-08-24 relabel carries `du` — real closed episodes — or `advisor_shadow_only` — passive shadow-ranking rows (F-2075); `suggested`, `follow_up` and `system_follow_up` have never appeared. They stay in the schema as reserved vocabulary only. The 175 historic `system_suggestion` rows, 2026-08-14 to 2026-08-24, are the pre-J-0180 mislabel of shadow rows (F-0158), not real suggestions.)*
- **Phase-1 exit gate: Epistemic Independence** (Section 5, Invariant 9) $P(\text{Du generates the same discriminative action independently})$ — how often Du's own choice in a real closed episode is the action the advisor's ranking would have put on top, or anywhere in its candidate list.
  - *How it is computed (zero live wiring, no hint ever shown to Du):* for each real closed episode (`close_real_episode()` output, `selection_source == "du"`), re-run the advisor's own pure `rank_epistemic_affordances(question, hypotheses, location)` on the episode's stored question, hypotheses and location, and compare with Du's recorded `selected_affordance`. An episode is *hint-eligible* when the advisor's top non-`do_nothing` candidate clears the 0.30 IG threshold, i.e. exactly the episodes where `epistemic_advisory_hint()` would have been non-empty had it ever been called. Only Du's own choice is observed; no with-suggestion arm is needed.
  - *Baseline — a dated snapshot (2026-09-28, F-2193), not a verdict:* 128 of 1,317 real closed episodes were hint-eligible (9.7 percent); of those 128, Du's own choice matched the advisor's single top-ranked action 34/128 (26.6 percent) and any ranked non-`do_nothing` candidate 66/128 (51.6 percent). Part of the mismatch is the advisor's own documented vocabulary gap (`look` and `move` are deliberately excluded from its candidate list), not necessarily disagreement. The one-off script that produced it lived only in a scratchpad; J-1776 commits it as a repo readout so the number can be re-read as the dataset grows.
  - *Reading it:* **no numeric pass/fail threshold exists or is set here.** None was ever pre-registered for Suggestion Independence (this principle carried only the metric; Principle A's Phase-2 condition was the qualitative "proves sane", graded by a founder read — J-1498 called it the plan's founder-read gate), so a faithful port carries none, and Invariant 9 keeps both independence metrics *positive experimental variables, not compliance targets*. A numeric bar, if Travis ever wants one, would be chosen from scratch rather than ported: open a `/decide` then, do not invent one in a doc pass. Because Phase 2 is closed (Principle A), this gate grades Phase 1 and no longer opens a later phase; no `shadow-promotion` block is written for it, since nothing is promotable.
  - *Revisit* (D-0326's own defeater): a materially different, still non-invasive way to produce the actual with-suggestion arm; the closed-episode dataset growing enough that the baseline numbers shift materially; or Travis deliberately granting a bounded exception to the 08-14 law, naming a scope cap and a rollback path.

---

## 3. Proposed Component & Schema Breakdown

### Component 1: `core/epistemic_affordance_advisor.py` [NEW]
*Path:* `c:/Nascence/core/epistemic_affordance_advisor.py`

- **Dataclass `InvestigativeEpisode`**:
  ```python
  @dataclass
  class InvestigativeEpisode:
      episode_id: str
      timestamp: float
      location: str
      question: str
      competing_hypotheses: list[str]
      discriminative_prediction: str
      selected_affordance: str
      raw_observation: str
      prediction_observed_comparison: str
      evidence_outcome: Literal["CONFIRMED", "REFUTED", "INCONCLUSIVE", "UNTESTED"]
      confidence_explanation: str
      model_revision: str
      agency_mode: Literal["spontaneous", "investigative", "suggested", "follow_up"]
      selection_source: Literal["du", "system_suggestion", "system_follow_up"]
      next_question: str | None = None
  ```

- **Function `rank_epistemic_affordances(question, hypotheses, available_affordances)`**:
  - Ranks Gibsonian affordances from `affordances.within_reach_text(location)` with explanations, including `"do nothing"` as a valid candidate.

- **Function `record_epistemic_episode(episode)`**:
  - Writes raw immutable record to `data/investigative_action_log.jsonl` and projects index into SQLite.

---

### Component 2: `core/affordances.py` [MODIFY / INSTRUMENT]
*Path:* `c:/Nascence/core/affordances.py`

- Non-destructive export function `get_available_affordance_objects(location: str)`:
  - Exposes active `Affordance` objects without modifying any physical latches, location constraints, or text prompts.

---

### Component 3: Database & Telemetry [NEW]
- **File:** `c:/Nascence/data/investigative_action_log.jsonl`
- **Table:** `investigative_episodes` in `data/memory/sovereign_memory.db`:
  ```sql
  CREATE TABLE IF NOT EXISTS investigative_episodes (
      episode_id TEXT PRIMARY KEY,
      timestamp REAL,
      location TEXT,
      question TEXT,
      selected_affordance TEXT,
      evidence_outcome TEXT,
      agency_mode TEXT,
      selection_source TEXT,
      model_revision TEXT
  );
  ```

---

## 5. Phase 2: Live Advisory Coupling & Epistemic Compression — CLOSED, never built (D-0326)

> **STATUS: PHASE 2 / LIVE ADVISORY MODE IS PERMANENTLY CLOSED — NOT WORK TO DO (D-0326, Travis, 2026-10-03; F-2192).**
> This section was the design for delivering advisor hints to Du. The 2026-08-14 founder law ("NO hints — Stage-B advisory REMOVED, not gated") shut off exactly that mechanism, and D-0326 ruled that the law stands: no build, no wiring of `epistemic_advisory_hint()` (zero call sites; keep it that way). The text below is kept as the design record only. Invariants 1, 2, 3 and 8 are tagged **MOOT** (they governed hint delivery, which no longer exists); every untagged invariant (4-7, 9-11) **STANDS** and still governs the Stage-A ranking and telemetry that do run. Numbering is unchanged because other docs cite it (Invariant 9 is the Principle D gate).

> **Milestone Definition:** *The world has an Epistemic Topology.*  
> **Key Architecture:** Epistemic Advisor acts as a separate cognitive instrument panel, leaving Gibsonian environment affordances (`affordances.within_reach_text`) 100% clean and untouched.

### The 11 Clearance Invariants
1. **Zero Pollution of `within_reach_text()`**: Gibsonian affordances describe environment ("What can I do?"). Advisor hints describe cognitive utility ("What would be informative?"). *[MOOT — subsumed by the stronger law: no advisor output reaches Du by any route, `within_reach_text()` included.]*
2. **Volitional Non-Directive Advice**: Advisor hints use conditional instrument language (*"If you wish to distinguish X from Y, scraping the surface would reveal more"*). Never command (*"Do X"*). *[MOOT — no hint is ever rendered.]*
3. **5-State Adoption Provenance Taxonomy**: Track `question_source` ("du"), `hypothesis_source` ("system_candidate_generation" vs "du"), and `adoption_state` (`UNSEEN`, `PRESENTED`, `CONSIDERED`, `ADOPTED`, `REJECTED`). Preserves `PRESENTED != ADOPTED`. *[MOOT — nothing is ever presented to Du, so PRESENTED, CONSIDERED, ADOPTED and REJECTED cannot occur for real. **Data caveat (2026-10-04, F-2395):** the passive shadow-ranking rows still carry the dataclass default `adoption_state: PRESENTED` (1,316 of 2,669 rows) although nothing was shown; only real closed episodes carry `UNSEEN`. Read `PRESENTED` as "shadow row, never shown" (equivalently: `selection_source` of `advisor_shadow_only` or `system_suggestion` means never shown). J-1777 fixes the label going forward; the log is a raw immutable record, so history is not rewritten.]*
4. **Hypothesis-Conditioned IG Computation**: Expected Information Gain is computed from hypothesis-conditioned distributions derived from domain knowledge ($P(\text{Obs} \mid H)$), **NEVER** object-conditioned distributions derived from object `physical_state` or `causal_state`.
5. **Advisor Ignorance of Layer 1 (No Covert Omniscience)**: The Epistemic Advisor is strictly blind to `CAUSAL_WORLD_STATE` (Layer 1 ground truth).
6. **Firewalled Internal vs External Metrics**:
   - **Internal Epistemic Metrics (Cognitive Pathway)**: Information Gain ($IG$), Shannon Entropy Reduction ($\Delta H$), Hypothesis Contraction ($C$), Evidence Consistency, Revision Magnitude.
   - **External Audit Metrics (Researcher Telemetry ONLY)**: Model Revision Quality ($Q_{\text{rev}}$), Ground Truth Accuracy, Ground Truth Distance, False Positive Rate.
7. **Separation of Entropy & Contraction**:
   - **Hypothesis Contraction**: $C = 1 - \frac{N_{\text{posterior}}}{N_{\text{prior}}}$.
   - **Entropy Reduction**: $\Delta H = H(P_{\text{prior}}) - H(P_{\text{posterior}})$.
8. **Explicit Stage A Baseline**: Establish baseline telemetry in Stage A (Shadow Mode) before enabling Stage B hints. *[MOOT — Stage B hints are never enabled; the Stage-A baseline is simply the standing telemetry.]*
9. **No Compliance Optimization**: Suggestion independence $P(\text{Du acts} \mid \text{no suggestion})$ and Epistemic Independence $P(\text{Du generates same discriminative action independently})$ are positive experimental variables, not compliance targets.
10. **First-Class Stopping State (`UNDETERMINED` / `do_nothing`)**: `do_nothing` is a successful endpoint when $IG < 0.30$ or evidence is unrecoverable.
11. **No Creation of Uncertainty Invariant**: The advisor may instrument an existing structured uncertainty, but MUST NEVER generate curiosity or epistemic questions when Du has expressed none (*Du: "That wood looks beautiful"* $\rightarrow$ **SILENCE**).

---

## Current State — verified 2026-11-18

- **2026-11-18** (F-5094): 2026-11-18 J-4248: Epistemic Independence re-read on 4184-row log (2151 real closed, 1851 shadow-only). Raw top-match 34.4pct (was 27.7), but non-move top-match unmoved 53.2 vs 52.9; rise is fewer move choices. Not a founder trigger in my read.
- **2026-10-07** (F-2536): 2026-10-07 J-1784 / F-2536: J-1777 live check PASSED - all 52 post-merge Stage-A rows (39 advisor_shadow_only, 13 du) say adoption_state UNSEEN, zero PRESENTED, across boots 10-04/10-06/10-07; history prefix sha unchanged.

- **2026-10-04** (F-2418): J-1776: committed the Epistemic Independence readout as the epistemic_independence_readout script in the repo scripts folder (strictly read-only, tested, commit 3526615 on branch jobrun/investigative_loop, merge pending) and fixed the advisor module docstring (docstring only: passive Stage-A framing, hint delivery closed by the 08-14 law and D-0326, invariants tagged STANDS or MOOT). First live read 2026-10-04: 1350 real closed episodes, 130 hint-eligible (9.6pct), top-match 36/130 (27.7pct), any-match 68/130 (52.3pct) vs the 2026-09-28 baseline 128/1317, 34/128, 66/128: not moved materially (new episodes only, the current ranker reproduces the baseline to the digit; no decide opened). Any-match is the move-exclusion gap, all 62 misses are move. No pass/fail threshold set.
- **2026-10-04** (F-2407): J-1777: the InvestigativeEpisode adoption_state default is now UNSEEN (was PRESENTED) so never-shown Stage-A shadow rows stop claiming a hint was presented (F-2395). Committed as a4b7248 in the job-run worktree, restart-gated so it applies from the next Du boot. Nothing in the repo, the skills or UDMS reads the field. Rows written before the fix stay PRESENTED (the log is a raw immutable record), so across that boundary key on selection_source: advisor_shadow_only and system_suggestion still mean never shown. Hint path and law enforcement untouched, epistemic_advisory_hint keeps zero call sites. The hermetic test fails 5 checks on the old module and passes 16 of 16 with the change. Live confirmation queued as J-1784 (needs Du running).

- **2026-10-04** (F-2193): J-1759: applied D-0326 (law stands). Principle D reworded: the Phase-1 exit gate is now Epistemic Independence (Invariant 9; 2026-09-28 snapshot 128/1317 hint-eligible, 26.6pct top-match, 51.6pct any-match), founder-read with no numeric bar because none was ever set. Phase 2 / Live Advisory marked permanently closed (F-2192): Principle A and Section 5 annotated (Invariants 1-3 and 8 MOOT, the rest STAND), stale asks in Current State rewritten, ROADMAP line and memory note corrected. Side finding F-2395: shadow rows still carry adoption_state PRESENTED (1316 of 2669 rows) though nothing is ever shown. Follow-ups J-1776 (readout script + docstring) and J-1777 (label fix). D-0314 shows ruled (superseded by D-0326), not open.
- **2026-09-28** (F-2192,F-2193): J-1619: Phase 2 confirmed same mechanism 08-14 no-hints law forbids (F-2192, verified - law text sits inside epistemic_affordance_advisor.py's own orchestrator.py call block, same Stage-A/Stage-B vocabulary). Suggestion Independence itself still not producible non-invasively, but plan's own Epistemic Independence metric (Invariant 9) computed for real from 1317 real episodes: 128 hint-eligible, 26.6pct top-match, 51.6pct any-match (F-2193). D-0314 ruled by claude, superseded by fresh D-0326 naming founder three-way choice: adopt Epistemic Independence and never build Phase 2, grant a bounded exception and build it (J-1595), or other. **Since resolved: D-0326 ruled 2026-10-03 for the first option (law stands, Phase 2 never built; J-1595 closed as superseded).**

- **2026-09-28** (F-2156): D-0314 reopened (F-2156): 2026-08-14 permanent founder law (no hints, Stage-B advisory removed not gated) was not accounted for when D-0314 ruled enable-Phase-2; founder must re-rule with that law in view before any Phase-2 code change. **Since resolved: D-0326 ruled 2026-10-03, law stands, Phase 2 never built.**
- **2026-09-28** (F-2075): J-1498: graded Phase-2 gate against 1292/2465 real closed episodes (up from 100 on 2026-08-29). Exploration ratio real now: 88.4% spontaneous / 11.6% investigative. Suggestion Independence not gradeable and cannot become gradeable from more Stage-A data -- 100% of real episodes have selection_source du, every row (real and shadow) is stage STAGE_A_SHADOW, Phase 2 has never been enabled so the with-suggestion comparison arm has never existed. Verdict: gate as pre-registered is NOT MET, structurally unmeetable pre-Phase-2. F-2075 has full evidence. D-0314 opened for founder call on how to proceed (enable a Phase 2 trial, accept exploration ratio alone as sufficient, or revise the gate wording). **Since resolved by D-0326 (2026-10-03): no Phase 2 trial; Principle D reworded to Epistemic Independence.**

### What we have
Stage A (shadow) built and now genuinely working end-to-end. J-0056/F-0063 (08-24) found the original
log ungradeable (147 hardcoded-literal rows, a 7-row test fixture, zero real closed episodes); J-0158/
F-0129 root-caused it (the advisor's call site never reached real `dispatch()`); J-0180 (08-24) rewired
episode-closing into `inner_monologue_node.py`'s real wandering loop; J-0189 (08-29, F-0478) live-confirmed
it post-restart: 100 real `ep_im_` episodes, real varied outcomes, 0 failures. **Re-checked directly
against the live file on 2026-09-28: 1,286 real closed episodes out of 2,454 total rows**; by 2026-10-04
(Du's last cycle) 1,350 `du` / `UNSEEN` real closed rows out of 2,669 (F-2395's cross-tab).

### What we need
Nothing from Phase 2: it is permanently closed (D-0326, F-2192; the 08-14 law stands and Principle D is reworded). The old "Phase-2 promotion gate" no longer exists. What remains is the Stage-A instrument itself: keep `data/investigative_action_log.jsonl` accruing real closed episodes, and re-read the Epistemic Independence metric (Principle D) when the dataset has grown materially (D-0326's own revisit trigger).

### What we're doing next
Re-read Epistemic Independence from the then-current real closed episodes (the Principle D baseline is a 2026-09-28 snapshot). J-1776 commits the one-off scratchpad computation as a repo readout and fixes the module docstring that still says "Live Advisory Coupling"; J-1777 fixes the `adoption_state: PRESENTED` mislabel on shadow rows (F-2395). No Phase-2 build, no wiring of `epistemic_advisory_hint()`.
