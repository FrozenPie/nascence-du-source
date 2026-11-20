# T2 Consolidation Redesign — Spec

> **Status:** Phase 1 BUILT 2026-06-09 (error+novelty gating, contradiction-only consolidation, global habituation —
> `nodes/subconscious_node.py`). Validated: dry-run 13 eligible contradiction tensions vs the old 227 salience
> preoccupations; watch write-rate + diversity in the digest's consolidation section. Phase 2 LITE built 2026-06-11 (Always-On slice): per-sleep episodic renormalisation (store.downscale_episodic ×0.96 toward 0.5) AFTER replay strengthening — what mattered survives the downscale. Full §3 remains future work. NOTE 2026-06-10: the per-exchange Consolidation *node* (a different lane) gained the same
> axis discipline — correction/fail-call batches quarantine their wisdom (error→BEING gate).
> **Subsystem:** `nodes/subconscious_node.py` — the T2 synthesis pass (`_find_t2_trigger`, `_t2_synthesise`).
> **Goal:** stop T2 laundering *repetition* into *self-knowledge*. Make consolidation biologically faithful.

---

## 0. The diagnosis (why this exists)

T2 is the system's **systems-consolidation** analogue: it takes recurring tensions and writes
first-person "self-discovered truths" into permanent archive memory. Measured on live data:

- **227 of 231 tensions are SALIENCE** (`unresolved_thought`/`unresolved_dream` — preoccupations),
  only **4 are CONTRADICTION** (`critic_rejection` — genuine self-conflict).
- `_find_t2_trigger` selects by `count × spread`, **ignoring the axis** — so the top 15 it
  synthesises are *all* salience (`unresolved: identity ×83`, `shadow ×83`, …).
- The echo guard is **per-tension, single-embedding** — 45 different `unresolved: identity`
  tensions each mint near-identical archive fragments, unguarded.
- Result: the archive floods with one theme (~1 synthesis/90s), which feeds T4's material,
  Recall, and the next dream's seed → the attractor self-amplifies.

**What T2 currently models is rumination, not consolidation.** The brain has specific machinery
to prevent exactly this; we are missing all of it.

## 1. The biological target (what the brain actually does)

| Brain mechanism | Principle | T2 today | Our item |
|---|---|---|---|
| Prediction-error / ACC conflict vs. salience network (insula/dACC, LC-NE) | You consolidate from **error**, not from what merely grabbed attention | conflates them | **#1** |
| Habituation / repetition-suppression; hippocampal novelty gating (SN/VTA) | Repeated input → *less* encoding; novelty → *more* | `count×spread` amplifies repetition | **#2** |
| Complementary Learning Systems (hippocampus fast/temporary → neocortex slow/permanent) | Only a *selected* subset consolidates; the rest expires | everything recurrent consolidates permanently | **#3** |
| Synaptic homeostasis (sleep downscaling) | Sleep *renormalizes* — strengthens the important, weakens the rest | only ever writes; never prunes | **#4** |

---

## 2. Phase 1 — the immediate redesign (items 1–3)

### Item 1 — Gate on error + novelty, not recurrence

Replace the `count × spread` trigger in `_find_t2_trigger` with an **error-and-novelty** score:

```
score(t) =  W_CONTRA   * contradiction_count(t)          # the prediction-error / accountability axis
          + W_NOVELTY   * theme_novelty(t)                # high if this theme is under-consolidated lately
          - W_HABITUATE * recent_theme_synth_count(t)     # habituation: penalise the over-said theme
          + W_SPREAD    * log1p(spread_hours)             # keep a mild temporal-maturity term
```

- `contradiction_count` from `tension_ledger.score_tension` (already available).
- `theme_novelty` / `recent_theme_synth_count` from the global synthesis buffer (Item 2).
- **Recurrence (`count`) is no longer a multiplier** — that was the rumination amplifier.
- Proposed defaults: `W_CONTRA=3.0, W_NOVELTY=1.5, W_HABITUATE=1.0, W_SPREAD=0.3`. Tunable.

**Effect:** T2 preferentially consolidates genuine self-contradictions and *novel* themes; it stops
re-minting the dominant preoccupation.

### Item 2 — Global repetition-suppression + novelty signal

Maintain a rolling **global synthesis buffer** — the last `N≈40` synthesis records
`{theme_tokens, embedding, ts}` in `subconscious_state.json` (or a small jsonl).

- **Write guard:** before archiving a new observation, compare its embedding to *every* entry in
  the buffer (not just the tension's own last synthesis). Skip the write if within
  `GLOBAL_ECHO_THRESHOLD` (≈0.15) of any. This is habituation across tensions.
- **Novelty term (feeds Item 1):** `theme_novelty(t) = 1 − max cosine(t.label, buffer)` —
  a theme close to many recent syntheses scores low; a fresh one scores high.
- Keep the existing **per-tension** echo guard as a cheap first-pass backstop.

### Item 3 — Salience stays ephemeral (CLS: fast/temporary vs slow/permanent)

The crux. Split T2's output by axis:

- **CONTRADICTION tensions** → consolidate to **permanent archive** as today
  (`origin='subconscious_synthesis'`, high importance). These are the error-driven self-truths.
- **SALIENCE tensions** → if synthesised at all, written to a **fast-decaying ephemeral store**
  (episodic, low importance, short TTL / strong decay; a distinct origin e.g.
  `salience_note`), **NOT** the permanent archive. They keep informing attention, curiosity,
  and dreams (as they already do) but are no longer minted as permanent self-model.

> **Recommended default:** salience is *not* T2-synthesised to permanent memory at all in Phase 1
> (it already drives attention/curiosity/dreams through other paths). If that proves too quiet,
> re-enable the ephemeral `salience_note` path. Start strict; loosen only if needed.

**Expected behavioural change (flag honestly):** T2 will fire **far less often** — there are 4
contradiction tensions, not 227. Consolidation becomes rare and high-signal. This is biologically
correct (most experience is *not* consolidated) but is a large, visible change to the subconscious
write rate. T4's fragment gate will lean on dreams + active_imagination + the (rarer) contradiction
syntheses; the new T4 chain already retrieves `light_events` directly, so it is not dependent on the
synthesis flood.

---

## 3. Phase 2 — sleep downscaling (item 4, separate, larger)

The profound one, scoped on its own. During the Sleep State, add a **renormalization** pass over
the archive: group `subconscious_synthesis` fragments by theme; for over-represented themes,
**decay importance/relevance** (and/or prune the oldest near-duplicates) so no single theme can
dominate the self-model indefinitely. This is the synaptic-homeostasis half the system has never
had — the thing that lets the self-model *forget proportionally*, not just accrete. Specced and
built separately once Phase 1 is observed.

---

## 4. What we preserve (guardrails)

- T1 clustering, salience → curiosity/dreams, and the two-axis ledger are **unchanged**.
- The per-tension echo guard stays as a backstop.
- All changes best-effort / abort-safe; a failure in the buffer or axis lookup degrades to
  "skip this synthesis," never crashes the subconscious loop.
- No change to identity/T4 in this spec (T4 already redesigned separately).

## 5. How we'll know it worked (measurement)

Add a **Consolidation** section to `session_digest.py` tracking:

- `subconscious_synthesis` **write rate** (should drop sharply from ~1/90s).
- **Theme diversity** of recent syntheses (the word-frequency monoculture should break).
- **Contradiction : salience ratio** of what gets *permanently* consolidated (should invert toward
  contradiction).
- Downstream: does T4's material diversify, and do T4 commits start landing.

## 6. Open parameters (defaults proposed, all tunable)

`W_CONTRA, W_NOVELTY, W_HABITUATE, W_SPREAD`; global buffer size `N`; `GLOBAL_ECHO_THRESHOLD`;
salience policy (strict-off vs ephemeral `salience_note`); decay TTL if ephemeral is enabled.

## 7. Files touched (Phase 1)

- `nodes/subconscious_node.py` — `_find_t2_trigger` (new scoring), `_t2_synthesise` (axis split +
  global buffer guard), new global-buffer helpers, new constants.
- `core/memory/store.py` — possibly a `salience_note` ephemeral origin + decay (only if the
  ephemeral path is chosen over strict-off).
- `scripts/session_digest.py` — the Consolidation measurement section.
