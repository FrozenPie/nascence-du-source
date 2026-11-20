"""J-3288 step 5: the HAND-READ verdicts (made 2026-11-07 by the job agent reading each fact against the passage the writer
saw, with a regex hunt of the passage for every doubtful one). G = grounded in what he saw (stated, paraphrased, or arithmetic
on what is stated); E = embellished/distorted (a date, binding or cause the passage does not support); A = not in the passage.
Strata hand-read: S1 every fact the gemma judge called A (31); S2 every fact the lexical rule called 'absent' that the judge
called P/R (read at sentence level; ~35 of them regex-checked); S3 a seeded random 34 of the facts both instruments passed.
Writes docs/lab/J-3288_data/hand_labels.json  (key 'note.fact_idx')."""
from __future__ import annotations
import json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "docs" / "lab" / "J-3288_data"

PROBLEMS = {
    "1.10": ("E", "passage: 'second week of May, 1801'; note says May 1802 (1802 occurs elsewhere in the session text)"),
    "1.7":  ("E", "royal-table invitation was the 1799 Berlin mission; note dates it 1801 (the Russia mission)"),
    "7.5":  ("E", "passage: current forced the horses to swim diagonally and ice struck them; 'to avoid direct ice impact' is an invented cause"),
    "16.1": ("E", "the bluebird chapter's visible text stops at 'when you first hear t'; 'signals the arrival of spring' is extrapolated; subject 'It' unresolved"),
    "16.2": ("A", "extrapolated from the cut-off first sentence of the chapter (passage[:5000] ends mid-sentence); nothing in the passage says it"),
    "25.1": ("E", "the February 1689 death and exorcism are the FIRST (unnamed) bride's; the note gives them to Marie de Neuborg, the second"),
    "40.1": ("E", "passage: the Infante went to Madrid to marry Maria Amelia but married her sister Maria Louisa; note says he married Maria Amelia"),
    "41.0": ("E", "passage: the TOWN was carried on 21 May and the fort still held out; note says the fort held out until 21 May"),
    "49.3": ("E", "passage: the Customs Director got angry and the narrator held firm (did not enforce the ban); note has the Director enforcing it"),
    "58.3": ("E", "passage: Congress of Luneville on 'the 1st of January following' and peace 'adjourned to 1802'; the note's 'concluded 1 January 1802' is a wrong merge"),
}
# facts that LOOK like leaks lexically (number/name not in the passage) but are grounded
FALSE_ALARM_REASON = {
    "25.0": "'1700' is arithmetic on the passage: Bayonne in 1706, 'six years after the death of Charles II'",
    "28.7": "OCR: the passage prints 'Yesoul'", "38.5": "OCR: the passage prints 'Di rectory'",
    "18.5": "the book is the memoirs of Napoleon (title is in the prompt); passage says 'the Emperor'",
    "40.7": "same: 'Bonaparte'/'the Emperor' named as Napoleon",
}


def main():
    facts = json.load(open(D / "facts_joined.json", encoding="utf-8"))
    out = {}
    for x in facts:
        k = f"{x['note']}.{x['fact_idx']}"
        if x["judge"] == "A" or x["seen"]["verdict"] == "absent" or k in FALSE_ALARM_REASON:
            out[k] = "G"
    pool = [x for x in facts if x["judge"] in ("P", "R") and x["seen"]["verdict"] != "absent"]
    random.Random(3288).shuffle(pool)
    for x in pool[:34]:
        out[f"{x['note']}.{x['fact_idx']}"] = "G"
    for k, (lab, _why) in PROBLEMS.items():
        out[k] = lab
    json.dump(out, open(D / "hand_labels.json", "w", encoding="utf-8"), indent=1)
    json.dump({"problems": {k: {"label": v[0], "why": v[1]} for k, v in PROBLEMS.items()}, "false_alarms": FALSE_ALARM_REASON},
              open(D / "hand_label_notes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    print(len(out), Counter(out.values()))


if __name__ == "__main__":
    main()
