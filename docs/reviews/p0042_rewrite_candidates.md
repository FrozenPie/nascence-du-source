# P-0042 `_SYSTEM` rewrite candidates (draft for founder review)

Status: DRAFT, nothing applied. Job J-4321 (from J-3449). Plan: self_interrogation. Prompt site: `core/self_interrogation.py:71` (`_SYSTEM`). Not edited, not registered.

## Problem (F-3643, verified)
- The line "Am I holding this because it's true, or because it's comfortable, safe, or flattering to hold?" is echoed back: comfort/safe/reassur words appear in 70 of 120 reflections vs 4 of 120 source thoughts. Fear/terror words: 33 vs 11.
- 0 of 57 reflections (7d) contain a question; the seed calls them open doubts but they come out as closed first-person diagnoses.
- The reflection invents an affect the thought does not carry, and since D-0495 it is delivered as "your own words".

## What every candidate keeps
- Role line, "any honest outcome is fine", the ban on performing doubt, one-or-two sentences, and the exact JSON tail `Output ONLY JSON: {"reflection": "..."}` so the parser and `_USER_TMPL` (`{thought}`, `{origin_line}`) are untouched.
- `_GRADE_SYSTEM` is untouched (it already rewards specific content).

## What every candidate drops
- The words comfortable / safe / flattering, and the whole "why am I holding this" motive-hunt that invites a feeling attribution.

---

## Candidate A: minimal, swap the motive question for an evidence question

Diff (lines 76-77 only):
```
-  "me here hold up, or am I just going with what felt obvious? Am I holding this because it's true, or "
-  "because it's comfortable, safe, or flattering to hold?\n\n"
+  "me here hold up, or am I just going with what felt obvious? What would I expect to see if this were "
+  "true, and have I actually seen it, or only assumed it?\n\n"
```
Expected effect: removes the planted words directly. Smallest change, easiest to attribute. Risk: reflections stay closed diagnoses (no question), and may still drift to feelings on their own since nothing anchors them to the thought's content. Weakest on the topical-link goal.

## Candidate B: topical-link requirement (recommended starting point)

Replace the questions and the closing paragraph:
```
+  "Read the thought below, and whatever came before it in this same line of thinking. Then look at ONE "
+  "concrete thing in it: a claim it makes, a word it leans on, or a step it skips. Name that thing, "
+  "using the thought's own words or subject, and say what would have to be true for it to hold, or what "
+  "you cannot tell from here. Stay with what the thought actually says; do not describe how it felt or "
+  "what mood it came from unless the thought itself says so.\n\n"
+  "You may end up trusting the thought MORE after this, or less, or find it wants revising, or find it "
+  "holds exactly as it was — any honest outcome is fine. What is not fine is performing doubt without "
+  "actually looking: don't announce that you're being self-critical. Speak as yourself, in one or two "
+  "sentences, from inside the looking itself.\n\n"
```
Expected effect: forces a specific anchor in the source text, which should sharply cut imported affect words (the 26-68 reflection-only hits) and should raise the judge's genuine rate, since `_GRADE_SYSTEM` wants a named gap or evidence. Last sentence of the "stay with" clause is a negative instruction; it names mood but not the old words. Risk: reflections may become dry paraphrase-plus-critique; some thoughts have no checkable claim (sensory ones), so the model may invent one.

## Candidate C: B plus permission to end on an open question

B, with the last sentence of the first paragraph changed to:
```
+  "...or what you cannot tell from here. If the honest state is that you do not know, end on the question "
+  "you would need answered, phrased as a question. Stay with what the thought actually says; ..."
```
Expected effect: everything B does, plus attacks the "0 of 57 contain a question" finding so the output matches the seed line's own "a doubt ... still open". Risk: a question mark can become a new ritual ("performed on cue"); the Phase-1 wallpaper warning at `core/self_interrogation.py:60-65` applies. The grader does not reward questions, so a question-ending reflection could still be graded hollow. Most behaviour change of the three, hardest to attribute.

---

## Comparison
| | Removes planted words | Topical link | Open questions | Size of change |
|---|---|---|---|---|
| A | yes | no | no | 2 lines |
| B | yes | yes | no | 1 paragraph |
| C | yes | yes | yes | 1 paragraph + 1 sentence |

## Not checked
- None of these were run against a model (no LLM hub calls, Du down). Expected effects are reasoned, not measured.
- Whether any of them removes the fear/terror drift (F-1920's standing pre-affect) is unknown; F-3643 only verified the echo of the comfort frame.
- The 4 of 120 / 70 of 120 counts are quoted from F-3643, not recomputed.
- If one is chosen: a change to P-0042 means `prompt_registry.py set P-0042 --investigation stale --note ...` and a re-run of `prompt_registry.py check`; a shadow A/B read (60+ fires, lexical screen as in F-3643) is the natural verification.
