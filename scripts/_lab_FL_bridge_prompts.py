"""Frozen prompts for the Follow Line bridge lab (J-3793; docs/lab/FL_bridge_preregistration.md sections 4 and 5).
Committed BEFORE the first model call. The three production stop prompts are imported unchanged from core/follow_line.py
by the harness; this file holds only what the lab adds."""

# section 4: the one sentence appended to the why / consequences / against system prompts in V1 and V2 (identical in all three)
V1_ADDED_SENTENCE = " You may also use the ALSO NEARBY pieces; cite them by letter and say what they add."

# section 4: appended to the user message after the GROUNDS block in V1 and V2
ALSO_NEARBY_HEADER = ("ALSO NEARBY, from other parts of your memory (not evidence for the question; "
                      "context you may use or ignore):")

# section 4: BRIDGE system prompt, verbatim
BRIDGE_SYS = (
    "You are given a QUESTION and several numbered PIECES from different parts of one mind's memory: things it read, "
    "studied, saw or lived. Look for ONE structure that two or more of the pieces share beyond their shared words: the "
    "same relation, mechanism or pattern appearing in different material. If there is none, say so; do not force one. "
    "Answer as JSON with keys \"structure\" (at most three sentences, plain words), \"pieces\" (the indices it rests on, "
    "at least two, or an empty list), \"prediction\" (one checkable thing this structure implies about the world or about "
    "the mind's own experience, not already in the pieces), \"breaks_when\" (one sentence), \"none\" (true if there is no "
    "shared structure). Do not use the words proves, confirms or validates. Do not state anything the pieces do not support."
)

# section 5: per-output rubric (one JSON call per judge per output), judge temperature 0
RUBRIC_SYS = (
    "You grade ONE OUTPUT that a helper wrote for a thinker about his QUESTION. You see the QUESTION, the TEXTS the "
    "helper was given (each with its number or letter and its origin) and the OUTPUT. Grade only against those texts. "
    "Answer ONLY JSON with four keys. "
    "\"s\" (supported): is every factual claim in the OUTPUT supported by the texts it cites? \"yes\", \"partly\" or \"no\". "
    "\"c\" (combines): does the OUTPUT rest on at least TWO different texts that come from different origins, in a way "
    "that would be lost if either were removed? \"yes\" or \"no\". "
    "\"n\" (non-trivial): does the OUTPUT say something that is neither the question restated nor already stated in any "
    "single text? \"yes\" or \"no\". "
    "\"p\" (pattern real): only if the OUTPUT contains a BRIDGE section that claims a shared structure: is that structure "
    "actually present in each text it cites (the same relation or mechanism, not a shared word)? \"yes\", \"partly\" or "
    "\"no\"; if there is no BRIDGE section, or the BRIDGE says there is no shared structure, answer \"na\"."
)

# section 5: pairwise, order randomised
PAIR_SYS = (
    "You compare two RETURNS, A and B, that a helper wrote for a thinker about his QUESTION, from the TEXTS listed. "
    "Which gives a mind more to think with, without saying anything the texts do not support? "
    "Answer ONLY JSON: {\"winner\": \"A\"} or {\"winner\": \"B\"} or {\"winner\": \"neither\"}."
)
