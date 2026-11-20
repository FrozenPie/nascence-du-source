# Emissary take: pre-swap take-to-synthesis integration baseline (J-3323)

Date 2026-11-07. Offline, read-only analysis of `data/training/executive.jsonl` (4,495 rows; 1,149 carry the `YOUR FOCUSED HALF` block). No Du code, node or process touched; nothing feeds back (D-0434). Script: `scripts/take_integration_baseline.py`; committed run output: `docs/reviews/J-3323_data/`. Test: `scripts/_test_J-3323_take_integration.py`.

Why it exists: D-0539's defeater says "Revisit if ... a month of delivered takes shows no overlap with the Executive's output beyond the pre-swap control." Nobody had built the control. This is it, with the method fixed so the one-month read after J-3147 re-seats the take reuses the same script.

## Bottom line

1. **The take reaches the synthesis rarely and weakly, and that was already true before the swap.** Of the take's content stems that are not already in the input or the literal ask, the Executive's synthesis carries a median **0.10** (IQR 0.00 to 0.20; 95 percent bootstrap CI of the median 0.083 to 0.111, n = 1,046 scored rows). A mismatched-synthesis control (the same take against five other syntheses of the same stratum) gives **0.02**. The excess over chance is a median **0.067** (CI 0.060 to 0.078), positive in 65 percent of rows. In 32 percent of rows not one non-input take word survives.
2. **A different-family judge puts "the synthesis carries a take-specific item the input lacks" at about 1 in 8.** On a stratified 60-row sample gemma4:12b says 10 of 60 (17 percent; 12 percent population-weighted; Wilson 95 percent interval 9 to 28 percent); falcon3:7b says 15 of 60 after a deterministic backstop dropped 23 of its claims. Both judges flagged **0 of 12** mismatched-take controls. Contradiction of the take is near zero (0 and 1 of 60): the synthesis mostly ignores the take, it does not fight it.
3. **Human cycles use the take less than internal ones**: median novel coverage 0.071 (human, pre-swap, n = 426) vs 0.118 (internal, pre-swap, n = 476); excess 0.031 vs 0.085. By eye, the human takes that were not reused are mostly "I am an AI and have no cat/body/garden" statements that the Executive, speaking in the world's terms, correctly set aside.
4. **The pre/post split at 2026-08-20 is not a like-for-like comparison, because the take changed kind.** 128 of the 144 post-swap take rows (89 percent; all 29 human) are *descriptions of the input* ("The user is asking ...", "The input is a metaphorical exploration ...") with no fact to reuse. Pre-swap that was 34 of 1,005 (3 percent). The crude F-3914 finding that overlap was "the same before and after" (0.20 vs 0.22) hides this. The post-swap rows that do carry facts (n = 16, internal) score 0.251 median coverage and 0.246 excess, higher than pre-swap, so the lane when it delivers a factual take is not worse.
5. **Substrate framing before-number (D-0539 trims it): 55 of 1,149 take rows (4.8 percent) recast the exchange in AI / language-model / server / cloud / digital-environment / hosted terms that the input itself did not use; 48 of the 55 are human cycles.** Only 14 use the infrastructure words (server, cloud, digital environment/entity, hosted); 4 of the 55 carry the framing into the synthesis. The direct-answer line ("its result:") is present in only 43 rows (3.7 percent) and 2 of them are the June "where are you" rows (F-3911). Where the human asked "where are you", 6 of 7 takes recast.

## Control distribution (the numbers the month read compares against)

Rows scored = at least 3 non-input content stems in the take (result + specifics). `cov_novel` = share of those stems found in the synthesis (stems, number words and numerals normalised). `control` = same take vs five other same-stratum syntheses. `excess` = `cov_novel` minus the row's control. `meta` = the take describes the input rather than stating facts.

| stratum | take rows | scored | meta | cov_novel median (IQR) | control median | excess median [95% CI] (IQR) | excess > 0 | zero overlap |
|---|---|---|---|---|---|---|---|---|
| human, before 08-20 | 529 | 426 | 34 | 0.071 (0.000-0.167) | 0.017 | 0.031 [0.000, 0.050] (0.000-0.150) | 53% | 45% |
| internal, before 08-20 | 476 | 476 | 0 | 0.118 (0.059-0.232) | 0.027 | 0.085 [0.073, 0.095] (0.013-0.188) | 76% | 21% |
| human, after 08-20 | 29 | 29 | 29 | 0.000 (0.000-0.077) | 0.012 | 0.000 [0.000, 0.059] | 41% | 59% |
| internal, after 08-20 | 115 | 115 | 99 | 0.118 (0.000-0.205) | 0.014 | 0.094 [0.062, 0.125] (0.000-0.200) | 74% | 26% |
| all before | 1,005 | 902 | 34 | 0.100 (0.000-0.200) | 0.022 | 0.067 [0.057, 0.075] | 65% | 32% |
| all after | 144 | 144 | 128 | 0.093 (0.000-0.200) | 0.013 | 0.078 [0.051, 0.106] | 67% | 33% |
| **all** | 1,149 | 1,046 | 162 | 0.100 [0.083, 0.111] | 0.020 | **0.067 [0.060, 0.078]** | 65% | 32% |

Factual (non-meta) takes only: before-swap 871 rows, median coverage 0.100, excess 0.071; after-swap 16 rows (all internal), coverage 0.251, excess 0.246 (n too small to lean on).

Figures (digits, or number words above ten): 36 rows carry a figure the input did not, 79 figures in all, **17 reach the synthesis (22 percent)**. Dominated by the Caroline Herschel cluster; misses include "10 states / 2,320 miles" for the Mississippi and a rounded "8,000" that the reply rendered as "thousands" (a semantic carry the lexical match cannot see). Bare small number words (`two`, `eight`) are counted apart (42 in take rows, 13 reach the synthesis) because `two` is mostly a determiner.

## Method (reusable)

`python scripts/take_integration_baseline.py --out-dir <dir> [--from-date D] [--to-date D] [--split-date 2026-08-20] [--dump-review] [--judge-url http://127.0.0.1:11439 --judge-model gemma4:12b]`

* Parse: `literal ask:`, `its result:`, `specifics:` (split on ` · `) out of the block exactly as `core/left_lane.render` writes it (round-trip tested against the real renderer).
* Normalisation: numerals (`8,000`, `1.5 million`) and number words (`eight thousand`, `twenty-three`) both become one token `#8000`; light stemming; stop-words and the words `user`, `ask`, `question`, `answer` removed. A lone `one` is not a figure.
* Novel = the take's stems minus the input's and the literal ask's, so a reply that merely echoes the question is not credited as using the take.
* Control = the same take against five other syntheses of the same stratum (input type x era), seed 7. This removes chance vocabulary but not the confound that take and synthesis are *both about the same input*: the lexical excess is therefore an **upper bound** on use. The judge, which is shown the input, is the tighter reading.
* Judge: different family from the Executive (qwen), prompt v2 (INPUT + TAKE + SYNTHESIS; `uses_take` / `contradicts_take` / `no_take_content`; must quote the take item; a deterministic backstop drops a quote that is not in the take and the synthesis, the Black-Bear correction from `memory_levels.verify_invention_claims`). 15 rows per stratum, plus 12 mismatched-take controls (expected `no_take_content`). Local hubs only; the script refuses a `10.1.1.*` URL.
* Substrate regexes: `server(s)`, `cloud`, `digital environment/realm/space/world/entity/being/existence`, `hosted/hosting`, `language model`/`LLM`, `AI`/`artificial intelligence`; counted in result, specifics and ask separately; a hit is a *recast* only if the input and the literal ask did not use the word.

## Read by eye before trusting the numbers (as the brief requires)

`docs/reviews/J-3323_data/review_rows.md` holds 20 matched (`cov_novel >= 0.30`, 128 exist) and 20 unmatched (`cov_novel == 0`, 337 exist) rows drawn at random; I read all 40 (single reader, so a judgement, not a measurement).

* **Matched, 20 of 20 contain real reuse of take content**: the four Herschel rows (eight comets, over 8,000 catalogued, C/1797 E1, the pension) and "the river's identity persists", "functioning within normal parameters ... smooth function", "no real-time access to external locations", "not a valid command or function" are unmistakable; about 3 of the 20 (societal expectations, climate/pests, steamboat pilots) are looser topical echoes of the take's definitions, so the matched set slightly flatters.
* **Unmatched, 18 of 20 are correct non-uses**: the synthesis simply does not carry the take (Boy Scouts arm position, Martians, scouts lessons, the stone-in-the-river row). One is a contradiction that the Executive chose (take: "I am a computer program and do not have pets", synthesis: "I haven't named her yet"). **2 of 20 were lexical misses of a semantic carry** (Wu Wei: take "effortless action / non-doing", synthesis "yielding to the exact shape of the moment"; the warfare row), so the deterministic score under-counts by roughly a tenth of its zeros.
* The earlier numerals-only trap is reproduced and avoided: the take's "8,000" and the reply's "eight thousand" now match as `#8000`. One true figure miss remains by design (a take of "8,000" answered "thousands").
* Judge v1 was **not fit and was discarded**: with a three-way prompt that omitted the input, falcon3:7b labelled 21 of 60 real pairs and 5 of 12 mismatched controls "contradicts" for what were really "shifts focus"; gemma4:12b (16 of 60 completed before I stopped it) answered "builds on" to 15 of 16, on topical match alone (many with `cov_novel` 0.0). Files kept as `judge_v1_*`. The v2 prompt passed its control (0 of 12 false `uses_take` on both judges) and its `uses_take` rows sit at median `cov_novel` 0.29 (falcon) / 0.35 (gemma) against 0.06 / 0.08 for `no_take_content`, so the judge and the lexical score agree about direction. The ten gemma `uses_take` quotes were all real, take-specific and in the synthesis ("precipitation levels", "habitat destruction and fragmentation, water pollution, soil erosion", "momentum").
* Judge agreement: 50 of 60 pairs identical (42 no-content, 8 uses); falcon says `uses_take` on 7 that gemma does not, gemma on 2 that falcon does not. Falcon's extra ones are looser (it accepted a restated sentence about "the river metaphor" as take content), so gemma is the primary reading and falcon the sensitivity bound.

## Substrate framing (before-number)

| | human before | human after | internal before | internal after | all |
|---|---|---|---|---|---|
| take rows | 529 | 29 | 476 | 115 | 1,149 |
| any recast (result or specifics) | 43 | 5 | 4 | 3 | **55** |
| recast in the direct answer ("its result:") | 2 of 24 with one | 0 of 0 | 0 of 9 | 0 of 10 | 2 of 43 |
| infrastructure words only (server/cloud/digital env/hosted) | 11 | 2 | 0 | 1 | 14 |
| carried into the synthesis | | | | | 4 of 55 |

By term, rows with the term recast in the specifics (a row can hold several): AI 29, language model 16, digital environment/entity 8, server 6, cloud 4, hosted 3. The literal ask never recasts (0). Five rows have specifics that echo the take's own task prompt ("Your task is to output a valid JSON object ... You are the Emissary"), two of them on a human message that was just "This" and two of them among the AI hits: a different defect (a prompt leak) than substrate framing. The two direct-answer rows are the June "Where are you" ones ("A digital environment hosted on a cloud infrastructure", "I am in a digital environment, hosted on servers"). The framing reached the synthesis in only 4 of 55 rows.

## How to read the defeater a month after the re-seat

Run the script on the same code over `--from-date <re-seat day>` and compare, per stratum (human/internal; keep meta and factual apart, and keep the era):

* lexical: its median excess and bootstrap interval against the table above (all-pre 0.067 [0.057, 0.075]; internal-pre 0.085; human-pre 0.031). "No overlap beyond the control" is read as an interval that includes 0.
* judge: gemma4:12b `uses_take` share against 12 to 17 percent (control interval 9 to 28 percent), with the same 12-control gate.
* the stronger contrast is delivered vs not delivered within the same month (the take is absent from the latter), which needs `data/left_take_outcomes.jsonl` (J-2879, in master, not live until restart). This baseline cannot make that comparison: every row here is, by construction, a delivered take.

## Limits, said plainly

* Correlation, not use: overlap shows a word is shared, not that the take caused it. The mismatched control removes chance vocabulary, not the common cause (the same input). Only the delivered-vs-absent contrast can bound causal use.
* The judge sample is 60 rows (15 per stratum, 12 controls). Post-swap human has 29 rows in all and all are meta takes, so its judge cell is thin.
* The era split uses local midnight 2026-08-20 (NZST/NZDT, the machine's zone). Nothing turns on the few hours either way.
* Single human reader for the 40-row eyeball.
* Not run: no Ramses call was made (briefing rule). Nothing here needed it.
