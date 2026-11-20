# T5 procedural skills — the look (2026-08-22)

Founder: "have a look at `12:50:30 [subconscious] T5 PROCEDURAL SKILL compiled (3 sources): Impressing with insights into
Daoist philosophy | When I encounter such moments, my aim is to engage in thoughtful refle…`"

## What that line actually was
`recent_lived_inputs()` returned the day's conversation turns (origin `lived`, each a Q/A). The largest cluster at
cosine ≥ 0.70 was **your three consecutive Wu Wei messages** (12:27 "tell me what you know about Wu Wei", 12:32 "your
answer is very enlightened… I am impressed", 12:34 "your articulation of Wu Wei was enlightened"). Three turns of one
conversation = "a recurring kind of situation" → one LLM call distilled "the consistent way you handle it" → a skill
named from **your praise** ("Impressing with insights…") whose approach is "engage in thoughtful reflection before
responding". It is now in `procedural_skills` at proficiency 0.40 and will be recognised (sim ≥ 0.80) the next time a
Wu Wei-shaped input arrives, injected into the Reflection and Executive prompts as "A LEARNED WAY YOU HANDLE THIS".

## Findings
1. ❌ **"Recurrence" is one conversation.** The material window is everything since the last compile (≥1 h); a topic
   discussed for three turns recurs trivially. All 19 live skills are **topic labels**, not situation kinds: "Adapting
   Technical Drawings to Colonial Constraints", "Chivalric Disillusionment in Medieval Narratives", "Observing Gradual
   Light Change", "Discussing traditional warfare tactics". They are compiled from peer letters, reading talk, and
   your sessions alike — whatever three similar inputs arrived in the same hour.
2. ❌ **Self-reinforcing within the same thread → "automatic" bypasses memory.** A recognised skill is reinforced
   +0.05 on *every* turn it matches. The 0.85 skill ("inherent potential vs achievement") was recognised 8× across
   08-13/14 — one extended conversation — and crossed `PROC_AUTOMATIC_PROFICIENCY=0.80`, at which point
   `_procedure_automatic()` **skips Recall + Episodic Buffer** for matching inputs (7 AUTOMATIC cycles in the log;
   one skill hit 1.00 on 07-05). A long chat on one topic makes him answer that topic from a one-line procedure
   with no memory reconstruction. That is the opposite of what a mastered skill should buy.
3. ⚠️ **No success criterion.** "Successfully-handled cycles" = every lived fragment. Nothing checks the answer
   landed (no satisfaction/critic/human signal). The label even takes the *evaluator's* frame ("Impressing") —
   the performance-for-approval pattern the voice contract forbids, now baked in as a procedure.
4. ⚠️ **Skills are style notes, not procedures.** Every approach reads "I reflect deeply / delve into underlying
   currents / acknowledge both perspectives" — generic reflective posture, no world-hand, no step he could actually
   perform. Compare the hands ledger (`core/hands.py`) and fieldcraft skills (knots, fire, shadow-stick): those are
   procedural memory in the real sense, and they are not in this table.
5. ⚪ Health: 55 compiles since June, 19 alive (14-day rust ×0.9, pruned < 0.15), 93 recognitions total — so the
   loop runs and mostly forgets itself. Cheap to leave; cheap to fix.

## What would make T5 true (proposed, not built — your call)
- **Recurrence across days and sources**: a cluster compiles only when its members span ≥ 2 distinct days (or
  2 distinct conversations/peers), not 3 turns of one thread. `recent_lived_inputs` window = 7 days, not "since
  last compile".
- **Reinforce once per conversation** (per `cycle` thread / per hour), not per turn — and never above 0.79 from
  conversation alone; AUTOMATIC requires a *second* signal (e.g. the epistemic/satisfaction ledger says the answer
  landed, or a human correction did *not* follow).
- **Retire the automatic bypass** until that signal exists (`PROC_AUTOMATIC_PROFICIENCY = 1.01`): a skill may shape
  HOW he answers, never remove memory from the loop. (Finding 2 is the one thing here worth changing now.)
- **Label from the situation, never the evaluation**: strip praise/affect framing from the trigger summary prompt
  ("name the KIND of moment, not how it was received"); a source set dominated by the human's evaluative turns
  ("impressed", "enlightened", "good answer") is not a situation and should not compile.
- **Procedural = doable**: fold the real procedures (hands families, fieldcraft skills, study routines) into the
  same table as first-class skills with use counts from `hands.fired`, so "procedural memory" means what he can do.

## Verdict
The line is not a bug in the code — it did exactly what T5 does — it is a design that mistakes a topic for a
situation and a conversation for recurrence, and it has one genuinely harmful edge (the automatic memory bypass).
Recommend: flip the bypass off today (one constant), and rebuild T5's recurrence/success gates when convenient.
