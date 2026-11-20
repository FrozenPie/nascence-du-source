---
name: feedback-decide-batch-id-mixup
description: "Never batch-open multiple /decide entries then batch-rule them by assumed sequential ID — verify each ID with `show` before ruling it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4595f5ad-65f2-480a-8d83-32786682d18c
  modified: 2026-08-28T21:25:32.170Z
---

When opening several new `/decide` entries in one shell block and then ruling them in a second block,
never assume the auto-assigned IDs land in the order/count you expect. Verify each ID's `plan` field
(via `decide.py show <id>`) immediately before writing its ruling — or better, open-then-rule ONE
decision at a time end-to-end, confirming plan-name match, before moving to the next.

**Why:** 2026-08-29, during the stalled-plans review pass (see [[project-plan-portfolio-audit]]): 5
decisions were opened in one batch (D-0075 through D-0079), but only 4 `rule` commands were written —
because one question in the preceding `AskUserQuestion` batch had covered two plans' worth of ground
in a single answer, I mentally collapsed two decisions into one ruling and miscounted. Every ID from
D-0076 onward silently received the ruling text meant for the NEXT id in sequence, and D-0079 (the
actual last one) was left completely unruled. This was caught only because a habit of running a
verification `show` loop after batch-ruling was already in place from the prior success in this same
session — without that check it would have logged founder rulings under the wrong plan slugs, which
is exactly the kind of provenance error this toolchain's `--by travis` requirement exists to prevent
(see [[feedback-decide-review-scope]] for the broader pattern this session validated).

**How to apply:** Any time `/decide open` is called more than once before the matching `/decide rule`
calls are written, treat the ID list as unverified until each one is confirmed against its `plan`
field. For a small batch (≤3), open-and-rule one at a time is cheap enough to just do. For a larger
batch, open all first, then immediately print a `show`-derived table of id→plan before writing a
single `rule` command, and write each `rule` by reading that table — never by counting AskUserQuestion
answers against a remembered open-order.
