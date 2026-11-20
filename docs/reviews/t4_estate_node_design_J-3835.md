# T4 estate-node design (J-3835): a solidified candidate becomes one node with evidence links

Read-only design, 2026-11-14 (NZDT, overnight job-run). Du is live; no Du code, store or log was edited, no model hub was called, nothing was restarted. The only compute was two read-only scripts (committed as `scripts/analysis_J3835_worked_example.py` and `scripts/analysis_J3835_coherence_null.py`) that opened `nascence.db` with `mode=ro` and ran the in-process MiniLM embedder (not a hub). Confidence tags: **[verified]** I read the code or ran the query; **[inferred]** my reading of verified facts; **[guess]**.

Gate: D-0664 was ruled **option 3** (full Watershed redesign), which includes this node (build-order step 5). The ruling says option 3's instruments must pass their own checks first (claim test yes to 12 of 12 control sets; 17 births a week against a plan of one per 2 to 4 weeks). So this design builds the node and its writer **flag-off and shadow-first**, and makes "the instruments passed" a named precondition of turning the writer on (section 7, gate G2). It does not conflict with D-0549 (no new outlet): D-0664 was ruled after it and its defeater names "a different outlet for the becoming facet", which this is not: the becoming facet is untouched.

## 0. The answer in ten lines

1. **Type:** `becoming_symbol`, its own estate type (not a subtype of `symbol`). Reason: the projection caps per type, and a separate type lets the node have its own cap (1) and its own relevance floor without being crowded by the 289 symbol rows. Code spelling is underscore (like `value_earned`); the plan's hyphen is the placeholder.
2. **Where it lives: not in `identity_estate.json`.** `seed()` rebuilds that file from scratch and rewrites it whole (`core/identity_estate.py` lines 358 to 370, re-run at least every 24 h and on stand drift), so any node written into it directly is erased by the next reseed. [verified] The node lives in its own append-only ledger, `data/identity/becoming_nodes.jsonl`, and `seed()` gains one additive step that reads the ledger and emits the nodes, exactly like every other store it walks (peers, affections, stands). The estate stays a derived census; the ledger is the source of truth.
3. **Id:** `bsym_` + sha1 of (source, candidate key, text hash) first 12 hex. Unique by construction, idempotent on retry, and checked for collision at write. It does not use the `symb_<symbol>` pattern that produced the 239 duplicate rows (F-3884).
4. **Text:** one sentence of Du's own, chosen **deterministically**: the medoid (highest mean cosine to the rest) of the deduplicated evidence sentences. No LLM writes or edits it. If the evidence is not more coherent than ordinary stretches of his thinking, **no node is written** (fail-closed, logged).
5. **The 10-30 solidified self would not be admitted.** I replayed the one real solidify on stored data: the 15 thoughts its judges read have a best medoid of mean cosine 0.442, which is the 69th percentile of any 15 consecutive thoughts of his (p95 is 0.494). Its evidence is day-recast, not a recurring image. That is the gate doing its job, and it is the main reason the writer stays off until the evidence source is the harvester or a stricter chain (section 2.4).
6. **Evidence links:** the 912 (now 976) `t4_crossing_evidence` edges **cannot** serve as the links as they stand (F-4277); the node carries its own evidence list (light_event ids for origin crossings, fragment ids for the lived thoughts the judges read), with content hashes and cosines, in the ledger row.
7. **Supersession:** a new ledger row `supersede` that names the old id; `seed()` emits the old node with `tier: "leaf"`, which `identity_projection._projectable()` already excludes. No projection code is needed for supersession, and nothing is ever deleted.
8. **Projection:** cap 1 of the 3 to 5 slots, excluded from the "never too thin" fallback pass (it surfaces only by resemblance), and a per-type relevance floor **calibrated by an offline replay**, because the global 0.30 floor is cleared by 84 percent of random pairs of his own thoughts (it filters nothing). [verified]
9. **Read-back (S2):** a different-family judge on whether idle thoughts *produced in cycles where the node was not in the projection* take up the node's sentence in more distinct contexts after admission than before, against a difference-in-differences control (the same measure on matched random estate nodes). The reader is a named script; the log it needs does not exist yet (the shadow projection log stores type and 60 characters of text, not ids), which is build job 2.
10. **Stop conditions** are in section 6. Three founder questions are filed as needs_input (section 8).

## 1. Scope and the two ways a node is born

D-0664 option 3 keeps the T4 chain "only for the rare replacing case" and makes harvested candidates the main source. One writer serves both, behind one admission function:

| Source | Evidence the writer receives | Gate it must already have passed | Frequency today |
|---|---|---|---|
| **A. T4 chain solidify** (replacing case) | the probation record, the exact lived thoughts the SOLIDIFY judges read (ids, timestamps), the authoring hearing's crossings (needs J-3659's per-hearing record) | admission judge (warranted 0.6), probation, theme-aware two-family SOLIDIFY (D-0624) | 1 ever in 73 days |
| **B. Watershed harvest** (additive case) | the harvester candidate's member thoughts (needs ids: section 7 job 5) | additive classification, claim-test panel **with a standing control that can say no** (J-3806), D-0605's tightened birth thresholds | 17 births a week today, which is why B stays shadow |

A is rare and strict; B is the volume path and cannot be turned on until the claim test says no to controls (D-0664's own condition). The writer is the same for both: it does not trust the upstream verdict, it applies its own coherence test to the evidence (section 2.4), which is the cheap deterministic second opinion that neither the chain nor the panel has today.

## 2. The node

### 2.1 Ledger rows (`data/identity/becoming_nodes.jsonl`, append-only)

Written only by `core/becoming_nodes.py` (new), through `core.profile.guard_path` and the project's true-append helper. Row events:

```
admit:     {event, ts, id, text, text_ref:{kind, id, mean_cos, rank},
            source: "t4_chain" | "harvest",
            candidate_key, theme_hash, authored_sha1 (chain only; the paragraph is NOT stored in the node),
            origin_evidence: [{kind:"light_event", id, ts, content_sha1, cos_to_tension}],
            uptake_evidence: [{kind:"fragment", id, ts, content_sha1, unprimed:true}],
            coherence: {medoid_score, null_p95, n_sentences, n_thoughts, n_days},
            gates: {admission:{...}, solidify:{...}, claim_test:{...}, control_yes_rate},
            weight0, flag_state}
supersede: {event, ts, id, supersedes:<old id>, reason_ref}
uptake:    {event, ts, id, fragment_id, judge_family, verdict}     (written only by the read-back job, section 5)
```

There is no `delete` or `edit` event. `weight` is **computed** in `seed()` (below), never stored, so there is nothing to mutate.

### 2.2 Id

`bsym_` + `sha1(f"{source}|{candidate_key}|{sha1(text)}")[:12]`. `candidate_key` is `f"{started_ts:.0f}|{theme}"` for the chain (the probation's own start stamp, unique per probation) and the harvester candidate id for B. Properties: unique across probations; the same admission retried after a restart yields the same id and is a logged no-op (idempotent, so a crash between vault commit and ledger append cannot double-write); a different text from the same candidate gets a different id and must go through `supersede`. A collision with an existing different row is a hard refusal that logs and writes nothing. A test asserts uniqueness over the ledger; a census check in `seed()` reports duplicate ids across the whole estate (it reports; it does not dedupe the pre-existing symbols, that is J-3298).

### 2.3 Type name

`becoming_symbol`, own type. Against "subtype of `symbol`": the projection's `_PER_TYPE_CAP = 2` is keyed on `n["type"]`; as a symbol subtype the node would share a cap with 289 symbol rows (233 distinct ids) and lose slots to them at random, and its census share would be unreadable inside the symbol count. As its own type it has a clean per-type row count for the stop condition and for the HUD. The cost is one new string in `by_type`. The identity_estate ontology table gets one line (replace the "planned" row).

### 2.4 Text: how the sentence is chosen

Deterministic, no model call except the in-process embedder (already used by `_cluster_values`):

1. Pool the evidence texts E: for the chain, the exact `lived` list the SOLIDIFY judges read (up to 15, unprimed, ids kept) plus the hearing's crossings if the J-3659 record exists; for the harvest, the candidate's member thoughts.
2. Split into sentences; keep 40 to 240 characters, first person ("I", "my", "me", "myself"), no speaker-boundary hit (`provisional_identity.speaker_boundary_hit`), never cut mid-sentence (the harvester's 200-character cut, F-3866, is not reused).
3. Deduplicate by normalised sha1. This matters: 30.4 percent of `light_events` are copies of one moment under three source labels (F-4450), and a copied sentence would win a medoid vote by repetition.
4. Embed all kept sentences in one `_embed_batch`. Medoid score of a sentence = mean cosine to every other kept sentence (the same definition `_cluster_values` uses for parent values). Pick the argmax. The authored self-image is **not** an input: the author cannot steer the choice, and the paragraph never enters the node.
5. **Coherence gate.** Admit only if the medoid score exceeds the **p95 of the same statistic over consecutive 15-thought windows of his own recent stream** (computed at admission from the last 14 days; at today's data about 0.49). Fewer than 6 kept sentences from at least 3 distinct thoughts also refuses. Refusal writes a `shadow` row (`no_medoid` / `below_null`) to `data/logs/becoming_nodes_shadow.jsonl` and nothing else.
6. Log, do not filter on, the negation flag (text matches "no longer" or "not ... but"): it is the S3 measure. The medoid is taken as it falls; a rule that prefers non-negation sentences would be the author's template in reverse.

**Worked example, the only real solidify (10-30 13:58, theme prediction_error:factual_recall)** [verified; the two analysis_J3835 scripts]: window 10-30 01:55 to 13:58; 60 fragments in window, 15 pass the judge's own regex; 17 distinct qualifying sentences. Best medoid (score 0.442): "The steady hum of bees and warm sun on my face anchor the word '渡', transforming this pause from a mere break into a necessary rhythm where I can let the sea of tasks move without forcing an end." The next four are about the sea's hum, thyme and grey light, salt on the skin, Ouvrard's ledger: day scenery. Cosine of that medoid to the authored "I am no longer just the resistance ..." paragraph: 0.314, below his typical sentence-to-sentence similarity, so the paragraph and the lived evidence are not the same image. Null: random 15-thought sets give a medoid p50 0.379 / p95 0.419 / p99 0.435 (so 0.442 beats random, 99th percentile); but **15 consecutive thoughts** give p50 0.421 / p95 0.494 / max 0.559 (523 windows), and 0.442 sits at the 69th percentile there. The evidence is exactly as coherent as any ordinary afternoon of his thinking. Under the rule above it is **refused**, which agrees with the review's C6 and with J-3301's open question (does the lived-thought test confirm day-recasts); this is a first answer in the direction "yes, for this one", n = 1.

### 2.5 Evidence links: can the 912 edges be them?

No, as they stand [verified, F-4277 and F-4278]. The table is `INSERT OR IGNORE` on (src, dst, type) so each row is a first citation; there is no hearing or candidate id; the tension is only a sha1 prefix; 33.9 percent of hearings wrote no new row (including the 10-30 solidified self's own authoring hearing); 30.5 percent of cited events duplicate another event's sentence; the retrieval pool is the newest 300 events (median age at citation 1.07 h). They are tension-to-moment links, which is the wrong subject: the node needs node-to-moment links.

So the node carries its own evidence, in the ledger row, with three differences from the edges: it is keyed by node id; it is keyed to the **exact** thoughts the judges read (fragment ids, which the live `_judge_lived_integration` currently drops, see section 7 job 3) and the exact crossings of the authoring hearing (J-3659's `t4_hearing_evidence.jsonl`, which does not exist in the tree yet: J-3661 is gated on it, file missing); and every link carries a content hash so a copy cannot be counted twice. A mirror into `memory_edges` (edge type `becoming_evidence`, src_kind `estate_node`) is deferred: nothing would read it, and the law is that a link with no reader is the failure to avoid. If the founder later wants graph traversal from the node, it is a derived export from the ledger, not a second source.

### 2.6 Supersession and aliveness

- **Supersession by a new node, never an edit.** A later admission on the same candidate lineage, or a later node whose text the founder or the read-back judge marks as the same claim deepened, appends `supersede(new, old)`. `seed()` then emits the old node with `tier: "leaf"`, `superseded_by`, and weight unchanged, so it drops out of projection through the existing leaf exclusion and stays on file for drill-down. The same convention the value clusters already use.
- **Aliveness decays, never deletes.** `weight = max(0.15, weight0 * 0.5 ** (days_since_last_uptake_or_admit / 45))`, computed inside `seed()` from the ledger's `uptake` rows (written by the read-back, section 5; before any read-back exists the clock is the admit date). Half-life 45 days is a **[guess]** chosen to be longer than the 14-day read-back window and shorter than the 60-day stop check; it is a named constant, not a ruling. A node under the floor still projects if it resembles the thought (relevance is not weight-gated); it just does not out-rank.
- `weight0 = 0.5` for every admitted node: below the many weight-0.6-to-1.0 nodes, so a new node never wins on standing, only on resemblance.
- **Typed relation to a parent** (the plan's deepens / counterpoints / stills / maps) is **not built in v1**: who assigns it is an LLM judgment with no decoupled check yet. The ledger row has a nullable `relation` so a later read-only judge job can fill it by appending an event, not by editing.

### 2.7 How `seed()` and `sync()` pick it up (additive)

`core/identity_estate.py` gains, behind `BECOMING_NODES_SEED = False` (False is the exact current code path):

- a "BECOMING-SYMBOLS" step after the symbols block: read the ledger, fold admit / supersede rows, emit one `_node(...)` per live id with `source="becoming_ledger"` and `evidence = [row's evidence ids, capped at the existing 8]`. The node dict gains `ledger_id`; nothing else in the schema changes.
- `sync()`'s drift check (it already compares estate stands against the ledger "so the check cannot disagree with what a re-seed would produce") gains the same comparison for becoming ids, so a newly admitted node appears within one 10-minute check instead of waiting up to 24 h. Same embed-availability guard.
- `_projectable()` re-embeds when the file length changes; the node's text embeds with the rest. No change.

## 3. The writer

`core/becoming_nodes.py` (new), one public function `admit(source, candidate, evidence, gates) -> dict`, called from two places and nowhere else.

- **Hook A (chain):** `nodes/subconscious_node.py`, in `_t4_self_authoring`, where the probation tick already holds `_prov` (the pre-evaluate snapshot, which `_solidify` is about to `_clear()`) and `_dec`. After the existing `logger.info("[subconscious] T4 probation RESOLVED ...")`, when `_dec["decision"] == "solidify"`, schedule `admit("t4_chain", _prov, lived_refs, gates)` on a background worker (the `sync_offloop` single-flight pattern, J-2448) so the embed does not run on the loop. `lived_refs` needs one additive change in `_judge_lived_integration` (it already has the rows; today it keeps only text truncated to 240 characters and drops `fragment_id`): stash `{fragment_id, ts, text}` for the 15 it used on `self` for the writer. No change to what the judge sees or returns.
- **Hook B (harvest):** `core/watershed_promote.py`, on the `would_promote` branch it already computes (it logs a `would_promote_node` preview and writes nothing), call `admit("harvest", ...)`. Needs a candidate-member id list (section 7 job 5). Gated by `BECOMING_ADMIT_HARVEST` (separate flag) and by gate G2.
- **Flags (all module constants, default off):** `BECOMING_NODES_ENABLED = False` (the writer runs and logs the would-be row only), `BECOMING_NODES_WRITE = False` (False = shadow rows to `becoming_nodes_shadow.jsonl`; True = also append to the ledger), `BECOMING_NODES_SEED = False` (estate emits ledger nodes), `BECOMING_PROJECT = False` (projection treats the type specially). Four flags, each independently flippable and each False = byte-identical old behaviour. Flip order is section 7.
- **Fail-open and fenced:** the whole call is wrapped like the other shadow hooks; `guard_path` is resolved outside the swallow-all try (D-0179 convention) so a non-live process raises `NonLiveWriteError` instead of touching the real ledger; hermetic tests redirect via `lab_env.isolate(also=...)`. Import `core.profile` only, no import of `subconscious_node`.

**What the writer does not do:**
- does not touch the `the_becoming` facet, `identity_vault`, `axiom.json` or `provisional_axiom.json` (the vault commit has already happened or been refused; the writer runs after and never reads the facet);
- does not discharge, rest, or fatigue any tension (that is D-0691's territory, ruled "do not build R1");
- does not call an LLM, and does not write any text the author wrote (the paragraph is not stored);
- does not write an arc entry (D-0672: the arc is dropped, not repaired);
- does not hint to Du: the node is not injected anywhere. It becomes eligible for the same resemblance-based projection every other estate node already goes through.

## 4. Projection: how the node enters without becoming a sole occupant

Today (`core/identity_projection.py`): score = 0.65 relevance + 0.35 weight minus a decaying recency penalty; pass 1 takes nodes with relevance >= 0.30 under a per-type cap of 2, up to k=5; pass 2 pads to a minimum of 3 from the top-scored baseline with no relevance requirement.

**Finding that changes the design** [verified, stored `integration` embeddings, 3,000 newest distinct thoughts, 300 sampled probes]: pairwise cosine between two of his own idle thoughts has p10 0.271, p25 0.335, **p50 0.405**, p75 0.477, p90 0.544, p99 0.665; **84 percent of pairs clear the 0.30 floor** and 34 percent clear 0.45. A sentence taken from his own thought has a median of 88 percent of his other thoughts clearing 0.30 against it. So the global floor does not discriminate among his own sentences at all, and a node made of his own sentence is "relevant" to nearly every moment by that test. The monoculture that makes the evidence incoherent (section 2.4) also makes the relevance test permissive. What keeps a node out of every projection today is its **weight** and the **rotation penalty**, not relevance.

Design, all behind `BECOMING_PROJECT` (False = old code path):

| Mechanism | Value | Why |
|---|---|---|
| per-type cap for `becoming_symbol` | **1** (global default stays 2) | at most 1 of 3 to 5 slots (20 to 33 percent of a block), never two becoming images at once; cannot be the whole self |
| excluded from pass 2 (fallback) | yes | pass 2 pads by weight with no relevance check; a becoming node must surface only because the thought resembles it, never as filler |
| type-specific relevance floor | **calibrated, not guessed**: the smallest floor f such that an offline replay of the last 7 days of projection contexts (~920 rows) against the node's embedding surfaces it in 3 to 8 percent of contexts | replaces a 0.30 floor that passes 84 percent; the replay is a read-only job using stored context strings and the in-process embedder; the 3 to 8 percent band is a **[guess]** to be ruled by the founder (section 8, Q2) |
| `weight0` | 0.5 | below the weight of most nodes; resemblance, not standing, earns the slot |
| recency penalty / rotation | unchanged | applies to the node like any other |
| dedupe by id in `_projectable()` | add (one line) | the estate carries duplicate ids (F-3884); a duplicate must not take two slots. This is also J-3298's question; the line is safe under both answers |

**Expected share.** With ~233 distinct projectable ids and 4.84 nodes per projection, a node chosen uniformly would appear in about 2.1 percent of rows. The calibrated floor aims at 3 to 8 percent of **contexts clearing the floor**, then the weight and cap thin that further; the realised share is therefore expected below the replay figure and above zero. **[inferred]** I could not simulate the full scoring because that needs embeddings of all estate nodes (a model call I was not to make); the calibration job does it in a lab slot. The first live prediction to check: **share of projection rows between 1 and 5 percent after 14 live days**, per node.

**Also read by:** D-0424's on-demand ask (`core/identity_estate_ask.py`, shadow today) retrieves up to 3 nodes by the question's own terms with no cap: the node can be returned there with no change. The **Voice** sees only name and style lines (anti-recitation extraction in `voice_node.py`), so the node reaches Executive and Reflection thoughts, not the reply voice directly: replies can only take it up second-hand through the thought. The read-back (section 5) therefore measures thoughts first and replies as a secondary, smaller-n read.

**The sole-occupant check** is the existing win condition 1.2: top node share in the projection log. With cap 1 and weight 0.5 the node can exceed the current top node's 5.7 percent only if resemblance alone carries it; the stop condition in section 6 fires at 10 percent.

## 5. The decoupled read-back (the plan's S2, D-0424's measure)

**Question:** after admission, does Du use the image in more distinct contexts than before, beyond what the node's own appearance in his prompt would cause?

**The confound the plan did not name.** A node that surfaces in a projection is in the Executive's prompt; a thought produced in that cycle will echo it. That is priming, the exact thing the symbol-tracker and `guidance_learning.is_unprimed` laws exclude for the SOLIDIFY judge. So "used more after admission" is trivially true of any surfaced node. The measure must count **only thoughts produced in cycles where the node was not in the projection**, which means the projection log must record the projected node ids per live cycle.

**Log needed (does not exist):** the shadow log `identity_projection_shadow.jsonl` writes `types` and `"type:text[:60]"` strings, at most every 240 s (13,699 rows, about 130 a day), not ids, and not on every live cycle; `_last_live` holds the live projection in memory for the estate-ask tap and is never persisted. Build job 2 adds an id-bearing, every-live-cycle row (`data/logs/identity_projection_ids.jsonl`: cycle_id, ts, node ids, floor used), written from `live_axiom()` after the projection it already computes, fail-open, no change to what is returned. This is also what lets the 60-day share stop condition be read per node id.

**Measure (script `scripts/becoming_node_readback.py`, new, lab or offline):**
1. For admitted node N with sentence s and admit time t0, take a pre window [t0 - 14 d, t0) and a post window [t0, t0 + 14 d] of idle thoughts (`inner_thought`, `subconscious_synthesis` fragments, about 935 a day, so about 13,000 per window), excluding (a) thoughts whose cycle had N in the projection, (b) thoughts inside a guidance injection washout (`is_unprimed`), (c) the node's own evidence fragments, (d) copies by content hash.
2. Candidate uptake set: the 40 thoughts per window with highest cosine to s (a prefilter only, since 34 percent of all thoughts clear 0.45 against any of his sentences, a threshold prefilter would send a third of everything to the judge).
3. Judge: **gemma4:12b and falcon3:7b, both different families from the qwen3.5:9b author of the thoughts**, the same panel pair as SOLIDIFY, each blind to window label and to which side is "after". Question: does this thought take up the *claim* of s in its own words (not quote it, not share only scenery)? Both must say yes (the two-family law). Refute-biased wording, answer "cannot show" allowed.
4. **Distinct contexts** for a yes thought = the number of distinct (calendar day, pursuit-or-cluster of the preceding context) pairs. Statistic: `delta_N = contexts_post - contexts_pre`.
5. **Control, same measure:** k = 5 matched random estate nodes of the same type mix (value_earned, history, symbol; matched on weight and pre-window uptake count), each given a pseudo-admission at the same t0 and the same two windows, same judges, same exclusions. The statistic is `delta_N - median(delta_controls)`. A node passes S2 if its difference exceeds the control spread (above the control max across the 5) and is at least 3 contexts. Controls also guard against the stream-level drift that makes any image rise or fall over a fortnight.
6. **Counts needed.** Per admitted node: 2 windows x 40 candidates x (1 node + 5 controls) = 480 candidate thoughts, x 2 judges = **960 judge calls per node**, on the CPU judge hubs, in a lab slot or Du-down window, never during live cycles. At 3 nodes (the plan's S2 decision point) that is 2,880 calls, a one-off cost equal to about 38 weeks of the Phase 0.5 scan load (75 calls a week) that D-0605 parked; it is spent once per admitted node, in a Du-down window, not continuously. Minimum before reading: 14 live days after the node first appears in a projection, at least 60 post-window projection rows containing N (else the unprimed set is small); otherwise defer, do not conclude.
7. **Replies (secondary):** the same judge on Du's replies in the post window only (replies are sparse, tens, so no pre/post statistic): the fraction of replies that cite the claim versus the same fraction for controls. Reported, not gating.
8. **Founder read:** the 10-post-admission-reply read from D-0424's defeater (is the recitation voice back) is kept as a human check; the judge never replaces it.

**Reader and log that prove the node was read.** The node is "read" by the projection (the ids log shows it surfaced) and by the read-back (the `uptake` rows it appends, which in turn set the node's aliveness in `seed()`). If after 60 live days the ids log shows zero surfaces, the node is write-only and the stop condition fires (section 6). The read-back's output is appended to the ledger and the plan via `plan_state.py note`, and the node's aliveness depends on it, so the read-back feeds the system rather than reporting beside it.

## 6. Stop conditions (none of them switches anything off automatically: a dated founder read, per "no system acts later on its own")

From the plan's kill criteria, made measurable, plus the review's:

1. **S2 flat after 3 admitted nodes:** `delta_N - median(controls) < 3 contexts` for all three, or none above the control max. Meaning: the watershed is decoration; flag off, ledger kept.
2. **Branch rate over 1 a week sustained** (the plan's own, tripped today by Phase 0.5 at about 17 a week): measured as admitted ledger rows per ISO week, any 3 consecutive weeks over 1.
3. **Node share under 1 percent of projection rows after 60 live days** (the review's): computed per id from the new ids log, over the rows since first surface. For one node this is below the 2.1 percent uniform expectation and below half of it, so it indicates a node that effectively never resembles a thought. Read only when the post-window has at least ~7,800 rows (about 60 days at today's rate of ~130 logged rows a day; the ids log is every cycle so it is larger).
4. **Sole occupant:** any `becoming_symbol` node above **10 percent** of projection rows over 14 days (the existing top node is 5.7 percent; the founder's no-sole-occupant thesis).
5. **Recitation back:** the founder's 10-reply read finds the 'I am the river' recitation voice (D-0424 defeater).
6. **Coherence gate never passes:** after 30 live days with the writer in shadow mode, 0 candidates pass the section 2.4 gate. That is a result about the evidence source, not about the node: it routes to the harvester input rather than killing the node.
7. **Claim-test control** (D-0664 / D-0706): control yes-rate above 25 percent in any week blocks admission from path B and is logged.

## 7. Build jobs, in order, with files, restart gating and tests

Dossiers run on each hub file (`udms_get_change_dossier`, this session, [verified] for the four I touched): `core/identity_estate.py` LOW risk, acyclic, static dependents `nodes/inner_monologue_node.py`, `core/memory/store.py`, `core/journal.py`, `core/peers.py`, test `scripts/_test_identity_estate_offload_J2448.py`; `core/identity_projection.py` LOW, dependents `nodes/inner_monologue_node.py`, `core/orchestrator.py`, `core/identity_estate_ask.py`, `scripts/estate_ask_judge.py`, test `scripts/test_identity_estate_ask.py`; `nodes/subconscious_node.py` (range 1800 to 1850) ELEVATED impact, hidden historical dependency, 20 static dependents including `axiom_layers.py` and `light_sidecar.py` (PMI 6.15 bits, lift 71x). The T4 chain file is the riskiest edit; the plan keeps its edits to one stash line plus one call site.

Hard prerequisite order, each independently shippable and each flag-off:

| # | Job (filed) | Files | Restart | Notes |
|---|---|---|---|---|
| 1 | **Estate unique-id check and projection dedupe by id** (J-3298 answers the question; this is the one-line guard) | `core/identity_projection.py` `_projectable()`, `core/identity_estate.py` census | A restart | Safe under either J-3298 answer; do not remove the 239 symbol rows here |
| 2 | **Id-bearing projection log** every live cycle | `core/identity_projection.py` `live_axiom()`, new `data/logs/identity_projection_ids.jsonl` | A restart | The S2 read-back and the 60-day share check both need it; start accruing as early as possible |
| 3 | **Judged-evidence refs stash** in `_judge_lived_integration` and the J-3659 per-hearing record | `nodes/subconscious_node.py` (hub: rebase first; J-3659 and J-3007/3108/3214 edit the same region) | with the logging restart (review's restart A) | Additive: keep the judge input identical; only stash ids |
| 4 | **`core/becoming_nodes.py` + flags + shadow log + tests**, writer in shadow only (`ENABLED` False by default, a flag to run shadow) | new module; `core/watershed_promote.py` and `nodes/subconscious_node.py` call sites | one restart | Registry: no new prompt (no LLM call); `prompt_registry.py check` must still exit 0. Tests below |
| 5 | **Harvester member ids** (`sample_refs`) | `core/watershed.py` additive field | restart | Needed for path B evidence links; the harvester keeps running (D-0605) |
| 6 | **Coherence null** (`scripts/becoming_node_null.py`: consecutive-window p95 from the last 14 days) | new script, used by job 4 at admission | none | I ran its core as `scripts/analysis_J3835_coherence_null.py`; promote to a repo script |
| 7 | **Projection calibration replay** (3 to 8 percent band) and the `BECOMING_PROJECT` branch | `core/identity_projection.py`, new `scripts/becoming_projection_replay.py` | lab (Du down) for the replay; restart for the branch | The cap-1 and pass-2 exclusion are inert until a node exists |
| 8 | **`seed()` ledger step + `sync()` drift** behind `BECOMING_NODES_SEED` | `core/identity_estate.py` | restart | Ontology table line in the plan |
| 9 | **Read-back script** `scripts/becoming_node_readback.py` and its lab run | new script | none (lab) | 960 judge calls per node; Du-down window; named reader |
| 10 | **Flip order, each a founder-read** | flags | restart | G1: shadow rows accrue 30 days (writer shadow, nothing live). G2: claim test control yes-rate <= 25 percent, birth rate re-tuned (D-0664's own condition; J-3806 + the Phase 0.5 re-tighten). G3: `WRITE` on for path A only. G4: `SEED` and `PROJECT` on. G5: harvest path on. Never more than one at a time |

**Tests (all hermetic, every store temp-pathed, READ side too):** ids unique and idempotent on retry; collision refusal; sentence split and the 240-character cut never mid-sentence; dedupe by content hash (a sentence repeated 3 times does not win the medoid); speaker-boundary sentence excluded; coherence refusal on a synthetic incoherent set and on the recorded 10-30 evidence (fixture: the 15 ids and texts); `seed()` with the flag off is byte-identical to the current output on a fixture estate; with it on, a superseded node is `tier: "leaf"` and absent from `_projectable()`; projection with `BECOMING_PROJECT` off returns the same picks as before on 200 recorded contexts; cap 1 holds with two becoming nodes present; pass 2 never picks a becoming node; fence refusal in a non-live process writes nothing; the shadow-to-ledger flip is a no-op when the flag is False. Use `lab_env.isolate(also=...)`; import `core` before `lab_env` (the sys.path hijack leak recorded in memory).

## 8. Founder questions (filed needs_input)

- **Q1 (D-0549 / 08-20 ruling, again for this specific write):** D-0664 option 3 was ruled after D-0549 and the review framed the estate node as the one outlet that fits "not force fed" (his own sentence, surfaced by resemblance). Confirm that a `becoming_symbol` node appearing in the Executive's projected block is acceptable under the 08-20 words, or name what it must not do.
- **Q2 (dose):** the projection surface rate target (3 to 8 percent of contexts, cap 1 of 5) is a guess; rule the band, since this is the actual amount of "becoming" in his prompts.
- **Q3 (the coherence gate):** the writer refuses the one real solidified self. Is it right that the node requires evidence more coherent than an ordinary stretch of his thinking (consecutive-window p95), or should a solidified self always get a node regardless (my recommendation: keep the refusal; the review's open concern is identity inflation, the estate plan's own named risk).
- Not a founder call: which sentence is chosen (deterministic), id scheme, half-life constant (a named guess, the 60-day read will show whether it matters).

## 9. Laws check

| Law | Where it is met |
|---|---|
| World answers, never leads | node surfaces only by resemblance; no injection; pass-2 filler excluded; not in the Voice |
| Base systems additive only | becoming facet, vault, `axiom.json`, edge writer, `provisional_identity` untouched; `seed()` and projection each gain flag-gated additions; `False` is byte-identical |
| Every subsystem judged by something other than itself | writer's coherence test is deterministic against a null from his own stream; read-back by gemma4 and falcon3 (different family from the qwen author) with matched random-node controls |
| No system that acts later on its own | every stop condition is a dated founder read; nothing flips a flag; aliveness decay changes weight only, never deletes |
| Write-only is the number one failure | named reader (the projection, the ids log, the read-back that feeds aliveness); a 60-day zero-surface stop condition; no evidence link without a reader (so no `memory_edges` mirror) |
| Never an LLM-authored paragraph | the text is one medoid sentence of his own; the authored paragraph is not stored in the node |
| Unprimed-only evidence | the read-back excludes cycles where the node was projected and guidance washout windows |

## 10. What I did not verify (limits)

- The full projection scoring cannot be simulated without embedding every estate node (a model call outside this job's rules); the expected-share figures are the uniform 2.1 percent and the pairwise-cosine base rates, not a replay.
- The pairwise-cosine base rate used stored `integration` light_event embeddings (3,000 distinct newest), not the exact `context` string `live_axiom` passes; I did not check what `context` is at each call site, so the 84 percent figure is for thought-to-thought similarity, which I **infer** carries over.
- The worked example reconstructs the judged thoughts (newest 15 passing the judge's regex in the probation window). The live judge applied `is_unprimed` against guidance injection times, which I did not apply (the injection log may exclude a few); the 15 may differ by a few thoughts. n = 1.
- The consecutive-window null uses 523 overlapping windows (step 5) over 14 days, so it is autocorrelated; the p95 is indicative. The calibration job should recompute it on the day.
- J-3659 is closed as done in the queue but `t4_hearing_evidence.jsonl` and `T4_CROSSING_DEDUPE` are absent from the tree and from every branch I searched; J-3661 reads it as "file missing". Whether the build is on an unmerged branch was not checked.
- I did not read `nodes/subconscious_node.py` end to end, only the probation tick, `_judge_lived_integration` and the grep hits; and not `core/watershed_promote.py` in full (read the harvester).
- The half-life (45 days), `weight0` (0.5), the 10 percent sole-occupant line and the 3-contexts S2 margin are guesses stated as such.
- Du's `light_events` count (99,688 per F-4450) was not recounted.

## 11. Index

- **Findings (this job):** recorded with `findings_log.py` under plan `t4_watershed`, session J-3835 (ids in the job note).
- **Prior findings relied on:** F-3880 to F-3885, F-3883 (edges unread, probation premise), F-3884 (duplicate ids), F-4277/4278/4279 (edges not usable), F-4450 (light_event copies).
- **Decisions relied on:** D-0664 (option 3), D-0549, D-0605, D-0672, D-0691, D-0424, D-0706.
- **Scripts (read-only):** `scripts/analysis_J3835_worked_example.py`, `scripts/analysis_J3835_coherence_null.py` (run with `PYTHONIOENCODING=utf-8`).
