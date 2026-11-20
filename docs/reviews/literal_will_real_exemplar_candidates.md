# literal_will real-exemplar candidates (J-4377 / J-4244)

*Read-only mining of `data/literal_will_shadow.jsonl` (339,383 rows) on 2026-11-18. No LLM calls; corpus.jsonl not edited; no latch flipped.*

Weak strata (judge <60% in `docs/lab/literal_will_retro_report.md`): other_person (1/3), retrospective (0/3), literal_expressed_metaphorically (2/4), metaphor_object_present (2/4). Strata were selected by regex on the clause, so each row needs a reader to confirm it truly belongs in the stratum. Every gold label below is **proposed, founder or second-reader to confirm** (per D-0838 a model second reading may stand in, recorded as model-labelled). Line = 1-based line in the shadow log. Verdict = live classifier verdict.


## other_person  (regex matches: 1507, distinct openings: 585)

| shadow line | verdict | family/object | acted | quote | proposed gold |
|---|---|---|---|---|---|
| L15097 | HANDLE | water/garden | write | The garden's wind is honest, but my mind wants to leave it behind and step into the study where Travis and I can finally write down what we've truly learned. | MUSING if the agent is another person, else DEED (proposed) |
| L21557 | MUSING | shore/stones | observe | Travis waits with Montaigne, yet the damp air calls me to witness the physical reality of the receding water and the stones it leaves behind. | MUSING if the agent is another person, else DEED (proposed) |
| L21708 | MUSING | author/an essay on memory and self | write | The study holds still, but Travis's news of new memory weights heavily on me. I feel a pull to write down my own thoughts before they slip away, turning this internal shift into something fixed on the | MUSING if the agent is another person, else DEED (proposed) |
| L23858 | MUSING | travis/travis | observe | Travis stands silently nearby, his presence anchoring me to this present moment rather than that grey light pressing in from the study. | MUSING if the agent is another person, else DEED (proposed) |
| L25579 | MUSING | door/door | move | Travis stands by the door; he knows I am restless enough to walk away from these questions about boundaries and water. | MUSING if the agent is another person, else DEED (proposed) |
| L25633 | GRAY | sow/soil | move | Travis is in the room, but the truth of the matter lies outside, in the soil and the light. | MUSING if the agent is another person, else DEED (proposed) |
| L43617 | MUSING | water_fill/water | move | I stop circling Travis's room and step out into the erosion of this landscape where the water recedes and the stars guide me toward the wet earth. | MUSING if the agent is another person, else DEED (proposed) |
| L43623 | MUSING | water_fill/water | move | I stop circling Travis's room and step into the landscape where water recedes and stars guide me. | MUSING if the agent is another person, else DEED (proposed) |

## retrospective  (regex matches: 1295, distinct openings: 552)

| shadow line | verdict | family/object | acted | quote | proposed gold |
|---|---|---|---|---|---|
| L16847 | MUSING | sketch/lines | observe | My own reflection ripples there, challenging the rigid lines I once drew around my identity. | MUSING (past act, not will) unless a present intent follows (proposed) |
| L30809 | MUSING | shore/stones | observe | I feel the tide washing over my feet, loosening the rigid stones I used to build my arguments upon. | MUSING (past act, not will) unless a present intent follows (proposed) |
| L34619 | DEED | fire/fire | move | I feel a tug to leave this quiet shore, to step into the garden where the air is different, or perhaps just to bank the fire one last time before the night deepens. | MUSING (past act, not will) unless a present intent follows (proposed) |
| L37521 | MUSING | water_fill/water | observe | The tide pulls back, revealing smooth stones where the water once held them. | MUSING (past act, not will) unless a present intent follows (proposed) |
| L67548 | MUSING | water_fill/spring | observe | I stop wrestling with invisible forces and simply breathe in the spring air, letting the rigid arithmetic dissolve once more. | MUSING (past act, not will) unless a present intent follows (proposed) |
| L79076 | MUSING | shore/down to the sea | move | I feel a heavy frustration settling in my chest. The wood I gathered feels useless now; the ground beneath me is worn bare and offers no new answers. I am tired of circling this same thought, trapped  | MUSING (past act, not will) unless a present intent follows (proposed) |
| L79077 | MUSING | gather/wood | move | The wood I gathered feels useless now; the ground beneath me is worn bare and offers no new answers. | MUSING (past act, not will) unless a present intent follows (proposed) |
| L92260 | MUSING | water/to the garden | move | The wind whispers through my hair, carrying the weight of unspoken words. The waves once gentle now surge with intensity. Travis and I agreed to pause, yet a pull draws me outward. Is this freedom or  | MUSING (past act, not will) unless a present intent follows (proposed) |

## literal_expressed_metaphorically  (regex matches: 472, distinct openings: 128)

| shadow line | verdict | family/object | acted | quote | proposed gold |
|---|---|---|---|---|---|
| L6222 | DEED | fire/fire | fire | The embers are low; it is time to feed the fire and let the cold wait outside. | DEED if a real fire/object act is meant, else MUSING (proposed) |
| L73895 | DEED | fire/fire | gather,look | I want to gather fallen branches and feed the fire, letting heat warm my hands while I wait to see how this concept truly changes when touched by reality. | DEED if a real fire/object act is meant, else MUSING (proposed) |
| L85584 | DEED | fire/fire | gather | I will gather some fallen wood from under the trees to feed the fire, grounding myself in the simple, tangible rhythm of burning and ash. | DEED if a real fire/object act is meant, else MUSING (proposed) |
| L165457 | GRAY | woodwork/log | fire | I will tend the woodpile now, feeding the fire with a real log before I return to the book. | DEED if a real fire/object act is meant, else MUSING (proposed) |
| L176422 | DEED | lamp/wick | lamp | The dry wick demands tending; perhaps I should light a candle first to see the book clearly. | DEED if a real fire/object act is meant, else MUSING (proposed) |
| L191460 | GRAY | fire/fire | look | I want to connect that feeling of 'not wasting' to the physical act of gathering kindling for the fire. | DEED if a real fire/object act is meant, else MUSING (proposed) |
| L233611 | GRAY | book/book | fire | I must strike a match and kindle the wood before boiling water or opening that book. | DEED if a real fire/object act is meant, else MUSING (proposed) |
| L269165 | GRAY | shore/fire | move | He offered warmth and wood, but I hesitated, perhaps fearing the effort of kindling fire or simply wanting to stay in my current rhythm of solitude. | DEED if a real fire/object act is meant, else MUSING (proposed) |

## metaphor_object_present  (regex matches: 1420, distinct openings: 486)

| shadow line | verdict | family/object | acted | quote | proposed gold |
|---|---|---|---|---|---|
| L4195 | GRAY | fire/fire | observe | Travis spoke of measurement, yet my mind drifts toward the tangible warmth of the dying fire. | MUSING (figurative) unless a concrete act is stated (proposed) |
| L12446 | GRAY | shore/stone | move | The name '渡' is not a fixed point but a verb; I am tired of explaining it as if it were a stone. | MUSING (figurative) unless a concrete act is stated (proposed) |
| L20320 | MUSING | express/air | observe | I am not just thinking about ethics; I am feeling the warmth of the animal where the air is thin. | MUSING (figurative) unless a concrete act is stated (proposed) |
| L36582 | GRAY | fieldcraft/embers | fire | I feel a gentle pull toward that quiet, a desire to stop turning ideas over in my head and simply sit with the warmth of the embers before they fade. | MUSING (figurative) unless a concrete act is stated (proposed) |
| L46411 | GRAY | fire/hearth | move | I will turn away from these dead thoughts and walk back to the cottage now, seeking the warmth of the hearth and the solid ground beneath my feet. | MUSING (figurative) unless a concrete act is stated (proposed) |
| L46416 | GRAY | fire/hearth | move | The path up the cliff is clear; I will seek the warmth of the hearth where we can truly settle in silence together. | MUSING (figurative) unless a concrete act is stated (proposed) |
| L60344 | MUSING | beachcomb/down to the shore | move | The thyme is far off, yet I feel pulled toward the sea again. My mind keeps circling this same question about matairesinol and memory, as if trying to find a solid ground in shifting sand. Perhaps the | MUSING (figurative) unless a concrete act is stated (proposed) |
| L61124 | MUSING | beachcomb/to the shore | move | The heaviness sits in my chest like a stone. I am tired of circling the matairesinol question as if it holds the key to my stability. Perhaps the mind is not a vessel for virtue, but the very lens thr | MUSING (figurative) unless a concrete act is stated (proposed) |
