# J-3011 (F-3718, P-0065): does the chapter prompt plant affect?

Status: edit built, restart-gated. Verdict on the finding: **narrowed, not confirmed as stated**. Scripts:
`scripts/j3011_chapter_affect_check.py` (read-only, all 87 chapters), `scripts/j3011_chapter_prompt_ab.py` (re-run
clusters, nothing stored), `scripts/_test_J-3011_chapter_prompt.py`. Raw data: `docs/lab/J-3011_data/`.

## 1. Check over ALL 87 chapters (not the 5 + 20 asked for)

Live store opened `mode=ro&immutable=1` (WAL empty, Du down). 79 level-1 + 9 level-2 rows exist with origin='chapter'; 87
have members.

| Test | Result |
|---|---|
| Exact planted word, `anxi*` in chapter body | 7 of 87 chapters (same as F-3718). Members containing `anxi*`: c368e458 0/107, 994e2ead 0/72, b8456aba 0/54, c8f88b32 (L2) 0/4, 2b072555 2/149, ec8a7311 (L2) 1/9, 7a0f391f 11/429. So for 4 of 7 the word is in no member at all. |
| Broad feeling lexicon (anxiety family incl. worry, tension, unease, restless; relief; calm; fear; ...) | 57 of 87 chapters name some feeling; 44 name an anxiety-family word (60 sentences). For 60 of 60 anxiety-family sentences at least one member carries a word of the same family. The "members do not state it" claim does NOT hold on the broad lexicon: Du's own thoughts use tension/restless/worry constantly. |
| Embedding, sentence to members (store's own MiniLM, max cosine) | feeling-naming sentences 0.684 mean (n=113) vs the same chapters' non-feeling sentences 0.685 (n=377). A feeling sentence is no further from its members than any other sentence. This test cannot separate planted from carried affect. |
| Embedding, member to feeling prototype | Members of chapters that name anxiety score 0.317 mean against an anxiety prototype vs 0.295 for members of chapters that do not (relief 0.400 vs 0.339 over 6 vs 81 chapters; calm 0.326 vs 0.274 over 12 vs 75). Members of feeling-naming chapters do carry somewhat more of the feeling, but absolute similarity is low (0.3). |

Reading: the strict claim (chapters invent a named feeling no member states) is true for a handful of chapters (the four
`anxi*` ones above), and false as a population statement. The "weight of my anxiety lift" sentences are the clearest
cases and sit in the same 4-5 chapters F-3718 already named.

## 2. Before/after on re-run clusters (author falcon3:7b :11440, temperature 0.6, 4 runs per cell, same 8-member sample)

Different model from the original author (command-r7b on Ramses, not called). Metric is deterministic: `anxi*` count in
the output; feeling families named that the 8-member sample does not itself state.

| Cluster | arm | `anxi*` outputs | outputs naming a feeling the sample lacks |
|---|---|---|---|
| c368e458, 994e2ead, b8456aba, f0a4109f, 7b4cb854 (5 x 4) | old prompt | 2 of 20 | 4 of 20 |
| same | new prompt, first wording (with "or eased") | 0 of 20 | 4 of 20 (2 were `relief`, a word that wording itself contained) |
| c368e458, f0a4109f, 994e2ead (3 x 4) | final prompt ("or eased" removed) | 1 of 12 | 2 of 12 |

The old prompt primes `anxi*` weakly on falcon3 (2 of 20; the stored chapters show 7 of 87 from the original author, so
the two are not comparable), and the sample sizes are tiny: this is direction, not proof. The new prompt does not make the unsampled-feeling rate worse
(2 of 12 vs 3 of 12 on the same three clusters). No output echoed "anxious year" under either prompt.

## 3. What changed

`core/chapters.py`: new `_author_system_prompt()` used by `try_form_chapter`. Dropped the "anxious year" example (now
"a stretch of time"), dropped the unconditional "what (if anything) moved by its end", added "Say that something changed
only if the sample shows it changing" and "Name a feeling only if the sample states that feeling in its own words;
otherwise say what you did and thought, and leave mood out." Schema, person/tense, 4-7 sentences, `/no_think` unchanged.
Guards and storage untouched. Registry: P-0065 needs `set P-0065 --investigation stale`.

## 4. Not run

The original author (command-r7b) was not called (Ramses is the founder's machine). A replay on that model, n >= 20 per
arm, is the only test that measures the real priming size: spawned as a lab job. The existing planted sentences in the 4
stored chapters were not touched (live store, and D-0638 governs chapter releases).
