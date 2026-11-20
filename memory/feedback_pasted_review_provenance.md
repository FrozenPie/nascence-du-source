---
name: feedback-pasted-review-provenance
description: "Travis pastes external auditor responses (GPT/Gemini/Perplexity) into chat, sometimes unlabelled and sometimes with his own ruling appended — check provenance before writing anything up as a founder decision."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 24362f92-5fed-41bf-ab7f-837372cb4473
  modified: 2026-08-22T10:53:15.890Z
---

On 2026-08-22 a long, polished design review of the train split/merge plan arrived as a user message.
I wrote it into the plan doc, the code docstring, and memory as "Founder's refinements" / "founder
decision". It was GPT's review, pasted in; only the last three lines ("Step 1 is 100% a go. Step 2 is
lab testable after that. Then we can decide on more.") were Travis. Had to re-attribute in three places.

**Why:** this project keeps auditor rounds (GPT, Gemini, "the LAST auditor") and founder rulings
separate on purpose — rulings are binding, auditor points are recommendations the founder may override.
Conflating them inflates a recommendation into law and hides which calls Travis has actually made.

**How to apply:** when a message reads like a structured external review (headings, "I would watch…",
"my overall reaction is…", bullet lists of questions, a tone shift from Travis's terse style), treat it as
a forwarded auditor response until confirmed. Tell-tales of Travis's own addendum: short lines at the
end, his typos ("Step to"), decisions rather than analysis. Label write-ups "auditor review (GPT),
forwarded by the founder" and list the founder's own rulings separately. If attribution is unclear and
it affects a ruling, ask — one line, not a quiz.

**Added 2026-10-30:** Perplexity is a third source (T-0105, F-3216, F-3217: a 12-subsystem psyche
spec, then a 10-addition SOTA list). Travis's framing that day: "no talk of consciousness allowed as
it is unmeasurable", and the outside reviewer only knows what we tell it — so its "gaps" must be
checked against the code before they count (F-3217: 7 of 10 already existed). Its reference links
cite papers dated 2026 with arxiv ids; treat them as unverified.
