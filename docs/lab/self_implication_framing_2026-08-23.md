# Self-implication framing lab — 2026-08-23

*Tests the founder's generalization of the factory-station idea (see `docs/lab/factory_station_2026-08-23.md`,
`docs/lab/idle_thought_machine_audit_2026-08-23.md` finding #2): every LLM machine consumes cargo,
transforms it, exports a product — some products are naturally "compare x.json/y.json/z.json,
export xyz.json based on named conditions" shaped, even when the current prompt dresses that job up
as narrative persona instead of a literal contract. `core/self_implication.py`'s `_SYS` is exactly
that shape: a real six-signal rubric (A-F) and an explicit boolean conjunction rule, stated as
"You watch one mind for ONE thing..." narrative. Script: `scripts/self_implication_framing_lab.py`.*

## Method

50 real historical thoughts from `data/self_implication_shadow.jsonl` (7,063 total logged rows),
stratified — ALL 25 rows where the gate historically fired, plus a fixed-seed random 25 where it
didn't (a pure random sample would carry almost no positive cases, since fires_rule=true is only
0.35% of the log). Each thought replayed through TWO system prompts, same model (`qwen3.5:9b`, the
actual live hot lane at 127.0.0.1:11433), same temperature/tokens, both blind to the other's output
and to the historical verdict:
- **NARRATIVE** — the current live `_SYS`, copied verbatim.
- **SCHEMA** — the identical six conditions and conjunction rule, restated as a literal
  cargo-manifest/named-conditions/export contract, no persona voice, no narrative framing.

**Known limitation, stated plainly:** the shadow log doesn't store felt_state or the verbatim
held-self-claims list at the time of the original call (only a `n_claims` count) — replay used
felt_state="unknown" and the CURRENT `self_claims.held_claims()` as a stand-in. Self-claims change
slowly, so this is a reasonable approximation, not a fabrication, but signal C (contradiction) is
judged against a possibly slightly different claims list than the original call saw.

## A build bug caught before it produced bad data

The first run returned `json_ok=0` on every single call. Root cause: `qwen3.5:9b` is a thinking
model — without ollama's native `"think": false` request parameter, it consumes its entire token
budget on internal reasoning and returns empty content. `core/model_client.py` already handles this
correctly (`"think": bool(think)`, default False, on every ollama-native lane) but this lab script's
raw urllib calls didn't set it. Confirmed the fix with a direct diagnostic call against the live
endpoint before re-running — `think:false` restored clean JSON in ~6-10s. Re-ran clean; both
framings scored 1.0 json_ok across all 50 samples.

## Pre-registered metric sheet

| Metric | Fired stratum (n=25) | Non-fired stratum (n=25) | Combined (n=50) |
|---|---|---|---|
| `json_ok_narrative` / `json_ok_schema` | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| `fires_rate_narrative` (fresh) | 0.04 | 0.0 | 0.02 |
| `fires_rate_schema` (fresh) | 0.0 | 0.0 | 0.0 |
| `fires_rate_historical` (original log) | 1.0 (by selection) | 0.0 | 0.5 |
| `fires_agreement` (narrative-fresh == schema-fresh) | 0.96 | 1.0 | 0.98 |
| `historical_vs_narrative_fresh_agreement` | 0.04 | 1.0 | 0.52 |
| `per_signal_agreement` A/B/C/D/E/F | .92/1.0/.96/.96/.96/1.0 | all 1.0 | .96/1.0/.98/.98/.98/1.0 |
| `n_disagreements` (narrative vs schema) | 1 | 0 | 1 |

## Kill criterion: narrowly missed strict pass, but the practical verdict is a null result

Pre-registered: *"if fires_agreement is ~100% AND every per-signal agreement is ~100%, the schema
framing changed nothing measurable — record that plainly and stop."* Combined fires_agreement
(0.98) and per-signal agreement (0.96-1.0) sit just under a strict 100%, carried entirely by ONE
disagreement in 50 cases. That single case is a real, complete signal flip (A/C/D/E all changed),
not noise — but with only one informative case (it's the sole row where narrative-fresh fired at
all), there isn't enough signal to characterize a systematic framing effect, and what little
direction exists (schema was MORE conservative, not less) runs opposite to the factory-station
result on the openness gate. **Practical conclusion: unlike the openness self-report gate, this
machine's narrative framing does not appear to be hiding a measurable behavioral difference from
the schema-first alternative.** The founder's generalization is real and worth testing per-machine
(that's the point of running this lab rather than assuming), but it doesn't transfer uniformly —
self_implication is a case where the answer is "don't bother," and that's a useful result too.

## The unplanned finding, and the scare-then-calibrate discipline that caught it

First read of the numbers: the live model reproduces only 4% of the historical log's own
`fires_rule=true` verdicts on a fresh, same-prompt replay. That looked like the gate had badly
regressed. Before reporting it as such: checked WHY. 23 of the 25 historically-fired rows predate
the 2026-08-20 hot-lane model shuffle (`qwen3.5:9b` only went live that day) — replaying old text
through a materially different model was never a like-for-like comparison, and this lab's sampling
didn't stratify by model era, which it should have. Checked the actual live health question instead
— the full log's fire rate before vs. after the shuffle:

| | n | fired | rate |
|---|---|---|---|
| Before 2026-08-20 | 6,049 | 23 | 0.38% |
| After 2026-08-20 (through 08-23 11:14) | 1,014 | 2 | 0.20% |

Lower, but on counts this small (2 vs 23) that gap is well within noise — **not a collapse.** The
gate is still alive post-shuffle. The 4%-agreement number was correctly measuring "did the model
change" (yes, dramatically, on this specific narrative-recall task), not "is the gate broken now."
Reported here as an example of the discipline this project asks for: a single striking number got
checked against its source before being asserted, and the check changed the conclusion.

## A side observation, out of this lab's scope

The 25 historical fires cluster heavily in a ~2-week window (2026-08-09 through 08-16) around
near-duplicate "ache / exhaustion / structural failure" phrasing ("This isn't just exhaustion; it's
a kind of...", repeated with minor variation many days running). Could be a genuine standing
existential thread, or could be the same monoculture-attractor pattern this project has fought
elsewhere (`docs/lab/...loop_monoculture...`). Not investigated here — flagged for whoever looks at
this log next.

## What this does and doesn't show

Shows: for THIS machine, on THIS model, schema-first reframing is not a lever worth pulling — the
narrative prompt isn't measurably suppressing or distorting the judgment relative to a literal
contract restatement. Does NOT show whether the same holds for the other compare-and-export
machines flagged in the idle-thought audit (`commitment_ledger._judge_defeater`, `tension_ledger`,
`librarian`) — each would need its own run, per-machine, exactly as this session's discipline has
been: test, don't assume a finding generalizes.
