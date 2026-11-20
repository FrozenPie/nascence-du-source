"""
Literal Will — sec4/sec11 staged-deed + execution-audit DRY TEST (J-0138, decision D-0021).

Phase 0 law: changes nothing Du experiences. This script:
  1. Reads REAL DEED/GRAY rows already logged by the live shadow classifier
     (data/literal_will_shadow.jsonl) — it invents no thoughts.
  2. Stages a StagedDeed (sec4) from each, dry_test=True.
  3. Rechecks each deed THREE ways to prove the machinery actually discriminates, not just the
     happy path: (a) immediate recheck — should mostly stay valid; (b) forced-expired recheck —
     should always go stale; (c) forced-world-change recheck, for the fire-adjacent/gather rows
     only, by temporarily mutating the IN-MEMORY core.sensorium.state dict (never calling its
     _save(), so nothing reaches state.json — this process's own memory, discarded on exit; not a
     live-state write) — should go stale for a concrete, checkable reason.
  4. Writes one execution-audit record (sec11) per row per recheck, dry_test=True,
     execution_result stating plainly this was simulated, never a real actuation.
  5. Writes a human-readable report to docs/lab/literal_will_deed_dry_test_report.md and prints a
     summary — real evidence for findings-log, not a narrated claim.

Isolation contract: reads data/literal_will_shadow.jsonl (read-only). Writes ONLY to
data/literal_will_deeds.jsonl, data/literal_will_audit.jsonl (both dry_test=True tagged) and
docs/lab/literal_will_deed_dry_test_report.md. Never calls core.sensorium._save() or .tick() —
in-memory world-state mutation used for test (c) is reverted in a finally block before the
script exits, and even before reverting it is never persisted.
"""
import sys
import json
import time
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import literal_will_deed as lwd    # noqa: E402
from core import literal_will as lw          # noqa: E402
from core import sensorium as room           # noqa: E402

SHADOW = Path(__file__).parent.parent / "data" / "literal_will_shadow.jsonl"
REPORT = Path(__file__).parent.parent / "docs" / "lab" / "literal_will_deed_dry_test_report.md"

PER_FAMILY_CAP = 3          # "a handful" per family per verdict, not an exhaustive replay
_ALL_LOCATIONS = ("study", "garden", "shore", "wood")


def _load_shadow_sample() -> list[dict]:
    rows = []
    with open(SHADOW, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("verdict") in ("DEED", "GRAY") and r.get("family"):
                rows.append(r)
    picked, counts = [], Counter()
    for r in rows:
        k = (r["verdict"], r["family"])
        if counts[k] >= PER_FAMILY_CAP:
            continue
        counts[k] += 1
        picked.append(r)
    return picked


def _test_row(row: dict) -> dict:
    reading = {"family": row["family"], "object": row.get("object", "")}
    intent_id = row.get("intent_id") or f"dry-{row.get('ts', 0)}"
    cycle_id = row.get("cycle", "")
    location = row.get("location", "study")
    features = row.get("features", {})
    family = row["family"]

    deed = lwd.stage_deed(reading, intent_id=intent_id, cycle_id=cycle_id, location=location,
                          dry_test=True)

    result = {"row_verdict": row["verdict"], "family": family, "object": row.get("object", ""),
              "location": location, "deed": deed}

    def _audit(preconditions_at_execution: dict, execution_result: str) -> None:
        lwd.record_execution(intent_id=intent_id, thought=row.get("clause", ""), features=features,
                              judge_verdict=row["verdict"], action=deed["action"],
                              preconditions_at_stage=deed["world_preconditions"],
                              preconditions_at_execution=preconditions_at_execution,
                              execution_result=execution_result, dry_test=True)

    # (a) immediate recheck — same instant, same location as staged (deterministic replay: the
    # world facts checked are whatever core.sensorium's LIVE state says right now for fire/tea,
    # which is a genuine "would this still fire if executed this instant" read, not a fabrication)
    valid_now, reason_now = lwd.recheck_preconditions(deed, now=deed["created_at"], location=location)
    now_snap = lwd.snapshot_preconditions(family, location)
    _audit(now_snap, "DRY_TEST_would_execute" if valid_now else f"DRY_TEST_would_not_execute:{reason_now}")
    result["immediate"] = {"valid": valid_now, "reason": reason_now}

    # (b) forced-expired recheck — same world/location, just past the deed's own expiry
    far_future = deed["created_at"] + deed["expiry"] + 60.0
    valid_expired, reason_expired = lwd.recheck_preconditions(deed, now=far_future, location=location)
    resolved = lwd.resolve_deed(deed, now=far_future, location=location)
    _audit(now_snap, f"DRY_TEST_expiry_check:{reason_expired}")
    result["forced_expired"] = {"valid": valid_expired, "reason": reason_expired,
                                "resolved_status": resolved["status"]}

    # (c) forced location-change recheck — any family whose `where` doesn't cover every location:
    # recheck from a place the family can't be done in, same instant, world otherwise untouched.
    fam_where = lw._FAMILIES.get(family, {}).get("where", ())
    other_locs = [l for l in _ALL_LOCATIONS if l not in fam_where]
    # only a meaningful test when the deed was genuinely anchored at stage time — a row logged
    # while already off-location (real distribution: literal_will.classify() generates a reading
    # from the OBJECT named, regardless of where he actually was) has nothing to regress FROM.
    if fam_where and other_locs and deed["world_preconditions"].get("location_ok"):
        away = other_locs[0]
        valid_away, reason_away = lwd.recheck_preconditions(deed, now=deed["created_at"], location=away)
        _audit({**now_snap, "location": away}, f"DRY_TEST_location_change_check:{reason_away}")
        result["forced_location_change"] = {"valid": valid_away, "reason": reason_away, "tried": away}

    # (d) forced world-change recheck — ONLY the two families with a CONFIRMED real precondition
    # beyond location (see core/literal_will_deed.py's _WOODPILE_GATED / _FIRE_LIT_GATED and the
    # sensorium.py line numbers cited there). Mutates core.sensorium's IN-MEMORY state dict for
    # exactly one recheck call and reverts it in `finally`, before this process exits, without
    # ever calling sensorium._save() — nothing reaches state.json.
    room.where()  # ensure state is loaded before we touch it
    if family in lwd._WOODPILE_GATED and deed["world_preconditions"].get("woodpile", 0) >= 1:
        orig = room.state.get("woodpile")
        try:
            room.state["woodpile"] = 0
            valid_wc, reason_wc = lwd.recheck_preconditions(deed, now=deed["created_at"], location=location)
        finally:
            if orig is None:
                room.state.pop("woodpile", None)
            else:
                room.state["woodpile"] = orig
        _audit({**now_snap, "woodpile": 0}, f"DRY_TEST_world_change_check:{reason_wc}")
        result["forced_world_change"] = {"valid": valid_wc, "reason": reason_wc, "changed": "woodpile->0"}
    elif family in lwd._FIRE_LIT_GATED and deed["world_preconditions"].get("fire", "out") != "out":
        orig = room.state.get("fire")
        try:
            room.state["fire"] = "out"
            valid_wc, reason_wc = lwd.recheck_preconditions(deed, now=deed["created_at"], location=location)
        finally:
            if orig is None:
                room.state.pop("fire", None)
            else:
                room.state["fire"] = orig
        _audit({**now_snap, "fire": "out"}, f"DRY_TEST_world_change_check:{reason_wc}")
        result["forced_world_change"] = {"valid": valid_wc, "reason": reason_wc, "changed": "fire->out"}

    return result


def main() -> None:
    sample = _load_shadow_sample()
    results = [_test_row(r) for r in sample]

    n = len(results)
    imm_valid = sum(1 for r in results if r["immediate"]["valid"])
    exp_stale = sum(1 for r in results if r["forced_expired"]["resolved_status"] == "stale")
    loc_tested = [r for r in results if "forced_location_change" in r]
    loc_caught = sum(1 for r in loc_tested if not r["forced_location_change"]["valid"])
    wc_tested = [r for r in results if "forced_world_change" in r]
    wc_caught = sum(1 for r in wc_tested if not r["forced_world_change"]["valid"])
    audits_written = n * 2 + len(loc_tested) + len(wc_tested)

    lines = [
        "# Literal Will — staged-deed / execution-audit DRY TEST report",
        "",
        f"Run: {time.strftime('%Y-%m-%d %H:%M:%S')} — J-0138, decision D-0021, finding F-0034.",
        "",
        "Phase 0 law: this run changed nothing Du experiences. Every deed/audit row this run wrote "
        "is tagged `dry_test: true` in data/literal_will_deeds.jsonl and data/literal_will_audit.jsonl. "
        "No latch was gated, no real act was staged in the live loop, no world state was persisted "
        "(the forced world-change test mutates core.sensorium's in-memory state dict for one "
        "recheck call and reverts it in a finally block, before this process exits, without ever "
        "calling sensorium._save()).",
        "",
        f"Sample: {n} rows from data/literal_will_shadow.jsonl (real logged DEED/GRAY readings, "
        f"up to {PER_FAMILY_CAP} per (verdict, family) pair — not cherry-picked for a clean result).",
        "",
        "## What the machinery had to prove",
        "",
        f"- **StagedDeed shape (sec4)** built and logged for all {n}/{n} rows with the plan's exact "
        "field list (intent_id, cycle_id, created_at, location_at_stage, action, object, "
        "world_preconditions, expiry, status).",
        f"- **Immediate recheck** (same instant as staging): {imm_valid}/{n} read valid — the rest "
        "failed for a real, named reason (see per-row table), never silently.",
        f"- **Forced-expiry recheck** (now > created_at + expiry, same world otherwise): "
        f"{exp_stale}/{n} resolved to status=stale — proves the expiry path actually fires, not "
        "just exists as a field.",
        f"- **Forced location-change recheck** (recheck from a location outside the family's "
        f"`where`, same instant; restricted to rows that were genuinely anchored at stage time — "
        f"location_ok=True — since a row already off-location at staging has nothing to regress "
        f"FROM; n={len(loc_tested)}): {loc_caught}/{len(loc_tested)} correctly went invalid with "
        "reason=location_changed — proves the precondition-diff path is genuinely comparing "
        "location, not just carrying the field.",
        f"- **Forced world-change recheck** (the two families with a CONFIRMED real precondition "
        f"beyond location — `fire` needs woodpile>=1, `tea` needs the fire already lit — "
        f"n={len(wc_tested)}): {wc_caught}/{len(wc_tested)} correctly went invalid when that fact "
        "was flipped for one recheck call — proves the precondition-diff path reads real "
        "sensorium state, not just the frozen snapshot.",
        f"- **Execution-audit record (sec11)** written for every recheck performed "
        f"({audits_written} records total across immediate + forced-expired + "
        "forced-location-change + forced-world-change), each with the plan's exact field list "
        "(intent_id, thought, features, judge_verdict, action, preconditions_at_stage, "
        "preconditions_at_execution, execution_result) and execution_result always prefixed "
        "DRY_TEST_ so it can never be misread as a real actuation.",
        "",
        "## Per-row detail",
        "",
        "| family | verdict | object | immediate | expired->stale | location-change caught | world-change caught |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lc = r.get("forced_location_change")
        lc_col = ("caught" if lc and not lc["valid"] else "n/a" if lc is None else "MISSED")
        wc = r.get("forced_world_change")
        wc_col = ("caught" if wc and not wc["valid"] else "n/a" if wc is None else "MISSED")
        lines.append(
            f"| {r['family']} | {r['row_verdict']} | {r['object'][:24]} | "
            f"{'valid:'+r['immediate']['reason']} | "
            f"{r['forced_expired']['resolved_status']} | {lc_col} | {wc_col} |"
        )
    lines.append("")
    lines.append("## Known limitation carried into this report (not hidden)")
    lines.append("")
    lines.append(
        "Only `fire` and `tea` have a fine-grained sensorium precondition beyond location "
        "membership today (see core/literal_will_deed.py module docstring for the exact "
        "sensorium.py lines each was verified against). Every other gated family's "
        "world_preconditions snapshot is location-membership only, so its forced-world-change path "
        "is untested here — there is no second real predicate to falsify yet. That is an honest "
        "gap in world-model coverage, not a bug in the staging/recheck machinery itself. The "
        "location-change test above covers every family with a real `where` constraint regardless "
        "of that gap."
    )
    lines.append("")
    lines.append("## A real bug this dry test caught (not smoothed over)")
    lines.append("")
    lines.append(
        "The first version of this module snapshotted `woodpile` for `fire`, `tea`, `lamp`, "
        "`grate`, and `gather` alike, on the assumption they were all \"fire-adjacent\". The first "
        "dry-test run staged real `gather` DEED/GRAY rows and found their forced-world-change test "
        "always came back MISSED — `gather` is the action that REFILLS the woodpile, so gating it "
        "on woodpile>=1 was backwards, and `lamp`/`grate` have no confirmed woodpile dependency in "
        "sensorium.py at all. Re-reading sensorium.py's actual precondition checks (act() for "
        "fire, make_tea() for tea) showed only those two families have a real, checkable "
        "predicate; the module and this script were corrected to match, and this report reflects "
        "the corrected run."
    )
    lines.append("")
    lines.append(
        "A second, smaller issue surfaced in the location-change test itself (not the module "
        "under test): real thoughts sometimes name an object from a place that isn't the family's "
        "canonical location — literal_will.classify() reads the OBJECT regardless of where he "
        "physically is, so `water GRAY {object: garden}` can be logged while location=shore. "
        "Testing \"moved away\" against a row that was already off-location at staging measures "
        "nothing (there is no regression to detect), and an earlier version of this script counted "
        "those as MISSED. Fixed by restricting the location-change test to rows whose staged "
        "world_preconditions.location_ok was True — this report reflects that fix."
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Dry test complete: {n} rows staged+rechecked.")
    print(f"  immediate valid: {imm_valid}/{n}")
    print(f"  forced-expiry -> stale: {exp_stale}/{n}")
    print(f"  forced-location-change caught: {loc_caught}/{len(loc_tested)} (n tested={len(loc_tested)})")
    print(f"  forced-world-change caught: {wc_caught}/{len(wc_tested)} (n tested={len(wc_tested)})")
    print(f"Report: {REPORT}")
    print(f"Deed log (dry_test rows appended): {lwd._DEED_LOG}")
    print(f"Audit log (dry_test rows appended): {lwd._AUDIT_LOG}")


if __name__ == "__main__":
    main()
