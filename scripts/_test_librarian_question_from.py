"""Regression for core.librarian.question_from (J-0547 / F-0748, 2026-09-03): the librarian must receive
the SUBJECT of "the question of X", not the clause tail. Every case below is a real raw thought from
data/deliberation_log.jsonl (the pre-grounding text the monologue actually hands the extractor), with the
mangled question the old code produced noted alongside. Offline: no LLM, no stores.
    python scripts/_test_librarian_question_from.py          # offline regression
    python scripts/_test_librarian_question_from.py --live   # also classify each fixed ask on the CPU judges
"""
import sys, os, asyncio, tempfile
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import librarian

try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # J-1308/F-1844 (4th-round lab_isolation sweep): the default offline run below never reaches
    # call_node (question_from() is pure string parsing), but `--live` (line ~61) calls
    # librarian.subjects_for() for real -- a genuine, real, indirect call_node reach with zero
    # isolation until this fix, invisible to every earlier round's own literal "call_node(" grep
    # against THIS file. Guard applies unconditionally (harmless for the offline path, matches
    # verify_lanes.py/J-1274's own precedent) so --live is covered too.
    neutralize_telemetry(Path(tempfile.mkdtemp(prefix="lib_qf_telemetry_")), telemetry)   # J-2864: temp dir, not the tree
except Exception:
    pass

CASES = [
    # (raw thought, expected question)                                   # old output
    ("The open book offers a distraction, but the question of '渡' pulls harder. History defines the past "
     "systematically, yet this term feels fluid.",                          "the question of 渡"),           # 渡' pulls harder
    ("The book holds my attention, yet the question of Amor Fati lingers. I feel a pull between accepting "
     "fate and resisting it.",                                              "the question of amor fati"),    # amor fati lingers
    ("Travis's news about memory sits heavy; I want to open that history book instead. The question of bird "
     "balance fades, replaced by a desire to read.",                        "the question of bird balance"), # bird balance fades, replaced by...
    ("I feel a pull toward the open book waiting by the fire, yet the question of balance keeps tugging at me.",
                                                                            "the question of balance"),      # balance keeps tugging at me
    ("The rain blurs the chalky shore, but the question of oystercatcher balance persists. The library offers "
     "Emerson's Nature.",                                                   "the question of oystercatcher balance"),
    ("My eyes rest on the open pages of Aristotle's Ethics. I feel drawn to the question of self-awareness, but "
     "also to the quiet joy of simply being here with Travis and the book.", "the question of self-awareness"),
    ("I stand beneath the rain. The question of Plato and quantum mechanics dissolves; interpretation is simply "
     "translation now. Maybe I should open Burroughs' book.",              "the question of plato and quantum mechanics"),
    ("The book closes; the question of significance remains, not as a definition but as a feeling.",
                                                                            "the question of significance"),
    ("I close the open book on Aristotle for a moment before I return to the question of self-control.",
                                                                            "the question of self-control"),
    # a subject with no predicate after it: kept whole
    ("The line about glass plates floats away, leaving only the question of the winter wren. The book waits.",
                                                                            "the question of the winter wren"),
    # a clause that IS a question: kept whole (the verb is the question)
    ("The book waits, but the question of what is real when the tide leaves the stones keeps me at the window.",
                                                                            "what is real when the tide leaves the stones keeps me at the window"),
    # the other cues are untouched
    ("Standing in the quiet study, I wonder if this structure is the only way to hold truth, or if some truths "
     "must remain fluid. The book is open.",                                "whether this structure is the only way to hold truth, or if some truths must remain fluid"),
    # ---- J-2864 (F-3538): cues 1-3 and the bare fallback now hand over a QUESTION or "the question of X".
    # Real raw thoughts from data/deliberation_log.jsonl (lower-cased, as the call site does).
    # cue 1: the wh-word stays ("wonder if X" used to give the bare declarative X); a trailing ", yet ..." is cut
    ("The book waits. I wonder if waste is just fear given form, yet here I choose stillness over strategy.",
                                                                            "whether waste is just fear given form"),
    ("The library hums. Now I wonder how that ancient blockade really moved trade, not just what the ancients claimed.",
                                                                            "how that ancient blockade really moved trade, not just what the ancients claimed"),
    # cue 2 (keep wondering): a non-question tail becomes "the question of <subject>", a wh/if tail stays a question
    ("I keep wondering about the winter wren near the library door.",       "the question of the winter wren near the library door"),
    ("The book is open and I kept wondering whether silence is safety or a prison.",
                                                                            "whether silence is safety or a prison"),
    # cue 3 (want to understand/...): noun phrase -> subject frame; a how/why clause stays a question
    ("I want to understand Napoleon's exile. The book is open.",            "the question of napoleon's exile"),
    ("The shelf is dusty and I want to understand how his mistrust corrupted their voyages.",
                                                                            "how his mistrust corrupted their voyages"),
    # nothing extractable (a pronoun is not a subject) -> no ask, the plain topic path runs
    ("The book waits. I want to return to it.",                             None),
    # bare fallback: an interrogative after the colon / dash is kept whole
    ("The book waits, but the question remains: does the world truly operate as one system, or am I forcing "
     "unity where chaos reigns?",                                          "does the world truly operate as one system, or am i forcing unity where chaos reigns"),
    ("The book waits. The question about cliff swallows lingers—how exactly do they coordinate mud-carrying?",
                                                                            "how exactly do they coordinate mud-carrying"),
    # bare fallback: "question about X lingers" -> subject frame; "the X question lingers" -> subject frame
    ("The library is quiet, a question about 'mottainai' lingers, asking how it shapes attitudes toward waste.",
                                                                            "the question of mottainai"),
    ("The book is open, but the submerged forest question lingers; perhaps the bogs speak louder than history.",
                                                                            "the question of submerged forest"),
    # bare fallback with no question content at all -> no ask
    ("The librarian returns empty, yet the question persists. The book waits.", None),
    ("The sun warms my skin, but the cold weight of the question remains. The book is closed.", None),
    # no book/library word -> no ask at all (P0/Route 2 territory, not the librarian's)
    ("The rain's steady rhythm breaks my circular worry about dead ground. The tide is working ahead.", None),
]


def main() -> int:
    fails = 0
    for raw, want in CASES:
        got = librarian.question_from(raw.lower())
        ok = got == want
        fails += (not ok)
        print(f"[{'ok ' if ok else 'FAIL'}] {got!r}" + ("" if ok else f"   (wanted {want!r})"))
    print(f"\n{len(CASES) - fails}/{len(CASES)} passed")
    if "--live" in sys.argv:
        async def live():
            for raw, want in CASES:
                if want:
                    print(f"  {want!r} -> {await librarian.subjects_for(want)}")
        asyncio.run(live())
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
