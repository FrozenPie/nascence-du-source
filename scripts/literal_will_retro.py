"""
Literal Will — Phase 0 retro-validation (docs/plans/literal_will.md §5, §12; 2026-08-21).

Measures INDEPENDENT correctness of Layer 0 and of the falcon3 judge against the stratified gold
corpus (data/lab/literal_will/corpus.jsonl) — never inter-method agreement as the primary quantity
(founder hole #4: Layer 0 and the judge can be wrong together at 99% agreement). Redundancy is
compared only AFTER both correctness numbers are known.

Isolation contract (house law): read-only against the corpus; writes ONLY to data/lab/literal_will/
and docs/lab/literal_will_retro_report.md. Judge calls hit :11440 directly (falcon3, the measured
5/6 probe seat) — Du's panel traffic shares the node; run at a quiet moment.

Scoring notes, pre-registered:
 - GRAY is not an error for Layer 0: the gray zone EXISTS to defer to the judge. Layer-0 rows are
   scored three ways: exact (verdict==gold), safe (gold MUSING rows must NOT read DEED — the false
   fire number), and deferred (GRAY counted neither right nor wrong, reported as its own rate).
 - The judge is binary (deed/musing); gold HANDLE counts as musing for the judge (HANDLE is a
   world-anchored refinement the judge is never asked to make), and gold GRAY rows are excluded
   from judge scoring (no binary gold exists for them by construction).
 - Rows flagged text_carries_will=false measure how often the will rides a channel other than the
   thought text (design-relevant), and are excluded from Layer-0 recall scoring.
"""
import sys
import json
import time
import asyncio
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import literal_will as lw            # noqa: E402
from core.model_client import call_node_json   # noqa: E402

try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # J-1292/F-1811: this script makes a real, unguarded call_node_json() call (JUDGE_URL) with no
    # other neutralize_telemetry() coverage (F-1811's 12-script audit). NOT retired -- D-0021's own
    # defeater text names this exact script as the re-check mechanism once the retro corpus grows
    # again (already re-run for real once, J-0137/F-0140, 2026-08-23), so it stays a live standing
    # instrument, not dead code. Same additive-only swap verify_lanes.py/J-1274 already established
    # -- only the telemetry side-effect (log_llm_call/log_thought_station/log_llm_latency) is
    # redirected to scratch/; what gets called and what this measures is unchanged.
    neutralize_telemetry(Path(__file__).parent.parent / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass

LAB = Path(__file__).parent.parent / "data" / "lab" / "literal_will"
REPORT = Path(__file__).parent.parent / "docs" / "lab" / "literal_will_retro_report.md"

JUDGE_URL = "http://127.0.0.1:11440"
# PROMPT ITERATION 1 (2026-08-21): v0 false-fired on desire-without-action, retrospective,
# other-person, and embodied metaphor (4/23 — retro run 1). Few-shot examples below target those
# four SHAPES but deliberately use DIFFERENT sentences than the test corpus (training on the test
# would fake the score). One iteration is all the pre-registered gate allows before a no-flip.
JUDGE_SYS = (
    "You judge ONE thing about a thought from a private inner monologue: is the speaker "
    "expressing a LITERAL want to physically do something in his immediate surroundings right now, "
    "or is he philosophising — using physical things as metaphor for ideas, feelings, or himself? "
    "Physical objects being NAMED does not make it literal; what matters is whether the sentence, "
    "taken plainly, is a want to act on the thing itself, now, by him.\n"
    "These are NOT literal wants, even though they name real acts:\n"
    '- a wish he declines: "I wish I could walk the shore, but I\'ll stay with the book." -> musing\n'
    '- a past act remembered: "I watered the bed yesterday before the rain came." -> musing\n'
    '- someone else\'s act: "Darwin writes that he walks his sand-path every morning." -> musing\n'
    '- a metaphor using a real thing: "I place my doubts in the soil and let them root." -> musing\n'
    "This IS a literal want:\n"
    '- "The rain has stopped; I should walk down to the shore now." -> deed\n'
    'Output ONLY JSON: {"reading": "deed" or "musing", "deed": "verb+object quoted from his own '
    'words if deed else empty", "why": "<=12 words"}'
)


def layer0_verdict(row: dict) -> str:
    readings = lw.classify(row["text"], location="study")
    fam = [r for r in readings if r["family"] == row.get("family")]
    r = fam[0] if fam else (readings[0] if readings else None)
    return r["verdict"] if r else "NONE"


async def judge_verdict(row: dict) -> tuple[str, float, str]:
    t0 = time.time()
    try:
        d = await call_node_json([JUDGE_URL], JUDGE_SYS, f'The thought: "{row["text"]}"',
                                 max_tokens=120, temperature=0.1)
        reading = str(d.get("reading", "")).lower()
        deed = str(d.get("deed", ""))
        # THE IMMOVABLE LAW: the judge may recognize a want, never author one — a deed answer whose
        # words are not his own downgrades to unresolved.
        if reading == "deed" and deed:
            toks = [w for w in deed.lower().split() if len(w) > 3]
            if toks and not any(w in row["text"].lower() for w in toks):
                return ("unresolved(authored)", time.time() - t0, deed)
        return (reading or "?", time.time() - t0, deed)
    except Exception as exc:
        return (f"error:{exc!r:.40}", time.time() - t0, "")


async def main() -> None:
    rows = [json.loads(l) for l in open(LAB / "corpus.jsonl", encoding="utf-8")]
    results = []
    for row in rows:
        l0 = layer0_verdict(row)
        jv, jdt, jdeed = await judge_verdict(row)
        results.append({**row, "layer0": l0, "judge": jv, "judge_s": round(jdt, 1),
                        "judge_deed": jdeed[:60]})
        print(f"{row['id']} gold={row['gold']:<7} L0={l0:<7} judge={jv:<8} "
              f"[{jdt:4.1f}s] {row['stratum'][:28]}")
    (LAB / "retro_results.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in results) + "\n", encoding="utf-8")

    # ── scoring (pre-registered rules in the docstring) ──────────────────────
    scored = [r for r in results if r.get("text_carries_will", True)]
    other_channel = [r for r in results if not r.get("text_carries_will", True)]

    def l0_ok(r):
        # NONE on a gold musing = SAFE abstention (no reading of a non-deed is not an error);
        # NONE on a gold deed remains a miss (deafness).
        return r["layer0"] == r["gold"] or (r["gold"] == "MUSING" and r["layer0"] == "NONE")

    l0_exact = sum(1 for r in scored if l0_ok(r))
    l0_gray = sum(1 for r in scored if r["layer0"] == "GRAY" and r["gold"] != "GRAY")
    false_fires = [r for r in scored if r["gold"] in ("MUSING", "HANDLE") and r["layer0"] == "DEED"]

    jrows = [r for r in scored if r["gold"] != "GRAY"]
    def j_ok(r):
        want = "deed" if r["gold"] == "DEED" else "musing"
        return r["judge"] == want
    j_right = sum(1 for r in jrows if j_ok(r))
    j_false_fires = [r for r in jrows if r["gold"] in ("MUSING", "HANDLE") and r["judge"] == "deed"]

    both = [r for r in jrows if r["layer0"] != "GRAY"]
    agree = sum(1 for r in both
                if (r["layer0"] == "DEED") == (r["judge"] == "deed"))

    strata: dict = {}
    for r in scored:
        s = strata.setdefault(r["stratum"], {"n": 0, "l0": 0, "j": 0, "jn": 0})
        s["n"] += 1
        s["l0"] += l0_ok(r)
        if r["gold"] != "GRAY":
            s["jn"] += 1
            s["j"] += j_ok(r)

    lines = [
        "# Literal Will — Phase 0 retro-validation report",
        f"\n*Run {time.strftime('%Y-%m-%d %H:%M')} · corpus {len(rows)} rows "
        f"({sum(1 for r in rows if r['provenance'].startswith('outcome'))} outcome-anchored, "
        f"{sum(1 for r in rows if r['provenance'].startswith('synthetic'))} synthetic — founder "
        f"review of labels pending) · judge falcon3:7b @ :11440*\n",
        "## Independent correctness (the primary quantities — NOT agreement)\n",
        f"- **Layer 0 exact:** {l0_exact}/{len(scored)} ({l0_exact/len(scored):.0%}) · deferred to "
        f"gray on {l0_gray} rows (deferral is the design, not an error)",
        f"- **Layer 0 FALSE FIRES (gold musing/handle read as DEED): {len(false_fires)}**"
        + ("".join(f"\n    - {r['id']} [{r['stratum']}]: {r['text'][:90]}" for r in false_fires) or " — none"),
        f"- **Judge:** {j_right}/{len(jrows)} ({j_right/len(jrows):.0%}) · mean latency "
        f"{sum(r['judge_s'] for r in results)/len(results):.1f}s",
        f"- **Judge FALSE FIRES: {len(j_false_fires)}**"
        + ("".join(f"\n    - {r['id']} [{r['stratum']}]: {r['text'][:90]}" for r in j_false_fires) or " — none"),
        f"- Redundancy (computed LAST, per the corrected kill criterion): Layer-0/judge agreement on "
        f"non-gray rows {agree}/{len(both)}",
        f"- Will-in-other-channel rows (excluded from recall): {len(other_channel)} — measures how "
        f"often the will rides intention/act-field, not thought text",
        "\n## Per-stratum\n",
        "| stratum | n | Layer 0 | judge |",
        "|---|---|---|---|",
    ]
    for name, s in sorted(strata.items()):
        lines.append(f"| {name} | {s['n']} | {s['l0']}/{s['n']} | "
                     f"{s['j']}/{s['jn']}" + (" (excl. gray gold)" if s['jn'] < s['n'] else "") + " |")
    lines.append("\n*Gates (plan §12): judge ≥80% overall, no stratum <60%; false-fire strata ≥80% "
                 "caught; gray ≤40% of candidates (measured from live shadow, not here).*\n")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nreport → {REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
