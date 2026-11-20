"""J-3086 / F-3797 (P-0076): essay_lesson.compose reports which path an essay took, record() writes it as extra
keys on the essay_lesson_log row, and the single-shot fallback keeps the whole EARLIER READING section and no
longer asks for a "title" key.

Temp paths only; the model is a scripted fake; record()'s side effects are replaced by recorders.
Run from the worktree:  python scripts/_test_J-3086_essay_path.py
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import core                                    # noqa: E402  (before anything that could resolve to C:\Nascence)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import essay_lesson as el            # noqa: E402

FAILS: list[str] = []


def check(cond, msg):
    print(("  ok:   " if cond else "  FAIL: ") + msg)
    if not cond:
        FAILS.append(msg)


TITLE = "Debit and Credit"
BODY = "\n".join("- note %03d: Wohlfart keeps the Schroeter ledgers and the firm trades sugar." % i for i in range(120))[:6900]   # over 6500, pinned under the threshold below (no map-reduce)
PRIOR = ("\n\n── FROM AN EARLIER READING ──\nEARLIER-MARK-START " + "I once read it as a plain story of work. " * 40
         + "EARLIER-MARK-END")
NOTES = BODY + PRIOR
el._REDUCE_THRESHOLD = 7000   # J-3598: live value is now == _SECTION_WINDOW (5000); pinned here to exercise the un-reduced fallback path
assert 6500 < len(BODY) <= el._REDUCE_THRESHOLD and len(BODY) > 6500 and len(BODY[:6500] + PRIOR) > 6500

SEC = ["Anton Wohlfart earns a place in the Schroeter firm through steady work at the ledgers, and the book "
       "measures him by it.",
       "Sabine runs the house while Fink schemes at the counting house; her patience sets the weather of the book "
       "while the counting house plots.",
       "Ehrenthal lends on mortgages, and the old merchant families keep the town's Jews outside their circle; "
       "credit sorts people into creditors and debtors."]
OUTLINE3 = {"thesis": "t", "sections": [{"heading": "H%d" % k, "covers": "c"} for k in range(3)]}


class Fake:
    """outline: 'raise' | a dict returned for the outline call. sections: texts the section writer returns in turn.
    outlines: optional list consumed one per outline call (overrides outline). Records the fallback call."""
    def __init__(self, outline, sections=(), outlines=None):
        self.outline, self.sections, self.outlines = outline, list(sections), outlines
        self.fb = None
        self.i = 0

    async def __call__(self, base_urls, system, user, max_tokens=0, temperature=0.0):
        if "Plan a real ESSAY" in system:
            self.i = 0
            o = self.outlines.pop(0) if self.outlines else self.outline
            if o == "raise":
                raise RuntimeError("hub down: connect timeout")
            return o
        if "writing one section" in system:
            t = self.sections[self.i] if self.i < len(self.sections) else ""
            self.i += 1
            return {"section": t}
        self.fb = (system, user)
        return {"essay": "The novel delves into the intricate interplay between social status, financial power and "
                         "moral judgment. " * 4}


def run(fake, notes=NOTES, gate=False):
    el.CAPSTONE_GATE = gate
    el._PATHS.pop(TITLE, None)
    el._CHECKS.pop(TITLE, None)
    essay = asyncio.run(el.compose(fake, [], TITLE, notes))
    return essay, dict(el._PATHS.get(TITLE) or {})


def test_paths():
    _e, p = run(Fake(OUTLINE3, SEC))
    check(p.get("path") == "sectioned" and not p.get("reason"), f"sectioned path recorded: {p}")
    _e, p = run(Fake(OUTLINE3, [SEC[0], "", SEC[2]]))
    check(p.get("path") == "sectioned" and "2 of 3" in p.get("reason", ""), f"partial sections noted: {p}")
    _e, p = run(Fake("raise"))
    check(p.get("path") == "single_shot" and "RuntimeError" in p["reason"] and "connect timeout" in p["reason"],
          f"outline exception recorded: {p}")
    _e, p = run(Fake({}))
    check(p.get("path") == "single_shot" and "0 dict section" in p["reason"], f"empty outline recorded: {p}")
    _e, p = run(Fake({"thesis": "t", "sections": ["one", "two", "three"]}))
    check(p.get("path") == "single_shot" and "0 dict section(s) of 3" in p["reason"], f"string sections recorded: {p}")
    _e, p = run(Fake(OUTLINE3, ["", "", ""]))
    check(p.get("path") == "single_shot" and "all 3 sections failed" in p["reason"], f"all-sections-failed recorded: {p}")


def test_fallback_prompt():
    f = Fake({})
    run(f)
    sysmsg, user = f.fb
    check('"title"' not in sysmsg and "an essay title" not in sysmsg, "unused title key dropped from the fallback contract")
    check('"essay"' in sysmsg, "fallback contract still asks for the essay key")
    check("EARLIER-MARK-START" in user and "EARLIER-MARK-END" in user,
          "the whole earlier-reading section reaches the fallback")
    part = user.split("recall of it:\n", 1)[1]
    check(len(part) <= 6500, f"fallback notes stay within 6500 chars: {len(part)}")
    check("EARLIER-MARK-END" not in (BODY[:6500] + PRIOR)[:6500], "(control) the old notes[:6500] cut lost the section's end")
    f = Fake({})
    run(f, BODY)
    check(f.fb[1].split("recall of it:\n", 1)[1] == BODY[:6500], "no prior section -> fallback notes are exactly body[:6500]")


def test_regen_path():
    # gate on: the first attempt is a repeating single-shot fallback that fails the check; the regeneration forms
    # through the outline and is kept
    notes = "\n".join("- " + n for n in (
        "I see that the firm of Schroeter trades in sugar and the clerk Anton Wohlfart keeps its ledgers.",
        "What strikes me is that Sabine, the daughter, runs the household while Fink schemes at the counting house.",
        "The Jews of the town are shut out of the old merchant families, and Ehrenthal lends money on mortgages."))
    f = Fake({}, SEC, outlines=[{}, OUTLINE3])
    _e, p = run(f, notes, gate=True)
    c = el._CHECKS.pop(TITLE, None)
    check(c is not None and c.get("attempts") == 2, f"regen ran (attempts==2): {c and c.get('attempts')}")
    check(p.get("path") == "sectioned" and p.get("regen") and p.get("first", "").startswith("single_shot"),
          f"adopted regen is recorded with the first attempt's path: {p}")
    el.CAPSTONE_GATE = False


def test_record_rows():
    from core import world_consolidation as wc, study, competence, mood, book_feelings, memory_edges
    from core.memory import store
    tmp = Path(tempfile.mkdtemp(prefix="j3086_"))
    el._STATE = tmp / "essay_lesson_state.json"
    el._LOG = tmp / "essay_lesson_log.jsonl"
    wc._LOG = tmp / "world_consolidation_log.jsonl"
    patches = [
        mock.patch.object(competence, "record_drill_accuracy", lambda *a, **k: None),
        mock.patch.object(book_feelings, "capstone", lambda *a, **k: None),
        mock.patch.object(store, "store_fragment", lambda *a, **k: "frag1"),
        mock.patch.object(store, "store_light_event", lambda *a, **k: None),
        mock.patch.object(study, "write_tablet", lambda *a, **k: None),
        mock.patch.object(memory_edges, "add_edge", lambda *a, **k: None),
        mock.patch.object(mood, "current_vec", lambda: None), mock.patch.object(mood, "current_valence", lambda: 0.0),
        mock.patch.object(mood, "current_felt", lambda: None),
        mock.patch.object(wc, "file_book_notes", lambda t, *a, **k: {"filed": 0}),
        mock.patch.object(study, "archive_book_note_files", lambda t, *a, **k: {"moved": 0, "dest": "x"}),
    ]
    for p in patches:
        p.start()
    try:
        essay, _p = run(Fake("raise"))
        el.record("b1.txt", TITLE, "T", essay, .5, .5, "fb", source_ids=[])
        el.record("b2.txt", "Other Book", "T", essay, .5, .5, "fb", source_ids=[])   # compose never ran for this one
        essay, _p = run(Fake(OUTLINE3, SEC))
        el.record("b3.txt", TITLE, "T", essay, .5, .5, "fb", source_ids=[])
    finally:
        for p in patches:
            p.stop()
    rows = [json.loads(l) for l in open(el._LOG, encoding="utf-8")]
    check(len(rows) == 3, f"three log rows written to the temp log: {len(rows)}")
    check(rows[0]["path"] == "single_shot" and "connect timeout" in rows[0]["path_reason"],
          f"fallback row: {rows[0].get('path')} / {rows[0].get('path_reason')}")
    check(rows[1]["path"] == "unknown" and "path_reason" not in rows[1], "no compose in process -> 'unknown', no reason")
    check(rows[2]["path"] == "sectioned" and "path_reason" not in rows[2], "sectioned row has path only")
    for k in ("ts", "title", "essay_title", "predicted", "measured", "feedback", "essay", "wider", "felt"):
        check(all(k in r for r in rows), f"existing key '{k}' still on every row")
    check(not el._PATHS and TITLE not in el._LAST_PATH, "record() popped the path state")
    check(Path(el._LOG).resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()), "log path is a temp path")


if __name__ == "__main__":
    test_paths()
    test_fallback_prompt()
    test_regen_path()
    test_record_rows()
    print("\nFAILED: %d" % len(FAILS) if FAILS else "\nALL OK")
    sys.exit(1 if FAILS else 0)
