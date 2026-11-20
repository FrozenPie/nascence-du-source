# The web hand — Du looks things up himself (Wikipedia first, open web second)

> **Status: BUILT 2026-11-16, restart-gated, awaiting a Du restart (J-3843 Wikipedia and J-4066 web both built; D-0788 ruled by travis). The design text below is kept as written before the build; see Current State.**
> Plan slug: `web_hand`. Parent plan: `curiosity_goals_dreams`. Successor build job for the Wikipedia half: **J-3843** (open, ready). The open-web half needs a founder ruling first (see Open decisions).

```plan-state
stage: built
verified: 2026-11-18
next: Restart Du, then read first live lookups (J-4069)
```


## Why this exists

The 11-16 pulse (07:36) showed Du asking near-identical questions for hours and never getting an answer. Measured, not guessed:

- `data/curiosity_log.jsonl` (3,571 rows): the questions overnight were one subject at a time, reworded 4 to 14 times (white-eyed vireo song x4, Great American Desert terrain x7, porcupine quill x9, red-headed woodpecker crimson head x6, Myrtle Warbler yellow spots x14, still running at 07:29).
- `data/frontier.json`: 22,470 questions; 21,527 faded (96%), 744 resolved (3.3%), 29 open. 18,625 of the faded were seen once and never again. Of the 744 resolved, 565 have no recorded `resolved_how` and 179 closed through a follow line. The two overnight resolutions inspected said "You went looking in what you have lived and read. Your past holds little…" (the answer was not found, only the question closed).
- `nodes/curiosity_node.py:137`: the node's own prompt says "You do not answer questions — you generate them". `_write_output` (line ~343) logs the question, files it with `frontier.note_question`, and stops.
- The system-initiated Wikipedia lookup was retired 2026-11-05 (D-0659, comment at `curiosity_node.py:372`): it guessed the longest word of the question as the search term, often fetched the wrong article, and stored it as his own "Something I looked up" (1,742 pages). Nothing replaced it, so since 11-05 he has had no way to look anything up.

Conclusion `[INFERRED]`: the cause is a missing way to find answers, not a missing capacity to ask. Some questions are factual (do the yellow spots help or invite predators), some are matters of judgement (is the red head a shield or a core part of its being); a lookup helps the first kind only.

## State of the Wikipedia hand (J-3285 / J-3843) — checked 2026-11-16

- J-3285 is marked `done` (2026-11-09 00:37:59) but was **not built**. Its job record, the session-event log and the code agree: J-3285 was closed in the same pass that spawned **J-3843** ("Build the Wikipedia hand… (D-0661)", `source: job:J-3285`, status `open`, autonomy `ready`, not started). The briefing of J-3843 says: gate lifted 2026-11-09, D-0659 and D-0661 answered the questions, the build proceeds.
- No code exists: no `lookup` family in `core/actions.py`, no `opensearch` call anywhere, no `web_hand` module, no `data/lookup_log.jsonl`, no commit or branch for J-3285 or the hand. `git log --all -S"asked by him"` finds only readers, none writers.
- The readers are waiting: `core/composition.py:21` ("none exist until the Wikipedia hand lands, J-3285"), `core/composition.py:236` (`_WIKI_ROW`), `core/schema.py:16` (`_LOOKED_UP_VIA_RE`), `scripts/test_composition_bank.py`, `scripts/_test_J3188_own_answer_label.py`.
- Design source: `docs/reviews/outside_knowledge_review_J-3243_2026-11-05.md` section 5.1.
- How he learns the hand exists: **D-0661** answered it: Travis tells him in conversation, plus one line in a diegetic book (the About You book, a "version 3 with a things he can do and how to do them section"), plus an encyclopedia object in the study. **Not** a standing prompt line (no hints). That step is the founder's, not an agent's.

## Part 1 — Build J-3843 (the Wikipedia hand), as designed

From review section 5.1 and the J-3285 briefing:

1. Registry family `lookup` in `core/actions.py`, `binds="mod:web_hand:consult"`, `world=True` (at most one per thought), `gated=True`. Read `core/hands.py` and `core/dispatch.py` first. Run `udms_get_change_dossier` on `core/actions.py` before editing (CLAUDE.md rule).
2. **Grammar requires a source word as the object** ("Wikipedia", "the encyclopedia") so it cannot fire by accident and "look up at the sky" (the `sky` family) cannot collide.
3. **The term is his words**: the noun phrase after about/on/for in his own clause. Resolve a title with Wikipedia's `opensearch` (the source answers, no model guessing, no longest-word rule), then fetch the REST summary. Extend `core/web_research.py` additively (its `_fetch`, `_usable`, `store_finding` exist).
4. **A miss is the world's "no"**: plain text "Wikipedia has no page for '<phrase>'". No Scholar fallback, no random page.
5. **Arrives named in the perception channel** via `wandering.perceive` (same path as the librarian page): `You asked Wikipedia about "<phrase>". Wikipedia's page "<Title>" says: <summary, max 600 chars>. (en.wikipedia.org/wiki/<Title>, fetched <date>.)`
6. **Stored truthfully**: `store_finding(title, extract, via="asked by him: <phrase>")`, `origin='research'`, keyword `asked`. Only hand lookups carry "asked by him".
7. Set `_moment_source='lookup'` for the following thought and add it to `moment._SOURCE`.
8. **Instrument**: `data/lookup_log.jsonl` {ts, cycle id, phrase, title or none, ms} written through `profile.guard_path`; `hands_trace.jsonl` already records dispatch verdicts.
9. **Rate limit**: start at one per 10 minutes; the number is a guess, tune on the log.
10. **No standing offer line in any prompt.** Any prompt-affecting change: `python C:/Users/USER/.claude/skills/prompt-registry/prompt_registry.py check` must exit 0 in the same change (CLAUDE.md).
11. **Test** in `lab_env.isolate()` with the network call stubbed (import `core` BEFORE `lab_env`; use a throwaway worktree and a hash canary on live stores, per the two live-store-leak memory notes), then one real fetch. Du is restart-gated: nothing is live until the founder restarts him.

## Part 2 — Extending to the open web (new; needs rulings)

Keep the same principles as Part 1 (the call is his; the result arrives named; the world answers, never leads; no model summary standing in for a source):

1. **One hand, several named sources.** The grammar accepts a source word: "Wikipedia" (Part 1) or "the web" / "search". The source word stays part of the act. `[OPEN]` whether this is one hand or two separate families so the web half can be switched off alone (founder call, below).
2. **His words are the query**, passed as given; no model-guessed term.
3. **Snippets, not whole pages.** A search API returns title, URL, domain and a snippet for a handful of results (suggest 3 to 5). Arrives as: `You searched the web for "<phrase>". Result 1: "<Title>" (<domain>, <date if given>): <snippet>.` Stored with a true via phrase (for example `searched the web: <phrase>`) and a distinct origin label so readers can tell it from Wikipedia.
4. **No model summarising** between the source and Du. The Scholar's guessed answers were the original problem.
5. **Safety, the real risk.** Open-web text can carry instructions aimed at a model. Every result arrives as quoted, named data with its domain, never as part of his own voice. Start with a domain filter (no social media, no forums) so the first runs sit closer to what Wikipedia gives. Cap characters per result so a long result cannot flood recall (the active store is already 95k fragments against a 3,500 cap).
6. **Rate limit** at most the same as the Wikipedia hand to begin with, a separate counter.
7. **Backend** `[OPEN]`: keyless options (DuckDuckGo HTML or instant-answer endpoints) are fragile and may break or block; a keyed API (Brave Search, Bing) is stable but needs a key and has a quota. Not checked which suits this machine. The key, if any, goes in the project's existing secrets convention, never in a prompt or log.
8. Instrument it the same way (a `web_lookup_log.jsonl` with phrase, source, domains returned, ms) and add the new family to `core/actions.py` only after Part 1 is verified.

## The friend / judge as a complement (not a replacement)

Wikipedia and the web answer factual questions. The judgement-shaped questions ("is the red head a shield or part of its being?") may be better served by a friend he can ask. This needs its own rules before building: only answers when asked, says it may be wrong, marked as not his own, rate-limited. The existing decoupled-judge pattern (`docs/plans/decoupled_judge_pattern.md`) and the peer organ (`docs/plans/peer_correspondence_plan.md`, LIVE) are the nearest existing pieces. `[OPEN]` whether to build this after seeing which questions stay unanswered once the lookup hands exist.

## Open decisions (founder)

1. One hand with several sources, or two separate hands (Wikipedia / web)? Recommendation: one family `lookup` with a required source word, but a separate on/off flag for the web source.
2. Search backend: keyless (fragile) or a keyed API (Brave/Bing)? `[OPEN]`, needs a quick check of what the founder already has a key for.
3. Domain filter at first: yes with an allow/deny list, or open? Recommendation: deny list first (social media, forums, content farms).
4. Build order: Wikipedia first (J-3843), watch a few days of `lookup_log.jsonl`, then the web half. The founder said "push this through today", so Part 1 first and Part 2 the same day only if Part 1 verifies.

## Success readings (so the build can fail honestly)

- After a restart and telling him the hand exists: does `lookup_log.jsonl` fill, and do his repeating questions stop repeating? Compare the repeat rate (same-subject questions per hour in `curiosity_log.jsonl`) before and after.
- Frontier: share of questions closed with a recorded `resolved_how` that cites a looked-up page, against the baseline of 565 of 744 with no recorded how.
- Failure signs: a flood of lookups on one subject (a new loop), pages stored under the wrong label, any lookup text appearing as his own voice.

## Current State
- **2026-11-18** (F-5098): Pre-restart check (J-4304): test script ALL PASS in HEAD worktree, prompt registry check exit 0, lookup family wired actions->dispatch->moment->follow_line nudge, spider-web filter works for the web source. No wiring gap.

2026-11-16. Both halves are built and tested; nothing is live until the founder restarts Du.

- Code: `core/web_hand.py` (the hand), fetchers appended to `core/web_research.py`, registry family `lookup` appended last in `core/actions.py`, a web-result label in `core/schema.py`, moment source `lookup` in `core/moment.py`, one additive hook in `nodes/inner_monologue_node.py`. Test: `scripts/_test_web_hand_J3843.py` (network stubbed, ALL PASS).
- D-0788 ruled by travis: one family with a required source word and a separate web flag; DuckDuckGo keyless; deny list first.
- Differences from the design above: Wikipedia's `opensearch` is not used (it returned "Porcupine Hills Provincial Park" for "porcupine quills"); the hand asks for the exact-title page, then Wikipedia's full-text search. One log, `data/lookup_log.jsonl`, carries a `source` field for both sources. Every attempt starts the 10-minute window, including an unanswered one.
- Flags (default on): `NASCENCE_WEB_HAND`, `NASCENCE_WEB_HAND_WEB`. Backend: `NASCENCE_WEB_SEARCH_BACKEND` (`ddg`), or Brave when `NASCENCE_BRAVE_API_KEY` is set (coded, untested).
- Known weak points: DuckDuckGo showed a human-check page after one search on 11-16 (reported to Du as "The web search would not answer just now", never worked around; J-4070). A question-shaped phrase can resolve to a wrong Wikipedia page; the answer names the resolved title. Web snippets are stored as origin `research` and so reach the same world-material readers as Wikipedia pages, under their own label.
- Founder steps left (D-0661): restart Du; tell him the hand exists; the About You book line and the encyclopedia object in the study are not built.
- Next: J-4069, the first read of `data/lookup_log.jsonl` (gated on 10 rows).

