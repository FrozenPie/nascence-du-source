"""J-1198: an independent, blind polarity label for every second-call why-text, from the hot lane model.

lab_j1198_second_call_read.py reads each judge's why-text by hand (with the bool visible next to it) to ask whether the
bool contradicts the judge's own why. This script is the cross-check that does not depend on that reader: the hot lane's
qwen3.5:9b (127.0.0.1:11433, temperature 0, the shared hot lane at concurrency 1) is shown ONLY the why-text (never the bool,
never which judge wrote it, never the claim) with the same T/F rubric, and labels it. A model-produced label is `inferred`
evidence, but it removes the bias of a reader who already saw the bool. Same isolation / rule-4 machinery as the runner.

  python -u scripts/lab_j1198_why_polarity_check.py            # label (resumable) + print the summary
  python -u scripts/lab_j1198_why_polarity_check.py --summary [--append-report]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import lab_j1198_walkback_replay as R   # noqa: E402  (write audit, redirects, rule-4 wrappers)
import lab_j1198_second_call_read as SR  # noqa: E402  (the manual labels + the second-call selector)

sys.stdout.reconfigure(encoding="utf-8")
NL = chr(10)
ap = argparse.ArgumentParser()
ap.add_argument("--summary", action="store_true")
ap.add_argument("--append-report", action="store_true")
ARGS = ap.parse_args()

ROWS = R.SCRATCH / "lab_j1198_polarity_rows.jsonl"
REPORT = ROOT / "docs" / "lab" / "train_split_merge_step2_replay_2026-09-22_walkback.md"
HEAD = "## Second call: blind polarity labels of the why-texts (hot-lane qwen3.5:9b, bool never shown)"
HOT = "http://127.0.0.1:11433"

SYSTEM = (
    'You read ONE short justification written by a judge who was asked this question about a CLAIM and the SUPPORT offered for it: '
    '"Does the support genuinely, independently earn a NARROWER or more modest version of the claim, or is it absent, circular or '
    'irrelevant with no narrower claim earned either?" Decide which answer the justification EXPRESSES, from its text alone. '
    '"T" = it names or asserts some narrower or more modest claim that the support does establish (even if it also says the full '
    'claim is not established). "F" = it says the support earns no narrower claim at all (no support, irrelevant, circular, '
    'nothing established). "?" = you cannot tell. Output ONLY JSON: {"label": "T"} or {"label": "F"} or {"label": "?"}')


def done() -> dict:
    out = {}
    if ROWS.exists():
        for l in ROWS.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                out[(r["unit"], r["judge"])] = r
    return out


def items() -> list:
    out = []
    for c in SR.second_calls():
        r = c["res"]
        for j, key in (("J1", "why1"), ("J2", "why2")) + ((("TB", "why3"),) if r["how"] == "tiebreak" else ()):
            if r.get(key):
                out.append({"unit": c["unit"], "judge": j, "why": r[key], "bool": r[{"J1": "v1", "J2": "v2", "TB": "verdict"}[j]]})
    return out


async def label_all() -> None:
    from core.model_client import call_node_json
    have = done()
    todo = [it for it in items() if (it["unit"], it["judge"]) not in have]
    R.progress("polarity-start", len(have), len(have) + len(todo), "hot lane, why-text only, temperature 0")
    for it in todo:
        R.CUR.update(unit="polarity", phase="polarity", attempt=1, persistent=set())
        lab, err = None, None
        try:
            d = await call_node_json([HOT], SYSTEM, "JUSTIFICATION: " + it["why"], max_tokens=30, temperature=0.0, timeout=300)
            lab = d.get("label") if isinstance(d, dict) else None
        except Exception as exc:                       # noqa: BLE001 -- recorded, never guessed
            err = f"{type(exc).__name__}: {str(exc)[:100]}"
        row = {"unit": it["unit"], "judge": it["judge"], "label": lab if lab in ("T", "F", "?") else None, "err": err, "ts": time.time()}
        R._append_jsonl(ROWS, row)
    R.progress("polarity-done", len(done()), len(items()), f"HOT infra_errors={R.STATS['HOT']['infra_errors']}")


def summary() -> str:
    rows = done()
    its = items()
    per = {"J1": Counter(), "J2": Counter(), "TB": Counter()}
    agree = disagree = 0
    for it in its:
        r = rows.get((it["unit"], it["judge"]))
        lab = r["label"] if r else None
        b = it["bool"]
        if lab is None or b is None:
            per[it["judge"]]["unlabelled"] += 1
        elif lab == "?":
            per[it["judge"]]["unclear"] += 1
        elif (b is True and lab == "T") or (b is False and lab == "F"):
            per[it["judge"]]["coherent"] += 1
        else:
            per[it["judge"]]["bool_contradicts_own_why"] += 1
        man = SR.LABELS.get((it["unit"], it["judge"]))
        if lab in ("T", "F") and man in ("T", "F"):
            if lab == man:
                agree += 1
            else:
                disagree += 1
    j1_false = [it for it in its if it["judge"] == "J1" and it["bool"] is False]
    j1_false_T = sum(1 for it in j1_false if (rows.get((it["unit"], "J1")) or {}).get("label") == "T")
    j1_false_F = sum(1 for it in j1_false if (rows.get((it["unit"], "J1")) or {}).get("label") == "F")
    lines = [HEAD, "",
             "Each judge's why-text was shown alone (no bool, no claim, no judge name) to the hot lane's qwen3.5:9b at temperature 0 with the "
             "same T/F rubric as the manual read (`scripts/lab_j1198_why_polarity_check.py`); an `inferred` cross-check that does not depend "
             "on the reader who saw the bool.", ""]
    for j, name in (("J1", "JUDGE_1 mixtral:8x7b"), ("J2", "JUDGE_2 falcon3:7b"), ("TB", "TIEBREAK granite3.1-moe:3b (its votes on the split cases)")):
        lines.append(f"- {name}: " + ", ".join(f"{k}={v}" for k, v in sorted(per[j].items())))
    # the polarity-CONVENTION-free view: in the tiebreak-decided cases the two judges' bools differ by construction; do their
    # why-texts (blind labels) point the same way?
    split_units = sorted({c["unit"] for c in SR.second_calls() if c["res"]["how"] == "tiebreak"})
    same = diff = unk = same_manual = diff_manual = 0
    for u in split_units:
        a, b2 = (rows.get((u, "J1")) or {}).get("label"), (rows.get((u, "J2")) or {}).get("label")
        if a in ("T", "F") and b2 in ("T", "F"):
            same += int(a == b2)
            diff += int(a != b2)
        else:
            unk += 1
        ma, mb = SR.LABELS.get((u, "J1")), SR.LABELS.get((u, "J2"))
        if ma in ("T", "F") and mb in ("T", "F"):
            same_manual += int(ma == mb)
            diff_manual += int(ma != mb)
    lines += ["", f"- Of JUDGE_1's {len(j1_false)} False bools, the blind label of its own why-text is T (a narrower claim earned) for {j1_false_T} and F (none earned) for {j1_false_F}.",
              f"- Agreement between the blind model labels and the manual labels (both T/F, where both exist): {agree}/{agree + disagree}. "
              "The form 'Support shows X but not Y' is genuinely ambiguous between the two labelers (and the blind labeler also finds "
              "'contradictions' for JUDGE_2, whose bools are mostly True), so read the absolute contradiction counts above as upper-uncertain.",
              f"- The convention-free view: in the {len(split_units)} tiebreak-decided cases the two judges' bools differ by construction (JUDGE_1 False, JUDGE_2 True); "
              f"their why-texts point the SAME way in {same} and OPPOSITE ways in {diff} by the blind labels ({unk} unlabelled), and in {same_manual} vs "
              f"{diff_manual} by the manual labels. The two labelers DISAGREE here (the manual read has the reasonings agreeing while the bools differ; "
              "the blind read does not), so 'the split is mostly a bool-versus-own-why disagreement' is NOT established by this data; only the explicit-form "
              "regex counts in the previous section are objective."]
    out = NL.join(lines)
    print(out)
    return out


def main() -> int:
    if not ARGS.summary:
        if not asyncio.run(R.du_is_down()):
            R.progress("polarity", 0, 0, "Du UP-or-UNKNOWN: refusing to send hub traffic")
            return 3
        asyncio.run(label_all())
    out = summary()
    if ARGS.append_report and REPORT.exists():
        text = REPORT.read_text(encoding="utf-8")
        cut = text.find(NL + NL + HEAD)
        if cut >= 0:
            tail_i = text.find(NL + "## ", cut + 4 + len(HEAD))
            text = text[:cut] + (text[tail_i:] if tail_i >= 0 else "")
        p3 = text.find(NL + NL + "## Part 3 — read against")
        text = (text[:p3].rstrip(NL) + NL + NL + out + NL + text[p3:]) if p3 >= 0 else (text.rstrip(NL) + NL + NL + out + NL)
        REPORT.write_text(text, encoding="utf-8")
        print(f"[polarity] wrote section into {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
