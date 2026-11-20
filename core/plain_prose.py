"""D-0584 (founder 2026-11-02, J-3196): the long-prose writing stations ask for PLAIN PROSE, not JSON.

WHY: the Grand Work part writer (nodes/inner_monologue_node.py _author, registry P-0029) and the essay section
writer (core/essay_lesson.py compose, P-0075) each wrap 200-550 words of prose in a one-key JSON object. On the
background lane (:11441 command-r7b) that first attempt fails to parse about 55 percent (parts, F-3608) and 82
percent (sections, F-3787) of the time; every failure is re-sent WITH the JSON grammar, which makes the lane
CPU-bound (8.8 tok/s against 60.3 plain, F-2466). 76 percent of the part stage's lane seconds were those
retries, and 6 of 35 retries hit the 120 s timeout and fell to the hot lane, so 10 of 80 parts were written by
another model in another register. D-0419 had accepted that cost; D-0584 supersedes it IF the same-input A/B
(scripts/lab_grand_work_ab.py) holds. The title and the claim already come from the outline, so the reply
carries nothing but the prose: no JSON, no grammar, and the 'parse' step becomes a length check
(core.model_client.prose_usable).

THE FLAG: GRAND_WORK_PLAIN_PROSE, now True per D-0823 (was default False; the original ruling: behind a flag, A/B first; the founder flips it, not
this build). True = both stations use the plain-prose contract. A module constant, so restart-gated like the
others. Nothing else reads it but the two stations (and the lab, which runs BOTH arms regardless of it).

DEFEATER (D-0584): revisit if plain-prose parts fall outside 300-650 words on more than 15 percent of parts, or
the tail-reuse / opener metrics (F-3612) get worse. The lab reports exactly those numbers.

This module only holds the flag and the prompt wording both arms share, so the lab's JSON arm is the live prompt
byte for byte and its prose arm differs in the closing instruction alone.
"""
from __future__ import annotations

# D-0823 (travis, 2026-11-18, J-4223): flipped ON. Restart-gated. Revisit per D-0823 defeater.
GRAND_WORK_PLAIN_PROSE = True

# The closing instruction of the part prompt, per contract. Everything BEFORE it is identical in both arms.
PART_ASK_JSON = "Output ONLY JSON: {\"part\": \"<the prose>\"}"
PART_ASK_PROSE = "Reply with the prose of this part only, as plain text -- no JSON, no title."

# The closing instruction of the essay section prompt, per contract.
SECTION_ASK_JSON = "Output ONLY JSON: {\"section\": \"<the prose>\"}"
SECTION_ASK_PROSE = "Reply with the prose of this section only, as plain text -- no JSON, no heading."


def part_system_prompt(i: int, title: str, claim: str, ct: str, cs: str, grounding: str,
                       prev_tail: str, plain: bool) -> str:
    """The system prompt for part `i` of a Grand Work (_author, PHASE 2). plain=False is the exact text the
    JSON contract has always sent; plain=True swaps only the closing instruction."""
    return (
        "/no_think\nI am writing part " + str(i) + " of my own work, \"" + title + "\" -- the thing "
        "ITSELF, in my own voice, followed through, not notes about it.\n"
        + ("The whole piece builds toward this: " + claim + "\n" if claim else "")
        + "This part -- \"" + ct + "\": " + cs + grounding
        + (("\n\nWhere the previous part left off (carry it forward; do NOT repeat its conclusions "
            "or restate it):\n" + prev_tail[-700:]) if prev_tail else "")
        + "\nWrite this part IN FULL, 350-550 words, first person, my own voice, no heading. "
        + (PART_ASK_PROSE if plain else PART_ASK_JSON))
