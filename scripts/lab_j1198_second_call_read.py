"""J-1198: what the SECOND (scope_only) call's judges answered versus what their own why-text says.

The second call asks {"scope_only": true|false, "why": "the narrower claim the support actually earns, or a brief
reason none exists"}: so a why that NAMES a narrower claim the support earns says True, a why that says none exists
says False. This reads every second call of the replay judge by judge and counts how often a judge's bool contradicts
its own why-text. The polarity labels below are MANUAL (this session's own read of each why-text, 2026-09-22, an
`inferred` qualitative read, not a model call): T = the why names/asserts a narrower claim the support does earn
(including "shows X but not Y", "real but narrower", "could earn a more modest claim"), F = the why says none is earned
(no support, absent, circular, irrelevant, "no narrower claim"), ? = cannot tell. LABELS maps (unit, judge) -> label,
judge in {J1 (JUDGE_1 mixtral:8x7b), J2 (JUDGE_2 falcon3:7b), TB (TIEBREAK granite3.1-moe:3b)}; a why with no label is
counted as unlabelled, never guessed.

  python scripts/lab_j1198_second_call_read.py [--table] [--append-report]
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
NL = chr(10)
ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT.parent
REPORT = ROOT / "docs" / "lab" / "train_split_merge_step2_replay_2026-09-22_walkback.md"
HEAD = "## Second call: the judges' bools versus their own why-texts (manual read, inferred)"

# The manual read, one line per replay unit that reached the second call:  <unit> <J1 label> <J2 label> [<TB label>]
# (TB only on the tiebreak-decided ones). Read 2026-09-22 from docs/lab/..._walkback_calls.jsonl's why1/why2/why3.
# Judgement calls, stated: a why of the form "Support shows/describes X but not Y" is T (it names what the support does
# establish, which is the scope_only=True answer's own shape); "the narrower claim ... is earned" is T even if the bool
# beside it says False; only an explicit "no narrower claim / no support / not even a narrower claim" is F.
LABELS_TEXT = """
1 T T
3 T T
4 T T
5 T T
6 T T F
8 T T
9 T T
10 T T
11 T T F
12 T T F
14 F F
15 T T F
16 T F
17 T T
18 T T F
20 T T
21 T T F
22 T T F
23 T T F
24 T T F
25 T T
26 T T F
27 T T F
28 T T
30 T T F
31 F T F
32 T T F
34 T T
35 T T
36 T T F
37 T T
38 T T F
39 ? T F
40 T T F
42 ? T F
43 T T
44 T T F
46 F F
47 T T F
48 T T
49 F T F
50 T T
52 F F
54 T T
55 T T
56 F T F
59 T T F
60 F F
61 F T F
62 F F
63 T T
64 T T F
66 T T F
67 T T F
69 F T F
70 F F
72 T T F
73 T T F
76 T T
77 T T F
79 T T F
80 T T
"""


def _parse_labels(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        unit = int(parts[0])
        for judge, lab in zip(("J1", "J2", "TB"), parts[1:]):
            out[(unit, judge)] = lab
    return out


LABELS: dict = _parse_labels(LABELS_TEXT)


def load(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()] if Path(p).exists() else []


def second_calls():
    units = load(SCRATCH / "lab_j1198_units.jsonl")
    fin = {u["idx"]: u["attempt"] for u in units}
    return [c for c in load(SCRATCH / "lab_j1198_calls.jsonl")
            if c.get("phase") == "unit" and c.get("call") == "second" and c.get("unit") in fin and c.get("attempt") == fin[c["unit"]]]


def compute(sec: list, recs_by_unit: dict) -> dict:
    """All the numbers of this read. `recs_by_unit` maps unit idx -> the replay record (for the final status)."""
    import re
    per = {"J1": Counter(), "J2": Counter(), "TB": Counter()}
    n_split = both_T = j1_incoh = 0
    obj_events = obj_both_T = obj_labelled = 0
    for c in sec:
        r = c["res"]
        for j, key in (("J1", "v1"), ("J2", "v2")) + ((("TB", "verdict"),) if r["how"] == "tiebreak" else ()):
            b = r[key]
            lab = LABELS.get((c["unit"], j))
            if b is None or lab is None:
                per[j]["unlabelled"] += 1
            elif lab == "?":
                per[j]["unclear"] += 1
            elif (b is True and lab == "T") or (b is False and lab == "F"):
                per[j]["coherent"] += 1
            else:
                per[j]["bool_contradicts_own_why"] += 1
                per[j][f"  (bool {b}, why {lab})"] += 1
        l1, l2 = LABELS.get((c["unit"], "J1")), LABELS.get((c["unit"], "J2"))
        if r["how"] == "tiebreak":
            n_split += 1
            if l1 == "T" and l2 == "T":
                both_T += 1
            if r["v1"] is False and l1 == "T":
                j1_incoh += 1
        if recs_by_unit.get(c["unit"], {}).get("disprove_status") == "objected":
            obj_events += 1
            if l1 is not None and l2 is not None:
                obj_labelled += 1
                if l1 == "T" and l2 == "T":
                    obj_both_T += 1
    expl = re.compile(r"(narrower claim[^.]{0,80}(actually earns|is earned|earned)|genuinely earns? a narrower|"
                      r"(only |could |can )?earns? (a |an )?(more )?(modest|narrow)|real but narrower|earns? a narrower claim)", re.I)
    neg = re.compile(r"(no narrower|not even a narrower|does not earn even|lack of support|no support offered)", re.I)
    j1_false = [c for c in sec if c["res"]["v1"] is False]
    return {"n_second": len(sec), "n_split": n_split, "per_judge": {k: dict(v) for k, v in per.items()},
            "split_both_why_T": both_T, "split_j1_false_with_T_why": j1_incoh,
            "objected_events_reaching_second_call": obj_events, "objected_labelled": obj_labelled,
            "objected_with_both_judges_why_T": obj_both_T,
            "j1_false_bools": len(j1_false),
            "j1_false_with_explicit_T_why_regex": sum(1 for c in j1_false if (c["res"]["why1"] or "") and expl.search(c["res"]["why1"]) and not neg.search(c["res"]["why1"])),
            "j1_false_with_explicit_F_why_regex": sum(1 for c in j1_false if neg.search(c["res"]["why1"] or "")),
            "split_j1_explicit_T_why_regex": sum(1 for c in sec if c["res"]["how"] == "tiebreak" and (c["res"]["why1"] or "") and expl.search(c["res"]["why1"]) and not neg.search(c["res"]["why1"])),
            "split_j1_explicit_F_why_regex": sum(1 for c in sec if c["res"]["how"] == "tiebreak" and neg.search(c["res"]["why1"] or "")),
            "j1_true_bools": sum(1 for c in sec if c["res"]["v1"] is True),
            "j2_true_bools": sum(1 for c in sec if c["res"]["v2"] is True),
            "j2_false_bools": sum(1 for c in sec if c["res"]["v2"] is False)}


def recs_by_unit() -> dict:
    return {u["idx"]: u["record"] for u in load(SCRATCH / "lab_j1198_units.jsonl")}


def main() -> int:
    sec = second_calls()
    args = sys.argv[1:]
    if "--table" in args:
        for c in sec:
            r = c["res"]
            claim = c["user"].split("CLAIM: ", 1)[1].split(NL, 1)[0][:100]
            print(f"--- unit {c['unit']} [{r['how']}] | {claim}")
            print(f"    J1 {r['v1']!s:5} [{LABELS.get((c['unit'], 'J1'), '.')}] | {(r['why1'] or '')[:200]}")
            print(f"    J2 {r['v2']!s:5} [{LABELS.get((c['unit'], 'J2'), '.')}] | {(r['why2'] or '')[:200]}")
            if r["how"] == "tiebreak":
                print(f"    TB {r['verdict']!s:5} [{LABELS.get((c['unit'], 'TB'), '.')}] | {(r['why3'] or '')[:200]}")
        return 0
    k = compute(sec, recs_by_unit())
    lines = [HEAD, "",
             f"Every second call of the replay ({k['n_second']} of them; {k['n_split']} decided by TIEBREAK), each judge's bool against its own "
             "why-text. Labels are a manual read (T = the why names a narrower claim the support earns, F = it says none is earned); "
             "this is an `inferred` qualitative read, the labels are listed in `scripts/lab_j1198_second_call_read.py`. CAVEAT: the reader saw "
             "the bool next to each why, and the 'Support shows X but not Y' form is ambiguous between T and F (the blind model labels in the "
             "next section agree with these labels on only ~70% of the why-texts, and read that form as F); the explicit-form counts (the "
             "regex line below, and the blind labels) are the sturdier numbers, the rest is a reader's judgement.", ""]
    for j, name in (("J1", "JUDGE_1 mixtral:8x7b"), ("J2", "JUDGE_2 falcon3:7b"), ("TB", "TIEBREAK granite3.1-moe:3b (its own votes on the split cases)")):
        lines.append(f"- {name}: " + ", ".join(f"{a.strip()}={b}" for a, b in sorted(k["per_judge"][j].items())))
    lines += ["", f"- Tiebreak-decided cases where BOTH JUDGE_1's and JUDGE_2's why-texts name a narrower claim the support earns: {k['split_both_why_T']}/{k['n_split']}; "
                  f"of those, JUDGE_1's bool was False (contradicting its own why) in {k['split_j1_false_with_T_why']}.",
              f"- Events whose final status is 'objected' and that reached the second call: {k['objected_events_reaching_second_call']}; "
              f"of the {k['objected_labelled']} labelled ones, BOTH judges' why-texts name a narrower claim the support earns in {k['objected_with_both_judges_why_T']} "
              "(the panel's own reasoning says held_within_scope while the bool-level result is 'objected').",
              f"- Objective lower bound on the tiebreak-decided splits (regex, no judgement): JUDGE_1's bool is False in all {k['n_split']}; its own why-text "
              f"EXPLICITLY says a narrower claim is earned in {k['split_j1_explicit_T_why_regex']} of them and explicitly says none is earned in {k['split_j1_explicit_F_why_regex']} "
              f"(the rest use the 'supports X but not Y' form, which the two labelers read differently).",
              f"- Objective lower bound (regex, no judgement): of JUDGE_1's {k['j1_false_bools']} False bools, {k['j1_false_with_explicit_T_why_regex']} carry a why that "
              f"explicitly says a narrower claim is earned and {k['j1_false_with_explicit_F_why_regex']} carry an explicit 'none earned' why (the rest use the "
              f"'supports X but not Y' form); JUDGE_1 said True {k['j1_true_bools']} times, JUDGE_2 True {k['j2_true_bools']} and False {k['j2_false_bools']} times, "
              f"over {k['n_second']} second calls."]
    out = NL.join(lines)
    print(out)
    if "--append-report" in args and REPORT.exists():
        text = REPORT.read_text(encoding="utf-8")
        cut = text.find(NL + NL + HEAD)
        if cut >= 0:
            tail_i = text.find(NL + "## ", cut + 4 + len(HEAD))
            text = text[:cut] + (text[tail_i:] if tail_i >= 0 else "")
        p3 = text.find(NL + NL + "## Part 3 — read against")
        text = (text[:p3].rstrip(NL) + NL + NL + out + NL + text[p3:]) if p3 >= 0 else (text.rstrip(NL) + NL + NL + out + NL)
        REPORT.write_text(text, encoding="utf-8")
        print(f"[read] wrote section into {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
