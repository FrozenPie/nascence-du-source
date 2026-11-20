# train_courier_cargo_ids — folded history


---

# History folded on 2026-09-27 from `docs\plans\train_courier_cargo_ids.md` (plan-compact, 1 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py train_courier_cargo_ids`._

## Current State — verified 2026-08-29

Built exactly as scoped in "What a concrete build would look like" below:

- **`core/cargo_types.py`** (new) — the 19 station `product_type` constants from the table below,
  plus a separate 4-value `WORLD_CARGO_TYPES` vocabulary (`WORLD_FACT_WEATHER`,
  `WORLD_FACT_SOUND`, `OBSERVATION_LEDGER_FACT`, `CALIBRATION_PAIR`) for the existing
  couriers/buses that don't map onto any station product (see "Retrofitting" section below).
- **`core/trains.py`** — `open()` gained an additive, optional `product_type: str | None = None`
  kwarg, stamped into the record and the open-event log row; `update()` already accepted it for
  free (generic `k in rec` field mirroring). Does not touch the existing `cargo` field.
- **`core/couriers.py`** — both existing routes now tag their `_log_delivery` call:
  `context_echo` → `cargo_type=WORLD_FACT_WEATHER`, `sound_echo` → `cargo_type=WORLD_FACT_SOUND`.
- **`core/buses.py`** — both existing routes tagged: `object_ledger_line` →
  `cargo_type=OBSERVATION_LEDGER_FACT`, `sync_investigation_calibration` →
  `cargo_type=CALIBRATION_PAIR`.
- **`nodes/inner_monologue_node.py`** (the one existing `trains.open()` call site, the Idle
  Line's core tick) — now passes `product_type=cargo_types.THOUGHT` when `self._train_kind ==
  "thought"` (the idle-thought generator job in the station map). Left `None` for `"reading"`
  trains — that shape isn't one of the 19 named station products, so it's untagged rather than
  guessed.

Not done, deliberately out of scope per the plan's own "separate design/build decision" note: no
NEW couriers/buses were built to fill the 5 gaps the plan named (Idle→Conversation, Deep Line
outbound, peer→recall, dream-freight window, SELF_CONCEPT_DELTA's no-delivery). This job was only
the naming/schema convention D-0082 scoped it as.

Verified: `python -c "from core import cargo_types as ct; assert len(ct.STATION_PRODUCT_TYPES)==19; assert len(ct.WORLD_CARGO_TYPES)==4"`
passes; a live `trains.open(..., product_type=...)` round-trip through `update()`/`close()`
confirmed the field persists on the record and closes cleanly. Delivery-log rows for all 4
retrofitted routes confirmed to carry `cargo_type` (verified via direct calls to each module's
`_log_delivery`/`_log_delivery`, then reverted out of the live `data/*_log.jsonl` files so no test
data was left in the real logs).
