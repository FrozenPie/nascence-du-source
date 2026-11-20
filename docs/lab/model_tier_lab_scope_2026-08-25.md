# Model-tier feasibility lab — scope, 2026-08-25

*Written for J-0221 (source: `decision:D-0013`). This is a SCOPE, not a run — no lab has been
executed yet, no verdict is claimed for any of the 8 mechanisms below. It exists so the actual
lab (spawned as a follow-up job) starts from a concrete design instead of a blank page.*

## 0. Precondition check — done, for real, right now

D-0013's defeater (a) requires *"a Ramses model (mixtral:8x7b or similar) is fully wired and
available for production routing, making a model-tier lab feasible."* Verified live, not assumed,
2026-08-25:

| Port | Model | Check | Result |
|---|---|---|---|
| `LAN-HOST:11436` | `falcon3:7b` | `/api/tags` | UP |
| `LAN-HOST:11437` | `granite3.1-moe:3b` | `/api/tags` | UP (still has the known JSON-closing defect — excluded below) |
| `LAN-HOST:11438` | `mixtral:8x7b` | `/api/tags` **and** a real `/api/chat` call | UP — real completion returned in 38.9s (`prompt_eval_count=18, eval_count=86`) |
| `LAN-HOST:11441` | `command-r7b` | `/api/tags` | UP |

**All four Ramses hubs are live, not just mixtral.** The founder's "mistral should now be up" was a
name mix-up for `mixtral:8x7b` (per `deploy/ramses/CARE_PACKAGE_2026-08-23.md` — `mistral:7b-instruct`
was tried and REJECTED for the i9 hub back on 2026-08-21 for a JSON-shell platform failure; the model
actually standing on the i9 today is `mixtral:8x7b`). Defeater (a) is met. **This does not answer
D-0013's actual question** (model-tier reassignment vs. schema-first rewrite, per mechanism) — that
needs the lab below run for real, on production-shaped prompts, not the generic tasks
`docs/lab/ramses_models_2026-08-23.md` already covered.

## 1. What already exists vs. what this lab still needs

`docs/lab/ramses_models_2026-08-23.md` already scored mixtral/falcon3/command-r7b on generic
`judge` and `synthesise` station shapes (`station_bench.py`, `judge16.py`). That data is real and
reusable as a PRIOR, but it is not a verdict on any of the 8 flagged mechanisms — each one has its
own prompt shape, its own token budget, and (for the judge-shaped ones) its own gold labels. The gap
this lab closes: **run the actual call site's prompt against the candidate model**, the same
discipline `lane2_model_lab.py`'s header states explicitly ("system prompt imported LIVE from
core/lane2.py") and `station_matrix.md` proves the hard way (constant-answer judges scored 0.50 and
looked "half right" until the actual answer strings were printed).

## 2. Per-mechanism scope, ranked as the audit ranked them

| # | Mechanism | Current wiring (confirmed in code) | Candidate | What the lab must do |
|---|---|---|---|---|
| 1 | `core.commitment_ledger._judge_defeater` (line 337) | `SERVE_CHAINS.get("background") or SERVE_CHAINS["hot"]`, `max_tokens=150, temperature=0.2, tier=3`, sys prompt `_JUDGE_SYS` | `mixtral:8x7b` (:11438) | Extract `_JUDGE_SYS` + the real `user` string format (COMMITMENT/SCOPE/CLAIMED REASON/DEED RECORD) verbatim from the module. Need ~12-16 gold-labeled (legitimate/illegitimate defeat reason, statement, deeds) cases — none exist yet; author them by hand from real `commitment_ledger` log entries (`_log_event` calls at lines ~409/414 give real historical `why`/`statement` text to draw on) so cases aren't synthetic. Score: accuracy vs. gold, discrimination (not constant-answer — station_matrix's own headline finding), latency at cooldown ≥60s budget (irrelevant — plenty of room). |
| 2 | `core.self_implication` | `self.conscious_urls` (hot lane), alone, no panel | `mixtral:8x7b` as a second opinion, panel-style like `self_interrogation`/`tension_ledger` | Extract the actual 6-signal schema and system prompt from `core/self_implication.py`. Need gold-labeled hard-event vs. not-hard-event thought samples. Score: per-signal agreement rate between hot-lane verdict and mixtral verdict on the SAME thought (not just final verdict) — a panel is only worth adding if the two genuinely disagree sometimes; if mixtral rubber-stamps the hot lane's calls this finding downgrades to "not worth the latency." |
| 3 | `core.study_note` | background lane (weakest live models) | `command-r7b` (:11441) — fire-and-forget path, latency-tolerant | Extract the actual synthesis prompt (passage → new-note-vs-deepen-existing decision). Metric: coverage (does the note capture what's actually new vs. restated) the same way `ramses_models_2026-08-23.md`'s synthesis table already measures coverage for `phi3:mini` — reuse that scorer, new prompt. |
| 4 | `core.letters` (Travis letter) | `self.base_urls` (background) vs. peer letters on `self.conscious_urls` (hot) | move call site to `conscious_urls` | **Not a model-tier lab question — this is a one-line wiring fix**, already fully diagnosed by the audit with no candidate-model uncertainty. Scope note only: flag for a direct fix, not a lab slot. |
| 5 | `core.librarian` | `falcon3:7b` (judge-2) primary, `gemma4:12b` fallback, single call, no panel | `mixtral:8x7b` as added fallback/primary | Extract the subject-heading mapping prompt. `core/librarian.py`'s own pre-registered hit-rate metric (referenced in the audit) is the right score — run real carried-questions through both and compare hit-rate directly, not a proxy. |
| 6 | `core.composition` grading | `gemma4:12b` (judge-1) | trial `mixtral:8x7b` | Lowest urgency (soft, already on judge tier). Reuse `station_bench.py`'s existing groundedness-graded task if it already covers this shape; if not, deprioritize behind 1-3, 5. |
| 7 | `core.retraction_ledger` | zero-LLM token-overlap | n/a — this is a "should it get an LLM at all" question, not a model pick | Out of scope for THIS lab (no candidate model to test yet); leave as its own future decision. |
| 8 | `core.journal_rollup` | hot lane (`qwen3.5:9b`), same as daily `journal` | trial `mixtral:8x7b` for the weekly (heavier, multi-doc) synthesis specifically | Lowest urgency (soft, "worth trying"), fires at most once/week — real-world test cadence is slow, so this is better done by pointing ONE real weekly rollup at mixtral and comparing output by eye against the last few `qwen3.5:9b` rollups, not a synthetic multi-run lab. |

## 3. Execution order recommendation

Ranked by (audit's own stakes ranking) × (how cheap the lab is to build):

1. **#1 `_judge_defeater`** — highest stakes (audit's own words: "literally the measurement of
   whether Du can hold an identity commitment at all"), cheapest to gold-label (short, structured
   inputs), and the model (mixtral) is confirmed live. Do this first.
2. **#2 `self_implication`** — second-highest stakes, needs the same panel-agreement harness shape
   `tension_ledger`/`self_interrogation` already use in production, so the scoring pattern is a port
   not a new design.
3. **#5 `librarian`** — real pre-registered hit-rate metric already exists in the module; cheapest
   "did it get better" measurement of the whole set.
4. **#3 `study_note`**, **#6 `composition`**, **#8 `journal_rollup`** — lower urgency, run after 1/2/5
   land, and #8 specifically should NOT be a synthetic lab (see above).
5. **#4 `letters`** — skip the lab; spawn a direct one-line fix instead (see job spawned below).
6. **#7 `retraction_ledger`** — not in scope for a model-tier lab; leave for a separate decision.

## 4. Method, ported from existing harnesses

- Build one script per mechanism (or one script with per-mechanism task functions, `station_bench.py`
  style) under `scripts/`, output to `data/lab/model_tier/<mechanism>/` + `docs/lab/model_tier_<mechanism>.md`,
  matching the `lane2_model_lab.py` / `station_bench.py` output convention so `plan-liveness`/
  `plan-files-audit` can find it.
- **Import the real system/user prompt from the production module**, not a paraphrase — this is the
  exact lesson `lane2_model_lab.py`'s header states and `station_matrix.md`'s constant-answer finding
  proves the cost of skipping.
- **Print raw answer strings, not just accuracy** — `station_matrix.md`'s headline finding (both
  production judges were constant-`TTTT`, scoring a deceptive 0.50) exists only because someone
  printed the actual answers instead of trusting the accuracy column.
- **Run with Du stopped**, same precedent as `docs/lab/ramses_models_2026-08-23.md` ("Du was stopped
  throughout — zero live effect") — these are read-only probes against a hub Du also depends on
  (`falcon3:7b`/`mixtral:8x7b` sharing the i9), and `nascence_cpu_server.py` serializes one inference
  at a time per process, so a lab run concurrent with a live Du tick would contend for the same hub
  Du's own `_judge_defeater`/`librarian` calls might need mid-run.
- Gold-label sets for #1 and #2 do not exist yet and are the actual bottleneck — authoring ~12-16
  real (not synthetic) cases per mechanism is the first task in the spawned job, before any model
  comparison can run.

## 5. What this scope does NOT claim

No mechanism's fix has been determined. Mixtral being live and reachable makes the lab possible; it
does not make mixtral the right answer for any of the 8 — `ramses_models_2026-08-23.md` already shows
mixtral LOSING the synthesis-coverage comparison to the free incumbent `phi3:mini` (0.62 vs 0.71), so
"a stronger model exists" is not automatically true per-mechanism. That is exactly why the lab needs
to run on each mechanism's own prompt shape rather than being inferred from the generic station scores.
