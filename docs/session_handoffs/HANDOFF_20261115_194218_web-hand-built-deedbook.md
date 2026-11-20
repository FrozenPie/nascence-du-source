# Web hand built (Wikipedia and web lookup), and The Deedbook, a manual of Du's hands

## Session timing
- **Session started:** 2026-11-15 19:10:05 UTC
- **Last message before wrap:** 2026-11-15 19:42:17 UTC
- **Wrapped:** 2026-11-15 19:42:18 UTC

## Summary
The founder asked for the Wikipedia hand and the open-web search to be ready for Du to use today (T-0137). Both halves were built, tested and committed; nothing is live until Du restarts. The founder then asked for a user manual of all Du's action hands; it was written as a docs file and as a book on Du's shelf.

## Decisions
- D-0788 ruled by travis (through a questionnaire in this session): one `lookup` family with a required source word, and a separate on/off flag for the web source; backend DuckDuckGo, keyless; a domain deny list first. Defeater recorded: the hand unused after a week of `data/lookup_log.jsonl`, web results appearing in his thoughts as his own voice, or DuckDuckGo breaking, blocking or rate-limiting.
- No ruling was made by Claude. Earlier rulings this rests on: D-0631, D-0659, D-0661.

## Builds
- J-3843 (Wikipedia hand) and J-4066 (web source) are done. Evidence in F-4808. Commit `a962d0c4` on master.
  - `core/web_hand.py` (new): the hand `consult(text)`, the phrase parser, a rate limit of one call per 600 s per source (every attempt starts the window, an unanswered one too), the domain deny list, and the log `data/lookup_log.jsonl` (ts, cycle, source, phrase, title, outcome, ms, domains).
  - `core/web_research.py` (appended only): `wiki_titles`, `wiki_page`, `web_search` with a DuckDuckGo backend and a Brave backend, `store_web_results`.
  - `core/actions.py`: family `lookup`, appended last, world, gated, binds `mod:web_hand:consult`. Verbs: look up, look, ask, consult, search, check, query, read, find. Objects: wikipedia, encyclopedia, encyclopaedia, the web, internet.
  - `core/schema.py`: a web-search row (content starting `[Searched the web:`) gets its own label. `core/moment.py`: source `lookup`. `nodes/inner_monologue_node.py`: one additive hook that tags the thought after a lookup.
  - Flags, read from the environment, default on: `NASCENCE_WEB_HAND`, `NASCENCE_WEB_HAND_WEB`. Backend: `NASCENCE_WEB_SEARCH_BACKEND` (default `ddg`); Brave is selected when `NASCENCE_BRAVE_API_KEY` is set.
  - Test: `scripts/_test_web_hand_J3843.py` (network stubbed, log and state in a temp folder), ALL PASS. `prompt_registry.py check` reported every prompt site registered. No prompt names the hand.
- The manual: `docs/guidelines/du_hands_manual.md`, commit `3d625500`. It covers all 46 registry families. 89 example sentences were run through `literal_will.classify` and all read as a willed deed for the intended family; none was run against the world.
- The book: `data/books/The_Deedbook.txt` (in `data/`, which git ignores). `library_hand.shelf_books()` lists it; title signature `{deedbook}`, no clash with another title. It was not put on his desk and him opening it was not tested.

## Findings
- F-4809: Wikipedia's `opensearch`, the resolver named in the J-3243 design, returned "Porcupine Hills Provincial Park" for "porcupine quills". The hand uses the exact-title page (Wikipedia follows its own redirects) and then Wikipedia's full-text search, which returns "Porcupine". A question-shaped phrase can still resolve badly ("why the red-headed woodpecker's head is red" gave "Red squirrel"); the answer always names the resolved title.
- F-4810: DuckDuckGo's keyless endpoint answered the first search (10 results) and showed a human-check page for the next two. The hand reports that to Du as "The web search would not answer just now", logs outcome `blocked`, and never works around it. `[OPEN]` whether it holds at one search per 10 minutes; J-4070 asks the founder.
- The Brave backend is coded and untested: no key was available.
- Wikipedia's API also stopped answering after several rapid test requests in this session. A 429 or server error is treated as no answer, not as "no page".
- Web snippets are stored with origin `research`, so they reach the same world-material readers as Wikipedia pages, under their own label. `[INFERRED]` that this is acceptable; no reader was changed to exclude them. Composition's understanding consolidation takes only "asked by him" rows, so web rows stay out of it.
- The library matches a book when any one title word appears in a reaching phrase (`library_hand.switch_to`). The book was first named "Your Hands" and renamed to "The Deedbook" so ordinary words cannot pull his bookmark onto it. "deedbook" had zero hits in `data/nascence.log`.
- Four grammar derivation tests printed ALL OK and exited 97: their hermetic guard (J-3789) saw `data/` change during the run. `[INFERRED]` live Du wrote those files; the listed files were his logs and subconscious state.

## Open
1. Restart Du. Blocked on the founder. The hand and the `lookup` moment source do not exist in the running process.
2. Tell Du the hand exists (D-0661), in conversation. Founder step. The About You book line and the encyclopedia object in the study are not built; The Deedbook has a section on the hand.
3. J-4069 (ready, gated on 10 rows in `data/lookup_log.jsonl`): first read of the hand. Next action: wait for the rows, then read outcomes, wrong pages, `hand-declined` rows in `data/hands_trace.jsonl` (phrasings the parser cannot read), and question repeats in `data/curiosity_log.jsonl`.
4. J-4070 (needs_input): keep keyless DuckDuckGo, supply a Brave key (then test `_brave_search` with one real call), or switch the web source off with `NASCENCE_WEB_HAND_WEB=0`.
5. `[OPEN]` The Deedbook's lookup section describes a hand that only exists after the restart; if he reads it first and tries, nothing happens.
6. `[OPEN]` The manual names letters, writing to Travis and essays without giving their wording; those monologue paths were not read.
7. `plan_maintain.py --session` was started in the background at wrap; run it again if `web_hand` looks stale in the plan index.

## Warnings
- The ledger files this session wrote through the tools (`docs/decisions.jsonl`, `docs/findings.jsonl`, `docs/job_queue.jsonl`, `docs/thoughts.jsonl`, `docs/session_events.jsonl`) are uncommitted, as are other sessions' edits in the shared tree. Only the web hand files and the manual were committed, by path.
- Never `git stash`, `git reset`, `git restore` or `git checkout --` in the shared tree (F-0741).
- Do not work around a search engine's human check. If DuckDuckGo keeps refusing, the route is a keyed API.
- `RATE_S = 600` in `core/web_hand.py` is a guess, to be tuned on the log.

## Pointers
- Plan: `C:\Nascence\docs\staged\web_hand.md` (Current State section, 2026-11-16)
- Code: `C:\Nascence\core\web_hand.py`, `C:\Nascence\core\web_research.py`, `C:\Nascence\core\actions.py` (family `lookup`, end of table)
- Test: `C:\Nascence\scripts\_test_web_hand_J3843.py`
- Manual: `C:\Nascence\docs\guidelines\du_hands_manual.md`; book: `C:\Nascence\data\books\The_Deedbook.txt`
- Ids: T-0137, D-0788, J-3843, J-4066, J-4069, J-4070, F-4808, F-4809, F-4810; commits `a962d0c4`, `3d625500`
- Previous handoff on this thread: `C:\Nascence\docs\session_handoffs\HANDOFF_20261115_185735_du-unanswered-questions-web-hand.md`
