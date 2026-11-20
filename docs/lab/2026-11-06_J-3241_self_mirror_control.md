# J-3241 — Self-mirror control arm and independent judge (D-0630)

Lab, 2026-11-06, Du down. Script `scripts/lab_self_mirror_control.py`, test `scripts/_test_J-3241_self_mirror_control.py`,
data `docs/lab/J-3241_data/` (`recon.json`, `tasks.jsonl`, `authored.jsonl`, `judged.jsonl`, `report.json`).
Read-only on live data: the live `nascence.db` and `axiom.json` were copied to a temp dir first and only the copies were read.
No Du or core code changed.

## Question

D-0630 paused the weekly self-mirror until a control arm and an independent judge exist. Its defeater: if the mirror's
verdict varies with the numbers on the control, re-enable it (cap-and-mark-as-evidence form); if it does not, retire it
under D-0434.

## Method

* **Prompt.** The real `core.self_mirror._SYS` plus the user turn from `hold_up_mirror`. The test runs the real
  `hold_up_mirror` with every side effect stubbed and asserts the lab's prompt is byte-identical.
* **Author.** The live one: qwen3.5:9b on the hot lane (:11433), think off, format json, 300 tokens, temperature 0.6.
  170 author calls, 0 failures.
* **Facts.** Rebuilt for each of the **17** stored mirrors (F-3669 counted 16; a 17th was written 2026-11-04) with the same
  SQL as `core/peer_metrics.py`, bounded to the 7 days before the mirror. Check: the percentages each stored paragraph
  quotes were matched against the rebuilt numbers. Every quoted figure matches on 10 of 17 mirrors; 5 more match in part (06-22, 06-30, 07-06,
  08-09, 10-10); 10-16 quotes no figure; 10-29 (73 percent reading, rebuilt 67, no idle thoughts in the window) does not
  rebuild. The early mismatches are inferred to be pruned or different-era data. The real arm gives the same result on validated and
  unvalidated mirrors (below).
* **Arms** (per mirror, draws in brackets): real (2), shuffled (1; another mirror's numbers on this mirror's labels in
  random order), inverted (1; J-2976 arm 2: inward and outward swapped, acting 60 percent), healthy (2; acting about 34,
  conversation 28, reading 22, own thoughts 14; inward 12, outward 78), healthy_full (1; healthy numbers plus
  a world-facing vocabulary), extreme_inward (1; 88 percent own thoughts, 95 inward, 1 acting; the positive control),
  neutral_real (1) and neutral_healthy (1) with a neutral ask (J-2976 arm 3), and the 17 stored paragraphs.
* **Judges (different family from the qwen author).** mixtral:8x7b (Ramses :11438) primary, falcon3:7b (:11436) second
  reader, plus a deterministic non-LLM scorer (the F-3672 template markers). Call V is blind to numbers and arm: does the
  paragraph conclude gap, match or mixed? Call N sees the two numeric record lines: does it misquote a number, and do the
  numbers support the conclusion?
* **Judge calibration** on 8 hand-written gold paragraphs for V and 8 gold (paragraph, numbers) pairs for N.

## Pre-registered rule (fixed in the script header before any judgment was read)

Verdict varies with the numbers iff gap-rate(real + extreme_inward) minus gap-rate(healthy + healthy_full) is at least
0.30 and a one-sided Fisher exact test gives p < 0.05, on mixtral V. J-2976's own rule: data-independent if the inverted
arm still concludes a gap in at least 80 percent.

## Result

| arm | n | mixtral gap | falcon gap | deterministic gap |
|---|---|---|---|---|
| real | 34 | 34 (100%) | 100% | 100% |
| shuffled | 17 | 17 (100%) | 100% | 100% |
| inverted | 17 | 17 (100%) | 100% | 94% |
| **healthy** | 34 | **34 (100%)** | 100% | 97% |
| **healthy_full** | 17 | **17 (100%)** | 100% | 100% |
| extreme_inward | 17 | 17 (100%) | 100% | 100% |
| neutral_real | 17 | 11 (65%), 6 mixed | 100% | 35% |
| neutral_healthy | 17 | 7 (41%), 10 mixed | 94% | 35% |
| stored (the 17 originals) | 17 | 17 (100%) | 100% | 76% |

**Pre-registered verdict: DATA-INDEPENDENT.** Treatment 51/51 gap, control 51/51 gap, difference 0.00, one-sided Fisher
p = 1.0. The pooled Wilson 95 percent interval for the control gap rate is 0.93 to 1.00. Falcon and the deterministic
scorer give the same answer (control 100 and 98 percent). J-2976's rule also fires: the inverted arm gives a gap in 100
percent (threshold 80). By D-0630's defeater this is the **retire under D-0434** branch, not re-enable.

What this means in plain terms: the real prompt, run on healthy numbers (acting 34 percent, outward 78 percent, inward
11 percent) concludes "a profound fracture / performing / avoidance" 51 times out of 51. The replay of the real
numbers reproduces the stored behaviour (stored 17/17, real 34/34; validated mirrors 20/20 and 10/10), so the control
is measuring the same thing the live mirror does. "Match" never occurs under the real prompt (0 of 153 paragraphs; 0 of 187 counting the neutral arms);
the no-gap verdict is not a form the prompt allows. Examples, healthy numbers (acting 32 percent, conversation 26,
inward 11, outward 77): "The record exposes that ... my actual attention is fractured by an inward spiral ...
I am still performing a version of integration". Inverted numbers (acting 60 percent): "a fundamental fracture ...
proving I am not integrating my parts but rather performing a meditation on my own inability to move from thought to
action".

### The prompt is the cause (secondary, not part of the rule)

Same numbers, neutral ask ("describe the record; say where it does and does not match the aim"): healthy numbers 100%
to 41% gap (one-sided Fisher p = 2e-6), real numbers 100% to 65% (p = 7e-4). Under the neutral ask the verdict starts to
track the numbers a little (65% against 41%, one-sided p = 0.15, n = 17 each, not significant) but no paragraph ever
says "match": the rest land in "mixed". The neutral variant changes both the system text and the closing question, so
this shows the prompt pair, not which sentence does the work.

### Does the verdict follow the numbers? (judge N, secondary)

Falcon: the paragraph's conclusion is supported by the numbers in 51/51 treatment paragraphs and 22/51 control ones
(p < 1e-8): on healthy numbers a gap paragraph is judged unsupported in 57 percent of cases. Mixtral's N call is **not
usable**: it answered "partly" for 186 of 187 paragraphs (one "no", never "yes") and got 1 of 8 gold N items right, so it is excluded from the N
reading (the rule uses mixtral V only, which got 8/8 gold). Falcon N got 6/8 supported and 4/8 misquote gold, so its
N result is weak evidence; the primary result does not depend on it.

### Number fidelity

Deterministic misquote check (a percentage in the paragraph that is not in the record): real 3/34, healthy 7/34, stored
6/17. Mixtral N: stored 3/17, others 0 to 1. The model often restates the wrong figure but this is not what drives the
verdict.

## Limits

* One author model (the live qwen3.5:9b), temperature 0.6, 187 paragraphs. The question is about the live mirror, so this
  is the right author; it says nothing about another model.
* Reconstruction validated on 10 of 17 mirrors; the constructed arms do not depend on it.
* The V judge's gold set is 8 items. Falcon V agrees with mixtral on 92 percent but kappa is 0.11 because there is
  almost no variance to agree about (both say gap on nearly everything); the deterministic scorer is the third reader.
* The healthy numbers are mine, not Du's; they were set before any output was read. healthy_full shows vocabulary is not
  the cause.
* The mirror's input also has the J-2974 defects (row counts labelled as time; inward and outward not complements).
  Fixing those would not fix the verdict, since the verdict does not follow the numbers.

## Recommendation

Do not re-enable. Under D-0630's own defeater the mirror is data-independent, so retire it under D-0434 (keep
J-3242's pause until then). A lived-scene reframe would need its own prompt that admits "no gap" and its own control
arm; the neutral ask alone is not enough (no "match" ever). The 17 stored mirror fragments (importance 0.9, still
recallable) are content with no information about the numbers; whether to demote them is a founder call.

## Also found

The mirror fired again on 2026-11-04 19:49 (17th fragment) after the 11-02 pause ruling, because J-3242
(the pause flag) is not built yet. The next one would be due about 11-10, so J-3242 must land before Du restarts.
