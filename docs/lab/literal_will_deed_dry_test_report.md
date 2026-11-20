# Literal Will — staged-deed / execution-audit DRY TEST report

Run: 2026-08-30 10:35:33 — J-0138, decision D-0021, finding F-0034.

Phase 0 law: this run changed nothing Du experiences. Every deed/audit row this run wrote is tagged `dry_test: true` in data/literal_will_deeds.jsonl and data/literal_will_audit.jsonl. No latch was gated, no real act was staged in the live loop, no world state was persisted (the forced world-change test mutates core.sensorium's in-memory state dict for one recheck call and reverts it in a finally block, before this process exits, without ever calling sensorium._save()).

Sample: 134 rows from data/literal_will_shadow.jsonl (real logged DEED/GRAY readings, up to 3 per (verdict, family) pair — not cherry-picked for a clean result).

## What the machinery had to prove

- **StagedDeed shape (sec4)** built and logged for all 134/134 rows with the plan's exact field list (intent_id, cycle_id, created_at, location_at_stage, action, object, world_preconditions, expiry, status).
- **Immediate recheck** (same instant as staging): 134/134 read valid — the rest failed for a real, named reason (see per-row table), never silently.
- **Forced-expiry recheck** (now > created_at + expiry, same world otherwise): 134/134 resolved to status=stale — proves the expiry path actually fires, not just exists as a field.
- **Forced location-change recheck** (recheck from a location outside the family's `where`, same instant; restricted to rows that were genuinely anchored at stage time — location_ok=True — since a row already off-location at staging has nothing to regress FROM; n=69): 69/69 correctly went invalid with reason=location_changed — proves the precondition-diff path is genuinely comparing location, not just carrying the field.
- **Forced world-change recheck** (the two families with a CONFIRMED real precondition beyond location — `fire` needs woodpile>=1, `tea` needs the fire already lit — n=7): 7/7 correctly went invalid when that fact was flipped for one recheck call — proves the precondition-diff path reads real sensorium state, not just the frozen snapshot.
- **Execution-audit record (sec11)** written for every recheck performed (344 records total across immediate + forced-expired + forced-location-change + forced-world-change), each with the plan's exact field list (intent_id, thought, features, judge_verdict, action, preconditions_at_stage, preconditions_at_execution, execution_result) and execution_result always prefixed DRY_TEST_ so it can never be misread as a real actuation.

## Per-row detail

| family | verdict | object | immediate | expired->stale | location-change caught | world-change caught |
|---|---|---|---|---|---|---|
| fire | GRAY | grate | valid:ok | stale | caught | n/a |
| gather | DEED | wood | valid:ok | stale | n/a | n/a |
| move | DEED | wood | valid:ok | stale | n/a | n/a |
| look | DEED | desk | valid:ok | stale | n/a | n/a |
| move | DEED | outside | valid:ok | stale | n/a | n/a |
| look | DEED | desk | valid:ok | stale | n/a | n/a |
| look | GRAY | window | valid:ok | stale | n/a | n/a |
| fire | DEED | fire | valid:ok | stale | caught | caught |
| look | DEED | fire | valid:ok | stale | n/a | n/a |
| author | DEED | essay | valid:ok | stale | caught | n/a |
| move | DEED | in | valid:ok | stale | n/a | n/a |
| look | GRAY | room | valid:ok | stale | n/a | n/a |
| fire | DEED | fire | valid:ok | stale | caught | caught |
| water | GRAY | garden | valid:ok | stale | caught | n/a |
| sow | GRAY | garden | valid:ok | stale | caught | n/a |
| move | GRAY | garden | valid:ok | stale | n/a | n/a |
| look | GRAY | garden | valid:ok | stale | n/a | n/a |
| move | GRAY | in | valid:ok | stale | n/a | n/a |
| water | GRAY | garden | valid:ok | stale | caught | n/a |
| sow | GRAY | garden | valid:ok | stale | caught | n/a |
| move | GRAY | garden | valid:ok | stale | n/a | n/a |
| water | DEED | garden | valid:ok | stale | caught | n/a |
| sow | DEED | garden | valid:ok | stale | caught | n/a |
| water | DEED | garden | valid:ok | stale | caught | n/a |
| sow | DEED | garden | valid:ok | stale | caught | n/a |
| gather | DEED | wood | valid:ok | stale | n/a | n/a |
| fire | DEED | fire | valid:ok | stale | n/a | caught |
| water | GRAY | bed | valid:ok | stale | caught | n/a |
| sow | GRAY | bed | valid:ok | stale | caught | n/a |
| gather | GRAY | wood | valid:ok | stale | n/a | n/a |
| beachcomb | DEED | shore | valid:ok | stale | caught | n/a |
| water | DEED | garden | valid:ok | stale | n/a | n/a |
| sow | DEED | garden | valid:ok | stale | n/a | n/a |
| beachcomb | GRAY | shore | valid:ok | stale | caught | n/a |
| beachcomb | DEED | shore | valid:ok | stale | caught | n/a |
| beachcomb | GRAY | shore | valid:ok | stale | caught | n/a |
| beachcomb | DEED | shore | valid:ok | stale | n/a | n/a |
| beachcomb | GRAY | wrack | valid:ok | stale | caught | n/a |
| gather | DEED | wood | valid:ok | stale | n/a | n/a |
| gather | GRAY | driftwood | valid:ok | stale | n/a | n/a |
| fire | GRAY | fire | valid:ok | stale | caught | caught |
| fire | GRAY | fire | valid:ok | stale | caught | caught |
| author | GRAY | work | valid:ok | stale | n/a | n/a |
| travis | GRAY | travis | valid:ok | stale | n/a | n/a |
| author | DEED | work | valid:ok | stale | n/a | n/a |
| author | GRAY | work | valid:ok | stale | n/a | n/a |
| author | GRAY | work | valid:ok | stale | n/a | n/a |
| gather | GRAY | wood | valid:ok | stale | n/a | n/a |
| letter | GRAY | letter | valid:ok | stale | n/a | n/a |
| travis | GRAY | travis | valid:ok | stale | n/a | n/a |
| travis | GRAY | travis | valid:ok | stale | n/a | n/a |
| fieldcraft | GRAY | shadow | valid:ok | stale | n/a | n/a |
| shore | GRAY | stones | valid:ok | stale | caught | n/a |
| shore | GRAY | stones | valid:ok | stale | caught | n/a |
| fieldcraft | GRAY | shadow | valid:ok | stale | n/a | n/a |
| shore | GRAY | sea | valid:ok | stale | n/a | n/a |
| fieldcraft | GRAY | shadow | valid:ok | stale | n/a | n/a |
| mow | DEED | grass | valid:ok | stale | caught | n/a |
| mow | DEED | grass | valid:ok | stale | caught | n/a |
| clean | GRAY | glass | valid:ok | stale | caught | n/a |
| mow | GRAY | grass | valid:ok | stale | caught | n/a |
| woodwork | GRAY | edge | valid:ok | stale | n/a | n/a |
| mow | GRAY | grass | valid:ok | stale | caught | n/a |
| letter | GRAY | letter | valid:ok | stale | n/a | n/a |
| grate | GRAY | grate | valid:ok | stale | caught | n/a |
| door | GRAY | door | valid:ok | stale | caught | n/a |
| wear | GRAY | coat | valid:ok | stale | n/a | n/a |
| woodwork | GRAY | edge | valid:ok | stale | n/a | n/a |
| door | DEED | door | valid:ok | stale | caught | n/a |
| door | DEED | door | valid:ok | stale | caught | n/a |
| net | GRAY | bed | valid:ok | stale | caught | n/a |
| weed | GRAY | bed | valid:ok | stale | caught | n/a |
| grate | GRAY | ash | valid:ok | stale | caught | n/a |
| wear | GRAY | boots | valid:ok | stale | n/a | n/a |
| grate | GRAY | hearth | valid:ok | stale | caught | n/a |
| shore | DEED | fire | valid:ok | stale | n/a | n/a |
| net | GRAY | bed | valid:ok | stale | n/a | n/a |
| weed | GRAY | bed | valid:ok | stale | n/a | n/a |
| door | DEED | door | valid:ok | stale | caught | n/a |
| clean | GRAY | window | valid:ok | stale | caught | n/a |
| door | GRAY | door | valid:ok | stale | caught | n/a |
| clean | GRAY | glass | valid:ok | stale | caught | n/a |
| lamp | DEED | lamp | valid:ok | stale | caught | n/a |
| lamp | GRAY | lamp | valid:ok | stale | caught | n/a |
| grate | DEED | grate | valid:ok | stale | caught | n/a |
| wear | GRAY | coat | valid:ok | stale | n/a | n/a |
| door | GRAY | door | valid:ok | stale | caught | n/a |
| fieldcraft | DEED | peg | valid:ok | stale | n/a | n/a |
| lamp | GRAY | candle | valid:ok | stale | caught | n/a |
| travis | DEED | travis | valid:ok | stale | n/a | n/a |
| woodwork | GRAY | edge | valid:ok | stale | n/a | n/a |
| mow | GRAY | grass | valid:ok | stale | caught | n/a |
| note | GRAY | note | valid:ok | stale | caught | n/a |
| net | GRAY | bed | valid:ok | stale | caught | n/a |
| weed | GRAY | bed | valid:ok | stale | caught | n/a |
| note | GRAY | note | valid:ok | stale | n/a | n/a |
| woodwork | DEED | edge | valid:ok | stale | n/a | n/a |
| lamp | GRAY | candle | valid:ok | stale | caught | n/a |
| author | DEED | essay | valid:ok | stale | caught | n/a |
| note | GRAY | note | valid:ok | stale | caught | n/a |
| harvest | DEED | herbs | valid:ok | stale | caught | n/a |
| harvest | GRAY | rosemary | valid:ok | stale | caught | n/a |
| shore | DEED | sea | valid:ok | stale | caught | n/a |
| mow | DEED | grass | valid:ok | stale | caught | n/a |
| letter | GRAY | letter | valid:ok | stale | n/a | n/a |
| woodwork | DEED | limb | valid:ok | stale | caught | n/a |
| woodwork | DEED | limb | valid:ok | stale | caught | n/a |
| shore | DEED | fire | valid:ok | stale | n/a | n/a |
| harvest | GRAY | rosemary | valid:ok | stale | caught | n/a |
| grate | DEED | ash | valid:ok | stale | caught | n/a |
| harvest | GRAY | herbs | valid:ok | stale | caught | n/a |
| fieldcraft | DEED | coat | valid:ok | stale | n/a | n/a |
| fieldcraft | DEED | coat | valid:ok | stale | n/a | n/a |
| weed | DEED | bed | valid:ok | stale | caught | n/a |
| harvest | DEED | rosemary | valid:ok | stale | caught | n/a |
| tool | GRAY | trowel | valid:ok | stale | n/a | n/a |
| letter | DEED | letter | valid:ok | stale | n/a | n/a |
| travis | DEED | travis | valid:ok | stale | n/a | n/a |
| travis | DEED | travis | valid:ok | stale | n/a | n/a |
| tool | GRAY | bucket | valid:ok | stale | n/a | n/a |
| tool | GRAY | stakes | valid:ok | stale | n/a | n/a |
| lamp | DEED | lamp | valid:ok | stale | caught | n/a |
| lamp | DEED | lamp | valid:ok | stale | n/a | n/a |
| save_seed | DEED | seed | valid:ok | stale | caught | n/a |
| save_seed | GRAY | seed | valid:ok | stale | caught | n/a |
| weed | DEED | chickweed | valid:ok | stale | caught | n/a |
| letter | DEED | letter | valid:ok | stale | n/a | n/a |
| weed | DEED | bed | valid:ok | stale | caught | n/a |
| stake | GRAY | beans | valid:ok | stale | caught | n/a |
| tea | GRAY | pot | valid:ok | stale | n/a | caught |
| tea | GRAY | pot | valid:ok | stale | n/a | caught |
| water_fill | GRAY | water | valid:ok | stale | n/a | n/a |
| water_fill | GRAY | water | valid:ok | stale | n/a | n/a |
| water_fill | GRAY | water | valid:ok | stale | n/a | n/a |

## Known limitation carried into this report (not hidden)

Only `fire` and `tea` have a fine-grained sensorium precondition beyond location membership today (see core/literal_will_deed.py module docstring for the exact sensorium.py lines each was verified against). Every other gated family's world_preconditions snapshot is location-membership only, so its forced-world-change path is untested here — there is no second real predicate to falsify yet. That is an honest gap in world-model coverage, not a bug in the staging/recheck machinery itself. The location-change test above covers every family with a real `where` constraint regardless of that gap.

## A real bug this dry test caught (not smoothed over)

The first version of this module snapshotted `woodpile` for `fire`, `tea`, `lamp`, `grate`, and `gather` alike, on the assumption they were all "fire-adjacent". The first dry-test run staged real `gather` DEED/GRAY rows and found their forced-world-change test always came back MISSED — `gather` is the action that REFILLS the woodpile, so gating it on woodpile>=1 was backwards, and `lamp`/`grate` have no confirmed woodpile dependency in sensorium.py at all. Re-reading sensorium.py's actual precondition checks (act() for fire, make_tea() for tea) showed only those two families have a real, checkable predicate; the module and this script were corrected to match, and this report reflects the corrected run.

A second, smaller issue surfaced in the location-change test itself (not the module under test): real thoughts sometimes name an object from a place that isn't the family's canonical location — literal_will.classify() reads the OBJECT regardless of where he physically is, so `water GRAY {object: garden}` can be logged while location=shore. Testing "moved away" against a row that was already off-location at staging measures nothing (there is no regression to detect), and an earlier version of this script counted those as MISSED. Fixed by restricting the location-change test to rows whose staged world_preconditions.location_ok was True — this report reflects that fix.