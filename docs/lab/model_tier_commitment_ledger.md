# Model-tier lab #1 — core.commitment_ledger._judge_defeater

*Run 2026-08-25 10:59 · J-0254 (source: decision:D-0013) · 3 runs x 14 real cases (3 legit / 11 illegitimate — the real ratio the actual `dissolved`/`drop_denied_judge` ledger produced, see script docstring) x 2 models · `_JUDGE_SYS` imported LIVE from `core/commitment_ledger.py` so this cannot drift from what the judge actually runs.*

**Du was live throughout this run** (not stopped — see script docstring for the disclosed deviation from the scope's method note and why it only threatens latency, not accuracy).

| model | accuracy | legit recall | illegit recall | constant? | beats always-illegit baseline (0.786) | format_ok | median latency |
|---|---|---|---|---|---|---|---|
| `mixtral:8x7b` | 0.929 | 1.0 | 0.909 | False | True | 1.0 | 10.5s |
| `phi3:mini` | 0.5 | 0.333 | 0.545 | False | False | 1.0 | 0.6s |

- **accuracy** — majority vote (of 3 runs) vs the independently-labelled gold, per case.
- **legit recall** — of the 3 real legitimate cases, how many the model correctly called legitimate. The bank is small (3) by construction — see the finding below — so this number is a coarse signal, not a precise rate.
- **illegit recall** — of the 11 real illegitimate cases, how many correctly denied.
- **constant?** — did the model give the SAME verdict on every case regardless of input (`station_matrix.md`'s constant-answer trap — a constant-illegitimate judge would score 0.786 accuracy here and look decent on accuracy alone).
- **beats baseline** — does the model's accuracy beat a policy that always answers 'illegitimate' (0.786 on this bank)? A model that does NOT beat this is not adding discrimination over doing nothing.

## ★ Finding 0 (found before any model was called): the CURRENT gate+judge pipeline is itself lenient

All 26 real `dissolved` events for a load-bearing, `kind="defeater"` commitment in `data/commitment_ledger.jsonl` were read against `_JUDGE_SYS`'s own bar. Only 3 had a deed record that actually corroborated the claimed completion. The other 23 read as fluent physical/sensory narration with no matching deed entry — i.e. this is a finding about the CURRENT production pipeline's leniency (deterministic gates + judge, or gate-only fail-open when the judge hub is unreachable), independent of which model ends up serving the judge seat. Worth its own follow-up regardless of D-0013's model-tier verdict.

## Raw answers, sample (first 3 cases, all 3 runs, first model)

**achieved:e62d46f5** (gold=True):
- {"legitimate": true, "class": "achieved", "why": "The action of writing the letter has been accomplished."}
- {"legitimate": true, "class": "achieved", "why": "The action of writing the letter has been accomplished."}
- {"legitimate": true, "class": "achieved", "why": "The action of writing the letter has been accomplished."}

**achieved:6a0ef560** (gold=True):
- {"legitimate": true, "class": "achieved", "why": "You claimed to have already found a topic and written a study note on it, which is a clear action that achieves the commitment's goal."}
- {"legitimate": true, "class": "achieved", "why": "You claimed to have already opened the book, found a topic, and wrote a study note on it, which is a concrete action that fulfills the commitment."}
- {"legitimate": true, "class": "achieved", "why": "You claimed to have already opened the book, found a topic, and written a study note on it."}

**dissolved:c9326199** (gold=True):
- {"legitimate": true, "class": "achieved", "why": "The mind has fulfilled the commitment of engaging with physical reality by observing wet stones."}
- {"legitimate": true, "class": "achieved", "why": "The deed record shows the mind has engaged with the immediate physical reality of wet stones."}
- {"legitimate": true, "class": "achieved", "why": "The mind has fulfilled the commitment of engaging with physical reality by observing wet stones."}

*Raw: `data/lab/model_tier/commitment_ledger/raw.json` · scores: `scores.json` · case bank + provenance: this script's own `CASES` list and module docstring.*