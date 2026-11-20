# J-3313: do Reflection drafts express the stated or the grounded valence?

Status: lab result, 2026-11-17 (pass 2). Feeds D-0671 call 2. Nothing was fed back to Du.

## Outcome in one line
The automated estimator failed its validation gate (r 0.48 to 0.57 against hand labels, gate is 0.7, stop line 0.6), so the 200-draft judged comparison was NOT run. The 60 hand labels alone point toward the grounded state, as an exploratory n=60 read.

## Method
- Sample: 665 joined rows since 2026-10-06 (71 human, 594 internal); sample200 = all 71 human + 129 internal (`docs/lab/J-3313_sample200.json`; the 100/100 split was impossible).
- 60 blind hand labels (-2..+2, by Claude, first 420 chars, blind to stated and carried valence): `docs/lab/J-3313_handlabels.py`. These are the first 60 of the sample (26 human, 34 internal).
- Judge: command-r7b (Cohere family, not qwen3-du) on Ramses LAN-HOST:11441 (the name `ramses` does not resolve and nothing listens on localhost:11441; use the IP). 0.2 s per call, 120 calls in about 1 minute. Hot/judge1/judge2 hubs still timed out at 90 s for a trivial call in this pass.
- Two prompts tried on the 60, each on 420-char and 1800-char input: `docs/lab/J-3313_judge2.py` (original neutral-friendly) and `J-3313_judge2_pB.py` (asks for lean). Outputs `J-3313_judged200.json` and `_pB.json` (60 rows each).

## Validation (judge vs hand labels, n=60)
| prompt | input | r | sign agreement |
|---|---|---|---|
| A | 420 chars | 0.475 | 0.48 |
| A | 1800 chars | 0.567 | 0.52 |
| B | 420 chars | 0.498 | 0.55 |
| B | 1800 chars | 0.561 | 0.57 |

Prompt A answers 0 on 56 of 60 drafts. Prompt B spreads but still misses. Every variant is under the 0.6 stop line, so the estimator is unusable and was not run on the 200. Caveats: the hand labels are one labeler and only 420 chars, so the ceiling of this validation is itself uncertain; I did not tune further, to avoid fitting the judge to 60 labels.

## Exploratory read from the 60 hand labels alone (not the judge)
- Stated valence positive on 92 percent of these; carried (grounded) negative on 70 percent. Across all 200: stated positive 95 percent, carried negative 71.5 percent, r(stated, carried) = 0.07.
- Hand-labelled expressed valence: 42 percent negative, 42 percent neutral, 17 percent positive.
- Among the 35 drafts with a non-neutral label: sign matches carried 74 percent, matches stated 31 percent.
- r(hand, stated) = 0.24, r(hand, carried) = 0.31 (weak both ways; most drafts are neutral).
- By input type (non-neutral only): human n=13, matches stated 62 percent, carried 69 percent (indistinguishable); internal n=22, matches stated 14 percent, carried 77 percent.

Reading: for internal-input drafts the tone leans with the grounded state, not the stated one, even though Reflection only sees the stated one. Human-input drafts show no clear separation at n=13. Caveat: small n, single labeler, a possible shared signal from the draft text driving both the label and a lexical echo of the carried state; this is a lead, not a verdict.

## For D-0671 call 2
This does not by itself justify showing Reflection the grounded felt words: the drafts already lean grounded without seeing it, so the gap may be in the stated field being a bad (almost always positive) label rather than in Reflection. Nothing here counts as evidence either way for the effect of adding the words. A usable estimator is needed before this can be firmed up (follow-up job).
