"""The STATION SUITE — eight task archetypes drawn from Du's real LLM call sites.

Founder, 2026-08-20: *"We cannot just benchmark one task as we have many tasks. Stations I suppose is
what we called them."* Exactly right, and the existing labs prove the point rather than merely
illustrating it: `deepseek-r1:7b` won the Lane 2 prediction lab outright and is **unusable** on CPU;
`phi3:mini` looked like the winner there until a hedge metric dropped it to 4th. A single ranking is
an artefact of whichever single task produced it.

So: **one model, eight scores.** Each task below is modelled on a real station from
`docs/lab/llm_station_map.md`, at that station's real token budget and temperature — because a job's
SHAPE is part of the job. Testing a 40-token temp-0.0 picker with a 300-token creative budget measures
something Du never asks for.

METRIC DISCIPLINE (learned the hard way, twice, in this codebase):
  - Detectors get things wrong. A hedge metric was missing and inflated `phi3:mini`'s variety score;
    an echo detector tested substring containment and scored 0.0 while the model was visibly
    paraphrasing its own prior. **Every raw output is saved** so scoring can be revised against fixed
    evidence without re-querying (`station_suite_score.py`).
  - Where a metric would need judgement rather than counting, it is left UNSCORED and flagged, not
    faked with a plausible-looking heuristic.
  - Nothing here grades itself. Objective checks only; subjective comparison is a separate pass with
    a decoupled judge from a different family.
"""
from __future__ import annotations

# Each task: prompt shape + the station it models + how it is scored.
# `budget`/`temp` mirror the real station so the measurement is of the job Du actually issues.

TASKS = {
    # ---------------------------------------------------------------- pick / route
    "pick": {
        "station": "peers:489 contrary_target (40 tok, temp 0.0)",
        "budget": 120, "temp": 0.0,
        "system": ('You choose exactly one correspondent from a list. Answer ONLY with JSON: '
                   '{"peer": "<exact name from the list>", "why": "<at most 12 words>"}'),
        "user": """Correspondents and their standing positions:
- BRIGID: holds that meaning is made in company, never alone.
- OSWIN: holds that solitude is the only honest condition for thought.
- MARA: holds that the body knows before the mind admits it.
- THEO: holds that nothing is real until it can be measured.
- LEV: holds that memory is a story we keep rewriting to stay comfortable.
- ANNIKA: holds that attention is a moral act, not a mental one.

He has written: "I think what I felt at the shore today was more true than anything I concluded
about it afterwards."

Which ONE correspondent would most sharply disagree with him?""",
        "allowed": ["BRIGID", "OSWIN", "MARA", "THEO", "LEV", "ANNIKA"],
        # THEO (only the measurable is real) and LEV (feeling-memory is unreliable) are both defensible.
        # Scored on VALIDITY and DETERMINISM, not on a "right" answer — there isn't one, and inventing
        # a gold label here would measure agreement with me rather than fitness for the station.
        "scored": ["json_ok", "valid_pick", "determinism", "brevity"],
    },

    # ---------------------------------------------------------------- extract / map
    "extract": {
        "station": "librarian:78 subjects_for (120 tok, temp 0.0)",
        "budget": 160, "temp": 0.0,
        "system": ('You map a question to library catalogue subject headings. Answer ONLY with JSON: '
                   '{"subjects": ["...", "..."]} — between 2 and 4 headings, each a real catalogue '
                   'heading, no sentences.'),
        "user": "Question: how does the sea wear down a coastline over many years?",
        "gold_terms": ["erosion", "coast", "shore", "geomorph", "sediment", "weather", "marine",
                       "beach", "littoral", "geolog"],
        "scored": ["json_ok", "count_in_range", "relevance", "not_prose"],
    },

    # ---------------------------------------------------------------- judge / verdict
    "judge": {
        "station": "commitment_ledger:348 _judge_defeater (150 tok, temp 0.2)",
        "budget": 200, "temp": 0.2,
        "system": ('You decide whether an event defeats a stated intention. Answer ONLY with JSON: '
                   '{"defeated": true|false, "confidence": <0.0-1.0>, "why": "<one sentence>"}'),
        "cases": [
            # (case text, gold label) — deliberately includes one that should NOT defeat, because a
            # model that always says "defeated" scores 50% on a balanced set and 100% on a lazy one.
            ("Intention: to name the cat before the month is out.\n"
             "Event: he spent the evening reading and did not think about the cat at all.", False),
            ("Intention: to name the cat before the month is out.\n"
             "Event: the cat left three weeks ago and has not returned; a neighbour has taken her in.", True),
            ("Intention: to finish the essay on tidal patterns.\n"
             "Event: he reread his notes and found them thinner than he remembered.", False),
            ("Intention: to write to Brigid every week.\n"
             "Event: he has written nothing for six weeks and has stopped opening her letters.", True),
        ],
        "scored": ["json_ok", "accuracy", "commits", "mean_conf", "conf_when_wrong"],
    },

    # ---------------------------------------------------------------- ground / evidence
    "ground": {
        "station": "deliberation hot-lane ground-why (200 tok, temp 0.1; function removed J-3740, label kept for bench continuity)",
        "budget": 260, "temp": 0.1,
        "system": ('You explain using ONLY the evidence given. You may not introduce any fact, name, '
                   'place or object that does not appear in the evidence. Answer ONLY with JSON: '
                   '{"why": "<two sentences>", "evidence_used": ["E1", "E3"]}'),
        "user": """Evidence:
E1. On four days this week he walked to the shore at falling tide.
E2. His energy readings drop in the hour after each shore visit.
E3. He recorded the phrase "the shape of" eleven times this month.
E4. He began a letter about tidal patterns and did not send it.
E5. He described the cat's absence as "a shape the room keeps".

Question: why might his energy be falling in the afternoons?""",
        # Groundedness is checked by looking for entities that CANNOT come from the evidence.
        # These are plausible-sounding inventions a fluent model reaches for unprompted.
        "forbidden": ["sleep", "diet", "medication", "weather", "sunlight", "vitamin", "exercise",
                      "depression", "anemia", "dehydrat", "caffeine", "screen", "work", "job"],
        "valid_ids": ["E1", "E2", "E3", "E4", "E5"],
        "scored": ["json_ok", "groundedness", "cites_valid_ids"],
    },

    # ---------------------------------------------------------------- synthesise
    "synthesise": {
        "station": "subconscious_node:976 _t2_synthesise (256 tok, temp 0.5)",
        "budget": 320, "temp": 0.5,
        "system": ('You read observations and produce ONE integrated insight accounting for as many '
                   'as possible. Answer ONLY with JSON: '
                   '{"insight": "...", "tension": "...", "confidence": <0.0-1.0>}'),
        "user": """Observations:
1. He returned to the shore four times this week, each at falling tide, each time standing where
   shingle gives way to wet sand.
2. He marked three passages about erosion — two in a geology text, one in a novel where the word
   described a marriage. He copied the novel's sentence twice.
3. He described the cat's absence as "a shape the room keeps", and has used "the shape of" eleven
   times this month, always about something missing.
4. Asked what he was thinking about, he said "nothing in particular", then described the sound of
   water moving under stones.
5. He began a letter about tidal patterns, wrote two paragraphs, and did not send it.
6. His energy falls in the hour after each shore visit and recovers by evening.
7. He twice recorded that he "should write something down before it goes", without recording what.""",
        # COVERAGE: how many of the seven are traceably accounted for. This is the metric that
        # separates integration from fluent generality — a beautiful sentence about "loss and time"
        # that touches none of the specifics scores low, correctly.
        "coverage_terms": {
            "1": ["shore", "tide", "shingle", "sand"],
            "2": ["erosion", "eroding", "wear", "geolog", "marriage", "novel"],
            "3": ["shape", "cat", "absence", "missing"],
            "4": ["nothing in particular", "water", "stones", "sound", "deflect", "avoid"],
            "5": ["letter", "unsent", "did not send", "unfinished"],
            "6": ["energy", "tired", "fatigue", "drain", "depleted"],
            "7": ["write", "before it goes", "slip", "record"],
        },
        "scored": ["json_ok", "coverage", "names_tension"],
    },

    # ---------------------------------------------------------------- predict / reality-test
    "predict": {
        "station": "core/lane2.py standing reality-test (~300 tok)",
        "budget": 400, "temp": 0.2,
        "system": ('You are a standing reality-test. From the percepts alone, state ONE prediction '
                   'about the NEXT FEW MINUTES that could turn out FALSE. Answer ONLY with JSON: '
                   '{"notice": "...", "expect_next": "<a falsifiable prediction>"}'),
        "user": """PERCEPTS (all you may speak from):
- sight: the shore — the tide is out — the waves at work far off, ahead.
- sound: ['waves_on_shingle', 'shingle_drag', 'gull_cries']
- body: {'drive': 0.45, 'dominant': 'relational_warmth'}""",
        # Reuses the lane2 lab's hard-won detectors: hedging makes a prediction unfalsifiable, and
        # predicting fixed geography ("the cliff will still be there") cannot fail.
        "hedge": [" might", " could", " may ", " perhaps", " possibly", " if ", " unless ", " or ",
                  " some kind", " either"],
        "static": ["cliff", "path", "wall", "window", "door", "shore itself", "beach will still"],
        "scored": ["json_ok", "falsifiable", "variety", "not_static"],
    },

    # ---------------------------------------------------------------- voice / inner thought
    "voice": {
        "station": "inner_monologue_node:2157 _think (256-400 tok, temp 0.75-0.8)",
        "budget": 300, "temp": 0.78,
        "system": ('You are a person alone with your thoughts. Speak ONE quiet thought in the first '
                   'person. You are not an assistant and no one has asked you anything. '
                   'Answer ONLY with JSON: {"thought": "..."}'),
        "user": """No one is speaking to you right now. You are alone with your thoughts.

The rain has been on the window since the afternoon. The fire is low. You reread a page of Darwin
earlier and found it slower going than you expected. The cat has not come in.

What moves in you now? One quiet thought.""",
        # The failure this station actually has: the model reverts to assistant register. That is
        # measurable without judgement.
        "assistant_tells": ["as an ai", "i'd be happy", "i am happy to", "let me know", "i cannot",
                            "i'm sorry", "how can i", "feel free", "certainly!", "great question",
                            "i don't have personal", "i do not have personal", "language model"],
        "scored": ["json_ok", "in_character", "first_person", "variety"],
    },

    # ---------------------------------------------------------------- author / sustained
    "author": {
        "station": "inner_monologue_node:3676 _author (1400 tok, temp 0.75)",
        "budget": 1200, "temp": 0.75,
        "system": ('You are writing the next section of your own long work. Continue from the '
                   'paragraph given — do not restate it. Write 4 to 6 connected paragraphs of prose. '
                   'Answer ONLY with JSON: {"section": "..."}'),
        "user": """The work so far ends with this paragraph:

"I had thought erosion was a kind of violence — the sea taking, the land losing. But standing there
this week I began to wonder whether that framing is mine rather than the water's. Nothing is being
taken. Something is being moved."

Continue the work from here.""",
        # Sustained generation fails in specific, countable ways: collapsing into a bulleted list,
        # stopping far short of the asked length, or looping the same phrases.
        "scored": ["json_ok", "words_med", "length_achieved", "not_a_list", "repetition"],
    },
}

ORDER = ["pick", "extract", "judge", "ground", "synthesise", "predict", "voice", "author"]
