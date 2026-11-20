"""J-3174 / D-0562: capstone repetition + own-source gate, regeneration, hold, and the sweep's respect for the hold.

Nothing here opens a live store: every path essay_lesson / world_consolidation writes is a temp path, the model is
a scripted fake, and the note-filing / memory-writing calls record() makes are replaced by recorders.
Run from the worktree:  python scripts/test_j3174_capstone_gate.py
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
    if not cond:
        FAILS.append(msg)
        print("  FAIL:", msg)


NOTES_LINES = [
    "I see that the firm of Schroeter trades in sugar and the clerk Anton Wohlfart keeps its ledgers.",
    "What strikes me is that Sabine, the daughter, runs the household while Fink schemes at the counting house.",
    "The Jews of the town are shut out of the old merchant families, and Ehrenthal lends money on mortgages.",
]
NOTES = "\n".join("- " + n for n in NOTES_LINES)

GOOD = ("The novel traces how Anton Wohlfart earns a place in the Schroeter firm through steady ledger work.\n\n"
        "## The household\n\nSabine runs the house while Fink schemes at the counting house, and the daughter's "
        "patience sets the moral weather of the book.\n\n"
        "## The money\n\nEhrenthal lends on mortgages, and the old merchant families keep the town's Jews outside "
        "their circle; credit becomes a way of sorting people.")
REPEAT = ("The novel delves into the intricate interplay between social status, financial power, and moral judgment.\n\n"
          "## The household\n\nThe novel delves into the intricate interplay between social status, financial power, "
          "and moral judgment in the household of Sabine.\n\n"
          "## The money\n\nThe novel delves into the intricate interplay between social status, financial power, "
          "and moral judgment around Ehrenthal.")
FOREIGN = ("The novel shows Anton Wohlfart at the Schroeter firm.\n\n## Elsewhere\n\nMary Rowlandson, taken by "
           "Narragansett raiders near Lancaster, reached Redemption Rock after the Wampanoag war, while Morris dreamed "
           "of Camelot and the Hundred Years War.")


def test_checks():
    r = el.check_repetition(GOOD)
    check(r["ok"], f"good essay should pass repetition: {r}")
    r = el.check_repetition(REPEAT)
    check(not r["ok"] and r["open_restate"] >= 0.5, f"restating essay should fail repetition: {r}")
    twice = "Credit sorts the people of the old town into debtors and creditors every season. " * 2
    r = el.check_repetition("The firm trades in sugar and keeps ledgers all year long. " + twice)
    check(not r["ok"] and r["adjacent"] >= 0.5, f"adjacent-sentence repeat should fail: {r}")
    s = el.check_own_source(GOOD, "\n".join(NOTES_LINES), "", "Debit and Credit")
    check(s["ok"], f"good essay should pass own-source: {s}")
    s = el.check_own_source(FOREIGN, "\n".join(NOTES_LINES), "", "Debit and Credit")
    check(not s["ok"] and any(f["term"] == "rowlandson" for f in s["failing"]), f"foreign names should fail: {s}")
    s = el.check_own_source(FOREIGN, "\n".join(NOTES_LINES), "Mary Rowlandson Narragansett Lancaster Redemption "
                            "Wampanoag Morris Camelot Hundred", "Debit and Credit")
    check(s["ok"] and "rowlandson" in s["cross_book"], f"cross-book terms are flagged, not rejected: {s}")
    # the own/cross split: a name only in the cross-book lines must not count as the book's own
    el._GATHER_META["T"] = {"n_own": 3}
    c = el.check_capstone("T", FOREIGN, NOTES + "\n- Mary Rowlandson was taken near Lancaster by Narragansett "
                          "raiders to Redemption Rock in the Wampanoag war; Morris dreamed of Camelot.")
    check(c["ok"] and c["own_source"]["cross_book"], f"split-aware check should flag cross-book: {c['own_source']}")
    el._GATHER_META.pop("T", None)


class Fake:
    """Scripted call_json: outline first, then one section per call from the given section texts."""
    def __init__(self, *attempts):
        self.attempts = list(attempts)      # each: None (outline fails) or a list of section texts
        self.calls = 0
        self.temps = []

    async def __call__(self, base_urls, system, user, max_tokens=0, temperature=0.0):
        self.calls += 1
        self.temps.append(temperature)
        if "Plan a real ESSAY" in system:
            self.cur = self.attempts.pop(0) if self.attempts else None
            self.i = 0
            if self.cur is None:
                return {}
            return {"thesis": "t", "sections": [{"heading": f"H{k}", "covers": "c"} for k in range(len(self.cur))]}
        if "writing one section" in system:
            t = self.cur[self.i]; self.i += 1
            return {"section": t}
        return {"essay": "A single shot essay about Anton Wohlfart and the Schroeter firm and its ledgers. " * 3}


SEC_BAD = ["The novel delves into the intricate interplay of status and money in the firm of Schroeter and Wohlfart." * 1,
           "The novel delves into the intricate interplay of status and money in the household of Schroeter and Sabine.",
           "The novel delves into the intricate interplay of status and money around Ehrenthal and the Schroeter firm."]
SEC_GOOD = ["Anton Wohlfart earns a place in the Schroeter firm through steady work at the ledgers, and the book "
            "measures him by it.",
            "Sabine runs the house while Fink schemes at the counting house; her patience sets the weather of the book "
            "while the counting house plots.",
            "Ehrenthal lends on mortgages, and the old merchant families keep the town's Jews outside their circle; "
            "credit sorts people into creditors and debtors."]


def test_compose_regen():
    el.CAPSTONE_GATE = True
    pad = lambda ts: [t + " " + x for t, x in zip(ts, ("The ledger work goes on through the year at the firm.",
                      "Over the winter the household keeps its accounts of coal and bread.",
                      "By the spring the mortgages come due and the town takes note."))]
    # 1. first fails, regeneration passes -> regeneration returned, attempts 2, warmer temperature
    f = Fake(pad(SEC_BAD), pad(SEC_GOOD))
    essay = asyncio.run(el.compose(f, [], "Debit and Credit", NOTES))
    c = el._CHECKS.pop("Debit and Credit", None)
    check(c and c["ok"] and c["attempts"] == 2, f"regen should pass on attempt 2: {c and (c['ok'], c['attempts'])}")
    check("Sabine runs the house" in essay, "the passing regeneration is the essay returned")
    check(0.7 in f.temps, f"regeneration must run warmer: {f.temps}")
    # 2. first passes -> exactly one outline + sections, no regeneration
    f = Fake(pad(SEC_GOOD))
    asyncio.run(el.compose(f, [], "Debit and Credit", NOTES))
    c = el._CHECKS.pop("Debit and Credit")
    check(c["ok"] and c["attempts"] == 1 and f.calls == 4, f"pass => 1 attempt, 4 calls: {c['attempts']} {f.calls}")
    # 3. first fails, the regeneration's outline does not form -> single-shot is NOT used as the second chance
    f = Fake(pad(SEC_BAD), None)
    essay = asyncio.run(el.compose(f, [], "Debit and Credit", NOTES))
    c = el._CHECKS.pop("Debit and Credit")
    check(not c["ok"] and c.get("regen") == "did not form" and "single shot" not in essay,
          f"no single-shot second chance: {c.get('regen')}")
    # 4. both fail -> the better (fewer failing sentences) one is returned, and the check says fail
    f = Fake(pad(SEC_BAD), pad(SEC_BAD[:1] + SEC_GOOD[1:]))
    asyncio.run(el.compose(f, [], "Debit and Credit", NOTES))
    c = el._CHECKS.pop("Debit and Credit")
    check(c["attempts"] == 2, f"both attempts made: {c['attempts']}")
    # 5. gate off -> old behaviour: no check, no regeneration
    el.CAPSTONE_GATE = False
    f = Fake(pad(SEC_BAD))
    asyncio.run(el.compose(f, [], "Debit and Credit", NOTES))
    check("Debit and Credit" not in el._CHECKS and f.calls == 4, "gate off must not check or regenerate")
    el.CAPSTONE_GATE = True


def test_record_and_hold():
    from core import world_consolidation as wc, study, competence, mood, book_feelings, memory_edges
    from core.memory import store
    tmp = Path(tempfile.mkdtemp(prefix="j3174_"))
    el._STATE = tmp / "essay_lesson_state.json"
    el._LOG = tmp / "essay_lesson_log.jsonl"
    wc._LOG = tmp / "world_consolidation_log.jsonl"
    filed, moved = [], []
    patches = [
        mock.patch.object(competence, "record_drill_accuracy", lambda *a, **k: None),
        mock.patch.object(book_feelings, "capstone", lambda *a, **k: None),
        mock.patch.object(store, "store_fragment", lambda *a, **k: "frag1"),
        mock.patch.object(store, "store_light_event", lambda *a, **k: None),
        mock.patch.object(study, "write_tablet", lambda *a, **k: None),
        mock.patch.object(memory_edges, "add_edge", lambda *a, **k: None),
        mock.patch.object(mood, "current_vec", lambda: None), mock.patch.object(mood, "current_valence", lambda: 0.0),
        mock.patch.object(mood, "current_felt", lambda: None),
        mock.patch.object(wc, "file_book_notes", lambda t, *a, **k: (filed.append(t) or {"filed": 3})),
        mock.patch.object(study, "archive_book_note_files", lambda t, *a, **k: (moved.append(t) or {"moved": 2, "dest": "x"})),
    ]
    for p in patches:
        p.start()
    try:
        title = "Debit and Credit"
        # PASS: filed as before, row says held=False
        el._CHECKS[title] = {"ok": True, "attempts": 1, "repetition": {"ok": True, "failing": [], "open_restate": .1,
                             "adjacent": .0}, "own_source": {"ok": True, "failing": [], "sections": [], "cross_book": []}}
        el.record("b1.txt", title, "T", GOOD, .5, .5, "fb", source_ids=[])
        check(filed == [title] and moved == [title], f"a passing capstone files its notes: {filed} {moved}")
        check(not el.filing_held(title), "no hold on a pass")
        # FAIL: not filed, held, log row carries the reasons
        filed.clear(); moved.clear()
        el._CHECKS[title] = {"ok": False, "attempts": 2, "repetition": {"ok": False, "open_restate": .8, "adjacent": .1,
                             "failing": [{"why": "restates opening", "score": .8, "sentence": "The novel delves"}]},
                             "own_source": {"ok": True, "failing": [], "sections": [], "cross_book": ["rowlandson"]}}
        el.record("b2.txt", title, "T", REPEAT, .5, .5, "fb", source_ids=[])
        check(not filed and not moved, f"a failing capstone must not file or move notes: {filed} {moved}")
        check(el.filing_held(title), "failing capstone is held")
        check(not el.filing_held("Debit and Credit Or the Catastrophes of a Clerk"),
              "a short held title does not hold a longer, different one")
        _long = "A Very Long Book Title About The Natural History Of Many Things Volume One Part Two"
        el._CHECKS[_long] = {"ok": False, "attempts": 2, "repetition": {"ok": False, "failing": []},
                             "own_source": {"ok": True, "failing": [], "sections": [], "cross_book": []}}
        el.record("bL.txt", _long, "T", REPEAT, .5, .5, "fb", source_ids=[])
        check(el.filing_held(_long[:50]) and el.filing_held(el._smart_cut(_long)) and not el.filing_held(_long[:20]),
              "a long held title matches its 50-char and smart-cut truncations, not a 20-char stub")
        el.release_hold(_long)
        rows = [json.loads(l) for l in open(el._LOG, encoding="utf-8")]
        ck = rows[1]["check"]
        check(rows[0]["check"]["ok"] and not ck["ok"] and ck["held"] and ck["attempts"] == 2 and ck["failing"],
              f"log rows carry pass/fail + reasons: {rows[0]['check']} {ck}")
        # the sleep sweep honours the hold (no DB opened: the early return comes first)
        s = wc._file_book_notes(title)
        check("held" in s["reason"] and s["filed"] == 0, f"sweep must leave a held book alone: {s}")
        # the founder's manual release is the only way back
        check(el.release_hold(title) and not el.filing_held(title), "release_hold lifts the hold")
        # a record with NO prior check runs one itself (gather_notes stubbed to a clean set) and never silently files
        filed.clear()
        with mock.patch.object(el, "gather_notes", lambda t, b: (NOTES, [])):
            el.record("b3.txt", title, "T", GOOD, .5, .5, "fb", source_ids=[])
        check(filed == [title], f"late check passes a clean essay: {filed}")
        filed.clear()
        with mock.patch.object(el, "gather_notes", lambda t, b: (NOTES, [])):
            el.record("b4.txt", "Another Book", "T", FOREIGN, .5, .5, "fb", source_ids=[])
        check(not filed and el.filing_held("Another Book"), "late check holds a foreign-sourced essay")
        # gate off: always files, row has no check
        el.CAPSTONE_GATE = False
        filed.clear()
        el.record("b5.txt", "Third Book", "T", REPEAT, .5, .5, "fb", source_ids=[])
        check(filed == ["Third Book"], "gate off files regardless")
        check("check" not in json.loads(open(el._LOG, encoding="utf-8").readlines()[-1]), "gate off writes no check")
        el.CAPSTONE_GATE = True
    finally:
        for p in patches:
            p.stop()


if __name__ == "__main__":
    for t in (test_checks, test_compose_regen, test_record_and_hold):
        print(t.__name__)
        try:
            t()
        except Exception as exc:
            import traceback; traceback.print_exc()
            FAILS.append(f"{t.__name__} raised {exc!r}")
    print("RESULT:", "FAIL %d" % len(FAILS) if FAILS else "ALL PASS")
    sys.exit(1 if FAILS else 0)
