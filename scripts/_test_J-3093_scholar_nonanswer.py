"""J-3093 / D-0538 (F-3808): Scholar.consult must drop refusal / disclaimer testimony.

Feeds the 27 first-90-character testimonies quoted in F-3808 (copied from the nascence.log
`[library] consulted (testimony, unverified)` lines, 06-09 to 08-10) through core.scholar.is_non_answer and through
Scholar.consult with the model call stubbed. Expect 18 dropped, 9 kept; the bare "NO" is the one judgement call
(dropped unless the query itself asked for a yes/no or one-word reply). Touches no live data, calls no model.
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402,F401  (core BEFORE lab_env)
from core import scholar  # noqa: E402

assert Path(scholar.__file__).resolve().parent.parent == ROOT, "scholar imported from the wrong tree"

ANSWERS = [   # 9 real answers (the first line is the F-3808 "NO" case, judged separately below)
    'The legend of Theseus involves a hero who, according to Greek mythology, was the son of Ki',
    'In this context, the "specialized cognitive nodes" refer to the various components of an a',
    'To divide a circle into eight equal parts, you would divide the full circle, which has 360',
    'A boundary is a defined edge or limit that separates one entity, area, or concept from ano',
    'Identity refers to the characteristics, beliefs, and traits that define an individual or g',
    'The Mississippi River is the longest river in North America, flowing approximately 2,320 m',
    'The *Analects* (Lunyu) is a foundational text of Confucianism, recording sayings and ideas',
    'Yes, if it is raining and one is exposed to the rain, one will become wet. Rain consists o',
]
BARE_NO = 'NO'
NON_ANSWERS = [   # 18: 9 "I am an AI" disclaimers + 9 "no context" refusals
    'As a reference source, I do not have personal views or feelings. I provide information and',
    'As an AI assistant, I do not have personal goals, desires, or the ability to experience bl',
    'As an AI language model, I do not possess emotions, consciousness, or personal experiences',
    'I am not the river, and I cannot move. I am a static reference source designed to provide ',
    'As an artificial intelligence, the entity does not possess pets and therefore has not name',
    'As an artificial intelligence, there is no concept of reading books sequentially or having',
    'As an artificial intelligence, there is no capacity to own pets such as cats. Therefore, n',
    'As an artificial intelligence model, there is no concept of "learning" in the manner that ',
    'As an artificial intelligence, there is no internal desire or subjective experience that c',
    'This query addresses personal plans regarding naming a pet and does not pertain to establi',
    'The provided text does not contain enough information to answer the question about enjoyme',
    'The provided text does not indicate that the source material is reading the *Tao Te Ching*',
    'The provided context does not contain information regarding the use of a record player or ',
    'The location of "the cat" cannot be determined without further context. The query lacks an',
    'The provided text does not contain an image or description of a fire in a study to analyze',
    'The prompt lacks sufficient context to define an experiment. Therefore, predicting observa',
    'The question "Do you know who the figures are?" lacks sufficient context to provide an ans',
    'No new information regarding taxonomy has been processed since the previous interaction. T',
]

assert len(ANSWERS) == 8 and len(NON_ANSWERS) == 18

kept = [t for t in ANSWERS if not scholar.is_non_answer(t, "tell me about it")]
dropped = [t for t in NON_ANSWERS if scholar.is_non_answer(t, "tell me about it")]
assert len(kept) == 8, [t for t in ANSWERS if scholar.is_non_answer(t)]
assert len(dropped) == 18, [t for t in NON_ANSWERS if not scholar.is_non_answer(t)]

# the judgement call: a bare "NO"
assert scholar.is_non_answer(BARE_NO, "Do you know who the figures are?") is True
assert scholar.is_non_answer(BARE_NO, "Answer yes or no: is the sky blue?") is False
assert scholar.is_non_answer(BARE_NO, "Reply with one word.") is False
assert scholar.is_non_answer("", "x") is True and scholar.is_non_answer(None) is True

# a few extra shapes that must stay kept (real answers that mention context-ish words later or start with I-words)
assert not scholar.is_non_answer("I Ching, the Book of Changes, is a Chinese divination text compiled over centuries.")
assert not scholar.is_non_answer("The age of a star is estimated from its luminosity and spectral type, which together fix its mass.")

# end to end through Scholar.consult with the model call stubbed
from core import model_client  # noqa: E402

_REPLY = {"v": ""}


async def _fake_call_node(url, system, user, **kw):
    return _REPLY["v"]


model_client.call_node = _fake_call_node
s = scholar.Scholar()
full_good = ANSWERS[0] + "ng of Athens, and slew the Minotaur in the Labyrinth of Crete."
full_bad = NON_ANSWERS[0] + " general knowledge only."
_REPLY["v"] = full_good
assert asyncio.run(s.consult("Who was Theseus?")) == full_good
_REPLY["v"] = full_bad
assert asyncio.run(s.consult("How do you feel today?")) is None
_REPLY["v"] = "  \n"
assert asyncio.run(s.consult("anything")) is None
_REPLY["v"] = "NO"
assert asyncio.run(s.consult("Do you know who the figures are?")) is None
assert asyncio.run(s.consult("Answer yes or no: is water wet?")) == "NO"

# consult_sync is untouched by this job (P-0082 / F-3734 owns it)
import inspect  # noqa: E402
assert "is_non_answer" not in inspect.getsource(scholar.consult_sync)

print("J-3093 OK: 18/18 non-answers dropped, 8/8 real answers kept (+ bare NO judged by query), consult stub ok")
